#!/usr/bin/env python3
"""
PPT Master - Native Formula MCE Fallback Regression Tests

Check that block and inline formulas carry their SVG preview as native shapes
in mc:Fallback while PowerPoint keeps reading the editable a14 Choice.

Usage:
    python3 -m unittest tests.test_formula_fallback

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local SVG-to-PPTX / PPTX-to-SVG converters.
"""

from __future__ import annotations

import base64
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_ooxml.ooxml import _text_containers  # noqa: E402
from pptx_shapes.semantic_hash import svg_text_fingerprint  # noqa: E402
from pptx_to_svg.shape_walker import _resolve_alternate_content  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'a14': 'http://schemas.microsoft.com/office/drawing/2010/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

BLOCK_FORMULA = (
    '<g id="dscr" data-pptx-replace-with="formula" '
    'data-pptx-x="200" data-pptx-y="200" data-pptx-width="600" '
    'data-pptx-height="160" data-pptx-bounds="200 200 600 160">'
    '<metadata type="application/json"><![CDATA['
    '{"latex":"DSCR=\\\\frac{EBITDA}{PD}","display":"block",'
    '"font_size":40,"color":"#173B57","align":"center"}'
    ']]></metadata>'
    '{preview}'
    '</g>'
)


def _block_formula(preview: str) -> str:
    return BLOCK_FORMULA.replace('{preview}', preview)


def _preserved_formula_shape(extra_attributes: str = '') -> str:
    """An imported shape whose unchanged source txBody holds Office Math."""
    txbody = (
        f'<p:txBody xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}" '
        f'xmlns:a14="{NS["a14"]}" xmlns:m="{NS["m"]}">'
        '<a:bodyPr/><a:lstStyle/><a:p><a14:m><m:oMathPara><m:oMath>'
        '<m:f><m:num><m:r><m:t>a</m:t></m:r></m:num>'
        '<m:den><m:r><m:t>b</m:t></m:r></m:den></m:f>'
        '</m:oMath></m:oMathPara></a14:m></a:p></p:txBody>'
    )
    shape = (
        '<g xmlns="http://www.w3.org/2000/svg" id="shape-13" '
        'data-pptx-object="shape" data-pptx-frame="64 200 896 104" '
        f'data-pptx-prst="rect" data-pptx-semantic-object="shape"{extra_attributes}>'
        '<path d="M 64 200 L 960 200 L 960 304 L 64 304 Z" fill="#F5F5F5" '
        'stroke="none" data-pptx-part="geometry"/>'
        '<metadata data-pptx-part="txbody" data-pptx-encoding="base64" '
        'data-pptx-text-sha256="{sha}">'
        f'{base64.b64encode(txbody.encode("utf-8")).decode("ascii")}'
        '</metadata>'
        '<text x="512" y="262" text-anchor="middle" font-size="28" '
        'fill="#123B63">a/b</text>'
        '</g>'
    )
    sha = svg_text_fingerprint(ET.fromstring(shape.replace('{sha}', '')))
    return shape.replace(' xmlns="http://www.w3.org/2000/svg"', '').replace(
        '{sha}', sha,
    )


class FormulaFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.svg_path = self.root / '01_formula.svg'

    def _export(self, body: str) -> ET.Element:
        self.svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
            f'{body}</svg>',
            encoding='utf-8',
        )
        xml, *_rest = convert_svg_to_slide_shapes(
            self.svg_path, resource_root=self.root,
        )
        return ET.fromstring(xml)

    def _alternate_content(self, slide: ET.Element) -> ET.Element:
        wrappers = slide.findall('.//mc:AlternateContent', NS)
        self.assertEqual(len(wrappers), 1)
        return wrappers[0]

    def _assert_unique_shape_ids(self, slide: ET.Element) -> None:
        ids = [node.get('id') for node in slide.iter(f"{{{NS['p']}}}cNvPr")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_block_formula_fallback_is_preview_text(self) -> None:
        slide = self._export(_block_formula(
            (
                '<text x="500" y="290" text-anchor="middle" font-size="40" '
                'fill="#173B57">DSCR = EBITDA / PD</text>'
            ),
        ))
        wrapper = self._alternate_content(slide)
        choice = wrapper.find('mc:Choice', NS)
        fallback = wrapper.find('mc:Fallback', NS)
        self.assertEqual(choice.get('Requires'), 'a14')
        self.assertIsNotNone(choice.find('.//a14:m/m:oMathPara', NS))
        self.assertIsNotNone(fallback)
        self.assertIsNone(fallback.find('.//a14:m', NS))
        fallback_text = ''.join(
            node.text or '' for node in fallback.iter(f"{{{NS['a']}}}t")
        )
        self.assertEqual(fallback_text, 'DSCR = EBITDA / PD')
        self._assert_unique_shape_ids(slide)

    def test_multi_part_block_preview_becomes_one_group(self) -> None:
        slide = self._export(_block_formula(
            (
                '<text x="300" y="290" font-size="40" fill="#173B57">DSCR =</text>'
                '<text x="560" y="260" text-anchor="middle" font-size="32" '
                'fill="#173B57">EBITDA</text>'
                '<line x1="480" y1="275" x2="640" y2="275" stroke="#173B57" '
                'stroke-width="2"/>'
                '<text x="560" y="320" text-anchor="middle" font-size="32" '
                'fill="#173B57">PD</text>'
            ),
        ))
        fallback = self._alternate_content(slide).find('mc:Fallback', NS)
        children = list(fallback)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].tag, f"{{{NS['p']}}}grpSp")
        self.assertEqual(len(children[0].findall('p:sp', NS)), 4)
        self._assert_unique_shape_ids(slide)

    def test_inline_formula_fallback_keeps_text_box_with_preview_run(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei">'
            'ratio <tspan data-pptx-inline-formula="\\frac{a_i}{b_i}">aᵢ/bᵢ</tspan>'
            ' holds</text>'
        )
        wrapper = self._alternate_content(slide)
        choice_shape = wrapper.find('mc:Choice/p:sp', NS)
        fallback_shape = wrapper.find('mc:Fallback/p:sp', NS)
        self.assertIsNotNone(choice_shape.find('.//a14:m/m:oMath', NS))
        self.assertIsNotNone(fallback_shape)
        self.assertIsNone(fallback_shape.find('.//a14:m', NS))
        fallback_text = ''.join(
            node.text or '' for node in fallback_shape.iter(f"{{{NS['a']}}}t")
        )
        self.assertEqual(fallback_text, 'ratio aᵢ/bᵢ holds')
        self.assertEqual(
            choice_shape.find('p:spPr/a:xfrm', NS).find('a:off', NS).attrib,
            fallback_shape.find('p:spPr/a:xfrm', NS).find('a:off', NS).attrib,
        )
        self._assert_unique_shape_ids(slide)

    def test_import_selects_choice_and_ignores_fallback(self) -> None:
        slide = self._export(_block_formula(
            (
                '<text x="500" y="290" text-anchor="middle" font-size="40" '
                'fill="#173B57">DSCR = EBITDA / PD</text>'
            ),
        ))
        selected = _resolve_alternate_content(self._alternate_content(slide))
        self.assertIsNotNone(selected)
        self.assertIsNotNone(selected.find('.//a14:m', NS))
        self.assertNotIn(
            'EBITDA / PD',
            ''.join(node.text or '' for node in selected.iter(f"{{{NS['a']}}}t")),
        )

    def test_text_readback_ignores_fallback_copy(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="40" font-family="Microsoft YaHei">'
            'ratio <tspan data-pptx-inline-formula="x">x</tspan> holds</text>'
        )
        containers = _text_containers(slide)
        self.assertEqual(len(containers), 1)
        self.assertIsNotNone(containers[0].find('.//a14:m', NS))

    def test_restored_source_math_gets_visible_text_fallback(self) -> None:
        slide = self._export(_preserved_formula_shape())
        wrapper = self._alternate_content(slide)
        self.assertIsNotNone(wrapper.find('mc:Choice/p:sp//a14:m', NS))
        fallback = wrapper.find('mc:Fallback', NS)
        self.assertIsNotNone(fallback)
        self.assertIsNone(fallback.find('.//a14:m', NS))
        self.assertEqual(
            ''.join(node.text or '' for node in fallback.iter(f"{{{NS['a']}}}t")),
            'a/b',
        )
        self.assertIsNotNone(fallback.find(".//a:srgbClr[@val='F5F5F5']", NS))
        self._assert_unique_shape_ids(slide)

    def test_fallback_copy_of_placeholder_drops_placeholder_role(self) -> None:
        slide = self._export(_preserved_formula_shape(
            ' data-ph-type="body" data-pptx-placeholder-index="1"'
        ))
        wrapper = self._alternate_content(slide)
        self.assertIsNotNone(wrapper.find('mc:Choice/p:sp/p:nvSpPr/p:nvPr/p:ph', NS))
        self.assertEqual(len(slide.findall('.//p:ph', NS)), 1)


if __name__ == '__main__':
    unittest.main()
