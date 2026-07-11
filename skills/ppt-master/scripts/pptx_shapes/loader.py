#!/usr/bin/env python3
"""
PPT Master - Preset Shape Data Loader

Load and validate the bundled DrawingML preset geometry catalog.

Usage:
    Import load_preset_shape_definitions from pptx_shapes.loader.

Examples:
    definitions = load_preset_shape_definitions()

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET

from .errors import PresetShapeDataError
from .models import (
    AdjustHandleDefinition,
    ConnectionSiteDefinition,
    GuideDefinition,
    PathCommandDefinition,
    PointExpression,
    PresetShapeDefinition,
    ShapePathDefinition,
    TextRectangleDefinition,
)


DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
EXPECTED_SHAPE_COUNT = 187
BUNDLED_DEFINITIONS_SHA256 = (
    "4a762444d8d85876881c02a5b1dedf6f73006fcd8acb7b4e393435615b37c780"
)
BUNDLED_SHAPE_TYPES_SHA256 = (
    "f2c3bdcda8569b358ce3196cfeb183849e33bfc7955fac961dc85fceb6b3b587"
)

_PACKAGE_DIR = Path(__file__).resolve().parent
BUNDLED_DEFINITIONS_PATH = _PACKAGE_DIR / "data" / "presetShapeDefinitions.xml"
BUNDLED_SHAPE_TYPES_PATH = _PACKAGE_DIR / "data" / "shape_type_values.txt"
_EXPECTED_ROOT_TAG = "presetShapeDefinitons"
_PATH_COMMAND_ARITY = {
    "moveTo": 1,
    "lnTo": 1,
    "quadBezTo": 2,
    "cubicBezTo": 3,
    "arcTo": 0,
    "close": 0,
}


def load_shape_type_values(path: Path | None = None) -> tuple[str, ...]:
    """Load the independent Open XML ``ShapeTypeValues`` coverage list."""

    source = path or BUNDLED_SHAPE_TYPES_PATH
    try:
        raw = source.read_bytes()
        names = tuple(
            line.strip()
            for line in raw.decode("utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    except (OSError, UnicodeDecodeError) as exc:
        raise PresetShapeDataError(
            f"Cannot read preset shape type catalog {source}: {exc}"
        ) from exc
    if path is None:
        actual = hashlib.sha256(_normalized_lf_bytes(raw)).hexdigest()
        if actual != BUNDLED_SHAPE_TYPES_SHA256:
            raise PresetShapeDataError(
                f"ShapeTypeValues checksum mismatch for {source}: "
                f"expected {BUNDLED_SHAPE_TYPES_SHA256}, found {actual}"
            )
    if len(names) != len(set(names)):
        raise PresetShapeDataError(f"Duplicate names in shape type catalog: {source}")
    if len(names) != EXPECTED_SHAPE_COUNT:
        raise PresetShapeDataError(
            f"Expected {EXPECTED_SHAPE_COUNT} ShapeTypeValues, found {len(names)}"
        )
    return names


def load_preset_shape_definitions(
    path: Path | None = None,
    *,
    expected_sha256: str | None = None,
    expected_names: tuple[str, ...] | None = None,
) -> tuple[PresetShapeDefinition, ...]:
    """Load one preset XML catalog and enforce uniqueness and coverage.

    The bundled catalog is hash-locked automatically. External catalogs are
    validated structurally and can opt into a caller-provided hash.
    """

    source = path or BUNDLED_DEFINITIONS_PATH
    locked_hash = (
        BUNDLED_DEFINITIONS_SHA256
        if path is None and expected_sha256 is None
        else expected_sha256
    )
    raw = _read_verified_bytes(source, locked_hash)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise PresetShapeDataError(f"Invalid preset geometry XML {source}: {exc}") from exc
    if _local_name(root.tag) != _EXPECTED_ROOT_TAG:
        raise PresetShapeDataError(
            f"Unexpected preset geometry root {_local_name(root.tag)!r} in {source}"
        )

    definitions = tuple(_parse_shape(element) for element in root)
    names = tuple(definition.name for definition in definitions)
    if len(names) != len(set(names)):
        raise PresetShapeDataError(f"Duplicate preset geometry names in {source}")

    catalog_names = expected_names
    if catalog_names is None and path is None:
        catalog_names = load_shape_type_values()
    if catalog_names is not None:
        missing = sorted(set(catalog_names) - set(names))
        extra = sorted(set(names) - set(catalog_names))
        if missing or extra:
            raise PresetShapeDataError(
                "Preset geometry coverage differs from ShapeTypeValues: "
                f"missing={missing}, extra={extra}"
            )
    return definitions


def _read_verified_bytes(path: Path, expected_sha256: str | None) -> bytes:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PresetShapeDataError(f"Cannot read preset geometry data {path}: {exc}") from exc
    if expected_sha256:
        actual = hashlib.sha256(_normalized_lf_bytes(raw)).hexdigest()
        if actual != expected_sha256:
            raise PresetShapeDataError(
                f"Preset geometry checksum mismatch for {path}: "
                f"expected {expected_sha256}, found {actual}"
            )
    return raw


def _normalized_lf_bytes(raw: bytes) -> bytes:
    """Normalize checkout line endings before verifying text-resource hashes."""

    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _parse_shape(element: ET.Element) -> PresetShapeDefinition:
    name = _local_name(element.tag)
    if not name:
        raise PresetShapeDataError("Preset shape name must not be empty")
    adjustments = _parse_guides(_find_child(element, "avLst"))
    guides = _parse_guides(_find_child(element, "gdLst"))
    handles = _parse_handles(_find_child(element, "ahLst"))
    connections = _parse_connections(_find_child(element, "cxnLst"))
    text_rectangle = _parse_text_rectangle(_find_child(element, "rect"))
    paths = _parse_paths(_find_child(element, "pathLst"), name)
    return PresetShapeDefinition(
        name=name,
        adjustments=adjustments,
        guides=guides,
        handles=handles,
        connections=connections,
        text_rectangle=text_rectangle,
        paths=paths,
    )


def _parse_guides(container: ET.Element | None) -> tuple[GuideDefinition, ...]:
    if container is None:
        return ()
    guides = []
    for element in container:
        if _local_name(element.tag) != "gd":
            raise PresetShapeDataError(
                f"Unexpected {_local_name(element.tag)!r} in guide list"
            )
        name = _required_attribute(element, "name")
        formula = _required_attribute(element, "fmla")
        guides.append(GuideDefinition(name=name, formula=formula))
    # Some normative preset definitions intentionally rebind an intermediate
    # name later in the ordered guide list. Preserve that sequential behavior.
    return tuple(guides)


def _parse_handles(
    container: ET.Element | None,
) -> tuple[AdjustHandleDefinition, ...]:
    if container is None:
        return ()
    handles = []
    for element in container:
        kind = _local_name(element.tag)
        if kind not in {"ahXY", "ahPolar"}:
            raise PresetShapeDataError(f"Unexpected adjustment handle: {kind!r}")
        position = _parse_position(element)
        handles.append(
            AdjustHandleDefinition(
                kind="xy" if kind == "ahXY" else "polar",
                position=position,
                x_reference=element.attrib.get("gdRefX"),
                minimum_x=element.attrib.get("minX"),
                maximum_x=element.attrib.get("maxX"),
                y_reference=element.attrib.get("gdRefY"),
                minimum_y=element.attrib.get("minY"),
                maximum_y=element.attrib.get("maxY"),
                angle_reference=element.attrib.get("gdRefAng"),
                minimum_angle=element.attrib.get("minAng"),
                maximum_angle=element.attrib.get("maxAng"),
                radius_reference=element.attrib.get("gdRefR"),
                minimum_radius=element.attrib.get("minR"),
                maximum_radius=element.attrib.get("maxR"),
            )
        )
    return tuple(handles)


def _parse_connections(
    container: ET.Element | None,
) -> tuple[ConnectionSiteDefinition, ...]:
    if container is None:
        return ()
    connections = []
    for element in container:
        if _local_name(element.tag) != "cxn":
            raise PresetShapeDataError(
                f"Unexpected connection-site element: {_local_name(element.tag)!r}"
            )
        connections.append(
            ConnectionSiteDefinition(
                angle=_required_attribute(element, "ang"),
                position=_parse_position(element),
            )
        )
    return tuple(connections)


def _parse_text_rectangle(
    element: ET.Element | None,
) -> TextRectangleDefinition | None:
    if element is None:
        return None
    return TextRectangleDefinition(
        left=_required_attribute(element, "l"),
        top=_required_attribute(element, "t"),
        right=_required_attribute(element, "r"),
        bottom=_required_attribute(element, "b"),
    )


def _parse_paths(
    container: ET.Element | None,
    shape_name: str,
) -> tuple[ShapePathDefinition, ...]:
    if container is None:
        raise PresetShapeDataError(f"Preset {shape_name!r} has no path list")
    paths = []
    for element in container:
        if _local_name(element.tag) != "path":
            raise PresetShapeDataError(
                f"Unexpected path-list element: {_local_name(element.tag)!r}"
            )
        paths.append(
            ShapePathDefinition(
                coordinate_width=element.attrib.get("w"),
                coordinate_height=element.attrib.get("h"),
                fill=element.attrib.get("fill", "norm"),
                stroke=_parse_boolean(element.attrib.get("stroke"), default=True),
                extrusion_ok=_parse_boolean(
                    element.attrib.get("extrusionOk"),
                    default=True,
                ),
                commands=tuple(_parse_path_command(command) for command in element),
            )
        )
    if not paths:
        raise PresetShapeDataError(f"Preset {shape_name!r} has an empty path list")
    return tuple(paths)


def _parse_path_command(element: ET.Element) -> PathCommandDefinition:
    name = _local_name(element.tag)
    expected_points = _PATH_COMMAND_ARITY.get(name)
    if expected_points is None:
        raise PresetShapeDataError(f"Unsupported preset path command: {name!r}")
    if name == "arcTo":
        parameters = tuple(
            _required_attribute(element, attribute)
            for attribute in ("wR", "hR", "stAng", "swAng")
        )
        return PathCommandDefinition(name=name, parameters=parameters)
    points = tuple(
        child for child in element if _local_name(child.tag) == "pt"
    )
    if len(points) != expected_points:
        raise PresetShapeDataError(
            f"Path command {name!r} expects {expected_points} points, "
            f"found {len(points)}"
        )
    parameters = tuple(
        coordinate
        for point in points
        for coordinate in (
            _required_attribute(point, "x"),
            _required_attribute(point, "y"),
        )
    )
    return PathCommandDefinition(name=name, parameters=parameters)


def _parse_position(parent: ET.Element) -> PointExpression:
    positions = [
        child for child in parent if _local_name(child.tag) == "pos"
    ]
    if len(positions) != 1:
        raise PresetShapeDataError(
            f"{_local_name(parent.tag)!r} must contain exactly one position"
        )
    return PointExpression(
        x=_required_attribute(positions[0], "x"),
        y=_required_attribute(positions[0], "y"),
    )


def _find_child(parent: ET.Element, local_name: str) -> ET.Element | None:
    matches = [child for child in parent if _local_name(child.tag) == local_name]
    if len(matches) > 1:
        raise PresetShapeDataError(
            f"Preset contains duplicate {local_name!r} elements"
        )
    return matches[0] if matches else None


def _required_attribute(element: ET.Element, name: str) -> str:
    value = element.attrib.get(name)
    if value is None or not value.strip():
        raise PresetShapeDataError(
            f"Element {_local_name(element.tag)!r} requires attribute {name!r}"
        )
    return value.strip()


def _parse_boolean(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    if value in {"true", "1"}:
        return True
    if value in {"false", "0"}:
        return False
    raise PresetShapeDataError(f"Invalid DrawingML boolean value: {value!r}")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
