#!/usr/bin/env python3
"""PPT Master - SVG Quality Check Tool

Stable CLI entry point and compatibility import surface for SVG validation.
Implementation lives in ``svg_quality/``.

Usage:
    python3 scripts/svg_quality_checker.py <svg_file>
    python3 scripts/svg_quality_checker.py <directory>
    python3 scripts/svg_quality_checker.py --all projects

Examples:
    python3 scripts/svg_quality_checker.py projects/demo --stage final --json

Dependencies:
    Same as svg_quality.cli.
"""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from attribution_guard import require_skill_integrity  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

from svg_quality.checker import (  # noqa: E402
    CANVAS_FORMATS,
    FONT_SIZE_ANCHOR_TOLERANCE_PX,
    HEX_VALUE_RE,
    IMAGE_DOWNSIZE_WARN_MIN_BYTES,
    IMAGE_DOWNSIZE_WARN_RATIO,
    SPARSE_UNDECLARED_FONT_SIZE_MAX_OCCURRENCES,
    SVG_NS,
    XLINK_NS,
    SVGQualityChecker,
)
from svg_quality.cli import main, print_usage  # noqa: E402

__all__ = [
    "CANVAS_FORMATS",
    "FONT_SIZE_ANCHOR_TOLERANCE_PX",
    "HEX_VALUE_RE",
    "IMAGE_DOWNSIZE_WARN_MIN_BYTES",
    "IMAGE_DOWNSIZE_WARN_RATIO",
    "SPARSE_UNDECLARED_FONT_SIZE_MAX_OCCURRENCES",
    "SVG_NS",
    "SVGQualityChecker",
    "XLINK_NS",
    "main",
    "print_usage",
]


if __name__ == "__main__":
    require_skill_integrity()
    main()
