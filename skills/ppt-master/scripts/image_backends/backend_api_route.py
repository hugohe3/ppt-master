#!/usr/bin/env python3
"""
API Route image generation backend.

Configuration keys:
  API_ROUTE_API_KEY   (required)
  API_ROUTE_BASE_URL  (optional, defaults to https://global.api-route.com/v1)
  API_ROUTE_MODEL     (optional)
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend api-route")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os
import time
import threading
import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    decode_data_uri,
    find_data_uri,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    normalize_image_size,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Constants                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

VALID_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8",
    "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
]

VALID_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]

DEFAULT_MODEL = "google/gemini-2.5-flash-image"
DEFAULT_ENDPOINT = "https://global.api-route.com/v1"

# ╔══════════════════════════════════════════════════════════════════╗
# ║  Image Generation                                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def _resolve_url(base_url: str) -> str:
    """Resolve the API Route chat completion generation endpoint."""
    return base_url.rstrip("/") + "/chat/completions"

def _message_image_uri(message: dict) -> str | None:
    """Locate the generated image in a chat completion message."""
    images = message.get("images")
    if images:
        url = images[0].get("image_url")
        if isinstance(url, dict):
            url = url.get("url")
        if url:
            return url

    return find_data_uri(message.get("content"))


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = DEFAULT_ENDPOINT) -> str:
    """Image generation via API Route."""
    url = _resolve_url(base_url)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": aspect_ratio,
            "image_size": "512" if image_size == "512px" else image_size
        }
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError(f"API Route response contained no choices: {data}")

                message = choices[0].get("message", {})
                image_uri = _message_image_uri(message)
                if not image_uri:
                    content_preview = str(message.get("content", ""))[:200]
                    raise ValueError(
                        f"API Route response contained no extractable image data. "
                        f"Message preview: {content_preview}"
                    )

                data_bytes, ext = decode_data_uri(image_uri)
                output_path = resolve_output_path(
                    output_dir=output_dir,
                    filename=filename,
                    prefix="api_route",
                    ext=ext
                )
                save_image_bytes(data_bytes, output_path)
                return output_path

            elif is_rate_limit_error(resp.status_code):
                delay = retry_delay(attempt, resp=resp)
                print(f"[API Route] Rate limit hit (attempt {attempt}/{MAX_RETRIES}), waiting {delay:.1f}s...")
                time.sleep(delay)
                continue

            elif is_permanent_error(resp.status_code):
                raise http_error("API Route", resp.status_code, resp.text)

            else:
                delay = retry_delay(attempt, resp=resp)
                print(f"[API Route] HTTP {resp.status_code} (attempt {attempt}/{MAX_RETRIES}), retrying in {delay:.1f}s...")
                time.sleep(delay)

        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"API Route request failed after {MAX_RETRIES} attempts: {e}")
            delay = retry_delay(attempt)
            print(f"[API Route] Network error (attempt {attempt}/{MAX_RETRIES}): {e}, retrying in {delay:.1f}s...")
            time.sleep(delay)

    raise RuntimeError(f"API Route generation failed after {MAX_RETRIES} attempts.")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Public API                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

def generate(prompt: str, aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None) -> str:
    """Generate an image using the API Route backend."""
    api_key = os.getenv("API_ROUTE_API_KEY")
    if not api_key:
        raise ValueError(
            "API_ROUTE_API_KEY is not set. "
            "Please set it via environment variable or in your .env file."
        )

    model = os.getenv("API_ROUTE_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("API_ROUTE_BASE_URL", DEFAULT_ENDPOINT)

    normalized_size = normalize_image_size(image_size, VALID_IMAGE_SIZES)
    ratio = aspect_ratio if aspect_ratio in VALID_ASPECT_RATIOS else "1:1"

    return _generate_image(
        api_key=api_key,
        prompt=prompt,
        aspect_ratio=ratio,
        image_size=normalized_size,
        output_dir=output_dir,
        filename=filename,
        model=model,
        base_url=base_url
    )
