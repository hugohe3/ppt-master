#!/usr/bin/env python3
"""Regression tests for shared image-backend naming, error, and retry helpers."""

from __future__ import annotations

import os
import sys
import unittest
from email.utils import formatdate
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_backends import backend_common  # noqa: E402


def _response(status: int, body: str, headers: dict | None = None) -> SimpleNamespace:
    import requests

    return SimpleNamespace(
        status_code=status,
        text=body,
        headers=requests.structures.CaseInsensitiveDict(headers or {}),
    )


class OutputPathTests(unittest.TestCase):
    def test_cli_filename_keeps_dotted_stem(self) -> None:
        path = backend_common.resolve_output_path("p", "/out", "gpt-image-2.5-sunburst_hero")
        self.assertEqual(path, os.path.join("/out", "gpt-image-2.5-sunburst_hero.png"))

    def test_image_extension_is_replaced(self) -> None:
        path = backend_common.resolve_output_path("p", "/out", "hero.v2.PNG", ".webp")
        self.assertEqual(path, os.path.join("/out", "hero.v2.webp"))


class BillingErrorTests(unittest.TestCase):
    def test_openai_billing_codes_are_global_permanent(self) -> None:
        for code in (
            "credit_balance_exhausted",
            "organization_spend_limit_exceeded",
            "project_spend_limit_exceeded",
            "organization_usage_limit_exceeded",
        ):
            with self.subTest(code=code):
                exc = backend_common.http_error(
                    _response(429, '{"error": {"code": "%s"}}' % code), "OpenAI image generation"
                )
                self.assertTrue(backend_common.is_global_permanent_error(exc))
                self.assertFalse(backend_common.is_rate_limit_error(exc))

    def test_plain_rate_limit_stays_retryable(self) -> None:
        exc = backend_common.http_error(
            _response(429, '{"error": {"code": "rate_limit_exceeded"}}'), "OpenAI image generation"
        )
        self.assertFalse(backend_common.is_permanent_error(exc))
        self.assertTrue(backend_common.is_rate_limit_error(exc))


class RetryDelayTests(unittest.TestCase):
    def test_retry_after_seconds_wins(self) -> None:
        exc = backend_common.http_error(_response(429, "slow down", {"Retry-After": "7"}), "x")
        self.assertEqual(backend_common.retry_delay(2, rate_limited=True, exc=exc), 7)

    def test_retry_after_ms_rounds_up(self) -> None:
        exc = backend_common.http_error(_response(429, "slow down", {"retry-after-ms": "1500"}), "x")
        self.assertEqual(exc.retry_after, 2)

    def test_retry_after_http_date(self) -> None:
        with mock.patch.object(backend_common.time, "time", return_value=1_000_000.0):
            exc = backend_common.http_error(
                _response(503, "busy", {"Retry-After": formatdate(1_000_030, usegmt=True)}), "x"
            )
        self.assertEqual(exc.retry_after, 30)

    def test_unrepresentable_retry_after_is_ignored(self) -> None:
        for value in ("inf", "1e309", "nan", "soon"):
            with self.subTest(value=value):
                exc = backend_common.http_error(_response(429, "slow down", {"Retry-After": value}), "x")
                self.assertIsNone(exc.retry_after)

    def test_retry_after_is_capped_and_found_through_the_cause_chain(self) -> None:
        cause = backend_common.http_error(_response(429, "slow down", {"Retry-After": "86400"}), "x")
        try:
            raise RuntimeError("Failed after 4 attempts") from cause
        except RuntimeError as wrapped:
            self.assertEqual(backend_common.retry_after_seconds(wrapped), 86400)
            with self.assertRaises(RuntimeError):
                backend_common.retry_delay(0, rate_limited=True, exc=wrapped)
        at_cap = backend_common.http_error(_response(429, "slow down", {"Retry-After": "300"}), "x")
        self.assertEqual(backend_common.retry_delay(0, rate_limited=True, exc=at_cap), 300)

    def test_backend_stops_retrying_when_the_wait_exceeds_the_cap(self) -> None:
        from image_backends import backend_openai

        limited = _response(429, '{"error": {"code": "rate_limit_exceeded"}}', {"Retry-After": "86400"})
        limited.ok = False
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), \
                mock.patch.object(backend_openai.requests, "post", return_value=limited) as post, \
                mock.patch.object(backend_openai.time, "sleep") as sleep, \
                mock.patch("sys.stdout"):
            with self.assertRaises(RuntimeError) as raised:
                backend_openai.generate("p")
        self.assertEqual(post.call_count, 1)
        sleep.assert_not_called()
        self.assertEqual(backend_common.retry_after_seconds(raised.exception), 86400)

    def test_non_openai_backend_waits_for_retry_after(self) -> None:
        from image_backends import backend_qwen

        limited = _response(429, '{"code": "Throttling.RateQuota"}', {"Retry-After": "42"})
        limited.json = lambda: {"code": "Throttling.RateQuota"}
        limited.ok = False
        with mock.patch.dict(os.environ, {"QWEN_API_KEY": "test"}), \
                mock.patch.object(backend_qwen.requests, "post", return_value=limited), \
                mock.patch.object(backend_qwen.time, "sleep") as sleep, \
                mock.patch("sys.stdout"):
            with self.assertRaises(RuntimeError):
                backend_qwen.generate("p", max_retries=1)
        sleep.assert_called_once_with(42)

    def test_rate_limit_backoff_has_bounded_jitter(self) -> None:
        exc = backend_common.http_error(_response(429, "slow down"), "x")
        self.assertIsNone(exc.retry_after)
        delays = {backend_common.retry_delay(1, rate_limited=True, exc=exc) for _ in range(200)}
        self.assertTrue(all(20 <= delay <= 25 for delay in delays))
        self.assertGreater(len(delays), 1)


