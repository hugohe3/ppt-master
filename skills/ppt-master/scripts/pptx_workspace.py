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
TEMPLATE_MANIFEST_PATH = Path("analysis/manifest.json")
CONVERSION_REPORT_PATH = Path("validation/conversion-report.json")
AUTHORING_SVG_FLAT_DIR = Path("authoring-svg-flat")
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


def source_pptx_path(workspace: Path) -> Path:
    """Return the semantic preserved-source package path."""
    return workspace / SOURCE_PPTX_PATH


def native_structure_path(workspace: Path) -> Path:
    """Return the semantic native-structure contract path."""
    return workspace / NATIVE_STRUCTURE_PATH


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
    seen_package_parts: set[str] = set()
    for index, raw in enumerate(items):
        context = f"round-trip resources.items[{index}]"
        if not isinstance(raw, dict):
            raise RuntimeError(f"{context} must be an object")
        package_part = raw.get("packagePart")
        kind = raw.get("kind")
        workspace_path = raw.get("workspacePath")
        materialized = raw.get("materialized")
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
        specs.append(WorkspaceResourceSpec(
            package_part=package_part,
            kind=kind,
            workspace_path=relative,
            materialized=materialized,
        ))
        seen_package_parts.add(package_part)
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
    "SOURCE_PPTX_PATH",
    "TEMPLATE_MANIFEST_PATH",
    "VIDEO_EXTENSIONS",
    "WorkspaceResourceSpec",
    "conversion_report_path",
    "inventory_package_resources",
    "load_roundtrip_manifest",
    "native_structure_path",
    "reject_removed_workspace_layout",
    "source_pptx_path",
    "slide_animation_config_sha256",
    "template_manifest_path",
    "write_workspace_resources",
    "workspace_resource_specs",
]
