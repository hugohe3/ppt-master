#!/usr/bin/env python3
"""End-to-end regression tests for synchronized spec and SVG updates."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from stamp_native_fallbacks import stamp_file  # noqa: E402


UPDATE_SPEC = SCRIPTS_DIR / "update_spec.py"
SVG_CHECKER = SCRIPTS_DIR / "svg_quality_checker.py"
FALLBACK_HASH_RE = re.compile(r'data-pptx-fallback-sha256="([0-9a-f]{64})"')


class UpdateSpecNativeFallbackTests(unittest.TestCase):
    def _copy_minimal_project(self, root: Path) -> Path:
        fixture = root / "fixture"
        svg_dir = fixture / "svg_output"
        svg_dir.mkdir(parents=True)
        (fixture / "spec_lock.md").write_text(
            """<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- background: #FFFFFF
- accent: #B23A2A
- body_text: #1F2937

## typography
- font_family: Microsoft YaHei
- body: 24
- title: 36

## pptx_structure
- mode: flat
""",
            encoding="utf-8",
        )
        svg_path = svg_dir / "01_native_table.svg"
        svg_path.write_text(
            """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"
  data-pptx-page-role="content" font-family="Microsoft YaHei">
  <rect id="background" data-pptx-role="background" x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
  <g id="accent-table" data-pptx-replace-with="table" data-pptx-bounds="100 100 300 80">
    <metadata type="application/json">{
      "schema": "ppt-master.semantic-table.v2",
      "name": "accent-table",
      "x": 100, "y": 100, "width": 300, "height": 80,
      "header_rows": 0,
      "column_widths": [300],
      "row_heights": [80],
      "style": {
        "font_family": "Microsoft YaHei",
        "font_size": 24,
        "band_row": false,
        "border_color": "#B23A2A",
        "border_width": 1
      },
      "rows": [[{"text": "Accent", "color": "#B23A2A"}]]
    }</metadata>
    <rect x="100" y="100" width="300" height="80" fill="#FFFFFF" stroke="#B23A2A"/>
    <text x="120" y="150" font-size="24" fill="#B23A2A">Accent</text>
  </g>
</svg>
""",
            encoding="utf-8",
        )
        svg_first, json_first, changed = stamp_file(svg_path, write=True)
        self.assertEqual((svg_first, json_first, changed), (1, 0, True))

        project = root / "project"
        shutil.copytree(fixture, project)
        return project

    def test_update_restamps_touched_native_fallback_and_checker_passes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self._copy_minimal_project(Path(temp_dir))
            lock_path = project / "spec_lock.md"
            svg_path = project / "svg_output" / "01_native_table.svg"
            original_lock = lock_path.read_bytes()
            original_svg = svg_path.read_bytes()
            original_hash = FALLBACK_HASH_RE.search(
                original_svg.decode("utf-8")
            )
            self.assertIsNotNone(original_hash)

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(UPDATE_SPEC),
                    str(project),
                    "colors.accent=#8C2F1F",
                    "--dry-run",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn(
                "[dry-run] native fallbacks: 1 marker(s) would be re-stamped",
                dry_run.stdout,
            )
            self.assertEqual(lock_path.read_bytes(), original_lock)
            self.assertEqual(svg_path.read_bytes(), original_svg)

            update = subprocess.run(
                [
                    sys.executable,
                    str(UPDATE_SPEC),
                    str(project),
                    "colors.accent=#8C2F1F",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(update.returncode, 0, update.stderr)
            self.assertIn(
                "native fallbacks: 1 marker(s) re-stamped",
                update.stdout,
            )
            updated_svg = svg_path.read_text(encoding="utf-8")
            self.assertNotIn("#B23A2A", updated_svg)
            self.assertIn("#8C2F1F", updated_svg)
            updated_hash = FALLBACK_HASH_RE.search(updated_svg)
            self.assertIsNotNone(updated_hash)
            self.assertNotEqual(original_hash.group(1), updated_hash.group(1))

            checker = subprocess.run(
                [
                    sys.executable,
                    str(SVG_CHECKER),
                    str(svg_path),
                    "--canonical-authoring",
                    "--stage",
                    "final",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                checker.returncode,
                0,
                checker.stdout + checker.stderr,
            )


if __name__ == "__main__":
    unittest.main()
