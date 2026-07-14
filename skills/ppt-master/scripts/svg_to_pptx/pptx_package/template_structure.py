#!/usr/bin/env python3
"""
PPT Master - Template Structure Metadata

Parse and validate explicit SVG metadata consumed by structured PPTX export.

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

from ..geometry_properties import (
    GeometryStyleError,
    materialize_inline_geometry_properties,
)


_NON_VISUAL_TAGS = frozenset({"defs", "title", "desc", "metadata", "style"})
_STRUCTURE_ATTRS = frozenset({
    "data-pptx-layer",
    "data-pptx-layout",
    "data-pptx-layout-kind",
    "data-pptx-layout-name",
    "data-pptx-master",
    "data-pptx-master-name",
    "data-pptx-placeholder",
    "data-pptx-placeholder-binding",
    "data-pptx-placeholder-bounds",
    "data-pptx-placeholder-carrier",
    "data-pptx-placeholder-idx",
    "data-pptx-editable",
})
_FLAT_FORBIDDEN_STRUCTURE_ATTRS = frozenset(
    _STRUCTURE_ATTRS - {"data-pptx-editable"}
)
_LAYERS = frozenset({"master", "layout", "slide"})
_PLACEHOLDERS = frozenset({
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
})
TEMPLATE_PLACEHOLDER_TYPES = {
    "title": "title",
    "subtitle": "subTitle",
    "body": "body",
    "picture": "pic",
    "chart": "chart",
    "table": "tbl",
    "object": "obj",
    "media": "media",
    "date": "dt",
    "footer": "ftr",
    "slide-number": "sldNum",
}
_TEXT_PLACEHOLDERS = frozenset({
    "title",
    "subtitle",
    "body",
    "date",
    "footer",
    "slide-number",
})
_OBJECT_PLACEHOLDER_TAGS = frozenset({
    "rect",
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "text",
    "image",
    "svg",
    "use",
})
_LAYOUT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MASTER_KEY_RE = _LAYOUT_KEY_RE
# Parse Markdown row syntax before validating each section's key grammar. Keeping
# those concerns separate prevents malformed keys from disappearing silently.
_LOCK_ROW_RE = re.compile(r"^-\s+([^:]+?)\s*:\s*(.*?)\s*$")
_LOCK_PAGE_RE = re.compile(r"^P(\d+)$")
PPTX_STRUCTURE_MODES = frozenset({"structured", "preserve", "flat"})
TEMPLATE_ADHERENCE_MODES = frozenset({"strict", "adaptive"})
PLACEHOLDER_BINDING_MODES = frozenset({"carrier", "proxy"})
_TEMPLATE_SKIN_ATTRS = frozenset({
    "color",
    "fill",
    "fill-opacity",
    "filter",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "opacity",
    "paint-order",
    "stop-color",
    "stop-opacity",
    "stroke",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-opacity",
    "stroke-width",
    "style",
    "text-decoration",
    "word-spacing",
})
_CSS_RULE_RE = re.compile(r"(?s)([^{}]+)\{([^{}]*)\}")
_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_CSS_ID_RE = re.compile(r"#([A-Za-z_][A-Za-z0-9_-]*)")
_CSS_CLASS_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_-]*)")
_CSS_ATTR_RE = re.compile(
    r"\[\s*([A-Za-z_:][A-Za-z0-9_.:-]*)"
    r"(?:\s*(?:[~|^$*]?=)\s*(['\"]?)([^\]'\"]+)\2)?\s*\]"
)
_CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
_CSS_TAG_RE = re.compile(r"(?:^|[\s>+~])([A-Za-z_][A-Za-z0-9_-]*|\*)")
NATIVE_STRUCTURE_SCHEMA = "ppt-master.native-structure.v1"
OOXML_UINT32_MAX = (1 << 32) - 1


class TemplateStructureError(RuntimeError):
    """Reject invalid or ambiguous template-structure metadata."""


@dataclass(frozen=True)
class PptxLayoutReference:
    """One spec_lock page-to-PowerPoint-layout assignment."""

    slide_num: int
    layout_key: str
    layout_name: str | None = None
    master_key: str | None = None


@dataclass(frozen=True)
class PptxLayoutDefinition:
    """One reusable PowerPoint Layout declared by a structured project lock."""

    layout_key: str
    master_key: str
    layout_name: str
    prototype_slide_num: int | None = None
    prototype_svg_path: Path | None = None


@dataclass(frozen=True)
class PptxMasterReference:
    """One named Master declared by the structured project lock."""

    master_key: str
    master_name: str


@dataclass(frozen=True)
class PptxPrototypeReference:
    """One spec_lock page-to-template-SVG prototype declaration."""

    slide_num: int
    template_basename: str
    svg_path: Path
    replication_mode: str | None = None


@dataclass(frozen=True)
class PptxStructureLock:
    """Optional project-level PPTX structure export policy."""

    mode: str
    template_adherence: str | None = None
    masters: tuple[PptxMasterReference, ...] = ()
    layout_definitions: tuple[PptxLayoutDefinition, ...] = ()
    layouts: tuple[PptxLayoutReference, ...] = ()
    prototypes: tuple[PptxPrototypeReference, ...] = ()
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
    placeholder_binding: str | None = None
    placeholder_carrier_tag: str | None = None
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
            self.placeholder_binding,
            self.placeholder_carrier_tag,
            self.is_background,
        )


@dataclass(frozen=True)
class TemplateSlideSpec:
    """Explicit structure contract parsed from one SVG slide."""

    slide_num: int
    svg_path: Path
    master_key: str
    master_name: str
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


def is_proxy_placeholder(item: TemplateElementSpec) -> bool:
    """Return whether a visible composite slot uses an invisible binding proxy."""
    return item.placeholder_binding == "proxy"


@dataclass(frozen=True)
class TemplatePlaceholderBinding:
    """Resolved PowerPoint identity for one template placeholder."""

    element: TemplateElementSpec
    placeholder_type: str
    assigned_idx: int | None

    @property
    def effective_idx(self) -> int:
        """Return the OOXML idx value after applying its default of zero."""
        return self.assigned_idx if self.assigned_idx is not None else 0


def template_placeholder_bindings(
    spec: TemplateSlideSpec,
) -> tuple[TemplatePlaceholderBinding, ...]:
    """Assign deterministic, collision-free PowerPoint placeholder identities."""
    next_idx = 1
    used_indices: dict[int, str] = {}
    bindings: list[TemplatePlaceholderBinding] = []
    for item in spec.placeholders:
        placeholder_type = TEMPLATE_PLACEHOLDER_TYPES.get(item.placeholder or "")
        if placeholder_type is None:
            raise TemplateStructureError(
                f"{spec.svg_path.name}: unsupported placeholder type "
                f"{item.placeholder!r}"
            )
        if item.placeholder == "title" and item.placeholder_idx is None:
            assigned_idx = None
        else:
            assigned_idx = (
                item.placeholder_idx
                if item.placeholder_idx is not None
                else next_idx
            )
        effective_idx = assigned_idx if assigned_idx is not None else 0
        if effective_idx > OOXML_UINT32_MAX:
            raise TemplateStructureError(
                f"{spec.svg_path.name}: layout {spec.layout_key!r} placeholder "
                f"{item.element_id!r} idx exceeds the OOXML UInt32 maximum "
                f"{OOXML_UINT32_MAX}"
            )
        previous = used_indices.get(effective_idx)
        if previous is not None:
            raise TemplateStructureError(
                f"{spec.svg_path.name}: layout {spec.layout_key!r} gives "
                f"placeholders {previous!r} and {item.element_id!r} the same "
                f"effective idx {effective_idx}; omitted idx defaults to 0 in OOXML"
            )
        used_indices[effective_idx] = item.element_id
        if assigned_idx is not None:
            next_idx = max(next_idx, assigned_idx + 1)
        bindings.append(TemplatePlaceholderBinding(
            element=item,
            placeholder_type=placeholder_type,
            assigned_idx=assigned_idx,
        ))
    return tuple(bindings)


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


def _template_replication_mode(template_dir: Path) -> str | None:
    """Read the optional replication mode from template design frontmatter."""
    spec_path = template_dir / "design_spec.md"
    try:
        lines = spec_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return None
        match = re.fullmatch(
            r"replication_mode\s*:\s*[\"']?(standard|fidelity|mirror)[\"']?",
            stripped,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).lower()
    return None


def _template_svg_path(
    template_dir: Path,
    raw_basename: str,
    context: str,
) -> tuple[str, Path]:
    """Resolve one flat template SVG basename inside the project workspace."""
    basename = (
        raw_basename[:-4]
        if raw_basename.lower().endswith(".svg")
        else raw_basename
    )
    if (
        not basename
        or basename in {".", ".."}
        or "/" in basename
        or "\\" in basename
        or any(ord(char) < 0x20 for char in basename)
    ):
        raise TemplateStructureError(
            f"spec_lock.md {context} has invalid template SVG basename "
            f"{raw_basename!r}"
        )
    svg_path = (template_dir / f"{basename}.svg").resolve()
    if svg_path.parent != template_dir or not svg_path.is_file():
        raise TemplateStructureError(
            f"spec_lock.md {context} references missing template SVG "
            f"templates/{basename}.svg"
        )
    return basename, svg_path


def load_pptx_structure_lock(project_path: Path) -> PptxStructureLock | None:
    """Load optional native-structure sections from spec_lock.md."""
    lock_path = project_path / "spec_lock.md"
    if not lock_path.is_file():
        return None
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise TemplateStructureError(f"Cannot read {lock_path}: {exc}") from exc

    sections: dict[str, list[tuple[str, str]]] = {}
    current_section: str | None = None
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections.setdefault(current_section, [])
            continue
        if current_section not in {
            "pptx_structure",
            "pptx_masters",
            "pptx_layouts",
            "page_pptx_layouts",
            "page_layouts",
        }:
            continue
        match = _LOCK_ROW_RE.fullmatch(line)
        if match:
            sections[current_section].append((
                match.group(1).strip(),
                match.group(2).strip(),
            ))
        elif re.match(r"^-\s+", line):
            raise TemplateStructureError(
                f"spec_lock.md {current_section} line {line_number} must use "
                "'- <key>: <value>' syntax"
            )

    structure_rows = sections.get("pptx_structure", [])
    master_rows = sections.get("pptx_masters", [])
    layout_rows = sections.get("pptx_layouts", [])
    page_layout_rows = sections.get("page_pptx_layouts", [])
    prototype_rows = sections.get("page_layouts", [])
    structure_section_present = "pptx_structure" in sections
    master_section_present = "pptx_masters" in sections
    layout_section_present = "pptx_layouts" in sections
    page_layout_section_present = "page_pptx_layouts" in sections
    prototype_section_present = "page_layouts" in sections
    if (
        not structure_rows
        and not master_rows
        and not layout_rows
        and not page_layout_rows
        and not prototype_rows
        and not structure_section_present
        and not master_section_present
        and not layout_section_present
        and not page_layout_section_present
        and not prototype_section_present
    ):
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
            "adaptive template use must export through structured mode"
        )
    if template_adherence and mode not in {"structured", "preserve"}:
        raise TemplateStructureError(
            "spec_lock.md template_adherence is allowed only in structured or "
            "preserve mode"
        )
    if any(key == "layout_strategy" for key, _value in structure_rows):
        raise TemplateStructureError(
            "spec_lock.md pptx_structure.layout_strategy is obsolete; SVG pages "
            "must declare their final structured Master/Layout contract directly"
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

    masters: list[PptxMasterReference] = []
    seen_master_keys: set[str] = set()
    for master_key, raw_name in master_rows:
        master_name = raw_name.strip()
        if not _MASTER_KEY_RE.fullmatch(master_key):
            raise TemplateStructureError(
                f"spec_lock.md has invalid Master key {master_key!r}; use 1-64 "
                "characters, start with an ASCII letter or digit, and use only "
                "ASCII letters, digits, dots, underscores, or hyphens"
            )
        if master_key in seen_master_keys:
            raise TemplateStructureError(
                f"spec_lock.md pptx_masters repeats Master key {master_key!r}"
            )
        if not master_name:
            raise TemplateStructureError(
                f"spec_lock.md Master {master_key!r} has an empty name"
            )
        seen_master_keys.add(master_key)
        masters.append(PptxMasterReference(master_key, master_name))

    if mode == "structured":
        if not master_rows:
            raise TemplateStructureError(
                "spec_lock.md structured mode requires a non-empty pptx_masters section"
            )
    elif master_section_present:
        raise TemplateStructureError(
            "spec_lock.md pptx_masters is allowed only when "
            "pptx_structure.mode is structured"
        )

    prototypes: list[PptxPrototypeReference] = []
    seen_prototype_slides: set[int] = set()
    template_dir = (project_path / "templates").resolve()
    template_replication_mode = _template_replication_mode(template_dir)
    if mode != "structured" and prototype_section_present:
        raise TemplateStructureError(
            "spec_lock.md page_layouts section is allowed only when pptx_structure.mode "
            "is structured"
        )
    for page_key, raw_value in prototype_rows:
        page_match = _LOCK_PAGE_RE.fullmatch(page_key)
        if not page_match or int(page_match.group(1)) <= 0:
            raise TemplateStructureError(
                f"spec_lock.md page_layouts key {page_key!r} must be P<NN>"
            )
        slide_num = int(page_match.group(1))
        if slide_num in seen_prototype_slides:
            raise TemplateStructureError(
                f"spec_lock.md page_layouts repeats page P{slide_num:02d}"
            )
        seen_prototype_slides.add(slide_num)
        raw_basename = raw_value.strip()
        basename, svg_path = _template_svg_path(
            template_dir,
            raw_basename,
            f"page_layouts P{slide_num:02d}",
        )
        prototypes.append(PptxPrototypeReference(
            slide_num=slide_num,
            template_basename=basename,
            svg_path=svg_path,
            replication_mode=template_replication_mode,
        ))

    if mode == "structured" and template_adherence and not prototypes:
        raise TemplateStructureError(
            "spec_lock.md structured template use requires one page_layouts row per page"
        )
    if prototypes and not template_adherence:
        raise TemplateStructureError(
            "spec_lock.md page_layouts requires template_adherence: strict or adaptive"
        )

    layout_definitions: list[PptxLayoutDefinition] = []
    references: list[PptxLayoutReference] = []
    if mode == "structured":
        if not layout_rows:
            raise TemplateStructureError(
                "spec_lock.md structured mode requires a non-empty "
                "pptx_layouts definition section"
            )
        seen_layout_keys: set[str] = set()
        for layout_key, raw_value in layout_rows:
            if not _LAYOUT_KEY_RE.fullmatch(layout_key):
                raise TemplateStructureError(
                    f"spec_lock.md has invalid Layout key {layout_key!r}; use 1-64 "
                    "characters, start with an ASCII letter or digit, and use only "
                    "ASCII letters, digits, dots, underscores, or hyphens"
                )
            if layout_key in seen_layout_keys:
                raise TemplateStructureError(
                    f"spec_lock.md pptx_layouts repeats Layout key {layout_key!r}"
                )
            seen_layout_keys.add(layout_key)
            parts = [part.strip() for part in raw_value.split("|")]
            if len(parts) != 3 or not all(parts):
                raise TemplateStructureError(
                    f"spec_lock.md Layout {layout_key!r} must be "
                    "'<master_key> | <PowerPoint layout name> | "
                    "<P<NN> or template:<basename>>'"
                )
            master_key, layout_name, raw_source = parts
            if not _MASTER_KEY_RE.fullmatch(master_key):
                raise TemplateStructureError(
                    f"spec_lock.md Layout {layout_key!r} has invalid Master key "
                    f"{master_key!r}"
                )
            if master_key not in seen_master_keys:
                raise TemplateStructureError(
                    f"spec_lock.md Layout {layout_key!r} references undeclared "
                    f"Master {master_key!r}"
                )
            prototype_slide_num: int | None = None
            prototype_svg_path: Path | None = None
            page_match = _LOCK_PAGE_RE.fullmatch(raw_source)
            if page_match and int(page_match.group(1)) > 0:
                prototype_slide_num = int(page_match.group(1))
            elif raw_source.startswith("template:"):
                raw_basename = raw_source.split(":", 1)[1].strip()
                _basename, prototype_svg_path = _template_svg_path(
                    template_dir,
                    raw_basename,
                    f"pptx_layouts Layout {layout_key!r}",
                )
            else:
                raise TemplateStructureError(
                    f"spec_lock.md Layout {layout_key!r} prototype source must be "
                    f"P<NN> or template:<basename>; found {raw_source!r}"
                )
            layout_definitions.append(PptxLayoutDefinition(
                layout_key=layout_key,
                master_key=master_key,
                layout_name=layout_name,
                prototype_slide_num=prototype_slide_num,
                prototype_svg_path=prototype_svg_path,
            ))

        seen_slides: set[int] = set()
        for page_key, raw_value in page_layout_rows:
            page_match = _LOCK_PAGE_RE.fullmatch(page_key)
            if not page_match or int(page_match.group(1)) <= 0:
                raise TemplateStructureError(
                    f"spec_lock.md page_pptx_layouts key {page_key!r} must be P<NN>"
                )
            slide_num = int(page_match.group(1))
            if slide_num in seen_slides:
                raise TemplateStructureError(
                    "spec_lock.md page_pptx_layouts repeats page "
                    f"P{slide_num:02d}"
                )
            seen_slides.add(slide_num)
            layout_key = raw_value.strip()
            if not _LAYOUT_KEY_RE.fullmatch(layout_key):
                raise TemplateStructureError(
                    f"spec_lock.md P{slide_num:02d} has invalid Layout key "
                    f"{layout_key!r}"
                )
            if layout_key not in seen_layout_keys:
                raise TemplateStructureError(
                    f"spec_lock.md P{slide_num:02d} references undeclared Layout "
                    f"{layout_key!r}"
                )
            references.append(PptxLayoutReference(
                slide_num=slide_num,
                layout_key=layout_key,
            ))
        if not references:
            raise TemplateStructureError(
                "spec_lock.md structured mode requires one page_pptx_layouts "
                "assignment per generated page"
            )
        unused_masters = sorted(
            seen_master_keys - {
                definition.master_key for definition in layout_definitions
            }
        )
        if unused_masters:
            raise TemplateStructureError(
                "spec_lock.md pptx_masters contains Master key(s) without a "
                "Layout definition: " + ", ".join(unused_masters)
            )
    elif mode == "preserve":
        if page_layout_section_present:
            raise TemplateStructureError(
                "spec_lock.md page_pptx_layouts is reserved for structured mode; "
                "preserve mode maps source Layouts directly in pptx_layouts"
            )
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
            parts = [part.strip() for part in raw_value.split("|")]
            if len(parts) not in {1, 2} or not parts[0]:
                raise TemplateStructureError(
                    f"spec_lock.md P{slide_num:02d} preserve mapping must be "
                    "'<layout_key>' or '<layout_key> | <PowerPoint layout name>'"
                )
            layout_key = parts[0]
            if not _LAYOUT_KEY_RE.fullmatch(layout_key):
                raise TemplateStructureError(
                    f"spec_lock.md P{slide_num:02d} has invalid Layout key "
                    f"{layout_key!r}"
                )
            references.append(PptxLayoutReference(
                slide_num=slide_num,
                layout_key=layout_key,
                layout_name=parts[1] if len(parts) == 2 else None,
            ))
        if not references:
            raise TemplateStructureError(
                "spec_lock.md preserve mode requires one pptx_layouts row per page"
            )
    else:
        if layout_section_present or page_layout_section_present:
            raise TemplateStructureError(
                "spec_lock.md pptx_layouts/page_pptx_layouts sections are not "
                "allowed when pptx_structure.mode is flat"
            )
    return PptxStructureLock(
        mode=mode,
        template_adherence=template_adherence,
        masters=tuple(masters),
        layout_definitions=tuple(layout_definitions),
        layouts=tuple(sorted(references, key=lambda item: item.slide_num)),
        prototypes=tuple(sorted(prototypes, key=lambda item: item.slide_num)),
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
    parsed = int(value)
    if parsed > OOXML_UINT32_MAX:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} data-pptx-placeholder-idx must be "
            f"at most {OOXML_UINT32_MAX}"
        )
    return parsed


def _validate_placeholder_carrier(
    carrier: ET.Element,
    placeholder: str,
    *,
    svg_path: Path,
    element_id: str,
) -> None:
    tag = _local_tag(carrier)
    if placeholder in _TEXT_PLACEHOLDERS and tag != "text":
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} placeholder '{placeholder}' must be "
            "carried by one direct <text> child"
        )
    if placeholder == "picture" and tag not in {"image", "svg"}:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} picture placeholder must be declared "
            "with one direct <image> or crop <svg> carrier"
        )
    if placeholder == "media" and tag not in {"image", "svg"}:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} media placeholder must be declared "
            "with one direct <image> or crop <svg> carrier"
        )
    if placeholder == "object" and tag not in _OBJECT_PLACEHOLDER_TAGS:
        raise TemplateStructureError(
            f"{svg_path.name}: {element_id} object placeholder carrier must be "
            "one direct text, image, or basic SVG shape"
        )
    if placeholder in {"chart", "table"}:
        native_kind = (carrier.get("data-pptx-native") or "").strip().lower()
        if tag != "g" or native_kind != placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id} placeholder '{placeholder}' must be "
                f"carried by one direct <g data-pptx-native=\"{placeholder}\"> marker"
            )


def _structure_attrs(elem: ET.Element) -> list[str]:
    return sorted(attr for attr in _STRUCTURE_ATTRS if elem.get(attr) is not None)


def parse_template_slide(
    svg_path: Path,
    slide_num: int,
    *,
    structured: bool = True,
) -> TemplateSlideSpec:
    """Parse one SVG's explicit template layout and structure elements."""
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: unable to parse SVG structure metadata: {exc}"
        ) from exc

    try:
        materialize_inline_geometry_properties(root)
    except GeometryStyleError as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: invalid inline geometry: {exc}"
        ) from exc

    if _local_tag(root) != "svg":
        raise TemplateStructureError(f"{svg_path.name}: root element must be <svg>")

    master_key = (root.get("data-pptx-master") or "").strip()
    master_name = (root.get("data-pptx-master-name") or "").strip()
    if structured and not master_key:
        raise TemplateStructureError(
            f"{svg_path.name}: structured export requires root data-pptx-master"
        )
    if structured and not master_name:
        raise TemplateStructureError(
            f"{svg_path.name}: structured export requires root data-pptx-master-name"
        )
    if not master_key:
        master_key = "preserved-source"
    if not master_name:
        master_name = "Preserved Source Master"
    if not _MASTER_KEY_RE.fullmatch(master_key):
        raise TemplateStructureError(
            f"{svg_path.name}: invalid data-pptx-master {master_key!r}; use 1-64 "
            "ASCII letters, digits, dots, underscores, or hyphens"
        )

    layout_key = (root.get("data-pptx-layout") or "").strip()
    if not layout_key:
        raise TemplateStructureError(
            f"{svg_path.name}: explicit Layout export requires root data-pptx-layout"
        )
    if not _LAYOUT_KEY_RE.fullmatch(layout_key):
        raise TemplateStructureError(
            f"{svg_path.name}: invalid data-pptx-layout {layout_key!r}; use 1-64 "
            "ASCII letters, digits, dots, underscores, or hyphens"
        )
    layout_name = (root.get("data-pptx-layout-name") or "").strip()
    if structured and not layout_name:
        raise TemplateStructureError(
            f"{svg_path.name}: structured export requires root data-pptx-layout-name"
        )
    if not layout_name:
        layout_name = re.sub(r"[-_.]+", " ", layout_key).strip().title() or layout_key
    if structured and root.get("data-pptx-layout-kind") is not None:
        raise TemplateStructureError(
            f"{svg_path.name}: data-pptx-layout-kind is obsolete; the root "
            "Master/Layout identity is already final"
        )

    illegal_root_attrs = sorted(
        attr for attr in _STRUCTURE_ATTRS
        if (
            attr not in {
                "data-pptx-layout",
                "data-pptx-layout-name",
                "data-pptx-master",
                "data-pptx-master-name",
            }
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
            f"{svg_path.name}: duplicate SVG id(s) are not allowed in explicit Layout mode: "
            + ", ".join(duplicate_ids)
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
        binding_raw = elem.get("data-pptx-placeholder-binding")
        carrier_raw = elem.get("data-pptx-placeholder-carrier")
        editable_raw = elem.get("data-pptx-editable")
        is_background = _is_full_canvas_solid_rect(elem, canvas)
        effective_layer = layer or ("slide" if is_background else None)

        if (
            elem.get("data-pptx-layout") is not None
            or elem.get("data-pptx-layout-name") is not None
            or elem.get("data-pptx-master") is not None
            or elem.get("data-pptx-master-name") is not None
        ):
            raise TemplateStructureError(
                f"{svg_path.name}: Master/Layout identity attributes belong on "
                "the root <svg> only"
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
        if structured and layer in {"master", "layout"} and tag == "g":
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} is a <g> on the {layer} "
                "layer; Master/Layout fixed elements must be root-level atoms"
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
        if binding_raw is not None and not placeholder:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} has placeholder binding "
                "without data-pptx-placeholder"
            )
        if carrier_raw is not None:
            raise TemplateStructureError(
                f"{svg_path.name}: {element_id or tag} declares "
                "data-pptx-placeholder-carrier on a root child; the marker belongs "
                "on the direct child inside a placeholder <g>"
            )
        if (effective_layer or placeholder) and not element_id:
            raise TemplateStructureError(
                f"{svg_path.name}: direct <{tag}> with Layout metadata requires an id"
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

        placeholder_bounds = _parse_placeholder_bounds(
            bounds_raw,
            svg_path=svg_path,
            element_id=element_id or tag,
        )
        if structured and placeholder and placeholder_bounds is None:
            raise TemplateStructureError(
                f"{svg_path.name}: Layout placeholder {element_id!r} requires "
                "explicit data-pptx-placeholder-bounds; define the "
                "reusable frame from the design zone, not the current text bounds"
            )
        placeholder_idx = _parse_placeholder_idx(
            placeholder_idx_raw,
            svg_path=svg_path,
            element_id=element_id or tag,
        )

        placeholder_binding: str | None = None
        placeholder_carrier_tag: str | None = None
        if placeholder and structured:
            if tag != "g":
                raise TemplateStructureError(
                    f"{svg_path.name}: placeholder {element_id!r} must be declared "
                    "on a root-level <g> authoring boundary"
                )
            wrapper_visual_attrs = sorted(
                name
                for name in elem.attrib
                if name != "id" and not name.startswith("data-pptx-")
            )
            if wrapper_visual_attrs:
                raise TemplateStructureError(
                    f"{svg_path.name}: placeholder group {element_id!r} must be a "
                    "render-neutral authoring boundary; move these attributes to "
                    "its content: " + ", ".join(wrapper_visual_attrs)
                )
            placeholder_binding = (binding_raw or "carrier").strip().lower()
            if binding_raw is not None and not binding_raw.strip():
                raise TemplateStructureError(
                    f"{svg_path.name}: placeholder {element_id!r} has an empty "
                    "data-pptx-placeholder-binding"
                )
            if placeholder_binding not in PLACEHOLDER_BINDING_MODES:
                allowed = ", ".join(sorted(PLACEHOLDER_BINDING_MODES))
                raise TemplateStructureError(
                    f"{svg_path.name}: placeholder {element_id!r} binding must be "
                    f"one of: {allowed}"
                )
            visual_children = [
                child for child in elem if _local_tag(child) not in _NON_VISUAL_TAGS
            ]
            carrier_children = [
                child
                for child in visual_children
                if (child.get("data-pptx-placeholder-carrier") or "")
                .strip()
                .lower()
                == "true"
            ]
            for child in elem:
                marker = child.get("data-pptx-placeholder-carrier")
                if marker is not None and marker.strip().lower() != "true":
                    raise TemplateStructureError(
                        f"{svg_path.name}: placeholder {element_id!r} carrier marker "
                        "must be exactly 'true'"
                    )
                illegal_child_attrs = [
                    attr
                    for attr in _structure_attrs(child)
                    if attr != "data-pptx-placeholder-carrier"
                ]
                if illegal_child_attrs:
                    raise TemplateStructureError(
                        f"{svg_path.name}: placeholder {element_id!r} child uses "
                        "nested structure metadata: " + ", ".join(illegal_child_attrs)
                    )
                for descendant in child.iter():
                    if descendant is child:
                        continue
                    nested_attrs = _structure_attrs(descendant)
                    if nested_attrs:
                        nested_id = descendant.get("id") or _local_tag(descendant)
                        raise TemplateStructureError(
                            f"{svg_path.name}: {nested_id} uses nested structure "
                            "metadata: " + ", ".join(nested_attrs)
                        )
            if placeholder_binding == "proxy":
                if placeholder != "object":
                    raise TemplateStructureError(
                        f"{svg_path.name}: placeholder {element_id!r} may use proxy "
                        "binding only with data-pptx-placeholder='object'"
                    )
                if carrier_children:
                    raise TemplateStructureError(
                        f"{svg_path.name}: proxy placeholder {element_id!r} must not "
                        "declare a carrier child"
                    )
                if not visual_children:
                    raise TemplateStructureError(
                        f"{svg_path.name}: proxy placeholder {element_id!r} must "
                        "contain visible Slide-local content"
                    )
            else:
                if len(visual_children) != 1 or len(carrier_children) != 1:
                    raise TemplateStructureError(
                        f"{svg_path.name}: carrier placeholder {element_id!r} must "
                        "contain exactly one visual direct child and mark it "
                        "data-pptx-placeholder-carrier='true'"
                    )
                carrier = carrier_children[0]
                placeholder_carrier_tag = _local_tag(carrier)
                _validate_placeholder_carrier(
                    carrier,
                    placeholder,
                    svg_path=svg_path,
                    element_id=element_id,
                )
        elif placeholder:
            placeholder_binding = "carrier"
            placeholder_carrier_tag = tag
            _validate_placeholder_carrier(
                elem,
                placeholder,
                svg_path=svg_path,
                element_id=element_id,
            )
        else:
            for descendant in elem.iter():
                if descendant is elem:
                    continue
                nested_attrs = _structure_attrs(descendant)
                if nested_attrs:
                    nested_id = descendant.get("id") or _local_tag(descendant)
                    raise TemplateStructureError(
                        f"{svg_path.name}: {nested_id} uses structure metadata below "
                        "the SVG root: " + ", ".join(nested_attrs)
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
                placeholder_binding=placeholder_binding,
                placeholder_carrier_tag=placeholder_carrier_tag,
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
                f"{svg_path.name}: explicit Layout mode allows at most one {scope} "
                "solid background"
            )

    spec = TemplateSlideSpec(
        slide_num=slide_num,
        svg_path=svg_path,
        master_key=master_key,
        master_name=master_name,
        layout_key=layout_key,
        layout_name=layout_name,
        elements=tuple(elements),
    )
    return spec


def _validate_template_slide_contracts(
    specs: list[TemplateSlideSpec],
) -> None:
    """Enforce cross-prototype Master and Layout structure identity."""
    by_master: dict[str, list[TemplateSlideSpec]] = {}
    for spec in specs:
        by_master.setdefault(spec.master_key, []).append(spec)
    for master_key, master_specs in by_master.items():
        prototype = master_specs[0]
        expected_master = tuple(
            item.contract_signature() for item in prototype.master_elements
        )
        for spec in master_specs[1:]:
            if spec.master_name != prototype.master_name:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: Master {master_key!r} uses name "
                    f"{spec.master_name!r}, expected {prototype.master_name!r}"
                )
            actual_master = tuple(
                item.contract_signature() for item in spec.master_elements
            )
            if actual_master != expected_master:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: Master {master_key!r} contract differs "
                    f"from {prototype.svg_path.name}; slides sharing one Master must "
                    "repeat the same root-level atoms in the same order"
                )

    by_layout: dict[str, list[TemplateSlideSpec]] = {}
    for spec in specs:
        by_layout.setdefault(spec.layout_key, []).append(spec)
    for layout_key, layout_specs in by_layout.items():
        prototype = layout_specs[0]
        template_placeholder_bindings(prototype)
        for spec in layout_specs[1:]:
            if spec.layout_name != prototype.layout_name:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: layout {layout_key!r} uses name "
                    f"{spec.layout_name!r}, expected {prototype.layout_name!r}"
                )
            if spec.master_key != prototype.master_key:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: globally unique layout {layout_key!r} "
                    f"belongs to Master {spec.master_key!r}, expected "
                    f"{prototype.master_key!r}"
                )
            if spec.layout_contract != prototype.layout_contract:
                raise TemplateStructureError(
                    f"{spec.svg_path.name}: layout {layout_key!r} structure differs "
                    f"from prototype {prototype.svg_path.name}; repeat the same layout "
                    "layers and placeholder ids/types in the same order"
                )


