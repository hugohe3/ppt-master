#!/usr/bin/env python3
"""
PPT Master - PPTX Animation Module

Provides one strict object-animation registry plus OOXML read/write helpers.

Supported transition effects:
    - Complete current PowerPoint gallery: Subtle, Exciting, Dynamic Content
    - Compatibility aliases: strips, circle, diamond, newsflash, plus, pull,
      wedge, wheel
    - none: no visual transition (handled by the shared transition core)

PowerPoint-native object animations:
    - 53 entrance effects (``entrance_*``)
    - 33 emphasis effects (``emphasis_*``)
    - 64 motion paths (``path_*``)
    - 53 exit effects (``exit_*``)

Legacy compatibility inputs (accepted but never selected for new output):
    appear, fade, fly, fly_left, fly_right, fly_top, cut, zoom, wipe,
    wipe_left, wipe_right, wipe_up, wipe_down, split, blinds, checkerboard,
    dissolve, random_bars, peek, wheel, box, circle, diamond, plus, strips,
    wedge, stretch, expand, swivel

The four media commands in MsoAnimEffect are intentionally excluded because
they require audio/video shapes or bookmarks rather than generated SVG groups.

Animation modes used by the builder:
    - single effect name (one of the above) — apply to every element
    - 'auto'   — pick effect from the group's SVG id. Image-like ids
                 (hero / figure- / image / img- / kpi) cycle through a
                 visual pool (``entrance_zoom`` / ``entrance_dissolve`` /
                 ``entrance_circle`` / ``entrance_box`` /
                 ``entrance_diamond`` / ``entrance_wheel``) so multiple
                 images vary across the deck. Other
                 semantic matches map to a single stable effect
                 (chart→``entrance_wipe``,
                 card-/step-/pillar-→``entrance_fly``,
                 title/takeaway→``entrance_fade``).
                 Unmatched ids cycle through a small modern pool
                 (``entrance_fade`` / ``entrance_wipe`` /
                 ``entrance_fly`` / ``entrance_zoom``).
    - 'mixed'  — compatible mode name: first element fades, the rest cycle
                 through a larger canonical PowerPoint entrance pool.
    - 'random' — pick a seeded canonical PowerPoint entrance per element

Generated animation rows are validated against their requested effect, target,
duration, order, and Start mode before a PPTX is published.  Package validation
also checks timing-tree placement, time-node identifiers, and shape references.

See references/animations.md for the public workflow contract.

Dependencies: None (standard-library XML generation and validation)

Usage:
    python3 scripts/pptx_animations.py --demo
    python3 scripts/pptx_animations.py --list
    python3 scripts/pptx_animations.py --describe entrance_fly
"""

import argparse
import copy
import hashlib
import json
import math
import posixpath
import random
import re
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from pptx_transitions import (
    LEGACY_TRANSITION_KEYS,
    MAX_OOXML_MILLISECONDS,
    MAX_OOXML_UNSIGNED_INT,
    NATIVE_TRANSITION_KEYS,
    NATIVE_TRANSITIONS,
    PML_NS,
    TRANSITION_ALIAS_OPTIONS,
    TRANSITION_ALIASES,
    TRANSITION_CATEGORIES,
    create_transition_xml,
    describe_transition_effect,
    validate_seconds,
)

configure_utf8_stdio()


# ============================================================================
# Object animation definitions
# ============================================================================

# Compatibility names normalize to canonical PowerPoint-authored presets.
# ``cut`` has no current object-animation preset, so the compatibility name
# resolves to the standard instantaneous entrance, ``entrance_appear``.
ANIMATION_ALIASES: dict[str, str] = {
    'appear': 'entrance_appear',
    'fade': 'entrance_fade',
    'fly': 'entrance_fly',
    'fly_left': 'entrance_fly',
    'fly_right': 'entrance_fly',
    'fly_top': 'entrance_fly',
    'cut': 'entrance_appear',
    'zoom': 'entrance_zoom',
    'wipe': 'entrance_wipe',
    'wipe_left': 'entrance_wipe',
    'wipe_right': 'entrance_wipe',
    'wipe_up': 'entrance_wipe',
    'wipe_down': 'entrance_wipe',
    'split': 'entrance_split',
    'blinds': 'entrance_blinds',
    'checkerboard': 'entrance_checkerboard',
    'dissolve': 'entrance_dissolve',
    'random_bars': 'entrance_random_bars',
    'peek': 'entrance_peek',
    'wheel': 'entrance_wheel',
    'box': 'entrance_box',
    'circle': 'entrance_circle',
    'diamond': 'entrance_diamond',
    'plus': 'entrance_plus',
    'strips': 'entrance_strips',
    'wedge': 'entrance_wedge',
    'stretch': 'entrance_stretch',
    'expand': 'entrance_expand',
    'swivel': 'entrance_swivel',
}

LEGACY_ANIMATION_KEYS = tuple(ANIMATION_ALIASES)
ANIMATION_CATEGORIES = ('entrance', 'emphasis', 'path', 'exit')
_PRESET_CLASS_BY_CATEGORY = {
    'entrance': 'entr',
    'emphasis': 'emph',
    'path': 'path',
    'exit': 'exit',
}
_DML_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
_REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_PACKAGE_REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
_AUDIO_REL_TYPE = (
    'http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio'
)
_P14_NS = 'http://schemas.microsoft.com/office/powerpoint/2010/main'
_MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
ET.register_namespace('p', PML_NS)
ET.register_namespace('a', _DML_NS)
ET.register_namespace('r', _REL_NS)
ET.register_namespace('p14', _P14_NS)

ANIMATION_EFFECT_OPTION_FIELDS = (
    'direction',
    'amount',
    'color',
    'font_name',
    'relative',
    'size',
)
ANIMATION_TIMING_OPTION_FIELDS = (
    'repeat_count',
    'repeat_duration',
    'auto_reverse',
    'rewind',
    'accelerate',
    'decelerate',
    'bounce_end',
    'restart',
)
ANIMATION_RESTARTS = ('always', 'when-not-active', 'never')
ANIMATION_AFTER_EFFECTS = ('none', 'dim', 'hide', 'hide-on-next-click')
_NON_CONCRETE_FONT_NAMES = frozenset({
    '-apple-system',
    'blinkmacsystemfont',
    'cursive',
    'emoji',
    'fantasy',
    'inherit',
    'initial',
    'math',
    'monospace',
    'revert',
    'revert-layer',
    'sans-serif',
    'serif',
    'system-ui',
    'ui-monospace',
    'ui-rounded',
    'ui-sans-serif',
    'ui-serif',
    'unset',
})

# Legacy directional names retain their historical semantics by desugaring
# into one canonical effect plus the matching PowerPoint EffectParameters
# value. New plans never select these aliases.
ANIMATION_ALIAS_OPTIONS: dict[str, dict[str, object]] = {
    'fly_left': {'direction': 'left'},
    'fly_right': {'direction': 'right'},
    'fly_top': {'direction': 'up'},
    'wipe_left': {'direction': 'left'},
    'wipe_right': {'direction': 'right'},
    'wipe_up': {'direction': 'up'},
    'wipe_down': {'direction': 'down'},
    'wheel': {'amount': 4},
}


def _load_native_animations() -> dict[str, dict[str, Any]]:
    """Load the PowerPoint-authored preset rows shipped with this module."""
    manifest_path = Path(__file__).with_name('pptx_animation_presets.json')
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f'unable to load native animation presets from {manifest_path}: {exc}'
        ) from exc
    if manifest.get('version') != 2:
        raise RuntimeError(
            f'unsupported native animation preset version: {manifest.get("version")!r}'
        )
    raw_effects = manifest.get('effects')
    if not isinstance(raw_effects, list):
        raise RuntimeError('native animation preset manifest field "effects" must be a list')

    native: dict[str, dict[str, Any]] = {}
    category_counts = {category: 0 for category in ANIMATION_CATEGORIES}
    for raw in raw_effects:
        if not isinstance(raw, dict):
            raise RuntimeError('native animation preset entries must be objects')
        key = raw.get('key')
        category = raw.get('category')
        if not isinstance(key, str) or not key:
            raise RuntimeError(f'native animation preset has invalid key: {key!r}')
        if category not in ANIMATION_CATEGORIES:
            raise RuntimeError(
                f'native animation preset {key!r} has invalid category: {category!r}'
            )
        if key in native or key in ANIMATION_ALIASES:
            raise RuntimeError(f'duplicate animation preset key: {key}')
        row_xml = raw.get('row_xml')
        if not isinstance(row_xml, str):
            raise RuntimeError(f'native animation preset {key!r} is missing row_xml')
        try:
            row = ET.fromstring(row_xml)
        except ET.ParseError as exc:
            raise RuntimeError(
                f'native animation preset {key!r} contains invalid row_xml: {exc}'
            ) from exc
        if row.tag != f'{{{PML_NS}}}cTn':
            raise RuntimeError(f'native animation preset {key!r} is not a p:cTn row')

        spec = {
            'name': str(raw.get('name') or key),
            'filter': raw.get('filter'),
            'presetID': int(raw.get('preset_id')),
            'presetSubtype': int(raw.get('preset_subtype')),
            'presetClass': _PRESET_CLASS_BY_CATEGORY[category],
            'category': category,
            'msoEffectId': int(raw.get('mso_effect_id')),
            'defaultDurationMs': raw.get('default_duration_ms'),
            'durationScalable': bool(raw.get('duration_scalable')),
            'rowXml': row_xml,
            'effectOptions': raw.get('effect_options', {}),
        }
        if row.get('presetClass') != spec['presetClass']:
            raise RuntimeError(f'native animation preset {key!r} changed presetClass')
        if int(row.get('presetID', '-1')) != spec['presetID']:
            raise RuntimeError(f'native animation preset {key!r} changed presetID')
        if int(row.get('presetSubtype', '-1')) != spec['presetSubtype']:
            raise RuntimeError(f'native animation preset {key!r} changed presetSubtype')
        effect_options = spec['effectOptions']
        if not isinstance(effect_options, dict):
            raise RuntimeError(
                f'native animation preset {key!r} effect_options must be an object'
            )
        unknown_options = set(effect_options) - set(ANIMATION_EFFECT_OPTION_FIELDS)
        if unknown_options:
            raise RuntimeError(
                f'native animation preset {key!r} has unknown effect option(s): '
                + ', '.join(sorted(unknown_options))
            )
        for option_name, option_spec in effect_options.items():
            if not isinstance(option_spec, dict):
                raise RuntimeError(
                    f'native animation preset {key!r} option {option_name!r} '
                    'must be an object'
                )
            required = option_spec.get('required', False)
            if not isinstance(required, bool):
                raise RuntimeError(
                    f'native animation preset {key!r} option {option_name!r} '
                    'required must be a boolean'
                )
            if required and 'default' in option_spec:
                raise RuntimeError(
                    f'native animation preset {key!r} option {option_name!r} '
                    'cannot define both required and default'
                )
            option_type = option_spec.get('type')
            if option_type == 'enum':
                values = option_spec.get('values')
                if not isinstance(values, dict) or not values:
                    raise RuntimeError(
                        f'native animation preset {key!r} enum option '
                        f'{option_name!r} must define values'
                    )
                default = str(option_spec.get('default'))
                if default not in values:
                    raise RuntimeError(
                        f'native animation preset {key!r} enum option '
                        f'{option_name!r} has an unknown default'
                    )
                for option_value, variant_xml in values.items():
                    if not isinstance(option_value, str) or not isinstance(
                        variant_xml,
                        str,
                    ):
                        raise RuntimeError(
                            f'native animation preset {key!r} enum option '
                            f'{option_name!r} contains an invalid variant'
                        )
                    try:
                        variant = ET.fromstring(variant_xml)
                    except ET.ParseError as exc:
                        raise RuntimeError(
                            f'native animation preset {key!r} enum option '
                            f'{option_name!r}/{option_value!r} contains invalid XML: '
                            f'{exc}'
                        ) from exc
                    if variant.tag != f'{{{PML_NS}}}cTn':
                        raise RuntimeError(
                            f'native animation preset {key!r} enum option '
                            f'{option_name!r}/{option_value!r} is not a p:cTn row'
                        )
                    if variant.get('presetClass') != spec['presetClass']:
                        raise RuntimeError(
                            f'native animation preset {key!r} enum option '
                            f'{option_name!r}/{option_value!r} changed presetClass'
                        )
                    if int(variant.get('presetID', '-1')) != spec['presetID']:
                        raise RuntimeError(
                            f'native animation preset {key!r} enum option '
                            f'{option_name!r}/{option_value!r} changed presetID'
                        )
            elif option_type not in {'number', 'string', 'boolean', 'color'}:
                raise RuntimeError(
                    f'native animation preset {key!r} option {option_name!r} '
                    f'has unknown type: {option_type!r}'
                )
        native[key] = spec
        category_counts[category] += 1

    expected_counts = {'entrance': 53, 'emphasis': 33, 'path': 64, 'exit': 53}
    if category_counts != expected_counts:
        raise RuntimeError(
            'native animation preset category counts changed: '
            f'{category_counts!r}; expected {expected_counts!r}'
        )
    return native


NATIVE_ANIMATIONS = _load_native_animations()
NATIVE_ANIMATION_KEYS = tuple(NATIVE_ANIMATIONS)
ANIMATIONS = {
    **NATIVE_ANIMATIONS,
    **{
        alias: NATIVE_ANIMATIONS[canonical]
        for alias, canonical in ANIMATION_ALIASES.items()
    },
}

ANIMATION_MODES = ('auto', 'mixed', 'random')
ANIMATION_TRIGGERS = ('on-click', 'with-previous', 'after-previous')

_TRIGGER_NODE_TYPES = {
    'on-click': 'clickEffect',
    'with-previous': 'withEffect',
    'after-previous': 'afterEffect',
}
_NODE_TYPE_TRIGGERS = {
    value: key for key, value in _TRIGGER_NODE_TYPES.items()
}


@dataclass(frozen=True)
class AnimationTarget:
    """Resolved object-animation request for one PowerPoint shape."""

    shape_id: int
    delay_ms: int
    effect: str
    duration_ms: int
    effect_options: Mapping[str, object]
    trigger_shape_id: int | None = None
    repeat_count: float | None = None
    repeat_duration_ms: int | None = None
    auto_reverse: bool | None = None
    rewind: bool | None = None
    accelerate: float | None = None
    decelerate: float | None = None
    bounce_end: float | None = None
    restart: str | None = None
    after_effect: str = 'none'
    after_effect_color: str | None = None
    sound_relationship_id: str | None = None
    sound_name: str | None = None

    @property
    def playback_duration_ms(self) -> int:
        """Return the wall-clock duration used by after-previous scheduling."""
        one_play = self.duration_ms * (2 if self.auto_reverse else 1)
        if self.repeat_duration_ms is not None:
            return self.repeat_duration_ms
        if self.repeat_count is not None:
            return max(1, round(one_play * self.repeat_count))
        return one_play


