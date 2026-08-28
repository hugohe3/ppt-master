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
