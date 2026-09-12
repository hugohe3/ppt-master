"""Regressions from the Thai jasmine-rice deck dogfood (2026-09-12)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import preset_shape_svg  # noqa: E402
import svg_position_calculator as calc  # noqa: E402
import text_measure  # noqa: E402
from svg_to_pptx.drawingml.theme_fonts import _complex_theme_scripts  # noqa: E402


class ScriptRateSampleTests(unittest.TestCase):
    def test_thai_outline_yields_a_thai_sample(self) -> None:
        samples = text_measure._script_rate_samples(
            ["ข้าวหอมมะลิ: จากนาสู่โลก ปีการตลาด 2568/69", "ขึ้นทะเบียนสิ่งบ่งชี้ทางภูมิศาสตร์"]
        )
        self.assertIn("Thai", samples)
        self.assertNotIn("Latin", samples)
        self.assertTrue(all("฀" <= ch <= "๿" for ch in samples["Thai"]))

    def test_latin_and_cjk_text_add_no_script_column(self) -> None:
        self.assertEqual(text_measure._script_rate_samples(["Clear slides 天地玄黄 2024"]), {})


class BatchAdjustTests(unittest.TestCase):
    ITEM = {"preset": "chevron", "id": "c1", "frame": [0, 0, 120, 60], "fill": "#123456"}

    def test_name_formula_strings_are_accepted(self) -> None:
        for field, value in (("adjust", ["adj=val 32000"]), ("adjust", "adj=val 32000"),
                             ("adjustments", ["adj=val 32000"]), ("adjustments", {"adj": "val 32000"})):
            fragments = preset_shape_svg._render_batch_items([{**self.ITEM, field: value}])
            self.assertEqual(len(fragments), 1, field)
            self.assertIn("32000", fragments[0])

    def test_wrong_shape_names_both_forms(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            preset_shape_svg._render_batch_items([{**self.ITEM, "adjustments": 5}])
        self.assertIn("NAME=FORMULA", str(ctx.exception))


class ThemeScriptTests(unittest.TestCase):
    def test_complex_scripts_follow_the_language(self) -> None:
        self.assertEqual(_complex_theme_scripts("th-TH"), ("Thai",))
        self.assertEqual(_complex_theme_scripts("hi-IN"), ("Deva",))
        self.assertEqual(_complex_theme_scripts("ar-SA"), ("Arab",))
        self.assertEqual(_complex_theme_scripts("he-IL"), ("Hebr",))
        self.assertEqual(_complex_theme_scripts("zh-CN"), ())


class SlotMidpointTests(unittest.TestCase):
    def test_points_sit_at_slot_centres(self) -> None:
        coord = calc.CoordinateSystem("ppt169", calc.ChartArea(152, 378, 920, 596))
        points = calc.LineChartCalculator(coord).calculate([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], (1, 5), (0, 7))
        xs = [p.svg_x for p in calc.slot_midpoint_points(points, coord)]
        self.assertEqual(xs, [228.8, 382.4, 536.0, 689.6, 843.2])


if __name__ == "__main__":
    unittest.main()
