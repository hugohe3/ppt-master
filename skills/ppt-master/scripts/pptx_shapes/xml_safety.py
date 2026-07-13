#!/usr/bin/env python3
"""Safety checks for opaque DrawingML fragments copied between PPTX parts."""

from __future__ import annotations

from xml.etree import ElementTree as ET


RELATIONSHIPS_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_RELATIONSHIP_ATTRIBUTE_PREFIX = f"{{{RELATIONSHIPS_NS}}}"


def has_relationship_attributes(root: ET.Element) -> bool:
    """Return whether a subtree contains any part-local relationship QName."""
    return any(
        attribute.startswith(_RELATIONSHIP_ATTRIBUTE_PREFIX)
        for element in root.iter()
        for attribute in element.attrib
    )
