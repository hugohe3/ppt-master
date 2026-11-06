#!/usr/bin/env python3
"""PPT Master - Companion Markdown Link Regression Tests

Exercise the project importer's companion-directory rewrite on synthetic Markdown.

Usage:
    python3 -m unittest tests.test_markdown_asset_refs

Examples:
    python3 -m unittest tests.test_markdown_asset_refs

Dependencies:
    Standard library, local PPT Master modules, and Pandoc for the CommonMark oracle.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from urllib.parse import quote


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_management.cli import ProjectManager  # noqa: E402


def _commonmark_targets(markdown):
    result = subprocess.run(
        ["pandoc", "--from=commonmark", "--to=json"],
        input=markdown, text=True, capture_output=True, check=True,
    )

    def collect(node):
        if isinstance(node, dict):
            if node.get("t") in {"Link", "Image"}:
                yield node["c"][-1][0]
            for value in node.values():
                yield from collect(value)
        elif isinstance(node, list):
            for item in node:
                yield from collect(item)

    return list(collect(json.loads(result.stdout)))


class MarkdownAssetReferenceTests(unittest.TestCase):
    def _rewrite(self, content, original="report_files", imported="report_files_2"):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "report.md"
            source.write_text(content, encoding="utf-8")
            ProjectManager(base_dir=Path(tmp))._rewrite_markdown_asset_refs(source, original, imported)
            return source.read_text(encoding="utf-8")

    def test_inline_images_and_links_keep_titles_and_surrounding_text(self):
        source = (
            'report_files/x.png\n\n'
            '![report_files/x.png](report_files/x.png "report_files/title")\n'
            '[download](./report_files/a\\(b\\).pdf?size=2#page "title")\n'
            '[![thumb](report_files/thumb.png)](<report_files/a(b.pdf>)\n'
        )
        expected = (
            'report_files/x.png\n\n'
            '![report_files/x.png](report_files_2/x.png "report_files/title")\n'
            '[download](./report_files_2/a\\(b\\).pdf?size=2#page "title")\n'
            '[![thumb](report_files_2/thumb.png)](<report_files_2/a(b.pdf>)\n'
        )
        self.assertEqual(self._rewrite(source), expected)

    def test_encoded_directory_keeps_encoded_filename_query_and_fragment(self):
        original = "带 空格_files"
        imported = "带 空格_2_files"
        encoded = quote(original)
        destination = quote(imported)
        source = (
            f'![image]({encoded}/a%20b.png?x=%2F#part)\n'
            f'[image](./{encoded}/a%28b.png)\n'
            f'[raw](<{original}/raw image.png>)\n'
        )
        expected = (
            f'![image]({destination}/a%20b.png?x=%2F#part)\n'
            f'[image](./{destination}/a%28b.png)\n'
            f'[raw](<{destination}/raw image.png>)\n'
        )
        self.assertEqual(self._rewrite(source, original, imported), expected)

    def test_markdown_escaped_directory_is_compared_after_unescaping(self):
        source = '![x](report\\_files/a.png)\n![x](report&#95;files/b.png)\n![x](report_files\\/c.png)\n'
        self.assertEqual(self._rewrite(source),
                         '![x](report_files_2/a.png)\n![x](report_files_2/b.png)\n'
                         '![x](report_files_2\\/c.png)\n')

    def test_reference_definitions_keep_labels_titles_and_usage(self):
        source = (
            '![picture][photo]\n[manual][]\n\n'
            '[photo]: <report_files/a(b.png> "report_files/title"\n'
            '[manual]:\n  ./report_files/manual.pdf\n'
        )
        expected = (
            '![picture][photo]\n[manual][]\n\n'
            '[photo]: <report_files_2/a(b.png> "report_files/title"\n'
            '[manual]:\n  ./report_files_2/manual.pdf\n'
        )
        self.assertEqual(self._rewrite(source), expected)

    def test_inline_fenced_and_indented_code_are_unchanged(self):
        source = (
            '`![x](report_files/a.png)` and ``[x](report_files/a`b.png)``\n\n'
            '```markdown\n![x](report_files/a.png)\n```\n\n'
            '~~~\n[x]: report_files/a.png\n~~~\n\n'
            '    ![x](report_files/a.png)\n\n'
            '\t[x](report_files/a.png)\n\n'
            '![real](report_files/real.png)\n'
        )
        self.assertEqual(self._rewrite(source), source.replace('(report_files/real.png)',
                                                               '(report_files_2/real.png)'))

    def test_html_blocks_comments_and_attributes_are_unchanged(self):
        source = (
            '<div>\n![x](report_files/a.png)\n</div>\n\n'
            '<script>\n[x](report_files/a.png)\n</script>\n\n'
            '<!--\n[x]: report_files/a.png\n-->\n\n'
            '<custom>\n[x](report_files/a.png)\n</custom>\n\n'
            '<span title="[x](report_files/a.png)">text</span>\n\n'
            'text <!-- [x](report_files/a.png) --> ![real](report_files/real.png)\n'
        )
        self.assertEqual(self._rewrite(source), source.replace('(report_files/real.png)',
                                                               '(report_files_2/real.png)'))

    def test_external_absolute_and_other_directory_targets_are_unchanged(self):
        targets = (
            'https://example.invalid/report_files/a.png', '//example.invalid/report_files/a.png',
            'file:///report_files/a.png', 'mailto:report_files/user', '/report_files/a.png',
            '../report_files/a.png', 'other/report_files/a.png', 'report_files_old/a.png',
            'report_files.png', '#report_files/a.png', '?q=report_files/a.png',
            'https://[invalid/report_files/a.png',
        )
        source = '\n'.join(f'[x]({target})' for target in targets)
        self.assertEqual(self._rewrite(source), source)
        source = '<https://example.invalid/[x](report_files/a.png)>\n'
        self.assertEqual(self._rewrite(source), source)

    def test_malformed_links_and_escaped_brackets_are_unchanged(self):
        source = (
            r'\[literal](report_files/a.png)' '\n'
            '[missing close](report_files/a.png\n'
            '[bad title](report_files/a.png junk)\n'
            '[unbalanced](report_files/a(b.png)\n'
            '[blank](\n\nreport_files/a.png)\n'
        )
        self.assertEqual(self._rewrite(source), source)

    def test_invalid_reference_definitions_and_code_definitions_are_unchanged(self):
        source = (
            '[bad]: report_files/a.png trailing garbage\n\n'
            '`code\n[ref]: report_files/a.png\nend`\n\n'
            '[real]: report_files/real.png "[x](report_files/title.png)"\n'
        )
        self.assertEqual(self._rewrite(source), source.replace('report_files/real.png',
                                                               'report_files_2/real.png'))
        source = 'paragraph\n[ref]: report_files/a.png\n'
        self.assertEqual(self._rewrite(source), source)
        source = '[ref]: report_files/a.png\n"title" trailing garbage\n'
        self.assertEqual(self._rewrite(source), source.replace('report_files/a.png', 'report_files_2/a.png'))

    def test_container_code_fences_are_unchanged(self):
        for opening, body, closing in (
            ('> ```', '> [x](report_files/a.png)', '> ```'),
            ('- ```', '  [x](report_files/a.png)', '  ```'),
            ('> - ~~~', '>   [x](report_files/a.png)', '>   ~~~'),
        ):
            with self.subTest(opening=opening):
                source = f'{opening}\n{body}\n{closing}\n\n[x](report_files/real.png)\n'
                self.assertEqual(self._rewrite(source), source.replace('(report_files/real.png)',
                                                                       '(report_files_2/real.png)'))

    def test_container_reference_definitions_keep_source_layout(self):
        cases = (
            '> ![i][x]\n>\n> [x]: report_files/a.png "title"\n',
            '> > ![i][x]\n> >\n> > [x]: <report_files/a.png>\n',
            '1. item\n\n   [x]: report_files/a.png\n\n   ![i][x]\n',
            '10. item\n\n    [x]: report_files/a.png\n\n    ![i][x]\n',
            '- [x]: report_files/a.png\n\n  ![i][x]\n',
            '> 1. item\n>\n>    [x]: report_files/a.png\n>\n>    ![i][x]\n',
        )
        for source in cases:
            with self.subTest(source=source):
                output = self._rewrite(source)
                self.assertEqual(output, source.replace('report_files/a.png', 'report_files_2/a.png'))
                self.assertEqual(_commonmark_targets(source), ['report_files/a.png'])
                self.assertEqual(_commonmark_targets(output), ['report_files_2/a.png'])

    def test_container_definitions_inside_code_or_paragraphs_are_unchanged(self):
        cases = (
            '> paragraph\n> [x]: report_files/a.png\n',
            '1. paragraph\n   [x]: report_files/a.png\n',
            '>     [x]: report_files/a.png\n',
            '1. item\n\n       [x]: report_files/a.png\n',
            '10. item\n\n        [x]: report_files/a.png\n',
            '> ```\n> [x]: report_files/a.png\n> ```\n',
            '- ```\n  [x]: report_files/a.png\n  ```\n',
            '- > ```\n  > [x]: report_files/a.png\n  > ```\n',
            '-     [x]: report_files/a.png\n',
            '1.     [x]: report_files/a.png\n',
        )
        for source in cases:
            with self.subTest(source=source):
                source += '\n\n![i][x]\n'
                self.assertEqual(self._rewrite(source), source)
                self.assertEqual(_commonmark_targets(source), [])

    def test_brackets_do_not_span_blank_paragraphs_or_form_nested_links(self):
        source = '[broken\n\ntext](report_files/a.png)\n'
        self.assertEqual(self._rewrite(source), source)
        source = '[outer [inner](report_files/inner.png)](report_files/outer.png)\n'
        self.assertEqual(self._rewrite(source), source.replace('(report_files/inner.png)',
                                                               '(report_files_2/inner.png)'))
        source = r'\![outer [inner](report_files/inner.png)](report_files/outer.png)' '\n'
        self.assertEqual(self._rewrite(source), source.replace('(report_files/inner.png)',
                                                               '(report_files_2/inner.png)'))
        source = '[a\n# heading\n](report_files/a.png)\n'
        self.assertEqual(self._rewrite(source), source)

    def test_query_and_fragment_are_not_part_of_the_directory(self):
        for suffix in ('?x=', '#x='):
            with self.subTest(suffix=suffix):
                source = f'[x](report_files{suffix}/file.png)\n'
                self.assertEqual(self._rewrite(source, 'report_files' + suffix, 'renamed'), source)

    def test_import_sources_moves_encoded_references_to_the_allocated_companion(self):
        for stem in ('report', '带 空格'):
            with self.subTest(stem=stem), tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
                root = Path(tmp)
                manager = ProjectManager(base_dir=root / 'projects')
                project = Path(manager.init_project('import-links', quick_generate=True))
                existing = project / 'sources' / f'{stem}.md'
                existing.parent.mkdir(parents=True, exist_ok=True)
                existing.write_text('Existing content\n', encoding='utf-8')
                incoming = root / 'incoming'
                incoming.mkdir()
                companion = incoming / f'{stem}_files'
                companion.mkdir()
                (companion / 'manual.txt').write_text('Asset bytes\n', encoding='utf-8')
                source = incoming / f'{stem}.md'
                content = f'[manual]({quote(companion.name)}/manual.txt?download#page)\n'
                source.write_text(content, encoding='utf-8')
                result = manager.import_sources(str(project), [str(source)], copy=True)
                imported = Path(result['markdown'][0])
                self.assertEqual(imported.name, f'{stem}_2.md')
                self.assertEqual(imported.read_text(encoding='utf-8'),
                                 f'[manual]({quote(stem + "_2_files")}/manual.txt?download#page)\n')
                self.assertEqual((imported.parent / f'{stem}_2_files' / 'manual.txt').read_text(),
                                 'Asset bytes\n')
                self.assertEqual(source.read_text(encoding='utf-8'), content)
                self.assertEqual(existing.read_text(encoding='utf-8'), 'Existing content\n')

    def test_unchanged_directory_is_a_no_op(self):
        source = '[x](report_files/a.png)\n'
        self.assertEqual(self._rewrite(source, imported="report_files"), source)
