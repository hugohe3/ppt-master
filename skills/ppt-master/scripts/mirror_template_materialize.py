#!/usr/bin/env python3
"""
PPT Master - Mirror Template Materializer

Materialize a deterministic structured SVG template workspace from one Type A
PPTX import workspace. The editable authoring IR is the only authoring input;
lossless SVG files are consulted solely to restore unchanged supported source
objects. Final templates and imported vectors contain no IR-only source refs.

Usage:
    python3 scripts/mirror_template_materialize.py \
        <import_workspace> <template_workspace>

Dependencies:
    None (standard library and sibling PPT Master modules only).
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from pptx_shapes import svg_preset_preview_fingerprint
from svg_authoring_view import (
    AUTHORING_MANIFEST_NAME,
    AUTHORING_SCHEMA,
    SOURCE_REF_ATTRIBUTE,
    semantic_subtree_sha256,
)
from svg_to_pptx.pptx_package.template_structure import (
    TemplateStructureError,
    parse_template_slides,
)

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NATIVE_STRUCTURE_SCHEMA = "ppt-master.native-structure.v1"
VECTOR_INVENTORY_SCHEMA = "vector_asset_inventory.v1"
IMPORTED_ICON_NAMESPACE = "imported"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

_NON_VISUAL_TAGS = frozenset({"defs", "desc", "metadata", "style", "title"})
_BITMAP_EXTENSIONS = frozenset({
    ".avif",
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
})
_INHERITED_PRESENTATION_ATTRIBUTES = frozenset({
    "color",
    "fill",
    "fill-opacity",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "paint-order",
    "shape-rendering",
    "stroke",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-opacity",
    "stroke-width",
    "text-anchor",
    "text-decoration",
    "word-spacing",
})
_AGGREGATE_GROUP_ATTRIBUTES = frozenset({
    "clip-path",
    "filter",
    "mask",
    "mix-blend-mode",
    "opacity",
})
_URL_REFERENCE_RE = re.compile(r"url\(\s*(['\"]?)#([^)'\"\s]+)\1\s*\)")
_CSS_ID_RE = re.compile(r"#([A-Za-z_][A-Za-z0-9_.:-]*)")
_SAFE_KEY_RE = re.compile(r"[^A-Za-z0-9_.-]+")


class MirrorMaterializationError(RuntimeError):
    """Reject incomplete, ambiguous, or unsafe mirror materialization input."""


@dataclass(frozen=True)
class SourceRefRecord:
    source_path: tuple[int, ...]
    initial_authoring_subtree_sha256: str


@dataclass(frozen=True)
class AuthoringDocument:
    name: str
    authoring_path: Path
    source_path: Path
    source_sha256: str
    source_refs: dict[str, SourceRefRecord]


@dataclass(frozen=True)
class VectorAssetRecord:
    icon: str
    asset_path: Path
    origin_document: str
    expected_sha256: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class SlotPlan:
    slot_id: str
    semantic_role: str
    placeholder_type: str | None
    idx: int | None
    shape_id: str
    bounds: tuple[float, float, float, float]


@dataclass
class RestorationStats:
    rehydrated_refs: int = 0
    fallback_refs: int = 0
    structural_refs: int = 0
    detached_connector_endpoints: int = 0

    def merge(self, other: "RestorationStats") -> None:
        self.rehydrated_refs += other.rehydrated_refs
        self.fallback_refs += other.fallback_refs
        self.structural_refs += other.structural_refs
        self.detached_connector_endpoints += other.detached_connector_endpoints

    def as_dict(self) -> dict[str, int]:
        return {
            "rehydrated_refs": self.rehydrated_refs,
            "fallback_refs": self.fallback_refs,
            "structural_refs": self.structural_refs,
            "detached_connector_endpoints": self.detached_connector_endpoints,
        }


@dataclass
class MaterializedFile:
    relative_path: Path
    payload: bytes


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path, *, context: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MirrorMaterializationError(f"Cannot read {context}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise MirrorMaterializationError(
            f"Invalid JSON in {context}: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise MirrorMaterializationError(f"{context} must be a JSON object: {path}")
    return payload


def _require_list(value: object, *, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise MirrorMaterializationError(f"{context} must be a list")
    return value


def _require_string(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MirrorMaterializationError(f"{context} must be a non-empty string")
    return value.strip()


def _require_boolean(value: object, *, context: str) -> bool:
    if not isinstance(value, bool):
        raise MirrorMaterializationError(f"{context} must be a boolean")
    return value


def _resolve_inside(root: Path, relative: str, *, context: str) -> Path:
    parsed = urlsplit(relative)
    if parsed.scheme or parsed.netloc or Path(parsed.path).is_absolute():
        raise MirrorMaterializationError(f"{context} must be a relative path: {relative}")
    resolved = (root / unquote(parsed.path)).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise MirrorMaterializationError(
            f"{context} escapes its declared root: {relative}"
        ) from exc
    return resolved


def _parse_svg(path: Path) -> ET.Element:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
    try:
        root = ET.fromstring(path.read_bytes(), parser=parser)
    except (OSError, ET.ParseError) as exc:
        raise MirrorMaterializationError(f"Cannot parse SVG {path}: {exc}") from exc
    if _local_name(root.tag) != "svg":
        raise MirrorMaterializationError(f"SVG root is not <svg>: {path}")
    return root


def _source_element(root: ET.Element, path: tuple[int, ...]) -> ET.Element:
    element = root
    try:
        for index in path:
            element = list(element)[index]
    except (IndexError, TypeError) as exc:
        raise MirrorMaterializationError(
            f"Source-ref path no longer resolves: {list(path)}"
        ) from exc
    return element


def _source_identity(element: ET.Element) -> str | None:
    scope = element.get("data-pptx-shape-scope")
    shape_id = element.get("data-pptx-shape-id")
    if not scope or not shape_id:
        return None
    return f"{scope}:{shape_id}"


def _load_authoring_documents(
    workspace: Path,
) -> tuple[Path, dict[str, AuthoringDocument]]:
    authoring_root = workspace / "authoring-svg"
    manifest_path = authoring_root / AUTHORING_MANIFEST_NAME
    manifest = _load_json(manifest_path, context="authoring manifest")
    if manifest.get("schema") != AUTHORING_SCHEMA:
        raise MirrorMaterializationError(
            f"Unsupported authoring manifest schema: {manifest.get('schema')!r}"
        )
    if manifest.get("projection_kind") != "layered":
        raise MirrorMaterializationError(
            "Mirror materialization requires projection_kind='layered'"
        )
    if manifest.get("authoring_root") != ".":
        raise MirrorMaterializationError("authoring_manifest.json authoring_root must be '.'")
    if manifest.get("source_ref_attribute") != SOURCE_REF_ATTRIBUTE:
        raise MirrorMaterializationError(
            "authoring_manifest.json uses an unsupported source-ref attribute"
        )

    source_root_raw = _require_string(
        manifest.get("source_root"),
        context="authoring_manifest.json source_root",
    )
    source_root = (authoring_root / source_root_raw).resolve()
    expected_source_root = (workspace / "svg").resolve()
    if source_root != expected_source_root:
        raise MirrorMaterializationError(
            "Type A mirror authoring manifest must resolve source_root to "
            f"{expected_source_root}, found {source_root}"
        )

    documents_raw = _require_list(
        manifest.get("documents"),
        context="authoring_manifest.json documents",
    )
    documents: dict[str, AuthoringDocument] = {}
    for index, raw in enumerate(documents_raw):
        if not isinstance(raw, dict):
            raise MirrorMaterializationError(f"documents[{index}] must be an object")
        authoring_name = _require_string(
            raw.get("authoring"),
            context=f"documents[{index}].authoring",
        )
        source_name = _require_string(
            raw.get("source"),
            context=f"documents[{index}].source",
        )
        if authoring_name in documents:
            raise MirrorMaterializationError(
                f"Duplicate authoring manifest document: {authoring_name}"
            )
        authoring_path = _resolve_inside(
            authoring_root,
            authoring_name,
            context=f"documents[{index}].authoring",
        )
        source_path = _resolve_inside(
            source_root,
            source_name,
            context=f"documents[{index}].source",
        )
        if not authoring_path.is_file() or authoring_path.suffix.lower() != ".svg":
            raise MirrorMaterializationError(
                f"Authoring SVG is missing: {authoring_path}"
            )
        if not source_path.is_file() or source_path.suffix.lower() != ".svg":
            raise MirrorMaterializationError(f"Lossless source SVG is missing: {source_path}")

        expected_source_sha = _require_string(
            raw.get("source_sha256"),
            context=f"documents[{index}].source_sha256",
        )
        actual_source_sha = _sha256_file(source_path)
        if actual_source_sha != expected_source_sha:
            raise MirrorMaterializationError(
                f"Lossless source SVG changed: {source_path.name}; expected "
                f"{expected_source_sha}, found {actual_source_sha}"
            )

        refs_raw = raw.get("source_refs")
        if not isinstance(refs_raw, dict):
            raise MirrorMaterializationError(
                f"documents[{index}].source_refs must be an object"
            )
        refs: dict[str, SourceRefRecord] = {}
        source_root_element = _parse_svg(source_path)
        for source_ref, ref_raw in refs_raw.items():
            if not isinstance(source_ref, str) or not isinstance(ref_raw, dict):
                raise MirrorMaterializationError(
                    f"Invalid source-ref record in {authoring_name}"
                )
            path_raw = ref_raw.get("source_path")
            if not (
                isinstance(path_raw, list)
                and all(isinstance(item, int) and item >= 0 for item in path_raw)
            ):
                raise MirrorMaterializationError(
                    f"{authoring_name} source ref {source_ref!r} has invalid source_path"
                )
            initial_hash = _require_string(
                ref_raw.get("initial_authoring_subtree_sha256"),
                context=f"{authoring_name} source ref {source_ref!r} hash",
            )
            source_path_tuple = tuple(path_raw)
            source_element = _source_element(source_root_element, source_path_tuple)
            if _source_identity(source_element) != source_ref:
                raise MirrorMaterializationError(
                    f"{authoring_name} source ref {source_ref!r} resolves to "
                    f"{_source_identity(source_element)!r}"
                )
            refs[source_ref] = SourceRefRecord(source_path_tuple, initial_hash)

        documents[authoring_name] = AuthoringDocument(
            name=authoring_name,
            authoring_path=authoring_path,
            source_path=source_path,
            source_sha256=expected_source_sha,
            source_refs=refs,
        )

    actual_authoring_files = {
        path.relative_to(authoring_root).as_posix()
        for path in authoring_root.rglob("*.svg")
        if path.is_file()
    }
    if actual_authoring_files != set(documents):
        raise MirrorMaterializationError(
            "Authoring manifest/file roster differs; missing="
            f"{sorted(set(documents) - actual_authoring_files)}, extra="
            f"{sorted(actual_authoring_files - set(documents))}"
        )
    if manifest.get("file_count") != len(documents):
        raise MirrorMaterializationError(
            "authoring_manifest.json file_count does not match documents"
        )
    expected_ref_count = sum(len(document.source_refs) for document in documents.values())
    if manifest.get("source_ref_count") != expected_ref_count:
        raise MirrorMaterializationError(
            "authoring_manifest.json source_ref_count does not match documents"
        )
    return authoring_root, documents


def _load_vector_assets(
    workspace: Path,
    documents: dict[str, AuthoringDocument],
) -> dict[str, VectorAssetRecord]:
    inventory_path = workspace / "authoring-svg_vector_asset_inventory.json"
    if not inventory_path.exists():
        return {}
    inventory = _load_json(inventory_path, context="vector asset inventory")
    if inventory.get("schema") != VECTOR_INVENTORY_SCHEMA:
        raise MirrorMaterializationError(
            f"Unsupported vector inventory schema: {inventory.get('schema')!r}"
        )
    if inventory.get("icon_namespace") != IMPORTED_ICON_NAMESPACE:
        raise MirrorMaterializationError(
            "Mirror vector inventory must use icon_namespace='imported'"
        )
    icons_root = workspace / "icons"
    records: dict[str, VectorAssetRecord] = {}
    for index, raw in enumerate(
        _require_list(inventory.get("assets"), context="vector inventory assets")
    ):
        if not isinstance(raw, dict):
            raise MirrorMaterializationError(f"vector assets[{index}] must be an object")
        icon = _require_string(raw.get("icon"), context=f"assets[{index}].icon")
        asset = _require_string(raw.get("asset"), context=f"assets[{index}].asset")
        origin = _require_string(raw.get("svg"), context=f"assets[{index}].svg")
        if not icon.startswith(f"{IMPORTED_ICON_NAMESPACE}/"):
            raise MirrorMaterializationError(
                f"Vector asset {icon!r} is outside imported/ namespace"
            )
        if icon in records:
            raise MirrorMaterializationError(f"Duplicate vector asset id: {icon}")
        if origin not in documents:
            raise MirrorMaterializationError(
                f"Vector asset {icon!r} names unknown origin document {origin!r}"
            )
        asset_path = _resolve_inside(
            icons_root,
            asset,
            context=f"vector asset {icon!r}",
        )
        if not asset_path.is_file() or asset_path.suffix.lower() != ".svg":
            raise MirrorMaterializationError(f"Vector asset is missing: {asset_path}")
        expected_sha256 = _require_string(
            raw.get("asset_sha256"),
            context=f"vector asset {icon!r} asset_sha256",
        )
        actual_sha256 = _sha256_file(asset_path)
        if actual_sha256 != expected_sha256:
            raise MirrorMaterializationError(
                f"Vector asset {icon!r} changed; expected {expected_sha256}, "
                f"found {actual_sha256}"
            )
        refs_raw = _require_list(
            raw.get("source_refs", []),
            context=f"vector asset {icon!r} source_refs",
        )
        if not all(isinstance(item, str) and item for item in refs_raw):
            raise MirrorMaterializationError(
                f"Vector asset {icon!r} source_refs must be strings"
            )
        records[icon] = VectorAssetRecord(
            icon=icon,
            asset_path=asset_path,
            origin_document=origin,
            expected_sha256=expected_sha256,
            source_refs=tuple(refs_raw),
        )
    if inventory.get("asset_count") != len(records):
        raise MirrorMaterializationError("Vector inventory asset_count is stale")
    return records


def _source_ref_counts(root: ET.Element) -> dict[str, int]:
    counts: dict[str, int] = {}
    for element in root.iter():
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if source_ref:
            counts[source_ref] = counts.get(source_ref, 0) + 1
    return counts


def _imported_icon_refs(root: ET.Element) -> set[str]:
    return {
        value
        for element in root.iter()
        if (value := (element.get("data-icon") or "").strip())
        if value.startswith(f"{IMPORTED_ICON_NAMESPACE}/")
    }


def _validate_source_ref_closure(
    documents: dict[str, AuthoringDocument],
    vector_assets: dict[str, VectorAssetRecord],
) -> set[str]:
    direct_counts: dict[str, dict[str, int]] = {}
    referenced_icons: set[str] = set()
    for name, document in documents.items():
        root = _parse_svg(document.authoring_path)
        direct_counts[name] = _source_ref_counts(root)
        referenced_icons.update(_imported_icon_refs(root))

    unknown_icons = sorted(referenced_icons - set(vector_assets))
    if unknown_icons:
        raise MirrorMaterializationError(
            "Authoring SVG references missing imported vector asset(s): "
            + ", ".join(unknown_icons)
        )

    asset_counts_by_document: dict[str, dict[str, int]] = {
        name: {} for name in documents
    }
    for icon in sorted(referenced_icons):
        record = vector_assets[icon]
        root = _parse_svg(record.asset_path)
        counts = _source_ref_counts(root)
        if set(counts) != set(record.source_refs):
            raise MirrorMaterializationError(
                f"Vector asset {icon!r} source-ref inventory is stale; expected "
                f"{sorted(record.source_refs)}, found {sorted(counts)}"
            )
        duplicate_refs = sorted(ref for ref, count in counts.items() if count != 1)
        if duplicate_refs:
            raise MirrorMaterializationError(
                f"Vector asset {icon!r} contains duplicate source refs: "
                + ", ".join(duplicate_refs)
            )
        origin_counts = asset_counts_by_document[record.origin_document]
        for source_ref, count in counts.items():
            origin_counts[source_ref] = origin_counts.get(source_ref, 0) + count

    for name, document in documents.items():
        combined = dict(direct_counts[name])
        for source_ref, count in asset_counts_by_document[name].items():
            combined[source_ref] = combined.get(source_ref, 0) + count
        expected = set(document.source_refs)
        actual = set(combined)
        duplicates = sorted(ref for ref, count in combined.items() if count != 1)
        if actual != expected or duplicates:
            raise MirrorMaterializationError(
                f"{name} source-ref closure differs from its manifest; missing="
                f"{sorted(expected - actual)}, extra={sorted(actual - expected)}, "
                f"duplicates={duplicates}"
            )
    return referenced_icons


def _load_native_graph(workspace: Path) -> dict[str, Any]:
    native_path = workspace / "native_structure.json"
    native = _load_json(native_path, context="native structure")
    if native.get("schema") != NATIVE_STRUCTURE_SCHEMA:
        raise MirrorMaterializationError(
            f"Unsupported native structure schema: {native.get('schema')!r}"
        )
    source = native.get("source")
    if not isinstance(source, dict):
        raise MirrorMaterializationError("native_structure.json source must be an object")
    template_name = _require_string(
        source.get("templateFile"),
        context="native_structure.json source.templateFile",
    )
    template_path = _resolve_inside(
        workspace,
        template_name,
        context="native source template",
    )
    if not template_path.is_file():
        raise MirrorMaterializationError(f"Native source template is missing: {template_path}")
    expected_sha = _require_string(
        source.get("sha256"),
        context="native_structure.json source.sha256",
    )
    actual_sha = _sha256_file(template_path)
    if actual_sha != expected_sha:
        raise MirrorMaterializationError(
            f"Native source template changed; expected {expected_sha}, found {actual_sha}"
        )

    slide_size = native.get("slideSize")
    if not isinstance(slide_size, dict):
        raise MirrorMaterializationError("native_structure.json slideSize is missing")
    for field in ("width_px", "height_px"):
        value = slide_size.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise MirrorMaterializationError(f"native slideSize.{field} must be positive")
    return native


def _load_inheritance(workspace: Path) -> dict[str, Any]:
    return _load_json(workspace / "svg" / "inheritance.json", context="inheritance graph")


def _validate_graph_roster(
    native: dict[str, Any],
    inheritance: dict[str, Any],
    documents: dict[str, AuthoringDocument],
) -> None:
    masters = _require_list(native.get("masters"), context="native masters")
    layouts = _require_list(native.get("layouts"), context="native layouts")
    slides = _require_list(native.get("slides"), context="native slides")
    inheritance_masters_raw = _require_list(
        inheritance.get("masters"),
        context="inheritance masters",
    )
    master_file_by_part = {
        _require_string(item.get("partPath"), context="inheritance Master partPath"):
        _require_string(item.get("file"), context="inheritance Master file")
        for item in inheritance_masters_raw
        if isinstance(item, dict)
    }
    for index, master in enumerate(masters):
        if not isinstance(master, dict):
            raise MirrorMaterializationError(f"native masters[{index}] must be an object")
        package_part = _require_string(
            master.get("packagePart"),
            context=f"native masters[{index}].packagePart",
        )
        svg_file = master_file_by_part.get(package_part)
        if svg_file is None:
            raise MirrorMaterializationError(
                f"Native Master part {package_part!r} has no inheritance SVG file"
            )
        master["svgFile"] = svg_file
    expected_files: set[str] = set()
    for collection, field in (
        (masters, "svgFile"),
        (layouts, "svgFile"),
        (slides, "layeredSvgFile"),
    ):
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                raise MirrorMaterializationError(f"native {field}[{index}] must be an object")
            expected_files.add(
                _require_string(item.get(field), context=f"native {field}[{index}]")
            )
    if expected_files != set(documents):
        raise MirrorMaterializationError(
            "Native graph and authoring document roster differ; missing="
            f"{sorted(expected_files - set(documents))}, extra="
            f"{sorted(set(documents) - expected_files)}"
        )

    inherited_masters = {
        _require_string(item.get("file"), context="inheritance master file")
        for item in inheritance_masters_raw
        if isinstance(item, dict)
    }
    inherited_layouts = {
        _require_string(item.get("file"), context="inheritance layout file"): item
        for item in _require_list(inheritance.get("layouts"), context="inheritance layouts")
        if isinstance(item, dict)
    }
    inherited_slides = {
        int(item.get("index")): item
        for item in _require_list(inheritance.get("slides"), context="inheritance slides")
        if isinstance(item, dict) and isinstance(item.get("index"), int)
    }
    if inherited_masters != {item["svgFile"] for item in masters}:
        raise MirrorMaterializationError("Inheritance Master roster differs from native graph")
    if set(inherited_layouts) != {item["svgFile"] for item in layouts}:
        raise MirrorMaterializationError("Inheritance Layout roster differs from native graph")
    if set(inherited_slides) != {int(item["index"]) for item in slides}:
        raise MirrorMaterializationError("Inheritance Slide roster differs from native graph")

    master_file_by_key = {item["key"]: item["svgFile"] for item in masters}
    layout_file_by_key = {item["key"]: item["svgFile"] for item in layouts}
    for layout in layouts:
        inherited = inherited_layouts[layout["svgFile"]]
        if inherited.get("master") != master_file_by_key.get(layout.get("masterKey")):
            raise MirrorMaterializationError(
                f"Layout {layout.get('key')!r} Master parent differs across native facts"
            )
        inherited_visibility = _require_boolean(
            inherited.get("showMasterShapes"),
            context=f"inheritance Layout {layout.get('key')!r} showMasterShapes",
        )
        native_visibility = _require_boolean(
            layout.get("showMasterShapes"),
            context=f"native Layout {layout.get('key')!r} showMasterShapes",
        )
        if inherited_visibility != native_visibility:
            raise MirrorMaterializationError(
                f"Layout {layout.get('key')!r} showMasterShapes differs across facts"
            )
    for slide in slides:
        inherited = inherited_slides[int(slide["index"])]
        if inherited.get("layout") != layout_file_by_key.get(slide.get("layoutKey")):
            raise MirrorMaterializationError(
                f"Slide {slide.get('index')} Layout parent differs across native facts"
            )
        if inherited.get("master") != master_file_by_key.get(slide.get("masterKey")):
            raise MirrorMaterializationError(
                f"Slide {slide.get('index')} Master parent differs across native facts"
            )
        inherited_visibility = _require_boolean(
            inherited.get("showInheritedShapes"),
            context=f"inheritance Slide {slide.get('index')} showInheritedShapes",
        )
        native_visibility = _require_boolean(
            slide.get("showInheritedShapes"),
            context=f"native Slide {slide.get('index')} showInheritedShapes",
        )
        if inherited_visibility != native_visibility:
            raise MirrorMaterializationError(
                f"Slide {slide.get('index')} showInheritedShapes differs across facts"
            )


def _absolutize_local_hrefs(root: ET.Element, base_dir: Path) -> None:
    for element in root.iter():
        for attribute in ("href", f"{{{XLINK_NS}}}href"):
            value = element.get(attribute)
            if not value or value.startswith("#"):
                continue
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            absolute = (base_dir / unquote(parsed.path)).resolve().as_posix()
            element.set(
                attribute,
                urlunsplit(("", "", absolute, parsed.query, parsed.fragment)),
            )


def _rehydrate_tree(
    root: ET.Element,
    document: AuthoringDocument,
    *,
    excluded_refs: set[str],
) -> RestorationStats:
    source_root = _parse_svg(document.source_path)
    stats = RestorationStats()

    def restore(element: ET.Element) -> ET.Element:
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        record = document.source_refs.get(source_ref or "")
        if source_ref and record is None:
            raise MirrorMaterializationError(
                f"{document.name} contains unknown source ref {source_ref!r}"
            )
        if source_ref and source_ref in excluded_refs:
            stats.structural_refs += 1
        elif source_ref and record is not None:
            actual_hash = semantic_subtree_sha256(
                element,
                ignored_attributes=frozenset({SOURCE_REF_ATTRIBUTE}),
            )
            if actual_hash == record.initial_authoring_subtree_sha256:
                restored = copy.deepcopy(_source_element(source_root, record.source_path))
                _absolutize_local_hrefs(restored, document.source_path.parent)
                stats.rehydrated_refs += 1
                return restored
            stats.fallback_refs += 1

        children = list(element)
        for index, child in enumerate(children):
            replacement = restore(child)
            if replacement is child:
                continue
            replacement.tail = child.tail
            element.remove(child)
            element.insert(index, replacement)
        return element

    restore(root)
    return stats


def _line_groups(text: ET.Element) -> list[list[ET.Element]]:
    """Return direct tspan runs grouped by their imported visual line."""
    groups: list[list[ET.Element]] = []
    for tspan in text:
        if _local_name(tspan.tag) != "tspan":
            return []
        raw_dy = _optional_float(tspan.get("dy"))
        starts_line = (
            not groups
            or tspan.get("x") is not None
            or tspan.get("y") is not None
            or (raw_dy is not None and abs(raw_dy) > 1e-9)
        )
        if starts_line:
            groups.append([tspan])
        else:
            groups[-1].append(tspan)
    return groups


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _text_body_segments(metadata: ET.Element) -> list[list[str]] | None:
    if metadata.get("data-pptx-encoding") != "base64":
        return None
    try:
        payload = base64.b64decode((metadata.text or "").strip(), validate=True)
        text_body = ET.fromstring(payload)
    except (ValueError, ET.ParseError):
        return None

    paragraphs: list[list[str]] = []
    for paragraph in text_body:
        if _local_name(paragraph.tag) != "p":
            continue
        segments = [""]
        for child in paragraph:
            tag = _local_name(child.tag)
            if tag == "br":
                segments.append("")
            elif tag in {"r", "fld"}:
                segments[-1] += "".join(
                    node.text or ""
                    for node in child.iter()
                    if _local_name(node.tag) == "t"
                )
        paragraphs.append(segments)
    return paragraphs


def _mark_explicit_breaks(
    authored_element: ET.Element,
    source_element: ET.Element,
) -> None:
    metadata = next(
        (
            child
            for child in source_element
            if _local_name(child.tag) == "metadata"
            and child.get("data-pptx-part") == "txbody"
        ),
        None,
    )
    if metadata is None:
        return
    paragraphs = _text_body_segments(metadata)
    if paragraphs is None:
        return
    authored_texts = [
        child for child in authored_element if _local_name(child.tag) == "text"
    ]
    if len(authored_texts) != len(paragraphs):
        return

    pending: list[ET.Element] = []
    for text, segments in zip(authored_texts, paragraphs):
        groups = _line_groups(text)
        if not groups:
            if len(segments) > 1:
                return
            continue
        line_texts = [
            _normalized_text(
                "".join(text for node in group for text in node.itertext())
            )
            for group in groups
        ]
        cursor = 0
        for segment_index, segment in enumerate(segments):
            target = _normalized_text(segment)
            combined = ""
            start = cursor
            while cursor < len(line_texts):
                combined = _normalized_text(" ".join((combined, line_texts[cursor])))
                cursor += 1
                if combined == target:
                    break
                if target and not target.startswith(combined):
                    return
            if combined != target:
                return
            if segment_index > 0 and start < len(groups):
                pending.append(groups[start][0])
        if cursor != len(groups):
            return
    for tspan in pending:
        tspan.set("data-paragraph-soft-break", "0")


def _annotate_unchanged_explicit_text_breaks(
    root: ET.Element,
    document: AuthoringDocument,
    excluded_refs: set[str],
) -> None:
    """Recover native a:br semantics without restoring a stale txBody."""
    if not excluded_refs:
        return
    source_root = _parse_svg(document.source_path)
    for element in root.iter():
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        record = document.source_refs.get(source_ref or "")
        if source_ref not in excluded_refs or record is None:
            continue
        actual_hash = semantic_subtree_sha256(
            element,
            ignored_attributes=frozenset({SOURCE_REF_ATTRIBUTE}),
        )
        if actual_hash != record.initial_authoring_subtree_sha256:
            continue
        _mark_explicit_breaks(
            element,
            _source_element(source_root, record.source_path),
        )


def _prepared_document(
    document: AuthoringDocument,
    *,
    excluded_refs: set[str],
) -> tuple[ET.Element, RestorationStats]:
    root = _parse_svg(document.authoring_path)
    _absolutize_local_hrefs(root, document.authoring_path.parent)
    stats = _rehydrate_tree(root, document, excluded_refs=excluded_refs)
    _annotate_unchanged_explicit_text_breaks(root, document, excluded_refs)
    return root, stats


def _safe_prefix(value: str) -> str:
    normalized = _SAFE_KEY_RE.sub("-", value).strip("-.")
    return normalized or "node"


def _namespace_ids(root: ET.Element, prefix: str) -> None:
    mapping: dict[str, str] = {}
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            mapping[element_id] = f"{prefix}{_safe_prefix(element_id)}"
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            element.set("id", mapping[element_id])
        for name, value in list(element.attrib.items()):
            if name == "id":
                continue
            if value.startswith("#") and value[1:] in mapping:
                element.set(name, f"#{mapping[value[1:]]}")
                continue
            rewritten = _URL_REFERENCE_RE.sub(
                lambda match: f"url(#{mapping.get(match.group(2), match.group(2))})",
                value,
            )
            if name.rsplit("}", 1)[-1] in {"aria-describedby", "aria-labelledby"}:
                rewritten = " ".join(mapping.get(token, token) for token in rewritten.split())
            element.set(name, rewritten)
        if _local_name(element.tag) == "style" and element.text:
            element.text = _CSS_ID_RE.sub(
                lambda match: f"#{mapping.get(match.group(1), match.group(1))}",
                element.text,
            )


def _parse_style(value: str | None) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for raw in (value or "").split(";"):
        if ":" not in raw:
            continue
        name, declaration = raw.split(":", 1)
        if name.strip() and declaration.strip():
            declarations[name.strip().lower()] = declaration.strip()
    return declarations


def _style_text(declarations: dict[str, str]) -> str:
    return ";".join(f"{name}:{value}" for name, value in declarations.items())


def _hidden(element: ET.Element) -> bool:
    style = _parse_style(element.get("style"))
    display = (element.get("display") or style.get("display") or "").strip().lower()
    visibility = (
        element.get("visibility") or style.get("visibility") or ""
    ).strip().lower()
    opacity = (element.get("opacity") or style.get("opacity") or "").strip()
    if display == "none" or visibility in {"hidden", "collapse"}:
        return True
    try:
        return bool(opacity) and float(opacity) <= 0
    except ValueError:
        return False


def _paint_value(element: ET.Element, name: str) -> str | None:
    value = element.get(name)
    if value is not None:
        return value.strip().lower()
    return _parse_style(element.get("style")).get(name)


def _visible_leaf(element: ET.Element) -> bool:
    if _hidden(element):
        return False
    tag = _local_name(element.tag)
    if tag in _NON_VISUAL_TAGS:
        return False
    if tag in {"g", "svg", "a"}:
        return any(_visible_leaf(child) for child in element)
    if tag in {"rect", "image", "foreignObject"}:
        for dimension in ("width", "height"):
            raw = element.get(dimension)
            if raw is not None:
                try:
                    if float(raw) <= 0:
                        return False
                except ValueError:
                    pass
        return True
    if tag in {"line", "polyline"}:
        stroke = _paint_value(element, "stroke")
        return stroke not in {None, "none", "transparent"}
    if tag in {"path", "polygon", "circle", "ellipse"}:
        fill = _paint_value(element, "fill")
        stroke = _paint_value(element, "stroke")
        return not (
            fill in {"none", "transparent"}
            and stroke in {None, "none", "transparent"}
        )
    if tag == "text":
        return bool("".join(element.itertext()).strip())
    return True


def _merge_group_inheritance(parent: ET.Element, child: ET.Element) -> None:
    for name in _INHERITED_PRESENTATION_ATTRIBUTES:
        if parent.get(name) is not None and child.get(name) is None:
            child.set(name, parent.get(name, ""))
    parent_style = _parse_style(parent.get("style"))
    child_style = _parse_style(child.get("style"))
    if parent_style:
        merged = dict(parent_style)
        merged.update(child_style)
        child.set("style", _style_text(merged))
    parent_transform = (parent.get("transform") or "").strip()
    child_transform = (child.get("transform") or "").strip()
    if parent_transform:
        child.set(
            "transform",
            " ".join(item for item in (parent_transform, child_transform) if item),
        )


def _flatten_fixed_group(group: ET.Element, *, context: str) -> list[ET.Element]:
    visible_children = [child for child in group if _visible_leaf(child)]
    group_style = _parse_style(group.get("style"))
    aggregate_attrs = {
        name for name in _AGGREGATE_GROUP_ATTRIBUTES if group.get(name) is not None
    }
    aggregate_attrs.update(
        name
        for name in _AGGREGATE_GROUP_ATTRIBUTES
        if name in group_style
    )
    if len(visible_children) > 1 and aggregate_attrs:
        raise MirrorMaterializationError(
            f"{context} cannot expand a multi-child group with aggregate effect(s): "
            + ", ".join(sorted(aggregate_attrs))
        )

    atoms: list[ET.Element] = []
    for child in visible_children:
        child_style = _parse_style(child.get("style"))
        conflicting_aggregate_attrs = {
            name
            for name in aggregate_attrs
            if child.get(name) is not None or name in child_style
        }
        if conflicting_aggregate_attrs:
            raise MirrorMaterializationError(
                f"{context} cannot collapse nested aggregate effect(s): "
                + ", ".join(sorted(conflicting_aggregate_attrs))
            )
        item = copy.deepcopy(child)
        _merge_group_inheritance(group, item)
        for name in aggregate_attrs:
            if group.get(name) is not None:
                item.set(name, group.get(name, ""))
        if _local_name(item.tag) == "g":
            atoms.extend(_flatten_fixed_group(item, context=context))
        else:
            atoms.append(item)
    if len(atoms) == 1:
        atom = atoms[0]
        for name in ("data-pptx-frame", "data-pptx-object", "data-pptx-prst"):
            if group.get(name) is not None and atom.get(name) is None:
                atom.set(name, group.get(name, ""))
    return atoms


def _fixed_atoms(
    root: ET.Element,
    *,
    scope: str,
    key: str,
) -> list[ET.Element]:
    atoms: list[ET.Element] = []
    serial = 0
    for child in root:
        tag = _local_name(child.tag)
        if tag in _NON_VISUAL_TAGS or child.get("data-ph-type") is not None:
            continue
        if not _visible_leaf(child):
            continue
        if tag == "g":
            expanded = _flatten_fixed_group(
                child,
                context=f"{scope} {key} element {child.get('id') or '<g>'}",
            )
        else:
            expanded = [copy.deepcopy(child)]
        source_ref = child.get(SOURCE_REF_ATTRIBUTE)
        source_token = source_ref.split(":", 1)[-1] if source_ref else str(serial + 1)
        for part, atom in enumerate(expanded, start=1):
            serial += 1
            atom.set(
                "id",
                f"{scope}-{_safe_prefix(key)}-{_safe_prefix(source_token)}-{part}",
            )
            atom.set("data-pptx-layer", scope)
            atom.set("data-pptx-editable", "false")
            atom.attrib.pop("data-ph-type", None)
            atoms.append(atom)
    return atoms


def _frame(element: ET.Element | None) -> tuple[float, float, float, float] | None:
    if element is None:
        return None
    raw = (element.get("data-pptx-frame") or "").replace(",", " ").split()
    if len(raw) != 4:
        return None
    try:
        values = tuple(float(item) for item in raw)
    except ValueError:
        return None
    if not all(math.isfinite(item) for item in values) or values[2] <= 0 or values[3] <= 0:
        return None
    return values


def _element_by_ref(root: ET.Element, source_ref: str) -> ET.Element | None:
    matches = [
        element
        for element in root.iter()
        if element.get(SOURCE_REF_ATTRIBUTE) == source_ref
    ]
    if len(matches) > 1:
        raise MirrorMaterializationError(f"Duplicate source ref in document: {source_ref}")
    return matches[0] if matches else None


def _placeholder_guide_by_semantic(
    root: ET.Element,
    semantic_role: str,
) -> ET.Element | None:
    matches = []
    for element in root.iter():
        placeholder_type = element.get("data-ph-type")
        if not placeholder_type:
            continue
        if _semantic_role({"type": placeholder_type}) == semantic_role:
            matches.append(element)
    return matches[0] if len(matches) == 1 else None


def _placeholder_idx(raw: object) -> int | None:
    if raw is None:
        return None
    try:
        value = int(str(raw))
    except ValueError as exc:
        raise MirrorMaterializationError(f"Invalid placeholder idx: {raw!r}") from exc
    if value < 0:
        raise MirrorMaterializationError(f"Placeholder idx must be non-negative: {raw!r}")
    return value


def _semantic_role(placeholder: dict[str, Any]) -> str:
    role = str(placeholder.get("semanticRole") or "").strip()
    placeholder_type = str(placeholder.get("type") or "").strip()
    mapping = {
        "ctrTitle": "title",
        "title": "title",
        "subTitle": "subtitle",
        "body": "body",
        "dt": "date",
        "ftr": "footer",
        "sldNum": "slide-number",
        "pic": "picture",
        "chart": "chart",
        "tbl": "table",
        "media": "media",
        "obj": "object",
    }
    normalized = role or mapping.get(placeholder_type, "object")
    if normalized not in {
        "title",
        "subtitle",
        "body",
        "picture",
        "chart",
        "table",
        "object",
        "media",
        "date",
        "footer",
        "slide-number",
    }:
        raise MirrorMaterializationError(
            f"Unsupported placeholder semantic role: {normalized!r}"
        )
    return normalized


def _placeholder_match(
    candidate: dict[str, Any],
    target: dict[str, Any],
) -> bool:
    candidate_idx = _placeholder_idx(candidate.get("idx"))
    target_idx = _placeholder_idx(target.get("idx"))
    if candidate_idx == target_idx and _semantic_role(candidate) == _semantic_role(target):
        return True
    return (
        candidate_idx == target_idx
        and str(candidate.get("type") or "") == str(target.get("type") or "")
    )


def _placeholder_with_semantic_fallback(
    candidates: Iterable[dict[str, Any]],
    target: dict[str, Any],
) -> dict[str, Any] | None:
    candidate_list = list(candidates)
    exact = [item for item in candidate_list if _placeholder_match(item, target)]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise MirrorMaterializationError(
            f"Ambiguous placeholder identity for semantic role {_semantic_role(target)!r}"
        )
    semantic = [
        item
        for item in candidate_list
        if _semantic_role(item) == _semantic_role(target)
    ]
    return semantic[0] if len(semantic) == 1 else None


def _native_geometry(placeholder: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geometry = placeholder.get("geometry")
    if not isinstance(geometry, dict):
        return None
    try:
        values = tuple(float(geometry[name]) for name in ("x", "y", "width", "height"))
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(item) for item in values) or values[2] <= 0 or values[3] <= 0:
        return None
    return values


def _slot_plans(
    layout: dict[str, Any],
    layout_root: ET.Element,
    source_slides: list[dict[str, Any]],
    slide_roots: dict[int, ET.Element],
    master: dict[str, Any],
    master_root: ET.Element,
) -> list[SlotPlan]:
    plans: list[SlotPlan] = []
    placeholders = _require_list(
        layout.get("placeholders", []),
        context=f"layout {layout.get('key')} placeholders",
    )
    master_placeholders = _require_list(
        master.get("placeholders", []),
        context=f"master {master.get('key')} placeholders",
    )
    for raw in placeholders:
        if not isinstance(raw, dict):
            raise MirrorMaterializationError(
                f"Layout {layout.get('key')} placeholder must be an object"
            )
        shape_id = _require_string(
            raw.get("shapeId"),
            context=f"layout {layout.get('key')} placeholder shapeId",
        )
        bounds = _frame(_element_by_ref(layout_root, f"layout:{shape_id}"))
        if bounds is None:
            for slide in source_slides:
                matching = next(
                    (
                        item
                        for item in slide.get("placeholders", [])
                        if isinstance(item, dict) and _placeholder_match(item, raw)
                    ),
                    None,
                )
                if matching is None:
                    continue
                slide_element = _element_by_ref(
                    slide_roots[int(slide["index"])],
                    f"slide:{matching['shapeId']}",
                )
                bounds = _frame(slide_element) or _native_geometry(matching)
                if bounds is not None:
                    break
        if bounds is None:
            matching_master = _placeholder_with_semantic_fallback(
                (item for item in master_placeholders if isinstance(item, dict)),
                raw,
            )
            if matching_master is not None:
                master_element = _element_by_ref(
                    master_root,
                    f"master:{matching_master['shapeId']}",
                )
                bounds = _frame(master_element) or _native_geometry(matching_master)
            else:
                bounds = _frame(
                    _placeholder_guide_by_semantic(master_root, _semantic_role(raw))
                )
        bounds = bounds or _native_geometry(raw)
        if bounds is None:
            raise MirrorMaterializationError(
                f"Layout {layout.get('key')!r} placeholder {shape_id!r} has no "
                "positive deterministic bounds in Layout, Slide, Master, or native facts"
            )
        plans.append(SlotPlan(
            slot_id=f"slot-{_safe_prefix(str(layout['key']))}-{_safe_prefix(shape_id)}",
            semantic_role=_semantic_role(raw),
            placeholder_type=(str(raw.get("type")) if raw.get("type") is not None else None),
            idx=_placeholder_idx(raw.get("idx")),
            shape_id=shape_id,
            bounds=bounds,
        ))
    effective_indices = [plan.idx if plan.idx is not None else 0 for plan in plans]
    if len(effective_indices) != len(set(effective_indices)):
        raise MirrorMaterializationError(
            f"Layout {layout.get('key')!r} has duplicate effective placeholder idx values"
        )
    return plans


def _copy_text_carrier(source: ET.Element | None) -> ET.Element | None:
    if source is None:
        return None
    texts = [element for element in source.iter() if _local_name(element.tag) == "text"]
    if not texts:
        return None
    if len(texts) == 1:
        carrier = copy.deepcopy(texts[0])
    else:
        carrier = ET.Element(f"{{{SVG_NS}}}text", dict(texts[0].attrib))
        previous_y = _optional_float(texts[0].get("y"))
        first_output = True
        for text_index, text in enumerate(texts):
            text_y = _optional_float(text.get("y"))
            text_children = [
                child for child in text if _local_name(child.tag) == "tspan"
            ]
            if text_children:
                for child_index, child in enumerate(text_children):
                    tspan = copy.deepcopy(child)
                    tspan.attrib.pop("y", None)
                    if first_output:
                        tspan.attrib.pop("x", None)
                    elif child_index == 0 and text_y is not None and previous_y is not None:
                        tspan.set("x", text.get("x", texts[0].get("x", "0")))
                        tspan.set("dy", _format_number(text_y - previous_y))
                    if text_index > 0 and child_index == 0:
                        tspan.set("data-paragraph-soft-break", "0")
                    carrier.append(tspan)
                    first_output = False
            elif text.text:
                attrs: dict[str, str] = {}
                if not first_output and text_y is not None and previous_y is not None:
                    attrs["x"] = text.get("x", texts[0].get("x", "0"))
                    attrs["dy"] = _format_number(text_y - previous_y)
                if text_index > 0:
                    attrs["data-paragraph-soft-break"] = "0"
                tspan = ET.SubElement(carrier, f"{{{SVG_NS}}}tspan", attrs)
                tspan.text = text.text
                first_output = False
            if text_y is not None:
                previous_y = text_y
    carrier.attrib.pop("id", None)
    _normalize_mergeable_tspans(carrier)
    source_frame = _frame(source)
    if source_frame is not None:
        carrier.set(
            "data-pptx-frame",
            " ".join(_format_number(value) for value in source_frame),
        )
    carrier.set("data-pptx-placeholder-carrier", "true")
    return carrier


def _visible_placeholder_decoration(element: ET.Element) -> bool:
    """Return whether one non-text placeholder subtree paints any pixels."""
    if _hidden(element):
        return False
    tag = _local_name(element.tag)
    if tag in _NON_VISUAL_TAGS or tag == "text":
        return False
    if tag in {"g", "svg", "a"}:
        return any(_visible_placeholder_decoration(child) for child in element)
    if tag in {"image", "foreignObject", "use"}:
        return _visible_leaf(element)
    if tag in {"line", "polyline"}:
        stroke = _paint_value(element, "stroke")
        return stroke not in {None, "none", "transparent"}
    if tag in {"rect", "path", "polygon", "circle", "ellipse"}:
        fill = _paint_value(element, "fill")
        stroke = _paint_value(element, "stroke")
        filter_value = _paint_value(element, "filter")
        return (
            fill not in {"none", "transparent"}
            or stroke not in {None, "none", "transparent"}
            or filter_value not in {None, "none"}
        )
    return False


def _placeholder_decorations(source: ET.Element | None) -> list[ET.Element]:
    """Copy direct visual children that decorate one text placeholder."""
    if source is None:
        return []
    decorations = [
        copy.deepcopy(child)
        for child in source
        if _visible_placeholder_decoration(child)
    ]
    for decoration in decorations:
        _merge_group_inheritance(source, decoration)
    _copy_placeholder_native_attributes(source, decorations)
    return decorations


def _copy_placeholder_native_attributes(
    source: ET.Element,
    geometries: list[ET.Element],
) -> None:
    """Carry one logical placeholder geometry's native identity to its leaf."""
    if len(geometries) == 1:
        decoration = geometries[0]
        native_attributes = {
            "data-pptx-frame",
            "data-pptx-geometry-kind",
            "data-pptx-geometry-reason",
            "data-pptx-geometry-sha256",
            "data-pptx-geometry-status",
            "data-pptx-object",
            "data-pptx-prst",
        }
        for name, value in source.attrib.items():
            if name in native_attributes or name.startswith("data-pptx-av-"):
                if decoration.get(name) is None:
                    decoration.set(name, value)


