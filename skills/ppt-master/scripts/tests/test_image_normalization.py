#!/usr/bin/env python3
"""Regressions for full-range grayscale depth normalization in image CLIs."""

import contextlib
import io
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import image_normalization
import image_treat
import slice_images


class ImageNormalizationTests(unittest.TestCase):
    def _sources(self, root: Path, values: list[int], *, transparency=None) -> None:
        images = root / "images"
        images.mkdir()
        data = [value for _ in range(40) for value in values for _ in range(20)]
        size = (20 * len(values), 40)
        source = Image.frombytes("I;16", size, struct.pack(f"<{len(data)}H", *data))
        options = {} if transparency is None else {"transparency": transparency}
        source.save(images / "gray16.png", **options)
        control = Image.frombytes("L", size, bytes(value // 256 for value in data))
        if transparency is not None:
            control.putalpha(Image.frombytes("L", size, bytes(0 if v == transparency else 255 for v in data)))
        control.save(images / "gray8.png")

    def _cli(self, root: Path, tool: str, name: str) -> Image.Image:
        output = io.StringIO()
        if tool == "slice":
            result = root / f"sliced-{name}" / "page.png"
            args = [str(root / "images" / f"{name}.png"), "--grid", "1x1",
                    "--names", "page", "-o", str(result.parent)]
            main = slice_images.main
        else:
            result = root / "images" / f"fit-{name}.png"
            args = [str(root), f"{name}.png", "--output", result.name, "--fit", "50x20"]
            main = image_treat.main
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = main(args)
        self.assertEqual(code, 0, output.getvalue())
        with Image.open(result) as image:
            return image.convert("RGBA")

    def test_slice_and_fit_match_8bit_control_without_source_changes(self) -> None:
        for tool in ("slice", "treat"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._sources(root, [0, 16384, 32768, 49152, 65535])
                before = {p: p.read_bytes() for p in (root / "images").iterdir()}
                actual = self._cli(root, tool, "gray16")
                control = self._cli(root, tool, "gray8")
                self.assertEqual(actual.size, (100, 40) if tool == "slice" else (50, 20))
                self.assertEqual(actual.tobytes(), control.tobytes())
                self.assertEqual([actual.getpixel((round((i + 0.5) * actual.width / 5), actual.height // 2))[0]
                                  for i in range(5)], [0, 64, 128, 192, 255])
                for path, data in before.items():
                    self.assertEqual(path.read_bytes(), data)

    def test_low_range_is_not_auto_stretched(self) -> None:
        for tool in ("slice", "treat"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._sources(root, [0, 255, 256, 1024, 16384])
                actual = self._cli(root, tool, "gray16")
                control = self._cli(root, tool, "gray8")
                self.assertEqual(actual.tobytes(), control.tobytes())
                self.assertEqual(actual.getextrema()[0][1], control.getextrema()[0][1])

    def test_transparent_sample_is_matched_before_depth_reduction(self) -> None:
        for tool in ("slice", "treat"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._sources(root, [0, 32768, 32769, 49152, 65535], transparency=32768)
                actual = self._cli(root, tool, "gray16")
                control = self._cli(root, tool, "gray8")
                self.assertEqual(actual.tobytes(), control.tobytes())

    def test_endian_modes_use_the_same_encoded_range(self) -> None:
        values = [0, 255, 256, 16384, 32768, 49152, 65535]
        for mode, endian in (("I;16", "<"), ("I;16L", "<"), ("I;16B", ">")):
            with self.subTest(mode=mode):
                source = Image.frombytes(mode, (len(values), 1), struct.pack(f"{endian}{len(values)}H", *values))
                result = image_normalization.normalize_grayscale_depth(source)
                self.assertEqual(list(result.tobytes()), [0, 0, 1, 64, 128, 192, 255])

    def test_legacy_integer_png_retains_format_context_in_both_consumers(self) -> None:
        original_open = Image.open

        def legacy_open(path, *args, **kwargs):
            source = original_open(path, *args, **kwargs)
            if Path(path).name == "gray16.png":
                with source:
                    converted = source.convert("I")
                converted.format = "PNG"
                return converted
            return source

        for tool in ("slice", "treat"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._sources(root, [0, 16384, 32768, 49152, 65535])
                with mock.patch.object(Image, "open", side_effect=legacy_open):
                    actual = self._cli(root, tool, "gray16")
                control = self._cli(root, tool, "gray8")
                self.assertEqual(actual.tobytes(), control.tobytes())

    def test_other_integer_and_8bit_images_are_unchanged(self) -> None:
        for mode, file_format in (("I", "TIFF"), ("I", None), ("L", "PNG"), ("RGB", "PNG")):
            with self.subTest(mode=mode, file_format=file_format):
                source = Image.new(mode, (5, 1))
                self.assertIs(image_normalization.normalize_grayscale_depth(source, source_format=file_format), source)
