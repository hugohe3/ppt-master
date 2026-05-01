import html
import re
from pathlib import Path
import types

import requests

from image_backends.backend_common import resilient_get
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

# Words that won't match image metadata in keyword-based search APIs.
_NOISE_WORDS = frozenset({
    "claude", "openai", "gpt", "gemini", "copilot", "chatgpt", "midjourney",
    "stable", "diffusion", "dall-e", "cursor", "anthropic", "microsoft",
    "google", "apple", "meta", "nvidia", "tesla",
    "ai", "code", "software", "system", "digital", "platform", "solution",
    "application", "interface", "framework", "algorithm", "api", "sdk",
    "assistant", "tool", "service", "technology", "tech", "program",
    "using", "with", "from", "that", "this", "have", "been", "will",
    "into", "more", "also", "very", "some", "than", "them", "other",
})


def _simplify_query(query: str, max_words: int = 4) -> str:
    """Simplify a verbose query for keyword-based image search APIs."""
    cleaned = re.sub(r"#[0-9a-fA-F]{3,8}", "", query)
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)
    words = cleaned.split()
    filtered = [w for w in words if w.lower() not in _NOISE_WORDS and len(w) > 2]
    if len(filtered) <= max_words:
        return " ".join(filtered)
    return " ".join(filtered[:max_words])


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


def _build_attribution_text(filename, candidate):
    title_part = f'"{candidate.title}"' if candidate.title else ""
    author_part = f"by {candidate.author}" if candidate.author else ""
    return f"{filename} — {title_part} {author_part}, via Wikimedia Commons, source: {candidate.source_page_url}, license: {candidate.license_name} {candidate.license_url}".strip()


def _requires_attribution(license_name, license_url):
    text = " ".join(
        part.strip().lower()
        for part in (license_name or "", license_url or "")
        if part
    )
    return "cc0" not in text and "public domain" not in text and "/publicdomain/" not in text


_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"})


def parse_results(payload):
    candidates = []
    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        for imageinfo in page.get("imageinfo", []):
            download_url = (imageinfo.get("url") or imageinfo.get("thumburl") or "").strip()
            if not download_url:
                continue
            # Skip non-image files (PDFs, SVGs, DJVU, etc.)
            url_path = download_url.split("?")[0].lower()
            if not any(url_path.endswith(ext) for ext in _IMAGE_EXTENSIONS):
                continue
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
                    attribution_required=_requires_attribution(license_name, license_url),
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
    clean_orientation = (orientation or "").strip().lower()

    # Try progressively simpler queries: original → simplified → first 3 words
    queries_to_try = [query]
    simplified = _simplify_query(query)
    if simplified != query:
        queries_to_try.append(simplified)
    words = simplified.split()
    if len(words) > 3:
        short = " ".join(words[:3])
        if short != simplified:
            queries_to_try.append(short)

    headers = {"User-Agent": "PPTMaster/1.0 (https://github.com/hugohe3/ppt-master; heyug3@gmail.com)"}
    request = ImageSearchRequest(
        query=query,
        purpose=purpose,
        orientation="" if clean_orientation == "any" else clean_orientation,
        filename=filename,
        slide=slide,
    )
    candidates = []
    for q in queries_to_try:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": q,
            "gsrnamespace": 6,
            "gsrlimit": search_limit,
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
        }
        response = resilient_get(API_URL, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        candidates = parse_results(response.json())
        if candidates:
            break
    if not candidates:
        raise RuntimeError(f"No acceptable Wikimedia candidates found for query: {query}")

    best_candidate = max(candidates, key=lambda candidate: score_candidate(candidate, request))

    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
        "orientation": orientation,
        "attribution_text": _build_attribution_text(filename, best_candidate),
    }
