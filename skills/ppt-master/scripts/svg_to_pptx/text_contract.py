#!/usr/bin/env python3
"""
PPT Master - SVG Text Layout Contract

Parse and validate explicit SVG paragraph/line semantics before any tspan
normalization mutates the author source tree.

Usage:
    Import ``validate_text_contracts`` from the SVG quality/export pipeline.

Examples:
    contracts = validate_text_contracts(svg_root, merge_paragraphs=True)

Dependencies:
    None (only uses the Python standard library)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
XML_SPACE_ATTR = "{http://www.w3.org/XML/1998/namespace}space"

TEXT_MODE_ATTR = "data-pptx-text-mode"
TEXT_BOUNDS_ATTR = "data-pptx-text-bounds"
TEXT_BREAK_ATTR = "data-pptx-break"
TEXT_JOIN_ATTR = "data-pptx-join"

RUNTIME_CONTRACT_ATTR = "data-pptx-runtime-text-contract"
RUNTIME_SOURCE_ID_ATTR = "data-pptx-runtime-source-text-id"
RUNTIME_REQUESTED_MODE_ATTR = "data-pptx-runtime-requested-mode"
RUNTIME_EFFECTIVE_MODE_ATTR = "data-pptx-runtime-effective-mode"
RUNTIME_LINE_INDEX_ATTR = "data-pptx-runtime-line-index"
RUNTIME_LINE_COUNT_ATTR = "data-pptx-runtime-line-count"
RUNTIME_MODE_REASON_ATTR = "data-pptx-runtime-mode-reason"
RUNTIME_ATTRS = frozenset(
    {
        RUNTIME_CONTRACT_ATTR,
        RUNTIME_SOURCE_ID_ATTR,
        RUNTIME_REQUESTED_MODE_ATTR,
        RUNTIME_EFFECTIVE_MODE_ATTR,
        RUNTIME_LINE_INDEX_ATTR,
        RUNTIME_LINE_COUNT_ATTR,
        RUNTIME_MODE_REASON_ATTR,
    }
)

TEXT_MODES = frozenset({"auto", "paragraph", "lines"})
BREAK_KINDS = frozenset({"soft", "line", "paragraph"})
JOIN_KINDS = frozenset({"space", "none"})

DY_TOLERANCE_PX = 0.5
MAX_DY_MULTIPLIER = 3.0

_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_COORDINATE_RE = re.compile(rf"^({_NUMBER})(?:px)?$")
_FOUR_NUMBERS_RE = re.compile(
    rf"^\s*({_NUMBER})(?:\s*,\s*|\s+)"
    rf"({_NUMBER})(?:\s*,\s*|\s+)"
    rf"({_NUMBER})(?:\s*,\s*|\s+)"
    rf"({_NUMBER})\s*$"
)
_TRANSLATE_RE = re.compile(
    rf"translate\(\s*({_NUMBER})(?:(?:\s*,\s*|\s+)({_NUMBER}))?\s*\)"
)


@dataclass
class TextContractDiagnostic:
    """Describe one stable, actionable text-contract violation."""

    code: str
    message: str
    source_name: str | None = None
    element_id: str | None = None
    element_tag: str = "text"
    attribute: str | None = None
    hint: str | None = None

    def format(self) -> str:
        """Format the diagnostic for checker/exporter user-facing output."""
        location = f"<{self.element_tag}>"
        if self.element_id:
            location = f"<{self.element_tag} id={self.element_id!r}>"
        if self.source_name:
            location = f"{self.source_name} {location}"
        attribute = f" {self.attribute}:" if self.attribute else ":"
        rendered = f"[{self.code}] {location}{attribute} {self.message}"
        if self.hint:
            rendered += f"; fix: {self.hint}"
        return rendered


class TextContractError(ValueError):
    """Aggregate explicit text-contract diagnostics without partial mutation."""

    def __init__(
        self,
        diagnostics: list[TextContractDiagnostic] | tuple[TextContractDiagnostic, ...],
    ):
        self.diagnostics = tuple(diagnostics)
        super().__init__(self.format())

    def format(self) -> str:
        """Format every diagnostic in deterministic discovery order."""
        return "\n".join(diagnostic.format() for diagnostic in self.diagnostics)


@dataclass
class TextVisualLine:
    """Normalized author-source view of one explicit paragraph visual line."""

    starter: ET.Element
    inline_tspans: tuple[ET.Element, ...]
    break_kind: str | None
    join_kind: str | None
    dy: float
    space_before: float = 0.0

    @property
    def elements(self) -> tuple[ET.Element, ...]:
        """Return the line starter followed by direct-child inline runs."""
        return (self.starter, *self.inline_tspans)


@dataclass
class TextBlockContract:
    """Validated explicit contract attached to one SVG ``<text>`` block."""

    element: ET.Element
    element_id: str
    requested_mode: str
    effective_mode: str
    mode_reason: str
    bounds: tuple[float, float, float, float] | None = None
    anchor_x: float | None = None
    anchor_y: float | None = None
    block_font_size: float | None = None
    base_line_height: float | None = None
    top_inset: float | None = None
    preserve_space: bool = False
    visual_lines: tuple[TextVisualLine, ...] = ()


def _local_name(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1]


def _style_map(elem: ET.Element) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for declaration in (elem.get("style") or "").split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        parsed[name.strip()] = value.strip()
    return parsed


def _element_chain(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> list[ET.Element]:
    chain = [elem]
    while chain[-1] in parent_map:
        chain.append(parent_map[chain[-1]])
    chain.reverse()
    return chain


def _effective_property(
    elem: ET.Element,
    name: str,
    parent_map: dict[ET.Element, ET.Element],
) -> str | None:
    value: str | None = None
    for node in _element_chain(elem, parent_map):
        if node.get(name) is not None:
            value = node.get(name)
        style_value = _style_map(node).get(name)
        if style_value is not None:
            value = style_value
    return value


def _preserves_space(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> bool:
    preserve = False
    for node in _element_chain(elem, parent_map):
        value = node.get(XML_SPACE_ATTR) or node.get("xml:space")
        if value == "preserve":
            preserve = True
        elif value == "default":
            preserve = False
    return preserve


def _parse_coordinate(value: str | None) -> float | None:
    if value is None:
        return None
    match = _COORDINATE_RE.fullmatch(value.strip())
    if not match:
        return None
    parsed = float(match.group(1))
    return parsed if math.isfinite(parsed) else None


def _parse_bounds(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    match = _FOUR_NUMBERS_RE.fullmatch(value)
    if not match:
        return None
    parsed = tuple(float(part) for part in match.groups())
    if not all(math.isfinite(part) for part in parsed):
        return None
    return parsed  # type: ignore[return-value]


def _parse_length_px(value: str | None, inherited: float = 16.0) -> float | None:
    if value is None:
        return inherited
    raw = value.strip().lower()
    match = re.fullmatch(rf"({_NUMBER})(px|pt|em|rem)?", raw)
    if not match:
        return None
    amount = float(match.group(1))
    if not math.isfinite(amount):
        return None
    unit = match.group(2) or "px"
    if unit == "pt":
        return amount * 4.0 / 3.0
    if unit in {"em", "rem"}:
        return amount * inherited
    return amount


def _effective_font_size(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> float | None:
    size = 16.0
    for node in _element_chain(elem, parent_map):
        raw = node.get("font-size")
        style_raw = _style_map(node).get("font-size")
        if style_raw is not None:
            raw = style_raw
        if raw is None:
            continue
        parsed = _parse_length_px(raw, size)
        if parsed is None or parsed <= 0:
            return None
        size = parsed
    return size


def _translate_only(value: str) -> bool:
    position = 0
    matched = False
    while position < len(value):
        separator = re.match(r"[\s,]*", value[position:])
        position += separator.end() if separator else 0
        if position >= len(value):
            break
        match = _TRANSLATE_RE.match(value, position)
        if not match:
            return False
        matched = True
        position = match.end()
    return matched


def _has_visible_direct_text(value: str | None, preserve_space: bool) -> bool:
    if not value:
        return False
    return bool(value) if preserve_space else bool(value.strip())


def _nearest_text(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> ET.Element | None:
    current = parent_map.get(elem)
    while current is not None:
        if _local_name(current) == "text":
            return current
        current = parent_map.get(current)
    return None


def _direct_metadata(elem: ET.Element, part: str) -> ET.Element | None:
    for child in elem:
        if (
            _local_name(child) == "metadata"
            and child.get("data-pptx-part") == part
        ):
            return child
    return None


def _native_text_carrier(
    text: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> ET.Element | None:
    current = parent_map.get(text)
    while current is not None:
        if _direct_metadata(current, "txbody") is not None:
            return current
        current = parent_map.get(current)
    return None


def _validate_native_carrier_contract(
    text: ET.Element,
    mode: str,
    merge_paragraphs: bool,
    parent_map: dict[ET.Element, ET.Element],
    diagnostics: list[TextContractDiagnostic],
) -> None:
    """Fail closed when an imported one-shape text carrier cannot be rebuilt."""
    carrier = _native_text_carrier(text, parent_map)
    if carrier is None:
        return

    if mode in {"auto", "lines"} or not merge_paragraphs:
        _add_diagnostic(
            diagnostics,
            "TEXT_NATIVE_MODE_UNSUPPORTED",
            text,
            "native text carriers only support effective paragraph mode",
            attribute=TEXT_MODE_ATTR,
            hint="use paragraph mode without --no-merge, or remove the native carrier metadata",
        )
        return

    visible_texts = [
        descendant
        for descendant in carrier.iter()
        if _local_name(descendant) == "text"
        and "".join(descendant.itertext()).strip()
    ]
    if len(visible_texts) != 1:
        _add_diagnostic(
            diagnostics,
            "TEXT_NATIVE_TEXT_COUNT",
            text,
            "native text carriers require exactly one non-empty text block",
            hint="keep one non-empty explicit paragraph inside the imported carrier",
        )

    carrier_metadata = _direct_metadata(carrier, "text-carrier")
    if (
        carrier_metadata is None
        or carrier_metadata.get("data-pptx-text-carrier-version") != "1"
    ):
        _add_diagnostic(
            diagnostics,
            "TEXT_NATIVE_CARRIER_METADATA_REQUIRED",
            text,
            "native paragraph recompilation requires version-1 text-carrier metadata",
            hint="re-import the source PPTX with the current pptx_to_svg converter",
        )
        return
    if carrier_metadata.get("data-pptx-text-carrier-eligible") != "1":
        reason = carrier_metadata.get("data-pptx-text-carrier-reason") or "unknown"
        _add_diagnostic(
            diagnostics,
            "TEXT_NATIVE_CARRIER_INELIGIBLE",
            text,
            f"the imported native text carrier is ineligible: {reason}",
            hint="use ordinary SVG text or remove the unsupported carrier feature",
        )


def _line_has_positional_descendant(starter: ET.Element) -> bool:
    for descendant in starter.iter():
        if descendant is starter or _local_name(descendant) != "tspan":
            continue
        if any(descendant.get(name) is not None for name in ("x", "y", "dy")):
            return True
    return False


def _add_diagnostic(
    diagnostics: list[TextContractDiagnostic],
    code: str,
    elem: ET.Element,
    message: str,
    *,
    attribute: str | None = None,
    hint: str | None = None,
    owner: ET.Element | None = None,
) -> None:
    identity = owner or elem
    diagnostics.append(
        TextContractDiagnostic(
            code=code,
            message=message,
            element_id=identity.get("id"),
            element_tag=_local_name(elem),
            attribute=attribute,
            hint=hint,
        )
    )


def _validate_transforms_and_baseline(
    text: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
    diagnostics: list[TextContractDiagnostic],
) -> None:
    for node in _element_chain(text, parent_map):
        style_transform = _style_map(node).get("transform")
        if style_transform is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_TRANSFORM_UNSUPPORTED",
                node,
                "CSS style transforms are unsupported for explicit paragraph bounds",
                attribute="style/transform",
                hint="move a pure translate into the SVG transform attribute",
                owner=text,
            )
            continue
        transform = node.get("transform")
        if transform and not _translate_only(transform):
            _add_diagnostic(
                diagnostics,
                "TEXT_TRANSFORM_UNSUPPORTED",
                node,
                "explicit paragraph bounds only support pure translate transforms",
                attribute="transform",
                hint="materialize the transform into coordinates or use mode='lines'",
                owner=text,
            )

    effective_dominant = _effective_property(text, "dominant-baseline", parent_map)
    effective_alignment = _effective_property(text, "alignment-baseline", parent_map)
    effective_shift = _effective_property(text, "baseline-shift", parent_map)
    if effective_dominant not in {None, "auto", "alphabetic"}:
        _add_diagnostic(
            diagnostics,
            "TEXT_BASELINE_UNSUPPORTED",
            text,
            f"unsupported inherited dominant-baseline {effective_dominant!r}",
            attribute="dominant-baseline",
            hint="use the default alphabetic baseline",
        )
    if effective_alignment not in {None, "auto", "baseline", "alphabetic"}:
        _add_diagnostic(
            diagnostics,
            "TEXT_BASELINE_UNSUPPORTED",
            text,
            f"unsupported inherited alignment-baseline {effective_alignment!r}",
            attribute="alignment-baseline",
            hint="use the default alphabetic baseline",
        )
    if effective_shift not in {
        None,
        "baseline",
        "0",
        "0px",
        "+0",
        "+0px",
        "-0",
        "-0px",
    }:
        _add_diagnostic(
            diagnostics,
            "TEXT_BASELINE_UNSUPPORTED",
            text,
            f"unsupported inherited baseline-shift {effective_shift!r}",
            attribute="baseline-shift",
            hint="remove baseline-shift from explicit paragraph text",
        )

    for node in text.iter():
        if node is text:
            continue
        if node is not text:
            transform = _style_map(node).get("transform") or node.get("transform")
            if transform:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_TRANSFORM_UNSUPPORTED",
                    node,
                    "tspan transforms are unsupported in explicit paragraph mode",
                    attribute="transform",
                    hint="remove the tspan transform and express line positions with x/dy",
                    owner=text,
                )

        styles = _style_map(node)
        dominant = styles.get("dominant-baseline") or node.get("dominant-baseline")
        alignment = styles.get("alignment-baseline") or node.get("alignment-baseline")
        shift = styles.get("baseline-shift") or node.get("baseline-shift")
        if dominant not in {None, "auto", "alphabetic"}:
            _add_diagnostic(
                diagnostics,
                "TEXT_BASELINE_UNSUPPORTED",
                node,
                f"unsupported dominant-baseline {dominant!r}",
                attribute="dominant-baseline",
                hint="use the default alphabetic baseline",
                owner=text,
            )
        if alignment not in {None, "auto", "baseline", "alphabetic"}:
            _add_diagnostic(
                diagnostics,
                "TEXT_BASELINE_UNSUPPORTED",
                node,
                f"unsupported alignment-baseline {alignment!r}",
                attribute="alignment-baseline",
                hint="use the default alphabetic baseline",
                owner=text,
            )
        if shift not in {None, "baseline", "0", "0px", "+0", "+0px", "-0", "-0px"}:
            _add_diagnostic(
                diagnostics,
                "TEXT_BASELINE_UNSUPPORTED",
                node,
                f"unsupported baseline-shift {shift!r}",
                attribute="baseline-shift",
                hint="remove baseline-shift from explicit paragraph text",
                owner=text,
            )


def _validate_unsupported_text_features(
    text: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
    diagnostics: list[TextContractDiagnostic],
) -> None:
    """Reject SVG text features that have no deterministic DrawingML mapping."""
    for attribute in ("dx", "dy", "rotate"):
        if text.get(attribute) is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_BLOCK_OFFSET_UNSUPPORTED",
                text,
                f"block-level {attribute} is unsupported in explicit paragraph mode",
                attribute=attribute,
                hint="fold the offset into x/y or use a pure translate",
            )

    for node in text.iter():
        for attribute in ("textLength", "lengthAdjust"):
            if node.get(attribute) is not None:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_LENGTH_ADJUST_UNSUPPORTED",
                    node,
                    "SVG text-length adjustment has no native paragraph mapping",
                    attribute=attribute,
                    hint="remove textLength/lengthAdjust and use normal font metrics",
                    owner=text,
                )
        if node is not text and node.get("rotate") is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_BLOCK_OFFSET_UNSUPPORTED",
                node,
                "per-character tspan rotation is unsupported in paragraph mode",
                attribute="rotate",
                hint="remove the rotate attribute or use mode='lines'",
                owner=text,
            )
        if node is text:
            continue
        styles = _style_map(node)
        if node.get("dx") is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_INLINE_OFFSET_UNSUPPORTED",
                node,
                "tspan dx offsets have no deterministic paragraph-run mapping",
                attribute="dx",
                hint="fold the offset into line x or remove it",
                owner=text,
            )
        local_writing = styles.get("writing-mode") or node.get("writing-mode")
        local_direction = styles.get("direction") or node.get("direction")
        local_bidi = styles.get("unicode-bidi") or node.get("unicode-bidi")
        if local_writing not in {None, "horizontal-tb"}:
            _add_diagnostic(
                diagnostics,
                "TEXT_WRITING_MODE_UNSUPPORTED",
                node,
                f"unsupported tspan writing-mode {local_writing!r}",
                attribute="writing-mode",
                hint="remove the run-level writing mode",
                owner=text,
            )
        if local_direction not in {None, "ltr"} or local_bidi not in {None, "normal"}:
            _add_diagnostic(
                diagnostics,
                "TEXT_DIRECTION_UNSUPPORTED",
                node,
                "run-level bidirectional controls are unsupported in v1",
                attribute="direction/unicode-bidi",
                hint="remove the run-level bidi controls",
                owner=text,
            )

    writing_mode = _effective_property(text, "writing-mode", parent_map)
    if writing_mode not in {None, "horizontal-tb"}:
        _add_diagnostic(
            diagnostics,
            "TEXT_WRITING_MODE_UNSUPPORTED",
            text,
            f"unsupported writing-mode {writing_mode!r}",
            attribute="writing-mode",
            hint="use horizontal-tb text or mode='lines'",
        )
    direction = _effective_property(text, "direction", parent_map)
    unicode_bidi = _effective_property(text, "unicode-bidi", parent_map)
    if direction not in {None, "ltr"} or unicode_bidi not in {None, "normal"}:
        _add_diagnostic(
            diagnostics,
            "TEXT_DIRECTION_UNSUPPORTED",
            text,
            "bidirectional paragraph controls are unsupported in v1",
            attribute="direction/unicode-bidi",
            hint="use default left-to-right text or mode='lines'",
        )


def _parse_paragraph_contract(
    text: ET.Element,
    element_id: str,
    parent_map: dict[ET.Element, ET.Element],
    merge_paragraphs: bool,
    diagnostics: list[TextContractDiagnostic],
) -> TextBlockContract | None:
    bounds_raw = text.get(TEXT_BOUNDS_ATTR)
    bounds = _parse_bounds(bounds_raw)
    if bounds_raw is None:
        _add_diagnostic(
            diagnostics,
            "TEXT_BOUNDS_REQUIRED",
            text,
            "paragraph mode requires four explicit text-frame bounds",
            attribute=TEXT_BOUNDS_ATTR,
            hint="add data-pptx-text-bounds='x y width height'",
        )
    elif bounds is None:
        _add_diagnostic(
            diagnostics,
            "TEXT_BOUNDS_INVALID",
            text,
            "bounds must contain exactly four finite unitless numbers",
            attribute=TEXT_BOUNDS_ATTR,
            hint="use data-pptx-text-bounds='x y width height'",
        )
    elif bounds[2] <= 0 or bounds[3] <= 0:
        _add_diagnostic(
            diagnostics,
            "TEXT_BOUNDS_NONPOSITIVE",
            text,
            "text-frame width and height must both be positive",
            attribute=TEXT_BOUNDS_ATTR,
            hint="provide positive width and height values",
        )

    _validate_transforms_and_baseline(text, parent_map, diagnostics)
    _validate_unsupported_text_features(text, parent_map, diagnostics)

    effective_font_size_raw = _effective_property(text, "font-size", parent_map)
    if (
        effective_font_size_raw is not None
        and re.fullmatch(rf"{_NUMBER}(?:em|rem)", effective_font_size_raw.strip().lower())
    ):
        _add_diagnostic(
            diagnostics,
            "TEXT_FONT_SIZE_RELATIVE",
            text,
            "relative block font sizes are unsupported in explicit paragraph mode",
            attribute="font-size",
            hint="resolve the block font size to unitless px or pt",
        )

    font_size = _effective_font_size(text, parent_map)
    if font_size is None:
        _add_diagnostic(
            diagnostics,
            "TEXT_FONT_SIZE_INVALID",
            text,
            "the inherited block font-size must resolve to a positive px value",
            attribute="font-size",
            hint="use a positive unitless, px, or pt font-size",
        )

    preserve_space = _preserves_space(text, parent_map)
    if _has_visible_direct_text(text.text, preserve_space):
        _add_diagnostic(
            diagnostics,
            "TEXT_PARAGRAPH_DIRECT_TEXT",
            text,
            "paragraph content must start inside a direct child tspan",
            hint="move the direct text into the first line tspan",
        )

    direct_children = list(text)
    for child in direct_children:
        if _local_name(child) != "tspan":
            _add_diagnostic(
                diagnostics,
                "TEXT_PARAGRAPH_CHILD_INVALID",
                child,
                "paragraph mode only accepts direct child tspan elements",
                hint="remove the non-tspan child or move it outside the text block",
                owner=text,
            )
        if _has_visible_direct_text(child.tail, preserve_space):
            _add_diagnostic(
                diagnostics,
                "TEXT_PARAGRAPH_DIRECT_TEXT",
                child,
                "direct tspan tail text is ambiguous paragraph content",
                hint="move the tail into the preceding or following line tspan",
                owner=text,
            )

    tspan_children = [child for child in direct_children if _local_name(child) == "tspan"]
    line_groups: list[list[ET.Element]] = []
    for tspan in tspan_children:
        positional = any(tspan.get(name) is not None for name in ("x", "y", "dy"))
        if positional:
            line_groups.append([tspan])
        elif not line_groups:
            _add_diagnostic(
                diagnostics,
                "TEXT_LINE_START_REQUIRED",
                tspan,
                "an inline tspan appears before the first positioned visual line",
                hint="give the first line tspan the required x/y or x/dy anchor",
                owner=text,
            )
        else:
            line_groups[-1].append(tspan)

    if not line_groups:
        _add_diagnostic(
            diagnostics,
            "TEXT_LINE_START_REQUIRED",
            text,
            "paragraph mode requires at least one positioned direct child tspan",
            hint="wrap the first visual line in a positioned tspan",
        )
        return None

    for group in line_groups:
        for line_part in group:
            if _line_has_positional_descendant(line_part):
                _add_diagnostic(
                    diagnostics,
                    "TEXT_POSITIONAL_NESTED",
                    line_part,
                    "nested positional tspans are unsupported in paragraph mode",
                    hint="keep x/y/dy only on direct visual-line starters",
                    owner=text,
                )
        content = "".join("".join(part.itertext()) for part in group)
        if not content.strip():
            _add_diagnostic(
                diagnostics,
                "TEXT_LINE_EMPTY",
                group[0],
                "empty or whitespace-only visual lines are unsupported in v1",
                hint="remove the empty line and express spacing on the next paragraph dy",
                owner=text,
            )

    parent_x_raw = text.get("x")
    parent_y_raw = text.get("y")
    first = line_groups[0][0]
    anchor_x: float | None = None
    anchor_y: float | None = None
    parent_anchor = parent_x_raw is not None or parent_y_raw is not None
    if parent_anchor and (parent_x_raw is None or parent_y_raw is None):
        _add_diagnostic(
            diagnostics,
            "TEXT_BLOCK_ANCHOR_INVALID",
            text,
            "parent text must provide both x and y, or neither",
            attribute="x/y",
            hint="use <text x y> with first <tspan x dy='0'>, or put x/y on the first tspan",
        )
    elif parent_anchor:
        anchor_x = _parse_coordinate(parent_x_raw)
        anchor_y = _parse_coordinate(parent_y_raw)
        first_x = _parse_coordinate(first.get("x"))
        first_dy = _parse_coordinate(first.get("dy"))
        if anchor_x is None or anchor_y is None or first_x is None:
            _add_diagnostic(
                diagnostics,
                "TEXT_BLOCK_ANCHOR_INVALID",
                first,
                "parent and first-line anchors must be finite unitless or px coordinates",
                attribute="x/y/dy",
                hint="use numeric parent x/y and repeat parent x on the first tspan",
                owner=text,
            )
        if first.get("y") is not None or first.get("dy") is None or first_dy != 0:
            _add_diagnostic(
                diagnostics,
                "TEXT_FIRST_LINE_GEOMETRY",
                first,
                "with parent x/y, the first line must use x and dy='0' without y",
                attribute="x/y/dy",
                hint="repeat the parent x and set dy='0' on the first tspan",
                owner=text,
            )
        if anchor_x is not None and first_x is not None and abs(anchor_x - first_x) > 1e-6:
            _add_diagnostic(
                diagnostics,
                "TEXT_LINE_X_MISMATCH",
                first,
                "first-line x does not repeat the block anchor",
                attribute="x",
                hint="set the first-line x equal to the parent text x",
                owner=text,
            )
    else:
        anchor_x = _parse_coordinate(first.get("x"))
        anchor_y = _parse_coordinate(first.get("y"))
        if anchor_x is None or anchor_y is None or first.get("dy") is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_FIRST_LINE_GEOMETRY",
                first,
                "without parent x/y, the first line must provide finite x/y and no dy",
                attribute="x/y/dy",
                hint="put x and y on the first tspan, or use the parent-anchor form",
                owner=text,
            )

    if first.get(TEXT_BREAK_ATTR) is not None:
        _add_diagnostic(
            diagnostics,
            "TEXT_BREAK_FIRST",
            first,
            "the first visual line cannot declare a preceding break",
            attribute=TEXT_BREAK_ATTR,
            hint="remove data-pptx-break from the first line",
            owner=text,
        )
    if first.get(TEXT_JOIN_ATTR) is not None:
        _add_diagnostic(
            diagnostics,
            "TEXT_JOIN_FORBIDDEN",
            first,
            "the first visual line cannot declare a join",
            attribute=TEXT_JOIN_ATTR,
            hint="remove data-pptx-join from the first line",
            owner=text,
        )

    raw_lines: list[tuple[ET.Element, tuple[ET.Element, ...], str | None, str | None, float]] = [
        (first, tuple(line_groups[0][1:]), None, None, 0.0)
    ]
    for group in line_groups[1:]:
        starter = group[0]
        line_x = _parse_coordinate(starter.get("x"))
        line_dy = _parse_coordinate(starter.get("dy"))
        if starter.get("y") is not None or starter.get("x") is None or line_x is None:
            _add_diagnostic(
                diagnostics,
                "TEXT_LINE_GEOMETRY_INVALID",
                starter,
                "later visual lines require a finite x and must not set y",
                attribute="x/y",
                hint="repeat the block anchor x and use a positive relative dy",
                owner=text,
            )
        if anchor_x is not None and line_x is not None and abs(anchor_x - line_x) > 1e-6:
            _add_diagnostic(
                diagnostics,
                "TEXT_LINE_X_MISMATCH",
                starter,
                "visual-line x does not repeat the block anchor",
                attribute="x",
                hint="set every line starter x equal to the block anchor",
                owner=text,
            )
        if line_dy is None or line_dy <= 0:
            _add_diagnostic(
                diagnostics,
                "TEXT_LINE_DY_INVALID",
                starter,
                "later visual lines require a positive relative dy",
                attribute="dy",
                hint="set dy to the positive distance from the preceding baseline",
                owner=text,
            )
            line_dy = 0.0
        break_kind = starter.get(TEXT_BREAK_ATTR)
        join_kind = starter.get(TEXT_JOIN_ATTR)
        if break_kind is None:
            _add_diagnostic(
                diagnostics,
                "TEXT_BREAK_REQUIRED",
                starter,
                "every visual line after the first must declare its break semantics",
                attribute=TEXT_BREAK_ATTR,
                hint="set data-pptx-break to soft, line, or paragraph",
                owner=text,
            )
        elif break_kind not in BREAK_KINDS:
            _add_diagnostic(
                diagnostics,
                "TEXT_BREAK_INVALID",
                starter,
                f"unknown break kind {break_kind!r}",
                attribute=TEXT_BREAK_ATTR,
                hint="use exactly soft, line, or paragraph",
                owner=text,
            )
        if break_kind == "soft":
            if join_kind is None:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_JOIN_REQUIRED",
                    starter,
                    "soft visual breaks require an explicit join policy",
                    attribute=TEXT_JOIN_ATTR,
                    hint="set data-pptx-join to space or none",
                    owner=text,
                )
            elif join_kind not in JOIN_KINDS:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_JOIN_INVALID",
                    starter,
                    f"unknown join kind {join_kind!r}",
                    attribute=TEXT_JOIN_ATTR,
                    hint="use exactly space or none",
                    owner=text,
                )
        elif join_kind is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_JOIN_FORBIDDEN",
                starter,
                "join is only valid with data-pptx-break='soft'",
                attribute=TEXT_JOIN_ATTR,
                hint="remove data-pptx-join or change the break to soft",
                owner=text,
            )
        raw_lines.append((starter, tuple(group[1:]), break_kind, join_kind, line_dy))

    for group in line_groups:
        for inline in group[1:]:
            for attribute in (TEXT_BREAK_ATTR, TEXT_JOIN_ATTR):
                if inline.get(attribute) is not None:
                    _add_diagnostic(
                        diagnostics,
                        (
                            "TEXT_BREAK_PLACEMENT"
                            if attribute == TEXT_BREAK_ATTR
                            else "TEXT_JOIN_PLACEMENT"
                        ),
                        inline,
                        "break/join metadata is only valid on a direct visual-line starter",
                        attribute=attribute,
                        hint="move the attribute to the positioned line-start tspan",
                        owner=text,
                    )

    base_line_height: float | None = None
    if len(raw_lines) > 1:
        positive_dys = [line[4] for line in raw_lines[1:] if line[4] > 0]
        if positive_dys:
            base_line_height = min(positive_dys)
            if font_size is not None and (
                base_line_height > font_size * MAX_DY_MULTIPLIER + DY_TOLERANCE_PX
            ):
                _add_diagnostic(
                    diagnostics,
                    "TEXT_LINE_HEIGHT_INVALID",
                    text,
                    "base line height exceeds three times the block font size",
                    attribute="dy",
                    hint="reduce line dy or split the content into separate text blocks",
                )
            for starter, _, break_kind, _, line_dy in raw_lines[1:]:
                if line_dy > base_line_height * MAX_DY_MULTIPLIER + DY_TOLERANCE_PX:
                    _add_diagnostic(
                        diagnostics,
                        "TEXT_LINE_HEIGHT_INVALID",
                        starter,
                        "line dy exceeds three times the normalized base line height",
                        attribute="dy",
                        hint="reduce the gap or use a separate text block",
                        owner=text,
                    )
                if break_kind in {"soft", "line"} and (
                    abs(line_dy - base_line_height) > DY_TOLERANCE_PX
                ):
                    _add_diagnostic(
                        diagnostics,
                        "TEXT_BREAK_SPACING_INVALID",
                        starter,
                        "soft and line breaks cannot carry paragraph spacing",
                        attribute="dy",
                        hint="use the base line height, or declare a paragraph break",
                        owner=text,
                    )

    visual_lines: list[TextVisualLine] = []
    for starter, inline, break_kind, join_kind, line_dy in raw_lines:
        space_before = 0.0
        if break_kind == "paragraph" and base_line_height is not None:
            space_before = max(0.0, line_dy - base_line_height)
        visual_lines.append(
            TextVisualLine(
                starter=starter,
                inline_tspans=inline,
                break_kind=break_kind,
                join_kind=join_kind,
                dy=line_dy,
                space_before=space_before,
            )
        )

    top_inset: float | None = None
    if bounds is not None and bounds[2] > 0 and bounds[3] > 0:
        text_anchor = _effective_property(text, "text-anchor", parent_map) or "start"
        if text_anchor not in {"start", "middle", "end"}:
            _add_diagnostic(
                diagnostics,
                "TEXT_ANCHOR_INVALID",
                text,
                f"unsupported text-anchor {text_anchor!r}",
                attribute="text-anchor",
                hint="use start, middle, or end",
            )
        if anchor_x is not None:
            expected_x = {
                "start": bounds[0],
                "middle": bounds[0] + bounds[2] / 2.0,
                "end": bounds[0] + bounds[2],
            }.get(text_anchor)
            if expected_x is not None and abs(anchor_x - expected_x) > DY_TOLERANCE_PX:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_BOUNDS_ANCHOR_MISMATCH",
                    text,
                    "block anchor x does not match the declared text frame and text-anchor",
                    attribute=TEXT_BOUNDS_ATTR,
                    hint="align line x with the frame left, center, or right anchor",
                )
        if anchor_y is not None:
            final_baseline = anchor_y + sum(line[4] for line in raw_lines[1:])
            bounds_bottom = bounds[1] + bounds[3]
            if (
                anchor_y < bounds[1] - DY_TOLERANCE_PX
                or anchor_y > bounds_bottom + DY_TOLERANCE_PX
                or final_baseline < bounds[1] - DY_TOLERANCE_PX
                or final_baseline > bounds_bottom + DY_TOLERANCE_PX
            ):
                _add_diagnostic(
                    diagnostics,
                    "TEXT_BOUNDS_BASELINE_OUTSIDE",
                    text,
                    "first or final visual baseline falls outside the declared text frame",
                    attribute=TEXT_BOUNDS_ATTR,
                    hint="increase frame height or correct the line baselines",
                )
            if font_size is not None:
                top_inset = anchor_y - bounds[1] - 0.85 * font_size
                if top_inset < -1e-9:
                    _add_diagnostic(
                        diagnostics,
                        "TEXT_TOP_INSET_NEGATIVE",
                        text,
                        "the baseline-to-frame offset produces a negative top inset",
                        attribute=TEXT_BOUNDS_ATTR,
                        hint="move bounds.y upward or move the first baseline downward",
                    )
                else:
                    top_inset = max(0.0, top_inset)

    effective_mode = "paragraph" if merge_paragraphs else "lines"
    mode_reason = "explicit-paragraph" if merge_paragraphs else "cli-no-merge"
    return TextBlockContract(
        element=text,
        element_id=element_id,
        requested_mode="paragraph",
        effective_mode=effective_mode,
        mode_reason=mode_reason,
        bounds=bounds,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        block_font_size=font_size,
        base_line_height=base_line_height,
        top_inset=top_inset,
        preserve_space=preserve_space,
        visual_lines=tuple(visual_lines),
    )


def validate_text_contracts(
    root: ET.Element,
    merge_paragraphs: bool = True,
    *,
    enforce_native_carrier: bool = True,
    source_name: str | None = None,
) -> dict[ET.Element, TextBlockContract]:
    """Validate every explicit text contract and return contracts by element.

    Validation is all-or-nothing. Every discoverable violation is collected and
    raised as one ``TextContractError`` before callers mutate the SVG tree.
    Unmarked legacy text is intentionally omitted from the result. Disable
    ``enforce_native_carrier`` only for strict visual-preview generation;
    formal PPTX export must keep it enabled.
    """
    diagnostics: list[TextContractDiagnostic] = []
    parent_map = {child: parent for parent in root.iter() for child in parent}
    id_counts: dict[str, int] = {}
    for elem in root.iter():
        elem_id = elem.get("id")
        if elem_id:
            id_counts[elem_id] = id_counts.get(elem_id, 0) + 1

    for elem in root.iter():
        tag = _local_name(elem)
        for attribute in elem.attrib:
            if attribute.startswith("data-paragraph-"):
                _add_diagnostic(
                    diagnostics,
                    "TEXT_INTERNAL_ATTR_FORBIDDEN",
                    elem,
                    "data-paragraph-* attributes are compiler-internal and cannot be authored",
                    attribute=attribute,
                    hint="remove the internal attribute and use the public text contract",
                    owner=_nearest_text(elem, parent_map),
                )
            elif attribute in RUNTIME_ATTRS:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_RUNTIME_ATTR_FORBIDDEN",
                    elem,
                    "data-pptx-runtime-* attributes are compiler-internal and cannot be authored",
                    attribute=attribute,
                    hint="remove the runtime attribute from svg_output",
                    owner=_nearest_text(elem, parent_map),
                )
        if elem.get(TEXT_MODE_ATTR) is not None and tag != "text":
            _add_diagnostic(
                diagnostics,
                "TEXT_MODE_PLACEMENT",
                elem,
                "text mode is only valid on an SVG text element",
                attribute=TEXT_MODE_ATTR,
                hint="move data-pptx-text-mode to the owning text element",
                owner=_nearest_text(elem, parent_map),
            )
        if elem.get(TEXT_BOUNDS_ATTR) is not None and tag != "text":
            _add_diagnostic(
                diagnostics,
                "TEXT_BOUNDS_PLACEMENT",
                elem,
                "text bounds are only valid on an SVG text element",
                attribute=TEXT_BOUNDS_ATTR,
                hint="move data-pptx-text-bounds to the owning text element",
                owner=_nearest_text(elem, parent_map),
            )
        for attribute, code in (
            (TEXT_BREAK_ATTR, "TEXT_BREAK_PLACEMENT"),
            (TEXT_JOIN_ATTR, "TEXT_JOIN_PLACEMENT"),
        ):
            if elem.get(attribute) is None:
                continue
            owner = _nearest_text(elem, parent_map)
            if tag != "tspan" or owner is None or parent_map.get(elem) is not owner:
                _add_diagnostic(
                    diagnostics,
                    code,
                    elem,
                    "break/join metadata is only valid on a direct visual-line tspan",
                    attribute=attribute,
                    hint="move the attribute to a direct line-start tspan in paragraph mode",
                    owner=owner,
                )
            elif owner.get(TEXT_MODE_ATTR) != "paragraph":
                _add_diagnostic(
                    diagnostics,
                    code,
                    elem,
                    "break/join metadata requires data-pptx-text-mode='paragraph'",
                    attribute=attribute,
                    hint="remove the attribute or opt the owning text into paragraph mode",
                    owner=owner,
                )

    contracts: dict[ET.Element, TextBlockContract] = {}
    for text in root.iter(f"{{{SVG_NS}}}text"):
        mode = text.get(TEXT_MODE_ATTR)
        if mode is None:
            if text.get(TEXT_BOUNDS_ATTR) is not None:
                _add_diagnostic(
                    diagnostics,
                    "TEXT_BOUNDS_MODE",
                    text,
                    "text bounds do not implicitly enable paragraph mode",
                    attribute=TEXT_BOUNDS_ATTR,
                    hint="add data-pptx-text-mode='paragraph' or remove bounds",
                )
            continue
        if mode not in TEXT_MODES:
            _add_diagnostic(
                diagnostics,
                "TEXT_MODE_INVALID",
                text,
                f"unknown text mode {mode!r}",
                attribute=TEXT_MODE_ATTR,
                hint="use exactly auto, paragraph, or lines without surrounding whitespace",
            )
            continue

        element_id = text.get("id") or ""
        if not element_id:
            _add_diagnostic(
                diagnostics,
                "TEXT_ID_REQUIRED",
                text,
                "an explicit text contract requires a non-empty stable id",
                attribute="id",
                hint="add a unique id to the text element",
            )
        elif id_counts.get(element_id, 0) != 1:
            _add_diagnostic(
                diagnostics,
                "TEXT_ID_DUPLICATE",
                text,
                f"explicit text id {element_id!r} is not unique in this SVG",
                attribute="id",
                hint="rename the text element so its id is unique",
            )

        if mode != "paragraph" and text.get(TEXT_BOUNDS_ATTR) is not None:
            _add_diagnostic(
                diagnostics,
                "TEXT_BOUNDS_FORBIDDEN",
                text,
                f"text bounds are not valid in {mode!r} mode",
                attribute=TEXT_BOUNDS_ATTR,
                hint="remove bounds or use paragraph mode",
            )

        if enforce_native_carrier:
            _validate_native_carrier_contract(
                text,
                mode,
                merge_paragraphs,
                parent_map,
                diagnostics,
            )

        if mode == "paragraph":
            contract = _parse_paragraph_contract(
                text,
                element_id,
                parent_map,
                merge_paragraphs,
                diagnostics,
            )
            if contract is not None:
                contracts[text] = contract
        else:
            effective_mode = "lines" if not merge_paragraphs or mode == "lines" else "auto"
            if not merge_paragraphs:
                reason = "cli-no-merge"
            elif mode == "lines":
                reason = "explicit-lines"
            else:
                reason = "legacy-auto"
            contracts[text] = TextBlockContract(
                element=text,
                element_id=element_id,
                requested_mode=mode,
                effective_mode=effective_mode,
                mode_reason=reason,
                preserve_space=_preserves_space(text, parent_map),
            )

    if diagnostics:
        if source_name:
            for diagnostic in diagnostics:
                diagnostic.source_name = source_name
        raise TextContractError(diagnostics)
    return contracts


__all__ = [
    "BREAK_KINDS",
    "JOIN_KINDS",
    "RUNTIME_CONTRACT_ATTR",
    "RUNTIME_ATTRS",
    "RUNTIME_EFFECTIVE_MODE_ATTR",
    "RUNTIME_LINE_COUNT_ATTR",
    "RUNTIME_LINE_INDEX_ATTR",
    "RUNTIME_MODE_REASON_ATTR",
    "RUNTIME_REQUESTED_MODE_ATTR",
    "RUNTIME_SOURCE_ID_ATTR",
    "TEXT_BOUNDS_ATTR",
    "TEXT_BREAK_ATTR",
    "TEXT_JOIN_ATTR",
    "TEXT_MODE_ATTR",
    "TextBlockContract",
    "TextContractDiagnostic",
    "TextContractError",
    "TextVisualLine",
    "validate_text_contracts",
]
