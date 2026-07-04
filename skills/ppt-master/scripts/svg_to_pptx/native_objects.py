"""Native PowerPoint table/chart converters for explicit SVG metadata markers."""

from __future__ import annotations

import io
import json
import re
import zipfile
from typing import Any
from xml.etree import ElementTree as ET

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - optional compatibility enhancement
    Workbook = None

from .drawingml_context import ConvertContext, IDENTITY_MATRIX, ShapeResult
from .drawingml_utils import (
    FONT_PX_TO_HUNDREDTHS_PT,
    ctx_h,
    ctx_w,
    ctx_x,
    ctx_y,
    detect_text_lang,
    matrix_multiply,
    parse_transform_matrix,
    px_to_emu,
    transform_point,
    _xml_escape,
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
    inferred = None
    if any(value is None for value in (raw_x, raw_y, raw_width, raw_height)):
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


def _chart_style_value(payload: dict[str, Any], *keys: str) -> Any:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    for source in (payload, style):
        for key in keys:
            if source.get(key) is not None:
                return source.get(key)
    return None


def _chart_style_color(
    payload: dict[str, Any],
    keys: tuple[str, ...],
    default: str | None,
) -> str | None:
    raw = _chart_style_value(payload, *keys)
    if raw is None:
        return default
    if str(raw).strip().lower() in {"none", "transparent"}:
        return None
    return _hex_or_none(raw) or default


def _classic_chart_style(payload: dict[str, Any], elem: ET.Element) -> dict[str, str | None]:
    fallback_background = _inferred_chart_background(elem)
    text_color = _most_common_color(_fallback_text_colors(elem)) or "404040"
    stroke_colors = _fallback_stroke_colors(elem)
    darkest_stroke = min(stroke_colors, key=_relative_luminance) if stroke_colors else None
    lightest_stroke = max(stroke_colors, key=_relative_luminance) if stroke_colors else None
    axis_color = darkest_stroke or text_color
    grid_color = (
        lightest_stroke
        if lightest_stroke and _relative_luminance(lightest_stroke) > _relative_luminance(axis_color)
        else "D9DED8"
    )
    chart_fill = _chart_style_color(
        payload,
        (
            "chart_area_fill",
            "chartAreaFill",
            "chart_fill",
            "chartFill",
            "background",
            "background_color",
            "backgroundColor",
            "fill",
        ),
        fallback_background,
    )
    return {
        "axis_color": _chart_style_color(
            payload,
            ("axis_color", "axisColor", "axis_line_color", "axisLineColor"),
            axis_color,
        ),
        "chart_fill": chart_fill,
        "grid_color": _chart_style_color(
            payload,
            ("grid_color", "gridColor", "gridline_color", "gridlineColor"),
            grid_color,
        ),
        "plot_fill": _chart_style_color(
            payload,
            ("plot_area_fill", "plotAreaFill", "plot_background", "plotBackground"),
            None,
        ),
        "text_color": _chart_style_color(
            payload,
            ("text_color", "textColor", "label_color", "labelColor", "font_color", "fontColor"),
            text_color,
        ),
    }


def _chart_text_sizes(payload: dict[str, Any]) -> dict[str, int]:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    base_raw = _first_present(
        payload.get("font_size"),
        payload.get("chart_font_size"),
        payload.get("chartFontSize"),
        style.get("font_size"),
        style.get("chart_font_size"),
        style.get("chartFontSize"),
    )
    axis_raw = _first_present(
        payload.get("axis_font_size"),
        payload.get("axisFontSize"),
        payload.get("tick_font_size"),
        payload.get("tickFontSize"),
        style.get("axis_font_size"),
        style.get("axisFontSize"),
        style.get("tick_font_size"),
        style.get("tickFontSize"),
        base_raw,
    )
    axis_title_raw = _first_present(
        payload.get("axis_title_font_size"),
        payload.get("axisTitleFontSize"),
        style.get("axis_title_font_size"),
        style.get("axisTitleFontSize"),
        axis_raw,
    )
    legend_raw = _first_present(
        payload.get("legend_font_size"),
        payload.get("legendFontSize"),
        style.get("legend_font_size"),
        style.get("legendFontSize"),
        base_raw,
    )
    title_raw = _first_present(
        payload.get("title_font_size"),
        payload.get("titleFontSize"),
        style.get("title_font_size"),
        style.get("titleFontSize"),
    )
    note_raw = _first_present(
        payload.get("note_font_size"),
        payload.get("noteFontSize"),
        style.get("note_font_size"),
        style.get("noteFontSize"),
        style.get("caption_font_size"),
        style.get("captionFontSize"),
        base_raw,
    )
    return {
        "axis": _font_size_hpt(axis_raw, 12),
        "axis_title": _font_size_hpt(axis_title_raw, 12),
        "base": _font_size_hpt(base_raw, 12),
        "legend": _font_size_hpt(legend_raw, 12),
        "note": _font_size_hpt(note_raw, 12),
        "title": _font_size_hpt(title_raw, 16),
    }


def _solid_fill_xml(color: str | None) -> str:
    if not color:
        return "<a:noFill/>"
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def _chart_area_sp_pr_xml(fill_color: str | None) -> str:
    return f"<c:spPr>{_solid_fill_xml(fill_color)}<a:ln><a:noFill/></a:ln></c:spPr>"


def _chart_line_sp_pr_xml(color: str | None, *, width: int = 9525) -> str:
    if not color:
        line_xml = "<a:ln><a:noFill/></a:ln>"
    else:
        line_xml = (
            f'<a:ln w="{width}" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            "<a:round/></a:ln>"
        )
    return f"<c:spPr>{line_xml}</c:spPr>"


def _major_gridlines_xml(color: str | None) -> str:
    return f'<c:majorGridlines>{_chart_line_sp_pr_xml(color, width=6350)}</c:majorGridlines>'


def _chart_tx_pr_xml(font_size: int, color: str | None = None) -> str:
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    return (
        "<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr>"
        f'<a:defRPr sz="{font_size}">{fill_xml}</a:defRPr>'
        '</a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>'
    )


def _axis_title_xml(title: Any, *, font_size: int, color: str | None = None) -> str:
    if not title:
        return ""
    text = str(title)
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    lang = detect_text_lang(text)
    return (
        "<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:r><a:rPr lang="{lang}" sz="{font_size}">{fill_xml}</a:rPr>'
        f"<a:t>{_xml_escape(text)}</a:t></a:r></a:p>"
        "</c:rich></c:tx><c:layout/><c:overlay val=\"0\"/></c:title>"
    )


def _axis_titles(payload: dict[str, Any]) -> dict[str, Any]:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    raw = payload.get("axis_titles", payload.get("axisTitles"))
    style_raw = style.get("axis_titles", style.get("axisTitles"))
    axis_map = raw if isinstance(raw, dict) else {}
    style_axis_map = style_raw if isinstance(style_raw, dict) else {}

    def pick(axis_keys: tuple[str, ...], root_keys: tuple[str, ...]) -> Any:
        values: list[Any] = []
        for key in root_keys:
            values.extend((
                payload.get(key),
                style.get(key),
            ))
        for key in axis_keys + root_keys:
            values.extend((
                axis_map.get(key),
                style_axis_map.get(key),
            ))
        return _first_present(*values)

    return {
        "category": pick(
            ("category", "cat", "category_axis", "categoryAxis"),
            ("category_axis_title", "categoryAxisTitle"),
        ),
        "value": pick(
            ("value", "val", "value_axis", "valueAxis"),
            ("value_axis_title", "valueAxisTitle"),
        ),
        "x": pick(("x", "x_axis", "xAxis"), ("x_axis_title", "xAxisTitle")),
        "y": pick(("y", "y_axis", "yAxis"), ("y_axis_title", "yAxisTitle")),
        "secondary_value": pick(
            ("secondary_value", "secondaryValue", "secondary_value_axis", "secondaryValueAxis"),
            ("secondary_value_axis_title", "secondaryValueAxisTitle", "right_axis_title", "rightAxisTitle"),
        ),
    }


def _text_box_xml(
    ctx: ConvertContext,
    *,
    text: str,
    role: str,
    off_x: int,
    off_y: int,
    ext_cx: int,
    ext_cy: int,
    font_size: int,
    color: str | None,
    align: str = "l",
    bold: bool = False,
) -> str:
    shape_id = ctx.next_id()
    align_key = _compact_key(align)
    algn = {
        "center": "ctr",
        "centre": "ctr",
        "ctr": "ctr",
        "middle": "ctr",
        "right": "r",
        "r": "r",
        "left": "l",
        "l": "l",
    }.get(align_key, "l")
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    bold_attr = ' b="1"' if bold else ""
    lang = detect_text_lang(text)
    name = _xml_escape(f"Chart {role.title()} {shape_id}")
    return f'''<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvSpPr txBox="1"/><p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
<a:noFill/>
<a:ln><a:noFill/></a:ln>
</p:spPr>
<p:txBody>
<a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t" anchorCtr="0"/>
<a:lstStyle/>
<a:p><a:pPr algn="{algn}"/>
<a:r><a:rPr lang="{lang}" sz="{font_size}"{bold_attr}>{fill_xml}</a:rPr><a:t>{_xml_escape(text)}</a:t></a:r>
</a:p>
</p:txBody>
</p:sp>'''


def _chart_companion_entries(payload: dict[str, Any], *, include_title: bool) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def add(role: str, value: Any) -> None:
        if value is None:
            return
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict):
                text = _first_present(item.get("text"), item.get("value"), item.get("content"))
                if text:
                    entries.append({"role": role, **item, "text": str(text)})
            elif str(item).strip():
                entries.append({"role": role, "text": str(item)})

    if include_title:
        add("title", payload.get("title"))
    add("caption", _first_present(payload.get("caption"), payload.get("subtitle")))
    add("source", _first_present(
        payload.get("source"),
        payload.get("source_note"),
        payload.get("sourceNote"),
    ))
    add("note", _first_present(
        payload.get("note"),
        payload.get("notes"),
        payload.get("footnote"),
        payload.get("footnotes"),
        payload.get("chart_note"),
        payload.get("chartNote"),
        payload.get("chart_notes"),
        payload.get("chartNotes"),
    ))
    return entries


def _chart_companion_text_xml(
    ctx: ConvertContext,
    payload: dict[str, Any],
    *,
    chart_bounds: tuple[int, int, int, int],
    chart_style: dict[str, str | None],
    note_font_size: int,
    title_font_size: int,
    include_title: bool,
) -> str:
    entries = _chart_companion_entries(payload, include_title=include_title)
    if not entries:
        return ""

    chart_off_x, chart_off_y, chart_ext_cx, chart_ext_cy = chart_bounds
    parts: list[str] = []
    below_index = 0
    for item in entries:
        role = str(item.get("role") or "note")
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        font_size = _font_size_hpt(item.get("font_size", item.get("fontSize")), 16 if role == "title" else 12)
        if role == "title" and item.get("font_size") is None and item.get("fontSize") is None:
            font_size = title_font_size
        elif item.get("font_size") is None and item.get("fontSize") is None:
            font_size = note_font_size

        color = _hex_or_none(item.get("color")) or chart_style.get("text_color")
        align = str(item.get("align") or ("ctr" if role == "title" else "l"))
        bold = bool(item.get("bold", role == "title"))
        has_box = all(_maybe_number(item.get(key)) is not None for key in ("x", "y", "width", "height"))
        if has_box:
            off_x = px_to_emu(ctx_x(_number(item["x"], "companion text x"), ctx))
            off_y = px_to_emu(ctx_y(_number(item["y"], "companion text y"), ctx))
            ext_cx = px_to_emu(ctx_w(_number(item["width"], "companion text width"), ctx))
            ext_cy = px_to_emu(ctx_h(_number(item["height"], "companion text height"), ctx))
        elif role == "title":
            off_x = chart_off_x
            off_y = chart_off_y
            ext_cx = chart_ext_cx
            ext_cy = px_to_emu(28)
        else:
            off_x = chart_off_x
            off_y = chart_off_y + chart_ext_cy + px_to_emu(4 + below_index * 18)
            ext_cx = chart_ext_cx
            ext_cy = px_to_emu(16)
            below_index += 1
        parts.append(_text_box_xml(
            ctx,
            text=text,
            role=role,
            off_x=off_x,
            off_y=off_y,
            ext_cx=ext_cx,
            ext_cy=ext_cy,
            font_size=font_size,
            color=color,
            align=align,
            bold=bold,
        ))
    return "".join(parts)


def _bool_attr(value: bool) -> str:
    return "1" if value else "0"


