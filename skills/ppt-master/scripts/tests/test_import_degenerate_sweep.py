"""Regress theme line inheritance and diagnosed degenerate source objects."""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_to_svg.converter import convert_pptx_to_svg


A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVG = "http://www.w3.org/2000/svg"
NS = {"a": A, "p": P, "s": SVG}
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aG1cAAAAASUVORK5CYII="
)


def _frame(width: int = 300, height: int = 100, *, graphic: bool = False) -> str:
    prefix = "p" if graphic else "a"
    return (
        f'<{prefix}:xfrm><a:off x="952500" y="952500"/>'
        f'<a:ext cx="{width * 9525}" cy="{height * 9525}"/></{prefix}:xfrm>'
    )


def _shape(height: int, local_line: str = "") -> str:
    return (
        '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Source"/>'
        '<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
        + _frame(height=height)
        + '<a:prstGeom prst="rect"/><a:noFill/>' + local_line
        + '</p:spPr><p:style><a:lnRef idx="1"><a:srgbClr val="123456"/>'
        '</a:lnRef></p:style></p:sp>'
    )


def _picture(fill: str, height: int = 100) -> str:
    return (
        '<p:pic><p:nvPicPr><p:cNvPr id="2" name="Picture"/>'
        '<p:cNvPicPr/><p:nvPr/></p:nvPicPr>' + fill
        + '<p:spPr>' + _frame(height=height)
        + '<a:prstGeom prst="rect"/></p:spPr></p:pic>'
    )


def _graphic(content: str, *, height: int = 100, kind: str = "table") -> str:
    uri = (
        "http://schemas.openxmlformats.org/presentationml/2006/ole"
        if kind == "ole" else f"http://schemas.openxmlformats.org/drawingml/2006/{kind}"
    )
    return (
        '<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="2" name="Graphic"/>'
        '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
        + _frame(height=height, graphic=True)
        + f'<a:graphic><a:graphicData uri="{uri}">{content}'
        '</a:graphicData></a:graphic></p:graphicFrame>'
    )


def _table(*, grid: str = '<a:gridCol w="2857500"/>', extra_cell: bool = False) -> str:
    cell = (
        '<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p>'
        '<a:r><a:rPr sz="1200"/><a:t>Kept</a:t></a:r>'
        '</a:p></a:txBody><a:tcPr/></a:tc>'
    )
    cells = cell + (cell.replace("Kept", "Outside grid") if extra_cell else "")
    return f'<a:tbl><a:tblPr/><a:tblGrid>{grid}</a:tblGrid><a:tr h="952500">{cells}</a:tr></a:tbl>'


