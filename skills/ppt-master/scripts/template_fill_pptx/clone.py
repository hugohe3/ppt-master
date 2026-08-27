"""apply: deep-clone a cloned slide's structured private dependency parts.

When the same source slide is reused for several output slides (the workflow
lets a fill plan list one ``source_slide`` many times), copying its
relationships verbatim leaves every clone pointing at one shared set of private
parts — custom-data tags, per-slide theme overrides, SmartArt diagrams. The
pages are not really independent: editing one output slide's structure would
bleed into its siblings.

This helper gives each cloned slide its own copy of every *structured* private
dependency (parts that carry an explicit content-type ``Override``) and rewrites
the relationship targets. Cloning is recursive, so a private part's own private
sub-parts (e.g. a diagram data part's drawing) are cloned too.

Two classes of target are deliberately left shared:

* **Shared structure** — slide layout / master / theme / notes master.
* **Binary blobs typed by a ``Default`` extension rule** — media (png / jpeg /
  emf ...) and, for template-fill callers, OLE embeddings. Picture/object edits
  happen in PowerPoint, which mints a new part and repoints only the edited
  shape's relationship, so sharing never bleeds — and it avoids duplicating
  large media when one source page drives many output slides. Deck-level
  round-trip cloning opts embeddings and model3d parts into private cloning.

Charts stay owned by ``chart_fill`` (which clones the chart part together with
its embedded workbook when an edit is applied) and notes slides by ``notes``;
both relationship types are skipped here.
"""

from __future__ import annotations

import copy
import posixpath
import re
import zipfile
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree as ET

from hyperlink_contract import SLIDE_JUMP_ACTION

from .ooxml import (
    CHART_REL_TYPE,
    CT_NS,
    NS,
    NOTES_SLIDE_REL_TYPE,
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
    _add_content_type_override,
    _add_slide_override,
    _content_type_root,
    _empty_relationships_root,
    _max_numeric_rid,
    _prune_unreferenced_parts,
    _relative_target,
)

_REL_TYPE_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"

# Structure shared across every slide: never cloned, target kept as-is. Note that
# ``themeOverride`` is a distinct, per-slide private type and is NOT listed here.
SHARED_REL_TYPES = frozenset(
    _REL_TYPE_BASE + name
    for name in ("slideLayout", "slideMaster", "notesMaster", "theme", "presProps", "viewProps", "tableStyles")
)

# Owned by other apply stages (chart_fill / notes) or a back-reference: skipped here.
SKIPPED_REL_TYPES = frozenset({CHART_REL_TYPE, NOTES_SLIDE_REL_TYPE, SLIDE_REL_TYPE})


def _make_part_allocator(entries: dict[str, bytes]) -> Callable[[str], str]:
    """Return a function that mints a fresh part name beside a source part.

    Names keep the source extension (so a content-type ``Default`` still covers
    media) and are unique against both existing entries and earlier allocations.
    """
    used = set(entries)

    def allocate(source_part: str) -> str:
        directory = posixpath.dirname(source_part)
        stem, ext = posixpath.splitext(posixpath.basename(source_part))
        index = 1
        while True:
            candidate = posixpath.join(directory, f"{stem}_tf{index}{ext}")
            if candidate not in used:
                used.add(candidate)
                return candidate
            index += 1

    return allocate


def _override_content_type(content_root: ET.Element, part: str) -> str | None:
    """Return the part's explicit content-type ``Override``, or ``None``.

    ``None`` means the part is typed by a ``Default`` extension rule — i.e. a
    binary blob (media / OLE) we deliberately keep shared rather than clone.
    """
    part_pn = "/" + part.lstrip("/")
    for override in content_root.findall(_qn(CT_NS, "Override")):
        if override.attrib.get("PartName") == part_pn:
            return override.attrib.get("ContentType")
    return None


def _is_shared(rel_type: str | None) -> bool:
    return bool(rel_type) and rel_type in SHARED_REL_TYPES


