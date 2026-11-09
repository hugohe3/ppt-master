#!/usr/bin/env python3
"""Regression tests for the Volcengine Seedream image backend."""

import io
import os
import sys
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_backends import backend_volcengine  # noqa: E402


ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
LAS_URL = "https://operator.las.cn-beijing.volces.com/api/v1/images/generations"
PRO = "doubao-seedream-5-0-pro-260628"
FLASH = "doubao-seedream-5-0-flash-260915"
V45 = "doubao-seedream-4-5-251128"


def _pixels(size: str) -> int:
    width, height = map(int, size.split("x"))
    return width * height


class VolcengineBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stdout = self.stack.enter_context(redirect_stdout(io.StringIO()))
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"url": "https://example.invalid/result.jpeg"}]}
        self.post = self.stack.enter_context(patch.object(
            backend_volcengine.requests, "post", return_value=response,
        ))
        self.stack.enter_context(patch.object(
            backend_volcengine, "download_image", side_effect=lambda url, path: path,
        ))
        self.stack.enter_context(patch.object(backend_volcengine.time, "sleep"))

    def _env(self, **values: str) -> None:
        self.stack.enter_context(patch.dict(os.environ, values, clear=True))

    def _call(self) -> tuple[str, dict, dict]:
        args, kwargs = self.post.call_args
        return args[0], kwargs["headers"], kwargs["json"]

    def test_ark_key_defaults_to_ark_and_seedream_5_pro(self) -> None:
        self._env(ARK_API_KEY="ark-key")
        backend_volcengine.generate("A harbor", aspect_ratio="16:9", filename="hero.jpeg")

        url, headers, payload = self._call()
        self.assertEqual(url, ARK_URL)
        self.assertEqual(headers["Authorization"], "Bearer ark-key")
        self.assertEqual(payload, {
            "model": PRO, "prompt": "A harbor", "size": "2848x1600",
            "response_format": "url", "watermark": False,
        })

    def test_lone_las_key_keeps_las_and_seedream_4_5(self) -> None:
        self._env(LAS_API_KEY="las-key")
        backend_volcengine.generate("A harbor", aspect_ratio="16:9", image_size="4K", filename="a.jpeg")

        url, headers, payload = self._call()
        self.assertEqual(url, LAS_URL)
        self.assertEqual(headers["Authorization"], "Bearer las-key")
        self.assertEqual((payload["model"], payload["size"]), (V45, "5504x3040"))

    def test_both_keys_prefer_ark_unless_base_url_selects_las(self) -> None:
        self._env(ARK_API_KEY="ark-key", LAS_API_KEY="las-key")
        backend_volcengine.generate("A harbor", filename="a.jpeg")
        url, headers, _ = self._call()
        self.assertEqual((url, headers["Authorization"]), (ARK_URL, "Bearer ark-key"))

        os.environ["VOLCENGINE_BASE_URL"] = "https://operator.las.cn-beijing.volces.com/api/v1"
        backend_volcengine.generate("A harbor", filename="b.jpeg")
        url, headers, payload = self._call()
        self.assertEqual((url, headers["Authorization"]), (LAS_URL, "Bearer las-key"))
        self.assertEqual(payload["model"], V45)

    def test_seedream_5_sizes_stay_within_official_limits(self) -> None:
        limits = backend_volcengine.SEEDREAM_5_PRO_LIMITS
        for model in (PRO, FLASH):
            for tier in ("512px", "1K", "2K", "4K"):
                for ratio in ("1:1", "16:9", "9:16", "21:9", "1.85:1", "4:1"):
                    size = backend_volcengine._resolve_size(ratio, tier, model)
                    with self.subTest(model=model, tier=tier, ratio=ratio, size=size):
                        self.assertGreaterEqual(_pixels(size), limits["min_pixels"])
                        self.assertLessEqual(_pixels(size), limits["max_pixels"])
        self.assertEqual(backend_volcengine._resolve_size("1:1", "1K", PRO), "1024x1024")

    def test_4k_on_seedream_5_reports_fallback(self) -> None:
        self._env(ARK_API_KEY="ark-key", VOLCENGINE_MODEL=FLASH)
        backend_volcengine.generate("A harbor", aspect_ratio="16:9", image_size="4K", filename="a.jpeg")

        _, _, payload = self._call()
        self.assertEqual(payload["model"], FLASH)
        self.assertEqual(payload["size"], "2848x1600")
        self.assertIn("does not support 4K", self.stdout.getvalue())

    def test_unknown_model_fails_before_any_request(self) -> None:
        self._env(ARK_API_KEY="ark-key", VOLCENGINE_MODEL="doubao-seedream-9-0")
        with self.assertRaises(ValueError):
            backend_volcengine.generate("A harbor", filename="a.jpeg")
        self.post.assert_not_called()

