#!/usr/bin/env python3
"""
PPT Master - Shared SVG Resource Helpers

Centralizes project-relative resource lookup and nested-SVG closure validation
used by the checker, finalizer, and SVG-to-PPTX exporter.

Usage:
    Imported by scripts; not intended as a standalone CLI.

Examples:
    from resource_paths import resolve_external_image_reference
    from resource_paths import svg_image_payload_error

Dependencies:
    None
"""

from __future__ import annotations

import base64
import binascii
import re
from pathlib import Path
from urllib.parse import unquote, unquote_to_bytes, urlsplit
from xml.etree import ElementTree as ET


SVG_WORK_DIR_NAMES = frozenset({
    'authoring-svg',
    'authoring-svg-flat',
    'svg',
    'svg_output',
    'svg_final',
    'svg-flat',
})
SVG_FINAL_CANDIDATE_PREFIX = '.svg_final.candidate-'
TEMPLATE_SOURCE_DIR_NAME = 'templates'
TEMPLATE_SPEC_FILENAME = 'design_spec.md'
_TEMPLATE_QUALIFIED_SPEC_RE = re.compile(
    r'design_spec\.(?:brand|style|layout|deck)\.[^/\\]+\.md'
)
_SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
_SVG_URL_REFERENCE_RE = re.compile(r'url\(\s*([^)]+?)\s*\)', re.IGNORECASE)
_SVG_CSS_URL_ATTRIBUTES = frozenset({
    'background',
    'background-image',
    'clip-path',
    'color-profile',
    'cursor',
    'fill',
    'filter',
    'marker',
    'marker-end',
    'marker-mid',
    'marker-start',
    'mask',
    'stroke',
    'style',
})
_SVG_DIRECT_RESOURCE_ATTRIBUTES = frozenset({'poster', 'src'})
_SVG_DATA_URI_DEPTH_LIMIT = 8
_SVG_EXTERNAL_DOCTYPE_RE = re.compile(
    br'<!DOCTYPE\b[^>]*\b(?:PUBLIC|SYSTEM)\b',
    re.IGNORECASE | re.DOTALL,
)
_XML_STYLESHEET_HREF_RE = re.compile(
    r'\bhref\s*=\s*([\'"])(.*?)\1',
    re.IGNORECASE | re.DOTALL,
)


def project_root_for_svg_path(svg_path: Path) -> Path:
    """Infer the project root from an SVG file path or SVG directory path."""
    path = Path(svg_path)
    base = path if path.is_dir() else path.parent
    if (
        base.name in SVG_WORK_DIR_NAMES
        or base.name.startswith(SVG_FINAL_CANDIDATE_PREFIX)
    ):
        return base.parent
    if (
        base.name == TEMPLATE_SOURCE_DIR_NAME
        and (
            (base / TEMPLATE_SPEC_FILENAME).is_file()
            or any(
                path.is_file()
                and _TEMPLATE_QUALIFIED_SPEC_RE.fullmatch(path.name)
                for path in base.glob('design_spec.*.md')
            )
        )
    ):
        return base.parent
    return base


def icon_dir_for_project(project_path: Path) -> Path:
    """Return the only valid icon root for a project."""
    return Path(project_path) / 'icons'


def icon_dir_for_svg(svg_path: Path) -> Path:
    """Return the project-local icon root for one SVG input."""
    return icon_dir_for_project(project_root_for_svg_path(svg_path))


def _decode_svg_data_uri(raw: str) -> tuple[bytes | None, str | None]:
    """Decode an SVG data URI; return ``(None, None)`` for other media."""
    value = raw.strip().strip('\'"')
    if not value.lower().startswith('data:'):
        return None, None
    header, separator, payload = value.partition(',')
    media_type = header[5:].split(';', 1)[0].strip().lower()
    if media_type != 'image/svg+xml':
        return None, None
    if not separator:
        return None, 'invalid embedded SVG data URI'
    is_base64 = any(
        token.strip().lower() == 'base64'
        for token in header.split(';')[1:]
    )
    try:
        decoded = (
            base64.b64decode(payload, validate=True)
            if is_base64
            else unquote_to_bytes(payload)
        )
    except (ValueError, binascii.Error):
        return None, 'invalid embedded SVG data URI'
    return decoded, None


def _svg_reference_error(raw: str, depth: int) -> str | None:
    """Return an external or recursively embedded SVG resource error."""
    value = raw.strip().strip('\'"')
    if not value:
        return 'empty resource reference'
    if value.startswith('#'):
        return None
    if not value.lower().startswith('data:'):
        return f'unpackaged external resource {value!r}'

    nested_svg, decode_error = _decode_svg_data_uri(value)
    if decode_error is not None:
        return decode_error
    if nested_svg is None:
        return None
    if depth >= _SVG_DATA_URI_DEPTH_LIMIT:
        return 'embedded SVG resource nesting exceeds the safety limit'
    nested_error = _svg_image_payload_error(nested_svg, depth + 1)
    if nested_error is None:
        return None
    return f'embedded SVG resource is not closed: {nested_error}'


