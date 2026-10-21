#!/usr/bin/env python3
"""
PPT Master - Native Chart Round-trip Identity Regression Tests

Keep imported chart identities on the graphicFrame while companion shapes
remain siblings with fresh ids through the public SVG converter.

Usage:
    python3 -m unittest tests.test_native_chart_roundtrip_identity

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local SVG-to-PPTX converter.
"""

from __future__ import annotations

import base64
import hashlib
import json
import posixpath
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pptx_transitions import (
    MorphPairExpectation,
    create_transition_xml,
    validate_pptx_morph_pairs,
)
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes


NS = {
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
SVG_NS = "http://www.w3.org/2000/svg"


def _chart(attributes: dict | None = None, **extra: object) -> str:
    marker = ET.Element(f"{{{SVG_NS}}}g", {
        "id": "chart",
        "data-pptx-replace-with": "chart",
        "data-pptx-native-authority": "json",
        **(attributes or {}),
    })
    ET.SubElement(marker, f"{{{SVG_NS}}}metadata", {
        "type": "application/json",
    }).text = json.dumps({
        "type": "column",
        "x": 100, "y": 100, "width": 600, "height": 400,
        "categories": ["A", "B"],
        "series": [{"name": "Values", "values": [3, 2]}],
        "name": "Payload chart",
        **extra,
    })
    return ET.tostring(marker, encoding="unicode")


def _blob(data: bytes) -> dict:
    return {
        "encoding": "base64",
        "payload": base64.b64encode(data).decode("ascii"),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


class NativeChartRoundtripIdentityTests(unittest.TestCase):
    def _export(self, body: str, *, trace_out: list | None = None) -> tuple:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            svg = root / "chart.svg"
            svg.write_text(
                f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720">{body}</svg>',
                encoding="utf-8",
            )
            xml, _media, rels, targets, parts, content_types = convert_svg_to_slide_shapes(
                svg, resource_root=root, native_objects=True, trace_out=trace_out,
            )
        return ET.fromstring(xml), rels, parts, content_types, targets

    def _assert_unique_ids(self, slide: ET.Element) -> None:
        ids = [node.get("id") for node in slide.findall(".//p:cNvPr", NS)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rebuilt_chart_keeps_id_and_morph_name_with_fresh_companions(self) -> None:
        chart_types = ({}, {"type": "treemap", "levels": [["A", "B"]], "values": [3, 2]})
        for chart_type in chart_types:
            for companions in (
                {}, {"source": "Source note"}, {"notes": ["Chart note"]}, {"caption": "Caption"},
                {"title": {"text": "Title", "x": 100, "y": 50, "width": 600, "height": 40}},
            ):
                with self.subTest(chart_type=chart_type, companions=companions):
                    slide, *_rest = self._export(
                        _chart({
                            "data-pptx-shape-id": "29",
                            "data-pptx-shape-scope": "slide",
                            "data-pptx-shape-name": '!!Revenue & "margin"',
                        }, **chart_type, **companions)
                        + '<rect x="0" y="0" width="10" height="10" '
                        'data-pptx-shape-id="2" data-pptx-shape-scope="slide"/>'
                    )
                    tree = slide.find("p:cSld/p:spTree", NS)
                    self.assertIsNone(tree.find("p:grpSp", NS))
                    frame = tree.find("p:graphicFrame/p:nvGraphicFramePr/p:cNvPr", NS)
                    self.assertIsNotNone(frame)
                    self.assertEqual(frame.get("id"), "29")
                    self.assertEqual(frame.get("name"), '!!Revenue & "margin"')
                    self.assertEqual(
                        [n.get("id") for n in slide.findall(".//p:cNvPr", NS)
                         if n.get("name", "").startswith("!!")],
                        ["29"],
                    )
                    if companions:
                        companion_ids = [
                            n.get("id") for n in tree.findall("p:sp/p:nvSpPr/p:cNvPr", NS)
                            if n.get("id") != "2"
                        ]
                        self.assertEqual(len(companion_ids), 1)
                        self.assertTrue(set(companion_ids).isdisjoint({"2", "29"}))
                    self._assert_unique_ids(slide)

    def test_companion_union_bounds_and_animation_trace_keep_frame_first(self) -> None:
        trace = []
        slide, _rels, _parts, _types, targets = self._export(_chart(
            {"data-pptx-shape-id": "29"},
            source={"text": "Source note", "x": 750, "y": 550, "width": 200, "height": 30},
        ), trace_out=trace)
        tree = slide.find("p:cSld/p:spTree", NS)
        shape_tags = {f"{{{NS['p']}}}{tag}" for tag in ("graphicFrame", "sp", "grpSp")}
        shapes = [node for node in tree if node.tag in shape_tags]
        self.assertEqual([node.tag for node in shapes], [f"{{{NS['p']}}}graphicFrame", f"{{{NS['p']}}}sp"])
        self.assertEqual(targets, [(29, "chart")])
        event = next(event for event in trace[0]["events"] if event.get("id") == "chart")
        self.assertEqual(event["shape_id"], 29)
        self.assertEqual(event["bounds_emu"], [value * 9525 for value in (100, 100, 950, 580)])

    def test_chartex_title_keeps_top_level_morph_pair(self) -> None:
        attributes = {"data-pptx-shape-id": "29", "data-pptx-shape-name": "!!chart"}
        payload = {"type": "treemap", "levels": [["A", "B"]], "values": [3, 2]}
        source, *_rest = self._export(_chart(attributes, **payload))
        destination, *_rest = self._export(_chart(attributes, title="Chart title", **payload))
        namespaces = " ".join(f'xmlns:{key}="{value}"' for key, value in NS.items())
        transitions = ET.fromstring(f'<root {namespaces}>{create_transition_xml("morph")}</root>')
        destination.extend(transitions)
        with tempfile.TemporaryDirectory() as temporary:
            pptx = Path(temporary) / "morph.pptx"
            with ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", ET.tostring(source))
                archive.writestr("ppt/slides/slide2.xml", ET.tostring(destination))
            validate_pptx_morph_pairs(pptx, [MorphPairExpectation(1, 2, "chart")])

    def test_rebuilt_chart_respects_source_scope(self) -> None:
        slide, *_rest = self._export(
            '<rect x="0" y="0" width="10" height="10" '
            'data-pptx-shape-id="29" data-pptx-shape-scope="slide"/>'
            + _chart({"data-pptx-shape-id": "29", "data-pptx-shape-scope": "layout1"})
        )
        frame = slide.find(".//p:graphicFrame/p:nvGraphicFramePr/p:cNvPr", NS)
        self.assertEqual(frame.get("id"), "30")
        self._assert_unique_ids(slide)

    def test_payload_morph_name_stays_on_frame_without_source_name(self) -> None:
        slide, *_rest = self._export(_chart(
            {"data-pptx-shape-id": "29"}, name="!!chart", notes=["Chart note"],
        ))
        self.assertEqual(
            [(n.get("id"), n.get("name")) for n in slide.findall(".//p:cNvPr", NS)
             if n.get("name", "").startswith("!!")],
            [("29", "!!chart")],
        )

    def test_without_source_id_keeps_allocation_and_name_precedence(self) -> None:
        for companions, expected_ids in (({}, ["1", "2", "3"]),
                                         ({"notes": ["Note"]}, ["1", "4", "2", "3", "5"])):
            for name, expected_name in (("Payload chart", "Payload chart"), ("", "chart")):
                with self.subTest(companions=companions, name=name):
                    slide, *_rest = self._export(
                        _chart({"data-pptx-shape-name": "Ignored without source id"},
                               name=name, **companions)
                        + '<rect x="0" y="0" width="10" height="10"/>'
                    )
                    self.assertEqual(
                        [n.get("id") for n in slide.findall(".//p:cNvPr", NS)], expected_ids,
                    )
                    frame = slide.find(".//p:graphicFrame/p:nvGraphicFramePr/p:cNvPr", NS)
                    self.assertEqual(frame.get("name"), expected_name)
                    group_name = slide.find(".//p:grpSp/p:nvGrpSpPr/p:cNvPr", NS)
                    if companions:
                        self.assertEqual(group_name.get("name"), expected_name)

    def test_rebuilt_charts_keep_distinct_relationships_and_parts(self) -> None:
        slide, rels, parts, _types, _targets = self._export(
            _chart({"id": "first", "data-pptx-shape-id": "29"})
            + _chart({"id": "second", "data-pptx-shape-id": "30"},
                     type="treemap", levels=[["A", "B"]], values=[3, 2])
        )
        references = slide.findall(".//c:chart", NS) + slide.findall(".//cx:chart", NS)
        rel_ids = [node.get(f"{{{NS['r']}}}id") for node in references]
        self.assertEqual(len(set(rel_ids)), 2)
        targets = []
        for rel_id in rel_ids:
            rel = next(item for item in rels if item["id"] == rel_id)
            target = posixpath.normpath(posixpath.join("ppt/slides", rel["target"]))
            self.assertIn(target, parts)
            targets.append(target)
        self.assertEqual(len(set(targets)), 2)
        self._assert_unique_ids(slide)

    def test_source_package_keeps_frame_name_and_exact_parts(self) -> None:
        source, rels, parts, content_types, _targets = self._export(_chart(name="!!source-chart"))
        frame = source.find(".//p:graphicFrame", NS)
        frame.find("p:nvGraphicFramePr/p:cNvPr", NS).set("id", "29")
        chart_part = posixpath.normpath(posixpath.join("ppt/slides", rels[0]["target"]))
        package = {
            "chart_part": chart_part,
            "frame": _blob(ET.tostring(frame)),
            "parts": [{
                "name": name, **_blob(data), "content_type": content_types.get(name),
            } for name, data in parts.items()],
        }
        slide, result_rels, result_parts, result_types, _targets = self._export(_chart(
            {"data-pptx-shape-id": "29"}, source_package=package,
            notes=["Must not be synthesized"],
        ))
        result_frame = slide.find(".//p:graphicFrame", NS)
        self.assertEqual(ET.tostring(result_frame), ET.tostring(frame))
        self.assertEqual(result_rels, rels)
        self.assertEqual(result_parts, parts)
        self.assertEqual(result_types, content_types)
        self.assertIsNone(slide.find(".//p:grpSp", NS))
        self._assert_unique_ids(slide)