def parse_template_slides(svg_files: list[Path]) -> list[TemplateSlideSpec]:
    """Parse a deck and enforce cross-slide master/layout contracts."""
    specs = [
        parse_template_slide(svg_path, slide_num)
        for slide_num, svg_path in enumerate(svg_files, start=1)
    ]
    if not specs:
        raise TemplateStructureError(
            "Explicit Layout export requires at least one SVG slide"
        )
    _validate_template_slide_contracts(specs)
    return specs


def parse_optional_layout_slides(
    svg_files: list[Path],
) -> list[TemplateSlideSpec] | None:
    """Parse an all-or-none structured Layout contract, or return no metadata."""
    roots: list[tuple[Path, ET.Element]] = []
    has_structure_metadata = False
    for svg_path in svg_files:
        try:
            root = ET.parse(svg_path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise TemplateStructureError(
                f"{svg_path.name}: unable to inspect SVG Layout metadata: {exc}"
            ) from exc
        roots.append((svg_path, root))
        has_structure_metadata = has_structure_metadata or any(
            elem.get(attr) is not None
            for elem in root.iter()
            for attr in _STRUCTURE_ATTRS
        )

    if not has_structure_metadata:
        return None

    missing_master_keys = [
        svg_path.name
        for svg_path, root in roots
        if not (root.get("data-pptx-master") or "").strip()
    ]
    missing_master_names = [
        svg_path.name
        for svg_path, root in roots
        if not (root.get("data-pptx-master-name") or "").strip()
    ]
    missing_keys = [
        svg_path.name
        for svg_path, root in roots
        if not (root.get("data-pptx-layout") or "").strip()
    ]
    missing_names = [
        svg_path.name
        for svg_path, root in roots
        if not (root.get("data-pptx-layout-name") or "").strip()
    ]
    if missing_master_keys or missing_master_names or missing_keys or missing_names:
        missing_fields: list[str] = []
        if missing_master_keys:
            missing_fields.append(
                "data-pptx-master: " + ", ".join(missing_master_keys)
            )
        if missing_master_names:
            missing_fields.append(
                "data-pptx-master-name: " + ", ".join(missing_master_names)
            )
        if missing_keys:
            missing_fields.append(
                "data-pptx-layout: " + ", ".join(missing_keys)
            )
        if missing_names:
            missing_fields.append(
                "data-pptx-layout-name: " + ", ".join(missing_names)
            )
        raise TemplateStructureError(
            "Explicit Layout metadata is all-or-none: once any SVG uses PPTX "
            "structure metadata, every generated page root must declare "
            "Master/Layout keys and names with non-empty values; "
            "missing "
            + "; ".join(missing_fields)
        )
    return parse_template_slides(svg_files)


def flat_structure_metadata_errors(svg_files: list[Path]) -> list[str]:
    """Return every Master/Layout marker forbidden by flat export."""
    errors: list[str] = []
    for svg_path in svg_files:
        try:
            root = ET.parse(svg_path).getroot()
        except (OSError, ET.ParseError) as exc:
            errors.append(
                f"{svg_path.name}: unable to inspect flat-mode metadata: {exc}"
            )
            continue
        for elem in root.iter():
            attrs = sorted(
                attr
                for attr in _FLAT_FORBIDDEN_STRUCTURE_ATTRS
                if elem.get(attr) is not None
            )
            if not attrs:
                continue
            element_id = (elem.get("id") or _local_tag(elem)).strip()
            errors.append(
                f"{svg_path.name}: flat mode forbids Master/Layout structure "
                f"metadata on {element_id!r}: " + ", ".join(attrs)
            )
    return errors


def parse_preserve_slides(svg_files: list[Path]) -> list[TemplateSlideSpec]:
    """Parse preserve-mode slides before source master grouping is known."""
    specs = [
        parse_template_slide(svg_path, slide_num, structured=False)
        for slide_num, svg_path in enumerate(svg_files, start=1)
    ]
    if not specs:
        raise TemplateStructureError("Preserve export requires at least one SVG slide")
    return specs


def structured_layout_definition_files(
    specs: list[TemplateSlideSpec],
    structure_lock: PptxStructureLock,
) -> list[Path]:
    """Validate the unique Layout roster and return unused prototype SVGs.

    A generated page can be the carrier for a used Layout definition. A Layout
    with no generated page must point at one installed template SVG; the builder
    converts that SVG on an internal trailing slide and removes the carrier slide
    after registering the reusable Layout.
    """
    if structure_lock.mode != "structured":
        return []
    definitions = {
        definition.layout_key: definition
        for definition in structure_lock.layout_definitions
    }
    specs_by_slide = {spec.slide_num: spec for spec in specs}
    used_layout_keys = {spec.layout_key for spec in specs}
    master_names = {
        master.master_key: master.master_name
        for master in structure_lock.masters
    }
    combined_specs = list(specs)
    definition_files: list[Path] = []
    next_slide_num = max(specs_by_slide, default=0) + 1
    for definition in structure_lock.layout_definitions:
        if definition.prototype_slide_num is not None:
            prototype = specs_by_slide.get(definition.prototype_slide_num)
            if prototype is None:
                raise TemplateStructureError(
                    f"spec_lock.md Layout {definition.layout_key!r} uses missing "
                    f"prototype page P{definition.prototype_slide_num:02d}"
                )
        elif definition.prototype_svg_path is not None:
            prototype = parse_template_slide(
                definition.prototype_svg_path,
                next_slide_num,
            )
            next_slide_num += 1
            combined_specs.append(prototype)
            if definition.layout_key not in used_layout_keys:
                definition_files.append(definition.prototype_svg_path)
        else:
            raise TemplateStructureError(
                f"spec_lock.md Layout {definition.layout_key!r} has no prototype"
            )
        expected_master_name = master_names.get(definition.master_key)
        if (
            prototype.layout_key != definition.layout_key
            or prototype.layout_name != definition.layout_name
            or prototype.master_key != definition.master_key
            or prototype.master_name != expected_master_name
        ):
            raise TemplateStructureError(
                f"spec_lock.md Layout {definition.layout_key!r} definition does "
                f"not match prototype {prototype.svg_path.name} root identity"
            )
    missing_definitions = sorted(used_layout_keys - set(definitions))
    if missing_definitions:
        raise TemplateStructureError(
            "spec_lock.md pptx_layouts is missing generated Layout key(s): "
            + ", ".join(missing_definitions)
        )
    _validate_template_slide_contracts(combined_specs)
    return definition_files


def template_lock_errors(
    specs: list[TemplateSlideSpec],
    structure_lock: PptxStructureLock,
) -> list[str]:
    """Return mismatches between parsed SVG layouts and the project lock."""
    if structure_lock.mode not in {"structured", "preserve"}:
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
    assignment_section = (
        "page_pptx_layouts"
        if structure_lock.mode == "structured"
        else "pptx_layouts"
    )
    if missing:
        pages = ", ".join(f"P{slide_num:02d}" for slide_num in missing)
        errors.append(
            f"spec_lock.md {assignment_section} is missing generated page(s): "
            f"{pages}"
        )
    if extra:
        pages = ", ".join(f"P{slide_num:02d}" for slide_num in extra)
        errors.append(
            f"spec_lock.md {assignment_section} references absent page(s): "
            f"{pages}"
        )
    for spec in specs:
        reference = references.get(spec.slide_num)
        if reference is None:
            continue
        if spec.layout_key != reference.layout_key:
            errors.append(
                f"{spec.svg_path.name}: data-pptx-layout={spec.layout_key!r} "
                f"does not match spec_lock P{spec.slide_num:02d} Layout key "
                f"{reference.layout_key!r}"
            )
        if structure_lock.mode == "preserve":
            if reference.layout_name and spec.layout_name != reference.layout_name:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-layout-name="
                    f"{spec.layout_name!r} does not match spec_lock "
                    f"P{spec.slide_num:02d} Layout name "
                    f"{reference.layout_name!r}"
                )
    if structure_lock.mode == "structured":
        definitions = {
            definition.layout_key: definition
            for definition in structure_lock.layout_definitions
        }
        master_names = {
            master.master_key: master.master_name for master in structure_lock.masters
        }
        for spec in specs:
            definition = definitions.get(spec.layout_key)
            if definition is not None:
                if spec.layout_name != definition.layout_name:
                    errors.append(
                        f"{spec.svg_path.name}: data-pptx-layout-name="
                        f"{spec.layout_name!r} does not match Layout "
                        f"{spec.layout_key!r} name {definition.layout_name!r}"
                    )
                if spec.master_key != definition.master_key:
                    errors.append(
                        f"{spec.svg_path.name}: data-pptx-master="
                        f"{spec.master_key!r} does not match Layout "
                        f"{spec.layout_key!r} Master {definition.master_key!r}"
                    )
            expected_name = master_names.get(spec.master_key)
            if expected_name is not None and spec.master_name != expected_name:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-master-name="
                    f"{spec.master_name!r} does not match spec_lock Master "
                    f"{spec.master_key!r} name {expected_name!r}"
                )
        try:
            structured_layout_definition_files(specs, structure_lock)
        except TemplateStructureError as exc:
            errors.append(str(exc))
    return errors


