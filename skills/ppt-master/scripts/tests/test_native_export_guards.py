#!/usr/bin/env python3
"""Regression tests for native export guards and SVG fidelity."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_shapes.formula import OOXML_COORDINATE_MAX  # noqa: E402
from pptx_gradients import native_gradient_metadata, preserved_native_gradient_xml  # noqa: E402
from svg_finalize.flatten_tspan import flatten_text_with_tspans  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_to_pptx.drawingml.converter import (  # noqa: E402
    SvgNativeConversionError,
    convert_svg_to_slide_shapes,
)
from svg_to_pptx.drawingml.styles import build_gradient_fill  # noqa: E402


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}


class NativeExportGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.svg_path = self.root / '01_fixture.svg'

    def _svg(self, body: str, attributes: str = '') -> None:
        self.svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            f'data-pptx-page-role="content" {attributes}>{body}</svg>',
            encoding='utf-8',
        )

    def _export(self) -> ET.Element:
        xml, *_rest = convert_svg_to_slide_shapes(self.svg_path, resource_root=self.root)
        return ET.fromstring(xml)

    def _check(self) -> dict:
        return SVGQualityChecker(quick_generate=True).check_file(str(self.svg_path))

    @staticmethod
    def _shape_colors(slide: ET.Element) -> list[str]:
        return [
            color.get('val')
            for color in slide.findall('.//p:sp/p:spPr/a:solidFill/a:srgbClr', NS)
        ]

    def test_huge_coordinate_export_fails_with_page_and_element(self) -> None:
        for transform in ('', 'transform="matrix(1 0 0 1 0 0)"'):
            with self.subTest(transform=transform):
                self._svg(
                    f'<rect id="huge" x="100000000000000000000000000000000000" y="100" width="200" height="100" '
                    f'fill="#FF0000" {transform}/>'
                )
                with self.assertRaises(SvgNativeConversionError) as caught:
                    self._export()
                self.assertIn('01_fixture.svg', str(caught.exception))
                self.assertIn('huge', str(caught.exception))
                self.assertIn('OOXML coordinate range', str(caught.exception))

    def test_checker_rejects_oversized_offsets_and_extents(self) -> None:
        for attribute in ('x', 'y', 'width', 'height'):
            with self.subTest(attribute=attribute):
                values = dict(x='100', y='100', width='200', height='100')
                values[attribute] = '100000000000000000000000000000000000'
                geometry = ' '.join(f'{key}="{value}"' for key, value in values.items())
                self._svg(f'<rect id="huge" {geometry} fill="#FF0000"/>')
                errors = self._check()['errors']
                self.assertTrue(any('huge' in error and 'OOXML' in error for error in errors), errors)
                with self.assertRaises(SvgNativeConversionError):
                    self._export()

    def test_coordinates_inside_ooxml_range_still_export(self) -> None:
        for x in (-10, OOXML_COORDINATE_MAX // 9525):
            with self.subTest(x=x):
                self._svg(f'<rect id="valid" x="{x}" y="100" width="20" height="10" fill="#123456"/>')
                self.assertFalse(self._check()['errors'])
                self.assertEqual(self._shape_colors(self._export()), ['123456'])

    def test_hidden_rect_is_omitted_for_attributes_and_style(self) -> None:
        for hiding in ('visibility="hidden"', 'style="visibility:hidden"',
                       'display="none"', 'style="display:none"'):
            with self.subTest(hiding=hiding):
                self._svg(
                    f'<rect id="hidden" x="100" y="100" width="200" height="100" fill="#FF0000" {hiding}/>'
                    '<rect id="shown" x="400" y="100" width="200" height="100" fill="#00FF00"/>'
                )
                self.assertEqual(self._shape_colors(self._export()), ['00FF00'])
                report = self._check()
                self.assertFalse(report['errors'])
                self.assertTrue(any('hidden' in warning and 'not be exported' in warning
                                    for warning in report['warnings']), report['warnings'])

    def test_display_none_group_cannot_be_overridden_by_descendants(self) -> None:
        for hiding in ('display="none"', 'style="display:none"'):
            with self.subTest(hiding=hiding):
                self._svg(
                    f'<g id="hidden-group" {hiding}>'
                    '<g display="inline" visibility="visible">'
                    '<rect id="child" x="100" y="100" width="200" height="100" fill="#FF0000"/>'
                    '</g></g>'
                )
                self.assertEqual(self._shape_colors(self._export()), [])
                warnings = self._check()['warnings']
                self.assertTrue(any('hidden-group' in warning and 'display:none' in warning
                                    for warning in warnings), warnings)

    def test_hidden_group_allows_explicitly_visible_descendant(self) -> None:
        for hiding, showing in (
            ('visibility="hidden"', 'visibility="visible"'),
            ('style="visibility:hidden"', 'style="visibility:visible"'),
        ):
            with self.subTest(hiding=hiding):
                self._svg(
                    f'<g id="hidden-group" {hiding}>'
                    '<rect id="hidden-child" x="100" y="100" width="200" height="100" fill="#FF0000"/>'
                    f'<g><rect id="shown" {showing} x="400" y="100" width="200" height="100" fill="#00FF00"/>'
                    '</g></g>'
                )
                self.assertEqual(self._shape_colors(self._export()), ['00FF00'])
                warnings = self._check()['warnings']
                self.assertTrue(any('hidden-child' in warning and 'visibility:hidden' in warning
                                    for warning in warnings), warnings)
                self.assertFalse(any('shown' in warning and 'not be exported' in warning for warning in warnings))

    def test_style_visibility_overrides_presentation_attribute(self) -> None:
        self._svg(
            '<rect id="shown" x="100" y="100" width="200" height="100" fill="#123456" '
            'visibility="hidden" style="visibility:visible"/>'
        )
        self.assertEqual(self._shape_colors(self._export()), ['123456'])

    def test_hidden_background_is_not_promoted(self) -> None:
        for body, attributes in (
            ('<rect width="1280" height="720" fill="#FF0000" visibility="hidden"/>', ''),
            ('<g display="none"><rect width="1280" height="720" fill="#FF0000"/></g>', ''),
            ('<rect width="1280" height="720" fill="#FF0000"/>', 'display="none"'),
        ):
            with self.subTest(body=body, attributes=attributes):
                self._svg(body, attributes)
                slide = self._export()
                self.assertIsNone(slide.find('p:cSld/p:bg', NS))
                self.assertEqual(self._shape_colors(slide), [])

    def test_native_geometry_carrier_survives_but_ancestor_can_hide_it(self) -> None:
        carrier = (
            '<path id="carrier" d="M 100 100 L 300 100 L 300 200 L 100 200 Z" '
            'fill="#123456" data-pptx-prst="rect" data-pptx-frame="100 100 200 100" '
            'data-pptx-object="shape" data-pptx-shape-id="2" data-pptx-part="geometry" '
            'visibility="hidden" pointer-events="none"/>'
        )
        self._svg(carrier)
        slide = self._export()
        self.assertEqual(self._shape_colors(slide), ['123456'])
        self.assertEqual(slide.find('.//p:sp/p:nvSpPr/p:cNvPr', NS).get('id'), '2')
        self.assertFalse(any('carrier' in warning and 'not be exported' in warning
                             for warning in self._check()['warnings']))
        self._svg(f'<g visibility="hidden">{carrier}</g>')
        self.assertEqual(self._shape_colors(self._export()), [])

    def _pattern(self, paints: str, attributes: str = 'data-pptx-pattern="smGrid"') -> None:
        self._svg(
            f'<defs><pattern id="pat" {attributes} patternUnits="userSpaceOnUse" '
            f'width="10" height="10">{paints}</pattern></defs>'
            '<rect id="pattern-shape" x="100" y="100" width="200" height="100" fill="url(#pat)"/>'
        )

    def test_pattern_missing_foreground_fails_checker_and_export(self) -> None:
        self._pattern('<rect width="10" height="10" fill="#FF0000"/>')
        errors = self._check()['errors']
        self.assertTrue(any('pat' in error and 'foreground' in error and 'data-pptx-fg' in error
                            for error in errors), errors)
        with self.assertRaisesRegex(SvgNativeConversionError, 'foreground'):
            self._export()

    def test_complete_pattern_exports_native_fill(self) -> None:
        self._pattern(
            '<rect width="10" height="10" fill="#FFFFFF"/>'
            '<path d="M 0 0 L 10 10" stroke="#123456"/>'
        )
        self.assertFalse(self._check()['errors'])
        pattern = self._export().find('.//a:pattFill', NS)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.get('prst'), 'smGrid')
        self.assertEqual(pattern.find('a:fgClr/a:srgbClr', NS).get('val'), '123456')
        self.assertEqual(pattern.find('a:bgClr/a:srgbClr', NS).get('val'), 'FFFFFF')

    def test_pattern_metadata_and_child_alpha_remain_supported(self) -> None:
        self._pattern(
            '<rect width="10" height="10" style="fill:#FFFFFF;fill-opacity:0.5"/>'
            '<path d="M 0 0 L 10 10" style="stroke:#123456;stroke-opacity:0.25"/>',
            'data-pptx-pattern="smGrid" data-pptx-fg="#123456" data-pptx-bg="#FFFFFF"',
        )
        self.assertFalse(self._check()['errors'])
        pattern = self._export().find('.//a:pattFill', NS)
        self.assertEqual(pattern.find('a:fgClr/a:srgbClr/a:alpha', NS).get('val'), '25000')
        self.assertEqual(pattern.find('a:bgClr/a:srgbClr/a:alpha', NS).get('val'), '50000')

    def test_unmarked_pattern_keeps_missing_foreground_fallback(self) -> None:
        self._pattern('<rect width="10" height="10" fill="#FF0000"/>', '')
        self.assertFalse(self._check()['errors'])
        slide = self._export()
        self.assertIsNone(slide.find('.//a:pattFill', NS))
        self.assertIsNotNone(slide.find('.//p:sp/p:spPr/a:noFill', NS))

    def test_single_child_rotation_matches_direct_transform(self) -> None:
        for child in (
            '<text x="100" y="120" {transform}>ABC</text>',
            '<rect x="100" y="120" width="80" height="30" {transform}/>',
        ):
            with self.subTest(child=child):
                transform = 'transform="rotate(90 100 120)"'
                self._svg(child.format(transform=transform), 'font-family="Arial" font-size="20"')
                direct = self._export().find('.//p:sp/p:spPr/a:xfrm', NS)
                self._svg(
                    f'<g {transform}>{child.format(transform="")}</g>',
                    'font-family="Arial" font-size="20"',
                )
                grouped = self._export()
                rotated = grouped.find('.//a:xfrm[@rot]', NS)
                self.assertIsNotNone(rotated)
                self.assertEqual(rotated.get('rot'), direct.get('rot'))
                self.assertEqual(rotated.find('a:off', NS).attrib, direct.find('a:off', NS).attrib)
                self.assertEqual(rotated.find('a:ext', NS).attrib, direct.find('a:ext', NS).attrib)

    def test_multiple_child_rotation_keeps_group_frame(self) -> None:
        self._svg(
            '<g transform="rotate(90 100 120)"><text x="100" y="120">ABC</text>'
            '<rect x="160" y="110" width="40" height="20"/></g>',
            'font-family="Arial" font-size="20"',
        )
        group = self._export().find('.//p:grpSp', NS)
        self.assertEqual(len(group.findall('p:sp', NS)), 2)
        frame = group.find('p:grpSpPr/a:xfrm', NS)
        self.assertEqual(frame.get('rot'), '5400000')
        self.assertEqual(frame.find('a:off', NS).attrib, {'x': '487680', 'y': '1468755'})
        self.assertEqual(frame.find('a:chOff', NS).attrib, {'x': '944880', 'y': '981075'})
        self.assertFalse(group.findall('p:sp/p:spPr/a:xfrm[@rot]', NS))

    def test_single_rect_matrix_matches_direct_geometry_and_skew_stays_rejected(self) -> None:
        for transform in ('matrix(0 1 -1 0 220 20)', 'matrix(2 0 0 3 10 20)'):
            with self.subTest(transform=transform):
                rect = '<rect x="100" y="120" width="80" height="30" {transform}/>'
                self._svg(rect.format(transform=f'transform="{transform}"'))
                direct = self._export().find('.//p:sp/p:spPr', NS)
                self._svg(f'<g transform="{transform}">{rect.format(transform="")}</g>')
                grouped = self._export().find('.//p:sp/p:spPr', NS)
                self.assertEqual(ET.tostring(grouped), ET.tostring(direct))
        for transform in ('matrix(1 0 0.36 1 0 0)', 'skewX(20)'):
            for body in (
                '<rect x="100" y="120" width="80" height="30" transform="{transform}"/>',
                '<g transform="{transform}"><rect x="100" y="120" width="80" height="30"/></g>',
            ):
                with self.subTest(transform=transform, body=body):
                    self._svg(body.format(transform=transform))
                    with self.assertRaisesRegex(SvgNativeConversionError, 'skew|skewX'):
                        self._export()

    def test_root_opacity_multiplies_group_and_fill_opacity(self) -> None:
        for attributes in ('opacity="0.5"', 'style="opacity:0.5"', 'opacity="0.8" style="opacity:0.5"'):
            for group_opacity, expected in (('1', '50000'), ('0.5', '25000')):
                with self.subTest(attributes=attributes, group_opacity=group_opacity):
                    self._svg(
                        f'<g opacity="{group_opacity}" data-pptx-bounds="50 50 500 300">'
                        '<rect x="100" y="100" width="200" height="100" fill="#FF0000"/></g>',
                        attributes,
                    )
                    self.assertFalse(self._check()['errors'])
                    alpha = self._export().find('.//p:sp/p:spPr/a:solidFill/a:srgbClr/a:alpha', NS)
                    self.assertIsNotNone(alpha)
                    self.assertEqual(alpha.get('val'), expected)
        self._svg('<rect width="1280" height="720" fill="#FF0000"/>', 'opacity="0"')
        self.assertEqual(self._export().find('.//a:alpha', NS).get('val'), '0')
        self._svg(
            '<rect x="100" y="100" width="200" height="100" fill="#FF0000"/>',
            'opacity="0.5" fill-opacity="0.5"',
        )
        self.assertEqual(self._export().find('.//a:alpha', NS).get('val'), '25000')

    def _native_gradient(self, alpha: str = '') -> ET.Element:
        gradient = ET.fromstring(
            '<linearGradient xmlns="http://www.w3.org/2000/svg" id="g" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#FF0000"/><stop offset="1" stop-color="#0000FF"/>'
            '</linearGradient>'
        )
        native = ET.fromstring(
            f'<a:gradFill xmlns:a="{NS["a"]}"><a:gsLst>'
            f'<a:gs pos="0"><a:srgbClr val="FF0000">{alpha}</a:srgbClr></a:gs>'
            '<a:gs pos="100000"><a:schemeClr val="accent1"/></a:gs>'
            '</a:gsLst><a:lin ang="0" scaled="1"/></a:gradFill>'
        )
        gradient.attrib.update(native_gradient_metadata(native, gradient))
        return gradient

    def test_native_gradient_opacity_uses_copy_and_preserves_identity(self) -> None:
        for source_alpha, expected in (('', '50000'), ('<a:alpha val="33333"/>', '16667')):
            with self.subTest(source_alpha=source_alpha):
                gradient = self._native_gradient(source_alpha)
                original = preserved_native_gradient_xml(gradient)
                attributes = dict(gradient.attrib)
                tinted = ET.fromstring(build_gradient_fill(gradient, opacity=0.5))
                self.assertEqual([n.get('val') for n in tinted.findall('.//a:alpha', NS)], [expected, '50000'])
                self.assertEqual(gradient.attrib, attributes)
                self.assertEqual(build_gradient_fill(gradient, opacity=None), original)
                self.assertEqual(build_gradient_fill(gradient, opacity=1.0), original)
                self.assertEqual(build_gradient_fill(gradient, opacity=0.5), ET.tostring(tinted, encoding='unicode'))
                transparent = ET.fromstring(build_gradient_fill(gradient, opacity=0.0))
                self.assertEqual([n.get('val') for n in transparent.findall('.//a:alpha', NS)], ['0', '0'])

    def test_native_gradient_shape_opacity_exports_each_stop(self) -> None:
        gradient = self._native_gradient()
        self._svg(
            f'<defs>{ET.tostring(gradient, encoding="unicode")}</defs>'
            '<rect x="100" y="100" width="200" height="100" fill="url(#g)" opacity="0.5"/>'
            '<rect x="400" y="100" width="200" height="100" fill="url(#g)"/>',
        )
        self.assertFalse(self._check()['errors'])
        gradients = self._export().findall('.//a:gradFill', NS)
        self.assertEqual([n.get('val') for n in gradients[0].findall('.//a:alpha', NS)], ['50000', '50000'])
        self.assertFalse(gradients[1].findall('.//a:alpha', NS))

    def test_inline_dx_adds_only_spacing_runs_to_text_body(self) -> None:
        for dx in ('10', '-10', '-200', '0'):
            with self.subTest(dx=dx):
                body = (
                    '<text x="100" y="120"><tspan {dx}>Alpha</tspan>'
                    '<tspan fill="#123456" dx="20">Beta</tspan></text>'
                )
                attributes = 'font-family="Arial" font-size="20"'
                self._svg(body.format(dx=f'dx="{dx}"'), attributes)
                self.assertFalse(self._check()['errors'])
                shifted = self._export().find('.//p:txBody', NS)
                self._svg(body.format(dx='').replace(' dx="20"', ''), attributes)
                unshifted = self._export().find('.//p:txBody', NS)
                paragraph = shifted.find('a:p', NS)
                spacers = [r for r in paragraph.findall('a:r', NS) if r.find('a:t', NS).text == '\u00a0']
                self.assertEqual(len(spacers), 1 if dx == '0' else 2)
                if dx != '0':
                    spacing = int(spacers[0].find('a:rPr', NS).get('spc'))
                    self.assertGreater(spacing, 0) if dx == '10' else self.assertLess(spacing, 0)
                for spacer in spacers:
                    paragraph.remove(spacer)
                self.assertEqual(ET.tostring(shifted), ET.tostring(unshifted))

    def test_inline_dx_keeps_nested_and_tail_runs(self) -> None:
        self._svg(
            '<text x="100" y="120"><tspan dx="10">A<tspan dx="-4" fill="#123456">B</tspan>C</tspan>'
            'D<tspan dx="5">E</tspan></text>',
            'font-family="Arial" font-size="20"',
        )
        self.assertFalse(self._check()['errors'])
        texts = [n.text for n in self._export().findall('.//a:t', NS)]
        self.assertEqual(texts, ['\u00a0', 'A', '\u00a0', 'B', 'CD', '\u00a0', 'E'])

    def test_inline_dx_does_not_coalesce_into_plain_ab(self) -> None:
        self._svg(
            '<text x="100" y="120"><tspan dx="10">A</tspan><tspan dx="20">B</tspan></text>',
            'font-family="Arial" font-size="20"',
        )
        shifted = self._export()
        runs = shifted.findall('.//a:r', NS)
        self.assertEqual([r.find('a:t', NS).text for r in runs], ['\u00a0', 'A', '\u00a0', 'B'])
        self.assertEqual([r.find('a:rPr', NS).get('spc') for r in runs], ['300', None, '1050', None])
        self._svg('<text x="100" y="120"><tspan>A</tspan><tspan>B</tspan></text>',
                  'font-family="Arial" font-size="20"')
        self.assertEqual([t.text for t in self._export().findall('.//a:t', NS)], ['AB'])

    def test_inline_dx_survives_empty_span_and_first_line_compaction(self) -> None:
        for first in ('<tspan dx="10">A</tspan>', '<tspan dx="10"/><tspan>A</tspan>'):
            with self.subTest(first=first):
                self._svg(
                    f'<text x="100" y="120">{first}<tspan x="100" dy="30">B</tspan></text>',
                    'font-family="Arial" font-size="20"',
                )
                texts = [t.text for t in self._export().findall('.//a:t', NS)]
                self.assertEqual(texts, ['\u00a0', 'A', 'B'])

    def test_inline_dx_survives_split_and_preserved_lines(self) -> None:
        for text_flow in ('split', 'preserve', 'reflow'):
            with self.subTest(text_flow=text_flow):
                self._svg(
                    '<text x="100" y="120"><tspan x="100">Alpha</tspan><tspan dx="10">Beta</tspan>'
                    '<tspan x="100" dy="30">Gamma</tspan><tspan dx="-5">Delta</tspan></text>',
                    'font-family="Arial" font-size="20"',
                )
                xml, *_ = convert_svg_to_slide_shapes(self.svg_path, resource_root=self.root, text_flow=text_flow)
                slide = ET.fromstring(xml)
                self.assertEqual(sum(n.text == '\u00a0' for n in slide.findall('.//a:t', NS)), 2)
                self.assertEqual(len(slide.findall('.//p:sp', NS)), 2 if text_flow == 'split' else 1)
                if text_flow == 'preserve':
                    self.assertEqual(len(slide.findall('.//a:br', NS)), 1)

    def test_line_starter_dx_is_consumed_once_and_small_dy_still_splits(self) -> None:
        self._svg(
            '<text x="100" y="120"><tspan x="100" dx="10">A</tspan>'
            '<tspan x="100" dx="-5" dy="30">B</tspan></text>',
            'font-family="Arial" font-size="20"',
        )
        positioned = ET.tostring(self._export())
        self._svg(
            '<text x="110" y="120">A</text><text x="95" y="150">B</text>',
            'font-family="Arial" font-size="20"',
        )
        self.assertEqual(positioned, ET.tostring(self._export()))
        tree = ET.ElementTree(ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg"><text x="100" y="120">A<tspan dy="-4">B</tspan>'
            '</text></svg>'
        ))
        self.assertTrue(flatten_text_with_tspans(tree))
        self.assertEqual([n.get('y') for n in tree.getroot()], ['120', '116'])


if __name__ == '__main__':
    unittest.main()
