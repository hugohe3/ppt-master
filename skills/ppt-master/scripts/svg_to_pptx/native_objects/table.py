"""Native PowerPoint table conversion."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.context import ConvertContext, ShapeResult
from ..drawingml.utils import px_to_emu, _xml_escape
from .chart_style import _font_face_xml
from .marker_common import (
    TABLE_URI,
    _bool_attr,
    _bounds,
    _chart_bool,
    _clean_hex,
    _compact_key,
    _first_present,
    _font_size_hpt,
    _normalized_fallback_text,
    _number,
    _visible_fallback_texts,
)


def _table_text_run(
    text: str,
    *,
    color: str,
    bold: bool,
    font_size: int,
    font_face: str | None,
) -> str:
    bold_attr = ' b="1"' if bold else ""
    return (
        f'<a:r><a:rPr lang="en-US" sz="{font_size}"{bold_attr}>'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'{_font_face_xml(font_face)}'
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


def _native_table_metadata_texts(table_rows: list[list[Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in table_rows:
        for cell in row:
            cell_data = _cell_payload(cell)
            text = _normalized_fallback_text(cell_data.get("text"))
            if text:
                counts[text] = counts.get(text, 0) + 1
    return counts


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
