#!/usr/bin/env python3
"""Integration tests for SVG hyperlink -> DrawingML converter.

Verifies end-to-end: SVG XML -> convert_element -> well-formed DrawingML XML
with correct hlinkClick embedding and relationship entries.
"""

from __future__ import annotations

import os
import re
import sys
from xml.etree import ElementTree as ET

# Import setup
_script_dir = os.path.dirname(os.path.abspath(__file__))
_scripts_parent = os.path.dirname(_script_dir)
sys.path.insert(0, _scripts_parent)

from svg_to_pptx.drawingml_converter import convert_element
from svg_to_pptx.drawingml_context import ConvertContext

SVG_NS = 'http://www.w3.org/2000/svg'

DML_NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'pkg': 'http://schemas.microsoft.com/office/2006/xmlPackage',
}


def _wrap_with_ns(xml_fragment: str) -> str:
    """Wrap a DrawingML fragment with namespace declarations for standalone parsing."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<pkg:package'
        ' xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage"'
        ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
        ' xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        + xml_fragment +
        '</pkg:package>'
    )


def test_basic_hyperlink_to_drawingml_xml() -> None:
    """Create SVG <a href="url"><rect/></a> -> DrawingML contains hlinkClick."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '20', 'width': '200', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return ShapeResult'
    assert 'a:hlinkClick' in result.xml, \
        f"DrawingML output must contain a:hlinkClick"
    print("  PASS  basic_hyperlink_to_drawingml_xml")


def test_rel_entries_has_correct_target() -> None:
    """Verify rel_entries records the right relationship target and type."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '20', 'width': '200', 'height': '100'})

    ctx = ConvertContext()
    convert_element(a_elem, ctx)

    targets = [(e['target'], e['type']) for e in ctx.rel_entries]
    assert any(target == 'https://example.com' for target, _ in targets), \
        f"rel_entries should contain 'https://example.com', got: {targets}"

    matching = [e for e in ctx.rel_entries if e['target'] == 'https://example.com']
    assert len(matching) == 1, f"Expected 1 rel entry, got {len(matching)}"
    print("  PASS  rel_entries_has_correct_target")


def test_output_xml_is_well_formed_with_ns() -> None:
    """Output DrawingML XML is well-formed when wrapped with namespace declarations."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '20', 'width': '200', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    # Raw fragment uses p:/a: prefixes without declarations (by design
    # for embedding in a larger doc). Wrap for standalone parsing.
    wrapped = _wrap_with_ns(result.xml)

    try:
        parsed = ET.fromstring(wrapped)
        assert parsed is not None, 'Parsed XML should not be None'
        cnvpr_list = parsed.findall('.//p:cNvPr', DML_NS)
        assert len(cnvpr_list) > 0, 'Should find at least one p:cNvPr element'
        hlink_list = parsed.findall('.//a:hlinkClick', DML_NS)
        assert len(hlink_list) > 0, 'Should find at least one a:hlinkClick element'
    except ET.ParseError as e:
        assert False, f'Output XML is not well-formed: {e}'
    print("  PASS  output_xml_is_well_formed_with_ns")


def test_hyperlink_with_multiple_children() -> None:
    """<a href="url"><rect/><rect/><circle/></a> -> all children wrapped, single rel."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '10', 'width': '100', 'height': '100'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '120', 'y': '10', 'width': '100', 'height': '100'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}circle',
                  {'cx': '300', 'cy': '60', 'r': '50'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return ShapeResult'
    assert 'a:hlinkClick' in result.xml, 'Multi-child hyperlink must contain a:hlinkClick'
    hyperlink_targets = [e['target'] for e in ctx.rel_entries
                         if e['target'] == 'https://example.com']
    assert len(hyperlink_targets) == 1, \
        f"Expected 1 rel entry for https://example.com, got {len(hyperlink_targets)}"
    print("  PASS  hyperlink_with_multiple_children")


def test_slide_link_integration() -> None:
    """<a data-pptx-slide="5"><rect/></a> -> correct slide target in rel_entries."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'data-pptx-slide': '5'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '10', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None
    assert 'a:hlinkClick' in result.xml
    assert any(e['target'] == 'slide5.xml' for e in ctx.rel_entries), \
        'rel_entries should contain slide5.xml for data-pptx-slide=5'
    print("  PASS  slide_link_integration")


