"""SVG element converters: rect, circle, line, path, polygon, polyline, text, image, ellipse."""

from __future__ import annotations

import math
import re
import base64
from typing import Any
from xml.etree import ElementTree as ET

from .drawingml_context import ConvertContext, ShapeResult
from .drawingml_utils import (
    SVG_NS, XLINK_NS, ANGLE_UNIT, FONT_PX_TO_HUNDREDTHS_PT, DASH_PRESETS,
    px_to_emu, _f, _get_attr,
    ctx_x, ctx_y, ctx_w, ctx_h,
    parse_hex_color, resolve_url_id, get_effective_filter_id,
    parse_font_family, is_cjk_char, estimate_text_width,
    _xml_escape,
)
from .drawingml_styles import (
    build_solid_fill, build_gradient_fill,
    build_fill_xml, build_stroke_xml, build_effect_xml,
    get_fill_opacity, get_stroke_opacity,
)
from .drawingml_paths import (
    PathCommand, parse_svg_path, svg_path_to_absolute,
    normalize_path_commands, path_commands_to_drawingml,
)


def _wrap_shape(
    shape_id: int, name: str,
    off_x: int, off_y: int,
    ext_cx: int, ext_cy: int,
    geom_xml: str, fill_xml: str, stroke_xml: str,
    effect_xml: str = '', extra_xml: str = '',
    rot: int = 0,
) -> str:
    """Wrap DrawingML content into a <p:sp> shape element."""
    rot_attr = f' rot="{rot}"' if rot else ''
    return f'''<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="{_xml_escape(name)}"/>
<p:cNvSpPr/><p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm{rot_attr}><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
{geom_xml}
{fill_xml}
{stroke_xml}
{effect_xml}
</p:spPr>
{extra_xml}
</p:sp>'''


# ---------------------------------------------------------------------------
# rect
# ---------------------------------------------------------------------------

