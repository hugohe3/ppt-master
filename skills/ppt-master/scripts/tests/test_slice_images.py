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
    def test_pure_key_despill_keeps_opaque_key_hue_foreground_and_recovers_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            key = (0, 255, 0)
            malachite = (63, 143, 108)
            image = Image.new("RGB", (240, 100), key)
            draw = ImageDraw.Draw(image)
            draw.rectangle((20, 20, 100, 80), fill=malachite)
            # A black shadow composited over the key at 50% alpha.
            draw.rectangle((140, 20, 220, 80), fill=(0, 128, 0))
            image.save(sheet_path)

            written = slice_sheet(
                sheet_path, 1, 1, root / "out",
                names=["element"], alpha=True, bg=key, tolerance=18,
            )
            element = Image.open(written[0]).convert("RGBA")

            self.assertEqual(element.getpixel((60, 50)), malachite + (255,))
            shadow_r, shadow_g, shadow_b, shadow_a = element.getpixel((180, 50))
            self.assertLessEqual(max(shadow_r, shadow_g, shadow_b), 8)
            self.assertTrue(120 <= shadow_a <= 136, shadow_a)
            self.assertEqual(element.getpixel((120, 50))[3], 0)

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
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("key background #00FF00", result.stderr)
            self.assertIn("dominant #57B265", result.stderr)
            self.assertIn("key spread 3", result.stderr)
            self.assertIn("--bg #57B265 --tolerance 12", result.stderr)
            self.assertFalse((output_dir / "element.png").exists())

    def test_strict_alpha_retries_once_when_every_finding_is_key_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            # A slightly off, noisy key (as a JPEG round-trip leaves it) with
            # one element well clear of every cell edge.
            image = Image.new("RGB", (120, 120), (2, 253, 2))
            px = image.load()
            for y in range(120):
                for x in range(120):
                    if (x * 7 + y * 13) % 5 == 0:
                        px[x, y] = (6, 240, 8)
            draw = ImageDraw.Draw(image)
            draw.rectangle((40, 40, 80, 80), fill=(170, 40, 55))
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
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            # Every finding is measured key noise, so the tool retries once
            # with the tolerance it measured instead of asking for a rerun.
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("key noise", result.stderr)
            self.assertIn("auto-retrying once with --tolerance", result.stderr)
            self.assertNotIn("content reaches the", result.stderr)
            self.assertTrue((output_dir / "element.png").exists())

    def test_inset_accepts_horizontal_and_vertical_fractions(self) -> None:
        from slice_images import parse_inset

        self.assertEqual(parse_inset("0.03"), (0.03, 0.03))
        self.assertEqual(parse_inset("0.01,0.03"), (0.01, 0.03))
        with self.assertRaises(ValueError):
            parse_inset("0.5")
        with self.assertRaises(ValueError):
            parse_inset("0.1,0.2,0.3")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            # Two wide bands with a white grid line between them: an
            # isotropic inset wide enough for the line would cut the glyphs.
            image = Image.new("RGB", (400, 100), (0, 0, 255))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 48, 399, 51), fill=(255, 255, 255))
            draw.rectangle((10, 8, 390, 40), fill=(240, 240, 240))
            draw.rectangle((10, 58, 390, 92), fill=(240, 240, 240))
            image.save(sheet_path)

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), str(sheet_path),
                    "--grid", "2x1", "--names", "a,b",
                    "--trim", "--alpha", "--strict-alpha",
                    "--bg", "#0000FF", "--inset", "0,0.06",
                    "--output", str(output_dir),
                ],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Image.open(output_dir / "a.png").size, (381, 33))
            self.assertEqual(Image.open(output_dir / "b.png").size, (381, 35))

    def test_strict_alpha_rejects_a_sheet_whose_ground_recovers_as_haze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            # The real ground (#034AF4) sits farther from pure blue than the
            # tolerance, so soft-alpha recovery turns the whole field into a
            # faint half-foreground; the outer gutter alone does not catch it.
            image = Image.new("RGB", (160, 120), (3, 74, 244))
            draw = ImageDraw.Draw(image)
            draw.rectangle((60, 40, 100, 80), fill=(250, 250, 250))
            image.save(sheet_path)

            args = [
                sys.executable, str(SCRIPT), str(sheet_path),
                "--grid", "1x1", "--names", "mark",
                "--trim", "--alpha", "--strict-alpha",
                "--output", str(output_dir),
            ]
            result = subprocess.run(
                args + ["--bg", "#0000FF", "--tolerance", "62"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("semi-transparent", result.stderr)
            self.assertIn("measured ground colour", result.stderr)
            self.assertFalse((output_dir / "mark.png").exists())

            result = subprocess.run(
                args + ["--bg", "#034AF4", "--tolerance", "62"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Image.open(output_dir / "mark.png").size, (41, 41))

    def test_uneven_key_ground_is_keyed_by_dominance_without_eating_thin_strokes(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            size = 400
            rng = np.random.default_rng(7)
            yy, xx = np.mgrid[0:size, 0:size]
            t = (xx + yy) / (2 * size)
            # A generated key painted as a gradient with grain: #00FF00 -> #25D23A.
            ground = np.stack([37 * t, 255 - 45 * t, 58 * t], axis=2)
            ground += rng.normal(0, 3.0, ground.shape)
            scale = 4
            ink = Image.new("L", (size * scale, size * scale), 0)
            draw = ImageDraw.Draw(ink)
            for index in range(9):
                offset = (110 + index * 22) * scale
                draw.line([(100 * scale, offset), (300 * scale, offset)], fill=255, width=scale)
                draw.line([(offset, 100 * scale), (offset, 300 * scale)], fill=255, width=scale * 2)
            ink = ink.resize((size, size), Image.LANCZOS)
            coverage = np.asarray(ink, dtype=np.float32)[..., None] / 255
            sheet = ground * (1 - coverage) + np.array([18, 18, 18]) * coverage
            Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), "RGB").save(sheet_path)

            slice_sheet(
                sheet_path, 1, 1, output_dir, names=["lines"],
                alpha=True, strict_alpha=True, bg=(0, 255, 0),
            )

            cut = np.asarray(Image.open(output_dir / "lines.png").convert("RGBA"), dtype=np.float32)
            alpha = cut[..., 3] / 255
            reference = coverage[..., 0]
            self.assertGreater(alpha[reference > 0.9].mean(), 0.95)
            self.assertLess(alpha[reference < 0.02].mean(), 0.01)
            opaque = alpha > 0.8
            key_tinted = opaque & (cut[..., 1] > cut[..., 0] + 30) & (cut[..., 1] > cut[..., 2] + 30)
            self.assertEqual(int(key_tinted.sum()), 0)

    def test_pure_key_light_edge_and_warm_shadow_leave_no_green_or_magenta_fringe(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            image = Image.new("RGB", (200, 200), (0, 255, 0))
            draw = ImageDraw.Draw(image)
            # A warm shadow at 40% over the key, then a cream disc whose edge
            # rings with a light key-tinted line, as a compressed render leaves it.
            draw.ellipse((66, 66, 156, 156), fill=(16, 165, 12))
            draw.ellipse((49, 49, 151, 151), fill=(223, 255, 206))
            draw.ellipse((50, 50, 150, 150), fill=(245, 237, 218))
            image.save(sheet_path)

            slice_sheet(
                sheet_path, 1, 1, root / "out", names=["disc"],
                alpha=True, strict_alpha=True, bg=(0, 255, 0), tolerance=40,
            )

            cut = np.asarray(Image.open(root / "out" / "disc.png").convert("RGBA"), dtype=np.int16)
            red, green, blue, alpha = (cut[..., index] for index in range(4))
            key_tinted = (alpha >= 128) & (green > np.maximum(red, blue) + 30)
            magenta = (alpha >= 64) & (green + 30 < np.minimum(red, blue))
            self.assertEqual(int(key_tinted.sum()), 0)
            self.assertEqual(int(magenta.sum()), 0)
            self.assertEqual(tuple(cut[100, 100]), (245, 237, 218, 255))
            shadow = cut[140, 140]
            self.assertTrue(80 <= shadow[3] <= 110, shadow)
            self.assertLessEqual(int(shadow[:3].max() - shadow[:3].min()), 12)

    def test_off_key_flat_ground_with_cast_shadow_is_keyed_by_dominance(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            ground = (94, 222, 81)
            image = Image.new("RGB", (240, 240), ground)
            draw = ImageDraw.Draw(image)
            # A contact shadow cast on the painted ground: dark ground, not key.
            draw.rectangle((70, 70, 190, 190), fill=(47, 111, 40))
            draw.rectangle((60, 60, 170, 170), fill=(150, 90, 60))
            image.save(sheet_path)

            slice_sheet(
                sheet_path, 1, 1, root / "out", names=["block"],
                trim=True, alpha=True, strict_alpha=True,
            )

            cut = np.asarray(Image.open(root / "out" / "block.png").convert("RGBA"), dtype=np.int16)
            red, green, blue, alpha = (cut[..., index] for index in range(4))
            key_tinted = (alpha >= 128) & (green > np.maximum(red, blue) + 30)
            self.assertEqual(int(key_tinted.sum()), 0)
            self.assertEqual(tuple(cut[50, 50]), (150, 90, 60, 255))
            self.assertLess(int(alpha[-5:, -5:].max()), 200)

    def test_glow_tail_in_margin_over_on_key_ground_is_not_haze(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            size = 200
            yy, xx = np.mgrid[0:size, 0:size]
            radius = np.hypot(xx - 100, yy - 100)
            # A pale disc whose soft glow fades into the key-only margin.
            coverage = np.where(radius <= 40, 1.0, np.clip(1 - (radius - 40) / 70, 0, 1) * 0.35)
            ground = np.array([2.0, 8.0, 254.0])
            sheet = ground * (1 - coverage[..., None]) + np.array([235.0, 225.0, 200.0]) * coverage[..., None]
            Image.fromarray(sheet.astype(np.uint8), "RGB").save(sheet_path)

            for bg in ((0, 0, 255), (2, 8, 254)):
                with self.subTest(bg=bg):
                    out = root / f"out_{bg[0]}"
                    slice_sheet(
                        sheet_path, 1, 1, out, names=["moon"],
                        alpha=True, strict_alpha=True, bg=bg, tolerance=18,
                    )
                    cut = np.asarray(Image.open(out / "moon.png").convert("RGBA"), dtype=np.int16)
                    red, green, blue, alpha = (cut[..., index] for index in range(4))
                    # A measured near-key ground still despills: the glow is not blue.
                    bluish = (alpha >= 40) & (blue > np.maximum(red, green) + 30)
                    self.assertEqual(int(bluish.sum()), 0)

    def test_strict_alpha_names_painted_card_cells_instead_of_a_key_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sheet_path = root / "sheet.png"
            output_dir = root / "output"
            # The model painted each cell as a dark card and left the key only
            # as thin grid lines: after --inset the cells are all panel.
            image = Image.new("RGB", (200, 100), (0, 0, 255))
            draw = ImageDraw.Draw(image)
            draw.rectangle((3, 3, 96, 96), fill=(12, 14, 30))
            draw.rectangle((103, 3, 196, 96), fill=(12, 14, 30))
            draw.rectangle((30, 30, 60, 60), fill=(240, 200, 120))
            draw.rectangle((130, 30, 160, 60), fill=(240, 200, 120))
            image.save(sheet_path)

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), str(sheet_path),
                    "--grid", "1x2", "--names", "a,b",
                    "--trim", "--alpha", "--strict-alpha",
                    "--bg", "#0000FF", "--inset", "0.05",
                    "--output", str(output_dir),
                ],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("painted backing panel", result.stderr)
            self.assertIn("Cells painted as panels", result.stderr)
            self.assertNotIn("Suggested rerun:", result.stderr)


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
