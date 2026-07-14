"""Closed project grammar for SVG text presentation properties.

The project accepts a deliberately small SVG text surface that maps
deterministically to editable DrawingML.  This module is shared by the quality
checker and the converter so unsupported values cannot be silently normalized
by one route and rejected by the other.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from .utils import font_px_to_hpt, parse_svg_length


_SVG_TEXT_PROPERTIES = frozenset({
    'font-weight',
    'font-style',
    'text-anchor',
    'letter-spacing',
    'text-decoration',
})

_TEXT_DECLARATION_PROPERTIES = _SVG_TEXT_PROPERTIES | {
    'font-family',
    'font-size',
}

_TEXT_INHERITANCE_TARGETS = frozenset({'svg', 'g', 'text', 'tspan'})

_UNSUPPORTED_TEXT_PROPERTIES = frozenset({
    'alignment-baseline',
    'baseline-shift',
    'direction',
    'dominant-baseline',
    'font-kerning',
    'font-feature-settings',
    'font-size-adjust',
    'font-stretch',
    'font-synthesis',
    'font-variant',
    'font-variation-settings',
    'font',
    'hyphens',
    'kerning',
    'line-height',
    'overflow-wrap',
    'text-align',
    'text-align-last',
    'text-indent',
    'text-rendering',
    'text-shadow',
    'text-transform',
    'unicode-bidi',
    'vertical-align',
    'white-space',
    'word-spacing',
    'word-break',
    'writing-mode',
})

_TEXT_DIRECT_ATTRIBUTES = frozenset({
    'fill',
    'fill-opacity',
    'filter',
    'font-family',
    'font-size',
    'font-style',
    'font-weight',
    'id',
    'letter-spacing',
    'opacity',
    'stroke',
    'stroke-opacity',
    'stroke-width',
    'style',
    'text-anchor',
    'text-decoration',
    'transform',
    'x',
    'xml:space',
    'y',
})

_TSPAN_DIRECT_ATTRIBUTES = frozenset({
    'dx',
    'dy',
    'fill',
    'fill-opacity',
    'font-family',
    'font-size',
    'font-style',
    'font-weight',
    'id',
    'letter-spacing',
    'opacity',
    'stroke',
    'stroke-opacity',
    'stroke-width',
    'style',
    'text-decoration',
    'x',
    'xml:space',
    'y',
})

_TEXT_INLINE_PROPERTIES = frozenset({
    'fill',
    'fill-opacity',
    'font-family',
    'font-size',
    'font-style',
    'font-weight',
    'letter-spacing',
    'opacity',
    'shape-rendering',
    'stroke',
    'stroke-opacity',
    'stroke-width',
    'text-anchor',
    'text-decoration',
})

_TSPAN_INLINE_PROPERTIES = _TEXT_INLINE_PROPERTIES - {'text-anchor'}

_CANONICAL_DECIMAL_RE = re.compile(r'^-?(?:\d+(?:\.\d+)?|\.\d+)$')
_COMPATIBLE_LETTER_SPACING_RE = re.compile(
    r'(-?(?:\d+(?:\.\d+)?|\.\d+))(px|pt|em)',
    re.IGNORECASE,
)
_XML_NAMESPACE = 'http://www.w3.org/XML/1998/namespace'
_DRAWINGML_TEXT_SPACING_MIN = -400_000
_DRAWINGML_TEXT_SPACING_MAX = 400_000


@dataclass(frozen=True)
class ParsedTextProperty:
    """One validated text-property value and its canonical representation."""

    value: object
    canonical: str
    compatible: bool = False


@dataclass(frozen=True)
class TextPropertyDiagnostic:
    """Stable checker/converter diagnostic for one text declaration."""

    severity: str
    label: str
    source: str
    name: str
    raw: str
    message: str
    canonical: str | None = None


def _local_name(value: object) -> str:
    text = str(value)
    return text.rsplit('}', 1)[-1] if '}' in text else text


def _element_label(elem: ET.Element) -> str:
    tag = _local_name(elem.tag)
    elem_id = elem.get('id')
    return f'<{tag} id="{elem_id}">' if elem_id else f'<{tag}>'


def _attribute_name(raw_name: str) -> str:
    if raw_name.startswith(f'{{{_XML_NAMESPACE}}}'):
        return f'xml:{raw_name.rsplit("}", 1)[-1]}'
    return _local_name(raw_name)


def _is_unregistered_prefixed_text_property(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered.startswith(('font-', 'text-'))
        and lowered not in _TEXT_DECLARATION_PROPERTIES
    )


def _format_decimal(value: float) -> str:
    if abs(value) < 1e-15:
        return '0'
    text = f'{value:.15f}'.rstrip('0').rstrip('.')
    return '0' if text in {'', '-0'} else text


def parse_project_font_weight(raw: str) -> ParsedTextProperty:
    """Parse the closed project font-weight grammar."""
    if raw in {'normal', 'bold'}:
        return ParsedTextProperty(raw == 'bold', raw)
    if raw in {str(value) for value in range(100, 1000, 100)}:
        return ParsedTextProperty(int(raw) >= 600, raw)
    aliases = {'medium': '500', 'semibold': '600'}
    if raw in aliases:
        canonical = aliases[raw]
        return ParsedTextProperty(int(canonical) >= 600, canonical, True)
    raise ValueError(
        "expected 'normal', 'bold', or an integer weight from 100 through 900"
    )


def parse_project_font_style(raw: str) -> ParsedTextProperty:
    """Parse the closed project font-style grammar."""
    if raw not in {'normal', 'italic'}:
        raise ValueError("expected 'normal' or 'italic'")
    return ParsedTextProperty(raw == 'italic', raw)


def parse_project_text_anchor(raw: str) -> ParsedTextProperty:
    """Parse the closed project text-anchor grammar."""
    if raw not in {'start', 'middle', 'end'}:
        raise ValueError("expected 'start', 'middle', or 'end'")
    return ParsedTextProperty(raw, raw)


def parse_project_text_decoration(raw: str) -> ParsedTextProperty:
    """Parse text decoration without substring-based false positives."""
    canonical = {
        'none': 'none',
        'underline': 'underline',
        'line-through': 'line-through',
        'underline line-through': 'underline line-through',
    }
    if raw in canonical:
        value = (
            'underline' in raw.split(),
            'line-through' in raw.split(),
        )
        return ParsedTextProperty(value, canonical[raw])
    if raw == 'line-through underline':
        return ParsedTextProperty(
            (True, True),
            'underline line-through',
            True,
        )
    raise ValueError(
        "expected 'none', 'underline', 'line-through', or "
        "'underline line-through'"
    )


def parse_project_letter_spacing(
    raw: str,
    *,
    font_size: float = 16.0,
    scale_x: float = 1.0,
) -> ParsedTextProperty:
    """Parse project tracking into scaled SVG pixels and validate DML range."""
    if _CANONICAL_DECIMAL_RE.fullmatch(raw):
        amount = float(raw)
        unit = ''
        compatible = False
    else:
        match = _COMPATIBLE_LETTER_SPACING_RE.fullmatch(raw)
        if match is None:
            raise ValueError(
                'expected a finite ordinary decimal, optionally followed by '
                'the registered compatible unit px, pt, or em'
            )
        amount = float(match.group(1))
        unit = match.group(2).lower()
        compatible = True

    if not math.isfinite(amount):
        raise ValueError('must be finite')
    if not math.isfinite(font_size) or font_size <= 0:
        raise ValueError('requires a finite positive effective font size')
    if not math.isfinite(scale_x) or scale_x <= 0:
        raise ValueError('requires a finite positive horizontal scale')

    if unit == 'em':
        value_px = amount * font_size
    elif unit == 'pt':
        value_px = amount * 4.0 / 3.0 * scale_x
    else:
        value_px = amount * scale_x

    spacing = round(value_px * 75)
    if not _DRAWINGML_TEXT_SPACING_MIN <= spacing <= _DRAWINGML_TEXT_SPACING_MAX:
        raise ValueError(
            'converts outside the DrawingML character-spacing range '
            f'{_DRAWINGML_TEXT_SPACING_MIN}..{_DRAWINGML_TEXT_SPACING_MAX}'
        )
    return ParsedTextProperty(
        value_px,
        _format_decimal(value_px),
        compatible,
    )


def drawingml_letter_spacing(value_px: float) -> int:
    """Return validated DrawingML ``a:rPr@spc`` hundredths-of-a-point."""
    if not math.isfinite(value_px):
        raise ValueError('letter-spacing must be finite')
    spacing = round(value_px * 75)
    if not _DRAWINGML_TEXT_SPACING_MIN <= spacing <= _DRAWINGML_TEXT_SPACING_MAX:
        raise ValueError(
            'letter-spacing converts outside the DrawingML range '
            f'{_DRAWINGML_TEXT_SPACING_MIN}..{_DRAWINGML_TEXT_SPACING_MAX}'
        )
    return spacing


def parse_project_text_property(
    name: str,
    raw: str,
    *,
    font_size: float = 16.0,
) -> ParsedTextProperty:
    """Parse one declaration from the shared text-property value contract."""
    parsers = {
        'font-weight': parse_project_font_weight,
        'font-style': parse_project_font_style,
        'text-anchor': parse_project_text_anchor,
        'letter-spacing': parse_project_letter_spacing,
        'text-decoration': parse_project_text_decoration,
    }
    parser = parsers.get(name)
    if parser is None:
        raise ValueError(f'unsupported project text property {name!r}')
    if name == 'letter-spacing':
        return parser(raw, font_size=font_size)
    return parser(raw)


def _iter_style_declarations(
    elem: ET.Element,
) -> tuple[list[tuple[str, str]], list[str]]:
    declarations: list[tuple[str, str]] = []
    malformed: list[str] = []
    for raw_fragment in (elem.get('style') or '').split(';'):
        fragment = raw_fragment.strip()
        if not fragment:
            continue
        if ':' not in fragment:
            malformed.append(fragment)
            continue
        raw_name, raw_value = fragment.split(':', 1)
        name = raw_name.strip().lower()
        value = raw_value.strip()
        if not name or not value:
            malformed.append(fragment)
            continue
        declarations.append((name, value))
    return declarations, malformed


def _resolve_font_sizes(
    root: ET.Element,
) -> tuple[dict[int, float], list[TextPropertyDiagnostic]]:
    """Resolve inherited font sizes and retain declaration-level failures."""
    resolved: dict[int, float] = {}
    diagnostics: list[TextPropertyDiagnostic] = []

    def parse_declared_size(
        elem: ET.Element,
        raw: str,
        source: str,
        parent_size: float,
        root_size: float,
    ) -> float | None:
        label = _element_label(elem)
        relative_base = (
            root_size
            if raw.strip().lower().endswith('rem')
            else parent_size
        )
        try:
            value = parse_svg_length(
                raw,
                parent_size,
                font_size=relative_base,
            )
            font_px_to_hpt(value)
        except ValueError as exc:
            diagnostics.append(TextPropertyDiagnostic(
                'error',
                label,
                source,
                'font-size',
                raw,
                f'{label} {source} font-size={raw!r}: {exc}',
            ))
            return None
        return value

    def walk(
        elem: ET.Element,
        parent_size: float,
        root_size: float,
    ) -> None:
        declarations, _ = _iter_style_declarations(elem)
        style_sizes = [
            raw
            for name, raw in declarations
            if name == 'font-size'
        ]
        direct_raw = elem.get('font-size')
        direct_size = (
            parse_declared_size(
                elem,
                direct_raw,
                'attribute',
                parent_size,
                root_size,
            )
            if direct_raw is not None
            else None
        )
        parsed_style_sizes = [
            parse_declared_size(
                elem,
                raw,
                'inline style',
                parent_size,
                root_size,
            )
            for raw in style_sizes
        ]
        effective_size = parent_size
        if style_sizes:
            last_style_size = parsed_style_sizes[-1]
            effective_size = (
                last_style_size
                if last_style_size is not None
                else parent_size
            )
        elif direct_raw is not None:
            effective_size = direct_size if direct_size is not None else parent_size
        resolved[id(elem)] = effective_size
        child_root_size = effective_size if elem is root else root_size
        for child in elem:
            walk(child, effective_size, child_root_size)

    walk(root, 16.0, 16.0)
    return resolved, diagnostics


def resolve_project_font_sizes(root: ET.Element) -> dict[int, float]:
    """Return effective SVG font sizes or reject an invalid declaration."""
    resolved, diagnostics = _resolve_font_sizes(root)
    if diagnostics:
        raise ValueError('; '.join(item.message for item in diagnostics[:8]))
    return resolved


def resolve_project_letter_spacings(
    root: ET.Element,
    font_sizes: dict[int, float] | None = None,
) -> dict[int, float]:
    """Resolve tracking at its declaration site before it is inherited."""
    effective_font_sizes = font_sizes or resolve_project_font_sizes(root)
    resolved: dict[int, float] = {}

    def walk(elem: ET.Element, parent_spacing: float) -> None:
        declarations, _ = _iter_style_declarations(elem)
        style = dict(declarations)
        direct_raw = elem.get('letter-spacing')
        style_raw = style.get('letter-spacing')
        effective_spacing = parent_spacing
        if style_raw is not None:
            effective_spacing = float(parse_project_letter_spacing(
                style_raw,
                font_size=effective_font_sizes[id(elem)],
            ).value)
        elif direct_raw is not None:
            effective_spacing = float(parse_project_letter_spacing(
                direct_raw,
                font_size=effective_font_sizes[id(elem)],
            ).value)
        resolved[id(elem)] = effective_spacing
        for child in elem:
            walk(child, effective_spacing)

    walk(root, 0.0)
    return resolved


def materialize_project_text_metrics(root: ET.Element) -> int:
    """Lower relative text metrics before positional tspan restructuring."""
    font_sizes = resolve_project_font_sizes(root)
    letter_spacings = resolve_project_letter_spacings(root, font_sizes)
    materialized = 0
    for elem in root.iter():
        canonical_font_size = _format_decimal(font_sizes[id(elem)])
        canonical_letter_spacing = _format_decimal(letter_spacings[id(elem)])
        if elem.get('font-size') is not None:
            elem.set('font-size', canonical_font_size)
            materialized += 1
        if elem.get('letter-spacing') is not None:
            elem.set('letter-spacing', canonical_letter_spacing)
            materialized += 1

        style = elem.get('style')
        if not style:
            continue
        retained: list[str] = []
        changed = False
        for raw_fragment in style.split(';'):
            fragment = raw_fragment.strip()
            if not fragment:
                continue
            if ':' not in fragment:
                retained.append(fragment)
                continue
            raw_name, _ = fragment.split(':', 1)
            name = raw_name.strip().lower()
            if name == 'font-size':
                retained.append(f'font-size:{canonical_font_size}')
                changed = True
                materialized += 1
            elif name == 'letter-spacing':
                retained.append(
                    f'letter-spacing:{canonical_letter_spacing}'
                )
                changed = True
                materialized += 1
            else:
                retained.append(fragment)
        if changed:
            elem.set('style', '; '.join(retained))
    return materialized


def _diagnose_text_declaration(
    elem: ET.Element,
    *,
    tag: str,
    source: str,
    name: str,
    raw: str,
    font_size: float,
) -> tuple[bool, TextPropertyDiagnostic | None]:
    """Return whether a declaration belongs to the text contract and its issue."""
    label = _element_label(elem)
    if _is_unregistered_prefixed_text_property(name):
        return True, TextPropertyDiagnostic(
            'error', label, source, name, raw,
            f'{label} uses unregistered inherited text property {name!r}; '
            'native PPTX export would ignore it',
        )
    if (
        name in _TEXT_DECLARATION_PROPERTIES
        and tag not in _TEXT_INHERITANCE_TARGETS
    ):
        return True, TextPropertyDiagnostic(
            'error', label, source, name, raw,
            f'{label} cannot carry text property {name!r}; place it on '
            '<svg>, <g>, <text>, or <tspan>',
        )
    if name in _UNSUPPORTED_TEXT_PROPERTIES:
        return True, TextPropertyDiagnostic(
            'error', label, source, name, raw,
            f'{label} uses unsupported text property {name!r}; '
            'it has no registered DrawingML mapping',
        )
    if name not in _SVG_TEXT_PROPERTIES:
        return name in _TEXT_DECLARATION_PROPERTIES, None
    if tag == 'tspan' and name == 'text-anchor':
        return True, TextPropertyDiagnostic(
            'error', label, source, name, raw,
            f'{label} cannot use text-anchor on <tspan>; place it on the '
            'containing <text> or an ancestor group',
        )
    try:
        parsed = parse_project_text_property(
            name,
            raw,
            font_size=font_size,
        )
    except ValueError as exc:
        return True, TextPropertyDiagnostic(
            'error', label, source, name, raw,
            f'{label} {source} {name}={raw!r}: {exc}',
        )
    if parsed.compatible:
        return True, TextPropertyDiagnostic(
            'warning', label, source, name, raw,
            f'{label} {source} {name}={raw!r} is compatible; '
            f'prefer {name}={parsed.canonical!r}',
            parsed.canonical,
        )
    return True, None


def project_text_property_diagnostics(
    root: ET.Element,
) -> list[TextPropertyDiagnostic]:
    """Validate the closed text attribute/value surface for one SVG tree."""
    font_sizes, diagnostics = _resolve_font_sizes(root)

    for elem in root.iter():
        tag = _local_name(elem.tag)
        label = _element_label(elem)
        direct_allowlist = {
            'text': _TEXT_DIRECT_ATTRIBUTES,
            'tspan': _TSPAN_DIRECT_ATTRIBUTES,
        }.get(tag)
        inline_allowlist = {
            'text': _TEXT_INLINE_PROPERTIES,
            'tspan': _TSPAN_INLINE_PROPERTIES,
        }.get(tag)

        for raw_name, raw in elem.attrib.items():
            name = _attribute_name(raw_name)
            if name == 'style' or name.startswith('data-'):
                continue
            handled, diagnostic = _diagnose_text_declaration(
                elem,
                tag=tag,
                source='attribute',
                name=name,
                raw=raw,
                font_size=font_sizes[id(elem)],
            )
            if diagnostic is not None:
                diagnostics.append(diagnostic)
            elif (
                not handled
                and direct_allowlist is not None
                and name not in direct_allowlist
            ):
                diagnostics.append(TextPropertyDiagnostic(
                    'error', label, 'attribute', name, raw,
                    f'{label} uses unsupported text attribute {name!r}; '
                    'native PPTX export would ignore it',
                ))

        declarations, malformed = _iter_style_declarations(elem)
        for fragment in malformed:
            property_hint = fragment.split(None, 1)[0].lower()
            if (
                inline_allowlist is not None
                or property_hint in _TEXT_DECLARATION_PROPERTIES
                or property_hint in _UNSUPPORTED_TEXT_PROPERTIES
                or _is_unregistered_prefixed_text_property(property_hint)
            ):
                diagnostics.append(TextPropertyDiagnostic(
                    'error', label, 'inline style', '<malformed>', fragment,
                    f'{label} has malformed inline style declaration {fragment!r}',
                ))
        for name, raw in declarations:
            handled, diagnostic = _diagnose_text_declaration(
                elem,
                tag=tag,
                source='inline style',
                name=name,
                raw=raw,
                font_size=font_sizes[id(elem)],
            )
            if diagnostic is not None:
                diagnostics.append(diagnostic)
            elif (
                not handled
                and inline_allowlist is not None
                and name not in inline_allowlist
            ):
                diagnostics.append(TextPropertyDiagnostic(
                    'error', label, 'inline style', name, raw,
                    f'{label} uses unsupported inline text property {name!r}; '
                    'native PPTX export would ignore it',
                ))

    return diagnostics


def project_text_property_errors(root: ET.Element) -> list[str]:
    """Return blocking diagnostics for the converter preflight."""
    return [
        diagnostic.message
        for diagnostic in project_text_property_diagnostics(root)
        if diagnostic.severity == 'error'
    ]
