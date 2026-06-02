"""PPTX template fill — analyze a deck as a reusable slide library and fill text.

Direct OOXML editing (no SVG round-trip): select source slides, replace
text / table / chart content from a fill plan, and write a new .pptx that keeps
the original PowerPoint design. Four stages mirror the CLI subcommands:
analyze -> scaffold -> check-plan -> apply.

Public entry: analyze_pptx(), scaffold_plan(), check_plan(), apply_plan(), main().
"""

from __future__ import annotations

from .analyzer import analyze_pptx
from .applier import apply_plan
from .checker import check_plan, print_check_report
from .cli import main
from .scaffolder import scaffold_plan

__all__ = [
    "analyze_pptx",
    "scaffold_plan",
    "check_plan",
    "print_check_report",
    "apply_plan",
    "main",
]