def _signature_attr_value(
    name: str,
    value: str,
    *,
    svg_path: Path | None,
    asset_identity: bool,
) -> str:
    """Normalize portable asset references without weakening visual identity."""
    if name.rsplit("}", 1)[-1] != "href":
        return value
    if asset_identity:
        if value.startswith("#") or "://" in value:
            return value
        if value.startswith("data:"):
            return "data-sha256:" + hashlib.sha256(
                value.encode("utf-8")
            ).hexdigest()
        if svg_path is None:
            raise TemplateStructureError(
                "literal asset comparison requires the source SVG path"
            )
        asset_path = (svg_path.parent / value).resolve()
        if not asset_path.is_file():
            raise TemplateStructureError(
                f"{svg_path.name}: mirror asset reference does not resolve: "
                f"{value!r}"
            )
        return "file-sha256:" + _file_sha256(asset_path)
    if value.startswith("data:") or "://" in value:
        return value
    return value.replace("\\", "/").rsplit("/", 1)[-1]


def _element_tree_signature(
    elem: ET.Element,
    *,
    include_skin: bool = False,
    include_text: bool = True,
    svg_path: Path | None = None,
    asset_identity: bool = False,
    ignore_structure_attrs: bool = False,
) -> tuple[object, ...]:
    """Return a stable structural or literal-visual SVG subtree signature."""
    text = (elem.text or "") if include_text else ""
    if _local_tag(elem) not in {"text", "tspan"} and not text.strip():
        text = ""
    attrs = tuple(sorted(
        (
            name,
            _signature_attr_value(
                name,
                value,
                svg_path=svg_path,
                asset_identity=asset_identity,
            ),
        )
        for name, value in elem.attrib.items()
        if (
            not (
                ignore_structure_attrs
                and name.rsplit("}", 1)[-1] in _STRUCTURE_ATTRS
            )
            and (
                include_skin
                or name.rsplit("}", 1)[-1] not in _TEMPLATE_SKIN_ATTRS
            )
        )
    ))
    return (
        elem.tag,
        attrs,
        text,
        tuple(
            _element_tree_signature(
                child,
                include_skin=include_skin,
                include_text=include_text,
                svg_path=svg_path,
                asset_identity=asset_identity,
                ignore_structure_attrs=ignore_structure_attrs,
            )
            for child in elem
        ),
    )


