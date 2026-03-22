#!/usr/bin/env python3
"""
PPT Master - SVG to DrawingML Native Shapes Converter

Converts SVG elements into native PowerPoint DrawingML shapes,
so the resulting PPTX is directly editable without manual "Convert to Shape".

This module handles the SVG subset used by PPT Master (after finalize_svg.py processing):
- rect, circle, line, path, polygon, polyline, text, g, image
- linearGradient, radialGradient (in defs)
- filter (shadow effects via feGaussianBlur + feOffset)
- transform (translate, scale, rotate)

Usage:
    from svg_to_shapes import convert_svg_to_slide_shapes
    slide_xml, media_files, rel_entries = convert_svg_to_slide_shapes(svg_path, slide_num=1)
"""

import math
import re
import base64
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'

# 1 SVG pixel = 9525 EMU (at 96 DPI)
EMU_PER_PX = 9525

# DrawingML font size unit: 1/100 of a point. 1px = 0.75pt at 96 DPI.
FONT_PX_TO_HUNDREDTHS_PT = 75

# DrawingML angle unit: 60000ths of a degree
ANGLE_UNIT = 60000

# Known East Asian fonts
EA_FONTS = {
    'PingFang SC', 'PingFang TC', 'PingFang HK',
    'Microsoft YaHei', 'Microsoft JhengHei',
    'SimSun', 'SimHei', 'FangSong', 'KaiTi', 'STKaiti',
    'STHeiti', 'STSong', 'STFangsong', 'STXihei', 'STZhongsong',
    'Hiragino Sans', 'Hiragino Sans GB', 'Hiragino Mincho ProN',
    'Noto Sans SC', 'Noto Sans TC', 'Noto Serif SC', 'Noto Serif TC',
    'Source Han Sans SC', 'Source Han Sans TC',
    'Source Han Serif SC', 'Source Han Serif TC',
    'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
    'YouYuan', 'LiSu', 'HuaWenKaiTi',
}
SYSTEM_FONTS = {'system-ui', '-apple-system', 'BlinkMacSystemFont'}

# Preset dash patterns: SVG stroke-dasharray -> DrawingML prstDash
DASH_PRESETS = {
    '4,4': 'dash',
    '4 4': 'dash',
    '6,3': 'dash',
    '6 3': 'dash',
    '2,2': 'sysDot',
    '2 2': 'sysDot',
    '8,4': 'lgDash',
    '8 4': 'lgDash',
    '8,4,2,4': 'lgDashDot',
    '8 4 2 4': 'lgDashDot',
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConvertContext:
    """Shared context passed through the conversion pipeline."""
    defs: Dict[str, ET.Element] = field(default_factory=dict)
    id_counter: int = 2  # start at 2 (1 is reserved for spTree root)
    slide_num: int = 1  # slide number for unique media filenames
    translate_x: float = 0.0
    translate_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    filter_id: Optional[str] = None  # inherited filter from parent <g>
    media_files: Dict[str, bytes] = field(default_factory=dict)  # filename -> data
    rel_entries: List[Dict[str, str]] = field(default_factory=list)
    rel_id_counter: int = 2  # rId1 reserved for slideLayout

    def next_id(self) -> int:
        cid = self.id_counter
        self.id_counter += 1
        return cid

    def next_rel_id(self) -> str:
        rid = f'rId{self.rel_id_counter}'
        self.rel_id_counter += 1
        return rid

    def child(self, dx: float = 0, dy: float = 0,
              sx: float = 1.0, sy: float = 1.0,
              filter_id: Optional[str] = None) -> 'ConvertContext':
        """Create child context with accumulated translation and scale."""
        return ConvertContext(
            defs=self.defs,
            id_counter=self.id_counter,
            slide_num=self.slide_num,
            translate_x=self.translate_x + dx,
            translate_y=self.translate_y + dy,
            scale_x=self.scale_x * sx,
            scale_y=self.scale_y * sy,
            filter_id=filter_id or self.filter_id,
            media_files=self.media_files,
            rel_entries=self.rel_entries,
            rel_id_counter=self.rel_id_counter,
        )

    def sync_from_child(self, child_ctx: 'ConvertContext'):
        """Sync counters back from child context."""
        self.id_counter = child_ctx.id_counter
        self.rel_id_counter = child_ctx.rel_id_counter


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def px_to_emu(px: float) -> int:
    """Convert SVG pixels to EMU."""
    return round(px * EMU_PER_PX)


def _f(val: Optional[str], default: float = 0.0) -> float:
    """Parse a float attribute, returning default if missing."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def ctx_x(val: float, ctx: 'ConvertContext') -> float:
    """Apply context scale + translate to an x coordinate."""
    return val * ctx.scale_x + ctx.translate_x


def ctx_y(val: float, ctx: 'ConvertContext') -> float:
    """Apply context scale + translate to a y coordinate."""
    return val * ctx.scale_y + ctx.translate_y


def ctx_w(val: float, ctx: 'ConvertContext') -> float:
    """Apply context scale to a width value."""
    return val * ctx.scale_x


def ctx_h(val: float, ctx: 'ConvertContext') -> float:
    """Apply context scale to a height value."""
    return val * ctx.scale_y


# ---------------------------------------------------------------------------
# Color / style parsing
# ---------------------------------------------------------------------------

def parse_hex_color(color_str: str) -> Optional[str]:
    """Parse '#RRGGBB' or '#RGB' to 'RRGGBB'. Returns None on failure."""
    if not color_str:
        return None
    color_str = color_str.strip()
    if color_str.startswith('#'):
        color_str = color_str[1:]
    if len(color_str) == 3:
        color_str = ''.join(c * 2 for c in color_str)
    if len(color_str) == 6 and all(c in '0123456789abcdefABCDEF' for c in color_str):
        return color_str.upper()
    return None


def parse_stop_style(style_str: str) -> Tuple[Optional[str], float]:
    """Parse stop element's style attribute: 'stop-color:#XXX;stop-opacity:N'"""
    color = None
    opacity = 1.0
    if not style_str:
        return color, opacity
    for part in style_str.split(';'):
        part = part.strip()
        if part.startswith('stop-color:'):
            color = parse_hex_color(part.split(':', 1)[1].strip())
        elif part.startswith('stop-opacity:'):
            try:
                opacity = float(part.split(':', 1)[1].strip())
            except ValueError:
                pass
    return color, opacity


def resolve_url_id(url_str: str) -> Optional[str]:
    """Extract ID from 'url(#someId)' reference."""
    if not url_str:
        return None
    m = re.match(r'url\(#([^)]+)\)', url_str.strip())
    return m.group(1) if m else None


def get_effective_filter_id(elem: ET.Element, ctx: ConvertContext) -> Optional[str]:
    """Get the filter ID for an element, considering inherited context."""
    filt = elem.get('filter')
    if filt:
        return resolve_url_id(filt)
    return ctx.filter_id


# ---------------------------------------------------------------------------
# Font parsing
# ---------------------------------------------------------------------------

def parse_font_family(font_family_str: str) -> Dict[str, str]:
    """Parse CSS font-family to latin/ea typefaces."""
    if not font_family_str:
        return {'latin': 'Segoe UI', 'ea': 'Microsoft YaHei'}

    fonts = [f.strip().strip("'\"") for f in font_family_str.split(',')]
    latin_font = None
    ea_font = None

    for font in fonts:
        if font in SYSTEM_FONTS or font in ('sans-serif', 'serif', 'monospace'):
            continue
        if font in EA_FONTS:
            ea_font = ea_font or font
        else:
            latin_font = latin_font or font

    # If no latin font found but we have EA, use EA as latin too
    # (PPT renders CJK text via latin typeface when ea doesn't match)
    if not latin_font and ea_font:
        latin_font = ea_font

    return {
        'latin': latin_font or 'Segoe UI',
        'ea': ea_font or latin_font or 'Microsoft YaHei',
    }


def is_cjk_char(ch: str) -> bool:
    """Check if a character is CJK."""
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x2E80 <= cp <= 0x2EFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0xF900 <= cp <= 0xFAFF or
            0x20000 <= cp <= 0x2A6DF)


