"""Core SVG -> DrawingML dispatcher, group handling, and main entry point."""

from __future__ import annotations

import base64
import binascii
import hashlib
import math
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from pptx_shapes import (
    has_relationship_attributes,
    resolve_preset_preview_hash,
    svg_preset_preview_fingerprint,
    svg_text_fingerprint,
    validate_ooxml_xfrm,
)
from pptx_effects import project_effect_status_errors, txbody_has_run_effects
from pptx_to_svg.preset_authoring import (
    materialize_compact_authored_preset_tree,
    validate_authored_preset_tree,
)
from resource_paths import icon_search_dirs_for_svg

from .context import ConvertContext, ShapeResult
from .paths import (
    project_freeform_geometry_errors,
    project_gradient_geometry_errors,
)
from .theme_colors import ThemeColorSpec
from .theme_fonts import ThemeFontSpec
from .text_properties import (
    materialize_project_text_metrics,
    project_text_property_errors,
    resolve_project_font_sizes,
    resolve_project_letter_spacings,
)
from .utils import (
    EMU_PER_PX,
    SVG_NS,
    _extract_inheritable_styles,
    _get_attr,
    _is_unit_axis_reflection,
    parse_svg_length,
    parse_transform_operations,
    parse_transform_matrix,
    project_definition_errors,
    project_definition_index,
    project_filter_errors,
    project_geometry_length_errors,
    project_gradient_errors,
    project_image_aspect_ratio_errors,
    project_marker_errors,
    project_opacity_errors,
    project_paint_errors,
    project_paint_reference_errors,
    project_stroke_style_errors,
    project_transform_errors,
    resolve_url_id,
    supports_full_project_transform,
    validate_dml_shape_matrix,
)
from .styles import (
    build_effect_xml, build_fill_xml,
    get_element_opacity, get_fill_opacity, get_stroke_opacity,
)
from .elements import (
    convert_rect, convert_circle, convert_ellipse,
    convert_line, convert_path,
    convert_polygon, convert_polyline,
    convert_text, convert_image, convert_nested_svg,
    project_clip_path_errors,
    project_image_errors,
    project_nested_svg_crop_errors,
)
from ..animation_config import is_chrome_id, usable_animation_group_id
from ..canvas_contract import (
    CanvasContractError,
    parse_project_svg_root,
    parse_project_viewbox,
)
from ..native_objects import (
    NativeMarkerAttributeError,
    convert_native_object,
    native_metadata_payload_matches,
    native_replacement_kind,
    native_marker_transform,
    snapshot_native_fallback_freshness,
)
from ..native_objects.marker_status import native_marker_status_errors
from ..semantic_markers import is_static_page_frame


class SvgNativeConversionError(RuntimeError):
    """Raised when an SVG cannot be faithfully converted to native DrawingML."""


def _require_chart_table_marker_attributes(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject contradictory chart/table marker aliases before either route."""
    errors: list[str] = []
    for elem in root.iter():
        if elem.tag.rsplit('}', 1)[-1] == 'metadata':
            continue
        marker_errors = native_marker_status_errors(elem)
        if marker_errors:
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            errors.extend(f'{marker_id}: {error}' for error in marker_errors)
            continue
        marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
        kind = native_replacement_kind(elem)
        if not kind:
            continue
        for child in elem:
            if child.tag.rsplit('}', 1)[-1] != 'metadata':
                continue
            try:
                native_metadata_payload_matches(child, kind)
            except NativeMarkerAttributeError as exc:
                errors.append(f'{marker_id}: {exc}')
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid chart/table replacement metadata: '
        f'{preview}{suffix}'
    )


def _require_project_freeform_geometry(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject malformed path and points values with one aggregated error."""
    errors = project_freeform_geometry_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project freeform geometry: '
        f'{preview}{suffix}'
    )


def _require_project_nested_svg_crops(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject nested SVG outside the imported picture-crop transport."""
    errors = project_nested_svg_crop_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid nested SVG crop wrapper(s): '
        f'{preview}{suffix}'
    )


def _require_project_clip_paths(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject clip references that cannot produce native picture geometry."""
    errors = project_clip_path_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project clip-path(s): '
        f'{preview}{suffix}'
    )


def _require_project_images(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject invalid picture frames and unresolved or corrupt sources."""
    path = Path(svg_path)
    errors = project_image_errors(root, path.parent)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{path.name}: invalid project image(s): {preview}{suffix}'
    )


def _require_project_transforms(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject invalid project transform syntax and mappings before conversion."""
    errors = project_transform_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project transform(s): '
        f'{preview}{suffix}'
    )


def _require_project_stroke_styles(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject invalid project line-style syntax and mappings before conversion."""
    errors = project_stroke_style_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project line style(s): '
        f'{preview}{suffix}'
    )


def _require_project_image_aspect_ratios(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject ambiguous image fit/crop values before native conversion."""
    errors = project_image_aspect_ratio_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project image aspect ratio(s): '
        f'{preview}{suffix}'
    )


def _require_project_opacities(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject malformed opacity values before native conversion."""
    errors = project_opacity_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project opacity value(s): '
        f'{preview}{suffix}'
    )


def _require_project_paints(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject invalid paint values before native conversion."""
    errors = project_paint_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project paint value(s): '
        f'{preview}{suffix}'
    )


def _require_project_definitions(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject definitions outside the direct, unique local-ref contract."""
    errors = project_definition_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project definition(s): '
        f'{preview}{suffix}'
    )


def _require_project_paint_references(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject unresolved or context-invalid local paint references."""
    errors = project_paint_reference_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project paint reference(s): '
        f'{preview}{suffix}'
    )


def _require_project_line_end_markers(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject markers outside the native line-end contract."""
    errors = project_marker_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project line-end marker(s): '
        f'{preview}{suffix}'
    )


def _require_project_gradients(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject gradients outside the normalized native interface."""
    errors = project_gradient_errors(root) + project_gradient_geometry_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project gradient(s): '
        f'{preview}{suffix}'
    )


def _require_project_filters(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject filters outside the native shadow/glow interface."""
    errors = project_filter_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project filter(s): '
        f'{preview}{suffix}'
    )


def _require_project_effect_status(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject source effects that the importer cannot map without distortion."""
    errors = project_effect_status_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: unsupported imported PPTX effect(s): '
        f'{preview}{suffix}'
    )


def _require_project_text_properties(
    root: ET.Element,
    svg_path: Path | str,
) -> None:
    """Reject text declarations outside the closed DrawingML mapping."""
    errors = project_text_property_errors(root)
    if not errors:
        return
    preview = '; '.join(errors[:8])
    suffix = '' if len(errors) <= 8 else f'; +{len(errors) - 8} more'
    raise SvgNativeConversionError(
        f'{Path(svg_path).name}: invalid project text property(s): '
        f'{preview}{suffix}'
    )


# ---------------------------------------------------------------------------
# Transform & layout helpers
# ---------------------------------------------------------------------------

