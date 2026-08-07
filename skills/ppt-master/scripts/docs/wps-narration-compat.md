# WPS Narration Compatibility (`wps_narration_compat.py`)

Converts an already-exported narrated PPTX into a WPS-compatible copy whose
narration auto-plays on slide entry, before all other effects.

## Why this exists

The Generate pipeline embeds per-slide narration in the PowerPoint
recorded-narration form: a hidden audio picture shape with
`ppaction://media` plus a trailing `p:audio` media node in the slide's
`p:timing`. PowerPoint starts that narration with the slide. WPS does not
recognize the implicit trigger — it leaves the narration unplayed and, when
set manually, places it after all animations.

WPS plays narration only when the timing tree carries an explicit
`mediacall` playFrom(0.0) effect as the **first row inside the main
sequence's delay=0 container par** — the exact serialization WPS's own
animation editor writes. This script rewrites each narrated slide's
`p:timing` into that verified shape and copies every other package part
byte-identically, so the PowerPoint-native export stays untouched.

## Usage

```bash
python3 skills/ppt-master/scripts/wps_narration_compat.py <narrated.pptx>
python3 skills/ppt-master/scripts/wps_narration_compat.py <narrated.pptx> -o out.pptx
python3 skills/ppt-master/scripts/wps_narration_compat.py <narrated.pptx> --overwrite
```

The default output is `<input stem>-wps.pptx` in the same directory; an
existing output file requires `--overwrite`. The script never modifies the
input file.

## Per-slide behavior

| Slide state | Result |
|---|---|
| Narration audio present, animation sequence exists | Effect rows are collected inside the delay=0 container (sibling rows move in, preserving order), and the `mediacall` row is inserted first. New timing node ids are appended after the tree's maximum, never renumbered. |
| Narration audio present, no animation sequence | A minimal main sequence (seq + mainSeq + delay=0 container) is synthesized around the `mediacall` row, keeping the trailing `p:audio` node. |
| Narration audio absent | Slide is left byte-identical. |
| `mediacall` row already present (idempotent re-run) | Slide is left byte-identical. |

## Output verification

- Only `ppt/slides/slideN.xml` parts change; every other package entry is
  byte-identical to the input.
- Each processed slide's `p:cTn@id` values stay unique across the whole
  timing tree.
- The `mediacall` `p:spTgt` targets the same shape id as the slide's
  `p:audio` media node.

## When to run

- Generate PPTX: after `generate-audio` Step 4 embeds narration, when the
  Stage-1 `WPS Compatibility` outcome in `design_spec.md §I` is enabled.
- Quick Generate: when the request or active-context decision explicitly
  asks for WPS-compatible narration playback.
- Manual: on any narrated PPTX that must auto-play in WPS.
