#!/usr/bin/env python3
"""
PPT Master - Narration Sync Tool

Derive click-free narration timing from the canonical animation config and
page-local SRT cues, then merge those subtitles against timing values read
from the final narrated PPTX.
See workflows/stages/generate-audio.md for the owning stage.

Usage:
    python3 scripts/narration_sync.py fingerprint <project_path>
    python3 scripts/narration_sync.py animations <project_path>
    python3 scripts/narration_sync.py subtitles <project_path> --pptx <pptx> --force
    python3 scripts/narration_sync.py subtitles <project_path> --pptx <pptx> \
        --video <powerpoint_video> --force

Examples:
    python3 scripts/narration_sync.py fingerprint projects/demo
    python3 scripts/narration_sync.py animations projects/demo
    python3 scripts/narration_sync.py subtitles projects/demo --pptx exports/demo.pptx --force
    python3 scripts/narration_sync.py subtitles projects/demo \
        --pptx exports/demo.pptx --video exports/demo.mp4 --force

Dependencies:
    ffprobe for animation-window validation. Optional exported-video calibration
    additionally requires ffmpeg and numpy.
"""

from __future__ import annotations

import argparse
import copy
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
from pptx_animations import (  # noqa: E402
    animation_seconds_to_milliseconds,
    normalize_animation_effect,
)
from pptx_transitions import read_slide_transition_xml  # noqa: E402
from svg_to_pptx.animation_config import (  # noqa: E402
    scan_project_targets,
    scan_svg_targets,
    validate_animation_config_errors,
    validate_transition_config,
)
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
    """One ordered animation target and its optional SRT cue anchor."""

    group_id: str
    cue_number: int | None


@dataclass(frozen=True)
class AnimationGroupState:
    """One effective canonical animation row before narration timing."""

    group_id: str
    order: int
    source_index: int
    duration_ms: int
    original_delay_ms: int


@dataclass(frozen=True)
class SlideAnimationSettings:
    """Effective animation settings inherited by one slide."""

    effect: str | None
    duration_ms: int
    stagger_ms: int
    trigger: str


