#!/usr/bin/env python3
"""Propagate a spec_lock.md value change to both the lock file and svg_output/*.svg.

Examples:
    python3 update_spec.py <project_path> primary=#0066AA
    python3 update_spec.py <project_path> colors.text=#111111
    python3 update_spec.py <project_path> typography.font_family='"Inter", Arial, sans-serif'

v2 scope:
- `colors.*` — HEX value replacement across svg_output/*.svg (case-insensitive match).
- `typography.font_family` — replaces the inner value of every `font-family="..."`
  / `font-family='...'` attribute in svg_output/*.svg.

Bare `key=value` (no dot) is treated as `colors.key=value` for backward compat.

Other keys (typography sizes, icons, images, canvas, forbidden) are intentionally
NOT supported — they involve attribute-scoped or semantic replacements whose
risk/benefit does not warrant bulk propagation. Edit spec_lock.md and the
affected SVGs by hand, or re-author the pages.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
FONT_FAMILY_RE = re.compile(r"""(font-family\s*=\s*)(["'])(.*?)\2""")


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


def replace_font_family_in_svgs(svg_dir: Path, new_value: str) -> list[Path]:
    """Replace the inner value of every `font-family="..."` / `font-family='...'`
    attribute in every .svg under svg_dir. Returns changed files.

    Preserves the outer quote character when possible; if the new value contains
    that same quote type, switches the outer quote to the other kind.
    """
    changed: list[Path] = []

    def _sub(m: re.Match[str]) -> str:
        prefix, quote, _inner = m.group(1), m.group(2), m.group(3)
        outer = quote
        if outer in new_value:
            outer = "'" if quote == '"' else '"'
            if outer in new_value:
                raise ValueError(
                    f"new font_family value contains both ' and \" — cannot embed: {new_value!r}"
                )
        return f"{prefix}{outer}{new_value}{outer}"

    for svg in sorted(svg_dir.glob("*.svg")):
        text = svg.read_text(encoding="utf-8")
        new_text, n = FONT_FAMILY_RE.subn(_sub, text)
        if n > 0 and new_text != text:
            svg.write_text(new_text, encoding="utf-8")
            changed.append(svg)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", type=Path, help="project folder containing spec_lock.md and svg_output/")
    ap.add_argument(
        "assignment",
        help="section.key=value (e.g. colors.primary=#0066AA, typography.font_family='\"Inter\", Arial, sans-serif'). "
        "Bare key=value is treated as colors.key=value.",
    )
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
        print("error: assignment must be [section.]key=value", file=sys.stderr)
        return 2
    lhs, new_value = args.assignment.split("=", 1)
    lhs = lhs.strip()
    new_value = new_value.strip()
    if "." in lhs:
        section, key = lhs.split(".", 1)
        section = section.strip()
        key = key.strip()
    else:
        section, key = "colors", lhs

    sections = parse_lock(lock)
    section_map = sections.get(section, {})
    if key not in section_map:
        known = {s: sorted(v) for s, v in sections.items()}
        print(
            f"error: {key!r} not found under `## {section}` in spec_lock.md.\n"
            f"known keys: {known}",
            file=sys.stderr,
        )
        return 2

    old_value = section_map[key]

    if section == "colors":
        if not HEX_RE.match(new_value):
            print(f"error: new value for colors.{key} must be a HEX color (got {new_value!r})", file=sys.stderr)
            return 2
        if old_value == new_value:
            print(f"no change: colors.{key} already = {new_value}")
            return 0
        rewrite_lock(lock, "colors", key, new_value)
        changed = replace_color_in_svgs(svg_dir, old_value, new_value)
    elif section == "typography" and key == "font_family":
        if old_value == new_value:
            print(f"no change: typography.font_family already = {new_value}")
            return 0
        rewrite_lock(lock, "typography", key, new_value)
        try:
            changed = replace_font_family_in_svgs(svg_dir, new_value)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        print(
            f"error: {section}.{key} is not supported by update_spec.py.\n"
            f"v2 supports: colors.* (HEX), typography.font_family.\n"
            f"Edit spec_lock.md and the affected SVGs by hand for other changes.",
            file=sys.stderr,
        )
        return 2

    print(f"spec_lock.md: {section}.{key}  {old_value} → {new_value}")
    print(f"svg_output/:  {len(changed)} file(s) updated")
    for p in changed:
        print(f"  - {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
