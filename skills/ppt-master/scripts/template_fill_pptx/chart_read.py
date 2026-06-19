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


def _chart_types_with_series(chart_root: ET.Element) -> list[ET.Element]:
    plot_area = chart_root.find(".//c:plotArea", NS)
    if plot_area is None:
        return []
    chart_types: list[ET.Element] = []
    for child in list(plot_area):
        if _local_name(child.tag).endswith("Chart") and child.findall("c:ser", NS):
            chart_types.append(child)
    return chart_types


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
    chart_types = _chart_types_with_series(chart_root)
    if not chart_types:
        return empty_chart_data()

    first_series = chart_types[0].find("c:ser", NS)
    categories = _cache_values(first_series.find("c:cat", NS)) if first_series is not None else []
    series_payload: list[dict[str, Any]] = []
    plot_types: list[str] = []
    for chart_type in chart_types:
        plot_name = _local_name(chart_type.tag)
        plot_types.append(plot_name)
        for series in chart_type.findall("c:ser", NS):
            index = len(series_payload) + 1
            series_categories = _cache_values(series.find("c:cat", NS))
            if not categories and series_categories:
                categories = series_categories
            series_payload.append(
                {
                    "name": _series_name(series, f"系列{index}"),
                    "values": _cache_values(series.find("c:val", NS), numeric=True),
                    "chart_type": plot_name,
                }
            )

    return {
        "chart_type": plot_types[0] if len(set(plot_types)) == 1 else "comboChart",
        "plot_types": plot_types,
        "category_count": len(categories),
        "series_count": len(series_payload),
        "categories": categories,
        "series": series_payload,
    }
