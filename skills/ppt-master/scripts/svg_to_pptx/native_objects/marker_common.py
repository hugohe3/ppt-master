"""Shared helpers for native PowerPoint object conversion."""

from __future__ import annotations

import json
import re
from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.context import ConvertContext, IDENTITY_MATRIX
from ..drawingml.utils import (
    FONT_PX_TO_HUNDREDTHS_PT,
    ctx_h,
    ctx_w,
    ctx_x,
    ctx_y,
    matrix_multiply,
    parse_transform_matrix,
    px_to_emu,
    transform_point,
)

TABLE_URI = "http://schemas.openxmlformats.org/drawingml/2006/table"
CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"
CHARTEX_URI = "http://schemas.microsoft.com/office/drawing/2014/chartex"
CHART_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
CHARTEX_REL_TYPE = "http://schemas.microsoft.com/office/2014/relationships/chartEx"
CHART_COLOR_STYLE_REL_TYPE = "http://schemas.microsoft.com/office/2011/relationships/chartColorStyle"
CHART_STYLE_REL_TYPE = "http://schemas.microsoft.com/office/2011/relationships/chartStyle"
PACKAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/package"
CHART_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"
CHARTEX_CONTENT_TYPE = "application/vnd.ms-office.chartex+xml"
CHART_COLOR_STYLE_CONTENT_TYPE = "application/vnd.ms-office.chartcolorstyle+xml"
CHART_STYLE_CONTENT_TYPE = "application/vnd.ms-office.chartstyle+xml"

_NATIVE_KINDS = {"table", "chart"}
_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_RE = re.compile(r"^rgba?\(([^)]+)\)$", re.IGNORECASE)
_POINT_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_CSS_NAMED_COLORS = {
    "aliceblue": "F0F8FF",
    "black": "000000",
    "blue": "0000FF",
    "brown": "A52A2A",
    "cyan": "00FFFF",
    "darkgray": "A9A9A9",
    "darkgrey": "A9A9A9",
    "gold": "FFD700",
    "gray": "808080",
    "green": "008000",
    "grey": "808080",
    "lightgray": "D3D3D3",
    "lightgrey": "D3D3D3",
    "magenta": "FF00FF",
    "navy": "000080",
    "orange": "FFA500",
    "purple": "800080",
    "red": "FF0000",
    "silver": "C0C0C0",
    "transparent": None,
    "white": "FFFFFF",
    "yellow": "FFFF00",
}


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if "}" in elem.tag else elem.tag


def _clean_hex(value: Any, default: str) -> str:
    return _hex_or_none(value) or _hex_or_none(default) or "000000"


