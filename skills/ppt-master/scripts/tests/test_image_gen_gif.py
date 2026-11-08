#!/usr/bin/env python3
"""Test single-image GIF dispatch and OpenAI requests with HTTP mocked out."""

from __future__ import annotations

import base64
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import image_gen  # noqa: E402
from image_backends import backend_openai  # noqa: E402


def _fits_gif_sheet(count: int, width: int, height: int) -> bool:
    """Check the candidate sheets measured on 2026-11-08 independently."""
    grids = {
        **dict.fromkeys(range(2, 9), ((2, 4), (4, 2))),
        9: ((3, 3),),
        **dict.fromkeys(range(10, 13), ((3, 4), (4, 3), (4, 4))),
        **dict.fromkeys(range(13, 17), ((4, 4),)),
    }
    return any(
        columns * width <= 3840 and rows * height <= 3840
        and columns * rows * width * height <= 8_294_400
        for columns, rows in grids[count]
    )


def _gif_bytes() -> bytes:
    """Build a two-frame GIF fixture with transparency and infinite looping."""
    first = Image.new("P", (8, 8), 0)
    second = Image.new("P", (8, 8), 0)
    palette = [0, 0, 0, 255, 0, 0, 0, 0, 255] + [0] * (768 - 9)
    for frame in (first, second):
        frame.putpalette(palette)
    first.putpixel((2, 2), 1)
    second.putpixel((5, 5), 2)
    output = io.BytesIO()
    first.save(output, format="GIF", save_all=True, append_images=[second],
               duration=200, loop=0, transparency=0, disposal=2)
    first.close()
    second.close()
    return output.getvalue()


class GifCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(mock.patch.stopall)
        mock.patch.dict(os.environ, {}, clear=True).start()
        self.load_env = mock.patch.object(image_gen, "_load_image_env_file").start()
        self.backend = SimpleNamespace(generate=mock.Mock(), SUPPORTS_REFERENCE_IMAGE=True)
        self.resolve = mock.patch.object(
            image_gen, "_resolve_backend", return_value=(self.backend, "openai")
        ).start()
        mock.patch.object(backend_openai.requests.sessions.Session, "request",
                          side_effect=AssertionError("Unexpected network call")).start()

    def _run(self, args: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["image_gen.py", *args]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                image_gen.main()
            except SystemExit as exc:
                return exc.code, output.getvalue()
        return 0, output.getvalue()

    def test_invalid_frames_and_duration_fail_before_loading_config(self) -> None:
        for value in ("1", "17", "0", "-1", "2.5", "abc"):
            with self.subTest(frames=value):
                code, output = self._run(["p", "--gif-frames", value])
                self.assertEqual(code, 2)
                self.assertIn("--gif-frames", output)
        for value in ("0", "-1", "1.5", "abc"):
            with self.subTest(duration=value):
                code, output = self._run(["p", "--gif-frames", "2", "--gif-frame-ms", value])
                self.assertEqual(code, 2)
                self.assertIn("positive integer", output)
        code, output = self._run(["p", "--gif-frame-ms", "100"])
        self.assertEqual(code, 2)
        self.assertIn("requires --gif-frames", output)
        self.load_env.assert_not_called()
        self.resolve.assert_not_called()

    def test_gif_flags_conflict_with_non_single_image_modes(self) -> None:
        for mode in (["--manifest", "missing.json"], ["--render-md", "missing.json"],
                     ["--list-backends"]):
            for flags in (["--gif-frames", "2"], ["--gif-frame-ms", "200"],
                          ["--gif-frames", "2", "--gif-frame-ms", "200"]):
                with self.subTest(mode=mode, flags=flags):
                    code, output = self._run([*mode, *flags])
                    self.assertEqual(code, 2)
                    self.assertIn("single-image mode only", output)
                    self.assertIn(mode[0], output)
        self.load_env.assert_not_called()
        self.backend.generate.assert_not_called()

    def test_backend_without_gif_marker_is_rejected(self) -> None:
        for name in image_gen.SUPPORTED_BACKENDS:
            with self.subTest(backend=name):
                self.resolve.return_value = self.backend, name
                code, output = self._run(["p", "--gif-frames", "2"])
                self.assertEqual(code, 1)
                self.assertIn(f"backend '{name}' does not support GIF output", output)
        self.backend.generate.assert_not_called()

    def test_gif_kwargs_are_forwarded_only_when_enabled(self) -> None:
        self.backend.SUPPORTS_GIF = True
        for count in range(2, 17):
            with self.subTest(frames=count):
                self.assertEqual(self._run(["p", "--gif-frames", str(count)])[0], 0)
                self.assertEqual(self.backend.generate.call_args.kwargs["gif_frames"], count)
                self.assertNotIn("gif_frame_ms", self.backend.generate.call_args.kwargs)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            Image.new("RGB", (8, 8)).save(source)
            self.assertEqual(self._run(["edit", "--reference-image", str(source),
                                       "--gif-frames", "16", "--gif-frame-ms", "1"])[0], 0)
            self.assertEqual(self.backend.generate.call_args.kwargs, {
                "prompt": "edit", "aspect_ratio": "1:1", "image_size": "1K",
                "output_dir": None, "filename": None, "model": None,
                "reference_image": str(source), "gif_frames": 16, "gif_frame_ms": 1,
            })

    def test_plain_and_reference_calls_omit_all_gif_kwargs(self) -> None:
        expected = {"prompt": "p", "aspect_ratio": "1:1", "image_size": "1K",
                    "output_dir": None, "filename": None, "model": None}
        self.assertEqual(self._run(["p"])[0], 0)
        self.backend.generate.assert_called_once_with(**expected)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            Image.new("RGB", (8, 8)).save(source)
            self.assertEqual(self._run(["p", "--reference-image", str(source)])[0], 0)
            self.assertEqual(self.backend.generate.call_args.kwargs,
                             {**expected, "reference_image": str(source)})


class OpenAIGifTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(mock.patch.stopall)
        # The placeholder never leaves this process; the HTTP transport is blocked.
        mock.patch.dict(os.environ, {"OPENAI_API_KEY": "unused-test-placeholder"}, clear=True).start()
        mock.patch.object(backend_openai.requests.sessions.Session, "request",
                          side_effect=AssertionError("Unexpected network call")).start()
        self.gif = _gif_bytes()
        response = SimpleNamespace(ok=True, json=lambda: {
            "data": [{"b64_json": base64.b64encode(self.gif).decode("ascii")}],
        })
        self.post = mock.patch.object(backend_openai.requests, "post", return_value=response).start()
        self.sleep = mock.patch.object(backend_openai.time, "sleep").start()
        self.output = io.StringIO()
        stdout = contextlib.redirect_stdout(self.output)
        self.addCleanup(stdout.__exit__, None, None, None)
        stdout.__enter__()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = directory.name
        self.source = Path(self.tmp) / "source.png"
        Image.new("RGB", (8, 8)).save(self.source)

    def _generate(self, **kwargs: object) -> Path:
        options = {"model": "gpt-image-2.6-sunburst", "output_dir": self.tmp, "gif_frames": 2}
        options.update(kwargs)
        return Path(backend_openai.generate("loop", **options))

    def test_unsupported_models_fail_before_retries_or_credentials(self) -> None:
        models = ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare", "gpt-image-2",
                  "gpt-image-1.5", "dall-e-3", "chatgpt-image-latest", "compatible",
                  "gpt-image-2.6", "prefix-gpt-image-2.6-sunburst", "gpt-image-3")
        with mock.patch.dict(os.environ, {}, clear=True):
            for model in models:
                for reference in (None, str(self.source)):
                    with self.subTest(model=model, editing=reference is not None):
                        with self.assertRaisesRegex(ValueError, "does not support GIF output"):
                            self._generate(model=model, reference_image=reference)
        self.post.assert_not_called()
        self.sleep.assert_not_called()

    def test_supported_minor_versions_and_snapshots(self) -> None:
        for model in ("gpt-image-2.6-sunburst", "gpt-image-2.6-flare",
                      "gpt-image-2.6-sunburst-2026-11-08", "gpt-image-2.7-flare",
                      "gpt-image-2.10-sunburst"):
            with self.subTest(model=model):
                self._generate(model=model)
                self.assertEqual(self.post.call_args.kwargs["json"]["model"], model)
        self.assertTrue(backend_openai.SUPPORTS_GIF)

    def test_output_configuration_conflicts_fail_locally(self) -> None:
        for setting, values in (("OPENAI_OUTPUT_FORMAT", ("png", "jpeg", "webp", "svg", "")),
                                ("OPENAI_OUTPUT_COMPRESSION", ("0", "80", "invalid", ""))):
            for value in values:
                for reference in (None, str(self.source)):
                    with self.subTest(setting=setting, value=value, editing=reference is not None):
                        with mock.patch.dict(os.environ, {setting: value}):
                            with self.assertRaisesRegex(ValueError, setting):
                                self._generate(reference_image=reference)
        self.post.assert_not_called()
        self.sleep.assert_not_called()

    def test_backend_validates_direct_gif_arguments(self) -> None:
        for options in ({"gif_frames": 1}, {"gif_frames": 17}, {"gif_frames": 2.5},
                        {"gif_frames": True}, {"gif_frame_ms": 0}, {"gif_frame_ms": -1},
                        {"gif_frame_ms": 1.5}, {"gif_frame_ms": True},
                        {"gif_frames": None, "gif_frame_ms": 200}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self._generate(**options)
        self.post.assert_not_called()
        self.sleep.assert_not_called()

    def test_sizes_fit_sheet_budget_for_all_counts_and_ratios(self) -> None:
        for count in range(2, 17):
            for ratio in ("16:9", "9:16", "1:1", "21:9", "3:1", "1:3"):
                with self.subTest(count=count, ratio=ratio):
                    size = backend_openai._select_size("gpt-image-2.6-sunburst", ratio, "4K",
                                                       gif_frames=count)
                    width, height = map(int, size.split("x"))
                    self.assertGreater(min(width, height), 0)
                    self.assertEqual(width % 16, 0)
                    self.assertEqual(height % 16, 0)
                    self.assertTrue(_fits_gif_sheet(count, width, height), size)
                    self.assertLessEqual(max(width, height) / min(width, height), 3)
                    target_w, target_h = map(int, ratio.split(":"))
                    self.assertAlmostEqual((width / height) / (target_w / target_h), 1, delta=0.02)

    def test_measured_sizes_fit_and_rejected_sizes_do_not(self) -> None:
        measured = ((9, 1024, 576), (9, 1280, 720), (16, 768, 432), (16, 432, 768),
                    (16, 512, 512), (12, 512, 512), (9, 1232, 528), (8, 1024, 576),
                    (6, 1024, 576), (2, 512, 512))
        for count, width, height in measured:
            with self.subTest(count=count, size=(width, height)):
                self.assertTrue(_fits_gif_sheet(count, width, height))
                size = backend_openai._select_size("gpt-image-2.6-sunburst", f"{width}:{height}",
                                                   "1K", gif_frames=count)
                fitted_w, fitted_h = map(int, size.split("x"))
                self.assertGreaterEqual(fitted_w * fitted_h, width * height)
        for count, width, height in ((4, 1904, 1072), (6, 1536, 864)):
            with self.subTest(count=count, size=(width, height)):
                self.assertFalse(_fits_gif_sheet(count, width, height))

    def test_generation_and_edit_send_largest_candidate_frame(self) -> None:
        for count, width, height in ((4, 1344, 752), (10, 1104, 624), (16, 944, 528)):
            for ratio, size in (("16:9", f"{width}x{height}"), ("9:16", f"{height}x{width}")):
                for reference in (None, str(self.source)):
                    with self.subTest(count=count, ratio=ratio, editing=reference is not None):
                        self._generate(gif_frames=count, aspect_ratio=ratio, reference_image=reference)
                        request = self.post.call_args.kwargs["data" if reference else "json"]
                        self.assertEqual(request["size"], size)

    def test_generation_payload_default_duration_and_quality_mapping(self) -> None:
        for tier, quality in (("512px", "low"), ("1K", "medium"), ("2K", "high"), ("4K", "high")):
            with self.subTest(tier=tier):
                path = self._generate(gif_frames=9, aspect_ratio="16:9", image_size=tier)
                self.assertEqual(self.post.call_args.args[0], "https://api.openai.com/v1/images/generations")
                self.assertEqual(self.post.call_args.kwargs["json"], {
                    "prompt": "loop", "model": "gpt-image-2.6-sunburst", "size": "1280x720",
                    "n": 1, "quality": quality, "output_format": "gif", "frame_count": 9,
                })
                self.assertEqual(path.suffix, ".gif")
        self.assertIn("Frame size:   1280x720", self.output.getvalue())
        self.assertIn("Frames:       9", self.output.getvalue())
        self.assertIn("Frame ms:     200", self.output.getvalue())

    def test_generation_and_edit_duration_transparency_and_multipart(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_OUTPUT_FORMAT": "gif", "OPENAI_BACKGROUND": "transparent"}):
            for duration in (100, 200, 600, 800):
                for reference in (None, str(self.source)):
                    with self.subTest(duration=duration, editing=reference is not None):
                        self._generate(reference_image=reference, gif_frame_ms=duration)
                        call = self.post.call_args
                        request = call.kwargs["data" if reference else "json"]
                        self.assertEqual(request["output_format"], "gif")
                        self.assertEqual(request["frame_count"], 2)
                        self.assertEqual(request["frame_duration_ms"], duration)
                        self.assertEqual(request["background"], "transparent")
                        self.assertNotIn("output_compression", request)
                        if reference:
                            self.assertEqual(call.args[0], "https://api.openai.com/v1/images/edits")
                            self.assertNotIn("json", call.kwargs)
                            self.assertNotIn("Content-Type", call.kwargs["headers"])
                            field, (name, handle, mime) = call.kwargs["files"][0]
                            self.assertEqual((field, name, mime), ("image[]", "source.png", "image/png"))
                            self.assertTrue(handle.closed)

    def test_saved_gif_is_byte_identical_even_with_a_static_filename_suffix(self) -> None:
        for reference in (None, str(self.source)):
            for filename in (None, "loop.v2", "loop.v2.gif", "loop.v2.png", "loop.v2.jpg"):
                with self.subTest(reference=reference, filename=filename):
                    path = self._generate(reference_image=reference, filename=filename)
                    self.assertEqual(path.suffix, ".gif")
                    self.assertEqual(path.read_bytes(), self.gif)
                    with Image.open(path) as image:
                        self.assertEqual(image.n_frames, 2)
                        self.assertEqual(image.info["loop"], 0)
                        self.assertEqual(image.info["duration"], 200)
                        self.assertEqual(image.convert("RGBA").getpixel((0, 0))[3], 0)

    def test_static_generation_and_edit_payloads_are_unchanged(self) -> None:
        png = self.source.read_bytes()
        self.post.return_value.json = lambda: {"data": [{"b64_json": base64.b64encode(png).decode("ascii")}]}
        for reference in (None, str(self.source)):
            with self.subTest(editing=reference is not None):
                path = self._generate(gif_frames=None, model="gpt-image-2.5-sunburst",
                                      reference_image=reference)
                request = self.post.call_args.kwargs["data" if reference else "json"]
                self.assertEqual(request, {"prompt": "loop", "model": "gpt-image-2.5-sunburst",
                                           "size": "1024x1024", "n": 1, "quality": "medium"})
                self.assertEqual(path.suffix, ".png")
                self.assertEqual(path.read_bytes(), png)
