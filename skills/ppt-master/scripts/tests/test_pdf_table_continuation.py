#!/usr/bin/env python3
"""Regression tests for merging PDF tables split across a page break.

Only page-break furniture may separate two halves of one table; a numeric or
labelled paragraph between same-header tables is content and must survive.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pdf_to_md  # noqa: E402

FIRST = "| A | B | C |\n|---|---|---|\n| one | two | three |"
SECOND = "| A | B | C |\n|---|---|---|\n| four | five | six |"
MERGED = "| A | B | C |\n|---|---|---|\n| one | two | three |\n| four | five | six |"


def _merge(markdown: str) -> str:
    return pdf_to_md.merge_markdown_continuation_tables(markdown)


class ContinuationMergeTests(unittest.TestCase):
    def test_page_break_with_printed_page_number_merges(self) -> None:
        source = f"{FIRST}\n\n12\n\n<!-- Page 3 -->\n\n{SECOND}"
        self.assertEqual(_merge(source), MERGED)

    def test_blank_gap_merges(self) -> None:
        self.assertEqual(_merge(f"{FIRST}\n\n{SECOND}"), MERGED)

    def test_numeric_paragraph_without_page_break_is_kept(self) -> None:
        for number in ("3000000", "2026", "42"):
            with self.subTest(number=number):
                source = f"{FIRST}\n{number}\n{SECOND}"
                self.assertEqual(_merge(source), source)

    def test_long_number_at_page_break_is_kept(self) -> None:
        source = f"{FIRST}\n\n3000000\n\n<!-- Page 3 -->\n\n{SECOND}"
        self.assertEqual(_merge(source), source)

    def test_label_paragraph_between_tables_is_kept(self) -> None:
        source = f"{FIRST}\n\n国有企业\n\n<!-- Page 3 -->\n\n{SECOND}"
        self.assertEqual(_merge(source), source)

    def test_lines_after_a_lone_table_are_kept(self) -> None:
        for tail in ("\n\nSome text", "\n\n2026\n\nSome text", "\n\n<!-- Page 2 -->\n\n7"):
            with self.subTest(tail=tail):
                source = FIRST + tail
                self.assertEqual(_merge(source), source)
