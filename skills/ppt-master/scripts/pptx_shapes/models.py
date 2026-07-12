#!/usr/bin/env python3
"""
PPT Master - PPTX Shape Models

Immutable value objects shared by the preset catalog loader and evaluator.

Usage:
    Import model classes from pptx_shapes.models.

Examples:
    from pptx_shapes.models import GuideDefinition

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class GuideDefinition:
    """One named DrawingML guide formula."""

    name: str
    formula: str


@dataclass(frozen=True)
class PointExpression:
    """A point whose coordinates are numeric literals or guide names."""

    x: str
    y: str


@dataclass(frozen=True)
class AdjustHandleDefinition:
    """An XY or polar adjustment handle from ``a:ahLst``."""

    kind: str
    position: PointExpression
    x_reference: str | None = None
    minimum_x: str | None = None
    maximum_x: str | None = None
    y_reference: str | None = None
    minimum_y: str | None = None
    maximum_y: str | None = None
    angle_reference: str | None = None
    minimum_angle: str | None = None
    maximum_angle: str | None = None
    radius_reference: str | None = None
    minimum_radius: str | None = None
    maximum_radius: str | None = None


@dataclass(frozen=True)
class ConnectionSiteDefinition:
    """One preset connection site before guide evaluation."""

    angle: str
    position: PointExpression


@dataclass(frozen=True)
class TextRectangleDefinition:
    """The preset's internal text rectangle expressions."""

    left: str
    top: str
    right: str
    bottom: str


@dataclass(frozen=True)
class PathCommandDefinition:
    """A DrawingML path command with parameters in document order.

    Parameter order is ``x,y`` for move/line, point order for Bezier commands,
    and ``wR,hR,stAng,swAng`` for arcs. ``close`` has no parameters.
    """

    name: str
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class ShapePathDefinition:
    """One path in a preset geometry definition."""

    coordinate_width: str | None
    coordinate_height: str | None
    fill: str
    stroke: bool
    extrusion_ok: bool
    commands: tuple[PathCommandDefinition, ...]


@dataclass(frozen=True)
class PresetShapeDefinition:
    """Complete immutable source definition for one preset shape."""

    name: str
    adjustments: tuple[GuideDefinition, ...]
    guides: tuple[GuideDefinition, ...]
    handles: tuple[AdjustHandleDefinition, ...]
    connections: tuple[ConnectionSiteDefinition, ...]
    text_rectangle: TextRectangleDefinition | None
    paths: tuple[ShapePathDefinition, ...]


@dataclass(frozen=True)
class EvaluatedPoint:
    """A point in the evaluated shape-local coordinate system."""

    x: float
    y: float


@dataclass(frozen=True)
class EvaluatedAdjustHandle:
    """An adjustment handle with resolved position and constraint bounds."""

    kind: str
    position: EvaluatedPoint
    x_reference: str | None = None
    minimum_x: float | None = None
    maximum_x: float | None = None
    y_reference: str | None = None
    minimum_y: float | None = None
    maximum_y: float | None = None
    angle_reference: str | None = None
    minimum_angle: float | None = None
    maximum_angle: float | None = None
    radius_reference: str | None = None
    minimum_radius: float | None = None
    maximum_radius: float | None = None


@dataclass(frozen=True)
class EvaluatedConnectionSite:
    """A connection site with resolved angle and position."""

    angle: float
    position: EvaluatedPoint


@dataclass(frozen=True)
class EvaluatedTextRectangle:
    """A resolved internal text rectangle."""

    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True)
class EvaluatedPathCommand:
    """A path command whose parameters have all been resolved to numbers."""

    name: str
    parameters: tuple[float, ...]


@dataclass(frozen=True)
class EvaluatedShapePath:
    """One resolved path and its DrawingML paint behavior."""

    coordinate_width: float
    coordinate_height: float
    fill: str
    stroke: bool
    extrusion_ok: bool
    commands: tuple[EvaluatedPathCommand, ...]


@dataclass(frozen=True)
class EvaluatedPresetGeometry:
    """All evaluated semantic geometry for one preset shape instance."""

    name: str
    width: float
    height: float
    left: float
    top: float
    adjustments: Mapping[str, float]
    guides: Mapping[str, float]
    handles: tuple[EvaluatedAdjustHandle, ...]
    connections: tuple[EvaluatedConnectionSite, ...]
    text_rectangle: EvaluatedTextRectangle | None
    paths: tuple[EvaluatedShapePath, ...]


def immutable_mapping(values: Mapping[str, float]) -> Mapping[str, float]:
    """Return a detached, read-only copy of a numeric mapping."""

    return MappingProxyType(dict(values))
