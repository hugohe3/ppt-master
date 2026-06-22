#!/usr/bin/env python3
"""
PPT Master - Point-to-Pixel Font Size Converter

Deterministic pt <-> SVG-px font-size conversion, the single source of truth for
the chat-fallback path of the Eight Confirmations (the Confirm UI does the same
math in app.js at submit time). PPT canvases confirm font sizes in pt; the
execution layer (design_spec.md / spec_lock.md / SVG) carries unitless px only.
Convert here instead of mental arithmetic so the chat path matches the UI path.

  px = pt * 4 / 3   (the inverse of the exporter's px * 0.75; canvas 1280px -> 960pt slide)

Rounding matches app.js `roundSize` (2 decimals, round-half-up), so a value
confirmed in pt round-trips back to the same pt at export.

Usage:
    python3 scripts/pt_to_px.py <pt> [<pt> ...]
    python3 scripts/pt_to_px.py --reverse <px> [<px> ...]

Examples:
    python3 scripts/pt_to_px.py 20            # -> 26.67   (write into spec_lock body)
    python3 scripts/pt_to_px.py 20 36 27 15   # body title subtitle annotation -> 26.67 48 36 20
    python3 scripts/pt_to_px.py --reverse 26.67   # -> 20   (what PowerPoint will display)

Dependencies:
    None (only uses standard library)

See references/strategist.md §g (Font Size Ramp) for the pt/px unit boundary.
"""

import sys
import math
import argparse
from typing import Optional

PT_TO_PX = 4 / 3        # px = pt * 4/3
PX_TO_PT = 0.75         # pt = px * 0.75 (mirrors svg_to_pptx FONT_PX_TO_HUNDREDTHS_PT)


def _round_half_up(value: float, decimals: int = 2) -> float:
    """Round half-up to ``decimals`` places, matching app.js ``Math.round``."""
    factor = 10 ** decimals
    return math.floor(value * factor + 0.5) / factor


def pt_to_px(pt: float) -> float:
    """Convert a pt font size to its unitless SVG px value."""
    return _round_half_up(pt * PT_TO_PX)


def px_to_pt(px: float) -> float:
    """Convert an SVG px font size back to the pt PowerPoint will display."""
    return _round_half_up(px * PX_TO_PT)


def _fmt(value: float) -> str:
    """Drop a trailing ``.0`` so integers print clean (32, not 32.0)."""
    return str(int(value)) if value == int(value) else f"{value:.2f}"


def _parse_size(raw: str) -> float:
    """Accept a bare number or a value with a stray pt/px suffix."""
    return float(raw.strip().lower().removesuffix("pt").removesuffix("px").strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert pt font sizes to unitless SVG px (or back with --reverse).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("sizes", nargs="+", help="One or more font sizes to convert.")
    parser.add_argument(
        "-r", "--reverse", action="store_true",
        help="Convert px -> pt instead of pt -> px (debug / verification).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    convert = px_to_pt if args.reverse else pt_to_px
    try:
        values = [convert(_parse_size(s)) for s in args.sizes]
    except ValueError:
        print("Error: every size must be a number (optionally suffixed pt/px).",
              file=sys.stderr)
        return 1
    print(" ".join(_fmt(v) for v in values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