def estimate_text_width(text: str, font_size: float, font_weight: str = '400') -> float:
    """Estimate text width in SVG pixels."""
    width = 0.0
    for ch in text:
        if is_cjk_char(ch):
            width += font_size
        elif ch == ' ':
            width += font_size * 0.3
        elif ch in 'mMwWOQ':
            width += font_size * 0.75
        elif ch in 'iIlj1!|':
            width += font_size * 0.3
        else:
            width += font_size * 0.55
    # Bold text is slightly wider
    if font_weight in ('bold', '600', '700', '800', '900'):
        width *= 1.05
    return width


# ---------------------------------------------------------------------------
# DrawingML XML builders
# ---------------------------------------------------------------------------

def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))


def build_solid_fill(color: str, opacity: Optional[float] = None) -> str:
    """Build <a:solidFill> XML."""
    alpha = ''
    if opacity is not None and opacity < 1.0:
        alpha = f'<a:alpha val="{int(opacity * 100000)}"/>'
    return f'<a:solidFill><a:srgbClr val="{color}">{alpha}</a:srgbClr></a:solidFill>'


def build_gradient_fill(grad_elem: ET.Element,
                        opacity: Optional[float] = None) -> str:
    """Build <a:gradFill> from SVG linearGradient or radialGradient element."""
    tag = grad_elem.tag.replace(f'{{{SVG_NS}}}', '')

    # Parse stops
    stops_xml = []
    for child in grad_elem:
        child_tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if child_tag != 'stop':
            continue
        offset_str = child.get('offset', '0').strip().rstrip('%')
        try:
            offset = float(offset_str)
            # If percentage (most common), offset is 0-100
            if offset > 1.0:
                offset = offset / 100.0
        except ValueError:
            offset = 0.0
        pos = int(offset * 100000)

        # Parse color from style attribute or direct attributes
        style = child.get('style', '')
        color, stop_opacity = parse_stop_style(style)
        if not color:
            color = parse_hex_color(child.get('stop-color', '#000000'))
        if color is None:
            color = '000000'
        # Also check direct stop-opacity attribute (overrides style)
        direct_stop_op = child.get('stop-opacity')
        if direct_stop_op is not None:
            try:
                stop_opacity = float(direct_stop_op)
            except ValueError:
                pass

        alpha_xml = ''
        effective_opacity = stop_opacity
        if opacity is not None:
            effective_opacity *= opacity
        if effective_opacity < 1.0:
            alpha_xml = f'<a:alpha val="{int(effective_opacity * 100000)}"/>'

        stops_xml.append(
            f'<a:gs pos="{pos}"><a:srgbClr val="{color}">{alpha_xml}</a:srgbClr></a:gs>'
        )

    if not stops_xml:
        return ''

    gs_list = '\n'.join(stops_xml)

    if tag == 'linearGradient':
        # Calculate angle from x1,y1 -> x2,y2
        # Values can be fractions (0-1) or percentages (0%-100%)
        def parse_grad_coord(val_str: str, default: float = 0.0) -> float:
            val_str = val_str.strip()
            if val_str.endswith('%'):
                return float(val_str.rstrip('%')) / 100.0
            v = float(val_str)
            # Heuristic: if > 1, treat as percentage
            return v / 100.0 if v > 1.0 else v

        x1 = parse_grad_coord(grad_elem.get('x1', '0'))
        y1 = parse_grad_coord(grad_elem.get('y1', '0'))
        x2 = parse_grad_coord(grad_elem.get('x2', '1'))
        y2 = parse_grad_coord(grad_elem.get('y2', '1'))

        angle_rad = math.atan2(y2 - y1, x2 - x1)
        angle_deg = math.degrees(angle_rad)
        # DrawingML angle: 0 = right, rotates clockwise, in 60000ths of degree
        # SVG gradient: angle from (x1,y1) to (x2,y2) in standard math direction
        # DrawingML lin ang: measured from top, clockwise
        dml_angle = int(((90 + angle_deg) % 360) * ANGLE_UNIT)

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


