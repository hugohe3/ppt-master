#!/usr/bin/env python3
"""
PPT Master - PPTX Animation Module

Provides XML generation for slide transition effects and entrance animations.

Supported transition effects:
    - fade: Fade in/out
    - push: Push
    - wipe: Wipe
    - split: Split
    - strips: Strips (diagonal wipe)
    - cover: Cover
    - random: Random

Supported entrance animations (per-element):
    appear, fade, fly, zoom, wipe, split, blinds,
    dissolve, peek, wheel, box, circle

Animation modes used by the builder:
    - single effect name (one of the above) — apply to every element
    - 'mixed'  — first element fade, the rest cycle through a curated pool
    - 'random' — pick a random effect per element

Dependencies: None (pure XML generation)
"""

from typing import Optional, Dict, Any


# ============================================================================
# Transition effect definitions
# ============================================================================

TRANSITIONS: Dict[str, Dict[str, Any]] = {
    'fade': {
        'name': 'Fade',
        'element': 'fade',
        'attrs': {},
    },
    'push': {
        'name': 'Push',
        'element': 'push',
        'attrs': {'dir': 'r'},  # Push from right
    },
    'wipe': {
        'name': 'Wipe',
        'element': 'wipe',
        'attrs': {'dir': 'r'},  # Wipe from right
    },
    'split': {
        'name': 'Split',
        'element': 'split',
        'attrs': {'orient': 'horz', 'dir': 'out'},
    },
    'strips': {
        'name': 'Strips',
        'element': 'strips',
        'attrs': {'dir': 'rd'},  # Diagonal wipe from bottom-right
    },
    'cover': {
        'name': 'Cover',
        'element': 'cover',
        'attrs': {'dir': 'r'},
    },
    'random': {
        'name': 'Random',
        'element': 'random',
        'attrs': {},
    },
}

def create_transition_xml(
    effect: str = 'fade',
    duration: float = 0.5,
    advance_after: Optional[float] = None
) -> str:
    """
    Generate a slide transition effect XML fragment

    Args:
        effect: Transition effect name (fade/push/wipe/split/strips/cover/random)
        duration: Transition duration (seconds, precise to milliseconds)
        advance_after: Auto-advance interval (seconds); None means manual advance

    Returns:
        A <p:transition> element string insertable into slide XML
    """
    if effect not in TRANSITIONS:
        effect = 'fade'

    trans_info = TRANSITIONS[effect]
    element_name = trans_info['element']
    attrs = trans_info['attrs']

    # Build dur attribute (milliseconds, precise control)
    dur_ms = int(duration * 1000)
    dur_attr = f' dur="{dur_ms}"'

    # Build auto-advance attribute
    adv_attr = ''
    if advance_after is not None:
        adv_tm = int(advance_after * 1000)  # Convert to milliseconds
        adv_attr = f' advTm="{adv_tm}"'

    # Build effect element attributes
    effect_attrs = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
    if effect_attrs:
        effect_attrs = ' ' + effect_attrs

    # Generate XML
    return f'''  <p:transition{dur_attr}{adv_attr}>
    <p:{element_name}{effect_attrs}/>
  </p:transition>'''


# ============================================================================
# Entrance animation definitions
# ============================================================================

#
# 'filter' values must be valid PowerPoint <p:animEffect filter=".."/> strings
# (see ECMA-376 §19.5.10 ST_TLAnimateEffectTransition / filter dictionary).
# Effects with filter=None render as plain "Appear" (visibility flip only).
#
ANIMATIONS: Dict[str, Dict[str, Any]] = {
    'appear':   {'name': 'Appear',   'filter': None},
    'fade':     {'name': 'Fade',     'filter': 'fade'},
    'fly':      {'name': 'Fly In',   'filter': 'slide',    'prLst': 'from(b)'},
    'zoom':     {'name': 'Zoom',     'filter': 'image'},
    'wipe':     {'name': 'Wipe',     'filter': 'wipe',     'prLst': 'from(l)'},
    'split':    {'name': 'Split',    'filter': 'barn',     'prLst': 'inHorizontal'},
    'blinds':   {'name': 'Blinds',   'filter': 'blinds',   'prLst': 'horizontal'},
    'dissolve': {'name': 'Dissolve', 'filter': 'dissolve'},
    'peek':     {'name': 'Peek',     'filter': 'wipe',     'prLst': 'from(b)'},
    'wheel':    {'name': 'Wheel',    'filter': 'wheel',    'prLst': 'spokes(1)'},
    'box':      {'name': 'Box',      'filter': 'box',      'prLst': 'in'},
    'circle':   {'name': 'Circle',   'filter': 'circle',   'prLst': 'in'},
}

