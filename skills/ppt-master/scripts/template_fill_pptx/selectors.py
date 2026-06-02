"""Plan selector builders and text extraction shared by check-plan and apply.

A replacement / table / chart edit can target a slot by ``slot_id`` (or
``table_id`` / ``chart_id``), ``shape_id``, or ``shape_name``; these helpers turn
a plan entry into an ordered list of lookup keys and pull the new text out.
"""

from __future__ import annotations

from typing import Any


def _plain_len(value: str) -> int:
    return len("".join(value.split()))


def _replacement_selectors(replacement: dict[str, Any]) -> list[str]:
    selectors = []
    if replacement.get("slot_id"):
        selectors.append(f"slot_id:{replacement['slot_id']}")
    if replacement.get("shape_id"):
        selectors.append(f"shape_id:{replacement['shape_id']}")
    if replacement.get("shape_name"):
        selectors.append(f"shape_name:{replacement['shape_name']}")
    return selectors


def _table_selectors(table_edit: dict[str, Any]) -> list[str]:
    selectors = []
    if table_edit.get("table_id"):
        selectors.append(f"table_id:{table_edit['table_id']}")
    if table_edit.get("shape_id"):
        selectors.append(f"shape_id:{table_edit['shape_id']}")
    if table_edit.get("shape_name"):
        selectors.append(f"shape_name:{table_edit['shape_name']}")
    return selectors


def _chart_selectors(chart_edit: dict[str, Any]) -> list[str]:
    selectors = []
    if chart_edit.get("chart_id"):
        selectors.append(f"chart_id:{chart_edit['chart_id']}")
    if chart_edit.get("shape_id"):
        selectors.append(f"shape_id:{chart_edit['shape_id']}")
    if chart_edit.get("shape_name"):
        selectors.append(f"shape_name:{chart_edit['shape_name']}")
    return selectors


def _replacement_text(replacement: dict[str, Any]) -> str:
    if "paragraphs" in replacement:
        paragraphs = replacement["paragraphs"]
        if not isinstance(paragraphs, list):
            raise RuntimeError("Replacement field 'paragraphs' must be a list")
        return "\n".join(str(item) for item in paragraphs)
    return str(replacement.get("text", ""))


def _table_cell_text(cell_edit: dict[str, Any]) -> str:
    if "paragraphs" in cell_edit:
        paragraphs = cell_edit["paragraphs"]
        if not isinstance(paragraphs, list):
            raise RuntimeError("Table cell field 'paragraphs' must be a list")
        return "\n".join(str(item) for item in paragraphs)
    return str(cell_edit.get("text", ""))
