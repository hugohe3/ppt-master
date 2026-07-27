#!/usr/bin/env python3
"""
PPT Master - PPTX Transition Core

Provide one strict transition registry plus shared OOXML read/write helpers for
generated slides, template-filled PPTX files, and native PPTX enhancement.
See references/animations.md for the public workflow and
scripts/docs/pptx-transitions.md for the OOXML contract.

Usage:
    Import from PPT Master PPTX builders and direct-package workflows.

Examples:
    from pptx_transitions import AdvanceUpdate, EnterUpdate, apply_slide_motion

Dependencies:
    lxml (preferred for prefix-preserving source-PPTX mutation)
"""

from __future__ import annotations

import io
import math
import posixpath
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, MutableMapping
from xml.etree import ElementTree as ET
from xml.sax.saxutils import quoteattr

try:
    from lxml import etree as LET
except ImportError:
    LET = None


PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
P15_NS = "http://schemas.microsoft.com/office/powerpoint/2012/main"
P159_NS = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

PRESENTATION_PROPS_PART = "ppt/presProps.xml"
PRESENTATION_RELS_PART = "ppt/_rels/presentation.xml.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"
PRESENTATION_PROPS_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps"
)
PRESENTATION_PROPS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"
)

DEFAULT_TRANSITION = "fade"
DEFAULT_TRANSITION_DURATION = 0.4
MAX_OOXML_MILLISECONDS = 4_294_967_295
# OOXML stores millisecond values and identifiers (shape ids, time-node ids,
# preset codes) as xsd:unsignedInt, so both ceilings share one value.
MAX_OOXML_UNSIGNED_INT = MAX_OOXML_MILLISECONDS


