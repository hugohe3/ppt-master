#!/usr/bin/env python3
"""
PPT Master - Native Existing PPTX Enhancer

Implementation core for the public native enhancement CLI and its legacy
narration compatibility entrypoint. It enhances an existing PPTX without
entering the SVG generation pipeline or modifying the original file.

Enhancement modules: read-only delivery checks, speaker notes, narration audio,
slide auto-advance timings, and optional global or per-slide page transitions.

Usage:
    python3 scripts/native_enhance_pptx.py init <source.pptx> [--name project_name]
    python3 scripts/native_enhance_pptx.py apply <project_path> [--output output.pptx]
    python3 scripts/native_enhance_pptx.py validate <project_path>

Examples:
    python3 scripts/native_enhance_pptx.py init projects/source.pptx --name fire_station
    python3 scripts/native_enhance_pptx.py apply projects/fire_station_native_enhance_20260626
    python3 scripts/native_enhance_pptx.py validate projects/fire_station_native_enhance_20260626

Dependencies:
    ffprobe for narration decodability and audio-duration validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from pptx_delivery_check import audit_pptx_delivery  # noqa: E402
from pptx_animations import (  # noqa: E402
    object_animation_fingerprint,
    validate_pptx_animation_package,
)
from pptx_transitions import (  # noqa: E402
    AdvanceUpdate,
    EnterUpdate,
    LEGACY_TRANSITION_KEYS,
    NATIVE_TRANSITION_KEYS,
    apply_slide_motion_xml,
    normalize_transition_effect_request,
    set_directory_use_timings,
    validate_pptx_transition_package,
    validate_seconds,
)
from svg_to_pptx.pptx_package.builder import (  # noqa: E402
    _add_default_content_type,
    _append_relationship,
    _ensure_notes_master,
)
from svg_to_pptx.pptx_package.narration import (  # noqa: E402
    AUDIO_CONTENT_TYPES,
    AUDIO_MARKER_PNG_BYTES,
    AUDIO_REL_TYPE,
    IMAGE_REL_TYPE,
    MEDIA_REL_TYPE,
    NARRATION_EXTENSIONS,
    inject_narration,
    next_shape_id,
    probe_audio_duration,
)
from svg_to_pptx.pptx_package.notes import (  # noqa: E402
    create_notes_slide_rels_xml,
    create_notes_slide_xml,
    markdown_to_plain_text,
)

configure_utf8_stdio()


PROJECT_SCHEMA = "native_pptx_enhancement_project.v1"
PLAN_SCHEMA = "native_pptx_enhancement_plan.v1"
VALIDATION_SCHEMA = "native_pptx_enhancement_validation.v1"
LEGACY_PROJECT_SCHEMAS = {"native_narration_pptx_project.v1"}
_WRITABLE_MODULES = ("notes", "audio", "timings", "transitions")
NOTES_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPE_NOTES_SLIDE = (
    "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
)
CONTENT_TYPE_NOTES_MASTER = (
    "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"
)
CONTENT_TYPE_THEME = "application/vnd.openxmlformats-officedocument.theme+xml"
_NOTES_SLIDE_PART_RE = re.compile(
    r"^ppt/notesSlides/notesSlide([1-9]\d*)\.xml$"
)
_LEGACY_MISSING_NOTES_MASTER_RE = re.compile(
    r"^ppt/notesSlides/_rels/notesSlide[1-9]\d*\.xml\.rels"
    r" -> ppt/notesmasters/notesmaster[1-9]\d*\.xml$",
    re.IGNORECASE,
)
_TRANSITION_MODULE_FIELDS = frozenset(
    {
        "enabled",
        "requires_confirmation",
        "status",
        "effect",
        "duration",
        "effect_options",
        "apply_without_audio",
        "slides",
    }
)
_TRANSITION_OVERRIDE_FIELDS = frozenset(
    {"effect", "duration", "effect_options"}
)
@dataclass(frozen=True)
class SlidePart:
    index: int
    part_name: str
    slide_number: int


@dataclass
class MaterialReadiness:
    note_paths: dict[int, Path]
    audio_paths: dict[int, Path]
    audio_durations: dict[int, float]
    notes_count: int
    audio_count: int
    missing_notes: list[int]
    invalid_notes: dict[int, str]
    missing_audio: list[int]
    invalid_audio: dict[int, str]
    module_errors: list[str]

    @property
    def ready(self) -> bool:
        return not (
            self.missing_notes
            or self.invalid_notes
            or self.missing_audio
            or self.invalid_audio
            or self.module_errors
        )


@dataclass(frozen=True)
class ResolvedTransitionPlan:
    global_enter: EnterUpdate
    slide_enters: Mapping[int, EnterUpdate]
    apply_without_audio: bool


def _sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_-]+", "_", value).strip("_")
    return slug or "native_enhance"


def _positive_seconds_arg(value: str) -> float:
    try:
        return validate_seconds(value, "transition duration", allow_zero=False)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _non_negative_seconds_arg(value: str) -> float:
    try:
        return validate_seconds(value, "narration padding", allow_zero=True)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_preflight_report(
    project_path: Path,
    plan: dict,
    modules: set[str],
    *,
    status: str,
    **details: object,
) -> dict:
    report = {
        "schema": VALIDATION_SCHEMA,
        "status": status,
        "phase": "preflight",
        "plan_status": plan.get("status") or "missing",
        "enabled_modules": sorted(modules),
        **details,
    }
    validation_dir = project_path / "validation"
    validation_dir.mkdir(exist_ok=True)
    _write_json(validation_dir / "report.json", report)
    return report


def _delivery_issues(report: dict, field: str) -> list[dict]:
    issues = report.get(field)
    if not isinstance(issues, list):
        return []
    return [issue for issue in issues if isinstance(issue, dict)]


def _fatal_source_delivery_messages(report: dict) -> list[str]:
    fatal = [
        issue
        for issue in _delivery_issues(report, "errors")
        if not (
            issue.get("code") == "dangling_internal_relationship"
            and isinstance(issue.get("message"), str)
            and _LEGACY_MISSING_NOTES_MASTER_RE.fullmatch(
                issue["message"]
            )
            is not None
        )
    ]
    if fatal:
        return [
            str(issue.get("message") or issue)
            for issue in fatal
        ]
    if report.get("status") == "failed" and not _delivery_issues(
        report,
        "errors",
    ):
        return ["delivery check failed without structured error details"]
    return []


def _new_delivery_errors(source: dict, candidate: dict) -> list[dict]:
    source_keys = {
        json.dumps(issue, ensure_ascii=False, sort_keys=True)
        for issue in _delivery_issues(source, "errors")
    }
    return [
        issue
        for issue in _delivery_issues(candidate, "errors")
        if json.dumps(issue, ensure_ascii=False, sort_keys=True)
        not in source_keys
    ]


def _delivery_has_findings(report: dict) -> bool:
    return bool(
        _delivery_issues(report, "errors")
        or _delivery_issues(report, "advisories")
    )


def _delivery_hidden_slide_indices(
    report: dict,
) -> tuple[int, ...] | None:
    slides = report.get("slides")
    hidden = slides.get("hidden") if isinstance(slides, dict) else None
    if not isinstance(hidden, list):
        return None
    indices: list[int] = []
    for item in hidden:
        index = item.get("index") if isinstance(item, dict) else None
        if isinstance(index, bool) or not isinstance(index, int):
            return None
        indices.append(index)
    return tuple(indices)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _archive_source_pptx(source_pptx: Path, archived_pptx: Path, projects_root: Path) -> str:
    """Move project-local sources into the project; copy external sources."""
    archived_pptx.parent.mkdir(parents=True, exist_ok=True)
    if source_pptx.resolve() == archived_pptx.resolve():
        return "reuse"
    if _is_relative_to(source_pptx, projects_root):
        shutil.move(str(source_pptx), str(archived_pptx))
        return "move"
    shutil.copy2(source_pptx, archived_pptx)
    return "copy"


def _relationship_file_for_part(extract_dir: Path, part_name: str) -> Path:
    part = Path(part_name)
    return extract_dir / part.parent / "_rels" / f"{part.name}.rels"


def _ensure_rels_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<Relationships xmlns="{PACKAGE_REL_NS}">\n</Relationships>',
        encoding="utf-8",
    )


def _target_to_part(target: str) -> str:
    target = target.lstrip("/")
    if target.startswith("ppt/"):
        return target
    return f"ppt/{target}"


def _slide_number_from_part(part_name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", part_name)
    if not match:
        raise ValueError(f"Unsupported slide part name: {part_name}")
    return int(match.group(1))


def _resolve_relationship_part(source_part: str, target: str) -> str:
    """Resolve an internal relationship target to a package part name."""
    target_path = target.split("#", 1)[0]
    if target_path.startswith("/"):
        return posixpath.normpath(target_path.lstrip("/"))
    return posixpath.normpath(
        posixpath.join(posixpath.dirname(source_part), target_path)
    )


def _notes_slide_index(part_name: str) -> int | None:
    match = _NOTES_SLIDE_PART_RE.fullmatch(part_name)
    return int(match.group(1)) if match else None


def _is_notes_slide_part(part_name: str) -> bool:
    """Return whether a relationship target stays in the notesSlides folder."""
    return (
        posixpath.dirname(part_name) == "ppt/notesSlides"
        and posixpath.basename(part_name).endswith(".xml")
        and posixpath.basename(part_name) != ".xml"
    )


def _notes_slide_part_for_slide(
    extract_dir: Path,
    slide: SlidePart,
) -> str | None:
    """Return the notes part currently related to a slide, if present."""
    slide_rels = _relationship_file_for_part(extract_dir, slide.part_name)
    if not slide_rels.exists():
        return None

    related_parts: list[str] = []
    for rel in ET.parse(slide_rels).getroot():
        if rel.attrib.get("Type") != NOTES_REL_TYPE:
            continue
        if rel.attrib.get("TargetMode", "").lower() == "external":
            raise RuntimeError(
                f"Slide {slide.index} has an external notesSlide relationship"
            )
        target = rel.attrib.get("Target")
        if not target:
            raise RuntimeError(
                f"Slide {slide.index} notesSlide relationship has no Target"
            )
        part_name = _resolve_relationship_part(slide.part_name, target)
        if not _is_notes_slide_part(part_name):
            raise RuntimeError(
                f"Slide {slide.index} has an unsupported notesSlide target: {target}"
            )
        related_parts.append(part_name)

    if len(related_parts) > 1:
        raise RuntimeError(
            f"Slide {slide.index} has multiple notesSlide relationships"
        )
    return related_parts[0] if related_parts else None


def _used_notes_slide_indices(extract_dir: Path) -> set[int]:
    """Collect every notesSlide number already reserved in the package."""
    used: set[int] = set()
    notes_dir = extract_dir / "ppt" / "notesSlides"
    for path in notes_dir.glob("notesSlide*.xml"):
        index = _notes_slide_index(f"ppt/notesSlides/{path.name}")
        if index is not None:
            used.add(index)
    for path in (notes_dir / "_rels").glob("notesSlide*.xml.rels"):
        index = _notes_slide_index(
            f"ppt/notesSlides/{path.name.removesuffix('.rels')}"
        )
        if index is not None:
            used.add(index)

    content_types_path = extract_dir / "[Content_Types].xml"
    if content_types_path.exists():
        content_types = content_types_path.read_text(encoding="utf-8")
        for match in re.finditer(
            r'PartName="/(ppt/notesSlides/notesSlide[1-9]\d*\.xml)"',
            content_types,
        ):
            index = _notes_slide_index(match.group(1))
            if index is not None:
                used.add(index)

    slides_rels_dir = extract_dir / "ppt" / "slides" / "_rels"
    for rels_path in slides_rels_dir.glob("slide*.xml.rels"):
        source_part = f"ppt/slides/{rels_path.name.removesuffix('.rels')}"
        for rel in ET.parse(rels_path).getroot():
            if (
                rel.attrib.get("Type") != NOTES_REL_TYPE
                or rel.attrib.get("TargetMode", "").lower() == "external"
            ):
                continue
            target = rel.attrib.get("Target")
            if not target:
                continue
            index = _notes_slide_index(
                _resolve_relationship_part(source_part, target)
            )
            if index is not None:
                used.add(index)
    return used


def _allocate_notes_slide_part(extract_dir: Path) -> str:
    used = _used_notes_slide_indices(extract_dir)
    index = max(used, default=0) + 1
    return f"ppt/notesSlides/notesSlide{index}.xml"


def read_slide_parts(extract_dir: Path) -> list[SlidePart]:
    presentation_path = extract_dir / "ppt" / "presentation.xml"
    rels_path = extract_dir / "ppt" / "_rels" / "presentation.xml.rels"
    if not presentation_path.exists() or not rels_path.exists():
        raise RuntimeError("PPTX package is missing presentation.xml or its relationships")

    rels_root = ET.parse(rels_path).getroot()
    rels: dict[str, str] = {}
    for rel in rels_root.findall(f"{{{PACKAGE_REL_NS}}}Relationship"):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            rels[rel_id] = target

    presentation_root = ET.parse(presentation_path).getroot()
    slide_parts: list[SlidePart] = []
    for index, slide_id in enumerate(
        presentation_root.findall(f".//{{{PRESENTATION_NS}}}sldId"),
        1,
    ):
        rel_id = slide_id.attrib.get(f"{{{REL_NS}}}id")
        if not rel_id or rel_id not in rels:
            continue
        part_name = _target_to_part(rels[rel_id])
        slide_parts.append(
            SlidePart(
                index=index,
                part_name=part_name,
                slide_number=_slide_number_from_part(part_name),
            )
        )
    if not slide_parts:
        raise RuntimeError("No slides found in presentation.xml")
    return slide_parts


def _source_state_errors(
    project_path: Path,
    project: dict,
    source_pptx: Path,
    slides: list[SlidePart],
) -> list[str]:
    """Return source-drift and slide-index consistency errors."""
    errors: list[str] = []
    actual_count = len(slides)
    actual_roster = [slide.part_name for slide in slides]

    expected_sha256 = project.get("source_sha256")
    if expected_sha256 is not None:
        if (
            not isinstance(expected_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
        ):
            errors.append("project.json source_sha256 is not a lowercase SHA-256 digest")
        elif _file_sha256(source_pptx) != expected_sha256:
            errors.append("archived source PPTX SHA-256 no longer matches project.json")

    expected_project_count = project.get("slide_count")
    if isinstance(expected_project_count, bool) or not isinstance(
        expected_project_count,
        int,
    ):
        errors.append("project.json slide_count is not an integer")
    elif expected_project_count != actual_count:
        errors.append(
            "archived source slide count no longer matches project.json: "
            f"{actual_count} != {expected_project_count}"
        )

    expected_project_roster = project.get("slide_part_roster")
    if expected_project_roster is not None:
        if (
            not isinstance(expected_project_roster, list)
            or any(
                not isinstance(part_name, str) or not part_name
                for part_name in expected_project_roster
            )
        ):
            errors.append("project.json slide_part_roster is not an array of part names")
        elif expected_project_roster != actual_roster:
            errors.append(
                "archived source ordered slide-part roster no longer matches "
                "project.json"
            )

    slide_index_path = project_path / "analysis" / "slide_index.json"
    if not slide_index_path.is_file():
        errors.append(f"slide index is missing: {slide_index_path}")
        return errors
    try:
        slide_index = _read_json(slide_index_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"unable to read slide index: {exc}")
        return errors

    expected_index_count = slide_index.get("slide_count")
    if isinstance(expected_index_count, bool) or not isinstance(
        expected_index_count,
        int,
    ):
        errors.append("slide_index.json slide_count is not an integer")
    elif expected_index_count != actual_count:
        errors.append(
            "archived source slide count no longer matches slide_index.json: "
            f"{actual_count} != {expected_index_count}"
        )

    indexed_slides = slide_index.get("slides")
    if not isinstance(indexed_slides, list):
        errors.append("slide_index.json slides is not an array")
        return errors
    expected_roster: list[str] = []
    for index, item in enumerate(indexed_slides, 1):
        part_name = item.get("part_name") if isinstance(item, dict) else None
        if not isinstance(part_name, str) or not part_name:
            errors.append(
                f"slide_index.json slides[{index - 1}].part_name is invalid"
            )
            continue
        expected_roster.append(part_name)
    if len(expected_roster) == len(indexed_slides) and expected_roster != actual_roster:
        errors.append(
            "archived source ordered slide-part roster no longer matches "
            "slide_index.json"
        )
    return errors


def _zip_dir(source_dir: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir).as_posix())


def _extract_pptx(source_pptx: Path, extract_dir: Path) -> None:
    with zipfile.ZipFile(source_pptx, "r") as zf:
        zf.extractall(extract_dir)


def _note_path(notes_dir: Path, index: int) -> Path | None:
    candidates = [
        notes_dir / f"{index:03d}.md",
        notes_dir / f"{index:02d}.md",
        notes_dir / f"{index}.md",
        notes_dir / f"slide{index:03d}.md",
        notes_dir / f"slide{index:02d}.md",
        notes_dir / f"slide{index}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _audio_path(audio_dir: Path, index: int) -> Path | None:
    stems = [
        f"{index:03d}",
        f"{index:02d}",
        str(index),
        f"slide{index:03d}",
        f"slide{index:02d}",
        f"slide{index}",
    ]
    for stem in stems:
        for ext in NARRATION_EXTENSIONS:
            candidate = audio_dir / f"{stem}{ext}"
            if candidate.exists():
                return candidate
    return None


def _collect_material_readiness(
    slides: list[SlidePart],
    notes_dir: Path,
    audio_dir: Path,
    modules: set[str],
) -> MaterialReadiness:
    """Inspect enabled-module inputs once for both validation and application."""
    notes_required = "notes" in modules
    audio_required = "audio" in modules or "timings" in modules
    timings_enabled = "timings" in modules
    note_paths: dict[int, Path] = {}
    audio_paths: dict[int, Path] = {}
    audio_durations: dict[int, float] = {}
    missing_notes: list[int] = []
    invalid_notes: dict[int, str] = {}
    missing_audio: list[int] = []
    invalid_audio: dict[int, str] = {}

    for slide in slides:
        note = _note_path(notes_dir, slide.index)
        if note is None:
            if notes_required:
                missing_notes.append(slide.index)
        else:
            try:
                note_text = markdown_to_plain_text(
                    note.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError) as exc:
                if notes_required:
                    invalid_notes[slide.index] = f"unable to read {note.name}: {exc}"
            else:
                if note_text:
                    note_paths[slide.index] = note
                elif notes_required:
                    invalid_notes[slide.index] = f"{note.name} has no spoken text"

        audio = _audio_path(audio_dir, slide.index)
        if audio is None:
            if audio_required:
                missing_audio.append(slide.index)
            continue
        try:
            if not audio.is_file() or audio.stat().st_size <= 0:
                raise ValueError(f"{audio.name} is not a non-empty file")
        except (OSError, ValueError) as exc:
            if audio_required:
                invalid_audio[slide.index] = str(exc)
            continue

        if audio_required:
            duration = probe_audio_duration(audio)
            if duration is None:
                invalid_audio[slide.index] = (
                    f"unable to decode {audio.name} with ffprobe"
                )
                continue
            if timings_enabled:
                audio_durations[slide.index] = duration
        audio_paths[slide.index] = audio

    module_errors: list[str] = []
    if timings_enabled and "audio" not in modules:
        module_errors.append("timings requires the audio module")
    return MaterialReadiness(
        note_paths=note_paths,
        audio_paths=audio_paths,
        audio_durations=audio_durations,
        notes_count=len(note_paths),
        audio_count=len(audio_paths),
        missing_notes=missing_notes,
        invalid_notes=invalid_notes,
        missing_audio=missing_audio,
        invalid_audio=invalid_audio,
        module_errors=module_errors,
    )


def _material_readiness_messages(readiness: MaterialReadiness) -> list[str]:
    messages = list(readiness.module_errors)
    if readiness.missing_notes:
        messages.append(
            "missing notes for slide(s): "
            + ", ".join(str(index) for index in readiness.missing_notes)
        )
    if readiness.invalid_notes:
        messages.append(
            "invalid notes: "
            + "; ".join(
                f"slide {index}: {reason}"
                for index, reason in sorted(readiness.invalid_notes.items())
            )
        )
    if readiness.missing_audio:
        messages.append(
            "missing audio for slide(s): "
            + ", ".join(str(index) for index in readiness.missing_audio)
        )
    if readiness.invalid_audio:
        messages.append(
            "invalid audio: "
            + "; ".join(
                f"slide {index}: {reason}"
                for index, reason in sorted(readiness.invalid_audio.items())
            )
        )
    return messages


def _material_readiness_report_fields(
    readiness: MaterialReadiness,
) -> dict[str, object]:
    return {
        "notes_count": readiness.notes_count,
        "audio_count": readiness.audio_count,
        "missing_notes": readiness.missing_notes,
        "invalid_notes": sorted(readiness.invalid_notes),
        "invalid_note_reasons": readiness.invalid_notes,
        "missing_audio": readiness.missing_audio,
        "invalid_audio": sorted(readiness.invalid_audio),
        "invalid_audio_reasons": readiness.invalid_audio,
        "module_errors": readiness.module_errors,
    }


def _add_override(content_types: str, part_name: str, content_type: str) -> str:
    if re.search(
        rf'<Override\b[^>]*\bPartName="/{re.escape(part_name)}"[^>]*/>',
        content_types,
    ):
        return content_types
    override = f'  <Override PartName="/{part_name}" ContentType="{content_type}"/>'
    return content_types.replace("</Types>", override + "\n</Types>")


def _add_notes_content_types(content_types: str, note_parts: set[str]) -> str:
    content_types = _add_override(content_types, "ppt/theme/theme2.xml", CONTENT_TYPE_THEME)
    content_types = _add_override(
        content_types,
        "ppt/notesMasters/notesMaster1.xml",
        CONTENT_TYPE_NOTES_MASTER,
    )
    for part_name in sorted(note_parts):
        content_types = _add_override(
            content_types,
            part_name,
            CONTENT_TYPE_NOTES_SLIDE,
        )
    return content_types


def _apply_notes(
    extract_dir: Path,
    slide: SlidePart,
    note_md: Path,
) -> str | None:
    notes_text = markdown_to_plain_text(note_md.read_text(encoding="utf-8"))
    if not notes_text:
        return None

    _ensure_notes_master(extract_dir)
    slide_rels = _relationship_file_for_part(extract_dir, slide.part_name)
    _ensure_rels_file(slide_rels)
    notes_part = _notes_slide_part_for_slide(extract_dir, slide)
    if notes_part is None:
        notes_part = _allocate_notes_slide_part(extract_dir)
        target = posixpath.relpath(
            notes_part,
            start=posixpath.dirname(slide.part_name),
        )
        _append_relationship(slide_rels, NOTES_REL_TYPE, target)

    notes_xml_path = extract_dir / notes_part
    notes_xml_path.parent.mkdir(parents=True, exist_ok=True)
    notes_xml_path.write_text(
        create_notes_slide_xml(slide.slide_number, notes_text),
        encoding="utf-8",
    )

    notes_rels_path = _relationship_file_for_part(extract_dir, notes_part)
    notes_rels_path.parent.mkdir(parents=True, exist_ok=True)
    notes_rels_path.write_text(
        create_notes_slide_rels_xml(slide.slide_number),
        encoding="utf-8",
    )
    return notes_part


def _native_audio_carriers(
    extract_dir: Path,
    slides: list[SlidePart],
) -> dict[int, list[str]]:
    """Return existing tool-owned narration carrier names by public slide."""
    carriers: dict[int, list[str]] = {}
    for slide in slides:
        slide_root = ET.parse(extract_dir / slide.part_name).getroot()
        names = sorted(
            {
                name
                for element in slide_root.iter(
                    f"{{{PRESENTATION_NS}}}cNvPr"
                )
                if (name := element.attrib.get("name", "")).startswith(
                    "native_enhance_audio_"
                )
            }
        )
        if names:
            carriers[slide.index] = names
    return carriers


def _allocate_media_name(media_dir: Path, preferred_name: str) -> str:
    preferred_path = media_dir / preferred_name
    if not preferred_path.exists():
        return preferred_name
    stem = preferred_path.stem
    suffix = preferred_path.suffix
    index = 2
    while True:
        candidate_name = f"{stem}_{index}{suffix}"
        if not (media_dir / candidate_name).exists():
            return candidate_name
        index += 1


def _ensure_audio_poster(media_dir: Path) -> str:
    preferred_name = "native_enhance_audio_poster.png"
    for candidate in sorted(
        media_dir.glob("native_enhance_audio_poster*.png")
    ):
        if not candidate.is_file():
            continue
        try:
            if candidate.read_bytes() == AUDIO_MARKER_PNG_BYTES:
                return candidate.name
        except OSError:
            continue
    poster_name = _allocate_media_name(media_dir, preferred_name)
    (media_dir / poster_name).write_bytes(AUDIO_MARKER_PNG_BYTES)
    return poster_name


def _apply_audio(
    extract_dir: Path,
    slide: SlidePart,
    audio_path: Path,
    *,
    enter: EnterUpdate,
    timings_enabled: bool,
    narration_padding: float,
    audio_duration: float | None = None,
) -> bool:
    media_dir = extract_dir / "ppt" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    ext = audio_path.suffix.lower()
    media_name = _allocate_media_name(
        media_dir,
        f"native_enhance_audio_{slide.index:03d}{ext}",
    )
    shutil.copy2(audio_path, media_dir / media_name)

    poster_name = _ensure_audio_poster(media_dir)

    slide_rels = _relationship_file_for_part(extract_dir, slide.part_name)
    _ensure_rels_file(slide_rels)
    media_rid = _append_relationship(slide_rels, MEDIA_REL_TYPE, f"../media/{media_name}")
    audio_rid = _append_relationship(slide_rels, AUDIO_REL_TYPE, f"../media/{media_name}")
    poster_rid = _append_relationship(slide_rels, IMAGE_REL_TYPE, f"../media/{poster_name}")

    slide_xml_path = extract_dir / slide.part_name
    slide_xml = slide_xml_path.read_text(encoding="utf-8")
    source_animation_fingerprint = object_animation_fingerprint(slide_xml)
    shape_id = next_shape_id(slide_xml)
    slide_xml = inject_narration(
        slide_xml,
        shape_id=shape_id,
        shape_name=media_name,
        audio_rid=audio_rid,
        media_rid=media_rid,
        poster_rid=poster_rid,
    )

    advance = AdvanceUpdate(mode="preserve")
    if timings_enabled:
        duration = audio_duration
        if duration is None:
            duration = probe_audio_duration(audio_path)
        if duration is None:
            raise RuntimeError(f"Unable to read narration duration with ffprobe: {audio_path}")
        advance = AdvanceUpdate(
            mode="narration",
            after=duration + narration_padding,
        )

    wrote_advance = False
    if enter.policy != "preserve" or timings_enabled:
        slide_xml, wrote_advance = apply_slide_motion_xml(
            slide_xml,
            enter=enter,
            advance=advance,
        )
    if object_animation_fingerprint(slide_xml) != source_animation_fingerprint:
        raise RuntimeError(
            f"Slide {slide.index} object animations changed while adding narration"
        )
    slide_xml_path.write_text(slide_xml, encoding="utf-8")
    return timings_enabled and wrote_advance


def _update_content_types(
    extract_dir: Path,
    note_parts: set[str],
    audio_exts: set[str],
) -> None:
    content_types_path = extract_dir / "[Content_Types].xml"
    content_types = content_types_path.read_text(encoding="utf-8")
    if note_parts:
        content_types = _add_notes_content_types(content_types, note_parts)
    for ext in sorted(audio_exts):
        content_type = AUDIO_CONTENT_TYPES.get(ext)
        if content_type:
            content_types = _add_default_content_type(content_types, ext, content_type)
    if audio_exts:
        content_types = _add_default_content_type(content_types, "png", "image/png")
    content_types_path.write_text(content_types, encoding="utf-8")


def _project_paths(project_path: Path) -> tuple[Path, Path, Path, Path]:
    project = _read_json(project_path / "project.json")
    source_pptx = project_path / project["source_pptx"]
    notes_dir = project_path / project["notes_dir"]
    audio_dir = project_path / project["audio_dir"]
    exports_dir = project_path / project["exports_dir"]
    return source_pptx, notes_dir, audio_dir, exports_dir


def _output_path_error(
    project_path: Path,
    project: dict,
    source_pptx: Path,
    output_path: Path,
) -> str | None:
    if output_path.suffix.lower() != ".pptx":
        return f"output must use a .pptx extension: {output_path}"
    if output_path == source_pptx.resolve():
        return "output must not overwrite the archived source PPTX"

    source_import = project.get("source_import")
    if isinstance(source_import, dict):
        original_path = source_import.get("original_path")
        if isinstance(original_path, str) and original_path:
            try:
                original = Path(original_path).expanduser().resolve()
            except OSError:
                original = None
            if original is not None and output_path == original:
                return "output must not overwrite the original source PPTX"

    protected = (
        project_path / "sources",
        project_path / "analysis",
        project_path / "notes",
        project_path / "audio",
        project_path / "validation",
    )
    for directory in protected:
        if _is_relative_to(output_path, directory):
            return (
                "output must not be written inside native-enhance control "
                f"directory: {directory}"
            )
    return None


def _plan_path(project_path: Path) -> Path:
    return project_path / "analysis" / "enhancement_plan.json"


def _load_enhancement_plan(project_path: Path) -> dict:
    path = _plan_path(project_path)
    if not path.exists():
        return {}
    return _read_json(path)


def _enabled_modules(plan: dict) -> set[str]:
    modules = plan.get("modules")
    if not isinstance(modules, dict):
        return set(_WRITABLE_MODULES)
    enabled: set[str] = set()
    for name in _WRITABLE_MODULES:
        config = modules.get(name)
        if isinstance(config, dict) and config.get("enabled") is True:
            enabled.add(name)
    return enabled


def _resolve_enter_update(
    *,
    cli_effect: str | None,
    configured_effect: object,
    configured_effect_options: object = None,
    transitions_enabled: bool,
    duration: float,
) -> EnterUpdate:
    if cli_effect is None and not transitions_enabled:
        if configured_effect == "none":
            normalize_transition_effect_request(
                configured_effect,
                configured_effect_options,
            )
            return EnterUpdate(policy="none", effect=None, duration=duration)
        return EnterUpdate(policy="preserve", duration=duration)

    effect = cli_effect if cli_effect is not None else configured_effect
    if effect == "none":
        normalize_transition_effect_request(
            effect,
            None if cli_effect is not None else configured_effect_options,
        )
        return EnterUpdate(policy="none", effect=None, duration=duration)
    effect, effect_options = normalize_transition_effect_request(
        effect,
        None if cli_effect is not None else configured_effect_options,
        allow_none=False,
    )

    return EnterUpdate(
        policy="replace",
        effect=effect,
        duration=duration,
        effect_options=effect_options,
    )


def _plan_confirmed(plan: dict) -> bool:
    return plan.get("status") == "confirmed"


def _native_transition_config(
    transition: str,
    duration: float,
    effect_options: object = None,
) -> dict[str, object]:
    if transition == "none":
        normalize_transition_effect_request(transition, effect_options)
        return {"effect": "none", "duration": duration}
    effect, effect_options = normalize_transition_effect_request(
        transition,
        effect_options,
        allow_none=False,
    )
    config: dict[str, object] = {
        "effect": effect,
        "duration": duration,
    }
    if effect_options:
        config["effect_options"] = effect_options
    return config


def _module_config(plan: dict, name: str) -> dict:
    modules = plan.get("modules")
    if not isinstance(modules, dict):
        return {}
    config = modules.get(name)
    return config if isinstance(config, dict) else {}


def _preserved_enabled(plan: dict, name: str, default: bool) -> bool:
    config = _module_config(plan, name)
    if "enabled" not in config:
        return default
    value = config["enabled"]
    if not isinstance(value, bool):
        raise ValueError(
            f"enhancement plan module {name}.enabled must be a boolean"
        )
    return value


def _resolved_draft_transition_config(
    project: dict,
    existing_plan: dict,
    *,
    transition: str | None,
    transition_duration: float | None,
    apply_transition_without_audio: bool | None,
) -> tuple[bool, dict[str, object]]:
    existing = _module_config(existing_plan, "transitions")
    project_default = (
        project.get("transition")
        if isinstance(project.get("transition"), dict)
        else {}
    )

    if transition is not None:
        raw_effect: object = transition
        raw_options: object = None
    elif "effect" in existing:
        raw_effect = existing["effect"]
        raw_options = existing.get("effect_options")
    elif "effect" in project_default:
        raw_effect = project_default["effect"]
        raw_options = project_default.get("effect_options")
    else:
        raw_effect = "fade"
        raw_options = None

    if not isinstance(raw_effect, str):
        raise ValueError("transition effect must be a string")
    if transition_duration is not None:
        raw_duration: object = transition_duration
    elif "duration" in existing:
        raw_duration = existing["duration"]
    elif "duration" in project_default:
        raw_duration = project_default["duration"]
    else:
        raw_duration = 0.5
    duration = validate_seconds(
        raw_duration,
        "transition duration",
        allow_zero=False,
    )
    config = _native_transition_config(
        raw_effect,
        duration,
        raw_options,
    )

    if apply_transition_without_audio is None:
        raw_apply_without_audio = existing.get(
            "apply_without_audio",
            False,
        )
    else:
        raw_apply_without_audio = apply_transition_without_audio
    if not isinstance(raw_apply_without_audio, bool):
        raise ValueError("transition apply_without_audio must be a boolean")
    config["apply_without_audio"] = raw_apply_without_audio

    if "slides" in existing:
        slides = existing["slides"]
        if not isinstance(slides, dict):
            raise ValueError("transition slides must be an object")
        config["slides"] = {
            str(key): dict(value) if isinstance(value, dict) else value
            for key, value in slides.items()
        }

    if transition is not None:
        enabled = transition != "none"
    else:
        enabled = _preserved_enabled(
            existing_plan,
            "transitions",
            raw_effect != "none",
        )
    return enabled, config


def _build_enhancement_plan(
    project: dict,
    *,
    slide_count: int,
    notes_count: int,
    audio_count: int,
    transition: str | None,
    transition_duration: float | None,
    narration_padding: float | None,
    apply_transition_without_audio: bool | None,
    existing_plan: dict | None = None,
) -> dict:
    previous = existing_plan or {}
    notes_enabled = _preserved_enabled(previous, "notes", True)
    audio_enabled = _preserved_enabled(previous, "audio", True)
    timings_enabled = _preserved_enabled(previous, "timings", True)
    previous_timings = _module_config(previous, "timings")
    raw_padding: object
    if narration_padding is not None:
        raw_padding = narration_padding
    else:
        raw_padding = previous_timings.get("narration_padding", 0.4)
    resolved_padding = validate_seconds(
        raw_padding,
        "narration padding",
        allow_zero=True,
    )
    transitions_enabled, transition_config = _resolved_draft_transition_config(
        project,
        previous,
        transition=transition,
        transition_duration=transition_duration,
        apply_transition_without_audio=apply_transition_without_audio,
    )
    return {
        "schema": PLAN_SCHEMA,
        "status": "draft",
        "source_pptx": project.get("source_pptx"),
        "slide_count": slide_count,
        "modules": {
            "notes": {
                "enabled": notes_enabled,
                "requires_confirmation": True,
                "status": (
                    "disabled"
                    if not notes_enabled
                    else (
                        "coverage_complete"
                        if notes_count == slide_count
                        else "needs_notes"
                    )
                ),
                "coverage": {"present": notes_count, "total": slide_count},
            },
            "audio": {
                "enabled": audio_enabled,
                "requires_confirmation": True,
                "status": (
                    "disabled"
                    if not audio_enabled
                    else (
                        "coverage_complete"
                        if audio_count == slide_count
                        else "needs_audio"
                    )
                ),
                "coverage": {"present": audio_count, "total": slide_count},
                "decodability": "unchecked",
            },
            "timings": {
                "enabled": timings_enabled,
                "requires_confirmation": True,
                "status": (
                    "disabled"
                    if not timings_enabled
                    else (
                        "audio_coverage_complete"
                        if audio_enabled and audio_count == slide_count
                        else "blocked_until_audio"
                    )
                ),
                "source": "audio_duration",
                "narration_padding": resolved_padding,
            },
            "transitions": {
                "enabled": transitions_enabled,
                "requires_confirmation": True,
                "status": (
                    "ready"
                    if (
                        transitions_enabled
                        or transition_config.get("effect") == "none"
                        or bool(transition_config.get("slides"))
                    )
                    else "disabled"
                ),
                **transition_config,
            },
        },
        "not_in_v1": [
            "object_animation",
            "visible_watermark",
            "footer_or_logo_insertion",
            "background_music",
            "media_compression",
        ],
    }


def _resolve_slide_enter(
    base: EnterUpdate,
    override: dict,
    *,
    slide_index: int,
) -> EnterUpdate:
    unknown = sorted(set(override) - _TRANSITION_OVERRIDE_FIELDS)
    if unknown:
        raise ValueError(
            f"transition slides.{slide_index} has unknown field(s): "
            + ", ".join(unknown)
        )

    raw_duration = override.get("duration", base.duration)
    duration = validate_seconds(
        raw_duration,
        f"transition slides.{slide_index}.duration",
        allow_zero=False,
    )
    effect = override.get("effect")
    if effect == "preserve":
        if "effect_options" in override:
            raise ValueError(
                f"transition slides.{slide_index} preserve cannot have "
                "effect_options"
            )
        return EnterUpdate(policy="preserve", duration=duration)

    if effect is None:
        if base.policy == "preserve":
            if "effect_options" in override:
                raise ValueError(
                    f"transition slides.{slide_index} effect_options requires "
                    "a native effect"
                )
            return EnterUpdate(policy="preserve", duration=duration)
        if base.policy == "none":
            if "effect_options" in override:
                raise ValueError(
                    f"transition slides.{slide_index} none cannot have "
                    "effect_options"
                )
            return EnterUpdate(policy="none", effect=None, duration=duration)
        effect = base.effect
        effect_options = override.get(
            "effect_options",
            base.effect_options,
        )
    else:
        if not isinstance(effect, str):
            raise ValueError(
                f"transition slides.{slide_index}.effect must be a string"
            )
        effect_options = override.get("effect_options")

    return _resolve_enter_update(
        cli_effect=None,
        configured_effect=effect,
        configured_effect_options=effect_options,
        transitions_enabled=True,
        duration=duration,
    )


def _validate_plan_modules(plan: dict) -> None:
    if plan and plan.get("schema") != PLAN_SCHEMA:
        raise ValueError(
            f"unsupported enhancement plan schema: {plan.get('schema')!r}"
        )
    modules_cfg = plan.get("modules")
    if modules_cfg is None:
        return
    if not isinstance(modules_cfg, dict):
        raise ValueError("enhancement plan modules must be an object")

    unknown_modules = sorted(set(modules_cfg) - set(_WRITABLE_MODULES))
    if unknown_modules:
        raise ValueError(
            "enhancement plan has unknown module(s): "
            + ", ".join(unknown_modules)
        )
    if plan.get("schema") == PLAN_SCHEMA:
        missing_modules = [
            name
            for name in _WRITABLE_MODULES
            if name not in modules_cfg
        ]
        if missing_modules:
            raise ValueError(
                "enhancement plan is missing module(s): "
                + ", ".join(missing_modules)
            )
    for name in _WRITABLE_MODULES:
        config = modules_cfg.get(name)
        if config is not None and not isinstance(config, dict):
            raise ValueError(
                f"enhancement plan module {name} must be an object"
            )
        if (
            isinstance(config, dict)
            and (
                "enabled" not in config
                or not isinstance(config["enabled"], bool)
            )
        ):
            raise ValueError(
                f"enhancement plan module {name}.enabled must be a boolean"
            )


def _resolve_transition_plan(
    project: dict,
    plan: dict,
    slides: list[SlidePart],
    *,
    cli_effect: str | None = None,
    cli_duration: float | None = None,
    cli_apply_without_audio: bool = False,
) -> ResolvedTransitionPlan:
    _validate_plan_modules(plan)
    plan_slide_count = plan.get("slide_count")
    if plan_slide_count is not None and plan_slide_count != len(slides):
        raise ValueError(
            "enhancement plan slide_count no longer matches the archived "
            f"source: {plan_slide_count!r} != {len(slides)}"
        )

    modules = _enabled_modules(plan)
    transitions_cfg = _module_config(plan, "transitions")
    unknown = sorted(set(transitions_cfg) - _TRANSITION_MODULE_FIELDS)
    if unknown:
        raise ValueError(
            "transition module has unknown field(s): " + ", ".join(unknown)
        )

    project_transition = (
        project.get("transition")
        if isinstance(project.get("transition"), dict)
        else {}
    )
    if (
        cli_effect is None
        and "effect_options" in transitions_cfg
        and "effect" not in transitions_cfg
    ):
        raise ValueError("transition effect_options requires an explicit effect")
    if (
        cli_effect is None
        and "effect_options" in project_transition
        and "effect" not in project_transition
        and "effect" not in transitions_cfg
    ):
        raise ValueError("transition effect_options requires an explicit effect")

    if "effect" in transitions_cfg:
        configured_effect = transitions_cfg["effect"]
        configured_options = transitions_cfg.get("effect_options")
    elif "effect" in project_transition:
        configured_effect = project_transition["effect"]
        configured_options = project_transition.get("effect_options")
    else:
        configured_effect = "fade"
        configured_options = None

    if cli_duration is not None:
        raw_duration: object = cli_duration
    elif "duration" in transitions_cfg:
        raw_duration = transitions_cfg["duration"]
    elif "duration" in project_transition:
        raw_duration = project_transition["duration"]
    else:
        raw_duration = 0.5
    duration = validate_seconds(
        raw_duration,
        "transition duration",
        allow_zero=False,
    )

    selected_base = _resolve_enter_update(
        cli_effect=cli_effect,
        configured_effect=configured_effect,
        configured_effect_options=configured_options,
        transitions_enabled=True,
        duration=duration,
    )
    global_enter = _resolve_enter_update(
        cli_effect=cli_effect,
        configured_effect=configured_effect,
        configured_effect_options=configured_options,
        transitions_enabled="transitions" in modules,
        duration=duration,
    )

    raw_apply_without_audio = transitions_cfg.get(
        "apply_without_audio",
        False,
    )
    if not isinstance(raw_apply_without_audio, bool):
        raise ValueError("transition apply_without_audio must be a boolean")
    apply_without_audio = (
        cli_apply_without_audio or raw_apply_without_audio
    )

    raw_slides = transitions_cfg.get("slides", {})
    if not isinstance(raw_slides, dict):
        raise ValueError("transition slides must be an object")
    valid_indices = {slide.index for slide in slides}
    slide_enters: dict[int, EnterUpdate] = {}
    for raw_index, override in raw_slides.items():
        if (
            not isinstance(raw_index, str)
            or re.fullmatch(r"[1-9]\d*", raw_index) is None
        ):
            raise ValueError(
                f"transition slide key must be a canonical 1-based index: "
                f"{raw_index!r}"
            )
        slide_index = int(raw_index)
        if slide_index not in valid_indices:
            raise ValueError(
                f"transition slide index is outside the source roster: "
                f"{slide_index}"
            )
        if not isinstance(override, dict):
            raise ValueError(
                f"transition slides.{slide_index} must be an object"
            )
        slide_enters[slide_index] = _resolve_slide_enter(
            selected_base,
            override,
            slide_index=slide_index,
        )

    if (
        ("transitions" in modules or cli_effect is not None)
        and "audio" not in modules
        and not apply_without_audio
        and not slide_enters
    ):
        raise ValueError(
            "transitions is enabled, but no slides are reachable: enable audio, "
            "set apply_without_audio=true, or add transitions.slides entries"
        )

    return ResolvedTransitionPlan(
        global_enter=global_enter,
        slide_enters=slide_enters,
        apply_without_audio=apply_without_audio,
    )


def _apply_transition_only(
    extract_dir: Path,
    slide: SlidePart,
    enter: EnterUpdate,
) -> bool:
    if enter.policy == "preserve":
        return False
    slide_xml_path = extract_dir / slide.part_name
    slide_xml = slide_xml_path.read_text(encoding="utf-8")
    source_animation_fingerprint = object_animation_fingerprint(slide_xml)
    slide_xml, _uses_timings = apply_slide_motion_xml(
        slide_xml,
        enter=enter,
        advance=AdvanceUpdate(mode="preserve"),
    )
    if object_animation_fingerprint(slide_xml) != source_animation_fingerprint:
        raise RuntimeError(
            f"Slide {slide.index} object animations changed while updating "
            "the transition"
        )
    slide_xml_path.write_text(slide_xml, encoding="utf-8")
    return True


def init_project(args: argparse.Namespace) -> int:
    source_pptx = Path(args.source_pptx).expanduser().resolve()
    if not source_pptx.exists() or source_pptx.suffix.lower() != ".pptx":
        print(f"error: expected an existing .pptx file: {source_pptx}", file=sys.stderr)
        return 1

    source_delivery = audit_pptx_delivery(source_pptx)
    fatal_delivery_messages = _fatal_source_delivery_messages(source_delivery)
    if fatal_delivery_messages:
        for message in fatal_delivery_messages:
            print(f"error: {message}", file=sys.stderr)
        return 1

    stem = _sanitize_slug(args.name or source_pptx.stem)
    date = datetime.now().strftime("%Y%m%d")
    project_path = (
        Path(args.project_dir).expanduser().resolve()
        if args.project_dir
        else Path(args.projects_root).expanduser().resolve() / f"{stem}_native_enhance_{date}"
    )
    if project_path.exists() and any(project_path.iterdir()):
        print(f"error: project directory already exists and is not empty: {project_path}", file=sys.stderr)
        return 1

    for dirname in ("sources", "analysis", "notes", "audio", "exports", "validation"):
        (project_path / dirname).mkdir(parents=True, exist_ok=True)

    archived_pptx = project_path / "sources" / source_pptx.name
    projects_root = Path(args.projects_root).expanduser().resolve()
    source_import_mode = _archive_source_pptx(source_pptx, archived_pptx, projects_root)

    source_md = project_path / "sources" / f"{source_pptx.stem}.md"
    ppt_to_md = _SCRIPTS_DIR / "source_to_md" / "ppt_to_md.py"
    result = subprocess.run(
        [sys.executable, str(ppt_to_md), str(archived_pptx), "-o", str(source_md)],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode

    with tempfile.TemporaryDirectory(prefix="native-enhance-intake-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(archived_pptx, extract_dir)
        slide_parts = read_slide_parts(extract_dir)
    source_sha256 = _file_sha256(archived_pptx)

    slide_index = {
        "schema": "native_pptx_enhancement_slide_index.v1",
        "source_pptx": f"sources/{source_pptx.name}",
        "slide_count": len(slide_parts),
        "slides": [
            {
                "index": slide.index,
                "note_file": f"notes/{slide.index:03d}.md",
                "audio_stem": f"{slide.index:03d}",
                "part_name": slide.part_name,
                "slide_number": slide.slide_number,
            }
            for slide in slide_parts
        ],
    }
    _write_json(project_path / "analysis" / "slide_index.json", slide_index)

    project = {
        "schema": PROJECT_SCHEMA,
        "kind": "native_pptx_enhancement",
        "modules": [
            "notes",
            "audio",
            "timings",
            "transitions",
            "delivery.check",
        ],
        "source_pptx": f"sources/{source_pptx.name}",
        "source_markdown": f"sources/{source_pptx.stem}.md",
        "source_import": {
            "mode": source_import_mode,
            "original_path": str(source_pptx),
        },
        "source_sha256": source_sha256,
        "slide_count": len(slide_parts),
        "slide_part_roster": [slide.part_name for slide in slide_parts],
        "notes_dir": "notes",
        "audio_dir": "audio",
        "exports_dir": "exports",
        "transition": _native_transition_config(
            args.transition,
            args.transition_duration,
        ),
        "audio": {
            "provider": "",
            "voice": "",
            "rate": "",
        },
    }
    _write_json(project_path / "project.json", project)
    plan = _build_enhancement_plan(
        project,
        slide_count=len(slide_parts),
        notes_count=0,
        audio_count=0,
        transition=args.transition,
        transition_duration=args.transition_duration,
        narration_padding=args.narration_padding,
        apply_transition_without_audio=args.apply_transition_without_audio,
    )
    _write_json(_plan_path(project_path), plan)
    source_delivery_file = source_delivery.get("file")
    if isinstance(source_delivery_file, dict):
        source_delivery_file["path"] = str(archived_pptx.resolve())
    _write_json(
        project_path / "validation" / "report.json",
        {
            "schema": VALIDATION_SCHEMA,
            "status": (
                "passed-with-advisories"
                if _delivery_has_findings(source_delivery)
                else "passed"
            ),
            "phase": "intake",
            "source_delivery_policy": "preserve-baseline",
            "delivery_check": source_delivery,
        },
    )

    print(f"Project: {project_path}", file=sys.stderr)
    print(f"Slides: {len(slide_parts)}", file=sys.stderr)
    print(f"Source import: {source_import_mode}", file=sys.stderr)
    print(f"Source markdown: {source_md}", file=sys.stderr)
    print(f"Draft enhancement plan: {_plan_path(project_path)}", file=sys.stderr)
    print(
        "Review the plan with the user and set status to \"confirmed\" before generating notes/audio/applying.",
        file=sys.stderr,
    )
    return 0


def plan_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project_path).expanduser().resolve()
    project = _read_json(project_path / "project.json")
    if project.get("schema") not in {PROJECT_SCHEMA, *LEGACY_PROJECT_SCHEMAS}:
        print(f"error: not a native PPTX enhancement project: {project_path}", file=sys.stderr)
        return 1

    source_pptx, notes_dir, audio_dir, _exports_dir = _project_paths(project_path)
    source_delivery = audit_pptx_delivery(source_pptx)
    fatal_delivery_messages = _fatal_source_delivery_messages(source_delivery)
    if fatal_delivery_messages:
        for message in fatal_delivery_messages:
            print(f"error: {message}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="native-enhance-plan-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(source_pptx, extract_dir)
        slides = read_slide_parts(extract_dir)

    source_errors = _source_state_errors(
        project_path,
        project,
        source_pptx,
        slides,
    )
    if source_errors:
        for error in source_errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    existing_plan = _load_enhancement_plan(project_path)
    try:
        _validate_plan_modules(existing_plan)
        readiness = _collect_material_readiness(
            slides,
            notes_dir,
            audio_dir,
            set(),
        )
        plan = _build_enhancement_plan(
            project,
            slide_count=len(slides),
            notes_count=readiness.notes_count,
            audio_count=readiness.audio_count,
            transition=args.transition,
            transition_duration=args.transition_duration,
            narration_padding=args.narration_padding,
            apply_transition_without_audio=args.apply_transition_without_audio,
            existing_plan=existing_plan,
        )
        _resolve_transition_plan(project, plan, slides)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _write_json(_plan_path(project_path), plan)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"Plan written: {_plan_path(project_path)}", file=sys.stderr)
    print(
        "Confirm by editing status to \"confirmed\" after user approval, then run apply.",
        file=sys.stderr,
    )
    return 0


def apply_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project_path).expanduser().resolve()
    project = _read_json(project_path / "project.json")
    if project.get("schema") not in {PROJECT_SCHEMA, *LEGACY_PROJECT_SCHEMAS}:
        print(f"error: not a native PPTX enhancement project: {project_path}", file=sys.stderr)
        return 1

    source_pptx, notes_dir, audio_dir, exports_dir = _project_paths(project_path)
    plan = _load_enhancement_plan(project_path)
    modules = _enabled_modules(plan)

    def fail_preflight(
        messages: list[str],
        *,
        status: str = "failed",
        **details: object,
    ) -> int:
        _write_preflight_report(
            project_path,
            plan,
            modules,
            status=status,
            errors=messages,
            **details,
        )
        for message in messages:
            print(f"error: {message}", file=sys.stderr)
        return 1

    _write_preflight_report(
        project_path,
        plan,
        modules,
        status="running",
    )
    if not _plan_confirmed(plan) and not args.force:
        return fail_preflight(
            [
                f"enhancement plan is not confirmed: {_plan_path(project_path)} "
                "(run plan, get user confirmation, set status to "
                "\"confirmed\", or pass --force)"
            ]
        )

    try:
        _validate_plan_modules(plan)
    except ValueError as exc:
        return fail_preflight(
            [str(exc)],
            plan_errors=[str(exc)],
        )

    source_delivery = audit_pptx_delivery(source_pptx)
    fatal_delivery_messages = _fatal_source_delivery_messages(source_delivery)
    if fatal_delivery_messages:
        return fail_preflight(
            fatal_delivery_messages,
            fatal_delivery_errors=fatal_delivery_messages,
            delivery_check=source_delivery,
        )

    modules_cfg = plan.get("modules") if isinstance(plan.get("modules"), dict) else {}
    timings_cfg = modules_cfg.get("timings", {})
    if not isinstance(timings_cfg, dict):
        timings_cfg = {}

    if args.narration_padding is not None:
        raw_narration_padding = args.narration_padding
    elif "narration_padding" in timings_cfg:
        raw_narration_padding = timings_cfg["narration_padding"]
    else:
        raw_narration_padding = 0.4

    try:
        if "timings" in modules:
            narration_padding = validate_seconds(
                raw_narration_padding,
                "narration padding",
                allow_zero=True,
            )
        else:
            narration_padding = 0.4
    except ValueError as exc:
        return fail_preflight([str(exc)])

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else exports_dir / f"{source_pptx.stem}_enhanced.pptx"
    )
    output_error = _output_path_error(
        project_path,
        project,
        source_pptx,
        output_path,
    )
    if output_error:
        return fail_preflight([output_error])
    if output_path.exists() and not args.overwrite:
        return fail_preflight(
            [f"output already exists, pass --overwrite: {output_path}"]
        )

    with tempfile.TemporaryDirectory(prefix="native-enhance-pptx-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(source_pptx, extract_dir)
        slides = read_slide_parts(extract_dir)

        source_errors = _source_state_errors(
            project_path,
            project,
            source_pptx,
            slides,
        )
        if source_errors:
            return fail_preflight(
                source_errors,
                source_errors=source_errors,
                delivery_check=source_delivery,
            )

        try:
            resolved_transitions = _resolve_transition_plan(
                project,
                plan,
                slides,
                cli_effect=args.transition,
                cli_duration=args.transition_duration,
                cli_apply_without_audio=args.apply_transition_without_audio,
            )
        except ValueError as exc:
            return fail_preflight(
                [str(exc)],
                transition_errors=[str(exc)],
                delivery_check=source_delivery,
            )

        readiness = _collect_material_readiness(
            slides,
            notes_dir,
            audio_dir,
            modules,
        )
        if not readiness.ready:
            return fail_preflight(
                _material_readiness_messages(readiness),
                status=(
                    "failed"
                    if readiness.module_errors
                    else "needs-materials"
                ),
                notes_required="notes" in modules,
                audio_required=(
                    "audio" in modules or "timings" in modules
                ),
                delivery_check=source_delivery,
                **_material_readiness_report_fields(readiness),
            )

        if "audio" in modules:
            existing_carriers = _native_audio_carriers(extract_dir, slides)
            if existing_carriers:
                details = "; ".join(
                    f"slide {index}: {', '.join(names)}"
                    for index, names in sorted(existing_carriers.items())
                )
                return fail_preflight(
                    [
                        "source PPTX already contains native-enhance narration "
                        "carrier(s); refusing to append duplicate audio: "
                        + details
                    ],
                    existing_native_audio_carriers=existing_carriers,
                    delivery_check=source_delivery,
                )

        note_parts: set[str] = set()
        audio_exts: set[str] = set()
        audio_count = 0
        transition_only_count = 0
        wrote_auto_advance = False
        for slide in slides:
            has_slide_transition = (
                slide.index in resolved_transitions.slide_enters
            )
            enter_update = resolved_transitions.slide_enters.get(
                slide.index,
                resolved_transitions.global_enter,
            )
            note = readiness.note_paths.get(slide.index)
            if "notes" in modules and note:
                notes_part = _apply_notes(extract_dir, slide, note)
                if notes_part is not None:
                    note_parts.add(notes_part)

            audio = readiness.audio_paths.get(slide.index)
            if "audio" in modules and audio:
                wrote_auto_advance = _apply_audio(
                    extract_dir,
                    slide,
                    audio,
                    enter=enter_update,
                    timings_enabled="timings" in modules,
                    narration_padding=narration_padding,
                    audio_duration=readiness.audio_durations.get(slide.index),
                ) or wrote_auto_advance
                audio_exts.add(audio.suffix.lower())
                audio_count += 1
                continue

            if (
                has_slide_transition
                or resolved_transitions.apply_without_audio
            ):
                transition_only_count += int(
                    _apply_transition_only(
                        extract_dir,
                        slide,
                        enter_update,
                    )
                )

        _update_content_types(extract_dir, note_parts, audio_exts)
        if wrote_auto_advance:
            set_directory_use_timings(extract_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="native-enhance-output-",
            dir=output_path.parent,
        ) as output_tmp:
            candidate_path = Path(output_tmp) / output_path.name
            _zip_dir(extract_dir, candidate_path)
            try:
                validate_pptx_transition_package(
                    candidate_path,
                    require_use_timings=wrote_auto_advance,
                )
            except ValueError as exc:
                raise RuntimeError(
                    f"PPTX transition package validation failed: {exc}"
                ) from exc
            try:
                validate_pptx_animation_package(
                    candidate_path,
                    require_supported_effects=False,
                )
            except ValueError as exc:
                raise RuntimeError(
                    f"PPTX animation/timing package validation failed: {exc}"
                ) from exc
            candidate_delivery = audit_pptx_delivery(candidate_path)
            introduced_delivery_errors = _new_delivery_errors(
                source_delivery,
                candidate_delivery,
            )
            if introduced_delivery_errors:
                raise RuntimeError(
                    "PPTX delivery postflight introduced structural error(s): "
                    + "; ".join(
                        str(issue.get("message") or issue)
                        for issue in introduced_delivery_errors
                    )
                )
            candidate_slides = candidate_delivery.get("slides")
            candidate_slide_count = (
                candidate_slides.get("count")
                if isinstance(candidate_slides, dict)
                else None
            )
            if candidate_slide_count != len(slides):
                raise RuntimeError(
                    "PPTX delivery postflight slide count changed: "
                    f"{candidate_slide_count!r} != {len(slides)}"
                )
            source_hidden_slides = _delivery_hidden_slide_indices(
                source_delivery
            )
            candidate_hidden_slides = _delivery_hidden_slide_indices(
                candidate_delivery
            )
            if (
                source_hidden_slides is None
                or candidate_hidden_slides is None
                or candidate_hidden_slides != source_hidden_slides
            ):
                raise RuntimeError(
                    "PPTX delivery postflight changed or could not verify "
                    "hidden-slide state"
                )
            candidate_path.replace(output_path)

    candidate_file = candidate_delivery.get("file")
    if isinstance(candidate_file, dict):
        candidate_file["path"] = str(output_path.resolve())
    report_status = (
        "passed-with-advisories"
        if (
            _delivery_has_findings(source_delivery)
            or _delivery_has_findings(candidate_delivery)
        )
        else "passed"
    )
    validation_dir = project_path / "validation"
    validation_dir.mkdir(exist_ok=True)
    _write_json(
        validation_dir / "report.json",
        {
            "schema": VALIDATION_SCHEMA,
            "status": report_status,
            "phase": "postflight",
            "plan_status": plan.get("status") or "missing",
            "enabled_modules": sorted(modules),
            "slide_count": len(slides),
            "applied": {
                "notes": len(note_parts),
                "audio": audio_count,
                "transition_only_slides": transition_only_count,
                "automatic_advance": wrote_auto_advance,
            },
            "transition_scope": {
                "global_enabled": "transitions" in modules,
                "global_policy": (
                    resolved_transitions.global_enter.policy
                ),
                "apply_without_audio": (
                    resolved_transitions.apply_without_audio
                ),
                "selected_slides": sorted(
                    resolved_transitions.slide_enters
                ),
            },
            "source_delivery_check": source_delivery,
            "output_delivery_check": candidate_delivery,
            "source_delivery_policy": "preserve-baseline",
            "introduced_delivery_errors": introduced_delivery_errors,
        },
    )

    print(f"Output: {output_path}", file=sys.stderr)
    print(f"Notes applied: {len(note_parts)}", file=sys.stderr)
    print(f"Audio embedded: {audio_count}", file=sys.stderr)
    if transition_only_count:
        print(f"Transition-only slides: {transition_only_count}", file=sys.stderr)
    return 0


def validate_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project_path).expanduser().resolve()
    project = _read_json(project_path / "project.json")
    if project.get("schema") not in {PROJECT_SCHEMA, *LEGACY_PROJECT_SCHEMAS}:
        print(f"error: not a native PPTX enhancement project: {project_path}", file=sys.stderr)
        return 1

    source_pptx, notes_dir, audio_dir, _exports_dir = _project_paths(project_path)
    plan = _load_enhancement_plan(project_path)
    modules = _enabled_modules(plan)
    source_delivery = audit_pptx_delivery(source_pptx)
    validation_dir = project_path / "validation"
    validation_dir.mkdir(exist_ok=True)
    fatal_delivery_messages = _fatal_source_delivery_messages(source_delivery)
    if fatal_delivery_messages:
        report = _write_preflight_report(
            project_path,
            plan,
            modules,
            status="failed",
            fatal_delivery_errors=fatal_delivery_messages,
            delivery_check=source_delivery,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    with tempfile.TemporaryDirectory(prefix="native-enhance-validate-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(source_pptx, extract_dir)
        slides = read_slide_parts(extract_dir)
        existing_carriers = (
            _native_audio_carriers(extract_dir, slides)
            if "audio" in modules
            else {}
        )

    source_errors = _source_state_errors(
        project_path,
        project,
        source_pptx,
        slides,
    )
    try:
        _validate_plan_modules(plan)
    except ValueError as exc:
        plan_errors = [str(exc)]
    else:
        plan_errors = []
    try:
        resolved_transitions = (
            _resolve_transition_plan(
                project,
                plan,
                slides,
            )
            if not plan_errors
            else None
        )
    except ValueError as exc:
        transition_errors = [str(exc)]
        transition_slide_count = 0
        transition_scope = None
    else:
        transition_errors = []
        if resolved_transitions is None:
            transition_slide_count = 0
            transition_scope = None
        else:
            transition_slide_count = len(
                resolved_transitions.slide_enters
            )
            transition_scope = {
                "global_enabled": "transitions" in modules,
                "global_policy": resolved_transitions.global_enter.policy,
                "apply_without_audio": (
                    resolved_transitions.apply_without_audio
                ),
                "selected_slides": sorted(
                    resolved_transitions.slide_enters
                ),
            }
    readiness = _collect_material_readiness(
        slides,
        notes_dir,
        audio_dir,
        modules,
    )
    hard_failure = bool(
        source_errors
        or readiness.module_errors
        or plan_errors
        or transition_errors
        or existing_carriers
    )
    if hard_failure:
        status = "failed"
    elif not readiness.ready:
        status = "needs-materials"
    else:
        status = (
            "passed-with-advisories"
            if _delivery_has_findings(source_delivery)
            else "passed"
        )
    report = _write_preflight_report(
        project_path,
        plan,
        modules,
        status=status,
        slide_count=len(slides),
        notes_required="notes" in modules,
        audio_required="audio" in modules or "timings" in modules,
        plan_errors=plan_errors,
        transition_errors=transition_errors,
        transition_override_count=transition_slide_count,
        transition_scope=transition_scope,
        source_errors=source_errors,
        existing_native_audio_carriers=existing_carriers,
        source_delivery_policy="preserve-baseline",
        delivery_check=source_delivery,
        **_material_readiness_report_fields(readiness),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if hard_failure:
        return 1
    return 0 if readiness.ready else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create/apply a native existing-PPTX enhancement project without SVG conversion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a native PPTX enhancement project")
    init.add_argument("source_pptx", help="source .pptx file")
    init.add_argument("--name", default=None, help="ASCII project name slug")
    init.add_argument("--project-dir", default=None, help="explicit project directory")
    init.add_argument("--projects-root", default="projects", help="projects root (default: projects)")
    init.add_argument(
        "--transition",
        default="fade",
        choices=[*NATIVE_TRANSITION_KEYS, *LEGACY_TRANSITION_KEYS, "none"],
        help="PowerPoint-native effect; old names are compatibility inputs",
    )
    init.add_argument("--transition-duration", type=_positive_seconds_arg, default=0.5)
    init.add_argument("--narration-padding", type=_non_negative_seconds_arg, default=0.4)
    init.add_argument(
        "--apply-transition-without-audio",
        action="store_true",
        help="draft the plan with page transitions for slides without audio",
    )
    init.set_defaults(func=init_project)

    plan = subparsers.add_parser("plan", help="draft an enhancement module plan")
    plan.add_argument("project_path", help="native enhancement project directory")
    plan.add_argument(
        "--transition",
        default=None,
        choices=[*NATIVE_TRANSITION_KEYS, *LEGACY_TRANSITION_KEYS, "none"],
        help=(
            "replace the saved global PowerPoint-native effect; omitted values "
            "preserve the current plan"
        ),
    )
    plan.add_argument(
        "--transition-duration",
        type=_positive_seconds_arg,
        default=None,
    )
    plan.add_argument(
        "--narration-padding",
        type=_non_negative_seconds_arg,
        default=None,
    )
    plan.add_argument(
        "--apply-transition-without-audio",
        action="store_true",
        default=None,
        help="include page transitions for slides without audio",
    )
    plan.set_defaults(func=plan_project)

    apply = subparsers.add_parser(
        "apply",
        help="patch confirmed notes/audio/timings/transitions into a copied PPTX",
    )
    apply.add_argument("project_path", help="native enhancement project directory")
    apply.add_argument("-o", "--output", default=None, help="output .pptx path")
    apply.add_argument("--overwrite", action="store_true", help="overwrite output if it exists")
    apply.add_argument(
        "--transition",
        default=None,
        choices=[*NATIVE_TRANSITION_KEYS, *LEGACY_TRANSITION_KEYS, "none"],
        help="PowerPoint-native effect; old names are compatibility inputs",
    )
    apply.add_argument("--transition-duration", type=_positive_seconds_arg, default=None)
    apply.add_argument("--narration-padding", type=_non_negative_seconds_arg, default=None)
    apply.add_argument("--force", action="store_true", help="apply without a confirmed enhancement plan")
    apply.add_argument(
        "--apply-transition-without-audio",
        action="store_true",
        help="also write page transitions on slides that do not have audio",
    )
    apply.set_defaults(func=apply_project)

    validate = subparsers.add_parser(
        "validate",
        help="check source integrity, plan semantics, and material readiness",
    )
    validate.add_argument("project_path", help="native enhancement project directory")
    validate.set_defaults(func=validate_project)
    return parser


def _record_preflight_exception(
    args: argparse.Namespace,
    exc: Exception,
) -> None:
    command = str(args.command)
    try:
        project_path = Path(args.project_path).expanduser().resolve()
        project = _read_json(project_path / "project.json")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as project_exc:
        if (
            project_path.is_dir()
            and (project_path / "validation").is_dir()
        ):
            try:
                _write_preflight_report(
                    project_path,
                    {},
                    set(),
                    status="failed",
                    errors=[f"{command} aborted: {exc}"],
                    project_errors=[
                        f"unable to read project.json: {project_exc}"
                    ],
                )
            except OSError:
                pass
        return
    if project.get("schema") not in {
        PROJECT_SCHEMA,
        *LEGACY_PROJECT_SCHEMAS,
    }:
        return
    plan_errors: list[str] = []
    try:
        plan = _load_enhancement_plan(project_path)
    except (OSError, ValueError, json.JSONDecodeError) as plan_exc:
        plan = {}
        plan_errors.append(f"unable to read enhancement plan: {plan_exc}")
    try:
        _write_preflight_report(
            project_path,
            plan,
            set() if plan_errors else _enabled_modules(plan),
            status="failed",
            errors=[f"{command} aborted: {exc}"],
            plan_errors=plan_errors,
        )
    except OSError:
        return


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        ET.ParseError,
    ) as exc:
        if args.command in {"apply", "validate"}:
            _record_preflight_exception(args, exc)
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
