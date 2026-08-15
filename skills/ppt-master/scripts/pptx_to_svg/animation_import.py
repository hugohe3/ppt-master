"""Import the finite PPT Master-owned object-animation contract.

The importer deliberately projects only canonical effect identity, pane order,
Start trigger, duration, relative delay, and one top-level SVG group target.
Everything else remains an explicit source-preservation boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET

from pptx_animations import (
    AnimationRowSummary,
    effective_animation_effect_options,
    read_slide_animation_sequence,
    validate_generated_animation_xml,
)

from .ooxml_loader import OoxmlPackage, SlideRef


_SVG_NS = "http://www.w3.org/2000/svg"
_UNSUPPORTED_TIMING_TAGS = frozenset(
    {
        "audio",
        "bldDgm",
        "bldGraphic",
        "bldLst",
        "bldOleChart",
        "bldP",
        "cmd",
        "video",
    }
)


class AnimationImportError(ValueError):
    """Raised when source timing exceeds the finite reversible contract."""


@dataclass(frozen=True)
class AnimationImport:
    """Canonical per-group animation rows for one slide."""

    groups: dict[str, dict[str, object]]


def import_slide_animation(
    pkg: OoxmlPackage,
    slide: SlideRef,
    *,
    slide_svg: str,
) -> AnimationImport | None:
    """Read one exact generated object-animation sequence into sidecar rows."""
    slide_xml = pkg.read_part_bytes(slide.part.path)
    if slide_xml is None:
        raise AnimationImportError(
            f"source slide part is missing: {slide.part.path}"
        )
    return read_animation_config(slide_xml, slide_svg)


def read_animation_config(
    slide_xml: str | bytes,
    slide_svg: str,
) -> AnimationImport | None:
    """Read one exact generated object-animation sequence from XML and SVG."""
    data = slide_xml.encode("utf-8") if isinstance(slide_xml, str) else slide_xml
    if not _contains_timing(data):
        return None

    try:
        summary = read_slide_animation_sequence(
            data,
            require_supported_effects=True,
        )
    except ValueError as exc:
        raise AnimationImportError(str(exc)) from exc
    if summary.timing_count != 1:
        raise AnimationImportError(
            "object animation requires exactly one effective root p:timing"
        )
    if not summary.rows:
        raise AnimationImportError(
            "p:timing contains no supported object-animation rows"
        )
    if summary.audio_target_ids:
        raise AnimationImportError(
            "media playback and animation sounds are outside the finite "
            "object-animation read-back contract"
        )
    unsupported_tags = _unsupported_timing_tags(data)
    if unsupported_tags:
        raise AnimationImportError(
            "unsupported timing feature(s): " + ", ".join(unsupported_tags)
        )

    group_id_by_shape_id = _top_level_shape_group_index(slide_svg)
    delays = _relative_delays(summary.rows)
    expected_targets: list[dict[str, object]] = []
    rows_by_group: dict[str, list[dict[str, object]]] = {}

    for order, (row, delay_ms) in enumerate(
        zip(summary.rows, delays),
        1,
    ):
        if row.effect is None or row.duration_ms is None:
            raise AnimationImportError(
                f"animation row {order} has no exact registry effect or duration"
            )
        group_id = _resolve_group_id(
            group_id_by_shape_id,
            row.shape_id,
            label=f"animation row {order} target",
        )
        trigger_group_id = None
        if row.trigger_shape_id is not None:
            trigger_group_id = _resolve_group_id(
                group_id_by_shape_id,
                row.trigger_shape_id,
                label=f"animation row {order} trigger",
            )

        sidecar_row: dict[str, object] = {
            "effect": row.effect,
            "duration": row.duration_ms / 1000.0,
            "delay": delay_ms / 1000.0,
            "order": order,
            "trigger": row.trigger,
        }
        expected_target: dict[str, object] = {
            "shape_id": row.shape_id,
            "delay_ms": delay_ms,
            "effect": row.effect,
            "duration": row.duration_ms / 1000.0,
            "trigger": row.trigger,
        }
        effect_options = dict(row.effect_options)
        try:
            default_options = effective_animation_effect_options(row.effect)
        except ValueError:
            default_options = None
        if effect_options != default_options:
            sidecar_row["effect_options"] = effect_options
            expected_target["effect_options"] = effect_options
        if row.trigger_shape_id is not None:
            expected_target["trigger_shape_id"] = row.trigger_shape_id
            sidecar_row["trigger_shape"] = trigger_group_id
        expected_targets.append(expected_target)
        rows_by_group.setdefault(group_id, []).append(sidecar_row)

    try:
        validate_generated_animation_xml(data, expected_targets)
    except ValueError as exc:
        raise AnimationImportError(str(exc)) from exc

    groups: dict[str, dict[str, object]] = {}
    for group_id, rows in rows_by_group.items():
        groups[group_id] = (
            rows[0]
            if len(rows) == 1
            else {"effects": rows}
        )
    return AnimationImport(groups=groups)


def _contains_timing(slide_xml: bytes) -> bool:
    """Return whether any selected or fallback branch contains p:timing."""
    try:
        root = ET.fromstring(slide_xml)
    except ET.ParseError as exc:
        raise AnimationImportError(f"invalid slide XML: {exc}") from exc
    return any(_local_name(node.tag) == "timing" for node in root.iter())


def _unsupported_timing_tags(slide_xml: bytes) -> tuple[str, ...]:
    """Return timing features that the finite sidecar projection cannot own."""
    root = ET.fromstring(slide_xml)
    found = {
        _local_name(node.tag)
        for node in root.iter()
        if _local_name(node.tag) in _UNSUPPORTED_TIMING_TAGS
    }
    return tuple(sorted(found))


def _top_level_shape_group_index(slide_svg: str) -> dict[int, tuple[str, ...]]:
    """Index direct slide-local SVG group anchors by source shape id."""
    try:
        root = ET.fromstring(slide_svg)
    except ET.ParseError as exc:
        raise AnimationImportError(f"invalid reconstructed slide SVG: {exc}") from exc

    groups: dict[int, list[str]] = {}
    group_id_counts: dict[str, int] = {}
    for child in list(root):
        if child.tag != f"{{{_SVG_NS}}}g":
            continue
        if child.get("data-pptx-shape-scope") != "slide":
            continue
        raw_shape_id = child.get("data-pptx-shape-id") or ""
        if not raw_shape_id.isdigit() or int(raw_shape_id) <= 0:
            continue
        group_id = child.get("id") or ""
        if not group_id.strip():
            continue
        shape_id = int(raw_shape_id)
        groups.setdefault(shape_id, []).append(group_id)
        group_id_counts[group_id] = group_id_counts.get(group_id, 0) + 1

    return {
        shape_id: (
            tuple(group_ids)
            if (
                len(group_ids) == 1
                and group_id_counts.get(group_ids[0]) == 1
            )
            else ()
        )
        for shape_id, group_ids in groups.items()
    }


def _resolve_group_id(
    group_id_by_shape_id: dict[int, tuple[str, ...]],
    shape_id: int,
    *,
    label: str,
) -> str:
    group_ids = group_id_by_shape_id.get(shape_id, ())
    if len(group_ids) != 1:
        raise AnimationImportError(
            f"{label} shape {shape_id} must map to exactly one unique "
            f"top-level slide SVG group; found {group_ids or 'none'}"
        )
    return group_ids[0]


def _relative_delays(rows: tuple[AnimationRowSummary, ...]) -> tuple[int, ...]:
    """Invert the native writer's absolute main-sequence offsets."""
    delays: list[int] = []
    previous_start_ms = 0
    previous_duration_ms = 0
    has_previous = False
    for index, row in enumerate(rows, 1):
        if row.playback_duration_ms is None:
            raise AnimationImportError(
                f"animation row {index} has no exact playback duration"
            )
        if row.trigger_shape_id is not None or row.trigger == "on-click":
            base_ms = 0
        elif row.trigger == "with-previous":
            base_ms = previous_start_ms if has_previous else 0
        elif row.trigger == "after-previous":
            base_ms = (
                previous_start_ms + previous_duration_ms
                if has_previous
                else 0
            )
        else:
            raise AnimationImportError(
                f"animation row {index} has unsupported trigger {row.trigger!r}"
            )
        delay_ms = row.offset_ms - base_ms
        if delay_ms < 0:
            raise AnimationImportError(
                f"animation row {index} has a negative reconstructed delay"
            )
        delays.append(delay_ms)
        if row.trigger_shape_id is None:
            previous_start_ms = row.offset_ms
            previous_duration_ms = row.playback_duration_ms
            has_previous = True
    return tuple(delays)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


__all__ = [
    "AnimationImport",
    "AnimationImportError",
    "import_slide_animation",
    "read_animation_config",
]
