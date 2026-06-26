"""PPTX template fill — analyze a deck as a reusable slide library and fill text.

Direct OOXML editing (no SVG round-trip): select source slides, replace
text / table / chart content from a fill plan, and write a new .pptx that keeps
the original PowerPoint design. CLI stages mirror the direct-PPTX workflow:
analyze -> scaffold -> check-plan -> apply -> validate.

Public entry: analyze_pptx(), scaffold_plan(), check_plan(), apply_plan(), main().
"""

from __future__ import annotations

from .analyzer import analyze_pptx
from .applier import apply_plan
from .checker import check_plan, print_check_report
from .cli import main
from .scaffolder import scaffold_plan
from .validator import print_validate_report, validate_project

__all__ = [
    "analyze_pptx",
    "scaffold_plan",
    "check_plan",
    "print_check_report",
    "apply_plan",
    "validate_project",
    "print_validate_report",
    "main",
]
