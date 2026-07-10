#!/usr/bin/env python3
"""
PPT Master - Semantic SVG Markers

Owns the minimal page and structural-role marker vocabulary used by SVG
authoring, validation, conversion traces, and native PPTX structure
reconstruction. These markers are compiler hints, not a parallel content model.

Usage:
    Import from svg_quality_checker.py or svg_to_pptx internals.

Examples:
    validate_semantic_markers(root, require_page_role=True)

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


PAGE_ROLE_TO_LAYOUT = {
    "cover": "Cover",
    "toc": "Agenda",
    "section": "Section",
    "content": "Content",
    "ending": "Closing",
}

STRUCTURAL_ROLES = frozenset({
    "background",
    "chrome",
    "decoration",
    "footer",
    "header",
    "logo",
    "page-number",
    "watermark",
})

CHROME_ROLE_TO_TOKEN = {
    "chrome": "chrome",
    "footer": "footer",
    "header": "header",
    "logo": "logo",
    "page-number": "pagenumber",
    "watermark": "watermark",
}

ANIMATION_CHROME_ROLES = STRUCTURAL_ROLES

SEMANTIC_ATTRS = frozenset({
    "data-pptx-page-role",
    "data-pptx-role",
})

_NON_VISUAL_TAGS = frozenset({"defs", "desc", "metadata", "style", "title"})
_MARKER_TOKEN_RE = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class SemanticMarkerIssue:
    """One semantic-marker validation issue."""

    severity: str
    message: str


def _local_tag(elem: ET.Element) -> str:
    """Return one element's local tag name."""
    return elem.tag.rsplit("}", 1)[-1] if "}" in str(elem.tag) else str(elem.tag)


def _normalized_marker(raw: str | None) -> str | None:
    """Normalize one marker value, preserving absence."""
    if raw is None:
        return None
    return raw.strip().lower()


def chrome_token_from_role(role: str | None) -> str | None:
    """Return the baseline chrome token represented by a semantic role."""
    normalized = _normalized_marker(role)
    return CHROME_ROLE_TO_TOKEN.get(normalized or "")


def chrome_token_from_markers(
    role: str | None,
    placeholder: str | None,
) -> str | None:
    """Return chrome behavior from specialized markers before generic roles."""
    if _normalized_marker(placeholder) == "slide-number":
        return "pagenumber"
    return chrome_token_from_role(role)


def is_chrome_role(role: str | None) -> bool:
    """Return whether a semantic role represents non-content page chrome."""
    normalized = _normalized_marker(role)
    return normalized in ANIMATION_CHROME_ROLES


def is_static_page_frame(
    role: str | None,
    placeholder: str | None,
) -> bool:
    """Return whether explicit markers identify a static page-frame object."""
    return (
        _normalized_marker(placeholder) == "slide-number"
        or is_chrome_role(role)
    )


def page_layout_name_from_svg(svg_path: Path) -> str | None:
    """Return the native baseline Layout name declared by the SVG page role."""
    root = ET.parse(svg_path).getroot()
    role = _normalized_marker(root.get("data-pptx-page-role"))
    return PAGE_ROLE_TO_LAYOUT.get(role or "")


def validate_semantic_markers(
    root: ET.Element,
    *,
    require_page_role: bool = False,
) -> list[SemanticMarkerIssue]:
    """Validate semantic markers without changing SVG rendering semantics."""
    issues: list[SemanticMarkerIssue] = []
    page_role_raw = root.get("data-pptx-page-role")
    page_role = _normalized_marker(page_role_raw)
    if page_role_raw is None:
        if require_page_role:
            issues.append(SemanticMarkerIssue(
                "warning",
                "page SVG is missing root data-pptx-page-role",
            ))
    elif not page_role:
        issues.append(SemanticMarkerIssue(
            "error",
            "root data-pptx-page-role must not be empty",
        ))
    elif not _MARKER_TOKEN_RE.fullmatch(page_role):
        issues.append(SemanticMarkerIssue(
            "error",
            f"invalid data-pptx-page-role={page_role_raw!r}; use lowercase kebab-case",
        ))
    elif page_role not in PAGE_ROLE_TO_LAYOUT:
        issues.append(SemanticMarkerIssue(
            "warning",
            f"unknown data-pptx-page-role={page_role_raw!r}",
        ))
    elif page_role_raw != page_role:
        issues.append(SemanticMarkerIssue(
            "warning",
            f"data-pptx-page-role should use canonical lowercase value {page_role!r}",
        ))

    id_counts: dict[str, int] = {}
    for elem in root.iter():
        elem_id = (elem.get("id") or "").strip()
        if elem_id:
            id_counts[elem_id] = id_counts.get(elem_id, 0) + 1

    marked_ids: set[str] = set()
    for elem in root.iter():
        tag = _local_tag(elem)
        elem_id = (elem.get("id") or "").strip()
        if elem is not root and elem.get("data-pptx-page-role") is not None:
            issues.append(SemanticMarkerIssue(
                "error",
                f"{elem_id or tag}: data-pptx-page-role belongs on the root <svg> only",
            ))

        role_raw = elem.get("data-pptx-role")
        role = _normalized_marker(role_raw)
        if role_raw is not None:
            if elem is root or tag in _NON_VISUAL_TAGS:
                issues.append(SemanticMarkerIssue(
                    "error",
                    f"{elem_id or tag}: data-pptx-role belongs on a visual SVG element",
                ))
            if not role:
                issues.append(SemanticMarkerIssue(
                    "error",
                    f"{elem_id or tag}: data-pptx-role must not be empty",
                ))
            elif not _MARKER_TOKEN_RE.fullmatch(role):
                issues.append(SemanticMarkerIssue(
                    "error",
                    f"{elem_id or tag}: invalid data-pptx-role={role_raw!r}; "
                    "use lowercase kebab-case",
                ))
            elif role not in STRUCTURAL_ROLES:
                issues.append(SemanticMarkerIssue(
                    "warning",
                    f"{elem_id or tag}: unknown data-pptx-role={role_raw!r}",
                ))
            elif role_raw != role:
                issues.append(SemanticMarkerIssue(
                    "warning",
                    f"{elem_id or tag}: data-pptx-role should use canonical "
                    f"lowercase value {role!r}",
                ))
            if not elem_id:
                issues.append(SemanticMarkerIssue(
                    "error",
                    f"<{tag}> with data-pptx-role requires a stable id",
                ))
            else:
                marked_ids.add(elem_id)

            layer = _normalized_marker(elem.get("data-pptx-layer"))
            placeholder = _normalized_marker(elem.get("data-pptx-placeholder"))
            if layer:
                issues.append(SemanticMarkerIssue(
                    "warning",
                    f"{elem_id or tag}: data-pptx-role is redundant when "
                    "data-pptx-layer already owns structure/animation behavior",
                ))
            if role == "page-number" and placeholder == "slide-number":
                issues.append(SemanticMarkerIssue(
                    "warning",
                    f"{elem_id or tag}: data-pptx-role='page-number' is redundant; "
                    "data-pptx-placeholder='slide-number' already owns the behavior",
                ))

    duplicates = sorted(
        elem_id for elem_id in marked_ids
        if id_counts.get(elem_id, 0) > 1
    )
    if duplicates:
        issues.append(SemanticMarkerIssue(
            "error",
            "semantic markers require unique ids; duplicate: " + ", ".join(duplicates),
        ))
    return issues
