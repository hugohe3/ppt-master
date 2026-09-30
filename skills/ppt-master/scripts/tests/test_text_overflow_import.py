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
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_to_svg.emu_units import Xfrm  # noqa: E402
from pptx_to_svg.tbl_to_svg import convert_tbl  # noqa: E402
from pptx_to_svg.txbody_to_svg import convert_txbody  # noqa: E402


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
