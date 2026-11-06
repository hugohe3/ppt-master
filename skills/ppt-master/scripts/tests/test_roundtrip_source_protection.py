#!/usr/bin/env python3
"""PPT Master - Native Source Protection Regression Tests

Exercise source collisions and safe atomic alias replacement through export.

Usage:
    python3 -m unittest tests.test_roundtrip_source_protection

Examples:
    Run the module from the scripts directory.

Dependencies:
    python-pptx and the local PPTX import/export pipeline.
"""

from __future__ import annotations

import errno
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from pptx import Presentation
from pptx.util import Inches

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_to_pptx.pptx_package.cli import main as export_main


class RoundtripSourceProtectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'original.pptx'
        self.workspace = self.root / 'workspace'
        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = 'SOURCE'
        slide.notes_slide.notes_text_frame.text = 'Original notes'
        deck.save(self.source)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            convert_pptx_to_svg(
                self.source, self.workspace, ConvertOptions(inheritance_mode='both', roundtrip=True),
            )
        self.backing = self.workspace / 'sources/source.pptx'
        self.source_bytes = self.source.read_bytes()
        (self.workspace / 'notes/slide_01.md').write_text('Revised notes\n', encoding='utf-8')

    def _export(self, output: Path | None = None) -> tuple[int, str]:
        args = [str(self.workspace), '--roundtrip']
        if output is not None:
            args += ['-o', str(output)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = export_main(args)
        return result, stdout.getvalue() + stderr.getvalue()

    def _snapshot(self) -> dict:
        return {str(path): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.workspace.rglob('*') if path.is_file()}

    def _assert_sources_unchanged(self) -> None:
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        self.assertEqual(self.backing.read_bytes(), self.source_bytes)

    def test_direct_and_normalized_source_paths_fail_before_writes(self) -> None:
        parent_alias = self.root / 'sources-alias'
        parent_alias.symlink_to(self.backing.parent, target_is_directory=True)
        targets = [self.source, self.backing, parent_alias / self.backing.name,
                   self.workspace / 'sources/../sources/source.pptx',
                   Path(os.path.relpath(self.source))]
        for target in targets:
            with self.subTest(target=target):
                before = self._snapshot()
                code, output = self._export(target)
                self.assertNotEqual(code, 0, output)
                self.assertIn('Choose a different output path', output)
                self.assertEqual(before, self._snapshot())
                self._assert_sources_unchanged()
        code, output = self._export(self.root / 'after-rejection.pptx')
        self.assertEqual(code, 0, output)

    def test_leaf_symlinks_and_hardlinks_replace_only_the_alias(self) -> None:
        for source in (self.source, self.backing):
            for kind in ('symlink', 'hardlink'):
                with self.subTest(source=source, kind=kind):
                    target = self.root / f'{source.stem}-{kind}.pptx'
                    if kind == 'symlink':
                        target.symlink_to(source)
                    else:
                        os.link(source, target)
                    self.assertTrue(target.samefile(source))
                    code, output = self._export(target)
                    self.assertEqual(code, 0, output)
                    self.assertFalse(target.is_symlink())
                    self.assertFalse(target.samefile(source))
                    self.assertNotEqual(target.read_bytes(), self.source_bytes)
                    self._assert_sources_unchanged()

    def test_atomic_publish_failure_does_not_copy_through_alias(self) -> None:
        target = self.root / 'alias.pptx'
        target.symlink_to(self.source)
        replace = os.replace

        def fail_publish(source, destination):
            if Path(destination) == target:
                raise OSError(errno.EXDEV, 'Cross-device link')
            return replace(source, destination)

        with patch('svg_to_pptx.pptx_package.builder.os.replace',
                   side_effect=fail_publish):
            code, output = self._export(target)
        self.assertNotEqual(code, 0, output)
        self.assertIn('Choose a different output path', output)
        self.assertTrue(target.is_symlink())
        self._assert_sources_unchanged()

    def test_distinct_and_default_output_succeed(self) -> None:
        for target in (self.root / 'distinct.pptx', None):
            code, output = self._export(target)
            self.assertEqual(code, 0, output)
            self.assertIn('rebuilt=0', output)
            self._assert_sources_unchanged()

    def test_legacy_manifest_keeps_workspace_source_protection(self) -> None:
        manifest_path = self.workspace / 'analysis/roundtrip_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['source'].pop('originalPath', None)
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        code, output = self._export(self.backing)
        self.assertNotEqual(code, 0, output)
        self.assertIn('Choose a different output path', output)
        code, output = self._export(self.root / 'legacy-output.pptx')
        self.assertEqual(code, 0, output)

    def test_foreign_absolute_source_path_keeps_workspace_portable(self) -> None:
        manifest_path = self.workspace / 'analysis/roundtrip_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['source']['originalPath'] = (
            '/external/original.pptx' if os.name == 'nt' else 'C:\\external\\original.pptx'
        )
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        code, output = self._export(self.root / 'portable.pptx')
        self.assertEqual(code, 0, output)
        code, output = self._export(self.backing)
        self.assertNotEqual(code, 0, output)

    def test_samefile_alternate_spelling_is_rejected(self) -> None:
        target = self.source.with_name('ORIGINAL.PPTX')
        samefile = Path.samefile

        def case_insensitive_samefile(path, other):
            if path == target and Path(other) == self.source:
                return True
            return samefile(path, other)

        before = self._snapshot()
        with patch.object(Path, 'samefile', case_insensitive_samefile):
            code, output = self._export(target)
        self.assertNotEqual(code, 0, output)
        self.assertIn('Choose a different output path', output)
        self.assertEqual(before, self._snapshot())
        self._assert_sources_unchanged()

    def test_non_roundtrip_generate_is_unaffected(self) -> None:
        project = self.root / 'generate'
        svg_dir = project / 'svg_output'
        svg_dir.mkdir(parents=True)
        (svg_dir / 'slide_01.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 720">'
            '<rect width="960" height="720" fill="#ffffff"/></svg>', encoding='utf-8',
        )
        output = project / 'sources/source.pptx'
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = export_main([str(project), '-s', 'svg_output', '-o', str(output)])
        self.assertEqual(code, 0, stdout.getvalue() + stderr.getvalue())
        self.assertTrue(output.is_file())
