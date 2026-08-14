#!/usr/bin/env python3
"""
PPT Master - Native Formula OMML Emitter

Emit the Microsoft 365 LaTeX profile AST as editable Office Math XML and
validate the narrow XML vocabulary produced by this module.

See references/native-formula.md for the owning compatibility contract.

Usage:
    Imported by formula_compiler.py.

Examples:
    emit_omml(expression, display=True)

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from .formula_ast import (
    Accent,
    AlignmentPoint,
    Bar,
    BorderBox,
    Delimiter,
    EquationArray,
    Fraction,
    Function,
    GroupChar,
    Limit,
    Matrix,
    Nary,
    Node,
    OperatorEmulator,
    Phantom,
    Prescript,
    Radical,
    RunStyle,
    Script,
    Sequence,
    Styled,
    Text,
    merge_run_styles,
)
from .formula_parser import FormulaCompileError


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_MAX_OMML_LENGTH = 1_048_576
_MAX_OMML_DEPTH = 256
_FORBIDDEN_XML_RE = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)

_MATH_ELEMENTS = frozenset({
    "acc", "accPr", "bar", "barPr", "baseJc", "begChr", "box", "boxPr",
    "borderBox", "borderBoxPr", "chr", "count", "ctrlPr", "d", "deg", "degHide",
    "den", "dPr", "e", "endChr", "eqArr", "eqArrPr", "f", "fName",
    "fPr", "func", "funcPr", "groupChr", "groupChrPr", "grow", "hideBot",
    "hideLeft", "hideRight", "hideTop", "jc", "lim", "limLoc", "limLow",
    "limLowPr", "limUpp", "limUppPr", "lit", "m", "mc", "mcPr", "mcs",
    "mPr", "mr", "nary", "naryPr", "nor", "num", "oMath", "oMathPara",
    "oMathParaPr", "phant", "phantPr", "plcHide", "pos", "r", "rad",
    "radPr", "rPr", "scr", "sepChr", "show", "sPre", "sPrePr", "opEmu",
    "sSub", "sSubSup", "sSup", "strikeBLTR", "strikeTLBR",
    "sty", "sub", "subHide", "sup", "supHide", "t",
    "type", "vertJc", "zeroAsc", "zeroDesc", "zeroWid",
})
_DRAWING_ELEMENTS = frozenset({
    "cs", "ea", "latin", "rPr", "solidFill", "srgbClr",
})
_DRAWING_ATTRIBUTES = frozenset({
    "b", "dirty", "i", "lang", "sz", "typeface", "val",
})
_ARGUMENT_ELEMENTS = frozenset({
    "acc", "bar", "borderBox", "box", "d", "eqArr", "f", "func", "groupChr",
    "limLow", "limUpp", "m", "nary", "phant", "r", "rad", "sPre",
    "sSub", "sSubSup", "sSup",
})
_ARGUMENT_CONTAINERS = frozenset({
    "deg", "den", "e", "fName", "lim", "num", "oMath", "sub", "sup",
})
_ON_OFF_ELEMENTS = frozenset({
    "degHide", "grow", "hideBot", "hideLeft", "hideRight", "hideTop", "nor",
    "lit", "opEmu", "plcHide", "show", "strikeBLTR", "strikeTLBR", "subHide", "supHide",
    "zeroAsc", "zeroDesc", "zeroWid",
})
_VALUE_ELEMENTS = frozenset({
    "baseJc", "begChr", "chr", "count", "degHide", "endChr", "grow",
    "hideBot", "hideLeft", "hideRight", "hideTop", "jc", "limLoc",
    "lit", "nor", "opEmu", "plcHide", "pos", "scr", "sepChr", "show", "strikeBLTR",
    "strikeTLBR", "sty", "subHide", "supHide", "type", "vertJc", "zeroAsc",
    "zeroDesc", "zeroWid",
})
_EMPTY_PROPERTY_ELEMENTS = frozenset({
    "funcPr", "limLowPr", "limUppPr", "sPrePr",
})
_PROPERTY_ORDER = {
    "accPr": ("chr", "ctrlPr"),
    "barPr": ("pos", "ctrlPr"),
    "boxPr": ("opEmu", "ctrlPr"),
    "borderBoxPr": (
        "hideTop", "hideBot", "hideLeft", "hideRight", "strikeBLTR",
        "strikeTLBR", "ctrlPr",
    ),
    "dPr": ("begChr", "sepChr", "endChr", "grow", "ctrlPr"),
    "eqArrPr": ("baseJc",),
    "fPr": ("type", "ctrlPr"),
    "groupChrPr": ("chr", "pos", "vertJc", "ctrlPr"),
    "mPr": ("baseJc", "plcHide", "mcs"),
    "mcPr": ("count",),
    "naryPr": (
        "chr", "limLoc", "grow", "subHide", "supHide", "ctrlPr",
    ),
    "oMathParaPr": ("jc",),
    "phantPr": ("show", "zeroWid", "zeroAsc", "zeroDesc"),
    "radPr": ("degHide", "ctrlPr"),
    "rPr": ("lit", "nor", "scr", "sty"),
}


def _math_tag(local_name: str) -> str:
    return f"{{{MATH_NS}}}{local_name}"


def _math_attrs(**values: str) -> dict[str, str]:
    return {_math_tag(name): value for name, value in values.items()}


def _math_element(
    parent: ET.Element,
    local_name: str,
    **attributes: str,
) -> ET.Element:
    return ET.SubElement(parent, _math_tag(local_name), _math_attrs(**attributes))


def _effective_style(
    inherited: RunStyle | None,
    local: RunStyle | None,
) -> RunStyle | None:
    return merge_run_styles(inherited, local)


def _append_control_style(
    properties: ET.Element,
    style: RunStyle | None,
) -> None:
    """Persist local control-glyph style that cannot live on a math run."""
    if style is None:
        return
    drawing_attributes: dict[str, str] = {}
    if style.style == "bi":
        drawing_attributes.update({"b": "1", "i": "1"})
    if not style.color and not drawing_attributes:
        return
    control_properties = _math_element(properties, "ctrlPr")
    drawing_properties = ET.SubElement(
        control_properties,
        f"{{{DRAWING_NS}}}rPr",
        drawing_attributes,
    )
    if style.color:
        solid_fill = ET.SubElement(
            drawing_properties,
            f"{{{DRAWING_NS}}}solidFill",
        )
        ET.SubElement(
            solid_fill,
            f"{{{DRAWING_NS}}}srgbClr",
            {"val": style.color},
        )


def _append_run(
    parent: ET.Element,
    value: str,
    style: RunStyle | None,
    *,
    literal: bool = False,
) -> None:
    if not value:
        return
    if style is not None and style.script == "script" and any(
        not character.isupper() for character in value
    ):
        start = 0
        uppercase = value[0].isupper()
        for index in range(1, len(value) + 1):
            current = value[index].isupper() if index < len(value) else not uppercase
            if current == uppercase:
                continue
            segment_style = style if uppercase else RunStyle(
                normal=style.normal,
                color=style.color,
                bold=style.bold,
                italic=style.italic,
                typeface=style.typeface,
            )
            _append_run(
                parent,
                value[start:index],
                segment_style,
                literal=literal,
            )
            start = index
            uppercase = current
        return
    run = _math_element(parent, "r")
    if literal or (
        style is not None and (style.style or style.normal or style.script)
    ):
        properties = _math_element(run, "rPr")
        if literal:
            _math_element(properties, "lit", val="on")
        if style is not None and style.normal is True:
            _math_element(properties, "nor", val="on")
        elif style is not None:
            if style.script:
                _math_element(properties, "scr", val=style.script)
            if style.style:
                _math_element(properties, "sty", val=style.style)
    if style is not None and any(
        value is not None
        for value in (style.color, style.bold, style.italic, style.typeface)
    ):
        drawing_attributes: dict[str, str] = {}
        if style.bold is not None:
            drawing_attributes["b"] = "1" if style.bold else "0"
        if style.italic is not None:
            drawing_attributes["i"] = "1" if style.italic else "0"
        drawing_properties = ET.SubElement(
            run,
            f"{{{DRAWING_NS}}}rPr",
            drawing_attributes,
        )
        if style.color:
            solid_fill = ET.SubElement(
                drawing_properties,
                f"{{{DRAWING_NS}}}solidFill",
            )
            ET.SubElement(
                solid_fill,
                f"{{{DRAWING_NS}}}srgbClr",
                {"val": style.color},
            )
        if style.typeface:
            for local_name in ("latin", "ea", "cs"):
                ET.SubElement(
                    drawing_properties,
                    f"{{{DRAWING_NS}}}{local_name}",
                    {"typeface": style.typeface},
                )
    text = _math_element(run, "t")
    if value != value.strip() or "  " in value:
        text.set(f"{{{XML_NS}}}space", "preserve")
    text.text = value


def _append_sequence(
    parent: ET.Element,
    sequence: Sequence,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    for child in sequence.children:
        _append_node(parent, child, inherited_style, display=display)


def _append_node(
    parent: ET.Element,
    node: Node,
    inherited_style: RunStyle | None = None,
    *,
    display: bool,
) -> None:
    if isinstance(node, Text):
        _append_run(
            parent,
            node.value,
            _effective_style(inherited_style, node.style),
            literal=node.literal,
        )
        return
    if isinstance(node, Sequence):
        _append_sequence(parent, node, inherited_style, display=display)
        return
    if isinstance(node, Styled):
        _append_sequence(
            parent,
            node.body,
            _effective_style(inherited_style, node.style),
            display=display,
        )
        return
    if isinstance(node, Fraction):
        fraction = _math_element(parent, "f")
        properties = _math_element(fraction, "fPr")
        _math_element(properties, "type", val=node.kind)
        _append_control_style(properties, inherited_style)
        numerator = _math_element(fraction, "num")
        _append_sequence(numerator, node.numerator, inherited_style, display=display)
        denominator = _math_element(fraction, "den")
        _append_sequence(denominator, node.denominator, inherited_style, display=display)
        return
    if isinstance(node, Radical):
        radical = _math_element(parent, "rad")
        properties = _math_element(radical, "radPr")
        _math_element(properties, "degHide", val="off" if node.degree else "on")
        _append_control_style(properties, inherited_style)
        degree = _math_element(radical, "deg")
        if node.degree is not None:
            _append_sequence(degree, node.degree, inherited_style, display=display)
        body = _math_element(radical, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    if isinstance(node, Script):
        _append_script(parent, node, inherited_style, display=display)
        return
    if isinstance(node, Prescript):
        _append_prescript(parent, node, inherited_style, display=display)
        return
    if isinstance(node, Nary):
        _append_nary(parent, node, inherited_style, display=display)
        return
    if isinstance(node, Delimiter):
        delimiter = _math_element(parent, "d")
        properties = _math_element(delimiter, "dPr")
        _math_element(properties, "begChr", val=node.left)
        _math_element(properties, "sepChr", val=node.separator)
        _math_element(properties, "endChr", val=node.right)
        _math_element(properties, "grow", val="on")
        _append_control_style(properties, inherited_style)
        for segment in node.segments:
            body = _math_element(delimiter, "e")
            _append_sequence(body, segment, inherited_style, display=display)
        return
    if isinstance(node, Matrix):
        _append_matrix(parent, node, inherited_style, display=display)
        return
    if isinstance(node, AlignmentPoint):
        _append_run(parent, "&", inherited_style)
        return
    if isinstance(node, EquationArray):
        equation_array = _math_element(parent, "eqArr")
        properties = _math_element(equation_array, "eqArrPr")
        _math_element(properties, "baseJc", val="center")
        for row in node.rows:
            body = _math_element(equation_array, "e")
            _append_sequence(body, row, inherited_style, display=display)
        return
    if isinstance(node, Accent):
        accent = _math_element(parent, "acc")
        properties = _math_element(accent, "accPr")
        _math_element(properties, "chr", val=node.character)
        _append_control_style(properties, inherited_style)
        body = _math_element(accent, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    if isinstance(node, Bar):
        bar = _math_element(parent, "bar")
        properties = _math_element(bar, "barPr")
        _math_element(properties, "pos", val=node.position)
        _append_control_style(properties, inherited_style)
        body = _math_element(bar, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    if isinstance(node, GroupChar):
        group = _math_element(parent, "groupChr")
        properties = _math_element(group, "groupChrPr")
        _math_element(properties, "chr", val=node.character)
        _math_element(properties, "pos", val=node.position)
        _math_element(properties, "vertJc", val=node.vertical_justification)
        _append_control_style(properties, inherited_style)
        body = _math_element(group, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    if isinstance(node, Limit):
        _append_limit(parent, node, inherited_style, display=display)
        return
    if isinstance(node, Function):
        _append_function(parent, node, inherited_style, display=display)
        return
    if isinstance(node, OperatorEmulator):
        box = _math_element(parent, "box")
        properties = _math_element(box, "boxPr")
        _math_element(properties, "opEmu", val="on")
        _append_control_style(properties, inherited_style)
        body = _math_element(box, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    if isinstance(node, Phantom):
        phantom = _math_element(parent, "phant")
        properties = _math_element(phantom, "phantPr")
        if node.kind == "phantom":
            _math_element(properties, "show", val="off")
        elif node.kind == "hphantom":
            _math_element(properties, "show", val="off")
            _math_element(properties, "zeroAsc", val="on")
            _math_element(properties, "zeroDesc", val="on")
        elif node.kind == "vphantom":
            _math_element(properties, "show", val="off")
            _math_element(properties, "zeroWid", val="on")
        else:
            raise FormulaCompileError(f"Unsupported phantom kind: {node.kind!r}")
        body = _math_element(phantom, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    if isinstance(node, BorderBox):
        border = _math_element(parent, "borderBox")
        properties = _math_element(border, "borderBoxPr")
        if node.kind in {"cancel", "bcancel", "xcancel"}:
            for side in ("hideTop", "hideBot", "hideLeft", "hideRight"):
                _math_element(properties, side, val="on")
        if node.kind == "cancel":
            _math_element(properties, "strikeBLTR", val="on")
        elif node.kind == "bcancel":
            _math_element(properties, "strikeTLBR", val="on")
        elif node.kind == "xcancel":
            _math_element(properties, "strikeBLTR", val="on")
            _math_element(properties, "strikeTLBR", val="on")
        elif node.kind not in {"boxed", "fbox", "framebox"}:
            raise FormulaCompileError(f"Unsupported border-box kind: {node.kind!r}")
        _append_control_style(properties, inherited_style)
        body = _math_element(border, "e")
        _append_sequence(body, node.body, inherited_style, display=display)
        return
    raise FormulaCompileError(f"Unsupported internal formula node: {type(node).__name__}")


def _append_script(
    parent: ET.Element,
    node: Script,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    if node.subscript is not None and node.superscript is not None:
        script = _math_element(parent, "sSubSup")
    elif node.subscript is not None:
        script = _math_element(parent, "sSub")
    else:
        script = _math_element(parent, "sSup")
    base = _math_element(script, "e")
    _append_node(base, node.base, inherited_style, display=display)
    if node.subscript is not None:
        subscript = _math_element(script, "sub")
        _append_sequence(subscript, node.subscript, inherited_style, display=display)
    if node.superscript is not None:
        superscript = _math_element(script, "sup")
        _append_sequence(superscript, node.superscript, inherited_style, display=display)


def _append_prescript(
    parent: ET.Element,
    node: Prescript,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    script = _math_element(parent, "sPre")
    _math_element(script, "sPrePr")
    subscript = _math_element(script, "sub")
    if node.subscript is not None:
        _append_sequence(subscript, node.subscript, inherited_style, display=display)
    superscript = _math_element(script, "sup")
    if node.superscript is not None:
        _append_sequence(superscript, node.superscript, inherited_style, display=display)
    base = _math_element(script, "e")
    _append_node(base, node.base, inherited_style, display=display)


def _append_nary(
    parent: ET.Element,
    node: Nary,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    nary = _math_element(parent, "nary")
    properties = _math_element(nary, "naryPr")
    _math_element(properties, "chr", val=node.symbol)
    if node.limit_modifier == "limits":
        limit_location = "undOvr"
    elif node.limit_modifier == "nolimits":
        limit_location = "subSup"
    elif node.category == "integral":
        limit_location = "subSup"
    else:
        limit_location = "undOvr" if display else "subSup"
    _math_element(properties, "limLoc", val=limit_location)
    _math_element(properties, "grow", val="off")
    _math_element(properties, "subHide", val="off" if node.subscript else "on")
    _math_element(properties, "supHide", val="off" if node.superscript else "on")
    _append_control_style(properties, inherited_style)
    subscript = _math_element(nary, "sub")
    if node.subscript is not None:
        _append_sequence(subscript, node.subscript, inherited_style, display=display)
    superscript = _math_element(nary, "sup")
    if node.superscript is not None:
        _append_sequence(superscript, node.superscript, inherited_style, display=display)
    body = _math_element(nary, "e")
    if node.body is not None:
        _append_sequence(body, node.body, inherited_style, display=display)


def _append_matrix(
    parent: ET.Element,
    node: Matrix,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    matrix = _math_element(parent, "m")
    properties = _math_element(matrix, "mPr")
    _math_element(properties, "baseJc", val="center")
    _math_element(properties, "plcHide", val="on")
    columns = _math_element(properties, "mcs")
    column_count = len(node.rows[0])
    for _ in range(column_count):
        column = _math_element(columns, "mc")
        column_properties = _math_element(column, "mcPr")
        _math_element(column_properties, "count", val="1")
    for row_data in node.rows:
        row = _math_element(matrix, "mr")
        for cell_data in row_data:
            cell = _math_element(row, "e")
            _append_sequence(cell, cell_data, inherited_style, display=display)


def _append_limit(
    parent: ET.Element,
    node: Limit,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    base: Node = node.base
    if node.lower is not None:
        lower = _math_element(parent, "limLow")
        _math_element(lower, "limLowPr")
        expression = _math_element(lower, "e")
        _append_node(expression, base, inherited_style, display=display)
        limit = _math_element(lower, "lim")
        _append_sequence(limit, node.lower, inherited_style, display=display)
        base = Sequence(())
        if node.upper is not None:
            wrapper = ET.Element(_math_tag("limUpp"))
            _math_element(wrapper, "limUppPr")
            expression = _math_element(wrapper, "e")
            expression.append(lower)
            limit = _math_element(wrapper, "lim")
            _append_sequence(limit, node.upper, inherited_style, display=display)
            parent.remove(lower)
            parent.append(wrapper)
        return
    if node.upper is not None:
        upper = _math_element(parent, "limUpp")
        _math_element(upper, "limUppPr")
        expression = _math_element(upper, "e")
        _append_node(expression, base, inherited_style, display=display)
        limit = _math_element(upper, "lim")
        _append_sequence(limit, node.upper, inherited_style, display=display)
        return
    _append_node(parent, base, inherited_style, display=display)


def _append_function(
    parent: ET.Element,
    node: Function,
    inherited_style: RunStyle | None,
    *,
    display: bool,
) -> None:
    function = _math_element(parent, "func")
    _math_element(function, "funcPr")
    name_parent = _math_element(function, "fName")
    name: Node = node.name
    if node.subscript is not None or node.superscript is not None:
        use_limits = node.limit_modifier == "limits" or (
            node.limit_modifier != "nolimits" and node.limit_style and display
        )
        if use_limits:
            name = Limit(name, lower=node.subscript, upper=node.superscript)
        else:
            name = Script(name, node.subscript, node.superscript)
    _append_node(name_parent, name, inherited_style, display=display)
    body = _math_element(function, "e")
    if node.body is not None:
        _append_sequence(body, node.body, inherited_style, display=display)


def _qualified_name(name: str) -> tuple[str | None, str]:
    if name.startswith("{") and "}" in name:
        namespace, local_name = name[1:].split("}", 1)
        return namespace, local_name
    return None, name


def _child_names(element: ET.Element) -> list[str]:
    return [_qualified_name(child.tag)[1] for child in element]


def _require_children(
    element: ET.Element,
    expected: tuple[str, ...],
) -> None:
    element_name = _qualified_name(element.tag)[1]
    actual = tuple(_child_names(element))
    if actual != expected:
        raise FormulaCompileError(
            f"m:{element_name} children must be {expected!r}, found {actual!r}"
        )


def _require_repeated_children(
    element: ET.Element,
    child_name: str,
    *,
    minimum: int,
    maximum: int,
) -> None:
    element_name = _qualified_name(element.tag)[1]
    actual = _child_names(element)
    if (
        not minimum <= len(actual) <= maximum
        or any(name != child_name for name in actual)
    ):
        raise FormulaCompileError(
            f"m:{element_name} must contain {minimum}..{maximum} "
            f"m:{child_name} children"
        )


def _validate_property_children(element: ET.Element, element_name: str) -> None:
    expected_order = _PROPERTY_ORDER[element_name]
    actual = _child_names(element)
    if len(actual) != len(set(actual)):
        raise FormulaCompileError(f"m:{element_name} contains duplicate properties")
    unknown = [name for name in actual if name not in expected_order]
    if unknown:
        raise FormulaCompileError(
            f"m:{element_name} contains unsupported properties: {unknown!r}"
        )
    order = [expected_order.index(name) for name in actual]
    if order != sorted(order):
        raise FormulaCompileError(f"m:{element_name} properties are out of order")
    if element_name == "rPr" and "nor" in actual and (
        "scr" in actual or "sty" in actual
    ):
        raise FormulaCompileError(
            "m:rPr cannot combine m:nor with m:scr or m:sty"
        )


def _math_value(element: ET.Element) -> str:
    value = element.get(_math_tag("val"))
    if value is None:
        element_name = _qualified_name(element.tag)[1]
        raise FormulaCompileError(f"m:{element_name} requires m:val")
    return value


def _validate_math_value(element: ET.Element, element_name: str) -> None:
    value = _math_value(element)
    allowed_values = {
        "baseJc": {"top", "center", "bot"},
        "jc": {"left", "right", "center", "centerGroup"},
        "limLoc": {"subSup", "undOvr"},
        "pos": {"top", "bot"},
        "scr": {
            "roman", "sans-serif", "monospace", "double-struck",
            "script", "fraktur",
        },
        "sty": {"p", "b", "i", "bi"},
        "type": {"bar", "lin", "noBar", "skw"},
        "vertJc": {"top", "bot"},
    }
    if element_name in _ON_OFF_ELEMENTS:
        if value not in {"on", "off", "true", "false", "1", "0"}:
            raise FormulaCompileError(
                f"m:{element_name} has invalid on/off value: {value!r}"
            )
        return
    if element_name == "count":
        if not value.isascii() or not value.isdigit() or not 1 <= int(value) <= 64:
            raise FormulaCompileError("m:count must be an integer from 1 to 64")
        return
    if element_name in {"begChr", "chr", "endChr", "sepChr"}:
        if len(value) > 1:
            raise FormulaCompileError(
                f"m:{element_name} must contain at most one character"
            )
        return
    allowed = allowed_values.get(element_name)
    if allowed is not None and value not in allowed:
        raise FormulaCompileError(
            f"m:{element_name} has invalid value: {value!r}"
        )


def _validate_drawing_element(element: ET.Element, element_name: str) -> None:
    attributes = {
        _qualified_name(name)[1]: value for name, value in element.attrib.items()
    }
    children = _child_names(element)
    if element_name == "rPr":
        unknown = set(attributes) - {"b", "dirty", "i", "lang", "sz"}
        if unknown:
            raise FormulaCompileError(
                f"a:rPr contains unsupported attributes: {sorted(unknown)!r}"
            )
        for name in ("b", "dirty", "i"):
            if name in attributes and attributes[name] not in {
                "on", "off", "true", "false", "1", "0",
            }:
                raise FormulaCompileError(
                    f"a:rPr@{name} has invalid on/off value"
                )
        if "sz" in attributes and (
            not attributes["sz"].isascii()
            or not attributes["sz"].isdigit()
            or not 100 <= int(attributes["sz"]) <= 400_000
        ):
            raise FormulaCompileError("a:rPr@sz must be from 100 to 400000")
        expected_order = ("solidFill", "latin", "ea", "cs")
        if len(children) != len(set(children)):
            raise FormulaCompileError("a:rPr contains duplicate child properties")
        if any(name not in expected_order for name in children):
            raise FormulaCompileError("a:rPr contains unsupported child properties")
        order = [expected_order.index(name) for name in children]
        if order != sorted(order):
            raise FormulaCompileError("a:rPr child properties are out of order")
        return
    if element_name == "solidFill":
        if attributes or children != ["srgbClr"]:
            raise FormulaCompileError("a:solidFill must contain one a:srgbClr")
        return
    if element_name == "srgbClr":
        if children or set(attributes) != {"val"} or not re.fullmatch(
            r"[0-9A-Fa-f]{6}", attributes["val"]
        ):
            raise FormulaCompileError("a:srgbClr@val must be six hexadecimal digits")
        return
    if element_name in {"latin", "ea", "cs"}:
        if children or set(attributes) != {"typeface"} or not attributes["typeface"]:
            raise FormulaCompileError(
                f"a:{element_name} must contain one non-empty typeface attribute"
            )


def _validate_math_structure(element: ET.Element, element_name: str) -> None:
    if element_name in _ARGUMENT_CONTAINERS:
        children = list(element)
        if element_name == "oMath" and not children:
            raise FormulaCompileError("m:oMath must contain a math expression")
        for child in children:
            namespace, child_name = _qualified_name(child.tag)
            if namespace != MATH_NS or child_name not in _ARGUMENT_ELEMENTS:
                raise FormulaCompileError(
                    f"m:{element_name} contains an invalid math argument child"
                )
        return
    fixed_children = {
        "acc": ("accPr", "e"),
        "bar": ("barPr", "e"),
        "borderBox": ("borderBoxPr", "e"),
        "box": ("boxPr", "e"),
        "f": ("fPr", "num", "den"),
        "func": ("funcPr", "fName", "e"),
        "groupChr": ("groupChrPr", "e"),
        "limLow": ("limLowPr", "e", "lim"),
        "limUpp": ("limUppPr", "e", "lim"),
        "mc": ("mcPr",),
        "nary": ("naryPr", "sub", "sup", "e"),
        "phant": ("phantPr", "e"),
        "rad": ("radPr", "deg", "e"),
        "sPre": ("sPrePr", "sub", "sup", "e"),
        "sSub": ("e", "sub"),
        "sSubSup": ("e", "sub", "sup"),
        "sSup": ("e", "sup"),
    }
    if element_name in fixed_children:
        _require_children(element, fixed_children[element_name])
        return
    if element_name == "oMathPara":
        children = tuple(_child_names(element))
        if children not in {("oMath",), ("oMathParaPr", "oMath")}:
            raise FormulaCompileError(
                "m:oMathPara must contain optional m:oMathParaPr then one m:oMath"
            )
        return
    if element_name == "d":
        children = _child_names(element)
        rows = children[1:] if children and children[0] == "dPr" else []
        if not 1 <= len(rows) <= 64 or any(name != "e" for name in rows):
            raise FormulaCompileError("m:d must contain m:dPr then 1..64 m:e children")
        return
    if element_name == "eqArr":
        children = _child_names(element)
        offset = 1 if children and children[0] == "eqArrPr" else 0
        rows = children[offset:]
        if not 1 <= len(rows) <= 64 or any(name != "e" for name in rows):
            raise FormulaCompileError("m:eqArr must contain 1..64 m:e rows")
        return
    if element_name == "m":
        children = _child_names(element)
        rows = children[1:] if children and children[0] == "mPr" else []
        if not 1 <= len(rows) <= 256 or any(name != "mr" for name in rows):
            raise FormulaCompileError("m:m must contain m:mPr then 1..256 m:mr rows")
        return
    if element_name == "mr":
        _require_repeated_children(element, "e", minimum=1, maximum=64)
        return
    if element_name == "mcs":
        _require_repeated_children(element, "mc", minimum=1, maximum=64)
        return
    if element_name == "r":
        children = [(_qualified_name(child.tag), child) for child in element]
        index = 0
        if index < len(children) and children[index][0] == (MATH_NS, "rPr"):
            index += 1
        if index < len(children) and children[index][0] == (DRAWING_NS, "rPr"):
            index += 1
        if index != len(children) - 1 or children[index][0] != (MATH_NS, "t"):
            raise FormulaCompileError(
                "m:r must contain optional m:rPr, optional a:rPr, then one m:t"
            )
        return
    if element_name == "ctrlPr":
        children = [(_qualified_name(child.tag), child) for child in element]
        if len(children) > 1 or (
            children and children[0][0] != (DRAWING_NS, "rPr")
        ):
            raise FormulaCompileError(
                "m:ctrlPr may contain only one optional a:rPr"
            )
        return
    if element_name in _PROPERTY_ORDER:
        _validate_property_children(element, element_name)
        return
    if element_name in _EMPTY_PROPERTY_ELEMENTS:
        if list(element):
            raise FormulaCompileError(f"m:{element_name} must be empty")
        return
    if element_name in _VALUE_ELEMENTS:
        if list(element):
            raise FormulaCompileError(f"m:{element_name} must not contain children")
        _validate_math_value(element, element_name)
        return
    if element_name == "t" and list(element):
        raise FormulaCompileError("m:t must not contain children")


def _validate_matrix_dimensions(root: ET.Element) -> None:
    for matrix in root.iter(_math_tag("m")):
        properties = matrix.find(_math_tag("mPr"))
        columns = properties.find(_math_tag("mcs")) if properties is not None else None
        if columns is None:
            raise FormulaCompileError("m:mPr must contain m:mcs")
        column_count = 0
        for column in columns:
            column_properties = column.find(_math_tag("mcPr"))
            count = (
                column_properties.find(_math_tag("count"))
                if column_properties is not None
                else None
            )
            if count is None:
                raise FormulaCompileError("m:mcPr must contain m:count")
            column_count += int(_math_value(count))
        if not 1 <= column_count <= 64:
            raise FormulaCompileError("matrix column count must be from 1 to 64")
        for row in matrix.findall(_math_tag("mr")):
            if len(row.findall(_math_tag("e"))) != column_count:
                raise FormulaCompileError(
                    "every matrix row must match the declared column count"
                )


def _validate_xml_tree(root: ET.Element) -> None:
    namespace, local_name = _qualified_name(root.tag)
    if namespace != MATH_NS or local_name not in {"oMathPara", "oMath"}:
        raise FormulaCompileError("OMML root must be m:oMathPara or m:oMath")

    math_roots = 0
    pending = [root]
    while pending:
        element = pending.pop()
        pending.extend(reversed(element))
        element_namespace, element_name = _qualified_name(element.tag)
        if element_namespace == MATH_NS and element_name not in _MATH_ELEMENTS:
            raise FormulaCompileError(
                f"OMML contains unsupported math element: {element_name!r}"
            )
        if element_namespace == DRAWING_NS and element_name not in _DRAWING_ELEMENTS:
            raise FormulaCompileError(
                f"OMML contains unsupported DrawingML element: {element_name!r}"
            )
        if element_namespace not in {MATH_NS, DRAWING_NS}:
            raise FormulaCompileError(
                f"OMML contains unsupported element namespace: {element_namespace!r}"
            )
        if element_namespace == MATH_NS and element_name in {"oMathPara", "oMath"}:
            math_roots += 1
        for attribute, value in element.attrib.items():
            attribute_namespace, attribute_name = _qualified_name(attribute)
            if (
                attribute_namespace == MATH_NS
                and attribute_name == "val"
                and element_namespace == MATH_NS
                and element_name in _VALUE_ELEMENTS
            ):
                continue
            if (
                attribute_namespace in {None, DRAWING_NS}
                and element_namespace == DRAWING_NS
                and attribute_name in _DRAWING_ATTRIBUTES
            ):
                continue
            if (
                attribute_namespace == XML_NS
                and element_namespace == MATH_NS
                and element_name == "t"
                and attribute_name == "space"
                and value == "preserve"
            ):
                continue
            raise FormulaCompileError(
                f"OMML contains unsupported attribute {attribute_name!r}"
            )
        if element_namespace == MATH_NS:
            _validate_math_structure(element, element_name)
        else:
            _validate_drawing_element(element, element_name)
        if element.text:
            if not (
                element_namespace == MATH_NS and element_name == "t"
            ) and element.text.strip():
                raise FormulaCompileError(
                    f"OMML text is only allowed inside m:t, found in {element_name!r}"
                )
        if element.tail and element.tail.strip():
            raise FormulaCompileError("OMML contains unexpected trailing text")

    expected_roots = 2 if local_name == "oMathPara" else 1
    if math_roots != expected_roots:
        raise FormulaCompileError("OMML must contain exactly one math expression")
    _validate_matrix_dimensions(root)
    if local_name == "oMathPara":
        direct_expressions = [
            child
            for child in root
            if _qualified_name(child.tag) == (MATH_NS, "oMath")
        ]
        if len(direct_expressions) != 1:
            raise FormulaCompileError(
                "m:oMathPara must contain exactly one direct m:oMath expression"
            )


def _validate_xml_depth(root: ET.Element) -> None:
    pending: list[tuple[ET.Element, int]] = [(root, 1)]
    while pending:
        element, depth = pending.pop()
        if depth > _MAX_OMML_DEPTH:
            raise FormulaCompileError(
                f"OMML nesting exceeds {_MAX_OMML_DEPTH} levels"
            )
        pending.extend((child, depth + 1) for child in reversed(element))


def _parse_omml_with_resource_limits(xml: str) -> ET.Element:
    if not isinstance(xml, str):
        raise FormulaCompileError("OMML fragment must be a string")
    if not xml.strip():
        raise FormulaCompileError("OMML fragment is empty")
    if len(xml) > _MAX_OMML_LENGTH:
        raise FormulaCompileError(
            f"OMML fragment exceeds the {_MAX_OMML_LENGTH}-character limit"
        )
    if _FORBIDDEN_XML_RE.search(xml):
        raise FormulaCompileError("DOCTYPE and ENTITY declarations are forbidden in OMML")
    try:
        root = ET.fromstring(xml)
    except (ET.ParseError, RecursionError) as exc:
        raise FormulaCompileError(f"Invalid OMML XML: {exc}") from exc
    _validate_xml_depth(root)
    return root


def _serialize_omml_with_resource_limits(root: ET.Element) -> str:
    ET.register_namespace("m", MATH_NS)
    ET.register_namespace("a", DRAWING_NS)
    try:
        canonical = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    except RecursionError as exc:
        raise FormulaCompileError("OMML nesting exceeds the XML serializer limit") from exc
    if len(canonical) > _MAX_OMML_LENGTH:
        raise FormulaCompileError(
            f"Canonical OMML exceeds the {_MAX_OMML_LENGTH}-character limit"
        )
    return canonical


def validate_omml_resource_limits(xml: str) -> str:
    """Apply only the shared serialized-size and XML-depth resource limits."""
    root = _parse_omml_with_resource_limits(xml)
    return _serialize_omml_with_resource_limits(root)


def validate_omml_fragment(xml: str) -> str:
    """Validate emitted Office Math XML and canonicalize namespace prefixes."""
    root = _parse_omml_with_resource_limits(xml)
    _validate_xml_tree(root)
    return _serialize_omml_with_resource_limits(root)


def emit_omml(expression: Sequence, *, display: bool) -> str:
    """Emit one block or inline Office Math root from the parsed AST."""
    if display:
        root = ET.Element(_math_tag("oMathPara"))
        properties = _math_element(root, "oMathParaPr")
        _math_element(properties, "jc", val="center")
        math = _math_element(root, "oMath")
    else:
        root = ET.Element(_math_tag("oMath"))
        math = root
    _append_sequence(math, expression, None, display=display)
    ET.register_namespace("m", MATH_NS)
    ET.register_namespace("a", DRAWING_NS)
    xml = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    return validate_omml_fragment(xml)


__all__ = [
    "DRAWING_NS",
    "MATH_NS",
    "emit_omml",
    "validate_omml_fragment",
    "validate_omml_resource_limits",
]
