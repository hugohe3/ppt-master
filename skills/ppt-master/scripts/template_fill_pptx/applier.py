"""apply: clone selected source slides into a new PPTX and write replacements.

Orchestrates the per-stage helpers (text / table / chart / transition / notes)
and rebuilds the presentation slide list, relationships, and content types.
"""

from __future__ import annotations

import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from hyperlink_contract import SLIDE_JUMP_ACTION
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
from .ooxml import (
    NS,
    REL_NS,
    SLIDE_REL_TYPE,
    SlideRef,
    _normalize_part,
    _parse_slide_refs,
    _qn,
    _rels_name_for_part,
    _xml_bytes,
)
from .package import (
    _add_notes_override,
    _add_slide_override,
    _content_type_root,
    _empty_relationships_root,
    _max_numeric_rid,
    _max_slide_id,
    _max_slide_part_number,
    _prune_unreferenced_parts,
    _relative_target,
)
from .table_fill import _apply_table_edits_to_slide
from .text_fill import _apply_replacements_to_slide
from .transitions import (
    DEFAULT_TRANSITION,
    DEFAULT_TRANSITION_DURATION,
    _resolve_slide_transition,
    _set_slide_transition,
)


@dataclass(frozen=True)
class _PlannedSlideClone:
    """One output slide resolved before any source relationship is rewritten."""

    offset: int
    item: dict[str, Any]
    source_slide: int
    source_ref: SlideRef
    slide_number: int
    part_name: str
    rels_name: str
    presentation_rid: str


def _build_clone_roster(
    plan_slides: list[Any],
    slide_refs: dict[int, SlideRef],
    *,
    next_slide_number: int,
    next_rel_number: int,
) -> list[_PlannedSlideClone]:
    """Resolve every planned output slide before cloning begins."""
    roster: list[_PlannedSlideClone] = []
    for offset, raw_item in enumerate(plan_slides):
        if not isinstance(raw_item, dict):
            raise RuntimeError(f"Plan slide {offset + 1} must be an object")
        source_slide = int(raw_item.get("source_slide", 0))
        if source_slide not in slide_refs:
            raise RuntimeError(f"Plan references a missing source slide: {source_slide}")
        slide_number = next_slide_number + offset
        roster.append(
            _PlannedSlideClone(
                offset=offset,
                item=raw_item,
                source_slide=source_slide,
                source_ref=slide_refs[source_slide],
                slide_number=slide_number,
                part_name=f"ppt/slides/slide{slide_number}.xml",
                rels_name=f"ppt/slides/_rels/slide{slide_number}.xml.rels",
                presentation_rid=f"rId{next_rel_number + offset}",
            )
        )
    return roster


_SLIDE_LAYOUT_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
)
_SLIDE_MASTER_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
)


def _slide_jump_relationship_ids(part_root: ET.Element) -> set[str]:
    """Return relationship ids used by actual same-deck click actions."""
    relationship_attr = _qn(NS["r"], "id")
    return {
        relationship_id
        for link in part_root.iter(_qn(NS["a"], "hlinkClick"))
        if (link.attrib.get("action") or "").strip() == SLIDE_JUMP_ACTION
        if (relationship_id := (link.attrib.get(relationship_attr) or "").strip())
    }


def _remap_slide_jump_relationships(
    part_root: ET.Element,
    relationships_root: ET.Element,
    *,
    source_owner_part: str,
    output_owner_part: str,
    owner_label: str,
    outputs_by_source_part: dict[str, list[str]],
    source_ref_by_part: dict[str, SlideRef],
    self_source_part: str | None = None,
    self_output_part: str | None = None,
) -> bool:
    """Point referenced slide-jump relationships at final output slides.

    Unreferenced ``/slide`` relationships are left untouched. A cloned slide's
    self-link follows that clone; shared layout/master links require one unique
    output for the referenced source slide.
    """
    relationship_ids = _slide_jump_relationship_ids(part_root)
    relationships = {
        rel.attrib.get("Id", ""): rel
        for rel in relationships_root.findall(_qn(REL_NS, "Relationship"))
    }
    changed = False
    for relationship_id in sorted(relationship_ids):
        rel = relationships.get(relationship_id)
        if rel is None:
            raise RuntimeError(
                f"{owner_label} has a slide jump with missing relationship "
                f"{relationship_id!r}"
            )
        if rel.attrib.get("Type") != SLIDE_REL_TYPE:
            raise RuntimeError(
                f"{owner_label} slide jump {relationship_id!r} does not use "
                "a slide relationship"
            )
        if rel.attrib.get("TargetMode") == "External":
            raise RuntimeError(
                f"{owner_label} has an external slide relationship"
            )
        target = rel.attrib.get("Target")
        if not target:
            raise RuntimeError(
                f"{owner_label} has a slide relationship without a target"
            )
        source_target_part = _normalize_part(target, source_owner_part)
        if (
            self_source_part is not None
            and self_output_part is not None
            and source_target_part == self_source_part
        ):
            output_target_part = self_output_part
        else:
            output_targets = outputs_by_source_part.get(source_target_part, [])
            source_target_ref = source_ref_by_part.get(source_target_part)
            target_label = (
                f"source slide {source_target_ref.index}"
                if source_target_ref is not None
                else source_target_part
            )
            if not output_targets:
                raise RuntimeError(
                    f"{owner_label} links to omitted {target_label}; "
                    "include the target exactly once or remove the link"
                )
            if len(output_targets) > 1:
                raise RuntimeError(
                    f"{owner_label} links to repeated {target_label}; "
                    "the output target is ambiguous"
                )
            output_target_part = output_targets[0]
        output_target = _relative_target(output_owner_part, output_target_part)
        if rel.attrib.get("Target") != output_target:
            rel.set("Target", output_target)
            changed = True
    return changed


