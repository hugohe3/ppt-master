#!/usr/bin/env python3
"""CLI: inject a native-diagram component into a deck as native editable shapes.

Usage::

    # drop onto a fresh blank slide in a brand-new deck
    python3 scripts/inject_diagram.py <component_dir> -o out.pptx

    # append onto an existing deck (new blank slide by default)
    python3 scripts/inject_diagram.py <component_dir> -o out.pptx --target deck.pptx

    # place into an existing slide, re-framed into a rectangle (EMU)
    python3 scripts/inject_diagram.py <component_dir> -o out.pptx --target deck.pptx \
        --slide 2 --into-existing --pos 914400,914400,10363200,5029200

EMU reference: 914400 EMU = 1 inch; a 16:9 slide is 12192000 x 6858000.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from native_diagrams import inject_diagram


def _parse_pos(s: str | None):
    if not s:
        return None
    parts = [float(p) for p in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--pos must be x,y,w,h in EMU")
    return tuple(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Inject a native-diagram component into a deck.")
    ap.add_argument("component", help="Component dir produced by extract_diagram.py")
    ap.add_argument("-o", "--output", required=True, help="Output .pptx path")
    ap.add_argument("--target", help="Existing deck to append into (default: new blank deck)")
    ap.add_argument("--slide", type=int, help="0-based slide index when --into-existing")
    ap.add_argument("--into-existing", action="store_true",
                    help="Place into an existing slide instead of adding a new blank one")
    ap.add_argument("--pos", type=_parse_pos,
                    help="Reframe into x,y,w,h (EMU); omit to keep original coordinates")
    args = ap.parse_args()

    result = inject_diagram(
        args.component,
        args.output,
        target_pptx=args.target,
        slide_index=args.slide,
        new_slide=not args.into_existing,
        pos=args.pos,
    )

    print()
    print("## Native Diagram Injected")
    print()
    print(f"**Output**: {result['out']}")
    print(f"**Shapes injected**: {result['injected_shapes']}")
    print(f"**Media re-embedded**: {result['media']}")
    print(f"**Repositioned**: {result['repositioned']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
