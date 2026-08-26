#!/usr/bin/env python3
"""Unified PPTX preparation entry point for the /create-template workflow.

Reads OOXML directly via `pptx_to_svg` and writes a reusable reference workspace:

- `analysis/manifest.json` — source of truth for slide size, theme, resources,
  image inventory, and per-slide / per-layout / per-master metadata
- `analysis/native_structure.json` + `sources/source.pptx` — source-structure
  facts and a byte-identical backing package
- `images/`, `audio/`, `sounds/`, `video/`, and `native-payloads/` — semantic
  source resources, created only when populated
- `validation/conversion-report.json` — source-recovery diagnostics emitted
  with SVG conversion
- `svg/` — canonical layered template view (every master
  and layout in the deck rendered once each as `master_*.svg` /
  `layout_*.svg`, slides contain only their own shapes, and an
  `inheritance.json` describes the reuse graph)
- `svg-flat/` — optional verification view (`--inheritance-mode both`): each
  `slide_NN.svg` is self-contained, so opening one slide shows the full page
  like PowerPoint would
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile

from console_encoding import configure_utf8_stdio
from pptx_workspace import (
    AUTHORING_SVG_DIR,
    AUTHORING_SVG_FLAT_DIR,
    CONVERSION_REPORT_PATH,
    TEMPLATE_MANIFEST_PATH,
    reject_removed_workspace_layout,
    template_manifest_path,
)
from template_import.manifest import build_manifest
from template_import.native_structure import (
    CONTRACT_NAME,
    SOURCE_TEMPLATE_NAME,
    write_native_structure_bundle,
)

configure_utf8_stdio()

_MANIFEST_NAME = TEMPLATE_MANIFEST_PATH.as_posix()
_CONVERSION_REPORT_NAME = CONVERSION_REPORT_PATH.as_posix()


def _project_authoring_directory(
    staged_dir: Path,
    *,
    source_dir: Path,
    output_dir: Path,
    projection_kind: str,
    id_prefix: str,
    reuse_inventory_path: Path | None = None,
) -> int:
    """Create one compact, readable authoring bundle in the transaction."""
    from extract_svg_assets import extract_directory
    from svg_authoring_view import project_svg_batch

    source_root = staged_dir / source_dir
    authoring_root = staged_dir / output_dir
    sources = sorted(source_root.rglob("*.svg"))
    if not sources:
        raise ValueError(f"No SVG files found under {source_root}")
    mapping = [
        (source, authoring_root / source.relative_to(source_root))
        for source in sources
    ]
    reports = project_svg_batch(
        mapping,
        source_root,
        authoring_root,
        force=False,
        projection_kind=projection_kind,
        source_proxy_dir=(
            staged_dir / "images" / "source-object-previews"
        ),
    )
    extract_directory(
        authoring_root,
        staged_dir / "icons",
        "imported",
        min_decoration_bytes=3000,
        inplace=True,
        id_prefix=id_prefix,
        inventory_path=(
            staged_dir / f"{output_dir.name}_vector_asset_inventory.json"
        ),
        reuse_inventory_path=reuse_inventory_path,
    )
    return len(reports)


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
            "Only extract analysis manifests, semantic resources, and the "
            "source-package bundle, without exporting slides to SVG"
        ),
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="Inline images as data: URIs instead of writing files to images/",
    )
    parser.add_argument(
        "--inheritance-mode",
        choices=("both", "layered", "flat"),
        default="layered",
        help=(
            "How to render master/layout shapes for slide SVGs. "
            "'layered' (default): emit the canonical svg/ tree with master, "
            "layout, and slide-local files plus svg/inheritance.json. "
            "'both': also emit svg-flat/ with self-contained per-slide "
            "verification files. In this mode svg/ still holds the layered "
            "renderings (template designers see master/layout/slide as "
            "separate files). 'flat': emit only projection-only, "
            "self-contained slide SVGs in svg/. Imported-deck round-trip "
            "uses the separate authoring-svg-flat/ contract."
        ),
    )
    return parser.parse_args()


def _managed_resource_paths(output_dir: Path) -> set[Path]:
    """Read the previous manifest's exact semantic-resource roster."""
    manifest_path = template_manifest_path(output_dir)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return set()
    if not isinstance(manifest, dict):
        return set()
    resources = manifest.get("resources")
    if isinstance(resources, dict) and isinstance(resources.get("items"), list):
        paths: set[Path] = set()
        allowed_roots = {
            "audio",
            "images",
            "native-payloads",
            "sounds",
            "video",
        }
        for item in resources["items"]:
            if not isinstance(item, dict):
                return set()
            value = item.get("workspacePath")
            if not isinstance(value, str):
                return set()
            path = Path(value)
            if (
                path.drive
                or path.anchor
                or path.is_absolute()
                or not path.parts
                or ".." in path.parts
                or path.parts[0] not in allowed_roots
            ):
                return set()
            paths.add(path)
        return paths

    return set()


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

    if args.skip_manifest and args.manifest_only:
        print("Error: --skip-manifest and --manifest-only cannot be used together")
        return 1

    try:
        reject_removed_workspace_layout(output_dir)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1
    previous_resources = _managed_resource_paths(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(
        prefix=f".{output_dir.name}.import-",
        dir=output_dir.parent,
    ))
    staged_dir = staging_root / "generated"
    staged_dir.mkdir()

    try:
        manifest = None
        native_structure = None
        manifest_path = staged_dir / _MANIFEST_NAME
        if not args.skip_manifest:
            try:
                manifest = build_manifest(
                    pptx_path,
                    staged_dir,
                    include_flat_svg=(
                        not args.manifest_only and args.inheritance_mode == "both"
                    ),
                )
            except (RuntimeError, OSError, ValueError) as exc:
                print(f"Error: failed to extract PPTX metadata: {exc}")
                return 1

            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            try:
                native_structure = write_native_structure_bundle(
                    pptx_path,
                    staged_dir,
                    manifest,
                )
            except (OSError, ValueError) as exc:
                print(f"Error: failed to write native structure bundle: {exc}")
                return 1

        result = None
        total_bytes = 0
        authoring_files = 0
        flat_authoring_files = 0
        if not args.manifest_only:
            from pptx_to_svg import convert_pptx_to_svg
            from pptx_to_svg.converter import ConvertOptions

            options = ConvertOptions(
                images_subdir="images",
                embed_images=args.embed_images,
                keep_hidden=False,
                inheritance_mode=args.inheritance_mode,
                asset_name_map=(
                    manifest.get("images", {}).get("imageMap", {})
                    if manifest else {}
                ),
            )
            try:
                result = convert_pptx_to_svg(pptx_path, staged_dir, options)
            except (BadZipFile, ET.ParseError, OSError, RuntimeError, ValueError) as exc:
                print(f"Error: failed to convert PPTX template source: {exc}")
                return 1
            total_bytes = sum(
                len(art.svg.encode("utf-8"))
                for art in result.slides
            )
            try:
                authoring_files = _project_authoring_directory(
                    staged_dir,
                    source_dir=Path("svg"),
                    output_dir=AUTHORING_SVG_DIR,
                    projection_kind=(
                        "flat" if args.inheritance_mode == "flat" else "layered"
                    ),
                    id_prefix="layered",
                )
                if args.inheritance_mode == "both":
                    flat_authoring_files = _project_authoring_directory(
                        staged_dir,
                        source_dir=Path("svg-flat"),
                        output_dir=AUTHORING_SVG_FLAT_DIR,
                        projection_kind="flat",
                        id_prefix="flat",
                        reuse_inventory_path=(
                            staged_dir
                            / f"{AUTHORING_SVG_DIR.name}_vector_asset_inventory.json"
                        ),
                    )
            except (ET.ParseError, OSError, RuntimeError, ValueError) as exc:
                print(f"Error: failed to create compact authoring SVG: {exc}")
                return 1

        from pptx_to_svg.converter import publish_staged_workspace

        try:
            publish_staged_workspace(
                output_dir,
                staged_dir,
                managed_root_files={
                    _MANIFEST_NAME,
                    CONTRACT_NAME,
                    SOURCE_TEMPLATE_NAME,
                    _CONVERSION_REPORT_NAME,
                },
                managed_relative_paths=previous_resources,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"Error: failed to publish PPTX template workspace: {exc}")
            return 1

        if args.manifest_only:
            print(f"Imported PPTX template source: {pptx_path.name}")
            print(f"Output directory: {output_dir}")
            if manifest is not None:
                print(f"Manifest: {_MANIFEST_NAME}")
                print(f"Native structure: {CONTRACT_NAME}")
                print(f"Source package analysis copy: {SOURCE_TEMPLATE_NAME}")
                print(
                    "Source structure assessment: "
                    f"{native_structure['strategy']['recommendedMode']}"
                )
                print("Template output mode: explicit SVG structure")
                print(f"Images exported: {len(manifest['images']['allImages'])}")
                print(f"Common images: {len(manifest['images']['commonImages'])}")
                print(f"Slides analyzed: {len(manifest['slides'])}")
                print(f"Layouts (unique): {len(manifest.get('layouts', []))}")
                print(f"Masters (unique): {len(manifest.get('masters', []))}")
            return 0

        print(f"Inheritance mode: {args.inheritance_mode}")
        print(f"Exported SVG slides: {len(result.slides)}")
        print(
            f"Compact authoring files: {authoring_files} "
            f"({AUTHORING_SVG_DIR}/)"
        )
        if args.inheritance_mode in {"layered", "both"}:
            print(f"Exported masters: {len(result.masters)}")
            print(f"Exported layouts: {len(result.layouts)}")
            print("Inheritance graph: svg/inheritance.json")
        if result.flat_slides:
            print(f"Flat companion slides: {len(result.flat_slides)} (svg-flat/)")
        if flat_authoring_files:
            print(
                f"Flat compact authoring files: {flat_authoring_files} "
                f"({AUTHORING_SVG_FLAT_DIR}/)"
            )
        if result.diagnostics:
            print(
                f"Source recovery warnings: {len(result.diagnostics)} "
                f"({_CONVERSION_REPORT_NAME})"
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
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
