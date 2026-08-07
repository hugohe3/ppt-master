"""Alibaba CosyVoice backend for narration audio generation."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from urllib import error, request

from tts_backends.backend_common import (
    download_audio,
    extension_from_format,
    get_bytes,
    post_json,
    publish_audio_subtitle,
    read_api_key,
    read_http_error,
)
from tts_backends.backend_edge import (
    DEFAULT_SUBTITLE_MAX_CHARS,
    format_word_timed_srt,
)


DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
DEFAULT_MODEL = "cosyvoice-v3-flash"
_TICKS_PER_MILLISECOND = 10_000


def output_extension(audio_format: str) -> str:
    return extension_from_format(audio_format)


def read_cosyvoice_api_key(env_name: str) -> str:
    env_names = tuple(dict.fromkeys([env_name, "COSYVOICE_API_KEY", "DASHSCOPE_API_KEY"]))
    return read_api_key(*env_names, label="CosyVoice/DashScope")


def resolve_url(base_url: str | None = None) -> str:
    base = (base_url or os.environ.get("COSYVOICE_TTS_BASE_URL") or DEFAULT_ENDPOINT).rstrip("/")
    if base.endswith("/SpeechSynthesizer"):
        return base
    return base + "/api/v1/services/audio/tts/SpeechSynthesizer"


def _parse_sse_event(data_lines: list[str]) -> dict | None:
    payload = "\n".join(data_lines).strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("CosyVoice streaming response contains invalid JSON") from exc
    if not isinstance(event, dict):
        raise RuntimeError("CosyVoice streaming event is not an object")
    return event


def _parse_sse(raw: bytes) -> list[dict]:
    try:
        body = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise RuntimeError("CosyVoice streaming response is not valid UTF-8") from exc

    if not any(line.startswith("data:") for line in body.splitlines()):
        event = _parse_sse_event([body])
        return [event] if event is not None else []

    events: list[dict] = []
    data_lines: list[str] = []
    for line in body.splitlines():
        if not line:
            event = _parse_sse_event(data_lines)
            if event is not None:
                events.append(event)
            data_lines = []
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    event = _parse_sse_event(data_lines)
    if event is not None:
        events.append(event)
    if not events:
        raise RuntimeError("CosyVoice streaming response contains no events")
    return events


def _post_streaming(
    url: str,
    *,
    api_key: str,
    payload: dict,
) -> list[dict]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=180) as response:
            return _parse_sse(response.read())
    except error.HTTPError as exc:
        raise RuntimeError(read_http_error(exc)) from exc
    except error.URLError as exc:
        raise RuntimeError(
            f"CosyVoice streaming request failed: {exc.reason}"
        ) from exc


def _ticks(value: object, *, field: str) -> int:
    if isinstance(value, bool):
        raise RuntimeError(f"CosyVoice word {field} is not numeric")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"CosyVoice word {field} is not numeric") from exc
    if not math.isfinite(numeric):
        raise RuntimeError(f"CosyVoice word {field} is not finite")
    return int(round(numeric * _TICKS_PER_MILLISECOND))


def _word_boundaries(events: list[dict]) -> tuple[list[dict], str]:
    sentence_text: dict[int, str] = {}
    sentence_words: dict[int, list] = {}
    audio_url = ""

    for event in events:
        code = event.get("code")
        message = event.get("message")
        if code or message:
            details = ": ".join(str(value) for value in (code, message) if value)
            raise RuntimeError(f"CosyVoice TTS failed: {details}")
        output = event.get("output") or {}
        if not isinstance(output, dict):
            continue
        audio = output.get("audio") or {}
        if isinstance(audio, dict) and isinstance(audio.get("url"), str):
            audio_url = audio["url"]

        sentence = output.get("sentence") or {}
        if not isinstance(sentence, dict):
            continue
        index = sentence.get("index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            continue
        original_text = output.get("original_text")
        if isinstance(original_text, str) and original_text:
            sentence_text[index] = original_text
        words = sentence.get("words")
        if isinstance(words, list) and words:
            sentence_words[index] = words

    if not audio_url:
        raise RuntimeError("CosyVoice streaming response contains no audio URL")
    if not sentence_words:
        raise RuntimeError(
            "CosyVoice returned no word timestamps. Use a cloned voice from "
            "cosyvoice-v3.5-plus/flash, cosyvoice-v3-plus/flash, or cosyvoice-v2, "
            "or a system voice marked as timestamp-supported; otherwise pass "
            "--cosyvoice-audio-only."
        )

    boundaries: list[dict] = []
    for sentence_index in sorted(sentence_words):
        original_text = sentence_text.get(sentence_index, "")
        for item in sentence_words[sentence_index]:
            if not isinstance(item, dict):
                raise RuntimeError("CosyVoice word timing is not an object")
            word = item.get("text")
            begin_index = item.get("begin_index")
            end_index = item.get("end_index")
            if (
                original_text
                and isinstance(begin_index, int)
                and not isinstance(begin_index, bool)
                and isinstance(end_index, int)
                and not isinstance(end_index, bool)
                and 0 <= begin_index < end_index <= len(original_text)
            ):
                word = original_text[begin_index:end_index]
            if not isinstance(word, str) or not word:
                raise RuntimeError("CosyVoice word timing contains no text")
            start = _ticks(item.get("begin_time"), field="start time")
            end = _ticks(item.get("end_time"), field="end time")
            if start < 0 or end <= start:
                raise RuntimeError(
                    "CosyVoice response contains an invalid word interval"
                )
            if boundaries and start < boundaries[-1]["offset"]:
                raise RuntimeError(
                    "CosyVoice word timestamps are not in chronological order"
                )
            boundaries.append({
                "text": word,
                "offset": start,
                "duration": end - start,
            })
    return boundaries, audio_url


def generate(
    text: str,
    output_path: Path,
    *,
    api_key: str,
    voice_id: str,
    model: str,
    audio_format: str,
    sample_rate: int,
    volume: int | None,
    rate: float | None,
    pitch: float | None,
    instruction: str | None,
    language_hint: str | None,
    base_url: str | None,
    subtitle_path: Path | None = None,
    subtitle_max_chars: int = DEFAULT_SUBTITLE_MAX_CHARS,
) -> None:
    input_payload: dict[str, object] = {
        "text": text,
        "voice": voice_id,
        "format": audio_format,
        "sample_rate": sample_rate,
    }
    if volume is not None:
        input_payload["volume"] = volume
    if rate is not None:
        input_payload["rate"] = rate
    if pitch is not None:
        input_payload["pitch"] = pitch
    if instruction:
        input_payload["instruction"] = instruction
    if language_hint:
        input_payload["language_hints"] = [language_hint]

    payload = {
        "model": model,
        "input": input_payload,
    }
    url = resolve_url(base_url)

    if subtitle_path is not None:
        input_payload["word_timestamp_enabled"] = True
        events = _post_streaming(
            url,
            api_key=api_key,
            payload=payload,
        )
        boundaries, audio_url = _word_boundaries(events)
        subtitle = format_word_timed_srt(
            text,
            boundaries,
            subtitle_max_chars,
            provider_label="CosyVoice",
        )
        publish_audio_subtitle(
            get_bytes(audio_url),
            output_path,
            subtitle,
            subtitle_path,
        )
        return

    data = post_json(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        payload=payload,
        timeout=180,
    )
    audio = (data.get("output") or {}).get("audio") or {}
    audio_url = audio.get("url")
    if not audio_url:
        raise RuntimeError(f"CosyVoice response missing audio URL: {data}")
    download_audio(audio_url, output_path)


def print_voices() -> None:
    print("CosyVoice voices are selected by voice.")
    print("Use a system voice name or a cloned/designed voice_id from CosyVoice.")
    print("Timestamp-supported system voice example: longanyang")
    print(
        "For SRT, use a supported CosyVoice cloned voice or a system voice "
        "marked timestamp-supported in the provider catalog."
    )