def build_fill_xml(elem: ET.Element, ctx: ConvertContext,
                   opacity: Optional[float] = None) -> str:
    """Build fill XML for a shape element."""
    fill = elem.get('fill')
    if fill is None:
        # SVG default fill is black
        fill = '#000000'

    if fill == 'none':
        return '<a:noFill/>'

    # Check for gradient reference
    grad_id = resolve_url_id(fill)
    if grad_id and grad_id in ctx.defs:
        return build_gradient_fill(ctx.defs[grad_id], opacity)

    # Solid color
    color = parse_hex_color(fill)
    if color:
        return build_solid_fill(color, opacity)

    return '<a:noFill/>'


def build_stroke_xml(elem: ET.Element, opacity: Optional[float] = None) -> str:
    """Build <a:ln> XML for stroke."""
    stroke = elem.get('stroke')
    if not stroke or stroke == 'none':
        return '<a:ln><a:noFill/></a:ln>'

    color = parse_hex_color(stroke)
    if not color:
        return '<a:ln><a:noFill/></a:ln>'

    width = _f(elem.get('stroke-width'), 1.0)
    width_emu = px_to_emu(width)

    # Dash pattern
    dash_xml = ''
    dasharray = elem.get('stroke-dasharray')
    if dasharray and dasharray != 'none':
        preset = DASH_PRESETS.get(dasharray.strip())
        if preset:
            dash_xml = f'<a:prstDash val="{preset}"/>'
        else:
            dash_xml = '<a:prstDash val="dash"/>'

    # Line cap
    cap_map = {'round': 'rnd', 'square': 'sq', 'butt': 'flat'}
    cap_attr = ''
    linecap = elem.get('stroke-linecap')
    if linecap and linecap in cap_map:
        cap_attr = f' cap="{cap_map[linecap]}"'

    alpha_xml = ''
    if opacity is not None and opacity < 1.0:
        alpha_xml = f'<a:alpha val="{int(opacity * 100000)}"/>'

    return f'''<a:ln w="{width_emu}"{cap_attr}>
<a:solidFill><a:srgbClr val="{color}">{alpha_xml}</a:srgbClr></a:solidFill>{dash_xml}
</a:ln>'''


def build_shadow_xml(filter_elem: ET.Element) -> str:
    """Build <a:effectLst> with <a:outerShdw> from SVG filter element."""
    if filter_elem is None:
        return ''

    std_dev = 4.0
    dx = 0.0
    dy = 4.0
    shadow_opacity = 0.3

    for child in filter_elem.iter():
        tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if tag == 'feGaussianBlur':
            std_dev = _f(child.get('stdDeviation'), 4.0)
        elif tag == 'feOffset':
            dx = _f(child.get('dx'), 0.0)
            dy = _f(child.get('dy'), 4.0)
        elif tag == 'feFlood':
            shadow_opacity = _f(child.get('flood-opacity'), 0.3)
        elif tag == 'feFuncA':
            # feComponentTransfer > feFuncA type="linear" slope="0.3"
            if child.get('type') == 'linear':
                shadow_opacity = _f(child.get('slope'), 0.3)

    blur_rad = px_to_emu(std_dev * 2)
    dist = px_to_emu(math.sqrt(dx * dx + dy * dy))
    # Direction angle: atan2(dy, dx), converted to DrawingML (from top, CW)
    dir_angle = int(((90 + math.degrees(math.atan2(dy, max(dx, 0.001)))) % 360) * ANGLE_UNIT)
    alpha_val = int(shadow_opacity * 100000)

    return f'''<a:effectLst>
<a:outerShdw blurRad="{blur_rad}" dist="{dist}" dir="{dir_angle}" algn="tl" rotWithShape="0">
<a:srgbClr val="000000"><a:alpha val="{alpha_val}"/></a:srgbClr>
</a:outerShdw>
</a:effectLst>'''


def get_element_opacity(elem: ET.Element) -> Optional[float]:
    """Get opacity value from element, returns None if 1.0 or not set."""
    op = elem.get('opacity')
    if op is None:
        return None
    try:
        val = float(op)
        return val if val < 1.0 else None
    except ValueError:
        return None


def get_fill_opacity(elem: ET.Element) -> Optional[float]:
    """
    Get effective fill opacity combining 'opacity' and 'fill-opacity'.
    Returns None if fully opaque.
    """
    base = 1.0
    op = elem.get('opacity')
    if op:
        try:
            base = float(op)
        except ValueError:
            pass

    fill_op = elem.get('fill-opacity')
    if fill_op:
        try:
            base *= float(fill_op)
        except ValueError:
            pass

    return base if base < 1.0 else None


def get_stroke_opacity(elem: ET.Element) -> Optional[float]:
    """
    Get effective stroke opacity combining 'opacity' and 'stroke-opacity'.
    Returns None if fully opaque.
    """
    base = 1.0
    op = elem.get('opacity')
    if op:
        try:
            base = float(op)
        except ValueError:
            pass

    stroke_op = elem.get('stroke-opacity')
    if stroke_op:
        try:
            base *= float(stroke_op)
        except ValueError:
            pass

    return base if base < 1.0 else None


# ---------------------------------------------------------------------------
# SVG Path Parser
# ---------------------------------------------------------------------------

@dataclass
class PathCommand:
    cmd: str  # M, L, C, Z, etc. (uppercase = absolute)
    args: List[float] = field(default_factory=list)


def parse_svg_path(d: str) -> List[PathCommand]:
    """Parse SVG path d attribute into a list of PathCommands."""
    if not d:
        return []

    commands = []
    # Tokenize: split into commands and numbers
    # Handle negative numbers and decimals correctly
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d)

    current_cmd = None
    current_args = []

    def flush():
        nonlocal current_cmd, current_args
        if current_cmd is not None:
            # Some commands can have implicit repeats
            arg_counts = {
                'M': 2, 'm': 2, 'L': 2, 'l': 2,
                'H': 1, 'h': 1, 'V': 1, 'v': 1,
                'C': 6, 'c': 6, 'S': 4, 's': 4,
                'Q': 4, 'q': 4, 'T': 2, 't': 2,
                'A': 7, 'a': 7, 'Z': 0, 'z': 0,
            }
            n = arg_counts.get(current_cmd, 0)
            if n == 0:
                commands.append(PathCommand(current_cmd, []))
            elif n > 0 and len(current_args) >= n:
                # Split into multiple commands if there are extra args
                i = 0
                while i + n <= len(current_args):
                    commands.append(PathCommand(current_cmd, current_args[i:i + n]))
                    # After first M, implicit commands become L
                    if current_cmd == 'M':
                        current_cmd = 'L'
                    elif current_cmd == 'm':
                        current_cmd = 'l'
                    i += n
            current_args = []

    for token in tokens:
        if token in 'MmLlHhVvCcSsQqTtAaZz':
            flush()
            current_cmd = token
            current_args = []
        else:
            try:
                current_args.append(float(token))
            except ValueError:
                pass

    flush()
    return commands


