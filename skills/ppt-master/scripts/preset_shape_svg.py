#!/usr/bin/env python3
"""
PPT Master - Preset Shape SVG Fragment Tool

Browse and recommend DrawingML presets, or print compact canonical
native-preset SVG groups to stdout for manual insertion into a hand-authored
page or template.

Usage:
    python3 scripts/preset_shape_svg.py list [--grouped] [--search QUERY]
    python3 scripts/preset_shape_svg.py describe PRESET [--compact]
    python3 scripts/preset_shape_svg.py recommend --role ROLE [options] [--compact]
    python3 scripts/preset_shape_svg.py render PRESET --id ID --frame X Y W H
    python3 scripts/preset_shape_svg.py render-batch --input FILE_OR_DASH

Examples:
    python3 scripts/preset_shape_svg.py list --grouped
    python3 scripts/preset_shape_svg.py recommend --role spine \
        --relationship order --directionality horizontal --compact
    python3 scripts/preset_shape_svg.py describe rightArrow --compact
    python3 scripts/preset_shape_svg.py render rightArrow --id next-step \
        --frame 160 210 320 112 --fill "#2563EB" --stroke none
    python3 scripts/preset_shape_svg.py render-batch --input shapes.json

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from console_encoding import configure_utf8_stdio
from pptx_shapes import CONNECTOR_PRESET_TYPES, get_preset_registry
from pptx_shapes.semantics import (
    SEMANTIC_ASPECTS,
    SEMANTIC_DIRECTIONALITY,
    SEMANTIC_RELATIONSHIPS,
    SEMANTIC_ROLES,
    SEMANTIC_SCOPES,
    SEMANTIC_TEXT_CAPACITIES,
    SEMANTIC_VISUAL_WEIGHTS,
    get_preset_shape_semantics,
)
from pptx_to_svg.preset_authoring import render_preset_shape_fragment


configure_utf8_stdio()


_BATCH_ITEM_FIELDS = frozenset({
    "preset",
    "id",
    "frame",
    "object_kind",
    "name",
    "fill",
    "fill_opacity",
    "stroke",
    "stroke_width",
    "stroke_opacity",
    "stroke_linecap",
    "stroke_linejoin",
    "filter_id",
    "adjustments",
})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print one compact canonical DrawingML preset SVG group. "
            "This tool never writes SVG files or page layouts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List preset names, optionally filtered by substring.",
    )
    list_parser.add_argument(
        "--search",
        default="",
        help=(
            "Case-insensitive preset-name substring; grouped output also "
            "searches semantic text."
        ),
    )
    list_parser.add_argument(
        "--grouped",
        action="store_true",
        help=(
            "Print a compact Office-category and semantic-group index with "
            "one-line intent summaries and preset names as JSON."
        ),
    )

    describe_parser = subparsers.add_parser(
        "describe",
        help="Print preset geometry and semantic metadata as JSON.",
    )
    describe_parser.add_argument("preset", help="DrawingML preset name.")
    describe_parser.add_argument(
        "--compact",
        action="store_true",
        help=(
            "Print one flat selection view with semantic boundaries and key "
            "geometry facts."
        ),
    )

    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Recall semantically matched preset candidates as JSON.",
    )
    recommend_parser.add_argument(
        "--role",
        action="append",
        required=True,
        choices=SEMANTIC_ROLES,
        help="Required page role; repeat to allow multiple roles.",
    )
    recommend_parser.add_argument(
        "--relationship",
        action="append",
        default=[],
        choices=SEMANTIC_RELATIONSHIPS,
        help="Required relationship fit; repeat to allow alternatives.",
    )
    recommend_parser.add_argument(
        "--scope",
        choices=("all", *SEMANTIC_SCOPES),
        default="general",
        help=(
            "Semantic scope. The general default excludes literal-only, "
            "flowchart, and navigation shapes."
        ),
    )
    recommend_parser.add_argument(
        "--directionality",
        choices=SEMANTIC_DIRECTIONALITY,
        help="Required direction or route character.",
    )
    recommend_parser.add_argument(
        "--aspect",
        choices=SEMANTIC_ASPECTS,
        help="Required frame tendency; flexible candidates also match.",
    )
    recommend_parser.add_argument(
        "--text-capacity",
        choices=SEMANTIC_TEXT_CAPACITIES,
        help="Minimum useful text capacity.",
    )
    recommend_parser.add_argument(
        "--visual-weight",
        choices=SEMANTIC_VISUAL_WEIGHTS,
        help="Required visual-weight band.",
    )
    recommend_parser.add_argument(
        "--query",
        default="",
        help="Optional English intent terms used to refine the recall set.",
    )
    recommend_parser.add_argument(
        "--limit",
        type=_positive_integer,
        default=12,
        help="Maximum returned candidates; default: 12.",
    )
    recommend_parser.add_argument(
        "--compact",
        action="store_true",
        help=(
            "Print a reduced recall view for direct inspection without "
            "downstream parsing."
        ),
    )

    render_parser = subparsers.add_parser(
        "render",
        help="Print one canonical authored-preset <g> fragment to stdout.",
    )
    render_parser.add_argument("preset", help="DrawingML preset name.")
    render_parser.add_argument(
        "--id",
        required=True,
        dest="element_id",
        help="Stable unique SVG group id.",
    )
    render_parser.add_argument(
        "--frame",
        required=True,
        nargs=4,
        type=float,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
        help="SVG frame in the fragment's insertion coordinate space.",
    )
    render_parser.add_argument(
        "--object-kind",
        choices=("shape", "connector"),
        default="shape",
        help="Emit a normal shape or a native PowerPoint connector.",
    )
    render_parser.add_argument(
        "--name",
        help="Optional PowerPoint object name.",
    )
    render_parser.add_argument(
        "--fill",
        default="none",
        help="Solid SVG fill, or none.",
    )
    render_parser.add_argument(
        "--fill-opacity",
        type=float,
        help="Fill opacity from 0 to 1.",
    )
    render_parser.add_argument(
        "--stroke",
        default="none",
        help="Solid SVG stroke, or none.",
    )
    render_parser.add_argument(
        "--stroke-width",
        type=float,
        help="Stroke width in SVG page units; defaults to 1 when stroked.",
    )
    render_parser.add_argument(
        "--stroke-opacity",
        type=float,
        help="Stroke opacity from 0 to 1.",
    )
    render_parser.add_argument(
        "--stroke-linecap",
        choices=("butt", "round", "square"),
    )
    render_parser.add_argument(
        "--stroke-linejoin",
        choices=("miter", "round", "bevel"),
    )
    render_parser.add_argument(
        "--filter-id",
        help=(
            "Optional local SVG filter id for one registered native shadow or "
            "glow; the complete page must define it in direct <defs>."
        ),
    )
    render_parser.add_argument(
        "--adjust",
        action="append",
        default=[],
        metavar="NAME=FORMULA",
        help=(
            "DrawingML adjustment formula; repeat for multiple guides, "
            "for example --adjust 'adj1=val 50000'."
        ),
    )

    batch_parser = subparsers.add_parser(
        "render-batch",
        help="Print multiple canonical authored-preset fragments atomically.",
    )
    batch_parser.add_argument(
        "--input",
        required=True,
        metavar="FILE_OR_DASH",
        help=(
            "UTF-8 JSON array of shape objects; use - to read stdin. "
            "Use an 'adjustments' object such as "
            "{\"adj\": \"val 42000\"}; the command prints no fragments "
            "when any item is invalid."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    registry = get_preset_registry()

    if args.command == "list":
        if args.grouped:
            payload = get_preset_shape_semantics().grouped(args.search)
            if payload["preset_count"] == 0:
                print(f"No preset semantics match {args.search!r}", file=sys.stderr)
                return 1
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        query = args.search.casefold().strip()
        names = [
            name for name in registry.names
            if not query or query in name.casefold()
        ]
        if not names:
            print(f"No preset names match {args.search!r}", file=sys.stderr)
            return 1
        print("\n".join(names))
        return 0

    if args.command == "describe":
        if args.preset not in registry:
            print(f"Unknown DrawingML preset: {args.preset!r}", file=sys.stderr)
            return 1
        definition = registry.get(args.preset)
        adjustments = [
            {"name": guide.name, "formula": guide.formula}
            for guide in definition.adjustments
        ]
        connector_preset = definition.name in CONNECTOR_PRESET_TYPES
        path_count = len(definition.paths)
        connection_site_count = len(definition.connections)
        has_text_rectangle = definition.text_rectangle is not None
        semantics = get_preset_shape_semantics().describe(args.preset)
        full_payload = {
            "preset": definition.name,
            "connector_preset": connector_preset,
            "adjustments": adjustments,
            "path_count": path_count,
            "connection_site_count": connection_site_count,
            "has_text_rectangle": has_text_rectangle,
            "semantics": semantics,
        }
        payload = (
            {
                "preset": definition.name,
                "intent": semantics["intent"],
                "recommended_for": semantics["recommended_for"],
                "avoid_for": semantics["avoid_for"],
                "adjustments": adjustments,
                "connector_preset": connector_preset,
                "path_count": path_count,
                "connection_site_count": connection_site_count,
                "has_text_rectangle": has_text_rectangle,
            }
            if args.compact
            else full_payload
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "recommend":
        full_payload = get_preset_shape_semantics().recommend(
            roles=args.role,
            scope=args.scope,
            relationships=args.relationship,
            directionality=args.directionality,
            aspect=args.aspect,
            text_capacity=args.text_capacity,
            visual_weight=args.visual_weight,
            query=args.query,
            limit=args.limit,
        )
        payload = (
            {
                "criteria": full_payload["criteria"],
                "candidate_count": full_payload["candidate_count"],
                "returned_count": full_payload["returned_count"],
                "selection_note": full_payload["selection_note"],
                "candidates": [
                    {
                        "preset": candidate["preset"],
                        "scope": candidate["scope"],
                        "literal_only": candidate["literal_only"],
                        "intent": candidate["intent"],
                        "why": candidate["why"],
                        "avoid_for": candidate["avoid_for"],
                    }
                    for candidate in full_payload["candidates"]
                ],
            }
            if args.compact
            else full_payload
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "render-batch":
        try:
            items = _read_batch_items(args.input)
            fragments = _render_batch_items(items)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print("\n".join(fragments))
        return 0

    try:
        adjustments = _parse_adjustments(args.adjust)
        style = _style_from_args(args)
        fragment = render_preset_shape_fragment(
            args.preset,
            tuple(args.frame),
            adjustments=adjustments,
            object_kind=args.object_kind,
            element_id=args.element_id,
            name=args.name,
            style=style,
            filter_id=args.filter_id,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(fragment)
    return 0


def _parse_adjustments(values: Sequence[str]) -> dict[str, str]:
    adjustments: dict[str, str] = {}
    for value in values:
        name, separator, formula = value.partition("=")
        name = name.strip()
        formula = formula.strip()
        if not separator or not name or not formula:
            raise ValueError(
                f"Invalid adjustment {value!r}; expected NAME=FORMULA"
            )
        if name in adjustments:
            raise ValueError(f"Duplicate adjustment guide: {name!r}")
        adjustments[name] = formula
    return adjustments


def _positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def _style_from_args(args: argparse.Namespace) -> dict[str, str]:
    return _style_from_values(
        fill=args.fill,
        fill_opacity=args.fill_opacity,
        stroke=args.stroke,
        stroke_width=args.stroke_width,
        stroke_opacity=args.stroke_opacity,
        stroke_linecap=args.stroke_linecap,
        stroke_linejoin=args.stroke_linejoin,
    )


def _style_from_values(
    *,
    fill: object = "none",
    fill_opacity: object | None = None,
    stroke: object = "none",
    stroke_width: object | None = None,
    stroke_opacity: object | None = None,
    stroke_linecap: object | None = None,
    stroke_linejoin: object | None = None,
) -> dict[str, str]:
    fill_text = str(fill)
    stroke_text = str(stroke)
    style = {
        "fill": fill_text,
        "stroke": stroke_text,
    }
    if fill_opacity is not None:
        style["fill-opacity"] = str(fill_opacity)
    if stroke_text != "none":
        style["stroke-width"] = str(
            1.0 if stroke_width is None else stroke_width
        )
    elif stroke_width is not None:
        raise ValueError("--stroke-width requires a non-none --stroke")
    if stroke_opacity is not None:
        style["stroke-opacity"] = str(stroke_opacity)
    if stroke_linecap is not None:
        style["stroke-linecap"] = str(stroke_linecap)
    if stroke_linejoin is not None:
        style["stroke-linejoin"] = str(stroke_linejoin)
    return style


def _read_batch_items(input_path: str) -> list[object]:
    """Read one JSON array from a path or stdin."""
    try:
        raw = (
            sys.stdin.read()
            if input_path == "-"
            else Path(input_path).read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise ValueError(f"Cannot read batch input {input_path!r}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid batch JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(payload, list) or not payload:
        raise ValueError("Batch input must be a non-empty JSON array")
    return payload


def _render_batch_items(items: Sequence[object]) -> list[str]:
    """Validate every batch item, then return all fragments together."""
    fragments: list[str] = []
    element_ids = set()
    for index, raw_item in enumerate(items):
        label = f"items[{index}]"
        if not isinstance(raw_item, dict):
            raise ValueError(f"{label} must be a JSON object")
        unknown = sorted(set(raw_item) - _BATCH_ITEM_FIELDS)
        if unknown:
            supported = ", ".join(sorted(_BATCH_ITEM_FIELDS))
            raise ValueError(
                f"{label} has unsupported fields: {', '.join(unknown)}; "
                f"supported fields: {supported}"
            )
        missing = [
            name for name in ("preset", "id", "frame")
            if name not in raw_item
        ]
        if missing:
            raise ValueError(f"{label} is missing: {', '.join(missing)}")

        element_id = str(raw_item["id"])
        if element_id in element_ids:
            raise ValueError(f"{label} duplicates SVG element id {element_id!r}")
        element_ids.add(element_id)
        frame = raw_item["frame"]
        if not isinstance(frame, list) or len(frame) != 4:
            raise ValueError(f"{label}.frame must be a four-number JSON array")
        adjustments = raw_item.get("adjustments", {})
        if not isinstance(adjustments, dict):
            raise ValueError(f"{label}.adjustments must be a JSON object")

        try:
            style = _style_from_values(
                fill=raw_item.get("fill", "none"),
                fill_opacity=raw_item.get("fill_opacity"),
                stroke=raw_item.get("stroke", "none"),
                stroke_width=raw_item.get("stroke_width"),
                stroke_opacity=raw_item.get("stroke_opacity"),
                stroke_linecap=raw_item.get("stroke_linecap"),
                stroke_linejoin=raw_item.get("stroke_linejoin"),
            )
            fragment = render_preset_shape_fragment(
                str(raw_item["preset"]),
                tuple(frame),
                adjustments=adjustments,
                object_kind=str(raw_item.get("object_kind", "shape")),
                element_id=element_id,
                name=(
                    str(raw_item["name"])
                    if raw_item.get("name") is not None
                    else None
                ),
                style=style,
                filter_id=(
                    str(raw_item["filter_id"])
                    if raw_item.get("filter_id") is not None
                    else None
                ),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label}: {exc}") from exc
        fragments.append(fragment)
    return fragments


if __name__ == "__main__":
    raise SystemExit(main())
