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
import re
from dataclasses import dataclass, field
from decimal import Decimal
from xml.etree import ElementTree as ET

from .color_resolver import ColorPalette, find_color_elem, resolve_color
from .emu_units import (
    ANGLE_UNIT,
    NS,
    PERCENT_UNIT,
    fmt_num,
    format_ooxml_alpha,
    format_ooxml_unit_ratio,
)


_OOXML_INTEGER_RE = re.compile(r"[+-]?[0-9]+")
_OOXML_PERCENT_LITERAL_RE = re.compile(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)%"
)
_OOXML_FULL_CIRCLE = 360 * ANGLE_UNIT
_OOXML_PERCENTAGE_MIN = Decimal(-(2**31)) / Decimal(PERCENT_UNIT)
_OOXML_PERCENTAGE_MAX = Decimal(2**31 - 1) / Decimal(PERCENT_UNIT)


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
        attrs["fill-opacity"] = format_ooxml_alpha(alpha)
    return FillResult(attrs=attrs)


def _resolve_grad_fill(elem: ET.Element, palette: ColorPalette | None,
                       prefix: str, seq, placeholder_hex: str | None) -> FillResult:
    """Convert <a:gradFill> to an SVG linearGradient or radialGradient."""
    _validate_gradient_attributes(elem)
    _validate_gradient_rotation(elem)
    _validate_gradient_flip(elem)
    _validate_gradient_tile_rect(elem)
    if seq is None:
        seq = [0]
    seq[0] += 1
    grad_id = f"{prefix}grad{seq[0]}"

    # Stops
    gs_lists = elem.findall("a:gsLst", NS)
    if len(gs_lists) != 1:
        raise ValueError(
            "DrawingML gradient fill requires exactly one gsLst"
        )
    gradient_stops = gs_lists[0].findall("a:gs", NS)
    if not gradient_stops:
        raise ValueError(
            "DrawingML gradient fill requires at least one color stop"
        )
    stops_xml = []
    for gs in gradient_stops:
        pos_pct = _gradient_stop_position(gs)
        color_elem = find_color_elem(gs)
        hex_, alpha = resolve_color(
            color_elem,
            palette,
            placeholder_hex=placeholder_hex,
        )
        if hex_ is None:
            raise ValueError(
                "DrawingML gradient stop color cannot be resolved"
            )
        opacity_attr = (
            f' stop-opacity="{format_ooxml_alpha(alpha)}"'
            if alpha < 1.0
            else ""
        )
        stops_xml.append(
            f'<stop offset="{format_ooxml_unit_ratio(pos_pct)}" '
            f'stop-color="{hex_}"{opacity_attr}/>'
        )
    # Linear vs radial vs path
    linear_directions = elem.findall("a:lin", NS)
    path_directions = elem.findall("a:path", NS)
    if len(linear_directions) + len(path_directions) > 1:
        raise ValueError(
            "DrawingML gradient fill must contain at most one lin/path "
            "direction"
        )
    lin = linear_directions[0] if linear_directions else None
    rad = path_directions[0] if path_directions else None

    if lin is not None:
        # ang is 1/60000 deg. 0° = horizontal left-to-right.
        _validate_linear_gradient_structure(lin)
        angle = _linear_gradient_angle(lin)
        _validate_linear_gradient_scaling(lin, angle)
        angle_deg = angle / ANGLE_UNIT
        x1, y1, x2, y2 = _angle_to_unit_endpoints(angle_deg)
        defs_xml = (
            f'<linearGradient id="{grad_id}" '
            f'x1="{fmt_num(x1, 4)}" y1="{fmt_num(y1, 4)}" '
            f'x2="{fmt_num(x2, 4)}" y2="{fmt_num(y2, 4)}">'
            + "".join(stops_xml)
            + "</linearGradient>"
        )
    elif rad is not None:
        _validate_path_gradient_structure(rad)
        _validate_path_gradient_type(rad)
        _validate_path_gradient_focus(rad)
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