def _placeholder_geometry(source: ET.Element | None) -> list[ET.Element]:
    """Copy direct source geometry even when it has no visible local paint."""
    if source is None:
        return []
    geometry_tags = {
        "circle",
        "ellipse",
        "line",
        "path",
        "polygon",
        "polyline",
        "rect",
    }
    geometries = [
        copy.deepcopy(child)
        for child in source
        if _local_name(child.tag) in geometry_tags and not _hidden(child)
    ]
    for geometry in geometries:
        _merge_group_inheritance(source, geometry)
    _copy_placeholder_native_attributes(source, geometries)
    return geometries


def _apply_placeholder_paint(source: ET.Element, target: ET.Element) -> None:
    """Apply inherited paint without replacing Slide-owned geometry."""
    paint_attributes = {
        "color",
        "fill",
        "fill-opacity",
        "fill-rule",
        "filter",
        "mix-blend-mode",
        "opacity",
        "paint-order",
        "shape-rendering",
        "stroke",
        "stroke-dasharray",
        "stroke-dashoffset",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-miterlimit",
        "stroke-opacity",
        "stroke-width",
        "vector-effect",
    }
    source_style = _parse_style(source.get("style"))
    target_style = _parse_style(target.get("style"))
    for name in paint_attributes:
        value = source.get(name)
        if value is None:
            value = source_style.get(name)
        if value is None:
            continue
        target.set(name, value)
        target_style.pop(name, None)
    if target_style:
        target.set("style", _style_text(target_style))
    else:
        target.attrib.pop("style", None)


