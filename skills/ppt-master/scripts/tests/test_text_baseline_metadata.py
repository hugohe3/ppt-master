#!/usr/bin/env python3
"""
PPT Master - Imported Text Baseline Metadata Regression Tests

Keep the imported baseline convention through text flattening and the
authoring projection used when rebuilding native shapes.

Usage:
    python3 -m unittest tests.test_text_baseline_metadata

Examples:
    Run this module from the scripts directory.

Dependencies:
    Standard library and the local SVG authoring tools.
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

from svg_authoring_view import project_svg_batch  # noqa: E402
from svg_finalize.flatten_tspan import flatten_text_with_tspans  # noqa: E402


SVG = "http://www.w3.org/2000/svg"
BASELINE_ATTR = "data-pptx-text-baseline"


class TextBaselineMetadataTests(unittest.TestCase):
    def test_split_and_preserved_rows_keep_the_imported_baseline_version(self) -> None:
        for merge_paragraphs in (False, True):
            with self.subTest(merge_paragraphs=merge_paragraphs):
                tree = ET.ElementTree(ET.fromstring(
                    f'<svg xmlns="{SVG}" viewBox="0 0 1280 720">'
                    '<text x="100" y="200" font-family="Calibri" font-size="40" '
                    f'{BASELINE_ATTR}="metrics-v1">'
                    '<tspan x="100" dy="0">First</tspan>'
                    '<tspan x="100" dy="48">Second</tspan></text></svg>'
                ))
                flatten_text_with_tspans(
                    tree,
                    merge_paragraphs=merge_paragraphs,
                    preserve_line_breaks=merge_paragraphs,
                )
                texts = list(tree.getroot().iter(f"{{{SVG}}}text"))
                self.assertEqual(len(texts), 1 if merge_paragraphs else 2)
                self.assertEqual(
                    [text.get(BASELINE_ATTR) for text in texts],
                    ["metrics-v1"] * len(texts),
                )

    def test_split_legacy_rows_do_not_acquire_a_new_baseline_version(self) -> None:
        tree = ET.ElementTree(ET.fromstring(
            f'<svg xmlns="{SVG}" viewBox="0 0 1280 720">'
            '<text x="100" y="200" font-size="40">'
            '<tspan x="100" dy="0">First</tspan>'
            '<tspan x="100" dy="48">Second</tspan></text></svg>'
        ))
        flatten_text_with_tspans(tree)
        texts = list(tree.getroot().iter(f"{{{SVG}}}text"))
        self.assertEqual(len(texts), 2)
        self.assertTrue(all(text.get(BASELINE_ATTR) is None for text in texts))

    def test_semantic_projection_keeps_the_first_paragraphs_baseline_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.svg"
            output_dir = root / "authoring"
            output = output_dir / "source.svg"
            source.write_text(
                f'<svg xmlns="{SVG}" viewBox="0 0 1280 720">'
                '<g id="shape-1" data-pptx-object="shape" data-pptx-prst="rect" '
                'data-pptx-frame="80 100 500 200">'
                '<rect data-pptx-part="geometry" data-pptx-object="shape" '
                'data-pptx-prst="rect" data-pptx-frame="80 100 500 200" '
                'x="80" y="100" width="500" height="200" fill="none"/>'
                '<text x="100" y="140" font-family="Calibri" font-size="20" '
                f'{BASELINE_ATTR}="metrics-v1">First</text>'
                '<text x="100" y="180" font-family="Calibri" font-size="20" '
                f'{BASELINE_ATTR}="metrics-v1">Second</text></g></svg>',
                encoding="utf-8",
            )
            project_svg_batch(
                [(source, output)], root, output_dir,
                force=False, projection_kind="flat",
            )
            projected = ET.parse(output).getroot()
            texts = list(projected.iter(f"{{{SVG}}}text"))
            self.assertEqual(len(texts), 1)
            self.assertEqual(texts[0].get(BASELINE_ATTR), "metrics-v1")
            self.assertEqual(texts[0].get("data-pptx-text-model"), "paragraphs")
