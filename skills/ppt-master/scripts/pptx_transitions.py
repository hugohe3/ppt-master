#!/usr/bin/env python3
"""
PPT Master - PPTX Transition Core

Provide one strict PowerPoint-native transition registry, a compatibility input
map, and shared OOXML read/write helpers for generated and source-preserving
round-trip PPTX files.
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping
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
RELATIONSHIPS_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)

PRESENTATION_PROPS_PART = "ppt/presProps.xml"
PRESENTATION_RELS_PART = "ppt/_rels/presentation.xml.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"
PRESENTATION_PROPS_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps"
)
PRESENTATION_PROPS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"
)
AUDIO_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
)
WAV_CONTENT_TYPES = frozenset({"audio/wav", "audio/x-wav"})

DEFAULT_TRANSITION = "fade"
DEFAULT_TRANSITION_DURATION = 0.4
MAX_OOXML_MILLISECONDS = 4_294_967_295
# OOXML stores millisecond values and identifiers (shape ids, time-node ids,
# preset codes) as xsd:unsignedInt, so both ceilings share one value.
MAX_OOXML_UNSIGNED_INT = MAX_OOXML_MILLISECONDS


_TRANSITION_SPECS: dict[str, dict[str, Any]] = {
    # PowerPoint-native public ordering is assembled by gallery category below.
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
    "dissolve": {
        "name": "Dissolve",
        "element": "dissolve",
        "attrs": {},
    },
    "random_bars": {
        "name": "Random Bars",
        "element": "randomBar",
        "attrs": {"dir": "vert"},
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

TRANSITION_CATEGORIES = ("subtle", "exciting", "dynamic_content")
_TRANSITION_KEYS_BY_CATEGORY = {
    "subtle": (
        "morph",
        "fade",
        "push",
        "wipe",
        "split",
        "reveal",
        "cut",
        "random_bars",
        "shape",
        "uncover",
        "cover",
        "flash",
    ),
    "exciting": (
        "fall_over",
        "drape",
        "curtains",
        "wind",
        "prestige",
        "fracture",
        "crush",
        "peel_off",
        "page_curl",
        "airplane",
        "origami",
        "dissolve",
        "checkerboard",
        "blinds",
        "clock",
        "ripple",
        "honeycomb",
        "glitter",
        "vortex",
        "shred",
        "switch",
        "flip",
        "gallery",
        "cube",
        "doors",
        "box",
        "comb",
        "zoom",
        "random",
    ),
    "dynamic_content": (
        "pan",
        "ferris_wheel",
        "conveyor",
        "rotate",
        "window",
        "orbit",
        "fly_through",
    ),
}

TRANSITION_EFFECT_OPTION_FIELDS = (
    "direction",
    "orientation",
    "style",
    "shape",
    "pattern",
    "origin",
    "pages",
    "morph_by",
    "through_black",
    "bounce",
)


def _enum_option(
    default: str,
    values: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "type": "enum",
        "default": default,
        "values": dict(values),
    }


def _attribute_enum(
    default: str,
    attribute: str,
    values: Mapping[str, str | None],
) -> dict[str, Any]:
    overrides: dict[str, dict[str, Any]] = {}
    for name, value in values.items():
        if value is None:
            overrides[name] = {"remove_attrs": (attribute,)}
        else:
            overrides[name] = {"attrs": {attribute: value}}
    return _enum_option(default, overrides)


def _boolean_option(
    default: bool,
    attribute: str,
) -> dict[str, Any]:
    return {
        "type": "boolean",
        "default": default,
        "values": {
            False: {"remove_attrs": (attribute,)},
            True: {"attrs": {attribute: "1"}},
        },
    }


_CARDINAL_DIRECTIONS = {
    "left": None,
    "right": "r",
    "up": "u",
    "down": "d",
}
_CORNER_DIRECTIONS = {
    **_CARDINAL_DIRECTIONS,
    "up_left": "lu",
    "up_right": "ru",
    "down_left": "ld",
    "down_right": "rd",
}
_TRANSITION_EFFECT_OPTIONS: dict[str, dict[str, dict[str, Any]]] = {
    "morph": {
        "morph_by": _attribute_enum(
            "object",
            "option",
            {
                "object": "byObject",
                "word": "byWord",
                "character": "byChar",
            },
        ),
    },
    "fade": {
        "style": _attribute_enum(
            "smoothly",
            "thruBlk",
            {"smoothly": None, "through_black": "1"},
        ),
    },
    "push": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {**_CARDINAL_DIRECTIONS, "left": "l"},
        ),
    },
    "wipe": {
        "direction": _attribute_enum("right", "dir", _CARDINAL_DIRECTIONS),
    },
    "split": {
        "orientation": _attribute_enum(
            "horizontal",
            "orient",
            {"horizontal": None, "vertical": "vert"},
        ),
        "direction": _attribute_enum(
            "out",
            "dir",
            {"in": "in", "out": None},
        ),
    },
    "reveal": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {"left": None, "right": "r"},
        ),
        "through_black": _boolean_option(False, "thruBlk"),
    },
    "cut": {
        "through_black": {
            "type": "boolean",
            "default": False,
            "values": {
                False: {"remove_attrs": ("thruBlk",)},
                True: {"attrs": {"thruBlk": "1"}},
            },
        },
    },
    "random_bars": {
        "orientation": _attribute_enum(
            "vertical",
            "dir",
            {"horizontal": None, "vertical": "vert"},
        ),
    },
    "shape": {
        "shape": _enum_option(
            "circle",
            {
                "circle": {"element": "circle"},
                "diamond": {"element": "diamond"},
                "plus": {"element": "plus"},
            },
        ),
    },
    "uncover": {
        "direction": _attribute_enum("right", "dir", _CORNER_DIRECTIONS),
    },
    "cover": {
        "direction": _attribute_enum("right", "dir", _CORNER_DIRECTIONS),
    },
    "fall_over": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": None, "right": "1"},
        ),
    },
    "drape": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": None, "right": "1"},
        ),
    },
    "wind": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": "1", "right": None},
        ),
    },
    "peel_off": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": None, "right": "1"},
        ),
    },
    "page_curl": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": None, "right": "1"},
        ),
        "pages": _attribute_enum(
            "single",
            "prst",
            {"single": "pageCurlSingle", "double": "pageCurlDouble"},
        ),
    },
    "airplane": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": "1", "right": None},
        ),
    },
    "origami": {
        "direction": _attribute_enum(
            "right",
            "invX",
            {"left": "1", "right": None},
        ),
    },
    "checkerboard": {
        "direction": _attribute_enum(
            "across",
            "dir",
            {"across": None, "down": "vert"},
        ),
    },
    "blinds": {
        "orientation": _attribute_enum(
            "vertical",
            "dir",
            {"horizontal": None, "vertical": "vert"},
        ),
    },
    "clock": {
        "style": _enum_option(
            "clockwise",
            {
                "clockwise": {
                    "element": "wheel",
                    "attrs": {"spokes": "1"},
                },
                "counterclockwise": {
                    "prefix": "p14",
                    "element": "wheelReverse",
                    "attrs": {"spokes": "1"},
                    "fallback": "fade",
                },
                "wedge": {
                    "element": "wedge",
                    "remove_attrs": ("spokes",),
                },
            },
        ),
    },
    "ripple": {
        "origin": _attribute_enum(
            "center",
            "dir",
            {
                "center": None,
                "up_left": "lu",
                "up_right": "ru",
                "down_left": "ld",
                "down_right": "rd",
            },
        ),
    },
    "glitter": {
        "shape": _attribute_enum(
            "diamond",
            "pattern",
            {"diamond": None, "hexagon": "hexagon"},
        ),
        "direction": _attribute_enum(
            "right",
            "dir",
            {
                "left": "r",
                "right": None,
                "up": "d",
                "down": "u",
            },
        ),
    },
    "vortex": {
        "direction": _attribute_enum("right", "dir", _CARDINAL_DIRECTIONS),
    },
    "shred": {
        "pattern": _attribute_enum(
            "strips",
            "pattern",
            {"strips": None, "rectangle": "rectangle"},
        ),
        "direction": _attribute_enum(
            "out",
            "dir",
            {"in": None, "out": "out"},
        ),
    },
    "switch": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {"left": "l", "right": "r"},
        ),
    },
    "flip": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {"left": "l", "right": "r"},
        ),
    },
    "gallery": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {"left": "l", "right": "r"},
        ),
    },
    "cube": {
        "direction": _attribute_enum("right", "dir", _CARDINAL_DIRECTIONS),
    },
    "doors": {
        "orientation": _attribute_enum(
            "vertical",
            "dir",
            {"horizontal": None, "vertical": "vert"},
        ),
    },
    "box": {
        "direction": _attribute_enum(
            "out",
            "dir",
            {"in": "in", "out": None},
        ),
    },
    "comb": {
        "orientation": _attribute_enum(
            "horizontal",
            "dir",
            {"horizontal": None, "vertical": "vert"},
        ),
    },
    "zoom": {
        "direction": _attribute_enum(
            "in",
            "dir",
            {"in": "in", "out": None},
        ),
    },
    "pan": {
        "direction": _attribute_enum("right", "dir", _CARDINAL_DIRECTIONS),
    },
    "ferris_wheel": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {"left": "l", "right": "r"},
        ),
    },
    "conveyor": {
        "direction": _attribute_enum(
            "right",
            "dir",
            {"left": "l", "right": "r"},
        ),
    },
    "rotate": {
        "direction": _attribute_enum("right", "dir", _CARDINAL_DIRECTIONS),
    },
    "window": {
        "orientation": _attribute_enum(
            "horizontal",
            "dir",
            {"horizontal": None, "vertical": "vert"},
        ),
    },
    "orbit": {
        "direction": _attribute_enum("right", "dir", _CARDINAL_DIRECTIONS),
    },
    "fly_through": {
        "direction": _attribute_enum(
            "in",
            "dir",
            {"in": None, "out": "out"},
        ),
        "bounce": _boolean_option(False, "hasBounce"),
    },
}

NATIVE_TRANSITIONS: dict[str, dict[str, Any]] = {}
for _category in TRANSITION_CATEGORIES:
    for _key in _TRANSITION_KEYS_BY_CATEGORY[_category]:
        if _key in NATIVE_TRANSITIONS:
            raise RuntimeError(f"duplicate native transition key: {_key}")
        _spec = dict(_TRANSITION_SPECS[_key])
        _spec["category"] = _category
        _spec["effectOptions"] = _TRANSITION_EFFECT_OPTIONS.get(_key, {})
        NATIVE_TRANSITIONS[_key] = _spec
if set(NATIVE_TRANSITIONS) != set(_TRANSITION_SPECS):
    raise RuntimeError("native transition gallery categories are incomplete")
if len(NATIVE_TRANSITIONS) != 48:
    raise RuntimeError(
        f"native transition gallery count changed: {len(NATIVE_TRANSITIONS)}"
    )
for _key, _spec in NATIVE_TRANSITIONS.items():
    _options = _spec["effectOptions"]
    _unknown_options = set(_options) - set(TRANSITION_EFFECT_OPTION_FIELDS)
    if _unknown_options:
        raise RuntimeError(
            f"native transition {_key!r} has unknown effect option(s): "
            + ", ".join(sorted(_unknown_options))
        )
    for _option_name, _option_spec in _options.items():
        if _option_spec.get("type") not in {"enum", "boolean"}:
            raise RuntimeError(
                f"native transition {_key!r} option {_option_name!r} "
                "must be enum or boolean"
            )
        _values = _option_spec.get("values")
        if not isinstance(_values, dict) or not _values:
            raise RuntimeError(
                f"native transition {_key!r} option {_option_name!r} "
                "must define values"
            )
        if _option_spec.get("default") not in _values:
            raise RuntimeError(
                f"native transition {_key!r} option {_option_name!r} "
                "has an unknown default"
            )

NATIVE_TRANSITION_KEYS = tuple(NATIVE_TRANSITIONS)
# Retained as a module-level compatibility name for existing imports. New code
# should use ``NATIVE_TRANSITIONS`` to distinguish the native registry from
# accepted legacy input names.
CANONICAL_TRANSITIONS = NATIVE_TRANSITIONS

TRANSITION_ALIASES: dict[str, str] = {
    "strips": "wipe",
    "circle": "shape",
    "diamond": "shape",
    "newsflash": "flash",
    "plus": "shape",
    "pull": "uncover",
    "wedge": "clock",
    "wheel": "clock",
}
LEGACY_TRANSITION_KEYS = tuple(TRANSITION_ALIASES)
TRANSITION_ALIAS_OPTIONS: dict[str, dict[str, object]] = {
    "strips": {"direction": "right"},
    "circle": {"shape": "circle"},
    "diamond": {"shape": "diamond"},
    "plus": {"shape": "plus"},
    "wedge": {"style": "wedge"},
    "wheel": {"style": "clockwise"},
}
TRANSITIONS: dict[str, dict[str, Any]] = dict(NATIVE_TRANSITIONS)
for _alias, _canonical_key in TRANSITION_ALIASES.items():
    TRANSITIONS[_alias] = NATIVE_TRANSITIONS[_canonical_key]

TRANSITION_NAMESPACES = {
    "p": PML_NS,
    "p14": P14_NS,
    "p15": P15_NS,
    "p159": P159_NS,
}

for _prefix, _uri in (
    *TRANSITION_NAMESPACES.items(),
    ("mc", MC_NS),
    ("r", RELATIONSHIPS_NS),
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
    effect_options: Mapping[str, object] | None = None


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
    effect_attributes: Mapping[str, str] = field(default_factory=dict)
    canonical_effect: str | None = None
    effect_options: Mapping[str, object] = field(default_factory=dict)
    sound_relationship_id: str | None = None
    sound_name: str | None = None
    fallback_sound_relationship_id: str | None = None
    fallback_sound_name: str | None = None


@dataclass(frozen=True)
class MorphPairExpectation:
    """One forced-Morph name expected on two adjacent generated slides."""

    source_slide_number: int
    destination_slide_number: int
    key: str

    @property
    def shape_name(self) -> str:
        return f"!!{self.key}"


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
    """Return one canonical PowerPoint transition or explicit no-effect."""
    if effect is None or effect == "none":
        if allow_none:
            return None
        raise ValueError("transition effect is required")
    if not isinstance(effect, str):
        raise ValueError(f"transition effect must be a string: {effect!r}")
    if effect in TRANSITION_ALIASES:
        return TRANSITION_ALIASES[effect]
    if effect in NATIVE_TRANSITIONS:
        return effect
    valid = ", ".join((*NATIVE_TRANSITION_KEYS, *LEGACY_TRANSITION_KEYS))
    raise ValueError(
        f"unknown transition effect {effect!r}; valid effects: {valid}, none"
    )


def normalize_transition_effect_options(
    effect: str,
    options: object = None,
) -> dict[str, object]:
    """Validate PowerPoint Effect Options for one native transition."""
    if effect not in NATIVE_TRANSITIONS:
        if options in (None, {}):
            return {}
        raise ValueError(
            "transition effect_options require one explicit native effect; "
            f"found {effect!r}"
        )
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise ValueError(
            f"transition effect_options must be an object: {options!r}"
        )

    option_specs = NATIVE_TRANSITIONS[effect]["effectOptions"]
    unknown = set(options) - set(option_specs)
    if unknown:
        unsupported = ", ".join(sorted(unknown))
        supported = ", ".join(option_specs) or "(none)"
        raise ValueError(
            f"transition effect {effect!r} does not support effect option(s): "
            f"{unsupported}; supported options: {supported}"
        )

    normalized: dict[str, object] = {}
    for name, value in options.items():
        spec = option_specs[name]
        field = f"transition effect_options.{name}"
        if spec["type"] == "enum":
            if not isinstance(value, str) or value not in spec["values"]:
                valid = ", ".join(spec["values"])
                raise ValueError(
                    f"{field} for {effect!r} must be one of {valid}: {value!r}"
                )
            normalized[name] = value
        elif spec["type"] == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"{field} must be a boolean: {value!r}")
            normalized[name] = value
        else:
            raise AssertionError(
                f"unhandled transition option type: {spec['type']!r}"
            )
    return normalized


def normalize_transition_effect_request(
    effect: object,
    options: object = None,
    *,
    allow_none: bool = True,
) -> tuple[str | None, dict[str, object]]:
    """Normalize one native effect plus options and legacy semantic aliases."""
    raw_effect = effect
    canonical = normalize_transition_effect(effect, allow_none=allow_none)
    alias_options = (
        TRANSITION_ALIAS_OPTIONS.get(raw_effect, {})
        if isinstance(raw_effect, str)
        else {}
    )
    explicit_options: Mapping[str, object]
    if options is None:
        explicit_options = {}
    elif isinstance(options, Mapping):
        explicit_options = options
    else:
        raise ValueError(
            f"transition effect_options must be an object: {options!r}"
        )
    for name, alias_value in alias_options.items():
        if name in explicit_options and explicit_options[name] != alias_value:
            raise ValueError(
                f"legacy transition effect {raw_effect!r} implies "
                f"effect_options.{name}={alias_value!r}, which conflicts with "
                f"{explicit_options[name]!r}"
            )
    merged = {**alias_options, **explicit_options}
    if canonical is None:
        if merged:
            raise ValueError(
                "transition effect_options require one explicit native effect; "
                "found 'none'"
            )
        return None, {}
    return canonical, normalize_transition_effect_options(canonical, merged)


def describe_transition_effect(effect: object) -> dict[str, Any]:
    """Return the author-facing parameter contract for one transition."""
    canonical, implied_options = normalize_transition_effect_request(
        effect,
        allow_none=False,
    )
    option_contract: dict[str, Any] = {}
    for name, raw_spec in NATIVE_TRANSITIONS[canonical]["effectOptions"].items():
        option_contract[name] = {
            "type": raw_spec["type"],
            "default": raw_spec["default"],
            "values": list(raw_spec["values"]),
        }
    return {
        "input": effect,
        "effect": canonical,
        "name": NATIVE_TRANSITIONS[canonical]["name"],
        "category": NATIVE_TRANSITIONS[canonical]["category"],
        "compatibility_alias": (
            effect
            if isinstance(effect, str) and effect in TRANSITION_ALIASES
            else None
        ),
        "implied_effect_options": implied_options,
        "effect_options": option_contract,
        "timing": {
            "duration": "positive seconds",
            "auto_advance": "non-negative seconds",
        },
        "sound": "project-relative .wav path or null in animations.json",
    }


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


def _effect_spec(
    effect: str,
    effect_options: object = None,
) -> tuple[str, str, str, dict[str, Any], str | None]:
    info = NATIVE_TRANSITIONS[effect]
    prefix = str(info.get("prefix", "p"))
    namespace = TRANSITION_NAMESPACES[prefix]
    element = str(info["element"])
    attrs = dict(info.get("attrs", {}))
    fallback = info.get("fallback")
    options = {
        name: option_spec["default"]
        for name, option_spec in info["effectOptions"].items()
    }
    options.update(
        normalize_transition_effect_options(effect, effect_options)
    )
    option_specs = info["effectOptions"]
    for name, value in options.items():
        override = option_specs[name]["values"][value]
        if "prefix" in override:
            prefix = str(override["prefix"])
            namespace = TRANSITION_NAMESPACES[prefix]
        if "element" in override:
            element = str(override["element"])
        for attribute in override.get("remove_attrs", ()):
            attrs.pop(str(attribute), None)
        attrs.update(
            {
                str(attribute): str(attribute_value)
                for attribute, attribute_value in override.get("attrs", {}).items()
            }
        )
        if "fallback" in override:
            fallback = override["fallback"]
    return prefix, namespace, element, attrs, str(fallback) if fallback else None


def _effect_xml(
    effect: str,
    effect_options: object = None,
) -> tuple[str, str, str]:
    prefix, _namespace, element, effect_attrs, _fallback = _effect_spec(
        effect,
        effect_options,
    )
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


def _normalize_transition_sound(
    sound: Mapping[str, object] | None,
) -> dict[str, str] | None:
    """Validate one packaged transition-sound relationship descriptor."""
    if sound is None:
        return None
    if not isinstance(sound, Mapping):
        raise ValueError("transition sound must be a relationship descriptor")
    unknown = set(sound) - {"relationship_id", "name"}
    if unknown:
        raise ValueError(
            "transition sound has unknown field(s): "
            + ", ".join(sorted(str(field) for field in unknown))
        )
    relationship_id = sound.get("relationship_id")
    name = sound.get("name")
    if not isinstance(relationship_id, str) or not relationship_id.strip():
        raise ValueError(
            "transition sound relationship_id must be a non-empty string"
        )
    if not isinstance(name, str) or not name.strip():
        raise ValueError("transition sound name must be a non-empty string")
    return {
        "relationship_id": relationship_id,
        "name": name,
    }


def _transition_sound_xml(
    sound: Mapping[str, str] | None,
    *,
    indent: str,
) -> str:
    """Return the optional p:sndAc payload at one indentation level."""
    if sound is None:
        return ""
    relationship_id = quoteattr(sound["relationship_id"])
    name = quoteattr(sound["name"])
    return (
        f"{indent}<p:sndAc>\n"
        f"{indent}  <p:stSnd>\n"
        f"{indent}    <p:snd r:embed={relationship_id} name={name}/>\n"
        f"{indent}  </p:stSnd>\n"
        f"{indent}</p:sndAc>\n"
    )


def create_transition_xml(
    effect: str | None = DEFAULT_TRANSITION,
    duration: float = 0.5,
    advance_after: float | None = None,
    advance_on_click: bool | None = None,
    effect_options: Mapping[str, object] | None = None,
    sound: Mapping[str, object] | None = None,
) -> str:
    """Build a direct or MCE-backed p:transition XML fragment."""
    normalized_effect, normalized_options = normalize_transition_effect_request(
        effect,
        effect_options,
    )
    normalized_sound = _normalize_transition_sound(sound)
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
        and normalized_sound is None
    ):
        return ""

    attr_text = _transition_attributes(
        duration_ms=duration_ms,
        advance_after_ms=advance_ms,
        advance_on_click=advance_on_click,
        declare_p14=normalized_effect is not None,
    )
    if normalized_effect is None:
        if normalized_sound is None:
            return f"  <p:transition{attr_text}/>"
        return (
            f"  <p:transition{attr_text}>\n"
            + _transition_sound_xml(normalized_sound, indent="    ")
            + "  </p:transition>"
        )

    prefix, element_name, effect_attrs = _effect_xml(
        normalized_effect,
        normalized_options,
    )
    if prefix != "p":
        _effect_prefix, _namespace, _element, _attrs, fallback = _effect_spec(
            normalized_effect,
            normalized_options,
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
        choice_sound_xml = _transition_sound_xml(
            normalized_sound,
            indent="        ",
        )
        fallback_sound_xml = _transition_sound_xml(
            normalized_sound,
            indent="        ",
        )
        return (
            f'  <mc:AlternateContent xmlns:mc="{MC_NS}">\n'
            f'    <mc:Choice xmlns:{prefix}="{TRANSITION_NAMESPACES[prefix]}" '
            f'Requires="{prefix}">\n'
            f"      <p:transition{attr_text}>\n"
            f"        <{prefix}:{element_name}{effect_attrs}/>\n"
            f"{choice_sound_xml}"
            "      </p:transition>\n"
            "    </mc:Choice>\n"
            "    <mc:Fallback>\n"
            f"      <p:transition{fallback_attr_text}>\n"
            f"        <{fallback_prefix}:{fallback_name}{fallback_attrs}/>\n"
            f"{fallback_sound_xml}"
            "      </p:transition>\n"
            "    </mc:Fallback>\n"
            "  </mc:AlternateContent>"
        )
    sound_xml = _transition_sound_xml(normalized_sound, indent="    ")
    return (
        f"  <p:transition{attr_text}>\n"
        f"    <{prefix}:{element_name}{effect_attrs}/>\n"
        f"{sound_xml}"
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
    effect_options: Mapping[str, object] | None = None,
) -> Any | None:
    normalized_effect, normalized_options = normalize_transition_effect_request(
        effect,
        effect_options,
    )
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
        options: Mapping[str, object] | None = None,
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
                _effect_spec(effect_name, options)
            )
            child = _new_element(context, _qn(namespace, element_name))
            for key, value in effect_attrs.items():
                child.set(key, str(value))
            transition.append(child)
        return transition

    if normalized_effect is None:
        return build_transition(None, include_duration=False)

    prefix, _namespace, _element, _attrs, fallback = _effect_spec(
        normalized_effect,
        normalized_options,
    )
    if prefix == "p":
        return build_transition(
            normalized_effect,
            include_duration=True,
            options=normalized_options,
        )

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
    choice.append(
        build_transition(
            normalized_effect,
            include_duration=True,
            options=normalized_options,
        )
    )
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


def _effect_identity(
    transition: Any | None,
) -> tuple[str | None, str | None, dict[str, str]]:
    if transition is None:
        return None, None, {}
    for child in list(transition):
        if child.tag == _qn(PML_NS, "sndAc"):
            continue
        return (
            _local_name(child.tag),
            _namespace_name(child.tag),
            {str(name): str(value) for name, value in child.attrib.items()},
        )
    return None, None, {}


def _sound_identity(
    transition: Any | None,
) -> tuple[str | None, str | None]:
    """Return one embedded transition sound relationship and display name."""
    if transition is None:
        return None, None
    sound_action = next(
        (
            child
            for child in list(transition)
            if child.tag == _qn(PML_NS, "sndAc")
        ),
        None,
    )
    if sound_action is None:
        return None, None
    start_sound = next(
        (
            child
            for child in list(sound_action)
            if child.tag == _qn(PML_NS, "stSnd")
        ),
        None,
    )
    if start_sound is None:
        return None, None
    sound = next(
        (
            child
            for child in list(start_sound)
            if child.tag == _qn(PML_NS, "snd")
        ),
        None,
    )
    if sound is None:
        return None, None
    return sound.get(_qn(RELATIONSHIPS_NS, "embed")), sound.get("name")


def _effective_transition_options(
    effect: str,
    options: Mapping[str, object] | None = None,
) -> dict[str, object]:
    effective = {
        name: spec["default"]
        for name, spec in NATIVE_TRANSITIONS[effect]["effectOptions"].items()
    }
    effective.update(normalize_transition_effect_options(effect, options))
    return effective


def _transition_option_combinations(effect: str) -> list[dict[str, object]]:
    combinations: list[dict[str, object]] = [{}]
    for name, spec in NATIVE_TRANSITIONS[effect]["effectOptions"].items():
        combinations = [
            {**combination, name: value}
            for combination in combinations
            for value in spec["values"]
        ]
    return combinations


def _identify_native_transition(
    element: str | None,
    namespace: str | None,
    attributes: Mapping[str, str],
) -> tuple[str | None, dict[str, object]]:
    if element is None or namespace is None:
        return None, {}
    for effect in NATIVE_TRANSITION_KEYS:
        for options in _transition_option_combinations(effect):
            _prefix, expected_namespace, expected_element, expected_attrs, _fallback = (
                _effect_spec(effect, options)
            )
            if (
                namespace == expected_namespace
                and element == expected_element
                and dict(attributes) == {
                    str(name): str(value)
                    for name, value in expected_attrs.items()
                }
            ):
                return effect, options
    return None, {}


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
    effect, effect_namespace, effect_attributes = _effect_identity(primary)
    fallback_effect, fallback_namespace, _fallback_attributes = _effect_identity(
        fallback
    )
    sound_relationship_id, sound_name = _sound_identity(primary)
    fallback_sound_relationship_id, fallback_sound_name = _sound_identity(
        fallback
    )
    canonical_effect, effect_options = _identify_native_transition(
        effect,
        effect_namespace,
        effect_attributes,
    )
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
        effect_attributes=effect_attributes,
        canonical_effect=canonical_effect,
        effect_options=effect_options,
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
        sound_relationship_id=sound_relationship_id,
        sound_name=sound_name,
        fallback_sound_relationship_id=fallback_sound_relationship_id,
        fallback_sound_name=fallback_sound_name,
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
    if (
        enter.policy != "replace"
        and enter.effect_options not in (None, {})
    ):
        raise ValueError(
            "transition effect_options require enter policy 'replace'"
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
            effect_options=None,
        )
        if transition is not None:
            _insert_transition_carrier(slide_root, transition)
        return advance_after is not None

    effect, effect_options = (
        normalize_transition_effect_request(
            enter.effect,
            enter.effect_options,
            allow_none=False,
        )
        if enter.policy == "replace"
        else (None, {})
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
        effect_options=effect_options,
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
        tuple(sorted(summary.effect_attributes.items())),
        summary.canonical_effect,
        tuple(sorted(summary.effect_options.items())),
        summary.fallback_effect,
        summary.fallback_effect_namespace,
        summary.duration_ms,
        summary.speed,
        summary.sound_relationship_id,
        summary.sound_name,
        summary.fallback_sound_relationship_id,
        summary.fallback_sound_name,
    )


def _expected_visual_identity(
    effect: str,
    effect_options: Mapping[str, object] | None = None,
) -> tuple[str, str, str, str | None, str | None, dict[str, Any]]:
    prefix, namespace, element, attrs, fallback = _effect_spec(
        effect,
        effect_options,
    )
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
        effect, effect_options = normalize_transition_effect_request(
            enter.effect,
            enter.effect_options,
            allow_none=False,
        )
        expected_effect_options = _effective_transition_options(
            effect,
            effect_options,
        )
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
        ) = _expected_visual_identity(effect, effect_options)
        if (
            after.carrier != expected_carrier
            or after.logical_count != 1
            or after.effect != expected_effect
            or after.effect_namespace != expected_namespace
            or after.canonical_effect != effect
            or dict(after.effect_options) != expected_effect_options
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
        if (
            after.sound_relationship_id is not None
            or after.fallback_sound_relationship_id is not None
        ):
            errors.append("none policy retained a transition sound")

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
    effect_options: Mapping[str, object] | None = None,
    sound: Mapping[str, object] | None = None,
) -> TransitionSummary:
    """Validate a generated transition against its resolved settings."""
    data = slide_xml.encode("utf-8") if isinstance(slide_xml, str) else slide_xml
    root = LET.fromstring(data) if LET is not None else parse_source_xml(data)
    errors = validate_slide_transition_structure(root) + validate_mce_prefixes(data)
    summary = read_slide_transition(root)
    normalized_effect, normalized_options = normalize_transition_effect_request(
        effect,
        effect_options,
    )
    normalized_sound = _normalize_transition_sound(sound)
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
        or normalized_sound is not None
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
        expected_sound_relationship_id = (
            normalized_sound["relationship_id"]
            if normalized_sound is not None
            else None
        )
        expected_sound_name = (
            normalized_sound["name"]
            if normalized_sound is not None
            else None
        )
        expected_fallback_sound_relationship_id = None
        expected_fallback_sound_name = None
        if normalized_effect is not None:
            (
                expected_carrier,
                expected_effect,
                expected_namespace,
                expected_fallback,
                expected_fallback_namespace,
                expected_attrs,
            ) = _expected_visual_identity(
                normalized_effect,
                normalized_options,
            )
            expected_effect_options = _effective_transition_options(
                normalized_effect,
                normalized_options,
            )
            if expected_carrier == "alternate-content":
                expected_fallback_sound_relationship_id = (
                    expected_sound_relationship_id
                )
                expected_fallback_sound_name = expected_sound_name
        else:
            expected_effect_options = {}
        if (
            summary.carrier != expected_carrier
            or summary.logical_count != 1
            or summary.effect != expected_effect
            or summary.effect_namespace != expected_namespace
            or summary.canonical_effect != normalized_effect
            or dict(summary.effect_options) != expected_effect_options
            or summary.fallback_effect != expected_fallback
            or summary.fallback_effect_namespace != expected_fallback_namespace
            or summary.duration_ms != expected_duration_ms
            or summary.advance_on_click != expected_click
            or summary.advance_after_ms != expected_after_ms
            or summary.sound_relationship_id != expected_sound_relationship_id
            or summary.sound_name != expected_sound_name
            or summary.fallback_sound_relationship_id
            != expected_fallback_sound_relationship_id
            or summary.fallback_sound_name != expected_fallback_sound_name
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
                if len(effect_children) != 1:
                    errors.append(
                        "generated transition must contain exactly one visual "
                        f"effect child; found {len(effect_children)}"
                    )
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


def _slide_relationships_part(slide_part: str) -> str:
    directory = posixpath.dirname(slide_part)
    filename = posixpath.basename(slide_part)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def _resolve_slide_relationship_target(
    slide_part: str,
    target: str,
) -> str | None:
    normalized_target = target.replace("\\", "/")
    if not normalized_target:
        return None
    if normalized_target.startswith("/"):
        resolved = posixpath.normpath(normalized_target.lstrip("/"))
    else:
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(slide_part), normalized_target)
        )
    if resolved == ".." or resolved.startswith("../"):
        return None
    return resolved


def _transition_sound_elements(slide_root: Any) -> list[Any]:
    sounds: list[Any] = []
    for carrier in transition_carriers(slide_root):
        for transition in _transition_elements(carrier):
            for sound_action in list(transition):
                if sound_action.tag != _qn(PML_NS, "sndAc"):
                    continue
                for start_sound in list(sound_action):
                    if start_sound.tag != _qn(PML_NS, "stSnd"):
                        continue
                    sounds.extend(
                        child
                        for child in list(start_sound)
                        if child.tag == _qn(PML_NS, "snd")
                    )
    return sounds


def _package_part_content_type(
    package: zipfile.ZipFile,
    target_part: str,
) -> str | None:
    """Resolve one package part's MIME type from defaults or overrides."""
    content_types_root = ET.fromstring(package.read(CONTENT_TYPES_PART))
    normalized_target = "/" + target_part.lstrip("/")
    for entry in content_types_root:
        if (
            entry.tag == _qn(CONTENT_TYPES_NS, "Override")
            and entry.get("PartName") == normalized_target
        ):
            return entry.get("ContentType")
    extension = Path(target_part).suffix.lstrip(".").lower()
    for entry in content_types_root:
        if (
            entry.tag == _qn(CONTENT_TYPES_NS, "Default")
            and str(entry.get("Extension") or "").lower() == extension
        ):
            return entry.get("ContentType")
    return None


