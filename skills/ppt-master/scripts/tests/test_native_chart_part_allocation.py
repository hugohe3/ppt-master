#!/usr/bin/env python3
"""
PPT Master - Native Chart Part Allocation Regression Tests

Exercise source preservation, chart-family allocation and collision errors
through the public SVG converter, with fixtures constructed in this module.

Usage:
    python3 -m unittest tests.test_native_chart_part_allocation

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local SVG-to-PPTX converter.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import posixpath
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pptx_ooxml.package import PackagePartRegistry
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes


NS = {
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
}
SVG_NS = "http://www.w3.org/2000/svg"


def _chart(name: str, *, values: tuple = (3, 2), source: dict | None = None,
           chartex: bool = False) -> str:
    elem = ET.Element(f"{{{SVG_NS}}}g", {
        "id": name,
        "data-pptx-replace-with": "chart",
        "data-pptx-native-authority": "json",
    })
    payload = {
        "type": "column", "name": name,
        "x": 100, "y": 100, "width": 600, "height": 400,
        "categories": ["A", "B"], "series": [{"name": "Values", "values": values}],
    }
    if source is not None:
        payload["source_package"] = source
    if chartex:
        payload.update(type="treemap", levels=[["A", "B"]], values=values)
    ET.SubElement(elem, f"{{{SVG_NS}}}metadata", {"type": "application/json"}).text = json.dumps(payload)
    return ET.tostring(elem, encoding="unicode")


def _blob(data: bytes) -> dict:
    return {"encoding": "base64", "payload": base64.b64encode(data).decode("ascii"),
            "sha256": hashlib.sha256(data).hexdigest()}


def _export(body: str, **kwargs: object) -> tuple:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        svg = root / "chart.svg"
        svg.write_text(f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720">{body}</svg>', encoding="utf-8")
        xml, _media, rels, _targets, parts, types = convert_svg_to_slide_shapes(
            svg, resource_root=root, native_objects=True, **kwargs,
        )
        return ET.fromstring(xml), rels, parts, types


def _source(chart_index: int = 102, workbook_index: int = 102,
            *, values: tuple = (11, 12), extras: dict | None = None) -> dict:
    slide, _rels, parts, types = _export(_chart("source", values=values))
    renamed = {}
    renamed_types = {}
    for name, data in parts.items():
        new_name = name.replace("chart101.xml", f"chart{chart_index}.xml").replace(
            "Sheet101.xlsx", f"Sheet{workbook_index}.xlsx",
        )
        if name.endswith(".rels"):
            data = data.replace(b"Sheet101.xlsx", f"Sheet{workbook_index}.xlsx".encode())
        renamed[new_name] = data
        if name in types:
            renamed_types[new_name] = types[name]
    renamed.update(extras or {})
    return {
        "chart_part": f"ppt/charts/chart{chart_index}.xml",
        "frame": _blob(ET.tostring(slide.find(".//p:graphicFrame", NS))),
        "parts": [{"name": name, **_blob(data), "content_type": renamed_types.get(name)}
                  for name, data in renamed.items()],
    }


def _chart_rows(slide: ET.Element, rels: list, parts: dict) -> list[dict]:
    rows = []
    for frame in slide.findall(".//p:graphicFrame", NS):
        reference = next(iter(frame.findall(".//c:chart", NS) + frame.findall(".//cx:chart", NS)))
        relation = next(rel for rel in rels if rel["id"] == reference.get(f"{{{NS['r']}}}id"))
        chart_part = posixpath.normpath(posixpath.join("ppt/slides", relation["target"]))
        rels_part = posixpath.join("ppt/charts/_rels", posixpath.basename(chart_part) + ".rels")
        chart_rels = ET.fromstring(parts[rels_part])
        workbook_rel = next(rel for rel in chart_rels if rel.get("Type").endswith("/package"))
        workbook_part = posixpath.normpath(posixpath.join("ppt/charts", workbook_rel.get("Target")))
        chart = ET.fromstring(parts[chart_part])
        values = [node.text for node in chart.findall(".//c:ser/c:val/c:numRef/c:numCache/c:pt/c:v", NS)]
        if reference.tag == f"{{{NS['cx']}}}chart":
            values = [node.text for node in chart.findall(".//cx:numDim/cx:lvl/cx:pt", NS)]
        with ZipFile(io.BytesIO(parts[workbook_part])) as workbook:
            sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
            workbook_values = [sheet.find(f".//x:c[@r='B{row}']/x:v", NS).text for row in (2, 3)]
        rows.append({"chart": chart_part, "rels": rels_part, "workbook": workbook_part,
                     "values": values, "workbook_values": workbook_values})
    return rows


class NativeChartPartAllocationTests(unittest.TestCase):
    def assert_source_unchanged(self, source: dict, parts: dict, types: dict) -> None:
        for item in source["parts"]:
            self.assertEqual(parts[item["name"]], base64.b64decode(item["payload"]))
            if item.get("content_type"):
                self.assertEqual(types[item["name"]], item["content_type"])

    def test_preserved_and_rebuilt_charts_keep_independent_data_in_both_orders(self) -> None:
        for source_index in (101, 102):
            for source_first in (True, False):
                with self.subTest(source_index=source_index, source_first=source_first):
                    source = _source(source_index, source_index)
                    markers = [_chart("preserved", source=source), _chart("rebuilt")]
                    if not source_first:
                        markers.reverse()
                    slide, rels, parts, types = _export("".join(markers))
                    rows = _chart_rows(slide, rels, parts)
                    for key in ("chart", "rels", "workbook"):
                        self.assertEqual(len({row[key] for row in rows}), 2)
                    expected = [["11", "12"], ["3", "2"]]
                    if not source_first:
                        expected.reverse()
                    self.assertEqual([row["values"] for row in rows], expected)
                    self.assertEqual([row["workbook_values"] for row in rows], expected)
                    self.assert_source_unchanged(source, parts, types)

    def test_workbook_collision_alone_advances_the_whole_family(self) -> None:
        source = _source(7, 102)
        slide, rels, parts, types = _export(_chart("preserved", source=source) + _chart("rebuilt"))
        rows = _chart_rows(slide, rels, parts)
        self.assertEqual(rows[1]["chart"], "ppt/charts/chart103.xml")
        self.assertEqual(rows[1]["workbook_values"], ["3", "2"])
        self.assert_source_unchanged(source, parts, types)

    def test_every_existing_family_member_and_content_type_reserves_the_number(self) -> None:
        for chartex in (False, True):
            prefix = "chartEx" if chartex else "chart"
            names = [f"ppt/charts/{prefix}101.xml", f"ppt/charts/_rels/{prefix}101.xml.rels",
                     "ppt/embeddings/Microsoft_Excel_Sheet101.xlsx"]
            if chartex:
                names += ["ppt/charts/style101.xml", "ppt/charts/colors101.xml"]
            for name in names:
                for override_only in (False, True):
                    with self.subTest(name=name, override_only=override_only):
                        with tempfile.TemporaryDirectory() as temporary:
                            root = Path(temporary)
                            if not override_only:
                                path = root / name
                                path.parent.mkdir(parents=True, exist_ok=True)
                                path.write_bytes(b"source bytes")
                            registry = PackagePartRegistry(root, {name: "source/content-type"})
                            slide, rels, parts, _types = _export(
                                _chart("rebuilt", chartex=chartex), package_parts=registry,
                            )
                            row = _chart_rows(slide, rels, parts)[0]
                            self.assertEqual(row["chart"], f"ppt/charts/{prefix}102.xml")
                            self.assertEqual(row["workbook_values"], ["3", "2"])
                            self.assertNotIn(name, parts)

    def test_chartex_skips_preserved_style_and_colors(self) -> None:
        for name in ("style102.xml", "colors102.xml", "_rels/chartEx102.xml.rels"):
            with self.subTest(name=name):
                source = _source(7, 7, extras={
                    f"ppt/charts/{name}": f'<Relationships xmlns="{NS["rel"]}"/>'.encode(),
                })
                slide, rels, parts, types = _export(
                    _chart("preserved", source=source) + _chart("rebuilt", chartex=True),
                )
                rows = _chart_rows(slide, rels, parts)
                self.assertEqual(rows[1]["chart"], "ppt/charts/chartEx103.xml")
                self.assertEqual(rows[1]["values"], ["3", "2"])
                self.assert_source_unchanged(source, parts, types)

    def test_legacy_numbers_stay_unchanged_without_collisions(self) -> None:
        slide, rels, parts, _types = _export(
            _chart("first") + _chart("second", chartex=True) + _chart("third"),
        )
        self.assertEqual([row["chart"] for row in _chart_rows(slide, rels, parts)],
                         ["ppt/charts/chart101.xml", "ppt/charts/chartEx102.xml", "ppt/charts/chart103.xml"])

    def test_more_than_one_hundred_charts_cannot_collide_with_the_next_slide(self) -> None:
        registry = PackagePartRegistry()
        _export("".join(_chart(f"chart-{index}") for index in range(101)), package_parts=registry)
        slide, rels, parts, _types = _export(_chart("next-page"), slide_num=2, package_parts=registry)
        self.assertEqual(_chart_rows(slide, rels, parts)[0]["chart"], "ppt/charts/chart202.xml")

    def test_nested_charts_share_the_package_registry(self) -> None:
        source = _source()
        slide, rels, parts, _types = _export(
            f'<g id="left">{_chart("preserved", source=source)}</g>'
            f'<g id="right">{_chart("rebuilt")}</g>',
        )
        self.assertEqual([row["values"] for row in _chart_rows(slide, rels, parts)],
                         [["11", "12"], ["3", "2"]])

    def test_duplicate_new_writes_fail_even_when_the_bytes_match(self) -> None:
        with patch.object(PackagePartRegistry, "next_index", return_value=101):
            with self.assertRaisesRegex(RuntimeError, r"part collision: .*ppt/.*first.*second"):
                _export(_chart("first") + _chart("second"))

    def test_conflicting_source_bytes_name_both_objects(self) -> None:
        with self.assertRaisesRegex(RuntimeError, r"part collision: .*ppt/.*first.*second"):
            _export(_chart("first", source=_source()) + _chart("second", source=_source(values=(8, 9))))

    def test_conflicting_source_content_types_fail_before_registration(self) -> None:
        source = _source()
        changed = json.loads(json.dumps(source))
        changed["parts"][0]["content_type"] = "conflicting/content-type"
        with self.assertRaisesRegex(RuntimeError, r"part collision: .*chart102.xml.*first.*second"):
            _export(_chart("first", source=source) + _chart("second", source=changed))

    def test_identical_source_dependencies_can_be_reused(self) -> None:
        source = _source()
        _slide, _rels, parts, types = _export(_chart("first", source=source) + _chart("second", source=source))
        self.assertEqual(len(parts), 3)
        self.assert_source_unchanged(source, parts, types)

    def test_source_cannot_overwrite_a_template_part(self) -> None:
        source = _source()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            part = root / source["chart_part"]
            part.parent.mkdir(parents=True)
            part.write_bytes(b"template bytes")
            with self.assertRaisesRegex(RuntimeError, r"part collision: .*chart102.xml.*template/source.*source"):
                _export(_chart("source", source=source), package_parts=PackagePartRegistry(root))
