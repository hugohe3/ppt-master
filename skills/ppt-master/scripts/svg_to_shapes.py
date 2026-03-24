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

# SVG attributes that are inheritable from parent <g> to children
INHERITABLE_ATTRS = [
    'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-linecap',
    'opacity', 'fill-opacity', 'stroke-opacity',
    'font-family', 'font-size', 'font-weight', 'font-style',
    'text-anchor', 'letter-spacing',
]

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
    'Songti SC', 'Songti TC',
}
SYSTEM_FONTS = {'system-ui', '-apple-system', 'BlinkMacSystemFont'}

# macOS/Linux-only fonts → Windows equivalents (PPTX targets Windows primarily)
FONT_FALLBACK_WIN = {
    'PingFang SC': 'Microsoft YaHei',
    'PingFang TC': 'Microsoft JhengHei',
    'PingFang HK': 'Microsoft JhengHei',
    'Hiragino Sans': 'Microsoft YaHei',
    'Hiragino Sans GB': 'Microsoft YaHei',
    'Hiragino Mincho ProN': 'SimSun',
    'STHeiti': 'SimHei',
    'STSong': 'SimSun',
    'STKaiti': 'KaiTi',
    'STFangsong': 'FangSong',
    'STXihei': 'Microsoft YaHei',
    'STZhongsong': 'SimSun',
    'Songti SC': 'SimSun',
    'Songti TC': 'SimSun',
    'Noto Sans SC': 'Microsoft YaHei',
    'Noto Sans TC': 'Microsoft JhengHei',
    'Noto Serif SC': 'SimSun',
    'Noto Serif TC': 'SimSun',
    'Source Han Sans SC': 'Microsoft YaHei',
    'Source Han Sans TC': 'Microsoft JhengHei',
    'Source Han Serif SC': 'SimSun',
    'Source Han Serif TC': 'SimSun',
    'WenQuanYi Micro Hei': 'Microsoft YaHei',
    'WenQuanYi Zen Hei': 'Microsoft YaHei',
    # Latin fonts (macOS / Linux / Web → Windows)
    'SF Pro': 'Segoe UI',
    'SF Pro Display': 'Segoe UI',
    'SF Pro Text': 'Segoe UI',
    'SF Mono': 'Consolas',
    'Menlo': 'Consolas',
    'Monaco': 'Consolas',
    'Helvetica Neue': 'Arial',
    'Helvetica': 'Arial',
    'Roboto': 'Segoe UI',
    'Ubuntu': 'Segoe UI',
    'Liberation Sans': 'Arial',
    'Liberation Serif': 'Times New Roman',
    'Liberation Mono': 'Consolas',
    'DejaVu Sans': 'Segoe UI',
    'DejaVu Serif': 'Times New Roman',
    'DejaVu Sans Mono': 'Consolas',
}
# Generic CSS font families → Windows defaults
GENERIC_FONT_MAP = {
    'monospace': 'Consolas',
    'sans-serif': 'Segoe UI',
    'serif': 'Times New Roman',
}
# Serif latin fonts — when these are the latin choice and no EA font is
# specified, prefer SimSun (serif CJK) over Microsoft YaHei (sans-serif CJK).
_SERIF_LATIN = {
    'Times New Roman', 'Georgia', 'Garamond', 'Palatino', 'Palatino Linotype',
    'Book Antiqua', 'Cambria', 'SimSun', 'Liberation Serif', 'DejaVu Serif',
}

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
    svg_dir: Optional[Path] = None  # directory of the source SVG file
    inherited_styles: Dict[str, str] = field(default_factory=dict)

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
              filter_id: Optional[str] = None,
              style_overrides: Optional[Dict[str, str]] = None) -> 'ConvertContext':
        """Create child context with accumulated translation, scale, and styles."""
        merged = dict(self.inherited_styles)
        if style_overrides:
            # Opacity is multiplicative, not override
            for op_key in ('opacity', 'fill-opacity', 'stroke-opacity'):
                if op_key in style_overrides and op_key in merged:
                    try:
                        merged[op_key] = str(float(merged[op_key]) * float(style_overrides[op_key]))
                    except ValueError:
                        merged[op_key] = style_overrides[op_key]
                elif op_key in style_overrides:
                    merged[op_key] = style_overrides[op_key]
            # Other attrs: child overrides parent
            for k, v in style_overrides.items():
                if k not in ('opacity', 'fill-opacity', 'stroke-opacity'):
                    merged[k] = v
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
            svg_dir=self.svg_dir,
            inherited_styles=merged,
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


