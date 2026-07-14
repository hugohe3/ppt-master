#!/usr/bin/env python3
"""Regression tests for SVG checker compatibility severity."""

import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from svg_quality_checker import SVGQualityChecker
from pptx_shapes import CONNECTOR_PRESET_TYPES, get_preset_registry
from pptx_to_svg.preset_authoring import (
    materialize_compact_authored_preset_tree,
    render_preset_shape_fragment,
    validate_authored_preset_tree,
)
from svg_to_pptx.drawingml.converter import (
    SvgNativeConversionError,
    convert_svg_to_slide_shapes,
)
from svg_to_pptx.drawingml.utils import parse_inline_style
from svg_to_pptx.native_objects import (
    NativeMarkerAttributeError,
    native_fallback_kind,
    native_import_source,
    native_replacement_kind,
    native_replacement_status,
    stamp_native_fallback_baseline,
)
from svg_to_pptx.pptx_package.template_structure import (
    TemplateStructureError,
    _validate_placeholder_carrier,
    parse_template_slide,
)
from svg_to_pptx.use_expander import UseExpansionError, expand_local_use_references


class SVGQualityCheckerCompatibilityTests(unittest.TestCase):
    """Keep supported aliases advisory and unsupported input blocking."""

    def _check(self, content: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'fixture.svg'
            svg_path.write_text(content, encoding='utf-8')
            return SVGQualityChecker().check_file(str(svg_path))

    def _check_with_spec_lock(self, content: str, lock_text: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project = Path(tmp_dir)
            output_dir = project / 'svg_output'
            output_dir.mkdir()
            (project / 'spec_lock.md').write_text(lock_text, encoding='utf-8')
            svg_path = output_dir / 'fixture.svg'
            svg_path.write_text(content, encoding='utf-8')
            return SVGQualityChecker().check_file(str(svg_path))

    @staticmethod
    def _text_bound_warnings(result: dict) -> list[str]:
        return [
            warning
            for warning in result['warnings']
            if 'estimated horizontal bounds exceed the viewBox' in warning
        ]

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

    def test_converter_string_path_preserves_inline_geometry_diagnostic(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 160 120">
  <rect x="10" y="10" height="40" fill="#2563EB"
        style="width: 60"/>
</svg>'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'string-path.svg'
            svg_path.write_text(source, encoding='utf-8')

            with self.assertRaisesRegex(
                SvgNativeConversionError,
                "string-path.svg: inline geometry materialization failed",
            ):
                convert_svg_to_slide_shapes(str(svg_path))

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

    def test_authored_hashless_native_marker_has_no_baseline_warning(self):
        content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="table" data-pptx-replace-with="table">
    <metadata type="application/json">{"x":80,"y":80,"width":320,"height":180,"rows":[["A"]]}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        result = self._check(content)
        self.assertTrue(result['passed'])
        self.assertEqual(result['warnings'], [])

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'authored.svg'
            svg_path.write_text(content, encoding='utf-8')
            stderr = io.StringIO()
            with patch('sys.stderr', new=stderr):
                convert_svg_to_slide_shapes(svg_path, native_objects=True)

        self.assertNotIn('fallback-sha256', stderr.getvalue())

    def test_imported_hashless_native_marker_warns_but_remains_compatible(self):
        for source_attribute in (
            'data-pptx-import-source="pptx"',
            'data-pptx-native-source="pptx"',
        ):
            content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="table" data-pptx-replace-with="table" {source_attribute}>
    <metadata type="application/json">{{"x":80,"y":80,"width":320,"height":180,"rows":[["A"]]}}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
            with self.subTest(source_attribute=source_attribute):
                result = self._check(content)
                self.assertTrue(result['passed'])
                self.assertIn(
                    'imported marker has no data-pptx-fallback-sha256 baseline',
                    '\n'.join(result['warnings']),
                )

                with tempfile.TemporaryDirectory() as tmp_dir:
                    svg_path = Path(tmp_dir) / 'imported.svg'
                    svg_path.write_text(content, encoding='utf-8')
                    stderr = io.StringIO()
                    with patch('sys.stderr', new=stderr):
                        convert_svg_to_slide_shapes(
                            svg_path,
                            native_objects=True,
                        )
                self.assertIn(
                    'imported marker has no data-pptx-fallback-sha256 baseline',
                    stderr.getvalue(),
                )

    def test_explicit_authored_fallback_baseline_still_blocks_stale_native_export(self):
        root = ET.fromstring(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="table" data-pptx-replace-with="table">
    <metadata type="application/json">{"x":80,"y":80,"width":320,"height":180,"rows":[["A"]]}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        )
        marker = next(elem for elem in root if elem.tag.endswith('g'))
        stamp_native_fallback_baseline(marker, document_root=root)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'sealed-authored.svg'
            ET.ElementTree(root).write(svg_path, encoding='unicode')
            fresh_result = SVGQualityChecker().check_file(str(svg_path))
            self.assertTrue(fresh_result['passed'])
            self.assertEqual(fresh_result['warnings'], [])
            convert_svg_to_slide_shapes(svg_path, native_objects=True)

            rect = next(elem for elem in marker if elem.tag.endswith('rect'))
            rect.set('fill', '#EEEEEE')
            ET.ElementTree(root).write(svg_path, encoding='unicode')
            stale_result = SVGQualityChecker().check_file(str(svg_path))
            self.assertTrue(stale_result['passed'])
            self.assertIn(
                'visible SVG fallback differs from its recorded baseline',
                '\n'.join(stale_result['warnings']),
            )
            convert_svg_to_slide_shapes(svg_path)
            with self.assertRaisesRegex(
                SvgNativeConversionError,
                'fallback was edited after its baseline',
            ):
                convert_svg_to_slide_shapes(svg_path, native_objects=True)

    def test_explicit_authored_invalid_fallback_baseline_still_fails_native_export(self):
        content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <g id="table" data-pptx-replace-with="table"
     data-pptx-fallback-sha256="invalid">
    <metadata type="application/json">{"x":80,"y":80,"width":320,"height":180,"rows":[["A"]]}</metadata>
    <rect x="80" y="80" width="320" height="180" fill="#FFFFFF"/>
  </g>
</svg>'''
        result = self._check(content)
        self.assertTrue(result['passed'])
        self.assertIn(
            'must be a 64-digit SHA-256',
            '\n'.join(result['warnings']),
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'invalid-baseline.svg'
            svg_path.write_text(content, encoding='utf-8')
            convert_svg_to_slide_shapes(svg_path)
            with self.assertRaisesRegex(
                SvgNativeConversionError,
                'must be a 64-digit SHA-256',
            ):
                convert_svg_to_slide_shapes(svg_path, native_objects=True)

    def test_authored_template_markers_do_not_preseed_static_fallback_hashes(self):
        template_root = SCRIPT_DIR.parent / 'templates'
        offenders = []
        for svg_path in template_root.rglob('*.svg'):
            root = ET.parse(svg_path).getroot()
            for elem in root.iter():
                if not native_replacement_kind(elem):
                    continue
                if native_import_source(elem) == 'pptx':
                    continue
                if elem.get('data-pptx-fallback-sha256') is not None:
                    offenders.append(str(svg_path.relative_to(template_root)))
        self.assertEqual(offenders, [])

    def test_chart_templates_name_all_top_level_groups(self):
        chart_root = SCRIPT_DIR.parent / 'templates' / 'charts'
        anonymous_groups = []
        duplicate_ids = []
        for svg_path in chart_root.glob('*.svg'):
            root = ET.parse(svg_path).getroot()
            seen_ids = set()
            for elem in root.iter():
                element_id = elem.get('id')
                if not element_id:
                    continue
                if element_id in seen_ids:
                    duplicate_ids.append(
                        f'{svg_path.name}: {element_id}'
                    )
                seen_ids.add(element_id)
            for index, child in enumerate(list(root), start=1):
                if child.tag.rsplit('}', 1)[-1] != 'g':
                    continue
                if (child.get('id') or '').strip():
                    continue
                anonymous_groups.append(
                    f'{svg_path.name}: root child {index}'
                )
        self.assertEqual(anonymous_groups, [])
        self.assertEqual(duplicate_ids, [])

    def test_chart_templates_use_canonical_readable_font_sizes(self):
        chart_root = SCRIPT_DIR.parent / 'templates' / 'charts'
        noncanonical_sizes = []
        undersized_text = []
        for svg_path in chart_root.glob('*.svg'):
            root = ET.parse(svg_path).getroot()
            for elem in root.iter():
                styles = parse_inline_style(elem.get('style'))
                raw_size = styles.get('font-size', elem.get('font-size'))
                if raw_size is None:
                    continue
                try:
                    size = float(raw_size)
                except ValueError:
                    noncanonical_sizes.append(
                        f'{svg_path.name}: {raw_size}'
                    )
                    continue
                if not math.isfinite(size):
                    noncanonical_sizes.append(
                        f'{svg_path.name}: {raw_size}'
                    )
                    continue
                if size < 12:
                    element_id = elem.get('id') or elem.tag.rsplit('}', 1)[-1]
                    undersized_text.append(
                        f'{svg_path.name}: {element_id}={raw_size}'
                    )
        self.assertEqual(noncanonical_sizes, [])
        self.assertEqual(undersized_text, [])

    def test_chart_text_bound_warnings_match_real_overflows(self):
        chart_root = SCRIPT_DIR.parent / 'templates' / 'charts'
        warned = set()
        for svg_path in chart_root.glob('*.svg'):
            result = SVGQualityChecker().check_file(str(svg_path))
            if self._text_bound_warnings(result):
                warned.add(svg_path.name)
        self.assertEqual(
            warned,
            {'bullet_chart.svg', 'pyramid_isometric.svg'},
        )

    def test_chart_catalog_passes_checker_and_export_routes(self):
        chart_root = SCRIPT_DIR.parent / 'templates' / 'charts'
        index = json.loads(
            (chart_root / 'charts_index.json').read_text(encoding='utf-8')
        )
        indexed_keys = set(index['charts'])
        svg_paths = sorted(chart_root.glob('*.svg'))
        svg_keys = {path.stem for path in svg_paths}
        self.assertEqual(index['meta']['total'], len(indexed_keys))
        self.assertEqual(svg_keys, indexed_keys)

        for svg_path in svg_paths:
            with self.subTest(chart=svg_path.stem):
                checker_result = SVGQualityChecker().check_file(str(svg_path))
                self.assertEqual(checker_result['errors'], [])

                default_result = convert_svg_to_slide_shapes(svg_path)
                default_xml = default_result[0]
                self.assertNotIn('<c:chart ', default_xml)
                self.assertNotIn('<cx:chart ', default_xml)
                self.assertNotIn('<a:tbl>', default_xml)

                root = ET.parse(svg_path).getroot()
                replacement_kinds = {
                    kind
                    for elem in root.iter()
                    if (kind := native_replacement_kind(elem))
                }
                stderr = io.StringIO()
                with patch('sys.stderr', new=stderr):
                    native_result = convert_svg_to_slide_shapes(
                        svg_path,
                        native_objects=True,
                    )
                native_xml = native_result[0]

                if not replacement_kinds:
                    self.assertEqual(native_result, default_result)
                    continue

                self.assertEqual(len(replacement_kinds), 1)
                self.assertNotEqual(native_result, default_result)
                if replacement_kinds == {'chart'}:
                    self.assertTrue(
                        '<c:chart ' in native_xml
                        or '<cx:chart ' in native_xml
                    )
                    self.assertNotIn('<a:tbl>', native_xml)
                elif replacement_kinds == {'table'}:
                    self.assertIn('<a:tbl>', native_xml)
                    self.assertNotIn('<c:chart ', native_xml)
                    self.assertNotIn('<cx:chart ', native_xml)
                else:
                    self.fail(
                        f'unsupported replacement kinds: {replacement_kinds}'
                    )

    def test_compact_authored_preset_exports_one_native_shape(self):
        fragment = render_preset_shape_fragment(
            'rightArrow',
            (10, 20, 100, 40),
            adjustments={'adj1': 50000, 'adj2': 50000},
            element_id='next-step',
            style={'fill': '#2563EB', 'stroke': 'none'},
        )
        self.assertNotIn('data-pptx-part', fragment)
        self.assertNotIn('data-pptx-preview-sha256', fragment)
        self.assertNotIn('visibility="hidden"', fragment)
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
            f'{fragment}</svg>'
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'compact.svg'
            svg_path.write_text(source, encoding='utf-8')
            result = SVGQualityChecker().check_file(str(svg_path))
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])
        self.assertEqual(slide_xml.count('<p:sp>'), 1)
        self.assertEqual(
            slide_xml.count('<a:prstGeom prst="rightArrow">'),
            1,
        )
        self.assertNotIn('<p:cxnSp>', slide_xml)

    def test_compact_multi_path_preset_exports_one_native_shape(self):
        fragment = render_preset_shape_fragment(
            'cube',
            (10, 20, 100, 80),
            element_id='cube-node',
            style={'fill': '#2563EB', 'stroke': 'none'},
        )
        group = ET.fromstring(fragment)
        self.assertEqual(len(group), 4)
        self.assertTrue(all(child.tag == 'path' for child in group))
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140">'
            f'{fragment}</svg>'
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'compact-multi.svg'
            svg_path.write_text(source, encoding='utf-8')
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertEqual(slide_xml.count('<p:sp>'), 1)
        self.assertEqual(slide_xml.count('<a:prstGeom prst="cube">'), 1)

    def test_every_registered_preset_supports_compact_authoring(self):
        registry = get_preset_registry()
        for index, preset in enumerate(registry.names):
            connector = preset in CONNECTOR_PRESET_TYPES
            style = (
                {
                    'fill': 'none',
                    'stroke': '#334155',
                    'stroke-width': '2',
                }
                if connector
                else {'fill': '#2563EB', 'stroke': 'none'}
            )
            with self.subTest(preset=preset):
                fragment = render_preset_shape_fragment(
                    preset,
                    (10, 20, 100, 60),
                    object_kind='connector' if connector else 'shape',
                    element_id=f'preset-{index}',
                    style=style,
                )
                root = ET.fromstring(
                    '<svg xmlns="http://www.w3.org/2000/svg">'
                    f'{fragment}</svg>'
                )
                self.assertEqual(validate_authored_preset_tree(root), [])
                self.assertEqual(
                    materialize_compact_authored_preset_tree(root),
                    1,
                )
                self.assertEqual(validate_authored_preset_tree(root), [])

    def test_compact_authored_connector_exports_one_native_connector(self):
        fragment = render_preset_shape_fragment(
            'bentConnector3',
            (10, 20, 100, 80),
            object_kind='connector',
            element_id='relationship',
            style={
                'fill': 'none',
                'stroke': '#334155',
                'stroke-width': '2',
            },
        )
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140">'
            f'{fragment}</svg>'
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'compact-connector.svg'
            svg_path.write_text(source, encoding='utf-8')
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertEqual(slide_xml.count('<p:cxnSp>'), 1)
        self.assertEqual(
            slide_xml.count('<a:prstGeom prst="bentConnector3">'),
            1,
        )
        self.assertNotIn('<p:sp>', slide_xml)

    def test_compact_authored_preset_rejects_stale_visible_path(self):
        fragment = render_preset_shape_fragment(
            'diamond',
            (20, 20, 80, 60),
            element_id='decision',
            style={'fill': '#F59E0B', 'stroke': 'none'},
        )
        stale = fragment.replace('M 20 50', 'M 21 50', 1)
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{stale}</svg>'
        )
        self._assert_checker_and_exporter_reject(
            source,
            'Compact authored preset path 1 differs from registry output',
            'Invalid authored preset structure',
        )

    def test_compact_authored_preset_rejects_noncanonical_frame_spelling(self):
        fragment = render_preset_shape_fragment(
            'diamond',
            (20, 20, 80, 60),
            element_id='decision',
            style={'fill': '#F59E0B', 'stroke': 'none'},
        ).replace(
            'data-pptx-frame="20 20 80 60"',
            'data-pptx-frame="2e1,20,+80,60.0"',
            1,
        )
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{fragment}</svg>'
        )

        self._assert_checker_and_exporter_reject(
            source,
            'data-pptx-frame must use the helper',
            'Invalid authored preset structure',
        )

    def test_compact_preset_ancestor_paint_is_compatible_with_warning(self):
        fragment = render_preset_shape_fragment(
            'diamond',
            (20, 20, 80, 60),
            element_id='decision',
            style={'fill': '#F59E0B', 'stroke': 'none'},
        )
        result = self._check(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            '<g id="faded" fill-opacity="0.25">'
            f'{fragment}</g></svg>'
        )

        self.assertTrue(result['passed'])
        self.assertIn(
            'Compact authored preset(s) use compatible ancestor paint',
            '\n'.join(result['warnings']),
        )

    def test_registry_derived_preset_layers_do_not_drift_from_spec_lock(self):
        fragment = render_preset_shape_fragment(
            'cube',
            (20, 20, 80, 60),
            element_id='cube',
            style={'fill': '#2563EB', 'stroke': 'none'},
        )
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{fragment}</svg>'
        )

        result = self._check_with_spec_lock(
            source,
            (
                '# Execution Lock\n\n'
                '## colors\n'
                '- primary: #2563EB\n'
            ),
        )

        self.assertTrue(result['passed'])
        self.assertNotIn('spec_lock drift', '\n'.join(result['warnings']))

    def test_spec_lock_color_fallback_normalizes_every_declared_color(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 160 120">
  <rect x="10" y="10" width="60" height="40" fill="#2563EB"/>
  <rect x="90" y="10" width="60" height="40" fill="#10B981"/>
</svg>'''
        lock_text = (
            '# Execution Lock\n\n'
            '## colors\n'
            '- primary: #2563EB\n'
            '- success: #10B981\n'
        )

        with patch('svg_quality_checker._parse_export_color', None):
            result = self._check_with_spec_lock(source, lock_text)

        self.assertTrue(result['passed'])
        self.assertNotIn('spec_lock drift', '\n'.join(result['warnings']))

    def test_spec_lock_color_fallback_accepts_empty_color_section(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 160 120">
  <rect x="10" y="10" width="60" height="40" fill="#FFFFFF"/>
</svg>'''
        lock_text = '# Execution Lock\n\n## colors\n'

        with patch('svg_quality_checker._parse_export_color', None):
            result = self._check_with_spec_lock(source, lock_text)

        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertIn('spec_lock drift', '\n'.join(result['warnings']))

    def test_foreign_namespace_cannot_impersonate_compact_svg_path(self):
        fragment = render_preset_shape_fragment(
            'diamond',
            (20, 20, 80, 60),
            element_id='decision',
            style={'fill': '#F59E0B', 'stroke': 'none'},
        )
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{fragment}</svg>'
        )
        group = list(root)[0]
        list(group)[0].tag = '{urn:foreign}path'
        source = ET.tostring(root, encoding='unicode')

        self._assert_checker_and_exporter_reject(
            source,
            'may contain only direct SVG paths',
            'Invalid authored preset structure',
        )

    def test_expanded_authored_preset_remains_compatible(self):
        fragment = render_preset_shape_fragment(
            'triangle',
            (20, 20, 80, 60),
            element_id='triangle-node',
            style={'fill': '#7C3AED', 'stroke': 'none'},
        )
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{fragment}</svg>'
        )
        self.assertEqual(materialize_compact_authored_preset_tree(root), 1)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'expanded.svg'
            ET.ElementTree(root).write(
                svg_path,
                encoding='utf-8',
                xml_declaration=True,
            )
            result = SVGQualityChecker().check_file(str(svg_path))
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertTrue(result['passed'])
        self.assertIn(
            'Compatible expanded authored-preset fragment(s) detected',
            '\n'.join(result['warnings']),
        )
        self.assertEqual(slide_xml.count('<a:prstGeom prst="triangle">'), 1)

    def test_malformed_expanded_preset_does_not_receive_migration_warning(self):
        fragment = render_preset_shape_fragment(
            'triangle',
            (20, 20, 80, 60),
            element_id='triangle-node',
            style={'fill': '#7C3AED', 'stroke': 'none'},
        )
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{fragment}</svg>'
        )
        self.assertEqual(materialize_compact_authored_preset_tree(root), 1)
        group = list(root)[0]
        preview = next(
            child
            for child in group
            if child.get('data-pptx-part') == 'geometry-preview'
        )
        group.remove(preview)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'malformed-expanded.svg'
            ET.ElementTree(root).write(
                svg_path,
                encoding='utf-8',
                xml_declaration=True,
            )
            result = SVGQualityChecker().check_file(str(svg_path))

        self.assertFalse(result['passed'])
        self.assertNotIn(
            'Compatible expanded authored-preset fragment(s) detected',
            '\n'.join(result['warnings']),
        )

    def test_expanded_authored_preset_rejects_compact_only_group_style(self):
        fragment = render_preset_shape_fragment(
            'triangle',
            (20, 20, 80, 60),
            element_id='triangle-node',
            style={'fill': '#7C3AED', 'stroke': 'none'},
        )
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{fragment}</svg>'
        )
        self.assertEqual(materialize_compact_authored_preset_tree(root), 1)
        list(root)[0].set('fill-opacity', '0.5')
        source = ET.tostring(root, encoding='unicode')

        self._assert_checker_and_exporter_reject(
            source,
            'unsupported attributes: fill-opacity',
            'Invalid authored preset structure',
        )

    def test_compact_authored_preset_is_a_structured_fixed_atom(self):
        fragment = render_preset_shape_fragment(
            'rightArrow',
            (20, 20, 80, 40),
            element_id='master-arrow',
            style={'fill': '#2563EB', 'stroke': 'none'},
        ).replace(
            ' fill="#2563EB"',
            ' data-pptx-layer="master" data-pptx-editable="false" '
            'fill="#2563EB"',
            1,
        )
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'data-pptx-master="master" data-pptx-master-name="Master" '
            'data-pptx-layout="layout" data-pptx-layout-name="Layout">'
            f'{fragment}</svg>'
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / '01_cover.svg'
            svg_path.write_text(source, encoding='utf-8')
            spec = parse_template_slide(svg_path, 1)
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertEqual(len(spec.elements), 1)
        self.assertEqual(spec.elements[0].element_id, 'master-arrow')
        self.assertEqual(spec.elements[0].layer, 'master')
        self.assertEqual(
            slide_xml.count('<a:prstGeom prst="rightArrow">'),
            1,
        )

    def test_stale_compact_preset_is_not_a_structured_atom_or_carrier(self):
        fragment = render_preset_shape_fragment(
            'diamond',
            (20, 20, 80, 60),
            element_id='decision',
            style={'fill': '#F59E0B', 'stroke': 'none'},
        ).replace('M 20 50', 'M 21 50', 1)
        carrier = ET.fromstring(fragment)
        carrier.set('data-pptx-placeholder-carrier', 'true')
        with self.assertRaisesRegex(
            TemplateStructureError,
            'object placeholder carrier must be',
        ):
            _validate_placeholder_carrier(
                carrier,
                'object',
                svg_path=Path('template.svg'),
                element_id='object-slot',
            )

        carrier.attrib.pop('data-pptx-placeholder-carrier')
        carrier.set('data-pptx-layer', 'master')
        carrier.set('data-pptx-editable', 'false')
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'data-pptx-master="master" data-pptx-master-name="Master" '
            'data-pptx-layout="layout" data-pptx-layout-name="Layout"/>'
        )
        root.append(carrier)
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / '01_cover.svg'
            ET.ElementTree(root).write(
                svg_path,
                encoding='utf-8',
                xml_declaration=True,
            )
            with self.assertRaisesRegex(
                TemplateStructureError,
                'is a <g> on the master layer',
            ):
                parse_template_slide(svg_path, 1)

    def test_expanded_authored_preset_does_not_gain_structured_atom_status(self):
        fragment = render_preset_shape_fragment(
            'rightArrow',
            (20, 20, 80, 40),
            element_id='master-arrow',
            style={'fill': '#2563EB', 'stroke': 'none'},
        )
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'data-pptx-master="master" data-pptx-master-name="Master" '
            'data-pptx-layout="layout" data-pptx-layout-name="Layout">'
            f'{fragment}</svg>'
        )
        self.assertEqual(materialize_compact_authored_preset_tree(root), 1)
        group = list(root)[0]
        group.set('data-pptx-layer', 'master')
        group.set('data-pptx-editable', 'false')

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / '01_cover.svg'
            ET.ElementTree(root).write(
                svg_path,
                encoding='utf-8',
                xml_declaration=True,
            )
            with self.assertRaisesRegex(
                TemplateStructureError,
                'is a <g> on the master layer',
            ):
                parse_template_slide(svg_path, 1)

    def test_compact_authored_preset_is_an_object_slot_carrier(self):
        carrier = ET.fromstring(render_preset_shape_fragment(
            'diamond',
            (20, 20, 80, 60),
            element_id='object-preset',
            style={'fill': '#F59E0B', 'stroke': 'none'},
        ))
        carrier.set('data-pptx-placeholder-carrier', 'true')

        _validate_placeholder_carrier(
            carrier,
            'object',
            svg_path=Path('template.svg'),
            element_id='object-slot',
        )

        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
            f'{ET.tostring(carrier, encoding="unicode")}</svg>'
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'object-carrier.svg'
            svg_path.write_text(source, encoding='utf-8')
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertEqual(
            slide_xml.count('<a:prstGeom prst="diamond">'),
            1,
        )

    def test_local_use_rejects_authored_preset_metadata(self):
        attributes = (
            'data-pptx-authoring="preset"',
            'data-pptx-object="shape"',
            'data-pptx-prst="diamond"',
            'data-pptx-frame="20 20 80 60"',
            'data-pptx-av-adj="val 50000"',
        )
        for attribute in attributes:
            root = ET.fromstring(
                '<svg xmlns="http://www.w3.org/2000/svg">'
                f'<defs><g id="source" {attribute}>'
                '<path d="M 0 5 L 5 0 L 10 5 L 5 10 Z"/>'
                '</g></defs><use href="#source"/></svg>'
            )
            with self.subTest(attribute=attribute):
                with self.assertRaises(UseExpansionError):
                    expand_local_use_references(root)

    def test_single_line_text_warning_uses_rendered_bounds(self):
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">'
            '<text x="10" y="30" font-size="20">\n'
            f'  {" " * 120}Fit\n'
            '</text>'
            '<text x="150" y="70" font-size="20">WWWW</text>'
            '</svg>'
        )
        result = self._check(source)
        bounds_warnings = self._text_bound_warnings(result)
        self.assertEqual(len(bounds_warnings), 1)
        self.assertIn("'WWWW'", bounds_warnings[0])
        self.assertNotIn("'Fit'", bounds_warnings[0])

    def test_single_line_text_warning_allows_one_pixel_tolerance(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 200 100" font-size="20">
  <text x="141" y="30">WWWW</text>
  <text x="142" y="70">MMMM</text>
</svg>'''
        )
        bounds_warnings = self._text_bound_warnings(result)
        self.assertEqual(len(bounds_warnings), 1)
        self.assertIn("'MMMM'", bounds_warnings[0])
        self.assertNotIn("'WWWW'", bounds_warnings[0])

    def test_single_line_text_warning_respects_text_anchor(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 200 100" font-size="20">
  <text x="100" y="20" text-anchor="middle">WWWWWWWW</text>
  <text x="40" y="20" text-anchor="middle">WWWWWWWW</text>
  <text x="160" y="20" text-anchor="middle">WWWWWWWW</text>
  <text x="200" y="50" text-anchor="end">WWWWWWWW</text>
  <text x="100" y="50" text-anchor="end">WWWWWWWW</text>
  <text x="210" y="50" text-anchor="end">WWWWWWWW</text>
</svg>'''
        result = self._check(source)
        bounds_warnings = self._text_bound_warnings(result)
        self.assertEqual(len(bounds_warnings), 1)
        self.assertIn('Detected 4 single-line text element(s)', bounds_warnings[0])

    def test_single_line_text_warning_resolves_inline_runs_and_transforms(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 200 100" font-size="20">
  <defs><g id="hidden"><text x="190" y="20">WWWW</text></g></defs>
  <g font-weight="semibold">
    <text x="150" y="20">WW<tspan>WW</tspan></text>
  </g>
  <text x="150" y="30" letter-spacing="50">A<tspan
        fill="#FF0000">B</tspan></text>
  <text x="50" y="40"><tspan x="10">WWWWWW</tspan>
    <tspan x="10" dy="20">WWWWWW</tspan></text>
  <g transform="translate(-200 0)"><text x="250" y="60">WWWW</text></g>
  <g transform="translate(100 0)"><text x="50" y="80">WWWW</text></g>
  <g transform="translate(100 0)"><g transform="rotate(180 0 45)">
    <text x="10" y="45" font-size="10">ii</text>
  </g></g>
  <text x="190" y="90">{{LONG_PLACEHOLDER}}</text>
</svg>'''
        result = self._check(source)
        bounds_warnings = self._text_bound_warnings(result)
        self.assertEqual(len(bounds_warnings), 1)
        self.assertIn('Detected 2 single-line text element(s)', bounds_warnings[0])

    def test_single_line_text_warning_includes_inherited_tracking(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 200 100">
  <g font-size="20" font-weight="semibold" letter-spacing="10">
    <text x="100" y="50">iiiiiiii</text>
  </g>
</svg>'''
        )
        bounds_warnings = self._text_bound_warnings(result)
        self.assertEqual(len(bounds_warnings), 1)
        self.assertIn("'iiiiiiii'", bounds_warnings[0])

    def test_single_line_text_warning_measures_negative_tracking_bounds(self):
        result = self._check(
            '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 200 100">
  <text x="50" y="25" font-size="20" letter-spacing="-100">AB</text>
  <text x="300" y="50" font-size="20" letter-spacing="-100">AB</text>
</svg>'''
        )
        bounds_warnings = self._text_bound_warnings(result)
        self.assertEqual(len(bounds_warnings), 1)
        self.assertIn('Detected 2 single-line text element(s)', bounds_warnings[0])

    def test_text_property_contract_preserves_registered_drawingml_semantics(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 640 360" font-style="italic">
  <g id="text-group" style="font-weight:600; text-anchor:end;
     letter-spacing:2; text-decoration:underline line-through">
    <text x="500" y="160" font-family="Arial" font-size="24">
      <tspan font-weight="500">Regular</tspan><tspan font-weight="600">Bold</tspan>
    </text>
  </g>
</svg>'''
        result = self._check(source)
        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'text-contract.svg'
            svg_path.write_text(source, encoding='utf-8')
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertEqual(slide_xml.count('<a:r>'), 2)
        self.assertEqual(slide_xml.count(' b="1"'), 1)
        self.assertEqual(slide_xml.count(' i="1"'), 2)
        self.assertEqual(slide_xml.count(' u="sng"'), 2)
        self.assertEqual(slide_xml.count(' strike="sngStrike"'), 2)
        self.assertEqual(slide_xml.count(' spc="150"'), 2)
        self.assertIn('algn="r"', slide_xml)

    def test_text_property_compatibility_aliases_warn_and_normalize(self):
        compatible = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 640 360">
  <text x="40" y="100" font-family="Arial" font-size="24"
        font-weight="medium" letter-spacing="2px"
        text-decoration="line-through underline">Medium</text>
  <text x="40" y="180" font-family="Arial" font-size="24"
        font-weight="semibold">Semibold</text>
</svg>'''
        canonical = compatible.replace(
            'font-weight="medium"', 'font-weight="500"'
        ).replace(
            'letter-spacing="2px"', 'letter-spacing="2"'
        ).replace(
            'text-decoration="line-through underline"',
            'text-decoration="underline line-through"',
        ).replace('font-weight="semibold"', 'font-weight="600"')

        result = self._check(compatible)
        warning_text = '\n'.join(result['warnings'])
        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertIn("font-weight='medium'", warning_text)
        self.assertIn('font-weight="500"', warning_text)
        self.assertIn("font-weight='semibold'", warning_text)
        self.assertIn('font-weight="600"', warning_text)
        self.assertIn("letter-spacing='2px'", warning_text)
        self.assertIn('letter-spacing="2"', warning_text)
        self.assertIn(
            "text-decoration='line-through underline'",
            warning_text,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'text-compatible.svg'
            svg_path.write_text(compatible, encoding='utf-8')
            compatible_xml = convert_svg_to_slide_shapes(svg_path)[0]
            svg_path.write_text(canonical, encoding='utf-8')
            canonical_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertEqual(compatible_xml, canonical_xml)
        self.assertEqual(compatible_xml.count(' b="1"'), 1)
        self.assertIn(' spc="150"', compatible_xml)
        self.assertIn(' u="sng"', compatible_xml)
        self.assertIn(' strike="sngStrike"', compatible_xml)

    def test_invalid_text_properties_block_checker_and_exporter(self):
        cases = {
            'anchor': ('text-anchor="banana"', 'text-anchor'),
            'weight': ('font-weight="heavy"', 'font-weight'),
            'style': ('font-style="oblique"', 'font-style'),
            'decoration': ('text-decoration="notunderline"', 'text-decoration'),
            'spacing': ('letter-spacing="banana"', 'letter-spacing'),
            'spacing_keyword': ('letter-spacing="normal"', 'letter-spacing'),
            'word_spacing': ('word-spacing="2"', 'word-spacing'),
            'baseline': ('style="dominant-baseline:middle"', 'dominant-baseline'),
            'unknown_attribute': ('textLength="120"', 'textLength'),
            'inline_filter': ('style="filter:url(#shadow)"', 'filter'),
        }
        for name, (declaration, expected) in cases.items():
            content = (
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                f'<text x="40" y="100" font-size="24" {declaration}>'
                'Broken</text></svg>'
            )
            with self.subTest(name=name):
                self._assert_checker_and_exporter_reject(
                    content,
                    expected,
                    'invalid project text property',
                )

    def test_compatible_letter_spacing_units_match_unitless_px(self):
        cases = (
            ('2px', '2', '150'),
            ('3pt', '4', '300'),
            ('1em', '24', '1800'),
        )
        for compatible, canonical, spacing in cases:
            source = (
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<text x="40" y="100" font-family="Arial" font-size="24" '
                f'letter-spacing="{compatible}">Tracking</text></svg>'
            )
            normalized = source.replace(
                f'letter-spacing="{compatible}"',
                f'letter-spacing="{canonical}"',
            )
            with self.subTest(value=compatible):
                result = self._check(source)
                self.assertTrue(result['passed'])
                self.assertIn(
                    f'letter-spacing="{canonical}"',
                    '\n'.join(result['warnings']),
                )
                with tempfile.TemporaryDirectory() as tmp_dir:
                    svg_path = Path(tmp_dir) / 'tracking.svg'
                    svg_path.write_text(source, encoding='utf-8')
                    compatible_xml = convert_svg_to_slide_shapes(svg_path)[0]
                    svg_path.write_text(normalized, encoding='utf-8')
                    canonical_xml = convert_svg_to_slide_shapes(svg_path)[0]
                self.assertEqual(compatible_xml, canonical_xml)
                self.assertIn(f' spc="{spacing}"', compatible_xml)

    def test_relative_font_sizes_share_one_inheritance_model(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 640 360" font-size="20">
  <g id="relative-text" font-size="1.5em" letter-spacing="1em">
    <text x="40" y="100" font-family="Arial" font-size="2em">Parent<tspan
          font-size=".5em">Child</tspan></text>
    <text x="40" y="180" font-family="Arial" font-size="2em">
      <tspan x="40" dy="60" font-size=".5em">Positioned child</tspan>
    </text>
  </g>
</svg>'''
        result = self._check(source)
        warning_text = '\n'.join(result['warnings'])
        self.assertTrue(result['passed'])
        self.assertEqual(result['errors'], [])
        self.assertIn('letter-spacing="30"', warning_text)
        self.assertNotIn('letter-spacing="60"', warning_text)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = Path(tmp_dir) / 'relative-text.svg'
            svg_path.write_text(source, encoding='utf-8')
            slide_xml = convert_svg_to_slide_shapes(svg_path)[0]

        self.assertIn(' sz="4500"', slide_xml)
        self.assertIn(' sz="2250"', slide_xml)
        self.assertIn(' spc="2250"', slide_xml)
        self.assertNotIn(' spc="4500"', slide_xml)

    def test_invalid_inherited_and_overridden_text_values_cannot_hide(self):
        cases = {
            'root_inheritance': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360" font-weight="heavy">'
                '<text x="40" y="100" font-size="24">Broken</text></svg>'
            ), 'font-weight'),
            'overridden_attribute': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<text x="40" y="100" font-size="24" font-weight="heavy" '
                'style="font-weight:700">Broken</text></svg>'
            ), 'font-weight'),
            'tspan_anchor': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<text x="40" y="100" font-size="24">'
                '<tspan text-anchor="end">Broken</tspan></text></svg>'
            ), 'text-anchor'),
            'spacing_range': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<text x="40" y="100" font-size="24" '
                'letter-spacing="5333.35">Broken</text></svg>'
            ), 'letter-spacing'),
            'malformed_inheritance': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<g style="font-weight"><text x="40" y="100" '
                'font-size="24">Broken</text></g></svg>'
            ), 'malformed inline style'),
            'hidden_invalid_font_size': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<text x="40" y="100" '
                'style="font-size:banana; font-size:24">Broken</text></svg>'
            ), 'font-size'),
            'wrong_element': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<rect x="20" y="20" width="100" height="60" '
                'font-weight="bold"/></svg>'
            ), 'cannot carry text property'),
            'unsupported_group_property': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<g line-height="2"><text x="40" y="100" '
                'font-size="24">Broken</text></g></svg>'
            ), 'line-height'),
            'unsupported_group_style': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<g style="font-feature-settings:smcp"><text x="40" '
                'y="100" font-size="24">Broken</text></g></svg>'
            ), 'font-feature-settings'),
            'unregistered_prefixed_property': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<g font-optical-sizing="auto"><text x="40" y="100" '
                'font-size="24">Broken</text></g></svg>'
            ), 'font-optical-sizing'),
            'malformed_prefixed_property': ((
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 640 360">'
                '<g style="font-optical-sizing"><text x="40" y="100" '
                'font-size="24">Broken</text></g></svg>'
            ), 'malformed inline style'),
        }
        for name, (content, expected) in cases.items():
            with self.subTest(name=name):
                self._assert_checker_and_exporter_reject(
                    content,
                    expected,
                    'invalid project text property',
                )


if __name__ == '__main__':
    unittest.main()
