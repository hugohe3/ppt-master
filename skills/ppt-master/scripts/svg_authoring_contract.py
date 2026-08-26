#!/usr/bin/env python3
"""Canonical compact SVG authoring contract.

The contract keeps authoring SVG as valid, readable XML.  It removes only
provably redundant inherited declarations and safely canonicalizes page-space
metadata; it never encodes geometry or invents semantic grouping.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from compact_svg_coordinates import (
    CoordinateCompactionStats,
    compact_svg_tree,
)
from compact_svg_styles import (
    INHERITABLE_ATTRIBUTES,
    StyleCompactionStats,
    compact_svg_style_tree,
    is_canonical_presentation_value,
)


_DEFINITION_SUBTREES = frozenset({
    "clipPath",
    "defs",
    "filter",
    "linearGradient",
    "marker",
    "mask",
    "pattern",
    "radialGradient",
    "symbol",
})
_ROOT_PAINT_ATTRIBUTES = frozenset({
    "clip-path",
    "color",
    "fill",
    "fill-opacity",
    "fill-rule",
    "marker-end",
    "marker-mid",
    "marker-start",
    "mask",
    "opacity",
    "paint-order",
    "filter",
    "stroke",
    "stroke-dasharray",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-opacity",
    "stroke-width",
})
_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_COORDINATE_ATTRIBUTES = frozenset({
    "data-pptx-bounds",
    "data-pptx-frame",
    "transform",
})


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


def _namespace(name: object) -> str | None:
    if not isinstance(name, str) or not name.startswith("{"):
        return None
    return name[1:].split("}", 1)[0]


def _style_names(value: str | None) -> set[str]:
    if not value:
        return set()
    names: set[str] = set()
    for declaration in value.split(";"):
        if ":" not in declaration:
            continue
        name, _raw_value = declaration.split(":", 1)
        normalized = name.strip().lower()
        if normalized:
            names.add(normalized)
    return names


def _style_value(value: str | None, name: str) -> str | None:
    if not value:
        return None
    resolved: str | None = None
    for declaration in value.split(";"):
        if ":" not in declaration:
            continue
        raw_name, raw_value = declaration.split(":", 1)
        if raw_name.strip().lower() == name:
            resolved = raw_value.strip().lower()
    return resolved


def _href_target(element: ET.Element) -> str | None:
    for name, value in element.attrib.items():
        if _local_name(name) == "href" and value.startswith("#"):
            return value[1:]
    return None


def _svg_namespace_errors(root: ET.Element) -> list[str]:
    errors: list[str] = []

    def visit(
        element: ET.Element,
        inside_metadata: bool,
        *,
        is_root: bool = False,
    ) -> None:
        if not isinstance(element.tag, str):
            return
        local = _local_name(element.tag)
        nested_metadata = inside_metadata or local == "metadata"
        if (
            not is_root
            and not inside_metadata
            and _namespace(element.tag) != _SVG_NAMESPACE
        ):
            errors.append(
                f"SVG element <{local}> exits the standard SVG namespace"
            )
        for child in element:
            visit(child, nested_metadata)

    visit(root, False, is_root=True)
    return errors


def _attribute_change_examples(
    before: ET.Element,
    after: ET.Element,
    *,
    coordinate_changes: bool,
    limit: int = 3,
) -> list[str]:
    examples: list[str] = []
    for index, (source, candidate) in enumerate(
        zip(before.iter(), after.iter()),
        start=1,
    ):
        if not isinstance(source.tag, str):
            continue
        names = sorted(set(source.attrib) | set(candidate.attrib))
        for name in names:
            is_coordinate = name in _COORDINATE_ATTRIBUTES
            if is_coordinate != coordinate_changes:
                continue
            old = source.get(name)
            new = candidate.get(name)
            if old == new:
                continue
            label = source.get("id") or f"{_local_name(source.tag)}[{index}]"
            examples.append(
                f"{label}:{name} {old!r} -> {new!r}"
            )
            if len(examples) == limit:
                return examples
    return examples


def _has_visible_text(root: ET.Element) -> bool:
    elements_by_id = {
        element_id: element
        for element in root.iter()
        if (element_id := element.get("id"))
    }

    def visit(
        element: ET.Element,
        *,
        inside_definition: bool,
        activated_reference: bool,
        display_hidden: bool,
        visibility: str,
        use_stack: frozenset[str],
    ) -> bool:
        local = _local_name(element.tag)
        display = _style_value(element.get("style"), "display")
        if display is None:
            display = (element.get("display") or "").strip().lower()
        nested_display_hidden = display_hidden or display == "none"

        own_visibility = _style_value(element.get("style"), "visibility")
        if own_visibility is None:
            own_visibility = (element.get("visibility") or "").strip().lower()
        nested_visibility = own_visibility or visibility

        nested_definition = inside_definition or (
            local in _DEFINITION_SUBTREES and not activated_reference
        )
        if (
            local == "text"
            and not nested_definition
            and not nested_display_hidden
            and nested_visibility not in {"hidden", "collapse"}
            and "".join(element.itertext()).strip()
        ):
            return True
        if local == "use" and not nested_display_hidden:
            target_id = _href_target(element)
            target = elements_by_id.get(target_id or "")
            if target is not None and target_id not in use_stack:
                if visit(
                    target,
                    inside_definition=False,
                    activated_reference=True,
                    display_hidden=False,
                    visibility=nested_visibility,
                    use_stack=use_stack | {target_id},
                ):
                    return True
        return any(
            visit(
                child,
                inside_definition=nested_definition,
                activated_reference=False,
                display_hidden=nested_display_hidden,
                visibility=nested_visibility,
                use_stack=use_stack,
            )
            for child in element
        )

    return visit(
        root,
        inside_definition=False,
        activated_reference=False,
        display_hidden=False,
        visibility="visible",
        use_stack=frozenset(),
    )


@dataclass
class AuthoringNormalizationStats:
    """Deterministic changes permitted before the first authoring write."""

    coordinates: CoordinateCompactionStats
    styles: StyleCompactionStats

    @property
    def changed_declarations(self) -> int:
        return (
            self.coordinates.changed_attributes
            + self.styles.changed_declarations
        )

    def as_dict(self) -> dict[str, dict[str, int] | int]:
        return {
            "coordinates": self.coordinates.as_dict(),
            "styles": self.styles.as_dict(),
            "changed_declarations": self.changed_declarations,
        }


def normalize_compact_authoring_tree(
    root: ET.Element,
    *,
    compact_native_frames: bool = True,
) -> AuthoringNormalizationStats:
    """Normalize one in-memory authoring tree without changing its semantics."""
    if _local_name(root.tag) != "svg":
        raise ValueError("Compact authoring requires an SVG root element")
    coordinates = compact_svg_tree(
        root,
        compact_native_frames=compact_native_frames,
    )
    styles = compact_svg_style_tree(root)
    return AuthoringNormalizationStats(
        coordinates=coordinates,
        styles=styles,
    )


def canonical_authoring_errors(
    root: ET.Element,
    *,
    compact_native_frames: bool = True,
) -> list[str]:
    """Return objective violations of the canonical compact authoring form."""
    if _local_name(root.tag) != "svg":
        return ["Canonical authoring requires an SVG root element"]

    errors: list[str] = []
    if _namespace(root.tag) != _SVG_NAMESPACE:
        errors.append(
            "Root SVG must use the standard http://www.w3.org/2000/svg "
            "namespace"
        )
    errors.extend(_svg_namespace_errors(root))

    style_elements = [
        element for element in root.iter()
        if _local_name(element.tag) == "style"
    ]
    if style_elements:
        errors.append(
            "Embedded <style> blocks are not canonical authoring; write "
            "supported values on the element or a meaningful ancestor"
        )
    class_elements = [
        element for element in root.iter()
        if element.get("class") is not None
    ]
    if class_elements:
        errors.append(
            "class selectors are not canonical authoring; keep explicit "
            "standard SVG presentation attributes"
        )

    unsafe_values = [
        (element.get("id") or _local_name(element.tag), name, value)
        for element in root.iter()
        for name in INHERITABLE_ATTRIBUTES
        if (value := element.get(name)) is not None
        and not is_canonical_presentation_value(
            value,
            property_name=name,
        )
    ]
    if unsafe_values:
        label, name, value = unsafe_values[0]
        errors.append(
            f"Element {label!r} has noncanonical {name}={value!r}; omit "
            "CSS-wide inheritance or resolve dynamic CSS before authoring"
        )

    root_style_names = _style_names(root.get("style"))
    root_paints = sorted(
        name
        for name in _ROOT_PAINT_ATTRIBUTES
        if root.get(name) is not None or name in root_style_names
    )
    if root_paints:
        errors.append(
            "Root SVG cannot declare shared paint values: "
            + ", ".join(root_paints)
            + "; put color and line defaults on meaningful groups"
        )

    for element in root.iter():
        if _local_name(element.tag) not in {"svg", "g"}:
            continue
        inherited_style_names = sorted(
            _style_names(element.get("style"))
            & set(INHERITABLE_ATTRIBUTES)
        )
        if inherited_style_names:
            label = element.get("id") or _local_name(element.tag)
            errors.append(
                f"Container {label!r} writes inherited defaults in inline "
                "style instead of presentation attributes: "
                + ", ".join(inherited_style_names)
            )

    if _has_visible_text(root) and not (root.get("font-family") or "").strip():
        errors.append(
            "Visible text requires one direct root font-family default; "
            "semantic groups and text elements keep only real overrides"
        )

    candidate = copy.deepcopy(root)
    stats = normalize_compact_authoring_tree(
        candidate,
        compact_native_frames=compact_native_frames,
    )
    if stats.styles.changed_declarations:
        examples = _attribute_change_examples(
            root,
            candidate,
            coordinate_changes=False,
        )
        errors.append(
            "Authoring SVG contains noncanonical or redundant inherited "
            f"style declarations ({stats.styles.changed_declarations} "
            "change(s)); examples: "
            + "; ".join(examples)
        )
    if stats.coordinates.changed_attributes:
        examples = _attribute_change_examples(
            root,
            candidate,
            coordinate_changes=True,
        )
        errors.append(
            "Authoring SVG contains safely compactable page-space metadata "
            f"({stats.coordinates.changed_attributes} attribute(s)); examples: "
            + "; ".join(examples)
        )
    return errors
