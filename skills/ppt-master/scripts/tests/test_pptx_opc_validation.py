#!/usr/bin/env python3
"""
PPT Master - OPC Package Relationship Validation Tests

Comprehensive unit tests for pptx_opc_validation.py covering canonical OPC
part path normalization, relationship source and target resolution, slide
roster calculation, and package relationship verification.

Usage:
    python3 -m unittest tests.test_pptx_opc_validation

Dependencies:
    None (standard library unittest only).
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from hyperlink_contract import (  # noqa: E402
    HYPERLINK_REL_TYPE,
    SLIDE_JUMP_ACTION,
    SLIDE_REL_TYPE,
)
from pptx_opc_validation import (  # noqa: E402
    PACKAGE_REL_NS,
    _presentation_slide_roster,
    _relationship_attrs_by_id,
    _relationships_path_for_part,
    _source_part_for_rels,
    canonical_opc_part_path,
    resolve_internal_opc_target,
    verify_hyperlink_relationships,
    verify_internal_relationships,
)


class CanonicalOpcPartPathTests(unittest.TestCase):
    """Tests for canonical_opc_part_path normalization and validation."""

    def test_valid_normal_paths(self) -> None:
        self.assertEqual(
            canonical_opc_part_path("ppt/presentation.xml"),
            "ppt/presentation.xml",
        )
        self.assertEqual(
            canonical_opc_part_path("ppt/slides/slide1.xml"),
            "ppt/slides/slide1.xml",
        )
        self.assertEqual(
            canonical_opc_part_path("docProps/core.xml"),
            "docprops/core.xml",
        )
        self.assertEqual(
            canonical_opc_part_path("[Content_Types].xml"),
            "[content_types].xml",
        )
        self.assertEqual(
            canonical_opc_part_path("_rels/.rels"),
            "_rels/.rels",
        )

    def test_lowercase_ascii_translation(self) -> None:
        self.assertEqual(
            canonical_opc_part_path("PPT/Slides/Slide1.XML"),
            "ppt/slides/slide1.xml",
        )
        self.assertEqual(
            canonical_opc_part_path("DOCPROPS/CORE.XML"),
            "docprops/core.xml",
        )
        self.assertEqual(
            canonical_opc_part_path("PPT/MEDIA/IMAGE1.PNG"),
            "ppt/media/image1.png",
        )

    def test_percent_encoded_unreserved_characters(self) -> None:
        # %41 -> 'A' -> 'a', %42 -> 'B' -> 'b', %43 -> 'C' -> 'c'
        self.assertEqual(canonical_opc_part_path("%41%42%43"), "abc")
        # %7E -> '~'
        self.assertEqual(canonical_opc_part_path("ppt/%7Eslide.xml"), "ppt/~slide.xml")
        # %2D -> '-', %2E -> '.', %5F -> '_'
        self.assertEqual(canonical_opc_part_path("ppt/%2D%2E%5F.xml"), "ppt/-._.xml")
        # %30 -> '0', %39 -> '9'
        self.assertEqual(canonical_opc_part_path("ppt/slide%30%39.xml"), "ppt/slide09.xml")
        # Mixed-case hex
        self.assertEqual(canonical_opc_part_path("%4a%4B"), "jk")
        # Unreserved character in directory segment
        self.assertEqual(
            canonical_opc_part_path("ppt/%53lides/slide1.xml"),
            "ppt/slides/slide1.xml",
        )

    def test_percent_encoded_reserved_characters(self) -> None:
        # Reserved chars (like space %20 or colon %3a) remain percent-encoded and lowercased
        self.assertEqual(canonical_opc_part_path("ppt/slide%201.xml"), "ppt/slide%201.xml")
        self.assertEqual(canonical_opc_part_path("ppt/data%3A1.xml"), "ppt/data%3a1.xml")

    def test_invalid_characters(self) -> None:
        self.assertIsNone(canonical_opc_part_path(""))
        self.assertIsNone(canonical_opc_part_path("ppt\\presentation.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/presentation.xml?query=1"))
        self.assertIsNone(canonical_opc_part_path("ppt/presentation.xml#fragment"))
        self.assertIsNone(canonical_opc_part_path("ppt/slides/"))
        self.assertIsNone(canonical_opc_part_path("ppt//slides/slide1.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/slide 1.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/slide\t1.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/slide\n1.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/slide\r1.xml"))
        self.assertIsNone(canonical_opc_part_path("\x00ppt/slide1.xml"))
        self.assertIsNone(canonical_opc_part_path("\x1fppt/slide1.xml"))

    def test_invalid_percent_encodings(self) -> None:
        # Truncated
        self.assertIsNone(canonical_opc_part_path("ppt/%2"))
        self.assertIsNone(canonical_opc_part_path("ppt/%"))
        self.assertIsNone(canonical_opc_part_path("ppt/%1"))
        # Non-hex characters
        self.assertIsNone(canonical_opc_part_path("ppt/%ZZ"))
        self.assertIsNone(canonical_opc_part_path("ppt/%1G"))
        self.assertIsNone(canonical_opc_part_path("ppt/%G1"))
        self.assertIsNone(canonical_opc_part_path("ppt/%-1"))
        # Null byte (%00)
        self.assertIsNone(canonical_opc_part_path("ppt/%00"))
        # Encoded forward slash (%2F)
        self.assertIsNone(canonical_opc_part_path("ppt/%2Fslide1.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/%2fslide1.xml"))
        # Encoded backslash (%5C)
        self.assertIsNone(canonical_opc_part_path("ppt/%5Cslide1.xml"))
        self.assertIsNone(canonical_opc_part_path("ppt/%5cslide1.xml"))

    def test_dot_segments(self) -> None:
        self.assertIsNone(canonical_opc_part_path("."))
        self.assertIsNone(canonical_opc_part_path(".."))
        self.assertIsNone(canonical_opc_part_path("foo/."))
        self.assertIsNone(canonical_opc_part_path("foo/.."))
        self.assertIsNone(canonical_opc_part_path("../foo"))
        self.assertIsNone(canonical_opc_part_path("/foo"))
        self.assertIsNone(canonical_opc_part_path("foo/../../bar"))


class SourcePartForRelsTests(unittest.TestCase):
    """Tests for _source_part_for_rels mapping .rels paths to source parts."""

    def test_identifies_source_part_from_rels_path(self) -> None:
        self.assertEqual(
            _source_part_for_rels("ppt/_rels/presentation.xml.rels"),
            "ppt/presentation.xml",
        )
        self.assertEqual(
            _source_part_for_rels("ppt/slides/_rels/slide1.xml.rels"),
            "ppt/slides/slide1.xml",
        )
        self.assertEqual(
            _source_part_for_rels("ppt/slideLayouts/_rels/slideLayout1.xml.rels"),
            "ppt/slideLayouts/slideLayout1.xml",
        )
        self.assertEqual(
            _source_part_for_rels("_rels/document.xml.rels"),
            "document.xml",
        )

    def test_package_level_rels_returns_none(self) -> None:
        self.assertIsNone(_source_part_for_rels("_rels/.rels"))
        self.assertIsNone(_source_part_for_rels(".rels"))
        self.assertIsNone(_source_part_for_rels("ppt/_rels/.rels"))

    def test_non_rels_extension_returns_none(self) -> None:
        self.assertIsNone(_source_part_for_rels("ppt/presentation.xml"))
        self.assertIsNone(_source_part_for_rels("ppt/_rels/presentation.xml"))
        self.assertIsNone(_source_part_for_rels("ppt/_rels/presentation.rels.xml"))


class ResolveInternalOpcTargetTests(unittest.TestCase):
    """Tests for resolve_internal_opc_target resolution and validation."""

    def test_relative_targets_from_rels_path(self) -> None:
        pres_rels = "ppt/_rels/presentation.xml.rels"
        self.assertEqual(
            resolve_internal_opc_target(pres_rels, "slide1.xml"),
            "ppt/slide1.xml",
        )
        self.assertEqual(
            resolve_internal_opc_target(pres_rels, "slides/slide1.xml"),
            "ppt/slides/slide1.xml",
        )

        slide_rels = "ppt/slides/_rels/slide1.xml.rels"
        self.assertEqual(
            resolve_internal_opc_target(slide_rels, "../slideLayouts/slideLayout1.xml"),
            "ppt/slidelayouts/slidelayout1.xml",
        )

        package_rels = "_rels/.rels"
        self.assertEqual(
            resolve_internal_opc_target(package_rels, "ppt/presentation.xml"),
            "ppt/presentation.xml",
        )

    def test_absolute_targets_starting_with_slash(self) -> None:
        pres_rels = "ppt/_rels/presentation.xml.rels"
        self.assertEqual(
            resolve_internal_opc_target(pres_rels, "/ppt/slides/slide1.xml"),
            "ppt/slides/slide1.xml",
        )
        self.assertEqual(
            resolve_internal_opc_target(pres_rels, "/docProps/core.xml"),
            "docprops/core.xml",
        )

    def test_fragment_only_targets(self) -> None:
        slide_rels = "ppt/slides/_rels/slide1.xml.rels"
        self.assertEqual(
            resolve_internal_opc_target(slide_rels, "#slide1"),
            "ppt/slides/slide1.xml",
        )
        pres_rels = "ppt/_rels/presentation.xml.rels"
        self.assertEqual(
            resolve_internal_opc_target(pres_rels, "#heading1"),
            "ppt/presentation.xml",
        )
        # Package-level .rels has no source part, so fragment-only targets return None
        self.assertIsNone(resolve_internal_opc_target("_rels/.rels", "#slide1"))

    def test_invalid_targets(self) -> None:
        pres_rels = "ppt/_rels/presentation.xml.rels"
        # Backslash
        self.assertIsNone(resolve_internal_opc_target(pres_rels, r"slides\slide1.xml"))
        # Query parameters
        self.assertIsNone(resolve_internal_opc_target(pres_rels, "slides/slide1.xml?param=1"))
        self.assertIsNone(resolve_internal_opc_target(pres_rels, "?query"))
        # Spaces and control characters
        self.assertIsNone(resolve_internal_opc_target(pres_rels, "slides/slide 1.xml"))
        self.assertIsNone(resolve_internal_opc_target(pres_rels, "slides/slide\t1.xml"))
        # URI schemes
        self.assertIsNone(
            resolve_internal_opc_target(pres_rels, "http://example.com/slide1.xml")
        )
        self.assertIsNone(
            resolve_internal_opc_target(pres_rels, "https://example.com/slide1.xml")
        )
        self.assertIsNone(
            resolve_internal_opc_target(pres_rels, "mailto:user@example.com")
        )
        # Network location (netloc)
        self.assertIsNone(
            resolve_internal_opc_target(pres_rels, "//server/share/slide1.xml")
        )
        # Empty string
        self.assertIsNone(resolve_internal_opc_target(pres_rels, ""))


class RelationshipsHelperTests(unittest.TestCase):
    """Tests for private helper functions in pptx_opc_validation."""

    def test_relationships_path_for_part(self) -> None:
        part = Path("ppt/presentation.xml")
        expected = Path("ppt/_rels/presentation.xml.rels")
        self.assertEqual(_relationships_path_for_part(part), expected)

        part2 = Path("ppt/slides/slide1.xml")
        expected2 = Path("ppt/slides/_rels/slide1.xml.rels")
        self.assertEqual(_relationships_path_for_part(part2), expected2)

    def test_relationship_attrs_by_id_missing_file(self) -> None:
        non_existent = Path("non/existent/part.xml.rels")
        self.assertEqual(_relationship_attrs_by_id(non_existent), {})

    def test_relationship_attrs_by_id_parses_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            rels_path = Path(tmp_dir) / "test.rels"
            rels_path.write_text(
                f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide1.xml"/>
    <Relationship Id="rId2" Type="{HYPERLINK_REL_TYPE}" Target="https://example.com" TargetMode="External"/>
    <Relationship Type="{SLIDE_REL_TYPE}" Target="missing_id.xml"/>
</Relationships>""",
                encoding="utf-8",
            )
            attrs = _relationship_attrs_by_id(rels_path)
            self.assertEqual(len(attrs), 2)
            self.assertIn("rId1", attrs)
            self.assertEqual(attrs["rId1"]["Target"], "slide1.xml")
            self.assertEqual(attrs["rId1"]["Type"], SLIDE_REL_TYPE)
            self.assertIn("rId2", attrs)
            self.assertEqual(attrs["rId2"]["TargetMode"], "External")

    def test_presentation_slide_roster_empty_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            roster = _presentation_slide_roster(Path(tmp_dir))
            self.assertEqual(roster, set())

    def test_presentation_slide_roster_resolves_slides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "ppt" / "_rels").mkdir(parents=True)
            (root / "ppt" / "presentation.xml").write_text(
                """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:sldIdLst>
        <p:sldId r:id="rId1" id="256"/>
    </p:sldIdLst>
</p:presentation>""",
                encoding="utf-8",
            )
            (root / "ppt" / "_rels" / "presentation.xml.rels").write_text(
                f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slides/slide1.xml"/>
</Relationships>""",
                encoding="utf-8",
            )
            roster = _presentation_slide_roster(root)
            self.assertEqual(roster, {"ppt/slides/slide1.xml"})


class VerifyHyperlinkRelationshipsTests(unittest.TestCase):
    """Tests for verify_hyperlink_relationships validation."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "ppt" / "_rels").mkdir(parents=True)
        (self.root / "ppt" / "slides" / "_rels").mkdir(parents=True)

        # Base presentation.xml with 1 slide
        (self.root / "ppt" / "presentation.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:sldIdLst>
        <p:sldId r:id="rId1" id="256"/>
    </p:sldIdLst>
</p:presentation>""",
            encoding="utf-8",
        )
        (self.root / "ppt" / "_rels" / "presentation.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slides/slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_slide(self, slide_xml: str, rels_xml: str) -> None:
        (self.root / "ppt" / "slides" / "slide1.xml").write_text(
            slide_xml, encoding="utf-8"
        )
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            rels_xml, encoding="utf-8"
        )

    def test_valid_hyperlinks_and_slide_jumps_pass(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1"/>
                            </a:rPr>
                        </a:r>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId2" action="ppaction://hlinksldjump"/>
                            </a:rPr>
                        </a:r>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick action="ppaction://media"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{HYPERLINK_REL_TYPE}" Target="https://example.com" TargetMode="External"/>
    <Relationship Id="rId2" Type="{SLIDE_REL_TYPE}" Target="slide1.xml"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertEqual(problems, [])

    def test_slide_jump_without_relationship_id(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick action="ppaction://hlinksldjump"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}"/>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("slide jump without relationship id" in p for p in problems)
        )

    def test_missing_hyperlink_relationship(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rIdMissing"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}"/>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("missing hyperlink relationship 'rIdMissing'" in p for p in problems)
        )

    def test_hyperlink_relationship_not_external(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{HYPERLINK_REL_TYPE}" Target="https://example.com"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("is not External" in p for p in problems)
        )

    def test_hyperlink_rel_used_for_slide_jump(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1" action="ppaction://hlinksldjump"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{HYPERLINK_REL_TYPE}" Target="https://example.com" TargetMode="External"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("uses an external hyperlink relationship" in p for p in problems)
        )

    def test_slide_relationship_cannot_be_external(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1" action="ppaction://hlinksldjump"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide1.xml" TargetMode="External"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("cannot be External" in p for p in problems)
        )

    def test_slide_relationship_lacks_hlinksldjump_action(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide1.xml"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("lacks hlinksldjump action" in p for p in problems)
        )

    def test_slide_jump_targets_non_roster_part(self) -> None:
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1" action="ppaction://hlinksldjump"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide99.xml"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("targets non-roster part ppt/slides/slide99.xml" in p for p in problems)
        )

    def test_slide_jump_uses_unexpected_relationship_type(self) -> None:
        custom_type = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        )
        slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rId1" action="ppaction://hlinksldjump"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{custom_type}" Target="../media/image1.png"/>
</Relationships>"""
        self._write_slide(slide_xml, rels_xml)
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("uses relationship type" in p for p in problems)
        )

    def test_slide_layout_and_master_inspected(self) -> None:
        (self.root / "ppt" / "slideLayouts" / "_rels").mkdir(parents=True)
        layout_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rIdLayout"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sldLayout>"""
        (self.root / "ppt" / "slideLayouts" / "slideLayout1.xml").write_text(
            layout_xml, encoding="utf-8"
        )
        (self.root / "ppt" / "slideLayouts" / "_rels" / "slideLayout1.xml.rels").write_text(
            f'<Relationships xmlns="{PACKAGE_REL_NS}"/>', encoding="utf-8"
        )
        problems = verify_hyperlink_relationships(self.root)
        self.assertTrue(
            any("missing hyperlink relationship 'rIdLayout'" in p for p in problems)
        )

    def test_malformed_slide_xml_skipped_gracefully(self) -> None:
        (self.root / "ppt" / "slides" / "slide1.xml").write_text(
            "<unclosed_tag>", encoding="utf-8"
        )
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f'<Relationships xmlns="{PACKAGE_REL_NS}"/>', encoding="utf-8"
        )
        problems = verify_hyperlink_relationships(self.root)
        self.assertEqual(problems, [])


