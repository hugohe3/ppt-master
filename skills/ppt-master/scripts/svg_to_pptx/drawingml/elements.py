"""SVG element converters: rect, circle, line, path, polygon, polyline, text, image, ellipse."""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes
from xml.etree import ElementTree as ET

from pptx_shapes import (
    CONNECTOR_PRESET_TYPES,
    OOXML_COORDINATE_MAX,
    OOXML_COORDINATE_MIN,
    get_preset_registry,
    has_relationship_attributes,
    load_shape_type_values,
    validate_ooxml_xfrm,
)
from pptx_effects import EFFECT_REASON_ATTR, EFFECT_STATUS_ATTR
from pptx_to_svg.preset_authoring import AUTHORING_ATTR, AUTHORING_VALUE
from resource_paths import resolve_external_image_reference

from .context import ConvertContext, ShapeResult
from .theme_colors import color_node_xml
from .theme_fonts import theme_font_tokens
from .text_properties import (
    drawingml_letter_spacing,
    normalize_project_text_segments,
    parse_project_font_style,
    parse_project_font_weight,
    parse_project_letter_spacing,
    parse_project_text_anchor,
    parse_project_text_decoration,
    resolve_project_xml_space,
)
from .utils import (
    SVG_NS, XLINK_NS, ANGLE_UNIT, FONT_PX_TO_HUNDREDTHS_PT,
    PROJECT_IMAGE_ASPECT_RATIO_ANCHORS,
    px_to_emu, _f, _get_attr, parse_svg_length,
    svg_length_x, svg_length_y, svg_length_size,
    ctx_x, ctx_y, ctx_w, ctx_h,
    rect_to_dml_xfrm,
    combine_opacity, parse_hex_color, parse_svg_color,
    resolve_url_id, get_effective_filter_id,
    parse_inline_style, parse_font_family, is_cjk_char,
    detect_text_lang, estimate_text_cluster_widths, font_px_to_hpt,
    resolve_text_run_fonts, split_project_text_clusters,
    is_thick_circle_shorthand, parse_project_geometry_length,
    is_canonical_project_geometry_length,
    parse_project_image_aspect_ratio,
    parse_project_opacity,
    parse_project_stroke_dasharray,
    project_definition_index,
    matrix_multiply, parse_transform_matrix, parse_transform_operations,
    transform_point, _xml_escape,
)
from .styles import (
    build_solid_fill, build_gradient_fill,
    build_fill_xml, build_stroke_xml, build_effect_xml, classify_filter_effect,
    get_element_opacity, get_fill_opacity, get_stroke_opacity,
)
from .paths import (
    PathCommand, parse_svg_path, parse_svg_points, svg_path_to_absolute,
    normalize_path_commands, path_commands_to_drawingml,
)


def _resolve_external_image(svg_dir: Path, href: str) -> Path:
    """Resolve a non-data-URI image href to a file on disk.

    Search order: next to the SVG (``svg_output/``), the project root, the
    project's ``images/`` (the single runtime image pool — template-bundled
    bitmaps plus AI / web / user images all live here), then ``templates/``
    (legacy flat-copied template assets). Raises ``FileNotFoundError`` if none
    of these exist.
    """
    candidate = resolve_external_image_reference(svg_dir, href)
    if candidate is not None:
        return candidate
    raise FileNotFoundError(f'External image not found: {href}')


_PROJECT_IMAGE_FORMATS = {
    'bmp': 'bmp',
    'emf': 'emf',
    'gif': 'gif',
    'jpeg': 'jpg',
    'jpg': 'jpg',
    'png': 'png',
    'svg': 'svg',
    'svg+xml': 'svg',
    'tif': 'tif',
    'tiff': 'tiff',
    'webp': 'webp',
    'wmf': 'wmf',
    'x-emf': 'emf',
    'x-wmf': 'wmf',
}
_PIL_IMAGE_FORMATS = {
    'bmp': 'BMP',
    'gif': 'GIF',
    'jpg': 'JPEG',
    'png': 'PNG',
    'tif': 'TIFF',
    'tiff': 'TIFF',
    'webp': 'WEBP',
}


def _normalize_project_image_format(raw: str) -> str | None:
    return _PROJECT_IMAGE_FORMATS.get(raw.strip().lower().lstrip('.'))


def _little_uint(data: bytes, offset: int, size: int) -> int:
    return int.from_bytes(data[offset:offset + size], 'little', signed=False)


def _valid_emf_payload(data: bytes) -> bool:
    """Validate the EMF header and complete bounded record stream."""
    if len(data) < 88:
        return False
    header_size = _little_uint(data, 4, 4)
    total_size = _little_uint(data, 48, 4)
    record_count = _little_uint(data, 52, 4)
    header_palette_entries = _little_uint(data, 68, 4)
    if (
        _little_uint(data, 0, 4) != 1
        or data[40:44] != b' EMF'
        or header_size < 88
        or header_size > total_size
        or total_size != len(data)
        or record_count < 1
    ):
        return False

    offset = 0
    count = 0
    last_type = 0
    last_size = 0
    while offset < total_size:
        if offset + 8 > total_size:
            return False
        record_type = _little_uint(data, offset, 4)
        record_size = _little_uint(data, offset + 4, 4)
        if record_size < 8 or record_size % 4 or offset + record_size > total_size:
            return False
        record_end = offset + record_size
        if count == 0 and (record_type != 1 or record_size != header_size):
            return False
        if count > 0 and record_type == 1:
            return False
        if record_type == 14:
            if (
                record_size < 20
                or record_end != total_size
                or _little_uint(data, record_end - 4, 4) != record_size
            ):
                return False
            palette_entries = _little_uint(data, offset + 8, 4)
            palette_offset = _little_uint(data, offset + 12, 4)
            if (
                palette_entries != header_palette_entries
                or palette_entries and (
                    palette_offset < 16
                    or palette_offset + palette_entries * 4 > record_size - 4
                )
            ):
                return False
        offset = record_end
        count += 1
        last_type = record_type
        last_size = record_size
    return (
        offset == total_size
        # MS-EMF counts all records. LibreOffice-generated EMF files in the
        # wild count records after the header, so retain that interoperable
        # spelling while keeping the complete stream bounded.
        and count in {record_count, record_count + 1}
        and last_type == 14
        and last_size >= 20
    )


def _valid_wmf_payload(data: bytes) -> bool:
    """Validate a standard or placeable WMF header and record stream."""
    meta_offset = 0
    if data.startswith(b'\xd7\xcd\xc6\x9a'):
        if len(data) < 40:
            return False
        checksum = 0
        for offset in range(0, 20, 2):
            checksum ^= _little_uint(data, offset, 2)
        if checksum != _little_uint(data, 20, 2):
            return False
        meta_offset = 22
    if len(data) < meta_offset + 24:
        return False
    meta_type = _little_uint(data, meta_offset, 2)
    header_words = _little_uint(data, meta_offset + 2, 2)
    version = _little_uint(data, meta_offset + 4, 2)
    total_words = _little_uint(data, meta_offset + 6, 4)
    max_record_words = _little_uint(data, meta_offset + 12, 4)
    if (
        meta_type not in {1, 2}
        or header_words != 9
        or version not in {0x0100, 0x0300}
        or total_words < 12
        or max_record_words < 3
    ):
        return False
    total_end = meta_offset + total_words * 2
    if total_end != len(data):
        return False

    offset = meta_offset + header_words * 2
    last_function = -1
    last_record_words = 0
    observed_max_record_words = 0
    while offset < total_end:
        if offset + 6 > total_end:
            return False
        record_words = _little_uint(data, offset, 4)
        function = _little_uint(data, offset + 4, 2)
        if (
            record_words < 3
            or record_words > max_record_words
            or offset + record_words * 2 > total_end
        ):
            return False
        record_end = offset + record_words * 2
        if function == 0 and (record_words != 3 or record_end != total_end):
            return False
        offset = record_end
        last_function = function
        last_record_words = record_words
        observed_max_record_words = max(
            observed_max_record_words,
            record_words,
        )
    return (
        offset == total_end
        and last_function == 0
        and last_record_words == 3
        and observed_max_record_words == max_record_words
    )


def _valid_project_image_payload(img_format: str, img_data: bytes) -> bool:
    """Return whether bytes are a supported image of the declared format."""
    if not img_data:
        return False
    if img_format == 'svg':
        try:
            root = ET.fromstring(img_data)
        except ET.ParseError:
            return False
        return root.tag == f'{{{SVG_NS}}}svg'
    if img_format == 'emf':
        return _valid_emf_payload(img_data)
    if img_format == 'wmf':
        return _valid_wmf_payload(img_data)

    expected = _PIL_IMAGE_FORMATS.get(img_format)
    if expected is None:
        return False
    try:
        from PIL import Image, UnidentifiedImageError  # type: ignore
    except ImportError:
        return False
    try:
        with Image.open(io.BytesIO(img_data)) as image:
            actual = (image.format or '').upper()
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return False
    return actual == expected


