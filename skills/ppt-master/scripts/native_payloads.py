#!/usr/bin/env python3
"""
PPT Master - Native SVG Metadata Store

Deduplicate opaque PowerPoint-native payloads and repeated restoration
attributes into one deterministic gzip-compressed workspace store, then
hydrate legacy inline metadata on demand.

Usage:
    Imported by mirror materialization, SVG validation, and SVG-to-PPTX export.

Examples:
    from native_payloads import hydrate_native_payload_refs

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import base64
import binascii
import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


LEGACY_PAYLOAD_STORE_SCHEMA = "ppt-master.native-payload-store.v1"
PAYLOAD_STORE_SCHEMA = "ppt-master.native-payload-store.v2"
PAYLOAD_STORE_FILENAME = "native_payloads.json.gz"
PAYLOAD_STORE_RELATIVE_PATH = Path("templates") / PAYLOAD_STORE_FILENAME
PAYLOAD_STORE_REFERENCE_PREFIX = (
    f"project:{PAYLOAD_STORE_RELATIVE_PATH.as_posix()}#sha256:"
)

NATIVE_RECORD_REF_ATTRIBUTE = "data-pptx-native-ref"
TXBODY_REF_ATTRIBUTE = "data-pptx-ref"
SHAPE_STYLE_ATTRIBUTE = "data-pptx-shape-style"
SHAPE_STYLE_REF_ATTRIBUTE = "data-pptx-shape-style-ref"
CUSTOM_GEOMETRY_ATTRIBUTE = "data-pptx-custgeom"
CUSTOM_GEOMETRY_REF_ATTRIBUTE = "data-pptx-custgeom-ref"

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_NATIVE_RECORD_ID_RE = re.compile(r"r(?:0|[1-9][0-9]*)")
_NATIVE_RECORD_ATTRIBUTES = frozenset({
    "data-pptx-custgeom-ref",
    "data-pptx-frame",
    "data-pptx-geometry-kind",
    "data-pptx-geometry-sha256",
    "data-pptx-object",
    "data-pptx-part",
    "data-pptx-preview-sha256",
    "data-pptx-prst",
    "data-pptx-ref",
    "data-pptx-shape-id",
    "data-pptx-shape-name",
    "data-pptx-shape-scope",
    "data-pptx-shape-style-ref",
    "data-pptx-text-sha256",
})
_NATIVE_RECORD_PREFIXES = (
    "data-pptx-av-",
    "data-pptx-end-",
    "data-pptx-start-",
)


class NativePayloadError(ValueError):
    """Reject malformed, missing, or contradictory native metadata transport."""


@dataclass
class NativePayloadStats:
    """Count externalized native metadata and its original inline bytes."""

    txbody_count: int = 0
    shape_style_count: int = 0
    custom_geometry_count: int = 0
    inline_bytes: int = 0
    native_record_count: int = 0
    native_attribute_bytes: int = 0

    def merge(self, other: "NativePayloadStats") -> None:
        self.txbody_count += other.txbody_count
        self.shape_style_count += other.shape_style_count
        self.custom_geometry_count += other.custom_geometry_count
        self.inline_bytes += other.inline_bytes
        self.native_record_count += other.native_record_count
        self.native_attribute_bytes += other.native_attribute_bytes

    def as_dict(self) -> dict[str, int]:
        return {
            "txbody_count": self.txbody_count,
            "shape_style_count": self.shape_style_count,
            "custom_geometry_count": self.custom_geometry_count,
            "inline_bytes": self.inline_bytes,
            "native_record_count": self.native_record_count,
            "native_attribute_bytes": self.native_attribute_bytes,
        }


@dataclass(frozen=True)
class NativePayloadStore:
    """Validated payload and native-attribute records loaded from one store."""

    payloads: dict[str, bytes]
    native_records: dict[str, dict[str, str]]


_STORE_CACHE: dict[Path, tuple[int, int, NativePayloadStore]] = {}


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _decode_base64(value: str, *, context: str) -> bytes:
    try:
        return base64.b64decode(value.strip(), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise NativePayloadError(f"{context} is not valid base64: {exc}") from exc


def _register_payload(payloads: dict[str, bytes], raw: bytes) -> str:
    digest = _sha256(raw)
    existing = payloads.get(digest)
    if existing is not None and existing != raw:
        raise NativePayloadError(
            f"SHA-256 collision while registering native payload {digest}"
        )
    payloads[digest] = raw
    return PAYLOAD_STORE_REFERENCE_PREFIX + digest


def _is_native_record_attribute(name: str) -> bool:
    return (
        name in _NATIVE_RECORD_ATTRIBUTES
        or name.startswith(_NATIVE_RECORD_PREFIXES)
    )


def _native_record_attributes(element: ET.Element) -> dict[str, str]:
    return {
        name: value
        for name, value in element.attrib.items()
        if _is_native_record_attribute(name)
    }


def _native_record_key(attributes: dict[str, str]) -> str:
    return json.dumps(
        attributes,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def collect_native_attribute_record_keys(root: ET.Element) -> set[str]:
    """Return canonical record keys for compressible native attributes."""
    keys: set[str] = set()
    for element in root.iter():
        if NATIVE_RECORD_REF_ATTRIBUTE in element.attrib:
            raise NativePayloadError(
                "native metadata is already externalized; source attributes "
                "must be hydrated before building a new store"
            )
        attributes = _native_record_attributes(element)
        if attributes:
            keys.add(_native_record_key(attributes))
    return keys


def build_native_attribute_records(
    record_keys: set[str],
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Assign deterministic short ids to canonical native-attribute records."""
    ids_by_key: dict[str, str] = {}
    records: dict[str, dict[str, str]] = {}
    for index, key in enumerate(sorted(record_keys)):
        try:
            attributes = json.loads(key)
        except json.JSONDecodeError as exc:
            raise NativePayloadError(
                f"Cannot decode canonical native-attribute record: {exc}"
            ) from exc
        if not isinstance(attributes, dict) or not attributes:
            raise NativePayloadError(
                "Canonical native-attribute record must be a non-empty object"
            )
        if any(
            not isinstance(name, str)
            or not isinstance(value, str)
            or not _is_native_record_attribute(name)
            for name, value in attributes.items()
        ):
            raise NativePayloadError(
                "Canonical native-attribute record contains an unsupported field"
            )
        record_id = f"r{index}"
        ids_by_key[key] = record_id
        records[record_id] = attributes
    return ids_by_key, records


