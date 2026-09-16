"""Write-side OOXML package plumbing for source-preserving slide cloning.

Content-type override insertion, relationship-element construction / lookup, and
part-number allocation used when cloning slides into a new package.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Callable
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

_OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_SLIDE_TAG = "{http://schemas.openxmlformats.org/presentationml/2006/main}sld"
# These Slide relationships require explicit XML consumers. Structural links
# (Layout, notes, comments, tags, theme overrides, etc.) are implicit and stay.
_EXPLICIT_SLIDE_REL_KINDS = frozenset({
    "audio", "video", "media", "image", "hyperlink", "slide", "chart", "chartEx",
    "oleObject", "package", "diagramData", "diagramLayout", "diagramQuickStyle",
    "diagramColors", "diagramDrawing", "control", "model3d",
})


def unreferenced_slide_relationships(
    slide: ET.Element,
    relationships: ET.Element,
    *,
    owner_part: str,
    read_part: Callable[[str], bytes],
) -> list[ET.Element]:
    """Find explicit Slide payload relationships with no remaining XML use."""
    if slide.tag != _SLIDE_TAG:
        return []
    referenced = {
        value for node in slide.iter() for name, value in node.attrib.items()
        if name.startswith(f"{{{_OFFICE_REL_NS}}}")
    }
    drawing_ids = {
        rel.get("Id") for rel in relationships
        if rel.get("Type", "").endswith("/diagramDrawing")
    }
    # Older SmartArt stores dataModelExt@relId in the live diagram data XML,
    # but resolves it against the owning Slide's relationships. Newer files
    # resolve it against the data part's own .rels instead.
    for rel in relationships:
        if rel.get("Id") not in referenced or not rel.get("Type", "").endswith("/diagramData"):
            continue
        data_part = _normalize_part(rel.get("Target", ""), owner_part)
        if rel.get("TargetMode") == "External" or data_part == ".." or data_part.startswith("../"):
            continue
        try:
            data = ET.fromstring(read_part(data_part))
        except (KeyError, OSError, ET.ParseError):
            continue
        try:
            data_rels = ET.fromstring(read_part(_rels_name_for_part(data_part)))
            local_ids = {item.get("Id") for item in data_rels}
        except (KeyError, OSError, ET.ParseError):
            local_ids = set()
        referenced.update(
            node.get("relId") for node in data.iter(
                "{http://schemas.microsoft.com/office/drawing/2008/diagram}dataModelExt"
            ) if node.get("relId") in drawing_ids and node.get("relId") not in local_ids
        )
    return [
        rel for rel in relationships
        if rel.get("Type", "").rsplit("/", 1)[-1] in _EXPLICIT_SLIDE_REL_KINDS
        and rel.get("Id") not in referenced
    ]


def unused_slide_relationship_problems(package_root: Path) -> list[str]:
    """Report dangling explicit relationships without rejecting implicit ones."""
    problems = []
    for path in sorted((package_root / "ppt" / "slides").glob("*.xml")):
        part = path.relative_to(package_root).as_posix()
        rels = package_root / _rels_name_for_part(part)
        if not rels.is_file():
            continue
        try:
            unused = unreferenced_slide_relationships(
                ET.parse(path).getroot(), ET.parse(rels).getroot(), owner_part=part,
                read_part=lambda name: (package_root / name).read_bytes(),
            )
        except ET.ParseError:
            continue  # The package XML verifier owns malformed XML.
        problems.extend(
            f"{part}: unreferenced relationship {rel.get('Id')!r} -> {rel.get('Target')!r}; "
            "the slide XML has no reference to this relationship"
            for rel in unused
        )
    return problems


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


def prune_unreferenced_directory_parts(
    package_root: Path,
    *,
    edited_slide_parts: set[str] | frozenset[str] = frozenset(),
) -> int:
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
    for part in sorted(edited_slide_parts):
        rels_name = _rels_name_for_part(part)
        if part not in entries or rels_name not in entries:
            continue
        relationships = ET.fromstring(entries[rels_name])
        unused = unreferenced_slide_relationships(
            ET.fromstring(entries[part]), relationships, owner_part=part, read_part=entries.__getitem__,
        )
        if unused:
            for rel in unused:
                relationships.remove(rel)
            entries[rels_name] = _xml_bytes(relationships)
            (package_root / rels_name).write_bytes(entries[rels_name])
    before = set(entries)
    _prune_unreferenced_parts(entries, content_root)
    removed = before - set(entries)
    for part_name in sorted(removed):
        target = package_root.joinpath(*part_name.split("/"))
        if target.is_file():
            target.unlink()
    (package_root / "[Content_Types].xml").write_bytes(_xml_bytes(content_root))
    return len(removed)
