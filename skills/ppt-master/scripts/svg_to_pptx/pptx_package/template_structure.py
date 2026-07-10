#!/usr/bin/env python3
"""
PPT Master - Template Structure Metadata

Parse and validate explicit SVG metadata consumed by template-mode PPTX export.

Usage:
    Imported by svg_to_pptx.pptx_package.builder and svg_quality_checker.py.

Examples:
    parse_template_slides([Path("projects/demo/svg_output/01_cover.svg")])

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


_NON_VISUAL_TAGS = frozenset({"defs", "title", "desc", "metadata", "style"})
_STRUCTURE_ATTRS = frozenset({
    "data-pptx-layer",
    "data-pptx-layout",
    "data-pptx-layout-name",
    "data-pptx-placeholder",
    "data-pptx-placeholder-bounds",
    "data-pptx-placeholder-idx",
    "data-pptx-editable",
})
_LAYERS = frozenset({"master", "layout", "slide"})
_PLACEHOLDERS = frozenset({
    "title",
    "body",
    "picture",
    "chart",
    "table",
    "footer",
    "slide-number",
})
_TEXT_PLACEHOLDERS = frozenset({"title", "body", "footer", "slide-number"})
_LAYOUT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_LOCK_ROW_RE = re.compile(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$")
_LOCK_PAGE_RE = re.compile(r"^P(\d+)$")
PPTX_STRUCTURE_MODES = frozenset({"baseline", "template", "preserve", "flat"})
TEMPLATE_ADHERENCE_MODES = frozenset({"strict", "adaptive"})
NATIVE_STRUCTURE_SCHEMA = "ppt-master.native-structure.v1"


class TemplateStructureError(RuntimeError):
    """Reject invalid or ambiguous template-structure metadata."""


@dataclass(frozen=True)
class PptxLayoutReference:
    """One spec_lock page-to-PowerPoint-layout declaration."""

    slide_num: int
    layout_key: str
    layout_name: str | None = None


@dataclass(frozen=True)
class PptxStructureLock:
    """Optional project-level PPTX structure export policy."""

    mode: str
    template_adherence: str | None = None
    layouts: tuple[PptxLayoutReference, ...] = ()
    source_template: Path | None = None
    native_structure: Path | None = None


@dataclass(frozen=True)
class NativePlaceholderSpec:
    """One placeholder exposed by a preserved source layout."""

    semantic_role: str
    placeholder_type: str
    idx: int | None
    geometry: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class NativeLayoutSpec:
    """One named layout retained from the source PPTX package."""

    key: str
    name: str
    package_part: str
    master_key: str
    placeholders: tuple[NativePlaceholderSpec, ...] = ()


@dataclass(frozen=True)
class NativeStructureContract:
    """Validated portable contract for a preserved source PPTX package."""

    source_template: Path
    contract_path: Path
    source_sha256: str
    slide_size_emu: tuple[int, int]
    layouts: tuple[NativeLayoutSpec, ...]

    def layout(self, key: str) -> NativeLayoutSpec:
        for layout in self.layouts:
            if layout.key == key:
                return layout
        raise TemplateStructureError(
            f"native_structure.json has no layout key {key!r}"
        )


@dataclass(frozen=True)
class TemplateElementSpec:
    """One direct SVG child carrying explicit PPTX structure metadata."""

    element_id: str
    order: int
    tag: str
    layer: str | None = None
    placeholder: str | None = None
    placeholder_bounds: tuple[float, float, float, float] | None = None
    placeholder_idx: int | None = None
    is_background: bool = False

    def contract_signature(self) -> tuple[object, ...]:
        """Return metadata that must agree across slides sharing a structure."""
        return (
            self.element_id,
            self.tag,
            self.layer,
            self.placeholder,
            self.placeholder_bounds,
            self.placeholder_idx,
            self.is_background,
        )


@dataclass(frozen=True)
class TemplateSlideSpec:
    """Explicit structure contract parsed from one SVG slide."""

    slide_num: int
    svg_path: Path
    layout_key: str
    layout_name: str
    elements: tuple[TemplateElementSpec, ...]

    @property
    def master_elements(self) -> tuple[TemplateElementSpec, ...]:
        return tuple(item for item in self.elements if item.layer == "master")

    @property
    def layout_elements(self) -> tuple[TemplateElementSpec, ...]:
        return tuple(item for item in self.elements if item.layer == "layout")

    @property
    def placeholders(self) -> tuple[TemplateElementSpec, ...]:
        return tuple(item for item in self.elements if item.placeholder)

    @property
    def layout_contract(self) -> tuple[tuple[object, ...], ...]:
        return tuple(
            item.contract_signature()
            for item in self.elements
            if item.layer == "layout" or item.placeholder
        )


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1] if isinstance(elem.tag, str) else ""


def _svg_canvas(root: ET.Element) -> tuple[float, float, float, float]:
    raw_viewbox = (root.get("viewBox") or "").strip()
    values = [part for part in re.split(r"[\s,]+", raw_viewbox) if part]
    if len(values) != 4:
        return 0.0, 0.0, 0.0, 0.0
    try:
        x, y, width, height = (float(value) for value in values)
    except ValueError:
        return 0.0, 0.0, 0.0, 0.0
    if not all(math.isfinite(value) for value in (x, y, width, height)):
        return 0.0, 0.0, 0.0, 0.0
    return x, y, width, height


def _is_full_canvas_solid_rect(
    elem: ET.Element,
    canvas: tuple[float, float, float, float],
) -> bool:
    """Return whether a direct rect is eligible for scoped p:bg compilation."""
    if canvas[2] <= 0 or canvas[3] <= 0:
        return False
    if _local_tag(elem) != "rect":
        return False
    if any(elem.get(attr) for attr in ("transform", "filter", "clip-path")):
        return False
    try:
        geometry = (
            float(elem.get("x", "0")),
            float(elem.get("y", "0")),
            float(elem.get("width", "0")),
            float(elem.get("height", "0")),
        )
        corner_radius = (
            float(elem.get("rx", "0")),
            float(elem.get("ry", "0")),
        )
    except ValueError:
        return False
    if not all(math.isfinite(value) for value in (*geometry, *corner_radius)):
        return False
    if corner_radius != (0.0, 0.0):
        return False
    if any(abs(actual - expected) > 0.5 for actual, expected in zip(geometry, canvas)):
        return False
    fill = (elem.get("fill") or "").strip().lower()
    if not fill or fill == "none" or fill.startswith("url("):
        return False
    stroke = (elem.get("stroke") or "none").strip().lower()
    if stroke != "none":
        try:
            if float(elem.get("stroke-opacity", "1")) != 0:
                return False
        except ValueError:
            return False
    return True


def _portable_project_file(
    project_path: Path,
    raw_value: str,
    field_name: str,
    suffix: str,
) -> Path:
    """Resolve a project-relative structure file without allowing escape."""
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1].strip()
    if not value:
        raise TemplateStructureError(
            f"spec_lock.md pptx_structure.{field_name} cannot be empty"
        )
    candidate = Path(value)
    if candidate.is_absolute():
        raise TemplateStructureError(
            f"spec_lock.md pptx_structure.{field_name} must be project-relative"
        )
    root = project_path.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise TemplateStructureError(
            f"spec_lock.md pptx_structure.{field_name} escapes the project directory"
        ) from exc
    if resolved.suffix.lower() != suffix:
        raise TemplateStructureError(
            f"spec_lock.md pptx_structure.{field_name} must reference a {suffix} file"
        )
    if not resolved.is_file():
        raise TemplateStructureError(
            f"spec_lock.md pptx_structure.{field_name} does not exist: {candidate}"
        )
    return resolved


def load_pptx_structure_lock(project_path: Path) -> PptxStructureLock | None:
    """Load optional pptx_structure/pptx_layouts sections from spec_lock.md."""
    lock_path = project_path / "spec_lock.md"
    if not lock_path.is_file():
        return None
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise TemplateStructureError(f"Cannot read {lock_path}: {exc}") from exc

    sections: dict[str, list[tuple[str, str]]] = {}
    current_section: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections.setdefault(current_section, [])
            continue
        if current_section not in {"pptx_structure", "pptx_layouts"}:
            continue
        match = _LOCK_ROW_RE.fullmatch(line)
        if match:
            sections[current_section].append((match.group(1), match.group(2)))

    structure_rows = sections.get("pptx_structure", [])
    layout_rows = sections.get("pptx_layouts", [])
    if not structure_rows and not layout_rows:
        return None
    mode_rows = [value.strip().lower() for key, value in structure_rows if key == "mode"]
    if len(mode_rows) != 1:
        raise TemplateStructureError(
            "spec_lock.md pptx_structure requires exactly one '- mode:' row"
        )
    mode = mode_rows[0]
    if mode not in PPTX_STRUCTURE_MODES:
        allowed = ", ".join(sorted(PPTX_STRUCTURE_MODES))
        raise TemplateStructureError(
            f"spec_lock.md pptx_structure.mode must be one of: {allowed}"
        )

    adherence_rows = [
        value.strip().lower()
        for key, value in structure_rows
        if key == "template_adherence"
    ]
    if len(adherence_rows) > 1:
        raise TemplateStructureError(
            "spec_lock.md pptx_structure allows at most one "
            "'- template_adherence:' row"
        )
    template_adherence = adherence_rows[0] if adherence_rows else None
    if template_adherence and template_adherence not in TEMPLATE_ADHERENCE_MODES:
        allowed = ", ".join(sorted(TEMPLATE_ADHERENCE_MODES))
        raise TemplateStructureError(
            "spec_lock.md pptx_structure.template_adherence must be one of: "
            f"{allowed}"
        )
    if mode == "preserve" and template_adherence == "adaptive":
        raise TemplateStructureError(
            "spec_lock.md preserve mode requires template_adherence: strict; "
            "adaptive template use must export through baseline"
        )

    source_rows = [
        value for key, value in structure_rows if key == "source_template"
    ]
    contract_rows = [
        value for key, value in structure_rows if key == "native_structure"
    ]
    source_template = None
    native_structure = None
    if mode == "preserve":
        if len(source_rows) != 1 or len(contract_rows) != 1:
            raise TemplateStructureError(
                "spec_lock.md preserve mode requires exactly one '- source_template:' "
                "row and one '- native_structure:' row"
            )
        source_template = _portable_project_file(
            project_path,
            source_rows[0],
            "source_template",
            ".pptx",
        )
        native_structure = _portable_project_file(
            project_path,
            contract_rows[0],
            "native_structure",
            ".json",
        )
    elif source_rows or contract_rows:
        raise TemplateStructureError(
            "spec_lock.md source_template/native_structure rows are allowed only "
            "when pptx_structure.mode is preserve"
        )

    references: list[PptxLayoutReference] = []
    seen_slides: set[int] = set()
    for page_key, raw_value in layout_rows:
        page_match = _LOCK_PAGE_RE.fullmatch(page_key)
        if not page_match or int(page_match.group(1)) <= 0:
            raise TemplateStructureError(
                f"spec_lock.md pptx_layouts key {page_key!r} must be P<NN>"
            )
        slide_num = int(page_match.group(1))
        if slide_num in seen_slides:
            raise TemplateStructureError(
                f"spec_lock.md pptx_layouts repeats page P{slide_num:02d}"
            )
        seen_slides.add(slide_num)
        value_parts = raw_value.split("|", 1)
        layout_key = value_parts[0].strip()
        layout_name = value_parts[1].strip() if len(value_parts) == 2 else None
        if not _LAYOUT_KEY_RE.fullmatch(layout_key):
            raise TemplateStructureError(
                f"spec_lock.md P{slide_num:02d} has invalid layout key "
                f"{layout_key!r}"
            )
        if len(value_parts) == 2 and not layout_name:
            raise TemplateStructureError(
                f"spec_lock.md P{slide_num:02d} has an empty layout name"
            )
        references.append(PptxLayoutReference(
            slide_num=slide_num,
            layout_key=layout_key,
            layout_name=layout_name,
        ))

    if mode in {"template", "preserve"} and not references:
        raise TemplateStructureError(
            f"spec_lock.md {mode} mode requires one pptx_layouts row per page"
        )
    if mode not in {"template", "preserve"} and references:
        raise TemplateStructureError(
            "spec_lock.md pptx_layouts is allowed only when pptx_structure.mode "
            "is template or preserve"
        )
    return PptxStructureLock(
        mode=mode,
        template_adherence=template_adherence,
        layouts=tuple(sorted(references, key=lambda item: item.slide_num)),
        source_template=source_template,
        native_structure=native_structure,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _native_geometry(raw: Any, context: str) -> tuple[float, float, float, float] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TemplateStructureError(f"{context} geometry must be an object or null")
    try:
        values = tuple(float(raw[key]) for key in ("x", "y", "width", "height"))
    except (KeyError, TypeError, ValueError) as exc:
        raise TemplateStructureError(f"{context} geometry is invalid") from exc
    if not all(math.isfinite(value) for value in values) or values[2] <= 0 or values[3] <= 0:
        raise TemplateStructureError(f"{context} geometry must be finite and positive")
    return values


def load_native_structure_contract(
    structure_lock: PptxStructureLock,
) -> NativeStructureContract:
    """Load and verify the native structure bundle selected by preserve mode."""
    if structure_lock.mode != "preserve":
        raise TemplateStructureError(
            "native structure contracts are available only in preserve mode"
        )
    source_template = structure_lock.source_template
    contract_path = structure_lock.native_structure
    if source_template is None or contract_path is None:
        raise TemplateStructureError(
            "preserve mode is missing source_template or native_structure"
        )
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateStructureError(
            f"Cannot read native structure contract {contract_path}: {exc}"
        ) from exc
    if not isinstance(raw, dict) or raw.get("schema") != NATIVE_STRUCTURE_SCHEMA:
        raise TemplateStructureError(
            f"{contract_path.name} must use schema {NATIVE_STRUCTURE_SCHEMA!r}"
        )

    source = raw.get("source")
    expected_sha = source.get("sha256") if isinstance(source, dict) else None
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise TemplateStructureError(
            f"{contract_path.name} source.sha256 must be a lowercase SHA-256 digest"
        )
    actual_sha = _file_sha256(source_template)
    if actual_sha != expected_sha:
        raise TemplateStructureError(
            f"{source_template.name} does not match {contract_path.name} source.sha256"
        )

    slide_size = raw.get("slideSize")
    try:
        slide_size_emu = (
            int(slide_size["width_emu"]),
            int(slide_size["height_emu"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TemplateStructureError(
            f"{contract_path.name} slideSize must contain width_emu/height_emu"
        ) from exc
    if slide_size_emu[0] <= 0 or slide_size_emu[1] <= 0:
        raise TemplateStructureError(
            f"{contract_path.name} slideSize values must be positive"
        )

    raw_layouts = raw.get("layouts")
    if not isinstance(raw_layouts, list) or not raw_layouts:
        raise TemplateStructureError(
            f"{contract_path.name} must contain at least one layout"
        )
    layouts: list[NativeLayoutSpec] = []
    seen_keys: set[str] = set()
    seen_parts: set[str] = set()
    for index, item in enumerate(raw_layouts, start=1):
        context = f"{contract_path.name} layouts[{index}]"
        if not isinstance(item, dict):
            raise TemplateStructureError(f"{context} must be an object")
        key = str(item.get("key") or "")
        name = str(item.get("name") or "").strip()
        package_part = str(item.get("packagePart") or "")
        master_key = str(item.get("masterKey") or "")
        if not _LAYOUT_KEY_RE.fullmatch(key):
            raise TemplateStructureError(f"{context} has invalid key {key!r}")
        if key in seen_keys:
            raise TemplateStructureError(f"{context} repeats layout key {key!r}")
        if not name:
            raise TemplateStructureError(f"{context} name cannot be empty")
        if (
            not package_part.startswith("ppt/slideLayouts/")
            or ".." in Path(package_part).parts
            or not package_part.endswith(".xml")
        ):
            raise TemplateStructureError(
                f"{context} packagePart must be a ppt/slideLayouts/*.xml part"
            )
        if package_part in seen_parts:
            raise TemplateStructureError(
                f"{context} repeats package part {package_part!r}"
            )
        if not master_key:
            raise TemplateStructureError(f"{context} masterKey cannot be empty")

        raw_placeholders = item.get("placeholders", [])
        if not isinstance(raw_placeholders, list):
            raise TemplateStructureError(f"{context} placeholders must be a list")
        placeholders: list[NativePlaceholderSpec] = []
        for ph_index, placeholder in enumerate(raw_placeholders, start=1):
            ph_context = f"{context} placeholders[{ph_index}]"
            if not isinstance(placeholder, dict):
                raise TemplateStructureError(f"{ph_context} must be an object")
            semantic_role = str(placeholder.get("semanticRole") or "other")
            placeholder_type = str(placeholder.get("type") or "obj")
            raw_idx = placeholder.get("idx")
            try:
                placeholder_idx = int(raw_idx) if raw_idx is not None else None
            except (TypeError, ValueError) as exc:
                raise TemplateStructureError(
                    f"{ph_context} idx must be an integer or null"
                ) from exc
            if placeholder_idx is not None and placeholder_idx < 0:
                raise TemplateStructureError(f"{ph_context} idx cannot be negative")
            placeholders.append(NativePlaceholderSpec(
                semantic_role=semantic_role,
                placeholder_type=placeholder_type,
                idx=placeholder_idx,
                geometry=_native_geometry(placeholder.get("geometry"), ph_context),
            ))
        layouts.append(NativeLayoutSpec(
            key=key,
            name=name,
            package_part=package_part,
            master_key=master_key,
            placeholders=tuple(placeholders),
        ))
        seen_keys.add(key)
        seen_parts.add(package_part)

    try:
        with zipfile.ZipFile(source_template, "r") as package:
            package_parts = set(package.namelist())
    except (OSError, zipfile.BadZipFile) as exc:
        raise TemplateStructureError(
            f"Cannot open preserved source template {source_template}: {exc}"
        ) from exc
    missing_parts = sorted(seen_parts - package_parts)
    if missing_parts:
        raise TemplateStructureError(
            f"{source_template.name} is missing layout part(s): " + ", ".join(missing_parts)
        )

    return NativeStructureContract(
        source_template=source_template,
        contract_path=contract_path,
        source_sha256=expected_sha,
        slide_size_emu=slide_size_emu,
        layouts=tuple(layouts),
    )


def _parse_placeholder_bounds(
    raw: str | None,
    *,
    svg_path: Path,
    element_id: str,
) -> tuple[float, float, float, float] | None:
    if raw is None:
        return None
    parts = [part for part in re.split(r"[\s,]+", raw.strip()) if part]
    if len(parts) != 4:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} data-pptx-placeholder-bounds must be "
            "'x y width height'"
        )
    try:
        x, y, width, height = (float(part) for part in parts)
    except ValueError as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder bounds must be numeric"
        ) from exc
    if not all(math.isfinite(value) for value in (x, y, width, height)):
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder bounds must be finite"
        )
    if width <= 0 or height <= 0:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder width/height must be positive"
        )
    return x, y, width, height


def _parse_placeholder_idx(
    raw: str | None,
    *,
    svg_path: Path,
    element_id: str,
) -> int | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value or not value.isdigit():
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} data-pptx-placeholder-idx must be "
            "a non-negative integer"
        )
    return int(value)


def _validate_placeholder_element(
    elem: ET.Element,
    placeholder: str,
    *,
    svg_path: Path,
    element_id: str,
) -> None:
    tag = _local_tag(elem)
    if placeholder in _TEXT_PLACEHOLDERS and tag != "text":
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder '{placeholder}' must be "
            "declared on a direct <text> element"
        )
    if placeholder == "picture" and tag not in {"image", "svg"}:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} picture placeholder must be declared "
            "on a direct <image> or nested crop <svg> element"
        )
    if placeholder in {"chart", "table"}:
        native_kind = (elem.get("data-pptx-native") or "").strip().lower()
        if tag != "g" or native_kind != placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id} placeholder '{placeholder}' must be "
                f"a direct <g data-pptx-native=\"{placeholder}\"> marker"
            )


def parse_template_slide(svg_path: Path, slide_num: int) -> TemplateSlideSpec:
    """Parse one SVG's explicit template layout and structure elements."""
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: unable to parse SVG structure metadata: {exc}"
        ) from exc

    if _local_tag(root) != "svg":
        raise TemplateStructureError(f"{svg_path.name}: root element must be <svg>")

    layout_key = (root.get("data-pptx-layout") or "").strip()
    if not layout_key:
        raise TemplateStructureError(
            f"{svg_path.name}: template export requires root data-pptx-layout"
        )
    if not _LAYOUT_KEY_RE.fullmatch(layout_key):
        raise TemplateStructureError(
            f"{svg_path.name}: invalid data-pptx-layout {layout_key!r}; use 1-64 "
            "ASCII letters, digits, dots, underscores, or hyphens"
        )
    layout_name = (root.get("data-pptx-layout-name") or "").strip()
    if not layout_name:
        layout_name = re.sub(r"[-_.]+", " ", layout_key).strip().title() or layout_key

    illegal_root_attrs = sorted(
        attr for attr in _STRUCTURE_ATTRS
        if (
            attr not in {"data-pptx-layout", "data-pptx-layout-name"}
            and root.get(attr) is not None
        )
    )
    if illegal_root_attrs:
        raise TemplateStructureError(
            f"{svg_path.name}: root <svg> cannot use {', '.join(illegal_root_attrs)}"
        )

    id_counts: dict[str, int] = {}
    for elem in root.iter():
        element_id = elem.get("id")
        if element_id:
            id_counts[element_id] = id_counts.get(element_id, 0) + 1
    duplicate_ids = sorted(element_id for element_id, count in id_counts.items() if count > 1)
    if duplicate_ids:
        raise TemplateStructureError(
            f"{svg_path.name}: duplicate SVG id(s) are not allowed in template mode: "
            + ", ".join(duplicate_ids)
        )

    direct_children = set(root)
    for elem in root.iter():
        if elem is root or elem in direct_children:
            continue
        nested_attrs = sorted(attr for attr in _STRUCTURE_ATTRS if elem.get(attr) is not None)
        if nested_attrs:
            element_id = elem.get("id") or _local_tag(elem) or "<unnamed>"
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id} uses template metadata below the SVG "
                "root; structure metadata is allowed only on direct children"
            )

    elements: list[TemplateElementSpec] = []
    canvas = _svg_canvas(root)
    last_order_rank = -1
    visual_order = 0
    for elem in root:
        tag = _local_tag(elem)
        if tag in _NON_VISUAL_TAGS:
            continue

        element_id = (elem.get("id") or "").strip()
        layer_raw = elem.get("data-pptx-layer")
        layer = (layer_raw or "").strip().lower() or None
        placeholder_raw = elem.get("data-pptx-placeholder")
        placeholder = (
            (placeholder_raw or "").strip().lower() or None
        )
        bounds_raw = elem.get("data-pptx-placeholder-bounds")
        placeholder_idx_raw = elem.get("data-pptx-placeholder-idx")
        editable_raw = elem.get("data-pptx-editable")
        is_background = _is_full_canvas_solid_rect(elem, canvas)
        effective_layer = layer or ("slide" if is_background else None)

        if (
            elem.get("data-pptx-layout") is not None
            or elem.get("data-pptx-layout-name") is not None
        ):
            raise TemplateStructureError(
                f"{svg_path.name}: data-pptx-layout and data-pptx-layout-name belong "
                "on the root <svg> only"
            )
        if layer and layer not in _LAYERS:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has unsupported "
                f"data-pptx-layer={layer!r}"
            )
        if layer_raw is not None and layer is None:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has empty data-pptx-layer"
            )
        if placeholder and placeholder not in _PLACEHOLDERS:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has unsupported "
                f"data-pptx-placeholder={placeholder!r}"
            )
        if placeholder_raw is not None and placeholder is None:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has empty "
                "data-pptx-placeholder"
            )
        if effective_layer and placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} cannot be both a static "
                "structure/background layer and a content placeholder"
            )
        if layer == "slide" and not is_background:
            raise TemplateStructureError(
                f"{svg_path.name}: data-pptx-layer='slide' is allowed only on a "
                "direct full-canvas solid background rect"
            )
        if bounds_raw is not None and not placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has placeholder bounds without "
                "data-pptx-placeholder"
            )
        if placeholder_idx_raw is not None and not placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has placeholder idx without "
                "data-pptx-placeholder"
            )
        if (effective_layer or placeholder) and not element_id:
            raise TemplateStructureError(
                f"{svg_path.name}: direct <{tag}> with template metadata requires an id"
            )
        if editable_raw is not None:
            if not effective_layer or editable_raw.strip().lower() != "false":
                raise TemplateStructureError(
                    f"{svg_path.name}: data-pptx-editable currently supports only "
                    "'false' on master/layout elements or slide backgrounds"
                )

        if is_background:
            order_rank = {"master": 0, "layout": 1, "slide": 2}[effective_layer]
        elif effective_layer == "master":
            order_rank = 3
        elif effective_layer == "layout":
            order_rank = 4
        else:
            order_rank = 5
        if order_rank < last_order_rank:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} violates template paint order; "
                "use Master background, Layout background, Slide background, "
                "Master shapes, Layout shapes, then Slide content/placeholders"
            )
        last_order_rank = order_rank

        if placeholder:
            _validate_placeholder_element(
                elem,
                placeholder,
                svg_path=svg_path,
                element_id=element_id,
            )
        placeholder_bounds = _parse_placeholder_bounds(
            bounds_raw,
            svg_path=svg_path,
            element_id=element_id or tag,
        )
        placeholder_idx = _parse_placeholder_idx(
            placeholder_idx_raw,
            svg_path=svg_path,
            element_id=element_id or tag,
        )

        if effective_layer or placeholder:
            elements.append(TemplateElementSpec(
                element_id=element_id,
                order=visual_order,
                tag=tag,
                layer=effective_layer,
                placeholder=placeholder,
                placeholder_bounds=placeholder_bounds,
                placeholder_idx=placeholder_idx,
                is_background=is_background,
            ))
        visual_order += 1

    for scope in ("master", "layout", "slide"):
        backgrounds = [
            item for item in elements
            if item.layer == scope and item.is_background
        ]
        if len(backgrounds) > 1:
            raise TemplateStructureError(
                f"{svg_path.name}: template mode allows at most one {scope} "
                "solid background"
            )

    return TemplateSlideSpec(
        slide_num=slide_num,
        svg_path=svg_path,
        layout_key=layout_key,
        layout_name=layout_name,
        elements=tuple(elements),
    )


