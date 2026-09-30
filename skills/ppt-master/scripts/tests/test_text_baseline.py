#!/usr/bin/env python3
"""
PPT Master - Native Text Baseline Regression Tests

Check exported frame positions against PowerPoint-rendered baseline samples.
Fixtures are self-contained and never read installed fonts.

Usage:
    python3 -m unittest tests.test_text_baseline

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local SVG-to-PPTX converter.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}
EMU_PER_PX = 9525


class TextBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.svg_path = self.root / '01_baseline.svg'

    def _export(self, body: str, *, text_flow: str = 'split') -> ET.Element:
        self.svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
            f'{body}</svg>',
            encoding='utf-8',
        )
        xml, *_rest = convert_svg_to_slide_shapes(
            self.svg_path, resource_root=self.root, text_flow=text_flow,
        )
        return ET.fromstring(xml)

    def _assert_top(self, shape: ET.Element, expected_px: float) -> None:
        offset = shape.find('p:spPr/a:xfrm/a:off', NS)
        self.assertIsNotNone(offset)
        self.assertAlmostEqual(
            int(offset.get('y')), expected_px * EMU_PER_PX, delta=1,
        )

    def _single_shape(self, slide: ET.Element) -> ET.Element:
        shapes = slide.findall('.//p:sp', NS)
        self.assertEqual(len(shapes), 1)
        return shapes[0]

    def test_default_spacing_uses_each_fonts_rendered_baseline(self) -> None:
        # Mac PowerPoint 16.113.2: observed offsets rounded to the native pt grid.
        samples = (
            ('Arial', 38.6666666667),
            ('Calibri', 37.3333333333),
            ('SimSun', 41.3333333333),
            ('SimHei', 41.3333333333),
            ('Microsoft YaHei', 38.6666666667),
        )
        for family, baseline_offset in samples:
            with self.subTest(family=family):
                slide = self._export(
                    f'<text x="100" y="200" font-size="40" '
                    f'font-family="{family}">Hgpq</text>'
                )
                shape = self._single_shape(slide)
                self._assert_top(shape, 200 - baseline_offset)
                self.assertIsNone(shape.find('.//a:lnSpc', NS))
                body = shape.find('p:txBody/a:bodyPr', NS)
                self.assertEqual(body.get('tIns'), '0')
                self.assertEqual(body.get('anchor'), 't')

    def test_font_metric_fields_distinguish_windows_and_typographic_metrics(self) -> None:
        for family, size, expected_offset in (
            ('Candara', 40, 37.3333333333),
            ('Aptos', 80, 73.3333333333),
            ('Segoe UI', 24, 24.0),
        ):
            with self.subTest(family=family):
                slide = self._export(
                    f'<text x="100" y="200" font-size="{size}" '
                    f'font-family="{family}">Hgpq</text>'
                )
                self._assert_top(self._single_shape(slide), 200 - expected_offset)

    def test_half_point_baseline_rounds_up(self) -> None:
        # The rendered 64 px SimSun sample resolves a 49.5 pt offset to 50 pt.
        slide = self._export(
            '<text x="100" y="200" font-size="64" font-family="SimSun">Hgpq</text>'
        )
        self._assert_top(self._single_shape(slide), 133.3333333333)

    def test_family_alias_and_unknown_family_have_deterministic_positions(self) -> None:
        for family in ('微软雅黑', 'Noto Sans SC', 'Unlisted Baseline Test Font'):
            with self.subTest(family=family):
                slide = self._export(
                    f'<text x="100" y="200" font-size="40" '
                    f'font-family="{family}">Hgpq</text>'
                )
                self._assert_top(self._single_shape(slide), 161.3333333333)

    def test_larger_font_size_controls_mixed_size_line_in_either_order(self) -> None:
        for sizes, expected_top in (
            ((20, 40), 161.3333333333),
            ((40, 20), 161.3333333333),
            ((24, 64), 138.6666666667),
            ((64, 24), 138.6666666667),
        ):
            with self.subTest(sizes=sizes):
                slide = self._export(
                    '<text x="100" y="200" font-size="20" font-family="Microsoft YaHei">'
                    f'<tspan font-size="{sizes[0]}">Hg</tspan>'
                    f'<tspan font-size="{sizes[1]}">pq</tspan></text>'
                )
                shape = self._single_shape(slide)
                self._assert_top(shape, expected_top)
                self.assertEqual(len(shape.findall('.//a:r', NS)), 2)

    def test_mixed_scripts_use_both_active_font_faces(self) -> None:
        for text in ('Hg中文pq', '中文Hgpq'):
            with self.subTest(text=text):
                slide = self._export(
                    '<text x="100" y="200" font-size="40" '
                    f'font-family="Calibri, SimSun">{text}</text>'
                )
                self._assert_top(self._single_shape(slide), 161.3333333333)

    def test_unused_east_asian_font_does_not_affect_latin_baseline(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" '
            'font-family="Calibri, SimSun">Hgpq</text>'
        )
        self._assert_top(self._single_shape(slide), 162.6666666667)

    def test_mixed_font_runs_share_position_regardless_of_order(self) -> None:
        runs = (
            '<tspan font-family="Calibri">Hg</tspan>',
            '<tspan font-family="SimSun">中文</tspan>',
        )
        for ordered_runs in (runs, runs[::-1]):
            with self.subTest(runs=ordered_runs):
                slide = self._export(
                    '<text x="100" y="200" font-size="40">'
                    + ''.join(ordered_runs) + '</text>'
                )
                self._assert_top(self._single_shape(slide), 161.3333333333)

    def test_preserved_lines_follow_fixed_spacing_baseline_transition(self) -> None:
        samples = (
            (40, '45.3333333333333', '3400', 164.0),
            (40, '48', '3600', 161.3333333333),
            (40, '49.3333333333333', '3700', 162.6666666667),
            # PowerPoint rounds 57.6 pt fixed spacing to 58 pt before choosing
            # the baseline branch, while the stored OOXML retains 5760.
            (64, '76.8', '5760', 141.3333333333),
        )
        for size, dy, spacing, expected_top in samples:
            with self.subTest(size=size, dy=dy):
                slide = self._export(
                    f'<text x="100" y="200" font-size="{size}" font-family="Microsoft YaHei">'
                    '<tspan x="100" dy="0">第一行</tspan>'
                    f'<tspan x="100" dy="{dy}">第二行</tspan></text>',
                    text_flow='preserve',
                )
                shape = self._single_shape(slide)
                self._assert_top(shape, expected_top)
                self.assertEqual(
                    [node.get('val') for node in shape.findall('.//a:lnSpc/a:spcPts', NS)],
                    [spacing],
                )
                self.assertEqual(len(shape.findall('.//a:br', NS)), 1)
                break_properties = shape.find('.//a:br/a:rPr', NS)
                self.assertIsNotNone(break_properties)
                self.assertEqual(break_properties.get('sz'), '4800' if size == 64 else '3000')
                self.assertEqual(
                    break_properties.find('a:latin', NS).get('typeface'), 'Microsoft YaHei',
                )
                self.assertEqual(
                    break_properties.find('a:ea', NS).get('typeface'), 'Microsoft YaHei',
                )

    def test_split_lines_each_use_their_own_default_spacing_baseline(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei">'
            '<tspan x="100" dy="0">第一行</tspan>'
            '<tspan x="100" dy="48">第二行</tspan></text>'
        )
        shapes = slide.findall('.//p:sp', NS)
        self.assertEqual(len(shapes), 2)
        for shape, expected_top in zip(shapes, (161.3333333333, 209.3333333333)):
            self._assert_top(shape, expected_top)
            self.assertIsNone(shape.find('.//a:lnSpc', NS))

    def test_larger_later_line_does_not_move_first_visual_line(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei">'
            '<tspan x="100" dy="0">第一行</tspan>'
            '<tspan x="100" dy="48" font-size="64">第二行</tspan></text>',
            text_flow='preserve',
        )
        shape = self._single_shape(slide)
        self._assert_top(shape, 161.3333333333)
        self.assertEqual(
            [run.get('sz') for run in shape.findall('.//a:rPr', NS)],
            ['3000', '4800'],
        )
        self.assertEqual(
            [spacing.get('val') for spacing in shape.findall('.//a:lnSpc/a:spcPts', NS)],
            ['3600', '3600'],
        )

    def test_relative_group_font_size_is_resolved_once_for_baseline(self) -> None:
        # Text-bearing group transforms reject scale; inherited em sizes are
        # the supported public converter path for this effective-size check.
        slide = self._export(
            '<g font-size="20">'
            '<text x="100" y="200" font-size="2em" font-family="Microsoft YaHei">'
            'Hgpq</text></g>'
        )
        shape = self._single_shape(slide)
        self._assert_top(shape, 161.3333333333)
        self.assertEqual(shape.find('.//a:rPr', NS).get('sz'), '3000')

    def test_extracted_bullet_size_does_not_move_the_text_baseline(self) -> None:
        for marker_size in (40, 80):
            with self.subTest(marker_size=marker_size):
                slide = self._export(
                    '<text x="100" y="200" font-size="40" font-family="Calibri">'
                    '<tspan x="100" dy="0">'
                    f'<tspan font-size="{marker_size}">• </tspan>First</tspan>'
                    '<tspan x="100" dy="48">Second</tspan></text>',
                    text_flow='preserve',
                )
                shape = self._single_shape(slide)
                self._assert_top(shape, 162.6666666667)
                paragraph = shape.find('.//a:pPr', NS)
                self.assertIsNotNone(paragraph.find('a:buSzTx', NS))
                self.assertIsNotNone(paragraph.find('a:buFontTx', NS))
                self.assertEqual(paragraph.find('a:buChar', NS).get('char'), '•')
                self.assertEqual(
                    [run.get('sz') for run in shape.findall('.//a:r/a:rPr', NS)],
                    ['3000', '3000'],
                )
                self.assertEqual(shape.find('.//a:br/a:rPr', NS).get('sz'), '3000')
                self.assertEqual(
                    [text.text for text in shape.findall('.//a:t', NS)],
                    ['First', 'Second'],
                )

    def test_missing_bold_italic_metrics_fall_back_to_the_bold_face(self) -> None:
        # Yu Gothic bundles regular and bold, but no italic metrics; synthetic
        # italic must preserve the selected weight's baseline rather than reset it.
        offsets = {}
        for weight, style in (('400', 'normal'), ('bold', 'normal'), ('bold', 'italic')):
            slide = self._export(
                '<text x="100" y="200" font-size="140" font-family="Yu Gothic" '
                f'font-weight="{weight}" font-style="{style}">Hgpq</text>'
            )
            shape = self._single_shape(slide)
            offsets[weight, style] = shape.find('p:spPr/a:xfrm/a:off', NS).get('y')
            run = shape.find('.//a:rPr', NS)
            self.assertEqual(run.get('b'), '1' if weight == 'bold' else None)
            self.assertEqual(run.get('i'), '1' if style == 'italic' else None)
        self.assertNotEqual(offsets['400', 'normal'], offsets['bold', 'normal'])
        self.assertEqual(offsets['bold', 'normal'], offsets['bold', 'italic'])

    def test_mixed_size_frame_contains_the_larger_fonts_line_height(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="20" font-family="Microsoft YaHei">'
            '<tspan font-size="20">Hg</tspan><tspan font-size="64">pq</tspan></text>'
        )
        shape = self._single_shape(slide)
        self._assert_top(shape, 138.6666666667)
        height_px = int(shape.find('p:spPr/a:xfrm/a:ext', NS).get('cy')) / EMU_PER_PX
        # A 64 px run needs its 76.8 px natural line, even when its parent is 20 px.
        self.assertGreaterEqual(height_px, 76.8)
        self.assertEqual(
            [run.get('sz') for run in shape.findall('.//a:rPr', NS)],
            ['1500', '4800'],
        )

    def test_super_and_subscript_keep_existing_shifted_run_positioning(self) -> None:
        for shift, drawingml_shift in (('super', '30000'), ('sub', '-25000')):
            with self.subTest(shift=shift):
                slide = self._export(
                    '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei">'
                    f'Hg<tspan baseline-shift="{shift}">2</tspan>pq</text>'
                )
                shape = self._single_shape(slide)
                self._assert_top(shape, 166)
                self.assertEqual(
                    [run.get('baseline') for run in shape.findall('.//a:rPr', NS)
                     if run.get('baseline') is not None],
                    [drawingml_shift],
                )

    def test_exact_imported_frame_preserves_frame_and_inset_reconstruction(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei" '
            'data-pptx-frame="80 100 500 200">Hgpq</text>'
        )
        shape = self._single_shape(slide)
        self._assert_top(shape, 100)
        self.assertEqual(
            shape.find('p:spPr/a:xfrm/a:ext', NS).attrib,
            {'cx': '4762500', 'cy': '1905000'},
        )
        self.assertEqual(shape.find('p:txBody/a:bodyPr', NS).get('tIns'), '628650')

    def test_inline_formula_retains_native_math_positioning(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei">'
            'Hg<tspan data-pptx-inline-formula="x">x</tspan>pq</text>'
        )
        shape = self._single_shape(slide)
        self._assert_top(shape, 166)
        self.assertIsNotNone(shape.find('.//m:oMath', NS))
