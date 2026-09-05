#!/usr/bin/env python3
"""Unit tests for source_to_md.py output naming and image-flag routing."""

from __future__ import annotations

import argparse
import codecs
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import source_to_md  # noqa: E402

WEB_BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(WEB_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_BACKEND_DIR))
from web_to_md import is_plain_text_document  # noqa: E402
import web_to_md  # noqa: E402
from excel_to_md import _format_cell_value  # noqa: E402


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
    def test_downloaded_webp_is_oriented_before_png_conversion(self) -> None:
        from PIL import Image

        image = Image.new("RGB", (80, 40), "red")
        exif = image.getexif()
        exif[274] = 6
        encoded = io.BytesIO()
        image.save(encoded, format="WEBP", exif=exif)
        response = Mock(content=encoded.getvalue(), headers={"Content-Type": "image/webp"})
        content = web_to_md.BeautifulSoup('<p><img src="photo.webp"/></p>', "html.parser")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(web_to_md, "_http_get", return_value=response), redirect_stdout(io.StringIO()):
                count = web_to_md.download_and_rewrite_images(content, "https://example.com/", tmp, "images")
            self.assertEqual(count, 1)
            with Image.open(next(Path(tmp).glob("*.png"))) as converted:
                self.assertEqual(converted.size, (40, 80))
                self.assertNotIn(274, converted.getexif())

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