def _table_text_run(
    text: str,
    *,
    color: str,
    bold: bool,
    font_size: int,
    font_face: str | None,
) -> str:
    bold_attr = ' b="1"' if bold else ""
    font_xml = ""
    if font_face:
        clean_font = _xml_escape(font_face)
        font_xml = f'<a:latin typeface="{clean_font}"/><a:ea typeface="{clean_font}"/>'
    return (
        f'<a:r><a:rPr lang="en-US" sz="{font_size}"{bold_attr}>'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'{font_xml}'
        "</a:rPr>"
        f"<a:t>{_xml_escape(text)}</a:t></a:r>"
    )


def _cell_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {"text": "" if value is None else str(value)}


_TABLE_SPAN_KEYS = {
    "col_span",
    "colSpan",
    "grid_span",
    "gridSpan",
    "hMerge",
    "merge",
    "merged",
    "row_span",
    "rowSpan",
    "vMerge",
}
_TABLE_TOP_LEVEL_SPAN_KEYS = {
    "merge_cells",
    "merged_cells",
    "merges",
    "spans",
}


def _table_rows(payload: dict[str, Any]) -> list[list[Any]]:
    columns = payload.get("columns") or []
    rows = payload.get("rows") or []
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise RuntimeError("Native PPTX table requires columns/rows lists")
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, list):
            raise RuntimeError(f"Native PPTX table row {idx} must be a list")

    table_rows = [list(columns)] if columns else []
    table_rows.extend(list(row) for row in rows)
    return table_rows


def _check_table_spans(payload: dict[str, Any], table_rows: list[list[Any]]) -> None:
    for key in _TABLE_TOP_LEVEL_SPAN_KEYS:
        if key in payload:
            raise RuntimeError(
                "Native PPTX table merged cells are not supported; use SVG fallback "
                "or merge cells in PowerPoint after export"
            )
    for row_idx, row in enumerate(table_rows, start=1):
        for col_idx, cell in enumerate(row, start=1):
            if not isinstance(cell, dict):
                continue
            used_keys = sorted(key for key in _TABLE_SPAN_KEYS if key in cell)
            if used_keys:
                keys = ", ".join(used_keys)
                raise RuntimeError(
                    f"Native PPTX table cell R{row_idx}C{col_idx} uses unsupported "
                    f"merged-cell field(s): {keys}"
                )


def _grid_is_strict(payload: dict[str, Any]) -> bool:
    return bool(payload.get("strict_grid", payload.get("strictGrid", False)))


def _validate_table_lengths(payload: dict[str, Any], table_rows: list[list[Any]]) -> int:
    if not table_rows:
        raise RuntimeError("Native PPTX table requires at least one row")
    col_count = max(len(row) for row in table_rows)
    if col_count <= 0:
        raise RuntimeError("Native PPTX table requires at least one column")
    if _grid_is_strict(payload) and any(len(row) != col_count for row in table_rows):
        raise RuntimeError("Native PPTX table strict_grid requires every row to have the same length")

    column_widths = payload.get("column_widths")
    if column_widths is not None:
        if not isinstance(column_widths, list) or len(column_widths) != col_count:
            raise RuntimeError("Native PPTX table column_widths must match the resolved column count")
        for idx, width in enumerate(column_widths, start=1):
            _number(width, f"column_widths[{idx}]")

    row_heights = payload.get("row_heights")
    if row_heights is not None:
        if not isinstance(row_heights, list) or len(row_heights) != len(table_rows):
            raise RuntimeError("Native PPTX table row_heights must match the resolved row count")
        for idx, height in enumerate(row_heights, start=1):
            _number(height, f"row_heights[{idx}]")

    return col_count


def _validate_table_cell_formatting(payload: dict[str, Any], table_rows: list[list[Any]]) -> None:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    for row in table_rows:
        for cell in row:
            cell_data = _cell_payload(cell)
            for side in ("left", "right", "top", "bottom"):
                _table_padding_value(cell_data, style, side)
            _table_border_width(cell_data, style)
            _table_anchor(cell_data, style)


def _validate_table_payload(payload: dict[str, Any]) -> tuple[list[list[Any]], int]:
    table_rows = _table_rows(payload)
    _check_table_spans(payload, table_rows)
    col_count = _validate_table_lengths(payload, table_rows)
    _validate_table_cell_formatting(payload, table_rows)
    return table_rows, col_count


