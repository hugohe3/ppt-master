#!/usr/bin/env python3
"""PPT Master - Native Merged Table Regression Tests

Exercise covered-cell formatting and authority-aware errors through the public
SVG converter and export CLI using small inline fixtures.

Usage:
    python3 -m unittest tests.test_native_table_merges

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local SVG-to-PPTX converter.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from xml.etree import ElementTree as ET

from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from svg_to_pptx.pptx_package.cli import main


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "s": "http://www.w3.org/2000/svg",
}


class NativeTableMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "input"
        self.source.mkdir()
        self.svg_path = self.source / "slide_01.svg"

    @staticmethod
    def _payload(covered: object, **extra: object) -> dict:
        return {
            "schema": "ppt-master.semantic-table.v2",
            "x": 20, "y": 20, "width": 400, "height": 160,
            "header_rows": 0,
            "rows": [
                [{"text": "Owner", "row_span": 2, "col_span": 2}, covered],
                [covered, covered],
            ],
            **extra,
        }

    def _write_svg(
        self, payload: dict, *, imported: bool = False, json_first: bool = True,
    ) -> ET.Element:
        root = ET.Element(f'{{{NS["s"]}}}svg', {
            "viewBox": "0 0 1280 720", "lang": "en-US",
        })
        marker = ET.SubElement(root, f'{{{NS["s"]}}}g', {
            "id": "shape-60", "data-pptx-replace-with": "table",
        })
        if json_first:
            marker.set("data-pptx-native-authority", "json")
        if imported:
            marker.set("data-pptx-import-source", "pptx")
        ET.SubElement(marker, f'{{{NS["s"]}}}metadata', {
            "type": "application/json",
        }).text = json.dumps(payload)
        self.svg_path.write_bytes(ET.tostring(root))
        return root

    def _export(self, payload: dict, *, imported: bool = False) -> list[list[ET.Element]]:
        self._write_svg(payload, imported=imported)
        xml, *_rest = convert_svg_to_slide_shapes(
            self.svg_path, resource_root=self.root, native_objects=True,
        )
        table = ET.fromstring(xml).find(".//a:tbl", NS)
        self.assertIsNotNone(table)
        return [row.findall("a:tc", NS) for row in table.findall("a:tr", NS)]

    def _run_cli(self) -> tuple[int, str]:
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            result = main([
                str(self.root), "--source", "input", "--native-charts-and-tables",
                "-o", str(self.root / "output.pptx"),
            ])
        return result, stderr.getvalue()

    def test_covered_formatting_reaches_tcpr_with_or_without_continuation_marker(self) -> None:
        formatting = {
            "fill": "#35778F", "fill_opacity": 0.65,
            "borders": {
                "left": {"style": "solid", "color": "#FFFFFF", "width": 3},
                "right": {"style": "none"},
                "diagonal_down": {"style": "solid", "color": "#112233", "width": 2},
            },
            "padding": {"left": 4, "right": 5, "top": 6, "bottom": 7},
            "valign": "bottom", "anchor_center": True, "horizontal_overflow": "clip",
            "color": "#112233", "font_size": 16, "bold": True, "align": "r", "lang": "en-US",
        }
        for imported in (False, True):
            for named_style in (False, True):
                for continuation in (False, True):
                    with self.subTest(imported=imported, named_style=named_style, continuation=continuation):
                        covered = {"text": ""}
                        if continuation:
                            covered["merge_continuation"] = True
                        if named_style:
                            covered["cell_style"] = "covered"
                        else:
                            covered.update(formatting)
                        payload = self._payload(
                            covered,
                            defaults={"cell": {"fill": "#000000", "padding": {"left": 1}}},
                            cell_styles={"covered": formatting} if named_style else {},
                        )
                        rows = self._export(payload, imported=imported)
                        self.assertEqual(rows[0][0].attrib, {"rowSpan": "2", "gridSpan": "2"})
                        for row, col, attrs in (
                            (0, 1, {"rowSpan": "2", "hMerge": "1"}),
                            (1, 0, {"gridSpan": "2", "vMerge": "1"}),
                            (1, 1, {"hMerge": "1", "vMerge": "1"}),
                        ):
                            cell = rows[row][col]
                            self.assertEqual(cell.attrib, attrs)
                            self.assertFalse(cell.findall("a:txBody//a:t", NS))
                            props = cell.find("a:tcPr", NS)
                            self.assertEqual(props.attrib, {
                                "anchor": "b", "anchorCtr": "1", "horzOverflow": "clip",
                                "marL": "38100", "marR": "47625", "marT": "57150", "marB": "66675",
                            })
                            fill = props.find("a:solidFill/a:srgbClr", NS)
                            self.assertEqual(fill.get("val"), "35778F")
                            self.assertEqual(fill.find("a:alpha", NS).get("val"), "65000")
                            self.assertEqual(props.find("a:lnL", NS).get("w"), "28575")
                            self.assertEqual(props.find("a:lnL/a:solidFill/a:srgbClr", NS).get("val"), "FFFFFF")
                            self.assertIsNotNone(props.find("a:lnR/a:noFill", NS))
                            self.assertEqual(props.find("a:lnTlToBr", NS).get("w"), "19050")

    def test_blank_forms_keep_defaults_and_authored_merge_topology(self) -> None:
        for covered in (None, "", {}, {"text": None}, {"text": ""}, {"merge_continuation": True}):
            with self.subTest(covered=covered):
                rows = self._export(self._payload(covered, defaults={"cell": {"fill": "#ABCDEF"}}))
                self.assertEqual([node.text for node in rows[0][0].findall(".//a:t", NS)], ["Owner"])
                for cell in (rows[0][1], rows[1][0], rows[1][1]):
                    self.assertEqual(cell.find("a:tcPr/a:solidFill/a:srgbClr", NS).get("val"), "ABCDEF")
                    self.assertFalse(cell.findall(".//a:t", NS))

    def test_covered_text_and_paragraphs_still_fail(self) -> None:
        for covered in (
            {"text": "hidden", "fill": "#35778F", "merge_continuation": True},
            {"text": " "}, {"text": 0}, {"text": []},
            {"paragraphs": [{"text": "hidden"}]},
            {"paragraphs": [{"runs": [{"text": "hidden"}]}]},
            {"paragraphs": [""]}, {"merge_continuation": False},
        ):
            with self.subTest(covered=covered):
                with self.assertRaisesRegex(RuntimeError, "merge-covered cell R1C2 must be blank"):
                    self._export(self._payload(covered))

    def test_covered_formatting_keeps_schema_and_merge_validation(self) -> None:
        for covered, message in (
            ({"unknown": "value"}, "unsupported field"),
            ({"cell_style": "missing"}, "unknown cell_style"),
            ({"fill_opacity": 2}, "fill_opacity"),
            ({"borders": {"left": {"style": "solid", "color": "#FFFFFF", "width": 0}}}, "width"),
            ({"col_span": 1}, "overlaps"),
        ):
            with self.subTest(covered=covered):
                with self.assertRaisesRegex(RuntimeError, message):
                    self._export(self._payload(covered))

    def test_json_first_validation_errors_do_not_recommend_svg_fallback(self) -> None:
        for imported in (False, True):
            with self.subTest(imported=imported):
                self._write_svg(self._payload({"text": "hidden"}), imported=imported)
                result, stderr = self._run_cli()
                self.assertEqual(result, 1, stderr)
                self.assertIn("JSON-first native payload validation failed", stderr)
                self.assertIn("slide_01.svg: shape-60:", stderr)
                self.assertIn("merge-covered cell R1C2 must be blank", stderr)
                self.assertIn("Correct the reported JSON payload", stderr)
                for incorrect in ("SVG-first", "projection validation", "remove the active", "Native-ready=no"):
                    self.assertNotIn(incorrect, stderr)

    def test_svg_first_validation_keeps_projection_guidance(self) -> None:
        self._write_svg(self._payload({"text": "hidden"}), json_first=False)
        result, stderr = self._run_cli()
        self.assertEqual(result, 1, stderr)
        self.assertIn("SVG-first fallback", stderr)
        self.assertIn("projection validation failed", stderr)
        self.assertIn("Native-ready=no", stderr)
        self.assertNotIn("JSON-first native payload validation failed", stderr)
