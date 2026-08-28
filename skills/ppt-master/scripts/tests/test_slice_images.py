#!/usr/bin/env python3
"""Focused tests for illustration-sheet alpha-key diagnostics."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "slice_images.py"


class SliceImagesDiagnosticsTests(unittest.TestCase):
    def test_strict_alpha_reports_measured_sheet_border_and_exact_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            image = Image.new("RGB", (100, 80), (87, 178, 101))
            draw = ImageDraw.Draw(image)
            draw.rectangle((30, 22, 70, 58), fill=(170, 40, 55))
            draw.point((0, 0), fill=(84, 176, 100))
            draw.point((99, 79), fill=(88, 180, 102))
            image.save(sheet_path)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(sheet_path),
                    "--grid", "1x1",
                    "--names", "element",
                    "--trim",
                    "--alpha",
                    "--strict-alpha",
                    "--bg", "#00FF00",
                    "--tolerance", "12",
                    "--output", str(output_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("key background #00FF00", result.stderr)
            self.assertIn("dominant #57B265", result.stderr)
            self.assertIn("max channel spread 3", result.stderr)
            self.assertIn("--bg #57B265 --tolerance 12", result.stderr)
            self.assertFalse((output_dir / "element.png").exists())


if __name__ == "__main__":
    unittest.main()
