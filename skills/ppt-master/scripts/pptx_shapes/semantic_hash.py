#!/usr/bin/env python3
"""
PPT Master - Native Shape Semantic Fingerprints

Build stable hashes for visible SVG text and generated preset preview layers.

Usage:
    Import svg_text_fingerprint or svg_preset_preview_fingerprint.

Examples:
    digest = svg_text_fingerprint(group_element)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import json
from xml.etree import ElementTree as ET


_ROOT_TEXT_STYLE_ATTRS = frozenset({
    "class",
    "fill",
    "fill-opacity",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "opacity",
    "style",
    "text-anchor",
    "text-decoration",
    "word-spacing",
})


def svg_text_fingerprint(root: ET.Element) -> str:
    """Hash text content, structure, positioning, and visible typography.

    Shape-level movement is intentionally excluded: the native ``a:xfrm``
    owns that change and the original ``p:txBody`` remains valid.  Text/tspan
    transforms and all their non-semantic attributes remain part of the hash.
    """

    payload = {
        "root_style": sorted(
            (name, value)
            for name, value in root.attrib.items()
            if name in _ROOT_TEXT_STYLE_ATTRS
        ),
        "text": [
            _element_payload(element)
            for element in root.iter()
            if _local_name(element.tag) == "text"
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def svg_preset_preview_fingerprint(root: ET.Element) -> str:
    """Hash the complete visible preview subtree and intermediate wrappers."""
    payload = _preview_subtree(root, is_root=True, active=False)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def resolve_preset_preview_hash(root: ET.Element) -> str | None:
    """Resolve and cross-check a logical preset group's fingerprint contract.

    The hash is duplicated on the logical group and hidden native carrier so
    stripping either copy cannot disable stale-preview detection.  A visible
    generated preview without either hash is invalid rather than legacy SVG.
    """
    has_preview = any(
        element.get("data-pptx-part")
        in {"geometry-preview", "geometry-detail"}
        for element in root.iter()
    )
    carrier_hashes = {
        value
        for element in root.iter()
        if element.get("data-pptx-part") == "geometry"
        and (value := element.get("data-pptx-preview-sha256")) is not None
    }
    group_hash = root.get("data-pptx-preview-sha256")
    if not has_preview and not carrier_hashes and group_hash is None:
        return None
    if len(carrier_hashes) > 1:
        raise ValueError("Native geometry carriers have inconsistent preview hashes")
    carrier_hash = next(iter(carrier_hashes), None)
    if (
        group_hash is not None
        and carrier_hash is not None
        and group_hash != carrier_hash
    ):
        raise ValueError("Logical group and native carrier preview hashes differ")
    expected = group_hash or carrier_hash
    if expected is None:
        raise ValueError("Generated preset preview is missing its fingerprint")
    return expected


def _preview_subtree(
    element: ET.Element,
    *,
    is_root: bool,
    active: bool,
) -> dict | None:
    part = element.get("data-pptx-part")
    contains_preview = part in {"geometry-preview", "geometry-detail"}
    child_active = active or contains_preview
    children = [
        payload
        for child in element
        if (
            payload := _preview_subtree(
                child,
                is_root=False,
                active=child_active,
            )
        ) is not None
    ]
    if is_root:
        return {"children": children}
    if not child_active and not children:
        return None
    return {
        "tag": _local_name(element.tag),
        "attrs": sorted(
            (name, value)
            for name, value in element.attrib.items()
            if name != "id"
            and name != "data-pptx-preview-sha256"
            and not name.startswith("data-pptx-runtime-")
        ),
        "children": children,
    }


def _element_payload(element: ET.Element) -> dict:
    return {
        "tag": _local_name(element.tag),
        "attrs": sorted(
            (name, value)
            for name, value in element.attrib.items()
            if not name.startswith("data-pptx-") and name != "id"
        ),
        "text": element.text or "",
        "children": [
            {
                "node": _element_payload(child),
                "tail": child.tail or "",
            }
            for child in element
            if _local_name(child.tag) in {"text", "tspan"}
        ],
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
