#!/usr/bin/env python3
"""
PPT Master backend that delegates generation to Hanako's local GPT Image 2 workbench.

Persistent source:
  D:/HanakoField/persistent-overrides/ppt-master-local-image/backend_local_workbench.py

Runtime copy installed into:
  <ppt-master>/skills/ppt-master/scripts/image_backends/backend_local_workbench.py

The actual image request is handled by:
  D:/HanakoField/image2本地使用/openai_compatible_image.py

That workbench owns API base URL, model, encrypted API key and timeout via its own .env.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

DEFAULT_WORKBENCH_SCRIPT = Path("D:/HanakoField/image2本地使用/openai_compatible_image.py")

GPT_IMAGE_2_SIZES = {
    "512px": {
        "1:1": "1024x1024", "16:9": "1824x1024", "9:16": "1024x1824",
        "3:2": "1536x1024", "2:3": "1024x1536", "4:3": "1368x1024",
        "3:4": "1152x1536", "4:5": "1024x1280", "5:4": "1280x1024",
        "21:9": "2688x1152",
    },
    "1K": {
        "1:1": "1024x1024", "16:9": "1824x1024", "9:16": "1024x1824",
        "3:2": "1536x1024", "2:3": "1024x1536", "4:3": "1368x1024",
        "3:4": "1152x1536", "4:5": "1024x1280", "5:4": "1280x1024",
        "21:9": "2688x1152",
    },
    "2K": {
        "1:1": "2560x2560", "16:9": "2560x1440", "9:16": "1440x2560",
        "3:2": "2560x1712", "2:3": "1712x2560", "4:3": "2560x1920",
        "3:4": "1920x2560", "4:5": "2048x2560", "5:4": "2560x2048",
        "21:9": "3360x1440",
    },
    "4K": {
        "1:1": "2560x2560", "16:9": "2560x1440", "9:16": "1440x2560",
        "3:2": "2560x1712", "2:3": "1712x2560", "4:3": "2560x1920",
        "3:4": "1920x2560", "4:5": "2048x2560", "5:4": "2560x2048",
        "21:9": "3360x1440",
    },
}

QUALITY_BY_IMAGE_SIZE = {
    "512px": "low",
    "1K": "high",
    "2K": "high",
    "4K": "high",
}


def _workbench_script_path() -> Path:
    configured = os.environ.get("IMAGE_LOCAL_WORKBENCH_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_WORKBENCH_SCRIPT


def _load_workbench_module() -> Any:
    script = _workbench_script_path()
    if not script.is_file():
        raise FileNotFoundError(f"Hanako local image workbench script not found: {script}")

    spec = importlib.util.spec_from_file_location("hanako_local_openai_compatible_image", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Hanako local image workbench script: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_image_size(image_size: str) -> str:
    s = str(image_size or "1K").strip()
    upper = s.upper()
    if upper in ("1K", "2K", "4K"):
        return upper
    if upper in ("512PX", "512"):
        return "512px"
    return s


def _resolve_output_path(prompt: str, output_dir: str | None = None,
                         filename: str | None = None, ext: str = ".png") -> str:
    if filename:
        file_name = os.path.splitext(filename)[0]
    else:
        safe = "".join(c for c in prompt if c.isalnum() or c in (" ", "_")).rstrip()
        safe = safe.replace(" ", "_").lower()[:30]
        file_name = safe or "generated_image"
    full_name = f"{file_name}{ext}"
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return str(Path(output_dir) / full_name)
    return full_name


def _select_size(aspect_ratio: str, image_size: str) -> str:
    image_size = _normalize_image_size(image_size)
    if image_size not in GPT_IMAGE_2_SIZES:
        raise ValueError(f"Unsupported image_size for local workbench: {image_size}")
    if aspect_ratio not in GPT_IMAGE_2_SIZES[image_size]:
        supported = sorted(GPT_IMAGE_2_SIZES[image_size])
        raise ValueError(f"Unsupported aspect_ratio for local workbench: {aspect_ratio}; supported: {supported}")
    return GPT_IMAGE_2_SIZES[image_size][aspect_ratio]


def _target_output(prompt: str, output_dir: str | None, filename: str | None) -> str:
    # PPT Master expects an exact file in project/images, so do not pass output_dir
    # to the local workbench. Its output_dir mode intentionally creates timestamped
    # subfolders. We compute the final path here and pass it as `output`.
    return _resolve_output_path(prompt, output_dir, filename, ".png")


def generate(prompt: str, negative_prompt: str = None,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = 0) -> str:
    """
    Generate one image through the Hanako local workbench and return the saved path.

    `max_retries` is accepted for PPT Master backend compatibility. Retry policy is
    intentionally left to PPT Master's caller / pipeline layer and the local provider.
    """
    del max_retries

    final_prompt = prompt
    if negative_prompt:
        final_prompt = f"{prompt}\n\nAvoid the following: {negative_prompt}"

    size = _select_size(aspect_ratio, image_size)
    normalized_image_size = _normalize_image_size(image_size)

    quality = os.environ.get("IMAGE_LOCAL_WORKBENCH_QUALITY") or QUALITY_BY_IMAGE_SIZE.get(normalized_image_size, "high")
    background = os.environ.get("IMAGE_LOCAL_WORKBENCH_BACKGROUND", "auto")
    timeout_raw = os.environ.get("IMAGE_LOCAL_WORKBENCH_TIMEOUT", "").strip()
    timeout = float(timeout_raw) if timeout_raw else None
    output = _target_output(final_prompt, output_dir, filename)

    workbench_script = _workbench_script_path()
    print("[Hanako Local Workbench]")
    print(f"  Script:       {workbench_script}")
    print(f"  Model:        {model or 'from local workbench .env'}")
    print(f"  Size:         {size} (from aspect_ratio={aspect_ratio}, image_size={normalized_image_size})")
    print(f"  Quality:      {quality}")
    print(f"  Output:       {output}")
    print()

    module = _load_workbench_module()
    try:
        result = module.generate_images(
            prompt=final_prompt,
            output=output,
            output_dir=None,
            size=size,
            model=model,
            n=1,
            timeout=timeout,
            quality=quality,
            background=background,
        )
    except SystemExit as exc:
        raise RuntimeError(str(exc)) from exc

    images = result.get("images") or []
    if not images:
        raise RuntimeError("Local workbench returned no images.")

    saved_path = str(images[0].get("path") or output)
    print(f"  File saved to: {saved_path}")
    return saved_path
