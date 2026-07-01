"""validate: read back the latest template-fill export and check core contract."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .ooxml import _load_json, _write_json


_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_SLIDE_HEADING_RE = re.compile(r"^## Slide\s+\d+\s*$", re.MULTILINE)
_TOTAL_SLIDES_RE = re.compile(r"^- Total slides:\s*(\d+)\s*$", re.MULTILINE)


def _latest_export(project_path: Path) -> Path:
    exports_dir = project_path / "exports"
    candidates = [path for path in exports_dir.glob("*.pptx") if path.is_file()]
    if not candidates:
        raise RuntimeError(f"No PPTX exports found in: {exports_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _readback_slide_count(markdown: str) -> int:
    match = _TOTAL_SLIDES_RE.search(markdown)
    if match:
        return int(match.group(1))
    return len(_SLIDE_HEADING_RE.findall(markdown))


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip()


def _contains_text(markdown: str, value: object) -> bool:
    normalized = _normalize_text(value)
    if not normalized:
        return True
    return normalized in _normalize_text(markdown)


def _first_library(project_path: Path) -> dict[str, Any] | None:
    libraries = sorted((project_path / "analysis").glob("*.slide_library.json"))
    if not libraries:
        return None
    return _load_json(libraries[0])


def _slot_role_lookup(library: dict[str, Any] | None) -> dict[tuple[int, str], str]:
    if library is None:
        return {}
    lookup: dict[tuple[int, str], str] = {}
    for slide in library.get("slides", []):
        slide_index = int(slide.get("slide_index", 0))
        for slot in slide.get("slots", []):
            slot_id = slot.get("slot_id")
            if isinstance(slot_id, str):
                lookup[(slide_index, slot_id)] = str(slot.get("role") or "")
    return lookup


def _title_texts(plan: dict[str, Any], role_lookup: dict[tuple[int, str], str]) -> list[tuple[int, str]]:
    titles: list[tuple[int, str]] = []
    for plan_slide, slide in enumerate(plan.get("slides", []), start=1):
        source_slide = int(slide.get("source_slide", 0))
        replacements = slide.get("replacements", [])
        if not isinstance(replacements, list):
            continue
        first_text = ""
        found_title = False
        for replacement in replacements:
            if not isinstance(replacement, dict):
                continue
            text = str(replacement.get("text") or "").strip()
            if not text:
                continue
            if not first_text:
                first_text = text
            slot_id = replacement.get("slot_id")
            if isinstance(slot_id, str) and role_lookup.get((source_slide, slot_id)) == "title_candidate":
                titles.append((plan_slide, text))
                found_title = True
                break
        if not found_title and first_text:
            titles.append((plan_slide, first_text))
    return titles


def _table_tokens(plan: dict[str, Any]) -> list[tuple[int, str]]:
    tokens: list[tuple[int, str]] = []
    for plan_slide, slide in enumerate(plan.get("slides", []), start=1):
        for table_edit in slide.get("table_edits", []) or []:
            for cell in table_edit.get("cells", []) or []:
                text = str(cell.get("text") or "").strip()
                if text:
                    tokens.append((plan_slide, text))
    return tokens


def _chart_tokens(plan: dict[str, Any]) -> list[tuple[int, str]]:
    tokens: list[tuple[int, str]] = []
    for plan_slide, slide in enumerate(plan.get("slides", []), start=1):
        for chart_edit in slide.get("chart_edits", []) or []:
            for category in chart_edit.get("categories", []) or []:
                if str(category).strip():
                    tokens.append((plan_slide, str(category)))
            for series in chart_edit.get("series", []) or []:
                name = str(series.get("name") or "").strip()
                if name:
                    tokens.append((plan_slide, name))
                for value in series.get("values", []) or []:
                    tokens.append((plan_slide, str(value)))
    return tokens


def _append_token_checks(
    *,
    results: list[dict[str, Any]],
    summary: dict[str, int],
    markdown: str,
    tokens: list[tuple[int, str]],
    code: str,
    label: str,
) -> None:
    seen: set[tuple[int, str]] = set()
    for plan_slide, text in tokens:
        key = (plan_slide, text)
        if key in seen:
            continue
        seen.add(key)
        if _contains_text(markdown, text):
            summary["ok"] += 1
            continue
        summary["warn"] += 1
        results.append(
            {
                "status": "WARN",
                "code": code,
                "plan_slide": plan_slide,
                "message": f"{label} not found in read-back Markdown",
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

    library = _first_library(project_path)
    role_lookup = _slot_role_lookup(library)
    _append_token_checks(
        results=results,
        summary=summary,
        markdown=markdown,
        tokens=_title_texts(plan, role_lookup),
        code="title_missing_in_readback",
        label="key title",
    )
    _append_token_checks(
        results=results,
        summary=summary,
        markdown=markdown,
        tokens=_table_tokens(plan),
        code="table_text_missing_in_readback",
        label="table text",
    )
    _append_token_checks(
        results=results,
        summary=summary,
        markdown=markdown,
        tokens=_chart_tokens(plan),
        code="chart_text_missing_in_readback",
        label="chart text",
    )

    planned_notes = [
        slide
        for slide in plan.get("slides", []) or []
        if str(slide.get("notes") or slide.get("speaker_notes") or "").strip()
    ]
    note_sections = markdown.count("### Speaker Notes")
    if len(planned_notes) == note_sections:
        summary["ok"] += 1
    elif planned_notes:
        summary["warn"] += 1
        results.append(
            {
                "status": "WARN",
                "code": "notes_count_mismatch",
                "expected": len(planned_notes),
                "actual": note_sections,
                "message": "read-back speaker notes count does not match planned notes",
            }
        )
    elif note_sections:
        summary["warn"] += 1
        results.append(
            {
                "status": "WARN",
                "code": "unexpected_notes_in_readback",
                "expected": 0,
                "actual": note_sections,
                "message": "read-back contains speaker notes although the plan has no notes fields",
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
