#!/usr/bin/env python3
"""
PPT Master - Template Structure Metadata

Parse and validate explicit SVG metadata consumed by template-mode PPTX export.

Usage:
    Imported by svg_to_pptx.pptx_package.builder and svg_quality_checker.py.

Examples:
    parse_template_slides([Path("projects/demo/svg_output/01_cover.svg")])

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


_NON_VISUAL_TAGS = frozenset({"defs", "title", "desc", "metadata", "style"})
_STRUCTURE_ATTRS = frozenset({
    "data-pptx-layer",
    "data-pptx-layout",
    "data-pptx-layout-name",
    "data-pptx-placeholder",
    "data-pptx-placeholder-bounds",
    "data-pptx-editable",
})
_LAYERS = frozenset({"master", "layout"})
_PLACEHOLDERS = frozenset({
    "title",
    "body",
    "picture",
    "chart",
    "table",
    "footer",
    "slide-number",
})
_TEXT_PLACEHOLDERS = frozenset({"title", "body", "footer", "slide-number"})
_LAYOUT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class TemplateStructureError(RuntimeError):
    """Reject invalid or ambiguous template-structure metadata."""


@dataclass(frozen=True)
class TemplateElementSpec:
    """One direct SVG child carrying explicit PPTX structure metadata."""

    element_id: str
    order: int
    tag: str
    layer: str | None = None
    placeholder: str | None = None
    placeholder_bounds: tuple[float, float, float, float] | None = None

    def contract_signature(self) -> tuple[object, ...]:
        """Return metadata that must agree across slides sharing a structure."""
        return (
            self.element_id,
            self.tag,
            self.layer,
            self.placeholder,
            self.placeholder_bounds,
        )


@dataclass(frozen=True)
class TemplateSlideSpec:
    """Explicit structure contract parsed from one SVG slide."""

    slide_num: int
    svg_path: Path
    layout_key: str
    layout_name: str
    elements: tuple[TemplateElementSpec, ...]

    @property
    def master_elements(self) -> tuple[TemplateElementSpec, ...]:
        return tuple(item for item in self.elements if item.layer == "master")

    @property
    def layout_elements(self) -> tuple[TemplateElementSpec, ...]:
        return tuple(item for item in self.elements if item.layer == "layout")

    @property
    def placeholders(self) -> tuple[TemplateElementSpec, ...]:
        return tuple(item for item in self.elements if item.placeholder)

    @property
    def layout_contract(self) -> tuple[tuple[object, ...], ...]:
        return tuple(
            item.contract_signature()
            for item in self.elements
            if item.layer == "layout" or item.placeholder
        )


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if isinstance(elem.tag, str) else ""


def _parse_placeholder_bounds(
    raw: str | None,
    *,
    svg_path: Path,
    element_id: str,
) -> tuple[float, float, float, float] | None:
    if raw is None:
        return None
    parts = [part for part in re.split(r"[\s,]+", raw.strip()) if part]
    if len(parts) != 4:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} data-pptx-placeholder-bounds must be "
            "'x y width height'"
        )
    try:
        x, y, width, height = (float(part) for part in parts)
    except ValueError as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder bounds must be numeric"
        ) from exc
    if not all(math.isfinite(value) for value in (x, y, width, height)):
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder bounds must be finite"
        )
    if width <= 0 or height <= 0:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder width/height must be positive"
        )
    return x, y, width, height


def _validate_placeholder_element(
    elem: ET.Element,
    placeholder: str,
    *,
    svg_path: Path,
    element_id: str,
) -> None:
    tag = _local_tag(elem)
    if placeholder in _TEXT_PLACEHOLDERS and tag != "text":
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder '{placeholder}' must be "
            "declared on a direct <text> element"
        )
    if placeholder == "picture" and tag not in {"image", "svg"}:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} picture placeholder must be declared "
            "on a direct <image> or nested crop <svg> element"
        )
    if placeholder in {"chart", "table"}:
        native_kind = (elem.get("data-pptx-native") or "").strip().lower()
        if tag != "g" or native_kind != placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id} placeholder '{placeholder}' must be "
                f"a direct <g data-pptx-native=\"{placeholder}\"> marker"
            )


def parse_template_slide(svg_path: Path, slide_num: int) -> TemplateSlideSpec:
    """Parse one SVG's explicit template layout and structure elements."""
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: unable to parse SVG structure metadata: {exc}"
        ) from exc

    if _local_tag(root) != "svg":
        raise TemplateStructureError(f"{svg_path.name}: root element must be <svg>")

    layout_key = (root.get("data-pptx-layout") or "").strip()
    if not layout_key:
        raise TemplateStructureError(
            f"{svg_path.name}: template export requires root data-pptx-layout"
        )
    if not _LAYOUT_KEY_RE.fullmatch(layout_key):
        raise TemplateStructureError(
            f"{svg_path.name}: invalid data-pptx-layout {layout_key!r}; use 1-64 "
            "ASCII letters, digits, dots, underscores, or hyphens"
        )
    layout_name = (root.get("data-pptx-layout-name") or "").strip()
    if not layout_name:
        layout_name = re.sub(r"[-_.]+", " ", layout_key).strip().title() or layout_key

    illegal_root_attrs = sorted(
        attr for attr in _STRUCTURE_ATTRS
        if (
            attr not in {"data-pptx-layout", "data-pptx-layout-name"}
            and root.get(attr) is not None
        )
    )
    if illegal_root_attrs:
        raise TemplateStructureError(
            f"{svg_path.name}: root <svg> cannot use {', '.join(illegal_root_attrs)}"
        )

    id_counts: dict[str, int] = {}
    for elem in root.iter():
        element_id = elem.get("id")
        if element_id:
            id_counts[element_id] = id_counts.get(element_id, 0) + 1
    duplicate_ids = sorted(element_id for element_id, count in id_counts.items() if count > 1)
    if duplicate_ids:
        raise TemplateStructureError(
            f"{svg_path.name}: duplicate SVG id(s) are not allowed in template mode: "
            + ", ".join(duplicate_ids)
        )

    direct_children = set(root)
    for elem in root.iter():
        if elem is root or elem in direct_children:
            continue
        nested_attrs = sorted(attr for attr in _STRUCTURE_ATTRS if elem.get(attr) is not None)
        if nested_attrs:
            element_id = elem.get("id") or _local_tag(elem) or "<unnamed>"
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id} uses template metadata below the SVG "
                "root; structure metadata is allowed only on direct children"
            )

    elements: list[TemplateElementSpec] = []
    phase = "master"
    visual_order = 0
    for elem in root:
        tag = _local_tag(elem)
        if tag in _NON_VISUAL_TAGS:
            continue

        element_id = (elem.get("id") or "").strip()
        layer_raw = elem.get("data-pptx-layer")
        layer = (layer_raw or "").strip().lower() or None
        placeholder_raw = elem.get("data-pptx-placeholder")
        placeholder = (
            (placeholder_raw or "").strip().lower() or None
        )
        bounds_raw = elem.get("data-pptx-placeholder-bounds")
        editable_raw = elem.get("data-pptx-editable")

        if (
            elem.get("data-pptx-layout") is not None
            or elem.get("data-pptx-layout-name") is not None
        ):
            raise TemplateStructureError(
                f"{svg_path.name}: data-pptx-layout and data-pptx-layout-name belong "
                "on the root <svg> only"
            )
        if layer and layer not in _LAYERS:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has unsupported "
                f"data-pptx-layer={layer!r}"
            )
        if layer_raw is not None and layer is None:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has empty data-pptx-layer"
            )
        if placeholder and placeholder not in _PLACEHOLDERS:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has unsupported "
                f"data-pptx-placeholder={placeholder!r}"
            )
        if placeholder_raw is not None and placeholder is None:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has empty "
                "data-pptx-placeholder"
            )
        if layer and placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} cannot be both a static "
                "master/layout layer and a content placeholder"
            )
        if bounds_raw is not None and not placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has placeholder bounds without "
                "data-pptx-placeholder"
            )
        if (layer or placeholder) and not element_id:
            raise TemplateStructureError(
                f"{svg_path.name}: direct <{tag}> with template metadata requires an id"
            )
        if editable_raw is not None:
            if not layer or editable_raw.strip().lower() != "false":
                raise TemplateStructureError(
                    f"{svg_path.name}: data-pptx-editable currently supports only "
                    "'false' on master/layout layer elements"
                )

        if layer == "master":
            if phase != "master":
                raise TemplateStructureError(
                    f"{svg_path.name}: master layer element {element_id} must precede "
                    "all layout and slide-local content"
                )
        elif layer == "layout":
            if phase == "slide":
                raise TemplateStructureError(
                    f"{svg_path.name}: layout layer element {element_id} must precede "
                    "all slide-local content"
                )
            phase = "layout"
        else:
            phase = "slide"

        if placeholder:
            _validate_placeholder_element(
                elem,
                placeholder,
                svg_path=svg_path,
                element_id=element_id,
            )
        placeholder_bounds = _parse_placeholder_bounds(
            bounds_raw,
            svg_path=svg_path,
            element_id=element_id or tag,
        )

        if layer or placeholder:
            elements.append(TemplateElementSpec(
                element_id=element_id,
                order=visual_order,
                tag=tag,
                layer=layer,
                placeholder=placeholder,
                placeholder_bounds=placeholder_bounds,
            ))
        visual_order += 1

    return TemplateSlideSpec(
        slide_num=slide_num,
        svg_path=svg_path,
        layout_key=layout_key,
        layout_name=layout_name,
        elements=tuple(elements),
    )


