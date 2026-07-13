"""Analyze a PPTX as reusable text, table, chart, and SmartArt source facts."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .chart_read import empty_chart_data, read_chart_data
from .diagram_read import read_smartart_diagrams
from .edit_safety import (
    _chart_edit_capability,
    _chart_frames,
    _chart_reference,
    _table_cell_merge_info,
    _table_merge_topology,
    _unsupported_chart_capability,
)
from .ooxml import (
    CHART_REL_TYPE,
    NS,
    SlideRef,
    _container_geometry,
    _emu_to_px,
    _normalize_part,
    _paragraph_texts,
    _parse_slide_refs,
    _read_xml,
    _shape_identity,
    _slide_relationships,
    _table_containers,
    _text_containers,
)

THANKS_KEYWORDS = ("thank", "thanks", "q&a", "qa", "contact", "致谢", "谢谢", "感谢", "答疑", "联系方式")
TOC_KEYWORDS = ("agenda", "contents", "content", "outline", "目录", "议程")
CHAPTER_KEYWORDS = ("chapter", "part", "section", "章节", "部分")


def _analyze_tables(slide_root: ET.Element, source_slide: int) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for order, container in enumerate(_table_containers(slide_root), start=1):
        shape_id, _shape_name = _shape_identity(container, order)
        table = container.find(".//a:tbl", NS)
        if table is None:
            continue
        merge_topology = _table_merge_topology(table)
        merge_anchors = {
            (int(item["row"]), int(item["col"])): item.get("anchor")
            for item in merge_topology["slave_cells"]
        }
        rows: list[dict[str, Any]] = []
        max_columns = 0
        for row_index, row in enumerate(table.findall("a:tr", NS)):
            cells: list[dict[str, Any]] = []
            for col_index, cell in enumerate(row.findall("a:tc", NS)):
                merge_info = _table_cell_merge_info(cell)
                merge_anchor = merge_anchors.get((row_index, col_index))
                if merge_anchor is not None:
                    merge_info["merge_anchor"] = merge_anchor
                    merge_info["anchor_row"] = merge_anchor["row"]
                    merge_info["anchor_col"] = merge_anchor["col"]
                elif merge_info["is_merge_slave"]:
                    merge_info["anchor_row"] = None
                    merge_info["anchor_col"] = None
                else:
                    merge_info["anchor_row"] = row_index
                    merge_info["anchor_col"] = col_index
                cells.append(
                    {
                        "row": row_index,
                        "col": col_index,
                        "text": "\n".join(_paragraph_texts(cell)),
                        **merge_info,
                    }
                )
            max_columns = max(max_columns, len(cells))
            rows.append({"row": row_index, "cells": cells})
        tables.append(
            {
                "table_id": f"s{source_slide:02d}_tbl{shape_id}",
                "row_count": len(rows),
                "column_count": max_columns,
                "rows": rows,
                "merge_topology": merge_topology,
            }
        )
    return tables


def _analyze_charts(zf: zipfile.ZipFile, slide_root: ET.Element, slide_ref: SlideRef) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    relationships = _slide_relationships(zf, slide_ref.rels_name)
    for order, container in enumerate(_chart_frames(slide_root), start=1):
        shape_id, _shape_name = _shape_identity(container, order)
        chart_kind, rel_id = _chart_reference(container)
        payload: dict[str, Any] = {"chart_id": f"s{slide_ref.index:02d}_ch{shape_id}"}
        payload.update(empty_chart_data())
        payload["chart_kind"] = chart_kind
        if chart_kind == "chartex":
            payload["chart_type"] = "chartEx"
            payload["plot_types"] = ["chartEx"]
            payload["edit_capability"] = _unsupported_chart_capability(
                "chart_edit_chartex_unsupported",
                "template-fill chart edits do not support ChartEx",
            )
            charts.append(payload)
            continue
        if chart_kind != "classic":
            payload["edit_capability"] = _unsupported_chart_capability(
                "chart_edit_plot_type_unsupported",
                "template-fill chart edits require a classic DrawingML chart reference",
            )
            charts.append(payload)
            continue

        rel = relationships.get(rel_id)
        if rel and rel.get("type") == CHART_REL_TYPE:
            chart_part = _normalize_part(rel["target"], slide_ref.part_name)
            try:
                chart_root = _read_xml(zf, chart_part)
                payload.update(read_chart_data(chart_root))
                payload["edit_capability"] = _chart_edit_capability(chart_root)
            except RuntimeError:
                payload.update(empty_chart_data())
                payload["edit_capability"] = _unsupported_chart_capability(
                    "chart_edit_part_unavailable",
                    "template-fill could not read the classic chart part",
                )
        else:
            payload["edit_capability"] = _unsupported_chart_capability(
                "chart_edit_relationship_unsupported",
                "template-fill chart edits require a classic chart relationship",
            )
        charts.append(payload)
    return charts


def _slot_role(slot: dict[str, Any], order: int) -> str:
    text = str(slot.get("text") or "")
    name = str(slot.get("shape_name") or "").lower()
    geometry = slot.get("geometry") or {}
    y = geometry.get("y")
    if order == 1 or "title" in name or "标题" in name:
        return "title_candidate"
    if isinstance(y, int) and y < 160 and len(text) <= 80:
        return "title_candidate"
    if slot.get("text_node_count", 0) >= 4 or len(text) >= 120:
        return "body_candidate"
    return "label_candidate"


def _font_size_px(container: ET.Element) -> float | None:
    sizes: list[float] = []
    for node in container.findall(".//a:rPr", NS) + container.findall(".//a:defRPr", NS):
        raw_size = node.attrib.get("sz")
        if not raw_size:
            continue
        try:
            sizes.append(int(raw_size) / 100 * 96 / 72)
        except ValueError:
            continue
    if not sizes:
        return None
    # Use the largest explicit run size as the conservative capacity baseline.
    return round(max(sizes), 2)


def _text_metrics(container: ET.Element, paragraph_count: int) -> dict[str, Any]:
    font_size_px = _font_size_px(container)
    return {
        "font_size_px": font_size_px,
        "paragraph_count": paragraph_count,
    }


def _classify_page_type(index: int, total: int, text: str, slots: list[dict[str, Any]]) -> str:
    normalized = text.lower()
    if index == 1:
        return "cover_candidate"
    if index == total or any(keyword in normalized for keyword in THANKS_KEYWORDS):
        return "ending_candidate"
    if any(keyword in normalized for keyword in TOC_KEYWORDS):
        return "toc_candidate"
    if any(keyword in normalized for keyword in CHAPTER_KEYWORDS):
        return "chapter_candidate"
    if len(slots) <= 2 and len(text) <= 80:
        return "chapter_candidate"
    return "content_candidate"


def _canvas_px(pres_root: ET.Element) -> dict[str, int | None]:
    size = pres_root.find("p:sldSz", NS)
    if size is None:
        return {"width": None, "height": None}
    return {
        "width": _emu_to_px(size.attrib.get("cx")),
        "height": _emu_to_px(size.attrib.get("cy")),
    }


def _fill_risk(
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    diagrams: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return a fill_risk descriptor when the slide has non-text content that text-fill cannot replace.

    Tables and charts may be covered by explicit edits. SmartArt is inventory-only:
    template-fill preserves it unchanged, so its source text may show through.
    """
    kinds: list[str] = []
    if tables:
        kinds.append("table")
    if charts:
        kinds.append("chart")
    if diagrams:
        kinds.append("smartart")
    if not kinds:
        return None
    kind_str = "/".join(kinds)
    guidance: list[str] = []
    if tables or charts:
        guidance.append("cover tables/charts with explicit edits")
    if diagrams:
        guidance.append("review preserved SmartArt source text")
    guidance_text = "; ".join(guidance)
    return {
        "has_non_text_content": True,
        "kinds": kinds,
        "reason": f"has non-text content ({kind_str}) that text-fill does not replace automatically; {guidance_text}",
    }