def _xml_stylesheet_error(raw_bytes: bytes, depth: int) -> str | None:
    """Return an external XML stylesheet processing-instruction error."""
    parser = ET.XMLPullParser(events=('pi',))
    try:
        parser.feed(raw_bytes)
        parser.close()
    except ET.ParseError:
        return None
    for _event, instruction in parser.read_events():
        text = (instruction.text or '').strip()
        if not text.lower().startswith('xml-stylesheet'):
            continue
        match = _XML_STYLESHEET_HREF_RE.search(text)
        if match is None:
            return 'XML stylesheet processing instruction lacks href'
        reference_error = _svg_reference_error(match.group(2), depth)
        if reference_error is not None:
            return f'XML stylesheet is not closed: {reference_error}'
    return None


def _svg_image_payload_error(raw_bytes: bytes, depth: int) -> str | None:
    """Return why one SVG image payload is not a closed packaged resource."""
    if _SVG_EXTERNAL_DOCTYPE_RE.search(raw_bytes):
        return 'unpackaged external XML doctype'
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as exc:
        return f'invalid SVG XML: {exc}'
    if root.tag != f'{{{_SVG_NAMESPACE}}}svg':
        return 'root must use the SVG namespace'

    stylesheet_error = _xml_stylesheet_error(raw_bytes, depth)
    if stylesheet_error is not None:
        return stylesheet_error
    for elem in root.iter():
        tag = str(elem.tag).rsplit('}', 1)[-1]
        for raw_name, raw_value in elem.attrib.items():
            name = raw_name.rsplit('}', 1)[-1]
            if name == 'href' and tag != 'a':
                reference_error = _svg_reference_error(raw_value, depth)
                if reference_error is not None:
                    return reference_error
            elif name in _SVG_DIRECT_RESOURCE_ATTRIBUTES:
                reference_error = _svg_reference_error(raw_value, depth)
                if reference_error is not None:
                    return reference_error
            elif name == 'data' and tag == 'object':
                reference_error = _svg_reference_error(raw_value, depth)
                if reference_error is not None:
                    return reference_error
            elif name == 'srcset' and raw_value.strip():
                return 'srcset resource lists are not closed SVG resources'

            if name not in _SVG_CSS_URL_ATTRIBUTES:
                continue
            for match in _SVG_URL_REFERENCE_RE.finditer(raw_value):
                reference_error = _svg_reference_error(match.group(1), depth)
                if reference_error is not None:
                    return f'url() resource is not closed: {reference_error}'

        if tag != 'style':
            continue
        style_text = ''.join(elem.itertext())
        if re.search(r'@import\b', style_text, flags=re.IGNORECASE):
            return 'unpackaged CSS import'
        for match in _SVG_URL_REFERENCE_RE.finditer(style_text):
            reference_error = _svg_reference_error(match.group(1), depth)
            if reference_error is not None:
                return f'url() resource is not closed: {reference_error}'
    return None


def svg_image_payload_error(raw_bytes: bytes) -> str | None:
    """Return why a nested SVG image is not a closed packaged resource."""
    return _svg_image_payload_error(raw_bytes, 0)


def svg_data_uri_payload_error(raw: str) -> str | None:
    """Return why an inline SVG image data URI is not a closed resource."""
    nested_svg, decode_error = _decode_svg_data_uri(raw)
    if decode_error is not None:
        return decode_error
    if nested_svg is None:
        return None
    nested_error = _svg_image_payload_error(nested_svg, 0)
    if nested_error is None:
        return None
    return f'inline SVG data URI is not closed: {nested_error}'


def external_image_reference_path(
    svg_dir: Path,
    href: str,
    *,
    project_root: Path | None = None,
) -> Path | None:
    """Resolve one exact SVG-relative image reference inside the project."""
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None
    decoded = unquote(parsed.path)
    if not decoded or Path(decoded).is_absolute():
        return None
    svg_dir = Path(svg_dir)
    resolved_project_root = (
        Path(project_root).resolve()
        if project_root is not None
        else project_root_for_svg_path(svg_dir).resolve()
    )
    resolved = (svg_dir / decoded).resolve()
    try:
        resolved.relative_to(resolved_project_root)
    except ValueError:
        return None
    return resolved


def resolve_external_image_reference(
    svg_dir: Path,
    href: str,
    *,
    project_root: Path | None = None,
) -> Path | None:
    """Resolve an exact SVG-relative image href, or return None."""
    candidate = external_image_reference_path(
        svg_dir,
        href,
        project_root=project_root,
    )
    return candidate if candidate is not None and candidate.is_file() else None