def parse_template_slides(svg_files: list[Path]) -> list[TemplateSlideSpec]:
    """Parse a deck and enforce cross-slide master/layout contracts."""
    specs = [
        parse_template_slide(svg_path, slide_num)
        for slide_num, svg_path in enumerate(svg_files, start=1)
    ]
    if not specs:
        raise TemplateStructureError("Template export requires at least one SVG slide")

    expected_master = tuple(
        item.contract_signature() for item in specs[0].master_elements
    )
    for spec in specs[1:]:
        actual_master = tuple(
            item.contract_signature() for item in spec.master_elements
        )
        if actual_master != expected_master:
            raise TemplateStructureError(
                f"{spec.svg_path.name}: master layer contract differs from "
                f"{specs[0].svg_path.name}; every template slide must repeat the same "
                "explicit master elements in the same order"
            )

    by_layout: dict[str, list[TemplateSlideSpec]] = {}
    for spec in specs:
        by_layout.setdefault(spec.layout_key, []).append(spec)
    for layout_key, layout_specs in by_layout.items():
        prototype = layout_specs[0]
        for spec in layout_specs[1:]:
            if spec.layout_name != prototype.layout_name:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: layout {layout_key!r} uses name "
                    f"{spec.layout_name!r}, expected {prototype.layout_name!r}"
                )
            if spec.layout_contract != prototype.layout_contract:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: layout {layout_key!r} structure differs "
                    f"from prototype {prototype.svg_path.name}; repeat the same layout "
                    "layers and placeholder ids/types in the same order"
                )
    return specs


