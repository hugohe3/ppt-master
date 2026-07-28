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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

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
SEARCH_FAILURE_NO_MATCH = "no-match"
SEARCH_FAILURE_RETRYABLE = "retryable"

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


@dataclass
class SearchDownloadResult:
    """Carry one search result without collapsing no-match and retryable failures."""

    candidate: Optional[AssetCandidate] = None
    provider_name: Optional[str] = None
    stage: Optional[str] = None
    actual_dimensions: Optional[tuple[int, int]] = None
    staged_path: Optional[Path] = None
    output_path: Optional[Path] = None
    failure_kind: Optional[str] = None
    error: Optional[str] = None


class DownloadQualityError(ValueError):
    """Signal a readable candidate that fails the requested image contract."""


def _is_pillow_decompression_error(exc: BaseException) -> bool:
    """Recognize Pillow's safety exception without making Pillow a hard import."""
    cls = type(exc)
    return (
        cls.__name__ == "DecompressionBombError"
        and cls.__module__.startswith("PIL.")
    )


def _is_recoverable_image_error(exc: BaseException) -> bool:
    """Return whether a provider/download/image failure can be reported cleanly."""
    return isinstance(
        exc,
        (
            requests.RequestException,
            OSError,
            RuntimeError,
            SyntaxError,
            ValueError,
        ),
    ) or _is_pillow_decompression_error(exc)


def _try_provider(
    name: str,
    request: ImageSearchRequest,
    license_tier_filter: str,
) -> tuple[Optional[list[AssetCandidate]], Optional[str]]:
    """Run one provider while preserving whether it errored or returned no rows."""
    try:
        module = _load_provider(name)
        return module.search(request, license_tier_filter=license_tier_filter), None
    except RuntimeError as exc:
        if _is_keyed_provider_unconfigured(name, exc):
            print(
                f"  [{name}] skipped: {exc}",
                file=sys.stderr,
            )
            return None, None
        else:
            print(f"  [{name}] error: {exc}", file=sys.stderr)
        return None, f"{name}: {exc}"
    except (requests.RequestException, OSError, ValueError) as exc:
        print(f"  [{name}] error: {exc}", file=sys.stderr)
        return None, f"{name}: {exc}"
    except ImportError as exc:
        print(f"  [{name}] error: {exc}", file=sys.stderr)
        return None, f"{name}: provider import failed: {exc}"


# ---------------------------------------------------------------------------
# Post-download quality validation
# ---------------------------------------------------------------------------

_MIN_DOWNLOAD_PIXELS = 800 * 600  # preserve the existing absolute thumbnail floor


def _validate_downloaded_quality(
    path: Path,
    *,
    min_width: int = 0,
    min_height: int = 0,
    enforce_thumbnail_floor: bool = True,
) -> bool:
    """Reject unreadable images and actual EXIF-oriented dimensions below contract.

    Upstream metadata can be inaccurate (e.g. Openverse aggregates rawpixel
    which only exposes a preview). This function checks what was actually
    written to disk. Automated paths also reject thumbnails/previews; explicit
    manual paths may disable that absolute floor while retaining their own
    requested dimensions.
    """
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required to validate downloaded image dimensions. "
            "Install it with: pip install Pillow"
        ) from exc
    try:
        with Image.open(path) as im:
            oriented = ImageOps.exif_transpose(im)
            oriented.load()
            w, h = oriented.size
            if oriented is not im:
                oriented.close()
            if w < min_width or h < min_height:
                print(
                    f"    rejected: downloaded image dimensions {w}x{h} are below "
                    f"the requested minimum {min_width}x{min_height}",
                    file=sys.stderr,
                )
                return False
            if enforce_thumbnail_floor and w * h < _MIN_DOWNLOAD_PIXELS:
                print(
                    f"    rejected: downloaded image too small "
                    f"({w}x{h} = {w*h:,} px < {_MIN_DOWNLOAD_PIXELS:,} px minimum)",
                    file=sys.stderr,
                )
                return False
            return True
    except Exception as exc:
        if not _is_recoverable_image_error(exc):
            raise
        print(
            f"    rejected: downloaded file is not a readable image ({exc})",
            file=sys.stderr,
        )
        return False


