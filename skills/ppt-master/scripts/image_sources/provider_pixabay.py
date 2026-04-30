import os
from pathlib import Path
import types

import requests

from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
    is_allowed_license,
    score_candidate,
)


API_URL = "https://pixabay.com/api/"
DEFAULT_PAGE_SIZE = 20
LICENSE_NAME = "Pixabay Content License"
LICENSE_URL = "https://pixabay.com/service/license-summary/"
ORIENTATION_MAP = {
    "landscape": "horizontal",
    "portrait": "vertical",
}


def _load_download_image():
    try:
        from image_backends.backend_common import download_image

        return download_image
    except TypeError as exc:
        if "|" not in str(exc):
            raise

    backend_path = Path(__file__).resolve().parent.parent / "image_backends" / "backend_common.py"
    source = backend_path.read_text(encoding="utf-8")
    module = types.ModuleType("_provider_backend_common_compat")
    exec(
        compile(
            "from __future__ import annotations\n" + source,
            str(backend_path),
            "exec",
        ),
        module.__dict__,
    )
    return module.download_image


def _as_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _build_attribution_text(candidate):
    parts = []
    if candidate.title:
        parts.append(candidate.title)
    if candidate.author:
        parts.append(f"by {candidate.author}")
    if candidate.license_name:
        parts.append(candidate.license_name)
    return " - ".join(parts)


def parse_results(payload):
    candidates = []
    for item in payload.get("hits", []):
        license_name = LICENSE_NAME
        license_url = LICENSE_URL
        if not is_allowed_license(license_name, license_url, provider="pixabay"):
            continue

        download_url = (
            (item.get("largeImageURL") or "").strip()
            or (item.get("webformatURL") or "").strip()
            or (item.get("previewURL") or "").strip()
        )
        if not download_url:
            continue

        title = (item.get("tags") or "").strip() or "Untitled"
        candidates.append(
            AssetCandidate(
                provider="pixabay",
                asset_id=str(item.get("id") or ""),
                title=title,
                source_page_url=(item.get("pageURL") or "").strip(),
                license_name=license_name,
                license_url=license_url,
                width=_as_int(item.get("imageWidth")),
                height=_as_int(item.get("imageHeight")),
                download_url=download_url,
                author=(item.get("user") or "").strip(),
                attribution_required=False,
                raw=item,
            )
        )
    return candidates


def search_and_download(
    *,
    query,
    output_dir,
    filename,
    slide="",
    purpose="",
    orientation="any",
    timeout=30,
    page_size=DEFAULT_PAGE_SIZE,
):
    api_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PIXABAY_API_KEY is required for the Pixabay provider")

    params = {
        "key": api_key,
        "q": query,
        "per_page": page_size,
    }
    clean_orientation = (orientation or "").strip().lower()
    if clean_orientation in ORIENTATION_MAP:
        params["orientation"] = ORIENTATION_MAP[clean_orientation]

    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()

    request = ImageSearchRequest(
        query=query,
        purpose=purpose,
        orientation="" if clean_orientation == "any" else clean_orientation,
        filename=filename,
        slide=slide,
    )
    candidates = parse_results(response.json())
    if not candidates:
        raise RuntimeError(f"No acceptable Pixabay candidates found for query: {query}")

    best_candidate = max(candidates, key=lambda candidate: score_candidate(candidate, request))

    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    download_image = _load_download_image()
    download_image(best_candidate.download_url, str(output_path))

    return {
        "filename": filename,
        "slide": slide,
        "purpose": purpose,
        "provider": "pixabay",
        "search_query": query,
        "source_page_url": best_candidate.source_page_url,
        "download_url": best_candidate.download_url,
        "author": best_candidate.author,
        "license_name": best_candidate.license_name,
        "license_url": best_candidate.license_url,
        "attribution_required": best_candidate.attribution_required,
        "attribution_text": _build_attribution_text(best_candidate),
    }
