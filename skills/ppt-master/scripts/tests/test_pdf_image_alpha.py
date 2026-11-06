#!/usr/bin/env python3
"""PPT Master - PDF Image Alpha Regression Tests

Preserve independent PDF soft masks and recover with opaque images when needed.

Usage:
    python3 -m unittest tests.test_pdf_image_alpha

Examples:
    Run the module from the scripts directory.

Dependencies:
    PyMuPDF, Pillow, and the local PDF converter.
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1] / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import fitz  # noqa: E402
from PIL import Image  # noqa: E402

import pdf_to_md  # noqa: E402

NEAREST = getattr(Image, "Resampling", Image).NEAREST


def _png(image):
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return stream.getvalue()


class PdfImageAlphaTests(unittest.TestCase):
    def _source(self, root, mask_size=(120, 80)):
        base = Image.new("RGB", (120, 80), (220, 40, 80))
        base.putpixel((90, 40), (20, 160, 230))
        mask = None
        if mask_size:
            mask = Image.new("L", mask_size)
            mask.putdata([round(255 * x / (mask.width - 1))
                          for y in range(mask.height) for x in range(mask.width)])
        source = root / "source.pdf"
        with fitz.open() as document:
            page = document.new_page(width=500, height=400)
            page.insert_text((40, 40), "Body text survives transparent image extraction.", fontsize=12)
            page.insert_image(fitz.Rect(40, 100, 280, 260), stream=_png(base),
                              mask=_png(mask) if mask else None)
            document.save(source)
        with fitz.open(source) as document:
            block = next(block for block in document[0].get_text("dict")["blocks"] if block["type"] == 1)
        return source, base, mask, block

    def _convert(self, source, *, mode="all"):
        output = source.with_name("result.md")
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            markdown = pdf_to_md.extract_pdf_to_markdown(str(source), str(output), images=mode)
        self.assertIn("Body text survives transparent image extraction.", markdown)
        manifest = json.loads((output.parent / "result_files/image_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 1)
        asset = output.parent / "result_files" / manifest[0]["filename"]
        self.assertIn(asset.name, markdown)
        return asset, stderr.getvalue()

    def test_same_size_mask_preserves_alpha_and_color(self):
        for mode in ("all", "filtered"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                source, base, mask, _ = self._source(Path(directory))
                original = source.read_bytes()
                asset, stderr = self._convert(source, mode=mode)
                with Image.open(asset) as image:
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(image.convert("RGB").tobytes(), base.tobytes())
                    self.assertEqual(image.getchannel("A").tobytes(), mask.tobytes())
                self.assertEqual(source.read_bytes(), original)
                self.assertNotIn("SMask was not applied", stderr)

    def test_mask_is_resized_to_base_dimensions(self):
        for size in ((60, 40), (240, 160)):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory:
                source, base, mask, _ = self._source(Path(directory), size)
                asset, _ = self._convert(source)
                with Image.open(asset) as image:
                    self.assertEqual(image.size, base.size)
                    self.assertEqual(image.convert("RGB").tobytes(), base.tobytes())
                    expected = mask.resize(base.size, NEAREST)
                    self.assertEqual(image.getchannel("A").tobytes(), expected.tobytes())

    def test_pillow_without_resampling_enum_resizes_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            source, base, mask, _ = self._source(Path(directory), (60, 40))
            legacy_image = SimpleNamespace(open=Image.open, NEAREST=NEAREST,
                                           DecompressionBombError=Image.DecompressionBombError)
            with patch("PIL.Image", legacy_image):
                asset, stderr = self._convert(source)
            with Image.open(asset) as image:
                self.assertEqual(image.size, base.size)
                self.assertEqual(image.getchannel("A").tobytes(),
                                 mask.resize(base.size, NEAREST).tobytes())
            self.assertNotIn("SMask was not applied", stderr)

    def test_opaque_image_bytes_are_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source, _, _, block = self._source(Path(directory), None)
            asset, stderr = self._convert(source)
            self.assertEqual(asset.read_bytes(), block["image"])
            self.assertEqual(asset.suffix, "." + block["ext"])
            self.assertNotIn("SMask", stderr)

    def test_missing_pillow_keeps_opaque_image_and_body(self):
        with tempfile.TemporaryDirectory() as directory:
            source, _, _, block = self._source(Path(directory))
            with patch.dict(sys.modules, {"PIL": None}):
                asset, stderr = self._convert(source)
            self.assertEqual(asset.read_bytes(), block["image"])
            self.assertIn("[WARN]", stderr)
            self.assertIn("keeping the opaque base image", stderr)
            self.assertIn("Install Pillow and rerun", stderr)

    def test_undecodable_mask_keeps_opaque_image_and_body(self):
        with tempfile.TemporaryDirectory() as directory:
            source, _, _, block = self._source(Path(directory))
            get_text = fitz.Page.get_text

            def corrupt_mask(page, *args, **kwargs):
                result = get_text(page, *args, **kwargs)
                if isinstance(result, dict):
                    for image in result.get("blocks", []):
                        if image["type"] == 1:
                            image["mask"] = b"invalid mask payload"
                return result

            with patch.object(fitz.Page, "get_text", corrupt_mask):
                asset, stderr = self._convert(source)
            self.assertEqual(asset.read_bytes(), block["image"])
            self.assertIn("[WARN]", stderr)
            self.assertIn("keeping the opaque base image", stderr)
            self.assertIn("Re-export the PDF with a valid grayscale mask", stderr)

    def test_different_masks_are_not_deduplicated(self):
        block = {"width": 200, "height": 150, "bbox": (10, 10, 70, 70),
                 "image": b"base" * 2500, "mask": b"first mask"}
        seen = set()
        page_rect = fitz.Rect(0, 0, 1000, 1000)
        self.assertTrue(pdf_to_md.should_keep_image(block, page_rect, seen))
        self.assertTrue(pdf_to_md.should_keep_image({**block, "mask": b"second mask"}, page_rect, seen))
        self.assertFalse(pdf_to_md.should_keep_image(block, page_rect, seen))
