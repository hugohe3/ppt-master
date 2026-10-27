#!/usr/bin/env python3
"""
PPT Master - Geometry Import Loss Regressions

Keep evaluated zero-axis paths and report geometry that cannot be recovered.

Usage:
    python3 -m unittest tests.test_pptx_geometry_import_losses

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPT Master importer.
"""

from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_to_svg.converter import convert_pptx_to_svg  # noqa: E402

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
SVG = 'http://www.w3.org/2000/svg'
NS = {'s': SVG, 'a': A}


def _frame(width: int, height: int, *, extent: bool = True) -> str:
    ext = f'<a:ext cx="{width * 9525}" cy="{height * 9525}"/>' if extent else ''
    return f'<a:xfrm><a:off x="1143000" y="1714500"/>{ext}</a:xfrm>'


def _shape(geometry: str, frame: str, *, connector: bool = False, hidden: bool = False) -> str:
    tag, nv_tag = ('cxnSp', 'CxnSp') if connector else ('sp', 'Sp')
    return (
        f'<p:{tag}><p:nv{nv_tag}Pr><p:cNvPr id="2" name="Source" hidden="{int(hidden)}"/>'
        f'<p:cNv{nv_tag}Pr/><p:nvPr/></p:nv{nv_tag}Pr><p:spPr>{frame}{geometry}'
        '<a:noFill/><a:ln w="19050"><a:solidFill><a:srgbClr val="123456"/>'
        f'</a:solidFill></a:ln></p:spPr></p:{tag}>'
    )


class GeometryImportLossTests(unittest.TestCase):
    def _import(self, content: str) -> tuple[ET.Element, dict]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source.pptx'
            with zipfile.ZipFile(source, 'w') as archive:
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
                    f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>'
                    f'{content}</p:spTree></p:cSld></p:sld>'
                ))
            result = convert_pptx_to_svg(source, root / 'output')
            report = json.loads((root / 'output/validation/conversion-report.json').read_text(encoding='utf-8'))
        return ET.fromstring(result.slides[0].svg), report

    def _assert_warning(self, report: dict, code: str, shape_id: str = '2') -> None:
        matching = [item for item in report['diagnostics'] if item['code'] == code and item['shape_id'] == shape_id]
        # Layered and flat projections must not duplicate the same warning.
        self.assertEqual(len(matching), 1, report)
        self.assertEqual(matching[0]['part_path'], 'ppt/slides/slide1.xml')
        self.assertEqual(matching[0]['slide_index'], 1)
        self.assertEqual(matching[0]['severity'], 'warning')
        self.assertEqual(report['summary']['warnings'], len(report['diagnostics']))

    def test_zero_axis_custom_paths_keep_source_payload_and_frame(self) -> None:
        for width, height, count in ((300, 0, 1), (0, 100, 1), (300, 0, 2)):
            with self.subTest(width=width, height=height, count=count):
                path = ('<a:path w="300" h="100" fill="none"><a:moveTo><a:pt x="0" y="0"/>'
                        '</a:moveTo><a:lnTo><a:pt x="300" y="100"/></a:lnTo></a:path>')
                geometry = f'<a:custGeom><a:pathLst>{path * count}</a:pathLst></a:custGeom>'
                svg, report = self._import(_shape(geometry, _frame(width, height)))
                leaf = svg.find('.//s:path', NS)
                self.assertIsNotNone(leaf)
                self.assertEqual(leaf.get('data-pptx-frame'), f'120 180 {width} {height}')
                self.assertEqual(leaf.get('d').count('M '), count)
                payload = ET.fromstring(base64.b64decode(leaf.get('data-pptx-custgeom')))
                expected = ET.fromstring(f'<a:custGeom xmlns:a="{A}"><a:pathLst>{path * count}</a:pathLst></a:custGeom>')
                self.assertEqual(ET.tostring(payload), ET.tostring(expected))
                self._assert_warning(report, 'geometry-degenerate-frame')

    def test_zero_axis_ordinary_presets_keep_evaluated_outline(self) -> None:
        for preset in ('rect', 'ellipse'):
            for width, height in ((300, 0), (0, 100)):
                with self.subTest(preset=preset, width=width, height=height):
                    svg, report = self._import(_shape(f'<a:prstGeom prst="{preset}"/>', _frame(width, height)))
                    path = svg.find('.//s:path', NS)
                    self.assertIsNotNone(path)
                    self.assertTrue(path.get('d'))
                    self.assertEqual(path.get('stroke'), '#123456')
                    self._assert_warning(report, 'geometry-degenerate-frame')

    def test_unrecoverable_frames_report_omission_without_guessing_geometry(self) -> None:
        for connector in (False, True):
            preset = 'straightConnector1' if connector else 'rect'
            for frame in ('', _frame(0, 0), _frame(0, 0, extent=False)):
                with self.subTest(connector=connector, frame=frame):
                    svg, report = self._import(_shape(f'<a:prstGeom prst="{preset}"/>', frame, connector=connector))
                    self.assertIsNone(svg.find('.//s:path', NS))
                    self._assert_warning(report, 'geometry-omitted')

    def test_collapsed_group_reports_source_mapping_and_each_omitted_child(self) -> None:
        child = _shape('<a:prstGeom prst="straightConnector1"/>', _frame(300, 0), connector=True)
        group = (
            '<p:grpSp><p:nvGrpSpPr><p:cNvPr id="3" name="Collapsed"/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm>'
            '<a:off x="1143000" y="1714500"/><a:ext cx="0" cy="952500"/>'
            '<a:chOff x="1143000" y="1714500"/><a:chExt cx="2857500" cy="952500"/>'
            f'</a:xfrm></p:grpSpPr>{child}</p:grpSp>'
        )
        svg, report = self._import(group)
        self.assertIsNone(svg.find('.//s:path', NS))
        self._assert_warning(report, 'group-collapsed-axis', '3')
        self._assert_warning(report, 'geometry-omitted')

    def test_hidden_and_positive_controls_do_not_report_geometry_loss(self) -> None:
        for frame, hidden in ((_frame(300, 100), False), (_frame(0, 0), True)):
            with self.subTest(hidden=hidden):
                _, report = self._import(_shape('<a:prstGeom prst="rect"/>', frame, hidden=hidden))
                expected = ['author-hidden-omitted'] if hidden else []
                self.assertEqual([item['code'] for item in report['diagnostics']], expected)

    def test_existing_zero_axis_connector_does_not_report_geometry_loss(self) -> None:
        svg, report = self._import(_shape(
            '<a:prstGeom prst="straightConnector1"/>', _frame(300, 0), connector=True,
        ))
        self.assertIsNotNone(svg.find('.//s:path', NS))
        self.assertEqual(report['diagnostics'], [])

    def test_unpainted_zero_axis_outline_is_not_resurrected(self) -> None:
        shape = _shape('<a:prstGeom prst="rect"/>', _frame(300, 0)).replace(
            '<a:solidFill><a:srgbClr val="123456"/></a:solidFill>', '<a:noFill/>',
        ).replace(
            '</p:sp>', '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>',
        )
        svg, report = self._import(shape)
        self.assertIsNone(svg.find('.//s:path', NS))
        self.assertIsNone(svg.find('.//s:g', NS))
        self.assertEqual(report['diagnostics'], [])