def svg_path_to_absolute(commands: List[PathCommand]) -> List[PathCommand]:
    """Convert all relative path commands to absolute."""
    result = []
    cx, cy = 0.0, 0.0  # Current point
    sx, sy = 0.0, 0.0  # Subpath start

    for cmd in commands:
        a = cmd.args
        if cmd.cmd == 'M':
            cx, cy = a[0], a[1]
            sx, sy = cx, cy
            result.append(PathCommand('M', [cx, cy]))
        elif cmd.cmd == 'm':
            cx += a[0]
            cy += a[1]
            sx, sy = cx, cy
            result.append(PathCommand('M', [cx, cy]))
        elif cmd.cmd == 'L':
            cx, cy = a[0], a[1]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'l':
            cx += a[0]
            cy += a[1]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'H':
            cx = a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'h':
            cx += a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'V':
            cy = a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'v':
            cy += a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'C':
            result.append(PathCommand('C', list(a)))
            cx, cy = a[4], a[5]
        elif cmd.cmd == 'c':
            abs_args = [
                cx + a[0], cy + a[1],
                cx + a[2], cy + a[3],
                cx + a[4], cy + a[5],
            ]
            result.append(PathCommand('C', abs_args))
            cx, cy = abs_args[4], abs_args[5]
        elif cmd.cmd == 'S':
            result.append(PathCommand('S', list(a)))
            cx, cy = a[2], a[3]
        elif cmd.cmd == 's':
            abs_args = [cx + a[0], cy + a[1], cx + a[2], cy + a[3]]
            result.append(PathCommand('S', abs_args))
            cx, cy = abs_args[2], abs_args[3]
        elif cmd.cmd == 'Q':
            result.append(PathCommand('Q', list(a)))
            cx, cy = a[2], a[3]
        elif cmd.cmd == 'q':
            abs_args = [cx + a[0], cy + a[1], cx + a[2], cy + a[3]]
            result.append(PathCommand('Q', abs_args))
            cx, cy = abs_args[2], abs_args[3]
        elif cmd.cmd == 'T':
            result.append(PathCommand('T', list(a)))
            cx, cy = a[0], a[1]
        elif cmd.cmd == 't':
            abs_args = [cx + a[0], cy + a[1]]
            result.append(PathCommand('T', abs_args))
            cx, cy = abs_args[0], abs_args[1]
        elif cmd.cmd == 'A':
            result.append(PathCommand('A', list(a)))
            cx, cy = a[5], a[6]
        elif cmd.cmd == 'a':
            abs_args = [a[0], a[1], a[2], a[3], a[4], cx + a[5], cy + a[6]]
            result.append(PathCommand('A', abs_args))
            cx, cy = abs_args[5], abs_args[6]
        elif cmd.cmd in ('Z', 'z'):
            result.append(PathCommand('Z', []))
            cx, cy = sx, sy

    return result


def _reflect_control_point(cp_x: float, cp_y: float,
                           cx: float, cy: float) -> Tuple[float, float]:
    """Reflect a control point through the current point."""
    return 2 * cx - cp_x, 2 * cy - cp_y


def _quad_to_cubic(qp_x: float, qp_y: float,
                   p0_x: float, p0_y: float,
                   p3_x: float, p3_y: float) -> List[float]:
    """Convert quadratic bezier control point to cubic bezier control points."""
    cp1_x = p0_x + 2.0 / 3.0 * (qp_x - p0_x)
    cp1_y = p0_y + 2.0 / 3.0 * (qp_y - p0_y)
    cp2_x = p3_x + 2.0 / 3.0 * (qp_x - p3_x)
    cp2_y = p3_y + 2.0 / 3.0 * (qp_y - p3_y)
    return [cp1_x, cp1_y, cp2_x, cp2_y, p3_x, p3_y]


