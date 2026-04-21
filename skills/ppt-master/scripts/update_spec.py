#!/usr/bin/env python3
"""Propagate a spec_lock.md value change to both the lock file and svg_output/*.svg.

Example:
    python3 update_spec.py <project_path> primary=#0066AA
    python3 update_spec.py <project_path> text=#111111

v1 scope:
- Only rewrites keys under the `colors` section of spec_lock.md.
- Replaces the old HEX value with the new one in every SVG under svg_output/.
  Case-insensitive match on hex; preserves the source's casing style in output.

Typography sizes, font_family, icons, and images are intentionally NOT supported
in v1 — they involve attribute-scoped replacements whose risk/benefit was not
worth the first cut. Add them here when a concrete need arises.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{3,8}$")


def parse_lock(lock_path: Path) -> dict[str, dict[str, str]]:
    """Return {section_name: {key: value}} parsed from spec_lock.md.

    The format is:
        ## section
        - key: value
    """
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in lock_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, {})
            continue
        if current is None:
            continue
        m = re.match(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$", line)
        if m:
            sections[current][m.group(1)] = m.group(2)
    return sections


def rewrite_lock(lock_path: Path, section: str, key: str, new_value: str) -> None:
    """Rewrite the single `- key: old_value` line under `## section`."""
    lines = lock_path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_section = False
    for i, raw in enumerate(lines):
        stripped = raw.rstrip("\n")
        if stripped.startswith("## "):
            in_section = stripped[3:].strip() == section
            continue
        if not in_section:
            continue
        m = re.match(r"^(-\s+)([A-Za-z0-9_]+)(\s*:\s*)(.+?)(\s*)$", stripped)
        if m and m.group(2) == key:
            lines[i] = f"{m.group(1)}{m.group(2)}{m.group(3)}{new_value}{m.group(5)}\n"
            lock_path.write_text("".join(lines), encoding="utf-8")
            return
    raise KeyError(f"key {key!r} not found under section {section!r} in {lock_path}")


def replace_color_in_svgs(svg_dir: Path, old_hex: str, new_hex: str) -> list[Path]:
    """Replace old_hex with new_hex in every .svg under svg_dir. Returns changed files."""
    if not HEX_RE.match(old_hex) or not HEX_RE.match(new_hex):
        raise ValueError(f"not a HEX color: old={old_hex!r} new={new_hex!r}")
    pattern = re.compile(re.escape(old_hex), re.IGNORECASE)
    changed: list[Path] = []
    for svg in sorted(svg_dir.glob("*.svg")):
        text = svg.read_text(encoding="utf-8")
        new_text, n = pattern.subn(new_hex, text)
        if n > 0:
            svg.write_text(new_text, encoding="utf-8")
            changed.append(svg)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", type=Path, help="project folder containing spec_lock.md and svg_output/")
    ap.add_argument("assignment", help="key=value, e.g. primary=#0066AA")
    args = ap.parse_args()

    project = args.project_path.resolve()
    lock = project / "spec_lock.md"
    svg_dir = project / "svg_output"

    if not lock.exists():
        print(f"error: spec_lock.md not found at {lock}", file=sys.stderr)
        return 2
    if not svg_dir.exists():
        print(f"error: svg_output/ not found at {svg_dir}", file=sys.stderr)
        return 2

    if "=" not in args.assignment:
        print("error: assignment must be key=value", file=sys.stderr)
        return 2
    key, new_value = args.assignment.split("=", 1)
    key = key.strip()
    new_value = new_value.strip()

    sections = parse_lock(lock)
    colors = sections.get("colors", {})
    if key not in colors:
        print(
            f"error: {key!r} is not a key under `## colors` in spec_lock.md.\n"
            f"v1 only supports color keys. Known: {sorted(colors)}",
            file=sys.stderr,
        )
        return 2

    old_value = colors[key]
    if not HEX_RE.match(new_value):
        print(f"error: new value must be a HEX color (got {new_value!r})", file=sys.stderr)
        return 2
    if old_value == new_value:
        print(f"no change: {key} already = {new_value}")
        return 0

    rewrite_lock(lock, "colors", key, new_value)
    changed = replace_color_in_svgs(svg_dir, old_value, new_value)

    print(f"spec_lock.md: colors.{key}  {old_value} → {new_value}")
    print(f"svg_output/:  {len(changed)} file(s) updated")
    for p in changed:
        print(f"  - {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
