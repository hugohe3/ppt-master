"""validate: read back the latest template-fill export and check core contract."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from .checker import _chart_lookup, _slot_lookup, _table_lookup
from .ooxml import _load_json, _write_json
from .selectors import (
    _chart_selectors,
    _replacement_selectors,
    _replacement_text,
    _table_cell_text,
    _table_selectors,
)


_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_SLIDE_HEADING_RE = re.compile(r"^## Slide\s+(\d+)\s*$", re.MULTILINE)
_SPEAKER_NOTES_RE = re.compile(r"^### Speaker Notes\s*$", re.MULTILINE)
_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\([^)]+\)")
_LIST_PREFIX_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
_TABLE_BREAK_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
_ESCAPED_READBACK_CONTROL_RE = re.compile(
    r"^\\(## Slide\s+\d+|### Speaker Notes)$"
)


def _latest_export(project_path: Path) -> Path:
    exports_dir = project_path / "exports"
    candidates = [path for path in exports_dir.glob("*.pptx") if path.is_file()]
    if not candidates:
        raise RuntimeError(f"No PPTX exports found in: {exports_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _readback_slide_count(markdown: str) -> int:
    return len(_SLIDE_HEADING_RE.findall(markdown))


def _slide_sections(markdown: str) -> dict[int, str]:
    matches = list(_SLIDE_HEADING_RE.finditer(markdown))
    sections: dict[int, str] = {}
    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(markdown)
        )
        sections[int(match.group(1))] = markdown[match.end():end].strip()
    return sections


def _split_notes(section: str) -> tuple[str, str]:
    match = _SPEAKER_NOTES_RE.search(section)
    if match is None:
        return section, ""
    return section[:match.start()].strip(), section[match.end():].strip()


def _normalize_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _unescape_readback_control_line(value: str) -> str:
    """Restore the display text of an escaped read-back section marker."""
    match = _ESCAPED_READBACK_CONTROL_RE.fullmatch(value)
    return match.group(1) if match else value


def _paragraph_lines(value: object) -> list[str]:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return [
        normalized
        for line in text.split("\n")
        if (normalized := _normalize_line(line))
    ]


def _markdown_line_variants(markdown: str) -> list[set[str] | None]:
    variants: list[set[str] | None] = []
    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if (
            not stripped
            or stripped.startswith("|")
            or stripped.startswith("![")
            or stripped.startswith("> [Chart")
            or stripped == "_No extractable text content._"
        ):
            variants.append(None)
            continue
        display = _MARKDOWN_LINK_RE.sub(r"\1", stripped)
        without_prefix = _LIST_PREFIX_RE.sub("", display, count=1)
        line_variants = {
            _unescape_readback_control_line(_normalize_line(candidate))
            for candidate in (stripped, display, without_prefix)
        }
        line_variants.discard("")
        variants.append(line_variants)
    return variants


def _contains_paragraphs(markdown: str, value: str) -> bool:
    expected = _paragraph_lines(value)
    if not expected:
        return True
    actual = _markdown_line_variants(markdown)
    if len(expected) > len(actual):
        return False
    for start in range(len(actual) - len(expected) + 1):
        if all(
            actual[start + offset] is not None
            and expected[offset] in actual[start + offset]
            for offset in range(len(expected))
        ):
            return True
    return False


def _table_cells(markdown: str) -> list[list[str]]:
    cells: list[list[str]] = []
    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        values = re.split(r"(?<!\\)\|", stripped[1:-1])
        normalized_values = [
            value.strip().replace(r"\|", "|")
            for value in values
        ]
        if normalized_values and all(
            _TABLE_SEPARATOR_RE.fullmatch(value) is not None
            for value in normalized_values
        ):
            continue
        for value in normalized_values:
            cells.append(_paragraph_lines(_TABLE_BREAK_RE.sub("\n", value)))
    return cells


def _contains_table_cell(markdown: str, value: str) -> bool:
    expected = _paragraph_lines(value)
    if not expected:
        return True
    return expected in _table_cells(markdown)


def _contains_chart_text(markdown: str, value: str) -> bool:
    return (
        _contains_paragraphs(markdown, value)
        or _contains_table_cell(markdown, value)
    )


def _first_library(project_path: Path) -> dict[str, Any] | None:
    libraries = sorted((project_path / "analysis").glob("*.slide_library.json"))
    if not libraries:
        return None
    return _load_json(libraries[0])


def _matched_library_target(
    lookup: dict[tuple[int, str], dict[str, Any]] | None,
    source_slide: int,
    selectors: list[str],
) -> dict[str, Any] | None:
    """Return the first library target matched by the runtime selector order."""
    if lookup is None:
        return None
    return next(
        (
            target
            for selector in selectors
            if (target := lookup.get((source_slide, selector))) is not None
        ),
        None,
    )


def _replacement_tokens(
    plan: dict[str, Any],
    library: dict[str, Any] | None,
) -> list[tuple[int, str, str, str]]:
    tokens: list[tuple[int, str, str, str]] = []
    slot_lookup = _slot_lookup(library) if library is not None else None
    for plan_slide, slide in enumerate(plan.get("slides", []), start=1):
        source_slide = int(slide.get("source_slide", 0))
        replacements = slide.get("replacements", [])
        if not isinstance(replacements, list):
            continue
        slide_tokens: list[tuple[str, bool]] = []
        for replacement in replacements:
            if not isinstance(replacement, dict):
                continue
            text = _replacement_text(replacement)
            if not _paragraph_lines(text):
                continue
            slot = _matched_library_target(
                slot_lookup,
                source_slide,
                _replacement_selectors(replacement),
            )
            if (
                library is not None
                and replacement.get("optional")
                and slot is None
            ):
                continue
            is_title = (
                slot is not None
                and str(slot.get("role") or "") == "title_candidate"
            )
            slide_tokens.append((text, is_title))
        if (
            library is None
            and slide_tokens
            and not any(is_title for _, is_title in slide_tokens)
        ):
            first_text, _ = slide_tokens[0]
            slide_tokens[0] = (first_text, True)
        for text, is_title in slide_tokens:
            tokens.append(
                (
                    plan_slide,
                    text,
                    (
                        "title_missing_in_readback"
                        if is_title
                        else "body_text_missing_in_readback"
                    ),
                    "title" if is_title else "replacement text",
                )
            )
    return tokens


def _table_tokens(
    plan: dict[str, Any],
    library: dict[str, Any] | None,
) -> list[tuple[int, str]]:
    tokens: list[tuple[int, str]] = []
    table_lookup = _table_lookup(library) if library is not None else None
    for plan_slide, slide in enumerate(plan.get("slides", []), start=1):
        source_slide = int(slide.get("source_slide", 0))
        for table_edit in slide.get("table_edits", []) or []:
            table = _matched_library_target(
                table_lookup,
                source_slide,
                _table_selectors(table_edit),
            )
            if (
                library is not None
                and table_edit.get("optional")
                and table is None
            ):
                continue
            for cell in table_edit.get("cells", []) or []:
                text = _table_cell_text(cell)
                if _paragraph_lines(text):
                    tokens.append((plan_slide, text))
    return tokens


def _format_chart_series_value(value: object) -> str:
    """Match ppt_to_md's display formatting for chart series values."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _chart_tokens(
    plan: dict[str, Any],
    library: dict[str, Any] | None,
) -> list[tuple[int, str]]:
    tokens: list[tuple[int, str]] = []
    chart_lookup = _chart_lookup(library) if library is not None else None
    for plan_slide, slide in enumerate(plan.get("slides", []), start=1):
        source_slide = int(slide.get("source_slide", 0))
        for chart_edit in slide.get("chart_edits", []) or []:
            chart = _matched_library_target(
                chart_lookup,
                source_slide,
                _chart_selectors(chart_edit),
            )
            if (
                library is not None
                and chart_edit.get("optional")
                and chart is None
            ):
                continue
            for category in chart_edit.get("categories", []) or []:
                if str(category).strip():
                    tokens.append((plan_slide, str(category)))
            for series in chart_edit.get("series", []) or []:
                name = str(series.get("name") or "").strip()
                if name:
                    tokens.append((plan_slide, name))
                for value in series.get("values", []) or []:
                    text = _format_chart_series_value(value)
                    if text:
                        tokens.append((plan_slide, text))
    return tokens


