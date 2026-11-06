#!/usr/bin/env python3
"""PPT Master - Source resource and link preservation regressions.

Usage:
    python3 -m unittest tests.test_source_resource_links

Examples:
    python3 -m unittest tests.test_source_resource_links.HtmlResourceTests

Dependencies:
    Document conversion dependencies and Pandoc for the CommonMark oracle.
"""

import base64
import contextlib
import html
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

BACKEND = Path(__file__).resolve().parents[1] / "source_to_md"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import doc_to_md  # noqa: E402


def _convert(source: Path) -> tuple[str, Path]:
    output = source.parent / "result.md"
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        markdown = doc_to_md.convert_to_markdown(str(source), str(output))
    return markdown, output


def _commonmark(markdown: str) -> dict:
    result = subprocess.run(
        ["pandoc", "--from=commonmark", "--to=json"],
        input=markdown, text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def _nodes(value: object, kind: str) -> list[dict]:
    found = []
    if isinstance(value, dict):
        if value.get("t") == kind:
            found.append(value)
        for child in value.values():
            found.extend(_nodes(child, kind))
    elif isinstance(value, list):
        for child in value:
            found.extend(_nodes(child, kind))
    return found


def _targets(markdown: str, kind: str) -> list[str]:
    return [node["c"][-1][0] for node in _nodes(_commonmark(markdown), kind)]


def _svg(marker: str) -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        f'<text>{marker}</text></svg>'
    ).encode("utf-8")


def _epub(path: Path, chapters: dict[str, str], images: dict[str, bytes]) -> None:
    manifest = []
    spine = []
    for index, name in enumerate(chapters):
        manifest.append(
            f'<item id="c{index}" href="{name}" media-type="application/xhtml+xml"/>'
        )
        spine.append(f'<itemref idref="c{index}"/>')
    for index, name in enumerate(images):
        manifest.append(f'<item id="i{index}" href="{name}" media-type="image/svg+xml"/>')
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
            '<dc:identifier id="id">resource-links</dc:identifier><dc:title>Resources</dc:title>'
            '<dc:language>en</dc:language></metadata>'
            f'<manifest>{"".join(manifest)}</manifest><spine>{"".join(spine)}</spine></package>'
        ))
        for name, body in chapters.items():
            archive.writestr(name, (
                '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
                f'<body>{body}</body></html>'
            ))
        for name, content in images.items():
            archive.writestr(name, content)


