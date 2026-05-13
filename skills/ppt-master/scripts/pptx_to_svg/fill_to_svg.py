"""DrawingML fill -> SVG fill conversion.

Handles:
- <a:solidFill>     -> fill="#XXXXXX" (+ fill-opacity)
- <a:noFill/>       -> fill="none"
- <a:gradFill>      -> linearGradient/radialGradient in <defs>, fill="url(#id)"
- <a:blipFill>      -> handled by pic_to_svg (this module short-circuits)

Returned FillResult is a struct of attribute dict + optional <defs> XML so the
slide assembler can collect gradient defs without conflicting IDs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from .color_resolver import ColorPalette, find_color_elem, resolve_color
from .emu_units import NS, fmt_num, percent_to_ratio


@dataclass
class FillResult:
    """Resolved fill: SVG attributes to apply + optional <defs> entries."""

    attrs: dict[str, str] = field(default_factory=dict)
    defs: list[str] = field(default_factory=list)  # XML strings of <linearGradient>/<radialGradient>

    @classmethod
    def none_fill(cls) -> "FillResult":
        return cls(attrs={"fill": "none"})

    @classmethod
    def inherit(cls) -> "FillResult":
        # No fill resolved — let caller decide whether to default
        return cls()


def resolve_fill(
    sp_pr: ET.Element | None,
    palette: ColorPalette | None,
    *,
    id_prefix: str = "g",
    id_seq: list[int] | None = None,
    placeholder_hex: str | None = None,
) -> FillResult:
    """Inspect <p:spPr>'s fill children and emit an SVG fill descriptor.

    Args:
        sp_pr: <p:spPr> or any element that may directly hold a fill child.
        palette: ColorPalette for scheme color resolution.
        id_prefix: prefix for generated gradient IDs.
        id_seq: external counter (single-element list) so callers can share
            unique gradient IDs across the whole slide.

    Returns:
        FillResult. If no recognized fill is found, result.attrs is empty —
        the caller should apply its own default (typically transparent /
        inherit from the source SVG).
    """
    if sp_pr is None:
        return FillResult.inherit()

    # Direct child fill (in priority order: explicit -> derived).
    handlers = (
        ("noFill", _resolve_no_fill),
        ("solidFill", _resolve_solid_fill),
        ("gradFill", _resolve_grad_fill),
        ("blipFill", _resolve_blip_fill),
        ("pattFill", _resolve_patt_fill),
    )

    local_name = sp_pr.tag.split("}", 1)[-1] if isinstance(sp_pr.tag, str) else ""
    for tag, handler in handlers:
        if local_name == tag:
            return handler(sp_pr, palette, id_prefix, id_seq, placeholder_hex)

    for tag, handler in handlers:
        elem = sp_pr.find(f"a:{tag}", NS)
        if elem is not None:
            return handler(elem, palette, id_prefix, id_seq, placeholder_hex)

    return FillResult.inherit()


# ---------------------------------------------------------------------------
# Per-fill handlers
# ---------------------------------------------------------------------------

def _resolve_no_fill(_elem, _palette, _prefix, _seq, _placeholder_hex) -> FillResult:
    return FillResult.none_fill()


def _resolve_solid_fill(elem: ET.Element, palette: ColorPalette | None,
                        _prefix: str, _seq, placeholder_hex: str | None) -> FillResult:
    color_elem = find_color_elem(elem)
    hex_, alpha = resolve_color(color_elem, palette, placeholder_hex=placeholder_hex)
    if hex_ is None:
        return FillResult.inherit()
    attrs: dict[str, str] = {"fill": hex_}
    if alpha < 1.0:
        attrs["fill-opacity"] = fmt_num(alpha, 4)
    return FillResult(attrs=attrs)


def _resolve_grad_fill(elem: ET.Element, palette: ColorPalette | None,
                       prefix: str, seq, placeholder_hex: str | None) -> FillResult:
    """Convert <a:gradFill> to an SVG linearGradient or radialGradient."""
    if seq is None:
        seq = [0]
    seq[0] += 1
    grad_id = f"{prefix}grad{seq[0]}"

    # Stops
    gs_lst = elem.find("a:gsLst", NS)
    if gs_lst is None:
        return FillResult.inherit()
    stops_xml = []
    for gs in gs_lst.findall("a:gs", NS):
        pos_pct = percent_to_ratio(gs.attrib.get("pos"), default=0.0)
        color_elem = find_color_elem(gs)
        hex_, alpha = resolve_color(color_elem, palette, placeholder_hex=placeholder_hex)
        if hex_ is None:
            continue
        opacity_attr = f' stop-opacity="{fmt_num(alpha, 4)}"' if alpha < 1.0 else ""
        stops_xml.append(
            f'<stop offset="{fmt_num(pos_pct, 4)}" stop-color="{hex_}"{opacity_attr}/>'
        )
    if not stops_xml:
        return FillResult.inherit()

    # Linear vs radial vs path
    lin = elem.find("a:lin", NS)
    rad = elem.find("a:path", NS)

    if lin is not None:
        # ang is 1/60000 deg. 0° = horizontal left-to-right.
        try:
            angle_deg = float(lin.attrib.get("ang", "0")) / 60000.0
        except ValueError:
            angle_deg = 0.0
        x1, y1, x2, y2 = _angle_to_unit_endpoints(angle_deg)
        defs_xml = (
            f'<linearGradient id="{grad_id}" '
            f'x1="{fmt_num(x1, 4)}" y1="{fmt_num(y1, 4)}" '
            f'x2="{fmt_num(x2, 4)}" y2="{fmt_num(y2, 4)}">'
            + "".join(stops_xml)
            + "</linearGradient>"
        )
    elif rad is not None:
        # Treat as radial regardless of path="circle" / "rect" / "shape" — SVG
        # only has circle/ellipse, and path="circle" maps to fillToRect=center.
        defs_xml = (
            f'<radialGradient id="{grad_id}" cx="0.5" cy="0.5" r="0.5">'
            + "".join(stops_xml)
            + "</radialGradient>"
        )
    else:
        # No direction specified — default to horizontal linear
        defs_xml = (
            f'<linearGradient id="{grad_id}" x1="0" y1="0" x2="1" y2="0">'
            + "".join(stops_xml)
            + "</linearGradient>"
        )

    return FillResult(
        attrs={"fill": f"url(#{grad_id})"},
        defs=[defs_xml],
    )


def _resolve_blip_fill(_elem, _palette, _prefix, _seq, _placeholder_hex) -> FillResult:
    """blipFill on <p:spPr> means a shape filled with an image — handled at
    pic_to_svg level. For now mark as transparent so the shape's outline
    still draws and pic_to_svg can layer the image on top.
    """
    return FillResult.none_fill()


def _resolve_patt_fill(elem: ET.Element, palette: ColorPalette | None,
                       prefix, seq, placeholder_hex: str | None) -> FillResult:
    """Pattern fills (<a:pattFill prst="..."/> with fg/bg colors)."""
    fg = elem.find("a:fgClr", NS)
    bg = elem.find("a:bgClr", NS)
    fg_hex, fg_alpha = resolve_color(
        find_color_elem(fg), palette, placeholder_hex=placeholder_hex,
    )
    bg_hex, bg_alpha = resolve_color(
        find_color_elem(bg), palette, placeholder_hex=placeholder_hex,
    )
    if fg_hex is None:
        return FillResult.inherit()

    prst = elem.attrib.get("prst", "")
    geom = _pattern_foreground(prst, fg_hex, fg_alpha)
    if geom is None:
        # Unsupported preset → degrade to solid fg color so the shape at
        # least carries the right tone. Round-trip will lose the texture.
        attrs: dict[str, str] = {"fill": fg_hex}
        if fg_alpha < 1.0:
            attrs["fill-opacity"] = fmt_num(fg_alpha, 4)
        return FillResult(attrs=attrs)
    tile_w, tile_h, fg_svg = geom

    if seq is None:
        seq = [0]
    seq[0] += 1
    pattern_id = f"{prefix}patt{seq[0]}"
    bg_rect = ""
    if bg_hex is not None:
        bg_opacity = (
            f' fill-opacity="{fmt_num(bg_alpha, 4)}"'
            if bg_alpha < 1.0 else ""
        )
        bg_rect = (
            f'<rect width="{tile_w}" height="{tile_h}" '
            f'fill="{bg_hex}"{bg_opacity}/>'
        )
    # Tag with data attributes so the reverse exporter can rebuild <a:pattFill>
    # faithfully (preset + fg/bg colors) instead of inferring from path geometry.
    bg_attr = f' data-pptx-bg="{bg_hex}"' if bg_hex is not None else ""
    pattern_xml = (
        f'<pattern id="{pattern_id}" patternUnits="userSpaceOnUse" '
        f'width="{tile_w}" height="{tile_h}" '
        f'data-pptx-pattern="{prst}" data-pptx-fg="{fg_hex}"{bg_attr}>'
        f'{bg_rect}{fg_svg}</pattern>'
    )
    return FillResult(
        attrs={"fill": f"url(#{pattern_id})"},
        defs=[pattern_xml],
    )


# ---------------------------------------------------------------------------
# Per-preset SVG geometry for <a:pattFill prst="...">
#
# Each handler returns (tile_w, tile_h, foreground_svg). The caller wraps with
# the background rect + <pattern> element. None means "unsupported preset" and
# the caller degrades to a solid fg color.
# ---------------------------------------------------------------------------

def _pattern_foreground(prst: str, fg: str,
                        fg_alpha: float) -> tuple[int, int, str] | None:
    stroke_op = (
        f' stroke-opacity="{fmt_num(fg_alpha, 4)}"'
        if fg_alpha < 1.0 else ""
    )
    fill_op = (
        f' fill-opacity="{fmt_num(fg_alpha, 4)}"'
        if fg_alpha < 1.0 else ""
    )

    # Diagonal stripes — tile size and stroke width pick the visual weight.
    diag = {
        "ltUpDiag":   (8,  1.0, "up", False),
        "dkUpDiag":   (8,  2.0, "up", False),
        "wdUpDiag":   (16, 1.0, "up", False),
        "dashUpDiag": (8,  1.0, "up", True),
        "ltDnDiag":   (8,  1.0, "dn", False),
        "dkDnDiag":   (8,  2.0, "dn", False),
        "wdDnDiag":   (16, 1.0, "dn", False),
        "dashDnDiag": (8,  1.0, "dn", True),
    }
    if prst in diag:
        tile, sw, direction, dashed = diag[prst]
        dash = ' stroke-dasharray="3 2"' if dashed else ""
        if direction == "up":
            d = f"M -2 {tile} L {tile} -2 M 0 {tile + 2} L {tile + 2} 0"
        else:
            d = f"M -2 0 L {tile} {tile + 2} M 0 -2 L {tile + 2} {tile}"
        return tile, tile, (
            f'<path d="{d}" stroke="{fg}"{stroke_op} '
            f'stroke-width="{fmt_num(sw)}" fill="none"{dash}/>'
        )

    # Horizontal / vertical lines.
    line_specs = {
        "horz":     ("h", 8, 1.0, False),
        "ltHorz":   ("h", 8, 0.5, False),
        "dkHorz":   ("h", 8, 2.0, False),
        "narHorz":  ("h", 4, 1.0, False),
        "dashHorz": ("h", 8, 1.0, True),
        "vert":     ("v", 8, 1.0, False),
        "ltVert":   ("v", 8, 0.5, False),
        "dkVert":   ("v", 8, 2.0, False),
        "narVert":  ("v", 4, 1.0, False),
        "dashVert": ("v", 8, 1.0, True),
    }
    if prst in line_specs:
        axis, tile, sw, dashed = line_specs[prst]
        dash = ' stroke-dasharray="3 2"' if dashed else ""
        mid = tile / 2.0
        if axis == "h":
            line = (
                f'<line x1="0" y1="{fmt_num(mid)}" '
                f'x2="{tile}" y2="{fmt_num(mid)}"'
            )
        else:
            line = (
                f'<line x1="{fmt_num(mid)}" y1="0" '
                f'x2="{fmt_num(mid)}" y2="{tile}"'
            )
        return tile, tile, (
            f'{line} stroke="{fg}"{stroke_op} '
            f'stroke-width="{fmt_num(sw)}"{dash}/>'
        )

    # Grids / crosses.
    if prst == "cross":
        return 8, 8, (
            f'<line x1="0" y1="4" x2="8" y2="4" stroke="{fg}"{stroke_op} stroke-width="1"/>'
            f'<line x1="4" y1="0" x2="4" y2="8" stroke="{fg}"{stroke_op} stroke-width="1"/>'
        )
    if prst == "diagCross":
        d = (
            "M -2 8 L 8 -2 M 0 10 L 10 0 "
            "M -2 0 L 8 10 M 0 -2 L 10 8"
        )
        return 8, 8, (
            f'<path d="{d}" stroke="{fg}"{stroke_op} stroke-width="1" fill="none"/>'
        )
    if prst in ("smGrid", "lgGrid"):
        tile = 4 if prst == "smGrid" else 16
        # Lines along top + left edges; tiles together produce a uniform grid.
        return tile, tile, (
            f'<path d="M 0 0 L {tile} 0 M 0 0 L 0 {tile}" '
            f'stroke="{fg}"{stroke_op} stroke-width="0.5" fill="none"/>'
        )
    if prst == "dotGrid":
        # Dots at corners → tiling yields a uniform dot grid.
        return 8, 8, (
            f'<circle cx="0" cy="0" r="1" fill="{fg}"{fill_op}/>'
        )
    if prst == "dotDmnd":
        return 8, 8, (
            f'<circle cx="0" cy="0" r="1" fill="{fg}"{fill_op}/>'
            f'<circle cx="4" cy="4" r="1" fill="{fg}"{fill_op}/>'
        )

    # Percentage shading — single centered dot whose area matches the target
    # density. Approximates PowerPoint's stipple without per-tile artwork.
    if prst.startswith("pct"):
        try:
            pct = float(prst[3:])
        except ValueError:
            return None
        pct = max(0.0, min(pct, 100.0))
        tile = 8
        radius = math.sqrt(pct / 100.0 * tile * tile / math.pi)
        radius = max(0.3, min(radius, tile / 2.0))
        return tile, tile, (
            f'<circle cx="{tile / 2}" cy="{tile / 2}" '
            f'r="{fmt_num(radius, 3)}" fill="{fg}"{fill_op}/>'
        )

    return None


def _hex_distance(a: str, b: str) -> float:
    """Euclidean distance between two #RRGGBB colors."""
    try:
        ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
        br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    except (ValueError, IndexError):
        return 255.0
    return math.sqrt((ar - br) ** 2 + (ag - bg) ** 2 + (ab - bb) ** 2)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _angle_to_unit_endpoints(angle_deg: float) -> tuple[float, float, float, float]:
    """Convert a DrawingML linear gradient angle to SVG x1/y1/x2/y2 in unit box.

    DrawingML 0° = horizontal pointing right; angle is clockwise.
    SVG default linearGradient is also unit-box (objectBoundingBox).
    """
    rad = math.radians(angle_deg % 360)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    # Center of unit box
    cx, cy = 0.5, 0.5
    # Half-extent in the direction of the angle vector.
    # We project the unit box onto the angle direction; the line endpoints are
    # the projections of the box corners.
    half = abs(cos_a) * 0.5 + abs(sin_a) * 0.5
    x1 = cx - cos_a * half
    y1 = cy - sin_a * half
    x2 = cx + cos_a * half
    y2 = cy + sin_a * half
    return x1, y1, x2, y2