class ImportDegenerateSweepTests(unittest.TestCase):
    def _import(
        self, content: str, *, theme_line: str | None = None, layout_content: str = "",
    ) -> tuple[ET.Element, dict]:
        def relationships(items: list[tuple[str, str, str]]) -> str:
            return (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + ''.join(f'<Relationship Id="{key}" Type="{R}/{kind}" Target="{target}"/>'
                          for key, kind, target in items)
                + '</Relationships>'
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pptx"
            with zipfile.ZipFile(source, "w") as package:
                package.writestr("ppt/presentation.xml", (
                    f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>'
                    '<p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
                    '<p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
                ))
                package.writestr("ppt/_rels/presentation.xml.rels", relationships([
                    ("rId1", "slide", "slides/slide1.xml"),
                ]))
                package.writestr("ppt/slides/slide1.xml", (
                    f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}">'
                    f'<p:cSld><p:spTree>{content}</p:spTree></p:cSld></p:sld>'
                ))
                package.writestr("ppt/slides/_rels/slide1.xml.rels", relationships([
                    ("rIdLayout", "slideLayout", "../slideLayouts/slideLayout1.xml"),
                    ("rIdImage", "image", "../media/source.png"),
                ]))
                package.writestr("ppt/media/source.png", PNG)
                package.writestr("ppt/slideLayouts/slideLayout1.xml", (
                    f'<p:sldLayout xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>'
                    f'{layout_content}</p:spTree></p:cSld></p:sldLayout>'
                ))
                package.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", relationships([
                    ("rIdMaster", "slideMaster", "../slideMasters/slideMaster1.xml"),
                ]))
                package.writestr("ppt/slideMasters/slideMaster1.xml", (
                    f'<p:sldMaster xmlns:p="{P}"><p:cSld><p:spTree/></p:cSld>'
                    '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
                    'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
                    'accent6="accent6" hlink="hlink" folHlink="folHlink"/></p:sldMaster>'
                ))
                if theme_line is not None:
                    package.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", relationships([
                        ("rIdTheme", "theme", "../theme/theme1.xml"),
                    ]))
                    colors = ''.join(
                        f'<a:{name}><a:srgbClr val="123456"/></a:{name}>'
                        for name in ('dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2',
                                     'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink')
                    )
                    package.writestr("ppt/theme/theme1.xml", (
                        f'<a:theme xmlns:a="{A}"><a:themeElements><a:clrScheme name="Test">'
                        f'{colors}</a:clrScheme><a:fmtScheme><a:lnStyleLst>{theme_line}'
                        '</a:lnStyleLst></a:fmtScheme></a:themeElements></a:theme>'
                    ))
            result = convert_pptx_to_svg(source, root / "output")
            report = json.loads((root / "output/validation/conversion-report.json").read_text())
            return ET.fromstring(result.slides[0].svg), report

    def _warning(self, report: dict, code: str) -> dict:
        found = [item for item in report["diagnostics"] if item["code"] == code]
        self.assertEqual(len(found), 1, report)
        self.assertEqual(found[0]["shape_id"], "2")
        self.assertEqual(found[0]["part_path"], "ppt/slides/slide1.xml")
        return found[0]

    def test_theme_line_paint_and_width_are_resolved_for_positive_and_zero_axes(self) -> None:
        for height in (100, 0):
            with self.subTest(height=height):
                svg, _ = self._import(_shape(height), theme_line=(
                    '<a:ln w="76200"><a:solidFill><a:schemeClr val="phClr"/>'
                    '</a:solidFill><a:prstDash val="dash"/></a:ln>'
                ))
                path = svg.find('.//s:path', NS)
                self.assertEqual(path.get("stroke"), "#123456")
                self.assertEqual(path.get("stroke-width"), "8")
                self.assertEqual(path.get("stroke-dasharray"), "4 4")
                self.assertEqual(path.get("data-pptx-frame"), f"100 100 300 {height}")

    def test_theme_no_fill_does_not_invent_an_outline(self) -> None:
        for height in (100, 0):
            with self.subTest(height=height):
                svg, report = self._import(_shape(height), theme_line='<a:ln w="76200"><a:noFill/></a:ln>')
                path = svg.find('.//s:path', NS)
                if height:
                    self.assertEqual(path.get("stroke"), "none")
                else:
                    self.assertIsNone(path)
                self.assertEqual(report["diagnostics"], [])

    def test_local_paint_overrides_theme_transparency_without_inheriting_its_alpha(self) -> None:
        local = '<a:ln w="19050"><a:solidFill><a:srgbClr val="ABCDEF"/></a:solidFill></a:ln>'
        svg, _ = self._import(_shape(100, local), theme_line=(
            '<a:ln w="76200"><a:solidFill><a:schemeClr val="phClr"><a:alpha val="0"/>'
            '</a:schemeClr></a:solidFill></a:ln>'
        ))
        path = svg.find('.//s:path', NS)
        self.assertEqual(path.get("stroke"), "#ABCDEF")
        self.assertEqual(path.get("stroke-width"), "2")
        self.assertIsNone(path.get("stroke-opacity"))

    def test_theme_gradient_stops_keep_placeholder_color(self) -> None:
        svg, _ = self._import(_shape(0), theme_line=(
            '<a:ln w="76200"><a:gradFill><a:gsLst>'
            '<a:gs pos="0"><a:schemeClr val="phClr"/></a:gs>'
            '<a:gs pos="100000"><a:srgbClr val="FFFFFF"/></a:gs>'
            '</a:gsLst><a:lin ang="0" scaled="1"/></a:gradFill></a:ln>'
        ))
        path = svg.find('.//s:path', NS)
        self.assertTrue(path.get("stroke").startswith("url(#"))
        gradient = svg.find('.//s:linearGradient', NS)
        self.assertEqual(gradient.get("gradientUnits"), "userSpaceOnUse")
        self.assertEqual([stop.get("stop-color") for stop in gradient], ["#123456", "#FFFFFF"])

    def test_inherited_cap_and_local_override_keep_source_line_ends(self) -> None:
        theme = '<a:ln w="9525" cap="flat"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
        for cap in (None, "flat", "rnd"):
            with self.subTest(cap=cap):
                attributes = f' cap="{cap}"' if cap else ''
                local = (
                    f'<a:ln w="19050"{attributes}><a:solidFill>'
                    '<a:srgbClr val="ABCDEF"/></a:solidFill></a:ln>'
                )
                svg, _ = self._import(_shape(100, local), theme_line=theme)
                self.assertEqual(svg.find('.//s:path', NS).get("stroke-linecap"),
                                 {None: "butt", "flat": "butt", "rnd": "round"}[cap])

    def test_missing_picture_sources_report_omission(self) -> None:
        for fill in ('', '<p:blipFill/>', '<p:blipFill><a:blip/></p:blipFill>'):
            with self.subTest(fill=fill):
                svg, report = self._import(_picture(fill))
                self.assertIsNone(svg.find('.//s:image', NS))
                self._warning(report, "picture-omitted")

    def test_nonpositive_picture_keeps_source_frame_and_reports_it(self) -> None:
        svg, report = self._import(_picture(
            '<p:blipFill><a:blip r:embed="rIdImage"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>',
            height=0,
        ))
        image = svg.find('.//s:image', NS)
        self.assertEqual(image.get("height"), "0")
        self.assertEqual(image.get("width"), "300")
        self._warning(report, "picture-degenerate-frame")

    def test_invalid_picture_crop_reports_the_existing_full_image_fallback(self) -> None:
        for crop in ("100000", "150000", "nan", "invalid"):
            with self.subTest(crop=crop):
                svg, report = self._import(_picture(
                    '<p:blipFill><a:blip r:embed="rIdImage"/>'
                    f'<a:srcRect l="{crop}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>',
                ))
                self.assertIsNotNone(svg.find('.//s:image', NS))
                self._warning(report, "picture-crop-omitted")

    def test_unrecoverable_table_grid_and_truncated_cells_are_diagnosed(self) -> None:
        for table, code in (
            (_table(grid=""), "table-geometry-omitted"),
            (_table(extra_cell=True), "table-geometry-unsupported"),
            (_table(grid='<a:gridCol w="0"/>'), "table-geometry-unsupported"),
            ('<a:tbl><a:tblGrid><a:gridCol w="2857500"/></a:tblGrid></a:tbl>', "table-geometry-omitted"),
        ):
            with self.subTest(table=table):
                _, report = self._import(_graphic(table))
                self._warning(report, code)

    def test_nonpositive_graphic_frames_report_without_inventing_dimensions(self) -> None:
        for kind, content in (("table", _table()), ("chart", ""), ("ole", "")):
            with self.subTest(kind=kind):
                svg, report = self._import(_graphic(content, height=0, kind=kind))
                self._warning(report, "graphic-degenerate-frame")
                group = svg.find('s:g', NS)
                self.assertEqual(group.get("data-pptx-frame"), "100 100 300 0")

    def test_unresolved_theme_line_does_not_invent_a_stroke(self) -> None:
        svg, report = self._import(_shape(100))
        self._warning(report, "theme-line-reference-omitted")
        self.assertIsNone(svg.find('.//s:path', NS).get("stroke"))

    def test_missing_graphic_preview_is_reported(self) -> None:
        _, report = self._import(_graphic("", kind="ole"))
        self._warning(report, "graphic-preview-unavailable")

    def test_nonpositive_formula_frame_preserves_content_and_reports_it(self) -> None:
        math = (
            '<a14:m xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" '
            'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
            '<m:oMathPara><m:oMath><m:r><a:rPr sz="1800">'
            '<a:solidFill><a:srgbClr val="123456"/></a:solidFill></a:rPr>'
            '<m:t>x</m:t></m:r></m:oMath></m:oMathPara></a14:m>'
        )
        shape = (
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Formula"/><p:cNvSpPr/><p:nvPr/>'
            '</p:nvSpPr><p:spPr>' + _frame(height=0)
            + '<a:prstGeom prst="rect"/><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p>' + math + '</a:p></p:txBody></p:sp>'
        )
        svg, report = self._import(shape)
        self._warning(report, "formula-degenerate-frame")
        group = svg.find('s:g', NS)
        self.assertEqual(group.get("data-pptx-frame"), "100 100 300 0")
        self.assertEqual(group.get("data-pptx-replace-with"), "formula")
        self.assertIn("x", ''.join(group.itertext()))

    def test_placeholder_inherits_omitted_and_explicit_zero_extents_with_diagnostic(self) -> None:
        shape = (
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Placeholder"/><p:cNvSpPr/>'
            '<p:nvPr><p:ph type="body" idx="42"/></p:nvPr></p:nvSpPr><p:spPr>'
            + _frame() + '<a:prstGeom prst="rect"/><a:noFill/></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Text</a:t></a:r></a:p>'
            '</p:txBody></p:sp>'
        )
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                extent = '<a:ext cx="2857500" cy="952500"/>'
                source = shape.replace(extent, '<a:ext cx="0" cy="0"/>' if explicit else '')
                svg, report = self._import(source, layout_content=shape)
                group = svg.find('s:g', NS)
                self.assertEqual(group.get("data-pptx-frame"), "100 100 300 100")
                self.assertTrue(svg.findall('.//s:text', NS))
                if explicit:
                    warning = self._warning(report, "degenerate-text-frame")
                    self.assertIn("100 100 0 0", warning["message"])
                else:
                    self.assertFalse(any(item["code"] == "degenerate-text-frame"
                                         for item in report["diagnostics"]))
