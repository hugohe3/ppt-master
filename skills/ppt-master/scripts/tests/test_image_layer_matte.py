#!/usr/bin/env python3
"""Regressions for flat-key monochrome alpha recovery."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

import image_layers


class ImageLayerMatteTests(unittest.TestCase):
    def _run(self, root: Path, key: str, fill: str = "#FFFFFF"):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = image_layers.main([
                "mono-matte", str(root), "--plate", "plate.png", "--key", key,
                "--box", "0", "0", "100", "100", "--canvas-width", "100",
                "--fill", fill, "--out", "result.png",
            ])
        return code, output.getvalue()

    def test_key_baselines_leave_background_and_holes_transparent(self) -> None:
        for key in ("#FF40FF", "#20FF20", "#20FF40", "#FF00FF", "#00FF00"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                color = tuple(int(key[i:i + 2], 16) for i in (1, 3, 5))
                plate = Image.new("RGB", (100, 100), color)
                draw = ImageDraw.Draw(plate)
                draw.rectangle((20, 20, 79, 79), fill="white")
                draw.rectangle((35, 35, 64, 64), fill=color)
                draw.rectangle((15, 20, 19, 79), fill=tuple(round((v + 255) / 2) for v in color))
                plate.save(root / "plate.png")
                before = (root / "plate.png").read_bytes()
                code, output = self._run(root, key, "#123456")
                self.assertEqual(code, 0, output)
                with Image.open(root / "result.png") as result:
                    self.assertEqual(result.getpixel((0, 0)), (18, 52, 86, 0))
                    self.assertEqual(result.getpixel((50, 50)), (18, 52, 86, 0))
                    self.assertEqual(result.getpixel((25, 25)), (18, 52, 86, 255))
                    self.assertAlmostEqual(result.getpixel((17, 25))[3], 128, delta=1)
                self.assertEqual((root / "plate.png").read_bytes(), before)

    def test_key_only_plate_is_fully_transparent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Image.new("RGB", (100, 100), (255, 64, 255)).save(root / "plate.png")
            code, output = self._run(root, "#FF40FF")
            self.assertEqual(code, 0, output)
            with Image.open(root / "result.png") as result:
                self.assertEqual(result.getextrema()[3], (0, 0))

    def test_key_without_low_channels_still_rejects_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Image.new("RGB", (100, 100), "white").save(root / "plate.png")
            code, output = self._run(root, "#FFFFFF")
            self.assertEqual(code, 1, output)
            self.assertIn("use a key with at least one channel below 128", output)
            self.assertFalse((root / "result.png").exists())
