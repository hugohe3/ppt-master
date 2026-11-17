#!/usr/bin/env python3
"""PPT Master - Local Template Confirmation Tests

Exercise library discovery and the confirmation/install receipt through the UI API.

Usage:
    python3 -m unittest tests.test_local_template_confirm

Examples:
    PYTHONPATH=skills/ppt-master/scripts python3 -m unittest tests.test_local_template_confirm

Dependencies:
    Standard library and the confirmation UI runtime dependencies.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import apply_template
import register_template
from confirm_ui import server


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) + '\n', encoding='utf-8')


class LocalTemplateConfirmationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.library = self.root / 'templates'
        config = {}
        for kind, original in register_template.KIND_CONFIG.items():
            directory = self.library / original['dir'].name
            index = directory / original['index'].name
            config[kind] = {**original, 'dir': directory, 'index': index}
            _write_json(index, {})
        for target in (
            patch.dict(register_template.KIND_CONFIG, config),
            patch.object(server, '_TEMPLATES_DIR', self.library),
        ):
            target.start()
            self.addCleanup(target.stop)
        self.project = self.root / 'project'
        self.confirm = self.project / 'confirm_ui'
        self.recommendation = {
            'stage': 'stage1', 'primary_language': 'en',
            'template_options': {
                'schema_version': 1, 'phase': 'template', 'default_mode': 'templates',
                'explicit_workspace_roots': [],
            },
        }
        self._write_stage1()
        self.client = server.create_app(str(self.project), idle_timeout=0).test_client()

    def _write_stage1(self) -> None:
        _write_json(self.confirm / 'recommendations.stage1.json', self.recommendation)

    def _add(self, kind: str, template_id: str, scope: str = 'local') -> Path:
        directory, index = register_template.get_library_paths(kind, scope)
        root = directory / template_id
        spec = root / 'templates' / 'design_spec.md'
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text(
            f'---\nkind: {kind}\n{kind}_id: {template_id}\n---\n# {template_id}\n',
            encoding='utf-8',
        )
        if kind in {'deck', 'layout'}:
            (spec.parent / '01.svg').write_text('<svg/>', encoding='utf-8')
        data = json.loads(index.read_text(encoding='utf-8')) if index.exists() else {}
        data[template_id] = {'summary': f'{scope} {kind}', 'page_count': 1}
        _write_json(index, data)
        return root

    def _options(self) -> dict:
        response = self.client.get('/api/recommendations')
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()['template_options']

    def test_discover_both_layers_and_preselect_exact_local_root_without_writes(self) -> None:
        for kind in register_template.KIND_CONFIG:
            self._add(kind, f'bundled_{kind}', 'builtin')
            self._add(kind, f'personal_{kind}')
        local = self.library / 'local' / 'decks' / 'personal_deck'
        self.recommendation['template_options']['explicit_workspace_roots'] = [str(local)]
        self._write_stage1()
        before = {path: path.read_bytes() for path in self.library.rglob('*') if path.is_file()}
        options = self._options()
        for kind in register_template.KIND_CONFIG:
            candidates = options['library'][kind]
            self.assertEqual([item['key'] for item in candidates], [
                f'library:{kind}:bundled_{kind}', f'library:local:{kind}:personal_{kind}',
            ])
            self.assertTrue(all(item['source'] == 'library' for item in candidates))
            self.assertEqual(candidates[1]['label'], f'personal_{kind}')
        self.assertEqual(options['preselected_keys'], ['library:local:deck:personal_deck'])
        self.assertEqual(options['explicit'], [])
        self.assertEqual(before, {path: path.read_bytes() for path in self.library.rglob('*') if path.is_file()})

    def test_same_id_retains_distinct_keys_roots_and_labels(self) -> None:
        for kind in register_template.KIND_CONFIG:
            self._add(kind, 'same', 'builtin')
            self._add(kind, 'same')
        for kind, candidates in self._options()['library'].items():
            self.assertEqual([item['label'] for item in candidates], ['same (built-in)', 'same (local)'])
            self.assertEqual([item['key'] for item in candidates], [
                f'library:{kind}:same', f'library:local:{kind}:same',
            ])
            self.assertNotEqual(candidates[0]['workspace_root'], candidates[1]['workspace_root'])

    def test_unicode_template_id_is_discovered_and_selected(self) -> None:
        self._add('deck', '中国电信')
        options = self._options()
        key = 'library:local:deck:中国电信'
        self.assertEqual(options['library']['deck'][0]['key'], key)
        response = self.client.post('/api/confirm', json={
            'stage': 'stage1', 'options_sha256': options['options_sha256'],
            'template_selection': {'mode': 'templates', 'selection_keys': [key]},
        })
        self.assertEqual(response.status_code, 200, response.get_json())

    def test_options_digest_tracks_local_index_metadata_and_empty_layers_are_stable(self) -> None:
        empty_digest = self._options()['options_sha256']
        for kind in register_template.KIND_CONFIG:
            _directory, index = register_template.get_library_paths(kind, 'local')
            _write_json(index, {})
        self.assertEqual(self._options()['options_sha256'], empty_digest)
        self._add('deck', 'personal')
        added = self._options()['options_sha256']
        self.assertNotEqual(added, empty_digest)
        _directory, index = register_template.get_library_paths('deck', 'local')
        data = json.loads(index.read_text(encoding='utf-8'))
        data['personal']['page_count'] = 2
        _write_json(index, data)
        self.assertNotEqual(self._options()['options_sha256'], added)

    def test_present_local_indexes_require_objects_and_safe_valid_entries(self) -> None:
        for kind in register_template.KIND_CONFIG:
            _directory, index = register_template.get_library_paths(kind, 'local')
            for data, message in (
                ([], 'must be an object'),
                ({'../escape': {}}, 'unsafe template id'),
                ({'has space': {}}, 'unsafe template id'),
                ({'trailing.': {}}, 'unsafe template id'),
                ({'missing': {}}, 'workspace does not exist'),
                ({'invalid': []}, 'must be an object'),
            ):
                with self.subTest(kind=kind, data=data):
                    _write_json(index, data)
                    response = self.client.get('/api/recommendations')
                    self.assertEqual(response.status_code, 409)
                    self.assertIn(message, response.get_json()['error'])
            index.write_text('{broken', encoding='utf-8')
            self.assertEqual(self.client.get('/api/recommendations').status_code, 409)
            _write_json(index, {})

    def test_local_workspace_requires_matching_spec_and_safe_path(self) -> None:
        root = self._add('deck', 'personal')
        spec = root / 'templates' / 'design_spec.md'
        for content, message in (
            ('---\nkind: brand\n---\n', 'expected'),
            ('# Missing frontmatter\n', 'must start with YAML frontmatter'),
        ):
            with self.subTest(content=content):
                spec.write_text(content, encoding='utf-8')
                response = self.client.get('/api/recommendations')
                self.assertEqual(response.status_code, 409)
                self.assertIn(message, response.get_json()['error'])
        spec.unlink()
        self.assertIn('is missing', self.client.get('/api/recommendations').get_json()['error'])
        outside = self.root / 'outside'
        outside.mkdir()
        directory, index = register_template.get_library_paths('deck', 'local')
        (directory / 'escape').symlink_to(outside, target_is_directory=True)
        _write_json(index, {'escape': {}})
        self.assertIn('direct child', self.client.get('/api/recommendations').get_json()['error'])

    def test_builtin_indexes_remain_required_and_strict(self) -> None:
        _directory, index = register_template.get_library_paths('deck', 'builtin')
        index.unlink()
        self.assertEqual(self.client.get('/api/recommendations').status_code, 409)
        _write_json(index, [])
        self.assertIn('must be an object', self.client.get('/api/recommendations').get_json()['error'])

    def test_local_selection_installs_and_passes_stage2_receipt_checks(self) -> None:
        self._add('deck', 'personal', 'builtin')
        root = self._add('deck', 'personal')
        options = self._options()
        response = self.client.post('/api/confirm', json={
            'stage': 'stage1', 'options_sha256': options['options_sha256'],
            'template_selection': {'mode': 'templates', 'selection_keys': ['library:local:deck:personal']},
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        selection = json.loads((self.confirm / 'template_selection.json').read_text(encoding='utf-8'))
        self.assertEqual(selection['selections'], [{
            'source': 'library', 'kind': 'deck', 'id': 'personal', 'workspace_root': str(root),
        }])
        palette = {
            'background': '#FFFFFF', 'secondary_bg': '#EEEEEE', 'primary': '#111111',
            'accent': '#0000FF', 'secondary_accent': '#FF0000', 'body_text': '#222222',
        }
        fonts = [{
            'heading': {'primary': face, 'css': face},
            'body': {'primary': face, 'css': face}, 'body_size': 24,
            'sizes': {'title': 40, 'subtitle': 30, 'annotation': 18},
        } for face in ('Arial', 'Georgia', 'Consolas')]
        _write_json(self.confirm / 'recommendations.stage2.json', {
            'stage': 'stage2', 'primary_language': 'en',
            'selection_sha256': selection['selection_sha256'],
            'recommend': {'generation_mode': 'continuous', 'image_usage': ['none']},
            'refine_spec': {'value': False}, 'design_spec_depth': {'value': 'brief'},
            'color': {'candidates': [palette] * 3}, 'typography': {'candidates': fonts},
            'template_application': {'value': 'Use the selected deck.'},
        })
        response = self.client.get('/api/recommendations')
        self.assertEqual(response.status_code, 409)
        self.assertIn('template_install.json', response.get_json()['error'])
        apply_template.apply_templates(self.project, [str(root)], validate=False)
        response = self.client.get('/api/recommendations')
        self.assertEqual(response.status_code, 200, response.get_json())
        spec = self.project / 'templates' / 'design_spec.deck.personal.md'
        self.assertIn('`skills/ppt-master/templates/local/decks/personal/` (library)',
                      spec.read_text(encoding='utf-8'))
        spec.write_text(spec.read_text(encoding='utf-8') + 'tampered\n', encoding='utf-8')
        response = self.client.get('/api/recommendations')
        self.assertEqual(response.status_code, 409)
        self.assertIn('installation', response.get_json()['error'])
