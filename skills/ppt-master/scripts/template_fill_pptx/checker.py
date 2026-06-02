"""check-plan: compare planned text / table / chart edits against source capacity."""

from __future__ import annotations

from typing import Any

from .selectors import (
    _chart_selectors,
    _plain_len,
    _replacement_selectors,
    _replacement_text,
    _table_selectors,
)


def _slot_lookup(library: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    lookup: dict[tuple[int, str], dict[str, Any]] = {}
    for slide in library.get("slides", []):
        slide_index = int(slide.get("slide_index", 0))
        for slot in slide.get("slots", []):
            if slot.get("slot_id"):
                lookup[(slide_index, f"slot_id:{slot['slot_id']}")] = slot
            if slot.get("shape_id"):
                lookup[(slide_index, f"shape_id:{slot['shape_id']}")] = slot
            if slot.get("shape_name"):
                lookup[(slide_index, f"shape_name:{slot['shape_name']}")] = slot
    return lookup


def _table_lookup(library: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    lookup: dict[tuple[int, str], dict[str, Any]] = {}
    for slide in library.get("slides", []):
        slide_index = int(slide.get("slide_index", 0))
        for table in slide.get("tables", []):
            if table.get("table_id"):
                lookup[(slide_index, f"table_id:{table['table_id']}")] = table
            if table.get("shape_id"):
                lookup[(slide_index, f"shape_id:{table['shape_id']}")] = table
            if table.get("shape_name"):
                lookup[(slide_index, f"shape_name:{table['shape_name']}")] = table
    return lookup


def _chart_lookup(library: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    lookup: dict[tuple[int, str], dict[str, Any]] = {}
    for slide in library.get("slides", []):
        slide_index = int(slide.get("slide_index", 0))
        for chart in slide.get("charts", []):
            if chart.get("chart_id"):
                lookup[(slide_index, f"chart_id:{chart['chart_id']}")] = chart
            if chart.get("shape_id"):
                lookup[(slide_index, f"shape_id:{chart['shape_id']}")] = chart
            if chart.get("shape_name"):
                lookup[(slide_index, f"shape_name:{chart['shape_name']}")] = chart
    return lookup


def _fit_status(
    *,
    role: str,
    old_len: int,
    new_len: int,
    old_paragraphs: int,
    new_paragraphs: int,
    geometry: dict[str, Any],
) -> tuple[str, str]:
    old_len = max(old_len, 1)
    ratio = new_len / old_len
    width = geometry.get("width")
    height = geometry.get("height")

    if role == "label_candidate" or (old_len <= 6 and old_paragraphs <= 1):
        if new_len > old_len:
            return "WARN", "short label exceeds original length; rewrite shorter"
        return "OK", "short label fits original length"

    if role == "title_candidate" and old_paragraphs <= 1:
        limit = 1.15 if old_len <= 8 else 1.35
        if ratio > limit:
            return "WARN", "title is too long for the original slot; rewrite first"
        return "OK", "title stays near original capacity"

    paragraph_limit = max(old_paragraphs + 2, old_paragraphs * 2, 2)
    if new_paragraphs > paragraph_limit:
        return "WARN", "body paragraph count changed too much; compress or split pages"

    if isinstance(width, int) and isinstance(height, int) and width * height < 30000 and ratio > 2.0:
        return "WARN", "small text box with much longer text; rewrite shorter"

    # Body text reflows, so a moderate amount of extra length is fine; only flag
    # gross overflow. Labels / titles keep their tighter guards above.
    body_limit = 3.0 if role == "body_candidate" else 2.2
    if ratio > body_limit:
        return "WARN", "text is much longer than source slot; rewrite or choose another page"
    return "OK", "within estimated slot capacity"


def check_plan(library: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Compare fill replacements against source slot capacity."""
    lookup = _slot_lookup(library)
    table_lookup = _table_lookup(library)
    chart_lookup = _chart_lookup(library)
    results: list[dict[str, Any]] = []
    summary = {"ok": 0, "warn": 0, "error": 0}

    for slide_index, slide in enumerate(plan.get("slides", []), start=1):
        source_slide = int(slide.get("source_slide", 0))
        replacements = slide.get("replacements", [])
        if not isinstance(replacements, list):
            results.append(
                {
                    "status": "ERROR",
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "message": "replacements must be a list",
                }
            )
            summary["error"] += 1
            continue

        for replacement in replacements:
            selectors = _replacement_selectors(replacement)
            slot = next((lookup.get((source_slide, selector)) for selector in selectors), None)
            text = _replacement_text(replacement)
            if slot is None:
                results.append(
                    {
                        "status": "ERROR",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "replacement target not found in slide library",
                    }
                )
                summary["error"] += 1
                continue

            old_text = str(slot.get("text") or "")
            old_len = _plain_len(old_text)
            new_len = _plain_len(text)
            old_paragraphs = int(slot.get("paragraph_count") or 1)
            new_paragraphs = max(len([line for line in text.splitlines() if line.strip()]), 1)
            status, message = _fit_status(
                role=str(slot.get("role") or ""),
                old_len=old_len,
                new_len=new_len,
                old_paragraphs=old_paragraphs,
                new_paragraphs=new_paragraphs,
                geometry=slot.get("geometry") or {},
            )
            summary["warn" if status == "WARN" else "ok"] += 1
            results.append(
                {
                    "status": status,
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "slot_id": slot.get("slot_id"),
                    "role": slot.get("role"),
                    "old_len": old_len,
                    "new_len": new_len,
                    "ratio": round(new_len / max(old_len, 1), 2),
                    "old_paragraphs": old_paragraphs,
                    "new_paragraphs": new_paragraphs,
                    "message": message,
                    "old_text": old_text,
                    "new_text": text,
                }
            )
        table_edits = slide.get("table_edits", [])
        if not isinstance(table_edits, list):
            results.append(
                {
                    "status": "ERROR",
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "message": "table_edits must be a list",
                }
            )
            summary["error"] += 1
            continue
        for table_edit in table_edits:
            selectors = _table_selectors(table_edit)
            table = next((table_lookup.get((source_slide, selector)) for selector in selectors), None)
            if table is None:
                results.append(
                    {
                        "status": "ERROR",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "table target not found in slide library",
                    }
                )
                summary["error"] += 1
                continue
            cells = table_edit.get("cells", [])
            if not isinstance(cells, list):
                results.append(
                    {
                        "status": "ERROR",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "table edit cells must be a list",
                    }
                )
                summary["error"] += 1
                continue
            row_count = int(table.get("row_count") or 0)
            column_count = int(table.get("column_count") or 0)
            for cell in cells:
                row = int(cell.get("row", -1))
                col = int(cell.get("col", -1))
                if row < 0 or col < 0 or row >= row_count or col >= column_count:
                    results.append(
                        {
                            "status": "ERROR",
                            "plan_slide": slide_index,
                            "source_slide": source_slide,
                            "selector": selectors[0] if selectors else "",
                            "message": f"table cell out of bounds: row={row} col={col}",
                        }
                    )
                    summary["error"] += 1
                    continue
                summary["ok"] += 1
                results.append(
                    {
                        "status": "OK",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "table_id": table.get("table_id"),
                        "row": row,
                        "col": col,
                        "message": "table cell target exists",
                    }
                )
        chart_edits = slide.get("chart_edits", [])
        if not isinstance(chart_edits, list):
            results.append(
                {
                    "status": "ERROR",
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "message": "chart_edits must be a list",
                }
            )
            summary["error"] += 1
            continue
        for chart_edit in chart_edits:
            selectors = _chart_selectors(chart_edit)
            chart = next((chart_lookup.get((source_slide, selector)) for selector in selectors), None)
            if chart is None:
                results.append(
                    {
                        "status": "ERROR",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "chart target not found in slide library",
                    }
                )
                summary["error"] += 1
                continue
            categories = chart_edit.get("categories", [])
            series = chart_edit.get("series", [])
            if not isinstance(categories, list) or not isinstance(series, list) or not series:
                results.append(
                    {
                        "status": "ERROR",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "chart edit requires categories list and non-empty series list",
                    }
                )
                summary["error"] += 1
                continue
            bad_series = [
                item
                for item in series
                if not isinstance(item, dict)
                or not isinstance(item.get("values", []), list)
                or len(item.get("values", [])) != len(categories)
            ]
            if bad_series:
                results.append(
                    {
                        "status": "ERROR",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "each chart series needs values matching categories length",
                    }
                )
                summary["error"] += 1
                continue
            summary["ok"] += 1
            results.append(
                {
                    "status": "OK",
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "chart_id": chart.get("chart_id"),
                    "category_count": len(categories),
                    "series_count": len(series),
                    "message": "chart edit target and data shape are valid",
                }
            )
    return {"schema": "template_fill_pptx_check.v1", "summary": summary, "results": results}


def print_check_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"check-plan: ok={summary['ok']} warn={summary['warn']} error={summary['error']}")
    for item in report["results"]:
        if item["status"] == "OK":
            continue
        if "ratio" in item:
            line = (
                "{status} P{plan_slide:02d} source={source_slide} {slot_id} "
                "{role} old={old_len} new={new_len} ratio={ratio}: {message}".format(**item)
            )
        else:
            target = item.get("slot_id") or item.get("selector") or ""
            line = (
                f"{item['status']} P{item['plan_slide']:02d} "
                f"source={item['source_slide']} {target}: {item['message']}".strip()
            )
        print(line)
