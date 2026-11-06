#!/usr/bin/env python3
"""
PPT Master - Native Metadata Cardinality Regression Tests

Reject ambiguous native payload children consistently in the checker and exporter.

Usage:
    python3 -m unittest tests.test_native_metadata_cardinality

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and local PPT Master modules.
"""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_quality.checker import SVGQualityChecker
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main as export_main


SVG_NS = "http://www.w3.org/2000/svg"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
REPAIR = 'keep exactly one <metadata type="application/json"> child'


def _payload(value: float = 211.16) -> dict:
    return {
        "type": "column", "x": 80, "y": 80, "width": 700, "height": 400,
        "categories": ["A", "B"], "series": [{"name": "Values", "values": [value, 2]}],
    }


def _marker(payloads: tuple = (211.16,)) -> ET.Element:
    marker = ET.Element(f"{{{SVG_NS}}}g", {
        "id": "data-chart", "data-pptx-replace-with": "chart",
        "data-pptx-native-authority": "json",
    })
    for value in payloads:
        ET.SubElement(marker, f"{{{SVG_NS}}}metadata", {
            "type": "application/json",
        }).text = json.dumps(_payload(value))
    return marker


class NativeMetadataCardinalityTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def _write(self, marker: ET.Element) -> Path:
        svg = ET.Element(f"{{{SVG_NS}}}svg", {
            "viewBox": "0 0 960 720", "font-family": "Arial", "lang": "en-US",
        })
        svg.append(marker)
        path = self.root / "slide_01.svg"
        ET.ElementTree(svg).write(path, encoding="utf-8", xml_declaration=True)
        return path

    def _assert_rejected(self, marker: ET.Element) -> None:
        svg = self._write(marker)
        checked = SVGQualityChecker().check_file(str(svg))
        self.assertTrue(any(REPAIR in error for error in checked["errors"]), checked)
        with self.assertRaisesRegex(RuntimeError, "keep exactly one") as caught:
            convert_svg_to_slide_shapes(svg, resource_root=self.root, native_objects=True)
        self.assertIn(REPAIR, str(caught.exception))

    def _assert_value(self, marker: ET.Element) -> None:
        svg = self._write(marker)
        self.assertEqual(SVGQualityChecker().check_file(str(svg))["errors"], [])
        _slide, _media, _rels, _targets, parts, _types = convert_svg_to_slide_shapes(
            svg, resource_root=self.root, native_objects=True,
        )
        chart = ET.fromstring(next(data for name, data in parts.items()
                                  if name.startswith("ppt/charts/chart") and name.endswith(".xml")))
        value = chart.find(
            f".//{{{CHART_NS}}}ser/{{{CHART_NS}}}val/{{{CHART_NS}}}numRef/"
            f"{{{CHART_NS}}}numCache/{{{CHART_NS}}}pt/{{{CHART_NS}}}v"
        )
        self.assertEqual(float(value.text), 211.16)

    def test_conflicting_or_identical_payload_children_are_rejected(self) -> None:
        for values in ((1.25, 211.16), (211.16, 211.16), (1.25, 2, 211.16)):
            with self.subTest(values=values):
                self._assert_rejected(_marker(values))

    def test_legacy_metadata_child_cannot_hide_second_payload(self) -> None:
        marker = _marker((1.25, 211.16))
        marker[1].attrib.clear()
        marker[1].set("data-pptx-kind", "chart")
        self._assert_rejected(marker)

    def test_legacy_payload_attribute_cannot_bypass_child_count(self) -> None:
        for attribute in ("data-pptx-json", "data-pptx-data"):
            with self.subTest(attribute=attribute):
                marker = _marker((1.25, 211.16))
                marker.set(attribute, json.dumps(_payload()))
                self._assert_rejected(marker)

    def test_single_payload_retains_native_value(self) -> None:
        self._assert_value(_marker())

    def test_non_payload_metadata_does_not_count(self) -> None:
        marker = _marker()
        ET.SubElement(marker, f"{{{SVG_NS}}}metadata", {"type": "text/plain"}).text = "Provenance"
        self._assert_value(marker)

    def test_single_legacy_payload_stays_read_compatible(self) -> None:
        marker = _marker()
        marker[0].attrib.clear()
        marker[0].set("data-pptx-kind", "chart")
        self._assert_value(marker)
        for attribute in ("data-pptx-json", "data-pptx-data"):
            with self.subTest(attribute=attribute):
                marker = _marker(())
                marker.set(attribute, json.dumps(_payload()))
                self._assert_value(marker)

    def test_table_and_formula_share_payload_child_guard(self) -> None:
        payloads = {
            "table": {
                "schema": "ppt-master.semantic-table.v2", "rows": [["A"]],
                "x": 80, "y": 80, "width": 700, "height": 400,
            },
            "formula": {"latex": "x", "x": 80, "y": 80, "width": 100, "height": 40},
        }
        for kind, payload in payloads.items():
            with self.subTest(kind=kind):
                marker = _marker((1, 2))
                marker.set("data-pptx-replace-with", kind)
                if kind == "formula":
                    marker.attrib.pop("data-pptx-native-authority")
                for metadata in marker:
                    metadata.text = json.dumps(payload)
                self._assert_rejected(marker)

    def test_roundtrip_rejects_ambiguous_payload_without_traceback(self) -> None:
        source = self.root / "source.pptx"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertTrue(create_pptx_with_native_svg(
                [self._write(_marker((1.25,)))], source, resource_root=self.root,
                native_objects=True, pptx_structure="flat", use_compat_mode=False,
                workers=1, transition=None, verbose=False,
            ))
            workspace = self.root / "workspace"
            convert_pptx_to_svg(source, workspace, options=ConvertOptions(
                inheritance_mode="both", roundtrip=True,
            ))
        svg = workspace / "authoring-svg-flat/slide_01.svg"
        tree = ET.parse(svg)
        marker = next(n for n in tree.getroot().iter() if n.get("data-pptx-replace-with") == "chart")
        second = copy.deepcopy(marker.find(f'{{{SVG_NS}}}metadata[@type="application/json"]'))
        payload = json.loads(second.text)
        payload["series"][0]["values"][0] = 211.16
        second.text = json.dumps(payload)
        marker.append(second)
        tree.write(svg, encoding="utf-8", xml_declaration=True)
        target = self.root / "output.pptx"
        prior_output = b"existing output must survive rejected input"
        target.write_bytes(prior_output)
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = export_main([
                str(workspace), "--roundtrip", "--native-charts-and-tables", "-o", str(target),
            ])
        self.assertEqual(code, 1)
        self.assertIn(REPAIR, stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(target.read_bytes(), prior_output)
