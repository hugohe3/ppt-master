import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_sources import provider_wikimedia


class WikimediaProviderTests(unittest.TestCase):
    def test_parse_results_extracts_license_and_author_and_marks_provider(self):
        payload = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Skyline.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/example.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Skyline.jpg",
                                "thumburl": "https://upload.wikimedia.org/thumb/example.jpg",
                                "width": 2048,
                                "height": 1365,
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "LicenseUrl": {
                                        "value": "https://creativecommons.org/licenses/by-sa/4.0/"
                                    },
                                    "Artist": {"value": "<span>Jane Doe</span>"},
                                    "ImageDescription": {"value": "<i>Skyline at dusk</i>"},
                                },
                            }
                        ],
                    }
                }
            }
        }

        results = provider_wikimedia.parse_results(payload)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "wikimedia")
        self.assertEqual(results[0].title, "Skyline at dusk")
        self.assertEqual(results[0].author, "Jane Doe")
        self.assertEqual(results[0].license_name, "CC BY-SA 4.0")
        self.assertEqual(
            results[0].license_url,
            "https://creativecommons.org/licenses/by-sa/4.0/",
        )
        self.assertTrue(results[0].attribution_required)

    def test_parse_results_returns_no_candidates_for_rejected_or_empty_payload(self):
        rejected_payload = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Restricted.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/restricted.jpg",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-NC 4.0"},
                                    "LicenseUrl": {
                                        "value": "https://creativecommons.org/licenses/by-nc/4.0/"
                                    },
                                },
                            },
                            {
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "LicenseUrl": {
                                        "value": "https://creativecommons.org/licenses/by-sa/4.0/"
                                    },
                                },
                            },
                        ],
                    }
                }
            }
        }

        self.assertEqual(provider_wikimedia.parse_results(rejected_payload), [])
        self.assertEqual(provider_wikimedia.parse_results({}), [])

    def test_parse_results_falls_back_to_thumburl_credit_and_page_title(self):
        payload = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Fallback title.jpg",
                        "imageinfo": [
                            {
                                "thumburl": "https://upload.wikimedia.org/thumb/example.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Fallback_title.jpg",
                                "width": 640,
                                "height": 480,
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "LicenseUrl": {
                                        "value": "https://creativecommons.org/licenses/by-sa/4.0/"
                                    },
                                    "Credit": {"value": "<span>Fallback Author</span>"},
                                },
                            }
                        ],
                    }
                }
            }
        }

        results = provider_wikimedia.parse_results(payload)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Fallback title.jpg")
        self.assertEqual(results[0].author, "Fallback Author")
        self.assertEqual(
            results[0].download_url,
            "https://upload.wikimedia.org/thumb/example.jpg",
        )

    def test_parse_results_does_not_require_attribution_for_public_domain_label(self):
        payload = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:PublicDomain.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/public-domain.jpg",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "Public domain"},
                                    "LicenseUrl": {
                                        "value": "https://creativecommons.org/publicdomain/mark/1.0/"
                                    },
                                },
                            }
                        ],
                    }
                }
            }
        }

        results = provider_wikimedia.parse_results(payload)

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].attribution_required)

    def test_search_and_download_raises_clear_error_when_no_candidates(self):
        response = mock.Mock()
        response.json.return_value = {"query": {"pages": {}}}
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(
                provider_wikimedia.requests,
                "get",
                return_value=response,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "No acceptable Wikimedia candidates found",
                ):
                    provider_wikimedia.search_and_download(
                        query="city skyline",
                        output_dir=tmpdir,
                        filename="hero.jpg",
                    )

    def test_search_and_download_creates_output_directory_before_download(self):
        response = mock.Mock()
        response.json.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Skyline.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/example.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Skyline.jpg",
                                "width": 2048,
                                "height": 1365,
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "LicenseUrl": {
                                        "value": "https://creativecommons.org/licenses/by-sa/4.0/"
                                    },
                                    "Artist": {"value": "Jane Doe"},
                                },
                            }
                        ],
                    }
                }
            }
        }
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "images"
            download = mock.Mock()
            with mock.patch.object(
                provider_wikimedia.requests,
                "get",
                return_value=response,
            ), mock.patch.object(
                provider_wikimedia,
                "_load_download_image",
                return_value=download,
            ):
                provider_wikimedia.search_and_download(
                    query="city skyline",
                    output_dir=str(output_dir),
                    filename="hero.jpg",
                )

            self.assertTrue(output_dir.is_dir())
            download.assert_called_once_with(
                "https://upload.wikimedia.org/example.jpg",
                str(output_dir / "hero.jpg"),
            )


if __name__ == "__main__":
    unittest.main()
