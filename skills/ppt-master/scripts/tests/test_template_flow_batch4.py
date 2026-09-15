#!/usr/bin/env python3
"""Regressions for dogfood template publication, typography and geometry.

Usage:
    python3 -m unittest tests.test_template_flow_batch4

Dependencies:
    Standard library and the script runtime dependencies.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mirror_template_materialize as mirror  # noqa: E402
import pptx_template_import  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_quality.slot_capacity import slot_capacity_report  # noqa: E402
from svg_to_pptx.drawingml.utils import parse_font_family, unsafe_exported_font_faces  # noqa: E402
from svg_to_pptx.drawingml.theme_fonts import MasterTextStyleSpec  # noqa: E402
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg  # noqa: E402
from svg_to_pptx.pptx_package.template_structure import parse_template_slide  # noqa: E402
from template_text_slots import analyze_template_text_slots  # noqa: E402

SVG_NS = 'http://www.w3.org/2000/svg'
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
PNG = ('data:image/png;base64,'
       'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC')


def _page(body: str, attributes: str = '') -> str:
    return (f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" font-family="Arial" '
            'data-pptx-master="m" data-pptx-master-name="Master" '
            f'data-pptx-layout="l" data-pptx-layout-name="Layout" {attributes}>{body}</svg>')


class TemplateFlowBatch4Tests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def _write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def test_s1_materializer_uses_resolved_workspace_scope(self) -> None:
        svg = self._write('source.svg', _page(
            '<text x="100" y="100" font-size="24">Source</text>'))
        pptx = self.root / 'source.pptx'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(create_pptx_with_native_svg(
                [svg], pptx, resource_root=self.root, verbose=False, use_compat_mode=False,
                master_text_style_spec=MasterTextStyleSpec(3000, 1800)))
            imported = self.root / 'imported'
            with patch.object(sys, 'argv', ['pptx_template_import.py', str(pptx),
                                           '-o', str(imported), '--inheritance-mode', 'both']):
                self.assertEqual(pptx_template_import.main(), 0)
        fake_script = self.root / 'skill/scripts/mirror_template_materialize.py'
        library = self.root / 'skill/templates/decks'
        library.mkdir(parents=True)
        outside = self.root / 'outside'
        outside.mkdir()
        (library / 'escaped').symlink_to(outside, target_is_directory=True)
        with patch.object(mirror, '__file__', str(fake_script)):
            for destination, kind, expected in (
                (self.root / 'project', 'deck', 'design_spec.deck.TODO.md'),
                (self.root / 'project-layout', 'layout', 'design_spec.layout.TODO.md'),
                (library / 'example', 'deck', 'design_spec.md'),
                (library.parent / 'layouts/example', 'layout', 'design_spec.md'),
                (library / 'escaped/project', 'deck', 'design_spec.deck.TODO.md'),
            ):
                with self.subTest(destination=destination):
                    receipt = mirror.materialize_mirror_template(imported, destination, kind=kind)
                    self.assertEqual(receipt['spec_skeleton'], f'templates/{expected}')
                    self.assertTrue((destination / 'templates' / expected).is_file())

    def test_s2_mirror_capacity_resolves_sidecar_selectors_and_effective_fonts(self) -> None:
        path = self._write('templates/01.svg', _page(
            '<g id="source" data-pptx-bounds="20 40 320 100" font-size="40">'
            '<text x="20" y="80"><tspan font-family="Microsoft YaHei">中文</tspan></text></g>'
            '<text id="unlisted" x="500" y="80">Unlisted</text>'))
        slots = analyze_template_text_slots(ET.parse(path).getroot())
        self._write('templates/template_execution_manifest.json', json.dumps({
            'replication_mode': 'mirror', 'source_geometry_unchanged': True,
        }))
        self._write('templates/template_execution/01.text-slots.json', json.dumps({
            'text_slots': [slots[0].model_payload()],
        }))
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        rows = slot_capacity_report([path])['slots']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['selector'], '#source>text')
        self.assertEqual(rows[0]['source'], 'mirror-text-slot')
        self.assertEqual(rows[0]['bounds'], (20, 40, 320, 100))
        self.assertEqual(rows[0]['font_size'], 40)
        self.assertEqual(rows[0]['font_family'], 'Microsoft YaHei')
        self.assertGreater(rows[0]['cjk']['characters_per_line'], 0)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        empty = self._write('empty.svg', _page('<rect width="5" height="5"/>'))
        report = slot_capacity_report([empty])
        self.assertEqual(report['slots'], [])
        self.assertIn('note', report)
        sidecar = self._write('templates/template_execution/01.text-slots.json', json.dumps({
            'text_slots': [{'selector': '#missing'}],
        }))
        self.assertIn('unavailable', slot_capacity_report([path])['slots'][0])
        sidecar.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'text_slots array'):
            slot_capacity_report([path])

    def test_s3_translucent_canvas_rect_stays_a_master_shape(self) -> None:
        self._write('design_spec.md', '---\nkind: deck\nnative_structure_mode: structured\n---\n# Spec\n')
        for opacity in ('fill-opacity="0.8"', 'opacity="0.8"',
                        'style="fill-opacity:0.8"', 'style="opacity:80%"'):
            with self.subTest(opacity=opacity):
                path = self._write('scrim.svg', _page(
                    '<rect id="m-bg" data-pptx-layer="master" width="1280" height="720" fill="#FFFFFF"/>'
                    f'<image id="m-field" data-pptx-layer="master" href="{PNG}" width="1280" height="720"/>'
                    '<rect id="m-scrim" data-pptx-layer="master" width="1280" height="720" '
                    f'fill="#FFFFFF" {opacity}/>'))
                result = SVGQualityChecker(template_mode=True).check_file(str(path))
                self.assertFalse(any('paint order' in issue for issue in result['errors']), result['errors'])
                parse_template_slide(path, 1)
        # Export an attribute-based case and inspect the native shape alpha.
        path.write_text(path.read_text().replace('style="opacity:80%"', 'fill-opacity="0.8"'))
        pptx = self.root / 'scrim.pptx'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(create_pptx_with_native_svg(
                [path], pptx, resource_root=self.root, verbose=False, use_compat_mode=False,
                master_text_style_spec=MasterTextStyleSpec(3000, 1800)))
        with zipfile.ZipFile(pptx) as package:
            master = ET.fromstring(package.read('ppt/slideMasters/slideMaster1.xml'))
        self.assertEqual(len(master.findall('./p:cSld/p:bg', NS)), 1)
        self.assertIsNone(master.find('./p:cSld/p:bg//a:alpha', NS))
        self.assertEqual(master.find('.//p:sp/p:spPr/a:solidFill/a:srgbClr/a:alpha', NS).get('val'), '80000')
        opaque = path.read_text().replace('fill-opacity="0.8"', 'fill-opacity="1"')
        path.write_text(opaque)
        self.assertTrue(any('paint order' in issue for issue in
                            SVGQualityChecker(template_mode=True).check_file(str(path))['errors']))
        for inherited in ('fill-opacity="0.8"', 'style="opacity:0.8"'):
            with self.subTest(inherited=inherited):
                path.write_text(opaque.replace('fill-opacity="1"', '').replace(
                    'data-pptx-layout="l"', f'data-pptx-layout="l" {inherited}'))
                self.assertFalse(any('paint order' in issue for issue in
                                     SVGQualityChecker(template_mode=True).check_file(str(path))['errors']))
                parse_template_slide(path, 1)

    def test_s4_cjk_alias_does_not_claim_the_named_latin_slot(self) -> None:
        for family in ('微软雅黑', 'Microsoft YaHei', 'microsoft yahei', 'noto sans sc'):
            for stack in (f'{family}, Arial', f'"{family}", Arial, sans-serif'):
                with self.subTest(stack=stack):
                    self.assertEqual(parse_font_family(stack), {'latin': 'Arial', 'ea': 'Microsoft YaHei'})
                    self.assertEqual(unsafe_exported_font_faces(stack), {})
        for stack in ('微软雅黑', 'Microsoft YaHei, SimHei, sans-serif'):
            self.assertEqual(parse_font_family(stack), {'latin': 'Microsoft YaHei', 'ea': 'Microsoft YaHei'})
        self.assertEqual(parse_font_family('Arial, sans-serif')['latin'], 'Arial')
        self.assertEqual(parse_font_family('serif, Microsoft YaHei')['latin'], 'Times New Roman')
        self.assertEqual(parse_font_family('Arial', 'ja-JP')['ea'], 'Yu Gothic')

    def test_s5_template_marker_checks_baseline_with_existing_severity(self) -> None:
        for baseline, bucket in ((272, 'errors'), (268.4, 'warnings'), (262.4, None), (257.6, None)):
            with self.subTest(baseline=baseline):
                path = self._write('chapter.svg', _page(
                    '<g id="chapter-num-slot" data-pptx-placeholder="body" data-pptx-bounds="160 176 320 120">'
                    f'<text id="chapter-num-carrier" data-pptx-carrier="true" x="160" y="{baseline}" '
                    'font-size="96">{{CHAPTER_NUM}}</text></g>'))
                result = SVGQualityChecker(template_mode=True).check_file(str(path))
                findings = {key: [issue for issue in result[key] if 'exceeds' in issue]
                            for key in ('errors', 'warnings')}
                if bucket:
                    self.assertEqual(len(findings[bucket]), 1, result)
                    self.assertIn('vertical axis', findings[bucket][0])
                else:
                    self.assertEqual(findings, {'errors': [], 'warnings': []})
                slot = slot_capacity_report([path])['slots'][0]
                self.assertEqual(slot['baseline_allowed'], [257.6, 262.4])
                self.assertEqual(slot['baseline'], baseline)

    def test_s6_fixed_layers_do_not_consume_sparse_display_quota(self) -> None:
        self._write('spec_lock.md', '<!-- ppt-master-schema: spec-lock/v1 -->\n'
                    '# Lock\n\n## typography\n- body: 24\n\n## pptx_structure\n- mode: structured\n')
        for layer in ('master', 'layout', None):
            with self.subTest(layer=layer):
                metadata = f'data-pptx-layer="{layer}" data-pptx-editable="false"' if layer else ''
                path = self._write('svg_output/01.svg', _page(''.join(
                    f'<text id="index-{i}" {metadata} x="140" y="{250 + i * 90}" font-size="40">0{i}</text>'
                    for i in range(4))))
                result = SVGQualityChecker().check_file(str(path))
                recurrence = [issue for issue in result['errors'] if 'typography-size recurrence:' in issue]
                self.assertEqual(bool(recurrence), layer is None, result)