def _resolved_placeholder_decorations(
    source: ET.Element | None,
    layout_guide: ET.Element | None,
    master_guide: ET.Element | None,
) -> list[ET.Element]:
    """Resolve text-placeholder decoration through Slide/Layout/Master."""
    local = _placeholder_decorations(source)
    if local:
        return local

    inherited: list[ET.Element] = []
    for candidate in (layout_guide, master_guide):
        inherited = _placeholder_decorations(candidate)
        if inherited:
            break
    if (
        source is None
        or source.get("data-pptx-placeholder-local-geometry") != "true"
        or len(inherited) != 1
    ):
        return inherited

    source_geometry = _placeholder_geometry(source)
    inherited_tag = _local_name(inherited[0].tag)
    if not source_geometry or inherited_tag not in {
        "circle",
        "ellipse",
        "line",
        "path",
        "polygon",
        "polyline",
        "rect",
    }:
        return inherited
    for geometry in source_geometry:
        _apply_placeholder_paint(inherited[0], geometry)
    return source_geometry


def _normalize_mergeable_tspans(text: ET.Element) -> None:
    """Mark the first line of a positional text block for paragraph merging."""
    tspans = [child for child in text if _local_name(child.tag) == "tspan"]
    if len(tspans) < 2 or not any(
        any(tspan.get(name) is not None for name in ("x", "y", "dy"))
        for tspan in tspans
    ):
        return
    first = tspans[0]
    if first.get("x") is None and text.get("x") is not None:
        first.set("x", text.get("x", ""))
    if first.get("y") is None and first.get("dy") is None:
        first.set("dy", "0")


