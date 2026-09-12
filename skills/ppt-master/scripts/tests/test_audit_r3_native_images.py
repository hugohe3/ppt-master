"""Regressions for round-three native object, calculator, and image findings."""

from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import image_treat  # noqa: E402
import slice_images  # noqa: E402
import svg_position_calculator as position_calculator  # noqa: E402
from svg_to_pptx.native_objects.chart_data import _chart_data  # noqa: E402
from svg_to_pptx.native_objects.chart_xml import _chart_xml  # noqa: E402


class OpaqueImageDerivativeTests(unittest.TestCase):
    def _derive(self, image: Image.Image, *, transparent: bool) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            images = project / "images"
            images.mkdir()
            source = images / "source.png"
            image.save(source)
            original = source.read_bytes()
            output = images / "derived.jpg"
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = image_treat.main([
                    str(project), source.name, "--output", output.name, "--fit", "64x40",
                ])
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(result, 1 if transparent else 0, stderr.getvalue())
            if transparent:
                self.assertFalse(output.exists())
                self.assertIn("JPEG output cannot hold the source's transparency", stderr.getvalue())
                self.assertEqual(sorted(p.name for p in images.iterdir()), [source.name])
            else:
                with Image.open(output) as derivative:
                    self.assertEqual(derivative.format, "JPEG")
                    self.assertEqual(derivative.mode, "RGB")
                    self.assertEqual(derivative.size, (64, 40))

    def test_rgb_and_opaque_alpha_modes_allow_jpeg(self) -> None:
        for mode, color in (("RGB", (30, 80, 120)), ("RGBA", (30, 80, 120, 255)), ("LA", (80, 255))):
            with self.subTest(mode=mode), Image.new(mode, (128, 80), color) as image:
                self._derive(image, transparent=False)

    def test_actual_alpha_pixels_refuse_jpeg_without_output(self) -> None:
        for mode, color in (("RGBA", (30, 80, 120, 255)), ("LA", (80, 255))):
            for alpha in (0, 254):
                with self.subTest(mode=mode, alpha=alpha), Image.new(mode, (128, 80), color) as image:
                    image.putpixel((64, 40), (*color[:-1], alpha))
                    self._derive(image, transparent=True)

    def test_palette_transparency_depends_on_used_pixels(self) -> None:
        for transparency in (1, bytes([255, 0] + [255] * 254), bytes([255, 254] + [255] * 254)):
            for used in (False, True):
                with self.subTest(transparency=repr(transparency)[:32], used=used):
                    with Image.new("P", (128, 80), 0) as image:
                        image.putpalette([30, 80, 120, 80, 120, 160] + [0] * 762)
                        image.info["transparency"] = transparency
                        if used:
                            image.putpixel((64, 40), 1)
                        self._derive(image, transparent=used)