def externalize_native_attribute_records(
    root: ET.Element,
    ids_by_key: dict[str, str],
) -> NativePayloadStats:
    """Replace supported native-attribute groups with deterministic short ids."""
    stats = NativePayloadStats()
    for element in root.iter():
        if NATIVE_RECORD_REF_ATTRIBUTE in element.attrib:
            raise NativePayloadError(
                "native metadata is already externalized; source attributes "
                "must be hydrated before building a new store"
            )
        attributes = _native_record_attributes(element)
        if not attributes:
            continue
        record_id = ids_by_key.get(_native_record_key(attributes))
        if record_id is None:
            raise NativePayloadError(
                "Native-attribute record was not registered before externalization"
            )
        for name in attributes:
            element.attrib.pop(name)
        element.set(NATIVE_RECORD_REF_ATTRIBUTE, record_id)
        stats.native_record_count += 1
        stats.native_attribute_bytes += sum(
            len(name) + len(value) + 4
            for name, value in attributes.items()
        )
    return stats


def externalize_native_payloads(
    root: ET.Element,
    payloads: dict[str, bytes],
) -> NativePayloadStats:
    """Move supported large inline native payloads into ``payloads``.

    Repeated restoration attributes are handled separately by
    ``externalize_native_attribute_records``. The supported opaque payload
    classes are:

    - ``metadata[data-pptx-part="txbody"]``
    - ``data-pptx-shape-style``
    - ``data-pptx-custgeom``
    """
    stats = NativePayloadStats()
    for element in root.iter():
        if (
            _local_name(element.tag) == "metadata"
            and element.get("data-pptx-part") == "txbody"
        ):
            has_reference = TXBODY_REF_ATTRIBUTE in element.attrib
            reference = element.get(TXBODY_REF_ATTRIBUTE) or ""
            encoded = (element.text or "").strip()
            encoding = element.get("data-pptx-encoding")
            if has_reference:
                if not reference:
                    raise NativePayloadError(
                        "txbody metadata has an empty payload reference"
                    )
                raise NativePayloadError(
                    "txbody metadata is already externalized; source payload "
                    "must be hydrated before building a new store"
                )
            elif encoded:
                if encoding != "base64":
                    raise NativePayloadError(
                        "txbody metadata must use base64 before externalization"
                    )
                raw = _decode_base64(encoded, context="txbody metadata")
                element.text = None
                element.attrib.pop("data-pptx-encoding", None)
                element.set(TXBODY_REF_ATTRIBUTE, _register_payload(payloads, raw))
                stats.txbody_count += 1
                stats.inline_bytes += len(encoded)
            else:
                raise NativePayloadError(
                    "txbody metadata requires inline base64 data or a payload reference"
                )

        has_shape_reference = SHAPE_STYLE_REF_ATTRIBUTE in element.attrib
        shape_reference = element.get(SHAPE_STYLE_REF_ATTRIBUTE) or ""
        shape_encoded = element.get(SHAPE_STYLE_ATTRIBUTE)
        if has_shape_reference and not shape_reference:
            raise NativePayloadError("shape-style metadata has an empty payload reference")
        if has_shape_reference:
            raise NativePayloadError(
                "shape-style metadata is already externalized; source payload "
                "must be hydrated before building a new store"
            )
        if shape_encoded:
            raw = _decode_base64(shape_encoded, context="shape-style metadata")
            element.attrib.pop(SHAPE_STYLE_ATTRIBUTE, None)
            element.set(
                SHAPE_STYLE_REF_ATTRIBUTE,
                _register_payload(payloads, raw),
            )
            stats.shape_style_count += 1
            stats.inline_bytes += len(shape_encoded)

        has_geometry_reference = CUSTOM_GEOMETRY_REF_ATTRIBUTE in element.attrib
        geometry_reference = element.get(CUSTOM_GEOMETRY_REF_ATTRIBUTE) or ""
        geometry_encoded = element.get(CUSTOM_GEOMETRY_ATTRIBUTE)
        if has_geometry_reference and not geometry_reference:
            raise NativePayloadError(
                "custom-geometry metadata has an empty payload reference"
            )
        if has_geometry_reference:
            raise NativePayloadError(
                "custom-geometry metadata is already externalized; source payload "
                "must be hydrated before building a new store"
            )
        if geometry_encoded:
            raw = _decode_base64(geometry_encoded, context="custom-geometry metadata")
            element.attrib.pop(CUSTOM_GEOMETRY_ATTRIBUTE, None)
            element.set(
                CUSTOM_GEOMETRY_REF_ATTRIBUTE,
                _register_payload(payloads, raw),
            )
            stats.custom_geometry_count += 1
            stats.inline_bytes += len(geometry_encoded)
    return stats


