"""analyze: read a PPTX as a reusable slide library of text / table / chart slots."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import (
    NS,
    _chart_containers,
    _container_geometry,
    _emu_to_px,
    _paragraph_texts,
    _parse_slide_refs,
    _read_xml,
    _shape_identity,
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
        rows: list[dict[str, Any]] = []
        max_columns = 0
        for row_index, row in enumerate(container.findall(".//a:tbl/a:tr", NS)):
            cells: list[dict[str, Any]] = []
            for col_index, cell in enumerate(row.findall("a:tc", NS)):
                cells.append(
                    {
                        "row": row_index,
                        "col": col_index,
                        "text": "\n".join(_paragraph_texts(cell)),
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
            }
        )
    return tables


def _analyze_charts(slide_root: ET.Element, source_slide: int) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    for order, container in enumerate(_chart_containers(slide_root), start=1):
        shape_id, _shape_name = _shape_identity(container, order)
        charts.append({"chart_id": f"s{source_slide:02d}_ch{shape_id}"})
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
                    }
                )

            tables = _analyze_tables(slide_root, slide_ref.index)
            charts = _analyze_charts(slide_root, slide_ref.index)
            slide_text = "\n".join(slot["text"] for slot in slots if slot["text"])
            slides.append(
                {
                    "slide_index": slide_ref.index,
                    "page_type": _classify_page_type(slide_ref.index, len(slide_refs), slide_text, slots),
                    "text_summary": slide_text[:500],
                    "slots": slots,
                    "tables": tables,
                    "charts": charts,
                }
            )

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
