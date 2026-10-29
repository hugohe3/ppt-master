#!/usr/bin/env python3
"""
Tencent Cloud TokenHub image generation backend.

Configuration keys:
  TENCENT_API_KEY / TOKENHUB_API_KEY   (required)
  TENCENT_BASE_URL                    (optional; domestic base or full endpoint)
  TENCENT_MODEL                       (optional; defaults to hy-image-v3)
  TENCENT_REVISE                      (optional; Hy only, defaults to true)
  TENCENT_WATERMARK                   (optional; Seedream only, defaults to false)
  TENCENT_OUTPUT_FORMAT               (optional; Seedream only, png or jpeg)
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend tencent")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import base64
import math
import os
import time

import requests

from image_backends.backend_common import (  # noqa: E402
    MAX_RETRIES,
    download_image,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    bounded_ratio,
    fit_size,
    normalize_image_size,
    note_aspect_ratio,
    require_api_key,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)


DEFAULT_BASE_URL = "https://tokenhub.tencentmaas.com"
DEFAULT_MODEL = "hy-image-v3"
MODEL_ENDPOINTS = {
    DEFAULT_MODEL: "/v1/wand/hunyuan-image/v3-generation",
    "seedream-image-v5.0-pro": "/v1/wand/si-image/generation",
    "seedream-image-v5.0-lite": "/v1/wand/si-image/generation",
}
SUPPORTED_MODELS = set(MODEL_ENDPOINTS)
IMAGE_SIZE_PIXELS = {"512px": 512, "1K": 1024, "2K": 2048, "4K": 4096}
# Official output limits; a size outside them is refitted, never rejected.
MODEL_SIZE_LIMITS = {
    DEFAULT_MODEL: {"min_edge": 512, "max_edge": 2048, "max_pixels": 1024 * 1024},
    "seedream-image-v5.0-pro": {"min_pixels": 921_600, "max_pixels": 4_624_220, "max_ratio": 16},
    "seedream-image-v5.0-lite": {"min_pixels": 3_686_400, "max_pixels": 16_777_216, "max_ratio": 16},
}


def _validate_model(model: str) -> str:
    """Limit the backend to the synchronous TokenHub image contracts."""
    resolved = model.strip()
    if resolved not in SUPPORTED_MODELS:
        detail = ""
        if resolved.startswith("vidu"):
            detail = " Vidu uses an asynchronous submit/query API that is not supported."
        raise ValueError(
            f"Unsupported Tencent model '{model}'. Supported: {sorted(SUPPORTED_MODELS)}.{detail}"
        )
    return resolved


def _resolve_url(base_url: str, model: str = DEFAULT_MODEL) -> str:
    """Resolve the model endpoint while accepting a full TokenHub URL."""
    base = base_url.strip().rstrip("/")
    if "/v1/wand/" in base:
        return base
    return base + MODEL_ENDPOINTS[model]


def _within_limits(width: int, height: int, limits: dict) -> bool:
    """Return whether a size satisfies one model's output limits."""
    long_edge, short_edge = max(width, height), min(width, height)
    return (
        short_edge >= limits.get("min_edge", 1)
        and long_edge <= limits.get("max_edge", long_edge)
        and limits.get("min_pixels", 0) <= width * height <= limits.get("max_pixels", width * height)
        and long_edge / short_edge <= limits.get("max_ratio", math.inf)
    )


def _resolve_size(aspect_ratio: str, image_size: str, model: str = DEFAULT_MODEL) -> str:
    """Resolve a pixel size from the requested area and aspect ratio."""
    normalized = normalize_image_size(image_size)
    pixels = IMAGE_SIZE_PIXELS.get(normalized)
    if pixels is None:
        raise ValueError(
            f"Unsupported image size '{image_size}' for Tencent backend. "
            f"Supported logical sizes: {list(IMAGE_SIZE_PIXELS)}."
        )
    ratio = bounded_ratio(aspect_ratio)
    if model == "seedream-image-v5.0-lite":
        pixels = max(pixels, 2048)

    step = 16 if model == DEFAULT_MODEL else 1
    width = math.floor(pixels * math.sqrt(ratio) / step) * step
    height = math.floor(pixels / math.sqrt(ratio) / step) * step
    limits = MODEL_SIZE_LIMITS[model]
    if not _within_limits(width, height, limits):
        # Tiers or ratios beyond the model's limits move to the nearest legal size.
        width, height = fit_size(ratio, pixels=pixels * pixels, step=step, **limits)
    return f"{width}x{height}"


def _read_bool(name: str, default: bool) -> bool:
    """Read a boolean provider option without silently accepting typos."""
    value = os.environ.get(name, str(default)).strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"Invalid argument: set {name} to true or false.")


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> str:
    """Generate one image with the Tencent backend."""
    model = _validate_model(model)
    size = _resolve_size(aspect_ratio, image_size, model)
    note_aspect_ratio(aspect_ratio, size.replace("x", ":"))
    url = _resolve_url(base_url, model)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
    }
    output_format = "png"
    if model == DEFAULT_MODEL:
        payload["revise"] = _read_bool("TENCENT_REVISE", True)
    else:
        output_format = (os.environ.get("TENCENT_OUTPUT_FORMAT") or "png").strip().lower()
        if output_format not in {"png", "jpeg"}:
            raise ValueError("Invalid argument: set TENCENT_OUTPUT_FORMAT to png or jpeg.")
        payload.update({
            "watermark": _read_bool("TENCENT_WATERMARK", False),
            "response_format": "url",
            "output_format": output_format,
        })

    print("[Tencent Cloud TokenHub]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    if model == "seedream-image-v5.0-lite" and normalize_image_size(image_size) in {"512px", "1K"}:
        print(f"  [INFO] Seedream lite requires at least 2K; upgrading {image_size} to 2K.")
    print(f"  Resolution:   {size}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "Tencent image generation")

    data = response.json()
    items = data.get("data") or []
    item = items[0] if items and isinstance(items[0], dict) else {}
    image_url = item.get("url")
    image_b64 = item.get("b64_json") if model != DEFAULT_MODEL else None
    if not image_url and not image_b64:
        raise RuntimeError(f"Tencent response missing image URL or base64 data: {data}")

    path = resolve_output_path(prompt, output_dir, filename, f".{output_format}")
    if image_url:
        return download_image(image_url, path)
    return save_image_bytes(base64.b64decode(image_b64), path, content_type=f"image/{output_format}")


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the Tencent backend."""
    resolved_model = _validate_model(model or os.environ.get("TENCENT_MODEL") or DEFAULT_MODEL)
    normalized_size = normalize_image_size(image_size)
    _resolve_size(aspect_ratio, normalized_size, resolved_model)
    prompt_limit = 8192 if resolved_model == DEFAULT_MODEL else 600
    if not prompt or len(prompt) > prompt_limit:
        raise ValueError(f"Invalid request: {resolved_model} requires a prompt of 1-{prompt_limit} characters.")
    api_key = require_api_key(
        "TENCENT_API_KEY",
        "TOKENHUB_API_KEY",
        message=(
            "No API key found. Set TENCENT_API_KEY or TOKENHUB_API_KEY "
            "in the current environment or a .env file."
        ),
    )
    base_url = os.environ.get("TENCENT_BASE_URL") or DEFAULT_BASE_URL

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
            delay = retry_delay(attempt, rate_limited=limited, exc=last_error)
            label = "Rate limit hit" if limited else f"Error: {exc}"
            print(f"\n  [WARN] {label}. Retrying in {delay}s...")
            time.sleep(delay)

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}") from last_error
