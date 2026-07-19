#!/usr/bin/env python3
"""
PPT Master - Authored Preset Shape Contract

Build and validate compact canonical SVG groups for newly authored PowerPoint
preset shapes while retaining expanded authored input compatibility.

Usage:
    Import render_preset_shape_fragment or validate_authored_preset_group.

Examples:
    fragment = render_preset_shape_fragment(
        "rightArrow",
        (80, 120, 240, 96),
        element_id="next-step",
        style={"fill": "#2563EB", "stroke": "none"},
    )

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import math
import re
from typing import Mapping
from xml.etree import ElementTree as ET

from pptx_shapes import (
    CONNECTOR_PRESET_TYPES,
    OOXML_COORDINATE_MAX,
    OOXML_COORDINATE_MIN,
    SUPPORTED_OPERATORS,
    get_preset_registry,
    resolve_preset_preview_hash,
    svg_preset_preview_fingerprint,
    validate_ooxml_line_width,
    validate_ooxml_xfrm,
)

from .emu_units import EMU_PER_PX, Xfrm, fmt_num
from .preset_registry_to_svg import render_preset_geometry
from .preset_svg_markup import (
    attrs_to_xml,
    serialize_compact_preset_layers,
    serialize_preset_layers,
)


AUTHORING_ATTR = "data-pptx-authoring"
AUTHORING_VALUE = "preset"
_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_ID_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]*")
_PAINT_RE = re.compile(r"(?:none|#[0-9A-Fa-f]{6})")
_INTEGER_RE = re.compile(r"[+-]?\d+")
_ADJUSTMENT_PREFIX = "data-pptx-av-"
_STYLE_ATTRS = (
    "fill",
    "fill-opacity",
    "stroke",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-opacity",
    "stroke-width",
)
_SEMANTIC_ATTRS = (
    AUTHORING_ATTR,
    "data-pptx-object",
    "data-pptx-prst",
    "data-pptx-frame",
)
_TEMPLATE_ATOM_ATTRS = (
    "data-pptx-layer",
    "data-pptx-editable",
    "data-pptx-carrier",
    "data-pptx-role",
)


def render_preset_shape_fragment(
    preset: str,
    frame: tuple[float, float, float, float],
    *,
    adjustments: Mapping[str, str | int | float] | None = None,
    object_kind: str = "shape",
    element_id: str,
    name: str | None = None,
    style: Mapping[str, str] | None = None,
) -> str:
    """Render one compact authored preset fragment for SVG insertion."""
    registry = get_preset_registry()
    if preset not in registry:
        raise ValueError(f"Unknown DrawingML preset shape: {preset!r}")
    if _ID_RE.fullmatch(element_id) is None:
        raise ValueError(f"Invalid SVG element id: {element_id!r}")
    if object_kind not in {"shape", "connector"}:
        raise ValueError("object_kind must be 'shape' or 'connector'")
    if preset in CONNECTOR_PRESET_TYPES and object_kind != "connector":
        raise ValueError(
            f"Connector preset {preset!r} requires object_kind='connector'"
        )
    if object_kind == "connector" and preset not in CONNECTOR_PRESET_TYPES:
        raise ValueError(
            f"Authored connector requires a connector preset, got {preset!r}"
        )

    x, y, width, height = _validate_frame(frame, object_kind)
    adjustment_values = _normalize_adjustments(adjustments or {})
    _validate_adjustments(preset, adjustment_values)
    registry.evaluate(
        preset,
        width,
        height,
        adjustments=adjustment_values,
    )
    rendered = render_preset_geometry(
        preset,
        Xfrm(x=x, y=y, w=width, h=height),
        adjustment_values,
    )
    if not rendered.paths:
        raise ValueError(f"Preset {preset!r} produced no visible SVG paths")

    frame_text = " ".join(
        fmt_num(value, 8) for value in (x, y, width, height)
    )
    semantic_attrs = {
        AUTHORING_ATTR: AUTHORING_VALUE,
        "data-pptx-object": object_kind,
        "data-pptx-prst": preset,
        "data-pptx-frame": frame_text,
    }
    if name:
        semantic_attrs["data-pptx-shape-name"] = name
    for guide_name, formula in adjustment_values.items():
        semantic_attrs[f"{_ADJUSTMENT_PREFIX}{guide_name}"] = str(formula)

    raw_style = dict(style or {})
    if "fill" not in raw_style or "stroke" not in raw_style:
        raise ValueError(
            "Compact authored preset requires explicit local fill and stroke"
        )
    style_attrs = _validate_style(raw_style)
    if (
        style_attrs.get("stroke", "none") != "none"
        and "stroke-width" not in style_attrs
    ):
        style_attrs["stroke-width"] = "1"
    if object_kind == "connector":
        if style_attrs.get("fill", "none") != "none":
            raise ValueError("Authored connector fill must be none")
        if not _has_visible_stroke(style_attrs):
            raise ValueError("Authored connector requires a visible stroke")
    group_attrs = {
        "id": element_id,
        **semantic_attrs,
        **style_attrs,
    }
    return (
        f'<g{attrs_to_xml(group_attrs)}>\n'
        f"{serialize_compact_preset_layers(rendered.paths, style_attrs)}\n"
        "</g>"
    )


def authored_preset_encoding(group: ET.Element) -> str | None:
    """Return ``compact`` / ``expanded`` for an authored preset group."""
    if (
        _local_name(group.tag) != "g"
        or group.get(AUTHORING_ATTR) != AUTHORING_VALUE
    ):
        return None
    parts = {
        child.get("data-pptx-part")
        for child in group
        if child.get("data-pptx-part") is not None
    }
    if parts:
        return "expanded"
    return "compact"


def validate_authored_preset_group(group: ET.Element) -> list[str]:
    """Return authored-preset contract errors for one logical group."""
    encoding = authored_preset_encoding(group)
    if encoding is None:
        return []
    if encoding == "compact":
        return _validate_compact_authored_preset_group(group)
    return _validate_expanded_authored_preset_group(group)


def _validate_compact_authored_preset_group(group: ET.Element) -> list[str]:
    """Validate the project-canonical compact authored-preset form."""
    errors: list[str] = []
    if not _is_svg_element(group, "g"):
        return [f'{AUTHORING_ATTR}="{AUTHORING_VALUE}" requires an SVG <g>']
    element_id = group.get("id")
    if element_id is None:
        errors.append("Authored preset logical group requires a stable id")
    elif _ID_RE.fullmatch(element_id) is None:
        errors.append(f"Authored preset logical group has invalid id {element_id!r}")

    unexpected_group_attrs = sorted(
        name for name in group.attrib
        if _is_unexpected_group_attr(name, compact=True)
    )
    if unexpected_group_attrs:
        errors.append(
            "Authored preset logical group has unsupported attributes: "
            + ", ".join(unexpected_group_attrs)
        )
    if group.get("data-pptx-preview-sha256") is not None:
        errors.append(
            "Compact authored preset derives preview integrity from the registry; "
            "remove data-pptx-preview-sha256"
        )
    if (group.text or "").strip():
        errors.append("Compact authored preset cannot contain text content")

    direct_children = list(group)
    if not direct_children:
        errors.append("Compact authored preset requires visible direct path layers")
        return errors
    if any(child.get("data-pptx-part") is not None for child in direct_children):
        errors.append(
            "Compact authored preset cannot mix transport carrier/preview markers"
        )
        return errors
    if any(
        not _is_svg_element(child, "path")
        for child in direct_children
    ):
        errors.append(
            "Compact authored preset is atomic and may contain only direct SVG paths"
        )
        return errors
    if any(list(child) for child in direct_children):
        errors.append("Compact authored preset paths cannot contain child elements")
    if any(
        (child.text or "").strip() or (child.tail or "").strip()
        for child in direct_children
    ):
        errors.append(
            "Compact authored preset paths may contain only whitespace around markup"
        )

    preset = group.get("data-pptx-prst") or ""
    object_kind = group.get("data-pptx-object") or ""
    if object_kind not in {"shape", "connector"}:
        errors.append(
            "Authored preset data-pptx-object must be 'shape' or 'connector'"
        )
    if preset in CONNECTOR_PRESET_TYPES and object_kind != "connector":
        errors.append(
            f"Connector preset {preset!r} requires data-pptx-object='connector'"
        )
    if object_kind == "connector" and preset not in CONNECTOR_PRESET_TYPES:
        errors.append(
            f"Authored connector requires a connector preset, got {preset!r}"
        )

    try:
        frame = _parse_frame(group.get("data-pptx-frame"), object_kind)
        canonical_frame = " ".join(fmt_num(value, 8) for value in frame)
        if group.get("data-pptx-frame") != canonical_frame:
            raise ValueError(
                "Compact authored preset data-pptx-frame must use the helper's "
                f"canonical spelling {canonical_frame!r}"
            )
        adjustments = {
            name[len(_ADJUSTMENT_PREFIX):]: value
            for name, value in group.attrib.items()
            if name.startswith(_ADJUSTMENT_PREFIX)
        }
        _validate_adjustments(preset, adjustments)
        rendered = render_preset_geometry(
            preset,
            Xfrm(x=frame[0], y=frame[1], w=frame[2], h=frame[3]),
            adjustments,
        )
        raw_style = {
            name: group.attrib[name]
            for name in _STYLE_ATTRS
            if name in group.attrib
        }
        if "fill" not in raw_style or "stroke" not in raw_style:
            raise ValueError(
                "Compact authored preset requires explicit local fill and stroke"
            )
        style_attrs = _validate_style(raw_style)
        noncanonical_style = sorted(
            name for name, value in style_attrs.items()
            if raw_style.get(name) != value
        )
        if noncanonical_style:
            raise ValueError(
                "Compact authored preset style uses non-canonical values: "
                + ", ".join(noncanonical_style)
            )
        if style_attrs.get("stroke", "none") != "none" and (
            "stroke-width" not in style_attrs
        ):
            raise ValueError(
                "Compact authored preset with a visible stroke requires stroke-width"
            )
        if object_kind == "connector":
            if style_attrs.get("fill", "none") != "none":
                raise ValueError("Authored connector fill must be none")
            if not _has_visible_stroke(style_attrs):
                raise ValueError("Authored connector requires a visible stroke")
        expected_markup = serialize_compact_preset_layers(
            rendered.paths,
            style_attrs,
        )
        expected_root = ET.fromstring(
            f'<g xmlns="http://www.w3.org/2000/svg">{expected_markup}</g>'
        )
    except (ET.ParseError, ValueError) as exc:
        errors.append(f"Cannot regenerate compact authored preset: {exc}")
        return errors

    expected_children = list(expected_root)
    if len(direct_children) != len(expected_children):
        errors.append(
            "Compact authored preset path count differs from registry output: "
            f"expected {len(expected_children)}, found {len(direct_children)}"
        )
        return errors
    for index, (actual, expected) in enumerate(
        zip(direct_children, expected_children),
        start=1,
    ):
        if actual.attrib != expected.attrib:
            errors.append(
                f"Compact authored preset path {index} differs from registry output"
            )
    return errors


def _validate_expanded_authored_preset_group(group: ET.Element) -> list[str]:
    """Validate the legacy expanded authored-preset compatibility form."""
    if group.get(AUTHORING_ATTR) != AUTHORING_VALUE:
        return []
    errors: list[str] = []
    if not _is_svg_element(group, "g"):
        return [f'{AUTHORING_ATTR}="{AUTHORING_VALUE}" requires an SVG <g>']
    element_id = group.get("id")
    if element_id is None:
        errors.append("Authored preset logical group requires a stable id")
    elif _ID_RE.fullmatch(element_id) is None:
        errors.append(f"Authored preset logical group has invalid id {element_id!r}")

    unexpected_group_attrs = sorted(
        name for name in group.attrib
        if _is_unexpected_group_attr(name, compact=False)
    )
    if unexpected_group_attrs:
        errors.append(
            "Authored preset logical group has unsupported attributes: "
            + ", ".join(unexpected_group_attrs)
        )

    direct_children = list(group)
    carriers = [
        child
        for child in direct_children
        if child.get("data-pptx-part") == "geometry"
    ]
    previews = [
        child
        for child in direct_children
        if child.get("data-pptx-part") == "geometry-preview"
    ]
    if len(carriers) != 1:
        errors.append(
            f"Authored preset requires exactly one direct geometry carrier; "
            f"found {len(carriers)}"
        )
    if len(previews) != 1:
        errors.append(
            f"Authored preset requires exactly one direct geometry preview; "
            f"found {len(previews)}"
        )
    allowed_children = set(carriers + previews)
    foreign_children = [
        child for child in direct_children
        if child not in allowed_children
    ]
    if foreign_children:
        errors.append(
            "Authored preset groups are atomic; place labels or decorations "
            "in a parent group"
        )
    if len(carriers) != 1 or len(previews) != 1:
        return errors

    carrier = carriers[0]
    preview = previews[0]
    if not _is_svg_element(carrier, "path"):
        errors.append("Authored preset geometry carrier must be an SVG <path>")
    if not _is_svg_element(preview, "g"):
        errors.append("Authored preset geometry preview must be an SVG <g>")
    if carrier.get("visibility") != "hidden":
        errors.append('Authored preset carrier requires visibility="hidden"')
    if carrier.get("pointer-events") != "none":
        errors.append('Authored preset carrier requires pointer-events="none"')

    for attr_name in _SEMANTIC_ATTRS:
        if group.get(attr_name) != carrier.get(attr_name):
            errors.append(
                f"Authored preset group/carrier {attr_name} values differ"
            )
    adjustment_names = {
        name
        for element in (group, carrier)
        for name in element.attrib
        if name.startswith(_ADJUSTMENT_PREFIX)
    }
    for attr_name in sorted(adjustment_names):
        if group.get(attr_name) != carrier.get(attr_name):
            errors.append(
                f"Authored preset group/carrier {attr_name} values differ"
            )

    unexpected_carrier_attrs = [
        name
        for name in carrier.attrib
        if _is_unexpected_carrier_attr(name)
    ]
    if unexpected_carrier_attrs:
        errors.append(
            "Authored preset carrier has unsupported presentation attributes: "
            + ", ".join(sorted(unexpected_carrier_attrs))
        )

    preset = carrier.get("data-pptx-prst") or ""
    object_kind = carrier.get("data-pptx-object") or ""
    if object_kind not in {"shape", "connector"}:
        errors.append(
            "Authored preset data-pptx-object must be 'shape' or 'connector'"
        )
    if preset in CONNECTOR_PRESET_TYPES and object_kind != "connector":
        errors.append(
            f"Connector preset {preset!r} requires data-pptx-object='connector'"
        )
    if object_kind == "connector" and preset not in CONNECTOR_PRESET_TYPES:
        errors.append(
            f"Authored connector requires a connector preset, got {preset!r}"
        )
    try:
        frame = _parse_frame(carrier.get("data-pptx-frame"), object_kind)
        adjustments = {
            name[len(_ADJUSTMENT_PREFIX):]: value
            for name, value in carrier.attrib.items()
            if name.startswith(_ADJUSTMENT_PREFIX)
        }
        _validate_adjustments(preset, adjustments)
        rendered = render_preset_geometry(
            preset,
            Xfrm(x=frame[0], y=frame[1], w=frame[2], h=frame[3]),
            adjustments,
        )
        style_attrs = _validate_style({
            name: carrier.attrib[name]
            for name in _STYLE_ATTRS
            if name in carrier.attrib
        })
        if object_kind == "connector":
            if style_attrs.get("fill", "none") != "none":
                raise ValueError("Authored connector fill must be none")
            if not _has_visible_stroke(style_attrs):
                raise ValueError("Authored connector requires a visible stroke")
        expected = serialize_preset_layers(
            rendered.paths,
            {
                name: value
                for name, value in carrier.attrib.items()
                if name in _SEMANTIC_ATTRS
                or name.startswith(_ADJUSTMENT_PREFIX)
                or name == "data-pptx-shape-name"
            },
            style_attrs,
        )
    except ValueError as exc:
        errors.append(f"Cannot regenerate authored preset preview: {exc}")
        return errors

    if (carrier.get("d") or "").strip() != _carrier_path(rendered.paths):
        errors.append("Authored preset carrier path differs from registry output")
    actual_preview_hash = svg_preset_preview_fingerprint(group)
    if actual_preview_hash != expected.preview_hash:
        errors.append("Authored preset visible preview differs from registry output")
    try:
        stored_hash = resolve_preset_preview_hash(group)
    except ValueError as exc:
        errors.append(f"Invalid authored preset preview fingerprint: {exc}")
    else:
        if stored_hash != expected.preview_hash:
            errors.append(
                "Authored preset fingerprint does not match regenerated metadata"
            )
    return errors


def validate_authored_preset_tree(root: ET.Element) -> list[str]:
    """Return structural errors for every authored preset marker in one SVG."""
    errors: list[str] = []
    id_counts: dict[str, int] = {}
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            id_counts[element_id] = id_counts.get(element_id, 0) + 1
    parents = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    for element in root.iter():
        authoring = element.get(AUTHORING_ATTR)
        if authoring is None:
            continue
        tag = _local_name(element.tag)
        label = _element_label(element)
        if authoring != AUTHORING_VALUE:
            errors.append(
                f"{label}: unsupported {AUTHORING_ATTR} value {authoring!r}"
            )
            continue
        if tag == "g":
            errors.extend(
                f"{label}: {error}"
                for error in validate_authored_preset_group(element)
            )
            element_id = element.get("id")
            if element_id and id_counts.get(element_id, 0) > 1:
                errors.append(
                    f"{label}: authored preset logical group id must be "
                    "globally unique"
                )
            continue
        if element.get("data-pptx-part") != "geometry":
            errors.append(
                f"{label}: authored preset metadata is allowed only on the "
                "logical group and its direct geometry carrier"
            )
            continue
        parent = parents.get(element)
        if (
            parent is None
            or not _is_svg_element(parent, "g")
            or parent.get(AUTHORING_ATTR) != AUTHORING_VALUE
        ):
            errors.append(
                f"{label}: authored preset geometry carrier must be a direct "
                "child of its authored logical group"
            )
    return errors


def materialize_compact_authored_preset_tree(root: ET.Element) -> int:
    """Expand validated compact authored presets in memory for conversion.

    Source SVG stays compact.  The converter reuses the established lossless
    carrier/preview path internally, so compact and expanded inputs share one
    DrawingML implementation.
    """
    materialized = 0
    for group in list(root.iter()):
        if authored_preset_encoding(group) != "compact":
            continue
        errors = _validate_compact_authored_preset_group(group)
        if errors:
            raise ValueError("; ".join(errors))

        preset = group.get("data-pptx-prst") or ""
        object_kind = group.get("data-pptx-object") or ""
        frame = _parse_frame(group.get("data-pptx-frame"), object_kind)
        adjustments = {
            name[len(_ADJUSTMENT_PREFIX):]: value
            for name, value in group.attrib.items()
            if name.startswith(_ADJUSTMENT_PREFIX)
        }
        rendered = render_preset_geometry(
            preset,
            Xfrm(x=frame[0], y=frame[1], w=frame[2], h=frame[3]),
            adjustments,
        )
        style_attrs = _validate_style({
            name: group.attrib[name]
            for name in _STYLE_ATTRS
            if name in group.attrib
        })
        semantic_attrs = {
            name: value
            for name, value in group.attrib.items()
            if name in _SEMANTIC_ATTRS
            or name.startswith(_ADJUSTMENT_PREFIX)
            or name == "data-pptx-shape-name"
        }
        markup = serialize_preset_layers(
            rendered.paths,
            semantic_attrs,
            style_attrs,
        )

        for name in _STYLE_ATTRS:
            group.attrib.pop(name, None)
        group.set("data-pptx-preview-sha256", markup.preview_hash)
        for child in list(group):
            group.remove(child)
        wrapper = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            f"{markup.markup}"
            "</svg>"
        )
        for child in list(wrapper):
            wrapper.remove(child)
            group.append(child)
        materialized += 1
    return materialized


def _validate_frame(
    frame: tuple[float, float, float, float],
    object_kind: str,
) -> tuple[float, float, float, float]:
    if len(frame) != 4:
        raise ValueError("frame must contain x, y, width, and height")
    values = tuple(float(value) for value in frame)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("frame values must be finite")
    width, height = values[2], values[3]
    if object_kind == "connector":
        if width < 0 or height < 0 or (width == 0 and height == 0):
            raise ValueError(
                "connector frame dimensions must be non-negative and not both zero"
            )
    elif width <= 0 or height <= 0:
        raise ValueError("shape frame width and height must be positive")
    validate_ooxml_xfrm(
        round(values[0] * EMU_PER_PX),
        round(values[1] * EMU_PER_PX),
        round(width * EMU_PER_PX),
        round(height * EMU_PER_PX),
    )
    return values


def _parse_frame(
    raw: str | None,
    object_kind: str,
) -> tuple[float, float, float, float]:
    if raw is None:
        raise ValueError("authored preset requires data-pptx-frame")
    parts = re.split(r"[\s,]+", raw.strip())
    if len(parts) != 4:
        raise ValueError("data-pptx-frame must contain four numbers")
    return _validate_frame(tuple(float(part) for part in parts), object_kind)


def _validate_style(style: Mapping[str, str]) -> dict[str, str]:
    unknown = sorted(set(style) - set(_STYLE_ATTRS))
    if unknown:
        raise ValueError(f"Unsupported authored preset style attributes: {unknown}")
    normalized = {name: str(value).strip() for name, value in style.items()}
    if not normalized:
        raise ValueError("Authored preset requires explicit fill and/or stroke")
    if normalized.get("fill", "none") == "none" and normalized.get(
        "stroke", "none"
    ) == "none":
        raise ValueError("Authored preset cannot have both fill and stroke set to none")
    for name in ("fill", "stroke"):
        value = normalized.get(name, "none")
        if _PAINT_RE.fullmatch(value) is None:
            raise ValueError(f"{name} must be none or a six-digit HEX color")
        normalized[name] = value.upper() if value != "none" else value
    if normalized.get("stroke", "none") == "none":
        unused_stroke_attrs = sorted(
            name for name in normalized
            if name.startswith("stroke-")
        )
        if unused_stroke_attrs:
            raise ValueError(
                "Stroke presentation attributes require a visible stroke: "
                + ", ".join(unused_stroke_attrs)
            )
    if normalized.get("stroke-linecap") not in {None, "butt", "round", "square"}:
        raise ValueError("stroke-linecap must be butt, round, or square")
    if normalized.get("stroke-linejoin") not in {None, "miter", "round", "bevel"}:
        raise ValueError("stroke-linejoin must be miter, round, or bevel")
    for name in ("fill-opacity", "stroke-opacity"):
        if name not in normalized:
            continue
        value = float(normalized[name])
        if not math.isfinite(value) or value < 0 or value > 1:
            raise ValueError(f"{name} must be between 0 and 1")
        normalized[name] = fmt_num(value, 6)
    if "stroke-width" in normalized:
        width = float(normalized["stroke-width"])
        if not math.isfinite(width) or width < 0:
            raise ValueError("stroke-width must be finite and non-negative")
        validate_ooxml_line_width(round(width * EMU_PER_PX))
        normalized["stroke-width"] = fmt_num(width, 6)
    if normalized.get("fill", "none") == "none" and "fill-opacity" in normalized:
        raise ValueError("fill-opacity requires a visible fill paint")
    if not _has_visible_fill(normalized) and not _has_visible_stroke(normalized):
        raise ValueError(
            "Authored preset requires at least one non-transparent visible paint"
        )
    return normalized


def _normalize_adjustments(
    adjustments: Mapping[str, str | int | float],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for name, value in adjustments.items():
        if isinstance(value, bool):
            raise ValueError(f"Adjustment {name!r} must not be boolean")
        if isinstance(value, int):
            formula = f"val {value}"
        elif isinstance(value, float):
            if not math.isfinite(value) or not value.is_integer():
                raise ValueError(
                    f"Numeric adjustment {name!r} must be a finite integer"
                )
            formula = f"val {int(value)}"
        else:
            formula = str(value).strip()
            if len(formula.split()) == 1:
                formula = f"val {formula}"
        normalized[str(name)] = formula
    return normalized


def _validate_adjustments(
    preset: str,
    adjustments: Mapping[str, str | int | float],
) -> None:
    registry = get_preset_registry()
    if preset not in registry:
        raise ValueError(f"Unknown DrawingML preset shape: {preset!r}")
    for name, formula in adjustments.items():
        if not isinstance(formula, str) or not formula.strip():
            raise ValueError(f"Adjustment {name!r} requires a formula")
        parts = formula.split()
        if parts[0] not in SUPPORTED_OPERATORS:
            raise ValueError(
                f"Adjustment {name!r} must use a DrawingML formula operator"
            )
        if parts[0] == "val" and len(parts) == 2:
            try:
                float(parts[1])
            except ValueError:
                pass
            else:
                if _INTEGER_RE.fullmatch(parts[1]) is None:
                    raise ValueError(
                        f"Adjustment {name!r} val operand must be an integer "
                        "coordinate"
                    )
    if not adjustments:
        return
    evaluated = registry.evaluate(
        preset,
        100000,
        100000,
        adjustments=adjustments,
    )
    for name, value in evaluated.adjustments.items():
        if name not in adjustments:
            continue
        if not OOXML_COORDINATE_MIN <= value <= OOXML_COORDINATE_MAX:
            raise ValueError(
                f"Adjustment {name!r} evaluates outside OOXML coordinate range"
            )


def _has_visible_fill(style: Mapping[str, str]) -> bool:
    return (
        style.get("fill", "none") != "none"
        and float(style.get("fill-opacity", "1")) > 0
    )


def _has_visible_stroke(style: Mapping[str, str]) -> bool:
    return (
        style.get("stroke", "none") != "none"
        and float(style.get("stroke-opacity", "1")) > 0
        and float(style.get("stroke-width", "1")) > 0
    )


def _is_unexpected_carrier_attr(name: str) -> bool:
    if name in {
        "d",
        "data-pptx-preview-sha256",
        "data-pptx-part",
        "data-pptx-shape-name",
        "visibility",
        "pointer-events",
        *_SEMANTIC_ATTRS,
        *_STYLE_ATTRS,
    }:
        return False
    return not name.startswith(_ADJUSTMENT_PREFIX)


def _is_unexpected_group_attr(name: str, *, compact: bool) -> bool:
    allowed = {
        "id",
        "transform",
        "data-pptx-preview-sha256",
        "data-pptx-shape-name",
        *_SEMANTIC_ATTRS,
    }
    if compact:
        allowed.update(_STYLE_ATTRS)
        allowed.update(_TEMPLATE_ATOM_ATTRS)
    if name in allowed:
        return False
    if name.startswith(_ADJUSTMENT_PREFIX):
        return False
    if name.startswith("data-pptx-runtime-") or name.startswith("aria-"):
        return False
    return name not in {"role", "tabindex"}


def _carrier_path(paths) -> str:
    return " ".join(path.d for path in paths).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _is_svg_element(element: ET.Element, local_name: str) -> bool:
    return element.tag in {
        local_name,
        f"{{{_SVG_NAMESPACE}}}{local_name}",
    }


def _element_label(element: ET.Element) -> str:
    tag = _local_name(element.tag)
    element_id = element.get("id")
    if element_id:
        return f'<{tag} id="{element_id}">'
    return f"<{tag}>"
