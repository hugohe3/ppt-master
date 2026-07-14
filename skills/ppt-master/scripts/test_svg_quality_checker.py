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
from svg_to_pptx.native_objects import (
    NativeMarkerAttributeError,
    native_fallback_kind,
    native_import_source,
    native_replacement_kind,
    native_replacement_status,
)
from svg_to_pptx.pptx_package.template_structure import (
    TemplateStructureError,
    _validate_placeholder_carrier,
)
from svg_to_pptx.use_expander import UseExpansionError, expand_local_use_references


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

    def test_degenerate_gradient_stroke_blocks_checker_and_exporter(self):
        self._assert_checker_and_exporter_reject(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2563EB"/>
      <stop offset="1" stop-color="#10B981"/>
    </linearGradient>
  </defs>
  <path d="M100 200 C260 200 420 200 620 200" fill="none"
        stroke="url(#flow)" stroke-width="40"/>
</svg>''',
            'objectBoundingBox gradients do not include stroke width',
            'invalid project gradient',
        )

    def test_isolated_move_does_not_expand_gradient_stroke_bounds(self):
        self._assert_checker_and_exporter_reject(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2563EB"/>
      <stop offset="1" stop-color="#10B981"/>
    </linearGradient>
  </defs>
  <path d="M100 200 H620 M100 201" fill="none"
        stroke="url(#flow)" stroke-width="40"/>
</svg>''',
            'zero intrinsic height',
            'invalid project gradient',
        )

    def test_expanded_use_gradient_stroke_matches_exporter_preflight(self):
        self._assert_checker_and_exporter_reject(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2563EB"/>
      <stop offset="1" stop-color="#10B981"/>
    </linearGradient>
    <symbol id="edge" viewBox="0 0 100 20">
      <path d="M0 10 H100" fill="none"/>
    </symbol>
  </defs>
  <g stroke="url(#flow)" stroke-width="10">
    <use href="#edge" x="100" y="100" width="200" height="40"/>
  </g>
</svg>''',
            'zero intrinsic height',
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

    def test_chart_table_replacement_attributes_resolve_canonical_and_legacy(self):
        import xml.etree.ElementTree as ET

        canonical = ET.fromstring(
            '<g data-pptx-replace-with="table" '
            'data-pptx-replacement-status="unsupported-table-style" '
            'data-pptx-import-source="pptx" '
            'data-pptx-fallback-kind="normalized"/>'
        )
        legacy = ET.fromstring(
            '<g data-pptx-native="table" '
            'data-pptx-native-status="unsupported-table-style" '
            'data-pptx-native-source="pptx" '
            'data-pptx-visual-status="normalized"/>'
        )
        for elem in (canonical, legacy):
            self.assertEqual(native_replacement_kind(elem), 'table')
            self.assertEqual(
                native_replacement_status(elem),
                'unsupported-table-style',
            )
            self.assertEqual(native_import_source(elem), 'pptx')
            self.assertEqual(native_fallback_kind(elem), 'normalized')

    def test_conflicting_chart_table_replacement_aliases_are_errors(self):
        import xml.etree.ElementTree as ET

        elem = ET.fromstring(
            '<g data-pptx-replace-with="chart" data-pptx-native="table"/>'
        )
        with self.assertRaisesRegex(
            NativeMarkerAttributeError,
            'data-pptx-replace-with.*conflicts',
        ):
            native_replacement_kind(elem)

        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="conflict" data-pptx-replace-with="chart" data-pptx-native="table"/>
</svg>'''
        )
        self.assertFalse(result['passed'])
        self.assertIn(
            'data-pptx-replace-with',
            '\n'.join(result['errors']),
        )
        self.assertNotIn(
            'legacy attribute data-pptx-native',
            '\n'.join(result['warnings']),
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'conflict.svg'
            svg_path.write_text(
                '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="conflict" data-pptx-replace-with="chart" data-pptx-native="table"/>
</svg>''',
                encoding='utf-8',
            )
            with self.assertRaisesRegex(
                SvgNativeConversionError,
                'invalid chart/table replacement metadata',
            ):
                convert_svg_to_slide_shapes(svg_path)

    def test_all_chart_table_replacement_alias_pairs_reject_conflicts(self):
        import xml.etree.ElementTree as ET

        cases = (
            (
                'data-pptx-replace-with="chart" data-pptx-native="table"',
                native_replacement_kind,
            ),
            (
                'data-pptx-replacement-status="one" data-pptx-native-status="two"',
                native_replacement_status,
            ),
            (
                'data-pptx-import-source="pptx" data-pptx-native-source="other"',
                native_import_source,
            ),
            (
                'data-pptx-fallback-kind="normalized" '
                'data-pptx-visual-status="source-preview"',
                native_fallback_kind,
            ),
        )
        for attributes, getter in cases:
            with self.subTest(attributes=attributes):
                elem = ET.fromstring(f'<g {attributes}/>')
                with self.assertRaises(NativeMarkerAttributeError):
                    getter(elem)

    def test_matching_chart_table_replacement_aliases_are_accepted(self):
        import xml.etree.ElementTree as ET

        cases = (
            (
                '<g data-pptx-replace-with="chart" data-pptx-native="chart"/>',
                native_replacement_kind,
                'chart',
            ),
            (
                '<g data-pptx-replacement-status="reason" '
                'data-pptx-native-status="reason"/>',
                native_replacement_status,
                'reason',
            ),
            (
                '<g data-pptx-import-source="pptx" '
                'data-pptx-native-source="pptx"/>',
                native_import_source,
                'pptx',
            ),
            (
                '<g data-pptx-fallback-kind="normalized" '
                'data-pptx-visual-status="normalized"/>',
                native_fallback_kind,
                'normalized',
            ),
        )
        for markup, getter, expected in cases:
            with self.subTest(markup=markup):
                self.assertEqual(getter(ET.fromstring(markup)), expected)

    def test_invalid_replacement_tokens_block_checker_and_default_export(self):
        cases = (
            ('data-pptx-replace-with="diagram"', 'unsupported data-pptx-replace-with'),
            ('data-pptx-replace-with="Chart"', 'must use lowercase chart or table'),
            ('data-pptx-replace-with=" chart "', 'surrounding whitespace'),
            ('data-pptx-replacement-status=""', 'must not be empty'),
            ('data-pptx-replacement-status=" reason "', 'surrounding whitespace'),
            ('data-pptx-import-source="other"', 'unsupported data-pptx-import-source'),
            ('data-pptx-fallback-kind="Normalized"', 'unsupported data-pptx-fallback-kind'),
        )
        for attributes, expected in cases:
            content = (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                f'<g id="marker" {attributes}/></svg>'
            )
            with self.subTest(attributes=attributes):
                result = self._check(content)
                self.assertFalse(result['passed'])
                self.assertIn(expected, '\n'.join(result['errors']))
                with tempfile.TemporaryDirectory() as tmp_dir:
                    svg_path = Path(tmp_dir) / 'invalid-token.svg'
                    svg_path.write_text(content, encoding='utf-8')
                    with self.assertRaisesRegex(
                        SvgNativeConversionError,
                        'invalid chart/table replacement metadata',
                    ):
                        convert_svg_to_slide_shapes(svg_path)

    def test_replacement_status_uses_closed_importer_reason_codes(self):
        legal = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="fallback" data-pptx-replacement-status="unsupported-table-style">
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        made_up = legal.replace('unsupported-table-style', 'made-up-reason')

        legal_result = self._check(legal)
        self.assertTrue(legal_result['passed'])
        self.assertEqual(legal_result['errors'], [])

        made_up_result = self._check(made_up)
        self.assertFalse(made_up_result['passed'])
        self.assertIn(
            "unsupported data-pptx-replacement-status value: 'made-up-reason'",
            '\n'.join(made_up_result['errors']),
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            legal_path = Path(tmp_dir) / 'legal.svg'
            made_up_path = Path(tmp_dir) / 'made-up.svg'
            legal_path.write_text(legal, encoding='utf-8')
            made_up_path.write_text(made_up, encoding='utf-8')
            convert_svg_to_slide_shapes(legal_path)
            with self.assertRaisesRegex(
                SvgNativeConversionError,
                'unsupported data-pptx-replacement-status value',
            ):
                convert_svg_to_slide_shapes(made_up_path)

    def test_legacy_replacement_attributes_remain_non_blocking(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="legacy-table" data-pptx-native="table"
     data-pptx-native-source="pptx" data-pptx-visual-status="normalized"
     data-pptx-x="80" data-pptx-y="80"
     data-pptx-width="320" data-pptx-height="180">
    <metadata data-pptx-kind="table">{"rows":[["A"]]}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        )
        warning_text = '\n'.join(result['warnings'])
        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertIn('legacy attribute data-pptx-native', warning_text)
        self.assertIn('legacy metadata attribute data-pptx-kind', warning_text)

    def test_canonical_placeholder_fallback_does_not_require_route_status(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="placeholder" data-pptx-fallback-kind="placeholder">
    <rect x="80" y="80" width="320" height="180" fill="#EEEEEE"/>
  </g>
</svg>'''
        )
        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertIn(
            'reconstruction-only placeholder',
            '\n'.join(result['warnings']),
        )

    def test_legacy_placeholder_fallback_still_requires_legacy_route_status(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="placeholder" data-pptx-visual-status="placeholder">
    <rect x="80" y="80" width="320" height="180" fill="#EEEEEE"/>
  </g>
</svg>'''
        )
        self.assertFalse(result['passed'])
        self.assertIn(
            "data-pptx-route-status='reconstruction-only'",
            '\n'.join(result['errors']),
        )

    def test_metadata_kind_must_match_parent_replacement_kind(self):
        content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="chart" data-pptx-replace-with="chart"
     data-pptx-x="80" data-pptx-y="80"
     data-pptx-width="320" data-pptx-height="180">
    <metadata type="application/json" data-pptx-kind="table">{"rows":[["A"]]}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        result = self._check(content)
        self.assertFalse(result['passed'])
        self.assertIn(
            "metadata kind 'table' conflicts with parent replacement kind 'chart'",
            '\n'.join(result['errors']),
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'metadata-conflict.svg'
            svg_path.write_text(content, encoding='utf-8')
            for native_objects in (False, True):
                with self.subTest(native_objects=native_objects):
                    with self.assertRaisesRegex(
                        SvgNativeConversionError,
                        "metadata kind 'table' conflicts",
                    ):
                        convert_svg_to_slide_shapes(
                            svg_path,
                            native_objects=native_objects,
                        )

    def test_conflicting_legacy_metadata_kind_aliases_are_errors(self):
        content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="chart" data-pptx-replace-with="chart"
     data-pptx-x="80" data-pptx-y="80"
     data-pptx-width="320" data-pptx-height="180">
    <metadata type="application/json" data-pptx-native="chart"
              data-pptx-kind="table">{"series":[]}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        result = self._check(content)
        self.assertFalse(result['passed'])
        self.assertIn(
            'metadata data-pptx-native conflicts with data-pptx-kind',
            '\n'.join(result['errors']),
        )
        self.assertNotIn(
            'legacy metadata attribute',
            '\n'.join(result['warnings']),
        )

    def test_structured_placeholder_wraps_replacement_alias_conflicts(self):
        import xml.etree.ElementTree as ET

        carrier = ET.fromstring(
            '<g data-pptx-replace-with="chart" data-pptx-native="table"/>'
        )
        with self.assertRaisesRegex(
            TemplateStructureError,
            'conflicting chart/table replacement metadata',
        ):
            _validate_placeholder_carrier(
                carrier,
                'chart',
                svg_path=Path('template.svg'),
                element_id='chart-slot',
            )

    def test_local_use_rejects_all_canonical_replacement_metadata(self):
        import xml.etree.ElementTree as ET

        attributes = (
            'data-pptx-replace-with="chart"',
            'data-pptx-replacement-status="reason"',
            'data-pptx-import-source="pptx"',
            'data-pptx-fallback-kind="normalized"',
            'data-pptx-fallback-sha256="' + ('0' * 64) + '"',
        )
        for attribute in attributes:
            root = ET.fromstring(
                '<svg xmlns="http://www.w3.org/2000/svg">'
                f'<defs><g id="source" {attribute}><rect width="10" height="10"/></g></defs>'
                '<use href="#source"/></svg>'
            )
            with self.subTest(attribute=attribute):
                with self.assertRaises(UseExpansionError):
                    expand_local_use_references(root)

    def test_canonical_and_legacy_table_markers_export_identically(self):
        payload = '{"x":80,"y":80,"width":320,"height":180,"rows":[["A"]]}'
        canonical = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="table" data-pptx-replace-with="table">
    <metadata type="application/json">{payload}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        legacy = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="table" data-pptx-native="table">
    <metadata data-pptx-native="table">{payload}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''

        with tempfile.TemporaryDirectory() as tmp_dir:
            canonical_path = Path(tmp_dir) / 'canonical.svg'
            legacy_path = Path(tmp_dir) / 'legacy.svg'
            canonical_path.write_text(canonical, encoding='utf-8')
            legacy_path.write_text(legacy, encoding='utf-8')
            canonical_result = convert_svg_to_slide_shapes(
                canonical_path,
                native_objects=True,
            )
            legacy_result = convert_svg_to_slide_shapes(
                legacy_path,
                native_objects=True,
            )

        self.assertEqual(canonical_result, legacy_result)


if __name__ == '__main__':
    unittest.main()
