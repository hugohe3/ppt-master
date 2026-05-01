#!/usr/bin/env python3
"""Generate per-slide narration audio from PPT Master notes.

This script uses `edge-tts` for the same cross-platform behavior on macOS,
Linux, and Windows.

Usage:
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --voice zh-CN-XiaoxiaoNeural
    python3 skills/ppt-master/scripts/notes_to_audio.py --list-common-voices
    python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale zh-CN

Dependency:
    python3 -m pip install edge-tts
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path


COMMON_VOICES = [
    ("zh-CN", "zh-CN-XiaoxiaoNeural", "女声，普通话，清晰自然，默认推荐"),
    ("zh-CN", "zh-CN-XiaoyiNeural", "女声，普通话，明亮"),
    ("zh-CN", "zh-CN-YunjianNeural", "男声，普通话，稳重"),
    ("zh-CN", "zh-CN-YunxiNeural", "男声，普通话，年轻"),
    ("zh-CN", "zh-CN-YunxiaNeural", "男声，普通话，少年感"),
    ("zh-CN", "zh-CN-YunyangNeural", "男声，普通话，播报感"),
    ("zh-HK", "zh-HK-HiuGaaiNeural", "女声，粤语"),
    ("zh-HK", "zh-HK-WanLungNeural", "男声，粤语"),
    ("zh-TW", "zh-TW-HsiaoChenNeural", "女声，台湾普通话"),
    ("zh-TW", "zh-TW-YunJheNeural", "男声，台湾普通话"),
    ("en-US", "en-US-JennyNeural", "女声，美式英语"),
    ("en-US", "en-US-GuyNeural", "男声，美式英语"),
    ("en-GB", "en-GB-SoniaNeural", "女声，英式英语"),
    ("en-GB", "en-GB-RyanNeural", "男声，英式英语"),
]


def spoken_text(markdown: str) -> str:
    """Return narration text exactly from notes, except Markdown headings."""
    lines: list[str] = []
    for raw in markdown.splitlines():
        if raw.lstrip().startswith("#"):
            continue
        line = raw.rstrip()
        if not line.strip():
            if lines and lines[-1] != "":
                lines.append("")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _edge_rate(rate: str) -> str:
    """Normalize a user-provided rate into edge-tts format."""
    value = rate.strip()
    if not value:
        return "+0%"
    if value.endswith("%"):
        if value[0] not in "+-":
            return f"+{value}"
        return value
    if re.fullmatch(r"[+-]?\d+", value):
        number = int(value)
        return f"{number:+d}%"
    return value


async def run_edge_tts(text: str, output_path: Path, *, voice: str, rate: str) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency `edge-tts`. Install it with: "
            "python3 -m pip install edge-tts"
        ) from exc

    communicate = edge_tts.Communicate(text, voice=voice, rate=_edge_rate(rate))
    await communicate.save(str(output_path))


def print_common_voices() -> None:
    print("Common edge-tts voices:")
    print("Locale   Voice                         Notes")
    print("------   ----------------------------  ----------------")
    for locale, voice, notes in COMMON_VOICES:
        print(f"{locale:<8} {voice:<29} {notes}")


async def print_edge_voices(locale: str | None = None) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency `edge-tts`. Install it with: "
            "python3 -m pip install edge-tts"
        ) from exc

    manager = await edge_tts.VoicesManager.create()
    voices = manager.voices
    if locale:
        voices = [voice for voice in voices if voice.get("Locale") == locale]
    for voice in sorted(voices, key=lambda item: (item.get("Locale", ""), item.get("ShortName", ""))):
        short_name = voice.get("ShortName", "")
        voice_locale = voice.get("Locale", "")
        gender = voice.get("Gender", "")
        friendly = voice.get("FriendlyName", "")
        print(f"{voice_locale:<8} {short_name:<34} {gender:<8} {friendly}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", type=Path, nargs="?")
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument(
        "--voice",
        default=None,
        help="edge-tts voice ShortName (required). Run --list-voices --locale <locale> to discover voices, or follow the generate-audio workflow for a locale-aware recommendation.",
    )
    parser.add_argument(
        "--rate",
        default="+0%",
        help='edge-tts speaking rate, e.g. "+0%%", "-10%%", "+15%%" (default: +0%%)',
    )
    parser.add_argument("--list-common-voices", action="store_true", help="print a curated voice list and exit")
    parser.add_argument("--list-voices", action="store_true", help="query edge-tts voices and exit")
    parser.add_argument("--locale", default=None, help='filter --list-voices by locale, e.g. "zh-CN"')
    args = parser.parse_args()

    if args.list_common_voices:
        print_common_voices()
        return 0

    if args.list_voices:
        try:
            asyncio.run(print_edge_voices(args.locale))
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.project_path is None:
        parser.error("project_path is required unless --list-voices or --list-common-voices is used")

    if not args.voice:
        parser.error(
            "--voice is required. Run --list-voices --locale <locale> to discover voices "
            "(e.g. --locale zh-CN), or follow skills/ppt-master/workflows/generate-audio.md "
            "for an AI-curated recommendation."
        )

    project = args.project_path
    notes_dir = project / "notes"
    output_dir = args.output or (project / "audio")
    output_dir.mkdir(parents=True, exist_ok=True)

    note_files = [
        path for path in sorted(notes_dir.glob("*.md"))
        if path.name != "total.md"
    ]
    if not note_files:
        print(f"error: no per-slide notes found in {notes_dir}", file=sys.stderr)
        return 2

    generated = 0
    for note_path in note_files:
        text = spoken_text(note_path.read_text(encoding="utf-8"))
        if not text:
            print(f"[skip] {note_path.name}: empty spoken text")
            continue
        output_path = output_dir / f"{note_path.stem}.mp3"
        try:
            asyncio.run(run_edge_tts(text, output_path, voice=args.voice, rate=args.rate))
        except Exception as exc:
            print(f"error: failed to generate {output_path}: {exc}", file=sys.stderr)
            return 1
        generated += 1
        print(f"[OK] {output_path}")

    print(f"[Done] Generated {generated}/{len(note_files)} audio file(s): {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
