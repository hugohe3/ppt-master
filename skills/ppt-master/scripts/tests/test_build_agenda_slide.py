#!/usr/bin/env python3
"""Unit tests for the clickable agenda slide builder."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if not sys.path or sys.path[0] != str(SCRIPTS_DIR):
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_agenda_slide import (  # noqa: E402
    extract_page_title,
    is_agenda_page,
    load_roster,
    main,
    parse_roles,
    plan_agenda,
    render_agenda_svg,
    title_from_filename,
)
from hyperlink_contract import project_hyperlink_errors  # noqa: E402
from svg_quality.checker import SVGQualityChecker  # noqa: E402
from svg_to_pptx.pptx_package.cli import main as export_main  # noqa: E402


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "s": "http://www.w3.org/2000/svg",
}


def _page(title: str, role: str, body: str = "Supporting line") -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" '
        f'viewBox="0 0 1280 720" data-pptx-page-role="{role}" font-family="Arial">'
        '<rect x="0" y="0" width="1280" height="720" fill="#F8FAFC"/>'
        f'<text x="80" y="200" font-family="Arial" font-size="48" fill="#0F172A">'
        f"{title}</text>"
        f'<text x="80" y="280" font-family="Arial" font-size="22" fill="#334155">'
        f"{body}</text></svg>\n"
    )


def _write_roster(root: Path, pages: list[tuple[str, str, str]]) -> Path:
    svg_dir = root / "svg_output"
    svg_dir.mkdir(parents=True)
    for name, title, role in pages:
        (svg_dir / name).write_text(_page(title, role), encoding="utf-8")
    return root


class TitleAndRoleTests(unittest.TestCase):
    def test_filename_title_strips_leading_index(self) -> None:
        self.assertEqual(title_from_filename("03_market_overview.svg"), "Market Overview")

    def test_extract_prefers_largest_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "02_body.svg"
            path.write_text(_page("Demand Signal", "content"), encoding="utf-8")
            title, role, canvas = extract_page_title(path)
            self.assertEqual(title, "Demand Signal")
            self.assertEqual(role, "content")
            self.assertEqual(canvas, (1280, 720))

    def test_parse_roles_accepts_all(self) -> None:
        self.assertEqual(parse_roles("all"), ("all",))
        self.assertEqual(parse_roles("content, section"), ("content", "section"))


class PlanTests(unittest.TestCase):
    def test_insert_after_cover_shifts_later_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _write_roster(
                Path(tmp),
                [
                    ("01_cover.svg", "Q3 Review", "cover"),
                    ("02_demand.svg", "Demand Signal", "content"),
                    ("03_risks.svg", "Open Risks", "content"),
                    ("04_end.svg", "Next Steps", "ending"),
                ],
            )
            pages = load_roster(project)
            items, write_index, replace, canvas = plan_agenda(pages)
            self.assertEqual(write_index, 2)
            self.assertIsNone(replace)
            self.assertEqual(canvas, (1280, 720))
            self.assertEqual(
                [(item.title, item.target_slide) for item in items],
                [("Demand Signal", 3), ("Open Risks", 4)],
            )

    def test_existing_toc_is_replaced_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _write_roster(
                Path(tmp),
                [
                    ("01_cover.svg", "Q3 Review", "cover"),
                    ("02_toc.svg", "Old Agenda", "toc"),
                    ("03_demand.svg", "Demand Signal", "content"),
                ],
            )
            pages = load_roster(project)
            self.assertTrue(is_agenda_page(pages[1]))
            items, write_index, replace, _canvas = plan_agenda(pages)
            self.assertEqual(write_index, 2)
            self.assertIsNotNone(replace)
            self.assertEqual(replace.path.name, "02_toc.svg")
            self.assertEqual(items[0].target_slide, 3)
            self.assertEqual(items[0].title, "Demand Signal")


class RenderAndCliTests(unittest.TestCase):
    def test_rendered_svg_has_slide_jumps_and_passes_contracts(self) -> None:
        from build_agenda_slide import AgendaItem

        svg = render_agenda_svg(
            [
                AgendaItem("Demand Signal", "02_demand.svg", "content", 3),
                AgendaItem("Open Risks", "03_risks.svg", "content", 4),
            ]
        )
        root = ET.fromstring(svg)
        hrefs = [node.get("href") for node in root.findall("{%s}a" % NS["s"])]
        self.assertEqual(hrefs, ["#slide-3", "#slide-4"])
        self.assertEqual(root.get("data-pptx-page-role"), "toc")
        self.assertEqual(project_hyperlink_errors(root, slide_count=5), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "02_agenda.svg"
            path.write_text(svg, encoding="utf-8")
            report = SVGQualityChecker(quick_generate=True).check_file(str(path))
            self.assertFalse(report["errors"], report["errors"])

    def test_cli_inserts_agenda_and_renames_later_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _write_roster(
                Path(tmp),
                [
                    ("01_cover.svg", "Q3 Review", "cover"),
                    ("02_demand.svg", "Demand Signal", "content"),
                    ("03_end.svg", "Next Steps", "ending"),
                ],
            )
            (project / "notes").mkdir()
            (project / "notes" / "02_demand.md").write_text("Talk track", encoding="utf-8")
            stderr = io.StringIO()
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main([str(project), "--json"])
            self.assertEqual(code, 0, stderr.getvalue())
            plan = json.loads(stdout.getvalue())
            self.assertEqual(plan["write_index"], 2)
            names = sorted(path.name for path in (project / "svg_output").glob("*.svg"))
            self.assertEqual(names, ["01_cover.svg", "02_agenda.svg", "03_demand.svg", "04_end.svg"])
            self.assertTrue((project / "notes" / "03_demand.md").is_file())
            self.assertFalse((project / "notes" / "02_demand.md").exists())

    def test_help_exits_zero_without_writing(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout), self.assertRaises(SystemExit) as caught:
            main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("clickable agenda", stdout.getvalue())

    def test_missing_project_is_nonzero(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main(["/tmp/ppt-master-missing-project"])
        self.assertEqual(code, 1)
        self.assertIn("svg_output", stderr.getvalue())


class ExportHyperlinkTests(unittest.TestCase):
    def test_exported_agenda_rows_jump_to_content_slides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _write_roster(
                Path(tmp),
                [
                    ("01_cover.svg", "Q3 Review", "cover"),
                    ("02_demand.svg", "Demand Signal", "content"),
                    ("03_risks.svg", "Open Risks", "content"),
                ],
            )
            self.assertEqual(main([str(project)]), 0)
            check = subprocess.run(
                [
                    sys.executable, "-B",
                    str(SCRIPTS_DIR / "svg_quality_checker.py"),
                    str(project),
                    "--quick-generate",
                    "--canonical-authoring",
                    "--stage", "final",
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            output = Path(tmp) / "agenda.pptx"
            stderr = io.StringIO()
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = export_main(
                    [str(project), "--quick-generate", "-o", str(output)]
                )
            self.assertEqual(code, 0, stdout.getvalue() + stderr.getvalue())
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as package:
                slide = ET.fromstring(package.read("ppt/slides/slide2.xml"))
                rels = ET.fromstring(
                    package.read("ppt/slides/_rels/slide2.xml.rels")
                )
            clicks = slide.findall(".//a:hlinkClick", NS)
            self.assertGreaterEqual(len(clicks), 2, ET.tostring(slide, encoding="unicode"))
            actions = {click.get("action") for click in clicks}
            self.assertIn("ppaction://hlinksldjump", actions)
            targets = {
                rel.get("Target")
                for rel in rels
                if rel.get("Type", "").endswith("/slide")
            }
            self.assertTrue(any(target.endswith("slide3.xml") for target in targets), targets)
            self.assertTrue(any(target.endswith("slide4.xml") for target in targets), targets)


if __name__ == "__main__":
    unittest.main()
