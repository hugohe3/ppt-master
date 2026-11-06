#!/usr/bin/env python3
"""Regressions for source aliases in unified and direct conversion batches."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import source_to_md
from _batch import run_path_batch


class SourceOutputProtectionTests(unittest.TestCase):
    def test_default_source_aliases_are_rejected_before_dispatch(self) -> None:
        for suffix in ('.docx', '.xlsx'):
            for kind in ('symlink', 'hardlink'):
                with self.subTest(suffix=suffix, kind=kind), tempfile.TemporaryDirectory() as tmp:
                    source = Path(tmp) / f'source{suffix}'
                    source.write_bytes(b'original')
                    output = source.with_suffix('.md')
                    if kind == 'symlink':
                        output.symlink_to(source)
                    else:
                        os.link(source, output)
                    with patch.object(source_to_md, 'dispatch_single') as convert, \
                            redirect_stderr(io.StringIO()) as err:
                        self.assertEqual(source_to_md.main([str(source)]), 1)
                    convert.assert_not_called()
                    self.assertIn('Choose a different -o path', err.getvalue())
                    self.assertEqual(source.read_bytes(), b'original')

    def test_directory_hardlink_to_another_input_rejects_whole_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / 'first.docx', root / 'second.xlsx'
            first.write_bytes(b'first')
            second.write_bytes(b'second')
            output = root / 'out'
            output.mkdir()
            os.link(second, output / 'first.md')
            with patch.object(source_to_md, 'dispatch_single') as convert, redirect_stderr(io.StringIO()):
                self.assertEqual(source_to_md.main([str(first), str(second), '-o', str(output)]), 1)
            convert.assert_not_called()
            self.assertEqual(second.read_bytes(), b'second')

    def test_directory_symlink_keeps_existing_rename_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.docx'
            source.write_bytes(b'original')
            source.with_suffix('.md').symlink_to(source)
            with patch.object(source_to_md, 'dispatch_single', return_value=0) as convert, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(source_to_md.main([str(source), '-o', tmp]), 0)
            self.assertEqual(convert.call_args.args[2], str(Path(tmp) / 'source_2.md'))
            self.assertEqual(source.read_bytes(), b'original')

    def test_explicit_aliases_remain_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.xlsx'
            source.write_bytes(b'original')
            output = Path(tmp) / 'alias.md'
            os.link(source, output)
            with patch.object(source_to_md, 'dispatch_single') as convert, redirect_stderr(io.StringIO()):
                self.assertEqual(source_to_md.main([str(source), '-o', str(output)]), 1)
            convert.assert_not_called()
            self.assertEqual(source.read_bytes(), b'original')

    def test_own_markdown_passthrough_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.md'
            source.write_text('# Original\n', encoding='utf-8')
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                self.assertEqual(source_to_md.main([str(source)]), 0)
            self.assertEqual(source.read_text(encoding='utf-8'), '# Original\n')

    def test_direct_batch_preflights_all_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'first.docx', Path(tmp) / 'second.docx'
            first.write_bytes(b'first')
            second.write_bytes(b'second')
            os.link(first, second.with_suffix('.md'))
            with patch('builtins.print'), patch.object(source_to_md, 'dispatch_single') as convert:
                self.assertEqual(run_path_batch([str(first), str(second)], {'.docx'}, None, convert), 1)
            convert.assert_not_called()
            self.assertFalse(first.with_suffix('.md').exists())
            self.assertEqual(first.read_bytes(), b'first')

    def test_unrelated_default_output_can_still_be_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.docx'
            source.write_bytes(b'original')
            source.with_suffix('.md').write_text('old', encoding='utf-8')
            def convert(input_path, output_path):
                output_path.write_text('converted', encoding='utf-8')
                return True
            self.assertEqual(run_path_batch([str(source)], {'.docx'}, None, convert), 0)
            self.assertEqual(source.with_suffix('.md').read_text(), 'converted')
            self.assertEqual(source.read_bytes(), b'original')
