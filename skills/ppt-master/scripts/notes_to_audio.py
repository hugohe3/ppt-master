#!/usr/bin/env python3
"""Generate per-slide narration audio from PPT Master notes.

This script uses provider backends for the same per-slide output contract on
macOS, Linux, and Windows. `edge-tts` remains the default no-key backend and
also writes one compact, word-timed SRT file per slide from the same TTS stream.

Usage:
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --voice zh-CN-XiaoxiaoNeural
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider elevenlabs --voice-id <voice_id>
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider minimax --voice-id <voice_id>
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider qwen --voice-id <voice>
    python3 skills/ppt-master/scripts/notes_to_audio.py <project_path> --provider cosyvoice --voice-id <voice>
    python3 skills/ppt-master/scripts/notes_to_audio.py --list-common-voices
    python3 skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale zh-CN

Dependencies:
    python3 -m pip install edge-tts
    ELEVENLABS_API_KEY=<key> for --provider elevenlabs
    MINIMAX_API_KEY=<key> for --provider minimax
    QWEN_API_KEY or DASHSCOPE_API_KEY=<key> for --provider qwen
    COSYVOICE_API_KEY or DASHSCOPE_API_KEY=<key> for --provider cosyvoice
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from console_encoding import configure_utf8_stdio
from config import load_prefixed_env_file
from tts_backends import (
    backend_cosyvoice,
    backend_edge,
    backend_elevenlabs,
    backend_minimax,
    backend_qwen,
)

configure_utf8_stdio()

DEFAULT_EDGE_CONCURRENCY = 3


@dataclass(frozen=True)
class AudioBackend:
    provider: str
    extension: str
    api_key: str = ""
    voice_id: str = ""


@dataclass(frozen=True)
class AudioJob:
    note_path: Path
    text: str
    output_path: Path


def _load_tts_env_file() -> None:
    """Load TTS-related keys from the first .env file, without overriding shell env."""
    load_prefixed_env_file((
        "ELEVENLABS_",
        "MINIMAX_",
        "QWEN_",
        "DASHSCOPE_",
        "COSYVOICE_",
    ))


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


def _prepare_audio_jobs(
    note_files: list[Path],
    output_dir: Path,
    extension: str,
) -> list[AudioJob]:
    """Read non-empty per-slide notes into ordered audio jobs."""
    jobs: list[AudioJob] = []
    for note_path in note_files:
        text = spoken_text(note_path.read_text(encoding="utf-8"))
        if not text:
            print(f"[skip] {note_path.name}: empty spoken text")
            continue
        jobs.append(AudioJob(
            note_path=note_path,
            text=text,
            output_path=output_dir / f"{note_path.stem}{extension}",
        ))
    return jobs


async def _generate_edge_jobs(
    jobs: list[AudioJob],
    subtitle_dir: Path,
    *,
    voice: str,
    rate: str,
    subtitle_max_chars: int,
    concurrency: int,
) -> list[BaseException | None]:
    """Generate ordered Edge jobs with bounded slide-level concurrency."""
    semaphore = asyncio.Semaphore(concurrency)

    async def generate_job(job: AudioJob) -> None:
        async with semaphore:
            await backend_edge.generate(
                job.text,
                job.output_path,
                voice=voice,
                rate=rate,
                subtitle_path=subtitle_dir / f"{job.note_path.stem}.srt",
                subtitle_max_chars=subtitle_max_chars,
            )

    raw_results = await asyncio.gather(
        *(generate_job(job) for job in jobs),
        return_exceptions=True,
    )
    return [
        result if isinstance(result, BaseException) else None
        for result in raw_results
    ]


def main() -> int:
    _load_tts_env_file()

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", type=Path, nargs="?")
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument(
        "--provider",
        choices=["edge", "elevenlabs", "minimax", "qwen", "cosyvoice"],
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
        help="provider voice ID/name. If omitted for cloud providers, --voice is used as a fallback.",
    )
    parser.add_argument(
        "--rate",
        default="+0%",
        help='edge-tts speaking rate, e.g. "+0%%", "-10%%", "+15%%" (default: +0%%). Ignored by cloud providers.',
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_EDGE_CONCURRENCY,
        help="maximum concurrent Edge slide requests (default: 3; ignored by cloud providers)",
    )
    parser.add_argument(
        "--subtitle-max-chars",
        type=int,
        default=backend_edge.DEFAULT_SUBTITLE_MAX_CHARS,
        help="maximum visible characters per Edge subtitle cue (default: 20)",
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
    parser.add_argument("--minimax-api-key-env", default="MINIMAX_API_KEY",
                        help="environment variable containing the MiniMax API key")
    parser.add_argument("--minimax-model", default="speech-2.8-hd",
                        help="MiniMax T2A model ID (default: speech-2.8-hd)")
    parser.add_argument("--minimax-base-url", default=None,
                        help="MiniMax T2A endpoint or base URL")
    parser.add_argument("--minimax-output-format", default="mp3", choices=["mp3", "wav"],
                        help="MiniMax audio format for PPT narration (default: mp3)")
    parser.add_argument("--minimax-sample-rate", type=int, default=32000,
                        help="MiniMax sample rate (default: 32000)")
    parser.add_argument("--minimax-bitrate", type=int, default=128000,
                        help="MiniMax bitrate in bps (default: 128000)")
    parser.add_argument("--minimax-channel", type=int, default=1,
                        help="MiniMax channel count (default: 1)")
    parser.add_argument("--minimax-speed", type=float, default=1.0,
                        help="MiniMax speaking speed (default: 1.0)")
    parser.add_argument("--minimax-volume", type=float, default=1.0,
                        help="MiniMax volume multiplier (default: 1.0)")
    parser.add_argument("--minimax-pitch", type=int, default=0,
                        help="MiniMax pitch adjustment (default: 0)")
    parser.add_argument("--minimax-language-boost", default="auto",
                        help="MiniMax language boost (default: auto)")
    parser.add_argument("--qwen-api-key-env", default=None,
                        help="environment variable containing the Qwen/DashScope API key")
    parser.add_argument("--qwen-model", default="qwen3-tts-flash",
                        help="Qwen TTS model ID (default: qwen3-tts-flash)")
    parser.add_argument("--qwen-base-url", default=None,
                        help="Qwen TTS endpoint or base URL")
    parser.add_argument("--qwen-language-type", default="Chinese",
                        help="Qwen language_type, e.g. Chinese or English (default: Chinese)")
    parser.add_argument("--qwen-instructions", default=None,
                        help="optional Qwen instruction text for supported models")
    parser.add_argument("--qwen-optimize-instructions", action=argparse.BooleanOptionalAction,
                        default=None, help="optionally ask Qwen to optimize instructions")
    parser.add_argument("--cosyvoice-api-key-env", default="COSYVOICE_API_KEY",
                        help="environment variable containing the CosyVoice/DashScope API key")
    parser.add_argument("--cosyvoice-model", default="cosyvoice-v3-flash",
                        help="CosyVoice model ID (default: cosyvoice-v3-flash)")
    parser.add_argument("--cosyvoice-base-url", default=None,
                        help="CosyVoice SpeechSynthesizer endpoint or base URL")
    parser.add_argument("--cosyvoice-output-format", default="mp3", choices=["mp3", "wav"],
                        help="CosyVoice audio format for PPT narration (default: mp3)")
    parser.add_argument("--cosyvoice-sample-rate", type=int, default=24000,
                        help="CosyVoice sample rate (default: 24000)")
    parser.add_argument("--cosyvoice-volume", type=int, default=None,
                        help="optional CosyVoice volume, 0-100")
    parser.add_argument("--cosyvoice-rate", type=float, default=None,
                        help="optional CosyVoice speaking rate, 0.5-2.0")
    parser.add_argument("--cosyvoice-pitch", type=float, default=None,
                        help="optional CosyVoice pitch multiplier, 0.5-2.0")
    parser.add_argument("--cosyvoice-instruction", default=None,
                        help="optional CosyVoice instruction text for supported voices/models")
    parser.add_argument("--cosyvoice-language-hint", default=None,
                        help="optional CosyVoice language hint, e.g. zh, en, ja")
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
                backend_elevenlabs.print_voices(
                    backend_elevenlabs.read_elevenlabs_api_key(args.elevenlabs_api_key_env)
                )
            elif args.provider == "minimax":
                backend_minimax.print_voices()
            elif args.provider == "qwen":
                backend_qwen.print_voices()
            elif args.provider == "cosyvoice":
                backend_cosyvoice.print_voices()
            else:
                asyncio.run(backend_edge.print_voices(args.locale))
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.project_path is None:
        parser.error("project_path is required unless --list-voices or --list-common-voices is used")

    voice_id = args.voice_id or args.voice

    if args.provider == "edge" and not args.voice:
        parser.error(
            "--voice is required for --provider edge. Run --list-voices --locale <locale> to discover voices "
            "(e.g. --locale zh-CN), or follow skills/ppt-master/workflows/stages/generate-audio.md "
            "for an AI-curated recommendation."
        )
        raise AssertionError("unreachable")

    if args.provider != "edge" and not voice_id:
        parser.error(f"--voice-id is required for --provider {args.provider}")
        raise AssertionError("unreachable")

    if args.subtitle_max_chars < 1:
        parser.error("--subtitle-max-chars must be at least 1")
        raise AssertionError("unreachable")

    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1")
        raise AssertionError("unreachable")

    if args.provider == "elevenlabs":
        if not voice_id:
            parser.error("--voice-id is required for --provider elevenlabs")
            raise AssertionError("unreachable")
        try:
            api_key = backend_elevenlabs.read_elevenlabs_api_key(args.elevenlabs_api_key_env)
            extension = backend_elevenlabs.output_extension(args.elevenlabs_output_format)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        backend = AudioBackend(provider=args.provider, extension=extension, api_key=api_key, voice_id=voice_id)
    elif args.provider == "minimax":
        try:
            api_key = backend_minimax.read_minimax_api_key(args.minimax_api_key_env)
            extension = backend_minimax.output_extension(args.minimax_output_format)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        backend = AudioBackend(provider=args.provider, extension=extension, api_key=api_key, voice_id=voice_id)
    elif args.provider == "qwen":
        try:
            api_key = backend_qwen.read_qwen_api_key(args.qwen_api_key_env)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        backend = AudioBackend(
            provider=args.provider,
            extension=backend_qwen.output_extension(),
            api_key=api_key,
            voice_id=voice_id,
        )
    elif args.provider == "cosyvoice":
        try:
            api_key = backend_cosyvoice.read_cosyvoice_api_key(args.cosyvoice_api_key_env)
            extension = backend_cosyvoice.output_extension(args.cosyvoice_output_format)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        backend = AudioBackend(provider=args.provider, extension=extension, api_key=api_key, voice_id=voice_id)
    else:
        backend = AudioBackend(provider=args.provider, extension=backend_edge.edge_output_extension(), voice_id=args.voice)

    project = args.project_path
    notes_dir = project / "notes"
    output_dir = args.output or (project / "audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    subtitle_dir = notes_dir / "subtitles"
    if backend.provider == "edge":
        subtitle_dir.mkdir(parents=True, exist_ok=True)

    note_files = [
        path for path in sorted(notes_dir.glob("*.md"))
        if path.name != "total.md"
    ]
    if not note_files:
        print(f"error: no per-slide notes found in {notes_dir}", file=sys.stderr)
        return 2

    jobs = _prepare_audio_jobs(note_files, output_dir, backend.extension)
    generated = 0
    if backend.provider == "edge":
        print(
            f"[Edge] Generating {len(jobs)} audio/SRT pair(s) "
            f"with concurrency={args.concurrency}"
        )
        try:
            results = asyncio.run(_generate_edge_jobs(
                jobs,
                subtitle_dir,
                voice=args.voice,
                rate=args.rate,
                subtitle_max_chars=args.subtitle_max_chars,
                concurrency=args.concurrency,
            ))
        except Exception as exc:
            print(f"error: Edge audio generation failed: {exc}", file=sys.stderr)
            return 1

        failed = False
        for job, result in zip(jobs, results):
            subtitle_path = subtitle_dir / f"{job.note_path.stem}.srt"
            if result is not None:
                print(
                    f"error: failed to generate {job.output_path}: {result}",
                    file=sys.stderr,
                )
                failed = True
                continue
            generated += 1
            print(f"[OK] {job.output_path}")
            print(f"     {subtitle_path}")
        if failed:
            return 1
    else:
        for job in jobs:
            output_path = job.output_path
            text = job.text
            try:
                if backend.provider == "elevenlabs":
                    backend_elevenlabs.generate(
                        text,
                        output_path,
                        api_key=backend.api_key,
                        voice_id=backend.voice_id,
                        model=args.elevenlabs_model,
                        output_format=args.elevenlabs_output_format,
                        stability=args.elevenlabs_stability,
                        similarity_boost=args.elevenlabs_similarity_boost,
                        style=args.elevenlabs_style,
                        speaker_boost=args.elevenlabs_speaker_boost,
                    )
                elif backend.provider == "minimax":
                    backend_minimax.generate(
                        text,
                        output_path,
                        api_key=backend.api_key,
                        voice_id=backend.voice_id,
                        model=args.minimax_model,
                        audio_format=args.minimax_output_format,
                        sample_rate=args.minimax_sample_rate,
                        bitrate=args.minimax_bitrate,
                        channel=args.minimax_channel,
                        speed=args.minimax_speed,
                        volume=args.minimax_volume,
                        pitch=args.minimax_pitch,
                        language_boost=args.minimax_language_boost,
                        base_url=args.minimax_base_url,
                    )
                elif backend.provider == "qwen":
                    backend_qwen.generate(
                        text,
                        output_path,
                        api_key=backend.api_key,
                        voice_id=backend.voice_id,
                        model=args.qwen_model,
                        language_type=args.qwen_language_type,
                        instructions=args.qwen_instructions,
                        optimize_instructions=args.qwen_optimize_instructions,
                        base_url=args.qwen_base_url,
                    )
                elif backend.provider == "cosyvoice":
                    backend_cosyvoice.generate(
                        text,
                        output_path,
                        api_key=backend.api_key,
                        voice_id=backend.voice_id,
                        model=args.cosyvoice_model,
                        audio_format=args.cosyvoice_output_format,
                        sample_rate=args.cosyvoice_sample_rate,
                        volume=args.cosyvoice_volume,
                        rate=args.cosyvoice_rate,
                        pitch=args.cosyvoice_pitch,
                        instruction=args.cosyvoice_instruction,
                        language_hint=args.cosyvoice_language_hint,
                        base_url=args.cosyvoice_base_url,
                    )
            except Exception as exc:
                print(f"error: failed to generate {output_path}: {exc}", file=sys.stderr)
                return 1
            generated += 1
            print(f"[OK] {output_path}")

    if backend.provider == "edge":
        print(
            f"[Done] Generated {generated}/{len(note_files)} audio/SRT pair(s): "
            f"{output_dir} + {subtitle_dir}"
        )
    else:
        print(f"[Done] Generated {generated}/{len(note_files)} audio file(s): {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
