"""Native chart metadata normalization."""

from __future__ import annotations

import math
from typing import Any

from .marker_common import (
    _chart_bool,
    _clean_hex,
    _compact_key,
    _first_present,
    _hex_or_none,
    _number,
    _powerpoint_line_width_emu,
)


def _chart_number(value: Any) -> int | float:
    if isinstance(value, bool):
        raise RuntimeError("Native PPTX chart values must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError("Native PPTX chart value is not numeric") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"Native PPTX chart value must be finite: {value}")
    return int(number) if number.is_integer() else number


def _chart_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError(f"Native PPTX chart {field_name} must be a list")
    return value


def _data_labels_config(payload: dict[str, Any]) -> dict[str, Any] | None:
    raw = _first_present(payload.get("data_labels"), payload.get("dataLabels"))
    if raw is None:
        return None
    if isinstance(raw, bool):
        return {} if raw else None
    if not isinstance(raw, dict):
        raise RuntimeError("Native PPTX chart data_labels must be a boolean or object")
    return raw


def _data_label_position(value: Any, chart_type: str, grouping: str | None) -> str | None:
    """Normalize and validate a label position for its chart plot."""
    if chart_type == "area":
        if value is not None:
            raise RuntimeError("Native PPTX area data labels do not support label position")
        return None
    is_stacked = chart_type in {"bar", "column"} and grouping in {
        "percentStacked", "stacked",
    }
    default = "ctr" if is_stacked else (
        "outEnd" if chart_type in {"bar", "column"} else "t"
    )
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


def _chart_data_labels(
    payload: dict[str, Any],
    chart_type: str,
    grouping: str | None,
    point_count: int,
) -> dict[str, Any] | None:
    config = _data_labels_config(payload)
    if config is None:
        return None
    if chart_type not in {"area", "bar", "column", "line"}:
        raise RuntimeError(
            f"Native PPTX {chart_type} chart data labels are outside current support"
        )
    _data_label_position(config.get("position"), chart_type, grouping)
    if config.get("color") is not None and _hex_or_none(config["color"]) is None:
        raise RuntimeError("Native PPTX chart data_labels.color must be a color")
    point_items = _data_label_point_items(
        config,
        chart_type,
        grouping,
        point_count,
    )
    for item in point_items:
        if item.get("color") is not None and _hex_or_none(item["color"]) is None:
            raise RuntimeError(
                "Native PPTX chart data_labels.points color must be a color"
            )
    colors = _chart_list(
        _first_present(
            config.get("colors"),
            config.get("label_colors"),
            config.get("labelColors"),
        ),
        "data_labels.colors",
    )
    if colors and len(colors) != point_count:
        raise RuntimeError("Native PPTX chart data_labels.colors must match point count")
    if any(_hex_or_none(color) is None for color in colors):
        raise RuntimeError("Native PPTX chart data_labels.colors entries must be colors")
    return config


def _data_label_point_items(
    config: dict[str, Any],
    chart_type: str,
    grouping: str | None,
    point_count: int,
) -> list[dict[str, Any]]:
    """Normalize selected point labels and validate their plot semantics."""
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
        _data_label_position(
            _first_present(data.get("position"), config.get("position")),
            chart_type,
            grouping,
        )
        seen.add(index)
        data["idx"] = index
        items.append(data)
    return items


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
    root_point_colors = _first_present(
        payload.get("point_colors"),
        payload.get("pointColors"),
    )
    if root_point_colors is not None and len(raw_series) != 1:
        raise RuntimeError("Native PPTX chart root point_colors is only valid for one series")

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
        raw_point_colors = _first_present(
            item.get("point_colors"),
            item.get("pointColors"),
            root_point_colors if idx == 1 else None,
        )
        point_colors = [
            _clean_hex(color, "#4472C4")
            for color in _chart_list(raw_point_colors, "series[].point_colors")
        ]
        if point_colors and len(point_colors) != len(values):
            raise RuntimeError("Native PPTX chart series point_colors must match values length")
        series_item = {"name": str(item.get("name") or f"Series {idx}"), "values": values}
        if point_colors:
            series_item["point_colors"] = point_colors
        fill_opacity = _first_present(
            item.get("fill_opacity"),
            item.get("fillOpacity"),
        )
        if fill_opacity is not None:
            fill_opacity = _number(fill_opacity, "series fill_opacity")
            if not 0 <= fill_opacity <= 1:
                raise RuntimeError(
                    "Native PPTX chart series fill_opacity must be between 0 and 1"
                )
            series_item["fill_opacity"] = fill_opacity
        line_width = _first_present(
            item.get("line_width"),
            item.get("lineWidth"),
        )
        if line_width is not None:
            line_width = _number(line_width, "series line_width")
            if line_width <= 0:
                raise RuntimeError("Native PPTX chart series line_width must be positive")
            _powerpoint_line_width_emu(line_width, "series line_width")
            series_item["line_width"] = line_width
        series.append(series_item)
    return series


def _category_chart_data(
    payload: dict[str, Any],
    chart_type: str,
    alias_grouping: str | None,
    alias_style: str | None,
) -> dict[str, Any]:
    categories = [str(item) for item in _chart_list(payload.get("categories", []), "categories")]
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}

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

    grouping = (
        _chart_grouping(chart_type, payload, alias_grouping)
        if chart_type in {"bar", "column", "line", "area"}
        else None
    )
    return {
        "kind": "category",
        "type": chart_type,
        "categories": categories,
        "grouping": grouping,
        "of_pie_type": of_pie_type,
        "line_style": line_style,
        "radar_marker_style": radar_marker_style,
        "radar_style": radar_style,
        "show_value_axis_labels": _chart_bool(
            _first_present(
                payload.get("show_value_axis_labels"),
                payload.get("showValueAxisLabels"),
                style.get("show_value_axis_labels"),
                style.get("showValueAxisLabels"),
            ),
            True,
        ),
        "data_labels": _chart_data_labels(
            payload,
            chart_type,
            grouping,
            len(categories),
        ),
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
    has_area_fill = bool(_first_present(plot_payload.get("area_fill"), plot_payload.get("areaFill")))
    if chart_type == "line" and has_area_fill:
        chart_type = "area"
    return chart_type, alias_grouping, alias_style


def _plot_series_area_style(plot_payload: dict[str, Any]) -> bool:
    for item in _chart_list(plot_payload.get("series", []), "series"):
        if not isinstance(item, dict):
            continue
        if _first_present(
            item.get("fill_opacity"),
            item.get("fillOpacity"),
        ) is not None:
            return True
    return False


def _combo_plot_entry(
    plot_payload: dict[str, Any],
    categories: list[str],
    *,
    fallback_series: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    chart_type, alias_grouping, alias_style = _combo_plot_type(plot_payload)
    if chart_type == "line" and _plot_series_area_style(plot_payload):
        raise RuntimeError(
            "Native PPTX combo line plot with series fill_opacity requires area_fill: true"
        )
    plot_series = fallback_series or _category_series(plot_payload, categories)
    grouping = (
        _chart_grouping(chart_type, plot_payload, alias_grouping)
        if chart_type in {"area", "column", "line"}
        else None
    )
    entry: dict[str, Any] = {
        "axis": _combo_axis_name(plot_payload),
        "data_labels": _chart_data_labels(
            plot_payload,
            chart_type,
            grouping,
            len(categories),
        ),
        "grouping": grouping,
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
            if (
                previous is not None
                and signature == previous_signature
                and plot.get("data_labels") == previous.get("data_labels")
            ):
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
            raw_subtotals = payload.get(
                "subtotals",
                payload.get("subtotal_indices", []),
            )
            subtotals: list[int] = []
            seen_subtotals: set[int] = set()
            for value in _chart_list(raw_subtotals, "subtotals"):
                index = _chart_number(value)
                if not isinstance(index, int):
                    raise RuntimeError("Native PPTX waterfall subtotal indices must be integers")
                if index < 0 or index >= len(values):
                    raise RuntimeError(
                        "Native PPTX waterfall subtotal index is outside point range"
                    )
                if index in seen_subtotals:
                    raise RuntimeError(
                        "Native PPTX waterfall subtotal indices must be unique"
                    )
                seen_subtotals.add(index)
                subtotals.append(index)
            data["subtotals"] = subtotals
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
    if _data_labels_config(payload) is not None:
        raise RuntimeError("Native PPTX stock chart data labels are outside current support")
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
    if _data_labels_config(payload) is not None:
        raise RuntimeError(
            f"Native PPTX {chart_type} chart data labels are outside current support"
        )
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
    if (
        chart_type not in _CATEGORY_CHART_TYPES | {"combo", "stock"} | _XY_CHART_TYPES
        and _data_labels_config(payload) is not None
    ):
        raise RuntimeError(
            f"Native PPTX {chart_type} chart data labels are outside current support"
        )
    if chart_type == "combo":
        return _combo_chart_data(payload)
    if chart_type in _CHARTEX_CHART_TYPES:
        return _chartex_chart_data(payload, chart_type)
    if chart_type == "stock":
        return _stock_chart_data(payload)
    if chart_type in _XY_CHART_TYPES:
        return _xy_chart_data(payload, chart_type, alias_style)
    return _category_chart_data(payload, chart_type, alias_grouping, alias_style)


def validate_chart_payload(payload: dict[str, Any]) -> None:
    """Check a native chart payload against the export schema.

    Public contract for the pptx_to_svg importer: raises RuntimeError on any
    payload the native chart exporter cannot represent.
    """
    _chart_data(payload)


def validate_data_label_position(
    value: Any,
    chart_type: str,
    grouping: str | None,
) -> None:
    """Check a data-label position against the export schema.

    Public contract for the pptx_to_svg importer: raises RuntimeError when the
    position is not representable for the given plot.
    """
    _data_label_position(value, chart_type, grouping)