class HtmlResourceTests(unittest.TestCase):
    def test_file_uri_path_is_decoded_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "literal%20.svg"
            image.write_bytes(_svg("PERCENT"))
            source = root / "page.html"
            source.write_text(f'<img src="{image.as_uri()}?v=2#left" alt="asset"/>', encoding="utf-8")
            markdown, output = _convert(source)
            ref = urlsplit(_targets(markdown, "Image")[0])
            self.assertEqual((output.parent / unquote(ref.path)).read_bytes(), image.read_bytes())
            self.assertEqual((ref.query, ref.fragment), ("v=2", "left"))

    def test_local_image_uri_suffixes_preserve_bytes_and_suffix(self) -> None:
        for suffix in ("", "?v=2", "#left", "?v=2#left"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                payload = _svg("LOCAL")
                (root / "with space.svg").write_bytes(payload)
                source = root / "page.html"
                source.write_text(
                    f'<p><img src="with%20space.svg{suffix}" alt="asset"/></p>', encoding="utf-8",
                )
                markdown, output = _convert(source)
                targets = _targets(markdown, "Image")
                self.assertEqual(len(targets), 1)
                target = urlsplit(targets[0])
                self.assertEqual((output.parent / unquote(target.path)).read_bytes(), payload)
                self.assertEqual((target.query, target.fragment),
                                 (urlsplit("asset.svg" + suffix).query,
                                  urlsplit("asset.svg" + suffix).fragment))
                manifest = json.loads(
                    (output.parent / "result_files/image_manifest.json").read_text(encoding="utf-8")
                )
                self.assertEqual(len(manifest[0]["occurrences"]), 1)

    def test_first_base_href_resolves_directories_files_and_file_uris(self) -> None:
        cases = ("none", "current", "directory", "file", "first", "file_uri")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                assets = root / "assets"
                assets.mkdir()
                local = _svg("LOCAL")
                selected = _svg("SELECTED")
                (root / "pic.svg").write_bytes(local)
                (assets / "pic.svg").write_bytes(selected)
                bases = {
                    "none": "",
                    "current": '<base href="./"/>',
                    "directory": '<base href="assets/"/>',
                    "file": '<base href="assets/another.html"/>',
                    "first": '<base target="_blank"/><base href="assets/"/><base href="./"/>',
                    "file_uri": f'<base href="{assets.as_uri()}/"/>',
                }
                source = root / "page.html"
                source.write_text(
                    f'<html><head>{bases[case]}</head><body><img src="pic.svg" alt="asset"/>'
                    '</body></html>', encoding="utf-8",
                )
                markdown, output = _convert(source)
                targets = _targets(markdown, "Image")
                self.assertEqual(len(targets), 1)
                copied = output.parent / unquote(urlsplit(targets[0]).path)
                self.assertEqual(copied.read_bytes(), local if case in {"none", "current"} else selected)


class EpubResourceTests(unittest.TestCase):
    def test_chapter_relative_images_keep_uri_suffixes_and_identity(self) -> None:
        for suffix in ("", "?v=2", "#left", "?v=2#left"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "book.epub"
                images = {f"{name}/pic space.svg": _svg(name) for name in ("a", "b")}
                chapters = {
                    f"{name}/text/ch.xhtml":
                    f'<p>{name}</p><img src="../pic%20space.svg{suffix}" alt="{name}"/>'
                    for name in ("a", "b")
                }
                _epub(source, chapters, images)
                markdown, output = _convert(source)
                targets = _targets(markdown, "Image")
                self.assertEqual(len(targets), 2)
                for name, ref in zip(("a", "b"), targets):
                    target = urlsplit(ref)
                    self.assertEqual((output.parent / unquote(target.path)).read_bytes(), _svg(name))
                    expected = urlsplit("asset.svg" + suffix)
                    self.assertEqual((target.query, target.fragment), (expected.query, expected.fragment))


class NotebookResourceTests(unittest.TestCase):
    def test_attachment_prefixes_are_independent_in_both_orders(self) -> None:
        for names in (("a.png", "a.png@2x"), ("a.png@2x", "a.png"), ("a.png", "b.png")):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "book.ipynb"
                payloads = [_svg(name) for name in names]
                notebook = {
                    "nbformat": 4, "nbformat_minor": 5, "metadata": {},
                    "cells": [{
                        "cell_type": "markdown", "id": "attachments", "metadata": {},
                        "source": "\n\n".join(f"![{name}](attachment:{name})" for name in names),
                        "attachments": {
                            name: {"image/svg+xml": base64.b64encode(payload).decode("ascii")}
                            for name, payload in zip(names, payloads)
                        },
                    }],
                }
                source.write_text(json.dumps(notebook), encoding="utf-8")
                markdown, output = _convert(source)
                refs = _targets(markdown, "Image")
                self.assertEqual(len(refs), 2)
                self.assertEqual(len(set(refs)), 2)
                self.assertEqual(
                    [(output.parent / unquote(urlsplit(ref).path)).read_bytes() for ref in refs], payloads,
                )


class MarkdownLinkTests(unittest.TestCase):
    TARGETS = (
        "https://example.invalid/report)2026.pdf",
        "https://example.invalid/report(2026.pdf",
        "https://example.invalid/report(2026).pdf",
        "https://example.invalid/report%292026.pdf",
        "https://example.invalid/report?q=cost)&n=2",
        "https://example.invalid/report?q=(cost&n=2",
        "https://example.invalid/plain.pdf",
    )

    def _body(self) -> str:
        return "".join(
            f'<p><a href="{html.escape(target, quote=True)}">link {index}</a></p>'
            for index, target in enumerate(self.TARGETS)
        )

    def _assert_targets(self, markdown: str) -> None:
        self.assertEqual(
            [unquote(target) for target in _targets(markdown, "Link")],
            [unquote(target) for target in self.TARGETS],
        )

    def test_html_links_round_trip_through_commonmark(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "links.html"
            source.write_text(self._body(), encoding="utf-8")
            markdown, _ = _convert(source)
            self._assert_targets(markdown)

    def test_epub_links_round_trip_through_commonmark(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "links.epub"
            _epub(source, {"chapter.xhtml": self._body()}, {})
            markdown, _ = _convert(source)
            self._assert_targets(markdown)

    def test_docx_body_and_table_links_round_trip_through_commonmark(self) -> None:
        from docx import Document
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.opc.constants import RELATIONSHIP_TYPE

        for location in ("body", "table"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as temporary:
                doc = Document()
                for target in self.TARGETS:
                    paragraph = (doc.add_paragraph() if location == "body"
                                 else doc.add_table(rows=1, cols=1).cell(0, 0).paragraphs[0])
                    relationship = paragraph.part.relate_to(
                        target, RELATIONSHIP_TYPE.HYPERLINK, is_external=True,
                    )
                    hyperlink = OxmlElement("w:hyperlink")
                    hyperlink.set(qn("r:id"), relationship)
                    run = OxmlElement("w:r")
                    text = OxmlElement("w:t")
                    text.text = "Evidence"
                    run.append(text)
                    hyperlink.append(run)
                    paragraph._p.append(hyperlink)
                source = Path(temporary) / "links.docx"
                doc.save(source)
                markdown, _ = _convert(source)
                self._assert_targets(markdown)

    def test_docx_literal_numbered_paragraphs_remain_paragraphs(self) -> None:
        from docx import Document

        for marker in (")", "."):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as temporary:
                doc = Document()
                doc.add_paragraph(f"5{marker} Fifth independent paragraph")
                doc.add_paragraph(f"9{marker} Ninth independent paragraph")
                source = Path(temporary) / "numbers.docx"
                doc.save(source)
                markdown, _ = _convert(source)
                parsed = _commonmark(markdown)
                self.assertFalse(_nodes(parsed, "OrderedList"), markdown)
                words = [node["c"] for node in _nodes(parsed, "Str")]
                self.assertIn(f"5{marker}", words)
                self.assertIn(f"9{marker}", words)

    def test_docx_prose_parentheses_have_no_backslashes(self) -> None:
        from docx import Document

        with tempfile.TemporaryDirectory() as temporary:
            doc = Document()
            text = "收入增长 (见附注 3) 与成本 (2024)."
            doc.add_paragraph(text)
            source = Path(temporary) / "prose.docx"
            doc.save(source)
            markdown, _ = _convert(source)
            self.assertEqual(markdown.strip(), text)

    def test_cleanup_preserves_only_target_and_number_marker_parentheses(self) -> None:
        source = (
            r"Body \(note\), inline 3\) remains prose." "\n\n"
            r'[Label \(note\)](https://example.invalid/a\)b "Title \(note\)")' "\n\n"
            r"![Alt \(note\)](assets/a\(b.png)" "\n\n"
            r"![Angle](<assets/a\)b.svg>)" "\n\n"
            "[reference][report]\n\n"
            r"[report]: https://example.invalid/a\(b" "\n\n"
            r"  5\) Fifth \(note\)" "\n\n"
            r"  9\) Ninth \(note\)" "\n\n"
            "\t" r"7\) Tabbed \(note\)" "\n\n"
            r"  5\. Dotted \(note\)" "\n"
        )
        expected = (
            "Body (note), inline 3) remains prose.\n\n"
            r'[Label (note)](https://example.invalid/a\)b "Title (note)")' "\n\n"
            r"![Alt (note)](assets/a\(b.png)" "\n\n"
            r"![Angle](<assets/a\)b.svg>)" "\n\n"
            "[reference][report]\n\n"
            r"[report]: https://example.invalid/a\(b" "\n\n"
            r"  5\) Fifth (note)" "\n\n"
            r"  9\) Ninth (note)" "\n\n"
            "\t" r"7\) Tabbed (note)" "\n\n"
            r"  5\. Dotted (note)" "\n"
        )
        cleaned = doc_to_md._clean_mammoth_markdown(source)
        self.assertEqual(cleaned, expected)
        self.assertEqual(_targets(cleaned, "Link"), [
            "https://example.invalid/a)b", "https://example.invalid/a(b",
        ])
        self.assertEqual(_targets(cleaned, "Image"), ["assets/a(b.png", "assets/a)b.svg"])
        self.assertFalse(_nodes(_commonmark(cleaned), "OrderedList"))