def _decode_data_image_uri(href: str) -> tuple[str, bytes] | None:
    """Decode and validate one closed-project image data URI."""
    if not href.startswith('data:') or ',' not in href:
        return None

    header, payload = href.split(',', 1)
    match = re.fullmatch(
        r'data:image/([A-Za-z0-9.+-]+)(?:;[^;,]*)*?(?:;base64)?',
        header,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    img_format = _normalize_project_image_format(match.group(1))
    if img_format is None:
        return None

    is_base64 = any(
        part.strip().lower() == 'base64'
        for part in header.split(';')[1:]
    )
    try:
        if is_base64:
            img_data = base64.b64decode(payload, validate=True)
        else:
            img_data = unquote_to_bytes(payload)
    except (ValueError, binascii.Error):
        return None
    if not _valid_project_image_payload(img_format, img_data):
        return None
    return img_format, img_data


@dataclass(frozen=True)
class ProjectImageSource:
    """Validated bytes and package extension for one SVG image reference."""

    img_format: str
    img_data: bytes


def _project_image_href(elem: ET.Element) -> str:
    href_keys = tuple(
        key for key in ('href', f'{{{XLINK_NS}}}href')
        if key in elem.attrib
    )
    if len(href_keys) != 1:
        raise ValueError('requires exactly one href or xlink:href')
    href = elem.get(href_keys[0])
    if href is None or not href.strip():
        raise ValueError('href cannot be empty')
    return href


def load_project_image_source(
    elem: ET.Element,
    svg_dir: Path | None,
) -> ProjectImageSource:
    """Load one exact SVG image source or raise a contract error."""
    if elem.tag != f'{{{SVG_NS}}}image':
        raise ValueError('expected an SVG-namespace <image> element')
    href = _project_image_href(elem)
    if href.startswith('data:'):
        decoded = _decode_data_image_uri(href)
        if decoded is None:
            raise ValueError(
                'data URI must contain a supported, non-empty image with '
                'valid encoding and bytes'
            )
        img_format, img_data = decoded
        return ProjectImageSource(img_format, img_data)

    if svg_dir is None:
        raise ValueError('external image requires an SVG directory context')
    try:
        img_path = _resolve_external_image(svg_dir, href)
    except FileNotFoundError as exc:
        raise ValueError(str(exc)) from exc
    img_format = _normalize_project_image_format(img_path.suffix)
    if img_format is None:
        raise ValueError(
            f'external image has unsupported file extension {img_path.suffix!r}'
        )
    try:
        img_data = img_path.read_bytes()
    except OSError as exc:
        raise ValueError(f'cannot read external image {href!r}: {exc}') from exc
    if not _valid_project_image_payload(img_format, img_data):
        raise ValueError(
            f'external image {href!r} is empty, corrupt, or does not match '
            f'its {img_path.suffix} extension'
        )
    return ProjectImageSource(img_format, img_data)


def project_image_errors(
    root: ET.Element,
    svg_dir: Path | None,
    *,
    allow_template_placeholders: bool = False,
) -> list[str]:
    """Return source and frame errors for exact SVG image elements."""
    errors: list[str] = []
    for elem in root.iter():
        if elem.tag.rsplit('}', 1)[-1] != 'image':
            continue
        label = _element_contract_label(elem)
        if elem.tag != f'{{{SVG_NS}}}image':
            errors.append(
                f'{label} must use the SVG namespace '
                f'{SVG_NS!r}'
            )
            continue
        style_values = parse_inline_style(elem.get('style'))
        for attribute in ('width', 'height'):
            raw = style_values.get(attribute)
            if raw is None:
                raw = elem.get(attribute)
            if raw is None:
                errors.append(
                    f'{label} requires explicit positive {attribute}'
                )
                continue
            try:
                value = parse_project_geometry_length(raw, attribute)
            except ValueError:
                # The shared geometry-length contract owns syntax diagnostics.
                continue
            if value <= 0:
                errors.append(
                    f'{label} {attribute} must be positive; got {raw!r}'
                )
        try:
            raw_href = _project_image_href(elem)
        except ValueError as exc:
            errors.append(f'{label} invalid image source: {exc}')
            continue
        if (
            allow_template_placeholders
            and '{{' in raw_href
            and '}}' in raw_href
        ):
            continue
        try:
            load_project_image_source(elem, svg_dir)
        except ValueError as exc:
            errors.append(f'{label} invalid image source: {exc}')
    return sorted(errors)


def _wrap_shape(
    shape_id: int, name: str,
    off_x: int, off_y: int,
    ext_cx: int, ext_cy: int,
    geom_xml: str, fill_xml: str, stroke_xml: str,
    effect_xml: str = '', extra_xml: str = '',
    rot: int = 0,
    xfrm_attr: str = '',
) -> str:
    """Wrap DrawingML content into a <p:sp> shape element."""
    rot_attr = f' rot="{rot}"' if rot else ''
    xfrm_attrs = f'{xfrm_attr}{rot_attr}'
    return f'''<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="{_xml_escape(name)}"/>
<p:cNvSpPr/><p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm{xfrm_attrs}><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
{geom_xml}
{fill_xml}
{stroke_xml}
{effect_xml}
</p:spPr>
{extra_xml}
</p:sp>'''


def _wrap_connector(
    shape_id: int,
    name: str,
    off_x: int,
    off_y: int,
    ext_cx: int,
    ext_cy: int,
    geom_xml: str,
    fill_xml: str,
    stroke_xml: str,
    effect_xml: str = '',
    rot: int = 0,
    xfrm_attr: str = '',
    connection_xml: str = '',
    extra_xml: str = '',
) -> str:
    """Wrap DrawingML content into a native ``p:cxnSp`` connector."""
    rot_attr = f' rot="{rot}"' if rot else ''
    xfrm_attrs = f'{xfrm_attr}{rot_attr}'
    return f'''<p:cxnSp>
<p:nvCxnSpPr>
<p:cNvPr id="{shape_id}" name="{_xml_escape(name)}"/>
<p:cNvCxnSpPr>{connection_xml}</p:cNvCxnSpPr><p:nvPr/>
</p:nvCxnSpPr>
<p:spPr>
<a:xfrm{xfrm_attrs}><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
{geom_xml}
{fill_xml}
{stroke_xml}
{effect_xml}
</p:spPr>
{extra_xml}
</p:cxnSp>'''


def _wrap_geometry_object(
    elem: ET.Element,
    ctx: ConvertContext,
    shape_id: int,
    name: str,
    off_x: int,
    off_y: int,
    ext_cx: int,
    ext_cy: int,
    geom_xml: str,
    fill_xml: str,
    stroke_xml: str,
    effect_xml: str = '',
    xfrm_attr: str = '',
) -> str:
    """Wrap a semantic leaf as a shape or connector without guessing."""
    name = elem.get('data-pptx-shape-name') or name
    shape_style_xml = _decode_shape_style(elem)
    object_kind = elem.get('data-pptx-object')
    if object_kind != 'connector':
        return _wrap_shape(
            shape_id,
            name,
            off_x,
            off_y,
            ext_cx,
            ext_cy,
            geom_xml,
            fill_xml,
            stroke_xml,
            effect_xml,
            extra_xml=shape_style_xml,
            xfrm_attr=xfrm_attr,
        )

    prst = elem.get('data-pptx-prst')
    is_custom = elem.get('data-pptx-geometry-kind') == 'custom'
    if prst is None and not is_custom:
        raise ValueError(
            'data-pptx-object="connector" requires preset or preserved '
            'custom geometry'
        )
    return _wrap_connector(
        shape_id,
        name,
        off_x,
        off_y,
        ext_cx,
        ext_cy,
        geom_xml,
        fill_xml,
        stroke_xml,
        effect_xml,
        xfrm_attr=xfrm_attr,
        connection_xml=_connector_connection_xml(elem, ctx),
        extra_xml=shape_style_xml,
    )


def _decode_shape_style(elem: ET.Element) -> str:
    encoded = elem.get('data-pptx-shape-style')
    if not encoded:
        return ''
    try:
        raw = base64.b64decode(encoded, validate=True)
        style = ET.fromstring(raw)
        decoded = raw.decode('utf-8')
    except (ValueError, binascii.Error, UnicodeDecodeError, ET.ParseError) as exc:
        raise ValueError(f'Invalid shape-style metadata: {exc}') from exc
    if style.tag != (
        '{http://schemas.openxmlformats.org/presentationml/2006/main}style'
    ):
        raise ValueError('Shape-style metadata payload must be p:style')
    if has_relationship_attributes(style):
        raise ValueError(
            'Shape-style metadata must not contain relationship attributes'
        )
    return decoded


def _connector_connection_xml(elem: ET.Element, ctx: ConvertContext) -> str:
    """Restore connector endpoint attachment using the reserved source id map."""
    parts: list[str] = []
    for endpoint, tag in (('start', 'stCxn'), ('end', 'endCxn')):
        raw_shape_id = elem.get(f'data-pptx-{endpoint}-shape-id')
        raw_site = elem.get(f'data-pptx-{endpoint}-site')
        if raw_shape_id is None and raw_site is None:
            continue
        if raw_shape_id is None or raw_site is None:
            raise ValueError(
                f'Connector {endpoint} endpoint requires both shape-id and site'
            )
        target_scope = (
            elem.get(f'data-pptx-{endpoint}-shape-scope')
            or elem.get('data-pptx-shape-scope')
            or 'slide'
        )
        target_id = ctx.reference_shape_id(raw_shape_id, target_scope)
        try:
            site = int(raw_site)
        except ValueError as exc:
            raise ValueError(
                f'Invalid connector {endpoint} site {raw_site!r}'
            ) from exc
        if site < 0 or site > 0xFFFFFFFF:
            raise ValueError(
                f'Connector {endpoint} site is outside unsigned integer range: {site}'
            )
        parts.append(f'<a:{tag} id="{target_id}" idx="{site}"/>')
    return ''.join(parts)


def _claim_element_shape_id(elem: ET.Element, ctx: ConvertContext) -> int:
    return ctx.claim_shape_id(
        elem.get('data-pptx-shape-id'),
        elem.get('data-pptx-shape-scope'),
    )


def _context_transform_matrix(ctx: ConvertContext) -> tuple[float, float, float, float, float, float]:
    """Return the current context as a full SVG affine matrix."""
    if ctx.use_transform_matrix:
        return ctx.transform_matrix
    return (
        ctx.scale_x, 0.0,
        0.0, ctx.scale_y,
        ctx.translate_x, ctx.translate_y,
    )


def _combined_transform_matrix(
    ctx: ConvertContext,
    transform: str | None,
) -> tuple[float, float, float, float, float, float]:
    """Compose context transform with an element-level transform attribute."""
    matrix = _context_transform_matrix(ctx)
    if transform:
        matrix = matrix_multiply(matrix, parse_transform_matrix(transform))
    return matrix


def _uses_full_transform(ctx: ConvertContext, transform: str | None) -> bool:
    return ctx.use_transform_matrix or bool(transform)


def _transformed_point(
    ctx: ConvertContext,
    x: float,
    y: float,
    transform: str | None,
) -> tuple[float, float]:
    if _uses_full_transform(ctx, transform):
        return transform_point(_combined_transform_matrix(ctx, transform), x, y)
    return ctx_x(x, ctx), ctx_y(y, ctx)


def _shape_xfrm_from_svg_rect(
    ctx: ConvertContext,
    raw_x: float,
    raw_y: float,
    raw_w: float,
    raw_h: float,
    resolved_x: float,
    resolved_y: float,
    resolved_w: float,
    resolved_h: float,
    transform: str | None,
    *,
    preserve_degenerate_axes: bool = False,
) -> tuple[str, int, int, int, int, tuple[int, int, int, int]]:
    """Build DrawingML xfrm data for an SVG rectangle-like element."""
    if _uses_full_transform(ctx, transform):
        return rect_to_dml_xfrm(
            raw_x, raw_y, raw_w, raw_h,
            _combined_transform_matrix(ctx, transform),
            preserve_degenerate_axes=preserve_degenerate_axes,
        )

    off_x = px_to_emu(resolved_x)
    off_y = px_to_emu(resolved_y)
    ext_cx = px_to_emu(resolved_w)
    ext_cy = px_to_emu(resolved_h)
    return '', off_x, off_y, ext_cx, ext_cy, (off_x, off_y, off_x + ext_cx, off_y + ext_cy)


def _transform_path_commands(
    commands: list[PathCommand],
    matrix: tuple[float, float, float, float, float, float],
) -> list[PathCommand]:
    """Apply an affine transform to normalized M/L/C/Z path commands."""
    transformed: list[PathCommand] = []
    for cmd in commands:
        if cmd.cmd in ('M', 'L'):
            x, y = transform_point(matrix, cmd.args[0], cmd.args[1])
            transformed.append(PathCommand(cmd.cmd, [x, y]))
        elif cmd.cmd == 'C':
            args: list[float] = []
            for i in range(0, 6, 2):
                x, y = transform_point(matrix, cmd.args[i], cmd.args[i + 1])
                args.extend([x, y])
            transformed.append(PathCommand(cmd.cmd, args))
        else:
            transformed.append(cmd)
    return transformed


# ---------------------------------------------------------------------------
# rect
# ---------------------------------------------------------------------------

# Cubic-Bézier control distance for approximating a quarter circle / ellipse.
# Distance from corner to control point along the tangent, expressed as a
# fraction of the radius. Standard "magic number" for a 90° arc (max error
# ~0.027% of the radius).
_BEZIER_QUARTER_K = 0.5522847498


# The hash-locked shared catalog is the single source of truth for the 187
# ECMA-376 ``ST_ShapeType`` values. Loading it here makes exporter validation
# fail closed if the catalog is missing, corrupt, or incomplete.
PPTX_PRESET_SHAPE_TYPES = frozenset(load_shape_type_values())

_PPTX_AV_PREFIX = 'data-pptx-av-'
_PPTX_GUIDE_NAME_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]{0,63}')
_PPTX_VAL_FORMULA_RE = re.compile(r'val[\t ]+([+-]?\d+)')
def _parse_preset_geometry_metadata(
    elem: ET.Element,
) -> tuple[str | None, list[tuple[str, str]], tuple[float, float, float, float] | None]:
    """Parse and validate rendering-neutral preset geometry metadata."""
    status = (elem.get('data-pptx-geometry-status') or '').strip()
    authoring = elem.get(AUTHORING_ATTR)
    if authoring not in {None, AUTHORING_VALUE}:
        raise ValueError(f'Unsupported {AUTHORING_ATTR} value {authoring!r}')
    if authoring == AUTHORING_VALUE:
        object_kind = elem.get('data-pptx-object')
        if object_kind not in {'shape', 'connector'}:
            raise ValueError(
                'Authored preset metadata requires data-pptx-object='
                '"shape" or "connector"'
            )
        preset = elem.get('data-pptx-prst')
        if preset is None:
            raise ValueError('Authored preset metadata requires data-pptx-prst')
        if preset in CONNECTOR_PRESET_TYPES and object_kind != 'connector':
            raise ValueError(
                f'Connector preset {preset!r} requires '
                'data-pptx-object="connector"'
            )
        if object_kind == 'connector' and preset not in CONNECTOR_PRESET_TYPES:
            raise ValueError(
                f'Authored connector requires a connector preset, got {preset!r}'
            )
        if elem.get('data-pptx-frame') is None:
            raise ValueError('Authored preset metadata requires data-pptx-frame')
    if status not in {'', 'exact', 'unsupported'}:
        raise ValueError(
            f'Unsupported data-pptx-geometry-status {status!r}; '
            'expected exact or unsupported'
        )
    raw_reason = elem.get('data-pptx-geometry-reason')
    if raw_reason is not None and status != 'unsupported':
        raise ValueError(
            'data-pptx-geometry-reason requires '
            'data-pptx-geometry-status="unsupported"'
        )
    if status == 'unsupported':
        reason = (raw_reason or 'unspecified').strip()
        raise ValueError(f'Unsupported source PPTX geometry: {reason}')

    prst = elem.get('data-pptx-prst')
    allowed_guide_names: frozenset[str] = frozenset()
    if prst is not None:
        if prst != prst.strip() or prst not in PPTX_PRESET_SHAPE_TYPES:
            raise ValueError(f'Unknown or invalid data-pptx-prst {prst!r}')
        allowed_guide_names = frozenset(
            guide.name
            for guide in get_preset_registry().get(prst).adjustments
        )

    guide_formulas: dict[str, str] = {}
    for attr_name, raw_fmla in elem.attrib.items():
        if not attr_name.startswith(_PPTX_AV_PREFIX):
            continue
        if prst is None:
            raise ValueError(f'{attr_name} requires data-pptx-prst')
        guide_name = attr_name[len(_PPTX_AV_PREFIX):]
        if not _PPTX_GUIDE_NAME_RE.fullmatch(guide_name):
            raise ValueError(f'Invalid preset adjustment guide name {guide_name!r}')
        if guide_name not in allowed_guide_names:
            raise ValueError(
                f'Preset {prst!r} has no adjustment guide named {guide_name!r}'
            )
        formula = raw_fmla.strip()
        if not formula:
            raise ValueError(f'{attr_name} must not be empty')
        match = _PPTX_VAL_FORMULA_RE.fullmatch(formula)
        if match is not None:
            value = int(match.group(1))
            if not OOXML_COORDINATE_MIN <= value <= OOXML_COORDINATE_MAX:
                raise ValueError(
                    f'{attr_name} value {value} is outside OOXML coordinate range'
                )
        guide_formulas[guide_name] = formula

    # Compatibility for SVGs emitted before the generic ``data-pptx-av-*``
    # contract. New imports always use the canonical full-formula attributes.
    if prst == 'round2SameRect':
        guide_names = set(guide_formulas)
        for guide_name, default in (('adj1', 16667), ('adj2', 0)):
            legacy_name = f'data-pptx-{guide_name}'
            if guide_name in guide_names or elem.get(legacy_name) is None:
                continue
            raw_value = elem.get(legacy_name, str(default))
            try:
                value = int(float(raw_value))
            except ValueError as exc:
                raise ValueError(f'{legacy_name} must be numeric, got {raw_value!r}') from exc
            value = max(0, min(100000, value))
            guide_formulas[guide_name] = f'val {value}'

    guides: list[tuple[str, str]] = []
    if prst is not None and guide_formulas:
        registry = get_preset_registry()
        try:
            evaluated = registry.evaluate(
                prst,
                100000,
                100000,
                adjustments=guide_formulas,
            )
        except ValueError as exc:
            raise ValueError(
                f'Invalid adjustment formula for preset {prst!r}: {exc}'
            ) from exc
        for name, value in evaluated.adjustments.items():
            if (
                name in guide_formulas
                and not OOXML_COORDINATE_MIN
                <= value
                <= OOXML_COORDINATE_MAX
            ):
                raise ValueError(
                    f'data-pptx-av-{name} evaluates outside OOXML coordinate range'
                )
        guides = [
            (guide.name, guide_formulas[guide.name])
            for guide in registry.get(prst).adjustments
            if guide.name in guide_formulas
        ]

    frame = None
    raw_frame = elem.get('data-pptx-frame')
    if raw_frame is not None:
        parts = re.split(r'[\s,]+', raw_frame.strip())
        if len(parts) != 4:
            raise ValueError(
                'data-pptx-frame must contain exactly four numbers: x y width height'
            )
        try:
            frame = tuple(float(part) for part in parts)
        except ValueError as exc:
            raise ValueError(f'Invalid data-pptx-frame {raw_frame!r}') from exc
        if not all(math.isfinite(value) for value in frame):
            raise ValueError(f'data-pptx-frame must contain finite numbers, got {raw_frame!r}')
        is_connector = (
            elem.get('data-pptx-object') == 'connector'
            or prst in CONNECTOR_PRESET_TYPES
        )
        if is_connector:
            if frame[2] < 0 or frame[3] < 0 or (frame[2] == 0 and frame[3] == 0):
                raise ValueError(
                    'Connector data-pptx-frame dimensions must be non-negative '
                    f'and not both zero, got {raw_frame!r}'
                )
        elif frame[2] <= 0 or frame[3] <= 0:
            raise ValueError(
                f'data-pptx-frame width and height must be positive, got {raw_frame!r}'
            )
        validate_ooxml_xfrm(
            px_to_emu(frame[0]),
            px_to_emu(frame[1]),
            px_to_emu(frame[2]),
            px_to_emu(frame[3]),
        )

    return prst, guides, frame


def validate_preset_geometry_metadata(elem: ET.Element) -> list[str]:
    """Return native shape metadata errors for authoring-time validation."""
    errors: list[str] = []
    try:
        _parse_preset_geometry_metadata(elem)
    except ValueError as exc:
        errors.append(str(exc))
    if elem.get('data-pptx-custgeom') is not None:
        try:
            _build_preserved_custom_geom(elem)
        except ValueError as exc:
            errors.append(str(exc))
    if elem.get('data-pptx-shape-style') is not None:
        try:
            _decode_shape_style(elem)
        except ValueError as exc:
            errors.append(str(exc))
    raw_shape_id = elem.get('data-pptx-shape-id')
    if raw_shape_id is not None:
        try:
            shape_id = int(raw_shape_id)
        except ValueError:
            errors.append(f'Invalid data-pptx-shape-id {raw_shape_id!r}')
        else:
            if shape_id < 2 or shape_id > 0xFFFFFFFF:
                errors.append(
                    'data-pptx-shape-id must be between 2 and 4294967295'
                )
    scope = elem.get('data-pptx-shape-scope')
    if scope is not None and re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', scope) is None:
        errors.append(f'Invalid data-pptx-shape-scope {scope!r}')
    for endpoint in ('start', 'end'):
        target = elem.get(f'data-pptx-{endpoint}-shape-id')
        site = elem.get(f'data-pptx-{endpoint}-site')
        if (target is None) != (site is None):
            errors.append(
                f'Connector {endpoint} endpoint requires both shape-id and site'
            )
        if target is not None:
            try:
                target_id = int(target)
                site_id = int(site or '')
            except ValueError:
                errors.append(f'Invalid connector {endpoint} endpoint metadata')
            else:
                if target_id < 2 or target_id > 0xFFFFFFFF:
                    errors.append(f'Connector {endpoint} shape-id is out of range')
                if site_id < 0 or site_id > 0xFFFFFFFF:
                    errors.append(f'Connector {endpoint} site is out of range')
    return errors


def _build_preset_geom_from_meta(elem: ET.Element) -> str | None:
    """Build validated native DrawingML preset geometry from SVG metadata."""
    prst, guides, _frame = _parse_preset_geometry_metadata(elem)
    if prst is None:
        return None
    if not guides:
        return f'<a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>'
    guide_xml = ''.join(
        f'<a:gd name="{_xml_escape(name)}" fmla="{_xml_escape(fmla)}"/>'
        for name, fmla in guides
    )
    return f'<a:prstGeom prst="{prst}"><a:avLst>{guide_xml}</a:avLst></a:prstGeom>'


def _build_preserved_custom_geom(elem: ET.Element) -> str | None:
    """Return unchanged native ``a:custGeom`` metadata, or mark it stale."""
    kind = elem.get('data-pptx-geometry-kind')
    if kind is None:
        return None
    if kind != 'custom':
        raise ValueError(f'Unsupported data-pptx-geometry-kind {kind!r}')
    encoded = elem.get('data-pptx-custgeom')
    expected_hash = elem.get('data-pptx-geometry-sha256')
    if not encoded or not expected_hash:
        raise ValueError(
            'Custom geometry metadata requires data-pptx-custgeom and '
            'data-pptx-geometry-sha256'
        )
    actual_hash = hashlib.sha256(
        (elem.get('d') or '').strip().encode('utf-8')
    ).hexdigest()
    if actual_hash != expected_hash:
        return None
    try:
        raw = base64.b64decode(encoded, validate=True)
        custom = ET.fromstring(raw)
        decoded = raw.decode('utf-8')
    except (ValueError, binascii.Error, UnicodeDecodeError, ET.ParseError) as exc:
        raise ValueError(f'Invalid custom geometry metadata: {exc}') from exc
    if custom.tag != (
        '{http://schemas.openxmlformats.org/drawingml/2006/main}custGeom'
    ):
        raise ValueError('Custom geometry metadata payload must be a:custGeom')
    if has_relationship_attributes(custom):
        raise ValueError(
            'Custom geometry metadata must not contain relationship attributes'
        )
    return decoded


def _shape_xfrm_from_preset_frame(
    elem: ET.Element,
    ctx: ConvertContext,
    fallback_raw_rect: tuple[float, float, float, float],
    fallback_resolved_rect: tuple[float, float, float, float],
    transform: str | None,
) -> tuple[str, int, int, int, int, tuple[int, int, int, int]]:
    """Use the preserved logical frame for native preset size when present."""
    prst, _guides, frame = _parse_preset_geometry_metadata(elem)
    if frame is None:
        raw_x, raw_y, raw_w, raw_h = fallback_raw_rect
        x, y, w, h = fallback_resolved_rect
    else:
        raw_x, raw_y, raw_w, raw_h = frame
        x = ctx_x(raw_x, ctx)
        y = ctx_y(raw_y, ctx)
        w = ctx_w(raw_w, ctx)
        h = ctx_h(raw_h, ctx)
    preserves_zero_axis = (
        elem.get('data-pptx-object') == 'connector'
        or prst in CONNECTOR_PRESET_TYPES
    )
    xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = _shape_xfrm_from_svg_rect(
        ctx,
        raw_x,
        raw_y,
        raw_w,
        raw_h,
        x,
        y,
        w,
        h,
        transform,
        preserve_degenerate_axes=preserves_zero_axis,
    )
    if not preserves_zero_axis:
        ext_cx = max(ext_cx, 1)
        ext_cy = max(ext_cy, 1)
    bounds_emu = (
        bounds_emu[0],
        bounds_emu[1],
        max(bounds_emu[2], off_x + ext_cx),
        max(bounds_emu[3], off_y + ext_cy),
    )
    return xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu


def _pathlike_preset_xfrm(
    elem: ET.Element,
    ctx: ConvertContext,
    transform: str | None,
    min_x: float,
    min_y: float,
    width: float,
    height: float,
) -> tuple[str, int, int, int, int, tuple[int, int, int, int]]:
    """Resolve a path-like preset xfrm from its logical frame or visual bounds."""
    _prst, _guides, frame = _parse_preset_geometry_metadata(elem)
    if frame is None:
        if _uses_full_transform(ctx, transform):
            tag = elem.tag.rsplit('}', 1)[-1]
            raise ValueError(
                f'Transformed preset-bearing <{tag}> requires data-pptx-frame '
                'to preserve its logical size'
            )
        off_x = px_to_emu(min_x)
        off_y = px_to_emu(min_y)
        ext_cx = max(px_to_emu(width), 1)
        ext_cy = max(px_to_emu(height), 1)
        return (
            '',
            off_x,
            off_y,
            ext_cx,
            ext_cy,
            (off_x, off_y, off_x + ext_cx, off_y + ext_cy),
        )
    return _shape_xfrm_from_preset_frame(
        elem,
        ctx,
        (0.0, 0.0, 1.0, 1.0),
        (min_x, min_y, width, height),
        transform,
    )


