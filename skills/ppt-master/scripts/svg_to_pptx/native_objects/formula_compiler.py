#!/usr/bin/env python3
r"""
PPT Master - Native Formula Compiler

Compile a strict, block-only LaTeX subset into editable Office Math XML.

Usage:
    Import compile_latex_to_omml() from the SVG-to-PPTX native-object pipeline.

Examples:
    compile_latex_to_omml(r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}")

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

_MAX_LATEX_LENGTH = 65_536
_MAX_OMML_LENGTH = 1_048_576
_MAX_PARSE_DEPTH = 128
_MAX_OMML_DEPTH = 256
_MAX_AST_NODES = 100_000
_FORBIDDEN_XML_RE = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_LATEX_COMMAND_RE = re.compile(r"\\[A-Za-z]+")
_ENVIRONMENT_NAME_RE = re.compile(r"[A-Za-z]+")
_MATH_ELEMENTS = frozenset({
    "acc",
    "accPr",
    "baseJc",
    "begChr",
    "chr",
    "count",
    "d",
    "deg",
    "degHide",
    "den",
    "dPr",
    "e",
    "endChr",
    "f",
    "fPr",
    "grow",
    "jc",
    "limLoc",
    "m",
    "mc",
    "mcJc",
    "mcPr",
    "mcs",
    "mPr",
    "mr",
    "nary",
    "naryPr",
    "nor",
    "num",
    "oMath",
    "oMathPara",
    "oMathParaPr",
    "plcHide",
    "r",
    "rad",
    "radPr",
    "rPr",
    "scr",
    "sepChr",
    "sSub",
    "sSubSup",
    "sSup",
    "sty",
    "sub",
    "subHide",
    "sup",
    "supHide",
    "t",
    "type",
})
_DRAWING_ELEMENTS = frozenset({"cs", "ea", "latin", "rPr", "solidFill", "srgbClr"})
_MATH_VALUE_ATTRIBUTES = frozenset({"val"})
_DRAWING_ATTRIBUTES = frozenset({"dirty", "lang", "sz", "typeface", "val"})

_GREEK_SYMBOLS = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "varepsilon": "ϵ",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "vartheta": "ϑ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "omicron": "ο",
    "pi": "π",
    "varpi": "ϖ",
    "rho": "ρ",
    "varrho": "ϱ",
    "sigma": "σ",
    "varsigma": "ς",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "varphi": "ϕ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Xi": "Ξ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Upsilon": "Υ",
    "Phi": "Φ",
    "Psi": "Ψ",
    "Omega": "Ω",
}

_UPRIGHT_SYMBOLS = {
    "times": "×",
    "cdot": "·",
    "div": "÷",
    "pm": "±",
    "mp": "∓",
    "le": "≤",
    "leq": "≤",
    "ge": "≥",
    "geq": "≥",
    "ne": "≠",
    "neq": "≠",
    "ll": "≪",
    "gg": "≫",
    "approx": "≈",
    "equiv": "≡",
    "sim": "∼",
    "simeq": "≃",
    "propto": "∝",
    "in": "∈",
    "notin": "∉",
    "ni": "∋",
    "subset": "⊂",
    "supset": "⊃",
    "subseteq": "⊆",
    "supseteq": "⊇",
    "cup": "∪",
    "cap": "∩",
    "setminus": "∖",
    "emptyset": "∅",
    "to": "→",
    "rightarrow": "→",
    "leftarrow": "←",
    "leftrightarrow": "↔",
    "Rightarrow": "⇒",
    "Leftarrow": "⇐",
    "Leftrightarrow": "⇔",
    "infty": "∞",
    "partial": "∂",
    "nabla": "∇",
    "ell": "ℓ",
    "ldots": "…",
    "cdots": "⋯",
    "forall": "∀",
    "exists": "∃",
    "land": "∧",
    "lor": "∨",
    "neg": "¬",
    "angle": "∠",
    "perp": "⊥",
    "parallel": "∥",
    "degree": "°",
}

_NAMED_OPERATORS = frozenset({
    "arccos",
    "arcsin",
    "arctan",
    "cos",
    "cosh",
    "cot",
    "coth",
    "csc",
    "det",
    "exp",
    "gcd",
    "inf",
    "lim",
    "ln",
    "log",
    "max",
    "min",
    "sec",
    "sin",
    "sinh",
    "sup",
    "tan",
    "tanh",
})

_NARY_SYMBOLS = {
    "sum": ("∑", "undOvr"),
    "prod": ("∏", "undOvr"),
    "int": ("∫", "subSup"),
}

_NARY_BODY_STOP_COMMANDS = frozenset({
    "Rightarrow",
    "Leftarrow",
    "Leftrightarrow",
    "approx",
    "cap",
    "cdot",
    "cup",
    "div",
    "equiv",
    "ge",
    "geq",
    "gg",
    "in",
    "land",
    "le",
    "leq",
    "leftarrow",
    "leftrightarrow",
    "ll",
    "lor",
    "mp",
    "ne",
    "neq",
    "ni",
    "notin",
    "parallel",
    "perp",
    "pm",
    "propto",
    "rightarrow",
    "setminus",
    "sim",
    "simeq",
    "subset",
    "subseteq",
    "supset",
    "supseteq",
    "times",
    "to",
})

_DELIMITER_COMMANDS = {
    "lbrace": "{",
    "rbrace": "}",
    "langle": "⟨",
    "rangle": "⟩",
    "lfloor": "⌊",
    "rfloor": "⌋",
    "lceil": "⌈",
    "rceil": "⌉",
    "vert": "|",
    "Vert": "‖",
}

_ENVIRONMENT_DELIMITERS = {
    "matrix": None,
    "pmatrix": ("(", ")"),
    "bmatrix": ("[", "]"),
    "vmatrix": ("|", "|"),
    "Vmatrix": ("‖", "‖"),
    "cases": ("{", ""),
    "aligned": None,
}

_ACCENT_COMMANDS = {
    "bar": "‾",
    "hat": "̂",
    "overline": "‾",
    "vec": "⃗",
}


class FormulaCompileError(ValueError):
    """Raised when formula source or OMML violates the supported contract."""


@dataclass(frozen=True)
class _RunStyle:
    style: str | None = None
    normal: bool = False
    script: str | None = None


@dataclass(frozen=True)
class _Text:
    value: str
    style: _RunStyle | None = None


@dataclass(frozen=True)
class _Sequence:
    children: tuple[_Node, ...]


@dataclass(frozen=True)
class _Styled:
    body: _Sequence
    style: _RunStyle


@dataclass(frozen=True)
class _Fraction:
    numerator: _Sequence
    denominator: _Sequence


@dataclass(frozen=True)
class _Radical:
    body: _Sequence
    degree: _Sequence | None = None


@dataclass(frozen=True)
class _Script:
    base: _Node
    subscript: _Sequence | None = None
    superscript: _Sequence | None = None


@dataclass(frozen=True)
class _Nary:
    symbol: str
    limit_location: str
    subscript: _Sequence | None = None
    superscript: _Sequence | None = None
    body: _Sequence | None = None
    limit_modifier: str | None = None


@dataclass(frozen=True)
class _Delimiter:
    left: str
    right: str
    body: _Sequence


@dataclass(frozen=True)
class _Matrix:
    environment: str
    rows: tuple[tuple[_Sequence, ...], ...]


@dataclass(frozen=True)
class _Accent:
    character: str
    body: _Sequence


_Node = (
    _Text
    | _Sequence
    | _Styled
    | _Fraction
    | _Radical
    | _Script
    | _Nary
    | _Delimiter
    | _Matrix
    | _Accent
)

_ROMAN_STYLE = _RunStyle(style="p")
_TEXT_STYLE = _RunStyle(style="p", normal=True)
_SPACING_STYLE = _RunStyle()
_PLAIN_OPERATOR_CHARS = frozenset("+−*/=<>±∓×÷·,;:!?")
_SPACING_COMMANDS = {
    ",": "\u2009",
    ":": "\u2005",
    ";": "\u2004",
    "!": "\u200b",
    " ": "\u2005",
}


class _LatexParser:
    """Parse the intentionally small formula-source grammar."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0
        self.depth = 0
        self.text_mode_depth = 0

    def parse(self) -> _Sequence:
        result = self._parse_sequence()
        if self.position != len(self.source):
            self._fail("Unexpected trailing formula source")
        if _is_empty(result):
            self._fail("Formula is empty")
        return result

    def _parse_sequence(
        self,
        *,
        terminator: str | None = None,
        stop_at_right: bool = False,
        stop_at_environment_boundary: bool = False,
    ) -> _Sequence:
        children: list[_Node] = []
        while self.position < len(self.source):
            if terminator is not None and self.source[self.position] == terminator:
                self.position += 1
                return _Sequence(tuple(children))
            if stop_at_right and self._at_control_word("right"):
                return _Sequence(tuple(children))
            if stop_at_environment_boundary and (
                self.source[self.position] == "&"
                or self.source.startswith("\\\\", self.position)
                or self._at_control_word("end")
            ):
                return _Sequence(tuple(children))

            char = self.source[self.position]
            if char == "}":
                self._fail("Unexpected closing group")
            if char in "^_":
                self._fail(f"Script marker {char!r} has no base")
            if char == "&":
                self._fail("Alignment marker '&' is only valid inside a matrix environment")

            atom = self._parse_complete_atom()
            _append_child(children, atom)

        if terminator is not None:
            self._fail(f"Unclosed group; expected {terminator!r}")
        if stop_at_right:
            self._fail("Unclosed delimiter; expected \\right")
        if stop_at_environment_boundary:
            self._fail("Unclosed matrix environment")
        return _Sequence(tuple(children))

    def _parse_atom(self) -> _Node:
        char = self.source[self.position]
        if char.isspace():
            while (
                self.position < len(self.source)
                and self.source[self.position].isspace()
            ):
                self.position += 1
            return (
                _Text(" ", _TEXT_STYLE)
                if self.text_mode_depth
                else _Sequence(())
            )
        if char == "{":
            return self._parse_group()
        if char == "\\":
            return self._parse_command()
        if char in "$#%":
            self._fail(f"Unsupported TeX syntax character {char!r}")
        if ord(char) < 32:
            self._fail("Unsupported control character")

        self.position += 1
        if char == "-":
            char = "−"
        elif char == "~":
            return _Text("\u2005", _SPACING_STYLE)
        style = _ROMAN_STYLE if char in _PLAIN_OPERATOR_CHARS else None
        return _Text(char, style)

    def _parse_command(self) -> _Node:
        command_start = self.position
        self.position += 1
        if self.position >= len(self.source):
            self._fail("Trailing backslash", position=command_start)

        char = self.source[self.position]
        if not _is_command_letter(char):
            self.position += 1
            if char == "\\":
                self._fail(
                    "Row separator '\\\\' is only valid inside a matrix environment",
                    position=command_start,
                )
            escaped = {
                "{": "{",
                "}": "}",
                "_": "_",
                "%": "%",
                "#": "#",
                "$": "$",
                "&": "&",
                "|": "‖",
            }
            if char in escaped:
                return _Text(escaped[char])
            if char in _SPACING_COMMANDS:
                return _Text(_SPACING_COMMANDS[char], _SPACING_STYLE)
            self._fail(f"Unsupported control symbol \\{char}", position=command_start)

        command = self._read_control_word_body()
        self._skip_whitespace()

        if command in _GREEK_SYMBOLS:
            return _Text(_GREEK_SYMBOLS[command])
        if command in _UPRIGHT_SYMBOLS:
            return _Text(_UPRIGHT_SYMBOLS[command], _ROMAN_STYLE)
        if command in _NAMED_OPERATORS:
            return _Text(command, _ROMAN_STYLE)
        if command in _DELIMITER_COMMANDS:
            return _Text(_DELIMITER_COMMANDS[command], _ROMAN_STYLE)
        if command in _NARY_SYMBOLS:
            symbol, limit_location = _NARY_SYMBOLS[command]
            return _Nary(symbol=symbol, limit_location=limit_location)
        if command == "frac":
            numerator = self._parse_required_group("fraction numerator")
            denominator = self._parse_required_group("fraction denominator")
            return _Fraction(numerator=numerator, denominator=denominator)
        if command == "sqrt":
            degree = self._parse_optional_degree()
            body = self._parse_required_group("radical body")
            return _Radical(body=body, degree=degree)
        if command == "left":
            return self._parse_delimited_expression()
        if command == "right":
            self._fail("Unexpected \\right without matching \\left", position=command_start)
        if command == "begin":
            return self._parse_environment()
        if command == "end":
            self._fail("Unexpected \\end without matching \\begin", position=command_start)
        if command in {"text", "mathrm", "mathbf", "mathit", "mathbb", "mathcal"}:
            styles = {
                "text": _TEXT_STYLE,
                "mathrm": _ROMAN_STYLE,
                "mathbf": _RunStyle(style="b"),
                "mathit": _RunStyle(style="i"),
                "mathbb": _RunStyle(style="p", script="double-struck"),
                "mathcal": _RunStyle(style="p", script="script"),
            }
            if command == "text":
                self.text_mode_depth += 1
            try:
                body = self._parse_required_group(f"\\{command} body")
            finally:
                if command == "text":
                    self.text_mode_depth -= 1
            return _Styled(body=body, style=styles[command])
        if command in _ACCENT_COMMANDS:
            body = self._parse_required_group(f"\\{command} body")
            return _Accent(character=_ACCENT_COMMANDS[command], body=body)
        if command == "quad":
            return _Text("\u2001", _SPACING_STYLE)
        if command == "qquad":
            return _Text("\u2001\u2001", _SPACING_STYLE)

        self._fail(f"Unsupported LaTeX command \\{command}", position=command_start)

    def _parse_group(self) -> _Sequence:
        self.position += 1
        return self._parse_nested_sequence(terminator="}")

    def _parse_required_group(self, description: str) -> _Sequence:
        self._skip_whitespace()
        if self.position >= len(self.source) or self.source[self.position] != "{":
            self._fail(f"{description.capitalize()} must use a braced group")
        result = self._parse_group()
        if _is_empty(result):
            self._fail(f"{description.capitalize()} cannot be empty")
        return result

    def _parse_optional_degree(self) -> _Sequence | None:
        if self.position >= len(self.source) or self.source[self.position] != "[":
            return None
        self.position += 1
        result = self._parse_nested_sequence(terminator="]")
        if _is_empty(result):
            self._fail("Radical degree cannot be empty")
        return result

    def _parse_nested_sequence(self, **kwargs: object) -> _Sequence:
        self.depth += 1
        if self.depth > _MAX_PARSE_DEPTH:
            self._fail(f"Formula nesting exceeds {_MAX_PARSE_DEPTH} levels")
        try:
            return self._parse_sequence(**kwargs)
        finally:
            self.depth -= 1

    def _parse_scripts(self, base: _Node) -> _Node:
        subscript: _Sequence | None = None
        superscript: _Sequence | None = None
        while True:
            saved_position = self.position
            self._skip_whitespace()
            if (
                self.position >= len(self.source)
                or self.source[self.position] not in "^_"
            ):
                self.position = saved_position
                break

            marker = self.source[self.position]
            self.position += 1
            self._skip_whitespace()
            argument = self._parse_script_argument(marker)
            if marker == "_":
                if subscript is not None:
                    self._fail("Duplicate subscript for one base")
                subscript = argument
            else:
                if superscript is not None:
                    self._fail("Duplicate superscript for one base")
                superscript = argument

        if subscript is None and superscript is None:
            return base
        if isinstance(base, _Nary):
            return _Nary(
                symbol=base.symbol,
                limit_location=base.limit_location,
                subscript=subscript,
                superscript=superscript,
                body=base.body,
                limit_modifier=base.limit_modifier,
            )
        return _Script(base=base, subscript=subscript, superscript=superscript)

    def _parse_complete_atom(self) -> _Node:
        atom = self._parse_atom()
        if isinstance(atom, _Nary):
            atom = self._parse_nary_limit_modifier(atom)
        atom = self._parse_scripts(atom)
        if isinstance(atom, _Nary):
            atom = self._parse_nary_limit_modifier(atom)
            atom = self._parse_nary_body(atom)
        return atom

    def _parse_nary_limit_modifier(self, node: _Nary) -> _Nary:
        saved_position = self.position
        self._skip_whitespace()
        if self._at_control_word("limits"):
            limit_location = "undOvr"
            command = "limits"
        elif self._at_control_word("nolimits"):
            limit_location = "subSup"
            command = "nolimits"
        else:
            self.position = saved_position
            return node

        if node.limit_modifier is not None:
            self._fail("N-ary operator has more than one limit modifier")
        self._consume_control_word(command)
        return _Nary(
            symbol=node.symbol,
            limit_location=limit_location,
            subscript=node.subscript,
            superscript=node.superscript,
            body=node.body,
            limit_modifier=command,
        )

    def _parse_nary_body(self, node: _Nary) -> _Nary:
        saved_position = self.position
        spacing = self._parse_nary_spacing()
        if not self._nary_body_follows():
            self.position = saved_position
            return node

        if self.source[self.position] == "{":
            operand = self._parse_group()
        else:
            operand = _Sequence((self._parse_nested_atom(),))
        body = _Sequence((*spacing, *operand.children))
        if _is_empty(body):
            self._fail("N-ary operator body cannot be empty")
        return _Nary(
            symbol=node.symbol,
            limit_location=node.limit_location,
            subscript=node.subscript,
            superscript=node.superscript,
            body=body,
            limit_modifier=node.limit_modifier,
        )

    def _parse_nested_atom(self) -> _Node:
        """Parse one recursively owned atom under the shared depth limit."""
        self.depth += 1
        if self.depth > _MAX_PARSE_DEPTH:
            self._fail(f"Formula nesting exceeds {_MAX_PARSE_DEPTH} levels")
        try:
            return self._parse_complete_atom()
        finally:
            self.depth -= 1

    def _parse_nary_spacing(self) -> tuple[_Node, ...]:
        """Consume spacing before a n-ary operand without losing explicit TeX."""
        spacing: list[_Node] = []
        while True:
            self._skip_whitespace()
            if self._at_control_word("quad"):
                self._consume_control_word("quad")
                spacing.append(_Text("\u2001", _SPACING_STYLE))
                continue
            if self._at_control_word("qquad"):
                self._consume_control_word("qquad")
                spacing.append(_Text("\u2001\u2001", _SPACING_STYLE))
                continue
            if (
                self.position + 1 < len(self.source)
                and self.source[self.position] == "\\"
                and self.source[self.position + 1] in {",", ";", ":", "!", " "}
            ):
                command = self.source[self.position + 1]
                self.position += 2
                spacing.append(_Text(_SPACING_COMMANDS[command], _SPACING_STYLE))
                continue
            return tuple(spacing)

    def _nary_body_follows(self) -> bool:
        if self.position >= len(self.source):
            return False
        if self.source.startswith("\\\\", self.position):
            return False
        char = self.source[self.position]
        if char in "}])&^_+-=<>/,;:!?":
            return False
        if char != "\\":
            return True
        if self._at_control_word("right") or self._at_control_word("end"):
            return False
        command_position = self.position + 1
        command_end = command_position
        while (
            command_end < len(self.source)
            and _is_command_letter(self.source[command_end])
        ):
            command_end += 1
        command = self.source[command_position:command_end]
        return command not in _NARY_BODY_STOP_COMMANDS

    def _parse_script_argument(self, marker: str) -> _Sequence:
        if self.position >= len(self.source):
            self._fail(f"Script marker {marker!r} has no argument")
        if self.source[self.position] == "{":
            result = self._parse_group()
        else:
            result = _Sequence((self._parse_atom(),))
        if _is_empty(result):
            self._fail(f"Script marker {marker!r} has an empty argument")
        return result

    def _parse_delimited_expression(self) -> _Delimiter:
        left = self._parse_delimiter_token("\\left")
        body = self._parse_nested_sequence(stop_at_right=True)
        self._consume_control_word("right")
        right = self._parse_delimiter_token("\\right")
        return _Delimiter(left=left, right=right, body=body)

    def _parse_delimiter_token(self, owner: str) -> str:
        self._skip_whitespace()
        if self.position >= len(self.source):
            self._fail(f"{owner} requires a delimiter")

        char = self.source[self.position]
        if char != "\\":
            self.position += 1
            if char in "()[]|.":
                return "" if char == "." else char
            self._fail(f"Unsupported delimiter {char!r} after {owner}")

        command_start = self.position
        self.position += 1
        if self.position >= len(self.source):
            self._fail(f"{owner} requires a delimiter", position=command_start)
        if not _is_command_letter(self.source[self.position]):
            delimiter = self.source[self.position]
            self.position += 1
            if delimiter in "{}|":
                return "‖" if delimiter == "|" else delimiter
            self._fail(f"Unsupported delimiter command \\{delimiter}", position=command_start)

        command = self._read_control_word_body()
        self._skip_whitespace()
        if command not in _DELIMITER_COMMANDS:
            self._fail(f"Unsupported delimiter command \\{command}", position=command_start)
        return _DELIMITER_COMMANDS[command]

    def _parse_environment(self) -> _Matrix:
        environment = self._parse_environment_name("\\begin")
        if environment not in _ENVIRONMENT_DELIMITERS:
            self._fail(f"Unsupported formula environment {environment!r}")

        rows: list[tuple[_Sequence, ...]] = []
        row: list[_Sequence] = []
        while True:
            cell = self._parse_nested_sequence(stop_at_environment_boundary=True)
            if _is_empty(cell):
                self._fail(f"Environment {environment!r} contains an empty cell")
            row.append(cell)

            if self.source[self.position] == "&":
                self.position += 1
                continue
            if self.source.startswith("\\\\", self.position):
                self.position += 2
                rows.append(tuple(row))
                row = []
                self._skip_whitespace()
                if self._at_control_word("end"):
                    self._consume_environment_end(environment)
                    break
                continue
            if self._at_control_word("end"):
                rows.append(tuple(row))
                self._consume_environment_end(environment)
                break
            self._fail(f"Malformed environment {environment!r}")

        column_count = len(rows[0])
        if any(len(current_row) != column_count for current_row in rows):
            self._fail(f"Environment {environment!r} has inconsistent column counts")
        return _Matrix(environment=environment, rows=tuple(rows))

    def _consume_environment_end(self, expected: str) -> None:
        self._consume_control_word("end")
        actual = self._parse_environment_name("\\end")
        if actual != expected:
            self._fail(
                f"Mismatched environment ending: expected {expected!r}, got {actual!r}"
            )

    def _parse_environment_name(self, owner: str) -> str:
        if self.position >= len(self.source) or self.source[self.position] != "{":
            self._fail(f"{owner} requires a braced environment name")
        closing = self.source.find("}", self.position + 1)
        if closing < 0:
            self._fail(f"Unclosed environment name after {owner}")
        name = self.source[self.position + 1 : closing]
        if not _ENVIRONMENT_NAME_RE.fullmatch(name):
            self._fail(f"Invalid environment name {name!r}")
        self.position = closing + 1
        return name

    def _at_control_word(self, expected: str) -> bool:
        prefix = f"\\{expected}"
        if not self.source.startswith(prefix, self.position):
            return False
        following = self.position + len(prefix)
        return (
            following >= len(self.source)
            or not _is_command_letter(self.source[following])
        )

    def _consume_control_word(self, expected: str) -> None:
        if not self._at_control_word(expected):
            self._fail(f"Expected \\{expected}")
        self.position += len(expected) + 1
        self._skip_whitespace()

    def _read_control_word_body(self) -> str:
        start = self.position
        while (
            self.position < len(self.source)
            and _is_command_letter(self.source[self.position])
        ):
            self.position += 1
        return self.source[start : self.position]

    def _skip_whitespace(self) -> None:
        while (
            self.position < len(self.source)
            and self.source[self.position].isspace()
        ):
            self.position += 1

    def _fail(self, message: str, *, position: int | None = None) -> None:
        offset = self.position if position is None else position
        start = max(0, offset - 12)
        end = min(len(self.source), offset + 12)
        context = self.source[start:end].replace("\n", " ")
        raise FormulaCompileError(f"{message} at offset {offset}: {context!r}")


