#!/usr/bin/env python3
"""Focused tests for illustration-sheet alpha-key diagnostics."""

from __future__ import annotations

import base64
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

from slice_images import slice_sheet
from svg_finalize.crop_images import process_svg_images
from svg_finalize.embed_images import _optimize_image_bytes
from svg_finalize.fix_image_aspect import (
    get_image_dimensions_from_base64,
    get_image_dimensions_pil,
)
from pptx_to_svg.pic_to_svg import _apply_blip_image_effects, _image_size_at_96_dpi


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "slice_images.py"


class SliceImagesDiagnosticsTests(unittest.TestCase):
    def test_sheet_orientation_is_applied_before_slicing(self) -> None:
        for orientation, expected_size in ((6, (40, 80)), (None, (80, 40))):
            with self.subTest(orientation=orientation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "sheet.jpg"
                image = Image.new("RGB", (80, 40), "red")
                image.paste("blue", (40, 0, 80, 40))
                exif = image.getexif()
                if orientation is not None:
                    exif[274] = orientation
                image.save(source, exif=exif)

                paths = slice_sheet(source, 1, 1, root / "output")

                with Image.open(paths[0]) as result:
                    self.assertEqual(result.size, expected_size)
                    self.assertNotIn(274, result.getexif())
                    self.assertGreater(result.getpixel((10, 10))[0], 200)
                    blue_point = (10, 60) if orientation == 6 else (60, 10)
                    self.assertGreater(result.getpixel(blue_point)[2], 200)

    def test_grid_uses_oriented_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sheet.jpg"
            image = Image.new("RGB", (80, 40), "red")
            image.paste("blue", (40, 0, 80, 40))
            exif = image.getexif()
            exif[274] = 6
            image.save(source, exif=exif)

            paths = slice_sheet(source, 2, 1, root / "output")

            for path, channel in zip(paths, (0, 2)):
                with Image.open(path) as result:
                    self.assertEqual(result.size, (40, 40))
                    self.assertGreater(result.getpixel((20, 20))[channel], 200)

    def test_strict_alpha_reports_measured_sheet_border_and_exact_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            image = Image.new("RGB", (100, 80), (87, 178, 101))
            draw = ImageDraw.Draw(image)
            draw.rectangle((30, 22, 70, 58), fill=(170, 40, 55))
            draw.point((0, 0), fill=(84, 176, 100))
            draw.point((99, 79), fill=(88, 180, 102))
            image.save(sheet_path)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(sheet_path),
                    "--grid", "1x1",
                    "--names", "element",
                    "--trim",
                    "--alpha",
                    "--strict-alpha",
                    "--bg", "#00FF00",
                    "--tolerance", "12",
                    "--output", str(output_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("key background #00FF00", result.stderr)
            self.assertIn("dominant #57B265", result.stderr)
            self.assertIn("key spread 3", result.stderr)
            self.assertIn("--bg #57B265 --tolerance 12", result.stderr)
            self.assertFalse((output_dir / "element.png").exists())


class ImageOrientationProcessingTests(unittest.TestCase):
    def test_compression_applies_orientation_and_preserves_image_format(self) -> None:
        for fmt, mime in (("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")):
            for orientation in (None, 6):
                with self.subTest(format=fmt, orientation=orientation):
                    image = Image.new("RGB", (80, 40), "red")
                    image.paste("blue", (40, 0, 80, 40))
                    exif = image.getexif()
                    if orientation is not None:
                        exif[274] = orientation
                    source = io.BytesIO()
                    image.save(source, format=fmt, exif=exif)
                    result = _optimize_image_bytes(source.getvalue(), mime, compress=True, max_dimension=20)
                    self.assertLess(len(result), len(source.getvalue()))
                    with Image.open(io.BytesIO(result)) as optimized:
                        self.assertEqual(optimized.format, fmt)
                        self.assertEqual(optimized.size, (10, 20) if orientation == 6 else (20, 10))
                        self.assertNotIn(274, optimized.getexif())

    def test_animated_images_are_not_reencoded(self) -> None:
        source = io.BytesIO()
        Image.new("RGB", (80, 40), "red").save(
            source, format="GIF", save_all=True,
            append_images=[Image.new("RGB", (80, 40), "blue")],
        )
        original = source.getvalue()
        self.assertEqual(_optimize_image_bytes(original, "image/gif", compress=True), original)

    def test_svg_dimensions_and_crop_use_display_orientation_while_import_keeps_stored_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "photo.jpg"
            image = Image.new("RGB", (80, 40), "red")
            image.paste("blue", (40, 0, 80, 40))
            exif = image.getexif()
            exif[274] = 6
            image.save(source, exif=exif, dpi=(96, 96))
            data = source.read_bytes()
            uri = "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
            self.assertEqual(get_image_dimensions_pil(str(source)), (40, 80))
            self.assertEqual(get_image_dimensions_from_base64(uri), (40, 80))
            # PPTX import keeps the stored pixel orientation: PowerPoint renders
            # an embedded picture without applying its EXIF orientation tag.
            self.assertEqual(_image_size_at_96_dpi(data, ET.Element("blipFill")), (80, 40))

            svg = root / "slide.svg"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 80">'
                '<image href="photo.jpg" width="40" height="80" '
                'preserveAspectRatio="xMidYMid slice"/></svg>',
                encoding="utf-8",
            )
            self.assertEqual(process_svg_images(str(svg), root / "cropped", verbose=False), (1, 0))
            with Image.open(root / "cropped" / "photo.jpg") as cropped:
                self.assertEqual(cropped.size, (40, 80))
                self.assertGreater(cropped.getpixel((10, 60))[2], 200)

            blip = ET.fromstring(
                '<a:blip xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                '<a:lum bright="10000"/></a:blip>'
            )
            _, adjusted, diagnostics = _apply_blip_image_effects("photo.jpg", data, blip)
            self.assertEqual(diagnostics, ())
            with Image.open(io.BytesIO(adjusted)) as result:
                self.assertEqual(result.size, (80, 40))

    def test_watermark_processing_applies_orientation(self) -> None:
        from gemini_watermark_remover import process_image

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "image.jpg"
            image = Image.new("RGB", (256, 160), "red")
            exif = image.getexif()
            exif[274] = 6
            image.save(source, exif=exif)
            output = process_image(source, Path(tmp) / "processed.png", verbose=False)
            with Image.open(output) as result:
                self.assertEqual(result.size, (160, 256))


if __name__ == "__main__":
    unittest.main()
