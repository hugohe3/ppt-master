#!/usr/bin/env python3
"""
PPT Master - DrawingML Text Baseline

Estimate the first baseline of ordinary top-anchored DrawingML text from
bundled font metrics. See scripts/docs/svg-pipeline.md for the rendering scope.

Usage:
    Import drawingml_text_baseline_offset from the DrawingML converter.

Examples:
    offset = drawingml_text_baseline_offset(runs, fonts, default_size=40)

Dependencies:
    None (only uses standard library and sibling modules)
"""

from __future__ import annotations

import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any

from .text_properties import parse_project_font_weight
from .utils import (
    FONT_PX_TO_HUNDREDTHS_PT,
    font_px_to_hpt,
    is_cjk_char,
    parse_font_family,
    primary_font_family,
)


@lru_cache(maxsize=1)
def _font_metrics() -> dict[str, Any]:
    with Path(__file__).with_name('font_metrics.json').open(encoding='utf-8') as handle:
        return json.load(handle)['families']


def _ascent_ratio(family: str, weight: str, style: str) -> Fraction:
    faces = _font_metrics().get(primary_font_family(family), {})
    bold = parse_project_font_weight(weight).value
    face_style = 'bold' if bold else 'regular'
    if style == 'italic':
        face_style = 'bold-italic' if bold else 'italic'
    # A synthesized italic keeps its real bold face when one is available.
    # Unknown fonts use a fixed ratio, independent of installed fonts.
    metrics = (
        faces.get(face_style)
        or (faces.get('bold') if bold else None)
        or faces.get('regular')
    )
    if metrics is None:
        return Fraction(4, 5)
    source = 'typo' if metrics['fsSelection'] & 128 else 'win'
    ascent, descent = metrics[source][:2]
    return Fraction(ascent, ascent + abs(descent))


def _whole_points(value: Fraction) -> int:
    rounded = value + Fraction(1, 2)
    return rounded.numerator // rounded.denominator


def drawingml_text_baseline_offset(
    runs: list[dict[str, Any]],
    default_fonts: dict[str, str],
    *,
    default_size: float,
    line_spacing_px: float | None = None,
    line_spacing_ratio: float = 1.0,
    language: str | None = None,
) -> float:
    """Return the first baseline's distance from a zero-inset frame top in px.

    Call only for ordinary text, without native math or baseline shifts.
    Runs describe the first visual line. Importers may supply resolved
    ``font_faces`` to retain the original DrawingML script slots. Font sizes
    and explicit line spacing use the same quantization as the emitted XML.
    """
    ascent = descent = largest_size = Fraction(0)
    for run in runs:
        if run.get('_line_break'):
            break
        text = str(run.get('text', ''))
        if not text:
            continue
        size = Fraction(font_px_to_hpt(run.get('font_size', default_size)), 100)
        fonts = run.get('font_faces') or (
            parse_font_family(str(run['font_family']), language)
            if run.get('font_family') else default_fonts
        )
        families = {fonts['ea'] if is_cjk_char(ch) else fonts['latin'] for ch in text}
        for family in families:
            ratio = _ascent_ratio(
                family,
                str(run.get('font_weight', '400')),
                str(run.get('font_style', 'normal')),
            )
            ascent = max(ascent, size * ratio)
            descent = max(descent, size * (1 - ratio))
        largest_size = max(largest_size, size)

    if not largest_size:
        return 0.0
    natural_height = Fraction(6, 5) * largest_size
    baseline = natural_height * ascent / (ascent + descent)
    if line_spacing_px is not None or line_spacing_ratio != 1.0:
        spacing = natural_height * Fraction(str(line_spacing_ratio))
        if line_spacing_px is not None:
            spacing = Fraction(round(line_spacing_px * FONT_PX_TO_HUNDREDTHS_PT), 100)
            # The compatible layout rounds fixed spacing before choosing its
            # branch: 57.6pt becomes 58pt even when natural height is 57.6pt.
            # Percentage spacing keeps its natural-height semantics.
            spacing = Fraction(_whole_points(spacing))
        minimum_baseline = Fraction(3, 4) * spacing
        baseline = (
            max(minimum_baseline, spacing - (natural_height - baseline))
            if spacing <= natural_height else minimum_baseline
        )

    # PowerPoint's compatible layout rounds the first-line offset to whole
    # points. Rational arithmetic preserves half-point ties (e.g. SimSun 64px)
    # without float epsilons or Python round()'s ties-to-even behavior.
    return float(_whole_points(baseline) * Fraction(4, 3))
