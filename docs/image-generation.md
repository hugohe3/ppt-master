# AI Image Generation: Measured Behavior

[English](./image-generation.md) | [Chinese](./zh/image-generation.md)

---

PPT Master generates in-deck images through [`image_gen.py`](../skills/ppt-master/scripts/image_gen.py); configuration, flags, and backend options are documented in [`scripts/docs/image.md`](../skills/ppt-master/scripts/docs/image.md). This page records how the two recommended providers actually behaved when called on their official APIs, so you can pick sizes, quality levels, and prompts with known costs and failure modes.

- **OpenAI**: `gpt-image-2.5-sunburst` (the backend default) and `gpt-image-2.6-sunburst` / `gpt-image-2.6-flare`. Measured 2026-11-05 and 2026-11-08.
- **Gemini**: `gemini-nano-banana-2.1` (the backend default, `thinking_level=MINIMAL`), with `gemini-3-pro-image` as a comparison. Measured 2026-11-08.

Every number below is a single measurement at that date (costs are estimated from the `usage` block × the provider's published price). Providers change models and prices; recheck their pricing pages before relying on a figure.

## Pricing mechanics

### OpenAI: billed by output tokens, and tokens follow the short edge

Image output costs $30 per 1M tokens (same unit price for 2.5 and 2.6). The token count depends on size and quality:

| 16:9 size | low | medium | high | xhigh |
|---|---|---|---|---|
| 1280x720 | $0.014 | $0.025 | $0.029 | $0.051 |
| 1536x864 | $0.016 | $0.028 | $0.033 | $0.058 |
| 1920x1088 | $0.019 | $0.035 | $0.040 | $0.071 |
| 2560x1440 | $0.026 | $0.048 | $0.056 | $0.099 |
| 3840x2160 | $0.047 | $0.086 | $0.101 | $0.178 |

(gpt-image-2.6-sunburst; 2.5 produced identical token counts at `high`.)

- At a similar pixel count, tokens scale with the **short edge squared**: 1:1 (1152x1152) cost 1.8× a 16:9 image (1536x864); 3:1 (2016x672) cost 0.6×. Swapping landscape and portrait costs the same.
- Above 720p, tokens grow roughly linearly with the short edge: 3840x2160 has 6.25× the pixels of 1536x864 but ~3.1× the tokens.
- Quality multipliers relative to `high` stayed constant across sizes: low ≈ 0.47×, medium ≈ 0.86×, xhigh ≈ 1.78×.
- `max` is accepted (although error messages only list `low/medium/high/auto`) and cost $0.13 at 1536x864 and $0.21 at 1024x1024, about 4–7× `high`.
- At 2.6, `medium` uses 3.3× the tokens of 2.5 `medium` (924 vs 280 at 1536x864); at `high` the two are equal.

### Gemini: a fixed price per size tier

| Tier | 16:9 pixels | Image tokens | Cost | Time |
|---|---|---|---|---|
| 1K | 1376x768 | 1120 | $0.036 | 7–10 s |
| 2K | 2752x1536 | 1680 | $0.054 | 14–17 s |
| 4K | 5504x3072 | 3780 | $0.117 | 23–28 s |

- All 14 aspect ratios cost the same 1120 image tokens at 1K.
- Output is always JPEG; there is no transparent-background option.
- `thinking_level=HIGH` added 900–3100 thinking tokens ($0.046–0.063 per image, 28–38 s). `gemini-3-pro-image` used the same 1120 image tokens at 4× the unit price ($0.137–0.142 per image).

## Size and aspect-ratio constraints

| | OpenAI 2.5 / 2.6 | Gemini nano-banana-2.1 |
|---|---|---|
| Ratios | Any W:H up to 3:1; both edges multiples of 16 | 14 fixed values: 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9 |
| Pixel range | 655,360 – 8,294,400 total; long edge ≤ 3840 | 1K / 2K / 4K (512 is rejected for this model) |
| Common trap | `1920x1080` is rejected (1080 is not a multiple of 16); use `1920x1088` | — |

`image_gen.py` already fits any requested ratio to these rules, so these constraints matter only when calling the APIs directly.

Composition across ratios: OpenAI composed natively at all 11 tested ratios from 1:3 to 3:1. Gemini composed natively at 12 of 14; at **1:4 and 1:8 it tiled the same scene vertically** (3 and about 11 copies) instead of one tall picture, while 4:1 and 8:1 were single compositions.

Resolution: OpenAI `high` / `xhigh` at 3840x2160 contained real added detail at 100% zoom; `low` became visibly mushy at large sizes. Gemini 1K / 2K / 4K stayed clean.

## Text inside images

The same prompts were sent to both providers: 12 everyday cases (English slide, Chinese poster title, a 76-character Chinese paragraph, mixed CN/EN KPI cards, a bar chart with values, an 8-step flowchart, brush calligraphy, a 4×4 table, shop signage in a photo, vertical classical text, a whiteboard formula, a newspaper front page) and 10 stress cases (a 320-character two-paragraph text, rare characters, 12 bullets, a 9:16 poster, an 8×5 bilingual table, Traditional Chinese, a CN/EN/JA/KO sign, a 32-number financial table, a 10-node timeline, a tiny footnote).

| Case type | OpenAI (2.6 / 2.5) | Gemini (nano-banana-2.1) |
|---|---|---|
| Titles, labels, bullets, KPI numbers, tables, chart values, multi-script signs | All correct | All correct |
| Chinese paragraphs (76 and 320 characters) | All correct across 2.5, 2.6, medium/high/xhigh, 2560 and 3840 widths | 4 of 5 paragraph images had one added or dropped character (e.g. an extra 中 in 增长中中位数, a doubled 问 across a line break); the 4K version was correct |
| Small body text (newspaper columns, ~13 px) | Coherent, correct Chinese, also at 3840 | Pseudo-Chinese: real and invented glyphs, sentences that do not read — at 1K, 2K, 4K, with HIGH thinking, and with 3-pro-image |
| Vertical classical poem | 2.6 dropped one comma in 3 of 7 images; 2.5 wrote one wrong character | All correct |
| Rare characters (囹圄, 龃龉, 彧, place names such as 亳州 / 歙县) | Place names correct; low-frequency single characters weak (彧 wrong everywhere); some forced to Traditional forms | Place names correct; 囹圄 and 龃龉 wrong in every variant, including 3-pro-image |
| Total observed in the everyday set (60 OpenAI images) | 1 wrong character, 3 missing commas | — |

`medium` and `high` did not differ in text accuracy on OpenAI; they differed in layout polish.

## Editing an existing image (change the text, keep the rest)

Both providers took a slide or photo plus an instruction such as "change 210 to 260 and 中 to 低, keep everything else".

| | OpenAI `/images/edits` | Gemini (image + instruction) |
|---|---|---|
| Correct text changes | 16 of 16 (2.6 Sunburst and Flare, 8 cases) | 8 of 8 |
| Unchanged areas | Flat slides: mean pixel difference 1–3 (re-encode noise); photos: 5–8 (subtle full-image re-render, same composition) | Not directly comparable (1376-wide JPEG output resized for comparison); one case moved a headline from its original position; one bar was raised only slightly instead of to the new value |
| Cost / time | ≈ $0.046 (1296 input image tokens + ~1080 output), 26–35 s (Flare ~10 s) | ≈ $0.038, 9–11 s |
| Masks | **Broken on 2.5 and 2.6**: a mask (alpha 0 = editable) turned the masked area into a solid black rectangle in the output | No mask parameter |

Plain instruction edits without a mask were reliable on both; avoid the OpenAI mask parameter.

## Animated GIF

### OpenAI 2.6: native GIF output

`image_gen.py --gif-frames N [--gif-frame-ms MS]` requests a GIF from `gpt-image-2.6-*` (generation, or animating an existing image with `--reference-image`); see [`scripts/docs/image.md`](../skills/ppt-master/scripts/docs/image.md) for the flags. Measured facts:

- 2–16 frames; `frame_duration_ms` is honored (100–800 ms tested); default 200 ms, `loop=0`. 2.5 models reject GIF.
- The server renders all frames as one sprite sheet and slices it. Grids by frame count: 2–8 frames → 2×4 or 4×2 (always 8 cells), 9 → 3×3, 10–12 → 3×4 / 4×3 / 4×4, 13–16 → 4×4. The sheet must stay within 3840 px per edge and 8,294,400 px total.
- Cost is the token cost of that sheet: 9 frames at 1024x576 and 16 frames at 768x432 (both a 3072x1728 sheet) each cost ≈ $0.06 at `medium`. Because 2–8 frames always use 8 cells, fewer frames do not cost less at the same frame size.
- `background=transparent` works (a loading spinner came back with a real alpha channel).
- Worked well: rotation, spinners, waves, particles, a product turntable (one full 360° turn with consistent details), a static Chinese title under a moving light sweep (text identical in all 9 frames), step-by-step highlighting with fixed labels, bars growing to labeled values, a waving character that stayed on-model, and animating an existing slide (an arrow growing while all text stayed still).
- Failed: a 2-frame discrete state change (a traffic light dimmed the red lamp but never lit the green one).
- `low` made shapes wobble between frames; `high` cost 22% more than `medium` without a visible gain. Flare finished in about half the time of Sunburst but left a ghosted hand on the waving character.

### Gemini: no GIF output

Gemini returns still images only. Asking for a 3×3 sprite sheet and slicing it locally did not produce usable animation: the gear's nine cells were nearly identical, and the bar-chart cells were unequal in size, so equal slicing mixed neighboring cells into each frame.

## SVG output (OpenAI 2.6, not used by the pipeline)

`output_format=svg` works only with the undocumented field `svg: {"model": "<text model>"}` and `n=1`; it is text → SVG only (edits reject SVG, so an existing image cannot be converted). Each SVG cost about $0.06–0.09 (image step plus the text model writing the SVG, which `usage` does not report). PPT Master does not call this; bring your own SVG through the icon library if you need vector art.

## Raw material

Scripts, per-request logs, every generated image, and comparison sheets for these measurements live outside the repository in the maintainer's project workspace; the facts above are the distilled result.