def _build_round_rect_custgeom(w: float, h: float, rx: float, ry: float) -> str:
    """Build a DrawingML ``custGeom`` for a rectangle with elliptical corners.

    Used when ``<rect>`` has rx ≠ ry, which DrawingML's preset ``roundRect``
    cannot express (the preset takes a single ``adj`` shared by all four
    corners and is implicitly symmetric). Each 90° elliptical arc is
    approximated by one cubic Bézier — within 0.03% of the true ellipse, far
    below any visible threshold at slide resolution.

    Trade-off vs. the symmetric ``prstGeom roundRect`` path: this geometry
    is custom, so PowerPoint's yellow corner-radius handle is gone and the
    shape can no longer be retuned in-place. That matches the underlying
    reality — rx ≠ ry has no single "radius" to drag — and remains far
    better than the previous behaviour (silently dropping all corners and
    rendering a hard rectangle).

    Args:
        w, h:   Pixel dimensions of the rectangle (post ctx-scale).
        rx, ry: Pixel corner radii along x and y. Will be clamped to half
                of w / h respectively per the SVG spec.

    Returns:
        A complete ``<a:custGeom>...</a:custGeom>`` XML string. Coordinates
        are emitted in EMU within a path-local coordinate system whose
        ``w`` / ``h`` equal the rectangle's pixel-converted dimensions.
    """
    # Clamp radii (SVG spec): rx > w/2 collapses to a half-circle end.
    rx = min(max(rx, 0.0), w / 2)
    ry = min(max(ry, 0.0), h / 2)

    width_emu = px_to_emu(w)
    height_emu = px_to_emu(h)
    rx_emu = px_to_emu(rx)
    ry_emu = px_to_emu(ry)

    cx_off = int(round(rx_emu * _BEZIER_QUARTER_K))
    cy_off = int(round(ry_emu * _BEZIER_QUARTER_K))

    def pt(x: int, y: int) -> str:
        return f'<a:pt x="{x}" y="{y}"/>'

    def cubic(c1: tuple[int, int], c2: tuple[int, int], end: tuple[int, int]) -> str:
        return (
            f'<a:cubicBezTo>{pt(*c1)}{pt(*c2)}{pt(*end)}</a:cubicBezTo>'
        )

    # Path traversed clockwise, starting just past the top-left corner.
    parts = [
        f'<a:moveTo>{pt(rx_emu, 0)}</a:moveTo>',
        f'<a:lnTo>{pt(width_emu - rx_emu, 0)}</a:lnTo>',
        # Top-right corner: (W-Rx, 0) → (W, Ry)
        cubic(
            (width_emu - rx_emu + cx_off, 0),
            (width_emu, ry_emu - cy_off),
            (width_emu, ry_emu),
        ),
        f'<a:lnTo>{pt(width_emu, height_emu - ry_emu)}</a:lnTo>',
        # Bottom-right corner: (W, H-Ry) → (W-Rx, H)
        cubic(
            (width_emu, height_emu - ry_emu + cy_off),
            (width_emu - rx_emu + cx_off, height_emu),
            (width_emu - rx_emu, height_emu),
        ),
        f'<a:lnTo>{pt(rx_emu, height_emu)}</a:lnTo>',
        # Bottom-left corner: (Rx, H) → (0, H-Ry)
        cubic(
            (rx_emu - cx_off, height_emu),
            (0, height_emu - ry_emu + cy_off),
            (0, height_emu - ry_emu),
        ),
        f'<a:lnTo>{pt(0, ry_emu)}</a:lnTo>',
        # Top-left corner: (0, Ry) → (Rx, 0)
        cubic(
            (0, ry_emu - cy_off),
            (rx_emu - cx_off, 0),
            (rx_emu, 0),
        ),
        '<a:close/>',
    ]

    path_xml = '\n'.join(parts)
    return (
        '<a:custGeom>'
        '<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
        '<a:rect l="l" t="t" r="r" b="b"/>'
        f'<a:pathLst><a:path w="{width_emu}" h="{height_emu}">'
        f'\n{path_xml}\n'
        '</a:path></a:pathLst>'
        '</a:custGeom>'
    )


def convert_rect(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <rect> to DrawingML shape.

    Symmetric rounded corners (rx == ry) are emitted as ``prstGeom roundRect``
    so PowerPoint treats them as a native rounded-rectangle shape: the yellow
    adjustment handle stays draggable, and "Reset Picture / Shape" works as
    expected. Elliptical corners (rx != ry) fall back to plain rect geometry
    for now — current corpora contain none, but the branch keeps callers from
    silently producing distorted custom geometry if one ever appears.
    """
    raw_x = svg_length_x(elem.get('x'), ctx)
    raw_y = svg_length_y(elem.get('y'), ctx)
    raw_w = svg_length_x(elem.get('width'), ctx)
    raw_h = svg_length_y(elem.get('height'), ctx)
    x = ctx_x(raw_x, ctx)
    y = ctx_y(raw_y, ctx)
    w = ctx_w(raw_w, ctx)
    h = ctx_h(raw_h, ctx)
    preset_geom = _build_preset_geom_from_meta(elem)

    if w <= 0 or h <= 0:
        return None

    # SVG spec: when only one of rx/ry is specified, the other inherits its
    # value. Real-world svg_output decks always write only `rx`, so ry must
    # be inferred to keep round corners from collapsing to zero on one axis.
    rx_attr = elem.get('rx')
    ry_attr = elem.get('ry')
    rx_raw = svg_length_x(rx_attr, ctx) if rx_attr is not None else 0.0
    ry_raw = svg_length_y(ry_attr, ctx) if ry_attr is not None else 0.0
    if rx_attr is not None and ry_attr is None:
        ry_raw = rx_raw
    elif ry_attr is not None and rx_attr is None:
        rx_raw = ry_raw
    rx = rx_raw * ctx.scale_x
    ry = ry_raw * ctx.scale_y

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_effect_xml(
            ctx.defs[filt_id],
            get_element_opacity(elem, ctx),
        )

    transform = elem.get('transform')

    if preset_geom is not None:
        geom = preset_geom
    elif rx > 0 and abs(rx - ry) < 0.5:
        # Symmetric corners → native PowerPoint rounded rectangle. adj is
        # the corner radius as a fraction of the shorter side, in 1/1000-
        # percent units, capped at 50000 (= radius equals half the shorter
        # side, i.e. capsule end).
        short_side = min(w, h)
        radius = min(rx, short_side / 2)
        adj = max(0, min(50000, int(round(radius / short_side * 100000))))
        geom = (
            '<a:prstGeom prst="roundRect">'
            f'<a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst>'
            '</a:prstGeom>'
        )
    elif rx > 0 or ry > 0:
        # Asymmetric corners (rx != ry) → DrawingML has no preset for
        # elliptical-corner rectangles, so emit a custGeom with one cubic
        # Bézier per 90° arc. We lose the prstGeom roundRect adjustment
        # handle, but symmetric and asymmetric cases now both render with
        # rounded corners instead of one of them silently flattening to
        # a hard rectangle.
        geom = _build_round_rect_custgeom(w, h, rx, ry)
    else:
        geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'

    shape_id = _claim_element_shape_id(elem, ctx)
    if preset_geom is not None:
        xfrm = _shape_xfrm_from_preset_frame(
            elem,
            ctx,
            (raw_x, raw_y, raw_w, raw_h),
            (x, y, w, h),
            transform,
        )
    else:
        xfrm = _shape_xfrm_from_svg_rect(
            ctx,
            raw_x,
            raw_y,
            raw_w,
            raw_h,
            x,
            y,
            w,
            h,
            transform,
        )
    xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = xfrm
    return ShapeResult(
        xml=_wrap_geometry_object(
            elem,
            ctx,
            shape_id, f'Rectangle {shape_id}',
            off_x, off_y, ext_cx, ext_cy,
            geom, fill, stroke, effect, xfrm_attr=xfrm_attr,
        ),
        bounds_emu=bounds_emu,
    )


# ---------------------------------------------------------------------------
# circle (including donut-chart arc segments)
# ---------------------------------------------------------------------------

def _build_arc_ring_path(
    cx: float, cy: float, r: float,
    stroke_width: float,
    dash_len: float, dash_offset: float,
    rotate_deg: float,
    sx: float, sy: float,
) -> tuple[str, int, int, int, int]:
    """Build a filled annular-sector (donut segment) as DrawingML custGeom.

    SVG donut charts use stroke-dasharray on a circle to draw arc segments.
    DrawingML cannot reproduce this, so we convert each arc segment into a
    filled ring shape (outer arc -> line -> inner arc -> close).

    Returns:
        (geom_xml, min_x_emu, min_y_emu, w_emu, h_emu).
    """
    circumference = 2 * math.pi * r
    if circumference <= 0:
        return '', 0, 0, 0, 0

    start_frac = -dash_offset / circumference
    end_frac = start_frac + dash_len / circumference

    start_angle = start_frac * 2 * math.pi + math.radians(rotate_deg)
    end_angle = end_frac * 2 * math.pi + math.radians(rotate_deg)

    half_sw = stroke_width / 2
    r_outer = r + half_sw
    r_inner = r - half_sw

    num_segments = max(16, int(abs(end_angle - start_angle) / (math.pi / 32)))
    angles = [
        start_angle + (end_angle - start_angle) * i / num_segments
        for i in range(num_segments + 1)
    ]

    outer_pts = [(cx + r_outer * math.sin(a), cy - r_outer * math.cos(a)) for a in angles]
    inner_pts = [(cx + r_inner * math.sin(a), cy - r_inner * math.cos(a)) for a in reversed(angles)]

    all_pts = [(px * sx, py * sy) for px, py in outer_pts + inner_pts]

    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x
    height = max_y - min_y

    if width < 0.5 or height < 0.5:
        return '', 0, 0, 0, 0

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    lines: list[str] = []
    for i, (px, py) in enumerate(all_pts):
        lx = px_to_emu(px - min_x)
        ly = px_to_emu(py - min_y)
        if i == 0:
            lines.append(f'<a:moveTo><a:pt x="{lx}" y="{ly}"/></a:moveTo>')
        else:
            lines.append(f'<a:lnTo><a:pt x="{lx}" y="{ly}"/></a:lnTo>')
    lines.append('<a:close/>')

    path_xml = '\n'.join(lines)
    geom = f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    return geom, px_to_emu(min_x), px_to_emu(min_y), w_emu, h_emu


def _is_donut_circle(elem: ET.Element, ctx: ConvertContext) -> bool:
    """Detect if a circle uses stroke-dasharray to simulate an arc segment."""
    dasharray = _get_attr(elem, 'stroke-dasharray', ctx)
    stroke = _get_attr(elem, 'stroke', ctx)
    fill = _get_attr(elem, 'fill', ctx)
    sw = svg_length_size(_get_attr(elem, 'stroke-width', ctx), ctx, 0)
    r = svg_length_size(elem.get('r'), ctx, 0)
    return is_thick_circle_shorthand(dasharray, stroke, fill, sw, r)


def convert_circle(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <circle> to DrawingML ellipse or donut-arc shape."""
    cx_ = svg_length_x(elem.get('cx'), ctx)
    cy_ = svg_length_y(elem.get('cy'), ctx)
    r = svg_length_size(elem.get('r'), ctx)
    preset_geom = _build_preset_geom_from_meta(elem)

    if r <= 0:
        return None

    # --- Donut-chart arc segment detection ---
    if preset_geom is None and _is_donut_circle(elem, ctx):
        dasharray = _get_attr(elem, 'stroke-dasharray', ctx)
        parsed_dasharray = parse_project_stroke_dasharray(
            dasharray,
            allow_zero_gap=True,
        )
        if parsed_dasharray is None:
            raise ValueError('Thick-circle arc requires one dash/gap pair')
        _preset, dash_values = parsed_dasharray
        dash_len = dash_values[0]
        raw_dash_offset = elem.get('stroke-dashoffset')
        dash_offset = (
            parse_project_geometry_length(
                raw_dash_offset,
                'stroke-dashoffset',
            )
            if raw_dash_offset is not None else 0.0
        )
        stroke_width = svg_length_size(_get_attr(elem, 'stroke-width', ctx), ctx, 1)

        rotate_deg = 0.0
        transform = elem.get('transform', '')
        if transform:
            operations = parse_transform_operations(transform)
            if len(operations) != 1 or operations[0][0] != 'rotate':
                raise ValueError(
                    'Thick-circle arc transform must be one rotate operation'
                )
            rotate_deg = operations[0][1][0]

        geom, min_x, min_y, w_emu, h_emu = _build_arc_ring_path(
            ctx_x(cx_, ctx) / ctx.scale_x,
            ctx_y(cy_, ctx) / ctx.scale_y,
            r, stroke_width, dash_len, dash_offset, rotate_deg,
            ctx.scale_x, ctx.scale_y,
        )
        if not geom:
            return None

        # Use the stroke color/gradient as fill for the arc shape
        stroke_val = _get_attr(elem, 'stroke', ctx)
        op = get_stroke_opacity(elem, ctx)
        grad_id = resolve_url_id(stroke_val) if stroke_val else None
        if grad_id and grad_id in ctx.defs:
            fill = build_gradient_fill(
                ctx.defs[grad_id],
                op,
                ctx.theme_color_spec,
                "fill",
            )
        elif stroke_val:
            color, color_alpha = parse_svg_color(stroke_val)
            fill = (
                build_solid_fill(
                    color,
                    combine_opacity(op, color_alpha),
                    ctx.theme_color_spec,
                    "fill",
                )
                if color else '<a:noFill/>'
            )
        else:
            fill = '<a:noFill/>'

        stroke_xml = '<a:ln><a:noFill/></a:ln>'

        effect = ''
        filt_id = get_effective_filter_id(elem, ctx)
        if filt_id and filt_id in ctx.defs:
            effect = build_effect_xml(
                ctx.defs[filt_id],
                get_element_opacity(elem, ctx),
            )

        shape_id = _claim_element_shape_id(elem, ctx)
        return ShapeResult(
            xml=_wrap_shape(
                shape_id, f'Arc {shape_id}',
                min_x, min_y, w_emu, h_emu,
                geom, fill, stroke_xml, effect,
            ),
            bounds_emu=(min_x, min_y, min_x + w_emu, min_y + h_emu),
        )

    # --- Normal circle ---
    transform = elem.get('transform')
    cx_s = ctx_x(cx_, ctx)
    cy_s = ctx_y(cy_, ctx)
    r_x = r * ctx.scale_x
    r_y = r * ctx.scale_y

    x = cx_s - r_x
    y = cy_s - r_y
    w = r_x * 2
    h = r_y * 2

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_effect_xml(
            ctx.defs[filt_id],
            get_element_opacity(elem, ctx),
        )

    geom = preset_geom or '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    shape_id = _claim_element_shape_id(elem, ctx)
    if preset_geom is not None:
        xfrm = _shape_xfrm_from_preset_frame(
            elem,
            ctx,
            (cx_ - r, cy_ - r, r * 2, r * 2),
            (x, y, w, h),
            transform,
        )
    else:
        xfrm = _shape_xfrm_from_svg_rect(
            ctx,
            cx_ - r,
            cy_ - r,
            r * 2,
            r * 2,
            x,
            y,
            w,
            h,
            transform,
        )
    xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = xfrm
    return ShapeResult(
        xml=_wrap_geometry_object(
            elem,
            ctx,
            shape_id, f'Ellipse {shape_id}',
            off_x, off_y, ext_cx, ext_cy,
            geom, fill, stroke, effect, xfrm_attr=xfrm_attr,
        ),
        bounds_emu=bounds_emu,
    )


# ---------------------------------------------------------------------------
# line
# ---------------------------------------------------------------------------

def convert_line(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <line> to DrawingML shape.

    Lines with marker-start / marker-end are converted using the 'line' preset
    geometry (prstGeom prst="line") so that PowerPoint renders native arrow
    heads (headEnd / tailEnd) correctly.  Plain lines (no markers) continue to
    use custom geometry which is sufficient and avoids flipH/flipV complexity.
    """
    preset_geom = _build_preset_geom_from_meta(elem)
    transform = elem.get('transform')
    raw_x1 = svg_length_x(elem.get('x1'), ctx)
    raw_y1 = svg_length_y(elem.get('y1'), ctx)
    raw_x2 = svg_length_x(elem.get('x2'), ctx)
    raw_y2 = svg_length_y(elem.get('y2'), ctx)
    x1, y1 = _transformed_point(
        ctx,
        raw_x1,
        raw_y1,
        transform,
    )
    x2, y2 = _transformed_point(
        ctx,
        raw_x2,
        raw_y2,
        transform,
    )

    min_x = min(x1, x2)
    min_y = min(y1, y2)

    stroke_op = get_stroke_opacity(elem, ctx)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    shape_id = _claim_element_shape_id(elem, ctx)
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)

    # Determine if this line carries arrow markers.
    has_marker = bool(
        _get_attr(elem, 'marker-start', ctx) or
        _get_attr(elem, 'marker-end', ctx)
    )

    if preset_geom is not None:
        # The preserved logical frame, not the rendered stroke/marker bounds,
        # owns the native shape size. Horizontal/vertical connectors retain a
        # one-EMU extent on the degenerate axis as required by DrawingML.
        raw_w = abs(raw_x2 - raw_x1)
        raw_h = abs(raw_y2 - raw_y1)
        resolved_w = abs(x2 - x1)
        resolved_h = abs(y2 - y1)
        xfrm_attr, off_x, off_y, w_emu, h_emu, bounds_emu = (
            _shape_xfrm_from_preset_frame(
                elem,
                ctx,
                (min(raw_x1, raw_x2), min(raw_y1, raw_y2), raw_w, raw_h),
                (min_x, min_y, resolved_w, resolved_h),
                transform,
            )
        )
        if not _uses_full_transform(ctx, transform):
            flip_attrs = []
            if x1 > x2:
                flip_attrs.append(' flipH="1"')
            if y1 > y2:
                flip_attrs.append(' flipV="1"')
            xfrm_attr += ''.join(flip_attrs)
        xml = _wrap_geometry_object(
            elem,
            ctx,
            shape_id,
            f'Connector {shape_id}' if elem.get('data-pptx-object') == 'connector'
            else f'Line {shape_id}',
            off_x,
            off_y,
            w_emu,
            h_emu,
            preset_geom,
            '<a:noFill/>',
            stroke,
            xfrm_attr=xfrm_attr,
        )
        return ShapeResult(xml=xml, bounds_emu=bounds_emu)

    if has_marker:
        # ----------------------------------------------------------------
        # Preset geometry approach: prstGeom prst="line"
        # PowerPoint only renders headEnd / tailEnd on lines whose geometry
        # it can intrinsically understand as a "line" (i.e. preset or
        # connector shapes).  Custom geometry shapes silently ignore
        # headEnd / tailEnd in most PowerPoint versions.
        #
        # The "line" preset draws from (0,0) to (w,h).
        #   headEnd  → placed at the start of the line = (x1, y1)
        #   tailEnd  → placed at the end   of the line = (x2, y2)
        # We set flipH / flipV so that the preset start/end align with the
        # original SVG endpoints:
        #   default  (no flip)  : top-left  → bottom-right  (x1≤x2, y1≤y2)
        #   flipH               : top-right → bottom-left   (x1>x2, y1≤y2)
        #   flipV               : bottom-left → top-right   (x1≤x2, y1>y2)
        #   flipH + flipV       : bottom-right → top-left   (x1>x2, y1>y2)
        # ----------------------------------------------------------------
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        # DrawingML requires ext cx/cy ≥ 1 EMU
        w_emu = px_to_emu(w) if w > 0 else 1
        h_emu = px_to_emu(h) if h > 0 else 1

        flip_h = x1 > x2
        flip_v = y1 > y2
        flip_attr = ''
        if flip_h and flip_v:
            flip_attr = ' flipH="1" flipV="1"'
        elif flip_h:
            flip_attr = ' flipH="1"'
        elif flip_v:
            flip_attr = ' flipV="1"'

        xml = _wrap_shape(
            shape_id,
            f'Line {shape_id}',
            off_x,
            off_y,
            w_emu,
            h_emu,
            '<a:prstGeom prst="line"><a:avLst/></a:prstGeom>',
            '<a:noFill/>',
            stroke,
            xfrm_attr=flip_attr,
        )
    else:
        # ----------------------------------------------------------------
        # Custom geometry (original behaviour) for plain lines.
        # ----------------------------------------------------------------
        w = max(abs(x2 - x1), 1)
        h = max(abs(y2 - y1), 1)
        w_emu = px_to_emu(w)
        h_emu = px_to_emu(h)

        lx1 = px_to_emu(x1 - min_x)
        ly1 = px_to_emu(y1 - min_y)
        lx2 = px_to_emu(x2 - min_x)
        ly2 = px_to_emu(y2 - min_y)

        geom = (
            f'<a:custGeom>'
            f'<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
            f'<a:rect l="l" t="t" r="r" b="b"/>'
            f'<a:pathLst><a:path w="{w_emu}" h="{h_emu}">'
            f'<a:moveTo><a:pt x="{lx1}" y="{ly1}"/></a:moveTo>'
            f'<a:lnTo><a:pt x="{lx2}" y="{ly2}"/></a:lnTo>'
            f'</a:path></a:pathLst>'
            f'</a:custGeom>'
        )
        xml = _wrap_shape(
            shape_id, f'Line {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, '<a:noFill/>', stroke,
        )

    return ShapeResult(xml=xml, bounds_emu=(off_x, off_y, off_x + w_emu, off_y + h_emu))


# ---------------------------------------------------------------------------
# path
# ---------------------------------------------------------------------------

def convert_path(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <path> to DrawingML custom geometry shape."""
    preset_geom = _build_preset_geom_from_meta(elem)
    preserved_custom_geom = _build_preserved_custom_geom(elem)
    native_geom = preset_geom or preserved_custom_geom
    d = elem.get('d', '')
    if not d:
        if native_geom is not None:
            raise ValueError('Native-geometry <path> requires a non-empty d attribute')
        return None

    commands = parse_svg_path(d)
    commands = svg_path_to_absolute(commands)
    commands = normalize_path_commands(commands)

    transform = elem.get('transform')
    if _uses_full_transform(ctx, transform):
        commands = _transform_path_commands(commands, _combined_transform_matrix(ctx, transform))
        path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
            commands, 0, 0, 1.0, 1.0,
        )
    else:
        path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
            commands, ctx.translate_x, ctx.translate_y,
            ctx.scale_x, ctx.scale_y,
        )

    if not path_xml:
        return None

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    geom = native_geom
    if geom is None:
        geom = f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_effect_xml(
            ctx.defs[filt_id],
            get_element_opacity(elem, ctx),
        )

    shape_id = _claim_element_shape_id(elem, ctx)
    xfrm_attr = ''
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)
    bounds_emu = (off_x, off_y, off_x + w_emu, off_y + h_emu)
    if native_geom is not None:
        xfrm = _pathlike_preset_xfrm(
            elem,
            ctx,
            transform,
            min_x,
            min_y,
            width,
            height,
        )
        xfrm_attr, off_x, off_y, w_emu, h_emu, bounds_emu = xfrm
    return ShapeResult(
        xml=_wrap_geometry_object(
            elem,
            ctx,
            shape_id, f'Freeform {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, fill, stroke, effect, xfrm_attr=xfrm_attr,
        ),
        bounds_emu=bounds_emu,
    )