def _arc_to_cubic_beziers(cx_: float, cy_: float,
                          rx: float, ry: float,
                          phi: float,
                          large_arc: int, sweep: int,
                          x2: float, y2: float) -> List[PathCommand]:
    """
    Convert SVG arc (endpoint parameterization) to cubic bezier curves.

    Uses the algorithm from the SVG spec (F.6.5) to convert endpoint to center
    parameterization, then approximates each arc segment with cubic beziers.
    """
    x1, y1 = cx_, cy_

    # If endpoints are the same, skip
    if abs(x1 - x2) < 1e-10 and abs(y1 - y2) < 1e-10:
        return []

    # Ensure radii are positive
    rx = abs(rx)
    ry = abs(ry)
    if rx < 1e-10 or ry < 1e-10:
        return [PathCommand('L', [x2, y2])]

    phi_rad = math.radians(phi)
    cos_phi = math.cos(phi_rad)
    sin_phi = math.sin(phi_rad)

    # Step 1: Compute (x1', y1')
    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    # Step 2: Compute (cx', cy')
    x1p2 = x1p * x1p
    y1p2 = y1p * y1p
    rx2 = rx * rx
    ry2 = ry * ry

    # Ensure radii are large enough
    lam = x1p2 / rx2 + y1p2 / ry2
    if lam > 1:
        lam_sqrt = math.sqrt(lam)
        rx *= lam_sqrt
        ry *= lam_sqrt
        rx2 = rx * rx
        ry2 = ry * ry

    num = max(rx2 * ry2 - rx2 * y1p2 - ry2 * x1p2, 0)
    den = rx2 * y1p2 + ry2 * x1p2
    sq = math.sqrt(num / den) if den > 1e-10 else 0.0

    if large_arc == sweep:
        sq = -sq

    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx

    # Step 3: Compute (cx, cy)
    arc_cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    arc_cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0

    # Step 4: Compute theta1 and dtheta
    def angle_between(ux, uy, vx, vy):
        n = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        if n < 1e-10:
            return 0
        c = (ux * vx + uy * vy) / n
        c = max(-1, min(1, c))
        a = math.acos(c)
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    theta1 = angle_between(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle_between(
        (x1p - cxp) / rx, (y1p - cyp) / ry,
        (-x1p - cxp) / rx, (-y1p - cyp) / ry
    )

    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi

    # Split arc into segments of at most 90 degrees
    n_segs = max(1, int(math.ceil(abs(dtheta) / (math.pi / 2))))
    d_per_seg = dtheta / n_segs

    result = []
    alpha = 4.0 / 3.0 * math.tan(d_per_seg / 4.0)

    for i in range(n_segs):
        t1 = theta1 + i * d_per_seg
        t2 = theta1 + (i + 1) * d_per_seg

        cos_t1 = math.cos(t1)
        sin_t1 = math.sin(t1)
        cos_t2 = math.cos(t2)
        sin_t2 = math.sin(t2)

        # Control points in unit circle
        ep1_x = cos_t1 - alpha * sin_t1
        ep1_y = sin_t1 + alpha * cos_t1
        ep2_x = cos_t2 + alpha * sin_t2
        ep2_y = sin_t2 - alpha * cos_t2
        ep_x = cos_t2
        ep_y = sin_t2

        # Scale by radii, rotate by phi, translate to center
        def transform_pt(px, py):
            x = rx * px
            y = ry * py
            xr = cos_phi * x - sin_phi * y + arc_cx
            yr = sin_phi * x + cos_phi * y + arc_cy
            return xr, yr

        cp1 = transform_pt(ep1_x, ep1_y)
        cp2 = transform_pt(ep2_x, ep2_y)
        ep = transform_pt(ep_x, ep_y)

        result.append(PathCommand('C', [cp1[0], cp1[1], cp2[0], cp2[1], ep[0], ep[1]]))

    return result


def normalize_path_commands(commands: List[PathCommand]) -> List[PathCommand]:
    """
    Normalize path commands:
    - Convert S/s to C (smooth cubic → explicit cubic)
    - Convert Q/q to C (quadratic → cubic)
    - Convert T/t to C (smooth quadratic → explicit cubic)
    - Convert A/a to C sequences (arc → cubic bezier approximation)
    """
    result = []
    cx, cy = 0.0, 0.0
    last_cp_x, last_cp_y = 0.0, 0.0  # Last control point for S/T
    last_cmd = ''

    for cmd in commands:
        a = cmd.args

        if cmd.cmd == 'M':
            cx, cy = a[0], a[1]
            last_cp_x, last_cp_y = cx, cy
            result.append(cmd)
        elif cmd.cmd == 'L':
            cx, cy = a[0], a[1]
            last_cp_x, last_cp_y = cx, cy
            result.append(cmd)
        elif cmd.cmd == 'C':
            last_cp_x, last_cp_y = a[2], a[3]  # Second control point
            cx, cy = a[4], a[5]
            result.append(cmd)
        elif cmd.cmd == 'S':
            # Reflect last cubic control point
            if last_cmd in ('C', 'S'):
                rcp_x, rcp_y = _reflect_control_point(last_cp_x, last_cp_y, cx, cy)
            else:
                rcp_x, rcp_y = cx, cy
            last_cp_x, last_cp_y = a[0], a[1]
            new_cx, new_cy = a[2], a[3]
            result.append(PathCommand('C', [rcp_x, rcp_y, a[0], a[1], new_cx, new_cy]))
            cx, cy = new_cx, new_cy
        elif cmd.cmd == 'Q':
            cubic = _quad_to_cubic(a[0], a[1], cx, cy, a[2], a[3])
            last_cp_x, last_cp_y = a[0], a[1]
            result.append(PathCommand('C', cubic))
            cx, cy = a[2], a[3]
        elif cmd.cmd == 'T':
            # Reflect last quadratic control point
            if last_cmd in ('Q', 'T'):
                qp_x, qp_y = _reflect_control_point(last_cp_x, last_cp_y, cx, cy)
            else:
                qp_x, qp_y = cx, cy
            last_cp_x, last_cp_y = qp_x, qp_y
            cubic = _quad_to_cubic(qp_x, qp_y, cx, cy, a[0], a[1])
            result.append(PathCommand('C', cubic))
            cx, cy = a[0], a[1]
        elif cmd.cmd == 'A':
            arc_beziers = _arc_to_cubic_beziers(
                cx, cy, a[0], a[1], a[2], int(a[3]), int(a[4]), a[5], a[6]
            )
            for bc in arc_beziers:
                result.append(bc)
            cx, cy = a[5], a[6]
            last_cp_x, last_cp_y = cx, cy
        elif cmd.cmd == 'Z':
            result.append(cmd)
        else:
            result.append(cmd)

        last_cmd = cmd.cmd

    return result


def path_commands_to_drawingml(commands: List[PathCommand],
                               offset_x: float = 0, offset_y: float = 0,
                               scale_x: float = 1.0, scale_y: float = 1.0) -> Tuple[str, float, float, float, float]:
    """
    Convert normalized path commands to DrawingML <a:path> inner XML.

    Returns: (path_xml, min_x, min_y, width, height) in scaled+offset coordinates.
    """
    if not commands:
        return '', 0, 0, 0, 0

    # First pass: calculate bounding box (applying scale + offset)
    points = []
    for cmd in commands:
        if cmd.cmd == 'M' or cmd.cmd == 'L':
            points.append((cmd.args[0] * scale_x + offset_x,
                           cmd.args[1] * scale_y + offset_y))
        elif cmd.cmd == 'C':
            for i in range(0, 6, 2):
                points.append((cmd.args[i] * scale_x + offset_x,
                               cmd.args[i + 1] * scale_y + offset_y))

    if not points:
        return '', 0, 0, 0, 0

    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)

    width = max(max_x - min_x, 1)
    height = max(max_y - min_y, 1)

    # Second pass: generate DrawingML path commands
    # Coordinates are in EMU, relative to shape's position
    parts = []
    for cmd in commands:
        if cmd.cmd == 'M':
            x_emu = px_to_emu(cmd.args[0] * scale_x + offset_x - min_x)
            y_emu = px_to_emu(cmd.args[1] * scale_y + offset_y - min_y)
            parts.append(f'<a:moveTo><a:pt x="{x_emu}" y="{y_emu}"/></a:moveTo>')
        elif cmd.cmd == 'L':
            x_emu = px_to_emu(cmd.args[0] * scale_x + offset_x - min_x)
            y_emu = px_to_emu(cmd.args[1] * scale_y + offset_y - min_y)
            parts.append(f'<a:lnTo><a:pt x="{x_emu}" y="{y_emu}"/></a:lnTo>')
        elif cmd.cmd == 'C':
            pts = []
            for i in range(0, 6, 2):
                x_emu = px_to_emu(cmd.args[i] * scale_x + offset_x - min_x)
                y_emu = px_to_emu(cmd.args[i + 1] * scale_y + offset_y - min_y)
                pts.append(f'<a:pt x="{x_emu}" y="{y_emu}"/>')
            parts.append(f'<a:cubicBezTo>{"".join(pts)}</a:cubicBezTo>')
        elif cmd.cmd == 'Z':
            parts.append('<a:close/>')

    path_inner = '\n'.join(parts)
    return path_inner, min_x, min_y, width, height