def _gradient_stop_position(gs: ET.Element) -> float:
    """Parse one required DrawingML fixed-percentage stop position."""
    raw = gs.get("pos")
    if raw is None:
        raise ValueError("DrawingML gradient stop requires a pos attribute")
    token = raw.strip()
    if _OOXML_INTEGER_RE.fullmatch(token) is None:
        raise ValueError(
            f"Invalid DrawingML gradient stop position: {raw!r}"
        )
    position = int(token)
    if not 0 <= position <= PERCENT_UNIT:
        raise ValueError(
            f"DrawingML gradient stop position={position} is outside "
            f"0..{PERCENT_UNIT}"
        )
    return position / PERCENT_UNIT


def _linear_gradient_angle(lin: ET.Element) -> int:
    """Parse one optional DrawingML positive fixed angle."""
    raw = lin.get("ang")
    if raw is None:
        return 0
    token = raw.strip()
    if _OOXML_INTEGER_RE.fullmatch(token) is None:
        raise ValueError(f"Invalid DrawingML linear gradient angle: {raw!r}")
    angle = int(token)
    if not 0 <= angle < _OOXML_FULL_CIRCLE:
        raise ValueError(
            f"DrawingML linear gradient angle={angle} is outside "
            f"0..{_OOXML_FULL_CIRCLE - 1}"
        )
    return angle


def _validate_linear_gradient_structure(lin: ET.Element) -> None:
    """Require one leaf a:lin with only the registered attributes."""
    unsupported = sorted(set(lin.attrib) - {"ang", "scaled"})
    if unsupported or list(lin) or (lin.text or "").strip():
        details = ", ".join(unsupported) if unsupported else "payload"
        raise ValueError(
            f"Invalid DrawingML linear gradient structure: {details}"
        )


def _validate_linear_gradient_scaling(
    lin: ET.Element,
    angle: int,
) -> None:
    """Require a scaling mode representable by unit-box SVG geometry."""
    scaled = _parse_ooxml_boolean(
        lin.get("scaled"),
        default=False,
        label="linear gradient scaled value",
    )
    quarter_turn = 90 * ANGLE_UNIT
    if not scaled and angle % quarter_turn:
        raise ValueError(
            "Unscaled non-cardinal DrawingML linear gradients are not "
            "representable by the normalized SVG mapping"
        )


def _validate_gradient_rotation(gradient: ET.Element) -> None:
    """Require a gradient that rotates with its containing shape."""
    rotates_with_shape = _parse_ooxml_boolean(
        gradient.get("rotWithShape"),
        default=True,
        label="gradient rotWithShape value",
    )
    if not rotates_with_shape:
        raise ValueError(
            "DrawingML gradients that do not rotate with their shape are "
            "not representable by the local SVG mapping"
        )


def _validate_gradient_attributes(gradient: ET.Element) -> None:
    """Reject attributes outside the registered gradient-fill contract."""
    unsupported = sorted(set(gradient.attrib) - {"flip", "rotWithShape"})
    if unsupported:
        raise ValueError(
            "Unsupported DrawingML gradient fill attribute(s): "
            + ", ".join(unsupported)
        )


def _validate_gradient_flip(gradient: ET.Element) -> None:
    """Reject gradient tile flipping absent from project SVG."""
    flip = gradient.get("flip", "none")
    if flip != "none":
        raise ValueError(f"Unsupported DrawingML gradient flip: {flip!r}")


def _validate_gradient_tile_rect(gradient: ET.Element) -> None:
    """Accept only the full-area gradient tile rectangle."""
    tile_rects = gradient.findall("a:tileRect", NS)
    if len(tile_rects) > 1:
        raise ValueError(
            "DrawingML gradient fill must contain at most one tileRect"
        )
    if not tile_rects:
        return
    values = _relative_rect_values(
        tile_rects[0],
        label="gradient tileRect",
    )
    for value in values.values():
        if value != 0:
            raise ValueError(
                "Non-zero DrawingML gradient tileRect is not representable "
                "by the project SVG gradient mapping"
            )


