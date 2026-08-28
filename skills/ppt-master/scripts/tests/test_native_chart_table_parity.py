#!/usr/bin/env python3
"""Regression tests for native ChartEx and table projection behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.native_objects.chartex import (  # noqa: E402
    _chart_ex_series_xml,
    _chart_ex_xml,
)
from svg_to_pptx.native_objects import (  # noqa: E402
    native_object_projection_warnings,
)
from svg_to_pptx.native_objects.table import (  # noqa: E402
    _table_border_specs,
    _table_border_xml,
    _validate_table_payload,
)
from svg_to_pptx.pptx_package.cli import (  # noqa: E402
    _native_object_projection_findings,
)
from svg_quality.checker import SVGQualityChecker  # noqa: E402


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "native_projection"


def _fixture_root(filename: str) -> ET.Element:
    return ET.parse(FIXTURES_DIR / filename).getroot()


def _fixture_marker(filename: str) -> ET.Element:
    return next(
        elem
        for elem in _fixture_root(filename).iter()
        if elem.get("data-pptx-replace-with") in {"chart", "table"}
    )


class NativeTableBorderTests(unittest.TestCase):
    def test_legacy_uniform_border_is_cardinal_only(self) -> None:
        for cell, style in (
            ({}, {"border_color": "#DDE3E9", "border_width": 1}),
            ({"border_color": "#DDE3E9", "border_width": 1}, {}),
        ):
            with self.subTest(cell=cell, style=style):
                specs = _table_border_specs(cell, style)
                border_xml = _table_border_xml(cell, style, None)

                self.assertTrue(all(specs[side] is not None for side in (
                    "left", "right", "top", "bottom",
                )))
                self.assertIsNone(specs["diagonal_down"])
                self.assertIsNone(specs["diagonal_up"])
                self.assertNotIn("lnTlToBr", border_xml)
                self.assertNotIn("lnBlToTr", border_xml)

    def test_diagonal_borders_require_explicit_cell_overrides(self) -> None:
        cell = {
            "borders": {
                "diagonal_down": {
                    "style": "solid",
                    "color": "#C90A4F",
                    "width": 2,
                },
                "diagonal_up": {"style": "none"},
            },
        }

        specs = _table_border_specs(cell, {})
        border_xml = _table_border_xml(cell, {}, None)

        self.assertEqual(specs["diagonal_down"].style, "solid")
        self.assertEqual(specs["diagonal_up"].style, "none")
        self.assertIn("lnTlToBr", border_xml)
        self.assertIn("lnBlToTr", border_xml)


class NativeTableMergeTests(unittest.TestCase):
    @staticmethod
    def _payload(covered_cell: dict) -> dict:
        return {
            "schema": "ppt-master.semantic-table.v2",
            "defaults": {
                "cell": {
                    "color": "#1F2937",
                    "fill": "#FFFFFF",
                    "padding": {"left": 8, "right": 8},
                    "valign": "middle",
                },
            },
            "rows": [[
                {"text": "Owner", "col_span": 2},
                covered_cell,
            ]],
        }

    def test_merge_blankness_uses_authored_cells_before_defaults(self) -> None:
        for covered_cell in (
            {},
            {"text": ""},
            {"merge_continuation": True},
        ):
            with self.subTest(covered_cell=covered_cell):
                _payload, rows, col_count, merge_layout = (
                    _validate_table_payload(self._payload(covered_cell))
                )
                self.assertEqual((len(rows), col_count), (1, 2))
                self.assertIn((0, 1), merge_layout)

        for covered_cell in (
            {"text": "authored"},
            {"paragraphs": [{"text": ""}]},
            {"fill": "#F1F4F8"},
        ):
            with self.subTest(covered_cell=covered_cell):
                with self.assertRaisesRegex(RuntimeError, "must be blank"):
                    _validate_table_payload(self._payload(covered_cell))


class NativeChartExTests(unittest.TestCase):
    @staticmethod
    def _chart_data(chart_type: str) -> dict:
        if chart_type in {"sunburst", "treemap"}:
            return {
                "type": chart_type,
                "levels": [["A", "B"]],
                "values": [1, 2],
            }
        if chart_type == "histogram":
            return {"type": chart_type, "values": [1, 2]}
        return {
            "type": chart_type,
            "categories": ["A", "B"],
            "values": [1, 2],
            "subtotals": [],
        }

    def test_chart_without_title_omits_title_element_and_uses_payload_name(self) -> None:
        chart_data = self._chart_data("treemap")
        for payload in (
            {"name": "Market & <Space>"},
            {"name": "Market & <Space>", "title": ""},
            {"name": "Market & <Space>", "title": {"text": " "}},
        ):
            with self.subTest(payload=payload):
                chart_xml = _chart_ex_xml(
                    payload,
                    chart_data,
                    chart_rels_id="rId1",
                ).decode("utf-8")

                self.assertNotIn("<cx:title", chart_xml)
                self.assertIn("<cx:v>Market &amp; &lt;Space&gt;</cx:v>", chart_xml)
                self.assertNotIn("Series 1", chart_xml)

    def test_chart_title_contains_text_and_supplies_series_name(self) -> None:
        chart_data = self._chart_data("treemap")
        title_xml = (
            '<cx:title pos="t" align="ctr" overlay="0">'
            '<cx:tx><cx:txData><cx:v>Visible &amp; &lt;Title&gt;</cx:v>'
            '</cx:txData></cx:tx></cx:title>'
        )
        for title in ("Visible & <Title>", {"text": "Visible & <Title>"}):
            with self.subTest(title=title):
                chart_xml = _chart_ex_xml(
                    {"name": "internal-name", "title": title},
                    chart_data,
                    chart_rels_id="rId1",
                ).decode("utf-8")

                self.assertIn(title_xml, chart_xml)
                self.assertGreaterEqual(
                    chart_xml.count("<cx:v>Visible &amp; &lt;Title&gt;</cx:v>"),
                    2,
                )

    def test_chart_ex_series_families_do_not_hardcode_series_one(self) -> None:
        for chart_type in (
            "treemap",
            "sunburst",
            "histogram",
            "pareto",
            "waterfall",
            "funnel",
        ):
            with self.subTest(chart_type=chart_type):
                series_xml = _chart_ex_series_xml(
                    {"name": "Native & Series"},
                    self._chart_data(chart_type),
                )
                self.assertNotIn("Series 1", series_xml)
                self.assertIn("Native &amp; Series", series_xml)


class NativeProjectionCheckerTests(unittest.TestCase):
    EXPECTED_FINDINGS = {
        "06_1145_completion.svg": (
            "style.text_color",
            "data mark fill #C90A4F",
        ),
        "07_segment_mix.svg": (
            "legend label is not visible",
            "'其他业务'",
            "style.text_color",
        ),
        "10_competitiveness.svg": (
            "style.text_color",
            "plot area is visible",
            "5 countable radial gridlines",
        ),
        "11_market_space.svg": (
            "tile color sequence not projected",
            "visible text not projected",
            "'61.57%'",
        ),
        "15_signing_target.svg": (
            "style.text_color",
        ),
        "27_business_models.svg": (
            "fallback row heights are non-uniform",
            "header style not projected",
            "whole column 5 fill #F4F6F8",
            "first-column text style not projected",
            "border topology not projected",
        ),
        "30_risk_matrix.svg": (
            "fallback row heights are non-uniform",
            "header style not projected",
            "first-column text style not projected",
            "border topology not projected",
            "inset graphical cell with text",
            "Native-ready=no",
        ),
        "31_power_market.svg": (
            "fallback row heights are non-uniform",
            "header style not projected",
            "whole column 4 fill #F4F6F8",
            "first-column text style not projected",
            "border topology not projected",
        ),
    }

    def test_projection_helpers_report_each_diagnosed_page(self) -> None:
        for filename, expected in self.EXPECTED_FINDINGS.items():
            with self.subTest(filename=filename):
                warnings = native_object_projection_warnings(
                    _fixture_marker(filename)
                )
                joined = "\n".join(warnings)
                for text in expected:
                    self.assertIn(text, joined)

    def test_explicit_chart_text_axis_and_grid_colors_use_role_inference(self) -> None:
        marker = ET.fromstring("""
            <g data-pptx-replace-with="chart" data-pptx-bounds="0 0 400 240">
              <metadata type="application/json">
                {
                  "x": 0, "y": 0, "width": 400, "height": 240,
                  "type": "column",
                  "categories": ["A"],
                  "series": [{"name": "Series", "values": [1]}],
                  "style": {
                    "text_color": "#111111",
                    "axis_color": "#222222",
                    "grid_color": "#333333"
                  }
                }
              </metadata>
              <text x="20" y="220" fill="#AAAAAA">A</text>
              <line id="x-axis" x1="20" y1="200" x2="380" y2="200"
                    stroke="#BBBBBB" />
              <line id="gridline-1" x1="20" y1="100" x2="380" y2="100"
                    stroke="#CCCCCC" />
              <rect id="bar-0" x="100" y="80" width="80" height="120"
                    fill="#4472C4" />
            </g>
        """)

        joined = "\n".join(native_object_projection_warnings(marker))

        self.assertIn(
            "style.text_color #111111 differs from fallback dominant text_color #AAAAAA",
            joined,
        )
        self.assertIn(
            "style.axis_color #222222 differs from fallback dominant axis_color #BBBBBB",
            joined,
        )
        self.assertIn(
            "style.grid_color #333333 differs from fallback dominant grid_color #CCCCCC",
            joined,
        )

    def test_checker_surfaces_projection_findings_as_warnings(self) -> None:
        checker = SVGQualityChecker()
        for filename, expected in self.EXPECTED_FINDINGS.items():
            with self.subTest(filename=filename):
                result = {"errors": [], "warnings": []}
                checker._check_native_object_markers(
                    _fixture_root(filename),
                    result,
                )
                joined = "\n".join(result["warnings"])
                for text in expected:
                    self.assertIn(text, joined)
                self.assertFalse(result["errors"])

    def test_native_export_preflight_collects_the_same_findings(self) -> None:
        fixture_paths = [
            FIXTURES_DIR / filename
            for filename in self.EXPECTED_FINDINGS
        ]

        findings = _native_object_projection_findings(fixture_paths)
        findings_by_page: dict[str, str] = {}
        for filename, _marker_id, warning in findings:
            findings_by_page.setdefault(filename, "")
            findings_by_page[filename] += warning + "\n"

        self.assertEqual(set(findings_by_page), set(self.EXPECTED_FINDINGS))
        for filename, expected in self.EXPECTED_FINDINGS.items():
            with self.subTest(filename=filename):
                for text in expected:
                    self.assertIn(text, findings_by_page[filename])

    def test_table_parity_accepts_uniform_run_level_bold_and_color(self) -> None:
        marker = ET.fromstring("""
            <g data-pptx-replace-with="table" data-pptx-bounds="0 0 200 80">
              <metadata type="application/json">
                {
                  "schema": "ppt-master.semantic-table.v2",
                  "x": 0, "y": 0, "width": 200, "height": 80,
                  "header_rows": 1,
                  "column_widths": [100, 100],
                  "row_heights": [40, 40],
                  "columns": [
                    {
                      "align": "l",
                      "paragraphs": [{"runs": [{
                        "text": "Level", "bold": true, "color": "#1E1A16"
                      }]}]
                    },
                    {
                      "align": "l",
                      "paragraphs": [{"runs": [{
                        "text": "Meaning", "bold": true, "color": "#1E1A16"
                      }]}]
                    }
                  ],
                  "rows": [[
                    {"paragraphs": [{"runs": [{
                      "text": "Altar", "bold": true, "color": "#1E1A16"
                    }]}]},
                    {"text": "Cosmos", "color": "#2F2A25"}
                  ]]
                }
              </metadata>
              <line x1="0" y1="0" x2="200" y2="0" stroke="#999999"/>
              <line x1="0" y1="40" x2="200" y2="40" stroke="#999999"/>
              <line x1="0" y1="80" x2="200" y2="80" stroke="#999999"/>
              <g font-weight="bold" fill="#1E1A16">
                <text x="10" y="25">Level</text>
                <text x="110" y="25">Meaning</text>
                <text x="10" y="65">Altar</text>
              </g>
              <text x="110" y="65" fill="#2F2A25">Cosmos</text>
            </g>
        """)

        joined = "\n".join(native_object_projection_warnings(marker))

        self.assertNotIn("header style not projected", joined)
        self.assertNotIn("first-column text style not projected", joined)

    def test_table_parity_accepts_positioned_tspan_lines_for_paragraphs(self) -> None:
        marker = ET.fromstring("""
            <g data-pptx-replace-with="table" data-pptx-bounds="0 0 200 80">
              <metadata type="application/json">
                {
                  "schema": "ppt-master.semantic-table.v2",
                  "x": 0, "y": 0, "width": 200, "height": 80,
                  "header_rows": 0,
                  "rows": [[{"paragraphs": ["First line", "Second line"]}]]
                }
              </metadata>
              <text x="10" y="25">
                <tspan x="10" y="25">First line</tspan><tspan x="10" dy="24">Second line</tspan>
              </text>
            </g>
        """)

        joined = "\n".join(native_object_projection_warnings(marker))

        self.assertNotIn("fallback text is missing", joined)


class NativeTablePayloadRoundTripTest(unittest.TestCase):
    def test_marker_validation_keeps_original_table_payload(self):
        """The converter re-expands the payload; validation must not hand back an expanded copy."""
        import xml.etree.ElementTree as ET
        from svg_to_pptx.native_objects import _validate_native_object_marker_payload
        from svg_to_pptx.native_objects.table import _build_native_table  # noqa: F401
        from semantic_table import expand_semantic_table_payload
        fixture = FIXTURES_DIR / "27_business_models.svg"
        root = ET.parse(fixture).getroot()
        marker = next(
            el for el in root.iter()
            if el.get("data-pptx-replace-with") == "table"
        )
        kind, payload, rows = _validate_native_object_marker_payload(marker)
        self.assertEqual(kind, "table")
        self.assertEqual(payload.get("schema"), "ppt-master.semantic-table.v2")
        expand_semantic_table_payload(payload)  # must still expand cleanly


if __name__ == "__main__":
    unittest.main()
