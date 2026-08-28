#!/usr/bin/env python3
"""
PPT Master - SVG Authoring View

Create a lightweight, non-destructive editable IR from PPTX-imported SVG
files. The source SVG remains the native-payload authority; the authoring copy
translates recognized shapes and tables into compact semantic components,
keeps stable source references, and omits bulky import-only/render-duplicate
payloads.

Usage:
    python3 scripts/svg_authoring_view.py <svg-file-or-directory> \
        -o <output-dir> --projection-kind <kind>

Examples:
    python3 scripts/svg_authoring_view.py analysis/source_svg_import/svg \
        -o analysis/authoring-svg --projection-kind layered
    python3 scripts/svg_authoring_view.py imported/slide_06.svg \
        -o /tmp/slide-authoring-view --projection-kind generic

Dependencies:
    None (standard library only).

The output directory is an authoring bundle: editable SVGs plus one
model-readable `authoring_summary.json` and one tool-only
`authoring_manifest.json` provenance sidecar. Layered IR remains the
template-creation input; final templates are materialized from it. A flat
authoring bundle at ``authoring-svg-flat/`` is the sole editable source for
``svg_to_pptx.py --roundtrip``. Directory runs prepare and stage the
complete batch before publishing it, so a failed page leaves the existing
destination set unchanged.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from compact_svg_coordinates import compact_svg_tree
from console_encoding import configure_utf8_stdio
from native_payloads import (
    CUSTOM_GEOMETRY_ATTRIBUTE,
    CUSTOM_GEOMETRY_REF_ATTRIBUTE,
    NATIVE_RECORD_REF_ATTRIBUTE,
    SHAPE_STYLE_ATTRIBUTE,
    SHAPE_STYLE_REF_ATTRIBUTE,
    TXBODY_REF_ATTRIBUTE,
)
from pptx_shapes import (
    NATIVE_FALLBACK_SHA256_ATTR,
    svg_native_fallback_fingerprint,
)
from svg_compatibility import normalize_single_child_group_filters
from svg_authoring_contract import (
    canonical_authoring_errors,
    normalize_compact_authoring_tree,
)
from svg_to_pptx.drawingml.context import IDENTITY_MATRIX
from svg_to_pptx.drawingml.utils import (
    INHERITABLE_ATTRS,
    matrix_multiply,
    parse_inline_style,
    parse_opacity,
    parse_transform_matrix,
)

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
AUTHORING_MANIFEST_NAME = "authoring_manifest.json"
AUTHORING_SUMMARY_NAME = "authoring_summary.json"
AUTHORING_SCHEMA = "ppt-master.svg-authoring-ir.v1"
AUTHORING_SUMMARY_SCHEMA = "ppt-master.svg-authoring-summary.v1"
SOURCE_REF_ATTRIBUTE = "data-pptx-source-ref"
SOURCE_PROXY_ATTRIBUTE = "data-pptx-source-proxy"
SOURCE_PROXY_KIND = "native-restore"
EXTERNAL_LINKED_IMAGE_PROXY_ATTRIBUTE = (
    "data-pptx-external-linked-image-proxy"
)
SEMANTIC_OBJECT_ATTRIBUTE = "data-pptx-semantic-object"
SEMANTIC_SHAPE_KIND = "shape"
SEMANTIC_TABLE_KIND = "table"
# Keep ordinary text and vectors inline. Large semantic/native payload objects
# that cannot move to an editable vector asset become atomic source proxies.
SOURCE_PROXY_MIN_BYTES = 4096
_SEMANTIC_CONTENT_TAGS = frozenset({"foreignObject", "text", "tspan"})
_SEMANTIC_AUTHORING_ATTRIBUTES = frozenset({
    "data-pptx-inline-formula",
    "data-pptx-page-role",
    "data-pptx-placeholder",
    "data-pptx-replace-with",
    "data-pptx-role",
    "data-pptx-shape-hyperlink",
    SEMANTIC_OBJECT_ATTRIBUTE,
})
_DRAWABLE_TAGS = frozenset({
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
})
_SEMANTIC_CARRIER_OWNER_ATTRIBUTES = frozenset({
    "data-pptx-frame",
    "data-pptx-geometry-kind",
    "data-pptx-object",
    "data-pptx-prst",
})
_URL_ID_RE = re.compile(r"url\(\s*(['\"]?)#([^)'\"\s]+)\1\s*\)")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def _serialize_svg(element: ET.Element) -> bytes:
    """Serialize SVG independently of namespace registrations from other tools."""
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    return ET.tostring(element, encoding="utf-8", xml_declaration=False)

# These fields identify source OOXML objects or carry opaque paint/effect
# payloads. They belong in the complete import SVG, not its lightweight view.
AUTHORING_OMITTED_SOURCE_ATTRIBUTES = {
    "data-name",
    "data-pptx-effect-ooxml",
    "data-pptx-effect-ooxml-sha256",
    "data-pptx-effect-reason",
    "data-pptx-effect-status",
    "data-pptx-gradient-ooxml",
    "data-pptx-gradient-ooxml-sha256",
    "data-pptx-gradient-preview-sha256",
    "data-pptx-custgeom",
    "data-pptx-geometry-sha256",
    "data-pptx-preview-sha256",
    NATIVE_FALLBACK_SHA256_ATTR,
    "data-pptx-roundtrip-object",
    "data-pptx-shape-id",
    "data-pptx-shape-name",
    "data-pptx-shape-scope",
    "data-pptx-shape-style",
}

ADOPT_OBJECT_STRIPPED_ATTRIBUTES = frozenset(
    AUTHORING_OMITTED_SOURCE_ATTRIBUTES
    | {
        SOURCE_REF_ATTRIBUTE,
        SOURCE_PROXY_ATTRIBUTE,
        NATIVE_RECORD_REF_ATTRIBUTE,
        TXBODY_REF_ATTRIBUTE,
        SHAPE_STYLE_ATTRIBUTE,
        SHAPE_STYLE_REF_ATTRIBUTE,
        CUSTOM_GEOMETRY_ATTRIBUTE,
        CUSTOM_GEOMETRY_REF_ATTRIBUTE,
        "data-pptx-encoding",
        "data-pptx-ooxml-sha256",
        "data-pptx-part",
        "data-pptx-text-sha256",
    }
)

_TSPAN_INHERITED_ATTRIBUTES = frozenset({
    "fill",
    "fill-opacity",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "stroke",
    "stroke-opacity",
    "text-anchor",
    "text-decoration",
})
_ADOPT_INHERITED_ATTRIBUTES = tuple(INHERITABLE_ATTRS)

# Compact native-shape intent is intentionally not in the removal set:
# data-pptx-object, data-pptx-prst, and data-pptx-frame remain useful while
# reviewing the visible fallback. Structural markers also pass through
# unchanged; the IR records identity but never decides payload-restoration
# policy.


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


@dataclass
class SourceReference:
    source_ref: str
    source_path: tuple[int, ...]
    initial_authoring_subtree_sha256: str | None = None
    representation: str = "inline"
    proxy_asset: Path | None = None
    proxy_asset_sha256: str | None = None

    def as_dict(self, output_dir: Path) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_path": list(self.source_path),
            "initial_authoring_subtree_sha256": self.initial_authoring_subtree_sha256,
            "representation": self.representation,
        }
        if self.representation == "source-proxy":
            if self.proxy_asset is None or self.proxy_asset_sha256 is None:
                raise ValueError(
                    f"Source proxy {self.source_ref} has no immutable asset record"
                )
            payload["proxy_asset"] = _portable_path(self.proxy_asset, output_dir)
            payload["proxy_asset_sha256"] = self.proxy_asset_sha256
        return payload


def _semantic_text(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value


def _stable_tag_name(tag: object) -> str:
    if isinstance(tag, str):
        return tag
    if tag is ET.Comment:
        return "#comment"
    if tag is ET.ProcessingInstruction:
        return "#processing-instruction"
    raise ValueError(f"Unsupported XML node type in source object: {tag!r}")


def semantic_subtree_sha256(
    element: ET.Element,
    *,
    ignored_attributes: frozenset[str] = frozenset(),
) -> str:
    """Hash parsed SVG semantics without attribute order or indentation noise."""
    digest = hashlib.sha256()

    def visit(item: ET.Element) -> None:
        digest.update(_stable_tag_name(item.tag).encode("utf-8"))
        for name, value in sorted(item.attrib.items()):
            if name in ignored_attributes:
                continue
            digest.update(b"\0a")
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(value.encode("utf-8"))
        text = _semantic_text(item.text)
        if text is not None:
            digest.update(b"\0t")
            digest.update(text.encode("utf-8"))
        for child in item:
            digest.update(b"\0c")
            visit(child)
            tail = _semantic_text(child.tail)
            if tail is not None:
                digest.update(b"\0l")
                digest.update(tail.encode("utf-8"))
        digest.update(b"\0e")

    visit(element)
    return digest.hexdigest()


def _iter_element_paths(
    root: ET.Element,
) -> list[tuple[tuple[int, ...], ET.Element]]:
    indexed: list[tuple[tuple[int, ...], ET.Element]] = []

    def walk(element: ET.Element, path: tuple[int, ...]) -> None:
        indexed.append((path, element))
        for index, child in enumerate(element):
            walk(child, (*path, index))

    walk(root, ())
    return indexed


def _source_reference(element: ET.Element) -> str | None:
    if not element.get("id") or not element.get("data-pptx-object"):
        return None
    scope = element.get("data-pptx-shape-scope")
    shape_id = element.get("data-pptx-shape-id")
    if not scope or not shape_id:
        return None
    return f"{scope}:{shape_id}"


def _stamp_source_references(root: ET.Element) -> list[SourceReference]:
    existing = [
        element
        for _, element in _iter_element_paths(root)
        if element.get(SOURCE_REF_ATTRIBUTE) is not None
    ]
    if existing:
        raise ValueError(
            f"Input already contains reserved {SOURCE_REF_ATTRIBUTE}; "
            "project from the lossless import SVG instead"
        )

    references: list[SourceReference] = []
    seen: set[str] = set()
    for path, element in _iter_element_paths(root):
        source_ref = _source_reference(element)
        if source_ref is None:
            continue
        if source_ref in seen:
            raise ValueError(f"Duplicate source object identity: {source_ref}")
        seen.add(source_ref)
        references.append(
            SourceReference(
                source_ref=source_ref,
                source_path=path,
            )
        )
        element.set(SOURCE_REF_ATTRIBUTE, source_ref)
    return references


def _index_initial_authoring_references(
    root: ET.Element,
    references: list[SourceReference],
) -> None:
    by_ref = {reference.source_ref: reference for reference in references}
    seen: set[str] = set()
    for element in root.iter():
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if source_ref is None:
            continue
        if source_ref in seen:
            raise ValueError(f"Duplicate authoring source reference: {source_ref}")
        reference = by_ref.get(source_ref)
        if reference is None:
            raise ValueError(f"Unknown authoring source reference: {source_ref}")
        seen.add(source_ref)
        reference.initial_authoring_subtree_sha256 = semantic_subtree_sha256(
            element,
            ignored_attributes=frozenset({SOURCE_REF_ATTRIBUTE}),
        )

    missing = sorted(set(by_ref) - seen)
    if missing:
        raise ValueError(
            "Authoring projection dropped source-referenced object(s): "
            + ", ".join(missing[:5])
        )


def _fresh_native_fallback_markers(root: ET.Element) -> set[ET.Element]:
    """Return native markers whose source fallback guard is currently valid."""
    fresh: set[ET.Element] = set()
    for element in root.iter():
        expected = element.get(NATIVE_FALLBACK_SHA256_ATTR)
        if (
            expected is None
            or expected != expected.strip()
            or _SHA256_RE.fullmatch(expected) is None
        ):
            continue
        if svg_native_fallback_fingerprint(
            element,
            document_root=root,
        ) == expected.lower():
            fresh.add(element)
    return fresh


@dataclass
class ProjectionStats:
    txbody_metadata: int = 0
    hidden_geometry_carriers: int = 0
    geometry_preview_wrappers: int = 0
    geometry_detail_markers: int = 0
    compatibility_normalizations: int = 0
    asset_references_rewritten: int = 0
    coordinate_attributes_compacted: int = 0
    style_declarations_compacted: int = 0
    inherited_text_attributes_compacted: int = 0
    single_tspans_collapsed: int = 0
    source_object_proxies: int = 0
    source_object_proxy_bytes: int = 0
    semantic_shapes: int = 0
    semantic_tables: int = 0
    semantic_table_preview_bytes: int = 0
    unused_definitions_pruned: int = 0
    source_attributes: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict[str, object]:
        return {
            "txbody_metadata": self.txbody_metadata,
            "hidden_geometry_carriers": self.hidden_geometry_carriers,
            "geometry_preview_wrappers": self.geometry_preview_wrappers,
            "geometry_detail_markers": self.geometry_detail_markers,
            "compatibility_normalizations": self.compatibility_normalizations,
            "source_attributes": dict(sorted(self.source_attributes.items())),
            "asset_references_rewritten": self.asset_references_rewritten,
            "coordinate_attributes_compacted": self.coordinate_attributes_compacted,
            "style_declarations_compacted": self.style_declarations_compacted,
            "inherited_text_attributes_compacted": (
                self.inherited_text_attributes_compacted
            ),
            "single_tspans_collapsed": self.single_tspans_collapsed,
            "source_object_proxies": self.source_object_proxies,
            "source_object_proxy_bytes": self.source_object_proxy_bytes,
            "semantic_shapes": self.semantic_shapes,
            "semantic_tables": self.semantic_tables,
            "semantic_table_preview_bytes": self.semantic_table_preview_bytes,
            "unused_definitions_pruned": self.unused_definitions_pruned,
        }

    def merge(self, other: "ProjectionStats") -> None:
        self.txbody_metadata += other.txbody_metadata
        self.hidden_geometry_carriers += other.hidden_geometry_carriers
        self.geometry_preview_wrappers += other.geometry_preview_wrappers
        self.geometry_detail_markers += other.geometry_detail_markers
        self.compatibility_normalizations += other.compatibility_normalizations
        self.asset_references_rewritten += other.asset_references_rewritten
        self.coordinate_attributes_compacted += (
            other.coordinate_attributes_compacted
        )
        self.style_declarations_compacted += other.style_declarations_compacted
        self.inherited_text_attributes_compacted += (
            other.inherited_text_attributes_compacted
        )
        self.single_tspans_collapsed += other.single_tspans_collapsed
        self.source_object_proxies += other.source_object_proxies
        self.source_object_proxy_bytes += other.source_object_proxy_bytes
        self.semantic_shapes += other.semantic_shapes
        self.semantic_tables += other.semantic_tables
        self.semantic_table_preview_bytes += other.semantic_table_preview_bytes
        self.unused_definitions_pruned += other.unused_definitions_pruned
        self.source_attributes.update(other.source_attributes)


@dataclass
class ProjectionReport:
    source: Path
    output: Path
    original_bytes: int
    projected_bytes: int
    stats: ProjectionStats
    source_sha256: str
    initial_authoring_sha256: str
    source_references: list[SourceReference]

    def as_dict(self) -> dict[str, object]:
        saved = self.original_bytes - self.projected_bytes
        reduction = (saved / self.original_bytes * 100) if self.original_bytes else 0.0
        return {
            "source": str(self.source),
            "output": str(self.output),
            "original_bytes": self.original_bytes,
            "projected_bytes": self.projected_bytes,
            "bytes_saved": saved,
            "reduction_percent": round(reduction, 2),
            "source_sha256": self.source_sha256,
            "initial_authoring_sha256": self.initial_authoring_sha256,
            "source_ref_count": len(self.source_references),
            "removed": self.stats.as_dict(),
        }


def _is_hidden_geometry_carrier(element: ET.Element) -> bool:
    if element.get("data-pptx-part") != "geometry":
        return False
    visibility = (element.get("visibility") or "").strip().lower()
    display = (element.get("display") or "").strip().lower()
    style = (element.get("style") or "").replace(" ", "").lower()
    return (
        visibility == "hidden"
        or display == "none"
        or "visibility:hidden" in style
        or "display:none" in style
    )


def _is_semantic_shape_candidate(element: ET.Element) -> bool:
    if (
        _local_name(element.tag) != "g"
        or element.get("data-pptx-object") not in {"shape", "connector"}
        or (
            element.get("data-pptx-prst") is None
            and element.get("data-pptx-geometry-kind") != "custom"
        )
    ):
        return False
    if any(
        name in element.attrib
        for name in (
            "data-pptx-placeholder",
            "data-pptx-placeholder-type",
            "data-pptx-placeholder-idx",
        )
    ):
        return False
    if any(
        item.get("data-pptx-effect-status") == "unsupported"
        or item.get("data-pptx-effect-ooxml") is not None
        for item in element.iter()
    ):
        return False
    carriers = [
        child
        for child in element
        if child.get("data-pptx-part") == "geometry"
        and _local_name(child.tag) in _DRAWABLE_TAGS
    ]
    if len(carriers) != 1:
        return False
    visible_texts = [
        item
        for item in element.iter()
        if _local_name(item.tag) == "text"
    ]
    if any(text not in list(element) for text in visible_texts):
        return False
    if any(
        item.get("data-pptx-inline-formula") is not None
        for text in visible_texts
        for item in text.iter()
    ):
        return False
    positional_texts = [
        text
        for text in visible_texts
        if any(
            _local_name(item.tag) == "tspan"
            and any(item.get(name) is not None for name in ("x", "y", "dy"))
            for item in text.iter()
        )
    ]
    if len(visible_texts) > 1 and positional_texts:
        return False
    for text in positional_texts:
        try:
            if not _normalize_semantic_text_lines(copy.deepcopy(text)):
                return False
        except ValueError:
            return False
    if element.get("data-pptx-object") == "connector" and visible_texts:
        return False
    if len(visible_texts) > 1:
        if any(text.get("transform") is not None for text in visible_texts):
            return False
        anchors = {
            (item.get("x"), item.get("text-anchor", "start"))
            for item in visible_texts
        }
        if len(anchors) != 1:
            return False
        try:
            baselines = [_semantic_text_baseline(text) for text in visible_texts]
        except ValueError:
            return False
        if any(current <= previous for previous, current in zip(
            baselines,
            baselines[1:],
        )):
            return False
    for child in element:
        tag = _local_name(child.tag)
        part = child.get("data-pptx-part")
        if child is carriers[0] or tag in {"metadata", "text", "a"}:
            continue
        if part in {"geometry-preview", "placeholder-sppr"}:
            continue
        if tag == "g" and all(
            _local_name(item.tag) in {"g", "text", "tspan", "a"}
            for item in child.iter()
        ):
            continue
        return False
    return True


def _mark_semantic_objects(root: ET.Element, stats: ProjectionStats) -> None:
    """Mark source objects whose authoring truth has a closed semantic IR."""
    for element in root.iter():
        if element.get("data-pptx-replace-with") == SEMANTIC_TABLE_KIND:
            element.set(SEMANTIC_OBJECT_ATTRIBUTE, SEMANTIC_TABLE_KIND)
            stats.semantic_tables += 1
            continue
        if _is_semantic_shape_candidate(element):
            element.set(SEMANTIC_OBJECT_ATTRIBUTE, SEMANTIC_SHAPE_KIND)
            stats.semantic_shapes += 1


def _make_geometry_carrier_visible(element: ET.Element) -> int:
    """Turn one import-only hidden carrier into the authored geometry surface."""
    changed = 0
    for name in ("visibility", "display", "pointer-events"):
        if name in element.attrib:
            del element.attrib[name]
            changed += 1

    style = element.get("style")
    if style is not None:
        declarations = [
            declaration.strip()
            for declaration in style.split(";")
            if declaration.strip()
        ]
        retained = [
            declaration
            for declaration in declarations
            if declaration.split(":", 1)[0].strip().lower()
            not in {"display", "pointer-events", "visibility"}
        ]
        normalized = "; ".join(retained)
        if normalized:
            if normalized != style:
                element.set("style", normalized)
                changed += 1
        else:
            del element.attrib["style"]
            changed += 1
    return changed


def _semantic_text_baseline(element: ET.Element) -> float:
    raw = element.get("y")
    if raw is None:
        raise ValueError("Semantic shape text requires an explicit y baseline")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"Semantic shape text has a non-numeric y baseline: {raw!r}"
        ) from exc
    if not math.isfinite(value):
        raise ValueError(
            f"Semantic shape text has a non-finite y baseline: {raw!r}"
        )
    return value


def _semantic_text_font_size(element: ET.Element) -> float:
    raw = element.get("font-size")
    if raw is None:
        return 16.0
    try:
        value = float(raw)
    except ValueError:
        return 16.0
    return value if math.isfinite(value) and value > 0 else 16.0


def _semantic_text_has_content(element: ET.Element) -> bool:
    return bool("".join(element.itertext()))


def _normalize_semantic_text_lines(text: ET.Element) -> bool:
    """Lower compatible positioned tspans into one semantic line model."""
    positional = [
        child
        for child in text
        if _local_name(child.tag) == "tspan"
        and any(child.get(name) is not None for name in ("x", "y", "dy"))
    ]
    if not positional:
        return False

    parent_x = text.get("x")
    advances: list[float] = []
    for child in positional:
        if child.get("y") is not None:
            raise ValueError(
                "Semantic shape text cannot normalize an absolute tspan y"
            )
        child_x = child.get("x")
        if child_x is not None and child_x != parent_x:
            raise ValueError(
                "Semantic shape text cannot normalize a tspan x jump"
            )
        raw_dy = child.get("dy")
        try:
            advance = float(raw_dy or "0")
        except ValueError as exc:
            raise ValueError(
                f"Semantic shape text has a non-numeric tspan dy: {raw_dy!r}"
            ) from exc
        if not math.isfinite(advance) or advance <= 0:
            raise ValueError(
                f"Semantic shape text requires a positive finite tspan dy: {raw_dy!r}"
            )
        advances.append(advance)

    first_line = ET.Element(f"{{{SVG_NS}}}tspan")
    first_line.text = text.text
    lines: list[ET.Element] = [first_line]
    current = first_line
    for child in list(text):
        clone = copy.deepcopy(child)
        if child in positional:
            for name in ("x", "y", "dy"):
                clone.attrib.pop(name, None)
            clone.set("data-paragraph-line-break", "1")
            lines.append(clone)
            current = clone
            continue
        current.append(clone)

    lines = [line for line in lines if _semantic_text_has_content(line)]
    if len(lines) < 2:
        return False
    for child in list(text):
        text.remove(child)
    text.text = None
    text.set("data-pptx-text-model", "lines")
    line_height = min(advances)
    text.set(
        "data-paragraph-line-height",
        f"{line_height:.6f}".rstrip("0").rstrip("."),
    )
    for line in lines:
        text.append(line)
    return True


def _semantic_paragraph_from_text(
    source: ET.Element,
    parent: ET.Element,
    *,
    space_before: float,
) -> ET.Element:
    """Wrap one rendered SVG text line as one semantic paragraph run tree."""
    paragraph = ET.Element(f"{{{SVG_NS}}}tspan")
    presentation_attributes = _TSPAN_INHERITED_ATTRIBUTES | {
        "baseline-shift",
        "opacity",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-width",
        "style",
    }
    for name in presentation_attributes:
        value = source.get(name)
        if value is not None and value != parent.get(name):
            paragraph.set(name, value)
    if space_before > 0:
        paragraph.set(
            "data-paragraph-space-before",
            f"{space_before:.6f}".rstrip("0").rstrip("."),
        )
    paragraph.text = source.text
    for child in source:
        paragraph.append(copy.deepcopy(child))
    return paragraph


def _merge_semantic_shape_texts(
    shape: ET.Element,
    texts: list[ET.Element],
) -> ET.Element:
    """Represent multiple rendered text rows as one paragraph-based text body."""
    baselines = [_semantic_text_baseline(text) for text in texts]
    positive_advances = [
        current - previous
        for previous, current in zip(baselines, baselines[1:])
        if current > previous
    ]
    line_height = _semantic_text_font_size(texts[0]) * 1.5
    if positive_advances:
        line_height = min(line_height, min(positive_advances))
    line_height = max(line_height, 1.0)

    combined = copy.deepcopy(texts[0])
    for child in list(combined):
        combined.remove(child)
    combined.text = None
    combined.set("data-pptx-text-model", "paragraphs")
    combined.set(
        "data-paragraph-line-height",
        f"{line_height:.6f}".rstrip("0").rstrip("."),
    )
    previous_baseline = baselines[0]
    for index, (source, baseline) in enumerate(zip(texts, baselines)):
        space_before = (
            0.0
            if index == 0
            else max(0.0, baseline - previous_baseline - line_height)
        )
        combined.append(
            _semantic_paragraph_from_text(
                source,
                combined,
                space_before=space_before,
            )
        )
        previous_baseline = baseline

    siblings = list(shape)
    first_index = siblings.index(texts[0])
    for text in texts:
        shape.remove(text)
    shape.insert(first_index, combined)
    return combined


def _compact_semantic_shapes(root: ET.Element, stats: ProjectionStats) -> None:
    """Collapse each semantic shape to one geometry carrier and one text body."""
    for shape in root.iter():
        if shape.get(SEMANTIC_OBJECT_ATTRIBUTE) != SEMANTIC_SHAPE_KIND:
            continue
        carriers = [
            child
            for child in shape
            if child.get("data-pptx-part") == "geometry"
            and _local_name(child.tag) in _DRAWABLE_TAGS
        ]
        if len(carriers) != 1:
            raise ValueError("Semantic shape requires exactly one geometry carrier")
        carrier = carriers[0]
        stats.compatibility_normalizations += _make_geometry_carrier_visible(carrier)
        for name in list(carrier.attrib):
            if (
                name not in _SEMANTIC_CARRIER_OWNER_ATTRIBUTES
                and not name.startswith("data-pptx-av-")
            ):
                continue
            owner_value = shape.get(name)
            if owner_value is None or owner_value != carrier.get(name):
                raise ValueError(
                    f"Semantic shape owner/carrier values differ for {name}"
                )
            carrier.attrib.pop(name, None)
            stats.compatibility_normalizations += 1

        direct_texts = [
            child for child in shape
            if _local_name(child.tag) == "text"
        ]
        all_texts = [
            item for item in shape.iter()
            if _local_name(item.tag) == "text"
        ]
        for text in direct_texts:
            if _normalize_semantic_text_lines(text):
                stats.compatibility_normalizations += 1
        if len(all_texts) > 1:
            if direct_texts != all_texts:
                raise ValueError(
                    "Multi-paragraph semantic shape text must be direct children"
                )
            _merge_semantic_shape_texts(shape, direct_texts)

        for child in list(shape):
            if child is carrier:
                continue
            tag = _local_name(child.tag)
            part = child.get("data-pptx-part")
            if tag in _DRAWABLE_TAGS or part in {
                "geometry-detail",
                "geometry-preview",
            }:
                _remove_child(shape, child)
                stats.compatibility_normalizations += 1


def _append_tail(parent: ET.Element, index: int, tail: str | None) -> None:
    if not tail:
        return
    if index > 0:
        previous = list(parent)[index - 1]
        previous.tail = (previous.tail or "") + tail
    else:
        parent.text = (parent.text or "") + tail


def _remove_child(parent: ET.Element, child: ET.Element) -> None:
    children = list(parent)
    index = children.index(child)
    tail = child.tail
    parent.remove(child)
    _append_tail(parent, index, tail)


def _unwrap_preview(parent: ET.Element, wrapper: ET.Element) -> bool:
    """Promote a marker-only preview wrapper without changing its geometry."""
    if wrapper.attrib or (wrapper.text and wrapper.text.strip()):
        return False

    siblings = list(parent)
    index = siblings.index(wrapper)
    promoted = list(wrapper)
    wrapper_tail = wrapper.tail
    for child in promoted:
        wrapper.remove(child)
    parent.remove(wrapper)

    for offset, child in enumerate(promoted):
        parent.insert(index + offset, child)

    if promoted:
        promoted[-1].tail = (promoted[-1].tail or "") + (wrapper_tail or "")
    else:
        _append_tail(parent, index, wrapper_tail)
    return True


def _strip_import_attributes(element: ET.Element, stats: ProjectionStats) -> None:
    for name in list(element.attrib):
        if name not in AUTHORING_OMITTED_SOURCE_ATTRIBUTES:
            continue
        stats.source_attributes[name] += 1
        del element.attrib[name]


def _compact_text_runs(root: ET.Element, stats: ProjectionStats) -> None:
    """Remove redundant run paint while preserving directly editable text."""
    for text in root.iter():
        if _local_name(text.tag) != "text":
            continue
        for span in list(text):
            if _local_name(span.tag) != "tspan":
                continue
            for name in list(span.attrib):
                if (
                    name in _TSPAN_INHERITED_ATTRIBUTES
                    and span.get(name) == text.get(name)
                ):
                    del span.attrib[name]
                    stats.inherited_text_attributes_compacted += 1

        if len(text) != 1:
            continue
        span = text[0]
        if (
            _local_name(span.tag) != "tspan"
            or span.attrib
            or len(span)
            or text.text not in {None, ""}
            or span.tail not in {None, ""}
        ):
            continue
        text.text = span.text
        text.remove(span)
        stats.single_tspans_collapsed += 1


def _project_subtree(parent: ET.Element, stats: ProjectionStats) -> None:
    for child in list(parent):
        part = child.get("data-pptx-part")
        tag = _local_name(child.tag)

        if tag == "metadata" and part == "txbody":
            stats.txbody_metadata += 1
            _remove_child(parent, child)
            continue

        if (
            _is_hidden_geometry_carrier(child)
            and parent.get(SEMANTIC_OBJECT_ATTRIBUTE) != SEMANTIC_SHAPE_KIND
        ):
            stats.hidden_geometry_carriers += 1
            _remove_child(parent, child)
            continue

        _project_subtree(child, stats)
        _strip_import_attributes(child, stats)

        if part == "geometry-preview":
            child.attrib.pop("data-pptx-part", None)
            stats.compatibility_normalizations += len(
                normalize_single_child_group_filters(child)
            )
            if _unwrap_preview(parent, child):
                stats.geometry_preview_wrappers += 1
        elif part == "geometry-detail":
            child.attrib.pop("data-pptx-part", None)
            stats.geometry_detail_markers += 1


def _rewrite_asset_reference(value: str, source_dir: Path, output_dir: Path) -> str:
    if not value or value.startswith("#"):
        return value
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return value

    resolved = (source_dir / parsed.path).resolve()
    try:
        relative = os.path.relpath(resolved, output_dir).replace(os.sep, "/")
    except ValueError:
        relative = resolved.as_uri()
    return urlunsplit(("", "", relative, parsed.query, parsed.fragment))


def _rewrite_asset_references(
    root: ET.Element,
    source_dir: Path,
    output_dir: Path,
    stats: ProjectionStats,
) -> None:
    for element in root.iter():
        for name in ("href", f"{{{XLINK_NS}}}href"):
            current = element.get(name)
            if current is None:
                continue
            rewritten = _rewrite_asset_reference(current, source_dir, output_dir)
            if rewritten != current:
                element.set(name, rewritten)
                stats.asset_references_rewritten += 1


def _definition_references(element: ET.Element) -> set[str]:
    references: set[str] = set()
    for item in element.iter():
        for name, value in item.attrib.items():
            references.update(match.group(2) for match in _URL_ID_RE.finditer(value))
            if _local_name(name) == "href" and value.startswith("#"):
                references.add(value[1:])
        if item.text:
            references.update(
                match.group(2) for match in _URL_ID_RE.finditer(item.text)
            )
    return references


def _definition_closure(
    root: ET.Element,
    content: list[ET.Element],
) -> tuple[list[ET.Element], set[int]]:
    definitions = [
        child for child in root
        if _local_name(child.tag) == "defs"
    ]
    owner_by_id: dict[str, ET.Element] = {}
    for definitions_root in definitions:
        for child in definitions_root:
            for item in child.iter():
                definition_id = item.get("id")
                if definition_id:
                    owner_by_id.setdefault(definition_id, child)

    required_ids: set[str] = set()
    pending = [
        reference
        for element in content
        for reference in _definition_references(element)
    ]
    selected_owners: set[int] = set()
    while pending:
        definition_id = pending.pop()
        if definition_id in required_ids:
            continue
        required_ids.add(definition_id)
        owner = owner_by_id.get(definition_id)
        if owner is None or id(owner) in selected_owners:
            continue
        selected_owners.add(id(owner))
        pending.extend(_definition_references(owner) - required_ids)
    return definitions, selected_owners


def _selected_definitions(
    root: ET.Element,
    content: list[ET.Element],
) -> list[ET.Element]:
    definitions, selected_owners = _definition_closure(root, content)
    selected: list[ET.Element] = []
    for definitions_root in definitions:
        clone = ET.Element(definitions_root.tag, dict(definitions_root.attrib))
        clone.text = definitions_root.text
        for child in definitions_root:
            always_keep = _local_name(child.tag) == "style" or not child.get("id")
            if always_keep or id(child) in selected_owners:
                clone.append(copy.deepcopy(child))
        if list(clone) or (clone.text and clone.text.strip()):
            selected.append(clone)
    return selected


def _prune_unreferenced_definitions(
    root: ET.Element,
    stats: ProjectionStats,
) -> None:
    definitions = [
        child for child in root
        if _local_name(child.tag) == "defs"
    ]
    if not definitions:
        return
    visible_content = [child for child in root if child not in definitions]
    _, selected_owners = _definition_closure(root, visible_content)
    for definitions_root in definitions:
        for child in list(definitions_root):
            always_keep = _local_name(child.tag) == "style" or not child.get("id")
            if always_keep or id(child) in selected_owners:
                continue
            definitions_root.remove(child)
            stats.unused_definitions_pruned += 1
        if not list(definitions_root) and not (
            definitions_root.text and definitions_root.text.strip()
        ):
            root.remove(definitions_root)


def _proxy_canvas_attributes(root: ET.Element) -> dict[str, str]:
    view_box = (root.get("viewBox") or "").split()
    if len(view_box) == 4:
        x, y, width, height = view_box
    else:
        x = y = "0"
        width = root.get("width") or "1"
        height = root.get("height") or "1"
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "preserveAspectRatio": "none",
    }


def _source_proxy_asset_bytes(
    root: ET.Element,
    element: ET.Element,
    authoring_dir: Path,
    proxy_dir: Path,
    stats: ProjectionStats,
    *,
    strip_element_transform: bool = False,
) -> bytes:
    asset_root = ET.Element(root.tag, dict(root.attrib))
    for definitions in _selected_definitions(root, [element]):
        asset_root.append(definitions)
    asset_element = copy.deepcopy(element)
    if strip_element_transform:
        asset_element.attrib.pop("transform", None)
    asset_root.append(asset_element)
    for item in asset_root.iter():
        item.attrib.pop(SOURCE_REF_ATTRIBUTE, None)
        item.attrib.pop(SOURCE_PROXY_ATTRIBUTE, None)
    _rewrite_asset_references(
        asset_root,
        authoring_dir,
        proxy_dir,
        stats,
    )
    stats.coordinate_attributes_compacted += compact_svg_tree(
        asset_root,
    ).changed_attributes
    payload = _serialize_svg(asset_root)
    return payload if payload.endswith(b"\n") else payload + b"\n"


def _source_proxy_element(
    root: ET.Element,
    source: ET.Element,
    source_ref: str,
    asset_path: Path,
    output_dir: Path,
) -> ET.Element:
    proxy = ET.Element(f"{{{SVG_NS}}}image")
    for name in (
        "id",
        "data-pptx-object",
        "data-pptx-frame",
        EXTERNAL_LINKED_IMAGE_PROXY_ATTRIBUTE,
        "data-pptx-prst",
        "data-pptx-av-adj",
        "data-pptx-av-adj1",
        "data-pptx-av-adj2",
        "data-pptx-import-source",
        "data-pptx-native-authority",
        "data-pptx-replacement-status",
        "data-pptx-replace-with",
        "data-pptx-placeholder",
        "data-pptx-placeholder-type",
        "data-pptx-placeholder-idx",
        "data-pptx-structure-role",
    ):
        value = source.get(name)
        if value is not None:
            proxy.set(name, value)
    proxy.attrib.update(_proxy_canvas_attributes(root))
    proxy.set(
        "href",
        os.path.relpath(asset_path, output_dir).replace(os.sep, "/"),
    )
    proxy.set(SOURCE_REF_ATTRIBUTE, source_ref)
    proxy.set(SOURCE_PROXY_ATTRIBUTE, SOURCE_PROXY_KIND)
    proxy.tail = source.tail
    return proxy


def _compact_semantic_tables(
    root: ET.Element,
    references: list[SourceReference],
    output_dir: Path,
    preview_dir: Path,
    stats: ProjectionStats,
) -> dict[Path, bytes]:
    """Keep table data inline while moving only its rendered preview aside."""
    assets: dict[Path, bytes] = {}
    reference_by_id = {
        reference.source_ref: reference
        for reference in references
    }
    for element in list(root.iter()):
        if element.get(SEMANTIC_OBJECT_ATTRIBUTE) != SEMANTIC_TABLE_KIND:
            continue
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if not source_ref or source_ref not in reference_by_id:
            raise ValueError("Semantic table has no source reference")
        payload_metadata = [
            child
            for child in element
            if _local_name(child.tag) == "metadata"
            and child.get("type") == "application/json"
        ]
        if len(payload_metadata) != 1:
            raise ValueError(
                f"Semantic table {source_ref} requires exactly one JSON payload"
            )

        preview_source = copy.deepcopy(element)
        for child in list(preview_source):
            if _local_name(child.tag) == "metadata":
                preview_source.remove(child)
        payload = _source_proxy_asset_bytes(
            root,
            preview_source,
            output_dir,
            preview_dir,
            stats,
            strip_element_transform=True,
        )
        digest = hashlib.sha256(payload).hexdigest()
        asset_path = preview_dir / f"semantic-table-preview-{digest}.svg"
        previous = assets.get(asset_path)
        if previous is not None and previous != payload:
            raise ValueError(f"Semantic table preview hash collision: {asset_path.name}")
        assets[asset_path] = payload

        metadata = payload_metadata[0]
        metadata.tail = None
        for child in list(element):
            element.remove(child)
        element.append(metadata)
        preview = ET.Element(f"{{{SVG_NS}}}image")
        preview.attrib.update(_proxy_canvas_attributes(root))
        preview.set(
            "href",
            os.path.relpath(asset_path, output_dir).replace(os.sep, "/"),
        )
        preview.set("data-pptx-part", "authoring-preview")
        element.append(preview)
        stats.semantic_table_preview_bytes += len(payload)
    return assets


def _prefer_editable_vector_asset(element: ET.Element) -> bool:
    """Keep pure vector decorations available for later `<use>` extraction."""
    if any(
        _local_name(item.tag) in _SEMANTIC_CONTENT_TAGS
        for item in element.iter()
    ):
        return False
    if any(
        "chart" in (item.get("id") or "").lower()
        for item in element.iter()
    ):
        return False
    return any(
        _local_name(item.tag) in _DRAWABLE_TAGS
        for item in element.iter()
    )


def _contains_authoring_semantics(element: ET.Element) -> bool:
    """Keep meaning-bearing content inline and editable for the model."""
    for item in element.iter():
        if _local_name(item.tag) in _SEMANTIC_CONTENT_TAGS:
            return True
        if any(item.get(name) is not None for name in _SEMANTIC_AUTHORING_ATTRIBUTES):
            return True
        if (
            _local_name(item.tag) == "metadata"
            and item.get("type") == "application/json"
        ):
            return True
    return False


def _externalize_large_source_objects(
    root: ET.Element,
    references: list[SourceReference],
    output_dir: Path,
    proxy_dir: Path,
    stats: ProjectionStats,
) -> dict[Path, bytes]:
    reference_by_id = {
        reference.source_ref: reference
        for reference in references
    }
    candidates: list[tuple[ET.Element, ET.Element]] = []

    def visit(parent: ET.Element, inside_source_ref: bool) -> None:
        for child in list(parent):
            source_ref = child.get(SOURCE_REF_ATTRIBUTE)
            if source_ref and not inside_source_ref:
                candidates.append((parent, child))
                continue
            visit(child, inside_source_ref or bool(source_ref))

    visit(root, False)
    assets: dict[Path, bytes] = {}
    for parent, element in candidates:
        if element.get(SEMANTIC_OBJECT_ATTRIBUTE) in {
            SEMANTIC_SHAPE_KIND,
            SEMANTIC_TABLE_KIND,
        }:
            continue
        original_bytes = len(_serialize_svg(element))
        forced_source_proxy = (
            element.get(SOURCE_PROXY_ATTRIBUTE) == SOURCE_PROXY_KIND
        )
        if (
            not forced_source_proxy
            and (
                original_bytes < SOURCE_PROXY_MIN_BYTES
                or _contains_authoring_semantics(element)
                or _prefer_editable_vector_asset(element)
            )
        ):
            continue
        source_ref = element.get(SOURCE_REF_ATTRIBUTE)
        if not source_ref or source_ref not in reference_by_id:
            raise ValueError("Large source object has no manifest reference")
        payload = _source_proxy_asset_bytes(
            root,
            element,
            output_dir,
            proxy_dir,
            stats,
        )
        digest = hashlib.sha256(payload).hexdigest()
        asset_path = proxy_dir / f"source-object-{digest}.svg"
        previous = assets.get(asset_path)
        if previous is not None and previous != payload:
            raise ValueError(f"Source proxy hash collision: {asset_path.name}")
        assets[asset_path] = payload

        reference = reference_by_id[source_ref]
        reference.representation = "source-proxy"
        reference.proxy_asset = asset_path
        reference.proxy_asset_sha256 = digest
        proxy = _source_proxy_element(
            root,
            element,
            source_ref,
            asset_path,
            output_dir,
        )
        siblings = list(parent)
        index = siblings.index(element)
        parent.remove(element)
        parent.insert(index, proxy)
        stats.source_object_proxies += 1
        stats.source_object_proxy_bytes += original_bytes

    _prune_unreferenced_definitions(root, stats)
    active_refs = {
        source_ref
        for element in root.iter()
        if (source_ref := element.get(SOURCE_REF_ATTRIBUTE))
    }
    references[:] = [
        reference
        for reference in references
        if reference.source_ref in active_refs
    ]
    return assets


def _render_projection(
    source: Path,
    output: Path,
    source_proxy_dir: Path | None = None,
) -> tuple[ProjectionReport, bytes, dict[Path, bytes]]:
    """Build one projection in memory without changing source or destination."""
    original = source.read_bytes()
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True),
    )
    root = ET.fromstring(original, parser=parser)
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Root element is not <svg>: {source}")

    fresh_native_markers = _fresh_native_fallback_markers(root)
    source_references = _stamp_source_references(root)
    stats = ProjectionStats()
    _mark_semantic_objects(root, stats)
    _compact_semantic_shapes(root, stats)
    _project_subtree(root, stats)
    _compact_text_runs(root, stats)
    stats.compatibility_normalizations += len(
        normalize_single_child_group_filters(root)
    )
    _strip_import_attributes(root, stats)
    _rewrite_asset_references(root, source.parent, output.parent, stats)
    source_proxy_assets: dict[Path, bytes] = {}
    if source_proxy_dir is not None:
        source_proxy_assets.update(_compact_semantic_tables(
            root,
            source_references,
            output.parent,
            source_proxy_dir,
            stats,
        ))
        source_proxy_assets.update(_externalize_large_source_objects(
            root,
            source_references,
            output.parent,
            source_proxy_dir,
            stats,
        ))
    normalization = normalize_compact_authoring_tree(root)
    stats.coordinate_attributes_compacted = (
        normalization.coordinates.changed_attributes
    )
    stats.style_declarations_compacted = (
        normalization.styles.changed_declarations
    )
    live_elements = set(root.iter())
    for marker in fresh_native_markers & live_elements:
        if marker.get(SEMANTIC_OBJECT_ATTRIBUTE) == SEMANTIC_TABLE_KIND:
            marker.attrib.pop(NATIVE_FALLBACK_SHA256_ATTR, None)
            continue
        marker.set(
            NATIVE_FALLBACK_SHA256_ATTR,
            svg_native_fallback_fingerprint(marker, document_root=root),
        )
    _index_initial_authoring_references(root, source_references)

    contract_errors = canonical_authoring_errors(root)
    if contract_errors:
        raise ValueError(
            "Canonical authoring projection failed: "
            + "; ".join(contract_errors)
        )

    projected = _serialize_svg(root)
    if not projected.endswith(b"\n"):
        projected += b"\n"

    report = ProjectionReport(
        source=source,
        output=output,
        original_bytes=len(original),
        projected_bytes=len(projected),
        stats=stats,
        source_sha256=hashlib.sha256(original).hexdigest(),
        initial_authoring_sha256=hashlib.sha256(projected).hexdigest(),
        source_references=source_references,
    )
    return report, projected, source_proxy_assets


def _portable_path(path: Path, base: Path) -> str:
    try:
        return os.path.relpath(path, base).replace(os.sep, "/")
    except ValueError:
        return path.resolve().as_uri()


def _authoring_manifest_bytes(
    reports: list[ProjectionReport],
    source_root: Path,
    output_dir: Path,
    projection_kind: str,
) -> bytes:
    documents = []
    for report in sorted(reports, key=lambda item: item.output.as_posix()):
        documents.append({
            "source": report.source.relative_to(source_root).as_posix(),
            "authoring": report.output.relative_to(output_dir).as_posix(),
            "source_sha256": report.source_sha256,
            "initial_authoring_sha256": report.initial_authoring_sha256,
            "source_refs": {
                reference.source_ref: reference.as_dict(output_dir)
                for reference in sorted(
                    report.source_references,
                    key=lambda item: item.source_ref,
                )
            },
        })

    payload = {
        "schema": AUTHORING_SCHEMA,
        "projection_kind": projection_kind,
        "source_root": _portable_path(source_root, output_dir),
        "authoring_root": ".",
        "source_ref_attribute": SOURCE_REF_ATTRIBUTE,
        "file_count": len(documents),
        "source_ref_count": sum(len(report.source_references) for report in reports),
        "documents": documents,
    }
    return (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def _authoring_document_kind(path: Path) -> str:
    name = path.name
    if name.startswith("master_"):
        return "master"
    if name.startswith("layout_"):
        return "layout"
    if name.startswith("slide_"):
        return "slide"
    return "generic"


def _authoring_summary_document(
    path: Path,
    relative_name: str,
    *,
    source_slide: int | None = None,
) -> dict[str, object]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"Cannot summarize authoring SVG {path}: {exc}") from exc
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Authoring document root is not <svg>: {path}")

    elements = list(root.iter())
    icon_references = sorted({
        icon_name
        for element in elements
        if (icon_name := element.get("data-icon"))
    })
    text_elements = [
        element for element in elements
        if _local_name(element.tag) == "text"
    ]
    summary: dict[str, object] = {
        "file": relative_name,
        "kind": _authoring_document_kind(path),
    }
    if source_slide is not None:
        summary["source_slide"] = source_slide
    summary.update({
        "bytes": path.stat().st_size,
        "viewBox": root.get("viewBox"),
        "elements": len(elements),
        "top_level_elements": len(root),
        "drawables": sum(
            _local_name(element.tag) in _DRAWABLE_TAGS
            for element in elements
        ),
        "text_elements": len(text_elements),
        "text_characters": sum(
            len("".join(element.itertext()))
            for element in text_elements
        ),
        "images": sum(
            _local_name(element.tag) == "image"
            for element in elements
        ),
        "icon_uses": sum(
            element.get("data-icon") is not None
            for element in elements
        ),
        "icon_refs": icon_references,
        "placeholders": sum(
            element.get("data-pptx-placeholder") is not None
            for element in elements
        ),
        "inline_source_refs": sum(
            element.get(SOURCE_REF_ATTRIBUTE) is not None
            for element in elements
        ),
        "source_proxies": sum(
            element.get(SOURCE_PROXY_ATTRIBUTE) == SOURCE_PROXY_KIND
            for element in elements
        ),
        "semantic_tables": sum(
            element.get(SEMANTIC_OBJECT_ATTRIBUTE) == SEMANTIC_TABLE_KIND
            for element in elements
        ),
        "semantic_shapes": sum(
            element.get(SEMANTIC_OBJECT_ATTRIBUTE) == SEMANTIC_SHAPE_KIND
            for element in elements
        ),
    })
    return summary


def _load_authoring_summary_manifest(
    authoring_dir: Path,
) -> tuple[dict[str, object], list[str], dict[str, int] | None]:
    manifest_path = authoring_dir / AUTHORING_MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            f"Authoring manifest not found: {manifest_path}"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Cannot decode authoring manifest {manifest_path}: {exc}"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != AUTHORING_SCHEMA:
        raise ValueError(
            f"Unsupported authoring manifest schema in {manifest_path}"
        )
    documents = manifest.get("documents")
    if not isinstance(documents, list):
        raise ValueError(
            f"Authoring manifest documents must be an array: {manifest_path}"
        )

    names: list[str] = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise ValueError(
                f"Authoring manifest documents[{index}] must be an object"
            )
        name = document.get("authoring")
        relative = Path(name) if isinstance(name, str) else Path()
        if (
            not isinstance(name, str)
            or not name
            or relative.is_absolute()
            or any(part in {"", ".", ".."} for part in relative.parts)
            or relative.suffix.lower() != ".svg"
        ):
            raise ValueError(
                f"Authoring manifest documents[{index}].authoring is invalid"
            )
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("Authoring manifest contains duplicate document names")

    from pptx_workspace import ROUNDTRIP_PAGE_PLAN_PATH

    project_path = authoring_dir.parent
    if (project_path / ROUNDTRIP_PAGE_PLAN_PATH).exists():
        from authoring_roundtrip import (
            AuthoringRoundtripError,
            _load_documents,
            _load_page_plan,
        )

        try:
            _, _, roundtrip_documents, _, _ = _load_documents(
                project_path,
                authoring_dir,
            )
            pages, _ = _load_page_plan(
                project_path,
                authoring_dir,
                roundtrip_documents,
            )
        except AuthoringRoundtripError as exc:
            raise ValueError(
                f"Cannot build page-plan-aware authoring summary: {exc}"
            ) from exc
        source_slides = {
            name: document.source_slide
            for name, document in roundtrip_documents.items()
        }
        source_slides.update({
            page.svg_name: page.source_slide
            for page in pages
        })
        return manifest, sorted(source_slides), source_slides

    actual_names = sorted(
        path.relative_to(authoring_dir).as_posix()
        for path in authoring_dir.rglob("*.svg")
        if path.is_file()
    )
    if sorted(names) != actual_names:
        raise ValueError(
            "Authoring manifest/file roster differs while building summary"
        )
    return manifest, sorted(names), None


def _authoring_summary_bytes(authoring_dir: Path) -> bytes:
    (
        manifest,
        document_names,
        source_slides,
    ) = _load_authoring_summary_manifest(authoring_dir)
    documents = [
        _authoring_summary_document(
            authoring_dir / name,
            name,
            source_slide=(
                source_slides[name]
                if source_slides is not None
                else None
            ),
        )
        for name in document_names
    ]
    total_icon_assets = {
        icon_name
        for document in documents
        for icon_name in document["icon_refs"]
    }
    totals = {
        "svg_bytes": sum(int(document["bytes"]) for document in documents),
        "elements": sum(int(document["elements"]) for document in documents),
        "top_level_elements": sum(
            int(document["top_level_elements"])
            for document in documents
        ),
        "drawables": sum(int(document["drawables"]) for document in documents),
        "text_elements": sum(
            int(document["text_elements"])
            for document in documents
        ),
        "text_characters": sum(
            int(document["text_characters"])
            for document in documents
        ),
        "images": sum(int(document["images"]) for document in documents),
        "icon_uses": sum(int(document["icon_uses"]) for document in documents),
        "unique_icon_assets": len(total_icon_assets),
        "placeholders": sum(
            int(document["placeholders"])
            for document in documents
        ),
        "inline_source_refs": sum(
            int(document["inline_source_refs"])
            for document in documents
        ),
        "source_proxies": sum(
            int(document["source_proxies"])
            for document in documents
        ),
        "semantic_tables": sum(
            int(document["semantic_tables"])
            for document in documents
        ),
        "semantic_shapes": sum(
            int(document["semantic_shapes"])
            for document in documents
        ),
        "machine_source_refs": manifest.get("source_ref_count"),
    }
    payload = {
        "schema": AUTHORING_SUMMARY_SCHEMA,
        "projection_kind": manifest.get("projection_kind"),
        "authoring_root": ".",
        "machine_manifest": AUTHORING_MANIFEST_NAME,
        "machine_manifest_policy": "tool-only; do not load into model context",
        "file_count": len(documents),
        "totals": totals,
        "documents": documents,
    }
    if totals["source_proxies"]:
        payload["source_proxy_policy"] = {
            "marker": f'{SOURCE_PROXY_ATTRIBUTE}="{SOURCE_PROXY_KIND}"',
            "purpose": (
                "Atomic visual preview of an immutable source-backed "
                "PowerPoint object"
            ),
            "editing": (
                "Keep unchanged to restore the native object; a Slide-local "
                "proxy may be removed to delete it; inherited proxies must "
                "remain; do not edit the proxy or its asset"
            ),
        }
    return (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def write_authoring_summary(authoring_dir: Path) -> Path:
    """Regenerate the model-readable summary from the current authoring SVGs."""
    authoring_dir = Path(authoring_dir).resolve()
    if not authoring_dir.is_dir():
        raise ValueError(f"Authoring directory not found: {authoring_dir}")
    payload = _authoring_summary_bytes(authoring_dir)
    summary_path = authoring_dir / AUTHORING_SUMMARY_NAME
    with tempfile.NamedTemporaryFile(
        prefix=f".{AUTHORING_SUMMARY_NAME}.",
        suffix=".tmp",
        dir=authoring_dir,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(payload)
    try:
        temporary_path.chmod(0o644)
        temporary_path.replace(summary_path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise
    return summary_path


def _parse_adopt_source(value: str) -> tuple[str, str]:
    match = re.fullmatch(r"([^/\\]+\.svg):(.+)", value, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(
            "--adopt-object must use <from.svg>:<element-id>"
        )
    source_name, element_id = match.groups()
    if not element_id.strip() or element_id != element_id.strip():
        raise ValueError("--adopt-object element id must be non-empty and trimmed")
    return source_name, element_id


def _authoring_page_path(
    authoring_dir: Path,
    name: str,
    *,
    label: str,
) -> Path:
    relative = Path(name)
    if (
        "/" in name
        or "\\" in name
        or relative.name != name
        or relative.suffix.lower() != ".svg"
        or name in {".", ".."}
    ):
        raise ValueError(f"{label} must name one SVG directly in {authoring_dir}")
    path = (authoring_dir / name).resolve()
    try:
        path.relative_to(authoring_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes the authoring directory: {name!r}") from exc
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")
    return path


def _parse_authoring_svg(path: Path) -> ET.Element:
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True),
    )
    try:
        root = ET.fromstring(path.read_bytes(), parser=parser)
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"Cannot parse authoring SVG {path}: {exc}") from exc
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Authoring document root is not <svg>: {path}")
    return root


def _element_chain(
    root: ET.Element,
    element: ET.Element,
) -> tuple[ET.Element, ...]:
    """Return the root-to-element ancestry chain."""
    parent_by_child = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    chain = [element]
    while chain[-1] is not root:
        parent = parent_by_child.get(chain[-1])
        if parent is None:
            raise ValueError("Adopted element is detached from its source SVG")
        chain.append(parent)
    return tuple(reversed(chain))


def _local_inherited_presentation(element: ET.Element) -> dict[str, str]:
    """Resolve supported local presentation attributes with CSS precedence."""
    values = {
        name: value
        for name in _ADOPT_INHERITED_ATTRIBUTES
        if (value := element.get(name)) is not None
    }
    values.update({
        name: value
        for name, value in parse_inline_style(element.get("style")).items()
        if name in _ADOPT_INHERITED_ATTRIBUTES
    })
    return values


def _local_opacity(element: ET.Element) -> str | None:
    inline = parse_inline_style(element.get("style"))
    return inline.get("opacity") or element.get("opacity")


def _set_explicit_presentation(
    element: ET.Element,
    name: str,
    value: str,
) -> None:
    """Write one resolved style as an attribute, removing its inline shadow."""
    inline = parse_inline_style(element.get("style"))
    if name in inline:
        inline.pop(name)
        if inline:
            element.set(
                "style",
                "; ".join(
                    f"{property_name}: {property_value}"
                    for property_name, property_value in inline.items()
                ),
            )
        else:
            element.attrib.pop("style", None)
    element.set(name, value)


def _format_transform_number(value: float) -> str:
    if math.isclose(value, 0.0, abs_tol=1e-12):
        value = 0.0
    return f"{value:.12g}"


def _materialize_adopted_context(
    source_root: ET.Element,
    source_element: ET.Element,
    target_root: ET.Element,
    adopted: ET.Element,
) -> tuple[tuple[str, ...], bool]:
    """Carry source ancestry style and transforms onto an adopted object."""
    chain = _element_chain(source_root, source_element)
    effective: dict[str, str] = {}
    for ancestor in chain:
        effective.update(_local_inherited_presentation(ancestor))
    target_defaults = _local_inherited_presentation(target_root)
    materialized: list[str] = []
    for name, value in effective.items():
        if target_defaults.get(name) == value:
            continue
        _set_explicit_presentation(adopted, name, value)
        materialized.append(name)

    source_opacity = 1.0
    source_has_opacity = False
    try:
        for ancestor in chain:
            raw_opacity = _local_opacity(ancestor)
            if raw_opacity is None:
                continue
            source_has_opacity = True
            source_opacity *= parse_opacity(
                raw_opacity,
                allow_percentage=True,
            )
        target_raw_opacity = _local_opacity(target_root)
        target_opacity = parse_opacity(
            target_raw_opacity,
            allow_percentage=True,
        )
    except ValueError as exc:
        raise ValueError(f"Cannot resolve adopted object opacity: {exc}") from exc
    if (
        (source_has_opacity or target_raw_opacity is not None)
        and not math.isclose(source_opacity, target_opacity, abs_tol=1e-12)
    ):
        _set_explicit_presentation(
            adopted,
            "opacity",
            _format_transform_number(source_opacity),
        )
        materialized.append("opacity")

    ancestor_transform_composed = any(
        (ancestor.get("transform") or "").strip()
        for ancestor in chain[:-1]
    )
    if ancestor_transform_composed:
        matrix = IDENTITY_MATRIX
        try:
            for ancestor in chain:
                raw_transform = ancestor.get("transform")
                if raw_transform:
                    matrix = matrix_multiply(
                        matrix,
                        parse_transform_matrix(raw_transform),
                    )
        except ValueError as exc:
            raise ValueError(
                f"Cannot compose adopted object ancestor transform: {exc}"
            ) from exc
        adopted.set(
            "transform",
            "matrix(" + " ".join(
                _format_transform_number(value)
                for value in matrix
            ) + ")",
        )
    return tuple(sorted(materialized)), ancestor_transform_composed


def _rewrite_adopted_fragment_ids(
    element: ET.Element,
    target_ids: set[str],
) -> dict[str, str]:
    subtree_ids = [
        item_id
        for item in element.iter()
        if (item_id := item.get("id"))
    ]
    duplicates = sorted(
        item_id
        for item_id, count in Counter(subtree_ids).items()
        if count > 1
    )
    if duplicates:
        raise ValueError(
            "Adopted subtree contains duplicate id(s): "
            + ", ".join(duplicates[:8])
        )

    reserved = set(target_ids) | set(subtree_ids)
    replacements: dict[str, str] = {}
    for item_id in subtree_ids:
        if item_id not in target_ids:
            continue
        base = f"{item_id}-adopted"
        candidate = base
        suffix = 2
        while candidate in reserved:
            candidate = f"{base}-{suffix}"
            suffix += 1
        replacements[item_id] = candidate
        reserved.add(candidate)

    if not replacements:
        return replacements

    def rewrite_url(match: re.Match[str]) -> str:
        quote, ref_id = match.group(1), match.group(2)
        return f"url({quote}#{replacements.get(ref_id, ref_id)}{quote})"

    for item in element.iter():
        item_id = item.get("id")
        if item_id in replacements:
            item.set("id", replacements[item_id])
        for name, value in list(item.attrib.items()):
            rewritten = _URL_ID_RE.sub(rewrite_url, value)
            if _local_name(name) == "href" and value.startswith("#"):
                rewritten = "#" + replacements.get(value[1:], value[1:])
            if rewritten != value:
                item.set(name, rewritten)
    return replacements


def _adopted_definition_clones(
    source_root: ET.Element,
    source_element: ET.Element,
) -> list[ET.Element]:
    """Copy the transitive source definitions referenced by one adopted object."""
    context_elements = [source_element]
    for ancestor in _element_chain(source_root, source_element)[:-1]:
        context = ET.Element(ancestor.tag)
        for name in (*_ADOPT_INHERITED_ATTRIBUTES, "opacity", "style"):
            value = ancestor.get(name)
            if value is not None:
                context.set(name, value)
        context_elements.append(context)
    definitions, selected_owners = _definition_closure(
        source_root,
        context_elements,
    )
    return [
        copy.deepcopy(child)
        for definitions_root in definitions
        for child in definitions_root
        if id(child) in selected_owners
    ]


def _append_adopted_definitions(
    target_root: ET.Element,
    definitions: list[ET.Element],
) -> None:
    if not definitions:
        return
    target_defs = next(
        (
            child
            for child in target_root
            if _local_name(child.tag) == "defs"
        ),
        None,
    )
    if target_defs is None:
        target_defs = ET.Element(f"{{{SVG_NS}}}defs")
        target_root.insert(0, target_defs)
    target_defs.extend(definitions)


def _authoring_source_document_ids(
    authoring_dir: Path,
    manifest: dict[str, object],
    authoring_name: str,
) -> set[str]:
    """Return ids hidden behind source refs in one authoring document."""
    documents = manifest.get("documents")
    if not isinstance(documents, list):
        return set()
    document = next(
        (
            item
            for item in documents
            if isinstance(item, dict)
            and item.get("authoring") == authoring_name
        ),
        None,
    )
    source_root_value = manifest.get("source_root")
    source_name = document.get("source") if document is not None else None
    if not isinstance(source_root_value, str) or not isinstance(source_name, str):
        return set()
    source_dir = (authoring_dir / source_root_value).resolve()
    source_path = _authoring_page_path(
        source_dir,
        source_name,
        label="--adopt-object target source",
    )
    source_root = _parse_authoring_svg(source_path)
    return {
        item_id
        for item in source_root.iter()
        if (item_id := item.get("id"))
    }


def _strip_adopted_transport(element: ET.Element) -> tuple[set[str], int]:
    stripped: set[str] = set()
    removed_metadata = 0

    def visit(parent: ET.Element) -> None:
        nonlocal removed_metadata
        for child in list(parent):
            original_part = child.get("data-pptx-part")
            has_transport = any(
                name in ADOPT_OBJECT_STRIPPED_ATTRIBUTES
                for name in child.attrib
            )
            is_json_metadata = (
                _local_name(child.tag) == "metadata"
                and child.get("type") == "application/json"
            )
            if (
                _local_name(child.tag) == "metadata"
                and not is_json_metadata
                and (original_part is not None or has_transport)
            ):
                stripped.update(
                    name
                    for name in child.attrib
                    if name in ADOPT_OBJECT_STRIPPED_ATTRIBUTES
                )
                parent.remove(child)
                removed_metadata += 1
                continue
            visit(child)

    visit(element)
    for item in element.iter():
        for name in list(item.attrib):
            if name not in ADOPT_OBJECT_STRIPPED_ATTRIBUTES:
                continue
            stripped.add(name)
            item.attrib.pop(name, None)
        if item.get(SEMANTIC_OBJECT_ATTRIBUTE) == SEMANTIC_SHAPE_KIND:
            stripped.add(SEMANTIC_OBJECT_ATTRIBUTE)
            item.attrib.pop(SEMANTIC_OBJECT_ATTRIBUTE, None)
    return stripped, removed_metadata


def _write_svg_atomically(path: Path, root: ET.Element) -> None:
    payload = _serialize_svg(root)
    if not payload.endswith(b"\n"):
        payload += b"\n"
    with tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(payload)
    try:
        temporary_path.chmod(path.stat().st_mode)
        temporary_path.replace(path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def adopt_authoring_object(
    authoring_dir: Path,
    source_spec: str,
    target_name: str,
) -> dict[str, object]:
    """Copy one cross-page object as authored SVG with no source identity."""
    authoring_dir = authoring_dir.resolve()
    if not authoring_dir.is_dir():
        raise ValueError(f"Authoring directory not found: {authoring_dir}")
    manifest, _, _ = _load_authoring_summary_manifest(authoring_dir)
    source_name, element_id = _parse_adopt_source(source_spec)
    source_path = _authoring_page_path(
        authoring_dir,
        source_name,
        label="--adopt-object source",
    )
    target_path = _authoring_page_path(
        authoring_dir,
        target_name,
        label="--into target",
    )
    if source_path == target_path:
        raise ValueError("--adopt-object source and --into target must differ")

    source_root = _parse_authoring_svg(source_path)
    target_root = _parse_authoring_svg(target_path)
    matches = [
        item
        for item in source_root.iter()
        if item.get("id") == element_id
    ]
    if not matches:
        raise ValueError(f"{source_name} has no element id {element_id!r}")
    if len(matches) > 1:
        raise ValueError(f"{source_name} repeats element id {element_id!r}")
    source_element = matches[0]
    if any(
        item.get(SOURCE_PROXY_ATTRIBUTE) == SOURCE_PROXY_KIND
        for item in source_element.iter()
    ):
        raise ValueError(
            f"Cannot adopt source proxy {source_name}:{element_id}; "
            "source proxies cannot move between pages"
        )

    adopted_definitions = _adopted_definition_clones(
        source_root,
        source_element,
    )
    adopted = copy.deepcopy(source_element)
    adopted.tail = None
    imported_icons = [
        item
        for item in adopted.iter()
        if _local_name(item.tag) == "use"
        and (item.get("data-icon") or "").startswith("imported/")
    ]
    inlined_icons = 0
    if imported_icons:
        from svg_to_pptx.use_expander import (
            UseExpansionError,
            expand_use_data_icons,
        )

        container = ET.Element(f"{{{SVG_NS}}}g")
        container.append(adopted)
        try:
            inlined_icons = expand_use_data_icons(
                container,
                authoring_dir.parent / "icons",
            )
        except UseExpansionError as exc:
            raise ValueError(
                f"Cannot inline source-page vector asset: {exc}"
            ) from exc
        adopted = container[0]
        if adopted.get("id") is None:
            adopted.set("id", element_id)
    residual_imports = sorted({
        icon
        for item in adopted.iter()
        if (icon := item.get("data-icon"))
        and icon.startswith("imported/")
    })
    if residual_imports:
        raise ValueError(
            "Adopted object retains source-owned imported vector(s): "
            + ", ".join(residual_imports)
        )

    inherited_attributes, ancestor_transform_composed = (
        _materialize_adopted_context(
            source_root,
            source_element,
            target_root,
            adopted,
        )
    )
    stripped, removed_metadata = _strip_adopted_transport(adopted)
    target_ids = {
        item_id
        for item in target_root.iter()
        if (item_id := item.get("id"))
    }
    target_ids.update(
        _authoring_source_document_ids(
            authoring_dir,
            manifest,
            target_name,
        )
    )
    adopted_envelope = ET.Element(f"{{{SVG_NS}}}g")
    adopted_envelope.append(adopted)
    adopted_envelope.extend(adopted_definitions)
    replacements = _rewrite_adopted_fragment_ids(
        adopted_envelope,
        target_ids,
    )
    adopted = adopted_envelope[0]
    adopted_definitions = list(adopted_envelope)[1:]
    adopted_id = adopted.get("id")
    if not adopted_id:
        raise ValueError("Adopted object lost its required id")
    _append_adopted_definitions(target_root, adopted_definitions)
    target_root.append(adopted)

    original_target = target_path.read_bytes()
    try:
        _write_svg_atomically(target_path, target_root)
        summary_path = write_authoring_summary(authoring_dir)
    except (OSError, ValueError):
        with tempfile.NamedTemporaryFile(
            prefix=f".{target_path.name}.rollback.",
            suffix=".tmp",
            dir=target_path.parent,
            delete=False,
        ) as handle:
            rollback_path = Path(handle.name)
            handle.write(original_target)
        rollback_path.chmod(target_path.stat().st_mode)
        rollback_path.replace(target_path)
        raise

    return {
        "authoring_dir": str(authoring_dir),
        "source": f"{source_name}:{element_id}",
        "target": target_name,
        "adopted_id": adopted_id,
        "renamed_ids": dict(sorted(replacements.items())),
        "copied_definitions": len(adopted_definitions),
        "inlined_imported_vectors": inlined_icons,
        "inherited_attributes": list(inherited_attributes),
        "ancestor_transform_composed": ancestor_transform_composed,
        "stripped_attributes": sorted(stripped),
        "removed_native_metadata": removed_metadata,
        "summary": str(summary_path),
    }


def _nearest_existing_directory(path: Path) -> Path:
    candidate = path
    while not os.path.lexists(candidate):
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    if not candidate.is_dir():
        raise NotADirectoryError(f"Output parent is not a directory: {candidate}")
    return candidate


def _ensure_directory(path: Path, created: list[Path]) -> None:
    missing: list[Path] = []
    candidate = path
    while not candidate.exists():
        if os.path.lexists(candidate):
            raise NotADirectoryError(f"Output parent is not a directory: {candidate}")
        missing.append(candidate)
        parent = candidate.parent
        if parent == candidate:
            raise NotADirectoryError(f"Cannot resolve output parent: {path}")
        candidate = parent
    if not candidate.is_dir():
        raise NotADirectoryError(f"Output parent is not a directory: {candidate}")

    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)


def _remove_created_directories(created: list[Path]) -> list[str]:
    errors: list[str] = []
    for directory in reversed(created):
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"could not remove {directory}: {exc}")
    return errors


def _rollback_published_files(
    published: list[tuple[Path, Path | None]],
    created: list[Path],
) -> list[str]:
    errors: list[str] = []
    for target, backup in reversed(published):
        try:
            if backup is None:
                target.unlink(missing_ok=True)
            else:
                backup.replace(target)
        except OSError as exc:
            errors.append(f"could not restore {target}: {exc}")
    errors.extend(_remove_created_directories(created))
    return errors


def _publish_existing_directory(
    staged: list[tuple[Path, Path]],
    staging_root: Path,
    *,
    force: bool,
) -> None:
    backup_root = staging_root / "previous"
    backups: dict[Path, Path | None] = {}

    for index, (target, _) in enumerate(staged):
        if not os.path.lexists(target):
            backups[target] = None
            continue
        if not force:
            raise FileExistsError(f"Output file already exists: {target}")
        if target.is_dir() and not target.is_symlink():
            raise IsADirectoryError(f"Output target is a directory: {target}")

        backup = backup_root / f"{index:06d}.bak"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup, follow_symlinks=False)
        backups[target] = backup

    created: list[Path] = []
    published: list[tuple[Path, Path | None]] = []
    try:
        for target, _ in staged:
            _ensure_directory(target.parent, created)

        staging_device = staging_root.stat().st_dev
        for target, _ in staged:
            if target.parent.stat().st_dev != staging_device:
                raise OSError(
                    f"Cannot atomically publish across filesystems: {target}"
                )
            if backups[target] is None and os.path.lexists(target):
                raise FileExistsError(
                    f"Output appeared while projections were staged: {target}"
                )

        for target, staged_file in staged:
            staged_file.replace(target)
            published.append((target, backups[target]))
    except OSError as exc:
        rollback_errors = _rollback_published_files(published, created)
        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise RuntimeError(
                f"Batch publish failed ({exc}); rollback was incomplete: {details}"
            ) from exc
        raise


def project_svg_batch(
    mapping: list[tuple[Path, Path]],
    source_root: Path,
    output_dir: Path,
    *,
    force: bool,
    projection_kind: str,
    source_proxy_dir: Path | None = None,
    publish_source_proxies: bool = True,
) -> list[ProjectionReport]:
    """Build and publish one complete authoring bundle transactionally."""
    if source_proxy_dir is not None and _is_within(
        source_proxy_dir.resolve(),
        output_dir.resolve(),
    ):
        raise ValueError("Source proxy assets must live outside the authoring bundle")
    rendered = [
        _render_projection(source, output, source_proxy_dir)
        for source, output in mapping
    ]
    proxy_assets: dict[Path, bytes] = {}
    for _, _, rendered_assets in rendered:
        for target, payload in rendered_assets.items():
            previous = proxy_assets.get(target)
            if previous is not None and previous != payload:
                raise ValueError(f"Source proxy collision: {target}")
            proxy_assets[target] = payload
    if source_proxy_dir is not None and not publish_source_proxies:
        for target, payload in proxy_assets.items():
            if not target.is_file() or target.read_bytes() != payload:
                raise ValueError(
                    f"Source proxy asset is missing or stale: {target}"
                )
    staging_parent = _nearest_existing_directory(output_dir.parent)

    with tempfile.TemporaryDirectory(
        prefix=".svg-authoring-view-",
        dir=staging_parent,
    ) as temporary:
        staging_root = Path(temporary)
        new_root = staging_root / "projected"
        staged: list[tuple[Path, Path]] = []

        for report, projected, _ in rendered:
            relative = report.output.relative_to(output_dir)
            staged_file = new_root / relative
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_bytes(projected)
            staged.append((report.output, staged_file))

        manifest_path = output_dir / AUTHORING_MANIFEST_NAME
        staged_manifest = new_root / AUTHORING_MANIFEST_NAME
        staged_manifest.write_bytes(
            _authoring_manifest_bytes(
                [report for report, _, _ in rendered],
                source_root,
                output_dir,
                projection_kind,
            )
        )
        staged.append((manifest_path, staged_manifest))
        staged_summary = write_authoring_summary(new_root)
        staged.append(
            (
                output_dir / AUTHORING_SUMMARY_NAME,
                staged_summary,
            )
        )

        if publish_source_proxies:
            proxy_staging = staging_root / "source-proxies"
            for index, (target, payload) in enumerate(sorted(
                proxy_assets.items(),
                key=lambda item: item[0].as_posix(),
            )):
                if os.path.lexists(target):
                    if (
                        target.is_symlink()
                        or not target.is_file()
                        or target.read_bytes() != payload
                    ):
                        raise FileExistsError(
                            f"Source proxy target has different content: {target}"
                        )
                    continue
                staged_proxy = proxy_staging / f"{index:06d}.svg"
                staged_proxy.parent.mkdir(parents=True, exist_ok=True)
                staged_proxy.write_bytes(payload)
                staged.append((target, staged_proxy))

        has_external_targets = any(
            not _is_within(target.resolve(), output_dir.resolve())
            for target, _ in staged
        )
        if not output_dir.exists() and not has_external_targets:
            created: list[Path] = []
            try:
                _ensure_directory(output_dir.parent, created)
                if os.path.lexists(output_dir):
                    raise FileExistsError(
                        f"Output directory appeared while projections were staged: {output_dir}"
                    )
                if output_dir.parent.stat().st_dev != staging_root.stat().st_dev:
                    raise OSError(
                        f"Cannot atomically publish across filesystems: {output_dir}"
                    )
                new_root.replace(output_dir)
            except OSError as exc:
                cleanup_errors = _remove_created_directories(created)
                if cleanup_errors:
                    details = "; ".join(cleanup_errors)
                    raise RuntimeError(
                        f"Batch publish failed ({exc}); cleanup was incomplete: {details}"
                    ) from exc
                raise
        else:
            _publish_existing_directory(
                staged,
                staging_root,
                force=force,
            )

    return [report for report, _, _ in rendered]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _source_mapping(input_path: Path, output_dir: Path) -> list[tuple[Path, Path]]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".svg":
            raise ValueError(f"Input file must use the .svg extension: {input_path}")
        return [(input_path, output_dir / input_path.name)]

    sources = sorted(
        path for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() == ".svg"
    )
    if not sources:
        raise ValueError(f"No SVG files found under: {input_path}")
    return [(source, output_dir / source.relative_to(input_path)) for source in sources]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create lightweight editable IR bundles from PPTX-imported SVG files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="SVG file or directory to project")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Explicit destination directory for projected SVG copies",
    )
    parser.add_argument(
        "--refresh-summary",
        action="store_true",
        help=(
            "Regenerate authoring_summary.json for an existing authoring "
            "bundle; input must be that bundle directory and -o is omitted"
        ),
    )
    parser.add_argument(
        "--adopt-object",
        metavar="<from.svg>:<element-id>",
        help=(
            "Copy one object from another page as authored SVG, strip its "
            "source/native transport, and refresh the bundle summary"
        ),
    )
    parser.add_argument(
        "--into",
        metavar="<target.svg>",
        help="Target page for --adopt-object",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Replace authoring files/manifest that already exist "
            "(never changes source files)"
        ),
    )
    parser.add_argument(
        "--projection-kind",
        choices=("layered", "flat", "generic"),
        default="generic",
        help="Record the IR representation kind in bundle metadata",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = args.input.resolve()

    if not input_path.exists():
        print(f"Error: input does not exist: {input_path}", file=sys.stderr)
        return 1
    if args.refresh_summary and args.adopt_object is not None:
        parser.error("--refresh-summary and --adopt-object are mutually exclusive")
    if args.adopt_object is not None:
        if args.into is None:
            parser.error("--adopt-object requires --into <target.svg>")
        if args.output_dir is not None:
            parser.error("--adopt-object does not accept -o/--output-dir")
        if args.force:
            parser.error("--adopt-object does not accept --force")
        if args.projection_kind != "generic":
            parser.error("--adopt-object does not accept --projection-kind")
        try:
            result = adopt_authoring_object(
                input_path,
                args.adopt_object,
                args.into,
            )
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.into is not None:
        parser.error("--into requires --adopt-object")
    if args.refresh_summary:
        if args.output_dir is not None:
            print(
                "Error: --refresh-summary does not accept -o/--output-dir",
                file=sys.stderr,
            )
            return 1
        try:
            summary_path = write_authoring_summary(input_path)
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({
            "authoring_dir": str(input_path),
            "summary": str(summary_path),
            "summary_bytes": summary_path.stat().st_size,
        }, ensure_ascii=False, indent=2))
        return 0
    if args.output_dir is None:
        parser.error("-o/--output-dir is required unless --refresh-summary is used")
    output_dir = args.output_dir.resolve()

    if output_dir.exists() and not output_dir.is_dir():
        print(f"Error: output path is not a directory: {output_dir}", file=sys.stderr)
        return 1
    if input_path.is_dir() and _is_within(output_dir, input_path):
        print("Error: output directory must not be inside the input directory", file=sys.stderr)
        return 1

    try:
        mapping = _source_mapping(input_path, output_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    same_file = [source for source, target in mapping if source.resolve() == target.resolve()]
    if same_file:
        print(f"Error: output would overwrite source SVG: {same_file[0]}", file=sys.stderr)
        return 1

    collisions = [target for _, target in mapping if os.path.lexists(target)]
    manifest_path = output_dir / AUTHORING_MANIFEST_NAME
    if os.path.lexists(manifest_path):
        collisions.append(manifest_path)
    summary_path = output_dir / AUTHORING_SUMMARY_NAME
    if os.path.lexists(summary_path):
        collisions.append(summary_path)
    if collisions and not args.force:
        print(
            f"Error: {len(collisions)} output file(s) already exist; "
            "use --force to replace the authoring bundle. "
            f"First collision: {collisions[0]}",
            file=sys.stderr,
        )
        return 1

    reports: list[ProjectionReport] = []
    try:
        source_root = input_path if input_path.is_dir() else input_path.parent
        reports = project_svg_batch(
            mapping,
            source_root,
            output_dir,
            force=args.force,
            projection_kind=args.projection_kind,
        )
    except (ET.ParseError, OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    total_stats = ProjectionStats()
    original_bytes = 0
    projected_bytes = 0
    for report in reports:
        original_bytes += report.original_bytes
        projected_bytes += report.projected_bytes
        total_stats.merge(report.stats)

    bytes_saved = original_bytes - projected_bytes
    reduction = (bytes_saved / original_bytes * 100) if original_bytes else 0.0
    result = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "manifest": str(output_dir / AUTHORING_MANIFEST_NAME),
        "summary": str(output_dir / AUTHORING_SUMMARY_NAME),
        "projection_kind": args.projection_kind,
        "file_count": len(reports),
        "files": [report.as_dict() for report in reports],
        "totals": {
            "original_bytes": original_bytes,
            "projected_bytes": projected_bytes,
            "bytes_saved": bytes_saved,
            "reduction_percent": round(reduction, 2),
            "removed": total_stats.as_dict(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
