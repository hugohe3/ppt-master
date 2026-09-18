"""Regressions from the 2026-09-18 template-plus-new-material Edit Native run."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_to_svg.emu_units import Xfrm  # noqa: E402
from pptx_to_svg.txbody_to_svg import convert_txbody  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
SVG = "http://www.w3.org/2000/svg"


def _tx_body(body_pr: str, run_pr: str = '<a:rPr sz="6000"/>') -> ET.Element:
    return ET.fromstring(
        f'<p:txBody xmlns:a="{A}" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f'{body_pr}<a:p><a:r>{run_pr}<a:t>61%</a:t></a:r></a:p></p:txBody>'
    )


def _convert(tx_body: ET.Element, theme_fonts: dict[str, str] | None = None) -> str:
    return convert_txbody(
        tx_body, Xfrm(x=0, y=0, w=400, h=200), None, theme_fonts=theme_fonts,
    ).svg


class ImportedTextFidelityTests(unittest.TestCase):
    def test_norm_autofit_font_scale_reaches_the_svg_font_size(self) -> None:
        plain = _convert(_tx_body('<a:bodyPr wrap="none"/>'))
        shrunk = _convert(_tx_body(
            '<a:bodyPr wrap="none"><a:normAutofit fontScale="25000" '
            'lnSpcReduction="20000"/></a:bodyPr>'
        ))
        self.assertIn('font-size="80"', plain)
        self.assertIn('font-size="20"', shrunk)

    def test_run_without_any_typeface_takes_the_theme_minor_pair(self) -> None:
        svg = _convert(
            _tx_body('<a:bodyPr/>'),
            {"minorLatin": "Arial", "minorEastAsia": "微软雅黑"},
        )
        self.assertIn('font-family="Arial, &quot;微软雅黑&quot;, sans-serif"', svg)


class SemanticShapeParagraphBlockTests(unittest.TestCase):
    def _errors(self, text: str) -> list[str]:
        root = ET.fromstring(
            f'<svg xmlns="{SVG}" viewBox="0 0 1280 720">'
            '<g id="s" data-pptx-semantic-object="shape" '
            f'data-pptx-frame="0 0 600 200">{text}</g></svg>'
        )
        result: dict = {"errors": [], "warnings": []}
        SVGQualityChecker._check_semantic_shape_text(root, result)
        return result["errors"]

    def test_absolute_y_rows_are_refused_before_export(self) -> None:
        errors = self._errors(
            '<text x="300" font-size="40"><tspan x="300" y="80">a</tspan>'
            '<tspan x="300" y="130">b</tspan></text>'
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("<tspan x dy>", errors[0])

    def test_relative_dy_rows_pass(self) -> None:
        self.assertEqual(self._errors(
            '<text x="300" y="80" font-size="40">a'
            '<tspan x="300" dy="50">b</tspan></text>'
        ), [])


if __name__ == "__main__":
    unittest.main()
