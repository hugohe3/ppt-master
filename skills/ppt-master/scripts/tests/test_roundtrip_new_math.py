#!/usr/bin/env python3
"""PPT Master - New Math in Native Round-trip Regression Tests

Keep newly authored Office Math usable when the source slide never declared
the a14 namespace that mc:Choice Requires it.

Usage:
    python3 -m unittest tests.test_roundtrip_new_math

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library, lxml, and the local PPTX import/export pipeline.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from lxml import etree as LET

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from pptx_transitions import (
    merged_mce_bindings,
    parse_xml_with_mce_bindings,
    serialize_source_xml,
    validate_mce_prefixes,
)
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main


SVG_NS = "http://www.w3.org/2000/svg"
MATH_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"


class RoundtripNewMathTests(unittest.TestCase):
    def _make_source(self, root: Path) -> Path:
        svg = root / "source.svg"
        svg.write_text(
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" '
            'font-family="Arial"><g id="retained">'
            '<rect x="50" y="50" width="100" height="60" fill="#123456"/>'
            "</g></svg>",
            encoding="utf-8",
        )
        source = root / "source.pptx"
        self.assertTrue(create_pptx_with_native_svg(
            [svg], source, resource_root=root, pptx_structure="flat",
            use_compat_mode=False, transition=None, workers=1, verbose=False,
        ))
        return source

    def _export_addition(self, source: Path, addition: str) -> LET._Element:
        workspace = source.parent / "workspace"
        output = source.parent / "output.pptx"
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            convert_pptx_to_svg(
                source, workspace, ConvertOptions(inheritance_mode="both", roundtrip=True),
            )
            authored = workspace / "authoring-svg-flat" / "slide_01.svg"
            authored.write_text(
                authored.read_text(encoding="utf-8").replace("</svg>", addition + "</svg>"),
                encoding="utf-8",
            )
            result = main([str(workspace), "--roundtrip", "-o", str(output)])
        self.assertEqual(result, 0, stdout.getvalue() + stderr.getvalue())
        with ZipFile(output) as archive:
            xml = archive.read("ppt/slides/slide1.xml")
        self.assertEqual(validate_mce_prefixes(xml), [])
        return LET.fromstring(xml)

    def test_new_block_and_inline_math_keep_required_namespace(self) -> None:
        additions = {
            "block": (
                '<g id="added-math" data-pptx-replace-with="formula" '
                'data-pptx-x="100" data-pptx-y="150" '
                'data-pptx-width="400" data-pptx-height="80" '
                'data-pptx-bounds="100 150 400 80">'
                '<metadata type="application/json">'
                '{"latex":"x=1","display":"block","font_size":28,'
                '"color":"#002060","align":"left"}</metadata>'
                '<text x="100" y="200" font-size="28">x = 1</text></g>'
            ),
            "inline": (
                '<g id="added-inline"><text x="100" y="200" font-size="28">'
                'Value <tspan data-pptx-inline-formula="x=1">x = 1</tspan>'
                "</text></g>"
            ),
        }
        for kind, addition in additions.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = self._make_source(root)
                parsed = self._export_addition(source, addition)
                choices = parsed.findall(f".//{{{MC_NS}}}Choice")
                self.assertTrue(choices)
                self.assertTrue(
                    all(choice.nsmap.get("a14") == MATH_NS for choice in choices)
                )
                self.assertIsNotNone(parsed.find(f".//{{{MATH_NS}}}m"))

    def test_plain_rectangle_preserves_source_ignorable_r(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = self._make_source(Path(temporary))
            vendor_source = source.with_name("vendor.pptx")
            with ZipFile(source) as original, ZipFile(vendor_source, "w") as modified:
                for entry in original.infolist():
                    data = original.read(entry)
                    if entry.filename == "ppt/slides/slide1.xml":
                        data = data.replace(b"xmlns:r=", b"xmlns:rel=").replace(
                            b"<p:sld ",
                            f'<p:sld xmlns:r="urn:vendor:ext" xmlns:mc="{MC_NS}" '
                            'mc:Ignorable="r" '.encode("utf-8"),
                        )
                    modified.writestr(entry, data)
            parsed = self._export_addition(
                vendor_source, '<rect x="200" y="70" width="80" height="40" fill="#ABCDEF"/>',
            )
        self.assertEqual(parsed.get(f"{{{MC_NS}}}Ignorable"), "r")
        self.assertEqual(parsed.nsmap["r"], "urn:vendor:ext")
        self.assertIsNotNone(parsed.find('.//a:srgbClr[@val="ABCDEF"]', parsed.nsmap))

    def test_conflicting_required_namespace_fails(self) -> None:
        source = f'<root xmlns:mc="{MC_NS}" xmlns:a14="urn:original"/>'
        root = ET.fromstring(source)
        ET.SubElement(root, f"{{{MC_NS}}}Choice", Requires="a14")
        with self.assertRaisesRegex(ValueError, "Conflicting MCE namespace"):
            serialize_source_xml(root, source, additional_bindings={"a14": MATH_NS})

    def test_shadowed_source_declaration_conflicts_only_when_required(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" xmlns:a14="urn:vendor" mc:Ignorable="a14">'
            f'<child xmlns:a14="{MATH_NS}"/></root>'
        )
        root = ET.fromstring(source)
        serialize_source_xml(root, source)
        ET.SubElement(root, f"{{{MC_NS}}}Choice", Requires="a14")
        with self.assertRaisesRegex(ValueError, "Conflicting MCE namespace binding for 'a14'"):
            serialize_source_xml(root, source, additional_bindings={"a14": MATH_NS})

    def test_generated_reserved_prefix_keeps_both_mce_and_element_namespaces(self) -> None:
        for prefix in ("ns77", "ns0"):
            with self.subTest(prefix=prefix):
                source = "<slide/>"
                root = ET.fromstring(source)
                ET.SubElement(root, "{urn:unregistered}shape")
                ET.SubElement(root, f"{{{MC_NS}}}Choice", Requires=prefix)
                output = serialize_source_xml(root, source, additional_bindings={prefix: MATH_NS})
                parsed = LET.fromstring(output)
                self.assertIsNotNone(parsed.find("{urn:unregistered}shape"))
                self.assertEqual(parsed.find(f"{{{MC_NS}}}Choice").nsmap[prefix], MATH_NS)

    def test_source_only_prefix_reserved_by_elementtree_survives(self) -> None:
        source = f'<root xmlns:mc="{MC_NS}" xmlns:ns77="urn:vendor" mc:Ignorable="ns77"/>'
        output = serialize_source_xml(ET.fromstring(source), source)
        self.assertEqual(LET.fromstring(output).nsmap["ns77"], "urn:vendor")

    def test_only_merged_references_require_their_scoped_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "generated.xml"
            path.write_text(
                f'<root xmlns:mc="{MC_NS}" xmlns:feature="urn:outer">'
                '<shape xmlns:feature="urn:inner"><detail mc:Ignorable="feature"/></shape>'
                '<shape><mc:Choice Requires="feature"/></shape></root>',
                encoding="utf-8",
            )
            generated, bindings = parse_xml_with_mce_bindings(path)
        source = "<merged/>"
        root = ET.fromstring(source)
        root.append(generated[0])
        selected = merged_mce_bindings(root, bindings)
        xml = LET.fromstring(serialize_source_xml(root, source, additional_bindings=selected))
        self.assertEqual(xml.find(".//detail").nsmap["feature"], "urn:inner")
        root.append(generated[1])
        with self.assertRaisesRegex(ValueError, "Conflicting MCE namespace binding for 'feature'"):
            merged_mce_bindings(root, bindings)
