#!/usr/bin/env python3
"""
Volcengine Seedream image generation backend.

Configuration keys:
  ARK_API_KEY / VOLCENGINE_API_KEY / LAS_API_KEY   (required; the key must match the endpoint)
  VOLCENGINE_BASE_URL                (optional; Ark by default, LAS when only LAS_API_KEY is set)
  VOLCENGINE_MODEL                   (optional; Seedream 5.0 pro / flash, or 4.5)
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

import math
import os
import time
from urllib.parse import urlparse

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    download_image,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    TIER_PIXELS,
    fit_size,
    match_aspect_ratio,
    normalize_image_size,
    note_aspect_ratio,
    require_api_key,
    resolve_output_path,
    retry_delay,
)


ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
LAS_ENDPOINT = "https://operator.las.cn-beijing.volces.com/api/v1/images/generations"
DEFAULT_ENDPOINT = ARK_ENDPOINT
DEFAULT_MODEL = "doubao-seedream-5-0-pro-260628"
# LAS does not list Seedream 5.0 pro / flash; its users keep the 4.5 default.
LAS_DEFAULT_MODEL = "doubao-seedream-4-5-251128"
DEFAULT_IMAGE_SIZE = "2K"
# Official total-pixel limits; a listed size outside them is refitted, never rejected.
SEEDREAM_5_PRO_LIMITS = {"min_pixels": 921_600, "max_pixels": 4_624_220, "max_ratio": 16}
MODEL_SIZE_LIMITS = {
    DEFAULT_MODEL: SEEDREAM_5_PRO_LIMITS,
    "doubao-seedream-5-0-flash-260915": SEEDREAM_5_PRO_LIMITS,
    LAS_DEFAULT_MODEL: {"min_pixels": 3_686_400, "max_pixels": 16_777_216, "max_ratio": 16},
}
SUPPORTED_MODELS = set(MODEL_SIZE_LIMITS)

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
    """Limit the backend to the Seedream contracts implemented below."""
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
    if base.endswith(("/api/v1", "/api/v3")):
        return base + "/images/generations"
    return base + "/api/v1/images/generations"


def _is_las(url: str) -> bool:
    """Return whether a base URL or endpoint points at the LAS gateway."""
    return ".las." in (urlparse(url).hostname or "")


def _resolve_base_url() -> str:
    """Pick the endpoint: explicit URL, LAS for a LAS-only key, otherwise Ark."""
    explicit = os.environ.get("VOLCENGINE_BASE_URL")
    if explicit:
        return explicit
    las_only = os.environ.get("LAS_API_KEY") and not (
        os.environ.get("ARK_API_KEY") or os.environ.get("VOLCENGINE_API_KEY")
    )
    return LAS_ENDPOINT if las_only else ARK_ENDPOINT


def _size_pixels(size: str) -> int:
    """Return the total pixels of a `WxH` size string."""
    return math.prod(map(int, size.split("x")))


def _tier_pixels(image_size: str) -> int:
    """Return the 1:1 pixel budget of a logical size preset."""
    normalized = normalize_image_size(image_size)
    sizes = ASPECT_RATIO_SIZE_MAP.get(normalized)
    if sizes:
        return _size_pixels(sizes["1:1"])
    if normalized not in TIER_PIXELS:
        raise ValueError(
            f"Unsupported image size '{image_size}' for Volcengine backend. "
            f"Supported logical sizes: {', '.join(TIER_PIXELS)}."
        )
    return TIER_PIXELS[normalized]


def _resolve_size(aspect_ratio: str, image_size: str, model: str = DEFAULT_MODEL) -> str:
    """Resolve the target resolution for a ratio, logical size preset, and model."""
    budget = _tier_pixels(image_size)
    limits = MODEL_SIZE_LIMITS[model]
    tables = [ASPECT_RATIO_SIZE_MAP.get(normalize_image_size(image_size)) or {}]
    if budget > limits["max_pixels"]:
        # A tier above the model's ceiling reuses the largest listed tier that fits.
        tables += sorted(ASPECT_RATIO_SIZE_MAP.values(), key=lambda t: -_size_pixels(t["1:1"]))
    for sizes in tables:
        listed = match_aspect_ratio(aspect_ratio, sizes)
        if listed and limits["min_pixels"] <= _size_pixels(sizes[listed]) <= limits["max_pixels"]:
            return sizes[listed]
    # Any other ratio, tier, or out-of-limit listed size is fitted to the model's rules.
    width, height = fit_size(aspect_ratio, pixels=budget, step=32, **limits)
    return f"{width}x{height}"


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = DEFAULT_IMAGE_SIZE,
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_ENDPOINT) -> str:
    """Generate one image with the Volcengine backend."""
    model = _validate_model(model)
    size = _resolve_size(aspect_ratio, image_size, model)
    note_aspect_ratio(aspect_ratio, size.replace("x", ":"))
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
    limits = MODEL_SIZE_LIMITS[model]
    budget = _tier_pixels(image_size)
    if not limits["min_pixels"] <= budget <= limits["max_pixels"]:
        print(f"  [INFO] {model} does not support {image_size}; using the nearest legal size.")
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
    base_url = _resolve_base_url()
    las = _is_las(base_url)
    resolved_model = (
        model or os.environ.get("VOLCENGINE_MODEL") or (LAS_DEFAULT_MODEL if las else DEFAULT_MODEL)
    )
    resolved_model = _validate_model(resolved_model)
    normalized_size = normalize_image_size(image_size)
    _resolve_size(aspect_ratio, normalized_size, resolved_model)
    # Ark and LAS keys are not interchangeable; prefer the key for the chosen endpoint.
    key_order = (
        ("LAS_API_KEY", "VOLCENGINE_API_KEY", "ARK_API_KEY") if las
        else ("ARK_API_KEY", "VOLCENGINE_API_KEY", "LAS_API_KEY")
    )
    api_key = require_api_key(
        *key_order,
        message=(
            "No API key found. Set ARK_API_KEY (Ark) or LAS_API_KEY (LAS) "
            "in the current environment or a .env file."
        ),
    )

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
