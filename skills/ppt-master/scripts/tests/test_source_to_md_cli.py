#!/usr/bin/env python3
"""Unit tests for source_to_md.py output naming and image-flag routing."""

from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import source_to_md  # noqa: E402

WEB_BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(WEB_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_BACKEND_DIR))
from web_to_md import is_plain_text_document  # noqa: E402


def _args(**overrides: object) -> argparse.Namespace:
    values = dict(
        images=None,
        no_images=False,
        filter_images=False,
        render_vector_figures=False,
    )
    values.update(overrides)
    return argparse.Namespace(**values)


class OutputNamingTests(unittest.TestCase):
    def test_single_input_extensionless_output_gets_md_suffix(self) -> None:
        self.assertEqual(
            source_to_md._dispatch_output_arg(
                "https://example.com/post", "web", "sources_cf", False, set(),
            ),
            "sources_cf.md",
        )
        self.assertEqual(
            source_to_md._dispatch_output_arg(
                "report.docx", "doc", "notes.markdown", False, set(),
            ),
            "notes.markdown",
        )

    def test_existing_directory_still_keeps_default_name_inside_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = source_to_md._dispatch_output_arg(
                "report.docx", "doc", tmp, False, set(),
            )
            self.assertEqual(Path(result), Path(tmp) / "report.md")


class ImageFlagRoutingTests(unittest.TestCase):
    def test_no_images_is_accepted_for_web_and_pdf(self) -> None:
        self.assertTrue(
            source_to_md._validate_pdf_image_flags(
                _args(no_images=True), ["web", "pdf"],
            )
        )
        self.assertTrue(
            source_to_md._validate_pdf_image_flags(
                _args(images="none"), ["web"],
            )
        )

    def test_other_image_flags_stay_pdf_only(self) -> None:
        self.assertFalse(
            source_to_md._validate_pdf_image_flags(
                _args(filter_images=True), ["web"],
            )
        )
        self.assertFalse(
            source_to_md._validate_pdf_image_flags(
                _args(no_images=True), ["doc"],
            )
        )

    def test_no_images_is_a_no_op_for_markdown_and_text(self) -> None:
        self.assertTrue(
            source_to_md._validate_pdf_image_flags(
                _args(no_images=True), ["markdown", "text", "web"],
            )
        )


class RawTextUrlTests(unittest.TestCase):
    def test_markdown_url_with_markdown_body_is_plain_text(self) -> None:
        self.assertTrue(is_plain_text_document(
            "https://raw.githubusercontent.com/astral-sh/uv/main/CHANGELOG.md",
            "# Changelog\n\n## 0.12.10\n\nReleased on 2026-09-04.\n",
        ))

    def test_html_bodies_and_html_urls_still_go_through_the_extractor(self) -> None:
        self.assertFalse(is_plain_text_document(
            "https://example.com/notes.md",
            "<!DOCTYPE html><html><body><p>rendered</p></body></html>",
        ))
        self.assertFalse(is_plain_text_document(
            "https://docs.astral.sh/uv/", "# looks like markdown but is a page",
        ))

    def test_skips_images_reads_both_spellings(self) -> None:
        self.assertTrue(source_to_md._skips_images(_args(no_images=True)))
        self.assertTrue(source_to_md._skips_images(_args(images="none")))
        self.assertFalse(source_to_md._skips_images(_args(images="all")))


if __name__ == "__main__":
    unittest.main()
