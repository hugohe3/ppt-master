#!/usr/bin/env python3
"""Regress Edit Native motion, narration, and notes overlays on small native decks.

Usage: python3 -m unittest tests.test_edit_native_batch_a
Dependencies: python-pptx and the converter's normal dependencies.
"""

from __future__ import annotations

import copy
import io
import json
import posixpath
import sys
import tempfile
import unittest
import wave
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.util import Inches  # noqa: E402

from pptx_animations import create_sequence_timing_xml  # noqa: E402
import notes_to_audio  # noqa: E402
from pptx_delivery_check import audit_pptx_delivery  # noqa: E402
from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg  # noqa: E402
from svg_to_pptx.pptx_package import cli, narration  # noqa: E402
from svg_to_pptx.pptx_package.discovery import find_notes_files  # noqa: E402

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}
MINIMAL_TIMING = (
    '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" '
    'restart="never" nodeType="tmRoot"/></p:par></p:tnLst></p:timing>'
)


def _fragment(xml: str) -> ET.Element:
    wrapped = '<root ' + ' '.join(f'xmlns:{k}="{v}"' for k, v in NS.items()) + '>'
    return ET.fromstring(wrapped + xml + '</root>')[0]


def _note(archive: zipfile.ZipFile, slide: int) -> tuple[str | None, str]:
    part = f'ppt/slides/slide{slide}.xml'
    rels = ET.fromstring(archive.read(f'ppt/slides/_rels/slide{slide}.xml.rels'))
    for rel in rels:
        if rel.get('Type', '').endswith('/notesSlide'):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(part), rel.get('Target')))
            root = ET.fromstring(archive.read(target))
            return target, ' '.join(node.text or '' for node in root.findall('.//a:t', NS))
    return None, ''


