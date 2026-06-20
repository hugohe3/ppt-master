#!/usr/bin/env python3
"""
PPT Master - Beautify Inventory Builder

Mechanically merge a source deck's extracts into one per-slide ledger for the
beautify-pptx workflow: text blocks + tables + charts (from a
`template_fill_pptx.py analyze` slide_library.json) joined with the images
bound to each slide (from a `ppt_to_md.py` image_manifest.json). The deterministic
join only — `ignored` and `needs_confirmation` are emitted empty for the agent
to fill with judgment (hidden shapes, combo charts, overcrowded pages, ...).

Usage:
    python3 scripts/beautify_inventory.py <slide_library.json> [--images <image_manifest.json>] [-o inventory.json]

Examples:
    python3 scripts/beautify_inventory.py projects/x/analysis/<stem>.slide_library.json \
        --images projects/x/images/image_manifest.json -o projects/x/analysis/beautify_inventory.json

Dependencies:
    None (standard library only).

See workflows/beautify-pptx.md Step 4 for how the inventory is consumed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


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
        slides_out.append({
            "slide_index": idx,
            "page_type": slide.get("page_type"),
            "text_blocks": text_blocks,
            "tables": tables,
            "charts": charts,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge slide_library.json + image_manifest.json into a per-slide beautify inventory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("slide_library", help="slide_library.json from `template_fill_pptx.py analyze`")
    parser.add_argument("--images", help="image_manifest.json from `ppt_to_md.py` (optional)")
    parser.add_argument("-o", "--output", help="Write JSON here (default: stdout)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    lib_path = Path(args.slide_library)
    if not lib_path.is_file():
        print(f"[ERROR] slide_library not found: {lib_path}", file=sys.stderr)
        return 1
    slide_library = json.loads(lib_path.read_text(encoding="utf-8"))

    manifest: list = []
    if args.images:
        img_path = Path(args.images)
        if not img_path.is_file():
            print(f"[ERROR] image manifest not found: {img_path}", file=sys.stderr)
            return 1
        manifest = json.loads(img_path.read_text(encoding="utf-8"))

    inventory = build_inventory(slide_library, _images_by_slide(manifest))

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
