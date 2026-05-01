from pathlib import Path
import types

import requests

from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
    is_allowed_license,
    score_candidate,
)


API_URL = "https://api.openverse.org/v1/images/"
DEFAULT_PAGE_SIZE = 20

# Words that won't match image metadata in keyword-based search APIs.
# Includes brand names, abstract tech terms, and generic filler.
_NOISE_WORDS = frozenset({
    # Brand/product names
    "claude", "openai", "gpt", "gemini", "copilot", "chatgpt", "midjourney",
    "stable", "diffusion", "dall-e", "cursor", "anthropic", "microsoft",
    "google", "apple", "meta", "nvidia", "tesla",
    # Abstract tech terms that rarely appear in image metadata
    "ai", "code", "software", "system", "digital", "platform", "solution",
    "application", "interface", "framework", "algorithm", "api", "sdk",
    "assistant", "tool", "service", "technology", "tech", "program",
    # Generic filler
    "using", "with", "from", "that", "this", "have", "been", "will",
    "into", "more", "also", "very", "some", "than", "them", "other",
})


def _simplify_query(query: str, max_words: int = 4) -> str:
    """Simplify a verbose query for keyword-based image search APIs.

    Openverse does full-text keyword matching on image metadata, not semantic search.
    Long queries with brand names, HEX codes, and composition notes return zero results.
    This extracts the most searchable keywords — concrete nouns and visual descriptors.
    """
    import re
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


def _build_attribution_text(filename, candidate):
    title_part = f'"{candidate.title}"' if candidate.title else ""
    author_part = f"by {candidate.author}" if candidate.author else ""
    return f"{filename} — {title_part} {author_part}, via Openverse, source: {candidate.source_page_url}, license: {candidate.license_name} {candidate.license_url}".strip()


def _requires_attribution(license_name, license_url):
    text = " ".join(
        part.strip().lower()
        for part in (license_name or "", license_url or "")
        if part
    )
    return "cc0" not in text and "public domain" not in text and "/publicdomain/" not in text


def parse_results(payload):
    candidates = []
    for item in payload.get("results", []):
        license_name = (item.get("license") or "").strip()
        license_url = (item.get("license_url") or "").strip()
        if not is_allowed_license(license_name, license_url, provider="openverse"):
            continue

        title = (item.get("title") or "").strip() or "Untitled"
        source_page_url = (item.get("foreign_landing_url") or item.get("detail_url") or "").strip()
        download_url = (item.get("url") or item.get("thumbnail") or "").strip()
        if not download_url:
            continue

        candidates.append(
            AssetCandidate(
                provider="openverse",
                asset_id=str(item.get("id") or ""),
                title=title,
                source_page_url=source_page_url,
                license_name=license_name,
                license_url=license_url,
                width=_as_int(item.get("width")),
                height=_as_int(item.get("height")),
                download_url=download_url,
                author=(item.get("creator") or "").strip(),
                attribution_required=_requires_attribution(license_name, license_url),
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
    clean_orientation = (orientation or "").strip().lower()
    orientation_to_aspect = {"landscape": "wide", "portrait": "tall", "square": "square"}

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
            "q": q,
            "page_size": page_size,
            "license": "by,by-sa,cc0,pdm",
            "size": "large",
        }
        if clean_orientation in orientation_to_aspect:
            params["aspect_ratio"] = orientation_to_aspect[clean_orientation]
        response = requests.get(API_URL, params=params, timeout=timeout)
        response.raise_for_status()
        candidates = parse_results(response.json())
        if candidates:
            break
    if not candidates:
        raise RuntimeError(f"No acceptable Openverse candidates found for query: {query}")

    best_candidate = max(candidates, key=lambda candidate: score_candidate(candidate, request))

    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    download_image = _load_download_image()
    download_image(best_candidate.download_url, str(output_path))

    return {
        "filename": filename,
        "slide": slide,
        "purpose": purpose,
        "provider": "openverse",
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
