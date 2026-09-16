"""Regression tests for the Edit Native P3 regression round (2026-09-16)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.drawingml.converter import (  # noqa: E402
    convert_svg_to_slide_shapes,
)
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_quality.checker import (  # noqa: E402
    _resolve_project_font_sizes,
    _resolve_project_letter_spacings,
)
from xml.etree import ElementTree as ET  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"
from svg_to_pptx.pptx_package.template_structure import (  # noqa: E402
    TemplateStructureError,
    _native_geometry,
)


class NativeGeometryTests(unittest.TestCase):
    """A collapsed built-in placeholder must not block the whole export."""

    def test_zero_extent_placeholder_reads_as_no_geometry(self) -> None:
        # PowerPoint writes <a:ext cx="0" cy="0"/> for the vertical-text
        # placeholder of its built-in "Title and Vertical Text" layout.
        self.assertIsNone(
            _native_geometry({"x": 0, "y": 0, "width": 0, "height": 0}, "layouts[12]")
        )
        self.assertIsNone(
            _native_geometry({"x": 10, "y": 10, "width": 100, "height": 0}, "layouts[12]")
        )

    def test_negative_or_non_finite_geometry_still_fails(self) -> None:
        with self.assertRaisesRegex(TemplateStructureError, "non-negative"):
            _native_geometry({"x": 0, "y": 0, "width": -1, "height": 5}, "layouts[0]")
        with self.assertRaisesRegex(TemplateStructureError, "non-negative"):
            _native_geometry({"x": 0, "y": 0, "width": float("nan"), "height": 5}, "layouts[0]")

    def test_positive_geometry_round_trips(self) -> None:
        self.assertEqual(
            _native_geometry({"x": 1, "y": 2, "width": 3, "height": 4}, "layouts[0]"),
            (1.0, 2.0, 3.0, 4.0),
        )


class NativeRestorePlaceholderTests(unittest.TestCase):
    """The materializer's placeholder for an unchanged full-canvas picture is a
    full-canvas rect inside a source-identified group; background promotion
    used to swallow it, so the round-trip overlay found no shape for it."""

    def test_source_identified_full_canvas_group_is_not_promoted(self) -> None:
        import tempfile

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
            '<g id="shape-1257" data-pptx-object="group" data-pptx-shape-id="1257" '
            'data-pptx-shape-scope="slide">'
            '<rect x="0" y="0" width="960" height="540.1" fill="#000000"/></g>'
            '<g id="shape-1258" data-pptx-object="group" data-pptx-shape-id="1258" '
            'data-pptx-shape-scope="slide">'
            '<rect x="10" y="10" width="100" height="50" fill="#FF0000"/></g>'
            '</svg>'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "slide_57.svg"
            path.write_text(svg, encoding="utf-8")
            shapes_xml = convert_svg_to_slide_shapes(
                path, resource_root=Path(tmp), slide_num=1, slide_count=1,
            )[0]
        self.assertIn('data-pptx-shape-id', svg)
        self.assertNotIn('<p:bg>', shapes_xml)
        self.assertEqual(shapes_xml.count('name="shape-1257"'), 1)
        self.assertEqual(shapes_xml.count('name="shape-1258"'), 1)


def _parse(svg: str) -> tuple[ET.Element, dict[int, ET.Element]]:
    root = ET.fromstring(svg)
    parents = {id(child): parent for parent in root.iter() for child in parent}
    return root, parents


class ImportedTextModelMeasurementTests(unittest.TestCase):
    """Imported ``paragraphs`` / ``lines`` texts are measured row by row."""

    def _bounds(self, svg: str):
        root, parents = _parse(svg)
        text = next(root.iter(f"{{{SVG_NS}}}text"))
        sizes = _resolve_project_font_sizes(root)
        spacings = _resolve_project_letter_spacings(root, sizes)
        return SVGQualityChecker._estimated_text_bounds(
            text, parents, sizes, spacings, include_headroom=False,
        )

    def test_paragraph_rows_stack_instead_of_concatenating(self) -> None:
        row = "这是一个很长很长的段落文字用来测试宽度估算是否按行进行"
        model = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
            '<g data-pptx-frame="0 0 960 200"><text x="10" y="40" font-size="20" '
            'data-pptx-text-model="paragraphs" data-paragraph-line-height="30">'
            f'<tspan>{row}</tspan><tspan data-paragraph-space-before="6">{row}</tspan>'
            f'<tspan>{row}</tspan></text></g></svg>'
        )
        single = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
            f'<g data-pptx-frame="0 0 960 200"><text x="10" y="40" font-size="20">{row}</text>'
            '</g></svg>'
        )
        stacked = self._bounds(model)
        one_row = self._bounds(single)
        self.assertIsNotNone(stacked)
        self.assertIsNotNone(one_row)
        # Same right edge as one row, three rows tall (two advances + spacing).
        self.assertAlmostEqual(stacked[2], one_row[2], delta=1.0)
        self.assertGreater(stacked[3] - one_row[3], 60.0)

    def test_lines_model_without_positions_is_still_measurable(self) -> None:
        model = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
            '<g data-pptx-frame="0 0 400 200"><text x="10" y="40" font-size="20" '
            'data-pptx-text-model="lines" data-paragraph-line-height="24">'
            '<tspan>first row</tspan>'
            '<tspan data-paragraph-line-break="1">second row is longer</tspan>'
            '</text></g></svg>'
        )
        bounds = self._bounds(model)
        self.assertIsNotNone(bounds)
        self.assertGreater(bounds[3], 40 + 24 - 5)


class _Record:
    representation = "shape"


class _Document:
    def __init__(self, refs):
        self.source_refs = {ref: _Record() for ref in refs}


class RoundtripTextDiffTests(unittest.TestCase):
    """Inside an edited owner, a source text that only moved vertically keeps
    its source-proven width instead of being re-estimated as edited text."""

    OWNER = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540">'
        '<g id="shape-3" data-pptx-source-ref="slide:3" data-pptx-frame="0 0 900 400">'
        '<text x="20" y="{y1}" font-size="16">{t1}</text>'
        '<text x="20" y="80" font-size="16">{t2}</text>'
        '</g></svg>'
    )

    def _diff(self, current: str, baseline: str):
        root, _ = _parse(current)
        baseline_root, _ = _parse(baseline)
        return SVGQualityChecker._roundtrip_text_diff_ids(
            root, _Document(["slide:3"]), baseline_root, {}, {},
        )

    def test_moved_row_and_untouched_sibling_stay_unchanged(self) -> None:
        baseline = self.OWNER.format(y1="40", t1="原文一", t2="原文二")
        current = self.OWNER.format(y1="41", t1="原文一", t2="原文二")
        included, unchanged = self._diff(current, baseline)
        self.assertEqual(len(included), 0)
        self.assertEqual(len(unchanged), 2)

    def test_edited_row_is_included_and_sibling_is_not(self) -> None:
        baseline = self.OWNER.format(y1="40", t1="原文一", t2="原文二")
        current = self.OWNER.format(y1="40", t1="改过的文字", t2="原文二")
        included, unchanged = self._diff(current, baseline)
        self.assertEqual(len(included), 1)
        self.assertEqual(len(unchanged), 1)

    def test_horizontal_move_counts_as_edited(self) -> None:
        baseline = self.OWNER.format(y1="40", t1="原文一", t2="原文二")
        current = baseline.replace('x="20" y="80"', 'x="600" y="80"')
        included, unchanged = self._diff(current, baseline)
        self.assertEqual(len(included), 1)


if __name__ == "__main__":
    unittest.main()
