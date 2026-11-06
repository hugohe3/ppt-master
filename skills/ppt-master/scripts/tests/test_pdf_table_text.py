#!/usr/bin/env python3
"""PPT Master - PDF Table Text Regression Tests

Preserve page-text decimals, spaces, and cell boundaries across table strategies.

Usage:
    python3 -m unittest tests.test_pdf_table_text

Examples:
    Run the module from the scripts directory.

Dependencies:
    PyMuPDF and the local PDF converter.
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1] / 'source_to_md'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
import pdf_to_md  # noqa: E402


ROWS = [
    ['Item', 'Unit', 'Value', 'Change'],
    ['Passengers', 'million', '4312', '11.9'],
    ['Turnover', 'bn pkm', '15799', '7.3'],
    ['Cost', 'USD per year', '5000', '-2.5'],
    ['Carbon', 'kg CO2 eq', '12', '0.01'],
]


class PdfTableTextTests(unittest.TestCase):
    def _page(self, *, ruling='full', caption=False, font='helv', size=10, rows=None):
        rows = rows or ROWS
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=700, height=450)
        if caption:
            page.insert_text((50, 70), '表 1 交通统计', fontsize=12, fontname='china-s')
        for index, row in enumerate(rows):
            for x, text in zip((60, 240, 400, 550), row):
                page.insert_text((x, 118 + 30 * index), text, fontsize=size, fontname=font)
        if ruling != 'none':
            columns = (230, 390, 530) if ruling == 'partial' else (50, 230, 390, 530, 680)
            for x in columns:
                page.draw_line((x, 100), (x, 100 + 30 * len(rows)))
            for index in range(len(rows) + 1):
                y = 100 + 30 * index
                page.draw_line((columns[0], y), (columns[-1], y))
        return page

    def _assert_table(self, page, **kwargs):
        candidates, _ = pdf_to_md.find_page_tables(page, **kwargs)
        self.assertEqual(len(candidates), 1, candidates)
        markdown = str(candidates[0]['content'])
        for row in ROWS:
            self.assertIn('|' + '|'.join(row) + '|', markdown)
        self.assertNotIn('<br>.', markdown)
        self.assertEqual(len(markdown.splitlines()), len(ROWS) + 1)
        return candidates[0]

    def test_ruled_table_keeps_decimals_and_spaces_across_fonts(self) -> None:
        for font, size in (('helv', 10), ('cour', 8), ('tiro', 12)):
            with self.subTest(font=font, size=size):
                self._assert_table(self._page(font=font, size=size))

    def test_partially_ruled_table_uses_the_same_text_extraction(self) -> None:
        page = self._page(ruling='partial')
        # Isolate the partial-grid consumer from layout-enabled detectors that
        # complete the missing outer borders before returning the table.
        rows = [SimpleNamespace(
            bbox=(230, 100 + 30 * index, 530, 130 + 30 * index),
            cells=[(x0, 100 + 30 * index, x1, 130 + 30 * index)
                   for x0, x1 in ((230, 390), (390, 530))],
        ) for index in range(len(ROWS))]
        table = SimpleNamespace(bbox=(230, 100, 530, 250), rows=rows)
        with patch.object(fitz.Page, 'find_tables', return_value=[table]):
            candidate = self._assert_table(page)
        self.assertEqual(candidate['method'], 'lines+text')

    def test_borderless_table_keeps_page_text(self) -> None:
        self._assert_table(self._page(ruling='none', caption=True))

    def test_caption_and_continuation_text_strategies_keep_empty_bands_empty(self) -> None:
        find_tables = fitz.Page.find_tables

        def text_only(page, *args, **kwargs):
            if kwargs.get('strategy') == 'text':
                return find_tables(page, *args, **kwargs)
            return []

        for continuation in (False, True):
            with self.subTest(continuation=continuation):
                page = self._page(ruling='none', caption=not continuation)
                with patch.object(fitz.Page, 'find_tables', text_only):
                    candidate = self._assert_table(page, include_top_continuation=continuation)
                self.assertEqual(candidate['method'], 'continuation-text' if continuation else 'caption-text')

    def test_multiline_empty_and_merged_cells_do_not_duplicate_text(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=500, height=400)
        for y in (100, 140, 180, 220):
            page.draw_line((40, y), (460, y))
        for x in (40, 320, 460):
            page.draw_line((x, 100), (x, 220))
        page.draw_line((180, 140), (180, 220))
        for position, text in (
            ((50, 115), 'Merged title'), ((330, 115), 'Change'),
            ((50, 155), 'alpha\nbeta'), ((190, 155), 'bn pkm'), ((330, 155), '11.9'),
            ((50, 195), 'Pipe'), ((330, 195), 'left|right'),
        ):
            page.insert_text(position, text, fontsize=10)
        # Supply the drawn cell grid: layout detection can independently split
        # a multiline cell into rows, which is outside text extraction's scope.
        rows = [
            SimpleNamespace(bbox=(40, 100, 460, 140),
                            cells=[(40, 100, 320, 140), None, (320, 100, 460, 140)]),
            *[SimpleNamespace(bbox=(40, y, 460, y + 40),
                              cells=[(x0, y, x1, y + 40)
                                     for x0, x1 in ((40, 180), (180, 320), (320, 460))])
              for y in (140, 180)],
        ]
        table = SimpleNamespace(bbox=(40, 100, 460, 220), rows=rows)
        with patch.object(fitz.Page, 'find_tables', return_value=[table]):
            candidates, _ = pdf_to_md.find_page_tables(page)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['content'],
                         '|Merged title||Change|\n|---|---|---|\n'
                         '|alpha<br>beta|bn pkm|11.9|\n|Pipe||left\\|right|')

    def test_multiline_text_uses_visual_line_order(self) -> None:
        document = fitz.open()
        self.addCleanup(document.close)
        page = document.new_page(width=400, height=400)
        for position, text in (
            ((50, 115), 'Label'), ((190, 115), 'Value'), ((50, 155), 'Row'),
            ((190, 170), 'second line'), ((190, 155), 'first line'),
        ):
            page.insert_text(position, text, fontsize=10)
        table = SimpleNamespace(bbox=(40, 100, 360, 190), rows=[
            SimpleNamespace(bbox=(40, y0, 360, y1),
                            cells=[(40, y0, 180, y1), (180, y0, 360, y1)])
            for y0, y1 in ((100, 140), (140, 190))
        ])
        with patch.object(fitz.Page, 'find_tables', return_value=[table]):
            candidates, _ = pdf_to_md.find_page_tables(page)
        self.assertEqual(candidates[0]['content'],
                         '|Label|Value|\n|---|---|\n|Row|first line<br>second line|')
