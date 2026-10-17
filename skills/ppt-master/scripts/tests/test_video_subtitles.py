#!/usr/bin/env python3
"""Unit tests for video_subtitles.py cue splitting and clause merging."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import video_subtitles  # noqa: E402


PAGE_SRT = """1
00:00:00,000 --> 00:00:04,000
We plan, we build, we ship.

2
00:00:04,000 --> 00:00:08,000
Design first, then measure, then iterate.
"""


class ClauseMergeTests(unittest.TestCase):
    def test_merged_clauses_keep_the_space_that_separated_them(self) -> None:
        self.assertEqual(
            video_subtitles._split_sentence("We plan, we build, we ship.", 20),
            ["We plan, we build,", "we ship."],
        )
        self.assertEqual(
            video_subtitles._split_sentence(
                "Alpha, beta, gamma, delta and epsilon.", 20
            ),
            ["Alpha, beta, gamma,", "delta and epsilon."],
        )

    def test_cjk_clauses_merge_without_inventing_a_space(self) -> None:
        self.assertEqual(
            video_subtitles._split_sentence(
                "第一步是调研，第二步是设计，第三步是交付。", 20
            ),
            ["第一步是调研，第二步是设计，", "第三步是交付。"],
        )

    def test_short_sentence_is_returned_unsplit(self) -> None:
        self.assertEqual(
            video_subtitles._split_sentence("We ship, we learn.", 20),
            ["We ship, we learn."],
        )

    def test_every_cue_is_a_trimmed_slice_within_the_character_budget(self) -> None:
        sentences = (
            "We plan, we build, we ship.",
            "Design first, then measure, then iterate on the result.",
            "Alpha, beta, gamma, delta and epsilon.",
            "第一步是调研，第二步是设计，第三步是交付。",
            "One extraordinarily long unbreakable token: supercalifragilistic.",
        )
        for max_chars in (3, 8, 20):
            for sentence in sentences:
                lines = video_subtitles._split_sentence(sentence, max_chars)
                with self.subTest(sentence=sentence, max_chars=max_chars):
                    self.assertTrue(lines)
                    for line in lines:
                        self.assertIn(line, " ".join(sentence.split()))
                        self.assertEqual(line, line.strip())
                        self.assertLessEqual(
                            sum(not c.isspace() for c in line), max_chars
                        )
                    self.assertEqual(
                        "".join(c for line in lines for c in line if not c.isspace()),
                        "".join(c for c in sentence if not c.isspace()),
                    )


class FrozenTranscriptTests(unittest.TestCase):
    def test_page_local_srt_text_reaches_the_transcript_with_its_spacing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subtitle_dir = Path(tmp) / "audio"
            subtitle_dir.mkdir()
            (subtitle_dir / "01-cover.srt").write_text(PAGE_SRT, encoding="utf-8")
            self.assertEqual(
                video_subtitles._frozen_transcript_lines(subtitle_dir, 20),
                [
                    "We plan, we build,",
                    "we ship.",
                    "Design first,",
                    "then measure,",
                    "then iterate.",
                ],
            )


class PageSubtitleOrderTests(unittest.TestCase):
    def test_page_srts_follow_numeric_slide_order(self) -> None:
        import narration_sync

        with tempfile.TemporaryDirectory() as tmp:
            for stem in ("slide_9", "slide_10", "slide_100", "slide_11", "total"):
                Path(tmp, f"{stem}.srt").write_text(
                    "1\n00:00:00,000 --> 00:00:01,000\nx\n", encoding="utf-8"
                )
            expected = ["slide_9", "slide_10", "slide_11", "slide_100"]
            self.assertEqual(
                [path.stem for path in video_subtitles._page_subtitle_paths(Path(tmp))], expected
            )
            self.assertEqual(narration_sync._page_subtitle_names(Path(tmp)), expected)