def _blank_text_carrier(
    plan: SlotPlan,
    layout_guide: ET.Element | None,
    master_guide: ET.Element | None,
) -> ET.Element:
    carrier = _copy_text_carrier(layout_guide)
    if carrier is None:
        carrier = _copy_text_carrier(master_guide)
    if carrier is None:
        x, y, _width, height = plan.bounds
        carrier = ET.Element(
            f"{{{SVG_NS}}}text",
            {
                "x": _format_number(x),
                "y": _format_number(y + min(height, 24)),
                "font-size": "18",
                "fill": "#000000",
                "data-pptx-placeholder-carrier": "true",
            },
        )
    carrier.text = None
    for child in list(carrier):
        carrier.remove(child)
    if carrier.get("data-pptx-frame") is None:
        carrier.set(
            "data-pptx-frame",
            " ".join(_format_number(value) for value in plan.bounds),
        )
    carrier.set("data-pptx-placeholder-carrier", "true")
    return carrier


def _format_number(value: float) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".") or "0"


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _slot_wrapper(
    plan: SlotPlan,
    source: ET.Element | None,
    *,
    layout_guide: ET.Element | None,
    master_guide: ET.Element | None,
) -> tuple[ET.Element, list[ET.Element]]:
    wrapper = ET.Element(
        f"{{{SVG_NS}}}g",
        {
            "id": plan.slot_id,
            "data-pptx-placeholder": plan.semantic_role,
            "data-pptx-placeholder-bounds": " ".join(
                _format_number(item) for item in plan.bounds
            ),
        },
    )
    if plan.idx is not None:
        wrapper.set("data-pptx-placeholder-idx", str(plan.idx))

    extras: list[ET.Element] = []
    if plan.semantic_role in {
        "title",
        "subtitle",
        "body",
        "date",
        "footer",
        "slide-number",
    }:
        carrier = _copy_text_carrier(source)
        if carrier is None:
            carrier = _blank_text_carrier(plan, layout_guide, master_guide)
        extras = _resolved_placeholder_decorations(
            source,
            layout_guide,
            master_guide,
        )
        for extra in extras:
            extra.attrib.pop("data-pptx-placeholder-carrier", None)
        wrapper.append(carrier)
        return wrapper, extras

    if plan.semantic_role == "object":
        proxy_source = source
        if proxy_source is None:
            proxy_source = layout_guide
        if proxy_source is None:
            proxy_source = master_guide
        if proxy_source is None:
            raise MirrorMaterializationError(
                f"Object slot {plan.slot_id!r} has no visible proxy source"
            )
        visible = [copy.deepcopy(child) for child in proxy_source if _visible_leaf(child)]
        if not visible:
            raise MirrorMaterializationError(
                f"Object slot {plan.slot_id!r} has no visible proxy content"
            )
        wrapper.set("data-pptx-placeholder-binding", "proxy")
        for child in visible:
            wrapper.append(child)
        return wrapper, extras

    expected_tags = {
        "picture": {"image", "svg"},
        "media": {"image", "svg"},
        "chart": {"g"},
        "table": {"g"},
    }[plan.semantic_role]
    carrier_source = source or layout_guide
    candidates = [
        element
        for element in (carrier_source.iter() if carrier_source is not None else [])
        if _local_name(element.tag) in expected_tags and _visible_leaf(element)
    ]
    if len(candidates) != 1:
        raise MirrorMaterializationError(
            f"Slot {plan.slot_id!r} requires exactly one visible "
            f"{plan.semantic_role} carrier, found {len(candidates)}"
        )
    carrier = copy.deepcopy(candidates[0])
    if plan.semantic_role in {"chart", "table"}:
        marker = carrier.get("data-pptx-replace-with")
        if marker != plan.semantic_role:
            raise MirrorMaterializationError(
                f"Slot {plan.slot_id!r} {plan.semantic_role} carrier lacks native marker"
            )
    carrier.set("data-pptx-placeholder-carrier", "true")
    wrapper.append(carrier)
    return wrapper, extras


