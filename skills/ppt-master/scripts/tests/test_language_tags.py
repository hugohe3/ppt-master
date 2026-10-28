#!/usr/bin/env python3
"""Language-tag aliases and Office Chinese region mapping."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from language_tags import (  # noqa: E402
    LanguageTagError,
    normalize_language_tag,
    office_language_tag,
)


class LanguageTagTests(unittest.TestCase):
    def test_hong_kong_aliases_normalize_to_zh_hk(self):
        for alias in (
            "Hong Kong Chinese",
            "Chinese (Hong Kong)",
            "Cantonese",
            "港式中文",
            "香港中文",
            "粵語",
            "粤语",
            "廣東話",
            "广东话",
        ):
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), "zh-HK")
                self.assertEqual(office_language_tag(alias), "zh-HK")

    def test_explicit_zh_hk_and_hant_hk_stay_hong_kong(self):
        self.assertEqual(office_language_tag("zh-HK"), "zh-HK")
        self.assertEqual(office_language_tag("zh-Hant-HK"), "zh-HK")

    def test_bare_chinese_still_resolves_hans(self):
        self.assertEqual(normalize_language_tag("中文"), "zh-Hans")
        self.assertEqual(office_language_tag("中文"), "zh-CN")

    def test_bare_zh_still_rejected(self):
        with self.assertRaises(LanguageTagError):
            normalize_language_tag("zh")


if __name__ == "__main__":
    unittest.main()
