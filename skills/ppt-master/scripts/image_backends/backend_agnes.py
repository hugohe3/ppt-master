#!/usr/bin/env python3
"""
Agnes AI image generation backend.

OpenAI-compatible API (agnes-image-2.1-flash etc.), but without
response_format=b64_json — Agnes returns URLs only.

Configuration keys:
  AGNES_API_KEY    (required)
  AGNES_BASE_URL   (optional, default: https://apihub.agnes-ai.com/v1)
  AGNES_MODEL      (optional, default: agnes-image-2.1-flash)
"""

import sys

if __name__ == "__main__" and any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]):
    print(__doc__)
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend agnes")
    raise SystemExit(0)

import os
import time
import threading

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


DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-image-2.1-flash"

# Agnes supports standard resolutions; map aspect_ratio + image_size to WxH.
# Based on typical t2i model size tables.
ASPECT_RATIO_SIZE_MAP = {
    "512px": {
        "1:1": "1024x1024",
        "16:9": "1280x720",
        "9:16": "720x1280",
        "3:2": "1152x768",
        "2:3": "768x1152",
        "4:3": "1024x768",
        "3:4": "768x1024",
        "4:5": "896x1120",
        "5:4": "1120x896",
        "21:9": "1344x576",
    },
    "1K": {
        "1:1": "1024x1024",
        "16:9": "1280x720",
        "9:16": "720x1280",
        "3:2": "1152x768",
        "2:3": "768x1152",
        "4:3": "1024x768",
        "3:4": "768x1024",
        "4:5": "896x1120",
        "5:4": "1120x896",
        "21:9": "1344x576",
    },
    "2K": {
        "1:1": "2048x2048",
        "16:9": "2048x1152",
        "9:16": "1152x2048",
        "3:2": "2016x1344",
        "2:3": "1344x2016",
        "4:3": "1920x1440",
        "3:4": "1440x1920",
        "4:5": "1600x2000",
        "5:4": "2000x1600",
        "21:9": "2560x1088",
    },
    "4K": {
        "1:1": "2880x2880",
        "16:9": "3840x2160",
        "9:16": "2160x3840",
        "3:2": "3520x2352",
        "2:3": "2352x3520",
        "4:3": "3264x2448",
        "3:4": "2448x3264",
        "4:5": "2560x3200",
        "5:4": "3200x2560",
        "21:9": "3840x1648",
    },
}


def _resolve_size(aspect_ratio: str, image_size: str) -> str:
    """Resolve target resolution from aspect_ratio and image_size."""
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
    """Generate one image via the Agnes OpenAI-compatible endpoint."""
    size = _resolve_size(aspect_ratio, image_size)
    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1,
    }

    print("[Agnes AI Image]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Size:         {size} (from aspect_ratio={aspect_ratio}, image_size={image_size})")
    print()

    # Heartbeat for long generations
    start_time = time.time()
    print(f"  [..] Generating...", end="", flush=True)
    heartbeat_stop = threading.Event()

    def _heartbeat():
        while not heartbeat_stop.is_set():
            heartbeat_stop.wait(5)
            if not heartbeat_stop.is_set():
                elapsed = time.time() - start_time
                print(f" {elapsed:.0f}s...", end="", flush=True)

    hb_thread = threading.Thread(target=_heartbeat, daemon=True)
    hb_thread.start()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300)
    finally:
        heartbeat_stop.set()
        hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if not response.ok:
        raise http_error(response, "Agnes image generation")

    resp_data = response.json()
    data = resp_data.get("data")
    if data:
        first = data[0]
        image_url = first.get("url")
        if image_url:
            path = resolve_output_path(prompt, output_dir, filename, ".png")
            return download_image(image_url, path)

    raise RuntimeError(f"No image URL in Agnes response. Response: {resp_data}")


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