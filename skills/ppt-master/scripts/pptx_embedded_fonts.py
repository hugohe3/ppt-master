#!/usr/bin/env python3
"""Validated sidecar contract for source PPTX embedded fonts.

The SVG projection keeps text editable, so an imported deck's embedded font
parts must travel beside the SVG workspace instead of being flattened into
glyph outlines.  This module owns the small manifest used by both conversion
directions and rejects stale, incomplete, or path-escaping payloads.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FONT_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
)
FONT_CONTENT_TYPE = "application/x-fontdata"
FONT_BUNDLE_DIR = PurePosixPath("native-payloads/embedded-fonts")
FONT_MANIFEST_PATH = FONT_BUNDLE_DIR / "manifest.json"
_FONT_STYLE_TAGS = frozenset({"regular", "bold", "italic", "boldItalic"})


class EmbeddedFontError(ValueError):
    """Reject an unsafe or incomplete embedded-font sidecar."""


@dataclass(frozen=True)
class EmbeddedFontPart:
    """One relationship-addressed source font payload."""

    relationship_id: str
    filename: str
    payload: bytes


@dataclass(frozen=True)
class EmbeddedFontBundle:
    """Presentation font-list XML plus all referenced font parts."""

    font_list_xml: bytes
    parts: tuple[EmbeddedFontPart, ...]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _font_relationship_ids(root: ET.Element) -> tuple[str, ...]:
    """Return every embedded-font relationship id in document order."""
    if root.tag != f"{{{PML_NS}}}embeddedFontLst":
        raise EmbeddedFontError(
            "Embedded font metadata root must be p:embeddedFontLst"
        )
    relationship_ids: list[str] = []
    for font in list(root):
        if font.tag != f"{{{PML_NS}}}embeddedFont":
            raise EmbeddedFontError(
                "Embedded font list may contain only p:embeddedFont entries"
            )
        descriptor = font.find(f"{{{PML_NS}}}font")
        if descriptor is None or not descriptor.attrib.get("typeface", "").strip():
            raise EmbeddedFontError(
                "Each embedded font entry requires a non-empty p:font typeface"
            )
        for child in list(font):
            name = _local_name(child.tag)
            if name == "font":
                continue
            if name not in _FONT_STYLE_TAGS or child.tag != f"{{{PML_NS}}}{name}":
                raise EmbeddedFontError(
                    f"Unsupported embedded font list child: {name}"
                )
            if list(child) or set(child.attrib) != {f"{{{REL_NS}}}id"}:
                raise EmbeddedFontError(
                    f"Embedded font slot {name} must contain only one r:id"
                )
            relationship_id = child.attrib[f"{{{REL_NS}}}id"].strip()
            if not relationship_id:
                raise EmbeddedFontError(
                    f"Embedded font slot {name} has an empty r:id"
                )
            if relationship_id not in relationship_ids:
                relationship_ids.append(relationship_id)
    if not relationship_ids:
        raise EmbeddedFontError("Embedded font list has no font payload slots")
    return tuple(relationship_ids)


def _validate_bundle(bundle: EmbeddedFontBundle) -> ET.Element:
    """Validate XML/part correspondence and return the parsed font list."""
    try:
        root = ET.fromstring(bundle.font_list_xml)
    except ET.ParseError as exc:
        raise EmbeddedFontError(
            f"Embedded font list XML is malformed: {exc}"
        ) from exc
    relationship_ids = _font_relationship_ids(root)
    parts_by_id: dict[str, EmbeddedFontPart] = {}
    filenames: set[str] = set()
    for part in bundle.parts:
        if part.relationship_id in parts_by_id:
            raise EmbeddedFontError(
                f"Duplicate embedded font relationship: {part.relationship_id}"
            )
        path = PurePosixPath(part.filename)
        if (
            not part.filename
            or path.is_absolute()
            or len(path.parts) != 1
            or path.name != part.filename
            or path.suffix.lower() != ".fntdata"
        ):
            raise EmbeddedFontError(
                f"Embedded font payload filename must be one .fntdata basename: "
                f"{part.filename!r}"
            )
        if part.filename in filenames:
            raise EmbeddedFontError(
                f"Duplicate embedded font payload filename: {part.filename}"
            )
        if not part.payload:
            raise EmbeddedFontError(
                f"Embedded font payload is empty: {part.filename}"
            )
        filenames.add(part.filename)
        parts_by_id[part.relationship_id] = part
    if set(relationship_ids) != set(parts_by_id):
        missing = sorted(set(relationship_ids) - set(parts_by_id))
        extra = sorted(set(parts_by_id) - set(relationship_ids))
        raise EmbeddedFontError(
            "Embedded font relationship roster mismatch: "
            f"missing={missing}, extra={extra}"
        )
    return root


def capture_embedded_fonts(
    presentation_root: ET.Element,
    relationships: Mapping[str, Mapping[str, str]],
    read_part: Callable[[str], bytes],
) -> EmbeddedFontBundle | None:
    """Capture the exact font-list metadata and every referenced font part."""
    font_list = presentation_root.find(f"{{{PML_NS}}}embeddedFontLst")
    if font_list is None:
        return None
    font_list_xml = ET.tostring(font_list, encoding="utf-8")
    relationship_ids = _font_relationship_ids(font_list)
    parts: list[EmbeddedFontPart] = []
    for index, relationship_id in enumerate(relationship_ids, start=1):
        relationship = relationships.get(relationship_id)
        if relationship is None:
            raise EmbeddedFontError(
                f"Embedded font relationship is missing: {relationship_id}"
            )
        if relationship.get("type") != FONT_REL_TYPE or relationship.get("external"):
            raise EmbeddedFontError(
                f"Embedded font relationship is not an internal font part: "
                f"{relationship_id}"
            )
        target = relationship.get("target", "")
        target_path = PurePosixPath(target)
        if (
            target_path.is_absolute()
            or len(target_path.parts) != 3
            or target_path.parts[:2] != ("ppt", "fonts")
            or target_path.suffix.lower() != ".fntdata"
        ):
            raise EmbeddedFontError(
                f"Embedded font relationship has an unsafe target: {target!r}"
            )
        try:
            payload = read_part(target)
        except (KeyError, OSError) as exc:
            raise EmbeddedFontError(
                f"Cannot read embedded font part {target}: {exc}"
            ) from exc
        parts.append(EmbeddedFontPart(
            relationship_id=relationship_id,
            filename=f"font{index}.fntdata",
            payload=payload,
        ))
    bundle = EmbeddedFontBundle(
        font_list_xml=font_list_xml,
        parts=tuple(parts),
    )
    _validate_bundle(bundle)
    return bundle


def embedded_font_typefaces(bundle: EmbeddedFontBundle) -> tuple[str, ...]:
    """Return the declared source typefaces in presentation order."""
    root = _validate_bundle(bundle)
    return tuple(
        descriptor.attrib["typeface"].strip()
        for descriptor in root.findall(
            f"{{{PML_NS}}}embeddedFont/{{{PML_NS}}}font"
        )
    )


def write_embedded_font_bundle(
    output_root: Path,
    bundle: EmbeddedFontBundle,
) -> tuple[dict[str, object], tuple[str, ...]]:
    """Write one converter-owned sidecar and return report metadata/paths."""
    _validate_bundle(bundle)
    bundle_dir = output_root.joinpath(*FONT_BUNDLE_DIR.parts)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    part_entries: list[dict[str, str]] = []
    managed_paths: list[str] = []
    for part in bundle.parts:
        relative_path = (FONT_BUNDLE_DIR / part.filename).as_posix()
        (output_root / relative_path).write_bytes(part.payload)
        managed_paths.append(relative_path)
        part_entries.append({
            "relationshipId": part.relationship_id,
            "path": relative_path,
            "sha256": hashlib.sha256(part.payload).hexdigest(),
        })
    manifest = {
        "schemaVersion": 1,
        "fontListOoxml": {
            "encoding": "base64",
            "sha256": hashlib.sha256(bundle.font_list_xml).hexdigest(),
            "payload": base64.b64encode(bundle.font_list_xml).decode("ascii"),
        },
        "parts": part_entries,
    }
    manifest_relative = FONT_MANIFEST_PATH.as_posix()
    (output_root / manifest_relative).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    managed_paths.append(manifest_relative)
    descriptor: dict[str, object] = {
        "manifest": manifest_relative,
        "partCount": len(bundle.parts),
        "typefaces": list(embedded_font_typefaces(bundle)),
    }
    return descriptor, tuple(managed_paths)


def _safe_workspace_path(project_root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise EmbeddedFontError("Embedded font sidecar path must be a string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise EmbeddedFontError(
            f"Embedded font sidecar path escapes the project: {value!r}"
        )
    expected_prefix = FONT_BUNDLE_DIR.parts
    if path.parts[:len(expected_prefix)] != expected_prefix:
        raise EmbeddedFontError(
            f"Embedded font sidecar path must stay under {FONT_BUNDLE_DIR}: "
            f"{value!r}"
        )
    resolved_root = project_root.resolve()
    resolved = (project_root / Path(*path.parts)).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise EmbeddedFontError(
            f"Embedded font sidecar path escapes the project: {value!r}"
        ) from exc
    if not resolved.is_file():
        raise EmbeddedFontError(
            f"Embedded font sidecar file is missing: {value}"
        )
    return resolved


def load_embedded_font_bundle(
    project_root: Path,
    descriptor: object,
) -> EmbeddedFontBundle | None:
    """Load and verify a font bundle referenced by conversion-report.json."""
    if descriptor is None:
        return None
    if not isinstance(descriptor, dict):
        raise EmbeddedFontError(
            "sourceDocument.embeddedFonts must be an object"
        )
    manifest_path = _safe_workspace_path(
        project_root,
        descriptor.get("manifest"),
    )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EmbeddedFontError(
            f"Cannot read embedded font manifest {manifest_path}: {exc}"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise EmbeddedFontError(
            "Embedded font manifest requires schemaVersion 1"
        )
    ooxml = manifest.get("fontListOoxml")
    if not isinstance(ooxml, dict) or ooxml.get("encoding") != "base64":
        raise EmbeddedFontError(
            "Embedded font manifest requires base64 fontListOoxml"
        )
    payload_value = ooxml.get("payload")
    digest = ooxml.get("sha256")
    if not isinstance(payload_value, str) or not isinstance(digest, str):
        raise EmbeddedFontError(
            "Embedded font fontListOoxml requires payload and sha256"
        )
    try:
        font_list_xml = base64.b64decode(payload_value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise EmbeddedFontError(
            "Embedded font fontListOoxml payload is invalid base64"
        ) from exc
    if hashlib.sha256(font_list_xml).hexdigest() != digest.lower():
        raise EmbeddedFontError(
            "Embedded font fontListOoxml checksum does not match"
        )
    raw_parts = manifest.get("parts")
    if not isinstance(raw_parts, list) or not raw_parts:
        raise EmbeddedFontError("Embedded font manifest has no parts")
    parts: list[EmbeddedFontPart] = []
    for entry in raw_parts:
        if not isinstance(entry, dict):
            raise EmbeddedFontError(
                "Embedded font manifest part entries must be objects"
            )
        relationship_id = entry.get("relationshipId")
        expected_digest = entry.get("sha256")
        if not isinstance(relationship_id, str) or not relationship_id:
            raise EmbeddedFontError(
                "Embedded font manifest part requires relationshipId"
            )
        if not isinstance(expected_digest, str):
            raise EmbeddedFontError(
                "Embedded font manifest part requires sha256"
            )
        part_path = _safe_workspace_path(project_root, entry.get("path"))
        payload = part_path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_digest.lower():
            raise EmbeddedFontError(
                f"Embedded font payload checksum does not match: {part_path}"
            )
        parts.append(EmbeddedFontPart(
            relationship_id=relationship_id,
            filename=part_path.name,
            payload=payload,
        ))
    bundle = EmbeddedFontBundle(
        font_list_xml=font_list_xml,
        parts=tuple(parts),
    )
    _validate_bundle(bundle)
    expected_count = descriptor.get("partCount")
    if expected_count is not None and expected_count != len(parts):
        raise EmbeddedFontError(
            "Embedded font report partCount does not match the manifest"
        )
    return bundle
