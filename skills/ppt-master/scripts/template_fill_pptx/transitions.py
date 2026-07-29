"""apply: page-to-page transitions for cloned slides.

Template Fill preserves each source transition unless the CLI or a per-slide
plan entry requests a replacement. Effects and OOXML mutation come from the
shared ``pptx_transitions`` core so every PPTX path uses the same writer.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from pptx_transitions import (
    AdvanceUpdate,
    EnterUpdate,
    apply_slide_motion,
    normalize_transition_effect_request,
    validate_seconds,
)

KEEP_TRANSITION = "keep"
# Preserve source transitions unless the CLI or a per-slide plan entry selects
# a replacement. The duration is consumed only when a visual effect is written.
DEFAULT_TRANSITION = KEEP_TRANSITION
DEFAULT_TRANSITION_DURATION = 0.5
TRANSITION_OBJECT_FIELDS = frozenset(
    {
        "effect",
        "effect_options",
        "duration",
        "advance_after",
    }
)

_UNSET = object()


def transition_unknown_fields(raw: dict[str, Any]) -> list[str]:
    """Return unsupported fields from a per-slide transition object."""
    return sorted(set(raw) - TRANSITION_OBJECT_FIELDS)


def _set_slide_transition(
    slide_root: ET.Element,
    *,
    effect: str | None,
    duration: float,
    effect_options: dict[str, object] | None = None,
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
            effect_options=effect_options,
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
) -> tuple[str | None, dict[str, object], float, float | None]:
    """Pick a slide's transition from its plan entry, falling back to CLI defaults."""
    raw = item.get("transition", _UNSET)
    if raw is _UNSET:
        if default_effect in (None, "none", KEEP_TRANSITION):
            return default_effect, {}, default_duration, None
        effect, effect_options = normalize_transition_effect_request(
            default_effect,
            allow_none=False,
        )
        return effect, effect_options, default_duration, None
    if isinstance(raw, dict):
        unknown = transition_unknown_fields(raw)
        if unknown:
            raise RuntimeError(
                "Transition has unknown field(s): " + ", ".join(unknown)
            )
        effect = raw.get("effect", default_effect)
        raw_options = raw.get("effect_options")
        if raw_options is not None and "effect" not in raw:
            raise RuntimeError(
                "Transition effect_options requires an explicit effect"
            )
        duration = raw.get("duration", default_duration)
        advance_after = raw.get("advance_after")
    else:
        effect = None if raw is None else str(raw)
        raw_options = None
        duration = default_duration
        advance_after = None
    effect_options: dict[str, object] = {}
    if effect is not None and effect not in ("none", KEEP_TRANSITION):
        try:
            effect, effect_options = normalize_transition_effect_request(
                effect,
                raw_options,
                allow_none=False,
            )
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
    elif raw_options not in (None, {}):
        raise RuntimeError(
            "Transition effect_options requires an explicit native effect"
        )
    try:
        resolved_duration = validate_seconds(
            duration,
            "transition duration",
            allow_zero=False,
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    return effect, effect_options, resolved_duration, advance_after
