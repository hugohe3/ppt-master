"""Regressions from the Chandrayaan-3 Hindi Quick deck dogfood (2026-09-12)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.drawingml.utils import (  # noqa: E402
    _estimate_grapheme_width,
    unsafe_exported_font_faces,
)
from svg_to_pptx.native_objects.chart_style import (  # noqa: E402
    _fallback_text_attr_values,
    _most_common_value,
)


class DevanagariWidthTests(unittest.TestCase):
    def test_spacing_vowel_signs_advance(self) -> None:
        base = _estimate_grapheme_width("क", 100)
        self.assertGreater(_estimate_grapheme_width("का", 100), base)
        self.assertGreater(_estimate_grapheme_width("को", 100), base)
        # non-spacing signs (u, virama+consonant) still sit on the base
        self.assertEqual(_estimate_grapheme_width("कु", 100), base)
        self.assertEqual(_estimate_grapheme_width("क्र", 100), base)


class IndicFontTests(unittest.TestCase):
    def test_windows_indic_and_thai_faces_are_safe(self) -> None:
        for face in ("Nirmala UI", "Mangal", "Leelawadee UI"):
            self.assertEqual(unsafe_exported_font_faces(face), {}, face)


class TableFallbackFaceTests(unittest.TestCase):
    def test_drawn_table_face_is_recoverable(self) -> None:
        elem = ET.fromstring(
            '<g xmlns="http://www.w3.org/2000/svg" font-family="Nirmala UI">'
            '<text x="0" y="0">क</text><text x="0" y="20" font-family="Consolas">1</text>'
            '<text x="0" y="40">ख</text></g>'
        )
        self.assertEqual(
            _most_common_value(_fallback_text_attr_values(elem, "font-family")),
            "Nirmala UI",
        )


if __name__ == "__main__":
    unittest.main()