def convert_rect(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <rect> to DrawingML shape."""
    x = ctx_x(_f(elem.get('x')), ctx)
    y = ctx_y(_f(elem.get('y')), ctx)
    w = ctx_w(_f(elem.get('width')), ctx)
    h = ctx_h(_f(elem.get('height')), ctx)

    if w <= 0 or h <= 0:
        return None

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_effect_xml(ctx.defs[filt_id])

    rot = 0
    transform = elem.get('transform')
    if transform:
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)

    geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'

    shape_id = ctx.next_id()
    off_x = px_to_emu(x)
    off_y = px_to_emu(y)
    ext_cx = px_to_emu(w)
    ext_cy = px_to_emu(h)
    return ShapeResult(
        xml=_wrap_shape(
            shape_id, f'Rectangle {shape_id}',
            off_x, off_y, ext_cx, ext_cy,
            geom, fill, stroke, effect, rot=rot,
        ),
        bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy),
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

    sw = _f(_get_attr(elem, 'stroke-width', ctx), 0)
    r = _f(elem.get('r'), 0)
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
    cx_ = _f(elem.get('cx'))
    cy_ = _f(elem.get('cy'))
    r = _f(elem.get('r'))

    if r <= 0:
        return None

    # --- Donut-chart arc segment detection ---
    if _is_donut_circle(elem, ctx):
        dasharray = _get_attr(elem, 'stroke-dasharray', ctx)
        dash_vals = re.split(r'[\s,]+', dasharray.strip())
        dash_len = float(dash_vals[0]) if dash_vals else 0
        dash_offset = _f(elem.get('stroke-dashoffset'), 0)
        stroke_width = _f(_get_attr(elem, 'stroke-width', ctx), 1)

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
        op = get_fill_opacity(elem, ctx)
        grad_id = resolve_url_id(stroke_val) if stroke_val else None
        if grad_id and grad_id in ctx.defs:
            fill = build_gradient_fill(ctx.defs[grad_id], op)
        elif stroke_val:
            color = parse_hex_color(stroke_val)
            fill = build_solid_fill(color, op) if color else '<a:noFill/>'
        else:
            fill = '<a:noFill/>'

        stroke_xml = '<a:ln><a:noFill/></a:ln>'

        effect = ''
        filt_id = get_effective_filter_id(elem, ctx)
        if filt_id and filt_id in ctx.defs:
            effect = build_effect_xml(ctx.defs[filt_id])

        shape_id = ctx.next_id()
        return ShapeResult(
            xml=_wrap_shape(
                shape_id, f'Arc {shape_id}',
                min_x, min_y, w_emu, h_emu,
                geom, fill, stroke_xml, effect,
            ),
            bounds_emu=(min_x, min_y, min_x + w_emu, min_y + h_emu),
        )

    # --- Normal circle ---
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
        effect = build_effect_xml(ctx.defs[filt_id])

    geom = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    shape_id = ctx.next_id()
    off_x = px_to_emu(x)
    off_y = px_to_emu(y)
    ext_cx = px_to_emu(w)
    ext_cy = px_to_emu(h)
    return ShapeResult(
        xml=_wrap_shape(
            shape_id, f'Ellipse {shape_id}',
            off_x, off_y, ext_cx, ext_cy,
            geom, fill, stroke, effect,
        ),
        bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy),
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
    x1 = ctx_x(_f(elem.get('x1')), ctx)
    y1 = ctx_y(_f(elem.get('y1')), ctx)
    x2 = ctx_x(_f(elem.get('x2')), ctx)
    y2 = ctx_y(_f(elem.get('y2')), ctx)

    min_x = min(x1, x2)
    min_y = min(y1, y2)

    stroke_op = get_stroke_opacity(elem, ctx)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    rot = 0
    transform = elem.get('transform')
    if transform:
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)

    shape_id = ctx.next_id()
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)

    # Determine if this line carries arrow markers.
    has_marker = bool(
        _get_attr(elem, 'marker-start', ctx) or
        _get_attr(elem, 'marker-end', ctx)
    )

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

        rot_attr = f' rot="{rot}"' if rot else ''
        xml = (
            f'<p:sp>'
            f'<p:nvSpPr>'
            f'<p:cNvPr id="{shape_id}" name="{_xml_escape(f"Line {shape_id}")}"/>'
            f'<p:cNvSpPr/><p:nvPr/>'
            f'</p:nvSpPr>'
            f'<p:spPr>'
            f'<a:xfrm{flip_attr}{rot_attr}>'
            f'<a:off x="{off_x}" y="{off_y}"/>'
            f'<a:ext cx="{w_emu}" cy="{h_emu}"/>'
            f'</a:xfrm>'
            f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:noFill/>'
            f'{stroke}'
            f'</p:spPr>'
            f'</p:sp>'
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
            geom, '<a:noFill/>', stroke, rot=rot,
        )

    return ShapeResult(
        xml=xml,
        bounds_emu=(off_x, off_y, off_x + w_emu, off_y + h_emu),
    )


# ---------------------------------------------------------------------------
# path
# ---------------------------------------------------------------------------

def convert_path(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <path> to DrawingML custom geometry shape."""
    d = elem.get('d', '')
    if not d:
        return None

    commands = parse_svg_path(d)
    commands = svg_path_to_absolute(commands)
    commands = normalize_path_commands(commands)

    tx, ty = 0.0, 0.0
    rot = 0
    transform = elem.get('transform')
    if transform:
        t_match = re.search(r'translate\(\s*([-\d.]+)[\s,]+([-\d.]+)\s*\)', transform)
        if t_match:
            tx = float(t_match.group(1))
            ty = float(t_match.group(2))
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)

    path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
        commands, ctx.translate_x + tx, ctx.translate_y + ty,
        ctx.scale_x, ctx.scale_y,
    )

    if not path_xml:
        return None

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

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
        effect = build_effect_xml(ctx.defs[filt_id])

    shape_id = ctx.next_id()
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)
    return ShapeResult(
        xml=_wrap_shape(
            shape_id, f'Freeform {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, fill, stroke, effect, rot=rot,
        ),
        bounds_emu=(off_x, off_y, off_x + w_emu, off_y + h_emu),
    )


# ---------------------------------------------------------------------------
# polygon / polyline
# ---------------------------------------------------------------------------

def _parse_points(points_str: str) -> list[tuple[float, float]]:
    """Parse SVG points attribute into a list of (x, y) tuples."""
    nums = re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)', points_str)
    if len(nums) < 4:
        return []
    return [(float(nums[i]), float(nums[i + 1])) for i in range(0, len(nums) - 1, 2)]


