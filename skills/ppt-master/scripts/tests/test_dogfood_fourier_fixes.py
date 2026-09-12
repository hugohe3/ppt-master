"""Regressions from the Fourier-transform formula deck dogfood (2026-09-12)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import compact_svg_styles  # noqa: E402
import text_measure  # noqa: E402
from svg_to_pptx.drawingml.utils import unsafe_exported_font_faces  # noqa: E402
from svg_to_pptx.native_objects.chart_data import _chart_data  # noqa: E402


def _line_payload(**series_extra: object) -> dict[str, object]:
    return {
        "type": "line",
        "categories": ["a", "b", "c"],
        "series": [{"name": "s", "values": [1, 2, 3], **series_extra}],
    }


class SeriesLineStyleTests(unittest.TestCase):
    def test_series_level_line_style_is_rejected_with_pointer(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            _chart_data(_line_payload(line_style="lineMarker"))
        self.assertIn("series[].line_style", str(ctx.exception))
        self.assertIn("chart root", str(ctx.exception))

    def test_root_line_style_still_accepted(self) -> None:
        payload = _line_payload()
        payload["line_style"] = "lineMarker"
        self.assertEqual(_chart_data(payload)["line_style"], "lineMarker")

    def test_typed_combo_series_keep_line_style(self) -> None:
        payload = {
            "type": "combo",
            "categories": ["a", "b"],
            "series": [
                {"type": "column", "name": "c", "values": [1, 2]},
                {"type": "line", "name": "l", "values": [2, 3], "line_style": "lineMarker"},
            ],
        }
        plots = _chart_data(payload)["plots"]
        self.assertEqual(plots[1]["line_style"], "lineMarker")


class CambriaMathTests(unittest.TestCase):
    def test_formula_face_is_not_flagged(self) -> None:
        self.assertEqual(unsafe_exported_font_faces("Cambria Math"), {})


class OutlineSplitTests(unittest.TestCase):
    def test_ascii_semicolon_before_cjk_splits_blocks(self) -> None:
        parts = text_measure._split_joined_blocks("A · B;C · 含 4 个导频;子载波间隔 · D")
        self.assertEqual(parts, ["A", "B;C", "含 4 个导频", "子载波间隔", "D"])


class CompactCdataTests(unittest.TestCase):
    SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g id="f" data-pptx-replace-with="formula">'
        '<metadata type="application/json"><![CDATA[{"latex": "a < b & c"}]]></metadata>'
        '<text x="1" y="2" style="fill:#000000;font-size:12px">a</text>'
        '<text x="1" y="20" style="fill:#000000;font-size:12px">b</text>'
        "</g></svg>\n"
    )

    def test_json_metadata_keeps_cdata_after_compaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.svg"
            path.write_text(self.SVG, encoding="utf-8")
            payload, stats = compact_svg_styles._compact_svg_bytes(path)
        self.assertGreater(stats.changed_declarations, 0)
        self.assertIn(b'<![CDATA[{"latex": "a < b & c"}]]>', payload)
        self.assertNotIn(b"&lt;", payload)


if __name__ == "__main__":
    unittest.main()
