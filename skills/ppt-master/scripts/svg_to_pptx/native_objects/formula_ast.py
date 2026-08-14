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
    "is_empty",
    "merge_run_styles",
]
