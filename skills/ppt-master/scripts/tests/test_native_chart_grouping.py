#!/usr/bin/env python3
"""Regression tests for native chart companion groups and animation targets."""

from __future__ import annotations

import base64
import hashlib
import json
import random
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_animations import create_sequence_timing_xml  # noqa: E402
from svg_to_pptx.drawingml.context import ConvertContext  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_element  # noqa: E402
from svg_to_pptx.native_objects import stamp_native_fallback_baseline  # noqa: E402
from svg_to_pptx.pptx_package.builder import _build_sequence_targets  # noqa: E402


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
SVG_NS = "http://www.w3.org/2000/svg"
EMU_PER_PX = 9525


def _payload(**extra: object) -> dict:
    return {
        "type": "column",
        "x": 100, "y": 80, "width": 400, "height": 240,
        "categories": ["A", "B"],
        "series": [{"name": "S", "values": [1, 2]}],
        **extra,
    }


def _marker(payload: dict, kind: str = "chart", **attrs: str) -> ET.Element:
    elem = ET.Element(f"{{{SVG_NS}}}g", {
        "id": "sales-chart",
        "data-pptx-replace-with": kind,
        "data-pptx-native-authority": "json",
        **attrs,
    })
    ET.SubElement(elem, f"{{{SVG_NS}}}metadata", {
        "type": "application/json",
    }).text = json.dumps(payload)
    ET.SubElement(elem, f"{{{SVG_NS}}}rect", {
        "x": "100", "y": "80", "width": "400", "height": "240", "fill": "#123456",
    })
    ET.SubElement(elem, f"{{{SVG_NS}}}text", {
        "x": "100", "y": "350", "font-size": "16",
    }).text = "Fallback label"
    return elem


def _parse(xml: str) -> ET.Element:
    namespaces = " ".join(f'xmlns:{key}="{value}"' for key, value in NS.items())
    return ET.fromstring(f"<root {namespaces}>{xml}</root>")


def _shape_id(shape: ET.Element) -> int:
    return int(shape.find(".//p:cNvPr", NS).get("id"))


def _box(shape: ET.Element, path: str) -> tuple[int, int, int, int]:
    xfrm = shape.find(path, NS)
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    x, y = int(off.get("x")), int(off.get("y"))
    return x, y, x + int(ext.get("cx")), y + int(ext.get("cy"))


