#!/usr/bin/env python3
"""
fal.ai image generation backend.

Configuration keys:
  FAL_KEY / FAL_API_KEY   (required)
  FAL_BASE_URL            (optional)
  FAL_MODEL               (optional; nano-banana-2 only)
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend fal")
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


VALID_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1",
    "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
]
DEFAULT_ENDPOINT = "https://fal.run"
DEFAULT_MODEL = "fal-ai/nano-banana-2"
SUPPORTED_MODELS = {DEFAULT_MODEL}

IMAGE_SIZE_TO_RESOLUTION = {
    "512px": "0.5K",
    "1K": "1K",
    "2K": "2K",
    "4K": "4K",
}


def _resolve_request_options(
    aspect_ratio: str,
    image_size: str,
    model: str,
) -> tuple[str, str]:
    """Validate request options and return normalized model and resolution values."""
    resolved_model = model.strip()
    if resolved_model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported fal model '{model}'. Supported: {sorted(SUPPORTED_MODELS)}"
        )
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for fal backend. "
            f"Supported: {VALID_ASPECT_RATIOS}"
        )
    normalized_size = normalize_image_size(image_size)
    resolution = IMAGE_SIZE_TO_RESOLUTION.get(normalized_size)
    if not resolution:
        raise ValueError(
            f"Unsupported image size '{image_size}' for fal backend. "
            f"Supported: {list(IMAGE_SIZE_TO_RESOLUTION)}"
        )
    return resolved_model, resolution


def _resolve_url(base_url: str, model: str) -> str:
    """Resolve the full fal endpoint URL for a model."""
    base = base_url.rstrip("/")
    if base.endswith(model):
        return base
    return f"{base}/{model}"


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_ENDPOINT) -> str:
    """Generate one image with the fal.ai backend."""
    model, resolution = _resolve_request_options(aspect_ratio, image_size, model)

    url = _resolve_url(base_url, model)
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "resolution": resolution,
    }

    print("[fal.ai]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution:   {resolution}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "fal image generation")

    data = response.json()
    images = data.get("images") or []
    image_url = images[0].get("url") if images else None
    if not image_url:
        raise RuntimeError(f"fal response missing image URL: {data}")

    path = resolve_output_path(prompt, output_dir, filename, ".png")
    return download_image(image_url, path)


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the fal.ai backend."""
    resolved_model = model or os.environ.get("FAL_MODEL") or DEFAULT_MODEL
    _resolve_request_options(aspect_ratio, image_size, resolved_model)
    api_key = require_api_key(
        "FAL_KEY",
        "FAL_API_KEY",
        message="No API key found. Set FAL_KEY or FAL_API_KEY in the current environment or a .env file.",
    )
    base_url = os.environ.get("FAL_BASE_URL") or DEFAULT_ENDPOINT

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
