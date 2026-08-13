#!/usr/bin/env python3
"""PPT Master stateless SVG contract checks.

Validates the SVG property surface shared with the native DrawingML exporter.
Each check receives an explicit XML root or source string and appends findings
to the supplied result dictionary.

Usage:
    Import checks from ``svg_quality.svg_contracts``.

Examples:
    from svg_quality.svg_contracts import check_paint_compatibility

Dependencies:
    Standard library plus local PPT Master SVG-to-PPTX modules.
"""

import copy
import math
import re
from collections import Counter, defaultdict
from typing import Dict, List
from xml.etree import ElementTree as ET

from .xml_support import (
    XLINK_NS,
    element_label as _element_label,
    local_name as _local_name,
)

try:
    from pptx_effects import (
        EFFECT_REASON_ATTR as _EFFECT_REASON_ATTR,
        EFFECT_STATUS_ATTR as _EFFECT_STATUS_ATTR,
        project_effect_status_errors as _project_effect_status_errors,
    )
except ImportError:
    _EFFECT_REASON_ATTR = "data-pptx-effect-reason"
    _EFFECT_STATUS_ATTR = "data-pptx-effect-status"
    _project_effect_status_errors = None

try:
    from svg_to_pptx.drawingml.utils import (
        DRAWINGML_TEXT_FONT_SIZE_MAX as _DRAWINGML_TEXT_FONT_SIZE_MAX,
        DRAWINGML_TEXT_FONT_SIZE_MIN as _DRAWINGML_TEXT_FONT_SIZE_MIN,
        PROJECT_OPACITY_PROPERTIES as _OPACITY_PROPERTIES,
        PROJECT_PAINT_PROPERTIES as _PAINT_PROPERTIES,
        PROJECT_PERCENTAGE_OPACITY_PROPERTIES as _PERCENTAGE_OPACITY_PROPERTIES,
        format_project_geometry_length as _format_project_geometry_length,
        format_project_image_aspect_ratio as _format_project_image_aspect_ratio,
        format_project_opacity as _format_project_opacity,
        font_px_to_hpt as _font_px_to_hpt,
        is_canonical_project_geometry_length as _is_canonical_project_geometry_length,
        is_project_opacity_default_form as _is_project_opacity_default_form,
        is_project_paint_default_form as _is_project_paint_default_form,
        iter_project_geometry_lengths as _iter_project_geometry_lengths,
        iter_project_image_aspect_ratios as _iter_project_image_aspect_ratios,
        iter_project_opacities as _iter_project_opacities,
        iter_project_paints as _iter_project_paints,
        iter_project_stroke_styles as _iter_project_stroke_styles,
        iter_project_transforms as _iter_project_transforms,
        noncanonical_stroke_dash_numbers as _noncanonical_stroke_dash_numbers,
        noncanonical_transform_numbers as _noncanonical_transform_numbers,
        parse_inline_style as _parse_inline_style,
        parse_project_geometry_length as _parse_project_geometry_length,
        parse_project_image_aspect_ratio as _parse_project_image_aspect_ratio,
        parse_project_opacity as _parse_project_opacity,
        parse_project_paint as _parse_project_paint,
        parse_project_stroke_dasharray as _parse_project_stroke_dasharray,
        parse_project_stroke_enum as _parse_project_stroke_enum,
        parse_svg_length as _parse_export_length,
        project_definition_errors as _project_definition_errors,
        project_filter_errors as _project_filter_errors,
        project_gradient_errors as _project_gradient_errors,
        project_image_aspect_ratio_errors as _project_image_aspect_ratio_errors,
        project_mask_errors as _project_mask_errors,
        project_marker_errors as _project_marker_errors,
        project_opacity_errors as _project_opacity_errors,
        project_paint_errors as _project_paint_errors,
        project_paint_reference_errors as _project_paint_reference_errors,
        project_stroke_style_errors as _project_stroke_style_errors,
        project_transform_errors as _project_transform_errors,
    )
