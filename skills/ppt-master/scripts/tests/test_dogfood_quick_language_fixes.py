"""Regressions from the Hebrew and Vietnamese Quick deck dogfoods (2026-09-12)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SCRIPTS_DIR / "source_to_md") not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR / "source_to_md"))

import web_to_md  # noqa: E402
from svg_to_pptx.drawingml.theme_fonts import load_theme_font_spec_from_pages  # noqa: E402
from svg_to_pptx.drawingml.utils import unsafe_exported_font_faces  # noqa: E402
from svg_to_pptx.pptx_package.cli import _declared_primary_language  # noqa: E402

PAGE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="he-IL" font-family="Segoe UI">'
    '<text x="10" y="80" font-family="David" font-size="48">שלום</text>'
    '<text x="10" y="120" font-size="20">טקסט</text></svg>\n'
)


class QuickLanguageChannelTests(unittest.TestCase):
    def test_root_lang_is_the_lockless_deck_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "svg_output").mkdir()
            (project / "svg_output" / "01_cover.svg").write_text(PAGE, encoding="utf-8")
            self.assertEqual(_declared_primary_language(project), "he-IL")
            spec = load_theme_font_spec_from_pages(project, "he-IL")
            self.assertIsNotNone(spec)
            self.assertEqual(spec.major_family, "David")
            self.assertEqual(spec.minor_family, "Segoe UI")
            self.assertEqual(spec.cs_scripts, ("Hebr",))

    def test_missing_root_lang_yields_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "svg_output").mkdir()
            (project / "svg_output" / "01_cover.svg").write_text(
                PAGE.replace(' lang="he-IL"', ''), encoding="utf-8"
            )
            self.assertIsNone(_declared_primary_language(project))


class FilenameTransliterationTests(unittest.TestCase):
    def test_vietnamese_title_keeps_its_letters(self) -> None:
        self.assertEqual(
            web_to_md.sanitize_filename("Khát vọng từ Buôn Ma Thuột - Thành phố cà phê"),
            "Khat_vong_tu_Buon_Ma_Thuot_-_Thanh_pho_ca_phe",
        )

    def test_other_scripts_survive(self) -> None:
        self.assertEqual(web_to_md.sanitize_filename("中国 报告 2025"), "中国_报告_2025")
        self.assertEqual(web_to_md.sanitize_filename("מגילות ים המלח"), "מגילות_ים_המלח")


class HebrewFaceTests(unittest.TestCase):
    def test_windows_hebrew_faces_are_safe(self) -> None:
        self.assertEqual(unsafe_exported_font_faces("David"), {})


if __name__ == "__main__":
    unittest.main()
