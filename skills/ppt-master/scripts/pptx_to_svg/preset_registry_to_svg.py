#!/usr/bin/env python3
"""
PPT Master - Preset Geometry SVG Adapter

Render evaluated DrawingML preset geometry as absolute SVG path layers.

Usage:
    Import render_preset_geometry from pptx_to_svg.preset_registry_to_svg.

Examples:
    geometry = render_preset_geometry("rightArrow", xfrm)

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from pptx_shapes import get_preset_registry

from .emu_units import Xfrm, fmt_num


@dataclass(frozen=True)
class SvgPresetPath:
    """One visible layer from a DrawingML preset's ``a:pathLst``."""

    d: str
    fill: str
    stroke: bool


@dataclass(frozen=True)
class SvgPresetGeometry:
    """A fully evaluated preset preview in slide-absolute SVG coordinates."""

    paths: tuple[SvgPresetPath, ...]


def render_preset_geometry(
    preset: str,
    xfrm: Xfrm,
    adjustments: Mapping[str, str | int | float] | None = None,
) -> SvgPresetGeometry:
    """Evaluate ``preset`` and project every DrawingML path into SVG space."""

    evaluated = get_preset_registry().evaluate(
        preset,
        xfrm.w,
        xfrm.h,
        adjustments=adjustments,
    )
    layers = tuple(
        SvgPresetPath(
            d=render_evaluated_path(
                path.commands,
                x=xfrm.x,
                y=xfrm.y,
                width=xfrm.w,
                height=xfrm.h,
                coordinate_width=path.coordinate_width,
                coordinate_height=path.coordinate_height,
            ),
            fill=path.fill,
            stroke=path.stroke,
        )
        for path in evaluated.paths
    )
    return SvgPresetGeometry(paths=tuple(layer for layer in layers if layer.d))


def render_evaluated_path(
    commands,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    coordinate_width: float,
    coordinate_height: float,
) -> str:
    scale_x = width / coordinate_width if coordinate_width else 1.0
    scale_y = height / coordinate_height if coordinate_height else 1.0

    def point(px: float, py: float) -> tuple[float, float]:
        return x + px * scale_x, y + py * scale_y

    parts: list[str] = []
    current = (x, y)
    subpath_start = current
    for command in commands:
        values = command.parameters
        if command.name == "moveTo":
            current = point(values[0], values[1])
            subpath_start = current
            parts.append(f"M {fmt_num(current[0])} {fmt_num(current[1])}")
        elif command.name == "lnTo":
            current = point(values[0], values[1])
            parts.append(f"L {fmt_num(current[0])} {fmt_num(current[1])}")
        elif command.name == "quadBezTo":
            control = point(values[0], values[1])
            current = point(values[2], values[3])
            parts.append(
                "Q "
                f"{fmt_num(control[0])} {fmt_num(control[1])} "
                f"{fmt_num(current[0])} {fmt_num(current[1])}"
            )
        elif command.name == "cubicBezTo":
            control_1 = point(values[0], values[1])
            control_2 = point(values[2], values[3])
            current = point(values[4], values[5])
            parts.append(
                "C "
                f"{fmt_num(control_1[0])} {fmt_num(control_1[1])} "
                f"{fmt_num(control_2[0])} {fmt_num(control_2[1])} "
                f"{fmt_num(current[0])} {fmt_num(current[1])}"
            )
        elif command.name == "arcTo":
            arc_parts, current = _render_arc(
                current,
                radius_x=values[0],
                radius_y=values[1],
                scale_x=scale_x,
                scale_y=scale_y,
                start_angle=values[2],
                sweep_angle=values[3],
            )
            parts.extend(arc_parts)
        elif command.name == "close":
            parts.append("Z")
            current = subpath_start
    return " ".join(parts)


def _render_arc(
    current: tuple[float, float],
    *,
    radius_x: float,
    radius_y: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    start_angle: float,
    sweep_angle: float,
) -> tuple[list[str], tuple[float, float]]:
    """Render one DrawingML arc, splitting full circles for SVG validity.

    DrawingML resolves the polar angle in the path-local ellipse before the
    path coordinate system is scaled into the shape frame.  Applying the
    angle correction to already-scaled radii bends explicit-extent paths such
    as ``cloud`` when the containing shape has a non-square aspect ratio.
    """

    radius_x = abs(radius_x)
    radius_y = abs(radius_y)
    scaled_radius_x = abs(radius_x * scale_x)
    scaled_radius_y = abs(radius_y * scale_y)
    if (
        radius_x <= 1e-12
        or radius_y <= 1e-12
        or scaled_radius_x <= 1e-12
        or scaled_radius_y <= 1e-12
        or abs(sweep_angle) <= 1e-12
    ):
        return [], current

    start_radians = _ellipse_parameter_angle(
        start_angle,
        radius_x,
        radius_y,
    )
    center_x = current[0] - scaled_radius_x * math.cos(start_radians)
    center_y = current[1] - scaled_radius_y * math.sin(start_radians)

    # SVG cannot represent a 360-degree arc with one A command because its
    # start and end points coincide.  Chunks of at most 180 degrees also keep
    # the large-arc flag deterministic for every preset definition.
    remaining = sweep_angle
    angle = start_angle
    parts: list[str] = []
    endpoint = current
    half_circle = 180.0 * 60000.0
    while abs(remaining) > 1e-9:
        step = math.copysign(min(abs(remaining), half_circle), remaining)
        angle += step
        end_radians = _ellipse_parameter_angle(angle, radius_x, radius_y)
        endpoint = (
            center_x + scaled_radius_x * math.cos(end_radians),
            center_y + scaled_radius_y * math.sin(end_radians),
        )
        large_arc = 1 if abs(step) > half_circle else 0
        sweep = 1 if step >= 0 else 0
        parts.append(
            "A "
            f"{fmt_num(scaled_radius_x)} {fmt_num(scaled_radius_y)} "
            f"0 {large_arc} {sweep} "
            f"{fmt_num(endpoint[0])} {fmt_num(endpoint[1])}"
        )
        remaining -= step
    return parts, endpoint


def _ellipse_parameter_angle(
    ooxml_angle: float,
    radius_x: float,
    radius_y: float,
) -> float:
    """Unskew an OOXML polar angle into an ellipse parameter angle."""
    radians = math.radians(ooxml_angle / 60000.0)
    return math.atan2(
        radius_x * math.sin(radians),
        radius_y * math.cos(radians),
    )
