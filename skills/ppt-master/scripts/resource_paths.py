#!/usr/bin/env python3
"""
PPT Master - Shared SVG Resource Path Helpers

Centralizes project-relative SVG resource lookup used by the checker,
finalizer, and SVG-to-PPTX exporter.

Usage:
    Imported by scripts; not intended as a standalone CLI.

Examples:
    from resource_paths import resolve_external_image_reference

Dependencies:
    None
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit


SVG_WORK_DIR_NAMES = frozenset({'svg_output', 'svg_final', 'svg-flat', 'svg_flat'})


def project_root_for_svg_path(svg_path: Path) -> Path:
    """Infer the project root from an SVG file path or SVG directory path."""
    path = Path(svg_path)
    base = path if path.is_dir() else path.parent
    if base.name in SVG_WORK_DIR_NAMES:
        return base.parent
    return base


def global_icons_dir() -> Path:
    """Return the skill-level icon library directory."""
    return Path(__file__).resolve().parent.parent / 'templates' / 'icons'


def icon_search_dirs_for_project(project_path: Path) -> tuple[Path, Path | None]:
    """Return project-first icon dirs plus the global fallback when needed."""
    global_dir = global_icons_dir()
    project_icons_dir = Path(project_path) / 'icons'
    if project_icons_dir.is_dir():
        return project_icons_dir, global_dir
    return global_dir, None


def icon_search_dirs_for_svg(svg_path: Path) -> tuple[Path, Path | None]:
    """Return icon dirs for an SVG file path or SVG directory path."""
    return icon_search_dirs_for_project(project_root_for_svg_path(svg_path))


def external_image_reference_candidates(svg_dir: Path, href: str) -> list[Path]:
    """Return candidate paths for a non-data-URI SVG image href."""
    parsed = urlsplit(href)
    if parsed.scheme and parsed.scheme not in {'file'}:
        return []
    decoded = unquote(
        parsed.path
        if parsed.scheme
        else href.split('?', 1)[0].split('#', 1)[0]
    )
    svg_dir = Path(svg_dir)
    project_root = project_root_for_svg_path(svg_dir)
    return [
        svg_dir / decoded,
        project_root / decoded,
        project_root / 'images' / decoded,
        project_root / 'templates' / decoded,
    ]


def resolve_external_image_reference(svg_dir: Path, href: str) -> Path | None:
    """Resolve an SVG image href to an existing file, or return None."""
    for candidate in external_image_reference_candidates(svg_dir, href):
        if candidate.exists():
            return candidate.resolve()
    return None


def unresolved_external_image_reference_path(svg_dir: Path, href: str) -> Path:
    """Return the first candidate path for diagnostics when resolution fails."""
    candidates = external_image_reference_candidates(svg_dir, href)
    if candidates:
        return candidates[0].resolve()
    return (Path(svg_dir) / href).resolve()
