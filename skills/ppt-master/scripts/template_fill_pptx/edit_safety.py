"""Classify template-fill chart and table edits before package mutation."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import NS, _qn

_XY_PLOTS = frozenset({"bubbleChart", "scatterChart"})


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _tag_namespace(tag: str) -> str:
    if not tag.startswith("{") or "}" not in tag:
        return ""
    return tag[1:].split("}", 1)[0]


def _chart_reference(frame: ET.Element) -> tuple[str, str]:
    """Return ``(classic|chartex|unknown, relationship id)`` for a chart frame."""
    graphic_data = frame.find(".//a:graphicData", NS)
    if graphic_data is None:
        return "", ""

    for node in graphic_data.iter():
        if _local_name(node.tag) != "chart":
            continue
        namespace = _tag_namespace(node.tag)
        rel_id = node.attrib.get(_qn(NS["r"], "id"), "")
        if namespace == NS["c"]:
            return "classic", rel_id
        if "chartex" in namespace.lower():
            return "chartex", rel_id
        return "unknown", rel_id

    uri = graphic_data.attrib.get("uri", "").lower()
    if "chartex" in uri:
        return "chartex", ""
    if "chart" in uri:
        return "unknown", ""
    return "", ""


def _chart_frames(slide_root: ET.Element) -> list[ET.Element]:
    """Return classic, ChartEx, and unknown chart graphic frames."""
    return [
        frame
        for frame in slide_root.findall(".//p:graphicFrame", NS)
        if _chart_reference(frame)[0]
    ]


def _unsupported_chart_capability(
    code: str,
    message: str,
    *,
    plot_type: str | None = None,
    plot_count: int = 0,
    data_model: str = "unknown",
) -> dict[str, Any]:
    return {
        "supported": False,
        "code": code,
        "message": message,
        "plot_type": plot_type,
        "plot_count": plot_count,
        "data_model": data_model,
    }


def _chart_edit_capability(chart_root: ET.Element) -> dict[str, Any]:
    """Classify whether the category cache writer can safely edit a chart part."""
    root_namespace = _tag_namespace(chart_root.tag)
    if "chartex" in root_namespace.lower():
        return _unsupported_chart_capability(
            "chart_edit_chartex_unsupported",
            "template-fill chart edits do not support ChartEx",
        )
    if root_namespace != NS["c"]:
        return _unsupported_chart_capability(
            "chart_edit_plot_type_unsupported",
            "template-fill chart edits require a classic DrawingML chart part",
        )

    plot_area = chart_root.find(".//c:plotArea", NS)
    if plot_area is None:
        return _unsupported_chart_capability(
            "chart_edit_plot_type_unsupported",
            "template-fill chart edits require a classic chart plotArea",
        )

    plot_nodes = [
        child
        for child in list(plot_area)
        if _tag_namespace(child.tag) == NS["c"] and _local_name(child.tag).endswith("Chart")
    ]
    if len(plot_nodes) > 1:
        return _unsupported_chart_capability(
            "chart_edit_multi_plot_unsupported",
            "template-fill chart edits do not support multi-plot or combination charts",
            plot_count=len(plot_nodes),
        )
    if not plot_nodes:
        return _unsupported_chart_capability(
            "chart_edit_plot_type_unsupported",
            "template-fill chart edits require exactly one recognized chart plot",
        )

    plot = plot_nodes[0]
    plot_type = _local_name(plot.tag)
    if plot_type == "scatterChart":
        return _unsupported_chart_capability(
            "chart_edit_scatter_unsupported",
            "template-fill chart edits do not support scatter xVal/yVal data",
            plot_type=plot_type,
            plot_count=1,
            data_model="xy",
        )
    if plot_type == "bubbleChart":
        return _unsupported_chart_capability(
            "chart_edit_bubble_unsupported",
            "template-fill chart edits do not support bubble xVal/yVal/bubbleSize data",
            plot_type=plot_type,
            plot_count=1,
            data_model="bubble",
        )
    series_nodes = plot.findall("c:ser", NS)
    if not series_nodes:
        return _unsupported_chart_capability(
            "chart_edit_no_series",
            "template-fill chart edits require at least one editable series",
            plot_type=plot_type,
            plot_count=1,
            data_model="category",
        )
    for series in series_nodes:
        if any(
            series.find(f"c:{tag}", NS) is not None
            for tag in ("xVal", "yVal", "bubbleSize")
        ):
            return _unsupported_chart_capability(
                "chart_edit_data_model_unsupported",
                "template-fill chart edits require c:cat/c:val series",
                plot_type=plot_type,
                plot_count=1,
            )
        category = series.find("c:cat", NS)
        values = series.find("c:val", NS)
        if category is None or values is None:
            return _unsupported_chart_capability(
                "chart_edit_data_model_unsupported",
                "template-fill chart edits require c:cat/c:val on every series",
                plot_type=plot_type,
                plot_count=1,
            )
    capability_warnings: list[dict[str, str]] = []
    if plot_area.find("c:dateAx", NS) is not None:
        capability_warnings.append(
            {
                "code": "chart_edit_date_axis_flattened",
                "message": (
                    "template-fill will flatten date-axis categories to the "
                    "replacement single-level category cache"
                ),
            }
        )
    if any(
        series.find("c:cat/c:multiLvlStrRef", NS) is not None
        for series in series_nodes
    ):
        capability_warnings.append(
            {
                "code": "chart_edit_multilevel_categories_flattened",
                "message": (
                    "template-fill will flatten multi-level categories to the "
                    "replacement single-level category cache"
                ),
            }
        )

    return {
        "supported": True,
        "code": "chart_edit_category_single_plot",
        "message": "single classic plot uses c:cat/c:val series",
        "plot_type": plot_type,
        "plot_count": 1,
        "data_model": "category",
        "warnings": capability_warnings,
    }


def _is_verified_category_capability(capability: Any) -> bool:
    """Return whether an analyzer capability matches the runtime structural gate."""
    return bool(
        isinstance(capability, dict)
        and capability.get("supported") is True
        and capability.get("code") == "chart_edit_category_single_plot"
        and capability.get("data_model") == "category"
        and capability.get("plot_count") == 1
        and isinstance(capability.get("plot_type"), str)
        and bool(capability.get("plot_type"))
        and capability.get("plot_type") not in _XY_PLOTS
    )


def _require_supported_chart_edit(chart_root: ET.Element) -> dict[str, Any]:
    """Raise before mutation unless ``chart_root`` uses the verified category model."""
    capability = _chart_edit_capability(chart_root)
    if not _is_verified_category_capability(capability):
        code = capability.get("code") or "chart_edit_capability_unknown"
        message = capability.get("message") or "chart edit capability is unknown"
        raise RuntimeError(f"{message} [{code}]")
    return capability


def _ooxml_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "on", "true"}


def _positive_span(value: str | None) -> int:
    try:
        return max(int(value or "1"), 1)
    except ValueError:
        return 1


def _table_cell_merge_info(cell: ET.Element) -> dict[str, Any]:
    """Return the merge role encoded directly on one physical ``a:tc`` cell."""
    h_merge = _ooxml_bool(cell.attrib.get("hMerge"))
    v_merge = _ooxml_bool(cell.attrib.get("vMerge"))
    row_span = _positive_span(cell.attrib.get("rowSpan"))
    col_span = _positive_span(cell.attrib.get("gridSpan"))
    is_merge_slave = h_merge or v_merge
    is_merge_anchor = not is_merge_slave and (row_span > 1 or col_span > 1)
    merge_role = "slave" if is_merge_slave else "anchor" if is_merge_anchor else "none"
    return {
        "merge_role": merge_role,
        "is_merge_anchor": is_merge_anchor,
        "is_merge_slave": is_merge_slave,
        "row_span": row_span,
        "col_span": col_span,
        "h_merge": h_merge,
        "v_merge": v_merge,
    }


def _table_merge_topology(table: ET.Element) -> dict[str, Any]:
    """Describe merge anchors and physical slave cells in a DrawingML table."""
    cell_states: list[tuple[int, int, dict[str, Any]]] = []
    anchors: list[dict[str, int]] = []
    for row_index, row in enumerate(table.findall("a:tr", NS)):
        for col_index, cell in enumerate(row.findall("a:tc", NS)):
            info = _table_cell_merge_info(cell)
            cell_states.append((row_index, col_index, info))
            if info["is_merge_anchor"]:
                anchors.append(
                    {
                        "row": row_index,
                        "col": col_index,
                        "row_span": info["row_span"],
                        "col_span": info["col_span"],
                    }
                )

    covered_by: dict[tuple[int, int], dict[str, int]] = {}
    for anchor in anchors:
        for row_index in range(anchor["row"], anchor["row"] + anchor["row_span"]):
            for col_index in range(anchor["col"], anchor["col"] + anchor["col_span"]):
                if (row_index, col_index) == (anchor["row"], anchor["col"]):
                    continue
                covered_by.setdefault(
                    (row_index, col_index),
                    {"row": anchor["row"], "col": anchor["col"]},
                )

    slave_cells: list[dict[str, Any]] = []
    for row_index, col_index, info in cell_states:
        if not info["is_merge_slave"]:
            continue
        slave: dict[str, Any] = {"row": row_index, "col": col_index}
        anchor = covered_by.get((row_index, col_index))
        if anchor is not None:
            slave["anchor"] = anchor
        slave_cells.append(slave)

    return {
        "has_merges": bool(anchors or slave_cells),
        "anchors": anchors,
        "slave_cells": slave_cells,
    }
