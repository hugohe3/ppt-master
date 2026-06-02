---
description: PPTX template fill workflow — use a native PowerPoint template deck, select fitting pages, and fill new material back without SVG conversion
---

# Template Fill (PPTX) Workflow

> Run when the user wants to fill new content into an existing deck. Typical requests include "fill this deck with the new content", "fill this back into the template", or "reuse this deck's design". They provide an existing `.pptx` as a native template deck plus topic / text materials and want the content filled back into that deck's design while selecting only the pages that fit the new story (a source page may be reused for several output slides).

This workflow is **independent** from the SVG generation pipeline. It treats the source PPTX as a native template / slide library, keeps the original PowerPoint design intact, and writes a new `.pptx` by cloning selected source slides and replacing text directly in OOXML.

## When to Run

Recognize any request that combines an existing PowerPoint with new content or a topic, for example:

| Pattern | Example |
|---|---|
| Existing `.pptx` + "fill back" intent | "Use this deck and fill in the attached material" |
| Existing `.pptx` + topic reuse | "Rework this PPTX around the new topic" |
| Existing `.pptx` + selective reuse | "Do not keep every page; only use the slides that fit" |
| Existing `.pptx` + copywriting replacement | "Keep the original design and replace the copy with this text" |
| Native PPT template fill | "Use this PowerPoint template for this content" |
| Direct wording | "Fill this deck with the new content" |

**Hard rule**: Do not run `pptx_to_svg.py`, `pptx_template_import.py`, `finalize_svg.py`, or `svg_to_pptx.py` for this workflow. SVG conversion is for presentation generation / template creation; this workflow is direct PowerPoint editing.

---

## Step 1: Inputs

🚧 **GATE**: The user has provided:

| Input | Required | Notes |
|---|---:|---|
| Source PPTX | Yes | Original design deck to reuse as a slide library |
| Content material | Yes | User text, Markdown, document, URL-derived source, or a clear topic brief |
| Target output intent | Optional | Audience, page count, tone, must-keep pages, must-drop pages |

If the content material is only a topic with no supporting facts, gather or ask for source material first. Do not invent detailed factual content.

---

## Step 2: Create the Project Workspace

Create a dedicated project directory under `projects/`. Do not write outputs directly into `projects/` root.

```bash
mkdir -p "<project_dir>/sources" "<project_dir>/analysis" "<project_dir>/exports" "<project_dir>/validation"
```

Use this fixed layout:

| Path | Required content |
|---|---|
| `<project_dir>/sources/` | Source PPTX and user-provided text / Markdown / converted materials |
| `<project_dir>/analysis/` | Slide library JSON, page-selection reasoning, and final fill plan |
| `<project_dir>/exports/` | Final generated PPTX only |
| `<project_dir>/validation/` | Read-back Markdown, extracted validation assets, and validation notes |

**Hard rule**: A template-fill project is a project, not a loose output file. The final answer must point to `<project_dir>/exports/<name>.pptx`, and all intermediate artifacts must remain inside `<project_dir>`.

---

## Step 3: Extract the Slide Library

Run:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py analyze "<project_dir>/sources/<source.pptx>" -o "<project_dir>/analysis/slide_library.json"
```

Read `<project_dir>/analysis/slide_library.json` and identify:

| Field | Use |
|---|---|
| `slides[].page_type` | Cover / chapter / content / ending candidate |
| `slides[].text_summary` | Current semantic purpose of the source page |
| `slides[].slots[]` | Replaceable text slots with `slot_id`, `role`, `geometry`, paragraph count, and old text |
| `slides[].slots[].role` | Title / body / label candidate hint |
| `slides[].tables[]` | Native PowerPoint tables with `table_id`, row / column counts, and per-cell coordinates + text |
| `slides[].charts[]` | Native PowerPoint charts with `chart_id` |

**Selection rule**: Pick pages by content fitness, not by source order alone. A source page is useful only if its visible structure can carry the target message without heavy redesign.

A page's layout already encodes a rhetorical shape — a single hero statement, a lead-then-detail split, a 2×2 comparison, a stepwise progression, a metric row. Match the source material's own logic to a page whose structure expresses that same logic; do not pour unrelated content into a slot just because it is empty. When no selected page fits a piece of content well, drop that page or that content rather than forcing it — a forced fill reads as stiff. It is fine to use fewer pages than the source deck has.

---

## Step 4: Build the Fill Plan

Create a scaffold:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py scaffold "<project_dir>/analysis/slide_library.json" -o "<project_dir>/analysis/fill_plan.json" --slides "1,3,4"
```

Then edit `<project_dir>/analysis/fill_plan.json` by hand from the source material. The plan is the single execution contract.