def parse_transform(transform_str: str) -> tuple[float, float, float, float, float]:
    """Parse an SVG transform list into (dx, dy, sx, sy, angle_deg).

    Composes every translate/scale/rotate/matrix operation rather than picking
    the first occurrence — needed for idioms like
    ``translate(cx cy) scale(-1 -1) translate(-cx -cy)`` which encode a flip
    around a non-origin pivot.

    When the composed matrix has no rotation, the decomposition preserves
    signed scale for flips. With rotation, scale uses the column magnitudes and
    angle uses the first transformed axis. Zero or non-orthogonal axes fail
    before decomposition because this tuple cannot represent them faithfully.
    """
    if not transform_str:
        return 0.0, 0.0, 1.0, 1.0, 0.0

    matrix = parse_transform_matrix(transform_str)
    validate_dml_shape_matrix(matrix)
    a, b, c, d, e, f = matrix

    # No shear / rotation: direct decomposition preserves the original signs of
    # sx / sy. ctx_x / ctx_y use the simple ``val * sx + tx`` formula, so this
    # is the only form that survives flip-around-pivot composites without
    # collapsing them into a rotation that the consumer can't honour.
    if abs(b) < 1e-9 and abs(c) < 1e-9:
        sx = a if a != 0 else 1.0
        sy = d if d != 0 else 1.0
        return e, f, sx, sy, 0.0

    sx = math.hypot(a, b)
    sy = math.hypot(c, d)
    if sx == 0:
        sx = 1.0
    if sy == 0:
        sy = 1.0

    angle_deg = math.degrees(math.atan2(b, a))
    return e, f, sx, sy, angle_deg


# ``rotate(angle)`` defaults to pivot (0,0); ``rotate(angle, cx, cy)`` rotates
# around (cx, cy). DrawingML grpSp ``rot`` always rotates around the group's
# own bounding-box centre — we need the SVG pivot so ``convert_g`` can
# compensate for the offset between those two centres.
def _root_viewport_size(root: ET.Element) -> tuple[float, float]:
    """Return the SVG root viewport size in user units."""
    viewbox = parse_project_viewbox(root.get('viewBox'))
    return float(viewbox.width), float(viewbox.height)


def _extract_rotate_pivot(transform_str: str) -> tuple[float, float] | None:
    """Return the (cx, cy) pivot of a sole ``rotate(...)`` in *transform_str*.

    Returns ``None`` when the transform list contains anything other than one
    rotate (other ops compose with rotate in a way the pivot-compensation
    fallback can't express). A bare ``rotate(angle)`` returns (0, 0).
    """
    if not transform_str:
        return None
    operations = parse_transform_operations(transform_str)
    if len(operations) != 1 or operations[0][0] != 'rotate':
        return None
    args = operations[0][1]
    cx = args[1] if len(args) == 3 else 0.0
    cy = args[2] if len(args) == 3 else 0.0
    return cx, cy


def _txbody_metadata(elem: ET.Element) -> ET.Element | None:
    for child in elem:
        if (
            child.tag.replace(f'{{{SVG_NS}}}', '') == 'metadata'
            and child.get('data-pptx-part') == 'txbody'
        ):
            return child
    return None


_TXBODY_UNCHANGED_ATTR = 'data-pptx-runtime-txbody-unchanged'
_PREVIEW_UNCHANGED_ATTR = 'data-pptx-runtime-preview-unchanged'


def _mark_unchanged_txbody_groups(root: ET.Element) -> None:
    """Snapshot author-visible text state before exporter preprocessing."""
    for group in root.iter():
        if group.tag.replace(f'{{{SVG_NS}}}', '') != 'g':
            continue
        metadata = _txbody_metadata(group)
        if metadata is None:
            continue
        expected = metadata.get('data-pptx-text-sha256')
        actual = svg_text_fingerprint(group)
        group.set(_TXBODY_UNCHANGED_ATTR, '1' if expected == actual else '0')


def _mark_unchanged_preset_previews(root: ET.Element) -> None:
    """Snapshot visible preset layers before exporter preprocessing."""
    for group in root.iter():
        if group.tag.replace(f'{{{SVG_NS}}}', '') != 'g':
            continue
        if (
            group.get('data-pptx-object') not in {'shape', 'connector'}
            or group.get('data-pptx-prst') is None
        ):
            continue
        try:
            expected = resolve_preset_preview_hash(group)
        except ValueError as exc:
            raise SvgNativeConversionError(
                f'Invalid preset preview fingerprint contract: {exc}'
            ) from exc
        if expected is None:
            continue
        actual = svg_preset_preview_fingerprint(group)
        group.set(_PREVIEW_UNCHANGED_ATTR, '1' if expected == actual else '0')


def _require_unchanged_preset_preview(group: ET.Element) -> None:
    try:
        expected = resolve_preset_preview_hash(group)
    except ValueError as exc:
        raise SvgNativeConversionError(
            f'Invalid preset preview fingerprint contract: {exc}'
        ) from exc
    if expected is None:
        return
    snapshot = group.get(_PREVIEW_UNCHANGED_ATTR)
    if snapshot == '1':
        return
    if snapshot is None and svg_preset_preview_fingerprint(group) == expected:
        return
    raise SvgNativeConversionError(
        'Visible preset preview was edited without updating its native '
        'data-pptx-prst/frame/adjustment carrier; export stopped to avoid '
        'silently discarding the SVG edit'
    )


def _decode_unchanged_txbody(
    group: ET.Element,
    metadata: ET.Element,
    *,
    trust_runtime_snapshot: bool = True,
) -> tuple[str, bool] | None:
    expected_hash = metadata.get('data-pptx-text-sha256')
    if not expected_hash:
        raise SvgNativeConversionError('txbody metadata requires a text hash')
    snapshot = (
        group.get(_TXBODY_UNCHANGED_ATTR)
        if trust_runtime_snapshot else None
    )
    unchanged = snapshot == '1' or (
        snapshot != '0'
        and svg_text_fingerprint(group) == expected_hash
    )
    if metadata.get('data-pptx-encoding') != 'base64':
        raise SvgNativeConversionError('txbody metadata requires base64 encoding')
    try:
        raw = base64.b64decode((metadata.text or '').strip(), validate=True)
        txbody = ET.fromstring(raw)
        decoded = raw.decode('utf-8')
    except (ValueError, binascii.Error, UnicodeDecodeError, ET.ParseError) as exc:
        raise SvgNativeConversionError(f'Invalid txbody metadata: {exc}') from exc
    if txbody.tag != (
        '{http://schemas.openxmlformats.org/presentationml/2006/main}txBody'
    ):
        raise SvgNativeConversionError('txbody metadata payload must be p:txBody')
    if has_relationship_attributes(txbody):
        raise SvgNativeConversionError(
            'txbody metadata must not contain part-local relationship attributes'
        )
    if not unchanged:
        if txbody_has_run_effects(txbody):
            raise SvgNativeConversionError(
                'Visible text or typography was edited while the source '
                'txBody contains run-level effects; export stopped to avoid '
                'silently discarding those effects'
            )
        return None
    return decoded, txbody_has_run_effects(txbody)


