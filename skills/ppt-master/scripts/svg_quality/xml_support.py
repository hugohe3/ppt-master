#!/usr/bin/env python3
"""PPT Master SVG quality XML helpers.

Provides namespace constants and compact element labels shared by quality-check
domains.

Usage:
    Import from ``svg_quality.checker`` or another ``svg_quality`` module.

Examples:
    from svg_quality.xml_support import local_name

Dependencies:
    Standard library only.
"""

from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def local_name(elem: ET.Element) -> str:
    """Return an XML element's namespace-free local tag name."""
    tag = elem.tag
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def element_label(elem: ET.Element) -> str:
    """Return a compact element label for validation messages."""
    tag = local_name(elem)
    elem_id = (elem.get("id") or "").strip()
    return f'<{tag} id="{elem_id}">' if elem_id else f"<{tag}>"
