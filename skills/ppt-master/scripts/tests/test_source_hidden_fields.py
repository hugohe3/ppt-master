#!/usr/bin/env python3
"""Regress DOCX visible text inside fields, tables, and content controls.

Usage: python3 -m unittest tests.test_source_hidden_fields
Dependencies: python-docx, mammoth
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source_to_md"))
import doc_to_md  # noqa: E402


def write_fixture(path: Path) -> None:
    """Build a document with every field/container combination and controls."""
    doc = Document()
    for table in (False, True):
        for control in (False, True):
            paragraph = doc.add_table(rows=1, cols=1).cell(0, 0).paragraphs[0] if table else doc.add_paragraph()
            label = f"T{int(table)}C{int(control)}"
            field = (
                '<w:fldSimple w:instr="AUTHOR">'
                f'<w:r><w:t>VISIBLE_{label}</w:t></w:r>'
                f'<w:r><w:rPr><w:vanish/></w:rPr><w:t>HIDDEN_{label}</w:t></w:r>'
                f'<w:r><w:rPr><w:vanish w:val="false"/></w:rPr><w:t>FALSE_{label}</w:t></w:r>'
                '</w:fldSimple>'
            )
            if control:
                field = f'<w:sdt><w:sdtContent>{field}</w:sdtContent></w:sdt>'
            paragraph._p.append(parse_xml(f'<w:r {nsdecls("w")}><w:t>PLAIN_{label}</w:t></w:r>'))
            paragraph._p.append(parse_xml(f'<w:customXml {nsdecls("w")}>{field}</w:customXml>')[0])
    doc.add_paragraph()._p.append(parse_xml(
        f'<w:r {nsdecls("w")}><w:rPr><w:vanish/></w:rPr><w:t>HIDDEN_PLAIN</w:t></w:r>'
    ))
    doc.save(path)


class HiddenFieldTests(unittest.TestCase):
    def test_fields_omit_hidden_results_in_every_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "fields.docx"
            write_fixture(source)
            errors = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
                markdown = doc_to_md.convert_to_markdown(str(source))
            markdown = markdown.replace("\\_", "_")
            self.assertNotIn("HIDDEN_", markdown)
            self.assertIn("5 hidden-text run(s) omitted", errors.getvalue())
            for label in ("T0C0", "T0C1", "T1C0", "T1C1"):
                for kind in ("VISIBLE", "FALSE", "PLAIN"):
                    self.assertIn(f"{kind}_{label}", markdown)
