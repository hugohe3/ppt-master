#!/usr/bin/env python3
"""
PPT Master - PPTX Animation Module

Provides one strict entrance-animation registry plus OOXML read/write helpers.

Supported transition effects:
    - fade: Fade in/out
    - push: Push
    - wipe: Wipe
    - split: Split
    - strips: Strips (diagonal wipe)
    - cover: Cover
    - random: Random

Supported entrance animations (per-element):
    appear, fade, fly, cut, zoom, wipe, split, blinds, checkerboard,
    dissolve, random_bars, peek, wheel, box, circle, diamond, plus,
    strips, wedge, stretch, expand, swivel

Animation modes used by the builder:
    - single effect name (one of the above) — apply to every element
    - 'auto'   — pick effect from the group's SVG id. Image-like ids
                 (hero / figure- / image / img- / kpi) cycle through a
                 visual pool (zoom / dissolve / circle / box / diamond /
                 wheel) so multiple images vary across the deck. Other
                 semantic matches map to a single stable effect
                 (chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade).
                 Unmatched ids cycle through a small modern pool
                 (fade / wipe / fly / zoom).
    - 'mixed'  — legacy mode: first element fades, the rest cycle through a
                 larger curated visible pool (kept for backward compatibility).
    - 'random' — pick a random effect from the legacy pool per element

Generated animation rows are validated against their requested effect, target,
duration, order, and Start mode before a PPTX is published.  Package validation
also checks timing-tree placement, time-node identifiers, and shape references.

See references/animations.md for the public workflow contract.

Dependencies: None (standard-library XML generation and validation)

Usage:
    python3 scripts/pptx_animations.py --demo
    python3 scripts/pptx_animations.py --list
"""

import argparse
import hashlib
import math
import random
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from pptx_transitions import (
    MAX_OOXML_MILLISECONDS,
    MAX_OOXML_UNSIGNED_INT,
    PML_NS,
    TRANSITIONS,
    create_transition_xml,
    validate_seconds,
)

configure_utf8_stdio()


# ============================================================================
# Entrance animation definitions
# ============================================================================

