#!/usr/bin/env python3
"""Focused tests for the authoring-time text measurement CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.drawingml.elements import (  # noqa: E402
    estimate_single_line_text_frame_width,
)
from svg_to_pptx.drawingml.utils import estimate_text_cluster_widths  # noqa: E402
from text_measure import (  # noqa: E402
    _CLOSING_PUNCTUATION,
    _OPENING_PUNCTUATION,
    _render_wrapped_svg,
    measure_text,
    text_box,
    wrap_text,
)
from svg_quality.checker import SVGQualityChecker  # noqa: E402


SCRIPT = SCRIPTS_DIR / 'text_measure.py'
SAMPLE = 'Current macro-free package; the main editable format in modern PowerPoint'
CJK_PARAGRAPHS = (
    '通体蓝瓦圆顶对应天穹，不靠体量压人，而用“圆”与“空”消解人与天地的隔阂；'
    '蓝瓦贴合青天之色，模糊人间与天宇的边界。',
    '三层汉白玉圆台层层递进，暗藏天时历法；古人在此祭天，以高台承接天地阳气，'
    '把四时流转、阴阳交替的规律固化为仪式。',
)


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
        self.assertEqual(result.stdout, f'736.5\t{SAMPLE}\n')

    def test_arial_raw_width_matches_reference_lines(self) -> None:
        cases = (
            (
                'The dissemination layer covers the poster you stand next to at a conference session',
                16, 'normal', 596,
            ),
            (
                'The fill loop is discrete: five verdict bands, one section edited per round,',
                28, 'bold', 966,
            ),
        )
        for text, size, weight, expected in cases:
            with self.subTest(weight=weight):
                actual = measure_text(
                    text, size=size, family='Arial', weight=weight,
                    include_headroom=False,
                )
                self.assertAlmostEqual(actual, expected, delta=expected * 0.02)

    def test_unknown_family_keeps_crude_width(self) -> None:
        text = 'The dissemination layer covers the poster you stand next to at a conference session'
        crude = sum(estimate_text_cluster_widths(text, 16))
        self.assertAlmostEqual(crude, 661.6)
        for family in ('Segoe UI', 'Unlisted Sans', 'Segoe UI, Arial'):
            with self.subTest(family=family):
                self.assertEqual(
                    measure_text(text, size=16, family=family, include_headroom=False),
                    crude,
                )

    def test_bundled_families_use_each_run_style(self) -> None:
        # Sum of the supplied A, i, W, and e-acute advances in each face.
        advances = {
            'Arial': (2.3892, 2.5, 2.3892, 2.5),
            'Times New Roman': (2.3876, 2.4438, 2.1654, 2.2778),
            'Georgia': (2.4229, 2.8101, 2.4156, 2.8076),
            'Verdana': (2.5425, 2.9107, 2.5429, 2.9107),
            'Calibri': (2.1954, 2.2612, 2.1757, 2.2495),
        }
        styles = (
            ('400', 'normal'), ('bold', 'normal'),
            ('400', 'italic'), ('bold', 'italic'),
        )
        for family, widths in advances.items():
            for (weight, style), width in zip(styles, widths):
                with self.subTest(family=family, weight=weight, style=style):
                    run = dict(
                        text='AiWé', font_size=20, font_family=family,
                        font_weight=weight, font_style=style,
                    )
                    self.assertAlmostEqual(
                        estimate_single_line_text_frame_width([run], include_headroom=False),
                        width * 20,
                    )

    def test_primary_family_and_style_aliases(self) -> None:
        for family in ('Arial', '  "ARIAL", sans-serif', "'arial', Consolas"):
            for weight in ('bold', '600', '700', '800', '900'):
                with self.subTest(family=family, weight=weight):
                    self.assertAlmostEqual(
                        measure_text('AiWé', size=20, family=family, weight=weight,
                                     include_headroom=False),
                        50.0,
                    )
        for weight, advance in (('500', 2.1654), ('600', 2.2778)):
            run = dict(
                text='AiWé', font_size=20, font_family='Times New Roman',
                font_weight=weight, font_style='oblique',
            )
            self.assertAlmostEqual(
                estimate_single_line_text_frame_width([run], include_headroom=False),
                advance * 20,
            )

    def test_mixed_cjk_and_latin_uses_separate_advances(self) -> None:
        for weight, latin in (('normal', 0.667 + 0.2222), ('bold', 0.7222 + 0.2778)):
            with self.subTest(weight=weight):
                self.assertAlmostEqual(
                    measure_text('中A文i', size=20, family='Arial', weight=weight,
                                 include_headroom=False),
                    (2 + latin) * 20,
                )

    def test_missing_glyph_falls_back_for_its_cluster_only(self) -> None:
        for weight, expected in (
            ('400', [0.667, 0.55, 0.2222]),
            ('bold', [0.7222, 0.55 * 1.05, 0.2778]),
        ):
            with self.subTest(weight=weight):
                self.assertEqual(
                    estimate_text_cluster_widths('AΩi', 16, weight, font_family='Arial'),
                    [advance * 16 for advance in expected],
                )
                self.assertAlmostEqual(
                    measure_text('AΩi', size=16, family='Arial', weight=weight,
                                 include_headroom=False),
                    sum(expected) * 16,
                )

    def test_extended_clusters_keep_existing_widths_and_tracking(self) -> None:
        text = 'e\u0301👩🏽‍💻🇨🇳1️⃣Ａｱ'
        for weight in ('400', 'bold'):
            with self.subTest(weight=weight):
                crude = estimate_text_cluster_widths(text, 20, weight)
                self.assertEqual(
                    estimate_text_cluster_widths(text, 20, weight, font_family='Arial'),
                    crude,
                )
                self.assertAlmostEqual(
                    measure_text(text, size=20, family='Arial', weight=weight,
                                 letter_spacing=2, include_headroom=False),
                    sum(crude) + 2 * (len(crude) - 1),
                )

    def test_arial_black_keeps_wide_family_factor(self) -> None:
        crude = sum(estimate_text_cluster_widths('CAPS', 20, 'bold'))
        self.assertAlmostEqual(
            measure_text('CAPS', size=20, family='Arial Black', weight='bold',
                         include_headroom=False),
            crude * 1.25,
        )

    def test_monospace_families_measure_fixed_pitch(self) -> None:
        text = "WHERE table = 'x'"
        consolas = measure_text(
            text, size=20, family='Consolas', include_headroom=False,
        )
        courier = measure_text(
            text, size=20, family='Courier New', include_headroom=False,
        )
        unlisted = measure_text(
            text, size=20, family='Victor Mono', include_headroom=False,
        )
        arial = measure_text(
            text, size=20, family='Arial', include_headroom=False,
        )
        self.assertAlmostEqual(consolas, len(text) * 0.55 * 20)
        self.assertAlmostEqual(courier, len(text) * 0.60 * 20, delta=1.0)
        self.assertAlmostEqual(unlisted, courier, delta=0.01)
        self.assertGreater(consolas, arial)
        # Weight never changes a fixed-pitch advance.
        self.assertAlmostEqual(
            measure_text(
                text, size=20, family='Consolas', weight='bold',
                include_headroom=False,
            ),
            consolas,
            delta=0.01,
        )

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

    def test_wrap_can_request_raw_width_without_headroom(self) -> None:
        with_headroom = measure_text(SAMPLE, size=22)
        raw = measure_text(SAMPLE, size=22, include_headroom=False)

        self.assertGreater(with_headroom, raw)
        result = _run_cli(
            'wrap', SAMPLE, '--size', '22', '--max-width', '900',
            '--x', '96', '--dy', '30', '--no-headroom', '--json',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['widths'], [raw])

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

    def test_cjk_wrap_fits_checker_module_bounds_and_obeys_line_punctuation(self) -> None:
        groups: list[str] = []
        for index, paragraph in enumerate(CJK_PARAGRAPHS):
            lines, widths, oversized = wrap_text(
                paragraph,
                size=24,
                family='Microsoft YaHei',
                max_width=540,
            )

            self.assertEqual(oversized, [])
            self.assertTrue(all(width <= 540 for width in widths))
            for line in lines:
                self.assertNotIn(line[0], _CLOSING_PUNCTUATION)
                self.assertNotIn(line[-1], _OPENING_PUNCTUATION)

            top = index * 180
            rendered = _render_wrapped_svg(
                lines,
                x=100,
                y=top + 30,
                dy=36,
            )
            groups.append(
                f'<g id="module-{index}" data-pptx-bounds="100 {top} 540 160">'
                f'{rendered}</g>'
            )

        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'font-family="Microsoft YaHei" font-size="24">'
            + ''.join(groups)
            + '</svg>'
        )
        result = {'warnings': [], 'errors': [], 'info': {}}
        SVGQualityChecker()._check_text_bounds(root, result)

        self.assertEqual(result['warnings'], [])
        self.assertEqual(result['errors'], [])

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