# ---------------------------------------------------------------------------
# polygon / polyline
# ---------------------------------------------------------------------------

def convert_polygon(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <polygon> to DrawingML custom geometry shape."""
    preset_geom = _build_preset_geom_from_meta(elem)
    points = parse_svg_points(elem.get('points', ''), min_points=3)

    commands = [PathCommand('M', [points[0][0], points[0][1]])]
    for px_, py_ in points[1:]:
        commands.append(PathCommand('L', [px_, py_]))
    commands.append(PathCommand('Z', []))

    transform = elem.get('transform')
    if _uses_full_transform(ctx, transform):
        commands = _transform_path_commands(commands, _combined_transform_matrix(ctx, transform))
        path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
            commands, 0, 0, 1.0, 1.0,
        )
    else:
        path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
            commands, ctx.translate_x, ctx.translate_y,
            ctx.scale_x, ctx.scale_y,
        )

    if not path_xml:
        return None

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    geom = preset_geom or f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    shape_id = _claim_element_shape_id(elem, ctx)
    xfrm_attr = ''
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)
    bounds_emu = (off_x, off_y, off_x + w_emu, off_y + h_emu)
    if preset_geom is not None:
        xfrm = _pathlike_preset_xfrm(
            elem,
            ctx,
            transform,
            min_x,
            min_y,
            width,
            height,
        )
        xfrm_attr, off_x, off_y, w_emu, h_emu, bounds_emu = xfrm
    return ShapeResult(
        xml=_wrap_geometry_object(
            elem,
            ctx,
            shape_id, f'Polygon {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, fill, stroke, xfrm_attr=xfrm_attr,
        ),
        bounds_emu=bounds_emu,
    )


def convert_polyline(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <polyline> to DrawingML custom geometry shape."""
    preset_geom = _build_preset_geom_from_meta(elem)
    points = parse_svg_points(elem.get('points', ''), min_points=2)

    commands = [PathCommand('M', [points[0][0], points[0][1]])]
    for px_, py_ in points[1:]:
        commands.append(PathCommand('L', [px_, py_]))

    transform = elem.get('transform')
    if _uses_full_transform(ctx, transform):
        commands = _transform_path_commands(commands, _combined_transform_matrix(ctx, transform))
        path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
            commands, 0, 0, 1.0, 1.0,
        )
    else:
        path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
            commands, ctx.translate_x, ctx.translate_y,
            ctx.scale_x, ctx.scale_y,
        )

    if not path_xml:
        return None

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    geom = preset_geom or f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    shape_id = _claim_element_shape_id(elem, ctx)
    xfrm_attr = ''
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)
    bounds_emu = (off_x, off_y, off_x + w_emu, off_y + h_emu)
    if preset_geom is not None:
        xfrm = _pathlike_preset_xfrm(
            elem,
            ctx,
            transform,
            min_x,
            min_y,
            width,
            height,
        )
        xfrm_attr, off_x, off_y, w_emu, h_emu, bounds_emu = xfrm
    return ShapeResult(
        xml=_wrap_geometry_object(
            elem,
            ctx,
            shape_id, f'Polyline {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, '<a:noFill/>', stroke, xfrm_attr=xfrm_attr,
        ),
        bounds_emu=bounds_emu,
    )


# ---------------------------------------------------------------------------
# text
# ---------------------------------------------------------------------------

_SERIF_WIDTH_FAMILIES = {
    'book antiqua',
    'cambria',
    'fangsong',
    'garamond',
    'georgia',
    'kaiti',
    'palatino',
    'palatino linotype',
    'serif',
    'simsun',
    'songti',
    'times',
    'times new roman',
}

_TEXTBOX_PADDING_MIN_PX = 0.5
_TEXTBOX_PADDING_MAX_PX = 2.0
_TEXTBOX_PADDING_RATIO = 0.04
# Single-line auto-fit headroom interpolates between a low-caps base and an
# all-caps ceiling by the fraction of cased letters that are uppercase. The
# crude per-char width estimate undercounts capitals most, so all-caps lines
# need the ceiling to keep wrap-ignoring renderers (LibreOffice) from folding;
# mixed-case titles only need the base, so they no longer inherit the worst-
# case width. Values are calibrated against LibreOffice renders of all-caps
# bold lines (the case the per-char estimate undercounts most) with bases left
# above the mixed-case and CJK render ratios; exact ratios shift with the
# renderer's font substitution, so these carry deliberate margin rather than
# tracking one environment's numbers.
_TEXT_WIDTH_HEADROOM_BASE = 1.06
_TEXT_WIDTH_HEADROOM_CAPS = 1.12
_SERIF_TEXT_WIDTH_HEADROOM_BASE = 1.12
_SERIF_TEXT_WIDTH_HEADROOM_CAPS = 1.36
_TEXT_BULLET_MARKERS = {
    '·': '•',
    '•': '•',
    '●': '●',
    '▪': '▪',
    '■': '■',
    '◆': '◆',
    '◇': '◇',
    '◦': '◦',
    '‣': '‣',
}
_TEXT_BULLET_RE = re.compile(
    r'^(?P<prefix>\s*)(?P<marker>[·•●▪■◆◇◦‣])(?P<space>\s*)'
)


def _normalize_text_run_whitespace(
    runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply the shared whitespace contract without losing run ownership."""
    normalized: list[dict[str, Any]] = []
    segments = [
        (str(run.get('_xml_space', 'default')), str(run.get('text', '')))
        for run in runs
    ]
    for index, text in normalize_project_text_segments(segments):
        run = {**runs[index], 'text': text}
        run.pop('_xml_space', None)
        normalized.append(run)
    return normalized


def _letter_spacing_to_drawingml_spc(letter_spacing_px: float) -> str:
    """Convert SVG px letter spacing into DrawingML rPr@spc."""
    spacing = drawingml_letter_spacing(letter_spacing_px)
    if spacing == 0:
        return ''
    return f' spc="{spacing}"'


def _is_serif_run(run: dict[str, Any]) -> bool:
    """Return whether a text run uses a serif-like family."""
    for family in str(run.get('font_family', '')).split(','):
        name = family.strip().strip("'\"").lower()
        if not name or name in {'sans-serif', 'sans serif'}:
            continue
        if name in _SERIF_WIDTH_FAMILIES:
            return True
        if 'serif' in name and 'sans' not in name:
            return True
    return False


def _estimate_run_text_width(run: dict[str, Any]) -> float:
    """Estimate one run using the metrics actually emitted to DrawingML."""
    text = str(run.get('text', ''))
    font_size_px = (
        font_px_to_hpt(float(run.get('font_size', 16)))
        / FONT_PX_TO_HUNDREDTHS_PT
    )
    cluster_widths = estimate_text_cluster_widths(
        text,
        font_size_px,
        str(run.get('font_weight', '400')),
    )
    letter_spacing_px = (
        drawingml_letter_spacing(
            float(run.get('letter_spacing', 0.0) or 0.0)
        )
        / FONT_PX_TO_HUNDREDTHS_PT
    )
    return sum(cluster_widths) + letter_spacing_px * max(
        len(cluster_widths) - 1,
        0,
    )


def validate_text_run_advances(runs: list[dict[str, Any]]) -> None:
    """Reject negative tracking that reverses or collapses one output run."""
    for run in runs:
        text = str(run.get('text', ''))
        letter_spacing = float(run.get('letter_spacing', 0.0) or 0.0)
        if len(split_project_text_clusters(text)) < 2 or letter_spacing >= 0:
            continue
        advance = _estimate_run_text_width(run)
        if advance > 0:
            continue
        snippet = re.sub(r'\s+', ' ', text)
        raise ValueError(
            'negative letter-spacing produces a non-positive DrawingML '
            f'text-run advance for {snippet!r} (advance={advance:g}px)'
        )


def _uppercase_fraction(runs: list[dict[str, Any]]) -> float:
    """Fraction of cased letters across ``runs`` that are uppercase.

    Caseless scripts (CJK, digits, punctuation) are ignored, so a Chinese or
    numeric line reports 0.0 and takes the low-caps headroom base.
    """
    upper = 0
    cased = 0
    for run in runs:
        for ch in str(run.get('text', '')):
            if ch.lower() != ch.upper():
                cased += 1
                if ch.isupper():
                    upper += 1
    if not cased:
        return 0.0
    return upper / cased


def _estimate_text_runs_width(
    runs: list[dict[str, Any]],
    *,
    include_headroom: bool = True,
) -> float:
    """Estimate a line of text runs.

    ``include_headroom`` is useful for single-line auto-fit boxes where a
    renderer that measures text slightly wider would otherwise wrap. The
    headroom scales with the line's uppercase fraction: all-caps lines (whose
    width the per-char estimate undercounts most) get the full ceiling, while
    mixed-case titles take a small base instead of inheriting the worst case.
    Paragraph boxes use this value as a wrapping constraint, so adding headroom
    there stretches the merged text frame beyond the author's source line width.
    """
    width = sum(_estimate_run_text_width(run) for run in runs)
    if not include_headroom:
        return width
    caps = _uppercase_fraction(runs)
    if any(_is_serif_run(run) for run in runs):
        base, ceiling = _SERIF_TEXT_WIDTH_HEADROOM_BASE, _SERIF_TEXT_WIDTH_HEADROOM_CAPS
    else:
        base, ceiling = _TEXT_WIDTH_HEADROOM_BASE, _TEXT_WIDTH_HEADROOM_CAPS
    return width * (base + (ceiling - base) * caps)


def estimate_single_line_text_frame_width(
    runs: list[dict[str, Any]],
) -> float:
    """Estimate the content width used by one generated DrawingML textbox."""
    content_runs, bullet = _extract_text_bullet(runs)
    width = _estimate_text_runs_width(content_runs)
    if bullet:
        font_size = (
            float(content_runs[0].get('font_size', 16))
            if content_runs else 16.0
        )
        width += _bullet_margin_px(bullet, font_size)
    return width


def validate_single_line_text_run_advances(
    runs: list[dict[str, Any]],
) -> None:
    """Validate the runs that remain after single-line bullet promotion."""
    content_runs, _bullet = _extract_text_bullet(runs)
    validate_text_run_advances(content_runs)


def _first_nonspace_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    for run in runs:
        if str(run.get('text', '')).strip():
            return run
    return None


def _strip_leading_chars_from_runs(
    runs: list[dict[str, Any]],
    char_count: int,
) -> list[dict[str, Any]]:
    stripped: list[dict[str, Any]] = []
    remaining = char_count
    for run in runs:
        text = str(run.get('text', ''))
        if remaining >= len(text):
            remaining -= len(text)
            continue
        if remaining > 0:
            text = text[remaining:]
            remaining = 0
        if text:
            stripped.append({**run, 'text': text})
    return stripped


def _take_leading_chars_from_runs(
    runs: list[dict[str, Any]],
    char_count: int,
) -> list[dict[str, Any]]:
    taken: list[dict[str, Any]] = []
    remaining = char_count
    for run in runs:
        if remaining <= 0:
            break
        text = str(run.get('text', ''))
        if remaining >= len(text):
            prefix = text
            remaining -= len(text)
        else:
            prefix = text[:remaining]
            remaining = 0
        if prefix:
            taken.append({**run, 'text': prefix})
    return taken


def _extract_text_bullet(
    runs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Convert a leading text bullet marker into paragraph metadata."""
    full_text = ''.join(str(run.get('text', '')) for run in runs)
    match = _TEXT_BULLET_RE.match(full_text)
    if not match:
        return runs, None
    if not full_text[match.end():].strip():
        return runs, None

    marker = match.group('marker')
    marker_run = _first_nonspace_run(runs) or {}
    prefix_runs = _take_leading_chars_from_runs(runs, match.end())
    replacement_prefix = _TEXT_BULLET_MARKERS.get(marker, marker) + (match.group('space') or ' ')
    replacement_runs = [{**marker_run, 'text': replacement_prefix}] if marker_run else []
    bullet = {
        'char': _TEXT_BULLET_MARKERS.get(marker, marker),
        'fill': marker_run.get('fill'),
        'fill_raw': marker_run.get('fill_raw'),
        'opacity': marker_run.get('opacity'),
        'source_prefix_width_px': _estimate_text_runs_width(prefix_runs, include_headroom=False),
        'margin_px': max(
            _estimate_text_runs_width(replacement_runs, include_headroom=False),
            8.0,
        ),
    }
    stripped = _strip_leading_chars_from_runs(runs, match.end())
    return (stripped or runs), bullet


def _bullet_margin_px(bullet: dict[str, Any], font_size: float) -> float:
    try:
        return float(bullet.get('margin_px', 0.0))
    except (TypeError, ValueError):
        return max(font_size * 0.95, 12.0)


def _bullet_indent_px(bullet: dict[str, Any], font_size: float) -> float:
    return -_bullet_margin_px(bullet, font_size)


def _build_bullet_xml(
    bullet: dict[str, Any] | None,
    ctx: ConvertContext | None,
) -> str:
    if not bullet:
        return ''
    fill = bullet.get('fill')
    fill_raw = bullet.get('fill_raw')
    color, color_alpha = parse_svg_color(
        fill_raw if isinstance(fill_raw, str) else ''
    )
    if color is None and isinstance(fill, str):
        color = parse_hex_color(fill)
    if color:
        opacity = combine_opacity(bullet.get('opacity'), color_alpha)
        alpha_xml = (
            f'<a:alphaMod val="{int(opacity * 100000)}"/>'
            if opacity is not None else ''
        )
        theme_spec = ctx.theme_color_spec if ctx is not None else None
        color_xml = (
            f'<a:buClr>{color_node_xml(color, theme_spec, "text", alpha_xml)}</a:buClr>'
        )
    else:
        color_xml = '<a:buClrTx/>'
    return (
        f'{color_xml}<a:buSzTx/><a:buFontTx/>'
        f'<a:buChar char="{_xml_escape(str(bullet.get("char", "•")))}"/>'
    )


def _paragraph_pr_xml(
    *,
    algn: str,
    font_size: float,
    body_xml: str = '',
    bullet: dict[str, Any] | None = None,
    ctx: ConvertContext | None = None,
) -> str:
    attrs = f'algn="{algn}"'
    if bullet:
        margin = px_to_emu(_bullet_margin_px(bullet, font_size))
        indent = px_to_emu(_bullet_indent_px(bullet, font_size))
        attrs += f' marL="{margin}" indent="{indent}"'
    return f'<a:pPr {attrs}>{body_xml}{_build_bullet_xml(bullet, ctx)}</a:pPr>'


def _estimate_bullet_line_width(
    runs: list[dict[str, Any]],
    default_fonts: dict[str, str],
    ctx: ConvertContext,
) -> float:
    line_runs, bullet = _extract_text_bullet(runs)
    line_runs = _coalesce_text_runs(line_runs, default_fonts, ctx)
    width = _estimate_text_runs_width(line_runs, include_headroom=False)
    if bullet:
        fs_px = float(line_runs[0].get('font_size', 16)) if line_runs else 16.0
        width += _bullet_margin_px(bullet, fs_px)
    return width


