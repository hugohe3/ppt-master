#!/usr/bin/env python3
"""
ModelScope image generation backend.

Configuration keys:
  MODELSCOPE_API_KEY    (required)
  MODELSCOPE_MODEL      (optional)
  MODELSCOPE_BASE_URL   (optional)
"""

import os
import time

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    save_image_bytes,
    http_error,
    is_rate_limit_error,
    normalize_image_size,
    require_api_key,
    resolve_output_path,
    retry_delay,
)

DEFAULT_ENDPOINT = "https://api-inference.modelscope.cn"
DEFAULT_MODEL = "Tongyi-MAI/Z-Image-Turbo"

# Resolution must be 64-aligned.
ASPECT_RATIO_SIZE_MAP = {
    "512px": {
        "1:1": "1024*1024",
        "3:4": "768*1024",
        "4:3": "1024*768",
        "9:16": "576*1024",
        "16:9": "1024*576"
    },
    "1K": {
        "1:1": "1280*1280",
        "3:4": "960*1280",
        "4:3": "1280*960",
        "9:16": "576*1024",
        "16:9": "1024*576"
    },
    "2K": {
        "1:1": "2048*2048",
        "3:4": "1536*2048",
        "4:3": "2048*1536",
        "9:16": "1152*2048",
        "16:9": "2048*1152"
    },
    "4K": {
        "1:1": "2048*2048",
        "3:4": "1920*2560",
        "4:3": "2560*1920",
        "9:16": "1728*3072",
        "16:9": "3072*1728"
    }
}

def _resolve_url(base_url: str) -> str:
    """Resolve the ModelScope generation endpoint."""
    base = base_url.rstrip("/").rstrip("/v1")
    if base.endswith(".cn"):
        return base
    raise ValueError(f"Unsupported ModelScope endpoint: {base_url}")

def _resolve_size(aspect_ratio: str, image_size: str) -> str:
    """Resolve the target resolution for a ratio and logical size preset.

    Args:
        aspect_ratio (str): The aspect ratio string. Supported values: '1:1', '3:4', '4:3', '9:16', '16:9'.
        image_size (str): The logical size preset. Supported values: '512px', '1K', '2K', '4K'.
    """
    normalized = normalize_image_size(image_size)
    size = (ASPECT_RATIO_SIZE_MAP.get(normalized) or {}).get(aspect_ratio)
    if not size:
        supported = sorted(ASPECT_RATIO_SIZE_MAP["1K"])
        raise ValueError(
            f"Unsupported aspect ratio '{aspect_ratio}' for ModelScope backend. "
            f"Supported: {supported}"
        )
    return size


def _generate_image(api_key: str, prompt: str, negative_prompt: str = None,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_ENDPOINT) -> str:
    """Generate one image with the ModelScope backend."""
    size = _resolve_size(aspect_ratio, image_size)
    url = _resolve_url(base_url)+'/v1/images/generations'
    common_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "negative_prompt":negative_prompt,
        "size": size.replace("*", "x"),

    }

    print(f"[ModelScope Models]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution:   {size}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers={**common_headers,"X-ModelScope-Async-Mode": "true"}, json=payload, timeout=300)
    

    # if response.status_code != 200:
    #     raise http_error(response, "ModelScope image generation")
    response.raise_for_status()

    
    task_id = response.json()["task_id"]
    while True:
      result = requests.get(
          f"{_resolve_url(base_url)}/v1/tasks/{task_id}",
          headers={**common_headers, "X-ModelScope-Task-Type": "image_generation"},
      )
      result.raise_for_status()
      data = result.json()

      if data["task_status"] == "SUCCEED":
          path = resolve_output_path(prompt, output_dir, filename, ".png")
          save_image_bytes(requests.get(data["output_images"][0]).content, path)
          elapsed = time.time() - start
          print(f"\n  [DONE] Response received ({elapsed:.1f}s)")
          break
      elif data["task_status"] == "FAILED":
          break
      time.sleep(3)
    


def generate(prompt: str, negative_prompt: str = None,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the ModelScope backend."""
    api_key = require_api_key(
        "MODELSCOPE_API_KEY",
        message="No API key found. Set MODELSCOPE_API_KEY in the current environment or the project-root .env.",
    )
    base_url = os.environ.get("MODELSCOPE_BASE_URL") or DEFAULT_ENDPOINT
    resolved_model = model or os.environ.get("MODELSCOPE_MODEL") or DEFAULT_MODEL

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(
                api_key=api_key,
                prompt=prompt,
                negative_prompt=negative_prompt,
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

