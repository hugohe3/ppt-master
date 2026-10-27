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
class OdtSurvivalTests(unittest.TestCase):
    def test_odt_table_header_textbox_and_conditional_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "document.odt"
            subprocess.run(
                ["pandoc", "-f", "markdown", "-o", str(source)],
                input="| HEADERMARK |\n|---|\n| BODYMARK |\n", text=True,
                capture_output=True, check=True,
            )
            with zipfile.ZipFile(source) as archive:
                parts = {name: archive.read(name) for name in archive.namelist()}
            parts["content.xml"] = parts["content.xml"].replace(b"</office:text>", (
                '<text:p>LEFTMARK <draw:frame text:anchor-type="as-char"><draw:text-box><text:p>BOXMARK '
                '<text:a xlink:href="https://example.invalid/BOXURL">BOXLINK</text:a>'
                '</text:p><text:p>BOXSECOND</text:p></draw:text-box></draw:frame> RIGHTMARK</text:p>'
                '<text:p><text:hidden-text text:is-hidden="false">CONDITIONVISIBLE</text:hidden-text>'
                '<text:hidden-text text:is-hidden="true">CONDITIONHIDDEN</text:hidden-text>'
                'TAILMARK</text:p></office:text>'
            ).encode())
            with zipfile.ZipFile(source, "w") as archive:
                for name, data in parts.items():
                    archive.writestr(name, data)
            original = source.read_bytes()
            diagnostics = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(diagnostics):
                text = doc_to_md.convert_to_markdown(str(source), str(root / "document.md"))
            for marker in (
                "HEADERMARK", "BODYMARK", "BOXMARK", "BOXSECOND", "BOXLINK", "BOXURL",
                "CONDITIONVISIBLE", "TAILMARK",
            ):
                self.assertIn(marker, text)
            self.assertNotIn("CONDITIONHIDDEN", text)
            self.assertLess(text.index("LEFTMARK"), text.index("BOXMARK"))
            self.assertLess(text.index("BOXSECOND"), text.index("RIGHTMARK"))
            self.assertIn("1 author-hidden field(s) omitted", diagnostics.getvalue())
            self.assertEqual(source.read_bytes(), original)