def convert_polygon(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <polygon> to DrawingML custom geometry shape."""
    points = _parse_points(elem.get('points', ''))
    if not points:
        return None

    commands = [PathCommand('M', [points[0][0], points[0][1]])]
    for px_, py_ in points[1:]:
        commands.append(PathCommand('L', [px_, py_]))
    commands.append(PathCommand('Z', []))

    path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
        commands, ctx.translate_x, ctx.translate_y,
        ctx.scale_x, ctx.scale_y,
    )

    if not path_xml:
        return None

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

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

    rot = 0
    transform = elem.get('transform')
    if transform:
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)

    shape_id = ctx.next_id()
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)
    return ShapeResult(
        xml=_wrap_shape(
            shape_id, f'Polygon {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, fill, stroke, rot=rot,
        ),
        bounds_emu=(off_x, off_y, off_x + w_emu, off_y + h_emu),
    )


def convert_polyline(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <polyline> to DrawingML custom geometry shape."""
    points = _parse_points(elem.get('points', ''))
    if not points:
        return None

    commands = [PathCommand('M', [points[0][0], points[0][1]])]
    for px_, py_ in points[1:]:
        commands.append(PathCommand('L', [px_, py_]))

    path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
        commands, ctx.translate_x, ctx.translate_y,
        ctx.scale_x, ctx.scale_y,
    )

    if not path_xml:
        return None

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

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

    rot = 0
    transform = elem.get('transform')
    if transform:
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)

    shape_id = ctx.next_id()
    off_x = px_to_emu(min_x)
    off_y = px_to_emu(min_y)
    return ShapeResult(
        xml=_wrap_shape(
            shape_id, f'Polyline {shape_id}',
            off_x, off_y, w_emu, h_emu,
            geom, '<a:noFill/>', stroke, rot=rot,
        ),
        bounds_emu=(off_x, off_y, off_x + w_emu, off_y + h_emu),
    )


# ---------------------------------------------------------------------------
# text
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Collapse internal whitespace/newlines into a single space, strip ends."""
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text).strip()


def _build_text_runs(
    elem: ET.Element,
    parent_attrs: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build a list of text runs from a <text> element, handling <tspan> children.

    Each run is a dict with keys: text, fill, fill_raw, font_weight,
    font_style, font_family, font_size.
    """
    runs: list[dict[str, Any]] = []

    if elem.text:
        t = _normalize_text(elem.text)
        if t:
            runs.append({**parent_attrs, 'text': t})

    for child in elem:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag == 'tspan':
            t = _normalize_text(''.join(child.itertext()))
            if t:
                run_attrs = dict(parent_attrs)
                if child.get('font-weight'):
                    run_attrs['font_weight'] = child.get('font-weight')
                if child.get('fill'):
                    child_fill = child.get('fill')
                    run_attrs['fill_raw'] = child_fill
                    c = parse_hex_color(child_fill)
                    if c:
                        run_attrs['fill'] = c
                if child.get('font-size'):
                    run_attrs['font_size'] = _f(child.get('font-size'), run_attrs['font_size'])
                if child.get('font-family'):
                    run_attrs['font_family'] = child.get('font-family')
                if child.get('font-style'):
                    run_attrs['font_style'] = child.get('font-style')
                if child.get('text-decoration'):
                    run_attrs['text_decoration'] = child.get('text-decoration')
                runs.append({**run_attrs, 'text': t})

            # Tail text after </tspan> belongs to parent
            if child.tail:
                t = _normalize_text(child.tail)
                if t:
                    runs.append({**parent_attrs, 'text': t})

    return runs


