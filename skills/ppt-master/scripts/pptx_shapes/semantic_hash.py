#!/usr/bin/env python3
"""
PPT Master - Native Shape Semantic Fingerprints

Build stable hashes for visible SVG text, generated preset previews, and
native chart/table fallback subtrees.

Usage:
    Import the fingerprint helper for the relevant semantic carrier.

Examples:
    digest = svg_text_fingerprint(group_element)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import json
import re
from xml.etree import ElementTree as ET


_ROOT_TEXT_STYLE_ATTRS = frozenset({
    "class",
    "fill",
    "fill-opacity",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "opacity",
    "style",
    "text-anchor",
    "text-decoration",
    "word-spacing",
})

_TEXT_CONTRACT_ATTRS = frozenset({
    "data-pptx-text-mode",
    "data-pptx-text-bounds",
    "data-pptx-break",
    "data-pptx-join",
})

NATIVE_FALLBACK_SHA256_ATTR = "data-pptx-fallback-sha256"
_NATIVE_FALLBACK_IGNORED_TAGS = frozenset({"metadata", "title", "desc"})
_NATIVE_FALLBACK_IGNORED_ATTRS = frozenset({
    "id",
    "data-name",
    "data-ph-type",
})
_URL_ID_RE = re.compile(
    r"url\(\s*(?P<quote>['\"]?)#(?P<id>[^)'\"\s]+)(?P=quote)\s*\)",
    re.IGNORECASE,
)


def svg_text_fingerprint(root: ET.Element) -> str:
    """Hash text content, structure, positioning, and visible typography.

    Shape-level movement is intentionally excluded: the native ``a:xfrm``
    owns that change and the original ``p:txBody`` remains valid.  Text/tspan
    transforms and all their non-semantic attributes remain part of the hash.
    """

    payload = {
        "root_style": sorted(
            (name, value)
            for name, value in root.attrib.items()
            if name in _ROOT_TEXT_STYLE_ATTRS
        ),
        "text": [
            _element_payload(element)
            for element in root.iter()
            if _local_name(element.tag) == "text"
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def svg_preset_preview_fingerprint(root: ET.Element) -> str:
    """Hash the complete visible preview subtree and intermediate wrappers."""
    payload = _preview_subtree(root, is_root=True, active=False)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def svg_native_fallback_fingerprint(
    root: ET.Element,
    *,
    document_root: ET.Element | None = None,
) -> str:
    """Hash one native chart/table marker's rendering-relevant SVG subtree.

    Native metadata, editor/runtime attributes, and stable element IDs are not
    fallback artwork. Reachable document-level fragment definitions are hashed
    when ``document_root`` is available. Transforms remain part of the digest
    because complete explicit native bounds are absolute and therefore do not
    consume marker transforms; changing one must make the replacement stale.
    """
    id_tokens = _native_fallback_id_tokens(root)
    dependencies = _native_fallback_external_dependencies(
        root,
        document_root,
        id_tokens,
    )
    payload = _native_fallback_subtree(
        root,
        id_tokens=id_tokens,
    )
    if dependencies:
        payload = {
            "marker": payload,
            "external_dependencies": [
                {
                    "token": id_tokens[element_id],
                    "node": _native_fallback_subtree(
                        target,
                        id_tokens=id_tokens,
                        force_include=True,
                    ),
                }
                for element_id, target in dependencies
            ],
        }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def svg_native_fallback_markup_fingerprint(
    markup: str,
    *,
    root_transform: str | None = None,
    external_markup: str | None = None,
) -> str:
    """Hash an SVG fallback fragment through the canonical marker function."""
    if external_markup:
        document_root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            f"<defs>{external_markup}</defs><g>{markup}</g>"
            "</svg>"
        )
        wrapper = document_root[-1]
    else:
        document_root = None
        wrapper = ET.fromstring(
            '<g xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            f"{markup}"
            "</g>"
        )
    if root_transform:
        wrapper.set("transform", root_transform)
    return svg_native_fallback_fingerprint(
        wrapper,
        document_root=document_root,
    )


def resolve_preset_preview_hash(root: ET.Element) -> str | None:
    """Resolve and cross-check a logical preset group's fingerprint contract.

    The hash is duplicated on the logical group and hidden native carrier so
    stripping either copy cannot disable stale-preview detection.  A visible
    generated preview without either hash is invalid rather than legacy SVG.
    """
    has_preview = any(
        element.get("data-pptx-part")
        in {"geometry-preview", "geometry-detail"}
        for element in root.iter()
    )
    carrier_hashes = {
        value
        for element in root.iter()
        if element.get("data-pptx-part") == "geometry"
        and (value := element.get("data-pptx-preview-sha256")) is not None
    }
    group_hash = root.get("data-pptx-preview-sha256")
    if not has_preview and not carrier_hashes and group_hash is None:
        return None
    if len(carrier_hashes) > 1:
        raise ValueError("Native geometry carriers have inconsistent preview hashes")
    carrier_hash = next(iter(carrier_hashes), None)
    if (
        group_hash is not None
        and carrier_hash is not None
        and group_hash != carrier_hash
    ):
        raise ValueError("Logical group and native carrier preview hashes differ")
    expected = group_hash or carrier_hash
    if expected is None:
        raise ValueError("Generated preset preview is missing its fingerprint")
    return expected


def _preview_subtree(
    element: ET.Element,
    *,
    is_root: bool,
    active: bool,
) -> dict | None:
    part = element.get("data-pptx-part")
    contains_preview = part in {"geometry-preview", "geometry-detail"}
    child_active = active or contains_preview
    children = [
        payload
        for child in element
        if (
            payload := _preview_subtree(
                child,
                is_root=False,
                active=child_active,
            )
        ) is not None
    ]
    if is_root:
        return {"children": children}
    if not child_active and not children:
        return None
    return {
        "tag": _local_name(element.tag),
        "attrs": sorted(
            (name, value)
            for name, value in element.attrib.items()
            if name != "id"
            and name != "data-pptx-preview-sha256"
            and not name.startswith("data-pptx-runtime-")
            and name not in _TEXT_CONTRACT_ATTRS
        ),
        "children": children,
    }


def _native_fallback_subtree(
    element: ET.Element,
    *,
    id_tokens: dict[str, str],
    force_include: bool = False,
) -> dict | None:
    tag = _local_name(element.tag)
    if not force_include and _native_fallback_element_hidden(element):
        return None

    attrs = []
    for raw_name, raw_value in element.attrib.items():
        name = _local_name(raw_name)
        if name in _NATIVE_FALLBACK_IGNORED_ATTRS:
            continue
        if name.startswith("data-pptx-"):
            continue
        attrs.append((
            raw_name,
            _normalize_native_fallback_id_refs(name, raw_value, id_tokens),
        ))

    children = []
    for child in element:
        child_payload = _native_fallback_subtree(
            child,
            id_tokens=id_tokens,
        )
        if child_payload is None:
            continue
        entry = {"node": child_payload}
        if child.tail and (
            child.tail.strip() or tag in {"text", "tspan", "textPath"}
        ):
            entry["tail"] = child.tail
        children.append(entry)

    text = element.text or ""
    payload = {
        "tag": tag,
        "attrs": sorted(attrs),
        "children": children,
    }
    if text and (text.strip() or tag in {"text", "tspan", "textPath", "style"}):
        payload["text"] = text
    return payload


def _native_fallback_id_tokens(
    root: ET.Element,
) -> dict[str, str]:
    tokens: dict[str, str] = {}

    def visit(
        element: ET.Element,
        *,
        is_root: bool,
        path: tuple[int, ...],
    ) -> None:
        element_id = None if is_root else element.get("id")
        if element_id and element_id not in tokens:
            tokens[element_id] = "native-node-" + "-".join(map(str, path))
        canonical_index = 0
        for child in element:
            if _native_fallback_element_hidden(child):
                continue
            visit(
                child,
                is_root=False,
                path=(*path, canonical_index),
            )
            canonical_index += 1

    visit(root, is_root=True, path=())
    return tokens


def _native_fallback_external_dependencies(
    marker: ET.Element,
    document_root: ET.Element | None,
    id_tokens: dict[str, str],
) -> list[tuple[str, ET.Element]]:
    """Resolve the marker's reachable document-level fragment references."""
    if document_root is None or document_root is marker:
        return []

    marker_nodes = set(marker.iter())
    targets: dict[str, ET.Element] = {}
    for element in document_root.iter():
        element_id = element.get("id")
        if element_id and element_id not in targets:
            targets[element_id] = element

    dependencies: list[tuple[str, ET.Element]] = []

    def add_reference(element_id: str) -> None:
        if not element_id or element_id in id_tokens:
            return
        target = targets.get(element_id)
        if target is None or target in marker_nodes:
            return
        id_tokens[element_id] = f"native-external-{len(dependencies) + 1}"
        dependencies.append((element_id, target))
        for nested_id in _native_fallback_fragment_references(
            target,
            force_include_root=True,
        ):
            add_reference(nested_id)

    for element_id in _native_fallback_fragment_references(marker):
        add_reference(element_id)
    return dependencies