def _strip_source_refs(root: ET.Element) -> None:
    for element in root.iter():
        element.attrib.pop(SOURCE_REF_ATTRIBUTE, None)
        element.attrib.pop("data-ph-type", None)


def _is_full_canvas_rect(
    element: ET.Element,
    width: float,
    height: float,
) -> bool:
    if _local_name(element.tag) != "rect":
        return False
    try:
        values = tuple(
            float(element.get(name, default))
            for name, default in (
                ("x", "0"),
                ("y", "0"),
                ("width", "0"),
                ("height", "0"),
            )
        )
    except ValueError:
        return False
    fill = _paint_value(element, "fill")
    return (
        math.isclose(values[0], 0, abs_tol=0.01)
        and math.isclose(values[1], 0, abs_tol=0.01)
        and math.isclose(values[2], width, abs_tol=0.01)
        and math.isclose(values[3], height, abs_tol=0.01)
        and fill not in {None, "none", "transparent"}
    )


def _non_visual_nodes(roots: Iterable[ET.Element]) -> tuple[ET.Element | None, list[ET.Element]]:
    definitions: list[ET.Element] = []
    styles: list[ET.Element] = []
    for root in roots:
        for child in root:
            tag = _local_name(child.tag)
            if tag == "defs":
                definitions.extend(copy.deepcopy(list(child)))
            elif tag == "style":
                styles.append(copy.deepcopy(child))
    defs_node = ET.Element(f"{{{SVG_NS}}}defs") if definitions else None
    if defs_node is not None:
        for definition in definitions:
            defs_node.append(definition)
    return defs_node, styles