def _build_run_xml(
    run: dict[str, Any],
    default_fonts: dict[str, str],
    ctx: ConvertContext | None = None,
) -> str:
    """Build a single <a:r> XML from a run dict. Supports gradient fills on text."""
    text = run['text']
    fill = run.get('fill', '000000')
    fill_raw = run.get('fill_raw', '')
    fw = run.get('font_weight', '400')
    fs_px = run.get('font_size', 16)
    fstyle = run.get('font_style', '')
    ff = run.get('font_family', '')
    opacity = run.get('opacity')

    text_dec = run.get('text_decoration', '')

    sz = round(fs_px * FONT_PX_TO_HUNDREDTHS_PT)
    b_attr = ' b="1"' if fw in ('bold', '600', '700', '800', '900') else ''
    i_attr = ' i="1"' if fstyle == 'italic' else ''
    u_attr = ' u="sng"' if 'underline' in text_dec else ''
    strike_attr = ' strike="sngStrike"' if 'line-through' in text_dec else ''

    fonts = parse_font_family(ff) if ff else default_fonts

    # Build fill XML - gradient or solid
    grad_id = resolve_url_id(fill_raw)
    if grad_id and ctx and grad_id in ctx.defs:
        fill_xml = build_gradient_fill(ctx.defs[grad_id], opacity)
    else:
        alpha_xml = ''
        if opacity is not None and opacity < 1.0:
            alpha_xml = f'<a:alpha val="{int(opacity * 100000)}"/>'
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">{alpha_xml}</a:srgbClr></a:solidFill>'

    return f'''<a:r>
<a:rPr lang="zh-CN" sz="{sz}"{b_attr}{i_attr}{u_attr}{strike_attr} dirty="0">
{fill_xml}
<a:latin typeface="{_xml_escape(fonts['latin'])}"/>
<a:ea typeface="{_xml_escape(fonts['ea'])}"/>
<a:cs typeface="{_xml_escape(fonts['latin'])}"/>
</a:rPr>
<a:t>{_xml_escape(text)}</a:t>
</a:r>'''


