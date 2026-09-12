#!/usr/bin/env python3
"""Regression tests for the 2026-09-12 sparse-input dogfood fixes.

Web pages that declare a charset but carry a few bad bytes keep that charset
under a lossy decode; a body extraction that keeps a sliver of the page warns;
and the carrier receipt counts design_spec §IX pages naming carried relations.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import web_to_md  # noqa: E402
from svg_quality.checker import count_carried_relationship_pages  # noqa: E402


def _response(raw: bytes, content_type: str = "text/html") -> SimpleNamespace:
    return SimpleNamespace(
        content=raw,
        headers={"Content-Type": content_type},
        encoding=None,
        apparent_encoding=None,
    )


class DeclaredCharsetLossyDecodeTests(unittest.TestCase):
    def test_declared_gb2312_survives_a_bad_byte(self) -> None:
        html = (
            '<html><head><meta charset="gb2312"><title>都江堰水利工程</title></head>'
            "<body><p>秦昭襄王五十一年，李冰主持修建都江堰。</p></body></html>"
        )
        raw = html.encode("gb2312") + b"\x81\x00" + "<p>尾声</p>".encode("gb2312")
        with self.assertRaises(UnicodeDecodeError):
            raw.decode("gb18030")
        text = web_to_md._decode_response_text(_response(raw))
        self.assertIn("都江堰水利工程", text)
        self.assertIn("李冰主持修建都江堰", text)
        self.assertIn("尾声", text)
        self.assertLess(text.count("�"), 3)

    def test_clean_declared_charset_is_still_strict(self) -> None:
        raw = "<meta charset=\"utf-8\"><p>Café</p>".encode("utf-8")
        self.assertEqual(web_to_md._decode_response_text(_response(raw)), raw.decode("utf-8"))


class BodyShortfallWarningTests(unittest.TestCase):
    def test_sliver_of_a_long_page_warns(self) -> None:
        page = "正文" * 1200
        warning = web_to_md._body_shortfall_warning("> 官方栏目", page)
        self.assertIsNotNone(warning)
        self.assertIn("content container was not recognised", warning)

    def test_short_pages_and_full_extractions_stay_quiet(self) -> None:
        self.assertIsNone(web_to_md._body_shortfall_warning("> 官方栏目", "栏目" * 50))
        page = "正文" * 1200
        self.assertIsNone(web_to_md._body_shortfall_warning(page[: len(page) // 2], page))


class RelationshipPageCountTests(unittest.TestCase):
    def test_counts_only_carried_relations(self) -> None:
        spec = "\n".join([
            "- **Relationships**: 六个年度值之间是 order(时间顺序)",
            "- **Relationships**: none",
            "- **Relationships**: 两条曲线之间是 contrast",
            "- **Relationships (binding)**: 国家铁路与其他铁路是 membership",
            "- **Relationships**：照片与数字之间是 link",
            "- **Audience move**: order of appearance is not a relationship line",
        ])
        self.assertEqual(count_carried_relationship_pages(spec), 3)

    def test_no_lines_means_zero(self) -> None:
        self.assertEqual(count_carried_relationship_pages("# nothing here\n"), 0)
