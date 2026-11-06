#!/usr/bin/env python3
"""PPT Master - Source chart category semantics regressions.

Usage:
    python3 -m unittest tests.test_source_chart_categories
Examples:
    Run from skills/ppt-master/scripts.
Dependencies:
    python-pptx, mammoth (conversion dependencies).
"""

import io
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR / "source_to_md"))
import doc_to_md  # noqa: E402
import ppt_to_md  # noqa: E402


def _presentation(kind):
    data = CategoryChartData()
    if kind == "date":
        data.categories = [date(2024, 1, 31), date(2024, 3, 15)]
        data.categories.number_format = "yyyy-mm-dd"
    elif kind == "hierarchy":
        for parent in ("North", "South"):
            group = data.add_category(parent)
            group.add_sub_category("Same")
    else:
        data.categories = ["Normal A", "Normal B"]
    data.add_series("Revenue", [11.25, 22.75])
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1), Inches(5), Inches(3), data,
    ).chart
    return prs, chart


def _write_docx(path, chart_xml):
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    c = "http://schemas.openxmlformats.org/drawingml/2006/chart"
    package = "http://schemas.openxmlformats.org/package/2006/relationships"
    parts = {
        "[Content_Types].xml": (
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
            'officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/charts/chart1.xml" ContentType="application/vnd.openxmlformats-'
            'officedocument.drawingml.chart+xml"/></Types>'
        ),
        "_rels/.rels": (
            f'<Relationships xmlns="{package}"><Relationship Id="document" '
            f'Type="{r}/officeDocument" Target="word/document.xml"/></Relationships>'
        ),
        "word/document.xml": (
            f'<w:document xmlns:w="{w}" xmlns:r="{r}" xmlns:c="{c}" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
            '<w:body><w:p><w:r><w:t>Source data</w:t></w:r></w:p>'
            '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="4000000" cy="2500000"/>'
            '<wp:docPr id="1" name="Revenue"/><a:graphic>'
            f'<a:graphicData uri="{c}"><c:chart r:id="chart"/></a:graphicData>'
            '</a:graphic></wp:inline></w:drawing></w:r></w:p></w:body></w:document>'
        ),
        "word/_rels/document.xml.rels": (
            f'<Relationships xmlns="{package}"><Relationship Id="chart" '
            f'Type="{r}/chart" Target="charts/chart1.xml"/></Relationships>'
        ),
        "word/charts/chart1.xml": chart_xml,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)