class ChartSeriesLineStyleTests(unittest.TestCase):
    def _marker_symbols(self, payload: dict) -> list[str]:
        marker = ET.fromstring('<g xmlns="http://www.w3.org/2000/svg" id="chart"/>')
        xml = _chart_xml(
            marker, payload, chart_rels_id="rId1", chart_data=_chart_data(payload),
            chart_bounds=(0, 0, 12192000, 6858000),
        )
        root = ET.fromstring(xml)
        ns = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
        return [node.get("val") for node in root.findall(".//c:marker/c:symbol", ns)]

    def test_non_combo_typed_series_cannot_bypass_line_style_rejection(self) -> None:
        for type_field in (None, "type", "chart_type"):
            for style_field in ("line_style", "lineStyle"):
                with self.subTest(type_field=type_field, style_field=style_field):
                    series = {"name": "S", "values": [1, 2], style_field: "lineMarker"}
                    if type_field:
                        series[type_field] = "line"
                    with self.assertRaises(RuntimeError) as caught:
                        _chart_data({"type": "line", "categories": ["A", "B"], "series": [series]})
                    self.assertEqual(
                        str(caught.exception),
                        "Native PPTX chart series[].line_style is not a series option; "
                        "set line_style on the chart root (combo: on the plot or typed series)",
                    )

    def test_typed_combo_line_markers_survive_normalization_and_xml(self) -> None:
        for type_field in ("type", "chart_type"):
            for style_field in ("line_style", "lineStyle"):
                with self.subTest(type_field=type_field, style_field=style_field):
                    payload = {
                        "type": "combo", "categories": ["A", "B"],
                        "series": [
                            {type_field: "column", "name": "C", "values": [1, 2]},
                            {type_field: "line", "name": "L", "values": [2, 3], style_field: "lineMarker"},
                        ],
                    }
                    self.assertEqual(_chart_data(payload)["plots"][1]["line_style"], "lineMarker")
                    symbols = self._marker_symbols(payload)
                    self.assertTrue(symbols)
                    self.assertNotIn("none", symbols)

    def test_root_and_combo_plot_line_markers_remain_supported(self) -> None:
        line = {
            "type": "line", "line_style": "lineMarker", "categories": ["A", "B"],
            "series": [{"name": "S", "values": [1, 2]}],
        }
        combo = {"type": "combo", "categories": ["A", "B"], "plots": [line]}
        for payload in (line, combo):
            with self.subTest(chart_type=payload["type"]):
                symbols = self._marker_symbols(payload)
                self.assertTrue(symbols)
                self.assertNotIn("none", symbols)


