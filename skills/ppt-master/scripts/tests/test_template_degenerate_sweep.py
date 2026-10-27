#!/usr/bin/env python3
"""Regressions for imported fixed geometry and placeholder source frames."""

from __future__ import annotations

import base64
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mirror_template_materialize as mirror
from compact_svg_coordinates import compact_svg_tree
from pptx_gradients import native_gradient_metadata
from svg_quality.checker import SVGQualityChecker
from svg_to_pptx.drawingml.converter import SvgNativeConversionError, convert_svg_to_slide_shapes
from template_import.manifest import extract_placeholders

SVG = "http://www.w3.org/2000/svg"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}


def _document(body: str = "") -> ET.Element:
    return ET.fromstring(f'<svg xmlns="{SVG}" viewBox="0 0 960 720">{body}</svg>')


def _compose(
    content: str, scope: str = "slide", plans: list | None = None,
    warnings: list[str] | None = None,
) -> ET.Element:
    empty = _document()
    master = {"key": "m", "name": "Master", "placeholders": []}
    layout = {"key": "l", "name": "Layout", "showMasterShapes": True, "placeholders": []}
    return mirror._compose_template(
        native={"slideSize": {"width_px": 960, "height_px": 720}},
        master=master, layout=layout,
        master_root=_document(content) if scope == "master" else empty,
        layout_root=_document(content) if scope == "layout" else empty,
        slide={"index": 1, "showInheritedShapes": True},
        slide_root=_document(content) if scope == "slide" else empty,
        slot_plans=plans or [],
        warnings=warnings,
    )


def _source_placeholder(width_emu: int) -> dict:
    source = ET.fromstring(
        f'<p:sldLayout xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp>'
        '<p:nvSpPr><p:cNvPr id="2" name="Body"/><p:cNvSpPr/><p:nvPr>'
        '<p:ph type="body" idx="42"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm>'
        f'<a:off x="1143000" y="1714500"/><a:ext cx="{width_emu}" cy="952500"/>'
        '</a:xfrm></p:spPr></p:sp></p:spTree></p:cSld></p:sldLayout>'
    )
    return extract_placeholders(source)[0]


class TemplateDegenerateSweepTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def _export(self, root: ET.Element) -> ET.Element:
        path = self.root / "source.svg"
        ET.ElementTree(root).write(path, encoding="utf-8")
        xml, *_ = convert_svg_to_slide_shapes(path, resource_root=self.root)
        return ET.fromstring(xml)

    def test_fixed_custom_shapes_keep_kind_payload_and_zero_extent(self) -> None:
        for scope in ("master", "layout"):
            for width, height in ((300, 0), (0, 100)):
                for count in (1, 2):
                    with self.subTest(scope=scope, frame=(width, height), paths=count):
                        custom = ET.fromstring(
                            f'<a:custGeom xmlns:a="{A}"><a:avLst/><a:gdLst/><a:ahLst/>'
                            '<a:cxnLst/><a:rect l="l" t="t" r="r" b="b"/><a:pathLst>'
                            + '<a:path w="300" h="100" fill="none"><a:moveTo><a:pt x="0" y="0"/>'
                            '</a:moveTo><a:lnTo><a:pt x="300" y="100"/></a:lnTo></a:path>' * count
                            + '</a:pathLst></a:custGeom>'
                        )
                        payload = base64.b64encode(ET.tostring(custom)).decode("ascii")
                        path = f"M 120 180 L {120 + width} {180 + height}"
                        digest = hashlib.sha256(path.encode()).hexdigest()
                        page = _compose(
                            '<g id="source" data-pptx-object="shape" data-pptx-geometry-kind="custom" '
                            f'data-pptx-frame="120 180 {width} {height}"><path d="{path}" '
                            f'data-pptx-custgeom="{payload}" data-pptx-geometry-sha256="{digest}" '
                            'stroke="#3060C0" stroke-width="4" fill="none"/></g>', scope,
                        )
                        geometry = next(element for element in page if element.tag == f"{{{SVG}}}path")
                        self.assertEqual(geometry.get("data-pptx-geometry-kind"), "custom")
                        result = {"errors": []}
                        SVGQualityChecker(template_mode=True)._check_preset_geometry_metadata(page, result)
                        self.assertEqual(result["errors"], [])
                        exported = self._export(page)
                        self.assertEqual(
                            ET.tostring(exported.find(".//a:custGeom", NS)).strip(), ET.tostring(custom),
                        )
                        self.assertEqual(exported.find(".//p:sp/p:spPr/a:xfrm/a:ext", NS).attrib, {
                            "cx": str(width * 9525), "cy": str(height * 9525),
                        })

    def test_fixed_custom_both_zero_stays_rejected(self) -> None:
        page = _compose(
            '<g id="source" data-pptx-object="shape" data-pptx-geometry-kind="custom" '
            'data-pptx-frame="120 180 0 0"><path d="M 120 180 L 120 180" '
            'stroke="#3060C0" fill="none"/></g>', "master",
        )
        with self.assertRaisesRegex(SvgNativeConversionError, "width and height must be positive"):
            self._export(page)

    def test_layout_native_frame_precedes_inherited_fallback(self) -> None:
        placeholder = _source_placeholder(2857500)
        master_placeholder = {"shapeId": "7", "type": "body", "idx": "42"}
        plans = mirror._slot_plans(
            {"key": "l", "placeholders": [placeholder]}, _document(), [], {},
            {"placeholders": [master_placeholder]},
            _document('<g data-pptx-source-ref="master:7" data-pptx-frame="48 168 864 475"/>'),
        )
        self.assertEqual(plans[0].bounds, (120, 180, 300, 100))
        master_guide = ET.fromstring(
            f'<g xmlns="{SVG}" data-pptx-frame="48 168 864 475">'
            '<text x="58" y="195" font-size="24">Master sample</text></g>'
        )
        carrier = mirror._blank_text_carrier(plans[0], None, master_guide)
        self.assertEqual(carrier.get("data-pptx-frame"), "120 180 300 100")
        self.assertIsNone(carrier.text)

    def test_single_emu_placeholder_keeps_positive_source_extent(self) -> None:
        placeholder = _source_placeholder(1)
        plans = mirror._slot_plans(
            {"key": "l", "placeholders": [placeholder]}, _document(), [], {},
            {"placeholders": []}, _document(),
        )
        self.assertEqual(round(plans[0].bounds[2] * 9525), 1)
        wrapper, _extras = mirror._slot_wrapper(
            plans[0], None, layout_guide=None, master_guide=None,
        )
        page = _document()
        page.append(wrapper)
        compact_svg_tree(page, compact_native_frames=False)
        bounds = tuple(float(value) for value in wrapper.get("data-pptx-bounds").split())
        self.assertEqual(round(bounds[2] * 9525), 1)
        text = wrapper.find(f"{{{SVG}}}text")
        self.assertEqual(round(float(text.get("data-pptx-frame").split()[2]) * 9525), 1)
        result = {"errors": []}
        SVGQualityChecker(template_mode=True)._check_preset_geometry_metadata(page, result)
        self.assertEqual(result["errors"], [])
        authored = _document('<g data-pptx-bounds="120 180 0.00010499 100"/>')
        compact_svg_tree(authored)
        self.assertEqual(authored[0].get("data-pptx-bounds"), "120 180 0 100")

    def test_nonpositive_and_missing_placeholder_frames_still_fail(self) -> None:
        for geometry in (
            None,
            {"x": 120, "y": 180, "width": 0, "height": 100},
            {"x": 120, "y": 180, "width": 0, "height": 0},
            {"x": 120, "y": 180, "width": -1, "height": 100},
        ):
            with self.subTest(geometry=geometry), self.assertRaisesRegex(
                mirror.MirrorMaterializationError, "no positive deterministic bounds",
            ):
                mirror._slot_plans(
                    {"key": "l", "placeholders": [{"shapeId": "2", "geometry": geometry}]},
                    _document(), [], {}, {"placeholders": []}, _document(),
                )

    def test_nonempty_placeholder_recovers_from_slot_bounds(self) -> None:
        plan = mirror.SlotPlan("slot", "body", "body", 42, "2", (120, 180, 300, 100))
        for frame in ("120 180 300 0", "120 180 0 100", "120 180 0 0"):
            with self.subTest(frame=frame):
                source = ET.fromstring(
                    f'<g xmlns="{SVG}" data-pptx-frame="{frame}">'
                    '<text x="120" y="195" font-size="16">Visible source text</text></g>'
                )
                wrapper, _extras = mirror._slot_wrapper(
                    plan, source, layout_guide=None, master_guide=None,
                )
                self.assertIsNone(wrapper[0].get("data-pptx-frame"))
                self.assertEqual(wrapper.get("data-pptx-bounds"), "120 180 300 100")
                self.assertEqual("".join(wrapper[0].itertext()), "Visible source text")
                page = _document()
                page.append(wrapper)
                result = {"errors": []}
                SVGQualityChecker(template_mode=True)._check_preset_geometry_metadata(page, result)
                self.assertEqual(result["errors"], [])
                exported = self._export(page)
                self.assertIn("Visible source text", [node.text for node in exported.findall(".//a:t", NS)])
                blank = mirror._blank_text_carrier(plan, source, None)
                self.assertEqual(blank.get("data-pptx-frame"), "120 180 300 100")
                self.assertFalse("".join(blank.itertext()))

    def test_gradient_source_bounds_use_resolved_document_definition(self) -> None:
        for alpha in (0, 1):
            with self.subTest(alpha=alpha):
                gradient = ET.fromstring(
                    f'<linearGradient xmlns="{SVG}" id="stroke" gradientUnits="userSpaceOnUse" '
                    'x1="120" y1="180" x2="420" y2="180">'
                    f'<stop offset="0" stop-color="#3060C0" stop-opacity="{alpha}"/>'
                    f'<stop offset="1" stop-color="#103050" stop-opacity="{alpha}"/></linearGradient>'
                )
                native = ET.fromstring(
                    f'<a:gradFill xmlns:a="{A}"><a:gsLst><a:gs pos="0"><a:srgbClr val="3060C0">'
                    f'<a:alpha val="{alpha * 100000}"/></a:srgbClr></a:gs><a:gs pos="100000">'
                    f'<a:srgbClr val="103050"><a:alpha val="{alpha * 100000}"/></a:srgbClr></a:gs>'
                    '</a:gsLst><a:lin ang="0" scaled="1"/></a:gradFill>'
                )
                gradient.attrib.update(native_gradient_metadata(native, gradient))
                content = (
                    '<defs>' + ET.tostring(gradient, encoding="unicode") + '</defs>'
                    '<g id="source" data-pptx-object="shape" data-pptx-prst="rect" '
                    'data-pptx-semantic-object="shape" data-pptx-frame="120 180 300 0">'
                    '<path data-pptx-part="geometry" d="M 120 180 L 420 180" '
                    'stroke="url(#stroke)" stroke-width="4" fill="none"/></g>'
                )
                if alpha == 0:
                    with self.assertRaisesRegex(mirror.MirrorMaterializationError, "no positive source frame"):
                        _compose(content)
                else:
                    page = _compose(content)
                    source = next(element for element in page if element.get("id") == "source")
                    self.assertEqual(source.get("data-pptx-bounds"), "120 178 300 4")
                    result = {"errors": []}
                    SVGQualityChecker(template_mode=True)._check_preset_geometry_metadata(page, result)
                    self.assertEqual(result["errors"], [])
                    exported = self._export(page)
                    self.assertEqual(exported.find(".//p:sp/p:spPr/a:xfrm/a:ext", NS).get("cy"), "0")

    def test_authored_gradient_does_not_grant_source_zero_axis_exception(self) -> None:
        with self.assertRaisesRegex(mirror.MirrorMaterializationError, "no positive source frame"):
            _compose(
                '<defs><linearGradient id="stroke"><stop offset="0" stop-color="#3060C0"/>'
                '<stop offset="1" stop-color="#103050"/></linearGradient></defs>'
                '<g id="source" data-pptx-object="shape" data-pptx-prst="rect" '
                'data-pptx-frame="120 180 300 0"><path d="M 120 180 L 420 180" '
                'stroke="url(#stroke)" stroke-width="4" fill="none"/></g>'
            )

    def test_invisible_degenerate_roots_are_omitted_with_context_in_all_layers(self) -> None:
        for scope in ("slide", "master", "layout"):
            for frame in ("", ' data-pptx-frame="120 180 640 0"', ' data-pptx-frame="120 180 0 0"'):
                with self.subTest(scope=scope, frame=frame):
                    warnings = []
                    page = _compose(
                        f'<g id="invisible-rule" data-pptx-object="group"{frame}>'
                        '<g data-pptx-object="connector"><path d="M 120 180 L 420 180" '
                        'fill="none" stroke="none"/></g></g>', scope, warnings=warnings,
                    )
                    self.assertFalse(any(element.get("id") == "invisible-rule" for element in page.iter()))
                    self.assertEqual(len(warnings), 1)
                    self.assertIn("Slide 1", warnings[0])
                    self.assertIn("invisible-rule", warnings[0])
                    self.assertIn("omitted invisible content", warnings[0])
                    if scope != "slide":
                        self.assertIn(scope.title(), warnings[0])
                    self.assertIsNone(self._export(page).find(".//p:sp", NS))

    def test_invisible_positive_slide_frame_is_retained(self) -> None:
        warnings = []
        page = _compose(
            '<g id="outline" data-pptx-frame="120 180 300 100">'
            '<path d="M 120 180 L 420 180" fill="none" stroke="none"/></g>', warnings=warnings,
        )
        self.assertEqual(next(node for node in page if node.get("id") == "outline").get(
            "data-pptx-bounds"), "120 180 300 100")
        self.assertEqual(warnings, [])

    def test_visible_unbounded_source_content_is_never_omitted(self) -> None:
        for frame in ("", ' data-pptx-frame="120 180 0 0"'):
            for content in (
                '<path d="M 120 180 L 420 180" stroke="#123456" fill="none"/>',
                '<text x="120" y="180">Visible text</text>',
                '<image x="120" y="180" width="300" height="100" href="image.png"/>',
            ):
                with self.subTest(frame=frame, content=content):
                    warnings = []
                    with self.assertRaisesRegex(mirror.MirrorMaterializationError, "no positive source frame"):
                        _compose(f'<g id="visible"{frame}>{content}</g>', warnings=warnings)
                    self.assertEqual(warnings, [])

    def test_omission_predicate_preserves_inherited_strokes_and_uncertain_images(self) -> None:
        for content in (
            '<g stroke="#123456"><path d="M 120 180 L 420 180" fill="none"/></g>',
            '<g><rect x="120" y="180" width="300" height="0" fill="none" stroke="#123456"/></g>',
            '<g><image x="120" y="180" width="0" height="0" href="image.png"/></g>',
            '<g visibility="hidden"><text visibility="visible">Visible text</text></g>',
            '<g fill="none"><path d="M 0 0 L 20 0 L 20 20 Z" style="fill:#ff0000"/></g>',
            '<g style="visibility:hidden"><text visibility="visible">Visible text</text></g>',
            '<g opacity="0" style="opacity:1"><text>Visible text</text></g>',
        ):
            with self.subTest(content=content):
                self.assertFalse(mirror._invisible_degenerate_source(ET.fromstring(content)))
        warnings = []
        page = _compose(
            '<g id="rule" data-pptx-object="connector" data-pptx-prst="straightConnector1" '
            'data-pptx-frame="120 180 300 0" stroke="#123456">'
            '<path d="M 120 180 L 420 180" fill="none"/></g>', warnings=warnings,
        )
        self.assertEqual(next(node for node in page if node.get("id") == "rule").get(
            "data-pptx-frame"), "120 180 300 0")
        self.assertEqual(warnings, [])
