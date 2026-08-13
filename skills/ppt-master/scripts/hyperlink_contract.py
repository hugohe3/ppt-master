#!/usr/bin/env python3
"""
PPT Master - Hyperlink Contract

Parse and validate the shared SVG hyperlink surface used by quality checks,
SVG-to-PPTX export, and PPTX-to-SVG round-trip conversion.

Usage:
    from hyperlink_contract import parse_hyperlink_target

Examples:
    parse_hyperlink_target("https://example.com")
    parse_hyperlink_target("#slide-3", slide_count=8)

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
HYPERLINK_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "hyperlink"
)
SLIDE_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
)
SLIDE_JUMP_ACTION = "ppaction://hlinksldjump"
SHAPE_HYPERLINK_ATTR = "data-pptx-shape-hyperlink"

_SLIDE_TARGET_RE = re.compile(r"#slide-([1-9][0-9]*)")
_URI_SCHEME_RE = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*):")
_FORBIDDEN_EXTERNAL_SCHEMES = frozenset({
    "data",
    "file",
    "javascript",
    "vbscript",
})
_NON_OUTPUT_ANCESTORS = frozenset({
    "defs",
    "desc",
    "metadata",
    "style",
    "symbol",
    "title",
})
_INLINE_CONTAINER_TAGS = frozenset({"text", "tspan"})
_INLINE_CONTENT_TAGS = frozenset({"tspan"})
_UNSUPPORTED_LINK_BEHAVIOR_ATTRIBUTES = frozenset({
    "download",
    "hreflang",
    "ping",
    "referrerpolicy",
    "rel",
    "target",
    "type",
})


class HyperlinkContractError(ValueError):
    """Raised when one hyperlink cannot be represented faithfully in PPTX."""


@dataclass(frozen=True)
class HyperlinkTarget:
    """One normalized hyperlink destination."""

    raw: str
    kind: str
    slide_number: int | None = None


def _local_name(elem: ET.Element) -> str:
    if not isinstance(elem.tag, str):
        return str(elem.tag)
    return elem.tag.rsplit("}", 1)[-1]


def parse_hyperlink_target(
    raw: str,
    *,
    slide_count: int | None = None,
) -> HyperlinkTarget:
    """Parse one canonical SVG hyperlink target.

    Same-deck jumps use ``#slide-N``. External destinations must be absolute
    URIs with an explicit scheme. Local files, script/data URLs, relative
    paths, arbitrary SVG fragments, whitespace, and control characters fail
    closed instead of being silently dropped during export.
    """
    if not isinstance(raw, str):
        raise HyperlinkContractError("hyperlink target must be a string")
    if not raw:
        raise HyperlinkContractError("hyperlink target must not be empty")
    if raw != raw.strip():
        raise HyperlinkContractError(
            "hyperlink target must not contain leading or trailing whitespace"
        )
    if any(ord(char) < 0x21 or ord(char) == 0x7F for char in raw):
        raise HyperlinkContractError(
            "hyperlink target must not contain whitespace or control characters; "
            "percent-encode URI spaces"
        )
    if "\\" in raw:
        raise HyperlinkContractError(
            "hyperlink target must use URI syntax, not a filesystem path"
        )

    slide_match = _SLIDE_TARGET_RE.fullmatch(raw)
    if slide_match is not None:
        slide_number = int(slide_match.group(1))
        if slide_count is not None and slide_number > slide_count:
            raise HyperlinkContractError(
                f"slide jump {raw!r} exceeds the {slide_count}-slide deck"
            )
        return HyperlinkTarget(
            raw=f"#slide-{slide_number}",
            kind="slide",
            slide_number=slide_number,
        )

    if raw.startswith("#"):
        raise HyperlinkContractError(
            "same-deck hyperlinks must use the exact #slide-N form"
        )
    scheme_match = _URI_SCHEME_RE.match(raw)
    if scheme_match is None:
        raise HyperlinkContractError(
            "external hyperlinks must be absolute URIs with an explicit scheme"
        )
    scheme = scheme_match.group(1).lower()
    if scheme in _FORBIDDEN_EXTERNAL_SCHEMES:
        raise HyperlinkContractError(
            f"external hyperlink scheme {scheme!r} is not allowed"
        )
    return HyperlinkTarget(raw=raw, kind="external")


def svg_hyperlink_href(elem: ET.Element) -> str:
    """Return the sole href value from one SVG ``<a>`` element."""
    if _local_name(elem) != "a" or elem.tag != f"{{{SVG_NS}}}a":
        raise HyperlinkContractError("hyperlink carrier must be an SVG <a>")
    href = elem.get("href")
    xlink_href = elem.get(f"{{{XLINK_NS}}}href")
    if href is not None and xlink_href is not None:
        raise HyperlinkContractError(
            "SVG <a> must not declare both href and xlink:href"
        )
    value = href if href is not None else xlink_href
    if value is None:
        raise HyperlinkContractError("SVG <a> must declare href")
    return value


def project_hyperlink_errors(
    root: ET.Element,
    *,
    slide_count: int | None = None,
) -> list[str]:
    """Return fail-closed diagnostics for every SVG hyperlink carrier."""
    errors: list[str] = []
    parent_by_id = {
        id(child): parent
        for parent in root.iter()
        for child in list(parent)
    }
    anchors = [
        elem for elem in root.iter()
        if _local_name(elem) == "a"
    ]
    for index, anchor in enumerate(anchors, 1):
        label = anchor.get("id") or f"anchor {index}"
        if anchor.tag != f"{{{SVG_NS}}}a":
            errors.append(f"{label}: hyperlink carrier must be an SVG <a>")
            continue
        try:
            href = svg_hyperlink_href(anchor)
            parse_hyperlink_target(href, slide_count=slide_count)
        except HyperlinkContractError as exc:
            errors.append(f"{label}: {exc}")

        unsupported_attrs = sorted(
            name
            for name in anchor.attrib
            if name.rsplit("}", 1)[-1].lower()
            in _UNSUPPORTED_LINK_BEHAVIOR_ATTRIBUTES
        )
        if unsupported_attrs:
            errors.append(
                f"{label}: unsupported link behavior attribute(s): "
                + ", ".join(unsupported_attrs)
            )

        ancestors: list[ET.Element] = []
        current = parent_by_id.get(id(anchor))
        while current is not None:
            ancestors.append(current)
            current = parent_by_id.get(id(current))
        ancestor_tags = [_local_name(elem) for elem in ancestors]
        if "a" in ancestor_tags:
            errors.append(f"{label}: nested SVG <a> elements are not supported")
        hidden_ancestor = next(
            (tag for tag in ancestor_tags if tag in _NON_OUTPUT_ANCESTORS),
            None,
        )
        if hidden_ancestor is not None:
            errors.append(
                f"{label}: hyperlink cannot appear inside non-output "
                f"<{hidden_ancestor}> content"
            )
        replacement_ancestor = next(
            (
                elem
                for elem in ancestors
                if elem.get("data-pptx-replace-with") is not None
                or elem.get("data-pptx-part") == "geometry-detail"
            ),
            None,
        )
        if replacement_ancestor is not None:
            errors.append(
                f"{label}: hyperlink cannot appear inside content replaced "
                "or skipped during native export"
            )

        inline = any(tag in _INLINE_CONTAINER_TAGS for tag in ancestor_tags)
        children = [
            child for child in list(anchor)
            if _local_name(child) not in _NON_OUTPUT_ANCESTORS
        ]
        if inline:
            if any(_local_name(child) not in _INLINE_CONTENT_TAGS for child in children):
                errors.append(
                    f"{label}: inline hyperlink content may contain only <tspan>"
                )
            positioned = [
                elem
                for elem in anchor.iter()
                if any(elem.get(name) is not None for name in ("x", "y", "dx", "dy"))
            ]
            if positioned:
                errors.append(
                    f"{label}: inline hyperlink cannot own x/y/dx/dy; "
                    "put line positioning on an enclosing <tspan>"
                )
            direct_parent = parent_by_id.get(id(anchor))
            if (
                direct_parent is not None
                and _local_name(direct_parent) == "text"
                and (
                    direct_parent.get("data-paragraph-line-height") is not None
                    or any(
                        _local_name(sibling) == "tspan"
                        and any(
                            sibling.get(name) is not None
                            for name in ("x", "y", "dx", "dy")
                        )
                        for sibling in list(direct_parent)
                    )
                )
            ):
                errors.append(
                    f"{label}: multi-line hyperlinks must be nested inside "
                    "the owning line <tspan>"
                )
            visible_text = "".join(anchor.itertext())
            if not visible_text.strip():
                errors.append(f"{label}: inline hyperlink must contain visible text")
        else:
            if anchor.text and anchor.text.strip():
                errors.append(
                    f"{label}: shape hyperlink cannot contain direct text; "
                    "wrap text in <text>"
                )
            visible_children = [
                child for child in children
                if child.get("data-pptx-part") != "geometry-detail"
            ]
            if not visible_children:
                errors.append(
                    f"{label}: shape hyperlink must wrap at least one visual element"
                )
            if any(_local_name(child) == "tspan" for child in children):
                errors.append(
                    f"{label}: shape hyperlink cannot contain a bare <tspan>; "
                    "wrap inline runs in <text>"
                )

    for index, carrier in enumerate(
        (
            elem
            for elem in root.iter()
            if elem.get(SHAPE_HYPERLINK_ATTR) is not None
        ),
        1,
    ):
        label = carrier.get("id") or f"shape hyperlink transport {index}"
        raw_target = carrier.get(SHAPE_HYPERLINK_ATTR) or ""
        try:
            parse_hyperlink_target(raw_target, slide_count=slide_count)
        except HyperlinkContractError as exc:
            errors.append(f"{label}: {exc}")
        if _local_name(carrier) != "g":
            errors.append(
                f"{label}: {SHAPE_HYPERLINK_ATTR} is allowed only on <g>"
            )
        ancestors: list[ET.Element] = []
        current = parent_by_id.get(id(carrier))
        while current is not None:
            ancestors.append(current)
            current = parent_by_id.get(id(current))
        if any(_local_name(elem) == "a" for elem in ancestors):
            errors.append(
                f"{label}: {SHAPE_HYPERLINK_ATTR} cannot be nested in <a>"
            )
        inline_anchors = [
            elem
            for elem in carrier.iter(f"{{{SVG_NS}}}a")
            if any(
                _local_name(ancestor) in _INLINE_CONTAINER_TAGS
                for ancestor in _ancestors_of(elem, parent_by_id)
            )
        ]
        if not inline_anchors:
            errors.append(
                f"{label}: {SHAPE_HYPERLINK_ATTR} is reserved for PPTX "
                "round-trip groups that also contain inline hyperlinks"
            )
    return errors


def _ancestors_of(
    elem: ET.Element,
    parent_by_id: dict[int, ET.Element],
) -> list[ET.Element]:
    """Return ancestors from nearest parent to the SVG root."""
    ancestors: list[ET.Element] = []
    current = parent_by_id.get(id(elem))
    while current is not None:
        ancestors.append(current)
        current = parent_by_id.get(id(current))
    return ancestors


def trigger_shape_hyperlink_errors(
    root: ET.Element,
    trigger_group_ids: set[str] | frozenset[str],
) -> list[str]:
    """Reject navigation links on click-trigger animation groups."""
    if not trigger_group_ids:
        return []
    parent_by_id = {
        id(child): parent
        for parent in root.iter()
        for child in list(parent)
    }
    errors: list[str] = []
    for elem in root.iter():
        group_id = elem.get("id")
        if _local_name(elem) != "g" or group_id not in trigger_group_ids:
            continue
        has_link = elem.get(SHAPE_HYPERLINK_ATTR) is not None or any(
            _local_name(descendant) == "a"
            or descendant.get(SHAPE_HYPERLINK_ATTR) is not None
            for descendant in elem.iter()
        )
        if not has_link:
            has_link = any(
                _local_name(ancestor) == "a"
                or ancestor.get(SHAPE_HYPERLINK_ATTR) is not None
                for ancestor in _ancestors_of(elem, parent_by_id)
            )
        if has_link:
            errors.append(
                f"animation trigger group {group_id!r} cannot also carry a "
                "hyperlink; use an ordinary animation or a separate trigger"
            )
    return errors


__all__ = [
    "HYPERLINK_REL_TYPE",
    "HyperlinkContractError",
    "HyperlinkTarget",
    "SHAPE_HYPERLINK_ATTR",
    "SLIDE_JUMP_ACTION",
    "SLIDE_REL_TYPE",
    "parse_hyperlink_target",
    "project_hyperlink_errors",
    "svg_hyperlink_href",
    "trigger_shape_hyperlink_errors",
]
