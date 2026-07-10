"""Core SVG -> DrawingML dispatcher, group handling, and main entry point."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from resource_paths import icon_search_dirs_for_svg

from .context import ConvertContext, ShapeResult
from .theme_colors import ThemeColorSpec
from .theme_fonts import ThemeFontSpec
from .utils import (
    SVG_NS, EMU_PER_PX,
    _extract_inheritable_styles, _f, _get_attr, parse_transform_matrix, resolve_url_id,
    parse_svg_length,
)
from .styles import (
    build_effect_xml, build_fill_xml, get_fill_opacity, get_stroke_opacity,
)
from .elements import (
    convert_rect, convert_circle, convert_ellipse,
    convert_line, convert_path,
    convert_polygon, convert_polyline,
    convert_text, convert_image, convert_nested_svg,
)
from ..animation_config import is_chrome_id
from ..native_objects import convert_native_object, native_marker_transform
from ..semantic_markers import is_static_page_frame


class SvgNativeConversionError(RuntimeError):
    """Raised when an SVG cannot be faithfully converted to native DrawingML."""


# ---------------------------------------------------------------------------
# Transform & layout helpers
# ---------------------------------------------------------------------------

def parse_transform(transform_str: str) -> tuple[float, float, float, float, float]:
    """Parse an SVG transform list into (dx, dy, sx, sy, angle_deg).

    Composes every translate/scale/rotate/matrix operation rather than picking
    the first occurrence — needed for idioms like
    ``translate(cx cy) scale(-1 -1) translate(-cx -cy)`` which encode a flip
    around a non-origin pivot.

    When the composed matrix has no shear and no rotation, the decomposition is
    exact (sx/sy may be negative to represent flips). When rotation is present
    without shear, sx/sy default to the column magnitudes and angle_deg is the
    rotation. Shear is not representable in this 5-tuple and silently
    collapses; callers that need exact fidelity should consume the full matrix
    via ``parse_transform_matrix``.
    """
    if not transform_str:
        return 0.0, 0.0, 1.0, 1.0, 0.0

    a, b, c, d, e, f = parse_transform_matrix(transform_str)

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
_ROTATE_RE = re.compile(
    r'rotate\(\s*([-\d.eE+]+)(?:[\s,]+([-\d.eE+]+)[\s,]+([-\d.eE+]+))?\s*\)'
)


def _root_viewport_size(root: ET.Element) -> tuple[float, float]:
    """Return the SVG root viewport size in user units."""
    view_box = root.get('viewBox')
    if view_box:
        raw_parts = re.split(r'[\s,]+', view_box.strip())
        if len(raw_parts) == 4:
            try:
                parts = [float(n) for n in raw_parts]
            except ValueError:
                parts = []
            if parts and parts[2] > 0 and parts[3] > 0:
                return parts[2], parts[3]

    width = parse_svg_length(root.get('width'), 1280.0)
    height = parse_svg_length(root.get('height'), 720.0)
    return max(width, 1.0), max(height, 1.0)


def _extract_rotate_pivot(transform_str: str) -> tuple[float, float] | None:
    """Return the (cx, cy) pivot of a sole ``rotate(...)`` in *transform_str*.

    Returns ``None`` when the transform list contains anything other than one
    rotate (other ops compose with rotate in a way the pivot-compensation
    fallback can't express). A bare ``rotate(angle)`` returns (0, 0).
    """
    if not transform_str:
        return None
    ops = [op for op in re.findall(r'(\w+)\s*\(', transform_str) if op]
    if ops != ['rotate']:
        return None
    match = _ROTATE_RE.search(transform_str)
    if not match:
        return None
    cx = float(match.group(2)) if match.group(2) is not None else 0.0
    cy = float(match.group(3)) if match.group(3) is not None else 0.0
    return cx, cy


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
        descendant.get('data-pptx-native')
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

    elem_id = elem.get('id')
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
        and not is_chrome
        and not elem.get('data-pptx-layer')
    )
    visual_children = [
        child for child in elem
        if child.tag.replace(f'{{{SVG_NS}}}', '') not in _NON_VISUAL_TAGS
    ]
    matrix_supported = not native_subtree_active and bool(transform) and visual_children and all(
        _supports_matrix_transform(child) for child in visual_children
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
        )
    elif rotate_pivot is not None:
        child_ctx = ctx.child(
            0, 0, 1.0, 1.0,
            filter_id=filter_id,
            style_overrides=style_overrides,
        )
    else:
        child_ctx = ctx.child(
            ctx.scale_x * dx if native_subtree_active else dx,
            ctx.scale_y * dy if native_subtree_active else dy,
            sx,
            sy,
            filter_id=filter_id,
            style_overrides=style_overrides,
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

    child_results: list[ShapeResult] = []
    for child in elem:
        result = convert_element(child, child_ctx)
        if result:
            child_results.append(result)

    ctx.sync_from_child(child_ctx)

    if not child_results:
        return None

    # Single-child non-semantic groups are flattened to reduce nesting. Top-level
    # semantic groups are preserved so animations target the group, not its
    # individual child shapes.
    if len(child_results) == 1 and not should_animate_group:
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
    group_id = ctx.next_id()

    # Record top-level semantic groups (e.g. <g id="p02-title">) so the
    # PPTX builder can emit per-element entrance timing. Only the outermost
    # multi-child wrapper qualifies — flattened single-child groups have no
    # <p:grpSp> to anchor a timing target on, and nested groups are
    # ignored to keep the animation budget at ~per-section granularity.
    if should_animate_group:
        ctx.anim_targets.append((group_id, elem_id))

    group_effect = ''
    if filter_id and filter_id in ctx.defs:
        group_effect = build_effect_xml(ctx.defs[filter_id])

    rot_emu = 0 if matrix_supported else int(angle_deg * 60000)
    rot_attr = f' rot="{rot_emu}"' if rot_emu else ''

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


def _supports_matrix_transform(elem: ET.Element) -> bool:
    """Return whether this subtree can consume a full affine matrix directly."""
    tag = elem.tag.replace(f'{{{SVG_NS}}}', '')
    if tag in {'rect', 'circle', 'ellipse', 'line', 'path', 'polygon', 'polyline', 'image'}:
        return True
    if tag == 'svg':
        visual_children = [
            child for child in elem
            if child.tag.replace(f'{{{SVG_NS}}}', '') not in _NON_VISUAL_TAGS
        ]
        return len(visual_children) == 1 and (
            visual_children[0].tag.replace(f'{{{SVG_NS}}}', '') == 'image'
        )
    if tag == 'g':
        visual_children = [
            child for child in elem
            if child.tag.replace(f'{{{SVG_NS}}}', '') not in _NON_VISUAL_TAGS
        ]
        return bool(visual_children) and all(
            _supports_matrix_transform(child) for child in visual_children
        )
    return False

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
    view_box = root.get('viewBox', '')
    parts = re.split(r'[\s,]+', view_box.strip()) if view_box else []
    if len(parts) == 4:
        try:
            x, y, w, h = (float(part) for part in parts)
            if w > 0 and h > 0:
                return x, y, w, h
        except ValueError:
            pass
    return 0.0, 0.0, _f(root.get('width')), _f(root.get('height'))


def _is_full_canvas_rect(
    elem: ET.Element,
    ctx: ConvertContext,
    canvas: tuple[float, float, float, float],
) -> bool:
    """Return whether a rect is a safe candidate for native slide background."""
    if elem.get('transform') or elem.get('filter') or elem.get('clip-path'):
        return False
    if _f(elem.get('rx')) > 0 or _f(elem.get('ry')) > 0:
        return False

    canvas_x, canvas_y, canvas_w, canvas_h = canvas
    if canvas_w <= 0 or canvas_h <= 0:
        return False

    tolerance = 0.5
    if abs(_f(elem.get('x')) - canvas_x) > tolerance:
        return False
    if abs(_f(elem.get('y')) - canvas_y) > tolerance:
        return False
    if abs(_f(elem.get('width')) - canvas_w) > tolerance:
        return False
    if abs(_f(elem.get('height')) - canvas_h) > tolerance:
        return False

    fill = _get_attr(elem, 'fill', ctx)
    if fill == 'none':
        return False

    stroke = _get_attr(elem, 'stroke', ctx)
    stroke_width = _f(_get_attr(elem, 'stroke-width', ctx), 1.0)
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
        child_ctx = ctx.child(style_overrides=style_overrides)
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
    defs: dict[str, ET.Element] = {}
    for defs_elem in root.iter(f'{{{SVG_NS}}}defs'):
        for child in defs_elem:
            elem_id = child.get('id')
            if elem_id:
                defs[elem_id] = child
    # Also check for defs without namespace
    for defs_elem in root.iter('defs'):
        for child in defs_elem:
            elem_id = child.get('id')
            if elem_id:
                defs[elem_id] = child
    return defs


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
            'data-pptx-placeholder',
            'data-pptx-placeholder-bounds',
            'data-pptx-placeholder-idx',
            'data-pptx-role',
        ):
            value = elem.get(attr)
            if value is not None:
                event[attr] = value
        event.update(metadata)
        ctx.trace_events.append(event)

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
    return elem.tag.split('}', 1)[-1] if isinstance(elem.tag, str) and '}' in elem.tag else str(elem.tag)


def _collect_unsupported_visuals(root: ET.Element) -> list[str]:
    issues: list[str] = []

    def walk(elem: ET.Element, path: str, in_defs: bool = False) -> None:
        tag = _local_tag(elem)
        current = f'{path}/{tag}'
        if in_defs:
            return
        if tag in _NON_VISUAL_TAGS:
            return
        if (tag not in _CONVERTERS
                and tag not in _NON_VISUAL_TAGS
                and tag not in _SUPPORTED_VISUAL_CHILD_TAGS):
            issues.append(current)
        for idx, child in enumerate(list(elem), start=1):
            walk(child, f'{current}[{idx}]', in_defs=(tag == 'defs'))

    for idx, child in enumerate(list(root), start=1):
        walk(child, f'/svg[{idx}]')
    return issues


def convert_svg_to_slide_shapes(
    svg_path: Path,
    slide_num: int = 1,
    verbose: bool = False,
    merge_paragraphs: bool = True,
    image_optimize: bool = True,
    image_max_dimension: int | None = 2560,
    image_sizing: str = 'cap',
    image_scale: float = 2.0,
    image_quality: int = 85,
    native_objects: bool = False,
    theme_font_spec: ThemeFontSpec | None = None,
    theme_color_spec: ThemeColorSpec | None = None,
    trace_out: list[dict[str, Any]] | None = None,
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
        native_objects: Convert explicit ``data-pptx-native`` table/chart
            markers to native PowerPoint objects. Default off.
        theme_font_spec: Optional major/minor theme-font contract. Matching SVG
            families emit DrawingML theme tokens instead of fixed typefaces.
        theme_color_spec: Optional context-aware theme-color contract. Exact
            locked colors emit DrawingML scheme tokens while local colors stay
            fixed.
        trace_out: Optional list populated with one per-slide trace dictionary.

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
    tree = ET.parse(str(svg_path))
    root = tree.getroot()
    viewport_width, viewport_height = _root_viewport_size(root)
    trace_events: list[dict[str, Any]] | None = [] if trace_out is not None else None
    trace_steps: list[dict[str, Any]] = []

    # Expand <use data-icon="..."/> placeholders in-memory so this dispatcher
    # can consume svg_output/ directly. Standard renderers and this converter
    # both ignore data-icon, so without expansion icons would silently drop.
    # The on-disk finalize_svg pipeline does the same expansion for svg_final/;
    # running this here makes the two pipelines behaviourally aligned.
    icons_dir, icons_fallback_dir = icon_search_dirs_for_svg(svg_path)
    if icons_dir.exists():
        from ..use_expander import expand_use_data_icons
        expanded = expand_use_data_icons(root, icons_dir, icons_fallback_dir)
        if expanded:
            trace_steps.append({'action': 'expand-use-data-icons', 'count': expanded})
        if verbose and expanded:
            print(f'  Expanded {expanded} <use data-icon="..."/> placeholder(s)')

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

    unsupported = _collect_unsupported_visuals(root)
    if unsupported:
        preview = '; '.join(unsupported[:8])
        suffix = '' if len(unsupported) <= 8 else f'; +{len(unsupported) - 8} more'
        raise SvgNativeConversionError(
            f'{svg_path.name}: unsupported visual SVG element(s): {preview}{suffix}'
        )

    defs = collect_defs(root)
    ctx = ConvertContext(
        defs=defs,
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
        trace_events=trace_events,
        theme_font_spec=theme_font_spec,
        theme_color_spec=theme_color_spec,
    )

    shapes: list[str] = []
    converted = 0
    skipped = 0
    background_xml, background_skip_id = _extract_background_candidate(root, ctx)
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
            if m and not child.get('data-pptx-layer'):
                if not is_static_page_frame(
                    child.get('data-pptx-role'),
                    child.get('data-pptx-placeholder'),
                ):
                    fallback_targets.append((int(m.group(1)), tag))
        else:
            if tag not in _NON_VISUAL_TAGS:
                skipped += 1

    # Animation target fallback. Semantic <g id="..."> groups are the
    # preferred anchors (set inside convert_g). When the SVG has none
    # at the root we fall back to top-level primitives, but only when
    # the count is reasonable. Presenter-click animation should reveal
    # semantic blocks, not atomized drawing primitives, so fallback is
    # intentionally capped at a low count.
    _ANIM_FALLBACK_CAP = 8
    if not ctx.anim_targets and 0 < len(fallback_targets) <= _ANIM_FALLBACK_CAP:
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
