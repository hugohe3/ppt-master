#!/usr/bin/env python3
"""Keep one current provenance block when an installed workspace is reused.

Run with: python3 -m unittest tests.test_template_provenance
Dependencies: standard library and the installer.
"""

import tempfile
import unittest
from pathlib import Path

from apply_template import apply_templates


class TemplateProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        (self.source / 'templates').mkdir(parents=True)
        self.spec_name = 'design_spec.brand.sample.md'
        self.prefix = '---\nkind: brand\nbrand_id: sample\n---\n\n# Sample Brand\n'
        self.body = '\n## Identity\n\nPreserve the supplied colors.\n'
        (self.source / 'templates' / self.spec_name).write_text(
            self.prefix + self.body, encoding='utf-8',
        )

    def _install(self, source, name):
        project = self.root / name
        project.mkdir()
        apply_templates(project, [str(source)], validate=False)
        return project

    def _spec(self, project):
        return (project / 'templates' / self.spec_name).read_text(encoding='utf-8')

    def test_multiple_hops_replace_the_header_provenance(self) -> None:
        source = self.source
        for name in ('first', 'second', 'third'):
            project = self._install(source, name)
            text = self._spec(project)
            expected = f'> **Installed from**: `{source.resolve()}/` (explicit)'
            self.assertEqual(text.count('> **Installed from**:'), 1)
            self.assertEqual(text, self.prefix + '\n' + expected + '\n' + self.body)
            source = project

    def test_historical_duplicates_are_replaced_without_touching_body_examples(self) -> None:
        example = '\n```markdown\n> **Installed from**: `example/` (explicit)\n```\n'
        old = ('\n> **Installed from**: `old-a/` (explicit)\n'
               '\n> **Installed from**: `old-b/` (library)\n')
        path = self.source / 'templates' / self.spec_name
        path.write_text(self.prefix + old + self.body + example, encoding='utf-8')
        project = self._install(self.source, 'recovered')
        expected = f'> **Installed from**: `{self.source.resolve()}/` (explicit)'
        self.assertEqual(self._spec(project), self.prefix + '\n' + expected + '\n' + self.body + example)

    def test_rerun_from_an_installed_source_is_byte_identical(self) -> None:
        first = self._install(self.source, 'first')
        second = self._install(first, 'second')
        before = (second / 'templates' / self.spec_name).read_bytes()
        plan = apply_templates(second, [str(first)], validate=False)
        self.assertTrue(all(item.status == 'identical' for item in plan.mappings))
        self.assertEqual((second / 'templates' / self.spec_name).read_bytes(), before)

    def test_composite_root_keeps_one_line_for_each_spec(self) -> None:
        style_name = 'design_spec.style.sample.md'
        (self.source / 'templates' / style_name).write_text(
            '---\nkind: style\nstyle_id: sample\n---\n\n# Sample Style\n\nKeep text concise.\n',
            encoding='utf-8',
        )
        first = self._install(self.source, 'first')
        second = self._install(first, 'second')
        for name in (self.spec_name, style_name):
            text = (second / 'templates' / name).read_text(encoding='utf-8')
            self.assertEqual(text.count('> **Installed from**:'), 1)
            self.assertIn(f'`{first.resolve()}/` (explicit)', text)
