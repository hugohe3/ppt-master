#!/usr/bin/env python3
"""
PPT Master - Markdown Conversion Profile Helpers

Write lightweight sidecar metadata for source_to_md conversion outputs.

Usage:
    Imported by scripts/source_to_md/*.py

Examples:
    write_conversion_profile(input_path="demo.pdf", markdown_path="demo.md", ...)

Dependencies:
    None
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


IMAGE_MANIFEST_NAME = "image_manifest.json"
PROFILE_SCHEMA = "ppt-master.source_to_md.profile.v1"
PROFILE_SUFFIX = ".conversion_profile.json"


def default_asset_dir(markdown_path: Path) -> Path:
    """Return the conventional companion asset directory for one Markdown output."""
    return markdown_path.parent / f"{markdown_path.stem}_files"


def profile_path_for(markdown_path: Path) -> Path:
    """Return the sidecar profile path for one Markdown output."""
    return markdown_path.with_name(f"{markdown_path.stem}{PROFILE_SUFFIX}")


def _display_path(path: Path | None, root: Path) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _count_tables(lines: list[str]) -> int:
    count = 0
    in_table = False
    separator_re = re.compile(
        r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$"
    )
    for line in lines:
        stripped = line.strip()
        is_table_line = stripped.startswith("|") and stripped.endswith("|")
        has_separator = bool(separator_re.match(stripped))
        if is_table_line or has_separator:
            if not in_table:
                count += 1
                in_table = True
            continue
        in_table = False
    return count


def markdown_stats(markdown_path: Path) -> dict[str, int]:
    """Return low-cost Markdown structure counts for inspection/debugging."""
    if not markdown_path.is_file():
        return {
            "line_count": 0,
            "char_count": 0,
            "heading_count": 0,
            "table_count": 0,
            "image_ref_count": 0,
            "link_count": 0,
        }

    text = markdown_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return {
        "line_count": len(lines),
        "char_count": len(text),
        "heading_count": sum(1 for line in lines if re.match(r"^#{1,6}\s+", line)),
        "table_count": _count_tables(lines),
        "image_ref_count": len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text)),
        "link_count": len(re.findall(r"(?<!!)\[[^\]]+\]\([^)]+\)", text)),
    }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _image_count_from_manifest(path: Path) -> int:
    payload = _read_json(path)
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return len(items)
    return 0


def build_conversion_profile(
    *,
    input_path: str,
    markdown_path: str | Path,
    converter: str,
    conversion_type: str,
    asset_dir: str | Path | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a sidecar profile without changing the Markdown conversion result."""
    markdown = Path(markdown_path)
    root = markdown.parent
    is_url = input_path.startswith(("http://", "https://"))
    source = None if is_url else Path(input_path)
    assets = Path(asset_dir) if asset_dir else default_asset_dir(markdown)
    image_manifest = assets / IMAGE_MANIFEST_NAME
    source_exists = bool(source and source.exists())

    return {
        "schema": PROFILE_SCHEMA,
        "converter": converter,
        "conversion_type": conversion_type,
        "source": {
            "path": input_path if is_url else _display_path(source, root),
            "name": input_path if is_url else (source.name if source else input_path),
            "suffix": "" if is_url else (source.suffix.lower() if source else ""),
            "kind": "url" if is_url else "file",
            "exists": source_exists,
            "size_bytes": (
                source.stat().st_size
                if source_exists and source is not None and source.is_file()
                else None
            ),
        },
        "outputs": {
            "markdown": _display_path(markdown, root),
            "asset_dir": _display_path(assets, root) if assets.is_dir() else "",
            "image_manifest": (
                _display_path(image_manifest, root) if image_manifest.is_file() else ""
            ),
            "image_count": _image_count_from_manifest(image_manifest),
        },
        "markdown": markdown_stats(markdown),
        "warnings": warnings or [],
    }


def write_conversion_profile(
    *,
    input_path: str,
    markdown_path: str | Path,
    converter: str,
    conversion_type: str,
    asset_dir: str | Path | None = None,
    warnings: list[str] | None = None,
) -> Path:
    """Write `<stem>.conversion_profile.json` beside one Markdown output."""
    markdown = Path(markdown_path)
    profile_path = profile_path_for(markdown)
    profile = build_conversion_profile(
        input_path=input_path,
        markdown_path=markdown,
        converter=converter,
        conversion_type=conversion_type,
        asset_dir=asset_dir,
        warnings=warnings,
    )
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return profile_path


def write_conversion_profile_best_effort(
    *,
    input_path: str,
    markdown_path: str | Path,
    converter: str,
    conversion_type: str,
    asset_dir: str | Path | None = None,
    warnings: list[str] | None = None,
) -> Path | None:
    """Write a profile sidecar, warning without changing converter success."""
    try:
        return write_conversion_profile(
            input_path=input_path,
            markdown_path=markdown_path,
            converter=converter,
            conversion_type=conversion_type,
            asset_dir=asset_dir,
            warnings=warnings,
        )
    except OSError as exc:
        print(f"[WARN] Could not write conversion profile: {exc}", file=sys.stderr)
        return None


def build_result_payload(
    *,
    input_path: str,
    markdown_path: str | Path,
    converter: str,
    conversion_type: str,
    asset_dir: str | Path | None = None,
    profile_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a compact JSON payload for CLI consumers."""
    markdown = Path(markdown_path)
    assets = Path(asset_dir) if asset_dir else default_asset_dir(markdown)
    image_manifest = assets / IMAGE_MANIFEST_NAME
    profile = Path(profile_path) if profile_path else profile_path_for(markdown)
    return {
        "input": (
            input_path
            if input_path.startswith(("http://", "https://"))
            else str(Path(input_path).resolve())
        ),
        "markdown": str(markdown.resolve()),
        "asset_dir": str(assets.resolve()) if assets.is_dir() else "",
        "image_manifest": str(image_manifest.resolve()) if image_manifest.is_file() else "",
        "conversion_profile": str(profile.resolve()) if profile.is_file() else "",
        "converter": converter,
        "conversion_type": conversion_type,
    }
