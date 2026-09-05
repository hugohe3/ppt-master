#!/usr/bin/env python3
"""Regression tests for coordinate, visibility, and pattern export guards."""

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
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_to_pptx.drawingml.converter import (  # noqa: E402
    SvgNativeConversionError,
    convert_svg_to_slide_shapes,
)


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


if __name__ == '__main__':
    unittest.main()
