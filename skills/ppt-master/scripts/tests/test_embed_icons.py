#!/usr/bin/env python3
"""Regression tests for icon attribute validation and SVG markup escaping."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_finalize.embed_icons import (  # noqa: E402
    extract_paths_from_icon,
    generate_icon_group,
    parse_use_element,
    process_svg_file,
    resolve_icon_color,
)
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402


class IconAttributeSecurityTests(unittest.TestCase):
    def test_rejects_single_quoted_transform_injection_before_write(self) -> None:
        source = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<use data-icon="chunk-filled/rocket" '
            'transform=\'translate(10, 10)" ONMOUSEOVER="alert(1)\'/></svg>'
        )
        with self.assertRaisesRegex(ValueError, 'Invalid icon transform'):
            parse_use_element(source)
        with patch.object(Path, 'exists', return_value=True), \
                patch.object(Path, 'read_text', return_value=source), \
                patch.object(Path, 'write_text') as write:
            with self.assertRaisesRegex(ValueError, 'Invalid icon transform'):
                process_svg_file(Path('/unused/svg_output/01.svg'), Path('/unused/icons'))
            write.assert_not_called()

    def test_direct_generation_escapes_attribute_boundaries(self) -> None:
        payload = 'translate(10, 10)" ONMOUSEOVER="alert(1)'
        for style, attribute in (
            ('fill', 'transform'), ('stroke', 'transform'),
            ('preserve', 'transform'), ('stroke', 'stroke-width'),
        ):
            with self.subTest(style=style, attribute=attribute):
                attrs = {'icon': 'chunk-filled/rocket', 'fill': '#000000', attribute: payload}
                output = generate_icon_group(attrs, ['<path d="M0 0h1v1z"/>'], style, (1, 2, 16, 16))
                group = ET.fromstring(output)
                self.assertEqual(group.get(attribute), payload)
                self.assertNotIn('" ONMOUSEOVER=', output)
                self.assertFalse(any(
                    name.lower().startswith('on')
                    for element in group.iter() for name in element.attrib
                ))

    def test_legal_transforms_remain_authoritative(self) -> None:
        for transform in (
            'translate(10, 10)',
            'matrix(1 0 0 1 10 20)',
            'matrix(1, 0, 0, 1, -1e2, .5)',
            'translate(-10, +.5) scale(2) rotate(45, 10, 20) skewX(5) skewY(-5)',
        ):
            with self.subTest(transform=transform):
                attrs = parse_use_element(
                    '<use data-icon="chunk-filled/rocket" x="99" y="88" width="48" '
                    f"transform='{transform}'/>"
                )
                group = ET.fromstring(generate_icon_group(attrs, ['<path d="M0 0h1"/>'], 'fill', 16))
                self.assertEqual(attrs['transform'], transform)
                self.assertEqual(group.get('transform'), transform)

    def test_legal_colors(self) -> None:
        for color in (
            '#abc', '#abcd', '#123ABC', '#123ABC80', 'none', 'currentColor',
            'rebeccapurple', 'rgb(255, 0, 10)', 'rgba(100%, 0%, 20%, .5)',
            'hsl(120, 50%, 40%)', 'hsla(120, 50%, 40%, .5)',
        ):
            with self.subTest(color=color):
                attrs = parse_use_element(f'<use data-icon="chunk-filled/rocket" fill="{color}"/>')
                self.assertEqual(resolve_icon_color(attrs, 'fill'), color)
                group = ET.fromstring(generate_icon_group(attrs, ['<path d="M0 0h1"/>'], 'fill', 16))
                self.assertEqual(group.get('fill'), color)

    def test_outline_colors_and_stroke_width_units(self) -> None:
        for width in ('0', '2', '1.5', '.5px', '0.1em', '10%'):
            with self.subTest(width=width):
                attrs = parse_use_element(
                    '<use data-icon="tabler-outline/home" fill="none" '
                    f'stroke="currentColor" stroke-width="{width}"/>'
                )
                self.assertNotIn('width', attrs)
                group = ET.fromstring(generate_icon_group(attrs, ['<path d="M0 0h1"/>'], 'stroke', 24))
                self.assertEqual(group.get('fill'), 'none')
                self.assertEqual(group.get('stroke'), 'currentColor')
                self.assertEqual(group.get('stroke-width'), width)

    def test_rejects_unsafe_attribute_grammars(self) -> None:
        for attribute, value in (
            ('fill', '#12'), ('fill', '#12345'), ('fill', '#1234567'),
            ('fill', 'url(#gradient)'), ('stroke', 'url(https://example.invalid/x)'),
            ('fill', '#fff" ONMOUSEOVER="alert(1)'),
            ('stroke', '#fff" ONMOUSEOVER="alert(1)'),
            ('fill', 'rgb(1, 2, expression(alert(1)))'),
            ('transform', 'translate(10, 10);alert(1)'),
            ('transform', 'matrix(1 0 0 1 NaN 0)'), ('transform', 'rotate()'),
            ('transform', 'translate(1,,2)'), ('transform', 'translate(1.2.3)'),
            ('stroke-width', '2" ONMOUSEOVER="alert(1)'),
            ('stroke-width', 'calc(1px + 2px)'), ('stroke-width', '2pt'),
        ):
            with self.subTest(attribute=attribute, value=value):
                with self.assertRaisesRegex(ValueError, f'Invalid icon {attribute}'):
                    parse_use_element(f'<use data-icon="chunk-filled/rocket" {attribute}=\'{value}\'/>')

    def test_direct_color_resolution_rejects_unsafe_values(self) -> None:
        for style in ('fill', 'stroke'):
            for attribute in ('fill', 'stroke'):
                with self.subTest(style=style, attribute=attribute):
                    attrs = {attribute: '#fff" ONMOUSEOVER="alert(1)'}
                    with self.assertRaisesRegex(ValueError, f'Invalid icon {attribute}'):
                        resolve_icon_color(attrs, style)
                    with self.assertRaisesRegex(ValueError, f'Invalid icon {attribute}'):
                        generate_icon_group(attrs, ['<path d="M0 0h1"/>'], style, 16)


class PreserveColorMarkerTests(unittest.TestCase):
    def test_single_and_double_quoted_markers_both_preserve_the_asset(self) -> None:
        asset = (
            '<svg viewBox="0 0 48 24" data-icon-style={q}preserve-color{q}>'
            '<g transform="translate(8 0)"><rect width="20" height="20" fill="#ff0000"/>'
            '<text>A</text></g></svg>'
        )
        for quote in ("'", '"'):
            with self.subTest(quote=quote), \
                    patch.object(Path, "exists", return_value=True), \
                    patch.object(Path, "read_text", return_value=asset.format(q=quote)):
                parts, style, _ = extract_paths_from_icon(Path("logo.svg"))
            self.assertEqual(style, "preserve")
            self.assertIn("#ff0000", "".join(parts))
            self.assertIn("<text>", "".join(parts))

    def test_single_quoted_stroke_icon_is_detected_as_stroke(self) -> None:
        icon = "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor'><path d='M4 12h16'/></svg>"
        with patch.object(Path, "exists", return_value=True), \
                patch.object(Path, "read_text", return_value=icon):
            _, style, _ = extract_paths_from_icon(Path("arrow.svg"))
        self.assertEqual(style, "stroke")


class OutlineIconFilledDetailTests(unittest.TestCase):
    ICONS_DIR = SCRIPTS_DIR.parent / 'templates' / 'icons'

    def _group(self, name: str) -> ET.Element:
        elements, style, base_size = extract_paths_from_icon(self.ICONS_DIR / f'{name}.svg')
        self.assertEqual(style, 'stroke')
        return ET.fromstring(generate_icon_group(
            {'x': 0, 'y': 0, 'width': 48, 'height': 48, 'fill': '#1A73E8', 'icon': name},
            elements, style, base_size,
        ))

    def test_filled_half_disc_stays_filled_without_a_line(self) -> None:
        half_disc, ring = self._group('tabler-outline/percentage-50')
        self.assertEqual((half_disc.get('fill'), half_disc.get('stroke')), ('#1A73E8', 'none'))
        self.assertEqual((ring.get('fill'), ring.get('stroke')), (None, None))

    def test_detail_and_outline_share_the_effective_color_in_drawingml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            icon_dir = project / 'icons' / 'tabler-outline'
            icon_dir.mkdir(parents=True)
            icon = (self.ICONS_DIR / 'tabler-outline' / 'percentage-50.svg').read_text(encoding='utf-8')
            (icon_dir / 'percentage-50.svg').write_text(
                icon.replace('fill="currentColor"', "fill = 'CurRentColor'")
                .replace('stroke="none"', "stroke = 'none'")
                .replace('stroke="currentColor"', 'stroke = "CURRENTcolor"'),
                encoding='utf-8',
            )
            slide = project / 'svg_output' / '01.svg'
            slide.parent.mkdir()
            for paint in (
                'fill="#1A73E8"',
                'fill="none" style="stroke:#1A73E8"',
                'fill="none" stroke="#FF0000" style="stroke:#1A73E8"',
                'fill="#FF0000" style="stroke:#1A73E8"',
                'fill="#FF0000" style="fill:#1A73E8"',
            ):
                with self.subTest(paint=paint):
                    slide.write_text(
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                        f'<use data-icon="tabler-outline/percentage-50" {paint}/></svg>',
                        encoding='utf-8',
                    )
                    xml, *_ = convert_svg_to_slide_shapes(slide, resource_root=project)
                    detail, ring = ET.fromstring(xml).findall('.//{*}sp/{*}spPr')
                    self.assertEqual(detail.find('{*}solidFill/{*}srgbClr').get('val'), '1A73E8')
                    self.assertIsNotNone(detail.find('{*}ln/{*}noFill'))
                    self.assertIsNotNone(ring.find('{*}noFill'))
                    self.assertEqual(ring.find('{*}ln/{*}solidFill/{*}srgbClr').get('val'), '1A73E8')

    def test_inline_none_suppresses_the_outline_stroke(self) -> None:
        elements, style, base_size = extract_paths_from_icon(self.ICONS_DIR / 'tabler-outline/percentage-50.svg')
        attrs = parse_use_element(
            '<use data-icon="tabler-outline/percentage-50" fill="none" stroke="#FF0000" style="stroke:none"/>'
        )
        group = ET.fromstring(generate_icon_group(attrs, elements, style, base_size))
        self.assertEqual(group.get('stroke'), 'none')
        self.assertEqual(group[0].get('fill'), 'none')
        self.assertIsNone(group[1].get('stroke'))

    def test_filled_dot_keeps_the_inherited_line(self) -> None:
        dot = self._group('tabler-outline/accessible')[-1]
        self.assertEqual((dot.get('fill'), dot.get('stroke')), ('#1A73E8', None))

    def test_plain_outline_icon_is_unchanged(self) -> None:
        group = self._group('tabler-outline/home')
        self.assertEqual((group.get('fill'), group.get('stroke')), ('none', '#1A73E8'))
        for path in group:
            self.assertEqual((path.get('fill'), path.get('stroke')), (None, None))