def _normalized_table_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _native_table_metadata_texts(table_rows: list[list[Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in table_rows:
        for cell in row:
            cell_data = _cell_payload(cell)
            text = _normalized_table_text(cell_data.get("text"))
            if text:
                counts[text] = counts.get(text, 0) + 1
    return counts


def _visible_fallback_texts(elem: ET.Element) -> list[str]:
    texts: list[str] = []
    for child in elem.iter():
        tag = _local_tag(child)
        if tag != "text":
            continue
        if child.get("display") == "none" or child.get("visibility") == "hidden":
            continue
        text = _normalized_table_text("".join(child.itertext()))
        if text:
            texts.append(text)
    return texts


def _native_table_warnings(elem: ET.Element, table_rows: list[list[Any]]) -> list[str]:
    fallback_texts = _visible_fallback_texts(elem)
    if not fallback_texts:
        return []
    metadata_counts = _native_table_metadata_texts(table_rows)
    missing: list[str] = []
    seen_counts: dict[str, int] = {}
    for text in fallback_texts:
        seen_counts[text] = seen_counts.get(text, 0) + 1
        if seen_counts[text] > metadata_counts.get(text, 0):
            missing.append(text)
    if not missing:
        return []

    sample = ", ".join(repr(text) for text in missing[:5])
    suffix = "" if len(missing) <= 5 else f", and {len(missing) - 5} more"
    return [
        "Native PPTX table fallback text is missing from metadata columns/rows "
        f"and will disappear with --native-objects: {sample}{suffix}"
    ]


def _weighted_lengths(
    total: int,
    count: int,
    weights: list[Any] | None,
    *,
    field_name: str,
) -> list[int]:
    if weights is None:
        base = max(total // count, 1)
        values = [base] * count
        values[-1] += total - sum(values)
        return values

    numeric = [max(_number(weight, field_name), 0.0) for weight in weights]
    numeric_total = sum(numeric)
    if numeric_total <= 0:
        raise RuntimeError(f"Native PPTX table {field_name} values must sum to a positive number")
    values = [max(round(total * weight / numeric_total), 1) for weight in numeric]
    values[-1] += total - sum(values)
    return values


def _table_padding_value(
    cell_data: dict[str, Any],
    style: dict[str, Any],
    side: str,
) -> int | None:
    side_keys = {
        "left": ("left", "l", "padding_left", "paddingLeft"),
        "right": ("right", "r", "padding_right", "paddingRight"),
        "top": ("top", "t", "padding_top", "paddingTop"),
        "bottom": ("bottom", "b", "padding_bottom", "paddingBottom"),
    }

    def from_source(source: dict[str, Any]) -> Any:
        for key in side_keys[side]:
            if key in source:
                return source[key]
        padding = source.get("padding", source.get("cell_padding"))
        if isinstance(padding, dict):
            for key in side_keys[side]:
                if key in padding:
                    return padding[key]
        elif padding is not None:
            return padding
        return None

    value = from_source(cell_data)
    if value is None:
        value = from_source(style)
    if value is None:
        return None
    return max(px_to_emu(max(_number(value, f"table {side} padding"), 0.0)), 0)


def _table_padding_attrs(cell_data: dict[str, Any], style: dict[str, Any]) -> str:
    attrs = []
    for attr, side in (
        ("marL", "left"),
        ("marR", "right"),
        ("marT", "top"),
        ("marB", "bottom"),
    ):
        value = _table_padding_value(cell_data, style, side)
        if value is not None:
            attrs.append(f'{attr}="{value}"')
    return (" " + " ".join(attrs)) if attrs else ""


def _table_anchor(cell_data: dict[str, Any], style: dict[str, Any]) -> str:
    raw = _first_present(
        cell_data.get("valign"),
        cell_data.get("vertical_align"),
        style.get("valign"),
        style.get("vertical_align"),
        "middle",
    )
    aliases = {
        "bottom": "b",
        "b": "b",
        "center": "ctr",
        "ctr": "ctr",
        "middle": "ctr",
        "top": "t",
        "t": "t",
    }
    anchor = aliases.get(_compact_key(raw))
    if not anchor:
        raise RuntimeError("Native PPTX table valign must be one of: top, middle, bottom")
    return anchor


def _table_border_width(cell_data: dict[str, Any], style: dict[str, Any]) -> float:
    width_raw = cell_data.get("border_width", cell_data.get("borderWidth", style.get("border_width")))
    color_raw = cell_data.get("border_color", cell_data.get("borderColor", style.get("border_color")))
    if width_raw is None and color_raw is None:
        return 0.0
    return _number(1 if width_raw is None else width_raw, "table border_width")


def _table_border_xml(cell_data: dict[str, Any], style: dict[str, Any]) -> str:
    color_raw = cell_data.get("border_color", cell_data.get("borderColor", style.get("border_color")))
    width = _table_border_width(cell_data, style)
    if width <= 0:
        return ""
    color = _clean_hex(color_raw, "#D9DEE7")
    line = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        '<a:prstDash val="solid"/>'
    )
    line_width = max(px_to_emu(width), 1)
    return "".join(
        f'<a:{tag} w="{line_width}">{line}</a:{tag}>'
        for tag in ("lnL", "lnR", "lnT", "lnB")
    )


def _build_native_table(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    table_rows, col_count = _validate_table_payload(payload)
    has_columns = bool(payload.get("columns") or [])
    header_rows = int(payload.get("header_rows", 1 if has_columns else 0))

    for row in table_rows:
        row.extend([""] * (col_count - len(row)))

    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    header_fill = _clean_hex(style.get("header_fill"), "#1F4E79")
    header_text = _clean_hex(style.get("header_text"), "#FFFFFF")
    body_fill = _clean_hex(style.get("body_fill"), "#FFFFFF")
    body_text = _clean_hex(style.get("body_text"), "#1F2937")
    band_fill = _clean_hex(style.get("band_fill"), "#F3F6FA")
    font_face = str(style["font_family"]) if style.get("font_family") else None
    body_font_size = _font_size_hpt(style.get("font_size"), 18)
    header_font_size = _font_size_hpt(
        style.get("header_font_size", style.get("font_size")),
        18,
    )

    off_x, off_y, ext_cx, ext_cy = _bounds(elem, payload, ctx)

    column_widths = payload.get("column_widths")
    grid_widths = _weighted_lengths(
        ext_cx,
        col_count,
        column_widths if isinstance(column_widths, list) else None,
        field_name="column_widths",
    )
    row_heights_raw = payload.get("row_heights")
    row_heights = _weighted_lengths(
        ext_cy,
        len(table_rows),
        row_heights_raw if isinstance(row_heights_raw, list) else None,
        field_name="row_heights",
    )

    grid_xml = "".join(f'<a:gridCol w="{width}"/>' for width in grid_widths)
    rows_xml: list[str] = []
    for row_idx, row in enumerate(table_rows):
        is_header = row_idx < header_rows
        cells_xml: list[str] = []
        for cell in row:
            cell_data = _cell_payload(cell)
            fill = _clean_hex(
                cell_data.get("fill"),
                header_fill if is_header else (band_fill if row_idx % 2 == 0 and row_idx else body_fill),
            )
            color = _clean_hex(cell_data.get("color"), header_text if is_header else body_text)
            align = str(cell_data.get("align") or ("ctr" if is_header else "l"))
            if align not in {"l", "ctr", "r"}:
                align = "l"
            text = "" if cell_data.get("text") is None else str(cell_data.get("text"))
            bold = bool(cell_data.get("bold", is_header))
            cell_font_size = (
                _font_size_hpt(cell_data.get("font_size"), 18)
                if "font_size" in cell_data
                else body_font_size
            )
            if is_header and "font_size" not in cell_data:
                cell_font_size = header_font_size
            paragraph_props = f'<a:pPr algn="{align}"/>' if align != "l" else "<a:pPr/>"
            tc_pr_attrs = (
                f' anchor="{_table_anchor(cell_data, style)}"'
                f'{_table_padding_attrs(cell_data, style)}'
            )
            border_xml = _table_border_xml(cell_data, style)
            cells_xml.append(
                "<a:tc>"
                "<a:txBody><a:bodyPr/><a:lstStyle/>"
                f"<a:p>{paragraph_props}"
                f"{_table_text_run(text, color=color, bold=bold, font_size=cell_font_size, font_face=font_face)}"
                "</a:p></a:txBody>"
                f'<a:tcPr{tc_pr_attrs}>{border_xml}<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill></a:tcPr>'
                "</a:tc>"
            )
        rows_xml.append(f'<a:tr h="{row_heights[row_idx]}">{"".join(cells_xml)}</a:tr>')

    shape_id = ctx.next_id()
    first_row = _bool_attr(header_rows > 0)
    band_row = _bool_attr(bool(style.get("band_row", True)))
    table_style_id = str(style.get("table_style_id") or "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}")
    name = _xml_escape(str(payload.get("name") or elem.get("id") or f"Native Table {shape_id}"))
    xml = f'''<p:graphicFrame>
<p:nvGraphicFramePr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
<p:nvPr/>
</p:nvGraphicFramePr>
<p:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></p:xfrm>
<a:graphic>
<a:graphicData uri="{TABLE_URI}">
<a:tbl>
<a:tblPr firstRow="{first_row}" bandRow="{band_row}">
<a:tableStyleId>{_xml_escape(table_style_id)}</a:tableStyleId>
</a:tblPr>
<a:tblGrid>{grid_xml}</a:tblGrid>
{''.join(rows_xml)}
</a:tbl>
</a:graphicData>
</a:graphic>
</p:graphicFrame>'''
    return ShapeResult(xml=xml, bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))


def _excel_col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result or "A"


def _chart_number(value: Any) -> int | float:
    if isinstance(value, bool):
        raise RuntimeError("Native PPTX chart values must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Native PPTX chart value is not numeric: {value}") from exc
    return int(number) if number.is_integer() else number


def _chart_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError(f"Native PPTX chart {field_name} must be a list")
    return value


_CATEGORY_CHART_TYPES = {
    "area",
    "bar",
    "column",
    "doughnut",
    "line",
    "of_pie",
    "pie",
    "radar",
}
_XY_CHART_TYPES = {"scatter", "bubble"}
_CHARTEX_CHART_TYPES = {
    "box_whisker",
    "funnel",
    "histogram",
    "pareto",
    "sunburst",
    "treemap",
    "waterfall",
}
_DEFERRED_CHART_TYPES = {
    "bullet",
    "gantt",
    "heatmap",
    "map",
}
_UNSUPPORTED_3D_CHART_TYPES = {
    "area3d",
    "bar3d",
    "column3d",
    "line3d",
    "pie3d",
    "surface",
}
_DEFAULT_CHART_COLORS = [
    "4472C4",
    "ED7D31",
    "A5A5A5",
    "FFC000",
    "5B9BD5",
    "70AD47",
    "264478",
    "9E480E",
]


def _compact_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _chart_kind(payload: dict[str, Any]) -> tuple[str, str | None, str | None]:
    raw_type = payload.get("type") or payload.get("chart_type") or "column"
    key = _compact_key(raw_type)
    aliases: dict[str, tuple[str, str | None, str | None]] = {
        "area": ("area", "standard", None),
        "areastacked": ("area", "stacked", None),
        "areastacked100": ("area", "percentStacked", None),
        "area100": ("area", "percentStacked", None),
        "bar": ("bar", "clustered", None),
        "barofpie": ("of_pie", None, "bar"),
        "barclustered": ("bar", "clustered", None),
        "barstacked": ("bar", "stacked", None),
        "barstacked100": ("bar", "percentStacked", None),
        "boxandwhisker": ("box_whisker", None, None),
        "boxplot": ("box_whisker", None, None),
        "boxwhisker": ("box_whisker", None, None),
        "bubble": ("bubble", None, None),
        "bullet": ("bullet", None, None),
        "bulletchart": ("bullet", None, None),
        "combo": ("combo", None, None),
        "combochart": ("combo", None, None),
        "choropleth": ("map", None, None),
        "conebarclustered": ("bar3d", "clustered", "cone"),
        "conebarstacked": ("bar3d", "stacked", "cone"),
        "conebarstacked100": ("bar3d", "percentStacked", "cone"),
        "conecol": ("column3d", "clustered", "cone"),
        "conecolclustered": ("column3d", "clustered", "cone"),
        "conecolstacked": ("column3d", "stacked", "cone"),
        "conecolstacked100": ("column3d", "percentStacked", "cone"),
        "col": ("column", "clustered", None),
        "column": ("column", "clustered", None),
        "columnclustered": ("column", "clustered", None),
        "columnstacked": ("column", "stacked", None),
        "columnstacked100": ("column", "percentStacked", None),
        "contour": ("surface", None, "topView"),
        "contourwireframe": ("surface", None, "topViewWireframe"),
        "cylinderbarclustered": ("bar3d", "clustered", "cylinder"),
        "cylinderbarstacked": ("bar3d", "stacked", "cylinder"),
        "cylinderbarstacked100": ("bar3d", "percentStacked", "cylinder"),
        "cylindercol": ("column3d", "clustered", "cylinder"),
        "cylindercolclustered": ("column3d", "clustered", "cylinder"),
        "cylindercolstacked": ("column3d", "stacked", "cylinder"),
        "cylindercolstacked100": ("column3d", "percentStacked", "cylinder"),
        "doughnut": ("doughnut", None, None),
        "doughnutexploded": ("doughnut", None, "exploded"),
        "donut": ("doughnut", None, None),
        "donutexploded": ("doughnut", None, "exploded"),
        "filledmap": ("map", None, None),
        "funnel": ("funnel", None, None),
        "funnelchart": ("funnel", None, None),
        "gantt": ("gantt", None, None),
        "ganttchart": ("gantt", None, None),
        "geo": ("map", None, None),
        "geomap": ("map", None, None),
        "heatmap": ("heatmap", None, None),
        "heatmapchart": ("heatmap", None, None),
        "histogram": ("histogram", None, None),
        "histogramchart": ("histogram", None, None),
        "line": ("line", "standard", "line"),
        "linemarkers": ("line", "standard", "lineMarker"),
        "linemarkersstacked": ("line", "stacked", "lineMarker"),
        "linemarkersstacked100": ("line", "percentStacked", "lineMarker"),
        "linestacked": ("line", "stacked", "line"),
        "linestacked100": ("line", "percentStacked", "line"),
        "linestackedmarkers": ("line", "stacked", "lineMarker"),
        "linestackedmarkers100": ("line", "percentStacked", "lineMarker"),
        "pie": ("pie", None, None),
        "pieexploded": ("pie", None, "exploded"),
        "ofpie": ("of_pie", None, "pie"),
        "pieofpie": ("of_pie", None, "pie"),
        "pareto": ("pareto", None, None),
        "paretochart": ("pareto", None, None),
        "pyramidbarclustered": ("bar3d", "clustered", "pyramid"),
        "pyramidbarstacked": ("bar3d", "stacked", "pyramid"),
        "pyramidbarstacked100": ("bar3d", "percentStacked", "pyramid"),
        "pyramidcol": ("column3d", "clustered", "pyramid"),
        "pyramidcolclustered": ("column3d", "clustered", "pyramid"),
        "pyramidcolstacked": ("column3d", "stacked", "pyramid"),
        "pyramidcolstacked100": ("column3d", "percentStacked", "pyramid"),
        "radar": ("radar", None, "line"),
        "radarfilled": ("radar", None, "filled"),
        "radarmarkers": ("radar", None, "lineMarker"),
        "scatter": ("scatter", None, "marker"),
        "stock": ("stock", None, "hlc"),
        "stockhlc": ("stock", None, "hlc"),
        "stockohlc": ("stock", None, "ohlc"),
        "stockvhlc": ("stock", None, "vhlc"),
        "stockvohlc": ("stock", None, "vohlc"),
        "surface": ("surface", None, "surface3D"),
        "surface3d": ("surface", None, "surface3D"),
        "surfacewireframe": ("surface", None, "surface3DWireframe"),
        "surfacetopview": ("surface", None, "topView"),
        "surfacetopviewwireframe": ("surface", None, "topViewWireframe"),
        "sunburst": ("sunburst", None, None),
        "sunburstchart": ("sunburst", None, None),
        "map": ("map", None, None),
        "mapchart": ("map", None, None),
        "threedarea": ("area3d", "standard", None),
        "threedareastacked": ("area3d", "stacked", None),
        "threedareastacked100": ("area3d", "percentStacked", None),
        "threedbar": ("bar3d", "clustered", "box"),
        "threedbarclustered": ("bar3d", "clustered", "box"),
        "threedbarstacked": ("bar3d", "stacked", "box"),
        "threedbarstacked100": ("bar3d", "percentStacked", "box"),
        "threedcolumn": ("column3d", "clustered", "box"),
        "threedcolumnclustered": ("column3d", "clustered", "box"),
        "threedcolumnstacked": ("column3d", "stacked", "box"),
        "threedcolumnstacked100": ("column3d", "percentStacked", "box"),
        "threedline": ("line3d", "standard", None),
        "threedpie": ("pie3d", None, None),
        "threedpieexploded": ("pie3d", None, "exploded"),
        "treemap": ("treemap", None, None),
        "treemapchart": ("treemap", None, None),
        "waterfall": ("waterfall", None, None),
        "waterfallchart": ("waterfall", None, None),
        "xy": ("scatter", None, "marker"),
        "xyscatter": ("scatter", None, "marker"),
        "xyscatterlines": ("scatter", None, "lineMarker"),
        "xyscatterlinesnomarkers": ("scatter", None, "line"),
        "xyscattersmooth": ("scatter", None, "smoothMarker"),
        "xyscattersmoothnomarkers": ("scatter", None, "smooth"),
    }
    if key.startswith("100percentstacked"):
        key = key.replace("100percentstacked", "", 1) + "stacked100"
    if key.startswith("percentstacked"):
        key = key.replace("percentstacked", "", 1) + "stacked100"
    if key.startswith("3d"):
        key = "threed" + key[2:]
    chart_type, grouping, style = aliases.get(key, (key, None, None))
    if chart_type in _UNSUPPORTED_3D_CHART_TYPES:
        raise RuntimeError("Native PPTX 3D charts are intentionally unsupported")
    if chart_type in _DEFERRED_CHART_TYPES:
        raise RuntimeError(
            f"Native PPTX {chart_type} chart is outside current basic chart support"
        )

    supported = sorted(_CATEGORY_CHART_TYPES | _XY_CHART_TYPES | _CHARTEX_CHART_TYPES | {"combo", "stock"})
    if chart_type not in supported:
        raise RuntimeError(f"Native PPTX chart type must be one of: {', '.join(supported)}")
    return chart_type, grouping, style


def _chart_grouping(
    chart_type: str,
    payload: dict[str, Any],
    alias_grouping: str | None,
) -> str | None:
    grouping = payload.get("grouping") or payload.get("chart_grouping") or alias_grouping
    if not grouping and payload.get("stacked"):
        grouping = "stacked"
    if not grouping:
        return "clustered" if chart_type in {"bar", "column"} else "standard"

    aliases = {
        "100": "percentStacked",
        "100percent": "percentStacked",
        "100percentstacked": "percentStacked",
        "clustered": "clustered",
        "percent": "percentStacked",
        "percentstacked": "percentStacked",
        "stacked": "stacked",
        "standard": "standard",
    }
    normalized = aliases.get(_compact_key(grouping))
    if chart_type in {"bar", "column"}:
        allowed = {"clustered", "stacked", "percentStacked"}
    elif chart_type in {"area", "line"}:
        allowed = {"standard", "stacked", "percentStacked"}
    else:
        allowed = {"standard"}
    if normalized not in allowed:
        if normalized in {"clustered", "standard"}:
            allowed_text = ", ".join(sorted(allowed))
            raise RuntimeError(f"Native PPTX {chart_type} chart grouping must be one of: {allowed_text}")
        raise RuntimeError(
            f"Native PPTX {grouping} grouping is outside current basic chart support"
        )
    return normalized


def _line_style(payload: dict[str, Any], alias_style: str | None) -> str:
    raw_style = payload.get("line_style") or payload.get("lineStyle") or alias_style
    if raw_style is None:
        raw_style = "lineMarker" if payload.get("markers") else "line"
    aliases = {
        "line": "line",
        "linemarker": "lineMarker",
        "marker": "lineMarker",
        "markers": "lineMarker",
        "none": "line",
        "nomarker": "line",
        "nomarkers": "line",
    }
    style = aliases.get(_compact_key(raw_style))
    if not style:
        raise RuntimeError("Native PPTX line_style must be one of: line, lineMarker")
    return style


def _radar_style(payload: dict[str, Any], alias_style: str | None) -> tuple[str, str | None]:
    raw_style = payload.get("radar_style") or payload.get("radarStyle") or alias_style or "line"
    aliases = {
        "filled": ("filled", None),
        "line": ("marker", "none"),
        "linemarker": ("marker", "circle"),
        "marker": ("marker", "none"),
        "markers": ("marker", "circle"),
        "standard": ("marker", "none"),
    }
    style = aliases.get(_compact_key(raw_style))
    if not style:
        raise RuntimeError(
            f"Native PPTX radar_style {raw_style} is outside current basic chart support"
        )
    return style


def _category_series(payload: dict[str, Any], categories: list[str]) -> list[dict[str, Any]]:
    raw_series = payload.get("series", [])
    if not categories or not isinstance(raw_series, list) or not raw_series:
        raise RuntimeError("Native PPTX chart requires non-empty categories and series")

    series: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_series, start=1):
        if not isinstance(item, dict):
            raise RuntimeError("Native PPTX chart series entries must be objects")
        values = [
            _chart_number(value)
            for value in _chart_list(item.get("values", []), "series[].values")
        ]
        if len(values) != len(categories):
            raise RuntimeError("Native PPTX chart series values must match categories length")
        series.append({"name": str(item.get("name") or f"Series {idx}"), "values": values})
    return series


def _category_chart_data(
    payload: dict[str, Any],
    chart_type: str,
    alias_grouping: str | None,
    alias_style: str | None,
) -> dict[str, Any]:
    categories = [str(item) for item in _chart_list(payload.get("categories", []), "categories")]

    series = _category_series(payload, categories)
    if chart_type in {"doughnut", "of_pie", "pie"}:
        if len(series) != 1:
            raise RuntimeError("Native PPTX pie-family charts support exactly one series")

    of_pie_type = None
    if chart_type == "of_pie":
        raw_of_pie_type = (
            payload.get("of_pie_type")
            or payload.get("ofPieType")
            or payload.get("secondary_type")
            or alias_style
            or "pie"
        )
        of_pie_aliases = {
            "bar": "bar",
            "barofpie": "bar",
            "pie": "pie",
            "pieofpie": "pie",
        }
        of_pie_type = of_pie_aliases.get(_compact_key(raw_of_pie_type))
        if not of_pie_type:
            raise RuntimeError("Native PPTX of_pie_type must be one of: bar, pie")

    line_style = _line_style(payload, alias_style) if chart_type == "line" else None
    radar_style = None
    radar_marker_style = None
    if chart_type == "radar":
        radar_style, radar_marker_style = _radar_style(payload, alias_style)

    if alias_style == "exploded" or payload.get("exploded"):
        raise RuntimeError("Native PPTX exploded pie/doughnut is outside current basic chart support")

    return {
        "kind": "category",
        "type": chart_type,
        "categories": categories,
        "grouping": _chart_grouping(chart_type, payload, alias_grouping)
        if chart_type in {"bar", "column", "line", "area"}
        else None,
        "of_pie_type": of_pie_type,
        "line_style": line_style,
        "radar_marker_style": radar_marker_style,
        "radar_style": radar_style,
        "series": series,
    }


def _combo_axis_name(plot_payload: dict[str, Any]) -> str:
    axis = plot_payload.get("axis") or plot_payload.get("value_axis")
    if axis is None and plot_payload.get("secondary_axis"):
        axis = "secondary"
    axis_key = _compact_key(axis or "primary")
    aliases = {
        "left": "primary",
        "primary": "primary",
        "right": "secondary",
        "secondary": "secondary",
        "secondaryaxis": "secondary",
    }
    normalized = aliases.get(axis_key)
    if not normalized:
        raise RuntimeError("Native PPTX combo plot axis must be primary or secondary")
    return normalized


def _combo_plot_type(plot_payload: dict[str, Any]) -> tuple[str, str | None, str | None]:
    chart_type, alias_grouping, alias_style = _chart_kind(plot_payload)
    if chart_type not in {"area", "column", "line"}:
        raise RuntimeError("Native PPTX combo plots support column, line, and area only")
    return chart_type, alias_grouping, alias_style


def _combo_plot_entry(
    plot_payload: dict[str, Any],
    categories: list[str],
    *,
    fallback_series: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    chart_type, alias_grouping, alias_style = _combo_plot_type(plot_payload)
    plot_series = fallback_series or _category_series(plot_payload, categories)
    entry: dict[str, Any] = {
        "axis": _combo_axis_name(plot_payload),
        "grouping": _chart_grouping(chart_type, plot_payload, alias_grouping)
        if chart_type in {"area", "column", "line"}
        else None,
        "series": plot_series,
        "type": chart_type,
    }
    if chart_type == "line":
        entry["line_style"] = _line_style(plot_payload, alias_style)
    return entry


def _combo_chart_data(payload: dict[str, Any]) -> dict[str, Any]:
    categories = [str(item) for item in _chart_list(payload.get("categories", []), "categories")]
    raw_plots = payload.get("plots", payload.get("chart_plots"))
    plots: list[dict[str, Any]] = []

    if raw_plots is not None:
        for item in _chart_list(raw_plots, "plots"):
            if not isinstance(item, dict):
                raise RuntimeError("Native PPTX combo plots must be objects")
            plots.append(_combo_plot_entry(item, categories))
    else:
        raw_series = _chart_list(payload.get("series", []), "series")
        if not raw_series:
            raise RuntimeError("Native PPTX combo chart requires plots or typed series")
        for idx, item in enumerate(raw_series, start=1):
            if not isinstance(item, dict):
                raise RuntimeError("Native PPTX chart series entries must be objects")
            if not (item.get("type") or item.get("chart_type")):
                raise RuntimeError("Native PPTX combo series entries require type")
            one_series = _category_series({"series": [item]}, categories)
            plot = _combo_plot_entry(item, categories, fallback_series=one_series)
            signature = (
                plot["axis"],
                plot.get("grouping"),
                plot.get("line_style"),
                plot["type"],
            )
            previous = plots[-1] if plots else None
            previous_signature = (
                previous.get("axis"),
                previous.get("grouping"),
                previous.get("line_style"),
                previous.get("type"),
            ) if previous else None
            if previous is not None and signature == previous_signature:
                previous["series"].extend(plot["series"])
            else:
                plots.append(plot)

    if not plots:
        raise RuntimeError("Native PPTX combo chart requires at least one plot")
    flat_series: list[dict[str, Any]] = []
    for plot in plots:
        plot["start_index"] = len(flat_series)
        flat_series.extend(plot["series"])
    if not flat_series:
        raise RuntimeError("Native PPTX combo chart requires at least one series")

    return {
        "categories": categories,
        "kind": "combo",
        "plots": plots,
        "series": flat_series,
        "type": "combo",
    }


def _chart_values(payload: dict[str, Any], field_name: str = "values") -> list[int | float]:
    raw_values = payload.get(field_name)
    if raw_values is None and isinstance(payload.get("series"), list) and payload["series"]:
        first_series = payload["series"][0]
        if isinstance(first_series, dict):
            raw_values = first_series.get("values")
    values = [_chart_number(value) for value in _chart_list(raw_values, field_name)]
    if not values:
        raise RuntimeError(f"Native PPTX chart {field_name} must be a non-empty list")
    return values


def _chart_categories(payload: dict[str, Any], count: int | None = None) -> list[str]:
    raw_categories = payload.get("categories", payload.get("labels", []))
    categories = [str(item) for item in _chart_list(raw_categories, "categories")]
    if count is not None:
        if not categories:
            categories = [f"Category {idx + 1}" for idx in range(count)]
        if len(categories) != count:
            raise RuntimeError("Native PPTX chart categories length must match values length")
    elif not categories:
        raise RuntimeError("Native PPTX chart requires non-empty categories")
    return categories


def _hierarchy_levels(payload: dict[str, Any], count: int) -> list[list[str]]:
    raw_levels = payload.get("levels")
    if raw_levels is not None:
        levels = [
            [str(value) for value in _chart_list(level, "levels[]")]
            for level in _chart_list(raw_levels, "levels")
        ]
    else:
        raw_categories = _chart_list(payload.get("categories", []), "categories")
        if raw_categories and all(isinstance(item, list) for item in raw_categories):
            path_rows = [[str(value) for value in item] for item in raw_categories]
        else:
            path_rows = [[str(item)] for item in raw_categories]
        if len(path_rows) != count:
            raise RuntimeError("Native PPTX hierarchical chart categories length must match values length")
        max_depth = max((len(row) for row in path_rows), default=0)
        levels = [
            [row[depth] if depth < len(row) else "" for row in path_rows]
            for depth in range(max_depth)
        ]

    if not levels:
        raise RuntimeError("Native PPTX hierarchical charts require levels or path categories")
    for level in levels:
        if len(level) != count:
            raise RuntimeError("Native PPTX hierarchical chart levels must match values length")
    return levels


def _treemap_parent_labels(payload: dict[str, Any]) -> str:
    raw = payload.get("parent_label_layout", payload.get("parent_labels", "overlapping"))
    aliases = {
        "banner": "banner",
        "none": "none",
        "overlapping": "overlapping",
    }
    layout = aliases.get(_compact_key(raw))
    if not layout:
        raise RuntimeError(
            "Native PPTX treemap parent_label_layout must be one of: banner, none, overlapping"
        )
    return layout


def _chartex_chart_data(payload: dict[str, Any], chart_type: str) -> dict[str, Any]:
    if chart_type in {"sunburst", "treemap"}:
        values = _chart_values(payload)
        levels = _hierarchy_levels(payload, len(values))
        data = {
            "kind": "chartex",
            "levels": levels,
            "type": chart_type,
            "values": values,
        }
        if chart_type == "treemap":
            data["parent_labels"] = _treemap_parent_labels(payload)
        return data

    if chart_type == "histogram":
        return {
            "kind": "chartex",
            "type": chart_type,
            "values": _chart_values(payload),
        }

    if chart_type in {"funnel", "pareto", "waterfall"}:
        values = _chart_values(payload)
        data = {
            "categories": _chart_categories(payload, len(values)),
            "kind": "chartex",
            "type": chart_type,
            "values": values,
        }
        if chart_type == "waterfall":
            subtotals = payload.get("subtotals", payload.get("subtotal_indices", []))
            data["subtotals"] = [
                int(_chart_number(value))
                for value in _chart_list(subtotals, "subtotals")
            ]
        return data

    if chart_type == "box_whisker":
        raw_series = _chart_list(payload.get("series", []), "series")
        if not raw_series:
            raise RuntimeError("Native PPTX boxWhisker chart requires non-empty series")
        series: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_series, start=1):
            if not isinstance(item, dict):
                raise RuntimeError("Native PPTX chart series entries must be objects")
            values = [_chart_number(value) for value in _chart_list(item.get("values", []), "series[].values")]
            if not values:
                raise RuntimeError("Native PPTX boxWhisker series values must be non-empty")
            categories = item.get("categories")
            if categories is None:
                categories = [str(item.get("name") or f"Series {idx}")] * len(values)
            categories_list = [str(value) for value in _chart_list(categories, "series[].categories")]
            if len(categories_list) != len(values):
                raise RuntimeError("Native PPTX boxWhisker series categories must match values length")
            series.append({
                "categories": categories_list,
                "name": str(item.get("name") or f"Series {idx}"),
                "values": values,
            })
        return {
            "kind": "chartex",
            "series": series,
            "type": chart_type,
        }

    raise RuntimeError(f"Native PPTX {chart_type} chart is outside current basic chart support")


def _stock_chart_data(payload: dict[str, Any]) -> dict[str, Any]:
    categories = [
        _chart_number(item)
        for item in _chart_list(payload.get("categories", payload.get("dates", [])), "categories")
    ]
    if not categories:
        raise RuntimeError("Native PPTX stock chart requires non-empty categories or dates")

    raw_series = payload.get("series")
    if raw_series is None:
        field_names = [("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close")]
        raw_series = [
            {"name": default_name, "values": payload.get(field_name, [])}
            for field_name, default_name in field_names
        ]
    series = _category_series({"series": raw_series}, categories)
    if len(series) != 4:
        raise RuntimeError("Native PPTX stock chart requires exactly four series: open, high, low, close")
    return {
        "categories": categories,
        "kind": "category",
        "series": series,
        "type": "stock",
    }


def _point_values(point: Any, *, chart_type: str) -> tuple[Any, Any, Any | None]:
    if isinstance(point, dict):
        return point.get("x"), point.get("y"), point.get("size", point.get("bubble_size"))
    if isinstance(point, (list, tuple)):
        if len(point) < 2:
            raise RuntimeError("Native PPTX XY chart points require x and y")
        size = point[2] if len(point) > 2 else None
        return point[0], point[1], size
    raise RuntimeError("Native PPTX XY chart points must be objects or arrays")


def _xy_chart_data(
    payload: dict[str, Any],
    chart_type: str,
    alias_style: str | None,
) -> dict[str, Any]:
    raw_series = payload.get("series", [])
    if not isinstance(raw_series, list) or not raw_series:
        raise RuntimeError("Native PPTX XY chart requires non-empty series")

    series: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_series, start=1):
        if not isinstance(item, dict):
            raise RuntimeError("Native PPTX chart series entries must be objects")

        if item.get("points") is not None:
            points = [
                _point_values(point, chart_type=chart_type)
                for point in _chart_list(item.get("points"), "series[].points")
            ]
            x_values = [_chart_number(point[0]) for point in points]
            y_values = [_chart_number(point[1]) for point in points]
            size_values = [_chart_number(point[2]) for point in points if point[2] is not None]
        else:
            x_raw = _chart_list(item.get("x", item.get("xs", [])), "series[].x")
            y_raw = _chart_list(
                item.get("y", item.get("ys", item.get("values", []))),
                "series[].y",
            )
            size_raw = _chart_list(
                item.get("size", item.get("sizes", item.get("bubble_size", []))),
                "series[].size",
            )
            x_values = [_chart_number(value) for value in x_raw]
            y_values = [_chart_number(value) for value in y_raw]
            size_values = [_chart_number(value) for value in size_raw]

        if not x_values or len(x_values) != len(y_values):
            raise RuntimeError("Native PPTX XY chart x/y values must be non-empty and same length")
        if chart_type == "bubble" and len(size_values) != len(x_values):
            raise RuntimeError("Native PPTX bubble chart requires one size per x/y value")

        series.append({
            "name": str(item.get("name") or f"Series {idx}"),
            "sizes": size_values,
            "x": x_values,
            "y": y_values,
        })

    scatter_style = _compact_key(payload.get("scatter_style") or alias_style or "marker")
    style_aliases = {
        "line": "line",
        "linemarker": "lineMarker",
        "markers": "marker",
        "marker": "marker",
        "smooth": "smooth",
        "smoothmarker": "smoothMarker",
    }
    if chart_type == "scatter" and scatter_style not in style_aliases:
        raise RuntimeError("Native PPTX scatter_style is unsupported")
    return {
        "kind": "xy",
        "type": chart_type,
        "scatter_style": style_aliases.get(scatter_style, "marker"),
        "series": series,
    }


def _chart_data(payload: dict[str, Any]) -> dict[str, Any]:
    chart_type, alias_grouping, alias_style = _chart_kind(payload)
    if chart_type == "combo":
        return _combo_chart_data(payload)
    if chart_type in _CHARTEX_CHART_TYPES:
        return _chartex_chart_data(payload, chart_type)
    if chart_type == "stock":
        return _stock_chart_data(payload)
    if chart_type in _XY_CHART_TYPES:
        return _xy_chart_data(payload, chart_type, alias_style)
    return _category_chart_data(payload, chart_type, alias_grouping, alias_style)


def _string_cache(values: list[str]) -> str:
    points = "".join(
        f'<c:pt idx="{idx}"><c:v>{_xml_escape(value)}</c:v></c:pt>'
        for idx, value in enumerate(values)
    )
    return f'<c:strCache><c:ptCount val="{len(values)}"/>{points}</c:strCache>'


def _number_cache(values: list[int | float]) -> str:
    points = "".join(
        f'<c:pt idx="{idx}"><c:v>{value}</c:v></c:pt>'
        for idx, value in enumerate(values)
    )
    return (
        '<c:numCache><c:formatCode>General</c:formatCode>'
        f'<c:ptCount val="{len(values)}"/>{points}</c:numCache>'
    )


def _series_color_xml(color: str | None, *, line: bool = True) -> str:
    if not color:
        return ""
    clean = _clean_hex(color, "#4472C4")
    line_xml = (
        f'<a:ln><a:solidFill><a:srgbClr val="{clean}"/></a:solidFill></a:ln>'
        if line else '<a:ln><a:noFill/></a:ln>'
    )
    return (
        "<c:spPr>"
        f'<a:solidFill><a:srgbClr val="{clean}"/></a:solidFill>'
        f'{line_xml}'
        "</c:spPr>"
    )


def _chart_color(colors: list[str], index: int) -> str:
    if index < len(colors):
        return colors[index]
    return _DEFAULT_CHART_COLORS[index % len(_DEFAULT_CHART_COLORS)]


def _data_point_colors_xml(count: int, colors: list[str]) -> str:
    return "".join(
        f'<c:dPt><c:idx val="{idx}"/>{_series_color_xml(_chart_color(colors, idx))}</c:dPt>'
        for idx in range(count)
    )


def _marker_xml(symbol: str | None) -> str:
    if not symbol:
        return ""
    if symbol == "none":
        return '<c:marker><c:symbol val="none"/></c:marker>'
    return f'<c:marker><c:symbol val="{_xml_escape(symbol)}"/></c:marker>'


def _series_xml(
    categories: list[str],
    series: list[dict[str, Any]],
    *,
    chart_type: str,
    line_style: str = "line",
    radar_marker_style: str | None = None,
    radar_style: str = "marker",
    colors: list[str],
    start_column: int = 2,
    start_index: int = 0,
) -> str:
    parts: list[str] = []
    for offset, item in enumerate(series):
        index = start_index + offset
        column_index = offset + start_column
        color_xml = _series_color_xml(_chart_color(colors, index))
        point_colors_xml = ""
        marker_xml = ""
        smooth_xml = ""
        if chart_type in {"doughnut", "of_pie", "pie"}:
            color_xml = ""
            point_count = (
                len(categories) + 1
                if chart_type == "of_pie"
                else len(categories)
            )
            point_colors_xml = _data_point_colors_xml(point_count, colors)
        if chart_type == "line":
            marker_xml = _marker_xml("circle" if line_style == "lineMarker" else "none")
            smooth_xml = '<c:smooth val="0"/>'
        if chart_type == "radar":
            if radar_style == "filled":
                color_xml = _series_color_xml(_chart_color(colors, index), line=False)
            marker_xml = _marker_xml(radar_marker_style)
        invert_xml = '<c:invertIfNegative val="0"/>' if chart_type in {"bar", "column"} else ""
        parts.append(
            "<c:ser>"
            f'<c:idx val="{index}"/><c:order val="{index}"/>'
            "<c:tx><c:strRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$1</c:f>"
            f"{_string_cache([str(item['name'])])}"
            "</c:strRef></c:tx>"
            f"{color_xml}{invert_xml}{marker_xml}{point_colors_xml}"
            "<c:cat><c:strRef>"
            f"<c:f>Sheet1!$A$2:$A${len(categories) + 1}</c:f>"
            f"{_string_cache(categories)}"
            "</c:strRef></c:cat>"
            "<c:val><c:numRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$2:${_excel_col(column_index)}${len(categories) + 1}</c:f>"
            f"{_number_cache(item['values'])}"
            "</c:numRef></c:val>"
            f"{smooth_xml}"
            "</c:ser>"
        )
    return "".join(parts)


def _chart_title_xml(title: Any, *, font_size: int, color: str | None = None) -> str:
    if not title:
        return '<c:autoTitleDeleted val="1"/>'
    text = _xml_escape(str(title))
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    return (
        "<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:r><a:rPr lang="en-US" sz="{font_size}">{fill_xml}</a:rPr><a:t>{text}</a:t></a:r></a:p>'
        "</c:rich></c:tx><c:layout/></c:title>"
        '<c:autoTitleDeleted val="0"/>'
    )


def _chart_legend_xml(payload: dict[str, Any], *, font_size: int, color: str | None = None) -> str:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    show_legend = payload.get("show_legend", style.get("show_legend", False))
    if not show_legend:
        return ""
    position_key = _compact_key(payload.get("legend_position") or style.get("legend_position") or "bottom")
    positions = {
        "bottom": "b",
        "b": "b",
        "left": "l",
        "l": "l",
        "right": "r",
        "r": "r",
        "top": "t",
        "t": "t",
    }
    position = positions.get(position_key, "b")
    return (
        f'<c:legend><c:legendPos val="{position}"/><c:layout/>'
        '<c:overlay val="0"/>'
        f'{_chart_tx_pr_xml(font_size, color)}'
        '</c:legend>'
    )


def _chart_ex_legend_xml(payload: dict[str, Any]) -> str:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    show_legend = payload.get("show_legend", style.get("show_legend", False))
    if not show_legend:
        return ""
    position_key = _compact_key(payload.get("legend_position") or style.get("legend_position") or "bottom")
    positions = {
        "bottom": "b",
        "b": "b",
        "left": "l",
        "l": "l",
        "right": "r",
        "r": "r",
        "top": "t",
        "t": "t",
    }
    position = positions.get(position_key, "b")
    return f'<cx:legend pos="{position}" align="ctr" overlay="0"/>'


def _scatter_series_style_xml(scatter_style: str, color: str) -> tuple[str, str, str]:
    has_line = scatter_style in {"line", "lineMarker", "smooth", "smoothMarker"}
    has_marker = scatter_style in {"lineMarker", "marker", "smoothMarker"}
    smooth = scatter_style in {"smooth", "smoothMarker"}
    marker_symbol = "circle" if has_marker else "none"
    return (
        _series_color_xml(color, line=has_line),
        f'<c:marker><c:symbol val="{marker_symbol}"/></c:marker>',
        f'<c:smooth val="{_bool_attr(smooth)}"/>',
    )


def _xy_series_xml(
    series: list[dict[str, Any]],
    *,
    chart_type: str,
    colors: list[str],
    scatter_style: str = "lineMarker",
) -> str:
    parts: list[str] = []
    column_stride = 3 if chart_type == "bubble" else 2
    for index, item in enumerate(series):
        x_col = 1 + index * column_stride
        y_col = x_col + 1
        first_row = 2
        last_row = len(item["x"]) + 1
        color = _chart_color(colors, index)
        color_xml = _series_color_xml(color)
        marker_xml = ""
        smooth_xml = ""
        if chart_type == "scatter":
            color_xml, marker_xml, smooth_xml = _scatter_series_style_xml(scatter_style, color)
        invert_xml = '<c:invertIfNegative val="0"/>' if chart_type == "bubble" else ""
        size_xml = ""
        if chart_type == "bubble":
            size_col = x_col + 2
            size_xml = (
                "<c:bubbleSize><c:numRef>"
                f"<c:f>Sheet1!${_excel_col(size_col)}${first_row}:"
                f"${_excel_col(size_col)}${last_row}</c:f>"
                f"{_number_cache(item['sizes'])}"
                "</c:numRef></c:bubbleSize><c:bubble3D val=\"0\"/>"
            )
        parts.append(
            "<c:ser>"
            f'<c:idx val="{index}"/><c:order val="{index}"/>'
            "<c:tx><c:strRef>"
            f"<c:f>Sheet1!${_excel_col(y_col)}$1</c:f>"
            f"{_string_cache([str(item['name'])])}"
            "</c:strRef></c:tx>"
            f"{color_xml}"
            f"{marker_xml}"
            f"{invert_xml}"
            "<c:xVal><c:numRef>"
            f"<c:f>Sheet1!${_excel_col(x_col)}${first_row}:"
            f"${_excel_col(x_col)}${last_row}</c:f>"
            f"{_number_cache(item['x'])}"
            "</c:numRef></c:xVal>"
            "<c:yVal><c:numRef>"
            f"<c:f>Sheet1!${_excel_col(y_col)}${first_row}:"
            f"${_excel_col(y_col)}${last_row}</c:f>"
            f"{_number_cache(item['y'])}"
            "</c:numRef></c:yVal>"
            f"{size_xml}"
            f"{smooth_xml}"
            "</c:ser>"
        )
    return "".join(parts)


def _bar_chart_group_xml(
    chart_type: str,
    grouping: str,
    ser_xml: str,
    *,
    cat_ax_id: str,
    val_ax_id: str,
) -> str:
    bar_dir = "bar" if chart_type == "bar" else "col"
    overlap_xml = (
        '<c:overlap val="100"/>'
        if grouping in {"stacked", "percentStacked"}
        else ""
    )
    return (
        "<c:barChart>"
        f'<c:barDir val="{bar_dir}"/><c:grouping val="{grouping}"/>'
        '<c:varyColors val="0"/>'
        f"{ser_xml}"
        '<c:gapWidth val="150"/>'
        f"{overlap_xml}"
        f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
        "</c:barChart>"
    )


def _line_area_chart_group_xml(
    chart_type: str,
    grouping: str,
    ser_xml: str,
    *,
    cat_ax_id: str,
    val_ax_id: str,
) -> str:
    tag = "lineChart" if chart_type == "line" else "areaChart"
    line_tail_xml = '<c:marker val="1"/><c:smooth val="0"/>' if chart_type == "line" else ""
    return (
        f'<c:{tag}><c:grouping val="{grouping}"/><c:varyColors val="0"/>'
        f"{ser_xml}"
        f"{line_tail_xml}"
        f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
        f"</c:{tag}>"
    )


def _secondary_axis_xml(
    cat_ax_id: str,
    val_ax_id: str,
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
    grouping: str | None = None,
) -> str:
    val_num_fmt = (
        '<c:numFmt formatCode="0%" sourceLinked="0"/>'
        if grouping == "percentStacked"
        else ""
    )
    axis_sp_pr = _chart_line_sp_pr_xml(chart_style.get("axis_color"))
    axis_tx_pr = _chart_tx_pr_xml(axis_font_size, chart_style.get("text_color"))
    val_title_xml = _axis_title_xml(
        axis_titles.get("secondary_value"),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    return (
        "<c:catAx>"
        f'<c:axId val="{cat_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        '<c:delete val="1"/><c:axPos val="b"/><c:majorTickMark val="none"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{val_ax_id}"/><c:crosses val="max"/><c:auto val="1"/>'
        '<c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/>'
        "</c:catAx>"
        "<c:valAx>"
        f'<c:axId val="{val_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="r"/>{val_title_xml}{val_num_fmt}'
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{cat_ax_id}"/><c:crosses val="max"/>'
        "</c:valAx>"
    )


def _combo_axis_grouping(plots: list[dict[str, Any]], axis: str) -> str | None:
    for plot in plots:
        if plot.get("axis") == axis and plot.get("grouping") == "percentStacked":
            return "percentStacked"
    return None


def _combo_plot_xml(
    chart_data: dict[str, Any],
    colors: list[str],
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
) -> str:
    categories = chart_data["categories"]
    primary_cat_ax_id = "2068027336"
    primary_val_ax_id = "2113994440"
    secondary_cat_ax_id = "2080229232"
    secondary_val_ax_id = "2098941040"
    parts: list[str] = []

    for plot in chart_data["plots"]:
        chart_type = plot["type"]
        axis = plot.get("axis", "primary")
        cat_ax_id = secondary_cat_ax_id if axis == "secondary" else primary_cat_ax_id
        val_ax_id = secondary_val_ax_id if axis == "secondary" else primary_val_ax_id
        start_index = int(plot.get("start_index", 0))
        ser_xml = _series_xml(
            categories,
            plot["series"],
            chart_type=chart_type,
            colors=colors,
            line_style=plot.get("line_style", "line"),
            start_column=2 + start_index,
            start_index=start_index,
        )
        grouping = plot.get("grouping") or ("clustered" if chart_type == "column" else "standard")
        if chart_type == "column":
            parts.append(_bar_chart_group_xml(
                chart_type,
                grouping,
                ser_xml,
                cat_ax_id=cat_ax_id,
                val_ax_id=val_ax_id,
            ))
        elif chart_type in {"area", "line"}:
            parts.append(_line_area_chart_group_xml(
                chart_type,
                grouping,
                ser_xml,
                cat_ax_id=cat_ax_id,
                val_ax_id=val_ax_id,
            ))
        else:
            raise RuntimeError("Native PPTX combo plots support column, line, and area only")

    has_secondary_axis = any(plot.get("axis") == "secondary" for plot in chart_data["plots"])
    axes_xml = _axis_xml(
        primary_cat_ax_id,
        primary_val_ax_id,
        axis_font_size=axis_font_size,
        axis_title_font_size=axis_title_font_size,
        axis_titles=axis_titles,
        chart_style=chart_style,
        chart_type="column",
        grouping=_combo_axis_grouping(chart_data["plots"], "primary"),
    )
    if has_secondary_axis:
        axes_xml += _secondary_axis_xml(
            secondary_cat_ax_id,
            secondary_val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            grouping=_combo_axis_grouping(chart_data["plots"], "secondary"),
        )
    return "".join(parts) + axes_xml


def _chart_plot_xml(
    chart_data: dict[str, Any],
    colors: list[str],
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
) -> str:
    chart_type = chart_data["type"]
    cat_ax_id = "2068027336"
    val_ax_id = "2113994440"
    if chart_data["kind"] == "combo":
        return _combo_plot_xml(
            chart_data,
            colors,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
        )
    if chart_data["kind"] == "xy":
        x_ax_id = "2080229232"
        y_ax_id = "2098941040"
        ser_xml = _xy_series_xml(
            chart_data["series"],
            chart_type=chart_type,
            colors=colors,
            scatter_style=chart_data.get("scatter_style", "lineMarker"),
        )
        if chart_type == "scatter":
            scatter_style = chart_data.get("scatter_style", "lineMarker")
            axes_xml = _xy_axis_xml(
                x_ax_id,
                y_ax_id,
                axis_font_size=axis_font_size,
                axis_title_font_size=axis_title_font_size,
                axis_titles=axis_titles,
                chart_style=chart_style,
            )
            return (
                f'<c:scatterChart><c:scatterStyle val="{scatter_style}"/>'
                '<c:varyColors val="0"/>'
                f"{ser_xml}"
                f'<c:axId val="{x_ax_id}"/><c:axId val="{y_ax_id}"/>'
                "</c:scatterChart>"
                f"{axes_xml}"
            )
        axes_xml = _xy_axis_xml(
            x_ax_id,
            y_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
        )
        return (
            '<c:bubbleChart><c:varyColors val="0"/>'
            f"{ser_xml}"
            '<c:bubbleScale val="100"/><c:showNegBubbles val="0"/>'
            f'<c:axId val="{x_ax_id}"/><c:axId val="{y_ax_id}"/>'
            "</c:bubbleChart>"
            f"{axes_xml}"
        )

    categories = chart_data["categories"]
    series = chart_data["series"]
    if chart_type == "stock":
        stock_cat_ax_id = "2068027336"
        stock_val_ax_id = "2113994440"
        axes_xml = _stock_axis_xml(
            stock_cat_ax_id,
            stock_val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
        )
        return (
            "<c:stockChart>"
            f"{_stock_series_xml(categories, series, colors=colors)}"
            '<c:hiLowLines/>'
            '<c:upDownBars><c:gapWidth val="150"/><c:upBars/><c:downBars/></c:upDownBars>'
            f'<c:axId val="{stock_cat_ax_id}"/><c:axId val="{stock_val_ax_id}"/>'
            "</c:stockChart>"
            f"{axes_xml}"
        )
    ser_xml = _series_xml(
        categories,
        series,
        chart_type=chart_type,
        line_style=chart_data.get("line_style", "line"),
        radar_marker_style=chart_data.get("radar_marker_style"),
        radar_style=chart_data.get("radar_style", "marker"),
        colors=colors,
    )

    if chart_type in {"bar", "column"}:
        bar_dir = "bar" if chart_type == "bar" else "col"
        grouping = chart_data.get("grouping") or "clustered"
        axes_xml = _axis_xml(
            cat_ax_id,
            val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            chart_type=chart_type,
            grouping=grouping,
        )
        overlap_xml = (
            '<c:overlap val="100"/>'
            if grouping in {"stacked", "percentStacked"}
            else ""
        )
        return (
            "<c:barChart>"
            f'<c:barDir val="{bar_dir}"/><c:grouping val="{grouping}"/>'
            f"{ser_xml}"
            '<c:gapWidth val="150"/>'
            f"{overlap_xml}"
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            "</c:barChart>"
            f"{axes_xml}"
        )
    if chart_type in {"line", "area"}:
        tag = "lineChart" if chart_type == "line" else "areaChart"
        grouping = chart_data.get("grouping") or "standard"
        axes_xml = _axis_xml(
            cat_ax_id,
            val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            chart_type=chart_type,
            grouping=grouping,
        )
        line_tail_xml = '<c:marker val="1"/><c:smooth val="0"/>' if chart_type == "line" else ""
        return (
            f'<c:{tag}><c:grouping val="{grouping}"/><c:varyColors val="0"/>'
            f"{ser_xml}"
            f"{line_tail_xml}"
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            f"</c:{tag}>"
            f"{axes_xml}"
        )
    if chart_type == "doughnut":
        return (
            '<c:doughnutChart><c:varyColors val="1"/>'
            f"{ser_xml}"
            '<c:firstSliceAng val="0"/><c:holeSize val="75"/>'
            "</c:doughnutChart>"
        )
    if chart_type == "of_pie":
        of_pie_type = chart_data.get("of_pie_type", "pie")
        return (
            f'<c:ofPieChart><c:ofPieType val="{of_pie_type}"/>'
            '<c:varyColors val="1"/>'
            f"{ser_xml}"
            '<c:gapWidth val="100"/><c:secondPieSize val="75"/><c:serLines/>'
            "</c:ofPieChart>"
        )
    if chart_type == "radar":
        radar_style = chart_data.get("radar_style", "marker")
        axes_xml = _axis_xml(
            cat_ax_id,
            val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            chart_type=chart_type,
        )
        return (
            f'<c:radarChart><c:radarStyle val="{radar_style}"/>'
            '<c:varyColors val="0"/>'
            f"{ser_xml}"
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            "</c:radarChart>"
            f"{axes_xml}"
        )
    return f'<c:pieChart><c:varyColors val="1"/>{ser_xml}<c:firstSliceAng val="0"/></c:pieChart>'


def _axis_xml(
    cat_ax_id: str,
    val_ax_id: str,
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
    chart_type: str,
    grouping: str | None = None,
) -> str:
    cat_pos = "l" if chart_type == "bar" else "b"
    val_pos = "b" if chart_type == "bar" else "l"
    val_num_fmt = (
        '<c:numFmt formatCode="0%" sourceLinked="0"/>'
        if grouping == "percentStacked"
        else ""
    )
    axis_sp_pr = _chart_line_sp_pr_xml(chart_style.get("axis_color"))
    axis_tx_pr = _chart_tx_pr_xml(axis_font_size, chart_style.get("text_color"))
    cat_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("category"), axis_titles.get("x")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    val_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("value"), axis_titles.get("y")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    return (
        "<c:catAx>"
        f'<c:axId val="{cat_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="{cat_pos}"/>{cat_title_xml}<c:majorTickMark val="out"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{val_ax_id}"/><c:crosses val="autoZero"/><c:auto val="1"/>'
        '<c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/>'
        "</c:catAx>"
        "<c:valAx>"
        f'<c:axId val="{val_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="{val_pos}"/>{_major_gridlines_xml(chart_style.get("grid_color"))}'
        f"{val_title_xml}{val_num_fmt}"
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{cat_ax_id}"/><c:crosses val="autoZero"/>'
        "</c:valAx>"
    )


def _xy_axis_xml(
    x_ax_id: str,
    y_ax_id: str,
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
) -> str:
    axis_sp_pr = _chart_line_sp_pr_xml(chart_style.get("axis_color"))
    axis_tx_pr = _chart_tx_pr_xml(axis_font_size, chart_style.get("text_color"))
    x_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("x"), axis_titles.get("category")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    y_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("y"), axis_titles.get("value")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    return (
        "<c:valAx>"
        f'<c:axId val="{x_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="b"/>{x_title_xml}<c:majorTickMark val="out"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{y_ax_id}"/><c:crosses val="autoZero"/>'
        '<c:crossBetween val="midCat"/>'
        "</c:valAx>"
        "<c:valAx>"
        f'<c:axId val="{y_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="l"/>{_major_gridlines_xml(chart_style.get("grid_color"))}'
        f'{y_title_xml}<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{x_ax_id}"/><c:crosses val="autoZero"/>'
        '<c:crossBetween val="midCat"/>'
        "</c:valAx>"
    )


def _stock_series_xml(
    categories: list[int | float],
    series: list[dict[str, Any]],
    *,
    colors: list[str],
) -> str:
    parts: list[str] = []
    for index, item in enumerate(series):
        column_index = index + 2
        parts.append(
            "<c:ser>"
            f'<c:idx val="{index}"/><c:order val="{index}"/>'
            "<c:tx><c:strRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$1</c:f>"
            f"{_string_cache([str(item['name'])])}"
            "</c:strRef></c:tx>"
            '<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>'
            '<c:marker><c:symbol val="none"/></c:marker>'
            "<c:cat><c:numRef>"
            f"<c:f>Sheet1!$A$2:$A${len(categories) + 1}</c:f>"
            f"{_number_cache(categories)}"
            "</c:numRef></c:cat>"
            "<c:val><c:numRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$2:${_excel_col(column_index)}${len(categories) + 1}</c:f>"
            f"{_number_cache(item['values'])}"
            "</c:numRef></c:val>"
            '<c:smooth val="0"/>'
            "</c:ser>"
        )
    return "".join(parts)


def _stock_axis_xml(
    cat_ax_id: str,
    val_ax_id: str,
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
) -> str:
    axis_sp_pr = _chart_line_sp_pr_xml(chart_style.get("axis_color"))
    axis_tx_pr = _chart_tx_pr_xml(axis_font_size, chart_style.get("text_color"))
    cat_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("category"), axis_titles.get("x")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    val_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("value"), axis_titles.get("y")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
    )
    return (
        "<c:dateAx>"
        f'<c:axId val="{cat_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        '<c:delete val="0"/><c:axPos val="b"/>'
        f'{cat_title_xml}<c:numFmt formatCode="m/d/yyyy" sourceLinked="1"/>'
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{val_ax_id}"/><c:crosses val="autoZero"/>'
        '<c:auto val="1"/><c:lblOffset val="100"/><c:baseTimeUnit val="days"/>'
        "</c:dateAx>"
        "<c:valAx>"
        f'<c:axId val="{val_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="l"/>{_major_gridlines_xml(chart_style.get("grid_color"))}'
        f'{val_title_xml}<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{cat_ax_id}"/><c:crosses val="autoZero"/>'
        "</c:valAx>"
    )


def _cx_points(values: list[Any]) -> str:
    return "".join(
        f'<cx:pt idx="{idx}">{_xml_escape(str(value))}</cx:pt>'
        for idx, value in enumerate(values)
    )


def _cx_col_range(start_col: int, col_count: int, row_count: int) -> str:
    start = _excel_col(start_col)
    end = _excel_col(start_col + col_count - 1)
    return f"Sheet1!${start}$2:${end}${row_count + 1}"


def _cx_str_dim(levels: list[list[str]], *, start_col: int, row_count: int) -> str:
    levels_xml = "".join(
        f'<cx:lvl ptCount="{len(level)}">{_cx_points(level)}</cx:lvl>'
        for level in reversed(levels)
    )
    return (
        '<cx:strDim type="cat">'
        f"<cx:f>{_cx_col_range(start_col, len(levels), row_count)}</cx:f>"
        f"{levels_xml}"
        "</cx:strDim>"
    )


def _cx_num_dim(
    values: list[int | float],
    *,
    dim_type: str,
    col: int,
) -> str:
    return (
        f'<cx:numDim type="{dim_type}">'
        f"<cx:f>Sheet1!${_excel_col(col)}$2:${_excel_col(col)}${len(values) + 1}</cx:f>"
        f'<cx:lvl ptCount="{len(values)}" formatCode="General">{_cx_points(values)}</cx:lvl>'
        "</cx:numDim>"
    )


def _chart_ex_data_xml(chart_data: dict[str, Any]) -> str:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        values = chart_data["values"]
        levels = chart_data["levels"]
        return (
            '<cx:data id="0">'
            f'{_cx_str_dim(levels, start_col=1, row_count=len(values))}'
            f'{_cx_num_dim(values, dim_type="size", col=len(levels) + 1)}'
            "</cx:data>"
        )
    if chart_type == "histogram":
        values = chart_data["values"]
        return f'<cx:data id="0">{_cx_num_dim(values, dim_type="val", col=1)}</cx:data>'
    if chart_type in {"funnel", "pareto", "waterfall"}:
        values = chart_data["values"]
        categories = chart_data["categories"]
        return (
            '<cx:data id="0">'
            f'{_cx_str_dim([categories], start_col=1, row_count=len(values))}'
            f'{_cx_num_dim(values, dim_type="val", col=2)}'
            "</cx:data>"
        )
    if chart_type == "box_whisker":
        parts: list[str] = []
        for idx, item in enumerate(chart_data["series"]):
            start_col = idx * 2 + 1
            parts.append(
                f'<cx:data id="{idx}">'
                f'{_cx_str_dim([item["categories"]], start_col=start_col, row_count=len(item["values"]))}'
                f'{_cx_num_dim(item["values"], dim_type="val", col=start_col + 1)}'
                "</cx:data>"
            )
        return "".join(parts)
    raise RuntimeError(f"Native PPTX {chart_type} chart is outside current basic chart support")


def _chart_ex_series_xml(chart_data: dict[str, Any]) -> str:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        layout_id = chart_type
        label_pos = "ctr" if chart_type == "sunburst" else "inEnd"
        layout_pr = ""
        if chart_type == "treemap":
            parent_labels = chart_data.get("parent_labels", "overlapping")
            layout_pr = (
                "<cx:layoutPr>"
                f'<cx:parentLabelLayout val="{parent_labels}"/>'
                "</cx:layoutPr>"
            )
        return (
            f'<cx:series layoutId="{layout_id}" uniqueId="{{00000000-0000-4000-8000-000000000001}}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$A$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            f'<cx:dataLabels pos="{label_pos}"><cx:visibility seriesName="0" categoryName="1" value="1"/></cx:dataLabels>'
            '<cx:dataId val="0"/>'
            f"{layout_pr}"
            "</cx:series>"
        )
    if chart_type == "histogram":
        return (
            '<cx:series layoutId="clusteredColumn" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$A$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataId val="0"/><cx:layoutPr><cx:binning intervalClosed="r"/></cx:layoutPr>'
            "</cx:series>"
        )
    if chart_type == "pareto":
        return (
            '<cx:series layoutId="clusteredColumn" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$B$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataId val="0"/><cx:layoutPr><cx:aggregation/></cx:layoutPr>'
            '<cx:axisId val="1"/></cx:series>'
            '<cx:series layoutId="paretoLine" ownerIdx="0" uniqueId="{00000000-0000-4000-8000-000000000002}">'
            '<cx:axisId val="2"/></cx:series>'
        )
    if chart_type == "waterfall":
        subtotals_xml = ""
        if chart_data.get("subtotals"):
            subtotal_items = "".join(f'<cx:idx val="{idx}"/>' for idx in chart_data["subtotals"])
            subtotals_xml = f"<cx:subtotals>{subtotal_items}</cx:subtotals>"
        return (
            '<cx:series layoutId="waterfall" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$B$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataLabels pos="outEnd"><cx:visibility seriesName="0" categoryName="0" value="1"/></cx:dataLabels>'
            f'<cx:dataId val="0"/><cx:layoutPr>{subtotals_xml}</cx:layoutPr>'
            "</cx:series>"
        )
    if chart_type == "funnel":
        return (
            '<cx:series layoutId="funnel" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$B$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataLabels><cx:visibility seriesName="0" categoryName="0" value="1"/></cx:dataLabels>'
            '<cx:dataId val="0"/></cx:series>'
        )
    if chart_type == "box_whisker":
        parts: list[str] = []
        for idx, item in enumerate(chart_data["series"]):
            value_col = _excel_col(idx * 2 + 2)
            parts.append(
                f'<cx:series layoutId="boxWhisker" uniqueId="{{00000000-0000-4000-8000-{idx + 1:012d}}}">'
                f'<cx:tx><cx:txData><cx:f>Sheet1!${value_col}$1</cx:f><cx:v>{_xml_escape(str(item["name"]))}</cx:v></cx:txData></cx:tx>'
                f'<cx:dataId val="{idx}"/><cx:layoutPr>'
                '<cx:visibility meanMarker="1" outliers="1"/>'
                '<cx:statistics quartileMethod="exclusive"/>'
                '</cx:layoutPr></cx:series>'
            )
        return "".join(parts)
    raise RuntimeError(f"Native PPTX {chart_type} chart is outside current basic chart support")


def _chart_ex_axes_xml(chart_data: dict[str, Any]) -> str:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        return ""
    if chart_type == "pareto":
        return (
            '<cx:axis id="0"><cx:catScaling gapWidth="0"/><cx:tickLabels/></cx:axis>'
            '<cx:axis id="1"><cx:valScaling/><cx:majorGridlines/><cx:tickLabels/></cx:axis>'
            '<cx:axis id="2"><cx:valScaling max="1" min="0"/><cx:units unit="percentage"/><cx:tickLabels/></cx:axis>'
        )
    if chart_type == "funnel":
        return '<cx:axis id="1"><cx:catScaling gapWidth="0.06"/><cx:tickLabels/></cx:axis>'
    gap_width = "0.5" if chart_type == "waterfall" else "0"
    if chart_type == "box_whisker":
        gap_width = "1"
    return (
        f'<cx:axis id="0"><cx:catScaling gapWidth="{gap_width}"/><cx:tickLabels/></cx:axis>'
        '<cx:axis id="1"><cx:valScaling/><cx:majorGridlines/><cx:tickLabels/></cx:axis>'
    )


def _chart_ex_xml(
    payload: dict[str, Any],
    chart_data: dict[str, Any],
    *,
    chart_rels_id: str,
) -> bytes:
    data_xml = _chart_ex_data_xml(chart_data)
    series_xml = _chart_ex_series_xml(chart_data)
    axes_xml = _chart_ex_axes_xml(chart_data)
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cx:chartSpace xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
               xmlns:cx="{CHARTEX_URI}">
<cx:chartData><cx:externalData r:id="{chart_rels_id}" cx:autoUpdate="0"/>{data_xml}</cx:chartData>
<cx:chart><cx:title pos="t" align="ctr" overlay="0"/>
<cx:plotArea><cx:plotAreaRegion>{series_xml}</cx:plotAreaRegion>{axes_xml}</cx:plotArea>
{_chart_ex_legend_xml(payload)}</cx:chart>
</cx:chartSpace>'''
    return xml.encode("utf-8")


def _chart_xml(
    elem: ET.Element,
    payload: dict[str, Any],
    *,
    chart_rels_id: str,
    chart_data: dict[str, Any],
) -> bytes:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    colors = (
        [_clean_hex(color, "#4472C4") for color in style.get("colors", [])]
        if isinstance(style.get("colors"), list)
        else []
    )
    text_sizes = _chart_text_sizes(payload)
    axis_titles = _axis_titles(payload)
    chart_style = _classic_chart_style(payload, elem)
    plot_xml = _chart_plot_xml(
        chart_data,
        colors,
        axis_font_size=text_sizes["axis"],
        axis_title_font_size=text_sizes["axis_title"],
        axis_titles=axis_titles,
        chart_style=chart_style,
    )
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<c:date1904 val="0"/>
<c:lang val="en-US"/>
<c:chart>
{_chart_title_xml(payload.get("title"), font_size=text_sizes["title"], color=chart_style.get("text_color"))}
<c:plotArea><c:layout/>{plot_xml}{_chart_area_sp_pr_xml(chart_style.get("plot_fill"))}</c:plotArea>
{_chart_legend_xml(payload, font_size=text_sizes["legend"], color=chart_style.get("text_color"))}
<c:plotVisOnly val="1"/>
<c:dispBlanksAs val="gap"/>
</c:chart>
{_chart_area_sp_pr_xml(chart_style.get("chart_fill"))}
{_chart_tx_pr_xml(text_sizes["base"], chart_style.get("text_color"))}
<c:externalData r:id="{chart_rels_id}"><c:autoUpdate val="0"/></c:externalData>
</c:chartSpace>'''
    return xml.encode("utf-8")


def _chart_rels_xml(workbook_target: str) -> bytes:
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="{PACKAGE_REL_TYPE}" Target="{_xml_escape(workbook_target)}"/>
</Relationships>'''
    return xml.encode("utf-8")


def _chart_ex_rels_xml(workbook_target: str, style_target: str, colors_target: str) -> bytes:
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="{PACKAGE_REL_TYPE}" Target="{_xml_escape(workbook_target)}"/>
<Relationship Id="rId2" Type="{CHART_STYLE_REL_TYPE}" Target="{_xml_escape(style_target)}"/>
<Relationship Id="rId3" Type="{CHART_COLOR_STYLE_REL_TYPE}" Target="{_xml_escape(colors_target)}"/>
</Relationships>'''
    return xml.encode("utf-8")


def _chart_ex_style_xml() -> bytes:
    return b'''<cs:chartStyle xmlns:cs="http://schemas.microsoft.com/office/drawing/2012/chartStyle" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" id="410"><cs:axisTitle><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="bg1"><a:lumMod val="65000"/></a:schemeClr></a:solidFill><a:ln w="19050"><a:solidFill><a:schemeClr val="bg1"/></a:solidFill></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:axisTitle><cs:categoryAxis><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:categoryAxis><cs:chartArea mods="allowNoFillOverride allowNoLineOverride"><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="bg1"/></a:solidFill><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr><cs:defRPr sz="1330"/></cs:chartArea><cs:dataLabel><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="lt1"/></cs:fontRef><cs:defRPr sz="1197"/></cs:dataLabel><cs:dataLabelCallout><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="dk1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="lt1"/></a:solidFill><a:ln><a:solidFill><a:schemeClr val="dk1"><a:lumMod val="25000"/><a:lumOff val="75000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr><cs:defRPr sz="1197"/><cs:bodyPr rot="0" spcFirstLastPara="1" vertOverflow="clip" horzOverflow="clip" vert="horz" wrap="square" lIns="36576" tIns="18288" rIns="36576" bIns="18288" anchor="ctr" anchorCtr="1"><a:spAutoFit/></cs:bodyPr></cs:dataLabelCallout><cs:dataPoint><cs:lnRef idx="0"/><cs:fillRef idx="0"><cs:styleClr val="auto"/></cs:fillRef><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:ln w="19050"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></cs:spPr></cs:dataPoint><cs:dataPoint3D><cs:lnRef idx="0"/><cs:fillRef idx="0"><cs:styleClr val="auto"/></cs:fillRef><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></cs:spPr></cs:dataPoint3D><cs:dataPointLine><cs:lnRef idx="0"><cs:styleClr val="auto"/></cs:lnRef><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="28575" cap="rnd"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:round/></a:ln></cs:spPr></cs:dataPointLine><cs:dataPointMarker><cs:lnRef idx="0"/><cs:fillRef idx="0"><cs:styleClr val="auto"/></cs:fillRef><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:ln w="9525"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></cs:spPr></cs:dataPointMarker><cs:dataPointMarkerLayout symbol="circle" size="5"/><cs:dataPointWireframe><cs:lnRef idx="0"><cs:styleClr val="auto"/></cs:lnRef><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="28575" cap="rnd"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:round/></a:ln></cs:spPr></cs:dataPointWireframe><cs:dataTable><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:ln w="9525"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:dataTable><cs:downBar><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="dk1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="dk1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></a:solidFill><a:ln w="9525"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr></cs:downBar><cs:dropLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="35000"/><a:lumOff val="65000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:dropLine><cs:errorBar><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:errorBar><cs:floor><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:floor><cs:gridlineMajor><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:gridlineMajor><cs:gridlineMinor><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:gridlineMinor><cs:hiLoLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="75000"/><a:lumOff val="25000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:hiLoLine><cs:leaderLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="35000"/><a:lumOff val="65000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:leaderLine><cs:legend><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1197"/></cs:legend><cs:plotArea mods="allowNoFillOverride allowNoLineOverride"><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:plotArea><cs:plotArea3D mods="allowNoFillOverride allowNoLineOverride"><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:plotArea3D><cs:seriesAxis><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:seriesAxis><cs:seriesLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill><a:round/></a:ln></cs:spPr></cs:seriesLine><cs:title><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1862"/></cs:title><cs:trendline><cs:lnRef idx="0"><cs:styleClr val="auto"/></cs:lnRef><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="19050" cap="rnd"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="sysDash"/></a:ln></cs:spPr></cs:trendline><cs:trendlineLabel><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1197"/></cs:trendlineLabel><cs:upBar><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="dk1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="lt1"/></a:solidFill><a:ln w="9525"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr></cs:upBar><cs:valueAxis><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1197"/></cs:valueAxis><cs:wall><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:wall></cs:chartStyle>'''


def _chart_ex_colors_xml() -> bytes:
    return b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cs:colorStyle xmlns:cs="http://schemas.microsoft.com/office/drawing/2012/chartStyle"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               meth="cycle" id="10">
<a:schemeClr val="accent1"/><a:schemeClr val="accent2"/><a:schemeClr val="accent3"/>
<a:schemeClr val="accent4"/><a:schemeClr val="accent5"/><a:schemeClr val="accent6"/>
</cs:colorStyle>'''


def _xlsx_cell_ref(row: int, col: int) -> str:
    return f"{_excel_col(col)}{row}"


def _xlsx_cell(value: Any, row: int, col: int) -> str:
    ref = _xlsx_cell_ref(row, col)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return (
        f'<c r="{ref}" t="inlineStr"><is><t>{_xml_escape(str(value))}</t></is></c>'
    )


def _minimal_workbook(rows: list[list[Any]]) -> bytes:
    if Workbook is not None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Sheet1"
        for row in rows:
            worksheet.append(row)
        buffer = io.BytesIO()
        workbook.save(buffer)
        workbook.close()
        return buffer.getvalue()

    sheet_rows = []
    for row_index, values in enumerate(rows, start=1):
        cells = "".join(
            _xlsx_cell(value, row_index, col_index)
            for col_index, value in enumerate(values, start=1)
        )
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')

    entries = {
        "[Content_Types].xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml"
          ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml"
          ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml"
          ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>''',
        "_rels/.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1"
              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
              Target="xl/workbook.xml"/>
</Relationships>''',
        "xl/workbook.xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>''',
        "xl/_rels/workbook.xml.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1"
              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
              Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2"
              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
              Target="styles.xml"/>
</Relationships>''',
        "xl/worksheets/sheet1.xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>''',
        "xl/styles.xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>''',
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data.encode("utf-8"))
    return buffer.getvalue()


