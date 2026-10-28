#!/usr/bin/env python3
"""Regress mixed PowerPoint beats through timing, import, and narration.

Usage:
    python3 -m unittest tests.test_animation_beat_timing

Dependencies:
    The animation and narration scripts' normal dependencies.
"""

from __future__ import annotations

import io
import json
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from narration_sync import rebuild_animations  # noqa: E402
from pptx_animations import (  # noqa: E402
    create_sequence_timing_xml,
    read_slide_animation_sequence,
    validate_generated_animation_xml,
)
from pptx_to_svg.animation_import import read_animation_config  # noqa: E402
from svg_to_pptx.pptx_package.builder import _build_sequence_targets  # noqa: E402

PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"p": PML_NS}


def _target(duration: float, trigger: str = "after-previous", delay_ms: int = 0,
            **options: object) -> dict:
    return {"shape_id": 2, "effect": "entrance_fade", "duration": duration,
            "trigger": trigger, "delay_ms": delay_ms, **options}


def _issue_targets() -> list[dict]:
    return [
        _target(0.75),
        _target(0.28, effect="entrance_zoom", effect_options={"direction": "out"}, accelerate=1),
        _target(0.12, "with-previous"),
        _target(0.09, effect="emphasis_grow_shrink", effect_options={"size": 110}, auto_reverse=True),
    ]


def _slide(targets: list[dict]) -> str:
    timing = create_sequence_timing_xml(targets)
    shape_ids = {target["shape_id"] for target in targets}
    shape_ids.update(target["trigger_shape_id"] for target in targets if "trigger_shape_id" in target)
    shapes = "".join(f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="item"/>'
                     '</p:nvSpPr></p:sp>' for shape_id in sorted(shape_ids))
    return (f'<p:sld xmlns:p="{PML_NS}"><p:cSld><p:spTree>{shapes}'
            f'</p:spTree></p:cSld>{timing}</p:sld>')


