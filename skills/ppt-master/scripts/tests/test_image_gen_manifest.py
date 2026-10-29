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



class ManifestRetryAfterTests(unittest.TestCase):
    def test_rate_limited_batch_waits_for_server_retry_after(self) -> None:
        from unittest import mock

        import requests
        from PIL import Image

        calls: dict[str, int] = {}

        def generate(**kwargs: object) -> str:
            name = str(kwargs["filename"])
            calls[name] = calls.get(name, 0) + 1
            if name == "a.png" and calls[name] == 1:
                headers = requests.structures.CaseInsensitiveDict({"Retry-After": "37"})
                cause = backend_common.http_error(
                    SimpleNamespace(status_code=429, text="rate limit", headers=headers),
                    "OpenAI image generation",
                )
                raise RuntimeError(f"Failed after 4 attempts. Last error: {cause}") from cause
            path = Path(str(kwargs["output_dir"])) / name
            Image.new("RGB", (8, 8)).save(path, format="PNG")
            return str(path)

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "image_prompts.json"
            items = [
                {"filename": name, "prompt": "p", "aspect_ratio": "1:1", "status": "Pending",
                 "page_role": "local", "text_policy": "none"}
                for name in ("a.png", "b.png")
            ]
            manifest_path.write_text(json.dumps({"items": items}), encoding="utf-8")
            manifest = image_gen.load_manifest(str(manifest_path))
            with mock.patch.object(image_gen.time, "sleep") as sleep, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                image_gen._run_manifest(
                    manifest, str(manifest_path), SimpleNamespace(generate=generate),
                    initial_concurrency=2, image_size="1K", output_dir=tmp, model=None,
                )
            self.assertIn(mock.call(37), sleep.call_args_list)
            self.assertEqual([item["status"] for item in manifest["items"]], ["Generated", "Generated"])

    def test_retry_after_beyond_the_cap_stops_the_run_instead_of_sleeping(self) -> None:
        from unittest import mock

        import requests
        from PIL import Image

        def generate(**kwargs: object) -> str:
            name = str(kwargs["filename"])
            if name == "a.png":
                headers = requests.structures.CaseInsensitiveDict({"Retry-After": str(10**20)})
                cause = backend_common.http_error(
                    SimpleNamespace(status_code=429, text="rate limit", headers=headers),
                    "OpenAI image generation",
                )
                raise RuntimeError(f"Failed after 4 attempts. Last error: {cause}") from cause
            path = Path(str(kwargs["output_dir"])) / name
            Image.new("RGB", (8, 8)).save(path, format="PNG")
            return str(path)

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "image_prompts.json"
            items = [
                {"filename": name, "prompt": "p", "aspect_ratio": "1:1", "status": "Pending",
                 "page_role": "local", "text_policy": "none"}
                for name in ("a.png", "b.png", "c.png")
            ]
            manifest_path.write_text(json.dumps({"items": items}), encoding="utf-8")
            manifest = image_gen.load_manifest(str(manifest_path))
            with mock.patch.object(image_gen.time, "sleep") as sleep, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = image_gen._run_manifest(
                    manifest, str(manifest_path), SimpleNamespace(generate=generate),
                    initial_concurrency=2, image_size="1K", output_dir=tmp, model=None,
                )
            sleep.assert_not_called()
            self.assertEqual(result, (1, 0, 0))
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            statuses = {item["filename"]: item["status"] for item in saved["items"]}
            self.assertEqual(statuses, {"a.png": "Pending", "b.png": "Generated", "c.png": "Pending"})

            argv = ["image_gen.py", "--manifest", str(manifest_path), "--backend", "openai"]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(image_gen, "_load_image_env_file"), \
                    mock.patch.object(image_gen, "_validate_runtime_config"), \
                    mock.patch.object(image_gen, "_resolve_backend",
                                      return_value=(SimpleNamespace(generate=generate), "openai")), \
                    mock.patch.object(image_gen.time, "sleep"), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as stopped:
                    image_gen.main()
            self.assertEqual(stopped.exception.code, 1)