TRANSITIONS: dict[str, dict[str, Any]] = {
    # Keep the original seven entries first for stable CLI/help ordering.
    "fade": {
        "name": "Fade",
        "element": "fade",
        "attrs": {},
    },
    "push": {
        "name": "Push",
        "element": "push",
        "attrs": {"dir": "r"},
    },
    "wipe": {
        "name": "Wipe",
        "element": "wipe",
        "attrs": {"dir": "r"},
    },
    "split": {
        "name": "Split",
        "element": "split",
        "attrs": {"orient": "horz", "dir": "out"},
    },
    "strips": {
        "name": "Strips",
        "element": "strips",
        "attrs": {"dir": "rd"},
    },
    "cover": {
        "name": "Cover",
        "element": "cover",
        "attrs": {"dir": "r"},
    },
    "random": {
        "name": "Random",
        "element": "random",
        "attrs": {},
    },
    "blinds": {
        "name": "Blinds",
        "element": "blinds",
        "attrs": {"dir": "vert"},
    },
    "checkerboard": {
        "name": "Checkerboard",
        "element": "checker",
        "attrs": {"dir": "horz"},
    },
    "circle": {
        "name": "Circle",
        "element": "circle",
        "attrs": {},
    },
    "comb": {
        "name": "Comb",
        "element": "comb",
        "attrs": {"dir": "horz"},
    },
    "cut": {
        "name": "Cut",
        "element": "cut",
        "attrs": {"thruBlk": "0"},
    },
    "diamond": {
        "name": "Diamond",
        "element": "diamond",
        "attrs": {},
    },
    "dissolve": {
        "name": "Dissolve",
        "element": "dissolve",
        "attrs": {},
    },
    "newsflash": {
        "name": "Newsflash",
        "element": "newsflash",
        "attrs": {},
    },
    "plus": {
        "name": "Plus",
        "element": "plus",
        "attrs": {},
    },
    "pull": {
        "name": "Pull",
        "element": "pull",
        "attrs": {"dir": "r"},
    },
    "random_bars": {
        "name": "Random Bars",
        "element": "randomBar",
        "attrs": {"dir": "vert"},
    },
    "wedge": {
        "name": "Wedge",
        "element": "wedge",
        "attrs": {},
    },
    "wheel": {
        "name": "Wheel",
        "element": "wheel",
        "attrs": {"spokes": "1"},
    },
    "zoom": {
        "name": "Zoom",
        "prefix": "p14",
        "element": "warp",
        "attrs": {"dir": "in"},
        "fallback": "fade",
    },
    # Current PowerPoint transition gallery: Subtle.
    "morph": {
        "name": "Morph",
        "prefix": "p159",
        "element": "morph",
        "attrs": {"option": "byObject"},
        "fallback": "fade",
    },
    "reveal": {
        "name": "Reveal",
        "prefix": "p14",
        "element": "reveal",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "shape": {
        "name": "Shape",
        "element": "circle",
        "attrs": {},
    },
    "uncover": {
        "name": "Uncover",
        "element": "pull",
        "attrs": {"dir": "r"},
    },
    "flash": {
        "name": "Flash",
        "prefix": "p14",
        "element": "flash",
        "attrs": {},
        "fallback": "fade",
    },
    # Current PowerPoint transition gallery: Exciting.
    "fall_over": {
        "name": "Fall Over",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "fallOver", "invX": "1"},
        "fallback": "fade",
    },
    "drape": {
        "name": "Drape",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "drape", "invX": "1"},
        "fallback": "fade",
    },
    "curtains": {
        "name": "Curtains",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "curtains"},
        "fallback": "fade",
    },
    "wind": {
        "name": "Wind",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "wind"},
        "fallback": "fade",
    },
    "prestige": {
        "name": "Prestige",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "prestige"},
        "fallback": "fade",
    },
    "fracture": {
        "name": "Fracture",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "fracture"},
        "fallback": "fade",
    },
    "crush": {
        "name": "Crush",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "crush"},
        "fallback": "fade",
    },
    "peel_off": {
        "name": "Peel Off",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "peelOff", "invX": "1"},
        "fallback": "fade",
    },
    "page_curl": {
        "name": "Page Curl",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "pageCurlSingle", "invX": "1"},
        "fallback": "fade",
    },
    "airplane": {
        "name": "Airplane",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "airplane"},
        "fallback": "fade",
    },
    "origami": {
        "name": "Origami",
        "prefix": "p15",
        "element": "prstTrans",
        "attrs": {"prst": "origami"},
        "fallback": "fade",
    },
    "clock": {
        "name": "Clock",
        "element": "wheel",
        "attrs": {"spokes": "1"},
    },
    "ripple": {
        "name": "Ripple",
        "prefix": "p14",
        "element": "ripple",
        "attrs": {},
        "fallback": "fade",
    },
    "honeycomb": {
        "name": "Honeycomb",
        "prefix": "p14",
        "element": "honeycomb",
        "attrs": {},
        "fallback": "fade",
    },
    "glitter": {
        "name": "Glitter",
        "prefix": "p14",
        "element": "glitter",
        "attrs": {},
        "fallback": "fade",
    },
    "vortex": {
        "name": "Vortex",
        "prefix": "p14",
        "element": "vortex",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "shred": {
        "name": "Shred",
        "prefix": "p14",
        "element": "shred",
        "attrs": {"dir": "out"},
        "fallback": "fade",
    },
    "switch": {
        "name": "Switch",
        "prefix": "p14",
        "element": "switch",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "flip": {
        "name": "Flip",
        "prefix": "p14",
        "element": "flip",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "gallery": {
        "name": "Gallery",
        "prefix": "p14",
        "element": "gallery",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "cube": {
        "name": "Cube",
        "prefix": "p14",
        "element": "prism",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "doors": {
        "name": "Doors",
        "prefix": "p14",
        "element": "doors",
        "attrs": {"dir": "vert"},
        "fallback": "fade",
    },
    "box": {
        "name": "Box",
        "element": "zoom",
        "attrs": {},
    },
    # Current PowerPoint transition gallery: Dynamic Content.
    "pan": {
        "name": "Pan",
        "prefix": "p14",
        "element": "pan",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "ferris_wheel": {
        "name": "Ferris Wheel",
        "prefix": "p14",
        "element": "ferris",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "conveyor": {
        "name": "Conveyor",
        "prefix": "p14",
        "element": "conveyor",
        "attrs": {"dir": "r"},
        "fallback": "fade",
    },
    "rotate": {
        "name": "Rotate",
        "prefix": "p14",
        "element": "prism",
        "attrs": {"dir": "r", "isContent": "1"},
        "fallback": "fade",
    },
    "window": {
        "name": "Window",
        "prefix": "p14",
        "element": "window",
        "attrs": {},
        "fallback": "fade",
    },
    "orbit": {
        "name": "Orbit",
        "prefix": "p14",
        "element": "prism",
        "attrs": {"dir": "r", "isContent": "1", "isInverted": "1"},
        "fallback": "fade",
    },
    "fly_through": {
        "name": "Fly Through",
        "prefix": "p14",
        "element": "flythrough",
        "attrs": {},
        "fallback": "fade",
    },
}

TRANSITION_NAMESPACES = {
    "p": PML_NS,
    "p14": P14_NS,
    "p15": P15_NS,
    "p159": P159_NS,
}

for _prefix, _uri in (
    *TRANSITION_NAMESPACES.items(),
    ("mc", MC_NS),
):
    try:
        ET.register_namespace(_prefix, _uri)
    except (AttributeError, ValueError):
        pass


@dataclass(frozen=True)
class EnterUpdate:
    """Describe how the current slide's visual transition enters."""

    policy: str = "replace"
    effect: str | None = DEFAULT_TRANSITION
    duration: float = DEFAULT_TRANSITION_DURATION


@dataclass(frozen=True)
class AdvanceUpdate:
    """Describe how the current slide advances to the next slide."""

    mode: str = "preserve"
    after: float | None = None


@dataclass(frozen=True)
class TransitionSummary:
    """Read-back summary of one slide's logical transition slot."""

    carrier: str
    logical_count: int
    effect: str | None = None
    effect_namespace: str | None = None
    fallback_effect: str | None = None
    fallback_effect_namespace: str | None = None
    duration_ms: int | None = None
    speed: str | None = None
    advance_on_click: bool | None = None
    advance_after_ms: int | None = None


def _qn(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _namespace_name(tag: str) -> str | None:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


def _value_repr(value: object) -> str:
    try:
        return repr(value)
    except Exception:
        return f"<{type(value).__name__}>"


def validate_seconds(
    value: object,
    field: str,
    *,
    allow_zero: bool,
) -> float:
    """Return a finite seconds value or raise a field-specific error."""
    display_value = _value_repr(value)
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number, not {display_value}")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            f"{field} must be a finite number: {display_value}"
        ) from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite: {display_value}")
    if allow_zero:
        if number < 0:
            raise ValueError(f"{field} must be non-negative: {display_value}")
    elif number <= 0:
        raise ValueError(f"{field} must be greater than zero: {display_value}")
    return number


def normalize_transition_effect(effect: object, *, allow_none: bool = True) -> str | None:
    """Return a known transition effect without silently changing it."""
    if effect is None or effect == "none":
        if allow_none:
            return None
        raise ValueError("transition effect is required")
    if not isinstance(effect, str):
        raise ValueError(f"transition effect must be a string: {effect!r}")
    if effect not in TRANSITIONS:
        valid = ", ".join(sorted(TRANSITIONS))
        raise ValueError(
            f"unknown transition effect {effect!r}; valid effects: {valid}, none"
        )
    return effect


def _seconds_to_ms(value: object, field: str, *, allow_zero: bool) -> int:
    seconds = validate_seconds(value, field, allow_zero=allow_zero)
    raw_milliseconds = seconds * 1000
    if (
        not math.isfinite(raw_milliseconds)
        or raw_milliseconds > MAX_OOXML_MILLISECONDS
    ):
        raise ValueError(
            f"{field} exceeds the OOXML millisecond limit: {value!r}"
        )
    milliseconds = int(raw_milliseconds)
    return milliseconds if allow_zero else max(1, milliseconds)


def _effect_spec(effect: str) -> tuple[str, str, str, dict[str, Any], str | None]:
    info = TRANSITIONS[effect]
    prefix = str(info.get("prefix", "p"))
    namespace = TRANSITION_NAMESPACES[prefix]
    element = str(info["element"])
    attrs = dict(info.get("attrs", {}))
    fallback = info.get("fallback")
    return prefix, namespace, element, attrs, str(fallback) if fallback else None


def _effect_xml(effect: str) -> tuple[str, str, str]:
    prefix, _namespace, element, effect_attrs, _fallback = _effect_spec(effect)
    attrs = " ".join(
        f'{key}="{value}"'
        for key, value in effect_attrs.items()
    )
    suffix = f" {attrs}" if attrs else ""
    return prefix, element, suffix


def _transition_attributes(
    *,
    duration_ms: int | None,
    advance_after_ms: int | None,
    advance_on_click: bool | None,
    declare_p14: bool,
) -> str:
    attrs: list[str] = []
    if duration_ms is not None:
        attrs.append(f'p14:dur="{duration_ms}"')
    if declare_p14:
        attrs.append(f'xmlns:p14="{P14_NS}"')
    if advance_on_click is not None:
        attrs.append(f'advClick="{1 if advance_on_click else 0}"')
    if advance_after_ms is not None:
        attrs.append(f'advTm="{advance_after_ms}"')
    return " " + " ".join(attrs) if attrs else ""


def create_transition_xml(
    effect: str | None = DEFAULT_TRANSITION,
    duration: float = 0.5,
    advance_after: float | None = None,
    advance_on_click: bool | None = None,
) -> str:
    """Build a direct or MCE-backed p:transition XML fragment."""
    normalized_effect = normalize_transition_effect(effect)
    duration_ms = None
    if normalized_effect is not None:
        duration_ms = _seconds_to_ms(
            duration,
            "transition duration",
            allow_zero=False,
        )
    if advance_on_click is not None:
        if not isinstance(advance_on_click, bool):
            raise ValueError(
                "transition advance_on_click must be a boolean or None"
            )
    advance_ms = None
    if advance_after is not None:
        advance_ms = _seconds_to_ms(
            advance_after,
            "transition advance_after",
            allow_zero=True,
        )

    if (
        normalized_effect is None
        and advance_ms is None
        and advance_on_click is None
    ):
        return ""

    attr_text = _transition_attributes(
        duration_ms=duration_ms,
        advance_after_ms=advance_ms,
        advance_on_click=advance_on_click,
        declare_p14=normalized_effect is not None,
    )
    if normalized_effect is None:
        return f"  <p:transition{attr_text}/>"

    prefix, element_name, effect_attrs = _effect_xml(normalized_effect)
    if prefix != "p":
        _effect_prefix, _namespace, _element, _attrs, fallback = _effect_spec(
            normalized_effect
        )
        fallback_effect = fallback or "fade"
        fallback_prefix, fallback_name, fallback_attrs = _effect_xml(
            fallback_effect
        )
        fallback_attr_text = _transition_attributes(
            duration_ms=None,
            advance_after_ms=advance_ms,
            advance_on_click=advance_on_click,
            declare_p14=False,
        )
        return (
            f'  <mc:AlternateContent xmlns:mc="{MC_NS}">\n'
            f'    <mc:Choice xmlns:{prefix}="{TRANSITION_NAMESPACES[prefix]}" '
            f'Requires="{prefix}">\n'
            f"      <p:transition{attr_text}>\n"
            f"        <{prefix}:{element_name}{effect_attrs}/>\n"
            "      </p:transition>\n"
            "    </mc:Choice>\n"
            "    <mc:Fallback>\n"
            f"      <p:transition{fallback_attr_text}>\n"
            f"        <{fallback_prefix}:{fallback_name}{fallback_attrs}/>\n"
            "      </p:transition>\n"
            "    </mc:Fallback>\n"
            "  </mc:AlternateContent>"
        )
    return (
        f"  <p:transition{attr_text}>\n"
        f"    <{prefix}:{element_name}{effect_attrs}/>\n"
        "  </p:transition>"
    )


def _is_lxml_element(element: object) -> bool:
    return LET is not None and isinstance(element, LET._Element)


def _new_element(
    context: Any,
    tag: str,
    *,
    nsmap: dict[str, str] | None = None,
) -> Any:
    if _is_lxml_element(context):
        return LET.Element(tag, nsmap=nsmap)
    return ET.Element(tag)


def _build_transition_element(
    context: Any,
    *,
    effect: str | None,
    duration: float,
    advance_after: float | None,
    advance_on_click: bool | None,
) -> Any | None:
    normalized_effect = normalize_transition_effect(effect)
    if (
        normalized_effect is None
        and advance_after is None
        and advance_on_click is not False
    ):
        return None

    if advance_on_click is not None:
        if not isinstance(advance_on_click, bool):
            raise ValueError(
                "transition advance_on_click must be a boolean or None"
            )
    duration_ms = (
        _seconds_to_ms(
            duration,
            "transition duration",
            allow_zero=False,
        )
        if normalized_effect is not None
        else None
    )
    advance_ms = (
        _seconds_to_ms(
            advance_after,
            "transition advance_after",
            allow_zero=True,
        )
        if advance_after is not None
        else None
    )

    def build_transition(
        effect_name: str | None,
        *,
        include_duration: bool,
    ) -> Any:
        nsmap = {"p": PML_NS}
        if include_duration:
            nsmap["p14"] = P14_NS
        transition = _new_element(
            context,
            _qn(PML_NS, "transition"),
            nsmap=nsmap,
        )
        if include_duration and duration_ms is not None:
            transition.set(_qn(P14_NS, "dur"), str(duration_ms))
        if advance_on_click is not None:
            transition.set("advClick", "1" if advance_on_click else "0")
        if advance_ms is not None:
            transition.set("advTm", str(advance_ms))
        if effect_name is not None:
            _prefix, namespace, element_name, effect_attrs, _fallback = (
                _effect_spec(effect_name)
            )
            child = _new_element(context, _qn(namespace, element_name))
            for key, value in effect_attrs.items():
                child.set(key, str(value))
            transition.append(child)
        return transition

    if normalized_effect is None:
        return build_transition(None, include_duration=False)

    prefix, _namespace, _element, _attrs, fallback = _effect_spec(
        normalized_effect
    )
    if prefix == "p":
        return build_transition(normalized_effect, include_duration=True)

    carrier = _new_element(
        context,
        _qn(MC_NS, "AlternateContent"),
        nsmap={"mc": MC_NS},
    )
    choice = _new_element(
        context,
        _qn(MC_NS, "Choice"),
        nsmap={prefix: TRANSITION_NAMESPACES[prefix]},
    )
    choice.set("Requires", prefix)
    choice.append(build_transition(normalized_effect, include_duration=True))
    fallback_node = _new_element(context, _qn(MC_NS, "Fallback"))
    fallback_node.append(
        build_transition(fallback or "fade", include_duration=False)
    )
    carrier.extend((choice, fallback_node))
    return carrier


def _transition_elements(carrier: Any) -> list[Any]:
    if carrier.tag == _qn(PML_NS, "transition"):
        return [carrier]
    return [
        element
        for element in carrier.iter()
        if element.tag == _qn(PML_NS, "transition")
    ]


def transition_carriers(slide_root: Any) -> list[Any]:
    """Return root-level direct or AlternateContent transition carriers."""
    carriers: list[Any] = []
    for child in list(slide_root):
        if child.tag == _qn(PML_NS, "transition"):
            carriers.append(child)
            continue
        if child.tag != _qn(MC_NS, "AlternateContent"):
            continue
        if _transition_elements(child):
            carriers.append(child)
    return carriers


def _primary_and_fallback(carrier: Any) -> tuple[Any | None, Any | None]:
    if carrier.tag == _qn(PML_NS, "transition"):
        return carrier, None

    primary = None
    fallback = None
    for child in list(carrier):
        transitions = _transition_elements(child)
        if not transitions:
            continue
        if child.tag == _qn(MC_NS, "Choice") and primary is None:
            primary = transitions[0]
        elif child.tag == _qn(MC_NS, "Fallback") and fallback is None:
            fallback = transitions[0]
    if primary is None:
        transitions = _transition_elements(carrier)
        primary = transitions[0] if transitions else None
    return primary, fallback


def _effect_identity(transition: Any | None) -> tuple[str | None, str | None]:
    if transition is None:
        return None, None
    for child in list(transition):
        if child.tag == _qn(PML_NS, "sndAc"):
            continue
        return _local_name(child.tag), _namespace_name(child.tag)
    return None, None


def _int_attribute(element: Any | None, *names: str) -> int | None:
    if element is None:
        return None
    for name in names:
        raw = element.get(name)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    return None


def _bool_attribute(element: Any, name: str, default: bool) -> bool:
    raw = element.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() not in {"0", "false", "off", "no"}


def read_slide_transition(slide_root: Any) -> TransitionSummary:
    """Read the primary transition without mistaking fallback for success."""
    carriers = transition_carriers(slide_root)
    if not carriers:
        return TransitionSummary(carrier="none", logical_count=0)

    carrier = carriers[0]
    primary, fallback = _primary_and_fallback(carrier)
    effect, effect_namespace = _effect_identity(primary)
    fallback_effect, fallback_namespace = _effect_identity(fallback)
    carrier_name = (
        "alternate-content"
        if carrier.tag == _qn(MC_NS, "AlternateContent")
        else "direct"
    )
    duration_ms = _int_attribute(
        primary,
        _qn(P14_NS, "dur"),
        "dur",
    )
    advance_after_ms = _int_attribute(primary, "advTm")
    return TransitionSummary(
        carrier=carrier_name if len(carriers) == 1 else "multiple",
        logical_count=len(carriers),
        effect=effect,
        effect_namespace=effect_namespace,
        fallback_effect=fallback_effect,
        fallback_effect_namespace=fallback_namespace,
        duration_ms=duration_ms,
        speed=primary.get("spd") if primary is not None else None,
        advance_on_click=(
            _bool_attribute(primary, "advClick", True)
            if primary is not None
            else None
        ),
        advance_after_ms=advance_after_ms,
    )


def _captured_advance(carriers: list[Any]) -> tuple[bool | None, float | None]:
    if not carriers:
        return None, None
    primary, _fallback = _primary_and_fallback(carriers[0])
    if primary is None:
        return None, None
    click = (
        _bool_attribute(primary, "advClick", True)
        if primary.get("advClick") is not None
        else None
    )
    advance_ms = _int_attribute(primary, "advTm")
    after = advance_ms / 1000 if advance_ms is not None else None
    return click, after


def _resolve_advance(
    update: AdvanceUpdate,
    *,
    preserved_click: bool | None,
    preserved_after: float | None,
) -> tuple[bool | None, float | None]:
    valid_modes = {"preserve", "click", "after", "both", "narration"}
    if update.mode not in valid_modes:
        raise ValueError(
            f"unknown slide advance mode {update.mode!r}; "
            f"valid modes: {', '.join(sorted(valid_modes))}"
        )
    if update.mode == "preserve":
        return preserved_click, preserved_after
    if update.mode == "click":
        return True, None
    if update.after is None:
        raise ValueError(f"slide advance mode {update.mode!r} requires 'after'")
    after = validate_seconds(
        update.after,
        "slide advance after",
        allow_zero=True,
    )
    if update.mode == "both":
        return True, after
    return False, after


def _set_advance_attributes(
    transition: Any,
    *,
    advance_on_click: bool | None,
    advance_after: float | None,
) -> None:
    if advance_on_click is None:
        transition.attrib.pop("advClick", None)
    else:
        transition.set("advClick", "1" if advance_on_click else "0")
    if advance_after is None:
        transition.attrib.pop("advTm", None)
    else:
        transition.set(
            "advTm",
            str(
                _seconds_to_ms(
                    advance_after,
                    "slide advance after",
                    allow_zero=True,
                )
            ),
        )


def _insert_transition_carrier(slide_root: Any, carrier: Any) -> None:
    children = list(slide_root)
    for index, child in enumerate(children):
        if child.tag in {
            _qn(PML_NS, "timing"),
            _qn(PML_NS, "extLst"),
        }:
            slide_root.insert(index, carrier)
            return

    clr_map = None
    for child in children:
        if child.tag == _qn(PML_NS, "clrMapOvr"):
            clr_map = child
    if clr_map is not None:
        slide_root.insert(list(slide_root).index(clr_map) + 1, carrier)
        return
    slide_root.append(carrier)


def _apply_slide_motion_unchecked(
    slide_root: Any,
    *,
    enter: EnterUpdate,
    advance: AdvanceUpdate,
) -> bool:
    """Apply one resolved enter/advance update and return whether advTm remains."""
    valid_policies = {"preserve", "replace", "none"}
    if enter.policy not in valid_policies:
        raise ValueError(
            f"unknown transition enter policy {enter.policy!r}; "
            f"valid policies: {', '.join(sorted(valid_policies))}"
        )

    carriers = transition_carriers(slide_root)
    if len(carriers) > 1:
        raise ValueError(
            "slide contains multiple logical transition carriers; "
            "refusing to preserve or replace an ambiguous source"
        )

    preserved_click, preserved_after = _captured_advance(carriers)
    advance_on_click, advance_after = _resolve_advance(
        advance,
        preserved_click=preserved_click,
        preserved_after=preserved_after,
    )

    if enter.policy == "preserve":
        if advance.mode == "preserve":
            return any(
                transition.get("advTm") is not None
                for carrier in carriers
                for transition in _transition_elements(carrier)
            )
        if carriers:
            for transition in _transition_elements(carriers[0]):
                _set_advance_attributes(
                    transition,
                    advance_on_click=advance_on_click,
                    advance_after=advance_after,
                )
            return advance_after is not None

        transition = _build_transition_element(
            slide_root,
            effect=None,
            duration=enter.duration,
            advance_after=advance_after,
            advance_on_click=advance_on_click,
        )
        if transition is not None:
            _insert_transition_carrier(slide_root, transition)
        return advance_after is not None

    effect = (
        normalize_transition_effect(enter.effect, allow_none=False)
        if enter.policy == "replace"
        else None
    )
    duration = validate_seconds(
        enter.duration,
        "transition duration",
        allow_zero=False,
    )

    if carriers:
        slide_root.remove(carriers[0])

    transition = _build_transition_element(
        slide_root,
        effect=effect,
        duration=duration,
        advance_after=advance_after,
        advance_on_click=advance_on_click,
    )
    if transition is not None:
        _insert_transition_carrier(slide_root, transition)
    return advance_after is not None


def _visual_identity(summary: TransitionSummary) -> tuple[Any, ...]:
    return (
        summary.carrier,
        summary.logical_count,
        summary.effect,
        summary.effect_namespace,
        summary.fallback_effect,
        summary.fallback_effect_namespace,
        summary.duration_ms,
        summary.speed,
    )


def _expected_visual_identity(
    effect: str,
) -> tuple[str, str, str, str | None, str | None, dict[str, Any]]:
    prefix, namespace, element, attrs, fallback = _effect_spec(effect)
    carrier = "direct" if prefix == "p" else "alternate-content"
    fallback_element = None
    fallback_namespace = None
    if carrier == "alternate-content":
        (
            _fallback_prefix,
            fallback_namespace,
            fallback_element,
            _fallback_attrs,
            _nested_fallback,
        ) = _effect_spec(fallback or "fade")
    return (
        carrier,
        element,
        namespace,
        fallback_element,
        fallback_namespace,
        attrs,
    )


def _validate_applied_motion(
    slide_root: Any,
    *,
    before: TransitionSummary,
    enter: EnterUpdate,
    advance: AdvanceUpdate,
) -> None:
    errors = validate_slide_transition_structure(slide_root)
    after = read_slide_transition(slide_root)

    if enter.policy == "preserve":
        if before.logical_count and _visual_identity(after) != _visual_identity(before):
            errors.append("preserve policy changed the source visual transition")
        elif not before.logical_count and after.effect is not None:
            errors.append("preserve policy added a visual transition")
    elif enter.policy == "replace":
        effect = normalize_transition_effect(enter.effect, allow_none=False)
        expected_duration = _seconds_to_ms(
            enter.duration,
            "transition duration",
            allow_zero=False,
        )
        (
            expected_carrier,
            expected_effect,
            expected_namespace,
            expected_fallback,
            expected_fallback_namespace,
            expected_attrs,
        ) = _expected_visual_identity(effect)
        if (
            after.carrier != expected_carrier
            or after.logical_count != 1
            or after.effect != expected_effect
            or after.effect_namespace != expected_namespace
            or after.fallback_effect != expected_fallback
            or after.fallback_effect_namespace != expected_fallback_namespace
            or after.duration_ms != expected_duration
        ):
            errors.append(
                f"replace policy read-back does not match effect {effect!r}"
            )
        carriers = transition_carriers(slide_root)
        if carriers:
            primary, _fallback = _primary_and_fallback(carriers[0])
            effect_children = [
                child
                for child in (list(primary) if primary is not None else [])
                if child.tag != _qn(PML_NS, "sndAc")
            ]
            if effect_children:
                actual_attrs = effect_children[0].attrib
                for name, value in expected_attrs.items():
                    if actual_attrs.get(name) != str(value):
                        errors.append(
                            f"replace policy wrote invalid {effect} {name} attribute"
                        )
    elif enter.policy == "none":
        if after.effect is not None or after.fallback_effect is not None:
            errors.append("none policy retained a visual transition")

    preserved_click = (
        before.advance_on_click
        if before.advance_on_click is not None
        else True
    )
    preserved_after = (
        before.advance_after_ms / 1000
        if before.advance_after_ms is not None
        else None
    )
    expected_click, expected_after = _resolve_advance(
        advance,
        preserved_click=preserved_click,
        preserved_after=preserved_after,
    )
    actual_click = (
        after.advance_on_click
        if after.advance_on_click is not None
        else True
    )
    actual_after_ms = after.advance_after_ms
    expected_after_ms = (
        _seconds_to_ms(
            expected_after,
            "transition advance_after",
            allow_zero=True,
        )
        if expected_after is not None
        else None
    )
    if actual_click != expected_click or actual_after_ms != expected_after_ms:
        errors.append("transition advance read-back does not match the requested mode")
    if advance.mode != "preserve":
        for carrier in transition_carriers(slide_root):
            for transition in _transition_elements(carrier):
                branch_click = _bool_attribute(transition, "advClick", True)
                branch_after_ms = _int_attribute(transition, "advTm")
                if (
                    branch_click != expected_click
                    or branch_after_ms != expected_after_ms
                ):
                    errors.append(
                        "transition fallback advance does not match the requested mode"
                    )
                    break

    if errors:
        raise ValueError("; ".join(errors))


def apply_slide_motion(
    slide_root: Any,
    *,
    enter: EnterUpdate,
    advance: AdvanceUpdate,
) -> bool:
    """Apply and immediately read back one resolved transition update."""
    before = read_slide_transition(slide_root)
    uses_timings = _apply_slide_motion_unchecked(
        slide_root,
        enter=enter,
        advance=advance,
    )
    _validate_applied_motion(
        slide_root,
        before=before,
        enter=enter,
        advance=advance,
    )
    return uses_timings


def _xml_declaration(source: str) -> str:
    match = re.match(r"\s*(<\?xml[^?]*\?>)", source)
    return match.group(1) if match else ""


def _serialize_lxml_like(root: Any, source: str) -> str:
    body = LET.tostring(root, encoding="unicode", pretty_print=False)
    declaration = _xml_declaration(source)
    return f"{declaration}\n{body}" if declaration else body


def namespace_bindings(xml_data: str | bytes) -> dict[str, str]:
    """Return source prefix bindings without changing the document."""
    data = xml_data.encode("utf-8") if isinstance(xml_data, str) else xml_data
    bindings: dict[str, str] = {}
    for _event, (prefix, uri) in ET.iterparse(
        io.BytesIO(data),
        events=("start-ns",),
    ):
        bindings[prefix or ""] = uri
    return bindings


def register_source_namespaces(xml_data: str | bytes) -> dict[str, str]:
    """Register source prefixes before stdlib ElementTree re-serialization."""
    bindings = namespace_bindings(xml_data)
    for prefix, uri in bindings.items():
        if prefix == "xml":
            continue
        try:
            ET.register_namespace(prefix, uri)
        except (AttributeError, ValueError):
            continue
    return bindings


def parse_source_xml(xml_data: str | bytes) -> ET.Element:
    """Parse XML after registering its original namespace prefixes."""
    data = xml_data.encode("utf-8") if isinstance(xml_data, str) else xml_data
    register_source_namespaces(data)
    return ET.fromstring(data)


def _required_mce_prefixes(root: Any) -> set[str]:
    prefixes = set(str(root.get(_qn(MC_NS, "Ignorable")) or "").split())
    for element in root.iter():
        if element.tag == _qn(MC_NS, "Choice"):
            prefixes.update(str(element.get("Requires") or "").split())
    return {prefix for prefix in prefixes if prefix}


def _inject_root_namespace_declarations(
    xml_data: bytes,
    *,
    bindings: dict[str, str],
    prefixes: set[str],
) -> bytes:
    text = xml_data.decode("utf-8")
    declaration_end = text.find("?>")
    root_start = text.find("<", declaration_end + 2 if declaration_end >= 0 else 0)
    root_end = text.find(">", root_start)
    if root_start < 0 or root_end < 0:
        raise ValueError("unable to locate serialized XML root element")

    opening = text[root_start:root_end]
    declarations: list[str] = []
    for prefix in sorted(prefixes):
        uri = bindings.get(prefix)
        if not uri:
            raise ValueError(
                f"MCE prefix {prefix!r} has no namespace binding in source XML"
            )
        if re.search(rf"\bxmlns:{re.escape(prefix)}\s*=", opening):
            continue
        declarations.append(f" xmlns:{prefix}={quoteattr(uri)}")
    if declarations:
        text = text[:root_end] + "".join(declarations) + text[root_end:]
    return text.encode("utf-8")


def validate_mce_prefixes(xml_data: str | bytes) -> list[str]:
    """Return unresolved MCE Requires/Ignorable prefix errors."""
    if LET is None:
        return []
    data = xml_data.encode("utf-8") if isinstance(xml_data, str) else xml_data
    try:
        root = LET.fromstring(data)
    except LET.XMLSyntaxError as exc:
        return [f"invalid XML: {exc}"]

    errors: list[str] = []
    ignorable = str(root.get(_qn(MC_NS, "Ignorable")) or "").split()
    for prefix in ignorable:
        if prefix not in root.nsmap:
            errors.append(f"mc:Ignorable prefix is not bound: {prefix}")
    for choice in root.iter(_qn(MC_NS, "Choice")):
        for prefix in str(choice.get("Requires") or "").split():
            if prefix not in choice.nsmap:
                errors.append(f"mc:Choice Requires prefix is not bound: {prefix}")
    return errors


def serialize_source_xml(root: ET.Element, source_xml: str | bytes) -> bytes:
    """Serialize stdlib XML while retaining MCE prefix bindings."""
    expected_transition = (
        read_slide_transition(root)
        if root.tag == _qn(PML_NS, "sld")
        else None
    )
    source = (
        source_xml.encode("utf-8")
        if isinstance(source_xml, str)
        else source_xml
    )
    bindings = register_source_namespaces(source)
    prefixes = _required_mce_prefixes(root)
    for prefix in prefixes:
        namespace = TRANSITION_NAMESPACES.get(prefix)
        if namespace is None:
            continue
        bindings[prefix] = namespace
        ET.register_namespace(prefix, namespace)
    serialized = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    serialized = _inject_root_namespace_declarations(
        serialized,
        bindings=bindings,
        prefixes=prefixes,
    )
    errors = validate_mce_prefixes(serialized)
    if expected_transition is not None:
        errors.extend(validate_slide_transition_xml(serialized))
        actual_transition = read_slide_transition_xml(serialized)
        if actual_transition != expected_transition:
            errors.append("slide transition changed during XML serialization")
    if errors:
        raise ValueError("; ".join(errors))
    return serialized


def apply_slide_motion_xml(
    slide_xml: str,
    *,
    enter: EnterUpdate,
    advance: AdvanceUpdate,
) -> tuple[str, bool]:
    """Apply motion to source XML while preserving MCE namespace prefixes."""
    source_bytes = slide_xml.encode("utf-8")
    if LET is not None:
        parser = LET.XMLParser(
            remove_blank_text=False,
            resolve_entities=False,
            no_network=True,
        )
        root = LET.fromstring(source_bytes, parser)
        uses_timings = apply_slide_motion(
            root,
            enter=enter,
            advance=advance,
        )
        output = _serialize_lxml_like(root, slide_xml)
    else:
        root = parse_source_xml(source_bytes)
        uses_timings = apply_slide_motion(
            root,
            enter=enter,
            advance=advance,
        )
        output = serialize_source_xml(root, source_bytes).decode("utf-8")

    expected_transition = read_slide_transition(root)
    errors = validate_slide_transition_xml(output)
    if read_slide_transition_xml(output) != expected_transition:
        errors.append("slide transition changed during XML serialization")
    if errors:
        raise ValueError("; ".join(errors))
    return output, uses_timings


def read_slide_transition_xml(slide_xml: str | bytes) -> TransitionSummary:
    """Read a transition summary from raw slide XML."""
    data = (
        slide_xml.encode("utf-8")
        if isinstance(slide_xml, str)
        else slide_xml
    )
    if LET is not None:
        root = LET.fromstring(data)
    else:
        root = parse_source_xml(data)
    return read_slide_transition(root)


def validate_generated_transition_xml(
    slide_xml: str | bytes,
    *,
    effect: str | None,
    duration: object,
    advance_on_click: bool | None,
    advance_after: object | None,
) -> TransitionSummary:
    """Validate a generated transition against its resolved settings."""
    data = slide_xml.encode("utf-8") if isinstance(slide_xml, str) else slide_xml
    root = LET.fromstring(data) if LET is not None else parse_source_xml(data)
    errors = validate_slide_transition_structure(root) + validate_mce_prefixes(data)
    summary = read_slide_transition(root)
    normalized_effect = normalize_transition_effect(effect)
    expected_click = True if advance_on_click is None else advance_on_click
    if not isinstance(expected_click, bool):
        errors.append("transition advance_on_click must be a boolean or None")
    expected_after_ms = (
        _seconds_to_ms(
            advance_after,
            "transition advance_after",
            allow_zero=True,
        )
        if advance_after is not None
        else None
    )
    expects_carrier = (
        normalized_effect is not None
        or expected_after_ms is not None
        or expected_click is False
    )

    if not expects_carrier:
        if summary.logical_count != 0:
            errors.append("generated slide unexpectedly contains a transition carrier")
    else:
        expected_duration_ms = (
            _seconds_to_ms(
                duration,
                "transition duration",
                allow_zero=False,
            )
            if normalized_effect is not None
            else None
        )
        expected_carrier = "direct"
        expected_effect = None
        expected_namespace = None
        expected_fallback = None
        expected_fallback_namespace = None
        expected_attrs: dict[str, Any] = {}
        if normalized_effect is not None:
            (
                expected_carrier,
                expected_effect,
                expected_namespace,
                expected_fallback,
                expected_fallback_namespace,
                expected_attrs,
            ) = _expected_visual_identity(normalized_effect)
        if (
            summary.carrier != expected_carrier
            or summary.logical_count != 1
            or summary.effect != expected_effect
            or summary.effect_namespace != expected_namespace
            or summary.fallback_effect != expected_fallback
            or summary.fallback_effect_namespace != expected_fallback_namespace
            or summary.duration_ms != expected_duration_ms
            or summary.advance_on_click != expected_click
            or summary.advance_after_ms != expected_after_ms
        ):
            errors.append("generated transition read-back does not match its settings")
        if normalized_effect is not None:
            carriers = transition_carriers(root)
            if carriers:
                primary, _fallback = _primary_and_fallback(carriers[0])
                effect_children = [
                    child
                    for child in (list(primary) if primary is not None else [])
                    if child.tag != _qn(PML_NS, "sndAc")
                ]
                if not effect_children:
                    errors.append("generated transition has no visual effect child")
                else:
                    for name, value in expected_attrs.items():
                        if effect_children[0].get(name) != str(value):
                            errors.append(
                                f"generated {normalized_effect} transition has "
                                f"invalid {name} attribute"
                            )

    if errors:
        raise ValueError("; ".join(errors))
    return summary


def validate_pptx_transition_package(
    pptx_path: Path,
    *,
    require_use_timings: bool = False,
) -> dict[str, TransitionSummary]:
    """Read back and validate every slide transition in a written PPTX.

    Return summaries keyed by package part name. Raise ``ValueError`` when the
    ZIP, slide transition structure, MCE bindings, or required presentation
    timing metadata is invalid.
    """
    errors: list[str] = []
    summaries: dict[str, TransitionSummary] = {}
    try:
        with zipfile.ZipFile(pptx_path, "r") as package:
            names = package.namelist()
            part_counts: dict[str, int] = {}
            for name in names:
                part_counts[name] = part_counts.get(name, 0) + 1
            duplicate_names = sorted(
                name for name, count in part_counts.items() if count > 1
            )
            if duplicate_names:
                errors.append(
                    "duplicate package parts: " + ", ".join(duplicate_names)
                )

            slide_names = sorted(
                name
                for name in names
                if name.startswith("ppt/slides/slide")
                and name.endswith(".xml")
            )
            for slide_name in slide_names:
                slide_xml = package.read(slide_name)
                for problem in validate_slide_transition_xml(slide_xml):
                    errors.append(f"{slide_name}: {problem}")
                try:
                    summaries[slide_name] = read_slide_transition_xml(slide_xml)
                except Exception as exc:
                    errors.append(f"{slide_name}: transition read-back failed: {exc}")

            if require_use_timings:
                errors.extend(_validate_package_use_timings(package, names))
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        errors.append(f"unable to read PPTX transition package: {exc}")

    if errors:
        raise ValueError("; ".join(errors))
    return summaries


def _validate_package_use_timings(
    package: zipfile.ZipFile,
    names: list[str],
) -> list[str]:
    errors: list[str] = []
    required_parts = {
        PRESENTATION_RELS_PART,
        CONTENT_TYPES_PART,
    }
    missing = sorted(required_parts - set(names))
    if missing:
        return ["timed advance is missing package parts: " + ", ".join(missing)]

    rels_root = ET.fromstring(package.read(PRESENTATION_RELS_PART))
    props_part = _presentation_props_part(rels_root)
    if props_part is None:
        return ["presentation relationships do not reference presentation properties"]
    if props_part not in names:
        return [f"presentation properties part is missing: {props_part}"]

    props_root = ET.fromstring(package.read(props_part))
    show_properties = props_root.find(_qn(PML_NS, "showPr"))
    if (
        show_properties is None
        or show_properties.get("useTimings") not in {"1", "true", "on"}
    ):
        errors.append(f"{props_part} must set p:showPr@useTimings=1")

    content_root = ET.fromstring(package.read(CONTENT_TYPES_PART))
    package_part_name = "/" + props_part.lstrip("/")
    if not any(
        override.get("PartName") == package_part_name
        and override.get("ContentType") == PRESENTATION_PROPS_CONTENT_TYPE
        for override in content_root
    ):
        errors.append(f"[Content_Types].xml must declare {props_part}")
    return errors


def validate_slide_transition_structure(slide_root: Any) -> list[str]:
    """Return logical-carrier and schema-order errors for one slide root."""
    errors: list[str] = []
    children = list(slide_root)
    carriers = transition_carriers(slide_root)
    if len(carriers) > 1:
        errors.append(
            f"slide has {len(carriers)} logical transition carriers; expected at most 1"
        )
    if carriers:
        carrier_index = children.index(carriers[0])
        common_slide = next(
            (
                child
                for child in children
                if child.tag == _qn(PML_NS, "cSld")
            ),
            None,
        )
        if common_slide is None:
            errors.append("slide with transition carrier must contain p:cSld")
        elif carrier_index < children.index(common_slide):
            errors.append("transition carrier must follow p:cSld")
        color_map = next(
            (
                child
                for child in children
                if child.tag == _qn(PML_NS, "clrMapOvr")
            ),
            None,
        )
        if color_map is not None and carrier_index < children.index(color_map):
            errors.append("transition carrier must follow p:clrMapOvr")
        for tag in ("timing", "extLst"):
            element = next(
                (
                    child
                    for child in children
                    if child.tag == _qn(PML_NS, tag)
                ),
                None,
            )
            if element is not None and carrier_index > children.index(element):
                errors.append(f"transition carrier must precede p:{tag}")

    for carrier in carriers:
        if carrier.tag != _qn(MC_NS, "AlternateContent"):
            continue
        choices = [
            child
            for child in list(carrier)
            if child.tag == _qn(MC_NS, "Choice")
        ]
        if not choices:
            errors.append("mc:AlternateContent transition must contain mc:Choice")
        for branch_name in ("Choice", "Fallback"):
            branches = [
                child
                for child in list(carrier)
                if child.tag == _qn(MC_NS, branch_name)
            ]
            for branch in branches:
                count = len(_transition_elements(branch))
                if count != 1:
                    errors.append(
                        f"mc:{branch_name} must contain exactly one p:transition; "
                        f"found {count}"
                    )
    return errors


def validate_slide_transition_xml(slide_xml: str | bytes) -> list[str]:
    """Validate raw slide transition structure and MCE prefix bindings."""
    data = slide_xml.encode("utf-8") if isinstance(slide_xml, str) else slide_xml
    try:
        if LET is not None:
            root = LET.fromstring(data)
        else:
            root = parse_source_xml(data)
    except Exception as exc:
        return [f"invalid slide XML: {exc}"]
    return validate_slide_transition_structure(root) + validate_mce_prefixes(data)


def _insert_show_properties(root: Any, element: Any) -> None:
    for index, child in enumerate(list(root)):
        if child.tag in {
            _qn(PML_NS, "clrMru"),
            _qn(PML_NS, "extLst"),
        }:
            root.insert(index, element)
            return
    root.append(element)


def _next_relationship_id(rels_xml: str) -> str:
    root = ET.fromstring(rels_xml)
    numbers: list[int] = []
    for relationship in root:
        match = re.fullmatch(r"rId(\d+)", relationship.get("Id", ""))
        if match is not None:
            numbers.append(int(match.group(1)))
    return f"rId{max(numbers, default=0) + 1}"


def _presentation_props_part(rels_root: Any) -> str | None:
    for relationship in rels_root:
        if relationship.get("Type") != PRESENTATION_PROPS_REL_TYPE:
            continue
        if relationship.get("TargetMode") == "External":
            raise ValueError("presentation properties relationship must be internal")
        target = str(relationship.get("Target") or "").replace("\\", "/")
        if not target:
            raise ValueError("presentation properties relationship has no target")
        if target.startswith("/"):
            part_name = target.lstrip("/")
        else:
            part_name = posixpath.normpath(posixpath.join("ppt", target))
        if part_name == ".." or part_name.startswith("../"):
            raise ValueError(
                "presentation properties relationship escapes the PPTX package"
            )
        return part_name
    return None


def _ensure_presentation_props_references(
    parts: MutableMapping[str, bytes],
    *,
    props_part: str,
) -> None:
    rels_source = parts[PRESENTATION_RELS_PART]
    rels_root = parse_source_xml(rels_source)
    if _presentation_props_part(rels_root) is None:
        ET.SubElement(
            rels_root,
            _qn(PACKAGE_REL_NS, "Relationship"),
            {
                "Id": _next_relationship_id(rels_source.decode("utf-8")),
                "Type": PRESENTATION_PROPS_REL_TYPE,
                "Target": "presProps.xml",
            },
        )
        parts[PRESENTATION_RELS_PART] = serialize_source_xml(
            rels_root,
            rels_source,
        )

    content_source = parts[CONTENT_TYPES_PART]
    content_root = parse_source_xml(content_source)
    part_name = "/" + props_part.lstrip("/")
    if not any(
        override.get("PartName") == part_name
        and override.get("ContentType") == PRESENTATION_PROPS_CONTENT_TYPE
        for override in content_root
    ):
        ET.SubElement(
            content_root,
            _qn(CONTENT_TYPES_NS, "Override"),
            {
                "PartName": part_name,
                "ContentType": PRESENTATION_PROPS_CONTENT_TYPE,
            },
        )
        parts[CONTENT_TYPES_PART] = serialize_source_xml(
            content_root,
            content_source,
        )


def set_package_use_timings(
    parts: MutableMapping[str, bytes],
    *,
    enabled: bool = True,
) -> None:
    """Set presentation-wide timing playback in ppt/presProps.xml."""
    rels_root = parse_source_xml(parts[PRESENTATION_RELS_PART])
    existing_props_part = _presentation_props_part(rels_root)
    props_part = existing_props_part or PRESENTATION_PROPS_PART
    if props_part in parts:
        source = parts[props_part]
        root = parse_source_xml(source)
    else:
        if existing_props_part is not None:
            raise ValueError(
                f"presentation properties part is missing: {props_part}"
            )
        source = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:presentationPr xmlns:p="{PML_NS}"/>'
        ).encode("utf-8")
        root = parse_source_xml(source)

    show_properties = root.find(_qn(PML_NS, "showPr"))
    if show_properties is None:
        show_properties = ET.Element(_qn(PML_NS, "showPr"))
        _insert_show_properties(root, show_properties)
    show_properties.set("useTimings", "1" if enabled else "0")
    parts[props_part] = serialize_source_xml(root, source)
    _ensure_presentation_props_references(parts, props_part=props_part)


def set_directory_use_timings(
    extract_dir: Path,
    *,
    enabled: bool = True,
) -> None:
    """Set presentation timing playback in an extracted PPTX directory."""
    part_names = {
        PRESENTATION_RELS_PART,
        CONTENT_TYPES_PART,
    }
    rels_source = (extract_dir / PRESENTATION_RELS_PART).read_bytes()
    rels_root = parse_source_xml(rels_source)
    props_part = _presentation_props_part(rels_root) or PRESENTATION_PROPS_PART
    if (extract_dir / props_part).is_file():
        part_names.add(props_part)
    parts = {
        name: (extract_dir / name).read_bytes()
        for name in part_names
    }
    set_package_use_timings(parts, enabled=enabled)
    for name, payload in parts.items():
        path = extract_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
