#!/usr/bin/env python3
"""PPT Master - Round-trip Connector Endpoint Regression Tests

Keep native attachments consistent when source endpoints are deleted or rebuilt.

Usage:
    python3 -m unittest tests.test_roundtrip_connector_endpoints

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPTX import/export pipeline.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_to_pptx.pptx_package import builder
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main as export_main


SVG = "http://www.w3.org/2000/svg"
NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def _png(red: int) -> bytes:
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + bytes((red, 70, 100)) * 2) * 2))
            + chunk(b"IEND", b""))


def _make_source(root: Path, *, nested: bool = False, hidden_start: bool = False) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "source.png").write_bytes(_png(20))
    page = root / "source.svg"
    page.write_text(
        f'<svg xmlns="{SVG}" viewBox="0 0 960 720" lang="en-US">'
        '<rect x="100" y="100" width="100" height="100" fill="#123456"/>'
        '<image href="source.png" x="400" y="100" width="100" height="100"/>'
        '</svg>', encoding="utf-8",
    )
    source = root / "source.pptx"
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        if not create_pptx_with_native_svg(
            [page], source, resource_root=root, pptx_structure="flat",
            use_compat_mode=False, transition=None, workers=1, verbose=False,
        ):
            raise AssertionError("Synthetic source export failed")
    with zipfile.ZipFile(source) as package:
        parts = {name: package.read(name) for name in package.namelist()}
    slide = ET.fromstring(parts["ppt/slides/slide1.xml"])
    tree = slide.find("p:cSld/p:spTree", NS)
    for tag, shape_id, name in (("sp", "2", "start"), ("pic", "3", "end")):
        shape = tree.find(f"p:{tag}", NS)
        nv = shape.find("./*/p:cNvPr", NS)
        nv.set("id", shape_id)
        nv.set("name", name)
        if hidden_start and shape_id == "2":
            nv.set("hidden", "1")
    connector = ET.fromstring(
        f'<p:cxnSp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">'
        '<p:nvCxnSpPr><p:cNvPr id="4" name="connection"/><p:cNvCxnSpPr>'
        '<a:stCxn id="2" idx="1"/><a:endCxn id="3" idx="3"/>'
        '</p:cNvCxnSpPr><p:nvPr/></p:nvCxnSpPr>'
        '<p:spPr><a:xfrm><a:off x="1905000" y="1428750"/>'
        '<a:ext cx="1905000" cy="0"/></a:xfrm>'
        '<a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom>'
        '<a:ln w="19050"><a:solidFill><a:srgbClr val="123456"/></a:solidFill></a:ln>'
        '</p:spPr></p:cxnSp>'
    )
    tree.append(connector)
    if nested:
        group = ET.fromstring(
            f'<p:grpSp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">'
            '<p:nvGrpSpPr><p:cNvPr id="5" name="parent"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="9144000" cy="6858000"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="9144000" cy="6858000"/></a:xfrm></p:grpSpPr>'
            '</p:grpSp>'
        )
        for child in list(tree):
            if child.tag in {f'{{{NS["p"]}}}{tag}' for tag in ("sp", "pic", "cxnSp")}:
                tree.remove(child)
                group.append(child)
        tree.append(group)
    parts["ppt/slides/slide1.xml"] = ET.tostring(slide, encoding="utf-8")
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as package:
        for name, data in parts.items():
            package.writestr(name, data)
    return source


def _edit(project: Path, operation: str) -> None:
    page = project / "authoring-svg-flat/slide_01.svg"
    root = ET.parse(page).getroot()
    if operation.startswith("delete"):
        target = "3" if operation == "delete_end" else "2"
        for parent in root.iter():
            for child in list(parent):
                if child.get("data-pptx-source-ref") == f"slide:{target}":
                    parent.remove(child)
        if operation == "delete_reuse":
            root.append(ET.fromstring(
                f'<rect xmlns="{SVG}" id="addition" x="700" y="500" '
                'width="80" height="80" fill="#ABCDEF" '
                'data-pptx-shape-id="2" data-pptx-shape-scope="slide"/>'
            ))
    elif operation in {"href", "bytes"}:
        image = root.find(f".//{{{SVG}}}image")
        if operation == "href":
            replacement = project / "images/replacement.png"
            replacement.write_bytes(_png(200))
            image.set("href", "../images/replacement.png")
        else:
            (page.parent / image.get("href")).resolve().write_bytes(_png(200))
    elif operation != "unchanged":
        raise ValueError(operation)
    if operation not in {"bytes", "unchanged"}:
        page.write_bytes(ET.tostring(root, encoding="utf-8"))


def _observe(path: Path) -> dict:
    with zipfile.ZipFile(path) as package:
        slide = ET.fromstring(package.read("ppt/slides/slide1.xml"))
    ids = [node.get("id") for node in slide.findall(".//p:cNvPr", NS)]
    connector = slide.find(".//p:cxnSp", NS)
    return {
        "ids": ids,
        "picture_id": (slide.find(".//p:pic/p:nvPicPr/p:cNvPr", NS).get("id")
                       if slide.find(".//p:pic", NS) is not None else None),
        "connections": {tag: node.attrib for tag in ("stCxn", "endCxn")
                        if (node := connector.find(f"p:nvCxnSpPr/p:cNvCxnSpPr/a:{tag}", NS)) is not None},
        "geometry": ET.tostring(connector.find("p:spPr", NS), encoding="unicode"),
    }


def _split_endpoint(project: Path) -> None:
    """Keep valid SVG IDs while expanding the edited endpoint into a group."""
    _edit(project, "href")
    page = project / "authoring-svg-flat/slide_01.svg"
    root = ET.parse(page).getroot()
    endpoint = next(node for node in root.iter() if node.get("data-pptx-source-ref") == "slide:3")
    ET.SubElement(endpoint, f"{{{SVG}}}rect", {
        "id": "split_piece", "x": "510", "y": "100", "width": "30", "height": "30", "fill": "#654321",
    })
    page.write_bytes(ET.tostring(root, encoding="utf-8"))


def _with_ambiguous_endpoint_trace(overlay):
    """Supply a degraded ownership trace without mocking conversion or export."""
    def apply(source_slide, source_rels, slide_path, rels_path, slide_patch, trace):
        trace = copy.deepcopy(trace)
        extra = next(event for event in trace["events"]
                     if event.get("id") == "split_piece" and event.get("decision") == "native")
        # Both actual generated shapes belong to the same top-level endpoint
        # group. Only its input ownership mapping is made ambiguous.
        trace["events"].append({**extra, "id": "shape-3"})
        return overlay(source_slide, source_rels, slide_path, rels_path, slide_patch, trace)
    return apply


class RoundtripConnectorEndpointsTests(unittest.TestCase):
    def test_ambiguous_endpoint_detaches_with_stderr_and_report_warning(self) -> None:
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = _make_source(root, nested=nested)
                before = _observe(source)
                project = root / "workspace"
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    convert_pptx_to_svg(source, project, ConvertOptions(roundtrip=True, inheritance_mode="both"))
                    _split_endpoint(project)
                    output = root / "output.pptx"
                    overlay = _with_ambiguous_endpoint_trace(builder._apply_roundtrip_slide_overlay)
                    with patch.object(builder, "_apply_roundtrip_slide_overlay", side_effect=overlay):
                        result = export_main([str(project), "--roundtrip", "-o", str(output)])
                self.assertEqual(result, 0, stdout.getvalue() + stderr.getvalue())
                after = _observe(output)
                self.assertNotIn("endCxn", after["connections"])
                self.assertEqual(after["connections"]["stCxn"], before["connections"]["stCxn"])
                self.assertEqual(after["geometry"], before["geometry"])
                report = json.loads((project / "validation/output.report.json").read_text(encoding="utf-8"))
                warnings = report["source"]["authoring_roundtrip"]["documents"][0]["warnings"]
                self.assertEqual(len(warnings), 1)
                warning = warnings[0]
                self.assertEqual(warning["code"], "roundtrip-connector-attachment-detached")
                self.assertEqual(warning["connector_id"], "4")
                self.assertEqual(warning["endpoint"], "endCxn")
                self.assertEqual(warning["source_target_id"], "3")
                self.assertEqual(len(warning["candidate_ids"]), 2)
                self.assertIn(warning["message"], stderr.getvalue())
                self.assertIn("connector 4 endCxn endpoint 3", warning["message"])
                self.assertIn("Reconnect this end", warning["message"])

    def _case(self, operation: str, *, nested: bool = False) -> tuple[dict, dict]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = _make_source(root, nested=nested)
            before = _observe(source)
            project = root / "workspace"
            log = io.StringIO()
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                convert_pptx_to_svg(source, project, ConvertOptions(roundtrip=True, inheritance_mode="both"))
                _edit(project, operation)
                output = root / "output.pptx"
                result = export_main([str(project), "--roundtrip", "-o", str(output)])
            self.assertEqual(result, 0, log.getvalue())
            after = _observe(output)
            self.assertEqual(after["geometry"], before["geometry"])
            self.assertEqual(len(after["ids"]), len(set(after["ids"])))
            self.assertTrue(all(node["id"] in after["ids"] for node in after["connections"].values()))
            return before, after

    def test_deleted_endpoint_detaches_only_that_end(self) -> None:
        for operation, removed, retained in (("delete_start", "stCxn", "endCxn"),
                                             ("delete_end", "endCxn", "stCxn")):
            for nested in (False, True):
                with self.subTest(operation=operation, nested=nested):
                    before, after = self._case(operation, nested=nested)
                    self.assertNotIn(removed, after["connections"])
                    self.assertEqual(after["connections"][retained], before["connections"][retained])

    def test_replacement_picture_keeps_connection_to_the_live_picture(self) -> None:
        for nested in (False, True):
            with self.subTest(nested=nested):
                before, after = self._case("href", nested=nested)
                self.assertEqual(after["connections"]["endCxn"]["id"], after["picture_id"])
                self.assertEqual(after["connections"]["stCxn"], before["connections"]["stCxn"])

    def test_deleted_id_reused_by_addition_does_not_reattach(self) -> None:
        _, after = self._case("delete_reuse")
        self.assertIn("2", after["ids"])
        self.assertNotIn("stCxn", after["connections"])

    def test_generated_connections_are_renumbered_without_retargeting_source_connections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = _make_source(root, hidden_start=True)
            project = root / "workspace"
            log = io.StringIO()
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                convert_pptx_to_svg(source, project, ConvertOptions(roundtrip=True, inheritance_mode="both"))
                page = project / "authoring-svg-flat/slide_01.svg"
                svg = ET.parse(page).getroot()
                svg.append(ET.fromstring(
                    f'<rect xmlns="{SVG}" id="new_endpoint" x="600" y="400" width="100" height="100" '
                    'fill="#ABCDEF" data-pptx-shape-id="2" data-pptx-shape-scope="slide"/>'
                ))
                svg.append(ET.fromstring(
                    f'<line xmlns="{SVG}" id="new_connection" x1="700" y1="450" x2="800" y2="450" '
                    'stroke="#ABCDEF" stroke-width="2" data-pptx-object="connector" '
                    'data-pptx-prst="straightConnector1" data-pptx-frame="700 450 100 0" '
                    'data-pptx-start-shape-id="2" data-pptx-start-site="1"/>'
                ))
                page.write_bytes(ET.tostring(svg, encoding="utf-8"))
                output = root / "output.pptx"
                result = export_main([str(project), "--roundtrip", "-o", str(output)])
            self.assertEqual(result, 0, log.getvalue())
            with zipfile.ZipFile(output) as package:
                slide = ET.fromstring(package.read("ppt/slides/slide1.xml"))
            shapes = {node.find("./*/p:cNvPr", NS).get("name"): node
                      for node in slide.findall("p:cSld/p:spTree/*", NS)
                      if node.find("./*/p:cNvPr", NS) is not None}
            self.assertEqual(shapes["connection"].find(".//a:stCxn", NS).get("id"), "2")
            new_shape = next(node for node in slide.findall(".//p:sp", NS)
                             if node.find("./*/p:cNvPr", NS).get("name") != "start")
            new_id = new_shape.find("./*/p:cNvPr", NS).get("id")
            self.assertNotEqual(new_id, "2")
            new_connector = next(node for node in slide.findall(".//p:cxnSp", NS)
                                 if node.find("./*/p:cNvPr", NS).get("name") != "connection")
            self.assertEqual(new_connector.find(".//a:stCxn", NS).get("id"), new_id)

    def test_unchanged_and_image_byte_controls_keep_original_connections(self) -> None:
        for operation in ("unchanged", "bytes"):
            with self.subTest(operation=operation):
                before, after = self._case(operation)
                self.assertEqual(after, before)
