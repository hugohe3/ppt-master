#!/usr/bin/env python3
"""Regression tests for literal Office text in Markdown source conversion.

Usage:
    python3 -m unittest tests.test_source_literal_text

Dependencies:
    Existing Office source-conversion dependencies and Pandoc for CommonMark.
"""

import subprocess
import sys
import tempfile
import unittest
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR / "source_to_md"))
from _markdown_text import escape_html_syntax, escape_markdown_text  # noqa: E402

READABLE_TEXT = "研发 R&D 投入, 若 a < b 且 x > y"
LITERALS = {
    "bold": "**STARLITERAL**",
    "code": "`BACKTICKLITERAL`",
    "underscore": "_ITALIC_ __BOLD__ ___BOTH___ normal_word",
    "link": "[LABELLITERAL](https://example.invalid/literal)",
    "image": "![ALTLITERAL](missing.png)",
    "html": "A<sup>2</sup>B",
    "entity": "&copy; &amp; &#65; &#x1F;",
    "break": "left<br>right",
    "html_image": '<img src="missing.png">',
    "literal_tag": "<b>标签</b>",
    "autolink": "<https://example.invalid/automatic>",
    "html_prefixes": "<!--literal--> <!DOCTYPE html> <?literal?>",
    "readable": READABLE_TEXT,
    "pipe": r"left\|right",
    "plain": "CONTROL中文😀",
}


class RenderedContent(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.tags = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "a":
            self.links.append(dict(attrs).get("href"))

    def handle_data(self, data):
        self.text.append(data)


class HtmlSyntaxEscapingTests(unittest.TestCase):
    def test_only_html_and_entity_prefixes_are_backslash_escaped(self):
        cases = (
            (READABLE_TEXT, READABLE_TEXT),
            ("<b>标签</b>", r"\<b>标签\</b>"),
            ("<https://example.invalid/>", r"\<https://example.invalid/>"),
            ("<!--x--> <!DOCTYPE html> <?x?>", r"\<!--x--> \<!DOCTYPE html> \<?x?>"),
            ("&amp; &#123; &#x1F; &#X1F;", r"\&amp; \&#123; \&#x1F; \&#X1F;"),
            ("<1 <中 < b >x R&D &amp & foo", "<1 <中 < b >x R&D &amp & foo"),
        )
        for original, expected in cases:
            with self.subTest(original=original):
                self.assertEqual(escape_html_syntax(original), expected)
        self.assertEqual(escape_markdown_text(r"\<b> \&amp;"), r"\\\<b> \\\&amp;")


def make_sources(root: Path) -> list[Path]:
    """Build fresh Office inputs with literal content and genuine structures."""
    from openpyxl import Workbook
    from pptx import Presentation
    from pptx.oxml import parse_xml
    from pptx.util import Inches

    root.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["CASEID", "VALUE"])
    for label, value in LITERALS.items():
        sheet.append([label, value])
    workbook.save(root / "literal.xlsx")

    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    m = "http://schemas.openxmlformats.org/officeDocument/2006/math"

    def paragraph(value):
        return '<w:p><w:r><w:t xml:space="preserve">' + escape(value) + '</w:t></w:r></w:p>'

    rows = ["<w:tr><w:tc>" + paragraph("CASEID") + "</w:tc><w:tc>" +
            paragraph("VALUE") + "</w:tc></w:tr>"]
    rows.extend("<w:tr><w:tc>" + paragraph(label) + "</w:tc><w:tc>" +
                paragraph(value) + "</w:tc></w:tr>" for label, value in LITERALS.items())
    genuine = ('<w:p><w:hyperlink r:id="link1"><w:r><w:t>Real [link]</w:t></w:r></w:hyperlink>'
               '<w:r><w:footnoteReference w:id="1"/></w:r>'
               '<m:oMath><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e>'
               '<m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:oMath></w:p>')
    rows.append('<w:tr><w:tc>' + paragraph("genuine") + '</w:tc><w:tc>' + genuine + '</w:tc></w:tr>')
    body = "".join(paragraph(value) for value in LITERALS.values())
    body += "<w:tbl>" + "".join(rows) + "</w:tbl>"
    content_types = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" '
                     'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" '
                     'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '<Override PartName="/word/footnotes.xml" '
                     'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
                     '</Types>')
    relns = "http://schemas.openxmlformats.org/package/2006/relationships"
    with zipfile.ZipFile(root / "literal.docx", "w") as package:
        package.writestr("[Content_Types].xml", content_types)
        package.writestr("_rels/.rels", f'<Relationships xmlns="{relns}"><Relationship Id="doc" '
                         f'Type="{r}/officeDocument" Target="word/document.xml"/></Relationships>')
        package.writestr("word/document.xml", f'<w:document xmlns:w="{w}" xmlns:r="{r}" xmlns:m="{m}">'
                         f'<w:body>{body}</w:body></w:document>')
        package.writestr("word/_rels/document.xml.rels", f'<Relationships xmlns="{relns}">'
                         f'<Relationship Id="link1" Type="{r}/hyperlink" Target="https://example.invalid/real" '
                         f'TargetMode="External"/><Relationship Id="notes" Type="{r}/footnotes" '
                         'Target="footnotes.xml"/></Relationships>')
        package.writestr("word/footnotes.xml", f'<w:footnotes xmlns:w="{w}"><w:footnote w:id="1">'
                         + paragraph("Real footnote.") + '</w:footnote></w:footnotes>')

    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    table_shape = slide.shapes.add_table(len(LITERALS) + 2, 2, Inches(0), Inches(0), Inches(8), Inches(5))
    table = table_shape.table
    table.cell(0, 0).text = "CASEID"
    table.cell(0, 1).text = "VALUE"
    for index, (label, value) in enumerate(LITERALS.items(), 1):
        table.cell(index, 0).text = label
        table.cell(index, 1).text = value
    table.cell(len(LITERALS) + 1, 0).text = "genuine"
    paragraph_node = table.cell(len(LITERALS) + 1, 1).text_frame.paragraphs[0]
    run = paragraph_node.add_run()
    run.text = "Real [link]"
    run.hyperlink.address = "https://example.invalid/real"
    paragraph_node._p.append(parse_xml(
        f'<a14:m xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" xmlns:m="{m}">'
        '<m:oMath><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e>'
        '<m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:oMath></a14:m>'
    ))
    presentation.save(root / "literal.pptx")
    return [root / f"literal.{suffix}" for suffix in ("xlsx", "docx", "pptx")]


class SourceLiteralTextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sources = make_sources(self.root)

    def _convert(self, suffix):
        source = next(item for item in self.sources if item.suffix == suffix)
        output = self.root / suffix.lstrip(".") / "converted.md"
        output.parent.mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "source_to_md.py"), str(source), "-o", str(output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output.read_text(encoding="utf-8")

    def _assert_literals(self, markdown):
        self.assertIn(r"\*\*STARLITERAL\*\*", markdown)
        self.assertIn(r"\`BACKTICKLITERAL\`", markdown)
        self.assertIn(r"\_ITALIC\_ \_\_BOLD\_\_ \_\_\_BOTH\_\_\_ normal_word", markdown)
        self.assertIn(r"\[LABELLITERAL\](https://example.invalid/literal)", markdown)
        self.assertIn(r"!\[ALTLITERAL\](missing.png)", markdown)
        self.assertIn(r"A\<sup>2\</sup>B", markdown)
        self.assertIn(r"\&copy; \&amp; \&#65; \&#x1F;", markdown)
        self.assertIn(r"left\<br>right", markdown)
        self.assertIn(r'\<img src="missing.png">', markdown)
        self.assertIn("CONTROL中文😀", markdown)
        self.assertNotIn("![ALTLITERAL](missing.png)", markdown)
        self.assertNotRegex(markdown, r'(?<!\\)<img src="missing.png">')

    def test_xlsx_strings_stay_literal(self):
        self._assert_literals(self._convert(".xlsx"))

    def test_docx_literals_keep_native_links_notes_and_math(self):
        markdown = self._convert(".docx")
        self._assert_literals(markdown)
        self.assertIn(r"[Real \[link\]](https://example.invalid/real)", markdown)
        self.assertIn("[^1]", markdown)
        self.assertIn("[^1]: Real footnote.", markdown)
        self.assertIn("$x^2$", markdown)

    def test_pptx_literals_keep_native_links_and_math(self):
        markdown = self._convert(".pptx")
        self._assert_literals(markdown)
        self.assertIn(r"[Real \[link\]](https://example.invalid/real)", markdown)
        self.assertIn("$x^2$", markdown)

    def test_readable_symbols_survive_all_four_office_paths(self):
        for suffix in (".docx", ".xlsx", ".pptx"):
            with self.subTest(suffix=suffix):
                markdown = self._convert(suffix)
                self.assertIn(READABLE_TEXT, markdown)
                if suffix == ".docx":
                    body, table = markdown.split("| CASEID | VALUE |", 1)
                    self.assertIn(READABLE_TEXT, body)
                    self.assertIn(READABLE_TEXT, table)

    def test_docx_body_html_prefixes_split_across_runs(self):
        from docx import Document

        document = Document()
        for fragments in (("&", "amp;"), ("<", "b>标签", "</", "b>"),
                          ("<", 'img src="missing.png">'),
                          ("研发 R", "&", "D 投入, 若 a ", "<", " b 且 x ", ">", " y")):
            paragraph = document.add_paragraph()
            for fragment in fragments:
                paragraph.add_run(fragment)
        document.save(self.root / "literal.docx")
        markdown = self._convert(".docx")
        self.assertIn(r"\&amp;", markdown)
        self.assertIn(r"\<b>标签\</b>", markdown)
        self.assertIn(r'\<img src="missing.png">', markdown)
        self.assertIn(READABLE_TEXT, markdown)

    def test_docx_table_html_prefixes_split_across_runs(self):
        from docx import Document

        document = Document()
        table = document.add_table(rows=4, cols=1)
        table.cell(0, 0).text = "Literal text"
        for row, fragments in enumerate((("&", "amp;"), ("<", "b>", "标签", "</b>"),
                                         (READABLE_TEXT,)), 1):
            paragraph = table.cell(row, 0).paragraphs[0]
            for fragment in fragments:
                paragraph.add_run(fragment)
        document.save(self.root / "literal.docx")
        markdown = self._convert(".docx")
        self.assertIn(r"| \&amp; |", markdown)
        self.assertIn(r"| \<b>标签\</b> |", markdown)
        self.assertIn(READABLE_TEXT, markdown)
        rendered = subprocess.run(
            ["pandoc", "-f", "commonmark+pipe_tables", "-t", "html"],
            input=markdown, capture_output=True, text=True, check=False,
        )
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        content = RenderedContent()
        content.feed(rendered.stdout)
        self.assertIn("&amp;", "".join(content.text))
        self.assertIn("<b>标签</b>", "".join(content.text))
        self.assertNotIn("b", content.tags)
        self.assertNotIn("img", content.tags)

    def test_commonmark_preserves_literal_tags_and_entities(self):
        for suffix in (".docx", ".xlsx", ".pptx"):
            with self.subTest(suffix=suffix):
                markdown = self._convert(suffix)
                rendered = subprocess.run(
                    ["pandoc", "-f", "commonmark+pipe_tables", "-t", "html"],
                    input=markdown, capture_output=True, text=True, check=False,
                )
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                content = RenderedContent()
                content.feed(rendered.stdout)
                text = "".join(content.text)
                occurrences = 2 if suffix == ".docx" else 1
                self.assertEqual(text.count("<b>标签</b>"), occurrences)
                self.assertEqual(text.count(LITERALS["entity"]), occurrences)
                self.assertEqual(text.count(LITERALS["html"]), occurrences)
                self.assertEqual(text.count(LITERALS["html_prefixes"]), occurrences)
                self.assertNotIn("b", content.tags)
                self.assertNotIn("img", content.tags)
                self.assertNotIn("https://example.invalid/literal", content.links)
                self.assertNotIn("https://example.invalid/automatic", content.links)
                if suffix != ".xlsx":
                    self.assertIn("https://example.invalid/real", content.links)

    def test_xlsx_merged_captions_keep_literal_block_prefixes(self):
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        captions = ("# LITERAL_HEADING", "- LITERAL_ITEM", "1. LITERAL_ITEM", "---", "-", "+", "1.", "1)")
        for row, value in enumerate(captions, 1):
            sheet.cell(row, 1, value)
            sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        sheet.append(["CASEID", "VALUE"])
        sheet.append(["plain", "CONTROL_TEXT"])
        workbook.save(self.root / "literal.xlsx")
        markdown = self._convert(".xlsx")
        self.assertIn(r"> \# LITERAL_HEADING", markdown)
        self.assertIn(r"> \- LITERAL_ITEM", markdown)
        self.assertIn(r"> 1\. LITERAL_ITEM", markdown)
        self.assertIn(r"> \---", markdown)
        for marker in (r"\-", r"\+", r"1\.", r"1\)"):
            self.assertIn(f"> {marker}\n", markdown)
        self.assertIn("| CASEID | VALUE |", markdown)
        self.assertIn("| plain | CONTROL_TEXT |", markdown)
