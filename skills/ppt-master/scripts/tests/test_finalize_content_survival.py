#!/usr/bin/env python3
"""Verify text visibility, links, and identity through finalization's public CLI."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SVG_NS = 'http://www.w3.org/2000/svg'


class FinalizeContentSurvivalTests(unittest.TestCase):
    def _finalize(self, content: str) -> ET.Element:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name)
        (project / 'svg_output').mkdir()
        (project / 'svg_output' / '01.svg').write_text(
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720">{content}</svg>',
            encoding='utf-8',
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / 'finalize_svg.py'), str(project)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return ET.parse(project / 'svg_final' / '01.svg').getroot()

    def test_split_rows_retain_identity_without_duplicate_ids(self) -> None:
        root = self._finalize(
            '<text id="name" data-pptx-shape-name="SELECTION_MARK" '
            'data-pptx-role="decoration" x="10" y="20" font-size="24">'
            '<tspan id="RUN_ID_MARK" x="10" dy="20">ONE_MARK</tspan>'
            '<tspan x="10" dy="30">TWO_MARK</tspan></text>'
            '<rect id="name-line-2" width="20" height="20"/>',
        )
        ids = [elem.get('id') for elem in root.iter() if elem.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('name', ids)
        self.assertIn('RUN_ID_MARK', ids)
        rows = root.findall(f'{{{SVG_NS}}}text')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].get('data-pptx-shape-name'), 'SELECTION_MARK')
        self.assertEqual(rows[1].get('data-pptx-role'), 'decoration')
        self.assertEqual(''.join(root.itertext()), 'ONE_MARKTWO_MARK')

    def test_direct_inline_anchor_and_tail_survive_split(self) -> None:
        root = self._finalize(
            '<text x="10" y="20" font-size="24">LEAD_MARK'
            '<a href="https://example.com/LINK_MARK">ANCHOR_MARK</a>TAIL_MARK'
            '<tspan x="10" dy="30">NEXT_MARK</tspan></text>',
        )
        self.assertEqual(''.join(root.itertext()), 'LEAD_MARKANCHOR_MARKTAIL_MARKNEXT_MARK')
        anchor = root.find(f'.//{{{SVG_NS}}}a')
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor.get('href'), 'https://example.com/LINK_MARK')

    def test_parent_and_row_visibility_survive_split(self) -> None:
        root = self._finalize(
            '<text display="none" x="10" y="20" font-size="24">'
            '<tspan x="10" dy="20">HIDDEN_PARENT_MARK</tspan></text>'
            '<text x="10" y="80" font-size="24">'
            '<tspan visibility="hidden" x="10" dy="20">HIDDEN_ROW_MARK</tspan>'
            '<tspan x="10" dy="30">VISIBLE_MARK</tspan></text>',
        )
        rows = {''.join(elem.itertext()): elem for elem in root.findall(f'{{{SVG_NS}}}text')}
        self.assertEqual(rows['HIDDEN_PARENT_MARK'].get('display'), 'none')
        self.assertEqual(rows['HIDDEN_ROW_MARK'].get('visibility'), 'hidden')
        self.assertIsNone(rows['VISIBLE_MARK'].get('visibility'))
