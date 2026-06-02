"""Write-side OOXML package plumbing for the apply stage.

Content-type override insertion, relationship-element construction / lookup, and
part-number allocation used when cloning slides into a new package.
"""

from __future__ import annotations

import posixpath
import re
from xml.etree import ElementTree as ET

from .ooxml import (
    CT_NS,
    NOTES_SLIDE_CONTENT_TYPE,
    NS,
    REL_NS,
    SLIDE_CONTENT_TYPE,
    _normalize_part,
    _qn,
    _rels_name_for_part,
)


def _content_type_root(root: ET.Element) -> ET.Element:
    if root.tag != _qn(CT_NS, "Types"):
        raise RuntimeError("[Content_Types].xml has an unexpected root element")
    return root


def _add_content_type_override(content_root: ET.Element, part_name: str, content_type: str) -> None:
    part_name = "/" + part_name.lstrip("/")
    for override in content_root.findall(_qn(CT_NS, "Override")):
        if override.attrib.get("PartName") == part_name:
            return
    ET.SubElement(
        content_root,
        _qn(CT_NS, "Override"),
        {"PartName": part_name, "ContentType": content_type},
    )


def _add_slide_override(content_root: ET.Element, part_name: str) -> None:
    _add_content_type_override(content_root, part_name, SLIDE_CONTENT_TYPE)


def _add_notes_override(content_root: ET.Element, part_name: str) -> None:
    _add_content_type_override(content_root, part_name, NOTES_SLIDE_CONTENT_TYPE)


def _empty_relationships_root() -> ET.Element:
    return ET.Element(_qn(REL_NS, "Relationships"))


def _find_relationship(root: ET.Element, rel_id: str) -> ET.Element | None:
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        if rel.attrib.get("Id") == rel_id:
            return rel
    return None


def _relative_target(from_part: str, to_part: str) -> str:
    return posixpath.relpath(to_part, posixpath.dirname(from_part))


def _max_slide_part_number(entries: dict[str, bytes]) -> int:
    max_number = 0
    pattern = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
    for name in entries:
        match = pattern.match(name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number


def _max_numeric_rid(root: ET.Element) -> int:
    max_id = 0
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        rel_id = rel.attrib.get("Id", "")
        match = re.fullmatch(r"rId(\d+)", rel_id)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id


def _max_slide_id(sld_id_lst: ET.Element) -> int:
    max_id = 255
    for sld_id in sld_id_lst.findall("p:sldId", NS):
        try:
            max_id = max(max_id, int(sld_id.attrib.get("id", "0")))
        except ValueError:
            continue
    return max_id


def _enqueue_rel_targets(
    entries: dict[str, bytes],
    rels_part: str,
    base_part: str,
    queue: list[str],
) -> None:
    data = entries.get(rels_part)
    if not data:
        return
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        if rel.attrib.get("TargetMode") == "External":
            continue
        target = rel.attrib.get("Target")
        if target:
            queue.append(_normalize_part(target, base_part or "x"))


def _reachable_parts(entries: dict[str, bytes]) -> set[str]:
    """Parts reachable from the package root by following relationships."""
    keep: set[str] = set()
    queue: list[str] = []
    _enqueue_rel_targets(entries, "_rels/.rels", "", queue)
    while queue:
        part = queue.pop()
        if part in keep:
            continue
        keep.add(part)
        _enqueue_rel_targets(entries, _rels_name_for_part(part), part, queue)
    return keep


def _prune_unreferenced_parts(entries: dict[str, bytes], content_root: ET.Element) -> None:
    """Drop parts not reachable from the package root through relationships.

    After cloning only the planned slides, the original slide / notesSlide /
    chart / embedding parts left in ``entries`` are orphaned — nothing in the
    rebuilt presentation references them. Reachability GC removes that dead
    weight so the output deck carries only the selected pages and their assets,
    and prunes the matching ``[Content_Types].xml`` overrides.
    """
    reachable = _reachable_parts(entries)
    keep = set(reachable)
    keep.update({"[Content_Types].xml", "_rels/.rels"})
    for part in reachable:
        rels = _rels_name_for_part(part)
        if rels in entries:
            keep.add(rels)

    for name in list(entries):
        if name not in keep:
            del entries[name]

    for override in list(content_root.findall(_qn(CT_NS, "Override"))):
        part_name = (override.attrib.get("PartName") or "").lstrip("/")
        if part_name and part_name not in reachable:
            content_root.remove(override)
