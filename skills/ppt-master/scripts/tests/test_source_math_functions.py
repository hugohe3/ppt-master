#!/usr/bin/env python3
"""Preserve LaTeX command boundaries in native Office function expressions.

Usage: python3 -m unittest tests.test_source_math_functions
Examples: Run the module from the scripts directory.
Dependencies: python-docx, mammoth, python-pptx
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from docx import Document
from docx.oxml import parse_xml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source_to_md"))
import doc_to_md  # noqa: E402
import ppt_to_md  # noqa: E402
from _omml_latex import _omml_to_latex  # noqa: E402

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
CASES = (("sin", "x", r"\sin x"), ("cos", "y", r"\cos y"),
         ("sin", "(x)", r"\sin{(x)}"), ("sin", "2", r"\sin2"))


def function_xml(name: str, argument: str) -> str:
    """Build a native function, rather than a plain-text math run."""
    return (f'<m:oMath xmlns:m="{MATH_NS}"><m:func>'
            f'<m:fName><m:r><m:t>{name}</m:t></m:r></m:fName>'
            f'<m:e><m:r><m:t>{argument}</m:t></m:r></m:e>'
            '</m:func></m:oMath>')


def write_fixture(path: Path) -> None:
    """Build a DOCX containing failing functions and ordinary controls."""
    document = Document()
    for name, argument, _ in CASES:
        document.add_paragraph()._p.append(parse_xml(function_xml(name, argument)))
    document.save(path)


class SourceMathFunctionTests(unittest.TestCase):
    def test_shared_math_converter_separates_single_letter_arguments(self) -> None:
        for name, argument, expected in CASES:
            with self.subTest(name=name, argument=argument):
                equation = ET.fromstring(function_xml(name, argument))
                self.assertEqual(_omml_to_latex(equation), expected)
                wrapper = ET.fromstring(
                    '<a14:m xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main">'
                    + function_xml(name, argument) + '</a14:m>'
                )
                self.assertEqual(ppt_to_md._office_math_markdown(wrapper), f"${expected}$")

    def test_docx_native_functions_survive_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "functions.docx"
            write_fixture(source)
            with contextlib.redirect_stdout(io.StringIO()):
                markdown = doc_to_md.convert_to_markdown(str(source))
            for _, _, expected in CASES:
                self.assertIn(f"${expected}$", markdown)
            self.assertNotIn(r"\sinx", markdown)