def _is_command_letter(char: str) -> bool:
    return char.isascii() and char.isalpha()


def _xml_character_allowed(char: str) -> bool:
    codepoint = ord(char)
    return (
        codepoint in {0x09, 0x0A, 0x0D}
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def _append_child(children: list[_Node], node: _Node) -> None:
    if isinstance(node, _Sequence) and not node.children:
        return
    if (
        isinstance(node, _Text)
        and children
        and isinstance(children[-1], _Text)
        and children[-1].style == node.style
    ):
        previous = children[-1]
        children[-1] = _Text(previous.value + node.value, node.style)
        return
    children.append(node)


def _is_empty(node: _Node) -> bool:
    if isinstance(node, _Text):
        return not node.value
    if isinstance(node, _Sequence):
        return not node.children or all(_is_empty(child) for child in node.children)
    if isinstance(node, _Styled):
        return _is_empty(node.body)
    return False


def _formula_node_count(root: _Node) -> int:
    """Return iterative AST size and reject impractically complex formulas."""
    pending: list[_Node] = [root]
    count = 0
    while pending:
        node = pending.pop()
        count += 1
        if count > _MAX_AST_NODES:
            raise FormulaCompileError(
                f"Formula exceeds the {_MAX_AST_NODES}-node complexity limit"
            )
        if isinstance(node, _Sequence):
            pending.extend(reversed(node.children))
        elif isinstance(node, _Styled):
            pending.append(node.body)
        elif isinstance(node, _Fraction):
            pending.extend((node.denominator, node.numerator))
        elif isinstance(node, _Radical):
            pending.append(node.body)
            if node.degree is not None:
                pending.append(node.degree)
        elif isinstance(node, _Script):
            pending.append(node.base)
            if node.subscript is not None:
                pending.append(node.subscript)
            if node.superscript is not None:
                pending.append(node.superscript)
        elif isinstance(node, _Nary):
            if node.subscript is not None:
                pending.append(node.subscript)
            if node.superscript is not None:
                pending.append(node.superscript)
            if node.body is not None:
                pending.append(node.body)
        elif isinstance(node, _Delimiter):
            pending.append(node.body)
        elif isinstance(node, _Matrix):
            for row in reversed(node.rows):
                pending.extend(reversed(row))
        elif isinstance(node, _Accent):
            pending.append(node.body)
    return count


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


def _append_run(parent: ET.Element, value: str, style: _RunStyle | None) -> None:
    if not value:
        return
    run = _math_element(parent, "r")
    if style is not None and (style.style or style.normal or style.script):
        properties = _math_element(run, "rPr")
        if style.normal:
            _math_element(properties, "nor", val="on")
        if style.style:
            _math_element(properties, "sty", val=style.style)
        if style.script:
            _math_element(properties, "scr", val=style.script)
    text = _math_element(run, "t")
    if value != value.strip() or "  " in value:
        text.set(f"{{{XML_NS}}}space", "preserve")
    text.text = value


def _append_node(
    parent: ET.Element,
    node: _Node,
    inherited_style: _RunStyle | None = None,
) -> None:
    if isinstance(node, _Text):
        _append_run(parent, node.value, node.style or inherited_style)
        return
    if isinstance(node, _Sequence):
        for child in node.children:
            _append_node(parent, child, inherited_style)
        return
    if isinstance(node, _Styled):
        _append_node(parent, node.body, node.style)
        return
    if isinstance(node, _Fraction):
        fraction = _math_element(parent, "f")
        properties = _math_element(fraction, "fPr")
        _math_element(properties, "type", val="bar")
        numerator = _math_element(fraction, "num")
        _append_node(numerator, node.numerator, inherited_style)
        denominator = _math_element(fraction, "den")
        _append_node(denominator, node.denominator, inherited_style)
        return
    if isinstance(node, _Radical):
        radical = _math_element(parent, "rad")
        properties = _math_element(radical, "radPr")
        _math_element(properties, "degHide", val="off" if node.degree else "on")
        degree = _math_element(radical, "deg")
        if node.degree is not None:
            _append_node(degree, node.degree, inherited_style)
        body = _math_element(radical, "e")
        _append_node(body, node.body, inherited_style)
        return
    if isinstance(node, _Script):
        _append_script(parent, node, inherited_style)
        return
    if isinstance(node, _Nary):
        _append_nary(parent, node, inherited_style)
        return
    if isinstance(node, _Delimiter):
        delimiter = _math_element(parent, "d")
        properties = _math_element(delimiter, "dPr")
        _math_element(properties, "begChr", val=node.left)
        _math_element(properties, "endChr", val=node.right)
        _math_element(properties, "sepChr", val="")
        _math_element(properties, "grow")
        body = _math_element(delimiter, "e")
        _append_node(body, node.body, inherited_style)
        return
    if isinstance(node, _Matrix):
        _append_matrix(parent, node, inherited_style)
        return
    if isinstance(node, _Accent):
        accent = _math_element(parent, "acc")
        properties = _math_element(accent, "accPr")
        _math_element(properties, "chr", val=node.character)
        body = _math_element(accent, "e")
        _append_node(body, node.body, inherited_style)
        return
    raise FormulaCompileError(f"Unsupported internal formula node: {type(node).__name__}")


def _append_script(
    parent: ET.Element,
    node: _Script,
    inherited_style: _RunStyle | None,
) -> None:
    if node.subscript is not None and node.superscript is not None:
        script = _math_element(parent, "sSubSup")
    elif node.subscript is not None:
        script = _math_element(parent, "sSub")
    else:
        script = _math_element(parent, "sSup")

    base = _math_element(script, "e")
    _append_node(base, node.base, inherited_style)
    if node.subscript is not None:
        subscript = _math_element(script, "sub")
        _append_node(subscript, node.subscript, inherited_style)
    if node.superscript is not None:
        superscript = _math_element(script, "sup")
        _append_node(superscript, node.superscript, inherited_style)


def _append_nary(
    parent: ET.Element,
    node: _Nary,
    inherited_style: _RunStyle | None,
) -> None:
    nary = _math_element(parent, "nary")
    properties = _math_element(nary, "naryPr")
    _math_element(properties, "chr", val=node.symbol)
    _math_element(properties, "limLoc", val=node.limit_location)
    _math_element(properties, "subHide", val="off" if node.subscript else "on")
    _math_element(properties, "supHide", val="off" if node.superscript else "on")

    subscript = _math_element(nary, "sub")
    if node.subscript is not None:
        _append_node(subscript, node.subscript, inherited_style)
    superscript = _math_element(nary, "sup")
    if node.superscript is not None:
        _append_node(superscript, node.superscript, inherited_style)
    body = _math_element(nary, "e")
    if node.body is not None:
        _append_node(body, node.body, inherited_style)


def _append_matrix(
    parent: ET.Element,
    node: _Matrix,
    inherited_style: _RunStyle | None,
) -> None:
    delimiters = _ENVIRONMENT_DELIMITERS[node.environment]
    matrix_parent = parent
    if delimiters is not None:
        delimiter = _math_element(parent, "d")
        properties = _math_element(delimiter, "dPr")
        _math_element(properties, "begChr", val=delimiters[0])
        _math_element(properties, "endChr", val=delimiters[1])
        _math_element(properties, "sepChr", val="")
        _math_element(properties, "grow")
        matrix_parent = _math_element(delimiter, "e")

    matrix = _math_element(matrix_parent, "m")
    properties = _math_element(matrix, "mPr")
    _math_element(properties, "baseJc", val="center")
    _math_element(properties, "plcHide", val="on")
    columns = _math_element(properties, "mcs")
    for index in range(len(node.rows[0])):
        column = _math_element(columns, "mc")
        column_properties = _math_element(column, "mcPr")
        justification = "center"
        if node.environment == "cases":
            justification = "left"
        elif node.environment == "aligned":
            justification = "right" if index % 2 == 0 else "left"
        _math_element(column_properties, "mcJc", val=justification)
        _math_element(column_properties, "count", val="1")

    for row_data in node.rows:
        row = _math_element(matrix, "mr")
        for cell_data in row_data:
            cell = _math_element(row, "e")
            _append_node(cell, cell_data, inherited_style)


def _qualified_name(name: str) -> tuple[str | None, str]:
    if name.startswith("{") and "}" in name:
        namespace, local_name = name[1:].split("}", 1)
        return namespace, local_name
    return None, name


def _validate_xml_tree(root: ET.Element) -> None:
    namespace, local_name = _qualified_name(root.tag)
    if namespace != MATH_NS or local_name not in {"oMathPara", "oMath"}:
        raise FormulaCompileError("OMML root must be m:oMathPara or m:oMath")

    math_roots = 0
    visible_text: list[str] = []
    pending: list[tuple[ET.Element, int]] = [(root, 1)]
    while pending:
        element, depth = pending.pop()
        if depth > _MAX_OMML_DEPTH:
            raise FormulaCompileError(
                f"OMML nesting exceeds {_MAX_OMML_DEPTH} levels"
            )
        pending.extend((child, depth + 1) for child in reversed(element))
        element_namespace, element_name = _qualified_name(element.tag)
        if (
            element_namespace == MATH_NS
            and element_name not in _MATH_ELEMENTS
        ):
            raise FormulaCompileError(
                f"OMML contains unsupported math element: {element_name!r}"
            )
        if (
            element_namespace == DRAWING_NS
            and element_name not in _DRAWING_ELEMENTS
        ):
            raise FormulaCompileError(
                f"OMML contains unsupported DrawingML element: {element_name!r}"
            )
        if element_namespace not in {MATH_NS, DRAWING_NS}:
            raise FormulaCompileError(
                f"OMML contains unsupported element namespace: {element_namespace!r}"
            )
        if element_namespace == MATH_NS and element_name in {"oMathPara", "oMath"}:
            math_roots += 1
        for attribute in element.attrib:
            attribute_namespace, attribute_name = _qualified_name(attribute)
            if (
                attribute_namespace == MATH_NS
                and attribute_name in _MATH_VALUE_ATTRIBUTES
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
                and element.attrib[attribute] == "preserve"
            ):
                continue
            if attribute_namespace is not None or attribute_name:
                raise FormulaCompileError(
                    f"OMML contains unsupported attribute {attribute_name!r}"
                )
        if element.text:
            if element_namespace == MATH_NS and element_name == "t":
                visible_text.append(element.text)
            elif element.text.strip():
                raise FormulaCompileError(
                    f"OMML text is only allowed inside m:t, found in {element_name!r}"
                )
        if element.tail and element.tail.strip():
            raise FormulaCompileError("OMML contains unexpected trailing text")

    expected_roots = 2 if local_name == "oMathPara" else 1
    if math_roots != expected_roots:
        raise FormulaCompileError("OMML must contain exactly one math expression")
    if _LATEX_COMMAND_RE.search("".join(visible_text)):
        raise FormulaCompileError("OMML contains an uncompiled LaTeX command")

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


def validate_omml_fragment(xml: str) -> str:
    """Validate the supported Office Math subset and canonicalize prefixes."""
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
    _validate_xml_tree(root)

    ET.register_namespace("m", MATH_NS)
    ET.register_namespace("a", DRAWING_NS)
    try:
        canonical = ET.tostring(
            root,
            encoding="unicode",
            short_empty_elements=True,
        )
    except RecursionError as exc:
        raise FormulaCompileError(
            "OMML nesting exceeds the XML serializer limit"
        ) from exc
    if len(canonical) > _MAX_OMML_LENGTH:
        raise FormulaCompileError(
            f"Canonical OMML exceeds the {_MAX_OMML_LENGTH}-character limit"
        )
    return canonical


def compile_latex_to_omml(latex: str) -> str:
    """Compile one standalone block formula into canonical m:oMathPara XML."""
    if not isinstance(latex, str):
        raise FormulaCompileError("LaTeX formula must be a string")
    if len(latex) > _MAX_LATEX_LENGTH:
        raise FormulaCompileError(
            f"LaTeX formula exceeds the {_MAX_LATEX_LENGTH}-character limit"
        )
    source = latex.strip()
    if not source:
        raise FormulaCompileError("LaTeX formula is empty")
    if any(not _xml_character_allowed(char) for char in source):
        raise FormulaCompileError(
            "LaTeX formula contains an invalid XML character"
        )

    expression = _LatexParser(source).parse()
    _formula_node_count(expression)

    root = ET.Element(_math_tag("oMathPara"))
    properties = _math_element(root, "oMathParaPr")
    _math_element(properties, "jc", val="center")
    math = _math_element(root, "oMath")
    _append_node(math, expression)

    ET.register_namespace("m", MATH_NS)
    xml = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    return validate_omml_fragment(xml)


__all__ = [
    "FormulaCompileError",
    "compile_latex_to_omml",
    "validate_omml_fragment",
]
