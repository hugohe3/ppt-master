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
    matrix_multiply,
    parse_transform_matrix,
    px_to_emu,
    transform_point,
    _xml_escape,
)

TABLE_URI = "http://schemas.openxmlformats.org/drawingml/2006/table"
CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"
CHART_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
PACKAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/package"
CHART_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"

_NATIVE_KINDS = {"table", "chart"}
_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
_POINT_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if "}" in elem.tag else elem.tag


def _clean_hex(value: Any, default: str) -> str:
    match = _HEX_RE.match(str(value or ""))
    if not match:
        match = _HEX_RE.match(default)
    return match.group(1).upper() if match else "000000"


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


def _validate_table_payload(payload: dict[str, Any]) -> None:
    columns = payload.get("columns") or []
    rows = payload.get("rows") or []
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise RuntimeError("Native PPTX table requires columns/rows lists")
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, list):
            raise RuntimeError(f"Native PPTX table row {idx} must be a list")

    table_rows = [columns] if columns else []
    table_rows.extend(rows)
    if not table_rows:
        raise RuntimeError("Native PPTX table requires at least one row")
    if max(len(row) for row in table_rows) <= 0:
        raise RuntimeError("Native PPTX table requires at least one column")


def _build_native_table(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    _validate_table_payload(payload)
    columns = payload.get("columns") or []
    rows = payload.get("rows") or []

    table_rows: list[list[Any]] = []
    header_rows = int(payload.get("header_rows", 1 if columns else 0))
    if columns:
        table_rows.append(columns)
    table_rows.extend(rows)

    col_count = max(len(row) for row in table_rows)
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
    row_height = max(ext_cy // len(table_rows), 1)

    column_widths = payload.get("column_widths")
    if isinstance(column_widths, list) and len(column_widths) == col_count:
        total = sum(max(float(width), 0.0) for width in column_widths) or col_count
        grid_widths = [max(round(ext_cx * max(float(width), 0.0) / total), 1) for width in column_widths]
        grid_widths[-1] += ext_cx - sum(grid_widths)
    else:
        base_width = max(ext_cx // col_count, 1)
        grid_widths = [base_width] * col_count
        grid_widths[-1] += ext_cx - sum(grid_widths)

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
            cells_xml.append(
                "<a:tc>"
                "<a:txBody><a:bodyPr/><a:lstStyle/>"
                f"<a:p>{paragraph_props}"
                f"{_table_text_run(text, color=color, bold=bold, font_size=cell_font_size, font_face=font_face)}"
                "</a:p></a:txBody>"
                f'<a:tcPr anchor="ctr"><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill></a:tcPr>'
                "</a:tc>"
            )
        rows_xml.append(f'<a:tr h="{row_height}">{"".join(cells_xml)}</a:tr>')

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
    "pie",
    "radar",
}
_XY_CHART_TYPES = {"scatter", "bubble"}
_DEFERRED_CHART_TYPES = {
    "box_whisker",
    "bullet",
    "combo",
    "funnel",
    "gantt",
    "heatmap",
    "histogram",
    "map",
    "of_pie",
    "pareto",
    "stock",
    "sunburst",
    "treemap",
    "waterfall",
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
        "line": ("line", "standard", None),
        "linemarkers": ("line", "standard", None),
        "linestacked": ("line", "stacked", None),
        "linestacked100": ("line", "percentStacked", None),
        "pie": ("pie", None, None),
        "pieexploded": ("pie", None, "exploded"),
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
        "radar": ("radar", None, "marker"),
        "radarfilled": ("radar", None, "filled"),
        "radarmarkers": ("radar", None, "marker"),
        "scatter": ("scatter", None, "lineMarker"),
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
        "xy": ("scatter", None, "lineMarker"),
        "xyscatter": ("scatter", None, "lineMarker"),
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

    supported = sorted(_CATEGORY_CHART_TYPES | _XY_CHART_TYPES)
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

    normalized = _compact_key(grouping)
    allowed = {"clustered"} if chart_type in {"bar", "column"} else {"standard"}
    if normalized not in allowed:
        if normalized in {"clustered", "standard"}:
            allowed_text = ", ".join(sorted(allowed))
            raise RuntimeError(f"Native PPTX {chart_type} chart grouping must be one of: {allowed_text}")
        raise RuntimeError(
            f"Native PPTX {grouping} grouping is outside current basic chart support"
        )
    return normalized


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
    if chart_type in {"doughnut", "pie"}:
        if len(series) != 1:
            raise RuntimeError("Native PPTX pie-family charts support exactly one series")

    radar_style = _compact_key(payload.get("radar_style") or alias_style or "marker")
    radar_aliases = {"marker": "marker", "markers": "marker"}
    if chart_type == "radar" and radar_style not in radar_aliases:
        raise RuntimeError(
            f"Native PPTX radar_style {radar_style} is outside current basic chart support"
        )

    if alias_style == "exploded" or payload.get("exploded"):
        raise RuntimeError("Native PPTX exploded pie/doughnut is outside current basic chart support")

    return {
        "kind": "category",
        "type": chart_type,
        "categories": categories,
        "grouping": _chart_grouping(chart_type, payload, alias_grouping)
        if chart_type in {"bar", "column", "line", "area"}
        else None,
        "radar_style": radar_aliases.get(radar_style, "marker"),
        "series": series,
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

    scatter_style = _compact_key(payload.get("scatter_style") or alias_style or "lineMarker")
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
        "scatter_style": style_aliases.get(scatter_style, "lineMarker"),
        "series": series,
    }


def _chart_data(payload: dict[str, Any]) -> dict[str, Any]:
    chart_type, alias_grouping, alias_style = _chart_kind(payload)
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


def _series_xml(
    categories: list[str],
    series: list[dict[str, Any]],
    *,
    chart_type: str,
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
        if chart_type in {"doughnut", "pie"}:
            color_xml = ""
            point_colors_xml = _data_point_colors_xml(len(categories), colors)
        marker_xml = '<c:marker><c:symbol val="circle"/></c:marker>' if chart_type == "line" else ""
        smooth_xml = '<c:smooth val="0"/>' if chart_type == "line" else ""
        parts.append(
            "<c:ser>"
            f'<c:idx val="{index}"/><c:order val="{index}"/>'
            "<c:tx><c:strRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$1</c:f>"
            f"{_string_cache([str(item['name'])])}"
            "</c:strRef></c:tx>"
            f"{color_xml}{marker_xml}{point_colors_xml}"
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


def _chart_title_xml(title: Any) -> str:
    if not title:
        return '<c:autoTitleDeleted val="1"/>'
    text = _xml_escape(str(title))
    return (
        "<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/>"
        f"<a:p><a:r><a:rPr lang=\"en-US\"/><a:t>{text}</a:t></a:r></a:p>"
        "</c:rich></c:tx><c:layout/></c:title>"
        '<c:autoTitleDeleted val="0"/>'
    )


def _chart_legend_xml(payload: dict[str, Any]) -> str:
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
    return f'<c:legend><c:legendPos val="{position}"/><c:layout/><c:overlay val="0"/></c:legend>'


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


def _chart_plot_xml(chart_data: dict[str, Any], colors: list[str]) -> str:
    chart_type = chart_data["type"]
    cat_ax_id = "2068027336"
    val_ax_id = "2113994440"
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
            return (
                f'<c:scatterChart><c:scatterStyle val="{scatter_style}"/>'
                '<c:varyColors val="0"/>'
                f"{ser_xml}"
                f'<c:axId val="{x_ax_id}"/><c:axId val="{y_ax_id}"/>'
                "</c:scatterChart>"
                f'{_xy_axis_xml(x_ax_id, y_ax_id)}'
            )
        return (
            '<c:bubbleChart><c:varyColors val="0"/>'
            f"{ser_xml}"
            '<c:bubbleScale val="100"/><c:showNegBubbles val="0"/>'
            f'<c:axId val="{x_ax_id}"/><c:axId val="{y_ax_id}"/>'
            "</c:bubbleChart>"
            f'{_xy_axis_xml(x_ax_id, y_ax_id)}'
        )

    categories = chart_data["categories"]
    series = chart_data["series"]
    ser_xml = _series_xml(
        categories,
        series,
        chart_type=chart_type,
        radar_style=chart_data.get("radar_style", "marker"),
        colors=colors,
    )

    if chart_type in {"bar", "column"}:
        bar_dir = "bar" if chart_type == "bar" else "col"
        grouping = chart_data.get("grouping") or "clustered"
        return (
            "<c:barChart>"
            f'<c:barDir val="{bar_dir}"/><c:grouping val="{grouping}"/>'
            f"{ser_xml}"
            '<c:gapWidth val="150"/>'
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            "</c:barChart>"
            f'{_axis_xml(cat_ax_id, val_ax_id, chart_type=chart_type)}'
        )
    if chart_type in {"line", "area"}:
        tag = "lineChart" if chart_type == "line" else "areaChart"
        grouping = chart_data.get("grouping") or "standard"
        return (
            f'<c:{tag}><c:grouping val="{grouping}"/><c:varyColors val="0"/>'
            f"{ser_xml}"
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            f"</c:{tag}>"
            f'{_axis_xml(cat_ax_id, val_ax_id, chart_type=chart_type)}'
        )
    if chart_type == "doughnut":
        return (
            '<c:doughnutChart><c:varyColors val="1"/>'
            f"{ser_xml}"
            '<c:firstSliceAng val="0"/><c:holeSize val="50"/>'
            "</c:doughnutChart>"
        )
    if chart_type == "radar":
        radar_style = chart_data.get("radar_style", "marker")
        return (
            f'<c:radarChart><c:radarStyle val="{radar_style}"/>'
            '<c:varyColors val="0"/>'
            f"{ser_xml}"
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            "</c:radarChart>"
            f'{_axis_xml(cat_ax_id, val_ax_id, chart_type=chart_type)}'
        )
    return f'<c:pieChart><c:varyColors val="1"/>{ser_xml}<c:firstSliceAng val="0"/></c:pieChart>'


def _axis_xml(cat_ax_id: str, val_ax_id: str, *, chart_type: str) -> str:
    cat_pos = "l" if chart_type == "bar" else "b"
    val_pos = "b" if chart_type == "bar" else "l"
    return (
        "<c:catAx>"
        f'<c:axId val="{cat_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="{cat_pos}"/><c:majorTickMark val="out"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        f'<c:crossAx val="{val_ax_id}"/><c:crosses val="autoZero"/><c:auto val="1"/>'
        '<c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/>'
        "</c:catAx>"
        "<c:valAx>"
        f'<c:axId val="{val_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="0"/><c:axPos val="{val_pos}"/><c:majorGridlines/>'
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f'<c:crossAx val="{cat_ax_id}"/><c:crosses val="autoZero"/>'
        "</c:valAx>"
    )


def _xy_axis_xml(x_ax_id: str, y_ax_id: str) -> str:
    return (
        "<c:valAx>"
        f'<c:axId val="{x_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        '<c:delete val="0"/><c:axPos val="b"/><c:majorTickMark val="out"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        f'<c:crossAx val="{y_ax_id}"/><c:crosses val="autoZero"/>'
        '<c:crossBetween val="midCat"/>'
        "</c:valAx>"
        "<c:valAx>"
        f'<c:axId val="{y_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        '<c:delete val="0"/><c:axPos val="l"/><c:majorGridlines/>'
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        '<c:tickLblPos val="nextTo"/>'
        f'<c:crossAx val="{x_ax_id}"/><c:crosses val="autoZero"/>'
        '<c:crossBetween val="midCat"/>'
        "</c:valAx>"
    )


def _chart_xml(
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
    plot_xml = _chart_plot_xml(chart_data, colors)
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<c:date1904 val="0"/>
<c:lang val="en-US"/>
<c:chart>
{_chart_title_xml(payload.get("title"))}
<c:plotArea><c:layout/>{plot_xml}</c:plotArea>
{_chart_legend_xml(payload)}
<c:plotVisOnly val="1"/>
<c:dispBlanksAs val="gap"/>
</c:chart>
<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1800"/></a:pPr>
<a:endParaRPr lang="en-US"/></a:p></c:txPr>
<c:externalData r:id="{chart_rels_id}"><c:autoUpdate val="0"/></c:externalData>
</c:chartSpace>'''
    return xml.encode("utf-8")


def _chart_rels_xml(workbook_target: str) -> bytes:
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="{PACKAGE_REL_TYPE}" Target="{_xml_escape(workbook_target)}"/>
</Relationships>'''
    return xml.encode("utf-8")


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


def _build_native_chart(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    chart_data = _chart_data(payload)
    off_x, off_y, ext_cx, ext_cy = _bounds(elem, payload, ctx)

    shape_id = ctx.next_id()
    rel_id = ctx.next_rel_id()
    local_index = 1 + sum(1 for part in ctx.package_files if part.startswith("ppt/charts/chart"))
    part_index = ctx.slide_num * 100 + local_index
    chart_name = f"chart{part_index}.xml"
    workbook_name = f"Microsoft_Excel_Sheet{part_index}.xlsx"
    chart_part = f"ppt/charts/{chart_name}"
    chart_rels_part = f"ppt/charts/_rels/{chart_name}.rels"
    workbook_part = f"ppt/embeddings/{workbook_name}"

    ctx.rel_entries.append({
        "id": rel_id,
        "type": CHART_REL_TYPE,
        "target": f"../charts/{chart_name}",
    })
    ctx.package_files[chart_part] = _chart_xml(
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
    xml = f'''<p:graphicFrame>
<p:nvGraphicFramePr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
<p:nvPr/>
</p:nvGraphicFramePr>
<p:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></p:xfrm>
<a:graphic>
<a:graphicData uri="{CHART_URI}">
<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" r:id="{rel_id}"/>
</a:graphicData>
</a:graphic>
</p:graphicFrame>'''
    return ShapeResult(xml=xml, bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))


def validate_native_object_marker(elem: ET.Element) -> None:
    """Validate a data-pptx-native marker without mutating the PPTX package."""
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-native value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX table/chart markers must be <g> elements")
    transform = elem.get("transform", "")
    if transform and any(token in transform for token in ("rotate", "matrix", "skew")):
        raise RuntimeError("Native PPTX table/chart markers support translate/scale transforms only")

    payload = _load_payload(elem, kind)
    _validate_bounds_inputs(elem, payload)
    if kind == "table":
        _validate_table_payload(payload)
    else:
        _chart_data(payload)


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
