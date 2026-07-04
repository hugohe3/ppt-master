"""Classic native chart XML emitters."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.utils import detect_text_lang, px_to_emu, _xml_escape
from .chart_data import _DEFAULT_CHART_COLORS, _chart_list, _data_labels_config
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
    _number,
)


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
        line_width_xml = f' w="{max(px_to_emu(_number(line_width, "series line_width")), 1)}"'
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


def _data_label_position(value: Any, chart_type: str, grouping: str | None) -> str | None:
    if chart_type == "area":
        if value is not None:
            raise RuntimeError("Native PPTX area data labels do not support label position")
        return None
    is_stacked = chart_type in {"bar", "column"} and grouping in {"percentStacked", "stacked"}
    default = "ctr" if is_stacked else ("outEnd" if chart_type in {"bar", "column"} else "t")
    if value is None:
        return default
    aliases = {
        "above": "t",
        "bestfit": "bestFit",
        "center": "ctr",
        "inbase": "inBase",
        "insidebase": "inBase",
        "insideend": "inEnd",
        "inend": "inEnd",
        "outend": "outEnd",
        "outsideend": "outEnd",
    }
    position = aliases.get(_compact_key(value))
    if not position:
        raise RuntimeError(
            "Native PPTX chart data label position must be one of: "
            "above, best_fit, center, inside_base, inside_end, outside_end"
        )
    if chart_type in {"bar", "column"}:
        if position not in {"ctr", "inBase", "inEnd", "outEnd"}:
            raise RuntimeError(
                "Native PPTX bar/column data label position must be one of: "
                "center, inside_base, inside_end, outside_end"
            )
        if is_stacked and position == "outEnd":
            raise RuntimeError(
                "Native PPTX stacked bar/column data labels do not support outside_end"
            )
    elif chart_type == "line" and position not in {"bestFit", "ctr", "t"}:
        raise RuntimeError(
            "Native PPTX line data label position must be one of: above, best_fit, center"
        )
    return position


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


def _data_label_point_items(config: dict[str, Any], point_count: int) -> list[dict[str, Any]]:
    raw_points = config.get("points")
    if raw_points is None:
        return []
    items: list[dict[str, Any]] = []
    seen: set[int] = set()
    for item in _chart_list(raw_points, "data_labels.points"):
        if isinstance(item, dict):
            raw_index = item.get("idx")
            data = dict(item)
        else:
            raw_index = item
            data = {}
        if isinstance(raw_index, bool):
            raise RuntimeError("Native PPTX chart data_labels.points idx must be an integer")
        index_value = _number(raw_index, "data_labels.points idx")
        if not index_value.is_integer():
            raise RuntimeError("Native PPTX chart data_labels.points idx must be an integer")
        index = int(index_value)
        if index < 0 or index >= point_count:
            raise RuntimeError("Native PPTX chart data_labels.points idx is outside point range")
        if index in seen:
            raise RuntimeError("Native PPTX chart data_labels.points idx values must be unique")
        seen.add(index)
        data["idx"] = index
        items.append(data)
    return items


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
    point_items = _data_label_point_items(config, point_count)
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
        return f"<c:dLbls>{point_label_xml}<c:showLeaderLines val=\"0\"/></c:dLbls>"

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
        '<c:showLeaderLines val="0"/>'
        "</c:dLbls>"
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
    categories: list[str],
    series: list[dict[str, Any]],
    *,
    chart_type: str,
    grouping: str | None = None,
    line_style: str = "line",
    radar_marker_style: str | None = None,
    radar_style: str = "marker",
    colors: list[str],
    data_labels: dict[str, Any] | None = None,
    data_label_font_size: int = 900,
    data_label_color: str | None = None,
    data_label_font_face: str | None = None,
    start_column: int = 2,
    start_index: int = 0,
) -> str:
    parts: list[str] = []
    for offset, item in enumerate(series):
        index = start_index + offset
        column_index = offset + start_column
        fill_opacity = item.get("fill_opacity") if chart_type == "area" else None
        line_width = item.get("line_width") if chart_type in {"area", "line"} else None
        color_xml = _series_color_xml(
            _chart_color(colors, index),
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
                color_xml = _series_color_xml(_chart_color(colors, index), line=False)
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
            if chart_type in {"area", "bar", "column", "line"} else ""
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
    axis_tx_pr = _chart_tx_pr_xml(
        axis_font_size,
        chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    val_title_xml = _axis_title_xml(
        axis_titles.get("secondary_value"),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    # Hidden secondary category axis controls secondary area fill baseline.
    return (
        "<c:catAx>"
        f'<c:axId val="{cat_ax_id}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        '<c:delete val="1"/><c:axPos val="b"/><c:majorTickMark val="none"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        f"{axis_sp_pr}{axis_tx_pr}"
        f'<c:crossAx val="{val_ax_id}"/><c:crosses val="autoZero"/><c:auto val="1"/>'
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
    categories = chart_data["categories"]
    primary_cat_ax_id = "2068027336"
    primary_val_ax_id = "2113994440"
    secondary_cat_ax_id = "2080229232"
    secondary_val_ax_id = "2098941040"
    parts: list[str] = []

    for plot in sorted(chart_data["plots"], key=_combo_plot_layer):
        chart_type = plot["type"]
        axis = plot.get("axis", "primary")
        cat_ax_id = secondary_cat_ax_id if axis == "secondary" else primary_cat_ax_id
        val_ax_id = secondary_val_ax_id if axis == "secondary" else primary_val_ax_id
        start_index = int(plot.get("start_index", 0))
        grouping = plot.get("grouping") or ("clustered" if chart_type == "column" else "standard")
        ser_xml = _series_xml(
            categories,
            plot["series"],
            chart_type=chart_type,
            grouping=grouping,
            colors=colors,
            data_labels=_data_labels_config(plot),
            data_label_font_size=axis_font_size,
            data_label_color=chart_style.get("text_color"),
            data_label_font_face=chart_style.get("font_face"),
            line_style=plot.get("line_style", "line"),
            start_column=2 + start_index,
            start_index=start_index,
        )
        if chart_type == "column":
            parts.append(_bar_chart_group_xml(
                chart_type,
                grouping,
                ser_xml,
                cat_ax_id=cat_ax_id,
                val_ax_id=val_ax_id,
                vary_colors=any(item.get("point_colors") for item in plot["series"]),
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
        data_labels=chart_data.get("data_labels"),
        data_label_font_size=axis_font_size,
        data_label_color=chart_style.get("text_color"),
        data_label_font_face=chart_style.get("font_face"),
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
            show_value_axis_labels=chart_data.get("show_value_axis_labels", True),
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
) -> str:
    cat_pos = "l" if chart_type == "bar" else "b"
    val_pos = "b" if chart_type == "bar" else "l"
    val_num_fmt = (
        '<c:numFmt formatCode="0%" sourceLinked="0"/>'
        if grouping == "percentStacked"
        else ""
    )
    val_tick_label_pos = "nextTo" if show_value_axis_labels else "none"
    axis_sp_pr = _chart_line_sp_pr_xml(chart_style.get("axis_color"))
    axis_tx_pr = _chart_tx_pr_xml(
        axis_font_size,
        chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    cat_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("category"), axis_titles.get("x")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    val_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("value"), axis_titles.get("y")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
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
        f'<c:tickLblPos val="{val_tick_label_pos}"/>'
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
    axis_tx_pr = _chart_tx_pr_xml(
        axis_font_size,
        chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    cat_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("category"), axis_titles.get("x")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
    )
    val_title_xml = _axis_title_xml(
        _first_present(axis_titles.get("value"), axis_titles.get("y")),
        font_size=axis_title_font_size,
        color=chart_style.get("text_color"),
        font_face=chart_style.get("font_face"),
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
