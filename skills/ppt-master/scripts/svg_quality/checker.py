#!/usr/bin/env python3
"""PPT Master SVG quality-check implementation.

Owns SVG, project-contract, template, and report validation. The stable CLI and
compatibility import surface remain in ``scripts/svg_quality_checker.py``.

Usage:
    Import through ``svg_quality_checker`` or invoke the stable script.

Examples:
    from svg_quality_checker import SVGQualityChecker

Dependencies:
    Standard library plus local PPT Master validation modules.
"""

import copy
import hashlib
import html
import json
import math
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from native_payloads import NativePayloadError, hydrate_native_payload_refs
from slide_roster import discover_slide_svgs

from . import svg_contracts
from .xml_support import (
    SVG_NS,
    XLINK_NS,
    element_label as _element_label,
    local_name as _local_name,
)

try:
    from project_utils import (
        CANVAS_FORMATS,
        validate_communication_trace,
    )
except ImportError:
    print("Warning: Unable to import project_utils")
    CANVAS_FORMATS = {}
    validate_communication_trace = None

from svg_to_pptx.canvas_contract import (
    CanvasContractError,
    parse_project_svg_root,
    parse_project_viewbox,
)

try:
    from project_management.project_specs import (
        parse_spec_lock as _parse_spec_lock,
        parse_spec_lock_image_value as _parse_spec_lock_image_value,
    )
except ImportError:
    _parse_spec_lock = None  # spec_lock anchor comparison will be skipped
    _parse_spec_lock_image_value = None

try:
    from svg_to_pptx.animation_config import (
        load_animation_config as _load_animation_config,
        usable_animation_group_id as _usable_animation_group_id,
        validate_animation_config as _validate_animation_config,
        validate_animation_config_errors as _validate_animation_config_errors,
        validate_transition_config as _validate_transition_config,
    )
except ImportError as exc:
    _load_animation_config = None
    _validate_animation_config = None
    _validate_animation_config_errors = None
    _validate_transition_config = None
    _animation_config_import_error = str(exc)

    def _usable_animation_group_id(raw: str | None) -> str | None:
        return raw if raw and raw.strip() else None
else:
    _animation_config_import_error = None

try:
    from svg_to_pptx.drawingml.utils import (
        IDENTITY_MATRIX as _IDENTITY_MATRIX,
        PROJECT_PAINT_PROPERTIES as _PAINT_PROPERTIES,
        PROJECT_TEXT_IMAGE_FILL_ATTR as _TEXT_IMAGE_FILL_ATTR,
        detect_text_lang as _detect_text_lang,
        matrix_multiply as _matrix_multiply,
        parse_inline_style as _parse_inline_style,
        parse_project_geometry_length as _parse_project_geometry_length,
        parse_project_image_aspect_ratio as _parse_project_image_aspect_ratio,
        parse_project_opacity as _parse_project_opacity,
        parse_svg_color as _parse_export_color,
        parse_transform_matrix as _parse_transform_matrix,
        project_mask_errors as _project_mask_errors,
        rect_to_dml_xfrm as _rect_to_dml_xfrm,
        transform_point as _transform_point,
        unsafe_exported_font_faces as _unsafe_exported_font_faces,
        validate_dml_shape_matrix as _validate_dml_shape_matrix,
    )
except ImportError:
    _IDENTITY_MATRIX = None
    _PAINT_PROPERTIES = None
    _TEXT_IMAGE_FILL_ATTR = 'data-pptx-text-image-fill'
    _detect_text_lang = None
    _matrix_multiply = None
    _parse_inline_style = None
    _parse_project_geometry_length = None
    _parse_project_image_aspect_ratio = None
    _parse_project_opacity = None
    _parse_export_color = None
    _parse_transform_matrix = None
    _project_mask_errors = None
    _rect_to_dml_xfrm = None
    _transform_point = None
    _unsafe_exported_font_faces = None
    _validate_dml_shape_matrix = None

try:
    from hyperlink_contract import (
        SHAPE_HYPERLINK_ATTR as _SHAPE_HYPERLINK_ATTR,
        project_hyperlink_errors as _project_hyperlink_errors,
    )
except ImportError:
    _SHAPE_HYPERLINK_ATTR = 'data-pptx-shape-hyperlink'
    _project_hyperlink_errors = None

try:
    from svg_to_pptx.drawingml.converter import (
        SvgNativeConversionError as _SvgNativeConversionError,
        collect_unsupported_visuals as _collect_unsupported_visuals,
        preserved_native_text_body as _preserved_native_text_body,
    )
except ImportError:
    _SvgNativeConversionError = None
    _collect_unsupported_visuals = None
    _preserved_native_text_body = None

try:
    from svg_to_pptx.drawingml.elements import (
        drawingml_text_frame_width_emu as _drawingml_text_frame_width_emu,
        estimate_single_line_text_frame_width as _estimate_single_line_text_frame_width,
        project_image_errors as _project_image_errors,
        validate_single_line_text_run_advances as _validate_single_line_text_run_advances,
        validate_preset_geometry_metadata as _validate_preset_geometry_metadata,
    )
except ImportError:
    _drawingml_text_frame_width_emu = None
    _estimate_single_line_text_frame_width = None
    _project_image_errors = None
    _validate_single_line_text_run_advances = None
    _validate_preset_geometry_metadata = None

try:
    from svg_to_pptx.drawingml.text_properties import (
        normalize_project_text_segments as _normalize_project_text_segments,
        parse_project_font_weight as _parse_project_font_weight,
        parse_project_text_anchor as _parse_project_text_anchor,
        resolve_project_xml_space as _resolve_project_xml_space,
        resolve_project_font_sizes as _resolve_project_font_sizes,
        resolve_project_letter_spacings as _resolve_project_letter_spacings,
    )
except ImportError:
    _normalize_project_text_segments = None
    _parse_project_font_weight = None
    _parse_project_text_anchor = None
    _resolve_project_xml_space = None
    _resolve_project_font_sizes = None
    _resolve_project_letter_spacings = None

try:
    from pptx_to_svg.preset_authoring import (
        AUTHORING_ATTR as _AUTHORING_ATTR,
        authored_preset_encoding as _authored_preset_encoding,
        validate_authored_preset_group as _validate_authored_preset_group,
        validate_authored_preset_tree as _validate_authored_preset_tree,
    )
except ImportError:
    _AUTHORING_ATTR = 'data-pptx-authoring'
    _authored_preset_encoding = None
    _validate_authored_preset_group = None
    _validate_authored_preset_tree = None

try:
    from pptx_shapes import (
        CONNECTOR_PRESET_TYPES as _CONNECTOR_PRESET_TYPES,
        resolve_preset_preview_hash as _resolve_preset_preview_hash,
        svg_preset_preview_fingerprint as _svg_preset_preview_fingerprint,
    )
except ImportError:
    _CONNECTOR_PRESET_TYPES = frozenset()
    _resolve_preset_preview_hash = None
    _svg_preset_preview_fingerprint = None

try:
    from svg_to_pptx.native_objects import (
        validate_native_object_marker as _validate_native_object_marker,
    )
except ImportError:
    _validate_native_object_marker = None

try:
    from svg_to_pptx.native_objects import (
        validate_native_object_marker_with_warnings as _validate_native_object_marker_with_warnings,
    )
except ImportError:
    _validate_native_object_marker_with_warnings = None

try:
    from svg_to_pptx.native_objects import (
        native_object_marker_warnings as _native_object_marker_warnings,
    )
except ImportError:
    _native_object_marker_warnings = None

try:
    from svg_to_pptx.native_objects import (
        INLINE_FORMULA_ATTR as _INLINE_FORMULA_ATTR,
        native_fallback_kind as _native_fallback_kind,
        inline_formula_marker_errors as _inline_formula_marker_errors,
        native_marker_legacy_warnings as _native_marker_legacy_warnings,
        native_replacement_kind as _native_replacement_kind,
        native_replacement_status as _native_replacement_status,
    )
except ImportError:
    _INLINE_FORMULA_ATTR = 'data-pptx-inline-formula'
    _native_fallback_kind = None
    _inline_formula_marker_errors = None
    _native_marker_legacy_warnings = None
    _native_replacement_kind = None
    _native_replacement_status = None

try:
    from svg_to_pptx.native_objects.marker_status import (
        native_marker_release_block_reason as _native_marker_release_block_reason,
        native_marker_status_errors as _native_marker_status_errors,
    )
except ImportError:
    _native_marker_release_block_reason = None
    _native_marker_status_errors = None

try:
    from svg_to_pptx.semantic_markers import (
        SEMANTIC_ATTRS as _SEMANTIC_ATTRS,
        is_static_page_frame as _is_static_page_frame,
        validate_semantic_markers as _validate_semantic_markers,
    )
except ImportError:
    _SEMANTIC_ATTRS = frozenset({
        'data-pptx-page-role',
        'data-pptx-role',
    })
    _is_static_page_frame = None
    _validate_semantic_markers = None

try:
    from svg_to_pptx.use_expander import (
        UseExpansionError as _UseExpansionError,
        expand_local_use_references as _expand_local_use_references,
    )
except ImportError:
    _UseExpansionError = None
    _expand_local_use_references = None

try:
    from svg_to_pptx.tspan_flattener import (
        flatten_positional_tspans as _flatten_positional_tspans,
        nested_positional_tspan_errors as _nested_positional_tspan_errors,
    )
except ImportError:
    _flatten_positional_tspans = None
    _nested_positional_tspan_errors = None

try:
    from svg_to_pptx.pptx_package.template_structure import (
        TemplateStructureError as _TemplateStructureError,
        _is_authored_preset_atom as _is_authored_preset_atom,
        load_pptx_structure_lock as _load_pptx_structure_lock,
        parse_template_slide as _parse_template_structure_slide,
        parse_template_slides as _parse_template_structure_slides,
        _structure_subtree_signature as _structure_subtree_signature,
        template_lock_errors as _template_lock_errors,
        template_prototype_errors as _template_prototype_errors,
        validate_template_svg as _validate_template_structure_svg,
    )
except ImportError:
    _TemplateStructureError = None
    _is_authored_preset_atom = None
    _load_pptx_structure_lock = None
    _parse_template_structure_slide = None
    _parse_template_structure_slides = None
    _structure_subtree_signature = None
    _template_lock_errors = None
    _template_prototype_errors = None
    _validate_template_structure_svg = None

try:
    from svg_to_pptx.drawingml.theme_colors import (
        ThemeColorError as _ThemeColorError,
        load_theme_color_spec as _load_theme_color_spec,
    )
    from svg_to_pptx.drawingml.theme_fonts import (
        ThemeFontError as _ThemeFontError,
        load_master_text_style_spec as _load_master_text_style_spec,
        load_theme_font_spec as _load_theme_font_spec,
    )
except ImportError:
    _ThemeColorError = None
    _ThemeFontError = None
    _load_theme_color_spec = None
    _load_master_text_style_spec = None
    _load_theme_font_spec = None

try:
    from svg_finalize.embed_icons import (
        resolve_icon_path as _resolve_icon_path,
        suggest_icon_name as _suggest_icon_name,
    )
except ImportError:
    _resolve_icon_path = None
    _suggest_icon_name = None

try:
    from resource_paths import (
        SVG_WORK_DIR_NAMES as _SVG_WORK_DIR_NAMES,
        icon_search_dirs_for_svg as _icon_search_dirs_for_svg,
        project_root_for_svg_path as _project_root_for_svg_path,
        resolve_external_image_reference as _resolve_external_image_reference,
    )
except ImportError:
    _SVG_WORK_DIR_NAMES = frozenset()
    _icon_search_dirs_for_svg = None
    _project_root_for_svg_path = None
    _resolve_external_image_reference = None


HEX_VALUE_RE = re.compile(
    r"#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})"
)

# Master/Layout preflight validation. Structured deck/layout-template projects
# are checked at authoring time; the exporter remains the final OOXML/package
# authority. Flat projects only receive the negative guard that rejects authored
# structure metadata. Template roster/placeholder checks always run. Current
# bundled templates opt in to complete structure validation through their
# native_structure_mode: structured declaration. Legacy template-mode packages
# fail closed; Create Template must author a new current-contract workspace.
_CHECK_PPTX_STRUCTURED_PROJECT = True

_BARE_HEX_VALUE_RE = re.compile(
    r"(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})"
)
_NON_VISUAL_SVG_TAGS = frozenset({
    'defs',
    'desc',
    'metadata',
    'style',
    'title',
})
_BOUNDS_ATTR = 'data-pptx-bounds'
_MORPH_STAGING_ATTR = 'data-pptx-morph-staging'
_BOUNDS_OVERFLOW_TOLERANCE = 1.0
_BOUNDS_OVERFLOW_ERROR_RATIO = 0.05
_PARAGRAPH_LINE_GAP_MIN_RATIO = 0.9
_PARAGRAPH_LINE_GAP_MAX_RATIO = 2.05
_PARAGRAPH_LINE_X_TOLERANCE = 0.5
_PARAGRAPH_LINE_MIN_TOTAL_CHARS = 12
_PARAGRAPH_LINE_MIN_LONGEST_CHARS = 8
_PARAGRAPH_LINE_TERMINATOR_RE = re.compile(r'[.!?。！？;；]["\'”’）)]*$')
_PARAGRAPH_LIST_MARKER_RE = re.compile(
    r'^\s*(?:[•·・▪◦‣]\s*|[-–—*]\s+|\d+[.)、]\s+|[（(]\d+[）)]\s*)\S+'
)
_LEGACY_PPTX_ATTRIBUTE_RENAMES = {
    'data-pptx-module-bounds': _BOUNDS_ATTR,
    'data-pptx-placeholder-bounds': _BOUNDS_ATTR,
    'data-pptx-placeholder-carrier': 'data-pptx-carrier',
    'data-pptx-placeholder-binding': 'data-pptx-binding',
    'data-pptx-placeholder-idx': 'data-pptx-idx',
}
_PPTX_ROOT_STRUCTURE_ATTRS = (
    'data-pptx-master',
    'data-pptx-master-name',
    'data-pptx-layout',
    'data-pptx-layout-name',
)
_PPTX_ROOT_VISIBILITY_ATTRS = (
    'data-pptx-show-master-shapes',
    'data-pptx-show-inherited-shapes',
)
_PPTX_STRUCTURE_ATTRS = frozenset({
    *_PPTX_ROOT_STRUCTURE_ATTRS,
    *_PPTX_ROOT_VISIBILITY_ATTRS,
    'data-pptx-layer',
    'data-pptx-layout-kind',
    'data-pptx-placeholder',
    'data-pptx-binding',
    'data-pptx-carrier',
    'data-pptx-idx',
})
_PPTX_PLACEHOLDER_DETAIL_ATTRS = frozenset({
    'data-pptx-binding',
    'data-pptx-idx',
})
_PPTX_STRUCTURE_SECTION_RE = re.compile(
    r"(?ms)^##[ \t]+pptx_structure[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)"
)
_PPTX_STRUCTURE_MODE_RE = re.compile(
    r"(?m)^-[ \t]+mode[ \t]*:[ \t]*([^\s#]+)[ \t]*(?:#.*)?$"
)
def _compact_preset_ancestor_paint(
    root: ET.Element,
) -> list[tuple[str, tuple[str, ...]]]:
    """Return compact presets affected by compatible ancestor paint."""
    if (
        _authored_preset_encoding is None
        or _validate_authored_preset_group is None
    ):
        return []
    parents = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    affected: list[tuple[str, tuple[str, ...]]] = []
    for group in root.iter():
        if (
            _authored_preset_encoding(group) != 'compact'
            or _validate_authored_preset_group(group)
        ):
            continue
        relevant = {'opacity'}
        if group.get('fill') != 'none' and group.get('fill-opacity') is None:
            relevant.add('fill-opacity')
        if group.get('stroke') != 'none':
            for name in (
                'stroke-opacity',
                'stroke-dasharray',
                'stroke-linecap',
                'stroke-linejoin',
            ):
                if group.get(name) is None:
                    relevant.add(name)

        inherited: set[str] = set()
        ancestor = parents.get(group)
        while ancestor is not None:
            declarations = {
                name: ancestor.get(name) or ''
                for name in relevant
                if ancestor.get(name) is not None
            }
            for declaration in (ancestor.get('style') or '').split(';'):
                name, separator, value = declaration.partition(':')
                name = name.strip().lower()
                if separator and name in relevant:
                    declarations[name] = value.strip()
            for name, value in declarations.items():
                normalized = value.strip().lower()
                if name in {'opacity', 'fill-opacity', 'stroke-opacity'}:
                    try:
                        if float(normalized) == 1:
                            continue
                    except ValueError:
                        pass
                elif name == 'stroke-dasharray' and normalized == 'none':
                    continue
                elif name == 'stroke-linecap' and normalized == 'butt':
                    continue
                elif name == 'stroke-linejoin' and normalized == 'miter':
                    continue
                inherited.add(name)
            ancestor = parents.get(ancestor)
        if inherited:
            affected.append((
                group.get('id') or '(no id)',
                tuple(sorted(inherited)),
            ))
    return affected


def _declared_pptx_structure_mode(project_path: Path) -> str | None:
    """Return the explicitly locked SVG structure mode without a fallback."""
    lock_path = project_path / 'spec_lock.md'
    try:
        content = lock_path.read_text(encoding='utf-8')
    except OSError:
        return None
    section_match = _PPTX_STRUCTURE_SECTION_RE.search(content)
    if section_match is None:
        return None
    mode_match = _PPTX_STRUCTURE_MODE_RE.search(section_match.group(1))
    return mode_match.group(1).strip().lower() if mode_match else None


def _generated_theme_contract_errors(project_path: Path) -> List[str]:
    """Validate the current-project theme contract required by release export."""
    if (
        _ThemeColorError is None
        or _ThemeFontError is None
        or _load_theme_color_spec is None
        or _load_master_text_style_spec is None
        or _load_theme_font_spec is None
    ):
        return [
            "PowerPoint theme contract validation is unavailable because the "
            "theme loader modules could not be imported."
        ]
    try:
        theme_font_spec = _load_theme_font_spec(project_path)
        _load_master_text_style_spec(project_path)
        theme_color_spec = _load_theme_color_spec(project_path)
    except (_ThemeFontError, _ThemeColorError) as exc:
        return [str(exc)]

    missing: List[str] = []
    if theme_font_spec is None:
        missing.append("typography font_family/title_family/body_family")
    if theme_color_spec is None:
        missing.append("colors")
    if not missing:
        return []
    return [
        "spec_lock.md generated PowerPoint theme contract is missing: "
        + ", ".join(missing)
    ]


def _parse_positive_bounds(
    value: str,
) -> Tuple[float, float, float, float]:
    """Parse one positive x/y/width/height boundary."""
    raw_values = [item for item in re.split(r"[\s,]+", value.strip()) if item]
    if len(raw_values) != 4:
        raise ValueError("must contain exactly four numbers: x y width height")
    try:
        values = tuple(float(item) for item in raw_values)
    except ValueError as exc:
        raise ValueError("must contain only numeric values") from exc
    if not all(math.isfinite(item) for item in values):
        raise ValueError("must contain only finite values")
    if values[2] <= 0 or values[3] <= 0:
        raise ValueError("must use positive width and height")
    return values


def _placeholder_bounds_error(value: str) -> str | None:
    """Return a concise error for invalid design-zone bounds."""
    try:
        _parse_positive_bounds(value)
    except ValueError as exc:
        return str(exc)
    return None


def _local_pptx_structure_errors(
    root: ET.Element,
    svg_path: Path,
    *,
    require_structure: bool,
) -> List[str]:
    """Validate the authoring shape of the structured SVG contract."""
    errors: List[str] = []
    root_values = {
        attr: (root.get(attr) or '').strip()
        for attr in _PPTX_ROOT_STRUCTURE_ATTRS
    }
    has_root_structure = any(root_values.values())
    if require_structure or has_root_structure:
        missing = [attr for attr, value in root_values.items() if not value]
        if missing:
            errors.append(
                f"{svg_path.name}: structured SVG root is missing "
                + ', '.join(missing)
            )
    for attr in _PPTX_ROOT_VISIBILITY_ATTRS:
        raw = root.get(attr)
        if raw is not None and raw not in {'true', 'false'}:
            errors.append(
                f"{svg_path.name}: root {attr} must be exactly 'true' or 'false'"
            )

    parent_by_id = {
        id(child): parent
        for parent in root.iter()
        for child in list(parent)
    }
    for elem in root.iter():
        tag = elem.tag.rsplit('}', 1)[-1]
        element_id = elem.get('id') or f"<{tag}>"
        parent = parent_by_id.get(id(elem))

        if elem is not root:
            nested_root_attrs = [
                attr for attr in (
                    *_PPTX_ROOT_STRUCTURE_ATTRS,
                    *_PPTX_ROOT_VISIBILITY_ATTRS,
                )
                if elem.get(attr) is not None
            ]
            if nested_root_attrs:
                errors.append(
                    f"{svg_path.name}: {element_id} carries root-only metadata "
                    + ', '.join(nested_root_attrs)
                )

        if elem.get('data-pptx-layout-kind') is not None:
            errors.append(
                f"{svg_path.name}: data-pptx-layout-kind is a legacy distillation "
                "attribute; restore the page to the structured contract"
            )

        layer = (elem.get('data-pptx-layer') or '').strip().lower()
        placeholder = (elem.get('data-pptx-placeholder') or '').strip().lower()
        if layer in {'master', 'layout'}:
            if parent is not root:
                errors.append(
                    f"{svg_path.name}: {element_id} data-pptx-layer={layer!r} "
                    "must be a direct child of the root <svg>"
                )
            if tag == 'g' and not (
                _is_authored_preset_atom is not None
                and _is_authored_preset_atom(elem)
            ):
                errors.append(
                    f"{svg_path.name}: {element_id} is a <g> marked as {layer}; "
                    "Master/Layout fixed visuals must be root-level atomic elements"
                )
            if placeholder:
                errors.append(
                    f"{svg_path.name}: {element_id} cannot be both a fixed "
                    f"{layer} element and a placeholder slot"
                )

        detail_attrs = [
            attr for attr in _PPTX_PLACEHOLDER_DETAIL_ATTRS
            if elem.get(attr) is not None
        ]
        if detail_attrs and not placeholder:
            errors.append(
                f"{svg_path.name}: {element_id} uses placeholder detail metadata "
                "without data-pptx-placeholder"
            )

        if placeholder:
            if parent is not root:
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} must be a "
                    "direct child of the root <svg>"
                )
            if tag != 'g':
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} must be a "
                    "root-level <g>"
                )
            if not (elem.get('id') or '').strip():
                errors.append(
                    f"{svg_path.name}: every placeholder slot <g> requires a stable id"
                )
            wrapper_attrs = sorted(
                attr.rsplit('}', 1)[-1]
                for attr in elem.attrib
                if attr != 'id'
                and not attr.rsplit('}', 1)[-1].startswith('data-pptx-')
            )
            if wrapper_attrs:
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} is an "
                    "authoring boundary and may carry only id/data-pptx-*; remove "
                    + ', '.join(wrapper_attrs)
                )
            bounds = (elem.get('data-pptx-bounds') or '').strip()
            if not bounds:
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} requires "
                    "data-pptx-bounds"
                )
            else:
                bounds_error = _placeholder_bounds_error(bounds)
                if bounds_error:
                    errors.append(
                        f"{svg_path.name}: placeholder slot {element_id} bounds "
                        + bounds_error
                    )

            binding = (
                elem.get('data-pptx-binding') or 'carrier'
            ).strip().lower()
            if binding not in {'carrier', 'proxy'}:
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} has unknown "
                    f"binding {binding!r}; use carrier or proxy"
                )
            carrier_descendants = [
                child for child in elem.iter()
                if child is not elem
                and child.get('data-pptx-carrier') is not None
            ]
            visual_children = [
                child for child in list(elem)
                if child.tag.rsplit('}', 1)[-1] not in _NON_VISUAL_SVG_TAGS
            ]
            direct_carriers = [
                child for child in visual_children
                if (child.get('data-pptx-carrier') or '').strip().lower()
                == 'true'
            ]
            nested_carriers = [
                child for child in carrier_descendants
                if parent_by_id.get(id(child)) is not elem
            ]
            if nested_carriers:
                names = ', '.join(
                    child.get('id') or f"<{child.tag.rsplit('}', 1)[-1]}>"
                    for child in nested_carriers
                )
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} has nested "
                    f"carrier marker(s): {names}; the carrier must be a direct child"
                )
            if binding == 'carrier':
                if len(visual_children) != 1 or len(direct_carriers) != 1:
                    errors.append(
                        f"{svg_path.name}: placeholder slot {element_id} requires "
                        "exactly one visual direct child, marked "
                        "data-pptx-carrier=\"true\""
                    )
            if binding == 'proxy':
                if placeholder != 'object':
                    errors.append(
                        f"{svg_path.name}: proxy binding is allowed only for an "
                        f"object placeholder, not {placeholder!r}"
                    )
                if carrier_descendants:
                    errors.append(
                        f"{svg_path.name}: proxy placeholder slot {element_id} must "
                        "not declare a visible placeholder carrier"
                    )
                if not visual_children:
                    errors.append(
                        f"{svg_path.name}: proxy placeholder slot {element_id} must "
                        "contain visible Slide-local content"
                    )

        carrier_value = elem.get('data-pptx-carrier')
        if carrier_value is not None:
            if carrier_value.strip().lower() != 'true':
                errors.append(
                    f"{svg_path.name}: {element_id} "
                    "data-pptx-carrier must equal true"
                )
            if parent is None or not (
                parent.get('data-pptx-placeholder') or ''
            ).strip():
                errors.append(
                    f"{svg_path.name}: placeholder carrier {element_id} must be a "
                    "direct child of a root placeholder slot"
                )

        if tag in _NON_VISUAL_SVG_TAGS and (layer or placeholder):
            errors.append(
                f"{svg_path.name}: non-visual {element_id} cannot carry "
                "Master/Layout/placeholder ownership"
            )

    return list(dict.fromkeys(errors))


def _normalize_hex_rgb(value: str) -> str | None:
    """Normalize 3/4/6/8-digit HEX to alpha-free ``RRGGBB``."""
    if not HEX_VALUE_RE.fullmatch(value):
        return None
    color = value[1:]
    if len(color) in {3, 4}:
        color = ''.join(channel * 2 for channel in color)
    return color[:6].upper()


# Cheap numeric envelope for font-size role enforcement. Semantic role assignment
# is prompt-owned; Checker only verifies that a used value is close to at least
# one declared size anchor.
FONT_SIZE_ANCHOR_TOLERANCE_PX = 2.0
SPARSE_UNDECLARED_FONT_SIZE_MAX_OCCURRENCES = 2

# Oversampling alone does not imply distortion and is often harmless for small
# logos. Warn about downscaling only when the source also has material on-disk
# weight, because PPTX embeds the compressed source asset rather than raw pixels.
IMAGE_DOWNSIZE_WARN_RATIO = 4.0
IMAGE_DOWNSIZE_WARN_MIN_BYTES = 1024 * 1024

def _design_spec_kind(spec_path: Path) -> str | None:
    """Return a roster-free ``kind`` declared in design_spec.md frontmatter.

    Lightweight detector that does not require PyYAML — scans only the
    frontmatter block (``---`` delimited). Used by ``check_directory`` to
    select schema-only validation for Brand and Style workspaces instead of
    SVG-roster validation.
    """
    try:
        text = spec_path.read_text(encoding='utf-8')
    except OSError:
        return None
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---\n', 4)
    if end == -1:
        return None
    fm_block = text[4:end]
    for line in fm_block.splitlines():
        stripped = line.strip()
        match = re.fullmatch(
            r'''kind\s*:\s*(?:(['"])(brand|style)\1|(brand|style))'''
            r'''(?:\s+#.*)?\s*''',
            stripped,
        )
        if match:
            return match.group(2) or match.group(3)
    return None


def _declared_template_structure_mode(target_path: Path) -> str | None:
    """Return a template directory's explicit native structure mode."""
    directory = target_path.parent if target_path.is_file() else target_path
    spec_path = directory / 'design_spec.md'
    try:
        text = spec_path.read_text(encoding='utf-8')
    except OSError:
        return None
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---\n', 4)
    if end == -1:
        return None
    match = re.search(
        r'^native_structure_mode:\s*([A-Za-z0-9_-]+)\s*$',
        text[4:end],
        re.MULTILINE,
    )
    return match.group(1).lower() if match else None


