#!/usr/bin/env python3
"""
PPT Master - Legacy Chart Recall Compatibility

Preserve the historical broad chart-recall CLI while delegating to the unified
visualization recall implementation. Published Structure bare keys validate as
intent-only compatibility values; they do not recall or load SVG assets. The
legacy ``valid`` list remains intact while ``resolved`` exposes each kind.

Usage:
    python3 scripts/chart_recall.py recall --page P03 --tag "time series" --tag "three metrics" --tag "trend"
    python3 scripts/chart_recall.py validate line_chart column_chart

Examples:
    python3 scripts/chart_recall.py validate process_flow

Dependencies:
    None (only uses the standard library)
"""

from __future__ import annotations

from visualization_recall import main


if __name__ == "__main__":
    raise SystemExit(main(legacy_output=True))