@dataclass(frozen=True)
class AnimationBuildResult:
    """Summary of one narration animation derivation."""

    slide_count: int
    group_count: int
    anchored_count: int
    fallback_count: int
    ignored_cue_count: int
    svg_fallback_slide_count: int
    timing_plan_written: bool


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
        if not isinstance(groups, list):
            raise ValueError(
                f'Narration timing plan slide "{slide_name}" groups must be a list'
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


def _load_canonical_animation_config(path: Path) -> dict[str, Any]:
    """Load and field-validate the read-only canonical animation sidecar."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Canonical animation config is missing: {path}. "
            "Complete the customize-animations stage first; narration sync "
            "does not create or replace animations.json."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Canonical animation config must be a JSON object: {path}")
    if raw.get("version", 1) != 1:
        raise ValueError(
            f"Unsupported canonical animation config version: {raw.get('version')!r}"
        )
    errors = list(
        dict.fromkeys(
            [
                *validate_transition_config(raw),
                *validate_animation_config_errors(raw),
            ]
        )
    )
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(
            f"Canonical animation config is invalid: {path}\n{details}"
        )
    return raw


def _page_subtitle_names(subtitle_dir: Path) -> list[str]:
    """Return ordered page-local SRT stems, excluding the merged sidecar."""
    if not subtitle_dir.is_dir():
        raise FileNotFoundError(f"Page-local SRT directory not found: {subtitle_dir}")
    names = [
        path.stem
        for path in sorted(subtitle_dir.glob("*.srt"))
        if path.stem != "total"
    ]
    if not names:
        raise FileNotFoundError(f"No page-local SRT files found under: {subtitle_dir}")
    return names


def _animation_slide_names(
    project_path: Path,
    config: dict[str, Any],
    subtitle_dir: Path,
) -> list[str]:
    """Resolve the page roster without parsing SVG unless a slide is missing."""
    slides = config.get("slides", {})
    if not isinstance(slides, dict):
        raise ValueError('Canonical animations.json field "slides" must be an object')
    canonical_names = list(slides)
    subtitle_names = _page_subtitle_names(subtitle_dir)
    subtitle_set = set(subtitle_names)

    missing_subtitles = [
        slide_name for slide_name in canonical_names if slide_name not in subtitle_set
    ]
    if missing_subtitles:
        raise FileNotFoundError(
            "Missing page-local SRT for canonical animation slide(s): "
            + ", ".join(missing_subtitles)
        )

    canonical_set = set(canonical_names)
    extra_subtitles = [
        slide_name for slide_name in subtitle_names if slide_name not in canonical_set
    ]
    unexpected = [
        slide_name
        for slide_name in extra_subtitles
        if not (project_path / "svg_output" / f"{slide_name}.svg").is_file()
    ]
    if unexpected:
        raise ValueError(
            "Page-local SRT has no matching canonical animation slide or SVG: "
            + ", ".join(unexpected)
        )
    if not extra_subtitles:
        return canonical_names
    return subtitle_names


def _animation_scope(
    scope: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    value = scope.get("animation", {})
    if not isinstance(value, dict):
        raise ValueError(f'{label} field "animation" must be an object')
    return value


def _effective_slide_animation(
    config: dict[str, Any],
    slide_cfg: dict[str, Any],
) -> SlideAnimationSettings:
    defaults = config.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError('Canonical animations.json field "defaults" must be an object')
    default_animation = _animation_scope(
        defaults,
        label="Canonical animations.json defaults",
    )
    slide_animation = _animation_scope(
        slide_cfg,
        label="Canonical animations.json slide",
    )
    effect = normalize_animation_effect(
        slide_animation.get(
            "effect",
            default_animation.get("effect", "none"),
        )
    )
    duration_ms = animation_seconds_to_milliseconds(
        slide_animation.get(
            "duration",
            default_animation.get("duration", 0.4),
        ),
        "canonical animation duration",
        allow_zero=False,
    )
    stagger_ms = animation_seconds_to_milliseconds(
        slide_animation.get(
            "stagger",
            default_animation.get("stagger", 0.5),
        ),
        "canonical animation stagger",
        allow_zero=True,
    )
    trigger = slide_animation.get(
        "trigger",
        default_animation.get("trigger", "after-previous"),
    )
    if not isinstance(trigger, str):
        raise ValueError(f"Canonical animation trigger must be a string: {trigger!r}")
    return SlideAnimationSettings(
        effect=effect,
        duration_ms=duration_ms,
        stagger_ms=stagger_ms,
        trigger=trigger,
    )


def _group_is_animated(
    group_cfg: dict[str, Any],
    slide_effect: str | None,
) -> bool:
    if "effect" not in group_cfg:
        return slide_effect is not None
    return normalize_animation_effect(group_cfg["effect"]) is not None


def _needs_svg_group_resolution(
    settings: SlideAnimationSettings,
    groups_cfg: dict[str, Any],
    plan_entries: list[TimingPlanEntry] | None,
) -> bool:
    """Return whether JSON alone cannot prove the effective group sequence."""
    active_explicit = [
        group_id
        for group_id, group_cfg in groups_cfg.items()
        if isinstance(group_cfg, dict)
        and _group_is_animated(group_cfg, settings.effect)
    ]
    if plan_entries is None:
        if settings.effect is not None:
            return True
        return (
            len(active_explicit) > 1
            and any("order" not in groups_cfg[group_id] for group_id in active_explicit)
        )

    candidate_ids = list(
        dict.fromkeys(
            [
                *(entry.group_id for entry in plan_entries),
                *active_explicit,
            ]
        )
    )
    active_candidates = [
        group_id
        for group_id in candidate_ids
        if group_id in groups_cfg
        and isinstance(groups_cfg[group_id], dict)
        and _group_is_animated(groups_cfg[group_id], settings.effect)
    ]
    if len(active_candidates) <= 1:
        return False
    return any("order" not in groups_cfg[group_id] for group_id in active_candidates)


def _resolve_animation_groups(
    project_path: Path,
    slide_name: str,
    slide_cfg: dict[str, Any],
    settings: SlideAnimationSettings,
    plan_entries: list[TimingPlanEntry] | None,
) -> tuple[list[AnimationGroupState], bool]:
    """Resolve one effective sequence, parsing only an ambiguous page SVG."""
    groups_value = slide_cfg.get("groups", {})
    if not isinstance(groups_value, dict):
        raise ValueError(
            f'Canonical animations.json slide "{slide_name}" groups must be an object'
        )
    groups_cfg: dict[str, dict[str, Any]] = {}
    for group_id, group_cfg in groups_value.items():
        if not isinstance(group_cfg, dict):
            raise ValueError(
                f'Canonical animations.json group "{slide_name}/{group_id}" '
                "must be an object"
            )
        groups_cfg[group_id] = group_cfg

    use_svg = _needs_svg_group_resolution(settings, groups_cfg, plan_entries)
    candidate_ids: list[str]
    if use_svg:
        svg_path = project_path / "svg_output" / f"{slide_name}.svg"
        if not svg_path.is_file():
            raise FileNotFoundError(
                f"Animation group mapping is ambiguous and requires the page SVG: "
                f"{svg_path}"
            )
        targets, anonymous_groups = scan_svg_targets(svg_path)
        duplicate_ids = sorted(
            group_id
            for group_id in {target.group_id for target in targets}
            if sum(target.group_id == group_id for target in targets) > 1
        )
        if duplicate_ids:
            raise ValueError(
                f'SVG slide "{slide_name}" has duplicate top-level group id(s): '
                + ", ".join(duplicate_ids)
            )
        for item in anonymous_groups:
            print(
                f"Warning: {item} has no id and cannot participate in narration timing",
                file=sys.stderr,
            )

        targets_by_id = {target.group_id: target for target in targets}
        referenced_ids = set(groups_cfg)
        if plan_entries is not None:
            referenced_ids.update(entry.group_id for entry in plan_entries)
        missing_ids = sorted(referenced_ids - set(targets_by_id))
        if missing_ids:
            raise ValueError(
                f'Animation mapping for slide "{slide_name}" references missing '
                f"top-level group(s): {', '.join(missing_ids)}"
            )
        structural_ids = sorted(
            group_id
            for group_id in referenced_ids
            if targets_by_id[group_id].structurally_static
            and (
                group_id not in groups_cfg
                or _group_is_animated(groups_cfg[group_id], settings.effect)
            )
        )
        if structural_ids:
            raise ValueError(
                f'Animation mapping for slide "{slide_name}" targets structural '
                f"group(s): {', '.join(structural_ids)}"
            )

        candidate_ids = []
        for target in targets:
            if target.structurally_static:
                continue
            group_cfg = groups_cfg.get(target.group_id, {})
            explicitly_animated = (
                target.group_id in groups_cfg
                and _group_is_animated(group_cfg, settings.effect)
            )
            if target.chrome and not explicitly_animated:
                continue
            candidate_ids.append(target.group_id)
    elif plan_entries is not None:
        candidate_ids = list(
            dict.fromkeys(
                [
                    *(entry.group_id for entry in plan_entries),
                    *groups_cfg,
                ]
            )
        )
    else:
        candidate_ids = list(groups_cfg)

    preliminaries: list[tuple[int, int, str, dict[str, Any]]] = []
    for source_index, group_id in enumerate(candidate_ids):
        group_cfg = groups_cfg.get(group_id, {})
        if not _group_is_animated(group_cfg, settings.effect):
            continue
        order = group_cfg.get("order", source_index + 1)
        if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
            raise ValueError(
                f'Canonical animation order for "{slide_name}/{group_id}" '
                f"must be a positive integer: {order!r}"
            )
        preliminaries.append((order, source_index, group_id, group_cfg))
    preliminaries.sort(key=lambda item: (item[0], item[1]))

    states: list[AnimationGroupState] = []
    for sequence_index, (order, source_index, group_id, group_cfg) in enumerate(
        preliminaries
    ):
        duration_ms = animation_seconds_to_milliseconds(
            group_cfg.get("duration", settings.duration_ms / 1000),
            f'canonical animation duration for "{slide_name}/{group_id}"',
            allow_zero=False,
        )
        original_delay_ms = animation_seconds_to_milliseconds(
            group_cfg.get(
                "delay",
                0 if sequence_index == 0 else settings.stagger_ms / 1000,
            ),
            f'canonical animation delay for "{slide_name}/{group_id}"',
            allow_zero=True,
        )
        states.append(
            AnimationGroupState(
                group_id=group_id,
                order=order,
                source_index=source_index,
                duration_ms=duration_ms,
                original_delay_ms=original_delay_ms,
            )
        )
    return states, use_svg


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
    canonical_path: Path,
    plan_path: Path,
    subtitle_dir: Path,
    audio_dir: Path,
    output_path: Path,
    narration_padding: float,
    force: bool,
) -> AnimationBuildResult:
    """Derive narration timing without modifying the canonical animation file."""
    if not math.isfinite(narration_padding) or narration_padding < 0:
        raise ValueError("Narration padding must be finite and non-negative")
    _reject_output_alias(
        output_path,
        [canonical_path, plan_path],
        label="Narration animation config",
    )
    canonical = _load_canonical_animation_config(canonical_path)
    slide_names = _animation_slide_names(project_path, canonical, subtitle_dir)
    subtitle_paths = [subtitle_dir / f"{slide_name}.srt" for slide_name in slide_names]
    _reject_output_alias(
        output_path,
        subtitle_paths,
        label="Narration animation config",
    )

    timing_plan: dict[str, list[TimingPlanEntry]] | None = None
    if plan_path.is_file():
        expected_srt_sha256, planned_padding, loaded_plan = _load_timing_plan(
            plan_path
        )
        if not math.isclose(
            narration_padding,
            planned_padding,
            rel_tol=0,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "Narration padding differs from the timing plan: "
                f"plan={planned_padding}, command={narration_padding}"
            )
        current_srt_sha256 = _subtitle_fingerprint(slide_names, subtitle_dir)
        if current_srt_sha256 != expected_srt_sha256:
            raise ValueError(
                "Narration timing plan was authored for a different SRT set: "
                f"plan={expected_srt_sha256}, current={current_srt_sha256}"
            )
        if set(loaded_plan) != set(slide_names):
            raise ValueError(
                "Narration timing plan slides do not match animations.json"
            )
        timing_plan = loaded_plan

    derived = copy.deepcopy(canonical)
    canonical_slides = canonical.get("slides", {})
    derived_slides = derived.setdefault("slides", {})
    if not isinstance(canonical_slides, dict) or not isinstance(
        derived_slides,
        dict,
    ):
        raise ValueError('Canonical animations.json field "slides" must be an object')

    anchored_count = 0
    fallback_count = 0
    ignored_cue_count = 0
    svg_fallback_slide_count = 0
    drift_warnings: list[str] = []
    audio_paths: list[Path] = []

    for slide_name in slide_names:
        cues = _parse_srt(subtitle_dir / f"{slide_name}.srt")
        audio_path = _find_audio(audio_dir, slide_name)
        audio_paths.append(audio_path)
        audio_duration = probe_audio_duration(audio_path)
        if audio_duration is None:
            raise RuntimeError(
                f"Unable to read narration duration with ffprobe: {audio_path}"
            )

        canonical_slide = canonical_slides.get(slide_name, {})
        if not isinstance(canonical_slide, dict):
            raise ValueError(
                f'Canonical animations.json slide "{slide_name}" must be an object'
            )
        derived_slide = derived_slides.setdefault(
            slide_name,
            copy.deepcopy(canonical_slide),
        )
        if not isinstance(derived_slide, dict):
            raise ValueError(
                f'Derived animation slide "{slide_name}" must be an object'
            )
        settings = _effective_slide_animation(canonical, canonical_slide)
        plan_entries = timing_plan.get(slide_name) if timing_plan else None
        states, used_svg = _resolve_animation_groups(
            project_path,
            slide_name,
            canonical_slide,
            settings,
            plan_entries,
        )
        if used_svg:
            svg_fallback_slide_count += 1

        state_ids = {state.group_id for state in states}
        cue_by_group: dict[str, int | None] = {}
        if plan_entries is not None:
            for entry in plan_entries:
                if entry.group_id not in state_ids:
                    raise ValueError(
                        f'Narration timing plan references a non-animated group: '
                        f"{slide_name}/{entry.group_id}"
                    )
                if entry.cue_number is not None and entry.cue_number > len(cues):
                    raise ValueError(
                        f'Narration timing plan "{slide_name}/{entry.group_id}" '
                        f"references cue {entry.cue_number}, but the SRT has "
                        f"{len(cues)} cues"
                    )
                cue_by_group[entry.group_id] = entry.cue_number
        else:
            cue_by_group = {
                state.group_id: index + 1 if index < len(cues) else None
                for index, state in enumerate(states)
            }

        animation_value = derived_slide.setdefault("animation", {})
        if not isinstance(animation_value, dict):
            raise ValueError(
                f'Derived animation slide "{slide_name}" animation must be an object'
            )
        animation_value["trigger"] = "after-previous"
        groups_value = derived_slide.setdefault("groups", {})
        if not isinstance(groups_value, dict):
            raise ValueError(
                f'Derived animation slide "{slide_name}" groups must be an object'
            )

        previous_end_ms = 0
        referenced_cues: set[int] = set()
        for state in states:
            cue_number = cue_by_group.get(state.group_id)
            if cue_number is None:
                fallback_count += 1
                delay_ms = state.original_delay_ms
                actual_start_ms = previous_end_ms + delay_ms
            else:
                anchored_count += 1
                referenced_cues.add(cue_number)
                desired_start_ms = cues[cue_number - 1].start_ms
                actual_start_ms = max(desired_start_ms, previous_end_ms)
                delay_ms = actual_start_ms - previous_end_ms
                drift_ms = actual_start_ms - desired_start_ms
                if drift_ms > 500:
                    drift_warnings.append(
                        f"{slide_name}/{state.group_id}: cue {cue_number} "
                        f"starts at {_seconds_from_ms(desired_start_ms):.3f}s, "
                        f"animation starts at {_seconds_from_ms(actual_start_ms):.3f}s "
                        f"(after-previous drift {_seconds_from_ms(drift_ms):.3f}s)"
                    )

            group_value = groups_value.setdefault(state.group_id, {})
            if not isinstance(group_value, dict):
                raise ValueError(
                    f'Derived animation group "{slide_name}/{state.group_id}" '
                    "must be an object"
                )
            group_value["order"] = state.order
            group_value["delay"] = _seconds_from_ms(delay_ms)
            previous_end_ms = actual_start_ms + state.duration_ms

        ignored_cue_count += len(cues) - len(referenced_cues)

        advance_ms = int((audio_duration + narration_padding) * 1000)
        if previous_end_ms > advance_ms:
            raise ValueError(
                f'Animations on slide "{slide_name}" end at '
                f"{_seconds_from_ms(previous_end_ms):.3f}s, after the recorded "
                f"slide advance at {_seconds_from_ms(advance_ms):.3f}s"
            )

    _reject_output_alias(
        output_path,
        audio_paths,
        label="Narration animation config",
    )
    _require_replaceable(output_path, force)
    derived_errors = list(
        dict.fromkeys(
            [
                *validate_transition_config(derived),
                *validate_animation_config_errors(derived),
            ]
        )
    )
    if derived_errors:
        details = "\n".join(f"- {error}" for error in derived_errors)
        raise ValueError(f"Derived narration animation config is invalid:\n{details}")
    _atomic_write_text(
        output_path,
        json.dumps(derived, ensure_ascii=False, indent=2) + "\n",
    )

    for warning in drift_warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return AnimationBuildResult(
        slide_count=len(slide_names),
        group_count=anchored_count + fallback_count,
        anchored_count=anchored_count,
        fallback_count=fallback_count,
        ignored_cue_count=ignored_cue_count,
        svg_fallback_slide_count=svg_fallback_slide_count,
        timing_plan_written=False,
    )


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
            "Derive narrated object animation timings and merge page-local "
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
        help="derive narration_animations.json from animations.json and page-local SRT",
    )
    animations.add_argument("project_path", help="Project directory")
    animations.add_argument(
        "--animation-config",
        default=None,
        help="Read-only canonical config; default: <project>/animations.json",
    )
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
        help=(
            "Narration animation output; "
            "default: <project>/narration_animations.json"
        ),
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
        help="Replace an existing narration_animations.json",
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
            slide_names = _page_subtitle_names(subtitle_dir)
            for slide_name in slide_names:
                _parse_srt(subtitle_dir / f"{slide_name}.srt")
            print(_subtitle_fingerprint(slide_names, subtitle_dir))
            return 0

        if args.command == "animations":
            canonical_path = _project_path(
                project_path,
                args.animation_config,
                Path("animations.json"),
            )
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
                Path("narration_animations.json"),
            )
            result = rebuild_animations(
                project_path,
                canonical_path=canonical_path,
                plan_path=plan_path,
                subtitle_dir=subtitle_dir,
                audio_dir=audio_dir,
                output_path=output_path,
                narration_padding=args.narration_padding,
                force=args.force,
            )
            print(f"Narration animation config written: {output_path}")
            print(
                f"Slides: {result.slide_count}; groups: {result.group_count}; "
                f"SRT-anchored: {result.anchored_count}; "
                f"canonical-delay fallback: {result.fallback_count}; "
                f"SVG fallback slides: {result.svg_fallback_slide_count}; "
                f"unused cues: {result.ignored_cue_count}"
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