def _minimal_category_chart_workbook(chart_data: dict[str, Any]) -> bytes:
    categories = chart_data["categories"]
    series = chart_data["series"]
    rows: list[list[Any]] = [["Category"] + [item["name"] for item in series]]
    for row_index, category in enumerate(categories):
        rows.append([category] + [item["values"][row_index] for item in series])
    return _minimal_workbook(rows)


def _minimal_xy_chart_workbook(chart_data: dict[str, Any]) -> bytes:
    series = chart_data["series"]
    is_bubble = chart_data["type"] == "bubble"
    rows: list[list[Any]] = [[]]
    for item in series:
        rows[0].extend([f"{item['name']} X", item["name"]])
        if is_bubble:
            rows[0].append(f"{item['name']} Size")

    max_points = max(len(item["x"]) for item in series)
    for point_idx in range(max_points):
        row: list[Any] = []
        for item in series:
            if point_idx < len(item["x"]):
                row.extend([item["x"][point_idx], item["y"][point_idx]])
                if is_bubble:
                    row.append(item["sizes"][point_idx])
            else:
                row.extend(["", ""])
                if is_bubble:
                    row.append("")
        rows.append(row)
    return _minimal_workbook(rows)


def _minimal_chart_ex_workbook(chart_data: dict[str, Any]) -> bytes:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        levels = chart_data["levels"]
        rows: list[list[Any]] = [[f"Level {idx + 1}" for idx in range(len(levels))] + ["Value"]]
        for row_idx, value in enumerate(chart_data["values"]):
            rows.append([level[row_idx] for level in levels] + [value])
        return _minimal_workbook(rows)
    if chart_type == "histogram":
        return _minimal_workbook([["Value"]] + [[value] for value in chart_data["values"]])
    if chart_type in {"funnel", "pareto", "waterfall"}:
        rows = [["Category", "Value"]]
        rows.extend(
            [category, chart_data["values"][idx]]
            for idx, category in enumerate(chart_data["categories"])
        )
        return _minimal_workbook(rows)
    if chart_type == "box_whisker":
        rows = [[]]
        for item in chart_data["series"]:
            rows[0].extend([f"{item['name']} Category", item["name"]])
        max_rows = max(len(item["values"]) for item in chart_data["series"])
        for row_idx in range(max_rows):
            row: list[Any] = []
            for item in chart_data["series"]:
                if row_idx < len(item["values"]):
                    row.extend([item["categories"][row_idx], item["values"][row_idx]])
                else:
                    row.extend(["", ""])
            rows.append(row)
        return _minimal_workbook(rows)
    raise RuntimeError(f"Native PPTX {chart_type} chart is outside current basic chart support")


