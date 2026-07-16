#!/usr/bin/env python3
"""Nano Banana Pro reference-image generation through Google GenAI HTTP."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from image_backends.backend_common import (  # noqa: E402
    MAX_RETRIES,
    download_image,
    http_error,
    require_api_key,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)


configure_utf8_stdio()

DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3-pro-image-preview"
DEFAULT_IMAGE_SIZE = "2K"


def _model(value: str | None = None) -> str:
    model = (value or os.environ.get("GOOGLE_GENAI_MODEL") or DEFAULT_MODEL).strip()
    aliases = {"gemini-3-pro-image": DEFAULT_MODEL}
    return aliases.get(model, model)


def _endpoint(model: str) -> str:
    endpoint = (os.environ.get("GOOGLE_GENAI_ENDPOINT") or DEFAULT_ENDPOINT).strip()
    return endpoint.replace("{model}", model).replace("{modeName}", model)


def _request_url(endpoint: str, api_key: str) -> str:
    if "googleapis.com" in endpoint:
        return endpoint
    parts = urlsplit(endpoint)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault("key", api_key)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _headers(endpoint: str, api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if "googleapis.com" in endpoint and not api_key.startswith("sk-"):
        headers["x-goog-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _image_size(value: str) -> str:
    normalized = value.strip().upper()
    if normalized != DEFAULT_IMAGE_SIZE:
        raise ValueError(
            "The nanobanana-pro-2K profile requires image_size=2K."
        )
    return normalized


def _inline_image(path_value: str, *, redact: bool = False) -> dict[str, str]:
    path = Path(path_value)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = "<base64 omitted>" if redact else base64.b64encode(path.read_bytes()).decode("ascii")
    return {"mime_type": mime, "data": data}


def _use_response_format() -> bool:
    value = os.environ.get("GOOGLE_GENAI_USE_RESPONSE_FORMAT", "1").strip().lower()
    return value not in {"0", "false", "no"}


def _request_body(
    prompt: str,
    aspect_ratio: str,
    image_size: str,
    reference_images: list[str],
    *,
    redact: bool = False,
) -> dict:
    size = _image_size(image_size)
    full_prompt = (
        f"{prompt.rstrip()}\n\n"
        f"Output aspect ratio requirement: {aspect_ratio}.\n"
        f"Output image size requirement: {size}."
    )
    parts: list[dict] = [{"text": full_prompt}]
    parts.extend(
        {"inline_data": _inline_image(path, redact=redact)}
        for path in reference_images
    )
    body: dict = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    if _use_response_format():
        body["response_format"] = {
            "aspect_ratio": aspect_ratio,
            "image_size": size,
        }
    else:
        body["generationConfig"]["imageConfig"] = {
            "aspectRatio": aspect_ratio,
            "imageSize": size,
        }
    return body


def build_redacted_request(
    *,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
    reference_images: list[str],
    model: str | None = None,
    quality: str | None = None,
) -> dict:
    """Build a secret-free Google GenAI request preview."""
    del quality
    resolved_model = _model(model)
    return {
        "method": "POST",
        "endpoint": _endpoint(resolved_model),
        "content_type": "application/json",
        "model": resolved_model,
        "body": _request_body(
            prompt,
            aspect_ratio,
            image_size,
            reference_images,
            redact=True,
        ),
    }


def _find_output(value) -> tuple[str, str] | None:
    if isinstance(value, dict):
        inline = value.get("inlineData") or value.get("inline_data")
        if isinstance(inline, dict) and inline.get("data"):
            return "base64", str(inline["data"])
        encoded = value.get("b64_json")
        if isinstance(encoded, str) and encoded:
            return "base64", encoded
        for key in ("url", "imageUrl", "image_url", "outputUrl", "output_url"):
            url = value.get(key)
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                return "url", url
        for child in value.values():
            found = _find_output(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_output(child)
            if found:
                return found
    return None


def _extract_output(payload: dict, output_path: str) -> str:
    found = _find_output(payload)
    if not found:
        raise RuntimeError("Nano Banana Pro response contains no image output")
    output_type, value = found
    if output_type == "url":
        return download_image(value, output_path)
    try:
        image_bytes = base64.b64decode(value)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("Nano Banana Pro returned invalid base64 image data") from exc
    return save_image_bytes(image_bytes, output_path)


def _write_run_record(
    output_path: str,
    request_preview: dict,
    *,
    status: str,
    error: str = "",
) -> None:
    record = {
        "schema_version": 1,
        "provider_profile": "nanobanana-pro-2K",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "request": request_preview,
    }
    if error:
        record["error"] = error[:500]
    Path(output_path).with_suffix(".generation.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generate(
    prompt: str,
    aspect_ratio: str = "1:1",
    image_size: str = DEFAULT_IMAGE_SIZE,
    output_dir: str | None = None,
    filename: str | None = None,
    model: str | None = None,
    max_retries: int = MAX_RETRIES,
    reference_images: list[str] | None = None,
    quality: str | None = None,
) -> str:
    """Generate one 2K image from text and optional reference images."""
    del quality
    references = [str(Path(path).resolve()) for path in (reference_images or [])]
    missing = [path for path in references if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"Reference image not found: {missing[0]}")

    api_key = require_api_key(
        "GOOGLE_GENAI_API_KEY",
        "GEMINI_API_KEY",
        message=(
            "No Nano Banana Pro key found. Set GOOGLE_GENAI_API_KEY "
            "or GEMINI_API_KEY in the current environment or .env file."
        ),
    )
    resolved_model = _model(model)
    endpoint = _endpoint(resolved_model)
    output_path = resolve_output_path(prompt, output_dir, filename, ext=".png")
    preview = build_redacted_request(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        reference_images=references,
        model=resolved_model,
    )
    body = _request_body(prompt, aspect_ratio, image_size, references)

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                _request_url(endpoint, api_key),
                headers=_headers(endpoint, api_key),
                json=body,
                timeout=max(30, int(os.environ.get("GOOGLE_GENAI_TIMEOUT", "300"))),
            )
            if response.status_code >= 400:
                raise http_error(response, "Nano Banana Pro")
            saved = _extract_output(response.json(), output_path)
            _write_run_record(output_path, preview, status="Generated")
            return saved
        except (OSError, ValueError, RuntimeError, requests.RequestException) as exc:
            last_error = exc
            if attempt >= max_retries:
                _write_run_record(output_path, preview, status="Failed", error=str(exc))
                raise RuntimeError(
                    f"Nano Banana Pro failed after {attempt + 1} attempt(s): {exc}"
                ) from exc
            time.sleep(retry_delay(attempt, "429" in str(exc)))
    raise RuntimeError(f"Nano Banana Pro failed: {last_error}")


if __name__ == "__main__":
    print(__doc__)
    print("Use via: python skills/ppt-master/scripts/image_gen.py --manifest <image_prompts.json>")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)
