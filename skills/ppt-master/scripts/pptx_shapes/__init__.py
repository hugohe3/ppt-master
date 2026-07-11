#!/usr/bin/env python3
"""
PPT Master - DrawingML Preset Shapes

Shared full-catalog loader, registry, and formula evaluator for PPTX shapes.

Usage:
    Import get_preset_registry from pptx_shapes.

Examples:
    from pptx_shapes import get_preset_registry
    arrow = get_preset_registry().evaluate("rightArrow", 320, 160)

Dependencies:
    None (only uses standard library)
"""

from .errors import (
    FormulaEvaluationError,
    FormulaSyntaxError,
    PresetShapeDataError,
    PresetShapeError,
    UnknownGuideError,
    UnknownPresetShapeError,
)
from .formula import (
    FULL_CIRCLE,
    OOXML_DEGREE,
    SUPPORTED_OPERATORS,
    FormulaEvaluator,
    build_builtin_guides,
    evaluate_formula,
)
from .loader import (
    BUNDLED_DEFINITIONS_PATH,
    BUNDLED_DEFINITIONS_SHA256,
    BUNDLED_SHAPE_TYPES_PATH,
    BUNDLED_SHAPE_TYPES_SHA256,
    DRAWINGML_NS,
    EXPECTED_SHAPE_COUNT,
    load_preset_shape_definitions,
    load_shape_type_values,
)
from .models import (
    EvaluatedPresetGeometry,
    PresetShapeDefinition,
)
from .registry import (
    CONNECTOR_PRESET_TYPES,
    PresetShapeRegistry,
    get_preset_registry,
)
from .semantic_hash import (
    resolve_preset_preview_hash,
    svg_preset_preview_fingerprint,
    svg_text_fingerprint,
)
from .xml_safety import RELATIONSHIPS_NS, has_relationship_attributes


__all__ = [
    "BUNDLED_DEFINITIONS_PATH",
    "BUNDLED_DEFINITIONS_SHA256",
    "BUNDLED_SHAPE_TYPES_PATH",
    "BUNDLED_SHAPE_TYPES_SHA256",
    "CONNECTOR_PRESET_TYPES",
    "DRAWINGML_NS",
    "EXPECTED_SHAPE_COUNT",
    "FULL_CIRCLE",
    "OOXML_DEGREE",
    "SUPPORTED_OPERATORS",
    "EvaluatedPresetGeometry",
    "FormulaEvaluationError",
    "FormulaEvaluator",
    "FormulaSyntaxError",
    "PresetShapeDataError",
    "PresetShapeDefinition",
    "PresetShapeError",
    "PresetShapeRegistry",
    "RELATIONSHIPS_NS",
    "UnknownGuideError",
    "UnknownPresetShapeError",
    "build_builtin_guides",
    "evaluate_formula",
    "get_preset_registry",
    "has_relationship_attributes",
    "load_preset_shape_definitions",
    "load_shape_type_values",
    "resolve_preset_preview_hash",
    "svg_text_fingerprint",
    "svg_preset_preview_fingerprint",
]
