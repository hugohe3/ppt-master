#!/usr/bin/env python3
"""
PPT Master - SVG Annotation Utilities

Read, write, and manage edit annotations in SVG files.
Annotations are stored as custom XML attributes (data-edit-target, data-edit-annotation)
on SVG elements, enabling AI-driven targeted editing.

Usage:
    (library module — imported by server.py and check_annotations.py)

Dependencies:
    None (only uses standard library)
"""

import xml.etree.ElementTree as ET
from typing import Optional

SVG_NS = 'http://www.w3.org/2000/svg'

# Register namespace to avoid ns0: prefix in output
ET.register_namespace('', SVG_NS)


def assign_temp_ids(root: ET.Element) -> None:
    """Assign deterministic temp ids (_edit_0, _edit_1, ...) to elements without one.

    Clears any leftover _edit_N ids from previous sessions first, to avoid
    shifted numbering when elements are added/removed between sessions.
    """
    for elem in root.iter():
        eid = elem.get('id', '')
        if eid.startswith('_edit_'):
            elem.attrib.pop('id', None)

    counter = 0
    for elem in root.iter():
        if elem is root:
            continue
        if elem.get('id') is None:
            elem.set('id', f'_edit_{counter}')
            counter += 1


def _find_by_id(root: ET.Element, element_id: str) -> Optional[ET.Element]:
    """Find an element by its id attribute in the SVG tree."""
    for elem in root.iter():
        if elem.get('id') == element_id:
            return elem
    return None


def parse_annotations(root: ET.Element) -> list[dict]:
    """Extract all annotations from an SVG element tree."""
    annotations = []
    for elem in root.iter():
        if elem.get('data-edit-target') == 'true':
            annotations.append({
                'element_id': elem.get('id', ''),
                'tag': elem.tag.split('}', 1)[1] if '}' in elem.tag else elem.tag,
                'annotation': elem.get('data-edit-annotation', ''),
            })
    return annotations


def set_annotation(root: ET.Element, element_id: str, annotation: str) -> bool:
    """Add or update an annotation on an SVG element. Returns True if found."""
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False
    elem.set('data-edit-target', 'true')
    elem.set('data-edit-annotation', annotation)
    return True


def remove_annotation(root: ET.Element, element_id: str) -> bool:
    """Remove annotation attributes from an SVG element. Returns True if found."""
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False
    elem.attrib.pop('data-edit-target', None)
    elem.attrib.pop('data-edit-annotation', None)
    return True


# ---------------------------------------------------------------------------
# Direct (AI-free) editing — used by server.py POST /api/slide/<name>/edit.
# These mutate the element itself (text content / presentation attributes)
# instead of leaving an annotation marker for the AI to act on. Value
# validation is the caller's responsibility; these helpers only write.
# ---------------------------------------------------------------------------

# Attributes that must never be edited from the browser property panel.
PROTECTED_ATTRS = frozenset({
    'id', 'class', 'data-edit-target', 'data-edit-annotation',
})
PROTECTED_ATTR_SUFFIXES = frozenset({
    'href',
})


def is_editable_attr(key: str) -> bool:
    """Return True when a raw SVG attribute is safe to edit from the UI."""
    key_lower = key.lower()
    if key_lower in PROTECTED_ATTRS:
        return False
    if key_lower.startswith('on'):
        return False
    if key_lower in PROTECTED_ATTR_SUFFIXES or key_lower.endswith(':href'):
        return False
    return True


def set_text(root: ET.Element, element_id: str, text: str) -> tuple[bool, Optional[str]]:
    """Set an element's text content (L1). Returns (ok, reason).

    Refuses elements that own <tspan> children: overwriting ``.text`` there
    would orphan the tspans and destroy the multi-line layout. The caller
    should target the specific <tspan> instead.
    """
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False, 'not-found'
    for child in elem:
        ctag = child.tag.split('}', 1)[1] if '}' in child.tag else child.tag
        if ctag == 'tspan':
            return False, 'has-tspan-children'
    elem.text = text
    return True, None


def set_attributes(
    root: ET.Element, element_id: str, attrs: dict,
) -> tuple[bool, Optional[str]]:
    """Set whitelisted presentation attributes (L2). Returns (ok, reason).

    Enforces is_editable_attr as a hard gate (defence in depth — server.py
    also validates values before calling here). Writes nothing if any key is
    disallowed, so a rejected request leaves the element untouched.
    """
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False, 'not-found'
    for key in attrs:
        if not is_editable_attr(key):
            return False, f'attr-not-allowed:{key}'
    for key, value in attrs.items():
        elem.set(key, str(value))
    return True, None


def remove_attribute(
    root: ET.Element, element_id: str, key: str,
) -> tuple[bool, Optional[str]]:
    """Remove a whitelisted attribute (used by undo when the old value was unset).

    Returns (ok, reason). Enforces is_editable_attr so undo can only touch the
    same surface a direct edit could.
    """
    if not is_editable_attr(key):
        return False, f'attr-not-allowed:{key}'
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False, 'not-found'
    elem.attrib.pop(key, None)
    return True, None


def strip_unused_temp_ids(root: ET.Element, keep_ids: set) -> None:
    """Drop transient ``_edit_N`` ids except those in ``keep_ids`` and any
    element still carrying a submitted annotation (its id is the AI's locator).

    Mirrors the cleanup in server.py's save-all so a direct edit never
    strips the id an unsaved/saved annotation depends on.
    """
    protected = set(keep_ids)
    for elem in root.iter():
        if elem.get('data-edit-target') == 'true':
            eid = elem.get('id')
            if eid:
                protected.add(eid)
    for elem in root.iter():
        eid = elem.get('id', '')
        if eid.startswith('_edit_') and eid not in protected:
            elem.attrib.pop('id', None)