def _textbox_padding(font_size: float) -> float:
    """Return small text-frame slack without visibly lengthening the box."""
    return max(
        _TEXTBOX_PADDING_MIN_PX,
        min(_TEXTBOX_PADDING_MAX_PX, font_size * _TEXTBOX_PADDING_RATIO),
    )


def drawingml_text_frame_width_emu(
    text_width: float,
    font_size: float,
) -> int:
    """Return the exact horizontal extent used by a generated text frame."""
    return px_to_emu(text_width + _textbox_padding(font_size) * 2)


def _text_opacity_ratio(value: str | None) -> float:
    """Parse a text opacity component and clamp it to the SVG ``0..1`` range."""
    if value is None:
        return 1.0
    return parse_project_opacity(value)


def _override_run_attrs(
    parent_attrs: dict[str, Any],
    tspan: ET.Element,
    ctx: ConvertContext,
) -> dict[str, Any]:
    """Layer a tspan's styling attributes over the inherited run attrs."""
    run_attrs = dict(parent_attrs)
    inline_style = parse_inline_style(tspan.get('style'))

    def tspan_attr(name: str) -> str | None:
        return inline_style.get(name) or tspan.get(name)

    object_opacity = float(run_attrs.get('_object_opacity', 1.0))
    fill_opacity = float(run_attrs.get('_fill_opacity', 1.0))
    stroke_opacity = float(run_attrs.get('_stroke_opacity', 1.0))
    if tspan_attr('opacity') is not None:
        object_opacity *= _text_opacity_ratio(tspan_attr('opacity'))
    if tspan_attr('fill-opacity') is not None:
        fill_opacity = _text_opacity_ratio(tspan_attr('fill-opacity'))
    if tspan_attr('stroke-opacity') is not None:
        stroke_opacity = _text_opacity_ratio(tspan_attr('stroke-opacity'))
    run_attrs['_object_opacity'] = object_opacity
    run_attrs['_fill_opacity'] = fill_opacity
    run_attrs['_stroke_opacity'] = stroke_opacity
    effective_fill_opacity = object_opacity * fill_opacity
    effective_stroke_opacity = object_opacity * stroke_opacity
    run_attrs['opacity'] = (
        effective_fill_opacity if effective_fill_opacity < 1.0 else None
    )
    run_attrs['stroke_opacity'] = (
        effective_stroke_opacity if effective_stroke_opacity < 1.0 else None
    )

    if tspan_attr('font-weight'):
        run_attrs['font_weight'] = parse_project_font_weight(
            tspan_attr('font-weight')
        ).canonical
    if tspan_attr('fill'):
        child_fill = tspan_attr('fill')
        run_attrs['fill_raw'] = child_fill
        c = parse_hex_color(child_fill)
        if c:
            run_attrs['fill'] = c
    if tspan_attr('stroke'):
        run_attrs['stroke_raw'] = tspan_attr('stroke')
    if tspan_attr('stroke-width'):
        run_attrs['stroke_width'] = parse_svg_length(
            tspan_attr('stroke-width'),
            run_attrs.get('stroke_width', 1.0),
            font_size=float(run_attrs.get('font_size', 16)),
        )
    resolved_font_size = ctx.text_font_sizes.get(id(tspan))
    if resolved_font_size is not None:
        run_attrs['font_size'] = resolved_font_size * ctx.scale_y
    elif tspan_attr('font-size'):
        run_attrs['font_size'] = parse_svg_length(
            tspan_attr('font-size'),
            run_attrs['font_size'],
            font_size=float(run_attrs.get('font_size', 16)),
        )
    if tspan_attr('font-family'):
        run_attrs['font_family'] = tspan_attr('font-family')
    if tspan_attr('font-style'):
        run_attrs['font_style'] = parse_project_font_style(
            tspan_attr('font-style')
        ).canonical
    if tspan_attr('text-decoration'):
        run_attrs['text_decoration'] = parse_project_text_decoration(
            tspan_attr('text-decoration')
        ).canonical
    resolved_letter_spacing = ctx.text_letter_spacings.get(id(tspan))
    if resolved_letter_spacing is not None:
        run_attrs['letter_spacing'] = resolved_letter_spacing * ctx.scale_x
    elif tspan_attr('letter-spacing'):
        run_attrs['letter_spacing'] = parse_project_letter_spacing(
            tspan_attr('letter-spacing'),
            font_size=float(run_attrs.get('font_size', 16)),
            scale_x=float(run_attrs.get('_scale_x', 1.0)),
        ).value
    return run_attrs


def _collect_tspan_runs(
    tspan: ET.Element,
    inherited_attrs: dict[str, Any],
    ctx: ConvertContext,
    inherited_xml_space: str = 'default',
) -> list[dict[str, Any]]:
    """Recursively turn a tspan subtree into runs, propagating styling through nested tspans.

    Order: tspan.text → (each nested child tspan's runs → that child's tail under THIS tspan's attrs).
    """
    runs: list[dict[str, Any]] = []
    own_attrs = _override_run_attrs(inherited_attrs, tspan, ctx)
    own_xml_space = resolve_project_xml_space(tspan, inherited_xml_space)

    if tspan.text:
        runs.append({
            **own_attrs,
            'text': tspan.text,
            '_xml_space': own_xml_space,
        })

    for child in tspan:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag == 'tspan':
            runs.extend(
                _collect_tspan_runs(child, own_attrs, ctx, own_xml_space)
            )
            if child.tail:
                runs.append({
                    **own_attrs,
                    'text': child.tail,
                    '_xml_space': own_xml_space,
                })

    return runs


def _build_text_runs(
    elem: ET.Element,
    parent_attrs: dict[str, Any],
    ctx: ConvertContext,
) -> list[dict[str, Any]]:
    """Build a list of text runs from a <text> element, handling <tspan> children.

    Each run is a dict with keys: text, fill, fill_raw, font_weight,
    font_style, font_family, font_size, letter_spacing. Nested tspans are walked
    recursively so inline format changes inside a tspan still produce distinct runs.
    """
    runs: list[dict[str, Any]] = []
    xml_space = resolve_project_xml_space(elem)

    if elem.text:
        runs.append({
            **parent_attrs,
            'text': elem.text,
            '_xml_space': xml_space,
        })

    for child in elem:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag == 'tspan':
            runs.extend(
                _collect_tspan_runs(child, parent_attrs, ctx, xml_space)
            )
            if child.tail:
                runs.append({
                    **parent_attrs,
                    'text': child.tail,
                    '_xml_space': xml_space,
                })

    return _normalize_text_run_whitespace(runs)


def _build_text_fill_xml(
    fill: str,
    fill_raw: str,
    opacity: float | None,
    ctx: ConvertContext | None,
) -> str:
    """Build DrawingML fill XML for a text run."""
    if fill_raw.strip().lower() in ('none', 'transparent'):
        return '<a:noFill/>'

    grad_id = resolve_url_id(fill_raw)
    if grad_id and ctx and grad_id in ctx.defs:
        return build_gradient_fill(
            ctx.defs[grad_id],
            opacity,
            ctx.theme_color_spec,
            "text",
        )

    parsed_color, color_alpha = parse_svg_color(fill_raw)
    fill = parsed_color or fill
    opacity = combine_opacity(opacity, color_alpha)
    alpha_xml = ''
    if opacity is not None:
        alpha_xml = f'<a:alphaMod val="{int(opacity * 100000)}"/>'
    theme_spec = ctx.theme_color_spec if ctx is not None else None
    return (
        '<a:solidFill>'
        f'{color_node_xml(fill, theme_spec, "text", alpha_xml)}'
        '</a:solidFill>'
    )


def _build_text_outline_xml(
    run: dict[str, Any],
    ctx: ConvertContext | None,
) -> str:
    """Build DrawingML outline XML for a text run from SVG stroke attributes."""
    stroke_raw = run.get('stroke_raw')
    if not stroke_raw or stroke_raw.strip().lower() in ('none', 'transparent'):
        return ''

    color, color_alpha = parse_svg_color(stroke_raw)
    if not color:
        return ''

    stroke_width = _f(str(run.get('stroke_width', 1.0)), 1.0)
    stroke_opacity = combine_opacity(run.get('stroke_opacity'), color_alpha)
    alpha_xml = ''
    if stroke_opacity is not None:
        alpha_xml = f'<a:alphaMod val="{int(stroke_opacity * 100000)}"/>'

    theme_spec = ctx.theme_color_spec if ctx is not None else None
    return (
        f'<a:ln w="{px_to_emu(stroke_width)}">'
        '<a:solidFill>'
        f'{color_node_xml(color, theme_spec, "stroke", alpha_xml)}'
        '</a:solidFill>'
        '</a:ln>'
    )


def _build_run_properties_xml(
    run: dict[str, Any],
    default_fonts: dict[str, str],
    ctx: ConvertContext | None = None,
    effect_xml: str = '',
) -> str:
    """Build the final ``a:rPr`` used to compare and emit one text run."""
    text = str(run['text'])
    fill = run.get('fill', '000000')
    fill_raw = run.get('fill_raw', '')
    fw = run.get('font_weight', '400')
    fs_px = run.get('font_size', 16)
    fstyle = run.get('font_style', '')
    ff = run.get('font_family', '')
    letter_spacing_px = float(run.get('letter_spacing', 0.0) or 0.0)
    opacity = run.get('opacity')

    text_dec = run.get('text_decoration', '')

    # Exported font size = fs_px * FONT_PX_TO_HUNDREDTHS_PT hundredths-of-pt,
    # rounded to **one decimal place of pt** (the nearest 10 hundredths). No 0.5pt
    # / integer snapping — whatever the px works out to is the size, e.g.
    # 18px -> 13.5pt, 24px -> 18.0pt, 42px -> 31.5pt.
    sz = font_px_to_hpt(fs_px)
    b_attr = ' b="1"' if parse_project_font_weight(fw).value else ''
    i_attr = ' i="1"' if fstyle == 'italic' else ''
    underline, strike = parse_project_text_decoration(
        text_dec or 'none'
    ).value
    u_attr = ' u="sng"' if underline else ''
    strike_attr = ' strike="sngStrike"' if strike else ''
    spc_attr = _letter_spacing_to_drawingml_spc(letter_spacing_px)

    fonts = parse_font_family(ff) if ff else default_fonts
    run_fonts = theme_font_tokens(
        fonts,
        ctx.theme_font_spec if ctx is not None else None,
    ) or resolve_text_run_fonts(text, fonts)
    lang = detect_text_lang(text)

    fill_xml = _build_text_fill_xml(fill, fill_raw, opacity, ctx)
    outline_xml = _build_text_outline_xml(run, ctx)

    return f'''<a:rPr lang="{lang}" sz="{sz}"{b_attr}{i_attr}{u_attr}{strike_attr}{spc_attr} dirty="0">
{outline_xml}
{fill_xml}
{effect_xml}
<a:latin typeface="{_xml_escape(run_fonts['latin'])}"/>
<a:ea typeface="{_xml_escape(run_fonts['ea'])}"/>
<a:cs typeface="{_xml_escape(run_fonts['cs'])}"/>
</a:rPr>'''


def _coalesce_text_runs(
    runs: list[dict[str, Any]],
    default_fonts: dict[str, str],
    ctx: ConvertContext | None,
) -> list[dict[str, Any]]:
    """Join adjacent runs that PowerPoint sees as one formatting run."""
    merged: list[dict[str, Any]] = []
    previous_properties: str | None = None
    for run in runs:
        text = str(run.get('text', ''))
        if not text:
            continue
        properties = _build_run_properties_xml(run, default_fonts, ctx)
        if merged and properties == previous_properties:
            candidate = {
                **merged[-1],
                'text': str(merged[-1].get('text', '')) + text,
            }
            candidate_properties = _build_run_properties_xml(
                candidate,
                default_fonts,
                ctx,
            )
            if candidate_properties == previous_properties:
                merged[-1] = candidate
                previous_properties = candidate_properties
                continue
        merged.append({**run, 'text': text})
        previous_properties = properties
    return merged


def _build_run_xml(
    run: dict[str, Any],
    default_fonts: dict[str, str],
    ctx: ConvertContext | None = None,
    effect_xml: str = '',
) -> str:
    """Build a single <a:r> XML from a run dict. Supports gradient fills on text."""
    text = str(run['text'])
    properties_xml = _build_run_properties_xml(
        run,
        default_fonts,
        ctx,
        effect_xml,
    )
    space_attr = ' xml:space="preserve"' if text != text.strip() or '  ' in text else ''

    return f'''<a:r>
{properties_xml}
<a:t{space_attr}>{_xml_escape(text)}</a:t>
</a:r>'''


