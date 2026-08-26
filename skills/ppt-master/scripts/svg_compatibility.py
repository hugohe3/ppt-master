"""Shared, semantics-preserving SVG compatibility normalizations.

See scripts/docs/svg-pipeline.md for the dangerous compatibility export
boundary.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET


_FILTER_TARGETS = frozenset({'circle', 'image', 'path', 'rect', 'text'})
_NON_VISUAL_TAGS = frozenset({'defs', 'desc', 'metadata', 'title'})


def _local_name(tag: object) -> str:
    return tag.rsplit('}', 1)[-1] if isinstance(tag, str) else ''


def normalize_single_child_group_filters(
    root: ET.Element,
) -> list[dict[str, str]]:
    """Move a group filter to its sole supported visual child.

    A filter on a one-child, attribute-free group is visually equivalent to
    the same filter on that child. Multi-child or otherwise styled groups are
    left unchanged because lowering would alter effect compositing.
    """
    normalizations: list[dict[str, str]] = []
    for group in root.iter():
        if _local_name(group.tag) != 'g':
            continue
        filter_value = group.get('filter')
        if filter_value is None:
            continue
        if set(group.attrib) != {'filter'}:
            continue
        if group.text and group.text.strip():
            continue
        visual_children = [
            child
            for child in group
            if isinstance(child.tag, str)
            and _local_name(child.tag) not in _NON_VISUAL_TAGS
        ]
        if len(visual_children) != 1:
            continue
        child = visual_children[0]
        child_tag = _local_name(child.tag)
        if child_tag not in _FILTER_TARGETS or child.get('filter') is not None:
            continue
        child.set('filter', filter_value)
        del group.attrib['filter']
        normalizations.append({
            'action': 'lower-single-child-group-filter',
            'target_tag': child_tag,
            'filter': filter_value,
        })
    return normalizations
