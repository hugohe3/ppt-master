#!/usr/bin/env python3
"""
PPT Master - Native Inline Formula Contract

Validate SVG inline-formula markers and build editable PowerPoint math runs.

Usage:
    Imported by the SVG quality checker and SVG-to-PPTX text converter.

Examples:
    <tspan data-pptx-inline-formula="x_i^2">xᵢ²</tspan>

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

from copy import deepcopy
from xml.etree import ElementTree as ET

from ..drawingml.utils import parse_inline_style, parse_svg_color
from .formula_compiler import (
    FormulaCompileError,
    compile_latex_to_inline_omml,
)


SVG_NS = "http://www.w3.org/2000/svg"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
OFFICE_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
INLINE_FORMULA_ATTR = "data-pptx-inline-formula"
_SVG_TEXT = f"{{{SVG_NS}}}text"
_SVG_TSPAN = f"{{{SVG_NS}}}tspan"
_SVG_A = f"{{{SVG_NS}}}a"
_MATH_RUN = f"{{{MATH_NS}}}r"
_MATH_RUN_PROPERTIES = f"{{{MATH_NS}}}rPr"
_DML_RUN_PROPERTIES = f"{{{DML_NS}}}rPr"
_POSITION_ATTRIBUTES = ("x", "y", "dx", "dy")
_PARAGRAPH_ATTRIBUTES = (
    "data-paragraph-line-height",
    "data-paragraph-line-break",
    "data-paragraph-soft-break",
    "data-paragraph-space-before",
)
_NON_OUTPUT_ANCESTORS = frozenset({
    "clipPath",
    "desc",
    "defs",
    "filter",
    "linearGradient",
    "marker",
    "mask",
    "metadata",
    "pattern",
    "radialGradient",
    "style",
    "symbol",
    "title",
})

for _prefix, _uri in (("a", DML_NS), ("m", MATH_NS)):
    try:
        ET.register_namespace(_prefix, _uri)
    except (ValueError, AttributeError):
        pass


def _marker_label(elem: ET.Element) -> str:
    elem_id = (elem.get("id") or "").strip()
    return f"<tspan id={elem_id!r}>" if elem_id else "<tspan>"


def inline_formula_marker_errors(root: ET.Element) -> list[str]:
    """Return strict authoring errors for every inline-formula marker."""
    errors: list[str] = []
    parent_map = {child: parent for parent in root.iter() for child in parent}
    markers = [
        elem for elem in root.iter()
        if elem.get(INLINE_FORMULA_ATTR) is not None
    ]

    for marker in markers:
        label = _marker_label(marker)
        if marker.tag != _SVG_TSPAN:
            tag = marker.tag.rsplit("}", 1)[-1]
            errors.append(
                f"{INLINE_FORMULA_ATTR} is only valid on <tspan>, found <{tag}>"
            )
            continue

        if marker.get("data-pptx-replace-with") is not None:
            errors.append(
                f"{label} cannot also declare data-pptx-replace-with"
            )

        source = marker.get(INLINE_FORMULA_ATTR) or ""
        if not source.strip():
            errors.append(f"{label} requires non-empty {INLINE_FORMULA_ATTR}")
        else:
            try:
                compile_latex_to_inline_omml(source)
            except FormulaCompileError as exc:
                errors.append(f"{label} has unsupported inline LaTeX: {exc}")

        if list(marker):
            errors.append(
                f"{label} must contain preview text directly and cannot nest elements"
            )
        if not (marker.text or "").strip():
            errors.append(f"{label} requires non-empty visible SVG preview text")
        elif marker.text != marker.text.strip():
            errors.append(
                f"{label} preview cannot contain leading or trailing whitespace; "
                "place spacing in the surrounding text"
            )

        positioned = [name for name in _POSITION_ATTRIBUTES if marker.get(name) is not None]
        if positioned:
            errors.append(
                f"{label} is an inline run and cannot set " + ", ".join(positioned)
            )
        paragraph_attrs = [
            name for name in _PARAGRAPH_ATTRIBUTES
            if marker.get(name) is not None
        ]
        if paragraph_attrs:
            errors.append(
                f"{label} cannot own paragraph layout metadata: "
                + ", ".join(paragraph_attrs)
            )

        effective_fill: str | None = None
        style_owner: ET.Element | None = marker
        while style_owner is not None:
            inline_style = parse_inline_style(style_owner.get("style"))
            effective_fill = inline_style.get("fill")
            if effective_fill is None:
                effective_fill = style_owner.get("fill")
            if effective_fill is not None:
                break
            style_owner = parent_map.get(style_owner)
        color, alpha = parse_svg_color(effective_fill or "#000000")
        if color is None or alpha <= 0:
            errors.append(
                f"{label} requires one visible solid fill color inherited "
                "from itself or its text ancestors"
            )

        parent = parent_map.get(marker)
        text_owner: ET.Element | None = None
        nested_marker = False
        inside_block_formula = False
        inside_native_replacement = False
        inside_preserved_text = False
        inside_placeholder = False
        inside_skipped_transport = False
        inside_baseline_shift = marker.get("baseline-shift") is not None
        invalid_inline_container: str | None = None
        non_output_ancestor: str | None = None
        fixed_structure_layer: str | None = None
        while parent is not None:
            parent_tag = parent.tag.rsplit("}", 1)[-1]
            if text_owner is None and parent.tag == _SVG_TEXT:
                text_owner = parent
            elif (
                text_owner is None
                and parent.tag not in {_SVG_A, _SVG_TSPAN}
                and invalid_inline_container is None
            ):
                invalid_inline_container = parent_tag
            if parent_tag in _NON_OUTPUT_ANCESTORS:
                non_output_ancestor = parent_tag
            if parent.get(INLINE_FORMULA_ATTR) is not None:
                nested_marker = True
            if parent.get("baseline-shift") is not None:
                inside_baseline_shift = True
            replacement = (
                parent.get("data-pptx-replace-with") or ""
            ).strip().lower()
            if replacement:
                inside_native_replacement = True
                inside_block_formula = (
                    inside_block_formula or replacement == "formula"
                )
            if (parent.get("data-pptx-part") or "").strip() in {
                "geometry-detail",
                "geometry-preview",
            }:
                inside_skipped_transport = True
            if parent.get("data-pptx-placeholder") is not None:
                inside_placeholder = True
            layer = (parent.get("data-pptx-layer") or "").strip().lower()
            if layer in {"master", "layout"}:
                fixed_structure_layer = layer
            if any(
                child.tag.rsplit("}", 1)[-1] == "metadata"
                and child.get("data-pptx-part") == "txbody"
                for child in parent
            ):
                inside_preserved_text = True
            parent = parent_map.get(parent)
        if text_owner is None:
            errors.append(f"{label} must be inside an SVG <text> element")
        elif invalid_inline_container is not None:
            errors.append(
                f"{label} can only be nested through <tspan>/<a> elements before "
                f"its owning <text>, found <{invalid_inline_container}>"
            )
        if non_output_ancestor is not None:
            errors.append(
                f"{label} cannot be placed inside non-output "
                f"<{non_output_ancestor}> content"
            )
        if nested_marker:
            errors.append(f"{label} cannot be nested inside another inline formula marker")
        if inside_baseline_shift:
            errors.append(
                f"{label} cannot combine baseline-shift with an inline formula"
            )
        if inside_block_formula:
            errors.append(
                f"{label} cannot be placed inside a block formula preview"
            )
        elif inside_native_replacement:
            errors.append(
                f"{label} cannot be placed inside a native replacement subtree"
            )
        if inside_skipped_transport:
            errors.append(
                f"{label} cannot be placed inside non-output geometry transport"
            )
        if inside_preserved_text:
            errors.append(
                f"{label} cannot be placed inside an imported preserved txBody group"
            )
        if inside_placeholder:
            errors.append(
                f"{label} cannot be used inside a structured Layout placeholder"
            )
        if fixed_structure_layer is not None:
            errors.append(
                f"{label} cannot be used on the {fixed_structure_layer} layer; "
                "inline formulas are slide-local text"
            )

    return errors


def _apply_run_properties(omml: str, run_properties_xml: str) -> str:
    """Replace DrawingML properties on every Office Math leaf run."""
    try:
        root = ET.fromstring(omml)
        wrapper = ET.fromstring(
            f'<root xmlns:a="{DML_NS}" xmlns:r="{OFFICE_REL_NS}">'
            f"{run_properties_xml}</root>"
        )
    except (ET.ParseError, RecursionError) as exc:
        raise RuntimeError(f"Invalid inline formula XML: {exc}") from exc
    if len(wrapper) != 1:
        raise RuntimeError("Inline formula styling must contain one a:rPr root")
    run_properties = wrapper[0]
    if root.tag != f"{{{MATH_NS}}}oMath":
        raise RuntimeError("Inline formula compiler must return one m:oMath root")
    if run_properties.tag != _DML_RUN_PROPERTIES:
        raise RuntimeError("Inline formula styling must use one a:rPr root")

    for run in root.iter(_MATH_RUN):
        for existing in list(run):
            if existing.tag == _DML_RUN_PROPERTIES:
                run.remove(existing)
        insert_at = 1 if len(run) and run[0].tag == _MATH_RUN_PROPERTIES else 0
        run.insert(insert_at, deepcopy(run_properties))

    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def build_inline_formula_xml(latex: str, run_properties_xml: str) -> str:
    """Build one ``a14:m`` inline math zone for insertion inside ``a:p``."""
    try:
        omml = compile_latex_to_inline_omml(latex)
    except FormulaCompileError as exc:
        raise RuntimeError(f"Unsupported inline formula LaTeX: {exc}") from exc
    styled = _apply_run_properties(omml, run_properties_xml)
    return f"<a14:m>{styled}</a14:m>"


def wrap_inline_formula_shape(shape_xml: str) -> str:
    """Wrap a text shape containing ``a14:m`` in its required MCE Choice."""
    return (
        f'<mc:AlternateContent xmlns:mc="{MC_NS}">'
        f'<mc:Choice xmlns:a14="{A14_NS}" Requires="a14">'
        f"{shape_xml}"
        "</mc:Choice>"
        "</mc:AlternateContent>"
    )


__all__ = [
    "INLINE_FORMULA_ATTR",
    "build_inline_formula_xml",
    "inline_formula_marker_errors",
    "wrap_inline_formula_shape",
]
