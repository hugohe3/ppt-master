#!/usr/bin/env python3
"""Shared diagnostic contract for unsupported imported object effects."""

from __future__ import annotations

from xml.etree import ElementTree as ET


EFFECT_STATUS_ATTR = "data-pptx-effect-status"
EFFECT_REASON_ATTR = "data-pptx-effect-reason"
UNSUPPORTED_EFFECT_STATUS = "unsupported"
_EFFECT_OBJECT_IDENTITY_ATTRS = (
    "data-pptx-object",
    "data-pptx-shape-id",
    "data-pptx-shape-scope",
)
_DML_NAMESPACE = "http://schemas.openxmlformats.org/drawingml/2006/main"
_TEXT_PROPERTY_TAGS = frozenset({
    f"{{{_DML_NAMESPACE}}}defRPr",
    f"{{{_DML_NAMESPACE}}}endParaRPr",
    f"{{{_DML_NAMESPACE}}}rPr",
})
_RUN_EFFECT_CONTAINER_TAGS = frozenset({
    f"{{{_DML_NAMESPACE}}}effectLst",
    f"{{{_DML_NAMESPACE}}}effectDag",
})


def project_effect_status_errors(root: ET.Element) -> list[str]:
    """Return blocking diagnostics for invalid or unsupported effect metadata."""
    errors: set[str] = set()
    parents = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    for elem in root.iter():
        raw_status = elem.get(EFFECT_STATUS_ATTR)
        raw_reason = elem.get(EFFECT_REASON_ATTR)
        if raw_status is None and raw_reason is None:
            continue
        parent = parents.get(elem)
        if (
            parent is not None
            and parent.get(EFFECT_STATUS_ATTR) == raw_status
            and parent.get(EFFECT_REASON_ATTR) == raw_reason
            and _same_source_object(parent, elem)
        ):
            # Import duplicates the marker on the logical object and carrier
            # so stripping either copy cannot erase the block. Report it once.
            continue
        label = _element_label(elem)
        status = (raw_status or "").strip()
        if status != UNSUPPORTED_EFFECT_STATUS:
            errors.add(
                f'{label} {EFFECT_STATUS_ATTR} must equal '
                f'{UNSUPPORTED_EFFECT_STATUS!r}; got {raw_status!r}'
            )
            continue
        reason = (raw_reason or "").strip()
        if not reason:
            errors.add(
                f'{label} {EFFECT_REASON_ATTR} requires a non-empty reason'
            )
            continue
        errors.add(f'{label} has unsupported source PPTX effect: {reason}')
    return sorted(errors)


def unsupported_effect_metadata(reason: str) -> dict[str, str]:
    """Build the canonical import-only marker for an unsupported effect."""
    reason = reason.strip()
    if not reason:
        raise ValueError("Unsupported PPTX effect reason must not be empty")
    return {
        EFFECT_STATUS_ATTR: UNSUPPORTED_EFFECT_STATUS,
        EFFECT_REASON_ATTR: reason,
    }


def txbody_has_run_effects(txbody: ET.Element | None) -> bool:
    """Return whether rebuilding a text body would discard a run effect."""
    if txbody is None:
        return False
    for properties in txbody.iter():
        if properties.tag not in _TEXT_PROPERTY_TAGS:
            continue
        for child in properties:
            if child.tag in _RUN_EFFECT_CONTAINER_TAGS and any(
                isinstance(effect.tag, str)
                for effect in child
            ):
                return True
    return False


def _element_label(elem: ET.Element) -> str:
    tag = elem.tag.rsplit("}", 1)[-1]
    elem_id = elem.get("id") or elem.get("data-name")
    if elem_id:
        return f'<{tag} id="{elem_id}">'
    shape_id = elem.get("data-pptx-shape-id")
    if shape_id:
        object_kind = elem.get("data-pptx-object") or "object"
        scope = elem.get("data-pptx-shape-scope") or "unknown"
        return (
            f'<{tag} data-pptx-object="{object_kind}" '
            f'data-pptx-shape-id="{shape_id}" '
            f'data-pptx-shape-scope="{scope}">'
        )
    return f"<{tag}>"


def _same_source_object(parent: ET.Element, child: ET.Element) -> bool:
    """Return whether a parent/child marker describes one imported object."""
    return all(
        child.get(attr) is not None
        and child.get(attr) == parent.get(attr)
        for attr in _EFFECT_OBJECT_IDENTITY_ATTRS
    )
