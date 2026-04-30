import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import total_md_split


class TotalMdSplitImageCreditsTests(unittest.TestCase):
    def test_split_notes_preserves_existing_image_credits_from_exact_stem_note(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "notes"
            existing_note = output_dir / "01_cover.md"
            existing_note.parent.mkdir(parents=True, exist_ok=True)
            existing_note.write_text(
                "Old note text\n\nImage Credits\n- Credit one\n",
                encoding="utf-8",
            )

            success = total_md_split.split_notes(
                {"01_cover": "New note text"},
                output_dir,
                verbose=False,
            )

            content = existing_note.read_text(encoding="utf-8")

        self.assertTrue(success)
        self.assertEqual(content, "New note text\n\nImage Credits\n- Credit one\n")

    def test_split_notes_preserves_existing_image_credits_from_legacy_slide_note(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "notes"
            legacy_note = output_dir / "slide02.md"
            legacy_note.parent.mkdir(parents=True, exist_ok=True)
            legacy_note.write_text(
                "Legacy note text\n\nImage Credits\n- Legacy credit\n",
                encoding="utf-8",
            )

            success = total_md_split.split_notes(
                {"02_agenda": "Agenda note text"},
                output_dir,
                verbose=False,
            )

            rewritten_note = output_dir / "02_agenda.md"
            content = rewritten_note.read_text(encoding="utf-8")

        self.assertTrue(success)
        self.assertEqual(
            content,
            "Agenda note text\n\nImage Credits\n- Legacy credit\n",
        )


if __name__ == "__main__":
    unittest.main()
