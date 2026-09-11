#!/usr/bin/env python3
"""Regression tests for the fixes reported by the Why Leaves Turn dogfood run.

Document URLs route to their own converter, bullet glyphs never promote a PDF
line to a heading, ``<polygon>`` carries a filter, and the exported slide size
type token follows the canvas.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pdf_to_md  # noqa: E402
import web_to_md  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402
from svg_to_pptx.drawingml.utils import project_filter_errors  # noqa: E402
from svg_to_pptx.pptx_package.builder import _slide_size_type  # noqa: E402

PDF_URL = "https://www.example.gov/content/pkg/report/pdf/report.pdf"


class RemoteDocumentSuffixTests(unittest.TestCase):
    def test_pdf_url_with_pdf_content_type(self) -> None:
        self.assertEqual(
            web_to_md.remote_document_suffix(PDF_URL, "application/pdf", b"%PDF-1.4"), ".pdf")

    def test_suffixless_download_answering_pdf(self) -> None:
        self.assertEqual(
            web_to_md.remote_document_suffix(
                "https://example.org/download?id=7", "application/pdf; charset=binary", b"%PDF-1.7"),
            ".pdf")

    def test_body_magic_wins_over_wrong_content_type(self) -> None:
        self.assertEqual(
            web_to_md.remote_document_suffix(
                "https://example.org/files/report", "application/octet-stream", b"%PDF-1.7"),
            ".pdf")

    def test_docx_url_by_suffix(self) -> None:
        self.assertEqual(
            web_to_md.remote_document_suffix(
                "https://example.org/a/brief.docx", "application/octet-stream", b"PK\x03\x04"),
            ".docx")

    def test_html_viewer_at_document_url_stays_web(self) -> None:
        self.assertIsNone(
            web_to_md.remote_document_suffix(PDF_URL, "text/html; charset=utf-8", b"<!doctyp"))

    def test_ordinary_page_is_not_a_document(self) -> None:
        self.assertIsNone(
            web_to_md.remote_document_suffix(
                "https://example.org/article", "text/html", b"<html>"))
        self.assertIsNone(
            web_to_md.remote_document_suffix(
                "https://example.org/page.html", "", b"<html>"))


class PdfBulletTests(unittest.TestCase):
    def test_middot_bullet_is_a_list_item(self) -> None:
        is_list, kind, content = pdf_to_md.detect_list_item("·\x01 Oaks turn red, brown, or russet;")
        self.assertTrue(is_list)
        self.assertEqual(kind, "ul")
        self.assertEqual(content, "- Oaks turn red, brown, or russet;")

    def test_bullet_led_line_is_never_a_heading(self) -> None:
        size_map = {"body": 12.1, "h1": 13.6}
        self.assertEqual(pdf_to_md.get_heading_level(13.6, size_map, "· Oaks turn red", 4), 0)
        self.assertEqual(pdf_to_md.get_heading_level(13.6, size_map, "Autumn colours", 16), 1)

    def test_bullet_glyph_span_detection(self) -> None:
        self.assertTrue(pdf_to_md.is_bullet_glyph_span("· "))
        self.assertTrue(pdf_to_md.is_bullet_glyph_span("•"))
        self.assertTrue(pdf_to_md.is_bullet_glyph_span("·\x01"))
        self.assertFalse(pdf_to_md.is_bullet_glyph_span("Oaks"))
        self.assertFalse(pdf_to_md.is_bullet_glyph_span("· Oaks"))


class PolygonFilterTests(unittest.TestCase):
    SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
        '<defs><filter id="paperShadow"><feDropShadow dx="0" dy="6" stdDeviation="6" '
        'flood-color="#000000" flood-opacity="0.25"/></filter></defs>'
        '<polygon id="sheet" points="100,100 400,120 380,400 90,380" fill="#E8D9C4" '
        'filter="url(#paperShadow)"/>'
        '</svg>'
    )

    def test_polygon_is_a_public_filter_target(self) -> None:
        errors = project_filter_errors(ET.fromstring(self.SVG))
        self.assertEqual([e for e in errors if "cannot use filter" in e], [])

    def test_polygon_exports_its_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            svg_path = root / "page.svg"
            svg_path.write_text(self.SVG, encoding="utf-8")
            xml, *_rest = convert_svg_to_slide_shapes(svg_path, resource_root=root)
        self.assertIn("<a:outerShdw", xml)
        self.assertIn("Polygon", xml)


class SlideSizeTypeTests(unittest.TestCase):
    def test_standard_ratios_keep_their_token(self) -> None:
        self.assertEqual(_slide_size_type(12192000, 6858000), "screen16x9")
        self.assertEqual(_slide_size_type(9144000, 6858000), "screen4x3")
        self.assertEqual(_slide_size_type(10287000, 18288000), "custom")
        self.assertEqual(_slide_size_type(11811000, 16706000), "custom")


if __name__ == "__main__":
    unittest.main()
