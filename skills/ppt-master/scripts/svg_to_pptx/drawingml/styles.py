"""Fill, stroke, and shadow XML builders for DrawingML conversion."""

from __future__ import annotations

import math
from xml.etree import ElementTree as ET

from pptx_shapes import validate_ooxml_line_width

from .context import ConvertContext
from .theme_colors import ThemeColorSpec, color_node_xml
from .utils import (
    SVG_NS, ANGLE_UNIT,
    px_to_emu, _f, _get_attr, parse_svg_length,
    combine_opacity, parse_inline_style, parse_opacity, parse_stop_style,
    classify_project_marker_shape,
    matrix_multiply, parse_svg_color, parse_transform_matrix, resolve_url_id,
    parse_project_filter_params, project_filter_drawingml_coordinates,
    parse_project_gradient_ratio,
    parse_project_stroke_dasharray, parse_project_stroke_enum,
    quantize_ooxml_alpha, quantize_ooxml_unit_ratio,
)


def build_solid_fill(
    color: str,
    opacity: float | None = None,
    theme_color_spec: ThemeColorSpec | None = None,
    usage: str = "fill",
) -> str:
    """Build <a:solidFill> XML."""
    alpha = ''
    if opacity is not None and opacity < 1.0:
        alpha = f'<a:alpha val="{quantize_ooxml_alpha(opacity)}"/>'
    return (
        '<a:solidFill>'
        f'{color_node_xml(color, theme_color_spec, usage, alpha)}'
        '</a:solidFill>'
    )


def build_gradient_fill(
    grad_elem: ET.Element,
    opacity: float | None = None,
    theme_color_spec: ThemeColorSpec | None = None,
    usage: str = "fill",
) -> str:
    """Build <a:gradFill> from SVG linearGradient or radialGradient element."""
    tag = grad_elem.tag.replace(f'{{{SVG_NS}}}', '')

    stops_xml = []
    for child in grad_elem:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag != 'stop':
            continue

        offset_str = child.get('offset')
        if offset_str is None:
            raise ValueError('Gradient stop requires an explicit offset')
        offset = parse_project_gradient_ratio(offset_str)
        pos = quantize_ooxml_unit_ratio(offset)

        # Parse color from style attribute or direct attributes
        style = child.get('style', '')
        style_values = parse_inline_style(style)
        color, stop_opacity = parse_stop_style(style)
        if not color:
            color, color_alpha = parse_svg_color(child.get('stop-color', '#000000'))
            stop_opacity *= color_alpha
        if color is None:
            color = '000000'

        direct_stop_op = child.get('stop-opacity')
        if direct_stop_op is not None and 'stop-opacity' not in style_values:
            stop_opacity *= parse_opacity(
                direct_stop_op,
                allow_percentage=True,
            )

        alpha_xml = ''
        effective_opacity = combine_opacity(stop_opacity, opacity)
        if effective_opacity is not None:
            alpha_xml = (
                f'<a:alpha val="{quantize_ooxml_alpha(effective_opacity)}"/>'
            )

        stops_xml.append(
            f'<a:gs pos="{pos}">'
            f'{color_node_xml(color, theme_color_spec, usage, alpha_xml)}'
            '</a:gs>'
        )

    if not stops_xml:
        return ''

    gs_list = '\n'.join(stops_xml)

    if tag == 'linearGradient':
        def parse_grad_coord(val_str: str, default: float = 0.0) -> float:
            val_str = val_str.strip()
            if val_str.endswith('%'):
                return float(val_str.rstrip('%')) / 100.0
            v = float(val_str)
            return v / 100.0 if v > 1.0 else v

        x1 = parse_grad_coord(grad_elem.get('x1', '0'))
        y1 = parse_grad_coord(grad_elem.get('y1', '0'))
        x2 = parse_grad_coord(grad_elem.get('x2', '1'))
        y2 = parse_grad_coord(grad_elem.get('y2', '1'))

        angle_rad = math.atan2(y2 - y1, x2 - x1)
        angle_deg = math.degrees(angle_rad)
        dml_angle = int((angle_deg % 360) * ANGLE_UNIT)

        return f'''<a:gradFill>
<a:gsLst>{gs_list}</a:gsLst>
<a:lin ang="{dml_angle}" scaled="1"/>
</a:gradFill>'''

    elif tag == 'radialGradient':
        return f'''<a:gradFill>
<a:gsLst>{gs_list}</a:gsLst>
<a:path path="circle">
<a:fillToRect l="50000" t="50000" r="50000" b="50000"/>
</a:path>
</a:gradFill>'''

    return ''


