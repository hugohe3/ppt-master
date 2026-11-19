"""Regression tests for splitting notes/total.md into per-page notes."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import total_md_split  # noqa: E402
from svg_to_pptx import create_pptx_with_native_svg  # noqa: E402
from svg_to_pptx.pptx_package.discovery import find_notes_files  # noqa: E402

STEMS = ["01_cover", "02_revenue", "03_outlook"]


def _parse(total_md: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        md_path = Path(tmp) / "total.md"
        md_path.write_text(total_md, encoding="utf-8")
        return total_md_split.parse_total_md(md_path, STEMS, verbose=False)


class HashPrefixedNarrationTests(unittest.TestCase):
    def test_hash_without_space_stays_in_its_page(self) -> None:
        notes = _parse(
            "# 01_cover\n欢迎大家。\n\n---\n\n"
            "# 02_revenue\n今年收入表现强劲。\n#1 产品收入增长 20%。\n其次是服务收入。\n\n---\n\n"
            "# 03_outlook\n明年继续投入。\n"
        )
        self.assertEqual(notes["01_cover"], "欢迎大家。")
        self.assertEqual(
            notes["02_revenue"],
            "今年收入表现强劲。\n#1 产品收入增长 20%。\n其次是服务收入。",
        )
        self.assertEqual(notes["03_outlook"], "明年继续投入。")

    def test_documented_heading_forms_still_split(self) -> None:
        notes = _parse("# Slide 1\nA\n\n---\n\n## 02_revenue\nB\n\n---\n\n#\t3\nC\n")
        self.assertEqual(notes, {"01_cover": "A", "02_revenue": "B", "03_outlook": "C"})

    def test_page_heading_allows_up_to_three_leading_spaces(self) -> None:
        for indent in range(4):
            with self.subTest(indent=indent):
                notes = _parse(f"# 01_cover\nA\n{' ' * indent}##\t02_revenue\nB\n    # 03_outlook\nC")
                self.assertEqual(notes, {"01_cover": "A", "02_revenue": "B\n    # 03_outlook\nC"})

    def test_repeated_page_sections_preserve_indented_content(self) -> None:
        notes = _parse("# 01_cover\n   \n    # literal\n# 01_cover\n\n# 01_cover\ncontinued")
        self.assertEqual(notes, {"01_cover": "    # literal\n\ncontinued"})

    def test_export_preserves_hash_narration_and_heading_paragraphs(self) -> None:
        notes = _parse(
            "# 01_cover\n欢迎大家。\n   # 02_revenue\n\n    # 开场白\n"
            "   ###\t本季收入\n#1 产品收入增长 20%。\n其次是服务收入。\n"
            "    # 缩进四格\n####### 七个井号\n#\n结束。"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = [root / f"{stem}.svg" for stem in STEMS[:2]]
            for page in pages:
                page.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                    '<rect width="20" height="20"/></svg>', encoding="utf-8",
                )
            output = root / "notes.pptx"
            self.assertTrue(total_md_split.split_notes(notes, root / "notes", verbose=False))
            self.assertTrue(create_pptx_with_native_svg(
                pages, output, resource_root=root, notes=find_notes_files(root, pages),
                pptx_structure="flat", verbose=False,
            ))
            with ZipFile(output) as archive:
                slide = ET.fromstring(archive.read("ppt/notesSlides/notesSlide2.xml"))
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        self.assertEqual(
            [p.findtext(".//a:t", "", ns) for p in slide.findall(".//a:p", ns)],
            [
                "# 开场白", "本季收入", "", "#1 产品收入增长 20%。", "其次是服务收入。",
                "# 缩进四格", "####### 七个井号", "", "结束。",
            ],
        )
