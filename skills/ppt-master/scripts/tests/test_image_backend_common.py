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

    def test_rate_limit_backoff_has_bounded_jitter(self) -> None:
        exc = backend_common.http_error(_response(429, "slow down"), "x")
        self.assertIsNone(exc.retry_after)
        delays = {backend_common.retry_delay(1, rate_limited=True, exc=exc) for _ in range(200)}
        self.assertTrue(all(20 <= delay <= 25 for delay in delays))
        self.assertGreater(len(delays), 1)