# ---------------------------------------------------------------------------
# Element converters
# ---------------------------------------------------------------------------

def _wrap_shape(shape_id: int, name: str, off_x: int, off_y: int,
                ext_cx: int, ext_cy: int,
                geom_xml: str, fill_xml: str, stroke_xml: str,
                effect_xml: str = '', extra_xml: str = '',
                rot: int = 0) -> str:
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


def convert_rect(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <rect> to DrawingML shape."""
    x = ctx_x(_f(elem.get('x')), ctx)
    y = ctx_y(_f(elem.get('y')), ctx)
    w = ctx_w(_f(elem.get('width')), ctx)
    h = ctx_h(_f(elem.get('height')), ctx)

    if w <= 0 or h <= 0:
        return ''

    fill_op = get_fill_opacity(elem)
    stroke_op = get_stroke_opacity(elem)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, stroke_op)

    # Shadow
    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_shadow_xml(ctx.defs[filt_id])

    geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Rectangle {shape_id}',
        px_to_emu(x), px_to_emu(y), px_to_emu(w), px_to_emu(h),
        geom, fill, stroke, effect
    )


def convert_circle(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <circle> to DrawingML ellipse shape."""
    cx_ = ctx_x(_f(elem.get('cx')), ctx)
    cy_ = ctx_y(_f(elem.get('cy')), ctx)
    r_x = _f(elem.get('r')) * ctx.scale_x
    r_y = _f(elem.get('r')) * ctx.scale_y

    if r_x <= 0 or r_y <= 0:
        return ''

    x = cx_ - r_x
    y = cy_ - r_y
    w = r_x * 2
    h = r_y * 2

    fill_op = get_fill_opacity(elem)
    stroke_op = get_stroke_opacity(elem)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, stroke_op)

    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_shadow_xml(ctx.defs[filt_id])

    geom = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Ellipse {shape_id}',
        px_to_emu(x), px_to_emu(y), px_to_emu(w), px_to_emu(h),
        geom, fill, stroke, effect
    )


def convert_line(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <line> to DrawingML custom geometry shape."""
    x1 = ctx_x(_f(elem.get('x1')), ctx)
    y1 = ctx_y(_f(elem.get('y1')), ctx)
    x2 = ctx_x(_f(elem.get('x2')), ctx)
    y2 = ctx_y(_f(elem.get('y2')), ctx)

    min_x = min(x1, x2)
    min_y = min(y1, y2)
    w = max(abs(x2 - x1), 1)
    h = max(abs(y2 - y1), 1)

    w_emu = px_to_emu(w)
    h_emu = px_to_emu(h)

    lx1 = px_to_emu(x1 - min_x)
    ly1 = px_to_emu(y1 - min_y)
    lx2 = px_to_emu(x2 - min_x)
    ly2 = px_to_emu(y2 - min_y)

    geom = f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
<a:moveTo><a:pt x="{lx1}" y="{ly1}"/></a:moveTo>
<a:lnTo><a:pt x="{lx2}" y="{ly2}"/></a:lnTo>
</a:path></a:pathLst>
</a:custGeom>'''

    stroke_op = get_stroke_opacity(elem)
    stroke = build_stroke_xml(elem, stroke_op)

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Line {shape_id}',
        px_to_emu(min_x), px_to_emu(min_y), w_emu, h_emu,
        geom, '<a:noFill/>', stroke
    )


def convert_path(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <path> to DrawingML custom geometry shape."""
    d = elem.get('d', '')
    if not d:
        return ''

    # Parse, absolutize, normalize
    commands = parse_svg_path(d)
    commands = svg_path_to_absolute(commands)
    commands = normalize_path_commands(commands)

    # Handle transform on the path element itself
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
        ctx.scale_x, ctx.scale_y
    )

    if not path_xml:
        return ''

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    geom = f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    fill_op = get_fill_opacity(elem)
    stroke_op = get_stroke_opacity(elem)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, stroke_op)

    effect = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect = build_shadow_xml(ctx.defs[filt_id])

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Freeform {shape_id}',
        px_to_emu(min_x), px_to_emu(min_y), w_emu, h_emu,
        geom, fill, stroke, effect, rot=rot
    )


