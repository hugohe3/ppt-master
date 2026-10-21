#!/usr/bin/env python3
"""
PPT Master - Formula Round-trip Identity Regression Tests

Keep imported formula identities on the editable Choice while preview Fallback
shapes allocate fresh ids through the public SVG converter.

Usage:
    python3 -m unittest tests.test_formula_roundtrip_identity

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local SVG-to-PPTX converter.
"""

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes


NS = {
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
PREVIEW = '<text x="200" y="240" font-size="28">x = 1</text>'


def _block_formula(attributes: str = "", preview: str = PREVIEW) -> str:
    return (
        '<g id="formula" data-pptx-replace-with="formula" '
        'data-pptx-x="100" data-pptx-y="200" data-pptx-width="400" '
        f'data-pptx-height="80" data-pptx-bounds="100 200 400 80" {attributes}>'
        '<metadata type="application/json">'
        '{"latex":"x=1","display":"block","font_size":28,"name":"!!formula"}'
        f'</metadata>{preview}</g>'
    )


class FormulaRoundtripIdentityTests(unittest.TestCase):
    def _export(self, body: str) -> ET.Element:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            svg = root / "formula.svg"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                f'{body}</svg>',
                encoding="utf-8",
            )
            xml, *_rest = convert_svg_to_slide_shapes(svg, resource_root=root)
        return ET.fromstring(xml)

    def _assert_unique_ids(self, slide: ET.Element) -> None:
        ids = [node.get("id") for node in slide.findall(".//p:cNvPr", NS)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_imported_block_choice_keeps_source_id_and_morph_name(self) -> None:
        previews = (
            PREVIEW,
            PREVIEW + '<line x1="100" y1="260" x2="500" y2="260" stroke="#000000"/>',
        )
        for preview in previews:
            with self.subTest(multipart=preview != PREVIEW):
                slide = self._export(
                    _block_formula(
                        'data-pptx-shape-id="29" data-pptx-shape-scope="slide"',
                        preview,
                    )
                    + '<rect x="0" y="0" width="10" height="10" '
                    'data-pptx-shape-id="2" data-pptx-shape-scope="slide"/>'
                )
                choice = slide.find(".//mc:Choice/p:sp/p:nvSpPr/p:cNvPr", NS)
                self.assertEqual(choice.get("id"), "29")
                self.assertEqual(choice.get("name"), "!!formula")
                fallback_ids = {
                    node.get("id") for node in slide.findall(".//mc:Fallback//p:cNvPr", NS)
                }
                self.assertTrue(fallback_ids)
                self.assertTrue(fallback_ids.isdisjoint({"2", "29"}))
                self._assert_unique_ids(slide)

    def test_block_identity_uses_source_scope(self) -> None:
        slide = self._export(
            '<rect x="0" y="0" width="10" height="10" '
            'data-pptx-shape-id="29" data-pptx-shape-scope="slide"/>'
            + _block_formula('data-pptx-shape-id="29" data-pptx-shape-scope="layout1"')
        )
        choice = slide.find(".//mc:Choice/p:sp/p:nvSpPr/p:cNvPr", NS)
        self.assertEqual(choice.get("id"), "30")
        self._assert_unique_ids(slide)

    def test_block_without_source_id_keeps_sequential_allocation(self) -> None:
        slide = self._export(
            _block_formula() + '<rect x="0" y="0" width="10" height="10"/>'
        )
        choice = slide.find(".//mc:Choice/p:sp/p:nvSpPr/p:cNvPr", NS)
        fallback = slide.find(".//mc:Fallback/p:sp/p:nvSpPr/p:cNvPr", NS)
        self.assertEqual(choice.get("id"), "2")
        self.assertEqual(fallback.get("id"), "3")
        self.assertEqual(
            [node.get("id") for node in slide.findall(".//p:cNvPr", NS)],
            ["1", "2", "3", "4"],
        )

    def test_inline_fallback_does_not_claim_source_id(self) -> None:
        slide = self._export(
            '<text x="100" y="200" font-size="28" data-pptx-shape-id="29" '
            'data-pptx-shape-scope="slide" data-pptx-shape-name="!!inline">'
            'value <tspan data-pptx-inline-formula="x">x</tspan></text>'
        )
        choice = slide.find(".//mc:Choice/p:sp/p:nvSpPr/p:cNvPr", NS)
        fallback = slide.find(".//mc:Fallback/p:sp/p:nvSpPr/p:cNvPr", NS)
        self.assertEqual(choice.get("id"), "29")
        self.assertEqual(choice.get("name"), "!!inline")
        self.assertEqual(fallback.get("id"), "2")
        self._assert_unique_ids(slide)
