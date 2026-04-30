import importlib
import json
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
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
        sys.modules.pop("image_sources.notes_writer", None)
        self.image_search = importlib.import_module("image_search")
        self.notes_writer = importlib.import_module("image_sources.notes_writer")

    def tearDown(self):
        sys.modules.pop("image_search", None)
        sys.modules.pop("image_sources.notes_writer", None)
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
            ("openverse", "wikimedia", "pexels", "pixabay"),
        )

    def test_parser_choices_match_provider_registry(self):
        parser = self.image_search.build_parser()
        provider_action = parser._option_string_actions["--provider"]

        self.assertEqual(
            tuple(provider_action.choices),
            tuple(self.image_search.PROVIDER_REGISTRY),
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

    def test_append_image_credits_writes_heading_only_once_across_repeated_calls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "notes" / "01_cover.md"

            self.notes_writer.append_image_credits(
                note_path,
                ["Credit one"],
            )
            self.notes_writer.append_image_credits(
                note_path,
                ["- Credit two"],
            )

            content = note_path.read_text(encoding="utf-8")

        self.assertEqual(content.count("Image Credits"), 1)
        self.assertIn("- Credit one\n", content)
        self.assertIn("- Credit two\n", content)

    def test_append_image_credits_does_not_duplicate_identical_credit_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "notes" / "01_cover.md"

            self.notes_writer.append_image_credits(
                note_path,
                ["Credit one"],
            )
            self.notes_writer.append_image_credits(
                note_path,
                ["- Credit one"],
            )

            content = note_path.read_text(encoding="utf-8")

        self.assertEqual(content.count("Image Credits"), 1)
        self.assertEqual(content.count("- Credit one\n"), 1)

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

    def test_main_writes_note_attribution_when_slide_is_supplied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "demo"
            output_dir = project_root / "images"
            manifest_item = {
                "filename": "hero.jpg",
                "provider": "openverse",
                "search_query": "city skyline",
                "slide": "01_cover.md",
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
            ):
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
                        "01_cover.md",
                    ]
                )

            note_path = project_root / "notes" / "01_cover.md"
            note_content = note_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(note_content.count("Image Credits"), 1)
        self.assertIn(
            "- City skyline - by Example Author - CC BY 4.0\n",
            note_content,
        )

    def test_main_writes_numeric_slide_notes_to_legacy_slide_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "demo"
            output_dir = project_root / "images"
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
            ):
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
                    ]
                )

            legacy_note_path = project_root / "notes" / "slide02.md"
            legacy_note_exists = legacy_note_path.exists()
            numeric_note_exists = (project_root / "notes" / "2.md").exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(legacy_note_exists)
        self.assertFalse(numeric_note_exists)

    def test_main_warns_and_skips_note_write_for_noncanonical_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloaded-assets"
            stderr = io.StringIO()
            manifest_item = {
                "filename": "hero.jpg",
                "provider": "openverse",
                "search_query": "city skyline",
                "slide": "01_cover.md",
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
            ):
                with redirect_stderr(stderr):
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
                            "01_cover.md",
                        ]
                    )

            stray_note_path = output_dir / "notes" / "01_cover.md"
            stray_note_exists = stray_note_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertIn("Skipping note attribution", stderr.getvalue())
        self.assertFalse(stray_note_exists)

    def test_main_returns_cli_error_when_selected_provider_module_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            stderr = io.StringIO()

            with mock.patch.object(
                self.image_search,
                "load_provider",
                side_effect=ModuleNotFoundError("missing provider"),
            ):
                with redirect_stderr(stderr):
                    exit_code = self.image_search.main(
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
            self.assertEqual(exit_code, 1)
            self.assertIn("Provider 'openverse' is unavailable", stderr.getvalue())
            self.assertFalse(manifest_path.exists())

    def test_main_returns_cli_error_when_provider_search_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            stderr = io.StringIO()
            provider = mock.Mock()
            provider.search_and_download.side_effect = RuntimeError(
                "No acceptable Pexels candidates found for query: city skyline"
            )

            with mock.patch.object(
                self.image_search,
                "load_provider",
                return_value=provider,
            ):
                with redirect_stderr(stderr):
                    exit_code = self.image_search.main(
                        [
                            "city skyline",
                            "--filename",
                            "hero.jpg",
                            "--output",
                            str(output_dir),
                            "--provider",
                            "pexels",
                        ]
                    )

            manifest_path = output_dir / "image_sources.json"
            self.assertEqual(exit_code, 1)
            self.assertIn(
                "Image search failed for provider 'pexels': "
                "No acceptable Pexels candidates found for query: city skyline",
                stderr.getvalue(),
            )
            self.assertFalse(manifest_path.exists())

    def test_main_still_propagates_unexpected_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            provider = mock.Mock()
            provider.search_and_download.side_effect = ValueError("unexpected")

            with mock.patch.object(
                self.image_search,
                "load_provider",
                return_value=provider,
            ):
                with self.assertRaises(ValueError):
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


if __name__ == "__main__":
    unittest.main()