def _validate_transition_sound_package_parts(
    package: zipfile.ZipFile,
    package_names: set[str],
    slide_part: str,
    slide_xml: bytes,
) -> list[str]:
    """Validate transition-sound relationships and embedded WAV targets."""
    errors: list[str] = []
    slide_root = (
        LET.fromstring(slide_xml)
        if LET is not None
        else parse_source_xml(slide_xml)
    )
    sounds = _transition_sound_elements(slide_root)
    if not sounds:
        return errors

    if CONTENT_TYPES_PART not in package_names:
        return ["transition sound is missing [Content_Types].xml"]

    relationships_part = _slide_relationships_part(slide_part)
    if relationships_part not in package_names:
        return [
            f"transition sound is missing slide relationships: "
            f"{relationships_part}"
        ]
    try:
        relationships_root = ET.fromstring(package.read(relationships_part))
    except (KeyError, ET.ParseError) as exc:
        return [f"unable to read {relationships_part}: {exc}"]

    relationships: dict[str, Any] = {}
    duplicate_ids: set[str] = set()
    for relationship in relationships_root:
        relationship_id = str(relationship.get("Id") or "")
        if not relationship_id:
            continue
        if relationship_id in relationships:
            duplicate_ids.add(relationship_id)
        relationships[relationship_id] = relationship
    if duplicate_ids:
        errors.append(
            f"{relationships_part} contains duplicate relationship id(s): "
            + ", ".join(sorted(duplicate_ids))
        )

    for sound in sounds:
        relationship_id = sound.get(_qn(RELATIONSHIPS_NS, "embed"))
        if not relationship_id:
            errors.append("p:snd must declare a non-empty r:embed")
            continue
        relationship = relationships.get(relationship_id)
        if relationship is None:
            errors.append(
                f"p:snd references missing slide relationship: "
                f"{relationship_id}"
            )
            continue
        if relationship.get("Type") != AUDIO_REL_TYPE:
            errors.append(
                f"transition sound relationship {relationship_id} must use "
                "the OOXML audio relationship type"
            )
        if relationship.get("TargetMode") == "External":
            errors.append(
                f"transition sound relationship {relationship_id} must be internal"
            )
            continue
        target = str(relationship.get("Target") or "")
        target_part = _resolve_slide_relationship_target(slide_part, target)
        if target_part is None:
            errors.append(
                f"transition sound relationship {relationship_id} has an "
                f"invalid target: {target!r}"
            )
            continue
        if Path(target_part).suffix.lower() != ".wav":
            errors.append(
                f"transition sound relationship {relationship_id} must target "
                f"a .wav part: {target_part}"
            )
        if target_part not in package_names:
            errors.append(
                f"transition sound relationship {relationship_id} target is "
                f"missing: {target_part}"
            )
            continue
        content_type = _package_part_content_type(package, target_part)
        if str(content_type or "").lower() not in WAV_CONTENT_TYPES:
            errors.append(
                f"transition sound target {target_part} must declare a WAV "
                f"content type; found {content_type!r}"
            )
        payload = package.read(target_part)
        if not (
            len(payload) >= 12
            and payload[:4] in {b"RIFF", b"RF64"}
            and payload[8:12] == b"WAVE"
        ):
            errors.append(
                f"transition sound target {target_part} is not RIFF/RF64 WAVE"
            )

    return errors


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

            package_names = set(names)
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
                try:
                    sound_errors = _validate_transition_sound_package_parts(
                        package,
                        package_names,
                        slide_name,
                        slide_xml,
                    )
                except Exception as exc:
                    errors.append(
                        f"{slide_name}: transition sound read-back failed: {exc}"
                    )
                else:
                    for problem in sound_errors:
                        errors.append(f"{slide_name}: {problem}")

            if require_use_timings:
                errors.extend(_validate_package_use_timings(package, names))
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        errors.append(f"unable to read PPTX transition package: {exc}")

    if errors:
        raise ValueError("; ".join(errors))
    return summaries


