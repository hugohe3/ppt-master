#!/usr/bin/env python3
"""The first-page probes read the roster's page 1, not the lexically first file."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_to_pptx.drawingml.theme_fonts import load_theme_font_spec_from_pages  # noqa: E402
from svg_to_pptx.pptx_package.cli import _declared_primary_language  # noqa: E402

NO_DECK_LANGUAGE = "Quick roster declares no deck language"


def _page(title_family: str, body_family: str, language: str = "") -> str:
    """One Quick page: root font-family is the body face, the 72px text the title face."""
    language_attribute = f' lang="{language}"' if language else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"'
        f'{language_attribute} font-family="{body_family}">'
        f'<text x="80" y="260" font-family="{title_family}" font-size="72">経営戦略</text>'
        '<text x="80" y="360" font-size="24">年度計画</text></svg>\n'
    )


def _build_roster(pages_dir: Path, width: int, cover_language: str = "ja-JP") -> None:
    """Write pages 1 to 10, numbered with ``width`` digits, the cover carrying the deck language."""
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / f"{1:0{width}d}_cover.svg").write_text(
        _page("Cover Title", "Cover Body", cover_language), encoding="utf-8"
    )
    for number in range(2, 10):
        (pages_dir / f"{number:0{width}d}_body.svg").write_text(
            _page("Body Title", "Body Font"), encoding="utf-8"
        )
    (pages_dir / f"{10:0{width}d}_end.svg").write_text(
        _page("End Title", "End Body"), encoding="utf-8"
    )


class UnpaddedRosterTests(unittest.TestCase):
    """``10_end.svg`` sorts before ``1_cover.svg`` by name but is still page 10."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.pages = self.project / "svg_output"
        _build_roster(self.pages, width=1)

    def test_deck_language_comes_from_the_cover(self) -> None:
        self.assertEqual(_declared_primary_language(self.project), "ja-JP")

    def test_theme_fonts_come_from_the_cover(self) -> None:
        spec = load_theme_font_spec_from_pages(self.project, "ja-JP")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.major_family, "Cover Title")
        self.assertEqual(spec.minor_family, "Cover Body")

    def test_the_deck_language_advisory_lands_on_the_cover(self) -> None:
        _build_roster(self.pages, width=1, cover_language="")
        checker = SVGQualityChecker(quick_generate=True)
        cover = checker.check_file(str(self.pages / "1_cover.svg"))
        last = checker.check_file(str(self.pages / "10_end.svg"))
        self.assertTrue(any(NO_DECK_LANGUAGE in text for text in cover["warnings"]))
        self.assertFalse(any(NO_DECK_LANGUAGE in text for text in last["warnings"]))


class PaddedRosterTests(unittest.TestCase):
    """A zero-padded roster already agreed with name order and must not move."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.pages = self.project / "svg_output"
        _build_roster(self.pages, width=2)

    def test_deck_language_and_theme_fonts_still_come_from_the_cover(self) -> None:
        self.assertEqual(_declared_primary_language(self.project), "ja-JP")
        spec = load_theme_font_spec_from_pages(self.project, "ja-JP")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.major_family, "Cover Title")
        self.assertEqual(spec.minor_family, "Cover Body")

    def test_the_deck_language_advisory_lands_on_the_cover(self) -> None:
        _build_roster(self.pages, width=2, cover_language="")
        checker = SVGQualityChecker(quick_generate=True)
        cover = checker.check_file(str(self.pages / "01_cover.svg"))
        last = checker.check_file(str(self.pages / "10_end.svg"))
        self.assertTrue(any(NO_DECK_LANGUAGE in text for text in cover["warnings"]))
        self.assertFalse(any(NO_DECK_LANGUAGE in text for text in last["warnings"]))
