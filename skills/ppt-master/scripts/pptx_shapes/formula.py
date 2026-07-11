#!/usr/bin/env python3
"""
PPT Master - DrawingML Formula Evaluator

Evaluate DrawingML geometry guide formulas and standard built-in guides.

Usage:
    Import FormulaEvaluator or evaluate_formula from pptx_shapes.formula.

Examples:
    evaluator = FormulaEvaluator(width=200, height=100)
    evaluator.evaluate("*/ w 1 2")

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import math
import re
from types import MappingProxyType
from typing import Mapping

from .errors import (
    FormulaEvaluationError,
    FormulaSyntaxError,
    UnknownGuideError,
)


OOXML_DEGREE = 60000.0
FULL_CIRCLE = 360.0 * OOXML_DEGREE
OOXML_COORDINATE_MIN = -27273042329600
OOXML_COORDINATE_MAX = 27273042316900
OOXML_LINE_WIDTH_MAX = 20116800

_OPERATOR_ARITY = {
    "val": 1,
    "*/": 3,
    "+-": 3,
    "+/": 3,
    "?:": 3,
    "abs": 1,
    "at2": 2,
    "cat2": 3,
    "cos": 2,
    "max": 2,
    "min": 2,
    "mod": 3,
    "pin": 3,
    "sat2": 3,
    "sin": 2,
    "sqrt": 1,
    "tan": 2,
}
SUPPORTED_OPERATORS = frozenset(_OPERATOR_ARITY)

_DIMENSION_GUIDE_RE = re.compile(r"^(wd|hd|ssd)([1-9][0-9]*)$")
_ANGLE_GUIDE_RE = re.compile(r"^(?:(\d+))?cd([1-9][0-9]*)$")


def validate_ooxml_xfrm(
    off_x: int,
    off_y: int,
    ext_cx: int,
    ext_cy: int,
) -> None:
    """Validate DrawingML shape offsets and extents in EMU."""
    for name, value in (("x", off_x), ("y", off_y)):
        if not OOXML_COORDINATE_MIN <= value <= OOXML_COORDINATE_MAX:
            raise ValueError(
                f"DrawingML xfrm offset {name}={value} is outside the "
                "OOXML coordinate range"
            )
    for name, value in (("cx", ext_cx), ("cy", ext_cy)):
        if value < 0 or value > OOXML_COORDINATE_MAX:
            raise ValueError(
                f"DrawingML xfrm extent {name}={value} is outside the "
                "OOXML positive-coordinate range"
            )


def validate_ooxml_line_width(width: int) -> None:
    """Validate one DrawingML ``ST_LineWidth`` value in EMU."""
    if width < 0 or width > OOXML_LINE_WIDTH_MAX:
        raise ValueError(
            f"DrawingML line width {width} is outside the OOXML line-width range"
        )


def build_builtin_guides(
    width: float,
    height: float,
    *,
    left: float = 0.0,
    top: float = 0.0,
) -> Mapping[str, float]:
    """Build the standard DrawingML geometry guide context for one frame."""

    width = _finite_number(width, "width")
    height = _finite_number(height, "height")
    left = _finite_number(left, "left")
    top = _finite_number(top, "top")
    if width < 0 or height < 0:
        raise FormulaEvaluationError("Shape width and height must be non-negative")

    right = left + width
    bottom = top + height
    short_side = min(width, height)
    long_side = max(width, height)
    values = {
        "l": left,
        "t": top,
        "r": right,
        "b": bottom,
        "w": width,
        "h": height,
        "hc": left + width / 2.0,
        "vc": top + height / 2.0,
        "ss": short_side,
        "ls": long_side,
        "cd2": FULL_CIRCLE / 2.0,
        "cd3": FULL_CIRCLE / 3.0,
        "cd4": FULL_CIRCLE / 4.0,
        "cd8": FULL_CIRCLE / 8.0,
        "3cd4": FULL_CIRCLE * 3.0 / 4.0,
        "3cd8": FULL_CIRCLE * 3.0 / 8.0,
        "5cd8": FULL_CIRCLE * 5.0 / 8.0,
        "7cd8": FULL_CIRCLE * 7.0 / 8.0,
    }
    for divisor in (2, 3, 4, 5, 6, 8, 10, 12, 16, 32):
        values[f"wd{divisor}"] = width / divisor
        values[f"hd{divisor}"] = height / divisor
        values[f"ssd{divisor}"] = short_side / divisor
    return MappingProxyType(values)


class FormulaEvaluator:
    """Evaluate guide formulas against a shape-local DrawingML context."""

    def __init__(
        self,
        width: float,
        height: float,
        *,
        left: float = 0.0,
        top: float = 0.0,
        values: Mapping[str, float] | None = None,
    ) -> None:
        self._builtins = dict(
            build_builtin_guides(width, height, left=left, top=top)
        )
        self._values: dict[str, float] = {}
        if values:
            for name, value in values.items():
                self.bind(name, value)

    @property
    def values(self) -> Mapping[str, float]:
        """Return a detached, read-only view of explicitly bound guides."""

        return MappingProxyType(dict(self._values))

    @property
    def builtins(self) -> Mapping[str, float]:
        """Return the resolved built-in guide values."""

        return MappingProxyType(dict(self._builtins))

    def bind(self, name: str, value: float) -> float:
        """Bind one evaluated adjustment or guide and return its numeric value."""

        if not name or name.isspace():
            raise FormulaEvaluationError("Guide name must not be empty")
        number = _finite_number(value, f"guide {name!r}")
        self._values[name] = number
        return number

    def resolve(self, token: str) -> float:
        """Resolve a literal, bound guide, or DrawingML built-in guide token."""

        token = token.strip()
        if not token:
            raise UnknownGuideError("Guide token must not be empty")
        try:
            return _finite_number(float(token), f"literal {token!r}")
        except ValueError:
            pass

        if token in self._values:
            return self._values[token]
        if token in self._builtins:
            return self._builtins[token]

        dynamic = self._resolve_dynamic_builtin(token)
        if dynamic is not None:
            self._builtins[token] = dynamic
            return dynamic
        raise UnknownGuideError(f"Unknown DrawingML guide token: {token!r}")

    def evaluate(self, formula: str) -> float:
        """Evaluate one complete DrawingML geometry formula."""

        parts = formula.split()
        if not parts:
            raise FormulaSyntaxError("DrawingML formula must not be empty")
        operator = parts[0]
        expected = _OPERATOR_ARITY.get(operator)
        if expected is None:
            raise FormulaSyntaxError(
                f"Unsupported DrawingML formula operator: {operator!r}"
            )
        if len(parts) < expected + 1:
            raise FormulaSyntaxError(
                f"Operator {operator!r} expects {expected} operands, "
                f"received {len(parts) - 1}: {formula!r}"
            )
        trailing = parts[expected + 1 :]
        if trailing and not (
            operator == "+-" and all(token == "0" for token in trailing)
        ):
            raise FormulaSyntaxError(
                f"Operator {operator!r} expects {expected} operands, "
                f"received {len(parts) - 1}: {formula!r}"
            )
        # POI 5.4.1 carries three circular-arrow formulas with one inert
        # trailing zero ("+- xH 0 dxB 0"). Apache POI ignores surplus tokens;
        # accept only this harmless form while keeping all other arity errors.
        operands = tuple(self.resolve(token) for token in parts[1 : expected + 1])
        try:
            result = _apply_operator(operator, operands)
        except (OverflowError, ValueError) as exc:
            raise FormulaEvaluationError(
                f"Cannot evaluate DrawingML formula {formula!r}: {exc}"
            ) from exc
        return _finite_number(result, f"result of {formula!r}")

    def evaluate_value(self, value: str | int | float) -> float:
        """Evaluate a formula string, guide token, or numeric adjustment value."""

        if isinstance(value, str):
            parts = value.split()
            if not parts:
                raise FormulaSyntaxError("DrawingML value must not be empty")
            if parts[0] in SUPPORTED_OPERATORS:
                return self.evaluate(value)
            if len(parts) == 1:
                return self.resolve(parts[0])
            raise FormulaSyntaxError(f"Invalid DrawingML value: {value!r}")
        return _finite_number(value, "guide value")

    def _resolve_dynamic_builtin(self, token: str) -> float | None:
        dimension_match = _DIMENSION_GUIDE_RE.fullmatch(token)
        if dimension_match:
            family, divisor_text = dimension_match.groups()
            divisor = int(divisor_text)
            base_name = {"wd": "w", "hd": "h", "ssd": "ss"}[family]
            return self._builtins[base_name] / divisor

        angle_match = _ANGLE_GUIDE_RE.fullmatch(token)
        if angle_match:
            numerator_text, divisor_text = angle_match.groups()
            numerator = int(numerator_text or "1")
            divisor = int(divisor_text)
            return FULL_CIRCLE * numerator / divisor
        return None


def evaluate_formula(
    formula: str,
    *,
    width: float,
    height: float,
    left: float = 0.0,
    top: float = 0.0,
    values: Mapping[str, float] | None = None,
) -> float:
    """Evaluate one formula without manually constructing an evaluator."""

    evaluator = FormulaEvaluator(
        width,
        height,
        left=left,
        top=top,
        values=values,
    )
    return evaluator.evaluate(formula)


def _apply_operator(operator: str, values: tuple[float, ...]) -> float:
    if operator == "val":
        return values[0]
    if operator == "*/":
        return 0.0 if values[2] == 0 else values[0] * values[1] / values[2]
    if operator == "+-":
        return values[0] + values[1] - values[2]
    if operator == "+/":
        return 0.0 if values[2] == 0 else (values[0] + values[1]) / values[2]
    if operator == "?:":
        return values[1] if values[0] > 0 else values[2]
    if operator == "abs":
        return abs(values[0])
    if operator == "at2":
        return math.degrees(math.atan2(values[1], values[0])) * OOXML_DEGREE
    if operator == "cat2":
        return values[0] * math.cos(math.atan2(values[2], values[1]))
    if operator == "cos":
        return values[0] * math.cos(math.radians(values[1] / OOXML_DEGREE))
    if operator == "max":
        return max(values[0], values[1])
    if operator == "min":
        return min(values[0], values[1])
    if operator == "mod":
        return math.sqrt(sum(value * value for value in values))
    if operator == "pin":
        return max(values[0], min(values[1], values[2]))
    if operator == "sat2":
        return values[0] * math.sin(math.atan2(values[2], values[1]))
    if operator == "sin":
        return values[0] * math.sin(math.radians(values[1] / OOXML_DEGREE))
    if operator == "sqrt":
        return math.sqrt(values[0])
    if operator == "tan":
        return values[0] * math.tan(math.radians(values[1] / OOXML_DEGREE))
    raise FormulaSyntaxError(f"Unsupported DrawingML formula operator: {operator!r}")


def _finite_number(value: float, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise FormulaEvaluationError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise FormulaEvaluationError(f"{label} must be finite")
    return number
