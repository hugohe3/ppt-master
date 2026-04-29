import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from image_search import build_parser, write_sources_manifest


class ImageSearchCliTests(unittest.TestCase):
    def test_parser_accepts_provider_and_filename(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "city skyline",
                "--provider",
                "wikimedia",
                "--filename",
                "hero.jpg",
            ]
        )

        self.assertEqual(args.query, "city skyline")
        self.assertEqual(args.provider, "wikimedia")
        self.assertEqual(args.filename, "hero.jpg")

    def test_write_sources_manifest_writes_item_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "image_sources.json"

            write_sources_manifest(
                path,
                [
                    {
                        "filename": "hero.jpg",
                        "provider": "wikimedia",
                    }
                ],
            )

            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["items"][0]["filename"], "hero.jpg")


if __name__ == "__main__":
    unittest.main()
