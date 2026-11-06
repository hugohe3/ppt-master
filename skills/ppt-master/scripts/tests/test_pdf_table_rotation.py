#!/usr/bin/env python3
"""PPT Master - Rotated PDF Table Regression Tests

Keep table cells and page text aligned without changing the source page.

Usage:
    python3 -m unittest tests.test_pdf_table_rotation

Examples:
    Run the module from the scripts directory.

Dependencies:
    PyMuPDF and the local PDF converter.
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1] / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
import pdf_to_md  # noqa: E402


ROWS = (("Item", "Unit", "Value"), ("Alpha", "km", "11.9"), ("Beta", "USD", "7.3"))


class PdfTableRotationTests(unittest.TestCase):
    def _page(self, document, angle, geometry):
        page = document.new_page(width=600, height=850)
        if geometry == "cropped":
            page.set_cropbox(fitz.Rect(50, 50, 550, 800))
        elif geometry == "offset":
            page.set_mediabox(fitz.Rect(30, 40, 630, 890))
            page.set_cropbox(fitz.Rect(50, 40, 540, 790))
        page.set_rotation(angle)
        derotate = +page.derotation_matrix
        page.set_rotation(0)
        page.insert_text(fitz.Point(72, 120) * derotate, "Body paragraph outside the table.",
                         fontsize=11, rotate=angle)
        xs, ys = (100, 220, 340, 460), (180, 210, 240, 270)
        for x in xs:
            page.draw_line(fitz.Point(x, ys[0]) * derotate, fitz.Point(x, ys[-1]) * derotate)
        for y in ys:
            page.draw_line(fitz.Point(xs[0], y) * derotate, fitz.Point(xs[-1], y) * derotate)
        for row, values in enumerate(ROWS):
            for column, value in enumerate(values):
                page.insert_text(fitz.Point(xs[column] + 8, ys[row] + 20) * derotate,
                                 value, fontsize=11, rotate=angle)
        page.set_rotation(angle)
        return page

    def _state(self, page):
        return (page.rotation, tuple(page.mediabox), tuple(page.cropbox), page.get_text(),
                page.parent.xref_object(page.xref),
                tuple(page.parent.xref_stream(xref) for xref in page.get_contents()))

    def test_quarter_turn_cells_share_page_text_coordinates(self):
        for angle in (90, 270):
            for geometry in ("plain", "cropped", "offset"):
                with self.subTest(angle=angle, geometry=geometry), fitz.open() as document:
                    page = self._page(document, angle, geometry)
                    original = self._state(page)
                    tables, _ = pdf_to_md.find_page_tables(page)
                    self.assertEqual(self._state(page), original)
                    self.assertEqual(len(tables), 1)
                    for row in ROWS:
                        self.assertIn("|" + "|".join(row) + "|", tables[0]["content"])
                    for block in page.get_text("blocks"):
                        if "Body paragraph" in block[4]:
                            self.assertTrue((fitz.Rect(block[:4]) & tables[0]["bbox"]).is_empty)
                        else:
                            bbox = fitz.Rect(block[:4])
                            self.assertGreater((bbox & tables[0]["bbox"]).get_area() / bbox.get_area(), 0.6)

    def test_conversion_keeps_each_cell_once_without_duplicate_prose(self):
        for angle in (90, 270):
            for geometry in ("plain", "cropped", "offset"):
                with self.subTest(angle=angle, geometry=geometry), tempfile.TemporaryDirectory() as directory:
                    source = Path(directory) / "source.pdf"
                    with fitz.open() as document:
                        self._page(document, angle, geometry)
                        document.save(source)
                    original = source.read_bytes()
                    with redirect_stdout(io.StringIO()):
                        markdown = pdf_to_md.extract_pdf_to_markdown(str(source), images="none")
                    self.assertIn("Body paragraph outside the table.", markdown)
                    for row in ROWS:
                        self.assertEqual(markdown.count("|" + "|".join(row) + "|"), 1)
                        for value in row:
                            self.assertEqual(markdown.count(value), 1)
                    self.assertEqual(source.read_bytes(), original)

    def test_zero_and_half_turn_do_not_enter_normalization(self):
        for angle in (0, 180):
            with self.subTest(angle=angle), fitz.open() as document:
                page = self._page(document, angle, "plain")
                # This check is about dispatch; retain the existing detector.
                with patch.object(fitz.Document, "insert_pdf", side_effect=AssertionError("normalized")):
                    pdf_to_md.find_page_tables(page)

    def test_blank_quarter_turn_pages_stay_empty_and_unchanged(self):
        for angle in (90, 270):
            with self.subTest(angle=angle), fitz.open() as document:
                page = document.new_page(width=600, height=850)
                page.set_cropbox(fitz.Rect(50, 50, 550, 800))
                page.set_rotation(angle)
                original = self._state(page)
                self.assertEqual(pdf_to_md.find_page_tables(page), ([], False))
                self.assertEqual(self._state(page), original)
