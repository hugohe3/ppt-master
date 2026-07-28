#!/usr/bin/env python3
"""
PPT Master - Shape Boolean SVG Fragment Tool

Combine closed SVG shapes and print the resulting canonical SVG path fragment
to stdout. Result geometry is in SVG-root coordinate space: replace the
operands at their original z-order under the final semantic or structured
parent, never under the old transformed ancestor. The source SVG is read-only;
this tool never rewrites the page.

Usage:
    python3 scripts/shape_boolean_svg.py render SVG_FILE \
        --operation OPERATION --source ID --source ID --id OUTPUT_ID

Examples:
    python3 scripts/shape_boolean_svg.py render slide.svg \
        --operation intersect --source circle --source card --id overlap
    python3 scripts/shape_boolean_svg.py render slide.svg \
        --operation subtract --source body --source cutout --id result \
        --fill "#2563EB" --stroke none

Dependencies:
    skia-pathops and local PPT Master modules
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Sequence

from console_encoding import configure_utf8_stdio


configure_utf8_stdio()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print the Boolean result of closed SVG shapes as canonical SVG "
            "path fragments in SVG-root coordinate space. Insert the result at "
            "the original z-order under the final semantic or structured "
            "parent, never under the old transformed ancestor. The source file "
            "is never modified."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser(
        "render",
        help="Print SVG-root-coordinate Boolean-result paths to stdout.",
    )
    render_parser.add_argument(
        "svg_file",
        type=Path,
        help="Source SVG containing the operand elements.",
    )
    render_parser.add_argument(
        "--operation",
        required=True,
        choices=("union", "combine", "fragment", "intersect", "subtract"),
        help="PowerPoint-compatible merge-shapes operation.",
    )
    render_parser.add_argument(
        "--source",
        action="append",
        required=True,
        dest="source_ids",
        metavar="ID",
        help=(
            "Operand element id in merge order; repeat at least twice. "
            "The first operand is primary for subtract and style inheritance."
        ),
    )
    render_parser.add_argument(
        "--id",
        required=True,
        dest="output_id",
        help="Stable id for the result, or the base id for fragment results.",
    )
    render_parser.add_argument(
        "--fill",
        help="Override the primary shape's solid SVG fill, or use none.",
    )
    render_parser.add_argument(
        "--fill-opacity",
        type=float,
        help="Override fill opacity from 0 to 1.",
    )
    render_parser.add_argument(
        "--stroke",
        help="Override the primary shape's solid SVG stroke, or use none.",
    )
    render_parser.add_argument(
        "--stroke-width",
        type=float,
        help="Override stroke width in SVG page units.",
    )
    render_parser.add_argument(
        "--stroke-opacity",
        type=float,
        help="Override stroke opacity from 0 to 1.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        style = _style_from_args(args)
        _validate_render_args(args)
        from svg_to_pptx.shape_boolean import (
            render_boolean_svg_fragments,
        )

        fragment = render_boolean_svg_fragments(
            args.svg_file,
            operation=args.operation,
            source_ids=args.source_ids,
            output_id=args.output_id,
            style=style or None,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(fragment)
    return 0


def _validate_render_args(args: argparse.Namespace) -> None:
    if len(args.source_ids) < 2:
        raise ValueError("--source must be repeated at least twice")
    if len(set(args.source_ids)) != len(args.source_ids):
        raise ValueError("--source ids must be unique")
    if not args.output_id.strip():
        raise ValueError("--id must not be empty")


def _style_from_args(args: argparse.Namespace) -> dict[str, str]:
    style: dict[str, str] = {}
    if args.fill is not None:
        style["fill"] = args.fill
    if args.fill_opacity is not None:
        _validate_opacity("--fill-opacity", args.fill_opacity)
        style["fill-opacity"] = str(args.fill_opacity)
    if args.stroke is not None:
        style["stroke"] = args.stroke
    if args.stroke_width is not None:
        if not math.isfinite(args.stroke_width) or args.stroke_width < 0:
            raise ValueError("--stroke-width must be greater than or equal to 0")
        style["stroke-width"] = str(args.stroke_width)
    if args.stroke_opacity is not None:
        _validate_opacity("--stroke-opacity", args.stroke_opacity)
        style["stroke-opacity"] = str(args.stroke_opacity)
    return style


def _validate_opacity(option: str, value: float) -> None:
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{option} must be between 0 and 1")


if __name__ == "__main__":
    raise SystemExit(main())
