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

Examples:
    python3 scripts/narration_sync.py fingerprint projects/demo
    python3 scripts/narration_sync.py animations projects/demo --force
    python3 scripts/narration_sync.py subtitles projects/demo --pptx exports/demo.pptx --force

Dependencies:
    ffprobe for animation-window validation; otherwise standard library and
    PPT Master's local SVG/PPTX helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import posixpath
import re
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


def merge_subtitles(
    project_path: Path,
    *,
    pptx_path: Path,
    subtitle_dir: Path,
    output_path: Path,
    force: bool,
) -> tuple[int, int, int]:
    """Merge local SRT files using timing values read from the final PPTX."""
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
        [pptx_path, *local_subtitle_paths],
        label="Merged subtitle",
    )
    _require_replaceable(output_path, force)
    timings = _read_powerpoint_timings(pptx_path, len(slide_names))
    merged_cues: list[SubtitleCue] = []
    timeline_ms = 0

    for slide_name, (transition_ms, advance_ms) in zip(slide_names, timings):
        local_cues = _parse_srt(subtitle_dir / f"{slide_name}.srt")
        if local_cues[-1].end_ms > advance_ms:
            raise ValueError(
                f"{slide_name}.srt ends at "
                f"{_seconds_from_ms(local_cues[-1].end_ms):.3f}s, after the "
                f"PowerPoint slide advance at {_seconds_from_ms(advance_ms):.3f}s"
            )
        audio_start_ms = timeline_ms + transition_ms
        merged_cues.extend(
            SubtitleCue(
                cue.start_ms + audio_start_ms,
                cue.end_ms + audio_start_ms,
                cue.text,
            )
            for cue in local_cues
        )
        timeline_ms = audio_start_ms + advance_ms

    _atomic_write_text(output_path, _format_srt(merged_cues))
    return len(slide_names), len(merged_cues), timeline_ms


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
        output_path = _project_path(
            project_path,
            args.output,
            Path("notes/subtitles/total.srt"),
        )
        slide_count, cue_count, timeline_ms = merge_subtitles(
            project_path,
            pptx_path=pptx_path,
            subtitle_dir=subtitle_dir,
            output_path=output_path,
            force=args.force,
        )
        print(f"Merged subtitle written: {output_path}")
        print(
            f"Slides: {slide_count}; cues: {cue_count}; "
            f"PowerPoint timeline: {_seconds_from_ms(timeline_ms):.3f}s"
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
