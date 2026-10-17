#!/usr/bin/env python3
"""Regression tests for manifest-driven image generation output names."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import image_gen  # noqa: E402
from image_backends import backend_common  # noqa: E402


class ManifestOutputNameTests(unittest.TestCase):
    def test_dotted_filenames_do_not_overwrite_each_other(self) -> None:
        from PIL import Image

        def generate(**kwargs: object) -> str:
            path = backend_common.resolve_output_path(
                str(kwargs["prompt"]), str(kwargs["output_dir"]), str(kwargs["filename"])
            )
            Image.new("RGB", (8, 8), str(kwargs["prompt"])).save(path, format="PNG")
            return path

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "image_prompts.json"
            items = [
                {"filename": name, "prompt": color, "aspect_ratio": "1:1", "status": "Pending",
                 "page_role": "local", "text_policy": "none"}
                for name, color in (("hero.png", "red"), ("hero.v2.png", "blue"))
            ]
            manifest_path.write_text(json.dumps({"items": items}), encoding="utf-8")
            manifest = image_gen.load_manifest(str(manifest_path))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                image_gen._run_manifest(
                    manifest, str(manifest_path), SimpleNamespace(generate=generate),
                    initial_concurrency=1, image_size="1K", output_dir=tmp, model=None,
                )
            with Image.open(Path(tmp) / "hero.png") as first, \
                    Image.open(Path(tmp) / "hero.v2.png") as second:
                self.assertEqual(first.getpixel((0, 0)), (255, 0, 0))
                self.assertEqual(second.getpixel((0, 0)), (0, 0, 255))