def parse_template_slides(svg_files: list[Path]) -> list[TemplateSlideSpec]:
    """Parse a deck and enforce cross-slide master/layout contracts."""
    specs = [
        parse_template_slide(svg_path, slide_num)
        for slide_num, svg_path in enumerate(svg_files, start=1)
    ]
    if not specs:
        raise TemplateStructureError("Template export requires at least one SVG slide")

    expected_master = tuple(
        item.contract_signature() for item in specs[0].master_elements
    )
    for spec in specs[1:]:
        actual_master = tuple(
            item.contract_signature() for item in spec.master_elements
        )
        if actual_master != expected_master:
            raise TemplateStructureError(
                f"{spec.svg_path.name}: master layer contract differs from "
                f"{specs[0].svg_path.name}; every template slide must repeat the same "
                "explicit master elements in the same order"
            )

    by_layout: dict[str, list[TemplateSlideSpec]] = {}
    for spec in specs:
        by_layout.setdefault(spec.layout_key, []).append(spec)
    for layout_key, layout_specs in by_layout.items():
        prototype = layout_specs[0]
        for spec in layout_specs[1:]:
            if spec.layout_name != prototype.layout_name:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: layout {layout_key!r} uses name "
                    f"{spec.layout_name!r}, expected {prototype.layout_name!r}"
                )
            if spec.layout_contract != prototype.layout_contract:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: layout {layout_key!r} structure differs "
                    f"from prototype {prototype.svg_path.name}; repeat the same layout "
                    "layers and placeholder ids/types in the same order"
                )
    return specs


def validate_template_svg(svg_path: Path) -> list[str]:
    """Return per-file template metadata errors for quality-check integration."""
    try:
        parse_template_slide(svg_path, 1)
    except TemplateStructureError as exc:
        return [str(exc)]
    return []
