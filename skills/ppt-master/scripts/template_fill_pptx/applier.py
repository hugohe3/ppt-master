"""apply: clone selected source slides into a new PPTX and write replacements.

Orchestrates the per-stage helpers (text / table / chart / transition / notes)
and rebuilds the presentation slide list, relationships, and content types.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from pptx_animations import (
    object_animation_fingerprint,
    validate_pptx_animation_package,
)
from pptx_transitions import (
    parse_source_xml,
    serialize_source_xml,
    set_package_use_timings,
    validate_pptx_transition_package,
)

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
    wrote_auto_advance = False

    for offset, item in enumerate(plan_slides):
        source_slide = int(item.get("source_slide", 0))
        if source_slide not in slide_refs:
            raise RuntimeError(f"Plan references a missing source slide: {source_slide}")
        source_ref = slide_refs[source_slide]
        new_slide_number = next_slide_number + offset
        new_part = f"ppt/slides/slide{new_slide_number}.xml"
        new_rels = f"ppt/slides/_rels/slide{new_slide_number}.xml.rels"
        new_rid = f"rId{next_rel_number + offset}"

        source_slide_xml = entries[source_ref.part_name]
        source_animation_fingerprint = object_animation_fingerprint(
            source_slide_xml
        )
        slide_root = parse_source_xml(source_slide_xml)
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
        slide_has_auto_advance = _set_slide_transition(
            slide_root,
            effect=slide_effect,
            duration=slide_duration,
            advance_after=slide_advance,
        )
        if slide_advance is not None and slide_has_auto_advance:
            wrote_auto_advance = True

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
        try:
            serialized_slide = serialize_source_xml(
                slide_root,
                source_slide_xml,
            )
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        if (
            object_animation_fingerprint(serialized_slide)
            != source_animation_fingerprint
        ):
            raise RuntimeError(
                f'Slide {source_slide} object animations changed during template fill'
            )
        entries[new_part] = serialized_slide
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
    if wrote_auto_advance:
        try:
            set_package_use_timings(entries)
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="template-fill-pptx-",
        dir=output_path.parent,
    ) as temp_dir:
        candidate_path = Path(temp_dir) / output_path.name
        with zipfile.ZipFile(
            candidate_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as out:
            for name, data in entries.items():
                out.writestr(name, data)
        try:
            validate_pptx_transition_package(
                candidate_path,
                require_use_timings=wrote_auto_advance,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"PPTX transition package validation failed: {exc}"
            ) from exc
        try:
            validate_pptx_animation_package(
                candidate_path,
                require_supported_effects=False,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"PPTX animation/timing package validation failed: {exc}"
            ) from exc
        candidate_path.replace(output_path)