def serialize_native_payload_store(
    payloads: dict[str, bytes],
    native_records: dict[str, dict[str, str]] | None = None,
) -> bytes:
    """Return one deterministic gzip-compressed native metadata store."""
    encoded_payloads: dict[str, str] = {}
    for digest, raw in sorted(payloads.items()):
        if _SHA256_RE.fullmatch(digest) is None or _sha256(raw) != digest:
            raise NativePayloadError(
                f"Native payload store key does not match its content: {digest!r}"
            )
        encoded_payloads[digest] = base64.b64encode(raw).decode("ascii")
    encoded_records: dict[str, dict[str, str]] = {}
    for record_id, attributes in sorted((native_records or {}).items()):
        if _NATIVE_RECORD_ID_RE.fullmatch(record_id) is None:
            raise NativePayloadError(
                f"Native metadata store contains an invalid record id: {record_id!r}"
            )
        if not isinstance(attributes, dict) or not attributes:
            raise NativePayloadError(
                f"Native metadata record {record_id} must be a non-empty object"
            )
        if any(
            not isinstance(name, str)
            or not isinstance(value, str)
            or not _is_native_record_attribute(name)
            for name, value in attributes.items()
        ):
            raise NativePayloadError(
                f"Native metadata record {record_id} contains an unsupported field"
            )
        encoded_records[record_id] = dict(sorted(attributes.items()))
    document = {
        "schema": PAYLOAD_STORE_SCHEMA,
        "hash": "sha256",
        "payloads": encoded_payloads,
        "native_records": encoded_records,
    }
    raw_json = json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return gzip.compress(raw_json, compresslevel=9, mtime=0)


