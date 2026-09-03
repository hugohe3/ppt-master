#!/usr/bin/env python3
"""Regression tests for image-search candidate promotion."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import image_search  # noqa: E402


class ImageSearchPromotionTests(unittest.TestCase):
    def test_quality_failure_reports_actual_required_and_metadata_dimensions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "images"
            candidate_dir = output_dir / "candidates" / "hero"
            candidate_dir.mkdir(parents=True)
            candidates_path = candidate_dir / "candidates.json"
            candidates_path.write_text(
                json.dumps({
                    "candidate_storage": "thumbnail-only",
                    "target_filename": "hero.jpg",
                    "request": {
                        "min_width": 1200,
                        "min_height": 800,
                    },
                    "candidates": [{
                        "filename": "candidate_01.jpg",
                        "provider": "pixabay",
                        "width": 4836,
                        "height": 2915,
                        "download_url": "https://example.invalid/original.jpg",
                    }],
                }),
                encoding="utf-8",
            )

            def fake_download(_url: str, destination: str, **_kwargs) -> None:
                Path(destination).write_bytes(b"fake downloaded image")

            stderr = io.StringIO()
            with (
                patch.object(
                    image_search,
                    "download_image",
                    side_effect=fake_download,
                ),
                patch.object(
                    image_search,
                    "_validate_downloaded_quality",
                    return_value=False,
                ),
                patch.object(
                    image_search,
                    "_measure_actual_image",
                    return_value=(1280, 772),
                ),
                redirect_stderr(stderr),
            ):
                result = image_search.promote_candidate(
                    output_dir,
                    "hero.jpg",
                    "candidate_01.jpg",
                )

            self.assertEqual(result, 1)
            message = stderr.getvalue()
            self.assertIn("candidate promotion failed", message)
            self.assertIn("measured 1280x772", message)
            self.assertIn("required minimum 1200x800", message)
            self.assertIn("metadata claimed 4836x2915", message)
            self.assertFalse((output_dir / "hero.jpg").exists())
            self.assertNotIn(
                "selected",
                json.loads(candidates_path.read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()


class CandidatePoolContinuationTests(unittest.TestCase):
    def test_later_pages_keep_earlier_saved_thumbnails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cand_dir = Path(temp_dir) / "candidates" / "hero"
            review_dir = cand_dir / "review"
            review_dir.mkdir(parents=True)
            (review_dir / "candidate_02.jpg").write_bytes(b"x")
            meta_path = cand_dir / "candidates.json"
            meta_path.write_text(json.dumps({
                "target_filename": "hero.jpg",
                "candidate_page": 1,
                "request": {"query": "bronze mask"},
                "candidates": [
                    {"rank": 1, "filename": "candidate_01.jpg", "review": "review/candidate_01.jpg"},
                    {"rank": 2, "filename": "candidate_02.jpg", "review": "review/candidate_02.jpg"},
                ],
            }), encoding="utf-8")
            request = image_search.ImageSearchRequest(
                query="bronze mask",
                purpose="",
                orientation="",
                filename="hero.jpg",
                slide="",
                min_width=1,
                min_height=1,
            )
            retained, pages = image_search._retained_pool_candidates(
                meta_path,
                review_dir,
                request,
                current_ranks={9, 10},
            )
            self.assertEqual([entry["rank"] for entry in retained], [2])
            self.assertEqual(pages, [1])

            changed = image_search.ImageSearchRequest(
                query="jade cong",
                purpose="",
                orientation="",
                filename="hero.jpg",
                slide="",
                min_width=1,
                min_height=1,
            )
            self.assertEqual(
                image_search._retained_pool_candidates(
                    meta_path, review_dir, changed, current_ranks=set()
                ),
                ([], []),
            )

    def test_batch_mode_rejects_a_positional_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "image_queries.json"
            manifest.write_text('{"items": []}', encoding="utf-8")
            with redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    image_search.main(["--batch", str(manifest), "bronze mask"])
            self.assertIn("positional query", stderr.getvalue())

    def test_page_continuation_requires_a_saved_pool(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    image_search.main([
                        "bronze mask",
                        "--filename", "hero.jpg",
                        "-o", temp_dir,
                        "--save-candidates",
                        "--candidate-page", "2",
                    ])
            self.assertIn("none was saved", stderr.getvalue())

    def test_multi_frame_camera_jpeg_keeps_its_primary_frame(self) -> None:
        try:
            from PIL import Image
        except ImportError:  # pragma: no cover - Pillow is a runtime dependency
            self.skipTest("Pillow unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "camera.jpg"
            first = Image.new("RGB", (64, 48), (200, 20, 20))
            second = Image.new("RGB", (64, 48), (20, 20, 200))
            first.save(path, format="MPO", save_all=True, append_images=[second])
            self.assertTrue(image_search._normalize_multi_frame_jpeg(path))
            with Image.open(path) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(getattr(image, "n_frames", 1), 1)
                self.assertGreater(image.getpixel((3, 3))[0], 150)
            self.assertFalse(image_search._normalize_multi_frame_jpeg(path))
