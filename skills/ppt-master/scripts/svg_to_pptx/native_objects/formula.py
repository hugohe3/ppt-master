#!/usr/bin/env python3
"""
PPT Master - Native Formula Shape Builder

Build editable PowerPoint formula shapes from explicit LaTeX markers.

Usage:
    Imported by the SVG-to-PPTX native-object converter.

Examples:
    from svg_to_pptx.native_objects.formula import build_native_formula

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.context import ConvertContext, ShapeResult
from ..drawingml.utils import _xml_escape, font_px_to_hpt
from .formula_compiler import FormulaCompileError, compile_latex_to_omml
from .marker_common import _bounds, _hex_or_none


DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_MATH_RUN = f"{{{MATH_NS}}}r"
_MATH_RUN_PROPERTIES = f"{{{MATH_NS}}}rPr"
_DML_RUN_PROPERTIES = f"{{{DML_NS}}}rPr"
_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_ALIGNMENTS = {
    "center": ("ctr", "center"),
    "left": ("l", "left"),
    "right": ("r", "right"),
}

for _prefix, _uri in (("a", DML_NS), ("m", MATH_NS)):
    try:
        ET.register_namespace(_prefix, _uri)
    except (ValueError, AttributeError):
        pass


@dataclass(frozen=True)
class FormulaSpec:
    """Validated formula source plus the PowerPoint text style to apply."""

    omml: str
    font_size_hpt: int
    color: str
    paragraph_alignment: str
    math_alignment: str
    language: str


def _positive_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise RuntimeError(f"Native PPTX formula {field_name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError(
            f"Native PPTX formula {field_name} must be numeric"
        ) from exc
    if not math.isfinite(result) or result <= 0:
        raise RuntimeError(
            f"Native PPTX formula {field_name} must be a positive finite number"
        )
    return result


def _formula_language(payload: dict[str, Any], ctx: ConvertContext | None) -> str:
    raw = payload.get("language")
    if raw is None and ctx is not None:
        raw = ctx.primary_language
    language = str(raw or "en-US").strip()
    if len(language) > 35 or _LANGUAGE_RE.fullmatch(language) is None:
        raise RuntimeError(
            "Native PPTX formula language must be a compact BCP-47 tag"
        )
    return language


def validate_formula_payload(
    payload: dict[str, Any],
    *,
    ctx: ConvertContext | None = None,
) -> FormulaSpec:
    """Validate and compile one block-formula payload."""
    latex = payload.get("latex")
    if not isinstance(latex, str) or not latex.strip():
        raise RuntimeError("Native PPTX formula metadata requires non-empty `latex`")

    display = str(payload.get("display") or "block").strip().lower()
    if display != "block":
        raise RuntimeError(
            "Native PPTX formula currently supports independent block formulas only"
        )

    raw_font_size = payload.get("font_size", 28)
    font_size_px = _positive_number(raw_font_size, "font_size")
    if font_size_px > 400:
        raise RuntimeError("Native PPTX formula font_size must not exceed 400 px")
    try:
        font_size_hpt = font_px_to_hpt(font_size_px)
    except ValueError as exc:
        raise RuntimeError(
            "Native PPTX formula font_size is outside the PowerPoint range"
        ) from exc

    raw_color = payload.get("color", "#000000")
    color = _hex_or_none(raw_color)
    if color is None:
        raise RuntimeError(
            "Native PPTX formula color must be a visible CSS color or HEX value"
        )

    alignment = str(payload.get("align") or "center").strip().lower()
    if alignment not in _ALIGNMENTS:
        choices = ", ".join(sorted(_ALIGNMENTS))
        raise RuntimeError(
            f"Native PPTX formula align must be one of: {choices}"
        )
    paragraph_alignment, math_alignment = _ALIGNMENTS[alignment]

    try:
        omml = compile_latex_to_omml(latex)
    except FormulaCompileError as exc:
        raise RuntimeError(f"Native PPTX formula LaTeX is unsupported: {exc}") from exc

    return FormulaSpec(
        omml=omml,
        font_size_hpt=font_size_hpt,
        color=color,
        paragraph_alignment=paragraph_alignment,
        math_alignment=math_alignment,
        language=_formula_language(payload, ctx),
    )


def _styled_omml(spec: FormulaSpec) -> str:
    """Apply DrawingML run styling and alignment to validated OMML."""
    root = ET.fromstring(spec.omml)
    if root.tag == f"{{{MATH_NS}}}oMathPara":
        para_properties = root.find(f"{{{MATH_NS}}}oMathParaPr")
        if para_properties is None:
            para_properties = ET.Element(f"{{{MATH_NS}}}oMathParaPr")
            root.insert(0, para_properties)
        justification = para_properties.find(f"{{{MATH_NS}}}jc")
        if justification is None:
            justification = ET.SubElement(
                para_properties,
                f"{{{MATH_NS}}}jc",
            )
        justification.set(f"{{{MATH_NS}}}val", spec.math_alignment)

    for run in root.iter(_MATH_RUN):
        for existing in list(run):
            if existing.tag == _DML_RUN_PROPERTIES:
                run.remove(existing)

        run_properties = ET.Element(
            _DML_RUN_PROPERTIES,
            {
                "lang": spec.language,
                "sz": str(spec.font_size_hpt),
                "dirty": "0",
            },
        )
        solid_fill = ET.SubElement(run_properties, f"{{{DML_NS}}}solidFill")
        ET.SubElement(
            solid_fill,
            f"{{{DML_NS}}}srgbClr",
            {"val": spec.color},
        )
        for tag in ("latin", "ea", "cs"):
            ET.SubElement(
                run_properties,
                f"{{{DML_NS}}}{tag}",
                {"typeface": "Cambria Math"},
            )

        insert_at = 0
        if len(run) and run[0].tag == _MATH_RUN_PROPERTIES:
            insert_at = 1
        run.insert(insert_at, run_properties)

    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def build_native_formula(
    elem: ET.Element,
    ctx: ConvertContext,
    payload: dict[str, Any],
    spec: FormulaSpec | None = None,
) -> ShapeResult:
    """Build one Choice-only editable formula with no image fallback."""
    formula_spec = spec or validate_formula_payload(payload, ctx=ctx)
    off_x, off_y, ext_cx, ext_cy = _bounds(elem, payload, ctx)
    shape_id = ctx.next_id()
    name = _xml_escape(
        str(payload.get("name") or elem.get("id") or f"Formula {shape_id}")
    )
    omml = _styled_omml(formula_spec)

    xml = f'''<mc:AlternateContent xmlns:mc="{MC_NS}">
<mc:Choice xmlns:a14="{A14_NS}" Requires="a14">
<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvSpPr txBox="1"><a:spLocks noGrp="1"/></p:cNvSpPr>
<p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
<a:noFill/>
<a:ln><a:noFill/></a:ln>
</p:spPr>
<p:txBody>
<a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0" wrap="none" anchor="ctr">
<a:normAutofit/>
</a:bodyPr>
<a:lstStyle/>
<a:p><a:pPr algn="{formula_spec.paragraph_alignment}"/>
<a14:m>{omml}</a14:m>
</a:p>
</p:txBody>
</p:sp>
</mc:Choice>
</mc:AlternateContent>'''
    return ShapeResult(
        xml=xml,
        bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy),
    )
