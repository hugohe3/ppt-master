#!/usr/bin/env python3
"""
Volcengine Seedream image generation backend.

Configuration keys:
  LAS_API_KEY / VOLCENGINE_API_KEY / ARK_API_KEY   (required)
  VOLCENGINE_BASE_URL                (optional)
  VOLCENGINE_MODEL                   (optional; Seedream 4.5 only)
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend volcengine")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os
import time

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    download_image,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    normalize_image_size,
    require_api_key,
    resolve_output_path,
    retry_delay,
)


DEFAULT_ENDPOINT = "https://operator.las.cn-beijing.volces.com/api/v1/images/generations"
DEFAULT_MODEL = "doubao-seedream-4-5-251128"
DEFAULT_IMAGE_SIZE = "2K"
SUPPORTED_MODELS = {DEFAULT_MODEL}

ASPECT_RATIO_SIZE_MAP = {
    "2K": {
        "1:1": "2048x2048",
        "2:3": "1664x2496",
        "3:2": "2496x1664",
        "3:4": "1728x2304",
        "4:3": "2304x1728",
        "9:16": "1600x2848",
        "16:9": "2848x1600",
        "21:9": "3136x1344",
    },
    "4K": {
        "1:1": "4096x4096",
        "2:3": "3328x4992",
        "3:2": "4992x3328",
        "3:4": "3520x4704",
        "4:3": "4704x3520",
        "9:16": "3040x5504",
        "16:9": "5504x3040",
        "21:9": "6240x2656",
    },
}


def _validate_model(model: str) -> str:
    """Limit the backend to the Seedream 4.5 contract implemented below."""
    resolved = model.strip()
    if resolved not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported Volcengine model '{model}'. Supported: {sorted(SUPPORTED_MODELS)}"
        )
    return resolved


def _resolve_url(base_url: str) -> str:
    """Resolve the Volcengine generation endpoint."""
    base = base_url.rstrip("/")
    if base.endswith("/images/generations"):
        return base
    if base.endswith("/api/v1"):
        return base + "/images/generations"
    return base + "/api/v1/images/generations"


def _resolve_size(aspect_ratio: str, image_size: str) -> str:
    """Resolve the target resolution for a ratio and logical size preset."""
    normalized = normalize_image_size(image_size)
    sizes = ASPECT_RATIO_SIZE_MAP.get(normalized)
    if sizes is None:
        supported_sizes = ", ".join(ASPECT_RATIO_SIZE_MAP)
        raise ValueError(
            f"Unsupported image size '{image_size}' for Volcengine backend. "
            f"Seedream 4.5 supports these sizes: {supported_sizes}."
        )
    size = sizes.get(aspect_ratio)
    if not size:
        supported = sorted(sizes)
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for Volcengine backend. "
            f"Supported: {supported}"
        )
    return size


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = DEFAULT_IMAGE_SIZE,
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_ENDPOINT) -> str:
    """Generate one image with the Volcengine backend."""
    model = _validate_model(model)
    size = _resolve_size(aspect_ratio, image_size)
    url = _resolve_url(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": False,
    }

    print("[Volcengine Seedream]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution:   {size}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "Volcengine image generation")

    data = response.json()
    items = data.get("data") or []
    image_url = items[0].get("url") if items else None
    if not image_url:
        raise RuntimeError(f"Volcengine response missing image URL: {data}")

    path = resolve_output_path(prompt, output_dir, filename, ".jpeg")
    return download_image(image_url, path)


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = DEFAULT_IMAGE_SIZE,
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the Volcengine backend."""
    resolved_model = model or os.environ.get("VOLCENGINE_MODEL") or DEFAULT_MODEL
    _validate_model(resolved_model)
    normalized_size = normalize_image_size(image_size)
    _resolve_size(aspect_ratio, normalized_size)
    api_key = require_api_key(
        "LAS_API_KEY",
        "VOLCENGINE_API_KEY",
        "ARK_API_KEY",
        message=(
            "No API key found. Set LAS_API_KEY, VOLCENGINE_API_KEY, or "
            "ARK_API_KEY in the current environment or a .env file."
        ),
    )
    base_url = os.environ.get("VOLCENGINE_BASE_URL") or DEFAULT_ENDPOINT

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