def _svg_reference_ids(elem: ET.Element) -> set[str]:
    """Return fragment ids referenced anywhere in one SVG subtree."""
    references: set[str] = set()
    for node in elem.iter():
        for name, value in node.attrib.items():
            if name.rsplit("}", 1)[-1] == "href" and value.startswith("#"):
                references.add(value[1:])
            references.update(
                match.group(2)[1:]
                for match in _CSS_URL_RE.finditer(value)
                if match.group(2).startswith("#")
            )
    return references


def _font_family_names(raw_value: str) -> set[str]:
    """Return normalized CSS font-family names from one declaration value."""
    return {
        value.strip().strip("'\"")
        for value in raw_value.split(",")
        if value.strip().strip("'\"")
    }


def _font_families_from_declarations(raw: str) -> set[str]:
    """Return font families assigned by one inline or stylesheet declaration."""
    families: set[str] = set()
    for match in re.finditer(
        r"font-family\s*:\s*([^;{}]+)",
        raw,
        flags=re.IGNORECASE,
    ):
        families.update(_font_family_names(match.group(1)))
    return families


def _scope_selector_tokens(
    root: ET.Element,
    elements: tuple[ET.Element, ...],
) -> tuple[set[str], set[str], set[str], list[dict[str, str]], set[str]]:
    """Collect the small selector vocabulary needed to filter SVG CSS rules."""
    ids: set[str] = set()
    classes: set[str] = set()
    tags: set[str] = set()
    attributes: list[dict[str, str]] = []
    font_families: set[str] = set()
    nodes = [root]
    for element in elements:
        nodes.extend(element.iter())
    for node in nodes:
        tags.add(_local_tag(node))
        node_id = (node.get("id") or "").strip()
        if node_id:
            ids.add(node_id)
        classes.update((node.get("class") or "").split())
        local_attrs = {
            name.rsplit("}", 1)[-1]: value
            for name, value in node.attrib.items()
        }
        attributes.append(local_attrs)
        if local_attrs.get("font-family"):
            font_families.update(
                _font_family_names(local_attrs["font-family"])
            )
        if local_attrs.get("style"):
            font_families.update(
                _font_families_from_declarations(local_attrs["style"])
            )
    return ids, classes, tags, attributes, font_families


