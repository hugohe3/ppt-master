#!/usr/bin/env python3
"""Regression tests for the 2026-09-12 revision-round dogfood fixes.

A revision round that inserts or drops a page can leave design_spec §IX naming
a page no SVG carries while every per-file check passes; the final gate now
compares the outline roster with svg_output/.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_utils import validate_outline_roster  # noqa: E402

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>\n'


def _spec(slides: list[int]) -> str:
    blocks = "".join(
        f"#### Slide {n:02d} - Page {n}\n- **Audience move**: a → b\n"
        f"- **Relationships**: order\n"
        for n in slides
    )
    return "# Spec\n\n## VIII. Image Resource List\n\n## IX. Content Outline\n" + blocks + "\n## X. Notes\n"


def _project(tmp: str, outline: list[int], pages: list[int]) -> Path:
    root = Path(tmp)
    (root / "design_spec.md").write_text(_spec(outline), encoding="utf-8")
    (root / "svg_output").mkdir()
    for n in pages:
        (root / "svg_output" / f"{n:02d}_page.svg").write_text(SVG, encoding="utf-8")
    return root


class OutlineRosterTests(unittest.TestCase):
    def test_matching_roster_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, [1, 2, 3], [1, 2, 3])
            self.assertEqual(validate_outline_roster(root), [])

    def test_missing_page_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, [1, 2, 3], [1, 2])
            errors = validate_outline_roster(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("names 3 slide(s) but svg_output/ holds 2", errors[0])
            self.assertIn("no SVG for Slide 03", errors[0])

    def test_unplanned_page_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, [1, 2], [1, 2, 3])
            errors = validate_outline_roster(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("no §IX block for page 03", errors[0])

    def test_empty_svg_output_before_authoring_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, [1, 2, 3], [])
            self.assertEqual(validate_outline_roster(root), [])

    def test_spec_without_outline_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, [1, 2], [1, 2])
            (root / "design_spec.md").write_text("# Spec\n\n## I. Goal\n", encoding="utf-8")
            self.assertEqual(validate_outline_roster(root), [])


if __name__ == "__main__":
    unittest.main()