def convert_polygon(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <polygon> to DrawingML custom geometry shape."""
    points_str = elem.get('points', '')
    if not points_str:
        return ''

    # Parse points
    nums = re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)', points_str)
    if len(nums) < 4:
        return ''

    points = []
    for i in range(0, len(nums) - 1, 2):
        points.append((float(nums[i]), float(nums[i + 1])))

    # Build path commands
    commands = [PathCommand('M', [points[0][0], points[0][1]])]
    for px_, py_ in points[1:]:
        commands.append(PathCommand('L', [px_, py_]))
    commands.append(PathCommand('Z', []))

    path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
        commands, ctx.translate_x, ctx.translate_y,
        ctx.scale_x, ctx.scale_y
    )

    if not path_xml:
        return ''

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    geom = f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    fill_op = get_fill_opacity(elem)
    stroke_op = get_stroke_opacity(elem)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, stroke_op)

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Polygon {shape_id}',
        px_to_emu(min_x), px_to_emu(min_y), w_emu, h_emu,
        geom, fill, stroke
    )


def convert_polyline(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <polyline> to DrawingML custom geometry shape."""
    points_str = elem.get('points', '')
    if not points_str:
        return ''

    nums = re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)', points_str)
    if len(nums) < 4:
        return ''

    points = []
    for i in range(0, len(nums) - 1, 2):
        points.append((float(nums[i]), float(nums[i + 1])))

    commands = [PathCommand('M', [points[0][0], points[0][1]])]
    for px_, py_ in points[1:]:
        commands.append(PathCommand('L', [px_, py_]))
    # No close for polyline

    path_xml, min_x, min_y, width, height = path_commands_to_drawingml(
        commands, ctx.translate_x, ctx.translate_y,
        ctx.scale_x, ctx.scale_y
    )

    if not path_xml:
        return ''

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    geom = f'''<a:custGeom>
<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>
<a:rect l="l" t="t" r="r" b="b"/>
<a:pathLst><a:path w="{w_emu}" h="{h_emu}">
{path_xml}
</a:path></a:pathLst>
</a:custGeom>'''

    fill_op = get_fill_opacity(elem)
    stroke_op = get_stroke_opacity(elem)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, stroke_op)

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Polyline {shape_id}',
        px_to_emu(min_x), px_to_emu(min_y), w_emu, h_emu,
        geom, '<a:noFill/>', stroke
    )