def _css_selector_matches_scope(
    selector: str,
    *,
    ids: set[str],
    classes: set[str],
    tags: set[str],
    attributes: list[dict[str, str]],
) -> bool:
    """Conservatively decide whether one simple SVG selector can affect scope."""
    selector_ids = set(_CSS_ID_RE.findall(selector))
    if selector_ids and not selector_ids.issubset(ids):
        return False
    selector_classes = set(_CSS_CLASS_RE.findall(selector))
    if selector_classes and not selector_classes.issubset(classes):
        return False
    for match in _CSS_ATTR_RE.finditer(selector):
        attr_name = match.group(1).rsplit(":", 1)[-1]
        expected = (match.group(3) or "").strip()
        if not any(
            attr_name in attrs
            and (not expected or attrs[attr_name].strip() == expected)
            for attrs in attributes
        ):
            return False
    selector_tags = {
        tag.lower()
        for tag in _CSS_TAG_RE.findall(selector)
        if tag != "*"
    }
    if selector_tags and not selector_tags.issubset(
        {tag.lower() for tag in tags}
    ):
        return False
    return True


def _css_asset_signature(value: str, svg_path: Path) -> str:
    """Replace CSS URL assets with byte identities while retaining fragments."""
    def replace(match: re.Match[str]) -> str:
        target = match.group(2).strip()
        if target.startswith("#"):
            return f"url({target})"
        identity = _signature_attr_value(
            "href",
            target,
            svg_path=svg_path,
            asset_identity=True,
        )
        return f"url({identity})"

    return _CSS_URL_RE.sub(replace, value)


