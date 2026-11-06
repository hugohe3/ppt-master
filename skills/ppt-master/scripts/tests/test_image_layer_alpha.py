#!/usr/bin/env python3
"""Regressions for sparse alpha in layer registration and base compositing."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageChops, ImageDraw

import image_layers
import image_ocr


class ImageLayerAlphaTests(unittest.TestCase):
    def _project(self, root: Path, *, strip: int, hidden: int = 255) -> None:
        root.mkdir(exist_ok=True)
        with Image.new("RGB", (640, 360), (80, 80, 80)) as page:
            ImageDraw.Draw(page).rectangle((120, 80, 220, 280), fill=(20, 160, 200))
            page.save(root / "page.png")
            with page.convert("RGBA") as layer:
                layer.paste((hidden, hidden, hidden, 0), (0, 0, strip, 360))
                layer.save(root / "layer.png")
        with Image.new("RGB", (640, 360), (200, 200, 200)) as image:
            image.save(root / "inpainted.png")
        ocr_dir = root / "analysis/ocr"
        ocr_dir.mkdir(parents=True)
        (ocr_dir / "page.json").write_text(json.dumps({
            "page_image": "page.png", "canvas": [640, 360],
            "blocks": [{"lines": [{"x": 0, "y": 10, "w": 6, "h": 6}]}],
        }), encoding="utf-8")

    def _check(self, root: Path) -> tuple[int, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = image_layers.main([
                "check", str(root), "--page-image", "page.png", "--layer", "layer.png",
            ])
        return code, stdout.getvalue() + stderr.getvalue()

    def _near_opaque_keyed_layer(self, root: Path) -> None:
        with Image.new("RGBA", (640, 360), (255, 0, 255, 250)) as layer:
            ImageDraw.Draw(layer).rectangle((120, 80, 220, 280), fill=(20, 160, 200, 250))
            layer.save(root / "layer.png")

    def test_near_opaque_magenta_layer_uses_key_for_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, strip=0)
            self._near_opaque_keyed_layer(root)
            before = (root / "layer.png").read_bytes()
            code, output = self._check(root)
            self.assertEqual(code, 0, output)
            self.assertIn("diff at origin 0.0", output)
            self.assertEqual((root / "layer.png").read_bytes(), before)

    def test_registered_sparse_layers_ignore_hidden_rgb(self) -> None:
        for width, hidden in ((25, 255), (25, 80), (100, 255)):
            with self.subTest(width=width, hidden=hidden), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._project(root, strip=width, hidden=hidden)
                before = (root / "layer.png").read_bytes()
                code, output = self._check(root)
                self.assertEqual(code, 0, output)
                self.assertIn("diff at origin 0.0", output)
                self.assertEqual((root / "layer.png").read_bytes(), before)

    def test_sparse_alpha_does_not_relax_shift_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, strip=25)
            with Image.open(root / "layer.png") as layer:
                shifted = ImageChops.offset(layer, 10, 0)
            shifted.save(root / "layer.png")
            code, output = self._check(root)
            self.assertEqual(code, 3, output)
            self.assertIn("NOT registered", output)

    def test_single_near_transparent_pixel_selects_alpha_without_coverage_floor(self) -> None:
        for value in (0, 19):
            with self.subTest(alpha=value), Image.new("RGBA", (100, 100), (255, 0, 255, 255)) as layer:
                layer.putpixel((50, 50), (80, 80, 80, value))
                layer.putpixel((50, 51), (80, 80, 80, 200))
                layer.putpixel((50, 52), (80, 80, 80, 201))
                mask = image_layers.layer_alpha(layer)
                self.assertTrue(mask[0, 0], "Near-transparent pixels select alpha before RGB key colors")
                self.assertFalse(mask[50, 50])
                self.assertFalse(mask[51, 50])
                self.assertTrue(mask[52, 50])

    def test_alpha_without_near_transparency_keeps_key_fallback(self) -> None:
        for value in (20, 128, 200, 201, 250, 254):
            with self.subTest(alpha=value), Image.new("RGBA", (100, 100), (255, 0, 255, value)) as layer:
                layer.putpixel((50, 50), (80, 80, 80, value))
                mask = image_layers.layer_alpha(layer)
                self.assertFalse(mask[0, 0])
                self.assertTrue(mask[50, 50])

    def test_palette_and_grayscale_sparse_transparency(self) -> None:
        with Image.new("LA", (100, 100), (80, 255)) as layer:
            layer.putpixel((50, 50), (255, 0))
            mask = image_layers.layer_alpha(layer)
            self.assertFalse(mask[50, 50])
            self.assertTrue(mask[0, 0])
        with Image.new("P", (100, 100), 0) as layer:
            layer.putpalette([80, 80, 80, 255, 255, 255] + [0] * 762)
            layer.info["transparency"] = 1
            layer.putpixel((50, 50), 1)
            mask = image_layers.layer_alpha(layer)
            self.assertFalse(mask[50, 50])
            self.assertTrue(mask[0, 0])

    def test_fully_opaque_inputs_keep_key_and_non_key_behavior(self) -> None:
        for mode in ("RGB", "RGBA"):
            with self.subTest(mode=mode), Image.new(mode, (100, 100), "magenta") as layer:
                layer.paste("blue", (10, 0, 100, 100))
                mask = image_layers.layer_alpha(layer)
                self.assertFalse(mask[50, 0])
                self.assertTrue(mask[50, 50])
            with self.subTest(mode=mode), Image.new(mode, (100, 100), "blue") as layer:
                self.assertTrue(image_layers.layer_alpha(layer).all())

    def test_fully_transparent_layer_still_rejects_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, strip=640)
            code, output = self._check(root)
            self.assertEqual(code, 1, output)
            self.assertIn("Layer has no opaque pixels", output)

    def test_merge_preserves_pixels_outside_layer_and_text_boxes(self) -> None:
        for width, hidden in ((25, 255), (25, 80), (100, 255), (0, 250)):
            with self.subTest(width=width, hidden=hidden), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._project(root, strip=width, hidden=hidden)
                if width == 0:
                    self._near_opaque_keyed_layer(root)
                names = ("page.png", "layer.png", "inpainted.png", "analysis/ocr/page.json")
                before = {name: (root / name).read_bytes() for name in names}
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    with mock.patch.object(image_ocr, "find_residue", return_value=None):
                        code = image_ocr.main([
                            "merge-base", str(root), "--page", "page", "--inpainted", "inpainted.png",
                            "--out", "merged.png", "--layer", "layer.png",
                        ])
                self.assertEqual(code, 0)
                with Image.open(root / "merged.png") as merged:
                    self.assertEqual(merged.getpixel((5, 180)), (80, 80, 80))
                    self.assertEqual(merged.getpixel((170, 180)), (200, 200, 200))
                    self.assertEqual(merged.getpixel((3, 13)), (200, 200, 200))
                for name in names:
                    self.assertEqual((root / name).read_bytes(), before[name])
