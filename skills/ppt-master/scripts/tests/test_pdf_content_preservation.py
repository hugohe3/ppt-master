#!/usr/bin/env python3
"""Regression tests: PDF table extraction keeps extracted cells as extracted.

All fixtures are PDFs constructed in memory or a temporary directory. Exercise
the public table finder without document-specific source files.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
import pdf_to_md  # noqa: E402


class TableContentPreservationTests(unittest.TestCase):
    def _extract_table(self, rows: list[list[str]]) -> str:
        column_width = 140
        row_height = 40
        width = len(rows[0]) * column_width
        height = len(rows) * row_height
        with fitz.open() as doc:
            page = doc.new_page(width=width + 80, height=height + 300)
            for column in range(len(rows[0]) + 1):
                x = 40 + column * column_width
                page.draw_line((x, 150), (x, 150 + height))
            for row in range(len(rows) + 1):
                y = 150 + row * row_height
                page.draw_line((40, y), (40 + width, y))
            for row_index, row in enumerate(rows):
                for column_index, value in enumerate(row):
                    if value:
                        page.insert_text(
                            (45 + column_index * column_width, 165 + row_index * row_height),
                            value,
                            fontname="china-s",
                            fontsize=10,
                        )
            tables, _ = pdf_to_md.find_page_tables(page)
            self.assertEqual(len(tables), 1)
            return tables[0]["content"]

    def _assert_rows_preserved(self, rows: list[list[str]]) -> None:
        lines = ["|" + "|".join(row) + "|" for row in rows]
        lines.insert(1, "|" + "|".join(["---"] * len(rows[0])) + "|")
        self.assertEqual(self._extract_table(rows), "\n".join(lines))

    def test_variable_categories_are_not_inferred_from_symbols(self) -> None:
        self._assert_rows_preserved([
            ["变量类型", "变量名称", "符号", "变量说明"],
            ["原始分类甲", "研发", "R＆D", "研发说明"],
            ["原始分类乙", "固定资本", "Fixed", "资本说明"],
            ["原始分类丙", "人力", "Hc", "人力说明"],
            ["原始分类丁", "税额", "Vat", "税额说明"],
            ["原始分类戊", "未知量", "Other", "未知说明"],
            ["", "无分类量", "Unknown", "分类留空"],
        ])

    def test_variable_rows_with_missing_fields_are_kept(self) -> None:
        self._assert_rows_preserved([
            ["变量类型", "变量名称", "符号", "变量说明"],
            ["有符号", "", "X", "没有名称"],
            ["无符号", "保留名称", "", "没有符号"],
            ["仅分类", "", "", ""],
        ])

    def test_paired_table_keeps_custom_headers_rows_and_extra_column(self) -> None:
        self._assert_rows_preserved([
            ["样本", "成对差分", "中位数", "离散度", "误差", "范围", "概率", "统计量", "自由度", "检验", "附加列"],
            ["次级头", "自定义名称", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "次级备注"],
            ["对一", "A", "2", "3", "4", "5", "6", "7", "8", "9", "额外数据"],
            ["合计", "B", "12", "13", "14", "15", "16", "17", "18", "19", "合计备注"],
        ])

    def test_regression_headers_and_first_column_text_are_kept(self) -> None:
        cases = {
            "single_outcome": [
                ["原始结果名称", "", ""],
                ["原始模型列", "(1)", "(2)"],
                ["x", "0.2", "0.3"],
            ],
            "model_first": [
                ["原始模型列", "(1)", "(2)"],
                ["原始结果列", "收入", "成本"],
                ["x", "0.2", "0.3"],
            ],
            "preface_before_model": [
                ["分组说明", "甲组", "乙组"],
                ["原始模型列", "(1)", "(2)"],
                ["原始结果列", "收入", "成本"],
                ["x", "0.2", "0.3"],
            ],
        }
        for name, rows in cases.items():
            with self.subTest(name=name):
                self._assert_rows_preserved(rows)

    def test_correlation_table_does_not_invent_a_column_or_diagonal(self) -> None:
        self._assert_rows_preserved([
            ["变量", "A", "B"],
            ["A", "0.95", ""],
            ["B", "0.25", "0.96"],
            ["C", "0.35", "0.45"],
        ])

    def test_empty_rows_and_columns_are_removed_without_losing_text(self) -> None:
        rows = [
            ["Label", "", "Value"],
            ["", "", ""],
            ["First", "", "alpha\nbeta"],
            ["Pipe", "", "left|right"],
        ]
        self.assertEqual(
            self._extract_table(rows),
            "|Label|Value|\n|---|---|\n|First|alpha<br>beta|\n|Pipe|left\\|right|",
        )