def _append_shape_text(
    shape: ShapeResult,
    txbody_xml: str,
) -> ShapeResult:
    if not shape.xml.lstrip().startswith('<p:sp>') or not shape.xml.rstrip().endswith('</p:sp>'):
        raise SvgNativeConversionError('Native txBody can only attach to p:sp')
    closing = shape.xml.rfind('</p:sp>')
    return ShapeResult(
        xml=(
            shape.xml[:closing]
            + txbody_xml
            + '\n'
            + shape.xml[closing:]
        ),
        bounds_emu=shape.bounds_emu,
    )


def preserved_native_text_body(
    group: ET.Element,
    *,
    trust_runtime_snapshot: bool = True,
) -> tuple[ET.Element, str] | None:
    """Return the geometry carrier and unchanged native text body, if usable."""
    metadata = _txbody_metadata(group)
    logical_text_shape = (
        group.get('data-pptx-object') == 'shape'
        and (
            group.get('data-pptx-prst') is not None
            or group.get('data-pptx-geometry-kind') == 'custom'
        )
        and metadata is not None
    )
    if not logical_text_shape:
        return None
    decoded_text = _decode_unchanged_txbody(
        group,
        metadata,
        trust_runtime_snapshot=trust_runtime_snapshot,
    )
    carrier_children = [
        child for child in group
        if child.get('data-pptx-part') == 'geometry'
    ]
    allowed_parts = {
        'geometry',
        'geometry-detail',
        'geometry-preview',
        'txbody',
    }
    has_foreign_visual = any(
        child.tag.replace(f'{{{SVG_NS}}}', '') not in {'text', 'metadata'}
        and child.get('data-pptx-part') not in allowed_parts
        for child in group
    )
    if decoded_text is None:
        return None
    native_text, has_run_effects = decoded_text
    if len(carrier_children) != 1 or has_foreign_visual:
        if has_run_effects:
            raise SvgNativeConversionError(
                'The source txBody contains run-level effects but cannot be '
                'restored as one native text shape; export stopped to avoid '
                'silently discarding those effects'
            )
        return None
    return carrier_children[0], native_text


# ---------------------------------------------------------------------------
# Group handling
# ---------------------------------------------------------------------------

