"""
SVG Annotation Utilities for ppt-master SVG Editor.

Handles reading, writing, and managing edit annotations in SVG files.
Annotations are stored as custom XML attributes: data-edit-target, data-edit-annotation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

SVG_NS = 'http://www.w3.org/2000/svg'

# Register namespace to avoid ns0: prefix in output
ET.register_namespace('', SVG_NS)


def assign_temp_ids(root: ET.Element) -> None:
    """
    Assign temporary ids to SVG elements that don't have one.

    Skips the root svg element and any element that already has an id.
    Temp ids are deterministic based on element tree order: _edit_0, _edit_1, ...
    """
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
    """
    Extract all annotations from an SVG element tree.

    Returns list of dicts with keys: element_id, tag, annotation.
    """
    annotations = []
    for elem in root.iter():
        if elem.get('data-edit-target') == 'true':
            annotations.append({
                'element_id': elem.get('id', ''),
                'tag': elem.tag.replace(f'{{{SVG_NS}}}', ''),
                'annotation': elem.get('data-edit-annotation', ''),
            })
    return annotations


def set_annotation(root: ET.Element, element_id: str, annotation: str) -> bool:
    """
    Add or update an annotation on an SVG element.

    Returns True if element was found and annotated, False otherwise.
    """
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False
    elem.set('data-edit-target', 'true')
    elem.set('data-edit-annotation', annotation)
    return True


def remove_annotation(root: ET.Element, element_id: str) -> bool:
    """
    Remove annotation attributes from an SVG element.

    Returns True if element was found, False otherwise.
    """
    elem = _find_by_id(root, element_id)
    if elem is None:
        return False
    elem.attrib.pop('data-edit-target', None)
    elem.attrib.pop('data-edit-annotation', None)
    return True
