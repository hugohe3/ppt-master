#!/usr/bin/env python3
"""Derive advisory text-slot capacity from SVG geometry and font metrics.

Usage:
    Via svg_quality_checker.py --template-mode --slot-capacity-report.

Dependencies:
    Standard library and the shared text estimator.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from text_measure import measure_text
from template_text_slots import analyze_template_text_slots
from svg_to_pptx.drawingml.text_properties import (
    resolve_project_font_sizes,
    resolve_project_letter_spacings,
)

from .checker import SVGQualityChecker, _effective_presentation_value, _parse_positive_bounds


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


def _mirror_text_bounds(carrier, parents, font_sizes, spacings):
    """Use the source text frame, falling back to measured text geometry."""
    owner = carrier
    while owner is not None:
        for name in ('data-pptx-bounds', 'data-pptx-frame'):
            raw = owner.get(name)
            if raw is None:
                continue
            try:
                bounds = _parse_positive_bounds(raw)
            except ValueError:
                continue
            if bounds is not None:
                return bounds, name
        owner = parents.get(id(owner))
    estimated = SVGQualityChecker._estimated_text_bounds(carrier, parents, font_sizes, spacings)
    if estimated is None:
        return None, 'unresolved text geometry'
    left, top, right, bottom = estimated
    return (left, top, right - left, bottom - top), 'estimated text geometry'


def _text_targets(path, root, parents, font_sizes, spacings):
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
        yield {'file': str(path), 'slot_id': slot.get('id'), 'source': 'placeholder',
               'placeholder': placeholder, 'bounds': bounds}, carriers[0]

    manifest = path.parent / 'template_execution_manifest.json'
    sidecar = path.parent / 'template_execution' / f'{path.stem}.text-slots.json'
    if not manifest.is_file() or not sidecar.is_file():
        return
    manifest_data = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(manifest_data, dict):
        raise ValueError(f'{manifest}: expected a manifest object')
    if manifest_data.get('replication_mode') != 'mirror':
        return
    text_elements = [element for element in root.iter() if element.tag.rsplit('}', 1)[-1] == 'text']
    by_selector = {
        selector: element
        for slot, element in zip(analyze_template_text_slots(root), text_elements)
        for selector in (slot.selector, slot.legacy_selector)
    }
    sidecar_data = json.loads(sidecar.read_text(encoding='utf-8'))
    if not isinstance(sidecar_data, dict) or not isinstance(sidecar_data.get('text_slots'), list):
        raise ValueError(f'{sidecar}: expected a text_slots array')
    for slot in sidecar_data['text_slots']:
        if not isinstance(slot, dict) or not isinstance(slot.get('selector'), str):
            raise ValueError(f'{sidecar}: each text slot requires a selector string')
        selector = slot['selector']
        carrier = by_selector.get(selector)
        row = {'file': str(path), 'slot_id': selector, 'selector': selector,
               'source': 'mirror-text-slot', 'placeholder': None, 'bounds': None}
        if carrier is None:
            yield {**row, 'unavailable': 'selector does not resolve to a text element'}, None
            continue
        row['bounds'], row['bounds_source'] = _mirror_text_bounds(carrier, parents, font_sizes, spacings)
        yield row, carrier


def slot_capacity_report(svg_files: list[Path]) -> dict:
    """Read placeholder and mirror text targets without changing files or gates."""
    slots = []
    for path in svg_files:
        root = ET.parse(path).getroot()
        parents = {id(child): parent for parent in root.iter() for child in parent}
        font_sizes = resolve_project_font_sizes(root)
        spacings = resolve_project_letter_spacings(root, font_sizes)
        for row, carrier in _text_targets(path, root, parents, font_sizes, spacings):
            bounds = row['bounds']
            if bounds is None:
                row.setdefault('unavailable', 'missing or invalid slot bounds')
                slots.append(row)
                continue
            # Imported paragraphs can put all visible text and typography on
            # tspans. Use the first visible run, and expose mixed-run conditions.
            runs = [node for node in carrier.iter() if (node.text or '').strip()]
            first_run = runs[0] if runs else carrier
            def value(name: str) -> str | None:
                return _effective_presentation_value(first_run, name, parents)

            size = font_sizes[id(first_run)]
            family = value('font-family') or 'Calibri'
            weight = value('font-weight') or 'normal'
            spacing = spacings[id(first_run)]
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
            ascent, descent = SVGQualityChecker._text_line_vertical_extent([], size)
            row['baseline_allowed'] = [bounds[1] + ascent, bounds[1] + bounds[3] - descent]
            lines = SVGQualityChecker._resolved_text_lines(carrier, parents, font_sizes, spacings)
            row['baseline'] = lines[0][2] if lines else None
            if not lines:
                # Source paragraph models may have a known first baseline even
                # when the estimator cannot resolve every subsequent line.
                try:
                    baseline = float((value('y') or '0').removesuffix('px'))
                except ValueError:
                    baseline = math.nan
                if math.isfinite(baseline):
                    row['baseline'] = baseline
            if lines and len(lines) > 1:
                row['baselines'] = [line[2] for line in lines]
            variants = sorted({
                (_effective_presentation_value(run, 'font-family', parents) or family,
                 font_sizes[id(run)])
                for run in runs
            })
            if len(variants) > 1:
                row['typography_variants'] = [
                    {'font_family': face, 'font_size': pixels} for face, pixels in variants
                ]
                row['estimate_scope'] = 'first visible run; measure mixed content separately'
            slots.append(row)
    report = {
        'schema': 'ppt-master.slot-capacity.v1', 'advisory': True,
        'assumptions': 'Uniform carrier typography; Latin sample distribution and CJK full-width glyphs. '
                       'Line count uses declared/baseline pitch or an explicit 1.2em estimate. '
                       'Measure actual content before locking typography; these are not limits.',
        'slots': slots,
    }
    if not slots:
        report['note'] = ('No text placeholder carriers or mirror text-slot targets were found. '
                          'Mirror targets are listed in template_execution/*.text-slots.json.')
    return report
