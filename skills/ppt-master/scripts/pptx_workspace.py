#!/usr/bin/env python3
"""
PPT Master - PPTX Semantic Workspace

Own the semantic on-disk paths and package-resource inventory shared by PPTX
import, template preparation, and source-preserving SVG round trips.

Usage:
    Imported by pptx_to_svg.py, pptx_template_import.py, and svg_to_pptx.py.

Examples:
    inventory = inventory_package_resources(package)
    write_workspace_resources(workspace, inventory)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import io
import json
import posixpath
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


SOURCE_PPTX_PATH = Path("sources/source.pptx")
NATIVE_STRUCTURE_PATH = Path("analysis/native_structure.json")
ROUNDTRIP_MANIFEST_PATH = Path("analysis/roundtrip_manifest.json")
ROUNDTRIP_PAGE_PLAN_PATH = Path("page_plan.json")
TEMPLATE_MANIFEST_PATH = Path("analysis/manifest.json")
CONVERSION_REPORT_PATH = Path("validation/conversion-report.json")
AUTHORING_SVG_FLAT_DIR = Path("authoring-svg-flat")
AUTHORING_SVG_DIR = Path("authoring-svg")
ROUNDTRIP_SVG_ROOT = Path("analysis/roundtrip-svg")
ROUNDTRIP_LAYERED_SVG_DIR = ROUNDTRIP_SVG_ROOT / "layered"
ROUNDTRIP_FLAT_SVG_DIR = ROUNDTRIP_SVG_ROOT / "flat"
REMOVED_WORKSPACE_ENTRIES = (
    Path("assets"),
    Path("conversion-report.json"),
    Path("manifest.json"),
    Path("native_structure.json"),
    Path("source_template.pptx"),
    Path("svg_flat"),
)

IMAGE_EXTENSIONS = frozenset({
    ".avif",
    ".bmp",
    ".emf",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
    ".wmf",
})
VIDEO_EXTENSIONS = frozenset({
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".webm",
    ".wmv",
})
AUDIO_EXTENSIONS = frozenset({
    ".aac",
    ".aif",
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".oga",
    ".ogg",
    ".wav",
    ".wma",
})

_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DOC_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_TRANSITION_TAG = (
    "{http://schemas.openxmlformats.org/presentationml/2006/main}transition"
)
_REL_ATTR_PREFIX = f"{{{_DOC_REL_NS}}}"
_CONTENT_TYPES_NS = (
    "http://schemas.openxmlformats.org/package/2006/content-types"
)
_FORMAT_BY_EXTENSION = {
    ".3mf": frozenset({"3mf"}),
    ".aac": frozenset({"aac"}),
    ".aif": frozenset({"aiff"}),
    ".aiff": frozenset({"aiff"}),
    ".avif": frozenset({"avif"}),
    ".avi": frozenset({"avi"}),
    ".bmp": frozenset({"bmp"}),
    ".doc": frozenset({"ole"}),
    ".docm": frozenset({"ooxml-docx"}),
    ".docx": frozenset({"ooxml-docx"}),
    ".dotm": frozenset({"ooxml-docx"}),
    ".dotx": frozenset({"ooxml-docx"}),
    ".emf": frozenset({"emf"}),
    ".eps": frozenset({"postscript"}),
    ".flac": frozenset({"flac"}),
    ".gif": frozenset({"gif"}),
    ".glb": frozenset({"glb"}),
    ".jpeg": frozenset({"jpeg"}),
    ".jpg": frozenset({"jpeg"}),
    ".ico": frozenset({"ico"}),
    ".m4a": frozenset({"iso-bmff"}),
    ".m4v": frozenset({"iso-bmff"}),
    ".mkv": frozenset({"ebml"}),
    ".mov": frozenset({"iso-bmff"}),
    ".mp3": frozenset({"mp3"}),
    ".mp4": frozenset({"iso-bmff"}),
    ".mpeg": frozenset({"mpeg"}),
    ".mpg": frozenset({"mpeg"}),
    ".oga": frozenset({"ogg"}),
    ".ogg": frozenset({"ogg"}),
    ".png": frozenset({"png"}),
    ".pdf": frozenset({"pdf"}),
    ".potm": frozenset({"ooxml-pptx"}),
    ".potx": frozenset({"ooxml-pptx"}),
    ".ppt": frozenset({"ole"}),
    ".pptm": frozenset({"ooxml-pptx"}),
    ".pptx": frozenset({"ooxml-pptx"}),
    ".svg": frozenset({"svg"}),
    ".tif": frozenset({"tiff"}),
    ".tiff": frozenset({"tiff"}),
    ".wav": frozenset({"wav"}),
    ".wdp": frozenset({"wdp"}),
    ".webm": frozenset({"ebml"}),
    ".webp": frozenset({"webp"}),
    ".wma": frozenset({"asf"}),
    ".wmf": frozenset({"wmf"}),
    ".wmv": frozenset({"asf"}),
    ".xls": frozenset({"ole"}),
    ".xlsb": frozenset({"ooxml-xlsx"}),
    ".xlsm": frozenset({"ooxml-xlsx"}),
    ".xlsx": frozenset({"ooxml-xlsx"}),
    ".xltm": frozenset({"ooxml-xlsx"}),
    ".xltx": frozenset({"ooxml-xlsx"}),
}
_FORMAT_MEDIA_KIND = {
    "aac": "audio",
    "aiff": "audio",
    "asf": "media",
    "avi": "video",
    "avif": "image",
    "bmp": "image",
    "ebml": "video",
    "emf": "image",
    "flac": "audio",
    "gif": "image",
    "ico": "image",
    "iso-bmff": "media",
    "jpeg": "image",
    "mp3": "audio",
    "mpeg": "video",
    "ogg": "media",
    "png": "image",
    "postscript": "image",
    "svg": "image",
    "tiff": "image",
    "wav": "audio",
    "wdp": "image",
    "webp": "image",
    "wmf": "image",
}
_FORMAT_BY_CONTENT_TYPE = {
    "application/pdf": frozenset({"pdf"}),
    "application/postscript": frozenset({"postscript"}),
    "application/vnd.ms-3mfdocument": frozenset({"3mf"}),
    "audio/aac": frozenset({"aac"}),
    "audio/aiff": frozenset({"aiff"}),
    "audio/flac": frozenset({"flac"}),
    "audio/mpeg": frozenset({"mp3"}),
    "audio/mp4": frozenset({"iso-bmff"}),
    "audio/ogg": frozenset({"ogg"}),
    "audio/wav": frozenset({"wav"}),
    "audio/x-aiff": frozenset({"aiff"}),
    "audio/x-ms-wma": frozenset({"asf"}),
    "audio/x-wav": frozenset({"wav"}),
    "image/avif": frozenset({"avif"}),
    "image/bmp": frozenset({"bmp"}),
    "image/gif": frozenset({"gif"}),
    "image/jpeg": frozenset({"jpeg"}),
    "image/png": frozenset({"png"}),
    "image/svg+xml": frozenset({"svg"}),
    "image/tiff": frozenset({"tiff"}),
    "image/vnd.ms-photo": frozenset({"wdp"}),
    "image/vnd.microsoft.icon": frozenset({"ico"}),
    "image/webp": frozenset({"webp"}),
    "image/x-eps": frozenset({"postscript"}),
    "image/x-emf": frozenset({"emf"}),
    "image/x-icon": frozenset({"ico"}),
    "image/x-wmf": frozenset({"wmf"}),
    "model/gltf-binary": frozenset({"glb"}),
    "video/mp4": frozenset({"iso-bmff"}),
    "video/mpeg": frozenset({"mpeg"}),
    "video/quicktime": frozenset({"iso-bmff"}),
    "video/webm": frozenset({"ebml"}),
    "video/x-matroska": frozenset({"ebml"}),
    "video/x-ms-wmv": frozenset({"asf"}),
    "video/x-msvideo": frozenset({"avi"}),
}


def source_pptx_path(workspace: Path) -> Path:
    """Return the semantic preserved-source package path."""
    return workspace / SOURCE_PPTX_PATH


def native_structure_path(workspace: Path) -> Path:
    """Return the semantic native-structure contract path."""
    return workspace / NATIVE_STRUCTURE_PATH


def roundtrip_page_plan_path(workspace: Path) -> Path:
    """Return the optional deck-level round-trip page-plan path."""
    return workspace / ROUNDTRIP_PAGE_PLAN_PATH


def template_manifest_path(workspace: Path) -> Path:
    """Return the semantic template-import manifest path."""
    return workspace / TEMPLATE_MANIFEST_PATH


def conversion_report_path(workspace: Path) -> Path:
    """Return the semantic conversion-report path."""
    return workspace / CONVERSION_REPORT_PATH


def reject_removed_workspace_layout(workspace: Path) -> None:
    """Reject mixed workspaces instead of guessing or migrating old paths."""
    if not workspace.is_dir():
        return
    present = [
        path.as_posix()
        for path in REMOVED_WORKSPACE_ENTRIES
        if (workspace / path).exists()
    ]
    if present:
        raise RuntimeError(
            "Output workspace uses removed paths: "
            + ", ".join(present)
            + "; choose a clean directory and import again"
        )


def _safe_basename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "resource"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sniff_zip_format(payload: bytes) -> str | None:
    """Return the semantic package family for one ZIP payload."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as package:
            names = set(package.namelist())
    except (OSError, zipfile.BadZipFile):
        return None
    if "xl/workbook.xml" in names or "xl/workbook.bin" in names:
        return "ooxml-xlsx"
    if "word/document.xml" in names:
        return "ooxml-docx"
    if "ppt/presentation.xml" in names:
        return "ooxml-pptx"
    if any(name.lower().endswith(".model") for name in names):
        return "3mf"
    return "zip"


