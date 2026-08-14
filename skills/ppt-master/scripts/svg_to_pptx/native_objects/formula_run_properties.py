#!/usr/bin/env python3
"""
PPT Master - Native Formula Run Property Merge

Merge marker-level DrawingML defaults with compiler-owned local formula style
without discarding either source.

See references/native-formula.md for the owning formula-style contract.

Usage:
    Imported by block and inline native formula builders.

Examples:
    merge_formula_run_properties(run, marker_properties)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

from copy import deepcopy
from xml.etree import ElementTree as ET

from .formula_omml import validate_omml_resource_limits
from .formula_parser import FormulaCompileError


DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

_DML_RUN_PROPERTIES = f"{{{DML_NS}}}rPr"
_MATH_RUN_PROPERTIES = f"{{{MATH_NS}}}rPr"
_MATH_CONTROL_PROPERTIES = f"{{{MATH_NS}}}ctrlPr"
_CONTROL_OWNER_TAGS = frozenset({
    f"{{{MATH_NS}}}{name}"
    for name in (
        "accPr",
        "barPr",
        "borderBoxPr",
        "boxPr",
        "dPr",
        "fPr",
        "groupChrPr",
        "naryPr",
        "radPr",
    )
})
_FILL_TAGS = frozenset({
    f"{{{DML_NS}}}blipFill",
    f"{{{DML_NS}}}gradFill",
    f"{{{DML_NS}}}grpFill",
    f"{{{DML_NS}}}noFill",
    f"{{{DML_NS}}}pattFill",
    f"{{{DML_NS}}}solidFill",
})
_COLOR_TAGS = frozenset({
    f"{{{DML_NS}}}{name}"
    for name in ("hslClr", "prstClr", "schemeClr", "scrgbClr", "srgbClr", "sysClr")
})
_ALPHA_TRANSFORM_TAGS = frozenset({
    f"{{{DML_NS}}}{name}"
    for name in ("alpha", "alphaMod", "alphaOff")
})
_RUN_PROPERTY_ORDER = {
    f"{{{DML_NS}}}{name}": index
    for index, names in enumerate((
        ("ln",),
        ("blipFill", "gradFill", "grpFill", "noFill", "pattFill", "solidFill"),
        ("effectDag", "effectLst"),
        ("highlight",),
        ("uLnTx",),
        ("uLn",),
        ("uFillTx",),
        ("uFill",),
        ("latin",),
        ("ea",),
        ("cs",),
        ("sym",),
        ("hlinkClick",),
        ("hlinkMouseOver",),
        ("rtl",),
        ("extLst",),
    ))
    for name in names
}


def _replace_child_group(
    target: ET.Element,
    local: ET.Element,
    tags: frozenset[str],
) -> None:
    local_children = [child for child in local if child.tag in tags]
    if not local_children:
        return
    positions = [index for index, child in enumerate(target) if child.tag in tags]
    insert_at = positions[0] if positions else 0
    for child in list(target):
        if child.tag in tags:
            target.remove(child)
    for offset, child in enumerate(local_children):
        target.insert(insert_at + offset, deepcopy(child))


def _inherit_default_fill_alpha(
    default_properties: ET.Element,
    local_properties: ET.Element,
) -> None:
    default_fill = next(
        (child for child in default_properties if child.tag in _FILL_TAGS),
        None,
    )
    local_fill = next(
        (child for child in local_properties if child.tag in _FILL_TAGS),
        None,
    )
    if default_fill is None or local_fill is None:
        return
    default_color = next(
        (child for child in default_fill if child.tag in _COLOR_TAGS),
        None,
    )
    local_color = next(
        (child for child in local_fill if child.tag in _COLOR_TAGS),
        None,
    )
    if default_color is None or local_color is None:
        return
    if any(child.tag in _ALPHA_TRANSFORM_TAGS for child in local_color):
        return
    for child in default_color:
        if child.tag in _ALPHA_TRANSFORM_TAGS:
            local_color.append(deepcopy(child))


def _normalize_child_order(properties: ET.Element) -> None:
    children = list(properties)
    ordered = sorted(
        enumerate(children),
        key=lambda item: (
            _RUN_PROPERTY_ORDER.get(item[1].tag, len(_RUN_PROPERTY_ORDER)),
            item[0],
        ),
    )
    if [child for _, child in ordered] == children:
        return
    for child in children:
        properties.remove(child)
    for _, child in ordered:
        properties.append(child)


def _merged_properties(
    default_properties: ET.Element,
    local_properties: ET.Element | None,
) -> ET.Element:
    merged = deepcopy(default_properties)
    if local_properties is None:
        _normalize_child_order(merged)
        return merged
    local = deepcopy(local_properties)
    _inherit_default_fill_alpha(merged, local)
    merged.attrib.update(local.attrib)
    _replace_child_group(merged, local, _FILL_TAGS)
    for child in local:
        if child.tag in _FILL_TAGS:
            continue
        for existing in list(merged):
            if existing.tag == child.tag:
                merged.remove(existing)
        merged.append(deepcopy(child))
    _normalize_child_order(merged)
    return merged


def merge_formula_run_properties(
    run: ET.Element,
    default_properties: ET.Element,
) -> None:
    """Merge one formula run's local a:rPr over marker-level defaults."""
    if default_properties.tag != _DML_RUN_PROPERTIES:
        raise RuntimeError("Formula run defaults must use one a:rPr root")
    local_properties = next(
        (child for child in run if child.tag == _DML_RUN_PROPERTIES),
        None,
    )
    merged = _merged_properties(default_properties, local_properties)
    if local_properties is not None:
        run.remove(local_properties)
    insert_at = 1 if len(run) and run[0].tag == _MATH_RUN_PROPERTIES else 0
    run.insert(insert_at, merged)


def merge_formula_control_properties(
    root: ET.Element,
    default_properties: ET.Element,
) -> None:
    """Merge marker defaults onto visible non-selectable math controls."""
    if default_properties.tag != _DML_RUN_PROPERTIES:
        raise RuntimeError("Formula control defaults must use one a:rPr root")
    for owner in root.iter():
        if owner.tag not in _CONTROL_OWNER_TAGS:
            continue
        control = next(
            (child for child in owner if child.tag == _MATH_CONTROL_PROPERTIES),
            None,
        )
        if control is None:
            control = ET.SubElement(owner, _MATH_CONTROL_PROPERTIES)
        local_properties = next(
            (child for child in control if child.tag == _DML_RUN_PROPERTIES),
            None,
        )
        merged = _merged_properties(default_properties, local_properties)
        if local_properties is not None:
            control.remove(local_properties)
        control.insert(0, merged)


def serialize_styled_formula_omml(root: ET.Element) -> str:
    """Serialize styled OMML under the compiler's final size and depth limits."""
    try:
        xml = ET.tostring(root, encoding="unicode", short_empty_elements=True)
        return validate_omml_resource_limits(xml)
    except (FormulaCompileError, RecursionError) as exc:
        raise RuntimeError(f"Invalid styled formula OMML: {exc}") from exc


__all__ = [
    "merge_formula_control_properties",
    "merge_formula_run_properties",
    "serialize_styled_formula_omml",
]