def _slide_placeholder_map(slide: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        f"slide:{item['shapeId']}": item
        for item in slide.get("placeholders", [])
        if isinstance(item, dict) and item.get("shapeId") is not None
    }


def _matching_slide_placeholder(
    slide: dict[str, Any],
    layout_placeholder: dict[str, Any],
) -> dict[str, Any] | None:
    matches = [
        item
        for item in slide.get("placeholders", [])
        if isinstance(item, dict) and _placeholder_match(item, layout_placeholder)
    ]
    if len(matches) > 1:
        raise MirrorMaterializationError(
            f"Slide {slide.get('index')} ambiguously matches Layout placeholder "
            f"{layout_placeholder.get('shapeId')}"
        )
    return matches[0] if matches else None


def _compose_template(
    *,
    native: dict[str, Any],
    master: dict[str, Any],
    layout: dict[str, Any],
    master_root: ET.Element,
    layout_root: ET.Element,
    slide: dict[str, Any] | None,
    slide_root: ET.Element | None,
    slot_plans: list[SlotPlan],
) -> ET.Element:
    width = float(native["slideSize"]["width_px"])
    height = float(native["slideSize"]["height_px"])
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "version": "1.1",
            "width": _format_number(width),
            "height": _format_number(height),
            "viewBox": f"0 0 {_format_number(width)} {_format_number(height)}",
            "data-pptx-master": str(master["key"]),
            "data-pptx-master-name": str(master["name"]),
            "data-pptx-layout": str(layout["key"]),
            "data-pptx-layout-name": str(layout["name"]),
            "data-pptx-show-master-shapes": str(
                _require_boolean(
                    layout.get("showMasterShapes"),
                    context=f"Layout {layout.get('key')!r} showMasterShapes",
                )
            ).lower(),
            "data-pptx-show-inherited-shapes": str(
                _require_boolean(
                    slide.get("showInheritedShapes"),
                    context=f"Slide {slide.get('index')} showInheritedShapes",
                )
                if slide
                else True
            ).lower(),
        },
    )

    roots = [master_root, layout_root]
    if slide_root is not None:
        roots.append(slide_root)
    defs, styles = _non_visual_nodes(roots)
    if defs is not None:
        root.append(defs)
    for style in styles:
        root.append(style)

    master_atoms = _fixed_atoms(master_root, scope="master", key=str(master["key"]))
    layout_atoms = _fixed_atoms(layout_root, scope="layout", key=str(layout["key"]))
    master_backgrounds = [
        atom for atom in master_atoms if _is_full_canvas_rect(atom, width, height)
    ]
    layout_backgrounds = [
        atom for atom in layout_atoms if _is_full_canvas_rect(atom, width, height)
    ]
    master_shapes = [atom for atom in master_atoms if atom not in master_backgrounds]
    layout_shapes = [atom for atom in layout_atoms if atom not in layout_backgrounds]

    slide_backgrounds: list[ET.Element] = []
    slide_content: list[ET.Element] = []
    source_placeholder_elements: dict[str, ET.Element] = {}
    if slide_root is not None and slide is not None:
        placeholder_refs = _slide_placeholder_map(slide)
        for index, child in enumerate(slide_root):
            if _local_name(child.tag) in _NON_VISUAL_TAGS:
                continue
            source_ref = child.get(SOURCE_REF_ATTRIBUTE)
            if source_ref in placeholder_refs:
                source_placeholder_elements[source_ref] = child
                continue
            item = copy.deepcopy(child)
            if _is_full_canvas_rect(item, width, height):
                item.set("id", item.get("id") or f"slide-{slide['index']}-background")
                item.set("data-pptx-layer", "slide")
                item.set("data-pptx-editable", "false")
                slide_backgrounds.append(item)
            else:
                item.set("id", item.get("id") or f"slide-{slide['index']}-node-{index + 1}")
                slide_content.append(item)
        if len(slide_backgrounds) > 1:
            raise MirrorMaterializationError(
                f"Slide {slide['index']} has more than one full-canvas solid background"
            )

    layout_placeholders = {
        str(item["shapeId"]): item
        for item in layout.get("placeholders", [])
        if isinstance(item, dict) and item.get("shapeId") is not None
    }
    master_placeholders = [
        item for item in master.get("placeholders", []) if isinstance(item, dict)
    ]
    slots: list[ET.Element] = []
    slot_extras: list[ET.Element] = []
    for plan in slot_plans:
        layout_placeholder = layout_placeholders[plan.shape_id]
        layout_guide = _element_by_ref(layout_root, f"layout:{plan.shape_id}")
        master_placeholder = _placeholder_with_semantic_fallback(
            master_placeholders,
            layout_placeholder,
        )
        master_guide = (
            _element_by_ref(master_root, f"master:{master_placeholder['shapeId']}")
            if master_placeholder is not None
            else _placeholder_guide_by_semantic(
                master_root,
                plan.semantic_role,
            )
        )
        source_element = None
        if slide is not None:
            slide_placeholder = _matching_slide_placeholder(slide, layout_placeholder)
            if slide_placeholder is not None:
                source_element = source_placeholder_elements.get(
                    f"slide:{slide_placeholder['shapeId']}"
                )
                if source_element is None:
                    raise MirrorMaterializationError(
                        f"Slide {slide['index']} placeholder {slide_placeholder['shapeId']} "
                        "is missing from its authoring SVG"
                    )
        wrapper, extras = _slot_wrapper(
            plan,
            source_element,
            layout_guide=layout_guide,
            master_guide=master_guide,
        )
        slots.append(wrapper)
        slot_extras.extend(extras)

    for element in (
        *master_backgrounds,
        *layout_backgrounds,
        *slide_backgrounds,
        *master_shapes,
        *layout_shapes,
        *slide_content,
        *slot_extras,
        *slots,
    ):
        _strip_source_refs(element)
        root.append(element)
    _strip_source_refs(root)
    return root


