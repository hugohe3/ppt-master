#!/usr/bin/env python3
"""
MiniMax image generation backend.

Configuration keys:
  MINIMAX_API_KEY   (required)
  MINIMAX_BASE_URL  (optional)
  MINIMAX_MODEL     (optional; image-01 only)
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend minimax")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import base64
import os
import time

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    detect_image_extension,
    download_image,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    normalize_image_size,
    require_api_key,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)


DEFAULT_ENDPOINT = "https://api.minimaxi.com/v1/image_generation"
DEFAULT_MODEL = "image-01"
SUPPORTED_MODELS = {DEFAULT_MODEL}

# Request the documented default response format. The API returns hosted links
# in `data.image_urls` for "url" and inline strings in `data.image_base64` for
# "base64"; both shapes are handled when the response is parsed.
DEFAULT_RESPONSE_FORMAT = "url"

# International fallback: set MINIMAX_BASE_URL=https://api.minimax.io if needed

ASPECT_RATIO_SIZE_MAP = {
    "512px": {
        "1:1": (512, 512),
        "16:9": (912, 512),
        "4:3": (680, 512),
        "3:2": (768, 512),
        "2:3": (512, 768),
        "3:4": (512, 680),
        "9:16": (512, 912),
        "21:9": (1192, 512),
    },
    "1K": {
        "1:1": (1024, 1024),
        "16:9": (1280, 720),
        "4:3": (1152, 864),
        "3:2": (1248, 832),
        "2:3": (832, 1248),
        "3:4": (864, 1152),
        "9:16": (720, 1280),
        "21:9": (1344, 576),
    },
    "2K": {
        "1:1": (2048, 2048),
        "16:9": (2048, 1152),
        "4:3": (2048, 1536),
        "3:2": (2048, 1368),
        "2:3": (1368, 2048),
        "3:4": (1536, 2048),
        "9:16": (1152, 2048),
        "21:9": (2048, 880),
    },
}


def _validate_model(model: str) -> str:
    """Limit the backend to the model contract implemented below."""
    resolved = model.strip()
    if resolved not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported MiniMax model '{model}'. Supported: {sorted(SUPPORTED_MODELS)}"
        )
    return resolved


def _resolve_url(base_url: str) -> str:
    """Resolve the MiniMax image generation endpoint.

    Accepts three forms of MINIMAX_BASE_URL:
      - Full endpoint:  https://api.minimax.io/v1/image_generation  → used as-is
      - Versioned base: https://api.minimax.io/v1                   → appends /image_generation
      - Root base:      https://api.minimax.io                      → appends /v1/image_generation
    """
    base = base_url.rstrip("/")
    if base.endswith("/image_generation"):
        return base
    if base.endswith("/v1"):
        return base + "/image_generation"
    return base + "/v1/image_generation"


def _resolve_dimensions(aspect_ratio: str, image_size: str) -> tuple[int, int]:
    """Resolve width and height from the unified aspect_ratio/image_size pair."""
    normalized = normalize_image_size(image_size)
    sizes = ASPECT_RATIO_SIZE_MAP.get(normalized)
    if sizes is None:
        supported_sizes = ", ".join(ASPECT_RATIO_SIZE_MAP)
        raise ValueError(
            f"Unsupported image size '{image_size}' for MiniMax backend. "
            f"image-01 supports these logical sizes: {supported_sizes}."
        )
    dimensions = sizes.get(aspect_ratio)
    if not dimensions:
        supported = sorted(sizes)
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for MiniMax backend. "
            f"Supported: {supported}"
        )
    return dimensions


def _extract_image_bytes(payload: dict) -> bytes | None:
    """Extract inline base64 image bytes from a MiniMax response payload."""
    data = payload.get("data") or {}
    image_base64 = data.get("image_base64") or []
    if image_base64:
        return base64.b64decode(image_base64[0])
    return None


def _extract_image_url(payload: dict) -> str | None:
    """Extract the first hosted image URL from a MiniMax response payload."""
    data = payload.get("data") or {}
    image_urls = data.get("image_urls") or []
    if image_urls:
        return image_urls[0]
    return None


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_ENDPOINT) -> str:
    """Generate one image with the MiniMax backend."""
    model = _validate_model(model)
    width, height = _resolve_dimensions(aspect_ratio, image_size)
    url = _resolve_url(base_url)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "width": width,
        "height": height,
        "response_format": DEFAULT_RESPONSE_FORMAT,
        "n": 1,
    }

    print("[MiniMax Image]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution:   {width}x{height} (from image_size={image_size})")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "MiniMax image generation")

    data = response.json()
    base_resp = data.get("base_resp") or {}
    if base_resp.get("status_code") not in (None, 0, "0"):
        raise RuntimeError(f"MiniMax image generation failed: {data}")

    image_bytes = _extract_image_bytes(data)
    if image_bytes:
        ext = detect_image_extension(image_bytes) or ".jpeg"
        path = resolve_output_path(prompt, output_dir, filename, ext)
        return save_image_bytes(image_bytes, path)

    image_url = _extract_image_url(data)
    if image_url:
        # image-01 serves JPEG; save_image_bytes realigns the extension when the
        # downloaded bytes are a different format.
        path = resolve_output_path(prompt, output_dir, filename, ".jpeg")
        return download_image(image_url, path)

    raise RuntimeError(f"MiniMax response missing image data: {data}")


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the MiniMax backend."""
    resolved_model = model or os.environ.get("MINIMAX_MODEL") or DEFAULT_MODEL
    _validate_model(resolved_model)
    normalized_size = normalize_image_size(image_size)
    _resolve_dimensions(aspect_ratio, normalized_size)
    api_key = require_api_key(
        "MINIMAX_API_KEY",
        message="No API key found. Set MINIMAX_API_KEY in the current environment or a .env file.",
    )
    base_url = os.environ.get("MINIMAX_BASE_URL") or DEFAULT_ENDPOINT

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(
                api_key=api_key,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=normalized_size,
                output_dir=output_dir,
                filename=filename,
                model=resolved_model,
                base_url=base_url,
            )
        except Exception as exc:
            last_error = exc
            if is_permanent_error(exc):
                raise
            if attempt >= max_retries:
                break
            limited = is_rate_limit_error(exc)
            delay = retry_delay(attempt, rate_limited=limited)
            label = "Rate limit hit" if limited else f"Error: {exc}"
            print(f"\n  [WARN] {label}. Retrying in {delay}s...")
            time.sleep(delay)

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")