def build_fill_xml(
    elem: ET.Element,
    ctx: ConvertContext,
    opacity: float | None = None,
    usage: str = "fill",
) -> str:
    """Build fill XML for a shape element, with inherited style support."""
    fill = _get_attr(elem, 'fill', ctx)
    if fill is None:
        fill = '#000000'  # SVG default fill is black

    if fill.strip().lower() in ('none', 'transparent'):
        return '<a:noFill/>'

    ref_id = resolve_url_id(fill)
    if ref_id and ref_id in ctx.defs:
        ref_elem = ctx.defs[ref_id]
        ref_tag = ref_elem.tag.replace(f'{{{SVG_NS}}}', '')
        if ref_tag == 'pattern':
            patt_xml = build_pattern_fill(
                ref_elem,
                opacity,
                ctx.theme_color_spec,
                usage,
            )
            if patt_xml:
                return patt_xml
            return '<a:noFill/>'
        return build_gradient_fill(
            ref_elem,
            opacity,
            ctx.theme_color_spec,
            usage,
        )

    color, color_alpha = parse_svg_color(fill)
    if color:
        return build_solid_fill(
            color,
            combine_opacity(opacity, color_alpha),
            ctx.theme_color_spec,
            usage,
        )

    return '<a:noFill/>'


def build_pattern_fill(
    pattern_elem: ET.Element,
    opacity: float | None = None,
    theme_color_spec: ThemeColorSpec | None = None,
    usage: str = "fill",
) -> str:
    """Build <a:pattFill> from an SVG <pattern> emitted by pptx_to_svg.

    Reads the round-trip annotations (data-pptx-pattern / data-pptx-fg /
    data-pptx-bg) when present. Falls back to inspecting the inner stroke /
    rect colors when annotations are absent (hand-authored SVG).
    """
    prst = pattern_elem.get('data-pptx-pattern') or 'ltUpDiag'

    paint_entries = []
    for child in pattern_elem:
        tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        style_values = parse_inline_style(child.get('style'))
        object_opacity = parse_opacity(
            style_values.get('opacity') or child.get('opacity')
        )
        for paint_attr in ('fill', 'stroke'):
            paint = style_values.get(paint_attr) or child.get(paint_attr)
            paint_hex, paint_alpha = parse_svg_color(paint) if paint else (None, 1.0)
            if paint_hex is None:
                continue
            paint_opacity = parse_opacity(
                style_values.get(f'{paint_attr}-opacity')
                or child.get(f'{paint_attr}-opacity')
            )
            paint_entries.append({
                'attr': paint_attr,
                'alpha': paint_alpha,
                'color': paint,
                'hex': paint_hex,
                'opacity': object_opacity * paint_opacity,
                'tag': tag,
            })

    fallback_bg = next((
        entry
        for entry in paint_entries
        if entry['tag'] == 'rect' and entry['attr'] == 'fill'
    ), None)
    fallback_fg = next((
        entry for entry in paint_entries if entry['attr'] == 'stroke'
    ), None)
    if fallback_fg is None:
        fallback_fg = next((
            entry
            for entry in paint_entries
            if entry['attr'] == 'fill' and entry is not fallback_bg
        ), None)

    fg_color = pattern_elem.get('data-pptx-fg')
    bg_color = pattern_elem.get('data-pptx-bg')
    fg_from_metadata = bool(fg_color)
    bg_from_metadata = bool(bg_color)
    if not fg_color and fallback_fg is not None:
        fg_color = fallback_fg['color']
    if not bg_color and fallback_bg is not None:
        bg_color = fallback_bg['color']

    fg_hex, fg_alpha = parse_svg_color(fg_color) if fg_color else (None, 1.0)
    bg_hex, bg_alpha = parse_svg_color(bg_color) if bg_color else (None, 1.0)
    if not fg_hex:
        return ''

    bg_source = next((
        entry
        for entry in paint_entries
        if entry['tag'] == 'rect'
        and entry['attr'] == 'fill'
        and entry['hex'] == bg_hex
    ), None)
    fg_source = next((
        entry
        for entry in paint_entries
        if entry['attr'] == 'stroke' and entry['hex'] == fg_hex
    ), None)
    if fg_source is None:
        fg_source = next((
            entry
            for entry in paint_entries
            if entry['attr'] == 'fill'
            and entry['hex'] == fg_hex
            and entry is not bg_source
        ), None)

    fg_child_opacity = 1.0
    if fg_source is not None:
        fg_child_opacity = fg_source['opacity'] * (
            fg_source['alpha'] if fg_from_metadata else 1.0
        )
    bg_child_opacity = 1.0
    if bg_source is not None:
        bg_child_opacity = bg_source['opacity'] * (
            bg_source['alpha'] if bg_from_metadata else 1.0
        )

    fg_opacity = combine_opacity(opacity, fg_alpha, fg_child_opacity)
    bg_opacity = combine_opacity(opacity, bg_alpha, bg_child_opacity)
    fg_alpha_xml = (
        f'<a:alpha val="{quantize_ooxml_alpha(fg_opacity)}"/>'
        if fg_opacity is not None else ''
    )
    bg_alpha_xml = (
        f'<a:alpha val="{quantize_ooxml_alpha(bg_opacity)}"/>'
        if bg_opacity is not None else ''
    )

    fg_xml = color_node_xml(fg_hex, theme_color_spec, usage, fg_alpha_xml)
    if bg_hex:
        bg_xml = color_node_xml(bg_hex, theme_color_spec, usage, bg_alpha_xml)
    else:
        bg_xml = color_node_xml('FFFFFF', theme_color_spec, usage, bg_alpha_xml)

    return (
        f'<a:pattFill prst="{prst}">'
        f'<a:fgClr>{fg_xml}</a:fgClr>'
        f'<a:bgClr>{bg_xml}</a:bgClr>'
        f'</a:pattFill>'
    )