def _page_type(slide: dict[str, Any]) -> str:
    raw = str(slide.get("pageType") or "").strip().lower()
    mapping = {
        "cover_candidate": "cover",
        "toc_candidate": "toc",
        "chapter_candidate": "chapter",
        "content_candidate": "content",
        "ending_candidate": "ending",
    }
    return mapping.get(raw, "content")


def _serialize_svg(root: ET.Element) -> bytes:
    payload = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    return payload if payload.endswith(b"\n") else payload + b"\n"


def _refresh_preset_preview_hashes(root: ET.Element) -> None:
    """Rebind imported preset guards after deterministic SVG ID namespacing."""
    for element in root.iter():
        if (
            _local_name(element.tag) == "g"
            and element.get("data-pptx-object") in {"shape", "connector"}
            and element.get("data-pptx-prst") is not None
            and element.get("data-pptx-preview-sha256") is not None
        ):
            fingerprint = svg_preset_preview_fingerprint(element)
            element.set("data-pptx-preview-sha256", fingerprint)
            for descendant in element.iter():
                if descendant.get("data-pptx-preview-sha256") is not None:
                    descendant.set("data-pptx-preview-sha256", fingerprint)


def _sanitize_connector_references(root: ET.Element) -> int:
    """Drop endpoint bindings whose native target is absent from this SVG tree."""
    identities = {
        (
            element.get("data-pptx-shape-scope"),
            element.get("data-pptx-shape-id"),
        )
        for element in root.iter()
        if element.get("data-pptx-shape-scope")
        and element.get("data-pptx-shape-id")
    }
    detached: set[tuple[str, str, str]] = set()
    for element in root.iter():
        connector_scope = element.get("data-pptx-shape-scope") or "unknown"
        connector_id = element.get("data-pptx-shape-id") or element.get("id") or "unknown"
        for endpoint in ("start", "end"):
            target_id_attr = f"data-pptx-{endpoint}-shape-id"
            target_id = element.get(target_id_attr)
            if target_id is None:
                continue
            target_scope = element.get(
                f"data-pptx-{endpoint}-shape-scope",
                connector_scope,
            )
            if (target_scope, target_id) in identities:
                continue
            detached.add((connector_scope, connector_id, endpoint))
            for suffix in ("shape-id", "shape-scope", "site"):
                element.attrib.pop(f"data-pptx-{endpoint}-{suffix}", None)
    return len(detached)


def _local_asset_path(value: str, base_dir: Path) -> Path | None:
    if not value or value.startswith("#"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).resolve()
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = Path(unquote(parsed.path))
    return path.resolve() if path.is_absolute() else (base_dir / path).resolve()


def _detected_bitmap_extension(path: Path) -> str | None:
    header = path.read_bytes()[:32]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if header.startswith(b"BM"):
        return ".bmp"
    if header.startswith((b"II*\x00", b"MM\x00*")):
        return ".tiff"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    return None


def _rewrite_packaged_assets(
    root: ET.Element,
    *,
    source_base: Path,
    final_svg_path: Path,
    template_workspace: Path,
    asset_sources: dict[Path, Path],
) -> None:
    for element in root.iter():
        for attribute in ("href", f"{{{XLINK_NS}}}href"):
            value = element.get(attribute)
            if value is None:
                continue
            source = _local_asset_path(value, source_base)
            if source is None:
                continue
            if not source.is_file():
                raise MirrorMaterializationError(
                    f"Referenced local asset is missing: {source}"
                )
            detected_extension = _detected_bitmap_extension(source)
            if detected_extension is not None:
                source_suffix = source.suffix.lower()
                equivalent_suffixes = (
                    {".jpg", ".jpeg"}
                    if detected_extension == ".jpg"
                    else {detected_extension}
                )
                packaged_name = (
                    source.name
                    if source_suffix in equivalent_suffixes
                    else f"{source.stem}{detected_extension}"
                )
                relative_target = Path("images") / packaged_name
            elif source.suffix.lower() in _BITMAP_EXTENSIONS:
                relative_target = Path("images") / source.name
            else:
                relative_target = Path("templates") / "assets" / source.name
            previous = asset_sources.get(relative_target)
            if previous is not None and _sha256_file(previous) != _sha256_file(source):
                raise MirrorMaterializationError(
                    f"Asset basename collision with different content: {source.name}"
                )
            asset_sources[relative_target] = source
            target = template_workspace / relative_target
            relative_href = os.path.relpath(target, final_svg_path.parent).replace(os.sep, "/")
            parsed = urlsplit(value)
            element.set(
                attribute,
                urlunsplit(("", "", relative_href, parsed.query, parsed.fragment)),
            )


def _materialize_icon(
    record: VectorAssetRecord,
    document: AuthoringDocument,
) -> tuple[ET.Element, RestorationStats]:
    actual_sha256 = _sha256_file(record.asset_path)
    if actual_sha256 != record.expected_sha256:
        raise MirrorMaterializationError(
            f"Vector asset {record.icon!r} changed during materialization; "
            f"expected {record.expected_sha256}, found {actual_sha256}"
        )
    root = _parse_svg(record.asset_path)
    _absolutize_local_hrefs(root, record.asset_path.parent)
    stats = _rehydrate_tree(root, document, excluded_refs=set())
    _strip_source_refs(root)
    return root, stats


def _ensure_no_source_refs(path: Path) -> None:
    root = _parse_svg(path)
    refs = sorted(_source_ref_counts(root))
    if refs:
        raise MirrorMaterializationError(
            f"Materialized file still contains source refs: {path}: {refs[:5]}"
        )


def _preflight_output(
    import_workspace: Path,
    template_workspace: Path,
    relative_files: Iterable[Path],
) -> None:
    import_resolved = import_workspace.resolve()
    output_resolved = template_workspace.resolve()
    try:
        output_resolved.relative_to(import_resolved)
    except ValueError:
        pass
    else:
        raise MirrorMaterializationError(
            "Template workspace must not be inside the import workspace"
        )
    try:
        import_resolved.relative_to(output_resolved)
    except ValueError:
        pass
    else:
        raise MirrorMaterializationError(
            "Import workspace must not be inside the template workspace"
        )

    templates_root = template_workspace / "templates"
    if templates_root.exists():
        if not templates_root.is_dir():
            raise MirrorMaterializationError(
                f"Template output is not a directory: {templates_root}"
            )
        existing = sorted(path for path in templates_root.iterdir())
        if existing:
            raise MirrorMaterializationError(
                f"Template output must be empty before mirror materialization: "
                f"{templates_root}; first entry: {existing[0].name}"
            )
    collisions = [
        template_workspace / relative
        for relative in relative_files
        if os.path.lexists(template_workspace / relative)
    ]
    if collisions:
        raise MirrorMaterializationError(
            f"Output file already exists: {collisions[0]}"
        )


def _nearest_existing_directory(path: Path) -> Path:
    candidate = path
    while not candidate.exists():
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    if not candidate.is_dir():
        raise MirrorMaterializationError(f"Output parent is not a directory: {candidate}")
    return candidate


