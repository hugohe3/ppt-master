#!/usr/bin/env python3
"""Exercise untouched local references through the live-preview save routes."""

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_editor.server import create_app  # noqa: E402


class EditorContentSurvivalTests(unittest.TestCase):
    def test_save_preserves_referenced_ids_and_untouched_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'svg_output').mkdir()
            path = project / 'svg_output' / '01.svg'
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1280 720">'
                '<defs><linearGradient id="_edit_0"><stop offset="0" stop-color="#123456"/>'
                '<stop offset="1" stop-color="#ABCDEF"/></linearGradient>'
                '<clipPath id="_edit_2"><rect width="60" height="40"/></clipPath>'
                '<g id="_edit_3"><text x="10" y="30">USE_MARK</text></g></defs>'
                '<style>#_edit_4 { visibility:hidden }</style>'
                '<rect id="box" x="10" width="100" height="80" fill="url(#_edit_0)" '
                'style="clip-path:url(\'#_edit_2\')" data-pptx-role="decoration"/>'
                '<use xlink:href="#_edit_3"/>'
                '<text id="text" x="10" y="200">TEXT_MARK<tspan>RUN_MARK</tspan></text>'
                '<a href="https://example.com/LINK_MARK"><text>LINK_TEXT_MARK</text></a>'
                '<text id="_edit_4" style="display:none">HIDDEN_MARK</text></svg>',
                encoding='utf-8',
            )
            client = create_app(str(project), idle_timeout=0).test_client()
            preview = ET.fromstring(client.get('/api/slide/01.svg').get_json()['content'])
            preview_ids = [elem.get('id') for elem in preview.iter() if elem.get('id')]
            self.assertEqual(len(preview_ids), len(set(preview_ids)))
            for marker in ('_edit_0', '_edit_2', '_edit_3', '_edit_4'):
                self.assertIn(marker, preview_ids)
            response = client.post('/api/slide/01.svg/edit', json={
                'element_id': 'box', 'attrs': {'x': '15'},
            })
            self.assertEqual(response.status_code, 200)
            client.post('/api/slide/01.svg/annotate', json={
                'element_id': 'text', 'annotation': 'ANNOTATION_MARK',
            })
            saved = client.post('/api/save-all').get_json()
            self.assertEqual(saved['files_modified'], ['01.svg'])
            root = ET.parse(path).getroot()
            ids = {elem.get('id') for elem in root.iter()}
            for marker in ('_edit_0', '_edit_2', '_edit_3', '_edit_4'):
                self.assertIn(marker, ids)
            text = path.read_text(encoding='utf-8')
            for marker in ('USE_MARK', 'TEXT_MARK', 'RUN_MARK', 'LINK_MARK',
                           'LINK_TEXT_MARK', 'HIDDEN_MARK', 'ANNOTATION_MARK'):
                self.assertIn(marker, text)
            hidden = next(elem for elem in root.iter() if elem.text == 'HIDDEN_MARK')
            self.assertEqual(hidden.get('style'), 'display:none')
