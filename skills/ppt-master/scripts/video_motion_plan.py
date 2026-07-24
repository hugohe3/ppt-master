#!/usr/bin/env python3
"""
PPT Master - Video Motion Plan

Derive an effect-aware video motion plan from one resolved SVG-to-PPTX
conversion trace. The plan preserves animation order, direction, duration,
and timing anchors while adding deterministic video-only motion parameters.

Usage:
    python3 scripts/video_motion_plan.py <conversion_trace.json> [options]

Examples:
    python3 scripts/video_motion_plan.py validation/deck.trace.json --force
    python3 scripts/video_motion_plan.py validation/deck.trace.json \
        --style dynamic -o validation/video_motion_plan.json --force

Dependencies:
    None (standard library only)

See scripts/docs/video-motion-plan.md for the downstream renderer contract.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()


VIDEO_MOTION_SCHEMA = "ppt-master.video-motion-plan.v1"
VIDEO_MOTION_STYLES = ("adaptive", "restrained", "dynamic")
_STYLE_MULTIPLIERS = {
    "adaptive": 1.0,
    "restrained": 0.72,
    "dynamic": 1.28,
}
_SVG_NS = "http://www.w3.org/2000/svg"
_EMU_PER_PX = 9525
_NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"conversion trace not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid conversion trace JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"conversion trace must be a JSON object: {path}")
    return value


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer: {value!r}")
    return value


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer: {value!r}")
    return value


def _finite_positive_float(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite positive number: {value!r}")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be a finite positive number: {value!r}")
    return number


def _resolve_svg_path(raw: object, trace_path: Path) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("conversion trace slide is missing its SVG path")
    path = Path(raw)
    if path.is_absolute() and path.is_file():
        return path

    candidates = [Path.cwd() / path, trace_path.parent / path]
    candidates.extend(parent / path for parent in trace_path.parents)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError(
        f"SVG referenced by conversion trace was not found: {raw}; "
        "run the command from the repository root or regenerate the trace"
    )


def _parse_canvas_emu(svg_path: Path) -> tuple[int, int]:
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"cannot read SVG canvas: {svg_path}: {exc}") from exc

    values = [
        float(match)
        for match in _NUMBER_RE.findall(root.get("viewBox") or "")
    ]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ValueError(f"SVG must have a positive four-number viewBox: {svg_path}")
    return (
        max(1, round(values[2] * _EMU_PER_PX)),
        max(1, round(values[3] * _EMU_PER_PX)),
    )


def _event_score(event: dict[str, Any]) -> int:
    score = 0
    if event.get("tag") == "g":
        score += 4
    if isinstance(event.get("id"), str) and event["id"].strip():
        score += 2
    if event.get("decision") == "native":
        score += 1
    return score


def _shape_events(slide: dict[str, Any]) -> dict[int, dict[str, Any]]:
    events = slide.get("events", [])
    if not isinstance(events, list):
        raise ValueError("conversion trace slide events must be a list")
    selected: dict[int, dict[str, Any]] = {}
    for raw_event in events:
        if not isinstance(raw_event, dict):
            continue
        shape_id = raw_event.get("shape_id")
        bounds = raw_event.get("bounds_emu")
        if (
            isinstance(shape_id, int)
            and shape_id > 0
            and isinstance(bounds, list)
            and len(bounds) == 4
            and all(isinstance(value, int) for value in bounds)
        ):
            current = selected.get(shape_id)
            if current is None or _event_score(raw_event) >= _event_score(current):
                selected[shape_id] = raw_event
    return selected


def _direction_for_effect(effect: str, filter_name: object) -> str | None:
    explicit = {
        "fly": "down",
        "fly_left": "left",
        "fly_right": "right",
        "fly_top": "up",
        "cut": "left",
        "wipe": "left",
        "wipe_left": "left",
        "wipe_right": "right",
        "wipe_up": "up",
        "wipe_down": "down",
        "peek": "down",
        "strips": "down-right",
    }
    if effect in explicit:
        return explicit[effect]
    if isinstance(filter_name, str):
        match = re.search(
            r"\((?:from)?(Top|Bottom|Left|Right|Up|Down)\)",
            filter_name,
            re.IGNORECASE,
        )
        if match:
            value = match.group(1).lower()
            return {"top": "up", "bottom": "down"}.get(value, value)
    return None


def _area_ratio(bounds: list[int], canvas_emu: tuple[int, int]) -> float:
    width = max(0, bounds[2] - bounds[0])
    height = max(0, bounds[3] - bounds[1])
    canvas_area = canvas_emu[0] * canvas_emu[1]
    return (width * height / canvas_area) if canvas_area else 0.0


def _adaptive_multiplier(
    style: str,
    page_role: object,
    object_count: int,
    area_ratio: float,
) -> float:
    multiplier = _STYLE_MULTIPLIERS[style]
    if style == "adaptive":
        if page_role in {"cover", "hero", "closing", "section"}:
            multiplier *= 1.08
        if object_count >= 5:
            multiplier *= 0.82
        elif object_count == 1:
            multiplier *= 1.06
        if area_ratio >= 0.42:
            multiplier *= 0.78
        elif 0 < area_ratio <= 0.10:
            multiplier *= 1.08
    return max(0.55, min(1.45, multiplier))


def _travel_vector(direction: str | None, magnitude: float) -> list[float]:
    vectors = {
        "left": [-magnitude, 0.0],
        "right": [magnitude, 0.0],
        "up": [0.0, -magnitude],
        "down": [0.0, magnitude],
        "down-right": [magnitude * 0.72, magnitude * 0.72],
    }
    return [round(value, 4) for value in vectors.get(direction, [0.0, 0.0])]


def _video_effect(
    effect: str,
    direction: str | None,
    multiplier: float,
) -> dict[str, Any]:
    common: dict[str, Any] = {
        "easing": "ease_out_cubic",
        "opacity_from": 0.0,
        "scale_from": 1.0,
        "travel_canvas_ratio": [0.0, 0.0],
        "blur_px": 0.0,
        "overshoot": 0.0,
        "mask_feather_px": 0.0,
        "motion_blur": 0.0,
    }

    if effect == "appear":
        common.update({
            "family": "hard_reveal",
            "opacity_from": 1.0,
            "easing": "step_end",
        })
    elif effect == "fade":
        common.update({
            "family": "soft_fade",
            "scale_from": round(1.0 - 0.008 * multiplier, 4),
            "blur_px": round(3.0 * multiplier, 2),
        })
    elif effect == "dissolve":
        common.update({
            "family": "grain_dissolve",
            "scale_from": round(1.0 - 0.006 * multiplier, 4),
            "blur_px": round(2.0 * multiplier, 2),
            "grain": round(0.26 * multiplier, 3),
        })
    elif effect in {"fly", "fly_left", "fly_right", "fly_top", "cut"}:
        magnitude = 0.045 * multiplier
        common.update({
            "family": "directional_slide",
            "direction": direction,
            "travel_canvas_ratio": _travel_vector(direction, magnitude),
            "blur_px": round(4.5 * multiplier, 2),
            "overshoot": round(0.012 * multiplier, 4),
            "motion_blur": round(0.22 * multiplier, 3),
        })
    elif effect in {
        "wipe",
        "wipe_left",
        "wipe_right",
        "wipe_up",
        "wipe_down",
        "peek",
    }:
        common.update({
            "family": "soft_mask_reveal",
            "direction": direction,
            "travel_canvas_ratio": _travel_vector(
                direction,
                0.012 * multiplier,
            ),
            "mask_feather_px": round(18.0 * multiplier, 2),
            "blur_px": round(1.5 * multiplier, 2),
        })
    elif effect in {"zoom", "expand", "stretch"}:
        common.update({
            "family": "focus_scale",
            "scale_from": round(1.0 - 0.055 * multiplier, 4),
            "blur_px": round(3.5 * multiplier, 2),
            "overshoot": round(0.008 * multiplier, 4),
        })
    elif effect == "split":
        common.update({
            "family": "split_mask",
            "mask_axis": "vertical",
            "mask_feather_px": round(12.0 * multiplier, 2),
        })
    elif effect in {"box", "circle", "diamond", "plus"}:
        common.update({
            "family": "shape_mask",
            "pattern": effect,
            "scale_from": round(1.0 - 0.025 * multiplier, 4),
            "mask_feather_px": round(10.0 * multiplier, 2),
        })
    elif effect in {
        "blinds",
        "checkerboard",
        "random_bars",
        "strips",
        "wedge",
        "wheel",
    }:
        common.update({
            "family": "pattern_reveal",
            "pattern": effect,
            "mask_feather_px": round(8.0 * multiplier, 2),
        })
    elif effect == "swivel":
        common.update({
            "family": "soft_swivel",
            "scale_from": round(1.0 - 0.025 * multiplier, 4),
            "rotation_from_deg": round(-4.0 * multiplier, 2),
            "blur_px": round(3.0 * multiplier, 2),
        })
    else:
        raise ValueError(f"unsupported resolved animation effect for video: {effect}")
    return common


def _transition_plan(raw_motion: object) -> dict[str, Any]:
    if not isinstance(raw_motion, dict):
        return {
            "source_effect": None,
            "video_effect": "cut",
            "duration_ms": 0,
            "easing": "linear",
        }
    effect = raw_motion.get("effect")
    duration = raw_motion.get("duration_ms")
    if effect is None:
        video_effect = "cut"
    elif effect == "fade":
        video_effect = "crossfade"
    elif effect in {"push", "cover"}:
        video_effect = "directional_push"
    elif effect in {"wipe", "split", "strips"}:
        video_effect = f"soft_{effect}"
    else:
        video_effect = "adaptive_crossfade"
    return {
        "source_effect": effect,
        "video_effect": video_effect,
        "duration_ms": duration if isinstance(duration, int) else 0,
        "easing": "ease_in_out_cubic",
    }


def build_video_motion_plan(
    trace_path: str | Path,
    *,
    style: str = "adaptive",
    default_slide_duration: float = 5.0,
) -> dict[str, Any]:
    """Build one renderer-neutral, effect-aware video motion plan."""
    path = Path(trace_path).resolve()
    if style not in VIDEO_MOTION_STYLES:
        raise ValueError(
            f"unknown video motion style {style!r}; valid styles: "
            f"{', '.join(VIDEO_MOTION_STYLES)}"
        )
    default_duration_ms = round(
        _finite_positive_float(
            default_slide_duration,
            "default slide duration",
        )
        * 1000
    )
    trace = _read_json_object(path)
    raw_slides = trace.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        raise ValueError("conversion trace must contain a non-empty slides list")

    slides: list[dict[str, Any]] = []
    total_objects = 0
    enhanced_objects = 0
    for raw_slide in raw_slides:
        if not isinstance(raw_slide, dict):
            raise ValueError("conversion trace slide entries must be objects")
        slide_num = _positive_int(raw_slide.get("slide_num"), "slide_num")
        svg_path = _resolve_svg_path(raw_slide.get("svg"), path)
        canvas_emu = _parse_canvas_emu(svg_path)
        event_index = _shape_events(raw_slide)

        animation = raw_slide.get("animation", {})
        if not isinstance(animation, dict):
            raise ValueError(f"slide {slide_num} animation summary must be an object")
        rows = animation.get("rows", [])
        if not isinstance(rows, list):
            raise ValueError(f"slide {slide_num} animation rows must be a list")

        objects: list[dict[str, Any]] = []
        for order, raw_row in enumerate(rows, 1):
            if not isinstance(raw_row, dict):
                raise ValueError(f"slide {slide_num} animation row must be an object")
            shape_id = _positive_int(
                raw_row.get("shape_id"),
                f"slide {slide_num} animation shape_id",
            )
            trigger = raw_row.get("trigger")
            if trigger == "on-click":
                raise ValueError(
                    f"slide {slide_num} uses on-click animation; video motion "
                    "requires click-free after-previous or with-previous timing"
                )
            if trigger not in {"after-previous", "with-previous"}:
                raise ValueError(
                    f"slide {slide_num} has unsupported video trigger: {trigger!r}"
                )
            effect = raw_row.get("effect")
            if not isinstance(effect, str) or not effect:
                raise ValueError(
                    f"slide {slide_num} animation row has no resolved effect"
                )
            start_ms = _non_negative_int(
                raw_row.get("offset_ms"),
                f"slide {slide_num} animation offset_ms",
            )
            duration_ms = _positive_int(
                raw_row.get("duration_ms"),
                f"slide {slide_num} animation duration_ms",
            )
            event = event_index.get(shape_id)
            if event is None:
                raise ValueError(
                    f"slide {slide_num} animation shape {shape_id} has no "
                    "conversion-trace bounds"
                )
            bounds = list(event["bounds_emu"])
            area_ratio = _area_ratio(bounds, canvas_emu)
            multiplier = _adaptive_multiplier(
                style,
                raw_slide.get("page_role"),
                len(rows),
                area_ratio,
            )
            direction = _direction_for_effect(
                effect,
                raw_row.get("filter_name"),
            )
            video = _video_effect(effect, direction, multiplier)
            video["duration_ms"] = duration_ms

            group_id = event.get("id")
            if not isinstance(group_id, str) or not group_id.strip():
                group_id = f"shape-{shape_id}"
            objects.append({
                "group_id": group_id,
                "shape_id": shape_id,
                "order": order,
                "source_effect": effect,
                "trigger": trigger,
                "start_ms": start_ms,
                "duration_ms": duration_ms,
                "bounds_emu": bounds,
                "area_ratio": round(area_ratio, 6),
                "video": video,
            })
            total_objects += 1
            if video["family"] != "hard_reveal":
                enhanced_objects += 1

        motion = raw_slide.get("motion")
        advance_after_ms = (
            motion.get("advance_after_ms")
            if isinstance(motion, dict)
            else None
        )
        content_end_ms = max(
            (
                item["start_ms"] + item["duration_ms"]
                for item in objects
            ),
            default=0,
        )
        if isinstance(advance_after_ms, int) and advance_after_ms > 0:
            slide_duration_ms = max(advance_after_ms, content_end_ms)
            duration_source = "recorded-advance"
        else:
            slide_duration_ms = max(default_duration_ms, content_end_ms + 750)
            duration_source = "default-hold"

        slides.append({
            "slide_num": slide_num,
            "svg": str(svg_path),
            "page_role": raw_slide.get("page_role"),
            "canvas_emu": list(canvas_emu),
            "duration_ms": slide_duration_ms,
            "duration_source": duration_source,
            "transition": _transition_plan(motion),
            "objects": objects,
        })

    return {
        "schema": VIDEO_MOTION_SCHEMA,
        "source_trace": str(path),
        "source_pptx": trace.get("output"),
        "style": style,
        "locks": {
            "object_identity": True,
            "object_order": True,
            "semantic_direction": True,
            "timing_anchor": True,
            "source_effect": True,
        },
        "optimizer_scope": [
            "easing",
            "travel_distance",
            "opacity",
            "scale",
            "mask_feather",
            "blur",
            "motion_blur",
            "overshoot",
        ],
        "slide_count": len(slides),
        "object_count": total_objects,
        "enhanced_object_count": enhanced_objects,
        "slides": slides,
    }


def write_video_motion_plan(
    trace_path: str | Path,
    output_path: str | Path,
    *,
    style: str = "adaptive",
    default_slide_duration: float = 5.0,
    force: bool = False,
) -> Path:
    """Build and write one video motion plan."""
    output = Path(output_path)
    if output.exists() and not force:
        raise FileExistsError(
            f"output already exists: {output}; pass --force to overwrite"
        )
    plan = build_video_motion_plan(
        trace_path,
        style=style,
        default_slide_duration=default_slide_duration,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output.resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Derive an effect-aware video motion plan from a resolved "
            "SVG-to-PPTX conversion trace."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "trace",
        help="Path to validation/<output_stem>.trace.json",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output JSON path; default: <trace>.video-motion.json",
    )
    parser.add_argument(
        "--style",
        choices=VIDEO_MOTION_STYLES,
        default="adaptive",
        help="Video-only enhancement intensity; default: adaptive",
    )
    parser.add_argument(
        "--default-slide-duration",
        type=float,
        default=5.0,
        help="Fallback seconds for slides without recorded advance timing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output plan",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    trace_path = Path(args.trace)
    output_path = (
        Path(args.output)
        if args.output
        else trace_path.with_suffix(".video-motion.json")
    )
    try:
        written = write_video_motion_plan(
            trace_path,
            output_path,
            style=args.style,
            default_slide_duration=args.default_slide_duration,
            force=args.force,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    plan = _read_json_object(written)
    print(written)
    print(
        f"Slides: {plan['slide_count']}; objects: {plan['object_count']}; "
        f"video-enhanced: {plan['enhanced_object_count']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