def _normalize_css_declarations(raw: str, svg_path: Path) -> str:
    """Normalize formatting-only CSS differences without changing cascade order."""
    declarations: list[str] = []
    for raw_declaration in raw.split(";"):
        declaration = raw_declaration.strip()
        if not declaration:
            continue
        if ":" not in declaration:
            declarations.append(" ".join(declaration.split()))
            continue
        name, value = declaration.split(":", 1)
        normalized_value = " ".join(
            _css_asset_signature(value.strip(), svg_path).split()
        )
        declarations.append(f"{name.strip().lower()}:{normalized_value}")
    return ";".join(declarations)


def _scope_css_signature(
    root: ET.Element,
    elements: tuple[ET.Element, ...],
    svg_path: Path,
) -> tuple[tuple[str, str], ...]:
    """Return only stylesheet rules that can affect the selected visual scope."""
    ids, classes, tags, attributes, font_families = _scope_selector_tokens(
        root,
        elements,
    )
    parsed_rules: list[tuple[str, str]] = []
    for style in root.iter():
        if _local_tag(style) != "style":
            continue
        css = _CSS_COMMENT_RE.sub("", style.text or "")
        for match in _CSS_RULE_RE.finditer(css):
            parsed_rules.append((match.group(1).strip(), match.group(2)))

    matched_selectors: dict[int, tuple[str, ...]] = {}
    for index, (raw_selector, body) in enumerate(parsed_rules):
        if raw_selector.startswith("@"):
            continue
        selectors = tuple(
            " ".join(selector.split())
            for selector in raw_selector.split(",")
            if _css_selector_matches_scope(
                selector,
                ids=ids,
                classes=classes,
                tags=tags,
                attributes=attributes,
            )
        )
        if selectors:
            matched_selectors[index] = selectors
            font_families.update(_font_families_from_declarations(body))

    rules: list[tuple[str, str]] = []
    for index, (raw_selector, body) in enumerate(parsed_rules):
        selectors = matched_selectors.get(index)
        if selectors is None:
            if not raw_selector.lower().startswith("@font-face"):
                continue
            declared_families = _font_families_from_declarations(body)
            if not declared_families.intersection(font_families):
                continue
            selectors = ("@font-face",)
        rules.append((
            ",".join(selectors),
            _normalize_css_declarations(body, svg_path),
        ))
    return tuple(rules)


def _scope_visual_resources_signature(
    root: ET.Element,
    elements: tuple[ET.Element, ...],
    svg_path: Path,
) -> tuple[object, ...]:
    """Capture root inheritance, relevant CSS, and the referenced defs closure."""
    if not elements:
        return ()
    root_attrs = tuple(sorted(
        (
            name,
            _signature_attr_value(
                name,
                value,
                svg_path=svg_path,
                asset_identity=True,
            ),
        )
        for name, value in root.attrib.items()
        if (
            name.rsplit("}", 1)[-1] not in _STRUCTURE_ATTRS
            and not name.rsplit("}", 1)[-1].startswith("data-")
        )
    ))
    css_rules = _scope_css_signature(root, elements, svg_path)
    references: set[str] = set()
    for element in elements:
        references.update(_svg_reference_ids(element))
    for _selector, declarations in css_rules:
        references.update(
            match.group(2)[1:]
            for match in _CSS_URL_RE.finditer(declarations)
            if match.group(2).startswith("#")
        )

    definitions_by_id: dict[str, ET.Element] = {}
    for definitions in root.iter():
        if _local_tag(definitions) != "defs":
            continue
        for definition in definitions.iter():
            definition_id = (definition.get("id") or "").strip()
            if definition_id:
                definitions_by_id[definition_id] = definition

    pending = list(references)
    resolved: set[str] = set()
    while pending:
        reference = pending.pop()
        if reference in resolved:
            continue
        resolved.add(reference)
        definition = definitions_by_id.get(reference)
        if definition is not None:
            pending.extend(_svg_reference_ids(definition) - resolved)
    definition_signatures = tuple(
        (
            reference,
            _element_tree_signature(
                definitions_by_id[reference],
                include_skin=True,
                include_text=True,
                svg_path=svg_path,
                asset_identity=True,
            ) if reference in definitions_by_id else ("missing", reference),
        )
        for reference in sorted(resolved)
    )
    return root_attrs, css_rules, definition_signatures