def _stage_validated_image(
    url: str,
    output_path: Path,
    *,
    min_width: int,
    min_height: int,
    enforce_thumbnail_floor: bool = True,
) -> tuple[Path, tuple[int, int]]:
    """Download and validate beside the target without changing the canonical."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}.",
        suffix=output_path.suffix,
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    keep_temp = False
    try:
        download_image(
            url,
            str(temp_path),
            headers={"User-Agent": USER_AGENT},
        )
        if not _validate_downloaded_quality(
            temp_path,
            min_width=min_width,
            min_height=min_height,
            enforce_thumbnail_floor=enforce_thumbnail_floor,
        ):
            raise DownloadQualityError(
                "downloaded image did not satisfy the requested dimensions/readability"
            )
        actual_dimensions = _measure_actual_image(temp_path)
        if actual_dimensions is None:
            raise DownloadQualityError(
                "downloaded image dimensions could not be measured"
            )
        keep_temp = True
        return temp_path, actual_dimensions
    finally:
        if not keep_temp:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _commit_staged_image(
    staged_path: Path,
    target_path: Path,
    manifest_writer: Callable[[], Path],
) -> Path:
    """Install a staged image and roll it back if provenance cannot be written."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path: Optional[Path] = None
    installed = False

    try:
        if target_path.exists():
            if not target_path.is_file():
                raise RuntimeError(
                    f"image target exists but is not a regular file: {target_path}"
                )
            fd, backup_name = tempfile.mkstemp(
                prefix=f".{target_path.stem}.backup.",
                suffix=target_path.suffix,
                dir=str(target_path.parent),
            )
            os.close(fd)
            reserved_backup_path = Path(backup_name)
            reserved_backup_path.unlink()
            os.replace(target_path, reserved_backup_path)
            backup_path = reserved_backup_path

        os.replace(staged_path, target_path)
        installed = True
        written = manifest_writer()
    except Exception as exc:
        rollback_errors: list[str] = []
        if installed:
            try:
                target_path.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"cannot remove new target: {rollback_exc}")
        if backup_path is not None and backup_path.exists():
            try:
                os.replace(backup_path, target_path)
            except OSError as rollback_exc:
                rollback_errors.append(f"cannot restore prior target: {rollback_exc}")
        if rollback_errors:
            raise RuntimeError(
                f"{exc}; image rollback also failed: {'; '.join(rollback_errors)}"
            ) from exc
        raise
    else:
        if backup_path is not None:
            try:
                backup_path.unlink(missing_ok=True)
            except OSError as exc:
                print(
                    f"  warning: could not remove image backup {backup_path}: {exc}",
                    file=sys.stderr,
                )
        return written
    finally:
        try:
            staged_path.unlink(missing_ok=True)
        except OSError:
            pass


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
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        return None
    review_path: Optional[Path] = None
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        review_path = dest_dir / f"{Path(name).stem}.jpg"
        with Image.open(src) as im:
            oriented = ImageOps.exif_transpose(im)
            review = oriented.convert("RGB")
            review.thumbnail((max_side, max_side))
            review.save(review_path, "JPEG", quality=85)
            review.close()
            if oriented is not im:
                oriented.close()
        return review_path
    except Exception as exc:
        if not _is_recoverable_image_error(exc):
            raise
        if review_path is not None:
            try:
                review_path.unlink(missing_ok=True)
            except OSError:
                pass
        return None


def _save_candidates_pool(
    ranked: list[tuple[float, str, AssetCandidate]],
    output_dir: Path,
    stem: str,
    selected_filename: str,
    min_width: int,
    min_height: int,
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
        keep_candidate = False
        try:
            download_image(
                candidate.download_url,
                str(cand_path),
                headers={"User-Agent": USER_AGENT},
            )
            if not _validate_downloaded_quality(
                cand_path,
                min_width=min_width,
                min_height=min_height,
            ):
                continue
            actual_dim = _measure_actual_image(cand_path)
            review_path = _write_review_copy(
                cand_path,
                cand_dir / "review",
                cand_filename,
            )
            idx += 1
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
                "attribution_required": (
                    candidate.license_tier == "attribution-required"
                ),
                "attribution_text": build_attribution_text(
                    selected_filename,
                    candidate,
                ),
                "width": actual_dim[0] if actual_dim else candidate.width,
                "height": actual_dim[1] if actual_dim else candidate.height,
            })
            keep_candidate = True
        except Exception as exc:
            if not _is_recoverable_image_error(exc):
                raise
            continue
        finally:
            if not keep_candidate:
                try:
                    cand_path.unlink(missing_ok=True)
                except OSError:
                    pass

    if pool:
        meta = {
            "target_filename": selected_filename,
            "selected": pool[0]["filename"],
            "searched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "candidates": pool,
        }
        meta_path = cand_dir / "candidates.json"
        _write_json_atomic(meta_path, meta)
        print(f"  candidates: {cand_dir}/ ({len(pool)} saved)", file=sys.stderr)


def search_and_download(
    providers: list[str],
    request: ImageSearchRequest,
    *,
    output_path: Path,
    strict_no_attribution: bool,
    save_candidates: bool = False,
    max_candidates: int = 4,
) -> SearchDownloadResult:
    """Find a candidate AND successfully download it.

    By default only the best match is downloaded. When ``save_candidates``
    is True (opt-in), the top-N candidates are also saved to
    ``candidates/<stem>/`` so the agent can review and ``--promote`` a
    better fit when the best match does not pass visual confirmation.

    Returns a structured result so batch mode can keep transient/provider
    failures retryable while treating a complete no-match as terminal.
    """
    license_filters: list[str] = (
        ["no-attribution-only"] if strict_no_attribution else ["all"]
    )

    provider_errors: list[str] = []
    download_errors: list[str] = []
    quality_rejections = 0

    for stage in license_filters:
        ranked: list[tuple[float, str, AssetCandidate]] = []
        for provider_name in providers:
            print(f"  -> trying {provider_name} ({stage}) ...", file=sys.stderr)
            candidates, provider_error = _try_provider(provider_name, request, stage)
            if provider_error:
                provider_errors.append(provider_error)
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
            try:
                _save_candidates_pool(
                    sorted_ranked,
                    output_path.parent,
                    stem,
                    output_path.name,
                    request.min_width,
                    request.min_height,
                    max_candidates=max_candidates,
                )
            except Exception as exc:
                if not _is_recoverable_image_error(exc):
                    raise
                print(
                    f"  warning: candidate pool could not be saved: {exc}",
                    file=sys.stderr,
                )

        # --- Pick the best downloadable candidate ---
        for _score, provider_name, candidate in sorted_ranked:
            # If candidates were already saved, the file may already
            # exist in the candidates dir — but we still need the
            # primary copy at output_path.
            try:
                staged_path, actual_dimensions = _stage_validated_image(
                    candidate.download_url,
                    output_path,
                    min_width=request.min_width,
                    min_height=request.min_height,
                )
                return SearchDownloadResult(
                    candidate=candidate,
                    provider_name=provider_name,
                    stage=stage,
                    actual_dimensions=actual_dimensions,
                    staged_path=staged_path,
                    output_path=output_path,
                )
            except DownloadQualityError:
                quality_rejections += 1
                continue
            except Exception as exc:
                if not _is_recoverable_image_error(exc):
                    raise
                print(
                    f"    download failed for {candidate.title!r}: {exc}",
                    file=sys.stderr,
                )
                download_errors.append(f"{provider_name}/{candidate.title}: {exc}")
                continue

    retryable_errors = provider_errors + download_errors
    if retryable_errors:
        return SearchDownloadResult(
            failure_kind=SEARCH_FAILURE_RETRYABLE,
            error="; ".join(retryable_errors)[:500],
        )

    detail = "no acceptable candidate across all providers/stages"
    if quality_rejections:
        detail += f" ({quality_rejections} candidate(s) failed actual-size/readability gates)"
    return SearchDownloadResult(
        failure_kind=SEARCH_FAILURE_NO_MATCH,
        error=detail,
    )


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def default_manifest_path(output_dir: str) -> Path:
    return Path(output_dir) / "image_sources.json"


def _validate_bare_filename(value: str, *, field_name: str = "filename") -> str:
    """Require a bare filename with no absolute or parent path components."""
    if (
        not value.strip()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or ":" in value
        or Path(value).is_absolute()
    ):
        raise ValueError(
            f"{field_name} must be a bare filename without path components: {value!r}"
        )
    return value


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
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            oriented = ImageOps.exif_transpose(im)
            try:
                return int(oriented.width), int(oriented.height)
            finally:
                if oriented is not im:
                    oriented.close()
    except Exception as exc:
        if not _is_recoverable_image_error(exc):
            raise
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
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"existing image sources manifest is unreadable: {path} ({exc}); "
            "repair or restore it before continuing"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"existing image sources manifest must be a JSON object: {path}"
        )
    items = payload.get("items")
    if not isinstance(items, list):
        raise RuntimeError(
            f"existing image sources manifest must contain an 'items' array: {path}"
        )
    if any(not isinstance(item, dict) for item in items):
        raise RuntimeError(
            f"existing image sources manifest contains a non-object item: {path}"
        )
    seen_filenames: dict[str, str] = {}
    for index, item in enumerate(items):
        filename = item.get("filename")
        if not isinstance(filename, str):
            raise RuntimeError(
                f"existing image sources manifest items[{index}].filename "
                f"must be a non-empty bare filename: {path}"
            )
        try:
            _validate_bare_filename(filename)
        except ValueError as exc:
            raise RuntimeError(
                f"existing image sources manifest items[{index}]: {exc}: {path}"
            ) from exc
        normalized_filename = filename.casefold()
        if normalized_filename in seen_filenames:
            raise RuntimeError(
                f"existing image sources manifest filename {filename!r} conflicts "
                f"with {seen_filenames[normalized_filename]!r} "
                f"(case-insensitive): {path}"
            )
        seen_filenames[normalized_filename] = filename
    return payload


