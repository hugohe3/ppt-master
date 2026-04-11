#!/usr/bin/env python3
"""
MiniMax Image Generation Backend

API: https://api.minimaxi.com/v1/image_generation
Model: image-01

Required environment variables:
  MINIMAX_API_KEY   (required)
  MINIMAX_BASE_URL  (optional, default: https://api.minimaxi.com/v1)
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
DEFAULT_MODEL = "image-01"


def require_api_key(*candidates: str, message: str) -> str:
    for key in candidates:
        value = os.environ.get(key)
        if value:
            return value
    sys.exit(f"[ERROR] {message}")


def _generate_image(api_key: str, prompt: str, base_url: str = DEFAULT_BASE_URL,
                    model: str = DEFAULT_MODEL, n: int = 1) -> list[dict]:
    """Generate image(s) via MiniMax API."""
    url = f"{base_url}/image_generation"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "response_format": "url",
        "n": n,
        "prompt_optimizer": True
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    images = []
    # MiniMax returns: {"data": {"image_urls": [...]}}
    image_urls = []
    if isinstance(data.get("data"), dict):
        image_urls = data["data"].get("image_urls", [])
    elif isinstance(data.get("data"), list):
        image_urls = data.get("data", [])
    elif isinstance(data.get("data"), str):
        image_urls = [data["data"]]

    for url_item in image_urls:
        if isinstance(url_item, str):
            images.append({"url": url_item, "revised_prompt": ""})
        elif isinstance(url_item, dict):
            images.append({
                "url": url_item.get("url", ""),
                "revised_prompt": url_item.get("revised_prompt", "")
            })

    return images


def generate(prompt: str, output_dir: str = ".", aspect_ratio: str = "16:9",
            image_size: str = "1K", n: int = 1, negative_prompt: str = None,
            filename: str = None, model: str = None) -> list[Path]:
    """Main entry point for image generation."""
    api_key = require_api_key(
        "MINIMAX_API_KEY",
        message="No API key found. Set MINIMAX_API_KEY in .env or environment."
    )

    base_url = os.environ.get("MINIMAX_BASE_URL", DEFAULT_BASE_URL)
    actual_model = model or DEFAULT_MODEL

    print(f"[MiniMax] Generating {n} image(s) with aspect_ratio={aspect_ratio}")
    print(f"[MiniMax] Prompt: {prompt[:100]}...")

    images = _generate_image(api_key, prompt, base_url, model=actual_model, n=n)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, img in enumerate(images):
        if img.get("url"):
            # Download image
            img_response = requests.get(img["url"], timeout=60)
            img_response.raise_for_status()

            fname = filename or f"minimax_{timestamp}_{i+1}.png"
            filepath = output_path / fname

            with open(filepath, "wb") as f:
                f.write(img_response.content)

            print(f"[OK] Saved: {filepath}")
            saved_files.append(filepath)

    return saved_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MiniMax Image Generation")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("--aspect_ratio", default="16:9",
                        choices=["1:1", "16:9", "9:16", "3:2", "2:3"],
                        help="Aspect ratio")
    parser.add_argument("--size", default="1K", help="Image size (1K, 2K)")
    parser.add_argument("-n", "--count", type=int, default=1, help="Number of images")

    args = parser.parse_args()
    saved = generate(args.prompt, args.output, args.aspect_ratio, args.size, args.count)

    if not saved:
        print("[ERROR] No images generated")
        sys.exit(1)