class SourceChartCategoryTests(unittest.TestCase):
    def _convert_pptx(self, prs):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            source = Path(tmp) / "source.pptx"
            prs.save(source)
            return ppt_to_md.convert_presentation_to_markdown(str(source), str(source.with_suffix(".md")))

    def test_date_categories_preserve_serial_values_and_date_semantics(self) -> None:
        prs, chart = _presentation("date")
        for system, value in (("1900", "0"), ("1900", "false"), ("1904", "1"),
                              ("1904", "true"), ("1904", None)):
            with self.subTest(date_system=system, value=value):
                date1904 = chart._chartSpace.find(qn("c:date1904"))
                if value is None:
                    date1904.attrib.pop("val", None)
                else:
                    date1904.set("val", value)
                markdown = self._convert_pptx(prs)
                self.assertIn("Excel date serials", markdown)
                self.assertIn("date system: " + system, markdown)
                self.assertIn("format: yyyy-mm-dd", markdown)
                self.assertIn("| 45322.0 | 11.25 |", markdown)
                self.assertIn("| 45366.0 | 22.75 |", markdown)

    def test_absent_date_system_defaults_to_1900(self) -> None:
        prs, chart = _presentation("date")
        chart._chartSpace.remove(chart._chartSpace.find(qn("c:date1904")))
        self.assertIn("date system: 1900", self._convert_pptx(prs))

    def test_hierarchical_categories_keep_parents_of_identical_leaves(self) -> None:
        prs, _ = _presentation("hierarchy")
        markdown = self._convert_pptx(prs)
        self.assertIn("| North / Same | 11.25 |", markdown)
        self.assertIn("| South / Same | 22.75 |", markdown)
        self.assertNotIn("Excel date serials", markdown)

    def test_deep_hierarchy_and_sparse_values_preserve_point_alignment(self) -> None:
        prs, chart = _presentation("normal")
        data = CategoryChartData()
        for parent in ("North", "South"):
            data.add_category(parent).add_sub_category("Area").add_sub_category("Same")
        data.add_series("Revenue", [11.25, None])
        chart.replace_data(data)
        markdown = self._convert_pptx(prs)
        self.assertIn("| North / Area / Same | 11.25 |", markdown)
        self.assertIn("| South / Area / Same |  |", markdown)

    def test_missing_hierarchical_categories_do_not_shift_series_values(self) -> None:
        for missing_index in (0, 1):
            for values in ([11, 22, 33, 44], [11, None, 33, 44]):
                with self.subTest(missing_index=missing_index, values=values):
                    prs, chart = _presentation("normal")
                    data = CategoryChartData()
                    for parent in ("North", "South"):
                        group = data.add_category(parent)
                        group.add_sub_category("A")
                        group.add_sub_category("B")
                    data.add_series("Revenue", values)
                    chart.replace_data(data)
                    cache = chart.series[0]._element.find(".//" + qn("c:multiLvlStrCache"))
                    leaf = cache.find(qn("c:lvl"))
                    leaf.remove(leaf.findall(qn("c:pt"))[missing_index])
                    markdown = self._convert_pptx(prs)
                    self.assertIn("| South / A | 33 |", markdown)
                    self.assertIn("| South / B | 44 |", markdown)
                    value = "" if values[missing_index] is None else str(values[missing_index])
                    rows = [[cell.strip() for cell in line.split("|")[1:-1]]
                            for line in markdown.splitlines() if line.startswith("| ")]
                    self.assertIn(["", value], rows)

    def test_missing_single_level_category_keeps_its_original_slot(self) -> None:
        prs, chart = _presentation("normal")
        category = chart.series[0]._element.find(qn("c:cat")).find(".//" + qn("c:strCache"))
        category.remove(category.findall(qn("c:pt"))[0])
        markdown = self._convert_pptx(prs)
        rows = [[cell.strip() for cell in line.split("|")[1:-1]]
                for line in markdown.splitlines() if line.startswith("| ")]
        self.assertIn(["", "11.25"], rows)
        self.assertIn("| Normal B | 22.75 |", markdown)

    def test_single_level_and_plain_list_categories_remain_compatible(self) -> None:
        prs, _ = _presentation("normal")
        markdown = self._convert_pptx(prs)
        self.assertIn("| Normal A | 11.25 |", markdown)
        self.assertIn("| Normal B | 22.75 |", markdown)
        self.assertNotIn("Excel date serials", markdown)
        chart = SimpleNamespace(
            chart_type="COLUMN_CLUSTERED", has_title=False,
            plots=[SimpleNamespace(categories=["Normal A", "Normal B"])],
            series=[SimpleNamespace(name="Revenue", values=[11.25, 22.75])],
        )
        self.assertIn("| Normal A | 11.25 |", ppt_to_md.chart_to_markdown(chart, "Normal"))

    def test_docx_embedded_chart_uses_the_same_category_semantics(self) -> None:
        for kind, expected in (("date", "Excel date serials"), ("hierarchy", "North / Same")):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                _, chart = _presentation(kind)
                source = Path(tmp) / "source.docx"
                _write_docx(source, chart._chartSpace.xml.encode("utf-8"))
                with redirect_stdout(io.StringIO()):
                    markdown = doc_to_md.convert_to_markdown(str(source), str(source.with_suffix(".md")))
                self.assertIn(expected, markdown)
                self.assertIn("11.25", markdown)
                self.assertIn("22.75", markdown)
