#!/usr/bin/env python3
"""
PPT Master - SVG Authoring View

Create a lightweight, non-destructive editable IR from PPTX-imported SVG
files. The source SVG remains the native-payload authority; the authoring copy
keeps visible SVG content, compact shape intent, and stable source references
while hiding bulky import-only payloads and duplicate hidden geometry carriers.

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
`authoring_manifest.json` provenance sidecar. It is the template-creation
input, not a release SVG directory; final templates are materialized from this
IR. Directory runs prepare and stage the complete batch before publishing it,
so a failed page leaves the existing destination set unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
AUTHORING_MANIFEST_NAME = "authoring_manifest.json"
AUTHORING_SUMMARY_NAME = "authoring_summary.json"
AUTHORING_SCHEMA = "ppt-master.svg-authoring-ir.v1"
AUTHORING_SUMMARY_SCHEMA = "ppt-master.svg-authoring-summary.v1"
SOURCE_REF_ATTRIBUTE = "data-pptx-source-ref"
_DRAWABLE_TAGS = frozenset({
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
})

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

# These fields identify the source OOXML object or guard its exact imported
# fallback. They belong in the complete import SVG, not its lightweight view.
IMPORT_SOURCE_ATTRIBUTES = {
    "data-name",
    "data-pptx-preview-sha256",
    "data-pptx-shape-id",
    "data-pptx-shape-name",
    "data-pptx-shape-scope",
    "data-pptx-shape-style",
}

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

    def as_dict(self) -> dict[str, object]:
        return {
            "source_path": list(self.source_path),
            "initial_authoring_subtree_sha256": self.initial_authoring_subtree_sha256,
        }


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


@dataclass
class ProjectionStats:
    txbody_metadata: int = 0
    hidden_geometry_carriers: int = 0
    geometry_preview_wrappers: int = 0
    geometry_detail_markers: int = 0
    asset_references_rewritten: int = 0
    coordinate_attributes_compacted: int = 0
    source_attributes: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict[str, object]:
        return {
            "txbody_metadata": self.txbody_metadata,
            "hidden_geometry_carriers": self.hidden_geometry_carriers,
            "geometry_preview_wrappers": self.geometry_preview_wrappers,
            "geometry_detail_markers": self.geometry_detail_markers,
            "source_attributes": dict(sorted(self.source_attributes.items())),
            "asset_references_rewritten": self.asset_references_rewritten,
            "coordinate_attributes_compacted": self.coordinate_attributes_compacted,
        }

    def merge(self, other: "ProjectionStats") -> None:
        self.txbody_metadata += other.txbody_metadata
        self.hidden_geometry_carriers += other.hidden_geometry_carriers
        self.geometry_preview_wrappers += other.geometry_preview_wrappers
        self.geometry_detail_markers += other.geometry_detail_markers
        self.asset_references_rewritten += other.asset_references_rewritten
        self.coordinate_attributes_compacted += (
            other.coordinate_attributes_compacted
        )
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
        if name not in IMPORT_SOURCE_ATTRIBUTES:
            continue
        stats.source_attributes[name] += 1
        del element.attrib[name]


def _project_subtree(parent: ET.Element, stats: ProjectionStats) -> None:
    for child in list(parent):
        part = child.get("data-pptx-part")
        tag = _local_name(child.tag)

        if tag == "metadata" and part == "txbody":
            stats.txbody_metadata += 1
            _remove_child(parent, child)
            continue

        if _is_hidden_geometry_carrier(child):
            stats.hidden_geometry_carriers += 1
            _remove_child(parent, child)
            continue

        _project_subtree(child, stats)
        _strip_import_attributes(child, stats)

        if part == "geometry-preview":
            child.attrib.pop("data-pptx-part", None)
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


def _render_projection(source: Path, output: Path) -> tuple[ProjectionReport, bytes]:
    """Build one projection in memory without changing source or destination."""
    original = source.read_bytes()
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True),
    )
    root = ET.fromstring(original, parser=parser)
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Root element is not <svg>: {source}")

    source_references = _stamp_source_references(root)
    stats = ProjectionStats()
    _project_subtree(root, stats)
    _strip_import_attributes(root, stats)
    _rewrite_asset_references(root, source.parent, output.parent, stats)
    stats.coordinate_attributes_compacted = compact_svg_tree(
        root,
    ).changed_attributes
    _index_initial_authoring_references(root, source_references)

    projected = ET.tostring(root, encoding="utf-8", xml_declaration=False)
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
    return report, projected


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
                reference.source_ref: reference.as_dict()
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
    return {
        "file": relative_name,
        "kind": _authoring_document_kind(path),
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
    }


def _load_authoring_summary_manifest(
    authoring_dir: Path,
) -> tuple[dict[str, object], list[str]]:
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

    actual_names = sorted(
        path.relative_to(authoring_dir).as_posix()
        for path in authoring_dir.rglob("*.svg")
        if path.is_file()
    )
    if sorted(names) != actual_names:
        raise ValueError(
            "Authoring manifest/file roster differs while building summary"
        )
    return manifest, sorted(names)


def _authoring_summary_bytes(authoring_dir: Path) -> bytes:
    manifest, document_names = _load_authoring_summary_manifest(authoring_dir)
    documents = [
        _authoring_summary_document(authoring_dir / name, name)
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
) -> list[ProjectionReport]:
    """Build and publish one complete authoring bundle transactionally."""
    rendered = [_render_projection(source, output) for source, output in mapping]
    staging_parent = _nearest_existing_directory(output_dir.parent)

    with tempfile.TemporaryDirectory(
        prefix=".svg-authoring-view-",
        dir=staging_parent,
    ) as temporary:
        staging_root = Path(temporary)
        new_root = staging_root / "projected"
        staged: list[tuple[Path, Path]] = []

        for report, projected in rendered:
            relative = report.output.relative_to(output_dir)
            staged_file = new_root / relative
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_bytes(projected)
            staged.append((report.output, staged_file))

        manifest_path = output_dir / AUTHORING_MANIFEST_NAME
        staged_manifest = new_root / AUTHORING_MANIFEST_NAME
        staged_manifest.write_bytes(
            _authoring_manifest_bytes(
                [report for report, _ in rendered],
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

        if not output_dir.exists():
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

    return [report for report, _ in rendered]


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
