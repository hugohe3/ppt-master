"""apply: page-to-page transitions for cloned slides.

Native templates usually ship an empty ``<p:transition/>`` that renders as no
motion, so ``apply`` injects a default transition unless told to ``keep`` the
source or set ``none``. Effects and OOXML mutation come from the shared
``pptx_transitions`` core so every PPTX path uses the same writer.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from pptx_transitions import (
    TRANSITIONS,
    AdvanceUpdate,
    EnterUpdate,
    apply_slide_motion,
    validate_seconds,
)

# Default page transition injected by `apply` when neither the CLI flag nor a
# per-slide plan field asks for something else. Use `keep` to preserve the
# source transitions instead.
DEFAULT_TRANSITION = "fade"
DEFAULT_TRANSITION_DURATION = 0.5
KEEP_TRANSITION = "keep"

_UNSET = object()


def _set_slide_transition(
    slide_root: ET.Element,
    *,
    effect: str | None,
    duration: float,
    advance_after: float | None = None,
) -> bool:
    """Apply a legacy template-fill transition through the shared core.

    ``None`` and ``keep`` preserve the source transition. ``none`` removes the
    visual transition while retaining an explicitly requested auto-advance.
    Legacy ``advance_after`` allowed both click and timed advance, so it maps to
    ``both`` rather than the stricter ``after`` mode. The return value reports
    whether the resulting slide contains an automatic advance.
    """
    if effect is None or effect == KEEP_TRANSITION:
        enter = EnterUpdate(policy="preserve")
        advance = AdvanceUpdate(
            mode="preserve" if advance_after is None else "both",
            after=advance_after,
        )
    elif effect == "none":
        enter = EnterUpdate(policy="none", effect=None, duration=duration)
        advance = AdvanceUpdate(
            mode="click" if advance_after is None else "both",
            after=advance_after,
        )
    else:
        enter = EnterUpdate(
            policy="replace",
            effect=effect,
            duration=duration,
        )
        advance = AdvanceUpdate(
            mode="click" if advance_after is None else "both",
            after=advance_after,
        )

    try:
        return apply_slide_motion(
            slide_root,
            enter=enter,
            advance=advance,
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


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
        effect = None if raw is None else str(raw)
        duration = default_duration
        advance_after = None
    if effect is not None and effect not in ("none", KEEP_TRANSITION) and effect not in TRANSITIONS:
        raise RuntimeError(
            f"Unknown transition effect '{effect}'. Valid: {', '.join(sorted(TRANSITIONS))}, none, {KEEP_TRANSITION}"
        )
    try:
        resolved_duration = validate_seconds(
            duration,
            "transition duration",
            allow_zero=False,
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    return effect, resolved_duration, advance_after
