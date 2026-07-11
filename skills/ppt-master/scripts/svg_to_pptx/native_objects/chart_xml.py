"""Classic native chart XML emitters."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.utils import detect_text_lang, _xml_escape
from .chart_data import (
    _DEFAULT_CHART_COLORS,
    _category_axis_is_date,
    _chart_list,
    _data_label_position,
    _data_label_point_items,
    _data_labels_config,
)
from .chart_style import (
    _alpha_xml,
    _axis_title_xml,
    _axis_titles,
    _chart_area_sp_pr_xml,
    _chart_line_sp_pr_xml,
    _chart_text_entry_color,
    _chart_text_entry_font_face,
    _chart_text_entry_font_size,
    _chart_text_entry,
    _chart_text_sizes,
    _chart_tx_pr_xml,
    _classic_chart_style,
    _font_face_xml,
    _major_gridlines_xml,
)
from .marker_common import (
    PACKAGE_REL_TYPE,
    _bool_attr,
    _chart_bool,
    _clean_hex,
    _compact_key,
    _excel_col,
    _first_present,
    _font_size_hpt,
    _hex_or_none,
    _powerpoint_line_width_emu,
)


def _string_cache(values: list[str]) -> str:
    points = "".join(
        f'<c:pt idx="{idx}"><c:v>{_xml_escape(value)}</c:v></c:pt>'
        for idx, value in enumerate(values)
    )
    return f'<c:strCache><c:ptCount val="{len(values)}"/>{points}</c:strCache>'


def _number_cache(
    values: list[int | float],
    number_format: str = "General",
) -> str:
    points = "".join(
        f'<c:pt idx="{idx}"><c:v>{value}</c:v></c:pt>'
        for idx, value in enumerate(values)
    )
    return (
        f'<c:numCache><c:formatCode>{_xml_escape(number_format)}</c:formatCode>'
        f'<c:ptCount val="{len(values)}"/>{points}</c:numCache>'
    )


def _category_reference_xml(
    categories: list[Any],
    *,
    column_index: int = 1,
    numeric: bool,
    number_format: str | None = None,
) -> str:
    reference_tag = "numRef" if numeric else "strRef"
    cache = (
        _number_cache(categories, number_format or "General")
        if numeric
        else _string_cache([str(value) for value in categories])
    )
    return (
        f"<c:cat><c:{reference_tag}>"
        f"<c:f>Sheet1!${_excel_col(column_index)}$2:"
        f"${_excel_col(column_index)}${len(categories) + 1}</c:f>"
        f"{cache}"
        f"</c:{reference_tag}></c:cat>"
    )


def _series_color_xml(
    color: str | None,
    *,
    line: bool = True,
    fill_opacity: Any = None,
    line_width: Any = None,
) -> str:
    if not color:
        return ""
    clean = _clean_hex(color, "#4472C4")
    alpha_xml = _alpha_xml(fill_opacity, "series fill_opacity")
    line_width_xml = ""
    if line_width is not None:
        line_width_xml = (
            f' w="{_powerpoint_line_width_emu(line_width, "series line_width")}"'
        )
    line_xml = (
        f'<a:ln{line_width_xml}><a:solidFill><a:srgbClr val="{clean}"/></a:solidFill></a:ln>'
        if line else '<a:ln><a:noFill/></a:ln>'
    )
    return (
        "<c:spPr>"
        f'<a:solidFill><a:srgbClr val="{clean}">{alpha_xml}</a:srgbClr></a:solidFill>'
        f'{line_xml}'
        "</c:spPr>"
    )


def _data_label_flags_xml(config: dict[str, Any]) -> str:
    show_value = _chart_bool(
        _first_present(config.get("show_value"), config.get("showValue"), config.get("value")),
        True,
    )
    show_category = _chart_bool(
        _first_present(config.get("show_category"), config.get("showCategory"), config.get("category")),
        False,
    )
    show_series = _chart_bool(
        _first_present(config.get("show_series"), config.get("showSeries"), config.get("series")),
        False,
    )
    show_percent = _chart_bool(
        _first_present(config.get("show_percent"), config.get("showPercent"), config.get("percent")),
        False,
    )
    return (
        '<c:showLegendKey val="0"/>'
        f'<c:showVal val="{_bool_attr(show_value)}"/>'
        f'<c:showCatName val="{_bool_attr(show_category)}"/>'
        f'<c:showSerName val="{_bool_attr(show_series)}"/>'
        f'<c:showPercent val="{_bool_attr(show_percent)}"/>'
        '<c:showBubbleSize val="0"/>'
    )


def _data_labels_xml(
    config: dict[str, Any] | None,
    *,
    chart_type: str,
    grouping: str | None,
    point_count: int,
    font_size: int,
    default_color: str | None,
    default_font_face: str | None,
) -> str:
    if config is None:
        return ""
    show_leader_lines = _chart_bool(
        _first_present(
            config.get("show_leader_lines"),
            config.get("showLeaderLines"),
        ),
        False,
    )
    leader_lines_xml = f'<c:showLeaderLines val="{_bool_attr(show_leader_lines)}"/>'
    position = _data_label_position(config.get("position"), chart_type, grouping)
    raw_font_size = _first_present(config.get("font_size"), config.get("fontSize"))
    label_font_size = _font_size_hpt(raw_font_size, 12) if raw_font_size is not None else font_size
    color = _hex_or_none(config.get("color")) or default_color
    bold = _chart_bool(config.get("bold"), False)
    font_face = _chart_text_entry_font_face(config, default_font_face)
    tx_pr_xml = _chart_tx_pr_xml(label_font_size, color, bold=bold, font_face=font_face)
    num_fmt = _first_present(
        config.get("number_format"),
        config.get("numberFormat"),
        config.get("format"),
    )
    num_fmt_xml = (
        f'<c:numFmt formatCode="{_xml_escape(str(num_fmt))}" sourceLinked="0"/>'
        if num_fmt else ""
    )
    flags_xml = _data_label_flags_xml(config)
    point_items = _data_label_point_items(
        config,
        chart_type,
        grouping,
        point_count,
    )
    if point_items:
        selected_items = {int(item["idx"]): item for item in point_items}
        point_label_xml = ""
        for idx in range(point_count):
            item = selected_items.get(idx)
            if item is None:
                point_label_xml += f'<c:dLbl><c:idx val="{idx}"/><c:delete val="1"/></c:dLbl>'
                continue
            item_font_size_raw = _first_present(item.get("font_size"), item.get("fontSize"))
            item_font_size = (
                _font_size_hpt(item_font_size_raw, 12)
                if item_font_size_raw is not None else label_font_size
            )
            item_color = _hex_or_none(item.get("color")) or color
            item_font_face = _chart_text_entry_font_face(item, font_face)
            item_position = _data_label_position(
                _first_present(item.get("position"), config.get("position")),
                chart_type,
                grouping,
            )
            item_num_fmt = _first_present(
                item.get("number_format"),
                item.get("numberFormat"),
                item.get("format"),
                num_fmt,
            )
            item_num_fmt_xml = (
                f'<c:numFmt formatCode="{_xml_escape(str(item_num_fmt))}" sourceLinked="0"/>'
                if item_num_fmt else ""
            )
            item_bold = _chart_bool(item.get("bold"), bold)
            item_position_xml = f'<c:dLblPos val="{item_position}"/>' if item_position else ""
            point_label_xml += (
                f'<c:dLbl><c:idx val="{idx}"/>'
                f"{item_num_fmt_xml}"
                f"{_chart_tx_pr_xml(item_font_size, item_color, bold=item_bold, font_face=item_font_face)}"
                f"{item_position_xml}"
                f"{_data_label_flags_xml({**config, **item})}"
                "</c:dLbl>"
            )
        return f"<c:dLbls>{point_label_xml}{leader_lines_xml}</c:dLbls>"

    label_colors = [
        _clean_hex(item, "#404040")
        for item in _chart_list(
            _first_present(config.get("colors"), config.get("label_colors"), config.get("labelColors")),
            "data_labels.colors",
        )
    ]
    if label_colors and len(label_colors) != point_count:
        raise RuntimeError("Native PPTX chart data_labels.colors must match point count")
    point_label_xml = ""
    for idx, label_color in enumerate(label_colors):
        position_xml = f'<c:dLblPos val="{position}"/>' if position else ""
        point_label_xml += (
            f'<c:dLbl><c:idx val="{idx}"/>'
            f"{num_fmt_xml}"
            f"{_chart_tx_pr_xml(label_font_size, label_color, bold=bold, font_face=font_face)}"
            f"{position_xml}"
            f"{flags_xml}"
            "</c:dLbl>"
        )
    position_xml = f'<c:dLblPos val="{position}"/>' if position else ""
    return (
        "<c:dLbls>"
        f"{point_label_xml}"
        f"{num_fmt_xml}{tx_pr_xml}"
        f"{position_xml}"
        f"{flags_xml}"
        f'{leader_lines_xml}'
        "</c:dLbls>"
    )


def _series_scoped_data_labels(config: dict[str, Any] | None) -> bool:
    """Return whether point-level overrides require a series ``c:dLbls``."""
    if config is None:
        return False
    return any(
        bool(config.get(key))
        for key in ("points", "colors", "label_colors", "labelColors")
    )


def _chart_color(colors: list[str], index: int) -> str:
    if index < len(colors):
        return colors[index]
    return _DEFAULT_CHART_COLORS[index % len(_DEFAULT_CHART_COLORS)]


def _data_point_colors_xml(
    count: int,
    colors: list[str],
    *,
    disable_negative_invert: bool = False,
) -> str:
    invert_xml = '<c:invertIfNegative val="0"/>' if disable_negative_invert else ""
    return "".join(
        f'<c:dPt><c:idx val="{idx}"/>{invert_xml}'
        f'{_series_color_xml(_chart_color(colors, idx))}</c:dPt>'
        for idx in range(count)
    )


def _marker_xml(symbol: str | None) -> str:
    if not symbol:
        return ""
    if symbol == "none":
        return '<c:marker><c:symbol val="none"/></c:marker>'
    return f'<c:marker><c:symbol val="{_xml_escape(symbol)}"/></c:marker>'


def _series_xml(
    categories: list[Any],
    series: list[dict[str, Any]],
    *,
    chart_type: str,
    grouping: str | None = None,
    line_style: str = "line",
    radar_marker_style: str | None = None,
    radar_style: str = "marker",
    colors: list[str],
    category_is_numeric: bool = False,
    category_number_format: str | None = None,
    data_labels: dict[str, Any] | None = None,
    data_label_font_size: int = 900,
    data_label_color: str | None = None,
    data_label_font_face: str | None = None,
    category_column: int = 1,
    color_start_index: int | None = None,
    series_indices: list[int] | None = None,
    start_column: int = 2,
    start_index: int = 0,
) -> str:
    parts: list[str] = []
    category_xml = _category_reference_xml(
        categories,
        column_index=category_column,
        numeric=category_is_numeric,
        number_format=category_number_format,
    )
    for offset, item in enumerate(series):
        index = (
            series_indices[offset]
            if series_indices is not None
            else start_index + offset
        )
        color_index = (
            color_start_index
            if color_start_index is not None
            else start_index
        ) + offset
        column_index = offset + start_column
        fill_opacity = item.get("fill_opacity") if chart_type == "area" else None
        line_width = item.get("line_width") if chart_type in {"area", "line"} else None
        color_xml = _series_color_xml(
            _chart_color(colors, color_index),
            fill_opacity=fill_opacity,
            line_width=line_width,
        )
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
            point_colors_xml = _data_point_colors_xml(
                point_count,
                item.get("point_colors") or colors,
            )
        elif chart_type in {"bar", "column"} and item.get("point_colors"):
            point_colors_xml = _data_point_colors_xml(
                len(item["values"]),
                item["point_colors"],
                disable_negative_invert=True,
            )
        if chart_type == "line":
            marker_xml = _marker_xml("circle" if line_style == "lineMarker" else "none")
            smooth_xml = '<c:smooth val="0"/>'
        if chart_type == "radar":
            if radar_style == "filled":
                color_xml = _series_color_xml(
                    _chart_color(colors, color_index),
                    line=False,
                )
            marker_xml = _marker_xml(radar_marker_style)
        invert_xml = '<c:invertIfNegative val="0"/>' if chart_type in {"bar", "column"} else ""
        data_labels_xml = (
            _data_labels_xml(
                data_labels,
                chart_type=chart_type,
                grouping=grouping,
                point_count=len(item["values"]),
                font_size=data_label_font_size,
                default_color=data_label_color,
                default_font_face=data_label_font_face,
            )
            if _series_scoped_data_labels(data_labels)
            and chart_type in {"area", "bar", "column", "line"}
            else ""
        )
        parts.append(
            "<c:ser>"
            f'<c:idx val="{index}"/><c:order val="{index}"/>'
            "<c:tx><c:strRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$1</c:f>"
            f"{_string_cache([str(item['name'])])}"
            "</c:strRef></c:tx>"
            f"{color_xml}{invert_xml}{marker_xml}{point_colors_xml}"
            f"{data_labels_xml}"
            f"{category_xml}"
            "<c:val><c:numRef>"
            f"<c:f>Sheet1!${_excel_col(column_index)}$2:${_excel_col(column_index)}${len(categories) + 1}</c:f>"
            f"{_number_cache(item['values'])}"
            "</c:numRef></c:val>"
            f"{smooth_xml}"
            "</c:ser>"
        )
    return "".join(parts)


def _chart_title_paragraph_xml(
    text: str,
    *,
    font_size: int,
    color: str | None = None,
    font_face: str | None = None,
) -> str:
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    lang = detect_text_lang(text)
    return (
        f'<a:p><a:r><a:rPr lang="{lang}" sz="{font_size}">{fill_xml}{_font_face_xml(font_face)}</a:rPr>'
        f"<a:t>{_xml_escape(text)}</a:t></a:r></a:p>"
    )


def _chart_title_xml(
    title: Any,
    *,
    font_size: int,
    color: str | None = None,
    subtitle: Any = None,
    subtitle_font_size: int | None = None,
    font_face: str | None = None,
) -> str:
    title_entry = _chart_text_entry(title)
    subtitle_entry = _chart_text_entry(subtitle)
    if title_entry is None and subtitle_entry is None:
        return '<c:autoTitleDeleted val="1"/>'
    paragraphs = []
    if title_entry is not None:
        text, item = title_entry
        paragraphs.append(_chart_title_paragraph_xml(
            text,
            font_size=_chart_text_entry_font_size(item, font_size),
            color=_chart_text_entry_color(item, color),
            font_face=_chart_text_entry_font_face(item, font_face),
        ))
    if subtitle_entry is not None:
        text, item = subtitle_entry
        paragraphs.append(_chart_title_paragraph_xml(
            text,
            font_size=_chart_text_entry_font_size(item, subtitle_font_size or font_size),
            color=_chart_text_entry_color(item, color),
            font_face=_chart_text_entry_font_face(item, font_face),
        ))
    return (
        "<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/>"
        f"{''.join(paragraphs)}"
        "</c:rich></c:tx><c:layout/></c:title>"
        '<c:autoTitleDeleted val="0"/>'
    )


def _chart_legend_xml(
    payload: dict[str, Any],
    *,
    font_size: int,
    color: str | None = None,
    font_face: str | None = None,
) -> str:
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
        f'{_chart_tx_pr_xml(font_size, color, font_face=font_face)}'
        '</c:legend>'
    )


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
    vary_colors: bool = False,
    data_labels_xml: str = "",
) -> str:
    bar_dir = "bar" if chart_type == "bar" else "col"
    vary_colors_xml = '<c:varyColors val="1"/>' if vary_colors else '<c:varyColors val="0"/>'
    overlap_xml = (
        '<c:overlap val="100"/>'
        if grouping in {"stacked", "percentStacked"}
        else ""
    )
    return (
        "<c:barChart>"
        f'<c:barDir val="{bar_dir}"/><c:grouping val="{grouping}"/>'
        f"{vary_colors_xml}"
        f"{ser_xml}"
        f"{data_labels_xml}"
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
    data_labels_xml: str = "",
) -> str:
    tag = "lineChart" if chart_type == "line" else "areaChart"
    line_tail_xml = '<c:marker val="1"/><c:smooth val="0"/>' if chart_type == "line" else ""
    return (
        f'<c:{tag}><c:grouping val="{grouping}"/><c:varyColors val="0"/>'
        f"{ser_xml}"
        f"{data_labels_xml}"
        f"{line_tail_xml}"
        f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
        f"</c:{tag}>"
    )


def _axis_scaling_xml(config: dict[str, Any]) -> str:
    orientation = "maxMin" if config.get("reverse") else "minMax"
    maximum = (
        f'<c:max val="{config["maximum"]}"/>'
        if config.get("maximum") is not None else ""
    )
    minimum = (
        f'<c:min val="{config["minimum"]}"/>'
        if config.get("minimum") is not None else ""
    )
    return f'<c:scaling><c:orientation val="{orientation}"/>{maximum}{minimum}</c:scaling>'


def _axis_position(config: dict[str, Any], default: str) -> str:
    return {
        "bottom": "b",
        "left": "l",
        "right": "r",
        "top": "t",
    }.get(str(config.get("position") or ""), default)


def _axis_label_position(config: dict[str, Any], default: str) -> str:
    return {
        "high": "high",
        "low": "low",
        "next_to": "nextTo",
        "none": "none",
    }.get(str(config.get("label_position") or ""), default)


def _axis_number_format_xml(
    config: dict[str, Any],
    default: str | None = None,
) -> str:
    number_format = config.get("number_format", default)
    if number_format is None:
        return ""
    return f'<c:numFmt formatCode="{_xml_escape(str(number_format))}" sourceLinked="0"/>'


def _axis_major_gridlines_xml(
    config: dict[str, Any],
    *,
    default: bool,
    color: str | None,
) -> str:
    enabled = config.get("major_gridlines", default)
    return _major_gridlines_xml(color) if enabled else ""


def _axis_pair_xml(
    cat_ax_id: str,
    val_ax_id: str,
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
    chart_type: str,
    grouping: str | None,
    show_value_axis_labels: bool,
    axes: dict[str, dict[str, Any]],
    secondary: bool,
) -> str:
    category_role = "secondary_category" if secondary else "category"
    value_role = "secondary_value" if secondary else "value"
    category = axes.get(category_role, {})
    value = axes.get(value_role, {})
    category_kind = str(category.get("kind") or ("date" if chart_type == "stock" else "text"))
    category_tag = "dateAx" if category_kind == "date" else "catAx"
    default_cat_pos = "l" if chart_type == "bar" else "b"
    default_val_pos = "r" if secondary else ("b" if chart_type == "bar" else "l")
    cat_pos = _axis_position(category, default_cat_pos)
    val_pos = _axis_position(value, default_val_pos)
    cat_delete = _bool_attr(not category.get("visible", not secondary))
    val_delete = _bool_attr(not value.get("visible", True))
    cat_tick_label_pos = _axis_label_position(category, "nextTo")
    default_val_tick = "nextTo" if show_value_axis_labels else "none"
    val_tick_label_pos = _axis_label_position(value, default_val_tick)
    default_value_format = "0%" if grouping == "percentStacked" else None
    cat_number_format = _axis_number_format_xml(
        category,
        "m/d/yyyy" if category_kind == "date" else None,
    )
    val_number_format = _axis_number_format_xml(value, default_value_format)
    axis_sp_pr = _chart_line_sp_pr_xml(chart_style.get("axis_color"))
    axis_tx_pr = _chart_tx_pr_xml(
        axis_font_size,
        chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    cat_title_xml = "" if secondary else _axis_title_xml(
        _first_present(axis_titles.get("category"), axis_titles.get("x")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    value_title_key = "secondary_value" if secondary else "value"
    value_title = axis_titles.get(value_title_key)
    if not secondary:
        value_title = _first_present(value_title, axis_titles.get("y"))
    val_title_xml = _axis_title_xml(
        value_title,
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    cat_gridlines = _axis_major_gridlines_xml(
        category,
        default=False,
        color=chart_style.get("grid_color"),
    )
    val_gridlines = _axis_major_gridlines_xml(
        value,
        default=not secondary,
        color=chart_style.get("grid_color"),
    )
    if category_kind == "date":
        category_tail = '<c:auto val="1"/><c:lblOffset val="100"/><c:baseTimeUnit val="days"/>'
    else:
        category_tail = (
            '<c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/>'
            '<c:noMultiLvlLbl val="0"/>'
        )
    is_combo = chart_type == "combo"
    cross_between = ""
    if chart_type == "area" and category_kind == "date":
        cross_between = '<c:crossBetween val="midCat"/>'
    elif chart_type == "stock" or is_combo:
        cross_between = '<c:crossBetween val="between"/>'
    major_unit = (
        f'<c:majorUnit val="{value["major_unit"]}"/>'
        if value.get("major_unit") is not None else ""
    )
    value_crosses = "max" if secondary else "autoZero"
    return (
        f"<c:{category_tag}>"
        f'<c:axId val="{cat_ax_id}"/>{_axis_scaling_xml(category)}'
        f'<c:delete val="{cat_delete}"/><c:axPos val="{cat_pos}"/>'
        f"{cat_gridlines}{cat_title_xml}{cat_number_format}"
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        f'<c:tickLblPos val="{cat_tick_label_pos}"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{val_ax_id}"/><c:crosses val="autoZero"/>{category_tail}'
        f"</c:{category_tag}>"
        "<c:valAx>"
        f'<c:axId val="{val_ax_id}"/>{_axis_scaling_xml(value)}'
        f'<c:delete val="{val_delete}"/><c:axPos val="{val_pos}"/>'
        f"{val_gridlines}{val_title_xml}{val_number_format}"
        '<c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
        f'<c:tickLblPos val="{val_tick_label_pos}"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{cat_ax_id}"/><c:crosses val="{value_crosses}"/>'
        f"{cross_between}{major_unit}"
        "</c:valAx>"
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
    axes: dict[str, dict[str, Any]] | None = None,
) -> str:
    return _axis_pair_xml(
        cat_ax_id,
        val_ax_id,
        axis_font_size=axis_font_size,
        axis_title_font_size=axis_title_font_size,
        axis_titles=axis_titles,
        chart_style=chart_style,
        chart_type="combo",
        grouping=grouping,
        show_value_axis_labels=True,
        axes=axes or {},
        secondary=True,
    )


def _combo_axis_grouping(plots: list[dict[str, Any]], axis: str) -> str | None:
    for plot in plots:
        if plot.get("axis") == axis and plot.get("grouping") == "percentStacked":
            return "percentStacked"
    return None


def _combo_plot_layer(plot: dict[str, Any]) -> int:
    return {
        "area": 0,
        "column": 1,
        "line": 2,
    }.get(str(plot.get("type")), 1)


def _combo_plot_xml(
    chart_data: dict[str, Any],
    colors: list[str],
    *,
    axis_font_size: int,
    axis_title_font_size: int,
    axis_titles: dict[str, Any],
    chart_style: dict[str, str | None],
) -> str:
    axes = chart_data.get("axes") or {}
    primary_cat_ax_id = "2068027336"
    primary_val_ax_id = "2113994440"
    secondary_cat_ax_id = "2080229232"
    secondary_val_ax_id = "2098941040"
    parts: list[str] = []

    for plot in sorted(chart_data["plots"], key=_combo_plot_layer):
        categories = plot["categories"]
        category_is_numeric = bool(plot.get("category_is_numeric"))
        chart_type = plot["type"]
        axis = plot.get("axis", "primary")
        cat_ax_id = secondary_cat_ax_id if axis == "secondary" else primary_cat_ax_id
        val_ax_id = secondary_val_ax_id if axis == "secondary" else primary_val_ax_id
        category_role = "secondary_category" if axis == "secondary" else "category"
        category_number_format = axes.get(category_role, {}).get("number_format")
        start_index = int(plot.get("start_index", 0))
        grouping = plot.get("grouping") or ("clustered" if chart_type == "column" else "standard")
        ser_xml = _series_xml(
            categories,
            plot["series"],
            chart_type=chart_type,
            grouping=grouping,
            colors=colors,
            category_is_numeric=category_is_numeric,
            category_number_format=category_number_format,
            data_labels=_data_labels_config(plot),
            data_label_font_size=axis_font_size,
            data_label_color=chart_style.get("text_color"),
            data_label_font_face=chart_style.get("font_face"),
            line_style=plot.get("line_style", "line"),
            category_column=int(plot.get("category_column", 1)),
            color_start_index=start_index,
            series_indices=plot.get("series_indices"),
            start_column=int(plot.get("start_column", 2 + start_index)),
            start_index=start_index,
        )
        data_labels = _data_labels_config(plot)
        data_labels_xml = (
            _data_labels_xml(
                data_labels,
                chart_type=chart_type,
                grouping=grouping,
                point_count=len(plot["series"][0]["values"]),
                font_size=axis_font_size,
                default_color=chart_style.get("text_color"),
                default_font_face=chart_style.get("font_face"),
            )
            if not _series_scoped_data_labels(data_labels)
            else ""
        )
        if chart_type == "column":
            parts.append(_bar_chart_group_xml(
                chart_type,
                grouping,
                ser_xml,
                cat_ax_id=cat_ax_id,
                val_ax_id=val_ax_id,
                vary_colors=any(item.get("point_colors") for item in plot["series"]),
                data_labels_xml=data_labels_xml,
            ))
        elif chart_type in {"area", "line"}:
            parts.append(_line_area_chart_group_xml(
                chart_type,
                grouping,
                ser_xml,
                cat_ax_id=cat_ax_id,
                val_ax_id=val_ax_id,
                data_labels_xml=data_labels_xml,
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
        chart_type="combo",
        grouping=_combo_axis_grouping(chart_data["plots"], "primary"),
        axes=axes,
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
            axes=axes,
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
        stock_axes = chart_data.get("axes") or {}
        stock_category_format = None
        if stock_axes:
            stock_category_format = (
                stock_axes.get("category", {}).get("number_format")
                or "m/d/yyyy"
            )
        stock_series_xml = _stock_series_xml(
            categories,
            series,
            colors=colors,
            category_number_format=stock_category_format,
        )
        axes_xml = _stock_axis_xml(
            stock_cat_ax_id,
            stock_val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            axes=stock_axes,
        )
        return (
            "<c:stockChart>"
            f"{stock_series_xml}"
            '<c:hiLowLines/>'
            '<c:upDownBars><c:gapWidth val="150"/><c:upBars/><c:downBars/></c:upDownBars>'
            f'<c:axId val="{stock_cat_ax_id}"/><c:axId val="{stock_val_ax_id}"/>'
            "</c:stockChart>"
            f"{axes_xml}"
        )
    series_grouping = chart_data.get("grouping") or (
        "clustered" if chart_type in {"bar", "column"} else "standard"
    )
    ser_xml = _series_xml(
        categories,
        series,
        chart_type=chart_type,
        grouping=series_grouping,
        line_style=chart_data.get("line_style", "line"),
        radar_marker_style=chart_data.get("radar_marker_style"),
        radar_style=chart_data.get("radar_style", "marker"),
        colors=colors,
        category_is_numeric=_category_axis_is_date(chart_data.get("axes") or {}),
        category_number_format=(
            (chart_data.get("axes") or {})
            .get("category", {})
            .get(
                "number_format",
                "m/d/yyyy"
                if _category_axis_is_date(chart_data.get("axes") or {})
                else None,
            )
        ),
        data_labels=chart_data.get("data_labels"),
        data_label_font_size=axis_font_size,
        data_label_color=chart_style.get("text_color"),
        data_label_font_face=chart_style.get("font_face"),
    )
    data_labels_xml = (
        _data_labels_xml(
            chart_data.get("data_labels"),
            chart_type=chart_type,
            grouping=series_grouping,
            point_count=len(series[0]["values"]),
            font_size=axis_font_size,
            default_color=chart_style.get("text_color"),
            default_font_face=chart_style.get("font_face"),
        )
        if chart_type in {"area", "bar", "column", "line"}
        and not _series_scoped_data_labels(chart_data.get("data_labels"))
        else ""
    )

    if chart_type in {"bar", "column"}:
        bar_dir = "bar" if chart_type == "bar" else "col"
        grouping = series_grouping
        axes_xml = _axis_xml(
            cat_ax_id,
            val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            chart_type=chart_type,
            grouping=grouping,
            show_value_axis_labels=chart_data.get("show_value_axis_labels", True),
            axes=chart_data.get("axes") or {},
        )
        overlap_xml = (
            '<c:overlap val="100"/>'
            if grouping in {"stacked", "percentStacked"}
            else ""
        )
        vary_colors_xml = (
            '<c:varyColors val="1"/>'
            if any(item.get("point_colors") for item in series)
            else '<c:varyColors val="0"/>'
        )
        return (
            "<c:barChart>"
            f'<c:barDir val="{bar_dir}"/><c:grouping val="{grouping}"/>'
            f"{vary_colors_xml}"
            f"{ser_xml}"
            f"{data_labels_xml}"
            '<c:gapWidth val="150"/>'
            f"{overlap_xml}"
            f'<c:axId val="{cat_ax_id}"/><c:axId val="{val_ax_id}"/>'
            "</c:barChart>"
            f"{axes_xml}"
        )
    if chart_type in {"line", "area"}:
        tag = "lineChart" if chart_type == "line" else "areaChart"
        grouping = series_grouping
        axes_xml = _axis_xml(
            cat_ax_id,
            val_ax_id,
            axis_font_size=axis_font_size,
            axis_title_font_size=axis_title_font_size,
            axis_titles=axis_titles,
            chart_style=chart_style,
            chart_type=chart_type,
            grouping=grouping,
            show_value_axis_labels=chart_data.get("show_value_axis_labels", True),
            axes=chart_data.get("axes") or {},
        )
        line_tail_xml = '<c:marker val="1"/><c:smooth val="0"/>' if chart_type == "line" else ""
        return (
            f'<c:{tag}><c:grouping val="{grouping}"/><c:varyColors val="0"/>'
            f"{ser_xml}"
            f"{data_labels_xml}"
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
            show_value_axis_labels=chart_data.get("show_value_axis_labels", True),
            axes=chart_data.get("axes") or {},
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
    show_value_axis_labels: bool = True,
    axes: dict[str, dict[str, Any]] | None = None,
) -> str:
    return _axis_pair_xml(
        cat_ax_id,
        val_ax_id,
        axis_font_size=axis_font_size,
        axis_title_font_size=axis_title_font_size,
        axis_titles=axis_titles,
        chart_style=chart_style,
        chart_type=chart_type,
        grouping=grouping,
        show_value_axis_labels=show_value_axis_labels,
        axes=axes or {},
        secondary=False,
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
    axis_tx_pr = _chart_tx_pr_xml(
        axis_font_size,
        chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    x_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("x"), axis_titles.get("category")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    y_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("y"), axis_titles.get("value")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
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
    category_number_format: str | None = None,
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
            f"{_number_cache(categories, category_number_format or 'General')}"
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
    axes: dict[str, dict[str, Any]] | None = None,
) -> str:
    normalized_axes = dict(axes or {})
    normalized_axes.setdefault("category", {"kind": "date", "position": "bottom"})
    return _axis_pair_xml(
        cat_ax_id,
        val_ax_id,
        axis_font_size=axis_font_size,
        axis_title_font_size=axis_title_font_size,
        axis_titles=axis_titles,
        chart_style=chart_style,
        chart_type="stock",
        grouping=None,
        show_value_axis_labels=True,
        axes=normalized_axes,
        secondary=False,
    )


def _chart_xml(
    elem: ET.Element,
    payload: dict[str, Any],
    *,
    chart_rels_id: str,
    chart_data: dict[str, Any],
    inherited_styles: dict[str, str] | None = None,
) -> bytes:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    colors = (
        [_clean_hex(color, "#4472C4") for color in style.get("colors", [])]
        if isinstance(style.get("colors"), list)
        else []
    )
    text_sizes = _chart_text_sizes(payload, elem, inherited_styles)
    axis_titles = _axis_titles(payload)
    chart_style = _classic_chart_style(payload, elem, inherited_styles)
    plot_xml = _chart_plot_xml(
        chart_data,
        colors,
        axis_font_size=text_sizes["axis"],
        axis_title_font_size=text_sizes["axis_title"],
        axis_titles=axis_titles,
        chart_style=chart_style,
    )
    title_xml = _chart_title_xml(
        payload.get("title"),
        font_size=text_sizes["title"],
        color=chart_style.get("text_color"),
        subtitle=payload.get("subtitle"),
        subtitle_font_size=text_sizes["subtitle"],
        font_face=chart_style.get("font_face"),
    )
    legend_xml = _chart_legend_xml(
        payload,
        font_size=text_sizes["legend"],
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<c:date1904 val="0"/>
<c:lang val="en-US"/>
<c:chart>
{title_xml}
<c:plotArea><c:layout/>{plot_xml}{_chart_area_sp_pr_xml(chart_style.get("plot_fill"))}</c:plotArea>
{legend_xml}
<c:plotVisOnly val="1"/>
<c:dispBlanksAs val="gap"/>
</c:chart>
{_chart_area_sp_pr_xml(chart_style.get("chart_fill"))}
{_chart_tx_pr_xml(text_sizes["base"], chart_style.get("text_color"), font_face=chart_style.get("font_face"))}
<c:externalData r:id="{chart_rels_id}"><c:autoUpdate val="0"/></c:externalData>
</c:chartSpace>'''
    return xml.encode("utf-8")


def _chart_rels_xml(workbook_target: str) -> bytes:
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="{PACKAGE_REL_TYPE}" Target="{_xml_escape(workbook_target)}"/>
</Relationships>'''
    return xml.encode("utf-8")
