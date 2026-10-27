#!/usr/bin/env python3
"""
PPT Master - Text Overflow Import Regression Tests

Verify that native text overflow remains visible beyond short shape and table
cell frames, while explicit clipping retains the existing line truncation.

Usage:
    python3 -m unittest tests.test_text_overflow_import

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPT Master importer.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_to_svg.emu_units import Xfrm  # noqa: E402
from pptx_to_svg.ooxml_loader import OoxmlPackage  # noqa: E402
from pptx_to_svg.slide_to_svg import assemble_part_solo, assemble_slide  # noqa: E402
from pptx_to_svg.tbl_to_svg import convert_tbl  # noqa: E402
from pptx_to_svg.txbody_to_svg import convert_txbody, convert_vertical_txbody  # noqa: E402


A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
SVG = 'http://www.w3.org/2000/svg'
NS = {'a': A, 's': SVG}
LINES = ('First', 'Second', 'Third')


def _text_body(
    overflow: str | None,
    *,
    spacing_percent: int = 100000,
    paragraphs: bool = False,
    anchor: str = 't',
    top_inset_px: int = 0,
    bottom_inset_px: int = 0,
) -> ET.Element:
    runs = [
        '<a:r><a:rPr sz="2400"><a:latin typeface="Arial"/>'
        f'<a:ea typeface="Arial"/></a:rPr><a:t>{text}</a:t></a:r>'
        for text in LINES
    ]
    paragraph_properties = (
        f'<a:pPr><a:lnSpc><a:spcPct val="{spacing_percent}"/></a:lnSpc></a:pPr>'
    )
    if paragraphs:
        content = ''.join(f'<a:p>{paragraph_properties}{run}</a:p>' for run in runs)
    else:
        line_break = '<a:br><a:rPr sz="2400"><a:latin typeface="Arial"/></a:rPr></a:br>'
        content = f'<a:p>{paragraph_properties}{line_break.join(runs)}</a:p>'
    overflow_attribute = f' vertOverflow="{overflow}"' if overflow is not None else ''
    return ET.fromstring(
        f'<p:txBody xmlns:p="{P}" xmlns:a="{A}">'
        f'<a:bodyPr anchor="{anchor}" wrap="none" lIns="0" '
        f'tIns="{top_inset_px * 9525}" rIns="0" bIns="{bottom_inset_px * 9525}"'
        f'{overflow_attribute}/><a:lstStyle/>{content}</p:txBody>'
    )


def _svg_root(markup: str) -> ET.Element:
    return ET.fromstring(f'<svg xmlns="{SVG}">{markup}</svg>')


def _visible_text(root: ET.Element) -> str:
    return ''.join(''.join(text.itertext()) for text in root.findall('.//s:text', NS))


class TextOverflowImportTests(unittest.TestCase):
    def _import(self, body: ET.Element, *, height: float = 32) -> ET.Element:
        result = convert_txbody(body, Xfrm(x=80, y=100, w=600, h=height), None)
        return _svg_root(result.svg)

    def _assert_anchor_shift(
        self,
        mode: str | None,
        anchor: str,
        paragraphs: bool,
        expected_shift: float,
        *,
        height: float = 32,
        top_inset_px: int = 0,
        bottom_inset_px: int = 0,
    ) -> None:
        options = {
            'paragraphs': paragraphs,
            'top_inset_px': top_inset_px,
            'bottom_inset_px': bottom_inset_px,
        }
        top = self._import(_text_body(mode, **options), height=height)
        anchored = self._import(_text_body(mode, anchor=anchor, **options), height=height)
        self.assertEqual(_visible_text(anchored), 'FirstSecondThird')
        top_texts = top.findall('s:text', NS)
        anchored_texts = anchored.findall('s:text', NS)
        self.assertEqual(len(anchored_texts), len(top_texts))
        for original, shifted in zip(top_texts, anchored_texts):
            self.assertAlmostEqual(float(shifted.get('y')) - float(original.get('y')), expected_shift)
        self.assertEqual(
            [span.get('dy') for span in anchored.findall('.//s:tspan', NS)],
            [span.get('dy') for span in top.findall('.//s:tspan', NS)],
        )

    def test_default_and_explicit_overflow_keep_all_soft_break_lines(self) -> None:
        for mode in (None, 'overflow'):
            for percent, advance in ((100000, 38.4), (150000, 57.6)):
                with self.subTest(mode=mode, percent=percent):
                    imported = self._import(_text_body(mode, spacing_percent=percent))
                    self.assertEqual(_visible_text(imported), 'FirstSecondThird')
                    advances = [float(span.get('dy')) for span in imported.findall('.//s:tspan', NS)
                                if span.get('dy') is not None]
                    self.assertEqual(advances, [advance, advance])

    def test_default_and_explicit_overflow_keep_paragraphs_below_the_frame(self) -> None:
        for mode in (None, 'overflow'):
            for percent, advance in ((100000, 38.4), (150000, 57.6)):
                with self.subTest(mode=mode, percent=percent):
                    imported = self._import(
                        _text_body(mode, spacing_percent=percent, paragraphs=True),
                    )
                    texts = imported.findall('s:text', NS)
                    self.assertEqual([''.join(text.itertext()) for text in texts], list(LINES))
                    baselines = [float(text.get('y')) for text in texts]
                    self.assertAlmostEqual(baselines[1] - baselines[0], advance)
                    self.assertAlmostEqual(baselines[2] - baselines[1], advance)
                    self.assertGreater(baselines[-1], 132)

    def test_explicit_clip_and_ellipsis_keep_existing_line_truncation(self) -> None:
        for mode in ('clip', 'ellipsis'):
            for paragraphs in (False, True):
                for percent in (100000, 150000):
                    top = self._import(_text_body(
                        mode, spacing_percent=percent, paragraphs=paragraphs,
                    ))
                    top_baseline = float(top.find('s:text', NS).get('y'))
                    for anchor in ('t', 'ctr', 'b'):
                        with self.subTest(mode=mode, paragraphs=paragraphs, percent=percent, anchor=anchor):
                            imported = self._import(_text_body(
                                mode, spacing_percent=percent, paragraphs=paragraphs, anchor=anchor,
                            ))
                            # Ellipsis glyph synthesis is outside this importer fix.
                            self.assertEqual(_visible_text(imported), 'First')
                            texts = imported.findall('s:text', NS)
                            self.assertEqual(len(texts), 1)
                            self.assertEqual(float(texts[0].get('y')), top_baseline)

    def test_overflow_keeps_center_and_bottom_alignment(self) -> None:
        # Layout-model height: three 32px lines at 1.2 leading = 115.2px.
        # These shifts test anchoring, not absolute native-render measurements.
        for mode in (None, 'overflow'):
            for paragraphs in (False, True):
                for anchor, shift in (('ctr', -41.6), ('b', -83.2)):
                    with self.subTest(mode=mode, paragraphs=paragraphs, anchor=anchor):
                        self._assert_anchor_shift(mode, anchor, paragraphs, shift)

    def test_nonoverflow_center_and_bottom_alignment_stays_within_frame(self) -> None:
        for mode in (None, 'overflow'):
            for paragraphs in (False, True):
                for anchor, shift in (('ctr', 22.4), ('b', 44.8)):
                    with self.subTest(mode=mode, paragraphs=paragraphs, anchor=anchor):
                        self._assert_anchor_shift(mode, anchor, paragraphs, shift, height=160)

    def test_overflow_alignment_uses_inner_frame_after_insets(self) -> None:
        for mode in (None, 'overflow'):
            for paragraphs in (False, True):
                for anchor, shift in (('ctr', -51.6), ('b', -103.2)):
                    with self.subTest(mode=mode, paragraphs=paragraphs, anchor=anchor):
                        self._assert_anchor_shift(
                            mode, anchor, paragraphs, shift,
                            top_inset_px=8, bottom_inset_px=12,
                        )

    def test_table_cells_follow_their_text_bodys_overflow_mode(self) -> None:
        for mode, expected in ((None, 'FirstSecondThird'), ('overflow', 'FirstSecondThird'),
                               ('clip', 'First'), ('ellipsis', 'First')):
            with self.subTest(mode=mode):
                table = ET.fromstring(
                    f'<a:tbl xmlns:a="{A}"><a:tblPr/>'
                    '<a:tblGrid><a:gridCol w="5715000"/></a:tblGrid>'
                    '<a:tr h="304800"><a:tc>'
                    '<a:tcPr marL="0" marT="0" marR="0" marB="0" anchor="t"/>'
                    '</a:tc></a:tr></a:tbl>'
                )
                body = _text_body(mode)
                body.tag = f'{{{A}}}txBody'
                table.find('a:tr/a:tc', NS).insert(0, body)
                result = convert_tbl(table, Xfrm(x=80, y=100, w=600, h=32), None)
                self.assertEqual(_visible_text(_svg_root(result.svg)), expected)


class RunEmphasisImportTests(unittest.TestCase):
    def test_true_and_one_both_import_bold_and_italic(self) -> None:
        for value in ('1', 'true'):
            with self.subTest(value=value):
                body = ET.fromstring(
                    f'<p:txBody xmlns:p="{P}" xmlns:a="{A}"><a:bodyPr/><a:lstStyle/>'
                    f'<a:p><a:r><a:rPr b="{value}" i="{value}"/><a:t>Key</a:t></a:r></a:p>'
                    '</p:txBody>'
                )
                svg = convert_txbody(body, Xfrm(x=0, y=0, w=300, h=100), None).svg
                self.assertIn('font-weight="bold"', svg)
                self.assertIn('font-style="italic"', svg)


def _vertical_body(mode: str | None, overflow: str | None = None) -> ET.Element:
    mode_attr = f' vert="{mode}"' if mode is not None else ''
    overflow_attr = f' vertOverflow="{overflow}"' if overflow is not None else ''
    return ET.fromstring(
        f'<p:txBody xmlns:p="{P}" xmlns:a="{A}">'
        f'<a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0"{mode_attr}{overflow_attr}/>'
        '<a:lstStyle/><a:p><a:r><a:rPr sz="1800"><a:latin typeface="Arial"/>'
        '<a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>中文ABC测试</a:t></a:r></a:p>'
        '</p:txBody>'
    )


class VerticalTextFrameImportTests(unittest.TestCase):
    def _import_slide(self, body: ET.Element, frame: Xfrm, *, diagnostics=None) -> ET.Element:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'source.pptx'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('ppt/presentation.xml', (
                    f'<p:presentation xmlns:p="{P}" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    '<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
                    '<p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
                ))
                archive.writestr('ppt/_rels/presentation.xml.rels', (
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId1" '
                    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                    'Target="slides/slide1.xml"/></Relationships>'
                ))
                archive.writestr('ppt/slides/slide1.xml', (
                    f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp>'
                    '<p:nvSpPr><p:cNvPr id="2" name="Vertical"/><p:cNvSpPr txBox="1"/>'
                    '<p:nvPr/></p:nvSpPr><p:spPr>'
                    f'<a:xfrm rot="{int(frame.rot * 60000)}">'
                    f'<a:off x="{int(frame.x * 9525)}" y="{int(frame.y * 9525)}"/>'
                    f'<a:ext cx="{int(frame.w * 9525)}" cy="{int(frame.h * 9525)}"/>'
                    '</a:xfrm><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
                    f'{ET.tostring(body, encoding="unicode")}'
                    '</p:sp></p:spTree></p:cSld></p:sld>'
                ))
            with OoxmlPackage(path) as package:
                svg, _ = assemble_slide(
                    package, next(package.iter_slides()), None, diagnostics=diagnostics,
                )
        return ET.fromstring(svg)

    def test_vertical_root_groups_keep_positive_source_frame(self) -> None:
        for mode in ('vert', 'eaVert', 'wordArtVert', 'wordArtVertRtl'):
            with self.subTest(mode=mode):
                root = self._import_slide(_vertical_body(mode), Xfrm(x=120, y=180, w=80, h=320))
                group = root.find('s:g[@id="shape-2-text"]', NS)
                self.assertIsNotNone(group)
                self.assertEqual(group.get('data-pptx-frame'), '120 180 80 320')
                self.assertIsNone(group.get('transform'))
                self.assertEqual(_visible_text(group), '中文ABC测试')

    def test_auto_stacked_cjk_root_keeps_its_narrow_source_frame(self) -> None:
        body = _vertical_body(None)
        body.find('a:p/a:r/a:t', NS).text = '中文窄框测试'
        root = self._import_slide(body, Xfrm(x=120, y=180, w=20, h=320))
        group = root.find('s:g[@id="shape-2-text"]', NS)
        self.assertIsNotNone(group)
        self.assertEqual(group.get('data-pptx-frame'), '120 180 20 320')
        self.assertEqual(_visible_text(group), '中文窄框测试')

    def test_rotated_vertical_text_frame_matches_its_positioned_glyphs(self) -> None:
        root = self._import_slide(
            _vertical_body('eaVert'), Xfrm(x=120, y=180, w=320, h=80, rot=90),
        )
        group = root.find('s:g[@id="shape-2-text"]', NS)
        self.assertIsNotNone(group)
        self.assertEqual(group.get('data-pptx-frame'), '240 60 80 320')
        self.assertIsNone(group.get('transform'))

    def test_degenerate_slide_text_keeps_its_frame_and_reports_its_source_identity(self) -> None:
        for width, height in ((80, 0), (0, 0), (0, 320), (80, 320)):
            for mode in ('vert', 'eaVert', 'wordArtVert', 'wordArtVertRtl'):
                with self.subTest(width=width, height=height, mode=mode):
                    diagnostics = []
                    root = self._import_slide(
                        _vertical_body(mode), Xfrm(x=120, y=180, w=width, h=height),
                        diagnostics=diagnostics,
                    )
                    group = root.find('s:g[@id="shape-2-text"]', NS)
                    self.assertIsNotNone(group)
                    self.assertEqual(group.get('data-pptx-frame'), f'120 180 {width} {height}')
                    self.assertEqual(_visible_text(group), '中文ABC测试')
                    self.assertEqual(
                        [row.code for row in diagnostics],
                        ['degenerate-text-frame'] if width == 0 or height == 0 else [],
                    )
                    for diagnostic in diagnostics:
                        self.assertEqual(diagnostic.shape_id, '2')
                        self.assertEqual(diagnostic.part_path, 'ppt/slides/slide1.xml')

    def test_layout_guide_without_local_frame_is_not_diagnosed_as_a_source_loss(self) -> None:
        for explicit_frame in (False, True):
            with self.subTest(explicit_frame=explicit_frame), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'source.pptx'
                local_frame = (
                    '<a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm>'
                    if explicit_frame else ''
                )
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr('ppt/presentation.xml', (
                        f'<p:presentation xmlns:p="{P}">'
                        '<p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
                    ))
                    archive.writestr('ppt/slideLayouts/slideLayout1.xml', (
                        f'<p:sldLayout xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp>'
                        '<p:nvSpPr><p:cNvPr id="2" name="Vertical guide"/><p:cNvSpPr/>'
                        '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
                        f'<p:spPr>{local_frame}</p:spPr>{ET.tostring(_vertical_body("eaVert"), encoding="unicode")}'
                        '</p:sp></p:spTree></p:cSld></p:sldLayout>'
                    ))
                    archive.writestr('ppt/slideMasters/slideMaster1.xml', (
                        f'<p:sldMaster xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp>'
                        '<p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr/>'
                        '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
                        '<p:spPr><a:xfrm><a:off x="914400" y="914400"/>'
                        '<a:ext cx="7620000" cy="3810000"/></a:xfrm></p:spPr>'
                        '</p:sp></p:spTree></p:cSld></p:sldMaster>'
                    ))
                diagnostics = []
                with OoxmlPackage(path) as package:
                    assemble_part_solo(
                        package, package.load_part('ppt/slideLayouts/slideLayout1.xml'), None,
                        role='layout', parent_master=package.load_part('ppt/slideMasters/slideMaster1.xml'),
                        diagnostics=diagnostics,
                    )
                self.assertEqual(
                    [row.code for row in diagnostics], ['degenerate-text-frame'] if explicit_frame else [],
                )


class VerticalTextOverflowImportTests(unittest.TestCase):
    def test_default_and_explicit_overflow_keep_every_vertical_glyph(self) -> None:
        for mode in ('vert', 'eaVert', 'wordArtVert', 'wordArtVertRtl'):
            for overflow in (None, 'overflow'):
                for width, height in ((80, 30), (80, 0), (0, 0)):
                    with self.subTest(mode=mode, overflow=overflow, width=width, height=height):
                        result = convert_vertical_txbody(
                            _vertical_body(mode, overflow), Xfrm(x=120, y=180, w=width, h=height), None,
                        )
                        self.assertEqual(_visible_text(_svg_root(result.svg)), '中文ABC测试')
                        self.assertEqual(result.frame, (120, 180, width, height))

    def test_explicit_clip_and_ellipsis_retain_existing_vertical_truncation(self) -> None:
        for mode in ('vert', 'eaVert', 'wordArtVert', 'wordArtVertRtl'):
            for overflow in ('clip', 'ellipsis'):
                with self.subTest(mode=mode, overflow=overflow):
                    result = convert_vertical_txbody(
                        _vertical_body(mode, overflow), Xfrm(x=120, y=180, w=80, h=30), None,
                    )
                    self.assertEqual(_visible_text(_svg_root(result.svg)), '中')