# ---------------------------------------------------------------------------
# Marker (arrow-head) support
# ---------------------------------------------------------------------------

def _marker_size_buckets(w_attr: float, h_attr: float) -> tuple[str, str]:
    """Map SVG markerWidth / markerHeight to DrawingML (w, len) buckets.

    DrawingML arrow-end sizing is categorical: sm / med / lg.
    Width (perpendicular to the line) maps from markerHeight;
    length (along the line) maps from markerWidth.
    """

    def bucket(v: float) -> str:
        if v < 6:
            return 'sm'
        if v > 12:
            return 'lg'
        return 'med'

    return bucket(h_attr), bucket(w_attr)


def _classify_marker(marker_elem: ET.Element) -> tuple[str, str, str] | None:
    """Classify an SVG <marker> into a DrawingML line-end preset.

    Returns (type, w, len) where:
        type in {'triangle', 'stealth', 'diamond', 'oval', 'arrow'}
        w, len in {'sm', 'med', 'lg'}
    or None if the marker cannot be classified.

    Current coverage is the five DrawingML line-end shapes: triangle, stealth,
    arrow, diamond, and oval. Anything else returns ``None``.
    """
    mw = _f(marker_elem.get('markerWidth'), 3.0)
    mh = _f(marker_elem.get('markerHeight'), 3.0)
    w_bucket, len_bucket = _marker_size_buckets(mw, mh)

    marker_type = classify_project_marker_shape(marker_elem)
    if marker_type is None:
        return None
    return marker_type, w_bucket, len_bucket