class AspectRatioTests(unittest.TestCase):
    def test_any_positive_ratio_parses_exactly(self) -> None:
        self.assertEqual(backend_common.parse_aspect_ratio("1.85:1"), backend_common.parse_aspect_ratio("37:20"))
        self.assertEqual(backend_common.parse_aspect_ratio(" 32 : 18 "), backend_common.parse_aspect_ratio("16:9"))
        for value in ("abc", "16:9:1", "0:1", "1:0", "-1:2", "inf:1", "nan:1", ""):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Invalid aspect ratio"):
                backend_common.parse_aspect_ratio(value)

    def test_nearest_ratio_prefers_exact_then_log_distance(self) -> None:
        choices = ["1:1", "16:9", "9:16", "21:9"]
        self.assertEqual(backend_common.nearest_aspect_ratio("32:18", choices), "16:9")
        self.assertEqual(backend_common.nearest_aspect_ratio("4:1", choices), "21:9")
        self.assertEqual(backend_common.nearest_aspect_ratio("1:4", choices), "9:16")

    def test_fit_size_clamps_ratio_and_keeps_orientation(self) -> None:
        rules = {"step": 8, "min_edge": 512, "max_edge": 2048}
        self.assertEqual(backend_common.fit_size("10:1", pixels=1024 * 1024, **rules), (2048, 512))
        self.assertEqual(backend_common.fit_size("1:10", pixels=4096 * 4096, **rules), (512, 2048))
        width, height = backend_common.fit_size("1:20", pixels=2048 * 2048, min_pixels=3_686_400,
                                                max_pixels=16_777_216, max_ratio=16)
        self.assertAlmostEqual(height / width, 16, delta=0.1)
        self.assertTrue(3_686_400 <= width * height <= 16_777_216)

    def test_fit_size_rounding_never_exceeds_the_ratio_limit(self) -> None:
        width, height = backend_common.fit_size("1000:1", pixels=4096 * 4096, min_pixels=921_600,
                                                max_pixels=4_624_220, max_ratio=16)
        self.assertLessEqual(width / height, 16)
        self.assertLessEqual(width * height, 4_624_220)

    def test_extreme_integer_ratios_stay_finite(self) -> None:
        huge, tiny = f"{10**309}:1", f"1:{10**324}"
        self.assertEqual(backend_common.fit_size(huge, pixels=1024 * 1024, step=16, max_ratio=3), (1776, 592))
        self.assertEqual(backend_common.nearest_aspect_ratio(tiny, ["1:1", "1:3"]), "1:3")
        backend_common.note_aspect_ratio(tiny, "1:3")


class OpenAISizeTests(unittest.TestCase):
    def test_listed_ratios_keep_their_table_sizes(self) -> None:
        from image_backends import backend_openai

        for tier, sizes in backend_openai.GPT_IMAGE_2_SIZES.items():
            for ratio, size in sizes.items():
                with self.subTest(tier=tier, ratio=ratio):
                    self.assertEqual(backend_openai._select_size("gpt-image-2.5-sunburst", ratio, tier), size)

    def test_any_ratio_fits_gpt_image_2_rules(self) -> None:
        from image_backends import backend_openai

        for ratio in ("4:1", "1:4", "8:1", "3:1", "2:1", "1:2", "16:10", "10:16", "9:21", "1.85:1", "7:2"):
            for tier in ("512px", "1K", "2K", "4K"):
                with self.subTest(ratio=ratio, tier=tier):
                    size = backend_openai._select_size("gpt-image-2", ratio, tier)
                    backend_openai._validate_gpt_image_2_size(size)
        self.assertEqual(backend_openai._select_size("gpt-image-2.5-flare", "4:1", "1K"), "1776x592")

    def test_legacy_and_unknown_models_use_their_nearest_entry(self) -> None:
        from image_backends import backend_openai

        self.assertEqual(backend_openai._select_size("gpt-image-1.5", "4:1", "1K"), "1536x1024")
        self.assertEqual(backend_openai._select_size("compatible-model", "1:4", "1K"), "1024x1792")
        # Unlisted ratios compare against real sizes, not nominal keys (5:4 -> 1536x1024).
        self.assertEqual(backend_openai._select_size("gpt-image-1.5", "1.2:1", "1K"), "1024x1024")
        self.assertEqual(backend_openai._select_size("compatible-model", "1.24:1", "1K"), "1536x1024")
        self.assertEqual(backend_openai._select_size("gpt-image-1.5", "5:4", "1K"), "1536x1024")


class ManifestAspectRatioTests(unittest.TestCase):
    def _load(self, ratio: str) -> dict:
        import json
        import tempfile

        import image_gen

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image_prompts.json"
            item = {"filename": "a.png", "prompt": "p", "aspect_ratio": ratio, "status": "Pending",
                    "page_role": "local", "text_policy": "none"}
            path.write_text(json.dumps({"items": [item]}), encoding="utf-8")
            return image_gen.load_manifest(str(path))

    def test_manifest_keeps_any_requested_ratio(self) -> None:
        for ratio in ("4:1", "1.85:1", "7:2"):
            with self.subTest(ratio=ratio):
                self.assertEqual(self._load(ratio)["items"][0]["aspect_ratio"], ratio)

    def test_manifest_rejects_malformed_ratio(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid aspect ratio"):
            self._load("0:1")
