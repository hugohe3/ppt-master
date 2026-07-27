#!/usr/bin/env python3
"""
PPT Master - Shape Boolean Core

Resolve closed SVG operands into root-coordinate paths and apply
PowerPoint-compatible merge-shapes operations without mutating the source SVG.
Callers insert returned paths at the SVG root in the primary operand's z-order;
reinserting them below an original transformed ancestor would transform twice.

Usage:
    Import render_boolean_svg_fragments from svg_to_pptx.shape_boolean.

Examples:
    fragment = render_boolean_svg_fragments(
        "projects/demo/svg_output/slide-01.svg",
        operation="intersect",
        source_ids=("shape-a", "shape-b"),
        output_id="shape-overlap",
    )

Dependencies:
    skia-pathops and local PPT Master modules
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from pptx_to_svg.emu_units import Xfrm
from pptx_to_svg.preset_authoring import (
    authored_preset_encoding,
    validate_authored_preset_group,
)
from pptx_to_svg.preset_registry_to_svg import render_preset_geometry
from pptx_to_svg.preset_svg_markup import attrs_to_xml

from .drawingml.context import AffineMatrix, IDENTITY_MATRIX
from .drawingml.paths import (
    PathCommand,
    normalize_path_commands,
    parse_svg_path,
    parse_svg_points,
    svg_path_to_absolute,
    transform_path_commands,
)
from .drawingml.utils import (
    matrix_multiply,
    parse_inline_style,
    parse_opacity,
    parse_project_geometry_length,
    parse_transform_matrix,
)


BOOLEAN_OPERATIONS = frozenset({
    "combine",
    "fragment",
    "intersect",
    "subtract",
    "union",
})

_BOOLEAN_TAGS = frozenset({"circle", "ellipse", "path", "polygon", "rect"})
_DEFINITION_TAGS = frozenset({
    "clipPath",
    "defs",
    "marker",
    "mask",
    "pattern",
    "symbol",
})
_ID_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]*")
_PRESENTATION_ATTRS = (
    "fill",
    "fill-opacity",
    "opacity",
    "stroke",
    "stroke-dasharray",
    "stroke-width",
    "stroke-opacity",
    "stroke-linecap",
    "stroke-linejoin",
)
_ROUNDTRIP_TRANSPORT_ATTRS = frozenset({
    "data-pptx-custgeom",
    "data-pptx-custgeom-ref",
    "data-pptx-geometry-kind",
    "data-pptx-native",
    "data-pptx-native-ref",
    "data-pptx-native-source",
    "data-pptx-native-status",
    "data-pptx-part",
    "data-pptx-shape-id",
    "data-pptx-shape-scope",
    "data-pptx-source-ref",
})
_RESULT_PRECISION = 6
_BEZIER_QUARTER_K = 0.5522847498307936


def render_boolean_svg_fragments(
    svg_file: str | Path,
    *,
    operation: str,
    source_ids: Sequence[str],
    output_id: str,
    style: Mapping[str, str] | None = None,
) -> str:
    """Return canonical SVG path fragments for one merge-shapes operation.

    The first source is the primary shape: subtract removes all later sources
    from it, and every result inherits its effective presentation attributes.
    All transforms are baked into root SVG coordinates, so callers must insert
    the result at the root in the primary operand's z-order. Fragment returns
    top-to-bottom, left-to-right sibling paths named ``<output_id>-1`` onward;
    every other operation returns one path named exactly ``output_id``.
    """
    if not isinstance(operation, str):
        raise ValueError("Shape Boolean operation must be a string")
    normalized_operation = operation.strip().lower()
    if normalized_operation not in BOOLEAN_OPERATIONS:
        allowed = ", ".join(sorted(BOOLEAN_OPERATIONS))
        raise ValueError(
            f"Unsupported shape Boolean operation {operation!r}; use {allowed}"
        )
    source_id_list = _validate_source_ids(source_ids)
    _validate_output_id(output_id)
    style_overrides = _validate_style_overrides(style)

    source_path = Path(svg_file)
    try:
        root = ET.parse(source_path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Cannot parse SVG {source_path}: {exc}") from exc
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Shape Boolean source must have an SVG root: {source_path}")
    if any(_local_name(element.tag) == "style" for element in root.iter()):
        raise ValueError(
            "Shape Boolean does not resolve embedded CSS; use explicit SVG "
            "presentation attributes on the operands"
        )

    parents = {
        child: parent
        for parent in root.iter()
        for child in list(parent)
    }
    elements_by_id, duplicate_ids = _index_element_ids(root)
    selected: list[ET.Element] = []
    for source_id in source_id_list:
        if source_id in duplicate_ids:
            raise ValueError(
                f"Shape Boolean source id {source_id!r} is not unique"
            )
        element = elements_by_id.get(source_id)
        if element is None:
            raise ValueError(f"Shape Boolean source id not found: {source_id!r}")
        selected.append(element)

    pathops = _load_pathops()
    operands = [
        _element_to_pathops(element, parents, pathops)
        for element in selected
    ]
    inherited_style = _effective_style(selected[0], parents)
    inherited_style.update(style_overrides)

    if normalized_operation == "fragment":
        results = _fragment_paths(operands, pathops)
        fragments: list[str] = []
        for index, result in enumerate(results, start=1):
            result_id = f"{output_id}-{index}"
            _validate_result_id_collision(
                result_id,
                elements_by_id,
                source_id_list,
            )
            fragments.append(
                _serialize_result_path(
                    result,
                    result_id,
                    inherited_style,
                    pathops,
                )
            )
        return "\n".join(fragments)

    result = _merge_paths(normalized_operation, operands, pathops)
    if _path_is_empty(result):
        raise ValueError(
            f"Shape Boolean {normalized_operation} produced no filled area"
        )
    _validate_result_id_collision(output_id, elements_by_id, source_id_list)
    return _serialize_result_path(
        result,
        output_id,
        inherited_style,
        pathops,
    )


def _validate_source_ids(source_ids: Sequence[str]) -> list[str]:
    if isinstance(source_ids, (str, bytes)):
        raise ValueError("Shape Boolean source_ids must be a sequence of ids")
    values = list(source_ids)
    if len(values) < 2:
        raise ValueError("Shape Boolean requires at least two source ids")
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("Shape Boolean source ids must be non-empty strings")
    if len(set(values)) != len(values):
        raise ValueError("Shape Boolean source ids must be unique")
    return values


def _validate_output_id(output_id: str) -> None:
    if not isinstance(output_id, str) or _ID_RE.fullmatch(output_id) is None:
        raise ValueError(f"Invalid SVG output id: {output_id!r}")


def _validate_style_overrides(
    style: Mapping[str, str] | None,
) -> dict[str, str]:
    if style is None:
        return {}
    unknown = sorted(set(style) - set(_PRESENTATION_ATTRS))
    if unknown:
        raise ValueError(
            "Unsupported shape Boolean style override(s): "
            + ", ".join(unknown)
        )
    normalized: dict[str, str] = {}
    for name in _PRESENTATION_ATTRS:
        if name not in style:
            continue
        value = style[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Shape Boolean style override {name!r} must be a non-empty string"
            )
        normalized[name] = value.strip()
    return normalized


def _index_element_ids(
    root: ET.Element,
) -> tuple[dict[str, ET.Element], set[str]]:
    elements: dict[str, ET.Element] = {}
    duplicates: set[str] = set()
    for element in root.iter():
        element_id = element.get("id")
        if not element_id:
            continue
        if element_id in elements:
            duplicates.add(element_id)
        else:
            elements[element_id] = element
    return elements, duplicates


def _validate_result_id_collision(
    result_id: str,
    elements_by_id: Mapping[str, ET.Element],
    source_ids: Sequence[str],
) -> None:
    if result_id in elements_by_id and result_id not in source_ids:
        raise ValueError(
            f"Shape Boolean result id already exists outside the sources: "
            f"{result_id!r}"
        )


def _load_pathops() -> Any:
    try:
        import pathops
    except ImportError as exc:
        raise RuntimeError(
            "Shape Boolean operations require skia-pathops. Install the "
            "project requirements, or run: pip install skia-pathops"
        ) from exc
    required = (
        "FillType",
        "Path",
        "PathOp",
        "PathOpsError",
        "PathVerb",
        "op",
        "simplify",
    )
    missing = [name for name in required if not hasattr(pathops, name)]
    if missing:
        raise RuntimeError(
            "Installed skia-pathops is incompatible; missing: "
            + ", ".join(missing)
        )
    return pathops


def _element_to_pathops(
    element: ET.Element,
    parents: Mapping[ET.Element, ET.Element],
    pathops: Any,
) -> Any:
    chain = _element_chain(element, parents)
    _validate_source_location(element, chain)
    matrix = _combined_transform(chain)
    tag = _local_name(element.tag)

    if tag == "g":
        commands = _compact_preset_commands(element, matrix)
    elif tag in _BOOLEAN_TAGS:
        commands = _shape_commands(element)
        commands = transform_path_commands(commands, matrix)
    else:
        supported = ", ".join(sorted(_BOOLEAN_TAGS))
        raise ValueError(
            f"Shape Boolean source {_element_label(element)} must be a closed "
            f"{supported}, or a compact authored preset group"
        )

    result = _simplify_path(_commands_to_pathops(commands, pathops), pathops)
    if _path_is_empty(result):
        raise ValueError(
            f"Shape Boolean source {_element_label(element)} has no filled area"
        )
    return result


def _element_chain(
    element: ET.Element,
    parents: Mapping[ET.Element, ET.Element],
) -> list[ET.Element]:
    chain = [element]
    current = element
    while current in parents:
        current = parents[current]
        chain.append(current)
    chain.reverse()
    return chain


def _validate_source_location(
    element: ET.Element,
    chain: Sequence[ET.Element],
) -> None:
    definition_ancestor = next(
        (
            ancestor
            for ancestor in chain[:-1]
            if _local_name(ancestor.tag) in _DEFINITION_TAGS
        ),
        None,
    )
    if definition_ancestor is not None:
        raise ValueError(
            f"Shape Boolean source {_element_label(element)} is inside "
            f"<{_local_name(definition_ancestor.tag)}>"
        )
    nested_svg_count = sum(
        1 for ancestor in chain if _local_name(ancestor.tag) == "svg"
    )
    if nested_svg_count > 1:
        raise ValueError(
            f"Shape Boolean source {_element_label(element)} is inside a nested "
            "<svg>; materialize its viewport transform first"
        )
    for ancestor in chain[:-1]:
        if (
            _local_name(ancestor.tag) == "g"
            and authored_preset_encoding(ancestor) is not None
        ):
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} is inside an "
                "authored preset; select the preset group's id"
            )
    _validate_geometry_presentation(element, chain)


def _validate_geometry_presentation(
    element: ET.Element,
    chain: Sequence[ET.Element],
) -> None:
    fill_rule = "nonzero"
    for current in chain:
        if current.get("class") is not None:
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} uses class; "
                "materialize its computed presentation first"
            )
        transport_attrs = sorted(
            name
            for name in _ROUNDTRIP_TRANSPORT_ATTRS
            if current.get(name) is not None
        )
        if transport_attrs:
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} carries "
                "PPTX import/round-trip metadata "
                f"({', '.join(transport_attrs)}); author or materialize an "
                "ordinary SVG shape first"
            )
        inline = parse_inline_style(current.get("style"))
        inline_transform = inline.get("transform")
        if (
            inline_transform is not None
            and inline_transform.strip().lower() not in {"", "none"}
        ):
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} uses a CSS "
                "transform; write it as an SVG transform attribute first"
            )
        display = inline.get("display", current.get("display"))
        if display is not None and display.strip().lower() == "none":
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} is not "
                "displayed"
            )
        visibility = inline.get("visibility", current.get("visibility"))
        if visibility is not None and visibility.strip().lower() in {
            "collapse",
            "hidden",
        }:
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} is not visible"
            )
        for name in ("clip-path", "mask"):
            raw = inline.get(name, current.get(name))
            if raw is not None and raw.strip().lower() not in {"", "none"}:
                raise ValueError(
                    f"Shape Boolean source {_element_label(element)} uses "
                    f"{name}; materialize the visible contour first"
                )
        raw_filter = inline.get("filter", current.get("filter"))
        if raw_filter is not None and raw_filter.strip().lower() not in {
            "",
            "none",
        }:
            raise ValueError(
                f"Shape Boolean source {_element_label(element)} uses filter; "
                "reapply the effect after materializing the result"
            )
        raw_fill_rule = inline.get("fill-rule", current.get("fill-rule"))
        if (
            raw_fill_rule is not None
            and raw_fill_rule.strip().lower() != "inherit"
        ):
            fill_rule = raw_fill_rule.strip().lower()
    if fill_rule != "nonzero":
        raise ValueError(
            f"Shape Boolean source {_element_label(element)} uses "
            f"fill-rule={fill_rule!r}; use explicit nonzero contour direction"
        )


def _combined_transform(chain: Sequence[ET.Element]) -> AffineMatrix:
    matrix = IDENTITY_MATRIX
    for element in chain[1:]:
        transform = element.get("transform")
        if transform:
            matrix = matrix_multiply(
                matrix,
                parse_transform_matrix(transform),
            )
    return matrix


def _shape_commands(element: ET.Element) -> list[PathCommand]:
    tag = _local_name(element.tag)
    if tag == "path":
        raw_path = element.get("d")
        if raw_path is None:
            raise ValueError(f"{_element_label(element)} requires d")
        commands = normalize_path_commands(
            svg_path_to_absolute(parse_svg_path(raw_path))
        )
        _require_closed_commands(commands, _element_label(element))
        return commands

    if tag == "polygon":
        points = parse_svg_points(
            element.get("points", ""),
            min_points=3,
        )
        commands = [PathCommand("M", [*points[0]])]
        commands.extend(
            PathCommand("L", [x, y])
            for x, y in points[1:]
        )
        commands.append(PathCommand("Z", []))
        return commands

    if tag == "rect":
        return _rect_commands(element)

    if tag == "circle":
        cx = _geometry_value(element, "cx", default=0.0)
        cy = _geometry_value(element, "cy", default=0.0)
        radius = _geometry_value(element, "r", required=True)
        if radius <= 0:
            raise ValueError(f"{_element_label(element)} r must be greater than 0")
        return _ellipse_commands(cx, cy, radius, radius)

    if tag == "ellipse":
        cx = _geometry_value(element, "cx", default=0.0)
        cy = _geometry_value(element, "cy", default=0.0)
        radius_x = _geometry_value(element, "rx", required=True)
        radius_y = _geometry_value(element, "ry", required=True)
        if radius_x <= 0 or radius_y <= 0:
            raise ValueError(
                f"{_element_label(element)} rx and ry must be greater than 0"
            )
        return _ellipse_commands(cx, cy, radius_x, radius_y)

    raise AssertionError(f"Unhandled Boolean source tag: {tag}")


def _geometry_value(
    element: ET.Element,
    attribute: str,
    *,
    default: float | None = None,
    required: bool = False,
) -> float:
    raw = element.get(attribute)
    if raw is None:
        if required:
            raise ValueError(f"{_element_label(element)} requires {attribute}")
        if default is None:
            raise AssertionError("Geometry attribute requires a default")
        return default
    try:
        return parse_project_geometry_length(raw, attribute)
    except ValueError as exc:
        raise ValueError(
            f"{_element_label(element)} {attribute}: {exc}"
        ) from exc


def _rect_commands(element: ET.Element) -> list[PathCommand]:
    x = _geometry_value(element, "x", default=0.0)
    y = _geometry_value(element, "y", default=0.0)
    width = _geometry_value(element, "width", required=True)
    height = _geometry_value(element, "height", required=True)
    if width <= 0 or height <= 0:
        raise ValueError(
            f"{_element_label(element)} width and height must be greater than 0"
        )

    raw_rx = element.get("rx")
    raw_ry = element.get("ry")
    radius_x = (
        _geometry_value(element, "rx", required=True)
        if raw_rx is not None else 0.0
    )
    radius_y = (
        _geometry_value(element, "ry", required=True)
        if raw_ry is not None else 0.0
    )
    if raw_rx is not None and raw_ry is None:
        radius_y = radius_x
    elif raw_ry is not None and raw_rx is None:
        radius_x = radius_y
    if radius_x < 0 or radius_y < 0:
        raise ValueError(
            f"{_element_label(element)} rx and ry must not be negative"
        )

    radius_x = min(radius_x, width / 2.0)
    radius_y = min(radius_y, height / 2.0)
    if radius_x <= 0 or radius_y <= 0:
        return [
            PathCommand("M", [x, y]),
            PathCommand("L", [x + width, y]),
            PathCommand("L", [x + width, y + height]),
            PathCommand("L", [x, y + height]),
            PathCommand("Z", []),
        ]

    kx = radius_x * _BEZIER_QUARTER_K
    ky = radius_y * _BEZIER_QUARTER_K
    right = x + width
    bottom = y + height
    return [
        PathCommand("M", [x + radius_x, y]),
        PathCommand("L", [right - radius_x, y]),
        PathCommand(
            "C",
            [
                right - radius_x + kx,
                y,
                right,
                y + radius_y - ky,
                right,
                y + radius_y,
            ],
        ),
        PathCommand("L", [right, bottom - radius_y]),
        PathCommand(
            "C",
            [
                right,
                bottom - radius_y + ky,
                right - radius_x + kx,
                bottom,
                right - radius_x,
                bottom,
            ],
        ),
        PathCommand("L", [x + radius_x, bottom]),
        PathCommand(
            "C",
            [
                x + radius_x - kx,
                bottom,
                x,
                bottom - radius_y + ky,
                x,
                bottom - radius_y,
            ],
        ),
        PathCommand("L", [x, y + radius_y]),
        PathCommand(
            "C",
            [
                x,
                y + radius_y - ky,
                x + radius_x - kx,
                y,
                x + radius_x,
                y,
            ],
        ),
        PathCommand("Z", []),
    ]


def _ellipse_commands(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
) -> list[PathCommand]:
    kx = radius_x * _BEZIER_QUARTER_K
    ky = radius_y * _BEZIER_QUARTER_K
    return [
        PathCommand("M", [center_x + radius_x, center_y]),
        PathCommand(
            "C",
            [
                center_x + radius_x,
                center_y + ky,
                center_x + kx,
                center_y + radius_y,
                center_x,
                center_y + radius_y,
            ],
        ),
        PathCommand(
            "C",
            [
                center_x - kx,
                center_y + radius_y,
                center_x - radius_x,
                center_y + ky,
                center_x - radius_x,
                center_y,
            ],
        ),
        PathCommand(
            "C",
            [
                center_x - radius_x,
                center_y - ky,
                center_x - kx,
                center_y - radius_y,
                center_x,
                center_y - radius_y,
            ],
        ),
        PathCommand(
            "C",
            [
                center_x + kx,
                center_y - radius_y,
                center_x + radius_x,
                center_y - ky,
                center_x + radius_x,
                center_y,
            ],
        ),
        PathCommand("Z", []),
    ]


def _compact_preset_commands(
    group: ET.Element,
    matrix: AffineMatrix,
) -> list[PathCommand]:
    encoding = authored_preset_encoding(group)
    if encoding != "compact":
        raise ValueError(
            f"Shape Boolean source {_element_label(group)} must be a compact "
            "authored preset group"
        )
    errors = validate_authored_preset_group(group)
    if errors:
        raise ValueError(
            f"Invalid compact authored preset {_element_label(group)}: "
            + "; ".join(errors)
        )
    if group.get("data-pptx-object") != "shape":
        raise ValueError(
            f"Shape Boolean source {_element_label(group)} must be a shape, "
            "not a connector"
        )

    frame = tuple(
        float(value)
        for value in (group.get("data-pptx-frame") or "").split()
    )
    if len(frame) != 4:
        raise ValueError(
            f"Compact authored preset {_element_label(group)} has an invalid "
            "data-pptx-frame"
        )
    adjustments = {
        name[len("data-pptx-av-"):]: value
        for name, value in group.attrib.items()
        if name.startswith("data-pptx-av-")
    }
    rendered = render_preset_geometry(
        group.get("data-pptx-prst") or "",
        Xfrm(x=frame[0], y=frame[1], w=frame[2], h=frame[3]),
        adjustments,
    )
    children = list(group)
    if len(children) != len(rendered.paths):
        raise ValueError(
            f"Compact authored preset {_element_label(group)} layer count "
            "differs from its registry geometry"
        )

    commands: list[PathCommand] = []
    for child, layer in zip(children, rendered.paths):
        if layer.fill == "none":
            continue
        raw_path = child.get("d")
        if raw_path is None:
            raise ValueError(
                f"Compact authored preset {_element_label(group)} contains a "
                "path without d"
            )
        child_commands = normalize_path_commands(
            svg_path_to_absolute(parse_svg_path(raw_path))
        )
        child_commands = _close_filled_commands(
            child_commands,
            f"{_element_label(group)} preset layer",
        )
        commands.extend(transform_path_commands(child_commands, matrix))
    if not commands:
        raise ValueError(
            f"Compact authored preset {_element_label(group)} has no filled "
            "silhouette"
        )
    return commands


def _close_filled_commands(
    commands: Sequence[PathCommand],
    label: str,
) -> list[PathCommand]:
    closed: list[PathCommand] = []
    open_subpath = False
    drew_segment = False
    for command in commands:
        if command.cmd == "M":
            if open_subpath:
                if not drew_segment:
                    raise ValueError(f"{label} has an empty subpath")
                closed.append(PathCommand("Z", []))
            open_subpath = True
            drew_segment = False
        elif command.cmd in {"L", "C"}:
            if not open_subpath:
                raise ValueError(f"{label} draws before its first move")
            drew_segment = True
        elif command.cmd == "Z":
            if not open_subpath:
                raise ValueError(f"{label} closes without an open subpath")
            if not drew_segment:
                raise ValueError(f"{label} has an empty subpath")
            open_subpath = False
        closed.append(command)
    if open_subpath:
        if not drew_segment:
            raise ValueError(f"{label} has an empty subpath")
        closed.append(PathCommand("Z", []))
    if not closed:
        raise ValueError(f"{label} has no drawable contour")
    return closed


def _require_closed_commands(
    commands: Sequence[PathCommand],
    label: str,
) -> None:
    open_subpath = False
    drew_segment = False
    closed_contour = False
    for command in commands:
        if command.cmd == "M":
            if open_subpath:
                raise ValueError(f"{label} contains an open subpath")
            open_subpath = True
            drew_segment = False
        elif command.cmd in {"L", "C"}:
            if not open_subpath:
                raise ValueError(f"{label} draws before its first move")
            drew_segment = True
        elif command.cmd == "Z":
            if not open_subpath:
                raise ValueError(f"{label} closes without an open subpath")
            if not drew_segment:
                raise ValueError(f"{label} has an empty subpath")
            open_subpath = False
            closed_contour = True
    if open_subpath:
        raise ValueError(f"{label} contains an open subpath")
    if not closed_contour:
        raise ValueError(f"{label} has no drawable closed contour")


def _commands_to_pathops(
    commands: Sequence[PathCommand],
    pathops: Any,
) -> Any:
    result = pathops.Path(fillType=pathops.FillType.WINDING)
    for command in commands:
        args = command.args
        if command.cmd == "M":
            result.moveTo(args[0], args[1])
        elif command.cmd == "L":
            result.lineTo(args[0], args[1])
        elif command.cmd == "C":
            result.cubicTo(*args)
        elif command.cmd == "Z":
            result.close()
        else:
            raise AssertionError(
                f"Unexpected normalized path command: {command.cmd}"
            )
    return result


def _merge_paths(
    operation: str,
    operands: Sequence[Any],
    pathops: Any,
) -> Any:
    operator_by_name = {
        "combine": pathops.PathOp.XOR,
        "intersect": pathops.PathOp.INTERSECTION,
        "subtract": pathops.PathOp.DIFFERENCE,
        "union": pathops.PathOp.UNION,
    }
    operator = operator_by_name[operation]
    result = operands[0]
    for operand in operands[1:]:
        result = _path_op(result, operand, operator, pathops)
        if _path_is_empty(result) and operation in {"intersect", "subtract"}:
            break
    return result


def _path_op(
    first: Any,
    second: Any,
    operator: Any,
    pathops: Any,
) -> Any:
    try:
        return pathops.op(
            first,
            second,
            operator,
            fix_winding=True,
            keep_starting_points=False,
            clockwise=False,
        )
    except pathops.PathOpsError as exc:
        raise ValueError(f"Skia path Boolean operation failed: {exc}") from exc


def _simplify_path(path: Any, pathops: Any) -> Any:
    """Resolve winding and self-intersections before filled-area checks."""
    try:
        return pathops.simplify(
            path,
            fix_winding=True,
            keep_starting_points=False,
            clockwise=False,
        )
    except pathops.PathOpsError as exc:
        raise ValueError(f"Skia path simplification failed: {exc}") from exc


def _fragment_paths(
    operands: Sequence[Any],
    pathops: Any,
) -> list[Any]:
    pieces: list[Any] = []
    covered: Any | None = None
    for operand in operands:
        split_pieces: list[Any] = []
        for piece in pieces:
            difference = _path_op(
                piece,
                operand,
                pathops.PathOp.DIFFERENCE,
                pathops,
            )
            intersection = _path_op(
                piece,
                operand,
                pathops.PathOp.INTERSECTION,
                pathops,
            )
            if not _path_is_empty(difference):
                split_pieces.append(difference)
            if not _path_is_empty(intersection):
                split_pieces.append(intersection)

        unique = (
            operand
            if covered is None
            else _path_op(
                operand,
                covered,
                pathops.PathOp.DIFFERENCE,
                pathops,
            )
        )
        if not _path_is_empty(unique):
            split_pieces.append(unique)
        pieces = split_pieces
        covered = (
            operand
            if covered is None
            else _path_op(
                covered,
                operand,
                pathops.PathOp.UNION,
                pathops,
            )
        )

    components = [
        component
        for piece in pieces
        for component in _connected_components(piece, pathops)
        if not _path_is_empty(component)
    ]
    if not components:
        raise ValueError("Shape Boolean fragment produced no filled area")
    components.sort(key=_path_sort_key)
    return components


def _connected_components(path: Any, pathops: Any) -> list[Any]:
    contours = [
        contour
        for contour in path.contours
        if not _path_is_empty(contour)
    ]
    if len(contours) <= 1:
        return contours

    parents: list[int | None] = [None] * len(contours)
    for child_index, child in enumerate(contours):
        child_bounds = child.bounds
        child_points = child.firstPoints
        if child_bounds is None or not child_points:
            continue
        candidates: list[tuple[float, int]] = []
        for parent_index, candidate in enumerate(contours):
            if child_index == parent_index:
                continue
            candidate_bounds = candidate.bounds
            if candidate_bounds is None:
                continue
            if not _bounds_contain(candidate_bounds, child_bounds):
                continue
            if candidate.area <= child.area:
                continue
            if candidate.contains(child_points[0]):
                candidates.append((candidate.area, parent_index))
        if candidates:
            parents[child_index] = min(candidates)[1]

    depths = [
        _contour_depth(index, parents)
        for index in range(len(contours))
    ]
    components: list[Any] = []
    for index, contour in enumerate(contours):
        if depths[index] % 2:
            continue
        component = pathops.Path(fillType=pathops.FillType.WINDING)
        component.addPath(contour)
        for child_index, parent_index in enumerate(parents):
            if parent_index == index and depths[child_index] % 2:
                component.addPath(contours[child_index])
        components.append(component)
    return components


def _bounds_contain(
    outer: tuple[float, float, float, float],
    inner: tuple[float, float, float, float],
) -> bool:
    scale = max(
        *(abs(value) for value in outer),
        *(abs(value) for value in inner),
        1.0,
    )
    tolerance = scale * 1e-7
    return (
        outer[0] <= inner[0] + tolerance
        and outer[1] <= inner[1] + tolerance
        and outer[2] >= inner[2] - tolerance
        and outer[3] >= inner[3] - tolerance
    )


def _contour_depth(
    index: int,
    parents: Sequence[int | None],
) -> int:
    depth = 0
    seen = {index}
    parent = parents[index]
    while parent is not None:
        if parent in seen:
            raise ValueError("Shape Boolean fragment produced cyclic contours")
        seen.add(parent)
        depth += 1
        parent = parents[parent]
    return depth


def _path_is_empty(path: Any) -> bool:
    bounds = path.bounds
    if bounds is None or len(path) == 0:
        return True
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    scale = max(abs(width), abs(height), 1.0)
    return (
        width <= 0
        or height <= 0
        or not math.isfinite(path.area)
        or path.area <= scale * scale * 1e-12
    )


def _path_sort_key(
    path: Any,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    tuple[tuple[str, tuple[float, ...]], ...],
]:
    bounds = path.bounds
    signature = tuple(
        (
            str(verb),
            tuple(
                round(coordinate, _RESULT_PRECISION)
                for point in points
                for coordinate in point
            ),
        )
        for verb, points in path
    )
    if bounds is None:
        return (
            math.inf,
            math.inf,
            math.inf,
            math.inf,
            math.inf,
            signature,
        )
    return (
        round(bounds[1], _RESULT_PRECISION),
        round(bounds[0], _RESULT_PRECISION),
        round(bounds[3], _RESULT_PRECISION),
        round(bounds[2], _RESULT_PRECISION),
        round(path.area, _RESULT_PRECISION),
        signature,
    )


def _effective_style(
    element: ET.Element,
    parents: Mapping[ET.Element, ET.Element],
) -> dict[str, str]:
    values: dict[str, str] = {}
    opacity = 1.0
    parent_opacity = 1.0
    chain = _element_chain(element, parents)
    for index, current in enumerate(chain):
        inline = parse_inline_style(current.get("style"))
        raw_opacity = inline.get("opacity", current.get("opacity"))
        if raw_opacity is None:
            local_opacity = 1.0
        elif raw_opacity.strip() == "inherit":
            local_opacity = parent_opacity
        else:
            local_opacity = parse_opacity(raw_opacity)
        if index > 0:
            opacity *= local_opacity
        parent_opacity = local_opacity
        for name in _PRESENTATION_ATTRS:
            if name == "opacity":
                continue
            raw = inline.get(name, current.get(name))
            if raw is not None and raw.strip() != "inherit":
                values[name] = raw.strip()
    if opacity < 1.0:
        values["opacity"] = _format_number(opacity)
    return {
        name: values[name]
        for name in _PRESENTATION_ATTRS
        if name in values
    }


def _serialize_result_path(
    path: Any,
    result_id: str,
    style: Mapping[str, str],
    pathops: Any,
) -> str:
    path_data = _pathops_to_svg_path(path, pathops)
    attributes = {
        "id": result_id,
        "d": path_data,
        **style,
    }
    return f"<path{attrs_to_xml(attributes)}/>"


def _pathops_to_svg_path(path: Any, pathops: Any) -> str:
    path.convertConicsToQuads(0.05)
    parts: list[str] = []
    current: tuple[float, float] | None = None
    subpath_start: tuple[float, float] | None = None
    open_subpath = False

    for verb, points in path:
        if verb == pathops.PathVerb.MOVE:
            point = points[0]
            parts.append(
                f"M {_format_number(point[0])} {_format_number(point[1])}"
            )
            current = point
            subpath_start = point
            open_subpath = True
        elif verb == pathops.PathVerb.LINE:
            point = points[0]
            parts.append(
                f"L {_format_number(point[0])} {_format_number(point[1])}"
            )
            current = point
        elif verb == pathops.PathVerb.QUAD:
            if current is None:
                raise ValueError("Shape Boolean result quadratic has no start point")
            control, end = points
            control_1 = (
                current[0] + (control[0] - current[0]) * 2.0 / 3.0,
                current[1] + (control[1] - current[1]) * 2.0 / 3.0,
            )
            control_2 = (
                end[0] + (control[0] - end[0]) * 2.0 / 3.0,
                end[1] + (control[1] - end[1]) * 2.0 / 3.0,
            )
            parts.append(
                "C "
                f"{_format_point(control_1)} "
                f"{_format_point(control_2)} "
                f"{_format_point(end)}"
            )
            current = end
        elif verb == pathops.PathVerb.CUBIC:
            control_1, control_2, end = points
            parts.append(
                "C "
                f"{_format_point(control_1)} "
                f"{_format_point(control_2)} "
                f"{_format_point(end)}"
            )
            current = end
        elif verb == pathops.PathVerb.CLOSE:
            parts.append("Z")
            current = subpath_start
            open_subpath = False
        else:
            raise ValueError(f"Unsupported skia-pathops result verb: {verb}")

    if open_subpath:
        raise ValueError("Shape Boolean engine returned an open contour")
    if not parts:
        raise ValueError("Shape Boolean engine returned no path commands")
    return " ".join(parts)


def _format_point(point: tuple[float, float]) -> str:
    return f"{_format_number(point[0])} {_format_number(point[1])}"


def _format_number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("Shape Boolean result contains a non-finite coordinate")
    rounded = round(value, _RESULT_PRECISION)
    if abs(rounded) < 10 ** (-_RESULT_PRECISION):
        return "0"
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.{_RESULT_PRECISION}f}".rstrip("0").rstrip(".")


def _local_name(tag: object) -> str:
    raw = str(tag)
    return raw.rsplit("}", 1)[-1] if "}" in raw else raw


def _element_label(element: ET.Element) -> str:
    tag = _local_name(element.tag)
    element_id = element.get("id")
    return f"<{tag} id={element_id!r}>" if element_id else f"<{tag}>"
