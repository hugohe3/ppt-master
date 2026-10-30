import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from project_utils import validate_outline_hyperlinks


class OutlineHyperlinksTests(unittest.TestCase):
    def test_xml_attributes_are_decoded_exactly_once(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / 'svg_output').mkdir()
            (project / 'design_spec.md').write_text(
                '## IX. Content Outline\n### Slide 07\n'
                '- Hyperlinks: https://example.com/?a=1&b=2; '
                'https://example.com/?literal=&amp;value; #slide-2\n',
                encoding='utf-8',
            )
            (project / 'svg_output' / '07_links.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'xmlns:link="http://www.w3.org/1999/xlink">'
                '<a href="https://example.com/?a=1&amp;b=2"><text>One</text></a>'
                '<a link:href="https://example.com/?literal=&amp;amp;value"/>'
                '<a href="&#35;slide-2"/></svg>',
                encoding='utf-8',
            )
            self.assertEqual(validate_outline_hyperlinks(project), [])
