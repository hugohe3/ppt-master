#!/usr/bin/env python3
"""
PPT Master - DrawingML Hyperlink Lowering

Register native PowerPoint hyperlink relationships and attach click actions to
text runs or clickable leaf shapes produced by the SVG converter.

Usage:
    from .hyperlinks import apply_shape_hyperlink, hyperlink_run_metadata

Examples:
    metadata = hyperlink_run_metadata(ctx, "https://example.com")
    linked = apply_shape_hyperlink(result, ctx, "#slide-2")

Dependencies:
    PPT Master hyperlink contract and DrawingML conversion context.
"""

from __future__ import annotations

import re

from hyperlink_contract import (
    HYPERLINK_REL_TYPE,
    SLIDE_JUMP_ACTION,
    SLIDE_REL_TYPE,
    parse_hyperlink_target,
)

from .context import ConvertContext, ShapeResult


HYPERLINK_RID_KEY = "_hyperlink_rid"
HYPERLINK_ACTION_KEY = "_hyperlink_action"

_CNVPR_RE = re.compile(
    r"<p:cNvPr\b[^<>]*(?:/>|>.*?</p:cNvPr>)",
    re.DOTALL,
)
_GROUP_NONVISUAL_RE = re.compile(
    r"<p:nvGrpSpPr>.*?</p:nvGrpSpPr>",
    re.DOTALL,
)


def register_hyperlink(
    ctx: ConvertContext,
    raw_target: str,
) -> tuple[str, str | None]:
    """Register one slide relationship and return ``(rId, action)``."""
    target = parse_hyperlink_target(
        raw_target,
        slide_count=ctx.slide_count,
    )
    if target.kind == "slide":
        relationship_type = SLIDE_REL_TYPE
        relationship_target = f"slide{target.slide_number}.xml"
        target_mode = None
        action = SLIDE_JUMP_ACTION
    else:
        relationship_type = HYPERLINK_REL_TYPE
        relationship_target = target.raw
        target_mode = "External"
        action = None

    for relationship in ctx.rel_entries:
        if (
            relationship.get("type") == relationship_type
            and relationship.get("target") == relationship_target
            and relationship.get("target_mode") == target_mode
        ):
            return relationship["id"], action

    relationship_id = ctx.next_rel_id()
    relationship = {
        "id": relationship_id,
        "type": relationship_type,
        "target": relationship_target,
    }
    if target_mode is not None:
        relationship["target_mode"] = target_mode
    ctx.rel_entries.append(relationship)
    return relationship_id, action


def hyperlink_click_xml(
    relationship_id: str,
    action: str | None = None,
) -> str:
    """Build one DrawingML click hyperlink child."""
    action_attr = f' action="{action}"' if action else ""
    return f'<a:hlinkClick r:id="{relationship_id}"{action_attr}/>'


def hyperlink_run_metadata(
    ctx: ConvertContext,
    raw_target: str,
) -> dict[str, str]:
    """Return the internal run fields for one SVG inline anchor."""
    relationship_id, action = register_hyperlink(ctx, raw_target)
    metadata = {HYPERLINK_RID_KEY: relationship_id}
    if action is not None:
        metadata[HYPERLINK_ACTION_KEY] = action
    return metadata


def apply_shape_hyperlink(
    result: ShapeResult,
    ctx: ConvertContext,
    raw_target: str,
) -> ShapeResult:
    """Attach one click hyperlink to every clickable leaf object.

    DrawingML group containers are selection/animation structures, not a
    reliable click-action carrier across PowerPoint APIs. A multi-object SVG
    anchor therefore shares one relationship across each leaf ``p:cNvPr``.
    Authors use an explicit background shape when the whole rectangular button
    area, including gaps between descendants, must be clickable.
    """
    relationship_id, action = register_hyperlink(ctx, raw_target)
    hlink_xml = hyperlink_click_xml(relationship_id, action)
    group_ranges = [
        (match.start(), match.end())
        for match in _GROUP_NONVISUAL_RE.finditer(result.xml)
    ]
    replacements: list[tuple[int, int, str]] = []
    for match in _CNVPR_RE.finditer(result.xml):
        if any(start <= match.start() < end for start, end in group_ranges):
            continue
        original = match.group(0)
        if "<a:hlinkClick" in original:
            raise ValueError(
                "hyperlink carrier already contains a click hyperlink"
            )
        if original.endswith("/>"):
            replacement = f"{original[:-2]}>{hlink_xml}</p:cNvPr>"
        else:
            replacement = original.replace(
                "</p:cNvPr>",
                f"{hlink_xml}</p:cNvPr>",
                1,
            )
        replacements.append((match.start(), match.end(), replacement))

    if not replacements:
        raise ValueError(
            "hyperlink carrier did not produce a clickable DrawingML leaf"
        )
    linked_xml = result.xml
    for start, end, replacement in reversed(replacements):
        linked_xml = linked_xml[:start] + replacement + linked_xml[end:]
    return ShapeResult(xml=linked_xml, bounds_emu=result.bounds_emu)


__all__ = [
    "HYPERLINK_ACTION_KEY",
    "HYPERLINK_RID_KEY",
    "apply_shape_hyperlink",
    "hyperlink_click_xml",
    "hyperlink_run_metadata",
    "register_hyperlink",
]
