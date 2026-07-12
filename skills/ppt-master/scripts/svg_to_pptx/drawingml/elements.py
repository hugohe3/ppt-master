"""SVG element converters: rect, circle, line, path, polygon, polyline, text, image, ellipse."""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import math
import re
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
from pptx_to_svg.preset_authoring import AUTHORING_ATTR, AUTHORING_VALUE
from resource_paths import resolve_external_image_reference

from .context import ConvertContext, ShapeResult
from .theme_colors import color_node_xml
from .theme_fonts import theme_font_tokens
from .utils import (
    SVG_NS, XLINK_NS, ANGLE_UNIT, FONT_PX_TO_HUNDREDTHS_PT, DASH_PRESETS,
    px_to_emu, _f, _get_attr, parse_svg_length,
    svg_length_x, svg_length_y, svg_length_size,
    ctx_x, ctx_y, ctx_w, ctx_h,
    rect_to_dml_xfrm,
    combine_opacity, parse_hex_color, parse_svg_color,
    resolve_url_id, get_effective_filter_id,
    parse_inline_style, parse_font_family, is_cjk_char, estimate_text_width,
    detect_text_lang, font_px_to_hpt, resolve_text_run_fonts,
    matrix_multiply, parse_transform_matrix, transform_point, _xml_escape,
)
from .styles import (
    build_solid_fill, build_gradient_fill,
    build_fill_xml, build_stroke_xml, build_effect_xml, classify_filter_effect,
    get_element_opacity, get_fill_opacity, get_stroke_opacity,
)
from .paths import (
    PathCommand, parse_svg_path, svg_path_to_absolute,
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


def _decode_data_image_uri(href: str) -> tuple[str, bytes] | None:
    """Decode SVG image data URIs, including URL-encoded non-base64 payloads."""
    if not href.startswith('data:') or ',' not in href:
        return None

    header, payload = href.split(',', 1)
    match = re.match(r'data:image/([^;,]+)', header, flags=re.IGNORECASE)
    if not match:
        return None

    img_format = match.group(1).lower()
    if img_format == 'svg+xml':
        img_format = 'svg'
    elif img_format == 'jpeg':
        img_format = 'jpg'

    is_base64 = any(
        part.strip().lower() == 'base64'
        for part in header.split(';')[1:]
    )
    if is_base64:
        img_data = base64.b64decode(payload)
    else:
        img_data = unquote_to_bytes(payload)
    return img_format, img_data


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
    if not dasharray or dasharray == 'none':
        return False
    stroke = _get_attr(elem, 'stroke', ctx)
    if not stroke or stroke == 'none':
        return False

    sw = svg_length_size(_get_attr(elem, 'stroke-width', ctx), ctx, 0)
    r = svg_length_size(elem.get('r'), ctx, 0)
    if sw <= 0 or r <= 0:
        return False

    # Standard dash presets are not donut segments
    if dasharray.strip() in DASH_PRESETS:
        return False

    # Thin strokes relative to radius are decorative dashed rings, not donut arcs.
    # Real donut arcs need sw/r >= 0.15 (e.g. sw=40 on r=100 → 0.40).
    if sw / r < 0.15:
        return False

    return True


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
        dash_vals = re.split(r'[\s,]+', dasharray.strip())
        dash_len = float(dash_vals[0]) if dash_vals else 0
        dash_offset = svg_length_size(elem.get('stroke-dashoffset'), ctx, 0)
        stroke_width = svg_length_size(_get_attr(elem, 'stroke-width', ctx), ctx, 1)

        rotate_deg = 0.0
        transform = elem.get('transform', '')
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rotate_deg = float(r_match.group(1))

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

def _parse_points(points_str: str) -> list[tuple[float, float]]:
    """Parse SVG points attribute into a list of (x, y) tuples."""
    nums = re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', points_str)
    if len(nums) < 4:
        return []
    return [(float(nums[i]), float(nums[i + 1])) for i in range(0, len(nums) - 1, 2)]


def convert_polygon(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <polygon> to DrawingML custom geometry shape."""
    preset_geom = _build_preset_geom_from_meta(elem)
    points = _parse_points(elem.get('points', ''))
    if not points:
        if preset_geom is not None:
            raise ValueError('Preset-bearing <polygon> requires valid points')
        return None

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
    points = _parse_points(elem.get('points', ''))
    if not points:
        if preset_geom is not None:
            raise ValueError('Preset-bearing <polyline> requires valid points')
        return None

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


def _normalize_text(text: str, *, preserve_space: bool = False) -> str:
    """Collapse runs of whitespace into a single space; do NOT strip the ends.

    Stripping at this layer would silently delete the inline boundary
    spaces in nested-tspan structures like
    ``<tspan>foo <tspan>bar</tspan> baz</tspan>``: the parent's text
    ("foo ") and the child's tail (" baz") would each lose the only space
    that separated them from the inner run, producing "foobarbaz".

    The paragraph's overall leading / trailing whitespace is removed once
    in ``_build_text_runs`` after all inline runs have been concatenated.
    """
    if not text:
        return ''
    if preserve_space:
        return text
    return re.sub(r'\s+', ' ', text)


def _preserves_space(elem: ET.Element) -> bool:
    xml_space = elem.get('{http://www.w3.org/XML/1998/namespace}space') or elem.get('xml:space')
    return xml_space == 'preserve'


def _parse_letter_spacing_px(
    value: str | None,
    *,
    font_size: float,
    scale_x: float = 1.0,
) -> float:
    """Parse an SVG letter-spacing value into scaled pixels."""
    if not value:
        return 0.0
    raw = value.strip().lower()
    if raw in {'normal', 'inherit', 'initial', 'unset'}:
        return 0.0

    match = re.fullmatch(r'([-+]?(?:\d*\.\d+|\d+\.?))(px|pt|em)?', raw)
    if not match:
        return 0.0

    amount = float(match.group(1))
    unit = match.group(2) or 'px'
    if unit == 'em':
        return amount * font_size
    if unit == 'pt':
        return amount * 4.0 / 3.0 * scale_x
    return amount * scale_x


def _letter_spacing_to_drawingml_spc(letter_spacing_px: float) -> str:
    """Convert SVG px letter spacing into DrawingML rPr@spc."""
    if abs(letter_spacing_px) < 1e-9:
        return ''
    spc_val = round(letter_spacing_px * FONT_PX_TO_HUNDREDTHS_PT)
    return f' spc="{spc_val}"'


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
    """Estimate one text run's rendered width, including tracking."""
    text = str(run.get('text', ''))
    base_width = estimate_text_width(
        text,
        float(run.get('font_size', 16)),
        str(run.get('font_weight', '400')),
    )
    letter_spacing_px = float(run.get('letter_spacing', 0.0) or 0.0)
    return base_width + letter_spacing_px * max(len(text) - 1, 0)


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


def _estimate_bullet_line_width(runs: list[dict[str, Any]]) -> float:
    line_runs, bullet = _extract_text_bullet(runs)
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


def _text_opacity_ratio(value: str | None) -> float:
    """Parse a text opacity component and clamp it to the SVG ``0..1`` range."""
    if value is None:
        return 1.0
    try:
        return max(0.0, min(1.0, float(value)))
    except ValueError:
        return 1.0


def _override_run_attrs(
    parent_attrs: dict[str, Any],
    tspan: ET.Element,
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
        run_attrs['font_weight'] = tspan_attr('font-weight')
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
    if tspan_attr('font-size'):
        run_attrs['font_size'] = parse_svg_length(
            tspan_attr('font-size'),
            run_attrs['font_size'],
            font_size=float(run_attrs.get('font_size', 16)),
        )
    if tspan_attr('font-family'):
        run_attrs['font_family'] = tspan_attr('font-family')
    if tspan_attr('font-style'):
        run_attrs['font_style'] = tspan_attr('font-style')
    if tspan_attr('text-decoration'):
        run_attrs['text_decoration'] = tspan_attr('text-decoration')
    if tspan_attr('letter-spacing'):
        run_attrs['letter_spacing'] = _parse_letter_spacing_px(
            tspan_attr('letter-spacing'),
            font_size=float(run_attrs.get('font_size', 16)),
            scale_x=float(run_attrs.get('_scale_x', 1.0)),
        )
    return run_attrs


def _collect_tspan_runs(
    tspan: ET.Element,
    inherited_attrs: dict[str, Any],
    preserve_space: bool = False,
) -> list[dict[str, Any]]:
    """Recursively turn a tspan subtree into runs, propagating styling through nested tspans.

    Order: tspan.text → (each nested child tspan's runs → that child's tail under THIS tspan's attrs).
    """
    runs: list[dict[str, Any]] = []
    own_attrs = _override_run_attrs(inherited_attrs, tspan)
    child_preserve_space = preserve_space or _preserves_space(tspan)

    if tspan.text:
        t = _normalize_text(tspan.text, preserve_space=child_preserve_space)
        if t:
            runs.append({**own_attrs, 'text': t})

    for child in tspan:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag == 'tspan':
            runs.extend(_collect_tspan_runs(child, own_attrs, child_preserve_space))
            if child.tail:
                t = _normalize_text(child.tail, preserve_space=child_preserve_space)
                if t:
                    runs.append({**own_attrs, 'text': t})

    return runs


def _build_text_runs(
    elem: ET.Element,
    parent_attrs: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build a list of text runs from a <text> element, handling <tspan> children.

    Each run is a dict with keys: text, fill, fill_raw, font_weight,
    font_style, font_family, font_size, letter_spacing. Nested tspans are walked
    recursively so inline format changes inside a tspan still produce distinct runs.
    """
    runs: list[dict[str, Any]] = []
    preserve_space = _preserves_space(elem)

    if elem.text:
        t = _normalize_text(elem.text, preserve_space=preserve_space)
        if t:
            runs.append({**parent_attrs, 'text': t})

    for child in elem:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag == 'tspan':
            runs.extend(_collect_tspan_runs(child, parent_attrs, preserve_space))
            if child.tail:
                t = _normalize_text(child.tail, preserve_space=preserve_space)
                if t:
                    runs.append({**parent_attrs, 'text': t})

    # Strip the paragraph's overall leading / trailing whitespace once unless
    # xml:space="preserve" asks us to keep source indentation.
    if runs and not preserve_space:
        runs[0]['text'] = runs[0]['text'].lstrip(' ')
        runs[-1]['text'] = runs[-1]['text'].rstrip(' ')
        runs = [r for r in runs if r['text']]

    return runs


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


def _build_run_xml(
    run: dict[str, Any],
    default_fonts: dict[str, str],
    ctx: ConvertContext | None = None,
    effect_xml: str = '',
) -> str:
    """Build a single <a:r> XML from a run dict. Supports gradient fills on text."""
    text = run['text']
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
    b_attr = ' b="1"' if fw in ('bold', '600', '700', '800', '900') else ''
    i_attr = ' i="1"' if fstyle == 'italic' else ''
    u_attr = ' u="sng"' if 'underline' in text_dec else ''
    strike_attr = ' strike="sngStrike"' if 'line-through' in text_dec else ''
    spc_attr = _letter_spacing_to_drawingml_spc(letter_spacing_px)

    fonts = parse_font_family(ff) if ff else default_fonts
    run_fonts = theme_font_tokens(
        fonts,
        ctx.theme_font_spec if ctx is not None else None,
    ) or resolve_text_run_fonts(text, fonts)
    lang = detect_text_lang(text)

    fill_xml = _build_text_fill_xml(fill, fill_raw, opacity, ctx)
    outline_xml = _build_text_outline_xml(run, ctx)

    space_attr = ' xml:space="preserve"' if text != text.strip() or '  ' in text else ''

    return f'''<a:r>
<a:rPr lang="{lang}" sz="{sz}"{b_attr}{i_attr}{u_attr}{strike_attr}{spc_attr} dirty="0">
{outline_xml}
{fill_xml}
{effect_xml}
<a:latin typeface="{_xml_escape(run_fonts['latin'])}"/>
<a:ea typeface="{_xml_escape(run_fonts['ea'])}"/>
<a:cs typeface="{_xml_escape(run_fonts['cs'])}"/>
</a:rPr>
<a:t{space_attr}>{_xml_escape(text)}</a:t>
</a:r>'''


def convert_text(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <text> to DrawingML text shape with multi-run support."""
    x = ctx_x(svg_length_x(elem.get('x'), ctx), ctx)
    y = ctx_y(svg_length_y(elem.get('y'), ctx), ctx)
    font_size = (
        parse_svg_length(_get_attr(elem, 'font-size', ctx), 16, font_size=16)
        * ctx.scale_y
    )
    font_weight = _get_attr(elem, 'font-weight', ctx) or '400'
    font_family_str = _get_attr(elem, 'font-family', ctx) or ''
    text_anchor = _get_attr(elem, 'text-anchor', ctx) or 'start'
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
    font_style = _get_attr(elem, 'font-style', ctx) or ''
    text_decoration = _get_attr(elem, 'text-decoration', ctx) or ''
    letter_spacing_px = _parse_letter_spacing_px(
        _get_attr(elem, 'letter-spacing', ctx),
        font_size=font_size,
        scale_x=ctx.scale_x or 1.0,
    )

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
        preserve_space = _preserves_space(elem)
        paragraph_runs = []
        for child in elem:
            if child.tag != f'{{{SVG_NS}}}tspan':
                continue
            line_runs = _collect_tspan_runs(child, parent_attrs, preserve_space)
            if line_runs and not preserve_space:
                line_runs[0]['text'] = line_runs[0]['text'].lstrip(' ')
                line_runs[-1]['text'] = line_runs[-1]['text'].rstrip(' ')
                line_runs = [r for r in line_runs if r['text']]
            if not line_runs:
                continue
            visual_line_widths.append(_estimate_bullet_line_width(line_runs))
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
                    prev[-1] = {**prev[-1], 'text': prev_text + ' '}
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
                stripped_paragraphs.append(stripped_runs)
                paragraph_bullets.append(bullet)
            paragraph_runs = stripped_paragraphs

    if paragraph_runs is not None:
        runs = [r for line in paragraph_runs for r in line]
    else:
        runs = _build_text_runs(elem, parent_attrs)
        runs, single_bullet = _extract_text_bullet(runs)

    if not runs:
        return None

    full_text = ''.join(r['text'] for r in runs)
    if not full_text.strip():
        return None

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
    if text_transform and 'rotate' not in text_transform and not ctx.use_transform_matrix:
        try:
            a, b, c, d, e, f = parse_transform_matrix(text_transform)
        except Exception:
            a, b, c, d, e, f = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
        # A pure-translate transform on a text element (hand-authored, or written
        # by a live-preview move) was otherwise ignored here, drifting the text.
        # Absorb the translation into the frame position; a scaling transform
        # would also need to scale font size / line metrics, so leave
        # non-translate transforms alone.
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
    if text_transform:
        rot_match = re.search(
            r'rotate\(\s*([-\d.]+)(?:[\s,]+([-\d.]+)[\s,]+([-\d.]+))?',
            text_transform,
        )
        if rot_match:
            angle_deg = float(rot_match.group(1))
            text_rot = int(angle_deg * ANGLE_UNIT)
            if rot_match.group(2) is not None:
                pivot_x = ctx_x(float(rot_match.group(2)), ctx)
                pivot_y = ctx_y(float(rot_match.group(3)), ctx)
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
    ext_cx = px_to_emu(box_w)
    ext_cy = px_to_emu(box_h)

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
        rx = _f(shape.get('rx'))
        ry = _f(shape.get('ry'), rx)
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
        pts = _parse_points(shape.get('points', ''))
        if not pts:
            return DEFAULT
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
    except (UnidentifiedImageError, OSError, ValueError):
        return (None, None)


def _parse_preserve_aspect_ratio(par: str | None) -> tuple[str, str]:
    """Parse SVG preserveAspectRatio into ``(align, mode)``."""
    parts = (par or 'xMidYMid meet').strip().split()
    align = parts[0] if parts else 'xMidYMid'
    mode = parts[1] if len(parts) > 1 else 'meet'
    return align, mode


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

    align, mode = _parse_preserve_aspect_ratio(elem.get('preserveAspectRatio'))
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

    x_anchor = {'xMin': 0.0, 'xMid': 0.5, 'xMax': 1.0}.get(align[:4], 0.5)
    y_anchor = {'YMin': 0.0, 'YMid': 0.5, 'YMax': 1.0}.get(align[4:], 0.5)

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
    align, mode = _parse_preserve_aspect_ratio(elem.get('preserveAspectRatio'))

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
    align, mode = _parse_preserve_aspect_ratio(elem.get('preserveAspectRatio'))

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

    x_anchor = {'xMin': 0.0, 'xMid': 0.5, 'xMax': 1.0}.get(align[:4], 0.5)
    y_anchor = {'YMin': 0.0, 'YMid': 0.5, 'YMax': 1.0}.get(align[4:], 0.5)

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
    href = elem.get('href') or elem.get(f'{{{XLINK_NS}}}href')
    if not href:
        return None

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
        return None

    # Extract image data
    if href.startswith('data:'):
        decoded = _decode_data_image_uri(href)
        if decoded is None:
            return None
        img_format, img_data = decoded
    else:
        if ctx.svg_dir is None:
            return None
        img_path = _resolve_external_image(ctx.svg_dir, href)
        img_format = img_path.suffix.lstrip('.').lower()
        if img_format == 'jpeg':
            img_format = 'jpg'
        img_data = img_path.read_bytes()

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

def convert_nested_svg(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert a nested <svg> sprite-crop wrapper to a DrawingML picture.

    Pattern produced by pptx_to_svg::

        <svg x="10" y="20" width="200" height="300" viewBox="0.5 0.3 0.5 0.7">
          <image href="..." x="0" y="0" width="1" height="1" preserveAspectRatio="none"/>
        </svg>

    The viewBox crops the unit-rectangle inner image; that crop is mapped to a
    DrawingML <a:srcRect> so PowerPoint can re-crop / "Reset Picture".
    """
    image_elem = elem.find(f'{{{SVG_NS}}}image')
    if image_elem is None:
        image_elem = elem.find('image')
    if image_elem is None:
        return None

    href = image_elem.get('href') or image_elem.get(f'{{{XLINK_NS}}}href')
    if not href:
        return None

    svg_x = svg_length_x(elem.get('x'), ctx)
    svg_y = svg_length_y(elem.get('y'), ctx)
    svg_w = svg_length_x(elem.get('width'), ctx)
    svg_h = svg_length_y(elem.get('height'), ctx)
    if svg_w <= 0 or svg_h <= 0:
        return None

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

    src_rect_xml = ''
    view_box = elem.get('viewBox', '')
    if view_box:
        parts = view_box.strip().split()
        if len(parts) == 4:
            vb_x, vb_y, vb_w, vb_h = (float(p) for p in parts)
            l = max(0, min(int(round(vb_x * 100000)), 100000))
            t = max(0, min(int(round(vb_y * 100000)), 100000))
            r = max(0, min(int(round((1.0 - vb_x - vb_w) * 100000)), 100000))
            b = max(0, min(int(round((1.0 - vb_y - vb_h) * 100000)), 100000))
            if l or t or r or b:
                src_rect_xml = f'<a:srcRect l="{l}" t="{t}" r="{r}" b="{b}"/>'

    if href.startswith('data:'):
        decoded = _decode_data_image_uri(href)
        if decoded is None:
            return None
        img_format, img_data = decoded
    else:
        if ctx.svg_dir is None:
            return None
        img_path = _resolve_external_image(ctx.svg_dir, href)
        img_format = img_path.suffix.lstrip('.').lower()
        if img_format == 'jpeg':
            img_format = 'jpg'
        img_data = img_path.read_bytes()

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