def convert_text(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <text> to DrawingML text shape with multi-run support."""
    x = ctx_x(_f(elem.get('x')), ctx)
    y = ctx_y(_f(elem.get('y')), ctx)
    font_size = _f(_get_attr(elem, 'font-size', ctx), 16) * ctx.scale_y
    font_weight = _get_attr(elem, 'font-weight', ctx) or '400'
    font_family_str = _get_attr(elem, 'font-family', ctx) or ''
    text_anchor = _get_attr(elem, 'text-anchor', ctx) or 'start'
    fill_raw = _get_attr(elem, 'fill', ctx) or '#000000'
    fill_color = parse_hex_color(fill_raw) or '000000'
    opacity = get_fill_opacity(elem, ctx)
    font_style = _get_attr(elem, 'font-style', ctx) or ''
    text_decoration = _get_attr(elem, 'text-decoration', ctx) or ''

    fonts = parse_font_family(font_family_str)

    parent_attrs: dict[str, Any] = {
        'fill': fill_color,
        'fill_raw': fill_raw,
        'font_weight': font_weight,
        'font_size': font_size,
        'font_family': font_family_str,
        'font_style': font_style,
        'text_decoration': text_decoration,
        'opacity': opacity,
    }
    runs = _build_text_runs(elem, parent_attrs)

    if not runs:
        return None

    full_text = ''.join(r['text'] for r in runs)
    if not full_text.strip():
        return None

    # Estimate text dimensions
    text_width = estimate_text_width(full_text, font_size, font_weight) * 1.15
    text_height = font_size * 1.5
    padding = font_size * 0.1

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

    # Letter spacing
    spc_attr = ''
    letter_spacing = _get_attr(elem, 'letter-spacing', ctx)
    if letter_spacing:
        try:
            spc_val = float(letter_spacing) * 100
            spc_attr = f' spc="{int(spc_val)}"'
        except ValueError:
            pass

    # Text rotation
    text_rot = 0
    text_transform = elem.get('transform', '')
    if text_transform:
        rot_match = re.search(r'rotate\(\s*([-\d.]+)', text_transform)
        if rot_match:
            text_rot = int(float(rot_match.group(1)) * ANGLE_UNIT)

    # Alignment
    algn_map = {'start': 'l', 'middle': 'ctr', 'end': 'r'}
    algn = algn_map.get(text_anchor, 'l')

    # Shadow effect
    effect_xml = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect_xml = build_effect_xml(ctx.defs[filt_id])

    shape_id = ctx.next_id()
    rot_attr = f' rot="{text_rot}"' if text_rot else ''

    runs_xml = '\n'.join(_build_run_xml(r, fonts, ctx) for r in runs)
    off_x = px_to_emu(box_x)
    off_y = px_to_emu(box_y)
    ext_cx = px_to_emu(box_w)
    ext_cy = px_to_emu(box_h)

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
{effect_xml}
</p:spPr>
<p:txBody>
<a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t" anchorCtr="0">
<a:spAutoFit/>
</a:bodyPr>
<a:lstStyle/>
<a:p>
<a:pPr algn="{algn}"/>
{runs_xml}
</a:p>
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
    raw_x = _f(elem.get('x'))
    raw_y = _f(elem.get('y'))
    raw_w = _f(elem.get('width'))
    raw_h = _f(elem.get('height'))

    x = ctx_x(raw_x, ctx)
    y = ctx_y(raw_y, ctx)
    w = ctx_w(raw_w, ctx)
    h = ctx_h(raw_h, ctx)

    if w <= 0 or h <= 0:
        return None

    # Extract image data
    if href.startswith('data:'):
        match = re.match(r'data:image/(\w+);base64,(.+)', href, re.DOTALL)
        if not match:
            return None
        img_format = match.group(1).lower()
        if img_format == 'jpeg':
            img_format = 'jpg'
        img_data = base64.b64decode(match.group(2))
    else:
        if ctx.svg_dir is None:
            return None
        img_path = ctx.svg_dir / href
        if not img_path.exists():
            img_path = ctx.svg_dir.parent / href
        if not img_path.exists():
            print(f'  Warning: External image not found: {href}')
            return None
        img_format = img_path.suffix.lstrip('.').lower()
        if img_format == 'jpeg':
            img_format = 'jpg'
        img_data = img_path.read_bytes()

    img_idx = len(ctx.media_files) + 1
    img_filename = f's{ctx.slide_num}_img{img_idx}.{img_format}'
    ctx.media_files[img_filename] = img_data

    r_id = ctx.next_rel_id()
    ctx.rel_entries.append({
        'id': r_id,
        'type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
        'target': f'../media/{img_filename}',
    })

    rot = 0
    transform = elem.get('transform')
    if transform:
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)
    rot_attr = f' rot="{rot}"' if rot else ''

    # Resolve clip-path → DrawingML geometry
    clip_geom = _resolve_clip_geometry(elem, ctx, raw_x, raw_y, raw_w, raw_h)

    shape_id = ctx.next_id()
    off_x = px_to_emu(x)
    off_y = px_to_emu(y)
    ext_cx = px_to_emu(w)
    ext_cy = px_to_emu(h)

    return ShapeResult(xml=f'''<p:pic>
<p:nvPicPr>
<p:cNvPr id="{shape_id}" name="Image {shape_id}"/>
<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
<p:nvPr/>
</p:nvPicPr>
<p:blipFill>
<a:blip r:embed="{r_id}"/>
<a:stretch><a:fillRect/></a:stretch>
</p:blipFill>
<p:spPr>
<a:xfrm{rot_attr}><a:off x="{off_x}" y="{off_y}"/>
<a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
{clip_geom}
</p:spPr>
</p:pic>''', bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))


# ---------------------------------------------------------------------------
# ellipse
# ---------------------------------------------------------------------------

def convert_ellipse(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert SVG <ellipse> to DrawingML ellipse shape."""
    cx_ = ctx_x(_f(elem.get('cx')), ctx)
    cy_ = ctx_y(_f(elem.get('cy')), ctx)
    rx = _f(elem.get('rx')) * ctx.scale_x
    ry = _f(elem.get('ry')) * ctx.scale_y

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

    geom = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    rot = 0
    transform = elem.get('transform')
    if transform:
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rot = int(float(r_match.group(1)) * ANGLE_UNIT)

    shape_id = ctx.next_id()
    off_x = px_to_emu(x)
    off_y = px_to_emu(y)
    ext_cx = px_to_emu(w)
    ext_cy = px_to_emu(h)
    return ShapeResult(
        xml=_wrap_shape(
            shape_id, f'Ellipse {shape_id}',
            off_x, off_y, ext_cx, ext_cy,
            geom, fill, stroke, rot=rot,
        ),
        bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy),
    )
