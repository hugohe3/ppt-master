"""Write-side OOXML package plumbing for source-preserving slide cloning.

Content-type override insertion, relationship-element construction / lookup, and
part-number allocation used when cloning slides into a new package.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from .ooxml import (
    CT_NS,
    REL_NS,
    SLIDE_CONTENT_TYPE,
    _normalize_part,
    _qn,
    _rels_name_for_part,
    _xml_bytes,
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


def _empty_relationships_root() -> ET.Element:
    return ET.Element(_qn(REL_NS, "Relationships"))


def _relative_target(from_part: str, to_part: str) -> str:
    return posixpath.relpath(to_part, posixpath.dirname(from_part))


def _max_numeric_rid(root: ET.Element) -> int:
    max_id = 0
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        rel_id = rel.attrib.get("Id", "")
        match = re.fullmatch(r"rId(\d+)", rel_id)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id


def _enqueue_rel_targets(
    entries: dict[str, bytes],
    rels_part: str,
    base_part: str,
    queue: list[str],
) -> None:
    data = entries.get(rels_part)
    if data is None:
        return
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise RuntimeError(
            f"Cannot parse relationships part {rels_part}: {exc}"
        ) from exc
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        if (rel.attrib.get("TargetMode") or "").strip().lower() == "external":
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


def prune_unreferenced_directory_parts(package_root: Path) -> int:
    """Prune unreachable parts from one extracted OOXML package directory."""
    entries = {
        path.relative_to(package_root).as_posix(): path.read_bytes()
        for path in package_root.rglob("*")
        if path.is_file()
    }
    content_types = entries.get("[Content_Types].xml")
    if content_types is None:
        raise RuntimeError("Extracted PPTX package has no [Content_Types].xml")
    content_root = _content_type_root(ET.fromstring(content_types))
    before = set(entries)
    _prune_unreferenced_parts(entries, content_root)
    removed = before - set(entries)
    for part_name in sorted(removed):
        target = package_root.joinpath(*part_name.split("/"))
        if target.is_file():
            target.unlink()
    (package_root / "[Content_Types].xml").write_bytes(_xml_bytes(content_root))
    return len(removed)
