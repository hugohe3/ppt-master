#!/usr/bin/env python3
"""
PPT Master - Language Tag Tests

Unit tests for language tag normalization, Office region mapping, base extraction,
and RTL detection helpers in language_tags.py.

Usage:
    python3 -m unittest tests.test_language_tags

Dependencies:
    None (only uses standard library unittest)
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from language_tags import (  # noqa: E402
    LanguageTagError,
    _NATURAL_LANGUAGE_NAMES,
    _RTL_BASE_LANGUAGES,
    _RTL_SCRIPTS,
    _alias_key,
    language_base,
    language_uses_rtl,
    normalize_language_tag,
    office_language_tag,
)


class LanguageTagErrorTests(unittest.TestCase):
    """Tests for LanguageTagError exception hierarchy and behavior."""

    def test_inherits_from_value_error(self) -> None:
        self.assertTrue(issubclass(LanguageTagError, ValueError))

    def test_exception_instantiation_and_catch(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            raise LanguageTagError("custom error message")
        self.assertIn("custom error message", str(ctx.exception))
        self.assertIsInstance(ctx.exception, LanguageTagError)


class NormalizeLanguageTagAliasTests(unittest.TestCase):
    """Tests for natural-language aliases supported by normalize_language_tag."""

    def test_english_aliases(self) -> None:
        for alias in ("English", "英文", "英语", "英語"):
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), "en-US")

    def test_simplified_chinese_aliases(self) -> None:
        aliases = (
            "Chinese",
            "Chinese Simplified",
            "Chinese (Simplified)",
            "Simplified Chinese",
            "Mandarin",
            "中文",
            "汉语",
            "漢語",
            "普通话",
            "普通話",
            "简体",
            "簡體",
            "简体中文",
            "簡體中文",
            "简中",
        )
        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), "zh-Hans")

    def test_traditional_chinese_aliases(self) -> None:
        aliases = (
            "Chinese Traditional",
            "Chinese (Traditional)",
            "Traditional Chinese",
            "繁体",
            "繁體",
            "繁体中文",
            "繁體中文",
            "繁中",
        )
        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), "zh-Hant")

    def test_japanese_aliases(self) -> None:
        for alias in ("Japanese", "日本語", "日文", "日语", "日語"):
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), "ja-JP")

    def test_korean_aliases(self) -> None:
        aliases = (
            "Korean",
            "한국어",
            "조선말",
            "韩语",
            "韓語",
            "朝鲜语",
            "朝鮮語",
        )
        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), "ko-KR")

    def test_alias_case_and_whitespace_insensitivity(self) -> None:
        cases = {
            "  english  ": "en-US",
            "ENGLISH": "en-US",
            "chinese simplified": "zh-Hans",
            "  Traditional   Chinese  ": "zh-Hant",
            "JAPANESE": "ja-JP",
            "korean": "ko-KR",
        }
        for alias, expected in cases.items():
            with self.subTest(alias=alias):
                self.assertEqual(normalize_language_tag(alias), expected)

    def test_alias_key_normalization(self) -> None:
        self.assertEqual(_alias_key("  Simplified   Chinese\t\n"), "simplified chinese")
        self.assertEqual(_alias_key("ENGLISH"), "english")


class NormalizeLanguageTagValidTests(unittest.TestCase):
    """Tests for valid BCP-47 tag normalization with various subtag combinations."""

    def test_simple_language_tags(self) -> None:
        self.assertEqual(normalize_language_tag("en"), "en")
        self.assertEqual(normalize_language_tag("es"), "es")
        self.assertEqual(normalize_language_tag("fr"), "fr")
        self.assertEqual(normalize_language_tag("de"), "de")
        self.assertEqual(normalize_language_tag("cmn"), "cmn")

    def test_underscore_replacement(self) -> None:
        self.assertEqual(normalize_language_tag("en_US"), "en-US")
        self.assertEqual(normalize_language_tag("zh_Hans"), "zh-Hans")
        self.assertEqual(normalize_language_tag("zh_Hans_CN"), "zh-Hans-CN")
        self.assertEqual(normalize_language_tag("es_419"), "es-419")
        self.assertEqual(normalize_language_tag("ja_JP"), "ja-JP")

    def test_casing_canonicalization(self) -> None:
        self.assertEqual(normalize_language_tag("EN-us"), "en-US")
        self.assertEqual(normalize_language_tag("ZH-HANS"), "zh-Hans")
        self.assertEqual(normalize_language_tag("zh-hant-tw"), "zh-Hant-TW")
        self.assertEqual(normalize_language_tag("sr-latn-rs"), "sr-Latn-RS")
        self.assertEqual(normalize_language_tag("sr-cyrl-ba"), "sr-Cyrl-BA")
        self.assertEqual(normalize_language_tag("ES-419"), "es-419")
        self.assertEqual(normalize_language_tag("sl-NEDIS"), "sl-nedis")

    def test_extlang_subtags(self) -> None:
        self.assertEqual(normalize_language_tag("zh-cmn-Hans"), "zh-cmn-Hans")
        self.assertEqual(normalize_language_tag("zh-cmn-Hans-CN"), "zh-cmn-Hans-CN")
        self.assertEqual(normalize_language_tag("ar-aao"), "ar-aao")
        self.assertEqual(normalize_language_tag("ar-aao-Arab-EG"), "ar-aao-Arab-EG")

    def test_numeric_regions(self) -> None:
        self.assertEqual(normalize_language_tag("es-419"), "es-419")
        self.assertEqual(normalize_language_tag("ar-001"), "ar-001")
        self.assertEqual(normalize_language_tag("en-150"), "en-150")

    def test_variants(self) -> None:
        self.assertEqual(normalize_language_tag("sl-rozaj"), "sl-rozaj")
        self.assertEqual(normalize_language_tag("sl-rozaj-biske"), "sl-rozaj-biske")
        self.assertEqual(normalize_language_tag("de-CH-1901"), "de-CH-1901")
        self.assertEqual(normalize_language_tag("ca-valencia"), "ca-valencia")

    def test_extensions(self) -> None:
        self.assertEqual(
            normalize_language_tag("en-US-u-ca-buddhist"),
            "en-US-u-ca-buddhist",
        )
        self.assertEqual(
            normalize_language_tag("de-DE-u-attr-co-phonebk"),
            "de-DE-u-attr-co-phonebk",
        )
        self.assertEqual(
            normalize_language_tag("en-a-myext"),
            "en-a-myext",
        )

    def test_private_use(self) -> None:
        self.assertEqual(normalize_language_tag("en-US-x-custom"), "en-US-x-custom")
        self.assertEqual(
            normalize_language_tag("zh-Hans-x-priv1-priv2"),
            "zh-Hans-x-priv1-priv2",
        )
        self.assertEqual(
            normalize_language_tag("en-x-single"),
            "en-x-single",
        )

    def test_complex_combinations(self) -> None:
        tag = "zh-cmn-Hans-CN-variant1-a-ext1-x-priv1"
        self.assertEqual(
            normalize_language_tag("ZH-CMN-HANS-cn-VARIANT1-A-EXT1-X-PRIV1"),
            tag,
        )


class NormalizeLanguageTagInvalidTests(unittest.TestCase):
    """Tests for rejection of malformed or disallowed language inputs."""

    def test_empty_and_whitespace_inputs(self) -> None:
        invalid_inputs = ("", "   ", "\t\n", "  \r\n  ")
        for val in invalid_inputs:
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)
                self.assertIn("non-empty BCP-47 tag", str(ctx.exception))

    def test_non_string_inputs(self) -> None:
        non_strings = (None, 123, 45.67, True, False, [], {}, set())
        for val in non_strings:
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)  # type: ignore[arg-type]
                self.assertIn("non-empty BCP-47 tag", str(ctx.exception))

    def test_empty_parts_and_hyphen_errors(self) -> None:
        cases = ("-en", "en-", "en--US", "zh--Hans", "en---US", "-")
        for val in cases:
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)
                self.assertIn("invalid BCP-47 language tag", str(ctx.exception))

    def test_invalid_characters(self) -> None:
        cases = ("en@US", "en#US", "en.US", "en$US", "es ES", "en/US")
        for val in cases:
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError):
                    normalize_language_tag(val)

    def test_malformed_primary_language_subtag(self) -> None:
        # Single-letter language (must be 2-8 letters)
        with self.assertRaises(LanguageTagError):
            normalize_language_tag("a")
        with self.assertRaises(LanguageTagError):
            normalize_language_tag("a-US")

        # Over 8 letters
        with self.assertRaises(LanguageTagError):
            normalize_language_tag("toolonglanguage")

        # Digits in primary language subtag
        with self.assertRaises(LanguageTagError):
            normalize_language_tag("e1")
        with self.assertRaises(LanguageTagError):
            normalize_language_tag("123")

    def test_natural_language_names_rejected(self) -> None:
        for name in sorted(_NATURAL_LANGUAGE_NAMES):
            with self.subTest(name=name):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(name)
                self.assertIn("use a BCP-47 language tag", str(ctx.exception))

                # Also test uppercase / titlecase variant
                with self.assertRaises(LanguageTagError) as ctx2:
                    normalize_language_tag(name.capitalize())
                self.assertIn("use a BCP-47 language tag", str(ctx2.exception))

    def test_und_tag_rejected(self) -> None:
        for val in ("und", "UND", "und-US", "UND-Latn"):
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)
                self.assertIn("und is not a usable primary language", str(ctx.exception))

    def test_unscripted_unregioned_chinese_rejected(self) -> None:
        for val in ("zh", "ZH", "zh_"):
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)
                self.assertTrue(
                    "Chinese must declare a script or region" in str(ctx.exception)
                    or "invalid BCP-47 language tag" in str(ctx.exception)
                )

        # Chinese with only variant or extlang but no script or region
        with self.assertRaises(LanguageTagError) as ctx:
            normalize_language_tag("zh-variant1")
        self.assertIn("Chinese must declare a script or region", str(ctx.exception))

        with self.assertRaises(LanguageTagError) as ctx:
            normalize_language_tag("zh-cmn")
        self.assertIn("Chinese must declare a script or region", str(ctx.exception))

    def test_duplicate_variants_rejected(self) -> None:
        with self.assertRaises(LanguageTagError) as ctx:
            normalize_language_tag("sl-rozaj-rozaj")
        self.assertIn("duplicate BCP-47 variant", str(ctx.exception))

        with self.assertRaises(LanguageTagError) as ctx:
            normalize_language_tag("sl-nedis-nedis")
        self.assertIn("duplicate BCP-47 variant", str(ctx.exception))

    def test_duplicate_extensions_rejected(self) -> None:
        with self.assertRaises(LanguageTagError) as ctx:
            normalize_language_tag("en-u-ca-u-nu")
        self.assertIn("duplicate BCP-47 extension", str(ctx.exception))

    def test_extension_without_subtag_rejected(self) -> None:
        for val in ("en-u", "en-US-a"):
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)
                self.assertIn("requires a following subtag", str(ctx.exception))

    def test_private_use_without_subtag_rejected(self) -> None:
        for val in ("en-x", "zh-Hans-x", "en-US-X"):
            with self.subTest(val=val):
                with self.assertRaises(LanguageTagError) as ctx:
                    normalize_language_tag(val)
                self.assertIn("BCP-47 private use requires a following subtag", str(ctx.exception))

    def test_invalid_subtag_rejected(self) -> None:
        with self.assertRaises(LanguageTagError) as ctx:
            normalize_language_tag("en-toolongsubtagname")
        self.assertIn("invalid BCP-47 subtag", str(ctx.exception))


class OfficeLanguageTagTests(unittest.TestCase):
    """Tests for office_language_tag PowerPoint region mapping."""

    def test_chinese_simplified_mappings(self) -> None:
        self.assertEqual(office_language_tag("zh-Hans"), "zh-CN")
        self.assertEqual(office_language_tag("zh-Hans-CN"), "zh-CN")
        self.assertEqual(office_language_tag("zh-Hans-SG"), "zh-SG")
        # Non-whitelisted region for Hans falls back to CN
        self.assertEqual(office_language_tag("zh-Hans-US"), "zh-CN")
        self.assertEqual(office_language_tag("zh-Hans-MY"), "zh-CN")

    def test_chinese_traditional_mappings(self) -> None:
        self.assertEqual(office_language_tag("zh-Hant"), "zh-TW")
        self.assertEqual(office_language_tag("zh-Hant-TW"), "zh-TW")
        self.assertEqual(office_language_tag("zh-Hant-HK"), "zh-HK")
        self.assertEqual(office_language_tag("zh-Hant-MO"), "zh-MO")
        # Non-whitelisted region for Hant falls back to TW
        self.assertEqual(office_language_tag("zh-Hant-US"), "zh-TW")
        self.assertEqual(office_language_tag("zh-Hant-CN"), "zh-TW")

    def test_chinese_aliases_resolve_to_office_tags(self) -> None:
        self.assertEqual(office_language_tag("Chinese"), "zh-CN")
        self.assertEqual(office_language_tag("Simplified Chinese"), "zh-CN")
        self.assertEqual(office_language_tag("Traditional Chinese"), "zh-TW")
        self.assertEqual(office_language_tag("繁體中文"), "zh-TW")

    def test_chinese_regional_tags_pass_through(self) -> None:
        for tag in ("zh-CN", "zh-TW", "zh-HK", "zh-SG", "zh-MO"):
            with self.subTest(tag=tag):
                self.assertEqual(office_language_tag(tag), tag)

    def test_non_chinese_tags_pass_through_unchanged(self) -> None:
        tags = (
            "en-US",
            "en-GB",
            "ja-JP",
            "ko-KR",
            "es-ES",
            "fr-FR",
            "de-DE",
            "pt-BR",
            "ar-SA",
            "ru-RU",
            "it-IT",
        )
        for tag in tags:
            with self.subTest(tag=tag):
                self.assertEqual(office_language_tag(tag), tag)

    def test_non_chinese_aliases_resolve_cleanly(self) -> None:
        self.assertEqual(office_language_tag("English"), "en-US")
        self.assertEqual(office_language_tag("Japanese"), "ja-JP")
        self.assertEqual(office_language_tag("Korean"), "ko-KR")

    def test_invalid_tag_raises_error(self) -> None:
        with self.assertRaises(LanguageTagError):
            office_language_tag("")
        with self.assertRaises(LanguageTagError):
            office_language_tag("invalid language name")


class LanguageBaseTests(unittest.TestCase):
    """Tests for language_base primary language extraction."""

    def test_simple_tags(self) -> None:
        self.assertEqual(language_base("en-US"), "en")
        self.assertEqual(language_base("es-ES"), "es")
        self.assertEqual(language_base("fr-FR"), "fr")
        self.assertEqual(language_base("de-DE"), "de")
        self.assertEqual(language_base("ja-JP"), "ja")
        self.assertEqual(language_base("ko-KR"), "ko")

    def test_standalone_language(self) -> None:
        self.assertEqual(language_base("en"), "en")
        self.assertEqual(language_base("es"), "es")
        self.assertEqual(language_base("fr"), "fr")

    def test_chinese_tags(self) -> None:
        self.assertEqual(language_base("zh-Hans"), "zh")
        self.assertEqual(language_base("zh-Hant"), "zh")
        self.assertEqual(language_base("zh-CN"), "zh")
        self.assertEqual(language_base("zh-TW"), "zh")
        self.assertEqual(language_base("zh-Hans-CN"), "zh")
        self.assertEqual(language_base("zh-Hant-HK"), "zh")

    def test_three_letter_base_languages(self) -> None:
        self.assertEqual(language_base("cmn-Hans"), "cmn")
        self.assertEqual(language_base("yue-Hant"), "yue")

    def test_casing_and_underscores(self) -> None:
        self.assertEqual(language_base("EN_US"), "en")
        self.assertEqual(language_base("ZH_hans"), "zh")
        self.assertEqual(language_base("ES_419"), "es")

    def test_aliases(self) -> None:
        self.assertEqual(language_base("English"), "en")
        self.assertEqual(language_base("Chinese"), "zh")
        self.assertEqual(language_base("Traditional Chinese"), "zh")
        self.assertEqual(language_base("Japanese"), "ja")
        self.assertEqual(language_base("Korean"), "ko")

    def test_invalid_tag_raises_error(self) -> None:
        with self.assertRaises(LanguageTagError):
            language_base("")
        with self.assertRaises(LanguageTagError):
            language_base("french")


class LanguageUsesRtlTests(unittest.TestCase):
    """Tests for language_uses_rtl detection of right-to-left languages and scripts."""

    def test_rtl_base_languages_without_script(self) -> None:
        for lang in sorted(_RTL_BASE_LANGUAGES):
            with self.subTest(lang=lang):
                self.assertTrue(language_uses_rtl(lang))

        # With regional subtags
        self.assertTrue(language_uses_rtl("ar-SA"))
        self.assertTrue(language_uses_rtl("ar-EG"))
        self.assertTrue(language_uses_rtl("he-IL"))
        self.assertTrue(language_uses_rtl("fa-IR"))
        self.assertTrue(language_uses_rtl("ur-PK"))

    def test_explicit_rtl_scripts(self) -> None:
        for script in sorted(_RTL_SCRIPTS):
            with self.subTest(script=script):
                # Script with neutral or non-RTL base language
                tag = f"en-{script}"
                self.assertTrue(language_uses_rtl(tag))

        # Real-world script pairs
        self.assertTrue(language_uses_rtl("az-Arab"))
        self.assertTrue(language_uses_rtl("ms-Arab"))
        self.assertTrue(language_uses_rtl("syr-Syrc"))
        self.assertTrue(language_uses_rtl("ff-Adlm"))
        self.assertTrue(language_uses_rtl("rhg-Rohg"))
        self.assertTrue(language_uses_rtl("dv-Thaa"))

    def test_ltr_script_overrides_rtl_base_language(self) -> None:
        self.assertFalse(language_uses_rtl("ar-Latn"))
        self.assertFalse(language_uses_rtl("he-Latn"))
        self.assertFalse(language_uses_rtl("fa-Latn"))
        self.assertFalse(language_uses_rtl("ur-Latn"))
        self.assertFalse(language_uses_rtl("ug-Cyrl"))

    def test_ltr_base_languages(self) -> None:
        ltr_tags = (
            "en",
            "en-US",
            "en-GB",
            "es-ES",
            "fr-FR",
            "de-DE",
            "it-IT",
            "pt-BR",
            "ru-RU",
            "ja-JP",
            "ko-KR",
            "zh-Hans",
            "zh-Hant",
            "zh-CN",
            "zh-TW",
        )
        for tag in ltr_tags:
            with self.subTest(tag=tag):
                self.assertFalse(language_uses_rtl(tag))

    def test_aliases_rtl_status(self) -> None:
        self.assertFalse(language_uses_rtl("English"))
        self.assertFalse(language_uses_rtl("Chinese"))
        self.assertFalse(language_uses_rtl("Simplified Chinese"))
        self.assertFalse(language_uses_rtl("Traditional Chinese"))
        self.assertFalse(language_uses_rtl("Japanese"))
        self.assertFalse(language_uses_rtl("Korean"))

    def test_extlang_handling(self) -> None:
        # Base language 'ar' is RTL, extlang 'aao' should be skipped
        self.assertTrue(language_uses_rtl("ar-aao"))
        self.assertTrue(language_uses_rtl("ar-aao-Arab"))
        # Explicit Latn script after extlang overrides RTL
        self.assertFalse(language_uses_rtl("ar-aao-Latn"))

    def test_invalid_tag_raises_error(self) -> None:
        with self.assertRaises(LanguageTagError):
            language_uses_rtl("")
        with self.assertRaises(LanguageTagError):
            language_uses_rtl("invalid tag")


if __name__ == "__main__":
    unittest.main()
