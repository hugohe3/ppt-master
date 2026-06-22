#!/usr/bin/env python3
"""Normalize per-slide narration files to a consistent EBU R128 loudness target."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


SUPPORTED_SUFFIXES = {".mp3", ".m4a", ".wav"}


def _run(command: list[str]) -> str:
    # FFmpeg can emit GBK/UTF-8-mixed metadata on Windows when narration filenames
    # contain CJK characters. Decode defensively because only its JSON payload is parsed.
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stderr = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode:
        raise RuntimeError(stderr[-2000:])
    return stderr


def _has_loudnorm(ffmpeg: str) -> bool:
    try:
        completed = subprocess.run(
            [ffmpeg, "-hide_banner", "-filters"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0 and "loudnorm" in (completed.stdout + completed.stderr)


def _find_ffmpeg(explicit_path: str | None) -> str:
    candidates: list[str] = []
    if explicit_path:
        candidates.append(explicit_path)

    try:
        import imageio_ffmpeg  # type: ignore

        candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        candidates.append(system_ffmpeg)

    for candidate in candidates:
        if _has_loudnorm(candidate):
            return candidate

    raise RuntimeError(
        "No FFmpeg binary with the loudnorm filter is available. Install imageio-ffmpeg "
        "(`python -m pip install imageio-ffmpeg`) or pass --ffmpeg <full-ffmpeg-path>."
    )


def _read_measurement(stderr: str) -> dict[str, str]:
    matches = re.findall(r"\{\s*\"input_i\".*?\}", stderr, flags=re.DOTALL)
    if not matches:
        raise RuntimeError(f"FFmpeg did not return loudness measurement data:\n{stderr[-1200:]}")
    return json.loads(matches[-1])


def _output_codec(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".mp3":
        return ["-c:a", "libmp3lame", "-b:a", "128k"]
    if suffix == ".m4a":
        return ["-c:a", "aac", "-b:a", "128k"]
    if suffix == ".wav":
        return ["-c:a", "pcm_s16le"]
    raise ValueError(f"Unsupported narration format: {path.suffix}")


def _normalize_one(
    ffmpeg: str,
    source: Path,
    destination: Path,
    target_lufs: float,
    true_peak: float,
    lra: float,
) -> tuple[float, float]:
    base_filter = f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}:print_format=json"
    measured = _read_measurement(
        _run([ffmpeg, "-hide_banner", "-i", str(source), "-af", base_filter, "-f", "null", "-"])
    )
    second_pass = (
        f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}:"
        f"measured_I={measured['input_i']}:measured_LRA={measured['input_lra']}:"
        f"measured_TP={measured['input_tp']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true:print_format=summary"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            ffmpeg,
            "-hide_banner",
            "-y",
            "-i",
            str(source),
            "-af",
            second_pass,
            "-ar",
            "32000",
            "-ac",
            "1",
            *_output_codec(destination),
            str(destination),
        ]
    )
    verified = _read_measurement(
        _run([ffmpeg, "-hide_banner", "-i", str(destination), "-af", base_filter, "-f", "null", "-"])
    )
    return float(measured["input_i"]), float(verified["input_i"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_dir", type=Path, help="Directory containing one audio file per slide")
    parser.add_argument("--output", type=Path, help="Destination directory; defaults to <audio_dir>_normalized")
    parser.add_argument("--target-lufs", type=float, default=-16.0, help="Integrated loudness target (default: -16)")
    parser.add_argument("--true-peak", type=float, default=-1.5, help="Maximum true peak in dBTP (default: -1.5)")
    parser.add_argument("--lra", type=float, default=11.0, help="Loudness range target (default: 11)")
    parser.add_argument("--ffmpeg", help="Path to a full FFmpeg binary with the loudnorm filter")
    args = parser.parse_args()

    source_dir = args.audio_dir.resolve()
    if not source_dir.is_dir():
        parser.error(f"Audio directory not found: {source_dir}")
    destination_dir = (args.output or source_dir.with_name(f"{source_dir.name}_normalized")).resolve()
    if destination_dir == source_dir:
        parser.error("--output must be a different directory from audio_dir; source audio is preserved.")

    sources = sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES)
    if not sources:
        parser.error("No .mp3, .m4a, or .wav narration files found.")

    ffmpeg = _find_ffmpeg(args.ffmpeg)
    results = []
    for source in sources:
        before, after = _normalize_one(ffmpeg, source, destination_dir / source.name, args.target_lufs, args.true_peak, args.lra)
        results.append({"file": source.name, "before_lufs": round(before, 2), "after_lufs": round(after, 2)})
        print(f"[OK] {source.name}: {before:.2f} LUFS -> {after:.2f} LUFS")

    print(
        json.dumps(
            {
                "files": len(results),
                "output": str(destination_dir),
                "target_lufs": args.target_lufs,
                "target_true_peak_dbtp": args.true_peak,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"[Error] {error}", file=sys.stderr)
        raise SystemExit(1)