**Pages are reusable**: the output is the ordered `slides` list, not a one-to-one copy of the source deck. A source page is not single-use — list the same `source_slide` as many times as you need, each entry with its own `replacements`, to drive several output slides from one good layout (e.g., reuse a single content layout for five content pages). Likewise you may omit source pages entirely and put the selected ones in any order. The plan structure:

```json
{
  "schema": "template_fill_pptx_plan.v1",
  "source_pptx": "projects/source.pptx",
  "slides": [
    {
      "source_slide": 1,
      "purpose": "cover",
      "notes": "Speaker notes for this filled slide.",
      "transition": "fade",
      "replacements": [
        {
          "slot_id": "s01_sh4",
          "text": "New title"
        }
      ],
      "table_edits": [
        {
          "table_id": "s01_tbl3",
          "cells": [
            {"row": 0, "col": 0, "text": "Metric"},
            {"row": 0, "col": 1, "text": "Value"}
          ]
        }
      ],
      "chart_edits": [
        {
          "chart_id": "s01_ch4",
          "categories": ["A", "B"],
          "series": [
            {"name": "Series 1", "values": [10, 20]}
          ]
        }
      ]
    }
  ]
}
```

**Per-slide plan discipline**:

| Decision | Rule |
|---|---|
| `source_slide` | Repeat the same value across multiple entries to reuse one source layout for several output slides; order is free |
| `notes` | Optional spoken speaker notes for the filled slide — see **Speaker notes** below; write prose, not a copy of the on-slide text |
| `transition` | Optional per-slide page transition; overrides the `apply --transition` default. Accepts an effect name (`fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random`), `none` to strip it, or `{ "effect": "push", "duration": 0.6 }` |
| `replacements` | Target by `slot_id` whenever possible; `shape_id` and `shape_name` are fallback selectors |
| `table_edits` | Optional native table cell edits; target by `table_id` whenever possible and use zero-based `row` / `col` |
| `chart_edits` | Optional native chart data edits; target by `chart_id`, set `categories`, and provide one or more `series` |
| Short text | For labels / chapter names / directory items, new text should be no longer than the original slot text |
| Body text | May be moderately freer than the original, but keep paragraph count and information density near the original slot |
| Empty slots | Use `scaffold --include-empty` only when a real placeholder is empty in the source deck |
| Native tables | Keep the original table row and column count; this workflow edits existing cells, not table structure |
| Native charts | Each series `values` list must match the category count; this workflow edits chart data, not chart styling |
| Facts | Every substantive claim must come from the user material |

**Fit check before apply**:

- Cover pages: replace title / subtitle / author only.
- Chapter pages: use short section labels.
- Dense content pages: compress material to bullets matching the existing slot capacity.
- Decorative or image-heavy pages: avoid forcing long prose into label-sized slots.

**Speaker notes (the `notes` field)** — distilled from the main pipeline's Logic Construction Phase, scaled to one note per planned slide:

Each `notes` value is **pure spoken narration**: write only what a presenter would say aloud, so the same text also works if the deck is later sent through `notes_to_audio.py`. The note explains and connects; it must not just restate the words already on the slide.

| Rule | Detail |
|---|---|
| Length | 2–5 natural sentences carrying the page's core message; cover / chapter / ending pages can be one or two sentences |
| Transitions | Carry page-to-page flow in the opening sentence as natural prose ("在明确了背景之后……" / "Having framed X, let's turn to Y") — never bracketed `[过渡]` / `[Transition]` tags |
| Plain prose only | No `#` heading line, no `- ` bullet lists, no `要点：① …` / `Key points:` lines, no `时长：2分钟` / `Duration:` annotations — embedded notes keep them verbatim and TTS would read them aloud |
| Number readability | Spell out figures when literal TTS pronunciation is awkward (Chinese "百分之六十八" over "68%"; plain English integers and percentages are fine) |
| One language | Match the deck's language; do not mix languages inside one note |
| Source-bound | Every substantive claim comes from the user material, same as `replacements` |

Example `notes` value for a Chinese content slide:

```json
"notes": "在看清整体市场格局之后，我们把镜头拉近到成都二手房的头部板块。当前挂牌均价同比上涨约百分之十二，但成交周期反而拉长到九十天以上，说明买方观望情绪在加重。这组数据是后面定价策略的基础，请重点留意。"
```

---

## Step 5: Check Text Capacity

