#!/usr/bin/env python3
"""Regression tests for fixes reported by the September 2026 dogfood runs.

Document URLs route to their own converter, bullet glyphs never promote a PDF
line to a heading, clause numbers stay text, a scanned PDF warns, ``<polygon>``
carries a filter, the exported slide size type token follows the canvas, and
``init`` keeps a pinned directory name.
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
from project_management.cli import _is_project_tree, PROJECTS_ROOT  # noqa: E402
from narration_sync import _project_input_path  # noqa: E402
from tts_backends import backend_edge  # noqa: E402
from compact_svg_styles import compact_svg_style_tree  # noqa: E402
from pptx_to_svg.preset_authoring import validate_authored_preset_tree  # noqa: E402
from pptx_ooxml.analyzer import _classify_page_type  # noqa: E402
from beautify_identity import _theme_font_refs  # noqa: E402
from svg_to_pptx.native_objects.chart_data import _chart_data_labels  # noqa: E402
from svg_to_pptx.native_objects.chart_xml import _data_labels_xml  # noqa: E402
from svg_to_pptx.drawingml.utils import parse_font_family  # noqa: E402
import text_measure  # noqa: E402

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


class PdfClauseAndScanTests(unittest.TestCase):
    def test_spaced_clause_number_is_not_a_list(self) -> None:
        self.assertFalse(pdf_to_md.detect_list_item("1. 1 职业名称")[0])
        self.assertFalse(pdf_to_md.detect_list_item("2. 1. 1 职业道德基本知识")[0])

    def test_ordinary_ordered_items_still_match(self) -> None:
        self.assertEqual(pdf_to_md.detect_list_item("1. 职业概况"), (True, "ol", "1. 职业概况"))
        self.assertEqual(pdf_to_md.detect_list_item("3. Overview"), (True, "ol", "3. Overview"))
        self.assertEqual(pdf_to_md.detect_list_item("1. 2024年营收"), (True, "ol", "1. 2024年营收"))
        self.assertFalse(pdf_to_md.detect_list_item("83.2% of respondents")[0])

    def test_scanned_pdf_warns(self) -> None:
        markdown = "\n".join(
            f"<!-- Page {i} -->\n![page {i}](scan_files/page_{i}.jpg)" for i in range(1, 14))
        warnings = pdf_to_md.scanned_pdf_warnings(markdown, 13, 13)
        self.assertEqual(len(warnings), 1)
        self.assertIn("13 page images", warnings[0])

    def test_text_pdf_does_not_warn(self) -> None:
        markdown = "\n".join("第一章 总则 " * 20 for _ in range(13))
        self.assertEqual(pdf_to_md.scanned_pdf_warnings(markdown, 13, 2), [])


class ImportSourcesProjectTreeTests(unittest.TestCase):
    def test_research_web_sources_dir_is_not_a_project(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECTS_ROOT) as tmp:
            root = Path(tmp)
            scratch = root.with_name(root.name + "_web_sources")
            scratch.mkdir()
            try:
                (scratch / "page.md").write_text("# page\n", encoding="utf-8")
                self.assertFalse(_is_project_tree(scratch / "page.md"))
                (root / "svg_output").mkdir()
                (root / "sources").mkdir()
                (root / "sources" / "a.md").write_text("# a\n", encoding="utf-8")
                self.assertTrue(_is_project_tree(root / "sources" / "a.md"))
            finally:
                for child in scratch.iterdir():
                    child.unlink()
                scratch.rmdir()


class NarrationRoundTests(unittest.TestCase):
    def test_subtitle_split_keeps_a_written_number_whole(self) -> None:
        text = "分别定点在东经八十度、一百一十点五度和一百四十度。"
        # Per-character word boundaries, as MiniMax returns them for Chinese.
        words = [
            backend_edge._MappedWord(start=i * 10, end=i * 10 + 10, source_start=i, source_end=i + 1)
            for i in range(len(text))
        ]
        parts = backend_edge._hard_split_span(text, (0, len(text)), words, 14)
        pieces = [text[a:b] for a, b in parts]
        for piece in pieces:
            self.assertFalse(
                piece.startswith(("一十", "十点", "点五")) or piece.endswith(("一百", "一百一", "点")),
                pieces,
            )
        self.assertEqual("".join(pieces), text.replace(" ", ""))

    def test_project_input_path_accepts_a_cwd_relative_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            (project / "exports").mkdir(parents=True)
            pptx = project / "exports" / "deck.pptx"
            pptx.write_bytes(b"PK")
            self.assertEqual(_project_input_path(project, "exports/deck.pptx"), project / "exports" / "deck.pptx")
            self.assertEqual(_project_input_path(project, str(pptx)), pptx)

    def test_web_to_md_refuses_output_file_for_several_urls(self) -> None:
        import io
        from contextlib import redirect_stderr
        buffer = io.StringIO()
        with redirect_stderr(buffer):
            rc = web_to_md.main(["https://example.org/a", "https://example.org/b", "-o", "out.md"])
        self.assertEqual(rc, 2)
        self.assertIn("--dir", buffer.getvalue())


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


class PresetPaintCompactionTests(unittest.TestCase):
    SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
        '<g id="rail-field" data-pptx-role="decoration" data-pptx-bounds="0 0 380 720">'
        '<rect x="0" y="0" width="300" height="720" fill="#004B20"/>'
        '<g id="p08-rail-edge" data-pptx-authoring="preset" data-pptx-object="shape" '
        'data-pptx-prst="rtTriangle" data-pptx-frame="300 0 80 720" fill="#004B20" '
        'stroke="none" transform="matrix(1 0 0 -1 0 720)">'
        '<path d="M 300 720 L 300 0 L 380 720 Z"/></g>'
        '</g></svg>'
    )

    def test_preset_keeps_local_paint(self) -> None:
        root = ET.fromstring(self.SVG)
        stats = compact_svg_style_tree(root)
        self.assertEqual(stats.changed_declarations, 0)
        self.assertEqual(validate_authored_preset_tree(root), [])

    def test_parent_paint_is_not_stripped_from_preset(self) -> None:
        root = ET.fromstring(self.SVG.replace(
            'data-pptx-bounds="0 0 380 720">',
            'data-pptx-bounds="0 0 380 720" fill="#004B20">',
        ))
        compact_svg_style_tree(root)
        preset = root.find('.//*[@id="p08-rail-edge"]')
        self.assertEqual(preset.get("fill"), "#004B20")
        self.assertEqual(validate_authored_preset_tree(root), [])

    def test_comment_nodes_do_not_crash(self) -> None:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        root = ET.fromstring(
            self.SVG.replace('<rect ', '<!-- chart-plot-area --><rect ', 1),
            parser=parser,
        )
        compact_svg_style_tree(root)
        self.assertEqual(validate_authored_preset_tree(root), [])


class BeautifyIntakeTests(unittest.TestCase):
    def test_prose_mentioning_part_stays_content(self) -> None:
        text = "涉及的主要扶持措施" + "对新增部分的场地按实际租金给予补贴。" * 10
        slots = [{}, {}]
        self.assertEqual(_classify_page_type(8, 16, text, slots), "content_candidate")
        self.assertEqual(
            _classify_page_type(3, 16, "第一部分 政府采购基本概念 PART ONE", slots),
            "chapter_candidate",
        )

    def test_theme_font_refs_resolve(self) -> None:
        refs = _theme_font_refs({
            "title": {"latin": "Verdana", "ea": "微软雅黑"},
            "body": {"latin": "Verdana", "ea": "微软雅黑"},
        })
        self.assertEqual(refs["+mn-ea"], "微软雅黑")
        self.assertEqual(refs["+mj-lt"], "Verdana")


class DataLabelPointTests(unittest.TestCase):
    @staticmethod
    def _xml(config: dict) -> str:
        return _data_labels_xml(
            config, chart_type="column", grouping="clustered", point_count=4,
            font_size=1400, default_color="#000000", default_font_face=None,
        )

    def test_show_flag_makes_points_overrides(self) -> None:
        xml = self._xml({"show_value": True, "points": [{"idx": 2, "delete": True}]})
        self.assertEqual(xml.count('<c:delete val="1"/>'), 1)
        self.assertIn('<c:showVal val="1"/><c:showCatName', xml.split("</c:dLbl>")[-1])

    def test_points_without_flag_list_the_only_labels(self) -> None:
        xml = self._xml({"points": [{"idx": 3}]})
        self.assertEqual(xml.count('<c:delete val="1"/>'), 3)

    def test_all_deleted_points_are_refused(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "no label remains"):
            _chart_data_labels(
                {"data_labels": {"points": [{"idx": 1, "delete": True}]}},
                "column", "clustered", 4,
            )


class JapaneseTypographyTests(unittest.TestCase):
    def test_small_kana_and_long_vowel_never_open_a_line(self) -> None:
        units = text_measure._protected_units("スーパーっゃ・")
        self.assertTrue(all(unit[0] not in "ーっゃ・" for unit in units))

    def test_wrapped_pdf_lines_join_without_space_between_cjk(self) -> None:
        self.assertEqual(pdf_to_md.join_wrapped_text("約６８億", "人ものお客様"), "約６８億人ものお客様")
        self.assertEqual(pdf_to_md.join_wrapped_text("新幹", "線"), "新幹線")
        self.assertEqual(pdf_to_md.join_wrapped_text("the high", "speed"), "the high speed")

    def test_ea_fallback_follows_deck_language(self) -> None:
        self.assertEqual(parse_font_family("'Georgia', serif", "ja-JP")["ea"], "Yu Mincho")
        self.assertEqual(parse_font_family("Arial", "ja")["ea"], "Yu Gothic")
        self.assertEqual(parse_font_family("'Hiragino Sans'", "ja-JP")["latin"], "Yu Gothic")
        self.assertEqual(parse_font_family("Arial", "zh-CN")["ea"], "Microsoft YaHei")
        self.assertEqual(parse_font_family("Arial")["ea"], "Microsoft YaHei")


class SlideSizeTypeTests(unittest.TestCase):
    def test_standard_ratios_keep_their_token(self) -> None:
        self.assertEqual(_slide_size_type(12192000, 6858000), "screen16x9")
        self.assertEqual(_slide_size_type(9144000, 6858000), "screen4x3")
        self.assertEqual(_slide_size_type(10287000, 18288000), "custom")
        self.assertEqual(_slide_size_type(11811000, 16706000), "custom")


if __name__ == "__main__":
    unittest.main()
