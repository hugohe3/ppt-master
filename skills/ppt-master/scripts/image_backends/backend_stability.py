#!/usr/bin/env python3
"""
Stability AI image generation backend.

Configuration keys:
  STABILITY_API_KEY   (required)
  STABILITY_BASE_URL  (optional)
  STABILITY_MODEL     (optional)
"""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

if __name__ == "__main__":
    print(__doc__)
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend stability")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os
import time

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    http_error,
    is_rate_limit_error,
    normalize_image_size,
    report_resolution,
    require_api_key,
    resolve_output_path,
    retry_delay,
)


VALID_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "4:5", "5:4",
    "9:16", "16:9", "9:21", "21:9",
]

DEFAULT_BASE_URL = "https://api.stability.ai"
DEFAULT_MODEL = "stable-image-core"

MODEL_ENDPOINTS = {
    "core": "/v2beta/stable-image/generate/core",
    "stable-image-core": "/v2beta/stable-image/generate/core",
    "ultra": "/v2beta/stable-image/generate/ultra",
    "stable-image-ultra": "/v2beta/stable-image/generate/ultra",
}


def _validate_request_options(aspect_ratio: str, image_size: str) -> None:
    """Validate unified request options before any retryable work."""
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for Stability backend. "
            f"Supported: {VALID_ASPECT_RATIOS}"
        )
    normalized_size = normalize_image_size(image_size)
    if normalized_size != "1K":
        raise ValueError(
            "Stability Core and Ultra generation only support the default '1K' preset; "
            f"got '{image_size}'. Use a Stability upscale endpoint for larger output."
        )


def _resolve_endpoint(model: str | None, base_url: str) -> tuple[str, str]:
    """Resolve the Stability model alias and endpoint URL."""
    resolved_model = model or DEFAULT_MODEL

    normalized_model = resolved_model.lower()
    endpoint = MODEL_ENDPOINTS.get(normalized_model)
    if not endpoint:
        supported = sorted(MODEL_ENDPOINTS)
        raise ValueError(
            f"Unsupported Stability model '{resolved_model}'. Supported aliases: {supported}"
        )
    return normalized_model, base_url.rstrip("/") + endpoint


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str | None = None, base_url: str = DEFAULT_BASE_URL) -> str:
    """Generate one image with the Stability backend."""
    _validate_request_options(aspect_ratio, image_size)

    resolved_model, url = _resolve_endpoint(model, base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }
    data = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
    }

    print("[Stability AI]")
    print(f"  Model:        {resolved_model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Preset Size:  {image_size}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()

    response = requests.post(
        url,
        headers=headers,
        data=data,
        files={"none": ""},
        timeout=300,
    )
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "Stability generation")

    path = resolve_output_path(prompt, output_dir, filename, ".png")
    with open(path, "wb") as f:
        f.write(response.content)
    print(f"  File saved to: {path}")
    report_resolution(path)
    return path


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the Stability backend."""
    base_url = os.environ.get("STABILITY_BASE_URL") or DEFAULT_BASE_URL
    resolved_model = model or os.environ.get("STABILITY_MODEL")
    _validate_request_options(aspect_ratio, image_size)
    _resolve_endpoint(resolved_model, base_url)
    api_key = require_api_key(
        "STABILITY_API_KEY",
        message="No API key found. Set STABILITY_API_KEY in the current environment or a .env file.",
    )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(
                api_key=api_key,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                output_dir=output_dir,
                filename=filename,
                model=resolved_model,
                base_url=base_url,
            )
        except Exception as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            limited = is_rate_limit_error(exc)
            delay = retry_delay(attempt, rate_limited=limited)
            label = "Rate limit hit" if limited else f"Error: {exc}"
            print(f"\n  [WARN] {label}. Retrying in {delay}s...")
            time.sleep(delay)

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")