class AnimationBeatTimingTests(unittest.TestCase):
    def _assert_offsets(self, targets: list[dict], expected: list[int]) -> str:
        slide = _slide(targets)
        summary = read_slide_animation_sequence(slide, require_supported_effects=True)
        self.assertEqual([row.offset_ms for row in summary.rows], expected)
        validate_generated_animation_xml(slide, targets)
        return slide

    def test_after_previous_waits_for_issue_331_zoom(self) -> None:
        slide = self._assert_offsets(_issue_targets(), [0, 750, 750, 1030])
        rows = read_slide_animation_sequence(slide).rows
        self.assertEqual(max(row.offset_ms + row.playback_duration_ms for row in rows), 1210)

    def test_each_with_previous_delay_uses_beat_start(self) -> None:
        self._assert_offsets([
            _target(0.2, delay_ms=100),
            _target(0.1, "with-previous", 200),
            _target(0.1, "with-previous", 50),
            _target(0.1, delay_ms=20),
        ], [100, 200, 50, 320])

    def test_long_parallel_playback_includes_repeat_and_reverse(self) -> None:
        for modifiers, end_ms in (({"repeat_count": 3, "auto_reverse": True}, 1200),
                                  ({"repeat_duration": 1.4, "auto_reverse": True}, 1400)):
            with self.subTest(modifiers=modifiers):
                self._assert_offsets([
                    _target(0.1), _target(0.2, "with-previous", **modifiers),
                    _target(0.05, "with-previous"), _target(0.1, delay_ms=30),
                ], [0, 0, 0, end_ms + 30])

    def test_click_resets_beat_and_interactive_rows_do_not_extend_it(self) -> None:
        self._assert_offsets([
            _target(2), _target(0.2, "on-click", 100),
            _target(0.1, "with-previous", 50), _target(0.1),
            _target(5, "on-click", 70, trigger_shape_id=3),
        ], [0, 100, 50, 300, 70])

    def test_uniform_start_modes_remain_consistent(self) -> None:
        for trigger, expected in (("after-previous", [100, 500, 750]),
                                  ("with-previous", [100, 200, 50])):
            with self.subTest(trigger=trigger):
                self._assert_offsets([_target(0.2, trigger, delay) for delay in (100, 200, 50)], expected)

    def test_verifier_rejects_old_early_after_previous_offset(self) -> None:
        targets = _issue_targets()
        root = ET.fromstring(_slide(targets))
        row = root.find('.//p:cTn[@presetClass="emph"]', NS)
        parent = {child: node for node in root.iter() for child in node}
        wrapper = parent[parent[parent[row]]]
        wrapper.find("p:stCondLst/p:cond", NS).set("delay", "870")
        with self.assertRaisesRegex(ValueError, "offset"):
            validate_generated_animation_xml(ET.tostring(root), targets)

    def test_import_preserves_parallel_delays_and_reexports_offsets(self) -> None:
        targets = [
            _target(0.75), _target(0.28, delay_ms=100),
            _target(0.12, "with-previous", 200),
            _target(0.05, "with-previous", 50), _target(0.09),
        ]
        svg = ('<svg xmlns="http://www.w3.org/2000/svg"><g id="content" '
               'data-pptx-shape-scope="slide" data-pptx-shape-id="2"/></svg>')
        imported = read_animation_config(_slide(targets), svg)
        effects = imported.groups["content"]["effects"]
        self.assertEqual([row["delay"] for row in effects], [0, 0.1, 0.2, 0.05, 0])
        rebuilt = [
            {key: value for key, value in row.items() if key not in {"delay", "order"}}
            | {"shape_id": 2, "delay_ms": round(row["delay"] * 1000)} for row in effects
        ]
        self._assert_offsets(rebuilt, [0, 850, 950, 800, 1130])

    def _narration(self, targets: list[dict], audio_duration: float,
                   *, following_cue: bool = False, cue_start: str = "00:00:00,000") -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            effects = [{key: value for key, value in target.items() if key not in {"shape_id", "delay_ms"}}
                       | {"delay": target["delay_ms"] / 1000, "order": 1} for target in targets]
            groups = {"content": {"effects": effects}}
            if following_cue:
                groups["next"] = {"effect": "entrance_fade", "duration": 0.1, "order": 2}
            canonical = {"defaults": {"animation": {"effect": "none", "stagger": 0},
                                      "transition": {"effect": "none"}},
                         "slides": {"slide": {"groups": groups}}}
            source = root / "animations.json"
            source.write_text(json.dumps(canonical), encoding="utf-8")
            subtitles = f"1\n{cue_start} --> 00:00:00,200\nFirst\n\n"
            if following_cue:
                subtitles += "2\n00:00:01,500 --> 00:00:01,700\nNext\n"
            (root / "slide.srt").write_text(subtitles, encoding="utf-8")
            (root / "slide.wav").write_bytes(b"")
            output = root / "derived.json"
            with patch("narration_sync.probe_audio_duration", return_value=audio_duration), \
                    redirect_stderr(io.StringIO()):
                rebuild_animations(root, canonical_path=source, plan_path=root / "missing-plan.json",
                                   subtitle_dir=root, audio_dir=root, output_path=output,
                                   narration_padding=0, narration_start_floor=0, force=False)
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), canonical)
            return json.loads(output.read_text(encoding="utf-8"))["slides"]["slide"]["groups"]

    def test_narration_cue_delay_uses_complete_preceding_beat(self) -> None:
        groups = self._narration(_issue_targets(), 2, following_cue=True)
        self.assertEqual(groups["next"]["delay"], 0.29)

    def test_narration_rejects_advance_before_complete_beat(self) -> None:
        with self.assertRaisesRegex(ValueError, "end at 1.210s.*advance at 1.100s"):
            self._narration(_issue_targets(), 1.1)

    def test_narration_nonzero_with_delays_do_not_accumulate(self) -> None:
        groups = self._narration([
            _target(0.3), _target(0.1, "with-previous", 200),
            _target(0.1, "with-previous", 50), _target(0.1),
        ], 0.52, cue_start="00:00:00,100")
        self.assertEqual([row["delay"] for row in groups["content"]["effects"]], [0.1, 0.2, 0.05, 0])

    def _sidecar_targets(self, groups: dict) -> list[dict]:
        anim_targets = [(index + 2, group_id) for index, group_id in enumerate(groups)]
        targets, _ = _build_sequence_targets(
            anim_targets, "slide", {"groups": groups}, None,
            {"trigger": "after-previous"}, 0.5, 0.5, 0, random.Random(0),
        )
        return targets

    def _staggered_groups(self) -> dict:
        return {
            "images": {"effect": "entrance_fade", "order": 1},
            "bracket": {"effect": "entrance_wipe", "order": 2},
            "legend": {"effect": "entrance_fade", "order": 2, "trigger": "with-previous"},
            "note": {"effect": "entrance_fade", "order": 3, "trigger": "with-previous", "delay": 0.2},
        }

    def test_builder_omitted_with_previous_delay_equals_explicit_zero(self) -> None:
        groups = self._staggered_groups()
        omitted = self._sidecar_targets(groups)
        groups["legend"]["delay"] = 0
        explicit_zero = self._sidecar_targets(groups)
        self.assertEqual(omitted, explicit_zero)
        self.assertEqual([target["delay_ms"] for target in omitted], [0, 500, 0, 200])
        self._assert_offsets(omitted, [0, 1000, 500, 700])

    def test_companion_repeating_leader_delay_starts_together(self) -> None:
        groups = self._staggered_groups()
        groups["legend"]["delay"] = 0.5
        targets = self._sidecar_targets(groups)
        self._assert_offsets(targets, [0, 1000, 1000, 700])

    def test_later_row_with_smaller_delay_starts_before_previous_row(self) -> None:
        groups = self._staggered_groups()
        groups["legend"]["delay"] = 0.2
        groups["note"]["delay"] = 0.05
        slide = self._assert_offsets(self._sidecar_targets(groups), [0, 1000, 700, 550])
        rows = read_slide_animation_sequence(slide).rows
        self.assertEqual([row.shape_id for row in rows], [2, 3, 4, 5])
        self.assertLess(rows[-1].offset_ms, rows[-2].offset_ms)

    def test_builder_delays_roundtrip_through_animation_import(self) -> None:
        for companion_delay in (None, 0, 0.5, 0.7):
            with self.subTest(companion_delay=companion_delay):
                groups = self._staggered_groups()
                if companion_delay is not None:
                    groups["legend"]["delay"] = companion_delay
                targets = self._sidecar_targets(groups)
                expected = [0, 1000, 500 + round((companion_delay or 0) * 1000), 700]
                slide = self._assert_offsets(targets, expected)
                svg_groups = "".join(
                    f'<g id="{group_id}" data-pptx-shape-scope="slide" '
                    f'data-pptx-shape-id="{index + 2}"/>'
                    for index, group_id in enumerate(groups)
                )
                imported = read_animation_config(
                    slide, f'<svg xmlns="http://www.w3.org/2000/svg">{svg_groups}</svg>',
                )
                self.assertEqual(imported.groups["legend"]["delay"], companion_delay or 0)
                self._assert_offsets(self._sidecar_targets(imported.groups), expected)

    def test_narration_beat_delays_agree_with_exporter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical = {"defaults": {"animation": {"effect": "none", "stagger": 0.5},
                                      "transition": {"effect": "none"}},
                         "slides": {"slide": {"groups": {"content": {"effects": [
                             {"effect": "entrance_fade", "duration": 0.5},
                             {"effect": "entrance_wipe", "duration": 0.5},
                             {"effect": "entrance_fade", "duration": 0.5, "trigger": "with-previous"},
                             {"effect": "entrance_fade", "duration": 0.5,
                              "trigger": "with-previous", "delay": 0},
                             {"effect": "entrance_fade", "duration": 0.5,
                              "trigger": "with-previous", "delay": 0.5},
                             {"effect": "entrance_fade", "duration": 0.5,
                              "trigger": "with-previous", "delay": 0.2},
                         ]}}}}}
            source = root / "animations.json"
            source.write_text(json.dumps(canonical), encoding="utf-8")
            (root / "slide.srt").write_text("1\n00:00:00,000 --> 00:00:00,200\nFirst\n",
                                            encoding="utf-8")
            (root / "slide.wav").write_bytes(b"")
            output = root / "derived.json"
            with patch("narration_sync.probe_audio_duration", return_value=3), \
                    redirect_stderr(io.StringIO()):
                rebuild_animations(root, canonical_path=source, plan_path=root / "missing-plan.json",
                                   subtitle_dir=root, audio_dir=root, output_path=output,
                                   narration_padding=0, narration_start_floor=0, force=False)
            derived_groups = json.loads(output.read_text(encoding="utf-8"))["slides"]["slide"]["groups"]
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), canonical)
        effects = derived_groups["content"]["effects"]
        self.assertEqual([row["delay"] for row in effects], [0, 0.5, 0, 0, 0.5, 0.2])
        expected = [0, 1000, 500, 500, 1000, 700]
        self._assert_offsets(self._sidecar_targets(canonical["slides"]["slide"]["groups"]), expected)
        self._assert_offsets(self._sidecar_targets(derived_groups), expected)
