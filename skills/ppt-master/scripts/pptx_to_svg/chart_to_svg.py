"""Extract native Chart replacement metadata from PPTX chart parts.

The visual chart preview still comes from the existing graphicFrame fallback.
This module only builds a conservative ``data-pptx-replace-with="chart"``
payload when the chart XML cache can be mapped to the current chart schema.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from svg_to_pptx.drawingml.utils import parse_font_family
from svg_to_pptx.native_objects.chart_data import (
    validate_chart_payload,
    validate_data_label_position,
)

from .chartex_to_svg import UnsupportedChartEx, extract_native_chartex_payload
from .color_resolver import ColorPalette, find_color_elem, resolve_color
from .emu_units import NS, Xfrm, ooxml_bool
from .normalized_chart_svg import SeriesVisualStyle, render_normalized_chart_svg
from .ooxml_loader import OoxmlPackage, PartRef


CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"
CHARTEX_URI = "http://schemas.microsoft.com/office/drawing/2014/chartex"

C_NS = {
    **NS,
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cx": CHARTEX_URI,
}


@dataclass
class ChartResult:
    """Native chart marker payload or a transparent unsupported status."""

    native_payload: dict[str, Any] | None = None
    native_status: str | None = None
    normalized_svg: str | None = None


class _UnsupportedChart(RuntimeError):
    """Raised when a chart should keep its visual fallback only."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


def extract_native_chart_payload(
    graphic_data: ET.Element | None,
    xfrm: Xfrm,
    slide_part: PartRef,
    pkg: OoxmlPackage,
    palette: ColorPalette | None = None,
) -> ChartResult:
    """Return native chart metadata for a supported classic or ChartEx chart."""
    if graphic_data is None:
        return ChartResult(native_status="unsupported-chart-reference")

    uri = graphic_data.attrib.get("uri", "")
    if uri == CHARTEX_URI or graphic_data.find("cx:chart", C_NS) is not None:
        try:
            payload = extract_native_chartex_payload(
                graphic_data,
                xfrm,
                slide_part,
                pkg,
                palette,
            )
        except UnsupportedChartEx as exc:
            return ChartResult(native_status=exc.status)
        except RuntimeError:
            return ChartResult(native_status="unsupported-chartex-parse")
        return ChartResult(native_payload=payload)
    if uri != CHART_URI:
        return ChartResult(native_status="unsupported-chart-uri")
    if xfrm.rot or xfrm.flip_h or xfrm.flip_v:
        return ChartResult(native_status="unsupported-native-transform")

    chart_ref = graphic_data.find("c:chart", C_NS)
    if chart_ref is None:
        return ChartResult(native_status="unsupported-chart-reference")
    rid = chart_ref.attrib.get(f"{{{NS['r']}}}id")
    if not rid:
        return ChartResult(native_status="unsupported-chart-reference")

    chart_path = slide_part.resolve_rel(rid)
    if not chart_path:
        return ChartResult(native_status="unsupported-chart-relationship")
    chart_part = pkg.load_part(chart_path)
    if chart_part is None:
        return ChartResult(native_status="unsupported-chart-part")

    try:
        payload, visual_styles = _payload_from_chart_xml(
            chart_part.xml,
            xfrm,
            palette=palette,
        )
        validate_chart_payload(payload)
    except _UnsupportedChart as exc:
        return ChartResult(native_status=exc.status)
    except RuntimeError:
        return ChartResult(native_status="unsupported-chart-schema")
    except (TypeError, ValueError, AttributeError):
        return ChartResult(native_status="unsupported-chart-parse")
    # The visual fallback is deliberately best-effort and isolated from the
    # active native payload. A renderer defect must never downgrade a chart
    # that the native schema has already validated.
    try:
        normalized_svg = render_normalized_chart_svg(payload, visual_styles)
    except (KeyError, TypeError, ValueError, OverflowError, ArithmeticError):
        normalized_svg = None
    return ChartResult(native_payload=payload, normalized_svg=normalized_svg)


def _payload_from_chart_xml(
    chart_root: ET.Element,
    xfrm: Xfrm,
    *,
    palette: ColorPalette | None = None,
) -> tuple[dict[str, Any], list[SeriesVisualStyle]]:
    plot_area = chart_root.find(".//c:plotArea", C_NS)
    if plot_area is None:
        raise _UnsupportedChart("unsupported-chart-plot")

    chart_nodes = [
        child
        for child in list(plot_area)
        if _local_name(child.tag).endswith("Chart")
    ]
    if not chart_nodes:
        raise _UnsupportedChart("unsupported-chart-plot")
    date_system = chart_root.find("c:date1904", C_NS)
    if date_system is not None and (
        not set(date_system.attrib).issubset({"val"}) or list(date_system)
    ):
        raise _UnsupportedChart("unsupported-date-system")
    uses_1904_dates = _strict_axis_bool(
        date_system,
        date_system is not None,
    )
    if len(chart_nodes) > 1:
        if uses_1904_dates and any(
            _category_cache_is_numeric(chart) for chart in chart_nodes
        ):
            raise _UnsupportedChart("unsupported-date-system")
        payload, visual_styles = _combo_payload(
            chart_root,
            plot_area,
            chart_nodes,
            xfrm,
            palette=palette,
        )
        return payload, visual_styles

    chart = chart_nodes[0]
    chart_tag = _local_name(chart.tag)
    has_date_axis = plot_area.find("c:dateAx", C_NS) is not None
    if uses_1904_dates and has_date_axis:
        raise _UnsupportedChart("unsupported-date-system")
    if has_date_axis:
        _validate_canonical_series_order(
            [chart],
            "unsupported-chart-series-order",
        )
    if chart_tag in {"area3DChart", "bar3DChart", "line3DChart", "pie3DChart", "surface3DChart"}:
        raise _UnsupportedChart("unsupported-3d-chart")
    if has_date_axis and chart_tag not in {"areaChart", "stockChart"}:
        raise _UnsupportedChart("unsupported-date-axis")
    if chart_tag == "barChart":
        payload = _category_payload(chart, _bar_chart_type(chart), xfrm)
    elif chart_tag in {
        "areaChart",
        "doughnutChart",
        "lineChart",
        "ofPieChart",
        "pieChart",
        "radarChart",
    }:
        chart_type = {
            "areaChart": "area",
            "doughnutChart": "doughnut",
            "lineChart": "line",
            "ofPieChart": "of_pie",
            "pieChart": "pie",
            "radarChart": "radar",
        }[chart_tag]
        category_kind = "date" if has_date_axis else "text"
        if chart_tag == "radarChart" and _category_cache_is_numeric(chart):
            category_kind = "numeric"
        payload = _category_payload(
            chart,
            chart_type,
            xfrm,
            category_kind=category_kind,
        )
        if chart_tag == "radarChart":
            if category_kind == "numeric":
                payload["categories"] = [
                    str(value) for value in payload["categories"]
                ]
            payload["radar_style"] = _effective_radar_style(chart)
    elif chart_tag == "scatterChart":
        payload = _xy_payload(chart, "scatter", xfrm)
        payload["axes"] = _xy_axis_contract(plot_area, chart)
    elif chart_tag == "bubbleChart":
        payload = _xy_payload(chart, "bubble", xfrm)
        payload["axes"] = _xy_axis_contract(plot_area, chart)
    elif chart_tag == "stockChart":
        payload, visual_styles = _stock_payload(
            chart_root,
            plot_area,
            chart,
            xfrm,
            palette=palette,
        )
        return payload, visual_styles
    else:
        raise _UnsupportedChart("unsupported-chart-type")

    if has_date_axis:
        payload["axes"] = _single_axis_contract(
            plot_area,
            chart,
            category_kind="date",
            cross_between="midCat",
        )
        expected_category_format = payload["axes"]["category"].get(
            "number_format",
            "m/d/yyyy",
        )
        if _numeric_category_cache_format(chart) != expected_category_format:
            raise _UnsupportedChart("unsupported-chart-category-format")

    visual_styles = _validate_chart_semantics(
        payload,
        plot_area,
        chart,
        palette=palette,
        validate_axes=not (
            has_date_axis or chart_tag in {"bubbleChart", "scatterChart"}
        ),
    )
    _apply_chart_metadata(payload, chart_root, plot_area, chart)
    return payload, visual_styles


