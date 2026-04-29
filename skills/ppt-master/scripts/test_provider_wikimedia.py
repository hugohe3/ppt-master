import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_sources.provider_wikimedia import parse_results


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

        results = parse_results(payload)

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


if __name__ == "__main__":
    unittest.main()