def _structure_subtree_signature(
    svg_path: Path,
    elements: tuple[TemplateElementSpec, ...],
    *,
    include_skin: bool = False,
    include_text: bool = True,
    asset_identity: bool = False,
) -> tuple[tuple[str, tuple[object, ...]], ...]:
    """Read structural or literal-visual signatures for direct SVG children."""
    try:
        root = ET.parse(svg_path).getroot()
        materialize_inline_geometry_properties(root)
    except (OSError, ET.ParseError, GeometryStyleError) as exc:
        raise TemplateStructureError(
            f"{svg_path.name}: unable to compare template prototype structure: {exc}"
        ) from exc
    direct_by_id = {
        (child.get("id") or "").strip(): child
        for child in root
        if (child.get("id") or "").strip()
    }
    signatures: list[tuple[str, tuple[object, ...]]] = []
    for item in elements:
        child = direct_by_id.get(item.element_id)
        if child is None:
            raise TemplateStructureError(
                f"{svg_path.name}: structure element {item.element_id!r} is no "
                "longer a direct SVG child"
            )
        signatures.append((
            item.element_id,
            _element_tree_signature(
                child,
                include_skin=include_skin,
                include_text=include_text,
                svg_path=svg_path,
                asset_identity=asset_identity,
            ),
        ))
    if include_skin:
        selected = tuple(
            direct_by_id[item.element_id]
            for item in elements
            if item.element_id in direct_by_id
        )
        signatures.append((
            "__visual_resources__",
            _scope_visual_resources_signature(root, selected, svg_path),
        ))
    return tuple(signatures)