#
# 'filter' values must be valid PowerPoint <p:animEffect filter=".."/> strings
# (see ECMA-376 §19.5.10 ST_TLAnimateEffectTransition / filter dictionary).
# Effects with filter=None render as plain "Appear" (visibility flip only).
#
ANIMATIONS: dict[str, dict[str, Any]] = {
    'appear':   {'name': 'Appear',   'filter': None, 'presetID': 1, 'presetSubtype': 0},
    'fade':     {'name': 'Fade',     'filter': 'fade', 'presetID': 10, 'presetSubtype': 0},
    'fly':      {'name': 'Fly In',   'filter': 'slide(fromBottom)', 'presetID': 2, 'presetSubtype': 4},
    'cut':      {'name': 'Cut In',   'filter': 'slide(fromLeft)', 'presetID': 42, 'presetSubtype': 8},
    'zoom':     {'name': 'Zoom',     'filter': 'image', 'presetID': 23, 'presetSubtype': 0},
    'wipe':     {'name': 'Wipe',     'filter': 'wipe(left)', 'presetID': 22, 'presetSubtype': 1},
    'split':    {'name': 'Split',    'filter': 'barn(inVertical)', 'presetID': 16, 'presetSubtype': 21},
    'blinds':   {'name': 'Blinds',   'filter': 'blinds(horizontal)', 'presetID': 3, 'presetSubtype': 10},
    'checkerboard': {'name': 'Checkerboard', 'filter': 'checkerboard(across)', 'presetID': 5, 'presetSubtype': 6},
    'dissolve': {'name': 'Dissolve', 'filter': 'dissolve', 'presetID': 9, 'presetSubtype': 0},
    'random_bars': {'name': 'Random Bars', 'filter': 'randombar(horizontal)', 'presetID': 14, 'presetSubtype': 10},
    'peek':     {'name': 'Peek',     'filter': 'wipe(down)', 'presetID': 12, 'presetSubtype': 4},
    'wheel':    {'name': 'Wheel',    'filter': 'wheel(4)', 'presetID': 21, 'presetSubtype': 0},
    'box':      {'name': 'Box',      'filter': 'box(in)', 'presetID': 4, 'presetSubtype': 0},
    'circle':   {'name': 'Circle',   'filter': 'circle(in)', 'presetID': 6, 'presetSubtype': 0},
    'diamond':  {'name': 'Diamond',  'filter': 'diamond(in)', 'presetID': 8, 'presetSubtype': 0},
    'plus':     {'name': 'Plus',     'filter': 'plus(in)', 'presetID': 13, 'presetSubtype': 0},
    'strips':   {'name': 'Strips',   'filter': 'strips(downRight)', 'presetID': 18, 'presetSubtype': 12},
    'wedge':    {'name': 'Wedge',    'filter': 'wedge', 'presetID': 20, 'presetSubtype': 0},
    'stretch':  {'name': 'Stretch',  'filter': 'stretch(across)', 'presetID': 17, 'presetSubtype': 0},
    'expand':   {'name': 'Expand',   'filter': 'stretch(across)', 'presetID': 50, 'presetSubtype': 0},
    'swivel':   {'name': 'Swivel',   'filter': 'wheel(1)', 'presetID': 19, 'presetSubtype': 0},
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
    """Resolved entrance-animation request for one PowerPoint shape."""

    shape_id: int
    delay_ms: int
    effect: str
    duration_ms: int


@dataclass(frozen=True)
class AnimationRowSummary:
    """Read-back summary for one entrance row in the animation pane."""

    shape_id: int
    effect: str | None
    trigger: str
    duration_ms: int
    offset_ms: int
    preset_id: int
    preset_subtype: int
    filter_name: str | None


@dataclass(frozen=True)
class AnimationSequenceSummary:
    """Read-back summary for the logical entrance sequence on one slide."""

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
    if effect in ANIMATIONS:
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


def _normalize_target(target: Sequence[object], default_duration_ms: int) -> AnimationTarget:
    if isinstance(target, (str, bytes)) or not isinstance(target, Sequence):
        raise ValueError(f'animation target must be a 3- or 4-item sequence: {target!r}')
    if len(target) not in (3, 4):
        raise ValueError(f'animation target must contain 3 or 4 items: {target!r}')
    shape_id = _positive_shape_id(target[0])
    delay_ms = _non_negative_milliseconds(target[1], 'animation target delay_ms')
    effect = normalize_animation_effect(
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
    )

# Pool used by 'mixed' / 'random' modes. Excludes 'appear' because it has no
# visible motion; mixed handles the first title-like element as fade separately.
_MIXED_POOL = [
    'blinds', 'checkerboard', 'dissolve', 'fly', 'cut',
    'random_bars', 'box', 'split', 'strips', 'wedge', 'wheel',
    'wipe', 'expand', 'fade', 'swivel', 'zoom',
]

# Small modern pool used by 'auto' mode when the group id matches no semantic
# pattern. Restricted to four widely supported, restrained effects so the
# fallback cycle never produces PowerPoint-era visuals.
_AUTO_POOL = ['fade', 'wipe', 'fly', 'zoom']

# Image-only diversity pool. Image-like groups (`hero`, `figure-`, `image`,
# `img-`, `kpi`) deliberately cycle through a richer set of visual effects
# rather than mapping to a single effect: images are visual focal points, so
# variation is desirable on them even when surrounding information-dense
# elements (titles, charts, lists) stay reserved. Pool members are chosen for
# image-friendly motion — no PowerPoint-era patterns (blinds / checkerboard /
# random_bars / wedge) that would dominate raster content.
_IMAGE_POOL = ['zoom', 'dissolve', 'circle', 'box', 'diamond', 'wheel']
_IMAGE_KEYWORDS: tuple[str, ...] = ('hero', 'figure-', 'image', 'img-', 'kpi')

# Ordered (substring, effect) patterns consumed by 'auto' mode for non-image
# groups. The first matching substring in the lowercased group id wins;
# ordering matters where substrings could overlap (e.g. 'title' before 'item'
# prevents 'item-title' from being misread as a list item). All substrings are
# lowercase. Image-like ids are handled separately via ``_IMAGE_POOL`` because
# they cycle rather than map to a single effect.
_SEMANTIC_PATTERNS: list[tuple[tuple[str, ...], str]] = [
    (('title', 'chapter-', 'section-', 'cover-', 'tagline', 'subtitle'), 'fade'),
    (('chart', 'table', 'legend', 'timeline', 'track'),                   'wipe'),
    (('card-', 'pillar-', 'item-', 'step-', 'stage-', 'tier-',
      'principle-', 'q-', 'schema-'),                                     'fly'),
    (('takeaway', 'callout', 'quote', 'source', 'conclusion', 'note',
      'try-at-home'),                                                     'fade'),
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
    animation: str = 'fade',
    duration: float = 1.0,
    delay: float = 0,
    shape_id: int = 2
) -> str:
    """
    Generate an entrance animation timing XML fragment

    Args:
        animation: Animation effect name (fade/fly/zoom/appear)
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
    anim_info = ANIMATIONS[animation]
    dur_ms = _seconds_to_ms(
        duration,
        'animation duration',
        allow_zero=False,
    )
    delay_ms = _seconds_to_ms(
        delay,
        'animation delay',
        allow_zero=True,
    )

    # Generate different effect XML depending on animation type
    if anim_info['filter'] is None:
        # appear animation: only sets visibility
        effect_xml = f'''                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="5" dur="1" fill="hold">
                                  <p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst>
                                </p:cTn>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                              </p:cBhvr>
                              <p:to><p:strVal val="visible"/></p:to>
                            </p:set>'''
    else:
        # Other animations: set visibility + animation effect
        filter_name = anim_info['filter']
        pr_attr = ''
        if 'prLst' in anim_info:
            pr_attr = f' prLst="{anim_info["prLst"]}"'

        effect_xml = f'''                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="5" dur="1" fill="hold">
                                  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                                </p:cTn>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                              </p:cBhvr>
                              <p:to><p:strVal val="visible"/></p:to>
                            </p:set>
                            <p:animEffect transition="in" filter="{filter_name}"{pr_attr}>
                              <p:cBhvr>
                                <p:cTn id="6" dur="{dur_ms}"/>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                              </p:cBhvr>
                            </p:animEffect>'''

    return f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" nodeType="tmRoot">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="none">
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="3" fill="hold">
                      <p:stCondLst>
                        <p:cond delay="{delay_ms}"/>
                      </p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="4" fill="hold">
                            <p:childTnLst>
{effect_xml}
                            </p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
            </p:seq>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>'''


def _build_effect_xml(
    animation: str,
    shape_id: int,
    duration_ms: int,
    set_id: int,
    eff_id: int,
) -> str:
    """Inner effect block for one target.

    Entrance effects are emitted as one animation pane row per target. Plain
    Appear uses a visibility set; motion/filter effects use animEffect directly
    to avoid duplicate rows for the same shape in PowerPoint.
    """
    animation = normalize_animation_effect(
        animation,
        allow_none=False,
        allow_modes=False,
    )
    shape_id = _positive_shape_id(shape_id)
    duration_ms = _non_negative_milliseconds(
        duration_ms,
        'animation duration_ms',
    )
    if duration_ms == 0:
        raise ValueError('animation duration_ms must be greater than zero')
    anim_info = ANIMATIONS[animation]
    set_block = f'''<p:set>
  <p:cBhvr>
    <p:cTn id="{set_id}" dur="1" fill="hold">
      <p:stCondLst><p:cond delay="0"/></p:stCondLst>
    </p:cTn>
    <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
    <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
  </p:cBhvr>
  <p:to><p:strVal val="visible"/></p:to>
</p:set>'''
    if anim_info['filter'] is None:
        return set_block
    return set_block + f'''
<p:animEffect transition="in" filter="{anim_info["filter"]}">
  <p:cBhvr>
    <p:cTn id="{eff_id}" dur="{duration_ms}"/>
    <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
  </p:cBhvr>
</p:animEffect>'''


def create_sequence_timing_xml(
    targets: list,
    duration: float = 0.3,
    trigger: str = 'after-previous',
) -> str:
    """Generate a multi-target entrance sequence.

    Args:
        targets: list of (shape_id, delay_ms, animation_name) or
            (shape_id, delay_ms, animation_name, duration_seconds) tuples, in
            the order they should play. ``delay_ms`` is the gap before
            this element starts, measured from when the previous element
            triggers (only used in ``after-previous`` mode; ignored in
            the other two).
        duration: per-element entrance duration in seconds.
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

    if trigger == 'on-click':
        # Each element is an independent click-driven par directly under
        # mainSeq. Three-level nesting per element: outer cTn holds for
        # the click via delay="indefinite", innermost cTn owns the
        # clickEffect + animation children. Each click advances the seq.
        steps = []
        for target in normalized_targets:
            shape_id = target.shape_id
            animation = target.effect
            item_dur_ms = target.duration_ms
            anim_info = ANIMATIONS[animation]
            preset_id = anim_info.get('presetID', 1)
            preset_subtype = anim_info.get('presetSubtype', 0)
            wrapper_id = next_id
            inner_id = next_id + 1
            leaf_id = next_id + 2
            set_id = next_id + 3
            eff_id = next_id + 4
            next_id += 5
            effect_xml = _build_effect_xml(animation, shape_id, item_dur_ms, set_id, eff_id)
            steps.append(f'''<p:par>
  <p:cTn id="{wrapper_id}" fill="hold">
    <p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>
    <p:childTnLst>
      <p:par>
        <p:cTn id="{inner_id}" fill="hold">
          <p:stCondLst><p:cond delay="0"/></p:stCondLst>
          <p:childTnLst>
            <p:par>
              <p:cTn id="{leaf_id}" presetID="{preset_id}" presetClass="entr"
                      presetSubtype="{preset_subtype}" fill="hold" nodeType="clickEffect">
                <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                <p:childTnLst>
                  {effect_xml}
                </p:childTnLst>
              </p:cTn>
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
        # Native PowerPoint after-previous export uses two timing layers for
        # each animation row: an outer wrapper owns the timeline offset, while
        # the inner effect cTn stays nodeType="afterEffect" with delay="0".
        # This keeps the animation pane editable as standard "After Previous"
        # rows instead of exposing synthetic per-effect cumulative delays.
        outer_id = next_id
        next_id += 1
        inner_steps = []
        with_wrapper_id = None
        if trigger == 'with-previous':
            with_wrapper_id = next_id
            next_id += 1
        elapsed_ms = 0
        prev_duration_ms = 0
        for i, target in enumerate(normalized_targets):
            shape_id = target.shape_id
            delay_ms = target.delay_ms
            animation = target.effect
            item_dur_ms = target.duration_ms
            anim_info = ANIMATIONS[animation]
            preset_id = anim_info.get('presetID', 1)
            preset_subtype = anim_info.get('presetSubtype', 0)

            if trigger == 'with-previous':
                leaf_id = next_id
                set_id = next_id + 1
                eff_id = next_id + 2
                next_id += 3
                effect_xml = _build_effect_xml(animation, shape_id, item_dur_ms, set_id, eff_id)
                inner_steps.append(f'''<p:par>
                  <p:cTn id="{leaf_id}" presetID="{preset_id}" presetClass="entr"
                          presetSubtype="{preset_subtype}" fill="hold" nodeType="withEffect">
                    <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                    <p:childTnLst>
                      {effect_xml}
                    </p:childTnLst>
                  </p:cTn>
                </p:par>''')
            else:
                if i == 0:
                    elapsed_ms = int(delay_ms)
                else:
                    elapsed_ms += prev_duration_ms + int(delay_ms)
                if elapsed_ms > MAX_OOXML_MILLISECONDS:
                    raise ValueError(
                        'animation sequence offset exceeds the OOXML '
                        f'millisecond limit at target {i + 1}: {elapsed_ms}'
                    )
                wrapper_id = next_id
                leaf_id = next_id + 1
                set_id = next_id + 2
                eff_id = next_id + 3
                next_id += 4
                effect_xml = _build_effect_xml(animation, shape_id, item_dur_ms, set_id, eff_id)
                inner_steps.append(f'''<p:par>
                  <p:cTn id="{wrapper_id}" fill="hold">
                    <p:stCondLst><p:cond delay="{elapsed_ms}"/></p:stCondLst>
                    <p:childTnLst>
                      <p:par>
                        <p:cTn id="{leaf_id}" presetID="{preset_id}" presetClass="entr"
                                presetSubtype="{preset_subtype}" fill="hold" nodeType="afterEffect">
                          <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                          <p:childTnLst>
                            {effect_xml}
                          </p:childTnLst>
                        </p:cTn>
                      </p:par>
                    </p:childTnLst>
                  </p:cTn>
                </p:par>''')
                prev_duration_ms = item_dur_ms

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

    return f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="seek">
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
              {all_steps}
                </p:childTnLst>
              </p:cTn>
              <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
              <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
            </p:seq>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>'''


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
      (zoom / dissolve / circle / box / diamond / wheel) by ``idx + offset``
      so multiple images vary across the deck. Other semantic matches in
      ``_SEMANTIC_PATTERNS`` return a single stable effect (chart→wipe,
      card-/step-/pillar-→fly, title/takeaway→fade). When the id matches no
      pattern, cycle through ``_AUTO_POOL`` (fade / wipe / fly / zoom).
    - 'mixed' (legacy): first element fixed to 'fade', rest cycle through
      ``_MIXED_POOL`` plus ``offset`` (so titles stay calm while content varies
      across slides). Kept for backward compatibility with existing CLI flags
      and animations.json sidecars.
    - 'random' (legacy): uniform random choice from ``_MIXED_POOL``.
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
    if mode in ANIMATIONS:
        return mode
    if mode == 'auto':
        semantic = _semantic_effect(group_id, idx, offset)
        if semantic is not None:
            return semantic
        return _AUTO_POOL[(idx + offset) % len(_AUTO_POOL)]
    if mode == 'mixed':
        if idx == 0:
            return 'fade'
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
            'one entrance row must resolve to exactly one shape id; '
            f'found {unique or "none"}'
        )
        return None
    return unique[0]


def _row_filter(row: ET.Element, errors: list[str]) -> str | None:
    effects = list(row.iter(_qn(PML_NS, 'animEffect')))
    if len(effects) > 1:
        errors.append(f'entrance row contains {len(effects)} p:animEffect nodes')
    if not effects:
        return None
    effect = effects[0]
    if effect.get('transition') != 'in':
        errors.append('entrance p:animEffect must set transition="in"')
    return effect.get('filter')


def _resolve_row_effect(
    row: ET.Element,
    filter_name: str | None,
    errors: list[str],
) -> tuple[str | None, int | None, int | None]:
    preset_id = _int_attribute(
        row,
        'presetID',
        'entrance p:cTn@presetID',
        errors,
        maximum=MAX_OOXML_UNSIGNED_INT,
    )
    preset_subtype = _int_attribute(
        row,
        'presetSubtype',
        'entrance p:cTn@presetSubtype',
        errors,
        maximum=MAX_OOXML_UNSIGNED_INT,
    )
    if preset_id is None or preset_subtype is None:
        return None, preset_id, preset_subtype
    matches = [
        key
        for key, info in ANIMATIONS.items()
        if int(info['presetID']) == preset_id
        and int(info['presetSubtype']) == preset_subtype
        and info['filter'] == filter_name
    ]
    if len(matches) == 1:
        return matches[0], preset_id, preset_subtype
    return None, preset_id, preset_subtype


def _behavior_duration_ms(
    row: ET.Element,
    filter_name: str | None,
    errors: list[str],
) -> int:
    if filter_name is None:
        behaviors = list(row.iter(_qn(PML_NS, 'set')))
    else:
        behaviors = list(row.iter(_qn(PML_NS, 'animEffect')))
    if len(behaviors) != 1:
        errors.append(
            'entrance row must contain exactly one primary behavior; '
            f'found {len(behaviors)}'
        )
        return 0
    common_behavior = behaviors[0].find(_qn(PML_NS, 'cBhvr'))
    duration_node = (
        common_behavior.find(_qn(PML_NS, 'cTn'))
        if common_behavior is not None
        else None
    )
    if duration_node is None:
        errors.append('entrance behavior is missing p:cBhvr/p:cTn')
        return 0
    duration = _int_attribute(
        duration_node,
        'dur',
        'entrance behavior duration',
        errors,
        minimum=1,
        maximum=MAX_OOXML_MILLISECONDS,
    )
    return duration or 0


def _row_offset_ms(
    row: ET.Element,
    trigger: str,
    parent_map: Mapping[ET.Element, ET.Element],
    errors: list[str],
) -> int:
    leaf_conditions = _direct_conditions(row)
    if len(leaf_conditions) != 1 or leaf_conditions[0].get('delay') != '0':
        errors.append('entrance row must have one leaf start condition with delay="0"')

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

    if trigger == 'on-click' and not saw_indefinite:
        errors.append('on-click entrance row is missing an indefinite click wrapper')
    if trigger in {'with-previous', 'after-previous'} and not (
        saw_indefinite and saw_main_begin
    ):
        errors.append(f'{trigger} sequence is missing the slide-entry onBegin anchor')
    if trigger == 'after-previous' and numeric_offset is None:
        errors.append('after-previous entrance row is missing its numeric offset wrapper')
    if trigger == 'after-previous':
        return numeric_offset or 0
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
        if row.get('presetClass') != 'entr':
            continue
        node_type = row.get('nodeType')
        trigger = _NODE_TYPE_TRIGGERS.get(node_type or '')
        if trigger is None:
            errors.append(
                f'unsupported entrance nodeType {node_type!r}; expected '
                f'{", ".join(_NODE_TYPE_TRIGGERS)}'
            )
            continue
        shape_id = _row_shape_id(row, errors)
        filter_name = _row_filter(row, errors)
        effect, preset_id, preset_subtype = _resolve_row_effect(
            row,
            filter_name,
            errors,
        )
        duration_ms = _behavior_duration_ms(row, filter_name, errors)
        offset_ms = _row_offset_ms(row, trigger, parent_map, errors)
        if shape_id is None or preset_id is None or preset_subtype is None:
            continue
        rows.append(
            AnimationRowSummary(
                shape_id=shape_id,
                effect=effect,
                trigger=trigger,
                duration_ms=duration_ms,
                offset_ms=offset_ms,
                preset_id=preset_id,
                preset_subtype=preset_subtype,
                filter_name=filter_name,
            )
        )
    return rows


def validate_slide_animation_structure(
    slide_root: ET.Element,
    *,
    require_supported_effects: bool = False,
) -> list[str]:
    """Return root timing, target, and generated-entrance structure errors."""
    errors: list[str] = []
    if slide_root.tag != _qn(PML_NS, 'sld'):
        return ['animation validation requires a PresentationML p:sld root']

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

    ctn_ids: list[int] = []
    for ctn in timing.iter(_qn(PML_NS, 'cTn')):
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

    entrance_nodes = [
        node for node in timing.iter(_qn(PML_NS, 'cTn'))
        if node.get('presetClass') == 'entr'
    ]
    if entrance_nodes and require_supported_effects:
        main_sequences = [
            node for node in timing.iter(_qn(PML_NS, 'cTn'))
            if node.get('nodeType') == 'mainSeq'
        ]
        if len(main_sequences) != 1:
            errors.append(
                'slides with entrance rows must contain exactly one mainSeq time node'
            )
    if require_supported_effects:
        rows = _animation_rows(slide_root, errors)
        if not rows and entrance_nodes:
            errors.append('generated entrance rows could not be read back')
    else:
        rows = []
    if rows:
        triggers = {row.trigger for row in rows}
        if len(triggers) != 1:
            errors.append(
                'one generated entrance sequence must use one Start mode; found '
                + ', '.join(sorted(triggers))
            )
        row_shape_ids = [row.shape_id for row in rows]
        if len(row_shape_ids) != len(set(row_shape_ids)):
            errors.append('generated entrance sequence repeats a shape target')
        for row in rows:
            if row.effect is None:
                errors.append(
                    'unsupported entrance effect tuple for shape '
                    f'{row.shape_id}: presetID={row.preset_id}, '
                    f'presetSubtype={row.preset_subtype}, '
                    f'filter={row.filter_name!r}'
                )
    return errors


def read_slide_animation_sequence(
    slide_xml: str | bytes,
    *,
    require_supported_effects: bool = False,
) -> AnimationSequenceSummary:
    """Read and validate the logical entrance sequence from one slide XML."""
    data = slide_xml.encode('utf-8') if isinstance(slide_xml, str) else slide_xml
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f'invalid slide XML: {exc}') from exc
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
    trigger = rows[0].trigger if rows else None
    return AnimationSequenceSummary(
        timing_count=len(direct_timings),
        trigger=trigger,
        rows=tuple(rows),
        audio_target_ids=tuple(audio_targets),
    )


