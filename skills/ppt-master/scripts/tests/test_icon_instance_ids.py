#!/usr/bin/env python3
"""Keep embedded icon definitions private to each SVG instance."""

import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from svg_finalize.embed_icons import process_svg_file  # noqa: E402


class IconInstanceIdsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.icons = self.project / 'icons'
        (self.icons / 'custom').mkdir(parents=True)
        (self.project / 'svg_output').mkdir()
        self.slide = self.project / 'svg_output' / '01.svg'
        for name, color in (('blue', '#0000FF'), ('red', '#FF0000')):
            (self.icons / 'custom' / f'{name}.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
                'data-icon-style="preserve-color"><defs><linearGradient id="paint">'
                f'<stop offset="0" stop-color="{color}"/>'
                f'<stop offset="1" stop-color="{color}"/>'
                '</linearGradient></defs><rect width="24" height="24" '
                'fill="url(#paint)"/></svg>', encoding='utf-8',
            )
        self.source = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
            '<g id="icon-instance-1-paint"/>'
            '<use id="blue-first" data-icon="custom/blue" x="80" y="80" '
            'width="240" height="240" data-pptx-role="decoration"/>'
            '<use id="red" data-icon="custom/red" x="400" y="80" width="240" height="240"/>'
            '<use id="blue-second" data-icon="custom/blue" x="720" y="80" '
            'width="240" height="240" opacity="0"/>'
            '</svg>'
        )
        self.slide.write_text(self.source, encoding='utf-8')

    def assert_instance_colors(self, root: ET.Element) -> None:
        ids = Counter(element.get('id') for element in root.iter() if element.get('id'))
        self.assertFalse({key: count for key, count in ids.items() if count > 1})
        by_id = {element.get('id'): element for element in root.iter() if element.get('id')}
        references = []
        for instance_id, color in (
            ('blue-first', '#0000FF'), ('red', '#FF0000'), ('blue-second', '#0000FF'),
        ):
            instance = by_id[instance_id]
            rect = next(element for element in instance.iter() if element.tag.endswith('rect'))
            reference = rect.get('fill')[5:-1]
            references.append(reference)
            gradient = next(element for element in instance.iter() if element.get('id') == reference)
            self.assertEqual([stop.get('stop-color') for stop in gradient], [color, color])
        self.assertEqual(len(set(references)), 3)
        self.assertEqual(by_id['blue-first'].get('data-pptx-role'), 'decoration')
        self.assertEqual(by_id['blue-second'].get('opacity'), '0')

    def test_finalize_cli_isolates_colliding_and_repeated_icons(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / 'finalize_svg.py'), str(self.project),
             '--only', 'embed-icons'], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_instance_colors(ET.parse(self.project / 'svg_final' / '01.svg').getroot())
        self.assertEqual(self.slide.read_text(encoding='utf-8'), self.source)

    def test_native_in_memory_expansion_isolates_instances(self) -> None:
        from svg_to_pptx.use_expander import expand_use_data_icons

        root = ET.fromstring(self.source)
        self.assertEqual(expand_use_data_icons(root, self.icons), 3)
        self.assert_instance_colors(root)

    def test_editor_preview_isolates_instances_without_changing_source(self) -> None:
        from svg_editor.server import create_app

        client = create_app(str(self.project), idle_timeout=0).test_client()
        response = client.get('/api/slide/01.svg')
        self.assertEqual(response.status_code, 200)
        self.assert_instance_colors(ET.fromstring(response.get_json()['content']))
        self.assertEqual(self.slide.read_text(encoding='utf-8'), self.source)

    def test_rewrites_local_urls_and_hrefs_without_changing_color_or_external_url(self) -> None:
        (self.icons / 'custom' / 'links.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 24 24" data-icon-style="preserve-color">'
            '<defs><linearGradient id="abc"><stop offset="0" stop-color="#abc"/></linearGradient>'
            '<linearGradient id="derived" href="#abc"/>'
            '<linearGradient id="legacy" xlink:href="#abc"/></defs>'
            '<rect id="shape" width="24" height="24" fill="url(#derived)" '
            'style="stroke: url( &apos;#legacy&apos; )"/>'
            '<image href="https://example.invalid/image.png#abc"/>'
            '</svg>', encoding='utf-8',
        )
        self.slide.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<use data-icon="custom/links"/><use data-icon="custom/links"/></svg>', encoding='utf-8',
        )
        process_svg_file(self.slide, self.icons)
        root = ET.parse(self.slide).getroot()
        all_ids = [element.get('id') for element in root.iter() if element.get('id')]
        self.assertEqual(len(all_ids), len(set(all_ids)))
        for group in root:
            local_ids = {element.get('id') for element in group.iter() if element.get('id')}
            for element in group.iter():
                for name, value in element.attrib.items():
                    if name.endswith('href') and value.startswith('#'):
                        self.assertIn(value[1:], local_ids)
                        self.assertNotEqual(value, '#abc')
                if element.tag.endswith('stop'):
                    self.assertEqual(element.get('stop-color'), '#abc')
                if element.tag.endswith('rect'):
                    self.assertNotEqual(element.get('fill'), 'url(#derived)')
                    self.assertNotIn("'#legacy'", element.get('style'))
                if element.tag.endswith('image'):
                    self.assertEqual(element.get('href'), 'https://example.invalid/image.png#abc')

    def test_namespace_is_deterministic_and_id_free_control_keeps_geometry(self) -> None:
        process_svg_file(self.slide, self.icons)
        first = self.slide.read_text(encoding='utf-8')
        self.slide.write_text(self.source, encoding='utf-8')
        process_svg_file(self.slide, self.icons)
        self.assertEqual(self.slide.read_text(encoding='utf-8'), first)
        (self.icons / 'custom' / 'plain.svg').write_text(
            '<svg viewBox="0 0 24 24" data-icon-style="preserve-color">'
            '<rect width="24" height="24" fill="#123456"/></svg>', encoding='utf-8',
        )
        self.slide.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<use id="plain" data-icon="custom/plain" x="10" y="20" width="48" height="48"/>'
            '</svg>', encoding='utf-8',
        )
        process_svg_file(self.slide, self.icons)
        group = ET.parse(self.slide).getroot()[0]
        self.assertEqual(group.get('id'), 'plain')
        self.assertEqual(group.get('transform'), 'translate(10, 20) scale(2)')
        self.assertEqual(group[0].attrib, {'width': '24', 'height': '24', 'fill': '#123456'})

    def test_namespacing_keeps_leading_xml_text_escaped(self) -> None:
        (self.icons / 'custom' / 'text.svg').write_text(
            '<svg viewBox="0 0 24 24" data-icon-style="preserve-color">'
            'A &amp; B &lt; C<rect id="box" width="24" height="24"/></svg>', encoding='utf-8',
        )
        self.slide.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><use data-icon="custom/text"/></svg>',
            encoding='utf-8',
        )
        process_svg_file(self.slide, self.icons)
        group = ET.parse(self.slide).getroot()[0]
        self.assertEqual(group.text.strip(), 'A & B < C')
