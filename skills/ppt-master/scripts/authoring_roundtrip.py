#!/usr/bin/env python3
"""
PPT Master - Flat Authoring Round-trip Materializer

Materialize editable ``authoring-svg-flat/`` pages back into layered slide SVG
inputs for the existing source-preserving SVG-to-PPTX exporter. Unchanged
source objects recover their original round-trip metadata; edited objects stay
as authored SVG and are converted normally.

Usage:
    Imported by svg_to_pptx.py for ``--roundtrip``.

Dependencies:
    None (standard library and sibling PPT Master modules only).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from extract_svg_assets import extract_file
from pptx_workspace import ROUNDTRIP_MANIFEST_PATH
from slide_roster import discover_slide_svgs
from svg_authoring_view import (
    AUTHORING_OMITTED_SOURCE_ATTRIBUTES,
    AUTHORING_MANIFEST_NAME,
    AUTHORING_SCHEMA,
    SOURCE_REF_ATTRIBUTE,
    SOURCE_PROXY_ATTRIBUTE,
    SOURCE_PROXY_KIND,
    project_svg_batch,
    semantic_subtree_sha256,
)
from svg_compatibility import normalize_single_child_group_filters


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
VECTOR_INVENTORY_SCHEMA = "vector_asset_inventory.v1"
IMPORTED_ICON_NAMESPACE = "imported"
_URL_ID_RE = re.compile(r"url\(\s*(['\"]?)#([^)'\"\s]+)\1\s*\)")
_PRESERVED_EFFECT_ATTRIBUTES = frozenset({
    "data-pptx-effect-ooxml",
    "data-pptx-effect-ooxml-sha256",
    "data-pptx-effect-reason",
    "data-pptx-effect-status",
})

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


class AuthoringRoundtripError(RuntimeError):
    """Reject stale, ambiguous, or incomplete authoring round-trip input."""


@dataclass(frozen=True)
class SourceRefRecord:
    source_path: tuple[int, ...]
    initial_authoring_subtree_sha256: str
    representation: str
    proxy_asset: Path | None = None
    proxy_asset_sha256: str | None = None


@dataclass(frozen=True)
class AuthoringDocument:
    name: str
    authoring_path: Path
    flat_source_path: Path
    layered_source_path: Path
    initial_authoring_sha256: str
    source_refs: dict[str, SourceRefRecord]


@dataclass(frozen=True)
class VectorAssetRecord:
    icon: str
    asset_path: Path
    origin_document: str
    source_sha256: str
    expected_asset_sha256: str
    actual_asset_sha256: str

    @property
    def element_prefix(self) -> str:
        return self.icon.rsplit("/", 1)[-1]

    @property
    def baseline_key(self) -> str:
        stem = self.element_prefix
        match = re.search(r"(slide_\d+_ill\d+)$", stem)
        slot = match.group(1) if match else self.source_sha256
        return f"{self.origin_document}:{slot}"

    @property
    def unchanged(self) -> bool:
        return self.actual_asset_sha256 == self.expected_asset_sha256


@dataclass(frozen=True)
class RefOccurrence:
    element: ET.Element
    asset: VectorAssetRecord | None


@dataclass(frozen=True)
class AuthoringRoundtripResult:
    svg_files: tuple[Path, ...]
    report: dict[str, Any]


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


def _parse_svg(path: Path) -> ET.Element:
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True),
    )
    try:
        return ET.fromstring(path.read_bytes(), parser=parser)
    except (OSError, ET.ParseError) as exc:
        raise AuthoringRoundtripError(f"Cannot parse SVG {path}: {exc}") from exc


def _load_json(path: Path, *, context: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuthoringRoundtripError(f"Missing {context}: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuthoringRoundtripError(f"Cannot read {context} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuthoringRoundtripError(f"{context} must be a JSON object: {path}")
    return payload


def _resolve_inside(root: Path, value: str, *, context: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise AuthoringRoundtripError(
            f"{context} resolves outside {root}: {value!r}"
        ) from exc
    return path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_element(root: ET.Element, path: tuple[int, ...]) -> ET.Element:
    element = root
    try:
        for index in path:
            element = list(element)[index]
    except (IndexError, TypeError) as exc:
        raise AuthoringRoundtripError(
            f"Source-ref path no longer resolves: {list(path)}"
        ) from exc
    return element


def _source_identity(element: ET.Element) -> str | None:
    scope = element.get("data-pptx-shape-scope")
    shape_id = element.get("data-pptx-shape-id")
    if not scope or not shape_id:
        return None
    return f"{scope}:{shape_id}"


def is_flat_authoring_bundle(authoring_dir: Path) -> bool:
    """Return whether a directory declares the supported flat authoring IR."""
    manifest_path = authoring_dir / AUTHORING_MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(manifest, dict)
        and manifest.get("schema") == AUTHORING_SCHEMA
        and manifest.get("projection_kind") == "flat"
        and manifest.get("authoring_root") == "."
        and manifest.get("source_ref_attribute") == SOURCE_REF_ATTRIBUTE
    )


def _load_documents(
    project_path: Path,
    authoring_dir: Path,
) -> tuple[Path, Path, dict[str, AuthoringDocument], dict[str, Any]]:
    manifest_path = authoring_dir / AUTHORING_MANIFEST_NAME
    manifest = _load_json(manifest_path, context="flat authoring manifest")
    if manifest.get("schema") != AUTHORING_SCHEMA:
        raise AuthoringRoundtripError(
            f"Unsupported authoring manifest schema: {manifest.get('schema')!r}"
        )
    if manifest.get("projection_kind") != "flat":
        raise AuthoringRoundtripError(
            "Authoring round-trip requires projection_kind='flat'"
        )
    if manifest.get("authoring_root") != ".":
        raise AuthoringRoundtripError(
            "authoring_manifest.json authoring_root must be '.'"
        )
    if manifest.get("source_ref_attribute") != SOURCE_REF_ATTRIBUTE:
        raise AuthoringRoundtripError(
            "authoring_manifest.json uses an unsupported source-ref attribute"
        )
    source_root_raw = manifest.get("source_root")
    if not isinstance(source_root_raw, str) or not source_root_raw.strip():
        raise AuthoringRoundtripError(
            "authoring_manifest.json source_root must be a non-empty string"
        )
    source_root = (authoring_dir / source_root_raw).resolve()
    try:
        source_root.relative_to(project_path)
    except ValueError as exc:
        raise AuthoringRoundtripError(
            "Flat authoring source_root must stay inside the import workspace"
        ) from exc
    if not source_root.is_dir():
        raise AuthoringRoundtripError(
            f"Flat authoring backing SVG directory is missing: {source_root}"
        )

    roundtrip_manifest = _load_json(
        project_path / ROUNDTRIP_MANIFEST_PATH,
        context="round-trip workspace manifest",
    )
    if roundtrip_manifest.get("schema") != "ppt-master.roundtrip-workspace.v1":
        raise AuthoringRoundtripError(
            "Unsupported round-trip workspace manifest schema: "
            f"{roundtrip_manifest.get('schema')!r}"
        )
    directories = roundtrip_manifest.get("directories")
    if not isinstance(directories, dict):
        raise AuthoringRoundtripError(
            "Round-trip workspace manifest directories must be an object"
        )
    flat_root_raw = directories.get("flatSvg")
    layered_root_raw = directories.get("layeredSvg")
    proxy_root_raw = directories.get("sourceObjectPreviews")
    if not isinstance(flat_root_raw, str) or not flat_root_raw:
        raise AuthoringRoundtripError(
            "Round-trip workspace manifest has no flat SVG backing directory"
        )
    if not isinstance(layered_root_raw, str) or not layered_root_raw:
        raise AuthoringRoundtripError(
            "Round-trip workspace manifest has no layered SVG backing directory"
        )
    if not isinstance(proxy_root_raw, str) or not proxy_root_raw:
        raise AuthoringRoundtripError(
            "Round-trip workspace manifest has no source-object preview directory"
        )
    flat_root = _resolve_inside(
        project_path,
        flat_root_raw,
        context="round-trip flat SVG backing directory",
    )
    layered_root = _resolve_inside(
        project_path,
        layered_root_raw,
        context="round-trip layered SVG backing directory",
    )
    proxy_root = _resolve_inside(
        project_path,
        proxy_root_raw,
        context="round-trip source-object preview directory",
    )
    if source_root != flat_root:
        raise AuthoringRoundtripError(
            "Authoring manifest source_root does not match the round-trip flat "
            "SVG backing directory"
        )
    if not layered_root.is_dir():
        raise AuthoringRoundtripError(
            f"Round-trip layered SVG backing directory is missing: {layered_root}"
        )

    documents_raw = manifest.get("documents")
    if not isinstance(documents_raw, list):
        raise AuthoringRoundtripError(
            "authoring_manifest.json documents must be an array"
        )
    documents: dict[str, AuthoringDocument] = {}
    for index, raw in enumerate(documents_raw):
        if not isinstance(raw, dict):
            raise AuthoringRoundtripError(f"documents[{index}] must be an object")
        authoring_name = raw.get("authoring")
        source_name = raw.get("source")
        if not isinstance(authoring_name, str) or not authoring_name:
            raise AuthoringRoundtripError(
                f"documents[{index}].authoring must be a non-empty string"
            )
        if not isinstance(source_name, str) or not source_name:
            raise AuthoringRoundtripError(
                f"documents[{index}].source must be a non-empty string"
            )
        if authoring_name in documents:
            raise AuthoringRoundtripError(
                f"Duplicate authoring manifest document: {authoring_name}"
            )
        authoring_path = _resolve_inside(
            authoring_dir,
            authoring_name,
            context=f"documents[{index}].authoring",
        )
        flat_source_path = _resolve_inside(
            source_root,
            source_name,
            context=f"documents[{index}].source",
        )
        layered_source_path = _resolve_inside(
            layered_root,
            source_name,
            context=f"documents[{index}] layered source",
        )
        for label, path in (
            ("authoring SVG", authoring_path),
            ("flat backing SVG", flat_source_path),
            ("layered backing SVG", layered_source_path),
        ):
            if not path.is_file() or path.suffix.lower() != ".svg":
                raise AuthoringRoundtripError(f"Missing {label}: {path}")
        expected_source_sha = raw.get("source_sha256")
        if not isinstance(expected_source_sha, str) or not expected_source_sha:
            raise AuthoringRoundtripError(
                f"documents[{index}].source_sha256 must be a non-empty string"
            )
        actual_source_sha = _sha256_file(flat_source_path)
        if actual_source_sha != expected_source_sha:
            raise AuthoringRoundtripError(
                f"Flat backing SVG changed: {flat_source_path.name}; expected "
                f"{expected_source_sha}, found {actual_source_sha}"
            )
        initial_authoring_sha = raw.get("initial_authoring_sha256")
        if not isinstance(initial_authoring_sha, str) or not initial_authoring_sha:
            raise AuthoringRoundtripError(
                f"documents[{index}].initial_authoring_sha256 must be a non-empty string"
            )

        refs_raw = raw.get("source_refs")
        if not isinstance(refs_raw, dict):
            raise AuthoringRoundtripError(
                f"documents[{index}].source_refs must be an object"
            )
        flat_root = _parse_svg(flat_source_path)
        refs: dict[str, SourceRefRecord] = {}
        for source_ref, ref_raw in refs_raw.items():
            if not isinstance(source_ref, str) or not isinstance(ref_raw, dict):
                raise AuthoringRoundtripError(
                    f"Invalid source-ref record in {authoring_name}"
                )
            source_path_raw = ref_raw.get("source_path")
            if not (
                isinstance(source_path_raw, list)
                and all(
                    isinstance(item, int) and not isinstance(item, bool) and item >= 0
                    for item in source_path_raw
                )
            ):
                raise AuthoringRoundtripError(
                    f"{authoring_name} source ref {source_ref!r} has invalid source_path"
                )
            initial_hash = ref_raw.get("initial_authoring_subtree_sha256")
            if not isinstance(initial_hash, str) or not initial_hash:
                raise AuthoringRoundtripError(
                    f"{authoring_name} source ref {source_ref!r} has no initial hash"
                )
            representation = ref_raw.get("representation")
            if representation not in {"inline", "source-proxy"}:
                raise AuthoringRoundtripError(
                    f"{authoring_name} source ref {source_ref!r} has an "
                    "unsupported representation"
                )
            proxy_asset: Path | None = None
            proxy_asset_sha256: str | None = None
            if representation == "source-proxy":
                proxy_asset_raw = ref_raw.get("proxy_asset")
                proxy_asset_sha256_raw = ref_raw.get("proxy_asset_sha256")
                if (
                    not isinstance(proxy_asset_raw, str)
                    or not proxy_asset_raw
                    or not isinstance(proxy_asset_sha256_raw, str)
                    or re.fullmatch(r"[0-9a-f]{64}", proxy_asset_sha256_raw) is None
                ):
                    raise AuthoringRoundtripError(
                        f"{authoring_name} source proxy {source_ref!r} has "
                        "incomplete asset metadata"
                    )
                proxy_asset = (authoring_dir / proxy_asset_raw).resolve()
                try:
                    proxy_asset.relative_to(proxy_root)
                except ValueError as exc:
                    proxy_root_name = proxy_root.relative_to(project_path).as_posix()
                    raise AuthoringRoundtripError(
                        f"{authoring_name} source proxy {source_ref!r} must use "
                        f"{proxy_root_name}/"
                    ) from exc
                if (
                    not proxy_asset.is_file()
                    or proxy_asset.suffix.lower() != ".svg"
                    or _sha256_file(proxy_asset) != proxy_asset_sha256_raw
                ):
                    raise AuthoringRoundtripError(
                        f"{authoring_name} source proxy asset is missing or changed: "
                        f"{proxy_asset}"
                    )
                proxy_asset_sha256 = proxy_asset_sha256_raw
            source_path_tuple = tuple(source_path_raw)
            source_element = _source_element(flat_root, source_path_tuple)
            if _source_identity(source_element) != source_ref:
                raise AuthoringRoundtripError(
                    f"{authoring_name} source ref {source_ref!r} resolves to "
                    f"{_source_identity(source_element)!r}"
                )
            refs[source_ref] = SourceRefRecord(
                source_path=source_path_tuple,
                initial_authoring_subtree_sha256=initial_hash,
                representation=representation,
                proxy_asset=proxy_asset,
                proxy_asset_sha256=proxy_asset_sha256,
            )
        documents[authoring_name] = AuthoringDocument(
            name=authoring_name,
            authoring_path=authoring_path,
            flat_source_path=flat_source_path,
            layered_source_path=layered_source_path,
            initial_authoring_sha256=initial_authoring_sha,
            source_refs=refs,
        )

    actual_files = {
        path.relative_to(authoring_dir).as_posix()
        for path in authoring_dir.rglob("*.svg")
        if path.is_file()
    }
    if actual_files != set(documents):
        raise AuthoringRoundtripError(
            "Authoring manifest/file roster differs; missing="
            f"{sorted(set(documents) - actual_files)}, "
            f"extra={sorted(actual_files - set(documents))}"
        )
    if manifest.get("file_count") != len(documents):
        raise AuthoringRoundtripError(
            "authoring_manifest.json file_count does not match documents"
        )
    expected_ref_count = sum(len(item.source_refs) for item in documents.values())
    if manifest.get("source_ref_count") != expected_ref_count:
        raise AuthoringRoundtripError(
            "authoring_manifest.json source_ref_count does not match documents"
        )
    return source_root, proxy_root, documents, manifest


def _load_current_assets(
    project_path: Path,
    authoring_dir: Path,
    documents: dict[str, AuthoringDocument],
) -> tuple[dict[str, VectorAssetRecord], dict[str, Any] | None]:
    inventory_path = project_path / f"{authoring_dir.name}_vector_asset_inventory.json"
    if not inventory_path.is_file():
        return {}, None
    inventory = _load_json(inventory_path, context="flat vector asset inventory")
    if inventory.get("schema") != VECTOR_INVENTORY_SCHEMA:
        raise AuthoringRoundtripError(
            f"Unsupported vector inventory schema: {inventory.get('schema')!r}"
        )
    if inventory.get("icon_namespace") != IMPORTED_ICON_NAMESPACE:
        raise AuthoringRoundtripError(
            "Flat authoring vector inventory must use icon_namespace='imported'"
        )
    assets_raw = inventory.get("assets")
    if not isinstance(assets_raw, list):
        raise AuthoringRoundtripError("Vector inventory assets must be an array")
    icons_root = project_path / "icons"
    records: dict[str, VectorAssetRecord] = {}
    for index, raw in enumerate(assets_raw):
        if not isinstance(raw, dict):
            raise AuthoringRoundtripError(f"vector assets[{index}] must be an object")
        values = {
            name: raw.get(name)
            for name in (
                "icon",
                "asset",
                "svg",
                "source_sha256",
                "asset_sha256",
            )
        }
        if not all(isinstance(value, str) and value for value in values.values()):
            raise AuthoringRoundtripError(
                f"vector assets[{index}] is missing a required string field"
            )
        icon = str(values["icon"])
        origin = str(values["svg"])
        if icon in records:
            raise AuthoringRoundtripError(f"Duplicate vector asset id: {icon}")
        if origin not in documents:
            raise AuthoringRoundtripError(
                f"Vector asset {icon!r} names unknown document {origin!r}"
            )
        asset_path = _resolve_inside(
            icons_root,
            str(values["asset"]),
            context=f"vector asset {icon!r}",
        )
        if not asset_path.is_file() or asset_path.suffix.lower() != ".svg":
            raise AuthoringRoundtripError(f"Vector asset is missing: {asset_path}")
        records[icon] = VectorAssetRecord(
            icon=icon,
            asset_path=asset_path,
            origin_document=origin,
            source_sha256=str(values["source_sha256"]),
            expected_asset_sha256=str(values["asset_sha256"]),
            actual_asset_sha256=_sha256_file(asset_path),
        )
    if inventory.get("asset_count") != len(records):
        raise AuthoringRoundtripError("Vector inventory asset_count is stale")
    return records, inventory


def _baseline_assets(
    entries: list[dict[str, Any]],
    icons_root: Path,
) -> dict[str, VectorAssetRecord]:
    records: dict[str, VectorAssetRecord] = {}
    for index, raw in enumerate(entries):
        values = {
            name: raw.get(name)
            for name in (
                "icon",
                "asset",
                "svg",
                "source_sha256",
                "asset_sha256",
            )
        }
        if not all(isinstance(value, str) and value for value in values.values()):
            raise AuthoringRoundtripError(
                f"Generated baseline vector asset {index} is incomplete"
            )
        icon = str(values["icon"])
        asset_path = icons_root / str(values["asset"])
        actual_sha = _sha256_file(asset_path)
        records[icon] = VectorAssetRecord(
            icon=icon,
            asset_path=asset_path,
            origin_document=str(values["svg"]),
            source_sha256=str(values["source_sha256"]),
            expected_asset_sha256=actual_sha,
            actual_asset_sha256=actual_sha,
        )
    return records


def _generate_baseline_bundle(
    project_path: Path,
    source_root: Path,
    source_proxy_dir: Path,
    documents: dict[str, AuthoringDocument],
    inventory: dict[str, Any] | None,
) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, VectorAssetRecord]]:
    temporary = tempfile.TemporaryDirectory(
        prefix=".authoring-baseline-",
        dir=project_path,
    )
    baseline_root = Path(temporary.name)
    mapping = [
        (document.flat_source_path, baseline_root / document.name)
        for document in sorted(documents.values(), key=lambda item: item.name)
    ]
    try:
        project_svg_batch(
            mapping,
            source_root,
            baseline_root,
            force=False,
            projection_kind="flat",
            source_proxy_dir=source_proxy_dir,
            publish_source_proxies=False,
        )
        if inventory is None:
            return temporary, baseline_root, {}
        min_drawables = inventory.get("min_drawables")
        min_bytes = inventory.get("min_bytes")
        min_decoration_bytes = inventory.get("min_decoration_bytes")
        if not all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in (min_drawables, min_bytes, min_decoration_bytes)
        ):
            raise AuthoringRoundtripError(
                "Flat vector inventory extraction thresholds are invalid"
            )
        icon_namespace = inventory.get("icon_namespace")
        if icon_namespace != IMPORTED_ICON_NAMESPACE:
            raise AuthoringRoundtripError(
                "Flat vector inventory must use icon_namespace='imported'"
            )
        baseline_icons = baseline_root / "_baseline_icons"
        entries: list[dict[str, Any]] = []
        for document in sorted(documents.values(), key=lambda item: item.name):
            entries.extend(
                extract_file(
                    baseline_root / document.name,
                    baseline_icons,
                    IMPORTED_ICON_NAMESPACE,
                    int(min_drawables),
                    int(min_bytes),
                    int(min_decoration_bytes),
                    True,
                    "baseline",
                    None,
                    None,
                )
            )
        return temporary, baseline_root, _baseline_assets(entries, baseline_icons)
    except Exception:
        temporary.cleanup()
        raise


def _collapse_hash_only_groups(root: ET.Element) -> None:
    """Canonicalize attribute-free one-child wrappers for edit comparison."""
    for parent in list(root.iter()):
        changed = True
        while changed:
            changed = False
            for index, child in enumerate(list(parent)):
                if (
                    _local_name(child.tag) != "g"
                    or child.attrib
                    or len(child) != 1
                    or (child.text and child.text.strip())
                ):
                    continue
                replacement = child[0]
                replacement.tail = child.tail
                parent.remove(child)
                parent.insert(index, replacement)
                changed = True
                break


def _normalized_hash(
    element: ET.Element,
    assets: dict[str, VectorAssetRecord],
    *,
    asset: VectorAssetRecord | None = None,
) -> str:
    normalized = copy.deepcopy(element)
    if asset is not None and not asset.unchanged:
        normalized.set(
            "data-pptx-edited-vector-asset-sha256",
            asset.actual_asset_sha256,
        )
    prefix = f"{asset.element_prefix}_" if asset is not None else None

    def rewrite_url(match: re.Match[str]) -> str:
        quote, ref_id = match.group(1), match.group(2)
        if prefix and ref_id.startswith(prefix):
            ref_id = ref_id[len(prefix):]
        return f"url({quote}#{ref_id}{quote})"

    for item in normalized.iter():
        if prefix:
            item_id = item.get("id")
            if item_id and item_id.startswith(prefix):
                item.set("id", item_id[len(prefix):])
            for name, value in list(item.attrib.items()):
                rewritten = _URL_ID_RE.sub(rewrite_url, value)
                if _local_name(name) == "href" and rewritten.startswith(f"#{prefix}"):
                    rewritten = "#" + rewritten[len(prefix) + 1:]
                if rewritten != value:
                    item.set(name, rewritten)
        if asset is not None:
            for name, value in list(item.attrib.items()):
                if _local_name(name) != "href" or value.startswith(("#", "data:")):
                    continue
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                resolved = (
                    asset.asset_path.parent / unquote(parsed.path)
                ).resolve()
                normalized_ref = f"asset-resource:{resolved.as_posix()}"
                if parsed.query:
                    normalized_ref += f"?{parsed.query}"
                if parsed.fragment:
                    normalized_ref += f"#{parsed.fragment}"
                item.set(name, normalized_ref)
        icon = item.get("data-icon")
        record = assets.get(icon or "")
        if record is not None:
            token = f"asset-slot:{record.baseline_key}"
            if not record.unchanged:
                token += f":edited:{record.actual_asset_sha256}"
            item.set("data-icon", token)
    normalize_single_child_group_filters(normalized)
    _collapse_hash_only_groups(normalized)
    return semantic_subtree_sha256(
        normalized,
        ignored_attributes=frozenset({SOURCE_REF_ATTRIBUTE}),
    )


def _referenced_assets(
    root: ET.Element,
    assets: dict[str, VectorAssetRecord],
    *,
    document_name: str,
) -> dict[str, tuple[VectorAssetRecord, ET.Element]]:
    referenced: dict[str, tuple[VectorAssetRecord, ET.Element]] = {}
    for element in root.iter():
        icon = (element.get("data-icon") or "").strip()
        if not icon or icon in referenced:
            continue
        record = assets.get(icon)
        if record is None:
            if icon.startswith(f"{IMPORTED_ICON_NAMESPACE}/"):
                raise AuthoringRoundtripError(
                    f"{document_name} references imported vector {icon!r} "
                    "without an inventory record"
                )
            continue
        if record.origin_document != document_name:
            raise AuthoringRoundtripError(
                f"{document_name} references {icon!r} owned by "
                f"{record.origin_document}"
            )
        referenced[icon] = (record, _parse_svg(record.asset_path))
    return referenced


def _ref_occurrences(
    root: ET.Element,
    referenced_assets: dict[str, tuple[VectorAssetRecord, ET.Element]],
) -> dict[str, list[RefOccurrence]]:
    occurrences: dict[str, list[RefOccurrence]] = {}
    for element in root.iter():
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if source_ref:
            occurrences.setdefault(source_ref, []).append(
                RefOccurrence(element=element, asset=None)
            )
    for record, asset_root in referenced_assets.values():
        for element in asset_root.iter():
            source_ref = element.get(SOURCE_REF_ATTRIBUTE)
            if source_ref:
                occurrences.setdefault(source_ref, []).append(
                    RefOccurrence(element=element, asset=record)
                )
    return occurrences


def _outer_source_ref_elements(root: ET.Element) -> list[ET.Element]:
    elements: list[ET.Element] = []

    def visit(element: ET.Element, inside_ref: bool) -> None:
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if source_ref and not inside_ref:
            elements.append(element)
            return
        for child in element:
            visit(child, inside_ref or bool(source_ref))

    visit(root, False)
    return elements


def _layered_ref_index(root: ET.Element) -> dict[str, ET.Element]:
    index: dict[str, ET.Element] = {}
    for element in root.iter():
        if not element.get("id") or not element.get("data-pptx-object"):
            continue
        source_ref = _source_identity(element)
        if source_ref is None:
            continue
        if source_ref in index:
            raise AuthoringRoundtripError(
                f"Layered SVG contains duplicate source identity {source_ref!r}"
            )
        index[source_ref] = element
    return index


def _direct_defs(root: ET.Element) -> ET.Element | None:
    return next(
        (child for child in root if _local_name(child.tag) == "defs"),
        None,
    )


def _definition_changes(
    current_root: ET.Element,
    baseline_root: ET.Element,
    current_assets: dict[str, VectorAssetRecord],
    baseline_assets: dict[str, VectorAssetRecord],
) -> tuple[bool, set[str]]:
    current_defs = _direct_defs(current_root)
    baseline_defs = _direct_defs(baseline_root)
    current_hash = (
        _normalized_hash(current_defs, current_assets)
        if current_defs is not None
        else None
    )
    baseline_hash = (
        _normalized_hash(baseline_defs, baseline_assets)
        if baseline_defs is not None
        else None
    )
    if current_hash == baseline_hash:
        return False, set()
    current_children = list(current_defs) if current_defs is not None else []
    baseline_children = list(baseline_defs) if baseline_defs is not None else []
    current_by_id = {
        child.get("id"): child
        for child in current_children
        if child.get("id")
    }
    baseline_by_id = {
        child.get("id"): child
        for child in baseline_children
        if child.get("id")
    }
    changed_ids = {
        definition_id
        for definition_id in set(current_by_id) | set(baseline_by_id)
        if definition_id not in current_by_id
        or definition_id not in baseline_by_id
        or _normalized_hash(current_by_id[definition_id], current_assets)
        != _normalized_hash(baseline_by_id[definition_id], baseline_assets)
    }
    return True, changed_ids


def _referenced_definition_ids(element: ET.Element) -> set[str]:
    references: set[str] = set()
    for item in element.iter():
        for name, value in item.attrib.items():
            references.update(match.group(2) for match in _URL_ID_RE.finditer(value))
            if _local_name(name) == "href" and value.startswith("#"):
                references.add(value[1:])
    return references


def _merge_defs(
    layered_root: ET.Element,
    authoring_root: ET.Element,
    *,
    include_authoring_changes: bool,
) -> ET.Element | None:
    layered_defs = _direct_defs(layered_root)
    authoring_defs = _direct_defs(authoring_root)
    if layered_defs is None and (
        authoring_defs is None or not include_authoring_changes
    ):
        return None
    merged = (
        copy.deepcopy(layered_defs)
        if layered_defs is not None
        else ET.Element(f"{{{SVG_NS}}}defs")
    )
    if not include_authoring_changes or authoring_defs is None:
        return merged
    by_id = {
        child.get("id"): (index, child)
        for index, child in enumerate(merged)
        if child.get("id")
    }
    existing_hashes = {
        semantic_subtree_sha256(child)
        for child in merged
    }
    for child in authoring_defs:
        clone = copy.deepcopy(child)
        definition_id = clone.get("id")
        if definition_id and definition_id in by_id:
            index, previous = by_id[definition_id]
            projected_previous = copy.deepcopy(previous)
            for item in projected_previous.iter():
                for name in AUTHORING_OMITTED_SOURCE_ATTRIBUTES:
                    item.attrib.pop(name, None)
            if (
                semantic_subtree_sha256(projected_previous)
                == semantic_subtree_sha256(clone)
            ):
                continue
            merged.remove(previous)
            merged.insert(index, clone)
            by_id[definition_id] = (index, clone)
            continue
        child_hash = semantic_subtree_sha256(clone)
        if child_hash not in existing_hashes:
            merged.append(clone)
            existing_hashes.add(child_hash)
    return merged


def _serialize_svg(root: ET.Element) -> bytes:
    payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return payload if payload.endswith(b"\n") else payload + b"\n"


def _rebase_resource_references(
    element: ET.Element,
    source_dir: Path,
    target_dir: Path,
    project_path: Path,
    *,
    recursive: bool,
) -> None:
    """Rebase exact local SVG resource hrefs without path guessing."""
    nodes = element.iter() if recursive else (element,)
    project_root = project_path.resolve()
    for node in nodes:
        if _local_name(node.tag) == "a":
            continue
        for name in ("href", f"{{{XLINK_NS}}}href"):
            raw = node.get(name)
            if raw is None or not raw or raw.startswith("#") or raw.startswith("data:"):
                continue
            parsed = urlsplit(raw)
            if (
                parsed.scheme
                or parsed.netloc
                or parsed.query
                or parsed.fragment
                or not parsed.path
                or Path(unquote(parsed.path)).is_absolute()
            ):
                raise AuthoringRoundtripError(
                    f"Unsupported SVG resource reference in {element.tag}: {raw!r}"
                )
            resolved = (source_dir / unquote(parsed.path)).resolve()
            try:
                resolved.relative_to(project_root)
            except ValueError as exc:
                raise AuthoringRoundtripError(
                    f"SVG resource reference escapes the project: {raw!r}"
                ) from exc
            relative = os.path.relpath(resolved, target_dir).replace(os.sep, "/")
            node.set(name, urlunsplit(("", "", relative, "", "")))


def _restore_preserved_effect_metadata(
    target: ET.Element,
    source: ET.Element,
) -> None:
    """Keep source-native effects when an author edits other object semantics."""
    source_by_id = {
        item_id: item
        for item in source.iter()
        if (item_id := item.get("id"))
    }
    for item in target.iter():
        source_item = (
            source
            if item is target
            else source_by_id.get(item.get("id") or "")
        )
        if source_item is None:
            continue
        for name in _PRESERVED_EFFECT_ATTRIBUTES:
            value = source_item.get(name)
            if value is not None and item.get(name) is None:
                item.set(name, value)


def _materialize_document(
    project_path: Path,
    document: AuthoringDocument,
    baseline_path: Path,
    output_path: Path,
    current_assets: dict[str, VectorAssetRecord],
    baseline_assets: dict[str, VectorAssetRecord],
) -> dict[str, Any]:
    current_root = _parse_svg(document.authoring_path)
    baseline_root = _parse_svg(baseline_path)
    layered_root = _parse_svg(document.layered_source_path)
    document_unchanged = (
        _normalized_hash(current_root, current_assets)
        == _normalized_hash(baseline_root, baseline_assets)
    )
    layered_index = _layered_ref_index(layered_root)
    current_referenced_assets = _referenced_assets(
        current_root,
        current_assets,
        document_name=document.name,
    )
    baseline_referenced_assets = _referenced_assets(
        baseline_root,
        baseline_assets,
        document_name=document.name,
    )
    current_occurrences = _ref_occurrences(
        current_root,
        current_referenced_assets,
    )
    baseline_occurrences = _ref_occurrences(
        baseline_root,
        baseline_referenced_assets,
    )
    expected_refs = set(document.source_refs)
    baseline_refs = set(baseline_occurrences)
    if baseline_refs != expected_refs:
        raise AuthoringRoundtripError(
            f"{document.name} regenerated baseline source-ref closure differs; "
            f"missing={sorted(expected_refs - baseline_refs)}, "
            f"extra={sorted(baseline_refs - expected_refs)}"
        )
    baseline_duplicates = sorted(
        ref for ref, items in baseline_occurrences.items() if len(items) != 1
    )
    if baseline_duplicates:
        raise AuthoringRoundtripError(
            f"{document.name} regenerated baseline has duplicate source refs: "
            + ", ".join(baseline_duplicates)
        )
    manifest_proxy_refs = {
        source_ref
        for source_ref, record in document.source_refs.items()
        if record.representation == "source-proxy"
    }
    baseline_proxy_refs = {
        source_ref
        for source_ref, occurrences in baseline_occurrences.items()
        if occurrences[0].element.get(SOURCE_PROXY_ATTRIBUTE) == SOURCE_PROXY_KIND
    }
    if baseline_proxy_refs != manifest_proxy_refs:
        raise AuthoringRoundtripError(
            f"{document.name} regenerated source-proxy roster differs; "
            f"missing={sorted(manifest_proxy_refs - baseline_proxy_refs)}, "
            f"extra={sorted(baseline_proxy_refs - manifest_proxy_refs)}"
        )
    current_unknown = sorted(set(current_occurrences) - expected_refs)
    if current_unknown:
        raise AuthoringRoundtripError(
            f"{document.name} contains unknown source refs: "
            + ", ".join(current_unknown)
        )
    current_duplicates = sorted(
        ref for ref, items in current_occurrences.items() if len(items) != 1
    )
    if current_duplicates:
        raise AuthoringRoundtripError(
            f"{document.name} contains duplicate source refs: "
            + ", ".join(current_duplicates)
        )

    defs_changed, changed_definition_ids = _definition_changes(
        current_root,
        baseline_root,
        current_assets,
        baseline_assets,
    )
    unchanged_refs: set[str] = set()
    edited_refs: set[str] = set()
    for source_ref, occurrences in current_occurrences.items():
        current = occurrences[0]
        baseline = baseline_occurrences[source_ref][0]
        current_hash = _normalized_hash(
            current.element,
            current_assets,
            asset=current.asset,
        )
        baseline_hash = _normalized_hash(
            baseline.element,
            baseline_assets,
            asset=baseline.asset,
        )
        references_changed_def = bool(
            changed_definition_ids
            & _referenced_definition_ids(current.element)
        )
        if current_hash == baseline_hash and not references_changed_def:
            unchanged_refs.add(source_ref)
        else:
            edited_refs.add(source_ref)
    deleted_refs = expected_refs - set(current_occurrences)
    edited_proxy_refs = sorted(edited_refs & manifest_proxy_refs)
    if edited_proxy_refs:
        raise AuthoringRoundtripError(
            f"{document.name} edits source-backed proxy object(s): "
            + ", ".join(edited_proxy_refs)
            + "; keep each proxy unchanged to restore its native PowerPoint "
            "object; only a complete Slide-local proxy may be removed to "
            "delete that object"
        )
    deleted_inherited_proxy_refs = sorted(
        source_ref
        for source_ref in deleted_refs & manifest_proxy_refs
        if not source_ref.startswith("slide:")
    )
    if deleted_inherited_proxy_refs:
        raise AuthoringRoundtripError(
            f"{document.name} deletes inherited source-backed proxy object(s): "
            + ", ".join(deleted_inherited_proxy_refs)
            + "; Master/Layout proxies must remain unchanged because a flat "
            "slide cannot delete shared structure"
        )

    def restore_nodes(
        element: ET.Element,
        source_dir: Path | None = None,
    ) -> list[ET.Element]:
        source_dir = source_dir or document.authoring_path.parent
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if source_ref in unchanged_refs:
            scope = source_ref.split(":", 1)[0]
            if scope != "slide":
                return []
            source = layered_index.get(source_ref)
            if source is None:
                raise AuthoringRoundtripError(
                    f"{document.name} cannot find {source_ref!r} in layered source"
                )
            restored = copy.deepcopy(source)
            _rebase_resource_references(
                restored,
                document.layered_source_path.parent,
                output_path.parent,
                project_path,
                recursive=True,
            )
            return [restored]

        if _local_name(element.tag) == "use":
            icon = (element.get("data-icon") or "").strip()
            referenced = current_referenced_assets.get(icon)
            if referenced is not None:
                record, asset_root = referenced
                outer_refs = _outer_source_ref_elements(asset_root)
                if outer_refs:
                    restored: list[ET.Element] = []
                    for outer in outer_refs:
                        restored.extend(
                            restore_nodes(outer, record.asset_path.parent)
                        )
                    return restored

        clone = copy.deepcopy(element)
        for child in list(clone):
            clone.remove(child)
        for original_child in element:
            replacements = restore_nodes(original_child, source_dir)
            if replacements:
                replacements[-1].tail = original_child.tail
            for replacement in replacements:
                clone.append(replacement)
        clone.attrib.pop(SOURCE_REF_ATTRIBUTE, None)
        _rebase_resource_references(
            clone,
            source_dir,
            output_path.parent,
            project_path,
            recursive=False,
        )
        if source_ref:
            source = layered_index.get(source_ref)
            if source is not None:
                if source_ref.startswith("slide:"):
                    for name in (
                        "data-pptx-shape-id",
                        "data-pptx-shape-scope",
                        "data-pptx-shape-name",
                        "data-name",
                    ):
                        if clone.get(name) is None and source.get(name) is not None:
                            clone.set(name, str(source.get(name)))
                _restore_preserved_effect_metadata(clone, source)
        return [clone]

    baseline_unreferenced = Counter(
        _normalized_hash(child, baseline_assets)
        for child in baseline_root
        if _local_name(child.tag) != "defs"
        and child.get(SOURCE_REF_ATTRIBUTE) is None
        and _local_name(child.tag) != "use"
    )
    output_root = copy.deepcopy(layered_root)
    for child in list(output_root):
        output_root.remove(child)
    for name in ("width", "height", "viewBox"):
        value = current_root.get(name)
        if value is not None:
            output_root.set(name, value)
    layered_defs_root = copy.deepcopy(layered_root)
    current_defs_root = copy.deepcopy(current_root)
    _rebase_resource_references(
        layered_defs_root,
        document.layered_source_path.parent,
        output_path.parent,
        project_path,
        recursive=True,
    )
    _rebase_resource_references(
        current_defs_root,
        document.authoring_path.parent,
        output_path.parent,
        project_path,
        recursive=True,
    )
    merged_defs = _merge_defs(
        layered_defs_root,
        current_defs_root,
        include_authoring_changes=defs_changed or bool(edited_refs),
    )
    merged_definition_ids = {
        definition_id
        for definition in (list(merged_defs) if merged_defs is not None else [])
        if (definition_id := definition.get("id"))
    }
    merged_definition_hashes = {
        semantic_subtree_sha256(definition)
        for definition in (list(merged_defs) if merged_defs is not None else [])
    }
    for record, asset_root in current_referenced_assets.values():
        asset_defs = _direct_defs(asset_root)
        if (
            record.unchanged
            or asset_defs is None
            or not _outer_source_ref_elements(asset_root)
        ):
            continue
        if merged_defs is None:
            merged_defs = ET.Element(f"{{{SVG_NS}}}defs")
        for definition in asset_defs:
            clone = copy.deepcopy(definition)
            _rebase_resource_references(
                clone,
                record.asset_path.parent,
                output_path.parent,
                project_path,
                recursive=True,
            )
            definition_id = clone.get("id")
            definition_hash = semantic_subtree_sha256(clone)
            if definition_hash in merged_definition_hashes:
                continue
            if definition_id and definition_id in merged_definition_ids:
                raise AuthoringRoundtripError(
                    f"{document.name} edited vector asset definition id "
                    f"collides with page definitions: {definition_id!r}"
                )
            merged_defs.append(clone)
            merged_definition_hashes.add(definition_hash)
            if definition_id:
                merged_definition_ids.add(definition_id)
    if merged_defs is not None and list(merged_defs):
        output_root.append(merged_defs)

    authored_unreferenced = 0
    expanded_vector_uses = 0
    for child in current_root:
        if _local_name(child.tag) == "defs":
            continue
        if (
            child.get(SOURCE_REF_ATTRIBUTE) is None
            and _local_name(child.tag) != "use"
        ):
            child_hash = _normalized_hash(child, current_assets)
            if baseline_unreferenced[child_hash] > 0:
                baseline_unreferenced[child_hash] -= 1
                continue
            authored_unreferenced += 1
        replacements = restore_nodes(child)
        if _local_name(child.tag) == "use" and len(replacements) > 1:
            expanded_vector_uses += 1
        for replacement in replacements:
            output_root.append(replacement)

    residual_refs = sorted({
        source_ref
        for element in output_root.iter()
        if (source_ref := element.get(SOURCE_REF_ATTRIBUTE))
    })
    if residual_refs:
        raise AuthoringRoundtripError(
            f"{document.name} materialization left source refs: {residual_refs[:5]}"
        )
    output_path.write_bytes(_serialize_svg(output_root))
    return {
        "file": document.name,
        "document_unchanged": document_unchanged,
        "source_ref_count": len(expected_refs),
        "source_ref_ids": sorted(expected_refs),
        "unchanged_refs": len(unchanged_refs),
        "unchanged_ref_ids": sorted(unchanged_refs),
        "edited_refs": len(edited_refs),
        "edited_ref_ids": sorted(edited_refs),
        "deleted_refs": len(deleted_refs),
        "deleted_ref_ids": sorted(deleted_refs),
        "authored_unreferenced": authored_unreferenced,
        "expanded_vector_uses": expanded_vector_uses,
        "defs_changed": defs_changed,
    }


def materialize_flat_authoring_roundtrip(
    project_path: Path,
    authoring_dir: Path,
    output_dir: Path,
) -> AuthoringRoundtripResult:
    """Materialize a flat authoring bundle into preserve-mode slide SVGs."""
    project_path = project_path.resolve()
    authoring_dir = authoring_dir.resolve()
    output_dir = output_dir.resolve()
    try:
        authoring_dir.relative_to(project_path)
        output_dir.relative_to(project_path)
    except ValueError as exc:
        raise AuthoringRoundtripError(
            "Authoring and materialized directories must stay inside the project"
        ) from exc
    if not authoring_dir.is_dir():
        raise AuthoringRoundtripError(
            f"Authoring directory does not exist: {authoring_dir}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        raise AuthoringRoundtripError(
            f"Materialized output directory must be empty: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    source_root, source_proxy_dir, documents, manifest = _load_documents(
        project_path,
        authoring_dir,
    )
    current_assets, inventory = _load_current_assets(
        project_path,
        authoring_dir,
        documents,
    )
    baseline_temporary, baseline_root, baseline_assets = _generate_baseline_bundle(
        project_path,
        source_root,
        source_proxy_dir,
        documents,
        inventory,
    )
    try:
        current_keys = sorted(record.baseline_key for record in current_assets.values())
        baseline_keys = sorted(record.baseline_key for record in baseline_assets.values())
        if current_keys != baseline_keys:
            raise AuthoringRoundtripError(
                "Regenerated flat vector extraction differs from its inventory; "
                f"missing={sorted(set(current_keys) - set(baseline_keys))}, "
                f"extra={sorted(set(baseline_keys) - set(current_keys))}"
            )
        document_reports = [
            _materialize_document(
                project_path,
                document,
                baseline_root / document.name,
                output_dir / document.name,
                current_assets,
                baseline_assets,
            )
            for document in sorted(documents.values(), key=lambda item: item.name)
        ]
    finally:
        baseline_temporary.cleanup()

    svg_files = tuple(discover_slide_svgs(output_dir))
    if len(svg_files) != len(documents):
        raise AuthoringRoundtripError(
            "Materialized slide roster does not match the authoring manifest"
        )
    totals = {
        key: sum(int(item[key]) for item in document_reports)
        for key in (
            "source_ref_count",
            "unchanged_refs",
            "edited_refs",
            "deleted_refs",
            "authored_unreferenced",
            "expanded_vector_uses",
        )
    }
    report: dict[str, Any] = {
        "schema": "ppt-master.authoring-roundtrip-materialization.v1",
        "authoring_root": str(authoring_dir),
        "manifest_schema": manifest.get("schema"),
        "projection_kind": manifest.get("projection_kind"),
        "materialized_slide_count": len(svg_files),
        "totals": totals,
        "documents": document_reports,
    }
    return AuthoringRoundtripResult(svg_files=svg_files, report=report)
