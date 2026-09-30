#!/usr/bin/env python3
"""
PPT Master - Text Baseline Round-trip Regression Tests

Exercise the public DrawingML importer and SVG exporter with self-contained
text fixtures, including edited native shapes with preserved frames.

Usage:
    python3 -m unittest tests.test_text_baseline_roundtrip

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPT Master conversion modules.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from authoring_roundtrip import materialize_flat_authoring_roundtrip  # noqa: E402
from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg  # noqa: E402
from pptx_to_svg.emu_units import Xfrm  # noqa: E402
from pptx_to_svg.txbody_to_svg import convert_txbody  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg  # noqa: E402


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    's': 'http://www.w3.org/2000/svg',
}
EMU_PER_PX = 9525


def _run(text: str, family: str = 'Microsoft YaHei', size_hpt: int = 3000) -> str:
    return (
        f'<a:r><a:rPr sz="{size_hpt}"><a:latin typeface="{family}"/>'
        f'<a:ea typeface="{family}"/><a:cs typeface="{family}"/>'
        f'</a:rPr><a:t>{escape(text)}</a:t></a:r>'
    )


def _txbody(
    runs: str,
    *,
    spacing_hpt: int | None = None,
    spacing_pct: int | None = None,
    top_inset: int = 0,
) -> ET.Element:
    spacing = (
        f'<a:lnSpc><a:spcPts val="{spacing_hpt}"/></a:lnSpc>'
        if spacing_hpt is not None else ''
    )
    if spacing_pct is not None:
        spacing = f'<a:lnSpc><a:spcPct val="{spacing_pct}"/></a:lnSpc>'
    return ET.fromstring(
        f'<p:txBody xmlns:a="{NS["a"]}" xmlns:p="{NS["p"]}">'
        f'<a:bodyPr anchor="t" wrap="none" lIns="0" tIns="{top_inset}" rIns="0" bIns="0"/>'
        f'<a:lstStyle/><a:p><a:pPr>{spacing}</a:pPr>{runs}</a:p></p:txBody>'
    )


class TextBaselineRoundtripTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.svg_path = self.root / '01_source.svg'

    def _write_svg(self, body: str) -> None:
        self.svg_path.write_text(
            f'<svg xmlns="{NS["s"]}" viewBox="0 0 1280 720">{body}</svg>',
            encoding='utf-8',
        )

    def _export(self, body: str, *, text_flow: str = 'split') -> ET.Element:
        self._write_svg(body)
        xml, *_rest = convert_svg_to_slide_shapes(
            self.svg_path, resource_root=self.root, text_flow=text_flow,
        )
        return ET.fromstring(xml)

    def _text_shape(self, slide: ET.Element) -> ET.Element:
        shapes = [shape for shape in slide.findall('.//p:sp', NS)
                  if shape.find('p:txBody', NS) is not None]
        self.assertEqual(len(shapes), 1)
        return shapes[0]

    def _import(self, body: ET.Element, frame: Xfrm | None = None) -> ET.Element:
        result = convert_txbody(
            body, frame or Xfrm(x=80, y=100, w=600, h=300), None,
        )
        root = ET.fromstring(f'<svg xmlns="{NS["s"]}">{result.svg}</svg>')
        self.assertTrue(root.findall('s:text', NS))
        return root

    def _import_shape(self, shape: ET.Element) -> ET.Element:
        offset = shape.find('p:spPr/a:xfrm/a:off', NS)
        extent = shape.find('p:spPr/a:xfrm/a:ext', NS)
        frame = Xfrm(
            x=int(offset.get('x')) / EMU_PER_PX,
            y=int(offset.get('y')) / EMU_PER_PX,
            w=int(extent.get('cx')) / EMU_PER_PX,
            h=int(extent.get('cy')) / EMU_PER_PX,
        )
        return self._import(shape.find('p:txBody', NS), frame)

    def _assert_baseline(self, imported: ET.Element, expected: float) -> ET.Element:
        text = imported.find('s:text', NS)
        self.assertAlmostEqual(float(text.get('y')), expected, delta=0.000001)
        self.assertEqual(text.get('data-pptx-text-baseline'), 'metrics-v1')
        return text

    def test_native_single_lines_use_their_fonts_baseline_and_top_inset(self) -> None:
        for family, size_hpt, offset in (
            ('Arial', 3000, 38.6666666667),
            ('Calibri', 3000, 37.3333333333),
            ('SimSun', 3000, 41.3333333333),
            ('SimHei', 3000, 41.3333333333),
            ('Microsoft YaHei', 3000, 38.6666666667),
            ('Segoe UI', 1800, 24.0),
        ):
            with self.subTest(family=family):
                body = _txbody(_run('Hgpq', family, size_hpt), top_inset=7 * EMU_PER_PX)
                self._assert_baseline(self._import(body), 107 + offset)

    def test_native_fixed_spacing_uses_the_first_visual_lines_size(self) -> None:
        samples = (
            (3000, 3400, 36.0, 45.3333333333),
            (3000, 3600, 38.6666666667, 48.0),
            (3000, 3700, 37.3333333333, 49.3333333333),
            (4800, 5760, 58.6666666667, 76.8),
        )
        for size_hpt, spacing, offset, advance in samples:
            with self.subTest(size=size_hpt, spacing=spacing):
                runs = (
                    _run('First', size_hpt=size_hpt)
                    + f'<a:br><a:rPr sz="{size_hpt}"/></a:br>'
                    + _run('Second', size_hpt=4800)
                )
                text = self._assert_baseline(
                    self._import(_txbody(runs, spacing_hpt=spacing)), 100 + offset,
                )
                advances = [float(span.get('dy')) for span in text.iter(f'{{{NS["s"]}}}tspan')
                            if span.get('dy') is not None]
                self.assertEqual(len(advances), 1)
                self.assertAlmostEqual(advances[0], advance, delta=0.000001)

    def test_native_mixed_fonts_and_sizes_share_the_entire_lines_baseline(self) -> None:
        samples = (
            _run('Hg', 'Calibri') + _run('中文', 'SimSun'),
            _run('中文', 'SimSun') + _run('Hg', 'Calibri'),
            _run('Hg', size_hpt=1500) + _run('pq', size_hpt=3000),
            _run('Hg', size_hpt=3000) + _run('pq', size_hpt=1500),
        )
        for runs in samples:
            with self.subTest(runs=runs):
                self._assert_baseline(self._import(_txbody(runs)), 138.6666666667)

    def test_percentage_spacing_remains_relative_to_the_natural_line_height(self) -> None:
        samples = (
            ('Microsoft YaHei', 3000, 50000, 18.6666666667, 24.0),
            ('Arial', 3000, 100000, 38.6666666667, 48.0),
            ('Calibri', 3000, 100000, 37.3333333333, 48.0),
            ('SimSun', 3000, 100000, 41.3333333333, 48.0),
            ('Microsoft YaHei', 3000, 100000, 38.6666666667, 48.0),
            ('Microsoft YaHei', 3000, 150000, 54.6666666667, 72.0),
            # 100% retains the natural 57.6 pt line height. Unlike spcPts=5760,
            # it does not first snap to 58 pt and choose the fixed-spacing branch.
            ('Microsoft YaHei', 4800, 100000, 61.3333333333, 76.8),
        )
        for family, size, percent, offset, advance in samples:
            with self.subTest(family=family, size=size, percent=percent):
                runs = (
                    _run('First', family, size)
                    + f'<a:br><a:rPr sz="{size}"/></a:br>'
                    + _run('Second', family, size)
                )
                text = self._assert_baseline(
                    self._import(_txbody(runs, spacing_pct=percent)), 100 + offset,
                )
                spans = [span for span in text.iter(f'{{{NS["s"]}}}tspan')
                         if span.get('dy') is not None]
                self.assertEqual(len(spans), 1)
                self.assertAlmostEqual(float(spans[0].get('dy')), advance, delta=0.000001)

    def test_local_line_spacing_choice_overrides_the_inherited_choice(self) -> None:
        samples = (
            ('spcPct', 100000, 'spcPts', 2000, 138.6666666667, 48.0),
            ('spcPts', 3400, 'spcPct', 150000, 136.0, 45.3333333333),
            ('spcPts', 0, 'spcPct', 150000, 100.0, 0.0),
        )
        for local_kind, local_value, inherited_kind, inherited_value, baseline, advance in samples:
            with self.subTest(local_kind=local_kind, local_value=local_value):
                runs = _run('First') + '<a:br><a:rPr sz="3000"/></a:br>' + _run('Second')
                body = _txbody(runs)
                body.find('a:p/a:pPr', NS).append(ET.fromstring(
                    f'<a:lnSpc xmlns:a="{NS["a"]}">'
                    f'<a:{local_kind} val="{local_value}"/></a:lnSpc>'
                ))
                body.find('a:lstStyle', NS).append(ET.fromstring(
                    f'<a:lvl1pPr xmlns:a="{NS["a"]}"><a:lnSpc>'
                    f'<a:{inherited_kind} val="{inherited_value}"/>'
                    '</a:lnSpc></a:lvl1pPr>'
                ))
                text = self._assert_baseline(self._import(body), baseline)
                spans = [span for span in text.iter(f'{{{NS["s"]}}}tspan')
                         if span.get('dy') is not None]
                self.assertEqual(len(spans), 1)
                self.assertAlmostEqual(float(spans[0].get('dy')), advance, delta=0.000001)

    def test_later_shifted_paragraph_keeps_the_whole_body_on_legacy_baselines(self) -> None:
        body = _txbody(_run('First'))
        shifted_paragraph = ET.fromstring(f'<a:p xmlns:a="{NS["a"]}">{_run("Raised")}</a:p>')
        shifted_paragraph.find('a:r/a:rPr', NS).set('baseline', '30000')
        body.append(shifted_paragraph)
        imported = self._import(body)
        texts = imported.findall('s:text', NS)
        self.assertEqual(len(texts), 2)
        self.assertAlmostEqual(float(texts[0].get('y')), 134.0)
        self.assertTrue(all(text.get('data-pptx-text-baseline') is None for text in texts))

    def test_svg_to_native_to_svg_restores_the_authored_first_baseline(self) -> None:
        samples = [
            (f'<text x="100" y="200" font-family="{family}" font-size="40">Hgpq</text>', 'split')
            for family in ('Arial', 'Calibri', 'SimSun', 'SimHei', 'Microsoft YaHei')
        ]
        samples.extend((
            ('<text x="100" y="200" font-family="Calibri, SimSun" font-size="40">'
             'Hg中文pq</text>', 'split'),
            ('<text x="100" y="200" font-family="Microsoft YaHei" font-size="20">'
             '<tspan>Hg</tspan><tspan font-size="40">pq</tspan></text>', 'split'),
            ('<text x="100" y="200" font-family="Microsoft YaHei" font-size="40">'
             '<tspan x="100" dy="0">First</tspan>'
             '<tspan x="100" dy="45.3333333333333">Second</tspan></text>', 'preserve'),
            ('<text x="100" y="200" font-family="Microsoft YaHei" font-size="64">'
             '<tspan x="100" dy="0">First</tspan>'
             '<tspan x="100" dy="76.8">Second</tspan></text>', 'preserve'),
        ))
        for svg, flow in samples:
            with self.subTest(svg=svg):
                shape = self._text_shape(self._export(svg, text_flow=flow))
                self._assert_baseline(self._import_shape(shape), 200)

    def test_imported_text_with_exact_frame_reconstructs_insets_without_drift(self) -> None:
        body = _txbody(_run('Hgpq'), top_inset=66 * EMU_PER_PX)
        frame = Xfrm(x=80, y=100, w=500, h=200)
        imported = self._import(body, frame)
        for edited_text in ('Edited', 'Again'):
            text = imported.find('s:text', NS)
            self.assertEqual(text.get('data-pptx-text-baseline'), 'metrics-v1')
            text.set('data-pptx-frame', '80 100 500 200')
            text.find('s:tspan', NS).text = edited_text
            shape = self._text_shape(self._export(ET.tostring(text, encoding='unicode')))
            self.assertEqual(
                shape.find('p:spPr/a:xfrm/a:off', NS).attrib,
                {'x': '762000', 'y': '952500'},
            )
            self.assertEqual(
                shape.find('p:spPr/a:xfrm/a:ext', NS).attrib,
                {'cx': '4762500', 'cy': '1905000'},
            )
            self.assertAlmostEqual(
                int(shape.find('p:txBody/a:bodyPr', NS).get('tIns')),
                628650, delta=1,
            )
            imported = self._import_shape(shape)

    def test_legacy_unmarked_svg_keeps_its_existing_exact_frame_insets(self) -> None:
        shape = self._text_shape(self._export(
            '<text x="100" y="200" font-family="Microsoft YaHei" font-size="40" '
            'data-pptx-frame="80 100 500 200">Legacy</text>'
        ))
        self.assertEqual(shape.find('p:spPr/a:xfrm/a:off', NS).get('y'), '952500')
        self.assertEqual(shape.find('p:txBody/a:bodyPr', NS).get('tIns'), '628650')

    def test_real_imported_workspace_preserves_frame_after_text_edit(self) -> None:
        self._write_svg(
            '<text x="100" y="200" font-family="Microsoft YaHei" font-size="40" '
            'data-pptx-frame="80 100 500 200">Hgpq</text>'
        )
        source = self.root / 'source.pptx'
        workspace = self.root / 'workspace'
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            success = create_pptx_with_native_svg(
                [self.svg_path], source, resource_root=self.root, pptx_structure='flat',
                use_compat_mode=False, transition=None, workers=1, verbose=False,
            )
            self.assertTrue(success)
            convert_pptx_to_svg(
                source, workspace, ConvertOptions(inheritance_mode='both', roundtrip=True),
            )
        with zipfile.ZipFile(source) as package:
            original = self._text_shape(ET.fromstring(package.read('ppt/slides/slide1.xml')))
        authoring_dir = workspace / 'authoring-svg-flat'
        authored = authoring_dir / 'slide_01.svg'
        document = ET.parse(authored)
        text = document.getroot().find('.//s:text', NS)
        self.assertIsNotNone(text)
        self.assertEqual(text.get('data-pptx-text-baseline'), 'metrics-v1')
        content = next(node for node in text.iter() if node.text == 'Hgpq')
        content.text = 'Edited'
        document.write(authored, encoding='utf-8', xml_declaration=True)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            materialized = materialize_flat_authoring_roundtrip(
                workspace, authoring_dir, workspace / 'materialized',
            )
            xml, *_rest = convert_svg_to_slide_shapes(
                materialized.svg_files[0], resource_root=workspace, text_flow='preserve',
            )
        rebuilt = self._text_shape(ET.fromstring(xml))
        self.assertEqual([node.text for node in rebuilt.findall('.//a:t', NS)], ['Edited'])
        for child in ('a:off', 'a:ext'):
            self.assertEqual(
                rebuilt.find(f'p:spPr/a:xfrm/{child}', NS).attrib,
                original.find(f'p:spPr/a:xfrm/{child}', NS).attrib,
            )
        for inset in ('lIns', 'tIns', 'rIns', 'bIns'):
            self.assertAlmostEqual(
                int(rebuilt.find('p:txBody/a:bodyPr', NS).get(inset)),
                int(original.find('p:txBody/a:bodyPr', NS).get(inset)), delta=1,
            )
