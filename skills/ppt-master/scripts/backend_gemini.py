#!/usr/bin/env python3
"""
Gemini Image Generation Backend

Generates images via the Google GenAI API (Gemini).
Used by image_gen.py as a backend module.

Environment variables (checked in order):
  IMAGE_API_KEY   / GEMINI_API_KEY   (required)
  IMAGE_BASE_URL  / GEMINI_BASE_URL  (optional) Custom API endpoint for proxy services
  IMAGE_MODEL                        (optional) Override default model

Dependencies:
  pip install google-genai Pillow
"""

import os
import sys
import time
import threading
from google import genai
from google.genai import types

# Optional dependency: PIL (used to report image resolution)
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ╔══════════════════════════════���═══════════════════════════════════╗
# ║  Constants                                                      ║
# ╚═══════════��═════════════════════════════��════════════════════════╝

VALID_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8",
    "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
]

VALID_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]

DEFAULT_MODEL = "gemini-3.1-flash-image-preview"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 10
RETRY_BACKOFF = 2


# ╔═════════════════��════════════════════════════════════════════════╗
# ║  Utilities                                                      ║
# ╚═══════════════���══════════════════════���═══════════════════════════╝

def save_binary_file(file_name: str, data: bytes):
    """Save binary data to a file"""
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


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


def _normalize_image_size(image_size: str) -> str:
    """
    Case-insensitive normalization: normalize user input to API-accepted format.
    e.g.: "2k" -> "2K", "4k" -> "4K", "512PX" -> "512px"
    """
    s = image_size.strip()
    upper = s.upper()
    if upper in ("1K", "2K", "4K"):
        return upper
    if upper in ("512PX", "512"):
        return "512px"
    return s


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
    return "429" in err_str or "rate" in err_str or "quota" in err_str or "resource_exhausted" in err_str


# ╔══════���═══════════════════════════════════════════════��═══════════╗
# ║  Image Generation                                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def _generate_image(api_key: str, prompt: str, negative_prompt: str = None,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = None) -> str:
    """
    Image generation via Gemini API (streaming).

    Returns:
        Path of the saved image file

    Raises:
        RuntimeError: When generation fails
    """
    if base_url:
        client = genai.Client(api_key=api_key, http_options={'base_url': base_url})
    else:
        client = genai.Client(api_key=api_key)

    final_prompt = prompt
    if negative_prompt:
        final_prompt += f"\n\nNegative prompt: {negative_prompt}"

    config_kwargs = {
        "response_modalities": ["IMAGE"],
        "image_config": types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    }
    if "flash" in model.lower():
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_level="MINIMAL",
        )
    config = types.GenerateContentConfig(**config_kwargs)

    mode_label = "Proxy Mode" if base_url else "Official Mode"
    print(f"[Gemini - {mode_label}]")
    if base_url:
        print(f"  Base URL:     {base_url}")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {final_prompt[:120]}{'...' if len(final_prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Image Size:   {image_size}")
    print()

    start_time = time.time()
    print(f"  ⏳ Generating...", end="", flush=True)

    heartbeat_stop = threading.Event()

    def _heartbeat():
        while not heartbeat_stop.is_set():
            heartbeat_stop.wait(5)
            if not heartbeat_stop.is_set():
                elapsed = time.time() - start_time
                print(f" {elapsed:.0f}s...", end="", flush=True)

    hb_thread = threading.Thread(target=_heartbeat, daemon=True)
    hb_thread.start()

    last_image_data = None
    chunk_count = 0
    total_bytes = 0

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=[final_prompt],
        config=config,
    ):
        elapsed = time.time() - start_time

        if chunk.parts is None:
            continue

        for part in chunk.parts:
            if part.text is not None:
                print(f"\n  Model says: {part.text}", end="", flush=True)
            elif part.inline_data is not None:
                chunk_count += 1
                data_size = len(part.inline_data.data) if part.inline_data.data else 0
                total_bytes += data_size
                size_str = f"{data_size / 1024:.0f}KB" if data_size < 1048576 else f"{data_size / 1048576:.1f}MB"
                print(f"\n  📦 Chunk #{chunk_count} received ({size_str}, {elapsed:.1f}s)", end="", flush=True)
                last_image_data = part

    heartbeat_stop.set()
    hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  ✅ Stream complete ({elapsed:.1f}s, {chunk_count} chunk(s), {total_bytes / 1024:.0f}KB total)")

    if last_image_data is not None and last_image_data.inline_data is not None:
        if chunk_count > 1:
            print(f"  Keeping the final chunk (highest quality).")
        image = last_image_data.as_image()
        path = _resolve_output_path(prompt, output_dir, filename, ".png")
        image.save(path)
        print(f"File saved to: {path}")
        _report_resolution(path)
        return path

    raise RuntimeError("No image was generated. The server may have refused the request.")


# ╔���═══════════════════════════════════���═════════════════════════════╗
# ║  Public Entry Point                                             ║
# ╚═════════════���═══════════════════════════���════════════════════════╝

def generate(prompt: str, negative_prompt: str = None,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """
    Gemini image generation with automatic retry.

    Reads credentials from environment variables:
      IMAGE_API_KEY / GEMINI_API_KEY (fallback)
      IMAGE_BASE_URL / GEMINI_BASE_URL (fallback)
      IMAGE_MODEL (optional override)

    Args:
        prompt: Positive prompt text
        negative_prompt: Negative prompt text
        aspect_ratio: Aspect ratio (e.g. "16:9", "1:1")
        image_size: Image size ("512px", "1K", "2K", "4K", case-insensitive)
        output_dir: Output directory
        filename: Output filename (without extension)
        model: Model name (default: gemini-3.1-flash-image-preview)
        max_retries: Maximum number of retries

    Returns:
        Path of the saved image file
    """
    api_key = os.environ.get("IMAGE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    base_url = os.environ.get("IMAGE_BASE_URL") or os.environ.get("GEMINI_BASE_URL")

    if not api_key:
        raise ValueError(
            "No API key found. Set IMAGE_API_KEY or GEMINI_API_KEY environment variable."
        )

    if model is None:
        model = os.environ.get("IMAGE_MODEL") or DEFAULT_MODEL

    image_size = _normalize_image_size(image_size)

    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect ratio '{aspect_ratio}'. Valid: {VALID_ASPECT_RATIOS}")

    if image_size not in VALID_IMAGE_SIZES:
        raise ValueError(f"Invalid image size '{image_size}'. Valid: {VALID_IMAGE_SIZES}")

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
