import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_sources.provider_openverse import parse_results


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

        results = parse_results(payload)

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


if __name__ == "__main__":
    unittest.main()
