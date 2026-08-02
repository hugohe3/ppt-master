"""Find SVG and notes files in a project directory."""

from __future__ import annotations

import re
from pathlib import Path

from slide_roster import discover_slide_svgs


class NotesFileReadError(RuntimeError):
    """Report a matched notes file that cannot be decoded or read."""


def find_svg_files(
    project_path: Path,
    source: str = 'output',
    *,
    allow_fallback: bool = True,
) -> tuple[list[Path], str]:
    """Find SVG files in the project.

    Args:
        project_path: Project directory path.
        source: SVG source directory alias or name.
            - 'output': svg_output (hand-authored source; native default)
            - 'final': svg_final (post-processed preview; diagnostic input)
            - or any subdirectory name
        allow_fallback: Try svg_output and then the project root when the
            requested directory is missing.

    Returns:
        (list_of_svg_files, actual_directory_name) tuple.
    """
    dir_map = {
        'output': 'svg_output',
        'final': 'svg_final',
    }

    dir_name = dir_map.get(source, source)
    svg_dir = project_path / dir_name

    if not svg_dir.exists():
        if not allow_fallback:
            return [], dir_name
        print(f"  Warning: {dir_name} directory does not exist, trying svg_output")
        dir_name = 'svg_output'
        svg_dir = project_path / dir_name

    if not svg_dir.exists():
        if project_path.is_dir():
            svg_dir = project_path
            dir_name = project_path.name
        else:
            return [], ''

    return discover_slide_svgs(svg_dir), dir_name


def find_notes_files(
    project_path: Path,
    svg_files: list[Path] | None = None,
) -> dict[str, str]:
    """Find notes files and map them to SVG files.

    Supports two matching modes (mixed matching supported):
    1. Match by filename (priority): notes/01_cover.md -> 01_cover.svg
    2. Match by index (backward compatible): notes/slide01.md -> 1st SVG

    Args:
        project_path: Project directory path.
        svg_files: SVG file list (for filename matching).

    Returns:
        Dict mapping SVG filename stem to notes content.
    """
    notes_dir = project_path / 'notes'
    notes: dict[str, str] = {}

    if not notes_dir.exists():
        return notes

    svg_stems_mapping: dict[str, int] = {}
    svg_index_mapping: dict[int, str] = {}
    if svg_files:
        for i, svg_path in enumerate(svg_files, 1):
            svg_stems_mapping[svg_path.stem] = i
            svg_index_mapping[i] = svg_path.stem

    for notes_file in notes_dir.glob('*.md'):
        stem = notes_file.stem

        # Try index-based matching (backward compat with slide01.md format).
        match = re.search(r'slide[_]?(\d+)', stem)
        mapped_stem = (
            svg_index_mapping.get(int(match.group(1)))
            if match
            else None
        )
        filename_match = stem in svg_stems_mapping
        if mapped_stem is None and not filename_match:
            continue

        try:
            content = notes_file.read_text(encoding='utf-8').strip()
        except (OSError, UnicodeError) as exc:
            raise NotesFileReadError(
                f"Cannot read matched notes file {notes_file}: {exc}"
            ) from exc
        if not content:
            continue

        if mapped_stem:
            notes[mapped_stem] = content

        # Filename-based matching overrides index-based matching.
        if filename_match:
            notes[stem] = content

    return notes
