#!/usr/bin/env python3
"""Regression tests for table recovery in the PDF and spreadsheet converters.

Bulletin PDFs that rule only the middle columns must still yield a full table,
and a spreadsheet whose first row is a source note must keep the real header.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
import excel_to_md  # noqa: E402
import pdf_to_md  # noqa: E402


def _partially_ruled_table_page() -> fitz.Page:
    """Draw a 4-column table whose ruling lines enclose only columns 2 and 3."""
    doc = fitz.open()
    page = doc.new_page(width=600, height=400)
    rows = [
        ("Item", "Unit", "2024", "Change"),
        ("Passengers", "million", "4312", "11.9"),
        ("National", "million", "4085", "10.9"),
        ("Other", "million", "227", "34.0"),
        ("Turnover", "bn pkm", "15799", "7.3"),
    ]
    top = 100
    step = 24
    for row_index, row in enumerate(rows):
        y = top + row_index * step + 16
        for col_index, (x, text) in enumerate(zip((60, 240, 340, 460), row)):
            page.insert_text((x, y), text, fontsize=10)
    shape = page.new_shape()
    x0, x1 = 230, 430
    for row_index in range(len(rows) + 1):
        y = top + row_index * step
        shape.draw_line((x0, y), (x1, y))
    for x in (x0, 330, x1):
        shape.draw_line((x, top), (x, top + len(rows) * step))
    shape.finish(color=(0, 0, 0), width=0.8)
    shape.commit()
    return page


class RuledTableRecoveryTests(unittest.TestCase):
    def test_columns_outside_the_ruling_are_reattached(self) -> None:
        page = _partially_ruled_table_page()
        candidates, _continues = pdf_to_md.find_page_tables(page)
        self.assertEqual(len(candidates), 1)
        markdown = str(candidates[0]["content"])
        lines = markdown.splitlines()
        self.assertEqual(lines[0], "|Item|Unit|2024|Change|")
        self.assertIn("|Passengers|million|4312|11.9|", lines)
        self.assertIn("|Turnover|bn pkm|15799|7.3|", lines)
        self.assertEqual(candidates[0]["method"], "lines+text")
        bbox = candidates[0]["bbox"]
        self.assertLess(bbox.x0, 100)
        self.assertGreater(bbox.x1, 460)

    def test_prose_beside_a_ruled_table_is_left_alone(self) -> None:
        page = _partially_ruled_table_page()
        for row_index in range(5):
            page.insert_text(
                (10, 100 + row_index * 24 + 16),
                "A running sentence sits beside the table here",
                fontsize=8,
            )
        candidates, _continues = pdf_to_md.find_page_tables(page)
        self.assertEqual(len(candidates), 1)
        lines = str(candidates[0]["content"]).splitlines()
        self.assertEqual(lines[0], "|Unit|2024|Change|")
        self.assertNotIn("sentence", str(candidates[0]["content"]))
        self.assertGreaterEqual(candidates[0]["bbox"].x0, 230)


class SpreadsheetCaptionRowTests(unittest.TestCase):
    def _convert(self, build) -> str:
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "data"
        build(sheet)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "book.xlsx"
            workbook.save(source)
            return excel_to_md.convert_to_markdown(str(source), str(Path(tmp) / "book.md"))

    def test_source_note_in_a1_becomes_a_quote_not_the_header(self) -> None:
        def build(sheet) -> None:
            sheet.append(["Source: World Bank, IS.RRS.TOTL.KM, downloaded 2026-09-12"])
            sheet.append(["Country", "Code", 2000, 2001])
            sheet.append(["China", "CHN", 58656, 59079])

        markdown = self._convert(build)
        self.assertIn("> Source: World Bank, IS.RRS.TOTL.KM, downloaded 2026-09-12", markdown)
        self.assertIn("| Country | Code | 2000 | 2001 |", markdown)
        self.assertNotIn("| Source: World Bank", markdown)

    def test_merged_title_band_is_also_peeled(self) -> None:
        def build(sheet) -> None:
            sheet.append(["Quarterly revenue"])
            sheet.merge_cells("A1:C1")
            sheet.append(["Quarter", "Revenue", "Growth"])
            sheet.append(["Q1", 10, 0.1])

        markdown = self._convert(build)
        self.assertIn("> Quarterly revenue", markdown)
        self.assertIn("| Quarter | Revenue | Growth |", markdown)

    def test_single_column_sheets_and_real_headers_are_untouched(self) -> None:
        def build(sheet) -> None:
            sheet.append(["Name", "Score"])
            sheet.append(["Ann", 3])

        markdown = self._convert(build)
        self.assertIn("| Name | Score |", markdown)
        self.assertNotIn("> Name", markdown)

        def build_single(sheet) -> None:
            sheet.append(["Memo"])
            sheet.append(["Only one column"])

        markdown = self._convert(build_single)
        self.assertIn("| Memo |", markdown)
        self.assertNotIn("> Memo", markdown)
