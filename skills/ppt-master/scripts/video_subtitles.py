#!/usr/bin/env python3
"""
PPT Master - Final Video Subtitles

Align the exact narration text frozen in page-local Edge SRT files against the
audio track of a finished PowerPoint-exported video. This produces a delivery
SRT from the actual video timeline without rewriting speaker notes or relying
on theoretical slide offsets.

Usage:
    python3 scripts/video_subtitles.py <project_path> --video <video> --language <language>

Examples:
    python3 scripts/video_subtitles.py projects/demo --video exports/demo.mp4 --language zh --force

Dependencies:
    ffmpeg
    python3 -m pip install stable-ts
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()


DEFAULT_MAX_CHARS = 20
_TIMING_RE = re.compile(
    r"^(?P<start>\d+:\d{2}:\d{2},\d{3})\s+-->\s+"
    r"(?P<end>\d+:\d{2}:\d{2},\d{3})(?:\s+.*)?$"
)
_CLAUSE_END = frozenset("，,；;：:")


@dataclass(frozen=True)
class SubtitleCue:
    """One validated SRT cue."""

    start_ms: int
    end_ms: int
    text: str


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


def _parse_srt(path: Path) -> list[SubtitleCue]:
    """Read one strict, non-overlapping SRT file."""
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
        cue_text = re.sub(r"\s+", " ", " ".join(lines[2:])).strip()
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


def _display_length(text: str) -> int:
    return sum(not character.isspace() for character in text)


def _hard_split(text: str, max_chars: int) -> list[str]:
    """Split an overlong clause without dropping characters."""
    output: list[str] = []
    remaining = text.strip()
    while _display_length(remaining) > max_chars:
        visible = 0
        split_at = 0
        whitespace_split = 0
        for index, character in enumerate(remaining, 1):
            if character.isspace():
                whitespace_split = index
                continue
            visible += 1
            if visible > max_chars:
                break
            split_at = index
        if whitespace_split and whitespace_split <= split_at:
            split_at = whitespace_split
        if split_at <= 0:
            raise ValueError("Unable to split an overlong subtitle clause")
        output.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        output.append(remaining)
    return output


def _split_sentence(text: str, max_chars: int) -> list[str]:
    """Keep one sentence unless its display length requires clause splitting."""
    sentence = re.sub(r"\s+", " ", text).strip()
    if _display_length(sentence) <= max_chars:
        return [sentence]

    clauses: list[str] = []
    start = 0
    for index, character in enumerate(sentence):
        if character not in _CLAUSE_END:
            continue
        clause = sentence[start:index + 1].strip()
        if clause:
            clauses.append(clause)
        start = index + 1
    tail = sentence[start:].strip()
    if tail:
        clauses.append(tail)

    atoms = [
        part
        for clause in clauses
        for part in _hard_split(clause, max_chars)
    ]
    output: list[str] = []
    for atom in atoms:
        if not output:
            output.append(atom)
            continue
        candidate = f"{output[-1]}{atom}"
        if _display_length(candidate) <= max_chars:
            output[-1] = candidate
        else:
            output.append(atom)
    return output


def _page_subtitle_paths(subtitle_dir: Path) -> list[Path]:
    """Resolve the ordered page-local SRT set without reading notes."""
    paths = [
        path
        for path in sorted(subtitle_dir.glob("*.srt"))
        if path.stem != "total"
    ]
    if not paths:
        raise FileNotFoundError(
            f"No page-local Edge SRT files found under {subtitle_dir}"
        )
    return paths


def _frozen_transcript_lines(
    subtitle_dir: Path,
    max_chars: int,
) -> list[str]:
    """Return display lines derived from the exact text used for TTS."""
    lines: list[str] = []
    for path in _page_subtitle_paths(subtitle_dir):
        for cue in _parse_srt(path):
            lines.extend(_split_sentence(cue.text, max_chars))
    if not lines:
        raise ValueError("The page-local SRT set contains no narration text")
    return lines


def _require_stable_whisper() -> Any:
    try:
        import stable_whisper
    except ImportError as exc:
        raise RuntimeError(
            "Final-video subtitle alignment requires stable-ts. "
            "Install it with: python3 -m pip install stable-ts"
        ) from exc
    return stable_whisper


def _text_key(text: str) -> str:
    return "".join(character for character in text if not character.isspace())


def align_video_subtitles(
    *,
    video_path: Path,
    subtitle_dir: Path,
    output_path: Path,
    language: str,
    model_name: str,
    device: str | None,
    max_chars: int,
    force: bool,
) -> tuple[int, int]:
    """Align frozen narration text to the final video's actual audio track."""
    if not video_path.is_file():
        raise FileNotFoundError(f"Finished video does not exist: {video_path}")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "Final-video subtitle alignment requires ffmpeg on PATH"
        )
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")
    if output_path.resolve() == video_path.resolve():
        raise ValueError("Subtitle output must not overwrite the finished video")
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Output already exists: {output_path}; pass --force to replace it"
        )

    transcript_lines = _frozen_transcript_lines(
        subtitle_dir,
        max_chars,
    )
    transcript = "\n".join(transcript_lines)
    stable_whisper = _require_stable_whisper()
    load_options: dict[str, Any] = {}
    if device:
        load_options["device"] = device
    model = stable_whisper.load_model(model_name, **load_options)
    result = model.align(
        str(video_path),
        transcript,
        language=language,
        original_split=True,
    )
    if result is None:
        raise RuntimeError("stable-ts could not align the narration transcript")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}.",
        suffix=".srt",
        dir=str(output_path.parent),
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        result.to_srt_vtt(
            str(temporary_path),
            segment_level=True,
            word_level=False,
        )
        output_cues = _parse_srt(temporary_path)
        output_text = _text_key("".join(cue.text for cue in output_cues))
        expected_text = _text_key("".join(transcript_lines))
        if output_text != expected_text:
            raise RuntimeError(
                "Aligned subtitle text differs from the frozen TTS transcript; "
                "the final SRT was not published"
            )
        if len(output_cues) != len(transcript_lines):
            raise RuntimeError(
                "stable-ts did not preserve the requested sentence/line "
                "boundaries; the final SRT was not published"
            )
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return len(transcript_lines), output_cues[-1].end_ms


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", type=Path, help="Project directory")
    parser.add_argument(
        "--video",
        required=True,
        help="Finished PowerPoint-exported video; relative paths are project-relative",
    )
    parser.add_argument(
        "--language",
        required=True,
        help="Narration language passed to stable-ts, e.g. zh, en, ja, or ko",
    )
    parser.add_argument(
        "--subtitle-dir",
        default=None,
        help="Page-local Edge SRT directory; default: <project>/notes/subtitles",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Final SRT path; default: beside the video with the same stem",
    )
    parser.add_argument(
        "--model",
        default="base",
        help="Whisper model used only for forced alignment (default: base)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional stable-ts device, e.g. cpu or cuda",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help="Maximum non-space characters per final subtitle cue (default: 20)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing final SRT",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = args.project_path.resolve()
    if not project_path.is_dir():
        parser.error(f"Project path does not exist: {project_path}")

    video_path = Path(args.video)
    if not video_path.is_absolute():
        video_path = project_path / video_path
    video_path = video_path.resolve()
    subtitle_dir = (
        Path(args.subtitle_dir)
        if args.subtitle_dir
        else Path("notes/subtitles")
    )
    if not subtitle_dir.is_absolute():
        subtitle_dir = project_path / subtitle_dir
    output_path = Path(args.output) if args.output else video_path.with_suffix(".srt")
    if not output_path.is_absolute():
        output_path = project_path / output_path

    try:
        cue_count, final_end_ms = align_video_subtitles(
            video_path=video_path,
            subtitle_dir=subtitle_dir.resolve(),
            output_path=output_path.resolve(),
            language=args.language,
            model_name=args.model,
            device=args.device,
            max_chars=args.max_chars,
            force=args.force,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output_path.resolve())
    print(
        f"Aligned {cue_count} final-video subtitle cue(s); "
        f"last cue ends at {final_end_ms / 1000:.3f}s",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
