#!/usr/bin/env python3
"""
OpenAI Compatible Image Generation Backend

Generates images via OpenAI-compatible APIs (OpenAI, local models like Qwen-Image, etc.).
Used by image_gen.py as a backend module.

Configuration keys:
  OPENAI_API_KEY   (required) API key
  OPENAI_BASE_URL  (optional) Custom API endpoint (e.g. http://127.0.0.1:3000/v1)
  OPENAI_MODEL     (optional) Model name (default: gpt-image-2.5-sunburst)
  OPENAI_SIZE_PRESET         (optional) auto, legacy, gpt-image, gpt-image-2, or dall-e-2
  OPENAI_RESPONSE_FORMAT     (optional) auto, b64_json, url, or omit
  OPENAI_QUALITY             (optional) auto, omit, low, medium, high, xhigh, max, standard, or hd
  OPENAI_OUTPUT_FORMAT       (optional) png, jpeg, or webp; gif with --gif-frames
  OPENAI_OUTPUT_COMPRESSION  (optional) 0-100, only for jpeg/webp GPT image output
  OPENAI_BACKGROUND          (optional) auto, opaque, or transparent for GPT image models
  OPENAI_MODERATION          (optional) auto or low for GPT image models
  OPENAI_INPUT_FIDELITY      (optional) high or low for supported GPT image edits

Image editing (image-to-image):
  When image_gen.py passes reference_image=<path> (single-image CLI only,
  via --reference-image), this backend calls /v1/images/edits with the source
  image + the prompt as an edit instruction, instead of /v1/images/generations.

GIF output (single-image CLI only):
  --gif-frames N (2-16) enables GIF generation or reference-image editing on
  gpt-image-2.6-* and later 2.x minors. --gif-frame-ms MS sets a positive frame
  duration (default 200 ms). Candidate sheets (columns x rows, measured
  2026-11-08): N=2-8: 2x4 or 4x2; N=9: 3x3; N=10-12: 3x4, 4x3, or 4x4;
  N=13-16: 4x4. Fit the requested ratio per grid and choose the largest frame
  by area: width <= floor(3840/columns), height <= floor(3840/rows), pixels
  <= 8,294,400/(columns*rows), multiples of 16, and an edge ratio <= 3:1.
  N=2-8 is always billed as an 8-cell sheet; fewer frames at the same size
  do not cost less. image_size still selects quality. Output is saved
  unchanged as .gif; OPENAI_OUTPUT_FORMAT must be unset or gif, and
  OPENAI_OUTPUT_COMPRESSION must be unset. See scripts/docs/image.md.

Dependencies:
  pip install requests Pillow
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
    print("Use via: python3 skills/ppt-master/scripts/image_gen.py \"prompt\" --backend openai")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import base64
import mimetypes
import os
import re
import time
import threading
from collections.abc import Mapping

import requests
from image_backends.backend_common import (
    MAX_RETRIES,
    download_image,
    fit_size,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    match_aspect_ratio,
    nearest_aspect_ratio,
    normalize_image_size,
    note_aspect_ratio,
    parse_aspect_ratio,
    resolve_output_path,
    retry_delay,
    save_image_bytes,
)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Constants                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# Aspect ratio -> DALL-E 3 / legacy compatible size mapping.
# Unknown OpenAI-compatible models use this table to preserve old behavior;
# other ratios take the nearest entry.
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

# Legacy GPT Image models and chatgpt-image-latest support only square,
# landscape, portrait, or auto.
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
# Listed ratios use these sizes; any other ratio is fitted to the rules at
# the tier's 1:1 pixel budget (beyond 3:1 it is clamped to 3:1).
GPT_IMAGE_2_SIZES = {
    "512px": {
        "1:1": "1024x1024", "16:9": "1280x720", "9:16": "720x1280",
        "3:2": "1248x832", "2:3": "832x1248", "4:3": "1024x768",
        "3:4": "768x1024", "4:5": "896x1120", "5:4": "1120x896",
        "21:9": "1280x544",
    },
    "1K": {
        "1:1": "1024x1024", "16:9": "1280x720", "9:16": "720x1280",
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

# image_size -> quality mapping
IMAGE_SIZE_TO_QUALITY = {
    "512px": "low",
    "1K":    "medium",
    "2K":    "high",
    "4K":    "high",
}

DEFAULT_MODEL = "gpt-image-2.5-sunburst"

GPT_IMAGE_2_MIN_PIXELS = 655_360
GPT_IMAGE_2_MAX_PIXELS = 8_294_400
GPT_IMAGE_2_MAX_EDGE = 3840
GPT_IMAGE_2_MAX_RATIO = 3

GPT_IMAGE_OUTPUT_FORMATS = {"png", "jpeg", "webp"}
GPT_IMAGE_OUTPUT_EXTENSIONS = {
    "png": ".png",
    "jpeg": ".jpg",
    "webp": ".webp",
    "gif": ".gif",
}
OPENAI_SIZE_PRESETS = {
    "auto",
    "legacy",
    "gpt-image",
    "gpt-image-legacy",
    "gpt-image-2",
    "dall-e-2",
    "dalle-2",
}
OPENAI_RESPONSE_FORMATS = {"auto", "b64_json", "url", "omit"}
OPENAI_QUALITY_VALUES = {
    "auto",
    "omit",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "standard",
    "hd",
}
GPT_IMAGE_BACKGROUNDS = {"auto", "opaque", "transparent"}
GPT_IMAGE_MODERATION_VALUES = {"auto", "low"}
GPT_IMAGE_INPUT_FIDELITY_VALUES = {"high", "low"}
DEFAULT_BASE_URL = "https://api.openai.com/v1"

# Signals to image_gen.py that this backend can accept a reference_image
# (image-to-image edit via /v1/images/edits). Other backends omit this marker.
SUPPORTS_REFERENCE_IMAGE = True
SUPPORTS_GIF = True


def _field(value, name: str):
    """Read a response field from either an SDK object or a dict."""
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _normalized_model(model: str) -> str:
    return (model or "").strip().lower()


def _is_gpt_image_model(model: str) -> bool:
    normalized = _normalized_model(model)
    return (
        normalized.startswith("gpt-image-")
        or normalized == "chatgpt-image-latest"
    )


def _is_gpt_image_2(model: str) -> bool:
    normalized = _normalized_model(model)
    return normalized.startswith("gpt-image-2") and not normalized.startswith("gpt-image-2.")


_GPT_IMAGE_2_MINOR_RE = re.compile(r"gpt-image-2\.(\d+)-")


def _is_gpt_image_2_5_or_later(model: str) -> bool:
    """GPT Image 2.5, 2.6, and later 2.x releases share sizes, quality tiers, and edit options."""
    match = _GPT_IMAGE_2_MINOR_RE.match(_normalized_model(model))
    return bool(match) and int(match.group(1)) >= 5


def _is_dall_e_2(model: str) -> bool:
    return _normalized_model(model) == "dall-e-2"


def _parse_size(size: str) -> tuple[int, int]:
    try:
        width_s, height_s = size.lower().split("x", 1)
        return int(width_s), int(height_s)
    except Exception as exc:
        raise ValueError(f"Invalid image size '{size}'. Expected WIDTHxHEIGHT.") from exc


def _validate_gpt_image_2_size(size: str) -> None:
    width, height = _parse_size(size)
    total_pixels = width * height
    long_edge = max(width, height)
    short_edge = min(width, height)

    errors = []
    if long_edge > GPT_IMAGE_2_MAX_EDGE:
        errors.append(f"max edge {long_edge}px exceeds {GPT_IMAGE_2_MAX_EDGE}px")
    if width % 16 != 0 or height % 16 != 0:
        errors.append("both edges must be multiples of 16px")
    if long_edge / short_edge > GPT_IMAGE_2_MAX_RATIO:
        errors.append("long:short edge ratio must not exceed 3:1")
    if not (GPT_IMAGE_2_MIN_PIXELS <= total_pixels <= GPT_IMAGE_2_MAX_PIXELS):
        errors.append(
            f"total pixels {total_pixels:,} must be between "
            f"{GPT_IMAGE_2_MIN_PIXELS:,} and {GPT_IMAGE_2_MAX_PIXELS:,}"
        )
    if errors:
        raise ValueError(f"Invalid gpt-image-2 size '{size}': {', '.join(errors)}")


def _nearest_listed_size(aspect_ratio: str, table: dict[str, str]) -> str:
    """Keep a listed ratio's size; otherwise pick the size whose real W:H is nearest.

    Legacy keys are nominal (5:4 maps to 1536x1024), so unlisted ratios compare
    against the sizes themselves, not the keys.
    """
    listed = match_aspect_ratio(aspect_ratio, table)
    if listed:
        return table[listed]
    sizes = {size.replace("x", ":"): size for size in table.values()}
    return sizes[nearest_aspect_ratio(aspect_ratio, sizes)]


def _select_size(
    model: str,
    aspect_ratio: str,
    image_size: str,
    size_preset: str | None = None,
    gif_frames: int | None = None,
) -> str:
    """Select a model-compatible size while preserving legacy fallbacks."""
    if gif_frames is not None:
        if gif_frames <= 8:
            grids = ((2, 4), (4, 2))
        elif gif_frames == 9:
            grids = ((3, 3),)
        elif gif_frames <= 12:
            grids = ((3, 4), (4, 3), (4, 4))
        else:
            grids = ((4, 4),)
        ratio = float(min(max(parse_aspect_ratio(aspect_ratio), 1 / GPT_IMAGE_2_MAX_RATIO),
                          GPT_IMAGE_2_MAX_RATIO))
        sizes = []
        for columns, rows in grids:
            max_width = GPT_IMAGE_2_MAX_EDGE // columns
            max_height = GPT_IMAGE_2_MAX_EDGE // rows
            # Translate the per-axis caps into fit_size's single long-edge cap.
            max_edge = (min(max_width, max_height * ratio) if ratio >= 1
                        else min(max_height, max_width / ratio))
            pixels = GPT_IMAGE_2_MAX_PIXELS // (columns * rows)
            sizes.append(fit_size(
                aspect_ratio,
                pixels=pixels,
                step=16,
                max_edge=int(max_edge),
                max_pixels=pixels,
                max_ratio=GPT_IMAGE_2_MAX_RATIO,
            ))
        width, height = max(sizes, key=lambda size: size[0] * size[1])
        return f"{width}x{height}"
    preset = size_preset or "auto"
    if preset in {"gpt-image-2"} or (
        preset == "auto" and (_is_gpt_image_2(model) or _is_gpt_image_2_5_or_later(model))
    ):
        sizes = GPT_IMAGE_2_SIZES[image_size]
        listed = match_aspect_ratio(aspect_ratio, sizes)
        if listed:
            size = sizes[listed]
        else:
            square_w, square_h = _parse_size(sizes["1:1"])
            width, height = fit_size(
                aspect_ratio,
                pixels=square_w * square_h,
                step=16,
                max_edge=GPT_IMAGE_2_MAX_EDGE,
                min_pixels=GPT_IMAGE_2_MIN_PIXELS,
                max_pixels=GPT_IMAGE_2_MAX_PIXELS,
                max_ratio=GPT_IMAGE_2_MAX_RATIO,
            )
            size = f"{width}x{height}"
        _validate_gpt_image_2_size(size)
        return size
    if preset in {"gpt-image", "gpt-image-legacy"} or (
        preset == "auto" and _is_gpt_image_model(model)
    ):
        return _nearest_listed_size(aspect_ratio, GPT_IMAGE_LEGACY_ASPECT_RATIO_TO_SIZE)
    if preset in {"dall-e-2", "dalle-2"} or (preset == "auto" and _is_dall_e_2(model)):
        return DALL_E_2_SIZE_BY_IMAGE_SIZE[image_size]
    return _nearest_listed_size(aspect_ratio, LEGACY_COMPAT_ASPECT_RATIO_TO_SIZE)


def _supports_response_format(model: str) -> bool:
    """GPT Image models always return base64; DALL-E/compatible models may need this."""
    return not _is_gpt_image_model(model)


def _read_env_choice(name: str, allowed: set[str]) -> str | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    normalized = value.strip().lower()
    if normalized not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(f"Invalid {name}='{value}'. Supported: {allowed_list}")
    return normalized


def _read_env_int(name: str, minimum: int, maximum: int) -> int | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {name}='{value}'. Expected integer {minimum}-{maximum}.") from exc
    if not (minimum <= parsed <= maximum):
        raise ValueError(f"Invalid {name}={parsed}. Expected integer {minimum}-{maximum}.")
    return parsed


def _gpt_image_options(model: str, gif_frames: int | None = None,
                       gif_frame_ms: int | None = None) -> tuple[dict, str]:
    """Read optional GPT Image request parameters from environment."""
    if gif_frames is not None:
        configured_format = os.environ.get("OPENAI_OUTPUT_FORMAT")
        if configured_format is not None and configured_format.strip().lower() != "gif":
            raise ValueError("GIF output requires OPENAI_OUTPUT_FORMAT to be unset or gif.")
        if "OPENAI_OUTPUT_COMPRESSION" in os.environ:
            raise ValueError("GIF output does not support OPENAI_OUTPUT_COMPRESSION. Remove this setting.")
    formats = {"gif"} if gif_frames is not None else GPT_IMAGE_OUTPUT_FORMATS
    output_format = _read_env_choice("OPENAI_OUTPUT_FORMAT", formats)
    if gif_frames is not None:
        output_format = "gif"
    output_ext = GPT_IMAGE_OUTPUT_EXTENSIONS[output_format] if output_format else ".png"
    options = {}
    if output_format:
        options["output_format"] = output_format
    if gif_frames is not None:
        options["frame_count"] = gif_frames
        if gif_frame_ms is not None:
            options["frame_duration_ms"] = gif_frame_ms

    output_compression = _read_env_int("OPENAI_OUTPUT_COMPRESSION", 0, 100)
    if output_compression is not None:
        if output_format not in {"jpeg", "webp"}:
            raise ValueError(
                "OPENAI_OUTPUT_COMPRESSION is only supported when "
                "OPENAI_OUTPUT_FORMAT is jpeg or webp."
            )
        options["output_compression"] = output_compression

    background = _read_env_choice("OPENAI_BACKGROUND", GPT_IMAGE_BACKGROUNDS)
    if background:
        if background == "transparent" and output_format == "jpeg":
            raise ValueError(
                "OPENAI_BACKGROUND=transparent requires OPENAI_OUTPUT_FORMAT=png or webp, not jpeg."
            )
        options["background"] = background

    moderation = _read_env_choice("OPENAI_MODERATION", GPT_IMAGE_MODERATION_VALUES)
    if moderation:
        options["moderation"] = moderation

    return options, output_ext


def _read_input_fidelity(model: str) -> str | None:
    """Read input fidelity for GPT Image edit requests."""
    input_fidelity = _read_env_choice(
        "OPENAI_INPUT_FIDELITY",
        GPT_IMAGE_INPUT_FIDELITY_VALUES,
    )
    if input_fidelity is None:
        return None
    if _is_gpt_image_2(model) or _is_gpt_image_2_5_or_later(model):
        raise ValueError(
            f"{model} does not accept OPENAI_INPUT_FIDELITY in this backend. Remove this setting."
        )
    if not _is_gpt_image_model(model):
        raise ValueError(
            f"{model} does not support OPENAI_INPUT_FIDELITY in this backend."
        )
    if _normalized_model(model) == "gpt-image-1-mini" and input_fidelity != "low":
        raise ValueError(f"{model} only supports OPENAI_INPUT_FIDELITY=low.")
    return input_fidelity


def _image_generations_url(base_url: str | None) -> str:
    base = (base_url or DEFAULT_BASE_URL).rstrip("/")
    if base.endswith("/images/generations"):
        return base
    return f"{base}/images/generations"


def _image_edits_url(base_url: str | None) -> str:
    base = (base_url or DEFAULT_BASE_URL).rstrip("/")
    if base.endswith("/images/edits"):
        return base
    if base.endswith("/images/generations"):
        # Swap the sibling endpoint rather than appending to a full URL.
        return base[: -len("/generations")] + "/edits"
    return f"{base}/images/edits"


def _read_size_preset() -> str | None:
    """Read the optional size mapping preset for OpenAI-compatible providers."""
    return _read_env_choice("OPENAI_SIZE_PRESET", OPENAI_SIZE_PRESETS)


def _read_response_format() -> str | None:
    """Read the optional response_format override."""
    return _read_env_choice("OPENAI_RESPONSE_FORMAT", OPENAI_RESPONSE_FORMATS)


def _read_quality(image_size: str, model: str) -> str | None:
    """Resolve the quality field for OpenAI-compatible requests."""
    quality = _read_env_choice("OPENAI_QUALITY", OPENAI_QUALITY_VALUES)
    if quality == "omit":
        return None
    if quality in {"xhigh", "max"} and not _is_gpt_image_2_5_or_later(model):
        raise ValueError(
            f"{model} does not support OPENAI_QUALITY={quality}. "
            "Only GPT Image 2.5 and later models (gpt-image-2.5-*, gpt-image-2.6-*, including snapshots) "
            "support xhigh and max."
        )
    if quality and quality != "auto":
        if _is_gpt_image_model(model) and quality in {"standard", "hd"}:
            raise ValueError(
                f"{model} does not support OPENAI_QUALITY={quality}. "
                "Use auto, omit, low, medium, or high."
            )
        return quality
    return IMAGE_SIZE_TO_QUALITY.get(image_size, "auto")


def _apply_response_format(request: dict, model: str) -> None:
    """Apply response_format while preserving the existing default behavior."""
    response_format = _read_response_format()
    if response_format == "omit":
        return
    if not _supports_response_format(model):
        if response_format in {"b64_json", "url"}:
            raise ValueError(
                f"{model} does not support OPENAI_RESPONSE_FORMAT. "
                "Use auto or omit."
            )
        return
    if response_format in {"b64_json", "url"}:
        request["response_format"] = response_format
        return
    request["response_format"] = "b64_json"


def _validate_request_options(
    model: str,
    aspect_ratio: str,
    image_size: str,
    *,
    editing: bool,
    gif_frames: int | None = None,
    gif_frame_ms: int | None = None,
) -> None:
    """Validate local model options before entering the retry loop."""
    if gif_frame_ms is not None:
        if gif_frames is None:
            raise ValueError("gif_frame_ms requires gif_frames (--gif-frames).")
        if type(gif_frame_ms) is not int or gif_frame_ms <= 0:
            raise ValueError("gif_frame_ms must be a positive integer.")
    if gif_frames is not None:
        if type(gif_frames) is not int or not 2 <= gif_frames <= 16:
            raise ValueError("gif_frames must be an integer from 2 to 16.")
        match = _GPT_IMAGE_2_MINOR_RE.match(_normalized_model(model))
        if not match or int(match.group(1)) < 6:
            raise ValueError(
                f"{model} does not support GIF output. Use gpt-image-2.6-* "
                "or a later 2.x minor via --model or OPENAI_MODEL."
            )
    size_preset = _read_size_preset()
    _select_size(model, aspect_ratio, image_size, size_preset, gif_frames)
    if not (editing and _is_dall_e_2(model)):
        _read_quality(image_size, model)
    if _is_gpt_image_model(model):
        _gpt_image_options(model, gif_frames, gif_frame_ms)
    if editing:
        _read_input_fidelity(model)
    _apply_response_format({}, model)


def _post_image_generation(api_key: str, base_url: str | None, request: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        _image_generations_url(base_url),
        headers=headers,
        json=request,
        timeout=300,
    )
    if not response.ok:
        raise http_error(response, "OpenAI image generation")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("OpenAI image generation returned invalid JSON.") from exc


def _post_image_edit(api_key: str, base_url: str | None,
                     data: dict, image_path: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    # GPT Image models take the image list field 'image[]'; dall-e-2 and other
    # OpenAI-compatible edit models use the singular 'image'.
    model = str(data.get("model", ""))
    field = "image[]" if _is_gpt_image_model(model) else "image"
    mime_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
    # Let requests build the multipart/form-data body (and its Content-Type
    # boundary) from files=; do not set Content-Type by hand.
    with open(image_path, "rb") as image_file:
        response = requests.post(
            _image_edits_url(base_url),
            headers=headers,
            data=data,
            files=[(field, (Path(image_path).name, image_file, mime_type))],
            timeout=300,
        )
    if not response.ok:
        raise http_error(response, "OpenAI image edit")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("OpenAI image edit returned invalid JSON.") from exc


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Image Generation                                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = "1K",
                    output_dir: str = None, filename: str = None,
                    model: str = DEFAULT_MODEL, base_url: str = None,
                    gif_frames: int | None = None, gif_frame_ms: int | None = None) -> str:
    """
    Image generation via OpenAI-compatible API.

    Maps aspect_ratio to OpenAI's size parameter, and image_size to quality.

    Returns:
        Path of the saved image file

    Raises:
        RuntimeError: When generation fails
    """
    # Map parameters
    size_preset = _read_size_preset()
    size = _select_size(model, aspect_ratio, image_size, size_preset, gif_frames)
    quality = _read_quality(image_size, model)
    output_ext = ".png"
    request = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "n": 1,
    }
    if quality is not None:
        request["quality"] = quality
    if _is_gpt_image_model(model):
        gpt_options, output_ext = _gpt_image_options(model, gif_frames, gif_frame_ms)
        request.update(gpt_options)
    _apply_response_format(request, model)

    mode_label = f"Proxy: {base_url}" if base_url else "OpenAI API"
    print(f"[OpenAI - {mode_label}]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    size_label = "Frame size:" if gif_frames is not None else "Size:"
    print(f"  {size_label:<14}{size} (from aspect_ratio={aspect_ratio})")
    if gif_frames is not None:
        print(f"  Frames:       {gif_frames}")
        print(f"  Frame ms:     {gif_frame_ms if gif_frame_ms is not None else 200}")
    note_aspect_ratio(aspect_ratio, size.replace("x", ":"))
    if size_preset and size_preset != "auto":
        print(f"  Size Preset:  {size_preset}")
    if quality is not None:
        print(f"  Quality:      {quality} (from image_size={image_size})")
    else:
        print("  Quality:      omitted")
    if request.get("response_format"):
        print(f"  Response:     {request['response_format']}")
    elif _read_response_format() == "omit":
        print("  Response:     omitted")
    if request.get("output_format"):
        print(f"  Format:       {request['output_format']}")
    if request.get("output_compression") is not None:
        print(f"  Compression:  {request['output_compression']}")
    if request.get("background"):
        print(f"  Background:   {request['background']}")
    if request.get("moderation"):
        print(f"  Moderation:   {request['moderation']}")
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
        resp = _post_image_generation(api_key, base_url, request)
    finally:
        heartbeat_stop.set()
        hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  [DONE] Image generated ({elapsed:.1f}s)")

    data = _field(resp, "data") if resp is not None else None
    if data:
        path = resolve_output_path(prompt, output_dir, filename, output_ext)
        if gif_frames is not None:
            # A caller's static suffix must not transcode and flatten the GIF.
            path = str(Path(path).with_suffix(".gif"))
        first_image = data[0]
        b64_json = _field(first_image, "b64_json")
        image_url = _field(first_image, "url")
        if b64_json:
            image_data = base64.b64decode(b64_json)
            return save_image_bytes(image_data, path)
        if image_url:
            return download_image(image_url, path)

    raise RuntimeError("No image was generated. The server may have refused the request.")


def _edit_image(api_key: str, prompt: str, reference_image: str,
                aspect_ratio: str = "1:1", image_size: str = "1K",
                output_dir: str = None, filename: str = None,
                model: str = DEFAULT_MODEL, base_url: str = None,
                gif_frames: int | None = None, gif_frame_ms: int | None = None) -> str:
    """
    Image-to-image edit via the OpenAI-compatible /v1/images/edits endpoint.

    Sends the reference image plus the prompt (used as the edit instruction).
    Mirrors _generate_image's size/quality/format handling but posts
    multipart/form-data instead of JSON.

    Returns:
        Path of the saved image file
    """
    size_preset = _read_size_preset()
    size = _select_size(model, aspect_ratio, image_size, size_preset, gif_frames)
    quality = None if _is_dall_e_2(model) else _read_quality(image_size, model)
    output_ext = ".png"
    request = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "n": 1,
    }
    if quality is not None:
        request["quality"] = quality
    if _is_gpt_image_model(model):
        gpt_options, output_ext = _gpt_image_options(model, gif_frames, gif_frame_ms)
        request.update(gpt_options)
    input_fidelity = _read_input_fidelity(model)
    if input_fidelity is not None:
        request["input_fidelity"] = input_fidelity
    _apply_response_format(request, model)

    mode_label = f"Proxy: {base_url}" if base_url else "OpenAI API"
    print(f"[OpenAI - {mode_label}]")
    print(f"  Mode:         edit (image-to-image)")
    print(f"  Model:        {model}")
    print(f"  Reference:    {reference_image}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    size_label = "Frame size:" if gif_frames is not None else "Size:"
    print(f"  {size_label:<14}{size} (from aspect_ratio={aspect_ratio})")
    if gif_frames is not None:
        print(f"  Frames:       {gif_frames}")
        print(f"  Frame ms:     {gif_frame_ms if gif_frame_ms is not None else 200}")
    note_aspect_ratio(aspect_ratio, size.replace("x", ":"))
    if size_preset and size_preset != "auto":
        print(f"  Size Preset:  {size_preset}")
    if quality is not None:
        print(f"  Quality:      {quality} (from image_size={image_size})")
    else:
        print("  Quality:      omitted")
    if request.get("response_format"):
        print(f"  Response:     {request['response_format']}")
    elif _read_response_format() == "omit":
        print("  Response:     omitted")
    if request.get("output_format"):
        print(f"  Format:       {request['output_format']}")
    if request.get("output_compression") is not None:
        print(f"  Compression:  {request['output_compression']}")
    if request.get("background"):
        print(f"  Background:   {request['background']}")
    if request.get("moderation"):
        print(f"  Moderation:   {request['moderation']}")
    if request.get("input_fidelity"):
        print(f"  Input Fidelity: {request['input_fidelity']}")
    print()

    start_time = time.time()
    print(f"  [..] Editing...", end="", flush=True)

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
        resp = _post_image_edit(api_key, base_url, request, reference_image)
    finally:
        heartbeat_stop.set()
        hb_thread.join(timeout=1)

    elapsed = time.time() - start_time
    print(f"\n  [DONE] Image edited ({elapsed:.1f}s)")

    data = _field(resp, "data") if resp is not None else None
    if data:
        path = resolve_output_path(prompt, output_dir, filename, output_ext)
        if gif_frames is not None:
            path = str(Path(path).with_suffix(".gif"))
        first_image = data[0]
        b64_json = _field(first_image, "b64_json")
        image_url = _field(first_image, "url")
        if b64_json:
            image_data = base64.b64decode(b64_json)
            return save_image_bytes(image_data, path)
        if image_url:
            return download_image(image_url, path)

    raise RuntimeError("No image was returned. The server may have refused the edit request.")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  Public Entry Point                                             ║
# ╚══════════════════════════════════════════════════════════════════╝

def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES,
             reference_image: str = None,
             gif_frames: int | None = None, gif_frame_ms: int | None = None) -> str:
    """
    OpenAI-compatible image generation (or image-to-image edit) with retry.

    Reads credentials from the current process environment or a `.env` file:
      OPENAI_API_KEY
      OPENAI_BASE_URL
      OPENAI_MODEL (optional override)

    Args:
        prompt: Prompt text (edit instruction when reference_image is set)
        aspect_ratio: Aspect ratio, mapped to OpenAI size
        image_size: Image size, mapped to OpenAI quality
        output_dir: Output directory
        filename: Output filename (without extension)
        model: Model name (default: gpt-image-2.5-sunburst)
        max_retries: Maximum number of retries
        reference_image: Optional source image path. When set, the request
            goes to /v1/images/edits (image-to-image) instead of
            /v1/images/generations.
        gif_frames: Optional GIF frame count (2-16); requires GPT Image 2.6+.
        gif_frame_ms: Optional positive frame duration in ms (API default 200).

    Returns:
        Path of the saved image file
    """
    if model is None:
        model = os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL

    image_size = normalize_image_size(image_size)

    parse_aspect_ratio(aspect_ratio)

    _validate_request_options(
        model,
        aspect_ratio,
        image_size,
        editing=reference_image is not None,
        gif_frames=gif_frames,
        gif_frame_ms=gif_frame_ms,
    )

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        raise ValueError(
            "No API key found. Set OPENAI_API_KEY in the current environment or a .env file."
        )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            if reference_image is not None:
                return _edit_image(api_key, prompt, reference_image,
                                   aspect_ratio, image_size, output_dir,
                                   filename, model, base_url, gif_frames, gif_frame_ms)
            return _generate_image(api_key, prompt,
                                   aspect_ratio, image_size, output_dir,
                                   filename, model, base_url, gif_frames, gif_frame_ms)
        except Exception as e:
            last_error = e
            if is_permanent_error(e):
                raise
            if attempt < max_retries and is_rate_limit_error(e):
                delay = retry_delay(attempt, rate_limited=True, exc=e)
                print(f"\n  [WARN] Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                      f"Waiting {delay}s before retry...")
                time.sleep(delay)
            elif attempt < max_retries:
                delay = retry_delay(attempt, rate_limited=False, exc=e)
                print(f"\n  [WARN] Error (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                      f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                break

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}") from last_error
