#!/usr/bin/env python3
"""Regressions for registration of completed, occluded layers."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

import image_layers


class ImageLayerRegistrationTests(unittest.TestCase):
    def _inputs(self, root: Path) -> None:
        page = Image.new("RGB", (640, 360), (80, 80, 80))
        layer = Image.new("RGBA", page.size)
        draw = ImageDraw.Draw(layer)
        draw.rectangle((80, 60, 479, 300), fill=(20, 160, 200, 255))
        draw.rectangle((100, 90, 125, 270), fill=(200, 90, 20, 255))
        page.paste(layer, mask=layer.getchannel("A"))
        page.save(root / "plain.png")
        ImageDraw.Draw(page).rectangle((280, 20, 550, 330), fill=(180, 180, 180))
        page.save(root / "page.png")
        layer.save(root / "layer.png")
        ImageChops.offset(layer, 10, 0).save(root / "shifted.png")
        mask = Image.new("L", page.size)
        ImageDraw.Draw(mask).rectangle((280, 20, 550, 330), fill=255)
        mask.save(root / "mask.png")

    def _check(self, root: Path, *, layer="layer.png", page="page.png", masked=True):
        args = ["check", str(root), "--page-image", page, "--layer", layer]
        if masked:
            args += ["--occlusion-mask", "mask.png"]
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = image_layers.main(args)
        return code, output.getvalue()

    def test_completed_layer_compares_only_visible_pixels_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            before = {path: path.read_bytes() for path in root.iterdir()}
            code, output = self._check(root)
            self.assertEqual(code, 0, output)
            self.assertIn("diff at origin 0.0", output)
            self.assertEqual({path: path.read_bytes() for path in root.iterdir()}, before)

    def test_shifted_completed_layer_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            code, output = self._check(root, layer="shifted.png")
            self.assertEqual(code, 3, output)
            self.assertIn("NOT registered", output)

    def test_unmasked_controls_and_occlusion_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            for page, layer, expected in (("plain.png", "layer.png", 0),
                                          ("plain.png", "shifted.png", 3),
                                          ("page.png", "layer.png", 3)):
                with self.subTest(page=page, layer=layer):
                    code, output = self._check(root, page=page, layer=layer, masked=False)
                    self.assertEqual(code, expected, output)
                    if expected:
                        self.assertIn("--occlusion-mask", output)

    def test_invalid_masks_fail_with_repair_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            for size, hint in (((320, 180), "canonical page canvas"),
                               ((640, 360), "mark only actual upper objects")):
                with self.subTest(size=size):
                    Image.new("L", size, 255).save(root / "mask.png")
                    code, output = self._check(root)
                    self.assertEqual(code, 1, output)
                    self.assertIn(hint, output)

    def test_empty_mask_matches_plain_registration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            Image.new("L", (640, 360)).save(root / "mask.png")
            self.assertEqual(self._check(root, page="plain.png"),
                             self._check(root, page="plain.png", masked=False))

    def test_visible_color_mismatch_is_not_hidden_by_mask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            with Image.open(root / "layer.png") as layer:
                changed = Image.new("RGBA", layer.size, (255, 255, 255, 255))
                changed.putalpha(layer.getchannel("A"))
                changed.save(root / "layer.png")
            code, output = self._check(root)
            self.assertEqual(code, 3, output)

    def test_mask_and_page_resize_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            for path in root.iterdir():
                with Image.open(path) as source:
                    resized = source.resize((1280, 720), Image.Resampling.NEAREST)
                resized.save(path)
            code, output = self._check(root)
            self.assertEqual(code, 0, output)
            code, output = self._check(root, layer="shifted.png")
            self.assertEqual(code, 3, output)

    def test_no_visible_shift_comparison_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._inputs(root)
            mask = Image.new("L", (640, 360), 255)
            mask.putpixel((200, 180), 0)
            mask.save(root / "mask.png")
            code, output = self._check(root)
            self.assertEqual(code, 1, output)
            self.assertIn("No visible pixels remain for shifted comparisons", output)

    def test_thin_occluders_survive_resampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            size = (1280, 720)
            page = Image.new("RGB", size, (80, 80, 80))
            # Keep RGB interpolation identical outside the occluders; sparse
            # transparent-edge interpolation is covered by the other fixtures.
            layer = Image.new("RGBA", size, (80, 80, 80, 255))
            draw = ImageDraw.Draw(layer)
            draw.rectangle((160, 120, 959, 600), fill=(20, 160, 200, 255))
            draw.rectangle((200, 180, 250, 540), fill=(200, 90, 20, 255))
            page.paste(layer, mask=layer.getchannel("A"))
            mask = Image.new("L", size)
            for x in range(560, 1097, 4):
                ImageDraw.Draw(page).line((x, 40, x, 660), fill=(180, 180, 180))
                ImageDraw.Draw(mask).line((x, 40, x, 660), fill=255)
            page.save(root / "page.png")
            layer.save(root / "layer.png")
            mask.save(root / "mask.png")
            ImageChops.offset(layer, 20, 0).save(root / "shifted.png")
            code, output = self._check(root)
            self.assertEqual(code, 0, output)
            self.assertIn("diff at origin 0.0", output)
            code, output = self._check(root, layer="shifted.png")
            self.assertEqual(code, 3, output)
