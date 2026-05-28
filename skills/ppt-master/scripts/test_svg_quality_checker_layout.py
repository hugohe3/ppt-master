#!/usr/bin/env python3
"""Regression tests for SVG layout geometry warnings."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from svg_quality_checker import SVGQualityChecker


SVG_TEMPLATE = """<svg width="1280" height="720" viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
{body}
</svg>
"""


def check_svg(body: str) -> dict:
    with TemporaryDirectory() as tmp:
        svg_path = Path(tmp) / "slide.svg"
        svg_path.write_text(SVG_TEMPLATE.format(body=body), encoding="utf-8")
        return SVGQualityChecker().check_file(str(svg_path), "ppt169")


def layout_warnings(result: dict) -> list[str]:
    return [
        warning
        for warning in result["warnings"]
        if warning.startswith("Layout geometry:")
    ]


class LayoutGeometryCheckTests(unittest.TestCase):
    def test_aligned_card_row_has_no_layout_warning(self) -> None:
        result = check_svg(
            """
<g id="cards">
  <g id="card_1"><rect x="120" y="160" width="260" height="140"/></g>
  <g id="card_2"><rect x="420" y="160" width="260" height="140"/></g>
  <g id="card_3"><rect x="720" y="160" width="260" height="140"/></g>
</g>
"""
        )

        self.assertEqual([], layout_warnings(result))

    def test_warns_when_visible_geometry_extends_outside_canvas(self) -> None:
        result = check_svg(
            """
<g id="content"><rect x="-24" y="120" width="260" height="140"/></g>
"""
        )

        self.assertTrue(
            any("extends outside canvas" in warning for warning in layout_warnings(result)),
            result["warnings"],
        )

    def test_text_anchor_end_keeps_estimated_text_bbox_inside_canvas(self) -> None:
        result = check_svg(
            """
<text x="1220" y="690" text-anchor="end" font-size="14">Page subtitle</text>
"""
        )

        self.assertEqual([], layout_warnings(result))

    def test_large_decorative_bleed_primitive_does_not_warn_as_content_overflow(self) -> None:
        result = check_svg(
            """
<circle cx="1100" cy="150" r="200" fill="#EEE"/>
"""
        )

        self.assertEqual([], layout_warnings(result))

    def test_warns_on_row_alignment_drift_among_similar_cards(self) -> None:
        result = check_svg(
            """
<g id="cards">
  <g id="card_1"><rect x="120" y="160" width="260" height="140"/></g>
  <g id="card_2"><rect x="420" y="174" width="260" height="140"/></g>
  <g id="card_3"><rect x="720" y="160" width="260" height="140"/></g>
</g>
"""
        )

        self.assertTrue(
            any("row alignment drift" in warning for warning in layout_warnings(result)),
            result["warnings"],
        )

    def test_warns_on_horizontal_spacing_variance_among_similar_cards(self) -> None:
        result = check_svg(
            """
<g id="cards">
  <g id="card_1"><rect x="120" y="160" width="220" height="140"/></g>
  <g id="card_2"><rect x="380" y="160" width="220" height="140"/></g>
  <g id="card_3"><rect x="720" y="160" width="220" height="140"/></g>
</g>
"""
        )

        self.assertTrue(
            any("horizontal spacing variance" in warning for warning in layout_warnings(result)),
            result["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