def _native_fallback_fragment_references(
    root: ET.Element,
    *,
    force_include_root: bool = False,
) -> list[str]:
    references: list[str] = []
    seen: set[str] = set()

    def add(element_id: str) -> None:
        if element_id and element_id not in seen:
            seen.add(element_id)
            references.append(element_id)

    def visit(element: ET.Element, *, force_include: bool) -> None:
        if not force_include and _native_fallback_element_hidden(element):
            return
        for raw_name, raw_value in sorted(element.attrib.items()):
            name = _local_name(raw_name)
            if name in _NATIVE_FALLBACK_IGNORED_ATTRS:
                continue
            if name.startswith("data-pptx-"):
                continue
            for match in _URL_ID_RE.finditer(raw_value):
                add(match.group("id"))
            if name == "href" and raw_value.startswith("#"):
                add(raw_value[1:])
        for child in element:
            visit(child, force_include=False)

    visit(root, force_include=force_include_root)
    return references


def _native_fallback_element_hidden(element: ET.Element) -> bool:
    if _local_name(element.tag) in _NATIVE_FALLBACK_IGNORED_TAGS:
        return True
    # ``display:none`` suppresses the entire descendant subtree.  SVG
    # ``visibility`` is different: a descendant may explicitly restore
    # ``visibility:visible``.  Keep visibility-hidden content in the digest
    # conservatively so such visible descendants cannot evade stale detection.
    return _native_fallback_style_value(element, "display") == "none"


