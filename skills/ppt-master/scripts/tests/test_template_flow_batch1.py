#!/usr/bin/env python3
"""Regression coverage for template-flow audit N1/N2/N4/N5/N6/N7/N8."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import apply_template  # noqa: E402
import template_preview_pptx  # noqa: E402
from confirm_ui import server  # noqa: E402
from svg_to_pptx.drawingml.theme_fonts import ThemeFontFace, ThemeFontSpec  # noqa: E402
from svg_to_pptx.pptx_package import builder  # noqa: E402
from svg_to_pptx.pptx_package.template_structure import (  # noqa: E402
    TemplateElementSpec,
    TemplateSlideSpec,
    TemplateStructureError,
)

PML = builder.PML_NS
DML = builder.DML_NS
TEMPLATES = SCRIPTS_DIR.parent / 'templates'


def _files(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def _workspace(root: Path, kind: str, template_id: str) -> Path:
    templates = root / 'templates'
    templates.mkdir(parents=True)
    (templates / f'design_spec.{kind}.{template_id}.md').write_text(
        f'---\nkind: {kind}\n{kind}_id: {template_id}\n---\n# {template_id}\n',
        encoding='utf-8',
    )
    if kind in {'layout', 'deck'}:
        (templates / f'{kind}.svg').write_text('<svg/>', encoding='utf-8')
    return root


def _confirm(project: Path, roots: list[Path], mode: str = 'templates') -> dict:
    confirm = project / 'confirm_ui'
    server._write_json_atomic(confirm / server.RECOMMENDATION_STAGE_NAMES[1], {
        'stage': 'stage1', 'template_options': {
            'schema_version': 1, 'phase': 'template', 'default_mode': mode,
            'explicit_workspace_roots': [str(root) for root in roots],
        },
    })
    options, candidates = server._build_template_options(confirm)
    keys = [key for key, candidate in candidates.items()
            if candidate['workspace_root'] in {str(root) for root in roots}]
    selection = server._resolve_template_confirmation(
        {'mode': mode, 'selection_keys': keys}, candidates, options['options_sha256'],
        project,
    )
    server._write_json_atomic(confirm / server.TEMPLATE_SELECTION_NAME, selection)
    server._write_json_atomic(confirm / server.RESULT_NAME, {
        'stage': 'stage1', 'status': 'stage1-confirmed',
        'stage1_sha256': server._stage1_sha256(confirm),
        'selection_sha256': selection['selection_sha256'],
    })
    return selection


class TemplateInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)
        self.project = _workspace(self.tmp / 'project', 'deck', 'old')
        self.layout = _workspace(self.tmp / 'layout', 'layout', 'new')
        for directory in ('images', 'icons'):
            (self.project / directory).mkdir()
            (self.project / directory / 'keep.bin').write_bytes(b'original')
            (self.layout / directory / 'nested').mkdir(parents=True)
            (self.layout / directory / 'nested' / 'new.bin').write_bytes(b'new')

    def _apply(self):
        return apply_template.apply_templates(
            self.project, [str(self.project), str(self.layout)], validate=False,
        )

    def test_n1_staging_copy_failure_preserves_original_tree(self) -> None:
        before = _files(self.project)
        copy2 = shutil.copy2

        def fail_copy(src, dst, *args, **kwargs):
            if Path(src) == self.layout / 'icons' / 'nested' / 'new.bin':
                raise OSError('injected staging failure')
            return copy2(src, dst, *args, **kwargs)

        with patch('apply_template.shutil.copy2', side_effect=fail_copy):
            with self.assertRaises((OSError, apply_template.ApplyTemplateError)):
                self._apply()
        self.assertEqual(_files(self.project), before)
        self.assertEqual(sorted(p.name for p in self.project.iterdir()), ['icons', 'images', 'templates'])

    def test_n1_each_publication_failure_restores_all_directories(self) -> None:
        (self.project / 'template_install.json').write_bytes(b'previous receipt')
        before = _files(self.project)
        replace = os.replace
        for name in ('templates', 'images', 'icons', 'template_install.json'):
            with self.subTest(destination=name):
                failed = False

                def fail_publish(src, dst):
                    nonlocal failed
                    if Path(dst) == self.project / name and not failed:
                        failed = True
                        raise OSError('injected publication failure')
                    return replace(src, dst)

                with patch('os.replace', side_effect=fail_publish):
                    with self.assertRaises((OSError, apply_template.ApplyTemplateError)):
                        self._apply()
                self.assertTrue(failed)
                self.assertEqual(_files(self.project), before)

    def test_n5_disjoint_explicit_roots_can_be_confirmed(self) -> None:
        brand = _workspace(self.tmp / 'brand', 'brand', 'identity')
        selection = _confirm(self.project, [brand, self.layout])
        self.assertEqual({item['kind'] for item in selection['selections']}, {'brand', 'layout'})

    def test_n5_conflicting_roots_are_rejected_in_both_orders(self) -> None:
        other = _workspace(self.tmp / 'other', 'layout', 'other')
        for roots in ([other, self.layout], [self.layout, other]):
            with self.subTest(roots=roots), self.assertRaisesRegex(ValueError, 'one workspace for kind'):
                _confirm(self.project, roots)

    def test_n5_multikind_root_cannot_be_partially_selected(self) -> None:
        (self.project / 'templates' / 'design_spec.brand.identity.md').write_text(
            '---\nkind: brand\nbrand_id: identity\n---\n# Identity\n', encoding='utf-8',
        )
        _confirm(self.project, [self.project])
        options, candidates = server._build_template_options(self.project / 'confirm_ui')
        keys = [key for key, item in candidates.items()
                if item['workspace_root'] == str(self.project) and item['kind'] == 'deck']
        with self.assertRaisesRegex(ValueError, 'every kind'):
            server._resolve_template_confirmation(
                {'mode': 'templates', 'selection_keys': keys}, candidates, options['options_sha256'],
                self.project,
            )

    def test_n6_authorized_in_place_install_keeps_confirmation_valid(self) -> None:
        _confirm(self.project, [self.project, TEMPLATES / 'layouts' / 'report_core'])
        apply_template.apply_templates(
            self.project, [str(self.project), str(TEMPLATES / 'layouts' / 'report_core')],
            validate=False,
        )
        self.assertIsNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))
        handoff = server._read_template_installation(self.project)
        self.assertEqual(handoff['status'], 'confirmed')

    def test_n6_external_spec_drift_is_rejected_before_install(self) -> None:
        _confirm(self.project, [self.layout])
        spec = self.layout / 'templates' / 'design_spec.layout.new.md'
        spec.write_text(spec.read_text(encoding='utf-8') + '\nChanged\n', encoding='utf-8')
        with self.assertRaises((ValueError, apply_template.ApplyTemplateError)):
            apply_template.apply_templates(self.project, [str(self.layout)], validate=False)

    def test_n6_unreceipted_in_place_change_is_rejected(self) -> None:
        _confirm(self.project, [self.project])
        (self.project / 'templates' / 'deck.svg').write_text('<svg>changed</svg>', encoding='utf-8')
        with self.assertRaises((ValueError, apply_template.ApplyTemplateError)):
            server._read_template_selection(self.project / 'confirm_ui' / server.TEMPLATE_SELECTION_NAME)

    def test_n6_options_drift_is_still_rejected(self) -> None:
        _confirm(self.project, [self.layout])
        options_path = self.project / 'confirm_ui' / server.RECOMMENDATION_STAGE_NAMES[1]
        options = json.loads(options_path.read_text(encoding='utf-8'))
        options['template_options']['lang'] = 'ja'
        previous_time = options_path.stat().st_mtime_ns
        server._write_json_atomic(options_path, options)
        os.utime(options_path, ns=(previous_time, previous_time))
        with self.assertRaisesRegex(ValueError, 'options_sha256'):
            server._read_template_selection(self.project / 'confirm_ui' / server.TEMPLATE_SELECTION_NAME)

    def test_n6_external_asset_drift_is_rejected_after_install(self) -> None:
        brand = _workspace(self.tmp / 'brand', 'brand', 'identity')
        (brand / 'images').mkdir()
        (brand / 'images' / 'logo.bin').write_bytes(b'logo')
        _confirm(self.project, [self.project, brand])
        apply_template.apply_templates(self.project, [str(self.project), str(brand)], validate=False)
        (brand / 'images' / 'logo.bin').write_bytes(b'drift')
        self.assertIsNotNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))

    def test_n8_unrelated_installed_spec_cannot_complete_handoff(self) -> None:
        _confirm(self.project, [TEMPLATES / 'brands' / 'zcare-rescue', TEMPLATES / 'layouts' / 'report_core'])
        self.assertIsNotNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))

    def test_n8_correct_filenames_without_installer_receipt_are_rejected(self) -> None:
        _confirm(self.project, [self.layout])
        shutil.copy2(self.layout / 'templates' / 'design_spec.layout.new.md', self.project / 'templates')
        self.assertIsNotNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))

    def test_n8_installed_asset_drift_invalidates_ready_handoff(self) -> None:
        _confirm(self.project, [self.project, TEMPLATES / 'brands' / 'zcare-rescue'])
        apply_template.apply_templates(
            self.project, [str(self.project), str(TEMPLATES / 'brands' / 'zcare-rescue')], validate=False,
        )
        self.assertIsNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))
        (self.project / 'icons' / 'keep.bin').write_bytes(b'changed')
        with self.assertRaises((ValueError, apply_template.ApplyTemplateError)):
            server._read_template_installation(self.project)

    def test_n8_receipt_for_another_selection_cannot_authorize_handoff(self) -> None:
        apply_template.apply_templates(self.project, [str(self.project)], validate=False)
        _confirm(self.project, [self.layout])
        self.assertIsNotNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))

    def test_n8_installed_spec_and_roster_changes_are_rejected(self) -> None:
        _confirm(self.project, [self.project])
        apply_template.apply_templates(self.project, [str(self.project)], validate=False)
        for relative in ('templates/design_spec.deck.old.md', 'templates/deck.svg'):
            with self.subTest(relative=relative):
                path = self.project / relative
                before = path.read_bytes()
                path.write_bytes(before + b'changed')
                self.assertIsNotNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))
                path.write_bytes(before)
        (self.project / 'images' / 'later-project-asset.bin').write_bytes(b'new project material')
        self.assertIsNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))

    def test_free_design_still_completes_without_installation(self) -> None:
        _confirm(self.project, [], mode='free_design')
        self.assertIsNone(server._stage2_ready_error(self.project, self.project / 'confirm_ui'))


class TemplateBuilderTests(unittest.TestCase):
    def _backgrounds(self, colors: list[str], *, baked: bool = False, public_count: int = 1):
        with tempfile.TemporaryDirectory() as tmp:
            root_dir = Path(tmp)
            item = TemplateElementSpec('background', 0, 'rect', layer='master', is_background=True)
            states = []
            for num, color in enumerate(colors, 1):
                root = ET.fromstring(f'<p:sld xmlns:p="{PML}" xmlns:a="{DML}"><p:cSld><p:spTree/></p:cSld></p:sld>')
                shape = ET.fromstring(
                    f'<p:sp xmlns:p="{PML}" xmlns:a="{DML}"><p:spPr>'
                    '<a:xfrm><a:off x="0" y="0"/><a:ext cx="1280" cy="720"/></a:xfrm>'
                    f'<a:prstGeom prst="rect"/><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                    '</p:spPr></p:sp>'
                )
                if baked:
                    root.find(f'{{{PML}}}cSld').insert(0, ET.fromstring(
                        builder._solid_background_xml_from_shape(shape, (1280, 720)),
                    ))
                else:
                    root.find(f'.//{{{PML}}}spTree').append(shape)
                path = root_dir / f'slide{num}.xml'
                ET.ElementTree(root).write(path, encoding='utf-8')
                spec = TemplateSlideSpec(
                    num, Path(f'page{num}.svg'), 'm', 'M', str(num), str(num), True, True, (item,),
                )
                states.append(builder._TemplateRuntimeSlide(
                    spec, path, path.with_suffix('.rels'), ET.ElementTree(root), root, {},
                    {} if baked else {'2': shape}, {} if baked else {'background': ['2']},
                ))
            target = root_dir / 'master.xml'
            target.write_text(
                f'<p:sldMaster xmlns:p="{PML}"><p:cSld><p:spTree/></p:cSld></p:sldMaster>',
                encoding='utf-8',
            )
            result = builder._move_template_static_shape(
                states, item, target, root_dir / 'master.rels', (1280, 720), public_slide_count=public_count,
            )
            self.assertTrue(all(not list(state.root.iter(f'{{{PML}}}sp')) for state in states))
            return result

    def test_n2_public_background_wins_over_unused_prototype(self) -> None:
        for baked in (False, True):
            with self.subTest(baked=baked):
                self.assertIn('FAFAFA', self._backgrounds(['FAFAFA', 'FFFFFF'], baked=baked))

    def test_n2_inconsistent_public_backgrounds_still_fail(self) -> None:
        for baked in (False, True):
            with self.subTest(baked=baked), self.assertRaises(TemplateStructureError):
                self._backgrounds(['FAFAFA', 'FFFFFF'], baked=baked, public_count=2)

    def test_n2_master_without_public_pages_uses_its_prototype(self) -> None:
        self.assertIn('FFFFFF', self._backgrounds(['FFFFFF'], public_count=0))

    def test_n7_custom_faces_survive_slide_and_layout_placeholder_rebuild(self) -> None:
        fonts = ThemeFontSpec(ThemeFontFace('Arial', 'SimSun', 'Arial'),
                              ThemeFontFace('Arial', 'SimSun', 'Arial'), 'Arial', 'Arial')
        for kind in ('title', 'body'):
            for face, expected in (('Arial Black', 'Arial Black'), ('Arial', '+mj-lt' if kind == 'title' else '+mn-lt'),
                                   ('+mn-lt', '+mj-lt' if kind == 'title' else '+mn-lt')):
                with self.subTest(kind=kind, face=face):
                    shape = ET.fromstring(
                        f'<p:sp xmlns:p="{PML}" xmlns:a="{DML}"><p:nvSpPr><p:nvPr/></p:nvSpPr>'
                        '<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r>'
                        f'<a:rPr><a:latin typeface="{face}"/></a:rPr><a:t>01</a:t>'
                        '</a:r></a:p></p:txBody></p:sp>'
                    )
                    item = TemplateElementSpec('number', 0, 'g', placeholder=kind,
                                               placeholder_bounds=(0, 0, 100, 100))
                    layout = builder._layout_placeholder_shape(shape, item, 1, fonts)
                    builder._patch_slide_placeholder(shape, item, 1, theme_font_spec=fonts)
                    for output in (shape, layout):
                        self.assertEqual(output.find(f'.//{{{DML}}}latin').get('typeface'), expected)


class TemplatePreviewTests(unittest.TestCase):
    def test_n4_default_report_core_preview_compiles_typed_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as output:
            code = template_preview_pptx.main([
                str(TEMPLATES / 'layouts' / 'report_core'), '-o', str(Path(tmp) / 'review.pptx'),
            ])
            self.assertEqual(code, 0, output.getvalue())
            self.assertIn('2 master(s)', output.getvalue())
            self.assertIn('typed', output.getvalue())


class TemplateBrowserTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is needed for the frontend behavior check')
    def test_n5_explicit_checkboxes_expand_roots_and_reject_kind_conflicts(self) -> None:
        source = (SCRIPTS_DIR / 'confirm_ui' / 'static' / 'app.js').read_text(encoding='utf-8')
        selection_code = source[source.index('    function normalizeTemplateCandidates('):
                                source.index('    function normalizeRecId(')]
        validation_code = source[source.index('    function templateSelectionValid('):
                                 source.index('    function submitStage1(')]
        script = '''
const assert = require('node:assert/strict');
var TEMPLATE_KINDS = ['brand', 'style', 'layout', 'deck'];
var TEMPLATE_SELECTIONS, TEMPLATE_OPTIONS, TEMPLATE_CANDIDATES, TEMPLATE_SELECTED_KEYS, TEMPLATE_MODE;
var status = {}, inputs = [];
var document = {
    getElementById: id => id === 'confirm-status' ? status : null,
    querySelectorAll: () => inputs
};
function t(key) { return key; }
function localized(item, field) { return item[field]; }
function el(tag, cls, text) {
    var element = {children: [], appendChild(child) { this.children.push(child); },
                   addEventListener(event, handler) { this[event] = handler; }};
    if (tag === 'input') inputs.push(element);
    return element;
}
''' + selection_code + validation_code + '''
const explicit = [
    {key: 'b', kind: 'brand', workspace_root: '/one'},
    {key: 's', kind: 'style', workspace_root: '/one'},
    {key: 'l', kind: 'layout', workspace_root: '/two'},
    {key: 'x', kind: 'layout', workspace_root: '/conflict'}
];
initTemplateOptions({default_mode: 'templates', explicit, preselected_keys: ['b', 's']});
renderExplicitTemplateChoices();
assert.equal(inputs.length, 3);
assert.deepEqual(TEMPLATE_SELECTED_KEYS, ['b', 's']);
inputs[1].checked = true;
inputs[1].change();
assert.deepEqual(TEMPLATE_SELECTED_KEYS, ['b', 's', 'l']);
assert.equal(templateSelectionValid(), true);
inputs[2].checked = true;
inputs[2].change();
assert.equal(templateSelectionValid(), false);
assert.deepEqual(TEMPLATE_SELECTED_KEYS, ['b', 's', 'l', 'x']);
inputs[2].checked = false;
inputs[2].change();
assert.equal(templateSelectionValid(), true);
chooseFreeDesign();
assert.deepEqual(TEMPLATE_SELECTED_KEYS, []);
assert.equal(inputs.some(input => input.checked), false);
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
