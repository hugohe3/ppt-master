#!/usr/bin/env python3
"""
PPT Master - Preset Shape Registry

Expose the complete preset catalog and evaluate shape geometry instances.

Usage:
    Import get_preset_registry from pptx_shapes.registry.

Examples:
    geometry = get_preset_registry().evaluate("rightArrow", 320, 160)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Mapping

from .errors import (
    FormulaEvaluationError,
    PresetShapeDataError,
    UnknownPresetShapeError,
)
from .formula import FormulaEvaluator
from .loader import load_preset_shape_definitions, load_shape_type_values
from .models import (
    AdjustHandleDefinition,
    EvaluatedAdjustHandle,
    EvaluatedConnectionSite,
    EvaluatedPathCommand,
    EvaluatedPoint,
    EvaluatedPresetGeometry,
    EvaluatedShapePath,
    EvaluatedTextRectangle,
    PointExpression,
    PresetShapeDefinition,
    immutable_mapping,
)


AdjustmentValue = str | int | float
CONNECTOR_PRESET_TYPES = frozenset(
    {
        "line",
        "lineInv",
        "straightConnector1",
        "bentConnector2",
        "bentConnector3",
        "bentConnector4",
        "bentConnector5",
        "curvedConnector2",
        "curvedConnector3",
        "curvedConnector4",
        "curvedConnector5",
    }
)


class PresetShapeRegistry:
    """Read-only registry for all standard DrawingML preset geometries."""

    def __init__(
        self,
        definitions: tuple[PresetShapeDefinition, ...],
        expected_names: tuple[str, ...],
    ) -> None:
        self._definitions = {
            definition.name: definition for definition in definitions
        }
        self._names = tuple(expected_names)
        if len(self._definitions) != len(definitions):
            raise PresetShapeDataError("Preset registry contains duplicate names")
        missing = sorted(set(expected_names) - set(self._definitions))
        extra = sorted(set(self._definitions) - set(expected_names))
        if missing or extra:
            raise PresetShapeDataError(
                "Preset registry differs from ShapeTypeValues: "
                f"missing={missing}, extra={extra}"
            )

    @classmethod
    def bundled(cls) -> PresetShapeRegistry:
        """Load the hash-locked catalog shipped with PPT Master."""

        names = load_shape_type_values()
        definitions = load_preset_shape_definitions(expected_names=names)
        return cls(definitions, names)

    @property
    def names(self) -> tuple[str, ...]:
        """Return all names in official ``ShapeTypeValues`` order."""

        return self._names

    def __len__(self) -> int:
        return len(self._definitions)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._definitions

    def contains(self, name: str) -> bool:
        """Return whether ``name`` is a standard preset in this catalog."""

        return name in self._definitions

    def get(self, name: str) -> PresetShapeDefinition:
        """Return one immutable source definition or raise a precise error."""

        try:
            return self._definitions[name]
        except KeyError as exc:
            raise UnknownPresetShapeError(
                f"Unknown DrawingML preset shape: {name!r}"
            ) from exc

    def evaluate(
        self,
        name: str,
        width: float,
        height: float,
        *,
        adjustments: Mapping[str, AdjustmentValue] | None = None,
    ) -> EvaluatedPresetGeometry:
        """Evaluate every guide, handle, connection, text rect, and path."""

        definition = self.get(name)
        evaluator = FormulaEvaluator(width, height)
        supplied = dict(adjustments or {})
        adjustment_names = {guide.name for guide in definition.adjustments}
        unknown = sorted(set(supplied) - adjustment_names)
        if unknown:
            raise FormulaEvaluationError(
                f"Preset {name!r} has no adjustments named {unknown}"
            )

        evaluated_adjustments: dict[str, float] = {}
        for guide in definition.adjustments:
            source = supplied.get(guide.name, guide.formula)
            value = evaluator.evaluate_value(source)
            evaluated_adjustments[guide.name] = evaluator.bind(guide.name, value)

        evaluated_guides: dict[str, float] = {}
        for guide in definition.guides:
            value = evaluator.evaluate(guide.formula)
            evaluated_guides[guide.name] = evaluator.bind(guide.name, value)

        return EvaluatedPresetGeometry(
            name=name,
            width=evaluator.resolve("w"),
            height=evaluator.resolve("h"),
            left=evaluator.resolve("l"),
            top=evaluator.resolve("t"),
            adjustments=immutable_mapping(evaluated_adjustments),
            guides=immutable_mapping(evaluated_guides),
            handles=tuple(
                _evaluate_handle(handle, evaluator)
                for handle in definition.handles
            ),
            connections=tuple(
                EvaluatedConnectionSite(
                    angle=evaluator.evaluate_value(connection.angle),
                    position=_evaluate_point(connection.position, evaluator),
                )
                for connection in definition.connections
            ),
            text_rectangle=_evaluate_text_rectangle(definition, evaluator),
            paths=tuple(
                EvaluatedShapePath(
                    coordinate_width=_path_extent(
                        path.coordinate_width,
                        evaluator.resolve("w"),
                        evaluator,
                    ),
                    coordinate_height=_path_extent(
                        path.coordinate_height,
                        evaluator.resolve("h"),
                        evaluator,
                    ),
                    fill=path.fill,
                    stroke=path.stroke,
                    extrusion_ok=path.extrusion_ok,
                    commands=tuple(
                        EvaluatedPathCommand(
                            name=command.name,
                            parameters=tuple(
                                evaluator.evaluate_value(parameter)
                                for parameter in command.parameters
                            ),
                        )
                        for command in path.commands
                    ),
                )
                for path in definition.paths
            ),
        )


@lru_cache(maxsize=1)
def get_preset_registry() -> PresetShapeRegistry:
    """Return the process-wide, lazily loaded bundled registry."""

    return PresetShapeRegistry.bundled()


def _evaluate_point(
    point: PointExpression,
    evaluator: FormulaEvaluator,
) -> EvaluatedPoint:
    return EvaluatedPoint(
        x=evaluator.evaluate_value(point.x),
        y=evaluator.evaluate_value(point.y),
    )


def _evaluate_handle(
    handle: AdjustHandleDefinition,
    evaluator: FormulaEvaluator,
) -> EvaluatedAdjustHandle:
    return EvaluatedAdjustHandle(
        kind=handle.kind,
        position=_evaluate_point(handle.position, evaluator),
        x_reference=handle.x_reference,
        minimum_x=_optional_value(handle.minimum_x, evaluator),
        maximum_x=_optional_value(handle.maximum_x, evaluator),
        y_reference=handle.y_reference,
        minimum_y=_optional_value(handle.minimum_y, evaluator),
        maximum_y=_optional_value(handle.maximum_y, evaluator),
        angle_reference=handle.angle_reference,
        minimum_angle=_optional_value(handle.minimum_angle, evaluator),
        maximum_angle=_optional_value(handle.maximum_angle, evaluator),
        radius_reference=handle.radius_reference,
        minimum_radius=_optional_value(handle.minimum_radius, evaluator),
        maximum_radius=_optional_value(handle.maximum_radius, evaluator),
    )


def _evaluate_text_rectangle(
    definition: PresetShapeDefinition,
    evaluator: FormulaEvaluator,
) -> EvaluatedTextRectangle | None:
    rectangle = definition.text_rectangle
    if rectangle is None:
        return None
    return EvaluatedTextRectangle(
        left=evaluator.evaluate_value(rectangle.left),
        top=evaluator.evaluate_value(rectangle.top),
        right=evaluator.evaluate_value(rectangle.right),
        bottom=evaluator.evaluate_value(rectangle.bottom),
    )


def _optional_value(
    value: str | None,
    evaluator: FormulaEvaluator,
) -> float | None:
    return None if value is None else evaluator.evaluate_value(value)


def _path_extent(
    value: str | None,
    shape_extent: float,
    evaluator: FormulaEvaluator,
) -> float:
    if value is None:
        return shape_extent
    resolved = evaluator.evaluate_value(value)
    return shape_extent if resolved == 0 else resolved
