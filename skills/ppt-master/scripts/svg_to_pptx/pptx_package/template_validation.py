#!/usr/bin/env python3
"""
PPT Master - Template Package Validation

Read a generated template-mode PPTX back and verify its reusable Layout graph.

Usage:
    Imported by svg_to_pptx.pptx_package.builder.

Examples:
    validate_pptx_template_package(Path("output.pptx"), template_specs)

Dependencies:
    None (only uses standard library and local modules)
"""

from __future__ import annotations

import posixpath
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

if __name__ == "__main__":
    if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]):
        print(__doc__)
        raise SystemExit(0)
    print(
        "Use this validator through the template-mode SVG-to-PPTX exporter.",
        file=sys.stderr,
    )
    raise SystemExit(1)

from ..drawingml.utils import EMU_PER_PX
from .template_structure import (
    OOXML_UINT32_MAX,
    TemplatePlaceholderBinding,
    TemplateSlideSpec,
    TemplateStructureError,
    template_placeholder_bindings,
)


PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SLIDE_LAYOUT_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
)
SLIDE_MASTER_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
)
SLIDE_LAYOUT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"
)
PRESENTATION_COLLECTION_ID_MIN = 1 << 31


@dataclass(frozen=True)
class _Relationship:
    rel_id: str
    rel_type: str
    target: str
    target_mode: str | None


@dataclass(frozen=True)
class _Placeholder:
    shape: ET.Element
    placeholder_type: str
    raw_type: str | None
    idx: int
    raw_idx: int | None


class _PackageReader:
    """Cache package XML while accumulating deterministic read-back errors."""

    def __init__(self, package: zipfile.ZipFile, errors: list[str]) -> None:
        self.package = package
        self.errors = errors
        self.names = frozenset(package.namelist())
        self._xml_cache: dict[str, ET.Element | None] = {}
        self._rels_cache: dict[str, tuple[_Relationship, ...]] = {}

    def xml(self, part: str) -> ET.Element | None:
        if part in self._xml_cache:
            return self._xml_cache[part]
        if part not in self.names:
            self.errors.append(f"missing package part {part}")
            self._xml_cache[part] = None
            return None
        try:
            root = ET.fromstring(self.package.read(part))
        except (KeyError, ET.ParseError) as exc:
            self.errors.append(f"{part} is not valid XML: {exc}")
            root = None
        self._xml_cache[part] = root
        return root

    def relationships(self, source_part: str) -> tuple[_Relationship, ...]:
        if source_part in self._rels_cache:
            return self._rels_cache[source_part]
        rels_part = _relationships_part_for(source_part)
        root = self.xml(rels_part)
        relationships: list[_Relationship] = []
        seen_ids: set[str] = set()
        if root is not None:
            for elem in root:
                attrs = {
                    key.rsplit("}", 1)[-1]: value
                    for key, value in elem.attrib.items()
                }
                rel_id = attrs.get("Id", "")
                rel_type = attrs.get("Type", "")
                target = attrs.get("Target", "")
                if not rel_id or not rel_type or not target:
                    self.errors.append(
                        f"{rels_part} contains a relationship without Id, Type, or Target"
                    )
                    continue
                if rel_id in seen_ids:
                    self.errors.append(f"{rels_part} repeats relationship id {rel_id}")
                    continue
                seen_ids.add(rel_id)
                relationships.append(_Relationship(
                    rel_id=rel_id,
                    rel_type=rel_type,
                    target=target,
                    target_mode=attrs.get("TargetMode"),
                ))
        result = tuple(relationships)
        self._rels_cache[source_part] = result
        return result


