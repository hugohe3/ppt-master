#!/usr/bin/env python3
"""Regression tests for SVG editor slide-list caching without a running server."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_editor import server  # noqa: E402


class SlideListCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        svg_dir = self.root / 'svg_output'
        svg_dir.mkdir()
        self.svg_path = svg_dir / '01.svg'
        cache_patch = patch.dict(server._LIST_CACHE, clear=True)
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        with patch.object(server.threading.Thread, 'start'):
            app = server.create_app(str(self.root), idle_timeout=0)
        app.config['TESTING'] = True
        self.client = app.test_client()

    def _slide(self) -> dict:
        response = self.client.get('/api/slides')
        self.assertEqual(response.status_code, 200)
        slides = response.get_json()['slides']
        self.assertEqual(len(slides), 1)
        return slides[0]

    def test_invalid_svg_keeps_error_on_repeated_requests(self) -> None:
        self.svg_path.write_text('<svg><g>', encoding='utf-8')
        first = self._slide()
        second = self._slide()
        for slide in (first, second):
            self.assertIs(slide['ok'], False)
            self.assertIn('XML parse error:', slide['error'])
            self.assertEqual(slide['annotation_count'], 0)
        self.assertEqual(second, first)

    def test_changed_mtime_refreshes_parse_status(self) -> None:
        self.svg_path.write_text('<svg><g>', encoding='utf-8')
        first = self._slide()
        self.assertIs(first['ok'], False)
        self.svg_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding='utf-8')
        mtime = first['mtime'] + 1
        os.utime(self.svg_path, (mtime, mtime))
        for _ in range(2):
            slide = self._slide()
            self.assertIs(slide['ok'], True)
            self.assertIsNone(slide['error'])
            self.assertEqual(slide['mtime'], mtime)


if __name__ == '__main__':
    unittest.main()


SLIDE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect id="box" x="0" y="0" width="10" height="10" fill="#000000"/>'
    '</svg>'
)


class StagingDraftTests(unittest.TestCase):
    """Unapplied staged work survives a server restart (issue #319)."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        svg_dir = self.root / 'svg_output'
        svg_dir.mkdir()
        self.svg_path = svg_dir / '01.svg'
        self.svg_path.write_text(SLIDE_SVG, encoding='utf-8')
        self.draft = self.root / 'live_preview' / 'draft.json'
        for cache in (server._LIST_CACHE, server._SLIDE_CACHE):
            cache_patch = patch.dict(cache, clear=True)
            cache_patch.start()
            self.addCleanup(cache_patch.stop)

    def _client(self):
        with patch.object(server.threading.Thread, 'start'):
            app = server.create_app(str(self.root), idle_timeout=0)
        app.config['TESTING'] = True
        return app.test_client()

    def _stage(self, client) -> None:
        response = client.post('/api/slide/01.svg/annotate', json={
            'element_id': 'box', 'annotation': 'make it blue',
        })
        self.assertIs(response.get_json()['draft_saved'], True)
        response = client.post('/api/slide/01.svg/edit', json={
            'element_id': 'box', 'attrs': {'fill': '#ff0000'},
        })
        self.assertIs(response.get_json()['draft_saved'], True)

    def test_restart_restores_staged_annotation_and_edit(self) -> None:
        self._stage(self._client())
        self.assertTrue(self.draft.exists())
        self.assertEqual(self.svg_path.read_text(encoding='utf-8'), SLIDE_SVG)

        client = self._client()
        draft = client.get('/api/config').get_json()['draft']
        restored = {'01.svg': {'annotations': True, 'edits': 1}}
        self.assertEqual(draft['startup']['restored'], restored)
        self.assertEqual(draft['pending'], restored)
        again = client.get('/api/config').get_json()['draft']
        self.assertEqual(again, {'pending': restored, 'startup': None})
        slide = client.get('/api/slide/01.svg').get_json()
        self.assertEqual(slide['undo_depth'], 1)
        self.assertEqual(
            slide['annotations'],
            [{'element_id': 'box', 'tag': 'rect', 'annotation': 'make it blue'}],
        )
        self.assertIn('#ff0000', slide['content'])

        saved = client.post('/api/save-all').get_json()
        self.assertEqual(saved['files_modified'], ['01.svg'])
        self.assertFalse(self.draft.exists())
        self.assertEqual(client.get('/api/config').get_json()['draft']['pending'], {})
        on_disk = self.svg_path.read_text(encoding='utf-8')
        self.assertIn('data-edit-annotation="make it blue"', on_disk)
        self.assertIn('#ff0000', on_disk)

    def test_changed_svg_sets_draft_aside_instead_of_replaying(self) -> None:
        self._stage(self._client())
        self.svg_path.write_text(SLIDE_SVG.replace('width="10"', 'width="20"'), encoding='utf-8')

        client = self._client()
        draft = client.get('/api/config').get_json()['draft']['startup']
        self.assertEqual(draft['restored'], {})
        self.assertEqual(draft['conflicts'], ['01.svg'])
        aside = self.draft.with_name(draft['conflict_file'])
        self.assertIn('make it blue', aside.read_text(encoding='utf-8'))
        self.assertFalse(self.draft.exists())
        self.assertEqual(client.get('/api/slide/01.svg').get_json()['undo_depth'], 0)

    def test_save_refuses_staged_work_when_svg_changed_on_disk(self) -> None:
        client = self._client()
        self._stage(client)
        changed = SLIDE_SVG.replace('width="10"', 'width="20"')
        self.svg_path.write_text(changed, encoding='utf-8')

        response = client.post('/api/save-all')
        self.assertIn('changed on disk', response.get_json()['error'])
        self.assertEqual(response.get_json()['files_modified'], [])
        self.assertEqual(self.svg_path.read_text(encoding='utf-8'), changed)
        self.assertTrue(self.draft.exists())

    def test_unreadable_draft_is_set_aside(self) -> None:
        self.draft.parent.mkdir()
        self.draft.write_text('{not json', encoding='utf-8')
        draft = self._client().get('/api/config').get_json()['draft']['startup']
        self.assertIs(draft['unreadable'], True)
        self.assertFalse(self.draft.exists())
        aside = self.draft.with_name(draft['conflict_file'])
        self.assertEqual(aside.read_text(encoding='utf-8'), '{not json')

    def test_reverting_all_staged_work_removes_draft(self) -> None:
        client = self._client()
        self._stage(client)
        client.delete('/api/slide/01.svg/annotate/box')
        response = client.post('/api/slide/01.svg/undo').get_json()
        self.assertIs(response['draft_saved'], True)
        self.assertFalse(self.draft.exists())

    def test_missing_annotation_target_keeps_page_staged(self) -> None:
        client = self._client()
        client.post('/api/slide/01.svg/annotate', json={
            'element_id': 'gone', 'annotation': 'fix this',
        })
        response = client.post('/api/save-all')
        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertIn('Annotation target not found: gone', body['error'])
        self.assertEqual(body['files_modified'], [])
        self.assertEqual(self.svg_path.read_text(encoding='utf-8'), SLIDE_SVG)
        self.assertIn('fix this', self.draft.read_text(encoding='utf-8'))

    def test_save_with_nothing_staged_writes_nothing(self) -> None:
        body = self._client().post('/api/save-all').get_json()
        self.assertEqual(body, {'status': 'ok', 'files_modified': [], 'draft_saved': True})
        self.assertFalse(self.draft.exists())


class AnnotationHelperTests(unittest.TestCase):
    def test_user_ids_with_the_temp_prefix_are_kept(self) -> None:
        from xml.etree import ElementTree as ET
        from svg_editor.annotations import assign_temp_ids, strip_unused_temp_ids

        root = ET.fromstring(
            '<svg><defs><linearGradient id="_edit_gradient"/></defs>'
            '<rect fill="url(#_edit_gradient)"/><text id="_edit_7">T</text></svg>'
        )
        assign_temp_ids(root)
        strip_unused_temp_ids(root, set())
        ids = {elem.get('id') for elem in root.iter()}
        self.assertIn('_edit_gradient', ids)
        self.assertNotIn('_edit_7', ids)

    def test_leading_dot_numbers_keep_following_line_in_place(self) -> None:
        from xml.etree import ElementTree as ET
        from svg_editor.annotations import promote_tspan_to_text

        root = ET.fromstring(
            '<svg><text y="100" x="0"><tspan id="a" dy=".5">A</tspan>'
            '<tspan id="b" dy=".5">B</tspan></text></svg>'
        )
        self.assertEqual(promote_tspan_to_text(root, 'a', '20', '30'), (True, None))
        following = next(elem for elem in root.iter() if elem.get('id') == 'b')
        self.assertEqual(float(following.get('dy')), 1.0)
