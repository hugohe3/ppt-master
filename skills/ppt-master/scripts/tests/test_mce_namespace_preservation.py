#!/usr/bin/env python3
"""PPT Master - MCE Namespace Preservation Regression Tests

Exercise MCE prefix and QName namespace declarations in the source XML
serializer without requiring optional lxml or python-pptx dependencies.

Usage:
    python3 -m unittest tests.test_mce_namespace_preservation

Dependencies:
    Standard library.
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pptx_transitions import (
    _inject_root_namespace_declarations,
    namespace_bindings,
    serialize_source_xml,
    validate_mce_prefixes,
)

try:
    from lxml import etree as LET
except ImportError:
    LET = None


PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
VENDOR_NS = "urn:example:mce-prefix"


class MceNamespacePreservationTests(unittest.TestCase):
    def _slide(self, attributes: str, body: str = "<p:cSld/>") -> str:
        return (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            f'xmlns:x14="{VENDOR_NS}" {attributes}>{body}</p:sld>'
        )

    def _namespace_bindings_by_id(
        self, xml_data: bytes, element_id: str, prefix: str,
    ) -> str | None:
        scopes: list[dict[str, str]] = [{}]
        declarations: dict[str, str] = {}
        for event, item in ET.iterparse(
            io.BytesIO(xml_data),
            events=("start-ns", "start", "end"),
        ):
            if event == "start-ns":
                namespace_prefix, uri = item
                declarations[namespace_prefix] = uri
            elif event == "start":
                scope = {**scopes[-1], **declarations}
                declarations.clear()
                scopes.append(scope)
                if item.get("id") == element_id:
                    return scope.get(prefix)
            else:
                scopes.pop()
        return None

    def test_individual_qname_attributes_preserve_namespace(self) -> None:
        for attribute in (
            "ProcessContent",
            "PreserveElements",
            "PreserveAttributes",
        ):
            with self.subTest(attribute=attribute):
                source = self._slide(
                    f'mc:{attribute}="x14:{attribute.lower()}"'
                )
                root = ET.fromstring(source)
                output = serialize_source_xml(root, source)
                self.assertEqual(
                    namespace_bindings(output).get("x14"),
                    VENDOR_NS,
                )
                self.assertEqual(validate_mce_prefixes(output), [])

    def test_must_understand_preserves_prefix_list_namespace(self) -> None:
        source = self._slide("mc:MustUnderstand=\"x14 vendor\"")
        source = source.replace(
            'xmlns:x14="urn:example:mce-prefix"',
            'xmlns:x14="urn:example:mce-prefix" '
            'xmlns:vendor="urn:example:vendor"',
        )
        root = ET.fromstring(source)
        output = serialize_source_xml(root, source)
        bindings = namespace_bindings(output)
        self.assertEqual(bindings.get("x14"), VENDOR_NS)
        self.assertEqual(bindings.get("vendor"), "urn:example:vendor")
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_multiple_qname_references_preserve_all_namespaces(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'xmlns:x14="urn:example:x14" xmlns:a15="urn:example:a15" '
            'mc:ProcessContent="x14:choice a15:shape" '
            'mc:PreserveElements="x14:element" '
            'mc:PreserveAttributes="a15:attribute"/>'
        )
        root = ET.fromstring(source)
        output = serialize_source_xml(root, source)
        bindings = namespace_bindings(output)
        self.assertEqual(bindings.get("x14"), "urn:example:x14")
        self.assertEqual(bindings.get("a15"), "urn:example:a15")
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_unqualified_element_qnames_use_default_namespace(self) -> None:
        for attribute in ("ProcessContent", "PreserveElements"):
            with self.subTest(attribute=attribute):
                source = (
                    '<root xmlns="urn:example:default" '
                    f'xmlns:mc="{MC_NS}" mc:{attribute}="element"/>'
                )
                root = LET.fromstring(source) if LET is not None else ET.fromstring(source)
                output = serialize_source_xml(root, source)
                text = output.decode("utf-8")
                self.assertIn('xmlns="urn:example:default"', text)
                self.assertNotIn("xmlns:=", text)
                self.assertEqual(validate_mce_prefixes(output), [])

    def test_unqualified_attribute_qname_uses_no_namespace(self) -> None:
        source = (
            '<root xmlns="urn:example:default" '
            f'xmlns:mc="{MC_NS}" mc:PreserveAttributes="attribute"/>'
        )
        root = LET.fromstring(source) if LET is not None else ET.fromstring(source)
        output = serialize_source_xml(root, source)
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_unqualified_element_qname_without_default_namespace_is_valid(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" mc:ProcessContent="element"/>'
        )
        root = LET.fromstring(source) if LET is not None else ET.fromstring(source)
        output = serialize_source_xml(root, source)
        text = output.decode("utf-8")
        self.assertNotIn("xmlns:='", text)
        self.assertNotIn("xmlns:=\"", text)
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_nested_declaration_is_preserved_in_lexical_scope(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'xmlns:x14="urn:example:outer">'
            '<p:cSld><p:sp mc:PreserveElements="x14:element" '
            'xmlns:x14="urn:example:inner"/></p:cSld></p:sld>'
        )
        root = ET.fromstring(source)
        output = serialize_source_xml(root, source)
        parsed = ET.fromstring(output)
        sp = parsed.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}sp")
        self.assertIsNotNone(sp)
        self.assertIn("x14", output.decode("utf-8"))
        self.assertIn("urn:example:inner", output.decode("utf-8"))
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_unbound_qname_prefix_fails_validation_and_serialization(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'mc:ProcessContent="missing:element"/>'
        )
        root = ET.fromstring(source)
        self.assertIn(
            "MCE QName prefix is not bound: missing",
            "; ".join(validate_mce_prefixes(source)),
        )
        with self.assertRaisesRegex(
            ValueError,
            "MCE prefix 'missing' has no namespace binding",
        ):
            serialize_source_xml(root, source)

    def test_unbound_prefix_list_fails_validation_and_serialization(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'mc:MustUnderstand="missing"/>'
        )
        root = ET.fromstring(source)
        self.assertIn(
            "MCE namespace prefix is not bound: missing",
            "; ".join(validate_mce_prefixes(source)),
        )
        with self.assertRaisesRegex(
            ValueError,
            "MCE prefix 'missing' has no namespace binding",
        ):
            serialize_source_xml(root, source)

    def test_ignorable_and_choice_require_survive(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'xmlns:a14="urn:example:a14" mc:Ignorable="a14">'
            f'<mc:Choice Requires="a14"/></p:sld>'
        )
        root = ET.fromstring(source)
        output = serialize_source_xml(root, source)
        bindings = namespace_bindings(output)
        self.assertEqual(bindings.get("a14"), "urn:example:a14")
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_conflicting_qname_binding_fails_closed(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" xmlns:a14="urn:original" '
            'mc:ProcessContent="a14:element"/>'
        )
        root = ET.fromstring(source)
        with self.assertRaisesRegex(
            ValueError,
            "Conflicting MCE namespace binding",
        ):
            serialize_source_xml(
                root,
                source,
                additional_bindings={"a14": "urn:generated"},
            )

    def test_nested_generated_reference_uses_lexical_binding(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" xmlns:feature="urn:outer">'
            '<shape xmlns:feature="urn:inner">'
            '<detail mc:ProcessContent="feature:element"/></shape></root>'
        )
        root = ET.fromstring(source)
        output = serialize_source_xml(root, source)
        self.assertIn("urn:inner", output.decode("utf-8"))
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_shadowed_prefix_keeps_root_and_nested_bindings(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" xmlns:feature="urn:outer" '
            'mc:Ignorable="feature">'
            '<shape xmlns:feature="urn:inner" '
            'mc:PreserveElements="feature:element"/></root>'
        )
        root = LET.fromstring(source) if LET is not None else ET.fromstring(source)
        output = serialize_source_xml(root, source)
        text = output.decode("utf-8")
        self.assertIn('xmlns:feature="urn:outer"', text)
        self.assertIn('<shape xmlns:feature="urn:inner"', text)
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_reordered_elements_keep_their_lexical_prefix_bindings(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}">'
            '<a id="A" xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<b id="B" xmlns:feature="urn:example:B" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        )
        root = ET.fromstring(source)
        root[:] = list(reversed(root[:]))

        output = serialize_source_xml(root, source)

        self.assertEqual(
            self._namespace_bindings_by_id(output, "A", "feature"),
            "urn:example:A",
        )
        self.assertEqual(
            self._namespace_bindings_by_id(output, "B", "feature"),
            "urn:example:B",
        )
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_inserted_and_deleted_elements_do_not_shift_source_bindings(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}">'
            '<a id="A" xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<b id="B" xmlns:feature="urn:example:B" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        )
        root = ET.fromstring(source)
        root.remove(root[1])
        root.extend((ET.Element("inserted"), ET.Element("another-inserted")))

        output = serialize_source_xml(root, source)

        self.assertEqual(
            self._namespace_bindings_by_id(output, "A", "feature"),
            "urn:example:A",
        )
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_root_and_reordered_shadowed_prefixes_keep_distinct_bindings(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" xmlns:feature="urn:example:root" '
            'mc:Ignorable="feature">'
            '<item id="A" xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<item id="B" xmlns:feature="urn:example:B" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        )
        root = ET.fromstring(source)
        root[:] = list(reversed(root[:]))

        output = serialize_source_xml(root, source)

        parsed = minidom.parseString(output)
        self.assertEqual(
            parsed.documentElement.getAttribute("xmlns:feature"),
            "urn:example:root",
        )
        self.assertEqual(
            self._namespace_bindings_by_id(output, "A", "feature"),
            "urn:example:A",
        )
        self.assertEqual(
            self._namespace_bindings_by_id(output, "B", "feature"),
            "urn:example:B",
        )
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_unmatched_mce_reference_in_different_structure_fails_closed(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}">'
            '<old-structure id="A" xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        )
        output_root = ET.fromstring(
            f'<root xmlns:mc="{MC_NS}"><new-structure>'
            '<item id="A" mc:MustUnderstand="feature"/>'
            "</new-structure></root>"
        )

        with self.assertRaisesRegex(
            ValueError,
            "no namespace binding in source or generated XML",
        ):
            serialize_source_xml(output_root, source)

    def test_comments_cdata_and_quoted_delimiters_are_not_scanned_as_tags(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}">'
            '<a id="A" xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<b id="B" xmlns:feature="urn:example:B" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        )
        serialized = (
            f'<?xml version="1.0" encoding="utf-8"?><root xmlns:mc="{MC_NS}" '
            'note="quoted > delimiter"><!-- <fake id="comment"/> -->'
            '<![CDATA[<fake id="cdata"/>]]>'
            '<a id="A" mc:MustUnderstand="feature"/>'
            '<b id="B" mc:MustUnderstand="feature"/></root>'
        ).encode("utf-8")

        output = _inject_root_namespace_declarations(
            serialized,
            prefixes={"feature"},
            source_xml=source,
        )

        self.assertIn(b'<!-- <fake id="comment"/> -->', output)
        self.assertIn(b'<![CDATA[<fake id="cdata"/>]]>', output)
        self.assertEqual(
            self._namespace_bindings_by_id(output, "A", "feature"),
            "urn:example:A",
        )
        self.assertEqual(
            self._namespace_bindings_by_id(output, "B", "feature"),
            "urn:example:B",
        )
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_existing_generated_binding_is_accepted_without_rewriting_xml(self) -> None:
        source = f'<root xmlns:mc="{MC_NS}"/>'
        serialized = (
            f'<root xmlns:mc="{MC_NS}">'
            '<mc:Choice xmlns:feature="urn:generated" Requires="feature"/>'
            "</root>"
        ).encode("utf-8")

        output = _inject_root_namespace_declarations(
            serialized,
            prefixes={"feature"},
            source_xml=source,
        )

        self.assertEqual(output, serialized)
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_duplicate_unidentified_source_paths_are_not_merged_as_correspondence(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}">'
            '<item xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<item xmlns:other="urn:example:B" '
            'mc:MustUnderstand="other"/>'
            "</root>"
        )
        serialized = (
            f'<root xmlns:mc="{MC_NS}">'
            '<item mc:MustUnderstand="feature"/>'
            "</root>"
        ).encode("utf-8")

        with self.assertRaisesRegex(
            ValueError,
            "ambiguous source-to-output correspondence",
        ):
            _inject_root_namespace_declarations(
                serialized,
                prefixes={"feature"},
                source_xml=source,
            )

    def test_duplicate_unidentified_source_paths_keep_explicit_output_bindings(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}">'
            '<item xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<item xmlns:other="urn:example:B" '
            'mc:MustUnderstand="other"/>'
            "</root>"
        )
        serialized = (
            f'<root xmlns:mc="{MC_NS}">'
            '<item xmlns:feature="urn:generated" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        ).encode("utf-8")

        output = _inject_root_namespace_declarations(
            serialized,
            prefixes={"feature"},
            source_xml=source,
        )

        self.assertEqual(output, serialized)
        self.assertEqual(validate_mce_prefixes(output), [])

    def test_duplicate_unidentified_paths_do_not_fall_back_to_root_binding(self) -> None:
        source = (
            f'<root xmlns:mc="{MC_NS}" xmlns:feature="urn:example:root" '
            'mc:Ignorable="feature">'
            '<item xmlns:feature="urn:example:A" '
            'mc:MustUnderstand="feature"/>'
            '<item xmlns:feature="urn:example:B" '
            'mc:MustUnderstand="feature"/>'
            "</root>"
        )
        serialized = (
            f'<root xmlns:mc="{MC_NS}" xmlns:feature="urn:example:root" '
            'mc:Ignorable="feature">'
            '<item mc:MustUnderstand="feature"/>'
            "</root>"
        ).encode("utf-8")

        with self.assertRaisesRegex(
            ValueError,
            "ambiguous source-to-output correspondence",
        ):
            _inject_root_namespace_declarations(
                serialized,
                prefixes={"feature"},
                source_xml=source,
            )

    def test_self_closing_root_namespace_is_inserted_before_slash(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'xmlns:x14="urn:example:mce-prefix" '
            'mc:ProcessContent="x14:content"/>'
        )
        root = ET.fromstring(source)
        output = serialize_source_xml(root, source)
        text = output.decode("utf-8")
        self.assertIn('xmlns:x14="urn:example:mce-prefix"', text)
        self.assertIn('xmlns:x14="urn:example:mce-prefix"/>', text)
        self.assertEqual(validate_mce_prefixes(output), [])

    @unittest.skipUnless(LET is not None, "lxml is not installed")
    def test_lxml_path_preserves_and_validates_qname_binding(self) -> None:
        source = (
            f'<p:sld xmlns:p="{PML_NS}" xmlns:mc="{MC_NS}" '
            'xmlns:x14="urn:example:mce-prefix" '
            'mc:PreserveElements="x14:element"/>'
        )
        root = LET.fromstring(source.encode("utf-8"))
        output = serialize_source_xml(root, source)
        parsed = LET.fromstring(output)
        self.assertEqual(
            parsed.nsmap.get("x14"),
            VENDOR_NS,
        )
        self.assertEqual(validate_mce_prefixes(output), [])


if __name__ == "__main__":
    unittest.main()
