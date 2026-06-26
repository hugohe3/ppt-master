"""check-plan: compare planned text / table / chart edits against source capacity."""

from __future__ import annotations

import unicodedata
from typing import Any

from .selectors import (
    _chart_selectors,
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


def _visual_width(text: str) -> float:
    """Estimate rendered text width in Latin-character units.

    ``len(text)`` is too crude for mixed CJK / Latin decks: Chinese characters
    generally consume about twice the horizontal space of ASCII letters, while
    punctuation and digits are narrower. The checker only needs a conservative
    fit signal, so use Unicode East Asian Width instead of a font-specific
    renderer.
    """
    width = 0.0
    for char in "".join(text.split()):
        east_asian_width = unicodedata.east_asian_width(char)
        if east_asian_width in {"F", "W"}:
            width += 2.0
        elif east_asian_width == "A":
            width += 1.5
        else:
            width += 1.0
    return width


def _display_width(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 1)


def _fallback_font_size_px(role: str, geometry: dict[str, Any], old_paragraphs: int) -> float:
    height = geometry.get("height")
    if isinstance(height, int) and old_paragraphs > 0:
        inferred = height / max(old_paragraphs, 1) / 1.25
        if 8 <= inferred <= 56:
            return inferred
    if role == "title_candidate":
        return 28.0
    if role == "body_candidate":
        return 16.0
    return 14.0


def _geometry_capacity_width(
    *,
    role: str,
    old_paragraphs: int,
    new_paragraphs: int,
    geometry: dict[str, Any],
    text_metrics: dict[str, Any],
) -> float | None:
    width = geometry.get("width")
    height = geometry.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        return None

    font_size_px = text_metrics.get("font_size_px")
    if not isinstance(font_size_px, (int, float)) or font_size_px <= 0:
        font_size_px = _fallback_font_size_px(role, geometry, old_paragraphs)

    line_height = max(font_size_px * 1.25, 1.0)
    max_lines = max(int(height / line_height), old_paragraphs, new_paragraphs, 1)
    horizontal_padding = 24 if width >= 180 else 12
    usable_width = max(width - horizontal_padding, width * 0.72, 1)
    latin_units_per_line = usable_width / max(font_size_px * 0.52, 1)
    capacity = latin_units_per_line * max_lines

    if role == "label_candidate":
        return capacity * 0.7
    if role == "title_candidate":
        return capacity * 0.85
    return capacity


def _fit_status(
    *,
    role: str,
    old_width: float,
    new_width: float,
    old_paragraphs: int,
    new_paragraphs: int,
    geometry: dict[str, Any],
    text_metrics: dict[str, Any],
) -> tuple[str, str]:
    old_width = max(old_width, 1.0)
    ratio = new_width / old_width
    width = geometry.get("width")
    height = geometry.get("height")
    capacity_width = _geometry_capacity_width(
        role=role,
        old_paragraphs=old_paragraphs,
        new_paragraphs=new_paragraphs,
        geometry=geometry,
        text_metrics=text_metrics,
    )

    if role == "label_candidate" or (old_width <= 8 and old_paragraphs <= 1):
        if capacity_width is not None and new_width <= capacity_width and not (old_width <= 8):
            return "OK", "short label fits estimated text-box capacity"
        label_limit = old_width
        if isinstance(width, int) and width >= 220:
            label_limit = max(label_limit, old_width * 1.25)
        if new_width > label_limit:
            return "WARN", "short label exceeds original visual width; rewrite shorter"
        return "OK", "short label fits original visual width"

    if role == "title_candidate" and old_paragraphs <= 1:
        if capacity_width is not None and new_width <= capacity_width:
            return "OK", "title fits estimated text-box capacity"
        limit = 1.15 if old_width <= 12 else 1.35
        if ratio > limit:
            return "WARN", "title is too long for the original slot; rewrite first"
        return "OK", "title stays near original capacity"

    paragraph_limit = max(old_paragraphs + 2, old_paragraphs * 2, 2)
    if new_paragraphs > paragraph_limit:
        return "WARN", "body paragraph count changed too much; compress or split pages"

    if isinstance(width, int) and isinstance(height, int) and width * height < 30000 and ratio > 2.0:
        return "WARN", "small text box with much longer text; rewrite shorter"

    if capacity_width is not None and new_width > capacity_width:
        return "WARN", "text exceeds estimated text-box capacity; rewrite or split"

    # Body text reflows, so a moderate amount of extra length is fine; only flag
    # gross overflow. Labels / titles keep their tighter guards above.
    body_limit = 3.0 if role == "body_candidate" else 2.2
    if ratio > body_limit:
        return "WARN", "text is much longer than source slot; rewrite or choose another page"
    return "OK", "within estimated slot capacity"


def _capacity_for_report(
    *,
    role: str,
    old_width: float,
    old_paragraphs: int,
    new_paragraphs: int,
    geometry: dict[str, Any],
    text_metrics: dict[str, Any],
) -> float | None:
    capacity = _geometry_capacity_width(
        role=role,
        old_paragraphs=old_paragraphs,
        new_paragraphs=new_paragraphs,
        geometry=geometry,
        text_metrics=text_metrics,
    )
    if capacity is None:
        return None
    return _display_width(max(capacity, old_width))


def _library_slide_index(library: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Build a mapping from slide_index to slide dict for O(1) lookup."""
    return {int(s.get("slide_index", 0)): s for s in library.get("slides", [])}


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
                    "code": "replacements_not_list",
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
                        "code": "replacement_target_not_found",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "replacement target not found in slide library",
                    }
                )
                summary["error"] += 1
                continue

            old_text = str(slot.get("text") or "")
            old_width = _visual_width(old_text)
            new_width = _visual_width(text)
            old_paragraphs = int(slot.get("paragraph_count") or 1)
            new_paragraphs = max(len([line for line in text.splitlines() if line.strip()]), 1)
            status, message = _fit_status(
                role=str(slot.get("role") or ""),
                old_width=old_width,
                new_width=new_width,
                old_paragraphs=old_paragraphs,
                new_paragraphs=new_paragraphs,
                geometry=slot.get("geometry") or {},
                text_metrics=slot.get("text_metrics") or {},
            )
            capacity_width = _capacity_for_report(
                role=str(slot.get("role") or ""),
                old_width=old_width,
                old_paragraphs=old_paragraphs,
                new_paragraphs=new_paragraphs,
                geometry=slot.get("geometry") or {},
                text_metrics=slot.get("text_metrics") or {},
            )
            summary["warn" if status == "WARN" else "ok"] += 1
            results.append(
                {
                    "status": status,
                    "code": "text_capacity" if status == "WARN" else "text_fit",
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "slot_id": slot.get("slot_id"),
                    "role": slot.get("role"),
                    "old_len": _display_width(old_width),
                    "new_len": _display_width(new_width),
                    "old_visual_width": _display_width(old_width),
                    "new_visual_width": _display_width(new_width),
                    "capacity_visual_width": capacity_width,
                    "ratio": round(new_width / max(old_width, 1.0), 2),
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
                    "code": "table_edits_not_list",
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
                        "code": "table_target_not_found",
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
                        "code": "table_cells_not_list",
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
                            "code": "table_cell_out_of_bounds",
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
                        "code": "table_target_exists",
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
                    "code": "chart_edits_not_list",
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
                        "code": "chart_target_not_found",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "message": "chart target not found in slide library",
                    }
                )
                summary["error"] += 1
                continue
            if len(chart.get("plot_types") or []) > 1:
                results.append(
                    {
                        "status": "ERROR",
                        "code": "chart_combo_unsupported",
                        "plan_slide": slide_index,
                        "source_slide": source_slide,
                        "selector": selectors[0] if selectors else "",
                        "chart_id": chart.get("chart_id"),
                        "message": (
                            "template-fill chart edits do not support multi-plot / combination charts; "
                            "use beautify/main pipeline to redraw the chart, or leave the native chart untouched"
                        ),
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
                        "code": "chart_data_invalid",
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
                        "code": "chart_series_length_mismatch",
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
                    "code": "chart_target_valid",
                    "plan_slide": slide_index,
                    "source_slide": source_slide,
                    "chart_id": chart.get("chart_id"),
                    "category_count": len(categories),
                    "series_count": len(series),
                    "message": "chart edit target and data shape are valid",
                }
            )
    # --- Guardrail 2: source slides with non-text content not covered by edits ---
    # For each plan slide, if the source slide has tables/charts in the library
    # but the plan slide provides no matching table_edits/chart_edits, warn that
    # text-fill will silently leave the original template content in place.
    lib_slides = _library_slide_index(library)
    for plan_slide_index, slide in enumerate(plan.get("slides", []), start=1):
        source_slide = int(slide.get("source_slide", 0))
        lib_slide = lib_slides.get(source_slide)
        if lib_slide is None:
            continue
        lib_tables = lib_slide.get("tables", [])
        lib_charts = lib_slide.get("charts", [])
        if not lib_tables and not lib_charts:
            continue
        # Check whether the plan slide provides edits covering the non-text content.
        has_table_edits = bool(slide.get("table_edits"))
        has_chart_edits = bool(slide.get("chart_edits"))
        uncovered_kinds: list[str] = []
        if lib_tables and not has_table_edits:
            uncovered_kinds.append("table")
        if lib_charts and not has_chart_edits:
            uncovered_kinds.append("chart")
        if not uncovered_kinds:
            continue
        kind_str = "/".join(uncovered_kinds)
        summary["warn"] += 1
        results.append(
            {
                "status": "WARN",
                "code": "non_text_content_unedited",
                "plan_slide": plan_slide_index,
                "source_slide": source_slide,
                "message": (
                    f"source slide {source_slide} has non-text content ({kind_str}) "
                    "with no matching edits in the plan; text-fill leaves it untouched "
                    "and original template content may show through "
                    "(add table_edits/chart_edits, or pick another source slide)"
                ),
            }
        )

    # --- Guardrail 1: same source slide reused too many times while unused layouts exist ---
    # Use a relative condition rather than an absolute threshold: only warn when
    # (a) a source slide is reused >= REUSE_WARN_THRESHOLD times, AND
    # (b) there are library slides that the plan never uses at all.
    # Rationale: a small template where every layout is referenced is fine even at
    # high per-slide reuse; "15-page template where only 1 page is ever cloned and
    # the rest sit idle" is the real smell we want to surface.
    # Threshold of 3: any source appearing 3+ times in a plan is meaningful reuse
    # (cover / TOC / ending typically appear at most twice), so >= 3 is a practical
    # signal without being overly sensitive.
    REUSE_WARN_THRESHOLD = 3
    source_use_counts: dict[int, int] = {}
    for slide in plan.get("slides", []):
        src = int(slide.get("source_slide", 0))
        if src:
            source_use_counts[src] = source_use_counts.get(src, 0) + 1
    all_lib_indices = {int(s.get("slide_index", 0)) for s in library.get("slides", []) if s.get("slide_index")}
    used_lib_indices = set(source_use_counts.keys())
    unused_lib_indices = sorted(all_lib_indices - used_lib_indices)
    if unused_lib_indices:
        for src, count in sorted(source_use_counts.items()):
            if count >= REUSE_WARN_THRESHOLD:
                unused_list = ", ".join(str(i) for i in unused_lib_indices)
                summary["warn"] += 1
                results.append(
                    {
                        "status": "WARN",
                        "code": "source_reuse_concentration",
                        "source_slide": src,
                        "reuse_count": count,
                        "unused_source_slides": unused_lib_indices,
                        "message": (
                            f"source slide {src} is reused {count} times while "
                            f"{len(unused_lib_indices)} source layout(s) are never used "
                            f"(indices: {unused_list}); "
                            "consider using other layouts for more variety"
                        ),
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
        elif "plan_slide" in item:
            target = item.get("slot_id") or item.get("selector") or ""
            line = (
                f"{item['status']} P{item['plan_slide']:02d} "
                f"source={item['source_slide']} {target}: {item['message']}".strip()
            )
        else:
            # Guardrail 1 WARNs are source-level (no plan_slide); print source + message.
            line = f"{item['status']} source={item.get('source_slide', '?')}: {item['message']}"
        print(line)
