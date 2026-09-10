#!/usr/bin/env python3
"""Exercise MiniMax original-text subtitle spans through audio generation.

Usage:
    python3 -m unittest tests.test_minimax_subtitles

Dependencies:
    None (only uses standard library).
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tts_backends import backend_minimax


class MiniMaxSubtitleTests(unittest.TestCase):
    def generate(self, text: str, words: list[dict], directory: Path) -> None:
        response = {
            "base_resp": {"status_code": 0},
            "data": {
                "audio": b"mock-audio".hex(),
                "subtitle_file": "https://example.invalid/subtitles.json",
            },
        }
        subtitle = json.dumps([{"timestamped_words": words}]).encode("utf-8")
        with (
            patch.object(backend_minimax, "post_json", return_value=response),
            patch.object(backend_minimax, "get_bytes", return_value=subtitle),
        ):
            backend_minimax.generate(
                text, directory / "page.mp3",
                api_key="test-key", voice_id="test-voice", model="speech-2.8-hd",
                audio_format="mp3", sample_rate=32000, bitrate=128000, channel=1,
                speed=1.0, volume=1.0, pitch=0, language_boost="auto", base_url=None,
                subtitle_path=directory / "page.srt",
            )

    def test_spoken_number_parts_keep_one_original_token_and_full_duration(self):
        words = [
            {"word": "第", "word_begin": 0, "word_end": 1, "time_begin": 0, "time_end": 100},
            {"word": "42", "word_begin": 1, "word_end": 3, "time_begin": 100, "time_end": 200},
            {"word": "42", "word_begin": 1, "word_end": 3, "time_begin": 200, "time_end": 300},
            {"word": "42", "word_begin": 1, "word_end": 3, "time_begin": 300, "time_end": 450},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.generate("第42。", words, directory)
            self.assertEqual((directory / "page.mp3").read_bytes(), b"mock-audio")
            self.assertEqual(
                (directory / "page.srt").read_text(encoding="utf-8"),
                "1\n00:00:00,000 --> 00:00:00,450\n第42。\n",
            )

    def test_repeated_words_at_distinct_positions_are_preserved(self):
        words = [
            {"word": "42", "word_begin": 0, "word_end": 2, "time_begin": 0, "time_end": 100},
            {"word": "42", "word_begin": 3, "word_end": 5, "time_begin": 100, "time_end": 200},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.generate("42，42。", words, directory)
            self.assertIn("42，42。", (directory / "page.srt").read_text(encoding="utf-8"))

    def test_missing_or_invalid_spans_do_not_hide_text_mismatches(self):
        for span in (None, (-1, 2), (0, 0), ("0", "2"), (False, 2)):
            with self.subTest(span=span), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                (directory / "page.mp3").write_bytes(b"previous-audio")
                (directory / "page.srt").write_text("previous-subtitles", encoding="utf-8")
                words = [
                    {"word": "42", "time_begin": 0, "time_end": 100},
                    {"word": "42", "time_begin": 100, "time_end": 200},
                ]
                if span is not None:
                    for word in words:
                        word.update(word_begin=span[0], word_end=span[1])
                with self.assertRaisesRegex(RuntimeError, "could not be aligned"):
                    self.generate("42。", words, directory)
                self.assertEqual((directory / "page.mp3").read_bytes(), b"previous-audio")
                self.assertEqual(
                    (directory / "page.srt").read_text(encoding="utf-8"), "previous-subtitles"
                )

    def test_merged_number_still_rejects_backwards_word_times(self):
        words = [
            {"word": "42", "word_begin": 0, "word_end": 2, "time_begin": 0, "time_end": 100},
            {"word": "42", "word_begin": 0, "word_end": 2, "time_begin": 100, "time_end": 200},
            {"word": "42", "word_begin": 0, "word_end": 2, "time_begin": 50, "time_end": 150},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "not in chronological order"):
                self.generate("42。", words, Path(temporary))
