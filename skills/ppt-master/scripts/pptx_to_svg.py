#!/usr/bin/env python3
"""CLI entry: convert a .pptx file to one SVG per slide.

Usage:
    python3 pptx_to_svg.py <pptx_file> [-o <output_dir>] [--embed-images]
                                       [--images-subdir <name>] [--keep-hidden]
                                       [--inheritance-mode {both,layered,flat}]
                                       [--roundtrip]
                                       [--strict]

Output structure (``--roundtrip``):
    <output_dir>/
        authoring-svg-flat/     sole editable SVG page source
        icons/imported/         on-demand complex vector decorations
        authoring-svg-flat_vector_asset_inventory.json
                                extracted-decoration source mapping
        animations.json         normalized transition/object-motion sidecar
        images/                 raster/SVG/EMF/WMF picture resources
        sounds/                 transition/object cue audio, when present
        audio/                  source narration/media audio, when present
        video/                  source video bytes, when present
        notes/                  imported speaker notes, when present
        native-payloads/        opaque source payloads, when present
        analysis/               structure, manifests, and immutable SVG backing
        validation/             conversion diagnostics
        sources/source.pptx     immutable backing package in --roundtrip

If -o is omitted, writes alongside the source file as <pptx_stem>_pptx_to_svg/.

This is the semantic import counterpart to svg_to_pptx.py: it reads OOXML
directly and emits declared SVG/native-marker subsets without claiming an
arbitrary lossless PPTX round trip.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile

# Allow running this script from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent))

from console_encoding import configure_utf8_stdio
from pptx_workspace import (
    AUTHORING_SVG_FLAT_DIR,
    CONVERSION_REPORT_PATH,
    NATIVE_STRUCTURE_PATH,
    SOURCE_PPTX_PATH,
)
from pptx_to_svg import convert_pptx_to_svg
from pptx_to_svg.converter import ConvertOptions

configure_utf8_stdio()


def _diagnostic_preview(message: str, limit: int = 240) -> str:
    """Return one compact CLI preview while the report retains full detail."""
    compact = " ".join(message.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _reconstruction_only_graphics(result: object) -> list[tuple[int, str]]:
    """Return slide/object labels for generated placeholders."""
    artifacts = getattr(result, "flat_slides", None) or getattr(result, "slides", [])
    diagnostics: list[tuple[int, str]] = []
    for artifact in artifacts:
        try:
            root = ET.fromstring(artifact.svg)
        except ET.ParseError:
            continue
        for elem in root.iter():
            fallback_kind = (
                elem.get("data-pptx-fallback-kind")
                or elem.get("data-pptx-visual-status")
            )
            if fallback_kind != "placeholder":
                continue
            marker_id = elem.get("id") or elem.get("data-name") or "<unnamed>"
            diagnostics.append((artifact.index, marker_id))
    return diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert .pptx to per-slide SVG by reading OOXML directly.",
    )
    parser.add_argument("pptx_file", help="Path to the source .pptx file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: <pptx_stem>_pptx_to_svg beside source)",
    )
    parser.add_argument(
        "--images-subdir",
        default="images",
        help="Subdirectory for extracted image resources (default: images)",
    )
    parser.add_argument(
        "--sounds-subdir",
        default="sounds",
        help="Subdirectory for transition/object cue audio (default: sounds)",
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="Base64-embed images inline instead of writing files",
    )
    parser.add_argument(
        "--keep-hidden",
        action="store_true",
        help='Include shapes marked hidden="1"',
    )
    parser.add_argument(
        "--inheritance-mode",
        choices=("both", "layered", "flat"),
        default="both",
        help=(
            "How to render inheritance. 'both' (default) writes layered SVGs "
            "under svg/ and complete preview slides under svg-flat/. "
            "'layered' writes only svg/ plus inheritance.json. 'flat' writes "
            "self-contained slides under svg/. Round-trip import requires "
            "'both' internally and publishes authoring-svg-flat/ as its sole "
            "editable SVG source."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Stop on the first unsupported/malformed source construct instead "
            "of the default tolerant conversion with diagnostics"
        ),
    )
    parser.add_argument(
        "--roundtrip",
        action="store_true",
        help=(
            "Create the source-preserving SVG round-trip workspace, including "
            "authoring-svg-flat/, semantic resources, and immutable analysis "
            "backing. Requires --inheritance-mode both."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pptx_path = Path(args.pptx_file).expanduser().resolve()
    if not pptx_path.exists():
        print(f"Error: file does not exist: {pptx_path}", file=sys.stderr)
        return 1
    if pptx_path.suffix.lower() != ".pptx":
        print(f"Error: expected a .pptx file, got: {pptx_path.name}", file=sys.stderr)
        return 1

    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else pptx_path.with_name(f"{pptx_path.stem}_pptx_to_svg")
    )

    options = ConvertOptions(
        images_subdir=args.images_subdir,
        sound_subdir=args.sounds_subdir,
        embed_images=args.embed_images,
        keep_hidden=args.keep_hidden,
        inheritance_mode=args.inheritance_mode,
        strict=args.strict,
        roundtrip=args.roundtrip,
    )

    try:
        result = convert_pptx_to_svg(pptx_path, output_dir, options)
    except (BadZipFile, ET.ParseError, OSError, RuntimeError, ValueError) as exc:
        print(f"Error: PPTX-to-SVG conversion failed: {exc}", file=sys.stderr)
        return 1

    print(f"Source: {pptx_path.name}")
    print(f"Canvas: {result.canvas_px[0]:.0f} x {result.canvas_px[1]:.0f} px")
    if result.theme_colors:
        scheme = ", ".join(f"{k}={v}" for k, v in sorted(result.theme_colors.items()))
        print(f"Theme colors: {scheme}")
    if result.theme_fonts:
        fonts = ", ".join(f"{k}={v}" for k, v in result.theme_fonts.items())
        print(f"Theme fonts: {fonts}")
    print(f"Slides converted: {len(result.slides)}")
    if result.diagnostics:
        print(
            f"Warning: {len(result.diagnostics)} source construct(s) were "
            "normalized, omitted, or replaced; see the validation report.",
            file=sys.stderr,
        )
        for item in result.diagnostics[:20]:
            location = (
                f"slide {item.slide_index}"
                if item.slide_index
                else item.part_path
            )
            shape = item.shape_name or item.shape_id
            if shape:
                location = f"{location}, {shape}" if location else shape
            print(
                f"  {location or 'package'}: {item.code}: "
                f"{_diagnostic_preview(item.message)}",
                file=sys.stderr,
            )
        if len(result.diagnostics) > 20:
            print(
                f"  ... and {len(result.diagnostics) - 20} more",
                file=sys.stderr,
            )
    reconstruction_only = _reconstruction_only_graphics(result)
    if reconstruction_only:
        print(
            "Warning: chart placeholder(s) without a baked preview are "
            "reconstruction-only. Default export keeps the placeholder; "
            "--native-charts-and-tables may reconstruct entries with a valid "
            "replacement marker:",
            file=sys.stderr,
        )
        for slide_index, marker_id in reconstruction_only[:20]:
            print(f"  slide {slide_index}: {marker_id}", file=sys.stderr)
        if len(reconstruction_only) > 20:
            print(
                f"  ... and {len(reconstruction_only) - 20} more",
                file=sys.stderr,
            )
    print(f"Output: {output_dir}")
    print(f"Animation config: {output_dir / 'animations.json'}")
    print(f"Conversion report: {output_dir / CONVERSION_REPORT_PATH}")
    if result.native_structure is not None:
        print(f"Editable SVG source: {output_dir / AUTHORING_SVG_FLAT_DIR}")
        print(f"Round-trip source: {output_dir / SOURCE_PPTX_PATH}")
        print(f"Round-trip structure: {output_dir / NATIVE_STRUCTURE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