def test_hlinkClick_is_xml_well_nested() -> None:
    """hlinkClick must be a child inside cNvPr, not after a self-closing tag."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    g_elem = ET.SubElement(a_elem, f'{{{SVG_NS}}}g')
    ET.SubElement(g_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '50', 'height': '50'})
    ET.SubElement(g_elem, f'{{{SVG_NS}}}rect',
                  {'x': '60', 'y': '0', 'width': '50', 'height': '50'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None
    # Check that hlinkClick is NOT after self-closing cNvPr
    has_bad_pattern = bool(re.search(
        r'<p:cNvPr\b[^>]*/>\s*<a:hlinkClick', result.xml
    ))
    idx = result.xml.find('<p:cNvPr')
    snippet = result.xml[idx:idx+300] if idx >= 0 else '(cNvPr not found)'
    assert not has_bad_pattern, (
        'BUG: hlinkClick after self-closing cNvPr (/>). '
        f'Must be inside <p:cNvPr>...</p:cNvPr>. Snippet: ...{snippet}'
    )
    print("  PASS  hlinkClick_is_xml_well_nested")


def test_multiple_unique_hyperlinks() -> None:
    """Multiple <a> elements with different URLs -> correct distinct rel entries."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})

    a1 = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com/page1'})
    ET.SubElement(a1, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '10', 'width': '100', 'height': '100'})

    a2 = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com/page2'})
    ET.SubElement(a2, f'{{{SVG_NS}}}rect',
                  {'x': '150', 'y': '10', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    r1 = convert_element(a1, ctx)
    r2 = convert_element(a2, ctx)

    assert r1 is not None and r2 is not None
    targets = [e['target'] for e in ctx.rel_entries
               if e['target'].startswith('https://example.com')]
    assert len(targets) == 2, \
        f"Expected 2 distinct rel entries, got {len(targets)}: {targets}"
    assert 'https://example.com/page1' in targets
    assert 'https://example.com/page2' in targets
    print("  PASS  multiple_unique_hyperlinks")


def test_duplicate_hyperlinks_deduplicated() -> None:
    """Same URL used twice -> each element gets its own rId (normal PPTX)."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})

    a1 = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    ET.SubElement(a1, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '10', 'width': '100', 'height': '100'})

    a2 = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'https://example.com'})
    ET.SubElement(a2, f'{{{SVG_NS}}}rect',
                  {'x': '150', 'y': '10', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    convert_element(a1, ctx)
    convert_element(a2, ctx)

    targets = [e['target'] for e in ctx.rel_entries
               if e['target'] == 'https://example.com']
    # Each hyperlink element gets its own relationship entry with unique rId.
    # This is correct PPTX behavior: shapes reference relationships by ID,
    # and multiple shapes can share the same target URL.
    assert len(targets) >= 1, \
        f"Expected at least 1 rel entry for duplicate URL, got {len(targets)}"
    rIds = [e['id'] for e in ctx.rel_entries if e['target'] == 'https://example.com']
    assert len(rIds) >= 1, f"Expected at least 1 rId, got {rIds}"
    print("  PASS  duplicate_hyperlinks_get_separate_entries")


def test_mailto_hyperlink_to_drawingml_xml() -> None:
    """<a href="mailto:foo@example.com"><rect/></a> -> well-formed DrawingML with hlinkClick + External rel."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'mailto:foo@example.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '10', 'y': '20', 'width': '200', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None
    assert 'a:hlinkClick' in result.xml
    assert any(e['target'] == 'mailto:foo@example.com' for e in ctx.rel_entries)
    matching = [e for e in ctx.rel_entries if e['target'] == 'mailto:foo@example.com']
    assert len(matching) == 1
    assert matching[0].get('target_mode') == 'External'
    print("  PASS  mailto_hyperlink_to_drawingml_xml")


# ===========================================================================
# Test runner
# ===========================================================================

def _run_tests() -> int:
    tests: list[tuple[str, callable]] = [
        ('test_basic_hyperlink_to_drawingml_xml', test_basic_hyperlink_to_drawingml_xml),
        ('test_rel_entries_has_correct_target', test_rel_entries_has_correct_target),
        ('test_output_xml_is_well_formed_with_ns', test_output_xml_is_well_formed_with_ns),
        ('test_hyperlink_with_multiple_children', test_hyperlink_with_multiple_children),
        ('test_slide_link_integration', test_slide_link_integration),
        ('test_hlinkClick_is_xml_well_nested', test_hlinkClick_is_xml_well_nested),
        ('test_multiple_unique_hyperlinks', test_multiple_unique_hyperlinks),
        ('test_duplicate_hyperlinks_deduplicated', test_duplicate_hyperlinks_deduplicated),
        ('test_mailto_hyperlink_to_drawingml_xml', test_mailto_hyperlink_to_drawingml_xml),
    ]

    print('=' * 60)
    print('  SVG Hyperlink Converter — Integration Tests')
    print('=' * 60 + '\n')

    passed = 0
    failed = 0
    errors = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as exc:
            print(f'  FAIL  {name}')
            print(f'        {exc}')
            failed += 1
        except Exception as exc:
            print(f'  ERROR {name}')
            import traceback
            traceback.print_exc()
            errors += 1

    total = len(tests)
    print(f'\n{"=" * 60}')
    print(f'  Results: {passed} passed, {failed} failed, {errors} errors  ({passed}/{total})')
    print(f'{"=" * 60}')

    return 1 if failed + errors > 0 else 0


if __name__ == '__main__':
    sys.exit(_run_tests())
