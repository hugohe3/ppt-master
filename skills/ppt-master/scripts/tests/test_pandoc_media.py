#!/usr/bin/env python3
"""Regression tests for output-side Pandoc image extraction and references."""

import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from urllib.parse import unquote


SCRIPTS = Path(__file__).resolve().parents[1]


def _png(color: tuple[int, int, int]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + bytes(color) * 2) * 2))
            + chunk(b"IEND", b""))


class PandocMediaTests(unittest.TestCase):
    def convert(self, source: Path, output: Path) -> tuple[str, dict, str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "source_to_md.py"), str(source),
             "-o", str(output), "--json"],
            cwd=SCRIPTS, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output.read_text(encoding="utf-8"), json.loads(result.stdout), result.stderr

    def assert_assets(self, output: Path, markdown: str, payload: dict, expected: list[bytes]) -> None:
        refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)
        self.assertEqual(len(refs), len(expected), markdown)
        for ref, content in zip(refs, expected):
            relative = Path(unquote(ref.strip("<>")))
            self.assertFalse(relative.is_absolute(), ref)
            self.assertEqual(relative.parts[0], f"{output.stem}_files")
            self.assertEqual((output.parent / relative).read_bytes(), content)
        manifest_path = Path(payload["image_manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), len(expected))
        for item in manifest:
            self.assertTrue((manifest_path.parent / item["filename"]).is_file())
            self.assertEqual(len(item["occurrences"]), 1, item)
        profile = json.loads(Path(payload["conversion_profile"]).read_text(encoding="utf-8"))
        self.assertEqual(profile["outputs"]["image_count"], len(expected))

    def test_rtf_embedded_png_is_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.rtf"
            png = _png((20, 180, 200))
            source.write_text(
                r"{\rtf1\ansi RTFBEFORE {\pict\pngblip\picw2\pich2 " + png.hex() + r"} RTFAFTER}",
                encoding="ascii",
            )
            original = source.read_bytes()
            output = root / "output" / "result.md"
            markdown, payload, _ = self.convert(source, output)
            self.assertIn("RTFBEFORE", markdown)
            self.assertIn("RTFAFTER", markdown)
            self.assert_assets(output, markdown, payload, [png])
            self.assertEqual(source.read_bytes(), original)

    def test_local_images_follow_markdown_to_a_separate_directory(self) -> None:
        documents = {
            "tex": r"\begin{document}BODYMARKER\includegraphics{assets/plot.png}\end{document}",
            "rst": "BODYMARKER\n\n.. image:: assets/plot.png\n",
            "org": "* BODYMARKER\n\n[[file:assets/plot.png]]\n",
            "typ": '= BODYMARKER\n#image("assets/plot.png")\n',
        }
        for suffix, content in documents.items():
            with self.subTest(format=suffix), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source_dir = root / "source files"
                assets = source_dir / "assets"
                assets.mkdir(parents=True)
                png = _png((20, 180, 200))
                image = assets / "plot.png"
                image.write_bytes(png)
                source = source_dir / f"main.{suffix}"
                source.write_text(content, encoding="utf-8")
                original = source.read_bytes()
                output = root / "new output" / "result.md"
                markdown, payload, _ = self.convert(source, output)
                self.assertIn("BODYMARKER", markdown)
                self.assert_assets(output, markdown, payload, [png])
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(image.read_bytes(), png)
                self.assertFalse((source_dir / "result_files").exists())

    def test_nested_media_and_duplicate_basenames_survive_spaced_output_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "source"
            expected = [_png((255, 0, 0)), _png((0, 255, 0)), _png((0, 0, 255)), _png((10, 20, 30))]
            names = ["plot.png", "media/plot.png", "media/deep/plot.png", "media/single.png"]
            for name, content in zip(names, expected):
                image = source_dir / name
                image.parent.mkdir(parents=True, exist_ok=True)
                image.write_bytes(content)
            source = source_dir / "main.rst"
            source.write_text("\n\n".join(f".. image:: {name}" for name in names), encoding="utf-8")
            output = root / "output files" / "result file.md"
            markdown, payload, _ = self.convert(source, output)
            self.assert_assets(output, markdown, payload, expected)
            self.assertIn("result%20file_files/single.png", markdown)
            self.assertIn("result%20file_files/media/plot.png", markdown)
            self.assertIn("result%20file_files/media/deep/plot.png", markdown)
            for name, content in zip(names, expected):
                self.assertEqual((source_dir / name).read_bytes(), content)

    def test_missing_image_retains_pandoc_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "main.rst"
            source.write_text("BODYMARKER\n\n.. image:: missing.png\n", encoding="utf-8")
            output = root / "output" / "result.md"
            markdown, payload, stderr = self.convert(source, output)
            self.assertIn("BODYMARKER", markdown)
            self.assertTrue(payload["warnings"])
            self.assertIn("missing.png", "\n".join(payload["warnings"]))
            self.assertIn(payload["warnings"][0], stderr)

    def test_flattening_does_not_rewrite_a_longer_image_name_or_existing_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "source"
            media = source_dir / "media"
            media.mkdir(parents=True)
            short = _png((255, 0, 0))
            long = _png((0, 255, 0))
            sentinel = _png((0, 0, 255))
            (media / "a.png").write_bytes(short)
            (media / "a.png-long.png").write_bytes(long)
            source = source_dir / "main.rst"
            source.write_text(
                ".. image:: media/a.png\n\n.. image:: media/a.png-long.png\n", encoding="utf-8",
            )
            output = root / "output" / "result.md"
            output_assets = output.parent / "result_files"
            output_assets.mkdir(parents=True)
            existing = output_assets / "a.png-long.png"
            existing.write_bytes(sentinel)
            markdown, _, _ = self.convert(source, output)
            refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)
            self.assertEqual(refs, ["result_files/a.png", "result_files/media/a.png-long.png"])
            self.assertEqual([(output.parent / ref).read_bytes() for ref in refs], [short, long])
            self.assertEqual(existing.read_bytes(), sentinel)

    def test_flattening_keeps_an_existing_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "source"
            media = source_dir / "media"
            media.mkdir(parents=True)
            png = _png((20, 180, 200))
            (media / "plot.png").write_bytes(png)
            source = source_dir / "main.rst"
            source.write_text(".. image:: media/plot.png\n", encoding="utf-8")
            output = root / "output" / "result.md"
            output_assets = output.parent / "result_files"
            output_assets.mkdir(parents=True)
            existing = output_assets / "plot.png"
            existing.symlink_to("missing.png")
            markdown, payload, _ = self.convert(source, output)
            self.assert_assets(output, markdown, payload, [png])
            self.assertIn("result_files/media/plot.png", markdown)
            self.assertTrue(existing.is_symlink())
            self.assertEqual(existing.readlink(), Path("missing.png"))

    def test_flattening_preserves_non_ascii_parentheses_and_apostrophe_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "source"
            media = source_dir / "media"
            media.mkdir(parents=True)
            names = ["中文.png", "a(b).png", "a'b.png"]
            expected = [_png((255, 0, 0)), _png((0, 255, 0)), _png((0, 0, 255))]
            for name, content in zip(names, expected):
                (media / name).write_bytes(content)
            source = source_dir / "main.rst"
            source.write_text("\n\n".join(f".. image:: media/{name}" for name in names), encoding="utf-8")
            output = root / "output" / "result file.md"
            markdown, payload, _ = self.convert(source, output)
            self.assert_assets(output, markdown, payload, expected)
            for name, content in zip(names, expected):
                self.assertEqual((media / name).read_bytes(), content)

    def test_complex_typst_failure_keeps_existing_source_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "main.typ"
            content = '#import "missing.typ": *\n#show: book.page.with(title: [Intro])\n= BODYMARKER\n'
            source.write_text(content, encoding="utf-8")
            output = root / "output" / "result.md"
            markdown, payload, _ = self.convert(source, output)
            self.assertIn('#import "missing.typ": *', markdown)
            self.assertIn("# BODYMARKER", markdown)
            self.assertTrue(any("headings mapped" in warning for warning in payload["warnings"]))
            self.assertEqual(source.read_text(encoding="utf-8"), content)
