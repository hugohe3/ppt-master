#!/usr/bin/env python3
"""Shared, dependency-light OPC package relationship validation."""

from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from hyperlink_contract import (
    HYPERLINK_REL_TYPE,
    SLIDE_JUMP_ACTION,
    SLIDE_REL_TYPE,
)


PACKAGE_REL_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
_RELATIONSHIPS_TAG = f"{{{PACKAGE_REL_NS}}}Relationships"
_RELATIONSHIP_TAG = f"{{{PACKAGE_REL_NS}}}Relationship"
_DRAWINGML_NS = (
    "http://schemas.openxmlformats.org/drawingml/2006/main"
)
_PRESENTATIONML_NS = (
    "http://schemas.openxmlformats.org/presentationml/2006/main"
)
_OFFICE_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_OPC_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_ASCII_LOWER_TRANSLATION = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
)


def canonical_opc_part_path(path: str) -> str | None:
    """Return an OPC-equivalent package path key, or None when invalid."""
    if (
        not path
        or "\\" in path
        or "?" in path
        or "#" in path
        or path.endswith("/")
        or "//" in path
        or any(ord(char) <= 0x20 for char in path)
    ):
        return None
    output: list[str] = []
    index = 0
    while index < len(path):
        char = path[index]
        if char != "%":
            output.append(char)
            index += 1
            continue
        if (
            index + 2 >= len(path)
            or re.fullmatch(
                r"[0-9A-Fa-f]{2}",
                path[index + 1:index + 3],
            )
            is None
        ):
            return None
        value = int(path[index + 1:index + 3], 16)
        decoded = chr(value)
        if value in {0, ord("/"), ord("\\")}:
            return None
        output.append(
            decoded
            if decoded in _OPC_UNRESERVED
            else f"%{value:02X}"
        )
        index += 3

    decoded_path = "".join(output)
    if decoded_path.rsplit("/", 1)[-1] in {".", ".."}:
        return None
    normalized = posixpath.normpath(decoded_path)
    if (
        not normalized
        or normalized in {".", ".."}
        or normalized.startswith("/")
        or normalized.startswith("../")
    ):
        return None
    return normalized.translate(_ASCII_LOWER_TRANSLATION)


def _source_part_for_rels(rels_path: str) -> str | None:
    filename = posixpath.basename(rels_path)
    if filename == ".rels" or not filename.endswith(".rels"):
        return None
    source_dir = posixpath.dirname(posixpath.dirname(rels_path))
    source_name = filename.removesuffix(".rels")
    return (
        posixpath.join(source_dir, source_name)
        if source_dir
        else source_name
    )


def resolve_internal_opc_target(
    rels_path: str,
    target: str,
) -> str | None:
    """Resolve one valid internal OPC Target to its canonical package key."""
    target_path_query = target.split("#", 1)[0]
    if (
        "\\" in target
        or "?" in target_path_query
        or any(ord(char) <= 0x20 for char in target)
    ):
        return None
    try:
        parsed = urlsplit(target)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc or parsed.query:
        return None

    source_part = _source_part_for_rels(rels_path)
    if parsed.path.startswith("/"):
        resolved = parsed.path[1:]
    elif parsed.path:
        base_dir = posixpath.dirname(source_part) if source_part else ""
        resolved = (
            posixpath.join(base_dir, parsed.path)
            if base_dir
            else parsed.path
        )
    elif source_part and "#" in target:
        resolved = source_part
    else:
        return None
    return canonical_opc_part_path(resolved)


def _relationships_path_for_part(part_path: Path) -> Path:
    return part_path.parent / "_rels" / f"{part_path.name}.rels"


def _relationship_attrs_by_id(rels_path: Path) -> dict[str, dict[str, str]]:
    if not rels_path.is_file():
        return {}
    root = ET.parse(rels_path).getroot()
    return {
        elem.attrib["Id"]: dict(elem.attrib)
        for elem in root.findall(_RELATIONSHIP_TAG)
        if elem.attrib.get("Id")
    }


def _presentation_slide_roster(extract_dir: Path) -> set[str]:
    """Return canonical slide parts reachable from ``p:sldIdLst``."""
    presentation = extract_dir / "ppt" / "presentation.xml"
    presentation_rels = _relationships_path_for_part(presentation)
    if not presentation.is_file() or not presentation_rels.is_file():
        return set()
    rels = _relationship_attrs_by_id(presentation_rels)
    root = ET.parse(presentation).getroot()
    roster: set[str] = set()
    rels_rel = presentation_rels.relative_to(extract_dir).as_posix()
    for slide_id in root.findall(
        f"{{{_PRESENTATIONML_NS}}}sldIdLst/"
        f"{{{_PRESENTATIONML_NS}}}sldId"
    ):
        relationship_id = slide_id.attrib.get(f"{{{_OFFICE_REL_NS}}}id")
        relationship = rels.get(relationship_id or "")
        if relationship is None or relationship.get("Type") != SLIDE_REL_TYPE:
            continue
        target = relationship.get("Target", "")
        resolved = resolve_internal_opc_target(rels_rel, target)
        if resolved is not None:
            roster.add(resolved)
    return roster