def _declared_template_canvas_viewbox(target_path: Path) -> str | None:
    """Return a template design spec's locked root-canvas value."""
    directory = target_path.parent if target_path.is_file() else target_path
    spec_path = directory / 'design_spec.md'
    try:
        text = spec_path.read_text(encoding='utf-8')
    except OSError:
        return None
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---\n', 4)
    if end == -1:
        return None
    match = re.search(
        r'^canvas_viewbox:\s*["\']?([^"\'\r\n]+?)["\']?\s*$',
        text[4:end],
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _template_structure_checks_enabled(target_path: Path) -> bool:
    """Return whether positive structure checks apply to this template."""
    return _declared_template_structure_mode(target_path) == 'structured'


def _direct_defs_index(
    root: ET.Element,
) -> tuple[Dict[str, ET.Element], set[str]]:
    """Return direct ``<defs>`` children by id plus duplicate ids."""
    definitions: Dict[str, ET.Element] = {}
    duplicates: set[str] = set()
    for defs_elem in root.iter():
        if _local_name(defs_elem) != 'defs':
            continue
        for child in defs_elem:
            definition_id = (child.get('id') or '').strip()
            if not definition_id:
                continue
            if definition_id in definitions:
                duplicates.add(definition_id)
            definitions[definition_id] = child
    return definitions, duplicates


def _effective_presentation_value(
    elem: ET.Element,
    name: str,
    parent_by_id: Dict[int, ET.Element],
) -> str | None:
    """Resolve one inherited presentation property for validation."""
    current: ET.Element | None = elem
    while current is not None:
        style_values = (
            _parse_inline_style(current.get('style'))
            if _parse_inline_style is not None else {}
        )
        if name in style_values:
            return style_values[name]
        direct = current.get(name)
        if direct is not None:
            return direct
        current = parent_by_id.get(id(current))
    return None


def _parse_viewbox_values(viewbox: str) -> Tuple[float, float, float, float] | None:
    """Parse a root viewBox into four numeric values."""
    try:
        parsed = parse_project_viewbox(viewbox)
    except CanvasContractError:
        return None
    return 0.0, 0.0, float(parsed.width), float(parsed.height)


def _parse_placeholders_fallback(block: str) -> Dict[str, Tuple[str, ...]]:
    """Tiny YAML-free reader for the documented ``placeholders:`` shape.

    Used only when PyYAML is unavailable. Recognized lines (indentation-aware,
    two-space indent assumed):

    .. code-block:: yaml

        placeholders:
          01_cover: ["{{TITLE}}", "{{LOGO}}"]
          03_content: []
          03a_content_two_col:
            - "{{LEFT_TITLE}}"
            - "{{RIGHT_TITLE}}"

    Anything outside this minimal grammar is silently skipped — designers who
    rely on advanced YAML should install pyyaml.
    """
    out: Dict[str, Tuple[str, ...]] = {}
    inline_re = re.compile(
        r"^\s{2}([A-Za-z0-9_]+)\s*:\s*\[(.*)\]\s*$"
    )
    empty_re = re.compile(r"^\s{2}([A-Za-z0-9_]+)\s*:\s*\[\s*\]\s*$")
    block_header_re = re.compile(r"^\s{2}([A-Za-z0-9_]+)\s*:\s*$")
    item_re = re.compile(r'^\s{4}-\s*"?([^"]+)"?\s*$')

    in_section = False
    current_block_key: str | None = None
    current_items: List[str] = []

    def _flush_block() -> None:
        nonlocal current_block_key, current_items
        if current_block_key is not None:
            out[current_block_key] = tuple(current_items)
            current_block_key = None
            current_items = []

    for line in block.splitlines():
        if line.startswith("placeholders:"):
            in_section = True
            continue
        if not in_section:
            continue

        # End of section: dedent to a non-key line.
        if line and not line.startswith(" "):
            _flush_block()
            in_section = False
            continue

        if current_block_key is not None:
            m = item_re.match(line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    current_items.append(value)
                continue
            # Block ended.
            _flush_block()

        if empty_re.match(line):
            key = empty_re.match(line).group(1)
            out[key] = ()
            continue

        m = inline_re.match(line)
        if m:
            key, raw = m.group(1), m.group(2)
            items = [p.strip().strip('"').strip("'") for p in raw.split(",")]
            out[key] = tuple(item for item in items if item)
            continue

        m = block_header_re.match(line)
        if m:
            current_block_key = m.group(1)
            current_items = []
            continue

    _flush_block()
    return out


class SVGQualityChecker:
    """SVG quality checker"""

    # Default placeholder convention per page-type prefix. This is a *hint*,
    # not a hard contract: templates may define their own placeholder vocabulary
    # via `placeholders:` in design_spec.md frontmatter (see
    # references/template-designer.md §4). Missing default placeholders surface
    # as warnings, never errors — designers may legitimately swap
    # `{{THANK_YOU}}` for `{{CLOSING_MESSAGE}}`, omit `{{DATE}}` when irrelevant,
    # or build content variants with bespoke slot vocabularies.
    #
    # Variants reuse the parent type's expectation (`03a_content_two_col.svg`
    # is matched by the same `content` rules as `03_content.svg`).
    #
    # Keys are page-type tokens, not numbered stems: template numbering is
    # presentation order within one template and shifts when the optional
    # TOC page is present (`02_chapter` in a four-page roster, `03_chapter`
    # in a five-page roster with `02_toc`), so the defaults must apply to
    # both spellings.
    DEFAULT_PLACEHOLDER_CONVENTION = {
        "cover": ("{{TITLE}}",),  # only the title is universally expected
        "chapter": ("{{CHAPTER_TITLE}}",),
        "toc": (),  # TOC layouts vary too widely to assert anything
        "content": ("{{PAGE_TITLE}}",),
        "ending": (),  # ending pages legitimately use varied vocabularies
    }

    def __init__(
        self,
        *,
        template_mode: bool = False,
        quick_generate: bool = False,
    ):
        self.template_mode = template_mode
        self.quick_generate = quick_generate
        self.results = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0
        }
        self.issue_types = defaultdict(int)
        # spec_lock anchor comparison state (populated only when
        # _parse_spec_lock is available and a spec_lock.md is found near the SVG)
        self._lock_cache: Dict[Path, Dict] = {}
        self._anchor_value_summary: Dict[str, Dict[str, set]] = {
            'colors': defaultdict(set),
            'fonts': defaultdict(set),
            'sizes': defaultdict(set),
        }
        self._undeclared_size_occurrences: Counter[str] = Counter()
        self._undeclared_size_counts_ready = False
        self._lock_seen = False  # True once we locate at least one spec_lock.md
        self._source_manifest_cache: Dict[
            Path,
            Tuple[Dict, str | None],
        ] = {}
        self._source_manifest_errors_reported: set[Path] = set()
        # Template-mode aggregation (populated by check_directory when
        # template_mode=True). Each entry is (severity, kind, message) where
        # severity is 'error' or 'warning'. Printed in print_summary.
        self._template_issues: List[Tuple[str, str, str]] = []
        self._spec_only_template_kind: str | None = None
        self._animation_issues: List[Tuple[str, str]] = []
        self._illustration_issues: List[Tuple[str, str, str]] = []
        self._communication_trace_issues: List[Tuple[str, str]] = []
        self._pptx_structure_issues: List[Tuple[str, str]] = []
        self._has_incomplete_page_roster = False
        self._active_slide_count: int | None = None
        self._prototype_by_output: Dict[Path, Path] = {}
        self._active_prototype_path: Path | None = None
        self._active_template_reuse_scope: str | None = None
        self._prototype_root_cache: Dict[Path, ET.Element | None] = {}
        self._source_import_summary: Dict[str, object] = {
            'warning_count': 0,
            'by_code': {},
        }
        self._aggregate_counts_applied = False

    @staticmethod
    def _append_inherited_info(
        result: Dict,
        kind: str,
        message: str,
    ) -> None:
        """Record prototype-owned diagnostics outside the warning channel."""
        result['info'].setdefault('inherited', []).append({
            'kind': kind,
            'message': message,
        })

    def _active_prototype_root(self) -> ET.Element | None:
        """Parse the selected mirror prototype once for inherited checks."""
        if (
            self._active_template_reuse_scope != 'mirror'
            or self._active_prototype_path is None
        ):
            return None
        path = self._active_prototype_path.resolve()
        if path in self._prototype_root_cache:
            return self._prototype_root_cache[path]
        try:
            root = ET.parse(path).getroot()
            hydrate_native_payload_refs(root, path)
        except (OSError, ET.ParseError, NativePayloadError):
            root = None
        self._prototype_root_cache[path] = root
        return root

    def check_file(
        self,
        svg_file: str,
        expected_format: str = None,
        *,
        expected_viewbox: str | None = None,
        expected_viewbox_label: str = "expected canvas",
    ) -> Dict:
        """
        Check a single SVG file

        Args:
            svg_file: SVG file path
            expected_format: Expected canvas format (e.g., 'ppt169')

        Returns:
            Check result dictionary
        """
        svg_path = Path(svg_file)

        if not svg_path.exists():
            return {
                'file': str(svg_file),
                'exists': False,
                'errors': ['File does not exist'],
                'warnings': [],
                'passed': False
            }

        result = {
            'file': svg_path.name,
            'path': str(svg_path),
            'exists': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'passed': True
        }

        try:
            source_bytes = svg_path.read_bytes()
            result['source_sha256'] = hashlib.sha256(source_bytes).hexdigest()
            content = source_bytes.decode('utf-8')

            # 0. Parse XML once — every other check assumes the file is valid
            # XML. Bail early on failure so the regex-based checks below don't
            # produce misleading errors on a broken document.
            root = self._parse_xml_root(content, result)
            if root is not None:
                try:
                    hydrated_payloads = hydrate_native_payload_refs(root, svg_path)
                except NativePayloadError as exc:
                    result['errors'].append(
                        f"Invalid native payload reference: {exc}"
                    )
                else:
                    if hydrated_payloads:
                        result['info']['native_payload_refs'] = hydrated_payloads

                # 1. Check viewBox
                self._check_viewbox(
                    root,
                    svg_path,
                    result,
                    expected_format,
                    expected_viewbox=expected_viewbox,
                    expected_viewbox_label=expected_viewbox_label,
                )
                self._check_legacy_pptx_attributes(root, svg_path, result)

                # 1a. Validate exact importer transport before compatible
                # inline geometry is materialized on the shared tree.
                svg_contracts.check_nested_svg_crop_contract(root, result)

                # 2. Check forbidden elements
                svg_contracts.check_forbidden_elements(content, root, result)
                svg_contracts.check_mask_contract(root, result)

                # 2a. Validate direct geometry lengths and stroke widths.
                svg_contracts.check_geometry_length_values(root, result)

                # 2b. Validate line-presentation grammar and mappings.
                svg_contracts.check_stroke_style_values(root, result)

                # 2c. Validate image fit/crop grammar and mappings.
                self._check_image_contract(root, svg_path, result)
                svg_contracts.check_image_aspect_ratio_values(root, result)

                # 2d. Validate complete path-data and point-list grammar.
                svg_contracts.check_freeform_geometry_values(root, result)

                # 2e. Validate complete transform grammar and native mappings.
                svg_contracts.check_transform_values(root, result)

                # 2f. Validate opacity grammar and native alpha mappings.
                svg_contracts.check_opacity_values(root, result)

                # 2g. Validate the closed authoring-property surface and
                # conditional definition interfaces before export.
                svg_contracts.check_authoring_property_contract(root, result)
                svg_contracts.check_text_property_contract(root, result)
                self._check_preserved_txbody_contract(root, result)
                svg_contracts.check_paint_compatibility(root, result)
                svg_contracts.check_reference_spelling(root, result)
                svg_contracts.check_definition_contract(root, result)
                svg_contracts.check_paint_reference_contract(root, result)
                svg_contracts.check_marker_contract(root, result)
                svg_contracts.check_clip_path_contract(root, result)

                # 2h. Validate the supported shadow/glow filter interface.
                svg_contracts.check_imported_effect_status(root, result)
                svg_contracts.check_filter_effects(root, result)

                # 2i. Validate gradient definitions, stops, and coordinates.
                svg_contracts.check_gradient_interfaces(root, result)

                # 3. Check font-size values
                svg_contracts.check_font_size_values(content, result)

                # 4. Check fonts
                self._check_fonts(content, result)

                # 5. Check text wrapping methods
                self._check_text_elements(content, root, result)

                # 5b. Validate native hyperlink targets and carrier structure.
                self._check_hyperlinks(root, result)

                # 6. Check image references (file existence and resolution)
                self._check_image_references(root, svg_path, result)

                # 7. Check icon placeholders resolve before post-processing.
                self._check_icon_placeholders(root, svg_path, result)

                # 7b. Reject visual elements the native converter cannot dispatch.
                self._check_unsupported_visual_elements(root, result)

                # 7c. Fail closed on invalid PPTX preset/adjustment metadata.
                self._check_preset_geometry_metadata(root, result)
                self._check_preset_geometry_transforms(root, result)

                # 8. Check object-level animation anchor quality.
                self._check_animation_group_ids(root, svg_path, result)

                # 8b. Check <pattern> elements declare a PPTX preset.
                self._check_pattern_fills(root, result)

                # 8c. Check explicit native replacement markers before export.
                self._check_native_object_markers(root, result)

                # 8d. Validate explicit master/layout/placeholder metadata.
                if (
                    _template_structure_checks_enabled(svg_path)
                    if self.template_mode
                    else _CHECK_PPTX_STRUCTURED_PROJECT
                ):
                    self._check_pptx_structure_metadata(root, svg_path, result)

                # 8e. Validate rendering-neutral page/structure compiler hints.
                self._check_semantic_markers(root, svg_path, result)

                # 9. Compare values with spec_lock anchors. Additional colors
                #    and fonts are informational. Generated-page type sizes may
                #    stay sparse twice; the third occurrence is an error. Other
                #    spec-backed SVG locations retain advisory review. Templates
                #    do not ship a spec_lock.md, so skip in template mode.
                if not self.template_mode:
                    self._check_spec_lock_alignment(
                        content,
                        svg_path,
                        result,
                        root=root,
                    )

                # 10. Check web-sourced image attribution. Templates don't carry
                #    image_sources.json; skip in template mode.
                if not self.template_mode:
                    self._check_sourced_image_attribution(
                        root,
                        svg_path,
                        result,
                    )

            # Determine pass/fail
            result['passed'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"Failed to read file: {e}")
            result['passed'] = False

        # Update statistics
        self.summary['total'] += 1
        if result['passed']:
            if result['warnings']:
                self.summary['warnings'] += 1
            else:
                self.summary['passed'] += 1
        else:
            self.summary['errors'] += 1

        # Categorize issue types
        for error in result['errors']:
            self.issue_types[self._categorize_issue(error)] += 1

        self.results.append(result)
        return result

    def _parse_xml_root(self, content: str, result: Dict) -> ET.Element | None:
        """Parse the SVG content as well-formed XML.

        SVG is strict XML.  AI-generated decks frequently produce content that
        looks fine in HTML5-tolerant previews but fails strict XML parsing —
        common causes are HTML named entities (&nbsp; &mdash; &copy;…) and
        bare XML reserved characters in text (R&D, error < 5%).  Such pages
        cannot be exported to PPTX, so we surface them here as a hard error
        before any downstream check looks at them.

        Returns the parsed root when the document is well-formed; otherwise
        appends an error and returns None.
        """
        try:
            return ET.fromstring(content)
        except ET.ParseError as e:
            result['errors'].append(
                f"Invalid XML: {e} — SVG must be well-formed XML. "
                f"Use raw Unicode for typography (—, ©, →, NBSP); "
                f"escape XML reserved chars as &amp; &lt; &gt; &quot; &apos; "
                f"(see references/shared-standards-core.md §1)."
            )
            return None

    def _check_viewbox(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
        expected_format: str = None,
        *,
        expected_viewbox: str | None = None,
        expected_viewbox_label: str = "expected canvas",
    ):
        """Validate the root page canvas and its project-level locks."""
        viewbox = root.get('viewBox')
        try:
            parsed = parse_project_svg_root(
                root,
                context=svg_path.name,
            )
        except CanvasContractError as exc:
            result['errors'].append(str(exc))
            return
        assert viewbox is not None
        result['info']['viewbox'] = viewbox
        if viewbox != parsed.canonical or not parsed.has_integer_dimensions:
            if parsed.has_integer_dimensions:
                recommendation = f'write viewBox="{parsed.canonical}"'
            else:
                recommendation = (
                    "fractional dimensions are reserved for compatible imported "
                    "custom slide sizes; new authoring uses integer pixels"
                )
            result['warnings'].append(
                f"Compatible non-canonical root viewBox {viewbox!r}; {recommendation}."
            )

        contracts: list[tuple[str, str]] = []
        if expected_viewbox is not None:
            contracts.append((expected_viewbox_label, expected_viewbox))
        elif not self.template_mode:
            lock = self._get_spec_lock(svg_path)
            if lock is not None and 'canvas' in lock:
                locked_viewbox = lock.get('canvas', {}).get('viewBox')
                if not locked_viewbox:
                    result['errors'].append(
                        "spec_lock.md canvas section must declare viewBox"
                    )
                else:
                    contracts.append(("spec_lock canvas", locked_viewbox))

        if expected_format and expected_format in CANVAS_FORMATS:
            contracts.append((
                f"canvas format {expected_format!r}",
                CANVAS_FORMATS[expected_format]['viewbox'],
            ))
        elif expected_format:
            result['errors'].append(f"Unsupported canvas format: {expected_format}")

        seen_contracts: set[tuple[str, str]] = set()
        for label, raw_expected in contracts:
            contract_key = (label, raw_expected)
            if contract_key in seen_contracts:
                continue
            seen_contracts.add(contract_key)
            try:
                expected = parse_project_viewbox(
                    raw_expected,
                    context=f"{label} viewBox",
                )
            except CanvasContractError as exc:
                result['errors'].append(str(exc))
                continue
            if parsed != expected:
                result['errors'].append(
                    f"viewBox mismatch: {label} requires '{expected.canonical}', "
                    f"got '{parsed.canonical}'"
                )

    def _check_image_contract(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ) -> None:
        """Validate picture frames, references, and bytes before export."""
        if _project_image_errors is None:
            result['errors'].append(
                'Unable to import the image validator; cannot verify picture '
                'frames or media'
            )
            return
        _working_root, _parent_by_id, images = self._visible_image_elements(root)
        for image in images:
            result['errors'].extend(
                _project_image_errors(
                    image,
                    svg_path.parent,
                    allow_template_placeholders=self.template_mode,
                )
            )

    def _check_fonts(self, content: str, result: Dict):
        """Check font usage.

        PPTX stores concrete typefaces per run with no CSS fallback. The
        converter resolves each SVG font stack to exported latin / EA typefaces;
        validate those exported values rather than the visual-preview tail.
        """
        font_matches = self._font_family_values(content)

        if not font_matches:
            return

        result['info']['fonts'] = sorted(set(font_matches))
        if _unsafe_exported_font_faces is None:
            result['warnings'].append(
                "Unable to import svg_to_pptx font resolver; skipped exported-font safety check"
            )
            return

        for font_family in font_matches:
            unsafe = [
                f"{role}={family}"
                for role, family in _unsafe_exported_font_faces(font_family).items()
            ]
            if unsafe:
                result['warnings'].append(
                    "Font stack exports non-PPT-safe typeface(s) to PPTX "
                    f"({', '.join(unsafe)}): {font_family}"
                )
                break

    @staticmethod
    def _font_family_values(content: str) -> List[str]:
        """Extract SVG font-family values from attributes and inline styles."""
        return SVGQualityChecker._svg_property_values(content, 'font-family')

    @staticmethod
    def _svg_property_values(content: str, property_name: str) -> List[str]:
        """Extract a SVG property from direct attributes and inline styles."""
        values: List[str] = []
        attr_re = re.compile(
            rf'\b{re.escape(property_name)}\s*=\s*(["\'])(.*?)\1',
            re.IGNORECASE | re.DOTALL,
        )
        for match in attr_re.finditer(content):
            values.append(html.unescape(match.group(2)).strip())

        for match in re.finditer(r'\bstyle\s*=\s*(["\'])(.*?)\1', content, re.IGNORECASE | re.DOTALL):
            style_value = html.unescape(match.group(2))
            for part in style_value.split(';'):
                if ':' not in part:
                    continue
                name, value = part.split(':', 1)
                if name.strip().lower() == property_name.lower():
                    values.append(value.strip())
        return [value for value in values if value]

    def _check_text_elements(self, content: str, root: ET.Element, result: Dict):
        """Check text elements and wrapping methods"""
        # Count text and tspan elements
        text_count = content.count('<text')
        tspan_count = content.count('<tspan')

        result['info']['text_elements'] = text_count
        result['info']['tspan_elements'] = tspan_count

        self._check_module_bounds_contract(root, result)
        self._check_text_output_geometry(root, result)
        self._check_text_bounds(root, result)
        self._check_fragmented_paragraph_text(root, result)
        self._check_unmergeable_leading_text(root, result)
        self._check_nested_positional_tspans(root, result)

    def _check_hyperlinks(self, root: ET.Element, result: Dict) -> None:
        """Validate the standard SVG anchor surface shared with export."""
        anchors = [
            elem for elem in root.iter()
            if _local_name(elem) == 'a'
        ]
        transports = [
            elem for elem in root.iter()
            if elem.get(_SHAPE_HYPERLINK_ATTR) is not None
        ]
        if not anchors and not transports:
            return
        result['info']['hyperlinks'] = len(anchors) + len(transports)
        if _project_hyperlink_errors is None:
            result['errors'].append(
                'Unable to import hyperlink validator; cannot verify SVG links'
            )
            return
        result['errors'].extend(
            f'Invalid SVG hyperlink: {error}'
            for error in _project_hyperlink_errors(
                root,
                slide_count=self._active_slide_count,
            )
        )

    def _check_nested_positional_tspans(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Reject nested baseline jumps that DrawingML runs cannot represent."""
        if _nested_positional_tspan_errors is None:
            return
        result['errors'].extend(_nested_positional_tspan_errors(root))

    @classmethod
    def _single_line_text_runs(
        cls,
        text_el: ET.Element,
    ) -> List[Tuple[ET.Element, str]] | None:
        """Return normalized inline runs, or ``None`` for positioned text."""
        if (
            _normalize_project_text_segments is None
            or _resolve_project_xml_space is None
        ):
            return None
        raw_runs: List[Tuple[ET.Element, str, str]] = []

        def append_run(owner: ET.Element, raw: str, xml_space: str) -> None:
            if raw:
                raw_runs.append((owner, xml_space, raw))

        def collect(container: ET.Element, inherited_xml_space: str) -> bool:
            try:
                xml_space = _resolve_project_xml_space(
                    container,
                    inherited_xml_space,
                )
            except ValueError:
                return False
            if container.text:
                append_run(container, container.text, xml_space)
            for child in list(container):
                if not cls._is_tspan(child):
                    return False
                if any(child.get(name) is not None for name in ('x', 'y', 'dx', 'dy')):
                    return False
                if any(
                    name.startswith('data-paragraph-')
                    for name in child.attrib
                ):
                    return False
                if not collect(child, xml_space):
                    return False
                if child.tail:
                    append_run(container, child.tail, xml_space)
            return True

        if not collect(text_el, 'default'):
            return None
        normalized = _normalize_project_text_segments([
            (xml_space, raw)
            for _owner, xml_space, raw in raw_runs
        ])
        return [
            (raw_runs[index][0], text)
            for index, text in normalized
        ]

    @staticmethod
    def _unchanged_txbody_group_ids(
        root: ET.Element,
    ) -> set[int]:
        """Return imported shape groups whose original text body will survive."""
        if _preserved_native_text_body is None:
            return set()
        unchanged: set[int] = set()
        for group in root.iter(f'{{{SVG_NS}}}g'):
            try:
                if _preserved_native_text_body(
                    group,
                    trust_runtime_snapshot=False,
                ) is not None:
                    unchanged.add(id(group))
            except _SvgNativeConversionError:
                # The dedicated txBody contract check owns the diagnostic.
                continue
        return unchanged

    @staticmethod
    def _check_preserved_txbody_contract(
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Validate imported txBody payloads independently of text geometry."""
        if _preserved_native_text_body is None:
            return
        errors: set[str] = set()
        for group in root.iter(f'{{{SVG_NS}}}g'):
            try:
                _preserved_native_text_body(
                    group,
                    trust_runtime_snapshot=False,
                )
            except _SvgNativeConversionError as exc:
                errors.add(
                    f'{_element_label(group)} cannot preserve source '
                    f'txBody: {exc}'
                )
        result['errors'].extend(sorted(errors))

    @staticmethod
    def _has_ancestor_id(
        elem: ET.Element,
        parent_by_id: Dict[int, ET.Element],
        ancestor_ids: set[int],
    ) -> bool:
        current = parent_by_id.get(id(elem))
        while current is not None:
            if id(current) in ancestor_ids:
                return True
            current = parent_by_id.get(id(current))
        return False

    @classmethod
    def _resolved_single_line_text_runs(
        cls,
        text_el: ET.Element,
        parent_by_id: Dict[int, ET.Element],
        font_sizes: Dict[int, float],
        letter_spacings: Dict[int, float],
    ) -> List[Dict] | None:
        """Resolve the same run metrics used by generated text-frame sizing."""
        source_runs = cls._single_line_text_runs(text_el)
        if source_runs is None:
            return None
        resolved: List[Dict] = []
        for owner, text in source_runs:
            raw_weight = (
                _effective_presentation_value(
                    owner,
                    'font-weight',
                    parent_by_id,
                )
                or 'normal'
            ).strip().lower()
            weight = _parse_project_font_weight(raw_weight).canonical
            family = (
                _effective_presentation_value(
                    owner,
                    'font-family',
                    parent_by_id,
                )
                or ''
            )
            opacity_chain: List[str] = []
            current: ET.Element | None = owner
            while current is not None:
                style_values = (
                    _parse_inline_style(current.get('style'))
                    if _parse_inline_style is not None else {}
                )
                raw_opacity = style_values.get('opacity')
                if raw_opacity is None:
                    raw_opacity = current.get('opacity')
                if raw_opacity is not None:
                    opacity_chain.append(raw_opacity.strip())
                current = parent_by_id.get(id(current))
            resolved.append({
                'owner': owner,
                'text': text,
                'font_size': font_sizes[id(owner)],
                'font_weight': weight,
                'font_family': family,
                'letter_spacing': letter_spacings[id(owner)],
                'font_style': _effective_presentation_value(
                    owner,
                    'font-style',
                    parent_by_id,
                ) or 'normal',
                'text_decoration': _effective_presentation_value(
                    owner,
                    'text-decoration',
                    parent_by_id,
                ) or 'none',
                'fill_raw': _effective_presentation_value(
                    owner,
                    'fill',
                    parent_by_id,
                ) or '#000000',
                'fill_opacity': _effective_presentation_value(
                    owner,
                    'fill-opacity',
                    parent_by_id,
                ) or '1',
                'stroke_raw': _effective_presentation_value(
                    owner,
                    'stroke',
                    parent_by_id,
                ) or 'none',
                'stroke_width': _effective_presentation_value(
                    owner,
                    'stroke-width',
                    parent_by_id,
                ) or '1',
                'stroke_opacity': _effective_presentation_value(
                    owner,
                    'stroke-opacity',
                    parent_by_id,
                ) or '1',
                'opacity_chain': tuple(reversed(opacity_chain)),
            })
        return cls._coalesce_checker_text_runs(resolved)

    @staticmethod
    def _coalesce_checker_text_runs(runs: List[Dict]) -> List[Dict]:
        """Join only runs whose resolved source styles are provably equal."""
        if _detect_text_lang is None:
            return runs
        style_keys = (
            'font_size',
            'font_weight',
            'font_family',
            'letter_spacing',
            'font_style',
            'text_decoration',
            'fill_raw',
            'fill_opacity',
            'stroke_raw',
            'stroke_width',
            'stroke_opacity',
            'opacity_chain',
        )

        def signature(run: Dict) -> Tuple:
            return (
                _detect_text_lang(str(run.get('text', ''))),
                *(run.get(key) for key in style_keys),
            )

        merged: List[Dict] = []
        previous_signature: Tuple | None = None
        for run in runs:
            current_signature = signature(run)
            if merged and current_signature == previous_signature:
                candidate = {
                    **merged[-1],
                    'text': (
                        str(merged[-1].get('text', ''))
                        + str(run.get('text', ''))
                    ),
                }
                candidate_signature = signature(candidate)
                if candidate_signature == previous_signature:
                    merged[-1] = candidate
                    previous_signature = candidate_signature
                    continue
            merged.append(run)
            previous_signature = current_signature
        return merged

    def _check_text_output_geometry(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Reject measurable run advances or frames with non-positive geometry."""
        helpers = (
            _drawingml_text_frame_width_emu,
            _estimate_single_line_text_frame_width,
            _parse_project_font_weight,
            _resolve_project_font_sizes,
            _resolve_project_letter_spacings,
            _validate_single_line_text_run_advances,
        )
        if any(helper is None for helper in helpers):
            return
        try:
            font_sizes = _resolve_project_font_sizes(root)
            letter_spacings = _resolve_project_letter_spacings(root, font_sizes)
        except ValueError:
            return

        parent_by_id = {
            id(child): parent
            for parent in root.iter()
            for child in list(parent)
        }
        unchanged_groups = self._unchanged_txbody_group_ids(root)
        errors: List[str] = []
        for text_el in root.iter(f'{{{SVG_NS}}}text'):
            chain: List[ET.Element] = []
            current: ET.Element | None = text_el
            while current is not None:
                chain.append(current)
                current = parent_by_id.get(id(current))
            if any(
                _local_name(current) in _NON_VISUAL_SVG_TAGS
                for current in chain
            ):
                continue
            if self._has_ancestor_id(text_el, parent_by_id, unchanged_groups):
                continue
            try:
                runs = self._resolved_single_line_text_runs(
                    text_el,
                    parent_by_id,
                    font_sizes,
                    letter_spacings,
                )
                if not runs:
                    continue
                if not ''.join(str(run['text']) for run in runs).strip():
                    continue
                text_width = _estimate_single_line_text_frame_width(runs)
                ext_cx = _drawingml_text_frame_width_emu(
                    text_width,
                    font_sizes[id(text_el)],
                )
            except (KeyError, TypeError, ValueError):
                continue
            if ext_cx < 1:
                errors.append(
                    f'{_element_label(text_el)} negative letter-spacing '
                    'produces a non-positive DrawingML text-frame extent '
                    f'(cx={ext_cx})'
                )
                continue
            try:
                _validate_single_line_text_run_advances(runs)
            except ValueError as exc:
                errors.append(f'{_element_label(text_el)} {exc}')
        result['errors'].extend(errors)

    @classmethod
    def _positioned_text_lines(
        cls,
        text_el: ET.Element,
        parent_by_id: Dict[int, ET.Element],
        font_sizes: Dict[int, float],
        letter_spacings: Dict[int, float],
    ) -> List[Tuple[ET.Element, float, float, List[Dict], float]] | None:
        """Resolve direct positioned tspans into estimable visual lines."""
        if _parse_project_geometry_length is None:
            return None
        children = list(text_el)
        if not children or (text_el.text or '').strip():
            return None
        if any(
            not cls._is_tspan(child)
            or not cls._is_line_tspan(child)
            or child.get('x') is None
            or (child.tail or '').strip()
            for child in children
        ):
            return None

        try:
            current_y = _parse_project_geometry_length(
                text_el.get('y') or '0',
                'y',
            )
        except ValueError:
            return None

        lines: List[Tuple[ET.Element, float, float, List[Dict], float]] = []
        for child in children:
            try:
                line_x = _parse_project_geometry_length(child.get('x'), 'x')
                line_y = (
                    _parse_project_geometry_length(child.get('y'), 'y')
                    if child.get('y') is not None
                    else current_y
                )
                if child.get('dx') is not None:
                    line_x += _parse_project_geometry_length(
                        child.get('dx'),
                        'dx',
                    )
                if child.get('dy') is not None:
                    line_y += _parse_project_geometry_length(
                        child.get('dy'),
                        'dy',
                    )
                runs = cls._resolved_single_line_text_runs(
                    child,
                    parent_by_id,
                    font_sizes,
                    letter_spacings,
                )
            except (KeyError, TypeError, ValueError):
                return None
            current_y = line_y
            if not runs:
                continue
            try:
                font_size = max(float(run['font_size']) for run in runs)
            except (KeyError, TypeError, ValueError):
                return None
            lines.append((child, line_x, line_y, runs, font_size))
        return lines or None

    @classmethod
    def _estimated_text_line_bounds(
        cls,
        line_el: ET.Element,
        x: float,
        y: float,
        runs: List[Dict],
        font_size: float,
        parent_by_id: Dict[int, ET.Element],
        *,
        include_headroom: bool = True,
    ) -> Tuple[float, float, float, float] | None:
        """Estimate one line's transformed visible bounds in SVG coordinates."""
        if any(helper is None for helper in (
            _estimate_single_line_text_frame_width,
            _IDENTITY_MATRIX,
            _matrix_multiply,
            _parse_project_text_anchor,
            _parse_transform_matrix,
            _transform_point,
        )):
            return None
        try:
            width = float(_estimate_single_line_text_frame_width(
                runs,
                include_headroom=include_headroom,
            ))
            raw_anchor = (
                _effective_presentation_value(
                    line_el,
                    'text-anchor',
                    parent_by_id,
                )
                or 'start'
            ).strip().lower()
            anchor = _parse_project_text_anchor(raw_anchor).value
        except (TypeError, ValueError):
            return None
        if not all(math.isfinite(value) for value in (x, y, width, font_size)):
            return None
        if width <= 0 or font_size <= 0:
            return None

        if anchor == 'middle':
            left = x - width / 2
            right = x + width / 2
        elif anchor == 'end':
            left = x - width
            right = x
        elif anchor == 'start':
            left = x
            right = x + width
        else:
            return None
        top = y - font_size * 0.85
        bottom = y + font_size * 0.35

        return cls._transformed_rect_bounds(
            line_el,
            (left, top, right - left, bottom - top),
            parent_by_id,
        )

    @classmethod
    def _estimated_text_bounds(
        cls,
        text_el: ET.Element,
        parent_by_id: Dict[int, ET.Element],
        font_sizes: Dict[int, float],
        letter_spacings: Dict[int, float],
        *,
        include_headroom: bool = True,
    ) -> Tuple[float, float, float, float] | None:
        """Estimate one single- or multi-line text carrier's visual bounds."""
        lines: List[Tuple[ET.Element, float, float, List[Dict], float]] | None
        try:
            runs = cls._resolved_single_line_text_runs(
                text_el,
                parent_by_id,
                font_sizes,
                letter_spacings,
            )
        except (KeyError, TypeError, ValueError):
            return None
        if runs:
            try:
                lines = [(
                    text_el,
                    _parse_project_geometry_length(text_el.get('x') or '0', 'x'),
                    _parse_project_geometry_length(text_el.get('y') or '0', 'y'),
                    runs,
                    max(float(run['font_size']) for run in runs),
                )]
            except (KeyError, TypeError, ValueError):
                return None
        else:
            lines = cls._positioned_text_lines(
                text_el,
                parent_by_id,
                font_sizes,
                letter_spacings,
            )
        if not lines:
            return None

        bounds = [
            cls._estimated_text_line_bounds(
                line_el,
                x,
                y,
                line_runs,
                font_size,
                parent_by_id,
                include_headroom=include_headroom,
            )
            for line_el, x, y, line_runs, font_size in lines
        ]
        resolved = [item for item in bounds if item is not None]
        if not resolved:
            return None
        return (
            min(item[0] for item in resolved),
            min(item[1] for item in resolved),
            max(item[2] for item in resolved),
            max(item[3] for item in resolved),
        )

    @staticmethod
    def _accumulated_transform_matrix(
        element: ET.Element,
        parent_by_id: Dict[int, ET.Element],
    ):
        """Return the element-to-root transform matrix when available."""
        if any(helper is None for helper in (
            _IDENTITY_MATRIX,
            _matrix_multiply,
            _parse_transform_matrix,
        )):
            return None
        chain: List[ET.Element] = []
        current: ET.Element | None = element
        while current is not None:
            chain.append(current)
            current = parent_by_id.get(id(current))
        matrix = _IDENTITY_MATRIX
        try:
            for current in reversed(chain):
                raw_transform = current.get('transform')
                if raw_transform:
                    matrix = _matrix_multiply(
                        matrix,
                        _parse_transform_matrix(raw_transform),
                    )
        except (TypeError, ValueError):
            return None
        return matrix

    @classmethod
    def _transformed_rect_bounds(
        cls,
        element: ET.Element,
        bounds: Tuple[float, float, float, float],
        parent_by_id: Dict[int, ET.Element],
    ) -> Tuple[float, float, float, float] | None:
        """Transform one local rectangle into root SVG coordinates."""
        if _transform_point is None:
            return None
        matrix = cls._accumulated_transform_matrix(element, parent_by_id)
        if matrix is None:
            return None
        x, y, width, height = bounds
        try:
            corners = [
                _transform_point(matrix, corner_x, corner_y)
                for corner_x, corner_y in (
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height),
                )
            ]
        except (TypeError, ValueError):
            return None
        xs = [point[0] for point in corners]
        ys = [point[1] for point in corners]
        return min(xs), min(ys), max(xs), max(ys)

    @classmethod
    def _transformed_rect_edge_lengths(
        cls,
        element: ET.Element,
        bounds: Tuple[float, float, float, float],
        parent_by_id: Dict[int, ET.Element],
    ) -> Tuple[float, float] | None:
        """Return frame-axis lengths after accumulated SVG transforms."""
        if _transform_point is None:
            return None
        matrix = cls._accumulated_transform_matrix(element, parent_by_id)
        if matrix is None:
            return None
        x, y, width, height = bounds
        try:
            origin = _transform_point(matrix, x, y)
            width_end = _transform_point(matrix, x + width, y)
            height_end = _transform_point(matrix, x, y + height)
        except (TypeError, ValueError):
            return None
        rendered_w = math.hypot(
            width_end[0] - origin[0],
            width_end[1] - origin[1],
        )
        rendered_h = math.hypot(
            height_end[0] - origin[0],
            height_end[1] - origin[1],
        )
        if rendered_w <= 0 or rendered_h <= 0:
            return None
        return rendered_w, rendered_h

    @staticmethod
    def _resolved_root_module_bounds(
        group: ET.Element,
    ) -> Tuple[str, Tuple[float, float, float, float]] | None:
        """Return one root module's explicit boundary in root coordinates."""
        raw = group.get(_BOUNDS_ATTR)
        if raw is None:
            return None
        try:
            x, y, width, height = _parse_positive_bounds(raw)
        except ValueError:
            return None
        return _BOUNDS_ATTR, (x, y, x + width, y + height)

    @staticmethod
    def _bounds_overflow_metrics(
        inner: Tuple[float, float, float, float],
        outer: Tuple[float, float, float, float],
        *,
        tolerance: float = _BOUNDS_OVERFLOW_TOLERANCE,
    ) -> Tuple[str, float, float] | None:
        """Return overflow axes and ratios relative to the outer dimensions."""
        left, top, right, bottom = inner
        outer_left, outer_top, outer_right, outer_bottom = outer
        left_overflow = max(outer_left - left, 0.0)
        right_overflow = max(right - outer_right, 0.0)
        top_overflow = max(outer_top - top, 0.0)
        bottom_overflow = max(bottom - outer_bottom, 0.0)
        horizontal = (
            left_overflow > tolerance
            or right_overflow > tolerance
        )
        vertical = (
            top_overflow > tolerance
            or bottom_overflow > tolerance
        )
        if not horizontal and not vertical:
            return None

        outer_width = outer_right - outer_left
        outer_height = outer_bottom - outer_top
        if outer_width <= 0.0 or outer_height <= 0.0:
            return None
        horizontal_ratio = (
            max(left_overflow, right_overflow) / outer_width
            if horizontal else 0.0
        )
        vertical_ratio = (
            max(top_overflow, bottom_overflow) / outer_height
            if vertical else 0.0
        )
        if horizontal and vertical:
            axes = 'horizontal and vertical'
        elif horizontal:
            axes = 'horizontal'
        else:
            axes = 'vertical'
        return axes, horizontal_ratio, vertical_ratio

    @staticmethod
    def _bounds_are_disjoint(
        first: Tuple[float, float, float, float],
        second: Tuple[float, float, float, float],
    ) -> bool:
        """Return whether two root-coordinate rectangles do not intersect."""
        left, top, right, bottom = first
        other_left, other_top, other_right, other_bottom = second
        return (
            right <= other_left
            or left >= other_right
            or bottom <= other_top
            or top >= other_bottom
        )

    @classmethod
    def _is_off_canvas_morph_group(
        cls,
        group: ET.Element,
        canvas: Tuple[float, float, float, float],
    ) -> bool:
        """Return whether a group declares one wholly off-canvas Morph state."""
        if group.get(_MORPH_STAGING_ATTR) != 'true':
            return False
        resolved = cls._resolved_root_module_bounds(group)
        return (
            resolved is not None
            and cls._bounds_are_disjoint(resolved[1], canvas)
        )

    @classmethod
    def _record_bounds_overflow(
        cls,
        result: Dict,
        *,
        subject: str,
        inner: Tuple[float, float, float, float],
        container: str,
        outer: Tuple[float, float, float, float],
        repair: str,
    ) -> None:
        """Record a warning through 5% overflow and an error above it."""
        metrics = cls._bounds_overflow_metrics(inner, outer)
        if metrics is None:
            return
        axes, horizontal_ratio, vertical_ratio = metrics
        overflow_ratio = max(horizontal_ratio, vertical_ratio)
        exceeds_error_ratio = (
            overflow_ratio > _BOUNDS_OVERFLOW_ERROR_RATIO
            and not math.isclose(
                overflow_ratio,
                _BOUNDS_OVERFLOW_ERROR_RATIO,
                rel_tol=0.0,
                abs_tol=1e-9,
            )
        )
        bucket = (
            result['errors']
            if exceeds_error_ratio
            else result['warnings']
        )
        left, top, right, bottom = inner
        outer_left, outer_top, outer_right, outer_bottom = outer
        bucket.append(
            f'{subject} exceeds {container} on the {axes} axis: '
            f'content ({left:.1f}, {top:.1f})-({right:.1f}, '
            f'{bottom:.1f}), container ({outer_left:.1f}, '
            f'{outer_top:.1f})-({outer_right:.1f}, '
            f'{outer_bottom:.1f}), overflow horizontal '
            f'{horizontal_ratio:.1%}, vertical {vertical_ratio:.1%}; '
            f'{repair}'
        )

    @classmethod
    def _record_canvas_text_overflow(
        cls,
        result: Dict,
        *,
        subject: str,
        inner: Tuple[float, float, float, float],
        canvas: Tuple[float, float, float, float],
    ) -> bool:
        """Record one page-boundary error and return whether it overflowed."""
        metrics = cls._bounds_overflow_metrics(inner, canvas)
        if metrics is None:
            return False
        axes, horizontal_ratio, vertical_ratio = metrics
        left, top, right, bottom = inner
        canvas_left, canvas_top, canvas_right, canvas_bottom = canvas
        result['errors'].append(
            f'{subject} exceeds the root viewBox on the {axes} axis: '
            f'content ({left:.1f}, {top:.1f})-({right:.1f}, '
            f'{bottom:.1f}), canvas ({canvas_left:.1f}, '
            f'{canvas_top:.1f})-({canvas_right:.1f}, '
            f'{canvas_bottom:.1f}), overflow horizontal '
            f'{horizontal_ratio:.1%}, vertical {vertical_ratio:.1%}; '
            'move or reflow the text until its estimated bounds stay on-page'
        )
        return True

    @staticmethod
    def _text_diagnostic_label(text_element: ET.Element) -> str:
        """Return a locatable label for one SVG text carrier."""
        label = _element_label(text_element)
        if (text_element.get('id') or '').strip():
            return label

        details: List[str] = []
        raw_x = (text_element.get('x') or '').strip()
        raw_y = (text_element.get('y') or '').strip()
        if raw_x or raw_y:
            details.append(f'x={raw_x or "?"}, y={raw_y or "?"}')
        snippet = re.sub(r'\s+', ' ', ''.join(text_element.itertext())).strip()
        if snippet:
            preview = snippet[:20] + ('…' if len(snippet) > 20 else '')
            details.append(f'text={preview!r}')
        return f'{label} ({"; ".join(details)})' if details else label

    @staticmethod
    def _is_hidden_element(
        element: ET.Element,
        parent_by_id: Dict[int, ET.Element],
    ) -> bool:
        """Return whether inherited display or visibility hides an element."""
        current: ET.Element | None = element
        while current is not None:
            style_values = (
                _parse_inline_style(current.get('style'))
                if _parse_inline_style is not None
                else {}
            )
            display = style_values.get('display')
            if display is None:
                display = current.get('display')
            if display and display.strip().lower() == 'none':
                return True
            current = parent_by_id.get(id(current))
        visibility = (
            _effective_presentation_value(
                element,
                'visibility',
                parent_by_id,
            )
            or ''
        ).strip().lower()
        return visibility in {'hidden', 'collapse'}

    @staticmethod
    def _has_zero_opacity(
        element: ET.Element,
        parent_by_id: Dict[int, ET.Element],
    ) -> bool:
        """Return whether an element or ancestor has zero effective opacity."""
        current: ET.Element | None = element
        while current is not None:
            style_values = (
                _parse_inline_style(current.get('style'))
                if _parse_inline_style is not None
                else {}
            )
            raw = style_values.get('opacity')
            if raw is None:
                raw = current.get('opacity')
            if raw is not None:
                value = raw.strip()
                try:
                    opacity = (
                        float(value[:-1]) / 100
                        if value.endswith('%')
                        else float(value)
                    )
                except ValueError:
                    pass
                else:
                    if opacity <= 0:
                        return True
            current = parent_by_id.get(id(current))
        return False

    @classmethod
    def _visible_image_elements(
        cls,
        root: ET.Element,
    ) -> Tuple[ET.Element, Dict[int, ET.Element], List[ET.Element]]:
        """Return rendered image instances after expanding static local uses."""
        working_root = copy.deepcopy(root)
        if (
            _expand_local_use_references is not None
            and _UseExpansionError is not None
        ):
            try:
                _expand_local_use_references(working_root)
            except _UseExpansionError:
                # The local-reference validator owns the actionable failure.
                working_root = copy.deepcopy(root)

        parent_by_id = {
            id(child): parent
            for parent in working_root.iter()
            for child in list(parent)
        }
        images = [
            element
            for element in working_root.iter(f'{{{SVG_NS}}}image')
            if not cls._is_hidden_element(element, parent_by_id)
            and not cls._has_non_visual_ancestor(
                element,
                working_root,
                parent_by_id,
            )
            and not cls._has_zero_opacity(element, parent_by_id)
        ]
        return working_root, parent_by_id, images

    @staticmethod
    def _has_non_visual_ancestor(
        element: ET.Element,
        module: ET.Element,
        parent_by_id: Dict[int, ET.Element],
    ) -> bool:
        """Return whether an element lives in a non-rendered module subtree."""
        current: ET.Element | None = element
        while current is not None and current is not module:
            if _local_name(current) in _NON_VISUAL_SVG_TAGS:
                return True
            current = parent_by_id.get(id(current))
        return False

    def _check_module_bounds_contract(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Validate direct root module boundaries in the SVG canvas."""
        parent_by_id = {
            id(child): parent
            for parent in root.iter()
            for child in list(parent)
        }
        viewbox = _parse_viewbox_values(root.get('viewBox') or '')
        canvas = None
        if viewbox is not None:
            x, y, width, height = viewbox
            canvas = (x, y, x + width, y + height)

        for element in root.iter():
            if element.get(_BOUNDS_ATTR) is None:
                continue
            if _local_name(element) != 'g':
                result['errors'].append(
                    f'{_element_label(element)} {_BOUNDS_ATTR} is valid '
                    'only on <g> layout modules'
                )

        for element in root.iter():
            raw_staging = element.get(_MORPH_STAGING_ATTR)
            if raw_staging is None:
                continue
            label = _element_label(element)
            if raw_staging != 'true':
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} must equal "true"; '
                    'set the exact value or remove the marker'
                )
                continue
            if _local_name(element) != 'g':
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} is valid only on <g>; '
                    'move it to the enclosing ordinary direct-root group'
                )
                continue
            if parent_by_id.get(id(element)) is not root:
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} requires a direct-root '
                    '<g>; move the marked group directly under <svg> or remove '
                    'the marker'
                )
                continue
            if not (element.get('id') or '').strip():
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} requires a stable non-empty '
                    'id; add an id to the marked direct-root group'
                )
                continue
            incompatible = [
                attribute
                for attribute in (
                    'data-pptx-layer',
                    'data-pptx-placeholder',
                )
                if element.get(attribute) is not None
            ]
            if incompatible:
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} cannot be combined with '
                    f'{", ".join(incompatible)}; use an ordinary Slide-local '
                    'group or remove the marker'
                )
                continue
            resolved = self._resolved_root_module_bounds(element)
            if resolved is None:
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} requires valid '
                    f'{_BOUNDS_ATTR}; add or fix positive root-coordinate '
                    'x y width height bounds'
                )
                continue
            if canvas is None:
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} cannot verify an off-canvas '
                    'endpoint without a valid root viewBox; fix the root viewBox'
                )
                continue
            if not self._bounds_are_disjoint(resolved[1], canvas):
                result['errors'].append(
                    f'{label} {_MORPH_STAGING_ATTR} requires wholly off-canvas '
                    f'{_BOUNDS_ATTR}; move the full bounds outside the root '
                    'viewBox or remove the marker from partially visible content'
                )

        missing: List[str] = []
        root_groups = [
            child
            for child in list(root)
            if _local_name(child) == 'g'
        ]
        require_bounds = (
            self.template_mode
            or root.get('data-pptx-page-role') is not None
            or any(
                root.get(attribute) is not None
                for attribute in _PPTX_ROOT_STRUCTURE_ATTRS
            )
        )
        for group in root_groups:
            if self._is_hidden_element(group, parent_by_id):
                continue
            raw_bounds = group.get(_BOUNDS_ATTR)
            if raw_bounds is None:
                missing.append(_element_label(group))
                continue
            try:
                _parse_positive_bounds(raw_bounds)
            except ValueError as exc:
                result['errors'].append(
                    f'{_element_label(group)} {_BOUNDS_ATTR} {exc}'
                )
                continue

            resolved = self._resolved_root_module_bounds(group)
            if resolved is None or canvas is None:
                continue
            if self._is_off_canvas_morph_group(group, canvas):
                continue
            attribute, bounds = resolved
            self._record_bounds_overflow(
                result,
                subject=f'{_element_label(group)} {attribute}',
                inner=bounds,
                container='canvas viewBox',
                outer=canvas,
                repair=(
                    'keep the root module subcanvas inside the SVG viewBox'
                ),
            )

        if missing:
            sample = '; '.join(missing[:3])
            suffix = '' if len(missing) <= 3 else f'; +{len(missing) - 3} more'
            bucket = result['errors'] if require_bounds else result['warnings']
            prefix = 'Detected' if require_bounds else 'Reference SVG: detected'
            bucket.append(
                f'{prefix} {len(missing)} visible root-level <g> '
                f'module(s) without explicit {_BOUNDS_ATTR} '
                f'({sample}{suffix}); every final-page/template root <g> declares '
                'its root-coordinate layout subcanvas even when it also carries '
                'data-pptx-frame or native chart/table coordinates'
            )

    def _check_text_bounds(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Validate visible text against page and root-module bounds."""
        helpers = (
            _estimate_single_line_text_frame_width,
            _parse_project_font_weight,
            _parse_project_geometry_length,
            _parse_project_text_anchor,
            _resolve_project_font_sizes,
            _resolve_project_letter_spacings,
        )
        if any(helper is None for helper in helpers):
            return
        try:
            font_sizes = _resolve_project_font_sizes(root)
            letter_spacings = _resolve_project_letter_spacings(
                root,
                font_sizes,
            )
        except ValueError:
            return

        parent_by_id = {
            id(child): parent
            for parent in root.iter()
            for child in list(parent)
        }
        unchanged_groups = self._unchanged_txbody_group_ids(root)
        viewbox = _parse_viewbox_values(root.get('viewBox') or '')
        canvas = None
        if viewbox is not None:
            x, y, width, height = viewbox
            canvas = (x, y, x + width, y + height)

        estimated_by_id: Dict[
            int,
            Tuple[float, float, float, float],
        ] = {}
        page_overflow_text_ids: set[int] = set()
        unverified: List[str] = []
        for text_element in root.iter(f'{{{SVG_NS}}}text'):
            if self._has_ancestor_id(
                text_element,
                parent_by_id,
                unchanged_groups,
            ):
                continue
            if self._has_non_visual_ancestor(
                text_element,
                root,
                parent_by_id,
            ):
                continue
            if self._is_hidden_element(text_element, parent_by_id):
                continue
            visible_text = ''.join(text_element.itertext())
            if (
                not visible_text.strip()
                or ('{{' in visible_text and '}}' in visible_text)
            ):
                continue
            estimated = self._estimated_text_bounds(
                text_element,
                parent_by_id,
                font_sizes,
                letter_spacings,
                include_headroom=True,
            )
            if estimated is not None:
                estimated_by_id[id(text_element)] = estimated

            if (
                canvas is None
                or self._has_zero_opacity(text_element, parent_by_id)
            ):
                continue

            page_estimated = self._estimated_text_bounds(
                text_element,
                parent_by_id,
                font_sizes,
                letter_spacings,
                include_headroom=False,
            )
            if page_estimated is None:
                unverified.append(self._text_diagnostic_label(text_element))
                continue
            direct_child = text_element
            parent = parent_by_id.get(id(direct_child))
            while parent is not None and parent is not root:
                direct_child = parent
                parent = parent_by_id.get(id(direct_child))
            morph_staging = (
                parent is root
                and _local_name(direct_child) == 'g'
                and self._is_off_canvas_morph_group(
                    direct_child,
                    canvas,
                )
                and self._bounds_are_disjoint(page_estimated, canvas)
            )
            if (
                not morph_staging
                and self._record_canvas_text_overflow(
                    result,
                    subject=self._text_diagnostic_label(text_element),
                    inner=page_estimated,
                    canvas=canvas,
                )
            ):
                page_overflow_text_ids.add(id(text_element))

        if unverified:
            sample = ', '.join(unverified[:3])
            suffix = (
                ''
                if len(unverified) <= 3
                else f', +{len(unverified) - 3} more'
            )
            result['warnings'].append(
                'Cannot verify root viewBox bounds for visible text with '
                f'unsupported or unresolved geometry: {sample}{suffix}; use '
                'supported explicit text positioning when page fit matters'
            )

        root_groups = [
            child
            for child in list(root)
            if _local_name(child) == 'g'
        ]
        for module in root_groups:
            if self._is_hidden_element(module, parent_by_id):
                continue
            resolved_module = self._resolved_root_module_bounds(module)
            if resolved_module is None:
                continue
            boundary_attribute, boundary = resolved_module
            for text_element in module.iter(f'{{{SVG_NS}}}text'):
                if id(text_element) in page_overflow_text_ids:
                    continue
                estimated = estimated_by_id.get(id(text_element))
                if estimated is None:
                    continue
                self._record_bounds_overflow(
                    result,
                    subject=self._text_diagnostic_label(text_element),
                    inner=estimated,
                    container=(
                        f'{_element_label(module)} {boundary_attribute}'
                    ),
                    outer=boundary,
                    repair=(
                        'expand the root module bounds into available '
                        'non-overlapping space; otherwise reflow the text'
                    ),
                )

    def _check_unmergeable_leading_text(self, root: ET.Element, result: Dict) -> None:
        """Warn when leading text cannot be normalized into one PPT text frame."""
        risky = []
        for text_el in root.iter(f'{{{SVG_NS}}}text'):
            if not (text_el.text or "").strip():
                continue
            children = list(text_el)
            if not any(self._is_line_tspan(child) for child in children):
                continue

            reason = self._leading_text_normalizer_reject_reason(text_el)
            if reason is not None:
                risky.append(reason)

        if risky:
            sample = '; '.join(risky[:3])
            suffix = '' if len(risky) <= 3 else f"; +{len(risky) - 3} more"
            result['warnings'].append(
                "Detected multi-line <text> with leading direct text that cannot "
                f"be normalized into one PPT text frame ({sample}{suffix})"
            )

    def _check_fragmented_paragraph_text(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Warn on high-confidence prose lines split into sibling text frames."""
        helpers = (
            _parse_project_geometry_length,
            _resolve_project_font_sizes,
        )
        if any(helper is None for helper in helpers):
            return
        try:
            font_sizes = _resolve_project_font_sizes(root)
        except ValueError:
            return

        parent_by_id = {
            id(child): parent
            for parent in root.iter()
            for child in list(parent)
        }
        unchanged_groups = self._unchanged_txbody_group_ids(root)
        style_properties = (
            'fill',
            'fill-opacity',
            'font-family',
            'font-style',
            'font-weight',
            'letter-spacing',
            'opacity',
            'stroke',
            'stroke-opacity',
            'stroke-width',
            'text-decoration',
        )

        def line_record(element: ET.Element) -> Dict | None:
            if (
                _local_name(element) != 'text'
                or list(element)
                or element.get('x') is None
                or element.get('y') is None
                or any(element.get(name) is not None for name in ('dx', 'dy'))
                or element.get('transform') is not None
                or self._is_hidden_element(element, parent_by_id)
                or self._has_ancestor_id(
                    element,
                    parent_by_id,
                    unchanged_groups,
                )
            ):
                return None
            text = (element.text or '').strip()
            compact_text = re.sub(r'\s+', '', text)
            if (
                not compact_text
                or ('{{' in text and '}}' in text)
                or _PARAGRAPH_LIST_MARKER_RE.match(text)
            ):
                return None
            anchor = (
                _effective_presentation_value(
                    element,
                    'text-anchor',
                    parent_by_id,
                )
                or 'start'
            ).strip().lower()
            if anchor != 'start':
                return None
            try:
                x = _parse_project_geometry_length(element.get('x'), 'x')
                y = _parse_project_geometry_length(element.get('y'), 'y')
                font_size = float(font_sizes[id(element)])
            except (KeyError, TypeError, ValueError):
                return None
            if font_size <= 0:
                return None
            style = tuple(
                (
                    _effective_presentation_value(
                        element,
                        name,
                        parent_by_id,
                    )
                    or ''
                ).strip().lower()
                for name in style_properties
            )
            return {
                'chars': len(compact_text),
                'font_size': font_size,
                'style': style,
                'text': text,
                'x': x,
                'y': y,
            }

        suspects: List[str] = []
        for group in list(root):
            if (
                _local_name(group) != 'g'
                or self._is_hidden_element(group, parent_by_id)
            ):
                continue
            current_run: List[Dict] = []

            def flush_run() -> None:
                if len(current_run) < 2:
                    return
                total_chars = sum(line['chars'] for line in current_run)
                longest_line = max(line['chars'] for line in current_run)
                if (
                    total_chars < _PARAGRAPH_LINE_MIN_TOTAL_CHARS
                    or longest_line < _PARAGRAPH_LINE_MIN_LONGEST_CHARS
                ):
                    return
                first = current_run[0]
                last = current_run[-1]
                suspects.append(
                    f'{_element_label(group)} x={first["x"]:.1f}, '
                    f'y={first["y"]:.1f}..{last["y"]:.1f}, '
                    f'{len(current_run)} lines'
                )

            for child in list(group):
                line = line_record(child)
                if line is None:
                    flush_run()
                    current_run = []
                    continue
                if current_run:
                    previous = current_run[-1]
                    line_gap = line['y'] - previous['y']
                    same_frame = (
                        abs(line['x'] - previous['x'])
                        <= _PARAGRAPH_LINE_X_TOLERANCE
                        and line['style'] == previous['style']
                        and math.isclose(
                            line['font_size'],
                            previous['font_size'],
                            rel_tol=0.0,
                            abs_tol=1e-6,
                        )
                        and line_gap
                        >= line['font_size'] * _PARAGRAPH_LINE_GAP_MIN_RATIO
                        and line_gap
                        <= line['font_size'] * _PARAGRAPH_LINE_GAP_MAX_RATIO
                        and not _PARAGRAPH_LINE_TERMINATOR_RE.search(
                            previous['text']
                        )
                    )
                    if not same_frame:
                        flush_run()
                        current_run = []
                current_run.append(line)
            flush_run()

        if not suspects:
            return
        sample = '; '.join(suspects[:3])
        suffix = '' if len(suspects) <= 3 else f'; +{len(suspects) - 3} more'
        result['warnings'].append(
            f'Detected {len(suspects)} paragraph-like line run(s) split '
            f'across sibling <text> elements ({sample}{suffix}). If each run '
            'is one prose paragraph, combine it into one <text>: keep its '
            'first line as direct text and use direct <tspan> children with '
            'the parent x and positive relative dy values for later lines. '
            'An all-<tspan> form may start with dy="0". Keep semantically '
            'independent text frames separate.'
        )

    @staticmethod
    def _is_tspan(elem: ET.Element) -> bool:
        return elem.tag == f'{{{SVG_NS}}}tspan'

    @classmethod
    def _is_line_tspan(cls, elem: ET.Element) -> bool:
        if not cls._is_tspan(elem):
            return False
        if elem.get('x') is not None or elem.get('y') is not None:
            return True
        dy = elem.get('dy')
        if dy is None:
            return False
        try:
            return float(re.match(r'^[\s,]*([+-]?(?:\d+\.?\d*|\d*\.\d+))', dy).group(1)) != 0
        except (AttributeError, ValueError):
            return True

    @classmethod
    def _leading_text_normalizer_reject_reason(cls, text_el: ET.Element) -> str | None:
        if text_el.get('x') is None:
            return '<text> has no x anchor'

        for child in list(text_el):
            if not cls._is_tspan(child):
                return '<text> has non-tspan child'
            if (child.tail or "").strip():
                return '<tspan> has non-empty tail text'

        return None

    def _check_image_references(self, root: ET.Element, svg_path: Path, result: Dict):
        """Check image file existence and effective rendered resolution."""
        svg_dir = svg_path.parent
        working_root, parent_by_id, images = self._visible_image_elements(root)

        for image in images:
            href = image.get('href') or image.get(f'{{{XLINK_NS}}}href')
            if not href or href.startswith('data:'):
                continue
            if self.template_mode and '{{' in href and '}}' in href:
                continue
            if _resolve_external_image_reference is None:
                result['warnings'].append(
                    "Detected image references, but shared image resolver could not be imported; "
                    "export will still validate them."
                )
                return

            img_path = _resolve_external_image_reference(svg_dir, href)
            if img_path is None:
                # The shared image-source contract already reports the
                # blocking resolution failure. This pass adds quality advice
                # only for valid, resolved images.
                continue

            # Check resolution vs display size
            display_owner = image
            parent = parent_by_id.get(id(image))
            if (
                parent is not None
                and parent is not working_root
                and parent.tag == f'{{{SVG_NS}}}svg'
            ):
                # Imported crops use a unit-frame inner image. Quality advice
                # must compare the source against the visible outer frame.
                display_owner = parent
            display_w_str = display_owner.get('width')
            display_h_str = display_owner.get('height')
            if not display_w_str or not display_h_str:
                continue

            try:
                display_x = float(display_owner.get('x') or '0')
                display_y = float(display_owner.get('y') or '0')
                local_display_w = float(display_w_str)
                local_display_h = float(display_h_str)
            except (ValueError, TypeError):
                continue
            if local_display_w <= 0 or local_display_h <= 0:
                continue
            display_w = local_display_w
            display_h = local_display_h
            transformed_size = self._transformed_rect_edge_lengths(
                display_owner,
                (display_x, display_y, local_display_w, local_display_h),
                parent_by_id,
            )
            if transformed_size is not None:
                display_w, display_h = transformed_size
            axis_scale_x = display_w / local_display_w
            axis_scale_y = display_h / local_display_h

            try:
                from PIL import Image as PILImage, ImageOps
                with PILImage.open(img_path) as img:
                    actual_w, actual_h = ImageOps.exif_transpose(img).size
                source_bytes = img_path.stat().st_size

                visible_w = float(actual_w)
                visible_h = float(actual_h)
                fit_owner = image
                if display_owner is not image:
                    fit_owner = display_owner
                    viewbox = (display_owner.get('viewBox') or '').split()
                    if len(viewbox) == 4:
                        try:
                            viewbox_w = float(viewbox[2])
                            viewbox_h = float(viewbox[3])
                        except ValueError:
                            pass
                        else:
                            if 0 < viewbox_w <= 1 and 0 < viewbox_h <= 1:
                                visible_w *= viewbox_w
                                visible_h *= viewbox_h

                raw_aspect = fit_owner.get('preserveAspectRatio')
                try:
                    align, mode = (
                        _parse_project_image_aspect_ratio(raw_aspect)
                        if _parse_project_image_aspect_ratio is not None
                        else ('xMidYMid', 'meet')
                    )
                except ValueError:
                    continue

                local_scale_x = local_display_w / visible_w
                local_scale_y = local_display_h / visible_h
                if align == 'none':
                    render_scale = max(
                        local_scale_x * axis_scale_x,
                        local_scale_y * axis_scale_y,
                    )
                    fit_label = 'none'
                elif mode == 'slice':
                    render_scale = (
                        max(local_scale_x, local_scale_y)
                        * max(axis_scale_x, axis_scale_y)
                    )
                    fit_label = 'slice'
                else:
                    render_scale = (
                        min(local_scale_x, local_scale_y)
                        * max(axis_scale_x, axis_scale_y)
                    )
                    fit_label = 'meet'

                if render_scale > 1.0:
                    result['warnings'].append(
                        f"Image {href} is {actual_w}x{actual_h} and renders at "
                        f"{render_scale:.2f}x scale in a "
                        f"{int(display_w)}x{int(display_h)} {fit_label} frame "
                        "— may appear blurry"
                    )
                elif (
                    render_scale < 1.0 / IMAGE_DOWNSIZE_WARN_RATIO
                    and source_bytes >= IMAGE_DOWNSIZE_WARN_MIN_BYTES
                ):
                    source_mib = source_bytes / (1024 * 1024)
                    result['warnings'].append(
                        f"Image {href} is {actual_w}x{actual_h} and renders at "
                        f"{render_scale:.2f}x scale in a "
                        f"{int(display_w)}x{int(display_h)} {fit_label} frame; "
                        f"the source is {source_mib:.1f} MiB — file-size "
                        "advisory only, not an aspect-ratio warning; consider "
                        "a smaller source asset"
                    )
            except ImportError:
                pass  # PIL not available, skip resolution check
            except Exception:
                pass  # Image unreadable, skip resolution check

    def _check_icon_placeholders(self, root: ET.Element, svg_path: Path, result: Dict) -> None:
        """Check that <use data-icon="..."> placeholders resolve."""
        placeholders = [
            elem for elem in root.iter()
            if _local_name(elem).lower() == 'use' and elem.get('data-icon') is not None
        ]
        if not placeholders:
            return

        if _resolve_icon_path is None:
            result['warnings'].append(
                "Detected data-icon placeholders, but icon resolver could not be imported; "
                "post-processing/export will still validate them."
            )
            return
        if _icon_search_dirs_for_svg is None:
            result['warnings'].append(
                "Detected data-icon placeholders, but shared icon search helper could not be imported; "
                "post-processing/export will still validate them."
            )
            return

        icons_dir, fallback_dir = _icon_search_dirs_for_svg(svg_path)
        require_project_local = self._requires_project_local_icons(svg_path)
        project_icons_dir = (
            _project_root_for_svg_path(svg_path) / 'icons'
            if _project_root_for_svg_path is not None
            else None
        )
        seen = set()
        for elem in placeholders:
            icon_name = (elem.get('data-icon') or '').strip()
            if not icon_name:
                result['errors'].append("Icon placeholder has empty data-icon value")
                continue
            if icon_name in seen:
                continue
            seen.add(icon_name)

            if require_project_local and project_icons_dir is not None:
                local_path, _ = _resolve_icon_path(
                    icon_name,
                    project_icons_dir,
                    None,
                )
                if not local_path.exists():
                    result['errors'].append(
                        f"Icon is not prepared in the project: {icon_name} "
                        f"(expected under {project_icons_dir}); return to "
                        "Strategist preparation instead of using the global fallback"
                    )
                    continue

            icon_path, _ = _resolve_icon_path(icon_name, icons_dir, fallback_dir)
            if not icon_path.exists():
                fallback_msg = f", then {fallback_dir}" if fallback_dir else ""
                suggestion = (
                    _suggest_icon_name(icon_name, icons_dir, fallback_dir)
                    if _suggest_icon_name is not None else None
                )
                hint = (
                    f"; identifiers are case-sensitive; use '{suggestion}'"
                    if suggestion else ""
                )
                result['errors'].append(
                    f"Icon not found: {icon_name} (searched {icons_dir}"
                    f"{fallback_msg}){hint}"
                )
                continue
            try:
                icon_root = ET.parse(icon_path).getroot()
                hydrated = hydrate_native_payload_refs(icon_root, icon_path)
            except (OSError, ET.ParseError, NativePayloadError) as exc:
                result['errors'].append(
                    f"Icon {icon_name} has invalid native payload metadata: {exc}"
                )
                continue
            if _project_mask_errors is not None:
                result['errors'].extend(
                    f'Icon {icon_name}: {error}'
                    for error in _project_mask_errors(icon_root)
                )
            if hydrated:
                result['info']['native_icon_payload_refs'] = (
                    result['info'].get('native_icon_payload_refs', 0) + hydrated
                )

    @staticmethod
    def _requires_project_local_icons(svg_path: Path) -> bool:
        """Return whether a generated page belongs to a versioned project."""
        if svg_path.parent.name != 'svg_output' or _project_root_for_svg_path is None:
            return False
        lock_path = _project_root_for_svg_path(svg_path) / 'spec_lock.md'
        try:
            first_line = next(
                (
                    line.strip()
                    for line in lock_path.read_text(encoding='utf-8-sig').splitlines()
                    if line.strip()
                ),
                '',
            )
        except OSError:
            return False
        return bool(
            re.fullmatch(
                r'<!--[ \t]+ppt-master-schema:[ \t]*spec-lock/v[1-9][0-9]*[ \t]+-->',
                first_line,
                re.IGNORECASE,
            )
        )

    def _check_unsupported_visual_elements(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Reject authored visual elements with no native converter dispatch."""
        if _collect_unsupported_visuals is None:
            result['errors'].append(
                "Unable to import native visual-element preflight; "
                "cannot verify SVG element support"
            )
            return
        if _expand_local_use_references is None or _UseExpansionError is None:
            result['errors'].append(
                "Unable to import local <use> expansion; "
                "cannot verify SVG element support"
            )
            return

        expanded_root = copy.deepcopy(root)
        try:
            _expand_local_use_references(expanded_root)
        except _UseExpansionError:
            # _check_forbidden_elements already reports the actionable
            # local-reference validation error.
            return

        unsupported = _collect_unsupported_visuals(
            expanded_root,
            allow_data_icon_use=True,
        )
        if not unsupported:
            return

        preview = '; '.join(unsupported[:8])
        suffix = '' if len(unsupported) <= 8 else f'; +{len(unsupported) - 8} more'
        result['errors'].append(
            f"Unsupported visual SVG element(s) for native PPTX export: "
            f"{preview}{suffix}"
        )

    def _check_preset_geometry_metadata(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Validate round-trip preset metadata with the exporter's parser."""
        marked = [
            elem
            for elem in root.iter()
            if (
                elem.get('data-pptx-prst') is not None
                or elem.get('data-pptx-frame') is not None
                or elem.get('data-pptx-geometry-status') is not None
                or elem.get('data-pptx-geometry-reason') is not None
                or elem.get('data-pptx-geometry-kind') is not None
                or elem.get('data-pptx-custgeom') is not None
                or elem.get('data-pptx-preview-sha256') is not None
                or elem.get('data-pptx-shape-id') is not None
                or elem.get('data-pptx-shape-scope') is not None
                or elem.get('data-pptx-shape-style') is not None
                or elem.get(_AUTHORING_ATTR) is not None
                or any(attr.startswith('data-pptx-av-') for attr in elem.attrib)
            )
        ]
        if not marked:
            return
        if _validate_preset_geometry_metadata is None:
            result['errors'].append(
                'Unable to import PPTX preset metadata validator; '
                'cannot verify native shape restoration'
            )
            return

        issues = set()
        for elem in marked:
            tag = _local_name(elem)
            elem_id = elem.get('id')
            label = f'<{tag} id="{elem_id}">' if elem_id else f'<{tag}>'
            for error in _validate_preset_geometry_metadata(elem):
                issues.add(f'{label} has invalid PPTX shape metadata: {error}')
        if _validate_authored_preset_tree is None:
            if any(
                elem.get(_AUTHORING_ATTR) is not None
                for elem in root.iter()
            ):
                issues.add(
                    'Unable to import authored PPTX preset validator'
                )
        else:
            for error in _validate_authored_preset_tree(root):
                issues.add(f'Invalid authored PPTX preset: {error}')
        if (
            _svg_preset_preview_fingerprint is None
            or _resolve_preset_preview_hash is None
        ):
            issues.add('Unable to import PPTX preset preview fingerprint validator')
        else:
            for elem in root.iter():
                if (
                    _local_name(elem) != 'g'
                    or elem.get('data-pptx-object') not in {'shape', 'connector'}
                    or elem.get('data-pptx-prst') is None
                ):
                    continue
                try:
                    expected = _resolve_preset_preview_hash(elem)
                except ValueError as exc:
                    elem_id = elem.get('id') or '(no id)'
                    issues.add(
                        f'<g id="{elem_id}"> has an invalid PPTX preset '
                        f'preview contract: {exc}'
                    )
                    continue
                if expected is None:
                    continue
                actual = _svg_preset_preview_fingerprint(elem)
                if actual != expected:
                    elem_id = elem.get('id') or '(no id)'
                    issues.add(
                        f'<g id="{elem_id}"> has a stale PPTX preset preview; '
                        'update the native carrier or restore the generated detail paths'
                    )
        result['errors'].extend(sorted(issues))
        if (
            _authored_preset_encoding is not None
            and _validate_authored_preset_group is not None
        ):
            expanded = [
                elem.get('id') or '(no id)'
                for elem in root.iter()
                if _authored_preset_encoding(elem) == 'expanded'
                and not _validate_authored_preset_group(elem)
            ]
            if expanded:
                examples = ', '.join(expanded[:3])
                suffix = '' if len(expanded) <= 3 else f', +{len(expanded) - 3} more'
                result['warnings'].append(
                    'Compatible expanded authored-preset fragment(s) detected '
                    f'({len(expanded)}: {examples}{suffix}). New project-authored '
                    'pages and templates use the compact helper form; the '
                    'expanded carrier/preview form remains readable for compatibility. '
                    'No change is required while it remains ordinary Slide-local input.'
                )
        inherited_paint = _compact_preset_ancestor_paint(root)
        if inherited_paint:
            examples = ', '.join(
                f'{element_id} ({"/".join(properties)})'
                for element_id, properties in inherited_paint[:3]
            )
            suffix = (
                ''
                if len(inherited_paint) <= 3
                else f', +{len(inherited_paint) - 3} more'
            )
            result['warnings'].append(
                'Compact authored preset(s) use compatible ancestor paint or '
                f'opacity ({examples}{suffix}). Canonical page/template authoring '
                'keeps preset paint local and reruns the helper with channel alpha; '
                'export remains supported.'
            )

    def _check_preset_geometry_transforms(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Reject preset transforms that DrawingML cannot represent exactly."""
        helpers = (
            _IDENTITY_MATRIX,
            _matrix_multiply,
            _parse_transform_matrix,
            _rect_to_dml_xfrm,
            _validate_dml_shape_matrix,
        )
        if any(helper is None for helper in helpers):
            return

        relevant: set[ET.Element] = set()

        def mark_relevant(element: ET.Element) -> bool:
            found = element.get('data-pptx-prst') is not None
            for child in element:
                found = mark_relevant(child) or found
            if found:
                relevant.add(element)
            return found

        mark_relevant(root)
        issues = set()

        def visit(element: ET.Element, parent_matrix) -> None:
            if element not in relevant:
                return
            matrix = parent_matrix
            transform = element.get('transform')
            if transform:
                try:
                    local_matrix = _parse_transform_matrix(transform)
                    matrix = _matrix_multiply(parent_matrix, local_matrix)
                except ValueError as exc:
                    issues.add(
                        f'<{_local_name(element)}> has invalid preset '
                        f'transform: {exc}'
                    )
                    return
            if element.get('data-pptx-prst') is not None:
                try:
                    raw_frame = element.get('data-pptx-frame')
                    if raw_frame:
                        frame = tuple(
                            float(part)
                            for part in re.split(r'[\s,]+', raw_frame.strip())
                        )
                        if len(frame) != 4:
                            raise ValueError(
                                'data-pptx-frame must contain four numbers'
                            )
                        preset = element.get('data-pptx-prst') or ''
                        _rect_to_dml_xfrm(
                            frame[0],
                            frame[1],
                            frame[2],
                            frame[3],
                            matrix,
                            preserve_degenerate_axes=(
                                element.get('data-pptx-object') == 'connector'
                                or preset in _CONNECTOR_PRESET_TYPES
                            ),
                        )
                    else:
                        _validate_dml_shape_matrix(matrix)
                except ValueError as exc:
                    elem_id = element.get('id') or '(no id)'
                    issues.add(
                        f'<{_local_name(element)} id="{elem_id}"> has '
                        f'unsupported preset transform: {exc}'
                    )
            for child in element:
                visit(child, matrix)

        visit(root, _IDENTITY_MATRIX)
        result['errors'].extend(sorted(issues))

    @staticmethod
    def _is_full_canvas_root_rect(
        root: ET.Element,
        element: ET.Element,
    ) -> bool:
        """Return whether one direct rect is the ordinary full-page backdrop."""
        if (
            _local_name(element) != 'rect'
            or _parse_project_geometry_length is None
            or any(
                element.get(attribute)
                for attribute in ('transform', 'filter', 'clip-path')
            )
        ):
            return False
        viewbox = _parse_viewbox_values(root.get('viewBox') or '')
        if viewbox is None:
            return False

        parent_by_id = {id(element): root}

        def inherited(name: str, default: str) -> str:
            return _effective_presentation_value(
                element,
                name,
                parent_by_id,
            ) or default

        try:
            values = {
                name: _parse_project_geometry_length(
                    element.get(name) or '0',
                    name,
                )
                for name in ('x', 'y', 'width', 'height', 'rx', 'ry')
            }
            stroke_width = _parse_project_geometry_length(
                inherited('stroke-width', '1'),
                'stroke-width',
            )
            stroke_opacity = (
                _parse_project_opacity(inherited('stroke-opacity', '1'))
                if _parse_project_opacity is not None else 1.0
            )
        except ValueError:
            return False
        fill = inherited('fill', '#000000').strip().lower()
        stroke = inherited('stroke', 'none').strip().lower()
        if (
            fill == 'none'
            or (
                stroke != 'none'
                and stroke_width > 0
                and stroke_opacity > 0
            )
        ):
            return False

        view_x, view_y, view_width, view_height = viewbox
        tolerance = 0.5
        return (
            values['rx'] == 0
            and values['ry'] == 0
            and abs(values['x'] - view_x) <= tolerance
            and abs(values['y'] - view_y) <= tolerance
            and abs(values['width'] - view_width) <= tolerance
            and abs(values['height'] - view_height) <= tolerance
        )

    def _check_animation_group_ids(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ):
        """Validate top-level animation anchors without policing inner groups."""
        non_visual = {'defs', 'title', 'desc', 'metadata', 'style'}
        group_indexes: Dict[str, List[int]] = defaultdict(list)
        ungrouped: List[str] = []
        ungrouped_signatures: List[Tuple[object, ...]] = []
        visual_index = 0

        for child in root:
            tag = _local_name(child)
            if tag in non_visual:
                continue
            visual_index += 1
            is_first_visual = visual_index == 1

            if tag == 'g':
                group_id = _usable_animation_group_id(child.get('id'))
                if group_id is None:
                    result['warnings'].append(
                        f"Top-level visible <g> #{visual_index} has no id; "
                        "object-level animation config cannot reference it"
                    )
                    continue
                group_indexes[group_id].append(visual_index)
                continue

            if svg_path.parent.name != 'svg_output':
                continue
            if child.get('data-pptx-layer') is not None:
                continue
            if (
                _is_static_page_frame is not None
                and _is_static_page_frame(
                    child.get('data-pptx-role'),
                    child.get('data-pptx-placeholder'),
                )
            ):
                continue
            if is_first_visual and self._is_full_canvas_root_rect(root, child):
                continue
            child_id = (child.get('id') or '').strip()
            ungrouped.append(
                f'<{tag} id="{child_id}">'
                if child_id else f'<{tag}> #{visual_index}'
            )
            ungrouped_signatures.append(
                self._prototype_element_signature(child)
            )

        for group_id, indexes in sorted(group_indexes.items()):
            if len(indexes) > 1:
                positions = ', '.join(str(item) for item in indexes)
                result['errors'].append(
                    f'Duplicate top-level group id {group_id!r} at visible '
                    f'positions {positions}; animation target ids must be unique'
                )

        if ungrouped:
            samples = ', '.join(ungrouped[:3])
            if len(ungrouped) > 3:
                samples += ', ...'
            message = (
                f'{len(ungrouped)} ungrouped top-level Slide-local element(s) '
                f'in svg_output ({samples}); group only logical content units '
                'in a top-level <g id="...">. Keep genuine static page framing '
                'as a root primitive and declare a supported data-pptx-role such '
                'as "background" or "decoration"'
            )
            prototype_root = self._active_prototype_root()
            prototype_ungrouped = (
                self._ungrouped_slide_local_facts(prototype_root)
                if prototype_root is not None
                else ([], [])
            )
            if (
                prototype_root is not None
                and ungrouped == prototype_ungrouped[0]
                and ungrouped_signatures == prototype_ungrouped[1]
            ):
                self._append_inherited_info(
                    result,
                    'animation_anchor',
                    message,
                )
            else:
                result['warnings'].append(message)

    @staticmethod
    def _prototype_element_signature(
        element: ET.Element,
    ) -> Tuple[object, ...]:
        """Compare warning-owned topology/style while ignoring visible text."""
        return (
            _local_name(element),
            tuple(sorted(element.attrib.items())),
            tuple(
                SVGQualityChecker._prototype_element_signature(child)
                for child in element
            ),
        )

    def _ungrouped_slide_local_facts(
        self,
        root: ET.Element,
    ) -> Tuple[List[str], List[Tuple[object, ...]]]:
        """Describe and fingerprint top-level non-group Slide-local atoms."""
        non_visual = {'defs', 'title', 'desc', 'metadata', 'style'}
        descriptors: List[str] = []
        signatures: List[Tuple[object, ...]] = []
        visual_index = 0
        for child in root:
            tag = _local_name(child)
            if tag in non_visual:
                continue
            visual_index += 1
            if tag == 'g' or child.get('data-pptx-layer') is not None:
                continue
            if (
                _is_static_page_frame is not None
                and _is_static_page_frame(
                    child.get('data-pptx-role'),
                    child.get('data-pptx-placeholder'),
                )
            ):
                continue
            if visual_index == 1 and self._is_full_canvas_root_rect(root, child):
                continue
            child_id = (child.get('id') or '').strip()
            descriptors.append(
                f'<{tag} id="{child_id}">'
                if child_id else f'<{tag}> #{visual_index}'
            )
            signatures.append(self._prototype_element_signature(child))
        return descriptors, signatures

    # OOXML ST_PresetPatternVal enum — anything outside this set produces a
    # PPTX schema violation ("PowerPoint found a problem with the content").
    _OOXML_PATTERN_PRESETS = frozenset({
        'pct5', 'pct10', 'pct20', 'pct25', 'pct30', 'pct40', 'pct50', 'pct60',
        'pct70', 'pct75', 'pct80', 'pct90',
        'horz', 'vert', 'ltHorz', 'ltVert', 'dkHorz', 'dkVert',
        'narHorz', 'narVert', 'dashHorz', 'dashVert',
        'cross', 'dnDiag', 'upDiag', 'ltDnDiag', 'ltUpDiag', 'dkDnDiag',
        'dkUpDiag', 'wdDnDiag', 'wdUpDiag',
        'dashDnDiag', 'dashUpDiag', 'diagCross',
        'smCheck', 'lgCheck', 'smGrid', 'lgGrid', 'dotGrid', 'smConfetti',
        'lgConfetti', 'horzBrick', 'diagBrick', 'solidDmnd', 'openDmnd',
        'dotDmnd', 'plaid', 'sphere', 'weave', 'wave', 'trellis', 'zigZag',
        'divot', 'shingle',
    })

    def _check_pattern_fills(self, root: ET.Element, result: Dict):
        """Audit <pattern> defs that drive PPTX <a:pattFill> output.

        svg_to_pptx maps <pattern fill> to native <a:pattFill prst="...">. The
        preset name comes from `data-pptx-pattern` (e.g. `lgGrid` / `smGrid` /
        `dkUpDiag`). Patterns marked with `data-pptx-text-image-fill` instead
        map to run-level <a:blipFill> and are validated by converter preflight.
        Two preset-pattern failure modes are worth catching pre-export:

        1. Missing annotation → the converter compatibility fallback chooses
           `ltUpDiag` (diagonal stripes), which is not an authoring contract.
        2. Invalid preset name → PPTX schema rejects the file; PowerPoint
           opens it with "needs to be repaired". OOXML
           `ST_PresetPatternVal` is a closed enum — only the names in
           `_OOXML_PATTERN_PRESETS` are legal. Inventing `ltGrid` (no such
           value) is the canonical mistake; the only grids are `smGrid` /
           `lgGrid` / `dotGrid`.
        """
        definitions, _duplicates = _direct_defs_index(root)
        referenced_patterns: set[str] = set()
        for elem in root.iter():
            style_values = (
                _parse_inline_style(elem.get('style'))
                if _parse_inline_style is not None else {}
            )
            fill = style_values.get('fill') or elem.get('fill')
            match = re.fullmatch(r'url\(#([^)]+)\)', (fill or '').strip())
            if match is None:
                continue
            definition = definitions.get(match.group(1))
            if definition is not None and _local_name(definition) == 'pattern':
                referenced_patterns.add(match.group(1))

        for pattern in (
            elem for elem in root.iter()
            if _local_name(elem) == 'pattern'
        ):
            pat_id = pattern.get('id', '<unnamed>')
            prst = pattern.get('data-pptx-pattern')
            if pattern.get(_TEXT_IMAGE_FILL_ATTR) is not None:
                continue
            if pat_id in referenced_patterns and not prst:
                result['warnings'].append(
                    f"Fidelity warning: <pattern id=\"{pat_id}\"> has no "
                    "data-pptx-pattern attribute, so the converter will use its "
                    "compatible `ltUpDiag` fallback. Generated SVG should declare a valid "
                    "data-pptx-pattern to make the intended preset explicit; "
                    "set data-pptx-fg/data-pptx-bg or matching child paints "
                    "when explicit pattern colors are required. No change is "
                    "required for export."
                )
            if pat_id in referenced_patterns and pattern.get('patternTransform'):
                result['errors'].append(
                    f"<pattern id=\"{pat_id}\"> cannot use patternTransform; "
                    "the native preset mapping does not preserve custom tile transforms"
                )
            if prst not in self._OOXML_PATTERN_PRESETS:
                if not prst:
                    continue
                result['errors'].append(
                    f"<pattern id=\"{pat_id}\"> uses data-pptx-pattern=\"{prst}\" "
                    "which is not in OOXML ST_PresetPatternVal — exported PPTX "
                    "will fail schema validation ('needs to be repaired'). "
                    "Use one of: smGrid / lgGrid / dotGrid (grids), "
                    "ltUpDiag / dkUpDiag / cross / diagCross / weave / plaid / "
                    "horzBrick (others); see references/native-data-interface.md §1 "
                    "for the full authoring enum."
                )

    def _check_native_object_markers(self, root: ET.Element, result: Dict) -> None:
        """Validate explicit native replacement markers before PPTX export."""
        inline_formula_markers = [
            elem for elem in root.iter()
            if elem.get(_INLINE_FORMULA_ATTR) is not None
        ]
        if inline_formula_markers and _inline_formula_marker_errors is None:
            result['errors'].append(
                "Unable to import inline-formula validator; cannot verify "
                f"{_INLINE_FORMULA_ATTR} markers"
            )
        elif _inline_formula_marker_errors is not None:
            for error in _inline_formula_marker_errors(root):
                result['errors'].append(f"Invalid inline formula marker: {error}")

        invalid_status_elements: set[ET.Element] = set()
        for elem in root.iter():
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            if elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            has_status = any(
                elem.get(name) is not None
                for name in (
                    'data-pptx-replace-with',
                    'data-pptx-native',
                    'data-pptx-fallback-kind',
                    'data-pptx-visual-status',
                    'data-pptx-route-status',
                    'data-pptx-replacement-status',
                    'data-pptx-native-status',
                    'data-pptx-import-source',
                    'data-pptx-native-source',
                )
            )
            if not has_status:
                continue
            if (
                _native_marker_status_errors is None
                or _native_marker_release_block_reason is None
            ):
                result['errors'].append(
                    "Unable to import native-object status validator; "
                    f"cannot verify PPTX graphic {marker_id}"
                )
                continue
            status_errors = _native_marker_status_errors(elem)
            for error in status_errors:
                result['errors'].append(
                    f"PPTX graphic {marker_id} has invalid status metadata: {error}"
                )
            if status_errors:
                invalid_status_elements.add(elem)
                continue
            if _native_marker_legacy_warnings is not None:
                for warning in _native_marker_legacy_warnings(elem):
                    result['warnings'].append(
                        f"PPTX replacement marker {marker_id}: {warning}"
                    )
            try:
                fallback_kind = (
                    _native_fallback_kind(elem)
                    if _native_fallback_kind is not None else None
                )
                replacement_kind = (
                    _native_replacement_kind(elem)
                    if _native_replacement_kind is not None else ''
                )
            except ValueError:
                # The shared status validator reported the alias conflict.
                continue
            if fallback_kind == 'placeholder':
                route = (
                    "the native Chart/Table route may reconstruct its active marker"
                    if replacement_kind
                    else "default export keeps the visible placeholder"
                )
                result['warnings'].append(
                    f"PPTX graphic {marker_id} is a reconstruction-only placeholder; "
                    f"it has no baked preview and {route}"
                )

        for elem in root.iter():
            if elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            if _native_replacement_status is None or _native_replacement_kind is None:
                continue
            try:
                status = _native_replacement_status(elem)
                replacement_kind = _native_replacement_kind(elem)
            except ValueError:
                continue
            if not status or replacement_kind:
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            result['warnings'].append(
                f"Native PPTX object {marker_id} is fallback-only: {status}"
            )

        markers = [
            elem for elem in root.iter()
            if (
                _native_replacement_kind is not None
                and elem.tag.rsplit('}', 1)[-1] != 'metadata'
                and elem not in invalid_status_elements
                and _native_replacement_kind(elem)
            )
        ]
        if not markers:
            return
        if _validate_native_object_marker is None:
            result['warnings'].append(
                "Detected data-pptx-replace-with markers, but replacement validator "
                "could not be imported; export-time validation will still run."
            )
            return

        parent_map = {
            child: parent
            for parent in root.iter()
            for child in parent
        }

        def append_metadata_legacy_warnings(marker: ET.Element) -> None:
            if _native_marker_legacy_warnings is None:
                return
            marker_id = marker.get('id') or '<unnamed>'
            for child in marker:
                if child.tag.rsplit('}', 1)[-1] != 'metadata':
                    continue
                for warning in _native_marker_legacy_warnings(child):
                    result['warnings'].append(
                        f"PPTX replacement marker {marker_id}: {warning}"
                    )

        for marker in markers:
            marker_id = marker.get('id') or '<unnamed>'
            ancestors = []
            parent = parent_map.get(marker)
            while parent is not None and parent is not root:
                if parent.tag.rsplit('}', 1)[-1] == 'g':
                    ancestors.append(parent)
                parent = parent_map.get(parent)
            ancestors_tuple = tuple(reversed(ancestors))
            if _validate_native_object_marker_with_warnings is not None:
                try:
                    warnings = _validate_native_object_marker_with_warnings(
                        marker,
                        ancestors=ancestors_tuple,
                        document_root=root,
                    )
                except RuntimeError as exc:
                    result['errors'].append(
                        f"Invalid data-pptx-replace-with marker {marker_id}: {exc}"
                    )
                    continue
                for warning in warnings:
                    result['warnings'].append(
                        f"data-pptx-replace-with marker {marker_id}: {warning}"
                    )
                append_metadata_legacy_warnings(marker)
                continue

            try:
                _validate_native_object_marker(marker, ancestors=ancestors_tuple)
            except RuntimeError as exc:
                result['errors'].append(
                    f"Invalid data-pptx-replace-with marker {marker_id}: {exc}"
                )
                continue
            append_metadata_legacy_warnings(marker)
            if _native_object_marker_warnings is None:
                continue
            for warning in _native_object_marker_warnings(
                marker,
                ancestors=ancestors_tuple,
                document_root=root,
            ):
                result['warnings'].append(
                    f"data-pptx-replace-with marker {marker_id}: {warning}"
                )

    def _check_pptx_structure_metadata(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ) -> None:
        """Validate the intrinsic structured Master/Layout SVG contract."""
        if self.quick_generate:
            forbidden_attrs = sorted({
                attr
                for elem in root.iter()
                for attr in _PPTX_STRUCTURE_ATTRS
                if elem.get(attr) is not None
            })
            if forbidden_attrs:
                result['errors'].append(
                    f"{svg_path.name}: Quick Generate uses flat export and "
                    "forbids Master/Layout/layer/placeholder metadata; remove "
                    + ', '.join(forbidden_attrs)
                )
            return
        if not self.template_mode and svg_path.parent.name == 'svg_output':
            declared_mode = _declared_pptx_structure_mode(
                self._resolve_project_path(svg_path)
            )
            if declared_mode == 'flat':
                forbidden_attrs = sorted({
                    attr
                    for elem in root.iter()
                    for attr in _PPTX_STRUCTURE_ATTRS
                    if elem.get(attr) is not None
                })
                if forbidden_attrs:
                    result['errors'].append(
                        f"{svg_path.name}: pptx_structure.mode: flat forbids "
                        "Master/Layout/layer/placeholder metadata; remove "
                        + ', '.join(forbidden_attrs)
                    )
                return
            if declared_mode != 'structured':
                # The project-level gate emits one actionable migration error.
                # Avoid burying it under repeated per-page structure failures.
                return
        has_structure_metadata = any(
            elem.get(attr) is not None
            for elem in root.iter()
            for attr in _PPTX_STRUCTURE_ATTRS
        )
        require_structure = bool(
            self.template_mode
            or svg_path.parent.name == 'svg_output'
        )
        if not has_structure_metadata and not require_structure:
            return
        result['errors'].extend(_local_pptx_structure_errors(
            root,
            svg_path,
            require_structure=require_structure,
        ))
        self._check_placeholder_carrier_flattening(root, svg_path, result)
        if svg_path.parent.name == 'svg_output':
            self._append_structure_coverage_warnings(root, result)
        if _validate_template_structure_svg is None:
            result['errors'].append(
                "Structured PPTX metadata validator could not be imported; "
                "the quality gate cannot verify this SVG"
            )
            return
        result['errors'].extend(_validate_template_structure_svg(svg_path))
        result['errors'] = list(dict.fromkeys(result['errors']))

    @staticmethod
    def _check_placeholder_carrier_flattening(
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ) -> None:
        """Reject slot carriers that export as multiple native children.

        Default export flattens non-mergeable positional ``<tspan>`` lines
        before converting the surrounding slot group to DrawingML. Reuse that
        exact transform here so the quality gate fails before the later
        placeholder-unwrapping step does.
        """
        if _flatten_positional_tspans is None:
            return

        candidate_ids: List[str] = []
        for slot in root.iter(f'{{{SVG_NS}}}g'):
            if not (slot.get('data-pptx-placeholder') or '').strip():
                continue
            binding = (
                slot.get('data-pptx-binding') or 'carrier'
            ).strip().lower()
            if binding != 'carrier':
                continue
            visual_children = [
                child for child in list(slot)
                if _local_name(child) not in _NON_VISUAL_SVG_TAGS
            ]
            carriers = [
                child for child in visual_children
                if (child.get('data-pptx-carrier') or '')
                .strip()
                .lower()
                == 'true'
            ]
            slot_id = (slot.get('id') or '').strip()
            if not slot_id or len(visual_children) != 1 or len(carriers) != 1:
                continue
            if not any(
                _local_name(descendant) == 'tspan'
                and any(
                    descendant.get(name) is not None
                    for name in ('x', 'y', 'dy')
                )
                for descendant in carriers[0].iter()
            ):
                continue
            candidate_ids.append(slot_id)

        if not candidate_ids:
            return

        flattened_root = copy.deepcopy(root)
        try:
            _flatten_positional_tspans(
                ET.ElementTree(flattened_root),
                merge_paragraphs=True,
                preserve_line_breaks=True,
            )
        except ValueError:
            # The shared text check reports the unsupported nested-position
            # contract; avoid turning a quality result into a checker crash.
            return
        slots_by_id = {
            (slot.get('id') or '').strip(): slot
            for slot in flattened_root.iter(f'{{{SVG_NS}}}g')
            if (slot.get('id') or '').strip()
        }
        for slot_id in candidate_ids:
            slot = slots_by_id.get(slot_id)
            if slot is None:
                continue
            native_children = [
                child for child in list(slot)
                if _local_name(child) not in _NON_VISUAL_SVG_TAGS
            ]
            if len(native_children) == 1:
                continue
            result['errors'].append(
                f"{svg_path.name}: placeholder slot {slot_id} becomes "
                f"{len(native_children)} native children after positional "
                "<tspan> flattening; a carrier-bound slot must export as one "
                "text or picture carrier. Use one single-frame dy-stacked text "
                "frame, or move independently positioned lines outside the slot"
            )

    def _append_structure_coverage_warnings(
        self,
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Warn on mapped pages that compile to bare Masters / empty Layouts.

        Zero-slot and framing-only Layouts are legal contracts, so these stay
        advisory warnings. They neither fail the workflow gate nor require a
        per-warning disposition.
        """
        messages = self._structure_coverage_messages(root)
        if not messages:
            return
        prototype_root = self._active_prototype_root()
        if (
            prototype_root is not None
            and messages == self._structure_coverage_messages(prototype_root)
        ):
            for message in messages:
                self._append_inherited_info(
                    result,
                    'structure_coverage',
                    message,
                )
            return
        result['warnings'].extend(messages)

    @staticmethod
    def _structure_coverage_messages(root: ET.Element) -> List[str]:
        """Return advisory coverage messages for one structured page."""
        if not (root.get('data-pptx-layout') or '').strip():
            return []
        messages: List[str] = []
        has_layer_mark = any(
            elem.get('data-pptx-layer') is not None
            for elem in root.iter()
        )
        has_layout_atom = any(
            child.get('data-pptx-layer') == 'layout'
            for child in list(root)
        )
        has_placeholder = any(
            elem.get('data-pptx-placeholder') is not None
            for elem in root.iter()
        )
        if not has_layer_mark:
            messages.append(
                'Mapped page declares data-pptx-layout but no data-pptx-layer '
                'mark; the exported Master gets no shared background/chrome '
                'and the Layout gets no static framing. Generated templates '
                'should mark the deck-wide '
                'background data-pptx-layer="master" and this layout key\'s '
                'framing data-pptx-layer="layout". No change or disposition '
                'is required.'
            )
        if not has_placeholder and not has_layout_atom:
            messages.append(
                'Mapped page has no placeholder slot and no '
                'data-pptx-layer="layout" atom; its Layout exports empty. '
                'Generated templates should declare the slots the page actually '
                'has (title / subtitle / '
                'body / picture / slide-number / footer) and mark the layout '
                'key\'s static framing unless this is intentionally a fixed '
                'zero-slot composition. No change or disposition is required.'
            )
        elif not has_placeholder:
            messages.append(
                'Mapped Layout has static framing but no insertable '
                'placeholder slot. Generated templates should declare the '
                'slots the page actually has (title / subtitle / body / '
                'picture / slide-number / footer) unless zero-slot is the '
                'intended reusable contract. No change or disposition is required.'
            )
        return messages

    @staticmethod
    def _check_legacy_pptx_attributes(
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ) -> None:
        """Reject superseded long-form authoring attributes."""
        for element in root.iter():
            for legacy, canonical in _LEGACY_PPTX_ATTRIBUTE_RENAMES.items():
                if element.get(legacy) is None:
                    continue
                result['errors'].append(
                    f'{svg_path.name}: {_element_label(element)} uses legacy '
                    f'{legacy}; rename it to {canonical}'
                )

    def _check_semantic_markers(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ) -> None:
        """Validate minimal compiler hints without changing SVG rendering."""
        has_semantics = any(
            elem.get(attr) is not None
            for elem in root.iter()
            for attr in _SEMANTIC_ATTRS
        )
        require_page_role = (
            svg_path.parent.name in {'svg_output', 'svg_final'}
            and root.get('data-pptx-layout') is None
        )
        if _validate_semantic_markers is None:
            if has_semantics:
                result['warnings'].append(
                    "Detected Semantic SVG markers, but their validator could "
                    "not be imported."
                )
            return
        for issue in _validate_semantic_markers(
            root,
            require_page_role=require_page_role,
        ):
            if issue.severity == 'error':
                result['errors'].append(issue.message)
            else:
                result['warnings'].append(issue.message)

    def _get_spec_lock(self, svg_path: Path):
        """Locate and parse spec_lock.md near the SVG. Returns dict or None.

        Looks in svg_path.parent and svg_path.parent.parent (covers the two
        common layouts: SVG directly under <project>/ or under
        <project>/svg_output/). Results are cached per lock path.
        """
        if self.quick_generate:
            return None
        if _parse_spec_lock is None:
            return None
        for candidate in (svg_path.parent / 'spec_lock.md',
                          svg_path.parent.parent / 'spec_lock.md'):
            if candidate in self._lock_cache:
                return self._lock_cache[candidate]
            if candidate.exists():
                try:
                    data = _parse_spec_lock(candidate)
                except Exception:
                    data = None
                self._lock_cache[candidate] = data
                if data is not None:
                    self._lock_seen = True
                return data
        return None

    def _prototype_drift_allowances(
        self,
    ) -> Tuple[set[str], set[str], set[str]]:
        """Return color/font/size values owned by the selected mirror page."""
        prototype_root = self._active_prototype_root()
        if prototype_root is None:
            return set(), set(), set()
        try:
            content = self._active_prototype_path.read_text(encoding='utf-8')
        except (AttributeError, OSError):
            return set(), set(), set()

        colors: set[str] = set()
        for attribute in _PAINT_PROPERTIES or ():
            for raw_value in self._svg_property_values(content, attribute):
                normalized = raw_value.strip()
                if normalized.lower() in {'none', 'transparent'} or re.fullmatch(
                    r'url\(#[^)]+\)', normalized
                ):
                    continue
                if _parse_export_color is not None:
                    color, _alpha = _parse_export_color(normalized)
                else:
                    color = _normalize_hex_rgb(normalized)
                if color:
                    colors.add(color)
        fonts = {
            self._normalize_font_stack(value)
            for value in self._font_family_values(content)
            if self._normalize_font_stack(value)
        }
        sizes = set(self._effective_text_size_counts(prototype_root))
        return colors, fonts, sizes

    def _declared_typography_size_anchors(
        self,
        lock: Dict,
    ) -> Tuple[Dict, set[str], List[float], List[str]]:
        """Return valid declared size anchors and malformed lock rows."""
        typography = lock.get('typography', {})
        positive_numeric_re = re.compile(
            r'^(?=.*[1-9])(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$'
        )
        locked_sizes: set[str] = set()
        anchor_sizes: List[float] = []
        invalid_sizes: List[str] = []
        for key, raw_value in typography.items():
            if key == 'font_family' or key.endswith('_family'):
                continue
            value = raw_value.strip()
            if positive_numeric_re.fullmatch(value) is None:
                invalid_sizes.append(f"{key}: {raw_value}")
                continue
            try:
                anchor = float(value)
            except (TypeError, ValueError):
                invalid_sizes.append(f"{key}: {raw_value}")
                continue
            if not math.isfinite(anchor) or anchor <= 0:
                invalid_sizes.append(f"{key}: {raw_value}")
                continue
            locked_sizes.add(self._canonical_font_size_key(anchor))
            anchor_sizes.append(anchor)
        return typography, locked_sizes, anchor_sizes, invalid_sizes

    def _count_undeclared_size_occurrences(
        self,
        root: ET.Element,
        *,
        locked_sizes: set[str],
        anchor_sizes: List[float],
        prototype_sizes: set[str],
    ) -> Counter[str]:
        """Count text objects using valid sizes outside all declared bands."""
        counts: Counter[str] = Counter()
        if not locked_sizes:
            return counts
        for value, occurrence_count in self._effective_text_size_counts(root).items():
            if value in prototype_sizes and value not in locked_sizes:
                continue
            if value in locked_sizes:
                continue
            try:
                used_px = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(used_px) or used_px < 0:
                continue
            if any(
                abs(used_px - anchor_px) <= FONT_SIZE_ANCHOR_TOLERANCE_PX
                for anchor_px in anchor_sizes
            ):
                continue
            counts[value] += occurrence_count
        return counts

    def _effective_text_size_counts(self, root: ET.Element) -> Counter[str]:
        """Count each effective size once per non-empty SVG text object."""
        counts: Counter[str] = Counter()
        if _resolve_project_font_sizes is None:
            return counts
        working_root = root
        if (
            _expand_local_use_references is not None
            and _UseExpansionError is not None
        ):
            expanded_root = copy.deepcopy(root)
            try:
                _expand_local_use_references(expanded_root)
            except _UseExpansionError:
                pass
            else:
                working_root = expanded_root
        try:
            effective_sizes = _resolve_project_font_sizes(working_root)
        except ValueError:
            return counts

        def collect_text_object_sizes(element: ET.Element) -> set[str]:
            values: set[str] = set()

            def visit(node: ET.Element) -> None:
                if (node.text or '').strip():
                    values.add(
                        self._canonical_font_size_key(effective_sizes[id(node)])
                    )
                for child in node:
                    visit(child)
                    if (child.tail or '').strip():
                        values.add(
                            self._canonical_font_size_key(
                                effective_sizes[id(node)]
                            )
                        )

            visit(element)
            return values

        definition_containers = {
            'clippath',
            'defs',
            'marker',
            'mask',
            'pattern',
            'symbol',
        }

        def visit_visible(element: ET.Element) -> None:
            local_name = _local_name(element).casefold()
            if local_name in definition_containers:
                return
            if local_name == 'text':
                counts.update(collect_text_object_sizes(element))
                return
            for child in element:
                visit_visible(child)

        visit_visible(working_root)
        return counts

    @staticmethod
    def _canonical_font_size_key(value: float) -> str:
        """Canonicalize equivalent numeric spellings for deck-wide counting."""
        return format(value, '.12g')

    def _prepare_undeclared_size_occurrences(
        self,
        svg_files: List[Path],
    ) -> None:
        """Pre-count sparse undeclared sizes before per-file diagnostics."""
        previous_prototype = self._active_prototype_path
        try:
            for svg_path in svg_files:
                lock = self._get_spec_lock(svg_path)
                if lock is None:
                    continue
                _typography, locked_sizes, anchor_sizes, _invalid = (
                    self._declared_typography_size_anchors(lock)
                )
                self._active_prototype_path = self._prototype_by_output.get(
                    svg_path.resolve()
                )
                _colors, _fonts, prototype_sizes = (
                    self._prototype_drift_allowances()
                )
                try:
                    content = svg_path.read_text(encoding='utf-8')
                except OSError:
                    continue
                try:
                    root = ET.fromstring(content)
                except ET.ParseError:
                    continue
                self._undeclared_size_occurrences.update(
                    self._count_undeclared_size_occurrences(
                        root,
                        locked_sizes=locked_sizes,
                        anchor_sizes=anchor_sizes,
                        prototype_sizes=prototype_sizes,
                    )
                )
        finally:
            self._active_prototype_path = previous_prototype
            self._undeclared_size_counts_ready = True

    def _check_spec_lock_alignment(
        self,
        content: str,
        svg_path: Path,
        result: Dict,
        *,
        root: ET.Element,
    ):
        """Compare SVG values with reusable anchors in spec_lock.md.

        Covers colors (fill / stroke / stop-color / flood-color / pattern
        metadata), font-family, and font-size.
        Additional colors and font families are valid contextual authoring and
        are recorded as information. A valid undeclared display size may occur
        at most twice across generated pages; its third occurrence makes it a
        recurring role and blocks ``svg_output`` until the role is declared.
        Structural text still maps to declared role bands. Exact mirror-
        prototype values remain inherited information. Exact values are
        accumulated in self._anchor_value_summary for end-of-run aggregation.
        When spec_lock.md is missing, silently skip this local comparison; the
        Generate route's required-artifact gate owns whether execution may begin.
        """
        lock = self._get_spec_lock(svg_path)
        if lock is None:
            return
        prototype_colors, prototype_fonts, prototype_sizes = (
            self._prototype_drift_allowances()
        )

        # Build allow-sets from the lock
        allowed_colors = set()
        for v in lock.get('colors', {}).values():
            if _parse_export_color is not None:
                color, _alpha = _parse_export_color(v)
                if color:
                    allowed_colors.add(color)
            else:
                color = _normalize_hex_rgb(v)
                if color:
                    allowed_colors.add(color)

        # A validated compact preset may contain registry-derived darken/lighten
        # layer colors.  Their base paint still comes from spec_lock; the exact
        # child HEX values are deterministic compiler evidence, not color drift.
        if (
            _authored_preset_encoding is not None
            and _validate_authored_preset_group is not None
        ):
            for group in root.iter():
                if (
                    _authored_preset_encoding(group) != 'compact'
                    or _validate_authored_preset_group(group)
                ):
                    continue
                for child in group:
                    for attribute in ('fill', 'stroke'):
                        raw_value = child.get(attribute)
                        if raw_value is None:
                            continue
                        if _parse_export_color is not None:
                            color, _alpha = _parse_export_color(raw_value)
                        else:
                            color = _normalize_hex_rgb(raw_value)
                        if color:
                            allowed_colors.add(color)
        locked_colors = set(allowed_colors)
        allowed_colors.update(prototype_colors)

        typo, locked_sizes, anchor_sizes, invalid_lock_sizes = (
            self._declared_typography_size_anchors(lock)
        )
        if invalid_lock_sizes:
            shown = ', '.join(invalid_lock_sizes[:5])
            more = len(invalid_lock_sizes) - 5
            suffix = f" (+{more} more)" if more > 0 else ""
            result['errors'].append(
                f"spec_lock typography sizes must be positive finite unitless px values; "
                f"found {shown}{suffix}."
            )

        # Font families: default `font_family` plus any per-role `*_family`
        # override (title_family / body_family / emphasis_family / code_family,
        # per templates/schemas/spec_lock.schema.json). Any of these is a legitimate declared
        # value; an SVG that uses any one of them is not drifting.
        allowed_fonts = set()
        if typo:
            default_font = typo.get('font_family', '').strip()
            if default_font:
                allowed_fonts.add(self._normalize_font_stack(default_font))
            for k, v in typo.items():
                if k == 'font_family' or not k.endswith('_family'):
                    continue
                v_clean = v.strip()
                # Skip placeholder text like "same as body (omit if identical)"
                if not v_clean or v_clean.lower().startswith('same as'):
                    continue
                allowed_fonts.add(self._normalize_font_stack(v_clean))
        locked_fonts = set(allowed_fonts)
        allowed_fonts.update(prototype_fonts)

        # Sizes: declared slots are anchors. Checker cannot infer which role a
        # text node carries, so it uses the union of their ±2px bands as a cheap
        # numeric safety net; prompt rules own semantic role mapping.
        # Scan SVG for used values
        color_drifts = set()
        inherited_colors = set()
        for attr in _PAINT_PROPERTIES or ():
            for raw_value in self._svg_property_values(content, attr):
                normalized = raw_value.strip()
                if normalized.lower() in {'none', 'transparent'} or re.fullmatch(
                    r'url\(#[^)]+\)', normalized
                ):
                    continue
                if _BARE_HEX_VALUE_RE.fullmatch(normalized):
                    continue
                if _parse_export_color is not None:
                    val, _alpha = _parse_export_color(normalized)
                    if val is None:
                        continue
                else:
                    val = _normalize_hex_rgb(normalized)
                    if val is None:
                        continue
                if val not in allowed_colors:
                    color_drifts.add(f'#{val}')
                elif val in prototype_colors and val not in locked_colors:
                    inherited_colors.add(f'#{val}')

        font_drifts = set()
        inherited_fonts = set()
        for val in self._font_family_values(content):
            normalized_font = self._normalize_font_stack(val)
            if allowed_fonts and normalized_font not in allowed_fonts:
                font_drifts.add(val)
            elif (
                normalized_font in prototype_fonts
                and normalized_font not in locked_fonts
            ):
                inherited_fonts.add(val)

        size_drift_counts = self._count_undeclared_size_occurrences(
            root,
            locked_sizes=locked_sizes,
            anchor_sizes=anchor_sizes,
            prototype_sizes=prototype_sizes,
        )
        size_drifts = set(size_drift_counts)
        inherited_sizes = set()
        for val in self._effective_text_size_counts(root):
            if val in prototype_sizes and val not in locked_sizes:
                inherited_sizes.add(val)

        # Record in run-wide aggregation. Colors/fonts beyond the anchor set are
        # contextual values, not release issues. Generated-page sizes enforce
        # role-anchor ownership; other spec-backed locations retain review.
        fname = svg_path.name
        for v in color_drifts:
            self._anchor_value_summary['colors'][v].add(fname)
        for v in font_drifts:
            self._anchor_value_summary['fonts'][v].add(fname)
        for v in size_drifts:
            self._anchor_value_summary['sizes'][v].add(fname)

        contextual_values = {}
        if color_drifts:
            contextual_values['colors'] = sorted(color_drifts)
        if font_drifts:
            contextual_values['font_families'] = sorted(font_drifts)
        if contextual_values:
            result['info']['contextual_values'] = contextual_values

        sparse_sizes = {}
        recurring_sizes = {}
        for value, local_count in size_drift_counts.items():
            total_count = (
                self._undeclared_size_occurrences.get(value, local_count)
                if self._undeclared_size_counts_ready
                else local_count
            )
            target = (
                sparse_sizes
                if total_count <= SPARSE_UNDECLARED_FONT_SIZE_MAX_OCCURRENCES
                else recurring_sizes
            )
            target[value] = total_count

        if sparse_sizes:
            result['info']['sparse_typography_sizes'] = {
                value: count for value, count in sorted(sparse_sizes.items())
            }

        if recurring_sizes:
            shown = ', '.join(
                f"{value} ({count} occurrences)"
                for value, count in sorted(recurring_sizes.items())
            )
            size_issue = (
                f"undeclared font-size {shown} exceeds the sparse-display limit "
                f"of {SPARSE_UNDECLARED_FONT_SIZE_MAX_OCCURRENCES} occurrences"
            )
            if svg_path.parent.name == 'svg_output':
                result['errors'].append(
                    "spec_lock typography-size recurrence: "
                    f"{size_issue}. Structural text must return to its declared "
                    "role band; a genuinely recurring display treatment needs a "
                    "justified named role in the Design Spec and spec_lock."
                )
            else:
                result['warnings'].append(
                    f"spec_lock typography-size recurrence review: {size_issue}"
                )
        inherited_parts = []
        if inherited_colors:
            inherited_parts.append(f"{len(inherited_colors)} color(s)")
        if inherited_fonts:
            inherited_parts.append(f"{len(inherited_fonts)} font-family value(s)")
        if inherited_sizes:
            inherited_parts.append(f"{len(inherited_sizes)} font-size value(s)")
        if inherited_parts:
            self._append_inherited_info(
                result,
                'spec_lock_alignment',
                f"{', '.join(inherited_parts)} come unchanged from mirror "
                "prototype and are accepted without expanding spec_lock.md",
            )

    def _find_image_sources_manifest(self, svg_path: Path) -> Path | None:
        """Locate image_sources.json for a project SVG.

        Quality checks run primarily on <project>/svg_output/*.svg, but this
        also supports SVGs checked from project root or svg_final.
        """
        bases = (svg_path.parent, svg_path.parent.parent, svg_path.parent.parent.parent)
        for base in bases:
            candidate = base / 'images' / 'image_sources.json'
            if candidate.exists():
                return candidate
        return None

    def _load_image_sources_manifest(
        self,
        svg_path: Path,
    ) -> Tuple[Dict, str | None, Path | None]:
        manifest_path = self._find_image_sources_manifest(svg_path)
        if manifest_path is None:
            return {}, None, None
        payload, error = self._read_image_sources_manifest(manifest_path)
        return payload, error, manifest_path

    def _read_image_sources_manifest(
        self,
        manifest_path: Path,
    ) -> Tuple[Dict, str | None]:
        """Read one provenance manifest without accepting damaged state."""
        if manifest_path in self._source_manifest_cache:
            return self._source_manifest_cache[manifest_path]
        try:
            payload = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            payload = {}
            error = f"cannot read {manifest_path}: {exc}"
        else:
            if not isinstance(payload, dict):
                error = f"{manifest_path} must contain a JSON object"
                payload = {}
            elif not isinstance(payload.get('items'), list):
                error = f"{manifest_path} must contain an items array"
                payload = {}
            elif any(not isinstance(item, dict) for item in payload['items']):
                error = f"{manifest_path} items must contain JSON objects"
                payload = {}
            else:
                seen_filenames: set[str] = set()
                error = None
                for index, item in enumerate(payload['items']):
                    filename = item.get('filename')
                    if (
                        not isinstance(filename, str)
                        or not filename.strip()
                        or filename in {'.', '..'}
                        or '/' in filename
                        or '\\' in filename
                        or ':' in filename
                        or Path(filename).is_absolute()
                    ):
                        error = (
                            f"{manifest_path} items[{index}].filename must be "
                            "a non-empty bare filename"
                        )
                        break
                    if filename in seen_filenames:
                        error = (
                            f"{manifest_path} contains duplicate filename "
                            f"{filename!r}"
                        )
                        break
                    seen_filenames.add(filename)
                if error:
                    payload = {}
        self._source_manifest_cache[manifest_path] = (payload, error)
        return payload, error

    @staticmethod
    def _external_image_reference_basename(href: str) -> str | None:
        """Return a decoded basename for one local external image href."""
        if not href or href.startswith('data:'):
            return None
        decoded_href = html.unescape(href)
        parsed = urlsplit(decoded_href)
        if parsed.scheme and parsed.scheme != 'file':
            return None
        path_part = (
            parsed.path
            if parsed.scheme
            else decoded_href.split('?', 1)[0].split('#', 1)[0]
        )
        return Path(unquote(path_part)).name or None

    @classmethod
    def _referenced_image_basenames(cls, root: ET.Element) -> set[str]:
        """Return external image basenames rendered by one parsed SVG."""
        filenames = set()
        _working_root, _parent_by_id, images = cls._visible_image_elements(root)
        for elem in images:
            href = elem.get('href') or elem.get(f'{{{XLINK_NS}}}href')
            filename = cls._external_image_reference_basename(href or '')
            if filename:
                filenames.add(filename)
        return filenames

    def _check_sourced_image_attribution(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ):
        """Require visible credit text for attribution-required web images.

        image_search.py records the legal tier in images/image_sources.json;
        Executor must render compact credit text into the SVG. This check
        binds each credit to the referenced image's author and license instead
        of accepting one generic deck-level CC token.
        """
        manifest, error, manifest_path = self._load_image_sources_manifest(svg_path)
        if error:
            if (
                manifest_path is not None
                and manifest_path not in self._source_manifest_errors_reported
            ):
                result['errors'].append(
                    f"Invalid image source manifest: {error}"
                )
                self._source_manifest_errors_reported.add(manifest_path)
            return

        items = manifest.get('items') or []
        if not items:
            return

        credit_blocks = self._visible_svg_text_blocks(root)
        referenced_filenames = self._referenced_image_basenames(root)

        for item in items:
            if not item.get('attribution_required') and item.get('license_tier') != 'attribution-required':
                continue

            filename = str(item.get('filename') or '')
            if not filename or filename not in referenced_filenames:
                continue

            license_name = str(item.get('license_name') or '').upper()
            license_token = 'CC BY-SA' if 'BY-SA' in license_name else 'CC BY'
            author = str(item.get('author') or '').strip()
            has_credit = bool(author) and any(
                author.casefold() in block.casefold()
                and license_token in block.upper()
                for block in credit_blocks
            )
            if not has_credit:
                result['errors'].append(
                    f"Missing image-specific inline attribution for sourced "
                    f"image {filename} ({author or 'unknown author'}; "
                    f"{license_token}). Add compact author + license credit per "
                    f"references/image-searcher.md §7."
                )

    @classmethod
    def _visible_svg_text_blocks(cls, root: ET.Element) -> List[str]:
        """Return rendered text blocks, excluding hidden/non-visual content."""
        working_root = copy.deepcopy(root)
        if (
            _expand_local_use_references is not None
            and _UseExpansionError is not None
        ):
            try:
                _expand_local_use_references(working_root)
            except _UseExpansionError:
                working_root = copy.deepcopy(root)
        parent_by_id = {
            id(child): parent
            for parent in working_root.iter()
            for child in list(parent)
        }

        blocks: List[str] = []
        for element in working_root.iter(f'{{{SVG_NS}}}text'):
            if (
                cls._is_hidden_element(element, parent_by_id)
                or cls._has_non_visual_ancestor(
                    element,
                    working_root,
                    parent_by_id,
                )
                or cls._has_zero_opacity(element, parent_by_id)
            ):
                continue
            text = re.sub(r'\s+', ' ', ' '.join(element.itertext())).strip()
            if text:
                blocks.append(text)
        return blocks

    @staticmethod
    def _normalize_size(value: str) -> str:
        """Normalize a font-size value for drift comparison.

        Unit-bearing SVG values are reported as errors before drift checking.
        The legacy `px` strip remains to avoid a duplicate drift warning after
        the hard error has already identified the unit problem.
        """
        v = value.strip().lower()
        if v.endswith('px'):
            v = v[:-2].strip()
        return v

    @staticmethod
    def _normalize_font_stack(stack: str) -> str:
        """Normalize a font-family stack for comparison: split on commas, strip
        quotes / whitespace, lowercase, rejoin. Collapses cosmetic differences
        (comma spacing, single vs double quotes, case) so that
        `Consolas,'Courier New',monospace` matches `Consolas, "Courier New", monospace`."""
        parts = [p.strip().strip('"\'').lower() for p in stack.split(',')]
        return ','.join(p for p in parts if p)

    def _categorize_issue(self, error_msg: str) -> str:
        """Categorize issue type"""
        if 'Invalid XML' in error_msg:
            return 'XML well-formedness'
        elif 'viewBox' in error_msg:
            return 'viewBox issues'
        elif 'foreignObject' in error_msg:
            return 'foreignObject'
        elif 'paint' in error_msg.lower() or 'color value' in error_msg.lower():
            return 'Paint issues'
        elif 'font' in error_msg.lower():
            return 'Font issues'
        else:
            return 'Other'

    def _configure_prototype_context(
        self,
        target_path: Path,
        svg_files: List[Path],
    ) -> None:
        """Map generated pages to selected prototypes for inherited diagnostics."""
        self._prototype_by_output = {}
        self._active_prototype_path = None
        self._active_template_reuse_scope = None
        self._source_import_summary = {
            'warning_count': 0,
            'by_code': {},
        }
        if (
            self.template_mode
            or self.quick_generate
            or _load_pptx_structure_lock is None
        ):
            return
        project_path = self._resolve_project_path(target_path)
        try:
            structure_lock = _load_pptx_structure_lock(project_path)
        except (_TemplateStructureError, OSError):
            # The project-level structure gate reports the actionable parser
            # error. Inherited classification is optional and stays silent.
            return
        if structure_lock is None:
            return
        self._active_template_reuse_scope = getattr(
            structure_lock,
            'template_reuse_scope',
            None,
        )
        references = {
            reference.slide_num: reference.svg_path
            for reference in structure_lock.prototypes
        }
        if target_path.is_file():
            sibling_files = discover_slide_svgs(target_path.parent)
            resolved_target = target_path.resolve()
            slide_num = next(
                (
                    index
                    for index, sibling in enumerate(sibling_files, start=1)
                    if sibling.resolve() == resolved_target
                ),
                1,
            )
            prototype = references.get(slide_num)
            if prototype is not None:
                self._prototype_by_output[resolved_target] = prototype.resolve()
        else:
            for slide_num, svg_path in enumerate(svg_files, start=1):
                prototype = references.get(slide_num)
                if prototype is not None:
                    self._prototype_by_output[svg_path.resolve()] = prototype.resolve()

        if self._active_template_reuse_scope not in {'mirror', 'layout'}:
            return
        manifest_path = (
            project_path / 'templates' / 'template_execution_manifest.json'
        )
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return
        if manifest.get('schema') != 'ppt-master.template-execution-manifest.v1':
            return
        source_import = manifest.get('source_import')
        if isinstance(source_import, dict):
            self._source_import_summary = source_import

    def check_directory(self, directory: str, expected_format: str = None) -> List[Dict]:
        """
        Check all SVG files in a directory

        Args:
            directory: Directory path
            expected_format: Expected canvas format

        Returns:
            List of check results
        """
        dir_path = Path(directory)
        self._has_incomplete_page_roster = False
        self._undeclared_size_occurrences = Counter()
        self._undeclared_size_counts_ready = False

        if not dir_path.exists():
            print(f"[ERROR] Directory does not exist: {directory}")
            self.summary['errors'] += 1
            self.issue_types['Input issues'] += 1
            return []

        # Brand and Style workspaces have no SVG roster. Validate their
        # portable contracts through the same authority used by library
        # registration, while keeping project scope independent of global
        # indexes and directory names.
        if self.template_mode and dir_path.is_dir():
            nested_spec = dir_path / 'templates' / 'design_spec.md'
            spec = nested_spec if nested_spec.is_file() else dir_path / 'design_spec.md'
            spec_kind = _design_spec_kind(spec) if spec.exists() else None
            if spec_kind in {'brand', 'style'}:
                self._spec_only_template_kind = spec_kind
                self.summary['total'] += 1
                spec_valid = True
                pretty_kind = spec_kind.title()
                print(
                    f"[INFO] {pretty_kind} directory detected "
                    f"(kind: {spec_kind}) — "
                    f"validating its portable workspace contract."
                )
                workspace_root = (
                    spec.parent.parent
                    if spec.parent.name == 'templates'
                    else spec.parent
                )
                try:
                    from register_template import (
                        SpecParseError,
                        validate_brand_workspace,
                        validate_style_workspace,
                    )
                    validator = {
                        'brand': validate_brand_workspace,
                        'style': validate_style_workspace,
                    }[spec_kind]
                    validator(workspace_root)
                except ImportError as exc:
                    spec_valid = False
                    self._template_issues.append((
                        'error',
                        f'{spec_kind}_contract',
                        f"{pretty_kind} schema validator could not be imported: {exc}",
                    ))
                except (OSError, SpecParseError) as exc:
                    spec_valid = False
                    self._template_issues.append((
                        'error',
                        f'{spec_kind}_contract',
                        str(exc),
                    ))
                if spec_valid:
                    self.summary['passed'] += 1
                return self.results

        # Find all SVG files
        if dir_path.is_file():
            svg_files = [dir_path]
        else:
            if self.template_mode:
                # Template directories live at templates/{layouts,decks}/<id>/.
                svg_files = discover_slide_svgs(dir_path)
            else:
                svg_output = dir_path / \
                    'svg_output' if (
                        dir_path / 'svg_output').exists() else dir_path
                svg_files = discover_slide_svgs(svg_output)

        if not svg_files:
            print(f"[ERROR] No SVG files found in: {directory}")
            self.summary['errors'] += 1
            self.issue_types['Input issues'] += 1
            return []

        self._active_slide_count = len(svg_files)

        self._configure_prototype_context(dir_path, svg_files)
        if not self.template_mode:
            self._prepare_undeclared_size_occurrences(svg_files)

        directory_expected_viewbox: str | None = None
        directory_expected_label = "the first SVG canvas"
        directory_lock_has_canvas = False
        if self.template_mode:
            template_viewbox = _declared_template_canvas_viewbox(dir_path)
            if template_viewbox:
                directory_expected_viewbox = template_viewbox
                directory_expected_label = "design_spec canvas_viewbox"
            else:
                directory_expected_viewbox = ""
                directory_expected_label = "design_spec canvas_viewbox"
        if expected_format is None and directory_expected_viewbox is None:
            lock = (
                None
                if self.template_mode
                else self._get_spec_lock(svg_files[0])
            )
            if lock is not None:
                if 'canvas' in lock:
                    directory_lock_has_canvas = True
                    locked_viewbox = lock.get('canvas', {}).get('viewBox')
                    if locked_viewbox:
                        directory_expected_viewbox = locked_viewbox
                        directory_expected_label = "spec_lock canvas"
                else:
                    directory_expected_viewbox = ""
                    directory_expected_label = "spec_lock canvas"
            if (
                directory_expected_viewbox is None
                and not directory_lock_has_canvas
            ):
                for svg_file in svg_files:
                    try:
                        root = ET.parse(svg_file).getroot()
                        first_canvas = parse_project_viewbox(
                            root.get('viewBox'),
                            context=f"{svg_file.name} root viewBox",
                        )
                    except (OSError, ET.ParseError, CanvasContractError):
                        continue
                    directory_expected_viewbox = first_canvas.canonical
                    directory_expected_label = f"first SVG {svg_file.name}"
                    break

        print(f"\n[SCAN] Checking {len(svg_files)} SVG file(s)...\n")

        for svg_file in svg_files:
            self._active_prototype_path = self._prototype_by_output.get(
                svg_file.resolve()
            )
            result = self.check_file(
                str(svg_file),
                expected_format,
                expected_viewbox=directory_expected_viewbox,
                expected_viewbox_label=directory_expected_label,
            )
            self._print_result(result)

        if self.template_mode:
            check_structure = _template_structure_checks_enabled(dir_path)
            if check_structure:
                self._check_pptx_structure_contract(dir_path, svg_files)
            if dir_path.is_dir():
                self._check_template_contract(
                    dir_path,
                    svg_files,
                    check_structure=check_structure,
                )
        elif _CHECK_PPTX_STRUCTURED_PROJECT:
            self._check_pptx_structure_contract(dir_path, svg_files)
        if (
            not self.template_mode
            and not self.quick_generate
            and dir_path.is_dir()
        ):
            self._check_animation_config_contract(dir_path)
            self._check_illustration_resource_contract(dir_path)
        if (
            not self.template_mode
            and not self.quick_generate
            and validate_communication_trace is not None
        ):
            project_path = self._resolve_project_path(dir_path)
            self._communication_trace_issues.extend(
                ('error', message)
                for message in validate_communication_trace(project_path)
            )
        return self.results

    def _check_pptx_structure_contract(
        self,
        target_path: Path,
        svg_files: List[Path],
    ) -> None:
        """Validate the all-page structured lock and reusable contracts."""
        if self.quick_generate:
            return
        project_path = self._resolve_project_path(target_path)
        standard_project = bool(
            not self.template_mode
            and (project_path / 'svg_output').is_dir()
        )
        declared_mode = (
            _declared_pptx_structure_mode(project_path)
            if standard_project
            else None
        )
        if standard_project and declared_mode in {'flat', 'structured'}:
            self._pptx_structure_issues.extend(
                ('error', message)
                for message in _generated_theme_contract_errors(project_path)
            )
        if standard_project and declared_mode == 'flat':
            if (
                _load_pptx_structure_lock is None
                or _TemplateStructureError is None
            ):
                self._pptx_structure_issues.append((
                    'error',
                    'Flat PPTX project validation is unavailable because the '
                    'template_structure module could not be imported.',
                ))
                return
            try:
                structure_lock = _load_pptx_structure_lock(project_path)
            except _TemplateStructureError as exc:
                self._pptx_structure_issues.append(('error', str(exc)))
                return
            if structure_lock is None or structure_lock.mode != 'flat':
                self._pptx_structure_issues.append((
                    'error',
                    'spec_lock.md must contain one complete '
                    'pptx_structure.mode: flat contract.',
                ))
            return
        has_metadata = False
        for svg_path in svg_files:
            try:
                root = ET.parse(svg_path).getroot()
            except (OSError, ET.ParseError):
                continue
            if any(
                elem.get(attr) is not None
                for elem in root.iter()
                for attr in _PPTX_STRUCTURE_ATTRS
            ):
                has_metadata = True
                break

        if not standard_project and not self.template_mode and not has_metadata:
            return
        if (
            _load_pptx_structure_lock is None
            or _parse_template_structure_slide is None
            or _parse_template_structure_slides is None
            or _structure_subtree_signature is None
            or _template_lock_errors is None
            or _TemplateStructureError is None
        ):
            self._pptx_structure_issues.append((
                'error',
                'Structured PPTX project validation is unavailable because the '
                'template_structure module could not be imported.',
            ))
            return

        if self.template_mode:
            try:
                specs = _parse_template_structure_slides(svg_files)
            except _TemplateStructureError as exc:
                self._pptx_structure_issues.append(('error', str(exc)))
                return
            self._pptx_structure_issues.extend(
                ('error', message)
                for message in self._shared_fixed_layer_errors(specs)
            )
            self._pptx_structure_issues.extend(
                ('warning', message)
                for message in self._duplicate_layout_key_warnings(specs)
            )
            return

        if standard_project and declared_mode != 'structured':
            label = repr(declared_mode) if declared_mode else (
                'missing (legacy implicit baseline)'
            )
            self._pptx_structure_issues.append((
                'error',
                'release SVG projects require an explicit spec_lock.md '
                'pptx_structure.mode: flat (free design / brand-only) or '
                f'structured (deck/layout template); found {label}. New '
                'free-design projects use mode: flat; create a new template '
                'workspace through skills/ppt-master/workflows/create-template.md, '
                'then generate new structured SVG pages before export. Existing '
                'PPTX/SVG files are not upgraded in place.',
            ))
            return

        try:
            structure_lock = _load_pptx_structure_lock(project_path)
        except _TemplateStructureError as exc:
            self._pptx_structure_issues.append(('error', str(exc)))
            return
        if structure_lock is None or structure_lock.mode != 'structured':
            self._pptx_structure_issues.append((
                'error',
                'spec_lock.md must contain one complete '
                'pptx_structure.mode: structured contract.',
            ))
            return
        complete_roster = target_path.is_dir()
        try:
            if not complete_roster and target_path.is_file():
                sibling_files = discover_slide_svgs(target_path.parent)
                resolved_target = target_path.resolve()
                slide_num = next(
                    (
                        index
                        for index, sibling in enumerate(sibling_files, start=1)
                        if sibling.resolve() == resolved_target
                    ),
                    1,
                )
                specs = [
                    _parse_template_structure_slide(target_path, slide_num)
                ]
            else:
                specs = _parse_template_structure_slides(svg_files)
        except _TemplateStructureError as exc:
            self._pptx_structure_issues.append(('error', str(exc)))
            return

        if complete_roster:
            actual_slides = {spec.slide_num for spec in specs}
            expected_slides = {
                reference.slide_num
                for reference in structure_lock.layouts
            }
            expected_slides.update(
                reference.slide_num
                for reference in structure_lock.prototypes
            )
            self._has_incomplete_page_roster = bool(
                expected_slides - actual_slides
            )
            self._pptx_structure_issues.extend(
                ('error', message)
                for message in _template_lock_errors(specs, structure_lock)
            )
        else:
            self._pptx_structure_issues.extend(
                ('error', message)
                for message in self._partial_structure_lock_errors(
                    specs,
                    structure_lock,
                )
            )
        if _template_prototype_errors is not None:
            self._pptx_structure_issues.extend(
                ('error', message)
                for message in _template_prototype_errors(
                    specs,
                    structure_lock,
                    require_complete_roster=complete_roster,
                )
            )
        self._pptx_structure_issues.extend(
            ('error', message)
            for message in self._shared_fixed_layer_errors(specs)
        )
        self._pptx_structure_issues.extend(
            ('warning', message)
            for message in self._duplicate_layout_key_warnings(specs)
        )

    @staticmethod
    def _partial_structure_lock_errors(specs, structure_lock) -> List[str]:
        """Compare explicitly checked pages without requiring the full roster."""
        references = {
            reference.slide_num: reference
            for reference in structure_lock.layouts
        }
        master_names = {
            master.master_key: master.master_name
            for master in structure_lock.masters
        }
        definitions = {
            definition.layout_key: definition
            for definition in structure_lock.layout_definitions
        }
        errors: List[str] = []
        for spec in specs:
            page = f"P{spec.slide_num:02d}"
            reference = references.get(spec.slide_num)
            if reference is None:
                errors.append(
                    f"spec_lock.md page_pptx_layouts is missing {page}"
                )
                continue
            definition = definitions.get(reference.layout_key)
            if definition is None:
                errors.append(
                    f"spec_lock.md pptx_layouts is missing Layout "
                    f"{reference.layout_key!r}"
                )
                continue
            if spec.master_key != definition.master_key:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-master={spec.master_key!r} "
                    f"does not match spec_lock Layout {reference.layout_key!r} "
                    f"Master key {definition.master_key!r}"
                )
            if spec.layout_key != reference.layout_key:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-layout={spec.layout_key!r} "
                    f"does not match spec_lock {page} layout key "
                    f"{reference.layout_key!r}"
                )
            if spec.layout_name != definition.layout_name:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-layout-name="
                    f"{spec.layout_name!r} does not match spec_lock Layout "
                    f"{reference.layout_key!r} name {definition.layout_name!r}"
                )
            expected_master_name = master_names.get(spec.master_key)
            if expected_master_name != spec.master_name:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-master-name="
                    f"{spec.master_name!r} does not match spec_lock Master "
                    f"{spec.master_key!r} name {expected_master_name!r}"
                )
        return errors

    def _duplicate_layout_key_warnings(self, specs) -> List[str]:
        """Flag distinct layout keys whose static contracts are identical.

        Keys split by page topic over one shared skeleton compile into
        duplicate PowerPoint Layouts; the fingerprint compares the
        id-insensitive layout-layer drawing plus the placeholder contract.
        """
        prototypes: Dict[Tuple[str, str], Path] = {}
        for spec in specs:
            prototypes.setdefault(
                (getattr(spec, 'master_key', ''), spec.layout_key),
                spec.svg_path,
            )
        if len(prototypes) < 2:
            return []
        fingerprint_keys: Dict[tuple, List[str]] = {}
        for (master_key, layout_key), svg_path in prototypes.items():
            fingerprint = self._layout_contract_fingerprint(svg_path)
            if fingerprint is None:
                continue
            fingerprint_keys.setdefault(
                (master_key, fingerprint),
                [],
            ).append(layout_key)
        messages = []
        for keys in fingerprint_keys.values():
            if len(keys) < 2:
                continue
            joined = ', '.join(sorted(keys))
            messages.append(
                f"layout keys {joined} declare identical static Layout framing "
                "and placeholder contracts; they compile to duplicate Layouts. "
                "Either merge them into one reusable key (spec_lock.md "
                "pptx_layouts + each SVG root), or — when their reusable "
                "contracts genuinely differ — assign distinct explicit default "
                "placeholder bounds and/or mark only truly stable framing as "
                'data-pptx-layer="layout". Slide-local content geometry does not '
                "define a Layout. This recommendation is advisory; no change or "
                "disposition is required."
            )
        return messages

    @classmethod
    def _shared_fixed_layer_errors(cls, specs) -> List[str]:
        """Reject fixed atoms whose payload varies inside one reuse scope."""
        master_groups = defaultdict(list)
        layout_groups = defaultdict(list)
        for spec in specs:
            master_groups[spec.master_key].append(spec)
            layout_groups[(spec.master_key, spec.layout_key)].append(spec)

        try:
            errors = cls._fixed_layer_group_errors(master_groups, 'master')
            errors.extend(cls._fixed_layer_group_errors(layout_groups, 'layout'))
        except _TemplateStructureError as exc:
            return [str(exc)]
        return errors

    @classmethod
    def _fixed_layer_group_errors(cls, groups, layer: str) -> List[str]:
        """Compare fixed atom payloads across grouped slide specifications."""
        errors = []
        for scope_key, group_specs in groups.items():
            if len(group_specs) < 2:
                continue
            variants = defaultdict(lambda: defaultdict(list))
            for spec in group_specs:
                payloads = cls._fixed_layer_payloads(spec, layer)
                for element_id, payload in payloads.items():
                    variants[element_id][payload].append(spec)
            for element_id, payload_specs in variants.items():
                if len(payload_specs) < 2:
                    continue
                slide_names = ', '.join(
                    spec.svg_path.name
                    for spec in sorted(group_specs, key=lambda item: item.slide_num)
                )
                if layer == 'master':
                    scope = f"Master {scope_key!r}"
                else:
                    master_key, layout_key = scope_key
                    scope = (
                        f"Layout {layout_key!r} under Master {master_key!r}"
                    )
                if element_id is None:
                    subject = "fixed visual resources"
                    verb = "differ"
                else:
                    subject = f"fixed element {element_id!r}"
                    verb = "differs"
                errors.append(
                    f"{scope} {subject} {verb} across slides: "
                    f"{slide_names}. Values marked data-pptx-layer={layer!r} must "
                    "remain identical throughout their reuse scope; move variable "
                    "text or images into a placeholder slot or keep them Slide-local."
                )
        return errors

    @staticmethod
    def _fixed_layer_payloads(spec, layer: str) -> Dict[object, tuple]:
        """Return resolved fixed-layer visual payloads keyed by SVG id."""
        elements = (
            spec.master_elements if layer == 'master' else spec.layout_elements
        )
        if not elements:
            return {}
        signature = _structure_subtree_signature(
            spec.svg_path,
            elements,
            include_skin=True,
            include_text=True,
            asset_identity=True,
        )
        return {
            None if element_id == '__visual_resources__' else element_id: payload
            for element_id, payload in signature
        }

    @staticmethod
    def _layout_contract_fingerprint(svg_path: Path):
        """Id-insensitive static contract: layout-layer XML + placeholder slots."""
        try:
            root = ET.parse(str(svg_path)).getroot()
        except (OSError, ET.ParseError):
            return None
        layout_parts = []
        placeholder_parts = []
        for child in list(root):
            if child.get('data-pptx-layer') == 'layout':
                clone = copy.deepcopy(child)
                for elem in clone.iter():
                    elem.attrib.pop('id', None)
                xml = ET.tostring(clone, encoding='unicode')
                layout_parts.append(re.sub(r'\s+', ' ', xml).strip())
            placeholder = child.get('data-pptx-placeholder')
            if placeholder is not None:
                carrier_tags = tuple(
                    grandchild.tag.rsplit('}', 1)[-1]
                    for grandchild in list(child)
                    if (
                        grandchild.get('data-pptx-carrier') or ''
                    ).strip().lower() == 'true'
                )
                placeholder_parts.append((
                    placeholder,
                    child.tag.rsplit('}', 1)[-1],
                    child.get('data-pptx-bounds') or '',
                    child.get('data-pptx-idx') or '',
                    (
                        child.get('data-pptx-binding') or 'carrier'
                    ).strip().lower(),
                    carrier_tags,
                ))
        return (
            tuple(layout_parts),
            tuple(sorted(placeholder_parts)),
        )

    def _check_illustration_resource_contract(self, dir_path: Path) -> None:
        """Project-level planned-image and illustration resource checks."""
        project_path = self._resolve_project_path(dir_path)
        spec_path = project_path / 'design_spec.md'
        if not spec_path.exists():
            return

        try:
            spec_text = spec_path.read_text(encoding='utf-8')
        except OSError as exc:
            self._illustration_issues.append((
                'warning',
                'spec_unreadable',
                f"could not read {spec_path}: {exc}",
            ))
            return

        current_contract = (
            '<!-- ppt-master-schema: design-spec/v1 -->' in spec_text
        )
        rows = self._extract_image_resource_rows(spec_text)
        if not rows and not current_contract:
            return

        lock_entries, lock_error = self._load_project_lock_image_entries(
            project_path
        )
        lock_images = set(lock_entries)
        svg_references, inline_image_counts, image_placements = (
            self._load_project_svg_image_references(project_path)
        )
        all_svg_references = (
            set().union(*(
                set(references)
                for references in svg_references.values()
            ))
            if svg_references
            else set()
        )

        sheet_rows = [
            row
            for row in rows
            if self._row_type(row).lower() == 'illustration sheet'
        ]
        slice_rows = [row for row in rows if self._row_acquire(row) == 'slice']
        for row in sheet_rows:
            filename = self._row_filename(row)
            if not filename:
                continue
            if filename in lock_images:
                self._illustration_issues.append((
                    'error',
                    'sheet_in_lock',
                    f"{filename} is an Illustration Sheet but is listed in spec_lock.md images; "
                    "only sliced element rows may be listed.",
                ))
            if filename in all_svg_references:
                self._illustration_issues.append((
                    'error',
                    'sheet_referenced',
                    f"{filename} is an Illustration Sheet but is referenced by an SVG; "
                    "generate it only as a slice source, never place it.",
                ))
            if (
                self._row_status(row) == 'generated'
                and not (project_path / 'images' / filename).is_file()
            ):
                self._illustration_issues.append((
                    'error',
                    'sheet_file_missing',
                    f"{filename} is a Generated Illustration Sheet but "
                    f"images/{filename} does not exist.",
                ))

        if current_contract:
            self._check_planned_image_closure(
                rows,
                project_path,
                lock_entries,
                lock_error,
                svg_references,
                inline_image_counts,
                image_placements,
            )
        else:
            for row in slice_rows:
                filename = self._row_filename(row)
                if not filename:
                    continue
                if filename not in lock_images:
                    self._illustration_issues.append((
                        'error',
                        'slice_missing_lock',
                        f"{filename} is a slice row but is absent from spec_lock.md images.",
                    ))
                if (
                    self._row_status(row) == 'generated'
                    and not (project_path / 'images' / filename).exists()
                ):
                    self._illustration_issues.append((
                        'error',
                        'slice_file_missing',
                        f"{filename} is a Generated slice row but "
                        f"images/{filename} does not exist.",
                    ))

    @staticmethod
    def _resolve_project_path(dir_path: Path) -> Path:
        """Resolve a checker target directory to its project root."""
        candidate = dir_path.parent if dir_path.is_file() else dir_path
        if (
            _project_root_for_svg_path is not None
            and candidate.name in _SVG_WORK_DIR_NAMES
        ):
            return _project_root_for_svg_path(candidate)
        if (
            (candidate / 'svg_output').exists()
            or (candidate / 'design_spec.md').exists()
        ):
            return candidate
        return candidate.parent

    @staticmethod
    def _split_md_table_row(line: str) -> List[str]:
        """Split a simple Markdown table row into stripped cells."""
        return [cell.strip().strip('`') for cell in line.strip().strip('|').split('|')]

    @classmethod
    def _extract_image_resource_rows(cls, spec_text: str) -> List[Dict[str, str]]:
        """Extract rows from design_spec.md §VIII Image Resource List."""
        section_match = re.search(
            r"^##\s+VIII\.\s+Image Resource List\b.*?(?=^##\s+|\Z)",
            spec_text,
            re.MULTILINE | re.DOTALL,
        )
        if not section_match:
            return []

        lines = section_match.group(0).splitlines()
        header = None
        rows: List[Dict[str, str]] = []
        in_resource_table = False
        for line in lines:
            if not line.strip().startswith('|'):
                if in_resource_table and rows:
                    break
                continue

            cells = cls._split_md_table_row(line)
            if not cells:
                continue
            if header is None:
                if any(cell.lower() == 'filename' for cell in cells):
                    header = cells
                    in_resource_table = True
                continue
            if set(cell.replace('-', '').strip() for cell in cells) == {''}:
                continue
            if not in_resource_table:
                continue
            row = {header[i]: cells[i] if i < len(cells) else '' for i in range(len(header))}
            filename = row.get('Filename', '').strip()
            if (
                filename.lower() != 'filename'
                and any(value.strip() for value in row.values())
            ):
                rows.append(row)

        return rows

    @staticmethod
    def _row_filename(row: Dict[str, str]) -> str:
        return Path(row.get('Filename', '').strip()).name

    @staticmethod
    def _row_raw_filename(row: Dict[str, str]) -> str:
        return row.get('Filename', '').strip()

    @staticmethod
    def _row_type(row: Dict[str, str]) -> str:
        return row.get('Type', '').strip()

    @staticmethod
    def _row_acquire(row: Dict[str, str]) -> str:
        return row.get('Acquire Via', '').strip().lower()

    @staticmethod
    def _row_status(row: Dict[str, str]) -> str:
        return row.get('Status', '').strip().lower()

    @staticmethod
    def _row_layout(row: Dict[str, str]) -> str:
        return row.get('Layout pattern', '').strip()

    @staticmethod
    def _row_crop(row: Dict[str, str]) -> str:
        return row.get('Crop Policy', '').strip().lower()

    @staticmethod
    def _layout_projection_matches(left: str, right: str) -> bool:
        """Compare one Strategist recommendation without locking its wording."""
        left_ids = re.findall(r'#([0-9]+)(?![0-9])', left)
        right_ids = re.findall(r'#([0-9]+)(?![0-9])', right)
        if left_ids or right_ids:
            return left_ids == right_ids

        def normalize(value: str) -> str:
            return re.sub(r'\s+', ' ', value.replace('`', '')).strip()

        return normalize(left) == normalize(right)

    def _load_project_lock_image_entries(
        self,
        project_path: Path,
    ) -> Tuple[Dict[str, List[Dict[str, str]]], str | None]:
        """Return parsed image-lock rows keyed by basename."""
        lock_path = project_path / 'spec_lock.md'
        if not lock_path.exists():
            return {}, f"{lock_path} does not exist"
        if _parse_spec_lock is None:
            return {}, "spec_lock parser is unavailable"
        if _parse_spec_lock_image_value is None:
            return {}, "spec_lock image parser is unavailable"
        try:
            lock = _parse_spec_lock(lock_path)
        except Exception as exc:
            return {}, f"cannot parse {lock_path}: {exc}"

        entries: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        legacy_metadata_keys = {
            'image_rendering',
            'image_rendering_references',
            'image_rendering_behavior',
        }
        errors: List[str] = []
        for key, value in lock.get('images', {}).items():
            if str(key).strip().lower() in legacy_metadata_keys:
                continue
            try:
                parsed = _parse_spec_lock_image_value(str(key), str(value))
            except ValueError as exc:
                errors.append(f"images row {key!r} {exc}")
                continue
            path_part = parsed['path']
            filename = Path(path_part).name
            if not filename:
                continue
            entries[filename].append({
                'key': str(key),
                'path': path_part,
                'source': parsed['source'],
                'pattern': parsed['pattern'],
                'crop': parsed['crop'],
                'legacy': parsed['legacy'],
            })
        error = (
            f"{lock_path}: " + "; ".join(errors)
            if errors
            else None
        )
        return dict(entries), error

    def _load_project_lock_images(self, project_path: Path) -> set[str]:
        """Return filenames listed under spec_lock.md images."""
        entries, _error = self._load_project_lock_image_entries(project_path)
        return set(entries)

    @classmethod
    def _load_project_svg_image_references(
        cls,
        project_path: Path,
    ) -> Tuple[
        Dict[Path, Dict[str, set[Path]]],
        Dict[Path, int],
        Dict[str, List[Tuple[Path, str, Tuple[str, ...]]]],
    ]:
        """Parse rendered image instances, paths, and crop mechanisms."""
        svg_dir = project_path / 'svg_output'
        if not svg_dir.exists():
            return {}, {}, {}
        out: Dict[Path, Dict[str, set[Path]]] = {}
        inline_counts: Dict[Path, int] = {}
        placements: Dict[
            str,
            List[Tuple[Path, str, Tuple[str, ...]]],
        ] = defaultdict(list)
        for svg_path in discover_slide_svgs(svg_dir):
            try:
                root = ET.parse(svg_path).getroot()
            except (OSError, ET.ParseError):
                continue
            working_root, parent_by_id, images = cls._visible_image_elements(root)
            references: Dict[str, set[Path]] = defaultdict(set)
            inline_count = 0
            for element in images:
                href = (
                    element.get('href')
                    or element.get(f'{{{XLINK_NS}}}href')
                    or ''
                )
                if href.lstrip().lower().startswith('data:'):
                    inline_count += 1
                    continue
                filename = cls._external_image_reference_basename(href)
                if not filename:
                    continue
                references.setdefault(filename, set())
                placements[filename].append((
                    svg_path,
                    element.get('preserveAspectRatio') or '',
                    cls._image_crop_mechanisms(
                        element,
                        working_root,
                        parent_by_id,
                    ),
                ))
                if _resolve_external_image_reference is not None:
                    resolved = _resolve_external_image_reference(
                        svg_path.parent,
                        href,
                    )
                    if resolved is not None:
                        references[filename].add(resolved.resolve())
            out[svg_path] = dict(references)
            if inline_count:
                inline_counts[svg_path] = inline_count
        return out, inline_counts, dict(placements)

    @staticmethod
    def _image_crop_mechanisms(
        image: ET.Element,
        root: ET.Element,
        parent_by_id: Dict[int, ET.Element],
    ) -> Tuple[str, ...]:
        """Return objective clipping mechanisms affecting one image instance."""
        mechanisms: List[str] = []
        current: ET.Element | None = image
        while current is not None:
            tag = _local_name(current)
            style_values = (
                _parse_inline_style(current.get('style'))
                if _parse_inline_style is not None
                else {}
            )
            for property_name in ('clip-path', 'mask'):
                value = style_values.get(property_name)
                if value is None:
                    value = current.get(property_name)
                if value and value.strip().lower() != 'none':
                    mechanisms.append(f"<{tag}> {property_name}")
            overflow = style_values.get('overflow')
            if overflow is None:
                overflow = current.get('overflow')
            if overflow and overflow.strip().lower() in {'hidden', 'clip'}:
                mechanisms.append(f"<{tag}> overflow={overflow.strip()!r}")
            if current is not root and tag == 'svg':
                mechanisms.append('nested <svg> viewport')
            current = parent_by_id.get(id(current))
        return tuple(dict.fromkeys(mechanisms))

    def _check_planned_image_closure(
        self,
        rows: List[Dict[str, str]],
        project_path: Path,
        lock_entries: Dict[str, List[Dict[str, str]]],
        lock_error: str | None,
        svg_references: Dict[Path, Dict[str, set[Path]]],
        inline_image_counts: Dict[Path, int],
        image_placements: Dict[
            str,
            List[Tuple[Path, str, Tuple[str, ...]]],
        ],
    ) -> None:
        """Close Design Spec, execution lock, files, SVGs, and provenance."""
        project_root = project_path.resolve()
        if inline_image_counts:
            total = sum(inline_image_counts.values())
            shown = ', '.join(
                f"{path.name} ({count})"
                for path, count in sorted(inline_image_counts.items())
            )
            self._illustration_issues.append((
                'error',
                'svg_inline_image_untracked',
                f"svg_output contains {total} inline data-URI image(s): "
                f"{shown}. Current projects must keep external project-local "
                "image hrefs so every placement closes through Design Spec "
                "§VIII and spec_lock.md.",
            ))
        valid_acquisitions = {
            'ai',
            'web',
            'user',
            'formula',
            'placeholder',
            'slice',
        }
        valid_statuses = {
            'pending',
            'failed',
            'generated',
            'sourced',
            'rendered',
            'needs-manual',
            'existing',
            'placeholder',
        }
        terminal_by_acquisition = {
            'ai': {'generated', 'needs-manual'},
            'web': {'sourced', 'needs-manual'},
            'user': {'existing', 'needs-manual'},
            'formula': {'rendered', 'needs-manual'},
            'placeholder': {'placeholder'},
            'slice': {'generated', 'needs-manual'},
        }
        current_image_contract = (
            any('Crop Policy' in row for row in rows)
            or any(
                entry.get('legacy') == 'false'
                for entries in lock_entries.values()
                for entry in entries
            )
        )
        seen_filenames: set[str] = set()
        for row in rows:
            raw_filename = self._row_raw_filename(row)
            filename = self._row_filename(row)
            acquire = self._row_acquire(row)
            status = self._row_status(row)
            layout = self._row_layout(row)
            crop = self._row_crop(row)
            filename_is_bare = bool(filename) and (
                filename not in {'.', '..'}
                and '/' not in filename
                and '\\' not in filename
                and ':' not in filename
            )
            filename_is_canonical = raw_filename in {
                filename,
                f"images/{filename}",
            }
            if not filename_is_bare or not filename_is_canonical:
                self._illustration_issues.append((
                    'error',
                    'planned_image_invalid_filename',
                    f"Design Spec §VIII Filename {raw_filename!r} must be "
                    "a non-empty bare filename or canonical "
                    "images/<filename> path.",
                ))
            elif filename in seen_filenames:
                self._illustration_issues.append((
                    'error',
                    'planned_image_duplicate_filename',
                    f"Design Spec §VIII repeats Filename {filename!r}; "
                    "one resource must have one authoritative row.",
                ))
            else:
                seen_filenames.add(filename)

            if current_image_contract and not layout:
                self._illustration_issues.append((
                    'error',
                    'planned_image_missing_pattern',
                    f"{filename or '(missing filename)'} has an empty Design "
                    "Spec §VIII Layout pattern; preserve one non-empty "
                    "Strategist recommendation without locking SVG geometry.",
                ))
            if current_image_contract and crop not in {'adaptive', 'no-crop'}:
                self._illustration_issues.append((
                    'error',
                    'planned_image_invalid_crop_policy',
                    f"{filename or '(missing filename)'} has invalid Design "
                    f"Spec §VIII Crop Policy "
                    f"{row.get('Crop Policy', '').strip()!r}; use adaptive "
                    "or no-crop.",
                ))

            if acquire not in valid_acquisitions:
                self._illustration_issues.append((
                    'error',
                    'planned_image_invalid_acquisition',
                    f"{filename or '(missing filename)'} has invalid "
                    f"Acquire Via {row.get('Acquire Via', '').strip()!r}.",
                ))
                continue
            if status not in valid_statuses:
                self._illustration_issues.append((
                    'error',
                    'planned_image_invalid_status',
                    f"{filename or '(missing filename)'} has invalid "
                    f"Status {row.get('Status', '').strip()!r}.",
                ))
                continue
            if status in {'pending', 'failed'}:
                self._illustration_issues.append((
                    'error',
                    'planned_image_not_terminal',
                    f"{filename or '(missing filename)'} has non-terminal "
                    f"Status {row.get('Status', '').strip()!r}; finish the "
                    "owning acquisition or mark it Needs-Manual before export.",
                ))
            elif status not in terminal_by_acquisition[acquire]:
                expected = ', '.join(sorted(terminal_by_acquisition[acquire]))
                self._illustration_issues.append((
                    'error',
                    'planned_image_status_mismatch',
                    f"{filename or '(missing filename)'} uses Acquire Via "
                    f"{acquire!r} but Status {status!r}; terminal status must "
                    f"be one of: {expected}.",
                ))

        if lock_error:
            self._illustration_issues.append((
                'error',
                'image_lock_unreadable',
                lock_error,
            ))
            return

        placed_rows = [
            row for row in rows
            if self._row_type(row).lower() != 'illustration sheet'
            and self._row_acquire(row)
            in {'ai', 'web', 'user', 'formula', 'placeholder', 'slice'}
        ]
        rows_by_filename = {
            self._row_filename(row): row
            for row in placed_rows
            if self._row_filename(row)
        }
        referenced_paths: Dict[str, set[Path]] = defaultdict(set)
        for references in svg_references.values():
            for filename, paths in references.items():
                referenced_paths[filename].update(paths)
        referenced = set(referenced_paths)

        for filename, row in rows_by_filename.items():
            if filename not in lock_entries:
                self._illustration_issues.append((
                    'error',
                    'planned_image_missing_lock',
                    f"{filename} is a placed Design Spec image row but is "
                    "absent from spec_lock.md images.",
                ))
                continue
            if current_image_contract and any(
                entry.get('legacy') != 'false'
                for entry in lock_entries[filename]
            ):
                self._illustration_issues.append((
                    'error',
                    'planned_image_legacy_lock_projection',
                    f"{filename} uses the current Design Spec image contract "
                    "but its spec_lock.md row does not provide complete "
                    "source=..., pattern=..., and crop=... metadata.",
                ))

        for filename in sorted(referenced - set(rows_by_filename)):
            lock_note = (
                ""
                if filename in lock_entries
                else " and is absent from spec_lock.md images"
            )
            self._illustration_issues.append((
                'error',
                'svg_image_missing_spec',
                f"svg_output references {filename}, but it has no placed "
                f"Design Spec §VIII row{lock_note}.",
            ))

        for filename, entries in lock_entries.items():
            row = rows_by_filename.get(filename)
            if row is None:
                self._illustration_issues.append((
                    'error',
                    'locked_image_missing_spec',
                    f"{filename} is listed in spec_lock.md images but has no "
                    "placed row in Design Spec §VIII.",
                ))
                continue

            acquire = self._row_acquire(row)
            status = self._row_status(row)
            layout_pattern = self._row_layout(row)
            crop_policy = self._row_crop(row)
            if len(entries) > 1:
                keys = ', '.join(repr(entry.get('key', '')) for entry in entries)
                self._illustration_issues.append((
                    'error',
                    'locked_image_duplicate_entries',
                    f"{filename} appears in multiple spec_lock.md image rows "
                    f"({keys}); one resource must have one authoritative row.",
                ))
            for entry in entries:
                if entry.get('legacy') != 'false':
                    continue
                if entry.get('source') != acquire:
                    self._illustration_issues.append((
                        'error',
                        'locked_image_source_mismatch',
                        f"{filename} spec_lock source={entry.get('source')!r} "
                        f"does not match Design Spec §VIII Acquire Via "
                        f"{acquire!r}.",
                    ))
                if entry.get('crop') != crop_policy:
                    self._illustration_issues.append((
                        'error',
                        'locked_image_crop_mismatch',
                        f"{filename} spec_lock crop={entry.get('crop')!r} "
                        f"does not match Design Spec §VIII Crop Policy "
                        f"{crop_policy!r}.",
                    ))
                if not self._layout_projection_matches(
                    entry.get('pattern', ''),
                    layout_pattern,
                ):
                    self._illustration_issues.append((
                        'error',
                        'locked_image_pattern_mismatch',
                        f"{filename} spec_lock pattern="
                        f"{entry.get('pattern')!r} does not preserve the "
                        "Design Spec §VIII Layout pattern recommendation "
                        f"{layout_pattern!r}. This Design Spec-to-spec_lock "
                        "projection check compares ordered catalog ids when "
                        "present, otherwise normalized text; it does not "
                        "compare SVG geometry or restrict the Executor's "
                        "realization.",
                    ))
            candidate_paths: List[Path] = []
            for entry in entries:
                raw_path = entry.get('path', '')
                if not raw_path:
                    continue
                lock_path = Path(raw_path)
                legacy_bare_filename = (
                    not lock_path.is_absolute()
                    and raw_path not in {'.', '..'}
                    and '/' not in raw_path
                    and '\\' not in raw_path
                    and ':' not in raw_path
                )
                if lock_path.is_absolute():
                    path = lock_path
                elif legacy_bare_filename:
                    path = project_path / 'images' / raw_path
                else:
                    path = project_path / raw_path
                resolved_path = path.resolve()
                try:
                    resolved_path.relative_to(project_root)
                except ValueError:
                    self._illustration_issues.append((
                        'error',
                        'locked_image_path_outside_project',
                        f"{filename} lock path {entry['path']!r} resolves "
                        "outside the project workspace.",
                    ))
                    continue
                candidate_paths.append(resolved_path)

            distinct_candidate_paths = set(candidate_paths)
            if len(distinct_candidate_paths) > 1:
                shown = ', '.join(
                    str(path.relative_to(project_root))
                    for path in sorted(distinct_candidate_paths)
                )
                self._illustration_issues.append((
                    'error',
                    'locked_image_ambiguous_paths',
                    f"{filename} resolves to multiple locked project paths: "
                    f"{shown}. One resource must have one authoritative asset.",
                ))

            expected_paths = {
                path
                for path in distinct_candidate_paths
                if path.is_file()
            }
            asset_exists = bool(expected_paths)
            file_required = status in {
                'existing',
                'generated',
                'sourced',
                'rendered',
            }
            if not asset_exists and file_required:
                expected = entries[0].get('path') or f"images/{filename}"
                self._illustration_issues.append((
                    'error',
                    'locked_image_file_missing',
                    f"{filename} is locked and has terminal Status "
                    f"{row.get('Status', '').strip()!r}, but {expected} "
                    "does not exist.",
                ))

            actual_paths = referenced_paths.get(filename, set())
            unexpected_paths = actual_paths - expected_paths
            if unexpected_paths:
                shown = ', '.join(
                    str(path.relative_to(project_root))
                    if path.is_relative_to(project_root)
                    else str(path)
                    for path in sorted(unexpected_paths)
                )
                self._illustration_issues.append((
                    'error',
                    'locked_image_reference_mismatch',
                    f"{filename} is referenced from {shown}, not exclusively "
                    "from its locked project path.",
                ))

            should_be_referenced = (
                acquire != 'placeholder'
                and asset_exists
                and status
                in {
                    'existing',
                    'generated',
                    'sourced',
                    'rendered',
                    'needs-manual',
                }
            )
            if should_be_referenced and not (actual_paths & expected_paths):
                self._illustration_issues.append((
                    'error',
                    'locked_image_unreferenced',
                    f"{filename} has usable terminal content but its locked "
                    "file is not referenced by any svg_output <image> element.",
                ))

            effective_no_crop = (
                crop_policy == 'no-crop'
                or acquire == 'formula'
                or any(entry.get('crop') == 'no-crop' for entry in entries)
            )
            if effective_no_crop:
                placements_by_svg: Dict[
                    Path,
                    List[Tuple[str, Tuple[str, ...]]],
                ] = defaultdict(list)
                for svg_path, raw_aspect, mechanisms in image_placements.get(
                    filename,
                    [],
                ):
                    placements_by_svg[svg_path].append((
                        raw_aspect,
                        mechanisms,
                    ))

                for svg_path, placements in placements_by_svg.items():
                    parsed_placements = []
                    for raw_aspect, mechanisms in placements:
                        try:
                            align, mode = (
                                _parse_project_image_aspect_ratio(raw_aspect or None)
                                if _parse_project_image_aspect_ratio is not None
                                else ('', '')
                            )
                        except ValueError:
                            # The per-SVG aspect-ratio validator owns malformed syntax.
                            continue
                        parsed_placements.append((
                            raw_aspect,
                            mechanisms,
                            align,
                            mode,
                        ))

                    has_complete_placement = any(
                        align != 'none'
                        and mode == 'meet'
                        and not mechanisms
                        for _raw_aspect, mechanisms, align, mode
                        in parsed_placements
                    )

                    for raw_aspect, _mechanisms, align, _mode in parsed_placements:
                        if align != 'none':
                            continue
                        actual = raw_aspect or '(implicit xMidYMid meet)'
                        self._illustration_issues.append((
                            'error',
                            'no_crop_image_fit_mismatch',
                            f"{svg_path.name}: {filename} is no-crop but its "
                            f"rendered placement uses "
                            f"preserveAspectRatio={actual!r}; stretching is not "
                            "a detail crop and remains forbidden.",
                        ))

                    if has_complete_placement:
                        continue

                    for raw_aspect, mechanisms, align, mode in parsed_placements:
                        if align != 'none' and mode != 'meet':
                            actual = raw_aspect or '(implicit xMidYMid meet)'
                            self._illustration_issues.append((
                                'error',
                                'no_crop_image_fit_mismatch',
                                f"{svg_path.name}: {filename} is no-crop but "
                                "this page has no complete placement and uses "
                                f"preserveAspectRatio={actual!r}; keep at least "
                                "one unclipped placement with a legal alignment "
                                "anchor and meet.",
                            ))
                        if mechanisms:
                            self._illustration_issues.append((
                                'error',
                                'no_crop_image_clipped',
                                f"{svg_path.name}: {filename} is no-crop but "
                                "this page has no complete placement; its "
                                "rendered placement is affected by "
                                f"{', '.join(mechanisms)}. Keep at least one "
                                "unclipped meet placement so every source pixel "
                                "remains visible.",
                            ))

        self._check_sourced_image_provenance(
            rows_by_filename,
            project_path,
        )

    def _check_sourced_image_provenance(
        self,
        rows_by_filename: Dict[str, Dict[str, str]],
        project_path: Path,
    ) -> None:
        """Require one valid provenance item for every Sourced web row."""
        sourced = {
            filename: row
            for filename, row in rows_by_filename.items()
            if self._row_acquire(row) == 'web'
            and self._row_status(row) == 'sourced'
        }
        if not sourced:
            return

        manifest_path = project_path / 'images' / 'image_sources.json'
        if not manifest_path.exists():
            self._illustration_issues.append((
                'error',
                'image_sources_missing',
                "Sourced web images are used, but "
                "images/image_sources.json does not exist.",
            ))
            return

        payload, error = self._read_image_sources_manifest(manifest_path)
        if error:
            if manifest_path not in self._source_manifest_errors_reported:
                self._illustration_issues.append((
                    'error',
                    'image_sources_invalid',
                    error,
                ))
                self._source_manifest_errors_reported.add(manifest_path)
            return

        manifest_items = {
            str(item.get('filename') or ''): item
            for item in payload['items']
            if item.get('filename')
        }
        valid_tiers = {
            'no-attribution',
            'attribution-required',
            'manual',
        }
        for filename in sourced:
            item = manifest_items.get(filename)
            if item is None:
                self._illustration_issues.append((
                    'error',
                    'sourced_image_missing_provenance',
                    f"{filename} is Sourced but has no matching entry in "
                    "images/image_sources.json.",
                ))
                continue

            tier = str(item.get('license_tier') or '').strip()
            if tier not in valid_tiers:
                self._illustration_issues.append((
                    'error',
                    'sourced_image_invalid_license_tier',
                    f"{filename} has invalid license_tier {tier!r} in "
                    "images/image_sources.json.",
                ))
            if tier != 'manual' and not str(
                item.get('attribution_text') or ''
            ).strip():
                self._illustration_issues.append((
                    'error',
                    'sourced_image_missing_attribution_text',
                    f"{filename} has license_tier {tier!r} but no "
                    "attribution_text in images/image_sources.json.",
                ))
            if tier == 'attribution-required' and not str(
                item.get('author') or ''
            ).strip():
                self._illustration_issues.append((
                    'error',
                    'sourced_image_missing_author',
                    f"{filename} requires attribution but has no author in "
                    "images/image_sources.json.",
                ))

    def _check_animation_config_contract(self, dir_path: Path) -> None:
        """Project-level animations.json reference checks."""
        project_path = self._resolve_project_path(dir_path)
        config_path = project_path / 'animations.json'
        if (
            _load_animation_config is None
            or _validate_animation_config is None
            or _validate_animation_config_errors is None
            or _validate_transition_config is None
        ):
            if config_path.is_file():
                detail = _animation_config_import_error or 'unknown import error'
                self._animation_issues.append((
                    'error',
                    f'animations.json validation is unavailable: {detail}',
                ))
            return
        try:
            config = _load_animation_config(project_path)
        except Exception as exc:
            self._animation_issues.append(('error', f"animations.json is invalid: {exc}"))
            return
        if not config:
            return
        fatal_errors = list(dict.fromkeys(
            _validate_transition_config(config)
            + _validate_animation_config_errors(config)
        ))
        for error in fatal_errors:
            self._animation_issues.append(('error', error))
        for message in _validate_animation_config(project_path, config):
            severity = (
                'warning'
                if ' has no id and cannot be customized in animations.json' in message
                else 'error'
            )
            self._animation_issues.append((severity, message))

    def _check_template_contract(
        self,
        dir_path: Path,
        svg_files: List[Path],
        *,
        check_structure: bool,
    ) -> None:
        """Check reusable-template structure, roster, and placeholder hints.

        - **Roster mismatch (orphan / missing)** is reported as an *error*: a
          stale roster will produce a wrong ``layouts_index.json`` entry.
        - **Explicit structure gaps** are errors when positive structure checks
          are enabled: every current reusable SVG declares its Master and Layout
          identity. Zero-placeholder Layouts are valid. Legacy template-mode
          packages fail and must be replaced by a new create-template workspace.
        - **Placeholder gaps** are reported as *warnings*. Templates may
          legitimately omit conventional placeholders or swap them out (e.g.
          ``{{CLOSING_MESSAGE}}`` instead of ``{{THANK_YOU}}``), and a content
          variant may use a bespoke slot vocabulary. Designers can declare
          their own per-stem expectations via ``placeholders:`` frontmatter
          in ``design_spec.md`` to suppress these warnings explicitly.

        Issues are aggregated and printed in :py:meth:`print_summary` so the
        per-file report stays focused on intrinsic SVG validity.
        """
        spec_path = dir_path / 'design_spec.md'
        spec_text = spec_path.read_text(encoding='utf-8') if spec_path.exists() else ""
        declared_structure_mode = _declared_template_structure_mode(dir_path)
        mode_error_recorded = False
        if declared_structure_mode != 'structured':
            mode_error_recorded = True
            self._template_issues.append((
                'error',
                'explicit_structure_mode',
                "design_spec.md frontmatter must declare "
                "native_structure_mode: structured; legacy template-mode "
                "workspaces must be re-created through create-template",
            ))
        if check_structure:
            native_contract_path = dir_path / 'native_structure.json'
            source_template_path = dir_path / 'source_template.pptx'
            legacy_structure_detected = False
            for svg_file in svg_files:
                try:
                    root = ET.parse(svg_file).getroot()
                except (OSError, ET.ParseError):
                    continue
                if not root.get('data-pptx-master'):
                    legacy_structure_detected = True
                    self._template_issues.append((
                        'error',
                        'explicit_master_missing',
                        f"{svg_file.name}: reusable templates require root "
                        "data-pptx-master metadata",
                    ))
                if not root.get('data-pptx-master-name'):
                    legacy_structure_detected = True
                    self._template_issues.append((
                        'error',
                        'explicit_master_name_missing',
                        f"{svg_file.name}: reusable templates require root "
                        "data-pptx-master-name metadata",
                    ))
                if not root.get('data-pptx-layout'):
                    self._template_issues.append((
                        'error',
                        'explicit_structure_missing',
                        f"{svg_file.name}: reusable templates require root "
                        "data-pptx-layout metadata",
                    ))
                if not root.get('data-pptx-layout-name'):
                    self._template_issues.append((
                        'error',
                        'explicit_structure_name_missing',
                        f"{svg_file.name}: reusable templates require root "
                        "data-pptx-layout-name metadata",
                    ))
                if root.get('data-pptx-layout-kind') is not None:
                    legacy_structure_detected = True
                    self._template_issues.append((
                        'error',
                        'deck_instance_layout_kind',
                        f"{svg_file.name}: reusable template prototypes must omit "
                        "legacy data-pptx-layout-kind metadata",
                    ))
                if any(
                    child.get('data-pptx-placeholder') is not None
                    and child.tag.rsplit('}', 1)[-1] != 'g'
                    for child in list(root)
                ):
                    legacy_structure_detected = True
                missing_bounds = [
                    child.get('id') or child.tag.rsplit('}', 1)[-1]
                    for child in list(root)
                    if child.get('data-pptx-placeholder') is not None
                    and child.get('data-pptx-bounds') is None
                ]
                if missing_bounds:
                    legacy_structure_detected = True
                    self._template_issues.append((
                        'error',
                        'placeholder_bounds_missing',
                        f"{svg_file.name}: reusable templates require "
                        "explicit design-zone data-pptx-bounds; missing: "
                        + ', '.join(missing_bounds),
                    ))
            if native_contract_path.exists() or source_template_path.exists():
                legacy_structure_detected = True
                self._template_issues.append((
                    'error',
                    'legacy_native_structure_pair',
                    "legacy native_structure.json/source_template.pptx template "
                    "contracts must be replaced through "
                    "skills/ppt-master/workflows/create-template.md",
                ))

            if declared_structure_mode != 'structured':
                legacy_structure_detected = True
                if not mode_error_recorded:
                    self._template_issues.append((
                        'error',
                        'explicit_structure_mode',
                        "design_spec.md frontmatter must declare "
                        "native_structure_mode: structured",
                    ))
            if legacy_structure_detected:
                self._template_issues.append((
                    'error',
                    'legacy_structure_contract',
                    "legacy template structure detected; create a new current "
                    "workspace through skills/ppt-master/workflows/"
                    "create-template.md before Step 3 consumption",
                ))
        spec_pages = self._extract_spec_roster(spec_text) if spec_text else []
        custom_contract = self._extract_frontmatter_placeholders(spec_text) if spec_text else {}

        on_disk = {p.stem for p in svg_files}

        if spec_pages:
            spec_set = set(spec_pages)
            orphan = sorted(on_disk - spec_set)
            missing = sorted(spec_set - on_disk)
            for page in orphan:
                self._template_issues.append((
                    'error',
                    'roster_orphan',
                    f"{page}.svg exists on disk but is not listed in design_spec.md Page Roster",
                ))
            for page in missing:
                self._template_issues.append((
                    'error',
                    'roster_missing',
                    f"design_spec.md Page Roster lists {page} but {page}.svg is missing on disk",
                ))
        elif spec_path.exists():
            # design_spec.md is present but the roster parser found nothing —
            # reusable template workspaces always fail closed.
            self._template_issues.append((
                'error',
                'roster_unknown',
                f"could not extract page roster from {spec_path.name}; "
                "skipping orphan/missing checks",
            ))
        else:
            self._template_issues.append((
                'error',
                'spec_missing',
                f"{spec_path.name} not found — required for every library template",
            ))

        # Per-file placeholder coverage. Variants reuse the parent type's set
        # (e.g. 03a_content_two_col.svg ↔ 03_content rules) unless the spec
        # frontmatter overrides that page (custom_contract takes precedence).
        for svg_file in svg_files:
            expected = self._lookup_template_contract(
                svg_file.stem, overrides=custom_contract,
            )
            if expected is None:
                continue  # extension pages or stems with no convention
            try:
                content = svg_file.read_text(encoding='utf-8')
            except OSError:
                continue
            for placeholder in expected:
                if placeholder not in content:
                    self._template_issues.append((
                        'warning',
                        'placeholder_hint',
                        f"{svg_file.name}: missing conventional placeholder {placeholder} "
                        "(declare 'placeholders:' frontmatter in design_spec.md to silence)",
                    ))

    @staticmethod
    def _extract_frontmatter_placeholders(spec_text: str) -> Dict[str, Tuple[str, ...]]:
        """Read the optional ``placeholders:`` map from design_spec.md frontmatter.

        Shape:

        .. code-block:: yaml

            placeholders:
              01_cover: ["{{TITLE}}", "{{BRAND_LOGO}}"]
              03_content: []        # explicitly assert "no expectation"
              03a_content_two_col:  # variant-specific override
                - "{{LEFT_TITLE}}"
                - "{{RIGHT_TITLE}}"

        Each key is a stem (full filename without ``.svg``) or page-type prefix
        (``01_cover``). An empty list silences the default convention for that
        stem; a populated list replaces the default. Stems / prefixes not
        listed fall back to ``DEFAULT_PLACEHOLDER_CONVENTION``.

        We parse with PyYAML when available; otherwise we fall back to a
        minimal regex that handles the documented shape.
        """
        if not spec_text.startswith("---\n"):
            return {}
        end = spec_text.find("\n---\n", 4)
        if end == -1:
            return {}
        block = spec_text[4:end]

        try:
            import yaml  # type: ignore
        except ImportError:
            return _parse_placeholders_fallback(block)

        try:
            data = yaml.safe_load(block) or {}
        except yaml.YAMLError:
            return {}
        if not isinstance(data, dict):
            return {}
        raw = data.get("placeholders")
        if not isinstance(raw, dict):
            return {}

        out: Dict[str, Tuple[str, ...]] = {}
        for stem, value in raw.items():
            if not isinstance(stem, str):
                continue
            if isinstance(value, list):
                out[stem] = tuple(str(v) for v in value)
            elif value is None:
                out[stem] = ()
        return out

    @staticmethod
    def _extract_spec_roster(spec_text: str) -> List[str]:
        """Best-effort: extract the page roster from design_spec.md.

        Templates do not share a uniform section index for the roster — the
        personality-only skeleton puts it at §V "Page Roster"; legacy specs use
        §VI "Page Roster" or bury filenames under §VII "Page Types" as
        ``### N. Cover Page (01_cover.svg)``. We match by title (any roman
        index), then fall back to scanning the whole document for any
        backtick-wrapped ``<stem>.svg`` reference.

        Returns the deduplicated stem list in document order. Empty result
        means we can't determine the roster confidently — caller should treat
        that as "skip orphan/missing checks", not as "no pages declared".
        """
        # Pass 1: explicit roster section, any roman numeral.
        sections = list(re.finditer(
            r"^##\s+[IVX]+\.\s+(?:(?:SVG\s+)?Page Roster|Page Structure|Pages|Page Types)\b.*?(?=^##\s+|\Z)",
            spec_text,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        ))
        roster_scope = next(
            (
                section.group(0)
                for section in sections
                if re.match(
                    r"^##\s+[IVX]+\.\s+(?:SVG\s+)?Page Roster\b",
                    section.group(0),
                    re.IGNORECASE,
                )
            ),
            None,
        )
        scope = roster_scope or next(
            (
                section.group(0)
                for section in sections
                if re.search(r"[`\(][0-9A-Za-z_]+\.svg[`\)]", section.group(0))
            ),
            sections[0].group(0) if sections else None,
        )

        # Pass 2: full document. We *only* trust this scan when the explicit
        # roster scan came up empty (no `<stem>.svg` references inside it) —
        # otherwise the explicit section's deliberate roster wins over loose
        # mentions elsewhere.
        explicit_scope = bool(
            scope and re.search(r"[`\(][0-9A-Za-z_]+\.svg[`\)]", scope)
        )
        if explicit_scope:
            text = scope
        else:
            text = spec_text

        stems: List[str] = []
        seen: set = set()
        # Accept backtick-quoted (`01_cover.svg`) and parenthesized
        # (01_cover.svg) forms — existing specs use either.
        svg_ref_re = re.compile(r"[`\(]([0-9A-Za-z_]+\.svg)[`\)]")
        for match in svg_ref_re.finditer(text):
            stem = match.group(1)[:-4]
            if stem in seen or (not explicit_scope and not re.match(r"^\d", stem)):
                continue
            seen.add(stem)
            stems.append(stem)

        # If the explicit §VI scan listed bare stems (without .svg), accept
        # those as fallback — but only when they were inside that section.
        if not stems and scope:
            for match in re.finditer(r"`([0-9]{2}[a-z]?_[A-Za-z0-9_]+)`", scope):
                stem = match.group(1)
                if stem in seen:
                    continue
                seen.add(stem)
                stems.append(stem)

        return stems

    @classmethod
    def _lookup_template_contract(
        cls, stem: str, *,
        overrides: Dict[str, Tuple[str, ...]] | None = None,
    ) -> Tuple[str, ...] | None:
        """Resolve a SVG stem to its expected placeholder set.

        Resolution order, first hit wins:
        1. ``overrides[stem]`` — frontmatter entry for the exact filename
        2. ``overrides[<page_type_prefix>]`` — frontmatter entry for the
           variant's parent type (e.g. ``03_content`` for
           ``03a_content_two_col``)
        3. ``DEFAULT_PLACEHOLDER_CONVENTION[<page_type>]`` — keyed by the
           type token alone, so it applies regardless of where the type
           lands in the template's presentation-order numbering

        Returns ``None`` for stems with no matching convention or override —
        e.g. extension pages like ``05_section_break``. ``()`` (empty tuple)
        is a valid value meaning "no expected placeholders" — used to
        explicitly silence the default convention.
        """
        overrides = overrides or {}
        if stem in overrides:
            return overrides[stem]

        # Variant convention: <NN><letter>?_<rest>; strip the letter to find
        # the parent type prefix, e.g. "03a_content_two_col" -> "03_content".
        match = re.match(r"^(\d{2})([a-z])?_([a-z]+)", stem)
        if not match:
            return None
        num, _letter, kind = match.groups()
        key = f"{num}_{kind}"
        if key in overrides:
            return overrides[key]
        return cls.DEFAULT_PLACEHOLDER_CONVENTION.get(kind)

    def _print_result(self, result: Dict):
        """Print check result for a single file"""
        if result['passed']:
            if result['warnings']:
                icon = "[WARN]"
                status = "Passed (with warnings)"
            else:
                icon = "[OK]"
                status = "Passed"
        else:
            icon = "[ERROR]"
            status = "Failed"

        print(f"{icon} {result['file']} - {status}")

        # Display basic info
        if result['info']:
            info_items = []
            if 'viewbox' in result['info']:
                info_items.append(f"viewBox: {result['info']['viewbox']}")
            if info_items:
                print(f"   {' | '.join(info_items)}")

        # Display errors
        if result['errors']:
            for error in result['errors']:
                print(f"   [ERROR] {error}")

        # Display the complete warning set from this run. The generation
        # workflow reviews all findings before one consolidated repair pass.
        if result['warnings']:
            for warning in result['warnings']:
                print(f"   [WARN] {warning}")

        print()

    def print_summary(self):
        """Print check summary"""
        self._apply_aggregated_issue_counts()

        print("=" * 80)
        print("[SUMMARY] Check Summary")
        print("=" * 80)

        print(f"\nTotal files: {self.summary['total']}")
        print(
            f"  [OK] Fully passed: {self.summary['passed']} ({self._percentage(self.summary['passed'])}%)")
        print(
            f"  [WARN] With warnings: {self.summary['warnings']} ({self._percentage(self.summary['warnings'])}%)")
        print(
            f"  [ERROR] With errors: {self.summary['errors']} ({self._percentage(self.summary['errors'])}%)")

        self._print_provenance_category_summary()

        if self.issue_types:
            print(f"\nIssue categories:")
            for issue_type, count in sorted(self.issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue_type}: {count}")

        # spec_lock anchor comparison (only printed when a lock was found)
        self._print_anchor_value_summary()

        # Template-mode aggregation (orphan/missing roster + placeholder hints)
        self._print_template_summary()

        # Animation config aggregation.
        self._print_animation_summary()

        # Illustration strategy aggregation.
        self._print_illustration_summary()

        # Communication contract and per-page audience movement.
        self._print_communication_trace_summary()

        # Explicit PowerPoint master/layout structure aggregation.
        self._print_pptx_structure_summary()

        # Source-owned import recovery belongs to the template, not this run.
        self._print_source_import_summary()

        # Fix suggestions
        if self.summary['errors'] > 0 or self.summary['warnings'] > 0:
            print(f"\n[TIP] Common fixes:")
            print(f"  1. XML well-formedness: write typography as raw Unicode (—, ©, →, NBSP); escape XML reserved chars as &amp; &lt; &gt; &quot; &apos; — never use HTML named entities like &nbsp; &mdash; &copy;")
            print(f"  2. viewBox issues: root viewBox is the canvas authority (see references/canvas-formats.md)")
            print(
                "  3. Paint recommendation: generated SVG prefers uppercase "
                "#RRGGBB plus channel-specific opacity; compatible alternatives "
                "remain non-blocking"
            )
            print(f"  4. foreignObject: Use <text> + <tspan> for manual line breaks")
            print(f"  5. Font issues: use PPT-safe exported typefaces (e.g. Microsoft YaHei / Arial / Consolas)")

    def _print_provenance_category_summary(self):
        """Print compact JSON-equivalent counts for token-safe gate handling."""
        categories = self._provenance_categories()
        rows = (
            (
                'blocking',
                len(categories['blocking']),
                'hard findings; gate also requires exit 0',
            ),
            (
                'introduced',
                len(categories['introduced']),
                'advisory; new or changed',
            ),
            (
                'inherited',
                len(categories['inherited']),
                'informational; prototype-identical',
            ),
            (
                'source-import',
                _source_import_warning_count(categories['source_import']),
                'informational; source-conversion loss',
            ),
        )

        print("\nProvenance categories:")
        for name, count, note in rows:
            print(f"  {f'{name}: {count}':<20} {note}")

    def _print_animation_summary(self):
        """Print animations.json validation issues if present."""
        if not self._animation_issues:
            return

        errors = [item for item in self._animation_issues if item[0] == 'error']
        warnings = [item for item in self._animation_issues if item[0] == 'warning']

        print("\n[ANIMATION] animations.json checks")
        for _severity, msg in errors:
            print(f"  [ERROR] {msg}")
        for _severity, msg in warnings:
            print(f"  [WARN] {msg}")

    def _print_illustration_summary(self):
        """Print project-level illustration strategy issues if present."""
        if not self._illustration_issues:
            return

        errors = [item for item in self._illustration_issues if item[0] == 'error']
        warnings = [item for item in self._illustration_issues if item[0] == 'warning']

        print("\n[IMAGES] Image resource checks")
        if errors:
            print(f"  Errors ({len(errors)}):")
            for _severity, kind, msg in errors:
                print(f"    [{kind}] {msg}")
        if warnings:
            print(f"  Warnings ({len(warnings)}):")
            for _severity, kind, msg in warnings:
                print(f"    [{kind}] {msg}")

    def _print_pptx_structure_summary(self):
        """Print project-level PowerPoint structure contract issues."""
        if not self._pptx_structure_issues:
            return
        print("\n[PPTX STRUCTURE] Master/layout contract checks")
        for severity, message in self._pptx_structure_issues:
            print(f"  [{severity.upper()}] {message}")

    def _print_communication_trace_summary(self):
        """Print project-level communication trace issues."""
        if not self._communication_trace_issues:
            return
        print("\n[COMMUNICATION TRACE] Contract and Audience move checks")
        for severity, message in self._communication_trace_issues:
            print(f"  [{severity.upper()}] {message}")

    def _print_source_import_summary(self):
        """Print source-owned tolerant-import diagnostics as information."""
        warning_count = _source_import_warning_count(
            self._source_import_summary
        )
        if warning_count <= 0:
            return
        print("\n[SOURCE IMPORT] Template-owned compatibility diagnostics")
        print(
            f"  [INFO] {warning_count} source-import warning(s); unchanged "
            "template recovery is not attributed to generated content."
        )
        by_code = self._source_import_summary.get('by_code')
        if isinstance(by_code, dict):
            for code, count in sorted(by_code.items()):
                print(f"    {code}: {count}")

    def _print_template_summary(self):
        """Aggregate template-mode roster / placeholder issues at the bottom.

        Errors land under the ``errors`` summary count (so the exit signal
        from ``main`` agrees), warnings under ``warnings``. Both are listed
        per file so the user can act on them directly.
        """
        if not self._template_issues and self._spec_only_template_kind is None:
            return

        errors = [item for item in self._template_issues if item[0] == 'error']
        warnings = [item for item in self._template_issues if item[0] == 'warning']

        print("\n[TEMPLATE] Template mode checks")
        if errors:
            print(f"  Errors ({len(errors)}):")
            for _sev, kind, msg in errors:
                print(f"    [{kind}] {msg}")
        if warnings:
            print(f"  Warnings ({len(warnings)}):")
            for _sev, kind, msg in warnings:
                print(f"    [{kind}] {msg}")
        if self._spec_only_template_kind is not None and not errors:
            pretty_kind = self._spec_only_template_kind.title()
            print(f"  {pretty_kind} design_spec.md contract passed.")
        if not errors:
            if self._spec_only_template_kind is None:
                print("  No structural roster issues.")
                print("  Conventional placeholder-name hints may be declared through "
                      "'placeholders:' frontmatter. Placeholder bounds are mandatory "
                      "design-zone metadata.")

    def _apply_aggregated_issue_counts(self):
        """Mirror project-level aggregate issues into summary counters once."""
        if self._aggregate_counts_applied:
            return
        self._aggregate_counts_applied = True

        animation_errors = [item for item in self._animation_issues if item[0] == 'error']
        animation_warnings = [item for item in self._animation_issues if item[0] == 'warning']
        self.summary['errors'] += len(animation_errors)
        self.summary['warnings'] += len(animation_warnings)
        for severity, _msg in self._animation_issues:
            self.issue_types[f'animation_config_{severity}'] += 1

        template_errors = [item for item in self._template_issues if item[0] == 'error']
        template_warnings = [item for item in self._template_issues if item[0] == 'warning']
        self.summary['errors'] += len(template_errors)
        self.summary['warnings'] += len(template_warnings)
        for severity, kind, _msg in self._template_issues:
            self.issue_types[f'template_{kind}_{severity}'] += 1

        illustration_errors = [item for item in self._illustration_issues if item[0] == 'error']
        illustration_warnings = [item for item in self._illustration_issues if item[0] == 'warning']
        self.summary['errors'] += len(illustration_errors)
        self.summary['warnings'] += len(illustration_warnings)
        for severity, kind, _msg in self._illustration_issues:
            self.issue_types[f'illustration_{kind}_{severity}'] += 1

        communication_errors = [
            item for item in self._communication_trace_issues
            if item[0] == 'error'
        ]
        communication_warnings = [
            item for item in self._communication_trace_issues
            if item[0] == 'warning'
        ]
        self.summary['errors'] += len(communication_errors)
        self.summary['warnings'] += len(communication_warnings)
        for severity, _msg in self._communication_trace_issues:
            self.issue_types[f'communication_trace_{severity}'] += 1

        structure_errors = [item for item in self._pptx_structure_issues if item[0] == 'error']
        structure_warnings = [item for item in self._pptx_structure_issues if item[0] == 'warning']
        self.summary['errors'] += len(structure_errors)
        self.summary['warnings'] += len(structure_warnings)
        for severity, _msg in self._pptx_structure_issues:
            self.issue_types[f'pptx_structure_{severity}'] += 1

    def _print_anchor_value_summary(self):
        """Print anchor comparisons without treating contextual paint/type as drift."""
        if not self._lock_seen:
            return
        has_contextual = any(
            self._anchor_value_summary[category]
            for category in ('colors', 'fonts')
        )
        has_undeclared_sizes = bool(self._anchor_value_summary['sizes'])
        if not has_contextual and not has_undeclared_sizes:
            print(
                "\n[OK] spec_lock anchor comparison: no additional contextual "
                "colors/fonts or out-of-band font sizes"
            )
            return

        if has_contextual:
            print("\nContextual values beyond spec_lock anchors (informational):")
            for category, label in (
                ('colors', 'Colors'),
                ('fonts', 'Font families'),
            ):
                items = self._anchor_value_summary.get(category, {})
                if not items:
                    continue
                entries = sorted(
                    items.items(), key=lambda item: (-len(item[1]), item[0])
                )
                print(f"  {label}:")
                for val, files in entries:
                    count = len(files)
                    suffix = "file" if count == 1 else "files"
                    print(f"    {val}  ({count} {suffix})")
            print(
                "Note: contextual page paint, gradient/effect colors, and "
                "export-safe typefaces are allowed.\n"
                "      Add a spec_lock row only when a value becomes a "
                "recurring named semantic role."
            )

        if has_undeclared_sizes:
            print(
                "\nTypography sizes outside every declared role anchor ±2px "
                "(up to 2 occurrences are sparse; the 3rd is recurring):"
            )
            entries = sorted(
                self._anchor_value_summary['sizes'].items(),
                key=lambda item: (-len(item[1]), item[0]),
            )
            for val, files in entries:
                occurrences = self._undeclared_size_occurrences.get(
                    val,
                    len(files),
                )
                file_count = len(files)
                file_suffix = "file" if file_count == 1 else "files"
                policy = (
                    "sparse"
                    if occurrences <= SPARSE_UNDECLARED_FONT_SIZE_MAX_OCCURRENCES
                    else "recurring — declare a role"
                )
                print(
                    f"  {val}  ({occurrences} occurrences in {file_count} "
                    f"{file_suffix}; {policy})"
                )

    def _percentage(self, count: int) -> int:
        """Calculate percentage"""
        if self.summary['total'] == 0:
            return 0
        return min(100, int(count / self.summary['total'] * 100))

    def export_report(self, output_file: str = 'svg_quality_report.txt'):
        """Export check report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PPT Master SVG Quality Check Report\n")
            f.write("=" * 80 + "\n\n")

            for result in self.results:
                status = "[OK] Passed" if result['passed'] else "[ERROR] Failed"
                f.write(f"{status} - {result['file']}\n")
                f.write(f"Path: {result.get('path', 'N/A')}\n")

                if result['info']:
                    f.write(f"Info: {result['info']}\n")

                if result['errors']:
                    f.write(f"\nErrors:\n")
                    for error in result['errors']:
                        f.write(f"  - {error}\n")

                if result['warnings']:
                    f.write(f"\nWarnings:\n")
                    for warning in result['warnings']:
                        f.write(f"  - {warning}\n")

                f.write("\n" + "-" * 80 + "\n\n")

            # Write summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("Check Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total files: {self.summary['total']}\n")
            f.write(f"Fully passed: {self.summary['passed']}\n")
            f.write(f"With warnings: {self.summary['warnings']}\n")
            f.write(f"With errors: {self.summary['errors']}\n")

        print(f"\n[REPORT] Check report exported: {output_file}")

    def _provenance_categories(self) -> Dict[str, object]:
        """Classify every issue by provenance.

        Single source for the JSON report's ``categories`` block and the
        terminal summary, so the console and the report never disagree about
        what blocks a release export.
        """
        self._apply_aggregated_issue_counts()
        introduced: List[Dict[str, str]] = []
        blocking: List[Dict[str, str]] = []
        inherited: List[Dict[str, str]] = []
        for result in self.results:
            filename = str(result.get('file') or '')
            introduced.extend({
                'file': filename,
                'message': warning,
            } for warning in result.get('warnings', []))
            blocking.extend({
                'file': filename,
                'message': error,
            } for error in result.get('errors', []))
            info = result.get('info') or {}
            for item in info.get('inherited', []):
                if isinstance(item, dict):
                    inherited.append({
                        'file': filename,
                        'kind': str(item.get('kind') or 'prototype'),
                        'message': str(item.get('message') or ''),
                    })

        project_issues = {
            'template': [
                {'severity': severity, 'kind': kind, 'message': message}
                for severity, kind, message in self._template_issues
            ],
            'animation': [
                {'severity': severity, 'message': message}
                for severity, message in self._animation_issues
            ],
            'illustration': [
                {'severity': severity, 'kind': kind, 'message': message}
                for severity, kind, message in self._illustration_issues
            ],
            'communication_trace': [
                {'severity': severity, 'message': message}
                for severity, message in self._communication_trace_issues
            ],
            'pptx_structure': [
                {'severity': severity, 'message': message}
                for severity, message in self._pptx_structure_issues
            ],
        }
        for group, issues in project_issues.items():
            for issue in issues:
                item = {
                    'scope': group,
                    'message': issue['message'],
                }
                if issue['severity'] == 'error':
                    blocking.append(item)
                else:
                    introduced.append(item)

        return {
            'blocking': blocking,
            'introduced': introduced,
            'inherited': inherited,
            'project_issues': project_issues,
            'source_import': dict(self._source_import_summary),
        }

    def export_json_report(
        self,
        output_file: str,
        *,
        target: str,
        stage: str,
    ) -> None:
        """Write a machine-readable quality report with provenance classes."""
        categories = self._provenance_categories()
        blocking = categories['blocking']
        introduced = categories['introduced']
        inherited = categories['inherited']
        project_issues = categories['project_issues']

        # Keep the legacy `drift` JSON field for report compatibility. Its
        # colors/fonts entries are informational anchor comparisons; sparse
        # size entries are informational until their third occurrence.
        drift = {
            category: {
                value: sorted(files)
                for value, files in sorted(values.items())
            }
            for category, values in self._anchor_value_summary.items()
        }
        source_import = categories['source_import']
        payload = {
            'schema': 'ppt-master.svg-quality-report.v1',
            'stage': stage,
            'target': str(Path(target).resolve()),
            'source_fingerprint': _quality_source_fingerprint(self.results),
            'summary': dict(self.summary),
            'issue_types': dict(sorted(self.issue_types.items())),
            'categories': {
                'blocking': {
                    'count': len(blocking),
                    'issues': blocking,
                },
                'introduced': {
                    'count': len(introduced),
                    'issues': introduced,
                },
                'inherited': {
                    'count': len(inherited),
                    'issues': inherited,
                },
                'source-import': {
                    'count': _source_import_warning_count(source_import),
                    'summary': source_import,
                },
            },
            'drift': drift,
            'project_issues': project_issues,
            'files': self.results,
        }
        report_path = Path(output_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        print(f"\n[REPORT] JSON quality report exported: {report_path}")


def _source_import_warning_count(summary: Dict[str, object]) -> int:
    """Return only a schema-compatible non-negative warning count."""
    value = summary.get('warning_count')
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _quality_source_fingerprint(results: List[Dict]) -> Dict[str, object]:
    """Bind a quality report to the exact SVG bytes that were checked."""
    files: List[Dict[str, object]] = []
    aggregate = hashlib.sha256()
    candidates = sorted(
        (
            result
            for result in results
            if result.get('exists') and result.get('path')
        ),
        key=lambda result: Path(str(result['path'])).name,
    )
    for result in candidates:
        path = Path(str(result['path']))
        file_sha256 = result.get('source_sha256')
        if not isinstance(file_sha256, str):
            files.append({
                'file': path.name,
                'sha256': None,
                'error': 'source bytes were not available during validation',
            })
            file_sha256 = 'unreadable'
        else:
            files.append({'file': path.name, 'sha256': file_sha256})
        aggregate.update(path.name.encode('utf-8'))
        aggregate.update(b'\0')
        aggregate.update(file_sha256.encode('ascii'))
        aggregate.update(b'\n')
    return {
        'algorithm': 'sha256',
        'digest': aggregate.hexdigest(),
        'file_count': len(files),
        'files': files,
    }