Run the data-based capacity check before applying the plan:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py check-plan "<project_dir>/analysis/slide_library.json" "<project_dir>/analysis/fill_plan.json" -o "<project_dir>/analysis/check_report.json"
```

Interpret the report:

| Warning type | Action |
|---|---|
| Short label exceeds original length | Rewrite shorter; do not shrink font by default |
| Title too long | Rewrite first; only use font-size changes as a last resort |
| Body much longer than source slot | Compress, split across another selected page, or choose a larger source page |
| Missing target | Fix `slot_id` / `shape_id`; do not apply the plan |

**Default fitting policy**: short text can be shorter but should not be longer; body text may be somewhat freer. Do not use per-item font shrinking as a default strategy because it breaks template consistency.

---

## Step 6: Apply the Plan

Run:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py apply "<project_dir>/sources/<source.pptx>" "<project_dir>/analysis/fill_plan.json" -o "<project_dir>/exports/<output.pptx>"
```

By default `apply` gives every cloned slide a `fade` transition (`0.5s`), because most native templates ship an empty `<p:transition/>` that renders as *no* motion. Override the default with `--transition <effect>` (`fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random`) and `--transition-duration <seconds>`; pass `--transition none` for no motion, or `--transition keep` to preserve each source slide's existing transition unchanged. A per-slide `transition` field in the plan overrides whatever the CLI selects for that slide.

`apply` appends a timestamp automatically. For example, `-o "<project_dir>/exports/demo.pptx"` writes `demo_YYYYMMDD_HHMMSS.pptx`. If the filename already ends with `_YYYYMMDD_HHMMSS`, it is left unchanged.

The script:

| Behavior | Result |
|---|---|
| Clones selected source slides | Original slide design, relationships, images, layouts, and animations are preserved where PowerPoint supports them |
| Replaces text nodes | Text frames remain editable in PowerPoint |
| Writes `notes` fields | Speaker notes are embedded as native PowerPoint notes slides |
| Applies `--transition` / per-slide `transition` | Populates each slide's `<p:transition>` with a native PowerPoint page transition |
| Rebuilds presentation slide list | Output deck contains only the planned slide sequence |
| Adds timestamp to PPTX filename | Matches the main SVG-to-PPTX export convention |
| Drops orphaned source parts | Output carries only the selected pages and the layouts / media / charts they still reference (reachability prune) |

**Animation policy**: Template-fill preserves each cloned slide's existing object animation XML (the SVG pipeline's generated object animation defaults are not applied here). Page transitions are the one motion layer this workflow writes directly, and `apply` adds a `fade` transition by default so a filled deck is never left with the template's empty no-motion transitions; change it with `apply --transition` / a per-slide `transition` field, or opt out with `--transition keep` (preserve source) or `--transition none`. If the user asks to change object-level animation order / timing / effects, treat that as a separate direct-PPTX animation customization task.

---

## Step 7: Validate Output

Run a lightweight readability check:

```bash
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py "<project_dir>/exports/<output.pptx>"
```

Move or copy the read-back Markdown and extracted files into `<project_dir>/validation/` so `exports/` contains only final deliverables.

Verify:

| Check | Expected |
|---|---|
| Output filename | Ends with `_YYYYMMDD_HHMMSS.pptx` |
| Slide count | Matches `len(fill_plan.slides)` |
| Key title text | Appears in the extracted Markdown |
| Native table cells | Updated values appear in the extracted Markdown table |
| Native chart data | Updated labels / values are present in the cloned chart XML |
| Multi-line body text | Preserves intended line / paragraph breaks |
| Speaker notes | `ppt_to_md.py` can read the generated PPTX without notes-related errors |
| Missing target errors | None from `template_fill_pptx.py apply` |

If the extracted text is correct but visual overflow is likely, reduce the text in `fill_plan.json` and re-run Step 4.

```markdown
## ✅ Template Fill Complete

- [x] `slide_library.json` extracted from the source PPTX
- [x] `fill_plan.json` selects only pages that fit the target story
- [x] `check-plan` run and capacity warnings resolved or explicitly accepted
- [x] Output PPTX generated through direct OOXML text replacement
- [x] Speaker notes embedded when `notes` fields are present
- [x] `ppt_to_md.py` readability check passed
```

---

## Current Boundary

| Capability | Status |
|---|---|
| Select / reorder / repeat source slides | Supported |
| Replace text in existing text frames | Supported |
| Edit native PowerPoint table cell text | Supported |
| Edit native PowerPoint chart categories / series data | Supported |
| Preserve original visual design | Supported by cloning slide parts directly |
| Page-to-page transitions | Supported via `apply --transition` or per-slide `transition` |
| Replace images | Not in v1 |
| Object-level entrance animations | Not in v1; preserved from source only, set as a separate task |
| Edit chart formatting / axes / legend layout | Not in v1 |
| Edit SmartArt deeply | Not in v1 |
| Automatic visual overflow detection | Not in v1; use text-capacity judgment from the library slots |
