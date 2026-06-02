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
  emf ...) and OLE embeddings. Picture/object edits happen in PowerPoint, which
  mints a new part and repoints only the edited shape's relationship, so sharing
  never bleeds — and it avoids duplicating large media when one source page
  drives many output slides.

Charts stay owned by ``chart_fill`` (which clones the chart part together with
its embedded workbook when an edit is applied) and notes slides by ``notes``;
both relationship types are skipped here.
"""

from __future__ import annotations

import posixpath
from typing import Callable
from xml.etree import ElementTree as ET

from .ooxml import (
    CHART_REL_TYPE,
    CT_NS,
    NOTES_SLIDE_REL_TYPE,
    REL_NS,
    SLIDE_REL_TYPE,
    _normalize_part,
    _qn,
    _rels_name_for_part,
    _xml_bytes,
)
from .package import _add_content_type_override, _relative_target

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
) -> None:
    """Rewrite ``rels_root`` in place, cloning each private target it references.

    ``cloned`` maps an already-handled source part to its clone so a single slide
    that references the same asset twice reuses one copy.
    """
    for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
        if rel.attrib.get("TargetMode") == "External":
            continue
        rel_type = rel.attrib.get("Type")
        if _is_shared(rel_type) or rel_type in SKIPPED_REL_TYPES:
            continue
        target = rel.attrib.get("Target")
        if not target:
            continue
        source_part = _normalize_part(target, owner_part)
        if source_part not in entries:
            continue
        content_type = _override_content_type(content_root, source_part)
        if content_type is None:
            # Binary blob typed by a Default extension rule (media / OLE): keep
            # it shared. See the module docstring for why this never bleeds.
            continue

        new_part = cloned.get(source_part)
        if new_part is None:
            new_part = allocate(source_part)
            entries[new_part] = entries[source_part]
            cloned[source_part] = new_part
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
    )
