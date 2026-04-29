import html
import re
from pathlib import Path
import types

import requests

from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
    is_allowed_license,
    score_candidate,
)


API_URL = "https://commons.wikimedia.org/w/api.php"
DEFAULT_SEARCH_LIMIT = 20
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


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


def clean_html_text(value):
    if not value:
        return ""
    text = html.unescape(str(value))
    text = TAG_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _extract_metadata(extmetadata, key):
    value = extmetadata.get(key, {})
    if isinstance(value, dict):
        value = value.get("value", "")
    return clean_html_text(value)


def _page_title_to_label(title):
    clean_title = clean_html_text(title)
    if clean_title.lower().startswith("file:"):
        return clean_title.split(":", 1)[1].strip()
    return clean_title


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
    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        for imageinfo in page.get("imageinfo", []):
            extmetadata = imageinfo.get("extmetadata") or {}
            license_name = _extract_metadata(extmetadata, "LicenseShortName")
            license_url = _extract_metadata(extmetadata, "LicenseUrl")
            if not is_allowed_license(license_name, license_url, provider="wikimedia"):
                continue

            title = (
                _extract_metadata(extmetadata, "ImageDescription")
                or _page_title_to_label(page.get("title", ""))
                or "Untitled"
            )
            author = (
                _extract_metadata(extmetadata, "Artist")
                or _extract_metadata(extmetadata, "Credit")
            )
            download_url = (imageinfo.get("url") or imageinfo.get("thumburl") or "").strip()
            if not download_url:
                continue

            candidates.append(
                AssetCandidate(
                    provider="wikimedia",
                    asset_id=str(page.get("pageid") or page.get("title") or ""),
                    title=title,
                    source_page_url=(imageinfo.get("descriptionurl") or "").strip(),
                    license_name=license_name,
                    license_url=license_url,
                    width=_as_int(imageinfo.get("width")),
                    height=_as_int(imageinfo.get("height")),
                    download_url=download_url,
                    author=author,
                    attribution_required=license_name.lower() not in ("cc0", "public domain"),
                    raw=page,
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
    search_limit=DEFAULT_SEARCH_LIMIT,
):
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": search_limit,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
    }
    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()

    clean_orientation = (orientation or "").strip().lower()
    request = ImageSearchRequest(
        query=query,
        purpose=purpose,
        orientation="" if clean_orientation == "any" else clean_orientation,
        filename=filename,
        slide=slide,
    )
    candidates = parse_results(response.json())
    if not candidates:
        raise RuntimeError(f"No acceptable Wikimedia candidates found for query: {query}")

    best_candidate = max(candidates, key=lambda candidate: score_candidate(candidate, request))

    output_path = Path(output_dir) / filename
    download_image = _load_download_image()
    download_image(best_candidate.download_url, str(output_path))

    return {
        "filename": filename,
        "slide": slide,
        "purpose": purpose,
        "provider": "wikimedia",
        "search_query": query,
        "source_page_url": best_candidate.source_page_url,
        "download_url": best_candidate.download_url,
        "author": best_candidate.author,
        "license_name": best_candidate.license_name,
        "license_url": best_candidate.license_url,
        "attribution_required": best_candidate.attribution_required,
        "attribution_text": _build_attribution_text(best_candidate),
    }