except ImportError:
    _DRAWINGML_TEXT_FONT_SIZE_MAX = None
    _DRAWINGML_TEXT_FONT_SIZE_MIN = None
    _OPACITY_PROPERTIES = None
    _PAINT_PROPERTIES = None
    _PERCENTAGE_OPACITY_PROPERTIES = None
    _format_project_geometry_length = None
    _format_project_image_aspect_ratio = None
    _format_project_opacity = None
    _font_px_to_hpt = None
    _is_canonical_project_geometry_length = None
    _is_project_opacity_default_form = None
    _is_project_paint_default_form = None
    _iter_project_geometry_lengths = None
    _iter_project_image_aspect_ratios = None
    _iter_project_opacities = None
    _iter_project_paints = None
    _iter_project_stroke_styles = None
    _iter_project_transforms = None
    _noncanonical_stroke_dash_numbers = None
    _noncanonical_transform_numbers = None
    _parse_inline_style = None
    _parse_project_geometry_length = None
    _parse_project_image_aspect_ratio = None
    _parse_project_opacity = None
    _parse_project_paint = None
    _parse_project_stroke_dasharray = None
    _parse_project_stroke_enum = None
    _parse_export_length = None
    _project_definition_errors = None
    _project_filter_errors = None
    _project_gradient_errors = None
    _project_image_aspect_ratio_errors = None
    _project_mask_errors = None
    _project_marker_errors = None
    _project_opacity_errors = None
    _project_paint_errors = None
    _project_paint_reference_errors = None
    _project_stroke_style_errors = None
    _project_transform_errors = None

try:
    from svg_to_pptx.drawingml.paths import (
        iter_project_freeform_geometry as _iter_project_freeform_geometry,
        noncanonical_path_numbers as _noncanonical_path_numbers,
        noncanonical_points_numbers as _noncanonical_points_numbers,
        project_gradient_geometry_errors as _project_gradient_geometry_errors,
    )
except ImportError:
    _iter_project_freeform_geometry = None
    _noncanonical_path_numbers = None
    _noncanonical_points_numbers = None
    _project_gradient_geometry_errors = None

try:
    from svg_to_pptx.drawingml.elements import (
        project_clip_path_errors as _project_clip_path_errors,
        project_nested_svg_crop_errors as _project_nested_svg_crop_errors,
    )
except ImportError:
    _project_clip_path_errors = None
    _project_nested_svg_crop_errors = None

try:
    from svg_to_pptx.drawingml.text_properties import (
        project_text_property_diagnostics as _project_text_property_diagnostics,
    )
except ImportError:
    _project_text_property_diagnostics = None

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

_CANONICAL_PAINT_ALPHA_PROPERTY = {
    "fill": "fill-opacity",
    "stroke": "stroke-opacity",
    "stop-color": "stop-opacity",
    "flood-color": "flood-opacity",
}
_SUPPORTED_INLINE_STYLE_PROPERTIES = frozenset({
    "cx", "cy", "fill", "fill-opacity", "filter", "flood-color",
    "flood-opacity", "font-family", "font-size", "font-style", "font-weight",
    "height", "letter-spacing", "opacity", "r", "rx", "ry",
    "shape-rendering", "stop-color", "stop-opacity", "stroke",
    "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "stroke-opacity",
    "stroke-width", "text-anchor", "text-decoration", "vector-effect",
    "width", "x", "y",
})
_BAKE_REQUIRED_VISUAL_PROPERTIES = frozenset({
    "backdrop-filter",
    "isolation",
    "mix-blend-mode",
})
_SHARED_FAIL_CLOSED_STYLE_PROPERTIES = frozenset({"mask"})


def check_forbidden_elements(
    content: str,
    root: ET.Element,
    result: Dict,
) -> None:
    """Check forbidden elements (blocklist)"""
    content_lower = content.lower()
    elems = list(root.iter())
    local_names = {_local_name(elem).lower() for elem in elems}

    # ============================================================
    # Forbidden elements blocklist - PPT incompatible
    # ============================================================

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
    # Text / fonts
    if 'textpath' in local_names:
        result['errors'].append("Detected forbidden <textPath> element (path text is incompatible with PPT)")
    if '@font-face' in content_lower:
        result['errors'].append("Detected forbidden @font-face (use system font stack)")

    # Animation / interaction
    if any(name.startswith('animate') for name in local_names):
        result['errors'].append(
            "Detected forbidden SMIL animation element <animate*> "
            "(SVG animations are not exported)"
        )
    if 'set' in local_names:
        result['errors'].append("Detected forbidden SMIL animation element <set> (SVG animations are not exported)")
    if 'script' in local_names:
        result['errors'].append("Detected forbidden <script> element (scripts and event handlers forbidden)")
    if re.search(r'\bon\w+\s*=', content):  # onclick, onload etc.
        result['errors'].append("Detected forbidden event attributes (e.g., onclick, onload)")

    # Other discouraged elements
    if 'iframe' in local_names:
        result['errors'].append("Detected <iframe> element (should not appear in SVG)")


