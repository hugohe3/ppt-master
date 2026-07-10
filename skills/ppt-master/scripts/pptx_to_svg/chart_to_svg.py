"""Extract editable native chart metadata from PPTX chart parts.

The visual chart preview still comes from the existing graphicFrame fallback.
This module only builds a conservative ``data-pptx-native="chart"`` payload
when the chart XML cache can be mapped to the current native chart schema.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from svg_to_pptx.drawingml.utils import parse_font_family
from svg_to_pptx.native_objects.chart_data import _chart_data, _data_label_position

from .emu_units import NS, Xfrm, ooxml_bool
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
) -> ChartResult:
    """Return native chart metadata for a supported classic chart."""
    if graphic_data is None:
        return ChartResult(native_status="unsupported-chart-reference")

    uri = graphic_data.attrib.get("uri", "")
    if uri == CHARTEX_URI or graphic_data.find("cx:chart", C_NS) is not None:
        return ChartResult(native_status="unsupported-chartex")
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
        payload = _payload_from_chart_xml(chart_part.xml, xfrm)
        _chart_data(payload)
    except _UnsupportedChart as exc:
        return ChartResult(native_status=exc.status)
    except RuntimeError:
        return ChartResult(native_status="unsupported-chart-schema")
    except (TypeError, ValueError, AttributeError):
        return ChartResult(native_status="unsupported-chart-parse")
    return ChartResult(native_payload=payload)


def _payload_from_chart_xml(chart_root: ET.Element, xfrm: Xfrm) -> dict[str, Any]:
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
    if len(chart_nodes) > 1:
        raise _UnsupportedChart("unsupported-combo-chart")
    if plot_area.find("c:dateAx", C_NS) is not None:
        raise _UnsupportedChart("unsupported-date-axis")

    chart = chart_nodes[0]
    chart_tag = _local_name(chart.tag)
    if chart_tag in {"area3DChart", "bar3DChart", "line3DChart", "pie3DChart", "surface3DChart"}:
        raise _UnsupportedChart("unsupported-3d-chart")
    if chart_tag == "barChart":
        payload = _category_payload(chart, _bar_chart_type(chart), xfrm)
    elif chart_tag in {"areaChart", "lineChart", "ofPieChart", "pieChart", "doughnutChart"}:
        chart_type = {
            "areaChart": "area",
            "lineChart": "line",
            "ofPieChart": "of_pie",
            "pieChart": "pie",
            "doughnutChart": "doughnut",
        }[chart_tag]
        payload = _category_payload(chart, chart_type, xfrm)
    elif chart_tag == "scatterChart":
        payload = _xy_payload(chart, "scatter", xfrm)
    elif chart_tag == "bubbleChart":
        payload = _xy_payload(chart, "bubble", xfrm)
    else:
        raise _UnsupportedChart("unsupported-chart-type")

    _validate_chart_semantics(payload, plot_area, chart)
    _apply_chart_metadata(payload, chart_root, plot_area, chart)
    return payload


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


def _canonical_sp_pr_color(sp_pr: ET.Element, *, line_visible: bool) -> str:
    """Extract a color only from the exact series style emitted here."""
    if sp_pr.attrib:
        raise _UnsupportedChart("unsupported-chart-series-style")
    children = list(sp_pr)
    if [_local_name(child.tag) for child in children] != ["solidFill", "ln"]:
        raise _UnsupportedChart("unsupported-chart-series-style")
    color = _canonical_srgb_color(children[0])
    line = children[1]
    if line.attrib or len(line) != 1:
        raise _UnsupportedChart("unsupported-chart-series-style")
    line_child = line[0]
    if line_visible:
        if _local_name(line_child.tag) != "solidFill":
            raise _UnsupportedChart("unsupported-chart-series-style")
        if _canonical_srgb_color(line_child) != color:
            raise _UnsupportedChart("unsupported-chart-series-style")
    elif (
        _local_name(line_child.tag) != "noFill"
        or line_child.attrib
        or list(line_child)
    ):
        raise _UnsupportedChart("unsupported-chart-series-style")
    return color


def _canonical_chart_colors(payload: dict[str, Any], plot: ET.Element) -> list[str] | None:
    """Recover colors from canonical series or pie data-point formatting."""
    chart_type = payload["type"]
    series_nodes = plot.findall("c:ser", C_NS)
    if chart_type in {"pie", "doughnut", "of_pie"}:
        if any(series.find("c:spPr", C_NS) is not None for series in series_nodes):
            raise _UnsupportedChart("unsupported-chart-series-style")
        point_nodes = [
            point
            for series in series_nodes
            for point in series.findall("c:dPt", C_NS)
        ]
        if not point_nodes:
            return None
        expected_count = len(payload["categories"]) + (1 if chart_type == "of_pie" else 0)
        colors: dict[int, str] = {}
        for point in point_nodes:
            if point.attrib or [_local_name(child.tag) for child in point] != ["idx", "spPr"]:
                raise _UnsupportedChart("unsupported-chart-series-style")
            idx = point.find("c:idx", C_NS)
            sp_pr = point.find("c:spPr", C_NS)
            try:
                point_index = int(idx.attrib.get("val", "")) if idx is not None else -1
            except ValueError:
                raise _UnsupportedChart("unsupported-chart-series-style") from None
            if (
                idx is None
                or set(idx.attrib) != {"val"}
                or list(idx)
                or sp_pr is None
                or point_index in colors
            ):
                raise _UnsupportedChart("unsupported-chart-series-style")
            colors[point_index] = _canonical_sp_pr_color(sp_pr, line_visible=True)
        if set(colors) != set(range(expected_count)):
            raise _UnsupportedChart("unsupported-chart-series-style")
        return [f"#{colors[index]}" for index in range(expected_count)]

    if any(series.find("c:dPt", C_NS) is not None for series in series_nodes):
        raise _UnsupportedChart("unsupported-chart-series-style")
    sp_pr_nodes = [series.find("c:spPr", C_NS) for series in series_nodes]
    if not any(sp_pr is not None for sp_pr in sp_pr_nodes):
        return None
    if any(sp_pr is None for sp_pr in sp_pr_nodes):
        raise _UnsupportedChart("unsupported-chart-series-style")
    line_visible = not (
        chart_type == "scatter"
        and payload.get("scatter_style", "marker") == "marker"
    )
    return [
        f"#{_canonical_sp_pr_color(sp_pr, line_visible=line_visible)}"
        for sp_pr in sp_pr_nodes
        if sp_pr is not None
    ]


def _validate_chart_semantics(
    payload: dict[str, Any],
    plot_area: ET.Element,
    plot: ET.Element,
) -> None:
    """Reject valid chart features the compact marker cannot reproduce."""
    chart_type = payload["type"]
    colors = _canonical_chart_colors(payload, plot)
    if colors:
        payload["style"] = {"colors": colors}
    for tag in (
        "trendline", "errBars", "dropLines", "hiLowLines", "upDownBars",
    ):
        if plot.find(f".//c:{tag}", C_NS) is not None:
            raise _UnsupportedChart("unsupported-chart-analysis-features")
    if plot_area.find("c:dTable", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-data-table")
    ser_lines = plot.find("c:serLines", C_NS)
    if ser_lines is not None and (
        chart_type != "of_pie" or ser_lines.attrib or list(ser_lines)
    ):
        raise _UnsupportedChart("unsupported-chart-analysis-features")

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
            if marker_node is not None and any(
                child.tag.rsplit("}", 1)[-1] != "symbol"
                for child in marker_node
            ):
                raise _UnsupportedChart("unsupported-chart-line-style")
            symbol = _element_val(series.find("c:marker/c:symbol", C_NS))
            if symbol not in {None, "circle", "none"}:
                raise _UnsupportedChart("unsupported-chart-line-style")
            marker_states.add(plot_has_markers if symbol is None else symbol != "none")
        if len(marker_states) > 1:
            raise _UnsupportedChart("unsupported-chart-line-style")

    if chart_type in {"bar", "column"}:
        gap_width = _element_val(plot.find("c:gapWidth", C_NS))
        if gap_width not in {None, "150"}:
            raise _UnsupportedChart("unsupported-chart-bar-options")
        overlap = _element_val(plot.find("c:overlap", C_NS))
        expected_overlap = "100" if grouping in {"stacked", "percentStacked"} else "0"
        if overlap is None:
            if expected_overlap != "0":
                raise _UnsupportedChart("unsupported-chart-bar-options")
        elif overlap != expected_overlap:
            raise _UnsupportedChart("unsupported-chart-bar-options")

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
        scatter_style = _element_val(plot.find("c:scatterStyle", C_NS)) or "marker"
        expected_marker = (
            "circle"
            if scatter_style in {"lineMarker", "marker", "smoothMarker"}
            else "none"
        )
        expected_smooth = scatter_style in {"smooth", "smoothMarker"}
        for series in plot.findall("c:ser", C_NS):
            marker = series.find("c:marker", C_NS)
            if marker is None:
                raise _UnsupportedChart("unsupported-chart-scatter-style")
            if any(
                child.tag.rsplit("}", 1)[-1] != "symbol"
                for child in marker
            ):
                raise _UnsupportedChart("unsupported-chart-scatter-style")
            symbol = _element_val(marker.find("c:symbol", C_NS))
            if symbol != expected_marker:
                raise _UnsupportedChart("unsupported-chart-scatter-style")
            smooth = series.find("c:smooth", C_NS)
            actual_smooth = bool(
                smooth is not None and ooxml_bool(smooth.attrib.get("val"), True)
            )
            if actual_smooth != expected_smooth:
                raise _UnsupportedChart("unsupported-chart-scatter-style")

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


def _apply_chart_metadata(
    payload: dict[str, Any],
    chart_root: ET.Element,
    plot_area: ET.Element,
    plot: ET.Element,
) -> None:
    """Copy visible classic-chart chrome supported by the native schema."""
    chart = chart_root.find("c:chart", C_NS)
    if chart is None:
        return

    title_element = chart.find("c:title", C_NS)
    overlay = title_element.find("c:overlay", C_NS) if title_element is not None else None
    if overlay is not None and ooxml_bool(overlay.attrib.get("val"), True):
        raise _UnsupportedChart("unsupported-chart-title-overlay")
    title_entries = _canonical_title_entries(title_element)
    if (
        title_element is not None
        and title_element.find("c:tx/c:rich", C_NS) is not None
        and title_entries is None
    ):
        raise _UnsupportedChart("unsupported-chart-title-format")
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
            if legend.find("c:legendEntry", C_NS) is not None:
                raise _UnsupportedChart("unsupported-chart-legend-filter")
            overlay = legend.find("c:overlay", C_NS)
            if overlay is not None and ooxml_bool(overlay.attrib.get("val"), True):
                raise _UnsupportedChart("unsupported-chart-legend-overlay")
            position = _element_val(legend.find("c:legendPos", C_NS)) or "r"
            if position not in {"b", "l", "r", "t"}:
                raise _UnsupportedChart("unsupported-chart-legend-position")
            payload["show_legend"] = True
            payload["legend_position"] = position

    if plot.find("c:ser/c:dLbls", C_NS) is not None:
        raise _UnsupportedChart("unsupported-chart-series-data-labels")
    data_labels = _data_labels_payload(plot.find("c:dLbls", C_NS))
    if data_labels:
        if payload["type"] not in {"area", "bar", "column", "line"}:
            raise _UnsupportedChart("unsupported-chart-data-labels")
        try:
            _data_label_position(
                data_labels.get("position"),
                payload["type"],
                payload.get("grouping"),
            )
        except RuntimeError:
            raise _UnsupportedChart("unsupported-chart-data-labels") from None
        payload["data_labels"] = data_labels

    axis_titles: dict[str, str] = {}
    category_titles = [
        text
        for axis in plot_area.findall("c:catAx", C_NS)
        if (text := _chart_text(axis.find("c:title", C_NS)))
    ]
    value_titles = [
        text
        for axis in plot_area.findall("c:valAx", C_NS)
        if (text := _chart_text(axis.find("c:title", C_NS)))
    ]
    if payload["type"] in {"scatter", "bubble"}:
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


def _category_payload(chart: ET.Element, chart_type: str, xfrm: Xfrm) -> dict[str, Any]:
    series_nodes = chart.findall("c:ser", C_NS)
    if not series_nodes:
        raise _UnsupportedChart("unsupported-chart-cache")

    categories = _category_values(series_nodes[0].find("c:cat", C_NS))
    if not categories:
        raise _UnsupportedChart("unsupported-chart-cache")

    series: list[dict[str, Any]] = []
    for idx, ser in enumerate(series_nodes, start=1):
        if _category_values(ser.find("c:cat", C_NS)) != categories:
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
    if chart_type == "scatter":
        style = _element_val(chart.find("c:scatterStyle", C_NS))
        if style:
            payload["scatter_style"] = style
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