# Pool used by 'mixed' / 'random' modes.  Excludes 'appear' (no visible motion)
# and keeps the first slot ('fade') for the title-like first element.
_MIXED_POOL = ['fade', 'fly', 'zoom', 'wipe', 'peek', 'blinds',
               'dissolve', 'split', 'wheel', 'box']


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
    if animation not in ANIMATIONS:
        animation = 'fade'

    anim_info = ANIMATIONS[animation]
    dur_ms = int(duration * 1000)
    delay_ms = int(delay * 1000)

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
            <p:seq concurrent="1" nextAc="seek">
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
    """Inner <p:set>/<p:animEffect> pair for one target."""
    anim_info = ANIMATIONS.get(animation, ANIMATIONS['fade'])
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
    pr_attr = f' prLst="{anim_info["prLst"]}"' if 'prLst' in anim_info else ''
    return set_block + f'''
<p:animEffect transition="in" filter="{anim_info["filter"]}"{pr_attr}>
  <p:cBhvr>
    <p:cTn id="{eff_id}" dur="{duration_ms}"/>
    <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
  </p:cBhvr>
</p:animEffect>'''


def create_sequence_timing_xml(
    targets: list,
    duration: float = 0.3,
) -> str:
    """Generate a multi-target entrance sequence triggered by one click.

    Args:
        targets: list of (shape_id, delay_ms, animation_name) tuples,
            in the order they should play. The first element triggers on
            click; subsequent elements use ``afterEffect`` chaining and
            their ``delay_ms`` becomes the gap after the previous element
            finishes.
        duration: per-element entrance duration in seconds.

    Returns:
        A ``<p:timing>`` element string. Returns an empty string when
        ``targets`` is empty.
    """
    if not targets:
        return ''

    dur_ms = int(duration * 1000)
    steps = []
    for i, target in enumerate(targets):
        shape_id, delay_ms, animation = target
        if animation not in ANIMATIONS:
            animation = 'fade'
        node_type = 'clickEffect' if i == 0 else 'afterEffect'
        base = 3 + 4 * i
        outer_id, inner_id, set_id, eff_id = base, base + 1, base + 2, base + 3
        effect_xml = _build_effect_xml(animation, shape_id, dur_ms, set_id, eff_id)
        steps.append(f'''<p:par>
  <p:cTn id="{outer_id}" fill="hold" nodeType="{node_type}">
    <p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst>
    <p:childTnLst>
      <p:par>
        <p:cTn id="{inner_id}" fill="hold">
          <p:childTnLst>
            {effect_xml}
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:childTnLst>
  </p:cTn>
</p:par>''')

    bld_list = '\n    '.join(
        f'<p:bldP spid="{sid}" grpId="0"/>' for sid, _, _ in targets
    )
    all_steps = '\n              '.join(steps)
    return f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" nodeType="tmRoot">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="seek">
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
              {all_steps}
                </p:childTnLst>
              </p:cTn>
            </p:seq>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
    <p:bldLst>
    {bld_list}
    </p:bldLst>
  </p:timing>'''


def pick_animation_effect(mode: str, idx: int) -> str:
    """Resolve a per-element effect name from a mode string.

    - A specific animation name returns itself (no variation).
    - 'mixed': first element fixed to 'fade', rest cycle through ``_MIXED_POOL``
      starting at index 1 (so titles stay calm while content varies).
    - 'random': uniform random choice from ``_MIXED_POOL``.
    - Unknown mode falls back to 'fade'.
    """
    if mode in ANIMATIONS:
        return mode
    if mode == 'mixed':
        if idx == 0:
            return 'fade'
        return _MIXED_POOL[(idx - 1) % (len(_MIXED_POOL) - 1) + 1]
    if mode == 'random':
        import random
        return random.choice(_MIXED_POOL)
    return 'fade'


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


if __name__ == '__main__':
    # Test output
    print("=== Transition Effect XML Example (fade, 500ms) ===")
    print(create_transition_xml('fade', 0.5))
    print()
    print("=== Entrance Animation XML Example (fade) ===")
    print(create_timing_xml('fade', 1.0))