def _build_native_chart(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    chart_data = _chart_data(payload)
    off_x, off_y, ext_cx, ext_cy = _bounds(elem, payload, ctx)

    shape_id = ctx.next_id()
    rel_id = ctx.next_rel_id()
    local_index = 1 + sum(1 for part in ctx.package_files if part.startswith("ppt/charts/chart"))
    part_index = ctx.slide_num * 100 + local_index
    workbook_name = f"Microsoft_Excel_Sheet{part_index}.xlsx"
    workbook_part = f"ppt/embeddings/{workbook_name}"

    if chart_data["kind"] == "chartex":
        chart_name = f"chartEx{part_index}.xml"
        style_name = f"style{part_index}.xml"
        colors_name = f"colors{part_index}.xml"
        chart_part = f"ppt/charts/{chart_name}"
        chart_rels_part = f"ppt/charts/_rels/{chart_name}.rels"
        style_part = f"ppt/charts/{style_name}"
        colors_part = f"ppt/charts/{colors_name}"
        graphic_uri = CHARTEX_URI
        chart_ref_xml = (
            f'<cx:chart xmlns:cx="{CHARTEX_URI}" '
            f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            f'r:id="{rel_id}"/>'
        )
        ctx.rel_entries.append({
            "id": rel_id,
            "type": CHARTEX_REL_TYPE,
            "target": f"../charts/{chart_name}",
        })
        ctx.package_files[chart_part] = _chart_ex_xml(payload, chart_data, chart_rels_id="rId1")
        ctx.package_files[chart_rels_part] = _chart_ex_rels_xml(
            f"../embeddings/{workbook_name}",
            style_name,
            colors_name,
        )
        ctx.package_files[style_part] = _chart_ex_style_xml()
        ctx.package_files[colors_part] = _chart_ex_colors_xml()
        ctx.package_files[workbook_part] = _minimal_chart_ex_workbook(chart_data)
        ctx.content_type_overrides[chart_part] = CHARTEX_CONTENT_TYPE
        ctx.content_type_overrides[style_part] = CHART_STYLE_CONTENT_TYPE
        ctx.content_type_overrides[colors_part] = CHART_COLOR_STYLE_CONTENT_TYPE
    else:
        chart_name = f"chart{part_index}.xml"
        chart_part = f"ppt/charts/{chart_name}"
        chart_rels_part = f"ppt/charts/_rels/{chart_name}.rels"
        graphic_uri = CHART_URI
        chart_ref_xml = (
            '<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
            f'r:id="{rel_id}"/>'
        )
        ctx.rel_entries.append({
            "id": rel_id,
            "type": CHART_REL_TYPE,
            "target": f"../charts/{chart_name}",
        })
        ctx.package_files[chart_part] = _chart_xml(
            elem,
            payload,
            chart_rels_id="rId1",
            chart_data=chart_data,
        )
        ctx.package_files[chart_rels_part] = _chart_rels_xml(f"../embeddings/{workbook_name}")
        if chart_data["kind"] == "xy":
            ctx.package_files[workbook_part] = _minimal_xy_chart_workbook(chart_data)
        else:
            ctx.package_files[workbook_part] = _minimal_category_chart_workbook(chart_data)
        ctx.content_type_overrides[chart_part] = CHART_CONTENT_TYPE

    name = _xml_escape(str(payload.get("name") or elem.get("id") or f"Native Chart {shape_id}"))
    chart_frame_xml = f'''<p:graphicFrame>
<p:nvGraphicFramePr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
<p:nvPr/>
</p:nvGraphicFramePr>
<p:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></p:xfrm>
<a:graphic>
<a:graphicData uri="{graphic_uri}">
{chart_ref_xml}
</a:graphicData>
</a:graphic>
</p:graphicFrame>'''
    text_sizes = _chart_text_sizes(payload)
    chart_style = _classic_chart_style(payload, elem)
    companion_xml = _chart_companion_text_xml(
        ctx,
        payload,
        chart_bounds=(off_x, off_y, ext_cx, ext_cy),
        chart_style=chart_style,
        note_font_size=text_sizes["note"],
        title_font_size=text_sizes["title"],
        include_title=chart_data["kind"] == "chartex",
    )
    xml = chart_frame_xml + companion_xml
    return ShapeResult(xml=xml, bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))


