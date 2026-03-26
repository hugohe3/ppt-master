#!/usr/bin/env python3
"""
Shared helpers for image generation backends.
"""

import os
import time

import requests

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


MAX_RETRIES = 3
RETRY_BASE_DELAY = 10
RETRY_BACKOFF = 2


def resolve_output_path(prompt: str, output_dir: str = None,
                        filename: str = None, ext: str = ".png") -> str:
    """Compute the final output file path based on parameters."""
    if filename:
        file_name = os.path.splitext(filename)[0]
    else:
        safe = "".join(c for c in prompt if c.isalnum() or c in (" ", "_")).rstrip()
        safe = safe.replace(" ", "_").lower()[:30]
        file_name = safe or "generated_image"

    full_name = f"{file_name}{ext}"
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, full_name)
    return full_name


def report_resolution(path: str):
    """Try to report image resolution using PIL."""
    if HAS_PIL:
        try:
            img = PILImage.open(path)
            print(f"  Resolution:   {img.size[0]}x{img.size[1]}")
        except Exception:
            pass


def normalize_image_size(image_size: str) -> str:
    """Normalize image size input to standard format."""
    s = image_size.strip()
    upper = s.upper()
    if upper in ("1K", "2K", "4K"):
        return upper
    if upper in ("512PX", "512"):
        return "512px"
    return s


def is_rate_limit_error(exc: Exception) -> bool:
    """Check whether the exception appears to be rate limiting."""
    err_str = str(exc).lower()
    return (
        "429" in err_str
        or "rate" in err_str
        or "quota" in err_str
        or "resource_exhausted" in err_str
    )


def retry_delay(attempt: int, rate_limited: bool) -> int:
    """Return the retry delay for a given attempt."""
    if rate_limited:
        return RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
    return 5


def download_image(url: str, path: str, headers: dict = None, timeout: int = 180) -> str:
    """Download an image URL and save it to disk."""
    response = requests.get(url, headers=headers or {}, timeout=timeout)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    print(f"  File saved to: {path}")
    report_resolution(path)
    return path


def require_api_key(*candidates: str, message: str):
    """Return the first non-empty env var from candidates or raise."""
    for name in candidates:
        value = os.environ.get(name)
        if value:
            return value
    raise ValueError(message)


def http_error(response: requests.Response, label: str) -> RuntimeError:
    """Convert an HTTP response into a readable RuntimeError."""
    body = response.text.strip()
    if len(body) > 500:
        body = body[:500] + "..."
    return RuntimeError(f"{label} failed ({response.status_code}): {body}")


def poll_json(url: str, headers: dict, *,
              interval_seconds: float = 2.0,
              timeout_seconds: int = 300,
              status_label: str = "status",
              ready_values=None,
              failed_values=None) -> dict:
    """Poll a JSON endpoint until it reports a ready or failed status."""
    ready = {value.lower() for value in (ready_values or ["ready", "success", "succeeded"])}
    failed = {value.lower() for value in (failed_values or ["error", "failed", "fail"])}

    start = time.time()
    while True:
        response = requests.get(url, headers=headers, timeout=180)
        response.raise_for_status()
        payload = response.json()
        raw_status = str(payload.get(status_label, "")).strip()
        status = raw_status.lower()

        if raw_status:
            print(f"  Status:       {raw_status}")

        if status in ready:
            return payload

        if status in failed:
            raise RuntimeError(f"Remote generation failed: {payload}")

        if time.time() - start > timeout_seconds:
            raise RuntimeError(
                f"Timed out after {timeout_seconds}s while polling {url}"
            )

        time.sleep(interval_seconds)