def _clone_part_private_deps(
    rels_root: ET.Element,
    *,
    owner_part: str,
    entries: dict[str, bytes],
    content_root: ET.Element,
    allocate: Callable[[str], str],
    cloned: dict[str, str],
    skipped_rel_types: frozenset[str],
    clone_default_part_prefixes: tuple[str, ...],
    back_references: dict[str, str],
) -> None:
    """Rewrite ``rels_root`` in place, cloning each private target it references.

    ``cloned`` maps an already-handled source part to its clone so a single slide
    that references the same asset twice reuses one copy.
    """
    for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
        if rel.attrib.get("TargetMode") == "External":
            continue
        rel_type = rel.attrib.get("Type")
        target = rel.attrib.get("Target")
        if not target:
            continue
        source_part = _normalize_part(target, owner_part)
        back_reference = back_references.get(source_part)
        if rel_type == SLIDE_REL_TYPE and back_reference is not None:
            rel.set("Target", _relative_target(owner_part, back_reference))
            continue
        if _is_shared(rel_type) or rel_type in skipped_rel_types:
            continue
        if source_part not in entries:
            continue
        content_type = _override_content_type(content_root, source_part)
        clone_default_part = any(
            source_part.startswith(prefix)
            for prefix in clone_default_part_prefixes
        )
        if content_type is None and not clone_default_part:
            # Binary blob typed by a Default extension rule (media / OLE): keep
            # it shared. See the module docstring for why this never bleeds.
            continue

        new_part = cloned.get(source_part)
        if new_part is None:
            new_part = allocate(source_part)
            entries[new_part] = entries[source_part]
            cloned[source_part] = new_part
            if content_type is not None:
                _add_content_type_override(content_root, new_part, content_type)

            sub_rels_data = entries.get(_rels_name_for_part(source_part))
            if sub_rels_data:
                sub_rels_root = ET.fromstring(sub_rels_data)
                _clone_part_private_deps(
                    sub_rels_root,
                    owner_part=new_part,
                    entries=entries,
                    content_root=content_root,
                    allocate=allocate,
                    cloned=cloned,
                    skipped_rel_types=skipped_rel_types,
                    clone_default_part_prefixes=clone_default_part_prefixes,
                    back_references=back_references,
                )
                entries[_rels_name_for_part(new_part)] = _xml_bytes(sub_rels_root)

        rel.set("Target", _relative_target(owner_part, new_part))


def deep_clone_slide_private_parts(
    slide_rels_root: ET.Element,
    *,
    new_slide_part: str,
    entries: dict[str, bytes],
    content_root: ET.Element,
    allocate: Callable[[str], str],
    skipped_rel_types: frozenset[str] = SKIPPED_REL_TYPES,
    clone_default_part_prefixes: tuple[str, ...] = (),
    back_references: dict[str, str] | None = None,
) -> None:
    """Give one cloned slide private copies of its private dependency parts.

    Mutates ``slide_rels_root`` (rewriting targets) and ``entries`` (adding the
    cloned parts and their content-type overrides). ``allocate`` is shared across
    every slide in the run so minted names never collide.
    """
    _clone_part_private_deps(
        slide_rels_root,
        owner_part=new_slide_part,
        entries=entries,
        content_root=content_root,
        allocate=allocate,
        cloned={},
        skipped_rel_types=skipped_rel_types,
        clone_default_part_prefixes=clone_default_part_prefixes,
        back_references=back_references or {},
    )


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
    fail_on_non_jump_slide_relationships: bool = False,
) -> bool:
    """Point referenced slide-jump relationships at final output slides."""
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

    if fail_on_non_jump_slide_relationships:
        for relationship_id, rel in sorted(relationships.items()):
            if (
                relationship_id in relationship_ids
                or rel.attrib.get("Type") != SLIDE_REL_TYPE
            ):
                continue
            if rel.attrib.get("TargetMode") == "External":
                raise RuntimeError(
                    f"{owner_label} has external non-jump slide relationship "
                    f"{relationship_id!r}; page-plan export refuses slide "
                    "relationships without a slide-jump action"
                )
            target = rel.attrib.get("Target")
            if not target:
                raise RuntimeError(
                    f"{owner_label} has non-jump slide relationship "
                    f"{relationship_id!r} without a target"
                )
            source_target_part = _normalize_part(target, source_owner_part)
            source_target_ref = source_ref_by_part.get(source_target_part)
            target_label = (
                f"source slide {source_target_ref.index}"
                if source_target_ref is not None
                else source_target_part
            )
            if (
                self_source_part is not None
                and self_output_part is not None
                and source_target_part == self_source_part
            ):
                output_targets = [self_output_part]
            else:
                output_targets = outputs_by_source_part.get(
                    source_target_part,
                    [],
                )
            if not output_targets:
                raise RuntimeError(
                    f"{owner_label} has non-jump slide relationship "
                    f"{relationship_id!r} to omitted {target_label}; "
                    "page-plan export refuses slide relationships without a "
                    "slide-jump action"
                )
            if len(output_targets) > 1:
                raise RuntimeError(
                    f"{owner_label} has non-jump slide relationship "
                    f"{relationship_id!r} to repeated {target_label}; "
                    "the output target is ambiguous"
                )
            output_target = _relative_target(
                output_owner_part,
                output_targets[0],
            )
            if rel.attrib.get("Target") != output_target:
                raise RuntimeError(
                    f"{owner_label} has non-jump slide relationship "
                    f"{relationship_id!r} to {target_label} that would require "
                    "retargeting after page planning; page-plan export refuses "
                    "slide relationships without a slide-jump action"
                )
    return changed