@dataclass(frozen=True)
class AnimationRowSummary:
    """Read-back summary for one object-animation row in the animation pane."""

    shape_id: int
    effect: str | None
    supported_effects: tuple[str, ...]
    preset_class: str
    trigger: str
    duration_ms: int | None
    offset_ms: int
    preset_id: int
    preset_subtype: int
    filter_name: str | None
    effect_options: Mapping[str, object]
    trigger_shape_id: int | None
    repeat_count: float | None
    repeat_duration_ms: int | None
    auto_reverse: bool
    rewind: bool
    accelerate: float
    decelerate: float
    bounce_end: float
    restart: str
    after_effect: str
    after_effect_color: str | None
    sound_relationship_id: str | None
    sound_name: str | None
    playback_duration_ms: int | None


@dataclass(frozen=True)
class AnimationSequenceSummary:
    """Read-back summary for the logical object sequence on one slide."""

    timing_count: int
    trigger: str | None
    rows: tuple[AnimationRowSummary, ...]
    audio_target_ids: tuple[int, ...]


def _qn(namespace: str, tag: str) -> str:
    return f'{{{namespace}}}{tag}'


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def normalize_animation_effect(
    effect: object,
    *,
    allow_none: bool = True,
    allow_modes: bool = True,
) -> str | None:
    """Return a supported effect/mode without silently substituting another."""
    if effect is None or effect == 'none':
        if allow_none:
            return None
        raise ValueError('animation effect is required')
    if not isinstance(effect, str):
        raise ValueError(f'animation effect must be a string: {effect!r}')
    if effect in ANIMATION_ALIASES:
        return ANIMATION_ALIASES[effect]
    if effect in NATIVE_ANIMATIONS:
        return effect
    if allow_modes and effect in ANIMATION_MODES:
        return effect
    valid = list(ANIMATIONS)
    if allow_modes:
        valid.extend(ANIMATION_MODES)
    if allow_none:
        valid.append('none')
    raise ValueError(
        f'unknown animation effect {effect!r}; valid effects: {", ".join(valid)}'
    )


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field} must be a finite number: {value!r}')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{field} must be a finite number: {value!r}')
    return number


def _normalize_animation_color(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f'{field} must be #RRGGBB or theme:<scheme-color>: {value!r}'
        )
    if re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
        return value.upper()
    if re.fullmatch(
        r'theme:(?:dk1|lt1|dk2|lt2|tx1|tx2|bg1|bg2|accent[1-6]|'
        r'hlink|folHlink)',
        value,
    ):
        return value
    raise ValueError(
        f'{field} must be #RRGGBB or theme:<scheme-color>: {value!r}'
    )


