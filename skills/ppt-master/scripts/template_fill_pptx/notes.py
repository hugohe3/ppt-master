"""Speaker-notes parts for cloned slides.

Builds native PowerPoint notes-slide XML and the slide<->notesSlide<->notesMaster
relationships from a plan's ``notes`` field, reusing the SVG pipeline's notes
renderer so embedded notes also feed ``notes_to_audio.py``.
"""

from __future__ import annotations

import posixpath
from xml.etree import ElementTree as ET

from svg_to_pptx.pptx_notes import create_notes_slide_xml, markdown_to_plain_text

from .ooxml import NOTES_SLIDE_REL_TYPE, REL_NS, SLIDE_REL_TYPE, _qn, _xml_bytes
from .package import _empty_relationships_root, _max_numeric_rid


def _find_notes_master_target(entries: dict[str, bytes]) -> str | None:
    notes_master_rel_type = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster"
    )

    for name, data in entries.items():
        if not name.startswith("ppt/notesSlides/_rels/notesSlide") or not name.endswith(".xml.rels"):
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            continue
        for rel in root.findall(_qn(REL_NS, "Relationship")):
            if rel.attrib.get("Type") == notes_master_rel_type:
                return rel.attrib.get("Target")

    presentation_rels = entries.get("ppt/_rels/presentation.xml.rels")
    if not presentation_rels:
        return None
    try:
        root = ET.fromstring(presentation_rels)
    except ET.ParseError:
        return None
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        if rel.attrib.get("Type") != notes_master_rel_type:
            continue
        target = rel.attrib.get("Target")
        if not target:
            return None
        if target.startswith("/"):
            target = target.lstrip("/")
        else:
            target = posixpath.normpath(posixpath.join("ppt", target))
        return posixpath.relpath(target, "ppt/notesSlides")
    return None


def _create_notes_rels_xml(slide_number: int, notes_master_target: str | None) -> bytes:
    root = _empty_relationships_root()
    if notes_master_target:
        ET.SubElement(
            root,
            _qn(REL_NS, "Relationship"),
            {
                "Id": "rId1",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster",
                "Target": notes_master_target,
            },
        )
        slide_rel_id = "rId2"
    else:
        slide_rel_id = "rId1"
    ET.SubElement(
        root,
        _qn(REL_NS, "Relationship"),
        {
            "Id": slide_rel_id,
            "Type": SLIDE_REL_TYPE,
            "Target": f"../slides/slide{slide_number}.xml",
        },
    )
    return _xml_bytes(root)


def _slide_rels_with_notes(
    rels_bytes: bytes | None,
    *,
    slide_number: int,
    notes_text: str,
    notes_master_target: str | None,
) -> tuple[bytes, dict[str, bytes]]:
    root = ET.fromstring(rels_bytes) if rels_bytes else _empty_relationships_root()
    for rel in list(root.findall(_qn(REL_NS, "Relationship"))):
        if rel.attrib.get("Type") == NOTES_SLIDE_REL_TYPE:
            root.remove(rel)

    note_entries: dict[str, bytes] = {}
    notes_text = notes_text.strip()
    if notes_text:
        rel_id = f"rId{_max_numeric_rid(root) + 1}"
        notes_part = f"ppt/notesSlides/notesSlide{slide_number}.xml"
        notes_rels_part = f"ppt/notesSlides/_rels/notesSlide{slide_number}.xml.rels"
        ET.SubElement(
            root,
            _qn(REL_NS, "Relationship"),
            {
                "Id": rel_id,
                "Type": NOTES_SLIDE_REL_TYPE,
                "Target": f"../notesSlides/notesSlide{slide_number}.xml",
            },
        )
        plain_notes = markdown_to_plain_text(notes_text)
        note_entries[notes_part] = create_notes_slide_xml(slide_number, plain_notes).encode("utf-8")
        note_entries[notes_rels_part] = _create_notes_rels_xml(slide_number, notes_master_target)

    return _xml_bytes(root), note_entries
