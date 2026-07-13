#!/usr/bin/env python3
"""
PPT Master - SVG Quality Check Tool

Checks whether SVG files comply with project technical specifications.

Usage:
    python3 scripts/svg_quality_checker.py <svg_file>
    python3 scripts/svg_quality_checker.py <directory>
    python3 scripts/svg_quality_checker.py --all examples
"""

import copy
import sys
import re
import json
import html
import math
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

try:
    from project_utils import CANVAS_FORMATS
except ImportError:
    print("Warning: Unable to import project_utils")
    CANVAS_FORMATS = {}

try:
    from update_spec import parse_lock as _parse_spec_lock
except ImportError:
    _parse_spec_lock = None  # spec_lock drift check will be skipped

try:
    from svg_to_pptx.animation_config import (
        load_animation_config as _load_animation_config,
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
else:
    _animation_config_import_error = None

try:
    from svg_to_pptx.drawingml.utils import (
        IDENTITY_MATRIX as _IDENTITY_MATRIX,
        matrix_multiply as _matrix_multiply,
        parse_transform_matrix as _parse_transform_matrix,
        parse_font_family as _parse_export_font_family,
        parse_inline_style as _parse_inline_style,
        parse_svg_color as _parse_export_color,
        rect_to_dml_xfrm as _rect_to_dml_xfrm,
        validate_dml_shape_matrix as _validate_dml_shape_matrix,
    )
except ImportError:
    _IDENTITY_MATRIX = None
    _matrix_multiply = None
    _parse_transform_matrix = None
    _parse_export_font_family = None
    _parse_inline_style = None
    _parse_export_color = None
    _rect_to_dml_xfrm = None
    _validate_dml_shape_matrix = None

try:
    from svg_to_pptx.drawingml.converter import (
        collect_unsupported_visuals as _collect_unsupported_visuals,
    )
except ImportError:
    _collect_unsupported_visuals = None

try:
    from svg_to_pptx.drawingml.elements import (
        validate_preset_geometry_metadata as _validate_preset_geometry_metadata,
    )
except ImportError:
    _validate_preset_geometry_metadata = None

try:
    from pptx_to_svg.preset_authoring import (
        AUTHORING_ATTR as _AUTHORING_ATTR,
        validate_authored_preset_tree as _validate_authored_preset_tree,
    )
except ImportError:
    _AUTHORING_ATTR = 'data-pptx-authoring'
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
        validate_semantic_markers as _validate_semantic_markers,
    )
except ImportError:
    _SEMANTIC_ATTRS = frozenset({
        'data-pptx-page-role',
        'data-pptx-role',
    })
    _validate_semantic_markers = None

try:
    from svg_to_pptx.geometry_properties import (
        materialize_inline_geometry_properties as _materialize_inline_geometry_properties,
        validate_inline_geometry_properties as _validate_inline_geometry_properties,
    )
except ImportError:
    _materialize_inline_geometry_properties = None
    _validate_inline_geometry_properties = None

try:
    from svg_to_pptx.use_expander import (
        UseExpansionError as _UseExpansionError,
        expand_local_use_references as _expand_local_use_references,
        validate_local_use_references as _validate_local_use_references,
    )
except ImportError:
    _UseExpansionError = None
    _expand_local_use_references = None
    _validate_local_use_references = None

