#!/usr/bin/env python3
"""Regression tests for SVG checker compatibility severity."""

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from svg_quality_checker import SVGQualityChecker
from svg_to_pptx.drawingml.converter import (
    SvgNativeConversionError,
    convert_svg_to_slide_shapes,
)


class SVGQualityCheckerCompatibilityTests(unittest.TestCase):
    """Keep supported aliases advisory and unsupported input blocking."""

    def _check(self, content: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'fixture.svg'
            svg_path.write_text(content, encoding='utf-8')
            return SVGQualityChecker().check_file(str(svg_path))

    def _assert_checker_and_exporter_reject(
        self,
        content: str,
        expected_checker_text: str,
        expected_exporter_text: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'fixture.svg'
            svg_path.write_text(content, encoding='utf-8')
            result = SVGQualityChecker().check_file(str(svg_path))
            self.assertFalse(result['passed'])
            self.assertIn(expected_checker_text, '\n'.join(result['errors']))
            with self.assertRaisesRegex(
                SvgNativeConversionError,
                expected_exporter_text,
            ):
                convert_svg_to_slide_shapes(svg_path)

    def test_canonical_generated_spelling_has_no_compatibility_warning(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <rect x="80" y="80" width="300" height="180"
        fill="#FF0000" fill-opacity="0.5"/>
  <text x="80" y="340" font-family="Arial" font-size="28"
        fill="#000080">Canonical</text>
</svg>'''
        )

        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])

    def test_supported_aliases_are_non_blocking_warnings(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1280 720">
  <defs>
    <g id="dot"><circle cx="0" cy="0" r="8" fill="#00AA00"/></g>
    <linearGradient id="legacy-gradient">
      <stop offset="0" stop-color="#0000FF" stop-opacity="50%"/>
      <stop offset="1" stop-color="#0000FF"/>
    </linearGradient>
    <pattern id="legacy-pattern" width="8" height="8">
      <rect width="8" height="8" fill="#FFFFFF"/>
      <path d="M0 8 L8 0" stroke="#999999"/>
    </pattern>
  </defs>
  <g id="faded" opacity="0.6">
    <rect x="80" y="80" width="300" height="180"
          fill="rgba(255, 0, 0, 0.5)" fill-opacity="1.2"/>
  </g>
  <rect x="420" y="80" width="300" height="180"
        fill="url(#legacy-pattern)"/>
  <rect x="760" y="80" width="300" height="180"
        fill="url(#legacy-gradient)"/>
  <text x="80" y="340" font-family="Arial" font-size="21pt"
        fill="navy">Aliases</text>
  <use xlink:href="#dot" x="100" y="420"/>
</svg>'''
        )

        warning_text = '\n'.join(result['warnings'])
        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertIn("fill='rgba(255, 0, 0, 0.5)'", warning_text)
        self.assertIn("fill-opacity='1.2'", warning_text)
        self.assertIn("stop-opacity='50%'", warning_text)
        self.assertIn('group opacity', warning_text)
        self.assertIn('font-size value(s) 21pt', warning_text)
        self.assertIn('legacy xlink:href', warning_text)
        self.assertIn('compatible `ltUpDiag` fallback', warning_text)
        self.assertTrue(all('No change is required' in item or 'does not require' in item
                            for item in result['warnings']))

    def test_unsupported_values_remain_errors(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <rect x="80" y="80" width="300" height="180"
        fill="var(--brand)" opacity="bogus" fill-opacity="50%"/>
  <text x="80" y="340" font-family="Arial" font-size="12%">Broken</text>
</svg>'''
        )

        error_text = '\n'.join(result['errors'])
        self.assertFalse(result['passed'])
        self.assertIn('must be a supported color', error_text)
        self.assertIn('must be one finite numeric opacity', error_text)
        self.assertIn('Unsupported font-size', error_text)

    def test_pattern_transform_stays_blocking_without_explicit_preset(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <defs>
    <pattern id="legacy-pattern" width="8" height="8"
             patternTransform="rotate(45)">
      <rect width="8" height="8" fill="#FFFFFF"/>
      <path d="M0 8 L8 0" stroke="#999999"/>
    </pattern>
  </defs>
  <rect x="80" y="80" width="300" height="180"
        fill="url(#legacy-pattern)"/>
</svg>'''
        )

        self.assertFalse(result['passed'])
        self.assertTrue(any('cannot use patternTransform' in item
                            for item in result['errors']))
        self.assertTrue(any('compatible `ltUpDiag` fallback' in item
                            for item in result['warnings']))

    def test_invalid_gradient_contract_blocks_checker_and_exporter(self):
        self._assert_checker_and_exporter_reject(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="broken" x1="0" x2="2">
      <stop offset="120%"/>
    </linearGradient>
  </defs>
  <rect x="80" y="80" width="300" height="180"
        fill="url(#broken)"/>
</svg>''',
            'requires an explicit stop-color',
            'invalid project gradient',
        )

    def test_invalid_filter_contract_blocks_checker_and_exporter(self):
        self._assert_checker_and_exporter_reject(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720">
  <defs>
    <filter id="broken">
      <feGaussianBlur stdDeviation="not-a-number"/>
    </filter>
  </defs>
  <rect x="80" y="80" width="300" height="180"
        fill="#FFFFFF" filter="url(#broken)"/>
</svg>''',
            'stdDeviation must be a finite number',
            'invalid project filter',
        )

    def test_missing_paint_reference_blocks_checker_and_exporter(self):
        self._assert_checker_and_exporter_reject(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720">
  <rect x="80" y="80" width="300" height="180"
        fill="url(#missing)"/>
</svg>''',
            'has no matching direct <defs> definition',
            'invalid project paint reference',
        )


if __name__ == '__main__':
    unittest.main()