def analyze_pptx(pptx_path: Path) -> dict[str, Any]:
    """Extract a slide library with text replacement slots."""
    with zipfile.ZipFile(pptx_path) as zf:
        pres_root = _read_xml(zf, "ppt/presentation.xml")
        slide_refs = _parse_slide_refs(zf)
        slides: list[dict[str, Any]] = []
        for slide_ref in slide_refs:
            slide_root = _read_xml(zf, slide_ref.part_name)
            slots: list[dict[str, Any]] = []
            for order, container in enumerate(_text_containers(slide_root), start=1):
                shape_id, shape_name = _shape_identity(container, order)
                paragraphs = _paragraph_texts(container)
                text = "\n".join(paragraphs)
                geometry = _container_geometry(container)
                role = _slot_role(
                    {
                        "text": text,
                        "shape_name": shape_name,
                        "geometry": geometry,
                        "text_node_count": len(container.findall(".//a:t", NS)),
                    },
                    order,
                )
                slots.append(
                    {
                        "slot_id": f"s{slide_ref.index:02d}_sh{shape_id}",
                        "role": role,
                        "text": text,
                        "paragraph_count": len(paragraphs),
                        "geometry": geometry,
                        "text_metrics": _text_metrics(container, len(paragraphs)),
                    }
                )

            tables = _analyze_tables(slide_root, slide_ref.index)
            charts = _analyze_charts(zf, slide_root, slide_ref)
            diagrams = read_smartart_diagrams(zf, slide_ref.part_name, slide_ref.index)
            slide_text = "\n".join(
                [slot["text"] for slot in slots if slot["text"]]
                + [
                    str(text)
                    for diagram in diagrams
                    for text in diagram.get("text_items", [])
                    if text
                ]
            )
            slide: dict[str, Any] = {
                "slide_index": slide_ref.index,
                "page_type": _classify_page_type(slide_ref.index, len(slide_refs), slide_text, slots),
                "text_summary": slide_text[:500],
                "slots": slots,
                "tables": tables,
                "charts": charts,
                "diagrams": diagrams,
            }
            risk = _fill_risk(tables, charts, diagrams)
            if risk is not None:
                slide["fill_risk"] = risk
            slides.append(slide)

    return {
        "schema": "template_fill_pptx_library.v1",
        "source_pptx": str(pptx_path),
        "slide_count": len(slides),
        "canvas_px": _canvas_px(pres_root),
        "slides": slides,
        "plan_contract": {
            "schema": "template_fill_pptx_plan.v1",
            "slides": [
                {
                    "source_slide": 1,
                    "purpose": "封面 / 章节 / 内容 / 结尾",
                    "replacements": [
                        {
                            "slot_id": "s01_sh2",
                            "text": "替换后的文字",
                        }
                    ],
                    "table_edits": [
                        {
                            "table_id": "s01_tbl3",
                            "cells": [{"row": 0, "col": 0, "text": "替换后的单元格"}],
                        }
                    ],
                    "chart_edits": [
                        {
                            "chart_id": "s01_ch4",
                            "categories": ["A", "B"],
                            "series": [{"name": "系列1", "values": [1, 2]}],
                        }
                    ],
                }
            ],
        },
    }
