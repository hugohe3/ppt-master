#!/usr/bin/env python3
"""PPT Master - Text source encoding regressions.

Usage:
    python3 -m unittest tests.test_source_text_encoding
Examples:
    Run from skills/ppt-master/scripts.
Dependencies:
    None (standard library only).
"""

import codecs
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
TEXT = "收入增长和利润说明\n正常对照\t2026"


class TextSourceEncodingTests(unittest.TestCase):
    def _run(self, script, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def _project(self, root):
        result = self._run(
            "project_manager.py", "init", "target_20261106", "--dir", root,
            "--quick-generate",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return root / "target_20261106"

    def test_supported_encodings_match_direct_conversion_and_quick_import(self) -> None:
        samples = {
            "utf8": TEXT.encode("utf-8"),
            "gb18030": TEXT.encode("gb18030"),
            "utf8_bom": codecs.BOM_UTF8 + TEXT.encode("utf-8"),
            "utf16_le": codecs.BOM_UTF16_LE + TEXT.encode("utf-16-le"),
            "utf16_be": codecs.BOM_UTF16_BE + TEXT.encode("utf-16-be"),
        }
        for name, raw in samples.items():
            with self.subTest(encoding=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "report.txt"
                source.write_bytes(raw)
                direct = root / "direct.md"
                result = self._run("source_to_md.py", source, "-o", direct)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(direct.read_text(encoding="utf-8"), TEXT)

                project = self._project(root)
                result = self._run("project_manager.py", "import-sources", project, source, "--copy")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual((project / "sources/report.md").read_text(encoding="utf-8"), TEXT)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual((project / "sources/report.txt").read_bytes(), raw)

    def test_invalid_or_binary_text_never_reports_success(self) -> None:
        samples = {
            "undecodable": (b"\xff", "Save the source as UTF-8 text and retry"),
            "broken_utf16": (codecs.BOM_UTF16_LE + b"a", "Save the source as UTF-8 text and retry"),
            "binary": (b"text\x00payload", "provide a text file"),
        }
        for name, (raw, repair) in samples.items():
            with self.subTest(input=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "report.txt"
                source.write_bytes(raw)
                direct = root / "direct.md"
                result = self._run("source_to_md.py", source, "-o", direct)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(repair, result.stdout + result.stderr)
                self.assertFalse(direct.exists())

                project = self._project(root)
                result = self._run("project_manager.py", "import-sources", project, source, "--copy")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(repair, result.stdout + result.stderr)
                self.assertNotIn("[OK] Imported sources", result.stdout)
                self.assertFalse((project / "sources/report.md").exists())
                self.assertEqual(source.read_bytes(), raw)