class ExcelCellValueTests(unittest.TestCase):
    def test_float_values_keep_excel_display_precision(self) -> None:
        # 15 significant digits, the precision Excel itself displays.
        cases = [
            (1234567.89, "1234567.89"),
            (0.1 + 0.2, "0.3"),
            (100.0, "100"),
            (1e-7, "1e-07"),
            (-0.5, "-0.5"),
            (1.2345678901234567, "1.23456789012346"),
            (-0.0, "-0"),
            (1e20, "1e+20"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                result = _format_cell_value(value)
                self.assertEqual(result, expected)
                self.assertAlmostEqual(float(result), value, delta=abs(value) * 1e-14)


class WebTraversalTests(unittest.TestCase):
    def test_inline_whitespace_is_preserved_once(self) -> None:
        cases = [
            ("<strong>Hello</strong> <em>World</em>", "**Hello** *World*"),
            ('See <a href="x">here</a> now', "See [here](x) now"),
            ("<code>a</code> <code>b</code>", "`a` `b`"),
            ("<strong>Hello</strong> \n\t <em>World</em>", "**Hello** *World*"),
            ("<strong>Hello</strong> <!-- comment --> <em>World</em>", "**Hello** *World*"),
            ("<strong>Hello</strong><em>World</em>", "**Hello***World*"),
        ]
        for html, expected in cases:
            with self.subTest(html=html):
                soup = web_to_md.BeautifulSoup(f"<p>{html}</p>", "html.parser")
                self.assertEqual(web_to_md.simple_html_to_markdown_traversal(soup), expected)

    def test_block_whitespace_does_not_leak_into_paragraphs(self) -> None:
        cases = [
            ("<p>one</p> \n <p>two</p>", "one\n\ntwo"),
            ("<div>one</div> \n <div>two</div>", "one\n\ntwo"),
            ("<section>one</section> \n <section>two</section>", "one\n\ntwo"),
            ("<ul> <li>one</li> <li>two</li> </ul>", "- one\n- two"),
            ("<p>  lead</p>", "lead"),
            ("<p>  lead</p><p>trail  </p>", "lead\n\ntrail"),
            ("<p> <strong>Hello</strong> <em>World</em> </p>", "**Hello** *World*"),
        ]
        for html, expected in cases:
            with self.subTest(html=html):
                soup = web_to_md.BeautifulSoup(html, "html.parser")
                self.assertEqual(web_to_md.simple_html_to_markdown_traversal(soup), expected)

    def test_preformatted_text_and_explicit_line_breaks_keep_spacing(self) -> None:
        cases = [
            ("<pre> a\n  b </pre>", "```\n a\n  b \n```"),
            ("<p>one<br>two</p>", "one  \ntwo"),
        ]
        for html, expected in cases:
            with self.subTest(html=html):
                soup = web_to_md.BeautifulSoup(html, "html.parser")
                self.assertEqual(web_to_md.simple_html_to_markdown_traversal(soup), expected)

    def test_links_resolve_relative_targets_and_keep_special_targets(self) -> None:
        cases = [
            ("../target", "[label](https://example.com/target)"),
            ("/abs", "[label](https://example.com/abs)"),
            ("//cdn.x/y", "[label](https://cdn.x/y)"),
            ("#frag", "[label](#frag)"),
            ("mailto:reader@example.com", "[label](mailto:reader@example.com)"),
            ("tel:+123456789", "[label](tel:+123456789)"),
            ("javascript:void(0)", "label"),
            ("JavaScript:void(0)", "label"),
        ]
        for href, expected in cases:
            with self.subTest(href=href):
                soup = web_to_md.BeautifulSoup(f'<p><a href="{href}">label</a></p>', "html.parser")
                self.assertEqual(
                    web_to_md.simple_html_to_markdown_traversal(soup, "https://example.com/a/page"),
                    expected,
                )

    def test_process_url_resolves_against_redirect_and_first_base_href(self) -> None:
        cases = [
            ("", "https://redirect.example/docs/"),
            ('<base href="https://base.example/root/">', "https://base.example/root/"),
            ('<base href="../assets/">', "https://redirect.example/assets/"),
            ('<base target="_blank"><base href="/first/"><base href="/ignored/">',
             "https://redirect.example/first/"),
        ]
        for base, expected_base in cases:
            with self.subTest(base=base), tempfile.TemporaryDirectory() as tmp:
                html = (
                    f"<html><head><title>Links</title>{base}</head><body>"
                    '<p><a href="target">target</a> <img src="pic.png" alt="pic"></p>'
                    "</body></html>"
                )
                response = Mock(
                    content=html.encode("utf-8"),
                    headers={"Content-Type": "text/html; charset=utf-8"},
                    encoding="utf-8",
                    apparent_encoding="utf-8",
                    url="https://redirect.example/docs/page",
                )
                response.raise_for_status.return_value = None
                output = Path(tmp) / "page.md"
                with patch.object(web_to_md, "_http_get", return_value=response), redirect_stdout(io.StringIO()):
                    result = web_to_md.process_url(
                        "https://original.example/start", str(output), download_images=False,
                    )
                self.assertTrue(result[0], result[2])
                markdown = output.read_text(encoding="utf-8")
                self.assertIn(f"[target]({expected_base}target)", markdown)
                self.assertIn(f"![pic]({expected_base}pic.png)", markdown)


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

    def test_passthrough_decodes_supported_encodings_without_changing_text(self) -> None:
        text = "# 中文金额 123.45\r\n\r\nKeep  spaces\tand tabs.\r\n"
        utf8 = text.encode("utf-8")
        cases = [
            ("utf8", utf8, "utf-8"),
            ("utf8_bom", codecs.BOM_UTF8 + utf8, "utf-8-sig"),
            ("utf16_le", codecs.BOM_UTF16_LE + text.encode("utf-16-le"), "utf-16"),
            ("utf16_be", codecs.BOM_UTF16_BE + text.encode("utf-16-be"), "utf-16"),
            ("gb18030", text.encode("gb18030"), "gb18030"),
        ]
        for name, raw, encoding in cases:
            for suffix in (".txt", ".md"):
                with self.subTest(encoding=name, suffix=suffix):
                    source = self.root / f"{name}{suffix}"
                    output = self.root / f"{name}_{suffix[1:]}_output.md"
                    source.write_bytes(raw)
                    result = self._run_cli(str(source), "-o", str(output))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(self._outputs(result), [output])
                    self.assertEqual(output.read_bytes(), utf8)
                    self.assertEqual(source.read_bytes(), raw)
                    profile = json.loads(output.with_suffix(".conversion_profile.json").read_text(encoding="utf-8"))
                    if encoding == "utf-8":
                        self.assertEqual(profile["warnings"], [])
                    else:
                        self.assertIn(encoding, result.stdout)
                        self.assertIn(encoding, " ".join(profile["warnings"]))

    def test_invalid_passthrough_fails_before_writing_outputs(self) -> None:
        cases = [
            bytes(range(256)),
            b"\x00\x01binary",
            codecs.BOM_UTF8 + b"\xff",
            codecs.BOM_UTF16_LE + b"A\x00B",
            codecs.BOM_UTF16_BE + b"\x00AB",
        ]
        for index, raw in enumerate(cases):
            with self.subTest(raw=raw):
                source = self.root / f"invalid_{index}.txt"
                output = self.root / f"output_{index}" / "result.md"
                source.write_bytes(raw)
                result = self._run_cli(str(source), "-o", str(output))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("[ERROR]", result.stderr)
                self.assertEqual(self._outputs(result), [])
                self.assertFalse(output.parent.exists())
                self.assertEqual(source.read_bytes(), raw)

    def test_non_utf8_passthrough_requires_a_distinct_output_path(self) -> None:
        for encoding in ("utf-8-sig", "utf-16", "gb18030"):
            with self.subTest(encoding=encoding):
                source = self.root / f"{encoding}.md"
                raw = "中文原稿\n".encode(encoding)
                source.write_bytes(raw)
                result = self._run_cli(str(source))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("-o", result.stderr)
                self.assertEqual(self._outputs(result), [])
                self.assertEqual(source.read_bytes(), raw)
                self.assertFalse(source.with_suffix(".conversion_profile.json").exists())


if __name__ == "__main__":
    unittest.main()
