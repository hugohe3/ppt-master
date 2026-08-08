"""MiniMax T2A backend for narration audio generation."""

from __future__ import annotations

import binascii
import json
import math
import os
from pathlib import Path

from tts_backends.backend_common import (
    extension_from_format,
    get_bytes,
    post_json,
    publish_audio_bytes,
    publish_audio_subtitle,
    read_api_key,
)
from tts_backends.backend_edge import (
    DEFAULT_SUBTITLE_MAX_CHARS,
    format_word_timed_srt,
)


DEFAULT_ENDPOINT = "https://api.minimaxi.com/v1/t2a_v2"
DEFAULT_MODEL = "speech-2.8-hd"
_TICKS_PER_MILLISECOND = 10_000

# International fallback: set MINIMAX_TTS_BASE_URL=https://api.minimax.io if needed.


def output_extension(audio_format: str) -> str:
    return extension_from_format(audio_format)


def read_minimax_api_key(env_name: str) -> str:
    return read_api_key(env_name, label="MiniMax")


def resolve_url(base_url: str | None = None) -> str:
    base = (base_url or os.environ.get("MINIMAX_TTS_BASE_URL") or DEFAULT_ENDPOINT).rstrip("/")
    if base.endswith("/t2a_v2"):
        return base
    if base.endswith("/v1"):
        return base + "/t2a_v2"
    return base + "/v1/t2a_v2"


def _ticks(value: object, *, field: str) -> int:
    if isinstance(value, bool):
        raise RuntimeError(f"MiniMax subtitle {field} is not numeric")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"MiniMax subtitle {field} is not numeric") from exc
    if not math.isfinite(numeric):
        raise RuntimeError(f"MiniMax subtitle {field} is not finite")
    return int(round(numeric * _TICKS_PER_MILLISECOND))


def _word_boundaries(raw: object) -> list[dict]:
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("MiniMax subtitle response contains no sentence blocks")

    boundaries: list[dict] = []
    for sentence in raw:
        if not isinstance(sentence, dict):
            raise RuntimeError("MiniMax subtitle sentence block is not an object")
        words = sentence.get("timestamped_words")
        if not isinstance(words, list) or not words:
            raise RuntimeError("MiniMax subtitle sentence block contains no word timings")
        for item in words:
            if not isinstance(item, dict):
                raise RuntimeError("MiniMax subtitle word timing is not an object")
            word = item.get("word")
            if not isinstance(word, str) or not word:
                raise RuntimeError("MiniMax subtitle word timing contains no text")
            start = _ticks(item.get("time_begin"), field="start time")
            end = _ticks(item.get("time_end"), field="end time")
            if start < 0 or end <= start:
                raise RuntimeError(
                    "MiniMax subtitle response contains an invalid word interval"
                )
            if boundaries and start < boundaries[-1]["offset"]:
                raise RuntimeError("MiniMax subtitle words are not in chronological order")
            boundaries.append(
                {
                    "text": word,
                    "offset": start,
                    "duration": end - start,
                }
            )
    return boundaries


def _download_subtitle(
    url: str,
    text: str,
    max_chars: int,
) -> str:
    try:
        raw = json.loads(get_bytes(url).decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("MiniMax subtitle response is not valid UTF-8 JSON") from exc
    return format_word_timed_srt(
        text,
        _word_boundaries(raw),
        max_chars,
        provider_label="MiniMax",
    )


def generate(
    text: str,
    output_path: Path,
    *,
    api_key: str,
    voice_id: str,
    model: str,
    audio_format: str,
    sample_rate: int,
    bitrate: int,
    channel: int,
    speed: float,
    volume: float,
    pitch: int,
    language_boost: str,
    base_url: str | None,
    subtitle_path: Path | None = None,
    subtitle_max_chars: int = DEFAULT_SUBTITLE_MAX_CHARS,
) -> None:
    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "language_boost": language_boost,
        "output_format": "hex",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": volume,
            "pitch": pitch,
        },
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
            "channel": channel,
        },
    }
    if subtitle_path is not None:
        payload["subtitle_enable"] = True
        payload["subtitle_type"] = "word"

    data = post_json(
        resolve_url(base_url),
        headers={"Authorization": f"Bearer {api_key}"},
        payload=payload,
        timeout=180,
    )
    base_resp = data.get("base_resp") or {}
    if base_resp.get("status_code") not in (None, 0, "0"):
        raise RuntimeError(f"MiniMax TTS failed: {data}")

    response_data = data.get("data") or {}
    audio_hex = response_data.get("audio")
    if not audio_hex:
        raise RuntimeError(f"MiniMax response missing audio data: {data}")
    try:
        audio = binascii.unhexlify(audio_hex)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError("MiniMax response audio is not valid hex data") from exc

    if subtitle_path is None:
        publish_audio_bytes(audio, output_path)
        return

    subtitle_url = response_data.get("subtitle_file")
    if not isinstance(subtitle_url, str) or not subtitle_url.strip():
        trace_id = data.get("trace_id") or "unknown"
        raise RuntimeError(
            f"MiniMax response missing subtitle file (trace_id={trace_id})"
        )
    subtitle = _download_subtitle(
        subtitle_url,
        text,
        subtitle_max_chars,
    )
    publish_audio_subtitle(audio, output_path, subtitle, subtitle_path)


def print_voices() -> None:
    print("MiniMax TTS voices are selected by voice_id.")
    print("Use a system voice ID or a cloned voice_id from MiniMax Voice Clone.")
    print("Example domestic system voice from MiniMax docs: male-qn-qingse")