def _combo_payload(
    chart_root: ET.Element,
    plot_area: ET.Element,
    chart_nodes: list[ET.Element],
    xfrm: Xfrm,
    *,
    palette: ColorPalette | None,
) -> tuple[dict[str, Any], list[SeriesVisualStyle]]:
    series_indices_by_plot = [
        _plot_series_indices(chart, "unsupported-combo-series-order")
        for chart in chart_nodes
    ]
    flat_series_indices = [
        index
        for series_indices in series_indices_by_plot
        for index in series_indices
    ]
    if sorted(flat_series_indices) != list(range(len(flat_series_indices))):
        raise _UnsupportedChart("unsupported-combo-series-order")
    axes_by_id = _axis_nodes_by_id(plot_area)
    if not axes_by_id:
        raise _UnsupportedChart("unsupported-combo-chart")
    axes: dict[str, dict[str, Any]] = {}
    axis_pairs: dict[str, tuple[str, str]] = {}
    primary_categories: list[Any] | None = None
    primary_categories_are_numeric = False
    plots: list[dict[str, Any]] = []
    visual_styles: list[SeriesVisualStyle] = []
    colors: list[str] = []
    referenced_axis_ids: set[str] = set()

    for chart, series_indices in zip(chart_nodes, series_indices_by_plot):
        chart_tag = _local_name(chart.tag)
        if chart_tag == "barChart":
            if _bar_chart_type(chart) != "column":
                raise _UnsupportedChart("unsupported-combo-chart")
            chart_type = "column"
        elif chart_tag == "lineChart":
            chart_type = "line"
        elif chart_tag == "areaChart":
            chart_type = "area"
        else:
            raise _UnsupportedChart("unsupported-combo-chart")

        cat_id, cat_axis, val_id, val_axis = _plot_axis_pair(chart, axes_by_id)
        if _local_name(cat_axis.tag) != "catAx":
            raise _UnsupportedChart("unsupported-combo-chart")
        val_position = _element_val(val_axis.find("c:axPos", C_NS))
        if val_position == "l":
            axis_name = "primary"
            category_role = "category"
            value_role = "value"
            allowed_value_crosses = {"autoZero"}
        elif val_position == "r":
            axis_name = "secondary"
            category_role = "secondary_category"
            value_role = "secondary_value"
            allowed_value_crosses = {"max"}
        else:
            raise _UnsupportedChart("unsupported-combo-chart")

        axis_pair = (cat_id, val_id)
        previous_pair = axis_pairs.get(axis_name)
        if previous_pair is not None and previous_pair != axis_pair:
            raise _UnsupportedChart("unsupported-combo-chart")
        if any(
            set(existing_pair).intersection(axis_pair)
            for name, existing_pair in axis_pairs.items()
            if name != axis_name
        ):
            raise _UnsupportedChart("unsupported-combo-chart")
        axis_pairs[axis_name] = axis_pair

        category_axis = _axis_config_from_xml(
            cat_axis,
            role=category_role,
            expected_cross_axis_id=val_id,
            allowed_crosses={"autoZero"},
            expected_cross_between=None,
        )
        value_axis = _axis_config_from_xml(
            val_axis,
            role=value_role,
            expected_cross_axis_id=cat_id,
            allowed_crosses=allowed_value_crosses,
            expected_cross_between="between",
        )
        for role, config in (
            (category_role, category_axis),
            (value_role, value_axis),
        ):
            if role in axes and axes[role] != config:
                raise _UnsupportedChart("unsupported-combo-chart")
            axes[role] = config
        referenced_axis_ids.update((cat_id, val_id))

        categories_are_numeric = _category_cache_is_numeric(chart)
        if categories_are_numeric:
            expected_category_format = category_axis.get(
                "number_format",
                "General",
            )
            if _numeric_category_cache_format(chart) != expected_category_format:
                raise _UnsupportedChart("unsupported-combo-category-format")
        plot_payload = _category_payload(
            chart,
            chart_type,
            xfrm,
            category_kind="numeric" if categories_are_numeric else "text",
        )
        if axis_name == "primary" and primary_categories is None:
            primary_categories = list(plot_payload["categories"])
            primary_categories_are_numeric = categories_are_numeric
        plot_styles = _validate_chart_semantics(
            plot_payload,
            plot_area,
            chart,
            palette=palette,
            validate_axes=False,
        )
        visual_styles.extend(plot_styles)
        colors.extend(
            str(color)
            for color in plot_payload.get("style", {}).get("colors", [])
        )
        _apply_plot_data_labels(plot_payload, chart)
        plot_entry: dict[str, Any] = {
            "axis": axis_name,
            "categories": list(plot_payload["categories"]),
            "category_numeric": categories_are_numeric,
            "series": plot_payload["series"],
            "series_indices": series_indices,
            "type": chart_type,
        }
        for key in ("data_labels", "grouping", "line_style"):
            if plot_payload.get(key) is not None:
                plot_entry[key] = plot_payload[key]
        plots.append(plot_entry)

    if primary_categories is None or not plots:
        raise _UnsupportedChart("unsupported-combo-chart")
    if referenced_axis_ids != set(axes_by_id):
        raise _UnsupportedChart("unsupported-combo-chart")

    category_layouts = {
        (
            bool(plot["category_numeric"]),
            tuple(plot["categories"]),
        )
        for plot in plots
    }
    if len(category_layouts) == 1:
        for plot in plots:
            plot.pop("categories")
            plot.pop("category_numeric")
    payload: dict[str, Any] = {
        **_bounds_payload(xfrm),
        "axes": axes,
        "categories": primary_categories,
        "plots": plots,
        "type": "combo",
    }
    if primary_categories_are_numeric:
        payload["category_numeric"] = True
    if colors:
        payload["style"] = {"colors": colors}
    _apply_chart_metadata(
        payload,
        chart_root,
        plot_area,
        chart_nodes[0],
        include_plot_labels=False,
    )
    return payload, visual_styles


