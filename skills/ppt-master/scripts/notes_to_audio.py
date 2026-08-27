#!/usr/bin/env python3
"""Generate per-slide narration audio from PPT Master notes.

This script uses provider backends for the same per-slide output contract on
macOS, Linux, and Windows. `edge-tts` remains the default no-key backend and
also writes one compact, word-timed SRT file per slide from the same TTS stream.
MiniMax and CosyVoice request word timings; ElevenLabs requests character
alignment. All four apply the same compact, text-faithful cue regrouping.
Qwen remains audio-only because its current TTS API exposes no timestamps.

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
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import authoring_roundtrip
from console_encoding import configure_utf8_stdio
from config import load_prefixed_env_file
from pptx_workspace import (
    AUTHORING_SVG_FLAT_DIR,
    ROUNDTRIP_MANIFEST_PATH,
)
from slide_roster import discover_slide_svgs
from tts_backends import (
    backend_cosyvoice,
    backend_edge,
    backend_elevenlabs,
    backend_minimax,
    backend_qwen,
)
from tts_backends.backend_common import temporary_path

configure_utf8_stdio()

DEFAULT_EDGE_CONCURRENCY = 3
SUPPORTED_AUDIO_EXTENSIONS = frozenset({".m4a", ".mp3", ".wav"})


@dataclass(frozen=True)
class AudioBackend:
    provider: str
    extension: str
    api_key: str = ""
    voice_id: str = ""


@dataclass(frozen=True)
class NoteRosterEntry:
    note_path: Path
    output_stem: str


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
    note_roster: list[NoteRosterEntry],
    output_dir: Path,
    extension: str,
) -> list[AudioJob]:
    """Read a complete per-slide notes roster into ordered audio jobs."""
    jobs: list[AudioJob] = []
    invalid: list[str] = []
    for entry in note_roster:
        note_path = entry.note_path
        if not note_path.is_file():
            invalid.append(f"{note_path.name} is missing")
            continue
        try:
            text = spoken_text(note_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            invalid.append(f"{note_path.name} is unreadable: {exc}")
            continue
        if not text:
            invalid.append(f"{note_path.name} has no spoken text")
            continue
        jobs.append(AudioJob(
            note_path=note_path,
            text=text,
            output_path=output_dir / f"{entry.output_stem}{extension}",
        ))
    if invalid:
        raise ValueError(
            "per-slide notes are incomplete: " + "; ".join(invalid)
        )
    return jobs


def _expected_note_roster(project: Path) -> list[NoteRosterEntry]:
    """Resolve the owning route's complete per-slide notes roster.

    Round-trip workspaces follow their validated page plan or identity roster,
    including source-note inheritance for copied output pages.
    """
    notes_dir = project / "notes"
    svg_files = discover_slide_svgs(project / "svg_output")
    if svg_files:
        aliases: dict[int, list[Path]] = {}
        for path in sorted(notes_dir.glob("*.md")):
            match = re.search(r"slide[_]?(\d+)", path.stem)
            if match:
                aliases.setdefault(int(match.group(1)), []).append(path)
        note_roster: list[NoteRosterEntry] = []
        for index, svg_path in enumerate(svg_files, 1):
            exact = notes_dir / f"{svg_path.stem}.md"
            if exact.exists():
                note_roster.append(NoteRosterEntry(
                    note_path=exact,
                    output_stem=svg_path.stem,
                ))
                continue
            matches = aliases.get(index, [])
            if len(matches) > 1:
                raise ValueError(
                    f"multiple notes files match slide {index}: "
                    + ", ".join(path.name for path in matches)
                )
            note_roster.append(
                NoteRosterEntry(
                    note_path=matches[0] if matches else exact,
                    output_stem=svg_path.stem,
                )
            )
        return note_roster

    slide_index_path = project / "analysis" / "slide_index.json"
    if slide_index_path.is_file():
        try:
            slide_index = json.loads(
                slide_index_path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid slide index: {exc}") from exc
        if not isinstance(slide_index, dict):
            raise ValueError("invalid slide index root")
        slides = slide_index.get("slides")
        slide_count = slide_index.get("slide_count")
        if (
            not isinstance(slides, list)
            or isinstance(slide_count, bool)
            or not isinstance(slide_count, int)
            or slide_count != len(slides)
        ):
            raise ValueError("invalid slide index notes roster")
        note_roster: list[NoteRosterEntry] = []
        for index, slide in enumerate(slides, 1):
            note_file = slide.get("note_file") if isinstance(slide, dict) else None
            if not isinstance(note_file, str) or Path(note_file).suffix != ".md":
                raise ValueError(
                    f"invalid slide index note_file for slide {index}"
                )
            note_name = Path(note_file).name
            note_roster.append(
                NoteRosterEntry(
                    note_path=notes_dir / note_name,
                    output_stem=Path(note_name).stem,
                )
            )
        return note_roster

    roundtrip_manifest_path = project / ROUNDTRIP_MANIFEST_PATH
    authoring_dir = project / AUTHORING_SVG_FLAT_DIR
    if roundtrip_manifest_path.is_file() and authoring_dir.is_dir():
        try:
            _, _, documents, _, _ = authoring_roundtrip._load_documents(
                project.resolve(),
                authoring_dir.resolve(),
            )
            pages, _ = authoring_roundtrip._load_page_plan(
                project.resolve(),
                authoring_dir.resolve(),
                documents,
            )
        except authoring_roundtrip.AuthoringRoundtripError as exc:
            raise ValueError(f"invalid round-trip notes roster: {exc}") from exc

        note_roster: list[NoteRosterEntry] = []
        missing_stems: list[str] = []
        for page in pages:
            note_path = notes_dir / f"{page.svg_stem}.md"
            if not note_path.is_file() and page.svg_name != page.source_svg_name:
                source_stem = Path(page.source_svg_name).stem
                note_path = notes_dir / f"{source_stem}.md"
            if not note_path.is_file():
                missing_stems.append(page.svg_stem)
                continue
            note_roster.append(NoteRosterEntry(
                note_path=note_path,
                output_stem=page.svg_stem,
            ))
        if missing_stems:
            raise ValueError(
                "round-trip per-slide notes are incomplete; missing stems: "
                + ", ".join(missing_stems)
            )
        return note_roster

    return [
        NoteRosterEntry(
            note_path=path,
            output_stem=path.stem,
        )
        for path in sorted(notes_dir.glob("*.md"))
        if path.name != "total.md"
    ]


def _remove_stale_audio_variants(output_path: Path) -> None:
    """Remove other supported formats only after the target audio is published."""
    for candidate in output_path.parent.iterdir():
        if (
            candidate.name != output_path.name
            and candidate.is_file()
            and candidate.stem == output_path.stem
            and candidate.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ):
            candidate.unlink()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _provider_manifest_details(
    args: argparse.Namespace,
    backend: AudioBackend,
) -> tuple[str, dict[str, object]]:
    if backend.provider == "edge":
        return "edge-tts", {
            "rate": args.rate,
        }
    if backend.provider == "elevenlabs":
        return args.elevenlabs_model, {
            "stability": args.elevenlabs_stability,
            "similarity_boost": args.elevenlabs_similarity_boost,
            "style": args.elevenlabs_style,
            "speed": args.elevenlabs_speed,
            "speaker_boost": args.elevenlabs_speaker_boost,
        }
    if backend.provider == "minimax":
        return args.minimax_model, {
            "speed": args.minimax_speed,
            "volume": args.minimax_volume,
            "pitch": args.minimax_pitch,
            "language_boost": args.minimax_language_boost,
        }
    if backend.provider == "qwen":
        return args.qwen_model, {
            "language_type": args.qwen_language_type,
            "optimize_instructions": args.qwen_optimize_instructions,
            "custom_instructions": True if args.qwen_instructions else None,
        }
    return args.cosyvoice_model, {
        "volume": args.cosyvoice_volume,
        "rate": args.cosyvoice_rate,
        "pitch": args.cosyvoice_pitch,
        "language_hint": args.cosyvoice_language_hint,
        "custom_instruction": True if args.cosyvoice_instruction else None,
    }


def _narration_manifest(
    args: argparse.Namespace,
    backend: AudioBackend,
    *,
    writes_subtitles: bool,
) -> dict[str, object]:
    model, raw_settings = _provider_manifest_details(args, backend)
    settings = {
        key: value
        for key, value in raw_settings.items()
        if value is not None
    }
    voice_ref = backend.voice_id
    if backend.provider != "edge":
        voice_ref = f"sha256:{_sha256_text(voice_ref)}"

    manifest: dict[str, object] = {
        "schema": "ppt-master.narration.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "provider": backend.provider,
        "model": model,
        "voice_ref": voice_ref,
        "audio_format": backend.extension.lstrip("."),
    }
    if settings:
        manifest["settings"] = settings
    if writes_subtitles:
        manifest["subtitles"] = {
            "format": "srt",
            "timing": (
                "character" if backend.provider == "elevenlabs" else "word"
            ),
            "max_visible_chars": args.subtitle_max_chars,
        }
    return manifest


def _publish_manifest(path: Path, manifest: dict[str, object]) -> None:
    descriptor, staged_path = temporary_path(path, ".tmp")
    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            descriptor = -1
            json.dump(manifest, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged_path, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        staged_path.unlink(missing_ok=True)


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
                subtitle_path=subtitle_dir / f"{job.output_path.stem}.srt",
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
        help="maximum visible characters per provider-timed subtitle cue (default: 20)",
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
        "--elevenlabs-speed",
        type=float,
        default=None,
        help="optional ElevenLabs speaking speed override, 0.7-1.2",
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
                        choices=[8000, 16000, 22050, 24000, 44100, 48000],
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
    parser.add_argument(
        "--cosyvoice-audio-only",
        action="store_true",
        help=(
            "skip CosyVoice timestamps/SRT for a model or voice that does not "
            "support them"
        ),
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

    for option, value, minimum, maximum in (
        ("--elevenlabs-stability", args.elevenlabs_stability, 0.0, 1.0),
        (
            "--elevenlabs-similarity-boost",
            args.elevenlabs_similarity_boost,
            0.0,
            1.0,
        ),
        ("--elevenlabs-style", args.elevenlabs_style, 0.0, 1.0),
        ("--elevenlabs-speed", args.elevenlabs_speed, 0.7, 1.2),
        ("--cosyvoice-volume", args.cosyvoice_volume, 0, 100),
        ("--cosyvoice-rate", args.cosyvoice_rate, 0.5, 2.0),
        ("--cosyvoice-pitch", args.cosyvoice_pitch, 0.5, 2.0),
    ):
        if value is not None and not minimum <= value <= maximum:
            parser.error(f"{option} must be between {minimum} and {maximum}")
            raise AssertionError("unreachable")

    if args.cosyvoice_audio_only and args.provider != "cosyvoice":
        parser.error("--cosyvoice-audio-only requires --provider cosyvoice")
        raise AssertionError("unreachable")

    if args.provider == "qwen" and args.qwen_instructions:
        if "instruct" not in args.qwen_model:
            parser.error(
                "--qwen-instructions requires a Qwen3 TTS Instruct model"
            )
            raise AssertionError("unreachable")
    if args.qwen_optimize_instructions and not args.qwen_instructions:
        parser.error(
            "--qwen-optimize-instructions requires --qwen-instructions"
        )
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
        backend = AudioBackend(
            provider=args.provider,
            extension=extension,
            api_key=api_key,
            voice_id=voice_id,
        )
    else:
        backend = AudioBackend(
            provider=args.provider,
            extension=backend_edge.edge_output_extension(),
            voice_id=args.voice,
        )

    project = args.project_path
    notes_dir = project / "notes"
    output_dir = args.output or (project / "audio")
    subtitle_dir = output_dir
    writes_subtitles = backend.provider in {
        "edge",
        "elevenlabs",
        "minimax",
    } or (
        backend.provider == "cosyvoice"
        and not args.cosyvoice_audio_only
    )

    try:
        note_roster = _expected_note_roster(project)
        if not note_roster:
            raise ValueError(f"no per-slide notes found in {notes_dir}")
        jobs = _prepare_audio_jobs(
            note_roster,
            output_dir,
            backend.extension,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    try:
        manifest_path.unlink(missing_ok=True)
        (output_dir / "total.srt").unlink(missing_ok=True)
    except OSError as exc:
        print(f"error: failed to clear stale narration metadata: {exc}", file=sys.stderr)
        return 1

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
            subtitle_path = subtitle_dir / f"{job.output_path.stem}.srt"
            if result is not None:
                print(
                    f"error: failed to generate {job.output_path}: {result}",
                    file=sys.stderr,
                )
                failed = True
                continue
            try:
                _remove_stale_audio_variants(job.output_path)
            except OSError as exc:
                print(
                    f"error: failed to remove stale audio for "
                    f"{job.output_path.stem}: {exc}",
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
            subtitle_path: Path | None = None
            try:
                if backend.provider == "elevenlabs":
                    if writes_subtitles:
                        subtitle_path = subtitle_dir / f"{output_path.stem}.srt"
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
                        speed=args.elevenlabs_speed,
                        speaker_boost=args.elevenlabs_speaker_boost,
                        subtitle_path=subtitle_path,
                        subtitle_max_chars=args.subtitle_max_chars,
                    )
                elif backend.provider == "minimax":
                    if writes_subtitles:
                        subtitle_path = subtitle_dir / f"{output_path.stem}.srt"
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
                        subtitle_path=subtitle_path,
                        subtitle_max_chars=args.subtitle_max_chars,
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
                    if writes_subtitles:
                        subtitle_path = subtitle_dir / f"{output_path.stem}.srt"
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
                        subtitle_path=subtitle_path,
                        subtitle_max_chars=args.subtitle_max_chars,
                    )
                _remove_stale_audio_variants(output_path)
                if not writes_subtitles:
                    output_path.with_suffix(".srt").unlink(missing_ok=True)
            except Exception as exc:
                print(f"error: failed to generate {output_path}: {exc}", file=sys.stderr)
                return 1
            generated += 1
            print(f"[OK] {output_path}")
            if subtitle_path is not None:
                print(f"     {subtitle_path}")

    try:
        _publish_manifest(
            manifest_path,
            _narration_manifest(
                args,
                backend,
                writes_subtitles=writes_subtitles,
            ),
        )
    except (OSError, RuntimeError) as exc:
        print(f"error: failed to publish narration manifest: {exc}", file=sys.stderr)
        return 1

    if writes_subtitles:
        print(
            f"[Done] Generated {generated}/{len(note_roster)} audio/SRT pair(s): "
            f"{output_dir}"
        )
    else:
        print(f"[Done] Generated {generated}/{len(note_roster)} audio file(s): {output_dir}")
    print(f"[REPORT] Narration manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
