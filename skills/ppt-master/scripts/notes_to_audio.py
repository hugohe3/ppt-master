#!/usr/bin/env python3
"""Generate per-slide narration audio from PPT Master notes.

This script uses provider backends for the same per-slide output contract on
macOS, Linux, and Windows. `edge-tts` remains the default no-key backend.

Usage:
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --voice zh-CN-XiaoxiaoNeural
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider elevenlabs --voice-id <voice_id>
    python3 skills/ppt-master/scripts/notes_to_audio.py --list-common-voices
    python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale zh-CN

Dependencies:
    python3 -m pip install edge-tts
    ELEVENLABS_API_KEY=<key> for --provider elevenlabs
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

from tts_backends import backend_edge, backend_elevenlabs


@dataclass(frozen=True)
class AudioBackend:
    provider: str
    extension: str


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", type=Path, nargs="?")
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument(
        "--provider",
        choices=["edge", "elevenlabs"],
        default="edge",
        help="audio generation backend (default: edge)",
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="edge-tts voice ShortName. For elevenlabs, --voice-id is preferred.",
    )
    parser.add_argument(
        "--voice-id",
        default=None,
        help="ElevenLabs voice ID. If omitted for --provider elevenlabs, --voice is used as a fallback.",
    )
    parser.add_argument(
        "--rate",
        default="+0%",
        help='edge-tts speaking rate, e.g. "+0%%", "-10%%", "+15%%" (default: +0%%). Ignored by elevenlabs.',
    )
    parser.add_argument(
        "--elevenlabs-api-key-env",
        default="ELEVENLABS_API_KEY",
        help="environment variable containing the ElevenLabs API key (default: ELEVENLABS_API_KEY)",
    )
    parser.add_argument(
        "--elevenlabs-model",
        default="eleven_multilingual_v2",
        help="ElevenLabs TTS model ID (default: eleven_multilingual_v2)",
    )
    parser.add_argument(
        "--elevenlabs-output-format",
        default="mp3_44100_128",
        help="ElevenLabs output format (default: mp3_44100_128)",
    )
    parser.add_argument(
        "--elevenlabs-stability",
        type=float,
        default=None,
        help="optional ElevenLabs voice stability override, 0.0-1.0",
    )
    parser.add_argument(
        "--elevenlabs-similarity-boost",
        type=float,
        default=None,
        help="optional ElevenLabs similarity boost override, 0.0-1.0",
    )
    parser.add_argument(
        "--elevenlabs-style",
        type=float,
        default=None,
        help="optional ElevenLabs style exaggeration override, 0.0-1.0",
    )
    parser.add_argument(
        "--elevenlabs-speaker-boost",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="optionally override ElevenLabs speaker boost",
    )
    parser.add_argument("--list-common-voices", action="store_true", help="print a curated voice list and exit")
    parser.add_argument("--list-voices", action="store_true", help="query provider voices and exit")
    parser.add_argument("--locale", default=None, help='filter --list-voices by locale, e.g. "zh-CN"')
    args = parser.parse_args()

    if args.list_common_voices:
        backend_edge.print_common_voices()
        return 0

    if args.list_voices:
        try:
            if args.provider == "elevenlabs":
                backend_elevenlabs.print_voices(backend_elevenlabs.read_api_key(args.elevenlabs_api_key_env))
            else:
                asyncio.run(backend_edge.print_voices(args.locale))
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.project_path is None:
        parser.error("project_path is required unless --list-voices or --list-common-voices is used")

    if args.provider == "edge" and not args.voice:
        parser.error(
            "--voice is required for --provider edge. Run --list-voices --locale <locale> to discover voices "
            "(e.g. --locale zh-CN), or follow skills/ppt-master/workflows/generate-audio.md "
            "for an AI-curated recommendation."
        )
        raise AssertionError("unreachable")

    if args.provider == "elevenlabs":
        voice_id = args.voice_id or args.voice
        if not voice_id:
            parser.error("--voice-id is required for --provider elevenlabs")
            raise AssertionError("unreachable")
        try:
            api_key = backend_elevenlabs.read_api_key(args.elevenlabs_api_key_env)
            extension = backend_elevenlabs.output_extension(args.elevenlabs_output_format)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        backend = AudioBackend(provider=args.provider, extension=extension)
    else:
        voice_id = args.voice
        api_key = ""
        backend = AudioBackend(provider=args.provider, extension=backend_edge.edge_output_extension())

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
        output_path = output_dir / f"{note_path.stem}{backend.extension}"
        try:
            if backend.provider == "elevenlabs":
                backend_elevenlabs.generate(
                    text,
                    output_path,
                    api_key=api_key,
                    voice_id=voice_id,
                    model=args.elevenlabs_model,
                    output_format=args.elevenlabs_output_format,
                    stability=args.elevenlabs_stability,
                    similarity_boost=args.elevenlabs_similarity_boost,
                    style=args.elevenlabs_style,
                    speaker_boost=args.elevenlabs_speaker_boost,
                )
            else:
                asyncio.run(backend_edge.generate(text, output_path, voice=args.voice, rate=args.rate))
        except Exception as exc:
            print(f"error: failed to generate {output_path}: {exc}", file=sys.stderr)
            return 1
        generated += 1
        print(f"[OK] {output_path}")

    print(f"[Done] Generated {generated}/{len(note_files)} audio file(s): {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