def _validate_path_gradient_focus(path: ET.Element) -> None:
    """Validate the focus rectangle normalized by the radial approximation."""
    focus_rects = path.findall("a:fillToRect", NS)
    if len(focus_rects) > 1:
        raise ValueError(
            "DrawingML path gradient must contain at most one fillToRect"
        )
    if focus_rects:
        _relative_rect_values(
            focus_rects[0],
            label="path gradient fillToRect",
        )


def _relative_rect_values(
    rect: ET.Element,
    *,
    label: str,
) -> dict[str, Decimal]:
    """Validate one DrawingML relative-rectangle leaf and parse its edges."""
    if (
        set(rect.attrib) - {"l", "t", "r", "b"}
        or list(rect)
        or (rect.text or "").strip()
    ):
        raise ValueError(f"Invalid DrawingML {label} structure")
    return {
        edge: _parse_ooxml_percentage(raw, label=f"{label} {edge}")
        for edge, raw in rect.attrib.items()
    }


def _parse_ooxml_percentage(raw: str, *, label: str) -> Decimal:
    """Parse one DrawingML ST_Percentage as an exact normalized ratio."""
    token = raw.strip()
    if _OOXML_INTEGER_RE.fullmatch(token) is not None:
        value = Decimal(token) / Decimal(PERCENT_UNIT)
    elif _OOXML_PERCENT_LITERAL_RE.fullmatch(token) is not None:
        value = Decimal(token[:-1]) / Decimal(100)
    else:
        raise ValueError(f"Invalid DrawingML {label}: {raw!r}")
    if not _OOXML_PERCENTAGE_MIN <= value <= _OOXML_PERCENTAGE_MAX:
        raise ValueError(f"Invalid DrawingML {label}: {raw!r}")
    return value


def _parse_ooxml_boolean(
    raw: str | None,
    *,
    default: bool,
    label: str,
) -> bool:
    """Parse one W3C XML Schema boolean without permissive aliases."""
    if raw is None:
        return default
    token = raw.strip()
    if token in {"1", "true"}:
        return True
    if token in {"0", "false"}:
        return False
    raise ValueError(f"Invalid DrawingML {label}: {raw!r}")


def _validate_path_gradient_type(path: ET.Element) -> None:
    """Require one registered DrawingML path-shade enum value."""
    path_type = path.get("path", "rect")
    if path_type not in {"circle", "rect", "shape"}:
        raise ValueError(
            f"Unsupported DrawingML path gradient type: {path_type!r}"
        )


def _validate_path_gradient_structure(path: ET.Element) -> None:
    """Require only the registered path attribute and focus rectangle."""
    unsupported = sorted(set(path.attrib) - {"path"})
    children = list(path)
    fill_to_rect_tag = f"{{{NS['a']}}}fillToRect"
    has_invalid_payload = (
        (path.text or "").strip()
        or any(
            child.tag != fill_to_rect_tag or (child.tail or "").strip()
            for child in children
        )
    )
    if unsupported or has_invalid_payload:
        details = ", ".join(unsupported) if unsupported else "payload"
        raise ValueError(
            f"Invalid DrawingML path gradient structure: {details}"
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
            attrs["fill-opacity"] = format_ooxml_alpha(fg_alpha)
        return FillResult(attrs=attrs)
    tile_w, tile_h, fg_svg = geom

    if seq is None:
        seq = [0]
    seq[0] += 1
    pattern_id = f"{prefix}patt{seq[0]}"
    bg_rect = ""
    if bg_hex is not None:
        bg_opacity = (
            f' fill-opacity="{format_ooxml_alpha(bg_alpha)}"'
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
        f' stroke-opacity="{format_ooxml_alpha(fg_alpha)}"'
        if fg_alpha < 1.0 else ""
    )
    fill_op = (
        f' fill-opacity="{format_ooxml_alpha(fg_alpha)}"'
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
