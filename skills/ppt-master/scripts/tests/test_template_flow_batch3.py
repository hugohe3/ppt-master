#!/usr/bin/env python3
"""Regressions for deterministic template publication and confirmation.

Usage:
    python3 -m unittest tests.test_template_flow_batch3

Dependencies:
    Standard library and the script runtime dependencies.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mirror_template_materialize as mirror  # noqa: E402
import apply_template  # noqa: E402
from confirm_ui import server  # noqa: E402
from project_management.cli import ProjectManager  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_to_pptx.pptx_package.template_structure import (  # noqa: E402
    load_pptx_structure_lock,
    parse_template_slides,
    structured_layout_definition_files,
)

SVG_NS = 'http://www.w3.org/2000/svg'


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding='utf-8')


def _stage1(mode: str = 'free_design') -> dict:
    return {
        'stage': 'stage1', 'primary_language': 'en',
        'template_options': {
            'schema_version': 1, 'phase': 'template', 'default_mode': mode,
            'explicit_workspace_roots': [],
        },
    }


def _structured_page(key: str, content: str = '') -> str:
    return (
        f'<svg xmlns="{SVG_NS}" width="1280" height="720" viewBox="0 0 1280 720" '
        f'data-pptx-master="m" data-pptx-master-name="Master" '
        f'data-pptx-layout="{key}" data-pptx-layout-name="{key}">{content}</svg>'
    )


def _stage2(selection_sha256: str, template: bool) -> tuple[dict, dict]:
    palette = {
        'background': '#FFFFFF', 'secondary_bg': '#EEEEEE', 'primary': '#111111',
        'accent': '#0000FF', 'secondary_accent': '#FF0000', 'body_text': '#222222',
    }
    fonts = [{
        'heading': {'primary': face, 'css': face},
        'body': {'primary': face, 'css': face}, 'body_size': 24,
        'sizes': {'title': 40, 'subtitle': 30, 'annotation': 18},
    } for face in ('Arial', 'Georgia', 'Consolas')]
    recommendation = {
        'stage': 'stage2', 'primary_language': 'en',
        'selection_sha256': selection_sha256,
        'recommend': {'generation_mode': 'continuous', 'image_usage': ['none']},
        'refine_spec': {'value': False}, 'design_spec_depth': {'value': 'brief'},
        'color': {'candidates': [palette] * 3}, 'typography': {'candidates': fonts},
    }
    result = {
        'stage': 'final', 'generation_mode': 'continuous', 'image_usage': ['none'],
        'refine_spec': False, 'design_spec_depth': 'brief',
        'color': palette, 'typography': fonts[0],
    }
    if template:
        recommendation['template_application'] = {'value': 'Use the selected brand and layout.'}
        result['template_application'] = 'Use the selected brand and layout.'
    return recommendation, result


class TemplateFlowBatch3Tests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_a_mirror_keeps_zero_height_source_line(self) -> None:
        empty = ET.fromstring(f'<svg xmlns="{SVG_NS}"/>')
        slide = ET.fromstring(
            f'<svg xmlns="{SVG_NS}"><g id="line" data-pptx-prst="line" '
            'data-pptx-frame="0 80 1280 0"><path d="M 0 80 L 1280 80" '
            'stroke="#000000" fill="none"/></g></svg>'
        )
        result = mirror._compose_template(
            native={'slideSize': {'width_px': 1280, 'height_px': 720}},
            master={'key': 'm', 'name': 'Master'},
            layout={'key': 'l', 'name': 'Layout', 'showMasterShapes': True},
            master_root=empty, layout_root=empty,
            slide={'index': 1, 'showInheritedShapes': True}, slide_root=slide,
            slot_plans=[],
        )
        line = next(e for e in result.iter() if e.get('id') == 'line')
        self.assertEqual(line.tag, f'{{{SVG_NS}}}path')
        self.assertEqual(line.get('d'), 'M 0 80 L 1280 80')

    def test_a_type_b_has_actionable_rejection(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = mirror.main([str(self.root), str(self.root / 'destination')])
        self.assertEqual(code, 1)
        self.assertIn('mirror publishes only pptx_template_import.py workspaces', stderr.getvalue())
        self.assertIn('apply_template.py', stderr.getvalue())
        self.assertNotIn('Traceback', stderr.getvalue())
        _write_json(self.root / 'authoring-svg' / mirror.AUTHORING_MANIFEST_NAME, {
            'schema': mirror.AUTHORING_SCHEMA, 'projection_kind': 'generic',
        })
        with self.assertRaisesRegex(mirror.MirrorMaterializationError, 'apply_template.py'):
            mirror._load_authoring_documents(self.root, set())

    def test_b_language_normalization_keeps_the_confirmed_round(self) -> None:
        confirm = self.root / 'confirm_ui'
        _write_json(confirm / 'recommendations.stage1.json', {
            **_stage1(), 'primary_language': 'AR_sa',
        })
        client = server.create_app(self.root).test_client()
        data = client.get('/api/recommendations').get_json()
        self.assertEqual(data['primary_language'], 'ar-SA')
        response = client.post('/api/confirm', json={
            'stage': 'stage1', 'options_sha256': data['template_options']['options_sha256'],
            'template_selection': {'mode': 'free_design', 'selection_keys': []},
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertFalse(server._fresh_template_restart(confirm))
        self.assertIsNone(server._stage2_ready_error(self.root, confirm))

    def test_b_embedded_options_and_equal_mtimes_allow_free_design(self) -> None:
        confirm = self.root / 'confirm_ui'
        rec = confirm / 'recommendations.stage1.json'
        _write_json(rec, _stage1())
        self.assertIsNone(server._confirmation_launch_error(confirm))
        client = server.create_app(self.root).test_client()
        response = client.post('/api/confirm', json={
            'stage': 'stage1',
            'options_sha256': server._build_template_options(confirm)[0]['options_sha256'],
            'template_selection': {'mode': 'free_design', 'selection_keys': []},
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        for path in confirm.iterdir():
            os.utime(path, ns=(1_000_000_000, 1_000_000_000))
        self.assertIsNone(server._stage2_ready_error(self.root, confirm))
        previous = json.loads((confirm / 'template_selection.json').read_text())
        data = _stage1()
        data['revision'] = 2
        _write_json(rec, data)
        os.utime(rec, ns=(1_000_000_000, 1_000_000_000))
        self.assertTrue(server._fresh_template_restart(confirm))
        self.assertIsNone(server._confirmation_launch_error(confirm))
        self.assertIsNotNone(server._stage2_ready_error(self.root, confirm))
        self.assertEqual(server._active_recommendations_path(confirm), rec)
        self.assertIsNone(server._wait_result_status(confirm / 'result.json', 'stage1'))
        response = client.post('/api/confirm', json={
            'stage': 'stage1',
            'options_sha256': server._build_template_options(confirm)[0]['options_sha256'],
            'template_selection': {'mode': 'free_design', 'selection_keys': []},
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        current = json.loads((confirm / 'template_selection.json').read_text())
        self.assertNotEqual(previous['selection_sha256'], current['selection_sha256'])

    def test_b_real_endpoints_require_install_and_selection_bound_stage2(self) -> None:
        for template in (True, False):
            with self.subTest(template=template):
                project = self.root / str(template)
                project.mkdir()
                confirm = project / 'confirm_ui'
                _write_json(confirm / 'recommendations.stage1.json',
                            _stage1('templates' if template else 'free_design'))
                client = server.create_app(project).test_client()
                options = client.get('/api/recommendations').get_json()['template_options']
                response = client.post('/api/confirm', json={
                    'stage': 'stage1', 'options_sha256': options['options_sha256'],
                    'template_selection': {
                        'mode': 'templates' if template else 'free_design',
                        'selection_keys': ['library:brand:zcare-rescue', 'library:layout:report_core']
                                          if template else [],
                    },
                })
                self.assertEqual(response.status_code, 200, response.get_json())
                selection = json.loads((confirm / 'template_selection.json').read_text())
                rec2, final = _stage2(selection['selection_sha256'], template)
                _write_json(confirm / 'recommendations.stage2.json', rec2)
                if template:
                    response = client.get('/api/recommendations')
                    self.assertEqual(response.status_code, 409)
                    self.assertIn('template_install.json', response.get_json()['error'])
                    apply_template.apply_templates(project, [
                        str(SCRIPTS.parent / 'templates' / 'brands' / 'zcare-rescue'),
                        str(SCRIPTS.parent / 'templates' / 'layouts' / 'report_core'),
                    ], validate=False)
                for path in confirm.iterdir():
                    os.utime(path, ns=(10, 10))
                response = client.get('/api/recommendations')
                self.assertEqual(response.status_code, 200, response.get_json())
                rec2['selection_sha256'] = '0' * 64
                _write_json(confirm / 'recommendations.stage2.json', rec2)
                self.assertNotEqual(client.get('/api/recommendations').status_code, 200)
                self.assertNotEqual(client.post('/api/confirm', json=final).status_code, 200)
                rec2['selection_sha256'] = selection['selection_sha256']
                _write_json(confirm / 'recommendations.stage2.json', rec2)
                response = client.post('/api/confirm', json=final)
                self.assertEqual(response.status_code, 200, response.get_json())
                result = json.loads((confirm / 'result.json').read_text())
                self.assertEqual(result['status'], 'confirmed')
                self.assertEqual(result['selection_sha256'], selection['selection_sha256'])
                self.assertFalse((confirm / 'template_handoff.json').exists())
                self.assertEqual(client.get('/api/recommendations').status_code, 409)

    def test_b_stale_browser_cannot_confirm_revised_options(self) -> None:
        confirm = self.root / 'confirm_ui'
        _write_json(confirm / 'recommendations.stage1.json', _stage1())
        client = server.create_app(self.root).test_client()
        options = client.get('/api/recommendations').get_json()['template_options']
        _write_json(confirm / 'recommendations.stage1.json', {**_stage1(), 'revision': 2})
        response = client.post('/api/confirm', json={
            'stage': 'stage1', 'options_sha256': options['options_sha256'],
            'template_selection': {'mode': 'free_design', 'selection_keys': []},
        })
        self.assertEqual(response.status_code, 409)
        self.assertFalse((confirm / 'template_selection.json').exists())

    def test_a_preservation_receipt_never_exempts_edited_geometry_or_assets(self) -> None:
        import hashlib

        svg = self.root / 'slide.svg'
        svg.write_text('<svg/>', encoding='utf-8')
        digest = hashlib.sha256(svg.read_bytes()).hexdigest()
        asset = self.root / 'photo.png'
        asset.write_bytes(b'original image asset')
        _write_json(self.root / 'template_execution_manifest.json', {
            'schema': 'ppt-master.template-execution-manifest.v1',
            'replication_mode': 'mirror', 'source_package_sha256': 'a' * 64,
            'source_geometry_unchanged': True,
            'templates': [{'prototype': 'slide.svg', 'source_svg_sha256': digest}],
            'source_files_sha256': {
                'slide.svg': digest, asset.name: hashlib.sha256(asset.read_bytes()).hexdigest(),
            },
        })
        geometry = '<text> exceeds the root viewBox on the horizontal axis'
        result = {'source_sha256': digest, 'errors': [geometry, 'missing image'],
                  'warnings': [], 'info': {}}
        checker = SVGQualityChecker(template_mode=True)
        checker._classify_preserved_mirror_geometry(svg, result)
        self.assertEqual(result['errors'], ['missing image'])
        self.assertEqual(len(result['info']['inherited']), 1)
        result.update(source_sha256='b' * 64, errors=[geometry], info={})
        checker._classify_preserved_mirror_geometry(svg, result)
        self.assertEqual(result['errors'], [geometry])
        asset.write_bytes(b'changed image asset')
        result.update(source_sha256=digest, errors=[geometry], info={})
        checker._classify_preserved_mirror_geometry(svg, result)
        self.assertEqual(result['errors'], [geometry])

    def test_a_edited_import_cannot_receive_source_geometry_provenance(self) -> None:
        import hashlib

        source = self.root / 'source.svg'
        source.write_text('<svg/>', encoding='utf-8')
        doc = mirror.AuthoringDocument(
            source.name, source, source, '', {}, hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        self.assertTrue(mirror._source_geometry_is_unchanged({source.name: doc}))
        source.write_text('<svg>edited</svg>', encoding='utf-8')
        self.assertFalse(mirror._source_geometry_is_unchanged({source.name: doc}))

    def test_a_spec_skeleton_is_factual_and_registration_rejects_todos(self) -> None:
        from register_template import SpecParseError, _extract_entry

        root = ET.fromstring(_structured_page('body'))
        native = {'slideSize': {'width_px': 1280, 'height_px': 720},
                  'source': {'sha256': 'a' * 64}, 'slides': [{'index': 1}]}
        spec = mirror._spec_skeleton(native, [(Path('templates/001_content.svg'), root)], 'deck')
        self.assertIn('deck_id: TODO', spec)
        self.assertIn('page_count: 1', spec)
        self.assertIn('canvas_format: ppt169', spec)
        self.assertIn('### Source Preservation Map', spec)
        templates = self.root / 'templates'
        templates.mkdir()
        (templates / 'design_spec.md').write_text(spec, encoding='utf-8')
        with self.assertRaisesRegex(SpecParseError, 'incomplete Design Spec skeleton'):
            _extract_entry('deck', self.root.name, self.root)

    def test_d_pptx_new_and_existing_companions_honor_switch(self) -> None:
        source = self.root / 'reference.pptx'
        source.write_bytes(b'source handled by converter below')
        manager = ProjectManager()

        def convert(_source: Path, markdown: Path) -> None:
            markdown.parent.mkdir(parents=True, exist_ok=True)
            markdown.write_text('reference', encoding='utf-8')
            assets = markdown.with_name(markdown.stem + '_files')
            assets.mkdir(exist_ok=True)
            (assets / 'photo.png').write_bytes(b'image')
            _write_json(assets / 'image_manifest.json', [{'filename': 'photo.png'}])

        for existing in (True, False):
            for propagate in (True, False):
                project = self.root / f'{existing}-{propagate}'
                project.mkdir()
                if existing:
                    convert(source, project / 'sources' / 'reference.md')
                with patch.object(manager, '_import_pptx_intake', return_value=project / 'analysis'), \
                        patch.object(manager, '_import_presentation', side_effect=convert):
                    manager.import_sources(str(project), [str(source)], copy=True,
                                           propagate_images=propagate)
                self.assertEqual((project / 'images' / 'photo.png').exists(), propagate)
                self.assertTrue((project / 'sources' / 'reference_files' / 'photo.png').exists())

    def test_e_quick_ignores_installed_unused_prototypes(self) -> None:
        pages = self.root / 'svg_output'
        pages.mkdir()
        templates = self.root / 'templates'
        templates.mkdir()
        page = pages / '01_body.svg'
        page.write_text(_structured_page('body'), encoding='utf-8')
        (templates / 'unused.svg').write_text('invalid unused prototype', encoding='utf-8')
        checker = SVGQualityChecker(quick_generate=True)
        checker._check_pptx_structure_contract(pages, [page])
        self.assertEqual(checker._pptx_structure_issues, [])
        self.assertEqual(checker._structured_native_slots, [])

    def test_c_capacity_is_font_sensitive_and_read_only(self) -> None:
        from svg_quality.slot_capacity import slot_capacity_report

        path = self.root / 'title.svg'
        path.write_text(_structured_page('title',
            '<g id="title" data-pptx-placeholder="title" data-pptx-bounds="0 0 320 100" '
            'font-family="Arial" font-size="40"><text data-pptx-carrier="true" '
            'x="0" y="40">{{TITLE}}</text></g>'), encoding='utf-8')
        before = path.read_bytes()
        report = slot_capacity_report([path])
        slot = report['slots'][0]
        self.assertEqual(slot['font_size'], 40)
        self.assertGreater(slot['latin']['characters_per_line'], slot['cjk']['characters_per_line'])
        self.assertGreater(slot['cjk']['lines'], 0)
        self.assertNotIn('errors', report)
        self.assertNotIn('warnings', report)
        self.assertEqual(path.read_bytes(), before)

    def test_c_capacity_reads_tspan_fonts_and_zero_baseline(self) -> None:
        from svg_quality.slot_capacity import slot_capacity_report

        path = self.root / 'mixed.svg'
        path.write_text(_structured_page('mixed',
            '<g id="mixed" data-pptx-placeholder="body" data-pptx-bounds="0 0 320 100">'
            '<text data-pptx-carrier="true" font-family="Arial" font-size="16">'
            '<tspan x="0" y="0" font-size="40">Large</tspan>'
            '<tspan x="0" y="48" font-size="24">Small</tspan></text></g>'), encoding='utf-8')
        slot = slot_capacity_report([path])['slots'][0]
        self.assertEqual(slot['font_size'], 40)
        self.assertEqual(slot['line_height'], 48)
        self.assertEqual(slot['line_height_source'], 'tspan baselines')
        self.assertEqual(len(slot['typography_variants']), 2)
        self.assertIn('first visible run', slot['estimate_scope'])

    def test_d_source_images_can_stay_out_of_runtime_pool(self) -> None:
        source = self.root / 'reference.md'
        source.write_text('![image](reference_files/photo.png)', encoding='utf-8')
        assets = self.root / 'reference_files'
        assets.mkdir()
        (assets / 'photo.png').write_bytes(b'bitmap')
        _write_json(assets / 'image_manifest.json', [{'filename': 'photo.png'}])
        project = self.root / 'project'
        project.mkdir()
        manager = ProjectManager()
        manager.import_sources(str(project), [str(source)], copy=True, propagate_images=False)
        self.assertTrue((project / 'sources' / 'reference_files' / 'photo.png').is_file())
        self.assertFalse((project / 'images').exists())
        manager.import_sources(str(project), [str(source)], copy=True)
        self.assertTrue((project / 'images' / 'photo.png').is_file())

    def test_e_registered_unused_typed_layout_is_in_checker_dependencies(self) -> None:
        pages = self.root / 'svg_output'
        pages.mkdir()
        templates = self.root / 'templates'
        templates.mkdir()
        (pages / '01_content.svg').write_text(_structured_page('content'), encoding='utf-8')
        (templates / '02_chart.svg').write_text(_structured_page('chart',
            '<g id="chart" data-pptx-placeholder="chart" data-pptx-bounds="0 0 600 400">'
            '<g data-pptx-carrier="true" data-pptx-replace-with="chart">'
            '<rect x="0" y="0" width="600" height="400"/></g>'
            '</g>'), encoding='utf-8')
        lock = ('## typography\n- font_family: Arial\n- title: 40\n- body: 24\n'
                '## colors\n- primary: #000000\n- background: #FFFFFF\n'
                '## pptx_structure\n- mode: structured\n## pptx_masters\n- m: Master\n'
                '## pptx_layouts\n- content: m | content | P01\n'
                '- chart: m | chart | template:02_chart\n'
                '## page_pptx_layouts\n- P01: content\n')
        (self.root / 'spec_lock.md').write_text(lock, encoding='utf-8')
        specs = parse_template_slides([pages / '01_content.svg'])
        structure = load_pptx_structure_lock(self.root)
        self.assertEqual(structured_layout_definition_files(specs, structure), [templates / '02_chart.svg'])
        checker = SVGQualityChecker()
        checker._check_pptx_structure_contract(pages, [pages / '01_content.svg'])
        self.assertEqual(checker._structured_native_slots, ['chart'], checker._pptx_structure_issues)
        (self.root / 'spec_lock.md').write_text(
            lock.replace('- chart: m | chart | template:02_chart\n', ''), encoding='utf-8')
        structure = load_pptx_structure_lock(self.root)
        self.assertEqual(structured_layout_definition_files(specs, structure), [])
