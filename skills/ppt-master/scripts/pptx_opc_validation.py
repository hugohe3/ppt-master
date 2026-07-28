#!/usr/bin/env python3
"""Shared, dependency-light OPC package relationship validation."""

from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET


PACKAGE_REL_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
_RELATIONSHIPS_TAG = f"{{{PACKAGE_REL_NS}}}Relationships"
_RELATIONSHIP_TAG = f"{{{PACKAGE_REL_NS}}}Relationship"
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
    return problems
