#!/usr/bin/env python3
"""Focused tests for the authoring-time text measurement CLI."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.drawingml.elements import (  # noqa: E402
    estimate_single_line_text_frame_width,
)
from text_measure import (  # noqa: E402
    _render_wrapped_svg,
    measure_text,
    text_box,
    wrap_text,
)


SCRIPT = SCRIPTS_DIR / 'text_measure.py'
SAMPLE = 'Current macro-free package; the main editable format in modern PowerPoint'


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TextMeasureTests(unittest.TestCase):
    def test_measure_matches_checker_estimator(self) -> None:
        run = {
            'text': SAMPLE,
            'font_size': 22.0,
            'font_family': 'Calibri',
            'font_weight': 'normal',
            'letter_spacing': 0.0,
        }
        expected = estimate_single_line_text_frame_width([run])

        self.assertAlmostEqual(measure_text(SAMPLE, size=22), expected)
        result = _run_cli('measure', SAMPLE, '--size', '22')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f'880.4\t{SAMPLE}\n')

    def test_wrap_lines_never_exceed_max_width(self) -> None:
        max_width = 180.0
        lines, widths, oversized = wrap_text(
            'Editable DrawingML text stays measurable',
            size=22,
            max_width=max_width,
        )

        self.assertGreater(len(lines), 1)
        self.assertEqual(oversized, [])
        for line, width in zip(lines, widths):
            direct = measure_text(line, size=22)
            self.assertAlmostEqual(width, direct)
            self.assertLessEqual(direct, max_width)

    def test_oversized_token_is_emitted_alone_with_warning(self) -> None:
        token = 'UnbreakableToken'
        lines, widths, oversized = wrap_text(token, size=22, max_width=20)

        self.assertEqual(lines, [token])
        self.assertGreater(widths[0], 20)
        self.assertEqual(oversized, [(token, widths[0])])
        result = _run_cli(
            'wrap', token, '--size', '22', '--max-width', '20',
            '--x', '96', '--dy', '30',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f'{token}\n')
        self.assertIn('Warning: token exceeds max width', result.stderr)

    def test_cjk_wrap_keeps_closing_punctuation_with_previous_cluster(self) -> None:
        lines, widths, oversized = wrap_text('甲乙，丙丁', size=20, max_width=45)

        self.assertEqual(lines, ['甲', '乙，', '丙丁'])
        self.assertEqual(oversized, [])
        self.assertTrue(all(width <= 45 for width in widths))

    def test_box_arithmetic_and_anchor_adjustment(self) -> None:
        expected_x = {'start': 100.0, 'middle': 60.0, 'end': 20.0}
        for anchor, left in expected_x.items():
            with self.subTest(anchor=anchor):
                bounds = text_box(
                    x=100,
                    baseline_y=50,
                    size=20,
                    lines=2,
                    dy=24,
                    width=80,
                    anchor=anchor,
                )
                self.assertEqual(bounds['x'], left)
                self.assertEqual(bounds['y'], 33.0)
                self.assertEqual(bounds['width'], 80.0)
                self.assertEqual(bounds['height'], 48.0)
                self.assertEqual(bounds['top'], 33.0)
                self.assertEqual(bounds['bottom'], 81.0)

        result = _run_cli(
            'box', '--x', '100', '--y', '50', '--size', '20',
            '--lines', '2', '--dy', '24', '--width', '80', '--anchor', 'middle',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            'data-pptx-bounds="60 33 80 48"\ttop=33\tbottom=81\n',
        )

    def test_wrapped_svg_escapes_xml_text(self) -> None:
        rendered = _render_wrapped_svg(
            ['A & B', '<C>'],
            x=1.234,
            dy=20,
            y=10,
        )

        self.assertEqual(
            rendered,
            '<text x="1.23" y="10">A &amp; B'
            '<tspan x="1.23" dy="20">&lt;C&gt;</tspan></text>',
        )


if __name__ == '__main__':
    unittest.main()