def parse_preserve_slides(svg_files: list[Path]) -> list[TemplateSlideSpec]:
    """Parse preserve-mode slides before source master grouping is known."""
    specs = [
        parse_template_slide(svg_path, slide_num)
        for slide_num, svg_path in enumerate(svg_files, start=1)
    ]
    if not specs:
        raise TemplateStructureError("Preserve export requires at least one SVG slide")
    return specs


def template_lock_errors(
    specs: list[TemplateSlideSpec],
    structure_lock: PptxStructureLock,
) -> list[str]:
    """Return mismatches between parsed SVG layouts and the project lock."""
    if structure_lock.mode not in {"template", "preserve"}:
        return []
    errors: list[str] = []
    references = {
        reference.slide_num: reference
        for reference in structure_lock.layouts
    }
    actual_slides = {spec.slide_num for spec in specs}
    expected_slides = set(references)
    missing = sorted(actual_slides - expected_slides)
    extra = sorted(expected_slides - actual_slides)
    if missing:
        pages = ", ".join(f"P{slide_num:02d}" for slide_num in missing)
        errors.append(
            f"spec_lock.md pptx_layouts is missing generated page(s): {pages}"
        )
    if extra:
        pages = ", ".join(f"P{slide_num:02d}" for slide_num in extra)
        errors.append(
            f"spec_lock.md pptx_layouts references absent page(s): {pages}"
        )
    for spec in specs:
        reference = references.get(spec.slide_num)
        if reference is None:
            continue
        if spec.layout_key != reference.layout_key:
            errors.append(
                f"{spec.svg_path.name}: data-pptx-layout={spec.layout_key!r} "
                f"does not match spec_lock P{spec.slide_num:02d} layout key "
                f"{reference.layout_key!r}"
            )
        if reference.layout_name and spec.layout_name != reference.layout_name:
            errors.append(
                f"{spec.svg_path.name}: data-pptx-layout-name={spec.layout_name!r} "
                f"does not match spec_lock P{spec.slide_num:02d} layout name "
                f"{reference.layout_name!r}"
            )
    return errors


