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

Supported entrance animations:
    - fade: Fade in
    - fly: Fly in
    - zoom: Zoom
    - appear: Appear

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

ANIMATIONS: Dict[str, Dict[str, Any]] = {
    'fade': {
        'name': 'Fade In',
        'filter': 'fade',
    },
    'fly': {
        'name': 'Fly In',
        'filter': 'fly',
        'prLst': 'from(b)',  # Fly in from bottom
    },
    'zoom': {
        'name': 'Zoom',
        'filter': 'zoom',
        'prLst': 'in',
    },
    'appear': {
        'name': 'Appear',
        'filter': None,  # No filter, only sets visibility
    },
}


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
