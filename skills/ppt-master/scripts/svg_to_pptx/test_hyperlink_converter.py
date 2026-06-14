#!/usr/bin/env python3
"""Unit tests for SVG-to-DrawingML hyperlink converter (``convert_a``).

Tests exercise normal cases, the Bug 1 scenario (nested empty <a> leaking
parent hlink), and the Bug 2 scenario (self-closing <p:cNvPr/> regex
mismatch).  Uses TDD discipline: Bug 1 and Bug 2 tests MUST FAIL until the
production bugs are fixed.
"""

from __future__ import annotations

import os
import re
import sys
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Import setup — ensure the svg_to_pptx package is discoverable
# ---------------------------------------------------------------------------
_script_dir = os.path.dirname(os.path.abspath(__file__))
_scripts_parent = os.path.dirname(_script_dir)
sys.path.insert(0, _scripts_parent)

from svg_to_pptx.drawingml_converter import convert_element       # noqa: E402
from svg_to_pptx.drawingml_context import ConvertContext           # noqa: E402
from svg_to_pptx.drawingml_elements import _process_a_children    # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SVG_NS = 'http://www.w3.org/2000/svg'

_HLINK_CLICK_TAG = 'a:hlinkClick'


# ===========================================================================
# Helper
# ===========================================================================

def _has_hlink_after_selfclose(xml: str) -> bool:
    """Return True if any self-closing cNvPr tag is followed by hlinkClick."""
    return bool(re.search(r'<p:cNvPr\b[^>]*/>\s*<a:hlinkClick', xml))


# ===========================================================================
# Test 1 — Normal external hyperlink
# ===========================================================================

def test_normal_href() -> None:
    """<a href="http://test.com"><rect/></a> → output carries hlinkClick."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'http://test.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    assert _HLINK_CLICK_TAG in result.xml, \
        f'result XML should contain {_HLINK_CLICK_TAG}'
    assert any(e['target'] == 'http://test.com' for e in ctx.rel_entries), \
        'rel_entries should contain http://test.com'


# ===========================================================================
# Test 2 — Internal slide link
# ===========================================================================

def test_slide_link() -> None:
    """<a data-pptx-slide="3"><rect/></a> → slide target registered."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'data-pptx-slide': '3'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    assert _HLINK_CLICK_TAG in result.xml, \
        f'result XML should contain {_HLINK_CLICK_TAG}'
    assert any(e['target'] == 'slide3.xml' for e in ctx.rel_entries), \
        'rel_entries should contain slide3.xml'


# ===========================================================================
# Test 3 — Unsupported URL scheme rejected
# ===========================================================================