def convert_text(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <text> to DrawingML text shape."""
    # Get text content (including children like tspan)
    text_content = ''.join(elem.itertext()).strip()
    if not text_content:
        return ''

    x = ctx_x(_f(elem.get('x')), ctx)
    y = ctx_y(_f(elem.get('y')), ctx)
    font_size = _f(elem.get('font-size'), 16) * ctx.scale_y
    font_weight = elem.get('font-weight', '400')
    font_family_str = elem.get('font-family', '')
    text_anchor = elem.get('text-anchor', 'start')
    fill_color = parse_hex_color(elem.get('fill', '#000000')) or '000000'
    opacity = get_fill_opacity(elem)

    fonts = parse_font_family(font_family_str)

    # Estimate text dimensions (generous to avoid clipping)
    text_width = estimate_text_width(text_content, font_size, font_weight) * 1.15
    text_height = font_size * 1.5
    padding = font_size * 0.1

    # Adjust position based on text-anchor
    if text_anchor == 'middle':
        box_x = x - text_width / 2 - padding
    elif text_anchor == 'end':
        box_x = x - text_width - padding
    else:  # start
        box_x = x - padding

    # y in SVG is baseline, move up by ~80% of font size for top of text
    box_y = y - font_size * 0.85

    box_w = text_width + padding * 2
    box_h = text_height + padding

    # DrawingML font size in hundredths of a point
    sz = round(font_size * FONT_PX_TO_HUNDREDTHS_PT)

    # Bold
    b_attr = ' b="1"' if font_weight in ('bold', '600', '700', '800', '900') else ''

    # Italic
    font_style = elem.get('font-style', '')
    i_attr = ' i="1"' if font_style == 'italic' else ''

    # Letter spacing: SVG px -> DrawingML hundredths of a point (spc)
    spc_attr = ''
    letter_spacing = elem.get('letter-spacing')
    if letter_spacing:
        try:
            spc_val = float(letter_spacing) * 100  # px to hundredths of pt (approx)
            spc_attr = f' spc="{int(spc_val)}"'
        except ValueError:
            pass

    # Text rotation (transform="rotate(...)" on text element)
    text_rot = 0
    text_transform = elem.get('transform', '')
    if text_transform:
        rot_match = re.search(r'rotate\(\s*([-\d.]+)', text_transform)
        if rot_match:
            text_rot = int(float(rot_match.group(1)) * ANGLE_UNIT)

    # Alignment
    algn_map = {'start': 'l', 'middle': 'ctr', 'end': 'r'}
    algn = algn_map.get(text_anchor, 'l')

    # Alpha
    alpha_xml = ''
    if opacity is not None and opacity < 1.0:
        alpha_xml = f'<a:alpha val="{int(opacity * 100000)}"/>'

    shape_id = ctx.next_id()
    rot_attr = f' rot="{text_rot}"' if text_rot else ''

    return f'''<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/>
<p:cNvSpPr txBox="1"/><p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm{rot_attr}><a:off x="{px_to_emu(box_x)}" y="{px_to_emu(box_y)}"/>
<a:ext cx="{px_to_emu(box_w)}" cy="{px_to_emu(box_h)}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
<a:noFill/>
<a:ln><a:noFill/></a:ln>
</p:spPr>
<p:txBody>
<a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t" anchorCtr="0">
<a:spAutoFit/>
</a:bodyPr>
<a:lstStyle/>
<a:p>
<a:pPr algn="{algn}"/>
<a:r>
<a:rPr lang="zh-CN" sz="{sz}"{b_attr}{i_attr}{spc_attr} dirty="0">
<a:solidFill><a:srgbClr val="{fill_color}">{alpha_xml}</a:srgbClr></a:solidFill>
<a:latin typeface="{_xml_escape(fonts['latin'])}"/>
<a:ea typeface="{_xml_escape(fonts['ea'])}"/>
<a:cs typeface="{_xml_escape(fonts['latin'])}"/>
</a:rPr>
<a:t>{_xml_escape(text_content)}</a:t>
</a:r>
</a:p>
</p:txBody>
</p:sp>'''


def convert_image(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <image> to DrawingML picture element."""
    href = elem.get('href') or elem.get(f'{{{XLINK_NS}}}href')
    if not href:
        return ''

    x = ctx_x(_f(elem.get('x')), ctx)
    y = ctx_y(_f(elem.get('y')), ctx)
    w = ctx_w(_f(elem.get('width')), ctx)
    h = ctx_h(_f(elem.get('height')), ctx)

    if w <= 0 or h <= 0:
        return ''

    # Extract base64 data
    if href.startswith('data:'):
        # data:image/png;base64,iVBOR...
        match = re.match(r'data:image/(\w+);base64,(.+)', href, re.DOTALL)
        if not match:
            return ''
        img_format = match.group(1).lower()
        if img_format == 'jpeg':
            img_format = 'jpg'
        img_data = base64.b64decode(match.group(2))
    else:
        # External file reference - skip in native mode
        return ''

    # Generate filename and relationship
    img_idx = len(ctx.media_files) + 1
    img_filename = f's{ctx.slide_num}_img{img_idx}.{img_format}'
    ctx.media_files[img_filename] = img_data

    r_id = ctx.next_rel_id()
    ctx.rel_entries.append({
        'id': r_id,
        'type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
        'target': f'../media/{img_filename}',
    })

    shape_id = ctx.next_id()

    return f'''<p:pic>
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
<a:xfrm><a:off x="{px_to_emu(x)}" y="{px_to_emu(y)}"/>
<a:ext cx="{px_to_emu(w)}" cy="{px_to_emu(h)}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
</p:spPr>
</p:pic>'''


def convert_ellipse(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <ellipse> to DrawingML ellipse shape."""
    cx_ = ctx_x(_f(elem.get('cx')), ctx)
    cy_ = ctx_y(_f(elem.get('cy')), ctx)
    rx = _f(elem.get('rx')) * ctx.scale_x
    ry = _f(elem.get('ry')) * ctx.scale_y

    if rx <= 0 or ry <= 0:
        return ''

    x = cx_ - rx
    y = cy_ - ry
    w = rx * 2
    h = ry * 2

    fill_op = get_fill_opacity(elem)
    stroke_op = get_stroke_opacity(elem)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, stroke_op)

    geom = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Ellipse {shape_id}',
        px_to_emu(x), px_to_emu(y), px_to_emu(w), px_to_emu(h),
        geom, fill, stroke
    )


# ---------------------------------------------------------------------------
# Group handling
# ---------------------------------------------------------------------------

def parse_transform(transform_str: str) -> Tuple[float, float, float, float]:
    """Parse transform string, extract translate and scale. Returns (dx, dy, sx, sy)."""
    if not transform_str:
        return 0.0, 0.0, 1.0, 1.0

    dx, dy = 0.0, 0.0
    sx, sy = 1.0, 1.0
    m = re.search(r'translate\(\s*([-\d.]+)[\s,]+([-\d.]+)\s*\)', transform_str)
    if m:
        dx = float(m.group(1))
        dy = float(m.group(2))
    m = re.search(r'scale\(\s*([-\d.]+)(?:[\s,]+([-\d.]+))?\s*\)', transform_str)
    if m:
        sx = float(m.group(1))
        sy = float(m.group(2)) if m.group(2) else sx
    return dx, dy, sx, sy


def convert_g(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <g> by expanding translate and scale into child coordinates."""
    transform = elem.get('transform', '')
    dx, dy, sx, sy = parse_transform(transform)

    # Check for filter on the group
    filter_id = resolve_url_id(elem.get('filter', ''))

    # Check for fill attribute on the group (used by icons)
    group_fill = elem.get('fill')

    child_ctx = ctx.child(dx, dy, sx, sy, filter_id)
    shapes = []

    for child in elem:
        # Propagate group fill to children that don't have their own fill
        if group_fill and not child.get('fill'):
            child.set('fill', group_fill)
        shape_xml = convert_element(child, child_ctx)
        if shape_xml:
            shapes.append(shape_xml)

    ctx.sync_from_child(child_ctx)
    return '\n'.join(shapes)


# ---------------------------------------------------------------------------
# SVG parsing and main dispatch
# ---------------------------------------------------------------------------

def collect_defs(root: ET.Element) -> Dict[str, ET.Element]:
    """Collect all <defs> children into an {id: element} dictionary."""
    defs = {}
    for defs_elem in root.iter(f'{{{SVG_NS}}}defs'):
        for child in defs_elem:
            elem_id = child.get('id')
            if elem_id:
                defs[elem_id] = child
    # Also check for defs without namespace (some SVGs)
    for defs_elem in root.iter('defs'):
        for child in defs_elem:
            elem_id = child.get('id')
            if elem_id:
                defs[elem_id] = child
    return defs


def convert_element(elem: ET.Element, ctx: ConvertContext) -> str:
    """Dispatch SVG element to appropriate converter."""
    tag = elem.tag.replace(f'{{{SVG_NS}}}', '')

    converters = {
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
    }

    converter = converters.get(tag)
    if converter:
        try:
            return converter(elem, ctx)
        except Exception as e:
            print(f'  Warning: Failed to convert <{tag}>: {e}')
            return ''

    # Skip known non-visual elements silently
    if tag in ('defs', 'title', 'desc', 'metadata', 'style'):
        return ''

    return ''


def convert_svg_to_slide_shapes(
    svg_path: Path,
    slide_num: int = 1,
    verbose: bool = False,
) -> Tuple[str, Dict[str, bytes], List[Dict[str, str]]]:
    """
    Convert an SVG file to a complete DrawingML slide XML.

    Args:
        svg_path: Path to the SVG file
        slide_num: Slide number (for naming)
        verbose: Print progress info

    Returns:
        (slide_xml, media_files, rel_entries)
        - slide_xml: Complete slide XML string
        - media_files: Dict of {filename: bytes} for media to write
        - rel_entries: List of relationship entries to add
    """
    tree = ET.parse(str(svg_path))
    root = tree.getroot()

    # Collect defs
    defs = collect_defs(root)

    # Create context
    ctx = ConvertContext(defs=defs, slide_num=slide_num)

    # Convert all top-level elements
    shapes = []
    converted = 0
    skipped = 0

    for child in root:
        tag = child.tag.replace(f'{{{SVG_NS}}}', '')
        if tag == 'defs':
            continue
        result = convert_element(child, ctx)
        if result:
            shapes.append(result)
            converted += 1
        else:
            if tag not in ('title', 'desc', 'metadata', 'style', 'defs'):
                skipped += 1

    if verbose:
        print(f'  Converted {converted} elements, skipped {skipped}')

    shapes_xml = '\n'.join(shapes)

    # Build complete slide XML
    slide_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld>
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

    return slide_xml, ctx.media_files, ctx.rel_entries
