#!/usr/bin/env python3
"""Regressions for source/link protection and refreshing ordinary slices."""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import slice_images


class SliceOutputProtectionTests(unittest.TestCase):
    def _source(self, root: Path) -> Path:
        source = root / "sheet.png"
        with Image.new("RGBA", (80, 40), (230, 10, 20, 255)) as image:
            image.paste((20, 210, 30, 128), (40, 0, 80, 40))
            image.save(source)
        return source

    def _run(self, source: Path, *options: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = slice_images.main([str(source), "--grid", "1x2", *options])
        return code, stdout.getvalue(), stderr.getvalue()

    def _assert_rejected(self, result: tuple[int, str, str]) -> None:
        code, stdout, stderr = result
        self.assertEqual(code, 1, stderr)
        self.assertEqual(stdout, "")
        self.assertIn("choose unused --names", stderr)
        self.assertIn("no output files were written", stderr)

    def test_same_source_first_or_last_rejects_before_any_slice(self) -> None:
        for names in ("sheet.png,second.png", "first.png,sheet.png"):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = self._source(root)
                before = source.read_bytes()
                self._assert_rejected(self._run(source, "--names", names))
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(sorted(p.name for p in root.iterdir()), [source.name])

    def test_symlink_and_hardlink_to_source_are_preserved(self) -> None:
        for kind in ("symlink", "hardlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = self._source(root)
                before = source.read_bytes()
                alias = root / "first.png"
                if kind == "symlink":
                    alias.symlink_to(source)
                else:
                    os.link(source, alias)
                self._assert_rejected(self._run(source, "--names", "first,second"))
                self.assertEqual(source.read_bytes(), before)
                self.assertTrue(alias.samefile(source))
                self.assertEqual(alias.is_symlink(), kind == "symlink")
                self.assertFalse((root / "second.png").exists())

    def test_default_generated_name_cannot_overwrite_source_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            os.link(source, root / "sheet_01.png")
            self._assert_rejected(self._run(source))
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((root / "sheet_02.png").exists())

    def test_output_directory_alias_cannot_hide_source_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            alias = root / "alias"
            alias.symlink_to(root, target_is_directory=True)
            self._assert_rejected(self._run(
                source, "--names", "sheet,second", "--output", str(alias),
            ))
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((root / "second.png").exists())

    def test_existing_regular_target_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            existing = root / "second.png"
            existing.write_bytes(b"old derivative")
            result = self._run(source, "--names", "first,second")
            self.assertEqual(result[0], 0, result[2])
            with Image.open(existing) as image:
                self.assertEqual(image.getpixel((20, 20)), (20, 210, 30, 128))
            self.assertEqual(source.read_bytes(), before)
            self.assertTrue((root / "first.png").is_file())

    def test_casing_follows_filesystem_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            existing = root / "FIRST.PNG"
            existing.write_bytes(b"existing derivative must survive")
            aliases_existing = (root / "first.png").exists()
            result = self._run(source, "--names", "first,second")
            self.assertEqual(result[0], 0, result[2])
            self.assertTrue((root / "first.png").is_file())
            self.assertTrue((root / "second.png").is_file())
            if aliases_existing:
                with Image.open(existing) as image:
                    self.assertEqual(image.getpixel((20, 20)), (230, 10, 20, 255))
            else:
                self.assertEqual(existing.read_bytes(), b"existing derivative must survive")
            self.assertEqual(source.read_bytes(), before)

    def test_regenerated_sheet_refreshes_slices_with_the_same_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            first = self._run(source, "--names", "first,second")
            self.assertEqual(first[0], 0, first[2])
            old_outputs = [(root / name).read_bytes() for name in ('first.png', 'second.png')]
            with Image.new('RGBA', (80, 40), (0, 70, 240, 255)) as image:
                image.paste((240, 180, 0, 255), (40, 0, 80, 40))
                image.save(source)
            before = source.read_bytes()
            second = self._run(source, "--names", "first,second")
            self.assertEqual(second[0], 0, second[2])
            self.assertEqual(second[1], first[1])
            self.assertEqual(source.read_bytes(), before)
            for index, name in enumerate(('first.png', 'second.png')):
                self.assertNotEqual((root / name).read_bytes(), old_outputs[index])
                with Image.open(root / name) as image:
                    expected = (0, 70, 240, 255) if index == 0 else (240, 180, 0, 255)
                    self.assertEqual(image.getpixel((20, 20)), expected)

    def test_late_source_alias_cannot_refresh_an_earlier_slice(self) -> None:
        for kind in ('same', 'hardlink', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = self._source(root)
                before = source.read_bytes()
                first = root / 'first.png'
                first.write_bytes(b'keep until preflight passes')
                if kind == 'hardlink':
                    os.link(source, root / 'second.png')
                elif kind == 'symlink':
                    (root / 'second.png').symlink_to(source)
                names = 'first,sheet' if kind == 'same' else 'first,second'
                self._assert_rejected(self._run(source, '--names', names))
                self.assertEqual(first.read_bytes(), b'keep until preflight passes')
                self.assertEqual(source.read_bytes(), before)

    def test_symlink_to_an_unrelated_slice_is_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            other = root / 'other.png'
            other.write_bytes(b'linked file must survive')
            (root / 'second.png').symlink_to(other)
            self._assert_rejected(self._run(source, '--names', 'first,second'))
            self.assertEqual(other.read_bytes(), b'linked file must survive')
            self.assertTrue((root / 'second.png').is_symlink())
            self.assertFalse((root / 'first.png').exists())
            self.assertEqual(source.read_bytes(), before)

    def test_dangling_symlink_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            missing = root / "missing.png"
            alias = root / "second.png"
            alias.symlink_to(missing)
            self._assert_rejected(self._run(source, "--names", "first,second"))
            self.assertTrue(alias.is_symlink())
            self.assertFalse(missing.exists())
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((root / "first.png").exists())

    def test_new_outputs_preserve_source_and_crop_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root)
            before = source.read_bytes()
            output = root / "output"
            code, stdout, stderr = self._run(
                source, "--names", "first,second", "--output", str(output),
            )
            self.assertEqual(code, 0, stderr)
            self.assertEqual(stdout.splitlines(), [str(output / "first.png"), str(output / "second.png")])
            self.assertEqual(source.read_bytes(), before)
            for name, expected in (("first.png", (230, 10, 20, 255)), ("second.png", (20, 210, 30, 128))):
                with Image.open(output / name) as image:
                    self.assertEqual(image.size, (40, 40))
                    self.assertEqual(image.getpixel((20, 20)), expected)