def _relationships_part_for(source_part: str) -> str:
    directory = posixpath.dirname(source_part)
    filename = posixpath.basename(source_part)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def _resolve_relationship_target(
    source_part: str,
    relationship: _Relationship,
    errors: list[str],
    context: str,
) -> str | None:
    target_mode = (relationship.target_mode or "Internal").lower()
    if target_mode != "internal":
        errors.append(f"{context} relationship must be internal")
        return None
    raw_target = relationship.target
    if "\\" in raw_target or any(ord(char) <= 0x20 for char in raw_target):
        errors.append(f"{context} has invalid target {raw_target!r}")
        return None
    try:
        parsed = urlsplit(raw_target)
    except ValueError:
        errors.append(f"{context} has invalid target {raw_target!r}")
        return None
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        errors.append(f"{context} has invalid target {raw_target!r}")
        return None
    decoded = unquote(parsed.path)
    if not decoded:
        errors.append(f"{context} has an empty target")
        return None
    if decoded.startswith("/"):
        candidate = decoded[1:]
    else:
        candidate = posixpath.join(posixpath.dirname(source_part), decoded)
    normalized = posixpath.normpath(candidate)
    if (
        normalized in {"", ".", ".."}
        or normalized.startswith("../")
        or normalized.startswith("/")
    ):
        errors.append(f"{context} target escapes the package: {raw_target!r}")
        return None
    return normalized


def _single_relationship_target(
    reader: _PackageReader,
    source_part: str,
    rel_type: str,
    context: str,
) -> tuple[_Relationship, str] | None:
    matches = [
        relationship
        for relationship in reader.relationships(source_part)
        if relationship.rel_type == rel_type
    ]
    if len(matches) != 1:
        reader.errors.append(
            f"{context} must have exactly one {rel_type.rsplit('/', 1)[-1]} "
            f"relationship, found {len(matches)}"
        )
        return None
    target = _resolve_relationship_target(
        source_part,
        matches[0],
        reader.errors,
        context,
    )
    if target is None:
        return None
    return matches[0], target


def _placeholder_for_shape(shape: ET.Element) -> ET.Element | None:
    paths = {
        f"{{{PML_NS}}}sp": (
            f"{{{PML_NS}}}nvSpPr/{{{PML_NS}}}nvPr/{{{PML_NS}}}ph"
        ),
        f"{{{PML_NS}}}pic": (
            f"{{{PML_NS}}}nvPicPr/{{{PML_NS}}}nvPr/{{{PML_NS}}}ph"
        ),
        f"{{{PML_NS}}}graphicFrame": (
            f"{{{PML_NS}}}nvGraphicFramePr/{{{PML_NS}}}nvPr/{{{PML_NS}}}ph"
        ),
    }
    path = paths.get(shape.tag)
    return shape.find(path) if path else None


def _read_placeholders(
    root: ET.Element,
    context: str,
    errors: list[str],
) -> dict[int, _Placeholder]:
    sp_tree = root.find(f"{{{PML_NS}}}cSld/{{{PML_NS}}}spTree")
    if sp_tree is None:
        errors.append(f"{context} has no p:cSld/p:spTree")
        return {}
    placeholders: dict[int, _Placeholder] = {}
    for shape in sp_tree:
        ph = _placeholder_for_shape(shape)
        if ph is None:
            continue
        raw_idx_value = ph.get("idx")
        try:
            raw_idx = int(raw_idx_value) if raw_idx_value is not None else None
        except ValueError:
            errors.append(f"{context} contains invalid placeholder idx {raw_idx_value!r}")
            continue
        idx = raw_idx if raw_idx is not None else 0
        if not 0 <= idx <= OOXML_UINT32_MAX:
            errors.append(
                f"{context} placeholder idx {idx} is outside the OOXML UInt32 range"
            )
            continue
        if idx in placeholders:
            errors.append(f"{context} repeats effective placeholder idx {idx}")
            continue
        raw_type = ph.get("type")
        placeholders[idx] = _Placeholder(
            shape=shape,
            placeholder_type=raw_type or "obj",
            raw_type=raw_type,
            idx=idx,
            raw_idx=raw_idx,
        )
    return placeholders


