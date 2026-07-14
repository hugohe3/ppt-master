"""Convert the closed DrawingML effect subset into project SVG filters.

One classifiable outer shadow or one glow maps to the public shadow/glow
contract. Every other source effect receives explicit blocking metadata; the
importer never relabels it as another native effect or drops it silently.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from pptx_effects import unsupported_effect_metadata
from pptx_shapes.formula import OOXML_COORDINATE_MAX

from .color_resolver import COLOR_TAGS, ColorPalette, resolve_color
from .emu_units import NS, emu_to_px, fmt_num


_OOXML_INTEGER_RE = re.compile(r"[+-]?\d+")
_OOXML_HEX_COLOR_RE = re.compile(r"[0-9A-Fa-f]{6}")
_OOXML_INT_MIN = -(2**31)
_OOXML_INT_MAX = 2**31 - 1
_DRAWINGML_NAMESPACE = NS["a"]
_DRAWINGML_TAG_PREFIX = f"{{{_DRAWINGML_NAMESPACE}}}"
_EFFECT_CONTAINER_NAMES = frozenset({"effectLst", "effectDag"})
# Modulation/offset transforms use DrawingML percentage types, not all fixed
# percentages; values above 100% such as satMod=175000 are valid.
_COLOR_MODIFIER_PERCENT_RANGES = {
    "alpha": (0, 100000),
    "alphaMod": (0, _OOXML_INT_MAX),
    "alphaOff": (-100000, 100000),
    "hueMod": (0, _OOXML_INT_MAX),
    "lumMod": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "lumOff": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "satMod": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "satOff": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "shade": (0, 100000),
    "tint": (0, 100000),
}
_COLOR_MODIFIER_FLAG_NAMES = frozenset({"comp", "gray", "inv"})


@dataclass(frozen=True)
class EffectResult:
    """One supported SVG filter or one explicit unsupported-source marker."""

    filter_id: str | None = None
    defs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()

    @classmethod
    def unsupported(cls, reason: str) -> "EffectResult":
        return cls(metadata=tuple(unsupported_effect_metadata(reason).items()))


def unsupported_target_effect_metadata(
    sp_pr: ET.Element | None,
    target: str,
) -> dict[str, str]:
    """Mark source effects that cannot attach to this SVG target type."""
    if sp_pr is None:
        return {}
    effect_names: list[str] = []
    for container in sp_pr:
        if (
            not isinstance(container.tag, str)
            or _local_name(container) not in _EFFECT_CONTAINER_NAMES
        ):
            continue
        container_name = _local_name(container)
        if container_name == "effectDag":
            effect_names.append(container_name)
            continue
        effect_names.extend(
            _local_name(child)
            for child in container
            if isinstance(child.tag, str)
        )
    if not effect_names:
        return {}
    return unsupported_effect_metadata(
        f"unsupported-effect-target:{target}:" + ",".join(effect_names)
    )


def convert_effects(
    sp_pr: ET.Element | None,
    palette: ColorPalette | None,
    *,
    id_prefix: str = "fx",
    id_seq: list[int] | None = None,
) -> EffectResult:
    """Return one supported filter or blocking metadata for source effects."""
    if sp_pr is None:
        return EffectResult()
    containers = [
        child
        for child in sp_pr
        if isinstance(child.tag, str)
        and _local_name(child) in _EFFECT_CONTAINER_NAMES
    ]
    if not containers:
        return EffectResult()
    container_names = [_local_name(child) for child in containers]
    if len(containers) != 1:
        return EffectResult.unsupported(
            "multiple-effect-containers:" + ",".join(container_names)
        )
    container = containers[0]
    container_name = container_names[0]
    if not container.tag.startswith(_DRAWINGML_TAG_PREFIX):
        return EffectResult.unsupported(
            f"invalid-effect-container-namespace:{container_name}"
        )
    if container_name == "effectDag":
        return EffectResult.unsupported("unsupported-effect-container:effectDag")
    effects = [
        child
        for child in container
        if isinstance(child.tag, str)
    ]
    if not effects:
        return EffectResult()
    names = [child.tag.split("}", 1)[-1] for child in effects]
    if len(effects) != 1:
        return EffectResult.unsupported(
            "multiple-effects:" + ",".join(names)
        )

    effect = effects[0]
    effect_name = names[0]
    if not effect.tag.startswith(_DRAWINGML_TAG_PREFIX):
        return EffectResult.unsupported(
            f"invalid-effect-namespace:{effect_name}"
        )
    try:
        if effect_name == "outerShdw":
            primitives = _outer_shadow(effect, palette)
        elif effect_name == "glow":
            primitives = _glow(effect, palette)
        else:
            return EffectResult.unsupported(
                f"unsupported-effect:{effect_name}"
            )
    except (OverflowError, TypeError, ValueError) as exc:
        return EffectResult.unsupported(
            f"invalid-effect:{effect_name}:{exc}"
        )

    if id_seq is None:
        id_seq = [0]
    id_seq[0] += 1
    filter_id = f"{id_prefix}{id_seq[0]}"

    # Filter region needs to extend beyond the bounding box to render shadows
    # and glows; choose generous defaults.
    filter_x = "-25%"
    filter_y = "-25%"
    filter_w = "150%"
    filter_h = "150%"

    defs_xml = (
        f'<filter id="{filter_id}" x="{filter_x}" y="{filter_y}" '
        f'width="{filter_w}" height="{filter_h}">'
        + primitives
        + "</filter>"
    )
    return EffectResult(filter_id=filter_id, defs=(defs_xml,))


def _color_alpha(elem: ET.Element, palette: ColorPalette | None) -> tuple[str, float]:
    direct_children = [
        child
        for child in elem
        if isinstance(child.tag, str)
    ]
    colors = [
        child
        for child in direct_children
        if _local_name(child) in COLOR_TAGS
    ]
    if len(colors) != 1:
        reason = "missing-color" if not colors else "multiple-colors"
        raise ValueError(reason)
    if len(direct_children) != 1:
        extras = [
            _local_name(child)
            for child in direct_children
            if child is not colors[0]
        ]
        raise ValueError("unexpected-effect-child:" + ",".join(extras))
    color = colors[0]
    if not color.tag.startswith(_DRAWINGML_TAG_PREFIX):
        raise ValueError(f"invalid-color-namespace:{_local_name(color)}")
    _validate_color(color, palette)
    hex_, alpha = resolve_color(color, palette)
    if hex_ is None:
        raise ValueError(f"unresolvable-color:{_local_name(color)}")
    return hex_, alpha


def _validate_color(
    color: ET.Element,
    palette: ColorPalette | None,
) -> None:
    """Validate the color subset resolved into one SVG filter paint."""
    color_name = _local_name(color)
    if color_name == "srgbClr":
        raw = color.get("val", "")
        if _OOXML_HEX_COLOR_RE.fullmatch(raw) is None:
            raise ValueError(f"invalid-color:{color_name}")
    elif color_name == "schemeClr":
        raw = (color.get("val") or "").strip()
        resolved = palette.resolve_scheme(raw) if palette is not None else None
        if resolved is None or _OOXML_HEX_COLOR_RE.fullmatch(resolved) is None:
            raise ValueError(f"unresolvable-color:{color_name}")
    elif color_name == "sysClr":
        raw = color.get("lastClr") or ""
        if _OOXML_HEX_COLOR_RE.fullmatch(raw) is None:
            raise ValueError(f"unresolvable-color:{color_name}")
    elif color_name == "hslClr":
        _required_integer(color, "hue", 0, 21_599_999)
        _required_integer(color, "sat", 0, 100000)
        _required_integer(color, "lum", 0, 100000)
    elif color_name == "scrgbClr":
        for attr in ("r", "g", "b"):
            _required_integer(color, attr, 0, 100000)
    elif not (color.get("val") or "").strip():
        raise ValueError(f"invalid-color:{color_name}")

    for modifier in color:
        if not isinstance(modifier.tag, str):
            continue
        modifier_name = _local_name(modifier)
        if not modifier.tag.startswith(_DRAWINGML_TAG_PREFIX):
            raise ValueError(
                f"invalid-color-modifier-namespace:{modifier_name}"
            )
        bounds = _COLOR_MODIFIER_PERCENT_RANGES.get(modifier_name)
        if bounds is not None:
            _required_integer(modifier, "val", *bounds)
        elif modifier_name == "hueOff":
            _required_integer(
                modifier,
                "val",
                _OOXML_INT_MIN,
                _OOXML_INT_MAX,
            )
        elif modifier_name not in _COLOR_MODIFIER_FLAG_NAMES:
            raise ValueError(f"unsupported-color-modifier:{modifier_name}")


def _required_integer(
    elem: ET.Element,
    attr: str,
    minimum: int,
    maximum: int,
) -> int:
    raw = elem.get(attr)
    if raw is None:
        raise ValueError(f"missing-{_local_name(elem)}-{attr}")
    token = raw.strip()
    if _OOXML_INTEGER_RE.fullmatch(token) is None:
        raise ValueError(f"invalid-{_local_name(elem)}-{attr}")
    value = int(token)
    if not minimum <= value <= maximum:
        raise ValueError(f"invalid-{_local_name(elem)}-{attr}")
    return value


def _local_name(elem: ET.Element) -> str:
    return elem.tag.rsplit("}", 1)[-1]


def _effect_integer(
    elem: ET.Element,
    attr: str,
    *,
    default: int = 0,
    non_negative: bool = False,
    maximum: int | None = None,
) -> int:
    raw = elem.get(attr)
    if raw is None:
        value = default
    else:
        token = raw.strip()
        if _OOXML_INTEGER_RE.fullmatch(token) is None:
            raise ValueError(f"{attr}={raw!r}")
        value = int(token)
    if (
        (non_negative and value < 0)
        or (maximum is not None and value > maximum)
    ):
        raise ValueError(f"{attr}={raw!r}")
    return value


def _direction_offset(elem: ET.Element) -> tuple[float, float]:
    """Read dir / dist into (dx, dy) px."""
    direction_units = _effect_integer(
        elem,
        "dir",
        non_negative=True,
        maximum=21_599_999,
    )
    dist_emu = _effect_integer(
        elem,
        "dist",
        non_negative=True,
        maximum=OOXML_COORDINATE_MAX,
    )
    direction_deg = direction_units / 60000.0
    dist_px = emu_to_px(dist_emu)
    rad = math.radians(direction_deg)
    return dist_px * math.cos(rad), dist_px * math.sin(rad)


def _blur_radius(elem: ET.Element, attr: str) -> float:
    return emu_to_px(_effect_integer(
        elem,
        attr,
        non_negative=True,
        maximum=OOXML_COORDINATE_MAX,
    ))


def _outer_shadow(
    elem: ET.Element,
    palette: ColorPalette | None,
) -> str:
    dx, dy = _direction_offset(elem)
    blur = _blur_radius(elem, "blurRad")
    dx_token = fmt_num(dx, 8)
    dy_token = fmt_num(dy, 8)
    if abs(float(dx_token)) <= 0.01 and abs(float(dy_token)) <= 0.01:
        raise ValueError("offset-is-not-classifiable")
    color, alpha = _color_alpha(elem, palette)
    # std deviation ~= blur radius / 2 (rough; PowerPoint shadows are larger)
    std = blur / 2.0
    # Use feDropShadow for compactness — it's well-supported in modern browsers.
    return (
        f'<feDropShadow dx="{dx_token}" dy="{dy_token}" '
        f'stdDeviation="{fmt_num(std, 8)}" '
        f'flood-color="{color}" flood-opacity="{fmt_num(alpha, 5)}"/>'
    )


def _glow(elem: ET.Element, palette: ColorPalette | None) -> str:
    if elem.get("rad") is None:
        raise ValueError("missing-rad")
    rad = _blur_radius(elem, "rad")
    color, alpha = _color_alpha(elem, palette)
    # svg_to_pptx maps stdDeviation directly back to a:glow@rad.
    std = rad
    return (
        f'<feGaussianBlur in="SourceAlpha" stdDeviation="{fmt_num(std, 8)}" result="blurred"/>'
        f'<feFlood flood-color="{color}" flood-opacity="{fmt_num(alpha, 5)}" result="flood"/>'
        f'<feComposite in="flood" in2="blurred" operator="in" result="glow"/>'
        f'<feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>'
    )
