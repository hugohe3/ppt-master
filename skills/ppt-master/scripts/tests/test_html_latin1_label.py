#!/usr/bin/env python3
"""Check declared HTML encodings through the local and offline web converters."""

from __future__ import annotations

import codecs
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR / "source_to_md"))

import doc_to_md  # noqa: E402
import web_to_md  # noqa: E402


def _page(head: str, body: bytes) -> bytes:
    return f"<html><head>{head}</head><body><p>".encode() + body + b"</p></body></html>"


class HtmlCharsetTests(unittest.TestCase):
    def _local(self, raw: bytes) -> str:
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            source = Path(tmp) / "legacy.html"
            source.write_bytes(raw)
            doc_to_md.convert_to_markdown(str(source))
            return source.with_suffix(".md").read_text(encoding="utf-8").removesuffix("\n")

    def _web(self, raw: bytes, content_type: str, filename: str = "legacy.html", *, encoding=None) -> str:
        response = SimpleNamespace(
            url=f"https://example.invalid/{filename}", content=raw,
            headers={"Content-Type": content_type} if content_type else {}, encoding=encoding,
        )
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            output = Path(tmp) / "web.md"
            with patch.object(web_to_md, "fetch_response", return_value=response):
                result = web_to_md.process_url(response.url, str(output), download_images=False)
            self.assertTrue(result[0], result)
            # The web writer prepends crawl metadata and a title for HTML pages.
            markdown = output.read_text(encoding="utf-8")
            _, separator, body = markdown.partition("-->\n\n")
            self.assertTrue(separator)
            return body.removeprefix("# Untitled\n\n")

    def test_html_labels_match_across_local_and_web_markdown(self) -> None:
        sentence = "It’s a “quote” – done. Café €5."
        for label in (
            "ISO-8859-1", "latin1", "iso8859-1", "iso_8859-1", "latin-1", "l1",
            "csisolatin1", "cp819", "ibm819", "windows-1252", "cp1252", "x-cp1252",
            "iso_8859-1:1987", "ascii",
        ):
            with self.subTest(label=label):
                head = f'<meta http-equiv="Content-Type" content="text/html; charset={label}">'
                page = _page(head, sentence.encode("cp1252"))
                self.assertEqual((self._local(page), self._web(page, "text/html")), (sentence, sentence))

    def test_undefined_bytes_survive_explicit_meta_and_header_labels(self) -> None:
        body = b"X\x81\x8d\x8f\x90\x9d\x93quote\x94Y"
        expected = "X\x81\x8d\x8f\x90\x9d“quote”Y"
        for label in ("iso-8859-1", "windows-1252", "cp1252"):
            with self.subTest(label=label):
                page = _page(f'<meta charset="{label}">', body)
                self.assertEqual(self._local(page), expected)
                self.assertEqual(self._web(page, ""), expected)
                self.assertEqual(self._web(_page("", body), f"text/html; charset={label}"), expected)

    def test_iso_8859_2_keeps_its_c1_byte_and_its_own_letters(self) -> None:
        page = _page('<meta charset="iso-8859-2">', b"X\x93\xa1Y")
        self.assertEqual((self._local(page), self._web(page, "text/html")), ("X\x93ĄY", "X\x93ĄY"))
        conflicting = _page('<meta charset="latin1">', b"X\x93\xa1Y")
        self.assertEqual(self._web(conflicting, "text/html; charset=iso-8859-2"), "X\x93ĄY")

    def test_utf8_bom_wins_over_latin1_declarations(self) -> None:
        text = "“收入”"
        page = codecs.BOM_UTF8 + _page('<meta charset="latin1">', text.encode())
        self.assertEqual(self._local(page), text)
        self.assertEqual(self._web(page, "text/html; charset=latin1"), text)

    def test_plain_text_keeps_latin1_next_line(self) -> None:
        self.assertEqual(self._web(b"X\x85Y", "text/plain; charset=iso-8859-1", "page.txt"), "X\x85Y")
        self.assertEqual(self._web(b"X\x85Y", "", "page.txt", encoding="latin1"), "X\x85Y")

    def test_html_without_a_meta_declaration(self) -> None:
        head = '<!-- <meta charset="latin1"> -->'
        text = "“收入”"
        self.assertEqual(self._local(_page(head, text.encode())), text)
        self.assertEqual(self._web(_page(head, b"X\x93Y"), "text/html", encoding="latin1"), "X“Y")
