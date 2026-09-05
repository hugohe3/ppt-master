#!/usr/bin/env python3
"""Regression tests for the Tencent Cloud TokenHub image backend."""

import base64
import io
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import image_gen  # noqa: E402
from image_backends import backend_tencent  # noqa: E402


class TencentBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.dict(os.environ, {"TENCENT_API_KEY": "test-key"}, clear=True))
        self.stdout = stack.enter_context(redirect_stdout(io.StringIO()))
        self.response = Mock(status_code=200)
        self.response.json.return_value = {
            "data": [{"url": "https://example.invalid/result.png"}],
            "request_id": "test-request",
        }
        self.post = stack.enter_context(patch.object(
            backend_tencent.requests, "post", return_value=self.response,
        ))
        stack.enter_context(patch.object(
            backend_tencent.requests, "get", side_effect=AssertionError("Unexpected network request"),
        ))
        self.download = stack.enter_context(patch.object(
            backend_tencent, "download_image", side_effect=lambda url, path: path,
        ))
        self.save = stack.enter_context(patch.object(
            backend_tencent, "save_image_bytes", side_effect=lambda data, path, **kwargs: path,
        ))
        self.sleep = stack.enter_context(patch.object(backend_tencent.time, "sleep"))

    def test_hy_endpoint_payload_and_download(self) -> None:
        result = backend_tencent.generate("A mountain", aspect_ratio="16:9", filename="hero.png")

        self.post.assert_called_once_with(
            "https://tokenhub.tencentmaas.com/v1/wand/hunyuan-image/v3-generation",
            headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
            json={
                "model": "hy-image-v3", "prompt": "A mountain",
                "size": "1360x768", "revise": True,
            },
            timeout=300,
        )
        self.download.assert_called_once_with("https://example.invalid/result.png", "hero.png")
        self.save.assert_not_called()
        self.assertEqual(result, "hero.png")
        self.assertIn("Resolution:   1360x768", self.stdout.getvalue())

    def test_seedream_endpoints_and_payloads(self) -> None:
        for model, resolution in (
            ("seedream-image-v5.0-pro", "1024x1024"),
            ("seedream-image-v5.0-lite", "2048x2048"),
        ):
            with self.subTest(model=model):
                self.post.reset_mock()
                backend_tencent.generate("A mountain", model=model)
                self.post.assert_called_once_with(
                    "https://tokenhub.tencentmaas.com/v1/wand/si-image/generation",
                    headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
                    json={
                        "model": model, "prompt": "A mountain", "size": resolution,
                        "watermark": False, "response_format": "url", "output_format": "png",
                    },
                    timeout=300,
                )

    def test_hy_area_limit_and_orientation(self) -> None:
        for ratio in ("16:9", "1:1", "9:16"):
            with self.subTest(ratio=ratio):
                resolution = backend_tencent._resolve_size(ratio, "1K")
                width, height = map(int, resolution.split("x"))
                expected_width, expected_height = map(int, ratio.split(":"))
                self.assertLessEqual(width * height, 1024 * 1024)
                self.assertGreater(width * height, 0.97 * 1024 * 1024)
                self.assertAlmostEqual(width / height, expected_width / expected_height, delta=0.02)
                for dimension in (width, height):
                    self.assertGreaterEqual(dimension, 512)
                    self.assertLessEqual(dimension, 2048)
                    self.assertEqual(dimension % 16, 0)

    def test_hy_dimension_boundaries(self) -> None:
        for ratio, logical_size, resolution in (
            ("1:1", "512px", "512x512"),
            ("4:1", "1K", "2048x512"),
            ("1:4", "1K", "512x2048"),
        ):
            with self.subTest(ratio=ratio, size=logical_size):
                self.assertEqual(backend_tencent._resolve_size(ratio, logical_size), resolution)

    def test_hy_rejects_impossible_sizes_before_request(self) -> None:
        for ratio, logical_size in (
            ("1:1", "2K"), ("1:1", "4K"), ("16:9", "512px"),
            ("1:8", "1K"), ("8:1", "1K"),
        ):
            with self.subTest(ratio=ratio, size=logical_size):
                with self.assertRaisesRegex(ValueError, "512-2048.*multiples of 16.*1024x1024"):
                    backend_tencent.generate("test", aspect_ratio=ratio, image_size=logical_size)
        self.post.assert_not_called()

    def test_seedream_lite_upgrades_small_sizes_once(self) -> None:
        for logical_size in ("1K", "512px"):
            with self.subTest(size=logical_size):
                self.stdout.seek(0)
                self.stdout.truncate(0)
                backend_tencent.generate("test", model="seedream-image-v5.0-lite", image_size=logical_size)
                self.assertEqual(self.post.call_args.kwargs["json"]["size"], "2048x2048")
                self.assertEqual(self.stdout.getvalue().count(f"upgrading {logical_size} to 2K"), 1)
                self.assertIn("Resolution:   2048x2048", self.stdout.getvalue())

    def test_seedream_area_scales_across_cli_ratios(self) -> None:
        for model, logical_size, side in (
            ("seedream-image-v5.0-pro", "1K", 1024),
            ("seedream-image-v5.0-pro", "2K", 2048),
            ("seedream-image-v5.0-lite", "2K", 2048),
            ("seedream-image-v5.0-lite", "4K", 4096),
        ):
            for ratio in image_gen.ALL_ASPECT_RATIOS:
                with self.subTest(model=model, size=logical_size, ratio=ratio):
                    size = backend_tencent._resolve_size(ratio, logical_size, model)
                    width, height = map(int, size.split("x"))
                    ratio_width, ratio_height = map(int, ratio.split(":"))
                    self.assertAlmostEqual(width * height / side ** 2, 1.0, delta=0.004)
                    self.assertAlmostEqual(width / height, ratio_width / ratio_height, delta=0.025)

    def test_seedream_pro_rejects_512px_and_4k(self) -> None:
        for logical_size in ("512px", "4K"):
            with self.subTest(size=logical_size):
                with self.assertRaisesRegex(ValueError, "Use 1K or 2K"):
                    backend_tencent.generate("test", model="seedream-image-v5.0-pro", image_size=logical_size)
        self.post.assert_not_called()

    def test_invalid_ratio_and_size_fail_before_request(self) -> None:
        for ratio in ("invalid", "0:1", "1:0", "-1:2", "1:2:3"):
            with self.subTest(ratio=ratio):
                with self.assertRaisesRegex(ValueError, "Unsupported aspect ratio"):
                    backend_tencent.generate("test", aspect_ratio=ratio)
        with self.assertRaisesRegex(ValueError, "Unsupported image size"):
            backend_tencent.generate("test", image_size="3K")
        self.post.assert_not_called()

    def test_unknown_model_lists_supported_models(self) -> None:
        with self.assertRaises(ValueError) as caught:
            backend_tencent.generate("test", model="other-model")
        for model in backend_tencent.SUPPORTED_MODELS:
            self.assertIn(model, str(caught.exception))
        self.post.assert_not_called()

    def test_vidu_reports_unsupported_async_api(self) -> None:
        with self.assertRaisesRegex(ValueError, "Vidu.*asynchronous submit/query API.*not supported"):
            backend_tencent.generate("test", model="vidu-image-q2")
        self.post.assert_not_called()

    def test_missing_key_names_both_options(self) -> None:
        os.environ.pop("TENCENT_API_KEY")
        with self.assertRaisesRegex(ValueError, "No API key found.*TENCENT_API_KEY or TOKENHUB_API_KEY"):
            backend_tencent.generate("test")
        self.post.assert_not_called()
        self.sleep.assert_not_called()

    def test_key_fallback_and_primary_precedence(self) -> None:
        os.environ["TOKENHUB_API_KEY"] = "fallback-key"
        backend_tencent.generate("test")
        self.assertEqual(self.post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
        os.environ["TENCENT_API_KEY"] = ""
        backend_tencent.generate("test")
        self.assertEqual(self.post.call_args.kwargs["headers"]["Authorization"], "Bearer fallback-key")

    def test_missing_image_includes_response_body(self) -> None:
        for model in backend_tencent.SUPPORTED_MODELS:
            for items in (None, [], [{}], [{"url": ""}]):
                with self.subTest(model=model, items=items):
                    self.response.json.return_value = {"data": items, "request_id": "missing-image"}
                    with self.assertRaisesRegex(RuntimeError, "missing image URL.*missing-image"):
                        backend_tencent.generate("test", model=model, max_retries=0)
        self.download.assert_not_called()
        self.save.assert_not_called()

    def test_full_endpoint_is_used_without_appending_path(self) -> None:
        for model, endpoint in backend_tencent.MODEL_ENDPOINTS.items():
            with self.subTest(model=model):
                url = "https://tokenhub-intl.tencentmaas.com" + endpoint
                os.environ["TENCENT_BASE_URL"] = url + "/"
                backend_tencent.generate("test", model=model)
                self.assertEqual(self.post.call_args.args[0], url)

    def test_international_base_selects_model_endpoint(self) -> None:
        os.environ["TENCENT_BASE_URL"] = "https://tokenhub-intl.tencentmaas.com/"
        backend_tencent.generate("test")
        self.assertEqual(
            self.post.call_args.args[0],
            "https://tokenhub-intl.tencentmaas.com/v1/wand/hunyuan-image/v3-generation",
        )

    def test_provider_options_apply_only_to_their_model(self) -> None:
        os.environ.update({
            "TENCENT_REVISE": "false", "TENCENT_WATERMARK": "true", "TENCENT_OUTPUT_FORMAT": "jpeg",
        })
        self.assertEqual(backend_tencent.generate("test"), "test.png")
        self.assertIs(self.post.call_args.kwargs["json"]["revise"], False)
        self.assertNotIn("watermark", self.post.call_args.kwargs["json"])
        self.assertNotIn("output_format", self.post.call_args.kwargs["json"])
        self.assertEqual(backend_tencent.generate("test", model="seedream-image-v5.0-pro"), "test.jpeg")
        self.assertIs(self.post.call_args.kwargs["json"]["watermark"], True)
        self.assertEqual(self.post.call_args.kwargs["json"]["output_format"], "jpeg")
        self.assertNotIn("revise", self.post.call_args.kwargs["json"])

    def test_seedream_base64_response_uses_shared_save(self) -> None:
        image_bytes = b"\x89PNG\r\n\x1a\nminimal-mocked-image"
        self.response.json.return_value = {"data": [{"b64_json": base64.b64encode(image_bytes).decode("ascii")}]}
        result = backend_tencent.generate("test", model="seedream-image-v5.0-pro")
        self.save.assert_called_once_with(image_bytes, "test.png", content_type="image/png")
        self.download.assert_not_called()
        self.assertEqual(result, "test.png")

    def test_permanent_http_errors_do_not_retry(self) -> None:
        for status, code in ((400, "FieldInvalid"), (401, "Unauthorized"), (422, "CreationPolicyViolation")):
            with self.subTest(status=status):
                self.post.reset_mock()
                self.response.status_code = status
                self.response.text = '{"error": {"code": "' + code + '"}}'
                with self.assertRaisesRegex(RuntimeError, rf"\({status}\).*{code}"):
                    backend_tencent.generate("test")
                self.post.assert_called_once()
        self.sleep.assert_not_called()

    def test_rate_limit_uses_shared_exponential_backoff(self) -> None:
        limited = Mock(status_code=429, text='{"error": {"code": "ConcurrencyLimit"}}')
        self.post.side_effect = [limited, limited, self.response]
        backend_tencent.generate("test")
        self.assertEqual(self.post.call_count, 3)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [10, 20])

    def test_server_error_is_retried(self) -> None:
        failure = Mock(status_code=500, text='{"error": {"code": "InternalError"}}')
        self.post.side_effect = [failure, self.response]
        backend_tencent.generate("test")
        self.sleep.assert_called_once_with(5)
        self.assertEqual(self.post.call_count, 2)

    def test_prompt_limits_fail_before_request(self) -> None:
        for model, limit in (("hy-image-v3", 8192), ("seedream-image-v5.0-pro", 600)):
            with self.subTest(model=model):
                with self.assertRaisesRegex(ValueError, f"1-{limit} characters"):
                    backend_tencent.generate("x" * (limit + 1), model=model)
        self.post.assert_not_called()

    def test_invalid_provider_options_do_not_retry(self) -> None:
        for key, model in (
            ("TENCENT_REVISE", "hy-image-v3"),
            ("TENCENT_WATERMARK", "seedream-image-v5.0-pro"),
            ("TENCENT_OUTPUT_FORMAT", "seedream-image-v5.0-pro"),
        ):
            with self.subTest(key=key), patch.dict(os.environ, {key: "invalid"}):
                with self.assertRaisesRegex(ValueError, key):
                    backend_tencent.generate("test", model=model)
        self.post.assert_not_called()
        self.sleep.assert_not_called()

    def test_registry_aliases_and_env_file_reach_backend(self) -> None:
        env_text = (
            "IMAGE_BACKEND=tokenhub\nTOKENHUB_API_KEY=dotenv-key\n"
            "TENCENT_MODEL=seedream-image-v5.0-pro\n"
            "TENCENT_BASE_URL=https://tokenhub-intl.tencentmaas.com\n"
            "TENCENT_WATERMARK=true\nTENCENT_OUTPUT_FORMAT=jpeg\nTENCENT_REVISE=false\n"
        )
        os.environ.pop("TENCENT_API_KEY")
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(env_text, encoding="utf-8")
            with patch("config.resolve_env_path", return_value=env_path):
                image_gen._load_image_env_file()
        self.assertEqual(os.environ["TENCENT_REVISE"], "false")
        for alias in ("tencent", "tokenhub", "hunyuan", "tencentmaas"):
            self.assertEqual(image_gen.BACKEND_ALIASES[alias], "tencent")
        backend, name = image_gen._resolve_backend()
        self.assertEqual(name, "tencent")
        self.assertIs(backend, backend_tencent)
        self.assertEqual(backend.generate("test"), "test.jpeg")
        self.assertEqual(
            self.post.call_args.args[0], "https://tokenhub-intl.tencentmaas.com/v1/wand/si-image/generation",
        )
        self.assertEqual(self.post.call_args.kwargs["headers"]["Authorization"], "Bearer dotenv-key")
        self.assertIs(self.post.call_args.kwargs["json"]["watermark"], True)


if __name__ == "__main__":
    unittest.main()
