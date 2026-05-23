#!/usr/bin/env python3
"""PPT Master - LaTeX Formula Renderer

Render LaTeX formulas in spec_lock.md to transparent PNG images
via the CodeCogs online LaTeX API (pdflatex quality).

A sidecar manifest (images/latex/manifest.json) records each formula's
pixel dimensions and type (inline/block) so the SVG executor can place
images at the correct scale.

Usage:
    python scripts/latex_render.py <project_path>
    python scripts/latex_render.py <project_path> --dry-run
    python scripts/latex_render.py <project_path> --dpi 400
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex patterns: $$...$$ (block) matched BEFORE $...$ (inline)
# ---------------------------------------------------------------------------
_RE_BLOCK = re.compile(r"\$\$([^$]+?)\$\$", re.DOTALL)
_RE_INLINE = re.compile(r"\$([^$\n]+?)\$")

_MANIFEST_NAME = "manifest.json"


def extract_formulas(text: str) -> list[tuple[str, str, bool]]:
    """Extract all formulas from text.

    Returns list of (full_match, latex_content, is_block).
    Block formulas ($$...$$) are extracted first, then inline ($...$).
    """
    results: list[tuple[str, str, bool]] = []
    claimed: list[tuple[int, int]] = []

    for m in _RE_BLOCK.finditer(text):
        results.append((m.group(0), m.group(1).strip(), True))
        claimed.append((m.start(), m.end()))

    for m in _RE_INLINE.finditer(text):
        if any(s <= m.start() < e for s, e in claimed):
            continue
        results.append((m.group(0), m.group(1).strip(), False))

    return results


def render_formula(latex: str, output_path: Path, dpi: int = 300) -> bool:
    """Render a single LaTeX formula to a transparent PNG via CodeCogs.

    Returns True on success, False on failure.
    """
    payload = rf"\dpi{{{dpi}}} {latex}"
    url = "https://latex.codecogs.com/png.latex?" + urllib.parse.quote(payload)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PPT-Master/1.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        if len(data) < 50:
            return False
        output_path.write_bytes(data)
        return True
    except Exception as exc:
        print(f"  [WARN] CodeCogs API failed for '{latex}': {exc}", file=sys.stderr)
        return False


def _image_dimensions(path: Path) -> tuple[int, int] | None:
    """Read PNG dimensions without full decode."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def process_spec_lock(
    project_path: Path,
    dry_run: bool = False,
    dpi: int = 300,
) -> int:
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
    seen: dict[str, str] = {}
    counter = 1
    replacements: list[tuple[str, str, str, bool]] = []  # + is_block

    for full_match, latex, is_block in formulas:
        if latex in seen:
            replacements.append((full_match, seen[latex], latex, is_block))
            continue
        file_ref = f"images/latex/F{counter:02d}.png"
        seen[latex] = file_ref
        replacements.append((full_match, file_ref, latex, is_block))
        counter += 1

    print(f"Found {len(replacements)} formula(s) ({len(seen)} unique).\n")

    if dry_run:
        for full_match, file_ref, latex, is_block in replacements:
            tag = "block" if is_block else "inline"
            print(f"  {file_ref} [{tag}]: {latex}")
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
        if render_formula(latex, out_path, dpi=dpi):
            print(f"  [OK]   {file_ref}: {latex}")
            rendered += 1
        else:
            print(f"  [FAIL] {file_ref}: render failed for '{latex}'",
                  file=sys.stderr)

    # Build manifest with dimensions + uniform scale factor
    manifest_formulas = {}
    heights: list[int] = []
    for latex, file_ref in seen.items():
        out_path = project_path / file_ref
        if not out_path.exists():
            continue
        dims = _image_dimensions(out_path)
        is_block = next(
            (ib for _, fr, _, ib in replacements if fr == file_ref), False
        )
        entry: dict = {"latex": latex, "type": "block" if is_block else "inline"}
        if dims:
            entry["width"] = dims[0]
            entry["height"] = dims[1]
            heights.append(dims[1])
        manifest_formulas[file_ref] = entry

    # Uniform scale factor: all formulas use the SAME scale so letter sizes
    # stay consistent.  Based on tallest formula → target display height.
    max_h = max(heights) if heights else 1
    target_display_height = 50  # px in SVG coordinate space
    uniform_scale = round(target_display_height / max_h, 4)

    manifest_path = latex_dir / _MANIFEST_NAME
    manifest = {
        "dpi": dpi,
        "uniform_scale": uniform_scale,
        "target_display_height": target_display_height,
        "max_source_height": max_h,
        "_comment": "Apply uniform_scale to ALL formula images so letter sizes stay consistent. Display size = source_size * uniform_scale.",
        "formulas": manifest_formulas,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                             encoding="utf-8")

    # Build set of formulas with valid PNGs
    rendered_ok: set[str] = set()
    for latex, file_ref in seen.items():
        if (project_path / file_ref).exists():
            rendered_ok.add(latex)

    # Replace only formulas whose PNG exists on disk
    new_text = text
    replaced = 0
    for full_match, file_ref, latex, _ in replacements:
        if latex in rendered_ok:
            new_text = new_text.replace(full_match, f"![]({file_ref})", 1)
            replaced += 1
        else:
            print(f"  [KEEP] {file_ref}: render failed, keeping original LaTeX",
                  file=sys.stderr)

    if replaced > 0:
        spec_lock.write_text(new_text, encoding="utf-8")
    print(f"\nRendered {rendered} formula(s), replaced {replaced} in spec_lock.md.")
    print(f"Manifest saved to {manifest_path}")
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
        help="Show what would be rendered without modifying files.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Rendering DPI (default: 300). Higher = larger output images.",
    )
    args = parser.parse_args(argv)

    project = args.project_path.resolve()
    if not project.is_dir():
        print(f"Error: {project} is not a directory.", file=sys.stderr)
        return 1

    return 0 if process_spec_lock(project, dry_run=args.dry_run, dpi=args.dpi) >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
