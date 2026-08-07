"""ElevenLabs backend for narration audio generation."""

from __future__ import annotations

import base64
import binascii
import json
import math
from pathlib import Path
from urllib import error, request
from urllib.parse import quote, urlencode

from tts_backends.backend_common import (
    publish_audio_bytes,
    publish_audio_subtitle,
    read_api_key,
)
from tts_backends.backend_edge import (
    DEFAULT_SUBTITLE_MAX_CHARS,
    format_word_timed_srt,
)


API_BASE = "https://api.elevenlabs.io/v1"
_TICKS_PER_SECOND = 10_000_000


def read_elevenlabs_api_key(env_name: str) -> str:
    return read_api_key(env_name, label="ElevenLabs")


def output_extension(output_format: str) -> str:
    codec = output_format.split("_", 1)[0].lower()
    if codec in {"mp3", "wav"}:
        return f".{codec}"
    raise RuntimeError(
        f"Unsupported ElevenLabs output format for PPT narration: {output_format}. "
        "Use an mp3_* or wav_* format."
    )


def _read_http_error(exc: error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return f"HTTP {exc.code}: {body or exc.reason}"


def _seconds_to_ticks(value: object, *, field: str) -> int:
    if isinstance(value, bool):
        raise RuntimeError(f"ElevenLabs alignment {field} is not numeric")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"ElevenLabs alignment {field} is not numeric"
        ) from exc
    if not math.isfinite(numeric):
        raise RuntimeError(f"ElevenLabs alignment {field} is not finite")
    return int(round(numeric * _TICKS_PER_SECOND))


def _is_unspaced_character(character: str) -> bool:
    """Return whether a script is safer to time one character at a time."""
    codepoint = ord(character)
    return (
        0x3040 <= codepoint <= 0x30FF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xAC00 <= codepoint <= 0xD7AF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0x20000 <= codepoint <= 0x2FA1F
    )


def _alignment_characters(
    text: str,
    alignment: object,
) -> tuple[list[str], list[object], list[object]]:
    if not isinstance(alignment, dict):
        raise RuntimeError("ElevenLabs response contains no original-text alignment")
    raw_characters = alignment.get("characters")
    raw_starts = alignment.get("character_start_times_seconds")
    raw_ends = alignment.get("character_end_times_seconds")
    if not all(isinstance(values, list) for values in (
        raw_characters,
        raw_starts,
        raw_ends,
    )):
        raise RuntimeError("ElevenLabs alignment arrays are missing")
    if not raw_characters or not (
        len(raw_characters) == len(raw_starts) == len(raw_ends)
    ):
        raise RuntimeError("ElevenLabs alignment arrays have inconsistent lengths")
    if any(not isinstance(item, str) or not item for item in raw_characters):
        raise RuntimeError("ElevenLabs alignment contains an invalid character")
    if "".join(raw_characters) != text:
        raise RuntimeError(
            "ElevenLabs original-text alignment differs from the narration text; "
            "audio and subtitles were not published"
        )

    characters: list[str] = []
    starts: list[object] = []
    ends: list[object] = []
    for raw_character, start, end in zip(
        raw_characters,
        raw_starts,
        raw_ends,
    ):
        for character in raw_character:
            characters.append(character)
            starts.append(start)
            ends.append(end)
    return characters, starts, ends


def _word_boundaries(text: str, alignment: object) -> list[dict]:
    characters, starts, ends = _alignment_characters(text, alignment)
    boundaries: list[dict] = []
    index = 0
    while index < len(characters):
        character = characters[index]
        if not character.isalnum():
            index += 1
            continue

        token_end = index + 1
        if not _is_unspaced_character(character):
            while token_end < len(characters):
                following = characters[token_end]
                if (
                    not following.isalnum()
                    or _is_unspaced_character(following)
                ):
                    break
                token_end += 1

        start = _seconds_to_ticks(starts[index], field="start time")
        end = _seconds_to_ticks(ends[token_end - 1], field="end time")
        if start < 0 or end <= start:
            raise RuntimeError(
                "ElevenLabs alignment contains an invalid character interval"
            )
        if boundaries and start < boundaries[-1]["offset"]:
            raise RuntimeError(
                "ElevenLabs alignment is not in chronological order"
            )
        boundaries.append({
            "text": "".join(characters[index:token_end]),
            "offset": start,
            "duration": end - start,
        })
        index = token_end

    if not boundaries:
        raise RuntimeError("ElevenLabs alignment contains no timed words")
    return boundaries


def generate(
    text: str,
    output_path: Path,
    *,
    api_key: str,
    voice_id: str,
    model: str,
    output_format: str,
    stability: float | None,
    similarity_boost: float | None,
    style: float | None,
    speed: float | None,
    speaker_boost: bool | None,
    subtitle_path: Path | None = None,
    subtitle_max_chars: int = DEFAULT_SUBTITLE_MAX_CHARS,
) -> None:
    payload: dict[str, object] = {
        "text": text,
        "model_id": model,
    }

    voice_settings: dict[str, object] = {}
    if stability is not None:
        voice_settings["stability"] = stability
    if similarity_boost is not None:
        voice_settings["similarity_boost"] = similarity_boost
    if style is not None:
        voice_settings["style"] = style
    if speed is not None:
        voice_settings["speed"] = speed
    if speaker_boost is not None:
        voice_settings["use_speaker_boost"] = speaker_boost
    if voice_settings:
        payload["voice_settings"] = voice_settings

    query = urlencode({"output_format": output_format})
    suffix = "/with-timestamps" if subtitle_path is not None else ""
    url = (
        f"{API_BASE}/text-to-speech/{quote(voice_id, safe='')}{suffix}?{query}"
    )
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=120) as response:
            response_data = response.read()
    except error.HTTPError as exc:
        raise RuntimeError(_read_http_error(exc)) from exc
    except error.URLError as exc:
        raise RuntimeError(f"ElevenLabs request failed: {exc.reason}") from exc

    if subtitle_path is None:
        publish_audio_bytes(response_data, output_path)
        return

    try:
        data = json.loads(response_data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "ElevenLabs timing response is not valid UTF-8 JSON"
        ) from exc
    encoded_audio = data.get("audio_base64")
    if not isinstance(encoded_audio, str) or not encoded_audio:
        raise RuntimeError("ElevenLabs timing response contains no audio")
    try:
        audio = base64.b64decode(encoded_audio, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(
            "ElevenLabs timing response audio is not valid base64"
        ) from exc
    subtitle = format_word_timed_srt(
        text,
        _word_boundaries(text, data.get("alignment")),
        subtitle_max_chars,
        provider_label="ElevenLabs",
    )
    publish_audio_subtitle(audio, output_path, subtitle, subtitle_path)


def print_voices(api_key: str) -> None:
    req = request.Request(
        f"{API_BASE}/voices",
        headers={"xi-api-key": api_key},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(_read_http_error(exc)) from exc
    except error.URLError as exc:
        raise RuntimeError(f"ElevenLabs request failed: {exc.reason}") from exc

    print("ElevenLabs voices:")
    print("Voice ID                 Name                           Category")
    print("-----------------------  -----------------------------  ----------")
    for item in data.get("voices", []):
        voice_id = item.get("voice_id", "")
        name = item.get("name", "")
        category = item.get("category", "")
        print(f"{voice_id:<23} {name:<29} {category}")
