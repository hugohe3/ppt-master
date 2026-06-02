"""Read native PowerPoint chart display caches for slide-library analysis.

The template-fill workflow edits chart data from explicit fill plans. This
module only reads the data currently visible in a chart XML part, keeping
workbook parsing out of the analyzer.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import NS


def empty_chart_data() -> dict[str, Any]:
    return {
        "chart_type": None,
        "category_count": 0,
        "series_count": 0,
        "categories": [],
        "series": [],
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _chart_type_with_series(chart_root: ET.Element) -> ET.Element | None:
    plot_area = chart_root.find(".//c:plotArea", NS)
    if plot_area is None:
        return None
    for child in list(plot_area):
        if _local_name(child.tag).endswith("Chart") and child.findall("c:ser", NS):
            return child
    return None


def _coerce_number(value: str) -> int | float | str:
    try:
        number = float(value)
    except ValueError:
        return value
    if number.is_integer():
        return int(number)
    return number


def _cache_values(parent: ET.Element | None, *, numeric: bool = False) -> list[Any]:
    if parent is None:
        return []
    cache = parent.find(".//c:strCache", NS)
    if cache is None:
        cache = parent.find(".//c:numCache", NS)
    if cache is None:
        return []
    values: list[Any] = []
    for point in cache.findall("c:pt", NS):
        value = point.findtext("c:v", default="", namespaces=NS)
        values.append(_coerce_number(value) if numeric else value)
    return values


def _series_name(series: ET.Element, fallback: str) -> str:
    tx = series.find("c:tx", NS)
    if tx is None:
        return fallback
    values = _cache_values(tx)
    if values:
        return str(values[0])
    direct = tx.findtext("c:v", default="", namespaces=NS)
    return direct or fallback


def read_chart_data(chart_root: ET.Element) -> dict[str, Any]:
    """Return a compact summary of chart type, categories, series, and values."""
    chart_type = _chart_type_with_series(chart_root)
    if chart_type is None:
        return empty_chart_data()

    series_nodes = chart_type.findall("c:ser", NS)
    categories = _cache_values(series_nodes[0].find("c:cat", NS)) if series_nodes else []
    series_payload: list[dict[str, Any]] = []
    for index, series in enumerate(series_nodes, start=1):
        series_payload.append(
            {
                "name": _series_name(series, f"系列{index}"),
                "values": _cache_values(series.find("c:val", NS), numeric=True),
            }
        )

    return {
        "chart_type": _local_name(chart_type.tag),
        "category_count": len(categories),
        "series_count": len(series_payload),
        "categories": categories,
        "series": series_payload,
    }
