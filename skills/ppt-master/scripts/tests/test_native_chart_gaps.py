#!/usr/bin/env python3
"""
PPT Master - Native Line Chart Gap Regression Tests

Exercise imported isolated values through the public round-trip checker and exporter.

Usage:
    python3 -m unittest tests.test_native_chart_gaps

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and local PPT Master modules.
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from pptx_to_svg.normalized_chart_svg import render_normalized_chart_svg
from svg_quality.checker import SVGQualityChecker
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main as export_main

SVG_NS = "http://www.w3.org/2000/svg"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"


class NativeChartGapTests(unittest.TestCase):
    def test_edited_line_values_keep_gaps_and_visible_markers(self) -> None:
        self._roundtrip_cases()

    def test_old_imported_preview_keeps_data_and_warns_without_reimport(self) -> None:
        self._roundtrip_cases(legacy_preview=True)

    def _roundtrip_cases(self, *, legacy_preview: bool = False) -> None:
        for values in ([1, None, 2, 3], [None, 1, None, 3], [1, 1.5, 2, 3]):
            with self.subTest(values=values), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source_svg = root / "slide.svg"
                payload = {
                    "type": "line", "x": 80, "y": 80, "width": 700, "height": 400,
                    "categories": ["A", "B", "C", "D"], "line_style": "lineMarker",
                    "series": [{"name": "Values", "values": values}],
                }
                source_svg.write_text(
                    f'<svg xmlns="{SVG_NS}" viewBox="0 0 960 720" font-family="Arial">'
                    '<g id="chart" data-pptx-replace-with="chart" data-pptx-native-authority="json">'
                    f'<metadata type="application/json">{json.dumps(payload)}</metadata></g></svg>',
                    encoding="utf-8",
                )
                source = root / "source.pptx"
                workspace = root / "workspace"
                output = root / "result.pptx"
                messages = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(messages):
                    self.assertTrue(create_pptx_with_native_svg(
                        [source_svg], source, resource_root=root, native_objects=True,
                        pptx_structure="flat", use_compat_mode=False, workers=1, transition=None, verbose=False,
                    ))
                    def preview(payload, styles):
                        rendered = render_normalized_chart_svg(payload, styles)
                        if legacy_preview:
                            # Seed the historical, invisible projection before
                            # import fingerprints are recorded; no exporter is mocked.
                            rendered += '<polyline points="100,100" fill="none" stroke="#123456"/>'
                        return rendered

                    with patch("pptx_to_svg.chart_to_svg.render_normalized_chart_svg", side_effect=preview):
                        convert_pptx_to_svg(
                            source, workspace, ConvertOptions(inheritance_mode="both", roundtrip=True),
                        )
                    path = workspace / "authoring-svg-flat/slide_01.svg"
                    tree = ET.parse(path)
                    metadata = next(node for node in tree.getroot().iter()
                                    if node.tag == f"{{{SVG_NS}}}metadata"
                                    and node.get("type") == "application/json")
                    edited = json.loads(metadata.text)
                    edited["series"][0]["values"][3] = 9
                    metadata.text = json.dumps(edited)
                    tree.write(path, encoding="utf-8")
                    results = SVGQualityChecker().check_roundtrip_workspace(str(workspace))
                    self.assertEqual(results[0]["errors"], [])
                    self.assertEqual(export_main([
                        str(workspace), "--roundtrip", "--native-charts-and-tables", "-o", str(output),
                    ]), 0)
                with ZipFile(output) as archive:
                    chart_path = next(name for name in archive.namelist()
                                      if name.startswith("ppt/charts/chart") and name.endswith(".xml"))
                    chart = ET.fromstring(archive.read(chart_path))
                cache = chart.find(f".//{{{CHART_NS}}}ser/{{{CHART_NS}}}val/{{{CHART_NS}}}numRef/"
                                   f"{{{CHART_NS}}}numCache")
                actual = [None] * int(cache.find(f"{{{CHART_NS}}}ptCount").get("val"))
                for point in cache.findall(f"{{{CHART_NS}}}pt"):
                    actual[int(point.get("idx"))] = float(point.find(f"{{{CHART_NS}}}v").text)
                self.assertEqual(actual, [*values[:3], 9])
                isolated = [node for node in tree.findall(f".//{{{SVG_NS}}}polyline")
                            if len(node.get("points").split()) == 1]
                self.assertEqual(len(isolated), int(legacy_preview))
                if legacy_preview:
                    self.assertIn("invisible isolated line preview segment", messages.getvalue())
                self.assertEqual(len(tree.findall(f".//{{{SVG_NS}}}circle")),
                                 sum(value is not None for value in values))