def _validate_stock_semantics(
    plot_area: ET.Element,
    chart: ET.Element,
) -> None:
    allowed_children = {"axId", "dLbls", "hiLowLines", "ser", "upDownBars"}
    if any(_local_name(child.tag) not in allowed_children for child in chart):
        raise _UnsupportedChart("unsupported-stock-chart")
    if plot_area.find("c:dTable", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-data-table")
    for tag in ("dropLines", "errBars", "trendline"):
        if chart.find(f".//c:{tag}", C_NS) is not None:
            raise _UnsupportedChart("unsupported-chart-analysis-features")
    if _data_labels_payload(chart.find("c:dLbls", C_NS)) is not None:
        raise _UnsupportedChart("unsupported-chart-data-labels")
    if len(chart.findall("c:dLbls", C_NS)) > 1:
        raise _UnsupportedChart("unsupported-stock-chart")

    hi_low_lines = chart.findall("c:hiLowLines", C_NS)
    up_down_bars = chart.findall("c:upDownBars", C_NS)
    if len(hi_low_lines) != 1 or len(up_down_bars) != 1:
        raise _UnsupportedChart("unsupported-stock-chart")
    hi_low_styles = hi_low_lines[0].findall("c:spPr", C_NS)
    if (
        hi_low_lines[0].attrib
        or len(hi_low_styles) > 1
        or any(_local_name(child.tag) != "spPr" for child in hi_low_lines[0])
    ):
        raise _UnsupportedChart("unsupported-stock-chart")
    up_down = up_down_bars[0]
    if up_down.attrib or any(
        _local_name(child.tag) not in {"downBars", "gapWidth", "upBars"}
        for child in up_down
    ):
        raise _UnsupportedChart("unsupported-stock-chart")
    gap_widths = up_down.findall("c:gapWidth", C_NS)
    if (
        len(gap_widths) != 1
        or set(gap_widths[0].attrib) != {"val"}
        or list(gap_widths[0])
        or _element_val(gap_widths[0]) != "150"
    ):
        raise _UnsupportedChart("unsupported-stock-chart")
    for tag in ("upBars", "downBars"):
        nodes = up_down.findall(f"c:{tag}", C_NS)
        styles = nodes[0].findall("c:spPr", C_NS) if nodes else []
        if (
            len(nodes) != 1
            or nodes[0].attrib
            or len(styles) > 1
            or any(_local_name(child.tag) != "spPr" for child in nodes[0])
        ):
            raise _UnsupportedChart("unsupported-stock-chart")

    allowed_series_children = {
        "cat", "extLst", "idx", "marker", "order", "smooth", "spPr",
        "tx", "val",
    }
    for series_node in chart.findall("c:ser", C_NS):
        if any(
            _local_name(child.tag) not in allowed_series_children
            for child in series_node
        ):
            raise _UnsupportedChart("unsupported-stock-chart")
        for child_name in allowed_series_children - {"extLst"}:
            if len(series_node.findall(f"c:{child_name}", C_NS)) > 1:
                raise _UnsupportedChart("unsupported-stock-chart")
        marker = series_node.find("c:marker", C_NS)
        symbol = marker.find("c:symbol", C_NS) if marker is not None else None
        if (
            marker is not None
            and (
                marker.attrib
                or len(marker) != 1
                or symbol is None
                or set(symbol.attrib) != {"val"}
                or list(symbol)
                or _element_val(symbol) != "none"
            )
        ):
            raise _UnsupportedChart("unsupported-stock-chart")
        smooth = series_node.find("c:smooth", C_NS)
        if smooth is not None:
            if set(smooth.attrib) != {"val"} or list(smooth):
                raise _UnsupportedChart("unsupported-stock-chart")
            if _strict_axis_bool(smooth, False):
                raise _UnsupportedChart("unsupported-stock-chart")
        for child_name in ("idx", "order"):
            child = series_node.find(f"c:{child_name}", C_NS)
            if child is None or set(child.attrib) != {"val"} or list(child):
                raise _UnsupportedChart("unsupported-stock-chart")


def _stock_payload(
    chart_root: ET.Element,
    plot_area: ET.Element,
    chart: ET.Element,
    xfrm: Xfrm,
    *,
    palette: ColorPalette | None,
) -> tuple[dict[str, Any], list[SeriesVisualStyle]]:
    series_nodes = chart.findall("c:ser", C_NS)
    if len(series_nodes) != 4:
        raise _UnsupportedChart("unsupported-stock-chart")
    categories = _numeric_values(series_nodes[0].find("c:cat", C_NS))
    if not categories:
        raise _UnsupportedChart("unsupported-chart-cache")
    series: list[dict[str, Any]] = []
    for index, series_node in enumerate(series_nodes, start=1):
        expected_index = str(index - 1)
        if (
            _element_val(series_node.find("c:idx", C_NS)) != expected_index
            or _element_val(series_node.find("c:order", C_NS)) != expected_index
        ):
            raise _UnsupportedChart("unsupported-stock-chart")
        if _numeric_values(series_node.find("c:cat", C_NS)) != categories:
            raise _UnsupportedChart("unsupported-chart-cache")
        values = _numeric_values(series_node.find("c:val", C_NS))
        if len(values) != len(categories):
            raise _UnsupportedChart("unsupported-chart-cache")
        series.append({
            "name": _series_name(series_node, index),
            "values": values,
        })
    axes = _single_axis_contract(
        plot_area,
        chart,
        category_kind="date",
        cross_between="between",
    )
    expected_category_format = axes["category"].get(
        "number_format",
        "m/d/yyyy",
    )
    category_cache_format = _numeric_category_cache_format(chart)
    if category_cache_format not in {"General", expected_category_format}:
        raise _UnsupportedChart("unsupported-chart-category-format")
    _validate_stock_semantics(plot_area, chart)
    payload: dict[str, Any] = {
        **_bounds_payload(xfrm),
        "axes": axes,
        "categories": categories,
        "series": series,
        "type": "stock",
    }
    visual_styles = _chart_visual_styles(payload, chart, palette)
    _apply_chart_metadata(payload, chart_root, plot_area, chart)
    return payload, visual_styles


def _canonical_srgb_color(fill: ET.Element | None) -> str:
    """Return an exporter-canonical solid RGB fill, or reject the style."""
    if fill is None or fill.attrib:
        raise _UnsupportedChart("unsupported-chart-series-style")
    children = list(fill)
    if (
        len(children) != 1
        or _local_name(children[0].tag) != "srgbClr"
        or set(children[0].attrib) != {"val"}
        or list(children[0])
    ):
        raise _UnsupportedChart("unsupported-chart-series-style")
    color = children[0].attrib["val"].strip()
    if len(color) != 6 or any(char not in "0123456789abcdefABCDEF" for char in color):
        raise _UnsupportedChart("unsupported-chart-series-style")
    return color.upper()


@dataclass(frozen=True)
class _LinePaint:
    color: str | None
    opacity: float
    width: float
    cap: str
    visible: bool
    automatic: bool


@dataclass(frozen=True)
class _ShapePaint:
    fill: str | None
    fill_opacity: float
    fill_explicit: bool
    line: _LinePaint | None


@dataclass(frozen=True)
class _MarkerPaint:
    symbol: str | None
    size: float
    shape: _ShapePaint


_FALLBACK_CHART_COLORS = (
    "#4472C4", "#ED7D31", "#A5A5A5", "#FFC000",
    "#5B9BD5", "#70AD47", "#264478", "#9E480E",
)
_COLOR_MODIFIERS_WITH_VALUE = {
    "alpha", "alphaMod", "alphaOff", "hueMod", "hueOff", "lumMod",
    "lumOff", "satMod", "satOff", "shade", "tint",
}
_COLOR_MODIFIERS_WITHOUT_VALUE = {"comp", "gray", "inv"}


def _resolved_solid_fill(
    fill: ET.Element,
    palette: ColorPalette | None,
) -> tuple[str, float]:
    if fill.attrib or len(fill) != 1:
        raise _UnsupportedChart("unsupported-chart-series-style")
    color = find_color_elem(fill)
    if color is None or color is not fill[0]:
        raise _UnsupportedChart("unsupported-chart-series-style")
    tag = _local_name(color.tag)
    allowed_attrs = {
        "srgbClr": {"val"},
        "schemeClr": {"val"},
        "sysClr": {"val", "lastClr"},
        "prstClr": {"val"},
        "hslClr": {"hue", "sat", "lum"},
        "scrgbClr": {"r", "g", "b"},
    }.get(tag)
    if allowed_attrs is None or not set(color.attrib).issubset(allowed_attrs):
        raise _UnsupportedChart("unsupported-chart-series-style")
    required = {
        "srgbClr": {"val"}, "schemeClr": {"val"}, "prstClr": {"val"},
        "hslClr": {"hue", "sat", "lum"}, "scrgbClr": {"r", "g", "b"},
    }.get(tag, set())
    if not required.issubset(color.attrib):
        raise _UnsupportedChart("unsupported-chart-series-style")
    for modifier in color:
        modifier_name = _local_name(modifier.tag)
        if modifier_name in _COLOR_MODIFIERS_WITH_VALUE:
            if set(modifier.attrib) != {"val"} or list(modifier):
                raise _UnsupportedChart("unsupported-chart-series-style")
            try:
                modifier_value = float(modifier.attrib["val"])
            except (TypeError, ValueError, OverflowError):
                raise _UnsupportedChart("unsupported-chart-series-style") from None
            if not math.isfinite(modifier_value):
                raise _UnsupportedChart("unsupported-chart-series-style")
        elif modifier_name in _COLOR_MODIFIERS_WITHOUT_VALUE:
            if modifier.attrib or list(modifier):
                raise _UnsupportedChart("unsupported-chart-series-style")
        else:
            raise _UnsupportedChart("unsupported-chart-series-style")
    try:
        resolved, alpha = resolve_color(color, palette)
    except (TypeError, ValueError, OverflowError):
        raise _UnsupportedChart("unsupported-chart-series-style") from None
    if resolved is None or not math.isfinite(alpha):
        raise _UnsupportedChart("unsupported-chart-series-style")
    return resolved.upper(), max(0.0, min(1.0, alpha))


def _resolved_line(
    line: ET.Element,
    palette: ColorPalette | None,
) -> _LinePaint:
    if not set(line.attrib).issubset({"w", "cap"}):
        raise _UnsupportedChart("unsupported-chart-series-style")
    raw_width = line.attrib.get("w")
    if raw_width is None:
        width = 1.5
    else:
        if re.fullmatch(r"[0-9]+", raw_width) is None:
            raise _UnsupportedChart("unsupported-chart-series-style")
        width = int(raw_width) / 9525.0
        if not 0 <= width <= 1000:
            raise _UnsupportedChart("unsupported-chart-series-style")
    cap_aliases = {None: "round", "rnd": "round", "sq": "square", "flat": "butt"}
    cap = cap_aliases.get(line.attrib.get("cap"))
    if cap is None:
        raise _UnsupportedChart("unsupported-chart-series-style")

    fill_nodes: list[ET.Element] = []
    for child in line:
        name = _local_name(child.tag)
        if name in {"solidFill", "noFill"}:
            fill_nodes.append(child)
        elif name == "prstDash":
            if child.attrib != {"val": "solid"} or list(child):
                raise _UnsupportedChart("unsupported-chart-series-style")
        elif name in {"round", "bevel"}:
            if child.attrib or list(child):
                raise _UnsupportedChart("unsupported-chart-series-style")
        elif name == "miter":
            if not set(child.attrib).issubset({"lim"}) or list(child):
                raise _UnsupportedChart("unsupported-chart-series-style")
            raw_limit = child.attrib.get("lim")
            if raw_limit is not None and re.fullmatch(r"[0-9]+", raw_limit) is None:
                raise _UnsupportedChart("unsupported-chart-series-style")
        else:
            raise _UnsupportedChart("unsupported-chart-series-style")
    if len(fill_nodes) > 1:
        raise _UnsupportedChart("unsupported-chart-series-style")
    if not fill_nodes:
        return _LinePaint(None, 1.0, width, cap, True, True)
    fill = fill_nodes[0]
    if _local_name(fill.tag) == "noFill":
        if fill.attrib or list(fill):
            raise _UnsupportedChart("unsupported-chart-series-style")
        return _LinePaint(None, 1.0, width, cap, False, False)
    color, opacity = _resolved_solid_fill(fill, palette)
    return _LinePaint(color, opacity, width, cap, True, False)


def _resolved_shape_paint(
    sp_pr: ET.Element | None,
    palette: ColorPalette | None,
) -> _ShapePaint:
    if sp_pr is None:
        return _ShapePaint(None, 1.0, False, None)
    if sp_pr.attrib:
        raise _UnsupportedChart("unsupported-chart-series-style")
    fill_nodes: list[ET.Element] = []
    line_nodes: list[ET.Element] = []
    for child in sp_pr:
        name = _local_name(child.tag)
        if name in {"solidFill", "noFill"}:
            fill_nodes.append(child)
        elif name == "ln":
            line_nodes.append(child)
        elif name == "effectLst":
            if child.attrib or list(child):
                raise _UnsupportedChart("unsupported-chart-series-style")
        else:
            raise _UnsupportedChart("unsupported-chart-series-style")
    if len(fill_nodes) > 1 or len(line_nodes) > 1:
        raise _UnsupportedChart("unsupported-chart-series-style")
    fill_color: str | None = None
    fill_opacity = 1.0
    fill_explicit = bool(fill_nodes)
    if fill_nodes:
        fill = fill_nodes[0]
        if _local_name(fill.tag) == "noFill":
            if fill.attrib or list(fill):
                raise _UnsupportedChart("unsupported-chart-series-style")
        else:
            fill_color, fill_opacity = _resolved_solid_fill(fill, palette)
    line = _resolved_line(line_nodes[0], palette) if line_nodes else None
    return _ShapePaint(fill_color, fill_opacity, fill_explicit, line)


def _resolved_marker(
    marker: ET.Element | None,
    palette: ColorPalette | None,
) -> _MarkerPaint:
    if marker is None:
        return _MarkerPaint(None, 5.0, _resolved_shape_paint(None, palette))
    if marker.attrib:
        raise _UnsupportedChart("unsupported-chart-series-style")
    allowed = {"symbol", "size", "spPr"}
    names = [_local_name(child.tag) for child in marker]
    if any(name not in allowed for name in names) or len(names) != len(set(names)):
        raise _UnsupportedChart("unsupported-chart-series-style")
    symbol_node = marker.find("c:symbol", C_NS)
    symbol = _element_val(symbol_node)
    if symbol_node is not None and (
        set(symbol_node.attrib) != {"val"} or list(symbol_node)
    ):
        raise _UnsupportedChart("unsupported-chart-series-style")
    if symbol not in {None, "circle", "none"}:
        raise _UnsupportedChart("unsupported-chart-series-style")
    size_node = marker.find("c:size", C_NS)
    size = 5.0
    if size_node is not None:
        raw_size = size_node.attrib.get("val", "")
        if set(size_node.attrib) != {"val"} or list(size_node) or re.fullmatch(r"[0-9]+", raw_size) is None:
            raise _UnsupportedChart("unsupported-chart-series-style")
        size = float(raw_size)
        if not 2 <= size <= 72:
            raise _UnsupportedChart("unsupported-chart-series-style")
    return _MarkerPaint(
        symbol,
        size,
        _resolved_shape_paint(marker.find("c:spPr", C_NS), palette),
    )


def _automatic_color(palette: ColorPalette | None, index: int) -> str:
    if palette is not None:
        resolved = palette.resolve_scheme(f"accent{index % 6 + 1}")
        if resolved:
            return f"#{resolved.upper()}"
    return _FALLBACK_CHART_COLORS[index % len(_FALLBACK_CHART_COLORS)]


def _line_color(line: _LinePaint | None, default: str | None) -> str | None:
    if line is None:
        return default
    if not line.visible:
        return None
    return default if line.automatic else line.color


def _series_visual_style(
    shape: _ShapePaint,
    marker: _MarkerPaint,
    *,
    chart_type: str,
    auto_color: str,
) -> SeriesVisualStyle:
    fill_default = auto_color if chart_type in {"area", "bar", "bubble", "column"} else None
    fill = shape.fill if shape.fill_explicit else fill_default
    if chart_type in {"line", "scatter"}:
        line_default = auto_color
    elif chart_type == "area":
        line_default = auto_color
    else:
        line_default = None
    stroke = _line_color(shape.line, line_default)
    marker_fill = marker.shape.fill if marker.shape.fill_explicit else auto_color
    marker_stroke = _line_color(marker.shape.line, auto_color)
    line = shape.line
    marker_line = marker.shape.line
    return SeriesVisualStyle(
        fill=fill,
        fill_opacity=shape.fill_opacity,
        stroke=stroke,
        stroke_opacity=line.opacity if line is not None else 1.0,
        stroke_width=line.width if line is not None else 1.5,
        line_cap=line.cap if line is not None else "round",
        marker_fill=marker_fill,
        marker_fill_opacity=marker.shape.fill_opacity,
        marker_stroke=marker_stroke,
        marker_stroke_opacity=marker_line.opacity if marker_line is not None else 1.0,
        marker_stroke_width=marker_line.width if marker_line is not None else 1.0,
        marker_size=marker.size,
    )


def _pie_visual_styles(
    payload: dict[str, Any],
    series: ET.Element,
    palette: ColorPalette | None,
) -> list[SeriesVisualStyle]:
    chart_type = payload["type"]
    expected_count = len(payload["categories"]) + (1 if chart_type == "of_pie" else 0)
    base_shape = _resolved_shape_paint(series.find("c:spPr", C_NS), palette)
    point_nodes = series.findall("c:dPt", C_NS)
    points: dict[int, _ShapePaint] = {}
    for point in point_nodes:
        if point.attrib:
            raise _UnsupportedChart("unsupported-chart-series-style")
        allowed = {"idx", "bubble3D", "explosion", "spPr"}
        names = [_local_name(child.tag) for child in point]
        if any(name not in allowed for name in names) or len(names) != len(set(names)):
            raise _UnsupportedChart("unsupported-chart-series-style")
        idx = point.find("c:idx", C_NS)
        if idx is None or set(idx.attrib) != {"val"} or list(idx):
            raise _UnsupportedChart("unsupported-chart-series-style")
        try:
            point_index = int(idx.attrib["val"])
        except ValueError:
            raise _UnsupportedChart("unsupported-chart-series-style") from None
        bubble_3d = point.find("c:bubble3D", C_NS)
        if bubble_3d is not None and (
            not set(bubble_3d.attrib).issubset({"val"})
            or list(bubble_3d)
            or ooxml_bool(bubble_3d.attrib.get("val"), True)
        ):
            raise _UnsupportedChart("unsupported-chart-series-style")
        if point_index < 0 or point_index >= expected_count or point_index in points:
            raise _UnsupportedChart("unsupported-chart-series-style")
        points[point_index] = _resolved_shape_paint(point.find("c:spPr", C_NS), palette)
    if points and set(points) != set(range(expected_count)):
        raise _UnsupportedChart("unsupported-chart-series-style")

    styles: list[SeriesVisualStyle] = []
    for index in range(expected_count):
        auto = _automatic_color(palette, index)
        point_shape = points.get(index, base_shape)
        fill = point_shape.fill if point_shape.fill_explicit else auto
        stroke = _line_color(point_shape.line, "#FFFFFF")
        line = point_shape.line
        styles.append(
            SeriesVisualStyle(
                fill=fill,
                fill_opacity=point_shape.fill_opacity,
                stroke=stroke,
                stroke_opacity=line.opacity if line is not None else 1.0,
                stroke_width=line.width if line is not None else 1.0,
                line_cap=line.cap if line is not None else "round",
                marker_fill=fill,
                marker_stroke=stroke,
            )
        )
    return styles


def _chart_visual_styles(
    payload: dict[str, Any],
    plot: ET.Element,
    palette: ColorPalette | None,
) -> list[SeriesVisualStyle]:
    chart_type = payload["type"]
    series_nodes = plot.findall("c:ser", C_NS)
    if chart_type in {"pie", "doughnut", "of_pie"}:
        if len(series_nodes) != 1:
            raise _UnsupportedChart("unsupported-chart-series-style")
        styles = _pie_visual_styles(payload, series_nodes[0], palette)
    else:
        if any(series.find("c:dPt", C_NS) is not None for series in series_nodes):
            raise _UnsupportedChart("unsupported-chart-series-style")
        styles = []
        for index, series in enumerate(series_nodes):
            auto = _automatic_color(palette, index)
            shape = _resolved_shape_paint(series.find("c:spPr", C_NS), palette)
            marker = _resolved_marker(series.find("c:marker", C_NS), palette)
            styles.append(
                _series_visual_style(
                    shape,
                    marker,
                    chart_type=chart_type,
                    auto_color=auto,
                )
            )
    colors = [
        style.fill or style.stroke or style.marker_fill or _automatic_color(palette, index)
        for index, style in enumerate(styles)
    ]
    if colors:
        payload["style"] = {"colors": colors}
    return styles


def _strict_axis_bool(elem: ET.Element | None, default: bool) -> bool:
    if elem is None:
        return default
    raw = elem.attrib.get("val")
    if raw is None:
        return default
    key = raw.strip().lower()
    if key in {"1", "on", "true"}:
        return True
    if key in {"0", "false", "off"}:
        return False
    raise _UnsupportedChart("unsupported-chart-axis-options")


def _validate_canonical_series_order(
    plots: list[ET.Element],
    status: str,
) -> None:
    expected_index = 0
    for plot in plots:
        for series in plot.findall("c:ser", C_NS):
            expected = str(expected_index)
            for child_name in ("idx", "order"):
                child = series.find(f"c:{child_name}", C_NS)
                if (
                    child is None
                    or set(child.attrib) != {"val"}
                    or list(child)
                    or _element_val(child) != expected
                ):
                    raise _UnsupportedChart(status)
            expected_index += 1


def _plot_series_indices(plot: ET.Element, status: str) -> list[int]:
    indices: list[int] = []
    for series in plot.findall("c:ser", C_NS):
        values: list[int] = []
        for child_name in ("idx", "order"):
            child = series.find(f"c:{child_name}", C_NS)
            raw_value = _element_val(child)
            if (
                child is None
                or set(child.attrib) != {"val"}
                or list(child)
                or raw_value is None
                or re.fullmatch(r"[0-9]+", raw_value) is None
            ):
                raise _UnsupportedChart(status)
            values.append(int(raw_value))
        if values[0] != values[1]:
            raise _UnsupportedChart(status)
        indices.append(values[0])
    if not indices or len(set(indices)) != len(indices):
        raise _UnsupportedChart(status)
    return indices


def _axis_number(elem: ET.Element | None) -> int | float | None:
    if elem is None:
        return None
    raw = elem.attrib.get("val")
    try:
        number = float(raw) if raw is not None else math.nan
    except (TypeError, ValueError, OverflowError):
        raise _UnsupportedChart("unsupported-chart-axis-options") from None
    if not math.isfinite(number):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    return int(number) if number.is_integer() else number


def _axis_nodes_by_id(plot_area: ET.Element) -> dict[str, ET.Element]:
    if plot_area.find("c:serAx", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    axes: dict[str, ET.Element] = {}
    for tag in ("catAx", "dateAx", "valAx"):
        for axis in plot_area.findall(f"c:{tag}", C_NS):
            axis_id = _element_val(axis.find("c:axId", C_NS))
            if not axis_id or axis_id in axes:
                raise _UnsupportedChart("unsupported-chart-axis-options")
            axes[axis_id] = axis
    return axes


def _plot_axis_pair(
    plot: ET.Element,
    axes_by_id: dict[str, ET.Element],
) -> tuple[str, ET.Element, str, ET.Element]:
    axis_ids = [_element_val(elem) for elem in plot.findall("c:axId", C_NS)]
    if len(axis_ids) != 2 or any(not axis_id for axis_id in axis_ids):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if len(set(axis_ids)) != 2:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    resolved = [(axis_id, axes_by_id.get(str(axis_id))) for axis_id in axis_ids]
    if any(axis is None for _, axis in resolved):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    category_axes = [
        (str(axis_id), axis)
        for axis_id, axis in resolved
        if axis is not None and _local_name(axis.tag) in {"catAx", "dateAx"}
    ]
    value_axes = [
        (str(axis_id), axis)
        for axis_id, axis in resolved
        if axis is not None and _local_name(axis.tag) == "valAx"
    ]
    if len(category_axes) != 1 or len(value_axes) != 1:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    cat_id, cat_axis = category_axes[0]
    val_id, val_axis = value_axes[0]
    return cat_id, cat_axis, val_id, val_axis


def _axis_config_from_xml(
    axis: ET.Element,
    *,
    role: str,
    expected_cross_axis_id: str,
    allowed_crosses: set[str],
    expected_cross_between: str | None,
) -> dict[str, Any]:
    axis_kind = _local_name(axis.tag)
    allowed_children = {
        "auto", "axId", "axPos", "baseTimeUnit", "crossAx", "crossBetween",
        "crosses", "delete", "lblAlgn", "lblOffset", "majorGridlines",
        "majorTickMark", "majorUnit", "minorTickMark", "noMultiLvlLbl",
        "numFmt", "scaling", "spPr", "tickLblPos", "title", "txPr",
    }
    if any(_local_name(child.tag) not in allowed_children for child in axis):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if axis.attrib:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    for child_name in allowed_children:
        if len(axis.findall(f"c:{child_name}", C_NS)) > 1:
            raise _UnsupportedChart("unsupported-chart-axis-options")
    simple_children = {
        "auto", "axId", "axPos", "baseTimeUnit", "crossAx",
        "crossBetween", "crosses", "delete", "lblAlgn", "lblOffset",
        "majorTickMark", "majorUnit", "minorTickMark", "noMultiLvlLbl",
        "tickLblPos",
    }
    if any(
        _local_name(child.tag) in simple_children
        and (set(child.attrib) != {"val"} or list(child))
        for child in axis
    ):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if axis.find("c:minorGridlines", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-axis-options")

    scaling = axis.find("c:scaling", C_NS)
    config: dict[str, Any] = {}
    if scaling is not None:
        if scaling.attrib or any(
            _local_name(child.tag) not in {"max", "min", "orientation"}
            for child in scaling
        ):
            raise _UnsupportedChart("unsupported-chart-axis-options")
        for child_name in ("orientation", "max", "min"):
            if len(scaling.findall(f"c:{child_name}", C_NS)) > 1:
                raise _UnsupportedChart("unsupported-chart-axis-options")
        if any(
            set(child.attrib) != {"val"} or list(child)
            for child in scaling
        ):
            raise _UnsupportedChart("unsupported-chart-axis-options")
        orientation = _element_val(scaling.find("c:orientation", C_NS)) or "minMax"
        if orientation not in {"maxMin", "minMax"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        config["reverse"] = orientation == "maxMin"
        minimum = _axis_number(scaling.find("c:min", C_NS))
        maximum = _axis_number(scaling.find("c:max", C_NS))
        if minimum is not None:
            config["minimum"] = minimum
        if maximum is not None:
            config["maximum"] = maximum
        if minimum is not None and maximum is not None and minimum >= maximum:
            raise _UnsupportedChart("unsupported-chart-axis-options")
    else:
        config["reverse"] = False

    position_aliases = {"b": "bottom", "l": "left", "r": "right", "t": "top"}
    position = position_aliases.get(_element_val(axis.find("c:axPos", C_NS)) or "")
    if position is None:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if role in {"category", "secondary_category"}:
        if position not in {"bottom", "top"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        config["kind"] = "date" if axis_kind == "dateAx" else "text"
    elif role == "x":
        if position not in {"bottom", "top"} or axis_kind != "valAx":
            raise _UnsupportedChart("unsupported-chart-axis-options")
        config["kind"] = "value"
    else:
        if position not in {"left", "right"} or axis_kind != "valAx":
            raise _UnsupportedChart("unsupported-chart-axis-options")
        config["kind"] = "value"
    config["position"] = position
    config["visible"] = not _strict_axis_bool(axis.find("c:delete", C_NS), False)

    tick_label_aliases = {
        "high": "high",
        "low": "low",
        "nextTo": "next_to",
        "none": "none",
    }
    tick_label_position = _element_val(axis.find("c:tickLblPos", C_NS)) or "nextTo"
    if tick_label_position not in tick_label_aliases:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    config["label_position"] = tick_label_aliases[tick_label_position]
    config["major_gridlines"] = axis.find("c:majorGridlines", C_NS) is not None

    num_fmt = axis.find("c:numFmt", C_NS)
    if num_fmt is not None:
        if list(num_fmt) or not set(num_fmt.attrib).issubset({"formatCode", "sourceLinked"}):
            raise _UnsupportedChart("unsupported-chart-axis-options")
        number_format = num_fmt.attrib.get("formatCode", "")
        if not number_format.strip():
            raise _UnsupportedChart("unsupported-chart-axis-number-format")
        config["number_format"] = number_format

    major_unit = _axis_number(axis.find("c:majorUnit", C_NS))
    if major_unit is not None:
        if role not in {"value", "secondary_value", "x", "y"} or major_unit <= 0:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        config["major_unit"] = major_unit

    if _element_val(axis.find("c:crossAx", C_NS)) != expected_cross_axis_id:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    crosses = _element_val(axis.find("c:crosses", C_NS)) or "autoZero"
    if crosses not in allowed_crosses:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    cross_between = _element_val(axis.find("c:crossBetween", C_NS))
    if cross_between != expected_cross_between:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    auto = axis.find("c:auto", C_NS)
    if auto is not None:
        _strict_axis_bool(auto, True)
    major_tick = _element_val(axis.find("c:majorTickMark", C_NS))
    minor_tick = _element_val(axis.find("c:minorTickMark", C_NS))
    if major_tick not in {None, "none", "out"} or minor_tick not in {None, "none"}:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    label_alignment = _element_val(axis.find("c:lblAlgn", C_NS))
    label_offset = _element_val(axis.find("c:lblOffset", C_NS))
    no_multi_level = _element_val(axis.find("c:noMultiLvlLbl", C_NS))
    if role in {"category", "secondary_category"}:
        if label_alignment not in {None, "ctr"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        if label_offset not in {None, "100"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        if no_multi_level not in {None, "0"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
    elif any(
        value is not None
        for value in (label_alignment, label_offset, no_multi_level, auto)
    ):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if axis_kind == "dateAx":
        if _element_val(axis.find("c:baseTimeUnit", C_NS)) not in {None, "days"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
    elif axis.find("c:baseTimeUnit", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    return config


def _single_axis_contract(
    plot_area: ET.Element,
    plot: ET.Element,
    *,
    category_kind: str,
    cross_between: str,
) -> dict[str, dict[str, Any]]:
    axes_by_id = _axis_nodes_by_id(plot_area)
    cat_id, cat_axis, val_id, val_axis = _plot_axis_pair(plot, axes_by_id)
    if set(axes_by_id) != {cat_id, val_id}:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if _local_name(cat_axis.tag) != ("dateAx" if category_kind == "date" else "catAx"):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    category = _axis_config_from_xml(
        cat_axis,
        role="category",
        expected_cross_axis_id=val_id,
        allowed_crosses={"autoZero"},
        expected_cross_between=None,
    )
    value = _axis_config_from_xml(
        val_axis,
        role="value",
        expected_cross_axis_id=cat_id,
        allowed_crosses={"autoZero"},
        expected_cross_between=cross_between,
    )
    return {"category": category, "value": value}


def _xy_axis_contract(
    plot_area: ET.Element,
    plot: ET.Element,
) -> dict[str, dict[str, Any]]:
    """Return the closed two-value-axis contract used by XY charts."""
    axes_by_id = _axis_nodes_by_id(plot_area)
    plot_axis_nodes = plot.findall("c:axId", C_NS)
    if len(plot_axis_nodes) != 2 or any(
        set(node.attrib) != {"val"} or list(node)
        for node in plot_axis_nodes
    ):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    axis_ids = [_element_val(node) for node in plot_axis_nodes]
    if any(not axis_id for axis_id in axis_ids) or len(set(axis_ids)) != 2:
        raise _UnsupportedChart("unsupported-chart-axis-options")
    if set(axes_by_id) != set(axis_ids):
        raise _UnsupportedChart("unsupported-chart-axis-options")

    resolved = [
        (str(axis_id), axes_by_id.get(str(axis_id)))
        for axis_id in axis_ids
    ]
    if any(
        axis is None or _local_name(axis.tag) != "valAx"
        for _, axis in resolved
    ):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    horizontal = [
        (axis_id, axis)
        for axis_id, axis in resolved
        if axis is not None
        and _element_val(axis.find("c:axPos", C_NS)) in {"b", "t"}
    ]
    vertical = [
        (axis_id, axis)
        for axis_id, axis in resolved
        if axis is not None
        and _element_val(axis.find("c:axPos", C_NS)) in {"l", "r"}
    ]
    if len(horizontal) != 1 or len(vertical) != 1:
        raise _UnsupportedChart("unsupported-chart-axis-options")

    x_id, x_axis = horizontal[0]
    y_id, y_axis = vertical[0]
    x_config = _axis_config_from_xml(
        x_axis,
        role="x",
        expected_cross_axis_id=y_id,
        allowed_crosses={"autoZero"},
        expected_cross_between="midCat",
    )
    y_config = _axis_config_from_xml(
        y_axis,
        role="y",
        expected_cross_axis_id=x_id,
        allowed_crosses={"autoZero"},
        expected_cross_between="midCat",
    )
    return {"x": x_config, "y": y_config}


def _validate_legacy_axes(payload: dict[str, Any], plot_area: ET.Element) -> None:
    """Keep the original narrow axis gate for payloads without axes metadata."""
    grouping = payload.get("grouping")
    axes = plot_area.findall("c:catAx", C_NS) + plot_area.findall("c:valAx", C_NS)
    for axis in axes:
        axis_kind = _local_name(axis.tag)
        axis_position = _element_val(axis.find("c:axPos", C_NS))
        delete = axis.find("c:delete", C_NS)
        if delete is not None and ooxml_bool(delete.attrib.get("val"), True):
            raise _UnsupportedChart("unsupported-chart-axis-options")
        scaling = axis.find("c:scaling", C_NS)
        if scaling is not None:
            for tag in ("logBase", "min", "max"):
                if scaling.find(f"c:{tag}", C_NS) is not None:
                    raise _UnsupportedChart("unsupported-chart-axis-options")
            orientation = _element_val(scaling.find("c:orientation", C_NS))
            if orientation not in {None, "minMax"}:
                raise _UnsupportedChart("unsupported-chart-axis-options")
        for tag in (
            "majorUnit", "minorUnit", "crossesAt", "dispUnits",
            "tickLblSkip", "tickMarkSkip",
        ):
            if axis.find(f"c:{tag}", C_NS) is not None:
                raise _UnsupportedChart("unsupported-chart-axis-options")
        crosses = _element_val(axis.find("c:crosses", C_NS))
        if crosses not in {None, "autoZero"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        auto = axis.find("c:auto", C_NS)
        if auto is not None and not ooxml_bool(auto.attrib.get("val"), True):
            raise _UnsupportedChart("unsupported-chart-axis-options")
        num_fmt = axis.find("c:numFmt", C_NS)
        if num_fmt is not None:
            format_code = num_fmt.attrib.get("formatCode", "").strip()
            allowed_formats = {"", "General"}
            if grouping == "percentStacked":
                allowed_formats.add("0%")
            if format_code not in allowed_formats:
                raise _UnsupportedChart("unsupported-chart-axis-number-format")
        tick_label_position = _element_val(axis.find("c:tickLblPos", C_NS))
        if payload["type"] in {"scatter", "bubble"} or axis_kind == "catAx":
            if tick_label_position not in {None, "nextTo"}:
                raise _UnsupportedChart("unsupported-chart-axis-options")
        elif tick_label_position == "none":
            payload["show_value_axis_labels"] = False
        elif tick_label_position not in {None, "nextTo"}:
            raise _UnsupportedChart("unsupported-chart-axis-options")

        has_major_gridlines = axis.find("c:majorGridlines", C_NS) is not None
        if payload["type"] in {"scatter", "bubble"}:
            expected_major_gridlines = axis_position in {"l", "r"}
        else:
            expected_major_gridlines = axis_kind == "valAx"
        if has_major_gridlines != expected_major_gridlines:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        if axis.find("c:minorGridlines", C_NS) is not None:
            raise _UnsupportedChart("unsupported-chart-axis-options")


def _validate_normalized_axis_topology(
    payload: dict[str, Any],
    plot_area: ET.Element,
    plot: ET.Element,
) -> None:
    """Validate a category/value pair whose presentation will normalize."""
    axes_by_id = _axis_nodes_by_id(plot_area)
    cat_id, cat_axis, val_id, val_axis = _plot_axis_pair(plot, axes_by_id)
    if set(axes_by_id) != {cat_id, val_id}:
        raise _UnsupportedChart("unsupported-chart-axis-options")

    plot_axis_nodes = plot.findall("c:axId", C_NS)
    if any(set(node.attrib) != {"val"} or list(node) for node in plot_axis_nodes):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    for axis, axis_id, cross_axis_id in (
        (cat_axis, cat_id, val_id),
        (val_axis, val_id, cat_id),
    ):
        if axis.attrib:
            raise _UnsupportedChart("unsupported-chart-axis-options")
        id_nodes = axis.findall("c:axId", C_NS)
        cross_nodes = axis.findall("c:crossAx", C_NS)
        if (
            len(id_nodes) != 1
            or len(cross_nodes) != 1
            or set(id_nodes[0].attrib) != {"val"}
            or set(cross_nodes[0].attrib) != {"val"}
            or list(id_nodes[0])
            or list(cross_nodes[0])
            or _element_val(id_nodes[0]) != axis_id
            or _element_val(cross_nodes[0]) != cross_axis_id
        ):
            raise _UnsupportedChart("unsupported-chart-axis-options")

    position_nodes = (
        cat_axis.findall("c:axPos", C_NS),
        val_axis.findall("c:axPos", C_NS),
    )
    if any(
        len(nodes) != 1
        or set(nodes[0].attrib) != {"val"}
        or list(nodes[0])
        for nodes in position_nodes
    ):
        raise _UnsupportedChart("unsupported-chart-axis-options")
    category_position = _element_val(position_nodes[0][0])
    value_position = _element_val(position_nodes[1][0])
    if payload["type"] == "bar":
        valid_positions = (
            category_position in {"l", "r"}
            and value_position in {"b", "t"}
        )
    else:
        valid_positions = (
            category_position in {"b", "t"}
            and value_position in {"l", "r"}
        )
    if not valid_positions:
        raise _UnsupportedChart("unsupported-chart-axis-options")


def _validate_or_normalize_legacy_axes(
    payload: dict[str, Any],
    plot_area: ET.Element,
    plot: ET.Element,
) -> None:
    """Keep exact legacy payloads while allowing presentation normalization."""
    try:
        _validate_legacy_axes(payload, plot_area)
    except _UnsupportedChart as exc:
        if exc.status not in {
            "unsupported-chart-axis-number-format",
            "unsupported-chart-axis-options",
        }:
            raise
        if payload["type"] in {"area", "column", "line"}:
            try:
                payload["axes"] = _single_axis_contract(
                    plot_area,
                    plot,
                    category_kind="text",
                    cross_between="between",
                )
                return
            except _UnsupportedChart:
                payload.pop("axes", None)
        _validate_normalized_axis_topology(payload, plot_area, plot)


def _effective_radar_style(plot: ET.Element) -> str:
    """Map Office radar marker variants to the writer's uniform style set."""
    style_nodes = plot.findall("c:radarStyle", C_NS)
    if len(style_nodes) > 1:
        raise _UnsupportedChart("unsupported-chart-radar-style")
    style_node = style_nodes[0] if style_nodes else None
    if style_node is not None and (
        set(style_node.attrib) != {"val"} or list(style_node)
    ):
        raise _UnsupportedChart("unsupported-chart-radar-style")
    style = _element_val(style_node) if style_node is not None else "standard"
    if style == "filled":
        return "filled"
    if style not in {"marker", "standard"}:
        raise _UnsupportedChart("unsupported-chart-radar-style")

    default_marker = style == "marker"
    marker_states: list[bool] = []
    for series in plot.findall("c:ser", C_NS):
        symbol = _element_val(series.find("c:marker/c:symbol", C_NS))
        marker_states.append(
            default_marker if symbol is None else symbol != "none"
        )
    return "lineMarker" if any(marker_states) else "line"


def _effective_scatter_style(
    plot: ET.Element,
    visual_styles: list[SeriesVisualStyle],
) -> str:
    """Normalize plot-level line intent plus uniform series overrides."""
    style_nodes = plot.findall("c:scatterStyle", C_NS)
    if len(style_nodes) > 1:
        raise _UnsupportedChart("unsupported-chart-scatter-style")
    style_node = style_nodes[0] if style_nodes else None
    if style_node is not None and (
        set(style_node.attrib) != {"val"} or list(style_node)
    ):
        raise _UnsupportedChart("unsupported-chart-scatter-style")
    plot_style = _element_val(style_node) or "marker"
    if plot_style not in {"line", "lineMarker", "marker", "smooth", "smoothMarker"}:
        raise _UnsupportedChart("unsupported-chart-scatter-style")
    plot_has_line = plot_style in {"line", "lineMarker", "smooth", "smoothMarker"}
    plot_is_smooth = plot_style in {"smooth", "smoothMarker"}

    style_by_state = {
        (False, True, False): "marker",
        (True, False, False): "line",
        (True, True, False): "lineMarker",
        (True, False, True): "smooth",
        (True, True, True): "smoothMarker",
    }
    effective_styles: set[str] = set()
    series_nodes = plot.findall("c:ser", C_NS)
    if len(series_nodes) != len(visual_styles):
        raise _UnsupportedChart("unsupported-chart-scatter-style")
    for series, visual_style in zip(series_nodes, visual_styles):
        line_node = series.find("c:spPr/a:ln", C_NS)
        has_line = plot_has_line if line_node is None else (
            visual_style.stroke is not None
            and visual_style.stroke_opacity > 0
        )
        markers = series.findall("c:marker", C_NS)
        if len(markers) != 1:
            raise _UnsupportedChart("unsupported-chart-scatter-style")
        marker = markers[0]
        symbol = marker.find("c:symbol", C_NS) if marker is not None else None
        if (
            marker is None
            or symbol is None
            or set(symbol.attrib) != {"val"}
            or list(symbol)
        ):
            raise _UnsupportedChart("unsupported-chart-scatter-style")
        symbol_value = _element_val(symbol)
        if symbol_value not in {"circle", "none"}:
            raise _UnsupportedChart("unsupported-chart-scatter-style")
        has_marker = symbol_value == "circle"

        smooth_nodes = series.findall("c:smooth", C_NS)
        if len(smooth_nodes) > 1:
            raise _UnsupportedChart("unsupported-chart-scatter-style")
        smooth = smooth_nodes[0] if smooth_nodes else None
        is_smooth = plot_is_smooth
        if smooth is not None:
            if not set(smooth.attrib).issubset({"val"}) or list(smooth):
                raise _UnsupportedChart("unsupported-chart-scatter-style")
            raw_smooth = smooth.attrib.get("val")
            key = raw_smooth.strip().lower() if raw_smooth is not None else "true"
            if key in {"1", "on", "true"}:
                is_smooth = True
            elif key in {"0", "false", "off"}:
                is_smooth = False
            else:
                raise _UnsupportedChart("unsupported-chart-scatter-style")
        if is_smooth and not has_line:
            raise _UnsupportedChart("unsupported-chart-scatter-style")

        effective_style = style_by_state.get((has_line, has_marker, is_smooth))
        if effective_style is None:
            raise _UnsupportedChart("unsupported-chart-scatter-style")
        effective_styles.add(effective_style)

    if len(effective_styles) != 1:
        raise _UnsupportedChart("unsupported-chart-scatter-style")
    return effective_styles.pop()


def _bounded_plot_integer(
    plot: ET.Element,
    name: str,
    *,
    minimum: int,
    maximum: int,
    status: str,
) -> int | None:
    nodes = plot.findall(f"c:{name}", C_NS)
    if len(nodes) > 1:
        raise _UnsupportedChart(status)
    if not nodes:
        return None
    node = nodes[0]
    raw_value = node.attrib.get("val")
    if (
        set(node.attrib) != {"val"}
        or list(node)
        or raw_value is None
        or re.fullmatch(r"-?[0-9]+", raw_value) is None
    ):
        raise _UnsupportedChart(status)
    value = int(raw_value)
    if not minimum <= value <= maximum:
        raise _UnsupportedChart(status)
    return value


def _validate_chart_semantics(
    payload: dict[str, Any],
    plot_area: ET.Element,
    plot: ET.Element,
    *,
    palette: ColorPalette | None = None,
    validate_axes: bool = True,
) -> list[SeriesVisualStyle]:
    """Reject valid chart features the compact marker cannot reproduce."""
    chart_type = payload["type"]
    grouping = payload.get("grouping")
    visual_styles = _chart_visual_styles(payload, plot, palette)
    for tag in (
        "trendline", "errBars", "dropLines", "hiLowLines", "upDownBars",
    ):
        if plot.find(f".//c:{tag}", C_NS) is not None:
            raise _UnsupportedChart("unsupported-chart-analysis-features")
    if plot_area.find("c:dTable", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-data-table")
    ser_line_nodes = plot.findall("c:serLines", C_NS)
    if len(ser_line_nodes) > 1:
        raise _UnsupportedChart("unsupported-chart-analysis-features")
    if ser_line_nodes:
        ser_lines = ser_line_nodes[0]
        if (
            chart_type != "of_pie"
            or ser_lines.attrib
            or len(ser_lines) > 1
            or any(_local_name(child.tag) != "spPr" for child in ser_lines)
        ):
            raise _UnsupportedChart("unsupported-chart-analysis-features")
    if validate_axes:
        _validate_or_normalize_legacy_axes(payload, plot_area, plot)

    if chart_type == "line":
        smooth_nodes = [plot.find("c:smooth", C_NS), *plot.findall("c:ser/c:smooth", C_NS)]
        if any(
            node is not None and ooxml_bool(node.attrib.get("val"), True)
            for node in smooth_nodes
        ):
            raise _UnsupportedChart("unsupported-chart-line-style")
        plot_marker = plot.find("c:marker", C_NS)
        plot_has_markers = bool(
            plot_marker is not None
            and ooxml_bool(plot_marker.attrib.get("val"), True)
        )
        marker_states: set[bool] = set()
        for series in plot.findall("c:ser", C_NS):
            marker_node = series.find("c:marker", C_NS)
            symbol = _element_val(series.find("c:marker/c:symbol", C_NS))
            if symbol not in {None, "circle", "none"}:
                raise _UnsupportedChart("unsupported-chart-line-style")
            marker_states.add(plot_has_markers if symbol is None else symbol != "none")
        if len(marker_states) > 1:
            raise _UnsupportedChart("unsupported-chart-line-style")

    if chart_type in {"bar", "column"}:
        _bounded_plot_integer(
            plot,
            "gapWidth",
            minimum=0,
            maximum=500,
            status="unsupported-chart-bar-options",
        )
        _bounded_plot_integer(
            plot,
            "overlap",
            minimum=-100,
            maximum=100,
            status="unsupported-chart-bar-options",
        )

    if chart_type == "bubble":
        bubble_scale = _element_val(plot.find("c:bubbleScale", C_NS))
        if bubble_scale not in {None, "100"}:
            raise _UnsupportedChart("unsupported-chart-bubble-options")
        show_negative = plot.find("c:showNegBubbles", C_NS)
        if show_negative is not None and ooxml_bool(
            show_negative.attrib.get("val"),
            True,
        ):
            raise _UnsupportedChart("unsupported-chart-bubble-options")
        size_represents = _element_val(plot.find("c:sizeRepresents", C_NS))
        if size_represents not in {None, "area"}:
            raise _UnsupportedChart("unsupported-chart-bubble-options")
        bubble_3d_nodes = [
            plot.find("c:bubble3D", C_NS),
            *plot.findall("c:ser/c:bubble3D", C_NS),
        ]
        if any(
            node is not None and ooxml_bool(node.attrib.get("val"), True)
            for node in bubble_3d_nodes
        ):
            raise _UnsupportedChart("unsupported-chart-bubble-options")

    if chart_type == "scatter":
        payload["scatter_style"] = _effective_scatter_style(plot, visual_styles)

    if chart_type in {"pie", "doughnut", "of_pie"}:
        for explosion in plot.findall(".//c:explosion", C_NS):
            if _element_val(explosion) not in {None, "0"}:
                raise _UnsupportedChart("unsupported-chart-pie-options")
        first_slice = _element_val(plot.find("c:firstSliceAng", C_NS))
        if first_slice not in {None, "0"}:
            raise _UnsupportedChart("unsupported-chart-pie-options")
    if chart_type == "doughnut":
        hole_size = _element_val(plot.find("c:holeSize", C_NS))
        if hole_size != "75":
            raise _UnsupportedChart("unsupported-chart-doughnut-options")
    if chart_type == "of_pie":
        for tag in ("splitType", "splitPos", "custSplit"):
            if plot.find(f"c:{tag}", C_NS) is not None:
                raise _UnsupportedChart("unsupported-chart-of-pie-options")
        gap_width = _element_val(plot.find("c:gapWidth", C_NS))
        if gap_width != "100":
            raise _UnsupportedChart("unsupported-chart-of-pie-options")
        second_size = _element_val(plot.find("c:secondPieSize", C_NS))
        if second_size not in {None, "75"}:
            raise _UnsupportedChart("unsupported-chart-of-pie-options")
    return visual_styles


def _apply_plot_data_labels(payload: dict[str, Any], plot: ET.Element) -> None:
    if plot.find("c:ser/c:dLbls", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-series-data-labels")
    data_labels = _data_labels_payload(plot.find("c:dLbls", C_NS))
    if not data_labels:
        return
    if payload["type"] not in {"area", "bar", "column", "line"}:
        raise _UnsupportedChart("unsupported-chart-data-labels")
    try:
        validate_data_label_position(
            data_labels.get("position"),
            payload["type"],
            payload.get("grouping"),
        )
    except RuntimeError:
        raise _UnsupportedChart("unsupported-chart-data-labels") from None
    payload["data_labels"] = data_labels


def _apply_chart_metadata(
    payload: dict[str, Any],
    chart_root: ET.Element,
    plot_area: ET.Element,
    plot: ET.Element,
    *,
    include_plot_labels: bool = True,
) -> None:
    """Copy visible classic-chart chrome supported by the native schema."""
    chart = chart_root.find("c:chart", C_NS)
    if chart is None:
        return

    title_element = chart.find("c:title", C_NS)
    title_entries = _canonical_title_entries(title_element)
    title = _chart_text(title_element)
    if title:
        if title_entries is not None:
            payload["title"] = title_entries[0]
            if len(title_entries) == 2:
                payload["subtitle"] = title_entries[1]
        else:
            payload["title"] = title

    legend = chart.find("c:legend", C_NS)
    if legend is not None:
        delete = legend.find("c:delete", C_NS)
        if delete is None or not ooxml_bool(delete.attrib.get("val"), True):
            position = _element_val(legend.find("c:legendPos", C_NS)) or "r"
            if position not in {"b", "l", "r", "t"}:
                raise _UnsupportedChart("unsupported-chart-legend-position")
            payload["show_legend"] = True
            payload["legend_position"] = position

    if include_plot_labels:
        _apply_plot_data_labels(payload, plot)

    axis_titles: dict[str, str] = {}
    category_axis_nodes = (
        plot_area.findall("c:catAx", C_NS)
        + plot_area.findall("c:dateAx", C_NS)
    )
    category_titles = [
        text
        for axis in category_axis_nodes
        if (text := _chart_text(axis.find("c:title", C_NS)))
    ]
    value_titles = [
        text
        for axis in plot_area.findall("c:valAx", C_NS)
        if (text := _chart_text(axis.find("c:title", C_NS)))
    ]
    if payload["type"] == "combo":
        if len(set(category_titles)) > 1:
            raise _UnsupportedChart("unsupported-chart-axis-titles")
        if category_titles:
            axis_titles["category"] = category_titles[0]
        for axis in plot_area.findall("c:valAx", C_NS):
            text = _chart_text(axis.find("c:title", C_NS))
            if not text:
                continue
            position = _element_val(axis.find("c:axPos", C_NS))
            key = "secondary_value" if position == "r" else "value"
            if key in axis_titles:
                raise _UnsupportedChart("unsupported-chart-axis-titles")
            axis_titles[key] = text
    elif payload["type"] in {"scatter", "bubble"}:
        if category_titles:
            raise _UnsupportedChart("unsupported-chart-axis-titles")
        titled_value_axes = [
            (
                _element_val(axis.find("c:axPos", C_NS)),
                _chart_text(axis.find("c:title", C_NS)),
            )
            for axis in plot_area.findall("c:valAx", C_NS)
        ]
        for position, text in titled_value_axes:
            if not text:
                continue
            key = "x" if position in {"b", "t"} else "y"
            if key in axis_titles:
                raise _UnsupportedChart("unsupported-chart-axis-titles")
            axis_titles[key] = text
    else:
        if len(category_titles) > 1 or len(value_titles) > 1:
            raise _UnsupportedChart("unsupported-chart-axis-titles")
        if category_titles:
            axis_titles["category"] = category_titles[0]
        if value_titles:
            axis_titles["value"] = value_titles[0]
    if axis_titles:
        payload["axis_titles"] = axis_titles


def _chart_text(container: ET.Element | None) -> str:
    if container is None:
        return ""
    paragraphs: list[str] = []
    for paragraph in container.findall(".//a:p", C_NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//a:t", C_NS))
        if text:
            paragraphs.append(text)
    if paragraphs:
        return "\n".join(paragraphs)
    values = [node.text or "" for node in container.findall(".//c:v", C_NS)]
    return "".join(values)


def _canonical_title_paragraph(paragraph: ET.Element) -> dict[str, Any] | None:
    """Return one exporter-canonical or basic Office title paragraph."""
    if paragraph.attrib or [_local_name(child.tag) for child in paragraph] != ["r"]:
        return None
    run = paragraph.find("a:r", C_NS)
    if run is None or run.attrib:
        return None
    run_child_names = [_local_name(child.tag) for child in run]
    if run_child_names == ["t"]:
        text = run.find("a:t", C_NS)
        if (
            text is None
            or text.attrib
            or list(text)
            or not (text.text or "")
            or text.text != text.text.strip()
        ):
            return None
        return {"text": text.text}
    if run_child_names != ["rPr", "t"]:
        return None
    run_props = run.find("a:rPr", C_NS)
    text = run.find("a:t", C_NS)
    if (
        run_props is None
        or set(run_props.attrib) != {"lang", "sz"}
        or text is None
        or text.attrib
        or list(text)
        or not (text.text or "")
        or text.text != text.text.strip()
    ):
        return None
    size_token = run_props.attrib["sz"]
    if re.fullmatch(r"[0-9]+", size_token) is None:
        return None
    size = int(size_token)
    if size % 10 != 0 or not 100 <= size <= 400000:
        return None
    child_names = [_local_name(child.tag) for child in run_props]
    if child_names not in ([], ["solidFill"], ["latin", "ea"], ["solidFill", "latin", "ea"]):
        return None
    solid_fill = run_props.find("a:solidFill", C_NS)
    color = None
    if solid_fill is not None:
        try:
            color = _canonical_srgb_color(solid_fill)
        except _UnsupportedChart:
            return None
    latin = run_props.find("a:latin", C_NS)
    east_asian = run_props.find("a:ea", C_NS)
    if (latin is None) != (east_asian is None):
        return None
    for font in (latin, east_asian):
        if font is not None and (
            set(font.attrib) != {"typeface"}
            or not font.attrib["typeface"].strip()
            or list(font)
        ):
            return None
    entry: dict[str, Any] = {
        "text": text.text,
        "font_size": _round_payload_number(size / 75.0),
    }
    if color is not None:
        entry["color"] = f"#{color}"
    if latin is not None and east_asian is not None:
        latin_name = latin.attrib["typeface"]
        east_asian_name = east_asian.attrib["typeface"]
        font_family = (
            latin_name
            if latin_name == east_asian_name
            else f"{latin_name}, {east_asian_name}"
        )
        resolved_fonts = parse_font_family(font_family)
        if (
            resolved_fonts["latin"] != latin_name
            or resolved_fonts["ea"] != east_asian_name
        ):
            return None
        entry["font_family"] = font_family
    return entry


def _canonical_title_entries(title: ET.Element | None) -> list[dict[str, Any]] | None:
    """Recognize exporter-canonical or basic Office rich title structure."""
    if title is None:
        return None
    title_child_names = [_local_name(child.tag) for child in title]
    if title_child_names not in (["tx", "layout"], ["tx", "layout", "overlay"]):
        return None
    overlay = title.find("c:overlay", C_NS)
    if overlay is not None and (
        set(overlay.attrib) != {"val"}
        or list(overlay)
        or ooxml_bool(overlay.attrib.get("val"), True)
    ):
        return None
    tx = title.find("c:tx", C_NS)
    layout = title.find("c:layout", C_NS)
    rich = title.find("c:tx/c:rich", C_NS)
    if (
        tx is None
        or tx.attrib
        or [_local_name(child.tag) for child in tx] != ["rich"]
        or layout is None
        or layout.attrib
        or list(layout)
        or rich is None
        or rich.attrib
    ):
        return None
    children = list(rich)
    child_names = [_local_name(child.tag) for child in children]
    if child_names not in (
        ["bodyPr", "lstStyle", "p"],
        ["bodyPr", "lstStyle", "p", "p"],
    ):
        return None
    if children[0].attrib or list(children[0]) or children[1].attrib or list(children[1]):
        return None
    entries = [_canonical_title_paragraph(paragraph) for paragraph in children[2:]]
    if any(entry is None for entry in entries):
        return None
    return [entry for entry in entries if entry is not None]


def _data_label_text_style(tx_pr: ET.Element) -> dict[str, Any]:
    """Extract the subset of label text properties emitted by this exporter."""
    body_pr = tx_pr.find("a:bodyPr", C_NS)
    list_style = tx_pr.find("a:lstStyle", C_NS)
    if body_pr is None or body_pr.attrib or list(body_pr):
        raise _UnsupportedChart("unsupported-chart-data-labels")
    if list_style is None or list_style.attrib or list(list_style):
        raise _UnsupportedChart("unsupported-chart-data-labels")
    paragraphs = tx_pr.findall("a:p", C_NS)
    if len(paragraphs) != 1:
        raise _UnsupportedChart("unsupported-chart-data-labels")
    paragraph = paragraphs[0]
    if any(
        child.tag.rsplit("}", 1)[-1] not in {"pPr", "endParaRPr"}
        for child in paragraph
    ):
        raise _UnsupportedChart("unsupported-chart-data-labels")
    p_pr = paragraph.find("a:pPr", C_NS)
    if p_pr is None or p_pr.attrib:
        raise _UnsupportedChart("unsupported-chart-data-labels")
    if any(
        child.tag.rsplit("}", 1)[-1] != "defRPr"
        for child in p_pr
    ):
        raise _UnsupportedChart("unsupported-chart-data-labels")
    end_r_pr = paragraph.find("a:endParaRPr", C_NS)
    if end_r_pr is not None and (
        any(name not in {"lang", "altLang"} for name in end_r_pr.attrib)
        or list(end_r_pr)
    ):
        raise _UnsupportedChart("unsupported-chart-data-labels")

    r_pr = p_pr.find("a:defRPr", C_NS)
    if r_pr is None:
        return {}
    allowed_attrs = {"sz", "b"}
    if any(name not in allowed_attrs for name in r_pr.attrib):
        raise _UnsupportedChart("unsupported-chart-data-labels")
    allowed_children = {"solidFill", "latin", "ea"}
    if any(
        child.tag.rsplit("}", 1)[-1] not in allowed_children
        for child in r_pr
    ):
        raise _UnsupportedChart("unsupported-chart-data-labels")

    style: dict[str, Any] = {}
    raw_size = r_pr.attrib.get("sz")
    if raw_size is not None:
        try:
            size_px = float(raw_size) / 75.0
        except ValueError:
            raise _UnsupportedChart("unsupported-chart-data-labels") from None
        if size_px <= 0 or not math.isfinite(size_px):
            raise _UnsupportedChart("unsupported-chart-data-labels")
        style["font_size"] = int(size_px) if size_px.is_integer() else round(size_px, 3)
    if r_pr.attrib.get("b") is not None:
        style["bold"] = ooxml_bool(r_pr.attrib.get("b"), True)

    solid_fill = r_pr.find("a:solidFill", C_NS)
    if solid_fill is not None:
        color_children = list(solid_fill)
        if (
            len(color_children) != 1
            or color_children[0].tag.rsplit("}", 1)[-1] != "srgbClr"
            or list(color_children[0])
        ):
            raise _UnsupportedChart("unsupported-chart-data-labels")
        color = color_children[0].attrib.get("val", "").strip()
        if len(color) != 6 or any(char not in "0123456789abcdefABCDEF" for char in color):
            raise _UnsupportedChart("unsupported-chart-data-labels")
        style["color"] = f"#{color.upper()}"

    latin = r_pr.find("a:latin", C_NS)
    east_asian = r_pr.find("a:ea", C_NS)
    latin_face = latin.attrib.get("typeface", "").strip() if latin is not None else ""
    east_asian_face = (
        east_asian.attrib.get("typeface", "").strip()
        if east_asian is not None else ""
    )
    font_face = (
        f"{latin_face}, {east_asian_face}"
        if latin_face and east_asian_face and latin_face != east_asian_face
        else latin_face or east_asian_face
    )
    if font_face:
        style["font_family"] = font_face
    return style


def _data_labels_payload(dlabels: ET.Element | None) -> dict[str, Any] | None:
    if dlabels is None:
        return None
    if dlabels.find("c:dLbl", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-point-labels")
    allowed_children = {
        "numFmt", "txPr", "dLblPos", "showLegendKey", "showVal",
        "showCatName", "showSerName", "showPercent", "showBubbleSize",
        "showLeaderLines",
    }
    if any(
        child.tag.rsplit("}", 1)[-1] not in allowed_children
        for child in dlabels
    ):
        raise _UnsupportedChart("unsupported-chart-data-labels")
    for tag in ("showLegendKey", "showBubbleSize"):
        elem = dlabels.find(f"c:{tag}", C_NS)
        if elem is not None and ooxml_bool(elem.attrib.get("val"), True):
            raise _UnsupportedChart("unsupported-chart-data-labels")

    config: dict[str, Any] = {}
    for tag, field in (
        ("showVal", "show_value"),
        ("showCatName", "show_category"),
        ("showSerName", "show_series"),
        ("showPercent", "show_percent"),
    ):
        elem = dlabels.find(f"c:{tag}", C_NS)
        config[field] = (
            ooxml_bool(elem.attrib.get("val"), True)
            if elem is not None else False
        )
    if not any(config.values()):
        return None

    leader_lines = dlabels.find("c:showLeaderLines", C_NS)
    if leader_lines is not None:
        config["show_leader_lines"] = ooxml_bool(
            leader_lines.attrib.get("val"),
            True,
        )

    position = _element_val(dlabels.find("c:dLblPos", C_NS))
    if position:
        position_aliases = {
            "bestFit": "best_fit",
            "ctr": "center",
            "inBase": "inside_base",
            "inEnd": "inside_end",
            "outEnd": "outside_end",
            "t": "above",
        }
        normalized_position = position_aliases.get(position)
        if normalized_position is None:
            raise _UnsupportedChart("unsupported-chart-data-labels")
        config["position"] = normalized_position
    num_fmt = dlabels.find("c:numFmt", C_NS)
    if num_fmt is not None and num_fmt.attrib.get("formatCode"):
        config["number_format"] = num_fmt.attrib["formatCode"]
    tx_pr = dlabels.find("c:txPr", C_NS)
    if tx_pr is not None:
        config.update(_data_label_text_style(tx_pr))
    return config


def _category_payload(
    chart: ET.Element,
    chart_type: str,
    xfrm: Xfrm,
    *,
    category_kind: str = "text",
) -> dict[str, Any]:
    series_nodes = chart.findall("c:ser", C_NS)
    if not series_nodes:
        raise _UnsupportedChart("unsupported-chart-cache")

    category_reader = (
        _numeric_values
        if category_kind in {"date", "numeric"}
        else _category_values
    )
    categories = category_reader(series_nodes[0].find("c:cat", C_NS))
    if not categories:
        raise _UnsupportedChart("unsupported-chart-cache")

    series: list[dict[str, Any]] = []
    for idx, ser in enumerate(series_nodes, start=1):
        if category_reader(ser.find("c:cat", C_NS)) != categories:
            raise _UnsupportedChart("unsupported-chart-cache")
        values = _numeric_values(ser.find("c:val", C_NS))
        if not values or len(values) != len(categories):
            raise _UnsupportedChart("unsupported-chart-cache")
        series.append({
            "name": _series_name(ser, idx),
            "values": values,
        })

    payload: dict[str, Any] = {
        **_bounds_payload(xfrm),
        "categories": categories,
        "series": series,
        "type": chart_type,
    }
    grouping = _element_val(chart.find("c:grouping", C_NS))
    if grouping and chart_type in {"area", "bar", "column", "line"}:
        payload["grouping"] = grouping
    if chart_type == "line":
        payload["line_style"] = _line_style(chart, series_nodes)
    if chart_type == "of_pie":
        payload["of_pie_type"] = _element_val(chart.find("c:ofPieType", C_NS)) or "pie"
    return payload


def _xy_payload(chart: ET.Element, chart_type: str, xfrm: Xfrm) -> dict[str, Any]:
    series_nodes = chart.findall("c:ser", C_NS)
    if not series_nodes:
        raise _UnsupportedChart("unsupported-chart-cache")

    series: list[dict[str, Any]] = []
    for idx, ser in enumerate(series_nodes, start=1):
        x_values = _numeric_values(ser.find("c:xVal", C_NS))
        y_values = _numeric_values(ser.find("c:yVal", C_NS))
        if not x_values or len(x_values) != len(y_values):
            raise _UnsupportedChart("unsupported-chart-cache")
        item: dict[str, Any] = {
            "name": _series_name(ser, idx),
            "x": x_values,
            "y": y_values,
        }
        if chart_type == "bubble":
            sizes = _numeric_values(ser.find("c:bubbleSize", C_NS))
            if len(sizes) != len(x_values):
                raise _UnsupportedChart("unsupported-chart-cache")
            item["sizes"] = sizes
        series.append(item)

    payload: dict[str, Any] = {
        **_bounds_payload(xfrm),
        "series": series,
        "type": chart_type,
    }
    return payload


def _bar_chart_type(chart: ET.Element) -> str:
    return "bar" if _element_val(chart.find("c:barDir", C_NS)) == "bar" else "column"


def _line_style(chart: ET.Element, series_nodes: list[ET.Element]) -> str:
    symbols = [
        _element_val(ser.find("c:marker/c:symbol", C_NS))
        for ser in series_nodes
    ]
    if symbols and all(symbol == "none" for symbol in symbols):
        return "line"
    if any(symbol not in {None, "none"} for symbol in symbols):
        return "lineMarker"
    marker = chart.find("c:marker", C_NS)
    if marker is not None and ooxml_bool(marker.attrib.get("val"), True):
        return "lineMarker"
    return "line"


def _category_values(cat: ET.Element | None) -> list[str]:
    cache = _first_cache(cat, ("strCache", "strLit"))
    if cache is not None:
        return [str(value) for value in _cache_point_values(cache)]
    cache = _first_cache(cat, ("numCache", "numLit"))
    if cache is None:
        return []
    format_code = cache.findtext("c:formatCode", default="", namespaces=C_NS).strip()
    if format_code and format_code.lower() != "general":
        raise _UnsupportedChart("unsupported-formatted-category-cache")
    numbers = _numeric_cache_values(cache)
    return [str(value) for value in numbers]


def _category_cache_is_numeric(chart: ET.Element) -> bool:
    """Return the cache representation shared by every series in one plot."""
    result: bool | None = None
    for series in chart.findall("c:ser", C_NS):
        category = series.find("c:cat", C_NS)
        has_text = _first_cache(category, ("strCache", "strLit")) is not None
        has_number = _first_cache(category, ("numCache", "numLit")) is not None
        if has_text == has_number:
            raise _UnsupportedChart("unsupported-combo-category-layout")
        current = has_number
        if result is not None and current != result:
            raise _UnsupportedChart("unsupported-combo-category-layout")
        result = current
    if result is None:
        raise _UnsupportedChart("unsupported-combo-category-layout")
    return result


def _numeric_category_cache_format(chart: ET.Element) -> str:
    """Return one exact numeric category-cache format shared by the plot."""
    formats: set[str] = set()
    for series in chart.findall("c:ser", C_NS):
        cache = _first_cache(
            series.find("c:cat", C_NS),
            ("numCache", "numLit"),
        )
        if cache is None:
            raise _UnsupportedChart("unsupported-chart-category-format")
        number_format = cache.findtext(
            "c:formatCode",
            default="",
            namespaces=C_NS,
        )
        if not number_format.strip():
            raise _UnsupportedChart("unsupported-chart-category-format")
        formats.add(number_format)
    if len(formats) != 1:
        raise _UnsupportedChart("unsupported-chart-category-format")
    return next(iter(formats))


def _series_name(ser: ET.Element, index: int) -> str:
    tx = ser.find("c:tx", C_NS)
    values = _text_cache_values(tx)
    if values:
        return values[0]
    direct = tx.findtext("c:v", default="", namespaces=C_NS) if tx is not None else ""
    return direct or f"Series {index}"


def _text_cache_values(parent: ET.Element | None) -> list[str]:
    cache = _first_cache(parent, ("strCache", "strLit"))
    if cache is not None:
        return [str(value) for value in _cache_point_values(cache)]
    cache = _first_cache(parent, ("numCache", "numLit"))
    return [str(value) for value in _cache_point_values(cache)]


def _numeric_values(parent: ET.Element | None) -> list[int | float]:
    cache = _first_cache(parent, ("numCache", "numLit"))
    if cache is None:
        return []
    return _numeric_cache_values(cache)


def _numeric_cache_values(cache: ET.Element) -> list[int | float]:
    values: list[int | float] = []
    for value in _cache_point_values(cache):
        number = float(value)
        if not math.isfinite(number):
            raise _UnsupportedChart("unsupported-chart-cache")
        values.append(int(number) if number.is_integer() else number)
    return values


def _first_cache(parent: ET.Element | None, names: tuple[str, ...]) -> ET.Element | None:
    if parent is None:
        return None
    for name in names:
        found = parent.find(f".//c:{name}", C_NS)
        if found is not None:
            return found
    return None


def _cache_point_values(cache: ET.Element | None) -> list[str]:
    if cache is None:
        return []
    points: dict[int, str] = {}
    for idx, point in enumerate(cache.findall("c:pt", C_NS)):
        raw_idx = point.attrib.get("idx")
        try:
            point_idx = int(raw_idx) if raw_idx is not None else idx
        except ValueError:
            raise _UnsupportedChart("unsupported-chart-cache")
        if point_idx < 0 or point_idx in points:
            raise _UnsupportedChart("unsupported-chart-cache")
        value = point.findtext("c:v", default="", namespaces=C_NS)
        points[point_idx] = value

    count_elem = cache.find("c:ptCount", C_NS)
    if count_elem is not None:
        try:
            point_count = int(count_elem.attrib.get("val", ""))
        except ValueError:
            raise _UnsupportedChart("unsupported-chart-cache")
    else:
        point_count = len(points)
    if (
        point_count < 0
        or point_count != len(points)
        or any(idx not in points for idx in range(point_count))
    ):
        raise _UnsupportedChart("unsupported-chart-cache")
    return [points[idx] for idx in range(point_count)]


def _element_val(elem: ET.Element | None) -> str | None:
    if elem is None:
        return None
    return elem.attrib.get("val")


def _bounds_payload(xfrm: Xfrm) -> dict[str, int | float]:
    return {
        "height": _round_payload_number(xfrm.h),
        "width": _round_payload_number(xfrm.w),
        "x": _round_payload_number(xfrm.x),
        "y": _round_payload_number(xfrm.y),
    }


def _round_payload_number(value: float) -> int | float:
    rounded = round(float(value), 3)
    return int(rounded) if rounded.is_integer() else rounded


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag
