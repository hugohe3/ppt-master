#!/usr/bin/env python3
"""Web image search CLI.

Sister tool to ``image_gen.py``: instead of generating an image from a
prompt, this searches openly-licensed image providers and downloads a
single best match.

Workflow:
    1. Build an :class:`ImageSearchRequest` from CLI args.
    2. Two-stage license-tier search:
       - Stage 1: ask each provider for ``no-attribution-only`` matches
         (CC0, Public Domain, Pexels, Pixabay). If any provider returns
         candidates, pick the highest-scoring one and stop.
       - Stage 2 (only if stage 1 yielded nothing AND
         ``--strict-no-attribution`` was NOT set): retry with the ``all``
         filter, accepting CC BY / CC BY-SA. The chosen image is recorded
         with ``license_tier == "attribution-required"`` so the Executor
         knows to add an inline credit on the slide.
    3. Download the chosen image into ``--output``.
    4. Append a record to ``image_sources.json`` (the single source of
       truth for downstream credit rendering).

Examples:
    # Default: zero-config, prefers no-attribution images
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
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# Make sibling modules importable when this script is invoked directly.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from image_backends.backend_common import download_image  # noqa: E402
from image_sources.provider_common import (  # noqa: E402
    AssetCandidate,
    ImageSearchRequest,
    USER_AGENT,
    build_attribution_text,
    ensure_json_parent,
    score_candidate,
)


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


# ---------------------------------------------------------------------------
# .env loading (lightweight; matches image_gen.py behavior)
# ---------------------------------------------------------------------------


def _load_dotenv_if_available() -> None:
    """Best-effort .env loading: cwd then repo root. Silently no-op if
    python-dotenv isn't installed or no file is found."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        load_dotenv(cwd_env, override=False)
    repo_env = _SCRIPTS_DIR.parent.parent.parent / ".env"
    if repo_env.is_file():
        load_dotenv(repo_env, override=False)


# ---------------------------------------------------------------------------
# Provider dispatch
# ---------------------------------------------------------------------------


def _load_provider(name: str):
    return importlib.import_module(PROVIDER_MODULES[name])


def _is_keyed_provider_unconfigured(provider_name: str, exc: Exception) -> bool:
    """Treat 'API key missing' as a non-fatal skip (so default fallback
    can keep going through the other providers)."""
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


def two_stage_search(
    providers: list[str],
    request: ImageSearchRequest,
    *,
    output_path: Path,
    strict_no_attribution: bool,
) -> tuple[Optional[AssetCandidate], Optional[str], Optional[str]]:
    """Find a candidate AND successfully download it.

    Iterates ``stages × providers × ranked candidates`` and returns the
    first candidate whose ``download_url`` actually transfers. A candidate
    that 403s, 404s, or otherwise fails to download is skipped and the
    next-best one is tried — so a single dead asset cannot fail the whole
    request.

    Returns ``(candidate, provider_name, stage)`` for the successfully
    downloaded image, or ``(None, None, None)`` if every combination
    failed.
    """
    stages: list[str] = ["no-attribution-only"]
    if not strict_no_attribution:
        stages.append("all")

    for stage in stages:
        for provider_name in providers:
            print(f"  -> trying {provider_name} ({stage}) ...", file=sys.stderr)
            candidates = _try_provider(provider_name, request, stage)
            if not candidates:
                continue

            ranked = sorted(
                candidates,
                key=lambda c: score_candidate(c, request),
                reverse=True,
            )

            for candidate in ranked:
                try:
                    download_image(
                        candidate.download_url,
                        str(output_path),
                        headers={"User-Agent": USER_AGENT},
                    )
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
    parser.add_argument("query", help="Search query (2-5 keywords work best).")
    parser.add_argument(
        "--filename",
        required=True,
        help="Local filename for the chosen image (e.g. cover_bg.jpg).",
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
            "Refuse CC BY / CC BY-SA results. If no CC0/Public Domain match is "
            "found, exit non-zero rather than falling back to attribution-required."
        ),
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Override manifest path. Defaults to <output>/image_sources.json.",
    )
    return parser


def _default_provider_chain() -> list[str]:
    """Zero-config providers first; add keyed providers only if their key
    is configured. This is the search order when ``--provider`` is unset."""
    chain: list[str] = list(ZERO_CONFIG_PROVIDERS)
    if os.environ.get("PEXELS_API_KEY"):
        chain.append("pexels")
    if os.environ.get("PIXABAY_API_KEY"):
        chain.append("pixabay")
    return chain


def main(argv: Optional[list[str]] = None) -> int:
    _load_dotenv_if_available()

    parser = build_parser()
    args = parser.parse_args(argv)

    request = ImageSearchRequest(
        query=args.query,
        purpose=args.purpose,
        orientation="" if args.orientation == "any" else args.orientation,
        filename=args.filename,
        slide=args.slide,
    )

    providers = [args.provider] if args.provider else _default_provider_chain()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.filename

    print(f"Searching providers: {', '.join(providers)}", file=sys.stderr)
    candidate, provider_name, stage = two_stage_search(
        providers,
        request,
        output_path=output_path,
        strict_no_attribution=args.strict_no_attribution,
    )

    if candidate is None:
        print(
            "No acceptable candidates could be downloaded across all "
            "providers/stages. Try a shorter query, drop "
            "--strict-no-attribution, or set an API key for a keyed provider.",
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
