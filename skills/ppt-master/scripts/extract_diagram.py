#!/usr/bin/env python3
"""CLI: extract a slide's diagram into a self-contained native-diagram component.

Usage::

    python3 scripts/extract_diagram.py <source.pptx> <slide_num> \
        [-o templates/native_diagrams/<key>] [--key <key>] [--summary "..."]

The component renders identically in any deck (theme dependencies flattened) and
stays natively editable. See ``native_diagrams/extract.py`` for the format.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from native_diagrams import extract_diagram


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract a native-diagram component from a .pptx slide.")
    ap.add_argument("source", help="Source .pptx file")
    ap.add_argument("slide_num", type=int, help="1-based slide number to lift")
    ap.add_argument("-o", "--output", help="Component dir (default: ./native_diagram_<slide_num>)")
    ap.add_argument("--key", help="Library key (default: output dir name)")
    ap.add_argument("--summary", default="", help="One-line selection summary for the index")
    args = ap.parse_args()

    out = Path(args.output) if args.output else Path(f"native_diagram_{args.slide_num}")
    meta = extract_diagram(args.source, args.slide_num, out, key=args.key, summary=args.summary)

    print()
    print("## Native Diagram Extracted")
    print()
    print(f"**Key**: {meta['key']}")
    print(f"**Source**: {meta['source']} (slide {meta['slide_num']})")
    print(f"**Path**: {out}")
    print(f"**Canvas (EMU)**: {meta['canvas_emu'][0]} x {meta['canvas_emu'][1]}")
    print(f"**Top-level shapes**: {meta['shape_count']}")
    print(f"**Theme flatten**: {meta['flatten']['colors']} schemeClr -> srgbClr "
          f"({meta['flatten']['colors_unresolved']} unresolved), "
          f"{meta['flatten']['fonts']} fonts")
    print(f"**Media files**: {len(meta['media'])}")
    if meta["charts_unsupported"]:
        print(f"**⚠ Charts not lifted (v1)**: {len(meta['charts_unsupported'])} graphicFrame chart(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
