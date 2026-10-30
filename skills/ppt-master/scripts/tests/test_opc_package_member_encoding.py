import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pptx_opc_validation import canonical_package_member_path, verify_internal_relationships
from video_sound_mix import _package_part_map


class PackageMemberOpcTests(unittest.TestCase):
    def test_verify_internal_relationships_resolves_space_encoded_media(self):
        with tempfile.TemporaryDirectory() as directory:
            extract_dir = Path(directory)
            media_dir = extract_dir / "ppt" / "media"
            media_dir.mkdir(parents=True)
            (media_dir / "image 1.png").write_bytes(b"test-png")

            slides_dir = extract_dir / "ppt" / "slides"
            slides_dir.mkdir(parents=True)
            (slides_dir / "slide1.xml").write_text("<p:sld/>", encoding="utf-8")

            rels_dir = slides_dir / "_rels"
            rels_dir.mkdir(parents=True)
            (rels_dir / "slide1.xml.rels").write_text(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                '  <Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                'Target="../media/image%201.png"/>\n'
                "</Relationships>",
                encoding="utf-8",
            )
            self.assertEqual(verify_internal_relationships(extract_dir), [])

    def test_canonical_package_member_path_encodes_spaces(self):
        self.assertEqual(
            canonical_package_member_path("ppt/media/image 1.png"),
            "ppt/media/image%201.png",
        )
        self.assertEqual(
            canonical_package_member_path("ppt/media/image1.png"),
            "ppt/media/image1.png",
        )

    def test_package_part_map_indexes_space_named_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "test.pptx"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("ppt/media/audio 1.wav", b"audio-bytes")
            with zipfile.ZipFile(archive_path, "r") as archive:
                mapping = _package_part_map(archive)
                self.assertIn("ppt/media/audio%201.wav", mapping)
                self.assertEqual(mapping["ppt/media/audio%201.wav"], "ppt/media/audio 1.wav")
