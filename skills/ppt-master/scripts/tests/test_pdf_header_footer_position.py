#!/usr/bin/env python3
"""Regression tests for position-aware PDF header and footer removal.

Repeated edge text must not erase signatures, and footer lines must not join
body dates before date/page-number cleanup.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
import pdf_to_md  # noqa: E402


class HeaderFooterPositionTests(unittest.TestCase):
    def _convert(self, last_page_lines: list[tuple[float, str]]) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "signature.pdf"
            with fitz.open() as doc:
                for number in range(1, 6):
                    page = doc.new_page(width=600, height=800)
                    page.insert_text((72, 40), "Example Company", fontname="helv", fontsize=12)
                    page.insert_text((72, 200), f"Body of section {number}.", fontname="helv", fontsize=12)
                    page.insert_text((72, 700), "Example Footer", fontname="helv", fontsize=12)
                    if number == 5:
                        for y, text in last_page_lines:
                            page.insert_text((72, y), text, fontname="helv", fontsize=12)
                    page.insert_text((290, 770), str(number), fontname="helv", fontsize=12)
                doc.save(source)
            return pdf_to_md.extract_pdf_to_markdown(str(source), images="none")

    def test_signature_equal_to_header_is_kept_and_header_removed(self) -> None:
        markdown = self._convert([(400, "Example Company"), (430, "October 2026")])
        self.assertEqual(markdown.count("Example Company"), 1)
        self.assertIn("October 2026", markdown)
        self.assertIn("Example Company", markdown.split("<!-- Page 5 -->")[1])

    def test_footer_page_number_does_not_swallow_body_date(self) -> None:
        markdown = self._convert([(430, "October 2026")])
        self.assertIn("October 2026", markdown)
        self.assertNotIn("October 2026 5", markdown)
        self.assertNotIn("Example Company", markdown)

    def test_signature_equal_to_header_inside_footer_is_kept(self) -> None:
        markdown = self._convert([(730, "Example Company"), (750, "October 2026")])
        self.assertEqual(markdown.count("Example Company"), 1)
        self.assertIn("October 2026", markdown)
        self.assertIn("Example Company", markdown.split("<!-- Page 5 -->")[1])
        self.assertNotIn("Example Footer", markdown)

    def test_date_and_page_number_inside_footer_are_removed(self) -> None:
        markdown = self._convert([(730, "November 2025 8")])
        self.assertNotIn("November 2025", markdown)
        self.assertIn("Body of section 5.", markdown)

    def test_date_and_page_number_inside_body_are_kept(self) -> None:
        markdown = self._convert([(430, "November 2025 8")])
        self.assertIn("November 2025 8", markdown)

    def test_line_crossing_header_boundary_is_kept(self) -> None:
        markdown = self._convert([(125, "Example Company")])
        self.assertEqual(markdown.count("Example Company"), 1)

    def test_repeated_footer_text_inside_body_is_kept(self) -> None:
        markdown = self._convert([(400, "Example Footer")])
        self.assertEqual(markdown.count("Example Footer"), 1)

    def test_body_line_in_block_crossing_header_boundary_is_kept(self) -> None:
        markdown = self._convert([(110, "Example Company"), (125, "Example Company")])
        self.assertEqual(markdown.count("Example Company"), 1)
