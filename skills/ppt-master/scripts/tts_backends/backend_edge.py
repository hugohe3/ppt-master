"""edge-tts backend for narration audio generation."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SUBTITLE_MAX_CHARS = 20
_SENTENCE_END = frozenset("。！？!?")
_CLAUSE_END = frozenset("，,；;：:")
_CLOSING_PUNCTUATION = frozenset('”’」』）》)"\'')


@dataclass(frozen=True)
class _MappedWord:
    start: int
    end: int
    source_start: int
    source_end: int


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
    """Generate narration audio and, when requested, its compact SRT."""
    if subtitle_path is not None:
        await _generate_with_subtitles(
            text,
            output_path,
            subtitle_path,
            voice=voice,
            rate=rate,
            max_chars=subtitle_max_chars,
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


def _text_key(text: str) -> str:
    return "".join(character.casefold() for character in text if character.isalnum())


def _source_key_positions(text: str) -> tuple[str, list[int]]:
    key: list[str] = []
    positions: list[int] = []
    for index, character in enumerate(text):
        if not character.isalnum():
            continue
        normalized = character.casefold()
        key.extend(normalized)
        positions.extend([index] * len(normalized))
    return "".join(key), positions


def _map_word_boundaries(text: str, boundaries: list[dict]) -> list[_MappedWord]:
    source_key, source_positions = _source_key_positions(text)
    boundary_keys = [_text_key(boundary["text"]) for boundary in boundaries]
    boundary_key = "".join(boundary_keys)
    if not source_key or source_key != boundary_key:
        raise RuntimeError(
            "Edge TTS word boundaries could not be aligned with the narration text; "
            "subtitle timing was not generated"
        )

    mapped: list[_MappedWord] = []
    key_offset = 0
    for boundary, word_key in zip(boundaries, boundary_keys):
        if not word_key:
            continue
        key_end = key_offset + len(word_key)
        mapped.append(
            _MappedWord(
                start=boundary["offset"],
                end=boundary["offset"] + boundary["duration"],
                source_start=source_positions[key_offset],
                source_end=source_positions[key_end - 1] + 1,
            )
        )
        key_offset = key_end
    return mapped


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _display_length(text: str, start: int, end: int) -> int:
    return sum(not character.isspace() for character in text[start:end])


def _is_sentence_end(text: str, index: int) -> bool:
    character = text[index]
    if character in _SENTENCE_END:
        return True
    if character != ".":
        return False
    previous = text[index - 1] if index else ""
    following = text[index + 1] if index + 1 < len(text) else ""
    return not (previous.isdigit() and following.isdigit())


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    index = 0
    while index < len(text):
        if not _is_sentence_end(text, index):
            index += 1
            continue
        end = index + 1
        while end < len(text) and text[end] in _CLOSING_PUNCTUATION:
            end += 1
        span = _trim_span(text, start, end)
        if span[0] < span[1]:
            spans.append(span)
        start = end
        index = end
    span = _trim_span(text, start, len(text))
    if span[0] < span[1]:
        spans.append(span)
    return spans


def _hard_split_span(
    text: str,
    span: tuple[int, int],
    words: list[_MappedWord],
    max_chars: int,
) -> list[tuple[int, int]]:
    start, end = span
    parts: list[tuple[int, int]] = []
    while _display_length(text, start, end) > max_chars:
        remaining_length = _display_length(text, start, end)
        remaining_parts = (remaining_length + max_chars - 1) // max_chars
        target_length = (remaining_length + remaining_parts - 1) // remaining_parts
        candidates = [
            (word.source_end, _display_length(text, start, word.source_end))
            for word in words
            if start < word.source_end < end
            and _display_length(text, start, word.source_end) <= max_chars
        ]
        if candidates:
            split_at, _ = min(
                candidates,
                key=lambda candidate: (
                    abs(candidate[1] - target_length),
                    -candidate[1],
                ),
            )
        else:
            split_at = next(
                (
                    word.source_end
                    for word in words
                    if start < word.source_end < end
                ),
                end,
            )
        if split_at >= end:
            break
        part = _trim_span(text, start, split_at)
        if part[0] < part[1]:
            parts.append(part)
        start = split_at
    part = _trim_span(text, start, end)
    if part[0] < part[1]:
        parts.append(part)
    return parts


def _split_sentence_span(
    text: str,
    sentence: tuple[int, int],
    words: list[_MappedWord],
    max_chars: int,
) -> list[tuple[int, int]]:
    if _display_length(text, *sentence) <= max_chars:
        return [sentence]

    start, end = sentence
    clauses: list[tuple[int, int]] = []
    clause_start = start
    for index in range(start, end):
        if text[index] not in _CLAUSE_END:
            continue
        clause = _trim_span(text, clause_start, index + 1)
        if clause[0] < clause[1]:
            clauses.append(clause)
        clause_start = index + 1
    clause = _trim_span(text, clause_start, end)
    if clause[0] < clause[1]:
        clauses.append(clause)

    atoms = [
        part
        for clause in clauses
        for part in _hard_split_span(text, clause, words, max_chars)
    ]
    merged: list[tuple[int, int]] = []
    for atom in atoms:
        if not merged:
            merged.append(atom)
            continue
        candidate = (merged[-1][0], atom[1])
        if _display_length(text, *candidate) <= max_chars:
            merged[-1] = candidate
        else:
            merged.append(atom)
    return merged


def _subtitle_cues(
    text: str,
    boundaries: list[dict],
    max_chars: int,
) -> list[_SubtitleCue]:
    if max_chars < 1:
        raise ValueError("subtitle_max_chars must be at least 1")
    words = _map_word_boundaries(text, boundaries)
    spans = [
        span
        for sentence in _sentence_spans(text)
        for span in _split_sentence_span(text, sentence, words, max_chars)
    ]

    pending: list[tuple[int, int, str]] = []
    assigned_word_indexes: list[int] = []
    for start, end in spans:
        matching = [
            (index, word)
            for index, word in enumerate(words)
            if word.source_start >= start and word.source_end <= end
        ]
        if not matching:
            continue
        cue_text = re.sub(r"\s+", " ", text[start:end]).strip()
        assigned_word_indexes.extend(index for index, _ in matching)
        pending.append((matching[0][1].start, matching[-1][1].end, cue_text))

    if assigned_word_indexes != list(range(len(words))):
        raise RuntimeError(
            "Edge TTS word boundaries crossed subtitle split points; "
            "subtitle timing was not generated"
        )
    if not pending:
        raise RuntimeError("Edge TTS produced no timed subtitle cues")

    cues: list[_SubtitleCue] = []
    for index, (start, word_end, cue_text) in enumerate(pending):
        next_start = pending[index + 1][0] if index + 1 < len(pending) else None
        end = next_start if next_start is not None and next_start > word_end else word_end
        cues.append(_SubtitleCue(start=start, end=end, text=cue_text))

    source_text = re.sub(r"\s+", "", text)
    subtitle_text = re.sub(r"\s+", "", "".join(cue.text for cue in cues))
    if subtitle_text != source_text:
        raise RuntimeError(
            "Generated subtitle text does not match the narration text; "
            "audio and subtitles were not published"
        )
    if any(_display_length(cue.text, 0, len(cue.text)) > max_chars for cue in cues):
        raise RuntimeError(
            "A single Edge TTS word boundary exceeds the subtitle character limit; "
            "audio and subtitles were not published"
        )
    if any(cue.end <= cue.start for cue in cues):
        raise RuntimeError(
            "Edge TTS returned an invalid subtitle timing interval; "
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
    max_chars: int,
) -> None:
    """Generate one MP3 and compact SRT from the same Edge word-timing stream."""
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
        boundary="WordBoundary",
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
                elif chunk["type"] == "WordBoundary":
                    boundaries.append(chunk)
            audio_stream.flush()
            os.fsync(audio_stream.fileno())

        if not received_audio:
            raise RuntimeError("Edge TTS returned no audio data")
        if not boundaries:
            raise RuntimeError("Edge TTS returned no word-boundary timing")
        subtitle_text = _format_srt(_subtitle_cues(text, boundaries, max_chars))

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