def _normalize_native_fallback_id_refs(
    name: str,
    value: str,
    id_tokens: dict[str, str],
) -> str:
    def replace_url(match: re.Match[str]) -> str:
        token = id_tokens.get(match.group("id"))
        return f"url(#{token})" if token is not None else match.group(0)

    normalized = _URL_ID_RE.sub(replace_url, value)
    if name in {"href", "xlink:href"} and normalized.startswith("#"):
        token = id_tokens.get(normalized[1:])
        if token is not None:
            return f"#{token}"
    return normalized


def _native_fallback_style_value(element: ET.Element, name: str) -> str | None:
    raw = element.get(name)
    if raw is not None:
        return raw.strip().lower()
    style = element.get("style") or ""
    for declaration in style.split(";"):
        if ":" not in declaration:
            continue
        key, value = declaration.split(":", 1)
        if key.strip().lower() == name:
            return value.strip().lower()
    return None


def _element_payload(element: ET.Element) -> dict:
    return {
        "tag": _local_name(element.tag),
        "attrs": sorted(
            (name, value)
            for name, value in element.attrib.items()
            if name != "id"
            and (
                not name.startswith("data-pptx-")
                or name in _TEXT_CONTRACT_ATTRS
            )
        ),
        "text": element.text or "",
        "children": [
            {
                "node": _element_payload(child),
                "tail": child.tail or "",
            }
            for child in element
            if _local_name(child.tag) in {"text", "tspan"}
        ],
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
