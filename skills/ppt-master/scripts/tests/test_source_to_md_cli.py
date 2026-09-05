#!/usr/bin/env python3
"""Unit tests for source_to_md.py output naming and image-flag routing."""

from __future__ import annotations

import argparse
import json
import subprocess
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


class SourceCollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _run_cli(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "source_to_md.py"), *arguments, "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def _outputs(self, result: subprocess.CompletedProcess) -> list[Path]:
        return [
            Path(json.loads(line)["markdown"])
            for line in result.stdout.splitlines() if line.startswith("{")
        ]

    def test_same_stem_batch_preserves_markdown_in_both_orders(self) -> None:
        for reverse in (False, True):
            for output_directory in (False, True):
                with self.subTest(reverse=reverse, output_directory=output_directory):
                    root = self.root / f"{reverse}_{output_directory}"
                    root.mkdir()
                    text_source = root / "same.txt"
                    markdown_source = root / "same.md"
                    text_source.write_text("TEXT-SOURCE\n", encoding="utf-8")
                    markdown_source.write_text("ORIGINAL-MARKDOWN\n", encoding="utf-8")
                    inputs = [text_source, markdown_source]
                    if reverse:
                        inputs.reverse()
                    arguments = [str(path) for path in inputs]
                    if output_directory:
                        arguments.extend(["-o", str(root)])
                    result = self._run_cli(*arguments)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(markdown_source.read_text(encoding="utf-8"), "ORIGINAL-MARKDOWN\n")
                    self.assertEqual(text_source.read_text(encoding="utf-8"), "TEXT-SOURCE\n")
                    outputs = self._outputs(result)
                    self.assertEqual(outputs, [root / "same_2.md", root / "same_3.md"])
                    for source, output in zip(inputs, outputs):
                        self.assertEqual(output.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
                    self.assertIn("Renamed output", result.stderr)
                    self.assertIn("Success: 2/2", result.stderr)

    def test_batch_outputs_with_the_same_stem_are_distinct(self) -> None:
        text_source = self.root / "same.txt"
        markdown_source = self.root / "same.markdown"
        text_source.write_text("TEXT-SOURCE\n", encoding="utf-8")
        markdown_source.write_text("ORIGINAL-MARKDOWN\n", encoding="utf-8")
        result = self._run_cli(str(text_source), str(markdown_source))
        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = self._outputs(result)
        self.assertEqual(outputs, [self.root / "same.md", self.root / "same_2.md"])
        self.assertEqual([path.read_text(encoding="utf-8") for path in outputs],
                         ["TEXT-SOURCE\n", "ORIGINAL-MARKDOWN\n"])

    def test_batch_suffixes_also_avoid_input_paths(self) -> None:
        inputs = [self.root / name for name in ("same.txt", "same.md", "same_2.md")]
        for index, source in enumerate(inputs):
            source.write_text(f"SOURCE-{index}\n", encoding="utf-8")
        result = self._run_cli(*(str(path) for path in inputs))
        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = self._outputs(result)
        self.assertEqual(len(set(outputs)), 3)
        self.assertFalse(set(inputs) & set(outputs))
        for index, (source, output) in enumerate(zip(inputs, outputs)):
            self.assertEqual(source.read_text(encoding="utf-8"), f"SOURCE-{index}\n")
            self.assertEqual(output.read_text(encoding="utf-8"), f"SOURCE-{index}\n")

    def test_explicit_output_refuses_another_existing_file(self) -> None:
        source = self.root / "same.txt"
        destination = self.root / "same.md"
        source.write_text("TEXT-SOURCE\n", encoding="utf-8")
        destination.write_text("ORIGINAL-MARKDOWN\n", encoding="utf-8")
        result = self._run_cli(str(source), "-o", str(destination))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[ERROR]", result.stderr)
        self.assertIn(str(destination), result.stderr)
        self.assertEqual(destination.read_text(encoding="utf-8"), "ORIGINAL-MARKDOWN\n")
        self.assertEqual(source.read_text(encoding="utf-8"), "TEXT-SOURCE\n")
        self.assertEqual(self._outputs(result), [])
        self.assertFalse(destination.with_suffix(".conversion_profile.json").exists())

    def test_single_markdown_passthrough_keeps_its_own_source(self) -> None:
        source = self.root / "same.md"
        source.write_text("ORIGINAL-MARKDOWN\n", encoding="utf-8")
        for options in ([], ["-o", str(source)]):
            with self.subTest(options=options):
                result = self._run_cli(str(source), *options)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self._outputs(result), [source])
                self.assertEqual(source.read_text(encoding="utf-8"), "ORIGINAL-MARKDOWN\n")


if __name__ == "__main__":
    unittest.main()