def _hex_or_none(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    named = _CSS_NAMED_COLORS.get(raw.lower())
    if named is not None or raw.lower() in _CSS_NAMED_COLORS:
        return named

    match = _HEX_RE.match(raw)
    if match:
        color = match.group(1).upper()
        if len(color) == 3:
            return "".join(channel * 2 for channel in color)
        return color

    match = _RGB_RE.match(raw)
    if not match:
        return None
    parts = [part.strip() for part in match.group(1).split(",")]
    if len(parts) not in {3, 4}:
        return None
    channels: list[int] = []
    for part in parts[:3]:
        try:
            if part.endswith("%"):
                value_float = float(part[:-1]) * 255.0 / 100.0
            else:
                value_float = float(part)
        except ValueError:
            return None
        channels.append(max(0, min(255, int(round(value_float)))))
    return "".join(f"{channel:02X}" for channel in channels)


def _style_attr(elem: ET.Element, name: str) -> str | None:
    if elem.get(name) is not None:
        return elem.get(name)
    style = elem.get("style")
    if not style:
        return None
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip() == name:
            return value.strip()
    return None


def _paint_visible(elem: ET.Element, paint: str) -> bool:
    for name in ("opacity", f"{paint}-opacity"):
        raw = _style_attr(elem, name)
        if raw is None:
            continue
        try:
            if float(raw) <= 0:
                return False
        except ValueError:
            continue
    return True


def _number(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Native PPTX object requires numeric {field_name}") from exc


def _maybe_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bbox_union(
    first: tuple[float, float, float, float] | None,
    second: tuple[float, float, float, float] | None,
) -> tuple[float, float, float, float] | None:
    if first is None:
        return second
    if second is None:
        return first
    return (
        min(first[0], second[0]),
        min(first[1], second[1]),
        max(first[2], second[2]),
        max(first[3], second[3]),
    )


def _bbox_from_points(points: list[tuple[float, float]]) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _apply_matrix_bbox(
    bbox: tuple[float, float, float, float],
    matrix: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bbox
    points = [
        transform_point(matrix, x1, y1),
        transform_point(matrix, x2, y1),
        transform_point(matrix, x2, y2),
        transform_point(matrix, x1, y2),
    ]
    result = _bbox_from_points(points)
    if result is None:
        raise RuntimeError("Native PPTX object fallback bbox inference failed")
    return result


def _points_attr_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    numbers = [float(item) for item in _POINT_RE.findall(value or "")]
    points = [
        (numbers[idx], numbers[idx + 1])
        for idx in range(0, len(numbers) - 1, 2)
    ]
    return _bbox_from_points(points)


def _path_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    tokens = re.findall(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", value or "")
    points: list[tuple[float, float]] = []
    index = 0
    command = ""
    current_x = 0.0
    current_y = 0.0
    subpath_x = 0.0
    subpath_y = 0.0

    def read_number() -> float | None:
        nonlocal index
        if index >= len(tokens) or re.fullmatch(r"[A-Za-z]", tokens[index]):
            return None
        number = float(tokens[index])
        index += 1
        return number

    def add_point(x_value: float, y_value: float, *, relative: bool) -> tuple[float, float]:
        x = current_x + x_value if relative else x_value
        y = current_y + y_value if relative else y_value
        points.append((x, y))
        return x, y

    while index < len(tokens):
        token = tokens[index]
        if re.fullmatch(r"[A-Za-z]", token):
            command = token
            index += 1
        if not command:
            break

        relative = command.islower()
        op = command.upper()
        if op == "Z":
            current_x, current_y = subpath_x, subpath_y
            points.append((current_x, current_y))
            command = ""
            continue

        if op in {"M", "L", "T"}:
            x_raw = read_number()
            y_raw = read_number()
            if x_raw is None or y_raw is None:
                break
            current_x, current_y = add_point(x_raw, y_raw, relative=relative)
            if op == "M":
                subpath_x, subpath_y = current_x, current_y
                command = "l" if relative else "L"
            continue

        if op == "H":
            x_raw = read_number()
            if x_raw is None:
                break
            current_x = current_x + x_raw if relative else x_raw
            points.append((current_x, current_y))
            continue

        if op == "V":
            y_raw = read_number()
            if y_raw is None:
                break
            current_y = current_y + y_raw if relative else y_raw
            points.append((current_x, current_y))
            continue

        if op == "C":
            values = [read_number() for _ in range(6)]
            if any(item is None for item in values):
                break
            for point_idx in range(0, 6, 2):
                current_x, current_y = add_point(
                    values[point_idx],  # type: ignore[arg-type]
                    values[point_idx + 1],  # type: ignore[arg-type]
                    relative=relative,
                )
            continue

        if op in {"S", "Q"}:
            values = [read_number() for _ in range(4)]
            if any(item is None for item in values):
                break
            for point_idx in range(0, 4, 2):
                current_x, current_y = add_point(
                    values[point_idx],  # type: ignore[arg-type]
                    values[point_idx + 1],  # type: ignore[arg-type]
                    relative=relative,
                )
            continue

        if op == "A":
            values = [read_number() for _ in range(7)]
            if any(item is None for item in values):
                break
            current_x, current_y = add_point(
                values[5],  # type: ignore[arg-type]
                values[6],  # type: ignore[arg-type]
                relative=relative,
            )
            continue

        break

    return _bbox_from_points(points)


def _element_local_bbox(elem: ET.Element) -> tuple[float, float, float, float] | None:
    tag = _local_tag(elem)
    if tag == "metadata":
        return None
    if tag in {"defs", "clipPath", "mask", "filter", "style"}:
        return None
    if elem.get("display") == "none" or elem.get("visibility") == "hidden":
        return None

    if tag in {"g", "svg", "a"}:
        bbox = None
        for child in elem:
            bbox = _bbox_union(bbox, _fallback_bbox(child))
        return bbox

    if tag in {"rect", "image", "use"}:
        x = _maybe_number(elem.get("x")) or 0.0
        y = _maybe_number(elem.get("y")) or 0.0
        width = _maybe_number(elem.get("width")) or 0.0
        height = _maybe_number(elem.get("height")) or 0.0
        if width <= 0 or height <= 0:
            return None
        return x, y, x + width, y + height

    if tag == "circle":
        cx = _maybe_number(elem.get("cx")) or 0.0
        cy = _maybe_number(elem.get("cy")) or 0.0
        r = _maybe_number(elem.get("r")) or 0.0
        if r <= 0:
            return None
        return cx - r, cy - r, cx + r, cy + r

    if tag == "ellipse":
        cx = _maybe_number(elem.get("cx")) or 0.0
        cy = _maybe_number(elem.get("cy")) or 0.0
        rx = _maybe_number(elem.get("rx")) or 0.0
        ry = _maybe_number(elem.get("ry")) or 0.0
        if rx <= 0 or ry <= 0:
            return None
        return cx - rx, cy - ry, cx + rx, cy + ry

    if tag == "line":
        points = [
            (_maybe_number(elem.get("x1")) or 0.0, _maybe_number(elem.get("y1")) or 0.0),
            (_maybe_number(elem.get("x2")) or 0.0, _maybe_number(elem.get("y2")) or 0.0),
        ]
        return _bbox_from_points(points)

    if tag in {"polygon", "polyline"}:
        return _points_attr_bbox(elem.get("points"))

    if tag == "path":
        # This intentionally approximates path geometry from command endpoints.
        # Explicit metadata remains the precise path for complex arcs/curves.
        return _path_bbox(elem.get("d"))

    if tag == "text":
        x = _maybe_number(elem.get("x")) or 0.0
        y = _maybe_number(elem.get("y")) or 0.0
        font_size = _maybe_number(elem.get("font-size")) or 16.0
        text = "".join(elem.itertext())
        width = max(len(text), 1) * font_size * 0.55
        height = font_size * 1.25
        return x, y - height * 0.8, x + width, y + height * 0.2

    return None


def _fallback_bbox(
    elem: ET.Element,
    matrix: tuple[float, float, float, float, float, float] = IDENTITY_MATRIX,
) -> tuple[float, float, float, float] | None:
    local_matrix = matrix
    transform = elem.get("transform")
    if transform:
        local_matrix = matrix_multiply(matrix, parse_transform_matrix(transform))

    tag = _local_tag(elem)
    if tag in {"g", "svg", "a"}:
        bbox = None
        for child in elem:
            bbox = _bbox_union(bbox, _fallback_bbox(child, local_matrix))
        return bbox

    local_bbox = _element_local_bbox(elem)
    if local_bbox is None:
        return None
    return _apply_matrix_bbox(local_bbox, local_matrix)


def _inferred_bounds(elem: ET.Element) -> tuple[float, float, float, float] | None:
    bbox = None
    for child in elem:
        bbox = _bbox_union(bbox, _fallback_bbox(child))
    return bbox


def _fallback_fill_candidates(
    elem: ET.Element,
    matrix: tuple[float, float, float, float, float, float] = IDENTITY_MATRIX,
    inherited_fill: str | None = None,
) -> list[tuple[float, str]]:
    tag = _local_tag(elem)
    if tag == "metadata" or tag in {"defs", "clipPath", "mask", "filter", "style"}:
        return []
    if elem.get("display") == "none" or elem.get("visibility") == "hidden":
        return []
    if not _paint_visible(elem, "fill"):
        return []

    local_matrix = matrix
    transform = elem.get("transform")
    if transform:
        local_matrix = matrix_multiply(matrix, parse_transform_matrix(transform))

    fill = _style_attr(elem, "fill")
    next_fill = fill if fill is not None else inherited_fill
    if tag in {"g", "svg", "a"}:
        candidates: list[tuple[float, str]] = []
        for child in elem:
            candidates.extend(_fallback_fill_candidates(child, local_matrix, next_fill))
        return candidates

    if tag != "rect":
        return []
    if not next_fill or next_fill.strip().lower() in {"none", "transparent"}:
        return []
    color = _hex_or_none(next_fill)
    if not color:
        return []
    local_bbox = _element_local_bbox(elem)
    if local_bbox is None:
        return []
    x1, y1, x2, y2 = _apply_matrix_bbox(local_bbox, local_matrix)
    area = max(x2 - x1, 0.0) * max(y2 - y1, 0.0)
    return [(area, color)] if area > 0 else []


def _inferred_chart_background(elem: ET.Element) -> str | None:
    bounds = _inferred_bounds(elem)
    if bounds is None:
        return None
    x1, y1, x2, y2 = bounds
    bounds_area = max(x2 - x1, 0.0) * max(y2 - y1, 0.0)
    if bounds_area <= 0:
        return None

    candidates: list[tuple[float, str]] = []
    for child in elem:
        candidates.extend(_fallback_fill_candidates(child))
    if not candidates:
        return None
    area, color = max(candidates, key=lambda item: item[0])
    # Avoid mistaking a large data bar for a chart background when no panel /
    # plot-area rectangle exists in the fallback drawing.
    return color if area >= bounds_area * 0.25 else None


def _fallback_text_colors(
    elem: ET.Element,
    inherited_fill: str | None = None,
) -> list[str]:
    tag = _local_tag(elem)
    if tag == "metadata" or tag in {"defs", "clipPath", "mask", "filter", "style"}:
        return []
    if elem.get("display") == "none" or elem.get("visibility") == "hidden":
        return []
    if not _paint_visible(elem, "fill"):
        return []

    fill = _style_attr(elem, "fill")
    next_fill = fill if fill is not None else inherited_fill
    colors: list[str] = []
    if tag in {"text", "tspan"} and next_fill:
        color = _hex_or_none(next_fill)
        if color:
            colors.append(color)
    for child in elem:
        colors.extend(_fallback_text_colors(child, next_fill))
    return colors


def _fallback_stroke_colors(
    elem: ET.Element,
    inherited_stroke: str | None = None,
) -> list[str]:
    tag = _local_tag(elem)
    if tag == "metadata" or tag in {"defs", "clipPath", "mask", "filter", "style"}:
        return []
    if elem.get("display") == "none" or elem.get("visibility") == "hidden":
        return []
    if not _paint_visible(elem, "stroke"):
        return []

    stroke = _style_attr(elem, "stroke")
    next_stroke = stroke if stroke is not None else inherited_stroke
    colors: list[str] = []
    if tag in {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect"} and next_stroke:
        color = _hex_or_none(next_stroke)
        if color:
            colors.append(color)
    for child in elem:
        colors.extend(_fallback_stroke_colors(child, next_stroke))
    return colors


def _most_common_color(colors: list[str]) -> str | None:
    if not colors:
        return None
    counts: dict[str, int] = {}
    for color in colors:
        counts[color] = counts.get(color, 0) + 1
    return max(counts.items(), key=lambda item: item[1])[0]


def _relative_luminance(color: str) -> float:
    channels = [int(color[idx:idx + 2], 16) / 255.0 for idx in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722


def _bounds(elem: ET.Element, payload: dict[str, Any], ctx: ConvertContext) -> tuple[int, int, int, int]:
    """Return object bounds as DrawingML EMU tuple."""
    if ctx.use_transform_matrix:
        raise RuntimeError("Native PPTX table/chart markers support translate/scale only")

    raw_x = payload.get("x", elem.get("data-pptx-x"))
    raw_y = payload.get("y", elem.get("data-pptx-y"))
    raw_width = payload.get("width", elem.get("data-pptx-width"))
    raw_height = payload.get("height", elem.get("data-pptx-height"))
    explicit_bounds = all(value is not None for value in (raw_x, raw_y, raw_width, raw_height))
    inferred = None
    if not explicit_bounds:
        inferred = _inferred_bounds(elem)
        if inferred is None:
            raise RuntimeError(
                "Native PPTX object requires x/y/width/height or visible fallback geometry"
            )

    x = _number(raw_x, "x") if raw_x is not None else inferred[0]  # type: ignore[index]
    y = _number(raw_y, "y") if raw_y is not None else inferred[1]  # type: ignore[index]
    width = (
        _number(raw_width, "width")
        if raw_width is not None else inferred[2] - inferred[0]  # type: ignore[index]
    )
    height = (
        _number(raw_height, "height")
        if raw_height is not None else inferred[3] - inferred[1]  # type: ignore[index]
    )
    if width <= 0 or height <= 0:
        raise RuntimeError("Native PPTX object width/height must be positive")

    if explicit_bounds:
        resolved_x = x
        resolved_y = y
        resolved_w = width
        resolved_h = height
    else:
        resolved_x = ctx_x(x, ctx)
        resolved_y = ctx_y(y, ctx)
        resolved_w = ctx_w(width, ctx)
        resolved_h = ctx_h(height, ctx)
    off_x = px_to_emu(resolved_x)
    off_y = px_to_emu(resolved_y)
    ext_cx = px_to_emu(resolved_w)
    ext_cy = px_to_emu(resolved_h)
    return off_x, off_y, ext_cx, ext_cy


def _validate_bounds_inputs(elem: ET.Element, payload: dict[str, Any]) -> None:
    raw_x = payload.get("x", elem.get("data-pptx-x"))
    raw_y = payload.get("y", elem.get("data-pptx-y"))
    raw_width = payload.get("width", elem.get("data-pptx-width"))
    raw_height = payload.get("height", elem.get("data-pptx-height"))
    inferred = None
    if any(value is None for value in (raw_x, raw_y, raw_width, raw_height)):
        inferred = _inferred_bounds(elem)
        if inferred is None:
            raise RuntimeError(
                "Native PPTX object requires x/y/width/height or visible fallback geometry"
            )

    width = (
        _number(raw_width, "width")
        if raw_width is not None else inferred[2] - inferred[0]  # type: ignore[index]
    )
    height = (
        _number(raw_height, "height")
        if raw_height is not None else inferred[3] - inferred[1]  # type: ignore[index]
    )
    if raw_x is not None:
        _number(raw_x, "x")
    if raw_y is not None:
        _number(raw_y, "y")
    if width <= 0 or height <= 0:
        raise RuntimeError("Native PPTX object width/height must be positive")


def _load_payload(elem: ET.Element, kind: str) -> dict[str, Any]:
    raw = elem.get("data-pptx-json") or elem.get("data-pptx-data")
    if raw is None:
        for child in elem:
            if _local_tag(child) != "metadata":
                continue
            metadata_kind = (child.get("data-pptx-native") or child.get("data-pptx-kind") or kind).lower()
            metadata_type = (child.get("type") or "").lower()
            if metadata_kind == kind or metadata_type == "application/json":
                raw = "".join(child.itertext()).strip()
                break

    if not raw:
        raise RuntimeError(f"Native PPTX {kind} marker requires JSON metadata")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Native PPTX {kind} metadata is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Native PPTX {kind} metadata must be a JSON object")
    return payload


def _font_size_hpt(value: Any, default_px: int = 18) -> int:
    try:
        px = float(value)
    except (TypeError, ValueError):
        px = float(default_px)
    return int(round(px * FONT_PX_TO_HUNDREDTHS_PT / 10.0)) * 10


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _bool_attr(value: bool) -> str:
    return "1" if value else "0"


def _chart_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    key = _compact_key(value)
    if key in {"1", "on", "true", "yes"}:
        return True
    if key in {"0", "false", "no", "off"}:
        return False
    return bool(value)


def _excel_col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result or "A"


def _compact_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())
