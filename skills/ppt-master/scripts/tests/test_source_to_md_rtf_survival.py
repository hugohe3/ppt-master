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


@unittest.skipUnless(shutil.which("pandoc"), "Pandoc fallback requires the optional system binary")
class RtfSurvivalTests(unittest.TestCase):
    def test_rtf_flat_hyperlink_fields_and_hidden_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "document.rtf"
            source.write_text(
                r'{\rtf1\ansi BEFORE {\v HIDDENMARK} '
                r'{\field{\*\fldinst HYPERLINK "https://example.invalid/LINKURL"}'
                r'{\fldrslt LINKTEXT}} AFTER}', encoding="ascii",
            )
            original = source.read_bytes()
            diagnostics = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(diagnostics):
                text = doc_to_md.convert_to_markdown(str(source), str(root / "document.md"))
            for marker in ("BEFORE", "LINKURL", "LINKTEXT", "AFTER"):
                self.assertIn(marker, text)
            self.assertNotIn("HIDDENMARK", text)
            self.assertIn("author-hidden", diagnostics.getvalue())
            self.assertEqual(source.read_bytes(), original)

    def test_rtf_nested_field_results_and_literal_backslashes_stay_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "nested.rtf"
            source.write_text(
                r'{\rtf1\ansi \\v VISIBLEMARK '
                r'{\field{\*\fldinst{HYPERLINK "https://example.invalid/NESTEDURL"}}'
                r'{\fldrslt{NESTEDTEXT}}}}', encoding="ascii",
            )
            diagnostics = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(diagnostics):
                text = doc_to_md.convert_to_markdown(str(source), str(root / "nested.md"))
            self.assertIn("VISIBLEMARK", text)
            self.assertIn("NESTEDTEXT", text)
            self.assertIn("NESTEDURL", text)
            self.assertNotIn("author-hidden", diagnostics.getvalue())