def convert_g(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <g> to DrawingML group shape <p:grpSp>.

    Preserves group structure so elements can be selected and moved together
    in PowerPoint. Single-child groups are flattened to avoid unnecessary nesting.

    Uses identity coordinate mapping (chOff/chExt == off/ext) so child shapes
    keep their absolute slide coordinates unchanged.
    """
    transform = elem.get('transform', '')
    native_subtree_active = ctx.native_objects_enabled and any(
        native_replacement_kind(descendant)
        and descendant.tag.replace(f'{{{SVG_NS}}}', '') != 'metadata'
        for descendant in elem.iter()
    )
    if native_subtree_active:
        dx, dy, sx, sy = native_marker_transform(transform)
        angle_deg = 0.0
    else:
        dx, dy, sx, sy, angle_deg = parse_transform(transform)

    filter_id = resolve_url_id(elem.get('filter', ''))
    style_overrides = _extract_inheritable_styles(elem)
    local_opacity = get_element_opacity(elem)
    if local_opacity is None:
        local_opacity = 1.0

    elem_id = usable_animation_group_id(elem.get('id'))
    semantic_role = elem.get('data-pptx-role')
    placeholder = elem.get('data-pptx-placeholder')
    has_explicit_semantics = (
        semantic_role is not None or placeholder is not None
    )
    is_chrome = (
        is_static_page_frame(semantic_role, placeholder)
        if has_explicit_semantics
        else is_chrome_id(elem_id)
    )
    should_animate_group = (
        ctx.depth == 0
        and elem_id
        and (
            not is_chrome
            or (
                not has_explicit_semantics
                and elem_id in ctx.animation_group_overrides
            )
        )
        and elem.get('data-pptx-layer') is None
    )
    visual_children = [
        child for child in elem
        if child.tag.replace(f'{{{SVG_NS}}}', '') not in _NON_VISUAL_TAGS
    ]
    unit_axis_reflection = (
        bool(transform)
        and _is_unit_axis_reflection(parse_transform_operations(transform))
    )
    matrix_supported = (
        not native_subtree_active
        and bool(transform)
        and visual_children
        and (
            supports_full_project_transform(elem)
            or unit_axis_reflection
        )
    )
    # A pure ``rotate(angle [cx cy])`` falls through to the fallback path
    # below (children are rect/text/path/etc. that don't consume a full
    # matrix). Decomposing the matrix produces translation components
    # (e, f) that encode the pivot — handing those to children would
    # *double-translate* them because grpSp's own ``rot`` already
    # rotates around the group's bounding-box centre. Skip the child
    # translation here and apply pivot-centre compensation to ``a:off``
    # below instead.
    rotate_pivot = _extract_rotate_pivot(transform) if not matrix_supported else None
    if matrix_supported:
        child_ctx = ctx.child(
            0, 0, 1.0, 1.0,
            transform_matrix=parse_transform_matrix(transform),
            filter_id=filter_id,
            style_overrides=style_overrides,
            opacity_multiplier=local_opacity,
        )
    elif rotate_pivot is not None:
        child_ctx = ctx.child(
            0, 0, 1.0, 1.0,
            filter_id=filter_id,
            style_overrides=style_overrides,
            opacity_multiplier=local_opacity,
        )
    else:
        child_ctx = ctx.child(
            ctx.scale_x * dx if native_subtree_active else dx,
            ctx.scale_y * dy if native_subtree_active else dy,
            sx,
            sy,
            filter_id=filter_id,
            style_overrides=style_overrides,
            opacity_multiplier=local_opacity,
        )

    if native_subtree_active and child_ctx.opacity_multiplier < 1.0:
        raise SvgNativeConversionError(
            "Group opacity cannot be applied to data-pptx-replace-with chart/table "
            "objects; export without --native-charts-and-tables to use the "
            "shape-based SVG fallback"
        )

    if child_ctx.native_objects_enabled:
        native_result = convert_native_object(elem, child_ctx)
        if native_result:
            ctx.sync_from_child(child_ctx)
            if should_animate_group:
                shape_match = re.search(r'<p:cNvPr id="(\d+)"', native_result.xml)
                if shape_match:
                    ctx.anim_targets.append((int(shape_match.group(1)), elem_id))
            return native_result

    if (
        elem.get('data-pptx-object') in {'shape', 'connector'}
        and elem.get('data-pptx-prst') is not None
    ):
        _require_unchanged_preset_preview(elem)

    preserved_text = preserved_native_text_body(elem)
    if preserved_text is not None:
        geometry_carrier, native_text = preserved_text
        geometry_ctx = child_ctx
        if transform and not native_subtree_active:
            geometry_ctx = ctx.child(
                0, 0, 1.0, 1.0,
                transform_matrix=parse_transform_matrix(transform),
                filter_id=filter_id,
                style_overrides=style_overrides,
                opacity_multiplier=local_opacity,
            )
        geometry_result = convert_element(geometry_carrier, geometry_ctx)
        ctx.sync_from_child(geometry_ctx)
        if geometry_result is None:
            raise SvgNativeConversionError(
                'Logical text shape has no convertible geometry carrier'
            )
        restored = _append_shape_text(
            geometry_result,
            native_text,
        )
        if should_animate_group and elem_id:
            shape_match = re.search(r'<p:cNvPr id="(\d+)"', restored.xml)
            if shape_match:
                ctx.anim_targets.append((int(shape_match.group(1)), elem_id))
        return restored

    child_results: list[ShapeResult] = []
    for child in elem:
        result = convert_element(child, child_ctx)
        if result:
            child_results.append(result)

    ctx.sync_from_child(child_ctx)

    if not child_results:
        return None

    # A logical imported preset may contain several render-only SVG detail
    # paths, but after those are skipped it owns exactly one native object.
    # Flatten that carrier even at the top level; otherwise animation grouping
    # would turn one source ``p:sp`` into a ``p:grpSp`` wrapper. Retarget an
    # optional animation to the restored leaf shape ID.
    logical_native_shape_group = (
        elem.get('data-pptx-object') in {'shape', 'connector'}
        and (
            elem.get('data-pptx-prst') is not None
            or elem.get('data-pptx-geometry-kind') == 'custom'
        )
    )
    explicit_native_group = elem.get('data-pptx-object') == 'group'
    if (
        len(child_results) == 1
        and not explicit_native_group
        and (not should_animate_group or logical_native_shape_group)
    ):
        if should_animate_group and elem_id:
            shape_match = re.search(r'<p:cNvPr id="(\d+)"', child_results[0].xml)
            if shape_match:
                ctx.anim_targets.append((int(shape_match.group(1)), elem_id))
        return child_results[0]

    # Multiple children, or a top-level semantic one-child group: wrap in
    # <p:grpSp> so PowerPoint can animate the group as one unit.
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    for child_result in child_results:
        bounds = child_result.bounds_emu
        if bounds is None:
            continue
        min_x = min(min_x, bounds[0])
        min_y = min(min_y, bounds[1])
        max_x = max(max_x, bounds[2])
        max_y = max(max_y, bounds[3])

    if min_x == float('inf'):
        return ShapeResult(xml='\n'.join(result.xml for result in child_results))

    group_x = int(min_x)
    group_y = int(min_y)
    group_w = max(int(max_x - min_x), 1)
    group_h = max(int(max_y - min_y), 1)

    # ``rotate(angle, cx, cy)`` rotates around the SVG pivot, but DrawingML
    # grpSp ``rot`` always rotates around the group's own bbox centre. When
    # those centres differ, the visual position drifts by exactly the
    # translation a rotate-around-pivot equals. Compensate by offsetting the
    # outer <a:off> only; <a:chOff> stays on the unshifted bbox so children
    # (still at their original SVG positions because rotate_pivot suppressed
    # the dx/dy translation above) remain aligned inside the group.
    off_x = group_x
    off_y = group_y
    if rotate_pivot is not None and angle_deg:
        cx_svg, cy_svg = rotate_pivot
        pivot_ex = (cx_svg + ctx.translate_x) * EMU_PER_PX
        pivot_ey = (cy_svg + ctx.translate_y) * EMU_PER_PX
        bbox_cx = group_x + group_w / 2
        bbox_cy = group_y + group_h / 2
        theta = math.radians(angle_deg)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        # Where the bbox centre lands after rotating around the pivot, minus
        # where DrawingML's grpSp rot would leave it (i.e. unchanged).
        delta_x = (bbox_cx - pivot_ex) * cos_t - (bbox_cy - pivot_ey) * sin_t + pivot_ex - bbox_cx
        delta_y = (bbox_cx - pivot_ex) * sin_t + (bbox_cy - pivot_ey) * cos_t + pivot_ey - bbox_cy
        off_x = int(round(group_x + delta_x))
        off_y = int(round(group_y + delta_y))

    shapes_xml = '\n'.join(result.xml for result in child_results)
    group_id = (
        ctx.claim_shape_id(
            elem.get('data-pptx-shape-id'),
            elem.get('data-pptx-shape-scope'),
        )
        if elem.get('data-pptx-object') == 'group'
        else ctx.next_id()
    )

    # Record top-level semantic groups (e.g. <g id="p02-title">) so the
    # PPTX builder can emit per-element entrance timing. Only the outermost
    # multi-child wrapper qualifies — flattened single-child groups have no
    # <p:grpSp> to anchor a timing target on, and nested groups are
    # ignored to keep the animation budget at ~per-section granularity.
    if should_animate_group:
        ctx.anim_targets.append((group_id, elem_id))

    group_effect = ''
    if filter_id and filter_id in ctx.defs:
        group_effect = build_effect_xml(
            ctx.defs[filter_id],
            child_ctx.opacity_multiplier,
        )

    rot_emu = 0 if matrix_supported else int(angle_deg * 60000)
    rot_attr = f' rot="{rot_emu}"' if rot_emu else ''
    validate_ooxml_xfrm(off_x, off_y, group_w, group_h)
    validate_ooxml_xfrm(group_x, group_y, group_w, group_h)

    return ShapeResult(xml=f'''<p:grpSp>
<p:nvGrpSpPr>
<p:cNvPr id="{group_id}" name="Group {group_id}"/>
<p:cNvGrpSpPr/>
<p:nvPr/>
</p:nvGrpSpPr>
<p:grpSpPr>
<a:xfrm{rot_attr}>
<a:off x="{off_x}" y="{off_y}"/>
<a:ext cx="{group_w}" cy="{group_h}"/>
<a:chOff x="{group_x}" y="{group_y}"/>
<a:chExt cx="{group_w}" cy="{group_h}"/>
</a:xfrm>
{group_effect}
</p:grpSpPr>
{shapes_xml}
</p:grpSp>''', bounds_emu=(group_x, group_y, group_x + group_w, group_y + group_h))


# ---------------------------------------------------------------------------
# Defs collection & element dispatch
# ---------------------------------------------------------------------------

_NON_VISUAL_TAGS = frozenset(('defs', 'title', 'desc', 'metadata', 'style'))

_CONVERTERS = {
    'rect': convert_rect,
    'circle': convert_circle,
    'ellipse': convert_ellipse,
    'line': convert_line,
    'path': convert_path,
    'polygon': convert_polygon,
    'polyline': convert_polyline,
    'text': convert_text,
    'image': convert_image,
    'g': convert_g,
    'svg': convert_nested_svg,
}

_SUPPORTED_VISUAL_CHILD_TAGS = frozenset(('tspan',))


def _parse_svg_canvas(root: ET.Element) -> tuple[float, float, float, float]:
    """Return the SVG canvas as (x, y, width, height) in SVG units."""
    viewbox = parse_project_viewbox(root.get('viewBox'))
    return 0.0, 0.0, float(viewbox.width), float(viewbox.height)


def _is_full_canvas_rect(
    elem: ET.Element,
    ctx: ConvertContext,
    canvas: tuple[float, float, float, float],
) -> bool:
    """Return whether a rect is a safe candidate for native slide background."""
    if elem.get('transform') or elem.get('filter') or elem.get('clip-path'):
        return False
    if any(
        elem.get(attr) is not None
        for attr in (
            'data-pptx-object',
            'data-pptx-prst',
            'data-pptx-frame',
            'data-pptx-geometry-status',
        )
    ):
        return False
    if (
        parse_svg_length(elem.get('rx'), 0.0) > 0
        or parse_svg_length(elem.get('ry'), 0.0) > 0
    ):
        return False

    canvas_x, canvas_y, canvas_w, canvas_h = canvas
    if canvas_w <= 0 or canvas_h <= 0:
        return False

    tolerance = 0.5
    if abs(parse_svg_length(elem.get('x'), 0.0) - canvas_x) > tolerance:
        return False
    if abs(parse_svg_length(elem.get('y'), 0.0) - canvas_y) > tolerance:
        return False
    if abs(parse_svg_length(elem.get('width'), 0.0) - canvas_w) > tolerance:
        return False
    if abs(parse_svg_length(elem.get('height'), 0.0) - canvas_h) > tolerance:
        return False

    fill = _get_attr(elem, 'fill', ctx)
    if fill == 'none':
        return False

    stroke = _get_attr(elem, 'stroke', ctx)
    stroke_width = parse_svg_length(_get_attr(elem, 'stroke-width', ctx), 1.0)
    stroke_opacity = get_stroke_opacity(elem, ctx)
    if stroke and stroke != 'none' and stroke_width > 0 and stroke_opacity != 0:
        return False

    return True


def _background_xml_from_rect(
    elem: ET.Element,
    ctx: ConvertContext,
) -> str:
    """Build native ``p:bg`` XML from a full-slide SVG background rect."""
    fill_xml = build_fill_xml(
        elem,
        ctx,
        get_fill_opacity(elem, ctx),
        usage="background",
    )
    if not fill_xml or '<a:noFill' in fill_xml:
        return ''
    return f'<p:bg><p:bgPr>{fill_xml}<a:effectLst/></p:bgPr></p:bg>'


def _extract_background_candidate(
    root: ET.Element,
    ctx: ConvertContext,
) -> tuple[str, int | None]:
    """Promote a first-layer SVG background rect to native PowerPoint bgPr.

    PowerPoint stores page background fills under ``p:cSld/p:bg/p:bgPr``.
    Keeping the full-canvas SVG rect in ``p:spTree`` makes it an ordinary
    selectable shape, so users hit it during bulk element selection. Only the
    first visual layer is considered, matching pptx_to_svg's round-trip output
    and avoiding accidental promotion of content panels.
    """
    canvas = _parse_svg_canvas(root)
    for child in root:
        tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if tag in _NON_VISUAL_TAGS:
            continue

        if tag == 'rect' and _is_full_canvas_rect(child, ctx, canvas):
            bg_xml = _background_xml_from_rect(child, ctx)
            if bg_xml:
                return bg_xml, id(child)
            return '', None

        if tag != 'g':
            return '', None
        if child.get('transform') or child.get('filter') or child.get('clip-path'):
            return '', None
        style_overrides = _extract_inheritable_styles(child)
        local_opacity = get_element_opacity(child)
        child_ctx = ctx.child(
            style_overrides=style_overrides,
            opacity_multiplier=1.0 if local_opacity is None else local_opacity,
        )
        visual_children = [
            grandchild for grandchild in child
            if grandchild.tag.replace(f'{{{SVG_NS}}}', '') not in _NON_VISUAL_TAGS
        ]
        if len(visual_children) != 1:
            return '', None
        only_child = visual_children[0]
        only_tag = only_child.tag.replace(f'{{{SVG_NS}}}', '')
        if only_tag == 'rect' and _is_full_canvas_rect(only_child, child_ctx, canvas):
            bg_xml = _background_xml_from_rect(only_child, child_ctx)
            if bg_xml:
                ctx.sync_from_child(child_ctx)
                return bg_xml, id(child)
            return '', None
        return '', None

    return '', None


def collect_defs(root: ET.Element) -> dict[str, ET.Element]:
    """Collect all <defs> children into an {id: element} dictionary."""
    definitions, _duplicates = project_definition_index(root)
    return definitions


def _build_source_shape_id_map(root: ET.Element) -> dict[tuple[str, str], int]:
    """Allocate page-unique ids for part-scoped imported shape identities."""
    source_entries: list[tuple[tuple[str, str], int]] = []
    seen_keys: set[tuple[str, str]] = set()
    for elem in root.iter():
        raw_id = elem.get('data-pptx-shape-id')
        if raw_id is None:
            continue
        scope = elem.get('data-pptx-shape-scope') or 'slide'
        if re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', scope) is None:
            raise SvgNativeConversionError(
                f'Invalid data-pptx-shape-scope {scope!r}'
            )
        try:
            shape_id = int(raw_id)
        except ValueError as exc:
            raise SvgNativeConversionError(
                f'Invalid data-pptx-shape-id {raw_id!r}'
            ) from exc
        if shape_id < 2 or shape_id > 0xFFFFFFFF:
            raise SvgNativeConversionError(
                f'data-pptx-shape-id must be between 2 and 4294967295, got {raw_id!r}'
            )
        key = (scope, raw_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        source_entries.append((key, shape_id))

    preferred_ids = {shape_id for _key, shape_id in source_entries}
    next_fresh = max(preferred_ids, default=1) + 1
    used: set[int] = set()
    mapping: dict[tuple[str, str], int] = {}
    for key, preferred in source_entries:
        output_id = preferred
        if output_id in used:
            while next_fresh in preferred_ids or next_fresh in used:
                next_fresh += 1
            if next_fresh > 0xFFFFFFFF:
                raise SvgNativeConversionError('Exhausted PowerPoint shape id range')
            output_id = next_fresh
            next_fresh += 1
        used.add(output_id)
        mapping[key] = output_id
    return mapping


def _geometry_trace_metadata(elem: ET.Element, result: ShapeResult) -> dict[str, Any]:
    """Describe the native geometry decision for conversion diagnostics."""
    xml = result.xml.lstrip()
    if xml.startswith('<p:grpSp>'):
        return {'output_geometry': 'group', 'fidelity': 'visual-only'}
    if xml.startswith('<p:pic>'):
        return {'output_geometry': 'picture', 'fidelity': 'native-normalized'}
    if xml.startswith('<p:graphicFrame>'):
        return {'output_geometry': 'native-object', 'fidelity': 'native-normalized'}

    preset_match = re.search(r'<a:prstGeom prst="([^"]+)"', xml)
    if preset_match is not None:
        preset = preset_match.group(1)
        source_preset = elem.get('data-pptx-prst')
        is_connector = xml.startswith('<p:cxnSp>')
        fidelity = (
            'exact'
            if source_preset == preset
            and elem.get('data-pptx-frame') is not None
            and not is_connector
            else 'native-normalized'
        )
        return {
            'output_geometry': 'preset',
            'preset': preset,
            'fidelity': fidelity,
        }
    if re.search(r'<a:custGeom(?:\s|>)', xml):
        carrier = next(
            (
                candidate
                for candidate in elem.iter()
                if candidate.get('data-pptx-part') == 'geometry'
            ),
            elem,
        )
        source_custom = (
            carrier.get('data-pptx-geometry-kind') == 'custom'
            and carrier.get('data-pptx-frame') is not None
        )
        expected_hash = carrier.get('data-pptx-geometry-sha256')
        actual_hash = hashlib.sha256(
            (carrier.get('d') or '').strip().encode('utf-8')
        ).hexdigest()
        unchanged = source_custom and expected_hash == actual_hash
        if unchanged:
            fidelity = 'exact'
            geometry_source = 'preserved-metadata'
        elif source_custom:
            fidelity = 'native-normalized'
            geometry_source = 'svg-recompiled'
        else:
            fidelity = 'visual-only'
            geometry_source = 'svg-authored'
        return {
            'output_geometry': 'custom',
            'fidelity': fidelity,
            'geometry_source': geometry_source,
        }
    return {'output_geometry': 'unknown', 'fidelity': 'visual-only'}


def convert_element(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Dispatch an SVG element to the appropriate converter."""
    tag = elem.tag.replace(f'{{{SVG_NS}}}', '')
    elem_id = elem.get('id')

    def trace(decision: str, **metadata: Any) -> None:
        if ctx.trace_events is None:
            return
        event: dict[str, Any] = {
            'tag': tag,
            'decision': decision,
        }
        if elem_id:
            event['id'] = elem_id
        for attr in (
            'data-pptx-layer',
            'data-pptx-object',
            'data-pptx-shape-id',
            'data-pptx-frame',
            'data-pptx-prst',
            'data-pptx-part',
            'data-pptx-geometry-status',
            'data-pptx-geometry-reason',
            'data-pptx-placeholder',
            'data-pptx-placeholder-bounds',
            'data-pptx-placeholder-carrier',
            'data-pptx-placeholder-idx',
            'data-pptx-role',
        ):
            value = elem.get(attr)
            if value is not None:
                event[attr] = value
        adjustments = {
            attr[len('data-pptx-av-'):]: value
            for attr, value in elem.attrib.items()
            if attr.startswith('data-pptx-av-')
        }
        if adjustments:
            event['adjustments'] = dict(sorted(adjustments.items()))
        event.update(metadata)
        ctx.trace_events.append(event)

    if elem.get('data-pptx-part') == 'geometry-detail':
        trace('skip', reason='render-only-preset-geometry-detail')
        return None

    converter = _CONVERTERS.get(tag)
    if converter:
        try:
            result = converter(elem, ctx)
        except Exception as e:
            trace('error', error=str(e))
            raise SvgNativeConversionError(f'Failed to convert <{tag}>: {e}') from e
        if result:
            shape_match = re.search(r'<p:cNvPr id="(\d+)"', result.xml)
            metadata: dict[str, Any] = {}
            if shape_match:
                metadata['shape_id'] = int(shape_match.group(1))
            if result.bounds_emu is not None:
                metadata['bounds_emu'] = list(result.bounds_emu)
            metadata.update(_geometry_trace_metadata(elem, result))
            trace('native', **metadata)
        else:
            trace('skip', reason='empty-or-non-rendering')
        return result

    if tag in _NON_VISUAL_TAGS:
        trace('skip', reason='non-visual')
        return None

    trace('unsupported')
    raise SvgNativeConversionError(f'Unsupported visual SVG element <{tag}>')


def _local_tag(elem: ET.Element) -> str:
    if not isinstance(elem.tag, str):
        return str(elem.tag)
    prefix = f'{{{SVG_NS}}}'
    return elem.tag[len(prefix):] if elem.tag.startswith(prefix) else elem.tag


def collect_unsupported_visuals(
    root: ET.Element,
    *,
    allow_data_icon_use: bool = False,
) -> list[str]:
    """Return visual element paths that the native converter cannot dispatch."""
    issues: list[str] = []

    def walk(
        elem: ET.Element,
        path: str,
        in_defs: bool = False,
        parent_tag: str | None = None,
    ) -> None:
        tag = _local_tag(elem)
        current = f'{path}/{tag}'
        if in_defs:
            return
        if tag in _NON_VISUAL_TAGS:
            return
        is_supported_visual_child = (
            tag in _SUPPORTED_VISUAL_CHILD_TAGS
            and parent_tag in {'text', 'tspan'}
        )
        is_data_icon_placeholder = (
            allow_data_icon_use
            and tag == 'use'
            and elem.get('data-icon') is not None
        )
        if (tag not in _CONVERTERS
                and tag not in _NON_VISUAL_TAGS
                and not is_supported_visual_child
                and not is_data_icon_placeholder):
            issues.append(current)
        for idx, child in enumerate(list(elem), start=1):
            walk(
                child,
                f'{current}[{idx}]',
                in_defs=(tag == 'defs'),
                parent_tag=tag,
            )

    for idx, child in enumerate(list(root), start=1):
        walk(child, f'/svg[{idx}]', parent_tag='svg')
    return issues


def convert_svg_to_slide_shapes(
    svg_path: str | Path,
    slide_num: int = 1,
    verbose: bool = False,
    merge_paragraphs: bool = True,
    image_optimize: bool = True,
    image_max_dimension: int | None = 2560,
    image_sizing: str = 'cap',
    image_scale: float = 2.0,
    image_quality: int = 85,
    native_objects: bool = False,
    animation_group_overrides: frozenset[str] | None = None,
    theme_font_spec: ThemeFontSpec | None = None,
    theme_color_spec: ThemeColorSpec | None = None,
    trace_out: list[dict[str, Any]] | None = None,
    promote_background: bool = True,
) -> tuple[
    str,
    dict[str, bytes],
    list[dict[str, str]],
    list,
    dict[str, bytes],
    dict[str, str],
]:
    """Convert an SVG file to a complete DrawingML slide XML.

    Args:
        svg_path: Path to the SVG file.
        slide_num: Slide number (for naming).
        verbose: Print progress info.
        merge_paragraphs: When True, mergeable paragraph blocks (same x,
            dy clustered around one base line-height) become a single
            editable text frame with multiple <a:p>. Disable it to preserve
            the SVG's exact line layout (one textbox per line).
        image_optimize: Downsample oversized raster images for PPTX export.
        image_max_dimension: Maximum optimized image dimension in pixels.
        image_sizing: ``cap`` to only cap source dimensions, ``display`` to
            size from rendered SVG boxes.
        image_scale: Target image pixels per SVG display pixel.
        image_quality: JPEG quality used for opaque optimized rasters.
        native_objects: Convert explicit ``data-pptx-replace-with`` chart/table
            markers to native PowerPoint Chart/Table objects. Default off.
        animation_group_overrides: Explicit top-level SVG group ids from
            ``animations.json`` that override the legacy chrome-name fallback.
            Explicit structural layer/role/placeholder markers remain excluded.
        theme_font_spec: Optional major/minor theme-font contract. Matching SVG
            families emit DrawingML theme tokens instead of fixed typefaces.
        theme_color_spec: Optional context-aware theme-color contract. Exact
            locked colors emit DrawingML scheme tokens while local colors stay
            fixed.
        trace_out: Optional list populated with one per-slide trace dictionary.
        promote_background: Promote the first eligible full-canvas rectangle
            into native ``p:bg``. Structured export disables this generic pass
            and applies its narrower explicit background contract later.

    Returns:
        (slide_xml, media_files, rel_entries, anim_targets,
        package_files, content_type_overrides) where:
        - slide_xml: Complete slide XML string.
        - media_files: Dict of {filename: bytes} for media to write.
        - rel_entries: List of relationship entries to add.
        - anim_targets: List of (shape_id, svg_id) tuples for top-level
          semantic groups, in z-order; consumed by the builder's optional
          per-element entrance timing emitter.
        - package_files: Dict of {pptx internal path: bytes} for non-media
          OOXML parts such as native chart XML and embedded workbooks.
        - content_type_overrides: Dict of {pptx internal path: content type}
          for package_files that require [Content_Types].xml overrides.
    """
    svg_path = Path(svg_path)
    tree = ET.parse(str(svg_path))
    root = tree.getroot()
    try:
        parse_project_svg_root(
            root,
            context=svg_path.name,
        )
    except CanvasContractError as exc:
        raise SvgNativeConversionError(str(exc)) from exc
    _require_chart_table_marker_attributes(root, svg_path)
    _require_project_nested_svg_crops(root, svg_path)
    _require_project_clip_paths(root, svg_path)
    authored_errors = validate_authored_preset_tree(root)
    if authored_errors:
        raise SvgNativeConversionError(
            'Invalid authored preset structure: ' + '; '.join(authored_errors)
        )
    # Validate the source contract once, then lower compact groups to the
    # established expanded transport IR.  Downstream conversion validates the
    # generated preview hash, not the source-format allowlist again.
    try:
        materialize_compact_authored_preset_tree(root)
    except ValueError as exc:
        raise SvgNativeConversionError(
            f'Invalid compact authored preset: {exc}'
        ) from exc
    _mark_unchanged_txbody_groups(root)
    _mark_unchanged_preset_previews(root)
    if native_objects:
        try:
            snapshot_native_fallback_freshness(root)
        except NativeMarkerAttributeError as exc:
            raise SvgNativeConversionError(
                f'{Path(svg_path).name}: conflicting chart/table replacement '
                f'metadata: {exc}'
            ) from exc
    trace_events: list[dict[str, Any]] | None = [] if trace_out is not None else None
    trace_steps: list[dict[str, Any]] = []

    from ..geometry_properties import (
        GeometryStyleError,
        materialize_inline_geometry_properties,
    )

    try:
        geometry_count = materialize_inline_geometry_properties(root)
    except GeometryStyleError as exc:
        raise SvgNativeConversionError(
            f'{svg_path.name}: inline geometry materialization failed: {exc}'
        ) from exc
    geometry_trace = None
    if geometry_count:
        geometry_trace = {
            'action': 'materialize-inline-geometry',
            'count': geometry_count,
        }
        trace_steps.append(geometry_trace)
        if verbose:
            print(f'  Materialized {geometry_count} inline geometry declaration(s)')

    geometry_length_errors = project_geometry_length_errors(root)
    if geometry_length_errors:
        preview = '; '.join(geometry_length_errors[:8])
        suffix = (
            '' if len(geometry_length_errors) <= 8
            else f'; +{len(geometry_length_errors) - 8} more'
        )
        raise SvgNativeConversionError(
            f'{Path(svg_path).name}: invalid project geometry length(s): '
            f'{preview}{suffix}'
        )

    _require_project_text_properties(root, svg_path)
    _require_project_freeform_geometry(root, svg_path)
    _require_project_stroke_styles(root, svg_path)
    _require_project_opacities(root, svg_path)
    _require_project_paints(root, svg_path)
    _require_project_definitions(root, svg_path)
    _require_project_paint_references(root, svg_path)
    _require_project_line_end_markers(root, svg_path)
    _require_project_gradients(root, svg_path)
    _require_project_effect_status(root, svg_path)
    _require_project_filters(root, svg_path)
    _require_project_image_aspect_ratios(root, svg_path)
    _require_project_transforms(root, svg_path)

    viewport_width, viewport_height = _root_viewport_size(root)

    # Expand project icon placeholders and static same-document <use>
    # references before unsupported-element preflight.
    from ..use_expander import (
        UseExpansionError,
        expand_local_use_references,
        expand_use_data_icons,
    )

    icons_dir, icons_fallback_dir = icon_search_dirs_for_svg(svg_path)
    if icons_dir.exists():
        expanded = expand_use_data_icons(root, icons_dir, icons_fallback_dir)
        if expanded:
            trace_steps.append({'action': 'expand-use-data-icons', 'count': expanded})
        if verbose and expanded:
            print(f'  Expanded {expanded} <use data-icon="..."/> placeholder(s)')
        if expanded:
            _require_project_freeform_geometry(root, svg_path)

    try:
        injected_geometry_count = materialize_inline_geometry_properties(root)
    except GeometryStyleError as exc:
        raise SvgNativeConversionError(
            f'{svg_path.name}: expanded icon geometry materialization failed: {exc}'
        ) from exc
    if injected_geometry_count:
        geometry_count += injected_geometry_count
        if geometry_trace is None:
            geometry_trace = {
                'action': 'materialize-inline-geometry',
                'count': geometry_count,
            }
            trace_steps.append(geometry_trace)
        else:
            geometry_trace['count'] = geometry_count
        if verbose:
            print(
                f'  Materialized {injected_geometry_count} inline geometry '
                'declaration(s) from expanded icons'
            )

    try:
        expanded_local = expand_local_use_references(root)
    except UseExpansionError as exc:
        raise SvgNativeConversionError(
            f'{svg_path.name}: local <use> expansion failed: {exc}'
        ) from exc
    if expanded_local:
        trace_steps.append({
            'action': 'expand-local-use-references',
            'count': expanded_local,
        })
        if verbose:
            print(f'  Expanded {expanded_local} local <use href="#..."/> instance(s)')

    # Recheck compiler-injected icon/use wrappers and cloned definition trees.
    _require_project_nested_svg_crops(root, svg_path)
    _require_project_images(root, svg_path)
    _require_project_clip_paths(root, svg_path)
    _require_project_text_properties(root, svg_path)
    _require_project_stroke_styles(root, svg_path)
    _require_project_opacities(root, svg_path)
    _require_project_paints(root, svg_path)
    _require_project_definitions(root, svg_path)
    _require_project_paint_references(root, svg_path)
    _require_project_gradients(root, svg_path)
    _require_project_effect_status(root, svg_path)
    _require_project_filters(root, svg_path)
    _require_project_image_aspect_ratios(root, svg_path)
    _require_project_transforms(root, svg_path)

    try:
        materialize_project_text_metrics(root)
    except ValueError as exc:
        raise SvgNativeConversionError(
            f'{svg_path.name}: text-metric materialization failed: {exc}'
        ) from exc

    # Flatten positional <tspan> (those with x/y/non-zero dy) into independent
    # <text> elements. DrawingML runs cannot reposition mid-paragraph, so a
    # dy-stacked block of tspans would otherwise collapse onto one baseline,
    # and an x-anchored tspan would render in the wrong column. finalize_svg
    # does the same flattening on disk; doing it here keeps native pptx output
    # correct when reading raw svg_output/.
    # merge_paragraphs additionally folds mergeable paragraph blocks into a
    # single annotated <text> for downstream multi-<a:p> conversion.
    from ..tspan_flattener import flatten_positional_tspans
    flattened = flatten_positional_tspans(tree, merge_paragraphs=merge_paragraphs)
    if flattened:
        trace_steps.append({
            'action': 'flatten-positional-tspans',
            'merge_paragraphs': merge_paragraphs,
        })
        if verbose:
            print('  Flattened positional <tspan> into independent <text>')

    _require_project_text_properties(root, svg_path)
    try:
        text_font_sizes = resolve_project_font_sizes(root)
        text_letter_spacings = resolve_project_letter_spacings(
            root,
            text_font_sizes,
        )
    except ValueError as exc:
        raise SvgNativeConversionError(
            f'{svg_path.name}: invalid project text-metric inheritance: {exc}'
        ) from exc

    unsupported = collect_unsupported_visuals(root)
    if unsupported:
        preview = '; '.join(unsupported[:8])
        suffix = '' if len(unsupported) <= 8 else f'; +{len(unsupported) - 8} more'
        raise SvgNativeConversionError(
            f'{svg_path.name}: unsupported visual SVG element(s): {preview}{suffix}'
        )

    defs = collect_defs(root)
    source_shape_id_map = _build_source_shape_id_map(root)
    ctx = ConvertContext(
        defs=defs,
        reserved_shape_ids=frozenset(source_shape_id_map.values()),
        source_shape_id_map=source_shape_id_map,
        slide_num=slide_num,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        svg_dir=Path(svg_path).parent,
        merge_paragraphs=merge_paragraphs,
        image_optimize=image_optimize,
        image_max_dimension=image_max_dimension,
        image_sizing=image_sizing,
        image_scale=image_scale,
        image_quality=image_quality,
        native_objects_enabled=native_objects,
        animation_group_overrides=animation_group_overrides or frozenset(),
        trace_events=trace_events,
        theme_font_spec=theme_font_spec,
        theme_color_spec=theme_color_spec,
        inherited_styles=_extract_inheritable_styles(root),
        text_font_sizes=text_font_sizes,
        text_letter_spacings=text_letter_spacings,
    )

    shapes: list[str] = []
    converted = 0
    skipped = 0
    has_top_level_group = any(
        child.tag.replace(f'{{{SVG_NS}}}', '') == 'g'
        for child in root
    )
    background_xml, background_skip_id = (
        _extract_background_candidate(root, ctx)
        if promote_background
        else ('', None)
    )
    promoted_backgrounds = 1 if background_xml else 0
    if background_xml and trace_events is not None:
        trace_events.append({
            'tag': 'rect',
            'decision': 'native-background',
            'reason': 'promoted-full-canvas-rect-to-bgPr',
        })
    # Per-element shape ids of every top-level child, used as an animation
    # fallback when no <g id="..."> groups are present at the root.
    fallback_targets: list = []

    for child in root:
        tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if tag == 'defs':
            continue
        if id(child) == background_skip_id:
            continue
        result = convert_element(child, ctx)
        if result:
            shapes.append(result.xml)
            converted += 1
            m = re.search(r'<p:cNvPr id="(\d+)"', result.xml)
            elem_id = child.get('id')
            role = child.get('data-pptx-role')
            placeholder = child.get('data-pptx-placeholder')
            has_explicit_semantics = role is not None or placeholder is not None
            structurally_static = (
                child.get('data-pptx-layer') is not None
                or (
                    has_explicit_semantics
                    and is_static_page_frame(role, placeholder)
                )
            )
            legacy_chrome = (
                not has_explicit_semantics
                and is_chrome_id(elem_id)
            )
            explicit_legacy_override = (
                elem_id is not None
                and elem_id in ctx.animation_group_overrides
            )
            if (
                m
                and not structurally_static
                and (not legacy_chrome or explicit_legacy_override)
            ):
                fallback_targets.append((int(m.group(1)), elem_id or tag))
        else:
            if tag not in _NON_VISUAL_TAGS:
                skipped += 1

    unresolved_connector_targets = sorted(
        ctx.referenced_shape_ids - ctx.claimed_shape_ids
    )
    if unresolved_connector_targets:
        raise SvgNativeConversionError(
            'Connector target shape ids were reserved but not restored: '
            + ', '.join(str(shape_id) for shape_id in unresolved_connector_targets)
        )

    # Animation target fallback. Semantic <g id="..."> groups are the
    # preferred anchors (set inside convert_g). When the SVG has none
    # at the root we fall back to top-level primitives, but only when
    # the count is reasonable. Presenter-click animation should reveal
    # semantic blocks, not atomized drawing primitives, so fallback is
    # intentionally capped at a low count.
    _ANIM_FALLBACK_CAP = 8
    if (
        not has_top_level_group
        and not ctx.anim_targets
        and 0 < len(fallback_targets) <= _ANIM_FALLBACK_CAP
    ):
        ctx.anim_targets = fallback_targets

    if verbose:
        promoted = (
            f', promoted {promoted_backgrounds} background'
            if promoted_backgrounds else ''
        )
        print(f'  Converted {converted} elements, skipped {skipped}{promoted}')

    if trace_out is not None:
        trace_out.append({
            'slide_num': slide_num,
            'svg': str(svg_path),
            'page_role': root.get('data-pptx-page-role'),
            'summary': {
                'converted': converted,
                'skipped': skipped,
                'promoted_backgrounds': promoted_backgrounds,
                'media_files': len(ctx.media_files),
                'package_files': len(ctx.package_files),
                'relationships': len(ctx.rel_entries),
                'animation_targets': len(ctx.anim_targets),
            },
            'preprocess': trace_steps,
            'events': trace_events or [],
        })

    shapes_xml = '\n'.join(shapes)

    slide_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld>
{background_xml}
<p:spTree>
<p:nvGrpSpPr>
<p:cNvPr id="1" name=""/>
<p:cNvGrpSpPr/><p:nvPr/>
</p:nvGrpSpPr>
<p:grpSpPr>
<a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>
<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>
</p:grpSpPr>
{shapes_xml}
</p:spTree>
</p:cSld>
<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''

    return (
        slide_xml,
        ctx.media_files,
        ctx.rel_entries,
        ctx.anim_targets,
        ctx.package_files,
        ctx.content_type_overrides,
    )