def test_unsupported_scheme_rejected() -> None:
    """<a href="javascript:alert(1)">… → no hlinkClick, no rel entry."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a',
                           {'href': 'javascript:alert(1)'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    assert _HLINK_CLICK_TAG not in result.xml, \
        f'{_HLINK_CLICK_TAG} should NOT appear for unsupported scheme'
    assert len(ctx.rel_entries) == 0, \
        'rel_entries should be empty for unsupported scheme'


# ===========================================================================
# Test 3b — file:// scheme blocked (added to UNSUPPORTED_URL_SCHEMES)
# ===========================================================================

def test_file_scheme_rejected() -> None:
    """<a href="file:///etc/passwd">… → no hlinkClick, no rel entry."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a',
                           {'href': 'file:///etc/passwd'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    assert _HLINK_CLICK_TAG not in result.xml, \
        f'{_HLINK_CLICK_TAG} should NOT appear for file:// scheme'
    assert len(ctx.rel_entries) == 0, \
        'rel_entries should be empty for file:// scheme'

# ===========================================================================
# Test 4 — Bug 1: nested empty <a> must NOT leak parent hlink
# ===========================================================================

def test_nested_empty_a_no_hlink_leak() -> None:
    """Empty <a> must clear hlink inherited from parent context.

    An empty <a> in a tree where the parent ConvertContext carries hlink_href
    should clear it for its subtree via ``ctx.child()``. Before the fix,
    ``ctx.child()`` copied hlink_href/hlink_slide and the empty <a> would
    silently leak the parent hyperlink to its children.

    Build::

        parent ctx with hlink_href='http://outer.com'
            <a>           ← empty (no href / no data-pptx-slide)
              <rect/>     ← must NOT get parent hlink
            </a>
    """
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    inner_a = ET.SubElement(svg, f'{{{SVG_NS}}}a')          # empty — no attrs
    ET.SubElement(inner_a, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    ctx.hlink_href = 'http://outer.com'         # simulate parent hyperlink
    convert_element(inner_a, ctx)

    # The empty <a> must clear hlink — rect must NOT inherit http://outer.com.
    assert not any(e['target'] == 'http://outer.com' for e in ctx.rel_entries), \
        ('BUG 1 — empty <a> leaked parent hlink: rel_entries contains '
         'http://outer.com.  The empty <a> should act as a hyperlink '
         'blocker for its subtree.')

# ===========================================================================
# Test 5 — Bug 2: self-closing <p:cNvPr/> regex mismatch
# ===========================================================================

def test_self_closing_cnvpr_with_group() -> None:
    """Single-child <g> inside <a> → hlinkClick must be inside cNvPr.

    Build::

        <a href="http://test.com">
          <g>
            <rect/>  ← multiple children force a <p:grpSp> wrapper
            <rect/>
          </g>
        </a>

    ``convert_g`` produces a self-closing ``<p:cNvPr id="N" name="Group N"/>``
    (no hlink because child ctx was cleared).  ``convert_a`` then tries::

        re.sub(r'(<p:cNvPr[^>]*>)', rf'\1{hlink}', result.xml, count=1)

    The regex *matches* the self-closing form but the back-reference captures
    ``<p:cNvPr …/`` — leaving ``>`` after it.  Replacement produces::

        <p:cNvPr …/><a:hlinkClick r:id="rId1"/>

    instead of::

        <p:cNvPr …><a:hlinkClick r:id="rId1"/></p:cNvPr>

    Fixed: no longer broken — _build_cnvpr_xml handles both self-closing and non-self-closing forms.
    """
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a', {'href': 'http://test.com'})
    g_elem = ET.SubElement(a_elem, f'{{{SVG_NS}}}g')              # no id / no anim
    ET.SubElement(g_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '50', 'height': '50'})
    ET.SubElement(g_elem, f'{{{SVG_NS}}}rect',
                  {'x': '60', 'y': '60', 'width': '50', 'height': '50'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'

    # Detect the bug pattern: self-closing cNvPr immediately followed by hlink
    assert not _has_hlink_after_selfclose(result.xml), \
        ('BUG 2 — hlinkClick appears after self-closing cNvPr (/>): '
         'the regex in convert_a does not handle /> tags.  '
         'hlinkClick should live *inside* <p:cNvPr>…</p:cNvPr>, not after />.')


# ===========================================================================
# Test 6 — Text <a> unsafe scheme rejected
# ===========================================================================

def test_text_a_unsafe_scheme_rejected() -> None:
    """<text><a href="javascript:..."><tspan>text</tspan></a></text> → no hlink in runs."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    text_el = ET.SubElement(svg, f'{{{SVG_NS}}}text',
                             {'x': '100', 'y': '100', 'font-size': '16'})
    a_el = ET.SubElement(text_el, f'{{{SVG_NS}}}a',
                          {'href': 'javascript:alert(1)'})
    ET.SubElement(a_el, f'{{{SVG_NS}}}tspan', {'fill': 'blue'}).text = 'click me'

    ctx = ConvertContext()
    result = convert_element(text_el, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    # Should NOT contain hlinkClick for the unsafe scheme
    assert 'javascript' not in result.xml, (
        'javascript scheme should be filtered from text hyperlink'
    )
    assert not any('javascript' in e.get('target', '') for e in ctx.rel_entries), (
        'rel_entries should not contain javascript URL'
    )


# ===========================================================================
# Test 7 — Tspan <a> unsafe scheme rejected
# ===========================================================================

def test_tspan_a_unsafe_scheme_rejected() -> None:
    """<tspan><a href="javascript:..."><tspan>text</tspan></a></tspan> → no hlink."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    text_el = ET.SubElement(svg, f'{{{SVG_NS}}}text',
                             {'x': '100', 'y': '100', 'font-size': '16'})
    outer_tspan = ET.SubElement(text_el, f'{{{SVG_NS}}}tspan')
    a_el = ET.SubElement(outer_tspan, f'{{{SVG_NS}}}a',
                          {'href': 'javascript:alert(1)'})
    ET.SubElement(a_el, f'{{{SVG_NS}}}tspan', {'fill': 'red'}).text = 'danger'

    ctx = ConvertContext()
    result = convert_element(text_el, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    assert 'javascript' not in result.xml, (
        'javascript scheme should be filtered from tspan-nested hyperlink'
    )
    assert not any('javascript' in e.get('target', '') for e in ctx.rel_entries), (
        'rel_entries should not contain javascript URL'
    )


# ===========================================================================
# Test 8 — Nested <a> tail text captured
# ===========================================================================

def test_nested_a_tail_text_captured() -> None:
    """Nested <a> with tail text after inner </a> → tail text preserved."""
    outer_a = ET.Element(f'{{{SVG_NS}}}a', {'href': 'https://outer.com'})
    outer_a.text = 'prefix '
    inner_a = ET.SubElement(outer_a, f'{{{SVG_NS}}}a',
                             {'href': 'https://inner.com'})
    inner_tspan = ET.SubElement(inner_a, f'{{{SVG_NS}}}tspan')
    inner_tspan.text = 'inner text'
    inner_a.tail = ' suffix'

    inherited = {'hlink_href': 'https://outer.com'}
    runs: list = []
    _process_a_children(outer_a, inherited, False, runs)

    texts = [r['text'] for r in runs]
    assert 'prefix ' in texts, f"prefix text missing from runs: {texts}"
    assert 'inner text' in texts, f"inner text missing from runs: {texts}"
    assert ' suffix' in texts, f"tail text after nested </a> missing from runs: {texts}"
    # Inner runs should have inner URL
    inner_runs = [r for r in runs if r.get('hlink_href') == 'https://inner.com']
    assert len(inner_runs) > 0, 'inner hyperlink should be on inner runs'
    # Tail run should have outer URL
    tail_runs = [r for r in runs if r['text'] == ' suffix']
    assert tail_runs, 'tail run should exist'
    assert tail_runs[0].get('hlink_href') == 'https://outer.com', (
        f'tail run should inherit outer href, got {tail_runs[0]}'
    )


# ===========================================================================
# Test 9 — XML escaping in _append_relationship
# ===========================================================================

def test_append_relationship_xml_escape() -> None:
    """_append_relationship escapes &, <, >, \" in id/type/target."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        rels_path = Path(tmpdir) / 'test.xml.rels'
        rels_path.write_text(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '</Relationships>'
        )
        # We'll test via direct XML check since _append_relationship
        # reads/writes the file. Instead, verify _xml_escape handles the
        # special characters that could appear in relationship targets.
        from svg_to_pptx.drawingml_utils import _xml_escape

        # Characters that MUST be escaped in XML attributes
        assert _xml_escape('&') == '&amp;'
        assert _xml_escape('<') == '&lt;'
        assert _xml_escape('>') == '&gt;'
        assert _xml_escape('"') == '&quot;'
        # URLs with query parameters containing & should be escaped
        escaped_url = _xml_escape('https://example.com?a=1&b=2')
        assert '&amp;' in escaped_url
        assert '&b' not in escaped_url


# ===========================================================================
# Test 10 — mailto: scheme is allowed
# ===========================================================================

def test_mailto_scheme_allowed() -> None:
    """<a href="mailto:foo@example.com">… → hlinkClick generated, rel registered."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a',
                           {'href': 'mailto:foo@example.com'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None, 'convert_element should return a ShapeResult'
    assert _HLINK_CLICK_TAG in result.xml, \
        f'{_HLINK_CLICK_TAG} should appear for mailto: scheme'
    assert any(e['target'] == 'mailto:foo@example.com' for e in ctx.rel_entries), \
        'rel_entries should contain mailto:foo@example.com'


# ===========================================================================
# Test 11 — tel: scheme is allowed
# ===========================================================================

def test_tel_scheme_allowed() -> None:
    """<a href="tel:+15550123">… → hlinkClick generated, rel registered."""
    svg = ET.Element(f'{{{SVG_NS}}}svg', {'viewBox': '0 0 1280 720'})
    a_elem = ET.SubElement(svg, f'{{{SVG_NS}}}a',
                           {'href': 'tel:+15550123'})
    ET.SubElement(a_elem, f'{{{SVG_NS}}}rect',
                  {'x': '0', 'y': '0', 'width': '100', 'height': '100'})

    ctx = ConvertContext()
    result = convert_element(a_elem, ctx)

    assert result is not None
    assert _HLINK_CLICK_TAG in result.xml
    assert any(e['target'] == 'tel:+15550123' for e in ctx.rel_entries), \
        'rel_entries should contain tel:+15550123'


# ===========================================================================
# Test runner
# ===========================================================================

def _run_tests() -> int:
    """Run all test functions and print a pass/fail summary.

    Returns 0 so the script always exits cleanly.
    """
    tests: list[tuple[str, callable]] = [              # type: ignore[name-defined]
        ('test_normal_href', test_normal_href),
        ('test_slide_link', test_slide_link),
        ('test_unsupported_scheme_rejected', test_unsupported_scheme_rejected),
        ('test_file_scheme_rejected', test_file_scheme_rejected),
        ('test_nested_empty_a_no_hlink_leak (Bug 1)', test_nested_empty_a_no_hlink_leak),
        ('test_self_closing_cnvpr_with_group (Bug 2)', test_self_closing_cnvpr_with_group),
        ('test_text_a_unsafe_scheme_rejected', test_text_a_unsafe_scheme_rejected),
        ('test_tspan_a_unsafe_scheme_rejected', test_tspan_a_unsafe_scheme_rejected),
        ('test_nested_a_tail_text_captured', test_nested_a_tail_text_captured),
        ('test_append_relationship_xml_escape', test_append_relationship_xml_escape),
        ('test_mailto_scheme_allowed', test_mailto_scheme_allowed),
        ('test_tel_scheme_allowed', test_tel_scheme_allowed),
    ]
    passed = 0
    failed = 0
    errors = 0

    print(f'{"=" * 60}')
    print('  SVG Hyperlink Converter — Unit Tests')
    print(f'{"=" * 60}\n')

    for name, test_fn in tests:
        try:
            test_fn()
            print(f'  PASS  {name}')
            passed += 1
        except AssertionError as exc:
            print(f'  FAIL  {name}')
            print(f'        {exc}')
            failed += 1
        except Exception as exc:
            print(f'  ERROR {name}')
            print(f'        {exc}')
            errors += 1

    total = len(tests)
    print(f'\n{"=" * 60}')
    print(f'  Results: {passed} passed, {failed} failed, {errors} errors  ({passed}/{total})')
    print(f'{"=" * 60}')

    return 1 if failed + errors > 0 else 0


if __name__ == '__main__':
    sys.exit(_run_tests())