def _validate_placeholder_roster(
    root: ET.Element,
    bindings: tuple[TemplatePlaceholderBinding, ...],
    context: str,
    errors: list[str],
    *,
    is_layout: bool,
) -> dict[int, _Placeholder]:
    actual = _read_placeholders(root, context, errors)
    expected = {binding.effective_idx: binding for binding in bindings}
    if set(actual) != set(expected):
        errors.append(
            f"{context} placeholder idx roster is {sorted(actual)}, "
            f"expected {sorted(expected)}"
        )
    for idx in sorted(set(actual).intersection(expected)):
        placeholder = actual[idx]
        binding = expected[idx]
        if placeholder.placeholder_type != binding.placeholder_type:
            errors.append(
                f"{context} placeholder idx {idx} has type "
                f"{placeholder.placeholder_type!r}, expected "
                f"{binding.placeholder_type!r}"
            )
        if binding.assigned_idx is None:
            if placeholder.raw_idx is not None:
                errors.append(
                    f"{context} title placeholder must use the omitted idx=0 form"
                )
        elif placeholder.raw_idx != binding.assigned_idx:
            errors.append(
                f"{context} placeholder idx {idx} must serialize explicit idx "
                f"{binding.assigned_idx}"
            )
        if is_layout and placeholder.raw_type is None:
            errors.append(
                f"{context} Layout placeholder idx {idx} must serialize its type"
            )
        if (
            not is_layout
            and binding.placeholder_type != "obj"
            and placeholder.raw_type is None
        ):
            errors.append(
                f"{context} Slide placeholder idx {idx} must serialize type "
                f"{binding.placeholder_type!r}"
            )
    return actual


def _validate_layout_header_footer(
    root: ET.Element,
    bindings: tuple[TemplatePlaceholderBinding, ...],
    context: str,
    errors: list[str],
) -> None:
    placeholder_roles = {
        binding.element.placeholder for binding in bindings
    }
    expected = {
        "hdr": False,
        "dt": "date" in placeholder_roles,
        "ftr": "footer" in placeholder_roles,
        "sldNum": "slide-number" in placeholder_roles,
    }
    header_footer = root.find(f"{{{PML_NS}}}hf")
    if header_footer is None:
        if any(expected.values()):
            errors.append(
                f"{context} has date/footer/slide-number placeholders but no p:hf"
            )
        return
    for attr, expected_value in expected.items():
        # CT_HeaderFooter boolean attributes default to true when omitted.
        raw_value = header_footer.get(attr, "1").lower()
        if raw_value not in {"0", "1", "false", "true"}:
            errors.append(f"{context} p:hf@{attr} is not a valid boolean")
            continue
        actual_value = raw_value in {"1", "true"}
        if actual_value != expected_value:
            errors.append(
                f"{context} p:hf@{attr} is {raw_value!r}, expected "
                f"{'1' if expected_value else '0'}"
            )


def _shape_bounds(
    shape: ET.Element,
    context: str,
    errors: list[str],
) -> tuple[int, int, int, int] | None:
    if shape.tag == f"{{{PML_NS}}}graphicFrame":
        xfrm = shape.find(f"{{{PML_NS}}}xfrm")
    else:
        xfrm = shape.find(f"{{{PML_NS}}}spPr/{{{DML_NS}}}xfrm")
    if xfrm is None:
        errors.append(f"{context} has no direct placeholder transform")
        return None
    off = xfrm.find(f"{{{DML_NS}}}off")
    ext = xfrm.find(f"{{{DML_NS}}}ext")
    if off is None or ext is None:
        errors.append(f"{context} placeholder transform has no a:off/a:ext")
        return None
    try:
        bounds = (
            int(off.attrib["x"]),
            int(off.attrib["y"]),
            int(ext.attrib["cx"]),
            int(ext.attrib["cy"]),
        )
    except (KeyError, ValueError):
        errors.append(f"{context} placeholder transform is invalid")
        return None
    if bounds[2] <= 0 or bounds[3] <= 0:
        errors.append(f"{context} placeholder width/height must be positive")
    return bounds


def _direct_text_body(shape: ET.Element) -> ET.Element | None:
    return shape.find(f"{{{PML_NS}}}txBody")


def _first_run_size(shape: ET.Element) -> str | None:
    text_body = _direct_text_body(shape)
    if text_body is None:
        return None
    run_props = text_body.find(f".//{{{DML_NS}}}rPr")
    return run_props.get("sz") if run_props is not None else None


def _level_one_default_size(shape: ET.Element) -> str | None:
    text_body = _direct_text_body(shape)
    if text_body is None:
        return None
    default_props = text_body.find(
        f"{{{DML_NS}}}lstStyle/"
        f"{{{DML_NS}}}lvl1pPr/"
        f"{{{DML_NS}}}defRPr"
    )
    return default_props.get("sz") if default_props is not None else None


