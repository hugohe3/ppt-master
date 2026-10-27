#!/usr/bin/env python3
"""Regression tests for source gradients and small native arc preservation."""

from __future__ import annotations

import base64
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_gradients import native_gradient_metadata, preserved_native_gradient_xml
from svg_authoring_view import project_svg_batch
from svg_quality.checker import SVGQualityChecker
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes, SvgNativeConversionError

SVG_NS = "http://www.w3.org/2000/svg"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": DML_NS, "p": PML_NS}


class ExportDegenerateSweepTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.svg"

    def _gradient_shape(self, *, vertical: bool = False, transparent: bool = False) -> ET.Element:
        root = ET.fromstring(
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" lang="en-US" '
            'data-pptx-page-role="content"><defs/></svg>'
        )
        opacity = "0" if transparent else "1"
        gradient = ET.fromstring(
            f'<linearGradient xmlns="{SVG_NS}" id="stroke" x1="100" y1="100" '
            'x2="400" y2="100" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#3060C0" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="#D7263D" stop-opacity="{opacity}"/>'
            '</linearGradient>'
        )
        native = ET.fromstring(
            f'<a:gradFill xmlns:a="{DML_NS}"><a:gsLst>'
            f'<a:gs pos="0"><a:srgbClr val="3060C0"><a:alpha val="{0 if transparent else 100000}"/>'
            '</a:srgbClr></a:gs><a:gs pos="100000"><a:srgbClr val="D7263D">'
            f'<a:alpha val="{0 if transparent else 100000}"/></a:srgbClr></a:gs>'
            '</a:gsLst><a:lin ang="0" scaled="1"/></a:gradFill>'
        )
        gradient.attrib.update(native_gradient_metadata(native, gradient))
        root[0].append(gradient)
        frame = "100 100 0 300" if vertical else "100 100 300 0"
        path = "M 100 100 L 100 400" if vertical else "M 100 100 L 400 100"
        group = ET.SubElement(root, f"{{{SVG_NS}}}g", {
            "id": "source-shape", "data-pptx-object": "shape", "data-pptx-frame": frame,
            "data-pptx-geometry-kind": "custom", "data-pptx-semantic-object": "shape",
            "data-pptx-bounds": "98 98 4 304" if vertical else "98 98 304 4",
        })
        geometry = (
            f'<a:custGeom xmlns:a="{DML_NS}"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
            '<a:rect l="l" t="t" r="r" b="b"/><a:pathLst><a:path w="300" h="100" fill="none">'
            '<a:moveTo><a:pt x="0" y="0"/></a:moveTo><a:lnTo><a:pt x="300" y="100"/>'
            '</a:lnTo></a:path></a:pathLst></a:custGeom>'
        )
        ET.SubElement(group, f"{{{SVG_NS}}}path", {
            "d": path, "data-pptx-part": "geometry", "stroke": "url(#stroke)",
            "stroke-width": "4", "fill": "none",
            "data-pptx-custgeom": base64.b64encode(geometry.encode()).decode(),
            "data-pptx-geometry-sha256": hashlib.sha256(path.encode()).hexdigest(),
        })
        self.source.write_bytes(ET.tostring(root))
        return root

    def test_imported_gradient_zero_axis_survives_projection_and_export(self) -> None:
        for vertical in (False, True):
            with self.subTest(vertical=vertical):
                root = self._gradient_shape(vertical=vertical)
                output = self.root / ("vertical" if vertical else "horizontal")
                projected = output / self.source.name
                project_svg_batch(
                    [(self.source, projected)], self.root, output,
                    force=False, projection_kind="layered",
                )
                tree = ET.parse(projected).getroot()
                gradient = tree.find(f"{{{SVG_NS}}}defs/{{{SVG_NS}}}linearGradient")
                self.assertIsNotNone(preserved_native_gradient_xml(gradient))
                path = tree.find(f".//{{{SVG_NS}}}path")
                self.assertIn("data-pptx-custgeom", path.attrib)
                checked = SVGQualityChecker(quick_generate=True).check_file(str(projected))
                self.assertEqual(checked["errors"], [])
                xml, *_ = convert_svg_to_slide_shapes(projected, resource_root=self.root)
                native = ET.fromstring(xml)
                extent = native.find(".//p:sp/p:spPr/a:xfrm/a:ext", NS)
                self.assertEqual(extent.attrib, {
                    "cx": "0" if vertical else "2857500",
                    "cy": "2857500" if vertical else "0",
                })
                exported_gradient = native.find(".//a:ln/a:gradFill", NS)
                expected = ET.fromstring(preserved_native_gradient_xml(root[0][0]))
                self.assertEqual(ET.tostring(exported_gradient), ET.tostring(expected))
                custom = native.find(".//a:custGeom", NS)
                self.assertEqual(len(custom.findall("a:pathLst/a:path", NS)), 1)

    def test_transparent_native_gradient_does_not_admit_zero_axis_shape(self) -> None:
        self._gradient_shape(transparent=True)
        with self.assertRaisesRegex(SvgNativeConversionError, "must be positive"):
            convert_svg_to_slide_shapes(self.source, resource_root=self.root)

    def test_authored_gradient_does_not_gain_source_frame_exception(self) -> None:
        root = self._gradient_shape()
        gradient = root[0][0]
        for name in list(gradient.attrib):
            if name.startswith("data-pptx-gradient"):
                del gradient.attrib[name]
        self.source.write_bytes(ET.tostring(root))
        with self.assertRaisesRegex(SvgNativeConversionError, "gradientUnits"):
            convert_svg_to_slide_shapes(self.source, resource_root=self.root)
        gradient.attrib.update({"gradientUnits": "objectBoundingBox", "x1": "0", "y1": "0", "x2": "1", "y2": "0"})
        self.source.write_bytes(ET.tostring(root))
        with self.assertRaisesRegex(SvgNativeConversionError, "zero intrinsic height"):
            convert_svg_to_slide_shapes(self.source, resource_root=self.root)

    def test_small_thick_circle_arc_keeps_representable_geometry(self) -> None:
        self.source.write_text(
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" lang="en-US" data-pptx-page-role="content">'
            '<g id="arc" data-pptx-bounds="530 250 220 220"><circle cx="640" cy="360" r="100" '
            'fill="none" stroke="#3060C0" stroke-width="20" stroke-dasharray="0.1 628.218530718"/>'
            '</g></svg>', encoding="utf-8",
        )
        checked = SVGQualityChecker(quick_generate=True).check_file(str(self.source))
        self.assertEqual(checked["errors"], [])
        xml, *_ = convert_svg_to_slide_shapes(self.source, resource_root=self.root)
        native = ET.fromstring(xml)
        self.assertEqual(len(native.findall(".//p:sp", NS)), 1)
        extent = native.find(".//p:sp/p:spPr/a:xfrm/a:ext", NS)
        self.assertGreater(int(extent.get("cx")), 0)
        self.assertLess(int(extent.get("cx")), 4763)
        self.assertGreater(int(extent.get("cy")), 0)
        self.assertIsNotNone(native.find(".//a:custGeom/a:pathLst/a:path", NS))
