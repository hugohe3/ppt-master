#!/usr/bin/env python3
r"""
PPT Master - Microsoft 365 LaTeX Formula Parser

Parse the documented Microsoft 365 LaTeX import profile into the internal
native-formula AST. Unknown commands remain fail-closed.

See references/native-formula.md for the owning authoring contract.

Usage:
    Import parse_latex_formula() from the native formula compiler facade.

Examples:
    parse_latex_formula(r"\binom{n}{k}", display=True)

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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
    append_child,
    is_empty,
    merge_run_styles,
)
from .formula_profile import (
    ACCENT_COMMANDS,
    BARE_DELIMITER_COMMAND_PAIRS,
    COLOR_NAMES,
    DELIMITER_COMMANDS,
    DISCARDED_ARGUMENT_COMMANDS,
    EQUATION_ARRAY_ENVIRONMENTS,
    GREEK_SYMBOLS,
    LIMIT_FUNCTIONS,
    MATRIX_ENVIRONMENTS,
    NARY_COMMANDS,
    NEGATED_SYMBOLS,
    NO_OUTPUT_COMMANDS,
    OPERATOR_BOUNDARY_COMMANDS,
    SPACING_COMMANDS,
    STANDARD_FUNCTIONS,
    SYMBOL_COMMANDS,
    UNSUPPORTED_COMMANDS,
    VARIANT_UPPERCASE_GREEK,
)


_MAX_PARSE_DEPTH = 128
_MAX_MACRO_EXPANSIONS = 500
_MAX_EXPANDED_LENGTH = 1_048_576
_ENVIRONMENT_NAME_RE = re.compile(r"[A-Za-z]+\*?")
_COLOR_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
_LENGTH_RE = re.compile(
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(mu|em|ex|pt)",
    re.IGNORECASE,
)
_BIG_DELIMITER_RE = re.compile(
    r"\\(?:big|Big|bigg|Bigg)([lrm]?)(?![A-Za-z])\s*"
    r"(\\[A-Za-z]+|\\[{}|]|[()\[\]{}|.])"
)
_BIG_LEFT_COMMAND = "pptmasterbigleft"
_BIG_RIGHT_COMMAND = "pptmasterbigright"
_BIG_MIDDLE_COMMAND = "pptmasterbigmiddle"
_BIG_SYMMETRIC_COMMAND = "pptmasterbigsymmetric"
_MIDDLE_DELIMITER_COMMANDS = ("middle", _BIG_MIDDLE_COMMAND)
_RIGHT_DELIMITER_COMMANDS = ("right", _BIG_RIGHT_COMMAND)
_WHITE_OPEN_RE = re.compile(
    r"(?:(?:\\left)?(?:\[|\\lbrack))\\!"
    r"(?:(?:\\left)?(?:\[|\\lbrack))"
)
_WHITE_CLOSE_RE = re.compile(
    r"(?:(?:\\right)?(?:\]|\\rbrack))\\!"
    r"(?:(?:\\right)?(?:\]|\\rbrack))"
)

_ROMAN_STYLE = RunStyle(style="p", is_default=True)
_TEXT_STYLE = RunStyle(normal=True)
_MATH_MODE_RESET_STYLE = RunStyle(
    normal=False,
    bold=False,
    italic=False,
    typeface="",
)
_SPACING_STYLE = RunStyle()
_PLAIN_OPERATOR_CHARS = frozenset("+−*/=<>±∓×÷⋅,;:!?")
_INFIX_FRACTIONS = frozenset({"over", "atop", "choose", "brace", "brack"})

_STYLE_WRAPPERS = {
    "mathrm": RunStyle(style="p"),
    "mathbf": RunStyle(style="b"),
    "mathit": RunStyle(style="i"),
    "mathsf": RunStyle(style="p", script="sans-serif"),
    "mathtt": RunStyle(style="p", script="monospace"),
    "mathbb": RunStyle(style="p", script="double-struck"),
    "Bbb": RunStyle(style="p", script="double-struck"),
    "mathcal": RunStyle(style="p", script="script"),
    "mathscr": RunStyle(style="p", script="script"),
    "mathfrak": RunStyle(style="p", script="fraktur"),
    "boldsymbol": RunStyle(style="bi"),
    "bm": RunStyle(style="bi"),
    "text": _TEXT_STYLE,
    "textrm": _TEXT_STYLE,
    "textnormal": _TEXT_STYLE,
    "textbf": RunStyle(normal=True, bold=True),
    "textit": RunStyle(normal=True, italic=True),
    "emph": RunStyle(normal=True, italic=True),
    "textsf": RunStyle(normal=True, typeface="Arial"),
    "texttt": RunStyle(normal=True, typeface="Courier New"),
    "mbox": _TEXT_STYLE,
    "hbox": _TEXT_STYLE,
}

_DECLARATION_STYLES = {
    "rm": RunStyle(style="p"),
    "bf": RunStyle(style="b"),
    "it": RunStyle(style="i"),
    "cal": RunStyle(style="p", script="script"),
    "frak": RunStyle(style="p", script="fraktur"),
    "sf": RunStyle(style="p", script="sans-serif"),
    "tt": RunStyle(style="p", script="monospace"),
}

_OVER_UNDER_COMMANDS = {
    "overbrace": ("⏞", "top", "bot"),
    "underbrace": ("⏟", "bot", "top"),
    "underrightarrow": ("→", "bot", "top"),
    "underleftarrow": ("←", "bot", "top"),
    "underleftrightarrow": ("↔", "bot", "top"),
}

_OVER_ARROW_COMMANDS = {
    "overrightarrow": "→",
    "overleftarrow": "←",
    "overleftrightarrow": "↔",
}


class FormulaCompileError(ValueError):
    """Raised when formula source violates the Microsoft 365 profile."""


@dataclass(frozen=True)
class _Macro:
    parameter_count: int
    body: str


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


def _read_control_word(source: str, position: int) -> tuple[str, int]:
    if position >= len(source) or source[position] != "\\":
        raise FormulaCompileError("Expected a LaTeX control word")
    position += 1
    start = position
    while position < len(source) and _is_command_letter(source[position]):
        position += 1
    if position == start:
        raise FormulaCompileError("Expected a LaTeX control word")
    return source[start:position], position


def _skip_whitespace(source: str, position: int) -> int:
    while position < len(source) and source[position].isspace():
        position += 1
    return position


def _read_raw_group(source: str, position: int) -> tuple[str, int]:
    position = _skip_whitespace(source, position)
    if position >= len(source) or source[position] != "{":
        raise FormulaCompileError("Expected a braced LaTeX group")
    depth = 1
    cursor = position + 1
    start = cursor
    while cursor < len(source):
        char = source[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:cursor], cursor + 1
        cursor += 1
    raise FormulaCompileError("Unclosed braced LaTeX group")


def _read_optional_integer(source: str, position: int) -> tuple[int | None, int]:
    position = _skip_whitespace(source, position)
    if position >= len(source) or source[position] != "[":
        return None, position
    closing = source.find("]", position + 1)
    if closing < 0:
        raise FormulaCompileError("Unclosed optional macro parameter count")
    raw = source[position + 1:closing].strip()
    if not raw.isdigit() or not 0 <= int(raw) <= 9:
        raise FormulaCompileError("Macro parameter count must be between 0 and 9")
    return int(raw), closing + 1


def _collect_macros(source: str) -> tuple[str, dict[str, _Macro]]:
    macros: dict[str, _Macro] = {}
    output: list[str] = []
    position = 0
    while position < len(source):
        if source[position] != "\\":
            output.append(source[position])
            position += 1
            continue
        try:
            command, command_end = _read_control_word(source, position)
        except FormulaCompileError:
            output.append(source[position])
            position += 1
            continue
        if command not in {"newcommand", "renewcommand", "def"}:
            output.append(source[position:command_end])
            position = command_end
            continue

        cursor = _skip_whitespace(source, command_end)
        if command in {"newcommand", "renewcommand"}:
            name_group, cursor = _read_raw_group(source, cursor)
            name_group = name_group.strip()
            if not re.fullmatch(r"\\[A-Za-z]+", name_group):
                raise FormulaCompileError(
                    f"\\{command} requires one control-word macro name"
                )
            parameter_count, cursor = _read_optional_integer(source, cursor)
            body, cursor = _read_raw_group(source, cursor)
            count = parameter_count or 0
            if re.search(r"#(?:0|[1-9][0-9])", body):
                raise FormulaCompileError("Macro body uses an invalid parameter number")
            macros[name_group[1:]] = _Macro(count, body)
        else:
            if cursor >= len(source) or source[cursor] != "\\":
                raise FormulaCompileError("\\def requires one control-word macro name")
            name, cursor = _read_control_word(source, cursor)
            parameters: list[int] = []
            cursor = _skip_whitespace(source, cursor)
            while cursor < len(source) and source[cursor] == "#":
                if cursor + 1 >= len(source) or source[cursor + 1] not in "123456789":
                    raise FormulaCompileError("\\def parameters must use #1 through #9")
                parameters.append(int(source[cursor + 1]))
                cursor = _skip_whitespace(source, cursor + 2)
            expected = list(range(1, len(parameters) + 1))
            if parameters != expected:
                raise FormulaCompileError("\\def parameters must be consecutive from #1")
            body, cursor = _read_raw_group(source, cursor)
            macros[name] = _Macro(len(parameters), body)
        position = cursor
    return "".join(output), macros


def _read_macro_argument(source: str, position: int) -> tuple[str, int]:
    position = _skip_whitespace(source, position)
    if position >= len(source):
        raise FormulaCompileError("Macro invocation is missing an argument")
    if source[position] == "{":
        return _read_raw_group(source, position)
    if source[position] == "\\":
        if position + 1 >= len(source):
            raise FormulaCompileError("Macro invocation ends with a backslash")
        if _is_command_letter(source[position + 1]):
            _, end = _read_control_word(source, position)
            return source[position:end], end
        return source[position:position + 2], position + 2
    return source[position], position + 1


def _expand_macros(source: str, macros: dict[str, _Macro]) -> str:
    if not macros:
        return source
    expansion_count = 0
    while True:
        output: list[str] = []
        position = 0
        replaced = False
        while position < len(source):
            if source[position] != "\\" or position + 1 >= len(source):
                output.append(source[position])
                position += 1
                continue
            if not _is_command_letter(source[position + 1]):
                output.append(source[position:position + 2])
                position += 2
                continue
            command, cursor = _read_control_word(source, position)
            macro = macros.get(command)
            if macro is None:
                output.append(source[position:cursor])
                position = cursor
                continue
            arguments: list[str] = []
            for _ in range(macro.parameter_count):
                argument, cursor = _read_macro_argument(source, cursor)
                arguments.append(argument)
            body = macro.body
            for index, argument in enumerate(arguments, start=1):
                body = body.replace(f"#{index}", argument)
            output.append(body)
            position = cursor
            expansion_count += 1
            if expansion_count > _MAX_MACRO_EXPANSIONS:
                raise FormulaCompileError(
                    f"Formula exceeds the {_MAX_MACRO_EXPANSIONS}-macro expansion limit"
                )
            replaced = True
        source = "".join(output)
        if len(source) > _MAX_EXPANDED_LENGTH:
            raise FormulaCompileError(
                f"Expanded formula exceeds the {_MAX_EXPANDED_LENGTH}-character limit"
            )
        if not replaced:
            return source


def _strip_outer_delimiters(source: str) -> str:
    pairs = (("$$", "$$"), ("$", "$"), ("\\(", "\\)"), ("\\[", "\\]"))
    for opener, closer in pairs:
        if source.startswith(opener):
            if not source.endswith(closer) or len(source) <= len(opener) + len(closer):
                raise FormulaCompileError(f"Unclosed outer LaTeX delimiter {opener!r}")
            return source[len(opener):-len(closer)].strip()
    return source


def _normalize_big_delimiters(source: str) -> str:
    def replace(match: re.Match[str]) -> str:
        direction = match.group(1)
        delimiter = match.group(2)
        if direction:
            command = {
                "l": _BIG_LEFT_COMMAND,
                "r": _BIG_RIGHT_COMMAND,
                "m": _BIG_MIDDLE_COMMAND,
            }[direction]
            return f"\\{command}{delimiter}"
        openers = {
            "(", "[", "{", ".", r"\{", r"\lbrace", r"\langle", r"\lfloor",
            r"\lceil", r"\lvert", r"\lVert", r"\lbrack",
        }
        closers = {
            ")", "]", "}", r"\}", r"\rbrace", r"\rangle", r"\rfloor",
            r"\rceil", r"\rvert", r"\rVert", r"\rbrack",
        }
        symmetric = {"|", r"\|", r"\vert", r"\Vert"}
        if delimiter in openers:
            return f"\\{_BIG_LEFT_COMMAND}{delimiter}"
        if delimiter in closers:
            return f"\\{_BIG_RIGHT_COMMAND}{delimiter}"
        if delimiter in symmetric:
            return f"\\{_BIG_SYMMETRIC_COMMAND}{delimiter}"
        return delimiter

    return _BIG_DELIMITER_RE.sub(replace, source)


def _normalize_white_brackets(source: str) -> str:
    source = _WHITE_OPEN_RE.sub(r"\\left⟦", source)
    return _WHITE_CLOSE_RE.sub(r"\\right⟧", source)


def _prepare_source(source: str) -> str:
    source = _strip_outer_delimiters(source.strip())
    if "%" in source:
        position = 0
        while position < len(source):
            if source[position] == "%" and (position == 0 or source[position - 1] != "\\"):
                raise FormulaCompileError("Unescaped % comments are outside the Office profile")
            position += 1
    without_definitions, macros = _collect_macros(source)
    expanded = _expand_macros(without_definitions, macros)
    return _normalize_white_brackets(_normalize_big_delimiters(expanded)).strip()


def _space_from_length(raw: str) -> str:
    match = _LENGTH_RE.fullmatch(raw.strip())
    if match is None:
        raise FormulaCompileError(f"Unsupported math spacing length: {raw!r}")
    amount = float(match.group(1))
    unit = match.group(2).lower()
    multiplier = {"mu": 1.0, "em": 18.0, "ex": 9.0, "pt": 1.8}[unit]
    mu = min(2160.0, amount * multiplier)
    if mu <= 0:
        return "\u200b"
    whole_em = int(mu // 18)
    remainder = mu - whole_em * 18
    output = "\u2003" * whole_em
    if remainder >= 14:
        output += "\u2003"
    elif remainder >= 9:
        output += "\u2002"
    elif remainder >= 4.5:
        output += "\u2004"
    elif remainder >= 3.5:
        output += "\u205f"
    elif remainder >= 2:
        output += "\u2009"
    elif remainder > 0:
        output += "\u200b"
    return output or "\u200b"


class _LatexParser:
    """Parse one prepared formula source under the Office import profile."""

    def __init__(
        self,
        source: str,
        *,
        display: bool,
        text_mode: bool = False,
        inherited_style: RunStyle | None = None,
    ) -> None:
        self.source = source
        self.position = 0
        self.depth = 0
        self.display = display
        self.text_mode_depth = 1 if text_mode else 0
        self.current_style = inherited_style
        self.environment_stack: list[str] = []

    def parse(self) -> Sequence:
        result = self._parse_sequence()
        if self.position != len(self.source):
            self._fail("Unexpected trailing formula source")
        if is_empty(result):
            self._fail("Formula is empty")
        return result

    def _parse_sequence(
        self,
        *,
        terminator: str | None = None,
        stop_commands: frozenset[str] = frozenset(),
        stop_at_environment_boundary: bool = False,
    ) -> Sequence:
        children: list[Node] = []
        while self.position < len(self.source):
            if terminator is not None and self.source[self.position] == terminator:
                self.position += 1
                return Sequence(tuple(children))
            if any(self._at_control_word(command) for command in stop_commands):
                return Sequence(tuple(children))
            if stop_at_environment_boundary and self._at_environment_boundary():
                return Sequence(tuple(children))

            char = self.source[self.position]
            if char == "}":
                self._fail("Unexpected closing group")
            if char == "&":
                self._fail("Alignment marker '&' is only valid inside an environment")
            if char in "^_":
                append_child(children, self._parse_prescript())
                continue
            infix = self._current_infix_command()
            if infix is not None:
                if not children:
                    self._fail(f"Infix fraction \\{infix} has no numerator")
                self._consume_control_word(infix)
                right = self._parse_nested_sequence(
                    terminator=terminator,
                    stop_commands=stop_commands,
                    stop_at_environment_boundary=stop_at_environment_boundary,
                )
                if is_empty(right):
                    self._fail(f"Infix fraction \\{infix} has no denominator")
                left = Sequence(tuple(children))
                fraction = Fraction(
                    numerator=left,
                    denominator=right,
                    kind="bar" if infix == "over" else "noBar",
                )
                if infix in {"choose", "brace", "brack"}:
                    delimiters = {
                        "choose": ("(", ")"),
                        "brace": ("{", "}"),
                        "brack": ("[", "]"),
                    }[infix]
                    return Sequence((Delimiter(*delimiters, (Sequence((fraction,)),)),))
                return Sequence((fraction,))

            atom = self._parse_complete_atom()
            append_child(children, atom)

        if terminator is not None:
            self._fail(f"Unclosed group; expected {terminator!r}")
        return Sequence(tuple(children))

    def _parse_atom(self) -> Node:
        char = self.source[self.position]
        if char.isspace():
            while self.position < len(self.source) and self.source[self.position].isspace():
                self.position += 1
            return self._styled_text(" ") if self.text_mode_depth else Sequence(())
        if char == "{":
            return self._parse_group()
        if char == "\\":
            return self._parse_command()
        if char in "([|":
            return self._parse_or_literal_character_delimiter(char)
        if char == "$":
            if not self.text_mode_depth:
                self._fail("Math delimiters are only allowed around the complete marker source")
            return self._parse_text_embedded_math("$", "$")
        if char in "#%":
            self._fail(f"Unsupported TeX syntax character {char!r}")
        if ord(char) < 32:
            self._fail("Unsupported control character")

        self.position += 1
        if self.text_mode_depth:
            return self._styled_text(char)
        if char == "-":
            char = "−"
        elif char == "~":
            return self._styled_text("\u00a0", _SPACING_STYLE)
        style = _ROMAN_STYLE if char in _PLAIN_OPERATOR_CHARS else None
        return self._styled_text(char, style)

    def _parse_command(self) -> Node:
        command_start = self.position
        self.position += 1
        if self.position >= len(self.source):
            self._fail("Trailing backslash", position=command_start)

        char = self.source[self.position]
        if not _is_command_letter(char):
            self.position += 1
            if char == "\\":
                self._fail(
                    "Row separator '\\\\' is only valid inside an environment",
                    position=command_start,
                )
            if char == "|":
                paired = self._try_symmetric_command_delimiter(command_start)
                if paired is not None:
                    return paired
                return self._styled_text("‖", _ROMAN_STYLE)
            if char == "(" and self.text_mode_depth:
                return self._parse_text_embedded_math("\\(", "\\)", opened=True)
            if char == "{":
                paired = self._try_escaped_brace_delimiter()
                if paired is not None:
                    return paired
            escaped = {
                "{": "{",
                "}": "}",
                "_": "_",
                "%": "%",
                "#": "#",
                "$": "$",
                "&": "&",
            }
            if char in escaped:
                return self._styled_text(
                    escaped[char],
                    literal=char == "&",
                )
            if char in SPACING_COMMANDS:
                return self._styled_text(SPACING_COMMANDS[char], _SPACING_STYLE)
            self._fail(f"Unsupported control symbol \\{char}", position=command_start)

        command = self._read_control_word_body()
        self._skip_whitespace()
        if command in UNSUPPORTED_COMMANDS:
            self._fail(f"Unsupported LaTeX command \\{command}", position=command_start)
        if command in {"vert", "Vert"}:
            paired = self._try_symmetric_named_delimiter(command)
            if paired is not None:
                return paired
        if command in GREEK_SYMBOLS:
            style = None
            if command[:1].isupper() and command not in VARIANT_UPPERCASE_GREEK:
                style = _ROMAN_STYLE
            return self._styled_text(GREEK_SYMBOLS[command], style)
        if command in SYMBOL_COMMANDS:
            return self._styled_text(SYMBOL_COMMANDS[command], _ROMAN_STYLE)
        if command in DELIMITER_COMMANDS:
            paired = self._try_command_delimiter(command, command_start)
            if paired is not None:
                return paired
            return self._styled_text(DELIMITER_COMMANDS[command], _ROMAN_STYLE)
        if command in NARY_COMMANDS:
            symbol, category = NARY_COMMANDS[command]
            return Nary(symbol=symbol, category=category)
        if command in STANDARD_FUNCTIONS:
            return Function(name=self._roman_name(command))
        if command in LIMIT_FUNCTIONS:
            return Function(name=self._roman_name(command), limit_style=True)
        if command == "operatorname":
            name = self._parse_required_argument("operator name", text_mode=True)
            return Function(name=Sequence((Styled(name, _ROMAN_STYLE),)))
        if command in {"frac", "dfrac", "tfrac", "cfrac", "ifrac"}:
            if (
                command == "cfrac"
                and self.position < len(self.source)
                and self.source[self.position] == "["
            ):
                self._parse_raw_optional_group("continued-fraction alignment")
            numerator = self._parse_required_argument("fraction numerator")
            denominator = self._parse_required_argument("fraction denominator")
            return Fraction(
                numerator=numerator,
                denominator=denominator,
                kind="skw" if command == "ifrac" else "bar",
            )
        if command in {"binom", "dbinom", "tbinom"}:
            numerator = self._parse_required_argument("binomial numerator")
            denominator = self._parse_required_argument("binomial denominator")
            fraction = Fraction(numerator, denominator, kind="noBar")
            return Delimiter("(", ")", (Sequence((fraction,)),))
        if command == "genfrac":
            left = self._delimiter_from_raw(self._parse_raw_required_group("left delimiter"))
            right = self._delimiter_from_raw(self._parse_raw_required_group("right delimiter"))
            thickness = self._parse_raw_required_group("fraction thickness").strip()
            self._parse_raw_required_group("fraction style")
            numerator = self._parse_required_argument("fraction numerator")
            denominator = self._parse_required_argument("fraction denominator")
            if not thickness:
                kind = "bar"
            elif thickness == "0":
                kind = "noBar"
            else:
                thickness_match = _LENGTH_RE.fullmatch(thickness)
                if thickness_match is None:
                    self._fail(
                        f"Invalid generalized-fraction thickness {thickness!r}"
                    )
                kind = (
                    "noBar"
                    if float(thickness_match.group(1)) == 0.0
                    else "bar"
                )
            fraction = Fraction(numerator, denominator, kind=kind)
            if left or right:
                return Delimiter(left, right, (Sequence((fraction,)),))
            return fraction
        if command == "sqrt":
            degree = self._parse_optional_argument("radical degree")
            body = self._parse_required_argument("radical body")
            return Radical(body=body, degree=degree)
        if command == "root":
            degree = self._parse_nested_sequence(stop_commands=frozenset({"of"}))
            if not self._at_control_word("of") or is_empty(degree):
                self._fail("\\root requires a degree followed by \\of")
            self._consume_control_word("of")
            body = self._parse_required_argument("radical body")
            return Radical(body=body, degree=degree)
        if command in {"left", _BIG_LEFT_COMMAND}:
            return self._parse_delimited_expression(command)
        if command == _BIG_RIGHT_COMMAND:
            right = self._parse_delimiter_token("explicit big right delimiter")
            return Delimiter("", right, (Sequence(()),))
        if command == _BIG_MIDDLE_COMMAND:
            separator = self._parse_delimiter_token("explicit big middle delimiter")
            return Delimiter("", "", (Sequence(()), Sequence(())), separator)
        if command == _BIG_SYMMETRIC_COMMAND:
            return self._parse_big_symmetric_delimiter()
        if command in {"right", "middle"}:
            self._fail(f"Unexpected \\{command} without matching \\left", position=command_start)
        if command == "begin":
            return self._parse_environment()
        if command == "end":
            self._fail("Unexpected \\end without matching \\begin", position=command_start)
        if command in _STYLE_WRAPPERS:
            text_mode = command in {
                "text", "textrm", "textnormal", "textbf", "textit", "emph",
                "textsf", "texttt", "mbox", "hbox",
            }
            body = self._parse_required_argument(f"\\{command} body", text_mode=text_mode)
            return Styled(body=body, style=_STYLE_WRAPPERS[command])
        if command in _DECLARATION_STYLES:
            self.current_style = merge_run_styles(
                self.current_style,
                _DECLARATION_STYLES[command],
            )
            return Sequence(())
        if command in ACCENT_COMMANDS:
            body = self._parse_required_argument(f"\\{command} body")
            return Accent(character=ACCENT_COMMANDS[command], body=body)
        if command == "overline":
            return Bar("top", self._parse_required_argument("overline body"))
        if command == "underline":
            return Bar("bot", self._parse_required_argument("underline body"))
        if command in _OVER_UNDER_COMMANDS:
            character, position, vertical = _OVER_UNDER_COMMANDS[command]
            body = self._parse_required_argument(f"\\{command} body")
            return GroupChar(character, position, vertical, body)
        if command in _OVER_ARROW_COMMANDS:
            body = self._parse_required_argument(f"\\{command} body")
            return GroupChar(_OVER_ARROW_COMMANDS[command], "top", "bot", body)
        if command in {"xrightarrow", "xleftarrow"}:
            lower = self._parse_optional_argument("arrow lower label", allow_empty=True)
            upper = self._parse_required_argument("arrow upper label", allow_empty=True)
            arrow = GroupChar(
                "→" if command == "xrightarrow" else "←",
                "bot",
                "top",
                upper,
            )
            return Limit(arrow, lower=lower) if lower is not None else arrow
        if command in {"overset", "stackrel"}:
            upper = self._parse_required_argument("upper limit")
            base = self._single_node(self._parse_required_argument("limit base"))
            return Limit(base=base, upper=upper)
        if command == "underset":
            lower = self._parse_required_argument("lower limit")
            base = self._single_node(self._parse_required_argument("limit base"))
            return Limit(base=base, lower=lower)
        if command == "buildrel":
            upper = self._parse_nested_sequence(stop_commands=frozenset({"over"}))
            if not self._at_control_word("over"):
                self._fail("\\buildrel requires \\over")
            if is_empty(upper):
                self._fail("\\buildrel requires an upper value")
            self._consume_control_word("over")
            base = self._single_node(self._parse_required_argument("buildrel base"))
            return Limit(base=base, upper=upper)
        if command == "substack":
            raw = self._parse_raw_required_group("substack body")
            return self._parse_synthetic_environment("aligned", raw)
        if command == "bmod":
            return Function(name=self._roman_name("mod"))
        if command in {"pmod", "mod"}:
            body = self._parse_required_argument(f"\\{command} body")
            content = Sequence((
                Text("mod", _ROMAN_STYLE),
                Text(" ", _SPACING_STYLE),
                *body.children,
            ))
            if command == "pmod":
                return Delimiter("(", ")", (content,))
            return content
        if command in _STYLE_COLOR_COMMANDS:
            color = self._parse_color()
            body = self._parse_required_argument(f"\\{command} body")
            return Styled(body, RunStyle(color=color))
        if command in {"boxed", "fbox", "framebox", "cancel", "bcancel", "xcancel"}:
            body = self._parse_required_argument(
                f"\\{command} body",
                text_mode=command in {"fbox", "framebox"},
            )
            return BorderBox(body=body, kind=command)
        if command in {"phantom", "hphantom", "vphantom"}:
            return Phantom(
                body=self._parse_required_argument(f"\\{command} body"),
                kind=command,
            )
        if command == "not":
            target = self._parse_required_argument("negated relation")
            node = self._single_node(target)
            if isinstance(node, Text) and len(node.value) == 1:
                negated = NEGATED_SYMBOLS.get(node.value)
                if negated is not None:
                    return self._styled_text(negated, _ROMAN_STYLE)
            return Accent("̸", target)
        if command == "eqalign":
            raw = self._parse_raw_required_group("eqalign body")
            return self._parse_synthetic_environment("aligned", raw.replace("\\cr", "\\\\"))
        if command == "ce":
            raw = self._parse_raw_required_group("chemical expression")
            return _ChemParser(raw, display=self.display).parse()
        if command == "bra":
            return Delimiter("⟨", "|", (self._parse_required_argument("bra body"),))
        if command == "ket":
            return Delimiter("|", "⟩", (self._parse_required_argument("ket body"),))
        if command in SPACING_COMMANDS:
            return self._styled_text(SPACING_COMMANDS[command], _SPACING_STYLE)
        if command in {"mkern", "mskip"}:
            return self._styled_text(self._parse_spacing_length(command), _SPACING_STYLE)
        if command == "hspace":
            return self._styled_text(
                _space_from_length(self._parse_raw_required_group("horizontal space")),
                _SPACING_STYLE,
            )
        if command in NO_OUTPUT_COMMANDS:
            return Sequence(())
        if command in DISCARDED_ARGUMENT_COMMANDS:
            self._parse_required_argument(f"\\{command} body", allow_empty=True)
            return Sequence(())
        if command == "mathrel":
            return OperatorEmulator(
                self._parse_required_argument("math relation body")
            )
        if command == "mathop":
            return Function(
                name=self._parse_required_argument("math operator body"),
                limit_style=True,
            )

        self._fail(f"Unsupported LaTeX command \\{command}", position=command_start)

    def _parse_group(self) -> Sequence:
        self.position += 1
        saved_style = self.current_style
        try:
            return self._parse_nested_sequence(terminator="}")
        finally:
            self.current_style = saved_style

    def _parse_required_argument(
        self,
        description: str,
        *,
        allow_empty: bool = False,
        text_mode: bool = False,
    ) -> Sequence:
        self._skip_whitespace()
        saved_text_depth = self.text_mode_depth
        if text_mode:
            self.text_mode_depth += 1
        try:
            if self.position >= len(self.source):
                self._fail(f"{description.capitalize()} is missing")
            if self.source[self.position] == "{":
                result = self._parse_group()
            else:
                result = Sequence((self._parse_nested_bare_atom(),))
        finally:
            self.text_mode_depth = saved_text_depth
        if not allow_empty and is_empty(result):
            self._fail(f"{description.capitalize()} cannot be empty")
        return result

    def _parse_optional_argument(
        self,
        description: str,
        *,
        allow_empty: bool = False,
    ) -> Sequence | None:
        self._skip_whitespace()
        if self.position >= len(self.source) or self.source[self.position] != "[":
            return None
        self.position += 1
        result = self._parse_nested_sequence(terminator="]")
        if not allow_empty and is_empty(result):
            self._fail(f"{description.capitalize()} cannot be empty")
        return result

    def _parse_raw_required_group(self, description: str) -> str:
        try:
            raw, self.position = _read_raw_group(self.source, self.position)
        except FormulaCompileError as exc:
            self._fail(f"{description.capitalize()} must use a braced group")
            raise AssertionError from exc
        return raw

    def _parse_raw_optional_group(self, description: str) -> str | None:
        self._skip_whitespace()
        if self.position >= len(self.source) or self.source[self.position] != "[":
            return None
        closing = self.source.find("]", self.position + 1)
        if closing < 0:
            self._fail(f"Unclosed {description}")
        raw = self.source[self.position + 1:closing]
        self.position = closing + 1
        self._skip_whitespace()
        return raw

    def _parse_nested_sequence(self, **kwargs: object) -> Sequence:
        self.depth += 1
        if self.depth > _MAX_PARSE_DEPTH:
            self._fail(f"Formula nesting exceeds {_MAX_PARSE_DEPTH} levels")
        try:
            return self._parse_sequence(**kwargs)
        finally:
            self.depth -= 1

    def _parse_nested_atom(self) -> Node:
        self.depth += 1
        if self.depth > _MAX_PARSE_DEPTH:
            self._fail(f"Formula nesting exceeds {_MAX_PARSE_DEPTH} levels")
        try:
            return self._parse_complete_atom()
        finally:
            self.depth -= 1

    def _parse_nested_bare_atom(self) -> Node:
        self.depth += 1
        if self.depth > _MAX_PARSE_DEPTH:
            self._fail(f"Formula nesting exceeds {_MAX_PARSE_DEPTH} levels")
        try:
            return self._parse_atom()
        finally:
            self.depth -= 1

    def _parse_complete_atom(self) -> Node:
        atom = self._parse_atom()
        if isinstance(atom, (Nary, Function)):
            atom = self._parse_limit_modifier(atom)
        atom = self._parse_scripts(atom)
        if isinstance(atom, (Nary, Function)):
            atom = self._parse_limit_modifier(atom)
            atom = self._parse_owned_body(atom)
        return atom

    def _parse_scripts(self, base: Node) -> Node:
        subscript: Sequence | None = None
        superscript: Sequence | None = None
        while True:
            saved_position = self.position
            self._skip_whitespace()
            if self.position >= len(self.source) or self.source[self.position] not in "^_":
                self.position = saved_position
                break
            marker = self.source[self.position]
            self.position += 1
            argument = self._parse_required_argument(f"script marker {marker!r}")
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
        if isinstance(base, Nary):
            return Nary(
                base.symbol,
                base.category,
                subscript,
                superscript,
                base.body,
                base.limit_modifier,
            )
        if isinstance(base, Function):
            return Function(
                base.name,
                base.body,
                subscript,
                superscript,
                base.limit_style,
                base.limit_modifier,
            )
        if isinstance(base, GroupChar):
            return Limit(base, lower=subscript, upper=superscript)
        if isinstance(base, Limit):
            return Limit(
                base.base,
                lower=subscript or base.lower,
                upper=superscript or base.upper,
            )
        return Script(base, subscript=subscript, superscript=superscript)

    def _parse_prescript(self) -> Prescript:
        subscript: Sequence | None = None
        superscript: Sequence | None = None
        while self.position < len(self.source) and self.source[self.position] in "^_":
            marker = self.source[self.position]
            self.position += 1
            argument = self._parse_required_argument(f"pre-script marker {marker!r}")
            if marker == "_":
                if subscript is not None:
                    self._fail("Duplicate pre-subscript")
                subscript = argument
            else:
                if superscript is not None:
                    self._fail("Duplicate pre-superscript")
                superscript = argument
            self._skip_whitespace()
        if self.position >= len(self.source):
            self._fail("Pre-script has no base")
        base = self._parse_nested_atom()
        return Prescript(base, subscript=subscript, superscript=superscript)

    def _parse_limit_modifier(self, node: Nary | Function) -> Nary | Function:
        saved = self.position
        self._skip_whitespace()
        command: str | None = None
        if self._at_control_word("limits"):
            command = "limits"
        elif self._at_control_word("nolimits"):
            command = "nolimits"
        if command is None:
            self.position = saved
            return node
        if node.limit_modifier is not None:
            self._fail("Operator has more than one limit modifier")
        self._consume_control_word(command)
        if isinstance(node, Nary):
            return Nary(
                node.symbol,
                node.category,
                node.subscript,
                node.superscript,
                node.body,
                command,
            )
        return Function(
            node.name,
            node.body,
            node.subscript,
            node.superscript,
            node.limit_style,
            command,
        )

    def _parse_owned_body(self, node: Nary | Function) -> Nary | Function:
        if node.body is not None:
            return node
        saved = self.position
        self._skip_whitespace()
        leading_spacing: list[Node] = []
        while self._transparent_prefix_follows():
            append_child(leading_spacing, self._parse_nested_atom())
            self._skip_whitespace()
        if self.position < len(self.source) and self.source[self.position] in "+-":
            append_child(leading_spacing, self._parse_nested_atom())
            self._skip_whitespace()
            while self._transparent_prefix_follows():
                append_child(leading_spacing, self._parse_nested_atom())
                self._skip_whitespace()
        if not self._owned_body_follows():
            self.position = saved
            return node
        if self.source[self.position] == "{":
            body = self._parse_group()
        else:
            body = Sequence((self._parse_nested_atom(),))
        if leading_spacing:
            body = Sequence((*leading_spacing, *body.children))
        if isinstance(node, Nary):
            children = list(body.children)
            while True:
                saved_tail = self.position
                self._skip_whitespace()
                tail_prefix: list[Node] = []
                while self._transparent_prefix_follows():
                    append_child(tail_prefix, self._parse_nested_atom())
                    self._skip_whitespace()
                if not self._owned_body_follows():
                    self.position = saved_tail
                    break
                for prefix_node in tail_prefix:
                    append_child(children, prefix_node)
                append_child(children, self._parse_nested_atom())
            body = Sequence(tuple(children))
        elif isinstance(node, Function):
            children = list(body.children)
            while self._call_delimiter_follows():
                append_child(children, self._parse_nested_atom())
            body = Sequence(tuple(children))
        if isinstance(node, Nary):
            return Nary(
                node.symbol,
                node.category,
                node.subscript,
                node.superscript,
                body,
                node.limit_modifier,
            )
        return Function(
            node.name,
            body,
            node.subscript,
            node.superscript,
            node.limit_style,
            node.limit_modifier,
        )

    def _transparent_prefix_follows(self) -> bool:
        if self.position >= len(self.source):
            return False
        if self.source[self.position] == "~":
            return True
        if self.source[self.position] != "\\" or self.position + 1 >= len(self.source):
            return False
        following = self.source[self.position + 1]
        if not _is_command_letter(following):
            return following in SPACING_COMMANDS
        command, _ = _read_control_word(self.source, self.position)
        return (
            command in SPACING_COMMANDS
            or command in NO_OUTPUT_COMMANDS
            or command in {"mkern", "mskip", "hspace"}
        )

    def _call_delimiter_follows(self) -> bool:
        self._skip_whitespace()
        if self.position >= len(self.source):
            return False
        if self.source[self.position] in "([|":
            return True
        if self.source.startswith((r"\|", r"\{"), self.position):
            return True
        if self.source[self.position] != "\\":
            return False
        if self.position + 1 >= len(self.source) or not _is_command_letter(
            self.source[self.position + 1]
        ):
            return False
        command, _ = _read_control_word(self.source, self.position)
        return command in BARE_DELIMITER_COMMAND_PAIRS

    def _owned_body_follows(self) -> bool:
        if self.position >= len(self.source) or self._at_environment_boundary():
            return False
        if any(
            self._at_control_word(command)
            for command in {"right", "middle", "end"}
        ):
            return False
        char = self.source[self.position]
        if char in "}])&^_+-=<>/,;:!?":
            return False
        if char != "\\":
            return True
        if (
            self.position + 1 < len(self.source)
            and not _is_command_letter(self.source[self.position + 1])
        ):
            return self.source[self.position + 1] not in {"\\", ",", ";", ":", "!", " "}
        command, _ = _read_control_word(self.source, self.position)
        return command not in OPERATOR_BOUNDARY_COMMANDS

    def _parse_delimited_expression(self, command: str = "left") -> Delimiter:
        left = self._parse_delimiter_token(f"\\{command}")
        segments: list[Sequence] = []
        separator = ""
        stop_commands = frozenset({
            *_MIDDLE_DELIMITER_COMMANDS,
            *_RIGHT_DELIMITER_COMMANDS,
        })
        while True:
            segments.append(
                self._parse_nested_sequence(stop_commands=stop_commands)
            )
            middle_command = next(
                (
                    candidate
                    for candidate in _MIDDLE_DELIMITER_COMMANDS
                    if self._at_control_word(candidate)
                ),
                None,
            )
            if middle_command is not None:
                self._consume_control_word(middle_command)
                current = self._parse_delimiter_token(f"\\{middle_command}")
                if separator and separator != current:
                    self._fail("One delimiter expression cannot mix middle characters")
                separator = current
                continue
            right = ""
            right_command = next(
                (
                    candidate
                    for candidate in _RIGHT_DELIMITER_COMMANDS
                    if self._at_control_word(candidate)
                ),
                None,
            )
            if right_command is not None:
                self._consume_control_word(right_command)
                right = self._parse_delimiter_token(f"\\{right_command}")
            return Delimiter(left, right, tuple(segments), separator)

    def _parse_big_symmetric_delimiter(self) -> Delimiter:
        delimiter = self._parse_delimiter_token("explicit big symmetric delimiter")
        body_start = self.position
        closing = self._find_matching_big_symmetric(delimiter, body_start)
        if closing is None:
            return Delimiter("", "", (Sequence(()), Sequence(())), delimiter)
        closing_start, after_closing = closing
        body = self._parse_fragment(self.source[body_start:closing_start])
        self.position = after_closing
        return Delimiter(delimiter, delimiter, (body,))

    def _find_matching_big_symmetric(
        self,
        delimiter: str,
        start: int,
    ) -> tuple[int, int] | None:
        group_depth = 0
        cursor = start
        while cursor < len(self.source):
            char = self.source[cursor]
            if char == "{":
                group_depth += 1
                cursor += 1
                continue
            if char == "}":
                group_depth = max(0, group_depth - 1)
                cursor += 1
                continue
            if char != "\\" or cursor + 1 >= len(self.source):
                cursor += 1
                continue
            if not _is_command_letter(self.source[cursor + 1]):
                cursor += 2
                continue
            command, after_command = _read_control_word(self.source, cursor)
            if group_depth != 0 or command != _BIG_SYMMETRIC_COMMAND:
                cursor = after_command
                continue
            saved_position = self.position
            try:
                self.position = _skip_whitespace(self.source, after_command)
                candidate = self._parse_delimiter_token(
                    "explicit big symmetric delimiter"
                )
                after_delimiter = self.position
            finally:
                self.position = saved_position
            if candidate == delimiter:
                return cursor, after_delimiter
            cursor = after_delimiter
        return None

    def _parse_delimiter_token(self, owner: str) -> str:
        self._skip_whitespace()
        if self.position >= len(self.source):
            self._fail(f"{owner} requires a delimiter")
        char = self.source[self.position]
        if char != "\\":
            self.position += 1
            if char in "()[]|.⟦⟧":
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
        if command not in DELIMITER_COMMANDS:
            self._fail(f"Unsupported delimiter command \\{command}", position=command_start)
        return DELIMITER_COMMANDS[command]

    def _parse_or_literal_character_delimiter(self, opener: str) -> Node:
        closer = {"(": ")", "[": "]", "|": "|"}[opener]
        start = self.position
        if opener == closer:
            closing = self._find_symmetric_character(start, opener)
        else:
            closing = self._find_matching_character(start, opener, closer)
        if closing is None:
            self.position += 1
            return self._styled_text(opener, _ROMAN_STYLE)
        body_source = self.source[start + 1:closing]
        body = self._parse_fragment(body_source)
        self.position = closing + 1
        return Delimiter(opener, closer, (body,))

    def _find_symmetric_character(self, start: int, delimiter: str) -> int | None:
        group_depth = 0
        cursor = start + 1
        while cursor < len(self.source):
            char = self.source[cursor]
            if char == "\\":
                cursor += 2
                continue
            if char == "{":
                group_depth += 1
            elif char == "}" and group_depth:
                group_depth -= 1
            elif char == delimiter and group_depth == 0:
                return cursor
            cursor += 1
        return None

    def _try_escaped_brace_delimiter(self) -> Node | None:
        closing = self._find_matching_control_symbol("{", "}", self.position)
        if closing is None:
            return None
        body = self._parse_fragment(self.source[self.position:closing])
        self.position = closing + 2
        return Delimiter("{", "}", (body,))

    def _try_command_delimiter(self, command: str, command_start: int) -> Node | None:
        pair = BARE_DELIMITER_COMMAND_PAIRS.get(command)
        if pair is None:
            return None
        closing_command, left, right = pair
        closing = self._find_matching_control_word(command, closing_command, self.position)
        if closing is None:
            return None
        body = self._parse_fragment(self.source[self.position:closing])
        _, after = _read_control_word(self.source, closing)
        self.position = _skip_whitespace(self.source, after)
        return Delimiter(left, right, (body,))

    def _try_symmetric_command_delimiter(self, command_start: int) -> Node | None:
        closing = self.source.find("\\|", self.position)
        if closing < 0:
            return None
        body = self._parse_fragment(self.source[self.position:closing])
        self.position = closing + 2
        return Delimiter("‖", "‖", (body,))

    def _try_symmetric_named_delimiter(self, command: str) -> Node | None:
        closing = self._find_symmetric_control_word(command, self.position)
        if closing is None:
            return None
        body = self._parse_fragment(self.source[self.position:closing])
        _, after = _read_control_word(self.source, closing)
        self.position = _skip_whitespace(self.source, after)
        delimiter = "‖" if command == "Vert" else "|"
        return Delimiter(delimiter, delimiter, (body,))

    def _find_matching_character(self, start: int, opener: str, closer: str) -> int | None:
        expected_closers = [closer]
        group_depth = 0
        cursor = start + 1
        explicit_delimiter_commands = {
            "left",
            "right",
            "middle",
            _BIG_LEFT_COMMAND,
            _BIG_RIGHT_COMMAND,
            _BIG_MIDDLE_COMMAND,
            _BIG_SYMMETRIC_COMMAND,
        }
        while cursor < len(self.source):
            char = self.source[cursor]
            if char == "\\":
                if cursor + 1 >= len(self.source):
                    return None
                if not _is_command_letter(self.source[cursor + 1]):
                    cursor += 2
                    continue
                command, cursor = _read_control_word(self.source, cursor)
                if group_depth == 0 and command in explicit_delimiter_commands:
                    cursor = self._skip_scanned_delimiter_token(cursor)
                continue
            if char == "{":
                group_depth += 1
                cursor += 1
                continue
            if char == "}":
                if group_depth == 0:
                    return None
                group_depth -= 1
                cursor += 1
                continue
            if group_depth == 0:
                if char in "([":
                    expected_closers.append(")" if char == "(" else "]")
                elif char in ")]":
                    if char != expected_closers[-1]:
                        return None
                    expected_closers.pop()
                    if not expected_closers:
                        return cursor
            cursor += 1
        return None

    def _skip_scanned_delimiter_token(self, position: int) -> int:
        position = _skip_whitespace(self.source, position)
        if position >= len(self.source):
            return position
        if self.source[position] != "\\":
            return position + 1
        if position + 1 >= len(self.source):
            return len(self.source)
        if not _is_command_letter(self.source[position + 1]):
            return position + 2
        _, position = _read_control_word(self.source, position)
        return position

    def _find_matching_control_symbol(
        self,
        opener: str,
        closer: str,
        start: int,
    ) -> int | None:
        depth = 1
        cursor = start
        while cursor + 1 < len(self.source):
            if self.source[cursor] != "\\":
                cursor += 1
                continue
            symbol = self.source[cursor + 1]
            if symbol == opener:
                depth += 1
            elif symbol == closer:
                depth -= 1
                if depth == 0:
                    return cursor
            cursor += 2
        return None

    def _find_matching_control_word(
        self,
        opener: str,
        closer: str,
        start: int,
    ) -> int | None:
        depth = 1
        cursor = start
        while cursor < len(self.source):
            if self.source[cursor] != "\\" or cursor + 1 >= len(self.source):
                cursor += 1
                continue
            if not _is_command_letter(self.source[cursor + 1]):
                cursor += 2
                continue
            command, end = _read_control_word(self.source, cursor)
            if command == opener:
                depth += 1
            elif command == closer:
                depth -= 1
                if depth == 0:
                    return cursor
            cursor = end
        return None

    def _find_symmetric_control_word(
        self,
        command: str,
        start: int,
    ) -> int | None:
        group_depth = 0
        cursor = start
        while cursor < len(self.source):
            char = self.source[cursor]
            if char == "{":
                group_depth += 1
                cursor += 1
                continue
            if char == "}":
                group_depth = max(0, group_depth - 1)
                cursor += 1
                continue
            if char != "\\" or cursor + 1 >= len(self.source):
                cursor += 1
                continue
            if not _is_command_letter(self.source[cursor + 1]):
                cursor += 2
                continue
            current, end = _read_control_word(self.source, cursor)
            if group_depth == 0 and current == command:
                return cursor
            cursor = end
        return None

    def _parse_environment(self) -> Node:
        environment = self._parse_environment_name("\\begin")
        if (
            environment not in MATRIX_ENVIRONMENTS
            and environment not in EQUATION_ARRAY_ENVIRONMENTS
        ):
            self._fail(f"Unsupported formula environment {environment!r}")

        if environment == "CD":
            return self._parse_cd_environment()

        column_alignments: tuple[str, ...] = ()
        if environment in {"array", "subarray"}:
            raw = self._parse_raw_required_group(f"{environment} column specification")
            filtered = tuple(char for char in raw if char in "lcr")
            if not filtered:
                self._fail(f"Environment {environment!r} requires l/c/r columns")
            column_alignments = tuple("center" for _ in filtered)
        elif environment in {"alignat", "alignat*", "alignedat"}:
            raw = self._parse_raw_required_group(f"{environment} column count").strip()
            if not raw.isdigit() or int(raw) <= 0:
                self._fail(f"Environment {environment!r} requires a positive column count")

        self.environment_stack.append(environment)
        try:
            rows = self._parse_environment_rows(environment)
        finally:
            self.environment_stack.pop()

        if environment in MATRIX_ENVIRONMENTS:
            if not column_alignments and rows:
                column_alignments = tuple("center" for _ in rows[0])
            matrix = Matrix(environment, rows, column_alignments)
            delimiters = MATRIX_ENVIRONMENTS[environment]
            if delimiters is not None:
                return Delimiter(delimiters[0], delimiters[1], (Sequence((matrix,)),))
            return matrix

        eq_rows: list[Sequence] = []
        for row in rows:
            children: list[Node] = []
            for index, cell in enumerate(row):
                if index:
                    children.append(AlignmentPoint())
                children.extend(cell.children)
            eq_rows.append(Sequence(tuple(children)))
        equation_array = EquationArray(tuple(eq_rows))
        if environment == "cases":
            return Delimiter("{", "", (Sequence((equation_array,)),))
        if environment == "rcases":
            return Delimiter("", "}", (Sequence((equation_array,)),))
        return equation_array

    def _parse_cd_environment(self) -> Matrix:
        ending = r"\end{CD}"
        closing = self.source.find(ending, self.position)
        if closing < 0:
            self._fail("Unclosed formula environment 'CD'")
        raw = self.source[self.position:closing]
        self.position = closing + len(ending)
        raw_rows = re.split(r"\\\\|\\cr(?![A-Za-z])", raw)
        if raw_rows and not raw_rows[-1].strip():
            raw_rows.pop()
        rows: list[tuple[Sequence, ...]] = []
        for raw_row in raw_rows:
            row = raw_row.strip()
            if not row:
                self._fail("Environment 'CD' cannot contain an empty row")
            horizontal_parts = re.split(r"@(>>>|<<<)", row)
            if len(horizontal_parts) > 1:
                cells: list[Sequence] = []
                for index, part in enumerate(horizontal_parts):
                    if index % 2:
                        cells.append(Sequence((Text(
                            "→" if part == ">>>" else "←",
                            _ROMAN_STYLE,
                        ),)))
                    else:
                        if "@" in part:
                            self._fail(
                                "Environment 'CD' supports only @>>>, @<<<, @VVV, and @AAA"
                            )
                        cells.append(self._parse_fragment(part.strip()))
                rows.append(tuple(cells))
                continue
            vertical_tokens = re.findall(r"@(VVV|AAA)", row)
            vertical_remainder = re.sub(r"@(VVV|AAA)|[&\s]", "", row)
            if vertical_tokens and not vertical_remainder:
                cells: list[Sequence] = []
                for index, token in enumerate(vertical_tokens):
                    if index:
                        cells.append(Sequence(()))
                    cells.append(Sequence((Text(
                        "↓" if token == "VVV" else "↑",
                        _ROMAN_STYLE,
                    ),)))
                rows.append(tuple(cells))
                continue
            if "@" in row:
                self._fail("Environment 'CD' supports only @>>>, @<<<, @VVV, and @AAA")
            rows.append(tuple(self._parse_fragment(cell.strip()) for cell in row.split("&")))
        if not rows:
            self._fail("Environment 'CD' cannot be empty")
        column_count = max(len(row) for row in rows)
        padded_rows = tuple(
            (*row, *(Sequence(()) for _ in range(column_count - len(row))))
            for row in rows
        )
        return Matrix(
            "CD",
            padded_rows,
            tuple("center" for _ in range(column_count)),
        )

    def _parse_environment_rows(
        self,
        environment: str,
    ) -> tuple[tuple[Sequence, ...], ...]:
        rows: list[tuple[Sequence, ...]] = []
        row: list[Sequence] = []
        while True:
            cell = self._parse_nested_sequence(stop_at_environment_boundary=True)
            row.append(cell)
            if self.position < len(self.source) and self.source[self.position] == "&":
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
            if self._at_control_word("cr"):
                self._consume_control_word("cr")
                rows.append(tuple(row))
                row = []
                if self._at_control_word("end"):
                    self._consume_environment_end(environment)
                    break
                continue
            if self._at_control_word("end"):
                rows.append(tuple(row))
                self._consume_environment_end(environment)
                break
            self._fail(f"Malformed environment {environment!r}")
        if not rows or not rows[0]:
            self._fail(f"Environment {environment!r} cannot be empty")
        if environment in MATRIX_ENVIRONMENTS:
            column_count = len(rows[0])
            if any(len(current) != column_count for current in rows):
                self._fail(f"Environment {environment!r} has inconsistent column counts")
        return tuple(rows)

    def _parse_synthetic_environment(self, environment: str, raw: str) -> Node:
        parser = _LatexParser(
            f"\\begin{{{environment}}}{raw}\\end{{{environment}}}",
            display=self.display,
            inherited_style=self.current_style,
        )
        result = parser.parse()
        return self._single_node(result)

    def _consume_environment_end(self, expected: str) -> None:
        self._consume_control_word("end")
        actual = self._parse_environment_name("\\end")
        if actual != expected:
            self._fail(
                f"Mismatched environment ending: expected {expected!r}, got {actual!r}"
            )

    def _parse_environment_name(self, owner: str) -> str:
        raw = self._parse_raw_required_group(f"{owner} environment name")
        if _ENVIRONMENT_NAME_RE.fullmatch(raw) is None:
            self._fail(f"Invalid environment name {raw!r}")
        return raw

    def _at_environment_boundary(self) -> bool:
        return (
            (self.position < len(self.source) and self.source[self.position] == "&")
            or self.source.startswith("\\\\", self.position)
            or self._at_control_word("cr")
            or self._at_control_word("end")
        )

    def _parse_text_embedded_math(
        self,
        opener: str,
        closer: str,
        *,
        opened: bool = False,
    ) -> Sequence:
        start = self.position if opened else self.position + len(opener)
        if not opened:
            self.position += len(opener)
        closing = self.source.find(closer, self.position)
        if closing < 0:
            self._fail(f"Unclosed embedded math delimiter {opener!r}", position=start)
        raw = self.source[self.position:closing]
        self.position = closing + len(closer)
        embedded = _LatexParser(
            raw,
            display=False,
            inherited_style=self.current_style,
        ).parse()
        return Sequence((Styled(embedded, _MATH_MODE_RESET_STYLE),))

    def _parse_fragment(self, raw: str) -> Sequence:
        if not raw:
            return Sequence(())
        return _LatexParser(
            raw,
            display=self.display,
            text_mode=bool(self.text_mode_depth),
            inherited_style=self.current_style,
        ).parse()

    def _parse_spacing_length(self, command: str) -> str:
        self._skip_whitespace()
        match = _LENGTH_RE.match(self.source, self.position)
        if match is None:
            self._fail(f"\\{command} requires a numeric length with mu/em/ex/pt")
        self.position = match.end()
        self._skip_whitespace()
        return _space_from_length(match.group(0))

    def _parse_color(self) -> str:
        raw = self._parse_raw_required_group("formula color").strip()
        if _COLOR_HEX_RE.fullmatch(raw):
            return raw[1:].upper()
        color = COLOR_NAMES.get(raw.lower())
        if color is None:
            self._fail(f"Unsupported formula color {raw!r}")
        return color

    def _delimiter_from_raw(self, raw: str) -> str:
        raw = raw.strip()
        if raw in {"", "."}:
            return ""
        if raw in "()[]|{}⟨⟩⌊⌋⌈⌉⟦⟧":
            return raw
        control_symbols = {r"\{": "{", r"\}": "}", r"\|": "‖"}
        if raw in control_symbols:
            return control_symbols[raw]
        if raw.startswith("\\"):
            command = raw[1:]
            if command in DELIMITER_COMMANDS:
                return DELIMITER_COMMANDS[command]
        self._fail(f"Unsupported generalized-fraction delimiter {raw!r}")

    def _roman_name(self, name: str) -> Sequence:
        return Sequence((Text(name, _ROMAN_STYLE),))

    def _single_node(self, sequence: Sequence) -> Node:
        if len(sequence.children) == 1:
            return sequence.children[0]
        return sequence

    def _styled_text(
        self,
        value: str,
        style: RunStyle | None = None,
        *,
        literal: bool = False,
    ) -> Text:
        return Text(
            value,
            merge_run_styles(self.current_style, style),
            literal=literal,
        )

    def _current_infix_command(self) -> str | None:
        for command in _INFIX_FRACTIONS:
            if self._at_control_word(command):
                return command
        return None

    def _at_control_word(self, expected: str) -> bool:
        prefix = f"\\{expected}"
        if not self.source.startswith(prefix, self.position):
            return False
        following = self.position + len(prefix)
        return following >= len(self.source) or not _is_command_letter(self.source[following])

    def _consume_control_word(self, expected: str) -> None:
        if not self._at_control_word(expected):
            self._fail(f"Expected \\{expected}")
        self.position += len(expected) + 1
        self._skip_whitespace()

    def _read_control_word_body(self) -> str:
        start = self.position
        while self.position < len(self.source) and _is_command_letter(self.source[self.position]):
            self.position += 1
        return self.source[start:self.position]

    def _skip_whitespace(self) -> None:
        self.position = _skip_whitespace(self.source, self.position)

    def _fail(self, message: str, *, position: int | None = None) -> None:
        offset = self.position if position is None else position
        start = max(0, offset - 16)
        end = min(len(self.source), offset + 16)
        context = self.source[start:end].replace("\n", " ")
        raise FormulaCompileError(f"{message} at offset {offset}: {context!r}")


_STYLE_COLOR_COMMANDS = frozenset({"color", "textcolor"})


class _ChemParser:
    """Parse the documented Microsoft 365 mhchem subset into shared AST nodes."""

    _ARROWS = {
        "<-->": "⟷",
        "<=>": "⇌",
        "<->": "↔",
        "->": "→",
        "<-": "←",
    }
    _UNSUPPORTED_AT_LABEL_RE = re.compile(r"@[<>=-]+\{")

    def __init__(self, source: str, *, display: bool) -> None:
        self.source = source
        self.position = 0
        self.display = display

    def parse(self) -> Sequence:
        children: list[Node] = []
        while self.position < len(self.source):
            if self._UNSUPPORTED_AT_LABEL_RE.match(self.source, self.position):
                raise FormulaCompileError(
                    "mhchem @{} arrow labels are unsupported; use [above][below]"
                )
            self._reject_unsupported_arrow()
            arrow = self._match_arrow()
            if arrow is not None:
                append_child(children, arrow)
                continue
            char = self.source[self.position]
            if char.isspace():
                while self.position < len(self.source) and self.source[self.position].isspace():
                    self.position += 1
                append_child(children, Text(" ", _TEXT_STYLE))
                continue
            if char == "\\":
                parser = _LatexParser(self.source[self.position:], display=self.display)
                node = parser._parse_complete_atom()
                self.position += parser.position
                append_child(children, node)
                continue
            if char == "{":
                raw, self.position = _read_raw_group(self.source, self.position)
                if raw in {"(", ")", "[", "]"}:
                    append_child(children, Text(raw, _ROMAN_STYLE))
                    continue
                body = _ChemParser(raw, display=self.display).parse()
                append_child(children, body)
                continue
            if char in "([":
                append_child(children, self._parse_grouped_formula(char))
                continue
            if char.isupper():
                append_child(children, self._parse_element())
                continue
            if char.isdigit():
                append_child(children, self._parse_number(children))
                continue
            if char == "^" and self._standalone_marker():
                self.position += 1
                append_child(children, Text("↑", _ROMAN_STYLE))
                continue
            if char in "^_":
                if self._has_right_script_base(children):
                    base = children.pop()
                    append_child(children, self._parse_explicit_scripts(base))
                else:
                    append_child(children, self._parse_isotope())
                continue
            if char in "+-":
                if self._is_bond_dash():
                    self.position += 1
                    append_child(children, Text("‒", _ROMAN_STYLE))
                elif (
                    children
                    and self.position > 0
                    and not self.source[self.position - 1].isspace()
                ):
                    self._attach_charge(children)
                else:
                    self.position += 1
                    append_child(children, Text("+" if char == "+" else "−", _ROMAN_STYLE))
                continue
            if char == "*":
                self.position += 1
                append_child(children, Text("·", _ROMAN_STYLE))
                continue
            if char == "=":
                self.position += 1
                append_child(children, Text("=", _ROMAN_STYLE))
                continue
            if char == "v" and self._standalone_marker():
                self.position += 1
                append_child(children, Text("↓", _ROMAN_STYLE))
                continue
            if char.islower():
                start = self.position
                while self.position < len(self.source) and self.source[self.position].islower():
                    self.position += 1
                word = self.source[start:self.position]
                following = self.position
                while following < len(self.source) and self.source[following].isspace():
                    following += 1
                is_variable = (
                    len(word) == 1
                    and following < len(self.source)
                    and self.source[following].isupper()
                )
                style = None if is_variable else _ROMAN_STYLE
                append_child(children, Text(word, style))
                continue
            self.position += 1
            append_child(children, Text("−" if char == "-" else char, _ROMAN_STYLE))
        return Sequence(tuple(children))

    def _parse_element(self) -> Node:
        start = self.position
        self.position += 1
        while self.position < len(self.source) and self.source[self.position].islower():
            self.position += 1
        base: Node = Text(self.source[start:self.position], _ROMAN_STYLE)
        if self.position < len(self.source) and self.source[self.position].isdigit():
            digits = self._read_digits()
            base = Script(base, subscript=Sequence((Text(digits, _ROMAN_STYLE),)))
        if self.position < len(self.source) and self.source[self.position] in "^_":
            base = self._parse_explicit_scripts(base)
        if (
            self.position < len(self.source)
            and self.source[self.position] in "+-"
            and not self._is_bond_dash()
        ):
            charge = self._read_charge()
            base = self._merge_script(
                base,
                superscript=Sequence((Text(charge, _ROMAN_STYLE),)),
            )
        return base

    def _parse_number(self, children: list[Node]) -> Node:
        start = self.position
        numerator = self._read_digits()
        number: Node = Text(numerator, _ROMAN_STYLE)
        if self.position < len(self.source) and self.source[self.position] == "/":
            saved = self.position
            self.position += 1
            if self.position < len(self.source) and self.source[self.position].isdigit():
                denominator = self._read_digits()
                number = Fraction(
                    Sequence((Text(numerator, _ROMAN_STYLE),)),
                    Sequence((Text(denominator, _ROMAN_STYLE),)),
                )
            else:
                self.position = saved
        if self._is_coefficient_position(start):
            following = self.position
            while following < len(self.source) and self.source[following].isspace():
                following += 1
            if following < len(self.source) and self.source[following].isupper():
                self.position = following
                return Sequence((number, Text("\u2009", _SPACING_STYLE)))
        return number

    def _parse_grouped_formula(self, opener: str) -> Node:
        closer = ")" if opener == "(" else "]"
        start = self.position + 1
        depth = 1
        cursor = start
        while cursor < len(self.source):
            if self.source[cursor] == opener:
                depth += 1
            elif self.source[cursor] == closer:
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        if cursor >= len(self.source):
            raise FormulaCompileError(f"Unclosed chemical delimiter {opener!r}")
        body = _ChemParser(self.source[start:cursor], display=self.display).parse()
        self.position = cursor + 1
        base: Node = Sequence((
            Text(opener, _ROMAN_STYLE),
            *body.children,
            Text(closer, _ROMAN_STYLE),
        ))
        if self.position < len(self.source) and self.source[self.position].isdigit():
            digits = self._read_digits()
            if self.position < len(self.source) and self.source[self.position] in "+-":
                charge = digits + self._read_charge()
                base = Script(
                    base,
                    superscript=Sequence((Text(charge, _ROMAN_STYLE),)),
                )
            else:
                base = Script(base, subscript=Sequence((Text(digits, _ROMAN_STYLE),)))
        if self.position < len(self.source) and self.source[self.position] in "+-":
            charge = self._read_charge()
            base = self._merge_script(
                base,
                superscript=Sequence((Text(charge, _ROMAN_STYLE),)),
            )
        return base

    def _parse_isotope(self) -> Prescript:
        subscript: Sequence | None = None
        superscript: Sequence | None = None
        while self.position < len(self.source) and self.source[self.position] in "^_":
            marker = self.source[self.position]
            self.position += 1
            raw = self._read_chem_script()
            value = self._chem_script_sequence(raw)
            if marker == "_":
                subscript = value
            else:
                superscript = value
        if self.position >= len(self.source) or not self.source[self.position].isupper():
            raise FormulaCompileError("Chemical pre-script requires an element base")
        base = self._parse_element()
        return Prescript(base, subscript=subscript, superscript=superscript)

    def _parse_explicit_scripts(self, base: Node) -> Script:
        subscript: Sequence | None = None
        superscript: Sequence | None = None
        while self.position < len(self.source) and self.source[self.position] in "^_":
            marker = self.source[self.position]
            self.position += 1
            raw = self._read_chem_script()
            if (
                marker == "^"
                and self.position < len(self.source)
                and self.source[self.position] in "+-"
            ):
                raw += self._read_charge()
            value = self._chem_script_sequence(raw)
            if marker == "_":
                subscript = value
            else:
                superscript = value
        return self._merge_script(
            base,
            subscript=subscript,
            superscript=superscript,
        )

    def _read_chem_script(self) -> str:
        if self.position >= len(self.source):
            raise FormulaCompileError("Chemical script is missing an argument")
        if self.source[self.position] == "{":
            raw, self.position = _read_raw_group(self.source, self.position)
            return raw
        char = self.source[self.position]
        self.position += 1
        return char

    def _attach_charge(self, children: list[Node]) -> None:
        charge = self._read_charge()
        base = children.pop()
        children.append(self._merge_script(
            base,
            superscript=Sequence((Text(charge, _ROMAN_STYLE),)),
        ))

    def _merge_script(
        self,
        base: Node,
        *,
        subscript: Sequence | None = None,
        superscript: Sequence | None = None,
    ) -> Script:
        if isinstance(base, Script):
            return Script(
                base.base,
                subscript or base.subscript,
                superscript or base.superscript,
            )
        return Script(base, subscript=subscript, superscript=superscript)

    def _chem_script_sequence(self, raw: str) -> Sequence:
        if "\\" in raw:
            return _LatexParser(raw, display=self.display).parse()
        normalized = raw.replace("-", "−")
        style = None if len(normalized) == 1 and normalized.islower() else _ROMAN_STYLE
        return Sequence((Text(normalized, style),))

    def _has_right_script_base(self, children: list[Node]) -> bool:
        if not children or self.position == 0:
            return False
        previous = self.source[self.position - 1]
        if previous.isspace() or previous in "+-=<>*/([{,;:":
            return False
        return not isinstance(children[-1], Limit)

    def _is_coefficient_position(self, start: int) -> bool:
        cursor = start - 1
        while cursor >= 0 and self.source[cursor].isspace():
            cursor -= 1
        return cursor < 0 or self.source[cursor] in "+<>=-"

    def _is_bond_dash(self) -> bool:
        return (
            self.position < len(self.source)
            and self.source[self.position] == "-"
            and self.position + 1 < len(self.source)
            and self.source[self.position + 1].isupper()
        )

    def _read_charge(self) -> str:
        start = self.position
        while self.position < len(self.source) and self.source[self.position] in "+-":
            self.position += 1
        return self.source[start:self.position].replace("-", "−")

    def _read_digits(self) -> str:
        start = self.position
        while self.position < len(self.source) and self.source[self.position].isdigit():
            self.position += 1
        return self.source[start:self.position]

    def _match_arrow(self) -> Node | None:
        for token, symbol in self._ARROWS.items():
            if not self.source.startswith(token, self.position):
                continue
            self.position += len(token)
            upper = self._read_arrow_label()
            lower = self._read_arrow_label()
            return Limit(Text(symbol, _ROMAN_STYLE), lower=lower, upper=upper)
        return None

    def _reject_unsupported_arrow(self) -> None:
        for token in ("<<=>>", "<=>>", "<<=>", "->>"):
            if self.source.startswith(token, self.position):
                raise FormulaCompileError(
                    f"Unsupported chemical reaction arrow {token!r}"
                )

    def _read_arrow_label(self) -> Sequence | None:
        if self.position >= len(self.source) or self.source[self.position] != "[":
            return None
        start = self.position + 1
        depth = 1
        brace_depth = 0
        cursor = start
        while cursor < len(self.source):
            char = self.source[cursor]
            if char == "\\":
                cursor += 2
                continue
            if char == "{":
                brace_depth += 1
            elif char == "}" and brace_depth:
                brace_depth -= 1
            elif brace_depth == 0 and char == "[":
                depth += 1
            elif brace_depth == 0 and char == "]":
                depth -= 1
                if depth == 0:
                    raw = self.source[start:cursor]
                    self.position = cursor + 1
                    return _ChemParser(raw, display=self.display).parse()
            cursor += 1
        raise FormulaCompileError("Unclosed chemical arrow label")

    def _standalone_marker(self) -> bool:
        before = self.position == 0 or self.source[self.position - 1].isspace()
        after_index = self.position + 1
        after = after_index >= len(self.source) or self.source[after_index].isspace()
        return before and after


def parse_latex_formula(latex: str, *, display: bool) -> Sequence:
    """Validate, normalize, and parse one Microsoft 365 LaTeX expression."""
    if not isinstance(latex, str):
        raise FormulaCompileError("LaTeX formula must be a string")
    source = latex.strip()
    if not source:
        raise FormulaCompileError("LaTeX formula is empty")
    if any(not _xml_character_allowed(char) for char in source):
        raise FormulaCompileError("LaTeX formula contains an invalid XML character")
    prepared = _prepare_source(source)
    if not prepared:
        raise FormulaCompileError("LaTeX formula is empty after preprocessing")
    return _LatexParser(prepared, display=display).parse()


__all__ = ["FormulaCompileError", "parse_latex_formula"]