_PRESERVE_PLACEHOLDER_TYPES = {
    "title": frozenset({"title", "ctrTitle"}),
    "body": frozenset({"body", "subTitle", "obj"}),
    "picture": frozenset({"pic", "obj"}),
    "chart": frozenset({"chart", "obj"}),
    "table": frozenset({"tbl", "obj"}),
    "footer": frozenset({"ftr"}),
    "slide-number": frozenset({"sldNum"}),
}


def match_native_placeholders(
    spec: TemplateSlideSpec,
    layout: NativeLayoutSpec,
) -> tuple[tuple[TemplateElementSpec, NativePlaceholderSpec], ...]:
    """Match slide placeholder markers to source layout placeholder identities."""
    available = list(layout.placeholders)
    matches: list[tuple[TemplateElementSpec, NativePlaceholderSpec]] = []
    for item in spec.placeholders:
        allowed_types = _PRESERVE_PLACEHOLDER_TYPES.get(item.placeholder or "", frozenset())
        candidate_index = None
        for index, candidate in enumerate(available):
            if candidate.placeholder_type not in allowed_types:
                continue
            if item.placeholder_idx is not None and candidate.idx != item.placeholder_idx:
                continue
            candidate_index = index
            break
        if candidate_index is None:
            idx_note = (
                f" idx={item.placeholder_idx}"
                if item.placeholder_idx is not None
                else ""
            )
            raise TemplateStructureError(
                f"{spec.svg_path.name}: placeholder {item.element_id!r} "
                f"({item.placeholder}{idx_note}) has no compatible source placeholder "
                f"in layout {layout.key!r}"
            )
        matches.append((item, available.pop(candidate_index)))
    return tuple(matches)


