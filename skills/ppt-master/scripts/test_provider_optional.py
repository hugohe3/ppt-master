import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_sources import provider_pexels, provider_pixabay
from image_sources.provider_common import is_allowed_license


class OptionalProviderLicenseTests(unittest.TestCase):
    def test_pexels_license_is_only_allowed_for_pexels_provider(self):
        self.assertFalse(is_allowed_license("Pexels License", "", provider=""))
        self.assertFalse(is_allowed_license("Pexels License", "", provider="pixabay"))
        self.assertTrue(is_allowed_license("Pexels License", "", provider="pexels"))

    def test_pixabay_license_is_only_allowed_for_pixabay_provider(self):
        self.assertFalse(is_allowed_license("Pixabay Content License", "", provider=""))
        self.assertFalse(
            is_allowed_license("Pixabay Content License", "", provider="pexels")
        )
        self.assertTrue(
            is_allowed_license("Pixabay Content License", "", provider="pixabay")
        )


class PexelsProviderTests(unittest.TestCase):
    def test_search_and_download_requires_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "PEXELS_API_KEY is required",
                ):
                    provider_pexels.search_and_download(
                        query="city skyline",
                        output_dir=tmpdir,
                        filename="hero.jpg",
                    )

    def test_search_and_download_raises_clear_error_when_no_results(self):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"photos": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"PEXELS_API_KEY": "pexels-key"}, clear=True):
                with mock.patch.object(provider_pexels.requests, "get", return_value=response):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "No acceptable Pexels candidates found",
                    ):
                        provider_pexels.search_and_download(
                            query="city skyline",
                            output_dir=tmpdir,
                            filename="hero.jpg",
                        )

    def test_search_and_download_raises_clear_error_when_all_results_are_unusable(self):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "photos": [
                {
                    "id": 11,
                    "width": 2400,
                    "height": 1600,
                    "url": "https://www.pexels.com/photo/city-skyline-11/",
                    "photographer": "Jane Doe",
                    "src": {},
                    "alt": "City skyline without image source",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"PEXELS_API_KEY": "pexels-key"}, clear=True):
                with mock.patch.object(provider_pexels.requests, "get", return_value=response):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "No acceptable Pexels candidates found",
                    ):
                        provider_pexels.search_and_download(
                            query="city skyline",
                            output_dir=tmpdir,
                            filename="hero.jpg",
                        )

    def test_search_and_download_downloads_selected_image_and_returns_manifest(self):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "photos": [
                {
                    "id": 10,
                    "width": 2400,
                    "height": 1600,
                    "url": "https://www.pexels.com/photo/city-skyline-10/",
                    "photographer": "Jane Doe",
                    "src": {
                        "original": "https://images.pexels.com/photos/10/original.jpeg",
                        "large2x": "https://images.pexels.com/photos/10/large2x.jpeg",
                    },
                    "alt": "City skyline at dusk",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "images"
            download = mock.Mock()
            with mock.patch.dict(os.environ, {"PEXELS_API_KEY": "pexels-key"}, clear=True):
                with mock.patch.object(
                    provider_pexels.requests,
                    "get",
                    return_value=response,
                ) as get_mock, mock.patch.object(
                    provider_pexels,
                    "_load_download_image",
                    return_value=download,
                ):
                    result = provider_pexels.search_and_download(
                        query="city skyline",
                        output_dir=str(output_dir),
                        filename="hero.jpg",
                        slide="2",
                        purpose="cover",
                        orientation="landscape",
                    )

            self.assertTrue(output_dir.is_dir())

        get_mock.assert_called_once()
        _, kwargs = get_mock.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "pexels-key")
        self.assertEqual(kwargs["params"]["query"], "city skyline")
        self.assertEqual(kwargs["params"]["orientation"], "landscape")
        download.assert_called_once_with(
            "https://images.pexels.com/photos/10/original.jpeg",
            str(output_dir / "hero.jpg"),
        )
        self.assertEqual(result["provider"], "pexels")
        self.assertEqual(result["source_page_url"], "https://www.pexels.com/photo/city-skyline-10/")
        self.assertEqual(
            result["download_url"],
            "https://images.pexels.com/photos/10/original.jpeg",
        )
        self.assertEqual(result["author"], "Jane Doe")
        self.assertEqual(result["license_name"], "Pexels License")
        self.assertEqual(result["license_url"], "https://www.pexels.com/license/")
        self.assertFalse(result["attribution_required"])
        self.assertEqual(
            result["attribution_text"],
            "City skyline at dusk - by Jane Doe - Pexels License",
        )


class PixabayProviderTests(unittest.TestCase):
    def test_search_and_download_requires_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "PIXABAY_API_KEY is required",
                ):
                    provider_pixabay.search_and_download(
                        query="forest trail",
                        output_dir=tmpdir,
                        filename="hero.jpg",
                    )

    def test_search_and_download_raises_clear_error_when_no_results(self):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"hits": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"PIXABAY_API_KEY": "pixabay-key"}, clear=True):
                with mock.patch.object(provider_pixabay.requests, "get", return_value=response):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "No acceptable Pixabay candidates found",
                    ):
                        provider_pixabay.search_and_download(
                            query="forest trail",
                            output_dir=tmpdir,
                            filename="hero.jpg",
                        )

    def test_search_and_download_raises_clear_error_when_all_results_are_unusable(self):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "hits": [
                {
                    "id": 21,
                    "pageURL": "https://pixabay.com/photos/forest-trail-21/",
                    "user": "John Doe",
                    "tags": "forest trail, nature",
                    "imageWidth": 2400,
                    "imageHeight": 1600,
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"PIXABAY_API_KEY": "pixabay-key"}, clear=True):
                with mock.patch.object(provider_pixabay.requests, "get", return_value=response):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "No acceptable Pixabay candidates found",
                    ):
                        provider_pixabay.search_and_download(
                            query="forest trail",
                            output_dir=tmpdir,
                            filename="hero.jpg",
                        )

    def test_search_and_download_downloads_selected_image_and_returns_manifest(self):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "hits": [
                {
                    "id": 20,
                    "pageURL": "https://pixabay.com/photos/forest-trail-20/",
                    "user": "John Doe",
                    "tags": "forest trail, nature",
                    "imageWidth": 2400,
                    "imageHeight": 1600,
                    "largeImageURL": "https://cdn.pixabay.com/photo-20-large.jpg",
                    "webformatURL": "https://cdn.pixabay.com/photo-20-web.jpg",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "images"
            download = mock.Mock()
            with mock.patch.dict(os.environ, {"PIXABAY_API_KEY": "pixabay-key"}, clear=True):
                with mock.patch.object(
                    provider_pixabay.requests,
                    "get",
                    return_value=response,
                ) as get_mock, mock.patch.object(
                    provider_pixabay,
                    "_load_download_image",
                    return_value=download,
                ):
                    result = provider_pixabay.search_and_download(
                        query="forest trail",
                        output_dir=str(output_dir),
                        filename="hero.jpg",
                        slide="4",
                        purpose="background",
                        orientation="landscape",
                    )

            self.assertTrue(output_dir.is_dir())

        get_mock.assert_called_once()
        _, kwargs = get_mock.call_args
        self.assertEqual(kwargs["params"]["key"], "pixabay-key")
        self.assertEqual(kwargs["params"]["q"], "forest trail")
        self.assertEqual(kwargs["params"]["orientation"], "horizontal")
        download.assert_called_once_with(
            "https://cdn.pixabay.com/photo-20-large.jpg",
            str(output_dir / "hero.jpg"),
        )
        self.assertEqual(result["provider"], "pixabay")
        self.assertEqual(result["source_page_url"], "https://pixabay.com/photos/forest-trail-20/")
        self.assertEqual(
            result["download_url"],
            "https://cdn.pixabay.com/photo-20-large.jpg",
        )
        self.assertEqual(result["author"], "John Doe")
        self.assertEqual(result["license_name"], "Pixabay Content License")
        self.assertEqual(result["license_url"], "https://pixabay.com/service/license-summary/")
        self.assertFalse(result["attribution_required"])
        self.assertEqual(
            result["attribution_text"],
            "forest trail, nature - by John Doe - Pixabay Content License",
        )


if __name__ == "__main__":
    unittest.main()