def validate_generated_animation_xml(
    slide_xml: str | bytes,
    targets: Sequence[Sequence[object]],
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
    expected = tuple(
        _normalize_target(target, default_duration_ms)
        for target in targets
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
    if expected and summary.trigger != trigger:
        errors.append(
            f'animation read-back trigger is {summary.trigger!r}; expected {trigger!r}'
        )

    expected_offsets: list[int] = []
    elapsed_ms = 0
    previous_duration_ms = 0
    for index, target in enumerate(expected):
        if trigger == 'after-previous':
            if index == 0:
                elapsed_ms = target.delay_ms
            else:
                elapsed_ms += previous_duration_ms + target.delay_ms
            if elapsed_ms > MAX_OOXML_MILLISECONDS:
                errors.append(
                    'requested animation sequence offset exceeds the OOXML '
                    f'millisecond limit at row {index + 1}: {elapsed_ms}'
                )
            expected_offsets.append(elapsed_ms)
            previous_duration_ms = target.duration_ms
        else:
            expected_offsets.append(0)

    for index, (actual, target) in enumerate(zip(summary.rows, expected), 1):
        spec = ANIMATIONS[target.effect]
        if actual.shape_id != target.shape_id:
            errors.append(
                f'animation row {index} targets shape {actual.shape_id}; '
                f'expected {target.shape_id}'
            )
        if actual.effect != target.effect:
            errors.append(
                f'animation row {index} resolved effect {actual.effect!r}; '
                f'expected {target.effect!r}'
            )
        if actual.preset_id != int(spec['presetID']):
            errors.append(f'animation row {index} presetID changed')
        if actual.preset_subtype != int(spec['presetSubtype']):
            errors.append(f'animation row {index} presetSubtype changed')
        if actual.filter_name != spec['filter']:
            errors.append(f'animation row {index} filter changed')
        expected_duration = 1 if target.effect == 'appear' else target.duration_ms
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
    if errors:
        raise ValueError('; '.join(errors))
    return summary


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
                try:
                    root = ET.fromstring(package.read(name))
                except ET.ParseError as exc:
                    errors.append(f'{name}: invalid XML: {exc}')
                    continue
                for error in validate_slide_animation_structure(
                    root,
                    require_supported_effects=require_supported_effects,
                ):
                    errors.append(f'{name}: {error}')
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
    """Get a list of all available transition effects"""
    return list(TRANSITIONS.keys())


def get_available_animations() -> list:
    """Get a list of all available entrance animations"""
    return list(ANIMATIONS.keys())


def get_transition_help() -> str:
    """Get help text for transition effects"""
    lines = ["Available transition effects:"]
    for key, info in TRANSITIONS.items():
        lines.append(f"  {key}: {info['name']}")
    return '\n'.join(lines)


def get_animation_help() -> str:
    """Get help text for entrance animations"""
    lines = ["Available entrance animations:"]
    for key, info in ANIMATIONS.items():
        lines.append(f"  {key}: {info['name']}")
    return '\n'.join(lines)


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--demo", action="store_true", help="print sample XML for a fade transition and animation")
    parser.add_argument("--list", action="store_true", help="list available transitions and entrance animations")
    args = parser.parse_args()

    if args.list:
        print(get_transition_help())
        print()
        print(get_animation_help())
        return

    if args.demo:
        print("=== Transition Effect XML Example (fade, 500ms) ===")
        print(create_transition_xml('fade', 0.5))
        print()
        print("=== Entrance Animation XML Example (fade) ===")
        print(create_timing_xml('fade', 1.0))
        return

    parser.print_help()


if __name__ == '__main__':
    main()
