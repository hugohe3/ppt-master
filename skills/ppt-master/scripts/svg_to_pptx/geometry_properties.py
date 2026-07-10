"""Materialize the supported inline SVG geometry-property subset.

SVG 2 lets selected geometry values participate in CSS. PPT Master does not
run a CSS engine, but it can safely compile literal per-element ``style``
declarations into the equivalent XML geometry attributes before any existing
SVG post-processing or DrawingML conversion runs.
"""

from __future__ import annotations

import copy
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'

INLINE_GEOMETRY_PROPERTIES = {
    'rect': frozenset({'x', 'y', 'width', 'height', 'rx', 'ry'}),
    'circle': frozenset({'cx', 'cy', 'r'}),
    'ellipse': frozenset({'cx', 'cy', 'rx', 'ry'}),
    'image': frozenset({'x', 'y', 'width', 'height'}),
    'svg': frozenset({'x', 'y', 'width', 'height'}),
    'use': frozenset({'x', 'y', 'width', 'height'}),
}

_GEOMETRY_LIKE_PROPERTIES = frozenset({
    'x', 'y', 'width', 'height', 'rx', 'ry', 'cx', 'cy', 'r',
    'x1', 'y1', 'x2', 'y2', 'dx', 'dy', 'points', 'd',
})
_NON_NEGATIVE_PROPERTIES = frozenset({'width', 'height', 'rx', 'ry', 'r'})
_PX_LENGTH_RE = re.compile(
    r'^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*(px)?\s*$',
    re.IGNORECASE,
)


class GeometryStyleError(ValueError):
    """Reject inline geometry that cannot be compiled deterministically."""


def _local_tag(elem: ET.Element) -> str:
    tag = str(elem.tag)
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def _format_number(value: float) -> str:
    if abs(value) < 1e-12:
        value = 0.0
    return f'{value:.12g}'


def _normalize_px_length(raw: str, tag: str, prop: str) -> str:
    """Return one finite CSS px literal as a unitless SVG user value."""
    match = _PX_LENGTH_RE.fullmatch(raw)
    if match is None:
        raise GeometryStyleError(
            f'<{tag}> inline geometry {prop} requires a finite px literal; '
            f'got {raw!r}'
        )
    value = float(match.group(1))
    if not math.isfinite(value):
        raise GeometryStyleError(
            f'<{tag}> inline geometry {prop} must be finite; got {raw!r}'
        )
    if match.group(2) is None and value != 0:
        raise GeometryStyleError(
            f'<{tag}> inline geometry {prop} requires px for non-zero values; '
            f'got {raw!r}'
        )
    if prop in _NON_NEGATIVE_PROPERTIES and value < 0:
        raise GeometryStyleError(
            f'<{tag}> inline geometry {prop} cannot be negative; got {raw!r}'
        )
    return _format_number(value)


def materialize_inline_geometry_properties(root: ET.Element) -> int:
    """Compile supported inline geometry declarations into XML attributes."""
    materialized = 0
    for elem in root.iter():
        style = elem.get('style')
        if not style:
            continue
        tag = _local_tag(elem)
        supported = INLINE_GEOMETRY_PROPERTIES.get(tag, frozenset())
        retained: list[str] = []
        element_materialized = 0
        for raw_declaration in style.split(';'):
            declaration = raw_declaration.strip()
            if not declaration:
                continue
            if ':' not in declaration:
                retained.append(declaration)
                continue
            raw_name, raw_value = declaration.split(':', 1)
            name = raw_name.strip().lower()
            value = raw_value.strip()
            if name not in _GEOMETRY_LIKE_PROPERTIES:
                retained.append(declaration)
                continue
            if name not in supported:
                raise GeometryStyleError(
                    f'<{tag}> does not support inline geometry property {name!r}; '
                    'use the element\'s XML geometry attribute instead'
                )
            elem.set(name, _normalize_px_length(value, tag, name))
            materialized += 1
            element_materialized += 1

        if element_materialized == 0:
            continue
        if retained:
            elem.set('style', '; '.join(retained))
        else:
            elem.attrib.pop('style', None)
    return materialized


def validate_inline_geometry_properties(root: ET.Element) -> list[str]:
    """Return inline geometry errors without mutating the caller's SVG tree."""
    try:
        materialize_inline_geometry_properties(copy.deepcopy(root))
    except GeometryStyleError as exc:
        return [str(exc)]
    return []


def materialize_inline_geometry_in_file(svg_path: Path) -> int:
    """Materialize inline geometry in one SVG file in place."""
    tree = ET.parse(str(svg_path))
    count = materialize_inline_geometry_properties(tree.getroot())
    if count:
        ET.register_namespace('', SVG_NS)
        ET.register_namespace('xlink', XLINK_NS)
        tree.write(str(svg_path), encoding='unicode', xml_declaration=False)
    return count
