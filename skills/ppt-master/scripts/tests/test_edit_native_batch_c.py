#!/usr/bin/env python3
"""Regress CLI arguments, round-trip quality receipts, shape text, and notes.

Usage:
    python3 -m unittest tests.test_edit_native_batch_c

Dependencies:
    Standard library and local PPT Master conversion modules.
"""

from __future__ import annotations

import asyncio
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import notes_to_audio  # noqa: E402
from authoring_roundtrip import SourceRefRecord  # noqa: E402
from pptx_delivery_check import audit_pptx_delivery  # noqa: E402
from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg  # noqa: E402
from svg_quality import cli as quality_cli  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402
from svg_to_pptx.pptx_package import cli as export_cli  # noqa: E402
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"
SVG = (
    f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" font-family="Arial">'
    '<rect x="20" y="20" width="500" height="100" fill="#123456"/>'
    '<text x="40" y="80" font-size="24" fill="#FFFFFF">Example</text></svg>'
)


def _invoke(main, *args: str) -> tuple[int, str]:
    output = io.StringIO()
    with patch.object(sys, "argv", ["batch-c", *map(str, args)]), \
            contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            code = main()
        except SystemExit as exc:
            code = exc.code
    return code or 0, output.getvalue()


def _workspace(root: Path, *, notes: bool = False) -> Path:
    pages = []
    for index in (1, 2):
        svg = root / f"slide_{index:02d}.svg"
        svg.write_text(SVG, encoding="utf-8")
        pages.append(svg)
    source = root / "source.pptx"
    with contextlib.redirect_stdout(io.StringIO()):
        success = create_pptx_with_native_svg(
            pages, source, resource_root=root, pptx_structure="flat",
            use_compat_mode=False, transition=None, workers=1, verbose=False,
            notes={"slide_01": "Private speaker note."} if notes else None,
        )
        if not success:
            raise AssertionError("Could not create the minimal source deck")
        workspace = root / "workspace"
        convert_pptx_to_svg(
            source, workspace, ConvertOptions(inheritance_mode="both", roundtrip=True),
        )
    return workspace


