#!/usr/bin/env python3
"""Regression tests for document conversion content survival."""

from __future__ import annotations

import contextlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1] / "source_to_md"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import doc_to_md  # noqa: E402


class EpubSurvivalTests(unittest.TestCase):
    def _book(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("mimetype", "application/epub+zip")
            archive.writestr("META-INF/container.xml", (
                '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                '<rootfiles><rootfile full-path="content.opf" '
                'media-type="application/oebps-package+xml"/></rootfiles></container>'
            ))
            archive.writestr("content.opf", (
                '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
                '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
                '<dc:identifier id="id">book</dc:identifier><dc:title>Book</dc:title>'
                '<dc:language>en</dc:language></metadata><manifest>'
                '<item id="a" href="a/ch.xhtml" media-type="application/xhtml+xml"/>'
                '<item id="b" href="b/ch.xhtml" media-type="application/xhtml+xml"/>'
                '<item id="note" href="note.xhtml" media-type="application/xhtml+xml"/>'
                '<item id="ia" href="a/pic.svg" media-type="image/svg+xml"/>'
                '<item id="ib" href="b/pic.svg" media-type="image/svg+xml"/>'
                '</manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>'
            ))
            for chapter in ("a", "b"):
                archive.writestr(f"{chapter}/ch.xhtml", (
                    '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
                    f'<body><p>CHAPTER{chapter}</p><img src="pic.svg" alt="IMAGE{chapter}"/>'
                    '<p hidden="hidden">INTERACTIVEHIDDEN</p>'
                    '<p style="display:none">INTERACTIVECSS</p>'
                    '<template>INERTTEMPLATE</template><script>INERTSCRIPT</script>'
                    '<style>INERTSTYLE</style><a href="../note.xhtml">NOTELINK</a></body></html>'
                ))
                archive.writestr(f"{chapter}/pic.svg", (
                    '<svg xmlns="http://www.w3.org/2000/svg">'
                    f'<text>PIXELS{chapter}</text></svg>'
                ))
            archive.writestr("note.xhtml", (
                '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Note</title></head>'
                '<body><p>LINKEDNOTE</p></body></html>'
            ))

    def test_spine_supplemental_text_and_inert_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "book.epub"
            self._book(source)
            diagnostics = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(diagnostics):
                text = doc_to_md.convert_to_markdown(str(source), str(root / "book.md"))
            for marker in ("CHAPTERa", "CHAPTERb", "LINKEDNOTE", "INTERACTIVEHIDDEN", "INTERACTIVECSS"):
                self.assertIn(marker, text)
            for marker in ("INERTTEMPLATE", "INERTSCRIPT", "INERTSTYLE"):
                self.assertNotIn(marker, text)
            self.assertLess(text.index("CHAPTERb"), text.index("CHAPTERa"))
            self.assertLess(text.index("CHAPTERa"), text.index("LINKEDNOTE"))
            self.assertIn("outside the reading spine", diagnostics.getvalue())
            self.assertIn("non-rendered", diagnostics.getvalue())

    def test_navigation_document_is_not_appended_as_text(self) -> None:
        from ebooklib import epub

        book = epub.EpubBook()
        book.set_identifier("nav-test")
        book.set_title("Book")
        book.set_language("en")
        chapter = epub.EpubHtml(title="Chapter", file_name="c1.xhtml")
        chapter.content = "<h1>Chapter</h1><p>CHAPTERBODY</p>"
        book.add_item(chapter)
        book.toc = (chapter,)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = [chapter]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            epub.write_epub(root / "book.epub", book)
            diagnostics = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(diagnostics):
                text = doc_to_md.convert_to_markdown(str(root / "book.epub"), str(root / "book.md"))
        self.assertIn("CHAPTERBODY", text)
        self.assertNotIn("](c1.xhtml)", text)
        self.assertNotIn("outside the reading spine", diagnostics.getvalue())

    def test_same_basename_images_resolve_relative_to_each_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "book.epub"
            self._book(source)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                text = doc_to_md.convert_to_markdown(str(source), str(root / "book.md"))
            for chapter in ("a", "b"):
                match = re.search(rf"!\[IMAGE{chapter}\]\(([^)]+)\)", text)
                self.assertIsNotNone(match)
                self.assertIn(f"PIXELS{chapter}", (root / match[1]).read_text())
