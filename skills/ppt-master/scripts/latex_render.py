#!/usr/bin/env python3
"""PPT Master - LaTeX Formula Renderer

Render LaTeX formulas in spec_lock.md to transparent PNG images.

Dependencies: matplotlib (pip install matplotlib)

Usage:
    python3 scripts/latex_render.py <project_path>
    python3 scripts/latex_render.py <project_path> --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex patterns: $$...$$ (block) matched BEFORE $...$ (inline)
# ---------------------------------------------------------------------------
_RE_BLOCK = re.compile(r"\$\$([^$]+?)\$\$", re.DOTALL)
_RE_INLINE = re.compile(r"\$([^$\n]+?)\$")


def extract_formulas(text: str) -> list[tuple[str, str, bool]]:
    """Extract all formulas from text.

    Returns list of (full_match, latex_content, is_block).
    Block formulas ($$...$$) are extracted first, then inline ($...$).
    """
    results: list[tuple[str, str, bool]] = []
    # Track spans already claimed by block matches
    claimed: list[tuple[int, int]] = []

    for m in _RE_BLOCK.finditer(text):
        results.append((m.group(0), m.group(1).strip(), True))
        claimed.append((m.start(), m.end()))

    for m in _RE_INLINE.finditer(text):
        # Skip if this position overlaps a claimed block span
        if any(s <= m.start() < e for s, e in claimed):
            continue
        results.append((m.group(0), m.group(1).strip(), False))

    return results


def render_formula(latex: str, output_path: Path, dpi: int = 300) -> bool:
    """Render a single LaTeX formula to a transparent PNG.

    Returns True on success, False on failure (prints warning).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.axis("off")
        ax.text(0, 0.5, f"${latex}$", fontsize=20, ha="left", va="center",
                transform=ax.transAxes)
        fig.savefig(
            str(output_path),
            dpi=dpi,
            transparent=True,
            bbox_inches="tight",
            pad_inches=0.05,
        )
        plt.close(fig)
        return True
    except Exception as exc:
        print(f"  [WARN] Failed to render '{latex}': {exc}", file=sys.stderr)
        return False


def process_spec_lock(project_path: Path, dry_run: bool = False) -> int:
    """Main entry: scan spec_lock.md, render, replace.

    Returns number of formulas rendered.
    """
    spec_lock = project_path / "spec_lock.md"
    if not spec_lock.is_file():
        print("spec_lock.md not found; nothing to do.")
        return 0

    text = spec_lock.read_text(encoding="utf-8")
    formulas = extract_formulas(text)

    if not formulas:
        print("No LaTeX formulas found in spec_lock.md.")
        return 0

    # Deduplicate: same latex → same file
    seen: dict[str, str] = {}  # latex → file reference like "images/latex/F01.png"
    counter = 1
    replacements: list[tuple[str, str, str]] = []  # (full_match, file_ref, latex)

    for full_match, latex, is_block in formulas:
        if latex in seen:
            replacements.append((full_match, seen[latex], latex))
            continue
        file_ref = f"images/latex/F{counter:02d}.png"
        seen[latex] = file_ref
        replacements.append((full_match, file_ref, latex))
        counter += 1

    print(f"Found {len(replacements)} formula(s) ({len(seen)} unique).\n")

    if dry_run:
        for full_match, file_ref, latex in replacements:
            print(f"  {file_ref}: {latex}")
        return 0

    # Ensure output directory exists
    latex_dir = project_path / "images" / "latex"
    latex_dir.mkdir(parents=True, exist_ok=True)

    # Render unique formulas
    rendered = 0
    for latex, file_ref in seen.items():
        out_path = project_path / file_ref
        if out_path.exists():
            print(f"  [SKIP] {file_ref} (already exists)")
            continue
        if render_formula(latex, out_path):
            print(f"  [OK]   {file_ref}: {latex}")
            rendered += 1

    # Build set of formulas with valid PNGs (rendered or pre-existing)
    rendered_ok: set[str] = set()
    for latex, file_ref in seen.items():
        if (project_path / file_ref).exists():
            rendered_ok.add(latex)

    # Replace only formulas whose PNG exists on disk
    new_text = text
    replaced = 0
    for full_match, file_ref, latex in replacements:
        if latex in rendered_ok:
            new_text = new_text.replace(full_match, f"![]({file_ref})", 1)
            replaced += 1
        else:
            print(f"  [SKIP] {file_ref}: render failed, keeping original text", file=sys.stderr)

    if replaced > 0:
        spec_lock.write_text(new_text, encoding="utf-8")
    print(f"\nRendered {rendered} formula(s), replaced {replaced} in spec_lock.md.")
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render LaTeX formulas in spec_lock.md to transparent PNG images."
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Path to the project directory (must contain spec_lock.md).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be rendered without actually rendering or modifying files.",
    )
    args = parser.parse_args(argv)

    project = args.project_path.resolve()
    if not project.is_dir():
        print(f"Error: {project} is not a directory.", file=sys.stderr)
        return 1

    return 0 if process_spec_lock(project, dry_run=args.dry_run) >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
