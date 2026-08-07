"""Shared helpers for TTS backends."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from urllib import error, request


def read_api_key(*env_names: str, label: str) -> str:
    for env_name in env_names:
        api_key = os.environ.get(env_name, "").strip()
        if api_key:
            return api_key
    joined = " or ".join(env_names)
    raise RuntimeError(f"Missing {label} API key. Set {joined}=<key>.")


def read_http_error(exc: error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return f"HTTP {exc.code}: {body or exc.reason}"


def post_json(url: str, *, headers: dict[str, str], payload: dict, timeout: int = 120) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(read_http_error(exc)) from exc
    except error.URLError as exc:
        raise RuntimeError(f"HTTP request failed: {exc.reason}") from exc


def get_bytes(url: str, *, timeout: int = 180) -> bytes:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except error.HTTPError as exc:
        raise RuntimeError(read_http_error(exc)) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Audio download failed: {exc.reason}") from exc


def download_audio(url: str, output_path: Path) -> None:
    publish_audio_bytes(get_bytes(url), output_path)


def temporary_path(target: Path, suffix: str) -> tuple[int, Path]:
    """Create a temporary file beside its eventual target."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=suffix,
        dir=target.parent,
    )
    return descriptor, Path(raw_path)


def publish_staged_pair(
    staged_first: Path,
    first_target: Path,
    staged_second: Path,
    second_target: Path,
) -> None:
    """Publish two staged files together, restoring prior targets on failure."""
    targets = (first_target, second_target)
    if first_target.resolve() == second_target.resolve():
        raise ValueError("paired outputs must use different paths")

    backups: dict[Path, Path] = {}
    published: set[Path] = set()
    try:
        for target in targets:
            if not target.exists():
                continue
            descriptor, backup = temporary_path(target, ".bak")
            os.close(descriptor)
            backup.unlink()
            os.replace(target, backup)
            backups[target] = backup

        for staged, target in (
            (staged_first, first_target),
            (staged_second, second_target),
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
        staged_first.unlink(missing_ok=True)
        staged_second.unlink(missing_ok=True)
        for backup in backups.values():
            backup.unlink(missing_ok=True)


def publish_audio_bytes(audio: bytes, output_path: Path) -> None:
    """Publish non-empty provider audio without exposing a partial target."""
    if not audio:
        raise RuntimeError("TTS provider returned empty audio data")

    descriptor, staged_path = temporary_path(output_path, ".tmp")
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(audio)
            stream.flush()
            os.fsync(stream.fileno())
        if staged_path.stat().st_size <= 0:
            raise RuntimeError("TTS provider returned empty audio data")
        os.replace(staged_path, output_path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        staged_path.unlink(missing_ok=True)


def publish_audio_subtitle(
    audio: bytes,
    output_path: Path,
    subtitle: str,
    subtitle_path: Path,
) -> None:
    """Publish one audio/SRT pair without exposing mismatched targets."""
    if not audio:
        raise RuntimeError("TTS provider returned empty audio data")
    if not subtitle.strip():
        raise RuntimeError("TTS provider returned empty subtitle data")

    audio_descriptor = -1
    subtitle_descriptor = -1
    staged_audio: Path | None = None
    staged_subtitle: Path | None = None
    try:
        audio_descriptor, staged_audio = temporary_path(output_path, ".tmp")
        subtitle_descriptor, staged_subtitle = temporary_path(subtitle_path, ".tmp")

        audio_stream = os.fdopen(audio_descriptor, "wb")
        audio_descriptor = -1
        with audio_stream:
            audio_stream.write(audio)
            audio_stream.flush()
            os.fsync(audio_stream.fileno())

        subtitle_stream = os.fdopen(
            subtitle_descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        )
        subtitle_descriptor = -1
        with subtitle_stream:
            subtitle_stream.write(subtitle)
            subtitle_stream.flush()
            os.fsync(subtitle_stream.fileno())

        publish_staged_pair(
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


def extension_from_format(audio_format: str) -> str:
    normalized = audio_format.strip().lower()
    if normalized in {"mp3", "wav"}:
        return f".{normalized}"
    raise RuntimeError(
        f"Unsupported audio format for PPT narration: {audio_format}. "
        "Use mp3 or wav, or transcode provider output before embedding."
    )
