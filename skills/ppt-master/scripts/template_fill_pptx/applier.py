"""apply: clone selected source slides into a new PPTX and write replacements.

Orchestrates the per-stage helpers (text / table / chart / transition / notes)
and rebuilds the presentation slide list, relationships, and content types.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .chart_fill import (
    _apply_chart_edits_to_slide_package,
    _max_chart_part_number,
    _max_embedding_part_number,
)
from .clone import _make_part_allocator, deep_clone_slide_private_parts
from .notes import _find_notes_master_target, _slide_rels_with_notes
from .ooxml import NS, REL_NS, SLIDE_REL_TYPE, _parse_slide_refs, _qn, _xml_bytes
from .package import (
    _add_notes_override,
    _add_slide_override,
    _content_type_root,
    _empty_relationships_root,
    _max_numeric_rid,
    _max_slide_id,
    _max_slide_part_number,
    _prune_unreferenced_parts,
)
from .table_fill import _apply_table_edits_to_slide
from .text_fill import _apply_replacements_to_slide
from .transitions import (
    DEFAULT_TRANSITION,
    DEFAULT_TRANSITION_DURATION,
    _resolve_slide_transition,
    _set_slide_transition,
)


def apply_plan(
    pptx_path: Path,
    plan: dict[str, Any],
    output_path: Path,
    *,
    transition: str | None = DEFAULT_TRANSITION,
    transition_duration: float = DEFAULT_TRANSITION_DURATION,
) -> None:
    """Create a filled PPTX by cloning selected source slides and replacing text."""
    plan_slides = plan.get("slides")
    if not isinstance(plan_slides, list) or not plan_slides:
        raise RuntimeError("Plan must contain a non-empty 'slides' list")

    with zipfile.ZipFile(pptx_path) as zf:
        entries = {info.filename: zf.read(info.filename) for info in zf.infolist() if not info.is_dir()}
        slide_refs = {slide.index: slide for slide in _parse_slide_refs(zf)}
    notes_master_target = _find_notes_master_target(entries)

    pres_root = ET.fromstring(entries["ppt/presentation.xml"])
    pres_rels_root = ET.fromstring(entries["ppt/_rels/presentation.xml.rels"])
    content_root = _content_type_root(ET.fromstring(entries["[Content_Types].xml"]))
    sld_id_lst = pres_root.find("p:sldIdLst", NS)
    if sld_id_lst is None:
        sld_id_lst = ET.SubElement(pres_root, _qn(NS["p"], "sldIdLst"))

    for child in list(sld_id_lst):
        sld_id_lst.remove(child)
    for rel in list(pres_rels_root.findall(_qn(REL_NS, "Relationship"))):
        if rel.attrib.get("Type") == SLIDE_REL_TYPE:
            pres_rels_root.remove(rel)

    next_slide_number = _max_slide_part_number(entries) + 1
    next_slide_id = _max_slide_id(sld_id_lst) + 1
    next_rel_number = _max_numeric_rid(pres_rels_root) + 1
    next_chart_number = _max_chart_part_number(entries)
    next_embedding_number = _max_embedding_part_number(entries)
    allocate_part = _make_part_allocator(entries)

    for offset, item in enumerate(plan_slides):
        source_slide = int(item.get("source_slide", 0))
        if source_slide not in slide_refs:
            raise RuntimeError(f"Plan references a missing source slide: {source_slide}")
        source_ref = slide_refs[source_slide]
        new_slide_number = next_slide_number + offset
        new_part = f"ppt/slides/slide{new_slide_number}.xml"
        new_rels = f"ppt/slides/_rels/slide{new_slide_number}.xml.rels"
        new_rid = f"rId{next_rel_number + offset}"

        slide_root = ET.fromstring(entries[source_ref.part_name])
        replacements = item.get("replacements", [])
        if not isinstance(replacements, list):
            raise RuntimeError(f"Slide {source_slide} replacements must be a list")
        _apply_replacements_to_slide(
            slide_root,
            source_slide=source_slide,
            replacements=replacements,
        )
        table_edits = item.get("table_edits", [])
        if not isinstance(table_edits, list):
            raise RuntimeError(f"Slide {source_slide} table_edits must be a list")
        _apply_table_edits_to_slide(
            slide_root,
            source_slide=source_slide,
            table_edits=table_edits,
        )
        slide_effect, slide_duration, slide_advance = _resolve_slide_transition(
            item,
            default_effect=transition,
            default_duration=transition_duration,
        )
        _set_slide_transition(
            slide_root,
            effect=slide_effect,
            duration=slide_duration,
            advance_after=slide_advance,
        )

        source_rels = entries.get(source_ref.rels_name)
        slide_rels_root = ET.fromstring(source_rels) if source_rels else _empty_relationships_root()
        deep_clone_slide_private_parts(
            slide_rels_root,
            new_slide_part=new_part,
            entries=entries,
            content_root=content_root,
            allocate=allocate_part,
        )
        chart_edits = item.get("chart_edits", [])
        if not isinstance(chart_edits, list):
            raise RuntimeError(f"Slide {source_slide} chart_edits must be a list")
        next_chart_number, next_embedding_number = _apply_chart_edits_to_slide_package(
            slide_root,
            slide_rels_root,
            entries,
            content_root,
            source_slide=source_slide,
            new_slide_part=new_part,
            chart_edits=chart_edits,
            next_chart_number=next_chart_number,
            next_embedding_number=next_embedding_number,
        )
        entries[new_part] = _xml_bytes(slide_root)
        notes_text = str(item.get("notes") or item.get("speaker_notes") or "")
        entries[new_rels], note_entries = _slide_rels_with_notes(
            _xml_bytes(slide_rels_root),
            slide_number=new_slide_number,
            notes_text=notes_text,
            notes_master_target=notes_master_target,
        )
        entries.update(note_entries)
        _add_slide_override(content_root, new_part)
        if note_entries:
            _add_notes_override(content_root, f"ppt/notesSlides/notesSlide{new_slide_number}.xml")

        ET.SubElement(
            pres_rels_root,
            _qn(REL_NS, "Relationship"),
            {
                "Id": new_rid,
                "Type": SLIDE_REL_TYPE,
                "Target": f"slides/slide{new_slide_number}.xml",
            },
        )
        ET.SubElement(
            sld_id_lst,
            _qn(NS["p"], "sldId"),
            {"id": str(next_slide_id + offset), _qn(NS["r"], "id"): new_rid},
        )

    entries["ppt/presentation.xml"] = _xml_bytes(pres_root)
    entries["ppt/_rels/presentation.xml.rels"] = _xml_bytes(pres_rels_root)
    _prune_unreferenced_parts(entries, content_root)
    entries["[Content_Types].xml"] = _xml_bytes(content_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in entries.items():
            out.writestr(name, data)
