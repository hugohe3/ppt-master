#!/usr/bin/env python3
"""Regression tests for the 2026-09-12 Edit Native PPTX dogfood fixes.

The animation sidecar validator resolved its slide roster only from
``svg_output/``; a round-trip workspace keeps its pages in
``authoring-svg-flat/`` and orders them by ``page_plan.json``, so every
reference in a workspace sidecar read as a missing slide.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.animation_config import (  # noqa: E402
    resolve_slide_svg_files,
    validate_animation_config,
)

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
    '<g id="hero" data-pptx-bounds="100 100 400 200"><rect x="100" y="100" width="400" height="200" fill="#123456"/></g>'
    '</svg>\n'
)


def _workspace(tmp: str, plan: list[dict] | None) -> Path:
    root = Path(tmp)
    authoring = root / 'authoring-svg-flat'
    authoring.mkdir()
    for n in (1, 2, 3):
        (authoring / f'slide_{n:02d}.svg').write_text(SVG, encoding='utf-8')
    if plan is not None:
        (root / 'page_plan.json').write_text(
            json.dumps({'schema': 'ppt-master.roundtrip-page-plan.v1', 'pages': plan}),
            encoding='utf-8',
        )
    return root


class RoundtripRosterTests(unittest.TestCase):
    def test_generate_project_still_uses_svg_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'svg_output').mkdir()
            (root / 'svg_output' / '01_cover.svg').write_text(SVG, encoding='utf-8')
            files, error = resolve_slide_svg_files(root)
            self.assertIsNone(error)
            self.assertEqual([f.name for f in files], ['01_cover.svg'])

    def test_missing_both_rosters_reports_svg_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            files, error = resolve_slide_svg_files(Path(tmp))
            self.assertEqual(files, [])
            self.assertIn('svg_output directory not found', error)

    def test_plan_order_is_the_output_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _workspace(tmp, [{'source_slide': 1}, {'source_slide': 3}, {'source_slide': 2}])
            files, error = resolve_slide_svg_files(root)
            self.assertIsNone(error)
            self.assertEqual([f.stem for f in files], ['slide_01', 'slide_03', 'slide_02'])

    def test_plan_svg_name_and_identity_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _workspace(tmp, None)
            (root / 'authoring-svg-flat' / 'kpi_copy.svg').write_text(SVG, encoding='utf-8')
            files, _ = resolve_slide_svg_files(root)
            self.assertEqual(len(files), 4)
            (root / 'page_plan.json').write_text(json.dumps({
                'schema': 'ppt-master.roundtrip-page-plan.v1',
                'pages': [{'source_slide': 2}, {'source_slide': 2, 'svg': 'kpi_copy.svg'}],
            }), encoding='utf-8')
            files, _ = resolve_slide_svg_files(root)
            self.assertEqual([f.stem for f in files], ['slide_02', 'kpi_copy'])

    def test_workspace_sidecar_validates_against_plan_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _workspace(tmp, [{'source_slide': 1}, {'source_slide': 3}, {'source_slide': 2}])
            config = {
                'version': 1,
                'defaults': {'animation': {'effect': 'none'}},
                'slides': {
                    'slide_03': {'groups': {'hero': {'effect': 'fade', 'order': 1}}},
                    'slide_02': {
                        'transition': {'effect': 'morph', 'duration': 1},
                        'morph': {'from': 'slide_03', 'pairs': {'key': {'from': 'hero', 'to': 'hero'}}},
                    },
                },
            }
            messages = validate_animation_config(root, config)
            self.assertEqual(messages, [])
            wrong = json.loads(json.dumps(config))
            wrong['slides']['slide_02']['morph']['from'] = 'slide_01'
            messages = validate_animation_config(root, wrong)
            self.assertTrue(any('immediately preceding slide "slide_03"' in m for m in messages), messages)


if __name__ == '__main__':
    unittest.main()