def _mirror_ordinary_slide_ids(spec: TemplateSlideSpec) -> set[str]:
    """Return stable ids that are ordinary Slide content in one mirror page."""
    try:
        root = ET.parse(spec.svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise TemplateStructureError(
            f"{spec.svg_path.name}: unable to inspect mirror page ownership: {exc}"
        ) from exc
    inherited_ids = {
        item.element_id
        for item in (
            *spec.master_elements,
            *spec.layout_elements,
            *spec.placeholders,
        )
    }
    return {
        element_id
        for child in root
        if _local_tag(child) not in _NON_VISUAL_TAGS
        if (element_id := (child.get("id") or "").strip())
        if element_id not in inherited_ids
    }


def _mirror_slide_local_signature(
    spec: TemplateSlideSpec,
    protected_ids: set[str],
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    """Capture literal mirror visuals that are Slide-local on either page.

    Visible text values may change, but their element topology, attributes,
    grouping, paint, geometry, and referenced asset bytes remain literal.
    Structure metadata may change when adaptive template authoring assigns an
    evolved Layout identity to the same stable SVG id.
    """
    try:
        root = ET.parse(spec.svg_path).getroot()
        materialize_inline_geometry_properties(root)
    except (OSError, ET.ParseError, GeometryStyleError) as exc:
        raise TemplateStructureError(
            f"{spec.svg_path.name}: unable to compare mirror page visuals: {exc}"
        ) from exc
    slide_elements: list[ET.Element] = []
    slide_visuals: list[tuple[object, ...]] = []
    for child in root:
        tag = _local_tag(child)
        if tag in _NON_VISUAL_TAGS:
            continue
        element_id = (child.get("id") or "").strip()
        if element_id and element_id not in protected_ids:
            continue
        slide_elements.append(child)
        slide_visuals.append(
            _element_tree_signature(
                child,
                include_skin=True,
                include_text=False,
                svg_path=spec.svg_path,
                asset_identity=True,
                ignore_structure_attrs=True,
            )
        )
    resources = _scope_visual_resources_signature(
        root,
        tuple(slide_elements),
        spec.svg_path,
    )
    return resources, tuple(slide_visuals)


def _prototype_placeholder_contract(
    spec: TemplateSlideSpec,
) -> tuple[tuple[object, ...], ...]:
    """Return the strict template placeholder contract without slide content."""
    return tuple(item.contract_signature() for item in spec.placeholders)


def _layout_contract_difference(
    actual: tuple[TemplateElementSpec, ...],
    expected: tuple[TemplateElementSpec, ...],
) -> str:
    """Describe the smallest actionable difference in a Layout atom roster."""
    actual_ids = tuple(item.element_id for item in actual)
    expected_ids = tuple(item.element_id for item in expected)
    actual_id_set = set(actual_ids)
    expected_id_set = set(expected_ids)
    missing = tuple(item for item in expected_ids if item not in actual_id_set)
    unexpected = tuple(item for item in actual_ids if item not in expected_id_set)
    details: list[str] = []
    if missing:
        details.append(
            "missing generated Layout element id(s): "
            + ", ".join(repr(item) for item in missing)
        )
    if unexpected:
        details.append(
            "unexpected generated Layout element id(s): "
            + ", ".join(repr(item) for item in unexpected)
        )
    if not details and actual_ids != expected_ids:
        details.append("generated Layout element order differs")
    if not details:
        details.append(
            "shared Layout element metadata, geometry, topology, or content differs"
        )
    return "; ".join(details)


def template_prototype_errors(
    specs: list[TemplateSlideSpec],
    structure_lock: PptxStructureLock,
    *,
    require_complete_roster: bool = True,
) -> list[str]:
    """Compare structured template pages with their selected SVG prototypes."""
    if structure_lock.mode != "structured" or not structure_lock.prototypes:
        return []
    errors: list[str] = []
    prototypes = {
        reference.slide_num: reference
        for reference in structure_lock.prototypes
    }
    adherence = structure_lock.template_adherence or "strict"
    actual_slides = {spec.slide_num for spec in specs}
    prototype_slides = set(prototypes)
    missing_prototypes = sorted(actual_slides - prototype_slides)
    extra_prototypes = sorted(prototype_slides - actual_slides)
    if missing_prototypes:
        errors.append(
            "spec_lock.md page_layouts is missing generated page(s): "
            + ", ".join(f"P{slide_num:02d}" for slide_num in missing_prototypes)
        )
    if require_complete_roster and extra_prototypes:
        errors.append(
            "spec_lock.md page_layouts references absent page(s): "
            + ", ".join(f"P{slide_num:02d}" for slide_num in extra_prototypes)
        )
    for spec in specs:
        reference = prototypes.get(spec.slide_num)
        if reference is None:
            errors.append(
                f"{spec.svg_path.name}: spec_lock.md page_layouts is missing "
                f"prototype P{spec.slide_num:02d}"
            )
            continue
        try:
            prototype = parse_template_slide(reference.svg_path, spec.slide_num)
        except TemplateStructureError as exc:
            errors.append(str(exc))
            continue

        try:
            literal_visual = reference.replication_mode == "mirror"
            expected_master_structure = _structure_subtree_signature(
                prototype.svg_path,
                prototype.master_elements,
                include_skin=literal_visual,
                asset_identity=literal_visual,
            )
            actual_master_structure = _structure_subtree_signature(
                spec.svg_path,
                spec.master_elements,
                include_skin=literal_visual,
                asset_identity=literal_visual,
            )
        except TemplateStructureError as exc:
            errors.append(str(exc))
            continue
        if (
            spec.master_key != prototype.master_key
            or spec.master_name != prototype.master_name
            or tuple(item.contract_signature() for item in spec.master_elements)
            != tuple(
                item.contract_signature() for item in prototype.master_elements
            )
            or actual_master_structure != expected_master_structure
        ):
            errors.append(
                f"{spec.svg_path.name}: template Master structure differs "
                f"from prototype {reference.svg_path.name}; strict and adaptive "
                "routes must retain its ids, topology, geometry, and content"
                + (" including mirror visual styling" if literal_visual else "")
            )

        if literal_visual:
            try:
                protected_slide_ids = (
                    _mirror_ordinary_slide_ids(prototype)
                    | _mirror_ordinary_slide_ids(spec)
                )
                expected_slide_visual = _mirror_slide_local_signature(
                    prototype,
                    protected_slide_ids,
                )
                actual_slide_visual = _mirror_slide_local_signature(
                    spec,
                    protected_slide_ids,
                )
            except TemplateStructureError as exc:
                errors.append(str(exc))
                continue
            if actual_slide_visual != expected_slide_visual:
                errors.append(
                    f"{spec.svg_path.name}: mirror Slide-local non-text visuals "
                    f"differ from prototype {reference.svg_path.name}; preserve "
                    "grouping, geometry, paint, effects, and referenced asset "
                    "identity, changing only visible text content"
                )

        try:
            expected_layout_structure = _structure_subtree_signature(
                prototype.svg_path,
                prototype.layout_elements,
                include_skin=literal_visual,
                asset_identity=literal_visual,
            )
            actual_layout_structure = _structure_subtree_signature(
                spec.svg_path,
                spec.layout_elements,
                include_skin=literal_visual,
                asset_identity=literal_visual,
            )
            if literal_visual:
                expected_placeholder_visual = _structure_subtree_signature(
                    prototype.svg_path,
                    prototype.placeholders,
                    include_skin=True,
                    include_text=False,
                    asset_identity=True,
                )
                actual_placeholder_visual = _structure_subtree_signature(
                    spec.svg_path,
                    spec.placeholders,
                    include_skin=True,
                    include_text=False,
                    asset_identity=True,
                )
            else:
                expected_placeholder_visual = ()
                actual_placeholder_visual = ()
        except TemplateStructureError as exc:
            errors.append(str(exc))
            continue

        placeholder_contract_same = (
            _prototype_placeholder_contract(spec)
            == _prototype_placeholder_contract(prototype)
        )
        layout_contract_same = (
            tuple(item.contract_signature() for item in spec.layout_elements)
            == tuple(
                item.contract_signature() for item in prototype.layout_elements
            )
            and actual_layout_structure == expected_layout_structure
        )
        placeholder_visual_same = (
            actual_placeholder_visual == expected_placeholder_visual
        )
        reusable_contract_same = (
            placeholder_contract_same
            and layout_contract_same
            and placeholder_visual_same
        )

        reuses_prototype_key = spec.layout_key == prototype.layout_key
        if adherence == "adaptive" and not reuses_prototype_key:
            if spec.layout_name == prototype.layout_name:
                errors.append(
                    f"{spec.svg_path.name}: adaptive template authoring created "
                    f"new layout key {spec.layout_key!r} but reused prototype picker "
                    f"name {prototype.layout_name!r}; assign a new key and name to "
                    "the evolved Layout contract"
                )
            if reusable_contract_same:
                errors.append(
                    f"{spec.svg_path.name}: adaptive template authoring changed "
                    "only the Layout key/name while the reusable static, "
                    "placeholder, and default-bounds contract is unchanged; "
                    f"reuse prototype identity {prototype.layout_key!r} / "
                    f"{prototype.layout_name!r}"
                )
            continue

        missing_bounds = [
            item.element_id
            for item in prototype.placeholders
            if item.placeholder_bounds is None
        ]
        if missing_bounds:
            if adherence == "strict":
                errors.append(
                    f"{reference.svg_path.name}: deferred strict template "
                    "authoring requires explicit data-pptx-placeholder-bounds "
                    "on every prototype placeholder; missing: "
                    + ", ".join(missing_bounds)
                )
            else:
                errors.append(
                    f"{spec.svg_path.name}: adaptive output reused prototype layout "
                    f"key {prototype.layout_key!r}, but that prototype lacks explicit "
                    "placeholder bounds; assign a new key and name to the evolved "
                    "Layout contract"
                )
            continue
        if spec.layout_key != prototype.layout_key:
            errors.append(
                f"{spec.svg_path.name}: strict template use must keep "
                f"prototype layout key {prototype.layout_key!r}, found "
                f"{spec.layout_key!r}"
            )
        if spec.layout_name != prototype.layout_name:
            if adherence == "strict":
                errors.append(
                    f"{spec.svg_path.name}: strict template use must keep "
                    f"prototype layout name {prototype.layout_name!r}, found "
                    f"{spec.layout_name!r}"
                )
            else:
                errors.append(
                    f"{spec.svg_path.name}: adaptive output reused prototype layout "
                    f"key {prototype.layout_key!r} but changed its picker name from "
                    f"{prototype.layout_name!r} to {spec.layout_name!r}; assign a "
                    "new key and name to the evolved Layout contract"
                )
        if not placeholder_contract_same:
            if adherence == "strict":
                errors.append(
                    f"{spec.svg_path.name}: strict placeholder id/type/index/default-"
                    f"bounds contract differs from prototype "
                    f"{reference.svg_path.name}"
                )
            else:
                errors.append(
                    f"{spec.svg_path.name}: adaptive output reused prototype layout "
                    f"key {prototype.layout_key!r} but changed its placeholder "
                    "contract; assign a new key and name"
                )
        if literal_visual and not placeholder_visual_same:
            errors.append(
                f"{spec.svg_path.name}: mirror placeholder geometry or visual "
                f"styling differs from prototype {reference.svg_path.name}; "
                "only visible text content may change under the reused Layout"
            )
        if not layout_contract_same:
            qualifier = "mirror visual/structural" if literal_visual else "structural"
            difference = _layout_contract_difference(
                spec.layout_elements,
                prototype.layout_elements,
            )
            if adherence == "strict":
                errors.append(
                    f"{spec.svg_path.name}: strict Layout {qualifier} contract "
                    f"differs from prototype {reference.svg_path.name}; {difference}"
                )
            else:
                errors.append(
                    f"{spec.svg_path.name}: adaptive output reused prototype layout "
                    f"key {prototype.layout_key!r} but changed its {qualifier} "
                    f"contract; {difference}; assign a new key and name"
                )
    return errors


_PRESERVE_PLACEHOLDER_TYPE_ORDER = {
    "title": ("title", "ctrTitle"),
    "subtitle": ("subTitle", "body", "obj"),
    "body": ("body", "obj", "subTitle"),
    "picture": ("pic", "obj"),
    "chart": ("chart", "obj"),
    "table": ("tbl", "obj"),
    "object": ("obj",),
    "media": ("media", "obj", "pic"),
    "date": ("dt",),
    "footer": ("ftr",),
    "slide-number": ("sldNum",),
}


def match_native_placeholders(
    spec: TemplateSlideSpec,
    layout: NativeLayoutSpec,
) -> tuple[tuple[TemplateElementSpec, NativePlaceholderSpec], ...]:
    """Match slide placeholder markers to source layout placeholder identities."""
    available = list(layout.placeholders)
    matches: list[tuple[TemplateElementSpec, NativePlaceholderSpec]] = []
    for item in spec.placeholders:
        allowed_types = _PRESERVE_PLACEHOLDER_TYPE_ORDER.get(
            item.placeholder or "",
            (),
        )
        candidate_index = None
        for placeholder_type in allowed_types:
            for index, candidate in enumerate(available):
                if candidate.placeholder_type != placeholder_type:
                    continue
                if (
                    item.placeholder_idx is not None
                    and candidate.idx != item.placeholder_idx
                ):
                    continue
                candidate_index = index
                break
            if candidate_index is not None:
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


def _placement_lint_errors(svg_path: Path) -> list[str]:
    """Enumerate every placement/paint-order violation in one pass.

    ``parse_template_slide`` fails fast on the first error, which discloses
    violations one whole fix-cycle at a time. The quality checker runs this
    pre-lint first so a single run reports every offender of the two
    highest-frequency classes: structure metadata below the root, and
    template paint-order violations.
    """
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError):
        return []
    if _local_tag(root) != "svg":
        return []
    errors: list[str] = []
    direct_children = set(root)
    allowed_carriers = {
        carrier
        for slot in root
        if (slot.get("data-pptx-placeholder") or "").strip()
        for carrier in slot
        if carrier.get("data-pptx-placeholder-carrier") is not None
    }
    for elem in root.iter():
        if elem is root or elem in direct_children:
            continue
        attrs = _structure_attrs(elem)
        if elem in allowed_carriers:
            attrs = [
                attr for attr in attrs
                if attr != "data-pptx-placeholder-carrier"
            ]
        if attrs:
            element_id = elem.get("id") or _local_tag(elem) or "<unnamed>"
            errors.append(
                f"{svg_path.name}: {element_id} uses template metadata below the SVG "
                "root; only a direct slot child may declare its carrier marker"
            )
    canvas = _svg_canvas(root)
    last_order_rank = -1
    for elem in root:
        tag = _local_tag(elem)
        if tag in _NON_VISUAL_TAGS:
            continue
        layer = (elem.get("data-pptx-layer") or "").strip().lower() or None
        if layer not in _LAYERS:
            layer = None
        is_background = _is_full_canvas_solid_rect(elem, canvas)
        effective_layer = layer or ("slide" if is_background else None)
        if is_background and effective_layer is not None:
            order_rank = {"master": 0, "layout": 1, "slide": 2}[effective_layer]
        elif effective_layer == "master":
            order_rank = 3
        elif effective_layer == "layout":
            order_rank = 4
        else:
            order_rank = 5
        if order_rank < last_order_rank:
            errors.append(
                f"{svg_path.name}: {elem.get('id') or tag} violates template paint "
                "order; use Master background, Layout background, Slide background, "
                "Master shapes, Layout shapes, then Slide content/placeholders"
            )
            continue
        last_order_rank = order_rank
    return errors


def validate_template_svg(svg_path: Path) -> list[str]:
    """Return per-file template metadata errors for quality-check integration."""
    errors = _placement_lint_errors(svg_path)
    try:
        parse_template_slide(svg_path, 1)
    except TemplateStructureError as exc:
        message = str(exc)
        if message not in errors:
            errors.append(message)
    return errors
