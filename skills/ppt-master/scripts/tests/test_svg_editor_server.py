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