def _remap_reachable_shared_layer_slide_jumps(
    entries: dict[str, bytes],
    output_slides: list[tuple[str, str]],
    *,
    outputs_by_source_part: dict[str, list[str]],
    source_ref_by_part: dict[str, SlideRef],
    fail_on_non_jump_slide_relationships: bool = False,
) -> None:
    """Remap links inherited from layouts and masters used by output slides."""
    pending: list[str] = []
    for part_name, rels_name in output_slides:
        rels_data = entries.get(rels_name)
        if not rels_data:
            continue
        rels_root = ET.fromstring(rels_data)
        for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
            if rel.attrib.get("Type") != _SLIDE_LAYOUT_REL_TYPE:
                continue
            target = rel.attrib.get("Target")
            if target:
                pending.append(_normalize_part(target, part_name))

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
            fail_on_non_jump_slide_relationships=(
                fail_on_non_jump_slide_relationships
            ),
        )
        if changed:
            entries[rels_name] = _xml_bytes(rels_root)
        for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
            if rel.attrib.get("Type") != _SLIDE_MASTER_REL_TYPE:
                continue
            target = rel.attrib.get("Target")
            if target:
                pending.append(_normalize_part(target, part_name))


def _remove_stale_slide_order_metadata(presentation_root: ET.Element) -> None:
    """Drop source-only custom-show and section rosters after page planning."""
    custom_shows = presentation_root.find("p:custShowLst", NS)
    if custom_shows is not None:
        presentation_root.remove(custom_shows)
    for extension_list in presentation_root.findall(".//p:extLst", NS):
        for extension in list(extension_list):
            if any(
                isinstance(child.tag, str)
                and child.tag.rsplit("}", 1)[-1] == "sectionLst"
                for child in extension.iter()
            ):
                extension_list.remove(extension)


def _update_app_slide_count(entries: dict[str, bytes], slide_count: int) -> None:
    app_part = "docProps/app.xml"
    payload = entries.get(app_part)
    if payload is None:
        return
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return
    entries[app_part] = re.sub(
        r"<Slides>.*?</Slides>",
        f"<Slides>{slide_count}</Slides>",
        text,
        count=1,
    ).encode("utf-8")


