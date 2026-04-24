#!/usr/bin/env python3
"""
OpenAI Compatible Image Generation Backend

Generates images via OpenAI-compatible APIs (OpenAI, local models like Qwen-Image, etc.).
Used by image_gen.py as a backend module.

Configuration keys:
  OPENAI_API_KEY   (required) API key
  OPENAI_BASE_URL  (optional) Custom API endpoint (e.g. http://127.0.0.1:3000/v1)
  OPENAI_MODEL     (optional) Model name (default: gpt-image-2)

Dependencies:
  pip install openai Pillow
"""

import base64
import os
import time
import threading
from collections.abc import Mapping

from openai import OpenAI
from image_backends.backend_common import (
    MAX_RETRIES,
    download_image,
    is_rate_limit_error,
    normalize_image_size,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Constants                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# Aspect ratio -> DALL-E 3 / legacy compatible size mapping.
# Unknown OpenAI-compatible models use this table to preserve old behavior.
LEGACY_COMPAT_ASPECT_RATIO_TO_SIZE = {
    "1:1":  "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "3:2":  "1536x1024",
    "2:3":  "1024x1536",
    "4:3":  "1536x1024",   # closest available
    "3:4":  "1024x1536",   # closest available
    "4:5":  "1024x1024",   # fallback to square
    "5:4":  "1024x1024",   # fallback to square
    "21:9": "1792x1024",   # closest wide format
}

# GPT Image 1/1.5/mini officially support only square, landscape, portrait, or auto.
GPT_IMAGE_LEGACY_ASPECT_RATIO_TO_SIZE = {
    "1:1":  "1024x1024",
    "16:9": "1536x1024",
    "9:16": "1024x1536",
    "3:2":  "1536x1024",
    "2:3":  "1024x1536",
    "4:3":  "1536x1024",
    "3:4":  "1024x1536",
    "4:5":  "1024x1536",
    "5:4":  "1536x1024",
    "21:9": "1536x1024",
}

# GPT Image 2 supports flexible sizes when both edges are multiples of 16,
# the edge ratio is <= 3:1, and the total pixels are within model limits.
GPT_IMAGE_2_SIZES = {
    "512px": {
        "1:1": "1024x1024", "16:9": "1152x648", "9:16": "648x1152",
        "3:2": "1248x832", "2:3": "832x1248", "4:3": "1024x768",
        "3:4": "768x1024", "4:5": "896x1120", "5:4": "1120x896",
        "21:9": "1280x544",
    },
    "1K": {
        "1:1": "1024x1024", "16:9": "1152x648", "9:16": "648x1152",
        "3:2": "1248x832", "2:3": "832x1248", "4:3": "1024x768",
        "3:4": "768x1024", "4:5": "896x1120", "5:4": "1120x896",
        "21:9": "1280x544",
    },
    "2K": {
        "1:1": "2048x2048", "16:9": "2048x1152", "9:16": "1152x2048",
        "3:2": "2016x1344", "2:3": "1344x2016", "4:3": "1920x1440",
        "3:4": "1440x1920", "4:5": "1600x2000", "5:4": "2000x1600",
        "21:9": "2560x1088",
    },
    "4K": {
        "1:1": "2880x2880", "16:9": "3840x2160", "9:16": "2160x3840",
        "3:2": "3520x2352", "2:3": "2352x3520", "4:3": "3264x2448",
        "3:4": "2448x3264", "4:5": "2560x3200", "5:4": "3200x2560",
        "21:9": "3840x1648",
    },
}

DALL_E_2_SIZE_BY_IMAGE_SIZE = {
    "512px": "512x512",
    "1K": "1024x1024",
    "2K": "1024x1024",
    "4K": "1024x1024",
}

VALID_ASPECT_RATIOS = list(LEGACY_COMPAT_ASPECT_RATIO_TO_SIZE.keys())

# image_size -> quality mapping
IMAGE_SIZE_TO_QUALITY = {
    "512px": "low",
    "1K":    "auto",
    "2K":    "high",
    "4K":    "high",
}

DEFAULT_MODEL = "gpt-image-2"


def _field(value, name: str):
    """Read a response field from either an SDK object or a dict."""
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _normalized_model(model: str) -> str:
    return (model or "").strip().lower()


def _is_gpt_image_model(model: str) -> bool:
    return _normalized_model(model).startswith("gpt-image-")


def _is_gpt_image_2(model: str) -> bool:
    return _normalized_model(model).startswith("gpt-image-2")


def _is_dall_e_2(model: str) -> bool:
    return _normalized_model(model) == "dall-e-2"


def _select_size(model: str, aspect_ratio: str, image_size: str) -> str:
    """Select a model-compatible size while preserving legacy fallbacks."""
    if _is_gpt_image_2(model):
        return GPT_IMAGE_2_SIZES[image_size][aspect_ratio]
    if _is_gpt_image_model(model):
        return GPT_IMAGE_LEGACY_ASPECT_RATIO_TO_SIZE[aspect_ratio]
    if _is_dall_e_2(model):
        return DALL_E_2_SIZE_BY_IMAGE_SIZE[image_size]
    return LEGACY_COMPAT_ASPECT_RATIO_TO_SIZE[aspect_ratio]


def _supports_response_format(model: str) -> bool:
    """GPT Image models always return base64; DALL-E/compatible models may need this."""
    return not _is_gpt_image_model(model)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Image Generation                                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def _generate_image(api_key: str, prompt: str, negative_prompt: str = None,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = None) -> str:
    """
    Image generation via OpenAI-compatible API.

    Maps aspect_ratio to OpenAI's size parameter, and image_size to quality.

    Returns:
        Path of the saved image file

    Raises:
        RuntimeError: When generation fails
    """
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Build prompt (OpenAI has no native negative_prompt, append to prompt)
    final_prompt = prompt
    if negative_prompt:
        final_prompt += f"\n\nAvoid the following: {negative_prompt}"

    # Map parameters
    size = _select_size(model, aspect_ratio, image_size)
    quality = IMAGE_SIZE_TO_QUALITY.get(image_size, "auto")

    mode_label = f"Proxy: {base_url}" if base_url else "OpenAI API"
    print(f"[OpenAI - {mode_label}]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {final_prompt[:120]}{'...' if len(final_prompt) > 120 else ''}")
    print(f"  Size:         {size} (from aspect_ratio={aspect_ratio})")
    print(f"  Quality:      {quality} (from image_size={image_size})")
    print()

    start_time = time.time()
    print(f"  [..] Generating...", end="", flush=True)

    # Heartbeat thread
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
        request = {
            "prompt": final_prompt,
            "model": model,
            "size": size,
            "quality": quality,
            "n": 1,
        }
        if _supports_response_format(model):
            request["response_format"] = "b64_json"

        resp = client.images.generate(**request)
    finally:
        heartbeat_stop.set()
        hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  [DONE] Image generated ({elapsed:.1f}s)")

    data = _field(resp, "data") if resp is not None else None
    if data:
        path = resolve_output_path(prompt, output_dir, filename, ".png")
        first_image = data[0]
        b64_json = _field(first_image, "b64_json")
        image_url = _field(first_image, "url")
        if b64_json:
            image_data = base64.b64decode(b64_json)
            return save_image_bytes(image_data, path)
        if image_url:
            return download_image(image_url, path)

    raise RuntimeError("No image was generated. The server may have refused the request.")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Public Entry Point                                             ║
# ╚══════════════════════════════════════════════════════════════════╝

def generate(prompt: str, negative_prompt: str = None,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """
    OpenAI-compatible image generation with automatic retry.

    Reads credentials from the current process environment or the project-root `.env`:
      OPENAI_API_KEY
      OPENAI_BASE_URL
      OPENAI_MODEL (optional override)

    Args:
        prompt: Positive prompt text
        negative_prompt: Negative prompt text (appended to prompt as "Avoid...")
        aspect_ratio: Aspect ratio, mapped to OpenAI size
        image_size: Image size, mapped to OpenAI quality
        output_dir: Output directory
        filename: Output filename (without extension)
        model: Model name (default: gpt-image-2)
        max_retries: Maximum number of retries

    Returns:
        Path of the saved image file
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")

    if not api_key:
        raise ValueError(
            "No API key found. Set OPENAI_API_KEY in the current environment or the project-root .env."
        )

    if model is None:
        model = os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL

    image_size = normalize_image_size(image_size)

    if aspect_ratio not in LEGACY_COMPAT_ASPECT_RATIO_TO_SIZE:
        supported = list(LEGACY_COMPAT_ASPECT_RATIO_TO_SIZE.keys())
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for OpenAI backend. "
            f"Supported: {supported}"
        )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(api_key, prompt, negative_prompt,
                                   aspect_ratio, image_size, output_dir,
                                   filename, model, base_url)
        except Exception as e:
            last_error = e
            if attempt < max_retries and is_rate_limit_error(e):
                delay = retry_delay(attempt, rate_limited=True)
                print(f"\n  [WARN] Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                      f"Waiting {delay}s before retry...")
                time.sleep(delay)
            elif attempt < max_retries:
                delay = retry_delay(attempt, rate_limited=False)
                print(f"\n  [WARN] Error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                      f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                break

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")
