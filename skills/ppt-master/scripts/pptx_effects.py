#!/usr/bin/env python3
"""Shared diagnostic contract for unsupported imported object effects."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from xml.etree import ElementTree as ET


EFFECT_STATUS_ATTR = "data-pptx-effect-status"
EFFECT_REASON_ATTR = "data-pptx-effect-reason"
NATIVE_EFFECT_ATTR = "data-pptx-effect-ooxml"
NATIVE_EFFECT_SHA256_ATTR = "data-pptx-effect-ooxml-sha256"
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
_NATIVE_EFFECT_CONTAINER_TAGS = frozenset({
    f"{{{_DML_NAMESPACE}}}effectLst",
    f"{{{_DML_NAMESPACE}}}effectDag",
})
_RELATIONSHIPS_NAMESPACE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)


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
        raw_native = elem.get(NATIVE_EFFECT_ATTR)
        raw_native_sha256 = elem.get(NATIVE_EFFECT_SHA256_ATTR)
        if (
            raw_status is None
            and raw_reason is None
            and raw_native is None
            and raw_native_sha256 is None
        ):
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
        if raw_native is not None or raw_native_sha256 is not None:
            try:
                preserved_native_effect_xml(elem)
            except ValueError as exc:
                errors.add(f"{label} has invalid preserved PPTX effect: {exc}")
            else:
                # The complete native effect container is the registered
                # round-trip fallback for effects outside the SVG subset.
                continue
        errors.add(f'{label} has unsupported source PPTX effect: {reason}')
    return sorted(errors)


def native_effect_metadata(effect_container: ET.Element) -> dict[str, str]:
    """Encode one relationship-free DrawingML effect container for round-trip."""
    _validate_native_effect_container(effect_container)
    raw = ET.tostring(effect_container, encoding="utf-8")
    return {
        NATIVE_EFFECT_ATTR: base64.b64encode(raw).decode("ascii"),
        NATIVE_EFFECT_SHA256_ATTR: hashlib.sha256(raw).hexdigest(),
    }


def preserved_native_effect_xml(elem: ET.Element) -> str | None:
    """Decode and validate one preserved DrawingML effect container."""
    encoded = elem.get(NATIVE_EFFECT_ATTR)
    expected_sha256 = elem.get(NATIVE_EFFECT_SHA256_ATTR)
    if encoded is None and expected_sha256 is None:
        return None
    if not encoded or not expected_sha256:
        raise ValueError(
            f"{NATIVE_EFFECT_ATTR} and {NATIVE_EFFECT_SHA256_ATTR} must appear together"
        )
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{NATIVE_EFFECT_ATTR} must be canonical base64") from exc
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256.strip().lower():
        raise ValueError(
            f"{NATIVE_EFFECT_SHA256_ATTR} does not match the preserved payload"
        )
    try:
        effect_container = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"preserved effect OOXML is malformed: {exc}") from exc
    _validate_native_effect_container(effect_container)
    return raw.decode("utf-8")


def _validate_native_effect_container(effect_container: ET.Element) -> None:
    """Require a standalone, relationship-free DrawingML effect container."""
    if effect_container.tag not in _NATIVE_EFFECT_CONTAINER_TAGS:
        raise ValueError(
            "preserved effect root must be a DrawingML effectLst or effectDag"
        )
    for node in effect_container.iter():
        if not isinstance(node.tag, str) or not node.tag.startswith(
            f"{{{_DML_NAMESPACE}}}"
        ):
            raise ValueError("preserved effect payload must contain only DrawingML")
        if any(
            isinstance(name, str)
            and name.startswith(f"{{{_RELATIONSHIPS_NAMESPACE}}}")
            for name in node.attrib
        ):
            raise ValueError("preserved effect payload cannot contain relationships")


def unsupported_effect_metadata(*reasons: str) -> dict[str, str]:
    """Build one canonical import marker without dropping compound reasons."""
    normalized: set[str] = set()
    for reason in reasons:
        reason = reason.strip()
        if not reason:
            raise ValueError("Unsupported PPTX effect reason must not be empty")
        items: object = reason
        if reason.startswith("["):
            try:
                items = json.loads(reason)
            except json.JSONDecodeError:
                pass
        if not isinstance(items, list):
            items = [reason]
        if not all(isinstance(item, str) and item.strip() for item in items):
            raise ValueError("Unsupported PPTX effect reasons must be strings")
        normalized.update(item.strip() for item in items)
    if not normalized:
        raise ValueError("Unsupported PPTX effect reason must not be empty")
    ordered = sorted(normalized)
    encoded = (
        ordered[0]
        if len(ordered) == 1
        else json.dumps(ordered, separators=(",", ":"))
    )
    return {
        EFFECT_STATUS_ATTR: UNSUPPORTED_EFFECT_STATUS,
        EFFECT_REASON_ATTR: encoded,
    }


def txbody_has_run_effects(*text_style_roots: ET.Element | None) -> bool:
    """Return whether rebuilding any supplied text style would lose an effect."""
    for root in text_style_roots:
        if root is None:
            continue
        for properties in root.iter():
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
