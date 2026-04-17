#!/usr/bin/env python3
"""
Unit tests for the MiniMax image generation backend.
"""

import base64
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Make the parent scripts/ directory importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_backends.backend_minimax import (
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    _extract_image_bytes,
    _resolve_dimensions,
    _resolve_url,
)


# ---------------------------------------------------------------------------
# _resolve_url
# ---------------------------------------------------------------------------

class TestResolveUrl:
    def test_full_endpoint_returned_as_is(self):
        url = "https://api.minimax.io/v1/image_generation"
        assert _resolve_url(url) == url

    def test_versioned_base_appends_path(self):
        assert _resolve_url("https://api.minimax.io/v1") == \
            "https://api.minimax.io/v1/image_generation"

    def test_root_base_appends_v1_and_path(self):
        assert _resolve_url("https://api.minimax.io") == \
            "https://api.minimax.io/v1/image_generation"

    def test_trailing_slash_stripped(self):
        assert _resolve_url("https://api.minimax.io/") == \
            "https://api.minimax.io/v1/image_generation"

    def test_domestic_endpoint(self):
        assert _resolve_url("https://api.minimaxi.com") == \
            "https://api.minimaxi.com/v1/image_generation"

    def test_domestic_full_endpoint(self):
        url = "https://api.minimaxi.com/v1/image_generation"
        assert _resolve_url(url) == url


# ---------------------------------------------------------------------------
# DEFAULT_ENDPOINT
# ---------------------------------------------------------------------------

class TestDefaultEndpoint:
    def test_uses_international_domain(self):
        assert "api.minimax.io" in DEFAULT_ENDPOINT

    def test_not_domestic_domain(self):
        assert "api.minimaxi.com" not in DEFAULT_ENDPOINT

    def test_contains_image_generation_path(self):
        assert DEFAULT_ENDPOINT.endswith("/image_generation")


# ---------------------------------------------------------------------------
# DEFAULT_MODEL
# ---------------------------------------------------------------------------

class TestDefaultModel:
    def test_default_model_is_image_01(self):
        assert DEFAULT_MODEL == "image-01"


# ---------------------------------------------------------------------------
# _resolve_dimensions
# ---------------------------------------------------------------------------

class TestResolveDimensions:
    def test_1k_1x1(self):
        w, h = _resolve_dimensions("1:1", "1K")
        assert w == 1024 and h == 1024

    def test_1k_16x9(self):
        w, h = _resolve_dimensions("16:9", "1K")
        assert w == 1280 and h == 720

    def test_512px_1x1(self):
        w, h = _resolve_dimensions("1:1", "512px")
        assert w == 512 and h == 512

    def test_unsupported_ratio_raises(self):
        with pytest.raises(ValueError, match="Unsupported aspect ratio"):
            _resolve_dimensions("7:3", "1K")

    def test_portrait_9x16(self):
        w, h = _resolve_dimensions("9:16", "1K")
        assert w == 720 and h == 1280


# ---------------------------------------------------------------------------
# _extract_image_bytes
# ---------------------------------------------------------------------------

class TestExtractImageBytes:
    def test_extracts_base64_image(self):
        sample = base64.b64encode(b"fake-image-data").decode()
        payload = {"data": {"image_base64": [sample]}}
        result = _extract_image_bytes(payload)
        assert result == b"fake-image-data"

    def test_returns_none_when_no_data(self):
        assert _extract_image_bytes({}) is None

    def test_returns_none_when_empty_list(self):
        assert _extract_image_bytes({"data": {"image_base64": []}}) is None

    def test_handles_missing_data_key(self):
        assert _extract_image_bytes({"other": "value"}) is None