try:
    from svg_to_pptx.pptx_package.template_structure import (
        TemplateStructureError as _TemplateStructureError,
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
    _load_pptx_structure_lock = None
    _parse_template_structure_slide = None
    _parse_template_structure_slides = None
    _structure_subtree_signature = None
    _template_lock_errors = None
    _template_prototype_errors = None
    _validate_template_structure_svg = None

try:
    from svg_finalize.embed_icons import (
        resolve_icon_path as _resolve_icon_path,
    )
except ImportError:
    _resolve_icon_path = None

try:
    from resource_paths import (
        SVG_WORK_DIR_NAMES as _SVG_WORK_DIR_NAMES,
        icon_search_dirs_for_svg as _icon_search_dirs_for_svg,
        project_root_for_svg_path as _project_root_for_svg_path,
        resolve_external_image_reference as _resolve_external_image_reference,
        unresolved_external_image_reference_path as _unresolved_external_image_reference_path,
    )
except ImportError:
    _SVG_WORK_DIR_NAMES = frozenset()
    _icon_search_dirs_for_svg = None
    _project_root_for_svg_path = None
    _resolve_external_image_reference = None
    _unresolved_external_image_reference_path = None


HEX_VALUE_RE = re.compile(
    r"#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})"
)

# Master/Layout preflight validation. Structured deck/layout-template projects
# are checked at authoring time; the exporter remains the final OOXML/package
# authority. Flat projects only receive the negative guard that rejects authored
# structure metadata. Template roster/placeholder checks always run; the legacy
# template structure override stays dormant until the bundled library migrates
# off native_structure_mode: template. Current structured templates opt in via
# their design_spec.md declaration without waiting for that migration.
_CHECK_PPTX_STRUCTURED_PROJECT = True
_CHECK_PPTX_TEMPLATE_MODE = False
# Explicit migration debt: remove each entry after that bundled workspace adopts
# native_structure_mode: structured. New/custom workspaces are never exempt.
_BUNDLED_LEGACY_TEMPLATE_DIRS = frozenset({
    'decks/中国电信/templates',
    'decks/中国电建/templates',
    'decks/中汽研/templates',
    'decks/招商银行/templates',
    'decks/重庆大学/templates',
    'layouts/academic_defense/templates',
    'layouts/ai_ops/templates',
    'layouts/government_blue/templates',
    'layouts/government_red/templates',
    'layouts/medical_university/templates',
    'layouts/pixel_retro/templates',
    'layouts/psychology_attachment/templates',
})

_BARE_HEX_VALUE_RE = re.compile(
    r"(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})"
)
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
_NON_VISUAL_SVG_TAGS = frozenset({
    'defs',
    'desc',
    'metadata',
    'style',
    'title',
})
_PPTX_ROOT_STRUCTURE_ATTRS = (
    'data-pptx-master',
    'data-pptx-master-name',
    'data-pptx-layout',
    'data-pptx-layout-name',
)
_PPTX_STRUCTURE_ATTRS = frozenset({
    *_PPTX_ROOT_STRUCTURE_ATTRS,
    'data-pptx-layer',
    'data-pptx-layout-kind',
    'data-pptx-placeholder',
    'data-pptx-placeholder-binding',
    'data-pptx-placeholder-bounds',
    'data-pptx-placeholder-carrier',
    'data-pptx-placeholder-idx',
})
_PPTX_PLACEHOLDER_DETAIL_ATTRS = frozenset({
    'data-pptx-placeholder-binding',
    'data-pptx-placeholder-bounds',
    'data-pptx-placeholder-idx',
})
_PPTX_STRUCTURE_SECTION_RE = re.compile(
    r"(?ms)^##[ \t]+pptx_structure[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)"
)
_PPTX_STRUCTURE_MODE_RE = re.compile(
    r"(?m)^-[ \t]+mode[ \t]*:[ \t]*([^\s#]+)[ \t]*(?:#.*)?$"
)
_SUPPORTED_FILTER_PRIMITIVES = frozenset({
    'feDropShadow',
    'feGaussianBlur',
    'feOffset',
    'feFlood',
    'feComposite',
    'feMerge',
    'feMergeNode',
    'feComponentTransfer',
    'feFuncA',
})
_FILTER_EFFECT_PRIMITIVES = frozenset({'feDropShadow', 'feGaussianBlur'})


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


def _placeholder_bounds_error(value: str) -> str | None:
    """Return a concise error for invalid design-zone bounds."""
    raw_values = [item for item in re.split(r"[\s,]+", value.strip()) if item]
    if len(raw_values) != 4:
        return "must contain exactly four numbers: x y width height"
    try:
        values = tuple(float(item) for item in raw_values)
    except ValueError:
        return "must contain only numeric values"
    if not all(math.isfinite(item) for item in values):
        return "must contain only finite values"
    if values[2] <= 0 or values[3] <= 0:
        return "must use positive width and height"
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
                attr for attr in _PPTX_ROOT_STRUCTURE_ATTRS
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
            if tag == 'g':
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
            bounds = (elem.get('data-pptx-placeholder-bounds') or '').strip()
            if not bounds:
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} requires "
                    "data-pptx-placeholder-bounds"
                )
            else:
                bounds_error = _placeholder_bounds_error(bounds)
                if bounds_error:
                    errors.append(
                        f"{svg_path.name}: placeholder slot {element_id} bounds "
                        + bounds_error
                    )

            binding = (
                elem.get('data-pptx-placeholder-binding') or 'carrier'
            ).strip().lower()
            if binding not in {'carrier', 'proxy'}:
                errors.append(
                    f"{svg_path.name}: placeholder slot {element_id} has unknown "
                    f"binding {binding!r}; use carrier or proxy"
                )
            carrier_descendants = [
                child for child in elem.iter()
                if child is not elem
                and child.get('data-pptx-placeholder-carrier') is not None
            ]
            visual_children = [
                child for child in list(elem)
                if child.tag.rsplit('}', 1)[-1] not in _NON_VISUAL_SVG_TAGS
            ]
            direct_carriers = [
                child for child in visual_children
                if (child.get('data-pptx-placeholder-carrier') or '').strip().lower()
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
                        "data-pptx-placeholder-carrier=\"true\""
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

        carrier_value = elem.get('data-pptx-placeholder-carrier')
        if carrier_value is not None:
            if carrier_value.strip().lower() != 'true':
                errors.append(
                    f"{svg_path.name}: {element_id} "
                    "data-pptx-placeholder-carrier must equal true"
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


# Fonts that survive direct PPTX typeface assignment on a typical Windows /
# macOS viewer without requiring a custom install. Keep this aligned with
# strategist.md §g and drawingml/utils.py FONT_FALLBACK_WIN.
PPT_SAFE_FONTS = {
    'microsoft yahei', 'simhei', 'simsun', 'kaiti', 'fangsong',
    'dengxian', 'microsoft jhenghei',
    'pingfang sc', 'heiti sc', 'songti sc', 'stsong',
    'arial', 'arial black', 'calibri', 'segoe ui', 'verdana',
    'helvetica', 'helvetica neue', 'tahoma', 'trebuchet ms',
    'times new roman', 'times', 'georgia', 'cambria', 'palatino',
    'garamond', 'book antiqua',
    'consolas', 'courier new', 'menlo', 'monaco',
    'impact',
}

# Ramp envelope for font-size drift detection.
# From design_spec_reference.md §IV — Font Size Hierarchy: the ramp spans
# from page-number floor (0.5x body) to cover-title ceiling (5.0x body).
# Intermediate px values within this envelope are permitted per
# executor-base.md §2.1 ("Executor may use an intermediate size ... provided
# the size's ratio to body falls within the corresponding role's band"); only
# values outside every band — i.e. outside this envelope — are drift.
RAMP_MIN_RATIO = 0.5
RAMP_MAX_RATIO = 5.0

# Modes / visual styles that legitimately use unbounded hero / poster type
# (huge cover numerals, act dividers, single-number reveals). For these the
# size-drift upper bound is dropped — the oversize is the design, not Executor
# drift. The lower bound still applies.
POSTER_SIZE_MODES = {'showcase'}
POSTER_SIZE_STYLES = {'zine'}


def _design_spec_is_brand(spec_path: Path) -> bool:
    """Return True when a design_spec.md frontmatter declares ``kind: brand``.

    Lightweight detector that does not require PyYAML — scans only the
    frontmatter block (``---`` delimited) for a ``kind:`` line whose value
    contains ``brand``. Used by ``check_directory`` to skip SVG validation
    on brand-only template directories.
    """
    try:
        text = spec_path.read_text(encoding='utf-8')
    except OSError:
        return False
    if not text.startswith('---\n'):
        return False
    end = text.find('\n---\n', 4)
    if end == -1:
        return False
    fm_block = text[4:end]
    for line in fm_block.splitlines():
        stripped = line.strip()
        if stripped.startswith('kind:'):
            value = stripped.split(':', 1)[1].strip().strip('"\'')
            return value == 'brand'
    return False


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


def _is_bundled_legacy_template(target_path: Path) -> bool:
    """Return whether a template is in the explicit bundled migration set."""
    directory = target_path.parent if target_path.is_file() else target_path
    library_root = Path(__file__).resolve().parents[1] / 'templates'
    try:
        relative_path = directory.resolve().relative_to(library_root.resolve())
    except ValueError:
        return False
    return relative_path.as_posix() in _BUNDLED_LEGACY_TEMPLATE_DIRS


def _legacy_template_structure_deferred(target_path: Path) -> bool:
    """Return whether a known bundled legacy template may defer structure."""
    return bool(
        not _CHECK_PPTX_TEMPLATE_MODE
        and _declared_template_structure_mode(target_path) == 'template'
        and _is_bundled_legacy_template(target_path)
    )


def _template_structure_checks_enabled(target_path: Path) -> bool:
    """Return whether positive structure checks apply to this template."""
    declared_mode = _declared_template_structure_mode(target_path)
    return bool(
        declared_mode == 'structured'
        or (_CHECK_PPTX_TEMPLATE_MODE and declared_mode == 'template')
    )


def _local_name(elem: ET.Element) -> str:
    """Return an XML element's namespace-free local tag name."""
    tag = elem.tag
    if not isinstance(tag, str):
        return ''
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def _parse_viewbox_values(viewbox: str) -> Tuple[float, float, float, float] | None:
    """Parse a root viewBox into four numeric values."""
    parts = re.split(r'[\s,]+', viewbox.strip())
    if len(parts) != 4:
        return None
    try:
        values = tuple(float(part) for part in parts)
    except ValueError:
        return None
    if values[2] <= 0 or values[3] <= 0:
        return None
    return values


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
    # is matched by the same `03_content` rules as `03_content.svg`).
    DEFAULT_PLACEHOLDER_CONVENTION = {
        "01_cover": ("{{TITLE}}",),  # only the title is universally expected
        "02_chapter": ("{{CHAPTER_TITLE}}",),
        "02_toc": (),  # TOC layouts vary too widely to assert anything
        "03_content": ("{{PAGE_TITLE}}",),
        "04_ending": (),  # ending pages legitimately use varied vocabularies
    }

    def __init__(self, *, template_mode: bool = False):
        self.template_mode = template_mode
        self.results = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0
        }
        self.issue_types = defaultdict(int)
        # spec_lock drift state (populated only when _parse_spec_lock is available
        # and a spec_lock.md is found near the SVG)
        self._lock_cache: Dict[Path, Dict] = {}
        self._drift_summary: Dict[str, Dict[str, set]] = {
            'colors': defaultdict(set),
            'fonts': defaultdict(set),
            'sizes': defaultdict(set),
        }
        self._lock_seen = False  # True once we locate at least one spec_lock.md
        self._source_manifest_cache: Dict[Path, Dict] = {}
        # Template-mode aggregation (populated by check_directory when
        # template_mode=True). Each entry is (severity, kind, message) where
        # severity is 'error' or 'warning'. Printed in print_summary.
        self._template_issues: List[Tuple[str, str, str]] = []
        self._animation_issues: List[Tuple[str, str]] = []
        self._illustration_issues: List[Tuple[str, str, str]] = []
        self._pptx_structure_issues: List[Tuple[str, str]] = []
        self._aggregate_counts_applied = False

    def check_file(self, svg_file: str, expected_format: str = None) -> Dict:
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
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 0. Parse XML once — every other check assumes the file is valid
            # XML. Bail early on failure so the regex-based checks below don't
            # produce misleading errors on a broken document.
            root = self._parse_xml_root(content, result)
            if root is not None:
                if root.get('transform'):
                    result['errors'].append(
                        'Root <svg> transform is unsupported; apply transforms '
                        'to child elements or groups'
                    )

                # 1. Check viewBox
                self._check_viewbox(root, result, expected_format)

                # 2. Check forbidden elements
                self._check_forbidden_elements(content, root, result)

                # 2b. Validate the supported shadow/glow filter interface.
                self._check_filter_effects(root, result)

                # 2c. Reject gradient inheritance and transform semantics.
                self._check_gradient_interfaces(root, result)

                # 3. Check font-size values
                self._check_font_size_values(content, result)

                # 4. Check fonts
                self._check_fonts(content, result)

                # 5. Check text wrapping methods
                self._check_text_elements(content, root, result)

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
                self._check_animation_group_ids(root, result)

                # 8b. Check <pattern> elements declare a PPTX preset.
                self._check_pattern_fills(root, result)

                # 8c. Check opt-in native table/chart markers before export.
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

                # 9. Check spec_lock drift (colors / font-family / font-size).
                #    Templates do not ship a spec_lock.md, so skip in template
                #    mode to avoid noise.
                if not self.template_mode:
                    self._check_spec_lock_drift(content, svg_path, result)

                # 10. Check web-sourced image attribution. Templates don't carry
                #    image_sources.json; skip in template mode.
                if not self.template_mode:
                    self._check_sourced_image_attribution(content, svg_path, result)

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
                f"(see references/shared-standards.md §1)."
            )
            return None

    def _check_viewbox(self, root: ET.Element, result: Dict, expected_format: str = None):
        """Check viewBox attribute"""
        viewbox = root.get('viewBox')
        if not viewbox:
            result['errors'].append("Missing viewBox attribute")
            return

        result['info']['viewbox'] = viewbox

        parts = re.split(r'[\s,]+', viewbox.strip())
        if len(parts) != 4:
            result['errors'].append(
                f"viewBox must contain exactly four numeric values; got: {viewbox}"
            )
            return
        try:
            values = tuple(float(part) for part in parts)
        except ValueError:
            result['errors'].append(
                f"viewBox must contain exactly four numeric values; got: {viewbox}"
            )
            return
        if values[2] <= 0 or values[3] <= 0:
            result['errors'].append(
                f"viewBox width/height must be positive; got: {viewbox}"
            )
            return

        if values[0] != 0 or values[1] != 0 or any(not part.isdigit() for part in parts):
            result['warnings'].append(f"Unusual viewBox format: {viewbox}")

        # Check if it matches expected format
        if expected_format and expected_format in CANVAS_FORMATS:
            expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']
            expected_values = _parse_viewbox_values(expected_viewbox)
            if expected_values and values != expected_values:
                result['errors'].append(
                    f"viewBox mismatch: expected '{expected_viewbox}', got '{viewbox}'"
                )

    def _check_forbidden_elements(self, content: str, root: ET.Element, result: Dict):
        """Check forbidden elements (blocklist)"""
        content_lower = content.lower()
        elems = list(root.iter())
        local_names = {_local_name(elem).lower() for elem in elems}

        # ============================================================
        # Forbidden elements blocklist - PPT incompatible
        # ============================================================

        # Clipping / masking
        # clipPath is allowed on <image> elements and on pptx_to_svg-generated
        # nested crop <svg data-pptx-crop="1"> wrappers. Both map back to
        # DrawingML picture geometry in the native converter.
        if 'clippath' in local_names:
            ids = {elem.get('id') for elem in elems if elem.get('id')}
            for elem in elems:
                clip_ref = elem.get('clip-path')
                if not clip_ref:
                    continue
                tag = _local_name(elem).lower()
                is_crop_svg = tag == 'svg' and elem.get('data-pptx-crop') == '1'
                if tag != 'image' and not is_crop_svg:
                    result['errors'].append(
                        "clip-path is only allowed on <image> elements or "
                        "pptx_to_svg crop wrappers — for shapes, draw the target "
                        "shape directly instead of clipping")
                match = re.search(r'url\(#([^)]+)\)', clip_ref)
                if match and match.group(1) not in ids:
                    result['errors'].append(
                        f"clip-path references #{match.group(1)} but no matching "
                        f"<clipPath id=\"{match.group(1)}\"> definition found")
        if 'mask' in local_names:
            result['errors'].append("Detected forbidden <mask> element (PPT does not support SVG masks)")

        # Style system
        if 'style' in local_names:
            result['errors'].append("Detected forbidden <style> element (use inline attributes instead)")
        if re.search(r'\bclass\s*=', content):
            result['errors'].append("Detected forbidden class attribute (use inline styles instead)")
        # id attribute: only report error when <style> also exists (id is harmful only with CSS selectors)
        # id inside <defs> for linearGradient/filter etc. is required, Inkscape also auto-adds id to elements,
        # standalone id attributes have no impact on PPT export
        if 'style' in local_names and re.search(r'\bid\s*=', content):
            result['errors'].append(
                "Detected id attribute used with <style> (CSS selectors forbidden, use inline styles instead)"
            )
        if re.search(r'<\?xml-stylesheet\b', content_lower):
            result['errors'].append("Detected forbidden xml-stylesheet (external CSS references forbidden)")
        if re.search(r'<link[^>]*rel\s*=\s*["\']stylesheet["\']', content_lower):
            result['errors'].append("Detected forbidden <link rel=\"stylesheet\"> (external CSS references forbidden)")
        if re.search(r'@import\s+', content_lower):
            result['errors'].append("Detected forbidden @import (external CSS references forbidden)")
        if _validate_inline_geometry_properties is None:
            result['warnings'].append(
                "Unable to import inline geometry validator; "
                "native export will still validate geometry styles."
            )
        else:
            geometry_errors = _validate_inline_geometry_properties(root)
            for error in geometry_errors:
                result['errors'].append(f"Invalid inline geometry property: {error}")
            if not geometry_errors:
                _materialize_inline_geometry_properties(root)

        # Structure / nesting
        if 'foreignobject' in local_names:
            result['errors'].append(
                "Detected forbidden <foreignObject> element (use <tspan> for manual line breaks)")
        has_generic_use = any(
            _local_name(elem).lower() == 'use' and elem.get('data-icon') is None
            for elem in elems
        )
        if has_generic_use:
            if _validate_local_use_references is None:
                result['warnings'].append(
                    "Detected local <use> references, but the shared validator "
                    "could not be imported; native export will still validate them."
                )
            else:
                for error in _validate_local_use_references(root):
                    result['errors'].append(f"Invalid local <use> reference: {error}")
        # marker-start / marker-end are conditionally allowed (see shared-standards.md §1.1).
        # The converter maps qualifying <marker> defs to native DrawingML <a:headEnd>/<a:tailEnd>.
        # We only warn when a marker is used without an obvious <defs> definition in the same file.
        if re.search(r'\bmarker-(?:start|end)\s*=\s*["\']url\(#([^)]+)\)', content_lower):
            if 'marker' not in local_names:
                result['errors'].append(
                    "Detected marker-start/marker-end referencing a marker id, "
                    "but no <marker> element found in the file")

        # Text / fonts
        if 'textpath' in local_names:
            result['errors'].append("Detected forbidden <textPath> element (path text is incompatible with PPT)")
        if '@font-face' in content_lower:
            result['errors'].append("Detected forbidden @font-face (use system font stack)")

        # Animation / interaction
        if any(name.startswith('animate') for name in local_names):
            result['errors'].append("Detected forbidden SMIL animation element <animate*> (SVG animations are not exported)")
        if 'set' in local_names:
            result['errors'].append("Detected forbidden SMIL animation element <set> (SVG animations are not exported)")
        if 'script' in local_names:
            result['errors'].append("Detected forbidden <script> element (scripts and event handlers forbidden)")
        if re.search(r'\bon\w+\s*=', content):  # onclick, onload etc.
            result['errors'].append("Detected forbidden event attributes (e.g., onclick, onload)")

        # Other discouraged elements
        if 'iframe' in local_names:
            result['errors'].append("Detected <iframe> element (should not appear in SVG)")

        # Paint-server references must match the exact definitions consumed by
        # drawingml.converter.collect_defs: direct children of <defs> only.
        defs_by_id = {}
        for defs_elem in elems:
            if _local_name(defs_elem).lower() != 'defs':
                continue
            for child in defs_elem:
                child_id = child.get('id')
                if child_id:
                    defs_by_id[child_id] = child
        pattern_descendant_ids = {
            id(descendant)
            for pattern in elems
            if _local_name(pattern).lower() == 'pattern'
            for descendant in pattern.iter()
            if descendant is not pattern
        }
        fill_shape_tags = {'rect', 'circle', 'ellipse', 'path', 'polygon', 'polyline'}
        stroke_shape_tags = fill_shape_tags | {'line'}
        paint_reference_errors = set()
        for elem in elems:
            style_values = (
                _parse_inline_style(elem.get('style'))
                if _parse_inline_style is not None else {}
            )
            for attr in ('fill', 'stroke'):
                value = style_values.get(attr) or elem.get(attr)
                match = re.fullmatch(r'url\(#([^)]+)\)', (value or '').strip())
                if match is None:
                    continue
                ref_id = match.group(1)
                target = defs_by_id.get(ref_id)
                elem_tag = _local_name(elem)
                elem_tag_lower = elem_tag.lower()
                if target is None:
                    paint_reference_errors.add(
                        f"<{elem_tag}> {attr}=url(#{ref_id}) has no matching "
                        "direct <defs> definition"
                    )
                    continue
                has_text_descendant = any(
                    _local_name(descendant).lower() in {'text', 'tspan'}
                    for descendant in elem.iter()
                    if descendant is not elem
                )
                if id(elem) in pattern_descendant_ids:
                    allowed_tags = ()
                elif attr == 'fill' and elem_tag_lower in fill_shape_tags:
                    allowed_tags = ('lineargradient', 'radialgradient', 'pattern')
                elif attr == 'stroke' and elem_tag_lower in stroke_shape_tags:
                    allowed_tags = ('lineargradient', 'radialgradient')
                elif attr == 'fill' and elem_tag_lower in {'text', 'tspan'}:
                    allowed_tags = ('lineargradient', 'radialgradient')
                elif attr == 'fill' and elem_tag_lower == 'g':
                    allowed_tags = (
                        ('lineargradient', 'radialgradient')
                        if has_text_descendant
                        else ('lineargradient', 'radialgradient', 'pattern')
                    )
                elif attr == 'stroke' and elem_tag_lower == 'g' and not has_text_descendant:
                    allowed_tags = ('lineargradient', 'radialgradient')
                else:
                    allowed_tags = ()
                target_tag = _local_name(target).lower()
                if not allowed_tags:
                    paint_reference_errors.add(
                        f"<{elem_tag}> {attr}=url(#{ref_id}) is not supported "
                        "by native PPTX conversion in this context"
                    )
                    continue
                if target_tag not in allowed_tags:
                    tag_labels = {
                        'lineargradient': 'linearGradient',
                        'radialgradient': 'radialGradient',
                        'pattern': 'pattern',
                    }
                    expected = '/'.join(
                        tag_labels[tag] for tag in allowed_tags
                    )
                    paint_reference_errors.add(
                        f"<{elem_tag}> {attr}=url(#{ref_id}) resolves to "
                        f"<{_local_name(target)}>; expected {expected}"
                    )
        result['errors'].extend(sorted(paint_reference_errors))

        # Paint grammar: use the exporter's parser so authoring validation and
        # native conversion accept the same CSS color subset.
        paint_values = [
            (attr, value)
            for attr in (
                'fill', 'stroke', 'stop-color', 'flood-color',
                'data-pptx-fg', 'data-pptx-bg',
            )
            for value in self._svg_property_values(content, attr)
        ]
        if _parse_export_color is None:
            result['warnings'].append(
                "Unable to import svg_to_pptx color parser; skipped paint syntax check"
            )
        else:
            invalid_paints = set()
            for attr, value in paint_values:
                normalized = value.strip()
                if attr in {'fill', 'stroke'} and (
                    normalized.lower() == 'none'
                    or re.fullmatch(r'url\(#[^)]+\)', normalized)
                ):
                    continue
                if _BARE_HEX_VALUE_RE.fullmatch(normalized):
                    invalid_paints.add(value)
                    continue
                color, _alpha = _parse_export_color(normalized)
                if color is None:
                    invalid_paints.add(value)
            if invalid_paints:
                shown = ', '.join(sorted(invalid_paints)[:5])
                more = len(invalid_paints) - 5
                suffix = f" (+{more} more)" if more > 0 else ""
                result['errors'].append(
                    "Unsupported SVG paint value(s) for PPTX export: "
                    f"{shown}{suffix}. Use a supported named color, rgb()/rgba(), "
                    "hsl()/hsla(), or #RGB/#RGBA/#RRGGBB/#RRGGBBAA."
                )
        for elem in elems:
            tag = _local_name(elem).lower()
            if tag not in {'g', 'image'}:
                continue
            raw_opacity = elem.get('opacity')
            if raw_opacity is None:
                style_match = re.search(
                    r'(?:^|;)\s*opacity\s*:\s*([^;]+)',
                    elem.get('style', ''),
                    flags=re.IGNORECASE,
                )
                raw_opacity = style_match.group(1).strip() if style_match else None
            if raw_opacity is None:
                continue
            try:
                opacity = float(raw_opacity)
            except ValueError:
                opacity = -1.0
            if not 0.0 <= opacity <= 1.0:
                result['errors'].append(
                    f"<{tag} opacity> must be a numeric value from 0 to 1, got {raw_opacity!r}"
                )
            if tag == 'g' and opacity < 1.0 and any(
                descendant.tag.rsplit('}', 1)[-1] != 'metadata'
                and descendant.get('data-pptx-native')
                for descendant in elem.iter()
            ):
                result['warnings'].append(
                    "<g opacity> around data-pptx-native content uses the SVG "
                    "fallback; --native-objects export rejects that combination"
                )

    def _check_filter_effects(self, root: ET.Element, result: Dict) -> None:
        """Validate filters against the native shadow/glow approximation."""
        elems = list(root.iter())
        direct_filters = []
        filters_by_id = {}
        for defs_elem in elems:
            if _local_name(defs_elem) != 'defs':
                continue
            for child in defs_elem:
                if _local_name(child) != 'filter':
                    continue
                direct_filters.append(child)
                filter_id = child.get('id')
                if filter_id:
                    filters_by_id[filter_id] = child

        issues = set()
        for elem in elems:
            tag = _local_name(elem)
            style_values = (
                _parse_inline_style(elem.get('style'))
                if _parse_inline_style is not None else {}
            )
            if style_values.get('filter'):
                issues.add(
                    f"<{tag}> filter must use a direct filter=\"url(#id)\" "
                    "attribute; inline style filters are not supported"
                )

            raw_filter = elem.get('filter')
            if raw_filter is None:
                continue
            match = re.fullmatch(r'url\(#([^)]+)\)', raw_filter.strip())
            if match is None:
                issues.add(
                    f"<{tag}> filter must be an exact local url(#id) reference; "
                    f"got {raw_filter!r}"
                )
                continue
            filter_id = match.group(1)
            if filter_id not in filters_by_id:
                issues.add(
                    f"<{tag}> filter=url(#{filter_id}) has no matching direct "
                    f"<defs><filter id=\"{filter_id}\"> definition"
                )

        for filter_elem in direct_filters:
            filter_id = filter_elem.get('id')
            label = f"filter #{filter_id}" if filter_id else '<filter> without id'
            primitives = [
                _local_name(descendant)
                for descendant in filter_elem.iter()
                if descendant is not filter_elem
            ]
            unsupported = sorted(
                set(primitives) - _SUPPORTED_FILTER_PRIMITIVES
            )
            if unsupported:
                issues.add(
                    f"{label} uses unsupported filter primitive(s): "
                    f"{', '.join(unsupported)}"
                )
            if not _FILTER_EFFECT_PRIMITIVES.intersection(primitives):
                issues.add(
                    f"{label} must contain feDropShadow or feGaussianBlur"
                )
            if any(
                _local_name(descendant) == 'feFuncA'
                and descendant.get('type') != 'linear'
                for descendant in filter_elem.iter()
            ):
                issues.add(f"{label} requires feFuncA type=\"linear\"")

        result['errors'].extend(sorted(issues))

    def _check_gradient_interfaces(self, root: ET.Element, result: Dict) -> None:
        """Reject gradient inheritance, transforms, and spread modes."""
        issues = set()
        for gradient in root.iter():
            tag = _local_name(gradient)
            if tag not in {'linearGradient', 'radialGradient'}:
                continue
            gradient_id = gradient.get('id')
            label = f"<{tag} id=\"{gradient_id}\">" if gradient_id else f'<{tag}>'
            attribute_names = {
                name.rsplit('}', 1)[-1]
                for name in gradient.attrib
            }
            if 'href' in attribute_names:
                issues.add(
                    f"{label} cannot inherit from href/xlink:href; "
                    "define gradient stops directly"
                )
            if 'gradientTransform' in attribute_names:
                issues.add(f"{label} cannot use gradientTransform")
            if 'spreadMethod' in attribute_names:
                issues.add(f"{label} cannot use spreadMethod")

        result['errors'].extend(sorted(issues))

    def _check_font_size_values(self, content: str, result: Dict):
        """Require font-size values to be unitless numeric SVG px values."""
        numeric_re = re.compile(r'^(?:\d+(?:\.\d+)?|\.\d+)$')
        bad_values = set()

        for match in re.finditer(r'\bfont-size\s*=\s*(["\'])(.*?)\1', content, re.IGNORECASE):
            raw = match.group(2).strip()
            if not numeric_re.fullmatch(raw):
                bad_values.add(raw)

        for match in re.finditer(r'\bfont-size\s*:\s*([^;"\']+)', content, re.IGNORECASE):
            raw = match.group(1).strip()
            if not numeric_re.fullmatch(raw):
                bad_values.add(raw)

        if bad_values:
            shown_values = sorted(bad_values)
            shown = ', '.join(shown_values[:5])
            more = len(shown_values) - 5
            suffix = f" (+{more} more)" if more > 0 else ""
            result['errors'].append(
                f"font-size must be a unitless numeric px value; found {shown}{suffix}. "
                "Write e.g. font-size=\"28\", never font-size=\"28px\" or \"21pt\"."
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
        if _parse_export_font_family is None:
            result['warnings'].append(
                "Unable to import svg_to_pptx font resolver; skipped exported-font safety check"
            )
            return

        for font_family in font_matches:
            exported = _parse_export_font_family(font_family)
            unsafe = [
                f"{role}={family}"
                for role, family in exported.items()
                if family.strip().lower() not in PPT_SAFE_FONTS
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

        # Check for overly long single-line text (may need wrapping)
        text_matches = re.findall(r'<text[^>]*>([^<]{100,})</text>', content)
        if text_matches:
            result['warnings'].append(
                f"Detected {len(text_matches)} potentially overly long single-line text(s) (consider using tspan for wrapping)"
            )

        self._check_unmergeable_leading_text(root, result)

    def _check_unmergeable_leading_text(self, root: ET.Element, result: Dict) -> None:
        """Warn when leading text cannot be normalized for paragraph merging."""
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
                f"be normalized for PPT paragraph merging ({sample}{suffix})"
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
        """Check image file existence and resolution vs display size."""
        svg_dir = svg_path.parent
        checked = set()

        for image in root.iter():
            if _local_name(image).lower() != 'image':
                continue

            href = image.get('href') or image.get(f'{{{XLINK_NS}}}href')
            if not href or href.startswith('data:'):
                continue
            if self.template_mode and '{{' in href and '}}' in href:
                continue
            if _resolve_external_image_reference is None or _unresolved_external_image_reference_path is None:
                result['warnings'].append(
                    "Detected image references, but shared image resolver could not be imported; "
                    "export will still validate them."
                )
                return
            if href in checked:
                continue
            checked.add(href)

            img_path = _resolve_external_image_reference(svg_dir, href)
            if img_path is None:
                resolved_path = _unresolved_external_image_reference_path(svg_dir, href)
                result['errors'].append(
                    f"Image file not found: {href} (resolved to {resolved_path})")
                continue

            # Check resolution vs display size
            display_w_str = image.get('width')
            display_h_str = image.get('height')
            if not display_w_str or not display_h_str:
                continue

            try:
                display_w = float(display_w_str)
                display_h = float(display_h_str)
            except (ValueError, TypeError):
                continue

            try:
                from PIL import Image as PILImage
                with PILImage.open(img_path) as img:
                    actual_w, actual_h = img.size

                if actual_w < display_w or actual_h < display_h:
                    result['warnings'].append(
                        f"Image {href} is {actual_w}x{actual_h} but displayed at "
                        f"{int(display_w)}x{int(display_h)} — may appear blurry")
                elif actual_w > display_w * 4 and actual_h > display_h * 4:
                    result['warnings'].append(
                        f"Image {href} is {actual_w}x{actual_h} but displayed at "
                        f"{int(display_w)}x{int(display_h)} — consider downsizing "
                        f"to reduce file size")
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
        seen = set()
        for elem in placeholders:
            icon_name = (elem.get('data-icon') or '').strip()
            if not icon_name:
                result['errors'].append("Icon placeholder has empty data-icon value")
                continue
            if icon_name in seen:
                continue
            seen.add(icon_name)

            icon_path, _ = _resolve_icon_path(icon_name, icons_dir, fallback_dir)
            if not icon_path.exists():
                fallback_msg = f", then {fallback_dir}" if fallback_dir else ""
                result['errors'].append(
                    f"Icon not found: {icon_name} (searched {icons_dir}"
                    f"{fallback_msg})"
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

    def _check_animation_group_ids(self, root: ET.Element, result: Dict):
        """Warn when visible top-level groups cannot be customized."""
        non_visual = {'defs', 'title', 'desc', 'metadata', 'style'}
        for index, child in enumerate(list(root), start=1):
            tag = child.tag.split('}', 1)[-1]
            if tag in non_visual:
                continue
            if tag == 'g' and not child.get('id'):
                result['warnings'].append(
                    f"Top-level visible <g> #{index} has no id; "
                    "object-level animation config cannot reference it"
                )

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
        `dkUpDiag`). Two failure modes worth catching pre-export:

        1. Missing annotation → converter silently falls back to `ltUpDiag`
           (diagonal stripes). Color metadata or child paints still resolve,
           with white as the final background fallback.
        2. Invalid preset name → PPTX schema rejects the file; PowerPoint
           opens it with "needs to be repaired". OOXML
           `ST_PresetPatternVal` is a closed enum — only the names in
           `_OOXML_PATTERN_PRESETS` are legal. Inventing `ltGrid` (no such
           value) is the canonical mistake; the only grids are `smGrid` /
           `lgGrid` / `dotGrid`.
        """
        for pattern in root.iter(f'{{{SVG_NS}}}pattern'):
            pat_id = pattern.get('id', '<unnamed>')
            prst = pattern.get('data-pptx-pattern')
            if not prst:
                result['warnings'].append(
                    f"<pattern id=\"{pat_id}\"> has no data-pptx-pattern attribute — "
                    "PPTX export will fall back to `ltUpDiag` (diagonal stripes), "
                    "not your custom geometry. Add a valid data-pptx-pattern; "
                    "set data-pptx-fg/data-pptx-bg or matching child paints "
                    "when explicit pattern colors are required."
                )
                continue
            if prst not in self._OOXML_PATTERN_PRESETS:
                result['errors'].append(
                    f"<pattern id=\"{pat_id}\"> uses data-pptx-pattern=\"{prst}\" "
                    "which is not in OOXML ST_PresetPatternVal — exported PPTX "
                    "will fail schema validation ('needs to be repaired'). "
                    "Use one of: smGrid / lgGrid / dotGrid (grids), "
                    "ltUpDiag / dkUpDiag / cross / diagCross / weave / plaid / "
                    "horzBrick (others); see references/shared-standards.md §7 "
                    "for the full authoring enum."
                )

    def _check_native_object_markers(self, root: ET.Element, result: Dict) -> None:
        """Validate opt-in native table/chart markers before PPTX export."""
        invalid_status_elements: set[ET.Element] = set()
        for elem in root.iter():
            if elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            has_status = any(
                elem.get(name) is not None
                for name in (
                    'data-pptx-visual-status',
                    'data-pptx-route-status',
                    'data-pptx-native-status',
                )
            )
            if not has_status:
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
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
            if elem.get('data-pptx-route-status') == 'reconstruction-only':
                route = (
                    "--native-objects may reconstruct its active native marker"
                    if (elem.get('data-pptx-native') or '').strip()
                    else "default export keeps the visible placeholder"
                )
                result['warnings'].append(
                    f"PPTX graphic {marker_id} is a reconstruction-only placeholder; "
                    f"it has no baked preview and {route}"
                )

        for elem in root.iter():
            status = elem.get('data-pptx-native-status')
            if not status or elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            if elem.get('data-pptx-native'):
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            result['warnings'].append(
                f"Native PPTX object {marker_id} is fallback-only: {status}"
            )

        markers = [
            elem for elem in root.iter()
            if (
                elem.get('data-pptx-native')
                and elem.tag.rsplit('}', 1)[-1] != 'metadata'
                and elem not in invalid_status_elements
            )
        ]
        if not markers:
            return
        if _validate_native_object_marker is None:
            result['warnings'].append(
                "Detected data-pptx-native markers, but native-object validator "
                "could not be imported; export-time validation will still run."
            )
            return

        parent_map = {
            child: parent
            for parent in root.iter()
            for child in parent
        }

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
                        f"Invalid data-pptx-native marker {marker_id}: {exc}"
                    )
                    continue
                for warning in warnings:
                    result['warnings'].append(
                        f"data-pptx-native marker {marker_id}: {warning}"
                    )
                continue

            try:
                _validate_native_object_marker(marker, ancestors=ancestors_tuple)
            except RuntimeError as exc:
                result['errors'].append(
                    f"Invalid data-pptx-native marker {marker_id}: {exc}"
                )
                continue
            if _native_object_marker_warnings is None:
                continue
            for warning in _native_object_marker_warnings(
                marker,
                ancestors=ancestors_tuple,
                document_root=root,
            ):
                result['warnings'].append(
                    f"data-pptx-native marker {marker_id}: {warning}"
                )

    def _check_pptx_structure_metadata(
        self,
        root: ET.Element,
        svg_path: Path,
        result: Dict,
    ) -> None:
        """Validate the intrinsic structured Master/Layout SVG contract."""
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
    def _append_structure_coverage_warnings(
        root: ET.Element,
        result: Dict,
    ) -> None:
        """Warn on mapped pages that compile to bare Masters / empty Layouts.

        Zero-slot and framing-only Layouts are legal contracts, so these stay
        warnings; the workflow gate requires each one to be fixed or
        explicitly kept with a stated reason.
        """
        if not (root.get('data-pptx-layout') or '').strip():
            return
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
            result['warnings'].append(
                'Mapped page declares data-pptx-layout but no data-pptx-layer '
                'mark; the exported Master gets no shared background/chrome '
                'and the Layout gets no static framing. Mark the deck-wide '
                'background data-pptx-layer="master" and this layout key\'s '
                'framing data-pptx-layer="layout".'
            )
        if not has_placeholder and not has_layout_atom:
            result['warnings'].append(
                'Mapped page has no placeholder slot and no '
                'data-pptx-layer="layout" atom; its Layout exports empty. '
                'Declare the slots the page actually has (title / subtitle / '
                'body / picture / slide-number / footer) and mark the layout '
                'key\'s static framing, or state why this fixed composition '
                'is intentionally zero-slot.'
            )
        elif not has_placeholder:
            result['warnings'].append(
                'Mapped Layout has static framing but no insertable '
                'placeholder slot. Keep it only when zero-slot is the '
                'intended reusable contract; otherwise declare the slots the '
                'page actually has (title / subtitle / body / picture / '
                'slide-number / footer).'
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

    def _check_spec_lock_drift(self, content: str, svg_path: Path, result: Dict):
        """Detect values used in the SVG that fall outside spec_lock.md.

        Covers colors (fill / stroke / stop-color / flood-color / pattern
        metadata), font-family, and font-size.
        Emits per-file warnings summarising the drift counts; exact drifting
        values are accumulated in self._drift_summary for the end-of-run
        aggregation. When spec_lock.md is missing, silently skip (consistent
        with executor-base.md §2.1's 'missing lock → warn and proceed' policy).
        """
        lock = self._get_spec_lock(svg_path)
        if lock is None:
            return

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

        typo = lock.get('typography', {})
        numeric_size_re = re.compile(r'^(?:\d+(?:\.\d+)?|\.\d+)$')
        invalid_lock_sizes = []
        for k, v in typo.items():
            if k == 'font_family' or k.endswith('_family'):
                continue
            if not numeric_size_re.fullmatch(v.strip()):
                invalid_lock_sizes.append(f"{k}: {v}")
        if invalid_lock_sizes:
            shown = ', '.join(invalid_lock_sizes[:5])
            more = len(invalid_lock_sizes) - 5
            suffix = f" (+{more} more)" if more > 0 else ""
            result['errors'].append(
                f"spec_lock typography sizes must be unitless numeric px values; "
                f"found {shown}{suffix}."
            )

        # Font families: default `font_family` plus any per-role `*_family`
        # override (title_family / body_family / emphasis_family / code_family,
        # per spec_lock_reference.md). Any of these is a legitimate declared
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

        # Sizes: declared slots are anchors; body is the ramp baseline.
        allowed_sizes = set()
        body_px = None
        for k, v in typo.items():
            if k == 'font_family' or k.endswith('_family'):
                continue
            allowed_sizes.add(self._normalize_size(v))
            if k == 'body':
                try:
                    body_px = float(self._normalize_size(v))
                except (ValueError, TypeError):
                    body_px = None

        # Scan SVG for used values
        color_drifts = set()
        for attr in (
            'fill', 'stroke', 'stop-color', 'flood-color',
            'data-pptx-fg', 'data-pptx-bg',
        ):
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

        font_drifts = set()
        for val in self._font_family_values(content):
            if allowed_fonts and self._normalize_font_stack(val) not in allowed_fonts:
                font_drifts.add(val)

        # Poster / showcase contexts use unbounded hero type — drop the ceiling.
        mode = (lock.get('mode', {}).get('mode') or '').strip().lower()
        vstyle = (lock.get('visual_style', {}).get('visual_style') or '').strip().lower()
        max_ratio = (float('inf') if mode in POSTER_SIZE_MODES or vstyle in POSTER_SIZE_STYLES
                     else RAMP_MAX_RATIO)

        size_drifts = set()
        used_sizes = []
        for raw_value in self._svg_property_values(content, 'font-size'):
            val = self._normalize_size(raw_value)
            used_sizes.append(val)
            if not allowed_sizes or val in allowed_sizes:
                continue
            # Intermediate values are allowed when they sit inside the ramp
            # envelope (ratio to body within [RAMP_MIN_RATIO, max_ratio]).
            if body_px and body_px > 0:
                try:
                    ratio = float(val) / body_px
                    if RAMP_MIN_RATIO <= ratio <= max_ratio:
                        continue
                except ValueError:
                    pass
            size_drifts.add(val)

        template_size_drift = self._detect_template_size_drift(
            used_sizes, allowed_sizes, body_px
        )

        # Record in run-wide aggregation
        fname = svg_path.name
        for v in color_drifts:
            self._drift_summary['colors'][v].add(fname)
        for v in font_drifts:
            self._drift_summary['fonts'][v].add(fname)
        for v in size_drifts:
            self._drift_summary['sizes'][v].add(fname)

        # Per-file warning (one condensed line; details live in summary)
        parts = []
        if color_drifts:
            parts.append(f"{len(color_drifts)} color(s)")
        if font_drifts:
            parts.append(f"{len(font_drifts)} font-family value(s)")
        if size_drifts:
            parts.append(f"{len(size_drifts)} font-size value(s)")
        if parts:
            result['warnings'].append(
                f"spec_lock drift: {', '.join(parts)} not in spec_lock.md "
                "(see drift summary for details)"
            )
        if template_size_drift:
            result['warnings'].append(template_size_drift)

    def _detect_template_size_drift(self, used_sizes, allowed_sizes, body_px):
        """Warn when template-like small sizes bypass the locked type ramp.

        The normal drift check deliberately permits in-ramp feature sizes, so
        it should not hard-fail valid hero numbers or one-off labels. This
        warning targets the common executor failure mode: copying a template's
        compact 12/15/16px text stack instead of mapping content roles to
        spec_lock typography, then reflowing from those locked px values.
        """
        if not allowed_sizes or not body_px or body_px <= 0:
            return None

        try:
            declared_min = min(float(v) for v in allowed_sizes)
        except ValueError:
            declared_min = None

        # Stay narrow on purpose: real decks carry legitimate undeclared
        # sub-body sizes (intermediate levels, labels, emphasis) just below the
        # locked body, so "any size < body" floods the warning and destroys its
        # credibility. Only flag values that read as genuine template leftovers
        # — at or below `body * 0.75`, or below the smallest declared slot. This
        # under-warns (a stray 15/16 against a body of 18 can slip through) in
        # exchange for not crying wolf on valid intermediate type.
        template_like_limit = body_px * 0.75
        template_like_sub_body = []
        for raw in used_sizes:
            if raw in allowed_sizes:
                continue
            try:
                size = float(raw)
            except (TypeError, ValueError):
                continue
            below_declared_floor = declared_min is not None and size < declared_min
            if size <= template_like_limit or below_declared_floor:
                template_like_sub_body.append(raw)

        if not template_like_sub_body:
            return None

        counts = Counter(template_like_sub_body)
        distinct = sorted(counts, key=lambda v: float(v))
        repeated_total = sum(counts.values())

        below_declared_floor = []
        if declared_min is not None:
            below_declared_floor = [v for v in distinct if float(v) < declared_min]

        if len(distinct) < 2 and repeated_total < 4 and not below_declared_floor:
            return None

        sample = ', '.join(
            f"{v}x{counts[v]}" if counts[v] > 1 else v
            for v in distinct[:5]
        )
        more = len(distinct) - 5
        suffix = f" (+{more} more)" if more > 0 else ""
        return (
            "possible template font-size drift: undeclared sub-body size(s) "
            f"{sample}{suffix}. Map each text item to a spec_lock typography "
            "role first, then reflow card height / y / dy / line-height from "
            "the locked px values."
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

    def _load_image_sources_manifest(self, svg_path: Path) -> Dict:
        manifest_path = self._find_image_sources_manifest(svg_path)
        if manifest_path is None:
            return {}
        if manifest_path in self._source_manifest_cache:
            return self._source_manifest_cache[manifest_path]
        try:
            payload = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            payload = {}
        self._source_manifest_cache[manifest_path] = payload
        return payload

    def _check_sourced_image_attribution(self, content: str, svg_path: Path, result: Dict):
        """Require visible credit text for attribution-required web images.

        image_search.py records the legal tier in images/image_sources.json;
        Executor must render compact credit text into the SVG. This check
        prevents a quality-first CC BY / CC BY-SA image from silently reaching
        export without attribution.
        """
        manifest = self._load_image_sources_manifest(svg_path)
        items = manifest.get('items') or []
        if not items:
            return

        text_content = html.unescape(re.sub(r'<[^>]+>', ' ', content))
        text_content = re.sub(r'\s+', ' ', text_content)
        svg_stem = svg_path.stem

        for item in items:
            if not item.get('attribution_required') and item.get('license_tier') != 'attribution-required':
                continue

            filename = Path(str(item.get('filename') or '')).name
            slide = str(item.get('slide') or '').strip()
            referenced = bool(filename and filename in content)
            same_slide = bool(slide and slide == svg_stem)
            if not referenced and not same_slide:
                continue

            license_name = str(item.get('license_name') or '').upper()
            license_token = 'CC BY-SA' if 'BY-SA' in license_name else 'CC BY'
            has_credit = license_token in text_content.upper()
            if not has_credit:
                result['errors'].append(
                    f"Missing inline attribution for sourced image {filename or '(unknown)'} "
                    f"({license_token}). Add compact credit text per "
                    f"references/image-searcher.md §7."
                )

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
        elif 'font' in error_msg.lower():
            return 'Font issues'
        else:
            return 'Other'

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

        if not dir_path.exists():
            print(f"[ERROR] Directory does not exist: {directory}")
            self.summary['errors'] += 1
            self.issue_types['Input issues'] += 1
            return []

        # Brand-only template workspaces have no SVG roster. Resolve the current
        # nested spec first and keep legacy-flat roots readable.
        if self.template_mode and dir_path.is_dir():
            nested_spec = dir_path / 'templates' / 'design_spec.md'
            spec = nested_spec if nested_spec.is_file() else dir_path / 'design_spec.md'
            if spec.exists() and _design_spec_is_brand(spec):
                print(
                    f"[INFO] Brand directory detected (kind: brand) — "
                    f"SVG checks skipped."
                )
                print(
                    f"[INFO] Validate brand specs via: "
                    f"python3 scripts/register_template.py "
                    f"--kind brand <brand_id> --dry-run"
                )
                return self.results

        # Find all SVG files
        if dir_path.is_file():
            svg_files = [dir_path]
        else:
            if self.template_mode:
                # Template directories live at templates/{layouts,decks}/<id>/.
                svg_files = sorted(dir_path.glob('*.svg'))
            else:
                svg_output = dir_path / \
                    'svg_output' if (
                        dir_path / 'svg_output').exists() else dir_path
                svg_files = sorted(svg_output.glob('*.svg'))

        if not svg_files:
            print(f"[ERROR] No SVG files found in: {directory}")
            self.summary['errors'] += 1
            self.issue_types['Input issues'] += 1
            return []

        print(f"\n[SCAN] Checking {len(svg_files)} SVG file(s)...\n")

        for svg_file in svg_files:
            result = self.check_file(str(svg_file), expected_format)
            self._print_result(result)

        if self.template_mode:
            check_structure = _template_structure_checks_enabled(dir_path)
            if _legacy_template_structure_deferred(dir_path):
                print(
                    "[INFO] Legacy native_structure_mode: template detected; "
                    "roster and placeholder checks remain active while positive "
                    "structure checks await library migration."
                )
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
        if not self.template_mode and dir_path.is_dir():
            self._check_animation_config_contract(dir_path)
            self._check_illustration_resource_contract(dir_path)

        return self.results

    def _check_pptx_structure_contract(
        self,
        target_path: Path,
        svg_files: List[Path],
    ) -> None:
        """Validate the all-page structured lock and reusable contracts."""
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
                'free-design projects use mode: flat; restore legacy '
                'template/structured metadata by following skills/ppt-master/'
                'workflows/restore-pptx-structure.md before export.',
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
                sibling_files = sorted(target_path.parent.glob('*.svg'))
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
        errors: List[str] = []
        for spec in specs:
            page = f"P{spec.slide_num:02d}"
            reference = references.get(spec.slide_num)
            if reference is None:
                errors.append(f"spec_lock.md pptx_layouts is missing {page}")
                continue
            if spec.master_key != reference.master_key:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-master={spec.master_key!r} "
                    f"does not match spec_lock {page} Master key "
                    f"{reference.master_key!r}"
                )
            if spec.layout_key != reference.layout_key:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-layout={spec.layout_key!r} "
                    f"does not match spec_lock {page} layout key "
                    f"{reference.layout_key!r}"
                )
            if spec.layout_name != reference.layout_name:
                errors.append(
                    f"{spec.svg_path.name}: data-pptx-layout-name="
                    f"{spec.layout_name!r} does not match spec_lock {page} "
                    f"layout name {reference.layout_name!r}"
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
                "define a Layout."
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
                        grandchild.get('data-pptx-placeholder-carrier') or ''
                    ).strip().lower() == 'true'
                )
                placeholder_parts.append((
                    placeholder,
                    child.tag.rsplit('}', 1)[-1],
                    child.get('data-pptx-placeholder-bounds') or '',
                    child.get('data-pptx-placeholder-idx') or '',
                    (
                        child.get('data-pptx-placeholder-binding') or 'carrier'
                    ).strip().lower(),
                    carrier_tags,
                ))
        return (
            tuple(layout_parts),
            tuple(sorted(placeholder_parts)),
        )

    def _check_illustration_resource_contract(self, dir_path: Path) -> None:
        """Project-level illustration resource checks."""
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

        rows = self._extract_image_resource_rows(spec_text)
        if not rows:
            return

        lock_images = self._load_project_lock_images(project_path)
        svg_texts = self._load_project_svg_texts(project_path)
        all_svg_text = "\n".join(svg_texts.values())

        sheet_rows = [row for row in rows if self._row_type(row).lower() == 'illustration sheet']
        slice_rows = [row for row in rows if self._row_acquire(row) == 'slice']
        image_rows = [
            row for row in rows
            if self._row_acquire(row) in {'ai', 'web', 'user', 'placeholder', 'slice'}
            and self._row_type(row).lower() not in {'latex formula', 'illustration sheet'}
        ]

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
            if filename in all_svg_text:
                self._illustration_issues.append((
                    'error',
                    'sheet_referenced',
                    f"{filename} is an Illustration Sheet but is referenced by an SVG; "
                    "generate it only as a slice source, never place it.",
                ))

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
                    f"{filename} is a Generated slice row but images/{filename} does not exist.",
                ))

        has_coverage_note = 'Image-as-canvas' in spec_text or 'image-as-canvas' in spec_text
        pattern_ids = self._collect_layout_pattern_ids(image_rows)
        if len(image_rows) >= 4 and not any(38 <= pid <= 46 for pid in pattern_ids):
            if not has_coverage_note:
                self._illustration_issues.append((
                    'warning',
                    'missing_image_as_canvas',
                    "deck has 4+ image-bearing rows but no #38-#46 image-as-canvas "
                    "layout and no coverage note in design_spec.md §VIII.",
                ))

        conventional_ids = {1, 2, 3, 5, 6}
        if len(image_rows) >= 4 and pattern_ids and pattern_ids.issubset(conventional_ids):
            if not has_coverage_note:
                self._illustration_issues.append((
                    'warning',
                    'layout_pattern_degenerated',
                    "all image-bearing rows use only basic full-bleed / left-right / "
                    "top-bottom patterns (#1/#2/#3/#5/#6); re-check "
                    "references/image-layout-patterns.md for modifiers or image-as-canvas options.",
                ))

        for row in image_rows:
            self._check_decorative_image_row(row, project_path, svg_texts)

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
            if filename and filename.lower() != 'filename':
                rows.append(row)

        return rows

    @staticmethod
    def _row_filename(row: Dict[str, str]) -> str:
        return Path(row.get('Filename', '').strip()).name

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
    def _collect_layout_pattern_ids(rows: List[Dict[str, str]]) -> set[int]:
        ids: set[int] = set()
        for row in rows:
            for match in re.finditer(r'#(\d+)\b', SVGQualityChecker._row_layout(row)):
                ids.add(int(match.group(1)))
        return ids

    def _load_project_lock_images(self, project_path: Path) -> set[str]:
        """Return filenames listed under spec_lock.md images."""
        lock_path = project_path / 'spec_lock.md'
        if _parse_spec_lock is None or not lock_path.exists():
            return set()
        try:
            lock = _parse_spec_lock(lock_path)
        except Exception:
            return set()
        images = set()
        for value in lock.get('images', {}).values():
            path_part = value.split('|', 1)[0].strip()
            images.add(Path(path_part).name)
        return images

    @staticmethod
    def _load_project_svg_texts(project_path: Path) -> Dict[Path, str]:
        """Read project SVG output files for project-level cross-checks."""
        svg_dir = project_path / 'svg_output'
        if not svg_dir.exists():
            return {}
        out: Dict[Path, str] = {}
        for svg_path in sorted(svg_dir.glob('*.svg')):
            try:
                out[svg_path] = svg_path.read_text(encoding='utf-8')
            except OSError:
                continue
        return out

    def _check_decorative_image_row(
        self,
        row: Dict[str, str],
        project_path: Path,
        svg_texts: Dict[Path, str],
    ) -> None:
        """Warn when decorative image patterns lack obvious SVG/file evidence."""
        filename = self._row_filename(row)
        if not filename:
            return
        layout = self._row_layout(row)
        ids = {int(match.group(1)) for match in re.finditer(r'#(\d+)\b', layout)}
        decorative_ids = ids & {4, 58, 63, 66, 69}
        if not decorative_ids:
            return
        if self._row_type(row).lower() == 'illustration sheet':
            return

        referenced_tags: List[Tuple[Path, str]] = []
        for svg_path, content in svg_texts.items():
            for tag in re.findall(r'<image\b[^>]*>', content, re.IGNORECASE):
                if filename in tag:
                    referenced_tags.append((svg_path, tag))

        if 63 in decorative_ids:
            if Path(filename).suffix.lower() != '.png':
                self._illustration_issues.append((
                    'warning',
                    'sticker_not_png',
                    f"{filename} uses #63 transparent sticker / cutout but is not a PNG.",
                ))
            elif not self._png_has_alpha(project_path / 'images' / filename):
                self._illustration_issues.append((
                    'warning',
                    'sticker_no_alpha',
                    f"{filename} uses #63 transparent sticker / cutout but the PNG "
                    "does not appear to have an alpha channel.",
                ))

        if not referenced_tags:
            return

        if 69 in decorative_ids and not any('rotate(' in tag for _path, tag in referenced_tags):
            self._illustration_issues.append((
                'warning',
                'rotation_missing',
                f"{filename} declares #69 slight rotation but no referenced <image> "
                "tag contains rotate(...).",
            ))

        if 4 in decorative_ids and not self._has_off_canvas_reference(referenced_tags):
            self._illustration_issues.append((
                'warning',
                'edge_bleed_missing',
                f"{filename} declares #4 edge bleed but no referenced <image> appears "
                "to extend past the canvas edge.",
            ))

        if 58 in decorative_ids and not self._has_corner_fragment_reference(referenced_tags):
            self._illustration_issues.append((
                'warning',
                'corner_fragment_missing',
                f"{filename} declares #58 decorative corner fragment but no referenced "
                "<image> appears near a canvas corner.",
            ))

        if 66 in decorative_ids:
            content_scope = "\n".join(svg_texts.get(path, '') for path, _tag in referenced_tags)
            if '<linearGradient' not in content_scope and 'opacity' not in content_scope:
                self._illustration_issues.append((
                    'warning',
                    'fade_missing',
                    f"{filename} declares #66 fade into background but the referencing "
                    "SVG has no obvious gradient or opacity treatment.",
                ))

    @staticmethod
    def _png_has_alpha(path: Path) -> bool:
        """Return True when a PNG appears to carry transparent pixels."""
        if not path.exists():
            return False
        try:
            from PIL import Image as PILImage
            with PILImage.open(path) as img:
                if img.mode in {'RGBA', 'LA'}:
                    alpha = img.getchannel('A')
                    return alpha.getextrema()[0] < 255
                return 'transparency' in img.info
        except (ImportError, OSError, ValueError):
            return False

    @staticmethod
    def _parse_image_geometry(tag: str) -> Tuple[float, float, float, float] | None:
        """Extract x/y/width/height from an <image> tag."""
        values = {}
        for attr in ('x', 'y', 'width', 'height'):
            match = re.search(rf'\b{attr}\s*=\s*["\']([^"\']+)["\']', tag)
            if not match:
                return None
            try:
                values[attr] = float(match.group(1))
            except ValueError:
                return None
        return values['x'], values['y'], values['width'], values['height']

    @staticmethod
    def _parse_svg_viewbox(content: str) -> Tuple[float, float] | None:
        """Return root viewBox width/height from SVG content."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return None
        viewbox = root.get('viewBox')
        if not viewbox:
            return None
        values = _parse_viewbox_values(viewbox)
        if values is None:
            return None
        return values[2], values[3]

    @classmethod
    def _has_off_canvas_reference(cls, refs: List[Tuple[Path, str]]) -> bool:
        for svg_path, tag in refs:
            geometry = cls._parse_image_geometry(tag)
            if geometry is None:
                continue
            x, y, width, height = geometry
            try:
                content = svg_path.read_text(encoding='utf-8')
            except OSError:
                continue
            viewbox = cls._parse_svg_viewbox(content)
            if viewbox is None:
                continue
            vb_width, vb_height = viewbox
            if x < 0 or y < 0 or x + width > vb_width or y + height > vb_height:
                return True
        return False

    @classmethod
    def _has_corner_fragment_reference(cls, refs: List[Tuple[Path, str]]) -> bool:
        for svg_path, tag in refs:
            geometry = cls._parse_image_geometry(tag)
            if geometry is None:
                continue
            x, y, width, height = geometry
            try:
                content = svg_path.read_text(encoding='utf-8')
            except OSError:
                continue
            viewbox = cls._parse_svg_viewbox(content)
            if viewbox is None:
                continue
            vb_width, vb_height = viewbox
            near_left = x <= 40
            near_top = y <= 40
            near_right = x + width >= vb_width - 40
            near_bottom = y + height >= vb_height - 40
            if (near_left or near_right) and (near_top or near_bottom):
                return True
        return False

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
          identity. Zero-placeholder Layouts are valid. Legacy library templates
          still receive roster and placeholder checks while awaiting migration.
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
        legacy_structure_deferred = _legacy_template_structure_deferred(dir_path)
        mode_error_recorded = False
        if declared_structure_mode != 'structured' and not legacy_structure_deferred:
            mode_error_recorded = True
            if declared_structure_mode == 'template':
                mode_error = (
                    "legacy native_structure_mode: template is accepted only for "
                    "the explicit bundled-library migration set; restore this "
                    "workspace to native_structure_mode: structured"
                )
            else:
                mode_error = (
                    "design_spec.md frontmatter must declare "
                    "native_structure_mode: structured; only the explicit bundled "
                    "legacy migration set may temporarily declare template"
                )
            self._template_issues.append((
                'error',
                'explicit_structure_mode',
                mode_error,
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
                    and child.get('data-pptx-placeholder-bounds') is None
                ]
                if missing_bounds:
                    legacy_structure_detected = True
                    self._template_issues.append((
                        'error',
                        'placeholder_bounds_missing',
                        f"{svg_file.name}: reusable templates require "
                        "explicit design-zone data-pptx-placeholder-bounds; missing: "
                        + ', '.join(missing_bounds),
                    ))
            if native_contract_path.exists() or source_template_path.exists():
                legacy_structure_detected = True
                self._template_issues.append((
                    'error',
                    'legacy_native_structure_pair',
                    "legacy native_structure.json/source_template.pptx template "
                    "contracts must be restored through "
                    "skills/ppt-master/workflows/restore-pptx-structure.md",
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
                    "legacy template structure detected; run "
                    "skills/ppt-master/workflows/restore-pptx-structure.md before "
                    "Step 3 consumption",
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
            # current structured templates fail closed; allowlisted legacy
            # library specs retain the historical warning until migration.
            severity = (
                'error'
                if declared_structure_mode == 'structured'
                else 'warning'
            )
            self._template_issues.append((
                severity,
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
        3. ``DEFAULT_PLACEHOLDER_CONVENTION[<page_type_prefix>]``

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
        return cls.DEFAULT_PLACEHOLDER_CONVENTION.get(key)

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

        # Display warnings
        if result['warnings']:
            for warning in result['warnings'][:2]:  # Only show first 2 warnings
                print(f"   [WARN] {warning}")
            if len(result['warnings']) > 2:
                print(f"   ... and {len(result['warnings']) - 2} more warning(s)")

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

        if self.issue_types:
            print(f"\nIssue categories:")
            for issue_type, count in sorted(self.issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue_type}: {count}")

        # spec_lock drift aggregation (only printed when a lock was found)
        self._print_drift_summary()

        # Template-mode aggregation (orphan/missing roster + placeholder hints)
        self._print_template_summary()

        # Animation config aggregation.
        self._print_animation_summary()

        # Illustration strategy aggregation.
        self._print_illustration_summary()

        # Explicit PowerPoint master/layout structure aggregation.
        self._print_pptx_structure_summary()

        # Fix suggestions
        if self.summary['errors'] > 0 or self.summary['warnings'] > 0:
            print(f"\n[TIP] Common fixes:")
            print(f"  1. XML well-formedness: write typography as raw Unicode (—, ©, →, NBSP); escape XML reserved chars as &amp; &lt; &gt; &quot; &apos; — never use HTML named entities like &nbsp; &mdash; &copy;")
            print(f"  2. viewBox issues: root viewBox is the canvas authority (see references/canvas-formats.md)")
            print(f"  3. foreignObject: Use <text> + <tspan> for manual line breaks")
            print(f"  4. Font issues: use PPT-safe exported typefaces (e.g. Microsoft YaHei / Arial / Consolas)")

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

        print("\n[ILLUSTRATION] Illustration strategy checks")
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

    def _print_template_summary(self):
        """Aggregate template-mode roster / placeholder issues at the bottom.

        Errors land under the ``errors`` summary count (so the exit signal
        from ``main`` agrees), warnings under ``warnings``. Both are listed
        per file so the user can act on them directly.
        """
        if not self._template_issues:
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
        if not errors:
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

        structure_errors = [item for item in self._pptx_structure_issues if item[0] == 'error']
        structure_warnings = [item for item in self._pptx_structure_issues if item[0] == 'warning']
        self.summary['errors'] += len(structure_errors)
        self.summary['warnings'] += len(structure_warnings)
        for severity, _msg in self._pptx_structure_issues:
            self.issue_types[f'pptx_structure_{severity}'] += 1

    def _print_drift_summary(self):
        """Print spec_lock drift aggregation if any was observed.

        Values are sorted by file-count descending so frequent drift surfaces
        first. Frequent drift usually means spec_lock.md is missing entries
        the Strategist should have included; rare drift is more likely actual
        Executor drift and warrants SVG review.
        """
        if not self._lock_seen:
            return
        has_drift = any(self._drift_summary[cat] for cat in self._drift_summary)
        if not has_drift:
            print("\n[OK] spec_lock drift: none — all colors, fonts, and sizes are anchored to spec_lock.md")
            return

        print("\nspec_lock drift — values used outside spec_lock.md:")
        labels = [('colors', 'Colors'),
                  ('fonts', 'Font families'),
                  ('sizes', 'Font sizes')]
        for category, label in labels:
            items = self._drift_summary.get(category, {})
            if not items:
                continue
            entries = sorted(items.items(), key=lambda x: (-len(x[1]), x[0]))
            print(f"  {label}:")
            for val, files in entries:
                n = len(files)
                suffix = "file" if n == 1 else "files"
                print(f"    {val}  ({n} {suffix})")
        print(
            "Tip: frequent out-of-lock values usually mean spec_lock.md is missing\n"
            "     entries — extend the lock (scripts/update_spec.py or manual edit).\n"
            "     Rare ones are likely Executor drift — review the affected SVGs."
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


def print_usage() -> None:
    """Print CLI usage information."""
    print("PPT Master - SVG Quality Check Tool\n")
    print("Usage:")
    print("  python3 scripts/svg_quality_checker.py <svg_file>")
    print("  python3 scripts/svg_quality_checker.py <directory>")
    print("  python3 scripts/svg_quality_checker.py <workspace>/templates --template-mode")
    print("  python3 scripts/svg_quality_checker.py --all examples")
    print("\nExamples:")
    print("  python3 scripts/svg_quality_checker.py examples/project/svg_output/slide_01.svg")
    print("  python3 scripts/svg_quality_checker.py examples/project/svg_output")
    print("  python3 scripts/svg_quality_checker.py examples/project")
    print("  python3 scripts/svg_quality_checker.py templates/layouts/academic_defense/templates --template-mode")
    print("  python3 scripts/svg_quality_checker.py templates/decks/招商银行/templates --template-mode")
    print("\nOptions:")
    print("  --format <ppt169|ppt43|...>   Expected canvas format")
    print("  --template-mode               Validate a template workspace's templates/ directory:")
    print("                                  glob *.svg directly and skip spec_lock checks;")
    print("                                  always enforce roster consistency and emit placeholder hints.")
    print("                                  native_structure_mode: structured also enables complete")
    print("                                  per-file and cross-page structure validation. Legacy")
    print("                                  native_structure_mode: template defers only those structure")
    print("                                  checks until the bundled template library is migrated.")


def main() -> None:
    """Run the CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    if sys.argv[1] in {"-h", "--help", "help"}:
        print_usage()
        sys.exit(0)

    if sys.argv[1].startswith("--") and sys.argv[1] not in {"--all"}:
        print(f"[ERROR] Missing target before option: {sys.argv[1]}")
        print_usage()
        sys.exit(1)

    template_mode = '--template-mode' in sys.argv
    checker = SVGQualityChecker(template_mode=template_mode)

    # Parse arguments
    target = sys.argv[1]
    expected_format = None

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]

    # Execute check
    if target == '--all':
        # Check all example projects
        base_dir = sys.argv[2] if len(sys.argv) > 2 else 'examples'
        from project_utils import find_all_projects
        projects = find_all_projects(base_dir)

        for project in projects:
            print(f"\n{'=' * 80}")
            print(f"Checking project: {project.name}")
            print('=' * 80)
            checker.check_directory(str(project))
    else:
        checker.check_directory(target, expected_format)

    # Print summary
    checker.print_summary()

    # Export report (if specified)
    if '--export' in sys.argv:
        output_file = 'svg_quality_report.txt'
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        checker.export_report(output_file)

    # Return exit code
    if checker.summary['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
