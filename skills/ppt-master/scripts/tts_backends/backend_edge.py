"""edge-tts backend for narration audio generation."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


# Kept for CLI compatibility. Edge sentence boundaries are no longer split by
# a local character limit.
DEFAULT_SUBTITLE_MAX_CHARS = 20


@dataclass(frozen=True)
class _SubtitleCue:
    start: int
    end: int
    text: str


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


def edge_output_extension() -> str:
    return ".mp3"


def normalize_rate(rate: str) -> str:
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


async def generate(
    text: str,
    output_path: Path,
    *,
    voice: str,
    rate: str,
    subtitle_path: Path | None = None,
    subtitle_max_chars: int = DEFAULT_SUBTITLE_MAX_CHARS,
) -> None:
    """Generate narration audio and, when requested, its sentence-timed SRT."""
    if subtitle_path is not None:
        _ = subtitle_max_chars  # Deprecated compatibility option; intentionally ignored.
        await _generate_with_subtitles(
            text,
            output_path,
            subtitle_path,
            voice=voice,
            rate=rate,
        )
        return

    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency `edge-tts`. Install it with: "
            "python3 -m pip install edge-tts"
        ) from exc

    communicate = edge_tts.Communicate(text, voice=voice, rate=normalize_rate(rate))
    await communicate.save(str(output_path))


def _temporary_path(target: Path, suffix: str) -> tuple[int, Path]:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=suffix,
        dir=target.parent,
    )
    return descriptor, Path(raw_path)


def _publish_pair(
    staged_audio: Path,
    output_path: Path,
    staged_subtitle: Path,
    subtitle_path: Path,
) -> None:
    targets = (output_path, subtitle_path)
    if output_path.resolve() == subtitle_path.resolve():
        raise ValueError("audio and subtitle outputs must use different paths")

    backups: dict[Path, Path] = {}
    published: set[Path] = set()
    try:
        for target in targets:
            if not target.exists():
                continue
            descriptor, backup = _temporary_path(target, ".bak")
            os.close(descriptor)
            backup.unlink()
            os.replace(target, backup)
            backups[target] = backup

        for staged, target in (
            (staged_audio, output_path),
            (staged_subtitle, subtitle_path),
        ):
            os.replace(staged, target)
            published.add(target)
    except Exception:
        for target in published:
            target.unlink(missing_ok=True)
        for target, backup in backups.items():
            if backup.exists():
                os.replace(backup, target)
        raise
    finally:
        staged_audio.unlink(missing_ok=True)
        staged_subtitle.unlink(missing_ok=True)
        for backup in backups.values():
            backup.unlink(missing_ok=True)


def _sentence_cues(text: str, boundaries: list[dict]) -> list[_SubtitleCue]:
    """Validate Edge sentence boundaries without re-segmenting them."""
    if not boundaries:
        raise RuntimeError("Edge TTS produced no sentence-boundary timing")

    cues: list[_SubtitleCue] = []
    for boundary in boundaries:
        cue_text = re.sub(r"\s+", " ", str(boundary.get("text", ""))).strip()
        try:
            start = int(boundary["offset"])
            duration = int(boundary["duration"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "Edge TTS returned an invalid sentence-boundary payload; "
                "audio and subtitles were not published"
            ) from exc

        if not cue_text or start < 0 or duration <= 0:
            raise RuntimeError(
                "Edge TTS returned an invalid subtitle timing interval; "
                "audio and subtitles were not published"
            )
        if cues and start < cues[-1].end:
            raise RuntimeError(
                "Edge TTS returned overlapping sentence-boundary timing; "
                "audio and subtitles were not published"
            )
        cues.append(
            _SubtitleCue(
                start=start,
                end=start + duration,
                text=cue_text,
            )
        )

    source_text = re.sub(r"\s+", "", text)
    subtitle_text = re.sub(r"\s+", "", "".join(cue.text for cue in cues))
    if subtitle_text != source_text:
        raise RuntimeError(
            "Generated subtitle text does not match the narration text; "
            "audio and subtitles were not published"
        )
    return cues


def _srt_timestamp(ticks: int) -> str:
    total_milliseconds = round(ticks / 10_000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _format_srt(cues: list[_SubtitleCue]) -> str:
    blocks = [
        (
            f"{index}\n"
            f"{_srt_timestamp(cue.start)} --> {_srt_timestamp(cue.end)}\n"
            f"{cue.text}"
        )
        for index, cue in enumerate(cues, 1)
    ]
    return "\n\n".join(blocks) + "\n"


async def _generate_with_subtitles(
    text: str,
    output_path: Path,
    subtitle_path: Path,
    *,
    voice: str,
    rate: str,
) -> None:
    """Generate one MP3 and sentence-timed SRT from the same Edge stream."""
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency `edge-tts`. Install it with: "
            "python3 -m pip install edge-tts"
        ) from exc

    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=normalize_rate(rate),
        boundary="SentenceBoundary",
    )
    audio_descriptor = -1
    subtitle_descriptor = -1
    staged_audio: Path | None = None
    staged_subtitle: Path | None = None
    boundaries: list[dict] = []
    received_audio = False
    try:
        audio_descriptor, staged_audio = _temporary_path(output_path, ".tmp")
        subtitle_descriptor, staged_subtitle = _temporary_path(subtitle_path, ".tmp")

        audio_stream = os.fdopen(audio_descriptor, "wb")
        audio_descriptor = -1
        with audio_stream:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_stream.write(chunk["data"])
                    received_audio = True
                elif chunk["type"] == "SentenceBoundary":
                    boundaries.append(chunk)
            audio_stream.flush()
            os.fsync(audio_stream.fileno())

        if not received_audio:
            raise RuntimeError("Edge TTS returned no audio data")
        if not boundaries:
            raise RuntimeError("Edge TTS returned no sentence-boundary timing")
        subtitle_text = _format_srt(_sentence_cues(text, boundaries))

        subtitle_stream = os.fdopen(
            subtitle_descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        )
        subtitle_descriptor = -1
        with subtitle_stream:
            subtitle_stream.write(subtitle_text)
            subtitle_stream.flush()
            os.fsync(subtitle_stream.fileno())
        assert staged_audio is not None
        assert staged_subtitle is not None
        _publish_pair(
            staged_audio,
            output_path,
            staged_subtitle,
            subtitle_path,
        )
    finally:
        if audio_descriptor >= 0:
            os.close(audio_descriptor)
        if subtitle_descriptor >= 0:
            os.close(subtitle_descriptor)
        if staged_audio is not None:
            staged_audio.unlink(missing_ok=True)
        if staged_subtitle is not None:
            staged_subtitle.unlink(missing_ok=True)


def print_common_voices() -> None:
    print("Common edge-tts voices:")
    print("Locale   Voice                         Notes")
    print("------   ----------------------------  ----------------")
    for locale, voice, notes in COMMON_VOICES:
        print(f"{locale:<8} {voice:<29} {notes}")


async def print_voices(locale: str | None = None) -> None:
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

