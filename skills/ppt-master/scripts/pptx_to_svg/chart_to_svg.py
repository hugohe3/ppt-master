"""Extract editable native chart metadata from PPTX chart parts.

The visual chart preview still comes from the existing graphicFrame fallback.
This module only builds a conservative ``data-pptx-native="chart"`` payload
when the chart XML cache can be mapped to the current native chart schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from svg_to_pptx.native_objects.chart_data import _chart_data

from .emu_units import NS, Xfrm
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

    chart = chart_nodes[0]
    chart_tag = _local_name(chart.tag)
    if chart_tag in {"area3DChart", "bar3DChart", "line3DChart", "pie3DChart", "surface3DChart"}:
        raise _UnsupportedChart("unsupported-3d-chart")
    if chart_tag == "barChart":
        return _category_payload(chart, _bar_chart_type(chart), xfrm)
    if chart_tag in {"areaChart", "lineChart", "ofPieChart", "pieChart", "doughnutChart"}:
        chart_type = {
            "areaChart": "area",
            "lineChart": "line",
            "ofPieChart": "of_pie",
            "pieChart": "pie",
            "doughnutChart": "doughnut",
        }[chart_tag]
        return _category_payload(chart, chart_type, xfrm)
    if chart_tag == "scatterChart":
        return _xy_payload(chart, "scatter", xfrm)
    if chart_tag == "bubbleChart":
        return _xy_payload(chart, "bubble", xfrm)
    raise _UnsupportedChart("unsupported-chart-type")


def _category_payload(chart: ET.Element, chart_type: str, xfrm: Xfrm) -> dict[str, Any]:
    series_nodes = chart.findall("c:ser", C_NS)
    if not series_nodes:
        raise _UnsupportedChart("unsupported-chart-cache")

    categories = _category_values(series_nodes[0].find("c:cat", C_NS))
    if not categories:
        raise _UnsupportedChart("unsupported-chart-cache")

    series: list[dict[str, Any]] = []
    for idx, ser in enumerate(series_nodes, start=1):
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
    if _element_val(chart.find("c:marker", C_NS)) == "1":
        return "lineMarker"
    for ser in series_nodes:
        marker_symbol = _element_val(ser.find("c:marker/c:symbol", C_NS))
        if marker_symbol and marker_symbol != "none":
            return "lineMarker"
    return "line"


def _category_values(cat: ET.Element | None) -> list[str]:
    values = _text_cache_values(cat)
    if values:
        return values
    numbers = _numeric_values(cat)
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
    values: list[int | float] = []
    for value in _cache_point_values(cache):
        number = float(value)
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
    points: list[tuple[int, str]] = []
    for idx, point in enumerate(cache.findall("c:pt", C_NS)):
        raw_idx = point.attrib.get("idx")
        try:
            point_idx = int(raw_idx) if raw_idx is not None else idx
        except ValueError:
            point_idx = idx
        value = point.findtext("c:v", default="", namespaces=C_NS)
        points.append((point_idx, value))
    return [value for _, value in sorted(points, key=lambda item: item[0])]


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
