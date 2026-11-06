#!/usr/bin/env python3
"""Offline regressions for title allocation across unified web subprocesses."""

import base64
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import source_to_md
import web_to_md


class UnifiedWebBatchTests(unittest.TestCase):
    def run_conversion(self, arguments: list[str]) -> tuple[int, str]:
        def response(url):
            body = (f'<html><head><title>Report</title></head><body><article>'
                    f'<p>MARKER-{url[-1]} ' + 'Body text. ' * 40 +
                    '</p><img src="https://example.invalid/pixel.png"></article></body></html>')
            return SimpleNamespace(url=url, headers={'Content-Type': 'text/html; charset=utf-8'},
                                   content=body.encode('utf-8'))

        def run_backend(command, name):
            self.assertEqual(name, 'web_to_md.py')
            # Each production call starts a fresh interpreter.
            web_to_md._AUTO_NAMED_OUTPUTS.clear()
            with redirect_stdout(io.StringIO()):
                return web_to_md.main(command[2:])

        with patch.object(source_to_md, 'run_backend', side_effect=run_backend), \
                patch.object(web_to_md, 'fetch_response', side_effect=response), \
                redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()):
            code = source_to_md.main(arguments)
        return code, output.getvalue()

    def test_three_same_titles_keep_all_bodies_and_distinct_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, stdout = self.run_conversion([
                'https://example.invalid/A', 'https://example.invalid/B', 'https://example.invalid/C',
                '-o', tmp, '--no-images', '--json',
            ])
            self.assertEqual(code, 0)
            outputs = sorted(Path(tmp).glob('*.md'))
            self.assertEqual([p.name for p in outputs], ['Report.md', 'Report_2.md', 'Report_3.md'])
            for marker, output in zip('ABC', outputs):
                self.assertIn('MARKER-' + marker, output.read_text(encoding='utf-8'))
                self.assertTrue(output.with_suffix('.conversion_profile.json').is_file())
            results = [json.loads(line) for line in stdout.splitlines()]
            self.assertEqual(len(results), 3)
            self.assertEqual(len({result['markdown'] for result in results}), 3)

    def test_web_title_avoids_a_later_local_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'Report.txt'
            source.write_text('LOCAL-MARKER', encoding='utf-8')
            output = root / 'out'
            output.mkdir()
            code, _ = self.run_conversion([
                'https://example.invalid/A', str(source), '-o', str(output), '--no-images',
            ])
            self.assertEqual(code, 0)
            self.assertIn('LOCAL-MARKER', (output / 'Report.md').read_text())
            self.assertIn('MARKER-A', (output / 'Report_2.md').read_text())

    def test_implicit_web_directory_keeps_names_between_children(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(web_to_md.CONFIG, output_dir=tmp):
            code, _ = self.run_conversion([
                'https://example.invalid/A', 'https://example.invalid/B', '--no-images',
            ])
            self.assertEqual(code, 0)
            self.assertEqual(len(list(Path(tmp).glob('*.md'))), 2)

    def test_web_title_cannot_overwrite_another_input_through_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'local.txt'
            source.write_bytes(b'LOCAL-SOURCE')
            output = root / 'out'
            output.mkdir()
            os.link(source, output / 'Report.md')
            code, _ = self.run_conversion([
                'https://example.invalid/A', str(source), '-o', str(output), '--no-images',
            ])
            self.assertEqual(code, 1)
            self.assertEqual(source.read_bytes(), b'LOCAL-SOURCE')
            self.assertEqual((output / 'Report.md').read_bytes(), b'LOCAL-SOURCE')

    def test_separate_runs_keep_existing_overwrite_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for marker in 'AB':
                code, _ = self.run_conversion([
                    'https://example.invalid/' + marker, '-o', tmp, '--no-images',
                ])
                self.assertEqual(code, 0)
            self.assertEqual(len(list(Path(tmp).glob('*.md'))), 1)
            self.assertIn('MARKER-B', (Path(tmp) / 'Report.md').read_text())

    def test_companion_assets_follow_the_allocated_title(self) -> None:
        png = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=')
        image = SimpleNamespace(content=png, headers={'Content-Type': 'image/png'}, raise_for_status=lambda: None)
        with tempfile.TemporaryDirectory() as tmp, patch.object(web_to_md, '_http_get', return_value=image):
            code, _ = self.run_conversion([
                'https://example.invalid/A', 'https://example.invalid/B', '-o', tmp,
            ])
            self.assertEqual(code, 0)
            for stem in ('Report', 'Report_2'):
                self.assertIn(stem + '_files/pixel.png', (Path(tmp) / f'{stem}.md').read_text())
                self.assertEqual((Path(tmp) / f'{stem}_files/pixel.png').read_bytes(), png)
