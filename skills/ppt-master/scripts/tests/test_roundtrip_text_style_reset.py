#!/usr/bin/env python3
"""PPT Master - Round-trip Text Style Reset Regression Tests

Keep explicit run style resets through native import, editing, and export.

Usage:
    python3 -m unittest tests.test_roundtrip_text_style_reset

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPT Master converters.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main as export_main


NS = {
    "s": "http://www.w3.org/2000/svg",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}
CASES = {
    "bold": ({"b": "1"}, {"b": "0"}),
    "italic": ({"i": "1"}, {"i": "0"}),
    "underline": ({"u": "sng"}, {"u": "none"}),
    "decoration": ({"u": "sng", "strike": "sngStrike"}, {"u": "none", "strike": "noStrike"}),
    "transparent": ({"alpha": "0"}, {"alpha": "100000"}),
    "quarter": ({"alpha": "25000"}, {"alpha": "100000"}),
    "control": ({"b": "0"}, {"b": "1"}),
}


def _make_source(root: Path, case: str) -> Path:
    """Construct source DrawingML explicitly instead of testing our own defaults."""
    root.mkdir(parents=True, exist_ok=True)
    pages = []
    for index, text in enumerate(("First Second", "Unchanged control"), start=1):
        page = root / f"slide_{index:02d}.svg"
        page.write_text(
            f'<svg xmlns="{NS["s"]}" viewBox="0 0 960 540" lang="en-US">'
            '<text x="80" y="140" font-family="Arial" font-size="24" '
            f'data-pptx-frame="70 100 700 120">{text}</text></svg>', encoding="utf-8",
        )
        pages.append(page)
    seed = root / "seed.pptx"
    assert create_pptx_with_native_svg(
        pages, seed, resource_root=root, pptx_structure="flat", use_compat_mode=False,
        transition=None, workers=1, verbose=False,
    )
    with zipfile.ZipFile(seed) as package:
        files = {name: package.read(name) for name in package.namelist()}
    slide = ET.fromstring(files["ppt/slides/slide1.xml"])
    shape = slide.find(".//p:sp", NS)
    shape.remove(shape.find("p:txBody", NS))
    body = ET.SubElement(shape, f'{{{NS["p"]}}}txBody')
    ET.SubElement(body, f'{{{NS["a"]}}}bodyPr', {
        "wrap": "none", "anchor": "t", "lIns": "0", "tIns": "0", "rIns": "0", "bIns": "0",
    })
    ET.SubElement(body, f'{{{NS["a"]}}}lstStyle')
    paragraph = ET.SubElement(body, f'{{{NS["a"]}}}p')
    for text, properties in zip(("First ", "Second"), CASES[case]):
        run = ET.SubElement(paragraph, f'{{{NS["a"]}}}r')
        attributes = {"sz": "1800", "lang": "en-US", **properties}
        alpha = attributes.pop("alpha", "100000")
        run_properties = ET.SubElement(run, f'{{{NS["a"]}}}rPr', attributes)
        fill = ET.SubElement(run_properties, f'{{{NS["a"]}}}solidFill')
        color = ET.SubElement(fill, f'{{{NS["a"]}}}srgbClr', {"val": "123456"})
        ET.SubElement(color, f'{{{NS["a"]}}}alpha', {"val": alpha})
        ET.SubElement(run_properties, f'{{{NS["a"]}}}latin', {"typeface": "Arial"})
        ET.SubElement(run, f'{{{NS["a"]}}}t').text = text
    files["ppt/slides/slide1.xml"] = ET.tostring(slide, encoding="utf-8")
    source = root / "source.pptx"
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as package:
        for name, payload in files.items():
            package.writestr(name, payload)
    return source


def _character_styles(slide: ET.Element) -> list[tuple]:
    result = []
    for run in slide.findall(".//a:r", NS):
        properties = run.find("a:rPr", NS)
        color = properties.find("a:solidFill/*", NS)
        alpha = 100000.0
        if color is not None:
            for transform in color:
                kind = transform.tag.rsplit("}", 1)[-1]
                value = float(transform.get("val", "0"))
                if kind == "alpha":
                    alpha = value
                elif kind == "alphaMod":
                    alpha *= value / 100000.0
                elif kind == "alphaOff":
                    alpha += value
        style = (
            properties.get("b", "0") in {"1", "true"},
            properties.get("i", "0") in {"1", "true"},
            properties.get("u", "none") != "none",
            properties.get("strike", "noStrike") != "noStrike",
            round(max(0, min(100000, alpha))),
        )
        result.extend((character, *style) for character in run.findtext("a:t", "", NS))
    return result


def _edit(workspace: Path) -> None:
    page = workspace / "authoring-svg-flat/slide_01.svg"
    tree = ET.parse(page)
    first = next(node for node in tree.getroot().iter() if node.text == "First ")
    first.text = "Edited "
    tree.write(page, encoding="utf-8", xml_declaration=True)


class RoundtripTextStyleResetTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def _roundtrip(self, case: str, *, edit: bool = True) -> tuple[ET.Element, ET.Element]:
        folder = self.root / case
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            source = _make_source(folder, case)
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            workspace = folder / "workspace"
            convert_pptx_to_svg(source, workspace, ConvertOptions(roundtrip=True, inheritance_mode="both"))
            if edit:
                _edit(workspace)
            output = folder / "result.pptx"
            code = export_main([str(workspace), "--roundtrip", "-o", str(output)])
        self.assertEqual(code, 0, log.getvalue())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(output) as exported:
            preserved = ["ppt/slides/slide2.xml", "ppt/slides/_rels/slide2.xml.rels"]
            if not edit:
                preserved.extend(["ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels"])
            for part in preserved:
                self.assertEqual(exported.read(part), original.read(part), part)
            return (
                ET.fromstring(original.read("ppt/slides/slide1.xml")),
                ET.fromstring(exported.read("ppt/slides/slide1.xml")),
            )

    def test_edited_imported_runs_preserve_explicit_style_resets(self) -> None:
        for case in CASES:
            with self.subTest(case=case):
                source, output = self._roundtrip(case)
                expected = _character_styles(source)
                expected = [(character, *expected[0][1:]) for character in "Edited "] + expected[6:]
                self.assertEqual(_character_styles(output), expected)
                second = next(run for run in output.findall(".//a:r", NS)
                              if "Second" in run.findtext("a:t", "", NS))
                properties = second.find("a:rPr", NS)
                for name, value in CASES[case][1].items():
                    if name != "alpha":
                        self.assertEqual(properties.get(name), value)
                if case in {"transparent", "quarter"}:
                    self.assertEqual(properties.find("a:solidFill/*/a:alphaMod", NS).get("val"), "100000")

    def test_unedited_source_pages_keep_original_xml(self) -> None:
        self._roundtrip("bold", edit=False)

    def _svg_export(self, body: str) -> ET.Element:
        page = self.root / "input.svg"
        page.write_text(f'<svg xmlns="{NS["s"]}" viewBox="0 0 960 540">{body}</svg>', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            xml, *_ = convert_svg_to_slide_shapes(page, resource_root=self.root, text_flow="preserve")
        return ET.fromstring(xml)

    def test_nested_explicit_reset_and_missing_child_style_remain_distinct(self) -> None:
        output = self._svg_export(
            '<text x="80" y="140" font-family="Arial" font-size="24" font-weight="bold" '
            'font-style="italic" text-decoration="underline line-through">'
            '<tspan>Inherited</tspan><tspan font-weight="normal" font-style="normal" '
            'text-decoration="none"><tspan>Plain</tspan></tspan><tspan>Inherited</tspan></text>'
        )
        styles = _character_styles(output)
        self.assertEqual(styles[:9], [(c, True, True, True, True, 100000) for c in "Inherited"])
        self.assertEqual(styles[9:14], [(c, False, False, False, False, 100000) for c in "Plain"])
        self.assertEqual(styles[14:], [(c, True, True, True, True, 100000) for c in "Inherited"])
        plain = output.findall(".//a:r", NS)[1].find("a:rPr", NS)
        self.assertEqual({name: plain.get(name) for name in ("b", "i", "u", "strike")},
                         {"b": "0", "i": "0", "u": "none", "strike": "noStrike"})

    def test_fill_opacity_reset_keeps_ancestor_object_opacity(self) -> None:
        output = self._svg_export(
            '<g opacity="0.5"><text x="80" y="140" font-size="24" fill-opacity="0.25">'
            '<tspan>Faded</tspan><tspan fill-opacity="1"><tspan>Reset</tspan></tspan></text></g>'
        )
        self.assertEqual(_character_styles(output),
                         [(c, False, False, False, False, 12500) for c in "Faded"]
                         + [(c, False, False, False, False, 50000) for c in "Reset"])

    def test_root_default_style_keeps_existing_omitted_attributes(self) -> None:
        output = self._svg_export(
            '<text x="80" y="140" font-size="24" font-weight="400" '
            'font-style="normal" text-decoration="none">Root</text>'
        )
        properties = output.find(".//a:rPr", NS)
        for name in ("b", "i", "u", "strike"):
            self.assertIsNone(properties.get(name))