def native_structure_lock_errors(
    specs: list[TemplateSlideSpec],
    structure_lock: PptxStructureLock,
    contract: NativeStructureContract,
) -> list[str]:
    """Return preserve-mode mismatches against the imported source contract."""
    if structure_lock.mode != "preserve":
        return []
    errors: list[str] = []
    references = {item.slide_num: item for item in structure_lock.layouts}
    contract_layouts = {layout.key: layout for layout in contract.layouts}

    for reference in structure_lock.layouts:
        layout = contract_layouts.get(reference.layout_key)
        if layout is None:
            errors.append(
                f"spec_lock.md P{reference.slide_num:02d} references unknown source "
                f"layout key {reference.layout_key!r}"
            )
            continue
        if reference.layout_name and reference.layout_name != layout.name:
            errors.append(
                f"spec_lock.md P{reference.slide_num:02d} layout name "
                f"{reference.layout_name!r} does not match source name {layout.name!r}"
            )

    master_contracts: dict[str, tuple[tuple[object, ...], ...]] = {}
    layout_contracts: dict[str, tuple[tuple[object, ...], ...]] = {}
    for spec in specs:
        reference = references.get(spec.slide_num)
        if reference is None:
            continue
        layout = contract_layouts.get(reference.layout_key)
        if layout is None:
            continue
        master_contract = tuple(
            item.contract_signature() for item in spec.master_elements
        )
        expected_master = master_contracts.setdefault(
            layout.master_key,
            master_contract,
        )
        if master_contract != expected_master:
            errors.append(
                f"{spec.svg_path.name}: preview master layer differs from another "
                f"page using source master {layout.master_key!r}"
            )
        expected_layout = layout_contracts.setdefault(
            layout.key,
            spec.layout_contract,
        )
        if spec.layout_contract != expected_layout:
            errors.append(
                f"{spec.svg_path.name}: preview layout/placeholder contract differs "
                f"from another page using source layout {layout.key!r}"
            )
        try:
            match_native_placeholders(spec, layout)
        except TemplateStructureError as exc:
            errors.append(str(exc))
    return errors


def validate_template_svg(svg_path: Path) -> list[str]:
    """Return per-file template metadata errors for quality-check integration."""
    try:
        parse_template_slide(svg_path, 1)
    except TemplateStructureError as exc:
        return [str(exc)]
    return []
