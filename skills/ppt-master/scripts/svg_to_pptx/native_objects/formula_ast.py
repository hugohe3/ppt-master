#!/usr/bin/env python3
"""
PPT Master - Native Formula Abstract Syntax Tree

Define the internal math nodes shared by the Microsoft 365 LaTeX parser,
chemistry parser, and OMML emitter.

See references/native-formula.md for the owning authoring contract.

Usage:
    Imported by native formula compiler modules.

Examples:
    expression = Sequence((Text("x"),))

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunStyle:
    style: str | None = None
    normal: bool | None = None
    script: str | None = None
    color: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    typeface: str | None = None
    is_default: bool = False


@dataclass(frozen=True)
class Text:
    value: str
    style: RunStyle | None = None
    literal: bool = False


@dataclass(frozen=True)
class Sequence:
    children: tuple[Node, ...]


@dataclass(frozen=True)
class Styled:
    body: Sequence
    style: RunStyle


@dataclass(frozen=True)
class Fraction:
    numerator: Sequence
    denominator: Sequence
    kind: str = "bar"


@dataclass(frozen=True)
class Radical:
    body: Sequence
    degree: Sequence | None = None


@dataclass(frozen=True)
class Script:
    base: Node
    subscript: Sequence | None = None
    superscript: Sequence | None = None


@dataclass(frozen=True)
class Prescript:
    base: Node
    subscript: Sequence | None = None
    superscript: Sequence | None = None


@dataclass(frozen=True)
class Nary:
    symbol: str
    category: str
    subscript: Sequence | None = None
    superscript: Sequence | None = None
    body: Sequence | None = None
    limit_modifier: str | None = None


@dataclass(frozen=True)
class Delimiter:
    left: str
    right: str
    segments: tuple[Sequence, ...]
    separator: str = ""


@dataclass(frozen=True)
class Matrix:
    environment: str
    rows: tuple[tuple[Sequence, ...], ...]
    column_alignments: tuple[str, ...] = ()


@dataclass(frozen=True)
class AlignmentPoint:
    pass


@dataclass(frozen=True)
class EquationArray:
    rows: tuple[Sequence, ...]


@dataclass(frozen=True)
class Accent:
    character: str
    body: Sequence


@dataclass(frozen=True)
class Bar:
    position: str
    body: Sequence


@dataclass(frozen=True)
class GroupChar:
    character: str
    position: str
    vertical_justification: str
    body: Sequence


@dataclass(frozen=True)
class Limit:
    base: Node
    lower: Sequence | None = None
    upper: Sequence | None = None


@dataclass(frozen=True)
class Function:
    name: Sequence
    body: Sequence | None = None
    subscript: Sequence | None = None
    superscript: Sequence | None = None
    limit_style: bool = False
    limit_modifier: str | None = None


@dataclass(frozen=True)
class OperatorEmulator:
    body: Sequence


@dataclass(frozen=True)
class Phantom:
    body: Sequence
    kind: str


@dataclass(frozen=True)
class BorderBox:
    body: Sequence
    kind: str


@dataclass(frozen=True)
class FormulaVerticalExtent:
    """Conservative formula bounds relative to the surrounding baseline."""

    ascent_em: float
    descent_em: float

    @property
    def height_em(self) -> float:
        """Return total vertical extent in units of the owning font size."""
        return self.ascent_em + self.descent_em


Node = (
    Text
    | Sequence
    | Styled
    | Fraction
    | Radical
    | Script
    | Prescript
    | Nary
    | Delimiter
    | Matrix
    | AlignmentPoint
    | EquationArray
    | Accent
    | Bar
    | GroupChar
    | Limit
    | Function
    | OperatorEmulator
    | Phantom
    | BorderBox
)


_BASE_VERTICAL_EXTENT = FormulaVerticalExtent(0.85, 0.35)
# These ratios model Office Math topology rather than any one installed font.
# The ordinary-text floor matches the exporter/checker baseline contract.
_SCRIPT_SCALE = 0.62
_FRACTION_SCALE = 0.68


def _max_vertical_extent(
    *extents: FormulaVerticalExtent,
) -> FormulaVerticalExtent:
    if not extents:
        return FormulaVerticalExtent(0.0, 0.0)
    return FormulaVerticalExtent(
        max(extent.ascent_em for extent in extents),
        max(extent.descent_em for extent in extents),
    )


def _scaled_vertical_extent(
    extent: FormulaVerticalExtent,
    scale: float,
) -> FormulaVerticalExtent:
    return FormulaVerticalExtent(
        extent.ascent_em * scale,
        extent.descent_em * scale,
    )


def _script_vertical_extent(
    base: FormulaVerticalExtent,
    subscript: Sequence | None,
    superscript: Sequence | None,
) -> FormulaVerticalExtent:
    ascent = base.ascent_em
    descent = base.descent_em
    if superscript is not None:
        upper = _scaled_vertical_extent(
            _node_vertical_extent(superscript),
            _SCRIPT_SCALE,
        )
        baseline_shift = 0.55
        ascent = max(ascent, baseline_shift + upper.ascent_em)
        descent = max(descent, upper.descent_em - baseline_shift)
    if subscript is not None:
        lower = _scaled_vertical_extent(
            _node_vertical_extent(subscript),
            _SCRIPT_SCALE,
        )
        baseline_shift = 0.30
        ascent = max(ascent, lower.ascent_em - baseline_shift)
        descent = max(descent, baseline_shift + lower.descent_em)
    return FormulaVerticalExtent(ascent, descent)


def _limit_vertical_extent(
    base: FormulaVerticalExtent,
    lower: Sequence | None,
    upper: Sequence | None,
) -> FormulaVerticalExtent:
    ascent = base.ascent_em
    descent = base.descent_em
    if upper is not None:
        upper_extent = _node_vertical_extent(upper)
        ascent += 0.14 + _SCRIPT_SCALE * upper_extent.height_em
    if lower is not None:
        lower_extent = _node_vertical_extent(lower)
        descent += 0.14 + _SCRIPT_SCALE * lower_extent.height_em
    return FormulaVerticalExtent(ascent, descent)


def _rows_vertical_extent(
    rows: tuple[tuple[Sequence, ...], ...] | tuple[Sequence, ...],
) -> FormulaVerticalExtent:
    row_heights: list[float] = []
    for row in rows:
        cells = row if isinstance(row, tuple) else (row,)
        row_extent = _max_vertical_extent(
            *(_node_vertical_extent(cell) for cell in cells)
        )
        row_heights.append(
            max(_BASE_VERTICAL_EXTENT.height_em, row_extent.height_em)
        )
    if not row_heights:
        return _BASE_VERTICAL_EXTENT
    total_height = sum(row_heights) + 0.18 * (len(row_heights) - 1)
    return FormulaVerticalExtent(
        max(_BASE_VERTICAL_EXTENT.ascent_em, total_height * 0.55),
        max(_BASE_VERTICAL_EXTENT.descent_em, total_height * 0.45),
    )


def _node_vertical_extent(node: Node) -> FormulaVerticalExtent:
    if isinstance(node, Text):
        return _BASE_VERTICAL_EXTENT
    if isinstance(node, AlignmentPoint):
        return FormulaVerticalExtent(0.0, 0.0)
    if isinstance(node, Sequence):
        return _max_vertical_extent(
            *(_node_vertical_extent(child) for child in node.children)
        )
    if isinstance(node, Styled):
        return _node_vertical_extent(node.body)
    if isinstance(node, Fraction):
        numerator = _node_vertical_extent(node.numerator)
        denominator = _node_vertical_extent(node.denominator)
        return FormulaVerticalExtent(
            max(
                _BASE_VERTICAL_EXTENT.ascent_em,
                0.28 + _FRACTION_SCALE * numerator.height_em,
            ),
            max(
                _BASE_VERTICAL_EXTENT.descent_em,
                0.06 + _FRACTION_SCALE * denominator.height_em,
            ),
        )
    if isinstance(node, Radical):
        body = _node_vertical_extent(node.body)
        ascent = body.ascent_em + 0.20
        if node.degree is not None:
            degree = _scaled_vertical_extent(
                _node_vertical_extent(node.degree),
                0.50,
            )
            ascent = max(ascent, 0.55 + degree.ascent_em)
        return FormulaVerticalExtent(ascent, max(body.descent_em, 0.40))
    if isinstance(node, (Script, Prescript)):
        return _script_vertical_extent(
            _node_vertical_extent(node.base),
            node.subscript,
            node.superscript,
        )
    if isinstance(node, Nary):
        base = _max_vertical_extent(
            FormulaVerticalExtent(1.05, 0.45),
            _node_vertical_extent(node.body)
            if node.body is not None else FormulaVerticalExtent(0.0, 0.0),
        )
        if node.limit_modifier == "limits":
            return _limit_vertical_extent(
                base,
                node.subscript,
                node.superscript,
            )
        return _script_vertical_extent(
            base,
            node.subscript,
            node.superscript,
        )
    if isinstance(node, Delimiter):
        body = _max_vertical_extent(
            *(_node_vertical_extent(segment) for segment in node.segments)
        )
        return FormulaVerticalExtent(
            max(_BASE_VERTICAL_EXTENT.ascent_em, body.ascent_em + 0.05),
            max(_BASE_VERTICAL_EXTENT.descent_em, body.descent_em + 0.05),
        )
    if isinstance(node, Matrix):
        return _rows_vertical_extent(node.rows)
    if isinstance(node, EquationArray):
        return _rows_vertical_extent(node.rows)
    if isinstance(node, Accent):
        body = _node_vertical_extent(node.body)
        return FormulaVerticalExtent(body.ascent_em + 0.24, body.descent_em)
    if isinstance(node, Bar):
        body = _node_vertical_extent(node.body)
        if node.position in {"bot", "bottom"}:
            return FormulaVerticalExtent(body.ascent_em, body.descent_em + 0.16)
        return FormulaVerticalExtent(body.ascent_em + 0.16, body.descent_em)
    if isinstance(node, GroupChar):
        body = _node_vertical_extent(node.body)
        if node.position in {"bot", "bottom"}:
            return FormulaVerticalExtent(body.ascent_em, body.descent_em + 0.30)
        return FormulaVerticalExtent(body.ascent_em + 0.30, body.descent_em)
    if isinstance(node, Limit):
        return _limit_vertical_extent(
            _node_vertical_extent(node.base),
            node.lower,
            node.upper,
        )
    if isinstance(node, Function):
        name = _node_vertical_extent(node.name)
        if node.subscript is not None or node.superscript is not None:
            if node.limit_modifier == "limits":
                name = _limit_vertical_extent(
                    name,
                    node.subscript,
                    node.superscript,
                )
            else:
                name = _script_vertical_extent(
                    name,
                    node.subscript,
                    node.superscript,
                )
        if node.body is None:
            return name
        return _max_vertical_extent(name, _node_vertical_extent(node.body))
    if isinstance(node, OperatorEmulator):
        return _node_vertical_extent(node.body)
    if isinstance(node, Phantom):
        if node.kind == "hphantom":
            return FormulaVerticalExtent(0.0, 0.0)
        return _node_vertical_extent(node.body)
    if isinstance(node, BorderBox):
        body = _node_vertical_extent(node.body)
        return FormulaVerticalExtent(
            body.ascent_em + 0.08,
            body.descent_em + 0.08,
        )
    return _BASE_VERTICAL_EXTENT


def formula_vertical_extent(root: Node) -> FormulaVerticalExtent:
    """Estimate native math ascent/descent from the parsed formula structure."""
    extent = _node_vertical_extent(root)
    return FormulaVerticalExtent(
        max(_BASE_VERTICAL_EXTENT.ascent_em, extent.ascent_em),
        max(_BASE_VERTICAL_EXTENT.descent_em, extent.descent_em),
    )


def merge_run_styles(base: RunStyle | None, override: RunStyle | None) -> RunStyle | None:
    """Merge inherited and local run style without clearing unrelated fields."""
    if base is None:
        return override
    if override is None:
        return base
    if override.is_default:
        return RunStyle(
            style=base.style if base.style is not None else override.style,
            normal=base.normal if base.normal is not None else override.normal,
            script=base.script if base.script is not None else override.script,
            color=base.color if base.color is not None else override.color,
            bold=base.bold if base.bold is not None else override.bold,
            italic=base.italic if base.italic is not None else override.italic,
            typeface=(
                base.typeface
                if base.typeface is not None
                else override.typeface
            ),
            is_default=base.is_default,
        )
    return RunStyle(
        style=override.style if override.style is not None else base.style,
        normal=override.normal if override.normal is not None else base.normal,
        script=override.script if override.script is not None else base.script,
        color=override.color if override.color is not None else base.color,
        bold=override.bold if override.bold is not None else base.bold,
        italic=override.italic if override.italic is not None else base.italic,
        typeface=(
            override.typeface
            if override.typeface is not None
            else base.typeface
        ),
        is_default=override.is_default,
    )


def append_child(children: list[Node], node: Node) -> None:
    """Append one node while coalescing adjacent text with equal style."""
    if isinstance(node, Sequence) and not node.children:
        return
    if (
        isinstance(node, Text)
        and children
        and isinstance(children[-1], Text)
        and children[-1].style == node.style
        and children[-1].literal == node.literal
    ):
        previous = children[-1]
        children[-1] = Text(
            previous.value + node.value,
            node.style,
            literal=node.literal,
        )
        return
    children.append(node)


def is_empty(node: Node) -> bool:
    """Return whether a node contains no visible or structural content."""
    if isinstance(node, Text):
        return not node.value
    if isinstance(node, Sequence):
        return not node.children or all(is_empty(child) for child in node.children)
    if isinstance(node, Styled):
        return is_empty(node.body)
    return False


def formula_node_count(root: Node, *, maximum: int) -> int:
    """Return iterative AST size and reject formulas above the supplied limit."""
    pending: list[Node] = [root]
    count = 0
    while pending:
        node = pending.pop()
        count += 1
        if count > maximum:
            raise ValueError(f"Formula exceeds the {maximum}-node complexity limit")
        if isinstance(node, Sequence):
            pending.extend(reversed(node.children))
        elif isinstance(node, Styled):
            pending.append(node.body)
        elif isinstance(node, Fraction):
            pending.extend((node.denominator, node.numerator))
        elif isinstance(node, Radical):
            pending.append(node.body)
            if node.degree is not None:
                pending.append(node.degree)
        elif isinstance(node, (Script, Prescript)):
            pending.append(node.base)
            if node.subscript is not None:
                pending.append(node.subscript)
            if node.superscript is not None:
                pending.append(node.superscript)
        elif isinstance(node, Nary):
            if node.subscript is not None:
                pending.append(node.subscript)
            if node.superscript is not None:
                pending.append(node.superscript)
            if node.body is not None:
                pending.append(node.body)
        elif isinstance(node, Delimiter):
            pending.extend(reversed(node.segments))
        elif isinstance(node, Matrix):
            for row in reversed(node.rows):
                pending.extend(reversed(row))
        elif isinstance(node, EquationArray):
            pending.extend(reversed(node.rows))
        elif isinstance(node, (
            Accent,
            Bar,
            GroupChar,
            OperatorEmulator,
            Phantom,
            BorderBox,
        )):
            pending.append(node.body)
        elif isinstance(node, Limit):
            pending.append(node.base)
            if node.lower is not None:
                pending.append(node.lower)
            if node.upper is not None:
                pending.append(node.upper)
        elif isinstance(node, Function):
            pending.append(node.name)
            if node.body is not None:
                pending.append(node.body)
            if node.subscript is not None:
                pending.append(node.subscript)
            if node.superscript is not None:
                pending.append(node.superscript)
    return count


__all__ = [
    "Accent",
    "AlignmentPoint",
    "Bar",
    "BorderBox",
    "Delimiter",
    "EquationArray",
    "Fraction",
    "FormulaVerticalExtent",
    "Function",
    "GroupChar",
    "Limit",
    "Matrix",
    "Nary",
    "Node",
    "OperatorEmulator",
    "Phantom",
    "Prescript",
    "Radical",
    "RunStyle",
    "Script",
    "Sequence",
    "Styled",
    "Text",
    "append_child",
    "formula_node_count",
    "formula_vertical_extent",
    "is_empty",
    "merge_run_styles",
]