def _ensure_directory(path: Path, created: list[Path]) -> None:
    missing: list[Path] = []
    candidate = path
    while not candidate.exists():
        if os.path.lexists(candidate):
            raise MirrorMaterializationError(
                f"Output parent is not a directory: {candidate}"
            )
        missing.append(candidate)
        candidate = candidate.parent
    if not candidate.is_dir():
        raise MirrorMaterializationError(f"Output parent is not a directory: {candidate}")
    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)


def _publish_files(
    template_workspace: Path,
    staged_root: Path,
    relative_files: list[Path],
) -> None:
    created_dirs: list[Path] = []
    published: list[Path] = []
    try:
        for relative in relative_files:
            target = template_workspace / relative
            _ensure_directory(target.parent, created_dirs)
        staging_device = staged_root.stat().st_dev
        for relative in relative_files:
            target = template_workspace / relative
            if target.parent.stat().st_dev != staging_device:
                raise MirrorMaterializationError(
                    f"Cannot atomically publish across filesystems: {target}"
                )
            if os.path.lexists(target):
                raise MirrorMaterializationError(
                    f"Output appeared while mirror files were staged: {target}"
                )
        for relative in relative_files:
            target = template_workspace / relative
            (staged_root / relative).replace(target)
            published.append(target)
    except (OSError, MirrorMaterializationError) as exc:
        rollback_errors: list[str] = []
        for path in reversed(published):
            try:
                path.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"could not remove {path}: {rollback_exc}")
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        if rollback_errors:
            raise MirrorMaterializationError(
                f"Mirror publish failed ({exc}); rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        raise MirrorMaterializationError(f"Mirror publish failed: {exc}") from exc


def materialize_mirror_template(
    import_workspace: Path,
    template_workspace: Path,
) -> dict[str, Any]:
    """Validate one Type A import graph and publish its mirror SVG contract."""
    authoring_root, documents = _load_authoring_documents(import_workspace)
    vector_assets = _load_vector_assets(import_workspace, documents)
    referenced_icons = _validate_source_ref_closure(documents, vector_assets)
    native = _load_native_graph(import_workspace)
    inheritance = _load_inheritance(import_workspace)
    _validate_graph_roster(native, inheritance, documents)

    masters = {item["key"]: item for item in native["masters"]}
    layouts = {item["key"]: item for item in native["layouts"]}
    slides = sorted(native["slides"], key=lambda item: int(item["index"]))
    if [int(item["index"]) for item in slides] != list(range(1, len(slides) + 1)):
        raise MirrorMaterializationError(
            "Mirror source slide indexes must be contiguous and start at 1"
        )

    prepared_masters: dict[str, ET.Element] = {}
    prepared_layouts: dict[str, ET.Element] = {}
    prepared_slides: dict[int, ET.Element] = {}
    total_stats = RestorationStats()
    for key, master in masters.items():
        document = documents[master["svgFile"]]
        root, stats = _prepared_document(
            document,
            excluded_refs=set(document.source_refs),
        )
        _namespace_ids(root, f"m-{_safe_prefix(str(key))}-")
        prepared_masters[key] = root
        total_stats.merge(stats)
    for key, layout in layouts.items():
        document = documents[layout["svgFile"]]
        root, stats = _prepared_document(
            document,
            excluded_refs=set(document.source_refs),
        )
        _namespace_ids(root, f"l-{_safe_prefix(str(key))}-")
        prepared_layouts[key] = root
        total_stats.merge(stats)
    for slide in slides:
        index = int(slide["index"])
        document = documents[slide["layeredSvgFile"]]
        placeholder_refs = {
            f"slide:{item['shapeId']}"
            for item in slide.get("placeholders", [])
            if isinstance(item, dict) and item.get("shapeId") is not None
        }
        root, stats = _prepared_document(document, excluded_refs=placeholder_refs)
        _namespace_ids(root, f"s-{index:03d}-")
        prepared_slides[index] = root
        total_stats.merge(stats)

    slides_by_layout: dict[str, list[dict[str, Any]]] = {key: [] for key in layouts}
    for slide in slides:
        slides_by_layout[str(slide["layoutKey"])].append(slide)

    plans_by_layout: dict[str, list[SlotPlan]] = {}
    for key, layout in layouts.items():
        master_key = str(layout["masterKey"])
        plans_by_layout[key] = _slot_plans(
            layout,
            prepared_layouts[key],
            slides_by_layout[key],
            prepared_slides,
            masters[master_key],
            prepared_masters[master_key],
        )

    materialized_roots: list[tuple[Path, ET.Element]] = []
    for slide in slides:
        index = int(slide["index"])
        layout = layouts[str(slide["layoutKey"])]
        master = masters[str(slide["masterKey"])]
        filename = Path("templates") / f"{index:03d}_{_page_type(slide)}.svg"
        root = _compose_template(
            native=native,
            master=master,
            layout=layout,
            master_root=prepared_masters[str(master["key"])],
            layout_root=prepared_layouts[str(layout["key"])],
            slide=slide,
            slide_root=prepared_slides[index],
            slot_plans=plans_by_layout[str(layout["key"])],
        )
        materialized_roots.append((filename, root))

    unused_layouts = [
        layout for key, layout in layouts.items() if not slides_by_layout[key]
    ]
    for layout in sorted(unused_layouts, key=lambda item: str(item["key"])):
        master = masters[str(layout["masterKey"])]
        filename = Path("templates") / f"layout_{layout['key']}.svg"
        root = _compose_template(
            native=native,
            master=master,
            layout=layout,
            master_root=prepared_masters[str(master["key"])],
            layout_root=prepared_layouts[str(layout["key"])],
            slide=None,
            slide_root=None,
            slot_plans=plans_by_layout[str(layout["key"])],
        )
        materialized_roots.append((filename, root))

    asset_sources: dict[Path, Path] = {}
    files: list[MaterializedFile] = []
    for relative_path, root in materialized_roots:
        final_path = template_workspace / relative_path
        _rewrite_packaged_assets(
            root,
            source_base=authoring_root,
            final_svg_path=final_path,
            template_workspace=template_workspace,
            asset_sources=asset_sources,
        )
        total_stats.detached_connector_endpoints += _sanitize_connector_references(root)
        _refresh_preset_preview_hashes(root)
        files.append(MaterializedFile(relative_path, _serialize_svg(root)))

    for icon in sorted(referenced_icons):
        record = vector_assets[icon]
        icon_root, stats = _materialize_icon(
            record,
            documents[record.origin_document],
        )
        total_stats.merge(stats)
        relative_path = Path("icons") / f"{icon}.svg"
        final_path = template_workspace / relative_path
        _rewrite_packaged_assets(
            icon_root,
            source_base=record.asset_path.parent,
            final_svg_path=final_path,
            template_workspace=template_workspace,
            asset_sources=asset_sources,
        )
        total_stats.detached_connector_endpoints += _sanitize_connector_references(
            icon_root
        )
        _refresh_preset_preview_hashes(icon_root)
        files.append(MaterializedFile(relative_path, _serialize_svg(icon_root)))

    for relative_target, source in sorted(asset_sources.items()):
        files.append(MaterializedFile(relative_target, source.read_bytes()))
    relative_files = [item.relative_path for item in files]
    if len(relative_files) != len(set(relative_files)):
        raise MirrorMaterializationError("Materializer produced duplicate output paths")
    _preflight_output(import_workspace, template_workspace, relative_files)

    staging_parent = _nearest_existing_directory(template_workspace.parent)
    with tempfile.TemporaryDirectory(
        prefix=".mirror-template-materialize-",
        dir=staging_parent,
    ) as temporary:
        staged_root = Path(temporary) / "staged"
        for item in files:
            target = staged_root / item.relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.payload)

        template_paths = sorted(
            staged_root / relative
            for relative, _root in materialized_roots
        )
        try:
            parse_template_slides(template_paths)
        except TemplateStructureError as exc:
            raise MirrorMaterializationError(
                f"Materialized structured SVG contract is invalid: {exc}"
            ) from exc
        for relative in relative_files:
            if relative.suffix.lower() == ".svg":
                _ensure_no_source_refs(staged_root / relative)
        _publish_files(
            template_workspace,
            staged_root,
            sorted(relative_files, key=lambda item: item.as_posix()),
        )

    return {
        "schema": "ppt-master.mirror-materialization-report.v1",
        "import_workspace": str(import_workspace),
        "template_workspace": str(template_workspace),
        "source_slide_indexes": [int(item["index"]) for item in slides],
        "source_slide_count": len(slides),
        "master_count": len(masters),
        "layout_count": len(layouts),
        "unused_layout_count": len(unused_layouts),
        "template_svg_count": len(materialized_roots),
        "imported_vector_count": len(referenced_icons),
        "packaged_asset_count": len(asset_sources),
        "restoration": total_stats.as_dict(),
        "files": [
            item.relative_path.as_posix()
            for item in sorted(files, key=lambda item: item.relative_path.as_posix())
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize a deterministic mirror template from one PPTX import "
            "workspace's layered authoring IR."
        )
    )
    parser.add_argument(
        "import_workspace",
        type=Path,
        help="Type A PPTX import workspace containing authoring-svg/ and native facts",
    )
    parser.add_argument(
        "template_workspace",
        type=Path,
        help="Empty template workspace destination (templates/ must be absent or empty)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    import_workspace = args.import_workspace.resolve()
    template_workspace = args.template_workspace.resolve()
    if not import_workspace.is_dir():
        print(f"Error: import workspace does not exist: {import_workspace}", file=sys.stderr)
        return 1
    try:
        report = materialize_mirror_template(import_workspace, template_workspace)
    except (MirrorMaterializationError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
