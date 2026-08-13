#!/usr/bin/env python3
"""
PPT Master - PPTX Hyperlink Resolver

Resolve native DrawingML click actions into the canonical SVG ``href`` form
used by the authoring and round-trip pipelines.

Usage:
    from .hyperlinks import resolve_click_hyperlink

Examples:
    result = resolve_click_hyperlink(rels, "rId3", "", slide_index_by_part=roster)

Dependencies:
    PPT Master hyperlink contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from hyperlink_contract import (
    HYPERLINK_REL_TYPE,
    HyperlinkContractError,
    SLIDE_JUMP_ACTION,
    SLIDE_REL_TYPE,
    parse_hyperlink_target,
)


@dataclass(frozen=True)
class HyperlinkResolution:
    """Resolved SVG target or one actionable source-package diagnostic."""

    href: str | None = None
    error: str | None = None


def resolve_click_hyperlink(
    relationships: dict[str, dict[str, str]],
    relationship_id: str,
    action: str,
    *,
    slide_index_by_part: dict[str, int],
) -> HyperlinkResolution:
    """Resolve a click hyperlink relationship from one OOXML source part."""
    if action == "ppaction://media":
        return HyperlinkResolution()
    if not relationship_id:
        return HyperlinkResolution(error="click hyperlink has no relationship id")
    relationship = relationships.get(relationship_id)
    if relationship is None:
        return HyperlinkResolution(
            error=f"click hyperlink relationship {relationship_id!r} is missing"
        )
    rel_type = relationship.get("type", "")
    target = relationship.get("target", "")
    external = relationship.get("external") == "1"

    if action == SLIDE_JUMP_ACTION:
        if external or rel_type != SLIDE_REL_TYPE:
            return HyperlinkResolution(
                error="hlinksldjump does not reference an internal slide"
            )
        slide_index = slide_index_by_part.get(target)
        if slide_index is None:
            return HyperlinkResolution(
                error=f"slide jump target {target!r} is not in the presentation roster"
            )
        return HyperlinkResolution(href=f"#slide-{slide_index}")

    if action.startswith("ppaction://") and action not in {
        "ppaction://hlinkurl",
    }:
        return HyperlinkResolution(
            error=f"unsupported PowerPoint click action {action!r}"
        )
    if not external or rel_type != HYPERLINK_REL_TYPE:
        return HyperlinkResolution(
            error="click hyperlink does not reference an external hyperlink"
        )
    try:
        parsed = parse_hyperlink_target(target)
    except HyperlinkContractError as exc:
        return HyperlinkResolution(error=str(exc))
    if parsed.kind != "external":
        return HyperlinkResolution(
            error="external hyperlink relationship resolved to a slide target"
        )
    return HyperlinkResolution(href=parsed.raw)


__all__ = ["HyperlinkResolution", "resolve_click_hyperlink"]
