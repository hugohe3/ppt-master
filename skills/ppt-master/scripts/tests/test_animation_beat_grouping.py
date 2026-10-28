#!/usr/bin/env python3
"""Regress shared native beat wrappers and legacy timing-tree imports.

Usage:
    python3 -m unittest tests.test_animation_beat_grouping

Dependencies:
    The animation scripts' normal dependencies.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_animations import (  # noqa: E402
    create_sequence_timing_xml,
    read_slide_animation_sequence,
    validate_generated_animation_xml,
)
from pptx_to_svg.animation_import import read_animation_config  # noqa: E402

PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"p": PML_NS}
SVG = ('<svg xmlns="http://www.w3.org/2000/svg"><g id="content" '
       'data-pptx-shape-scope="slide" data-pptx-shape-id="2"/></svg>')


def _target(trigger: str, delay_ms: int = 0, duration: float = 0.2, **options: object) -> dict:
    return {"shape_id": 2, "effect": "entrance_fade", "duration": duration,
            "trigger": trigger, "delay_ms": delay_ms, **options}


def _slide(timing: str) -> str:
    return (f'<p:sld xmlns:p="{PML_NS}"><p:cSld><p:spTree>'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="content"/></p:nvSpPr></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="button"/></p:nvSpPr></p:sp>'
            f'</p:spTree></p:cSld>{timing}</p:sld>')


def _legacy_slide(rows: list[tuple[str, int, int]]) -> str:
    """Build the former per-row-wrapper fixture without invoking the writer.

    Each tuple supplies the native node type, wrapper offset, and leaf delay.
    The fade behavior is frozen from the pre-grouping output.
    """
    wrappers = []
    for index, (node_type, offset_ms, delay_ms) in enumerate(rows):
        wrapper_id = 4 + index * 4
        wrappers.append(f'''<p:par><p:cTn id="{wrapper_id}" fill="hold">
          <p:stCondLst><p:cond delay="{offset_ms}"/></p:stCondLst><p:childTnLst><p:par>
            <p:cTn id="{wrapper_id + 1}" presetID="10" presetClass="entr"
                   presetSubtype="0" fill="hold" grpId="0" nodeType="{node_type}">
              <p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst><p:childTnLst>
                <p:set><p:cBhvr><p:cTn id="{wrapper_id + 2}" dur="1" fill="hold">
                  <p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
                  <p:tgtEl><p:spTgt spid="2"/></p:tgtEl>
                  <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                </p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
                <p:animEffect transition="in" filter="fade"><p:cBhvr>
                  <p:cTn id="{wrapper_id + 3}" dur="500"/>
                  <p:tgtEl><p:spTgt spid="2"/></p:tgtEl>
                </p:cBhvr></p:animEffect>
              </p:childTnLst>
            </p:cTn>
          </p:par></p:childTnLst>
        </p:cTn></p:par>''')
    return _slide(f'''<p:timing><p:tnLst><p:par>
      <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
        <p:seq concurrent="1" nextAc="seek">
          <p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst><p:par>
            <p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>
              <p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>
            </p:stCondLst><p:childTnLst>{''.join(wrappers)}</p:childTnLst></p:cTn>
          </p:par></p:childTnLst></p:cTn>
          <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
          <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
        </p:seq>
      </p:childTnLst></p:cTn>
    </p:par></p:tnLst></p:timing>''')


class AnimationBeatGroupingTests(unittest.TestCase):
    def _assert_layout(self, targets: list[dict], offsets: list[int],
                       layout: list[list[list[int]]]) -> str:
        slide = _slide(create_sequence_timing_xml(targets))
        summary = read_slide_animation_sequence(slide, require_supported_effects=True)
        self.assertEqual([row.offset_ms for row in summary.rows], offsets)
        validate_generated_animation_xml(slide, targets)
        root = ET.fromstring(slide)
        main = root.find('.//p:cTn[@nodeType="mainSeq"]', NS)
        rows = [row for row in main.iter(f"{{{PML_NS}}}cTn") if row.get("presetClass")]
        row_indices = {row: index for index, row in enumerate(rows)}
        actual = []
        for group in main.findall("p:childTnLst/p:par/p:cTn", NS):
            beats = []
            for beat in group.findall("p:childTnLst/p:par/p:cTn", NS):
                beats.append([row_indices[row] for row in beat.findall("p:childTnLst/p:par/p:cTn", NS)])
            actual.append(beats)
        self.assertEqual(actual, layout)
        return slide

    def test_issue_331_keeps_offsets_and_shares_zoom_beat(self) -> None:
        self._assert_layout([
            _target("after-previous", duration=0.75),
            _target("after-previous", duration=0.28, effect="entrance_zoom",
                    effect_options={"direction": "out"}, accelerate=1),
            _target("with-previous", duration=0.12),
            _target("after-previous", duration=0.09, effect="emphasis_grow_shrink",
                    effect_options={"size": 110}, auto_reverse=True),
        ], [0, 750, 750, 1030], [[[0], [1, 2], [3]]])

    def test_mixed_click_groups_and_out_of_order_delays(self) -> None:
        self._assert_layout([
            _target("after-previous", duration=2),
            _target("with-previous", 2000, 0.1),
            _target("after-previous", 100),
            _target("with-previous", 50, 0.1),
            _target("on-click", 400, 0.3),
            _target("with-previous", 100),
            _target("after-previous", 20),
            _target("with-previous", 0, 0.1),
        ], [0, 2000, 2200, 2150, 400, 100, 720, 700],
            [[[0, 1], [2, 3]], [[4, 5], [6, 7]]])

    def test_equal_offsets_do_not_merge_separate_click_beats(self) -> None:
        self._assert_layout([
            _target("with-previous"), _target("with-previous"),
            _target("on-click"), _target("with-previous"),
            _target("on-click"), _target("with-previous"),
        ], [0] * 6, [[[0, 1]], [[2, 3]], [[4, 5]]])

    def test_uniform_modes_use_the_same_beat_structure(self) -> None:
        cases = [
            ("with-previous", [0, 0, 0], [0, 0, 0], [[[0, 1, 2]]]),
            ("with-previous", [450, 450, 450], [450, 450, 450], [[[0, 1, 2]]]),
            ("with-previous", [100, 200, 50], [100, 200, 50], [[[0, 1, 2]]]),
            ("after-previous", [100, 200, 50], [100, 500, 750], [[[0], [1], [2]]]),
            ("on-click", [100, 200, 50], [100, 200, 50], [[[0]], [[1]], [[2]]]),
        ]
        for trigger, delays, offsets, layout in cases:
            with self.subTest(trigger=trigger, delays=delays):
                self._assert_layout([_target(trigger, delay) for delay in delays], offsets, layout)

    def test_interactive_rows_stay_outside_shared_main_beats(self) -> None:
        slide = self._assert_layout([
            _target("on-click", 400, 5, trigger_shape_id=3),
            _target("after-previous", 100), _target("with-previous", 50),
            _target("after-previous", 20),
        ], [100, 50, 320, 400], [[[0, 1], [2]]])
        root = ET.fromstring(slide)
        interactive = root.findall('.//p:cTn[@nodeType="interactiveSeq"]', NS)
        self.assertEqual(len(interactive), 1)
        self.assertEqual(sum(row.get("presetClass") is not None
                             for row in interactive[0].iter(f"{{{PML_NS}}}cTn")), 1)

    def test_legacy_per_row_wrappers_still_read_import_and_reexport(self) -> None:
        cases = [
            ([('afterEffect', 0, 0), ('afterEffect', 500, 500),
              ('withEffect', 500, 200), ('withEffect', 500, 0), ('afterEffect', 1500, 500)],
             [0, 1000, 700, 500, 2000], [[[0], [1, 2, 3], [4]]]),
            ([('withEffect', 0, 450), ('withEffect', 0, 450), ('withEffect', 0, 100)],
             [450, 450, 100], [[[0, 1, 2]]]),
        ]
        for rows, offsets, layout in cases:
            with self.subTest(rows=rows):
                legacy = _legacy_slide(rows)
                summary = read_slide_animation_sequence(legacy, require_supported_effects=True)
                self.assertEqual([row.offset_ms for row in summary.rows], offsets)
                effects = read_animation_config(legacy, SVG).groups["content"]["effects"]
                self.assertEqual([round(row["delay"] * 1000) for row in effects],
                                 [delay for _, _, delay in rows])
                targets = [
                    {key: value for key, value in row.items() if key not in {"delay", "order"}}
                    | {"shape_id": 2, "delay_ms": round(row["delay"] * 1000)}
                    for row in effects
                ]
                validate_generated_animation_xml(legacy, targets)
                rebuilt = self._assert_layout(targets, offsets, layout)
                self.assertEqual(read_slide_animation_sequence(rebuilt), summary)
                self.assertEqual(read_animation_config(rebuilt, SVG).groups,
                                 read_animation_config(legacy, SVG).groups)
