"""Import PPT Master-owned Office Math into canonical SVG formula markers.

The reverse contract is deliberately narrow: accept only the closed OMML
vocabulary already validated by the native formula compiler, serialize that
structure to compiler-accepted LaTeX, and build a plain-text SVG preview.
Unknown third-party OMML remains outside this module's reconstruction claim.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from svg_to_pptx.native_objects.formula_compiler import (
    FormulaCompileError,
    compile_latex_to_inline_omml,
    compile_latex_to_omml,
    validate_omml_fragment,
)
from svg_to_pptx.native_objects.formula_profile import (
    ACCENT_COMMANDS,
    NARY_COMMANDS,
)


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"

_M = f"{{{MATH_NS}}}"
_A = f"{{{DRAWING_NS}}}"
_A14_M = f"{{{A14_NS}}}m"
_PROPERTY_SUFFIX = "Pr"

_NARY_COMMAND_BY_SYMBOL = {
    symbol: command
    for command, (symbol, _category) in NARY_COMMANDS.items()
}
_ACCENT_COMMAND_BY_CHARACTER = {
    character: command
    for command, character in ACCENT_COMMANDS.items()
}
_GROUP_COMMANDS = {
    ("⏞", "top", "bot"): "overbrace",
    ("⏟", "bot", "top"): "underbrace",
    ("→", "bot", "top"): "underrightarrow",
    ("←", "bot", "top"): "underleftarrow",
    ("↔", "bot", "top"): "underleftrightarrow",
    ("→", "top", "bot"): "overrightarrow",
    ("←", "top", "bot"): "overleftarrow",
    ("↔", "top", "bot"): "overleftrightarrow",
}
_DELIMITER_COMMANDS = {
    "{": r"\{",
    "}": r"\}",
    "⟨": r"\langle",
    "⟩": r"\rangle",
    "⌊": r"\lfloor",
    "⌋": r"\rfloor",
    "⌈": r"\lceil",
    "⌉": r"\rceil",
    "‖": r"\Vert",
    "⟦": "⟦",
    "⟧": "⟧",
}
_SPACING_LATEX = {
    "\u200b": r"\!",
    "\u2009": r"\,",
    "\u205f": r"\:",
    "\u2004": r"\;",
    "\u2002": r"\enspace{}",
    "\u2003": r"\quad{}",
    "\u00a0": "~",
}


class FormulaImportError(ValueError):
    """Raised when source OMML is outside the reversible project contract."""


@dataclass(frozen=True)
class FormulaImport:
    """Canonical formula source plus a visible SVG-preview representation."""

    latex: str
    preview: str
    font_size_px: float
    color: str
    align: str
    language: str


def import_formula(math_zone: ET.Element, *, display: bool) -> FormulaImport:
    """Validate and reconstruct one ``a14:m`` formula zone."""
    if math_zone.tag != _A14_M:
        raise FormulaImportError("formula carrier must be one a14:m element")
    children = [child for child in math_zone if isinstance(child.tag, str)]
    if len(children) != 1:
        raise FormulaImportError("a14:m must contain exactly one Office Math root")
    root = children[0]
    expected = f"{_M}{'oMathPara' if display else 'oMath'}"
    if root.tag != expected:
        kind = "block" if display else "inline"
        raise FormulaImportError(
            f"{kind} formula requires m:{expected.rsplit('}', 1)[-1]}"
        )

    try:
        canonical = validate_omml_fragment(
            ET.tostring(root, encoding="unicode", short_empty_elements=True)
        )
        validated_root = ET.fromstring(canonical)
        latex = _serialize_root(validated_root)
        if display:
            compile_latex_to_omml(latex)
        else:
            compile_latex_to_inline_omml(latex)
    except (FormulaCompileError, ET.ParseError, RecursionError) as exc:
        raise FormulaImportError(str(exc)) from exc

    preview = _preview_root(validated_root).strip()
    if not latex.strip() or not preview:
        raise FormulaImportError("formula reconstruction produced empty content")
    font_size_px, color, language = _dominant_run_style(validated_root)
    return FormulaImport(
        latex=latex,
        preview=preview,
        font_size_px=font_size_px,
        color=color,
        align=_formula_alignment(validated_root),
        language=language,
    )


def opaque_formula_preview(math_zone: ET.Element) -> str:
    """Return readable source text without claiming native reconstruction."""
    text = "".join(
        item.text or ""
        for item in math_zone.iter(f"{_M}t")
    ).strip()
    return text or "[unsupported formula]"


def _serialize_root(root: ET.Element) -> str:
    if root.tag == f"{_M}oMathPara":
        math = root.find(f"{_M}oMath")
        if math is None:
            raise FormulaImportError("m:oMathPara is missing m:oMath")
        return _serialize_children(math)
    if root.tag == f"{_M}oMath":
        return _serialize_children(root)
    raise FormulaImportError("unsupported Office Math root")


def _serialize_children(parent: ET.Element, *, alignment: bool = False) -> str:
    return "".join(
        _serialize_node(child, alignment=alignment)
        for child in parent
        if _local_name(child) not in {_PROPERTY_SUFFIX, "ctrlPr"}
        and not _local_name(child).endswith(_PROPERTY_SUFFIX)
    )


def _serialize_argument(owner: ET.Element, name: str, *, alignment: bool = False) -> str:
    element = owner.find(f"{_M}{name}")
    if element is None:
        raise FormulaImportError(
            f"m:{_local_name(owner)} is missing required m:{name}"
        )
    return _serialize_children(element, alignment=alignment)


def _serialize_node(element: ET.Element, *, alignment: bool = False) -> str:
    name = _local_name(element)
    if name == "r":
        return _serialize_run(element, alignment=alignment)
    if name == "f":
        kind = _property_value(element, "fPr", "type", "bar")
        command = {"bar": "frac", "skw": "ifrac"}.get(kind)
        numerator = _serialize_argument(element, "num")
        denominator = _serialize_argument(element, "den")
        if command is not None:
            return f"\\{command}{{{numerator}}}{{{denominator}}}"
        if kind == "noBar":
            return (
                r"\genfrac{}{}{0pt}{}"
                f"{{{numerator}}}{{{denominator}}}"
            )
        raise FormulaImportError(f"unsupported reversible fraction type: {kind!r}")
    if name == "rad":
        body = _serialize_argument(element, "e")
        degree = _serialize_argument(element, "deg")
        return f"\\sqrt[{degree}]{{{body}}}" if degree else f"\\sqrt{{{body}}}"
    if name in {"sSub", "sSup", "sSubSup"}:
        base = _serialize_argument(element, "e")
        subscript = _serialize_optional_argument(element, "sub")
        superscript = _serialize_optional_argument(element, "sup")
        return _scripted(f"{{{base}}}", subscript, superscript)
    if name == "sPre":
        base = _serialize_argument(element, "e")
        subscript = _serialize_optional_argument(element, "sub")
        superscript = _serialize_optional_argument(element, "sup")
        return _scripted("", subscript, superscript) + f"{{{base}}}"
    if name == "nary":
        symbol = _property_value(element, "naryPr", "chr", "")
        command = _NARY_COMMAND_BY_SYMBOL.get(symbol)
        if command is None:
            raise FormulaImportError(f"unsupported reversible n-ary symbol: {symbol!r}")
        source = f"\\{command}"
        # Serialize the source location explicitly when it uses under/over
        # limits. ``subSup`` is the neutral default in both formula contexts.
        default_location = "subSup"
        location = _property_value(element, "naryPr", "limLoc", default_location)
        if location != default_location:
            source += r"\limits" if location == "undOvr" else r"\nolimits"
        source = _scripted(
            source,
            _serialize_optional_argument(element, "sub"),
            _serialize_optional_argument(element, "sup"),
        )
        body = _serialize_optional_argument(element, "e")
        return source + (f"{{{body}}}" if body else "")
    if name == "d":
        left = _property_value(element, "dPr", "begChr", "(")
        right = _property_value(element, "dPr", "endChr", ")")
        separator = _property_value(element, "dPr", "sepChr", "")
        segments = [
            _serialize_children(child)
            for child in element.findall(f"{_M}e")
        ]
        middle = f"\\middle{_delimiter(separator, side='middle')}" if separator else ""
        return (
            f"\\left{_delimiter(left, side='left')}"
            + middle.join(segments)
            + f"\\right{_delimiter(right, side='right')}"
        )
    if name == "m":
        rows = []
        for row in element.findall(f"{_M}mr"):
            rows.append("&".join(
                _serialize_children(cell)
                for cell in row.findall(f"{_M}e")
            ))
        return r"\begin{matrix}" + r"\\".join(rows) + r"\end{matrix}"
    if name == "eqArr":
        rows = [
            _serialize_children(row, alignment=True)
            for row in element.findall(f"{_M}e")
        ]
        return r"\begin{aligned}" + r"\\".join(rows) + r"\end{aligned}"
    if name == "acc":
        character = _property_value(element, "accPr", "chr", "")
        command = _ACCENT_COMMAND_BY_CHARACTER.get(character)
        if character == "̸":
            command = "not"
        if command is None:
            raise FormulaImportError(f"unsupported reversible accent: {character!r}")
        return f"\\{command}{{{_serialize_argument(element, 'e')}}}"
    if name == "bar":
        position = _property_value(element, "barPr", "pos", "top")
        command = "overline" if position == "top" else "underline"
        return f"\\{command}{{{_serialize_argument(element, 'e')}}}"
    if name == "groupChr":
        key = (
            _property_value(element, "groupChrPr", "chr", ""),
            _property_value(element, "groupChrPr", "pos", "top"),
            _property_value(element, "groupChrPr", "vertJc", "bot"),
        )
        command = _GROUP_COMMANDS.get(key)
        if command is None:
            raise FormulaImportError(f"unsupported reversible group character: {key!r}")
        return f"\\{command}{{{_serialize_argument(element, 'e')}}}"
    if name == "limLow":
        base = _serialize_argument(element, "e")
        lower = _serialize_argument(element, "lim")
        return f"\\underset{{{lower}}}{{{base}}}"
    if name == "limUpp":
        base = _serialize_argument(element, "e")
        upper = _serialize_argument(element, "lim")
        return f"\\overset{{{upper}}}{{{base}}}"
    if name == "func":
        function_name = _serialize_argument(element, "fName")
        body = _serialize_optional_argument(element, "e")
        source = f"\\mathop{{{function_name}}}"
        return source + (f"{{{body}}}" if body else "")
    if name == "box":
        enabled = _property_value(element, "boxPr", "opEmu", "off")
        if enabled not in {"on", "true", "1"}:
            raise FormulaImportError("only operator-emulator m:box is reversible")
        return f"\\mathrel{{{_serialize_argument(element, 'e')}}}"
    if name == "phant":
        properties = element.find(f"{_M}phantPr")
        zero_width = _on_property(properties, "zeroWid")
        zero_ascent = _on_property(properties, "zeroAsc")
        zero_descent = _on_property(properties, "zeroDesc")
        if zero_width:
            command = "vphantom"
        elif zero_ascent and zero_descent:
            command = "hphantom"
        else:
            command = "phantom"
        return f"\\{command}{{{_serialize_argument(element, 'e')}}}"
    if name == "borderBox":
        properties = element.find(f"{_M}borderBoxPr")
        rising = _on_property(properties, "strikeBLTR")
        falling = _on_property(properties, "strikeTLBR")
        hidden = all(
            _on_property(properties, side)
            for side in ("hideTop", "hideBot", "hideLeft", "hideRight")
        )
        if hidden and rising and falling:
            command = "xcancel"
        elif hidden and rising:
            command = "cancel"
        elif hidden and falling:
            command = "bcancel"
        elif not hidden and not rising and not falling:
            command = "boxed"
        else:
            raise FormulaImportError("unsupported reversible border-box properties")
        return f"\\{command}{{{_serialize_argument(element, 'e')}}}"
    if name in {"e", "deg", "den", "fName", "lim", "num", "sub", "sup"}:
        return _serialize_children(element, alignment=alignment)
    raise FormulaImportError(f"unsupported reversible Office Math element: m:{name}")


def _serialize_optional_argument(owner: ET.Element, name: str) -> str:
    element = owner.find(f"{_M}{name}")
    return _serialize_children(element) if element is not None else ""


def _scripted(base: str, subscript: str, superscript: str) -> str:
    if subscript:
        base += f"_{{{subscript}}}"
    if superscript:
        base += f"^{{{superscript}}}"
    return base


def _serialize_run(run: ET.Element, *, alignment: bool) -> str:
    text_element = run.find(f"{_M}t")
    value = text_element.text or "" if text_element is not None else ""
    properties = run.find(f"{_M}rPr")
    literal = _on_property(properties, "lit")
    normal = _on_property(properties, "nor")
    source = _escape_text(value, alignment=alignment and not literal, text_mode=normal)
    if not source:
        return ""
    drawing = run.find(f"{_A}rPr")
    if normal:
        typeface = ""
        if drawing is not None:
            latin = drawing.find(f"{_A}latin")
            typeface = latin.get("typeface", "") if latin is not None else ""
        text_command = {
            "Arial": "textsf",
            "Courier New": "texttt",
        }.get(typeface, "text")
        source = f"\\{text_command}{{{source}}}"
        if drawing is not None and _drawing_on(drawing, "b"):
            source = f"\\textbf{{{source}}}"
        if drawing is not None and _drawing_on(drawing, "i"):
            source = f"\\textit{{{source}}}"
    else:
        script = _property_child_value(properties, "scr")
        style = _property_child_value(properties, "sty")
        command = {
            "sans-serif": "mathsf",
            "monospace": "mathtt",
            "double-struck": "mathbb",
            "script": "mathcal",
            "fraktur": "mathfrak",
        }.get(script or "")
        if command is None:
            command = {
                "p": "mathrm",
                "b": "mathbf",
                "i": "mathit",
                "bi": "boldsymbol",
            }.get(style or "")
        if command is not None:
            source = f"\\{command}{{{source}}}"
    color = _drawing_color(drawing)
    if color is not None:
        source = f"\\textcolor{{#{color}}}{{{source}}}"
    return source


def _escape_text(value: str, *, alignment: bool, text_mode: bool) -> str:
    parts: list[str] = []
    for character in value:
        if character in _SPACING_LATEX and not text_mode:
            parts.append(_SPACING_LATEX[character])
        elif character == " " and not text_mode:
            parts.append(r"\ ")
        elif character == "&":
            parts.append("&" if alignment else r"\&")
        elif character in "{}_%#$":
            parts.append("\\" + character)
        elif character == "\\":
            parts.append(r"\backslash{}")
        elif character == "~" and not text_mode:
            parts.append(r"\text{~}")
        elif character == "^" and not text_mode:
            parts.append(r"\text{^}")
        else:
            parts.append(character)
    return "".join(parts)


def _delimiter(value: str, *, side: str) -> str:
    if not value:
        return "."
    if value == "|":
        return "|"
    command = _DELIMITER_COMMANDS.get(value)
    if command is not None:
        if value == "‖" and side == "left":
            command = r"\lVert"
        if value == "‖" and side == "right":
            command = r"\rVert"
        if command.startswith("\\") and command[1:].isalpha():
            return command + " "
        return command
    if len(value) == 1:
        return value
    raise FormulaImportError(f"unsupported reversible delimiter: {value!r}")


def _preview_root(root: ET.Element) -> str:
    math = root.find(f"{_M}oMath") if root.tag == f"{_M}oMathPara" else root
    if math is None:
        return ""
    return _preview_children(math)


def _preview_children(parent: ET.Element) -> str:
    return "".join(
        _preview_node(child)
        for child in parent
        if not _local_name(child).endswith(_PROPERTY_SUFFIX)
        and _local_name(child) != "ctrlPr"
    )


def _preview_argument(owner: ET.Element, name: str) -> str:
    child = owner.find(f"{_M}{name}")
    return _preview_children(child) if child is not None else ""


def _preview_node(element: ET.Element) -> str:
    name = _local_name(element)
    if name == "r":
        text = element.find(f"{_M}t")
        return text.text or "" if text is not None else ""
    if name == "f":
        return f"({_preview_argument(element, 'num')})/({_preview_argument(element, 'den')})"
    if name == "rad":
        degree = _preview_argument(element, "deg")
        prefix = f"√[{degree}]" if degree else "√"
        return f"{prefix}({_preview_argument(element, 'e')})"
    if name in {"sSub", "sSup", "sSubSup"}:
        base = _preview_argument(element, "e")
        subscript = _preview_argument(element, "sub")
        superscript = _preview_argument(element, "sup")
        return _preview_script(base, subscript, superscript)
    if name == "sPre":
        prefix = _preview_script(
            "",
            _preview_argument(element, "sub"),
            _preview_argument(element, "sup"),
        )
        return prefix + _preview_argument(element, "e")
    if name == "nary":
        symbol = _property_value(element, "naryPr", "chr", "")
        return _preview_script(
            symbol,
            _preview_argument(element, "sub"),
            _preview_argument(element, "sup"),
        ) + _preview_argument(element, "e")
    if name == "d":
        left = _property_value(element, "dPr", "begChr", "(")
        right = _property_value(element, "dPr", "endChr", ")")
        separator = _property_value(element, "dPr", "sepChr", "")
        segments = [_preview_children(child) for child in element.findall(f"{_M}e")]
        return left + separator.join(segments) + right
    if name == "m":
        rows = [
            ", ".join(_preview_children(cell) for cell in row.findall(f"{_M}e"))
            for row in element.findall(f"{_M}mr")
        ]
        return "[" + "; ".join(rows) + "]"
    if name == "eqArr":
        return "  ".join(
            _preview_children(row)
            for row in element.findall(f"{_M}e")
        )
    if name == "acc":
        return _preview_argument(element, "e") + _property_value(element, "accPr", "chr", "")
    if name == "bar":
        marker = "¯" if _property_value(element, "barPr", "pos", "top") == "top" else "_"
        return marker + f"({_preview_argument(element, 'e')})"
    if name == "groupChr":
        marker = _property_value(element, "groupChrPr", "chr", "")
        return marker + f"({_preview_argument(element, 'e')})"
    if name == "limLow":
        return _preview_script(
            _preview_argument(element, "e"),
            _preview_argument(element, "lim"),
            "",
        )
    if name == "limUpp":
        return _preview_script(
            _preview_argument(element, "e"),
            "",
            _preview_argument(element, "lim"),
        )
    if name == "func":
        return _preview_argument(element, "fName") + _preview_argument(element, "e")
    if name in {"box", "phant"}:
        return _preview_argument(element, "e")
    if name == "borderBox":
        return "□(" + _preview_argument(element, "e") + ")"
    if name in {"e", "deg", "den", "fName", "lim", "num", "sub", "sup"}:
        return _preview_children(element)
    return ""


def _preview_script(base: str, subscript: str, superscript: str) -> str:
    if subscript:
        base += f"_({subscript})"
    if superscript:
        base += f"^({superscript})"
    return base


def _dominant_run_style(root: ET.Element) -> tuple[float, str, str]:
    sizes: list[str] = []
    colors: list[str] = []
    languages: list[str] = []
    for properties in root.iter(f"{_A}rPr"):
        if properties.get("sz"):
            sizes.append(properties.get("sz") or "")
        if properties.get("lang"):
            languages.append(properties.get("lang") or "")
        color = properties.find(f"{_A}solidFill/{_A}srgbClr")
        if color is not None and color.get("val"):
            colors.append(color.get("val") or "")
    raw_size = _dominant(sizes, "2100")
    try:
        font_size = max(1.0, min(400.0, int(raw_size) / 75.0))
    except ValueError:
        font_size = 28.0
    return (
        font_size,
        f"#{_dominant(colors, '000000').upper()}",
        _dominant(languages, "en-US"),
    )


def _formula_alignment(root: ET.Element) -> str:
    if root.tag != f"{_M}oMathPara":
        return "left"
    value = _property_value(root, "oMathParaPr", "jc", "center")
    return {"left": "left", "right": "right"}.get(value, "center")


def _dominant(values: list[str], default: str) -> str:
    return Counter(values).most_common(1)[0][0] if values else default


def _property_value(owner: ET.Element, properties: str, name: str, default: str) -> str:
    container = owner.find(f"{_M}{properties}")
    value = _property_child_value(container, name)
    return value if value is not None else default


def _property_child_value(owner: ET.Element | None, name: str) -> str | None:
    if owner is None:
        return None
    child = owner.find(f"{_M}{name}")
    return child.get(f"{_M}val") if child is not None else None


def _on_property(owner: ET.Element | None, name: str) -> bool:
    return _property_child_value(owner, name) in {"on", "true", "1"}


def _drawing_on(owner: ET.Element, name: str) -> bool:
    return owner.get(name) in {"on", "true", "1"}


def _drawing_color(owner: ET.Element | None) -> str | None:
    if owner is None:
        return None
    color = owner.find(f"{_A}solidFill/{_A}srgbClr")
    return color.get("val") if color is not None else None


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


__all__ = [
    "A14_NS",
    "FormulaImport",
    "FormulaImportError",
    "import_formula",
    "opaque_formula_preview",
]
