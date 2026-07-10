"""Native PowerPoint table conversion."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.context import ConvertContext, ShapeResult
from ..drawingml.utils import _xml_escape
from .chart_style import _font_face_xml
from .marker_common import (
    TABLE_URI,
    _bool_attr,
    _bounds,
    _clean_hex,
    _compact_key,
    _first_present,
    _font_size_hpt,
    _normalized_fallback_text,
    _number,
    _powerpoint_emu,
    _powerpoint_line_width_emu,
    _visible_fallback_texts,
)


def _table_text_run(
    text: str,
    *,
    color: str | None,
    bold: bool | None,
    font_size: int | None,
    font_face: str | None,
) -> str:
    size_attr = f' sz="{font_size}"' if font_size is not None else ""
    bold_attr = f' b="{_bool_attr(bold)}"' if bold is not None else ""
    color_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    space_attr = ' xml:space="preserve"' if text != text.strip() else ""
    return (
        f'<a:r><a:rPr lang="en-US"{size_attr}{bold_attr}>'
        f'{color_xml}'
        f'{_font_face_xml(font_face)}'
        "</a:rPr>"
        f"<a:t{space_attr}>{_xml_escape(text)}</a:t></a:r>"
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
_TABLE_MAX_ROWS = 1000
_TABLE_MAX_COLUMNS = 1000


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
    value = payload.get("strict_grid", payload.get("strictGrid"))
    return _table_bool(value, "strict_grid", default=False)


def _table_bool(value: Any, field_name: str, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    key = _compact_key(value)
    if key in {"1", "on", "true", "yes"}:
        return True
    if key in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"Native PPTX table {field_name} must be a boolean")


def _table_header_rows(payload: dict[str, Any], row_count: int) -> int:
    default = 1 if payload.get("columns") else 0
    value = _number(payload.get("header_rows", default), "table header_rows")
    if not value.is_integer():
        raise RuntimeError("Native PPTX table header_rows must be an integer")
    header_rows = int(value)
    if not 0 <= header_rows <= row_count:
        raise RuntimeError(
            "Native PPTX table header_rows must be between zero and the resolved row count"
        )
    return header_rows


def _validate_table_lengths(payload: dict[str, Any], table_rows: list[list[Any]]) -> int:
    if not table_rows:
        raise RuntimeError("Native PPTX table requires at least one row")
    col_count = max(len(row) for row in table_rows)
    if col_count <= 0:
        raise RuntimeError("Native PPTX table requires at least one column")
    if len(table_rows) > _TABLE_MAX_ROWS or col_count > _TABLE_MAX_COLUMNS:
        raise RuntimeError("Native PPTX table supports at most 1000 rows and columns")
    if _grid_is_strict(payload) and any(len(row) != col_count for row in table_rows):
        raise RuntimeError("Native PPTX table strict_grid requires every row to have the same length")

    column_widths = payload.get("column_widths")
    if column_widths is not None:
        if not isinstance(column_widths, list) or len(column_widths) != col_count:
            raise RuntimeError("Native PPTX table column_widths must match the resolved column count")
        _table_weights(column_widths, "column_widths")

    row_heights = payload.get("row_heights")
    if row_heights is not None:
        if not isinstance(row_heights, list) or len(row_heights) != len(table_rows):
            raise RuntimeError("Native PPTX table row_heights must match the resolved row count")
        _table_weights(row_heights, "row_heights")

    return col_count


def _validate_table_cell_formatting(payload: dict[str, Any], table_rows: list[list[Any]]) -> None:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    _table_bool(style.get("band_row"), "style.band_row", default=True)
    for row in table_rows:
        for cell in row:
            cell_data = _cell_payload(cell)
            if "bold" in cell_data:
                _table_bool(cell_data["bold"], "cell bold", default=False)
            for side in ("left", "right", "top", "bottom"):
                _table_padding_value(cell_data, style, side)
            border_width = _table_border_width(cell_data, style)
            if border_width > 0:
                _powerpoint_line_width_emu(
                    border_width,
                    "table border_width",
                )
            _table_anchor(cell_data, style)


def _validate_table_payload(payload: dict[str, Any]) -> tuple[list[list[Any]], int]:
    table_rows = _table_rows(payload)
    _check_table_spans(payload, table_rows)
    col_count = _validate_table_lengths(payload, table_rows)
    _table_header_rows(payload, len(table_rows))
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
    if total < count:
        raise RuntimeError(
            f"Native PPTX table {field_name} cannot fit {count} positive grid lengths"
        )
    if weights is None:
        base, remainder = divmod(total, count)
        return [base + (1 if idx < remainder else 0) for idx in range(count)]

    numeric = _table_weights(weights, field_name)
    largest = max(numeric)
    normalized = [weight / largest for weight in numeric]
    normalized_total = sum(normalized)
    distributable = total - count
    quotas = [distributable * weight / normalized_total for weight in normalized]
    extras = [int(quota) for quota in quotas]
    remainder = distributable - sum(extras)
    if remainder < 0 or remainder > count:
        raise RuntimeError(f"Native PPTX table {field_name} allocation overflowed")
    order = sorted(
        range(count),
        key=lambda idx: (quotas[idx] - extras[idx], normalized[idx], -idx),
        reverse=True,
    )
    for idx in order[:remainder]:
        extras[idx] += 1
    return [extra + 1 for extra in extras]


def _table_weights(weights: list[Any], field_name: str) -> list[float]:
    numeric = [
        _number(weight, f"{field_name}[{idx}]")
        for idx, weight in enumerate(weights, start=1)
    ]
    if any(weight < 0 for weight in numeric):
        raise RuntimeError(f"Native PPTX table {field_name} values must be non-negative")
    if max(numeric, default=0.0) <= 0:
        raise RuntimeError(
            f"Native PPTX table {field_name} values must sum to a positive number"
        )
    return numeric


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
    pixels = max(_number(value, f"table {side} padding"), 0.0)
    return _powerpoint_emu(pixels, f"table {side} padding")


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
    line_width = _powerpoint_line_width_emu(width, "table border_width")
    return "".join(
        f'<a:{tag} w="{line_width}">{line}</a:{tag}>'
        for tag in ("lnL", "lnR", "lnT", "lnB")
    )


def _build_native_table(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    table_rows, col_count = _validate_table_payload(payload)
    header_rows = _table_header_rows(payload, len(table_rows))
    preserve_source_style = elem.get("data-pptx-native-source") == "pptx"

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
            if preserve_source_style:
                fill = (
                    _clean_hex(cell_data.get("fill"), "#FFFFFF")
                    if cell_data.get("fill") is not None else None
                )
                color = (
                    _clean_hex(cell_data.get("color"), "#000000")
                    if cell_data.get("color") is not None else None
                )
                align = str(cell_data.get("align") or "l")
            else:
                fill = _clean_hex(
                    cell_data.get("fill"),
                    header_fill if is_header else (
                        band_fill if row_idx % 2 == 0 and row_idx else body_fill
                    ),
                )
                color = _clean_hex(
                    cell_data.get("color"),
                    header_text if is_header else body_text,
                )
                align = str(cell_data.get("align") or ("ctr" if is_header else "l"))
            if align not in {"l", "ctr", "r"}:
                align = "l"
            text = "" if cell_data.get("text") is None else str(cell_data.get("text"))
            if preserve_source_style:
                bold = (
                    _table_bool(cell_data["bold"], "cell bold", default=False)
                    if "bold" in cell_data else None
                )
                cell_font_size = (
                    _font_size_hpt(cell_data.get("font_size"), 18)
                    if "font_size" in cell_data else None
                )
            else:
                bold = _table_bool(cell_data.get("bold"), "cell bold", default=is_header)
                cell_font_size = (
                    _font_size_hpt(cell_data.get("font_size"), 18)
                    if "font_size" in cell_data
                    else body_font_size
                )
                if is_header and "font_size" not in cell_data:
                    cell_font_size = header_font_size
            paragraph_props = f'<a:pPr algn="{align}"/>' if align != "l" else "<a:pPr/>"
            anchor_keys = {"valign", "vertical_align"}
            anchor_attr = ""
            if not preserve_source_style or anchor_keys.intersection(cell_data) or anchor_keys.intersection(style):
                anchor_attr = f' anchor="{_table_anchor(cell_data, style)}"'
            tc_pr_attrs = f'{anchor_attr}{_table_padding_attrs(cell_data, style)}'
            border_xml = _table_border_xml(cell_data, style)
            fill_xml = (
                f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
                if fill else ""
            )
            cells_xml.append(
                "<a:tc>"
                "<a:txBody><a:bodyPr/><a:lstStyle/>"
                f"<a:p>{paragraph_props}"
                f"{_table_text_run(text, color=color, bold=bold, font_size=cell_font_size, font_face=font_face)}"
                "</a:p></a:txBody>"
                f'<a:tcPr{tc_pr_attrs}>{border_xml}{fill_xml}</a:tcPr>'
                "</a:tc>"
            )
        rows_xml.append(f'<a:tr h="{row_heights[row_idx]}">{"".join(cells_xml)}</a:tr>')

    shape_id = ctx.next_id()
    first_row = _bool_attr(header_rows > 0)
    band_row = _bool_attr(_table_bool(style.get("band_row"), "style.band_row", default=True))
    table_style_id = style.get("table_style_id")
    if table_style_id is None and not preserve_source_style:
        table_style_id = "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"
    table_style_xml = (
        f'<a:tableStyleId>{_xml_escape(str(table_style_id))}</a:tableStyleId>'
        if table_style_id else ""
    )
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
{table_style_xml}
</a:tblPr>
<a:tblGrid>{grid_xml}</a:tblGrid>
{''.join(rows_xml)}
</a:tbl>
</a:graphicData>
</a:graphic>
</p:graphicFrame>'''
    return ShapeResult(xml=xml, bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))