def _write_json_atomic(path: str | Path, payload: dict) -> Path:
    """Write JSON through a same-directory temporary file and atomic rename."""
    target = ensure_json_parent(path)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.stem + ".", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target


def write_sources_manifest(path: Path, item: dict) -> Path:
    """Append ``item`` to the manifest at ``path``, replacing any prior
    entry that targets the same filename."""
    manifest_path = Path(path)
    payload = _read_existing_manifest(manifest_path)
    filename = item.get("filename")
    if not isinstance(filename, str):
        raise RuntimeError("new image source item requires a string filename")
    try:
        _validate_bare_filename(filename)
    except ValueError as exc:
        raise RuntimeError(f"new image source item: {exc}") from exc

    items: list[dict] = list(payload.get("items") or [])
    normalized_filename = filename.casefold()
    differently_cased = next(
        (
            existing["filename"]
            for existing in items
            if isinstance(existing.get("filename"), str)
            and existing["filename"].casefold() == normalized_filename
            and existing["filename"] != filename
        ),
        None,
    )
    if differently_cased is not None:
        raise RuntimeError(
            f"new image source filename {filename!r} conflicts with existing "
            f"{differently_cased!r} (case-insensitive)"
        )
    items = [
        i
        for i in items
        if not isinstance(i.get("filename"), str)
        or i["filename"].casefold() != normalized_filename
    ]
    items.append(item)

    payload["items"] = items
    payload["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload.setdefault(
        "license_verification",
        "provider metadata used; manual review recommended for external delivery",
    )

    return _write_json_atomic(manifest_path, payload)


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
        1. Stage and validate ``candidates/<stem>/<candidate_filename>``
        2. Replace the canonical image and its provenance as one rollback unit
        3. Advance ``candidates.json`` only after provenance succeeds
    """
    import shutil

    target_filename = _validate_bare_filename(
        target_filename, field_name="target filename"
    )
    candidate_filename = _validate_bare_filename(
        candidate_filename, field_name="candidate filename"
    )
    mpath = manifest_path or default_manifest_path(str(output_dir))
    try:
        manifest = _read_existing_manifest(mpath)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    stem = Path(target_filename).stem
    cand_dir = output_dir / "candidates" / stem
    cand_meta_path = cand_dir / "candidates.json"

    if not cand_meta_path.is_file():
        print(f"Error: {cand_meta_path} not found.", file=sys.stderr)
        return 1

    try:
        meta = json.loads(cand_meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: cannot read {cand_meta_path}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(meta, dict) or not isinstance(meta.get("candidates"), list):
        print(
            f"Error: {cand_meta_path} must contain a candidates array.",
            file=sys.stderr,
        )
        return 1
    candidates = meta.get("candidates", [])

    entry = next(
        (
            candidate
            for candidate in candidates
            if isinstance(candidate, dict)
            and candidate.get("filename") == candidate_filename
        ),
        None,
    )
    if entry is None:
        names = [
            str(candidate.get("filename"))
            for candidate in candidates
            if isinstance(candidate, dict) and candidate.get("filename")
        ]
        print(
            f"Error: '{candidate_filename}' not found. Available: {', '.join(names)}",
            file=sys.stderr,
        )
        return 1

    src_path = cand_dir / candidate_filename
    dst_path = output_dir / target_filename
    if not src_path.is_file():
        print(f"Error: {src_path} does not exist on disk.", file=sys.stderr)
        return 1

    items: list[dict] = list(manifest.get("items") or [])
    target_item: Optional[dict] = None
    for item in items:
        filename = item.get("filename")
        if (
            isinstance(filename, str)
            and filename.casefold() == target_filename.casefold()
        ):
            target_item = item
            break
    if target_item is None:
        print(
            f"Error: {mpath} has no provenance entry for {target_filename!r}.",
            file=sys.stderr,
        )
        return 1
    if target_item["filename"] != target_filename:
        print(
            f"Error: target filename casing {target_filename!r} conflicts with "
            f"provenance filename {target_item['filename']!r}.",
            file=sys.stderr,
        )
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    fd, staged_name = tempfile.mkstemp(
        prefix=f".{dst_path.stem}.promote.",
        suffix=dst_path.suffix,
        dir=str(dst_path.parent),
    )
    os.close(fd)
    staged_path = Path(staged_name)
    try:
        shutil.copy2(src_path, staged_path)
        if not _validate_downloaded_quality(
            staged_path,
            enforce_thumbnail_floor=False,
        ):
            raise DownloadQualityError(
                "candidate image did not satisfy the readability/size gate"
            )
        actual_dim = _measure_actual_image(staged_path)
        if actual_dim is None:
            raise DownloadQualityError("candidate dimensions could not be measured")
        w, h = actual_dim
        if w < 1 or h < 1:
            raise DownloadQualityError("candidate dimensions must be positive")
        if w * h < _MIN_DOWNLOAD_PIXELS:
            print(
                f"  warning: explicitly promoted image is low resolution ({w}x{h})",
                file=sys.stderr,
            )

        target_item["provider"] = entry.get("provider", "")
        target_item["title"] = entry.get("title", "")
        target_item["author"] = entry.get("author", "")
        target_item["source_page_url"] = entry.get("source_page_url", "")
        target_item["download_url"] = entry.get("download_url", "")
        target_item["license_name"] = entry.get("license_name", "")
        target_item["license_url"] = entry.get("license_url", "")
        target_item["license_tier"] = entry.get("license_tier", "")
        target_item["attribution_required"] = entry.get(
            "attribution_required",
            False,
        )
        # Recompute the credit from the promoted candidate — never carry the
        # replaced image's attribution_text (wrong author/title/source).
        target_item["attribution_text"] = build_attribution_text(
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
        target_item["width"] = w
        target_item["height"] = h
        target_item.pop("metadata_dimensions", None)
        target_item["status"] = "promoted"
        manifest["items"] = items
        manifest["generated_at"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        _commit_staged_image(
            staged_path,
            dst_path,
            lambda: _write_json_atomic(mpath, manifest),
        )
    except Exception as exc:
        if not _is_recoverable_image_error(exc):
            raise
        print(f"Error: candidate promotion failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            staged_path.unlink(missing_ok=True)
        except OSError:
            pass

    print(f"  promoted: {candidate_filename} → {target_filename}", file=sys.stderr)
    print(f"  manifest updated: {mpath}", file=sys.stderr)

    # The selection marker must never move ahead of canonical provenance.
    meta["selected"] = candidate_filename
    try:
        _write_json_atomic(cand_meta_path, meta)
    except OSError as exc:
        print(
            f"Error: image was promoted, but {cand_meta_path} could not be updated: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1

    review = _write_review_copy(dst_path, output_dir / ".review", target_filename)
    if review is not None:
        print(f"  review copy: {review}", file=sys.stderr)
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
    min_width: int = 1200,
    min_height: int = 800,
) -> int:
    """Download a user-supplied image URL into the target and record it.

    The model-agnostic manual path: when an automated best match is not
    suitable (or the running model cannot see images at all), a human finds a
    good image, passes its URL, and it replaces the target. License is unknown
    for an arbitrary URL, so the manifest marks it ``manual`` and notes that
    verifying usage rights is the user's responsibility.
    """
    target_filename = _validate_bare_filename(
        target_filename, field_name="target filename"
    )
    mpath = manifest_path or default_manifest_path(str(output_dir))
    try:
        existing_manifest = _read_existing_manifest(mpath)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    prior = next(
        (
            item
            for item in existing_manifest.get("items", [])
            if isinstance(item.get("filename"), str)
            and item["filename"].casefold() == target_filename.casefold()
        ),
        {},
    )
    if prior and prior["filename"] != target_filename:
        print(
            f"Error: target filename casing {target_filename!r} conflicts with "
            f"provenance filename {prior['filename']!r}.",
            file=sys.stderr,
        )
        return 1
    try:
        inherited_required_terms = _parse_required_terms(
            prior.get("required_terms")
        )
    except ValueError as exc:
        print(
            f"Error: existing provenance has invalid required_terms: {exc}",
            file=sys.stderr,
        )
        return 1
    final_required_terms = inherited_required_terms or required_terms

    output_dir.mkdir(parents=True, exist_ok=True)
    dst_path = output_dir / target_filename
    try:
        staged_path, actual_dim = _stage_validated_image(
            url,
            dst_path,
            min_width=min_width,
            min_height=min_height,
            enforce_thumbnail_floor=False,
        )
    except (
        DownloadQualityError,
        requests.RequestException,
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(f"Error: failed to download {url}: {exc}", file=sys.stderr)
        return 1

    # Inherit page context (which slide / purpose / query this image serves)
    # from the entry being replaced; override only source / license / size /
    # status so the audit trail survives a manual swap.
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
        "width": actual_dim[0],
        "height": actual_dim[1],
        "attribution_text": "",
        "status": "manual",
        "note": (
            "Manually supplied image URL; verifying usage rights is the user's "
            "responsibility."
        ),
    }
    if final_required_terms:
        item["required_terms"] = list(final_required_terms)

    try:
        written = _commit_staged_image(
            staged_path,
            dst_path,
            lambda: write_sources_manifest(mpath, item),
        )
    except (
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(
            f"Error: failed to replace {target_filename} and record provenance: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        try:
            staged_path.unlink(missing_ok=True)
        except OSError:
            pass

    print(f"  fetched: {url} -> {target_filename}", file=sys.stderr)
    print(f"  manifest updated: {written}", file=sys.stderr)
    review = _write_review_copy(dst_path, output_dir / ".review", target_filename)
    if review is not None:
        print(f"  review copy: {review}", file=sys.stderr)
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
    except OSError as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc
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

    seen_filenames: dict[str, str] = {}
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
        for dimension_field in ("min_width", "min_height"):
            if dimension_field not in item:
                continue
            value = item[dimension_field]
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise ValueError(
                    f"{prefix} field '{dimension_field}' must be a positive integer"
                )
        fname = item["filename"]
        try:
            _validate_bare_filename(fname)
        except ValueError as exc:
            raise ValueError(f"{prefix} {exc}") from exc
        normalized_filename = fname.casefold()
        if normalized_filename in seen_filenames:
            raise ValueError(
                f"{prefix} filename {fname!r} conflicts with "
                f"{seen_filenames[normalized_filename]!r} (case-insensitive)"
            )
        seen_filenames[normalized_filename] = fname

    return data


def save_search_manifest(path: str, data: dict) -> None:
    """Atomically write the batch manifest back (tmp file + rename)."""
    try:
        _write_json_atomic(path, data)
    except OSError as exc:
        raise RuntimeError(
            f"cannot update image query manifest {path}: {exc}"
        ) from exc


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
) -> tuple[
    Optional[dict],
    Optional[str],
    bool,
    Optional[Path],
    Optional[Path],
]:
    """Run the full search + download for one batch item (thread worker).

    Returns ``(manifest_item, error, retryable, staged_path, output_path)``.
    Only network and staged-file work happens here; canonical replacement and
    all manifest writes are serialized by the caller.
    """
    filename = _validate_bare_filename(item["filename"])
    orientation = item.get("orientation", "any") or "any"
    strict = bool(item.get("strict_no_attribution", default_strict))
    required_terms = _parse_required_terms(item.get("required_terms"))
    _warn_weak_required_terms(required_terms)
    request = ImageSearchRequest(
        query=item["query"],
        purpose=item.get("purpose", ""),
        orientation="" if orientation == "any" else orientation,
        filename=filename,
        slide=item.get("slide", ""),
        min_width=int(item.get("min_width", default_min_width)),
        min_height=int(item.get("min_height", default_min_height)),
        required_terms=required_terms,
    )

    pinned = item.get("provider") or default_provider
    providers = [pinned] if pinned else _default_provider_chain()
    output_path = output_dir / filename

    result = search_and_download(
        providers,
        request,
        output_path=output_path,
        strict_no_attribution=strict,
        save_candidates=save_candidates,
        max_candidates=max_candidates,
    )
    if result.candidate is None:
        return (
            None,
            result.error or "search failed",
            result.failure_kind == SEARCH_FAILURE_RETRYABLE,
            None,
            None,
        )
    if result.staged_path is None or result.output_path is None:
        return (
            None,
            "search succeeded without a staged output",
            True,
            None,
            None,
        )

    try:
        item_args = argparse.Namespace(
            filename=filename,
            slide=item.get("slide", ""),
            purpose=item.get("purpose", ""),
            query=item["query"],
            orientation=orientation,
            required_terms=request.required_terms,
        )
        manifest_item = _candidate_to_manifest_item(
            result.candidate,
            item_args,
            provider_name=result.provider_name or "",
            stage=result.stage or "",
            actual_dimensions=result.actual_dimensions,
        )
        return (
            manifest_item,
            None,
            False,
            result.staged_path,
            result.output_path,
        )
    except Exception:
        if result.staged_path is not None:
            try:
                result.staged_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


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
) -> tuple[int, int, int, int]:
    """Process all Pending/Failed rows concurrently with a bounded pool.

    On success the rich provenance entry is appended to ``image_sources.json``
    (the credit source of truth) and the row's status flips to ``Sourced``.
    A row that exhausts the provider/stage chain becomes ``Needs-Manual``
    (terminal). Status is written back after each completion, so an interrupt
    preserves finished rows. Returns ``(sourced, needs_manual, failed, skipped)``.
    """
    sources_manifest = _read_existing_manifest(sources_manifest_path)
    items = manifest["items"]

    provenance_filenames = {
        item["filename"].casefold(): item["filename"]
        for item in sources_manifest.get("items", [])
        if isinstance(item.get("filename"), str)
    }
    repaired_sourced = False
    for item in items:
        if item["status"] != SEARCH_STATUS_SOURCED:
            continue
        filename = item["filename"]
        target_path = output_dir / filename
        reasons: list[str] = []
        provenance_filename = provenance_filenames.get(filename.casefold())
        if provenance_filename is None:
            reasons.append("image_sources.json has no matching provenance entry")
        elif provenance_filename != filename:
            reasons.append(
                "image_sources.json filename casing does not match "
                f"({provenance_filename!r} vs {filename!r})"
            )
        if not target_path.is_file():
            reasons.append("target file is missing")
        else:
            min_width = int(item.get("min_width", default_min_width))
            min_height = int(item.get("min_height", default_min_height))
            try:
                target_is_valid = _validate_downloaded_quality(
                    target_path,
                    min_width=min_width,
                    min_height=min_height,
                )
            except RuntimeError as exc:
                reasons.append(f"target validation unavailable: {exc}")
            else:
                if not target_is_valid:
                    reasons.append(
                        "target file is unreadable or below requested dimensions"
                    )
        if reasons:
            item["status"] = SEARCH_STATUS_FAILED
            item["last_error"] = (
                "Sourced state validation failed: " + "; ".join(reasons)
            )[:500]
            repaired_sourced = True
            print(f"  [RETRY] {filename} — {item['last_error']}")
    if repaired_sourced:
        save_search_manifest(manifest_path, manifest)

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
        return 0, 0, 0, skipped

    print(
        f"\n[Batch] {total} row(s) to search, {skipped} already done. "
        f"concurrency={concurrency}\n"
    )

    sourced_count = 0
    needs_manual_count = 0
    failed_count = 0
    write_lock = threading.Lock()

    def _one(idx: int):
        try:
            manifest_item, error, retryable, staged_path, target_path = (
                _search_one_item(
                    items[idx],
                    output_dir=output_dir,
                    save_candidates=save_candidates,
                    max_candidates=max_candidates,
                    default_provider=default_provider,
                    default_strict=default_strict,
                    default_min_width=default_min_width,
                    default_min_height=default_min_height,
                )
            )
            return (
                idx,
                manifest_item,
                error,
                retryable,
                staged_path,
                target_path,
            )
        except Exception as exc:  # noqa: BLE001 — provider code raises freely
            return idx, None, str(exc)[:500], True, None, None

    futures: list[concurrent.futures.Future] = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = [ex.submit(_one, i) for i in pending_idx]
            for fut in concurrent.futures.as_completed(futures):
                (
                    idx,
                    manifest_item,
                    error,
                    retryable,
                    staged_path,
                    target_path,
                ) = fut.result()
                item = items[idx]
                with write_lock:
                    if (
                        manifest_item is not None
                        and staged_path is not None
                        and target_path is not None
                    ):
                        try:
                            _commit_staged_image(
                                staged_path,
                                target_path,
                                lambda: write_sources_manifest(
                                    sources_manifest_path,
                                    manifest_item,
                                ),
                            )
                        except Exception as exc:
                            if not _is_recoverable_image_error(exc):
                                raise
                            item["status"] = SEARCH_STATUS_FAILED
                            item["last_error"] = (
                                f"canonical/provenance commit failed: {exc}"
                            )[:500]
                            failed_count += 1
                            print(
                                f"  [FAIL] {item['filename']} — "
                                f"{item['last_error']}"
                            )
                        else:
                            item["status"] = SEARCH_STATUS_SOURCED
                            item["provider"] = manifest_item.get("provider", "")
                            item["license_tier"] = manifest_item.get(
                                "license_tier",
                                "",
                            )
                            item.pop("last_error", None)
                            sourced_count += 1
                            review = _write_review_copy(
                                target_path,
                                output_dir / ".review",
                                target_path.name,
                            )
                            if review is not None:
                                print(
                                    f"  review copy: {review}",
                                    file=sys.stderr,
                                )
                            print(
                                f"  [OK]   {item['filename']} "
                                f"({item['provider']})"
                            )
                    elif retryable:
                        item["status"] = SEARCH_STATUS_FAILED
                        item["last_error"] = error or "provider/download failure"
                        failed_count += 1
                        print(
                            f"  [FAIL] {item['filename']} — {item['last_error']}"
                        )
                    else:
                        item["status"] = SEARCH_STATUS_NEEDS_MANUAL
                        item["last_error"] = error or "search failed"
                        needs_manual_count += 1
                        print(
                            f"  [MANUAL] {item['filename']} — "
                            f"{item['last_error']}"
                        )
                    save_search_manifest(manifest_path, manifest)
    finally:
        # Workers only stage files. Any result not committed because of an
        # interrupt or a later manifest error must not leave candidate residue.
        for future in futures:
            if not future.done():
                continue
            try:
                outcome = future.result()
            except BaseException:
                continue
            staged_path = outcome[4]
            if staged_path is not None:
                try:
                    staged_path.unlink(missing_ok=True)
                except OSError:
                    pass

    print(
        f"\n[Batch] Done: {sourced_count} sourced / {failed_count} failed / "
        f"{needs_manual_count} needs-manual ({skipped} pre-skipped). "
        f"Manifest: {manifest_path}"
    )
    return sourced_count, needs_manual_count, failed_count, skipped


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
        help="Search query (1-4 concrete keywords work best). Omit in --batch mode.",
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

    try:
        if args.filename:
            args.filename = _validate_bare_filename(args.filename)
        if args.promote:
            args.promote = _validate_bare_filename(
                args.promote, field_name="--promote candidate filename"
            )
    except ValueError as exc:
        parser.error(str(exc))
    if args.min_width < 1 or args.min_height < 1:
        parser.error("--min-width and --min-height must both be positive integers")

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
            min_width=args.min_width,
            min_height=args.min_height,
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
            _, needs_manual, failed, _ = run_search_manifest(
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
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        # Mirror image_gen.py: any unresolved retryable or manual row keeps the
        # command non-zero. It is a gate signal, not a request to hide progress.
        return 1 if needs_manual or failed else 0

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

    manifest_path = (
        Path(args.manifest) if args.manifest else default_manifest_path(args.output)
    )
    try:
        _read_existing_manifest(manifest_path)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.filename

    print(f"Searching providers: {', '.join(providers)}", file=sys.stderr)
    result = search_and_download(
        providers,
        request,
        output_path=output_path,
        strict_no_attribution=args.strict_no_attribution,
        save_candidates=args.save_candidates,
        max_candidates=args.max_candidates,
    )

    if result.candidate is None:
        print(
            f"{result.error or 'Image search failed'}. "
            "Try a shorter query, use default attribution mode if strict mode "
            "is enabled, or set an API key for a keyed provider.",
            file=sys.stderr,
        )
        return 1

    print(
        f"  picked: {result.candidate.title!r} from {result.provider_name} "
        f"({result.candidate.license_name or 'no license string'}, "
        f"{result.candidate.license_tier})",
        file=sys.stderr,
    )

    # The staged file has already been measured; upstream metadata can still be
    # off (e.g. Openverse aggregates rawpixel which only exposes previews).
    actual_dimensions = result.actual_dimensions
    if (
        actual_dimensions is not None
        and result.candidate.width
        and result.candidate.height
        and actual_dimensions[0] * actual_dimensions[1]
        < 0.5 * result.candidate.width * result.candidate.height
    ):
        print(
            f"\n[!] Downloaded image is much smaller than upstream metadata "
            f"({actual_dimensions[0]}x{actual_dimensions[1]} vs "
            f"{result.candidate.width}x{result.candidate.height}). The provider "
            f"likely only exposes a preview here. Layout based on the manifest's "
            f"width/height will be accurate; the metadata_dimensions field "
            f"is preserved for reference.",
            file=sys.stderr,
        )

    if result.staged_path is None or result.output_path is None:
        print("Error: image search returned no staged output.", file=sys.stderr)
        if result.staged_path is not None:
            try:
                result.staged_path.unlink(missing_ok=True)
            except OSError:
                pass
        return 1
    try:
        item = _candidate_to_manifest_item(
            result.candidate,
            args,
            provider_name=result.provider_name or "",
            stage=result.stage or "",
            actual_dimensions=actual_dimensions,
        )
        written = _commit_staged_image(
            result.staged_path,
            result.output_path,
            lambda: write_sources_manifest(manifest_path, item),
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            result.staged_path.unlink(missing_ok=True)
        except OSError:
            pass
    print(f"  manifest: {written}", file=sys.stderr)
    review = _write_review_copy(
        result.output_path,
        result.output_path.parent / ".review",
        result.output_path.name,
    )
    if review is not None:
        print(f"  review copy: {review}", file=sys.stderr)

    if result.candidate.license_tier == "attribution-required":
        print(
            "\n[!] This image requires on-slide attribution. "
            "Executor should add a small credit element to the slide using "
            "the 'attribution_text' field in the manifest.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
