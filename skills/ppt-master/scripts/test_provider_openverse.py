import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_sources import provider_openverse


class OpenverseProviderTests(unittest.TestCase):
    def test_parse_results_keeps_cc_by_asset_and_marks_provider(self):
        payload = {
            "results": [
                {
                    "id": "ov-1",
                    "title": "City skyline",
                    "creator": "Jane Doe",
                    "license": "CC BY 4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "thumbnail": "https://cdn.example.com/thumb.jpg",
                    "url": "https://cdn.example.com/full.jpg",
                    "foreign_landing_url": "https://example.com/source",
                    "width": 1920,
                    "height": 1080,
                },
                {
                    "id": "ov-2",
                    "title": "Rejected asset",
                    "creator": "Nope",
                    "license": "CC BY-NC 4.0",
                    "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
                    "url": "https://cdn.example.com/rejected.jpg",
                    "foreign_landing_url": "https://example.com/rejected",
                    "width": 1600,
                    "height": 900,
                },
            ]
        }

        results = provider_openverse.parse_results(payload)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "openverse")
        self.assertEqual(results[0].title, "City skyline")
        self.assertEqual(results[0].author, "Jane Doe")
        self.assertEqual(results[0].license_name, "CC BY 4.0")
        self.assertEqual(
            results[0].license_url,
            "https://creativecommons.org/licenses/by/4.0/",
        )
        self.assertTrue(results[0].attribution_required)

    def test_parse_results_returns_no_candidates_for_rejected_or_empty_payload(self):
        rejected_payload = {
            "results": [
                {
                    "id": "ov-2",
                    "title": "Rejected asset",
                    "creator": "Nope",
                    "license": "CC BY-NC 4.0",
                    "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
                    "url": "https://cdn.example.com/rejected.jpg",
                },
                {
                    "id": "ov-3",
                    "title": "Missing download URL",
                    "creator": "Nope",
                    "license": "CC BY 4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                },
            ]
        }

        self.assertEqual(provider_openverse.parse_results(rejected_payload), [])
        self.assertEqual(provider_openverse.parse_results({}), [])

    def test_parse_results_uses_thumbnail_when_full_url_missing(self):
        payload = {
            "results": [
                {
                    "id": "ov-4",
                    "title": "Thumbnail only",
                    "creator": "Jane Doe",
                    "license": "CC BY 4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "thumbnail": "https://cdn.example.com/thumb-only.jpg",
                    "detail_url": "https://example.com/detail",
                    "width": 1200,
                    "height": 800,
                }
            ]
        }

        results = provider_openverse.parse_results(payload)

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].download_url,
            "https://cdn.example.com/thumb-only.jpg",
        )
        self.assertEqual(results[0].source_page_url, "https://example.com/detail")

    def test_parse_results_does_not_require_attribution_for_cc0_variant(self):
        payload = {
            "results": [
                {
                    "id": "ov-5",
                    "title": "Public domain skyline",
                    "creator": "Jane Doe",
                    "license": "CC0 1.0",
                    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                    "url": "https://cdn.example.com/public-domain.jpg",
                }
            ]
        }

        results = provider_openverse.parse_results(payload)

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].attribution_required)

    def test_search_and_download_raises_clear_error_when_no_candidates(self):
        response = mock.Mock()
        response.json.return_value = {"results": []}
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(
                provider_openverse.requests,
                "get",
                return_value=response,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "No acceptable Openverse candidates found",
                ):
                    provider_openverse.search_and_download(
                        query="city skyline",
                        output_dir=tmpdir,
                        filename="hero.jpg",
                    )

    def test_search_and_download_creates_output_directory_before_download(self):
        response = mock.Mock()
        response.json.return_value = {
            "results": [
                {
                    "id": "ov-6",
                    "title": "City skyline",
                    "creator": "Jane Doe",
                    "license": "CC BY 4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "url": "https://cdn.example.com/full.jpg",
                    "foreign_landing_url": "https://example.com/source",
                    "width": 1920,
                    "height": 1080,
                }
            ]
        }
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "images"
            download = mock.Mock()
            with mock.patch.object(
                provider_openverse.requests,
                "get",
                return_value=response,
            ), mock.patch.object(
                provider_openverse,
                "_load_download_image",
                return_value=download,
            ):
                provider_openverse.search_and_download(
                    query="city skyline",
                    output_dir=str(output_dir),
                    filename="hero.jpg",
                )

            self.assertTrue(output_dir.is_dir())
            download.assert_called_once_with(
                "https://cdn.example.com/full.jpg",
                str(output_dir / "hero.jpg"),
            )


if __name__ == "__main__":
    unittest.main()