def _remap_reachable_shared_layer_slide_jumps(
    entries: dict[str, bytes],
    clone_roster: list[_PlannedSlideClone],
    *,
    outputs_by_source_part: dict[str, list[str]],
    source_ref_by_part: dict[str, SlideRef],
) -> None:
    """Remap links inherited from layouts and masters used by output slides."""
    pending: list[str] = []
    for clone in clone_roster:
        rels_data = entries.get(clone.rels_name)
        if not rels_data:
            continue
        rels_root = ET.fromstring(rels_data)
        for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
            if rel.attrib.get("Type") != _SLIDE_LAYOUT_REL_TYPE:
                continue
            target = rel.attrib.get("Target")
            if target:
                pending.append(_normalize_part(target, clone.part_name))

    visited: set[str] = set()
    while pending:
        part_name = pending.pop()
        if part_name in visited:
            continue
        visited.add(part_name)
        part_data = entries.get(part_name)
        rels_name = _rels_name_for_part(part_name)
        rels_data = entries.get(rels_name)
        if not part_data or not rels_data:
            continue
        part_root = ET.fromstring(part_data)
        rels_root = ET.fromstring(rels_data)
        changed = _remap_slide_jump_relationships(
            part_root,
            rels_root,
            source_owner_part=part_name,
            output_owner_part=part_name,
            owner_label=part_name,
            outputs_by_source_part=outputs_by_source_part,
            source_ref_by_part=source_ref_by_part,
        )
        if changed:
            entries[rels_name] = _xml_bytes(rels_root)
        for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
            if rel.attrib.get("Type") != _SLIDE_MASTER_REL_TYPE:
                continue
            target = rel.attrib.get("Target")
            if target:
                pending.append(_normalize_part(target, part_name))


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

    clone_roster = _build_clone_roster(
        plan_slides,
        slide_refs,
        next_slide_number=next_slide_number,
        next_rel_number=next_rel_number,
    )
    source_ref_by_part = {ref.part_name: ref for ref in slide_refs.values()}
    outputs_by_source_part: dict[str, list[str]] = {}
    for clone in clone_roster:
        outputs_by_source_part.setdefault(clone.source_ref.part_name, []).append(clone.part_name)

    for clone in clone_roster:
        item = clone.item
        source_slide = clone.source_slide
        source_ref = clone.source_ref
        new_slide_number = clone.slide_number
        new_part = clone.part_name
        new_rels = clone.rels_name
        new_rid = clone.presentation_rid

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
        (
            slide_effect,
            slide_effect_options,
            slide_duration,
            slide_advance,
        ) = _resolve_slide_transition(
            item,
            default_effect=transition,
            default_duration=transition_duration,
        )
        slide_has_auto_advance = _set_slide_transition(
            slide_root,
            effect=slide_effect,
            effect_options=slide_effect_options,
            duration=slide_duration,
            advance_after=slide_advance,
        )
        if slide_advance is not None and slide_has_auto_advance:
            wrote_auto_advance = True

        source_rels = entries.get(source_ref.rels_name)
        slide_rels_root = ET.fromstring(source_rels) if source_rels else _empty_relationships_root()
        _remap_slide_jump_relationships(
            slide_root,
            slide_rels_root,
            source_owner_part=source_ref.part_name,
            output_owner_part=new_part,
            owner_label=f"Source slide {source_slide}",
            outputs_by_source_part=outputs_by_source_part,
            source_ref_by_part=source_ref_by_part,
            self_source_part=source_ref.part_name,
            self_output_part=new_part,
        )
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
            {
                "id": str(next_slide_id + clone.offset),
                _qn(NS["r"], "id"): new_rid,
            },
        )

    _remap_reachable_shared_layer_slide_jumps(
        entries,
        clone_roster,
        outputs_by_source_part=outputs_by_source_part,
        source_ref_by_part=source_ref_by_part,
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
