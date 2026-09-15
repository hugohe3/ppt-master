#!/usr/bin/env python3
"""Derive advisory text-slot capacity from SVG geometry and font metrics.

Usage:
    Via svg_quality_checker.py --template-mode --slot-capacity-report.

Dependencies:
    Standard library and the shared text estimator.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree as ET

from text_measure import measure_text

from .checker import _effective_presentation_value, _parse_positive_bounds


def _number(value: str | None, default: float) -> float:
    try:
        number = float((value or '').removesuffix('px'))
    except ValueError:
        return default
    return number if math.isfinite(number) and number > 0 else default


def _capacity(width: float, height: float, size: float, family: str,
              weight: str, spacing: float, line_height: float, sample: str) -> dict:
    # Binary search measures the whole line, including estimator headroom and
    # tracking. Latin capacity describes this stated sample, not all strings.
    def fits(count: int) -> bool:
        text = (sample * (count // len(sample) + 1))[:count]
        return measure_text(text, size=size, family=family, weight=weight,
                            letter_spacing=spacing) <= width

    low, high = 0, 1
    while high < 1_000_000 and fits(high):
        low, high = high, high * 2
    while low + 1 < high:
        middle = (low + high) // 2
        if fits(middle):
            low = middle
        else:
            high = middle
    return {
        'sample': sample, 'characters_per_line': low,
        'lines': max(0, 1 + math.floor((height - size) / line_height)),
    }


def slot_capacity_report(svg_files: list[Path]) -> dict:
    """Read text placeholders without adding checker issues or changing files."""
    slots = []
    for path in svg_files:
        root = ET.parse(path).getroot()
        parents = {id(child): parent for parent in root.iter() for child in parent}
        for slot in root.iter():
            placeholder = slot.get('data-pptx-placeholder')
            if not placeholder:
                continue
            carriers = [child for child in slot
                        if child.tag.rsplit('}', 1)[-1] == 'text'
                        and child.get('data-pptx-carrier') == 'true']
            if not carriers:
                continue
            try:
                bounds = _parse_positive_bounds(slot.get('data-pptx-bounds', ''))
            except ValueError:
                bounds = None
            row = {'file': str(path), 'slot_id': slot.get('id'),
                   'placeholder': placeholder, 'bounds': bounds}
            if bounds is None:
                slots.append({**row, 'unavailable': 'missing or invalid slot bounds'})
                continue
            carrier = carriers[0]
            # Imported paragraphs can put all visible text and typography on
            # tspans. Use the first visible run, and expose mixed-run conditions.
            runs = [node for node in carrier.iter() if (node.text or '').strip()]
            first_run = runs[0] if runs else carrier
            def value(name: str) -> str | None:
                return _effective_presentation_value(first_run, name, parents)

            size = _number(value('font-size'), 16.0)
            family = value('font-family') or 'Calibri'
            weight = value('font-weight') or 'normal'
            spacing_raw = value('letter-spacing') or '0'
            try:
                spacing = float(spacing_raw.removesuffix('px'))
                if not math.isfinite(spacing):
                    spacing = 0.0
            except ValueError:
                spacing = 0.0
            raw_line_height = value('line-height')
            line_height = size * 1.2
            line_height_source = 'estimated 1.2em'
            if raw_line_height and raw_line_height != 'normal':
                if raw_line_height.endswith('%'):
                    line_height = size * _number(raw_line_height[:-1], 120) / 100
                elif raw_line_height.endswith('em'):
                    line_height = size * _number(raw_line_height[:-2], 1.2)
                elif raw_line_height.endswith('px'):
                    line_height = _number(raw_line_height, line_height)
                else:
                    line_height = size * _number(raw_line_height, 1.2)
                line_height_source = 'declared'
            else:
                # Explicit tspan baselines are the actual authored line pitch.
                baseline_values = set()
                for tspan in carrier:
                    try:
                        y = float(tspan.get('y', '').removesuffix('px'))
                    except ValueError:
                        continue
                    if math.isfinite(y):
                        baseline_values.add(y)
                ys = sorted(baseline_values)
                pitches = [b - a for a, b in zip(ys, ys[1:]) if b > a]
                if pitches:
                    line_height = min(pitches)
                    line_height_source = 'tspan baselines'
            row.update({
                'font_family': family, 'font_size': size, 'font_weight': weight,
                'font_family_source': 'declared' if value('font-family') else 'assumed Calibri',
                'font_size_source': 'declared' if value('font-size') else 'assumed 16px',
                'letter_spacing': spacing, 'line_height': line_height,
                'line_height_source': line_height_source,
                'latin': _capacity(bounds[2], bounds[3], size, family, weight,
                                   spacing, line_height, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '),
                'cjk': _capacity(bounds[2], bounds[3], size, family, weight,
                                 spacing, line_height, '汉'),
            })
            variants = sorted({
                (_effective_presentation_value(run, 'font-family', parents) or family,
                 _number(_effective_presentation_value(run, 'font-size', parents), size))
                for run in runs
            })
            if len(variants) > 1:
                row['typography_variants'] = [
                    {'font_family': face, 'font_size': pixels} for face, pixels in variants
                ]
                row['estimate_scope'] = 'first visible run; measure mixed content separately'
            slots.append(row)
    return {
        'schema': 'ppt-master.slot-capacity.v1', 'advisory': True,
        'assumptions': 'Uniform carrier typography; Latin sample distribution and CJK full-width glyphs. '
                       'Line count uses declared/baseline pitch or an explicit 1.2em estimate. '
                       'Measure actual content before locking typography; these are not limits.',
        'slots': slots,
    }
