#!/usr/bin/env python3
"""
PPT Master - Template Preview PPTX Exporter

Export every SVG prototype in a template workspace as one structured review deck.

Usage:
    python3 scripts/template_preview_pptx.py <template_workspace> [-o output.pptx]

Examples:
    python3 scripts/template_preview_pptx.py projects/my_template
    python3 scripts/template_preview_pptx.py templates/decks/my_template -o review.pptx

Dependencies:
    python-pptx
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio


configure_utf8_stdio()

from pptx import Presentation  # noqa: E402

from svg_to_pptx.drawingml.theme_fonts import (  # noqa: E402
    MasterTextStyleSpec,
)
from svg_to_pptx.drawingml.utils import font_px_to_hpt  # noqa: E402
from svg_to_pptx.pptx_package.builder import (  # noqa: E402
    create_pptx_with_native_svg,
)


_FRONTMATTER_ID_RE = re.compile(
    r"^(?:template_id|deck_id|layout_id)\s*:\s*(.+?)\s*$",
    re.MULTILINE,
)
_FONT_SIZE_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)(?:px)?$")
_FILENAME_UNSAFE_RE = re.compile(r"[\\/:*?\"<>|\x00-\x1f]+")
_TITLE_PLACEHOLDERS = frozenset({"title", "subtitle"})
_BODY_PLACEHOLDERS = frozenset({
    "body",
    "date",
    "footer",
    "slide-number",
})
_DEFAULT_TITLE_PX = 40.0
_DEFAULT_BODY_PX = 24.0


def _resolve_workspace(path: Path) -> tuple[Path, Path]:
    """Resolve one workspace root and its canonical template-source directory."""
    candidate = path.expanduser().resolve()
    nested_spec = candidate / "templates" / "design_spec.md"
    if nested_spec.is_file():
        return candidate, candidate / "templates"

    direct_spec = candidate / "design_spec.md"
    if direct_spec.is_file():
        if candidate.name == "templates" and (candidate.parent / "exports").is_dir():
            return candidate.parent, candidate
        return candidate, candidate

    raise ValueError(
        "template workspace must contain templates/design_spec.md "
        "(current structure) or design_spec.md (legacy flat package)"
    )


def _template_id(spec_path: Path, workspace: Path) -> str:
    """Read a portable template id, falling back to the workspace directory name."""
    text = spec_path.read_text(encoding="utf-8")
    match = _FRONTMATTER_ID_RE.search(text)
    raw = match.group(1).strip().strip("'\"") if match else workspace.name
    safe = _FILENAME_UNSAFE_RE.sub("_", raw).strip(" ._")
    return safe or "template"


def _style_property(style: str, name: str) -> str | None:
    """Return one inline CSS declaration value."""
    for declaration in style.split(";"):
        key, separator, value = declaration.partition(":")
        if separator and key.strip().lower() == name:
            return value.strip()
    return None


def _font_size_px(element: ET.Element) -> float | None:
    """Read one finite positive SVG font size in px."""
    raw = element.get("font-size")
    if raw is None:
        raw = _style_property(element.get("style", ""), "font-size")
    if raw is None:
        return None
    match = _FONT_SIZE_RE.fullmatch(raw.strip())
    if match is None:
        return None
    value = float(match.group(1))
    return value if math.isfinite(value) and value > 0 else None


def _carrier_sizes(svg_files: list[Path]) -> tuple[list[float], list[float]]:
    """Collect authored title/body sizes from semantic placeholder carriers."""
    title_sizes: list[float] = []
    body_sizes: list[float] = []
    for svg_path in svg_files:
        root = ET.parse(svg_path).getroot()
        for slot in root.iter():
            placeholder = slot.get("data-pptx-placeholder")
            if placeholder not in _TITLE_PLACEHOLDERS | _BODY_PLACEHOLDERS:
                continue
            for carrier in slot.iter():
                if carrier.get("data-pptx-placeholder-carrier") != "true":
                    continue
                size = _font_size_px(carrier)
                if size is None:
                    continue
                target = title_sizes if placeholder in _TITLE_PLACEHOLDERS else body_sizes
                target.append(size)
    return title_sizes, body_sizes


def _master_text_style(svg_files: list[Path]) -> tuple[MasterTextStyleSpec, float, float]:
    """Build review-only Master text defaults without requiring a project lock."""
    title_sizes, body_sizes = _carrier_sizes(svg_files)
    title_px = float(statistics.median(title_sizes)) if title_sizes else _DEFAULT_TITLE_PX
    body_px = float(statistics.median(body_sizes)) if body_sizes else _DEFAULT_BODY_PX
    return (
        MasterTextStyleSpec(
            title_hpt=font_px_to_hpt(title_px),
            body_hpt=font_px_to_hpt(body_px),
        ),
        title_px,
        body_px,
    )


def _verify_output(output_path: Path) -> tuple[int, int, int]:
    """Reopen the review deck and return slide/master/layout counts."""
    presentation = Presentation(str(output_path))
    master_count = len(presentation.slide_masters)
    layout_count = sum(len(master.slide_layouts) for master in presentation.slide_masters)
    return len(presentation.slides), master_count, layout_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a complete template workspace as a structured PPTX review deck."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "template_workspace",
        help=(
            "Workspace containing templates/design_spec.md; legacy flat template "
            "directories are also accepted."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output PPTX path. Default: "
            "<template_workspace>/exports/<template_id>_template_preview.pptx"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing review PPTX after an intentional re-export.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        workspace, template_dir = _resolve_workspace(Path(args.template_workspace))
        svg_files = sorted(template_dir.glob("*.svg"))
        if not svg_files:
            raise ValueError(f"template directory has no SVG prototypes: {template_dir}")

        template_id = _template_id(template_dir / "design_spec.md", workspace)
        output_path = (
            Path(args.output).expanduser().resolve()
            if args.output
            else workspace / "exports" / f"{template_id}_template_preview.pptx"
        )
        if output_path.suffix.lower() != ".pptx":
            raise ValueError(f"output must use a .pptx extension: {output_path}")
        if output_path.exists() and not args.force:
            raise ValueError(
                f"output already exists: {output_path}; use --force to replace it"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        text_style, title_px, body_px = _master_text_style(svg_files)

        print("PPT Master - Template Preview PPTX Exporter")
        print(f"  Workspace: {workspace}")
        print(f"  Template source: {template_dir}")
        print(f"  SVG prototypes: {len(svg_files)}")
        print(f"  Review Master defaults: title {title_px:g}px, body {body_px:g}px")
        print(f"  Output: {output_path}")

        success = create_pptx_with_native_svg(
            svg_files=svg_files,
            output_path=output_path,
            canvas_format=None,
            verbose=True,
            transition=None,
            enable_notes=False,
            animation=None,
            image_optimize=False,
            native_objects=True,
            pptx_structure="structured",
            master_text_style_spec=text_style,
        )
        if not success or not output_path.is_file():
            print("Error: template preview export did not produce a PPTX", file=sys.stderr)
            return 1

        slide_count, master_count, layout_count = _verify_output(output_path)
        if slide_count != len(svg_files):
            print(
                "Error: review PPTX slide count does not match the template SVG roster "
                f"({slide_count} != {len(svg_files)})",
                file=sys.stderr,
            )
            return 1

        print(
            "[OK] Template preview verified: "
            f"{slide_count} slides, {master_count} master(s), {layout_count} layout(s)"
        )
        print(output_path)
        return 0
    except (OSError, ET.ParseError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