def _content_type_overrides(
    reader: _PackageReader,
) -> dict[str, list[str]]:
    root = reader.xml("[Content_Types].xml")
    overrides: dict[str, list[str]] = {}
    if root is None:
        return overrides
    for elem in root:
        if elem.tag.rsplit("}", 1)[-1] != "Override":
            continue
        part_name = elem.get("PartName", "")
        content_type = elem.get("ContentType", "")
        if part_name and content_type:
            overrides.setdefault(part_name, []).append(content_type)
    return overrides


def _validate_uint32_id_roster(
    elements: list[ET.Element],
    context: str,
    errors: list[str],
    *,
    min_value: int = 0,
) -> set[int]:
    values: set[int] = set()
    for element in elements:
        raw_value = element.get("id")
        try:
            value = int(raw_value) if raw_value is not None else -1
        except ValueError:
            value = -1
        if not min_value <= value <= OOXML_UINT32_MAX:
            errors.append(
                f"{context} contains id {raw_value!r} outside the OOXML range "
                f"{min_value}..{OOXML_UINT32_MAX}"
            )
            continue
        if value in values:
            errors.append(f"{context} repeats numeric id {value}")
            continue
        values.add(value)
    return values


def _validate_registered_part_roster(
    reader: _PackageReader,
    source_part: str,
    rel_type: str,
    entries: list[ET.Element],
    expected_targets: set[str],
    context: str,
) -> set[int]:
    relationships = [
        relationship
        for relationship in reader.relationships(source_part)
        if relationship.rel_type == rel_type
    ]
    targets_by_id: dict[str, str] = {}
    ids_by_target: dict[str, list[str]] = {}
    for relationship in relationships:
        target = _resolve_relationship_target(
            source_part,
            relationship,
            reader.errors,
            context,
        )
        if target is None:
            continue
        targets_by_id[relationship.rel_id] = target
        ids_by_target.setdefault(target, []).append(relationship.rel_id)
    for target, rel_ids in sorted(ids_by_target.items()):
        if len(rel_ids) > 1:
            reader.errors.append(
                f"{context} targets {target} through multiple relationships: "
                + ", ".join(rel_ids)
            )

    actual_targets = set(targets_by_id.values())
    if actual_targets != expected_targets:
        missing = sorted(expected_targets - actual_targets)
        extra = sorted(actual_targets - expected_targets)
        reader.errors.append(
            f"{context} registered target roster differs; missing={missing}, "
            f"extra={extra}"
        )

    entry_rel_ids: list[str] = []
    for entry in entries:
        rel_id = entry.get(f"{{{REL_NS}}}id")
        if not rel_id:
            reader.errors.append(f"{context} contains an entry without r:id")
            continue
        entry_rel_ids.append(rel_id)
    if len(entry_rel_ids) != len(set(entry_rel_ids)):
        reader.errors.append(f"{context} repeats an entry r:id")
    if set(entry_rel_ids) != {relationship.rel_id for relationship in relationships}:
        reader.errors.append(
            f"{context} entry r:id roster does not match its relationships"
        )
    return _validate_uint32_id_roster(
        entries,
        context,
        reader.errors,
        min_value=PRESENTATION_COLLECTION_ID_MIN,
    )


def _validate_presentation_master_registration(
    reader: _PackageReader,
    master_parts: set[str],
) -> None:
    presentation_part = "ppt/presentation.xml"
    presentation_root = reader.xml(presentation_part)
    if presentation_root is None:
        return
    master_id_entries = presentation_root.findall(
        f"{{{PML_NS}}}sldMasterIdLst/{{{PML_NS}}}sldMasterId"
    )
    _validate_registered_part_roster(
        reader,
        presentation_part,
        SLIDE_MASTER_REL_TYPE,
        master_id_entries,
        master_parts,
        "Presentation p:sldMasterIdLst",
    )


