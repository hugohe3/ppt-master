#!/usr/bin/env python3
"""
PPT Master - Video Sound Mix

Recover transition and object-animation sound cues from the final narrated
PPTX, calibrate them to a PowerPoint-exported video, render an independent SFX
stem, and mix that stem with the video's narration track.
See workflows/stages/generate-audio.md for the owning delivery stage.

Usage:
    python3 scripts/video_sound_mix.py <project_path> --pptx <pptx> \
        --trace <trace.json> --video <raw.mp4> [options]

Examples:
    python3 scripts/video_sound_mix.py projects/demo \
        --pptx exports/demo_narrated.pptx \
        --trace validation/demo_narrated.trace.json \
        --video exports/demo_raw.mp4 --force

Dependencies:
    ffmpeg, ffprobe, and numpy
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from narration_sync import (  # noqa: E402
    VideoTimelineCalibration,
    calibrate_video_timeline,
    presentation_slide_members,
)
from pptx_animations import read_slide_animation_sequence  # noqa: E402
from pptx_opc_validation import (  # noqa: E402
    canonical_opc_part_path,
    resolve_internal_opc_target,
)
from pptx_transitions import (  # noqa: E402
    AUDIO_REL_TYPE,
    read_slide_transition_xml,
)

configure_utf8_stdio()


_PACKAGE_REL_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
_RELATIONSHIP_TAG = f"{{{_PACKAGE_REL_NS}}}Relationship"
_DEFAULT_TRANSITION_GAIN_DB = -9.1
_DEFAULT_ANIMATION_GAIN_DB = -12.0
_DEFAULT_LIMITER_DBFS = -1.0
_OUTPUT_SAMPLE_RATE = 48_000
_OUTPUT_AUDIO_BITRATE = "192k"
_START_TIME_TOLERANCE_MS = 1
_VERIFICATION_SAMPLE_RATE = 8000
_MIN_VERIFICATION_WINDOW_SAMPLES = 2
_MIN_SOUND_MIX_CORRELATION = 0.20


@dataclass(frozen=True)
class SoundCue:
    """One resolved PPTX sound cue placed on the exported-video timeline."""

    kind: str
    slide_num: int
    slide_name: str
    row_index: int | None
    shape_id: int | None
    group_id: str | None
    relationship_id: str
    sound_name: str
    package_part: str
    media_sha256: str
    media_path: Path
    source_duration_ms: int
    powerpoint_time_ms: int
    video_time_ms: int
    gain_db: float


@dataclass(frozen=True)
class SoundMixResult:
    """Published files and cue count from one video sound mix."""

    output_path: Path
    stem_path: Path
    report_path: Path
    cue_count: int
    verification_correlation: float
    true_peak_dbfs: float


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain one JSON object: {path}")
    return value


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_input_path(project_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else project_path / path).resolve()


def _project_output_path(
    project_path: Path,
    value: str | None,
    default: Path,
) -> Path:
    path = Path(value).expanduser() if value else default
    return (path if path.is_absolute() else project_path / path).resolve()


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(
            f"Video sound mixing requires {name} on PATH. Install ffmpeg "
            "and make both ffmpeg and ffprobe available."
        )
    return path


def _run_command(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{label} failed:\n{details}")
    return result


def _probe_media(path: Path, ffprobe_path: str) -> dict[str, Any]:
    result = _run_command(
        [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            (
                "format=duration,start_time:"
                "stream=index,codec_type,codec_name,time_base,start_pts,"
                "start_time,duration_ts,duration,sample_rate,channels,"
                "width,height,avg_frame_rate"
            ),
            "-of",
            "json",
            str(path),
        ],
        f"ffprobe inspection for {path}",
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON for {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"ffprobe returned an invalid payload for {path}")
    return payload


def _duration_ms(probe: dict[str, Any], label: str) -> int:
    format_value = probe.get("format")
    raw_duration = (
        format_value.get("duration")
        if isinstance(format_value, dict)
        else None
    )
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unable to read {label} duration with ffprobe") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"{label} duration must be positive and finite")
    return int(round(duration * 1000))


def _stream_duration_ms(
    stream: dict[str, Any],
    *,
    fallback_ms: int,
) -> int:
    try:
        duration = float(stream.get("duration"))
    except (TypeError, ValueError):
        return fallback_ms
    if not math.isfinite(duration) or duration <= 0:
        return fallback_ms
    return int(round(duration * 1000))


def _stream_start_ms(stream: dict[str, Any]) -> int:
    try:
        start = float(stream.get("start_time", 0))
    except (TypeError, ValueError):
        return 0
    if not math.isfinite(start):
        return 0
    return int(round(start * 1000))


def _frame_duration_ms(stream: dict[str, Any]) -> float:
    value = stream.get("avg_frame_rate")
    if not isinstance(value, str) or "/" not in value:
        return 1000 / 30
    numerator_text, denominator_text = value.split("/", 1)
    try:
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except ValueError:
        return 1000 / 30
    if numerator <= 0 or denominator <= 0:
        return 1000 / 30
    return 1000 * denominator / numerator


def _stream_timing_signature(stream: dict[str, Any]) -> dict[str, object]:
    """Return the packet-clock fields that must survive video stream copy."""
    signature: dict[str, object] = {}
    for key in ("time_base", "start_pts", "duration_ts"):
        value = stream.get(key)
        if value is None:
            raise ValueError(f"Video stream is missing {key}")
        signature[key] = value
    return signature


def _audio_sample_count(stream: dict[str, Any]) -> int:
    """Resolve an audio stream duration to exact samples from its time base."""
    try:
        sample_rate = int(stream.get("sample_rate"))
        duration_ts = int(stream.get("duration_ts"))
        time_base = Fraction(str(stream.get("time_base")))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("Unable to read exact audio sample count") from exc
    samples = duration_ts * time_base * sample_rate
    if samples.denominator != 1:
        raise ValueError(
            "Audio duration does not resolve to a whole number of samples"
        )
    return samples.numerator


def _target_sample_count(duration_ms: int) -> int:
    return int(round(duration_ms * _OUTPUT_SAMPLE_RATE / 1000))


def _streams(probe: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    raw_streams = probe.get("streams")
    if not isinstance(raw_streams, list):
        return []
    return [
        stream
        for stream in raw_streams
        if isinstance(stream, dict) and stream.get("codec_type") == kind
    ]


def _stream_hash(path: Path, selector: str, ffmpeg_path: str) -> str:
    result = _run_command(
        [
            ffmpeg_path,
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            selector,
            "-c",
            "copy",
            "-f",
            "hash",
            "-hash",
            "sha256",
            "-",
        ],
        f"stream hash for {path}",
    )
    match = re.search(r"SHA256=([0-9a-fA-F]{64})", result.stdout)
    if match is None:
        raise RuntimeError(f"Unable to parse stream hash for {path}")
    return match.group(1).lower()


def _maximum_volume_db(path: Path, ffmpeg_path: str) -> float | None:
    result = subprocess.run(
        [
            ffmpeg_path,
            "-nostdin",
            "-hide_banner",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Volume inspection failed for {path}:\n{result.stderr.strip()}"
        )
    match = re.search(r"max_volume:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*dB", result.stderr)
    if match is None:
        raise RuntimeError(f"Unable to read maximum volume for {path}")
    if match.group(1) == "-inf":
        return None
    return float(match.group(1))


def _true_peak_dbfs(path: Path, ffmpeg_path: str) -> float | None:
    result = subprocess.run(
        [
            ffmpeg_path,
            "-nostdin",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"True-peak inspection failed for {path}:\n{result.stderr.strip()}"
        )
    matches = re.findall(
        r"Peak:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*dBFS",
        result.stderr,
    )
    if not matches:
        raise RuntimeError(f"Unable to read true peak for {path}")
    if matches[-1] == "-inf":
        return None
    return float(matches[-1])


def _decode_audio_f32(path: Path, ffmpeg_path: str) -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Video sound verification requires numpy. Install it with: "
            "python3 -m pip install numpy"
        ) from exc
    result = subprocess.run(
        [
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
            str(_VERIFICATION_SAMPLE_RATE),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        details = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Unable to decode audio for verification: {path}\n{details}")
    return np.frombuffer(result.stdout, dtype="<f4").astype(np.float64)


def _sound_mix_correlation(
    *,
    raw_video_path: Path,
    mixed_video_path: Path,
    stem_path: Path,
    cues: list[SoundCue],
    duration_ms: int,
    ffmpeg_path: str,
) -> float:
    """Correlate the added final-audio component with the rendered SFX stem."""
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Video sound verification requires numpy. Install it with: "
            "python3 -m pip install numpy"
        ) from exc

    target_samples = int(round(duration_ms * _VERIFICATION_SAMPLE_RATE / 1000))
    decoded = [
        _decode_audio_f32(path, ffmpeg_path)
        for path in (raw_video_path, mixed_video_path, stem_path)
    ]
    arrays: list[Any] = []
    for samples in decoded:
        if len(samples) < target_samples:
            samples = np.pad(samples, (0, target_samples - len(samples)))
        arrays.append(samples[:target_samples])
    raw_audio, mixed_audio, stem_audio = arrays

    cue_mask = np.zeros(target_samples, dtype=bool)
    for cue in cues:
        start = int(round(cue.video_time_ms * _VERIFICATION_SAMPLE_RATE / 1000))
        end = int(
            round(
                (cue.video_time_ms + cue.source_duration_ms)
                * _VERIFICATION_SAMPLE_RATE
                / 1000
            )
        )
        cue_mask[max(0, start):min(target_samples, end)] = True
    cue_indices = np.flatnonzero(cue_mask)
    if len(cue_indices) < _MIN_VERIFICATION_WINDOW_SAMPLES:
        raise RuntimeError("SFX cue windows are too short for mix verification")

    background = ~cue_mask
    raw_background = raw_audio[background]
    mixed_background = mixed_audio[background]
    denominator = float(np.dot(raw_background, raw_background))
    narration_scale = (
        float(np.dot(mixed_background, raw_background)) / denominator
        if denominator > 1e-12
        else 1.0
    )
    added_audio = mixed_audio - narration_scale * raw_audio

    best_correlation = -1.0
    maximum_lag = max(1, _VERIFICATION_SAMPLE_RATE // 200)
    for lag in range(-maximum_lag, maximum_lag + 1):
        shifted_indices = cue_indices + lag
        valid = (shifted_indices >= 0) & (shifted_indices < target_samples)
        if not valid.any():
            continue
        observed = added_audio[shifted_indices[valid]]
        expected = stem_audio[cue_indices[valid]]
        observed = observed - observed.mean()
        expected = expected - expected.mean()
        norm = float(np.linalg.norm(observed) * np.linalg.norm(expected))
        if norm <= 1e-12:
            continue
        correlation = float(np.dot(observed, expected) / norm)
        best_correlation = max(best_correlation, correlation)
    if best_correlation < _MIN_SOUND_MIX_CORRELATION:
        raise RuntimeError(
            "Mixed-video audio does not reliably contain the rendered SFX stem: "
            f"correlation={best_correlation:.3f}, "
            f"required>={_MIN_SOUND_MIX_CORRELATION:.2f}"
        )
    return best_correlation


def _trace_slides(trace: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    raw_slides = trace.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        raise ValueError("Conversion trace must contain a non-empty slides array")
    slide_count = trace.get("slide_count")
    if slide_count != len(raw_slides):
        raise ValueError(
            "Conversion trace slide_count does not match its slides array"
        )

    slides: list[dict[str, Any]] = []
    slide_names: list[str] = []
    for expected_number, raw_slide in enumerate(raw_slides, 1):
        if not isinstance(raw_slide, dict):
            raise ValueError(
                f"Conversion trace slide {expected_number} must be an object"
            )
        if raw_slide.get("slide_num") != expected_number:
            raise ValueError(
                "Conversion trace slides must be numbered consecutively from 1"
            )
        raw_svg = raw_slide.get("svg")
        if not isinstance(raw_svg, str) or not raw_svg.strip():
            raise ValueError(
                f"Conversion trace slide {expected_number} has no SVG path"
            )
        slide_name = Path(raw_svg).stem
        if not slide_name:
            raise ValueError(
                f"Conversion trace slide {expected_number} has an invalid SVG path"
            )
        slides.append(raw_slide)
        slide_names.append(slide_name)
    if len(set(slide_names)) != len(slide_names):
        raise ValueError("Conversion trace slide names must be unique")
    return slides, slide_names


def _shape_group_ids(trace_slide: dict[str, Any]) -> dict[int, str]:
    events = trace_slide.get("events")
    if not isinstance(events, list):
        return {}
    mapping: dict[int, str] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        shape_id = event.get("shape_id")
        group_id = event.get("id")
        if (
            isinstance(shape_id, int)
            and not isinstance(shape_id, bool)
            and isinstance(group_id, str)
            and group_id
        ):
            mapping[shape_id] = group_id
    return mapping


def _package_part_map(package: zipfile.ZipFile) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for member in package.namelist():
        key = canonical_opc_part_path(member)
        if key is None:
            continue
        prior = mapping.get(key)
        if prior is not None and prior != member:
            raise ValueError(
                "PPTX contains OPC-equivalent duplicate package parts: "
                f"{prior!r}, {member!r}"
            )
        mapping[key] = member
    return mapping


def _relationships_part(slide_part: str) -> str:
    slide_path = Path(slide_part)
    return (
        slide_path.parent / "_rels" / f"{slide_path.name}.rels"
    ).as_posix()


def _slide_relationships(
    package: zipfile.ZipFile,
    rels_part: str,
) -> dict[str, ET.Element]:
    try:
        root = ET.fromstring(package.read(rels_part))
    except KeyError as exc:
        raise ValueError(f"PPTX is missing slide relationships: {rels_part}") from exc
    except ET.ParseError as exc:
        raise ValueError(f"Invalid slide relationships XML: {rels_part}") from exc
    relationships: dict[str, ET.Element] = {}
    for relationship in root.findall(_RELATIONSHIP_TAG):
        relationship_id = relationship.get("Id")
        if not relationship_id:
            continue
        if relationship_id in relationships:
            raise ValueError(
                f"Duplicate relationship id {relationship_id!r} in {rels_part}"
            )
        relationships[relationship_id] = relationship
    return relationships


def _extract_sound(
    *,
    package: zipfile.ZipFile,
    package_parts: dict[str, str],
    relationships: dict[str, ET.Element],
    rels_part: str,
    relationship_id: str,
    temp_dir: Path,
    ffprobe_path: str,
    extracted: dict[str, tuple[str, str, Path, int]],
) -> tuple[str, str, Path, int]:
    relationship = relationships.get(relationship_id)
    if relationship is None:
        raise ValueError(
            f"PPTX sound relationship is missing: {rels_part}#{relationship_id}"
        )
    if relationship.get("Type") != AUDIO_REL_TYPE:
        raise ValueError(
            f"PPTX sound relationship is not audio: {rels_part}#{relationship_id}"
        )
    if relationship.get("TargetMode", "Internal") == "External":
        raise ValueError(
            f"PPTX sound relationship must be internal: {rels_part}#{relationship_id}"
        )
    target = relationship.get("Target") or ""
    target_key = resolve_internal_opc_target(rels_part, target)
    if target_key is None:
        raise ValueError(
            f"PPTX sound relationship target is invalid: {rels_part}#{relationship_id}"
        )
    package_part = package_parts.get(target_key)
    if package_part is None:
        raise ValueError(
            f"PPTX sound relationship target is missing: {target!r}"
        )
    cached = extracted.get(package_part)
    if cached is not None:
        return cached

    payload = package.read(package_part)
    media_sha256 = hashlib.sha256(payload).hexdigest()
    extension = Path(package_part).suffix.lower()
    if extension not in {".m4a", ".mp3", ".wav"}:
        raise ValueError(
            f"PPTX animation sound uses an unsupported media type: {package_part}"
        )
    media_path = temp_dir / f"{media_sha256}{extension}"
    media_path.write_bytes(payload)
    source_duration_ms = _duration_ms(
        _probe_media(media_path, ffprobe_path),
        f"PPTX sound {package_part}",
    )
    resolved = (package_part, media_sha256, media_path, source_duration_ms)
    extracted[package_part] = resolved
    return resolved


def _require_equal(actual: object, expected: object, field: str) -> None:
    if actual != expected:
        raise ValueError(
            f"Final narrated trace does not match the PPTX at {field}: "
            f"trace={actual!r}, pptx={expected!r}"
        )


def _resolve_sound_cues(
    *,
    pptx_path: Path,
    trace_slides: list[dict[str, Any]],
    calibration: VideoTimelineCalibration,
    transition_gain_db: float,
    animation_gain_db: float,
    video_duration_ms: int,
    temp_dir: Path,
    ffprobe_path: str,
) -> list[SoundCue]:
    cues: list[SoundCue] = []
    extracted: dict[str, tuple[str, str, Path, int]] = {}
    with zipfile.ZipFile(pptx_path) as package:
        slide_members = presentation_slide_members(package)
        if len(slide_members) != len(trace_slides):
            raise ValueError(
                f"Final narrated PPTX has {len(slide_members)} slides, but "
                f"the trace has {len(trace_slides)}"
            )
        package_parts = _package_part_map(package)

        for slide_num, (slide_part, trace_slide, calibrated) in enumerate(
            zip(slide_members, trace_slides, calibration.slides),
            1,
        ):
            slide_xml = package.read(slide_part)
            transition = read_slide_transition_xml(slide_xml)
            animation = read_slide_animation_sequence(
                slide_xml,
                require_supported_effects=True,
            )
            trace_motion = trace_slide.get("motion")
            trace_animation = trace_slide.get("animation")
            if not isinstance(trace_motion, dict) or not isinstance(
                trace_animation, dict
            ):
                raise ValueError(
                    f"Conversion trace slide {slide_num} lacks resolved motion"
                )

            _require_equal(
                trace_motion.get("duration_ms"),
                transition.duration_ms,
                f"slide {slide_num} transition duration",
            )
            _require_equal(
                trace_motion.get("advance_after_ms"),
                transition.advance_after_ms,
                f"slide {slide_num} recorded advance",
            )
            _require_equal(
                trace_motion.get("sound_relationship_id"),
                transition.sound_relationship_id,
                f"slide {slide_num} transition sound relationship",
            )
            _require_equal(
                trace_motion.get("sound_name"),
                transition.sound_name,
                f"slide {slide_num} transition sound name",
            )
            _require_equal(
                trace_motion.get("fallback_sound_relationship_id"),
                transition.fallback_sound_relationship_id,
                f"slide {slide_num} fallback transition sound relationship",
            )
            _require_equal(
                trace_motion.get("fallback_sound_name"),
                transition.fallback_sound_name,
                f"slide {slide_num} fallback transition sound name",
            )
            if transition.fallback_sound_relationship_id not in {
                None,
                transition.sound_relationship_id,
            }:
                raise ValueError(
                    f"Slide {slide_num} transition primary and fallback "
                    "branches reference different sounds"
                )

            raw_rows = trace_animation.get("rows")
            if not isinstance(raw_rows, list):
                raise ValueError(
                    f"Conversion trace slide {slide_num} animation rows are invalid"
                )
            if len(raw_rows) != len(animation.rows):
                raise ValueError(
                    f"Final narrated trace has {len(raw_rows)} animation rows "
                    f"on slide {slide_num}; PPTX has {len(animation.rows)}"
                )
            for row_index, (raw_row, actual_row) in enumerate(
                zip(raw_rows, animation.rows),
                1,
            ):
                if not isinstance(raw_row, dict):
                    raise ValueError(
                        f"Conversion trace slide {slide_num} row {row_index} "
                        "must be an object"
                    )
                for key, expected in (
                    ("shape_id", actual_row.shape_id),
                    ("offset_ms", actual_row.offset_ms),
                    ("trigger", actual_row.trigger),
                    ("sound_relationship_id", actual_row.sound_relationship_id),
                    ("sound_name", actual_row.sound_name),
                ):
                    _require_equal(
                        raw_row.get(key),
                        expected,
                        f"slide {slide_num} animation row {row_index} {key}",
                    )

            sound_relationship_ids = {
                relationship_id
                for relationship_id in (
                    transition.sound_relationship_id,
                    *(
                        row.sound_relationship_id
                        for row in animation.rows
                    ),
                )
                if relationship_id is not None
            }
            relationships: dict[str, ET.Element] = {}
            rels_part = _relationships_part(slide_part)
            if sound_relationship_ids:
                relationships = _slide_relationships(package, rels_part)

            group_ids = _shape_group_ids(trace_slide)
            if transition.sound_relationship_id is not None:
                package_part, media_sha256, media_path, source_duration_ms = (
                    _extract_sound(
                        package=package,
                        package_parts=package_parts,
                        relationships=relationships,
                        rels_part=rels_part,
                        relationship_id=transition.sound_relationship_id,
                        temp_dir=temp_dir,
                        ffprobe_path=ffprobe_path,
                        extracted=extracted,
                    )
                )
                cues.append(
                    SoundCue(
                        kind="transition",
                        slide_num=slide_num,
                        slide_name=calibrated.slide_name,
                        row_index=None,
                        shape_id=None,
                        group_id=None,
                        relationship_id=transition.sound_relationship_id,
                        sound_name=transition.sound_name or Path(package_part).name,
                        package_part=package_part,
                        media_sha256=media_sha256,
                        media_path=media_path,
                        source_duration_ms=source_duration_ms,
                        powerpoint_time_ms=calibrated.powerpoint_slide_start_ms,
                        video_time_ms=calibrated.video_slide_start_ms,
                        gain_db=transition_gain_db,
                    )
                )

            for row_index, row in enumerate(animation.rows, 1):
                if row.sound_relationship_id is None:
                    continue
                if row.trigger not in {"after-previous", "with-previous"}:
                    raise ValueError(
                        f"Slide {slide_num} animation row {row_index} uses "
                        f"{row.trigger!r}; video sound timing requires a "
                        "click-free row"
                    )
                package_part, media_sha256, media_path, source_duration_ms = (
                    _extract_sound(
                        package=package,
                        package_parts=package_parts,
                        relationships=relationships,
                        rels_part=rels_part,
                        relationship_id=row.sound_relationship_id,
                        temp_dir=temp_dir,
                        ffprobe_path=ffprobe_path,
                        extracted=extracted,
                    )
                )
                powerpoint_time_ms = (
                    calibrated.powerpoint_slide_start_ms
                    + calibrated.transition_ms
                    + row.offset_ms
                )
                video_time_ms = (
                    calibrated.video_slide_start_ms
                    + calibrated.transition_ms
                    + row.offset_ms
                )
                cues.append(
                    SoundCue(
                        kind="animation",
                        slide_num=slide_num,
                        slide_name=calibrated.slide_name,
                        row_index=row_index,
                        shape_id=row.shape_id,
                        group_id=group_ids.get(row.shape_id),
                        relationship_id=row.sound_relationship_id,
                        sound_name=row.sound_name or Path(package_part).name,
                        package_part=package_part,
                        media_sha256=media_sha256,
                        media_path=media_path,
                        source_duration_ms=source_duration_ms,
                        powerpoint_time_ms=powerpoint_time_ms,
                        video_time_ms=video_time_ms,
                        gain_db=animation_gain_db,
                    )
                )

    cues.sort(
        key=lambda cue: (
            cue.video_time_ms,
            cue.slide_num,
            0 if cue.kind == "transition" else 1,
            cue.row_index or 0,
        )
    )
    if not cues:
        raise ValueError(
            "Final narrated PPTX and trace contain no transition or "
            "object-animation sound cues; use the PowerPoint video directly"
        )
    for cue in cues:
        if cue.video_time_ms < 0 or cue.video_time_ms >= video_duration_ms:
            raise ValueError(
                f"Sound cue falls outside the video: slide {cue.slide_num}, "
                f"time={cue.video_time_ms}ms, video={video_duration_ms}ms"
            )
        cue_end_ms = cue.video_time_ms + cue.source_duration_ms
        if cue_end_ms > video_duration_ms:
            raise ValueError(
                f"Sound cue would be truncated by the video end: slide "
                f"{cue.slide_num}, cue end={cue_end_ms}ms, "
                f"video={video_duration_ms}ms"
            )
    return cues


def _render_stem(
    *,
    cues: list[SoundCue],
    duration_ms: int,
    output_path: Path,
    ffmpeg_path: str,
) -> None:
    target_samples = _target_sample_count(duration_ms)
    command = [
        ffmpeg_path,
        "-nostdin",
        "-hide_banner",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={_OUTPUT_SAMPLE_RATE}:cl=stereo",
    ]
    for cue in cues:
        command.extend(["-i", str(cue.media_path)])

    filters = [
        (
            f"[0:a:0]aformat=sample_fmts=fltp:sample_rates={_OUTPUT_SAMPLE_RATE}:"
            "channel_layouts=stereo,"
            f"atrim=end_sample={target_samples},asetpts=N/SR/TB[base]"
        )
    ]
    labels = ["[base]"]
    for input_index, cue in enumerate(cues, 1):
        label = f"cue{input_index}"
        delay_samples = int(
            round(cue.video_time_ms * _OUTPUT_SAMPLE_RATE / 1000)
        )
        filters.append(
            f"[{input_index}:a:0]aresample={_OUTPUT_SAMPLE_RATE},"
            "aformat=sample_fmts=fltp:"
            f"sample_rates={_OUTPUT_SAMPLE_RATE}:channel_layouts=stereo,"
            f"asetpts=N/SR/TB,volume={cue.gain_db:.3f}dB,"
            f"adelay={delay_samples}S:all=1,"
            f"apad=whole_len={target_samples},"
            f"atrim=end_sample={target_samples}[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=first:"
        "dropout_transition=0:normalize=0,"
        f"atrim=end_sample={target_samples},asetpts=N/SR/TB[stem]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[stem]",
            "-c:a",
            "pcm_f32le",
            "-ar",
            str(_OUTPUT_SAMPLE_RATE),
            "-ac",
            "2",
            "-y",
            str(output_path),
        ]
    )
    _run_command(command, "SFX stem render")


def _mix_video(
    *,
    video_path: Path,
    stem_path: Path,
    duration_ms: int,
    limiter_dbfs: float,
    output_path: Path,
    ffmpeg_path: str,
) -> None:
    target_samples = _target_sample_count(duration_ms)
    limiter_ratio = 10 ** (limiter_dbfs / 20)
    filter_graph = (
        f"[0:a:0]aresample={_OUTPUT_SAMPLE_RATE}:first_pts=0,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"asetpts=N/SR/TB,apad=whole_len={target_samples},"
        f"atrim=end_sample={target_samples}[narration];"
        f"[1:a:0]aresample={_OUTPUT_SAMPLE_RATE}:first_pts=0,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"asetpts=N/SR/TB,apad=whole_len={target_samples},"
        f"atrim=end_sample={target_samples}[sfx];"
        "[narration][sfx]amix=inputs=2:duration=first:"
        "dropout_transition=0:normalize=0,"
        f"alimiter=limit={limiter_ratio:.9f}:attack=5:release=50:"
        "level=false:latency=true,"
        f"apad=whole_len={target_samples},"
        f"atrim=end_sample={target_samples},asetpts=N/SR/TB[mixed]"
    )
    _run_command(
        [
            ffmpeg_path,
            "-nostdin",
            "-hide_banner",
            "-v",
            "error",
            "-i",
            str(video_path),
            "-i",
            str(stem_path),
            "-filter_complex",
            filter_graph,
            "-map",
            "0:v:0",
            "-map",
            "[mixed]",
            "-map_metadata",
            "0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            _OUTPUT_AUDIO_BITRATE,
            "-ar",
            str(_OUTPUT_SAMPLE_RATE),
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            "-y",
            str(output_path),
        ],
        "Narration and SFX mix",
    )


def _temporary_output(path: Path, suffix: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f".{path.stem}.",
        suffix=suffix,
        dir=path.parent,
    )
    os.close(descriptor)
    temporary = Path(raw_path)
    temporary.unlink()
    return temporary


def _publish_outputs(replacements: list[tuple[Path, Path]]) -> None:
    """Publish verified outputs together, restoring prior files on failure."""
    backups: dict[Path, Path] = {}
    published: list[Path] = []
    try:
        for _temporary, destination in replacements:
            if not destination.exists():
                continue
            backup = _temporary_output(destination, f".backup{destination.suffix}")
            os.replace(destination, backup)
            backups[destination] = backup
        for temporary, destination in replacements:
            os.replace(temporary, destination)
            published.append(destination)
    except OSError as exc:
        rollback_errors: list[str] = []
        for destination in reversed(published):
            backup = backups.pop(destination, None)
            try:
                if backup is None:
                    destination.unlink(missing_ok=True)
                else:
                    os.replace(backup, destination)
            except OSError as rollback_exc:
                rollback_errors.append(f"{destination}: {rollback_exc}")
        for destination, backup in backups.items():
            try:
                os.replace(backup, destination)
            except OSError as rollback_exc:
                rollback_errors.append(f"{destination}: {rollback_exc}")
        if rollback_errors:
            raise RuntimeError(
                "Output publication failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        raise
    else:
        for backup in backups.values():
            backup.unlink(missing_ok=True)


def _cue_report(cue: SoundCue) -> dict[str, Any]:
    return {
        "kind": cue.kind,
        "slide_num": cue.slide_num,
        "slide_name": cue.slide_name,
        "row_index": cue.row_index,
        "shape_id": cue.shape_id,
        "group_id": cue.group_id,
        "relationship_id": cue.relationship_id,
        "sound_name": cue.sound_name,
        "package_part": cue.package_part,
        "media_sha256": cue.media_sha256,
        "source_duration_ms": cue.source_duration_ms,
        "powerpoint_time_ms": cue.powerpoint_time_ms,
        "video_time_ms": cue.video_time_ms,
        "gain_db": cue.gain_db,
    }


def mix_video_sounds(
    project_path: Path,
    *,
    pptx_path: Path,
    trace_path: Path,
    video_path: Path,
    audio_dir: Path,
    subtitle_dir: Path | None,
    output_path: Path,
    stem_path: Path,
    report_path: Path,
    transition_gain_db: float = _DEFAULT_TRANSITION_GAIN_DB,
    animation_gain_db: float = _DEFAULT_ANIMATION_GAIN_DB,
    limiter_dbfs: float = _DEFAULT_LIMITER_DBFS,
    force: bool = False,
) -> SoundMixResult:
    """Render and publish one calibrated animation-sound video mix."""
    project_path = project_path.resolve()
    pptx_path = pptx_path.resolve()
    trace_path = trace_path.resolve()
    video_path = video_path.resolve()
    audio_dir = audio_dir.resolve()
    subtitle_dir = subtitle_dir.resolve() if subtitle_dir is not None else None
    output_path = output_path.resolve()
    stem_path = stem_path.resolve()
    report_path = report_path.resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path does not exist: {project_path}")
    for label, path in (
        ("Final narrated PPTX", pptx_path),
        ("Final narrated conversion trace", trace_path),
        ("Raw PowerPoint video", video_path),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{label} does not exist: {path}")
    if pptx_path.suffix.lower() != ".pptx":
        raise ValueError(f"Final narrated PPTX must use .pptx: {pptx_path}")
    if video_path.suffix.lower() != ".mp4":
        raise ValueError(f"Raw PowerPoint video must use .mp4: {video_path}")
    if output_path.suffix.lower() != ".mp4":
        raise ValueError(f"Mixed video output must use .mp4: {output_path}")
    if stem_path.suffix.lower() != ".wav":
        raise ValueError(f"SFX stem output must use .wav: {stem_path}")
    if report_path.suffix.lower() != ".json":
        raise ValueError(f"Sound mix report must use .json: {report_path}")

    outputs = [output_path, stem_path, report_path]
    if len(set(outputs)) != len(outputs):
        raise ValueError("Mixed video, SFX stem, and report paths must differ")
    invalid_outputs = [
        path for path in outputs if path.exists() and not path.is_file()
    ]
    if invalid_outputs:
        raise ValueError(
            "Sound mix outputs must be regular files or unused paths: "
            + ", ".join(str(path) for path in invalid_outputs)
        )
    existing = [path for path in outputs if path.exists()]
    if existing and not force:
        raise FileExistsError(
            "Sound mix output already exists; use --force to replace it: "
            + ", ".join(str(path) for path in existing)
        )
    for label, value in (
        ("transition gain", transition_gain_db),
        ("animation gain", animation_gain_db),
    ):
        if not math.isfinite(value) or value < -60 or value > 0:
            raise ValueError(f"{label} must be finite and between -60 and 0 dB")
    if not math.isfinite(limiter_dbfs) or not -12 <= limiter_dbfs < 0:
        raise ValueError("limiter ceiling must be finite, at least -12, and below 0 dBFS")

    ffmpeg_path = _require_tool("ffmpeg")
    ffprobe_path = _require_tool("ffprobe")
    trace = _read_json_object(trace_path, "Conversion trace")
    trace_slides, slide_names = _trace_slides(trace)
    raw_probe = _probe_media(video_path, ffprobe_path)
    raw_format_duration_ms = _duration_ms(raw_probe, "raw PowerPoint video")
    raw_video_streams = _streams(raw_probe, "video")
    raw_audio_streams = _streams(raw_probe, "audio")
    if len(raw_video_streams) != 1 or len(raw_audio_streams) != 1:
        raise ValueError(
            "Raw PowerPoint video must contain one video stream and one "
            "narration audio stream"
        )
    raw_duration_ms = _stream_duration_ms(
        raw_video_streams[0],
        fallback_ms=raw_format_duration_ms,
    )
    raw_video_start_ms = _stream_start_ms(raw_video_streams[0])
    raw_audio_start_ms = _stream_start_ms(raw_audio_streams[0])
    start_delta_ms = abs(raw_video_start_ms - raw_audio_start_ms)
    frame_duration_ms = _frame_duration_ms(raw_video_streams[0])
    if (
        abs(raw_video_start_ms) > _START_TIME_TOLERANCE_MS
        or abs(raw_audio_start_ms) > _START_TIME_TOLERANCE_MS
        or start_delta_ms > _START_TIME_TOLERANCE_MS
    ):
        raise ValueError(
            "Raw PowerPoint video audio and video streams must both start at "
            f"zero: video={raw_video_start_ms}ms, audio={raw_audio_start_ms}ms"
        )
    raw_video_timing = _stream_timing_signature(raw_video_streams[0])

    calibration = calibrate_video_timeline(
        slide_names=slide_names,
        pptx_path=pptx_path,
        audio_dir=audio_dir,
        video_path=video_path,
        subtitle_dir=subtitle_dir,
    )
    protected_inputs = {
        pptx_path,
        trace_path,
        video_path,
        *(slide.audio_path.resolve() for slide in calibration.slides),
    }
    aliases = protected_inputs.intersection(outputs)
    if aliases:
        raise ValueError(
            "Sound mix outputs must not overwrite inputs: "
            + ", ".join(str(path) for path in sorted(aliases))
        )
    temporary_stem = _temporary_output(stem_path, ".wav")
    temporary_video = _temporary_output(output_path, ".mp4")
    temporary_report = _temporary_output(report_path, ".json")
    try:
        with tempfile.TemporaryDirectory(prefix="ppt-master-video-sounds-") as raw_dir:
            cues = _resolve_sound_cues(
                pptx_path=pptx_path,
                trace_slides=trace_slides,
                calibration=calibration,
                transition_gain_db=transition_gain_db,
                animation_gain_db=animation_gain_db,
                video_duration_ms=raw_duration_ms,
                temp_dir=Path(raw_dir),
                ffprobe_path=ffprobe_path,
            )
            _render_stem(
                cues=cues,
                duration_ms=raw_duration_ms,
                output_path=temporary_stem,
                ffmpeg_path=ffmpeg_path,
            )
            stem_peak_db = _maximum_volume_db(temporary_stem, ffmpeg_path)
            if stem_peak_db is None or stem_peak_db < -90:
                raise RuntimeError("Rendered SFX stem is silent")
            _mix_video(
                video_path=video_path,
                stem_path=temporary_stem,
                duration_ms=raw_duration_ms,
                limiter_dbfs=limiter_dbfs,
                output_path=temporary_video,
                ffmpeg_path=ffmpeg_path,
            )

        stem_probe = _probe_media(temporary_stem, ffprobe_path)
        mixed_probe = _probe_media(temporary_video, ffprobe_path)
        stem_duration_ms = _duration_ms(stem_probe, "SFX stem")
        mixed_duration_ms = _duration_ms(mixed_probe, "mixed video")
        mixed_video_streams = _streams(mixed_probe, "video")
        mixed_audio_streams = _streams(mixed_probe, "audio")
        if len(mixed_video_streams) != 1 or len(mixed_audio_streams) != 1:
            raise RuntimeError(
                "Mixed video must contain one copied video stream and one audio stream"
            )
        mixed_video_duration_ms = _stream_duration_ms(
            mixed_video_streams[0],
            fallback_ms=mixed_duration_ms,
        )
        mixed_audio_duration_ms = _stream_duration_ms(
            mixed_audio_streams[0],
            fallback_ms=mixed_duration_ms,
        )
        target_samples = _target_sample_count(raw_duration_ms)
        stem_samples = _audio_sample_count(_streams(stem_probe, "audio")[0])
        if stem_samples != target_samples:
            raise RuntimeError(
                "SFX stem sample count does not match the raw video target: "
                f"stem={stem_samples}, target={target_samples}"
            )
        mixed_video_timing = _stream_timing_signature(mixed_video_streams[0])
        if mixed_video_timing != raw_video_timing:
            raise RuntimeError(
                "Mixed output changed the PowerPoint video packet timeline: "
                f"raw={raw_video_timing!r}, mixed={mixed_video_timing!r}"
            )
        duration_tolerance_ms = max(
            frame_duration_ms,
            1024 * 1000 / _OUTPUT_SAMPLE_RATE,
        ) + 1
        if abs(mixed_audio_duration_ms - raw_duration_ms) > duration_tolerance_ms:
            raise RuntimeError(
                "Mixed audio duration does not match the raw video: "
                f"audio={mixed_audio_duration_ms}ms, raw={raw_duration_ms}ms"
            )

        raw_video_hash = _stream_hash(video_path, "0:v:0", ffmpeg_path)
        mixed_video_hash = _stream_hash(temporary_video, "0:v:0", ffmpeg_path)
        if raw_video_hash != mixed_video_hash:
            raise RuntimeError("Mixed output changed the PowerPoint video stream")
        raw_audio_hash = _stream_hash(video_path, "0:a:0", ffmpeg_path)
        mixed_audio_hash = _stream_hash(temporary_video, "0:a:0", ffmpeg_path)
        if raw_audio_hash == mixed_audio_hash:
            raise RuntimeError("Mixed output audio is unchanged from the raw video")
        mixed_peak_db = _maximum_volume_db(temporary_video, ffmpeg_path)
        true_peak_dbfs = _true_peak_dbfs(temporary_video, ffmpeg_path)
        if true_peak_dbfs is None or true_peak_dbfs >= 0:
            raise RuntimeError(
                "Mixed-video audio is silent or clips after encoding: "
                f"true_peak={true_peak_dbfs!r} dBFS"
            )
        verification_correlation = _sound_mix_correlation(
            raw_video_path=video_path,
            mixed_video_path=temporary_video,
            stem_path=temporary_stem,
            cues=cues,
            duration_ms=raw_duration_ms,
            ffmpeg_path=ffmpeg_path,
        )

        trace_output = trace.get("output")
        trace_output_matches_pptx = False
        if isinstance(trace_output, str) and trace_output.strip():
            trace_output_matches_pptx = Path(trace_output).expanduser().resolve() == pptx_path

        report = {
            "schema": "ppt-master.video-sound-mix-report.v1",
            "version": 1,
            "status": "passed",
            "inputs": {
                "pptx": {
                    "path": str(pptx_path),
                    "sha256": _sha256_path(pptx_path),
                },
                "conversion_trace": {
                    "path": str(trace_path),
                    "sha256": _sha256_path(trace_path),
                    "declared_output_matches_pptx": trace_output_matches_pptx,
                },
                "raw_video": {
                    "path": str(video_path),
                    "sha256": _sha256_path(video_path),
                    "duration_ms": raw_duration_ms,
                    "video_start_ms": _stream_start_ms(raw_video_streams[0]),
                    "audio_start_ms": _stream_start_ms(raw_audio_streams[0]),
                    "video_stream_sha256": raw_video_hash,
                    "video_timing": raw_video_timing,
                    "audio_stream_sha256": raw_audio_hash,
                    "video_codec": raw_video_streams[0].get("codec_name"),
                    "audio_codec": raw_audio_streams[0].get("codec_name"),
                },
            },
            "settings": {
                "transition_gain_db": transition_gain_db,
                "animation_gain_db": animation_gain_db,
                "limiter_dbfs": limiter_dbfs,
                "mix_normalize": False,
                "ducking": False,
                "background_music": False,
                "sample_rate": _OUTPUT_SAMPLE_RATE,
                "audio_bitrate": _OUTPUT_AUDIO_BITRATE,
            },
            "timeline": {
                "method": "page narration correlation against raw video audio",
                "powerpoint_timeline_ms": calibration.powerpoint_timeline_ms,
                "minimum_correlation": min(
                    slide.correlation for slide in calibration.slides
                ),
                "slides": [
                    {
                        "slide_num": index,
                        "slide_name": slide.slide_name,
                        "powerpoint_slide_start_ms": slide.powerpoint_slide_start_ms,
                        "powerpoint_narration_start_ms": (
                            slide.powerpoint_narration_start_ms
                        ),
                        "video_slide_start_ms": slide.video_slide_start_ms,
                        "video_narration_start_ms": slide.video_narration_start_ms,
                        "adjustment_ms": slide.adjustment_ms,
                        "correlation": slide.correlation,
                    }
                    for index, slide in enumerate(calibration.slides, 1)
                ],
            },
            "cues": [_cue_report(cue) for cue in cues],
            "outputs": {
                "sfx_stem": {
                    "path": str(stem_path),
                    "sha256": _sha256_path(temporary_stem),
                    "duration_ms": stem_duration_ms,
                    "sample_count": stem_samples,
                    "maximum_volume_db": stem_peak_db,
                },
                "mixed_video": {
                    "path": str(output_path),
                    "sha256": _sha256_path(temporary_video),
                    "duration_ms": mixed_duration_ms,
                    "video_duration_ms": mixed_video_duration_ms,
                    "audio_duration_ms": mixed_audio_duration_ms,
                    "video_stream_sha256": mixed_video_hash,
                    "video_timing": mixed_video_timing,
                    "audio_stream_sha256": mixed_audio_hash,
                    "video_codec": mixed_video_streams[0].get("codec_name"),
                    "audio_codec": mixed_audio_streams[0].get("codec_name"),
                    "maximum_volume_db": mixed_peak_db,
                    "true_peak_dbfs": true_peak_dbfs,
                },
            },
            "validation": {
                "trace_matches_pptx_motion": True,
                "cue_count": len(cues),
                "stem_non_silent": True,
                "mixed_audio_present": True,
                "video_stream_preserved": True,
                "duration_delta_ms": mixed_video_duration_ms - raw_duration_ms,
                "video_timeline_preserved": True,
                "limiter_applied": True,
                "sound_mix_correlation": verification_correlation,
                "minimum_sound_mix_correlation": _MIN_SOUND_MIX_CORRELATION,
            },
        }
        temporary_report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        _publish_outputs(
            [
                (temporary_stem, stem_path),
                (temporary_video, output_path),
                (temporary_report, report_path),
            ]
        )
    finally:
        for temporary in (temporary_stem, temporary_video, temporary_report):
            temporary.unlink(missing_ok=True)

    return SoundMixResult(
        output_path=output_path,
        stem_path=stem_path,
        report_path=report_path,
        cue_count=len(cues),
        verification_correlation=verification_correlation,
        true_peak_dbfs=true_peak_dbfs,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Mix PPTX transition/object-animation sounds into a "
            "PowerPoint-exported narrated video."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="PPT Master project directory")
    parser.add_argument(
        "--pptx",
        required=True,
        help="Final narrated PPTX; relative paths resolve under the project",
    )
    parser.add_argument(
        "--trace",
        required=True,
        help="Final narrated conversion trace; relative paths resolve under the project",
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Raw PowerPoint-exported video; relative paths resolve under the project",
    )
    parser.add_argument(
        "--audio-dir",
        default=None,
        help="Page narration audio directory; default: <project>/audio",
    )
    parser.add_argument(
        "--subtitle-dir",
        default=None,
        help=(
            "Optional page-local SRT directory used to refine calibration; "
            "default: <project>/audio"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Final mixed MP4; default: beside raw video as *_mixed.mp4",
    )
    parser.add_argument(
        "--stem-output",
        default=None,
        help="Independent SFX WAV; default: beside raw video as *_sfx.wav",
    )
    parser.add_argument(
        "--report-output",
        default=None,
        help="Sound mix JSON receipt; default: beside raw video as *_sound_mix.json",
    )
    parser.add_argument(
        "--transition-gain-db",
        type=float,
        default=_DEFAULT_TRANSITION_GAIN_DB,
        help="Transition cue gain in dB (default: -9.1, about 35%%)",
    )
    parser.add_argument(
        "--animation-gain-db",
        type=float,
        default=_DEFAULT_ANIMATION_GAIN_DB,
        help="Object-animation cue gain in dB (default: -12, about 25%%)",
    )
    parser.add_argument(
        "--limiter-dbfs",
        type=float,
        default=_DEFAULT_LIMITER_DBFS,
        help="Final peak limiter ceiling in dBFS (default: -1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing mixed video, stem, and report outputs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = Path(args.project_path).expanduser().resolve()
    if not project_path.is_dir():
        parser.error(f"Project path does not exist: {project_path}")

    pptx_path = _project_input_path(project_path, args.pptx)
    trace_path = _project_input_path(project_path, args.trace)
    video_path = _project_input_path(project_path, args.video)
    audio_dir = _project_output_path(
        project_path,
        args.audio_dir,
        Path("audio"),
    )
    subtitle_dir = _project_output_path(
        project_path,
        args.subtitle_dir,
        Path("audio"),
    )
    default_output = video_path.with_name(f"{video_path.stem}_mixed.mp4")
    default_stem = video_path.with_name(f"{video_path.stem}_sfx.wav")
    default_report = video_path.with_name(f"{video_path.stem}_sound_mix.json")
    output_path = _project_output_path(project_path, args.output, default_output)
    stem_path = _project_output_path(
        project_path,
        args.stem_output,
        default_stem,
    )
    report_path = _project_output_path(
        project_path,
        args.report_output,
        default_report,
    )

    try:
        result = mix_video_sounds(
            project_path,
            pptx_path=pptx_path,
            trace_path=trace_path,
            video_path=video_path,
            audio_dir=audio_dir,
            subtitle_dir=subtitle_dir,
            output_path=output_path,
            stem_path=stem_path,
            report_path=report_path,
            transition_gain_db=args.transition_gain_db,
            animation_gain_db=args.animation_gain_db,
            limiter_dbfs=args.limiter_dbfs,
            force=args.force,
        )
    except (FileNotFoundError, FileExistsError, OSError, RuntimeError, ValueError) as exc:
        print(f"Video sound mix failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"[POSTFLIGHT] status=passed cues={result.cue_count} "
        "video_stream=preserved audio_mix=verified "
        f"correlation={result.verification_correlation:.3f} "
        f"true_peak={result.true_peak_dbfs:.1f}dBFS"
    )
    print(f"[Done] Mixed video: {result.output_path}")
    print(f"[Done] SFX stem: {result.stem_path}")
    print(f"[REPORT] Video sound mix: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
