#!/usr/bin/env python3
"""Regression tests for icon attribute validation and SVG markup escaping."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_finalize.embed_icons import (  # noqa: E402
    generate_icon_group,
    parse_use_element,
    process_svg_file,
    resolve_icon_color,
)


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
