#!/usr/bin/env python3
"""
PPT Master - Preset Shape SVG Markup

Serialize evaluated DrawingML preset layers for lossless transport or compact
project authoring.

Usage:
    Import serialize_preset_layers from pptx_to_svg.preset_svg_markup.

Examples:
    markup = serialize_preset_layers(layers, semantic_attrs, style_attrs)

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence
from xml.etree import ElementTree as ET

from pptx_shapes import svg_preset_preview_fingerprint

from .preset_registry_to_svg import SvgPresetPath


@dataclass(frozen=True)
class PresetSvgMarkup:
    """Lossless hidden-carrier and visible-preview markup for one preset."""

    carrier: str
    preview: str
    preview_hash: str

    @property
    def markup(self) -> str:
        """Return the carrier and preview in canonical document order."""
        return f"{self.carrier}\n{self.preview}"


def serialize_preset_layers(
    layers: Sequence[SvgPresetPath],
    semantic_attrs: Mapping[str, str],
    style_attrs: Mapping[str, str],
) -> PresetSvgMarkup:
    """Serialize one preset without duplicating its native PowerPoint object."""
    detail_style_attrs = dict(style_attrs)
    preview_group_attrs = {"data-pptx-part": "geometry-preview"}
    for name in ("filter", "opacity"):
        value = detail_style_attrs.pop(name, None)
        if value is not None:
            preview_group_attrs[name] = value

    detail_layers: list[str] = []
    for layer in layers:
        attrs = dict(detail_style_attrs)
        apply_preset_path_fill(attrs, layer.fill)
        if not layer.stroke:
            remove_stroke_attrs(attrs)
            attrs["stroke"] = "none"
        attrs["data-pptx-part"] = "geometry-detail"
        detail_layers.append(
            f'<path d="{_xml_escape(layer.d)}"{attrs_to_xml(attrs)}/>'
        )

    preview = (
        f'<g{attrs_to_xml(preview_group_attrs)}>\n'
        + "\n".join(detail_layers)
        + "\n</g>"
    )
    preview_root = ET.fromstring(
        f'<svg xmlns="http://www.w3.org/2000/svg">{preview}</svg>'
    )
    preview_hash = svg_preset_preview_fingerprint(preview_root)
    carrier_attrs = {
        **style_attrs,
        **semantic_attrs,
        "data-pptx-preview-sha256": preview_hash,
        "data-pptx-part": "geometry",
        "visibility": "hidden",
        "pointer-events": "none",
    }
    combined_path = " ".join(layer.d for layer in layers)
    carrier = (
        f'<path d="{_xml_escape(combined_path)}"'
        f'{attrs_to_xml(carrier_attrs)}/>'
    )
    return PresetSvgMarkup(
        carrier=carrier,
        preview=preview,
        preview_hash=preview_hash,
    )


def serialize_compact_preset_layers(
    layers: Sequence[SvgPresetPath],
    style_attrs: Mapping[str, str],
) -> str:
    """Serialize visible preset layers without transport-only duplication.

    Base paint lives once on the logical authored group and is inherited by
    each path.  A path writes only the fill/stroke override required by its
    DrawingML layer.  The authored-preset validator regenerates this exact
    markup from the registry, so no serialized fingerprint is needed.
    """
    base_fill = style_attrs.get("fill", "none")
    base_stroke = style_attrs.get("stroke", "none")
    detail_layers: list[str] = []
    for layer in layers:
        attrs: dict[str, str] = {}
        if layer.fill == "none":
            if base_fill != "none":
                attrs["fill"] = "none"
        elif layer.fill != "norm":
            derived_fill = {"fill": base_fill}
            apply_preset_path_fill(derived_fill, layer.fill)
            if derived_fill.get("fill") != base_fill:
                attrs["fill"] = derived_fill["fill"]
        if not layer.stroke and base_stroke != "none":
            attrs["stroke"] = "none"
        detail_layers.append(
            f'<path d="{_xml_escape(layer.d)}"{attrs_to_xml(attrs)}/>'
        )
    return "\n".join(detail_layers)


def apply_preset_path_fill(attrs: dict[str, str], mode: str) -> None:
    """Apply one DrawingML path fill mode to SVG presentation attributes."""
    if mode == "none":
        attrs["fill"] = "none"
        attrs.pop("fill-opacity", None)
        return
    if mode == "norm":
        return
    color = attrs.get("fill", "")
    if not color.startswith("#") or len(color) != 7:
        return
    try:
        channels = tuple(
            int(color[offset:offset + 2], 16)
            for offset in (1, 3, 5)
        )
    except ValueError:
        return
    if mode in {"darken", "darkenLess"}:
        factor = 0.65 if mode == "darken" else 0.82
        adjusted = tuple(round(channel * factor) for channel in channels)
    elif mode in {"lighten", "lightenLess"}:
        amount = 0.4 if mode == "lighten" else 0.2
        adjusted = tuple(
            round(channel + (255 - channel) * amount)
            for channel in channels
        )
    else:
        return
    attrs["fill"] = "#" + "".join(
        f"{channel:02X}" for channel in adjusted
    )


def remove_stroke_attrs(attrs: dict[str, str]) -> None:
    """Remove inherited stroke and marker attributes from one path layer."""
    for name in tuple(attrs):
        if name.startswith("stroke") or name in {"marker-start", "marker-end"}:
            attrs.pop(name, None)


def attrs_to_xml(attrs: Mapping[str, str]) -> str:
    """Serialize SVG attributes in deterministic insertion order."""
    return "".join(
        f' {name}="{_xml_escape(value)}"'
        for name, value in attrs.items()
    )


def _xml_escape(value: str) -> str:
    text = str(value)
    if any(not _is_xml_10_character(character) for character in text):
        raise ValueError("SVG markup contains an XML 1.0-incompatible character")
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _is_xml_10_character(character: str) -> bool:
    codepoint = ord(character)
    return (
        codepoint in {0x09, 0x0A, 0x0D}
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )
