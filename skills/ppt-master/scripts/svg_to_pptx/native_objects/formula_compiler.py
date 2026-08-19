#!/usr/bin/env python3
r"""
PPT Master - Native Formula Compiler

Compile the documented Microsoft 365 LaTeX input profile into editable block
or inline Office Math XML.

See references/native-formula.md for the owning authoring contract.

Usage:
    Import compile_latex_to_omml() or compile_latex_to_inline_omml() from the
    SVG-to-PPTX native-object pipeline.

Examples:
    compile_latex_to_omml(r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}")

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

from .formula_ast import (
    FormulaVerticalExtent,
    Sequence,
    formula_node_count,
    formula_vertical_extent,
)
from .formula_omml import emit_omml, validate_omml_fragment
from .formula_parser import FormulaCompileError, parse_latex_formula


_MAX_LATEX_LENGTH = 65_536
_MAX_AST_NODES = 100_000


def _parse_checked_formula(latex: str, *, display: bool) -> Sequence:
    if not isinstance(latex, str):
        raise FormulaCompileError("LaTeX formula must be a string")
    if len(latex) > _MAX_LATEX_LENGTH:
        raise FormulaCompileError(
            f"LaTeX formula exceeds the {_MAX_LATEX_LENGTH}-character limit"
        )
    try:
        expression = parse_latex_formula(latex, display=display)
        try:
            formula_node_count(expression, maximum=_MAX_AST_NODES)
        except ValueError as exc:
            raise FormulaCompileError(str(exc)) from exc
        return expression
    except RecursionError as exc:
        raise FormulaCompileError(
            "Formula nesting exceeds the supported limit"
        ) from exc


def _compile(latex: str, *, display: bool) -> str:
    expression = _parse_checked_formula(latex, display=display)
    try:
        return emit_omml(expression, display=display)
    except RecursionError as exc:
        raise FormulaCompileError(
            "Formula nesting exceeds the supported limit"
        ) from exc


def compile_latex_to_omml(latex: str) -> str:
    """Compile one standalone block formula into canonical m:oMathPara XML."""
    return _compile(latex, display=True)


def compile_latex_to_inline_omml(latex: str) -> str:
    """Compile one inline formula into canonical m:oMath XML."""
    return _compile(latex, display=False)


def estimate_inline_formula_vertical_extent(
    latex: str,
) -> FormulaVerticalExtent:
    """Estimate inline native-math bounds relative to its text baseline."""
    expression = _parse_checked_formula(latex, display=False)
    try:
        return formula_vertical_extent(expression)
    except RecursionError as exc:
        raise FormulaCompileError(
            "Formula nesting exceeds the supported limit"
        ) from exc


__all__ = [
    "FormulaCompileError",
    "compile_latex_to_inline_omml",
    "compile_latex_to_omml",
    "estimate_inline_formula_vertical_extent",
    "validate_omml_fragment",
]
