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
    def test_image_search_request_supports_forward_compatible_fields(self):
        request = ImageSearchRequest(
            query="city skyline",
            purpose="hero",
            orientation="landscape",
            min_width=1280,
            min_height=720,
            filename="hero.png",
            slide="3",
        )

        self.assertEqual(request.query, "city skyline")
        self.assertEqual(request.purpose, "hero")
        self.assertEqual(request.orientation, "landscape")
        self.assertEqual(request.min_width, 1280)
        self.assertEqual(request.min_height, 720)
        self.assertEqual(request.filename, "hero.png")
        self.assertEqual(request.slide, "3")

    def test_asset_candidate_supports_richer_provider_metadata(self):
        candidate = AssetCandidate(
            provider="wikimedia",
            title="Downtown skyline",
            source_page_url="https://example.com/source",
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            width=1920,
            height=1080,
            download_url="https://example.com/download.jpg",
            author="Example Author",
            attribution_required=True,
            raw={"id": "abc123"},
        )

        self.assertEqual(candidate.provider, "wikimedia")
        self.assertEqual(candidate.title, "Downtown skyline")
        self.assertEqual(candidate.source_page_url, "https://example.com/source")
        self.assertEqual(candidate.download_url, "https://example.com/download.jpg")
        self.assertEqual(candidate.author, "Example Author")
        self.assertTrue(candidate.attribution_required)
        self.assertEqual(candidate.raw, {"id": "abc123"})

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
            purpose="background",
            orientation="landscape",
        )
        landscape = AssetCandidate(
            provider="wikimedia",
            title="wide",
            source_page_url="https://example.com/landscape",
            download_url="https://example.com/landscape.jpg",
            width=1920,
            height=1080,
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
        )
        portrait = AssetCandidate(
            provider="wikimedia",
            title="tall",
            source_page_url="https://example.com/portrait",
            download_url="https://example.com/portrait.jpg",
            width=1080,
            height=1920,
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
        )

        self.assertGreater(
            score_candidate(landscape, request),
            score_candidate(portrait, request),
        )

    def test_rejected_license_never_beats_allowed_candidate(self):
        request = ImageSearchRequest(
            query="forest",
            purpose="background",
            orientation="landscape",
        )
        allowed = AssetCandidate(
            provider="wikimedia",
            title="usable",
            source_page_url="https://example.com/allowed",
            download_url="https://example.com/allowed.jpg",
            width=1600,
            height=900,
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
        )
        rejected = AssetCandidate(
            provider="wikimedia",
            title="too restrictive",
            source_page_url="https://example.com/rejected",
            download_url="https://example.com/rejected.jpg",
            width=20000,
            height=12000,
            license_name="CC BY-NC 4.0",
            license_url="https://creativecommons.org/licenses/by-nc/4.0/",
        )

        self.assertGreater(
            score_candidate(allowed, request),
            score_candidate(rejected, request),
        )

    def test_ensure_json_parent_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "image_sources.json"
            ensure_json_parent(path)
            self.assertTrue(path.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