def _extract_inheritable_styles(elem: ET.Element) -> Dict[str, str]:
    """Extract all SVG-inheritable presentation attributes from an element."""
    styles = {}
    for attr in INHERITABLE_ATTRS:
        val = elem.get(attr)
        if val is not None:
            styles[attr] = val
    return styles


def _get_attr(elem: ET.Element, attr: str, ctx: 'ConvertContext') -> Optional[str]:
    """Get effective attribute: element's own value first, then inherited from context."""
    val = elem.get(attr)
    if val is not None:
        return val
    return ctx.inherited_styles.get(attr)


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
    """Parse CSS font-family to latin/ea typefaces.

    Prioritises Windows-available fonts since PPTX is primarily opened on
    Windows.  macOS/Linux-only fonts are mapped to their Windows equivalents
    via FONT_FALLBACK_WIN.
    """
    if not font_family_str:
        return {'latin': 'Segoe UI', 'ea': 'Microsoft YaHei'}

    fonts = [f.strip().strip("'\"") for f in font_family_str.split(',')]
    latin_font = None
    ea_font = None

    for font in fonts:
        if font in SYSTEM_FONTS:
            continue
        # Resolve generic families
        if font in GENERIC_FONT_MAP:
            resolved = GENERIC_FONT_MAP[font]
            latin_font = latin_font or resolved
            continue
        # Map to Windows equivalent if needed
        win_font = FONT_FALLBACK_WIN.get(font, font)
        if font in EA_FONTS:
            ea_font = ea_font or win_font
        else:
            latin_font = latin_font or win_font

    # If no latin font found but we have EA, use EA as latin too
    # (PPT renders CJK text via latin typeface when ea doesn't match)
    if not latin_font and ea_font:
        latin_font = ea_font

    final_latin = latin_font or 'Segoe UI'

    # EA must always be a CJK-capable font — never fall back to a latin-only
    # font like Arial or Georgia, which would break Chinese/Japanese/Korean text.
    if not ea_font:
        ea_font = 'SimSun' if final_latin in _SERIF_LATIN else 'Microsoft YaHei'

    return {
        'latin': final_latin,
        'ea': ea_font,
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
        # DrawingML lin ang: 0°=left-to-right, 90°=top-to-bottom (clockwise)
        # SVG atan2 with y-down: 0°=left-to-right, 90°=top-to-bottom — same system
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


def build_fill_xml(elem: ET.Element, ctx: ConvertContext,
                   opacity: Optional[float] = None) -> str:
    """Build fill XML for a shape element, with inherited style support."""
    fill = _get_attr(elem, 'fill', ctx)
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


def build_stroke_xml(elem: ET.Element, ctx: ConvertContext,
                     opacity: Optional[float] = None) -> str:
    """Build <a:ln> XML for stroke, with inherited style support."""
    stroke = _get_attr(elem, 'stroke', ctx)
    if not stroke or stroke == 'none':
        return '<a:ln><a:noFill/></a:ln>'

    width = _f(_get_attr(elem, 'stroke-width', ctx), 1.0)
    width_emu = px_to_emu(width)

    # Dash pattern
    dash_xml = ''
    dasharray = _get_attr(elem, 'stroke-dasharray', ctx)
    if dasharray and dasharray != 'none':
        preset = DASH_PRESETS.get(dasharray.strip())
        if preset:
            dash_xml = f'<a:prstDash val="{preset}"/>'
        else:
            dash_xml = '<a:prstDash val="dash"/>'

    # Line cap
    cap_map = {'round': 'rnd', 'square': 'sq', 'butt': 'flat'}
    cap_attr = ''
    linecap = _get_attr(elem, 'stroke-linecap', ctx)
    if linecap and linecap in cap_map:
        cap_attr = f' cap="{cap_map[linecap]}"'

    # Check for gradient stroke
    grad_id = resolve_url_id(stroke)
    if grad_id and grad_id in ctx.defs:
        grad_fill = build_gradient_fill(ctx.defs[grad_id], opacity)
        return f'<a:ln w="{width_emu}"{cap_attr}>{grad_fill}{dash_xml}</a:ln>'

    # Solid color stroke
    color = parse_hex_color(stroke)
    if not color:
        return '<a:ln><a:noFill/></a:ln>'

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


def get_fill_opacity(elem: ET.Element, ctx: Optional[ConvertContext] = None) -> Optional[float]:
    """
    Get effective fill opacity combining 'opacity' and 'fill-opacity',
    including inherited values from context.
    Returns None if fully opaque.
    """
    base = 1.0
    op = _get_attr(elem, 'opacity', ctx) if ctx else elem.get('opacity')
    if op:
        try:
            base = float(op)
        except ValueError:
            pass

    fill_op = _get_attr(elem, 'fill-opacity', ctx) if ctx else elem.get('fill-opacity')
    if fill_op:
        try:
            base *= float(fill_op)
        except ValueError:
            pass

    return base if base < 1.0 else None


def get_stroke_opacity(elem: ET.Element, ctx: Optional[ConvertContext] = None) -> Optional[float]:
    """
    Get effective stroke opacity combining 'opacity' and 'stroke-opacity',
    including inherited values from context.
    Returns None if fully opaque.
    """
    base = 1.0
    op = _get_attr(elem, 'opacity', ctx) if ctx else elem.get('opacity')
    if op:
        try:
            base = float(op)
        except ValueError:
            pass

    stroke_op = _get_attr(elem, 'stroke-opacity', ctx) if ctx else elem.get('stroke-opacity')
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

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

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


def _build_arc_ring_path(cx: float, cy: float, r: float,
                         stroke_width: float,
                         dash_len: float, dash_offset: float,
                         rotate_deg: float,
                         sx: float, sy: float) -> tuple:
    """Build a filled annular-sector (donut segment) as DrawingML custGeom.

    SVG donut charts use stroke-dasharray on a circle to draw arc segments.
    DrawingML cannot reproduce this, so we convert each arc segment into a
    filled ring shape (outer arc → line → inner arc → close).

    Returns (geom_xml, min_x_emu, min_y_emu, w_emu, h_emu).
    """
    circumference = 2 * math.pi * r
    if circumference <= 0:
        return '', 0, 0, 0, 0

    # Arc start/end as fraction of circumference
    start_frac = -dash_offset / circumference
    end_frac = start_frac + dash_len / circumference

    # Convert to angles (radians), starting from top (SVG rotate(-90) is common)
    start_angle = start_frac * 2 * math.pi + math.radians(rotate_deg)
    end_angle = end_frac * 2 * math.pi + math.radians(rotate_deg)

    half_sw = stroke_width / 2
    r_outer = (r + half_sw)
    r_inner = (r - half_sw)

    # Generate points for the arc (use enough segments for smoothness)
    num_segments = max(16, int(abs(end_angle - start_angle) / (math.pi / 32)))
    angles = [start_angle + (end_angle - start_angle) * i / num_segments
              for i in range(num_segments + 1)]

    outer_pts = [(cx + r_outer * math.sin(a), cy - r_outer * math.cos(a)) for a in angles]
    inner_pts = [(cx + r_inner * math.sin(a), cy - r_inner * math.cos(a)) for a in reversed(angles)]

    all_pts = outer_pts + inner_pts

    # Apply scale
    all_pts = [(px * sx, py * sy) for px, py in all_pts]

    # Bounding box
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    min_x = min(xs)
    min_y = min(ys)
    max_x = max(xs)
    max_y = max(ys)
    width = max_x - min_x
    height = max_y - min_y

    if width < 0.5 or height < 0.5:
        return '', 0, 0, 0, 0

    w_emu = px_to_emu(width)
    h_emu = px_to_emu(height)

    # Build path commands (translate to local coordinates)
    lines = []
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
    # Donut segments have large stroke-width relative to radius
    sw = _f(_get_attr(elem, 'stroke-width', ctx), 0)
    r = _f(elem.get('r'), 0)
    if sw <= 0 or r <= 0:
        return False
    # If dasharray doesn't match a standard preset, treat as arc
    if dasharray.strip() in DASH_PRESETS:
        return False
    return True


def convert_circle(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <circle> to DrawingML ellipse shape.

    Detects SVG donut-chart circles (stroke-dasharray arc segments) and
    converts them to filled annular-sector shapes instead.
    """
    cx_ = _f(elem.get('cx'))
    cy_ = _f(elem.get('cy'))
    r = _f(elem.get('r'))

    if r <= 0:
        return ''

    # --- Donut-chart arc segment detection ---
    if _is_donut_circle(elem, ctx):
        dasharray = _get_attr(elem, 'stroke-dasharray', ctx)
        dash_vals = re.split(r'[\s,]+', dasharray.strip())
        dash_len = float(dash_vals[0]) if dash_vals else 0
        dash_offset = _f(elem.get('stroke-dashoffset'), 0)
        stroke_width = _f(_get_attr(elem, 'stroke-width', ctx), 1)

        # Parse rotate transform on the element
        rotate_deg = 0.0
        transform = elem.get('transform', '')
        r_match = re.search(r'rotate\(\s*([-\d.]+)', transform)
        if r_match:
            rotate_deg = float(r_match.group(1))

        geom, min_x, min_y, w_emu, h_emu = _build_arc_ring_path(
            ctx_x(cx_, ctx) / ctx.scale_x,  # pass unscaled center
            ctx_y(cy_, ctx) / ctx.scale_y,
            r, stroke_width, dash_len, dash_offset, rotate_deg,
            ctx.scale_x, ctx.scale_y
        )
        if not geom:
            return ''

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
            effect = build_shadow_xml(ctx.defs[filt_id])

        shape_id = ctx.next_id()
        return _wrap_shape(
            shape_id, f'Arc {shape_id}',
            min_x, min_y, w_emu, h_emu,
            geom, fill, stroke_xml, effect
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

    stroke_op = get_stroke_opacity(elem, ctx)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

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

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

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

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

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

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

    shape_id = ctx.next_id()
    return _wrap_shape(
        shape_id, f'Polyline {shape_id}',
        px_to_emu(min_x), px_to_emu(min_y), w_emu, h_emu,
        geom, '<a:noFill/>', stroke
    )


def _normalize_text(text: str) -> str:
    """Collapse internal whitespace/newlines into a single space, strip ends."""
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text).strip()


def _build_text_runs(elem: ET.Element, parent_attrs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build a list of text runs from a <text> element, handling <tspan> children.

    Each run is a dict with keys: text, fill, fill_raw, font_weight, font_style,
    font_family, font_size.  Child <tspan> attributes override parent defaults.
    """
    runs = []

    # Direct text of <text> element (before first child)
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
                # Override with tspan-specific attributes
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
                runs.append({**run_attrs, 'text': t})

            # Tail text after </tspan> (still belongs to parent)
            if child.tail:
                t = _normalize_text(child.tail)
                if t:
                    runs.append({**parent_attrs, 'text': t})

    return runs


def _build_run_xml(run: Dict[str, Any], default_fonts: Dict[str, str],
                   ctx: Optional[ConvertContext] = None) -> str:
    """Build a single <a:r> XML from a run dict. Supports gradient fills on text."""
    text = run['text']
    fill = run.get('fill', '000000')
    fill_raw = run.get('fill_raw', '')
    fw = run.get('font_weight', '400')
    fs_px = run.get('font_size', 16)
    fstyle = run.get('font_style', '')
    ff = run.get('font_family', '')
    opacity = run.get('opacity')

    sz = round(fs_px * FONT_PX_TO_HUNDREDTHS_PT)
    b_attr = ' b="1"' if fw in ('bold', '600', '700', '800', '900') else ''
    i_attr = ' i="1"' if fstyle == 'italic' else ''

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
<a:rPr lang="zh-CN" sz="{sz}"{b_attr}{i_attr} dirty="0">
{fill_xml}
<a:latin typeface="{_xml_escape(fonts['latin'])}"/>
<a:ea typeface="{_xml_escape(fonts['ea'])}"/>
<a:cs typeface="{_xml_escape(fonts['latin'])}"/>
</a:rPr>
<a:t>{_xml_escape(text)}</a:t>
</a:r>'''


def convert_text(elem: ET.Element, ctx: ConvertContext) -> str:
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

    fonts = parse_font_family(font_family_str)

    # Build runs from <text> + <tspan> children
    parent_attrs = {
        'fill': fill_color,
        'fill_raw': fill_raw,
        'font_weight': font_weight,
        'font_size': font_size,
        'font_family': font_family_str,
        'font_style': font_style,
        'opacity': opacity,
    }
    runs = _build_text_runs(elem, parent_attrs)

    if not runs:
        return ''

    # Combined text for width estimation
    full_text = ''.join(r['text'] for r in runs)
    if not full_text.strip():
        return ''

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

    # Shadow effect from filter
    effect_xml = ''
    filt_id = get_effective_filter_id(elem, ctx)
    if filt_id and filt_id in ctx.defs:
        effect_xml = build_shadow_xml(ctx.defs[filt_id])

    shape_id = ctx.next_id()
    rot_attr = f' rot="{text_rot}"' if text_rot else ''

    # Build runs XML (pass ctx for gradient support)
    runs_xml = '\n'.join(_build_run_xml(r, fonts, ctx) for r in runs)

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

    # Extract image data
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
        # External file reference - resolve relative to SVG directory
        if ctx.svg_dir is None:
            return ''
        img_path = ctx.svg_dir / href
        if not img_path.exists():
            # Also try relative to project root (parent of svg_final/)
            img_path = ctx.svg_dir.parent / href
        if not img_path.exists():
            print(f'  Warning: External image not found: {href}')
            return ''
        img_format = img_path.suffix.lstrip('.').lower()
        if img_format == 'jpeg':
            img_format = 'jpg'
        img_data = img_path.read_bytes()

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

    fill_op = get_fill_opacity(elem, ctx)
    stroke_op = get_stroke_opacity(elem, ctx)
    fill = build_fill_xml(elem, ctx, fill_op)
    stroke = build_stroke_xml(elem, ctx, stroke_op)

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


def _extract_shape_bounds_emu(shape_xml: str) -> Optional[Tuple[int, int, int, int]]:
    """Extract bounds (x, y, x+cx, y+cy) in EMU from a shape XML string.

    Works for <p:sp>, <p:pic>, and <p:grpSp> — the first <a:off> and <a:ext>
    in each is the element's own position/size on the slide.
    """
    off_match = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"', shape_xml)
    ext_match = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', shape_xml)
    if off_match and ext_match:
        x = int(off_match.group(1))
        y = int(off_match.group(2))
        cx = int(ext_match.group(1))
        cy = int(ext_match.group(2))
        return (x, y, x + cx, y + cy)
    return None


def convert_g(elem: ET.Element, ctx: ConvertContext) -> str:
    """Convert SVG <g> to DrawingML group shape <p:grpSp>.

    Preserves group structure so elements can be selected and moved together
    in PowerPoint.  Single-child groups are flattened to avoid unnecessary nesting.

    Uses identity coordinate mapping (chOff/chExt == off/ext) so child shapes
    keep their absolute slide coordinates unchanged.
    """
    transform = elem.get('transform', '')
    dx, dy, sx, sy = parse_transform(transform)

    # Check for filter on the group
    filter_id = resolve_url_id(elem.get('filter', ''))

    # Extract all inheritable styles from this <g>
    style_overrides = _extract_inheritable_styles(elem)

    child_ctx = ctx.child(dx, dy, sx, sy, filter_id, style_overrides)

    # Convert all children
    child_shapes = []
    for child in elem:
        shape_xml = convert_element(child, child_ctx)
        if shape_xml:
            child_shapes.append(shape_xml)

    ctx.sync_from_child(child_ctx)

    if not child_shapes:
        return ''

    # Single child: flatten (no need for group wrapper)
    if len(child_shapes) == 1:
        return child_shapes[0]

    # Multiple children: wrap in <p:grpSp>
    # Calculate group bounds from child shapes (in EMU)
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    for shape_xml in child_shapes:
        bounds = _extract_shape_bounds_emu(shape_xml)
        if bounds:
            min_x = min(min_x, bounds[0])
            min_y = min(min_y, bounds[1])
            max_x = max(max_x, bounds[2])
            max_y = max(max_y, bounds[3])

    if min_x == float('inf'):
        # No shapes with extractable bounds — fall back to flat join
        return '\n'.join(child_shapes)

    group_x = int(min_x)
    group_y = int(min_y)
    group_w = max(int(max_x - min_x), 1)
    group_h = max(int(max_y - min_y), 1)

    shapes_xml = '\n'.join(child_shapes)
    group_id = ctx.next_id()

    # Shadow effect from filter on the group
    group_effect = ''
    if filter_id and filter_id in ctx.defs:
        group_effect = build_shadow_xml(ctx.defs[filter_id])

    # Identity coordinate mapping: chOff/chExt mirrors off/ext
    # so children keep their absolute slide coordinates as-is.
    return f'''<p:grpSp>
<p:nvGrpSpPr>
<p:cNvPr id="{group_id}" name="Group {group_id}"/>
<p:cNvGrpSpPr/>
<p:nvPr/>
</p:nvGrpSpPr>
<p:grpSpPr>
<a:xfrm>
<a:off x="{group_x}" y="{group_y}"/>
<a:ext cx="{group_w}" cy="{group_h}"/>
<a:chOff x="{group_x}" y="{group_y}"/>
<a:chExt cx="{group_w}" cy="{group_h}"/>
</a:xfrm>
{group_effect}
</p:grpSpPr>
{shapes_xml}
</p:grpSp>'''


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
    ctx = ConvertContext(defs=defs, slide_num=slide_num, svg_dir=Path(svg_path).parent)

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
