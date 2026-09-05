#!/usr/bin/env python3
"""Regression tests for image rotation task outcomes and EXIF handling."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

from rotate_images import ImageRotator, main


class ImageRotationTests(unittest.TestCase):
    def test_fix_exit_status_tracks_failed_and_invalid_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "image.png"
            fixes = root / "fixes.json"
            cases = (
                ([{"path": str(root / "missing.png"), "rotation": 90}], 1),
                ([{"path": str(source), "rotation": "bad"}], 1),
                ([{"path": str(source)}], 1),
                ([{"rotation": 90}], 1),
                ([None, {"path": 42, "rotation": 90}], 1),
                ([{"path": str(source), "rotation": 90}], 0),
                ([{"path": str(source), "rotation": 0}], 0),
                ([], 0),
                ({"path": str(source), "rotation": 90}, 1),
            )
            for tasks, expected in cases:
                with self.subTest(tasks=tasks):
                    Image.new("RGB", (80, 40), "red").save(source)
                    fixes.write_text(json.dumps(tasks), encoding="utf-8")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["fix", str(fixes)]), expected)

    def test_fix_continues_after_failures_and_reports_success_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "image.png"
            Image.new("RGB", (80, 40), "red").save(source)
            tasks = [None, {}, {"path": str(source), "rotation": "bad"},
                     {"path": str(source), "rotation": 90}]
            with redirect_stdout(io.StringIO()):
                stats = ImageRotator().apply_fixes(tasks)
            self.assertEqual(stats, {"total": 4, "success": 1, "failed": 3})
            with Image.open(source) as result:
                self.assertEqual(result.size, (40, 80))

    def test_manual_rotation_follows_exif_display_orientation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "image.jpg"
            image = Image.new("RGB", (80, 40), "red")
            image.paste("blue", (40, 0, 80, 40))
            exif = image.getexif()
            exif[274] = 6
            image.save(source, exif=exif)
            with redirect_stdout(io.StringIO()):
                stats = ImageRotator().apply_fixes([{"path": str(source), "rotation": 90}])
            self.assertEqual(stats["success"], 1)
            with Image.open(source) as result:
                self.assertEqual(result.size, (80, 40))
                self.assertEqual(result.getexif().get(274, 1), 1)
                self.assertGreater(result.getpixel((10, 10))[2], 200)

    def test_auto_and_gen_fail_on_unreadable_images_and_missing_directories(self) -> None:
        for command in ("auto", "gen"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as tmp:
                images = Path(tmp) / "images"
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main([command, str(images)]), 1)
                images.mkdir()
                (images / "bad.jpg").write_bytes(b"not an image")
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main([command, str(images)]), 1)
                self.assertFalse((Path(tmp) / "image_orientation_tool.html").exists())

    def test_auto_and_gen_accept_valid_images(self) -> None:
        for command in ("auto", "gen"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as tmp:
                images = Path(tmp) / "images"
                images.mkdir()
                source = images / "image.jpg"
                image = Image.new("RGB", (80, 40), "red")
                exif = image.getexif()
                exif[274] = 6
                image.save(source, exif=exif)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main([command, str(images)]), 0)
                    self.assertEqual(main([command, str(images)]), 0)
                with Image.open(source) as result:
                    self.assertEqual(result.size, (40, 80))
                    self.assertEqual(result.getexif().get(274, 1), 1)

    def test_auto_continues_after_failed_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bad.jpg").write_bytes(b"not an image")
            image = Image.new("RGB", (80, 40), "red")
            exif = image.getexif()
            exif[274] = 6
            image.save(root / "good.jpg", exif=exif)
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(["auto", str(root)]), 1)
            self.assertIn("Auto-fixed EXIF orientation for 1 image(s)", stdout.getvalue())
            with Image.open(root / "good.jpg") as result:
                self.assertEqual(result.size, (40, 80))


if __name__ == "__main__":
    unittest.main()
