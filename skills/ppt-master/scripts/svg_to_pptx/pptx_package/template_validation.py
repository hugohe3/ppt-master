#!/usr/bin/env python3
"""
PPT Master - Template Package Validation

Read a generated structured PPTX back and verify its reusable Master/Layout graph.

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
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

if __name__ == "__main__":
    if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]):
        print(__doc__)
        raise SystemExit(0)
    print(
        "Use this validator through the structured SVG-to-PPTX exporter.",
        file=sys.stderr,
    )
    raise SystemExit(1)

from ..drawingml.utils import EMU_PER_PX
from .template_structure import (
    OOXML_UINT32_MAX,
    TemplatePlaceholderBinding,
    TemplateSlideSpec,
    TemplateStructureError,
    is_proxy_placeholder,
    template_placeholder_bindings,
)


PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
SLIDE_LAYOUT_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
)
SLIDE_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
)
SLIDE_MASTER_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
)
THEME_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
)
SLIDE_LAYOUT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"
)
SLIDE_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
)
SLIDE_MASTER_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"
)
PRESENTATION_COLLECTION_ID_MIN = 1 << 31
PRESENTATION_SLIDE_ID_MIN = 256
_TOP_LEVEL_VISIBLE_TAGS = frozenset({
    f"{{{PML_NS}}}sp",
    f"{{{PML_NS}}}pic",
    f"{{{PML_NS}}}graphicFrame",
    f"{{{PML_NS}}}grpSp",
    f"{{{PML_NS}}}cxnSp",
})


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


def _validate_unique_creation_ids(
    reader: _PackageReader,
    parts: set[str],
) -> None:
    """Reject cloned PowerPoint parts that retain the same p14:creationId."""
    owners: dict[int, str] = {}
    for part in sorted(parts):
        root = reader.xml(part)
        if root is None:
            continue
        c_sld = root.find(f"{{{PML_NS}}}cSld")
        if c_sld is None:
            continue
        seen_in_part: set[int] = set()
        for creation_id in c_sld.findall(
            f"{{{PML_NS}}}extLst/{{{PML_NS}}}ext/"
            f"{{{P14_NS}}}creationId"
        ):
            raw_value = creation_id.get("val")
            try:
                value = int(raw_value or "")
            except ValueError:
                reader.errors.append(
                    f"{part} has invalid p14:creationId value {raw_value!r}"
                )
                continue
            if value < 0 or value > OOXML_UINT32_MAX:
                reader.errors.append(
                    f"{part} p14:creationId {value} is outside OOXML UInt32"
                )
                continue
            if value in seen_in_part:
                reader.errors.append(
                    f"{part} repeats p14:creationId {value}"
                )
                continue
            seen_in_part.add(value)
            previous_owner = owners.setdefault(value, part)
            if previous_owner != part:
                reader.errors.append(
                    f"p14:creationId {value} is shared by "
                    f"{previous_owner} and {part}"
                )


def _top_level_shape_names(
    root: ET.Element,
    context: str,
    errors: list[str],
) -> tuple[str, ...]:
    """Return deterministic names for every visible top-level OOXML shape."""
    c_sld = root.find(f"{{{PML_NS}}}cSld")
    shape_tree = (
        c_sld.find(f"{{{PML_NS}}}spTree") if c_sld is not None else None
    )
    if shape_tree is None:
        errors.append(f"{context} has no p:cSld/p:spTree")
        return ()
    names: list[str] = []
    for child in shape_tree:
        if child.tag not in _TOP_LEVEL_VISIBLE_TAGS:
            continue
        c_nv_pr = next(child.iter(f"{{{PML_NS}}}cNvPr"), None)
        name = c_nv_pr.get("name") if c_nv_pr is not None else None
        if not name:
            errors.append(f"{context} contains a top-level shape without a name")
            continue
        names.append(name)
    return tuple(names)


def _validate_named_shape_roster(
    root: ET.Element,
    expected_names: set[str] | tuple[str, ...] | list[str],
    context: str,
    errors: list[str],
    *,
    exact: bool,
    ordered: bool = False,
) -> None:
    """Validate reusable structure and ordinary Slide carriers by stable name."""
    expected_sequence = tuple(expected_names)
    expected_set = set(expected_sequence)
    actual_names = _top_level_shape_names(root, context, errors)
    counts = Counter(actual_names)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    if duplicates:
        errors.append(
            f"{context} repeats structured shape name(s): " + ", ".join(duplicates)
        )
    actual_set = set(actual_names)
    missing = sorted(expected_set - actual_set)
    if missing:
        errors.append(
            f"{context} is missing structured shape(s): " + ", ".join(missing)
        )
    if exact:
        unexpected = sorted(actual_set - expected_set)
        if unexpected:
            errors.append(
                f"{context} contains unexpected shape(s): "
                + ", ".join(unexpected)
            )
    if ordered and not missing:
        actual_sequence = (
            actual_names
            if exact
            else tuple(name for name in actual_names if name in expected_set)
        )
        if actual_sequence != expected_sequence:
            errors.append(
                f"{context} structured shape order is {actual_sequence}, "
                f"expected {expected_sequence}"
            )


def _top_level_shape_by_name(
    root: ET.Element,
    name: str,
) -> ET.Element | None:
    c_sld = root.find(f"{{{PML_NS}}}cSld")
    shape_tree = (
        c_sld.find(f"{{{PML_NS}}}spTree") if c_sld is not None else None
    )
    if shape_tree is None:
        return None
    for child in shape_tree:
        if child.tag not in _TOP_LEVEL_VISIBLE_TAGS:
            continue
        c_nv_pr = next(child.iter(f"{{{PML_NS}}}cNvPr"), None)
        if c_nv_pr is not None and c_nv_pr.get("name") == name:
            return child
    return None


def _has_explicit_background(root: ET.Element) -> bool:
    c_sld = root.find(f"{{{PML_NS}}}cSld")
    return c_sld is not None and c_sld.find(f"{{{PML_NS}}}bg") is not None


def _xml_payload_signature(elem: ET.Element) -> tuple[object, ...]:
    """Return a namespace-stable exact XML payload signature."""
    return (
        elem.tag,
        tuple(sorted(elem.attrib.items())),
        (elem.text or "").strip(),
        tuple(_xml_payload_signature(child) for child in elem),
    )


def _background_payload_signatures(
    root: ET.Element,
) -> tuple[tuple[object, ...], ...]:
    c_sld = root.find(f"{{{PML_NS}}}cSld")
    backgrounds = (
        c_sld.findall(f"{{{PML_NS}}}bg")
        if c_sld is not None
        else []
    )
    return tuple(_xml_payload_signature(background) for background in backgrounds)


def _expected_background_signature(
    background_xml: str,
) -> tuple[object, ...]:
    """Parse a standalone p:bg fragment regardless of its serialized prefix."""
    try:
        wrapper = ET.fromstring(
            f'<root xmlns:p="{PML_NS}" xmlns:a="{DML_NS}">'
            f"{background_xml}</root>"
        )
    except ET.ParseError as exc:
        raise ValueError(f"invalid expected p:bg payload: {exc}") from exc
    children = list(wrapper)
    if len(children) != 1 or children[0].tag != f"{{{PML_NS}}}bg":
        raise ValueError("expected background payload must contain exactly one p:bg")
    return _xml_payload_signature(children[0])


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
    *,
    min_id: int = PRESENTATION_COLLECTION_ID_MIN,
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
        min_value=min_id,
    )


def _numbered_part_family(
    names: frozenset[str],
    directory: str,
    stem: str,
) -> set[str]:
    """Return exact numbered XML parts such as slide12.xml in one directory."""
    prefix = f"{directory}/{stem}"
    parts: set[str] = set()
    for name in names:
        if not name.startswith(prefix) or not name.endswith(".xml"):
            continue
        number = name[len(prefix):-4]
        if (
            number.isdigit()
            and int(number) > 0
            and posixpath.dirname(name) == directory
        ):
            parts.add(name)
    return parts


def _validate_physical_part_roster(
    reader: _PackageReader,
    expected_parts: set[str],
    directory: str,
    stem: str,
    context: str,
) -> None:
    actual_parts = _numbered_part_family(reader.names, directory, stem)
    if actual_parts != expected_parts:
        reader.errors.append(
            f"{context} physical part roster differs; "
            f"missing={sorted(expected_parts - actual_parts)}, "
            f"extra={sorted(actual_parts - expected_parts)}"
        )


def _validate_content_type_part_roster(
    overrides: dict[str, list[str]],
    expected_parts: set[str],
    directory: str,
    stem: str,
    content_type: str,
    errors: list[str],
    context: str,
) -> None:
    family = _numbered_part_family(
        frozenset(name.lstrip("/") for name in overrides),
        directory,
        stem,
    )
    if family != expected_parts:
        errors.append(
            f"[Content_Types].xml {context} Override roster differs; "
            f"missing={sorted(expected_parts - family)}, "
            f"extra={sorted(family - expected_parts)}"
        )
    for part in sorted(expected_parts):
        values = overrides.get(f"/{part}", [])
        if values != [content_type]:
            errors.append(
                f"[Content_Types].xml must declare {part} exactly once as "
                f"{content_type}"
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


def _validate_master_theme_ownership(
    reader: _PackageReader,
    master_parts: set[str],
) -> None:
    """Require a separate Theme part for every structured Slide Master."""
    owners: dict[str, str] = {}
    for master_part in sorted(master_parts):
        resolved = _single_relationship_target(
            reader,
            master_part,
            THEME_REL_TYPE,
            f"Master {master_part}",
        )
        if resolved is None:
            continue
        _relationship, theme_part = resolved
        if not (
            theme_part.startswith("ppt/theme/")
            and theme_part.endswith(".xml")
        ):
            reader.errors.append(
                f"Master {master_part} targets non-Theme part {theme_part}"
            )
            continue
        reader.xml(theme_part)
        previous_owner = owners.setdefault(theme_part, master_part)
        if previous_owner != master_part:
            reader.errors.append(
                f"Theme {theme_part} is shared by structured Masters "
                f"{previous_owner} and {master_part}"
            )


def _validate_presentation_slide_registration(
    reader: _PackageReader,
    slide_parts: set[str],
) -> None:
    presentation_part = "ppt/presentation.xml"
    presentation_root = reader.xml(presentation_part)
    if presentation_root is None:
        return
    slide_id_entries = presentation_root.findall(
        f"{{{PML_NS}}}sldIdLst/{{{PML_NS}}}sldId"
    )
    _validate_registered_part_roster(
        reader,
        presentation_part,
        SLIDE_REL_TYPE,
        slide_id_entries,
        slide_parts,
        "Presentation p:sldIdLst",
        min_id=PRESENTATION_SLIDE_ID_MIN,
    )


def validate_pptx_template_package(
    pptx_path: str | Path,
    specs: list[TemplateSlideSpec],
    *,
    layout_specs: list[TemplateSlideSpec] | None = None,
    expected_layout_parts: dict[str, str] | None = None,
    expected_master_parts: dict[str, str] | None = None,
    expected_backgrounds: dict[str, str | None] | None = None,
    expected_shape_rosters: dict[str, tuple[str, ...]] | None = None,
) -> None:
    """Validate a finished structured PPTX against its explicit SVG contract.

    ``specs`` describes published slides. ``layout_specs`` may additionally
    include internal prototypes for unused Layouts. Export supplies exact part,
    background, and shape expectations for deterministic serialization
    read-back. Callers with only published-slide specs retain the original
    portable relationship checks.
    """
    if not specs:
        raise ValueError("structured package validation requires at least one slide spec")

    structure_specs = layout_specs or specs
    specs_by_layout: dict[str, list[TemplateSlideSpec]] = {}
    public_specs_by_layout: dict[str, list[TemplateSlideSpec]] = {}
    bindings_by_layout: dict[str, tuple[TemplatePlaceholderBinding, ...]] = {}
    try:
        for spec in structure_specs:
            specs_by_layout.setdefault(spec.layout_key, []).append(spec)
        for spec in specs:
            public_specs_by_layout.setdefault(spec.layout_key, []).append(spec)
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
            if expected_backgrounds is not None:
                for part, background_xml in sorted(expected_backgrounds.items()):
                    root = reader.xml(part)
                    if root is None:
                        continue
                    if background_xml is None:
                        expected_signatures: tuple[tuple[object, ...], ...] = ()
                    else:
                        try:
                            expected_signatures = (
                                _expected_background_signature(background_xml),
                            )
                        except ValueError as exc:
                            errors.append(f"{part} {exc}")
                            continue
                    actual_signatures = _background_payload_signatures(root)
                    if actual_signatures != expected_signatures:
                        errors.append(
                            f"{part} p:bg count/payload differs from the exact "
                            "structured-export expectation"
                        )
            if expected_shape_rosters is not None:
                for part, roster in sorted(expected_shape_rosters.items()):
                    root = reader.xml(part)
                    if root is None:
                        continue
                    _validate_named_shape_roster(
                        root,
                        roster,
                        part,
                        errors,
                        exact=True,
                        ordered=True,
                    )
            layout_parts_by_key = dict(expected_layout_parts or {})
            keys_by_layout_part = {
                part: key for key, part in layout_parts_by_key.items()
            }
            if len(keys_by_layout_part) != len(layout_parts_by_key):
                errors.append(
                    "expected Layout part mapping assigns one part to multiple keys"
                )
            if expected_layout_parts is not None and (
                set(expected_layout_parts) != set(specs_by_layout)
            ):
                errors.append(
                    "expected Layout key roster differs from the SVG contract; "
                    f"missing={sorted(set(specs_by_layout) - set(expected_layout_parts))}, "
                    f"extra={sorted(set(expected_layout_parts) - set(specs_by_layout))}"
                )
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
                previous_part = layout_parts_by_key.setdefault(spec.layout_key, layout_part)
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
            master_specs_by_part: dict[str, TemplateSlideSpec] = {}
            master_parts_by_key = dict(expected_master_parts or {})
            keys_by_master_part = {
                part: key for key, part in master_parts_by_key.items()
            }
            expected_master_keys = {
                spec.master_key for spec in structure_specs
            }
            if len(keys_by_master_part) != len(master_parts_by_key):
                errors.append(
                    "expected Master part mapping assigns one part to multiple keys"
                )
            if expected_master_parts is not None and (
                set(expected_master_parts) != expected_master_keys
            ):
                errors.append(
                    "expected Master key roster differs from the SVG contract; "
                    f"missing={sorted(expected_master_keys - set(expected_master_parts))}, "
                    f"extra={sorted(set(expected_master_parts) - expected_master_keys)}"
                )
            for layout_key, layout_specs in specs_by_layout.items():
                prototype = layout_specs[0]
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
                expected_layout_names = tuple(
                    f"{item.element_id} Layout"
                    if item.layer == "layout"
                    else f"{item.element_id} Placeholder"
                    for item in prototype.elements
                    if (
                        (item.layer == "layout" and not item.is_background)
                        or item.placeholder
                    )
                )
                _validate_named_shape_roster(
                    layout_root,
                    expected_layout_names,
                    f"Layout {layout_key!r}",
                    errors,
                    exact=True,
                    ordered=True,
                )
                expected_layout_background = any(
                    item.is_background for item in prototype.layout_elements
                )
                actual_layout_background = _has_explicit_background(layout_root)
                if actual_layout_background != expected_layout_background:
                    errors.append(
                        f"Layout {layout_key!r} background ownership is "
                        f"{actual_layout_background}, expected "
                        f"{expected_layout_background} from the SVG contract"
                    )
                if (
                    expected_layout_background
                    and expected_backgrounds is not None
                    and layout_part not in expected_backgrounds
                ):
                    errors.append(
                        f"Layout {layout_key!r} has no pre-promotion p:bg payload "
                        "for exact read-back"
                    )
                slide_placeholders: dict[int, dict[int, _Placeholder]] = {}
                for spec in public_specs_by_layout.get(layout_key, []):
                    slide_root = slide_roots.get(spec.slide_num)
                    if slide_root is None:
                        continue
                    expected_slide_bindings = bindings
                    slide_placeholders[spec.slide_num] = _validate_placeholder_roster(
                        slide_root,
                        expected_slide_bindings,
                        f"Slide {spec.slide_num}",
                        errors,
                        is_layout=False,
                    )
                    expected_slide_background = any(
                        item.layer == "slide" and item.is_background
                        for item in spec.elements
                    )
                    actual_slide_background = _has_explicit_background(slide_root)
                    if actual_slide_background != expected_slide_background:
                        errors.append(
                            f"Slide {spec.slide_num} background ownership is "
                            f"{actual_slide_background}, expected "
                            f"{expected_slide_background} from the SVG contract"
                        )
                    slide_part = f"ppt/slides/slide{spec.slide_num}.xml"
                    if (
                        expected_slide_background
                        and expected_backgrounds is not None
                        and slide_part not in expected_backgrounds
                    ):
                        errors.append(
                            f"Slide {spec.slide_num} has no pre-promotion p:bg "
                            "payload for exact read-back"
                        )
                    expected_carrier_names = [
                        (
                            f"{item.element_id} Proxy Content"
                            if is_proxy_placeholder(item)
                            else f"{item.element_id} Placeholder Carrier"
                        )
                        for item in spec.placeholders
                    ]
                    expected_carrier_names.extend(
                        "Placeholder Binding "
                        f"{binding.placeholder_type} {binding.effective_idx}"
                        for binding in bindings
                        if is_proxy_placeholder(binding.element)
                    )
                    _validate_named_shape_roster(
                        slide_root,
                        expected_carrier_names,
                        f"Slide {spec.slide_num}",
                        errors,
                        exact=False,
                        ordered=True,
                    )
                    bindings_by_element = {
                        binding.element.element_id: binding
                        for binding in bindings
                    }
                    for item in spec.placeholders:
                        proxy_binding = is_proxy_placeholder(item)
                        carrier_name = (
                            f"{item.element_id} Proxy Content"
                            if proxy_binding
                            else f"{item.element_id} Placeholder Carrier"
                        )
                        carrier = _top_level_shape_by_name(slide_root, carrier_name)
                        carrier_placeholder = (
                            carrier.find(f".//{{{PML_NS}}}ph")
                            if carrier is not None
                            else None
                        )
                        if proxy_binding:
                            if carrier_placeholder is not None:
                                errors.append(
                                    f"Slide {spec.slide_num} proxy content "
                                    f"{carrier_name!r} must remain ordinary"
                                )
                        elif carrier is not None and carrier_placeholder is None:
                            errors.append(
                                f"Slide {spec.slide_num} carrier "
                                f"{carrier_name!r} must own its p:ph binding"
                            )
                        if not proxy_binding:
                            continue
                        placeholder_binding = bindings_by_element[item.element_id]
                        binding_name = (
                            "Placeholder Binding "
                            f"{placeholder_binding.placeholder_type} "
                            f"{placeholder_binding.effective_idx}"
                        )
                        binding_shape = _top_level_shape_by_name(
                            slide_root,
                            binding_name,
                        )
                        if binding_shape is None:
                            continue
                        c_nv_pr = next(
                            binding_shape.iter(f"{{{PML_NS}}}cNvPr"),
                            None,
                        )
                        if (
                            c_nv_pr is None
                            or c_nv_pr.get("hidden", "0").lower()
                            not in {"1", "true"}
                        ):
                            errors.append(
                                f"Slide {spec.slide_num} binding proxy "
                                f"{binding_name!r} must be hidden"
                            )
                        if binding_shape.find(f".//{{{PML_NS}}}ph") is None:
                            errors.append(
                                f"Slide {spec.slide_num} binding proxy "
                                f"{binding_name!r} has no p:ph"
                            )
                        alpha_values = {
                            alpha.get("val")
                            for alpha in binding_shape.findall(
                                f".//{{{DML_NS}}}srgbClr/{{{DML_NS}}}alpha"
                            )
                        }
                        proxy_text = "".join(
                            node.text or ""
                            for node in binding_shape.findall(
                                f".//{{{DML_NS}}}t"
                            )
                        )
                        if "0" not in alpha_values or proxy_text != "\u200b":
                            errors.append(
                                f"Slide {spec.slide_num} binding proxy "
                                f"{binding_name!r} must contain exactly one fully "
                                "transparent zero-width run"
                            )

                prototype_placeholders = slide_placeholders.get(
                    prototype.slide_num,
                    {},
                )
                for binding in bindings:
                    idx = binding.effective_idx
                    layout_placeholder = layout_placeholders.get(idx)
                    prototype_placeholder = prototype_placeholders.get(idx)
                    if is_proxy_placeholder(binding.element):
                        prototype_placeholder = None
                    if layout_placeholder is None:
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
                    elif prototype_placeholder is not None:
                        expected_bounds = _shape_bounds(
                            prototype_placeholder.shape,
                            f"Slide {prototype.slide_num} placeholder "
                            f"{binding.element.element_id!r}",
                            errors,
                        )
                    else:
                        expected_bounds = None
                        errors.append(
                            f"{context} has neither explicit bounds nor a bound "
                            "prototype Slide placeholder"
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

                    prompt_size = _first_run_size(layout_placeholder.shape)
                    default_size = _level_one_default_size(
                        layout_placeholder.shape
                    )
                    if prototype_placeholder is not None:
                        prototype_size = _first_run_size(
                            prototype_placeholder.shape
                        )
                        if prototype_size is None:
                            continue
                        if prompt_size != prototype_size:
                            errors.append(
                                f"{context} prompt size is {prompt_size!r}, expected "
                                f"{prototype_size!r}"
                            )
                        if default_size != prototype_size:
                            errors.append(
                                f"{context} level-1 default size is "
                                f"{default_size!r}, expected {prototype_size!r}"
                            )
                    elif prompt_size is not None and default_size != prompt_size:
                        errors.append(
                            f"{context} level-1 default size is {default_size!r}, "
                            f"expected its prompt size {prompt_size!r}"
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
                previous_master_part = master_parts_by_key.setdefault(
                    prototype.master_key,
                    master_part,
                )
                if previous_master_part != master_part:
                    errors.append(
                        f"Master key {prototype.master_key!r} targets both "
                        f"{previous_master_part} and {master_part}"
                    )
                previous_master_key = keys_by_master_part.setdefault(
                    master_part,
                    prototype.master_key,
                )
                if previous_master_key != prototype.master_key:
                    errors.append(
                        f"Master keys {previous_master_key!r} and "
                        f"{prototype.master_key!r} both target {master_part}"
                    )
                previous_master_spec = master_specs_by_part.setdefault(
                    master_part,
                    prototype,
                )
                if previous_master_spec.master_key != prototype.master_key:
                    errors.append(
                        f"{master_part} is shared by conflicting SVG Master contracts"
                    )
                layout_parts_by_master.setdefault(master_part, set()).add(
                    layout_part
                )

            layout_id_owners: dict[int, str] = {}
            for master_part, layout_parts in sorted(layout_parts_by_master.items()):
                master_root = reader.xml(master_part)
                if master_root is None:
                    continue
                master_spec = master_specs_by_part.get(master_part)
                if master_spec is not None:
                    master_c_sld = master_root.find(f"{{{PML_NS}}}cSld")
                    actual_master_name = (
                        master_c_sld.get("name")
                        if master_c_sld is not None
                        else None
                    )
                    if actual_master_name != master_spec.master_name:
                        errors.append(
                            f"Master {master_part} has picker name "
                            f"{actual_master_name!r}, expected "
                            f"{master_spec.master_name!r}"
                        )
                    _validate_named_shape_roster(
                        master_root,
                        tuple(
                            f"{item.element_id} Master"
                            for item in master_spec.master_elements
                            if not item.is_background
                        ),
                        f"Master {master_part}",
                        errors,
                        exact=True,
                        ordered=True,
                    )
                    expected_master_background = any(
                        item.is_background
                        for item in master_spec.master_elements
                    )
                    if (
                        expected_master_background
                        and not _has_explicit_background(master_root)
                    ):
                        errors.append(
                            f"Master {master_part} is missing its explicit background"
                        )
                    if (
                        expected_master_background
                        and expected_backgrounds is not None
                        and master_part not in expected_backgrounds
                    ):
                        errors.append(
                            f"Master {master_part} has no pre-promotion p:bg payload "
                            "for exact read-back"
                        )
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

            expected_slide_parts = {
                f"ppt/slides/slide{spec.slide_num}.xml"
                for spec in specs
            }
            expected_layout_parts = set(layout_parts_by_key.values())
            _validate_physical_part_roster(
                reader,
                expected_slide_parts,
                "ppt/slides",
                "slide",
                "Slide",
            )
            _validate_physical_part_roster(
                reader,
                expected_layout_parts,
                "ppt/slideLayouts",
                "slideLayout",
                "Layout",
            )
            _validate_physical_part_roster(
                reader,
                used_master_parts,
                "ppt/slideMasters",
                "slideMaster",
                "Master",
            )
            _validate_content_type_part_roster(
                overrides,
                expected_slide_parts,
                "ppt/slides",
                "slide",
                SLIDE_CONTENT_TYPE,
                errors,
                "Slide",
            )
            _validate_content_type_part_roster(
                overrides,
                expected_layout_parts,
                "ppt/slideLayouts",
                "slideLayout",
                SLIDE_LAYOUT_CONTENT_TYPE,
                errors,
                "Layout",
            )
            _validate_content_type_part_roster(
                overrides,
                used_master_parts,
                "ppt/slideMasters",
                "slideMaster",
                SLIDE_MASTER_CONTENT_TYPE,
                errors,
                "Master",
            )
            _validate_unique_creation_ids(
                reader,
                expected_slide_parts | expected_layout_parts | used_master_parts,
            )
            _validate_presentation_slide_registration(reader, expected_slide_parts)
            _validate_presentation_master_registration(reader, used_master_parts)
            _validate_master_theme_ownership(reader, used_master_parts)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot read template PPTX package {path}: {exc}") from exc

    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise ValueError(f"structured package read-back failed:\n{details}")