def _normalize_powerpoint_font_name(value: object, field: str) -> str:
    """Return one concrete PowerPoint font name without checking installation."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f'{field} must be one concrete PowerPoint font name: {value!r}'
        )
    normalized = value.strip()
    if len(normalized) > 255:
        raise ValueError(f'{field} exceeds 255 characters')
    if ',' in normalized:
        raise ValueError(
            f'{field} must be one concrete PowerPoint font name, '
            f'not a CSS font stack: {value!r}'
        )
    if normalized.casefold() in _NON_CONCRETE_FONT_NAMES:
        raise ValueError(
            f'{field} must be one concrete PowerPoint font name, '
            f'not a generic family or CSS-wide keyword: {value!r}'
        )
    return normalized


def normalize_animation_effect_options(
    effect: str,
    options: object = None,
) -> dict[str, object]:
    """Validate effect-specific PowerPoint EffectParameters values."""
    if effect not in NATIVE_ANIMATIONS:
        if options in (None, {}):
            return {}
        raise ValueError(
            'animation effect_options require one explicit canonical effect; '
            f'found {effect!r}'
        )
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise ValueError(f'animation effect_options must be an object: {options!r}')

    option_specs = NATIVE_ANIMATIONS[effect]['effectOptions']
    unknown = set(options) - set(option_specs)
    if unknown:
        unsupported = ', '.join(sorted(unknown))
        supported = ', '.join(option_specs) or '(none)'
        raise ValueError(
            f'animation effect {effect!r} does not support effect option(s): '
            f'{unsupported}; supported options: {supported}'
        )
    missing_required = sorted(
        name
        for name, spec in option_specs.items()
        if spec.get('required') and name not in options
    )
    if missing_required:
        required_fields = ', '.join(
            f'effect_options.{name}' for name in missing_required
        )
        raise ValueError(
            f'animation effect {effect!r} requires {required_fields}'
        )

    normalized: dict[str, object] = {}
    for name, value in options.items():
        spec = option_specs[name]
        option_type = spec['type']
        field = f'animation effect_options.{name}'
        if option_type == 'enum':
            key = str(value)
            if isinstance(value, bool) or key not in spec['values']:
                valid = ', '.join(spec['values'])
                raise ValueError(
                    f'{field} for {effect!r} must be one of {valid}: {value!r}'
                )
            normalized[name] = (
                int(key)
                if name == 'amount' and re.fullmatch(r'\d+', key)
                else key
            )
        elif option_type == 'number':
            number = _finite_number(value, field)
            minimum = spec.get('minimum')
            maximum = spec.get('maximum')
            if minimum is not None and number < float(minimum):
                raise ValueError(
                    f'{field} for {effect!r} must be at least {minimum}: {value!r}'
                )
            if maximum is not None and number > float(maximum):
                raise ValueError(
                    f'{field} for {effect!r} must be at most {maximum}: {value!r}'
                )
            normalized[name] = number
        elif option_type == 'string':
            if name == 'font_name':
                normalized[name] = _normalize_powerpoint_font_name(value, field)
            else:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f'{field} must be a non-empty string: {value!r}'
                    )
                normalized_value = value.strip()
                if len(normalized_value) > 255:
                    raise ValueError(f'{field} exceeds 255 characters')
                normalized[name] = normalized_value
        elif option_type == 'boolean':
            if not isinstance(value, bool):
                raise ValueError(f'{field} must be a boolean: {value!r}')
            normalized[name] = value
        elif option_type == 'color':
            normalized[name] = _normalize_animation_color(value, field)
        else:
            raise AssertionError(f'unhandled animation effect option type: {option_type}')
    return normalized


def normalize_animation_effect_request(
    effect: object,
    options: object = None,
    *,
    allow_none: bool = True,
    allow_modes: bool = True,
) -> tuple[str | None, dict[str, object]]:
    """Normalize one effect plus options, including legacy semantic aliases."""
    raw_effect = effect
    canonical = normalize_animation_effect(
        effect,
        allow_none=allow_none,
        allow_modes=allow_modes,
    )
    alias_options = (
        ANIMATION_ALIAS_OPTIONS.get(raw_effect, {})
        if isinstance(raw_effect, str)
        else {}
    )
    explicit_options: Mapping[str, object]
    if options is None:
        explicit_options = {}
    elif isinstance(options, Mapping):
        explicit_options = options
    else:
        raise ValueError(f'animation effect_options must be an object: {options!r}')
    for name, alias_value in alias_options.items():
        if name in explicit_options and explicit_options[name] != alias_value:
            raise ValueError(
                f'legacy animation effect {raw_effect!r} implies '
                f'effect_options.{name}={alias_value!r}, which conflicts with '
                f'{explicit_options[name]!r}'
            )
    merged = {**alias_options, **explicit_options}
    if canonical is None or canonical in ANIMATION_MODES:
        if merged:
            raise ValueError(
                'animation effect_options require one explicit canonical effect; '
                f'found {canonical or "none"!r}'
            )
        return canonical, {}
    return canonical, normalize_animation_effect_options(canonical, merged)


def normalize_animation_trigger(trigger: object) -> str:
    """Return a supported PowerPoint Start mode or raise a precise error."""
    if not isinstance(trigger, str):
        raise ValueError(f'animation trigger must be a string: {trigger!r}')
    if trigger not in ANIMATION_TRIGGERS:
        raise ValueError(
            f'unknown animation trigger {trigger!r}; valid triggers: '
            f'{", ".join(ANIMATION_TRIGGERS)}'
        )
    return trigger


def _seconds_to_ms(value: object, field: str, *, allow_zero: bool) -> int:
    seconds = validate_seconds(value, field, allow_zero=allow_zero)
    raw_milliseconds = seconds * 1000
    if (
        not math.isfinite(raw_milliseconds)
        or raw_milliseconds > MAX_OOXML_MILLISECONDS
    ):
        raise ValueError(f'{field} exceeds the OOXML millisecond limit: {value!r}')
    milliseconds = int(raw_milliseconds)
    return milliseconds if allow_zero else max(1, milliseconds)


def animation_seconds_to_milliseconds(
    value: object,
    field: str,
    *,
    allow_zero: bool,
) -> int:
    """Convert validated animation seconds to the OOXML millisecond range."""
    return _seconds_to_ms(value, field, allow_zero=allow_zero)


def _positive_shape_id(value: object, field: str = 'animation shape_id') -> int:
    if isinstance(value, bool):
        raise ValueError(f'{field} must be a positive integer: {value!r}')
    if isinstance(value, int):
        shape_id = value
    elif isinstance(value, str) and re.fullmatch(r'[1-9]\d*', value):
        shape_id = int(value)
    else:
        raise ValueError(f'{field} must be a positive integer: {value!r}')
    if shape_id <= 0 or shape_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(f'{field} must be a positive integer: {value!r}')
    return shape_id


def _non_negative_milliseconds(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f'{field} must be a non-negative integer: {value!r}')
    if isinstance(value, int):
        milliseconds = value
    elif isinstance(value, str) and re.fullmatch(r'\d+', value):
        milliseconds = int(value)
    else:
        raise ValueError(f'{field} must be a non-negative integer: {value!r}')
    if milliseconds < 0 or milliseconds > MAX_OOXML_MILLISECONDS:
        raise ValueError(
            f'{field} must be between 0 and {MAX_OOXML_MILLISECONDS}: {value!r}'
        )
    return milliseconds


def _optional_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f'{field} must be a boolean: {value!r}')
    return value


def _optional_ratio(value: object, field: str) -> float:
    ratio = _finite_number(value, field)
    if ratio < 0 or ratio > 1:
        raise ValueError(f'{field} must be between 0 and 1: {value!r}')
    return ratio


def _normalize_repeat_count(value: object) -> float:
    count = _finite_number(value, 'animation repeat_count')
    if count <= 0 or count * 1000 > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(
            'animation repeat_count must be positive and fit the OOXML range: '
            f'{value!r}'
        )
    return count


def _normalize_after_effect(value: object) -> tuple[str, str | None]:
    if value is None:
        return 'none', None
    if isinstance(value, str):
        effect_type = value
        color = None
    elif isinstance(value, Mapping):
        unknown = set(value) - {'type', 'color'}
        if unknown:
            raise ValueError(
                'animation after_effect has unknown field(s): '
                + ', '.join(sorted(unknown))
            )
        effect_type = value.get('type', 'none')
        color = value.get('color')
    else:
        raise ValueError(
            f'animation after_effect must be a string or object: {value!r}'
        )
    if effect_type not in ANIMATION_AFTER_EFFECTS:
        raise ValueError(
            f'animation after_effect.type must be one of '
            f'{", ".join(ANIMATION_AFTER_EFFECTS)}: {effect_type!r}'
        )
    if effect_type == 'dim':
        if color is None:
            raise ValueError('animation dim after_effect requires color')
        return effect_type, _normalize_animation_color(
            color,
            'animation after_effect.color',
        )
    if color is not None:
        raise ValueError(
            f'animation after_effect.color is valid only with type "dim": {color!r}'
        )
    return effect_type, None


def _normalize_sound(value: object) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if not isinstance(value, Mapping):
        raise ValueError(
            'low-level animation sound must be an object with '
            'relationship_id and name'
        )
    unknown = set(value) - {'relationship_id', 'name'}
    if unknown:
        raise ValueError(
            'low-level animation sound has unknown field(s): '
            + ', '.join(sorted(unknown))
        )
    relationship_id = value.get('relationship_id')
    name = value.get('name')
    if not isinstance(relationship_id, str) or not re.fullmatch(
        r'rId[1-9]\d*',
        relationship_id,
    ):
        raise ValueError(
            'low-level animation sound relationship_id must match rIdN: '
            f'{relationship_id!r}'
        )
    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f'low-level animation sound name must be non-empty: {name!r}'
        )
    return relationship_id, name


def _normalize_target_mapping(
    target: Mapping[str, object],
    default_duration_ms: int,
) -> AnimationTarget:
    allowed = {
        'shape_id',
        'delay_ms',
        'effect',
        'duration',
        'effect_options',
        'trigger_shape_id',
        *ANIMATION_TIMING_OPTION_FIELDS,
        'after_effect',
        'sound',
    }
    unknown = set(target) - allowed
    if unknown:
        raise ValueError(
            'animation target has unknown field(s): ' + ', '.join(sorted(unknown))
        )
    shape_id = _positive_shape_id(target.get('shape_id'))
    delay_ms = _non_negative_milliseconds(
        target.get('delay_ms', 0),
        'animation target delay_ms',
    )
    effect, effect_options = normalize_animation_effect_request(
        target.get('effect'),
        target.get('effect_options'),
        allow_none=False,
        allow_modes=False,
    )
    duration_ms = default_duration_ms
    if target.get('duration') is not None:
        duration_ms = _seconds_to_ms(
            target.get('duration'),
            'animation target duration',
            allow_zero=False,
        )
    trigger_shape_id = (
        _positive_shape_id(
            target['trigger_shape_id'],
            'animation target trigger_shape_id',
        )
        if 'trigger_shape_id' in target
        else None
    )
    if trigger_shape_id == shape_id:
        raise ValueError(
            'animation trigger_shape_id must target a different shape'
        )
    repeat_count = (
        _normalize_repeat_count(target['repeat_count'])
        if 'repeat_count' in target
        else None
    )
    repeat_duration_ms = (
        _seconds_to_ms(
            target['repeat_duration'],
            'animation repeat_duration',
            allow_zero=False,
        )
        if 'repeat_duration' in target
        else None
    )
    if repeat_count is not None and repeat_duration_ms is not None:
        raise ValueError(
            'animation repeat_count and repeat_duration are mutually exclusive'
        )
    auto_reverse = (
        _optional_bool(target['auto_reverse'], 'animation auto_reverse')
        if 'auto_reverse' in target
        else None
    )
    rewind = (
        _optional_bool(target['rewind'], 'animation rewind')
        if 'rewind' in target
        else None
    )
    accelerate = (
        _optional_ratio(target['accelerate'], 'animation accelerate')
        if 'accelerate' in target
        else None
    )
    decelerate = (
        _optional_ratio(target['decelerate'], 'animation decelerate')
        if 'decelerate' in target
        else None
    )
    if (
        accelerate is not None
        and decelerate is not None
        and accelerate + decelerate > 1
    ):
        raise ValueError(
            'animation accelerate + decelerate must not exceed 1'
        )
    bounce_end = (
        _optional_ratio(target['bounce_end'], 'animation bounce_end')
        if 'bounce_end' in target
        else None
    )
    if bounce_end and decelerate:
        raise ValueError(
            'animation bounce_end and decelerate are mutually exclusive '
            'in PowerPoint'
        )
    restart = target.get('restart')
    if restart is not None and restart not in ANIMATION_RESTARTS:
        raise ValueError(
            f'animation restart must be one of '
            f'{", ".join(ANIMATION_RESTARTS)}: {restart!r}'
        )
    after_effect, after_effect_color = _normalize_after_effect(
        target.get('after_effect')
    )
    sound_relationship_id, sound_name = _normalize_sound(target.get('sound'))
    return AnimationTarget(
        shape_id=shape_id,
        delay_ms=delay_ms,
        effect=effect,
        duration_ms=duration_ms,
        effect_options=effect_options,
        trigger_shape_id=trigger_shape_id,
        repeat_count=repeat_count,
        repeat_duration_ms=repeat_duration_ms,
        auto_reverse=auto_reverse,
        rewind=rewind,
        accelerate=accelerate,
        decelerate=decelerate,
        bounce_end=bounce_end,
        restart=restart,
        after_effect=after_effect,
        after_effect_color=after_effect_color,
        sound_relationship_id=sound_relationship_id,
        sound_name=sound_name,
    )


def _normalize_target(
    target: Sequence[object] | Mapping[str, object],
    default_duration_ms: int,
) -> AnimationTarget:
    if isinstance(target, Mapping):
        return _normalize_target_mapping(target, default_duration_ms)
    if isinstance(target, (str, bytes)) or not isinstance(target, Sequence):
        raise ValueError(f'animation target must be a 3- or 4-item sequence: {target!r}')
    if len(target) not in (3, 4):
        raise ValueError(f'animation target must contain 3 or 4 items: {target!r}')
    shape_id = _positive_shape_id(target[0])
    delay_ms = _non_negative_milliseconds(target[1], 'animation target delay_ms')
    effect, effect_options = normalize_animation_effect_request(
        target[2],
        allow_none=False,
        allow_modes=False,
    )
    duration_ms = default_duration_ms
    if len(target) == 4 and target[3] is not None:
        duration_ms = _seconds_to_ms(
            target[3],
            'animation target duration',
            allow_zero=False,
        )
    return AnimationTarget(
        shape_id=shape_id,
        delay_ms=delay_ms,
        effect=effect,
        duration_ms=duration_ms,
        effect_options=effect_options,
    )

# Pool used by 'mixed' / 'random' modes. Every entry is a canonical
# PowerPoint-authored preset; compatibility aliases never enter selection.
_MIXED_POOL = [
    'entrance_blinds', 'entrance_checkerboard', 'entrance_dissolve',
    'entrance_fly', 'entrance_ascend', 'entrance_random_bars',
    'entrance_box', 'entrance_split', 'entrance_strips', 'entrance_wedge',
    'entrance_wheel', 'entrance_wipe', 'entrance_expand', 'entrance_fade',
    'entrance_swivel', 'entrance_zoom',
]

# Small modern pool used by 'auto' mode when the group id matches no semantic
# pattern. Restricted to four widely supported, restrained effects so the
# fallback cycle never produces PowerPoint-era visuals.
_AUTO_POOL = [
    'entrance_fade',
    'entrance_wipe',
    'entrance_fly',
    'entrance_zoom',
]

# Image-only diversity pool. Image-like groups (`hero`, `figure-`, `image`,
# `img-`, `kpi`) deliberately cycle through a richer set of visual effects
# rather than mapping to a single effect: images are visual focal points, so
# variation is desirable on them even when surrounding information-dense
# elements (titles, charts, lists) stay reserved. Pool members are chosen for
# image-friendly motion — no PowerPoint-era patterns (``entrance_blinds`` /
# ``entrance_checkerboard`` / ``entrance_random_bars`` / ``entrance_wedge``)
# that would dominate raster content.
_IMAGE_POOL = [
    'entrance_zoom',
    'entrance_dissolve',
    'entrance_circle',
    'entrance_box',
    'entrance_diamond',
    'entrance_wheel',
]
_IMAGE_KEYWORDS: tuple[str, ...] = ('hero', 'figure-', 'image', 'img-', 'kpi')

# Ordered (substring, effect) patterns consumed by 'auto' mode for non-image
# groups. The first matching substring in the lowercased group id wins;
# ordering matters where substrings could overlap (e.g. 'title' before 'item'
# prevents 'item-title' from being misread as a list item). All substrings are
# lowercase. Image-like ids are handled separately via ``_IMAGE_POOL`` because
# they cycle rather than map to a single effect.
_SEMANTIC_PATTERNS: list[tuple[tuple[str, ...], str]] = [
    (
        ('title', 'chapter-', 'section-', 'cover-', 'tagline', 'subtitle'),
        'entrance_fade',
    ),
    (
        ('chart', 'table', 'legend', 'timeline', 'track'),
        'entrance_wipe',
    ),
    (('card-', 'pillar-', 'item-', 'step-', 'stage-', 'tier-',
      'principle-', 'q-', 'schema-'),                           'entrance_fly'),
    (('takeaway', 'callout', 'quote', 'source', 'conclusion', 'note',
      'try-at-home'),                                           'entrance_fade'),
]


def _semantic_effect(group_id: str | None, idx: int = 0, offset: int = 0) -> str | None:
    """Return the effect mapped from a group id, or None if no pattern matches.

    Image-like ids cycle through ``_IMAGE_POOL`` using ``idx + offset`` so the
    same deck shows different effects across multiple images. Other semantic
    matches return a single stable effect because information-dense elements
    benefit from consistency, not variation.
    """
    if not group_id:
        return None
    lower = group_id.lower()
    if any(k in lower for k in _IMAGE_KEYWORDS):
        return _IMAGE_POOL[(idx + offset) % len(_IMAGE_POOL)]
    for substrings, effect in _SEMANTIC_PATTERNS:
        if any(s in lower for s in substrings):
            return effect
    return None


def create_timing_xml(
    animation: str = 'entrance_fade',
    duration: float = 1.0,
    delay: float = 0,
    shape_id: int = 2
) -> str:
    """
    Generate an object-animation timing XML fragment

    Args:
        animation: Canonical PowerPoint effect name
        duration: Animation duration (seconds)
        delay: Animation delay (seconds)
        shape_id: Target shape ID (SVG image is typically 2)

    Returns:
        A <p:timing> element string insertable into slide XML
    """
    animation = normalize_animation_effect(
        animation,
        allow_none=False,
        allow_modes=False,
    )
    shape_id = _positive_shape_id(shape_id)
    delay_ms = _seconds_to_ms(
        delay,
        'animation delay',
        allow_zero=True,
    )
    return create_sequence_timing_xml(
        [(shape_id, delay_ms, animation, duration)],
        duration=duration,
        trigger='after-previous',
    )


def _ctn_numeric_delay(ctn: ET.Element) -> int:
    """Return the largest direct numeric start delay on one time node."""
    conditions = ctn.find(_qn(PML_NS, 'stCondLst'))
    if conditions is None:
        return 0
    values = [
        int(condition.get('delay', '0'))
        for condition in conditions.findall(_qn(PML_NS, 'cond'))
        if condition.get('delay', '').isdigit()
    ]
    return max(values, default=0)


def _row_effective_duration_ms(row: ET.Element) -> int | None:
    """Return the finite end time PowerPoint exposes for one preset row."""
    ends: list[int] = []
    for ctn in row.iter(_qn(PML_NS, 'cTn')):
        if ctn is row:
            continue
        raw_duration = ctn.get('dur')
        if raw_duration is None or not raw_duration.isdigit():
            continue
        ends.append(_ctn_numeric_delay(ctn) + int(raw_duration))
    return max(ends) if ends else None


def _scale_animation_row_duration(
    row: ET.Element,
    *,
    base_duration_ms: int,
    requested_duration_ms: int,
) -> None:
    """Scale all finite behavior durations/delays as one PowerPoint row."""
    ratio = requested_duration_ms / base_duration_ms
    for ctn in row.iter(_qn(PML_NS, 'cTn')):
        if ctn is row:
            continue
        raw_duration = ctn.get('dur')
        if raw_duration is not None and raw_duration.isdigit():
            numeric_duration = int(raw_duration)
            ctn.set(
                'dur',
                (
                    '1'
                    if numeric_duration == 1
                    else str(max(1, round(numeric_duration * ratio)))
                ),
            )
        conditions = ctn.find(_qn(PML_NS, 'stCondLst'))
        if conditions is None:
            continue
        for condition in conditions.findall(_qn(PML_NS, 'cond')):
            raw_delay = condition.get('delay')
            if raw_delay is not None and raw_delay.isdigit():
                condition.set('delay', str(round(int(raw_delay) * ratio)))

    actual_duration = _row_effective_duration_ms(row)
    if actual_duration is None or actual_duration == requested_duration_ms:
        return
    end_nodes = [
        ctn
        for ctn in row.iter(_qn(PML_NS, 'cTn'))
        if ctn is not row
        and (ctn.get('dur') or '').isdigit()
        and _ctn_numeric_delay(ctn) + int(ctn.get('dur', '0')) == actual_duration
    ]
    for ctn in end_nodes:
        delay = _ctn_numeric_delay(ctn)
        if delay >= requested_duration_ms:
            conditions = ctn.find(_qn(PML_NS, 'stCondLst'))
            numeric = (
                [
                    condition
                    for condition in conditions.findall(_qn(PML_NS, 'cond'))
                    if condition.get('delay', '').isdigit()
                ]
                if conditions is not None
                else []
            )
            if numeric:
                numeric[-1].set('delay', str(max(0, requested_duration_ms - 1)))
                delay = _ctn_numeric_delay(ctn)
        ctn.set('dur', str(max(1, requested_duration_ms - delay)))


def _row_semantic_signature(row: ET.Element) -> tuple[object, ...]:
    """Return an id/target/duration-independent preset behavior signature."""
    def canonical(element: ET.Element) -> tuple[object, ...]:
        attributes: list[tuple[str, str]] = []
        local_name = _local_name(element.tag)
        for name, value in sorted(element.attrib.items()):
            if name in {'id', 'nodeType', 'grpId'}:
                continue
            if local_name == 'spTgt' and name == 'spid':
                value = '#shape'
            elif local_name == 'cTn' and name == 'dur' and value.isdigit():
                value = '#duration'
            elif local_name == 'cond' and name == 'delay' and value.isdigit():
                value = '#delay'
            attributes.append((name, value))
        return (
            element.tag,
            tuple(attributes),
            (element.text or '').strip(),
            tuple(canonical(child) for child in list(element)),
        )

    return canonical(row)


def _row_timing_profile(
    row: ET.Element,
) -> tuple[tuple[str, float, float], ...]:
    """Return behavior timing ratios, excluding 1ms visibility bookkeeping."""
    total = _row_effective_duration_ms(row)
    if total is None or total <= 1:
        return ()
    parent_map = {
        child: parent
        for parent in row.iter()
        for child in list(parent)
    }
    behavior_names = {
        'anim',
        'animClr',
        'animEffect',
        'animMotion',
        'animRot',
        'animScale',
        'set',
    }
    profile: list[tuple[str, float, float]] = []
    for ctn in row.iter(_qn(PML_NS, 'cTn')):
        if ctn is row:
            continue
        raw_duration = ctn.get('dur')
        if raw_duration is None or not raw_duration.isdigit():
            continue
        duration = int(raw_duration)
        owner = parent_map.get(ctn)
        while owner is not None and _local_name(owner.tag) not in behavior_names:
            owner = parent_map.get(owner)
        behavior = _local_name(owner.tag) if owner is not None else 'unknown'
        if (
            duration == 1
            and behavior == 'set'
            and owner is not None
            and any(
                (attribute.text or '') == 'style.visibility'
                for attribute in owner.iter(_qn(PML_NS, 'attrName'))
            )
        ):
            continue
        profile.append(
            (
                behavior,
                _ctn_numeric_delay(ctn) / total,
                duration / total,
            )
        )
    return tuple(profile)


def _animation_spec_matches_row(row: ET.Element, spec: Mapping[str, Any]) -> bool:
    """Require the PowerPoint-authored structure and internal timing ratios."""
    template = ET.fromstring(spec['rowXml'])
    if _row_semantic_signature(row) != _row_semantic_signature(template):
        return False
    actual_duration = _row_effective_duration_ms(row)
    if actual_duration is not None and actual_duration < 100:
        # Millisecond quantization necessarily collapses multi-step ratios at
        # sub-100ms speeds; structure and total duration remain authoritative.
        return True
    actual_profile = _row_timing_profile(row)
    template_profile = _row_timing_profile(template)
    if len(actual_profile) != len(template_profile):
        return False
    for actual, expected in zip(actual_profile, template_profile):
        if actual[0] != expected[0]:
            return False
        if abs(actual[1] - expected[1]) > 0.01:
            return False
        if abs(actual[2] - expected[2]) > 0.01:
            return False
    return True


def _format_decimal(value: float) -> str:
    """Format one finite decimal without exponent notation or negative zero."""
    rendered = f'{value:.9f}'.rstrip('0').rstrip('.')
    return '0' if rendered in {'', '-0'} else rendered


def _color_element(value: str) -> ET.Element:
    if value.startswith('#'):
        return ET.Element(_qn(_DML_NS, 'srgbClr'), {'val': value[1:]})
    return ET.Element(_qn(_DML_NS, 'schemeClr'), {'val': value.split(':', 1)[1]})


def _replace_animation_colors(row: ET.Element, value: str) -> None:
    parent_map = {
        child: parent
        for parent in row.iter()
        for child in list(parent)
    }
    color_tags = {
        _qn(_DML_NS, 'srgbClr'),
        _qn(_DML_NS, 'schemeClr'),
        _qn(_DML_NS, 'hslClr'),
        _qn(_DML_NS, 'scrgbClr'),
        _qn(_DML_NS, 'sysClr'),
        _qn(_DML_NS, 'prstClr'),
    }
    colors = [element for element in row.iter() if element.tag in color_tags]
    if not colors:
        raise RuntimeError('color-capable animation preset lost its color node')
    for color in colors:
        parent = parent_map[color]
        index = list(parent).index(color)
        parent.remove(color)
        parent.insert(index, _color_element(value))


def _set_effect_option_value(
    row: ET.Element,
    animation: str,
    name: str,
    value: object,
) -> None:
    if name == 'amount' and animation == 'emphasis_spin':
        rotations = list(row.iter(_qn(PML_NS, 'animRot')))
        if len(rotations) != 1:
            raise RuntimeError('emphasis_spin preset lost its p:animRot node')
        rotations[0].set('by', str(round(float(value) * 60000)))
        return
    if name == 'amount' and animation == 'emphasis_transparency':
        matched = False
        for node in row.iter(_qn(PML_NS, 'set')):
            attributes = {
                (attribute.text or '').strip()
                for attribute in node.iter(_qn(PML_NS, 'attrName'))
            }
            if 'style.opacity' not in attributes:
                continue
            values = list(node.iter(_qn(PML_NS, 'strVal')))
            if len(values) != 1:
                raise RuntimeError(
                    'emphasis_transparency preset lost its opacity value'
                )
            values[0].set('val', _format_decimal(1 - float(value)))
            matched = True
        if not matched:
            raise RuntimeError(
                'emphasis_transparency preset lost its opacity behavior'
            )
        return
    if name == 'color':
        _replace_animation_colors(row, str(value))
        return
    if name == 'font_name':
        matched = False
        for node in row.iter(_qn(PML_NS, 'set')):
            attributes = {
                (attribute.text or '').strip()
                for attribute in node.iter(_qn(PML_NS, 'attrName'))
            }
            if 'style.fontFamily' not in attributes:
                continue
            values = list(node.iter(_qn(PML_NS, 'strVal')))
            if len(values) != 1:
                raise RuntimeError(
                    'emphasis_change_font preset lost its font value'
                )
            values[0].set('val', str(value))
            matched = True
        if not matched:
            raise RuntimeError(
                'emphasis_change_font preset lost its font behavior'
            )
        return
    if name == 'relative':
        motions = list(row.iter(_qn(PML_NS, 'animMotion')))
        if len(motions) != 1:
            raise RuntimeError('motion-path preset lost its p:animMotion node')
        motions[0].set('pathEditMode', 'relative' if value else 'fixed')
        return
    if name == 'size':
        scales = list(row.iter(_qn(PML_NS, 'animScale')))
        if len(scales) != 1:
            raise RuntimeError(
                'emphasis_grow_shrink preset lost its p:animScale node'
        )
        amount = str(round(float(value) * 1000))
        targets = scales[0].findall(_qn(PML_NS, 'to'))
        if len(targets) > 1:
            raise RuntimeError(
                'emphasis_grow_shrink preset lost its scale value'
            )
        target = (
            targets[0]
            if targets
            else ET.SubElement(scales[0], _qn(PML_NS, 'to'))
        )
        target.set('x', amount)
        target.set('y', amount)
        return
    raise AssertionError(f'unhandled continuous animation option: {name}')


def _animation_row_for_options(
    animation: str,
    effect_options: Mapping[str, object],
) -> ET.Element:
    """Return the authored variant row with continuous options applied."""
    spec = NATIVE_ANIMATIONS[animation]
    option_specs = spec['effectOptions']
    row_xml = spec['rowXml']
    for name, value in effect_options.items():
        option_spec = option_specs[name]
        if option_spec['type'] != 'enum':
            continue
        key = str(value)
        row_xml = option_spec['values'][key]
    row = ET.fromstring(row_xml)
    for name, value in effect_options.items():
        if option_specs[name]['type'] == 'enum':
            continue
        _set_effect_option_value(row, animation, name, value)
    return row


def _apply_timing_options(row: ET.Element, target: AnimationTarget) -> None:
    if target.repeat_count is not None:
        row.set('repeatCount', str(round(target.repeat_count * 1000)))
        row.attrib.pop('repeatDur', None)
    if target.repeat_duration_ms is not None:
        row.set('repeatDur', str(target.repeat_duration_ms))
        row.attrib.pop('repeatCount', None)
    if target.auto_reverse is not None:
        if target.auto_reverse:
            row.set('autoRev', '1')
        else:
            row.attrib.pop('autoRev', None)
    if target.rewind is not None:
        row.set('fill', 'remove' if target.rewind else 'hold')
    if target.accelerate is not None:
        if target.accelerate:
            row.set('accel', str(round(target.accelerate * 100000)))
        else:
            row.attrib.pop('accel', None)
    if target.decelerate is not None:
        if target.decelerate:
            row.set('decel', str(round(target.decelerate * 100000)))
        else:
            row.attrib.pop('decel', None)
    if target.bounce_end is not None:
        bounce_nodes = [
            node
            for node in row.iter()
            if _local_name(node.tag) in {
                'anim',
                'animClr',
                'animEffect',
                'animMotion',
                'animRot',
                'animScale',
            }
        ]
        if target.bounce_end and not bounce_nodes:
            raise ValueError(
                f'animation effect {target.effect!r} has no behavior that '
                'supports bounce_end'
            )
        if target.bounce_end:
            row.set(
                _qn(_P14_NS, 'presetBounceEnd'),
                str(round(target.bounce_end * 100000)),
            )
        else:
            row.attrib.pop(_qn(_P14_NS, 'presetBounceEnd'), None)
        for node in bounce_nodes:
            if target.bounce_end:
                node.set(
                    _qn(_P14_NS, 'bounceEnd'),
                    str(round(target.bounce_end * 100000)),
                )
            else:
                node.attrib.pop(_qn(_P14_NS, 'bounceEnd'), None)
    if target.restart is not None:
        row.set(
            'restart',
            {
                'always': 'always',
                'when-not-active': 'whenNotActive',
                'never': 'never',
            }[target.restart],
        )


def _append_after_effect(
    row: ET.Element,
    target: AnimationTarget,
    row_id: int,
) -> None:
    if target.after_effect == 'none':
        return
    sub_timing = row.find(_qn(PML_NS, 'subTnLst'))
    if sub_timing is None:
        sub_timing = ET.SubElement(row, _qn(PML_NS, 'subTnLst'))
    if target.after_effect == 'dim':
        animation = ET.SubElement(
            sub_timing,
            _qn(PML_NS, 'animClr'),
            {'clrSpc': 'rgb', 'dir': 'cw'},
        )
        behavior = ET.SubElement(
            animation,
            _qn(PML_NS, 'cBhvr'),
            {'override': 'childStyle'},
        )
        ET.SubElement(
            behavior,
            _qn(PML_NS, 'cTn'),
            {
                'dur': '1',
                'fill': 'hold',
                'display': '0',
                'masterRel': 'nextClick',
                'afterEffect': '1',
            },
        )
        target_element = ET.SubElement(behavior, _qn(PML_NS, 'tgtEl'))
        ET.SubElement(
            target_element,
            _qn(PML_NS, 'spTgt'),
            {'spid': str(target.shape_id)},
        )
        names = ET.SubElement(behavior, _qn(PML_NS, 'attrNameLst'))
        ET.SubElement(names, _qn(PML_NS, 'attrName')).text = 'ppt_c'
        destination = ET.SubElement(animation, _qn(PML_NS, 'to'))
        destination.append(_color_element(str(target.after_effect_color)))
        return

    setting = ET.SubElement(sub_timing, _qn(PML_NS, 'set'))
    behavior = ET.SubElement(
        setting,
        _qn(PML_NS, 'cBhvr'),
        {'override': 'childStyle'},
    )
    ctn_attributes = {
        'dur': '1',
        'fill': 'hold',
        'display': '0',
        'masterRel': (
            'sameClick'
            if target.after_effect == 'hide'
            else 'nextClick'
        ),
        'afterEffect': '1',
    }
    ctn = ET.SubElement(behavior, _qn(PML_NS, 'cTn'), ctn_attributes)
    if target.after_effect == 'hide':
        conditions = ET.SubElement(ctn, _qn(PML_NS, 'stCondLst'))
        condition = ET.SubElement(
            conditions,
            _qn(PML_NS, 'cond'),
            {'evt': 'end', 'delay': '0'},
        )
        ET.SubElement(condition, _qn(PML_NS, 'tn'), {'val': str(row_id)})
    target_element = ET.SubElement(behavior, _qn(PML_NS, 'tgtEl'))
    ET.SubElement(
        target_element,
        _qn(PML_NS, 'spTgt'),
        {'spid': str(target.shape_id)},
    )
    names = ET.SubElement(behavior, _qn(PML_NS, 'attrNameLst'))
    ET.SubElement(names, _qn(PML_NS, 'attrName')).text = 'style.visibility'
    destination = ET.SubElement(setting, _qn(PML_NS, 'to'))
    ET.SubElement(destination, _qn(PML_NS, 'strVal'), {'val': 'hidden'})


def _append_animation_sound(row: ET.Element, target: AnimationTarget) -> None:
    if target.sound_relationship_id is None:
        return
    sub_timing = row.find(_qn(PML_NS, 'subTnLst'))
    if sub_timing is None:
        sub_timing = ET.SubElement(row, _qn(PML_NS, 'subTnLst'))
    audio = ET.SubElement(sub_timing, _qn(PML_NS, 'audio'))
    media = ET.SubElement(audio, _qn(PML_NS, 'cMediaNode'))
    ctn = ET.SubElement(
        media,
        _qn(PML_NS, 'cTn'),
        {'display': '0', 'masterRel': 'sameClick'},
    )
    conditions = ET.SubElement(ctn, _qn(PML_NS, 'stCondLst'))
    condition = ET.SubElement(
        conditions,
        _qn(PML_NS, 'cond'),
        {'evt': 'begin', 'delay': '0'},
    )
    ET.SubElement(condition, _qn(PML_NS, 'tn'), {'val': str(row.get('id'))})
    end_conditions = ET.SubElement(ctn, _qn(PML_NS, 'endCondLst'))
    end_condition = ET.SubElement(
        end_conditions,
        _qn(PML_NS, 'cond'),
        {'evt': 'onStopAudio', 'delay': '0'},
    )
    target_element = ET.SubElement(end_condition, _qn(PML_NS, 'tgtEl'))
    ET.SubElement(target_element, _qn(PML_NS, 'sldTgt'))
    target_element = ET.SubElement(media, _qn(PML_NS, 'tgtEl'))
    ET.SubElement(
        target_element,
        _qn(PML_NS, 'sndTgt'),
        {
            _qn(_REL_NS, 'embed'): str(target.sound_relationship_id),
            'name': str(target.sound_name),
        },
    )


def _instantiate_animation_row(
    target: AnimationTarget,
    node_type: str,
    row_id: int,
    first_behavior_id: int,
) -> tuple[str, int]:
    """Instantiate one PowerPoint-authored preset row for a generated shape."""
    animation = target.effect
    shape_id = target.shape_id
    duration_ms = target.duration_ms
    spec = NATIVE_ANIMATIONS[animation]
    row = _animation_row_for_options(animation, target.effect_options)
    row.set('id', str(row_id))
    row.set('nodeType', node_type)
    conditions = row.find(_qn(PML_NS, 'stCondLst'))
    if conditions is None:
        raise RuntimeError(f'animation preset {animation!r} lost p:stCondLst')
    direct_conditions = conditions.findall(_qn(PML_NS, 'cond'))
    if len(direct_conditions) != 1:
        raise RuntimeError(
            f'animation preset {animation!r} must have one start condition'
        )
    direct_conditions[0].attrib.clear()
    direct_conditions[0].set(
        'delay',
        str(
            target.delay_ms
            if (
                node_type == 'afterEffect'
                or (
                    node_type == 'clickEffect'
                    and target.trigger_shape_id is not None
                )
            )
            else 0
        ),
    )

    if spec['durationScalable']:
        base_duration_ms = int(spec['defaultDurationMs'])
        _scale_animation_row_duration(
            row,
            base_duration_ms=base_duration_ms,
            requested_duration_ms=duration_ms,
        )

    _apply_timing_options(row, target)
    _append_after_effect(row, target, row_id)
    _append_animation_sound(row, target)

    next_id = first_behavior_id
    for ctn in row.iter(_qn(PML_NS, 'cTn')):
        if ctn is row:
            continue
        ctn.set('id', str(next_id))
        next_id += 1
    for target in row.iter(_qn(PML_NS, 'spTgt')):
        target.set('spid', str(shape_id))
    return ET.tostring(row, encoding='unicode'), next_id


def _build_animation_row_xml(
    target: AnimationTarget,
    trigger: str,
    row_id: int,
    first_behavior_id: int,
) -> tuple[str, int]:
    """Build one canonical PowerPoint-authored animation-pane row."""
    node_type = _TRIGGER_NODE_TYPES[trigger]
    return _instantiate_animation_row(
        target,
        node_type,
        row_id,
        first_behavior_id,
    )


def create_sequence_timing_xml(
    targets: list,
    duration: float = 0.3,
    trigger: str = 'after-previous',
) -> str:
    """Generate a multi-target object-animation sequence.

    Args:
        targets: list of (shape_id, delay_ms, animation_name) or
            (shape_id, delay_ms, animation_name, duration_seconds) tuples, in
            the order they should play. ``delay_ms`` is the gap before
            this element starts in ``after-previous`` mode. For a mapping
            target with ``trigger_shape_id``, it is the delay after that
            shape is clicked; otherwise the other Start modes ignore it.
        duration: per-element animation duration in seconds. Instantaneous
            native presets retain their PowerPoint-authored duration.
        trigger: PowerPoint-standard Start mode for each element.
            ``'after-previous'`` — first element fires on slide entry,
            rest chain after the previous one with ``delay_ms`` spacing
            (default).
            ``'on-click'`` — one presenter click per element.
            ``'with-previous'`` — all elements start together on slide
            entry.

    Returns:
        A ``<p:timing>`` element string. Returns an empty string when
        ``targets`` is empty.
    """
    trigger = normalize_animation_trigger(trigger)
    default_dur_ms = _seconds_to_ms(
        duration,
        'animation duration',
        allow_zero=False,
    )
    if targets is None or isinstance(targets, (str, bytes)):
        raise ValueError('animation targets must be a sequence of target tuples')
    if not targets:
        return ''
    normalized_targets = [
        _normalize_target(target, default_dur_ms)
        for target in targets
    ]
    shape_ids = [target.shape_id for target in normalized_targets]
    if len(shape_ids) != len(set(shape_ids)):
        raise ValueError('animation targets must not contain duplicate shape ids')
    next_id = 3
    main_targets = [
        target
        for target in normalized_targets
        if target.trigger_shape_id is None
    ]
    interactive_targets = [
        target
        for target in normalized_targets
        if target.trigger_shape_id is not None
    ]

    if trigger == 'on-click':
        # Each element is an independent click-driven par directly under
        # mainSeq. Three-level nesting per element: outer cTn holds for
        # the click via delay="indefinite", innermost cTn owns the
        # clickEffect + animation children. Each click advances the seq.
        steps = []
        for target in main_targets:
            wrapper_id = next_id
            inner_id = next_id + 1
            leaf_id = next_id + 2
            row_xml, next_id = _build_animation_row_xml(
                target,
                trigger,
                leaf_id,
                next_id + 3,
            )
            steps.append(f'''<p:par>
  <p:cTn id="{wrapper_id}" fill="hold">
    <p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>
    <p:childTnLst>
      <p:par>
        <p:cTn id="{inner_id}" fill="hold">
          <p:stCondLst><p:cond delay="0"/></p:stCondLst>
          <p:childTnLst>
            <p:par>
              {row_xml}
            </p:par>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:childTnLst>
  </p:cTn>
</p:par>''')
        all_steps = '\n              '.join(steps)
    else:
        # with-previous / after-previous: wrap the entire cascade in ONE
        # par so the sequence has a real trigger anchor under mainSeq.
        #
        # Native PowerPoint after-previous export uses two timing layers:
        # each row owns its TriggerDelayTime, while its wrapper owns the
        # previous row's absolute end. Their sum is the absolute start offset.
        outer_id = next_id
        next_id += 1
        inner_steps = []
        with_wrapper_id = None
        if trigger == 'with-previous':
            with_wrapper_id = next_id
            next_id += 1
        elapsed_ms = 0
        for target_index, target in enumerate(main_targets, 1):
            if trigger == 'with-previous':
                leaf_id = next_id
                row_xml, next_id = _build_animation_row_xml(
                    target,
                    trigger,
                    leaf_id,
                    next_id + 1,
                )
                inner_steps.append(f'''<p:par>
                  {row_xml}
                </p:par>''')
            else:
                if elapsed_ms > MAX_OOXML_MILLISECONDS:
                    raise ValueError(
                        'animation sequence offset exceeds the OOXML '
                        f'millisecond limit at target {target_index}: {elapsed_ms}'
                    )
                wrapper_id = next_id
                leaf_id = next_id + 1
                row_xml, next_id = _build_animation_row_xml(
                    target,
                    trigger,
                    leaf_id,
                    next_id + 2,
                )
                inner_steps.append(f'''<p:par>
                  <p:cTn id="{wrapper_id}" fill="hold">
                    <p:stCondLst><p:cond delay="{elapsed_ms}"/></p:stCondLst>
                    <p:childTnLst>
                      <p:par>
                        {row_xml}
                      </p:par>
                    </p:childTnLst>
                  </p:cTn>
                </p:par>''')
                elapsed_ms += target.delay_ms + target.playback_duration_ms

        inner_xml = '\n                '.join(inner_steps)
        if trigger == 'with-previous':
            # Match PowerPoint's native "Start: With Previous" export:
            # one delay=0 wrapper begins on slide entry, and all withEffect
            # rows live under that wrapper so they truly start in parallel.
            inner_xml = f'''<p:par>
                      <p:cTn id="{with_wrapper_id}" fill="hold">
                        <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                        <p:childTnLst>
                          {inner_xml}
                        </p:childTnLst>
                      </p:cTn>
                    </p:par>'''
        if trigger in ('with-previous', 'after-previous'):
            # Match PowerPoint's native slide-entry export: the wrapper waits
            # for mainSeq to begin, then child nodes resolve their Start modes.
            outer_start_conditions = (
                '<p:cond delay="indefinite"/>'
                '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>'
            )
        else:
            outer_start_conditions = '<p:cond delay="0"/>'
        all_steps = f'''<p:par>
                <p:cTn id="{outer_id}" fill="hold">
                  <p:stCondLst>{outer_start_conditions}</p:stCondLst>
                  <p:childTnLst>
                    {inner_xml}
                  </p:childTnLst>
                </p:cTn>
              </p:par>'''

    if main_targets:
        main_sequence_xml = f'''<p:seq concurrent="1" nextAc="seek">
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
              {all_steps}
                </p:childTnLst>
              </p:cTn>
              <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
              <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
            </p:seq>'''
    else:
        main_sequence_xml = ''
        next_id = 2

    interactive_sequences: list[str] = []
    for target in interactive_targets:
        sequence_id = next_id
        wrapper_id = next_id + 1
        inner_id = next_id + 2
        row_id = next_id + 3
        row_xml, next_id = _build_animation_row_xml(
            target,
            'on-click',
            row_id,
            next_id + 4,
        )
        trigger_shape_id = target.trigger_shape_id
        interactive_sequences.append(f'''<p:seq concurrent="1" nextAc="seek">
              <p:cTn id="{sequence_id}" restart="whenNotActive" fill="hold" evtFilter="cancelBubble" nodeType="interactiveSeq">
                <p:stCondLst><p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="{trigger_shape_id}"/></p:tgtEl></p:cond></p:stCondLst>
                <p:endSync evt="end" delay="0"><p:rtn val="all"/></p:endSync>
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="{wrapper_id}" fill="hold">
                      <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="{inner_id}" fill="hold">
                            <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                            <p:childTnLst><p:par>{row_xml}</p:par></p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
              <p:nextCondLst><p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="{trigger_shape_id}"/></p:tgtEl></p:cond></p:nextCondLst>
            </p:seq>''')
    sequence_xml = '\n            '.join(
        [
            value
            for value in (
                main_sequence_xml,
                *interactive_sequences,
            )
            if value
        ]
    )

    timing_xml = f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
          <p:childTnLst>
            {sequence_xml}
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>'''
    if not any(target.bounce_end for target in normalized_targets):
        return timing_xml

    fallback_xml = re.sub(
        r'\s+p14:(?:presetBounceEnd|bounceEnd)="\d+"',
        '',
        timing_xml,
    )
    fallback_xml = fallback_xml.replace(
        f' xmlns:p14="{_P14_NS}"',
        '',
    )
    return f'''  <mc:AlternateContent xmlns:mc="{_MC_NS}">
    <mc:Choice xmlns:p14="{_P14_NS}" Requires="p14">
      {timing_xml}
    </mc:Choice>
    <mc:Fallback>
      {fallback_xml}
    </mc:Fallback>
  </mc:AlternateContent>'''


def pick_animation_effect(
    mode: str,
    idx: int,
    offset: int = 0,
    group_id: str | None = None,
    *,
    rng: random.Random | None = None,
) -> str:
    """Resolve a per-element effect name from a mode string.

    - A specific animation name returns itself (no variation).
    - 'auto': map ``group_id`` to an effect. Image-like ids
      (hero / figure- / image / img- / kpi) cycle through ``_IMAGE_POOL``
      (``entrance_zoom`` / ``entrance_dissolve`` / ``entrance_circle`` /
      ``entrance_box`` / ``entrance_diamond`` / ``entrance_wheel``) by
      ``idx + offset``
      so multiple images vary across the deck. Other semantic matches in
      ``_SEMANTIC_PATTERNS`` return a single stable effect
      (chart→``entrance_wipe``, card-/step-/pillar-→``entrance_fly``,
      title/takeaway→``entrance_fade``). When the id matches no pattern, cycle
      through ``_AUTO_POOL``.
    - 'mixed' (compatible mode name): first element fixed to
      ``entrance_fade``; the rest cycle through ``_MIXED_POOL`` plus
      ``offset`` so titles stay calm while content varies across slides.
    - 'random': uniform seeded choice from the same canonical preset pool.
    Unknown modes fail explicitly; no effect is silently substituted.
    """
    mode = normalize_animation_effect(
        mode,
        allow_none=False,
        allow_modes=True,
    )
    if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
        raise ValueError(f'animation index must be a non-negative integer: {idx!r}')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError(
            f'animation offset must be a non-negative integer: {offset!r}'
        )
    if mode in NATIVE_ANIMATIONS:
        return mode
    if mode == 'auto':
        semantic = _semantic_effect(group_id, idx, offset)
        if semantic is not None:
            return semantic
        return _AUTO_POOL[(idx + offset) % len(_AUTO_POOL)]
    if mode == 'mixed':
        if idx == 0:
            return 'entrance_fade'
        return _MIXED_POOL[(idx - 1 + offset) % len(_MIXED_POOL)]
    if mode == 'random':
        chooser = rng if rng is not None else random
        return chooser.choice(_MIXED_POOL)
    raise AssertionError(f'unhandled animation mode: {mode}')


def _int_attribute(
    element: ET.Element,
    name: str,
    label: str,
    errors: list[str],
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int | None:
    value = element.get(name)
    if value is None or not re.fullmatch(r'\d+', value):
        errors.append(f'{label} must be an integer; found {value!r}')
        return None
    number = int(value)
    if number < minimum:
        errors.append(f'{label} must be at least {minimum}; found {number}')
        return None
    if maximum is not None and number > maximum:
        errors.append(f'{label} must be at most {maximum}; found {number}')
        return None
    return number


def _direct_conditions(ctn: ET.Element) -> list[ET.Element]:
    condition_list = ctn.find(_qn(PML_NS, 'stCondLst'))
    if condition_list is None:
        return []
    return [
        child for child in list(condition_list)
        if child.tag == _qn(PML_NS, 'cond')
    ]


def _shape_index(
    slide_root: ET.Element,
) -> tuple[dict[int, tuple[str, bool]], list[str]]:
    parent_map = {
        child: parent
        for parent in slide_root.iter()
        for child in list(parent)
    }
    index: dict[int, tuple[str, bool]] = {}
    errors: list[str] = []
    shape_tags = {'sp', 'grpSp', 'pic', 'graphicFrame', 'cxnSp', 'contentPart'}
    for non_visual in slide_root.iter(_qn(PML_NS, 'cNvPr')):
        shape_id = _int_attribute(
            non_visual,
            'id',
            'p:cNvPr@id',
            errors,
            minimum=1,
            maximum=MAX_OOXML_UNSIGNED_INT,
        )
        if shape_id is None:
            continue
        owner = parent_map.get(non_visual)
        while owner is not None and _local_name(owner.tag) not in shape_tags:
            owner = parent_map.get(owner)
        kind = _local_name(owner.tag) if owner is not None else 'unknown'
        has_text = bool(
            owner is not None
            and kind == 'sp'
            and any(
                _local_name(element.tag) == 't' and (element.text or '').strip()
                for element in owner.iter()
            )
        )
        if shape_id in index:
            errors.append(f'duplicate p:cNvPr@id {shape_id}')
        else:
            index[shape_id] = (kind, has_text)
    return index, errors


def _row_shape_id(row: ET.Element, errors: list[str]) -> int | None:
    shape_ids: list[int] = []
    for target in row.iter(_qn(PML_NS, 'spTgt')):
        value = _int_attribute(
            target,
            'spid',
            'animation p:spTgt@spid',
            errors,
            minimum=1,
            maximum=MAX_OOXML_UNSIGNED_INT,
        )
        if value is not None:
            shape_ids.append(value)
    unique = sorted(set(shape_ids))
    if len(unique) != 1:
        errors.append(
            'one object-animation row must resolve to exactly one shape id; '
            f'found {unique or "none"}'
        )
        return None
    return unique[0]


def _row_filter(
    row: ET.Element,
    preset_class: str,
    errors: list[str],
) -> str | None:
    effects = list(row.iter(_qn(PML_NS, 'animEffect')))
    if len(effects) > 1:
        errors.append(
            f'object-animation row contains {len(effects)} p:animEffect nodes'
        )
    if not effects:
        return None
    effect = effects[0]
    expected_transition = {'entr': 'in', 'exit': 'out'}.get(preset_class)
    if expected_transition is not None and effect.get('transition') != expected_transition:
        errors.append(
            f'{preset_class} p:animEffect must set '
            f'transition="{expected_transition}"'
        )
    return effect.get('filter')


def _resolve_row_effect(
    row: ET.Element,
    filter_name: str | None,
    errors: list[str],
) -> tuple[tuple[str, ...], str | None, int | None, int | None]:
    preset_class = row.get('presetClass')
    if preset_class not in set(_PRESET_CLASS_BY_CATEGORY.values()):
        errors.append(
            f'unsupported p:cTn@presetClass {preset_class!r}; expected '
            + ', '.join(sorted(set(_PRESET_CLASS_BY_CATEGORY.values())))
        )
        return (), preset_class, None, None
    preset_id = _int_attribute(
        row,
        'presetID',
        'object-animation p:cTn@presetID',
        errors,
        maximum=MAX_OOXML_UNSIGNED_INT,
    )
    preset_subtype = _int_attribute(
        row,
        'presetSubtype',
        'object-animation p:cTn@presetSubtype',
        errors,
        maximum=MAX_OOXML_UNSIGNED_INT,
    )
    if preset_id is None or preset_subtype is None:
        return (), preset_class, preset_id, preset_subtype
    matches = [
        key
        for key, info in NATIVE_ANIMATIONS.items()
        if info['presetClass'] == preset_class
        if int(info['presetID']) == preset_id
    ]
    return tuple(matches), preset_class, preset_id, preset_subtype


def _behavior_duration_ms(
    row: ET.Element,
    errors: list[str],
) -> int | None:
    duration = _row_effective_duration_ms(row)
    if duration is not None and duration > MAX_OOXML_MILLISECONDS:
        errors.append(
            'object-animation behavior duration exceeds the OOXML '
            f'millisecond limit: {duration}'
        )
    return duration


def _read_animation_color(
    row: ET.Element,
    errors: list[str],
    label: str,
) -> str | None:
    colors = [
        element
        for element in row.iter()
        if element.tag in {
            _qn(_DML_NS, 'srgbClr'),
            _qn(_DML_NS, 'schemeClr'),
        }
    ]
    if not colors:
        errors.append(f'{label} is missing its color value')
        return None
    rendered = []
    for color in colors:
        if color.tag == _qn(_DML_NS, 'srgbClr'):
            value = color.get('val')
            rendered.append(f'#{value.upper()}' if value else '')
        else:
            value = color.get('val')
            rendered.append(f'theme:{value}' if value else '')
    unique = tuple(dict.fromkeys(value for value in rendered if value))
    if len(unique) != 1:
        errors.append(f'{label} contains inconsistent color values: {unique!r}')
        return None
    return unique[0] if unique else None


def _read_effect_options(
    row: ET.Element,
    effect: str | None,
    filter_name: str | None,
    errors: list[str],
) -> dict[str, object]:
    if effect is None:
        return {}
    option_specs = NATIVE_ANIMATIONS[effect]['effectOptions']
    values: dict[str, object] = {}
    for name, spec in option_specs.items():
        option_type = spec['type']
        if option_type == 'enum':
            matches = []
            for value, variant_xml in spec['values'].items():
                variant = ET.fromstring(variant_xml)
                variant_filter = _row_filter(variant, variant.get('presetClass', ''), [])
                if variant.get('presetSubtype') != row.get('presetSubtype'):
                    continue
                if variant_filter != filter_name:
                    continue
                matches.append(value)
            if len(matches) != 1:
                errors.append(
                    f'animation effect {effect!r} option {name!r} could not be '
                    f'read from presetSubtype={row.get("presetSubtype")!r}, '
                    f'filter={filter_name!r}'
                )
                continue
            value: object = matches[0]
            if name == 'amount' and re.fullmatch(r'\d+', str(value)):
                value = int(str(value))
            values[name] = value
        elif name == 'amount' and effect == 'emphasis_spin':
            rotations = list(row.iter(_qn(PML_NS, 'animRot')))
            raw = rotations[0].get('by') if len(rotations) == 1 else None
            if raw is None or not re.fullmatch(r'-?\d+', raw):
                errors.append('emphasis_spin row has an invalid rotation amount')
            else:
                values[name] = int(raw) / 60000
        elif name == 'amount' and effect == 'emphasis_transparency':
            opacity_values = []
            for node in row.iter(_qn(PML_NS, 'set')):
                attributes = {
                    (attribute.text or '').strip()
                    for attribute in node.iter(_qn(PML_NS, 'attrName'))
                }
                if 'style.opacity' in attributes:
                    opacity_values.extend(
                        value.get('val')
                        for value in node.iter(_qn(PML_NS, 'strVal'))
                    )
            if len(opacity_values) != 1:
                errors.append('emphasis_transparency row has an invalid opacity')
            else:
                try:
                    values[name] = 1 - float(str(opacity_values[0]))
                except ValueError:
                    errors.append(
                        'emphasis_transparency row has a non-numeric opacity'
                    )
        elif name == 'color':
            color = _read_animation_color(
                row,
                errors,
                f'animation effect {effect!r} color option',
            )
            if color is not None:
                values[name] = color
        elif name == 'font_name':
            fonts = []
            for node in row.iter(_qn(PML_NS, 'set')):
                attributes = {
                    (attribute.text or '').strip()
                    for attribute in node.iter(_qn(PML_NS, 'attrName'))
                }
                if 'style.fontFamily' in attributes:
                    fonts.extend(
                        value.get('val')
                        for value in node.iter(_qn(PML_NS, 'strVal'))
                    )
            if len(fonts) != 1:
                errors.append(
                    'emphasis_change_font row must contain one font name'
                )
                continue
            try:
                values[name] = _normalize_powerpoint_font_name(
                    fonts[0],
                    'emphasis_change_font row font name',
                )
            except ValueError as exc:
                errors.append(str(exc))
        elif name == 'relative':
            motions = list(row.iter(_qn(PML_NS, 'animMotion')))
            if len(motions) != 1:
                errors.append(f'motion-path effect {effect!r} has no single path')
            else:
                values[name] = motions[0].get('pathEditMode') != 'fixed'
        elif name == 'size':
            scales = list(row.iter(_qn(PML_NS, 'animScale')))
            targets = (
                scales[0].findall(_qn(PML_NS, 'to'))
                if len(scales) == 1
                else []
            )
            raw = (
                targets[0].get('x')
                if len(targets) == 1
                else '100000' if not targets and len(scales) == 1 else None
            )
            if raw is None or not re.fullmatch(r'\d+', raw):
                errors.append('emphasis_grow_shrink row has an invalid size')
            else:
                values[name] = int(raw) / 1000
        else:
            errors.append(
                f'animation effect {effect!r} option {name!r} has no reader'
            )
    return values


def _timing_summary(
    row: ET.Element,
    duration_ms: int | None,
    errors: list[str],
) -> tuple[
    float | None,
    int | None,
    bool,
    bool,
    float,
    float,
    float,
    str,
    int | None,
]:
    raw_repeat_count = row.get('repeatCount')
    repeat_count = None
    if raw_repeat_count is not None:
        if not re.fullmatch(r'\d+', raw_repeat_count):
            errors.append(
                f'object-animation repeatCount must be numeric; found '
                f'{raw_repeat_count!r}'
            )
        else:
            repeat_count = int(raw_repeat_count) / 1000
    raw_repeat_duration = row.get('repeatDur')
    repeat_duration_ms = None
    if raw_repeat_duration is not None:
        if not re.fullmatch(r'\d+', raw_repeat_duration):
            errors.append(
                f'object-animation repeatDur must be numeric; found '
                f'{raw_repeat_duration!r}'
            )
        else:
            repeat_duration_ms = int(raw_repeat_duration)
    if repeat_count is not None and repeat_duration_ms is not None:
        errors.append('object-animation row sets both repeatCount and repeatDur')

    def ratio(attribute: str) -> float:
        raw = row.get(attribute)
        if raw is None:
            return 0.0
        if not re.fullmatch(r'\d+', raw):
            errors.append(
                f'object-animation {attribute} must be numeric; found {raw!r}'
            )
            return 0.0
        number = int(raw)
        if number > 100000:
            errors.append(
                f'object-animation {attribute} exceeds 100000; found {number}'
            )
        return number / 100000

    accelerate = ratio('accel')
    decelerate = ratio('decel')
    if accelerate + decelerate > 1:
        errors.append('object-animation accel + decel exceeds 100000')
    raw_bounce_values = {
        node.get(_qn(_P14_NS, 'bounceEnd'))
        for node in row.iter()
        if node.get(_qn(_P14_NS, 'bounceEnd')) is not None
    }
    preset_bounce = row.get(_qn(_P14_NS, 'presetBounceEnd'))
    if preset_bounce is not None:
        raw_bounce_values.add(preset_bounce)
    bounce_end = 0.0
    if len(raw_bounce_values) > 1:
        errors.append(
            'object-animation behaviors disagree on p14:bounceEnd'
        )
    elif raw_bounce_values:
        raw_bounce = next(iter(raw_bounce_values))
        if raw_bounce is None or not re.fullmatch(r'\d+', raw_bounce):
            errors.append(
                f'object-animation p14:bounceEnd must be numeric; '
                f'found {raw_bounce!r}'
            )
        else:
            bounce_value = int(raw_bounce)
            if bounce_value > 100000:
                errors.append(
                    'object-animation p14:bounceEnd exceeds 100000; '
                    f'found {bounce_value}'
                )
            bounce_end = bounce_value / 100000
    auto_reverse = row.get('autoRev') == '1'
    rewind = row.get('fill') == 'remove'
    restart = {
        None: 'never',
        'always': 'always',
        'whenNotActive': 'when-not-active',
        'never': 'never',
    }.get(row.get('restart'))
    if restart is None:
        errors.append(
            f'object-animation restart has unknown value: {row.get("restart")!r}'
        )
        restart = 'never'

    playback_duration_ms = None
    if duration_ms is not None:
        one_play = duration_ms * (2 if auto_reverse else 1)
        if repeat_duration_ms is not None:
            playback_duration_ms = repeat_duration_ms
        elif repeat_count is not None:
            playback_duration_ms = max(1, round(one_play * repeat_count))
        else:
            playback_duration_ms = one_play
    return (
        repeat_count,
        repeat_duration_ms,
        auto_reverse,
        rewind,
        accelerate,
        decelerate,
        bounce_end,
        restart,
        playback_duration_ms,
    )


def _after_effect_summary(
    row: ET.Element,
    errors: list[str],
) -> tuple[str, str | None]:
    sub_timing = row.find(_qn(PML_NS, 'subTnLst'))
    if sub_timing is None:
        return 'none', None
    after_nodes = [
        node
        for node in list(sub_timing)
        if any(
            ctn.get('afterEffect') == '1'
            for ctn in node.iter(_qn(PML_NS, 'cTn'))
        )
    ]
    if not after_nodes:
        return 'none', None
    if len(after_nodes) != 1:
        errors.append(
            f'object-animation row contains {len(after_nodes)} after effects'
        )
        return 'none', None
    node = after_nodes[0]
    if node.tag == _qn(PML_NS, 'animClr'):
        return (
            'dim',
            _read_animation_color(node, errors, 'animation dim after effect'),
        )
    if node.tag == _qn(PML_NS, 'set'):
        ctns = list(node.iter(_qn(PML_NS, 'cTn')))
        master_relation = ctns[0].get('masterRel') if ctns else None
        if master_relation == 'sameClick':
            return 'hide', None
        if master_relation == 'nextClick':
            return 'hide-on-next-click', None
    errors.append('object-animation row contains an unknown after effect')
    return 'none', None


def _sound_summary(
    row: ET.Element,
    errors: list[str],
) -> tuple[str | None, str | None]:
    sounds = list(row.iter(_qn(PML_NS, 'sndTgt')))
    if not sounds:
        return None, None
    if len(sounds) != 1:
        errors.append(f'object-animation row contains {len(sounds)} sounds')
        return None, None
    relationship_id = sounds[0].get(_qn(_REL_NS, 'embed'))
    name = sounds[0].get('name')
    if relationship_id is None or name is None:
        errors.append('object-animation sound is missing relationship id or name')
    return relationship_id, name


def _row_trigger_shape_id(
    row: ET.Element,
    parent_map: Mapping[ET.Element, ET.Element],
    errors: list[str],
) -> int | None:
    current = parent_map.get(row)
    while current is not None:
        if (
            current.tag == _qn(PML_NS, 'cTn')
            and current.get('nodeType') == 'interactiveSeq'
        ):
            shape_targets = [
                target
                for condition in _direct_conditions(current)
                if condition.get('evt') == 'onClick'
                for target in condition.iter(_qn(PML_NS, 'spTgt'))
            ]
            if len(shape_targets) != 1:
                errors.append(
                    'interactive animation sequence must have one trigger shape'
                )
                return None
            return _int_attribute(
                shape_targets[0],
                'spid',
                'interactive animation trigger shape id',
                errors,
                minimum=1,
                maximum=MAX_OOXML_UNSIGNED_INT,
            )
        current = parent_map.get(current)
    return None


def _row_offset_ms(
    row: ET.Element,
    trigger: str,
    trigger_shape_id: int | None,
    parent_map: Mapping[ET.Element, ET.Element],
    errors: list[str],
) -> int:
    leaf_conditions = _direct_conditions(row)
    leaf_delay = None
    if (
        len(leaf_conditions) == 1
        and re.fullmatch(r'\d+', leaf_conditions[0].get('delay') or '')
    ):
        leaf_delay = int(leaf_conditions[0].get('delay', '0'))
    else:
        errors.append(
            'object-animation row must have one numeric leaf start condition'
        )
    if (
        trigger != 'after-previous'
        and trigger_shape_id is None
        and leaf_delay not in {None, 0}
    ):
        errors.append(
            f'{trigger} object-animation row must have leaf delay="0"'
        )

    current = parent_map.get(row)
    saw_indefinite = False
    saw_main_begin = False
    numeric_offset: int | None = None
    while current is not None:
        if current.tag == _qn(PML_NS, 'cTn'):
            conditions = _direct_conditions(current)
            if any(condition.get('delay') == 'indefinite' for condition in conditions):
                saw_indefinite = True
            if any(
                condition.get('evt') == 'onBegin'
                and condition.get('delay') == '0'
                and any(
                    target.get('val') == '2'
                    for target in condition.iter(_qn(PML_NS, 'tn'))
                )
                for condition in conditions
            ):
                saw_main_begin = True
            if trigger in {'with-previous', 'after-previous'}:
                numeric = [
                    condition.get('delay')
                    for condition in conditions
                    if condition.get('evt') is None
                    and re.fullmatch(r'\d+', condition.get('delay') or '')
                ]
                if numeric and numeric_offset is None:
                    numeric_offset = int(numeric[0])
                    if numeric_offset > MAX_OOXML_MILLISECONDS:
                        errors.append(
                            'animation row offset exceeds the OOXML '
                            f'millisecond limit: {numeric_offset}'
                        )
        current = parent_map.get(current)

    if (
        trigger == 'on-click'
        and trigger_shape_id is None
        and not saw_indefinite
    ):
        errors.append(
            'on-click object-animation row is missing an indefinite click wrapper'
        )
    if trigger in {'with-previous', 'after-previous'} and not (
        saw_indefinite and saw_main_begin
    ):
        errors.append(f'{trigger} sequence is missing the slide-entry onBegin anchor')
    if trigger == 'after-previous' and numeric_offset is None:
        errors.append(
            'after-previous object-animation row is missing its numeric offset wrapper'
        )
    if trigger == 'after-previous':
        absolute_offset = (numeric_offset or 0) + (leaf_delay or 0)
        if absolute_offset > MAX_OOXML_MILLISECONDS:
            errors.append(
                'animation row absolute offset exceeds the OOXML '
                f'millisecond limit: {absolute_offset}'
            )
        return absolute_offset
    if trigger_shape_id is not None:
        return leaf_delay or 0
    return 0


def _animation_rows(
    slide_root: ET.Element,
    errors: list[str],
) -> list[AnimationRowSummary]:
    parent_map = {
        child: parent
        for parent in slide_root.iter()
        for child in list(parent)
    }
    rows: list[AnimationRowSummary] = []
    for row in slide_root.iter(_qn(PML_NS, 'cTn')):
        preset_class = row.get('presetClass')
        if preset_class not in set(_PRESET_CLASS_BY_CATEGORY.values()):
            continue
        node_type = row.get('nodeType')
        trigger = _NODE_TYPE_TRIGGERS.get(node_type or '')
        if trigger is None:
            errors.append(
                f'unsupported object-animation nodeType {node_type!r}; expected '
                f'{", ".join(_NODE_TYPE_TRIGGERS)}'
            )
            continue
        shape_id = _row_shape_id(row, errors)
        filter_name = _row_filter(row, preset_class, errors)
        supported_effects, resolved_class, preset_id, preset_subtype = (
            _resolve_row_effect(
            row,
            filter_name,
            errors,
        )
        )
        duration_ms = _behavior_duration_ms(row, errors)
        trigger_shape_id = _row_trigger_shape_id(row, parent_map, errors)
        offset_ms = _row_offset_ms(
            row,
            trigger,
            trigger_shape_id,
            parent_map,
            errors,
        )
        resolved_effect = supported_effects[0] if supported_effects else None
        effect_options = _read_effect_options(
            row,
            resolved_effect,
            filter_name,
            errors,
        )
        (
            repeat_count,
            repeat_duration_ms,
            auto_reverse,
            rewind,
            accelerate,
            decelerate,
            bounce_end,
            restart,
            playback_duration_ms,
        ) = _timing_summary(row, duration_ms, errors)
        after_effect, after_effect_color = _after_effect_summary(row, errors)
        sound_relationship_id, sound_name = _sound_summary(row, errors)
        if (
            shape_id is None
            or resolved_class is None
            or preset_id is None
            or preset_subtype is None
        ):
            continue
        rows.append(
            AnimationRowSummary(
                shape_id=shape_id,
                effect=resolved_effect,
                supported_effects=supported_effects,
                preset_class=resolved_class,
                trigger=trigger,
                duration_ms=duration_ms,
                offset_ms=offset_ms,
                preset_id=preset_id,
                preset_subtype=preset_subtype,
                filter_name=filter_name,
                effect_options=effect_options,
                trigger_shape_id=trigger_shape_id,
                repeat_count=repeat_count,
                repeat_duration_ms=repeat_duration_ms,
                auto_reverse=auto_reverse,
                rewind=rewind,
                accelerate=accelerate,
                decelerate=decelerate,
                bounce_end=bounce_end,
                restart=restart,
                after_effect=after_effect,
                after_effect_color=after_effect_color,
                sound_relationship_id=sound_relationship_id,
                sound_name=sound_name,
                playback_duration_ms=playback_duration_ms,
            )
        )
    return rows


def _select_supported_timing_branch(slide_root: ET.Element) -> ET.Element:
    """Project p14 AlternateContent timing onto one effective slide tree."""
    projected = copy.deepcopy(slide_root)
    alternate_tag = _qn(_MC_NS, 'AlternateContent')
    choice_tag = _qn(_MC_NS, 'Choice')
    fallback_tag = _qn(_MC_NS, 'Fallback')
    for index, child in list(enumerate(list(projected))):
        if child.tag != alternate_tag:
            continue
        branches = [
            branch
            for branch in list(child)
            if branch.tag in {choice_tag, fallback_tag}
        ]
        selected_timing = None
        for branch in branches:
            if (
                branch.tag == choice_tag
                and 'p14' in (branch.get('Requires') or '').split()
            ):
                selected_timing = branch.find(_qn(PML_NS, 'timing'))
                if selected_timing is not None:
                    break
        if selected_timing is None:
            for branch in branches:
                selected_timing = branch.find(_qn(PML_NS, 'timing'))
                if selected_timing is not None:
                    break
        if selected_timing is None:
            continue
        projected.remove(child)
        projected.insert(index, copy.deepcopy(selected_timing))
    return projected


def validate_slide_animation_structure(
    slide_root: ET.Element,
    *,
    require_supported_effects: bool = False,
) -> list[str]:
    """Return root timing, target, and generated-object structure errors."""
    errors: list[str] = []
    if slide_root.tag != _qn(PML_NS, 'sld'):
        return ['animation validation requires a PresentationML p:sld root']
    slide_root = _select_supported_timing_branch(slide_root)

    direct_timings = [
        child for child in list(slide_root)
        if child.tag == _qn(PML_NS, 'timing')
    ]
    all_timings = list(slide_root.iter(_qn(PML_NS, 'timing')))
    nested_count = len(all_timings) - len(direct_timings)
    if nested_count:
        errors.append(
            f'slide contains {nested_count} nested p:timing element(s); '
            'timing must be a direct child of p:sld'
        )
    if len(direct_timings) > 1:
        errors.append(
            f'slide has {len(direct_timings)} root p:timing elements; expected at most 1'
        )
    if not direct_timings:
        return errors

    timing = direct_timings[0]
    root_children = list(slide_root)
    timing_index = root_children.index(timing)
    for required_before in ('cSld', 'clrMapOvr', 'transition'):
        sibling = next(
            (
                child for child in root_children
                if child.tag == _qn(PML_NS, required_before)
            ),
            None,
        )
        if sibling is not None and root_children.index(sibling) > timing_index:
            errors.append(f'p:{required_before} must precede p:timing')
    extension_list = next(
        (
            child for child in root_children
            if child.tag == _qn(PML_NS, 'extLst')
        ),
        None,
    )
    if extension_list is not None and root_children.index(extension_list) < timing_index:
        errors.append('root p:extLst must follow p:timing')

    timing_children = list(timing)
    timing_name_order = [_local_name(child.tag) for child in timing_children]
    if 'bldLst' in timing_name_order and 'tnLst' in timing_name_order:
        if timing_name_order.index('bldLst') < timing_name_order.index('tnLst'):
            errors.append('p:tnLst must precede p:bldLst')

    parent_map = {
        child: parent
        for parent in timing.iter()
        for child in list(parent)
    }
    ctn_ids: list[int] = []
    for ctn in timing.iter(_qn(PML_NS, 'cTn')):
        if ctn.get('id') is None:
            ancestor = parent_map.get(ctn)
            while ancestor is not None and ancestor is not timing:
                if ancestor.tag == _qn(PML_NS, 'subTnLst'):
                    break
                ancestor = parent_map.get(ancestor)
            if (
                ancestor is not None
                and ancestor.tag == _qn(PML_NS, 'subTnLst')
            ):
                continue
        value = _int_attribute(
            ctn,
            'id',
            'p:cTn@id',
            errors,
            maximum=MAX_OOXML_UNSIGNED_INT,
        )
        if value is not None:
            ctn_ids.append(value)
    duplicates = sorted(
        value for value in set(ctn_ids) if ctn_ids.count(value) > 1
    )
    if duplicates:
        errors.append(
            'duplicate p:cTn@id values: ' + ', '.join(map(str, duplicates))
        )

    roots = [
        node for node in timing.iter(_qn(PML_NS, 'cTn'))
        if node.get('nodeType') == 'tmRoot'
    ]
    if len(roots) != 1:
        errors.append(
            f'p:timing must contain exactly one tmRoot time node; found {len(roots)}'
        )

    shape_index, shape_errors = _shape_index(slide_root)
    errors.extend(shape_errors)
    for target in timing.iter(_qn(PML_NS, 'spTgt')):
        shape_id = _int_attribute(
            target,
            'spid',
            'p:spTgt@spid',
            errors,
            minimum=1,
            maximum=MAX_OOXML_UNSIGNED_INT,
        )
        if shape_id is not None and shape_id not in shape_index:
            errors.append(f'p:spTgt references missing shape id {shape_id}')

    build_keys: list[tuple[int, int]] = []
    for build in timing.iter(_qn(PML_NS, 'bldP')):
        shape_id = _int_attribute(
            build,
            'spid',
            'p:bldP@spid',
            errors,
            minimum=1,
            maximum=MAX_OOXML_UNSIGNED_INT,
        )
        group_id = _int_attribute(
            build,
            'grpId',
            'p:bldP@grpId',
            errors,
            maximum=MAX_OOXML_UNSIGNED_INT,
        )
        if shape_id is None or group_id is None:
            continue
        build_keys.append((shape_id, group_id))
        kind, has_text = shape_index.get(shape_id, ('missing', False))
        if kind == 'missing':
            errors.append(f'p:bldP references missing shape id {shape_id}')
        elif require_supported_effects and (kind != 'sp' or not has_text):
            errors.append(
                f'p:bldP shape id {shape_id} must reference a text-bearing p:sp; '
                f'found {kind}'
            )
    if len(build_keys) != len(set(build_keys)):
        errors.append('p:bldP (spid, grpId) pairs must be unique')

    animation_nodes = [
        node for node in timing.iter(_qn(PML_NS, 'cTn'))
        if node.get('presetClass') in set(_PRESET_CLASS_BY_CATEGORY.values())
    ]
    if require_supported_effects:
        rows = _animation_rows(slide_root, errors)
        if not rows and animation_nodes:
            errors.append('generated object-animation rows could not be read back')
    else:
        rows = []
    if rows:
        regular_rows = [
            row for row in rows if row.trigger_shape_id is None
        ]
        interactive_rows = [
            row for row in rows if row.trigger_shape_id is not None
        ]
        main_sequences = [
            node for node in timing.iter(_qn(PML_NS, 'cTn'))
            if node.get('nodeType') == 'mainSeq'
        ]
        expected_main_sequences = 1 if regular_rows else 0
        if len(main_sequences) != expected_main_sequences:
            errors.append(
                'generated object-animation rows require '
                f'{expected_main_sequences} mainSeq time node(s); found '
                f'{len(main_sequences)}'
            )
        interactive_sequences = [
            node for node in timing.iter(_qn(PML_NS, 'cTn'))
            if node.get('nodeType') == 'interactiveSeq'
        ]
        if len(interactive_sequences) != len(interactive_rows):
            errors.append(
                'each generated trigger-shape animation must have one '
                'interactiveSeq time node'
            )
        regular_triggers = {row.trigger for row in regular_rows}
        if len(regular_triggers) > 1:
            errors.append(
                'one generated main object-animation sequence must use one '
                'Start mode; found '
                + ', '.join(sorted(regular_triggers))
            )
        row_shape_ids = [row.shape_id for row in rows]
        if len(row_shape_ids) != len(set(row_shape_ids)):
            errors.append('generated object-animation sequence repeats a shape target')
        for row in rows:
            if (
                row.trigger_shape_id is not None
                and row.trigger != 'on-click'
            ):
                errors.append(
                    'trigger-shape animation must use the on-click Start mode '
                    f'for shape {row.shape_id}'
                )
            if row.trigger_shape_id == row.shape_id:
                errors.append(
                    'animation target and trigger shape must differ for shape '
                    f'{row.shape_id}'
                )
            if not row.supported_effects:
                errors.append(
                    'unsupported object-animation effect tuple for shape '
                    f'{row.shape_id}: presetClass={row.preset_class}, '
                    f'presetID={row.preset_id}, '
                    f'presetSubtype={row.preset_subtype}, '
                    f'filter={row.filter_name!r}'
                )
    return errors


def read_slide_animation_sequence(
    slide_xml: str | bytes,
    *,
    require_supported_effects: bool = False,
) -> AnimationSequenceSummary:
    """Read and validate the logical object-animation sequence from slide XML."""
    data = slide_xml.encode('utf-8') if isinstance(slide_xml, str) else slide_xml
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f'invalid slide XML: {exc}') from exc
    root = _select_supported_timing_branch(root)
    errors = validate_slide_animation_structure(
        root,
        require_supported_effects=require_supported_effects,
    )
    row_errors: list[str] = []
    rows = _animation_rows(root, row_errors)
    for error in row_errors:
        if error not in errors:
            errors.append(error)
    if errors:
        raise ValueError('; '.join(errors))
    direct_timings = [
        child for child in list(root)
        if child.tag == _qn(PML_NS, 'timing')
    ]
    audio_targets: list[int] = []
    for audio in root.iter(_qn(PML_NS, 'audio')):
        for target in audio.iter(_qn(PML_NS, 'spTgt')):
            value = target.get('spid')
            if value and value.isdigit():
                audio_targets.append(int(value))
    regular_triggers = {
        row.trigger for row in rows if row.trigger_shape_id is None
    }
    trigger = (
        next(iter(regular_triggers))
        if len(regular_triggers) == 1
        else ('on-click' if rows and not regular_triggers else None)
    )
    return AnimationSequenceSummary(
        timing_count=len(direct_timings),
        trigger=trigger,
        rows=tuple(rows),
        audio_target_ids=tuple(audio_targets),
    )


def validate_generated_animation_xml(
    slide_xml: str | bytes,
    targets: Sequence[Sequence[object] | Mapping[str, object]],
    *,
    duration: float = 0.3,
    trigger: str = 'after-previous',
) -> AnimationSequenceSummary:
    """Read back one generated sequence and require exact requested semantics."""
    trigger = normalize_animation_trigger(trigger)
    default_duration_ms = _seconds_to_ms(
        duration,
        'animation duration',
        allow_zero=False,
    )
    normalized_expected = tuple(
        _normalize_target(target, default_duration_ms)
        for target in targets
    )
    # PowerPoint stores ordinary rows in mainSeq and shape-triggered rows in
    # separate interactiveSeq containers. Their relative cross-sequence order
    # has no playback meaning, so read-back follows the native container order.
    expected = tuple(
        target
        for target in normalized_expected
        if target.trigger_shape_id is None
    ) + tuple(
        target
        for target in normalized_expected
        if target.trigger_shape_id is not None
    )
    summary = read_slide_animation_sequence(
        slide_xml,
        require_supported_effects=True,
    )
    errors: list[str] = []
    if len(summary.rows) != len(expected):
        errors.append(
            f'animation read-back row count is {len(summary.rows)}; '
            f'expected {len(expected)}'
        )
    expected_main_targets = tuple(
        target for target in expected if target.trigger_shape_id is None
    )
    expected_sequence_trigger = (
        trigger if expected_main_targets else ('on-click' if expected else None)
    )
    if expected and summary.trigger != expected_sequence_trigger:
        errors.append(
            f'animation read-back trigger is {summary.trigger!r}; '
            f'expected {expected_sequence_trigger!r}'
        )

    expected_offsets: list[int] = []
    elapsed_ms = 0
    previous_duration_ms = 0
    main_index = 0
    for index, target in enumerate(expected):
        if target.trigger_shape_id is not None:
            expected_offsets.append(target.delay_ms)
        elif trigger == 'after-previous':
            if main_index == 0:
                elapsed_ms = target.delay_ms
            else:
                elapsed_ms += previous_duration_ms + target.delay_ms
            if elapsed_ms > MAX_OOXML_MILLISECONDS:
                errors.append(
                    'requested animation sequence offset exceeds the OOXML '
                    f'millisecond limit at row {index + 1}: {elapsed_ms}'
                )
            expected_offsets.append(elapsed_ms)
            previous_duration_ms = target.playback_duration_ms
            main_index += 1
        else:
            expected_offsets.append(0)

    for index, (actual, target) in enumerate(zip(summary.rows, expected), 1):
        spec = NATIVE_ANIMATIONS[target.effect]
        expected_row = _animation_row_for_options(
            target.effect,
            target.effect_options,
        )
        if spec['durationScalable']:
            _scale_animation_row_duration(
                expected_row,
                base_duration_ms=int(spec['defaultDurationMs']),
                requested_duration_ms=target.duration_ms,
            )
        _apply_timing_options(expected_row, target)
        option_errors: list[str] = []
        expected_filter = _row_filter(
            expected_row,
            str(spec['presetClass']),
            option_errors,
        )
        expected_options = _read_effect_options(
            expected_row,
            target.effect,
            expected_filter,
            option_errors,
        )
        (
            expected_repeat_count,
            expected_repeat_duration_ms,
            expected_auto_reverse,
            expected_rewind,
            expected_accelerate,
            expected_decelerate,
            expected_bounce_end,
            expected_restart,
            expected_playback_duration_ms,
        ) = _timing_summary(
            expected_row,
            (
                target.duration_ms
                if spec['durationScalable']
                else spec['defaultDurationMs']
            ),
            option_errors,
        )
        if option_errors:
            errors.append(
                f'animation row {index} expected-option model failed: '
                + '; '.join(option_errors)
            )
        if actual.shape_id != target.shape_id:
            errors.append(
                f'animation row {index} targets shape {actual.shape_id}; '
                f'expected {target.shape_id}'
            )
        expected_row_trigger = (
            'on-click' if target.trigger_shape_id is not None else trigger
        )
        if actual.trigger != expected_row_trigger:
            errors.append(
                f'animation row {index} trigger is {actual.trigger!r}; '
                f'expected {expected_row_trigger!r}'
            )
        if actual.trigger_shape_id != target.trigger_shape_id:
            errors.append(
                f'animation row {index} trigger shape is '
                f'{actual.trigger_shape_id!r}; expected '
                f'{target.trigger_shape_id!r}'
            )
        if target.effect not in actual.supported_effects:
            errors.append(
                f'animation row {index} resolved effects '
                f'{actual.supported_effects!r}; expected {target.effect!r}'
            )
        if actual.preset_class != spec['presetClass']:
            errors.append(f'animation row {index} presetClass changed')
        if actual.preset_id != int(spec['presetID']):
            errors.append(f'animation row {index} presetID changed')
        if actual.preset_subtype != int(expected_row.get('presetSubtype', '-1')):
            errors.append(f'animation row {index} presetSubtype changed')
        if actual.filter_name != expected_filter:
            errors.append(f'animation row {index} filter changed')
        if dict(actual.effect_options) != expected_options:
            errors.append(
                f'animation row {index} effect_options are '
                f'{dict(actual.effect_options)!r}; expected {expected_options!r}'
            )
        expected_duration = (
            target.duration_ms
            if spec['durationScalable']
            else spec['defaultDurationMs']
        )
        if actual.duration_ms != expected_duration:
            errors.append(
                f'animation row {index} duration is {actual.duration_ms}ms; '
                f'expected {expected_duration}ms'
            )
        if actual.offset_ms != expected_offsets[index - 1]:
            errors.append(
                f'animation row {index} offset is {actual.offset_ms}ms; '
                f'expected {expected_offsets[index - 1]}ms'
            )
        timing_pairs = (
            ('repeat_count', actual.repeat_count, expected_repeat_count),
            (
                'repeat_duration_ms',
                actual.repeat_duration_ms,
                expected_repeat_duration_ms,
            ),
            ('auto_reverse', actual.auto_reverse, expected_auto_reverse),
            ('rewind', actual.rewind, expected_rewind),
            ('accelerate', actual.accelerate, expected_accelerate),
            ('decelerate', actual.decelerate, expected_decelerate),
            ('bounce_end', actual.bounce_end, expected_bounce_end),
            ('restart', actual.restart, expected_restart),
            (
                'playback_duration_ms',
                actual.playback_duration_ms,
                expected_playback_duration_ms,
            ),
        )
        for field, actual_value, expected_value in timing_pairs:
            if actual_value != expected_value:
                errors.append(
                    f'animation row {index} {field} is {actual_value!r}; '
                    f'expected {expected_value!r}'
                )
        if actual.after_effect != target.after_effect:
            errors.append(
                f'animation row {index} after_effect is '
                f'{actual.after_effect!r}; expected {target.after_effect!r}'
            )
        if actual.after_effect_color != target.after_effect_color:
            errors.append(
                f'animation row {index} after_effect_color is '
                f'{actual.after_effect_color!r}; '
                f'expected {target.after_effect_color!r}'
            )
        if actual.sound_relationship_id != target.sound_relationship_id:
            errors.append(
                f'animation row {index} sound relationship is '
                f'{actual.sound_relationship_id!r}; '
                f'expected {target.sound_relationship_id!r}'
            )
        if actual.sound_name != target.sound_name:
            errors.append(
                f'animation row {index} sound name is '
                f'{actual.sound_name!r}; expected {target.sound_name!r}'
            )
    if errors:
        raise ValueError('; '.join(errors))
    resolved_rows = tuple(
        replace(actual, effect=target.effect)
        for actual, target in zip(summary.rows, expected)
    )
    return replace(summary, rows=resolved_rows)


def validate_pptx_animation_package(
    pptx_path: str | Path,
    *,
    require_supported_effects: bool = False,
) -> None:
    """Validate timing placement and shape references for every slide part."""
    path = Path(pptx_path)
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as package:
            names = sorted(
                name
                for name in package.namelist()
                if re.fullmatch(r'ppt/slides/slide\d+\.xml', name)
            )
            for name in names:
                slide_data = package.read(name)
                try:
                    root = ET.fromstring(slide_data)
                except ET.ParseError as exc:
                    errors.append(f'{name}: invalid XML: {exc}')
                    continue
                for error in validate_slide_animation_structure(
                    root,
                    require_supported_effects=require_supported_effects,
                ):
                    errors.append(f'{name}: {error}')
                try:
                    summary = read_slide_animation_sequence(slide_data)
                except ValueError:
                    continue
                sound_ids = {
                    row.sound_relationship_id
                    for row in summary.rows
                    if row.sound_relationship_id is not None
                }
                if not sound_ids:
                    continue
                slide_leaf = posixpath.basename(name)
                rels_name = (
                    f'ppt/slides/_rels/{slide_leaf}.rels'
                )
                if rels_name not in package.namelist():
                    errors.append(
                        f'{name}: animation sound relationships are missing'
                    )
                    continue
                try:
                    relationships = ET.fromstring(package.read(rels_name))
                except ET.ParseError as exc:
                    errors.append(f'{rels_name}: invalid XML: {exc}')
                    continue
                by_id = {
                    rel.get('Id'): rel
                    for rel in relationships.findall(
                        _qn(_PACKAGE_REL_NS, 'Relationship')
                    )
                }
                for relationship_id in sorted(sound_ids):
                    relationship = by_id.get(relationship_id)
                    if relationship is None:
                        errors.append(
                            f'{name}: animation sound relationship '
                            f'{relationship_id} is missing'
                        )
                        continue
                    if relationship.get('Type') != _AUDIO_REL_TYPE:
                        errors.append(
                            f'{name}: animation sound relationship '
                            f'{relationship_id} is not an audio relationship'
                        )
                        continue
                    target = relationship.get('Target')
                    if not target:
                        errors.append(
                            f'{name}: animation sound relationship '
                            f'{relationship_id} has no target'
                        )
                        continue
                    target_part = posixpath.normpath(
                        posixpath.join(posixpath.dirname(name), target)
                    )
                    if target_part not in package.namelist():
                        errors.append(
                            f'{name}: animation sound target is missing: '
                            f'{target_part}'
                        )
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f'unable to read PPTX package {path}: {exc}') from exc
    if errors:
        raise ValueError('; '.join(errors))


def object_animation_fingerprint(slide_xml: str | bytes) -> str | None:
    """Return a prefix/whitespace-independent fingerprint of object animation.

    Narration audio is intentionally excluded.  Direct-PPTX routes use this
    fingerprint before and after their allowed edits to prove that they did not
    take ownership of or rewrite existing object animations.
    """
    data = slide_xml.encode('utf-8') if isinstance(slide_xml, str) else slide_xml
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f'invalid slide XML: {exc}') from exc
    root = _select_supported_timing_branch(root)
    timings = [
        child for child in list(root)
        if child.tag == _qn(PML_NS, 'timing')
    ]
    if len(timings) > 1:
        raise ValueError(
            f'slide has {len(timings)} root p:timing elements; expected at most 1'
        )
    if not timings:
        return None
    timing = timings[0]
    behavior_tags = {
        _qn(PML_NS, name)
        for name in (
            'anim',
            'animClr',
            'animEffect',
            'animMotion',
            'animRot',
            'animScale',
            'cmd',
            'set',
        )
    }
    has_object_animation = any(
        element.tag in behavior_tags
        or (
            element.tag == _qn(PML_NS, 'cTn')
            and element.get('presetClass') is not None
        )
        for element in timing.iter()
    )
    if not has_object_animation:
        return None

    def without_audio(element: ET.Element) -> tuple[object, ...] | None:
        if element.tag == _qn(PML_NS, 'audio'):
            return None
        children = tuple(
            value
            for child in list(element)
            if (value := without_audio(child)) is not None
        )
        return (
            element.tag,
            tuple(sorted(element.attrib.items())),
            (element.text or '').strip(),
            children,
        )

    canonical = without_audio(timing)
    return hashlib.sha256(repr(canonical).encode('utf-8')).hexdigest()


def entrance_animation_fingerprint(slide_xml: str | bytes) -> str | None:
    """Compatibility alias for :func:`object_animation_fingerprint`."""
    return object_animation_fingerprint(slide_xml)


def get_available_transitions() -> list:
    """Get native transition keys followed by compatibility inputs."""
    return [*NATIVE_TRANSITION_KEYS, *LEGACY_TRANSITION_KEYS]


def get_available_animations() -> list:
    """Get canonical object-animation keys followed by compatibility inputs."""
    return list(ANIMATIONS.keys())


def get_transition_help() -> str:
    """Get categorized native transitions plus legacy compatibility inputs."""
    lines = ["Available transition effects:"]
    for category in TRANSITION_CATEGORIES:
        lines.append(f"  PowerPoint-native {category} effects:")
        for key in NATIVE_TRANSITION_KEYS:
            info = NATIVE_TRANSITIONS[key]
            if info["category"] == category:
                lines.append(f"    {key}: {info['name']}")
    lines.append("  Legacy compatibility inputs (never selected for new output):")
    for key in LEGACY_TRANSITION_KEYS:
        canonical = TRANSITION_ALIASES[key]
        implied = TRANSITION_ALIAS_OPTIONS.get(key)
        option_suffix = f", implies {implied}" if implied else ""
        lines.append(
            f"    {key}: compatibility alias for {canonical} "
            f"({NATIVE_TRANSITIONS[canonical]['name']}{option_suffix})"
        )
    return '\n'.join(lines)


def get_animation_help() -> str:
    """Get categorized help text for every object-animation effect."""
    lines = ['Available object animations:']
    for category in ANIMATION_CATEGORIES:
        lines.append(f'  PowerPoint-native {category} effects:')
        for key in NATIVE_ANIMATION_KEYS:
            info = NATIVE_ANIMATIONS[key]
            if info['category'] == category:
                lines.append(f"    {key}: {info['name']}")
    lines.append('  Legacy compatibility inputs (never selected for new output):')
    for key in LEGACY_ANIMATION_KEYS:
        canonical = ANIMATION_ALIASES[key]
        implied = ANIMATION_ALIAS_OPTIONS.get(key)
        option_suffix = (
            f', implies {implied}'
            if implied
            else ''
        )
        lines.append(
            f"    {key}: compatibility alias for {canonical} "
            f"({NATIVE_ANIMATIONS[canonical]['name']}{option_suffix})"
        )
    return '\n'.join(lines)


def describe_animation_effect(effect: object) -> dict[str, Any]:
    """Return the author-facing option contract for one animation effect."""
    canonical = normalize_animation_effect(
        effect,
        allow_none=False,
        allow_modes=False,
    )
    assert canonical is not None
    implied_options = (
        dict(ANIMATION_ALIAS_OPTIONS.get(effect, {}))
        if isinstance(effect, str)
        else {}
    )
    option_contract: dict[str, Any] = {}
    for name, raw_spec in NATIVE_ANIMATIONS[canonical]['effectOptions'].items():
        spec = {
            key: value
            for key, value in raw_spec.items()
            if key != 'values'
        }
        if raw_spec.get('type') == 'enum':
            spec['values'] = list(raw_spec['values'])
        option_contract[name] = spec
    return {
        'input': effect,
        'effect': canonical,
        'compatibility_alias': (
            effect if isinstance(effect, str) and effect in ANIMATION_ALIASES else None
        ),
        'implied_effect_options': implied_options,
        'effect_options': option_contract,
        'timing': {
            'duration': 'positive seconds',
            'delay': 'non-negative seconds; group scope only',
            'stagger': 'non-negative seconds; animation scope only',
            'trigger': list(ANIMATION_TRIGGERS),
            'trigger_shape': (
                'other top-level SVG group id; group scope only; maps to '
                'PowerPoint "On Click of"'
            ),
            'repeat_count': 'positive number; mutually exclusive with repeat_duration',
            'repeat_duration': 'positive seconds; mutually exclusive with repeat_count',
            'auto_reverse': 'boolean',
            'rewind': 'boolean',
            'accelerate': 'number from 0 to 1',
            'decelerate': 'number from 0 to 1',
            'bounce_end': (
                'number from 0 to 1; requires an interpolated behavior and '
                'is mutually exclusive with decelerate'
            ),
            'restart': list(ANIMATION_RESTARTS),
        },
        'after_effect': list(ANIMATION_AFTER_EFFECTS),
        'sound': 'project-relative or absolute .m4a, .mp3, or .wav path',
        'derived_not_configured': {
            'speed': 'derived from duration',
            'smooth_start': 'derived from accelerate',
            'smooth_end': 'derived from decelerate',
        },
    }


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="print sample XML for a fade transition and entrance_fade animation",
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='list available transitions and object animations',
    )
    parser.add_argument(
        '--describe',
        metavar='EFFECT',
        help='print the complete parameter contract for one object animation',
    )
    parser.add_argument(
        '--describe-transition',
        metavar='EFFECT',
        help='print the PowerPoint Effect Options for one page transition',
    )
    args = parser.parse_args()

    if args.describe:
        try:
            print(
                json.dumps(
                    describe_animation_effect(args.describe),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        except ValueError as exc:
            parser.error(str(exc))
        return

    if args.describe_transition:
        try:
            print(
                json.dumps(
                    describe_transition_effect(args.describe_transition),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        except ValueError as exc:
            parser.error(str(exc))
        return

    if args.list:
        print(get_transition_help())
        print()
        print(get_animation_help())
        return

    if args.demo:
        print("=== Transition Effect XML Example (fade, 500ms) ===")
        print(create_transition_xml('fade', 0.5))
        print()
        print("=== Entrance Animation XML Example (entrance_fade) ===")
        print(create_timing_xml('entrance_fade', 1.0))
        return

    parser.print_help()


if __name__ == '__main__':
    main()