def _emit_line_end(
    elem: ET.Element,
    ctx: ConvertContext,
    which: str,
) -> str:
    """Build <a:headEnd> or <a:tailEnd> XML for an element's marker reference.

    Args:
        which: 'head' (SVG marker-start) or 'tail' (SVG marker-end).

    Returns empty string if no marker, cannot resolve, or cannot classify.
    """
    attr = 'marker-start' if which == 'head' else 'marker-end'
    ref = _get_attr(elem, attr, ctx)
    if not ref or ref == 'none':
        return ''

    marker_id = resolve_url_id(ref)
    if not marker_id or marker_id not in ctx.defs:
        return ''

    marker_elem = ctx.defs[marker_id]
    tag = marker_elem.tag.replace(f'{{{SVG_NS}}}', '')
    if tag != 'marker':
        # ID collision with non-marker defs entry; ignore.
        return ''

    cls = _classify_marker(marker_elem)
    if cls is None:
        print(
            f'  Warning: marker "{marker_id}" shape cannot be classified; '
            'skipping (supported: triangle, stealth, arrow, diamond, oval)'
        )
        return ''

    typ, w_bucket, len_bucket = cls

    # Reclassify size buckets based on markerUnits semantics:
    #
    # markerUnits="strokeWidth" (SVG default):
    #   markerWidth IS a ratio to stroke-width, and DrawingML headEnd/tailEnd
    #   also scale proportionally with line width.  We should compare the ratio
    #   (markerWidth) directly against ratio-based thresholds — do NOT multiply
    #   by stroke-width, because that double-counts the scaling.
    #   Empirical DrawingML arrow ratios:
    #     sm  ≈ 1.5×  stroke-width  →  markerWidth ≤ 2.0
    #     med ≈ 2.5×  stroke-width  →  markerWidth  2.0 – 3.5
    #     lg  ≈ 3.5×  stroke-width  →  markerWidth ≥ 3.5
    #
    # markerUnits="userSpaceOnUse":
    #   markerWidth/Height are absolute pixel values – keep the existing
    #   absolute-pixel thresholds from _marker_size_buckets (6 / 12).
    marker_units = marker_elem.get('markerUnits', 'strokeWidth')
    if marker_units != 'userSpaceOnUse':
        mw = _f(marker_elem.get('markerWidth'), 3.0)
        mh = _f(marker_elem.get('markerHeight'), 3.0)

        def _ratio_bucket(v: float) -> str:
            if v <= 2.0:
                return 'sm'
            if v >= 3.5:
                return 'lg'
            return 'med'

        w_bucket = _ratio_bucket(mh)    # h → perpendicular width
        len_bucket = _ratio_bucket(mw)  # w → length along line

    dml_tag = 'headEnd' if which == 'head' else 'tailEnd'
    return f'<a:{dml_tag} type="{typ}" w="{w_bucket}" len="{len_bucket}"/>'


def _effective_stroke_scale(elem: ET.Element, ctx: ConvertContext) -> float:
    """Approximate the effective SVG geometry transform as one line-width scale."""
    vector_effect = _get_attr(elem, 'vector-effect', ctx)
    if vector_effect:
        vector_effect = parse_project_stroke_enum(
            'vector-effect',
            vector_effect,
        )
        if vector_effect == 'non-scaling-stroke':
            return 1.0

    if ctx.use_transform_matrix:
        matrix = ctx.transform_matrix
    else:
        matrix = (
            ctx.scale_x, 0.0,
            0.0, ctx.scale_y,
            ctx.translate_x, ctx.translate_y,
        )

    # The context already contains ancestor transforms. Shape converters apply
    # the leaf element's transform directly, so compose that local matrix once.
    transform = elem.get('transform')
    if transform:
        matrix = matrix_multiply(matrix, parse_transform_matrix(transform))

    # DrawingML has one line width. sqrt(|det|) equals the uniform scale for a
    # similarity transform and the principal-scale geometric mean otherwise.
    a, b, c, d, _e, _f = matrix
    return math.sqrt(abs(a * d - b * c))


