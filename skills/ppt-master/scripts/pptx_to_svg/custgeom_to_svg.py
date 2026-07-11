"""DrawingML <a:custGeom> -> SVG <path d="..."> conversion.

Reverse of svg_to_pptx/drawingml/paths.py path_commands_to_drawingml.

Path command mapping:
    <a:moveTo>      -> M
    <a:lnTo>        -> L
    <a:cubicBezTo>  -> C
    <a:quadBezTo>   -> Q
    <a:arcTo>       -> A   (DrawingML uses center + sweep angles; we convert
                            to SVG endpoint parameterization)
    <a:close/>      -> Z

DrawingML <a:path w="..." h="..."> defines a shape-local coordinate system.
Each path resolves guide formulas against that local coordinate system, then
its coordinates are projected into the shape's absolute SVG frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET

from pptx_shapes import FormulaEvaluationError, FormulaEvaluator

from .emu_units import NS, Xfrm
from .preset_registry_to_svg import render_evaluated_path


@dataclass(frozen=True)
class _EvaluatedCommand:
    name: str
    parameters: tuple[float, ...]


def convert_custom_geom(
    cust_geom: ET.Element,
    xfrm: Xfrm,
) -> str | None:
    """Evaluate a complete custom geometry and return absolute SVG path data."""
    path_lst = cust_geom.find("a:pathLst", NS)
    if path_lst is None:
        return None
    shape_evaluator = _custom_geometry_evaluator(cust_geom, xfrm.w, xfrm.h)
    paths = [
        _convert_one_path(path_elem, cust_geom, xfrm, shape_evaluator)
        for path_elem in path_lst.findall("a:path", NS)
    ]
    rendered = [path for path in paths if path]
    return " ".join(rendered) if rendered else None


def _custom_geometry_evaluator(
    cust_geom: ET.Element,
    width: float,
    height: float,
) -> FormulaEvaluator:
    evaluator = FormulaEvaluator(width, height)
    for list_name in ("avLst", "gdLst"):
        guide_list = cust_geom.find(f"a:{list_name}", NS)
        if guide_list is None:
            continue
        for guide in guide_list.findall("a:gd", NS):
            name = guide.attrib.get("name", "").strip()
            formula = guide.attrib.get("fmla", "").strip()
            if not name or not formula:
                raise FormulaEvaluationError(
                    f"Custom geometry {list_name} contains an incomplete guide"
                )
            evaluator.bind(name, evaluator.evaluate(formula))
    return evaluator


def _convert_one_path(
    path_elem: ET.Element,
    cust_geom: ET.Element,
    xfrm: Xfrm,
    shape_evaluator: FormulaEvaluator,
) -> str:
    coordinate_width = _path_extent(
        path_elem.get("w"),
        xfrm.w,
        shape_evaluator,
    )
    coordinate_height = _path_extent(
        path_elem.get("h"),
        xfrm.h,
        shape_evaluator,
    )
    path_evaluator = _custom_geometry_evaluator(
        cust_geom,
        coordinate_width,
        coordinate_height,
    )
    commands = tuple(
        _evaluate_path_command(command, path_evaluator)
        for command in path_elem
        if isinstance(command.tag, str)
    )
    return render_evaluated_path(
        commands,
        x=xfrm.x,
        y=xfrm.y,
        width=xfrm.w,
        height=xfrm.h,
        coordinate_width=coordinate_width,
        coordinate_height=coordinate_height,
    )


def _evaluate_path_command(
    element: ET.Element,
    evaluator: FormulaEvaluator,
) -> _EvaluatedCommand:
    name = element.tag.rsplit("}", 1)[-1]
    if name == "arcTo":
        values = tuple(
            evaluator.evaluate_value(_required_attr(element, attr))
            for attr in ("wR", "hR", "stAng", "swAng")
        )
        return _EvaluatedCommand(name=name, parameters=values)
    expected_points = {
        "moveTo": 1,
        "lnTo": 1,
        "quadBezTo": 2,
        "cubicBezTo": 3,
        "close": 0,
    }.get(name)
    if expected_points is None:
        raise FormulaEvaluationError(
            f"Unsupported custom geometry path command: {name!r}"
        )
    points = element.findall("a:pt", NS)
    if len(points) != expected_points:
        raise FormulaEvaluationError(
            f"Custom path command {name!r} expects {expected_points} point(s), "
            f"found {len(points)}"
        )
    values = tuple(
        evaluator.evaluate_value(_required_attr(point, coordinate))
        for point in points
        for coordinate in ("x", "y")
    )
    return _EvaluatedCommand(name=name, parameters=values)


def _path_extent(
    raw: str | None,
    shape_extent: float,
    evaluator: FormulaEvaluator,
) -> float:
    if raw is None:
        return shape_extent
    value = evaluator.evaluate_value(raw)
    return shape_extent if value == 0 else value


def _required_attr(element: ET.Element, name: str) -> str:
    value = element.attrib.get(name)
    if value is None or not value.strip():
        raise FormulaEvaluationError(
            f"Custom geometry element {element.tag.rsplit('}', 1)[-1]!r} "
            f"requires attribute {name!r}"
        )
    return value.strip()