def verify_hyperlink_relationships(extract_dir: Path) -> list[str]:
    """Return hyperlink/action mismatches and slide jumps outside the roster."""
    roster = _presentation_slide_roster(extract_dir)
    problems: list[str] = []
    source_patterns = (
        "ppt/slides/slide*.xml",
        "ppt/slideLayouts/slideLayout*.xml",
        "ppt/slideMasters/slideMaster*.xml",
    )
    for pattern in source_patterns:
        for part_path in sorted(extract_dir.glob(pattern)):
            rels_path = _relationships_path_for_part(part_path)
            rels = _relationship_attrs_by_id(rels_path)
            part_rel = part_path.relative_to(extract_dir).as_posix()
            rels_rel = rels_path.relative_to(extract_dir).as_posix()
            try:
                root = ET.parse(part_path).getroot()
            except ET.ParseError:
                continue
            for link in root.iter(f"{{{_DRAWINGML_NS}}}hlinkClick"):
                action = (link.attrib.get("action") or "").strip()
                if action == "ppaction://media":
                    continue
                relationship_id = (
                    link.attrib.get(f"{{{_OFFICE_REL_NS}}}id") or ""
                ).strip()
                if not relationship_id:
                    if action == SLIDE_JUMP_ACTION:
                        problems.append(
                            f"{part_rel} -> <slide jump without relationship id>"
                        )
                    continue
                relationship = rels.get(relationship_id)
                if relationship is None:
                    problems.append(
                        f"{part_rel} -> <missing hyperlink relationship "
                        f"{relationship_id!r}>"
                    )
                    continue
                rel_type = relationship.get("Type", "")
                target_mode = relationship.get("TargetMode", "")
                target = relationship.get("Target", "")
                if rel_type == HYPERLINK_REL_TYPE:
                    if target_mode.lower() != "external":
                        problems.append(
                            f"{part_rel} -> <hyperlink relationship "
                            f"{relationship_id!r} is not External>"
                        )
                    if action == SLIDE_JUMP_ACTION:
                        problems.append(
                            f"{part_rel} -> <slide jump {relationship_id!r} "
                            "uses an external hyperlink relationship>"
                        )
                    continue
                if rel_type == SLIDE_REL_TYPE:
                    if target_mode:
                        problems.append(
                            f"{part_rel} -> <slide relationship "
                            f"{relationship_id!r} cannot be External>"
                        )
                    if action != SLIDE_JUMP_ACTION:
                        problems.append(
                            f"{part_rel} -> <slide relationship "
                            f"{relationship_id!r} lacks hlinksldjump action>"
                        )
                    resolved = resolve_internal_opc_target(rels_rel, target)
                    if resolved is not None and resolved not in roster:
                        problems.append(
                            f"{part_rel} -> <slide jump {relationship_id!r} "
                            f"targets non-roster part {resolved}>"
                        )
                    continue
                if action == SLIDE_JUMP_ACTION:
                    problems.append(
                        f"{part_rel} -> <slide jump {relationship_id!r} uses "
                        f"relationship type {rel_type!r}>"
                    )
    return problems


def verify_internal_relationships(extract_dir: Path) -> list[str]:
    """Return invalid or dangling internal relationships in an OPC package."""
    package_parts: set[str] = set()
    for path in extract_dir.rglob("*"):
        if not path.is_file():
            continue
        key = canonical_opc_part_path(
            path.relative_to(extract_dir).as_posix()
        )
        if key is not None:
            package_parts.add(key)

    problems: list[str] = []
    for rels_path in sorted(extract_dir.rglob("*.rels")):
        rels_rel = rels_path.relative_to(extract_dir).as_posix()
        try:
            root = ET.parse(rels_path).getroot()
        except ET.ParseError as exc:
            problems.append(
                f"{rels_rel} -> <invalid relationships XML: {exc}>"
            )
            continue
        if root.tag != _RELATIONSHIPS_TAG:
            problems.append(
                f"{rels_rel} -> <invalid Relationships namespace>"
            )
            continue

        seen_ids: set[str] = set()
        for element in root:
            if element.tag != _RELATIONSHIP_TAG:
                problems.append(
                    f"{rels_rel} -> <invalid relationships child "
                    f"{element.tag!r}>"
                )
                continue
            relationship_id = (element.attrib.get("Id") or "").strip()
            relationship_type = (
                element.attrib.get("Type") or ""
            ).strip()
            target = (element.attrib.get("Target") or "").strip()
            target_mode = (
                element.attrib.get("TargetMode") or ""
            ).strip()

            if not relationship_id:
                problems.append(f"{rels_rel} -> <missing relationship Id>")
            elif relationship_id in seen_ids:
                problems.append(
                    f"{rels_rel} -> <duplicate relationship Id "
                    f"{relationship_id!r}>"
                )
            else:
                seen_ids.add(relationship_id)
            if not relationship_type:
                problems.append(
                    f"{rels_rel} -> <missing relationship Type>"
                )
            if not target:
                problems.append(f"{rels_rel} -> <missing Target>")
                continue
            if target_mode and target_mode.lower() not in {
                "internal",
                "external",
            }:
                problems.append(
                    f"{rels_rel} -> <invalid TargetMode "
                    f"{target_mode!r}>"
                )
                continue
            if target_mode.lower() == "external":
                continue

            resolved = resolve_internal_opc_target(rels_rel, target)
            if resolved is None:
                problems.append(
                    f"{rels_rel} -> <invalid Target {target!r}>"
                )
            elif resolved not in package_parts:
                problems.append(f"{rels_rel} -> {resolved}")
    problems.extend(verify_hyperlink_relationships(extract_dir))
    return problems
