import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class ImageSearchCliTests(unittest.TestCase):
    def setUp(self):
        self._provider_module_names = [
            "image_sources.provider_openverse",
            "image_sources.provider_wikimedia",
            "image_sources.provider_pexels",
            "image_sources.provider_pixabay",
        ]
        self._saved_modules = {
            name: sys.modules.get(name) for name in self._provider_module_names
        }
        for name in self._provider_module_names:
            sys.modules.pop(name, None)

        sys.modules.pop("image_search", None)
        self.image_search = importlib.import_module("image_search")

    def tearDown(self):
        sys.modules.pop("image_search", None)
        for name in self._provider_module_names:
            sys.modules.pop(name, None)
            saved_module = self._saved_modules[name]
            if saved_module is not None:
                sys.modules[name] = saved_module

    def test_import_does_not_load_provider_modules(self):
        for name in self._provider_module_names:
            self.assertNotIn(name, sys.modules)

    def test_parser_accepts_expected_options_and_defaults(self):
        parser = self.image_search.build_parser()

        args = parser.parse_args(
            [
                "city skyline",
                "--provider",
                "wikimedia",
                "--filename",
                "hero.jpg",
                "--output",
                "projects/demo/images",
                "--slide",
                "3",
                "--purpose",
                "background",
                "--orientation",
                "landscape",
            ]
        )

        self.assertEqual(args.query, "city skyline")
        self.assertEqual(args.provider, "wikimedia")
        self.assertEqual(args.filename, "hero.jpg")
        self.assertEqual(args.output, "projects/demo/images")
        self.assertEqual(args.slide, "3")
        self.assertEqual(args.purpose, "background")
        self.assertEqual(args.orientation, "landscape")
        self.assertIsNone(args.manifest)

    def test_parser_only_exposes_currently_implemented_providers(self):
        parser = self.image_search.build_parser()
        provider_action = parser._option_string_actions["--provider"]

        self.assertEqual(
            tuple(provider_action.choices),
            ("openverse", "wikimedia"),
        )

    def test_parser_defaults_orientation_and_provider(self):
        parser = self.image_search.build_parser()

        args = parser.parse_args(
            [
                "city skyline",
                "--filename",
                "hero.jpg",
            ]
        )

        self.assertEqual(args.provider, "openverse")
        self.assertEqual(args.output, ".")
        self.assertEqual(args.slide, "")
        self.assertEqual(args.purpose, "")
        self.assertEqual(args.orientation, "any")
        self.assertIsNone(args.manifest)

    def test_write_sources_manifest_writes_required_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "image_sources.json"

            self.image_search.write_sources_manifest(
                path,
                [
                    {
                        "filename": "hero.jpg",
                        "provider": "wikimedia",
                    }
                ],
            )

            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(
            data["license_verification"],
            self.image_search.LICENSE_VERIFICATION_NOTE,
        )
        self.assertIn("generated_at", data)
        self.assertEqual(data["items"][0]["filename"], "hero.jpg")

    def test_main_writes_provider_manifest_to_output_directory_when_manifest_omitted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            manifest_item = {
                "filename": "hero.jpg",
                "provider": "openverse",
                "search_query": "city skyline",
                "slide": "2",
                "purpose": "cover",
                "source_page_url": "https://example.com/source",
                "download_url": "https://example.com/hero.jpg",
                "author": "Example Author",
                "license_name": "CC BY 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "attribution_required": True,
                "attribution_text": "City skyline - by Example Author - CC BY 4.0",
            }

            provider = mock.Mock()
            provider.search_and_download.return_value = manifest_item
            with mock.patch.object(
                self.image_search,
                "load_provider",
                return_value=provider,
            ) as load_provider:
                exit_code = self.image_search.main(
                    [
                        "city skyline",
                        "--filename",
                        "hero.jpg",
                        "--output",
                        str(output_dir),
                        "--provider",
                        "openverse",
                        "--slide",
                        "2",
                        "--purpose",
                        "cover",
                        "--orientation",
                        "landscape",
                    ]
                )

            manifest_path = output_dir / "image_sources.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        load_provider.assert_called_once_with("openverse")
        provider.search_and_download.assert_called_once_with(
            query="city skyline",
            output_dir=str(output_dir),
            filename="hero.jpg",
            slide="2",
            purpose="cover",
            orientation="landscape",
        )
        self.assertEqual(data["items"][0]["filename"], "hero.jpg")
        self.assertEqual(data["items"][0]["provider"], "openverse")
        self.assertEqual(data["items"][0]["search_query"], "city skyline")
        self.assertEqual(data["items"][0]["slide"], "2")
        self.assertEqual(data["items"][0]["purpose"], "cover")
        self.assertEqual(data["items"][0]["source_page_url"], "https://example.com/source")
        self.assertEqual(data["items"][0]["download_url"], "https://example.com/hero.jpg")
        self.assertEqual(data["items"][0]["author"], "Example Author")
        self.assertEqual(data["items"][0]["license_name"], "CC BY 4.0")
        self.assertEqual(
            data["items"][0]["license_url"],
            "https://creativecommons.org/licenses/by/4.0/",
        )
        self.assertTrue(data["items"][0]["attribution_required"])
        self.assertEqual(
            data["items"][0]["attribution_text"],
            "City skyline - by Example Author - CC BY 4.0",
        )

    def test_main_raises_when_selected_provider_module_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"

            with mock.patch.object(
                self.image_search,
                "load_provider",
                side_effect=ModuleNotFoundError("missing provider"),
            ):
                with self.assertRaises(ModuleNotFoundError):
                    self.image_search.main(
                        [
                            "city skyline",
                            "--filename",
                            "hero.jpg",
                            "--output",
                            str(output_dir),
                            "--provider",
                            "openverse",
                        ]
                    )

            manifest_path = output_dir / "image_sources.json"
            self.assertFalse(manifest_path.exists())


if __name__ == "__main__":
    unittest.main()
