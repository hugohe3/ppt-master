#!/usr/bin/env python3
"""
PPT Master - Slide Roster Helpers

Orders slide SVG filenames by numeric segments for consistent page rosters.

Usage:
    Imported by export, validation, preview, animation, and narration tools.

Examples:
    discover_slide_svgs(Path("projects/demo/svg_output"))

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path


_NUMBER_RE = re.compile(r"(\d+)")


def _slide_filename_sort_key(
    path: Path,
) -> tuple[tuple[tuple[int, int | str], ...], str]:
    """Order numeric filename segments by value, then break ties by name."""
    name = path.name
    folded = name.casefold()
    segments = tuple(
        (0, int(segment)) if segment.isdigit() else (1, segment)
        for segment in _NUMBER_RE.split(folded)
    )
    return segments, name


def sort_slide_paths(paths: Iterable[Path]) -> list[Path]:
    """Order per-page files (SVG, notes, SRT) by numeric filename segments."""
    return sorted(paths, key=_slide_filename_sort_key)


def discover_slide_svgs(directory: Path) -> list[Path]:
    """Return direct child SVG files in numeric filename order."""
    return sort_slide_paths(directory.glob("*.svg"))