def convert_text(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <text> to DrawingML text shape with multi-run support."""
    x = ctx_x(svg_length_x(elem.get('x'), ctx), ctx)
    y = ctx_y(svg_length_y(elem.get('y'), ctx), ctx)
    resolved_font_size = ctx.text_font_sizes.get(id(elem))
    font_size = (
        resolved_font_size * ctx.scale_y
        if resolved_font_size is not None
        else parse_svg_length(
            _get_attr(elem, 'font-size', ctx),
            16,
            font_size=16,
        ) * ctx.scale_y
    )
    font_weight = parse_project_font_weight(
        _get_attr(elem, 'font-weight', ctx) or '400'
    ).canonical
    font_family_str = _get_attr(elem, 'font-family', ctx) or ''
    text_anchor = parse_project_text_anchor(
        _get_attr(elem, 'text-anchor', ctx) or 'start'
    ).canonical
    fill_raw = _get_attr(elem, 'fill', ctx) or '#000000'
    fill_color = parse_hex_color(fill_raw) or '000000'
    opacity = get_fill_opacity(elem, ctx)
    object_opacity = get_element_opacity(elem, ctx)
    object_opacity = 1.0 if object_opacity is None else object_opacity
    fill_opacity = _text_opacity_ratio(_get_attr(elem, 'fill-opacity', ctx))
    stroke_raw = _get_attr(elem, 'stroke', ctx) or ''
    stroke_width = svg_length_size(_get_attr(elem, 'stroke-width', ctx), ctx, 1.0)
    stroke_opacity = get_stroke_opacity(elem, ctx)
    stroke_opacity_value = _text_opacity_ratio(_get_attr(elem, 'stroke-opacity', ctx))
    font_style = parse_project_font_style(
        _get_attr(elem, 'font-style', ctx) or 'normal'
    ).canonical
    text_decoration = parse_project_text_decoration(
        _get_attr(elem, 'text-decoration', ctx) or 'none'
    ).canonical
    raw_letter_spacing = _get_attr(elem, 'letter-spacing', ctx)
    resolved_letter_spacing = ctx.text_letter_spacings.get(id(elem))
    if resolved_letter_spacing is not None:
        letter_spacing_px = resolved_letter_spacing * ctx.scale_x
    elif raw_letter_spacing is not None:
        letter_spacing_px = parse_project_letter_spacing(
            raw_letter_spacing,
            font_size=font_size,
            scale_x=ctx.scale_x or 1.0,
        ).value
    else:
        letter_spacing_px = 0.0

    fonts = parse_font_family(font_family_str)

    parent_attrs: dict[str, Any] = {
        'fill': fill_color,
        'fill_raw': fill_raw,
        'font_weight': font_weight,
        'font_size': font_size,
        'font_family': font_family_str,
        'font_style': font_style,
        'text_decoration': text_decoration,
        'letter_spacing': letter_spacing_px,
        '_scale_x': ctx.scale_x or 1.0,
        '_object_opacity': object_opacity,
        '_fill_opacity': fill_opacity,
        '_stroke_opacity': stroke_opacity_value,
        'opacity': opacity,
        'stroke_raw': stroke_raw,
        'stroke_width': stroke_width,
        'stroke_opacity': stroke_opacity,
    }

    # Paragraph mode: flatten_tspan marks <text> with data-paragraph-line-height
    # when its direct-child tspans form a mergeable paragraph (same x, dy
    # clustered around one base line-height). Each direct tspan becomes one
    # <a:p> so the paragraph survives as a single editable text frame.
    # Per-line data-paragraph-space-before encodes paragraph gaps (extra dy
    # above the base line-height) for the corresponding <a:p>.
    # Paragraph mode is controlled by ctx.merge_paragraphs. When off, ignore
    # any data-paragraph-* markers and fall through to the original
    # one-text-per-tspan path so the SVG's pixel layout is preserved.
    line_height_attr = elem.get('data-paragraph-line-height') if ctx.merge_paragraphs else None
    line_height_px = _f(line_height_attr) if line_height_attr is not None else None
    paragraph_runs: list[list[dict[str, Any]]] | None = None
    paragraph_space_before: list[float] = []
    paragraph_bullets: list[dict[str, Any] | None] = []
    # Per-tspan widths (visual lines as the deck author drew them) regardless
    # of how many merge into one <a:p>; used to size the textbox so PowerPoint
    # has room to wrap text to the SVG's original line widths.
    visual_line_widths: list[float] = []
    if line_height_px is not None and line_height_px > 0:
        xml_space = resolve_project_xml_space(elem)
        paragraph_runs = []
        for child in elem:
            if child.tag != f'{{{SVG_NS}}}tspan':
                continue
            line_runs = _collect_tspan_runs(
                child,
                parent_attrs,
                ctx,
                xml_space,
            )
            line_runs = _normalize_text_run_whitespace(line_runs)
            if not line_runs:
                continue
            visual_line_widths.append(
                _estimate_bullet_line_width(line_runs, fonts, ctx)
            )
            soft_break = child.get('data-paragraph-soft-break') == '1'
            if soft_break and paragraph_runs:
                # Append to the previous paragraph. A Latin line-wrap needs a
                # space to keep two words apart (SVG used a dy break, not
                # punctuation); CJK wraps mid-sentence with no inter-character
                # space, so a joining space there is a spurious artifact.
                prev = paragraph_runs[-1]
                prev_text = prev[-1]['text'] if prev else ''
                next_text = line_runs[0]['text']
                boundary_is_cjk = (
                    (prev_text and is_cjk_char(prev_text[-1]))
                    or (next_text and is_cjk_char(next_text[0]))
                )
                if prev and not prev_text.endswith(' ') \
                        and not next_text.startswith(' ') \
                        and not boundary_is_cjk:
                    prev.append({
                        **prev[-1],
                        'text': ' ',
                        'letter_spacing': 0.0,
                    })
                prev.extend(line_runs)
            else:
                paragraph_runs.append(line_runs)
                sb_attr = child.get('data-paragraph-space-before')
                paragraph_space_before.append(_f(sb_attr) if sb_attr else 0.0)
        if not paragraph_runs:
            paragraph_runs = None
            paragraph_space_before = []
            visual_line_widths = []
        else:
            stripped_paragraphs: list[list[dict[str, Any]]] = []
            for line_runs in paragraph_runs:
                stripped_runs, bullet = _extract_text_bullet(line_runs)
                stripped_paragraphs.append(
                    _coalesce_text_runs(stripped_runs, fonts, ctx)
                )
                paragraph_bullets.append(bullet)
            paragraph_runs = stripped_paragraphs

    if paragraph_runs is not None:
        runs = [r for line in paragraph_runs for r in line]
    else:
        runs = _build_text_runs(elem, parent_attrs, ctx)
        runs, single_bullet = _extract_text_bullet(runs)
        runs = _coalesce_text_runs(runs, fonts, ctx)

    full_text = ''.join(r['text'] for r in runs) if runs else ''
    if not full_text.strip():
        is_placeholder_carrier = (
            (elem.get('data-pptx-placeholder-carrier') or '').strip().lower()
            == 'true'
        )
        if not is_placeholder_carrier:
            return None
        # A declared carrier must compile to one native text shape even when its
        # authored visual is blank. U+200B is invisible but survives DrawingML.
        runs = [{**parent_attrs, 'text': '\u200b'}]
        paragraph_runs = None
        paragraph_space_before = []
        paragraph_bullets = []
        visual_line_widths = []
        single_bullet = None

    # Estimate text dimensions
    if paragraph_runs is not None:
        # Use the WIDEST visual line (per-tspan as the deck author drew it),
        # not the joined-up paragraph: soft-broken paragraphs concatenate
        # many lines into one <a:p>, and measuring the joined string would
        # blow the textbox past the canvas.
        text_width = max(visual_line_widths) if visual_line_widths else 0.0
        # Total height assumes the visual line count from the SVG source;
        # if PowerPoint wraps to more or fewer lines after the user resizes,
        # the user resizes the height accordingly.
        text_height = (
            line_height_px * (len(visual_line_widths) - 1)
            + sum(paragraph_space_before)
            + font_size * 1.5
        )
    else:
        text_width = _estimate_text_runs_width(runs)
        if single_bullet:
            fs_px = float(runs[0].get('font_size', font_size)) if runs else font_size
            text_width += _bullet_margin_px(single_bullet, fs_px)
        text_height = font_size * 1.5
    padding = _textbox_padding(font_size)

    # Adjust position based on text-anchor
    if text_anchor == 'middle':
        box_x = x - text_width / 2 - padding
    elif text_anchor == 'end':
        box_x = x - text_width - padding
    else:
        box_x = x - padding

    box_y = y - font_size * 0.85
    box_w = text_width + padding * 2
    box_h = text_height + padding

    text_transform = elem.get('transform', '')
    text_operations = (
        parse_transform_operations(text_transform)
        if text_transform else ()
    )
    translate_only = bool(text_operations) and all(
        name == 'translate' for name, _args in text_operations
    )
    rotate_only = (
        len(text_operations) == 1
        and text_operations[0][0] == 'rotate'
    )
    if text_operations and not (translate_only or rotate_only):
        raise ValueError(
            'Text transform must be a translate-only list or one rotate operation'
        )
    if translate_only and not ctx.use_transform_matrix:
        a, b, c, d, e, f = parse_transform_matrix(text_transform)
        # A pure-translate transform on a text element (hand-authored, or written
        # by a live-preview move) was otherwise ignored here, drifting the text.
        # Absorb the translation into the frame position.
        if (
            abs(a - 1.0) < 1e-9 and abs(b) < 1e-9
            and abs(c) < 1e-9 and abs(d - 1.0) < 1e-9
        ):
            sx = ctx.scale_x or 1.0
            sy = ctx.scale_y or 1.0
            raw_box_x = (box_x - ctx.translate_x) / sx
            raw_box_y = (box_y - ctx.translate_y) / sy
            box_x = ctx.translate_x + sx * (a * raw_box_x + e)
            box_y = ctx.translate_y + sy * (d * raw_box_y + f)

    # Text rotation. SVG's rotate(angle [cx cy]) rotates around (cx, cy), but
    # DrawingML's <a:xfrm rot="..."> rotates the shape around its own center.
    # When a pivot is given (and differs from the box center), translate the
    # box so its center lands where SVG would place the rotated visual center —
    # otherwise rotated y-axis labels etc. drift to the wrong location.
    text_rot = 0
    if rotate_only:
        rotate_args = text_operations[0][1]
        angle_deg = rotate_args[0]
        text_rot = int(angle_deg * ANGLE_UNIT)
        if len(rotate_args) == 3:
            pivot_x = ctx_x(rotate_args[1], ctx)
            pivot_y = ctx_y(rotate_args[2], ctx)
            cx_box = box_x + box_w / 2
            cy_box = box_y + box_h / 2
            rad = math.radians(angle_deg)
            dx = cx_box - pivot_x
            dy = cy_box - pivot_y
            new_cx = pivot_x + dx * math.cos(rad) - dy * math.sin(rad)
            new_cy = pivot_y + dx * math.sin(rad) + dy * math.cos(rad)
            box_x = new_cx - box_w / 2
            box_y = new_cy - box_h / 2

    # Alignment
    algn_map = {'start': 'l', 'middle': 'ctr', 'end': 'r'}
    algn = algn_map.get(text_anchor, 'l')

    # Shadow effect
    shape_effect_xml = ''
    text_effect_xml = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        filter_elem = ctx.defs[filt_id]
        effect_kind = classify_filter_effect(filter_elem)
        if effect_kind == 'glow':
            text_effect_xml = build_effect_xml(
                filter_elem,
                get_element_opacity(elem, ctx),
            )
        elif effect_kind == 'shadow':
            shape_effect_xml = build_effect_xml(
                filter_elem,
                get_element_opacity(elem, ctx),
            )

    shape_id = _claim_element_shape_id(elem, ctx)
    rot_attr = f' rot="{text_rot}"' if text_rot else ''

    if paragraph_runs is not None:
        # SVG dy(px) -> hundredths-of-a-point: dy_pt = dy_px * 0.75, then x100.
        line_spc_val = round(line_height_px * FONT_PX_TO_HUNDREDTHS_PT)
        ln_spc_xml = f'<a:lnSpc><a:spcPts val="{line_spc_val}"/></a:lnSpc>'
        paragraph_xml_chunks = []
        for line, extra_px, bullet in zip(paragraph_runs, paragraph_space_before, paragraph_bullets):
            spc_bef_xml = ''
            if extra_px > 0:
                spc_bef_val = round(extra_px * FONT_PX_TO_HUNDREDTHS_PT)
                spc_bef_xml = f'<a:spcBef><a:spcPts val="{spc_bef_val}"/></a:spcBef>'
            runs_inner = '\n'.join(_build_run_xml(r, fonts, ctx, text_effect_xml) for r in line)
            p_pr_xml = _paragraph_pr_xml(
                algn=algn,
                font_size=float(line[0].get('font_size', font_size)) if line else font_size,
                body_xml=f'{ln_spc_xml}{spc_bef_xml}',
                bullet=bullet,
                ctx=ctx,
            )
            paragraph_xml_chunks.append(
                f'<a:p>\n{p_pr_xml}\n{runs_inner}\n</a:p>'
            )
        paragraphs_xml = '\n'.join(paragraph_xml_chunks)
    else:
        runs_xml = '\n'.join(_build_run_xml(r, fonts, ctx, text_effect_xml) for r in runs)
        p_pr_xml = _paragraph_pr_xml(
            algn=algn,
            font_size=float(runs[0].get('font_size', font_size)) if runs else font_size,
            bullet=single_bullet,
            ctx=ctx,
        )
        paragraphs_xml = f'<a:p>\n{p_pr_xml}\n{runs_xml}\n</a:p>'

    off_x = px_to_emu(box_x)
    off_y = px_to_emu(box_y)
    ext_cx = drawingml_text_frame_width_emu(text_width, font_size)
    ext_cy = px_to_emu(box_h)
    if ext_cx < 1 or ext_cy < 1:
        raise ValueError(
            'negative letter-spacing produces a non-positive DrawingML '
            f'text-frame extent (cx={ext_cx}, cy={ext_cy})'
        )
    validate_ooxml_xfrm(off_x, off_y, ext_cx, ext_cy)
    validate_text_run_advances(runs)

    # Paragraph mode: wrap="square" so text reflows when the user resizes,
    # but NO spAutoFit — otherwise PowerPoint expands the frame to fit a
    # long joined-up <a:p> on one line, blowing past the canvas. The cx we
    # write below is the longest source SVG line without single-line renderer
    # headroom; PowerPoint wraps long paragraphs inside this design width.
    # Single-line text keeps wrap="none" + spAutoFit for tight fidelity.
    if paragraph_runs is not None:
        body_pr_xml = (
            '<a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" '
            'anchor="t" anchorCtr="0"/>'
        )
    else:
        body_pr_xml = (
            '<a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" '
            'anchor="t" anchorCtr="0">\n<a:spAutoFit/>\n</a:bodyPr>'
        )

    return ShapeResult(xml=f'''<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/>
<p:cNvSpPr txBox="1"/><p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm{rot_attr}><a:off x="{off_x}" y="{off_y}"/>
<a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
<a:noFill/>
<a:ln><a:noFill/></a:ln>
{shape_effect_xml}
</p:spPr>
<p:txBody>
{body_pr_xml}
<a:lstStyle/>
{paragraphs_xml}
</p:txBody>
</p:sp>''', bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))


# ---------------------------------------------------------------------------
# clipPath support (image clipping)
# ---------------------------------------------------------------------------

def _clip_commands_to_geom(
    commands: list[PathCommand],
    img_x: float, img_y: float,
    img_w: float, img_h: float,
    object_bbox: bool,
) -> str:
    """Convert clip path commands to DrawingML custGeom XML.

    Coordinates are transformed relative to the image bounding box so that
    (img_x, img_y) maps to (0, 0) and (img_x+img_w, img_y+img_h) maps to
    (w_emu, h_emu).
    """
    w_emu = px_to_emu(img_w)
    h_emu = px_to_emu(img_h)

    if w_emu <= 0 or h_emu <= 0:
        return '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'

    def _tx(x: float) -> int:
        if object_bbox:
            return int(x * w_emu)
        return px_to_emu(x - img_x)

    def _ty(y: float) -> int:
        if object_bbox:
            return int(y * h_emu)
        return px_to_emu(y - img_y)

    parts: list[str] = []
    for cmd in commands:
        if cmd.cmd == 'M':
            parts.append(
                f'<a:moveTo><a:pt x="{_tx(cmd.args[0])}" '
                f'y="{_ty(cmd.args[1])}"/></a:moveTo>'
            )
        elif cmd.cmd == 'L':
            parts.append(
                f'<a:lnTo><a:pt x="{_tx(cmd.args[0])}" '
                f'y="{_ty(cmd.args[1])}"/></a:lnTo>'
            )
        elif cmd.cmd == 'C':
            pts = ''.join(
                f'<a:pt x="{_tx(cmd.args[i])}" y="{_ty(cmd.args[i + 1])}"/>'
                for i in range(0, 6, 2)
            )
            parts.append(f'<a:cubicBezTo>{pts}</a:cubicBezTo>')
        elif cmd.cmd == 'Z':
            parts.append('<a:close/>')

    path_inner = '\n'.join(parts)
    return f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_inner}
</a:path></a:pathLst>
</a:custGeom>'''


_CLIP_SHAPE_TAGS = frozenset({'circle', 'ellipse', 'rect', 'path', 'polygon'})
_CLIP_NON_VISUAL_ELEMENTS = frozenset({
    f'{{{SVG_NS}}}{tag}' for tag in ('desc', 'metadata', 'style', 'title')
})


def _element_contract_label(elem: ET.Element) -> str:
    tag = elem.tag.rsplit('}', 1)[-1]
    elem_id = (elem.get('id') or '').strip()
    return f'<{tag} id="{elem_id}">' if elem_id else f'<{tag}>'


def _unsupported_clip_rule_properties(elem: ET.Element) -> tuple[str, ...]:
    style_values = parse_inline_style(elem.get('style'))
    return tuple(
        name for name in ('clip-rule', 'fill-rule')
        if elem.get(name) is not None or name in style_values
    )


def _effective_clip_geometry_length(
    elem: ET.Element,
    attribute: str,
    *,
    default: float | None = None,
) -> float:
    style_values = parse_inline_style(elem.get('style'))
    raw = style_values.get(attribute)
    if raw is None:
        raw = elem.get(attribute)
    if raw is None:
        if default is None:
            raise ValueError(f'requires {attribute}')
        return default
    return parse_project_geometry_length(raw, attribute)


def _clip_preset_geometry_error(
    target: ET.Element,
    shape: ET.Element,
    clip_units: str,
) -> str | None:
    """Reject primitive clips that cannot map to a full-frame preset."""
    shape_tag = shape.tag.rsplit('}', 1)[-1].lower()
    if shape_tag not in {'circle', 'ellipse', 'rect'}:
        return None
    target_label = _element_contract_label(target)
    try:
        target_x = _effective_clip_geometry_length(target, 'x', default=0.0)
        target_y = _effective_clip_geometry_length(target, 'y', default=0.0)
        target_w = _effective_clip_geometry_length(target, 'width')
        target_h = _effective_clip_geometry_length(target, 'height')
    except ValueError as exc:
        return f'cannot validate {shape_tag} against {target_label}: {exc}'
    if target_w <= 0 or target_h <= 0:
        return (
            f'cannot validate {shape_tag} against {target_label}: target '
            'width and height must be positive'
        )

    object_bbox = clip_units == 'objectBoundingBox'
    expected_x = 0.0 if object_bbox else target_x
    expected_y = 0.0 if object_bbox else target_y
    expected_w = 1.0 if object_bbox else target_w
    expected_h = 1.0 if object_bbox else target_h

    def close(actual: float, expected: float) -> bool:
        return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6)

    try:
        if shape_tag == 'circle':
            cx = _effective_clip_geometry_length(shape, 'cx', default=0.0)
            cy = _effective_clip_geometry_length(shape, 'cy', default=0.0)
            radius = _effective_clip_geometry_length(shape, 'r', default=0.0)
            fits = (
                close(expected_w, expected_h)
                and close(cx, expected_x + expected_w / 2.0)
                and close(cy, expected_y + expected_h / 2.0)
                and close(radius, expected_w / 2.0)
            )
        elif shape_tag == 'ellipse':
            cx = _effective_clip_geometry_length(shape, 'cx', default=0.0)
            cy = _effective_clip_geometry_length(shape, 'cy', default=0.0)
            rx = _effective_clip_geometry_length(shape, 'rx', default=0.0)
            ry = _effective_clip_geometry_length(shape, 'ry', default=0.0)
            fits = (
                close(cx, expected_x + expected_w / 2.0)
                and close(cy, expected_y + expected_h / 2.0)
                and close(rx, expected_w / 2.0)
                and close(ry, expected_h / 2.0)
            )
        else:
            rect_x = _effective_clip_geometry_length(shape, 'x', default=0.0)
            rect_y = _effective_clip_geometry_length(shape, 'y', default=0.0)
            rect_w = _effective_clip_geometry_length(shape, 'width', default=0.0)
            rect_h = _effective_clip_geometry_length(shape, 'height', default=0.0)
            fits = (
                close(rect_x, expected_x)
                and close(rect_y, expected_y)
                and close(rect_w, expected_w)
                and close(rect_h, expected_h)
            )
            if fits:
                rx_raw = (
                    parse_inline_style(shape.get('style')).get('rx')
                    or shape.get('rx')
                )
                ry_raw = (
                    parse_inline_style(shape.get('style')).get('ry')
                    or shape.get('ry')
                )
                rx = (
                    parse_project_geometry_length(rx_raw, 'rx')
                    if rx_raw is not None else None
                )
                ry = (
                    parse_project_geometry_length(ry_raw, 'ry')
                    if ry_raw is not None else None
                )
                if rx is None and ry is not None:
                    rx = ry
                elif ry is None and rx is not None:
                    ry = rx
                rx = rx or 0.0
                ry = ry or 0.0
                if rx > 0 or ry > 0:
                    if object_bbox:
                        fits = close(rx * target_w, ry * target_h)
                    else:
                        fits = close(rx, ry)
    except ValueError as exc:
        return f'{shape_tag} geometry for {target_label} is invalid: {exc}'

    if fits:
        return None
    return (
        f'{shape_tag} geometry must cover the complete frame of {target_label} '
        'for native preset mapping; use path or polygon for partial, offset, '
        'or non-uniform clips'
    )


def project_clip_path_errors(root: ET.Element) -> list[str]:
    """Return clip-path errors that would otherwise degrade picture geometry."""
    definitions, duplicates = project_definition_index(root)
    errors: set[str] = set()
    for elem in root.iter():
        raw_ref = elem.get('clip-path')
        if raw_ref is None or raw_ref.strip().lower() == 'none':
            continue
        label = _element_contract_label(elem)
        is_svg_image = elem.tag == f'{{{SVG_NS}}}image'
        is_imported_crop = (
            elem.tag == f'{{{SVG_NS}}}svg'
            and elem.get('data-pptx-crop') == '1'
        )
        if not is_svg_image and not is_imported_crop:
            errors.add(
                f'{label} clip-path is allowed only on <image> or an imported '
                'data-pptx-crop="1" wrapper'
            )
        match = re.fullmatch(r'url\(#([^)]+)\)', raw_ref.strip())
        if match is None:
            errors.add(
                f'{label} clip-path must be an exact local url(#id) '
                f'reference; got {raw_ref!r}'
            )
            continue
        clip_id = match.group(1)
        if clip_id in duplicates:
            errors.add(
                f'{label} clip-path=url(#{clip_id}) is ambiguous because the '
                'definition id is duplicated'
            )
            continue
        clip = definitions.get(clip_id)
        if clip is None or clip.tag != f'{{{SVG_NS}}}clipPath':
            errors.add(
                f'{label} clip-path=url(#{clip_id}) has no matching direct '
                f'<defs><clipPath id="{clip_id}"> definition'
            )
            continue
        clip_label = f'<clipPath id="{clip_id}">'
        clip_units = clip.get('clipPathUnits', 'userSpaceOnUse')
        if clip_units not in {'userSpaceOnUse', 'objectBoundingBox'}:
            errors.add(
                f'{clip_label} has unsupported clipPathUnits={clip_units!r}'
            )
        if clip.get('transform'):
            errors.add(f'{clip_label} cannot use transform')
        clip_rules = _unsupported_clip_rule_properties(clip)
        if clip_rules:
            errors.add(
                f'{clip_label} cannot use {", ".join(clip_rules)}; native '
                'picture geometry has no equivalent winding-rule control'
            )
        visual_children = [
            child for child in list(clip)
            if child.tag not in _CLIP_NON_VISUAL_ELEMENTS
        ]
        if len(visual_children) != 1:
            errors.add(
                f'{clip_label} must contain exactly one direct supported shape'
            )
            continue
        shape = visual_children[0]
        shape_tag = shape.tag.rsplit('}', 1)[-1].lower()
        if (
            shape_tag not in _CLIP_SHAPE_TAGS
            or shape.tag != f'{{{SVG_NS}}}{shape_tag}'
        ):
            errors.add(
                f'{clip_label} child <{shape_tag}> is unsupported; use '
                'circle, ellipse, rect, path, or polygon'
            )
            continue
        if shape.get('transform'):
            errors.add(f'{clip_label} child <{shape_tag}> cannot use transform')
            continue
        shape_rules = _unsupported_clip_rule_properties(shape)
        if shape_rules:
            errors.add(
                f'{clip_label} child <{shape_tag}> cannot use '
                f'{", ".join(shape_rules)}; native picture geometry has no '
                'equivalent winding-rule control'
            )
            continue
        if clip_units in {'userSpaceOnUse', 'objectBoundingBox'}:
            geometry_error = _clip_preset_geometry_error(
                elem,
                shape,
                clip_units,
            )
            if geometry_error is not None:
                errors.add(f'{clip_label} {geometry_error}')
    return sorted(errors)


def _resolve_clip_geometry(
    elem: ET.Element,
    ctx: ConvertContext,
    raw_x: float, raw_y: float,
    raw_w: float, raw_h: float,
) -> str:
    """Resolve clip-path on an image element to DrawingML geometry XML.

    Supports:
      - circle / ellipse  → prstGeom ellipse
      - rect with rx/ry   → prstGeom roundRect
      - path / polygon     → custGeom

    Args:
        elem: SVG element bearing a clip-path attribute.
        ctx:  Conversion context (carries defs).
        raw_x, raw_y: Image position in SVG space (pre-ctx-transform).
        raw_w, raw_h: Image dimensions in SVG space (pre-ctx-transform).

    Returns:
        DrawingML geometry XML string.
    """
    DEFAULT = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'

    clip_ref = elem.get('clip-path', '')
    if not clip_ref or clip_ref == 'none':
        return DEFAULT

    clip_id = resolve_url_id(clip_ref)
    if not clip_id or clip_id not in ctx.defs:
        return DEFAULT

    clip_elem = ctx.defs[clip_id]
    clip_tag = clip_elem.tag.replace(f'{{{SVG_NS}}}', '')
    if clip_tag != 'clipPath':
        return DEFAULT

    # Find the first shape child of the clipPath
    shape = None
    for child in clip_elem:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag in ('circle', 'ellipse', 'rect', 'path', 'polygon'):
            shape = child
            break

    if shape is None:
        return DEFAULT

    shape_tag = shape.tag.replace(f'{{{SVG_NS}}}', '')
    is_obb = clip_elem.get('clipPathUnits') == 'objectBoundingBox'

    # --- Circle / Ellipse → preset ellipse ---
    if shape_tag in ('circle', 'ellipse'):
        return '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    # --- Rect with rx/ry → preset roundRect ---
    if shape_tag == 'rect':
        rx_attr = shape.get('rx')
        ry_attr = shape.get('ry')
        rx = svg_length_x(rx_attr, ctx) if rx_attr is not None else 0.0
        ry = svg_length_y(ry_attr, ctx) if ry_attr is not None else rx
        if rx <= 0 and ry <= 0:
            return DEFAULT  # plain rect clip is a no-op
        r = max(rx, ry)
        if is_obb:
            r = r * min(raw_w, raw_h)
        shorter = min(raw_w, raw_h)
        if shorter <= 0:
            return DEFAULT
        adj = int(min(r / (shorter / 2), 1.0) * 50000)
        return (
            f'<a:prstGeom prst="roundRect"><a:avLst>'
            f'<a:gd name="adj" fmla="val {adj}"/>'
            f'</a:avLst></a:prstGeom>'
        )

    # --- Path → custGeom ---
    if shape_tag == 'path':
        d = shape.get('d', '')
        if not d:
            return DEFAULT
        commands = parse_svg_path(d)
        commands = svg_path_to_absolute(commands)
        commands = normalize_path_commands(commands)
        if not commands:
            return DEFAULT
        return _clip_commands_to_geom(
            commands, raw_x, raw_y, raw_w, raw_h, is_obb,
        )

    # --- Polygon → custGeom ---
    if shape_tag == 'polygon':
        pts = parse_svg_points(shape.get('points', ''), min_points=3)
        commands = [PathCommand('M', [pts[0][0], pts[0][1]])]
        for px_, py_ in pts[1:]:
            commands.append(PathCommand('L', [px_, py_]))
        commands.append(PathCommand('Z', []))
        return _clip_commands_to_geom(
            commands, raw_x, raw_y, raw_w, raw_h, is_obb,
        )

    return DEFAULT


# ---------------------------------------------------------------------------
# image
# ---------------------------------------------------------------------------

def _picture_xfrm_from_rect(
    ctx: ConvertContext,
    x: float,
    y: float,
    w: float,
    h: float,
) -> tuple[str, int, int, int, int, tuple[int, int, int, int]]:
    """Build DrawingML xfrm data for a picture rectangle.

    Coordinates ``x``, ``y``, ``w``, ``h`` MUST already be in ctx-resolved
    space (i.e. callers have applied ``ctx_x`` / ``ctx_w`` upstream). When
    ``ctx.use_transform_matrix`` is set, raw SVG-space coordinates are
    expected and the matrix path applies the transform itself.
    """
    if ctx.use_transform_matrix:
        return rect_to_dml_xfrm(x, y, w, h, ctx.transform_matrix)

    off_x = px_to_emu(x)
    off_y = px_to_emu(y)
    ext_cx = px_to_emu(w)
    ext_cy = px_to_emu(h)
    return '', off_x, off_y, ext_cx, ext_cy, (off_x, off_y, off_x + ext_cx, off_y + ext_cy)


def _picture_xfrm_from_svg_rect(
    ctx: ConvertContext,
    raw_x: float,
    raw_y: float,
    raw_w: float,
    raw_h: float,
    resolved_x: float,
    resolved_y: float,
    resolved_w: float,
    resolved_h: float,
    transform: str | None,
) -> tuple[str, int, int, int, int, tuple[int, int, int, int]]:
    """Build picture xfrm data, honoring element-level SVG transforms.

    ``raw_*`` values stay in the element's source SVG coordinate space for
    matrix decomposition; ``resolved_*`` values are the existing scalar path.
    """
    if ctx.use_transform_matrix:
        matrix = ctx.transform_matrix
        if transform:
            matrix = matrix_multiply(matrix, parse_transform_matrix(transform))
        return rect_to_dml_xfrm(raw_x, raw_y, raw_w, raw_h, matrix)

    if transform:
        context_matrix = (
            ctx.scale_x, 0.0,
            0.0, ctx.scale_y,
            ctx.translate_x, ctx.translate_y,
        )
        matrix = matrix_multiply(context_matrix, parse_transform_matrix(transform))
        return rect_to_dml_xfrm(raw_x, raw_y, raw_w, raw_h, matrix)

    return _picture_xfrm_from_rect(ctx, resolved_x, resolved_y, resolved_w, resolved_h)


def _read_image_size(data: bytes) -> tuple[int | None, int | None]:
    """Read intrinsic image dimensions (width, height) from raw bytes.

    Used by ``convert_image`` to translate SVG ``preserveAspectRatio`` into
    DrawingML ``<a:srcRect>`` so the original image is preserved and remains
    croppable inside PowerPoint.

    Returns ``(None, None)`` on any failure — callers fall back to the
    legacy stretch behaviour.
    """
    try:
        from PIL import Image, UnidentifiedImageError  # type: ignore
    except ImportError:
        return (None, None)
    try:
        with Image.open(io.BytesIO(data)) as img:
            return img.size
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        ZeroDivisionError,
    ):
        return (None, None)


def _image_has_alpha(img: Any) -> bool:
    """Return whether a PIL image carries useful transparency."""
    if img.mode in ('RGBA', 'LA'):
        return True
    if img.mode == 'P':
        return 'transparency' in getattr(img, 'info', {})
    return False


def _image_target_size(
    display_w: float,
    display_h: float,
    *,
    max_dimension: int | None,
    scale: float,
) -> tuple[int, int]:
    """Resolve optimized pixel dimensions from rendered SVG dimensions."""
    target_w = max(1, int(round(display_w * max(scale, 1.0))))
    target_h = max(1, int(round(display_h * max(scale, 1.0))))
    if max_dimension and max(target_w, target_h) > max_dimension:
        ratio = max_dimension / max(target_w, target_h)
        target_w = max(1, int(round(target_w * ratio)))
        target_h = max(1, int(round(target_h * ratio)))
    return target_w, target_h


def _fit_full_image_target(
    img_w: int,
    img_h: int,
    box_w: float,
    box_h: float,
    align: str,
    mode: str,
    *,
    sizing: str,
    max_dimension: int | None,
    scale: float,
) -> tuple[int, int]:
    """Size the full source image; never crop pixels.

    ``cap`` mode only limits oversized source images by maximum dimension.
    ``display`` mode sizes to the rendered SVG box budget.
    """
    if img_w <= 0 or img_h <= 0:
        return (1, 1)

    if sizing == 'cap':
        target_w, target_h = img_w, img_h
        if max_dimension and max(target_w, target_h) > max_dimension:
            ratio = max_dimension / max(target_w, target_h)
            target_w = max(1, int(round(target_w * ratio)))
            target_h = max(1, int(round(target_h * ratio)))
        return target_w, target_h

    target_box_w, target_box_h = _image_target_size(
        box_w,
        box_h,
        max_dimension=None,
        scale=scale,
    )
    img_ratio = img_w / img_h
    box_ratio = box_w / box_h if box_h else img_ratio

    if align != 'none' and mode == 'slice':
        if box_ratio >= img_ratio:
            target_w = target_box_w
            target_h = int(round(target_w / img_ratio))
        else:
            target_h = target_box_h
            target_w = int(round(target_h * img_ratio))
    else:
        ratio = min(target_box_w / img_w, target_box_h / img_h, 1.0)
        target_w = int(round(img_w * ratio))
        target_h = int(round(img_h * ratio))

    target_w = max(1, target_w)
    target_h = max(1, target_h)
    if max_dimension and max(target_w, target_h) > max_dimension:
        ratio = max_dimension / max(target_w, target_h)
        target_w = max(1, int(round(target_w * ratio)))
        target_h = max(1, int(round(target_h * ratio)))
    return target_w, target_h


def _resize_for_target(img: Any, target_w: int, target_h: int) -> Any:
    """Downscale a PIL image to the target dimensions without upsampling."""
    width, height = img.size
    if target_w >= width and target_h >= height:
        return img
    ratio = min(target_w / width, target_h / height)
    if ratio >= 1.0:
        return img
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return img
    new_size = (max(1, int(round(width * ratio))), max(1, int(round(height * ratio))))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def _encode_optimized_image(img: Any, *, prefer_jpeg: bool, quality: int) -> tuple[bytes, str] | None:
    """Encode a PIL image for PPTX media."""
    buf = io.BytesIO()
    try:
        if prefer_jpeg and not _image_has_alpha(img):
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(buf, format='JPEG', quality=max(1, min(quality, 100)), optimize=True)
            return buf.getvalue(), 'jpg'
        if img.mode == 'P':
            img = img.convert('RGBA' if _image_has_alpha(img) else 'RGB')
        img.save(buf, format='PNG', optimize=True)
        return buf.getvalue(), 'png'
    except (OSError, ValueError):
        return None


def _optimize_image_for_pptx(
    elem: ET.Element,
    ctx: ConvertContext,
    img_data: bytes,
    img_format: str,
    box_w: float,
    box_h: float,
) -> tuple[bytes, str]:
    """Optimize full raster image bytes for native PPTX embedding."""
    if not ctx.image_optimize:
        return img_data, img_format
    if img_format.lower() in {'svg', 'emf', 'wmf'}:
        return img_data, img_format

    try:
        from PIL import Image, UnidentifiedImageError  # type: ignore
    except ImportError:
        return img_data, img_format

    try:
        img = Image.open(io.BytesIO(img_data))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        return img_data, img_format

    # Multi-frame images (animated GIF / WebP / APNG): resize/re-encode
    # below keeps frame 0 only, flattening the animation in the exported
    # PPTX. Pass the original bytes through — animations are exempt from
    # optimization and the size cap (before this optimizer existed, the
    # native path embedded raster bytes verbatim and animations survived).
    if getattr(img, 'is_animated', False):
        return img_data, img_format

    align, mode = parse_project_image_aspect_ratio(
        elem.get('preserveAspectRatio')
    )
    target_w, target_h = _fit_full_image_target(
        img.size[0],
        img.size[1],
        box_w,
        box_h,
        align,
        mode,
        sizing=ctx.image_sizing,
        max_dimension=ctx.image_max_dimension,
        scale=ctx.image_scale,
    )

    original_size = img.size
    img = _resize_for_target(img, target_w, target_h)
    resized = img.size != original_size
    prefer_jpeg = img_format.lower() in {'png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff'}
    encoded = _encode_optimized_image(img, prefer_jpeg=prefer_jpeg, quality=ctx.image_quality)
    if encoded is None:
        return img_data, img_format

    optimized_data, optimized_format = encoded
    if not resized and len(optimized_data) >= len(img_data):
        return img_data, img_format

    return optimized_data, optimized_format


def _compute_slice_src_rect(
    img_w: float, img_h: float,
    box_w: float, box_h: float,
    align: str,
) -> tuple[int, int, int, int] | None:
    """Compute DrawingML ``<a:srcRect>`` (l, t, r, b) for SVG slice mode.

    SVG ``preserveAspectRatio="<align> slice"`` means: scale the image so it
    fully covers the box (CSS object-fit: cover) and crop the overflow at the
    given alignment anchor. DrawingML ``srcRect`` expresses the same intent
    by specifying which sub-rectangle of the source image to display, in
    units of 1/1000 of a percent (0–100000).

    Returns ``None`` when no cropping is required (image and box already
    match) or when inputs are degenerate.
    """
    if img_w <= 0 or img_h <= 0 or box_w <= 0 or box_h <= 0:
        return None

    # Scale factor that makes the image cover the box (cover semantics).
    scale = max(box_w / img_w, box_h / img_h)
    visible_w = box_w / scale  # ≤ img_w
    visible_h = box_h / scale  # ≤ img_h

    if abs(visible_w - img_w) < 0.5 and abs(visible_h - img_h) < 0.5:
        return None  # No crop needed

    crop_w_total = max(0.0, img_w - visible_w)
    crop_h_total = max(0.0, img_h - visible_h)

    x_anchor, y_anchor = PROJECT_IMAGE_ASPECT_RATIO_ANCHORS[align]

    crop_l = crop_w_total * x_anchor
    crop_r = crop_w_total - crop_l
    crop_t = crop_h_total * y_anchor
    crop_b = crop_h_total - crop_t

    l = max(0, min(100000, int(round(crop_l / img_w * 100000))))
    t = max(0, min(100000, int(round(crop_t / img_h * 100000))))
    r = max(0, min(100000, int(round(crop_r / img_w * 100000))))
    b = max(0, min(100000, int(round(crop_b / img_h * 100000))))

    return (l, t, r, b)


def _resolve_image_src_rect(
    elem: ET.Element,
    img_data: bytes,
    box_w: float, box_h: float,
) -> str:
    """Build ``<a:srcRect .../>`` XML for an SVG <image> based on its
    preserveAspectRatio. Returns an empty string when no srcRect is needed
    (meet mode, none mode, or already-aligned content).

    Slice mode is resolved into a srcRect so the original image is embedded
    intact and PowerPoint's crop tool / "Reset Picture" continue to work.
    Meet mode is handled separately by ``_resolve_image_meet_fit`` (which
    shrinks the picture frame to match image aspect ratio); none mode keeps
    the legacy stretch behaviour intentionally.
    """
    align, mode = parse_project_image_aspect_ratio(
        elem.get('preserveAspectRatio')
    )

    if align == 'none' or mode != 'slice':
        return ''  # meet handled by frame fit; none → stretch is correct per SVG spec

    img_w, img_h = _read_image_size(img_data)
    if img_w is None or img_h is None:
        return ''

    rect = _compute_slice_src_rect(float(img_w), float(img_h), box_w, box_h, align)
    if rect is None:
        return ''

    l, t, r, b = rect
    return f'<a:srcRect l="{l}" t="{t}" r="{r}" b="{b}"/>'


def _resolve_image_meet_fit(
    elem: ET.Element,
    img_data: bytes,
    box_w: float, box_h: float,
) -> tuple[float, float, float, float] | None:
    """For SVG ``preserveAspectRatio="<align> meet"``, compute the letterboxed
    sub-rectangle ``(dx, dy, fit_w, fit_h)`` inside the original box that
    matches the image's intrinsic aspect ratio.

    PowerPoint has no native ``meet`` semantic — ``<a:stretch><a:fillRect/>``
    fills the entire frame and would distort the image whenever the SVG
    container ratio differs from the source image ratio. The fix is to shrink
    the ``<p:pic>`` frame itself (off + ext) so the frame and image share an
    aspect ratio; the stretch then fills a correctly-shaped frame.

    Returns ``None`` when the adjustment is not applicable:
      - mode is ``slice`` (handled by srcRect path)
      - align is ``none`` (SVG spec says: stretch — do not adjust)
      - intrinsic image dimensions cannot be read
      - frame already matches image ratio (no-op)
    """
    align, mode = parse_project_image_aspect_ratio(
        elem.get('preserveAspectRatio')
    )

    if align == 'none' or mode == 'slice':
        return None

    img_w, img_h = _read_image_size(img_data)
    if img_w is None or img_h is None or img_w <= 0 or img_h <= 0:
        return None
    if box_w <= 0 or box_h <= 0:
        return None

    scale = min(box_w / img_w, box_h / img_h)
    fit_w = img_w * scale
    fit_h = img_h * scale

    if abs(fit_w - box_w) < 0.5 and abs(fit_h - box_h) < 0.5:
        return None  # already matches — no adjustment

    x_anchor, y_anchor = PROJECT_IMAGE_ASPECT_RATIO_ANCHORS[align]

    dx = (box_w - fit_w) * x_anchor
    dy = (box_h - fit_h) * y_anchor

    return (dx, dy, fit_w, fit_h)


def _build_image_blip_xml(r_id: str, opacity: float | None) -> str:
    """Build an image blip with native DrawingML transparency when requested."""
    if opacity is None:
        return f'<a:blip r:embed="{r_id}"/>'
    alpha = int(round(opacity * 100000))
    return (
        f'<a:blip r:embed="{r_id}">'
        f'<a:alphaModFix amt="{alpha}"/>'
        '</a:blip>'
    )


def convert_image(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <image> to DrawingML picture element.

    Supports clip-path attribute: when present, the clipPath shape is mapped
    to DrawingML picture geometry (prstGeom or custGeom) so the image is
    natively clipped in PowerPoint.
    """
    source = load_project_image_source(elem, ctx.svg_dir)

    # Raw coordinates (pre-context-transform) for clip path calculations
    raw_x = svg_length_x(elem.get('x'), ctx)
    raw_y = svg_length_y(elem.get('y'), ctx)
    raw_w = svg_length_x(elem.get('width'), ctx)
    raw_h = svg_length_y(elem.get('height'), ctx)

    if ctx.use_transform_matrix:
        x = raw_x
        y = raw_y
        w = raw_w
        h = raw_h
    else:
        x = ctx_x(raw_x, ctx)
        y = ctx_y(raw_y, ctx)
        w = ctx_w(raw_w, ctx)
        h = ctx_h(raw_h, ctx)

    if w <= 0 or h <= 0:
        raise ValueError('image width and height must be positive')

    img_format = source.img_format
    img_data = source.img_data

    img_data, img_format = _optimize_image_for_pptx(
        elem, ctx, img_data, img_format, w, h,
    )

    img_idx = len(ctx.media_files) + 1
    img_filename = f's{ctx.slide_num}_img{img_idx}.{img_format}'
    ctx.media_files[img_filename] = img_data

    r_id = ctx.next_rel_id()
    ctx.rel_entries.append({
        'id': r_id,
        'type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
        'target': f'../media/{img_filename}',
    })

    transform = elem.get('transform')

    # Resolve clip-path → DrawingML geometry
    clip_geom = _resolve_clip_geometry(elem, ctx, raw_x, raw_y, raw_w, raw_h)

    # Resolve preserveAspectRatio="<align> slice" as DrawingML crop metadata.
    # Image optimization only downscales the full source image; it never crops
    # pixels out of the embedded media.
    src_rect_xml = _resolve_image_src_rect(elem, img_data, w, h)
    blip_xml = _build_image_blip_xml(r_id, get_element_opacity(elem, ctx))

    # Resolve preserveAspectRatio="<align> meet" by shrinking the picture
    # frame to match the image's aspect ratio. Skipped when a real clip-path
    # produces non-trivial geometry: such clip rectangles are defined against
    # the original box and would no longer line up after a frame shift.
    # A clip-path that resolves back to the default rect geometry (e.g. plain
    # <rect> without rx/ry) is a no-op and must not block meet adjustment.
    clip_is_noop = clip_geom == '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    meet_fit = None if not clip_is_noop else _resolve_image_meet_fit(elem, img_data, w, h)

    shape_id = _claim_element_shape_id(elem, ctx)
    if meet_fit is not None:
        dx, dy, fit_w, fit_h = meet_fit
        if ctx.use_transform_matrix:
            raw_fit_x = raw_x + dx
            raw_fit_y = raw_y + dy
            raw_fit_w = fit_w
            raw_fit_h = fit_h
        else:
            raw_fit_x = raw_x + (dx / ctx.scale_x if ctx.scale_x else dx)
            raw_fit_y = raw_y + (dy / ctx.scale_y if ctx.scale_y else dy)
            raw_fit_w = fit_w / ctx.scale_x if ctx.scale_x else fit_w
            raw_fit_h = fit_h / ctx.scale_y if ctx.scale_y else fit_h
        xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = _picture_xfrm_from_svg_rect(
            ctx,
            raw_fit_x,
            raw_fit_y,
            raw_fit_w,
            raw_fit_h,
            x + dx,
            y + dy,
            fit_w,
            fit_h,
            transform,
        )
    else:
        xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = _picture_xfrm_from_svg_rect(
            ctx,
            raw_x,
            raw_y,
            raw_w,
            raw_h,
            x,
            y,
            w,
            h,
            transform,
        )

    return ShapeResult(xml=f'''<p:pic>
<p:nvPicPr>
<p:cNvPr id="{shape_id}" name="Image {shape_id}"/>
<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
<p:nvPr/>
</p:nvPicPr>
<p:blipFill>
{blip_xml}
{src_rect_xml}<a:stretch><a:fillRect/></a:stretch>
</p:blipFill>
<p:spPr>
<a:xfrm{xfrm_attr}><a:off x="{off_x}" y="{off_y}"/>
<a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
{clip_geom}
</p:spPr>
</p:pic>''', bounds_emu=bounds_emu)


# ---------------------------------------------------------------------------
# ellipse
# ---------------------------------------------------------------------------

def convert_ellipse(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <ellipse> to DrawingML ellipse shape."""
    preset_geom = _build_preset_geom_from_meta(elem)
    raw_cx = svg_length_x(elem.get('cx'), ctx)
    raw_cy = svg_length_y(elem.get('cy'), ctx)
    rx_attr = elem.get('rx')
    ry_attr = elem.get('ry')
    raw_rx = svg_length_x(rx_attr, ctx) if rx_attr is not None else 0.0
    raw_ry = svg_length_y(ry_attr, ctx) if ry_attr is not None else 0.0
    if rx_attr is not None and ry_attr is None:
        raw_ry = raw_rx
    elif ry_attr is not None and rx_attr is None:
        raw_rx = raw_ry
    cx_ = ctx_x(raw_cx, ctx)
    cy_ = ctx_y(raw_cy, ctx)
    rx = raw_rx * ctx.scale_x
    ry = raw_ry * ctx.scale_y

    if rx <= 0 or ry <= 0:
        return None

    x = cx_ - rx
    y = cy_ - ry
    w = rx * 2
    h = ry * 2

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    geom = preset_geom or '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    transform = elem.get('transform')

    shape_id = _claim_element_shape_id(elem, ctx)
    if preset_geom is not None:
        xfrm = _shape_xfrm_from_preset_frame(
            elem,
            ctx,
            (raw_cx - raw_rx, raw_cy - raw_ry, raw_rx * 2, raw_ry * 2),
            (x, y, w, h),
            transform,
        )
    else:
        xfrm = _shape_xfrm_from_svg_rect(
            ctx,
            raw_cx - raw_rx,
            raw_cy - raw_ry,
            raw_rx * 2,
            raw_ry * 2,
            x,
            y,
            w,
            h,
            transform,
        )
    xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = xfrm
    return ShapeResult(
        xml=_wrap_geometry_object(
            elem,
            ctx,
            shape_id, f'Ellipse {shape_id}',
            off_x, off_y, ext_cx, ext_cy,
            geom, fill, stroke, xfrm_attr=xfrm_attr,
        ),
        bounds_emu=bounds_emu,
    )


# ---------------------------------------------------------------------------
# nested <svg> sprite (template-import round-trip)
# ---------------------------------------------------------------------------

# Inverse of pptx_to_svg/pic_to_svg.py:101-113 — that path writes a cropped
# DrawingML picture as an outer <svg viewBox> wrapping a unit-rectangle <image>.
# Without this converter, every cropped picture in a template-import SVG is
# silently dropped on re-export.

@dataclass(frozen=True)
class NestedSvgCropSpec:
    """Validated transport fields for one imported cropped picture."""

    image: ET.Element
    x: float
    y: float
    width: float
    height: float
    src_l: int
    src_t: int
    src_r: int
    src_b: int


_NESTED_CROP_OUTER_ATTRIBUTES = frozenset({
    'clip-path',
    'data-pptx-crop',
    EFFECT_REASON_ATTR,
    EFFECT_STATUS_ATTR,
    'data-pptx-frame',
    'data-pptx-layer',
    'data-pptx-object',
    'data-pptx-placeholder-carrier',
    'data-pptx-shape-id',
    'data-pptx-shape-name',
    'data-pptx-shape-scope',
    'id',
    'preserveAspectRatio',
    'transform',
    'viewBox',
    'x',
    'y',
    'width',
    'height',
})
_NESTED_CROP_IMAGE_ATTRIBUTES = frozenset({
    'href',
    f'{{{XLINK_NS}}}href',
    'opacity',
    'preserveAspectRatio',
    'x',
    'y',
    'width',
    'height',
})
_DRAWINGML_PERCENTAGE_MIN = -(2 ** 31)
_DRAWINGML_PERCENTAGE_MAX = 2 ** 31 - 1


def _unsupported_nested_crop_attributes(
    elem: ET.Element,
    allowed: frozenset[str],
) -> list[str]:
    unsupported = []
    for name in elem.attrib:
        if name in allowed:
            continue
        unsupported.append(name.rsplit('}', 1)[-1])
    return sorted(unsupported)


def parse_project_nested_svg_crop(elem: ET.Element) -> NestedSvgCropSpec:
    """Parse the closed nested-SVG transport written by ``pptx_to_svg``."""
    if elem.tag != f'{{{SVG_NS}}}svg':
        raise ValueError('expected an SVG-namespace nested <svg> crop wrapper')

    unsupported = _unsupported_nested_crop_attributes(
        elem,
        _NESTED_CROP_OUTER_ATTRIBUTES,
    )
    if unsupported:
        raise ValueError(
            'nested crop <svg> has unsupported attribute(s): '
            + ', '.join(unsupported)
        )
    crop_marker = elem.get('data-pptx-crop')
    clip_path = elem.get('clip-path')
    if crop_marker is not None and crop_marker != '1':
        raise ValueError('nested crop data-pptx-crop must be exactly "1"')
    if clip_path is None:
        if crop_marker is not None:
            raise ValueError(
                'nested crop data-pptx-crop="1" requires clip-path'
            )
    elif clip_path.strip().lower() == 'none':
        raise ValueError('nested crop clip-path cannot be "none"')
    elif crop_marker != '1':
        raise ValueError(
            'nested crop clip-path requires data-pptx-crop="1"'
        )
    if elem.text and elem.text.strip():
        raise ValueError(
            'nested crop <svg> cannot contain non-whitespace character data'
        )

    children = list(elem)
    if (
        len(children) != 1
        or children[0].tag != f'{{{SVG_NS}}}image'
    ):
        raise ValueError(
            'nested <svg> is reserved for imported picture crops; expected '
            'exactly one direct SVG-namespace <image> child'
        )
    image_elem = children[0]
    if image_elem.tail and image_elem.tail.strip():
        raise ValueError(
            'nested crop <svg> cannot contain non-whitespace character data'
        )
    if list(image_elem) or (image_elem.text and image_elem.text.strip()):
        raise ValueError('nested crop <image> must be an empty element')

    unsupported = _unsupported_nested_crop_attributes(
        image_elem,
        _NESTED_CROP_IMAGE_ATTRIBUTES,
    )
    if unsupported:
        raise ValueError(
            'nested crop <image> has unsupported attribute(s): '
            + ', '.join(unsupported)
        )

    try:
        _project_image_href(image_elem)
    except ValueError as exc:
        raise ValueError(f'nested crop <image> {exc}') from exc

    required_outer = (
        'x',
        'y',
        'width',
        'height',
        'viewBox',
        'preserveAspectRatio',
    )
    missing = [name for name in required_outer if elem.get(name) is None]
    if missing:
        raise ValueError(
            'nested crop <svg> requires explicit x, y, width, height, '
            'viewBox, and preserveAspectRatio="none"; missing '
            + ', '.join(missing)
        )
    if elem.get('preserveAspectRatio') != 'none':
        raise ValueError(
            'nested crop <svg> preserveAspectRatio must be exactly "none"'
        )

    frame_values: dict[str, float] = {}
    for name in ('x', 'y', 'width', 'height'):
        raw = elem.get(name)
        assert raw is not None
        try:
            frame_values[name] = parse_project_geometry_length(raw, name)
        except ValueError as exc:
            raise ValueError(
                f'nested crop <svg> {name}={raw!r}: {exc}'
            ) from exc
    if frame_values['width'] <= 0 or frame_values['height'] <= 0:
        raise ValueError('nested crop <svg> width and height must be positive')

    view_box = elem.get('viewBox') or ''
    view_box_tokens = view_box.strip().split()
    if (
        len(view_box_tokens) != 4
        or any(
            not is_canonical_project_geometry_length(token)
            for token in view_box_tokens
        )
    ):
        raise ValueError(
            'nested crop viewBox must contain four finite unitless ordinary '
            'decimals separated by whitespace'
        )
    vb_x, vb_y, vb_w, vb_h = (
        parse_project_geometry_length(token, 'x')
        for token in view_box_tokens
    )
    if vb_w <= 0 or vb_h <= 0:
        raise ValueError('nested crop viewBox width and height must be positive')
    src_l = round(vb_x * 100000)
    src_t = round(vb_y * 100000)
    src_r = round((1.0 - vb_x - vb_w) * 100000)
    src_b = round((1.0 - vb_y - vb_h) * 100000)
    src_values = (src_l, src_t, src_r, src_b)
    if (
        any(
            value < _DRAWINGML_PERCENTAGE_MIN
            or value > _DRAWINGML_PERCENTAGE_MAX
            for value in src_values
        )
        or src_l + src_r >= 100000
        or src_t + src_b >= 100000
    ):
        raise ValueError(
            'nested crop viewBox cannot be represented as a DrawingML '
            'srcRect with a positive visible region within the signed '
            'percentage range'
        )
    if not any(src_values):
        raise ValueError(
            'nested crop viewBox="0 0 1 1" is redundant; use a plain <image>'
        )

    required_image_values = {
        'x': '0',
        'y': '0',
        'width': '1',
        'height': '1',
        'preserveAspectRatio': 'none',
    }
    invalid_image_values = [
        f'{name}={image_elem.get(name)!r}'
        for name, expected in required_image_values.items()
        if image_elem.get(name) != expected
    ]
    if invalid_image_values:
        raise ValueError(
            'nested crop <image> must use x="0", y="0", width="1", '
            'height="1", and preserveAspectRatio="none"; got '
            + ', '.join(invalid_image_values)
        )

    return NestedSvgCropSpec(
        image=image_elem,
        x=frame_values['x'],
        y=frame_values['y'],
        width=frame_values['width'],
        height=frame_values['height'],
        src_l=src_l,
        src_t=src_t,
        src_r=src_r,
        src_b=src_b,
    )


def project_nested_svg_crop_errors(root: ET.Element) -> list[str]:
    """Return contract errors for every nested SVG transport wrapper."""
    errors: list[str] = []
    parent_by_id = {
        id(child): parent
        for parent in root.iter()
        for child in list(parent)
    }
    for elem in root.iter():
        if elem is root or elem.tag.rsplit('}', 1)[-1] != 'svg':
            continue
        elem_id = (elem.get('id') or '').strip()
        label = f'<svg id="{elem_id}">' if elem_id else '<svg>'
        ancestor = parent_by_id.get(id(elem))
        invalid_ancestor: ET.Element | None = None
        while ancestor is not None and ancestor is not root:
            if (
                ancestor.tag != f'{{{SVG_NS}}}g'
                or ancestor.get('data-pptx-part') is not None
            ):
                invalid_ancestor = ancestor
                break
            ancestor = parent_by_id.get(id(ancestor))
        if invalid_ancestor is not None:
            errors.append(
                f'{label} invalid imported crop wrapper: visual ancestor chain '
                'may contain only ordinary <g> elements'
            )
            continue
        try:
            parse_project_nested_svg_crop(elem)
        except ValueError as exc:
            errors.append(f'{label} invalid imported crop wrapper: {exc}')
    return sorted(errors)


def convert_nested_svg(elem: ET.Element, ctx: ConvertContext) -> ShapeResult:
    """Convert a nested <svg> sprite-crop wrapper to a DrawingML picture.

    Pattern produced by pptx_to_svg::

        <svg x="10" y="20" width="200" height="300" viewBox="0.5 0.3 0.5 0.7">
          <image href="..." x="0" y="0" width="1" height="1" preserveAspectRatio="none"/>
        </svg>

    The viewBox crops the unit-rectangle inner image; that crop is mapped to a
    DrawingML <a:srcRect> so PowerPoint can re-crop / "Reset Picture".
    """
    crop = parse_project_nested_svg_crop(elem)
    image_elem = crop.image
    source = load_project_image_source(image_elem, ctx.svg_dir)

    svg_x = crop.x
    svg_y = crop.y
    svg_w = crop.width
    svg_h = crop.height

    if ctx.use_transform_matrix:
        x = svg_x
        y = svg_y
        w = svg_w
        h = svg_h
    else:
        x = ctx_x(svg_x, ctx)
        y = ctx_y(svg_y, ctx)
        w = ctx_w(svg_w, ctx)
        h = ctx_h(svg_h, ctx)

    src_rect_xml = (
        f'<a:srcRect l="{crop.src_l}" t="{crop.src_t}" '
        f'r="{crop.src_r}" b="{crop.src_b}"/>'
    )

    img_format = source.img_format
    img_data = source.img_data

    img_data, img_format = _optimize_image_for_pptx(
        image_elem, ctx, img_data, img_format, w, h,
    )

    img_idx = len(ctx.media_files) + 1
    img_filename = f's{ctx.slide_num}_img{img_idx}.{img_format}'
    ctx.media_files[img_filename] = img_data

    r_id = ctx.next_rel_id()
    ctx.rel_entries.append({
        'id': r_id,
        'type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
        'target': f'../media/{img_filename}',
    })

    transform = elem.get('transform')

    shape_id = _claim_element_shape_id(elem, ctx)
    xfrm_attr, off_x, off_y, ext_cx, ext_cy, bounds_emu = _picture_xfrm_from_svg_rect(
        ctx,
        svg_x,
        svg_y,
        svg_w,
        svg_h,
        x,
        y,
        w,
        h,
        transform,
    )
    clip_geom = _resolve_clip_geometry(elem, ctx, svg_x, svg_y, svg_w, svg_h)
    blip_xml = _build_image_blip_xml(
        r_id,
        get_element_opacity(image_elem, ctx),
    )

    return ShapeResult(xml=f'''<p:pic>
<p:nvPicPr>
<p:cNvPr id="{shape_id}" name="Image {shape_id}"/>
<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
<p:nvPr/>
</p:nvPicPr>
<p:blipFill>
{blip_xml}
{src_rect_xml}<a:stretch><a:fillRect/></a:stretch>
</p:blipFill>
<p:spPr>
<a:xfrm{xfrm_attr}><a:off x="{off_x}" y="{off_y}"/>
<a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
{clip_geom}
</p:spPr>
</p:pic>''', bounds_emu=bounds_emu)
