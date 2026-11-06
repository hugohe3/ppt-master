#!/usr/bin/env python3
"""PPT Master - Rotated PDF Header and Footer Regression Tests

Keep body text and edge noise in their displayed page bands.

Usage:
    python3 -m unittest tests.test_pdf_header_footer_rotation

Examples:
    Run the module from the scripts directory.

Dependencies:
    PyMuPDF and the local PDF converter.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
import pdf_to_md  # noqa: E402


class HeaderFooterRotationTests(unittest.TestCase):
    def _convert(self, rotation, fill_page, count=3, crop=False):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "rotated.pdf"
            with fitz.open() as doc:
                for number in range(1, count + 1):
                    page = doc.new_page(width=600 if crop else 500, height=850 if crop else 750)
                    if crop:
                        page.set_cropbox(fitz.Rect(50, 50, 550, 800))
                    page.set_rotation(rotation)
                    fill_page(page, number)
                doc.save(source)
            original = source.read_bytes()
            markdown = pdf_to_md.extract_pdf_to_markdown(str(source), images="none")
            self.assertEqual(source.read_bytes(), original)
            return markdown

    def _display_text(self, page, y, text):
        page.insert_text(
            fitz.Point(72, y) * page.derotation_matrix,
            text,
            fontsize=11,
            rotate=page.rotation,
        )

    def test_repeated_body_is_preserved_at_all_rotations(self) -> None:
        def fill(page, number):
            page.insert_text((90, 470), "CONTRACTCLAUSE7", fontsize=11)
            page.insert_text((90, 540), f"CONCLUSIONMARK{number}", fontsize=12)

        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                markdown = self._convert(rotation, fill)
                self.assertEqual(markdown.count("CONTRACTCLAUSE7"), 3)
                for number in range(1, 4):
                    self.assertIn(f"CONCLUSIONMARK{number}", markdown)

    def test_date_page_pattern_in_rotated_body_is_preserved(self) -> None:
        def fill(page, number):
            page.insert_text((90, 470), "November 2025 8", fontsize=11)

        for rotation in (90, 270):
            with self.subTest(rotation=rotation):
                self.assertIn("November 2025 8", self._convert(rotation, fill, count=1))

    def test_display_edges_removed_but_body_signature_is_preserved(self) -> None:
        def fill(page, number):
            self._display_text(page, 35, "Running header")
            self._display_text(page, page.rect.height - 30, "Running footer")
            self._display_text(page, page.rect.height / 2, f"BODYMARK{number}")
            if number == 3:
                self._display_text(page, page.rect.height / 2 + 30, "Running header")

        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                markdown = self._convert(rotation, fill)
                self.assertEqual(markdown.count("Running header"), 1)
                self.assertNotIn("Running footer", markdown)
                for number in range(1, 4):
                    self.assertIn(f"BODYMARK{number}", markdown)

    def test_display_footer_date_page_pattern_is_removed(self) -> None:
        def fill(page, number):
            self._display_text(page, page.rect.height / 2, "BODYMARK")
            self._display_text(page, page.rect.height - 30, "November 2025 8")

        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                markdown = self._convert(rotation, fill, count=1)
                self.assertNotIn("November 2025", markdown)
                self.assertIn("BODYMARK", markdown)

    def test_rotated_text_crossing_display_band_boundary_is_preserved(self) -> None:
        def fill(page, number):
            self._display_text(page, 35, "Running header")
            self._display_text(page, page.rect.height - 30, "Running footer")
            if number == 3:
                self._display_text(page, page.rect.height * 0.15 + 5, "Running header")
                self._display_text(page, page.rect.height * 0.85 + 5, "Running footer")

        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                markdown = self._convert(rotation, fill)
                self.assertEqual(markdown.count("Running header"), 1)
                self.assertEqual(markdown.count("Running footer"), 1)

    def test_rotated_footer_signature_equal_to_header_is_preserved(self) -> None:
        def fill(page, number):
            self._display_text(page, 35, "Company signature")
            self._display_text(page, page.rect.height - 60, "Running footer")
            if number == 3:
                self._display_text(page, page.rect.height - 30, "Company signature")

        for rotation in (90, 180, 270):
            with self.subTest(rotation=rotation):
                markdown = self._convert(rotation, fill)
                self.assertEqual(markdown.count("Company signature"), 1)
                self.assertNotIn("Running footer", markdown)

    def test_cropped_rotated_page_uses_display_edges(self) -> None:
        def fill(page, number):
            self._display_text(page, 35, "Running header")
            self._display_text(page, page.rect.height / 2, "REPEATEDBODY")
            self._display_text(page, page.rect.height - 30, "Running footer")

        for rotation in (90, 270):
            with self.subTest(rotation=rotation):
                markdown = self._convert(rotation, fill, crop=True)
                self.assertEqual(markdown.count("REPEATEDBODY"), 3)
                self.assertNotIn("Running header", markdown)
                self.assertNotIn("Running footer", markdown)
