"""apply: page-to-page transitions for cloned slides.

Native templates usually ship an empty ``<p:transition/>`` that renders as no
motion, so ``apply`` injects a default transition unless told to ``keep`` the
source or set ``none``. Effects come from the shared ``pptx_animations``
vocabulary so they match the SVG export path.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import NS, P14_NS, _qn

try:
    from pptx_animations import TRANSITIONS
except ImportError:
    TRANSITIONS = {}

# Default page transition injected by `apply` when neither the CLI flag nor a
# per-slide plan field asks for something else. Use `keep` to preserve the
# source transitions instead.
DEFAULT_TRANSITION = "fade"
DEFAULT_TRANSITION_DURATION = 0.5
KEEP_TRANSITION = "keep"

_UNSET = object()


def _build_transition_element(
    effect: str,
    duration: float,
    advance_after: float | None = None,
) -> ET.Element:
    """Build a populated <p:transition> element from the shared TRANSITIONS vocabulary."""
    info = TRANSITIONS[effect]
    transition = ET.Element(_qn(NS["p"], "transition"))
    transition.set(_qn(P14_NS, "dur"), str(int(float(duration) * 1000)))
    if advance_after is not None:
        transition.set("advTm", str(int(float(advance_after) * 1000)))
    child = ET.SubElement(transition, _qn(NS["p"], info["element"]))
    for key, value in info.get("attrs", {}).items():
        child.set(key, str(value))
    return transition


def _set_slide_transition(
    slide_root: ET.Element,
    *,
    effect: str | None,
    duration: float,
    advance_after: float | None = None,
) -> None:
    """Replace the cloned slide's transition element (empty in most templates).

    ``effect`` of ``None`` or ``"keep"`` leaves the source transition untouched;
    ``"none"`` strips it so the slide advances with no animation. OOXML requires
    the transition to sit after ``p:clrMapOvr`` and before ``p:timing``.
    """
    if effect is None or effect == KEEP_TRANSITION:
        return

    new_element = None if effect == "none" else _build_transition_element(effect, duration, advance_after)
    existing = slide_root.find("p:transition", NS)
    if existing is not None:
        index = list(slide_root).index(existing)
        slide_root.remove(existing)
        if new_element is not None:
            slide_root.insert(index, new_element)
        return
    if new_element is None:
        return

    timing = slide_root.find("p:timing", NS)
    if timing is not None:
        slide_root.insert(list(slide_root).index(timing), new_element)
        return
    clr_map_ovr = slide_root.find("p:clrMapOvr", NS)
    if clr_map_ovr is not None:
        slide_root.insert(list(slide_root).index(clr_map_ovr) + 1, new_element)
        return
    slide_root.append(new_element)


def _resolve_slide_transition(
    item: dict[str, Any],
    *,
    default_effect: str | None,
    default_duration: float,
) -> tuple[str | None, float, float | None]:
    """Pick a slide's transition from its plan entry, falling back to CLI defaults."""
    raw = item.get("transition", _UNSET)
    if raw is _UNSET:
        return default_effect, default_duration, None
    if isinstance(raw, dict):
        effect = raw.get("effect", default_effect)
        duration = raw.get("duration", default_duration)
        advance_after = raw.get("advance_after")
    else:
        effect = str(raw)
        duration = default_duration
        advance_after = None
    if effect is not None and effect not in ("none", KEEP_TRANSITION) and effect not in TRANSITIONS:
        raise RuntimeError(
            f"Unknown transition effect '{effect}'. Valid: {', '.join(sorted(TRANSITIONS))}, none, {KEEP_TRANSITION}"
        )
    return effect, float(duration), advance_after
