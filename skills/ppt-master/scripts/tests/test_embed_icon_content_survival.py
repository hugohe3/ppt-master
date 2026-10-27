#!/usr/bin/env python3
"""Verify icon replacement retains authored identity and visibility."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class IconContentSurvivalTests(unittest.TestCase):
    def test_finalize_keeps_hidden_icons_hidden_and_preserves_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'svg_output').mkdir()
            icon_dir = project / 'icons' / 'imported'
            icon_dir.mkdir(parents=True)
            (icon_dir / 'marker.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                '<path d="M2 2H22V22H2Z"/></svg>', encoding='utf-8',
            )
            (project / 'svg_output' / '01.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                '<use id="VISIBLE_MARK" data-icon="imported/marker" '
                'data-pptx-role="decoration" data-edit-annotation="A &amp; B" '
                'x="20" y="20" width="40" height="40" fill="#123456"/>'
                '<use id="DISPLAY_MARK" data-icon="imported/marker" '
                'x="100" y="20" width="40" height="40" display="none"/>'
                '<use id="STYLE_MARK" data-icon="imported/marker" '
                'x="200" y="20" width="40" height="40" style="display:none"/>'
                '<use id="OPACITY_MARK" data-icon="imported/marker" '
                'x="300" y="20" width="40" height="40" opacity="0"/>'
                '</svg>', encoding='utf-8',
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / 'finalize_svg.py'), str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            root = ET.parse(project / 'svg_final' / '01.svg').getroot()
            elements = {elem.get('id'): elem for elem in root.iter() if elem.get('id')}
            self.assertEqual(elements['VISIBLE_MARK'].get('data-pptx-role'), 'decoration')
            self.assertEqual(elements['VISIBLE_MARK'].get('data-edit-annotation'), 'A & B')
            self.assertEqual(elements['DISPLAY_MARK'].get('display'), 'none')
            self.assertEqual(elements['STYLE_MARK'].get('style'), 'display:none')
            self.assertEqual(elements['OPACITY_MARK'].get('opacity'), '0')

            from svg_editor.server import create_app

            client = create_app(str(project), idle_timeout=0).test_client()
            preview = ET.fromstring(client.get('/api/slide/01.svg').get_json()['content'])
            icon = next(elem for elem in preview.iter() if elem.get('id') == 'VISIBLE_MARK')
            self.assertEqual(icon.get('data-icon'), 'imported/marker')