def build_stroke_xml(
    elem: ET.Element,
    ctx: ConvertContext,
    opacity: float | None = None,
) -> str:
    """Build <a:ln> XML for stroke, with inherited style support."""
    stroke = _get_attr(elem, 'stroke', ctx)
    if not stroke or stroke.strip().lower() in ('none', 'transparent'):
        return '<a:ln><a:noFill/></a:ln>'

    source_width = parse_svg_length(_get_attr(elem, 'stroke-width', ctx), 1.0)
    width_emu = px_to_emu(source_width * _effective_stroke_scale(elem, ctx))
    validate_ooxml_line_width(width_emu)

    # Dash pattern
    dash_xml = ''
    dasharray = _get_attr(elem, 'stroke-dasharray', ctx)
    if dasharray:
        parsed_dasharray = parse_project_stroke_dasharray(dasharray)
        if parsed_dasharray is not None:
            preset, values = parsed_dasharray
            if preset:
                dash_xml = f'<a:prstDash val="{preset}"/>'
            else:
                # The project contract normalizes compatible longer arrays to
                # their first dash/gap pair before DrawingML quantization.
                d_raw, sp_raw = values[:2]
                sw = max(source_width, 0.001)
                d_pct = max(1, round(d_raw / sw * 100000))
                sp_pct = max(1, round(sp_raw / sw * 100000))
                dash_xml = (
                    '<a:custDash>'
                    f'<a:ds d="{d_pct}" sp="{sp_pct}"/>'
                    '</a:custDash>'
                )

    # Line cap
    cap_map = {'round': 'rnd', 'square': 'sq', 'butt': 'flat'}
    cap_attr = ''
    linecap = _get_attr(elem, 'stroke-linecap', ctx)
    if linecap:
        linecap = parse_project_stroke_enum('stroke-linecap', linecap)
        cap_attr = f' cap="{cap_map[linecap]}"'

    # Line join
    join_xml = ''
    linejoin = _get_attr(elem, 'stroke-linejoin', ctx)
    if linejoin:
        linejoin = parse_project_stroke_enum('stroke-linejoin', linejoin)
    if linejoin == 'round':
        join_xml = '<a:round/>'
    elif linejoin == 'bevel':
        join_xml = '<a:bevel/>'
    elif linejoin == 'miter':
        join_xml = '<a:miter lim="800000"/>'

    # Line-end markers (SVG marker-start / marker-end → <a:headEnd>/<a:tailEnd>)
    # DrawingML schema order is: fill → prstDash → join → headEnd → tailEnd,
    # so these must be appended after join_xml.
    head_end = _emit_line_end(elem, ctx, 'head')
    tail_end = _emit_line_end(elem, ctx, 'tail')
    line_ends = head_end + tail_end

    # Gradient stroke
    grad_id = resolve_url_id(stroke)
    if grad_id and grad_id in ctx.defs:
        grad_fill = build_gradient_fill(
            ctx.defs[grad_id],
            opacity,
            ctx.theme_color_spec,
            "stroke",
        )
        return f'<a:ln w="{width_emu}"{cap_attr}>{grad_fill}{dash_xml}{join_xml}{line_ends}</a:ln>'

    # Solid color stroke
    color, color_alpha = parse_svg_color(stroke)
    if not color:
        return '<a:ln><a:noFill/></a:ln>'

    opacity = combine_opacity(opacity, color_alpha)
    alpha_xml = ''
    if opacity is not None and opacity < 1.0:
        alpha_xml = f'<a:alpha val="{quantize_ooxml_alpha(opacity)}"/>'

    color_xml = color_node_xml(color, ctx.theme_color_spec, "stroke", alpha_xml)
    return f'''<a:ln w="{width_emu}"{cap_attr}>
<a:solidFill>{color_xml}</a:solidFill>{dash_xml}{join_xml}{line_ends}
</a:ln>'''


