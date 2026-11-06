#!/usr/bin/env python3
"""Regression tests for source-relative Pandoc includes and diagnostics."""

import base64
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote


SCRIPTS = Path(__file__).resolve().parents[1]
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII="
)


class PandocIncludePathTests(unittest.TestCase):
    def convert(self, source: Path, output: Path) -> tuple[subprocess.CompletedProcess, dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "source_to_md.py"), str(source),
             "-o", str(output), "--json"],
            cwd=SCRIPTS, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result, json.loads(result.stdout)

    def test_includes_use_source_directory_with_separate_or_same_output(self) -> None:
        for location in ("separate", "same", "decoy"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source_dir = root / "source files"
                source_dir.mkdir()
                output_dir = source_dir if location == "same" else root / "output files"
                output_dir.mkdir(exist_ok=True)
                source = source_dir / "main.tex"
                source.write_text(
                    "\\begin{document}MAINMARKER\n\\input{body}\n\\end{document}",
                    encoding="utf-8",
                )
                child = source_dir / "body.tex"
                child.write_text("CORRECTBODY", encoding="utf-8")
                canaries = [source, child]
                if location == "decoy":
                    decoy = output_dir / "body.tex"
                    decoy.write_text("WRONGDECOY", encoding="utf-8")
                    canaries.append(decoy)
                original = {path: path.read_bytes() for path in canaries}
                output = output_dir / "result.md"
                _, payload = self.convert(source, output)
                text = output.read_text(encoding="utf-8")
                self.assertIn("MAINMARKER", text)
                self.assertIn("CORRECTBODY", text)
                self.assertNotIn("WRONGDECOY", text)
                self.assertNotIn("warnings", payload)
                self.assertEqual({path: path.read_bytes() for path in canaries}, original)

    def test_missing_include_warning_reaches_stderr_profile_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "main.tex"
            source.write_text(
                "\\begin{document}KEEPMARKER\\input{missing}\\end{document}", encoding="utf-8",
            )
            output = root / "output" / "result.md"
            result, payload = self.convert(source, output)
            profile = json.loads(Path(payload["conversion_profile"]).read_text(encoding="utf-8"))
            self.assertIn("KEEPMARKER", output.read_text(encoding="utf-8"))
            self.assertEqual(payload["warnings"], profile["warnings"])
            self.assertTrue(payload["warnings"])
            self.assertIn("Could not load include file missing.tex", "\n".join(payload["warnings"]))
            self.assertIn(payload["warnings"][0], result.stderr)

    def test_odt_media_stays_beside_output_with_spaces_in_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "source files"
            source_dir.mkdir()
            image = source_dir / "plot.png"
            image.write_bytes(PNG)
            markdown = source_dir / "input.md"
            markdown.write_text("ODTBODY\n\n![plot](plot.png)\n", encoding="utf-8")
            source = source_dir / "input.odt"
            producer = subprocess.run(
                ["pandoc", "-f", "markdown", str(markdown), "-o", str(source)],
                cwd=source_dir, capture_output=True, text=True,
            )
            self.assertEqual(producer.returncode, 0, producer.stderr)
            original = source.read_bytes()
            output = root / "output files" / "result.md"
            self.convert(source, output)
            text = output.read_text(encoding="utf-8")
            refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
            self.assertEqual(len(refs), 1, text)
            self.assertTrue(refs[0].startswith("result_files/"), refs[0])
            asset = output.parent / unquote(refs[0])
            self.assertEqual(asset.read_bytes(), PNG)
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse((source_dir / "result_files").exists())