class EditNativeBatchCTests(unittest.TestCase):
    def test_c1_negative_voice_options_accept_space_and_equals(self) -> None:
        for option, value in (("--rate", "-5%"), ("--pitch", "-2Hz"), ("--volume", "-10%")):
            for arguments in ([option, value], [f"{option}={value}"]):
                with self.subTest(arguments=arguments):
                    code, output = _invoke(
                        notes_to_audio.main, *arguments, "--list-common-voices",
                    )
                    self.assertEqual(code, 0, output)
        for arguments in (["--rate"], ["--rate", "--unknown"], ["--unknown"]):
            with self.subTest(invalid=arguments):
                code, _ = _invoke(notes_to_audio.main, *arguments, "--list-common-voices")
                self.assertEqual(code, 2)
        job = notes_to_audio.AudioJob(Path("note.md"), "Example", Path("page.mp3"))
        with patch.object(notes_to_audio.backend_edge, "generate", new_callable=AsyncMock) as generate:
            results = asyncio.run(notes_to_audio._generate_edge_jobs(
                [job], Path("subtitles"), voice="en-US-AriaNeural",
                rate="-5%", pitch="-2Hz", volume="-10%",
                subtitle_max_chars=20, concurrency=1,
            ))
        self.assertEqual(results, [None])
        self.assertEqual(generate.await_args.kwargs["rate"], "-5%")
        self.assertEqual(generate.await_args.kwargs["pitch"], "-2Hz")
        self.assertEqual(generate.await_args.kwargs["volume"], "-10%")
        communicate = Mock(return_value=SimpleNamespace(save=AsyncMock()))
        with patch.dict(sys.modules, {"edge_tts": SimpleNamespace(Communicate=communicate)}):
            asyncio.run(notes_to_audio.backend_edge.generate(
                "Example", Path("page.mp3"), voice="en-US-AriaNeural",
                rate="-5%", pitch="-2Hz", volume="-10%",
            ))
        self.assertEqual(communicate.call_args.kwargs["pitch"], "-2Hz")
        self.assertEqual(communicate.call_args.kwargs["volume"], "-10%")
        with patch.object(notes_to_audio.backend_edge, "_generate_with_subtitles", new_callable=AsyncMock) as generate:
            asyncio.run(notes_to_audio.backend_edge.generate(
                "Example", Path("page.mp3"), voice="en-US-AriaNeural",
                rate="-5%", pitch="-2Hz", volume="-10%", subtitle_path=Path("page.srt"),
            ))
        self.assertEqual(generate.await_args.kwargs["pitch"], "-2Hz")
        self.assertEqual(generate.await_args.kwargs["volume"], "-10%")

    def test_c2_roundtrip_quality_receipt_tracks_authoring_and_page_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = _workspace(root)
            output = workspace / "exports/result.pptx"
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "-o", output)
            self.assertEqual(code, 0, log)
            self.assertIn("quality_gate=not-provided", log)
            code, log = _invoke(quality_cli.main, workspace, "--roundtrip", "--json")
            self.assertEqual(code, 0, log)
            report_path = workspace / "validation/svg_quality_report.json"
            self.assertTrue(report_path.is_file(), log)
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "-o", output)
            self.assertEqual(code, 0, log)
            self.assertIn("quality_gate=passed", log)
            postflight = workspace / "validation/result.report.json"
            self.assertEqual(
                export_cli._load_deck_motion_handoff(workspace, str(postflight), []),
                json.loads(postflight.read_text(encoding="utf-8"))["deck_motion"],
            )
            plan = workspace / "page_plan.json"
            plan.write_text(json.dumps({
                "schema": "ppt-master.roundtrip-page-plan.v1",
                "pages": [{"source_slide": 2}, {"source_slide": 1}],
            }), encoding="utf-8")
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "-o", output)
            self.assertEqual(code, 0, log)
            self.assertIn("quality_gate=stale", log)
            code, log = _invoke(quality_cli.main, workspace, "--roundtrip", "--json")
            self.assertEqual(code, 0, log)
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "-o", output)
            self.assertEqual(code, 0, log)
            self.assertIn("quality_gate=passed", log)
            plan.write_text(json.dumps({
                "schema": "ppt-master.roundtrip-page-plan.v1",
                "pages": [{"source_slide": 1}, {"source_slide": 2}],
            }), encoding="utf-8")
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "-o", output)
            self.assertEqual(code, 0, log)
            self.assertIn("quality_gate=stale", log)
            code, log = _invoke(quality_cli.main, workspace, "--roundtrip", "--json")
            self.assertEqual(code, 0, log)
            svg = workspace / "authoring-svg-flat/slide_01.svg"
            svg.write_text(svg.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "-o", output)
            self.assertEqual(code, 0, log)
            self.assertIn("quality_gate=stale", log)

    def test_c3_semantic_text_contract_matches_export_and_skips_unchanged(self) -> None:
        first = '<text x="40" y="60" font-size="20">First</text>'
        second = '<text x="40" y="90" font-size="20">Second</text>'
        cases = (
            (first + second, "Semantic shape requires at most one paragraph-based text component"),
            (f"<g>{first}</g>", "Semantic shape text must be one direct SVG text component"),
            (first, None),
            ('<text x="40" y="60" font-size="20">First<tspan x="40" dy="30">Second</tspan></text>', None),
            ("", None),
        )
        with tempfile.TemporaryDirectory() as tmp:
            svg = Path(tmp) / "slide.svg"
            for body, error in cases:
                with self.subTest(body=body):
                    content = (
                        f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" font-family="Arial">'
                        '<g id="shape" data-pptx-semantic-object="shape" data-pptx-frame="20 20 500 100">'
                        '<rect data-pptx-part="geometry" x="20" y="20" width="500" height="100"/>'
                        f'{body}</g></svg>'
                    )
                    svg.write_text(content, encoding="utf-8")
                    root = ET.fromstring(content)
                    if error:
                        with self.assertRaisesRegex(RuntimeError, error):
                            convert_svg_to_slide_shapes(str(svg), resource_root=svg.parent)
                    else:
                        convert_svg_to_slide_shapes(str(svg), resource_root=svg.parent)
                    checker = SVGQualityChecker()
                    with contextlib.redirect_stdout(io.StringIO()):
                        generated = checker.check_file(str(svg))
                    roundtrip = SVGQualityChecker()._check_roundtrip_file(
                        svg, SimpleNamespace(source_refs={}), root, {}, {},
                        output_index=1, source_slide=1,
                    )
                    for result in (generated, roundtrip):
                        errors = "\n".join(result["errors"])
                        if error:
                            self.assertIn(error, errors)
                        else:
                            self.assertNotIn("Semantic shape", errors)
                    group = root.find(f"{{{SVG_NS}}}g")
                    group.set("data-pptx-source-ref", "slide:2")
                    svg.write_bytes(ET.tostring(root))
                    source = SimpleNamespace(source_refs={
                        "slide:2": SourceRefRecord((), "", "semantic-shape"),
                    })
                    unchanged = SVGQualityChecker()._check_roundtrip_file(
                        svg, source, copy.deepcopy(root), {}, {},
                        output_index=1, source_slide=1,
                    )
                    self.assertFalse(unchanged["errors"], unchanged)
            ordinary = (
                f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" font-family="Arial">'
                f'<g id="ordinary">{first}{second}</g></svg>'
            )
            svg.write_text(ordinary, encoding="utf-8")
            convert_svg_to_slide_shapes(str(svg), resource_root=svg.parent)
            with contextlib.redirect_stdout(io.StringIO()):
                result = SVGQualityChecker().check_file(str(svg))
            self.assertNotIn("Semantic shape", "\n".join(result["errors"]))

    def test_c4_no_notes_removes_parts_overrides_and_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = _workspace(Path(tmp), notes=True)
            self.assertFalse((workspace / "page_plan.json").exists())
            output = workspace / "exports/no_notes.pptx"
            code, log = _invoke(export_cli.main, workspace, "--roundtrip", "--no-notes", "-o", output)
            self.assertEqual(code, 0, log)
            with zipfile.ZipFile(output) as archive:
                self.assertFalse([name for name in archive.namelist() if name.startswith((
                    "ppt/notesSlides/", "ppt/notesMasters/",
                ))])
                for name in archive.namelist():
                    if name.endswith(".rels") or name == "[Content_Types].xml":
                        self.assertNotIn(b"notesSlide", archive.read(name), name)
                        self.assertNotIn(b"notesMaster", archive.read(name), name)
            report = audit_pptx_delivery(output)
            self.assertFalse(report["errors"], report)
            orphan = workspace / "exports/orphan.pptx"
            with zipfile.ZipFile(output) as source, zipfile.ZipFile(orphan, "w") as target:
                for name in source.namelist():
                    payload = source.read(name)
                    if name == "[Content_Types].xml":
                        tree = ET.fromstring(payload)
                        ET.SubElement(tree, f"{tree.tag.removesuffix('Types')}Override", {
                            "PartName": "/ppt/notesSlides/notesSlide1_tf1.xml",
                            "ContentType": "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
                        })
                        payload = ET.tostring(tree)
                    target.writestr(name, payload)
                target.writestr(
                    "ppt/notesSlides/notesSlide1_tf1.xml",
                    '<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>',
                )
            report = audit_pptx_delivery(orphan)
            self.assertFalse(report["errors"], report)
            advisory = next((
                item for item in report["advisories"] if item["code"] == "orphan_notes_parts"
            ), None)
            self.assertIsNotNone(advisory, report)
            self.assertEqual(advisory["parts"], ["ppt/notesSlides/notesSlide1_tf1.xml"])