class StrictAlphaMarginRegressionTests(unittest.TestCase):
    def test_a13_pure_key_soft_shadow_and_glow_preserve_partial_alpha(self) -> None:
        for key in ((255, 0, 0), (0, 255, 0), (0, 0, 255)):
            for foreground in ((0, 0, 0), (255, 255, 255)):
                with self.subTest(key=key, foreground=foreground), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    sheet = Image.new("RGB", (120, 120), key)
                    for y in range(120):
                        for x in range(120):
                            distance = math.hypot(x - 60, y - 60)
                            alpha = 255 if distance < 9 else round(128 * max(0, 32 - distance) / 23)
                            pixel = tuple(round((base * (255 - alpha) + color * alpha) / 255)
                                          for base, color in zip(key, foreground))
                            sheet.putpixel((x, y), pixel)
                    source = root / "sheet.png"
                    sheet.save(source)
                    expected = slice_images.slice_sheet(
                        source, 1, 1, root / "normal", trim=True, alpha=True, bg=key,
                    )
                    actual = slice_images.slice_sheet(
                        source, 1, 1, root / "strict", trim=True, alpha=True,
                        strict_alpha=True, bg=key,
                    )
                    with Image.open(expected[0]) as normal, Image.open(actual[0]) as strict:
                        self.assertEqual(strict.size, normal.size)
                        self.assertEqual(strict.tobytes(), normal.tobytes())
                        histogram = strict.getchannel("A").histogram()
                        self.assertGreater(sum(histogram[20:151]) / (strict.width * strict.height), 0.15)
                        self.assertGreater(histogram[255], 0)

    def test_a13_off_key_ground_and_inner_margin_haze_fail_without_output(self) -> None:
        for fault in ("off_key_ground", "inner_margin_noise"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                key = (0, 0, 255)
                sheet = Image.new("RGB", (120, 120), key)
                draw = ImageDraw.Draw(sheet)
                if fault == "off_key_ground":
                    draw.rectangle((0, 0, 119, 119), fill=(3, 74, 244))
                else:
                    # All four outer 1% edges are pure; the required 10%
                    # margins contain haze well beyond the key tolerance.
                    draw.rectangle((4, 4, 115, 115), fill=(0, 0, 180))
                draw.rectangle((50, 50, 70, 70), fill=(255, 255, 255))
                source = root / "sheet.png"
                sheet.save(source)
                output = root / "output"
                stderr = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                    result = slice_images.main([
                        str(source), "--grid", "1x1", "--names", "element",
                        "--trim", "--alpha", "--strict-alpha", "--bg", "#0000FF",
                        "--tolerance", "62", "--output", str(output),
                    ])
                self.assertEqual(result, 1)
                self.assertIn("four 10% key-only margins", stderr.getvalue())
                self.assertIn("measured ground colour", stderr.getvalue())
                self.assertFalse((output / "element.png").exists())


class CalculatorFiniteInputTests(unittest.TestCase):
    def _run_calculator(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = position_calculator.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_nonfinite_scalar_parameters_fail_before_calculation(self):
        cases = (
            ('bar', '--bar-width', ['--data', 'A:10,B:20']),
            ('bar', '--gap-width', ['--data', 'A:10,B:20']),
            ('pie', '--radius', ['--data', 'A:10,B:20']),
            ('pie', '--inner-radius', ['--data', 'A:10,B:20']),
            ('pie', '--start-angle', ['--data', 'A:10,B:20']),
            ('radar', '--radius', ['--data', 'A:10,B:20,C:30']),
            ('radar', '--max-value', ['--data', 'A:10,B:20,C:30']),
            ('grid', '--padding', ['--rows', '2', '--cols', '3']),
            ('grid', '--gap', ['--rows', '2', '--cols', '3']),
        )
        for value in ('NaN', 'Infinity', '-Infinity'):
            for chart, option, required in cases:
                with self.subTest(chart=chart, option=option, value=value):
                    code, stdout, stderr = self._run_calculator(
                        ['calc', chart, *required, f'{option}={value}']
                    )
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, '')
                    self.assertIn(option, stderr)
                    self.assertIn('must be finite', stderr)
            with self.subTest(command='validate', value=value):
                code, stdout, stderr = self._run_calculator(
                    ['validate', 'unused.svg', '--extract', f'--tolerance={value}']
                )
                self.assertNotEqual(code, 0)
                self.assertEqual(stdout, '')
                self.assertIn('--tolerance must be finite', stderr)

    def test_nonfinite_tuple_parameters_identify_component(self):
        cases = (
            ('bar', '--area', ['--data', 'A:10,B:20'], '0,0,{},100', 2),
            ('bar', '--value-range', ['--data', 'A:10,B:20'], '0,{}', 1),
            ('pie', '--center', ['--data', 'A:10,B:20'], '{},100', 0),
            ('radar', '--center', ['--data', 'A:10,B:20,C:30'], '100,{}', 1),
            ('line', '--area', ['--data', 'A:10,B:20'], '0,{},100,100', 1),
            ('line', '--x-range', ['--data', 'A:10,B:20'], '0,{}', 1),
            ('line', '--y-range', ['--data', 'A:10,B:20'], '0,{}', 1),
            ('grid', '--area', ['--rows', '2', '--cols', '3'], '0,0,100,{}', 3),
        )
        for value in ('NaN', 'Infinity', '-Infinity'):
            for chart, option, required, template, index in cases:
                with self.subTest(chart=chart, option=option, value=value):
                    code, stdout, stderr = self._run_calculator(
                        ['calc', chart, *required, f'{option}={template.format(value)}']
                    )
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, '')
                    self.assertIn(f'{option}[{index}] must be finite', stderr)

    def test_nonfinite_data_identifies_point_without_category_fallback(self):
        for value in ('NaN', 'Infinity', '-Infinity'):
            for chart in ('bar', 'pie', 'radar', 'line'):
                with self.subTest(chart=chart, value=value):
                    code, stdout, stderr = self._run_calculator(
                        ['calc', chart, '--data', f'A:10,B:{value},C:30']
                    )
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, '')
                    self.assertIn("--data point 2 ('B')", stderr)
                    self.assertIn('must be finite', stderr)
            for data in (f'1:10,{value}:20', f'A:10,{value}:20'):
                with self.subTest(data=data):
                    code, stdout, stderr = self._run_calculator(['calc', 'line', '--data', data])
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, '')
                    self.assertIn('--data point 2 x must be finite', stderr)

    def test_finite_inputs_preserve_gap_boundaries_and_chart_modes(self):
        cases = [
            ['calc', 'bar', '--data', 'A:10,B:20', '--gap-width=0'],
            ['calc', 'bar', '--data', 'A:10,B:20', '--gap-width=150', '--horizontal'],
            ['calc', 'pie', '--data', 'A:10,B:20', '--center=100,100', '--radius=50'],
            ['calc', 'radar', '--data', 'A:10,B:20,C:30', '--max-value=40'],
            ['calc', 'line', '--data', 'A:10,B:20', '--slot-midpoints'],
            ['calc', 'line', '--data', '0:10,1:20', '--x-range=0,1', '--y-range=0,30'],
            ['calc', 'grid', '--rows=2', '--cols=3', '--padding=0', '--gap=10'],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, stdout, stderr = self._run_calculator(argv)
                self.assertEqual(code, 0, stderr)
                self.assertTrue(stdout)
                self.assertNotRegex(stdout.lower(), r'\b(?:nan|inf|infinity)\b')

    def test_nonfinite_json_config_and_expected_coordinates_identify_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_file = root / 'config.json'
            expected_file = root / 'expected.json'
            svg_file = root / 'chart.svg'
            svg_file.write_text('<svg><rect id="bar_a" x="0" y="10"/></svg>', encoding='utf-8')
            for value in (float('nan'), float('inf'), float('-inf')):
                configs = (
                    ({'type': 'bar', 'data': {'A': value}}, 'config.data.A'),
                    ({'type': 'pie', 'data': {'A': 10}, 'radius': value}, 'config.radius'),
                    ({'type': 'line', 'data': [[1, 10], [2, value]]}, 'config.data[1][1]'),
                    ({'type': 'custom_line', 'values': [10, value]}, 'config.values[1]'),
                )
                for config, location in configs:
                    with self.subTest(config=config):
                        config_file.write_text(json.dumps(config), encoding='utf-8')
                        code, stdout, stderr = self._run_calculator(['from-json', str(config_file)])
                        self.assertNotEqual(code, 0)
                        self.assertEqual(stdout, '')
                        self.assertIn(f'{location} must be finite', stderr)
                expected_file.write_text(json.dumps({'bar_a': {'x': value}}), encoding='utf-8')
                code, stdout, stderr = self._run_calculator(
                    ['validate', str(svg_file), '--expected', str(expected_file)]
                )
                self.assertNotEqual(code, 0)
                self.assertEqual(stdout, '')
                self.assertIn('--expected.bar_a.x must be finite', stderr)

    def test_interactive_nonfinite_values_exit_nonzero(self):
        for answers, location in (
            (['1', 'A:nan', ''], '--data point 1'),
            (['2', 'A:10', '', 'inf'], 'radius'),
            (['3', 'A:10,B:20,C:30', '100,-Infinity', ''], 'center[1]'),
            (['4', 'A:10,B:nan', ''], '--data point 2'),
            (['5', 'nan'], 'rows'),
            (['6', '-inf'], 'base_x'),
        ):
            with self.subTest(answers=answers), mock.patch('builtins.input', side_effect=answers):
                code, stdout, stderr = self._run_calculator(['interactive'])
                self.assertNotEqual(code, 0)
                self.assertIn(location, stderr)
                self.assertIn('must be finite', stderr)


class NativeTableMixedRunAuditTests(unittest.TestCase):
    def _table_svg(self, red_text: str, *, mismatch: str = "", column: int = 0,
                   header: bool = False, split_runs: bool = False) -> str:
        import json
        from xml.etree import ElementTree as ET

        first_run = {"text": "AAA", "color": "#000000", "bold": False}
        red_run = {"text": red_text, "color": "#FF0000", "bold": True}
        if mismatch == "bold":
            red_run["bold"] = False
        elif mismatch == "color":
            red_run["color"] = "#000000"
        elif mismatch == "swapped":
            first_run.update(color="#FF0000", bold=True)
            red_run.update(color="#000000", bold=False)
        runs = [first_run, red_run]
        if split_runs:
            runs = [{**first_run, "text": "A"}, {**first_run, "text": "AA"}, red_run]
        cell = {
            "color": "#000000", "bold": False, "align": "l",
            "paragraphs": [{"runs": runs}],
        }
        row = [cell, {"text": "OTHER", "color": "#000000", "align": "l"}]
        if column == 1:
            row.reverse()
        payload = {
            "schema": "ppt-master.semantic-table.v2",
            "x": 100, "y": 100, "width": 600, "height": 100,
            "header_rows": 1 if header else 0,
            "column_widths": [1, 1],
            "style": {"body_text": "#000000", "font_family": "Arial", "font_size": 20},
            "rows": [row],
        }
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
            '<g id="table" data-pptx-replace-with="table">'
            '<metadata type="application/json"/>'
            '<rect x="100" y="100" width="600" height="100" fill="none" stroke="#000000"/>'
            '<line x1="400" y1="100" x2="400" y2="200" stroke="#000000"/>'
            f'<text x="{115 + 300 * column}" y="150" fill="#000000" font-size="20" font-family="Arial">'
            f'AAA<tspan fill="#FF0000" font-weight="bold">{red_text}</tspan></text>'
            f'<text x="{415 - 300 * column}" y="150" fill="#000000" font-size="20" '
            'font-family="Arial">OTHER</text>'
            '</g></svg>'
        )
        root[0][0].text = json.dumps(payload)
        return ET.tostring(root, encoding="unicode")

    def _table_pipeline(self, project: Path, svg: str):
        import subprocess
        import sys

        scripts = Path(__file__).resolve().parents[1]
        output = project / "native.pptx"
        svg_dir = project / "svg_output"
        svg_dir.mkdir(parents=True)
        (svg_dir / "01.svg").write_text(svg, encoding="utf-8")
        commands = [
            ["stamp_native_fallbacks.py", str(svg_dir), "--write"],
            ["svg_quality_checker.py", str(project), "--canonical-authoring", "--stage", "final",
             "--json", "--quick-generate"],
            ["svg_to_pptx.py", str(project), "--quick-generate", "--native-charts-and-tables",
             "-o", str(output)],
        ]
        results = []
        for script, *arguments in commands:
            result = subprocess.run(
                [sys.executable, "-B", str(scripts / script), *arguments],
                capture_output=True, text=True, check=False,
            )
            results.append(result)
        for result in results[:2]:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return output, results[-1]

    def test_a06_mixed_runs_pass_stamp_checker_and_native_export_at_any_length(self) -> None:
        import tempfile
        import zipfile
        from xml.etree import ElementTree as ET

        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        with tempfile.TemporaryDirectory() as tmp:
            for length in (1, 10):
                with self.subTest(length=length):
                    red_text = "B" * length
                    output, result = self._table_pipeline(
                        Path(tmp) / str(length), self._table_svg(red_text)
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    with zipfile.ZipFile(output) as package:
                        slide = ET.fromstring(package.read("ppt/slides/slide1.xml"))
                    cell = slide.find(".//a:tbl/a:tr/a:tc", ns)
                    self.assertIsNotNone(cell)
                    actual = [
                        (run.find("a:t", ns).text, run.find("a:rPr", ns).get("b"),
                         run.find("a:rPr/a:solidFill/a:srgbClr", ns).get("val"))
                        for run in cell.findall(".//a:r", ns)
                    ]
                    self.assertEqual(actual, [("AAA", "0", "000000"), (red_text, "1", "FF0000")])

    def test_a06_missing_minority_bold_or_color_still_blocks_native_export(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for mismatch in ("bold", "color", "swapped"):
                with self.subTest(mismatch=mismatch):
                    output, result = self._table_pipeline(
                        Path(tmp) / mismatch, self._table_svg("B", mismatch=mismatch)
                    )
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("not projected", result.stdout + result.stderr)
                    self.assertFalse(output.exists())

    def test_a06_header_and_body_run_parity_share_effective_styles(self) -> None:
        from xml.etree import ElementTree as ET
        from svg_to_pptx.native_objects import native_object_projection_warnings

        for header, column in ((True, 0), (False, 1)):
            for length in (1, 10):
                with self.subTest(header=header, column=column, length=length):
                    root = ET.fromstring(self._table_svg(
                        "B" * length, header=header, column=column, split_runs=True
                    ))
                    warnings = native_object_projection_warnings(root[0], document_root=root)
                    self.assertEqual(warnings, [])
                    root = ET.fromstring(self._table_svg(
                        "B" * length, header=header, column=column, mismatch="color"
                    ))
                    warnings = native_object_projection_warnings(root[0], document_root=root)
                    self.assertTrue(any("not projected" in warning for warning in warnings), warnings)

    def test_a06_repeated_paragraph_text_matches_each_style_occurrence(self) -> None:
        from xml.etree import ElementTree as ET
        from svg_to_pptx.native_objects import native_object_projection_warnings

        root = ET.fromstring(self._table_svg("B"))
        marker = root[0]
        payload = json.loads(marker[0].text)
        payload["rows"][0][0]["paragraphs"] = [
            {"runs": [{"text": "SAME", "color": "#000000", "bold": False}]},
            {"runs": [{"text": "SAME", "color": "#FF0000", "bold": True}]},
        ]
        marker[0].text = json.dumps(payload)
        first_text = marker[3]
        first_text.remove(first_text[0])
        first_text.text = "SAME"
        second_text = ET.SubElement(marker, first_text.tag, {
            **first_text.attrib, "y": "175", "fill": "#FF0000", "font-weight": "bold",
        })
        second_text.text = "SAME"
        self.assertEqual(native_object_projection_warnings(marker, document_root=root), [])
        payload["rows"][0][0]["paragraphs"][1]["runs"][0]["color"] = "#000000"
        marker[0].text = json.dumps(payload)
        warnings = native_object_projection_warnings(marker, document_root=root)
        self.assertTrue(any("color #FF0000" in warning for warning in warnings), warnings)
        payload["rows"][0][0]["paragraphs"][1]["runs"][0]["color"] = "#FF0000"
        payload["rows"][0][0]["paragraphs"][0]["runs"][0]["color"] = "#FF0000"
        marker[0].text = json.dumps(payload)
        warnings = native_object_projection_warnings(marker, document_root=root)
        self.assertTrue(any("color #000000" in warning for warning in warnings), warnings)

    def test_a06_header_text_keeps_exported_body_color_defaults(self) -> None:
        from xml.etree import ElementTree as ET
        from svg_to_pptx.native_objects import native_object_projection_warnings

        for body_color in (None, "#123456"):
            with self.subTest(body_color=body_color):
                root = ET.fromstring(self._table_svg("B", header=True))
                marker = root[0]
                payload = json.loads(marker[0].text)
                payload["rows"] = [[{"text": "AAA", "align": "l"}, {"text": "OTHER", "align": "l"}]]
                if body_color is None:
                    payload["style"].pop("body_text")
                else:
                    payload["style"]["body_text"] = body_color
                marker[0].text = json.dumps(payload)
                marker[3].remove(marker[3][0])
                marker[3].set("fill", body_color or "#1F2937")
                marker[4].set("fill", body_color or "#1F2937")
                self.assertEqual(native_object_projection_warnings(marker, document_root=root), [])
