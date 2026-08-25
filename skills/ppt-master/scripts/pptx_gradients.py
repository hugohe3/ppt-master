#!/usr/bin/env python3
"""Validated native payload contract for imported DrawingML gradients."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from xml.etree import ElementTree as ET


NATIVE_GRADIENT_ATTR = "data-pptx-gradient-ooxml"
NATIVE_GRADIENT_SHA256_ATTR = "data-pptx-gradient-ooxml-sha256"
NATIVE_GRADIENT_PREVIEW_SHA256_ATTR = "data-pptx-gradient-preview-sha256"
_DML_NAMESPACE = "http://schemas.openxmlformats.org/drawingml/2006/main"
_RELATIONSHIPS_NAMESPACE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_TRANSPORT_ATTRIBUTES = frozenset({
    "id",
    NATIVE_GRADIENT_ATTR,
    NATIVE_GRADIENT_SHA256_ATTR,
    NATIVE_GRADIENT_PREVIEW_SHA256_ATTR,
})


def native_gradient_metadata(
    grad_fill: ET.Element,
    preview_gradient: ET.Element,
) -> dict[str, str]:
    """Encode a relationship-free gradFill and bind it to its SVG preview."""
    _validate_native_gradient(grad_fill)
    raw = ET.tostring(grad_fill, encoding="utf-8")
    return {
        NATIVE_GRADIENT_ATTR: base64.b64encode(raw).decode("ascii"),
        NATIVE_GRADIENT_SHA256_ATTR: hashlib.sha256(raw).hexdigest(),
        NATIVE_GRADIENT_PREVIEW_SHA256_ATTR: gradient_preview_fingerprint(
            preview_gradient
        ),
    }


def preserved_native_gradient_xml(gradient: ET.Element) -> str | None:
    """Return unchanged imported gradFill OOXML or defer to SVG authoring."""
    encoded = gradient.get(NATIVE_GRADIENT_ATTR)
    expected_sha256 = gradient.get(NATIVE_GRADIENT_SHA256_ATTR)
    expected_preview = gradient.get(NATIVE_GRADIENT_PREVIEW_SHA256_ATTR)
    if encoded is None and expected_sha256 is None and expected_preview is None:
        return None
    if not encoded or not expected_sha256 or not expected_preview:
        raise ValueError(
            "Imported gradient payload, payload hash, and preview hash must "
            "appear together"
        )
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Imported gradient payload must be canonical base64") from exc
    if hashlib.sha256(raw).hexdigest() != expected_sha256.strip().lower():
        raise ValueError("Imported gradient payload hash does not match")
    try:
        grad_fill = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"Imported gradient OOXML is malformed: {exc}") from exc
    _validate_native_gradient(grad_fill)
    if gradient_preview_fingerprint(gradient) != expected_preview.strip().lower():
        return None
    return raw.decode("utf-8")


def gradient_preview_fingerprint(gradient: ET.Element) -> str:
    """Hash visible SVG gradient semantics while excluding transport fields."""
    payload = {
        "tag": _local_name(gradient.tag),
        "attributes": sorted(
            (name, value)
            for name, value in gradient.attrib.items()
            if _local_name(name) not in _TRANSPORT_ATTRIBUTES
        ),
        "stops": [
            {
                "attributes": sorted(child.attrib.items()),
                "text": (child.text or "").strip(),
            }
            for child in gradient
            if _local_name(child.tag) == "stop"
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_native_gradient(grad_fill: ET.Element) -> None:
    """Require one standalone, relationship-free DrawingML gradFill."""
    if grad_fill.tag != f"{{{_DML_NAMESPACE}}}gradFill":
        raise ValueError("Imported gradient root must be a DrawingML gradFill")
    for node in grad_fill.iter():
        if not isinstance(node.tag, str) or not node.tag.startswith(
            f"{{{_DML_NAMESPACE}}}"
        ):
            raise ValueError("Imported gradient payload must contain only DrawingML")
        if any(
            isinstance(name, str)
            and name.startswith(f"{{{_RELATIONSHIPS_NAMESPACE}}}")
            for name in node.attrib
        ):
            raise ValueError("Imported gradient payload cannot contain relationships")


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""
