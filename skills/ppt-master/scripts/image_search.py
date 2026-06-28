#!/usr/bin/env python3
"""Web image search CLI.

Sister tool to ``image_gen.py``: instead of generating an image from a
prompt, this searches openly-licensed image providers and downloads a
single best match.

Workflow:
    1. Build an :class:`ImageSearchRequest` from CLI args.
    2. Quality-first license search:
       - Default: ask each provider for ``all`` allowed matches (CC0,
         Public Domain, Pexels, Pixabay, CC BY, CC BY-SA), pick the
         highest-scoring downloadable candidate, and record whether it
         needs attribution.
       - Strict mode: when ``--strict-no-attribution`` is set, ask only
         for ``no-attribution-only`` matches and fail if none can be
         downloaded.
    3. Download the chosen image into ``--output``.
    4. Append a record to ``image_sources.json`` (the single source of
       truth for downstream credit rendering).

Examples:
    # Default: zero-config, quality-first across allowed licenses
    python3 scripts/image_search.py "offshore wind farm" \
        --filename cover_bg.jpg --slide 01_cover \
        --orientation landscape -o projects/demo/images

    # Strict mode: refuse anything that would require attribution
    python3 scripts/image_search.py "abstract gradient" \
        --filename hero.jpg --strict-no-attribution \
        -o projects/demo/images

    # Pin a specific provider (useful when an API key is set)
    python3 scripts/image_search.py "executive meeting" \
        --filename team.jpg --provider pexels \
        --orientation landscape -o projects/demo/images
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import json
import os
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# Make sibling modules importable when this script is invoked directly.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from config import load_prefixed_env_file  # noqa: E402
from image_backends.backend_common import download_image  # noqa: E402
from image_sources.provider_common import (  # noqa: E402
    AssetCandidate,
    ImageSearchRequest,
    USER_AGENT,
    build_attribution_text,
    ensure_json_parent,
    score_candidate,
)

configure_utf8_stdio()


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDER_MODULES: dict[str, str] = {
    "openverse": "image_sources.provider_openverse",
    "wikimedia": "image_sources.provider_wikimedia",
    "pexels": "image_sources.provider_pexels",
    "pixabay": "image_sources.provider_pixabay",
}

# Providers that work without configuration. ``image_search.py`` defaults
# to these so a fresh clone can search immediately.
ZERO_CONFIG_PROVIDERS: tuple[str, ...] = ("openverse", "wikimedia")
KEYED_PROVIDERS: tuple[str, ...] = ("pexels", "pixabay")
ALL_PROVIDERS: tuple[str, ...] = ZERO_CONFIG_PROVIDERS + KEYED_PROVIDERS

ORIENTATION_CHOICES = ("any", "landscape", "portrait", "square")

# --- Batch mode (`--batch image_queries.json`) -----------------------------
# Web providers are politeness-sensitive (Wikimedia/Openverse expect a modest
# rate), so the default concurrency is deliberately low. Sister-tool
# `image_gen.py` hits a paid API and defaults higher; here 3 keeps several
# rows in flight without hammering any single free provider. Set to 1 to
# restore strict one-at-a-time pacing.
DEFAULT_SEARCH_CONCURRENCY = 3

SEARCH_STATUS_PENDING = "Pending"
SEARCH_STATUS_SOURCED = "Sourced"
SEARCH_STATUS_FAILED = "Failed"
SEARCH_STATUS_NEEDS_MANUAL = "Needs-Manual"
SEARCH_VALID_STATUSES = {
    SEARCH_STATUS_PENDING,
    SEARCH_STATUS_SOURCED,
    SEARCH_STATUS_FAILED,
    SEARCH_STATUS_NEEDS_MANUAL,
}
# A row reaching `Needs-Manual` after the full provider/stage chain is terminal
# (see image-searcher.md §8); only Pending/Failed rows are retried on re-run.
SEARCH_RETRYABLE_STATUSES = {SEARCH_STATUS_PENDING, SEARCH_STATUS_FAILED}
SEARCH_REQUIRED_ITEM_FIELDS = ("filename", "query", "status")

_WEAK_REQUIRED_TERM_PARTS = frozenset({
    "ancient town",
    "bridge",
    "canyon",
    "cave",
    "city",
    "floating bridge",
    "forest",
    "gate",
    "grand canyon",
    "ground fissure",
    "lake",
    "monastery",
    "monument",
    "river",
    "shrine",
    "square",
    "station",
    "stone forest",
    "stone pillar",
    "stream",
    "temple",
    "valley",
    "village",
    "古城",
    "古镇",
    "地缝",
    "大峡谷",
    "寺",
    "峡谷",
    "广场",
    "桥",
    "洞",
    "溪",
    "石林",
    "石柱",
})


def _parse_required_terms(raw: object) -> tuple[str, ...]:
    """Parse entity-safety terms from CLI / batch JSON.

    Multiple groups are ANDed. Alternatives inside one group are separated by
    ``|``; comma splitting is accepted as CLI convenience. Examples:
    ``["Chongqing", "Jiefangbei|Liberation Monument"]``.
    """
    if raw is None:
        return ()
    values: list[str]
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, (list, tuple)):
        values = []
        for item in raw:
            if not isinstance(item, str):
                raise ValueError("required_terms items must be strings")
            values.append(item)
    else:
        raise ValueError("required_terms must be a string or list of strings")

    terms: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                terms.append(part)
    return tuple(terms)


def _warn_weak_required_terms(required_terms: tuple[str, ...]) -> None:
    """Warn when required_terms contain generic category words.

    These terms are useful in the query but dangerous as identity gates:
    broadening a small Chinese attraction from its proper name to "canyon" /
    "stone pillar" raises coverage while admitting wrong entities.
    """
    weak: list[str] = []
    for group in required_terms:
        for part in group.split("|"):
            normalized = part.strip().lower()
            if normalized in _WEAK_REQUIRED_TERM_PARTS:
                weak.append(part.strip())
    if weak:
        print(
            "  warning: required_terms contains generic category term(s) "
            f"{weak}; keep proper-name / geography anchors too, and prefer "
            "Needs-Manual or --from-url over loosening identity gates.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------


def _load_search_env_file() -> None:
    """Load image-search keys from the shared PPT Master .env locations."""
    load_prefixed_env_file(("PEXELS_", "PIXABAY_"))


# ---------------------------------------------------------------------------
# Provider dispatch
# ---------------------------------------------------------------------------


def _load_provider(name: str):
    return importlib.import_module(PROVIDER_MODULES[name])


def _is_keyed_provider_unconfigured(provider_name: str, exc: Exception) -> bool:
    """Treat 'API key missing' as a non-fatal skip so the default provider
    chain can keep going."""
    if provider_name not in KEYED_PROVIDERS:
        return False
    return "API_KEY" in str(exc)


def _try_provider(
    name: str,
    request: ImageSearchRequest,
    license_tier_filter: str,
) -> Optional[list[AssetCandidate]]:
    """Run one provider; print and swallow recoverable errors, return None
    so the dispatcher can try the next provider."""
    try:
        module = _load_provider(name)
        return module.search(request, license_tier_filter=license_tier_filter)
    except RuntimeError as exc:
        if _is_keyed_provider_unconfigured(name, exc):
            print(
                f"  [{name}] skipped: {exc}",
                file=sys.stderr,
            )
        else:
            print(f"  [{name}] error: {exc}", file=sys.stderr)
        return None
    except (requests.RequestException, ValueError) as exc:
        print(f"  [{name}] error: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Post-download quality validation
# ---------------------------------------------------------------------------

_MIN_DOWNLOAD_PIXELS = 800 * 600  # reject anything below ~480K px


def _validate_downloaded_quality(path: Path) -> bool:
    """Reject images that are too small after download.

    Upstream metadata can be inaccurate (e.g. Openverse aggregates rawpixel
    which only exposes a preview). This function checks what was actually
    written to disk and rejects thumbnails / previews.
    """
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return True  # can't check without Pillow; assume OK
    try:
        with Image.open(path) as im:
            w, h = im.size
            if w * h < _MIN_DOWNLOAD_PIXELS:
                print(
                    f"    rejected: downloaded image too small "
                    f"({w}x{h} = {w*h:,} px < {_MIN_DOWNLOAD_PIXELS:,} px minimum)",
                    file=sys.stderr,
                )
                return False
            return True
    except (OSError, ValueError):
        return True  # unreadable image; let downstream handle it


def _write_review_copy(
    src: Path, dest_dir: Path, name: str, max_side: int = 1024
) -> Optional[Path]:
    """Write a downscaled JPEG review copy of ``src`` into ``dest_dir``.

    The placed / promoted asset is always the full-resolution original; this
    bounded copy exists only so the agent can Read a sanely-sized image to
    confirm suitability regardless of how large the source is. Best-effort —
    returns None (non-fatal) if Pillow or the source is unavailable.
    """
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return None
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        review_path = dest_dir / f"{Path(name).stem}.jpg"
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((max_side, max_side))
            im.save(review_path, "JPEG", quality=85)
        return review_path
    except (OSError, ValueError):
        return None


def _save_candidates_pool(
    ranked: list[tuple[float, str, AssetCandidate]],
    output_dir: Path,
    stem: str,
    selected_filename: str,
    max_candidates: int = 4,
) -> None:
    """Download top-N candidates into ``candidates/<stem>/`` and write
    a ``candidates.json`` manifest for manual review."""
    cand_dir = output_dir / "candidates" / stem
    cand_dir.mkdir(parents=True, exist_ok=True)

    pool: list[dict] = []
    idx = 0
    for score, provider_name, candidate in ranked:
        if idx >= max_candidates:
            break
        suffix = Path(candidate.download_url.split("?")[0]).suffix or ".jpg"
        cand_filename = f"candidate_{idx + 1:02d}{suffix}"
        cand_path = cand_dir / cand_filename
        try:
            download_image(
                candidate.download_url,
                str(cand_path),
                headers={"User-Agent": USER_AGENT},
            )
            if not _validate_downloaded_quality(cand_path):
                cand_path.unlink(missing_ok=True)
                continue
        except (requests.RequestException, OSError, RuntimeError, ValueError):
            continue
        idx += 1
        actual_dim = _measure_actual_image(cand_path)
        review_path = _write_review_copy(cand_path, cand_dir / "review", cand_filename)
        pool.append({
            "rank": idx,
            "score": round(score, 2),
            "filename": cand_filename,
            "review": f"review/{review_path.name}" if review_path else None,
            "provider": provider_name,
            "title": candidate.title,
            "author": candidate.author,
            "source_page_url": candidate.source_page_url,
            "download_url": candidate.download_url,
            "license_name": candidate.license_name,
            "license_url": candidate.license_url,
            "license_tier": candidate.license_tier,
            "attribution_required": candidate.license_tier == "attribution-required",
            "attribution_text": build_attribution_text(selected_filename, candidate),
            "width": actual_dim[0] if actual_dim else candidate.width,
            "height": actual_dim[1] if actual_dim else candidate.height,
        })

    if pool:
        meta = {
            "target_filename": selected_filename,
            "selected": pool[0]["filename"],
            "searched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "candidates": pool,
        }
        meta_path = cand_dir / "candidates.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  candidates: {cand_dir}/ ({len(pool)} saved)", file=sys.stderr)


def search_and_download(
    providers: list[str],
    request: ImageSearchRequest,
    *,
    output_path: Path,
    strict_no_attribution: bool,
    save_candidates: bool = False,
    max_candidates: int = 4,
) -> tuple[Optional[AssetCandidate], Optional[str], Optional[str]]:
    """Find a candidate AND successfully download it.

    By default only the best match is downloaded. When ``save_candidates``
    is True (opt-in), the top-N candidates are also saved to
    ``candidates/<stem>/`` so the agent can review and ``--promote`` a
    better fit when the best match does not pass visual confirmation.

    Returns ``(candidate, provider_name, stage)`` for the successfully
    downloaded image, or ``(None, None, None)`` if every combination
    failed.
    """
    license_filters: list[str] = (
        ["no-attribution-only"] if strict_no_attribution else ["all"]
    )

    for stage in license_filters:
        ranked: list[tuple[float, str, AssetCandidate]] = []
        for provider_name in providers:
            print(f"  -> trying {provider_name} ({stage}) ...", file=sys.stderr)
            candidates = _try_provider(provider_name, request, stage)
            if not candidates:
                continue

            provider_ranked = [
                (score_candidate(c, request), provider_name, c) for c in candidates
            ]
            provider_ranked = [
                item for item in provider_ranked if item[0] != float("-inf")
            ]
            if not provider_ranked:
                reason = "query"
                if request.required_terms:
                    reason += f" / required_terms={list(request.required_terms)}"
                print(
                    f"    no candidate matched {reason}; trying next provider/stage",
                    file=sys.stderr,
                )
                continue
            ranked.extend(provider_ranked)

        sorted_ranked = sorted(ranked, key=lambda item: item[0], reverse=True)

        # --- Save candidate pool (before picking the winner) ---
        if save_candidates and sorted_ranked:
            stem = Path(output_path).stem
            _save_candidates_pool(
                sorted_ranked, output_path.parent, stem, output_path.name,
                max_candidates=max_candidates,
            )

        # --- Pick the best downloadable candidate ---
        for _score, provider_name, candidate in sorted_ranked:
            # If candidates were already saved, the file may already
            # exist in the candidates dir — but we still need the
            # primary copy at output_path.
            try:
                download_image(
                    candidate.download_url,
                    str(output_path),
                    headers={"User-Agent": USER_AGENT},
                )
                if not _validate_downloaded_quality(output_path):
                    output_path.unlink(missing_ok=True)
                    continue
                review = _write_review_copy(
                    output_path, output_path.parent / ".review", output_path.name
                )
                if review is not None:
                    print(f"  review copy: {review}", file=sys.stderr)
                return candidate, provider_name, stage
            except (requests.RequestException, OSError, RuntimeError, ValueError) as exc:
                print(
                    f"    download failed for {candidate.title!r}: {exc}",
                    file=sys.stderr,
                )
                continue

    return None, None, None


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def default_manifest_path(output_dir: str) -> Path:
    return Path(output_dir) / "image_sources.json"


def _measure_actual_image(path: Path) -> Optional[tuple[int, int]]:
    """Return ``(width, height)`` of the file actually saved at ``path``.

    Upstream metadata (``candidate.width``/``height``) describes the
    original image on the provider's server, which may differ from what
    we are allowed to download — for example, second-tier sources
    aggregated by Openverse (rawpixel etc.) often only expose a
    1024px-wide preview. The Executor needs to know what is actually on
    disk for layout purposes; this function provides that ground truth.

    Returns ``None`` if Pillow is unavailable or the file is unreadable.
    """
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            return int(im.width), int(im.height)
    except (OSError, ValueError):
        return None


def _candidate_to_manifest_item(
    candidate: AssetCandidate,
    args: argparse.Namespace,
    *,
    provider_name: str,
    stage: str,
    actual_dimensions: Optional[tuple[int, int]] = None,
) -> dict:
    """Build the manifest entry.

    ``width`` / ``height`` reflect the file actually saved to disk
    (measured by Pillow after download). The upstream-claimed dimensions
    are only kept under ``metadata_dimensions`` when they disagree with
    reality, which is the only case where this distinction matters.
    """
    if actual_dimensions is not None:
        width, height = actual_dimensions
    else:
        width, height = candidate.width, candidate.height

    item = {
        "filename": args.filename,
        "slide": args.slide,
        "purpose": args.purpose,
        "search_query": args.query,
        "orientation": args.orientation,
        "provider": provider_name,
        "stage": stage,
        "title": candidate.title,
        "author": candidate.author,
        "source_page_url": candidate.source_page_url,
        "download_url": candidate.download_url,
        "license_name": candidate.license_name,
        "license_url": candidate.license_url,
        "license_tier": candidate.license_tier,
        "attribution_required": candidate.license_tier == "attribution-required",
        "width": width,
        "height": height,
        "attribution_text": build_attribution_text(args.filename, candidate),
        "status": "sourced",
    }
    required_terms = _parse_required_terms(
        getattr(args, "required_terms", None) or getattr(args, "require_terms", None)
    )
    if required_terms:
        item["required_terms"] = list(required_terms)

    # Only carry upstream-claimed dimensions when they differ — this flags
    # cases where the provider returned a preview rather than the original.
    if (
        actual_dimensions is not None
        and candidate.width
        and candidate.height
        and (candidate.width, candidate.height) != actual_dimensions
    ):
        item["metadata_dimensions"] = {
            "width": candidate.width,
            "height": candidate.height,
            "note": "upstream-reported size; actual downloaded file is smaller (likely a preview)",
        }

    return item


def _read_existing_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"  warning: existing manifest at {path} is unreadable, "
            f"starting fresh ({exc})",
            file=sys.stderr,
        )
        return {}


def write_sources_manifest(path: Path, item: dict) -> Path:
    """Append ``item`` to the manifest at ``path``, replacing any prior
    entry that targets the same filename."""
    manifest_path = ensure_json_parent(path)
    payload = _read_existing_manifest(manifest_path)

    items: list[dict] = list(payload.get("items") or [])
    items = [i for i in items if i.get("filename") != item["filename"]]
    items.append(item)

    payload["items"] = items
    payload["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload.setdefault(
        "license_verification",
        "provider metadata used; manual review recommended for external delivery",
    )

    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest_path


# ---------------------------------------------------------------------------
# Promote: replace primary image with a candidate
# ---------------------------------------------------------------------------


def promote_candidate(
    output_dir: Path,
    target_filename: str,
    candidate_filename: str,
    manifest_path: Optional[Path] = None,
) -> int:
    """Replace the primary image with a candidate from the pool.

    Steps:
        1. Copy ``candidates/<stem>/<candidate_filename>`` → ``<target_filename>``
        2. Update ``candidates.json`` selected field
        3. Update ``image_sources.json`` with the candidate's metadata
    """
    import shutil

    stem = Path(target_filename).stem
    cand_dir = output_dir / "candidates" / stem
    cand_meta_path = cand_dir / "candidates.json"

    if not cand_meta_path.exists():
        print(f"Error: {cand_meta_path} not found.", file=sys.stderr)
        return 1

    meta = json.loads(cand_meta_path.read_text(encoding="utf-8"))
    candidates = meta.get("candidates", [])

    entry = next((c for c in candidates if c["filename"] == candidate_filename), None)
    if entry is None:
        names = [c["filename"] for c in candidates]
        print(
            f"Error: '{candidate_filename}' not found. Available: {', '.join(names)}",
            file=sys.stderr,
        )
        return 1

    src_path = cand_dir / candidate_filename
    dst_path = output_dir / target_filename
    if not src_path.exists():
        print(f"Error: {src_path} does not exist on disk.", file=sys.stderr)
        return 1

    shutil.copy2(str(src_path), str(dst_path))
    print(f"  promoted: {candidate_filename} → {target_filename}", file=sys.stderr)
    review = _write_review_copy(dst_path, output_dir / ".review", target_filename)
    if review is not None:
        print(f"  review copy: {review}", file=sys.stderr)

    # Update candidates.json
    meta["selected"] = candidate_filename
    cand_meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )

    # Update image_sources.json
    mpath = manifest_path or default_manifest_path(str(output_dir))
    actual_dim = _measure_actual_image(dst_path)
    w = actual_dim[0] if actual_dim else entry.get("width", 0)
    h = actual_dim[1] if actual_dim else entry.get("height", 0)

    manifest = _read_existing_manifest(mpath)
    items: list[dict] = list(manifest.get("items") or [])
    for item in items:
        if item.get("filename") == target_filename:
            item["provider"] = entry["provider"]
            item["title"] = entry["title"]
            item["author"] = entry["author"]
            item["source_page_url"] = entry["source_page_url"]
            item["download_url"] = entry["download_url"]
            item["license_name"] = entry["license_name"]
            item["license_url"] = entry.get("license_url", "")
            item["license_tier"] = entry["license_tier"]
            item["attribution_required"] = entry.get("attribution_required", False)
            # Recompute the credit from the promoted candidate — never carry the
            # replaced image's attribution_text (wrong author/title/source).
            item["attribution_text"] = build_attribution_text(
                target_filename,
                AssetCandidate(
                    provider=entry.get("provider", ""),
                    title=entry.get("title", ""),
                    source_page_url=entry.get("source_page_url", ""),
                    license_name=entry.get("license_name", ""),
                    license_url=entry.get("license_url", ""),
                    license_tier=entry.get("license_tier", ""),
                    width=w,
                    height=h,
                    download_url=entry.get("download_url", ""),
                    author=entry.get("author", ""),
                ),
            )
            item["width"] = w
            item["height"] = h
            item.pop("metadata_dimensions", None)
            item["status"] = "promoted"
            break
    manifest["items"] = items
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    mpath.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    print(f"  manifest updated: {mpath}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# Manual URL replacement (model-agnostic)
# ---------------------------------------------------------------------------


def fetch_url_replace(
    output_dir: Path,
    target_filename: str,
    url: str,
    manifest_path: Optional[Path] = None,
    *,
    slide: str = "",
    purpose: str = "",
    search_query: str = "",
    orientation: str = "",
    required_terms: tuple[str, ...] = (),
) -> int:
    """Download a user-supplied image URL into the target and record it.

    The model-agnostic manual path: when an automated best match is not
    suitable (or the running model cannot see images at all), a human finds a
    good image, passes its URL, and it replaces the target. License is unknown
    for an arbitrary URL, so the manifest marks it ``manual`` and notes that
    verifying usage rights is the user's responsibility.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dst_path = output_dir / target_filename
    try:
        download_image(url, str(dst_path), headers={"User-Agent": USER_AGENT})
    except (requests.RequestException, OSError, RuntimeError, ValueError) as exc:
        print(f"Error: failed to download {url}: {exc}", file=sys.stderr)
        return 1
    if not dst_path.exists():
        print(f"Error: download produced no file at {dst_path}", file=sys.stderr)
        return 1

    print(f"  fetched: {url} -> {target_filename}", file=sys.stderr)
    review = _write_review_copy(dst_path, output_dir / ".review", target_filename)
    if review is not None:
        print(f"  review copy: {review}", file=sys.stderr)

    actual_dim = _measure_actual_image(dst_path)
    mpath = manifest_path or default_manifest_path(str(output_dir))
    # Inherit page context (which slide / purpose / query this image serves)
    # from the entry being replaced; override only source / license / size /
    # status so the audit trail survives a manual swap.
    prior = next(
        (i for i in _read_existing_manifest(mpath).get("items", [])
         if i.get("filename") == target_filename),
        {},
    )
    item = {
        "filename": target_filename,
        "slide": prior.get("slide") or slide,
        "purpose": prior.get("purpose") or purpose,
        "search_query": prior.get("search_query") or search_query,
        "orientation": prior.get("orientation") or orientation,
        "provider": "manual",
        "title": "",
        "author": "",
        "source_page_url": url,
        "download_url": url,
        "license_name": "unverified — user-supplied URL",
        "license_url": "",
        "license_tier": "manual",
        "attribution_required": False,
        "width": actual_dim[0] if actual_dim else 0,
        "height": actual_dim[1] if actual_dim else 0,
        "attribution_text": "",
        "status": "manual",
        "note": "Manually supplied image URL; verifying usage rights is the user's responsibility.",
    }
    inherited_required_terms = _parse_required_terms(prior.get("required_terms"))
    final_required_terms = inherited_required_terms or required_terms
    if final_required_terms:
        item["required_terms"] = list(final_required_terms)
    written = write_sources_manifest(mpath, item)
    print(f"  manifest updated: {written}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# Batch mode (`--batch image_queries.json`)
# ---------------------------------------------------------------------------


def load_search_manifest(path: str) -> dict:
    """Load and validate an ``image_queries.json`` batch manifest.

    Schema (top level): ``{"items": [ ... ]}``. Each item requires
    ``filename``, ``query``, ``status``. Optional per-item overrides:
    ``slide``, ``purpose``, ``orientation``, ``provider``,
    ``strict_no_attribution``, ``min_width``, ``min_height``, ``last_error``.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path}: {exc.msg} "
            f"(line {exc.lineno}, col {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top level must be a JSON object, got {type(data).__name__}"
        )

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: 'items' must be a non-empty array")

    seen_filenames: set[str] = set()
    for i, item in enumerate(items):
        prefix = f"{path}: items[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be an object")
        for field in SEARCH_REQUIRED_ITEM_FIELDS:
            if field not in item:
                raise ValueError(f"{prefix} missing required field '{field}'")
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(
                    f"{prefix} field '{field}' must be a non-empty string"
                )
        if item["status"] not in SEARCH_VALID_STATUSES:
            raise ValueError(
                f"{prefix} status '{item['status']}' is invalid. "
                f"Valid: {sorted(SEARCH_VALID_STATUSES)}"
            )
        if "required_terms" in item:
            try:
                _parse_required_terms(item["required_terms"])
            except ValueError as exc:
                raise ValueError(f"{prefix} {exc}") from exc
        fname = item["filename"]
        if fname in seen_filenames:
            raise ValueError(f"{prefix} duplicate filename '{fname}'")
        seen_filenames.add(fname)

    return data


def save_search_manifest(path: str, data: dict) -> None:
    """Atomically write the batch manifest back (tmp file + rename)."""
    target = Path(path)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.stem + ".", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _resolve_search_concurrency(cli_value: Optional[int]) -> int:
    """CLI value wins over IMAGE_SEARCH_CONCURRENCY env; default 3."""
    if cli_value is not None:
        return max(1, cli_value)
    env_val = os.environ.get("IMAGE_SEARCH_CONCURRENCY", "").strip()
    if env_val.isdigit():
        return max(1, int(env_val))
    return DEFAULT_SEARCH_CONCURRENCY


def _search_one_item(
    item: dict,
    *,
    output_dir: Path,
    save_candidates: bool,
    max_candidates: int,
    default_provider: Optional[str],
    default_strict: bool,
    default_min_width: int,
    default_min_height: int,
) -> tuple[Optional[dict], Optional[str]]:
    """Run the full search + download for one batch item (thread worker).

    Returns ``(manifest_item, error)``. Only the network/disk work happens
    here; all manifest writes are serialized by the caller.
    """
    orientation = item.get("orientation", "any") or "any"
    strict = bool(item.get("strict_no_attribution", default_strict))
    required_terms = _parse_required_terms(item.get("required_terms"))
    _warn_weak_required_terms(required_terms)
    request = ImageSearchRequest(
        query=item["query"],
        purpose=item.get("purpose", ""),
        orientation="" if orientation == "any" else orientation,
        filename=item["filename"],
        slide=item.get("slide", ""),
        min_width=int(item.get("min_width", default_min_width)),
        min_height=int(item.get("min_height", default_min_height)),
        required_terms=required_terms,
    )

    pinned = item.get("provider") or default_provider
    providers = [pinned] if pinned else _default_provider_chain()
    output_path = output_dir / item["filename"]

    candidate, provider_name, stage = search_and_download(
        providers,
        request,
        output_path=output_path,
        strict_no_attribution=strict,
        save_candidates=save_candidates,
        max_candidates=max_candidates,
    )
    if candidate is None:
        return None, "no acceptable candidate across all providers/stages"

    actual_dimensions = _measure_actual_image(output_path)
    item_args = argparse.Namespace(
        filename=item["filename"],
        slide=item.get("slide", ""),
        purpose=item.get("purpose", ""),
        query=item["query"],
        orientation=orientation,
        required_terms=request.required_terms,
    )
    manifest_item = _candidate_to_manifest_item(
        candidate,
        item_args,
        provider_name=provider_name,
        stage=stage,
        actual_dimensions=actual_dimensions,
    )
    return manifest_item, None


def run_search_manifest(
    manifest: dict,
    manifest_path: str,
    *,
    output_dir: Path,
    sources_manifest_path: Path,
    concurrency: int,
    save_candidates: bool,
    max_candidates: int,
    default_provider: Optional[str],
    default_strict: bool,
    default_min_width: int,
    default_min_height: int,
) -> tuple[int, int, int]:
    """Process all Pending/Failed rows concurrently with a bounded pool.

    On success the rich provenance entry is appended to ``image_sources.json``
    (the credit source of truth) and the row's status flips to ``Sourced``.
    A row that exhausts the provider/stage chain becomes ``Needs-Manual``
    (terminal). Status is written back after each completion, so an interrupt
    preserves finished rows. Returns ``(sourced, needs_manual, skipped)``.
    """
    items = manifest["items"]
    pending_idx = [
        i for i, it in enumerate(items)
        if it["status"] in SEARCH_RETRYABLE_STATUSES
    ]
    total = len(pending_idx)
    skipped = len(items) - total

    if total == 0:
        print(
            f"[Batch] Nothing to do — all {len(items)} row(s) already in a "
            "terminal state (Sourced / Needs-Manual)."
        )
        return 0, 0, skipped

    print(
        f"\n[Batch] {total} row(s) to search, {skipped} already done. "
        f"concurrency={concurrency}\n"
    )

    sourced_count = 0
    needs_manual_count = 0
    write_lock = threading.Lock()

    def _one(idx: int):
        try:
            manifest_item, error = _search_one_item(
                items[idx],
                output_dir=output_dir,
                save_candidates=save_candidates,
                max_candidates=max_candidates,
                default_provider=default_provider,
                default_strict=default_strict,
                default_min_width=default_min_width,
                default_min_height=default_min_height,
            )
            return idx, manifest_item, error
        except Exception as exc:  # noqa: BLE001 — provider code raises freely
            return idx, None, str(exc)[:500]

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(_one, i) for i in pending_idx]
        for fut in concurrent.futures.as_completed(futures):
            idx, manifest_item, error = fut.result()
            item = items[idx]
            with write_lock:
                if manifest_item is not None:
                    write_sources_manifest(sources_manifest_path, manifest_item)
                    item["status"] = SEARCH_STATUS_SOURCED
                    item["provider"] = manifest_item.get("provider", "")
                    item["license_tier"] = manifest_item.get("license_tier", "")
                    item.pop("last_error", None)
                    sourced_count += 1
                    print(f"  [OK]   {item['filename']} ({item['provider']})")
                else:
                    item["status"] = SEARCH_STATUS_NEEDS_MANUAL
                    item["last_error"] = error or "search failed"
                    needs_manual_count += 1
                    print(f"  [MANUAL] {item['filename']} — {item['last_error']}")
                save_search_manifest(manifest_path, manifest)

    print(
        f"\n[Batch] Done: {sourced_count} sourced / {needs_manual_count} "
        f"needs-manual ({skipped} pre-skipped). Manifest: {manifest_path}"
    )
    return sourced_count, needs_manual_count, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search openly-licensed web images and download a single best match. "
            "Sister to image_gen.py."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Search query (2-5 keywords work best). Omit in --batch mode.",
    )
    parser.add_argument(
        "--filename",
        default=None,
        help=(
            "Local filename for the chosen image (e.g. cover_bg.jpg). "
            "Required for single-query, --promote, and --from-url modes; "
            "ignored in --batch."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory. Manifest defaults to <output>/image_sources.json.",
    )
    parser.add_argument(
        "--provider",
        choices=ALL_PROVIDERS,
        default=None,
        help=(
            "Pin one provider. Default: try zero-config providers (openverse, "
            "wikimedia) plus any keyed provider whose API key is set."
        ),
    )
    parser.add_argument(
        "--orientation",
        choices=ORIENTATION_CHOICES,
        default="any",
        help="Preferred orientation.",
    )
    parser.add_argument(
        "--purpose",
        default="",
        help="Purpose tag stored in the manifest (e.g. background, hero, side).",
    )
    parser.add_argument(
        "--slide",
        default="",
        help="Slide identifier the image belongs to (e.g. 01_cover).",
    )
    parser.add_argument(
        "--strict-no-attribution",
        action="store_true",
        help=(
            "Refuse CC BY / CC BY-SA results. If no attribution-free match is "
            "downloadable, exit non-zero."
        ),
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=1200,
        help="Minimum acceptable image width in pixels (default: 1200).",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=800,
        help="Minimum acceptable image height in pixels (default: 800).",
    )
    parser.add_argument(
        "--require-terms",
        action="append",
        default=None,
        metavar="TERM[,TERM...]",
        help=(
            "Entity-safety gate: require each metadata term group before a "
            "candidate can be accepted. Repeatable; comma separates groups; "
            "'A|B' means aliases within one group. Example: "
            "--require-terms Chongqing --require-terms 'Jiefangbei|Liberation Monument'."
        ),
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Override manifest path. Defaults to <output>/image_sources.json.",
    )
    parser.add_argument(
        "--batch",
        default=None,
        metavar="QUERIES_JSON",
        help=(
            "Process a batch of search requests from an image_queries.json "
            "manifest concurrently, writing provenance into image_sources.json "
            "and status back into the queries manifest."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help=(
            "Max concurrent searches in --batch mode. Defaults to "
            f"IMAGE_SEARCH_CONCURRENCY env or {DEFAULT_SEARCH_CONCURRENCY}. "
            "Keep modest — free providers are rate-sensitive; use 1 for "
            "strict one-at-a-time pacing."
        ),
    )
    parser.add_argument(
        "--save-candidates",
        action="store_true",
        help=(
            "Opt-in: also save a small candidate pool to candidates/<stem>/ "
            "(with downscaled review copies) so a better fit can be promoted "
            "when the best match fails visual confirmation. Default: only the "
            "best match is downloaded."
        ),
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=4,
        help="Max candidates to save when --save-candidates is set (default: 4).",
    )
    parser.add_argument(
        "--promote",
        default=None,
        metavar="CANDIDATE_FILE",
        help=(
            "Promote a candidate to replace the primary image. "
            "Example: --promote candidate_03.jpg --filename 05_wulong.jpg -o images/"
        ),
    )
    parser.add_argument(
        "--from-url",
        default=None,
        metavar="URL",
        help=(
            "Manual replacement: download a user-supplied image URL into "
            "--filename and record it (license marked 'manual'). Works without "
            "a multimodal model. Example: --from-url https://… --filename team.jpg -o images/"
        ),
    )
    return parser


def _default_provider_chain() -> list[str]:
    """Keyed high-quality providers first; zero-config providers as fallback.
    This is the search order when ``--provider`` is unset."""
    chain: list[str] = []
    if os.environ.get("PEXELS_API_KEY"):
        chain.append("pexels")
    if os.environ.get("PIXABAY_API_KEY"):
        chain.append("pixabay")
    chain.extend(ZERO_CONFIG_PROVIDERS)
    return chain


def main(argv: Optional[list[str]] = None) -> int:
    _load_search_env_file()

    parser = build_parser()
    args = parser.parse_args(argv)

    output_dir = Path(args.output)

    # --- Promote mode ---
    if args.promote:
        if not args.filename:
            parser.error("--filename is required in --promote mode")
        return promote_candidate(
            output_dir,
            args.filename,
            args.promote,
            manifest_path=Path(args.manifest) if args.manifest else None,
        )

    # --- Manual URL replacement ---
    if args.from_url:
        if not args.filename:
            parser.error("--filename is required with --from-url")
        return fetch_url_replace(
            output_dir,
            args.filename,
            args.from_url,
            manifest_path=Path(args.manifest) if args.manifest else None,
            slide=args.slide,
            purpose=args.purpose,
            search_query=args.query or "",
            orientation="" if args.orientation == "any" else args.orientation,
            required_terms=_parse_required_terms(args.require_terms),
        )

    # --- Batch mode ---
    if args.batch:
        if not os.path.isfile(args.batch):
            print(f"Error: queries manifest not found: {args.batch}", file=sys.stderr)
            return 1
        try:
            manifest = load_search_manifest(args.batch)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        batch_output_dir = (
            output_dir if args.output != "." else Path(args.batch).parent
        )
        batch_output_dir.mkdir(parents=True, exist_ok=True)
        sources_manifest_path = (
            Path(args.manifest) if args.manifest
            else default_manifest_path(str(batch_output_dir))
        )
        try:
            _, needs_manual, _ = run_search_manifest(
                manifest,
                args.batch,
                output_dir=batch_output_dir,
                sources_manifest_path=sources_manifest_path,
                concurrency=_resolve_search_concurrency(args.concurrency),
                save_candidates=args.save_candidates,
                max_candidates=args.max_candidates,
                default_provider=args.provider,
                default_strict=args.strict_no_attribution,
                default_min_width=args.min_width,
                default_min_height=args.min_height,
            )
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Partial progress preserved in manifest.")
            return 130
        # Mirror image_gen.py: a non-zero code flags rows that need manual
        # attention. It is a signal, not a halt — the workflow (image-base.md
        # §6) surfaces Needs-Manual rows and continues regardless.
        return 1 if needs_manual else 0

    # --- Single-query search mode ---
    if not args.query:
        parser.error("query is required unless --batch, --promote, or --from-url is used")
    if not args.filename:
        parser.error("--filename is required in single-query mode")

    request = ImageSearchRequest(
        query=args.query,
        purpose=args.purpose,
        orientation="" if args.orientation == "any" else args.orientation,
        filename=args.filename,
        slide=args.slide,
        min_width=args.min_width,
        min_height=args.min_height,
        required_terms=_parse_required_terms(args.require_terms),
    )
    _warn_weak_required_terms(request.required_terms)

    providers = [args.provider] if args.provider else _default_provider_chain()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.filename

    print(f"Searching providers: {', '.join(providers)}", file=sys.stderr)
    candidate, provider_name, stage = search_and_download(
        providers,
        request,
        output_path=output_path,
        strict_no_attribution=args.strict_no_attribution,
        save_candidates=args.save_candidates,
        max_candidates=args.max_candidates,
    )

    if candidate is None:
        print(
            "No acceptable candidates could be downloaded across all "
            "providers/filters. Try a shorter query, use default attribution "
            "mode if strict mode is enabled, or set an API key for a keyed provider.",
            file=sys.stderr,
        )
        return 1

    print(
        f"  picked: {candidate.title!r} from {provider_name} "
        f"({candidate.license_name or 'no license string'}, "
        f"{candidate.license_tier})",
        file=sys.stderr,
    )

    # Measure what was actually written to disk; upstream metadata can be
    # off (e.g. Openverse aggregates rawpixel which only exposes previews).
    actual_dimensions = _measure_actual_image(output_path)
    if (
        actual_dimensions is not None
        and candidate.width
        and candidate.height
        and actual_dimensions[0] * actual_dimensions[1]
        < 0.5 * candidate.width * candidate.height
    ):
        print(
            f"\n[!] Downloaded image is much smaller than upstream metadata "
            f"({actual_dimensions[0]}x{actual_dimensions[1]} vs "
            f"{candidate.width}x{candidate.height}). The provider likely "
            f"only exposes a preview here. Layout based on the manifest's "
            f"width/height will be accurate; the metadata_dimensions field "
            f"is preserved for reference.",
            file=sys.stderr,
        )

    item = _candidate_to_manifest_item(
        candidate,
        args,
        provider_name=provider_name,
        stage=stage,
        actual_dimensions=actual_dimensions,
    )
    manifest_path = Path(args.manifest) if args.manifest else default_manifest_path(args.output)
    write_sources_manifest(manifest_path, item)
    print(f"  manifest: {manifest_path}", file=sys.stderr)

    if candidate.license_tier == "attribution-required":
        print(
            "\n[!] This image requires on-slide attribution. "
            "Executor should add a small credit element to the slide using "
            "the 'attribution_text' field in the manifest.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
