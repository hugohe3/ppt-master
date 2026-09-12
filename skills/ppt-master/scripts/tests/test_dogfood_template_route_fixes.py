#!/usr/bin/env python3
"""Regression tests for the 2026-09-12 Create Template dogfood fixes.

A zero-padded page-number literal ("02") is the same slide number as "2" and
compiles into a slidenum field; a placeholder slot on a structured page is
rejected as a Morph endpoint by the sidecar validator instead of failing only
at export.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.animation_config import validate_animation_config  # noqa: E402
from svg_to_pptx.pptx_package.builder import (  # noqa: E402
    _replace_literal_run_with_slidenum_field,
)

PML = 'http://schemas.openxmlformats.org/presentationml/2006/main'
DML = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def _shape(text: str) -> ET.Element:
    return ET.fromstring(
        f'<p:sp xmlns:p="{PML}" xmlns:a="{DML}"><p:txBody><a:bodyPr/>'
        f'<a:p><a:r><a:rPr lang="zh-CN"/><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'
    )


def _page(structured: bool) -> str:
    root_attrs = ' data-pptx-master="m" data-pptx-layout="body"' if structured else ''
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"{root_attrs}>'
        '<g id="title-slot" data-pptx-placeholder="title" data-pptx-bounds="80 60 1120 90">'
        '<text x="80" y="120">T</text></g>'
        '<g id="mark" data-pptx-bounds="80 600 40 40"><rect x="80" y="600" width="40" height="40"/></g>'
        '</svg>\n'
    )


def _project(tmp: str, structured: bool, lock_mode: str | None) -> Path:
    root = Path(tmp)
    (root / 'svg_output').mkdir()
    for name in ('01_a.svg', '02_b.svg'):
        (root / 'svg_output' / name).write_text(_page(structured), encoding='utf-8')
    if lock_mode:
        (root / 'spec_lock.md').write_text(
            f'# Execution Lock\n\n## pptx_structure\n- mode: {lock_mode}\n\n## colors\n- primary: #000000\n',
            encoding='utf-8',
        )
    return root


def _config(group: str) -> dict:
    return {
        'version': 1,
        'defaults': {'animation': {'effect': 'none'}},
        'slides': {
            '02_b': {
                'transition': {'effect': 'morph', 'duration': 1},
                'morph': {'from': '01_a', 'pairs': {'key': {'from': group, 'to': group}}},
            },
        },
    }


class SlideNumberFieldTests(unittest.TestCase):
    def test_zero_padded_literal_becomes_field(self) -> None:
        shape = _shape('02')
        self.assertTrue(_replace_literal_run_with_slidenum_field(shape, '2', '{GUID}'))
        fld = shape.find(f'.//{{{DML}}}fld')
        self.assertIsNotNone(fld)
        self.assertEqual(fld.attrib['type'], 'slidenum')
        self.assertEqual(fld.findtext(f'{{{DML}}}t'), '2')

    def test_plain_literal_still_becomes_field(self) -> None:
        self.assertTrue(_replace_literal_run_with_slidenum_field(_shape('12'), '12', '{GUID}'))

    def test_other_number_is_left_alone(self) -> None:
        shape = _shape('03')
        self.assertFalse(_replace_literal_run_with_slidenum_field(shape, '2', '{GUID}'))
        self.assertIsNone(shape.find(f'.//{{{DML}}}fld'))


class PlaceholderMorphEndpointTests(unittest.TestCase):
    def test_slot_on_structured_page_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, structured=True, lock_mode='structured')
            messages = validate_animation_config(root, _config('title-slot'))
            self.assertTrue(any('placeholder slot' in m for m in messages), messages)

    def test_slide_local_group_on_structured_page_is_fine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, structured=True, lock_mode='structured')
            self.assertEqual(validate_animation_config(root, _config('mark')), [])

    def test_flat_lock_keeps_slot_pairable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, structured=True, lock_mode='flat')
            self.assertEqual(validate_animation_config(root, _config('title-slot')), [])

    def test_page_without_layout_metadata_keeps_slot_pairable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp, structured=False, lock_mode=None)
            self.assertEqual(validate_animation_config(root, _config('title-slot')), [])


if __name__ == '__main__':
    unittest.main()