def _top_level_shape_types_by_name(
    slide_xml: bytes,
) -> dict[str, list[str]]:
    """Return top-level Selection Pane names and their OOXML container types."""
    root = LET.fromstring(slide_xml) if LET is not None else parse_source_xml(slide_xml)
    sp_tree = root.find(f".//{{{PML_NS}}}cSld/{{{PML_NS}}}spTree")
    if sp_tree is None:
        raise ValueError("slide has no p:cSld/p:spTree")
    shapes: dict[str, list[str]] = {}
    for child in sp_tree:
        c_nv_pr = next(child.iter(_qn(PML_NS, "cNvPr")), None)
        name = c_nv_pr.get("name") if c_nv_pr is not None else None
        if not name:
            continue
        shapes.setdefault(name, []).append(_local_name(child.tag))
    return shapes


def validate_pptx_morph_pairs(
    pptx_path: Path,
    expectations: Iterable[MorphPairExpectation],
) -> None:
    """Prove that every requested forced-Morph pair survives final packaging."""
    expected_pairs = tuple(expectations)
    if not expected_pairs:
        return

    errors: list[str] = []
    slide_shapes: dict[int, dict[str, list[str]]] = {}
    slide_transitions: dict[int, TransitionSummary] = {}
    involved_slides = {
        slide_number
        for pair in expected_pairs
        for slide_number in (
            pair.source_slide_number,
            pair.destination_slide_number,
        )
    }
    try:
        with zipfile.ZipFile(pptx_path, "r") as package:
            names = set(package.namelist())
            for slide_number in sorted(involved_slides):
                part = f"ppt/slides/slide{slide_number}.xml"
                if part not in names:
                    errors.append(f"{part}: Morph slide part is missing")
                    continue
                slide_xml = package.read(part)
                try:
                    slide_shapes[slide_number] = _top_level_shape_types_by_name(
                        slide_xml
                    )
                    slide_transitions[slide_number] = read_slide_transition_xml(
                        slide_xml
                    )
                except Exception as exc:
                    errors.append(f"{part}: Morph read-back failed: {exc}")
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        errors.append(f"unable to read PPTX Morph package: {exc}")

    for slide_number, names_to_types in slide_shapes.items():
        duplicate_names = sorted(
            name
            for name, types in names_to_types.items()
            if name.startswith("!!") and len(types) != 1
        )
        if duplicate_names:
            errors.append(
                f"ppt/slides/slide{slide_number}.xml: duplicate forced-Morph "
                f"name(s): {', '.join(duplicate_names)}"
            )

    for pair in expected_pairs:
        if pair.destination_slide_number != pair.source_slide_number + 1:
            errors.append(
                f'Morph pair "{pair.key}" must connect adjacent generated slides'
            )
            continue
        source_shapes = slide_shapes.get(pair.source_slide_number)
        destination_shapes = slide_shapes.get(pair.destination_slide_number)
        if source_shapes is None or destination_shapes is None:
            continue

        shape_name = pair.shape_name
        source_types = source_shapes.get(shape_name, [])
        destination_types = destination_shapes.get(shape_name, [])
        if len(source_types) != 1:
            errors.append(
                f'Morph pair "{pair.key}" expected exactly one source object '
                f'named "{shape_name}" on slide {pair.source_slide_number}'
            )
        if len(destination_types) != 1:
            errors.append(
                f'Morph pair "{pair.key}" expected exactly one destination '
                f'object named "{shape_name}" on slide '
                f'{pair.destination_slide_number}'
            )
        if (
            len(source_types) == 1
            and len(destination_types) == 1
            and source_types[0] != destination_types[0]
        ):
            errors.append(
                f'Morph pair "{pair.key}" changes OOXML object type from '
                f'{source_types[0]} to {destination_types[0]}'
            )

        transition = slide_transitions.get(pair.destination_slide_number)
        if (
            transition is not None
            and (
                transition.canonical_effect != "morph"
                or transition.effect_options.get("morph_by") != "object"
            )
        ):
            errors.append(
                f'Morph pair "{pair.key}" destination slide '
                f'{pair.destination_slide_number} does not use Morph by object'
            )

    declared_names_by_edge: dict[tuple[int, int], set[str]] = {}
    for pair in expected_pairs:
        declared_names_by_edge.setdefault(
            (
                pair.source_slide_number,
                pair.destination_slide_number,
            ),
            set(),
        ).add(pair.shape_name)
    for source_slide_number in sorted(slide_shapes):
        destination_slide_number = source_slide_number + 1
        if destination_slide_number not in slide_shapes:
            continue
        transition = slide_transitions.get(destination_slide_number)
        if (
            transition is None
            or transition.canonical_effect != "morph"
        ):
            continue
        source_names = {
            name
            for name in slide_shapes[source_slide_number]
            if name.startswith("!!")
        }
        destination_names = {
            name
            for name in slide_shapes[destination_slide_number]
            if name.startswith("!!")
        }
        declared_names = declared_names_by_edge.get(
            (source_slide_number, destination_slide_number),
            set(),
        )
        unexpected_names = sorted(
            (source_names & destination_names) - declared_names
        )
        if unexpected_names:
            errors.append(
                f"Morph edge {source_slide_number}->{destination_slide_number} "
                "contains undeclared forced name(s): "
                + ", ".join(unexpected_names)
            )

    if errors:
        raise ValueError("; ".join(dict.fromkeys(errors)))


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
        for transition in _transition_elements(carrier):
            sound_actions = [
                child
                for child in list(transition)
                if child.tag == _qn(PML_NS, "sndAc")
            ]
            if len(sound_actions) > 1:
                errors.append(
                    "p:transition must contain at most one p:sndAc; "
                    f"found {len(sound_actions)}"
                )
            if sound_actions:
                start_sounds = [
                    child
                    for child in list(sound_actions[0])
                    if child.tag == _qn(PML_NS, "stSnd")
                ]
                if len(start_sounds) > 1:
                    errors.append(
                        "p:sndAc must contain at most one p:stSnd; "
                        f"found {len(start_sounds)}"
                    )
                if start_sounds:
                    sounds = [
                        child
                        for child in list(start_sounds[0])
                        if child.tag == _qn(PML_NS, "snd")
                    ]
                    if len(sounds) != 1:
                        errors.append(
                            "p:stSnd must contain exactly one p:snd; "
                            f"found {len(sounds)}"
                        )
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