class NativeChartGroupingTests(unittest.TestCase):
    def _convert(self, elem: ET.Element, **options: object) -> tuple:
        ctx = ConvertContext(native_objects_enabled=True, trace_events=[], **options)
        result = convert_element(elem, ctx)
        self.assertIsNotNone(result)
        return result, _parse(result.xml), ctx

    def _assert_group(self, result, root: ET.Element, ctx: ConvertContext) -> ET.Element:
        self.assertEqual(len(root), 1, "replacement must be one slide object")
        group = root[0]
        self.assertEqual(group.tag, f"{{{NS['p']}}}grpSp")
        frame = group.find("p:graphicFrame", NS)
        self.assertIsNotNone(frame)
        labels = group.findall("p:sp", NS)
        self.assertTrue(labels)
        child_bounds = [_box(frame, "p:xfrm")]
        child_bounds.extend(_box(label, "p:spPr/a:xfrm") for label in labels)
        expected = (
            min(box[0] for box in child_bounds),
            min(box[1] for box in child_bounds),
            max(box[2] for box in child_bounds),
            max(box[3] for box in child_bounds),
        )
        self.assertEqual(result.bounds_emu, expected)
        self.assertEqual(_box(group, "p:grpSpPr/a:xfrm"), expected)
        xfrm = group.find("p:grpSpPr/a:xfrm", NS)
        self.assertEqual(xfrm.find("a:off", NS).attrib, xfrm.find("a:chOff", NS).attrib)
        self.assertEqual(xfrm.find("a:ext", NS).attrib, xfrm.find("a:chExt", NS).attrib)
        ids = [int(node.get("id")) for node in group.findall(".//p:cNvPr", NS)]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ctx.anim_targets, [(_shape_id(group), "sales-chart")])
        self.assertNotEqual(_shape_id(group), _shape_id(frame))
        self.assertEqual(ctx.trace_events[-1]["output_geometry"], "native-object")
        self.assertEqual(ctx.trace_events[-1]["fidelity"], "native-normalized")
        self.assertEqual(ctx.trace_events[-1]["shape_id"], _shape_id(group))
        return group

    def test_classic_companions_keep_text_style_and_union_bounds(self) -> None:
        payload = _payload(
            name='Sales & "margin"',
            title={"text": "Bounded title", "x": 50, "y": 30, "width": 200, "height": 30},
            caption="Caption",
            source="Source",
            notes=[{
                "text": "Far right note", "x": 520, "y": 100, "width": 100, "height": 24,
                "font_size": 18, "color": "#C8102E", "bold": True,
            }],
            footnote="Footnote",
        )
        result, root, ctx = self._convert(_marker(payload))
        group = self._assert_group(result, root, ctx)
        self.assertEqual(
            [node.text for node in group.findall("p:sp/p:txBody//a:t", NS)],
            ["Bounded title", "Caption", "Source", "Far right note", "Footnote"],
        )
        self.assertEqual(result.bounds_emu, tuple(v * EMU_PER_PX for v in (50, 30, 620, 376)))
        self.assertEqual(group.find("p:nvGrpSpPr/p:cNvPr", NS).get("name"), 'Sales & "margin"')
        note = group.findall("p:sp", NS)[3]
        run = note.find("p:txBody/a:p/a:r/a:rPr", NS)
        self.assertEqual(run.get("sz"), "1350")
        self.assertEqual(run.get("b"), "1")
        self.assertEqual(run.find("a:solidFill/a:srgbClr", NS).get("val"), "C8102E")
        self.assertTrue(all(label.find("p:nvSpPr/p:cNvSpPr", NS).get("txBox") == "1"
                            for label in group.findall("p:sp", NS)))

    def test_sidecar_timing_targets_whole_group_once(self) -> None:
        result, root, ctx = self._convert(_marker(_payload(notes=["First", "Second"])))
        group = self._assert_group(result, root, ctx)
        targets, _ = _build_sequence_targets(
            ctx.anim_targets, "slide", {"groups": {"sales-chart": {
                "effect": "entrance_wipe", "effect_options": {"direction": "right"},
                "duration": 0.9, "order": 3,
            }}}, None, {}, 0.5, 0.2, 0, random.Random(0),
        )
        self.assertEqual(len(targets), 1)
        timing = _parse(create_sequence_timing_xml(targets))
        self.assertEqual(
            {int(node.get("spid")) for node in timing.findall(".//p:spTgt", NS)},
            {_shape_id(group)},
        )
        self.assertIn('filter="wipe(right)"', ET.tostring(timing, encoding="unicode"))
        self.assertFalse(timing.findall(".//p:bldP", NS))

    def test_no_emitted_companions_keep_single_frame(self) -> None:
        for extra in ({}, {"notes": [], "caption": " ", "source": ""},
                      {"notes": [{"text": " "}], "title": "Internal chart title"}):
            with self.subTest(extra=extra):
                result, root, ctx = self._convert(_marker(_payload(**extra)))
                self.assertEqual(len(root), 1)
                self.assertEqual(root[0].tag, f"{{{NS['p']}}}graphicFrame")
                self.assertEqual(ctx.anim_targets, [(_shape_id(root[0]), "sales-chart")])
                self.assertEqual(result.bounds_emu, tuple(v * EMU_PER_PX for v in (100, 80, 500, 320)))

    def test_chartex_companions_keep_chart_relationship_and_package(self) -> None:
        for companions in ({}, {"title": "Tree", "subtitle": "Subtitle", "notes": ["Note"]}):
            with self.subTest(companions=companions):
                result, root, ctx = self._convert(_marker(_payload(
                    type="treemap", levels=[["A", "B"]], values=[1, 2], **companions,
                )))
                if companions:
                    group = self._assert_group(result, root, ctx)
                    self.assertEqual([n.text for n in group.findall(".//a:t", NS)],
                                     ["Tree", "Subtitle", "Note"])
                else:
                    self.assertEqual(root[0].tag, f"{{{NS['p']}}}graphicFrame")
                chart = root.find(".//cx:chart", NS)
                self.assertIsNotNone(chart)
                self.assertEqual(chart.get(f"{{{NS['r']}}}id"), ctx.rel_entries[0]["id"])
                self.assertTrue(ctx.rel_entries[0]["type"].endswith("/chartEx"))
                self.assertIn("ppt/charts/chartEx101.xml", ctx.package_files)
                self.assertIn("ppt/charts/style101.xml", ctx.package_files)
                self.assertIn("ppt/charts/colors101.xml", ctx.package_files)
                self.assertIn("ppt/embeddings/Microsoft_Excel_Sheet101.xlsx", ctx.package_files)

    def test_source_package_keeps_claimed_frame_id_and_exact_parts(self) -> None:
        _, original, source_ctx = self._convert(_marker(_payload()))
        frame = original[0]
        frame.find("p:nvGraphicFramePr/p:cNvPr", NS).set("id", "77")
        frame_bytes = ET.tostring(frame, encoding="utf-8")

        def blob(data: bytes) -> dict:
            return {"encoding": "base64", "payload": base64.b64encode(data).decode("ascii"),
                    "sha256": hashlib.sha256(data).hexdigest()}

        source = {
            "chart_part": "ppt/charts/chart101.xml",
            "frame": blob(frame_bytes),
            "parts": [{
                "name": name, **blob(data),
                "content_type": source_ctx.content_type_overrides.get(name),
            } for name, data in source_ctx.package_files.items()],
        }
        elem = _marker(_payload(source_package=source, notes=["Must not be synthesized"]),
                       **{"data-pptx-shape-id": "77"})
        _, root, ctx = self._convert(
            elem, reserved_shape_ids=frozenset({77}),
            source_shape_id_map={("slide", "77"): 77}, rel_id_counter=8,
        )
        self.assertEqual(len(root), 1)
        self.assertEqual(root[0].tag, f"{{{NS['p']}}}graphicFrame")
        self.assertEqual(_shape_id(root[0]), 77)
        self.assertEqual(ctx.anim_targets, [(77, "sales-chart")])
        self.assertEqual(ctx.package_files, source_ctx.package_files)
        self.assertEqual(ctx.content_type_overrides, source_ctx.content_type_overrides)
        frame.find(".//c:chart", NS).set(f"{{{NS['r']}}}id", "rId8")
        self.assertEqual(ET.tostring(root[0]), ET.tostring(frame))

    def test_table_stays_one_native_frame(self) -> None:
        _, root, ctx = self._convert(_marker({
            "schema": "ppt-master.semantic-table.v2",
            "x": 100, "y": 80, "width": 400, "height": 240,
            "rows": [["A", "B"], ["1", "2"]],
        }, kind="table"))
        self.assertEqual(len(root), 1)
        self.assertEqual(root[0].tag, f"{{{NS['p']}}}graphicFrame")
        self.assertIsNotNone(root.find(".//a:tbl", NS))
        self.assertEqual(ctx.anim_targets, [(_shape_id(root[0]), "sales-chart")])

    def test_svg_fallback_still_groups_and_reports_visual_geometry(self) -> None:
        elem = _marker(_payload(notes=["Fallback label"]))
        elem.attrib.pop("data-pptx-native-authority")
        stamp_native_fallback_baseline(elem)
        ctx = ConvertContext(trace_events=[])
        result = convert_element(elem, ctx)
        root = _parse(result.xml)
        self.assertEqual(len(root), 1)
        self.assertEqual(root[0].tag, f"{{{NS['p']}}}grpSp")
        self.assertIsNone(root.find(".//p:graphicFrame", NS))
        self.assertEqual(ctx.anim_targets, [(_shape_id(root[0]), "sales-chart")])
        self.assertEqual(ctx.trace_events[-1]["output_geometry"], "group")
        self.assertEqual(ctx.trace_events[-1]["fidelity"], "visual-only")

    def test_nested_transformed_group_includes_outlying_companion(self) -> None:
        for explicit in (True, False):
            with self.subTest(explicit=explicit):
                outer = ET.Element(f"{{{SVG_NS}}}g", {
                    "id": "section", "transform": "translate(10 20) scale(2)",
                })
                payload = _payload(notes=[{
                    "text": "Outside", "x": 1100, "y": 700, "width": 100, "height": 30,
                }])
                if not explicit:
                    for key in ("x", "y", "width", "height"):
                        payload.pop(key)
                elem = _marker(payload)
                if not explicit:
                    elem.attrib.pop("data-pptx-native-authority")
                    elem.remove(elem.find(f"{{{SVG_NS}}}text"))
                    stamp_native_fallback_baseline(elem)
                outer.append(elem)
                result, root, ctx = self._convert(outer)
                group = root[0]
                self.assertEqual(ctx.anim_targets, [(_shape_id(group), "section")])
                self.assertEqual(len(root.findall(".//p:grpSp", NS)), 2)
                frame = group.find(".//p:graphicFrame", NS)
                # Explicit payload boxes are already in slide coordinates;
                # inferred fallback bounds consume the ancestor transform.
                frame_box = (100, 80, 500, 320) if explicit else (210, 180, 1010, 660)
                self.assertEqual(_box(frame, "p:xfrm"), tuple(v * EMU_PER_PX for v in frame_box))
                expected = tuple(v * EMU_PER_PX for v in (*frame_box[:2], 1200, 730))
                self.assertEqual(result.bounds_emu, expected)
                self.assertEqual(_box(group, "p:grpSpPr/a:xfrm"), expected)


if __name__ == "__main__":
    unittest.main()
