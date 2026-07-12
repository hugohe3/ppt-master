"""Extract native ChartEx payloads from PPTX chart parts.

The parser is deliberately closed around the seven ChartEx data models that
the native writer already emits.  Data topology and caches must be complete;
unmodeled chart chrome, labels, axes, binning options, and style details are
allowed to normalize during editable native reconstruction.
"""

from __future__ import annotations

import math
import re
from typing import Any
from xml.etree import ElementTree as ET

from svg_to_pptx.native_objects.chart_data import validate_chart_payload
from svg_to_pptx.native_objects.marker_common import CHART_COLOR_STYLE_REL_TYPE

from .color_resolver import COLOR_TAGS, ColorPalette, resolve_color
from .emu_units import NS, Xfrm
from .ooxml_loader import OoxmlPackage, PartRef


CHARTEX_URI = "http://schemas.microsoft.com/office/drawing/2014/chartex"

CX_NS = {
    **NS,
    "cx": CHARTEX_URI,
}

_INT_TOKEN_RE = re.compile(r"[0-9]+")
_HIERARCHY_LAYOUTS = {"sunburst", "treemap"}
_FLAT_LAYOUTS = {"funnel", "waterfall"}
_LEGEND_POSITIONS = {"b", "l", "r", "t"}


class UnsupportedChartEx(RuntimeError):
    """A ChartEx part cannot map to the current native authoring schema."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


def extract_native_chartex_payload(
    graphic_data: ET.Element | None,
    xfrm: Xfrm,
    slide_part: PartRef,
    pkg: OoxmlPackage,
    palette: ColorPalette | None = None,
) -> dict[str, Any]:
    """Return a writer-valid payload for one supported ChartEx reference.

    ``UnsupportedChartEx.status`` is suitable for ``data-pptx-native-status``
    when the reference, relationship, data topology, or cache is unusable.
    Style-part failures never reject an otherwise valid data payload.
    """
    if graphic_data is None:
        raise UnsupportedChartEx("unsupported-chart-reference")
    if xfrm.rot or xfrm.flip_h or xfrm.flip_v:
        raise UnsupportedChartEx("unsupported-native-transform")

    chart_ref = graphic_data.find("cx:chart", CX_NS)
    if chart_ref is None:
        raise UnsupportedChartEx("unsupported-chart-reference")
    rid = chart_ref.attrib.get(f"{{{NS['r']}}}id")
    if not rid:
        raise UnsupportedChartEx("unsupported-chart-reference")

    chart_path = slide_part.resolve_rel(rid)
    if not chart_path:
        raise UnsupportedChartEx("unsupported-chart-relationship")
    chart_part = pkg.load_part(chart_path)
    if chart_part is None:
        raise UnsupportedChartEx("unsupported-chart-part")

    try:
        payload = _payload_from_chartex_xml(chart_part.xml, xfrm)
        colors = _resolved_chart_colors(chart_part, pkg, palette)
        if colors:
            payload["style"] = {"colors": colors}
        validate_chart_payload(payload)
    except UnsupportedChartEx:
        raise
    except RuntimeError as exc:
        raise UnsupportedChartEx("unsupported-chartex-schema") from exc
    except (AttributeError, OverflowError, TypeError, ValueError) as exc:
        raise UnsupportedChartEx("unsupported-chartex-parse") from exc
    return payload


def _payload_from_chartex_xml(
    chart_root: ET.Element,
    xfrm: Xfrm,
) -> dict[str, Any]:
    if chart_root.tag != f"{{{CHARTEX_URI}}}chartSpace":
        raise UnsupportedChartEx("unsupported-chartex-part")

    chart_data = _one_child(chart_root, "chartData", "unsupported-chartex-structure")
    chart = _one_child(chart_root, "chart", "unsupported-chartex-structure")
    plot_area = _one_child(chart, "plotArea", "unsupported-chartex-structure")
    region = _one_child(plot_area, "plotAreaRegion", "unsupported-chartex-structure")

    data_by_id = _data_parts(chart_data)
    series_nodes = _children(region, "series")
    if not series_nodes:
        raise UnsupportedChartEx("unsupported-chartex-series")

    chart_type = _chart_type(series_nodes)
    payload: dict[str, Any] = {
        **_bounds_payload(xfrm),
        "type": chart_type,
    }

    referenced_data_ids: list[int]
    if chart_type in _HIERARCHY_LAYOUTS:
        data_id = _series_data_id(series_nodes[0])
        data = _require_data(data_by_id, data_id)
        raw_levels = _string_dimension(data, expected_levels=None)
        values = _numeric_dimension(data, "size")
        if not raw_levels or any(len(level) != len(values) for level in raw_levels):
            raise UnsupportedChartEx("unsupported-chartex-cache")
        # ChartEx serializes the innermost level first; the authoring schema
        # and workbook writer use the natural outermost-to-innermost order.
        payload["levels"] = list(reversed(raw_levels))
        payload["values"] = values
        if chart_type == "treemap":
            parent_labels = _treemap_parent_labels(series_nodes[0])
            if parent_labels is not None:
                payload["parent_label_layout"] = parent_labels
        referenced_data_ids = [data_id]
    elif chart_type == "histogram":
        data_id = _series_data_id(series_nodes[0])
        data = _require_data(data_by_id, data_id)
        _reject_dimensions(data, allowed={"numDim"})
        payload["values"] = _numeric_dimension(data, "val")
        referenced_data_ids = [data_id]
    elif chart_type in {"funnel", "pareto", "waterfall"}:
        data_id = _series_data_id(series_nodes[0])
        data = _require_data(data_by_id, data_id)
        categories = _string_dimension(data, expected_levels=1)[0]
        values = _numeric_dimension(data, "val")
        if len(categories) != len(values):
            raise UnsupportedChartEx("unsupported-chartex-cache")
        payload["categories"] = categories
        payload["values"] = values
        if chart_type == "waterfall":
            payload["subtotals"] = _waterfall_subtotals(series_nodes[0])
        referenced_data_ids = [data_id]
    elif chart_type == "box_whisker":
        items: list[dict[str, Any]] = []
        referenced_data_ids = []
        for index, series in enumerate(series_nodes, start=1):
            data_id = _series_data_id(series)
            if data_id in referenced_data_ids:
                raise UnsupportedChartEx("unsupported-chartex-data-id")
            data = _require_data(data_by_id, data_id)
            categories = _string_dimension(data, expected_levels=1)[0]
            values = _numeric_dimension(data, "val")
            if len(categories) != len(values):
                raise UnsupportedChartEx("unsupported-chartex-cache")
            items.append({
                "categories": categories,
                "name": _series_name(series, index),
                "values": values,
            })
            referenced_data_ids.append(data_id)
        payload["series"] = items
    else:  # pragma: no cover - _chart_type is closed, keep the invariant explicit.
        raise UnsupportedChartEx("unsupported-chartex-type")

    if set(referenced_data_ids) != set(data_by_id):
        raise UnsupportedChartEx("unsupported-chartex-data-id")

    legend = chart.find("cx:legend", CX_NS)
    if legend is not None:
        payload["show_legend"] = True
        position = legend.attrib.get("pos")
        if position in _LEGEND_POSITIONS:
            payload["legend_position"] = position
    return payload


def _chart_type(series_nodes: list[ET.Element]) -> str:
    layouts = [series.attrib.get("layoutId", "") for series in series_nodes]
    if len(series_nodes) == 1 and layouts[0] in _HIERARCHY_LAYOUTS | _FLAT_LAYOUTS:
        return layouts[0]
    if layouts and all(layout == "boxWhisker" for layout in layouts):
        return "box_whisker"
    if len(series_nodes) == 1 and layouts == ["clusteredColumn"]:
        if series_nodes[0].find("cx:layoutPr/cx:binning", CX_NS) is None:
            raise UnsupportedChartEx("unsupported-chartex-series")
        return "histogram"
    if len(series_nodes) == 2 and layouts == ["clusteredColumn", "paretoLine"]:
        primary, line = series_nodes
        if (
            primary.find("cx:layoutPr/cx:aggregation", CX_NS) is None
            or line.attrib.get("ownerIdx") != "0"
            or line.find("cx:dataId", CX_NS) is not None
        ):
            raise UnsupportedChartEx("unsupported-chartex-series")
        return "pareto"
    raise UnsupportedChartEx("unsupported-chartex-type")


def _data_parts(chart_data: ET.Element) -> dict[int, ET.Element]:
    result: dict[int, ET.Element] = {}
    for data in _children(chart_data, "data"):
        data_id = _nonnegative_int(data.attrib.get("id"), "unsupported-chartex-data-id")
        if data_id in result:
            raise UnsupportedChartEx("unsupported-chartex-data-id")
        result[data_id] = data
    if not result:
        raise UnsupportedChartEx("unsupported-chartex-data-id")
    return result


def _series_data_id(series: ET.Element) -> int:
    data_ids = _children(series, "dataId")
    if len(data_ids) != 1:
        raise UnsupportedChartEx("unsupported-chartex-data-id")
    return _nonnegative_int(
        data_ids[0].attrib.get("val"),
        "unsupported-chartex-data-id",
    )


def _require_data(data_by_id: dict[int, ET.Element], data_id: int) -> ET.Element:
    data = data_by_id.get(data_id)
    if data is None:
        raise UnsupportedChartEx("unsupported-chartex-data-id")
    return data


def _string_dimension(
    data: ET.Element,
    *,
    expected_levels: int | None,
) -> list[list[str]]:
    _reject_dimensions(data, allowed={"strDim", "numDim"})
    dimensions = [
        child
        for child in _children(data, "strDim")
        if child.attrib.get("type") == "cat"
    ]
    if len(dimensions) != 1 or len(_children(data, "strDim")) != 1:
        raise UnsupportedChartEx("unsupported-chartex-dimension")
    levels = _children(dimensions[0], "lvl")
    if not levels or (expected_levels is not None and len(levels) != expected_levels):
        raise UnsupportedChartEx("unsupported-chartex-dimension")
    return [_level_values(level, numeric=False) for level in levels]


def _numeric_dimension(data: ET.Element, dim_type: str) -> list[int | float]:
    dimensions = [
        child
        for child in _children(data, "numDim")
        if child.attrib.get("type") == dim_type
    ]
    if len(dimensions) != 1 or len(_children(data, "numDim")) != 1:
        raise UnsupportedChartEx("unsupported-chartex-dimension")
    levels = _children(dimensions[0], "lvl")
    if len(levels) != 1:
        raise UnsupportedChartEx("unsupported-chartex-dimension")
    return _level_values(levels[0], numeric=True)


def _reject_dimensions(data: ET.Element, *, allowed: set[str]) -> None:
    for child in data:
        name = _local_name(child.tag)
        if name.endswith("Dim") and name not in allowed:
            raise UnsupportedChartEx("unsupported-chartex-dimension")


def _level_values(
    level: ET.Element,
    *,
    numeric: bool,
) -> list[Any]:
    point_count = _nonnegative_int(
        level.attrib.get("ptCount"),
        "unsupported-chartex-cache",
    )
    points: dict[int, Any] = {}
    for point in _children(level, "pt"):
        point_index = _nonnegative_int(
            point.attrib.get("idx"),
            "unsupported-chartex-cache",
        )
        if point_index >= point_count or point_index in points or list(point):
            raise UnsupportedChartEx("unsupported-chartex-cache")
        raw_value = point.text or ""
        points[point_index] = (
            _numeric_value(raw_value)
            if numeric
            else raw_value
        )
    if (
        len(points) != point_count
        or any(index not in points for index in range(point_count))
    ):
        raise UnsupportedChartEx("unsupported-chartex-cache")
    return [points[index] for index in range(point_count)]


def _numeric_value(raw_value: str) -> int | float:
    if not raw_value.strip():
        raise UnsupportedChartEx("unsupported-chartex-cache")
    try:
        number = float(raw_value)
    except (OverflowError, ValueError):
        raise UnsupportedChartEx("unsupported-chartex-cache") from None
    if not math.isfinite(number):
        raise UnsupportedChartEx("unsupported-chartex-cache")
    return int(number) if number.is_integer() else number


def _waterfall_subtotals(series: ET.Element) -> list[int]:
    subtotals: list[int] = []
    for item in series.findall("cx:layoutPr/cx:subtotals/cx:idx", CX_NS):
        subtotals.append(
            _nonnegative_int(item.attrib.get("val"), "unsupported-chartex-cache")
        )
    return subtotals


def _treemap_parent_labels(series: ET.Element) -> str | None:
    parent = series.find("cx:layoutPr/cx:parentLabelLayout", CX_NS)
    if parent is None:
        return None
    value = parent.attrib.get("val")
    return value if value in {"banner", "none", "overlapping"} else None


def _series_name(series: ET.Element, index: int) -> str:
    value = series.findtext("cx:tx/cx:txData/cx:v", default="", namespaces=CX_NS)
    return value or f"Series {index}"


def _resolved_chart_colors(
    chart_part: PartRef,
    pkg: OoxmlPackage,
    palette: ColorPalette | None,
) -> list[str]:
    """Resolve the base color cycle; any style failure normalizes silently."""
    try:
        targets = [
            info.get("target")
            for info in chart_part.rels.values()
            if info.get("type") == CHART_COLOR_STYLE_REL_TYPE
            and not info.get("external")
            and info.get("target")
        ]
        if len(targets) != 1:
            return []
        colors_part = pkg.load_part(str(targets[0]))
        if colors_part is None:
            return []
        color_nodes = [
            child
            for child in colors_part.xml
            if _namespace(child.tag) == NS["a"]
            and _local_name(child.tag) in COLOR_TAGS
        ]
        if not color_nodes:
            return []
        colors: list[str] = []
        for color_node in color_nodes:
            color, _alpha = resolve_color(color_node, palette)
            if color is None:
                return []
            colors.append(color)
        return colors
    except (AttributeError, OverflowError, RuntimeError, TypeError, ValueError):
        return []


def _one_child(parent: ET.Element, name: str, status: str) -> ET.Element:
    children = _children(parent, name)
    if len(children) != 1:
        raise UnsupportedChartEx(status)
    return children[0]


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [
        child
        for child in parent
        if child.tag == f"{{{CHARTEX_URI}}}{name}"
    ]


def _nonnegative_int(raw_value: str | None, status: str) -> int:
    if raw_value is None or _INT_TOKEN_RE.fullmatch(raw_value) is None:
        raise UnsupportedChartEx(status)
    value = int(raw_value)
    if value < 0:
        raise UnsupportedChartEx(status)
    return value


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


def _namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag
