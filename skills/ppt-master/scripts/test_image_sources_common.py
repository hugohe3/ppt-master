import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
    ensure_json_parent,
    is_allowed_license,
    normalize_orientation,
    score_candidate,
)


class ImageSourcesCommonTests(unittest.TestCase):
    def test_open_license_allows_cc_by_but_rejects_cc_by_nc(self):
        self.assertTrue(
            is_allowed_license(
                "CC BY 4.0",
                "https://creativecommons.org/licenses/by/4.0/",
            )
        )
        self.assertFalse(
            is_allowed_license(
                "CC BY-NC 4.0",
                "https://creativecommons.org/licenses/by-nc/4.0/",
            )
        )

    def test_pexels_license_requires_matching_provider(self):
        self.assertFalse(
            is_allowed_license("Pexels License", "", provider="")
        )
        self.assertTrue(
            is_allowed_license("Pexels License", "", provider="pexels")
        )

    def test_normalize_orientation(self):
        self.assertEqual(normalize_orientation(1920, 1080), "landscape")
        self.assertEqual(normalize_orientation(1080, 1920), "portrait")
        self.assertEqual(normalize_orientation(1000, 1000), "square")

    def test_landscape_background_prefers_landscape_candidate(self):
        request = ImageSearchRequest(
            query="mountains",
            orientation="landscape",
            use_case="background",
        )
        landscape = AssetCandidate(
            provider="wikimedia",
            asset_id="landscape",
            title="wide",
            width=1920,
            height=1080,
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
        )
        portrait = AssetCandidate(
            provider="wikimedia",
            asset_id="portrait",
            title="tall",
            width=1080,
            height=1920,
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
        )

        self.assertGreater(
            score_candidate(landscape, request),
            score_candidate(portrait, request),
        )

    def test_ensure_json_parent_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "image_sources.json"
            ensure_json_parent(path)
            self.assertTrue(path.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