def validate_pptx_template_package(
    pptx_path: str | Path,
    specs: list[TemplateSlideSpec],
) -> None:
    """Validate a finished template-mode PPTX against its explicit SVG contract."""
    if not specs:
        raise ValueError("template package validation requires at least one slide spec")

    specs_by_layout: dict[str, list[TemplateSlideSpec]] = {}
    bindings_by_layout: dict[str, tuple[TemplatePlaceholderBinding, ...]] = {}
    try:
        for spec in specs:
            specs_by_layout.setdefault(spec.layout_key, []).append(spec)
        for layout_key, layout_specs in specs_by_layout.items():
            bindings_by_layout[layout_key] = template_placeholder_bindings(
                layout_specs[0]
            )
    except TemplateStructureError as exc:
        raise ValueError(str(exc)) from exc

    errors: list[str] = []
    path = Path(pptx_path)
    try:
        with zipfile.ZipFile(path) as package:
            reader = _PackageReader(package, errors)
            overrides = _content_type_overrides(reader)
            layout_parts_by_key: dict[str, str] = {}
            keys_by_layout_part: dict[str, str] = {}
            slide_roots: dict[int, ET.Element] = {}

            for spec in specs:
                slide_part = f"ppt/slides/slide{spec.slide_num}.xml"
                slide_root = reader.xml(slide_part)
                if slide_root is not None:
                    slide_roots[spec.slide_num] = slide_root
                relationship_target = _single_relationship_target(
                    reader,
                    slide_part,
                    SLIDE_LAYOUT_REL_TYPE,
                    f"Slide {spec.slide_num}",
                )
                if relationship_target is None:
                    continue
                _relationship, layout_part = relationship_target
                if not (
                    layout_part.startswith("ppt/slideLayouts/")
                    and layout_part.endswith(".xml")
                ):
                    errors.append(
                        f"Slide {spec.slide_num} targets non-Layout part {layout_part}"
                    )
                    continue
                reader.xml(layout_part)
                previous_part = layout_parts_by_key.setdefault(
                    spec.layout_key,
                    layout_part,
                )
                if previous_part != layout_part:
                    errors.append(
                        f"layout key {spec.layout_key!r} targets both {previous_part} "
                        f"and {layout_part}"
                    )
                previous_key = keys_by_layout_part.setdefault(
                    layout_part,
                    spec.layout_key,
                )
                if previous_key != spec.layout_key:
                    errors.append(
                        f"layout keys {previous_key!r} and {spec.layout_key!r} both "
                        f"target {layout_part}"
                    )

            used_master_parts: set[str] = set()
            layout_parts_by_master: dict[str, set[str]] = {}
            for layout_key, layout_specs in specs_by_layout.items():
                layout_part = layout_parts_by_key.get(layout_key)
                if layout_part is None:
                    errors.append(f"layout key {layout_key!r} has no resolved Layout part")
                    continue
                layout_root = reader.xml(layout_part)
                if layout_root is None:
                    continue
                if layout_root.tag != f"{{{PML_NS}}}sldLayout":
                    errors.append(f"{layout_part} is not a p:sldLayout part")
                if layout_root.get("type") != "cust":
                    errors.append(f"{layout_part} must have type='cust'")
                if layout_root.get("preserve") != "1":
                    errors.append(f"{layout_part} must have preserve='1'")
                if layout_root.get("showMasterSp", "1").lower() not in {
                    "1",
                    "true",
                }:
                    errors.append(f"{layout_part} must show its Master shape tree")
                c_sld = layout_root.find(f"{{{PML_NS}}}cSld")
                expected_name = layout_specs[0].layout_name
                actual_name = c_sld.get("name") if c_sld is not None else None
                if actual_name != expected_name:
                    errors.append(
                        f"{layout_part} has picker name {actual_name!r}, expected "
                        f"{expected_name!r}"
                    )

                override_values = overrides.get(f"/{layout_part}", [])
                if override_values != [SLIDE_LAYOUT_CONTENT_TYPE]:
                    errors.append(
                        f"[Content_Types].xml must declare {layout_part} exactly once "
                        f"as {SLIDE_LAYOUT_CONTENT_TYPE}"
                    )

                bindings = bindings_by_layout[layout_key]
                layout_placeholders = _validate_placeholder_roster(
                    layout_root,
                    bindings,
                    f"Layout {layout_key!r}",
                    errors,
                    is_layout=True,
                )
                _validate_layout_header_footer(
                    layout_root,
                    bindings,
                    f"Layout {layout_key!r}",
                    errors,
                )
                slide_placeholders: dict[int, dict[int, _Placeholder]] = {}
                for spec in layout_specs:
                    slide_root = slide_roots.get(spec.slide_num)
                    if slide_root is None:
                        continue
                    slide_placeholders[spec.slide_num] = _validate_placeholder_roster(
                        slide_root,
                        bindings,
                        f"Slide {spec.slide_num}",
                        errors,
                        is_layout=False,
                    )

                prototype = layout_specs[0]
                prototype_placeholders = slide_placeholders.get(
                    prototype.slide_num,
                    {},
                )
                for binding in bindings:
                    idx = binding.effective_idx
                    layout_placeholder = layout_placeholders.get(idx)
                    prototype_placeholder = prototype_placeholders.get(idx)
                    if layout_placeholder is None or prototype_placeholder is None:
                        continue
                    context = (
                        f"Layout {layout_key!r} placeholder "
                        f"{binding.element.element_id!r}"
                    )
                    actual_bounds = _shape_bounds(
                        layout_placeholder.shape,
                        context,
                        errors,
                    )
                    if binding.element.placeholder_bounds is not None:
                        expected_bounds = tuple(
                            round(value * EMU_PER_PX)
                            for value in binding.element.placeholder_bounds
                        )
                    else:
                        expected_bounds = _shape_bounds(
                            prototype_placeholder.shape,
                            f"Slide {prototype.slide_num} placeholder "
                            f"{binding.element.element_id!r}",
                            errors,
                        )
                    if (
                        actual_bounds is not None
                        and expected_bounds is not None
                        and actual_bounds != expected_bounds
                    ):
                        errors.append(
                            f"{context} bounds are {actual_bounds}, expected "
                            f"{expected_bounds}"
                        )

                    prototype_size = _first_run_size(prototype_placeholder.shape)
                    if prototype_size is not None:
                        prompt_size = _first_run_size(layout_placeholder.shape)
                        if prompt_size != prototype_size:
                            errors.append(
                                f"{context} prompt size is {prompt_size!r}, expected "
                                f"{prototype_size!r}"
                            )
                        default_size = _level_one_default_size(
                            layout_placeholder.shape
                        )
                        if default_size != prototype_size:
                            errors.append(
                                f"{context} level-1 default size is "
                                f"{default_size!r}, expected {prototype_size!r}"
                            )

                master_target = _single_relationship_target(
                    reader,
                    layout_part,
                    SLIDE_MASTER_REL_TYPE,
                    f"Layout {layout_key!r}",
                )
                if master_target is None:
                    continue
                _relationship, master_part = master_target
                if not (
                    master_part.startswith("ppt/slideMasters/")
                    and master_part.endswith(".xml")
                ):
                    errors.append(
                        f"Layout {layout_key!r} targets non-Master part {master_part}"
                    )
                    continue
                reader.xml(master_part)
                used_master_parts.add(master_part)
                layout_parts_by_master.setdefault(master_part, set()).add(
                    layout_part
                )

            layout_id_owners: dict[int, str] = {}
            for master_part, layout_parts in sorted(layout_parts_by_master.items()):
                master_root = reader.xml(master_part)
                if master_root is None:
                    continue
                layout_id_entries = master_root.findall(
                    f"{{{PML_NS}}}sldLayoutIdLst/"
                    f"{{{PML_NS}}}sldLayoutId"
                )
                layout_ids = _validate_registered_part_roster(
                    reader,
                    master_part,
                    SLIDE_LAYOUT_REL_TYPE,
                    layout_id_entries,
                    layout_parts,
                    f"Master {master_part} p:sldLayoutIdLst",
                )
                for layout_id in sorted(layout_ids):
                    previous_owner = layout_id_owners.setdefault(
                        layout_id,
                        master_part,
                    )
                    if previous_owner != master_part:
                        errors.append(
                            f"Slide Layout numeric id {layout_id} appears in both "
                            f"{previous_owner} and {master_part}"
                        )

            _validate_presentation_master_registration(reader, used_master_parts)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot read template PPTX package {path}: {exc}") from exc

    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"template package read-back failed:\n{details}")
