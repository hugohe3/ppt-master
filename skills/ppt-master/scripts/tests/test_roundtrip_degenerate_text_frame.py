#!/usr/bin/env python3
"""Keep recoverable degenerate source text editable without changing passthrough."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from authoring_roundtrip import materialize_flat_authoring_roundtrip
from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_to_pptx.drawingml.converter import SvgNativeConversionError
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main as export_main

SVG = "http://www.w3.org/2000/svg"
NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


class RoundtripDegenerateTextFrameTests(unittest.TestCase):
    def _workspace(
        self, root: Path, extent: tuple[int, int], *, stroked: bool = False,
    ) -> tuple[Path, Path]:
        root.mkdir(parents=True, exist_ok=True)
        pages = []
        for number, text in enumerate(("Text", "Control"), start=1):
            page = root / f"slide_{number:02d}.svg"
            page.write_text(
                f'<svg xmlns="{SVG}" viewBox="0 0 1280 720" lang="en-US" font-family="Arial">'
                f'<text x="100" y="140" font-size="24" fill="#123456">{text}</text></svg>',
                encoding="utf-8",
            )
            pages.append(page)
        source = root / "source.pptx"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertTrue(create_pptx_with_native_svg(
                pages, source, resource_root=root, pptx_structure="flat",
                use_compat_mode=False, transition=None, workers=1, verbose=False,
            ))
        with zipfile.ZipFile(source) as package:
            files = {name: package.read(name) for name in package.namelist()}
        slide = ET.fromstring(files["ppt/slides/slide1.xml"])
        frame = slide.find(".//p:sp/p:spPr/a:xfrm/a:ext", NS)
        frame.set("cx", str(extent[0]))
        frame.set("cy", str(extent[1]))
        if stroked:
            line = slide.find(".//p:sp/p:spPr/a:ln", NS)
            line.clear()
            line.set("w", "38100")
            fill = ET.SubElement(line, f"{{{NS['a']}}}solidFill")
            ET.SubElement(fill, f"{{{NS['a']}}}srgbClr", {"val": "123456"})
        files["ppt/slides/slide1.xml"] = ET.tostring(slide, encoding="utf-8")
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as package:
            for name, payload in files.items():
                package.writestr(name, payload)
        workspace = root / "workspace"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            convert_pptx_to_svg(
                source, workspace, ConvertOptions(roundtrip=True, inheritance_mode="both"),
            )
        return source, workspace

    def _edit(self, workspace: Path, frame: str | None = None) -> None:
        page = workspace / "authoring-svg-flat/slide_01.svg"
        root = ET.parse(page).getroot()
        source = next(node for node in root.iter() if node.get("data-pptx-source-ref", "").startswith("slide:"))
        text = next(node for node in source.iter() if node.text == "Text")
        text.text = "Edited"
        if frame is not None:
            source.set("data-pptx-frame", frame)
        page.write_bytes(ET.tostring(root))

    def test_edited_nonpositive_source_text_uses_computed_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for index, extent in enumerate(((0, 0), (2857500, 0), (0, 952500))):
                with self.subTest(extent=extent):
                    _, workspace = self._workspace(Path(temporary) / str(index), extent)
                    self._edit(workspace)
                    result = materialize_flat_authoring_roundtrip(
                        workspace, workspace / "authoring-svg-flat", workspace / "materialized",
                    )
                    self.assertEqual(result.report["totals"]["edited_refs"], 1)
                    output = workspace / "exports/result.pptx"
                    log = io.StringIO()
                    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                        status = export_main([str(workspace), "--roundtrip", "-o", str(output)])
                    self.assertEqual(status, 0, log.getvalue())
                    with zipfile.ZipFile(output) as exported:
                        slide = ET.fromstring(exported.read("ppt/slides/slide1.xml"))
                        self.assertIn("Edited", [text.text for text in slide.findall(".//a:t", NS)])
                        frame = slide.find(".//p:sp/p:spPr/a:xfrm/a:ext", NS)
                        self.assertGreater(int(frame.get("cx")), 0)
                        self.assertGreater(int(frame.get("cy")), 0)

    def test_explicit_positive_repair_allows_edited_source_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, workspace = self._workspace(Path(temporary), (0, 0))
            self._edit(workspace, "100 100 300 100")
            result = materialize_flat_authoring_roundtrip(
                workspace, workspace / "authoring-svg-flat", workspace / "materialized",
            )
            self.assertEqual(result.report["totals"]["edited_refs"], 1)
            self.assertIn("Edited", (workspace / "materialized/slide_01.svg").read_text())

    def test_unchanged_degenerate_source_pages_remain_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, workspace = self._workspace(Path(temporary), (0, 0))
            output = workspace / "exports/result.pptx"
            log = io.StringIO()
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                result = export_main([str(workspace), "--roundtrip", "-o", str(output)])
            self.assertEqual(result, 0, log.getvalue())
            self.assertIn("passthrough=2", log.getvalue())
            with zipfile.ZipFile(source) as original, zipfile.ZipFile(output) as exported:
                for page in ("ppt/slides/slide1.xml", "ppt/slides/slide2.xml"):
                    self.assertEqual(original.read(page), exported.read(page))

    def test_stroked_zero_axis_shape_uses_existing_text_frame_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, workspace = self._workspace(Path(temporary), (2857500, 0), stroked=True)
            self._edit(workspace)
            materialize_flat_authoring_roundtrip(
                workspace, workspace / "authoring-svg-flat", workspace / "materialized",
            )
            materialized = ET.parse(workspace / "materialized/slide_01.svg").getroot()
            carrier = next(node for node in materialized.iter() if any(
                child.get("data-pptx-part") == "geometry" for child in node
            ))
            self.assertEqual(carrier.get("data-pptx-frame").split()[2:], ["300", "0"])
            output = workspace / "exports/result.pptx"
            log = io.StringIO()
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                with self.assertRaisesRegex(SvgNativeConversionError, "data-pptx-frame width and height must be positive"):
                    export_main([str(workspace), "--roundtrip", "-o", str(output)])
