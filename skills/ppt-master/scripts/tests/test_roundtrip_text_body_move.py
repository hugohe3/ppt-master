#!/usr/bin/env python3
"""PPT Master - Round-trip Text Body Translation Regression Tests

Exercise native text retention through import, materialization, and conversion.

Usage:
    python3 -m unittest tests.test_roundtrip_text_body_move

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPTX/SVG converters.
"""

from __future__ import annotations

import base64
import io
import re
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import authoring_roundtrip
from authoring_roundtrip import materialize_flat_authoring_roundtrip
from pptx_shapes import svg_text_fingerprint
from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_to_pptx.drawingml.converter import SvgNativeConversionError, convert_svg_to_slide_shapes
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg


NS = {
    "s": "http://www.w3.org/2000/svg",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


def _normalized(element: ET.Element) -> str:
    return ET.canonicalize(ET.tostring(element, encoding="unicode"), rewrite_prefixes=True)


def _body(*, formula: bool, reversible: bool = False, multiline: bool = False) -> str:
    # System colors are valid native math but outside the reverse-import subset.
    color = '<a:srgbClr val="123456"/>' if reversible else '<a:sysClr val="windowText" lastClr="123456"/>'
    math = (
        '<a14:m><m:oMath><m:r><a:rPr><a:solidFill>'
        f'{color}'
        '</a:solidFill></a:rPr><m:t>x</m:t></m:r></m:oMath></a14:m>'
    ) if formula else ""
    second_line = '<a:p><a:r><a:rPr sz="1800"/><a:t>Second line</a:t></a:r></a:p>' if multiline else ""
    return (
        f'<p:txBody xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}" '
        f'xmlns:a14="{NS["a14"]}" xmlns:m="{NS["m"]}">'
        '<a:bodyPr wrap="square" lIns="19050" tIns="28575" rIns="38100" bIns="47625">'
        '<a:normAutofit fontScale="90000" lnSpcReduction="10000"/>'
        '</a:bodyPr><a:lstStyle/><a:p><a:pPr>'
        '<a:buAutoNum type="arabicPeriod" startAt="3"/></a:pPr>'
        '<a:r><a:rPr lang="fr-FR" sz="1800"/><a:t>Bonjour </a:t></a:r>'
        f'{math}{math}<a:endParaRPr lang="fr-FR" sz="1800"/>'
        f'</a:p>{second_line}</p:txBody>'
    )


class RoundtripTextBodyMoveTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "workspace"

    def _import(
        self, *, formula: bool = True, reversible: bool = False, multiline: bool = False, transform: str = "",
    ) -> None:
        svg = ET.fromstring(
            f'<svg xmlns="{NS["s"]}" width="960" height="540" viewBox="0 0 960 540">'
            '<g id="shape-7" data-pptx-object="shape" data-pptx-shape-id="7" '
            'data-pptx-shape-scope="slide" data-pptx-frame="80 100 500 120" '
            'data-pptx-prst="rect" data-pptx-semantic-object="shape">'
            '<path d="M80 100 H580 V220 H80 Z" fill="#FFFFFF" '
            'stroke="none" data-pptx-part="geometry"/>'
            '<text x="90" y="145" font-size="24" font-family="Arial" '
            'fill="#123456">Bonjour xx</text></g></svg>'
        )
        carrier = svg.find("s:g", NS)
        if transform:
            carrier.set("transform", transform)
        metadata = ET.SubElement(carrier, f'{{{NS["s"]}}}metadata', {
            "data-pptx-part": "txbody",
            "data-pptx-encoding": "base64",
            "data-pptx-text-sha256": svg_text_fingerprint(carrier),
        })
        body = _body(formula=formula, reversible=reversible, multiline=multiline)
        metadata.text = base64.b64encode(body.encode()).decode("ascii")
        svg_path = self.root / "slide.svg"
        svg_path.write_bytes(ET.tostring(svg))
        source = self.root / "source.pptx"
        log = io.StringIO()
        with redirect_stdout(log), redirect_stderr(log):
            success = create_pptx_with_native_svg(
                [svg_path], source, resource_root=self.root, pptx_structure="flat",
                use_compat_mode=False, transition=None, workers=1, verbose=False,
            )
            self.assertTrue(success, log.getvalue())
            convert_pptx_to_svg(
                source, self.workspace, ConvertOptions(inheritance_mode="both", roundtrip=True),
            )
        with zipfile.ZipFile(source) as archive:
            self.original = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        self.original = next(
            shape for shape in self.original.findall(".//p:sp", NS)
            if shape.find("p:nvSpPr/p:cNvPr", NS).get("id") == "7"
        )
        self.path = self.workspace / "authoring-svg-flat" / "slide_01.svg"
        self.svg = ET.parse(self.path).getroot()
        self.carrier = next(
            node for node in self.svg.iter() if node.get("data-pptx-source-ref") == "slide:7"
        )
        if formula and not reversible:
            self.assertFalse(any(node.get("data-pptx-inline-formula") for node in self.carrier.iter()))

    def _move_frame(self, index: int = 0, delta: float = 20) -> None:
        frame = self.carrier.get("data-pptx-frame").split()
        frame[index] = str(float(frame[index]) + delta)
        self.carrier.set("data-pptx-frame", " ".join(frame))

    def _move_coordinates(self, dx: float, dy: float) -> None:
        self._move_frame(0, dx)
        self._move_frame(1, dy)
        x, y, width, height = map(float, self.carrier.get("data-pptx-frame").split())
        self.carrier.find('*[@data-pptx-part="geometry"]').set(
            "d", f"M {x:g} {y:g} L {x + width:g} {y:g} L {x + width:g} {y + height:g} L {x:g} {y + height:g} Z",
        )
        for node in self.carrier.iter():
            if node.tag not in {f'{{{NS["s"]}}}text', f'{{{NS["s"]}}}tspan'}:
                continue
            for axis, delta in (("x", dx), ("y", dy)):
                if node.get(axis) is not None:
                    node.set(axis, " ".join(
                        f"{float(value) + delta:.12g}" for value in re.split(r"[\s,]+", node.get(axis).strip())
                    ))

    def _materialize(self):
        self.path.write_bytes(ET.tostring(self.svg))
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            materialized = materialize_flat_authoring_roundtrip(
                self.workspace, self.path.parent, self.workspace / "materialized",
            )
            self.materialized = ET.parse(materialized.svg_files[0]).getroot()
        self.warning_output = stderr.getvalue()
        self.warnings = materialized.report["documents"][0]["warnings"]
        return materialized.svg_files[0]

    def _convert(self) -> ET.Element:
        path = self._materialize()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            xml, *_ = convert_svg_to_slide_shapes(path, resource_root=self.workspace, text_flow="preserve")
        return ET.fromstring(xml)

    def _export(self) -> ET.Element:
        return next(
            shape for shape in self._convert().findall(".//p:sp", NS)
            if shape.find("p:nvSpPr/p:cNvPr", NS).get("id") == "7"
        )

    def _wrap_carrier(self, **attributes) -> None:
        parent = next(node for node in self.svg.iter() if self.carrier in list(node))
        index = list(parent).index(self.carrier)
        parent.remove(self.carrier)
        wrapper = ET.Element(f'{{{NS["s"]}}}g', attributes)
        wrapper.append(self.carrier)
        parent.insert(index, wrapper)

    def _assert_preserved(self, result: ET.Element, *, dx: int = 20, dy: int = 0) -> None:
        self.assertEqual(_normalized(result.find("p:txBody", NS)),
                         _normalized(self.original.find("p:txBody", NS)))
        before = self.original.find("p:spPr/a:xfrm", NS)
        after = result.find("p:spPr/a:xfrm", NS)
        self.assertEqual(after.attrib, before.attrib)
        self.assertEqual(after.find("a:ext", NS).attrib, before.find("a:ext", NS).attrib)
        for axis, delta in (("x", dx), ("y", dy)):
            self.assertEqual(int(after.find("a:off", NS).get(axis)),
                             int(before.find("a:off", NS).get(axis)) + delta * 9525)
        self.assertEqual(self.warnings, [])
        self.assertNotIn("native-formula-to-text", self.warning_output)

    def test_frame_translation_preserves_complete_txbody_and_math(self) -> None:
        self._import()
        self._move_frame()
        self._move_frame(1, -10)
        result = self._export()
        self.assertEqual(len(result.findall(".//a14:m", NS)), 2)
        self._assert_preserved(result, dy=-10)

    def test_coordinate_translation_preserves_complete_txbody_and_math(self) -> None:
        self._import(multiline=True)
        self._move_coordinates(20, -10)
        result = self._export()
        self.assertEqual(len(result.findall(".//a14:m", NS)), 2)
        self._assert_preserved(result, dy=-10)

    def test_coordinate_translation_includes_explicit_tspan_positions(self) -> None:
        self._import()
        parse_svg = authoring_roundtrip._parse_svg

        def with_run_positions(path):
            # Exercise equivalent imported projections with explicit run origins.
            root = parse_svg(path)
            for text in root.iter(f'{{{NS["s"]}}}text'):
                span = text.find("s:tspan", NS)
                if span is not None:
                    for axis in ("x", "y"):
                        if span.get(axis) is None:
                            span.set(axis, text.get(axis))
            return root

        self.svg = with_run_positions(self.path)
        self.carrier = next(node for node in self.svg.iter() if node.get("data-pptx-source-ref") == "slide:7")
        self._move_coordinates(20, -10)
        with patch("authoring_roundtrip._parse_svg", side_effect=with_run_positions):
            result = self._export()
        self._assert_preserved(result, dy=-10)

    def test_moving_only_one_line_does_not_restore_and_warns(self) -> None:
        self._import(multiline=True)
        self._move_coordinates(20, -10)
        line = next(node for node in self.carrier.iter() if node.text == "Second line")
        line.set("x", str(float(self.carrier.find(".//s:text", NS).get("x")) + 5))
        self._materialize()
        self.assertIsNone(self.materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))
        self.assertIn("reason=text-edited", self.warning_output)

    def test_object_translation_preserves_complete_txbody(self) -> None:
        self._import()
        self.carrier.set("transform", "translate(20 0)")
        self._assert_preserved(self._export())

    def test_ancestor_translation_preserves_complete_txbody(self) -> None:
        self._import()
        self._wrap_carrier(transform="translate(20 0)")
        self._assert_preserved(self._export())

    def test_translation_keeps_existing_rotation(self) -> None:
        self._import(transform="rotate(15 330 160)")
        self._wrap_carrier(transform="translate(20 0)")
        self._assert_preserved(self._export())

    def test_width_change_warns_and_does_not_restore(self) -> None:
        self._import()
        self._move_frame(2, 100)
        result = self._export()
        self.assertEqual(len(result.findall(".//a14:m", NS)), 0)
        self.assertIsNone(self.materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))
        self.assertEqual(len(self.warnings), 1)
        self.assertEqual(self.warnings[0]["code"], "native-formula-to-text")
        self.assertEqual(self.warnings[0]["output_page"], 1)
        self.assertEqual(self.warnings[0]["source_ref"], "slide:7")
        for value in ("page=1", "slide_01.svg", "object=shape-7", "native formulas will become plain text",
                      "reason=size/transform-changed"):
            self.assertIn(value, self.warning_output)

    def test_rotation_and_flip_warn_and_do_not_restore(self) -> None:
        for transform in ("rotate(15 330 160)", "translate(660 0) scale(-1 1)"):
            with self.subTest(transform=transform), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                self.workspace = self.root / "workspace"
                self._import()
                self.carrier.set("transform", transform)
                result = self._export()
                self.assertEqual(len(result.findall(".//a14:m", NS)), 0)
                self.assertEqual(len(self.warnings), 1)

    def test_scale_warns_and_does_not_restore_at_materialization(self) -> None:
        self._import()
        self._wrap_carrier(transform="scale(1.1 1)")
        self._materialize()
        self.assertIsNone(self.materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))
        self.assertEqual(len(self.warnings), 1)

    def test_edited_text_is_not_overwritten_after_move(self) -> None:
        self._import()
        self._move_frame()
        run = next(node for node in self.carrier.iter() if node.text and "Bonjour" in node.text)
        run.text = run.text.replace("Bonjour", "Bonsoir")
        result = self._export()
        text = "".join(node.text or "" for node in result.findall(".//a:t", NS))
        self.assertIn("Bonsoir", text)
        self.assertNotIn("Bonjour", text)
        self.assertEqual(len(result.findall(".//a14:m", NS)), 0)
        self.assertIn("reason=text-edited", self.warning_output)

    def test_text_edit_without_move_warns(self) -> None:
        self._import()
        run = next(node for node in self.carrier.iter() if node.text and "Bonjour" in node.text)
        run.text = run.text.replace("Bonjour", "Bonsoir")
        result = self._export()
        self.assertEqual(len(result.findall(".//a14:m", NS)), 0)
        self.assertIn("reason=text-edited", self.warning_output)

    def test_edited_style_is_not_overwritten_after_move(self) -> None:
        self._import()
        self._move_frame()
        self.carrier.find(".//s:text", NS).set("font-size", "32")
        result = self._export()
        self.assertIsNone(self.materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))
        self.assertIsNotNone(result.find('.//a:rPr[@sz="2400"]', NS))
        self.assertIn("reason=text-edited", self.warning_output)

    def test_local_text_translation_does_not_restore(self) -> None:
        self._import()
        self._move_frame()
        self.carrier.find(".//s:text", NS).set("transform", "translate(5 0)")
        self._export()
        self.assertIsNone(self.materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))

    def test_plain_text_translation_preserves_complete_txbody(self) -> None:
        self._import(formula=False)
        self._move_frame()
        self._assert_preserved(self._export())

    def test_plain_text_resize_has_no_formula_warning(self) -> None:
        self._import(formula=False)
        self._move_frame(2, 100)
        self._export()
        self.assertEqual(self.warnings, [])
        self.assertNotIn("native formulas will become plain text", self.warning_output)

    def test_native_markers_rebuild_after_resize_without_loss_warning(self) -> None:
        self._import(reversible=True)
        self.assertEqual(sum(bool(node.get("data-pptx-inline-formula")) for node in self.carrier.iter()), 2)
        self._move_frame(2, 100)
        result = self._convert()
        self.assertEqual(len(result.findall(".//a14:m", NS)), 2)
        self.assertEqual(self.warnings, [])

    def test_ancestor_opacity_edit_is_not_overwritten_after_move(self) -> None:
        self._import()
        self._wrap_carrier(transform="translate(20 0)", opacity="0.5")
        result = self._export()
        self.assertIsNone(self.materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))
        self.assertEqual(len(result.findall(".//a14:m", NS)), 0)

    def test_bad_payload_does_not_raise_during_loss_diagnosis(self) -> None:
        for payload in ("not base64!", base64.b64encode(b"<broken>").decode("ascii")):
            for edit in ("size", "text"):
                with self.subTest(payload=payload, edit=edit), tempfile.TemporaryDirectory() as directory:
                    self.root = Path(directory)
                    self.workspace = self.root / "workspace"
                    self._import()
                    if edit == "size":
                        self._move_frame(2, 100)
                    else:
                        self.carrier.find(".//s:text/s:tspan", NS).text = "Edited"
                    parse_svg = authoring_roundtrip._parse_svg
                    corrupted = []

                    def corrupt_payload(path):
                        root = parse_svg(path)
                        metadata = root.find('.//s:metadata[@data-pptx-part="txbody"]', NS)
                        if metadata is not None:
                            metadata.text = payload
                            corrupted.append(path)
                        return root

                    with patch("authoring_roundtrip._parse_svg", side_effect=corrupt_payload):
                        result = self._export()
                    self.assertTrue(corrupted)
                    self.assertEqual(len(result.findall(".//a14:m", NS)), 0)
                    self.assertEqual(self.warnings, [])

    def test_restored_bad_payload_keeps_converter_validation(self) -> None:
        self._import()
        self._move_frame()
        parse_svg = authoring_roundtrip._parse_svg
        corrupted = []

        def corrupt_payload(path):
            root = parse_svg(path)
            metadata = root.find('.//s:metadata[@data-pptx-part="txbody"]', NS)
            if metadata is not None:
                metadata.text = "not base64!"
                corrupted.append(path)
            return root

        with patch("authoring_roundtrip._parse_svg", side_effect=corrupt_payload):
            with self.assertRaisesRegex(SvgNativeConversionError, "Invalid txbody metadata"):
                self._export()
        self.assertTrue(corrupted)
