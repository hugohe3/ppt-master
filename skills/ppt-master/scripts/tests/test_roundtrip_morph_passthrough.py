#!/usr/bin/env python3
"""PPT Master - Round-trip Morph Passthrough Regression Tests

Exercise explicit pairing through the public exporter with preserved endpoints.

Usage:
    python3 -m unittest tests.test_roundtrip_morph_passthrough

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPTX/SVG converters.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from pptx_transitions import MorphPairExpectation, validate_pptx_morph_pairs
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main


NS = {
    's': 'http://www.w3.org/2000/svg',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}


class RoundtripMorphPassthroughTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / 'workspace'
        self.key = 'hero'

    def _import(
        self, *, count: int = 2, formatted: bool = False, encoding: str = 'utf-8',
        transition: str | None = 'morph', collision: bool = False,
    ) -> None:
        files = []
        for index in range(1, count + 1):
            path = self.root / f'page_{index:02}.svg'
            path.write_text(
                f'<svg xmlns="{NS["s"]}" viewBox="0 0 960 540" lang="en-US">'
                '<g id="hero" data-pptx-bounds="50 50 100 80">'
                '<rect x="50" y="50" width="100" height="80" fill="#123456"/>'
                '<rect x="60" y="60" width="20" height="20" fill="#ABCDEF"/></g>'
                '<g id="other" data-pptx-bounds="250 50 100 80">'
                '<rect x="250" y="50" width="100" height="80" fill="#654321"/>'
                '<rect x="260" y="60" width="20" height="20" fill="#FEDCBA"/></g>'
                '</svg>', encoding='utf-8',
            )
            files.append(path)
        source = self.root / 'source.pptx'
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertTrue(create_pptx_with_native_svg(
                files, source, resource_root=self.root, pptx_structure='flat',
                use_compat_mode=False, transition=transition, workers=1, verbose=False,
            ))
        with ZipFile(source) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        for index in range(1, count + 1):
            part = f'ppt/slides/slide{index}.xml'
            xml = parts[part].decode('utf-8')
            original_id = next(node.get('id') for node in ET.fromstring(xml).findall('.//p:cNvPr', NS)
                               if node.get('name') == 'hero')
            xml = xml.replace(f'id="{original_id}" name="hero"', 'id="29" name="hero"')
            if collision:
                xml = xml.replace('name="other"', 'name="!!hero"')
            if formatted:
                xml = xml.replace('xmlns:p=', 'xmlns:z=').replace('<p:', '<z:').replace('</p:', '</z:')
                xml = xml.replace('name="hero"', 'descr="literal > name=\'decoy\'" name = \'hero\'')
                xml = xml.replace('</z:spTree>', '<!-- <z:cNvPr id="29" name="decoy"/> --></z:spTree>')
                xml = xml.replace('><', '>\r\n<')
            if encoding != 'utf-8':
                xml = xml.replace('encoding="UTF-8"', f'encoding="{encoding}"')
                xml = xml.replace("encoding='utf-8'", f"encoding='{encoding}'")
            parts[part] = xml.encode(encoding)
        with ZipFile(source, 'w', ZIP_DEFLATED) as archive:
            for name, payload in parts.items():
                archive.writestr(name, payload)
        self.source_parts = parts
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            convert_pptx_to_svg(
                source, self.workspace, ConvertOptions(inheritance_mode='both', roundtrip=True),
            )

    def _pair(self, *, count: int = 2, stems: list[str] | None = None) -> None:
        stems = stems or [f'slide_{index:02}' for index in range(1, count + 1)]
        path = self.workspace / 'animations.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        for source, destination in zip(stems, stems[1:]):
            row = config['slides'].setdefault(destination, {})
            row.setdefault('transition', {'effect': 'morph', 'duration': 0.6})
            row['morph'] = {'from': source, 'pairs': {self.key: {'from': 'shape-29', 'to': 'shape-29'}}}
        path.write_text(json.dumps(config), encoding='utf-8')

    def _edit(self, index: int) -> None:
        path = self.workspace / 'authoring-svg-flat' / f'slide_{index:02}.svg'
        source = path.read_text(encoding='utf-8')
        self.assertIn('#123456', source)
        path.write_text(source.replace('#123456', '#135790'), encoding='utf-8')

    def _export(self, *flags: str, expected_exit: int = 0) -> dict[str, bytes]:
        path = self.root / 'output.pptx'
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main([str(self.workspace), '--roundtrip', '-o', str(path), *flags])
        self.stdout, self.stderr = stdout.getvalue(), stderr.getvalue()
        self.assertEqual(result, expected_exit, self.stdout + self.stderr)
        self.assertNotIn('Traceback', self.stderr)
        if expected_exit:
            self.assertFalse(path.exists())
            return {}
        self.output = path
        report = json.loads((self.workspace / 'validation/output.report.json').read_text(encoding='utf-8'))
        self.summary = report['source']['authoring_roundtrip']['export_summary']
        with ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}

    def _assert_names(self, parts: dict[str, bytes], count: int = 2) -> None:
        for index in range(1, count + 1):
            root = ET.fromstring(parts[f'ppt/slides/slide{index}.xml'])
            names = [node.get('name') for node in root.findall('.//p:cNvPr', NS) if node.get('id') == '29']
            self.assertEqual(names, ['!!' + self.key])
        validate_pptx_morph_pairs(self.output, [
            MorphPairExpectation(index, index + 1, self.key) for index in range(1, count)
        ])

    def _assert_only_name_changed(
        self, parts: dict[str, bytes], index: int, *, formatted: bool = False, encoding: str = 'utf-8',
    ) -> None:
        part = f'ppt/slides/slide{index}.xml'
        old = "name = 'hero'" if formatted else 'name="hero"'
        quoted = escape('!!' + self.key, {'"': '&quot;', "'": '&apos;'})
        new = f"name = '{quoted}'" if formatted else f'name="{quoted}"'
        # Replace the known fixture attribute, without reserializing either side.
        codec = 'utf-16-le' if encoding == 'UTF-16' else encoding
        self.assertEqual(parts[part], self.source_parts[part].replace(old.encode(codec), new.encode(codec)))
        rels = f'ppt/slides/_rels/slide{index}.xml.rels'
        self.assertEqual(parts[rels], self.source_parts[rels])

    def test_preserved_source_and_rebuilt_destination(self) -> None:
        self._import()
        self._edit(2)
        self._pair()
        parts = self._export()
        self._assert_names(parts)
        self._assert_only_name_changed(parts, 1)
        self.assertEqual(self.summary, {
            'output_pages': 2, 'passthrough': 0, 'cloned_passthrough': 0, 'patched': 1, 'rebuilt': 1,
        })
        self.assertIn('patched=1 rebuilt=1', self.stdout)

    def test_rebuilt_source_and_preserved_destination(self) -> None:
        self._import()
        self._edit(1)
        self._pair()
        parts = self._export()
        self._assert_names(parts)
        self._assert_only_name_changed(parts, 2)
        self.assertEqual((self.summary['patched'], self.summary['rebuilt']), (1, 1))

    def test_both_preserved_with_escaped_name_and_original_markup(self) -> None:
        self._import(formatted=True)
        self.key = '身份 & "quote" <tag> \'single\''
        self._pair()
        parts = self._export()
        self._assert_names(parts)
        for index in (1, 2):
            self._assert_only_name_changed(parts, index, formatted=True)
        self.assertEqual((self.summary['patched'], self.summary['rebuilt']), (2, 0))

    def test_preserved_utf16_xml_keeps_encoding_and_bytes(self) -> None:
        self._import(encoding='UTF-16')
        self._pair()
        parts = self._export()
        self._assert_names(parts)
        for index in (1, 2):
            self._assert_only_name_changed(parts, index, encoding='UTF-16')

    def test_chain_patches_middle_endpoint_once(self) -> None:
        self._import(count=3)
        self._edit(3)
        self._pair(count=3)
        parts = self._export()
        self._assert_names(parts, count=3)
        for index in (1, 2):
            self._assert_only_name_changed(parts, index)
        self.assertEqual((self.summary['patched'], self.summary['rebuilt']), (2, 1))

    def test_planned_copy_is_patched_by_output_identity(self) -> None:
        self._import()
        directory = self.workspace / 'authoring-svg-flat'
        (directory / 'copy.svg').write_bytes((directory / 'slide_01.svg').read_bytes())
        (self.workspace / 'page_plan.json').write_text(json.dumps({
            'schema': 'ppt-master.roundtrip-page-plan.v1',
            'pages': [{'source_slide': 1, 'svg': 'copy.svg'}, {'source_slide': 2}],
        }), encoding='utf-8')
        self._pair(stems=['copy', 'slide_02'])
        self._edit(2)
        parts = self._export()
        self._assert_names(parts)
        # Clone relationship targets have their own names; slide XML is still exact.
        self.assertEqual(parts['ppt/slides/slide1.xml'], self.source_parts['ppt/slides/slide1.xml'].replace(
            b'name="hero"', b'name="!!hero"',
        ))
        self.assertEqual((self.summary['cloned_passthrough'], self.summary['patched']), (0, 1))

    def test_no_explicit_morph_preserves_source_xml(self) -> None:
        self._import(transition=None)
        parts = self._export()
        for index in (1, 2):
            part = f'ppt/slides/slide{index}.xml'
            self.assertEqual(parts[part], self.source_parts[part])
        self.assertEqual((self.summary['passthrough'], self.summary['patched']), (2, 0))

    def test_new_transition_preserves_source_endpoint_bytes(self) -> None:
        self._import(transition=None)
        self._pair()
        parts = self._export()
        self._assert_names(parts)
        self._assert_only_name_changed(parts, 1)
        self.assertEqual((self.summary['patched'], self.summary['rebuilt']), (2, 0))

    def test_notes_overlay_and_pairing_keep_slide_bytes(self) -> None:
        self._import()
        self._pair()
        notes = self.workspace / 'notes'
        notes.mkdir(exist_ok=True)
        (notes / 'slide_01.md').write_text('New speaker note.', encoding='utf-8')
        parts = self._export()
        self._assert_names(parts)
        self.assertEqual(parts['ppt/slides/slide1.xml'], self.source_parts['ppt/slides/slide1.xml'].replace(
            b'name="hero"', b'name="!!hero"',
        ))
        self.assertTrue(any(b'New speaker note.' in payload for name, payload in parts.items()
                            if name.startswith('ppt/notesSlides/')))
        self.assertEqual((self.summary['patched'], self.summary['rebuilt']), (2, 0))

    def test_name_collision_fails_without_traceback_or_delivery(self) -> None:
        self._import(collision=True)
        self._pair()
        self._export(expected_exit=1)
        self.assertIn('!!hero', self.stderr)
        self.assertIn('unmapped object on slide 1', self.stderr)

    def test_both_rebuilt_remain_supported(self) -> None:
        self._import()
        self._edit(1)
        self._edit(2)
        self._pair()
        parts = self._export()
        self._assert_names(parts)
        self.assertEqual((self.summary['patched'], self.summary['rebuilt']), (0, 2))

    def test_invalid_pair_fails_without_traceback_or_delivery(self) -> None:
        self._import()
        self._pair()
        path = self.workspace / 'animations.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        config['slides']['slide_02']['morph']['pairs'][self.key]['from'] = 'missing'
        path.write_text(json.dumps(config), encoding='utf-8')
        self._export(expected_exit=1)
        self.assertIn('slide_01', self.stderr)
        self.assertIn('missing', self.stderr)
