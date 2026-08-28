#!/usr/bin/env python3
"""Focused regression tests for SVG text and module-bound checks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_quality import checker as checker_module  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402


SVG_NS = 'http://www.w3.org/2000/svg'


def _parse_svg(
    body: str,
    root_attributes: str = '',
    view_box: str = '0 0 1000 1000',
) -> ET.Element:
    return ET.fromstring(
        f'<svg xmlns="{SVG_NS}" viewBox="{view_box}" '
        f'{root_attributes}>{body}</svg>'
    )


def _empty_result() -> dict:
    return {'errors': [], 'warnings': []}


class SVGQualityCheckerBoundsTests(unittest.TestCase):
    def test_leading_direct_text_and_positioned_tspans_are_estimable(self) -> None:
        root = _parse_svg(
            '<g id="module" data-pptx-bounds="0 0 1000 1000">'
            '<text id="mixed" x="10" y="30" font-size="20">'
            'Leading <tspan font-weight="700">bold</tspan>'
            '<tspan x="10" dy="28">Second line</tspan>'
            '</text></g>'
        )
        text_element = root.find(f'.//{{{SVG_NS}}}text')
        self.assertIsNotNone(text_element)
        parent_by_id = {
            id(child): parent
            for parent in root.iter()
            for child in list(parent)
        }
        font_sizes = checker_module._resolve_project_font_sizes(root)
        letter_spacings = checker_module._resolve_project_letter_spacings(
            root,
            font_sizes,
        )

        lines = SVGQualityChecker._positioned_text_lines(
            text_element,
            parent_by_id,
            font_sizes,
            letter_spacings,
        )

        self.assertIsNotNone(lines)
        self.assertEqual(len(lines), 2)
        self.assertEqual(
            [''.join(run['text'] for run in line[3]) for line in lines],
            ['Leading bold', 'Second line'],
        )
        result = _empty_result()
        SVGQualityChecker()._check_text_bounds(root, result)
        self.assertFalse(
            any('Cannot verify' in warning for warning in result['warnings'])
        )

    def test_existing_all_tspan_and_inline_single_line_forms_still_resolve(self) -> None:
        cases = {
            'all_tspan': (
                '<text x="10" y="30" font-size="20">'
                '<tspan x="10">First</tspan>'
                '<tspan x="10" dy="28">Second</tspan>'
                '</text>',
                2,
            ),
            'single_inline': (
                '<text x="10" y="30" font-size="20">'
                'First <tspan font-weight="700">line</tspan>'
                '</text>',
                1,
            ),
        }
        for name, (text_svg, expected_lines) in cases.items():
            with self.subTest(name=name):
                root = _parse_svg(
                    '<g id="module" data-pptx-bounds="0 0 1000 1000">'
                    f'{text_svg}</g>'
                )
                text_element = root.find(f'.//{{{SVG_NS}}}text')
                parent_by_id = {
                    id(child): parent
                    for parent in root.iter()
                    for child in list(parent)
                }
                font_sizes = checker_module._resolve_project_font_sizes(root)
                letter_spacings = checker_module._resolve_project_letter_spacings(
                    root,
                    font_sizes,
                )
                bounds = SVGQualityChecker._estimated_text_bounds(
                    text_element,
                    parent_by_id,
                    font_sizes,
                    letter_spacings,
                )
                self.assertIsNotNone(bounds)
                if expected_lines == 2:
                    lines = SVGQualityChecker._positioned_text_lines(
                        text_element,
                        parent_by_id,
                        font_sizes,
                        letter_spacings,
                    )
                    self.assertEqual(len(lines), expected_lines)
                else:
                    runs = SVGQualityChecker._resolved_single_line_text_runs(
                        text_element,
                        parent_by_id,
                        font_sizes,
                        letter_spacings,
                    )
                    self.assertIsNotNone(runs)

    def test_module_bounds_use_headroom_but_page_bounds_do_not(self) -> None:
        root = _parse_svg(
            '<g id="module" data-pptx-bounds="0 0 100 100">'
            '<text id="text" x="0" y="20" font-size="12">Text</text>'
            '</g>'
        )
        include_headroom_calls = []

        def estimated_bounds(*_args, include_headroom=True, **_kwargs):
            include_headroom_calls.append(include_headroom)
            right = 106.0 if include_headroom else 100.0
            return (0.0, 0.0, right, 20.0)

        result = _empty_result()
        checker = SVGQualityChecker()
        with patch.object(
            checker,
            '_estimated_text_bounds',
            side_effect=estimated_bounds,
        ):
            checker._check_text_bounds(root, result)

        self.assertEqual(include_headroom_calls, [True, False])
        self.assertTrue(
            any('data-pptx-bounds' in error for error in result['errors'])
        )
        self.assertFalse(
            any('root viewBox' in error for error in result['errors'])
        )

    def test_horizontal_overflow_reports_per_cluster_width_and_capacity(
        self,
    ) -> None:
        cjk_text = '天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏'
        module_root = _parse_svg(
            '<g id="module" data-pptx-bounds="0 0 540 100">'
            f'<text x="0" y="30" font-size="24">{cjk_text}</text>'
            '</g>'
        )
        module_result = _empty_result()
        SVGQualityChecker()._check_text_bounds(module_root, module_result)
        module_error = next(
            error
            for error in module_result['errors']
            if 'data-pptx-bounds on the horizontal axis' in error
        )
        self.assertTrue(
            module_error.endswith(
                '≈25.4 px per CJK char at 24px incl. headroom; '
                '≈21 chars fit in 540 px'
            ),
            module_error,
        )

        page_root = _parse_svg(
            '<g id="module" data-pptx-bounds="0 0 1000 100">'
            f'<text x="0" y="30" font-size="24">{cjk_text}</text>'
            '</g>',
            view_box='0 0 540 100',
        )
        page_result = _empty_result()
        SVGQualityChecker()._check_text_bounds(page_root, page_result)
        page_error = next(
            error
            for error in page_result['errors']
            if 'exceeds the root viewBox on the horizontal axis' in error
        )
        self.assertTrue(
            page_error.endswith(
                '≈24.0 px per CJK char at 24px without headroom; '
                '≈22 chars fit in 540 px'
            ),
            page_error,
        )

    def test_root_module_overlap_is_error_with_minimal_exemptions(self) -> None:
        cases = (
            (
                'overlap_above_tolerance',
                _parse_svg(
                    '<g id="first" data-pptx-bounds="0 0 100 100"/>'
                    '<g id="second" data-pptx-bounds="98.9 0 100 100"/>'
                ),
                True,
            ),
            (
                'overlap_at_tolerance',
                _parse_svg(
                    '<g id="first" data-pptx-bounds="0 0 100 100"/>'
                    '<g id="second" data-pptx-bounds="99 0 100 100"/>'
                ),
                False,
            ),
            (
                'static_page_frame',
                _parse_svg(
                    '<g id="background" data-pptx-role="background" '
                    'data-pptx-bounds="0 0 1000 1000"/>'
                    '<g id="content" data-pptx-bounds="100 100 200 200"/>'
                ),
                False,
            ),
            (
                'structured_slots',
                _parse_svg(
                    '<g id="picture" data-pptx-placeholder="picture" '
                    'data-pptx-bounds="0 0 500 500"/>'
                    '<g id="title" data-pptx-placeholder="title" '
                    'data-pptx-bounds="100 100 300 100"/>',
                    'data-pptx-master="master" '
                    'data-pptx-master-name="Master" '
                    'data-pptx-layout="layout" '
                    'data-pptx-layout-name="Layout"',
                ),
                False,
            ),
            (
                'structured_ordinary_modules',
                _parse_svg(
                    '<g id="first" data-pptx-bounds="0 0 100 100"/>'
                    '<g id="second" data-pptx-bounds="50 0 100 100"/>',
                    'data-pptx-master="master" '
                    'data-pptx-master-name="Master" '
                    'data-pptx-layout="layout" '
                    'data-pptx-layout-name="Layout"',
                ),
                True,
            ),
            (
                'off_canvas_morph_staging',
                _parse_svg(
                    '<g id="morph-a" data-pptx-morph-staging="true" '
                    'data-pptx-bounds="1100 0 100 100"/>'
                    '<g id="morph-b" data-pptx-morph-staging="true" '
                    'data-pptx-bounds="1100 0 100 100"/>'
                ),
                False,
            ),
        )
        checker = SVGQualityChecker()
        for name, root, expects_overlap_error in cases:
            with self.subTest(name=name):
                result = _empty_result()
                checker._check_module_bounds_contract(root, result)
                overlap_errors = [
                    error
                    for error in result['errors']
                    if 'data-pptx-bounds overlaps' in error
                ]
                self.assertEqual(bool(overlap_errors), expects_overlap_error)


if __name__ == '__main__':
    unittest.main()
