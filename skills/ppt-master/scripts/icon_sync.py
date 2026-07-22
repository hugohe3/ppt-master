#!/usr/bin/env python3
"""
PPT Master - Icon Sync

Copy chosen library icons into `<project>/icons/<lib>/` when selected. Missing
names exit non-zero before export. Known basenames need no separate existence
check; search the chosen library only for unresolved concepts.

Project-local custom icons count as satisfied. In one Strategist selection
batch, `simple-icons` may accompany one of the four stylistic libraries for
real brand marks.

Usage:
    python3 scripts/icon_sync.py <project_path> <lib/name> [<lib/name> ...]

Examples:
    python3 scripts/icon_sync.py projects/deck tabler-outline/home tabler-outline/chart
    python3 scripts/icon_sync.py projects/deck tabler-outline/home simple-icons/github

Dependencies:
    None (standard library only).

See references/executor-base.md §4 and templates/icons/README.md.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

_LIB_ALIASES = {"chunk": "chunk-filled"}
_STYLISTIC_LIBRARIES = {
    "chunk-filled",
    "phosphor-duotone",
    "tabler-filled",
    "tabler-outline",
}
_GLOBAL_ICONS_DIR = Path(__file__).resolve().parent.parent / "templates" / "icons"


def _split_name(icon_name: str) -> tuple[str, str]:
    """`lib/name` -> (lib, name), applying the chunk→chunk-filled alias."""
    if "/" not in icon_name:
        # legacy un-prefixed names live in chunk-filled/
        return "chunk-filled", icon_name
    lib, name = icon_name.split("/", 1)
    return _LIB_ALIASES.get(lib, lib), name


def sync_icons(project_path: Path, icon_names: list[str], global_dir: Path = _GLOBAL_ICONS_DIR) -> tuple[list[str], list[str]]:
    """Copy each `lib/name` from the global library into `<project>/icons/`.

    Returns (copied, missing). A name already present in the project (e.g. a
    custom icon) counts as satisfied, not missing.
    """
    project_icons = project_path / "icons"
    copied: list[str] = []
    missing: list[str] = []

    for raw in icon_names:
        lib, name = _split_name(raw)
        src = global_dir / lib / f"{name}.svg"
        dst = project_icons / lib / f"{name}.svg"
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(f"{lib}/{name}")
        elif dst.is_file():
            copied.append(f"{lib}/{name} (already in project)")
        else:
            missing.append(f"{lib}/{name}")

    return copied, missing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy chosen library icons into a project's icons/ folder; report missing ones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("icons", nargs="+", help="Icon names to copy, e.g. chunk-filled/home")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    project = Path(args.project_path)
    if not project.is_dir():
        print(f"[ERROR] project not found: {project}", file=sys.stderr)
        return 1

    requested_libraries = {_split_name(raw)[0] for raw in args.icons}
    stylistic_libraries = sorted(requested_libraries & _STYLISTIC_LIBRARIES)
    if len(stylistic_libraries) > 1:
        print(
            f"[ERROR] mixed stylistic icon libraries: {', '.join(stylistic_libraries)}",
            file=sys.stderr,
        )
        print(
            "Choose one of the four stylistic libraries per selection batch; "
            "simple-icons may coexist for real brand marks.",
            file=sys.stderr,
        )
        return 1

    copied, missing = sync_icons(project, args.icons)

    if copied:
        print(f"[OK] {len(copied)} icon(s) in {project / 'icons'}:", file=sys.stderr)
        for c in copied:
            print(f"     + {c}", file=sys.stderr)

    if missing:
        print(f"\n[MISSING] {len(missing)} icon(s) not in the library — re-pick before continuing:", file=sys.stderr)
        for m in missing:
            lib = m.split("/", 1)[0]
            print(
                f'     ✗ {m}   (search: rg --files "{_GLOBAL_ICONS_DIR / lib}" -g \'*<keyword>*.svg\')',
                file=sys.stderr,
            )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