def _infer_shadow_alignment(dx: float, dy: float, threshold: float = 0.5) -> str:
    """Infer outer shadow alignment from the SVG offset vector.

    DrawingML applies alignment before blur/offset transforms, so we anchor the
    shadow opposite to the dominant offset direction:
    - diagonal offsets map to the opposite corner
    - pure vertical offsets stay centered, matching common PPT shadow presets
    - pure horizontal offsets anchor to the opposite side
    """
    if abs(dx) < threshold and abs(dy) < threshold:
        return 'ctr'
    if abs(dx) < threshold:
        return 'ctr'
    if abs(dy) < threshold:
        return 'l' if dx > 0 else 'r'
    if dx > 0 and dy > 0:
        return 'tl'
    if dx < 0 and dy > 0:
        return 'tr'
    if dx > 0 and dy < 0:
        return 'bl'
    return 'br'


def _shadow_dir_angle(dx: float, dy: float) -> int:
    """Convert an SVG offset vector to DrawingML clockwise angle units.

    OOXML angles are expressed in 60,000ths of a degree, with positive angles
    rotating clockwise toward the positive Y axis. SVG uses the same screen
    coordinate orientation (positive Y points downward), so the raw screen-space
    vector angle can be mapped directly with atan2(dy, dx).
    """
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        return 0
    angle_deg = math.degrees(math.atan2(dy, dx)) % 360
    return int(angle_deg * ANGLE_UNIT)


def build_shadow_xml(
    filter_elem: ET.Element,
    opacity: float | None = None,
) -> str:
    """Build <a:effectLst> with <a:outerShdw> from SVG filter element.

    SVG-to-DrawingML shadow mapping notes:
    - SVG feGaussianBlur stdDeviation (σ) maps to DrawingML blurRad using a
      2.0× scale. Rationale: σ is a standard deviation whose visual radius
      is ~3σ, while DrawingML blurRad is an outer-spread pixel distance.
      A 1.0× scale makes PowerPoint render sharp, concentrated shadows
      ("heavy" visual). 2.0× matches the CSS drop-shadow↔box-shadow
      convention and produces softer diffusion closer to the SVG preview.
    - The algn attribute is inferred from the offset direction so that
      the shadow aligns naturally with the shape edge.
    """
    if filter_elem is None:
        return ''

    p = parse_project_filter_params(filter_elem)
    dx = p['dx']
    dy = p['dy']
    # For shadow, default dy to 4 if no offset was found
    if not p['has_offset']:
        dy = 4.0
        p = {**p, 'dy': dy}

    coordinates = project_filter_drawingml_coordinates(p, 'shadow')
    blur_rad = coordinates['blurRad']
    dist = coordinates['dist']
    dir_angle = _shadow_dir_angle(dx, dy)
    # PowerPoint renders outerShdw alpha slightly heavier than SVG's filter
    # composite (different blending path). Scale by 0.75 to match the SVG
    # preview after blur has been corrected to 2.0× σ.
    opacity_multiplier = 1.0 if opacity is None else opacity
    alpha_val = quantize_ooxml_alpha(
        p['opacity'] * opacity_multiplier * 0.75
    )
    algn = _infer_shadow_alignment(dx, dy)

    return f'''<a:effectLst>
<a:outerShdw blurRad="{blur_rad}" dist="{dist}" dir="{dir_angle}" algn="{algn}" rotWithShape="0">
<a:srgbClr val="{p['color']}"><a:alpha val="{alpha_val}"/></a:srgbClr>
</a:outerShdw>
</a:effectLst>'''