def _validate_native_object_marker_payload(
    elem: ET.Element,
) -> tuple[str, dict[str, Any], list[list[Any]] | None]:
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return "", {}, None
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-native value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX table/chart markers must be <g> elements")
    transform = elem.get("transform", "")
    if transform and any(token in transform for token in ("rotate", "matrix", "skew")):
        raise RuntimeError("Native PPTX table/chart markers support translate/scale transforms only")

    payload = _load_payload(elem, kind)
    _validate_bounds_inputs(elem, payload)
    table_rows = None
    if kind == "table":
        table_rows, _ = _validate_table_payload(payload)
    else:
        _chart_data(payload)
    return kind, payload, table_rows


def validate_native_object_marker(elem: ET.Element) -> None:
    """Validate a data-pptx-native marker without mutating the PPTX package."""
    _validate_native_object_marker_payload(elem)


def validate_native_object_marker_with_warnings(elem: ET.Element) -> list[str]:
    """Validate a data-pptx-native marker and return non-fatal warnings."""
    kind, _, table_rows = _validate_native_object_marker_payload(elem)
    if kind != "table" or table_rows is None:
        return []
    return _native_table_warnings(elem, table_rows)


def native_object_marker_warnings(elem: ET.Element) -> list[str]:
    """Return non-fatal warnings for a data-pptx-native marker."""
    return validate_native_object_marker_with_warnings(elem)


def convert_native_object(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert a marked SVG group to a native PowerPoint table or chart."""
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return None
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-native value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX table/chart markers must be <g> elements")
    transform = elem.get("transform", "")
    if transform and any(token in transform for token in ("rotate", "matrix", "skew")):
        raise RuntimeError("Native PPTX table/chart markers support translate/scale transforms only")

    payload = _load_payload(elem, kind)
    if kind == "table":
        return _build_native_table(elem, ctx, payload)
    return _build_native_chart(elem, ctx, payload)
