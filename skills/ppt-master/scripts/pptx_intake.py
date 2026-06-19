#!/usr/bin/env python3
"""
PPT Master - PPTX Intake Enrichment

Extract reusable PPTX intake facts into a standard analysis bundle. This is a
read-only companion to `ppt_to_md.py`: Markdown remains the content source,
while this bundle provides canvas, visual identity, slide geometry, tables, and
native chart data for downstream workflows.

Usage:
    python3 scripts/pptx_intake.py <source.pptx> -o <output_dir>

Examples:
    python3 scripts/pptx_intake.py deck.pptx -o projects/demo/analysis

Dependencies:
    None beyond the repository scripts used for PPTX parsing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from beautify_identity import extract_identity  # noqa: E402
from template_fill_pptx.analyzer import analyze_pptx  # noqa: E402


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _chart_summary(slide_library: dict[str, Any]) -> dict[str, Any]:
    charts: list[dict[str, Any]] = []
    total_series = 0
    multi_plot_count = 0
    for slide in slide_library.get("slides", []):
        for chart in slide.get("charts", []):
            series_count = int(chart.get("series_count") or 0)
            plot_types = chart.get("plot_types") or []
            if len(plot_types) > 1:
                multi_plot_count += 1
            total_series += series_count
            charts.append(
                {
                    "slide_index": slide.get("slide_index"),
                    "chart_id": chart.get("chart_id"),
                    "chart_type": chart.get("chart_type"),
                    "plot_types": plot_types,
                    "category_count": chart.get("category_count", 0),
                    "series_count": series_count,
                    "series_names": [
                        series.get("name")
                        for series in chart.get("series", [])
                        if series.get("name")
                    ],
                }
            )
    return {
        "chart_count": len(charts),
        "series_count": total_series,
        "multi_plot_chart_count": multi_plot_count,
        "charts": charts,
    }


def _table_summary(slide_library: dict[str, Any]) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    for slide in slide_library.get("slides", []):
        for table in slide.get("tables", []):
            tables.append(
                {
                    "slide_index": slide.get("slide_index"),
                    "table_id": table.get("table_id"),
                    "row_count": table.get("row_count", 0),
                    "column_count": table.get("column_count", 0),
                }
            )
    return {"table_count": len(tables), "tables": tables}


def build_source_profile(
    pptx_path: Path,
    identity: dict[str, Any],
    slide_library: dict[str, Any],
) -> dict[str, Any]:
    """Build the Strategist-facing digest over the raw intake artifacts."""
    return {
        "schema": "pptx_intake_profile.v1",
        "source_pptx": str(pptx_path),
        "slide_count": slide_library.get("slide_count", identity.get("slide_count", 0)),
        "usage_contract": {
            "standard_generation": (
                "Use identity and slide-library fields as source facts and recommendation "
                "candidates only; do not preserve original page count, order, or coordinates "
                "unless the user selected a beautify/template-fill workflow."
            ),
            "beautify": (
                "Promote source text, page order, page count, colors, and fonts into locked "
                "constraints after user confirmation."
            ),
            "template_fill": (
                "Use slide slots, tables, charts, and geometry as the native PPTX fill contract."
            ),
        },
        "artifacts": {
            "identity": "identity.json",
            "slide_library": "slide_library.json",
        },
        "canvas": identity.get("canvas", {}),
        "identity": {
            "theme_palette": (identity.get("theme") or {}).get("palette", {}),
            "theme_fonts": (identity.get("theme") or {}).get("fonts", {}),
            "observed_colors": (identity.get("observed") or {}).get("colors", []),
            "observed_fonts": (identity.get("observed") or {}).get("fonts", {}),
        },
        "structure": {
            "canvas_px": slide_library.get("canvas_px", {}),
            "page_types": [
                {
                    "slide_index": slide.get("slide_index"),
                    "page_type": slide.get("page_type"),
                    "slot_count": len(slide.get("slots", [])),
                }
                for slide in slide_library.get("slides", [])
            ],
        },
        "tables": _table_summary(slide_library),
        "charts": _chart_summary(slide_library),
    }


def run_intake(pptx_path: Path, output_dir: Path) -> dict[str, Path]:
    """Write `identity.json`, `slide_library.json`, and `source_profile.json`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    identity = extract_identity(pptx_path)
    slide_library = analyze_pptx(pptx_path)
    profile = build_source_profile(pptx_path, identity, slide_library)

    identity_path = output_dir / "identity.json"
    slide_library_path = output_dir / "slide_library.json"
    profile_path = output_dir / "source_profile.json"
    _write_json(identity_path, identity)
    _write_json(slide_library_path, slide_library)
    _write_json(profile_path, profile)
    return {
        "identity": identity_path,
        "slide_library": slide_library_path,
        "source_profile": profile_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract standard PPTX intake analysis artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", help="Source PPTX / PPTM / PPSX / PPSM / POTX / POTM file")
    parser.add_argument("-o", "--output-dir", required=True, help="Output project analysis directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        print(f"Error: source not found: {source}", file=sys.stderr)
        return 1
    try:
        outputs = run_intake(source, Path(args.output_dir).expanduser().resolve())
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"Error: PPTX intake failed: {exc}", file=sys.stderr)
        return 1
    print(f"PPTX intake -> {Path(args.output_dir).expanduser().resolve()}", file=sys.stderr)
    for name, path in outputs.items():
        print(f"  {name}: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