def clone_presentation_slides(
    source_pptx: Path,
    source_slides: tuple[int, ...],
    output_path: Path,
    *,
    package_overrides: dict[str, bytes] | None = None,
) -> None:
    """Clone an ordered source-slide roster into canonical output slide parts.

    Structured private dependencies, including notes, charts, diagrams, and
    embeddings, are cloned per output page. Shared layout/master/theme parts and
    ordinary media remain shared. Same-deck hyperlinks use the template-fill
    omitted/ambiguous destination contract.
    """
    if not source_slides:
        raise RuntimeError("Round-trip page plan must contain at least one slide")
    with zipfile.ZipFile(source_pptx) as archive:
        entries = {
            info.filename: archive.read(info.filename)
            for info in archive.infolist()
            if not info.is_dir()
        }
        slide_refs = {
            slide.index: slide
            for slide in _parse_slide_refs(archive)
        }
    for part_name, payload in (package_overrides or {}).items():
        if part_name not in entries:
            raise RuntimeError(
                f"Round-trip resource override names a missing source part: {part_name}"
            )
        entries[part_name] = payload

    missing = sorted(set(source_slides) - set(slide_refs))
    if missing:
        raise RuntimeError(
            "Round-trip page plan references missing source slide(s): "
            + ", ".join(str(index) for index in missing)
        )

    presentation_root = ET.fromstring(entries["ppt/presentation.xml"])
    presentation_rels_root = ET.fromstring(
        entries["ppt/_rels/presentation.xml.rels"]
    )
    content_root = _content_type_root(
        ET.fromstring(entries["[Content_Types].xml"])
    )
    slide_list = presentation_root.find("p:sldIdLst", NS)
    if slide_list is None:
        raise RuntimeError("Source presentation.xml has no p:sldIdLst")
    source_slide_ids = {
        entry.attrib.get(_qn(NS["r"], "id"), ""): copy.deepcopy(entry)
        for entry in slide_list.findall("p:sldId", NS)
    }
    for child in list(slide_list):
        slide_list.remove(child)
    for rel in list(
        presentation_rels_root.findall(_qn(REL_NS, "Relationship"))
    ):
        if rel.attrib.get("Type") == SLIDE_REL_TYPE:
            presentation_rels_root.remove(rel)
    _remove_stale_slide_order_metadata(presentation_root)

    next_rid = _max_numeric_rid(presentation_rels_root) + 1
    allocate = _make_part_allocator(entries)
    source_ref_by_part = {
        reference.part_name: reference
        for reference in slide_refs.values()
    }
    output_slides: list[tuple[str, str]] = []
    outputs_by_source_part: dict[str, list[str]] = {}
    for output_index, source_index in enumerate(source_slides, start=1):
        source_ref = slide_refs[source_index]
        output_part = f"ppt/slides/slide{output_index}.xml"
        output_rels = _rels_name_for_part(output_part)
        output_slides.append((output_part, output_rels))
        outputs_by_source_part.setdefault(source_ref.part_name, []).append(
            output_part
        )

    source_entries = dict(entries)
    for output_index, source_index in enumerate(source_slides, start=1):
        source_ref = slide_refs[source_index]
        output_part, output_rels = output_slides[output_index - 1]
        source_slide_xml = source_entries[source_ref.part_name]
        source_rels_xml = source_entries.get(source_ref.rels_name)
        slide_root = ET.fromstring(source_slide_xml)
        relationships_root = (
            ET.fromstring(source_rels_xml)
            if source_rels_xml is not None
            else _empty_relationships_root()
        )
        _remap_slide_jump_relationships(
            slide_root,
            relationships_root,
            source_owner_part=source_ref.part_name,
            output_owner_part=output_part,
            owner_label=f"Source slide {source_index}",
            outputs_by_source_part=outputs_by_source_part,
            source_ref_by_part=source_ref_by_part,
            self_source_part=source_ref.part_name,
            self_output_part=output_part,
            fail_on_non_jump_slide_relationships=True,
        )
        deep_clone_slide_private_parts(
            relationships_root,
            new_slide_part=output_part,
            entries=entries,
            content_root=content_root,
            allocate=allocate,
            skipped_rel_types=frozenset({SLIDE_REL_TYPE}),
            clone_default_part_prefixes=(
                "ppt/embeddings/",
                "ppt/model3d/",
            ),
            back_references={source_ref.part_name: output_part},
        )
        entries[output_part] = source_slide_xml
        entries[output_rels] = _xml_bytes(relationships_root)
        _add_slide_override(content_root, output_part)

        relationship_id = f"rId{next_rid + output_index - 1}"
        ET.SubElement(
            presentation_rels_root,
            _qn(REL_NS, "Relationship"),
            {
                "Id": relationship_id,
                "Type": SLIDE_REL_TYPE,
                "Target": f"slides/slide{output_index}.xml",
            },
        )
        source_slide_id_template = source_slide_ids.get(source_ref.rel_id)
        if source_slide_id_template is None:
            raise RuntimeError(
                f"Source slide {source_index} has no p:sldId entry"
            )
        source_slide_id = copy.deepcopy(source_slide_id_template)
        source_slide_id.set("id", str(255 + output_index))
        source_slide_id.set(_qn(NS["r"], "id"), relationship_id)
        slide_list.append(source_slide_id)

    _remap_reachable_shared_layer_slide_jumps(
        entries,
        output_slides,
        outputs_by_source_part=outputs_by_source_part,
        source_ref_by_part=source_ref_by_part,
        fail_on_non_jump_slide_relationships=True,
    )
    entries["ppt/presentation.xml"] = _xml_bytes(presentation_root)
    entries["ppt/_rels/presentation.xml.rels"] = _xml_bytes(
        presentation_rels_root
    )
    _prune_unreferenced_parts(entries, content_root)
    entries["[Content_Types].xml"] = _xml_bytes(content_root)
    _update_app_slide_count(entries, len(source_slides))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as output:
        for part_name, payload in entries.items():
            output.writestr(part_name, payload)
