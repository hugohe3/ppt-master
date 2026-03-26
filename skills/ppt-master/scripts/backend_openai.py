#!/usr/bin/env python3
"""
OpenAI Compatible Image Generation Backend

Generates images via OpenAI-compatible APIs (OpenAI, local models like Qwen-Image, etc.).
Used by image_gen.py as a backend module.

Environment variables:
  IMAGE_API_KEY    (required) API key
  IMAGE_BASE_URL   (optional) Custom API endpoint (e.g. http://127.0.0.1:3000/v1)
  IMAGE_MODEL      (optional) Model name (default: gpt-image-1)

Dependencies:
  pip install openai Pillow
"""

import base64
import io
import os
import sys
import time
import threading

from openai import OpenAI

# Optional dependency: PIL (used to report image resolution)
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Constants                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# Aspect ratio -> OpenAI size mapping
# Covers common PPT/social media ratios
ASPECT_RATIO_TO_SIZE = {
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

VALID_ASPECT_RATIOS = list(ASPECT_RATIO_TO_SIZE.keys())

# image_size -> quality mapping
IMAGE_SIZE_TO_QUALITY = {
    "512px": "low",
    "1K":    "auto",
    "2K":    "high",
    "4K":    "high",
}

DEFAULT_MODEL = "gpt-image-1"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 10
RETRY_BACKOFF = 2


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Utilities                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

def _resolve_output_path(prompt: str, output_dir: str = None,
                         filename: str = None, ext: str = ".png") -> str:
    """Compute the final output file path based on parameters"""
    if filename:
        file_name = os.path.splitext(filename)[0]
    else:
        safe = "".join(c for c in prompt if c.isalnum() or c in (' ', '_')).rstrip()
        safe = safe.replace(" ", "_").lower()[:30]
        file_name = safe or "generated_image"

    full_name = f"{file_name}{ext}"
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, full_name)
    return full_name


def _report_resolution(path: str):
    """Try to report image resolution using PIL"""
    if HAS_PIL:
        try:
            img = PILImage.open(path)
            print(f"  Resolution:   {img.size[0]}x{img.size[1]}")
        except Exception:
            pass


def _is_rate_limit_error(e: Exception) -> bool:
    """Check whether the exception is a rate limit (429) error"""
    err_str = str(e).lower()
    return "429" in err_str or "rate" in err_str or "quota" in err_str


def _normalize_image_size(image_size: str) -> str:
    """Normalize image size input to standard format."""
    s = image_size.strip()
    upper = s.upper()
    if upper in ("1K", "2K", "4K"):
        return upper
    if upper in ("512PX", "512"):
        return "512px"
    return s


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
    size = ASPECT_RATIO_TO_SIZE.get(aspect_ratio, "1024x1024")
    quality = IMAGE_SIZE_TO_QUALITY.get(image_size, "auto")

    mode_label = f"Proxy: {base_url}" if base_url else "OpenAI API"
    print(f"[OpenAI - {mode_label}]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {final_prompt[:120]}{'...' if len(final_prompt) > 120 else ''}")
    print(f"  Size:         {size} (from aspect_ratio={aspect_ratio})")
    print(f"  Quality:      {quality} (from image_size={image_size})")
    print()

    start_time = time.time()
    print(f"  ⏳ Generating...", end="", flush=True)

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
        resp = client.images.generate(
            prompt=final_prompt,
            model=model,
            size=size,
            quality=quality,
            n=1,
            response_format="b64_json",
        )
    finally:
        heartbeat_stop.set()
        hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  ✅ Image generated ({elapsed:.1f}s)")

    if resp is not None and resp.data:
        path = _resolve_output_path(prompt, output_dir, filename, ".png")
        image_data = base64.b64decode(resp.data[0].b64_json)

        if HAS_PIL:
            image = PILImage.open(io.BytesIO(image_data))
            image.save(path)
        else:
            with open(path, "wb") as f:
                f.write(image_data)

        print(f"  File saved to: {path}")
        _report_resolution(path)
        return path

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

    Reads credentials from environment variables:
      IMAGE_API_KEY  / OPENAI_API_KEY   (fallback)
      IMAGE_BASE_URL / OPENAI_BASE_URL  (fallback)
      IMAGE_MODEL    (optional override)

    Args:
        prompt: Positive prompt text
        negative_prompt: Negative prompt text (appended to prompt as "Avoid...")
        aspect_ratio: Aspect ratio, mapped to OpenAI size
        image_size: Image size, mapped to OpenAI quality
        output_dir: Output directory
        filename: Output filename (without extension)
        model: Model name (default: gpt-image-1)
        max_retries: Maximum number of retries

    Returns:
        Path of the saved image file
    """
    api_key = os.environ.get("IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")

    if not api_key:
        raise ValueError(
            "No API key found. Set IMAGE_API_KEY or OPENAI_API_KEY environment variable."
        )

    if model is None:
        model = os.environ.get("IMAGE_MODEL") or DEFAULT_MODEL

    image_size = _normalize_image_size(image_size)

    if aspect_ratio not in ASPECT_RATIO_TO_SIZE:
        supported = list(ASPECT_RATIO_TO_SIZE.keys())
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
            if attempt < max_retries and _is_rate_limit_error(e):
                delay = RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
                print(f"\n  ⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                      f"Waiting {delay}s before retry...")
                time.sleep(delay)
            elif attempt < max_retries:
                delay = 5
                print(f"\n  ⚠️  Error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                      f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                break

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")
