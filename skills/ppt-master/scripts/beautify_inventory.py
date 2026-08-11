#!/usr/bin/env python3
"""
PPT Master - Beautify Inventory Builder

Mechanically merge a source deck's extracts into one per-slide ledger for the
beautify-pptx profile: text blocks + tables + charts + SmartArt structure (from a
`template_fill_pptx.py analyze` slide_library.json) joined with the images
bound to each slide (from a `ppt_to_md.py` image_manifest.json). The deterministic
join only — `ignored` and `needs_confirmation` are emitted empty for the agent
to fill with judgment (hidden shapes, combo charts, overcrowded pages, ...).

Usage:
    python3 scripts/beautify_inventory.py <slide_library.json> [--images <image_manifest.json>] [-o inventory.json]
    python3 scripts/beautify_inventory.py <inventory.json> --summary
    python3 scripts/beautify_inventory.py <inventory.json> --page N [--with-geometry]

Examples:
    python3 scripts/beautify_inventory.py projects/x/analysis/<stem>.slide_library.json \
        --images projects/x/images/image_manifest.json -o projects/x/analysis/beautify_inventory.json
    python3 scripts/beautify_inventory.py projects/x/analysis/beautify_inventory.json --summary
    python3 scripts/beautify_inventory.py projects/x/analysis/beautify_inventory.json --page 7

Dependencies:
    None (standard library only).

See workflows/profiles/beautify-pptx.md Step 4 for how the inventory is consumed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()


_GEOMETRY_KEYS = {
    "geometry",
    "display_ratio",
    "display_left_emu",
    "display_top_emu",
    "display_width_emu",
    "display_height_emu",
}


def _images_by_slide(manifest: list) -> dict[int, list[dict]]:
    """Map slide_index -> [image entries on that slide], from ppt_to_md occurrences."""
    by_slide: dict[int, list[dict]] = {}
    for entry in manifest:
        filename = entry.get("filename")
        for occ in entry.get("occurrences", []):
            idx = occ.get("slide_index")
            if idx is None:
                continue
            by_slide.setdefault(idx, []).append({
                "filename": filename,
                "shape_name": occ.get("shape_name"),
                "pixel_width": entry.get("pixel_width"),
                "pixel_height": entry.get("pixel_height"),
                "display_ratio": occ.get("display_ratio"),
                "display_left_emu": occ.get("display_left_emu"),
                "display_top_emu": occ.get("display_top_emu"),
                "display_width_emu": occ.get("display_width_emu"),
                "display_height_emu": occ.get("display_height_emu"),
                "usage_count": entry.get("usage_count"),
            })
    return by_slide


def _table_cells(table: dict) -> list[list[str]]:
    """Row-major 2D grid of cell text from a slide_library table."""
    grid = []
    for row in table.get("rows", []):
        grid.append([c.get("text", "") for c in row.get("cells", [])])
    return grid


def build_inventory(slide_library: dict, images_by_slide: dict[int, list[dict]]) -> dict:
    """Join slide_library slides with per-slide images into one ledger."""
    slides_out = []
    for slide in slide_library.get("slides", []):
        idx = slide.get("slide_index")
        text_blocks = [
            {
                "slot_id": s.get("slot_id"),
                "role": s.get("role"),
                "text": s.get("text", ""),
                "paragraph_count": s.get("paragraph_count"),
                "geometry": s.get("geometry"),
            }
            for s in slide.get("slots", [])
        ]
        tables = [
            {
                "table_id": t.get("table_id"),
                "row_count": t.get("row_count"),
                "column_count": t.get("column_count"),
                "cells": _table_cells(t),  # 2D text grid — convenient for diff
                "rows": t.get("rows", []),  # raw row/col cells — preserves merged / multi-header fidelity
            }
            for t in slide.get("tables", [])
        ]
        charts = [
            {
                "chart_id": c.get("chart_id"),
                "chart_type": c.get("chart_type"),
                "category_count": c.get("category_count"),
                "series_count": c.get("series_count"),
                "categories": c.get("categories", []),  # frozen data
                "series": c.get("series", []),           # frozen data (name + values)
            }
            for c in slide.get("charts", [])
        ]
        diagrams = [
            {
                "diagram_id": diagram.get("diagram_id"),
                "shape_name": diagram.get("shape_name"),
                "geometry": diagram.get("geometry"),
                "layout": diagram.get("layout", {}),
                "root_ids": diagram.get("root_ids", []),
                "nodes": diagram.get("nodes", []),
                "connections": diagram.get("connections", []),
                "status": diagram.get("status"),
                "warnings": diagram.get("warnings", []),
            }
            for diagram in slide.get("diagrams", [])
        ]
        slides_out.append({
            "slide_index": idx,
            "page_type": slide.get("page_type"),
            "text_blocks": text_blocks,
            "tables": tables,
            "charts": charts,
            "diagrams": diagrams,
            "images": images_by_slide.get(idx, []),
            "ignored": [],            # agent fills: hidden shapes, master-only text, image crop/rotation
            "needs_confirmation": [],  # agent fills: combo/dual-axis charts, merged-cell tables, overcrowded pages
        })

    return {
        "schema": "beautify_inventory.v1",
        "source": slide_library.get("source_pptx"),
        "slide_count": slide_library.get("slide_count", len(slides_out)),
        "canvas_px": slide_library.get("canvas_px"),
        "slides": slides_out,
    }


def _view_payload(inventory: dict, view: str, slides: list[dict]) -> dict:
    """Wrap projected slides with the canonical deck-level facts."""
    return {
        "schema": "beautify_inventory.view.v1",
        "inventory_schema": inventory.get("schema", "beautify_inventory.v1"),
        "view": view,
        "source": inventory.get("source"),
        "slide_count": inventory.get("slide_count", len(inventory.get("slides", []))),
        "canvas_px": inventory.get("canvas_px"),
        "slides": slides,
    }


def _summary_view(inventory: dict) -> dict:
    """Project the whole roster into compact per-slide counts and review flags."""
    slides = []
    for slide in inventory.get("slides", []):
        slides.append({
            "slide_index": slide.get("slide_index"),
            "page_type": slide.get("page_type"),
            "text_block_count": len(slide.get("text_blocks", [])),
            "table_count": len(slide.get("tables", [])),
            "chart_count": len(slide.get("charts", [])),
            "diagram_count": len(slide.get("diagrams", [])),
            "image_count": len(slide.get("images", [])),
            "ignored": slide.get("ignored", []),
            "needs_confirmation": slide.get("needs_confirmation", []),
        })
    return _view_payload(inventory, "summary", slides)


def _without_geometry(value: Any) -> Any:
    """Remove explicit source-layout geometry while preserving content and data."""
    if isinstance(value, dict):
        return {
            key: _without_geometry(item)
            for key, item in value.items()
            if key not in _GEOMETRY_KEYS
        }
    if isinstance(value, list):
        return [_without_geometry(item) for item in value]
    return value


def _page_view(inventory: dict, slide_index: int, with_geometry: bool) -> Optional[dict]:
    """Project one slide by its canonical slide_index."""
    for slide in inventory.get("slides", []):
        if slide.get("slide_index") != slide_index:
            continue
        projected = slide if with_geometry else _without_geometry(slide)
        return _view_payload(inventory, "page", [projected])
    return None


def _positive_int(value: str) -> int:
    """Parse a positive slide index for argparse."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("page must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a beautify inventory from a slide library, or print a read-only "
            "model view from a canonical beautify inventory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_json",
        help="slide_library.json in builder mode, or beautify_inventory.v1 JSON in a view mode",
    )
    parser.add_argument(
        "--images",
        help="image_manifest.json for a slide_library input (optional)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write the full built inventory here (builder mode only; default: stdout)",
    )
    view_group = parser.add_mutually_exclusive_group()
    view_group.add_argument(
        "--summary",
        action="store_true",
        help="Print deck facts, per-slide object counts, and review flags to stdout",
    )
    view_group.add_argument(
        "--page",
        type=_positive_int,
        metavar="N",
        help="Print one slide's frozen content/data by slide_index to stdout",
    )
    parser.add_argument(
        "--with-geometry",
        action="store_true",
        help="Retain source-layout geometry in a --page view",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    view_requested = args.summary or args.page is not None
    if view_requested and args.output:
        parser.error("--summary/--page write to stdout and cannot be combined with --output")
    if args.with_geometry and args.page is None:
        parser.error("--with-geometry requires --page")

    input_path = Path(args.input_json)
    if not input_path.is_file():
        print(f"[ERROR] input JSON not found: {input_path}", file=sys.stderr)
        return 1
    input_data = json.loads(input_path.read_text(encoding="utf-8"))

    input_schema = input_data.get("schema")
    if input_schema == "beautify_inventory.view.v1":
        parser.error(
            "beautify_inventory.view.v1 is a read-only stdout projection and "
            "cannot be used as input"
        )
    is_inventory = input_schema == "beautify_inventory.v1"
    if is_inventory and not view_requested:
        parser.error(
            "beautify_inventory.v1 input requires --summary or --page; "
            "builder mode requires slide_library.json"
        )
    if is_inventory and args.images:
        parser.error("--images cannot be combined with a beautify_inventory.v1 input")
    if view_requested and not is_inventory:
        parser.error("--summary/--page require a canonical beautify_inventory.v1 input")

    manifest: list = []
    if args.images and not is_inventory:
        img_path = Path(args.images)
        if not img_path.is_file():
            print(f"[ERROR] image manifest not found: {img_path}", file=sys.stderr)
            return 1
        manifest = json.loads(img_path.read_text(encoding="utf-8"))

    inventory = input_data if is_inventory else build_inventory(
        input_data,
        _images_by_slide(manifest),
    )

    if args.summary:
        print(json.dumps(_summary_view(inventory), ensure_ascii=False, indent=2))
        return 0
    if args.page is not None:
        page_view = _page_view(inventory, args.page, args.with_geometry)
        if page_view is None:
            available = ", ".join(
                str(slide.get("slide_index"))
                for slide in inventory.get("slides", [])
            )
            print(
                f"[ERROR] slide_index {args.page} not found; available: {available or 'none'}",
                file=sys.stderr,
            )
            return 1
        print(json.dumps(page_view, ensure_ascii=False, indent=2))
        return 0

    payload = json.dumps(inventory, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"[OK] inventory written to: {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
