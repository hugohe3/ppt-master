#!/usr/bin/env python3
"""
Agnes Image 2.1 Flash generation backend.

Configuration keys:
  AGNES_API_KEY   (required)
  AGNES_BASE_URL  (optional)
  AGNES_MODEL     (optional)
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend agnes")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os
import time

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    download_image,
    http_error,
    is_rate_limit_error,
    normalize_image_size,
    require_api_key,
    resolve_output_path,
    retry_delay,
)


DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1/images/generations"
DEFAULT_MODEL = "agnes-image-2.1-flash"

ASPECT_RATIO_SIZE_MAP = {
    "512px": {
        "1:1": "512x512",
        "4:3": "512x384",
        "3:4": "384x512",
        "16:9": "512x288",
        "9:16": "288x512",
    },
    "1K": {
        "1:1": "1024x1024",
        "4:3": "1024x768",
        "3:4": "768x1024",
        "16:9": "1024x576",
        "9:16": "576x1024",
    },
    "2K": {
        "1:1": "1440x1440",
        "4:3": "1440x1080",
        "3:4": "1080x1440",
        "16:9": "1440x810",
        "9:16": "810x1440",
    },
    "4K": {
        "1:1": "2048x2048",
        "4:3": "2048x1536",
        "3:4": "1536x2048",
        "16:9": "2048x1152",
        "9:16": "1152x2048",
    },
}


def _resolve_size(aspect_ratio: str, image_size: str) -> str:
    """Resolve the target resolution for a ratio and logical size preset."""
    normalized = normalize_image_size(image_size)
    size = (ASPECT_RATIO_SIZE_MAP.get(normalized) or {}).get(aspect_ratio)
    if not size:
        supported = sorted(ASPECT_RATIO_SIZE_MAP["1K"])
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for Agnes backend. "
            f"Supported: {supported}"
        )
    return size


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> str:
    """Generate one image with the Agnes backend."""
    size = _resolve_size(aspect_ratio, image_size)
    url = base_url.rstrip("/")
    if not url.endswith("/v1/images/generations"):
        url = url + "/v1/images/generations"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "extra_body": {
            "response_format": "url",
        },
    }

    print("[Agnes Image 2.1 Flash]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution:   {size}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=360)
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "Agnes image generation")

    data = response.json()
    items = data.get("data") or []
    image_url = items[0].get("url") if items else None
    if not image_url:
        raise RuntimeError(f"Agnes response missing image URL: {data}")

    path = resolve_output_path(prompt, output_dir, filename, ".png")
    return download_image(image_url, path)


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the Agnes backend."""
    api_key = require_api_key(
        "AGNES_API_KEY",
        message="No API key found. Set AGNES_API_KEY in the current environment or a .env file.",
    )
    base_url = os.environ.get("AGNES_BASE_URL") or DEFAULT_BASE_URL
    resolved_model = model or os.environ.get("AGNES_MODEL") or DEFAULT_MODEL

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