class EditNativeBatchATests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _source(self, *, count: int = 1, timing: str = '', advance: bool = False,
                notes: tuple[int, ...] = ()) -> Path:
        prs = Presentation()
        for number in range(1, count + 1):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1))
            if number in notes:
                slide.notes_slide.notes_text_frame.text = f'Original note for source {number}'
            transition = _fragment('<p:transition spd="med"><p:random/></p:transition>')
            if advance:
                transition.set('advClick', '0')
                transition.set('advTm', '4200')
            # python-pptx uses lxml; append through its own parser.
            from pptx.oxml import parse_xml
            slide._element.append(parse_xml(ET.tostring(transition)))
            if timing:
                slide._element.append(parse_xml(ET.tostring(_fragment(timing))))
        source = self.root / 'source.pptx'
        prs.save(source)
        return source

    def _import(self, source: Path, name: str = 'workspace') -> Path:
        project = self.root / name
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            convert_pptx_to_svg(source, project, ConvertOptions(inheritance_mode='both', roundtrip=True))
        return project

    def _export(self, project: Path, *args: str, name: str = 'result.pptx', success: bool = True):
        output = project / name
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = cli.main([str(project), '--roundtrip', '-o', str(output), *args])
        if success:
            self.assertEqual(result, 0, stdout.getvalue() + stderr.getvalue())
            self.assertTrue(output.is_file())
        return output, result, stdout.getvalue(), stderr.getvalue()

    def _config(self, project: Path, *, slides=None, defaults=None) -> None:
        path = project / 'animations.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        if slides is not None:
            config['slides'] = slides
        if defaults is not None:
            config.setdefault('defaults', {}).update(defaults)
        path.write_text(json.dumps(config), encoding='utf-8')

    def _audio(self, project: Path, stem: str = 'slide_01', sample: int = 0) -> Path:
        directory = project / 'audio'
        directory.mkdir(exist_ok=True)
        path = directory / f'{stem}.wav'
        with wave.open(str(path), 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(sample.to_bytes(2, 'little', signed=True) * 1600)
        return path

    def _slide(self, path: Path, number: int = 1) -> ET.Element:
        with zipfile.ZipFile(path) as archive:
            return ET.fromstring(archive.read(f'ppt/slides/slide{number}.xml'))

    def test_a1_animation_and_default_changes_do_not_replace_source_transition(self) -> None:
        source = self._source()
        for name, row, defaults in (
            ('row', {'slide_01': {'animation': {'effect': 'none'}}}, None),
            ('default', {}, {'animation': {'effect': 'entrance_fade'}}),
        ):
            with self.subTest(name=name):
                project = self._import(source, name)
                self._config(project, slides=row, defaults=defaults)
                output, *_ = self._export(project)
                root = self._slide(output)
                self.assertEqual(ET.tostring(root.find('p:transition', NS)),
                                 ET.tostring(self._slide(source).find('p:transition', NS)))
                if name == 'default':
                    self.assertIsNotNone(root.find('p:timing', NS))

    def test_a1_user_edited_default_transition_replaces_deck_wide(self) -> None:
        source = self._source()
        project = self._import(source)
        self._config(project, slides={}, defaults={'transition': {'effect': 'fade', 'duration': 0.4}})
        output, *_ = self._export(project)
        transition = self._slide(output).find('p:transition', NS)
        self.assertIsNotNone(transition)
        self.assertIsNotNone(transition.find('p:fade', NS))

    def test_a2_explicit_none_removes_timing_and_keeps_transition_and_shapes(self) -> None:
        source = self._source(timing=create_sequence_timing_xml([(2, 0, 'entrance_fade')]))
        project = self._import(source)
        self._config(project, slides={'slide_01': {'animation': {'effect': 'none'}}})
        output, *_ = self._export(project)
        before, after = self._slide(source), self._slide(output)
        self.assertIsNone(after.find('p:timing', NS))
        for xpath in ('p:transition', 'p:cSld/p:spTree'):
            self.assertEqual(ET.tostring(before.find(xpath, NS)), ET.tostring(after.find(xpath, NS)))

    def test_a1_legacy_baseline_and_unlisted_motion_are_preserved(self) -> None:
        source = self._source(count=2, timing=create_sequence_timing_xml([(2, 0, 'entrance_fade')]))
        project = self._import(source)
        manifest_path = project / 'analysis/roundtrip_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['sidecars']['animations'].pop('baseline', None)
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        self._config(project, slides={'slide_01': {'animation': {'effect': 'none'}}})
        output, *_ = self._export(project)
        self.assertIsNone(self._slide(output).find('p:timing', NS))
        self.assertEqual(ET.tostring(self._slide(output, 2)), ET.tostring(self._slide(source, 2)))

    def test_a3_narration_accepts_minimal_native_timing(self) -> None:
        project = self._import(self._source(timing=MINIMAL_TIMING))
        self._audio(project)
        output, *_ = self._export(project, '--recorded-narration', 'audio')
        self.assertEqual(len(self._slide(output).findall('.//p:audio', NS)), 1)

    def test_a4_preserved_unreconstructed_click_timing_blocks_recording(self) -> None:
        timing = create_sequence_timing_xml([(2, 0, 'entrance_fade')], trigger='on-click')
        timing = timing.replace('presetID="10"', 'presetID="999"')
        project = self._import(self._source(timing=timing))
        self._audio(project)
        _, result, _, error = self._export(project, '--recorded-narration', 'audio', success=False)
        self.assertNotEqual(result, 0)
        self.assertIn('slide_01', error)
        self.assertIn('source slide 1', error)
        self.assertIn('shape', error)
        self.assertIn('2', error)
        self._config(project, slides={'slide_01': {'animation': {'effect': 'none'}}})
        self._export(project, '--recorded-narration', 'audio')

    def test_a5_effect_only_changes_preserve_native_advance(self) -> None:
        source = self._source(advance=True)
        for name, args, row in (
            ('cli', ('-t', 'fade'), None),
            ('sidecar', (), {'slide_01': {'transition': {'effect': 'fade', 'duration': 0.4}}}),
        ):
            with self.subTest(name=name):
                project = self._import(source, name)
                if row:
                    self._config(project, slides=row)
                output, *_ = self._export(project, *args)
                transition = self._slide(output).find('p:transition', NS)
                self.assertEqual((transition.get('advClick'), transition.get('advTm')), ('0', '4200'))
                self.assertIsNotNone(transition.find('p:fade', NS))

    def test_a5_imported_narration_matches_output_stems(self) -> None:
        project = self._import(self._source())
        self._audio(project)
        narrated, *_ = self._export(project, '--recorded-narration', 'audio')
        imported = self._import(narrated, 'narrated_import')
        matched = narration.find_narration_files(imported / 'audio', [imported / 'slide_01.svg'])
        self.assertEqual(set(matched), {'slide_01'})
        self._audio(imported, stem='01', sample=200)
        self.assertEqual(
            narration.find_narration_files(imported / 'audio', [imported / 'slide_01.svg']), matched,
        )
        replacement = self._audio(imported, sample=100)
        self.assertEqual(
            narration.find_narration_files(imported / 'audio', [imported / 'slide_01.svg']),
            {'slide_01': replacement},
        )
        repeated, *_ = self._export(imported, '--recorded-narration', 'audio')
        with zipfile.ZipFile(repeated) as archive:
            # The earlier narration part is replaced in place: one narration
            # media part, carrying the replacement bytes, no `_1` suffix growth.
            narration_parts = [
                name for name in archive.namelist()
                if name.startswith('ppt/media/narration') and name.endswith('.wav')
            ]
            self.assertEqual(narration_parts, ['ppt/media/narration1.wav'])
            self.assertEqual(archive.read('ppt/media/narration1.wav'), replacement.read_bytes())
            self.assertEqual(len(self._slide(repeated).findall('.//p:audio', NS)), 1)

    def test_a5_full_overlay_preserves_advance_and_explicit_advance_wins(self) -> None:
        source = self._source(advance=True)
        project = self._import(source)
        self._audio(project)
        output, *_ = self._export(project, '-t', 'none', '--narration-audio-dir', 'audio')
        transition = self._slide(output).find('p:transition', NS)
        self.assertEqual((transition.get('advClick'), transition.get('advTm')), ('0', '4200'))
        self.assertEqual(list(transition), [])
        self._config(project, slides={'slide_01': {'transition': {'auto_advance': 2.3}}})
        output, *_ = self._export(project, name='advance.pptx')
        transition = self._slide(output).find('p:transition', NS)
        self.assertEqual((transition.get('advClick'), transition.get('advTm')), ('1', '2300'))
        self.assertIsNotNone(transition.find('p:random', NS))

    def test_a6_repeated_injection_replaces_owned_audio_only(self) -> None:
        root = self._slide(self._source())
        xml = ET.tostring(root, encoding='unicode')
        for number in (1, 2):
            xml = narration.inject_narration(
                xml, shape_id=narration.next_shape_id(xml), shape_name='narration1.wav',
                audio_rid=f'rId{number * 3}', media_rid=f'rId{number * 3 + 1}',
                poster_rid=f'rId{number * 3 + 2}', start_delay=0.8,
            )
        final = ET.fromstring(xml)
        self.assertEqual(len(final.findall('.//p:pic', NS)), 1)
        self.assertEqual(len(final.findall('.//p:audio', NS)), 1)

    def test_a6_second_export_does_not_overwrite_source_media(self) -> None:
        project = self._import(self._source())
        self._audio(project)
        narrated, *_ = self._export(project, '--recorded-narration', 'audio')
        imported = self._import(narrated, 'second')
        # Keep an unrelated audio shape sharing the original audio part.
        source = imported / 'sources/source.pptx'
        with zipfile.ZipFile(source) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        root = ET.fromstring(entries['ppt/slides/slide1.xml'])
        other = copy.deepcopy(root.find('.//p:pic', NS))
        other.find('p:nvPicPr/p:cNvPr', NS).attrib.update(id='99', name='Unrelated sound')
        # This shape deliberately has neither the new marker nor the legacy geometry.
        for ext in other.findall('.//p:ext', NS):
            if 'ppt-master' in ext.get('uri', ''):
                other.find('.//p:extLst', NS).remove(ext)
        other.find('p:spPr/a:xfrm/a:off', NS).set('x', '0')
        root.find('p:cSld/p:spTree', NS).append(other)
        other_timing = copy.deepcopy(root.find('.//p:audio', NS))
        other_timing.find('.//p:cTn', NS).set('id', '99')
        other_timing.find('.//p:spTgt', NS).set('spid', '99')
        root.find('.//p:cTn[@nodeType="tmRoot"]/p:childTnLst', NS).append(other_timing)
        entries['ppt/slides/slide1.xml'] = ET.tostring(root)
        shared_source = self.root / 'shared_audio.pptx'
        with zipfile.ZipFile(shared_source, 'w') as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        shared = self._import(shared_source, 'shared')
        self._audio(shared, sample=100)
        output, *_ = self._export(shared, '--recorded-narration', 'audio')
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read('ppt/media/narration1.wav'), entries['ppt/media/narration1.wav'])
            final = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            self.assertEqual(len(final.findall('.//p:pic', NS)), 2)
            self.assertEqual(len(final.findall('.//p:audio', NS)), 2)
            retained = next(node for node in final.findall('.//p:audio', NS)
                            if node.find('.//p:spTgt', NS).get('spid') == '99')
            self.assertEqual(ET.tostring(retained), ET.tostring(other_timing))

    def test_a7_sparse_notes_and_copied_page_are_independent(self) -> None:
        project = self._import(self._source(count=4, notes=(3, 4)))
        (project / 'notes/slide_01.md').write_text('New first note', encoding='utf-8')
        output, *_ = self._export(project)
        with zipfile.ZipFile(output) as archive:
            self.assertIn('Original note for source 3', _note(archive, 3)[1])
            self.assertIn('New first note', _note(archive, 1)[1])
        authoring = project / 'authoring-svg-flat'
        (authoring / 'copy.svg').write_bytes((authoring / 'slide_03.svg').read_bytes())
        (project / 'page_plan.json').write_text(json.dumps({
            'schema': 'ppt-master.roundtrip-page-plan.v1',
            'pages': [{'source_slide': 3}, {'source_slide': 3, 'svg': 'copy.svg'}],
        }), encoding='utf-8')
        (project / 'notes/copy.md').write_text('Copy only', encoding='utf-8')
        output, _, stdout, _ = self._export(project, name='copies.pptx')
        self.assertIn('Speaker notes: 2 page(s)', stdout)
        with zipfile.ZipFile(output) as archive:
            self.assertIn('Original note for source 3', _note(archive, 1)[1])
            self.assertIn('Copy only', _note(archive, 2)[1])
            self.assertNotEqual(_note(archive, 1)[0], _note(archive, 2)[0])

    def test_a7_shared_source_notes_allocate_a_private_part(self) -> None:
        source = self._source(count=3, notes=(3,))
        with zipfile.ZipFile(source) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        rels_path = 'ppt/slides/_rels/slide1.xml.rels'
        rels = ET.fromstring(entries[rels_path])
        ET.SubElement(rels, f"{{{NS['rel']}}}Relationship", {
            'Id': 'rIdNotes', 'Type': NS['r'] + '/notesSlide', 'Target': '../notesSlides/notesSlide1.xml',
        })
        entries[rels_path] = ET.tostring(rels)
        with zipfile.ZipFile(source, 'w') as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        project = self._import(source)
        (project / 'notes/slide_01.md').write_text('Private first note', encoding='utf-8')
        output, *_ = self._export(project)
        with zipfile.ZipFile(output) as archive:
            self.assertIn('Original note for source 3', _note(archive, 3)[1])
            self.assertIn('Private first note', _note(archive, 1)[1])
            self.assertNotEqual(_note(archive, 1)[0], _note(archive, 3)[0])

    def test_a8_roundtrip_notes_match_stems_only(self) -> None:
        project = self.root / 'notes_workspace'
        (project / 'authoring-svg-flat').mkdir(parents=True)
        (project / 'notes').mkdir()
        for name in ('slide_03', 'slide_13'):
            (project / 'notes' / f'{name}.md').write_text(name, encoding='utf-8')
        roster = [project / f'slide_{number:02d}.svg' for number in (3, 4, 16)]
        self.assertEqual(find_notes_files(project, roster), {'slide_03': 'slide_03'})

    def test_a9_delivery_counts_cloned_notes_parts_by_type(self) -> None:
        project = self._import(self._source(count=4, notes=(3, 4)))
        authoring = project / 'authoring-svg-flat'
        (authoring / 'copy.svg').write_bytes((authoring / 'slide_04.svg').read_bytes())
        (project / 'page_plan.json').write_text(json.dumps({
            'schema': 'ppt-master.roundtrip-page-plan.v1',
            'pages': [{'source_slide': 4}, {'source_slide': 4, 'svg': 'copy.svg'}],
        }), encoding='utf-8')
        output, *_ = self._export(project)
        report = audit_pptx_delivery(output)
        self.assertEqual(report['package']['parts']['notes'], 2)
        self.assertEqual(report['package']['parts']['slides'], 2)

    def test_a9_arbitrary_slide_master_and_layout_part_names_are_counted(self) -> None:
        source = self._source(notes=(1,))
        with zipfile.ZipFile(source) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        renames = {'slide1.xml': 'customSlide.xml', 'notesSlide1.xml': 'customNotes.xml',
                   'slideMaster1.xml': 'customMaster.xml', 'slideLayout7.xml': 'customLayout.xml'}
        renamed = self.root / 'renamed.pptx'
        with zipfile.ZipFile(renamed, 'w') as archive:
            for name, data in entries.items():
                for old, new in renames.items():
                    name = name.replace(old, new)
                    if name.endswith(('.xml', '.rels')):
                        data = data.replace(old.encode(), new.encode())
                archive.writestr(name, data)
        parts = audit_pptx_delivery(renamed)['package']['parts']
        self.assertEqual((parts['slides'], parts['notes'], parts['masters'], parts['layouts']), (1, 1, 1, 11))

    def test_p1_star6_negative_rate_is_accepted_without_equals(self) -> None:
        with patch.object(sys, 'argv', ['notes_to_audio.py', '--list-common-voices', '--rate', '-5%']):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(notes_to_audio.main(), 0)
