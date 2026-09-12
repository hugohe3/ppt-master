#!/usr/bin/env python3
"""Regressions for third-round text, font, and language audit fixes."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_to_pptx import convert_svg_to_slide_shapes  # noqa: E402
from svg_to_pptx.drawingml.theme_fonts import (  # noqa: E402
    MasterTextStyleSpec,
    apply_theme_font_spec,
    load_theme_font_spec,
)
from svg_to_pptx.pptx_package.builder import (  # noqa: E402
    _apply_template_text_language,
    create_pptx_with_native_svg,
)
from text_measure import measure_text, wrap_text  # noqa: E402

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
THAI_SAMPLE = "ข้าวหอมมะลิไทยคุณภาพดีและส่งออกทั่วโลก"
ARABIC_SAMPLE = "مرحبا بكم في عالم القهوة العربية والتقاليد الجميلة"


class WordControlWrappingTests(unittest.TestCase):
    def test_joining_controls_keep_oversized_words_intact(self) -> None:
        words = (
            "क्\u200dषत्रिय", "می\u200cروم", "हिन्\u200dदी",
            "ab\u034fcd", "ab\u2060cd", "क्षत्रिय", "میروم",
            "ن\u2060\u064eص", "क\u2060\u093fताब",
        )
        for word in words:
            with self.subTest(word=word):
                width = measure_text(word, size=20, family="Arial")
                lines, widths, oversized = wrap_text(
                    word, size=20, family="Arial", max_width=width * 0.7,
                )
                self.assertEqual(lines, [word])
                self.assertEqual(widths, [width])
                self.assertEqual(oversized, [(word, width)])

    def test_spaces_and_nbsp_remain_word_boundaries(self) -> None:
        width = measure_text("alpha", size=20, family="Arial")
        for separator in (" ", "\u00a0", "\t"):
            with self.subTest(separator=separator):
                lines, widths, oversized = wrap_text(
                    "alpha" + separator + "beta", size=20,
                    family="Arial", max_width=width,
                )
                self.assertEqual(lines, ["alpha", "beta"])
                self.assertEqual(oversized, [])
                self.assertTrue(all(value <= width for value in widths))

    def test_thai_and_cjk_keep_unspaced_wrapping(self) -> None:
        for text in (THAI_SAMPLE, "中文正文需要正常换行保持文字完整"):
            with self.subTest(text=text):
                lines, widths, oversized = wrap_text(
                    text, size=20, family="Arial", max_width=100,
                )
                self.assertGreater(len(lines), 1)
                self.assertEqual("".join(lines), text)
                self.assertEqual(oversized, [])
                self.assertTrue(all(width <= 100 for width in widths))


class ThemeScriptOverrideTests(unittest.TestCase):
    def test_explicit_script_selects_the_actual_theme_font(self) -> None:
        cases = (
            ("pa-Arab-PK", "Arab"),
            ("pa-Guru-IN", "Guru"),
            ("pa-IN", "Guru"),
            ("hi-Latn", "Latn"),
            ("pa-x-Arab", "Guru"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "spec_lock.md").write_text(
                "# Spec Lock\n## typography\n- font_family: Tahoma\n"
                "- title_family: Tahoma\n- body_family: Tahoma\n",
                encoding="utf-8",
            )
            theme_path = project / "ppt" / "theme" / "theme1.xml"
            theme_path.parent.mkdir(parents=True)
            for language, selected in cases:
                with self.subTest(language=language):
                    theme_path.write_text(
                        f'<a:theme xmlns:a="{NS["a"]}"><a:themeElements>'
                        '<a:fontScheme name="Office">'
                        + "".join(
                            f'<a:{role}><a:latin typeface="Calibri"/>'
                            '<a:ea typeface=""/><a:cs typeface=""/>'
                            '<a:font script="Arab" typeface="Arial"/>'
                            '<a:font script="Guru" typeface="Raavi"/>'
                            '<a:font script="Deva" typeface="Mangal"/>'
                            f'</a:{role}>'
                            for role in ("majorFont", "minorFont")
                        )
                        + '</a:fontScheme></a:themeElements></a:theme>',
                        encoding="utf-8",
                    )
                    spec = load_theme_font_spec(project, language)
                    self.assertIsNotNone(spec)
                    self.assertEqual(spec.cs_scripts, (selected,))
                    apply_theme_font_spec(project, spec)
                    root = ET.parse(theme_path).getroot()
                    for role in ("majorFont", "minorFont"):
                        collection = root.find(f".//a:{role}", NS)
                        fonts = {
                            node.get("script"): node.get("typeface")
                            for node in collection.findall("a:font", NS)
                        }
                        for script, original in (
                            ("Arab", "Arial"), ("Guru", "Raavi"), ("Deva", "Mangal"),
                        ):
                            self.assertEqual(
                                fonts[script], "Tahoma" if script == selected else original,
                            )


class ExportedRunLanguageTests(unittest.TestCase):
    def test_latin_script_tags_survive_actual_svg_conversion(self) -> None:
        cases = (
            ("sr-Latn-RS", "Dobro jutro", "sr-Latn-RS"),
            ("zh-Latn", "Ni hao", "zh-Latn"),
            ("sr-Cyrl-RS", "Добро јутро", "sr-Cyrl-RS"),
            ("vi-VN", "Xin chào", "vi-VN"),
            ("zh-CN", "2026 AI", "en-US"),
            ("ar-SA", "2026 AI", "en-US"),
            ("sr-Cyrl-RS", "Dobro jutro", "en-US"),
            ("sr-x-Latn", "Dobro jutro", "en-US"),
            ("zh-CN", "2026 !", "zh-CN"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            svg = folder / "01.svg"
            for language, content, expected in cases:
                with self.subTest(language=language, content=content):
                    svg.write_text(
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                        '<text x="100" y="140" font-size="42" '
                        f'font-family="Arial" fill="#111111">{content}</text></svg>',
                        encoding="utf-8",
                    )
                    xml, *_ = convert_svg_to_slide_shapes(
                        svg, resource_root=folder, verbose=False, primary_language=language,
                    )
                    root = ET.fromstring(xml)
                    runs = root.findall(".//a:r", NS)
                    self.assertTrue(runs)
                    self.assertEqual("".join(run.findtext("a:t", namespaces=NS) for run in runs), content)
                    self.assertEqual(
                        {run.find("a:rPr", NS).get("lang") for run in runs}, {expected},
                    )


class StructuredTextLanguageTests(unittest.TestCase):
    def test_structured_package_keeps_authored_runs_and_localizes_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            svg = folder / "01.svg"
            elements = []
            expected = {}
            for index, layer in enumerate(("master", "layout", "slide")):
                metadata = (
                    f' data-pptx-layer="{layer}" data-pptx-editable="false"'
                    if layer != "slide" else ""
                )
                for offset, (content, language) in enumerate((
                    (f"{layer.upper()} ENGLISH", "en-US"), (f"中文正文{index}", "zh-CN"),
                )):
                    expected[content] = (layer, language)
                    elements.append(
                        f'<text id="{layer}-{offset}" x="100" y="{70 + index * 150 + offset * 50}" '
                        f'font-size="24" fill="#000000"{metadata}>{content}</text>'
                    )
            elements.append(
                '<g id="title-slot" data-pptx-placeholder="title" '
                'data-pptx-bounds="100 570 900 60" data-pptx-idx="10">'
                '<text x="100" y="610" font-size="30" fill="#000000" '
                'data-pptx-carrier="true">占位符正文</text></g>'
            )
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
                'font-family="Arial" data-pptx-master="master-default" '
                'data-pptx-master-name="Default Master" data-pptx-layout="content" '
                'data-pptx-layout-name="Content">' + "".join(elements) + '</svg>',
                encoding="utf-8",
            )
            pptx = folder / "structured.pptx"
            self.assertTrue(create_pptx_with_native_svg(
                [svg], pptx, resource_root=folder, pptx_structure="structured",
                master_text_style_spec=MasterTextStyleSpec(3000, 1800),
                primary_language="zh-CN", verbose=False,
            ))
            seen = set()
            default_count = 0
            with zipfile.ZipFile(pptx) as package:
                for part in package.namelist():
                    if not part.endswith(".xml"):
                        continue
                    layer = next((name for prefix, name in (
                        ("ppt/slideMasters/", "master"), ("ppt/slideLayouts/", "layout"),
                        ("ppt/slides/", "slide"),
                    ) if part.startswith(prefix)), None)
                    if layer is None and part != "ppt/presentation.xml":
                        continue
                    root = ET.fromstring(package.read(part))
                    for run in root.findall(".//a:r", NS):
                        content = run.findtext("a:t", namespaces=NS)
                        if content in expected:
                            wanted_layer, wanted_language = expected[content]
                            self.assertEqual(layer, wanted_layer)
                            self.assertEqual(run.find("a:rPr", NS).get("lang"), wanted_language)
                            seen.add(content)
                    if layer == "slide":
                        continue
                    for tag in ("defRPr", "endParaRPr"):
                        for node in root.findall(f".//a:{tag}", NS):
                            self.assertEqual(node.get("lang"), "zh-CN", (part, tag))
                            default_count += 1
            self.assertEqual(seen, set(expected))
            self.assertGreater(default_count, 0)

    def test_empty_template_placeholders_receive_the_deck_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for directory, part_name, tag in (
                ("slideMasters", "slideMaster1.xml", "sldMaster"),
                ("slideLayouts", "slideLayout1.xml", "sldLayout"),
            ):
                path = folder / "ppt" / directory / part_name
                path.parent.mkdir(parents=True)
                path.write_text(
                    f'<p:{tag} xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">'
                    '<p:cSld><p:spTree><p:sp><p:nvSpPr><p:cNvPr id="2" name="Empty"/>'
                    '<p:cNvSpPr/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
                    '<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle><a:lvl1pPr>'
                    '<a:defRPr lang="en-US"/></a:lvl1pPr></a:lstStyle><a:p>'
                    '<a:r><a:rPr lang="en-US"/><a:t> </a:t></a:r>'
                    '<a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>'
                    f'</p:spTree></p:cSld></p:{tag}>',
                    encoding="utf-8",
                )
            _apply_template_text_language(folder, "zh-CN")
            for path in (folder / "ppt").glob("*/*.xml"):
                root = ET.parse(path).getroot()
                for tag in ("rPr", "defRPr", "endParaRPr"):
                    properties = root.findall(f".//a:{tag}", NS)
                    self.assertTrue(properties)
                    self.assertTrue(all(node.get("lang") == "zh-CN" for node in properties))
                original = path.read_bytes()
                _apply_template_text_language(folder, "zh-CN")
                self.assertEqual(path.read_bytes(), original)


class IncrementalCalibrationTests(unittest.TestCase):
    def _run_calibration(self, project: Path, *options: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS_DIR / "text_measure.py"),
             "calibrate", str(project), *options],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _read_calibration(self, project: Path) -> dict:
        return json.loads((project / "validation" / "text_calibration.json").read_text(encoding="utf-8"))

    def test_quick_and_default_keep_prior_role_weight_samples_and_rates(self) -> None:
        for default in (False, True):
            with self.subTest(default=default), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                if default:
                    (project / "spec_lock.md").write_text(
                        "# Spec Lock\n\n## typography\n- font_family: Arial\n"
                        "- body_family: Arial\n- title_family: Arial\n- body: 20\n- title: 40\n",
                        encoding="utf-8",
                    )
                first_run = self._run_calibration(
                    project, "--role", "title:Arial:40:bold", "--sample", THAI_SAMPLE, "--json",
                )
                first = json.loads(first_run.stdout)
                second_run = self._run_calibration(
                    project, "--role", "body:Arial:20:bold" if default else "body:Arial:20",
                )
                second = self._read_calibration(project)
                self.assertEqual(second["roles"]["title"], first["roles"]["title"])
                self.assertEqual(second["script_samples"], first["script_samples"])
                self.assertIn("Thai", second["script_samples"])
                self.assertEqual(second["roles"]["title"]["weight"], "bold")
                self.assertEqual(second["roles"]["body"]["weight"], "bold" if default else "normal")
                self.assertTrue(all(
                    row["script_clusters_per_100px"]["Thai"] > 0
                    for row in second["roles"].values()
                ))
                self.assertIn("Thai ≈clusters/100px", second_run.stdout)
                notes = " ".join(second["notes"])
                self.assertIn("title", notes)
                self.assertIn("bold", notes)
                self.assertNotIn("every role is measured at normal weight", notes)
                if default:
                    self.assertIn("body", notes)

    def test_incremental_default_notes_follow_the_saved_role_family(self) -> None:
        for explicit_family in (None, "Georgia"):
            with self.subTest(explicit_family=explicit_family), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                (project / "spec_lock.md").write_text(
                    "# Spec Lock\n\n## typography\n- font_family: Arial\n"
                    "- body_family: Arial\n- body: 20\n- hero: 48\n",
                    encoding="utf-8",
                )
                options = ["--role", f"hero:{explicit_family}:48"] if explicit_family else []
                first = json.loads(self._run_calibration(project, *options, "--json").stdout)
                result = self._run_calibration(project, "--role", "kicker:Arial:16")
                second = self._read_calibration(project)
                self.assertEqual(second["roles"]["hero"], first["roles"]["hero"])
                first_fallback = [note for note in first["notes"] if "no hero_family" in note]
                second_fallback = [note for note in second["notes"] if "no hero_family" in note]
                self.assertEqual(second_fallback, first_fallback)
                if explicit_family:
                    self.assertEqual(second_fallback, [])
                    self.assertEqual(second["roles"]["hero"]["family"], explicit_family)
                else:
                    self.assertEqual(len(second_fallback), 1)
                    self.assertIn("body_family", second_fallback[0])
                    self.assertIn(second_fallback[0], result.stdout)

    def test_added_script_sample_preserves_saved_rows_and_displays_missing_rates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            first_run = self._run_calibration(
                project, "--role", "title:Arial:40:bold", "--sample", THAI_SAMPLE, "--json",
            )
            first = json.loads(first_run.stdout)
            second_run = self._run_calibration(
                project, "--role", "body:Arial:20", "--sample", ARABIC_SAMPLE,
                "--sample", THAI_SAMPLE[::-1],
            )
            second = self._read_calibration(project)
            self.assertEqual(second["roles"]["title"], first["roles"]["title"])
            self.assertEqual(second["script_samples"]["Thai"], first["script_samples"]["Thai"])
            self.assertEqual(set(second["script_samples"]), {"Thai", "Arabic"})
            self.assertEqual(set(second["roles"]["body"]["script_clusters_per_100px"]), {"Thai", "Arabic"})
            rows = [line.split(" | ") for line in second_run.stdout.splitlines()]
            headers = next(row for row in rows if row[0] == "role")
            title = next(row for row in rows if row[0] == "title")
            self.assertEqual(title[headers.index("Arabic ≈clusters/100px")], "-")

    def test_legacy_saved_script_rates_keep_their_column_without_sample_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self._run_calibration(
                project, "--role", "title:Arial:40:bold", "--sample", THAI_SAMPLE,
            )
            previous = self._read_calibration(project)
            previous["script_samples"] = {}
            (project / "validation" / "text_calibration.json").write_text(
                json.dumps(previous), encoding="utf-8",
            )
            result = self._run_calibration(project, "--role", "body:Arial:20")
            current = self._read_calibration(project)
            self.assertEqual(current["roles"]["title"], previous["roles"]["title"])
            self.assertIn("Thai ≈clusters/100px", result.stdout)
