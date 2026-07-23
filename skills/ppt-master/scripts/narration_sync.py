#!/usr/bin/env python3
"""
PPT Master - Narration Sync Tool

Rebuild click-free object timing from page-local SRT cues, then merge those
subtitles against timing values read from the final narrated PPTX.
See workflows/stages/generate-audio.md for the owning stage.

Usage:
    python3 scripts/narration_sync.py fingerprint <project_path>
    python3 scripts/narration_sync.py animations <project_path> --force
    python3 scripts/narration_sync.py subtitles <project_path> --pptx <pptx> --force
    python3 scripts/narration_sync.py subtitles <project_path> --pptx <pptx> \
        --video <powerpoint_video> --force

Examples:
    python3 scripts/narration_sync.py fingerprint projects/demo
    python3 scripts/narration_sync.py animations projects/demo --force
    python3 scripts/narration_sync.py subtitles projects/demo --pptx exports/demo.pptx --force
    python3 scripts/narration_sync.py subtitles projects/demo \
        --pptx exports/demo.pptx --video exports/demo.mp4 --force

Dependencies:
    ffprobe for animation-window validation. Optional exported-video calibration
    additionally requires ffmpeg and numpy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from pptx_transitions import read_slide_transition_xml  # noqa: E402
from svg_to_pptx.animation_config import scan_project_targets  # noqa: E402
from svg_to_pptx.pptx_package.narration import (  # noqa: E402
    NARRATION_EXTENSIONS,
    probe_audio_duration,
)

configure_utf8_stdio()


_PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DOC_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_TIMING_RE = re.compile(
    r"^(?P<start>\d+:\d{2}:\d{2},\d{3})\s+-->\s+"
    r"(?P<end>\d+:\d{2}:\d{2},\d{3})(?:\s+.*)?$"
)
_RHYTHM_RE = re.compile(r"^-\s*P(?P<page>\d+)\s*:\s*(?P<rhythm>[a-z-]+)\s*$")
_RHYTHM_PROFILES = {
    "dense": {
        "transition_duration": 0.3,
        "animation_duration": 0.35,
        "stagger": 0.18,
    },
    "anchor": {
        "transition_duration": 0.5,
        "animation_duration": 0.5,
        "stagger": 0.3,
    },
    "breathing": {
        "transition_duration": 0.5,
        "animation_duration": 0.6,
        "stagger": 0.3,
    },
}
_DEFAULT_PROFILE = {
    "transition_duration": 0.4,
    "animation_duration": 0.4,
    "stagger": 0.25,
}
_ALIGNMENT_SAMPLE_RATE = 8000
_ALIGNMENT_FINE_HZ = 1000
_ALIGNMENT_COARSE_FACTOR = 10
_ALIGNMENT_SEARCH_WINDOW_MS = 2000
_ALIGNMENT_REFINE_WINDOW_MS = 100
_ALIGNMENT_TEMPLATE_MAX_MS = 12_000
_ALIGNMENT_MIN_CORRELATION = 0.85
_ALIGNMENT_END_TOLERANCE_MS = 100


@dataclass(frozen=True)
class SubtitleCue:
    """One parsed SRT cue on a millisecond timeline."""

    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class TimingPlanEntry:
    """One ordered SVG animation target and its optional SRT cue anchor."""

    group_id: str
    cue_number: int | None


@dataclass(frozen=True)
class SubtitleMergeResult:
    """Summary of one page-local SRT merge."""

    slide_count: int
    cue_count: int
    powerpoint_timeline_ms: int
    minimum_video_adjustment_ms: int | None = None
    maximum_video_adjustment_ms: int | None = None
    minimum_video_correlation: float | None = None


def _timestamp_to_ms(value: str) -> int:
    hours_text, minutes_text, remainder = value.split(":")
    seconds_text, milliseconds_text = remainder.split(",")
    hours = int(hours_text)
    minutes = int(minutes_text)
    seconds = int(seconds_text)
    milliseconds = int(milliseconds_text)
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"Invalid SRT timestamp: {value}")
    return (((hours * 60) + minutes) * 60 + seconds) * 1000 + milliseconds


def _ms_to_timestamp(value: int) -> str:
    if value < 0:
        raise ValueError(f"SRT timestamp cannot be negative: {value}")
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _parse_srt(path: Path) -> list[SubtitleCue]:
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", text.strip())
    cues: list[SubtitleCue] = []
    previous_end = -1

    for block_number, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if len(lines) < 3:
            raise ValueError(f"{path}: malformed SRT block {block_number}")
        try:
            cue_number = int(lines[0].strip())
        except ValueError as exc:
            raise ValueError(
                f"{path}: invalid cue number in block {block_number}"
            ) from exc
        if cue_number != block_number:
            raise ValueError(
                f"{path}: cue numbers must be consecutive from 1; "
                f"block {block_number} is numbered {cue_number}"
            )
        timing_match = _TIMING_RE.match(lines[1].strip())
        if timing_match is None:
            raise ValueError(
                f"{path}: invalid cue timing in block {block_number}"
            )
        start_ms = _timestamp_to_ms(timing_match.group("start"))
        end_ms = _timestamp_to_ms(timing_match.group("end"))
        cue_text = "\n".join(lines[2:]).strip()
        if not cue_text:
            raise ValueError(f"{path}: empty cue text in block {block_number}")
        if end_ms <= start_ms:
            raise ValueError(
                f"{path}: cue {block_number} must end after it starts"
            )
        if start_ms < previous_end:
            raise ValueError(
                f"{path}: cue {block_number} overlaps the preceding cue"
            )
        cues.append(SubtitleCue(start_ms, end_ms, cue_text))
        previous_end = end_ms

    if not cues:
        raise ValueError(f"No subtitle cues found: {path}")
    return cues


def _format_srt(cues: list[SubtitleCue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n"
            f"{_ms_to_timestamp(cue.start_ms)} --> "
            f"{_ms_to_timestamp(cue.end_ms)}\n"
            f"{cue.text}"
        )
    return "\n\n".join(blocks) + "\n"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        stream = os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")
        descriptor = -1
        with stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary_path.unlink(missing_ok=True)


def _project_path(project_path: Path, value: str | None, default: Path) -> Path:
    path = Path(value) if value else default
    return path if path.is_absolute() else project_path / path


def _project_input_path(project_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_path / path


def _require_replaceable(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}; pass --force to replace it")


def _reject_output_alias(
    output_path: Path,
    input_paths: list[Path],
    *,
    label: str,
) -> None:
    output_resolved = output_path.resolve()
    for input_path in input_paths:
        if output_resolved == input_path.resolve():
            raise ValueError(
                f"{label} output must not overwrite an input file: {output_path}"
            )


def _subtitle_fingerprint(slide_names: list[str], subtitle_dir: Path) -> str:
    digest = hashlib.sha256()
    for slide_name in slide_names:
        path = subtitle_dir / f"{slide_name}.srt"
        digest.update(slide_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_timing_plan(
    path: Path,
) -> tuple[str, float, dict[str, list[TimingPlanEntry]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Narration timing plan must be a JSON object: {path}")
    unknown_top = set(raw) - {
        "version",
        "srt_sha256",
        "narration_padding",
        "slides",
    }
    if unknown_top:
        raise ValueError(
            f"Narration timing plan has unknown top-level field(s): "
            f"{', '.join(sorted(unknown_top))}"
        )
    if raw.get("version") != 1:
        raise ValueError(
            f"Unsupported narration timing plan version: {raw.get('version')!r}"
        )
    srt_sha256 = raw.get("srt_sha256")
    if (
        not isinstance(srt_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", srt_sha256) is None
    ):
        raise ValueError(
            'Narration timing plan field "srt_sha256" must be a lowercase '
            "SHA-256 digest of the ordered page-local SRT files"
        )
    narration_padding = raw.get("narration_padding")
    if (
        isinstance(narration_padding, bool)
        or not isinstance(narration_padding, (int, float))
        or not math.isfinite(float(narration_padding))
        or narration_padding < 0
    ):
        raise ValueError(
            'Narration timing plan field "narration_padding" must be a '
            "finite non-negative number"
        )
    slides = raw.get("slides")
    if not isinstance(slides, dict):
        raise ValueError('Narration timing plan field "slides" must be an object')

    result: dict[str, list[TimingPlanEntry]] = {}
    for slide_name, slide_raw in slides.items():
        if not isinstance(slide_name, str) or not slide_name:
            raise ValueError("Narration timing plan slide names must be non-empty strings")
        if not isinstance(slide_raw, dict) or set(slide_raw) != {"groups"}:
            raise ValueError(
                f'Narration timing plan slide "{slide_name}" must contain only "groups"'
            )
        groups = slide_raw["groups"]
        if not isinstance(groups, list) or not groups:
            raise ValueError(
                f'Narration timing plan slide "{slide_name}" groups must be a non-empty list'
            )

        entries: list[TimingPlanEntry] = []
        seen_groups: set[str] = set()
        for position, entry_raw in enumerate(groups, 1):
            if not isinstance(entry_raw, dict):
                raise ValueError(
                    f'Narration timing plan "{slide_name}" group #{position} '
                    "must be an object"
                )
            unknown_fields = set(entry_raw) - {"id", "cue"}
            if unknown_fields:
                raise ValueError(
                    f'Narration timing plan "{slide_name}" group #{position} '
                    f"has unknown field(s): {', '.join(sorted(unknown_fields))}"
                )
            group_id = entry_raw.get("id")
            if not isinstance(group_id, str) or not group_id.strip():
                raise ValueError(
                    f'Narration timing plan "{slide_name}" group #{position} '
                    'field "id" must be a non-empty string'
                )
            if group_id in seen_groups:
                raise ValueError(
                    f'Narration timing plan "{slide_name}" repeats group "{group_id}"'
                )
            cue_number = entry_raw.get("cue")
            if cue_number is not None and (
                isinstance(cue_number, bool)
                or not isinstance(cue_number, int)
                or cue_number <= 0
            ):
                raise ValueError(
                    f'Narration timing plan "{slide_name}/{group_id}" cue '
                    "must be a positive integer or null"
                )
            entries.append(TimingPlanEntry(group_id, cue_number))
            seen_groups.add(group_id)
        result[slide_name] = entries
    return srt_sha256, float(narration_padding), result


def _load_page_rhythms(path: Path) -> dict[int, str]:
    if not path.exists():
        return {}
    rhythms: dict[int, str] = {}
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## page_rhythm"
            continue
        if not in_section:
            continue
        match = _RHYTHM_RE.match(line.strip())
        if match is None:
            continue
        rhythms[int(match.group("page"))] = match.group("rhythm")
    return rhythms


def _profile_for_slide(
    slide_index: int,
    slide_count: int,
    rhythms: dict[int, str],
) -> dict[str, float]:
    profile = dict(_RHYTHM_PROFILES.get(rhythms.get(slide_index), _DEFAULT_PROFILE))
    if slide_index == 1:
        profile["transition_duration"] = 0.6
        profile["animation_duration"] = max(profile["animation_duration"], 0.55)
        profile["stagger"] = max(profile["stagger"], 0.3)
    if slide_index == slide_count:
        profile["transition_duration"] = 0.6
        profile["animation_duration"] = max(profile["animation_duration"], 0.65)
        profile["stagger"] = max(profile["stagger"], 0.35)
    return profile


def _find_audio(audio_dir: Path, slide_name: str) -> Path:
    matches = [
        path
        for path in audio_dir.iterdir()
        if path.is_file()
        and path.stem == slide_name
        and path.suffix.lower() in NARRATION_EXTENSIONS
    ]
    if not matches:
        raise FileNotFoundError(f"Missing narration audio for slide: {slide_name}")
    if len(matches) > 1:
        rendered = ", ".join(str(path) for path in matches)
        raise ValueError(f"Multiple narration audio files match {slide_name}: {rendered}")
    return matches[0]


def _seconds_from_ms(value: int) -> float:
    return round(value / 1000, 3)


def rebuild_animations(
    project_path: Path,
    *,
    plan_path: Path,
    subtitle_dir: Path,
    audio_dir: Path,
    output_path: Path,
    narration_padding: float,
    force: bool,
) -> tuple[int, int, int, int]:
    """Replace ``animations.json`` from the current SVG/SRT timing plan."""
    if not math.isfinite(narration_padding) or narration_padding < 0:
        raise ValueError("Narration padding must be finite and non-negative")
    _reject_output_alias(
        output_path,
        [plan_path],
        label="Animation config",
    )

    targets_by_slide, anonymous_groups = scan_project_targets(project_path)
    if anonymous_groups:
        details = "\n".join(f"- {item}" for item in anonymous_groups)
        raise ValueError(
            "Every top-level animation group must have an id before narration sync:\n"
            f"{details}"
        )
    slide_names = list(targets_by_slide)
    if not slide_names:
        raise ValueError(f"No SVG slides found under: {project_path / 'svg_output'}")

    for slide_name, targets in targets_by_slide.items():
        group_ids = [target.group_id for target in targets]
        duplicate_ids = sorted(
            group_id
            for group_id in set(group_ids)
            if group_ids.count(group_id) > 1
        )
        if duplicate_ids:
            raise ValueError(
                f'SVG slide "{slide_name}" has duplicate top-level group id(s): '
                f"{', '.join(duplicate_ids)}"
            )

    (
        expected_srt_sha256,
        planned_narration_padding,
        timing_plan,
    ) = _load_timing_plan(plan_path)
    if not math.isclose(
        narration_padding,
        planned_narration_padding,
        rel_tol=0,
        abs_tol=1e-9,
    ):
        raise ValueError(
            "Narration padding differs from the timing plan: "
            f"plan={planned_narration_padding}, command={narration_padding}"
        )
    subtitle_paths = [
        subtitle_dir / f"{slide_name}.srt"
        for slide_name in slide_names
    ]
    _reject_output_alias(
        output_path,
        subtitle_paths,
        label="Animation config",
    )
    current_srt_sha256 = _subtitle_fingerprint(slide_names, subtitle_dir)
    if current_srt_sha256 != expected_srt_sha256:
        raise ValueError(
            "Narration timing plan was authored for a different SRT set: "
            f"plan={expected_srt_sha256}, current={current_srt_sha256}; "
            "rebuild the cue mapping before regenerating animations"
        )

    expected_slides = set(slide_names)
    planned_slides = set(timing_plan)
    if expected_slides != planned_slides:
        missing = sorted(expected_slides - planned_slides)
        extra = sorted(planned_slides - expected_slides)
        details = []
        if missing:
            details.append(f"missing slide(s): {', '.join(missing)}")
        if extra:
            details.append(f"unknown slide(s): {', '.join(extra)}")
        raise ValueError("Narration timing plan does not match current SVGs: " + "; ".join(details))

    rhythms = _load_page_rhythms(project_path / "spec_lock.md")
    slides_config: dict[str, Any] = {}
    anchored_count = 0
    fallback_count = 0
    drift_warnings: list[str] = []
    audio_paths: list[Path] = []

    for slide_index, slide_name in enumerate(slide_names, 1):
        cues = _parse_srt(subtitle_dir / f"{slide_name}.srt")
        audio_path = _find_audio(audio_dir, slide_name)
        audio_paths.append(audio_path)
        audio_duration = probe_audio_duration(audio_path)
        if audio_duration is None:
            raise RuntimeError(
                f"Unable to read narration duration with ffprobe: {audio_path}"
            )

        all_targets = {target.group_id: target for target in targets_by_slide[slide_name]}
        required_groups = {
            target.group_id
            for target in targets_by_slide[slide_name]
            if not target.chrome
        }
        entries = timing_plan[slide_name]
        planned_groups = {entry.group_id for entry in entries}
        missing_groups = sorted(required_groups - planned_groups)
        if missing_groups:
            raise ValueError(
                f'Narration timing plan slide "{slide_name}" omits content group(s): '
                f"{', '.join(missing_groups)}"
            )

        for entry in entries:
            target = all_targets.get(entry.group_id)
            if target is None:
                raise ValueError(
                    f'Narration timing plan references missing group: '
                    f"{slide_name}/{entry.group_id}"
                )
            if target.structurally_static:
                raise ValueError(
                    f"Narration timing plan cannot animate structural group: "
                    f"{slide_name}/{entry.group_id}"
                )
            if entry.cue_number is not None and entry.cue_number > len(cues):
                raise ValueError(
                    f'Narration timing plan "{slide_name}/{entry.group_id}" '
                    f"references cue {entry.cue_number}, but the SRT has {len(cues)} cues"
                )

        profile = _profile_for_slide(slide_index, len(slide_names), rhythms)
        animation_duration_ms = int(profile["animation_duration"] * 1000)
        stagger_ms = int(profile["stagger"] * 1000)
        previous_end_ms = 0
        groups_config: dict[str, Any] = {}

        for order, entry in enumerate(entries, 1):
            next_entry = entries[order] if order < len(entries) else None
            effective_duration_ms = animation_duration_ms
            if (
                entry.cue_number is not None
                and next_entry is not None
                and next_entry.cue_number == entry.cue_number
            ):
                effective_duration_ms = min(animation_duration_ms, 250)

            if entry.cue_number is None:
                fallback_count += 1
                if order == 1:
                    desired_start_ms = cues[0].start_ms
                    actual_start_ms = max(desired_start_ms, previous_end_ms)
                    delay_ms = actual_start_ms - previous_end_ms
                else:
                    delay_ms = stagger_ms
                    actual_start_ms = previous_end_ms + delay_ms
            else:
                anchored_count += 1
                desired_start_ms = cues[entry.cue_number - 1].start_ms
                actual_start_ms = max(desired_start_ms, previous_end_ms)
                delay_ms = actual_start_ms - previous_end_ms
                drift_ms = actual_start_ms - desired_start_ms
                if drift_ms > 500:
                    drift_warnings.append(
                        f"{slide_name}/{entry.group_id}: cue {entry.cue_number} "
                        f"starts at {_seconds_from_ms(desired_start_ms):.3f}s, "
                        f"animation starts at {_seconds_from_ms(actual_start_ms):.3f}s "
                        f"(after-previous drift {_seconds_from_ms(drift_ms):.3f}s)"
                    )

            group_config = {
                "order": order,
                "delay": _seconds_from_ms(delay_ms),
            }
            if effective_duration_ms != animation_duration_ms:
                group_config["duration"] = _seconds_from_ms(effective_duration_ms)
            groups_config[entry.group_id] = group_config
            previous_end_ms = actual_start_ms + effective_duration_ms

        advance_ms = int((audio_duration + narration_padding) * 1000)
        if previous_end_ms > advance_ms:
            raise ValueError(
                f'Animations on slide "{slide_name}" end at '
                f"{_seconds_from_ms(previous_end_ms):.3f}s, after the recorded "
                f"slide advance at {_seconds_from_ms(advance_ms):.3f}s"
            )

        slides_config[slide_name] = {
            "transition": {
                "effect": "fade",
                "duration": profile["transition_duration"],
            },
            "animation": {
                "effect": "auto",
                "duration": profile["animation_duration"],
                "stagger": profile["stagger"],
                "trigger": "after-previous",
            },
            "groups": groups_config,
        }

    _reject_output_alias(
        output_path,
        audio_paths,
        label="Animation config",
    )
    _require_replaceable(output_path, force)
    config = {
        "version": 1,
        "defaults": {
            "transition": {"effect": "fade", "duration": 0.4},
            "animation": {
                "effect": "auto",
                "duration": 0.4,
                "stagger": 0.25,
                "trigger": "after-previous",
            },
        },
        "slides": slides_config,
    }
    _atomic_write_text(
        output_path,
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
    )

    for warning in drift_warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return len(slide_names), anchored_count + fallback_count, anchored_count, fallback_count


def _presentation_slide_members(package: zipfile.ZipFile) -> list[str]:
    try:
        presentation_root = ET.fromstring(package.read("ppt/presentation.xml"))
        relationships_root = ET.fromstring(
            package.read("ppt/_rels/presentation.xml.rels")
        )
    except KeyError as exc:
        raise ValueError(
            f"Narrated PPTX is missing presentation ordering data: {exc}"
        ) from exc

    relationship_targets: dict[str, str] = {}
    for relationship in relationships_root.iter(f"{{{_REL_NS}}}Relationship"):
        relationship_id = relationship.get("Id")
        target = relationship.get("Target")
        if (
            relationship_id
            and target
            and relationship.get("TargetMode", "Internal") != "External"
        ):
            relationship_targets[relationship_id] = target.replace("\\", "/")

    slide_list = presentation_root.find(f"{{{_PML_NS}}}sldIdLst")
    if slide_list is None:
        raise ValueError("Narrated PPTX presentation has no slide order")

    members: list[str] = []
    for slide_id in slide_list.findall(f"{{{_PML_NS}}}sldId"):
        relationship_id = slide_id.get(f"{{{_DOC_REL_NS}}}id")
        target = relationship_targets.get(relationship_id or "")
        if target is None:
            raise ValueError(
                "Narrated PPTX slide order references a missing relationship: "
                f"{relationship_id!r}"
            )
        if target.startswith("/"):
            member = posixpath.normpath(target.lstrip("/"))
        else:
            member = posixpath.normpath(posixpath.join("ppt", target))
        if member not in package.namelist():
            raise ValueError(
                f"Narrated PPTX slide relationship target is missing: {member}"
            )
        members.append(member)
    return members


def _read_powerpoint_timings(pptx_path: Path, slide_count: int) -> list[tuple[int, int]]:
    timings: list[tuple[int, int]] = []
    with zipfile.ZipFile(pptx_path) as package:
        slide_members = _presentation_slide_members(package)
        if len(slide_members) != slide_count:
            raise ValueError(
                f"Narrated PPTX has {len(slide_members)} slides, "
                f"but the project has {slide_count}"
            )
        for slide_index, member in enumerate(slide_members, 1):
            summary = read_slide_transition_xml(package.read(member))
            if summary.logical_count != 1:
                raise ValueError(
                    f"Narrated PPTX slide {slide_index} has "
                    f"{summary.logical_count} logical transition carriers"
                )
            advance_ms = summary.advance_after_ms
            if advance_ms is None:
                raise ValueError(
                    f"Narrated PPTX slide {slide_index} has no recorded advance time"
                )
            transition_ms = summary.duration_ms or 0
            if advance_ms <= 0 or transition_ms < 0:
                raise ValueError(
                    f"Narrated PPTX slide {slide_index} has invalid timing values"
                )
            timings.append((transition_ms, advance_ms))
    return timings


def _powerpoint_audio_starts(
    timings: list[tuple[int, int]],
) -> tuple[list[int], int]:
    """Return theoretical narration starts and the complete PPTX timeline."""
    audio_starts: list[int] = []
    timeline_ms = 0
    for transition_ms, advance_ms in timings:
        audio_start_ms = timeline_ms + transition_ms
        audio_starts.append(audio_start_ms)
        timeline_ms = audio_start_ms + advance_ms
    return audio_starts, timeline_ms


def _require_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Exported-video subtitle calibration requires numpy. "
            "Install it with: python3 -m pip install numpy"
        ) from exc
    return np


def _decode_audio_envelopes(path: Path, ffmpeg_path: str) -> tuple[Any, Any]:
    """Decode the first audio stream and return 1 ms and 10 ms RMS envelopes."""
    np = _require_numpy()
    command = [
        ffmpeg_path,
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(_ALIGNMENT_SAMPLE_RATE),
        "-f",
        "s16le",
        "-",
    ]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        details = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Unable to decode audio with ffmpeg: {path}\n{details}")

    samples = np.frombuffer(result.stdout, dtype="<i2")
    samples_per_frame = _ALIGNMENT_SAMPLE_RATE // _ALIGNMENT_FINE_HZ
    usable_sample_count = len(samples) // samples_per_frame * samples_per_frame
    if usable_sample_count < samples_per_frame * 500:
        raise ValueError(f"Audio is too short for subtitle calibration: {path}")

    frames = (
        samples[:usable_sample_count]
        .astype(np.float32)
        .reshape(-1, samples_per_frame)
    )
    fine = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    fine = np.log1p(120 * fine)
    smooth_width = max(1, _ALIGNMENT_FINE_HZ // 200)
    fine = np.convolve(
        fine,
        np.ones(smooth_width, dtype=np.float64) / smooth_width,
        mode="same",
    ).astype(np.float64)

    coarse_count = len(fine) // _ALIGNMENT_COARSE_FACTOR
    coarse = fine[
        :coarse_count * _ALIGNMENT_COARSE_FACTOR
    ].reshape(coarse_count, _ALIGNMENT_COARSE_FACTOR).mean(axis=1)
    return fine, coarse


def _best_correlation(search: Any, template: Any) -> tuple[int, float]:
    """Return the best normalized-correlation index for one search window."""
    np = _require_numpy()
    if len(search) < len(template):
        raise ValueError("Video alignment search window is shorter than its template")

    centered_template = template - template.mean()
    template_norm = float(np.linalg.norm(centered_template))
    if template_norm <= 1e-9:
        raise ValueError("Narration audio has no usable variation for video alignment")

    numerators = np.correlate(search, centered_template, mode="valid")
    prefix = np.concatenate(([0.0], np.cumsum(search, dtype=np.float64)))
    squared_prefix = np.concatenate(
        ([0.0], np.cumsum(search * search, dtype=np.float64))
    )
    width = len(template)
    window_sums = prefix[width:] - prefix[:-width]
    window_squared_sums = squared_prefix[width:] - squared_prefix[:-width]
    window_variances = np.maximum(
        window_squared_sums - (window_sums * window_sums / width),
        1e-18,
    )
    scores = numerators / (np.sqrt(window_variances) * template_norm)
    best_index = int(np.argmax(scores))
    return best_index, float(scores[best_index])


def _alignment_template_bounds(
    fine_envelope: Any,
    cues: list[SubtitleCue],
) -> tuple[int, int]:
    duration_ms = len(fine_envelope)
    start_ms = min(cues[0].start_ms, max(0, duration_ms - 500))
    cue_end_ms = min(cues[-1].end_ms, duration_ms)
    end_ms = min(duration_ms, start_ms + _ALIGNMENT_TEMPLATE_MAX_MS)
    end_ms = min(end_ms, max(start_ms + 1000, cue_end_ms))
    if end_ms - start_ms < 500:
        raise ValueError("Narration cue range is too short for video alignment")
    return start_ms, end_ms


def _locate_audio_start(
    video_fine: Any,
    video_coarse: Any,
    audio_fine: Any,
    audio_coarse: Any,
    cues: list[SubtitleCue],
    predicted_start_ms: int,
) -> tuple[int, float]:
    """Locate one page narration near its predicted exported-video position."""
    start_ms, end_ms = _alignment_template_bounds(audio_fine, cues)
    coarse_start = start_ms // _ALIGNMENT_COARSE_FACTOR
    coarse_end = max(
        coarse_start + 50,
        end_ms // _ALIGNMENT_COARSE_FACTOR,
    )
    coarse_template = audio_coarse[coarse_start:coarse_end]
    predicted_coarse = predicted_start_ms // _ALIGNMENT_COARSE_FACTOR
    coarse_window = _ALIGNMENT_SEARCH_WINDOW_MS // _ALIGNMENT_COARSE_FACTOR
    search_start = max(
        0,
        predicted_coarse + coarse_start - coarse_window,
    )
    search_end = min(
        len(video_coarse),
        predicted_coarse + coarse_start + coarse_window + len(coarse_template),
    )
    coarse_index, _coarse_score = _best_correlation(
        video_coarse[search_start:search_end],
        coarse_template,
    )
    coarse_audio_start_ms = (
        search_start + coarse_index - coarse_start
    ) * _ALIGNMENT_COARSE_FACTOR

    fine_template = audio_fine[start_ms:end_ms]
    fine_search_start = max(
        0,
        coarse_audio_start_ms + start_ms - _ALIGNMENT_REFINE_WINDOW_MS,
    )
    fine_search_end = min(
        len(video_fine),
        coarse_audio_start_ms
        + start_ms
        + _ALIGNMENT_REFINE_WINDOW_MS
        + len(fine_template),
    )
    fine_index, fine_score = _best_correlation(
        video_fine[fine_search_start:fine_search_end],
        fine_template,
    )
    audio_start_ms = fine_search_start + fine_index - start_ms
    return audio_start_ms, fine_score


def _align_audio_starts_to_video(
    *,
    slide_names: list[str],
    local_cues: dict[str, list[SubtitleCue]],
    theoretical_starts: list[int],
    audio_dir: Path,
    video_path: Path,
) -> tuple[list[int], list[float], list[Path]]:
    """Align every page narration to the audio track of an exported video."""
    if not video_path.is_file():
        raise FileNotFoundError(f"Exported video does not exist: {video_path}")
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError(
            "Exported-video subtitle calibration requires ffmpeg. "
            "Install ffmpeg and make it available on PATH."
        )

    video_fine, video_coarse = _decode_audio_envelopes(video_path, ffmpeg_path)
    aligned_starts: list[int] = []
    correlations: list[float] = []
    audio_paths: list[Path] = []

    for index, slide_name in enumerate(slide_names):
        audio_path = _find_audio(audio_dir, slide_name)
        audio_paths.append(audio_path)
        audio_fine, audio_coarse = _decode_audio_envelopes(audio_path, ffmpeg_path)
        if (
            local_cues[slide_name][-1].end_ms
            > len(audio_fine) + _ALIGNMENT_END_TOLERANCE_MS
        ):
            raise ValueError(
                f"{slide_name}.srt ends after its narration audio: "
                f"cue end={_seconds_from_ms(local_cues[slide_name][-1].end_ms):.3f}s, "
                f"decoded audio={_seconds_from_ms(len(audio_fine)):.3f}s"
            )
        if index == 0:
            predicted_start_ms = theoretical_starts[index]
        else:
            predicted_start_ms = (
                aligned_starts[index - 1]
                + theoretical_starts[index]
                - theoretical_starts[index - 1]
            )
        aligned_start_ms, correlation = _locate_audio_start(
            video_fine,
            video_coarse,
            audio_fine,
            audio_coarse,
            local_cues[slide_name],
            predicted_start_ms,
        )
        if correlation < _ALIGNMENT_MIN_CORRELATION:
            raise ValueError(
                f"Exported-video audio match is unreliable for {slide_name}: "
                f"correlation={correlation:.3f}, "
                f"required>={_ALIGNMENT_MIN_CORRELATION:.2f}"
            )
        if aligned_starts and aligned_start_ms <= aligned_starts[-1]:
            raise ValueError(
                f"Exported-video audio order is invalid at slide {slide_name}"
            )
        final_cue_end_ms = (
            aligned_start_ms + local_cues[slide_name][-1].end_ms
        )
        if (
            final_cue_end_ms
            > len(video_fine) + _ALIGNMENT_END_TOLERANCE_MS
        ):
            raise ValueError(
                f"Exported video ends before the final cue on slide {slide_name}: "
                f"cue end={_seconds_from_ms(final_cue_end_ms):.3f}s, "
                f"decoded video audio={_seconds_from_ms(len(video_fine)):.3f}s"
            )
        aligned_starts.append(aligned_start_ms)
        correlations.append(correlation)

    return aligned_starts, correlations, audio_paths


def _merge_subtitles_result(
    project_path: Path,
    *,
    pptx_path: Path,
    subtitle_dir: Path,
    output_path: Path,
    force: bool,
    audio_dir: Path | None = None,
    video_path: Path | None = None,
) -> SubtitleMergeResult:
    """Merge local SRT files on the PPTX or exported-video timeline."""
    targets_by_slide, _anonymous_groups = scan_project_targets(project_path)
    slide_names = list(targets_by_slide)
    if not slide_names:
        raise ValueError(f"No SVG slides found under: {project_path / 'svg_output'}")

    local_subtitle_paths = [
        subtitle_dir / f"{slide_name}.srt"
        for slide_name in slide_names
    ]
    _reject_output_alias(
        output_path,
        [pptx_path, *local_subtitle_paths, *([video_path] if video_path else [])],
        label="Merged subtitle",
    )
    _require_replaceable(output_path, force)
    timings = _read_powerpoint_timings(pptx_path, len(slide_names))
    theoretical_starts, timeline_ms = _powerpoint_audio_starts(timings)
    local_cues = {
        slide_name: _parse_srt(subtitle_dir / f"{slide_name}.srt")
        for slide_name in slide_names
    }
    video_adjustments: list[int] = []
    correlations: list[float] = []

    if video_path is None:
        audio_starts = theoretical_starts
    else:
        resolved_audio_dir = audio_dir or project_path / "audio"
        audio_starts, correlations, audio_paths = _align_audio_starts_to_video(
            slide_names=slide_names,
            local_cues=local_cues,
            theoretical_starts=theoretical_starts,
            audio_dir=resolved_audio_dir,
            video_path=video_path,
        )
        _reject_output_alias(
            output_path,
            audio_paths,
            label="Merged subtitle",
        )
        video_adjustments = [
            actual - theoretical
            for actual, theoretical in zip(audio_starts, theoretical_starts)
        ]

    merged_cues: list[SubtitleCue] = []

    for slide_name, audio_start_ms, (_transition_ms, advance_ms) in zip(
        slide_names,
        audio_starts,
        timings,
    ):
        slide_cues = local_cues[slide_name]
        if slide_cues[-1].end_ms > advance_ms:
            raise ValueError(
                f"{slide_name}.srt ends at "
                f"{_seconds_from_ms(slide_cues[-1].end_ms):.3f}s, after the "
                f"PowerPoint slide advance at {_seconds_from_ms(advance_ms):.3f}s"
            )
        for cue in slide_cues:
            merged_cue = SubtitleCue(
                cue.start_ms + audio_start_ms,
                cue.end_ms + audio_start_ms,
                cue.text,
            )
            if merged_cues and merged_cue.start_ms < merged_cues[-1].end_ms:
                raise ValueError(
                    f"Video-calibrated subtitle overlap before slide {slide_name}"
                )
            merged_cues.append(merged_cue)

    _atomic_write_text(output_path, _format_srt(merged_cues))
    return SubtitleMergeResult(
        slide_count=len(slide_names),
        cue_count=len(merged_cues),
        powerpoint_timeline_ms=timeline_ms,
        minimum_video_adjustment_ms=(
            min(video_adjustments) if video_adjustments else None
        ),
        maximum_video_adjustment_ms=(
            max(video_adjustments) if video_adjustments else None
        ),
        minimum_video_correlation=(
            min(correlations) if correlations else None
        ),
    )


def merge_subtitles(
    project_path: Path,
    *,
    pptx_path: Path,
    subtitle_dir: Path,
    output_path: Path,
    force: bool,
) -> tuple[int, int, int]:
    """Merge local SRT files using timing values read from the final PPTX."""
    result = _merge_subtitles_result(
        project_path,
        pptx_path=pptx_path,
        subtitle_dir=subtitle_dir,
        output_path=output_path,
        force=force,
    )
    return (
        result.slide_count,
        result.cue_count,
        result.powerpoint_timeline_ms,
    )


def merge_subtitles_to_video(
    project_path: Path,
    *,
    pptx_path: Path,
    subtitle_dir: Path,
    audio_dir: Path,
    video_path: Path,
    output_path: Path,
    force: bool,
) -> SubtitleMergeResult:
    """Merge local SRT files after calibrating page starts to an exported video."""
    return _merge_subtitles_result(
        project_path,
        pptx_path=pptx_path,
        subtitle_dir=subtitle_dir,
        output_path=output_path,
        force=force,
        audio_dir=audio_dir,
        video_path=video_path,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild narrated object animation timings and merge page-local "
            "SRT files on PowerPoint's final timeline."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fingerprint = subparsers.add_parser(
        "fingerprint",
        help="print the SHA-256 used to bind a timing plan to page-local SRT files",
    )
    fingerprint.add_argument("project_path", help="Project directory")
    fingerprint.add_argument(
        "--subtitle-dir",
        default=None,
        help="Page-local SRT directory; default: <project>/notes/subtitles",
    )

    animations = subparsers.add_parser(
        "animations",
        help="replace animations.json from narration_timing.json and page-local SRT",
    )
    animations.add_argument("project_path", help="Project directory")
    animations.add_argument(
        "--plan",
        default=None,
        help="Timing plan; default: <project>/narration_timing.json",
    )
    animations.add_argument(
        "--subtitle-dir",
        default=None,
        help="Page-local SRT directory; default: <project>/notes/subtitles",
    )
    animations.add_argument(
        "--audio-dir",
        default=None,
        help="Narration audio directory; default: <project>/audio",
    )
    animations.add_argument(
        "-o",
        "--output",
        default=None,
        help="Animation config output; default: <project>/animations.json",
    )
    animations.add_argument(
        "--narration-padding",
        type=float,
        default=0.5,
        help="Seconds added after each narration before slide advance (default: 0.5)",
    )
    animations.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing animations.json",
    )

    subtitles = subparsers.add_parser(
        "subtitles",
        help="merge page-local SRT using timings read from a narrated PPTX",
    )
    subtitles.add_argument("project_path", help="Project directory")
    subtitles.add_argument(
        "--pptx",
        required=True,
        help=(
            "Final narrated PPTX whose recorded timing values define the "
            "timeline; relative paths are resolved under the project"
        ),
    )
    subtitles.add_argument(
        "--subtitle-dir",
        default=None,
        help="Page-local SRT directory; default: <project>/notes/subtitles",
    )
    subtitles.add_argument(
        "--video",
        default=None,
        help=(
            "PowerPoint-exported video whose audio track calibrates page starts; "
            "relative paths are resolved under the project"
        ),
    )
    subtitles.add_argument(
        "--audio-dir",
        default=None,
        help=(
            "Page-local narration audio used with --video; "
            "default: <project>/audio"
        ),
    )
    subtitles.add_argument(
        "-o",
        "--output",
        default=None,
        help="Merged SRT output; default: <project>/notes/subtitles/total.srt",
    )
    subtitles.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing merged SRT",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        parser.error(f"Project path does not exist: {project_path}")

    try:
        if args.command == "fingerprint":
            subtitle_dir = _project_path(
                project_path,
                args.subtitle_dir,
                Path("notes/subtitles"),
            )
            targets_by_slide, _anonymous_groups = scan_project_targets(project_path)
            slide_names = list(targets_by_slide)
            if not slide_names:
                raise ValueError(
                    f"No SVG slides found under: {project_path / 'svg_output'}"
                )
            for slide_name in slide_names:
                _parse_srt(subtitle_dir / f"{slide_name}.srt")
            print(_subtitle_fingerprint(slide_names, subtitle_dir))
            return 0

        if args.command == "animations":
            plan_path = _project_path(
                project_path,
                args.plan,
                Path("narration_timing.json"),
            )
            subtitle_dir = _project_path(
                project_path,
                args.subtitle_dir,
                Path("notes/subtitles"),
            )
            audio_dir = _project_path(
                project_path,
                args.audio_dir,
                Path("audio"),
            )
            output_path = _project_path(
                project_path,
                args.output,
                Path("animations.json"),
            )
            slide_count, group_count, anchored_count, fallback_count = rebuild_animations(
                project_path,
                plan_path=plan_path,
                subtitle_dir=subtitle_dir,
                audio_dir=audio_dir,
                output_path=output_path,
                narration_padding=args.narration_padding,
                force=args.force,
            )
            print(f"Animation config rebuilt: {output_path}")
            print(
                f"Slides: {slide_count}; groups: {group_count}; "
                f"SRT-anchored: {anchored_count}; sequential fallback: {fallback_count}"
            )
            return 0

        pptx_path = _project_input_path(project_path, args.pptx).resolve()
        subtitle_dir = _project_path(
            project_path,
            args.subtitle_dir,
            Path("notes/subtitles"),
        )
        audio_dir = _project_path(
            project_path,
            args.audio_dir,
            Path("audio"),
        )
        video_path = (
            _project_input_path(project_path, args.video).resolve()
            if args.video
            else None
        )
        output_path = _project_path(
            project_path,
            args.output,
            Path("notes/subtitles/total.srt"),
        )
        result = _merge_subtitles_result(
            project_path,
            pptx_path=pptx_path,
            subtitle_dir=subtitle_dir,
            audio_dir=audio_dir,
            video_path=video_path,
            output_path=output_path,
            force=args.force,
        )
        print(f"Merged subtitle written: {output_path}")
        print(
            f"Slides: {result.slide_count}; cues: {result.cue_count}; "
            "PowerPoint timeline: "
            f"{_seconds_from_ms(result.powerpoint_timeline_ms):.3f}s"
        )
        if result.minimum_video_correlation is not None:
            print(
                "Exported-video calibration: page adjustment "
                f"{_seconds_from_ms(result.minimum_video_adjustment_ms or 0):+.3f}s "
                "to "
                f"{_seconds_from_ms(result.maximum_video_adjustment_ms or 0):+.3f}s; "
                f"minimum correlation: {result.minimum_video_correlation:.3f}"
            )
        return 0
    except (
        ET.ParseError,
        OSError,
        OverflowError,
        ValueError,
        RuntimeError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
