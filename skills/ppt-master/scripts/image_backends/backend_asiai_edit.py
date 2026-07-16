#!/usr/bin/env python3
"""GPT Image 2 reference-image editing through the asiai multipart API."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path

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

DEFAULT_ENDPOINT = "https://api.asiai.cloud/v1/images/edits"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_QUALITY = "medium"


def _normalized_endpoint(value: str | None = None) -> str:
    """Force stale generations overrides onto the asiai image-edit contract."""
    endpoint = (value or os.environ.get("ASIAI_GPT_IMAGE_ENDPOINT") or DEFAULT_ENDPOINT).strip()
    endpoint = endpoint.rstrip("/")
    for suffix in ("/v1/images/generations", "/images/generations"):
        if endpoint.endswith(suffix):
            return endpoint[: -len(suffix)] + "/v1/images/edits"
    return endpoint


def _size(aspect_ratio: str, image_size: str) -> str:
    normalized = image_size.strip().upper()
    if normalized not in {"1K", "1024", "1024PX"}:
        raise ValueError(
            "The GPT Image 2 profiles currently support only 1K. "
            "Use image_size=1K."
        )
    if aspect_ratio in {"2:3", "3:4", "4:5", "9:16"}:
        return "1024x1536"
    if aspect_ratio in {"3:2", "4:3", "5:4", "16:9", "21:9"}:
        return "1536x1024"
    return "1024x1024"


def build_redacted_request(
    *,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
    reference_images: list[str],
    model: str | None = None,
    quality: str | None = None,
) -> dict:
    """Build a secret-free request preview for dry-run validation."""
    return {
        "method": "POST",
        "endpoint": _normalized_endpoint(),
        "content_type": "multipart/form-data",
        "fields": {
            "model": model or os.environ.get("ASIAI_GPT_IMAGE_MODEL") or DEFAULT_MODEL,
            "prompt": prompt,
            "size": _size(aspect_ratio, image_size),
            "quality": quality or os.environ.get("ASIAI_GPT_IMAGE_QUALITY") or DEFAULT_QUALITY,
            "n": 1,
        },
        "image[]": [Path(path).name for path in reference_images],
    }


def _extract_output(payload: dict, output_path: str) -> str:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise RuntimeError("GPT Image 2 response contains no data[] image output")
    first = data[0]
    if not isinstance(first, dict):
        raise RuntimeError("GPT Image 2 response data[0] is invalid")
    encoded = first.get("b64_json")
    if encoded:
        try:
            image_bytes = base64.b64decode(encoded)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("GPT Image 2 returned invalid b64_json") from exc
        return save_image_bytes(image_bytes, output_path)
    url = first.get("url")
    if url:
        return download_image(str(url), output_path)
    raise RuntimeError("GPT Image 2 response contains neither url nor b64_json")


def _write_run_record(
    output_path: str,
    request_preview: dict,
    *,
    status: str,
    error: str = "",
) -> None:
    record = {
        "schema_version": 1,
        "provider_profile": (
            "gptimage2.0-1K-mid"
            if request_preview.get("fields", {}).get("quality") == "medium"
            else "gptimage2.0-1K-low"
        ),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "request": request_preview,
    }
    if error:
        record["error"] = error[:500]
    path = Path(output_path).with_suffix(".generation.json")
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate(
    prompt: str,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    output_dir: str | None = None,
    filename: str | None = None,
    model: str | None = None,
    max_retries: int = MAX_RETRIES,
    reference_images: list[str] | None = None,
    quality: str | None = None,
) -> str:
    """Edit one or more reference images and save the generated result."""
    references = [str(Path(path).resolve()) for path in (reference_images or [])]
    if not references:
        raise ValueError(
            "The asiai-edit backend requires reference_images. "
            "Use the openai backend for text-only generation."
        )
    missing = [path for path in references if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"Reference image not found: {missing[0]}")

    api_key = require_api_key(
        "ASIAI_GPT_IMAGE_API_KEY",
        "ASIAI_API_KEY",
        message=(
            "No GPT Image 2 edit key found. Set ASIAI_GPT_IMAGE_API_KEY "
            "in the current environment or .env file."
        ),
    )
    endpoint = _normalized_endpoint()
    resolved_model = model or os.environ.get("ASIAI_GPT_IMAGE_MODEL") or DEFAULT_MODEL
    resolved_quality = quality or os.environ.get("ASIAI_GPT_IMAGE_QUALITY") or DEFAULT_QUALITY
    output_path = resolve_output_path(prompt, output_dir, filename, ext=".png")
    preview = build_redacted_request(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        reference_images=references,
        model=resolved_model,
        quality=resolved_quality,
    )

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        handles = []
        try:
            files = []
            for path_value in references:
                path = Path(path_value)
                handle = path.open("rb")
                handles.append(handle)
                mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                files.append(("image[]", (path.name, handle, mime)))
            response = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                data=preview["fields"],
                files=files,
                timeout=max(30, int(os.environ.get("ASIAI_GPT_IMAGE_TIMEOUT", "300"))),
            )
            if response.status_code >= 400:
                raise http_error(response, "GPT Image 2 edit")
            saved = _extract_output(response.json(), output_path)
            _write_run_record(output_path, preview, status="Generated")
            return saved
        except (OSError, ValueError, RuntimeError, requests.RequestException) as exc:
            last_error = exc
            if attempt >= max_retries:
                _write_run_record(output_path, preview, status="Failed", error=str(exc))
                raise RuntimeError(f"GPT Image 2 edit failed after {attempt + 1} attempt(s): {exc}") from exc
            time.sleep(retry_delay(attempt, "429" in str(exc)))
        finally:
            for handle in handles:
                handle.close()
    raise RuntimeError(f"GPT Image 2 edit failed: {last_error}")


if __name__ == "__main__":
    print(__doc__)
    print("Use via: python skills/ppt-master/scripts/image_gen.py --manifest <image_prompts.json>")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)