def build_glow_xml(
    filter_elem: ET.Element,
    opacity: float | None = None,
) -> str:
    """Build <a:effectLst> with <a:glow> from SVG filter element.

    Used for filters that have feGaussianBlur without meaningful feOffset,
    typically title glow or highlight effects.
    """
    if filter_elem is None:
        return ''

    p = parse_project_filter_params(filter_elem)
    rad = project_filter_drawingml_coordinates(p, 'glow')['rad']
    opacity_multiplier = 1.0 if opacity is None else opacity
    alpha_val = quantize_ooxml_alpha(p['opacity'] * opacity_multiplier)

    return f'''<a:effectLst>
<a:glow rad="{rad}">
<a:srgbClr val="{p['color']}"><a:alpha val="{alpha_val}"/></a:srgbClr>
</a:glow>
</a:effectLst>'''


def classify_filter_effect(filter_elem: ET.Element) -> str | None:
    """Classify an SVG filter into a supported DrawingML effect kind."""
    if filter_elem is None:
        return None

    p = parse_project_filter_params(filter_elem)
    return 'shadow' if p['has_offset'] else 'glow'


def build_effect_xml(
    filter_elem: ET.Element,
    opacity: float | None = None,
) -> str:
    """Build effect XML by classifying the SVG filter as shadow or glow.

    Classification rules:
    - feOffset with non-zero dx/dy → outer shadow
    - No feOffset or zero offset → glow effect
    """
    if filter_elem is None:
        return ''

    effect_kind = classify_filter_effect(filter_elem)
    if effect_kind == 'shadow':
        return build_shadow_xml(filter_elem, opacity)
    if effect_kind == 'glow':
        return build_glow_xml(filter_elem, opacity)
    return ''


def get_element_opacity(
    elem: ET.Element,
    ctx: ConvertContext | None = None,
) -> float | None:
    """Get local opacity multiplied by any approximated ancestor group alpha."""
    base = ctx.opacity_multiplier if ctx is not None else 1.0
    if ctx is not None:
        op = _get_attr(elem, 'opacity', ctx)
    else:
        op = parse_inline_style(elem.get('style')).get('opacity') or elem.get('opacity')
    if op is None:
        return base if base < 1.0 else None
    val = base * parse_opacity(op)
    return val if val < 1.0 else None


def get_fill_opacity(
    elem: ET.Element,
    ctx: ConvertContext | None = None,
) -> float | None:
    """Get effective fill opacity combining 'opacity' and 'fill-opacity'.

    Returns:
        Combined opacity value, or None if fully opaque.
    """
    base = ctx.opacity_multiplier if ctx is not None else 1.0

    op = _get_attr(elem, 'opacity', ctx) if ctx else elem.get('opacity')
    if op is not None:
        base *= parse_opacity(op)

    fill_op = _get_attr(elem, 'fill-opacity', ctx) if ctx else elem.get('fill-opacity')
    if fill_op is not None:
        base *= parse_opacity(fill_op)

    return base if base < 1.0 else None


def get_stroke_opacity(
    elem: ET.Element,
    ctx: ConvertContext | None = None,
) -> float | None:
    """Get effective stroke opacity combining 'opacity' and 'stroke-opacity'.

    Returns:
        Combined opacity value, or None if fully opaque.
    """
    base = ctx.opacity_multiplier if ctx is not None else 1.0

    op = _get_attr(elem, 'opacity', ctx) if ctx else elem.get('opacity')
    if op is not None:
        base *= parse_opacity(op)

    stroke_op = _get_attr(elem, 'stroke-opacity', ctx) if ctx else elem.get('stroke-opacity')
    if stroke_op is not None:
        base *= parse_opacity(stroke_op)

    return base if base < 1.0 else None
