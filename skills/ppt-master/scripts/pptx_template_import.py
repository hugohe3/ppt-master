#!/usr/bin/env python3
"""Unified PPTX preparation entry point for the /create-template workflow.

Reads OOXML directly via `pptx_to_svg` and writes a reusable reference workspace:

- `manifest.json` — single source of truth for slide size, theme colors, fonts,
  asset inventory, and per-slide / per-layout / per-master metadata
- `native_structure.json` + `source_template.pptx` — source-structure facts and
  a byte-identical analysis copy used to rebuild explicit SVG structure
- `summary.md` — short human-readable digest derived from manifest.json
- `assets/` — extracted reusable image assets
- `svg/` — primary view: by default the layered template view (every master
  and layout in the deck rendered once each as `master_*.svg` /
  `layout_*.svg`, slides contain only their own shapes, and an
  `inheritance.json` describes the reuse graph)
- `svg-flat/` — companion view (default mode "both"): each `slide_NN.svg`
  is self-contained — master/layout decoration is inlined — so opening any
  one slide shows the full page like PowerPoint would
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile

from console_encoding import configure_utf8_stdio
from template_import.manifest import build_manifest
from template_import.native_structure import write_native_structure_bundle

configure_utf8_stdio()


def parse_args() -> argparse.Namespace:
    """Build the CLI argument parser for the import entry point."""
    parser = argparse.ArgumentParser(
        description="Prepare a PPTX reference workspace for /create-template."
    )
    parser.add_argument("pptx_file", help="Path to the source .pptx file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: <pptx_stem>_template_import beside the source file)",
    )
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help=(
            "Skip metadata, asset inventory, native structure contract, and "
            "preserved source-package generation"
        ),
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help=(
            "Only extract manifest.json + summary.md + reusable assets + the "
            "native structure/source pair, without exporting slides to SVG"
        ),
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="Inline images as data: URIs instead of writing files to assets/",
    )
    parser.add_argument(
        "--inheritance-mode",
        choices=("both", "layered", "flat"),
        default="both",
        help=(
            "How to render master/layout shapes for slide SVGs. "
            "'both' (default): emit both views — svg/ holds the layered "
            "renderings (template designers see master/layout/slide as "
            "separate files plus svg/inheritance.json) and svg-flat/ holds "
            "self-contained per-slide SVGs (each one renders correctly when "
            "opened on its own). 'layered': only the svg/ tree, useful when "
            "you don't need the flat view. 'flat': only self-contained slide "
            "SVGs in svg/, the round-trip view used by svg_to_pptx."
        ),
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point: write the PPTX reference workspace to disk."""
    args = parse_args()
    pptx_path = Path(args.pptx_file).expanduser().resolve()
    if not pptx_path.exists():
        print(f"Error: file does not exist: {pptx_path}")
        return 1
    if pptx_path.suffix.lower() != ".pptx":
        print(f"Error: expected a .pptx file, got: {pptx_path.name}")
        return 1

    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else pptx_path.with_name(f"{pptx_path.stem}_template_import")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.skip_manifest and args.manifest_only:
        print("Error: --skip-manifest and --manifest-only cannot be used together")
        return 1

    manifest = None
    native_structure = None
    manifest_path = output_dir / "manifest.json"
    if not args.skip_manifest:
        try:
            manifest = build_manifest(pptx_path, output_dir)
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"Error: failed to extract PPTX metadata: {exc}")
            return 1

        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            native_structure = write_native_structure_bundle(
                pptx_path,
                output_dir,
                manifest,
            )
        except (OSError, ValueError) as exc:
            print(f"Error: failed to write native structure bundle: {exc}")
            return 1

    if args.manifest_only:
        print(f"Imported PPTX template source: {pptx_path.name}")
        print(f"Output directory: {output_dir}")
        if manifest is not None:
            print(f"Manifest: {manifest_path.name}")
            print("Native structure: native_structure.json")
            print("Source package analysis copy: source_template.pptx")
            print(
                "Source structure assessment: "
                f"{native_structure['strategy']['recommendedMode']}"
            )
            print("Template output mode: explicit SVG structure")
            print("Summary: summary.md")
            print(f"Assets exported: {len(manifest['assets']['allAssets'])}")
            print(f"Common assets: {len(manifest['assets']['commonAssets'])}")
            print(f"Slides analyzed: {len(manifest['slides'])}")
            print(f"Layouts (unique): {len(manifest.get('layouts', []))}")
            print(f"Masters (unique): {len(manifest.get('masters', []))}")
        return 0

    from pptx_to_svg import convert_pptx_to_svg
    from pptx_to_svg.converter import ConvertOptions

    options = ConvertOptions(
        media_subdir="assets",
        embed_images=args.embed_images,
        keep_hidden=False,
        inheritance_mode=args.inheritance_mode,
        asset_name_map=manifest.get("assets", {}).get("assetMap", {}) if manifest else {},
    )
    try:
        result = convert_pptx_to_svg(pptx_path, output_dir, options)
    except (BadZipFile, ET.ParseError, OSError, RuntimeError, ValueError) as exc:
        print(f"Error: failed to convert PPTX template source: {exc}")
        return 1
    total_bytes = sum(len(art.svg.encode("utf-8")) for art in result.slides)

    print(f"Inheritance mode: {args.inheritance_mode}")
    print(f"Exported SVG slides: {len(result.slides)}")
    if args.inheritance_mode in {"layered", "both"}:
        print(f"Exported masters: {len(result.masters)}")
        print(f"Exported layouts: {len(result.layouts)}")
        print("Inheritance graph: svg/inheritance.json")
    if result.flat_slides:
        print(f"Flat companion slides: {len(result.flat_slides)} (svg-flat/)")
    if result.diagnostics:
        print(
            f"Source recovery warnings: {len(result.diagnostics)} "
            "(conversion-report.json)"
        )
    print(f"SVG bytes (primary): {total_bytes}")
    print(f"Output directory: {output_dir}")
    if native_structure is not None:
        print(
            "Source structure assessment: "
            f"{native_structure['strategy']['recommendedMode']}; "
            "create-template rebuilds explicit SVG structure"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