def _sniff_resource_format(payload: bytes) -> str | None:
    """Identify common PPTX resource formats from their bytes."""
    header = payload[:64]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header.startswith(b"BM"):
        return "bmp"
    if header.startswith((b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")):
        return "tiff"
    if header.startswith((b"II\xbc\x01", b"MM\x01\xbc")):
        return "wdp"
    if len(header) >= 44 and header[40:44] == b" EMF":
        return "emf"
    if header.startswith(b"\xd7\xcd\xc6\x9a"):
        return "wmf"
    if (
        len(header) >= 6
        and header[:2] in {b"\x01\x00", b"\x02\x00"}
        and header[2:4] == b"\x09\x00"
    ):
        return "wmf"
    if header.startswith(b"\x00\x00\x01\x00"):
        return "ico"
    if header.startswith(b"%PDF-"):
        return "pdf"
    if header.startswith(b"%!PS-Adobe-"):
        return "postscript"
    if len(header) >= 12 and header[:4] in {b"RIFF", b"RF64"}:
        form = header[8:12]
        if form == b"WAVE":
            return "wav"
        if form == b"AVI ":
            return "avi"
        if form == b"WEBP":
            return "webp"
    if header.startswith(b"FORM") and header[8:12] in {b"AIFF", b"AIFC"}:
        return "aiff"
    if header.startswith(b"fLaC"):
        return "flac"
    if header.startswith(b"OggS"):
        return "ogg"
    if header.startswith(b"ID3") or (
        len(header) >= 2
        and header[0] == 0xFF
        and header[1] & 0xE0 == 0xE0
        and header[1] & 0x06 != 0
    ):
        return "mp3"
    if (
        len(header) >= 2
        and header[0] == 0xFF
        and header[1] & 0xF6 == 0xF0
    ):
        return "aac"
    if header.startswith(b"\x30\x26\xb2\x75\x8e\x66\xcf\x11"):
        return "asf"
    if header.startswith(b"\x1aE\xdf\xa3"):
        return "ebml"
    if header.startswith(b"glTF"):
        return "glb"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        box_size = int.from_bytes(header[:4], "big")
        brands = {
            header[offset:offset + 4]
            for offset in range(8, min(len(header), box_size or len(header)), 4)
        }
        if brands & {b"avif", b"avis"}:
            return "avif"
        return "iso-bmff"
    if header.startswith((b"\x00\x00\x01\xba", b"\x00\x00\x01\xb3")):
        return "mpeg"
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "ole"
    if header.startswith(b"PK"):
        return _sniff_zip_format(payload)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return None
    if root.tag == "svg" or root.tag.endswith("}svg"):
        return "svg"
    return None


def _package_content_types(
    package: zipfile.ZipFile,
) -> tuple[dict[str, str], dict[str, str]]:
    """Read Default and Override declarations from a PPTX package."""
    try:
        root = ET.fromstring(package.read("[Content_Types].xml"))
    except (KeyError, ET.ParseError) as exc:
        raise RuntimeError(
            "Round-trip source PPTX has an invalid [Content_Types].xml"
        ) from exc
    defaults = {
        str(item.get("Extension", "")).lower(): str(item.get("ContentType", ""))
        for item in root.findall(f"{{{_CONTENT_TYPES_NS}}}Default")
        if item.get("Extension") and item.get("ContentType")
    }
    overrides = {
        str(item.get("PartName", "")).lstrip("/"): str(
            item.get("ContentType", "")
        )
        for item in root.findall(f"{{{_CONTENT_TYPES_NS}}}Override")
        if item.get("PartName") and item.get("ContentType")
    }
    return defaults, overrides


def _expected_content_type_formats(content_type: str) -> frozenset[str]:
    normalized = content_type.partition(";")[0].strip().lower()
    known = _FORMAT_BY_CONTENT_TYPE.get(normalized)
    if known is not None:
        return known
    if "spreadsheetml" in normalized:
        return frozenset({"ooxml-xlsx"})
    if "wordprocessingml" in normalized:
        return frozenset({"ooxml-docx"})
    if "presentationml" in normalized:
        return frozenset({"ooxml-pptx"})
    return frozenset()


def _validate_changed_resource_format(
    *,
    spec: WorkspaceResourceSpec,
    payload: bytes,
    source_payload: bytes,
    content_type: str,
) -> None:
    """Refuse changed bytes that no longer fit their source package part."""
    suffix = PurePosixPath(spec.package_part).suffix.lower()
    actual_format = _sniff_resource_format(payload)
    source_format = _sniff_resource_format(source_payload)
    expected_by_extension = _FORMAT_BY_EXTENSION.get(suffix, frozenset())
    expected_by_content_type = _expected_content_type_formats(content_type)
    declared_media_kind = content_type.partition("/")[0].lower()
    actual_media_kind = _FORMAT_MEDIA_KIND.get(actual_format or "")
    has_declared_expectation = bool(
        source_format
        or expected_by_extension
        or expected_by_content_type
        or declared_media_kind in {"audio", "image", "video"}
    )
    mismatch = actual_format is None or not has_declared_expectation or (
        actual_format is not None
        and (
            (source_format is not None and actual_format != source_format)
            or (
                bool(expected_by_extension)
                and actual_format not in expected_by_extension
            )
            or (
                bool(expected_by_content_type)
                and actual_format not in expected_by_content_type
            )
            or (
                declared_media_kind in {"audio", "image", "video"}
                and actual_media_kind not in {declared_media_kind, "media"}
            )
        )
    )
    if not mismatch:
        return
    detected = actual_format or "unrecognized"
    raise RuntimeError(
        "Changed round-trip resource format does not match its source part: "
        f"{spec.workspace_path.as_posix()} is {detected}, but "
        f"{spec.package_part} uses extension {suffix or '<none>'} and "
        f"Content-Type {content_type!r}"
    )


def _source_part_for_relationships(rels_path: str) -> str | None:
    if rels_path == "_rels/.rels":
        return None
    marker = "/_rels/"
    if marker not in rels_path or not rels_path.endswith(".rels"):
        return None
    parent, filename = rels_path.split(marker, 1)
    return f"{parent}/{filename[:-5]}"


def _resolve_relationship_target(source_part: str | None, target: str) -> str:
    normalized = target.replace("\\", "/")
    if normalized.startswith("/"):
        return normalized.lstrip("/")
    base_dir = posixpath.dirname(source_part or "")
    return posixpath.normpath(posixpath.join(base_dir, normalized)).lstrip("/")


def _transition_relationship_ids(
    package: zipfile.ZipFile,
    source_part: str | None,
) -> set[str]:
    if source_part is None or not source_part.startswith("ppt/slides/"):
        return set()
    try:
        root = ET.fromstring(package.read(source_part))
    except (KeyError, ET.ParseError):
        return set()
    ids: set[str] = set()
    for transition in root.iter(_TRANSITION_TAG):
        for node in transition.iter():
            for name, value in node.attrib.items():
                if name.startswith(_REL_ATTR_PREFIX) and value:
                    ids.add(value)
    return ids


@dataclass(frozen=True)
class PackageResource:
    """One source package payload exposed through a semantic workspace path."""

    package_part: str
    kind: str
    workspace_path: str
    payload: bytes
    relationship_types: tuple[str, ...] = ()
    source_parts: tuple[str, ...] = ()
    owner_parts: tuple[str, ...] = ()

    @property
    def sha256(self) -> str:
        return _sha256(self.payload)

    def manifest_row(self, *, materialized: bool = True) -> dict[str, object]:
        """Return the compact machine-readable inventory record."""
        return {
            "packagePart": self.package_part,
            "kind": self.kind,
            "workspacePath": self.workspace_path,
            "sha256": self.sha256,
            "bytes": len(self.payload),
            "relationshipTypes": list(self.relationship_types),
            "sourceParts": list(self.source_parts),
            "ownerParts": list(self.owner_parts),
            "materialized": materialized,
        }


@dataclass(frozen=True)
class PackageResourceInventory:
    """Deterministic semantic projection of source package payloads."""

    resources: tuple[PackageResource, ...] = ()

    def path_map(self) -> dict[str, str]:
        """Map source package part names to workspace-relative paths."""
        return {
            resource.package_part: resource.workspace_path
            for resource in self.resources
        }

    def image_name_map(self) -> dict[str, str]:
        """Map package image parts to basenames used by SVG hrefs."""
        return {
            resource.package_part: PurePosixPath(resource.workspace_path).name
            for resource in self.resources
            if resource.kind == "image"
        }

    def manifest(self, *, include_images: bool = True) -> dict[str, object]:
        """Return the versioned resource inventory payload."""
        return {
            "schema": "ppt-master.workspace-resources.v1",
            "items": [
                resource.manifest_row(
                    materialized=include_images or resource.kind != "image",
                )
                for resource in self.resources
            ],
        }


@dataclass(frozen=True)
class WorkspaceResourceSpec:
    """One semantic resource mapped back to its source package part."""

    package_part: str
    kind: str
    workspace_path: Path
    materialized: bool
    source_sha256: str
    current_sha256: str | None
    owner_parts: tuple[str, ...]

    @property
    def changed(self) -> bool:
        """Return whether materialized workspace bytes differ from import."""
        return (
            self.materialized
            and self.current_sha256 is not None
            and self.current_sha256 != self.source_sha256
        )


def workspace_resource_specs(
    workspace: Path,
    manifest: dict[str, object],
) -> tuple[WorkspaceResourceSpec, ...]:
    """Validate and resolve the resource map used by round-trip export."""
    resources = manifest.get("resources")
    if not isinstance(resources, dict):
        raise RuntimeError("Round-trip manifest resources must be an object")
    if resources.get("schema") != "ppt-master.workspace-resources.v1":
        raise RuntimeError(
            "Unsupported round-trip resource schema: "
            f"{resources.get('schema')!r}"
        )
    items = resources.get("items")
    if not isinstance(items, list):
        raise RuntimeError("Round-trip manifest resources.items must be an array")

    workspace_root = workspace.resolve()
    specs: list[WorkspaceResourceSpec] = []
    changed_payloads: list[tuple[WorkspaceResourceSpec, bytes]] = []
    seen_package_parts: set[str] = set()
    for index, raw in enumerate(items):
        context = f"round-trip resources.items[{index}]"
        if not isinstance(raw, dict):
            raise RuntimeError(f"{context} must be an object")
        package_part = raw.get("packagePart")
        kind = raw.get("kind")
        workspace_path = raw.get("workspacePath")
        materialized = raw.get("materialized")
        source_sha256 = raw.get("sha256")
        raw_owner_parts = raw.get("ownerParts")
        if not isinstance(package_part, str) or not package_part:
            raise RuntimeError(f"{context}.packagePart must be a non-empty string")
        package_path = PurePosixPath(package_part)
        if (
            package_path.is_absolute()
            or ".." in package_path.parts
            or "\\" in package_part
            or not any(
                package_part.startswith(prefix)
                for prefix in (
                    "ppt/media/",
                    "ppt/embeddings/",
                    "ppt/model3d/",
                )
            )
        ):
            raise RuntimeError(
                f"{context}.packagePart is outside the supported PPTX payload roots"
            )
        if package_part in seen_package_parts:
            raise RuntimeError(f"{context} repeats package part {package_part!r}")
        if not isinstance(kind, str) or not kind:
            raise RuntimeError(f"{context}.kind must be a non-empty string")
        if not isinstance(workspace_path, str) or not workspace_path:
            raise RuntimeError(f"{context}.workspacePath must be a non-empty string")
        relative = Path(workspace_path)
        if (
            relative.drive
            or relative.anchor
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise RuntimeError(f"{context}.workspacePath must stay project-relative")
        resolved = (workspace_root / relative).resolve()
        try:
            resolved.relative_to(workspace_root)
        except ValueError as exc:
            raise RuntimeError(
                f"{context}.workspacePath resolves outside the project"
            ) from exc
        if not isinstance(materialized, bool):
            raise RuntimeError(f"{context}.materialized must be a boolean")
        if materialized and not resolved.is_file():
            raise RuntimeError(
                f"Materialized round-trip resource is missing: {workspace_path}"
            )
        if (
            not isinstance(source_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None
        ):
            raise RuntimeError(f"{context}.sha256 must be a lowercase SHA-256")
        if not isinstance(raw_owner_parts, list) or not all(
            isinstance(value, str) and value
            for value in raw_owner_parts
        ):
            raise RuntimeError(f"{context}.ownerParts must be an array of parts")
        payload = resolved.read_bytes() if materialized else None
        current_sha256 = _sha256(payload) if payload is not None else None
        spec = WorkspaceResourceSpec(
            package_part=package_part,
            kind=kind,
            workspace_path=relative,
            materialized=materialized,
            source_sha256=source_sha256,
            current_sha256=current_sha256,
            owner_parts=tuple(raw_owner_parts),
        )
        specs.append(spec)
        if payload is not None and spec.changed:
            changed_payloads.append((spec, payload))
        seen_package_parts.add(package_part)

    if changed_payloads:
        source_path = source_pptx_path(workspace_root)
        if not source_path.is_file():
            raise RuntimeError(
                "Changed round-trip resources require the preserved source PPTX: "
                f"{source_path}"
            )
        try:
            with zipfile.ZipFile(source_path) as package:
                defaults, overrides = _package_content_types(package)
                names = set(package.namelist())
                for spec, payload in changed_payloads:
                    if spec.package_part not in names:
                        raise RuntimeError(
                            "Round-trip source package part is missing: "
                            f"{spec.package_part}"
                        )
                    suffix = (
                        PurePosixPath(spec.package_part).suffix.lstrip(".").lower()
                    )
                    content_type = overrides.get(spec.package_part) or defaults.get(
                        suffix,
                    )
                    if not content_type:
                        raise RuntimeError(
                            "Round-trip source package part has no Content-Type: "
                            f"{spec.package_part}"
                        )
                    _validate_changed_resource_format(
                        spec=spec,
                        payload=payload,
                        source_payload=package.read(spec.package_part),
                        content_type=content_type,
                    )
        except zipfile.BadZipFile as exc:
            raise RuntimeError(
                f"Round-trip source PPTX is not a valid ZIP package: {source_path}"
            ) from exc
    return tuple(specs)


def _is_semantic_owner_part(package_part: str) -> bool:
    return any(
        package_part.startswith(prefix)
        for prefix in (
            "ppt/slides/slide",
            "ppt/slideLayouts/slideLayout",
            "ppt/slideMasters/slideMaster",
            "ppt/notesSlides/notesSlide",
        )
    ) and package_part.endswith(".xml")


def _resource_owner_parts(
    package_part: str,
    parents_by_target: dict[str, set[str]],
) -> tuple[str, ...]:
    """Resolve Slide/Layout/Master/Notes owners through relationship chains."""
    owners: set[str] = set()
    visited = {package_part}
    pending = [package_part]
    while pending:
        current = pending.pop()
        for parent in parents_by_target.get(current, set()):
            if parent in visited:
                continue
            visited.add(parent)
            if _is_semantic_owner_part(parent):
                owners.add(parent)
            else:
                pending.append(parent)
    return tuple(sorted(owners))


def _classify_resource(
    package_part: str,
    relationship_types: set[str],
    *,
    transition_only: bool,
) -> tuple[str, Path]:
    suffix = PurePosixPath(package_part).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image", Path("images")
    if (
        suffix in VIDEO_EXTENSIONS
        or any(rel_type.endswith("/video") for rel_type in relationship_types)
    ):
        return "video", Path("video")
    if suffix in AUDIO_EXTENSIONS:
        if transition_only:
            return "sound", Path("sounds")
        return "audio", Path("audio")
    if package_part.startswith("ppt/embeddings/"):
        return "native-payload", Path("native-payloads/embeddings")
    if package_part.startswith("ppt/model3d/"):
        return "native-payload", Path("native-payloads/model3d")
    return "native-payload", Path("native-payloads/media")


def inventory_package_resources(
    package: zipfile.ZipFile,
) -> PackageResourceInventory:
    """Classify reusable and opaque PPTX payloads into semantic directories."""
    references: dict[str, list[dict[str, object]]] = defaultdict(list)
    parents_by_target: dict[str, set[str]] = defaultdict(set)
    names = set(package.namelist())
    for rels_path in sorted(name for name in names if name.endswith(".rels")):
        source_part = _source_part_for_relationships(rels_path)
        transition_ids = _transition_relationship_ids(package, source_part)
        try:
            root = ET.fromstring(package.read(rels_path))
        except (KeyError, ET.ParseError):
            continue
        for relationship in root.findall(f"{{{_REL_NS}}}Relationship"):
            if relationship.attrib.get("TargetMode") == "External":
                continue
            rel_id = relationship.attrib.get("Id", "")
            rel_type = relationship.attrib.get("Type", "")
            target = relationship.attrib.get("Target", "")
            if not rel_id or not rel_type or not target:
                continue
            resolved = _resolve_relationship_target(source_part, target)
            if source_part:
                parents_by_target[resolved].add(source_part)
            references[resolved].append({
                "relationshipType": rel_type,
                "sourcePart": source_part or "",
                "transition": rel_id in transition_ids,
            })

    candidate_parts = sorted(
        name
        for name in names
        if not name.endswith("/")
        and (
            name.startswith("ppt/media/")
            or name.startswith("ppt/embeddings/")
            or name.startswith("ppt/model3d/")
        )
    )
    allocated: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    resources: list[PackageResource] = []
    for package_part in candidate_parts:
        rows = references.get(package_part, [])
        relationship_types = {
            str(row["relationshipType"])
            for row in rows
            if row.get("relationshipType")
        }
        transition_flags = [bool(row.get("transition")) for row in rows]
        transition_only = bool(transition_flags) and all(transition_flags)
        kind, directory = _classify_resource(
            package_part,
            relationship_types,
            transition_only=transition_only,
        )
        payload = package.read(package_part)
        digest = _sha256(payload)
        original_name = _safe_basename(PurePosixPath(package_part).name)
        key = (directory.as_posix(), original_name.lower())
        allocations = allocated[key]
        existing_name = next(
            (name for known_digest, name in allocations if known_digest == digest),
            None,
        )
        if existing_name is None:
            stem = Path(original_name).stem
            suffix = Path(original_name).suffix
            existing_name = (
                original_name
                if not allocations
                else f"{stem}_{len(allocations) + 1}{suffix}"
            )
            allocations.append((digest, existing_name))
        workspace_path = (directory / existing_name).as_posix()
        resources.append(PackageResource(
            package_part=package_part,
            kind=kind,
            workspace_path=workspace_path,
            payload=payload,
            relationship_types=tuple(sorted(relationship_types)),
            source_parts=tuple(sorted({
                str(row["sourcePart"])
                for row in rows
                if row.get("sourcePart")
            })),
            owner_parts=_resource_owner_parts(
                package_part,
                parents_by_target,
            ),
        ))
    return PackageResourceInventory(resources=tuple(resources))


def write_workspace_resources(
    workspace: Path,
    inventory: PackageResourceInventory,
    *,
    include_images: bool = True,
) -> tuple[str, ...]:
    """Write the exact resource inventory without overwriting different bytes."""
    written: list[str] = []
    for resource in inventory.resources:
        if resource.kind == "image" and not include_images:
            continue
        relative = Path(resource.workspace_path)
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not target.is_file() or target.read_bytes() != resource.payload:
                raise RuntimeError(
                    "Semantic resource path collides with different content: "
                    f"{relative}"
                )
        else:
            target.write_bytes(resource.payload)
        written.append(relative.as_posix())
    return tuple(written)


def load_roundtrip_manifest(workspace: Path) -> dict[str, object] | None:
    """Load the semantic round-trip manifest when present."""
    path = workspace / ROUNDTRIP_MANIFEST_PATH
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read round-trip manifest {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"Round-trip manifest must be a JSON object: {path}")
    return raw


def slide_animation_config_sha256(
    config: dict[str, object],
    slide_stem: str,
) -> str:
    """Hash global motion settings plus one slide's animation configuration."""
    slides = config.get("slides")
    slide_config = slides.get(slide_stem) if isinstance(slides, dict) else None
    payload = {
        "global": {
            key: value
            for key, value in config.items()
            if key != "slides"
        },
        "slide": slide_config,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(serialized)


__all__ = [
    "AUDIO_EXTENSIONS",
    "CONVERSION_REPORT_PATH",
    "REMOVED_WORKSPACE_ENTRIES",
    "IMAGE_EXTENSIONS",
    "NATIVE_STRUCTURE_PATH",
    "PackageResource",
    "PackageResourceInventory",
    "ROUNDTRIP_MANIFEST_PATH",
    "ROUNDTRIP_PAGE_PLAN_PATH",
    "SOURCE_PPTX_PATH",
    "TEMPLATE_MANIFEST_PATH",
    "VIDEO_EXTENSIONS",
    "WorkspaceResourceSpec",
    "conversion_report_path",
    "inventory_package_resources",
    "load_roundtrip_manifest",
    "native_structure_path",
    "reject_removed_workspace_layout",
    "roundtrip_page_plan_path",
    "source_pptx_path",
    "slide_animation_config_sha256",
    "template_manifest_path",
    "write_workspace_resources",
    "workspace_resource_specs",
]