class VerifyInternalRelationshipsTests(unittest.TestCase):
    """Tests for verify_internal_relationships package-wide integrity checks."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "_rels").mkdir(parents=True)
        (self.root / "ppt" / "_rels").mkdir(parents=True)
        (self.root / "ppt" / "slides" / "_rels").mkdir(parents=True)

        (self.root / "[Content_Types].xml").write_text(
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
            encoding="utf-8",
        )
        (self.root / "_rels" / ".rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1"
                  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                  Target="ppt/presentation.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        (self.root / "ppt" / "presentation.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:sldIdLst>
        <p:sldId r:id="rId1" id="256"/>
    </p:sldIdLst>
</p:presentation>""",
            encoding="utf-8",
        )
        (self.root / "ppt" / "_rels" / "presentation.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slides/slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        (self.root / "ppt" / "slides" / "slide1.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>""",
            encoding="utf-8",
        )
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}"/>""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_valid_internal_package_passes(self) -> None:
        problems = verify_internal_relationships(self.root)
        self.assertEqual(problems, [])

    def test_missing_target_part(self) -> None:
        # Add relationship pointing to non-existent slide2.xml
        (self.root / "ppt" / "_rels" / "presentation.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slides/slide1.xml"/>
    <Relationship Id="rId2" Type="{SLIDE_REL_TYPE}" Target="slides/slide2.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("ppt/_rels/presentation.xml.rels -> ppt/slides/slide2.xml" in p for p in problems)
        )

    def test_invalid_relationships_xml(self) -> None:
        # Corrupt package-level .rels
        (self.root / "_rels" / ".rels").write_text(
            "<unclosed_relationships", encoding="utf-8"
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("invalid relationships XML" in p for p in problems)
        )
        self.assertTrue(
            any("_rels/.rels" in p for p in problems)
        )

    def test_invalid_relationships_namespace(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://wrong.namespace.com">
    <Relationship Id="rId1" Type="type" Target="slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("invalid Relationships namespace" in p for p in problems)
        )

    def test_invalid_relationships_child(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <UnknownChild Id="rId2"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("invalid relationships child" in p for p in problems)
        )

    def test_missing_relationship_id(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Type="{SLIDE_REL_TYPE}" Target="slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("missing relationship Id" in p for p in problems)
        )

    def test_duplicate_relationship_id(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide1.xml"/>
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("duplicate relationship Id 'rId1'" in p for p in problems)
        )

    def test_missing_relationship_type(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Target="slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("missing relationship Type" in p for p in problems)
        )

    def test_missing_target(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("missing Target" in p for p in problems)
        )

    def test_invalid_target_mode(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slide1.xml" TargetMode="InvalidMode"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("invalid TargetMode 'InvalidMode'" in p for p in problems)
        )

    def test_external_target_mode_skipped(self) -> None:
        # External relationship does not need to exist in local package
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId2" Type="{HYPERLINK_REL_TYPE}" Target="https://external.example.com" TargetMode="External"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertEqual(problems, [])

    def test_invalid_internal_target(self) -> None:
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rId1" Type="{SLIDE_REL_TYPE}" Target="slides\\slide1.xml"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("invalid Target" in p for p in problems)
        )

    def test_cascades_to_verify_hyperlink_relationships(self) -> None:
        # Create a slide with a hyperlink error (hyperlink not external)
        (self.root / "ppt" / "slides" / "slide1.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:hlinkClick r:id="rIdHlink"/>
                            </a:rPr>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>""",
            encoding="utf-8",
        )
        (self.root / "ppt" / "slides" / "_rels" / "slide1.xml.rels").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{PACKAGE_REL_NS}">
    <Relationship Id="rIdHlink" Type="{HYPERLINK_REL_TYPE}" Target="https://example.com"/>
</Relationships>""",
            encoding="utf-8",
        )
        problems = verify_internal_relationships(self.root)
        self.assertTrue(
            any("is not External" in p for p in problems)
        )


if __name__ == "__main__":
    unittest.main()