def _parse_reference(value: str) -> tuple[PurePosixPath, str]:
    prefix = "project:"
    marker = "#sha256:"
    if not value.startswith(prefix) or marker not in value:
        raise NativePayloadError(
            f"Unsupported native payload reference: {value!r}"
        )
    path_text, digest = value[len(prefix):].split(marker, 1)
    relative = PurePosixPath(path_text)
    if (
        not path_text
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise NativePayloadError(
            f"Native payload reference must use a safe project-relative path: {value!r}"
        )
    if _SHA256_RE.fullmatch(digest) is None:
        raise NativePayloadError(
            f"Native payload reference has an invalid SHA-256 digest: {value!r}"
        )
    return relative, digest


def _resolve_store_path(svg_path: Path, relative: PurePosixPath) -> Path:
    start = Path(svg_path).expanduser().resolve().parent
    relative_path = Path(*relative.parts)
    for base in (start, *start.parents):
        candidate = base / relative_path
        if candidate.is_file():
            return candidate.resolve()
    raise NativePayloadError(
        f"Native payload store not found for {svg_path}: {relative.as_posix()}"
    )


def _load_store(path: Path) -> NativePayloadStore:
    resolved = path.resolve()
    try:
        stat = resolved.stat()
    except OSError as exc:
        raise NativePayloadError(
            f"Cannot inspect native payload store {resolved}: {exc}"
        ) from exc
    cached = _STORE_CACHE.get(resolved)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return cached[2]

    try:
        document = json.loads(gzip.decompress(resolved.read_bytes()).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativePayloadError(
            f"Cannot decode native payload store {resolved}: {exc}"
        ) from exc
    if not isinstance(document, dict) or document.get("schema") not in {
        LEGACY_PAYLOAD_STORE_SCHEMA,
        PAYLOAD_STORE_SCHEMA,
    }:
        raise NativePayloadError(
            f"Unsupported native payload store schema in {resolved}"
        )
    if document.get("hash") != "sha256":
        raise NativePayloadError(
            f"Unsupported native payload store hash algorithm in {resolved}"
        )
    encoded_payloads = document.get("payloads")
    if not isinstance(encoded_payloads, dict):
        raise NativePayloadError(
            f"Native payload store must contain a payload object: {resolved}"
        )

    payloads: dict[str, bytes] = {}
    for digest, encoded in encoded_payloads.items():
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise NativePayloadError(
                f"Native payload store contains an invalid digest key: {digest!r}"
            )
        if not isinstance(encoded, str):
            raise NativePayloadError(
                f"Native payload {digest} must be a base64 string"
            )
        raw = _decode_base64(
            encoded,
            context=f"native payload {digest} in {resolved}",
        )
        if _sha256(raw) != digest:
            raise NativePayloadError(
                f"Native payload {digest} failed content-hash validation"
            )
        payloads[digest] = raw
    schema = document.get("schema")
    if schema == PAYLOAD_STORE_SCHEMA and "native_records" not in document:
        raise NativePayloadError(
            f"Native payload store is missing native_records: {resolved}"
        )
    native_records_value = document.get("native_records", {})
    if schema == PAYLOAD_STORE_SCHEMA and not isinstance(native_records_value, dict):
        raise NativePayloadError(
            f"Native payload store must contain a native_records object: {resolved}"
        )
    if schema == LEGACY_PAYLOAD_STORE_SCHEMA:
        native_records_value = {}

    native_records: dict[str, dict[str, str]] = {}
    for record_id, attributes in native_records_value.items():
        if (
            not isinstance(record_id, str)
            or _NATIVE_RECORD_ID_RE.fullmatch(record_id) is None
        ):
            raise NativePayloadError(
                f"Native payload store contains an invalid record id: {record_id!r}"
            )
        if not isinstance(attributes, dict) or not attributes:
            raise NativePayloadError(
                f"Native metadata record {record_id} must be a non-empty object"
            )
        validated: dict[str, str] = {}
        for name, value in attributes.items():
            if (
                not isinstance(name, str)
                or not isinstance(value, str)
                or not _is_native_record_attribute(name)
            ):
                raise NativePayloadError(
                    f"Native metadata record {record_id} contains an unsupported field"
                )
            validated[name] = value
        native_records[record_id] = validated

    store = NativePayloadStore(
        payloads=payloads,
        native_records=native_records,
    )
    _STORE_CACHE[resolved] = (stat.st_mtime_ns, stat.st_size, store)
    return store


def _payload_for_reference(value: str, svg_path: Path) -> bytes:
    relative, digest = _parse_reference(value)
    store_path = _resolve_store_path(svg_path, relative)
    payload = _load_store(store_path).payloads.get(digest)
    if payload is None:
        raise NativePayloadError(
            f"Native payload {digest} is missing from {store_path}"
        )
    return payload


def _native_record_for_reference(
    value: str,
    svg_path: Path,
) -> dict[str, str]:
    if _NATIVE_RECORD_ID_RE.fullmatch(value) is None:
        raise NativePayloadError(
            f"Native metadata reference has an invalid record id: {value!r}"
        )
    store_path = _resolve_store_path(
        svg_path,
        PurePosixPath(PAYLOAD_STORE_RELATIVE_PATH.as_posix()),
    )
    record = _load_store(store_path).native_records.get(value)
    if record is None:
        raise NativePayloadError(
            f"Native metadata record {value} is missing from {store_path}"
        )
    return record


def hydrate_native_payload_refs(root: ET.Element, svg_path: Path) -> int:
    """Restore compact native records and payloads as legacy inline metadata.

    The operation preflights every reference before mutating the tree, so an
    invalid store leaves the caller's parsed SVG unchanged.
    """
    record_operations: list[tuple[ET.Element, dict[str, str]]] = []
    payload_operations: list[tuple[str, ET.Element, bytes]] = []
    for element in root.iter():
        effective_attributes = dict(element.attrib)
        has_native_record = NATIVE_RECORD_REF_ATTRIBUTE in element.attrib
        native_record_ref = element.get(NATIVE_RECORD_REF_ATTRIBUTE) or ""
        if has_native_record:
            if not native_record_ref:
                raise NativePayloadError(
                    "native metadata has an empty record reference"
                )
            record = _native_record_for_reference(native_record_ref, svg_path)
            conflicts = sorted(set(record) & set(element.attrib))
            if conflicts:
                raise NativePayloadError(
                    "native metadata cannot carry both inline fields and a record: "
                    + ", ".join(conflicts)
                )
            effective_attributes.update(record)
            record_operations.append((element, record))

        if (
            _local_name(element.tag) == "metadata"
            and effective_attributes.get("data-pptx-part") == "txbody"
        ):
            has_reference = TXBODY_REF_ATTRIBUTE in effective_attributes
            reference = effective_attributes.get(TXBODY_REF_ATTRIBUTE) or ""
            if has_reference:
                if not reference:
                    raise NativePayloadError(
                        "txbody metadata has an empty payload reference"
                    )
                if (element.text or "").strip() or element.get("data-pptx-encoding"):
                    raise NativePayloadError(
                        "txbody metadata cannot carry both inline data and a reference"
                    )
                payload_operations.append(
                    ("txbody", element, _payload_for_reference(reference, svg_path))
                )

        has_shape_reference = SHAPE_STYLE_REF_ATTRIBUTE in effective_attributes
        shape_reference = effective_attributes.get(SHAPE_STYLE_REF_ATTRIBUTE) or ""
        if has_shape_reference:
            if not shape_reference:
                raise NativePayloadError(
                    "shape-style metadata has an empty payload reference"
                )
            if effective_attributes.get(SHAPE_STYLE_ATTRIBUTE):
                raise NativePayloadError(
                    "shape-style metadata cannot carry both inline data and a reference"
                )
            payload_operations.append(
                (
                    "shape-style",
                    element,
                    _payload_for_reference(shape_reference, svg_path),
                )
            )

        has_geometry_reference = CUSTOM_GEOMETRY_REF_ATTRIBUTE in effective_attributes
        geometry_reference = (
            effective_attributes.get(CUSTOM_GEOMETRY_REF_ATTRIBUTE) or ""
        )
        if has_geometry_reference:
            if not geometry_reference:
                raise NativePayloadError(
                    "custom-geometry metadata has an empty payload reference"
                )
            if effective_attributes.get(CUSTOM_GEOMETRY_ATTRIBUTE):
                raise NativePayloadError(
                    "custom-geometry metadata cannot carry both inline data and a reference"
                )
            payload_operations.append(
                (
                    "custom-geometry",
                    element,
                    _payload_for_reference(geometry_reference, svg_path),
                )
            )

    for element, record in record_operations:
        element.attrib.pop(NATIVE_RECORD_REF_ATTRIBUTE)
        element.attrib.update(record)

    for kind, element, raw in payload_operations:
        encoded = base64.b64encode(raw).decode("ascii")
        if kind == "txbody":
            element.text = encoded
            element.set("data-pptx-encoding", "base64")
            element.attrib.pop(TXBODY_REF_ATTRIBUTE, None)
        elif kind == "shape-style":
            element.set(SHAPE_STYLE_ATTRIBUTE, encoded)
            element.attrib.pop(SHAPE_STYLE_REF_ATTRIBUTE, None)
        else:
            element.set(CUSTOM_GEOMETRY_ATTRIBUTE, encoded)
            element.attrib.pop(CUSTOM_GEOMETRY_REF_ATTRIBUTE, None)
    return len(record_operations) + len(payload_operations)