def check_paint_compatibility(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject unsupported paint and advise one generated-SVG spelling.

    The exporter parser owns compatibility. Any paint it can parse remains
    valid input; the checker only warns when that spelling differs from the
    generated-SVG default (uppercase ``#RRGGBB`` plus explicit alpha).
    """
    helpers = (
        _PAINT_PROPERTIES,
        _PERCENTAGE_OPACITY_PROPERTIES,
        _format_project_opacity,
        _is_project_paint_default_form,
        _iter_project_paints,
        _parse_inline_style,
        _parse_project_opacity,
        _parse_project_paint,
        _project_paint_errors,
    )
    if any(helper is None for helper in helpers):
        result['warnings'].append(
            "Unable to import svg_to_pptx paint parsers; skipped paint syntax check"
        )
        return

    result['errors'].extend(_project_paint_errors(root))
    recommendations: Counter[tuple[str, str, str]] = Counter()
    recommendation_examples: Dict[tuple[str, str, str], List[str]] = defaultdict(list)

    def remember_example(store: Dict, key: tuple, label: str) -> None:
        labels = store[key]
        if label not in labels and len(labels) < 3:
            labels.append(label)

    for elem, name, raw_value, source in _iter_project_paints(root):
        try:
            kind, normalized, color_alpha = _parse_project_paint(
                raw_value,
                name,
            )
        except ValueError:
            continue
        if _is_project_paint_default_form(raw_value, name):
            continue

        source_label = f'{_element_label(elem)} {source}'
        if kind == 'none':
            replacement = f'{name}="none"'
        elif kind == 'reference':
            replacement = f'{name}="url(#{normalized})"'
        elif name in {'fill', 'stroke'} and raw_value.strip().lower() == 'transparent':
            replacement = f'{name}="none"'
        else:
            replacement = f'{name}="#{normalized}"'
            alpha_name = _CANONICAL_PAINT_ALPHA_PROPERTY.get(name)
            if color_alpha < 1.0 and alpha_name is not None:
                style_values = _parse_inline_style(elem.get('style'))
                existing_alpha_raw = (
                    style_values.get(alpha_name) or elem.get(alpha_name)
                )
                if existing_alpha_raw is None:
                    existing_alpha = 1.0
                else:
                    try:
                        existing_alpha = _parse_project_opacity(
                            existing_alpha_raw,
                            allow_percentage=(
                                alpha_name in _PERCENTAGE_OPACITY_PROPERTIES
                            ),
                        )
                    except ValueError:
                        existing_alpha = None
                effective_alpha = (
                    color_alpha * existing_alpha
                    if existing_alpha is not None else color_alpha
                )
                replacement += (
                    f' {alpha_name}="'
                    f'{_format_project_opacity(effective_alpha)}"'
                )
            elif color_alpha < 1.0:
                replacement += (
                    '; put alpha on the matching pattern child fill/stroke '
                    'opacity'
                )

        key = (name, raw_value, replacement)
        recommendations[key] += 1
        remember_example(recommendation_examples, key, source_label)

    for (name, raw_value, replacement), count in sorted(recommendations.items()):
        examples = ', '.join(
            recommendation_examples[(name, raw_value, replacement)]
        )
        result['warnings'].append(
            f"Recommendation: {name}={raw_value!r} is converter-compatible "
            f"in {count} location(s) ({examples}); generated SVG should "
            f"prefer {replacement}. No change is required for export."
        )


def check_reference_spelling(root: ET.Element, result: Dict) -> None:
    """Recommend SVG 2 ``href`` while retaining legacy XLink input."""
    labels = []
    xlink_href = f'{{{XLINK_NS}}}href'
    for elem in root.iter():
        if _local_name(elem).lower() not in {'a', 'image', 'use'}:
            continue
        if elem.get(xlink_href) is not None:
            labels.append(_element_label(elem))
    if labels:
        examples = ', '.join(labels[:3])
        suffix = f' (+{len(labels) - 3} more)' if len(labels) > 3 else ''
        result['warnings'].append(
            f"Recommendation: legacy xlink:href is supported on {len(labels)} "
            f"reference(s) ({examples}{suffix}); generated SVG should prefer "
            "href. No change is required for export."
        )


def check_opacity_values(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject malformed opacity and advise generated-SVG values."""
    helpers = (
        _PERCENTAGE_OPACITY_PROPERTIES,
        _format_project_opacity,
        _is_project_opacity_default_form,
        _iter_project_opacities,
        _parse_inline_style,
        _parse_project_opacity,
        _project_opacity_errors,
    )
    if any(helper is None for helper in helpers):
        result['warnings'].append(
            "Unable to import svg_to_pptx opacity validators; native "
            "export will still validate opacity syntax."
        )
        return

    result['errors'].extend(_project_opacity_errors(root))
    recommendations: Counter[tuple[str, str, str]] = Counter()
    examples: Dict[tuple[str, str, str], List[str]] = defaultdict(list)
    fidelity_warnings: set[str] = set()

    for elem, property_name, raw, source in _iter_project_opacities(root):
        try:
            value = _parse_project_opacity(
                raw,
                allow_percentage=(
                    property_name in _PERCENTAGE_OPACITY_PROPERTIES
                ),
            )
        except ValueError:
            continue
        if _is_project_opacity_default_form(raw):
            continue
        normalized = _format_project_opacity(value)
        key = (property_name, raw, normalized)
        recommendations[key] += 1
        label = f'{_element_label(elem)} {source}'
        if label not in examples[key] and len(examples[key]) < 3:
            examples[key].append(label)

    for elem in root.iter():
        if _local_name(elem).lower() != 'g':
            continue
        style_values = _parse_inline_style(elem.get('style'))
        raw_opacity = (
            style_values['opacity']
            if 'opacity' in style_values else elem.get('opacity')
        )
        if raw_opacity is None:
            continue
        try:
            opacity = _parse_project_opacity(raw_opacity)
        except ValueError:
            continue
        if opacity < 1.0:
            fidelity_warnings.add(
                f"Fidelity warning: {_element_label(elem)} uses group "
                f"opacity={raw_opacity!r}. The converter distributes this "
                "alpha to descendants and cannot preserve isolated group "
                "compositing; generated SVG should prefer descendant alpha. "
                "Existing input remains convertible and does not require "
                "modification."
            )

    for (property_name, raw, normalized), count in sorted(
        recommendations.items()
    ):
        shown_examples = ', '.join(
            examples[(property_name, raw, normalized)]
        )
        result['warnings'].append(
            f"Recommendation: {property_name}={raw!r} is "
            f"converter-compatible in {count} location(s) "
            f"({shown_examples}); generated SVG should prefer "
            f'{property_name}="{normalized}". No change is required '
            "for export."
        )
    result['warnings'].extend(sorted(fidelity_warnings))


def check_authoring_property_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Validate inline CSS and attributes against the authoring surface."""
    errors: set[str] = set()
    validated_value_properties = set(_OPACITY_PROPERTIES or ())
    validated_value_properties.update(_PAINT_PROPERTIES or ())
    for elem in root.iter():
        label = _element_label(elem)
        for fragment in (elem.get('style') or '').split(';'):
            fragment = fragment.strip()
            if not fragment:
                continue
            if ':' not in fragment:
                if fragment.lower() not in validated_value_properties:
                    errors.add(
                        f"{label} has malformed inline style declaration "
                        f"{fragment!r}"
                    )
                continue
            name, value = fragment.split(':', 1)
            name = name.strip().lower()
            value = value.strip()
            if not name or not value:
                if name not in validated_value_properties:
                    errors.add(
                        f"{label} has malformed inline style declaration "
                        f"{fragment!r}"
                    )
                continue
            if name in _BAKE_REQUIRED_VISUAL_PROPERTIES:
                errors.add(
                    f"{label} uses Bake-required visual property {name!r}; "
                    "bake the effect or rebuild it with supported geometry"
                )
            elif (
                name not in _SUPPORTED_INLINE_STYLE_PROPERTIES
                and name not in _SHARED_FAIL_CLOSED_STYLE_PROPERTIES
            ):
                errors.add(
                    f"{label} uses unsupported inline style property {name!r}; "
                    "native PPTX export would ignore it"
                )
            if '!important' in value.lower():
                errors.add(
                    f"{label} inline style property {name!r} cannot use !important"
                )

        for attr_name in elem.attrib:
            local_attr = attr_name.rsplit('}', 1)[-1]
            if local_attr in _BAKE_REQUIRED_VISUAL_PROPERTIES:
                errors.add(
                    f"{label} uses Bake-required visual attribute {local_attr!r}; "
                    "bake the effect or rebuild it with supported geometry"
                )

    result['errors'].extend(sorted(errors))


def check_text_property_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Validate text property names and values with the export contract."""
    if _project_text_property_diagnostics is None:
        result['warnings'].append(
            "Unable to import the shared text-property validator; native "
            "export will still validate text properties."
        )
        return

    errors: set[str] = set()
    recommendations: Counter[tuple[str, str, str]] = Counter()
    examples: Dict[tuple[str, str, str], List[str]] = defaultdict(list)
    for diagnostic in _project_text_property_diagnostics(root):
        if diagnostic.severity == 'error':
            errors.add(diagnostic.message)
            continue
        if diagnostic.canonical is None:
            continue
        key = (
            diagnostic.name,
            diagnostic.raw,
            diagnostic.canonical,
        )
        recommendations[key] += 1
        if (
            diagnostic.label not in examples[key]
            and len(examples[key]) < 3
        ):
            examples[key].append(diagnostic.label)

    result['errors'].extend(sorted(errors))
    for (name, raw, canonical), count in sorted(recommendations.items()):
        shown_examples = ', '.join(examples[(name, raw, canonical)])
        result['warnings'].append(
            f"Recommendation: text property {name}={raw!r} is "
            f"converter-compatible in {count} location(s) "
            f"({shown_examples}); generated SVG should prefer "
            f'{name}="{canonical}". No change is required for export.'
        )


def check_definition_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Require conditional definitions to be direct, uniquely identified defs."""
    if _project_definition_errors is None:
        result['warnings'].append(
            "Unable to import the shared definition validator; native "
            "export will still validate local definitions."
        )
        return
    result['errors'].extend(_project_definition_errors(root))


def check_paint_reference_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Validate paint-server resolution and native target contexts."""
    if _project_paint_reference_errors is None:
        result['warnings'].append(
            "Unable to import the shared paint-reference validator; native "
            "export will still validate local paint references."
        )
        return
    result['errors'].extend(_project_paint_reference_errors(root))


def check_marker_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Validate marker references against the native line-end contract."""
    if _project_marker_errors is None:
        result['warnings'].append(
            'Unable to import the shared marker validator; native export '
            'will still validate line-end markers.'
        )
        return
    result['errors'].extend(_project_marker_errors(root))


def check_clip_path_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Validate image clip paths against the native picture geometry mapping."""
    if _project_clip_path_errors is None:
        result['errors'].append(
            'Unable to import the clip-path validator; cannot verify '
            'native picture geometry references'
        )
        return
    result['errors'].extend(_project_clip_path_errors(root))


def check_mask_contract(root: ET.Element, result: Dict) -> None:
    """Reject SVG masks through the native exporter's shared validator."""
    if _project_mask_errors is None:
        result['errors'].append(
            'Unable to import the shared mask validator; cannot verify '
            'that native PPTX export will preserve all visible effects'
        )
        return
    result['errors'].extend(_project_mask_errors(root))


def check_filter_effects(root: ET.Element, result: Dict) -> None:
    """Validate filters against the native shadow/glow approximation."""
    if _project_filter_errors is None:
        result['warnings'].append(
            "Unable to import the shared filter validator; native export "
            "will still validate shadow/glow filters."
        )
        return
    result['errors'].extend(_project_filter_errors(root))


def check_imported_effect_status(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject source PPTX effects that have no faithful SVG mapping."""
    if _project_effect_status_errors is None:
        if any(
            elem.get(_EFFECT_STATUS_ATTR) is not None
            or elem.get(_EFFECT_REASON_ATTR) is not None
            for elem in root.iter()
        ):
            result['errors'].append(
                'Unable to import the PPTX effect-status validator; '
                'cannot verify imported effect fidelity'
            )
        return
    result['errors'].extend(_project_effect_status_errors(root))


def check_gradient_interfaces(root: ET.Element, result: Dict) -> None:
    """Validate the normalized native gradient authoring interface."""
    if (
        _project_gradient_errors is None
        or _project_gradient_geometry_errors is None
    ):
        result['warnings'].append(
            "Unable to import the shared gradient validator; native export "
            "will still validate gradient definitions."
        )
        return
    gradient_errors = set(_project_gradient_errors(root))
    gradient_errors.update(_project_gradient_geometry_errors(root))
    if (
        _expand_local_use_references is not None
        and _UseExpansionError is not None
    ):
        expanded_root = copy.deepcopy(root)
        try:
            _expand_local_use_references(expanded_root)
        except _UseExpansionError:
            # The local-reference check owns the actionable diagnostic.
            pass
        else:
            gradient_errors.update(
                _project_gradient_geometry_errors(expanded_root)
            )
    result['errors'].extend(sorted(gradient_errors))


def check_geometry_length_values(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject invalid project geometry and advise the unitless spelling."""
    if (
        _format_project_geometry_length is None
        or _is_canonical_project_geometry_length is None
        or _iter_project_geometry_lengths is None
        or _parse_project_geometry_length is None
    ):
        result['warnings'].append(
            "Unable to import svg_to_pptx geometry length validators; "
            "native export will still validate project geometry."
        )
        return

    errors: set[str] = set()
    recommendations: Counter[tuple[str, str, str]] = Counter()
    examples: Dict[tuple[str, str, str], List[str]] = defaultdict(list)

    for elem, attribute, raw, source in _iter_project_geometry_lengths(root):
        label = f'{_element_label(elem)} {source}'
        try:
            value = _parse_project_geometry_length(raw, attribute)
        except ValueError as exc:
            errors.add(f"{label} {attribute}={raw!r}: {exc}")
            continue
        if _is_canonical_project_geometry_length(raw):
            continue
        normalized = _format_project_geometry_length(value)
        key = (attribute, raw, normalized)
        recommendations[key] += 1
        if label not in examples[key] and len(examples[key]) < 3:
            examples[key].append(label)

    result['errors'].extend(sorted(errors))
    for (attribute, raw, normalized), count in sorted(recommendations.items()):
        shown_examples = ', '.join(examples[(attribute, raw, normalized)])
        result['warnings'].append(
            f"Recommendation: project geometry {attribute}={raw!r} is "
            f"converter-compatible in {count} location(s) ({shown_examples}); "
            f"generated SVG should prefer the unitless px spelling "
            f'{attribute}="{normalized}". No change is required for export.'
        )


def check_stroke_style_values(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject invalid line styles and advise project-canonical spellings."""
    helpers = (
        _format_project_geometry_length,
        _is_canonical_project_geometry_length,
        _iter_project_stroke_styles,
        _noncanonical_stroke_dash_numbers,
        _parse_project_geometry_length,
        _parse_project_stroke_dasharray,
        _parse_project_stroke_enum,
        _project_stroke_style_errors,
    )
    if any(helper is None for helper in helpers):
        result['warnings'].append(
            "Unable to import svg_to_pptx line-style validators; native "
            "export will still validate line-presentation syntax."
        )
        return

    result['errors'].extend(_project_stroke_style_errors(root))
    recommendations: Counter[tuple[str, str, str, str]] = Counter()
    examples: Dict[tuple[str, str, str, str], List[str]] = defaultdict(list)

    for elem, attribute, raw, source in _iter_project_stroke_styles(root):
        label = f'{_element_label(elem)} {source}'
        normalized = None
        reason = ''

        if attribute == 'stroke-dasharray':
            try:
                parsed = _parse_project_stroke_dasharray(
                    raw,
                    allow_zero_gap=True,
                )
                noncanonical = _noncanonical_stroke_dash_numbers(raw)
            except ValueError:
                continue
            if parsed is None:
                if raw != 'none':
                    normalized = 'none'
                    reason = 'remove surrounding whitespace'
            else:
                preset, values = parsed
                longer_custom = preset is None and len(values) > 2
                if noncanonical or longer_custom or raw != raw.strip():
                    kept_values = values[:2] if longer_custom else values
                    normalized = ' '.join(
                        _format_project_geometry_length(value)
                        for value in kept_values
                    )
                    reasons = []
                    if noncanonical:
                        reasons.append('use ordinary decimal numbers')
                    if longer_custom:
                        reasons.append(
                            'make the first-pair export normalization explicit'
                        )
                    if raw != raw.strip():
                        reasons.append('remove surrounding whitespace')
                    reason = '; '.join(reasons)
        elif attribute == 'stroke-dashoffset':
            try:
                value = _parse_project_geometry_length(raw, attribute)
            except ValueError:
                continue
            if not _is_canonical_project_geometry_length(raw):
                normalized = _format_project_geometry_length(value)
                reason = 'use the unitless px spelling'
        else:
            try:
                value = _parse_project_stroke_enum(attribute, raw)
            except ValueError:
                continue
            if raw != value:
                normalized = value
                reason = 'remove surrounding whitespace'

        if normalized is None:
            continue
        key = (attribute, raw, normalized, reason)
        recommendations[key] += 1
        if label not in examples[key] and len(examples[key]) < 3:
            examples[key].append(label)

    for (attribute, raw, normalized, reason), count in sorted(
        recommendations.items()
    ):
        shown_examples = ', '.join(
            examples[(attribute, raw, normalized, reason)]
        )
        result['warnings'].append(
            f"Recommendation: line style {attribute}={raw!r} is "
            f"converter-compatible in {count} location(s) "
            f"({shown_examples}); generated SVG should prefer "
            f'{attribute}="{normalized}" to {reason}. No change is '
            "required for export."
        )


def check_image_aspect_ratio_values(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject ambiguous image fit/crop values and advise canonical forms."""
    helpers = (
        _format_project_image_aspect_ratio,
        _iter_project_image_aspect_ratios,
        _parse_project_image_aspect_ratio,
        _project_image_aspect_ratio_errors,
    )
    if any(helper is None for helper in helpers):
        result['warnings'].append(
            "Unable to import svg_to_pptx image aspect-ratio validators; "
            "native export will still validate image fit/crop syntax."
        )
        return

    result['errors'].extend(_project_image_aspect_ratio_errors(root))
    recommendations: Counter[tuple[str, str]] = Counter()
    examples: Dict[tuple[str, str], List[str]] = defaultdict(list)

    for elem, raw in _iter_project_image_aspect_ratios(root):
        try:
            align, mode = _parse_project_image_aspect_ratio(raw)
        except ValueError:
            continue
        normalized = _format_project_image_aspect_ratio(align, mode)
        if raw == normalized:
            continue
        key = (raw, normalized)
        recommendations[key] += 1
        label = _element_label(elem)
        if label not in examples[key] and len(examples[key]) < 3:
            examples[key].append(label)

    for (raw, normalized), count in sorted(recommendations.items()):
        shown_examples = ', '.join(examples[(raw, normalized)])
        result['warnings'].append(
            f"Recommendation: image preserveAspectRatio={raw!r} is "
            f"converter-compatible in {count} location(s) "
            f"({shown_examples}); generated SVG should prefer "
            f'preserveAspectRatio="{normalized}". No change is required '
            "for export."
        )


def check_nested_svg_crop_contract(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reserve nested SVG for the imported picture-crop transport."""
    if _project_nested_svg_crop_errors is None:
        result['errors'].append(
            'Unable to import the nested SVG crop validator; cannot '
            'verify imported picture-crop wrappers'
        )
        return
    result['errors'].extend(_project_nested_svg_crop_errors(root))


def check_freeform_geometry_values(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject malformed path/points syntax and advise decimal spelling."""
    helpers = (
        _format_project_geometry_length,
        _iter_project_freeform_geometry,
        _noncanonical_path_numbers,
        _noncanonical_points_numbers,
    )
    if any(helper is None for helper in helpers):
        result['warnings'].append(
            "Unable to import svg_to_pptx freeform geometry validators; "
            "native export will still validate path and points syntax."
        )
        return

    errors: set[str] = set()
    recommendations: Counter[tuple[str, str, str]] = Counter()
    examples: Dict[tuple[str, str, str], List[str]] = defaultdict(list)

    for elem, attribute, raw, min_points in _iter_project_freeform_geometry(root):
        label = _element_label(elem)
        try:
            if raw is None:
                tag = _local_name(elem)
                raise ValueError(f'<{tag}> requires {attribute}')
            if attribute == 'd':
                compatible_numbers = _noncanonical_path_numbers(raw)
            else:
                required_points = min_points or 2
                compatible_numbers = _noncanonical_points_numbers(
                    raw,
                    min_points=required_points,
                )
        except ValueError as exc:
            errors.add(f'{label} {attribute}: {exc}')
            continue

        for number in compatible_numbers:
            normalized = _format_project_geometry_length(float(number))
            key = (attribute, number, normalized)
            recommendations[key] += 1
            if label not in examples[key] and len(examples[key]) < 3:
                examples[key].append(label)

    result['errors'].extend(sorted(errors))
    for (attribute, raw, normalized), count in sorted(recommendations.items()):
        shown_examples = ', '.join(examples[(attribute, raw, normalized)])
        result['warnings'].append(
            f"Recommendation: freeform geometry {attribute} numeric token "
            f"{raw!r} is converter-compatible in {count} occurrence(s) "
            f"({shown_examples}); generated SVG should prefer the ordinary "
            f"decimal spelling {normalized!r}. No change is required for export."
        )


def check_transform_values(
    root: ET.Element,
    result: Dict,
) -> None:
    """Reject invalid transforms and advise ordinary decimal spelling."""
    helpers = (
        _format_project_geometry_length,
        _iter_project_transforms,
        _noncanonical_transform_numbers,
        _project_transform_errors,
    )
    if any(helper is None for helper in helpers):
        result['warnings'].append(
            "Unable to import svg_to_pptx transform validators; "
            "native export will still validate transform syntax."
        )
        return

    transform_errors = set(_project_transform_errors(root))
    if (
        not transform_errors
        and _expand_local_use_references is not None
        and _UseExpansionError is not None
    ):
        expanded_root = copy.deepcopy(root)
        try:
            _expand_local_use_references(expanded_root)
        except _UseExpansionError:
            # The local-reference check owns the actionable diagnostic.
            pass
        else:
            transform_errors.update(_project_transform_errors(expanded_root))
    result['errors'].extend(
        f'Invalid SVG transform: {error}'
        for error in sorted(transform_errors)
    )

    recommendations: Counter[tuple[str, str]] = Counter()
    examples: Dict[tuple[str, str], List[str]] = defaultdict(list)
    for elem, raw in _iter_project_transforms(root):
        try:
            compatible_numbers = _noncanonical_transform_numbers(raw)
        except ValueError:
            continue
        for number in compatible_numbers:
            normalized = _format_project_geometry_length(float(number))
            key = (number, normalized)
            recommendations[key] += 1
            label = _element_label(elem)
            if label not in examples[key] and len(examples[key]) < 3:
                examples[key].append(label)

    for (raw, normalized), count in sorted(recommendations.items()):
        shown_examples = ', '.join(examples[(raw, normalized)])
        result['warnings'].append(
            f"Recommendation: transform numeric token {raw!r} is "
            f"converter-compatible in {count} occurrence(s) "
            f"({shown_examples}); generated SVG should prefer the ordinary "
            f"decimal spelling {normalized!r}. No change is required for export."
        )


def check_font_size_values(content: str, result: Dict) -> None:
    """Keep supported font-size units compatible and recommend unitless px."""
    canonical_re = re.compile(r'^(?:\d+(?:\.\d+)?|\.\d+)$')
    values = set()

    for match in re.finditer(r'\bfont-size\s*=\s*(["\'])(.*?)\1', content, re.IGNORECASE):
        values.add(match.group(2).strip())

    for match in re.finditer(r'\bfont-size\s*:\s*([^;"\']+)', content, re.IGNORECASE):
        values.add(match.group(1).strip())

    if _parse_export_length is None:
        result['warnings'].append(
            "Unable to import svg_to_pptx length parser; skipped font-size syntax check"
        )
        return

    unsupported = set()
    drawingml_out_of_range = set()
    compatible_noncanonical = set()
    for raw in values:
        try:
            parsed_px = _parse_export_length(raw, math.nan, font_size=16)
        except (TypeError, ValueError):
            unsupported.add(raw)
            continue
        if not math.isfinite(parsed_px) or parsed_px < 0:
            unsupported.add(raw)
            continue
        if _font_px_to_hpt is not None:
            try:
                _font_px_to_hpt(parsed_px)
            except ValueError:
                drawingml_out_of_range.add(raw)
                continue
        if not canonical_re.fullmatch(raw):
            compatible_noncanonical.add(raw)

    if unsupported:
        shown_values = sorted(unsupported)
        shown = ', '.join(shown_values[:5])
        more = len(shown_values) - 5
        suffix = f" (+{more} more)" if more > 0 else ""
        result['errors'].append(
            f"Unsupported font-size value(s): {shown}{suffix}. Use a finite "
            "non-negative SVG length supported by svg_to_pptx."
        )

    if drawingml_out_of_range:
        shown_values = sorted(drawingml_out_of_range)
        shown = ', '.join(shown_values[:5])
        more = len(shown_values) - 5
        suffix = f" (+{more} more)" if more > 0 else ""
        result['errors'].append(
            f"font-size value(s) {shown}{suffix} are outside the DrawingML "
            f"range sz={_DRAWINGML_TEXT_FONT_SIZE_MIN}.."
            f"{_DRAWINGML_TEXT_FONT_SIZE_MAX} (1..4000pt); PowerPoint would "
            "repair the exported file. Do not use tiny transparent text as "
            "a placeholder carrier: leave a text carrier blank or use the "
            "composite object proxy contract."
        )

    if compatible_noncanonical:
        shown_values = sorted(compatible_noncanonical)
        shown = ', '.join(shown_values[:5])
        more = len(shown_values) - 5
        suffix = f" (+{more} more)" if more > 0 else ""
        result['warnings'].append(
            f"Recommendation: font-size value(s) {shown}{suffix} are "
            "converter-compatible; generated SVG should prefer unitless px "
            "values such as font-size=\"28\". No change is required for export."
        )
