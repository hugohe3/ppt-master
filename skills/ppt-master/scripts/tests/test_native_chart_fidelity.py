"""Native chart export follows the fallback drawing: order, markers, fills, spacing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx.native_objects.chart_data import _chart_data  # noqa: E402
from svg_to_pptx.native_objects.chart_style import (  # noqa: E402
    _inferred_bar_gap_width,
    _inferred_bar_overlap,
    _inferred_cross_between,
    _native_chart_chrome_warnings,
)
from svg_to_pptx.native_objects.chart_xml import _chart_xml  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"


def _marker(fallback: str) -> ET.Element:
    svg = ET.fromstring(
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720">'
        '<g id="chart" data-pptx-replace-with="chart">'
        '<metadata type="application/json">{}</metadata>'
        f"{fallback}</g></svg>"
    )
    return svg.find(f"{{{SVG_NS}}}g")


def _render(payload: dict, fallback: str = "") -> str:
    elem = _marker(fallback)
    return _chart_xml(
        elem,
        payload,
        chart_rels_id="rId1",
        chart_data=_chart_data(payload),
        chart_bounds=(0, 0, 12192000, 6858000),
    ).decode("utf-8")


def _bar_payload(**extra: object) -> dict:
    payload = {
        "type": "bar",
        "categories": ["A", "B", "C"],
        "series": [{"name": "S", "values": [1, 2, 3]}],
    }
    payload.update(extra)
    return payload


class CategoryOrderTests(unittest.TestCase):
    def test_bar_categories_read_top_down_with_value_axis_at_bottom(self) -> None:
        xml = _render(_bar_payload())
        cat_ax = xml[xml.index("<c:catAx>"):xml.index("</c:catAx>")]
        val_ax = xml[xml.index("<c:valAx>"):xml.index("</c:valAx>")]
        self.assertIn('<c:orientation val="maxMin"/>', cat_ax)
        self.assertIn('<c:crosses val="autoZero"/>', cat_ax)
        self.assertIn('<c:axPos val="b"/>', val_ax)
        self.assertIn('<c:crosses val="max"/>', val_ax)

    def test_bar_reverse_false_restores_bottom_up_order(self) -> None:
        xml = _render(_bar_payload(axes={"category": {"reverse": False}}))
        cat_ax = xml[xml.index("<c:catAx>"):xml.index("</c:catAx>")]
        val_ax = xml[xml.index("<c:valAx>"):xml.index("</c:valAx>")]
        self.assertIn('<c:orientation val="minMax"/>', cat_ax)
        self.assertIn('<c:crosses val="autoZero"/>', val_ax)

    def test_column_value_axis_on_the_right_crosses_at_the_last_category(self) -> None:
        payload = _bar_payload(type="column", axes={"value": {"position": "right"}})
        xml = _render(payload)
        val_ax = xml[xml.index("<c:valAx>"):xml.index("</c:valAx>")]
        self.assertIn('<c:axPos val="r"/>', val_ax)
        self.assertIn('<c:crosses val="max"/>', val_ax)

    def test_combo_secondary_axes_keep_their_crossing(self) -> None:
        payload = {
            "type": "combo",
            "categories": ["A", "B"],
            "plots": [
                {"type": "column", "series": [{"name": "C", "values": [1, 2]}]},
                {"type": "line", "axis": "secondary", "series": [{"name": "L", "values": [3, 4]}]},
            ],
        }
        xml = _render(payload)
        crossings = [
            xml[idx:idx + 60]
            for idx in range(len(xml))
            if xml.startswith("<c:crosses", idx)
        ]
        self.assertEqual(len(crossings), 4)
        self.assertIn("autoZero", crossings[2])
        self.assertIn("max", crossings[3])

    def test_fallback_order_warning_names_the_expected_reverse(self) -> None:
        payload = _bar_payload(axes={"category": {"reverse": False}})
        fallback = (
            '<text x="10" y="20">A</text><text x="10" y="80">C</text>'
        )
        warnings = _native_chart_chrome_warnings(_marker(fallback), payload)
        self.assertTrue(any("axes.category.reverse: true" in item for item in warnings))
        self.assertEqual(_native_chart_chrome_warnings(_marker(fallback), _bar_payload()), [])


class LineMarkerTests(unittest.TestCase):
    def test_line_marker_style_writes_sized_coloured_markers(self) -> None:
        payload = {
            "type": "line",
            "line_style": "lineMarker",
            "marker_size": 10,
            "categories": ["A", "B"],
            "series": [{"name": "S", "values": [1, 2]}],
            "style": {"colors": ["#111111"]},
        }
        xml = _render(payload)
        self.assertIn('<c:marker><c:symbol val="circle"/><c:size val="8"/>', xml)
        self.assertIn('<a:srgbClr val="111111"/></a:solidFill><a:ln>', xml)

    def test_point_colors_mark_single_points_and_leave_null_bare(self) -> None:
        payload = {
            "type": "line",
            "categories": ["A", "B", "C"],
            "series": [{
                "name": "S",
                "values": [1, 2, 3],
                "point_colors": [None, None, "#C8102E"],
            }],
        }
        xml = _render(payload)
        self.assertEqual(xml.count("<c:dPt>"), 3)
        self.assertIn(
            '<c:dPt><c:idx val="2"/><c:marker><c:symbol val="circle"/>'
            '<c:spPr><a:solidFill><a:srgbClr val="C8102E"/>',
            xml,
        )
        self.assertIn('<c:dPt><c:idx val="0"/><c:marker><c:symbol val="none"/>', xml)

    def test_bar_point_colors_still_require_colours(self) -> None:
        payload = _bar_payload(series=[{"name": "S", "values": [1, 2, 3], "point_colors": [None, "#111111", "#222222"]}])
        with self.assertRaises(RuntimeError):
            _chart_data(payload)

    def test_marker_warning_fires_only_without_markers(self) -> None:
        fallback = '<circle cx="10" cy="10" r="5" fill="#C8102E"/>'
        payload = {
            "type": "line",
            "categories": ["A", "B"],
            "series": [{"name": "S", "values": [1, 2]}],
            "style": {"colors": ["#111111"]},
        }
        warnings = _native_chart_chrome_warnings(_marker(fallback), payload)
        self.assertEqual(len(warnings), 2)
        self.assertIn("point marker(s)", warnings[0])
        self.assertIn("#C8102E", warnings[1])
        payload["series"][0]["point_colors"] = [None, "#C8102E"]
        self.assertEqual(_native_chart_chrome_warnings(_marker(fallback), payload), [])


class GapAndFillTests(unittest.TestCase):
    def test_null_values_leave_gaps_in_the_cache(self) -> None:
        payload = {
            "type": "line",
            "categories": ["A", "B", "C"],
            "series": [{"name": "S", "values": [1, None, 3]}],
        }
        xml = _render(payload)
        num_cache = xml[xml.index("<c:numCache>"):xml.index("</c:numCache>")]
        self.assertIn('<c:ptCount val="3"/><c:pt idx="0"><c:v>1</c:v></c:pt><c:pt idx="2">', num_cache)
        self.assertNotIn('<c:pt idx="1">', num_cache)
        self.assertIn('<c:dispBlanksAs val="gap"/>', xml)

    def test_all_null_series_is_rejected(self) -> None:
        payload = {
            "type": "line",
            "categories": ["A", "B"],
            "series": [{"name": "S", "values": [None, None]}],
        }
        with self.assertRaises(RuntimeError):
            _chart_data(payload)

    def test_area_has_no_outline_unless_line_width_is_set(self) -> None:
        payload = {
            "type": "area",
            "categories": ["A", "B"],
            "series": [{"name": "S", "values": [1, 2], "fill_opacity": 0.14}],
            "style": {"colors": ["#111111"]},
        }
        xml = _render(payload)
        self.assertIn('<a:alpha val="14000"/>', xml)
        self.assertIn("<a:ln><a:noFill/></a:ln>", xml[xml.index("<c:ser>"):xml.index("</c:ser>")])
        payload["series"][0]["line_width"] = 3
        xml = _render(payload)
        self.assertIn('<a:ln w="28575">', xml[xml.index("<c:ser>"):xml.index("</c:ser>")])

    def test_area_warnings_report_translucency_and_overlaid_lines(self) -> None:
        fallback = (
            '<path d="M0 0 L10 10 L20 0 Z" fill="#111111" fill-opacity="0.14"/>'
            '<polyline points="0,0 10,10 20,0" fill="none" stroke="#111111"/>'
        )
        payload = {
            "type": "area",
            "categories": ["A", "B", "C"],
            "series": [{"name": "S", "values": [1, 2, 1]}],
        }
        warnings = _native_chart_chrome_warnings(_marker(fallback), payload)
        self.assertEqual(len(warnings), 2)
        self.assertIn("fill-opacity 0.14", warnings[0])
        self.assertIn('type "combo"', warnings[1])


class SpacingTests(unittest.TestCase):
    def test_explicit_gap_width_and_overlap_are_written(self) -> None:
        xml = _render(_bar_payload(type="column", gap_width=60, overlap=-20))
        self.assertIn('<c:gapWidth val="60"/><c:overlap val="-20"/>', xml)

    def test_gap_width_is_read_from_fallback_columns(self) -> None:
        payload = _bar_payload(
            type="column",
            plot_area={"x": 0, "y": 0, "width": 300, "height": 100},
        )
        fallback = (
            '<rect x="20" y="50" width="60" height="50" fill="#111111"/>'
            '<rect x="120" y="30" width="60" height="70" fill="#111111"/>'
            '<rect x="220" y="10" width="60" height="90" fill="#111111"/>'
        )
        elem = _marker(fallback)
        chart_data = _chart_data(payload)
        self.assertEqual(_inferred_bar_gap_width(elem, chart_data), 67)
        self.assertIn('<c:gapWidth val="67"/>', _render(payload, fallback))

    def test_overlap_is_read_from_clustered_bars(self) -> None:
        payload = {
            "type": "bar",
            "categories": ["A", "B"],
            "series": [{"name": "S1", "values": [1, 2]}, {"name": "S2", "values": [2, 3]}],
            "plot_area": {"x": 0, "y": 0, "width": 200, "height": 100},
        }
        fallback = (
            '<rect x="0" y="10" width="100" height="20" fill="#111111"/>'
            '<rect x="0" y="34" width="120" height="20" fill="#222222"/>'
            '<rect x="0" y="60" width="80" height="20" fill="#111111"/>'
            '<rect x="0" y="84" width="140" height="20" fill="#222222"/>'
        )
        chart_data = _chart_data(payload)
        self.assertEqual(_inferred_bar_overlap(_marker(fallback), chart_data), -20)

    def test_cross_between_follows_the_fallback_start(self) -> None:
        payload = {
            "type": "line",
            "categories": ["A", "B", "C", "D"],
            "series": [{"name": "S", "values": [1, 2, 3, 4]}],
            "plot_area": {"x": 100, "y": 0, "width": 400, "height": 100},
        }
        chart_data = _chart_data(payload)
        centred = '<polyline points="150,10 250,20 350,30 450,40" fill="none" stroke="#111111"/>'
        edged = '<polyline points="100,10 233,20 366,30 500,40" fill="none" stroke="#111111"/>'
        self.assertEqual(_inferred_cross_between(_marker(centred), chart_data), "between")
        self.assertEqual(_inferred_cross_between(_marker(edged), chart_data), "midCat")
        self.assertIn('<c:crossBetween val="midCat"/>', _render(payload, edged))
        self.assertIn('<c:crossBetween val="between"/>', _render(payload))

    def test_axis_text_colour_font_and_size_are_per_axis(self) -> None:
        payload = _bar_payload(axes={
            "category": {"color": "#1A1A1A"},
            "value": {"color": "#6E6E6E", "font_family": "Arial", "font_size": 16},
        })
        xml = _render(payload)
        cat_ax = xml[xml.index("<c:catAx>"):xml.index("</c:catAx>")]
        val_ax = xml[xml.index("<c:valAx>"):xml.index("</c:valAx>")]
        self.assertIn('<a:srgbClr val="1A1A1A"/>', cat_ax)
        self.assertIn('sz="1200"', val_ax)
        self.assertIn('<a:srgbClr val="6E6E6E"/>', val_ax)
        self.assertIn('<a:latin typeface="Arial"/>', val_ax)
        with self.assertRaises(RuntimeError):
            _chart_data(_bar_payload(axes={"value": {"color": "grey-ish"}}))

    def test_tick_marks_default_to_none_and_accept_out(self) -> None:
        self.assertIn('<c:majorTickMark val="none"/>', _render(_bar_payload()))
        xml = _render(_bar_payload(axes={"value": {"tick_marks": "out"}}))
        val_ax = xml[xml.index("<c:valAx>"):xml.index("</c:valAx>")]
        self.assertIn('<c:majorTickMark val="out"/>', val_ax)


class CompanionPlacementTests(unittest.TestCase):
    def test_svg_first_companion_sits_on_the_fallback_baseline(self) -> None:
        import json
        import re
        import tempfile

        from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes

        payload = {
            "x": 100, "y": 100, "width": 600, "height": 300,
            "name": "chart-note",
            "type": "column",
            "categories": ["A", "B"],
            "series": [{"name": "S", "values": [1, 2]}],
            "plot_area": {"x": 140, "y": 130, "width": 540, "height": 250},
            "style": {"colors": ["#111111"], "text_color": "#111111"},
            # y copied from the SVG baseline: without fallback anchoring the
            # box would start at the baseline and cover the plot top.
            "notes": [{"text": "Unit note", "x": 140, "y": 120, "width": 200, "height": 24, "font_size": 18}],
        }
        svg = (
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720">'
            '<g id="chart-note" data-pptx-replace-with="chart">'
            f'<metadata type="application/json">{json.dumps(payload)}</metadata>'
            '<rect x="140" y="130" width="540" height="250" fill="#FFFFFF"/>'
            '<text x="140" y="120" font-size="18" fill="#111111">Unit note</text>'
            '<text x="410" y="400" font-size="18" fill="#111111">A</text>'
            '<text x="410" y="400" font-size="18" fill="#111111">B</text>'
            "</g></svg>"
        )
        from svg_to_pptx.native_objects.fallback_hash import stamp_native_fallback_baseline

        root = ET.fromstring(svg)
        stamp_native_fallback_baseline(root.find(f"{{{SVG_NS}}}g"), document_root=root)
        svg = ET.tostring(root, encoding="unicode")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "01.svg"
            path.write_text(svg, encoding="utf-8")
            slide_xml, *_ = convert_svg_to_slide_shapes(
                path,
                resource_root=Path(tmp),
                native_objects=True,
            )
        note = slide_xml[slide_xml.index("Chart Note"):]
        off_y = int(re.search(r'<a:off x="\d+" y="(\d+)"/>', note).group(1))
        self.assertEqual(off_y, 102 * 9525)  # baseline 120px minus one 18px em


if __name__ == "__main__":
    unittest.main()
