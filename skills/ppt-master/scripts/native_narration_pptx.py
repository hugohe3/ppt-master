#!/usr/bin/env python3
"""
PPT Master - Native Existing PPTX Enhancer

Create and apply a lightweight project for enhancing an existing PPTX without
entering the SVG generation pipeline or modifying the original file.

V1 enhancement modules: speaker notes, narration audio, slide auto-advance
timings, and optional page transitions.

Usage:
    python3 scripts/native_enhance_pptx.py init <source.pptx> [--name project_name]
    python3 scripts/native_enhance_pptx.py apply <project_path> [--output output.pptx]
    python3 scripts/native_enhance_pptx.py validate <project_path>

Examples:
    python3 scripts/native_enhance_pptx.py init projects/source.pptx --name fire_station
    python3 scripts/native_enhance_pptx.py apply projects/fire_station_native_enhance_20260626
    python3 scripts/native_enhance_pptx.py validate projects/fire_station_native_enhance_20260626

Dependencies:
    ffprobe for audio-duration-based auto-advance timings.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from pptx_animations import (  # noqa: E402
    object_animation_fingerprint,
    validate_pptx_animation_package,
)
from pptx_transitions import (  # noqa: E402
    AdvanceUpdate,
    EnterUpdate,
    TRANSITIONS,
    apply_slide_motion_xml,
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
LEGACY_PROJECT_SCHEMAS = {"native_narration_pptx_project.v1"}
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


@dataclass(frozen=True)
class SlidePart:
    index: int
    part_name: str
    slide_number: int


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
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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


def _remove_relationships_by_type(rels_path: Path, rel_type: str) -> None:
    if not rels_path.exists():
        return
    content = rels_path.read_text(encoding="utf-8")
    content = re.sub(
        rf'\s*<Relationship\b[^>]*\bType="{re.escape(rel_type)}"[^>]*/>',
        "",
        content,
    )
    rels_path.write_text(content, encoding="utf-8")


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


def _add_override(content_types: str, part_name: str, content_type: str) -> str:
    if re.search(
        rf'<Override\b[^>]*\bPartName="/{re.escape(part_name)}"[^>]*/>',
        content_types,
    ):
        return content_types
    override = f'  <Override PartName="/{part_name}" ContentType="{content_type}"/>'
    return content_types.replace("</Types>", override + "\n</Types>")


def _add_notes_content_types(content_types: str, note_indices: set[int]) -> str:
    content_types = _add_override(content_types, "ppt/theme/theme2.xml", CONTENT_TYPE_THEME)
    content_types = _add_override(
        content_types,
        "ppt/notesMasters/notesMaster1.xml",
        CONTENT_TYPE_NOTES_MASTER,
    )
    for index in sorted(note_indices):
        content_types = _add_override(
            content_types,
            f"ppt/notesSlides/notesSlide{index}.xml",
            CONTENT_TYPE_NOTES_SLIDE,
        )
    return content_types


def _apply_notes(extract_dir: Path, slide: SlidePart, note_md: Path) -> None:
    notes_text = markdown_to_plain_text(note_md.read_text(encoding="utf-8"))
    if not notes_text:
        return

    _ensure_notes_master(extract_dir)
    notes_dir = extract_dir / "ppt" / "notesSlides"
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_xml_path = notes_dir / f"notesSlide{slide.index}.xml"
    notes_xml_path.write_text(
        create_notes_slide_xml(slide.slide_number, notes_text),
        encoding="utf-8",
    )

    notes_rels_dir = notes_dir / "_rels"
    notes_rels_dir.mkdir(parents=True, exist_ok=True)
    notes_rels_path = notes_rels_dir / f"notesSlide{slide.index}.xml.rels"
    notes_rels_path.write_text(
        create_notes_slide_rels_xml(slide.slide_number),
        encoding="utf-8",
    )

    slide_rels = _relationship_file_for_part(extract_dir, slide.part_name)
    _ensure_rels_file(slide_rels)
    _remove_relationships_by_type(slide_rels, NOTES_REL_TYPE)
    _append_relationship(
        slide_rels,
        NOTES_REL_TYPE,
        f"../notesSlides/notesSlide{slide.index}.xml",
    )


def _apply_audio(
    extract_dir: Path,
    slide: SlidePart,
    audio_path: Path,
    *,
    enter: EnterUpdate,
    timings_enabled: bool,
    narration_padding: float,
) -> bool:
    media_dir = extract_dir / "ppt" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    ext = audio_path.suffix.lower()
    media_name = f"native_enhance_audio_{slide.index:03d}{ext}"
    shutil.copy2(audio_path, media_dir / media_name)

    poster_name = "native_enhance_audio_poster.png"
    poster_path = media_dir / poster_name
    if not poster_path.exists():
        poster_path.write_bytes(AUDIO_MARKER_PNG_BYTES)

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


def _update_content_types(extract_dir: Path, note_indices: set[int], audio_exts: set[str]) -> None:
    content_types_path = extract_dir / "[Content_Types].xml"
    content_types = content_types_path.read_text(encoding="utf-8")
    if note_indices:
        content_types = _add_notes_content_types(content_types, note_indices)
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
        return {"notes", "audio", "timings", "transitions"}
    enabled: set[str] = set()
    for name, config in modules.items():
        if isinstance(config, dict) and config.get("enabled") is True:
            enabled.add(str(name))
    return enabled


def _resolve_enter_update(
    *,
    cli_effect: str | None,
    configured_effect: object,
    transitions_enabled: bool,
    duration: float,
) -> EnterUpdate:
    if cli_effect is None and not transitions_enabled:
        if configured_effect == "none":
            return EnterUpdate(policy="none", effect=None, duration=duration)
        return EnterUpdate(policy="preserve", duration=duration)

    effect = cli_effect if cli_effect is not None else configured_effect
    if not isinstance(effect, str):
        raise ValueError(f"transition effect must be a string: {effect!r}")
    if effect == "none":
        return EnterUpdate(policy="none", effect=None, duration=duration)
    if effect not in TRANSITIONS:
        valid = ", ".join(sorted(TRANSITIONS))
        raise ValueError(
            f"unknown transition effect {effect!r}; valid effects: {valid}, none"
        )

    return EnterUpdate(policy="replace", effect=effect, duration=duration)


def _plan_confirmed(plan: dict) -> bool:
    return plan.get("status") == "confirmed"


def _build_enhancement_plan(
    project: dict,
    *,
    slide_count: int,
    notes_count: int,
    audio_count: int,
    transition: str,
    transition_duration: float,
    narration_padding: float,
    apply_transition_without_audio: bool,
) -> dict:
    return {
        "schema": "native_pptx_enhancement_plan.v1",
        "status": "draft",
        "source_pptx": project.get("source_pptx"),
        "slide_count": slide_count,
        "modules": {
            "notes": {
                "enabled": True,
                "requires_confirmation": True,
                "status": "ready" if notes_count == slide_count else "needs_notes",
                "coverage": {"ready": notes_count, "total": slide_count},
            },
            "audio": {
                "enabled": True,
                "requires_confirmation": True,
                "status": "ready" if audio_count == slide_count else "needs_audio",
                "coverage": {"ready": audio_count, "total": slide_count},
            },
            "timings": {
                "enabled": True,
                "requires_confirmation": True,
                "status": "ready" if audio_count == slide_count else "blocked_until_audio",
                "source": "audio_duration",
                "narration_padding": narration_padding,
            },
            "transitions": {
                "enabled": transition != "none",
                "requires_confirmation": True,
                "status": "ready",
                "effect": transition,
                "duration": transition_duration,
                "apply_without_audio": apply_transition_without_audio,
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


def init_project(args: argparse.Namespace) -> int:
    source_pptx = Path(args.source_pptx).expanduser().resolve()
    if not source_pptx.exists() or source_pptx.suffix.lower() != ".pptx":
        print(f"error: expected an existing .pptx file: {source_pptx}", file=sys.stderr)
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
        "modules": ["notes", "audio", "timings", "transitions"],
        "source_pptx": f"sources/{source_pptx.name}",
        "source_markdown": f"sources/{source_pptx.stem}.md",
        "source_import": {
            "mode": source_import_mode,
            "original_path": str(source_pptx),
        },
        "slide_count": len(slide_parts),
        "notes_dir": "notes",
        "audio_dir": "audio",
        "exports_dir": "exports",
        "transition": {
            "effect": args.transition,
            "duration": args.transition_duration,
        },
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
    with tempfile.TemporaryDirectory(prefix="native-enhance-plan-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(source_pptx, extract_dir)
        slides = read_slide_parts(extract_dir)

    notes_count = sum(1 for slide in slides if _note_path(notes_dir, slide.index) is not None)
    audio_count = sum(1 for slide in slides if _audio_path(audio_dir, slide.index) is not None)
    plan = _build_enhancement_plan(
        project,
        slide_count=len(slides),
        notes_count=notes_count,
        audio_count=audio_count,
        transition=args.transition,
        transition_duration=args.transition_duration,
        narration_padding=args.narration_padding,
        apply_transition_without_audio=args.apply_transition_without_audio,
    )
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
    transition_cfg = project.get("transition", {}) if isinstance(project.get("transition"), dict) else {}
    plan = _load_enhancement_plan(project_path)
    if not _plan_confirmed(plan) and not args.force:
        print(
            f"error: enhancement plan is not confirmed: {_plan_path(project_path)} "
            "(run plan, get user confirmation, set status to \"confirmed\", or pass --force)",
            file=sys.stderr,
        )
        return 1

    modules = _enabled_modules(plan)
    modules_cfg = plan.get("modules") if isinstance(plan.get("modules"), dict) else {}
    transitions_cfg = modules_cfg.get("transitions", {})
    if not isinstance(transitions_cfg, dict):
        transitions_cfg = {}
    timings_cfg = modules_cfg.get("timings", {})
    if not isinstance(timings_cfg, dict):
        timings_cfg = {}

    if "effect" in transitions_cfg:
        configured_effect = transitions_cfg["effect"]
    elif "effect" in transition_cfg:
        configured_effect = transition_cfg["effect"]
    else:
        configured_effect = "fade"

    if args.transition_duration is not None:
        raw_transition_duration = args.transition_duration
    elif "duration" in transitions_cfg:
        raw_transition_duration = transitions_cfg["duration"]
    elif "duration" in transition_cfg:
        raw_transition_duration = transition_cfg["duration"]
    else:
        raw_transition_duration = 0.5

    if args.narration_padding is not None:
        raw_narration_padding = args.narration_padding
    elif "narration_padding" in timings_cfg:
        raw_narration_padding = timings_cfg["narration_padding"]
    else:
        raw_narration_padding = 0.4

    try:
        if args.transition is not None or "transitions" in modules:
            transition_duration = validate_seconds(
                raw_transition_duration,
                "transition duration",
                allow_zero=False,
            )
        else:
            transition_duration = 0.5
        if "timings" in modules:
            narration_padding = validate_seconds(
                raw_narration_padding,
                "narration padding",
                allow_zero=True,
            )
        else:
            narration_padding = 0.4
        enter_update = _resolve_enter_update(
            cli_effect=args.transition,
            configured_effect=configured_effect,
            transitions_enabled="transitions" in modules,
            duration=transition_duration,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    apply_transition_without_audio = (
        args.apply_transition_without_audio
        or bool(transitions_cfg.get("apply_without_audio"))
    )

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else exports_dir / f"{source_pptx.stem}_enhanced.pptx"
    )
    if output_path.exists() and not args.overwrite:
        print(f"error: output already exists, pass --overwrite: {output_path}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="native-enhance-pptx-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(source_pptx, extract_dir)
        slides = read_slide_parts(extract_dir)

        note_indices: set[int] = set()
        audio_exts: set[str] = set()
        audio_count = 0
        transition_only_count = 0
        wrote_auto_advance = False
        for slide in slides:
            note = _note_path(notes_dir, slide.index)
            if "notes" in modules and note:
                _apply_notes(extract_dir, slide, note)
                note_indices.add(slide.index)

            audio = _audio_path(audio_dir, slide.index)
            if "audio" in modules and audio:
                wrote_auto_advance = _apply_audio(
                    extract_dir,
                    slide,
                    audio,
                    enter=enter_update,
                    timings_enabled="timings" in modules,
                    narration_padding=narration_padding,
                ) or wrote_auto_advance
                audio_exts.add(audio.suffix.lower())
                audio_count += 1
                continue

            if (
                apply_transition_without_audio
                and enter_update.policy != "preserve"
            ):
                slide_xml_path = extract_dir / slide.part_name
                slide_xml = slide_xml_path.read_text(encoding="utf-8")
                source_animation_fingerprint = object_animation_fingerprint(
                    slide_xml
                )
                slide_xml, _uses_timings = apply_slide_motion_xml(
                    slide_xml,
                    enter=enter_update,
                    advance=AdvanceUpdate(mode="preserve"),
                )
                if (
                    object_animation_fingerprint(slide_xml)
                    != source_animation_fingerprint
                ):
                    raise RuntimeError(
                        f"Slide {slide.index} object animations changed while "
                        "updating the transition"
                    )
                slide_xml_path.write_text(
                    slide_xml,
                    encoding="utf-8",
                )
                transition_only_count += 1

        _update_content_types(extract_dir, note_indices, audio_exts)
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
            candidate_path.replace(output_path)

    print(f"Output: {output_path}", file=sys.stderr)
    print(f"Notes applied: {len(note_indices)}", file=sys.stderr)
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
    with tempfile.TemporaryDirectory(prefix="native-enhance-validate-") as tmp:
        extract_dir = Path(tmp) / "pptx"
        _extract_pptx(source_pptx, extract_dir)
        slides = read_slide_parts(extract_dir)

    plan = _load_enhancement_plan(project_path)
    modules = _enabled_modules(plan)
    notes_count = sum(1 for slide in slides if _note_path(notes_dir, slide.index) is not None)
    audio_count = sum(1 for slide in slides if _audio_path(audio_dir, slide.index) is not None)
    missing_notes = (
        [slide.index for slide in slides if _note_path(notes_dir, slide.index) is None]
        if "notes" in modules
        else []
    )
    missing_audio = (
        [slide.index for slide in slides if _audio_path(audio_dir, slide.index) is None]
        if "audio" in modules
        else []
    )
    report = {
        "schema": "native_pptx_enhancement_validation.v1",
        "slide_count": len(slides),
        "plan_status": plan.get("status") or "missing",
        "enabled_modules": sorted(modules),
        "notes_required": "notes" in modules,
        "audio_required": "audio" in modules,
        "notes_count": notes_count,
        "audio_count": audio_count,
        "missing_notes": missing_notes,
        "missing_audio": missing_audio,
    }
    validation_dir = project_path / "validation"
    validation_dir.mkdir(exist_ok=True)
    _write_json(validation_dir / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not missing_notes and not missing_audio else 2


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
    init.add_argument("--transition", default="fade", choices=sorted(TRANSITIONS.keys()))
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
    plan.add_argument("--transition", default="fade", choices=sorted(TRANSITIONS.keys()) + ["none"])
    plan.add_argument("--transition-duration", type=_positive_seconds_arg, default=0.5)
    plan.add_argument("--narration-padding", type=_non_negative_seconds_arg, default=0.4)
    plan.add_argument(
        "--apply-transition-without-audio",
        action="store_true",
        help="include page transitions for slides without audio",
    )
    plan.set_defaults(func=plan_project)

    apply = subparsers.add_parser("apply", help="patch notes/audio/timings into a copied PPTX")
    apply.add_argument("project_path", help="native narration project directory")
    apply.add_argument("-o", "--output", default=None, help="output .pptx path")
    apply.add_argument("--overwrite", action="store_true", help="overwrite output if it exists")
    apply.add_argument("--transition", default=None, choices=sorted(TRANSITIONS.keys()) + ["none"])
    apply.add_argument("--transition-duration", type=_positive_seconds_arg, default=None)
    apply.add_argument("--narration-padding", type=_non_negative_seconds_arg, default=None)
    apply.add_argument("--force", action="store_true", help="apply without a confirmed enhancement plan")
    apply.add_argument(
        "--apply-transition-without-audio",
        action="store_true",
        help="also write page transitions on slides that do not have audio",
    )
    apply.set_defaults(func=apply_project)

    validate = subparsers.add_parser("validate", help="check notes/audio coverage")
    validate.add_argument("project_path", help="native narration project directory")
    validate.set_defaults(func=validate_project)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
