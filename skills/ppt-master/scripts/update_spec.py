#!/usr/bin/env python3
"""Propagate a spec_lock.md value change to both the lock file and svg_output/*.svg.

Examples:
    python3 update_spec.py <project_path> primary=#0066AA
    python3 update_spec.py <project_path> colors.text=#111111
    python3 update_spec.py <project_path> \\
        typography.font_family='Arial, "Microsoft YaHei", sans-serif'

v2 scope:
- `colors.*` — HEX value replacement across svg_output/*.svg (case-insensitive match).
- `typography.font_family` — replaces the inner value of every `font-family="..."`
  / `font-family='...'` attribute in svg_output/*.svg. This is a global replace:
  every text element becomes the new family, regardless of role, and every
  existing `typography.*_family` lock row is updated to the same value.

Bare `key=value` (no dot) is treated as `colors.key=value` for backward compat.

Other keys as independent targets (typography sizes, per-role
`typography.*_family` overrides, icons, images, canvas, forbidden) are
intentionally NOT supported — they involve attribute-scoped or semantic
replacements whose risk/benefit does not warrant bulk propagation. For
per-role family changes, edit spec_lock.md and re-author the affected pages.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from console_encoding import configure_utf8_stdio
from project_management.project_specs import parse_spec_lock as parse_lock
from stamp_native_fallbacks import (
    NativeFallbackStampError,
    prepare_native_fallback_baselines,
)

configure_utf8_stdio()

HEX_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
FONT_FAMILY_RE = re.compile(r"""(font-family\s*=\s*)(["'])(.*?)\2""")


def plan_lock_values(
    lock_path: Path, section: str, updates: dict[str, str]
) -> str:
    """Return a lock rewrite only after every target row validates."""
    lines = lock_path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_section = False
    found: set[str] = set()
    for i, raw in enumerate(lines):
        stripped = raw.rstrip("\r\n")
        line_ending = raw[len(stripped) :]
        if stripped.startswith("## "):
            in_section = stripped[3:].strip() == section
            continue
        if not in_section:
            continue
        m = re.match(r"^(-\s+)([A-Za-z0-9_]+)(\s*:\s*)(.+?)(\s*)$", stripped)
        if not m or m.group(2) not in updates:
            continue
        key = m.group(2)
        if key in found:
            raise ValueError(
                f"duplicate key {key!r} under section {section!r} in {lock_path}"
            )
        found.add(key)
        lines[i] = (
            f"{m.group(1)}{key}{m.group(3)}{updates[key]}{m.group(5)}"
            f"{line_ending}"
        )

    missing = set(updates) - found
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise KeyError(
            f"key(s) {missing_list} not found under section {section!r} in {lock_path}"
        )
    return "".join(lines)


def _plan_color_updates(
    svg_dir: Path,
    old_hex: str,
    new_hex: str,
) -> list[tuple[Path, str, int]]:
    """Return planned color rewrites without touching the SVG files."""
    if not HEX_RE.match(old_hex) or not HEX_RE.match(new_hex):
        raise ValueError(f"not a HEX color: old={old_hex!r} new={new_hex!r}")
    pattern = re.compile(
        rf"{re.escape(old_hex)}(?![0-9A-Fa-f])",
        re.IGNORECASE,
    )
    planned: list[tuple[Path, str, int]] = []
    for svg in sorted(svg_dir.glob("*.svg")):
        text = svg.read_text(encoding="utf-8")
        new_text, count = pattern.subn(new_hex, text)
        if count > 0:
            planned.append((svg, new_text, count))
    return planned


def _plan_font_family_updates(
    svg_dir: Path,
    new_value: str,
) -> list[tuple[Path, str, int]]:
    """Return planned font-family rewrites without touching the SVG files."""

    def replace_value(match: re.Match[str]) -> str:
        prefix, quote, _inner = match.group(1), match.group(2), match.group(3)
        outer = quote
        if outer in new_value:
            outer = "'" if quote == '"' else '"'
            if outer in new_value:
                raise ValueError(
                    f"new font_family value contains both ' and \" — cannot embed: "
                    f"{new_value!r}"
                )
        return f"{prefix}{outer}{new_value}{outer}"

    planned: list[tuple[Path, str, int]] = []
    for svg in sorted(svg_dir.glob("*.svg")):
        text = svg.read_text(encoding="utf-8")
        new_text, count = FONT_FAMILY_RE.subn(replace_value, text)
        if count > 0 and new_text != text:
            planned.append((svg, new_text, count))
    return planned


def _plan_native_fallback_updates(
    planned: list[tuple[Path, str, int]],
) -> tuple[list[tuple[Path, str, int]], int]:
    """Re-stamp changed SVG text in memory before the joint publish."""
    stamped: list[tuple[Path, str, int]] = []
    restamped_markers = 0
    for path, text, replacement_count in planned:
        payload, _svg_first, _json_first, restamped = (
            prepare_native_fallback_baselines(text.encode("utf-8"), path)
        )
        stamped.append((path, payload.decode("utf-8"), replacement_count))
        restamped_markers += restamped
    return stamped, restamped_markers


def _publish_text_updates(updates: list[tuple[Path, str]]) -> None:
    """Publish existing text files as one rollback unit."""
    if not updates:
        return
    targets = [path for path, _text in updates]
    if len(targets) != len(set(targets)):
        raise ValueError("transaction contains duplicate output paths")
    for target in targets:
        if not target.is_file() or target.is_symlink():
            raise OSError(f"transaction target must be a regular file: {target}")

    transaction_dir = Path(
        tempfile.mkdtemp(
            prefix=".update-spec-",
            dir=targets[0].parent,
        )
    )
    staged_dir = transaction_dir / "staged"
    backup_dir = transaction_dir / "previous"
    preserve_transaction = False
    published: list[tuple[Path, Path]] = []
    try:
        staged_dir.mkdir()
        backup_dir.mkdir()
        staged: list[tuple[Path, Path, Path]] = []
        transaction_device = transaction_dir.stat().st_dev
        for index, (target, text) in enumerate(updates):
            if target.parent.stat().st_dev != transaction_device:
                raise OSError(
                    f"cannot atomically publish across filesystems: {target}"
                )
            staged_path = staged_dir / f"{index:06d}.new"
            backup_path = backup_dir / f"{index:06d}.bak"
            staged_path.write_text(text, encoding="utf-8")
            shutil.copymode(target, staged_path)
            shutil.copy2(target, backup_path, follow_symlinks=False)
            staged.append((target, staged_path, backup_path))

        try:
            for target, staged_path, backup_path in staged:
                os.replace(staged_path, target)
                published.append((target, backup_path))
        except BaseException as publish_error:
            rollback_errors: list[str] = []
            for target, backup_path in reversed(published):
                try:
                    os.replace(backup_path, target)
                except BaseException as rollback_error:
                    rollback_errors.append(
                        f"could not restore {target}: "
                        f"{type(rollback_error).__name__}: {rollback_error}"
                    )
            if rollback_errors:
                preserve_transaction = True
                raise RuntimeError(
                    f"update_spec publish failed ({publish_error}); rollback was "
                    f"incomplete: {'; '.join(rollback_errors)}; recovery directory: "
                    f"{transaction_dir}"
                ) from publish_error
            raise
    finally:
        if not preserve_transaction:
            shutil.rmtree(transaction_dir, ignore_errors=True)


def replace_color_in_svgs(
    svg_dir: Path, old_hex: str, new_hex: str, *, dry_run: bool = False
) -> list[tuple[Path, int]]:
    """Replace old_hex with new_hex in every .svg under svg_dir.

    Returns a list of (path, replacement_count) for each changed file. The
    count comes straight from re.subn so callers can spot anomalies —
    e.g. one file with 50 hits when the rest have 4-8 is likely a stray
    HEX literal inside <text> content rather than a styling attribute.

    Two-phase: plan all file updates in memory, then publish them with rollback.
    If planning or publishing fails, the original files are retained.

    When dry_run=True, the planning phase still runs (so bad HEX still raises
    and callers see which files would change), but no disk writes happen. The
    returned list describes the would-change files.
    """
    planned = _plan_color_updates(svg_dir, old_hex, new_hex)
    if not dry_run:
        _publish_text_updates([
            (svg, new_text)
            for svg, new_text, _count in planned
        ])
    return [(path, count) for path, _text, count in planned]


def replace_font_family_in_svgs(
    svg_dir: Path, new_value: str, *, dry_run: bool = False
) -> list[tuple[Path, int]]:
    """Replace the inner value of every `font-family="..."` / `font-family='...'`
    attribute in every .svg under svg_dir.

    Returns a list of (path, replacement_count) for each changed file.

    Preserves the outer quote character when possible; if the new value contains
    that same quote type, switches the outer quote to the other kind.

    Two-phase: plan all file updates in memory, then publish them with rollback.
    A conflicting quote style fails during planning, before files are touched.

    When dry_run=True, the planning phase still runs (so the ValueError still
    fires and callers see which files would change), but no disk writes happen.
    The returned list describes the would-change files.
    """
    planned = _plan_font_family_updates(svg_dir, new_value)
    if not dry_run:
        _publish_text_updates([
            (svg, new_text)
            for svg, new_text, _count in planned
        ])
    return [(path, count) for path, _text, count in planned]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", type=Path, help="project folder containing spec_lock.md and svg_output/")
    ap.add_argument(
        "assignment",
        help=(
            "section.key=value (e.g. colors.primary=#0066AA, "
            "typography.font_family='Arial, \"Microsoft YaHei\", sans-serif'). "
            "Bare key=value is treated as colors.key=value."
        ),
    )
    ap.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="preview which SVGs would change; do not write anything to disk.",
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
    lock_changes: list[tuple[str, str, str]] = []

    if section == "colors":
        if not HEX_RE.match(new_value):
            print(f"error: new value for colors.{key} must be a HEX color (got {new_value!r})", file=sys.stderr)
            return 2
        if old_value == new_value:
            print(f"no change: colors.{key} already = {new_value}")
            return 0
        try:
            planned_lock = plan_lock_values(lock, "colors", {key: new_value})
        except (KeyError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        planned_svg = _plan_color_updates(svg_dir, old_value, new_value)
        lock_changes = [(key, old_value, new_value)]
    elif section == "typography" and key == "font_family":
        family_keys = [
            name
            for name in section_map
            if name == "font_family" or name.endswith("_family")
        ]
        lock_changes = [
            (name, section_map[name], new_value)
            for name in family_keys
            if section_map[name] != new_value
        ]
        if not lock_changes:
            print(f"no change: all typography.*_family rows already = {new_value}")
            return 0
        try:
            planned_lock = plan_lock_values(
                lock,
                "typography",
                {name: new_value for name in family_keys},
            )
            planned_svg = _plan_font_family_updates(svg_dir, new_value)
        except (KeyError, ValueError) as e:
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

    try:
        planned_svg, restamped_markers = _plan_native_fallback_updates(planned_svg)
    except (NativeFallbackStampError, UnicodeError) as exc:
        print(f"error: native fallback baselines could not be prepared: {exc}", file=sys.stderr)
        return 2

    changed = [
        (path, count)
        for path, _text, count in planned_svg
    ]
    if not args.dry_run:
        try:
            _publish_text_updates([
                *(
                    (path, new_text)
                    for path, new_text, _count in planned_svg
                ),
                (lock, planned_lock),
            ])
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"error: update was not published: {exc}", file=sys.stderr)
            return 2

    if args.dry_run:
        for lock_key, previous, replacement in lock_changes:
            print(
                f"[dry-run] spec_lock.md: "
                f"{section}.{lock_key}  {previous} → {replacement}"
            )
        print(f"[dry-run] svg_output/:  {len(changed)} file(s) would be updated")
        print(
            f"[dry-run] native fallbacks: {restamped_markers} marker(s) "
            "would be re-stamped"
        )
    else:
        for lock_key, previous, replacement in lock_changes:
            print(
                f"spec_lock.md: {section}.{lock_key}  {previous} → {replacement}"
            )
        print(f"svg_output/:  {len(changed)} file(s) updated")
        print(f"native fallbacks: {restamped_markers} marker(s) re-stamped")
    for p, n in changed:
        suffix = "replacement" if n == 1 else "replacements"
        print(f"  - {p.name} ({n} {suffix})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