def _append_page_token_checks(
    *,
    results: list[dict[str, Any]],
    summary: dict[str, int],
    sections: dict[int, str],
    tokens: list[tuple[int, str, str, str]],
    status: str,
    matcher: Callable[[str, str], bool],
) -> None:
    summary_key = status.lower()
    for plan_slide, text, code, label in tokens:
        body, _ = _split_notes(sections.get(plan_slide, ""))
        if matcher(body, text):
            summary["ok"] += 1
            continue
        summary[summary_key] += 1
        results.append(
            {
                "status": status,
                "code": code,
                "plan_slide": plan_slide,
                "message": f"{label} not found on the corresponding read-back slide",
                "text": text,
            }
        )


def validate_project(project_path: Path) -> dict[str, Any]:
    """Run read-back validation for a template-fill project."""
    project_path = project_path.expanduser().resolve()
    plan_path = project_path / "analysis" / "fill_plan.json"
    if not plan_path.is_file():
        raise RuntimeError(f"Missing fill plan: {plan_path}")

    plan = _load_json(plan_path)
    output_path = _latest_export(project_path)
    validation_dir = project_path / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    readback_path = validation_dir / "readback.md"

    ppt_to_md = _SCRIPTS_DIR / "source_to_md" / "ppt_to_md.py"
    try:
        subprocess.run(
            [sys.executable, str(ppt_to_md), str(output_path), "-o", str(readback_path)],
            cwd=_SCRIPTS_DIR.parents[2],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing executable: {sys.executable}") from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(details or "ppt_to_md read-back failed") from exc

    markdown = readback_path.read_text(encoding="utf-8", errors="replace")
    results: list[dict[str, Any]] = []
    summary = {"ok": 0, "warn": 0, "error": 0}
    sections = _slide_sections(markdown)

    expected_slides = len(plan.get("slides", []) or [])
    actual_slides = _readback_slide_count(markdown)
    if expected_slides == actual_slides:
        summary["ok"] += 1
    else:
        summary["error"] += 1
        results.append(
            {
                "status": "ERROR",
                "code": "slide_count_mismatch",
                "expected": expected_slides,
                "actual": actual_slides,
                "message": "read-back slide count does not match fill_plan.slides",
            }
        )

    for plan_slide in range(1, expected_slides + 1):
        if plan_slide in sections:
            continue
        summary["error"] += 1
        results.append(
            {
                "status": "ERROR",
                "code": "slide_missing_in_readback",
                "plan_slide": plan_slide,
                "message": "planned slide section is missing from read-back Markdown",
            }
        )

    library = _first_library(project_path)
    _append_page_token_checks(
        results=results,
        summary=summary,
        sections=sections,
        tokens=_replacement_tokens(plan, library),
        status="ERROR",
        matcher=_contains_paragraphs,
    )
    _append_page_token_checks(
        results=results,
        summary=summary,
        sections=sections,
        tokens=[
            (plan_slide, text, "table_text_missing_in_readback", "table cell text")
            for plan_slide, text in _table_tokens(plan, library)
        ],
        status="ERROR",
        matcher=_contains_table_cell,
    )
    _append_page_token_checks(
        results=results,
        summary=summary,
        sections=sections,
        tokens=[
            (plan_slide, text, "chart_text_missing_in_readback", "chart text")
            for plan_slide, text in _chart_tokens(plan, library)
        ],
        status="WARN",
        matcher=_contains_chart_text,
    )

    for plan_slide, slide in enumerate(plan.get("slides", []) or [], start=1):
        _, notes = _split_notes(sections.get(plan_slide, ""))
        planned_notes = str(slide.get("notes") or slide.get("speaker_notes") or "")
        if _paragraph_lines(planned_notes):
            if _contains_paragraphs(notes, planned_notes):
                summary["ok"] += 1
                continue
            summary["error"] += 1
            results.append(
                {
                    "status": "ERROR",
                    "code": "notes_missing_in_readback",
                    "plan_slide": plan_slide,
                    "message": (
                        "planned speaker notes not found on the corresponding "
                        "read-back slide"
                    ),
                    "text": planned_notes,
                }
            )
        elif notes.strip():
            summary["warn"] += 1
            results.append(
                {
                    "status": "WARN",
                    "code": "unexpected_notes_in_readback",
                    "plan_slide": plan_slide,
                    "message": (
                        "read-back slide contains speaker notes although the "
                        "plan slide has no notes field"
                    ),
                }
            )

    report = {
        "schema": "template_fill_pptx_validate.v1",
        "project": str(project_path),
        "export": str(output_path),
        "readback": str(readback_path),
        "summary": summary,
        "results": results,
    }
    _write_json(validation_dir / "validate_report.json", report)
    return report


def print_validate_report(report: dict[str, Any]) -> None:
    """Print a compact validation report."""
    summary = report["summary"]
    print(f"validate: ok={summary['ok']} warn={summary['warn']} error={summary['error']}")
    print(f"export: {report['export']}")
    print(f"readback: {report['readback']}")
    for item in report["results"]:
        text = item.get("text")
        suffix = f" text={text!r}" if text else ""
        print(f"{item['status']} {item['code']}: {item['message']}{suffix}")
