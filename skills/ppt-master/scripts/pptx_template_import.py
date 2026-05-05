#!/usr/bin/env python3
"""Unified PPTX preparation entry point for the /create-template workflow.

Reads OOXML directly via `pptx_to_svg` and writes a reusable reference workspace:

- `manifest.json` — slide size, theme colors, fonts, asset inventory
- `master_layout_refs.json` / `master_layout_analysis.md` — master/layout structure
- `analysis.md` — page-type guidance
- `assets/` — extracted reusable image assets
- `svg/` — shape-level SVG per slide (real <text>, <image>, geometry)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from template_import.manifest import build_manifest


def parse_args() -> argparse.Namespace:
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
        help="Skip PPTX metadata extraction and asset inventory generation",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only extract manifest.json, analysis.md, and reusable assets without exporting slides to SVG",
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="Inline images as data: URIs instead of writing files to assets/",
    )
    return parser.parse_args()


def main() -> int:
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

    if not args.skip_manifest:
        try:
            manifest = build_manifest(pptx_path, output_dir)
        except Exception as exc:
            print(f"Error: failed to extract PPTX metadata: {exc}")
            return 1

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.manifest_only:
        print(f"Imported PPTX template source: {pptx_path.name}")
        print(f"Output directory: {output_dir}")
        if not args.skip_manifest:
            print(f"Manifest: {manifest_path.name}")
            print(f"Assets exported: {len(manifest['assets']['allAssets'])}")
            print(f"Common assets: {len(manifest['assets']['commonAssets'])}")
            print(f"Slides analyzed: {len(manifest['slides'])}")
        return 0

    from pptx_to_svg import convert_pptx_to_svg
    from pptx_to_svg.converter import ConvertOptions

    options = ConvertOptions(
        media_subdir="assets",
        embed_images=args.embed_images,
        keep_hidden=False,
    )
    result = convert_pptx_to_svg(pptx_path, output_dir, options)
    total_bytes = sum(len(art.svg.encode("utf-8")) for art in result.slides)

    print(f"Exported SVG slides: {len(result.slides)}")
    print(f"SVG bytes: {total_bytes}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
