---
description: Fill Native PPTX route — use a native PowerPoint template deck, select fitting pages, and fill new material back without SVG conversion
---

# Fill Native PPTX Route

> Run when the user provides a raw `.pptx` template plus new content / a new topic and asks to generate a `.pptx` from that template. Typical requests include "use this PPT template to generate a PPTX", "fill this deck with the new content", "fill this back into the template", "replace the copy in this PowerPoint", or "keep the original PowerPoint pages and swap in this material". This route treats the existing `.pptx` as a native slide library and produces a new `.pptx` by selecting, cloning, and patching source slides.

This route is **independent** from the SVG generation pipeline. It treats the source PPTX as a native template / slide library, keeps the original PowerPoint design intact, and writes a new `.pptx` by cloning selected source slides and replacing text directly in OOXML.

**Boundary against template-based generation**: run this route for raw PPTX template + generated PPTX requests. Skip this route only when the user explicitly wants a reusable template workspace or an SVG-generated deck that can freely select / repeat / skip / adapt template pages. In that case, they must run [`create-template.md`](./create-template.md) first and then provide the generated workspace root to Generate PPTX.

| User wants | Route |
|---|---|
| Generate a PPTX from a raw PPTX template | This route |
| Directly edit / fill cloned PPTX slides | This route |
| Create a reusable design asset from the PPTX | `create-template` |
| Generate a new PPT from a reusable template package | Main pipeline Step 3 with the explicit template directory path |
| Generate through the SVG pipeline directly from a raw PPTX "template" | Not allowed; create the template package first |

## When to Run

Recognize requests that combine an existing PowerPoint template with new content or a topic and ask for a generated `.pptx` without explicitly requesting the reusable SVG/template-package route:

| Pattern | Example |
|---|---|
| Existing `.pptx` + "fill back" intent | "Use this deck and fill in the attached material" |
| Raw PPTX template + generated PPTX | "Use this PowerPoint template to generate a PPTX about this topic" |
| Existing `.pptx` + selective reuse | "Do not keep every page; only use the slides that fit" |
| Existing `.pptx` + copywriting replacement | "Keep the original design and replace the copy with this text" |
| Native PPT template fill | "Use this PowerPoint template for this content and fill the slides directly" |
| Direct wording | "Fill this deck with the new content" |

**Hard rule**: Do not run `pptx_to_svg.py`, `pptx_template_import.py`, `finalize_svg.py`, or `svg_to_pptx.py` for this route. SVG conversion is for presentation generation / template creation; this route is direct PowerPoint editing.

**Deterministic routing rule**: do not ask a route-choice question for raw PPTX template + generated PPTX requests; route them here. If the user asks for SVG/template-workspace generation from a raw PPTX, state that `create-template` must run first and stop this route until they provide the generated workspace root.

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

Create a dedicated project directory under `projects/`. Do not write outputs directly into `projects/` root. Reuse the standard project manager so source import rules stay consistent with the rest of the repository:

```bash
python3 skills/ppt-master/scripts/project_manager.py init "<project_name>" --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources "<project_dir>" "<source.pptx>" "<material...>"
```

**Source import rule**: `project_manager.py import-sources` copies files from outside the repository and moves repo-local files by default, unless `--copy` / `--move` is explicitly supplied. Keep this shared behavior; do not create a separate template-fill import path.

Use this fixed layout:

| Path | Required content |
|---|---|
| `<project_dir>/sources/` | Source PPTX and user-provided text / Markdown / converted materials |
| `<project_dir>/analysis/` | Slide library JSON, page-selection reasoning, and final fill plan |
| `<project_dir>/exports/` | Final generated PPTX only |
| `<project_dir>/validation/` | Read-back Markdown, extracted validation assets, and validation notes |

**Hard rule**: A template-fill project is a project, not a loose output file. The final answer must point to `<project_dir>/exports/<name>.pptx`, and all intermediate artifacts must remain inside `<project_dir>`.

---

## Step 3: Extract the PPTX Intake Bundle

`project_manager.py import-sources` automatically runs the standard PPTX intake for imported PowerPoint files and writes `<stem>.slide_library.json` into `<project_dir>/analysis/`. If you are working from a manually assembled project that does not have the intake artifact, run the template-fill analyzer directly:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py analyze "<project_dir>/sources/<source.pptx>" -o "<project_dir>/analysis/<stem>.slide_library.json"
```

Read `<project_dir>/analysis/<stem>.slide_library.json` (intake prefixes per-deck artifacts by the template deck's file stem) and identify:

| Field | Use |
|---|---|
| `slides[].page_type` | Cover / chapter / content / ending candidate |
| `slides[].text_summary` | Current semantic purpose of the source page |
| `slides[].slots[]` | Replaceable text slots with `slot_id`, `role`, `geometry`, paragraph count, and old text |
| `slides[].slots[].role` | Title / body / label candidate hint |
| `slides[].tables[]` | Native PowerPoint tables with `table_id`, row / column counts, per-cell coordinates/text, and merge anchor/slave topology |
| `slides[].charts[]` | Native PowerPoint charts with `chart_id` and an `edit_capability` safety result derived from the actual chart XML |
| `slides[].diagrams[]` | SmartArt layout, semantic nodes, hierarchy/connections, geometry, and extraction status; inventory-only |

**Selection rule**: Pick pages by content fitness, not by source order alone. A source page is useful only if its visible structure can carry the target message without heavy redesign.

A page's layout already encodes a rhetorical shape — a single hero statement, a lead-then-detail split, a 2×2 comparison, a stepwise progression, a metric row. Match the source material's own logic to a page whose structure expresses that same logic; do not pour unrelated content into a slot just because it is empty. When no selected page fits a piece of content well, drop that page or that content rather than forcing it — a forced fill reads as stiff. It is fine to use fewer pages than the source deck has.

**Layout-first planning**: Treat `<stem>.slide_library.json` as a layout inventory, not as an ordered deck outline. Before writing `fill_plan.json`, infer each reusable source page's affordance from JSON fields:

| JSON signal | Layout planning use |
|---|---|
| `slides[].page_type` | Identify cover / TOC / chapter / ending candidates, but do not preserve their original order by default |
| `slots[].role` counts | Infer whether the page is a hero statement, comparison, multi-card list, timeline, metric row, or dense explanation |
| `slots[].geometry` | Estimate whether each text slot is a short label, medium title, body block, caption, or decorative number |
| `slots[].text_metrics.font_size_px` | Estimate text capacity together with geometry; larger type means fewer safe characters |
| `slots[].text_summary` | Read the source page's original rhetorical pattern, not its literal placeholder wording |
| `diagrams[].layout` + `nodes` | Understand the SmartArt's source meaning; template-fill preserves it unchanged and cannot map new text into it |

**SmartArt boundary**: A selected source slide keeps its original native SmartArt parts. `check-plan` warns because the fill plan cannot replace SmartArt node text; choose another layout unless the original diagram content is intentionally retained, or explicitly accept the warning.

**Hard rule**: The target story controls output order. Source slides may move forward, move backward, be omitted, or be reused several times when their layout matches multiple target messages. Never treat source slide order as a default outline unless the user explicitly asks to preserve it.

**Required mapping pass**: Record a concise page-to-layout rationale in each planned slide before finalizing the plan. Use the per-slide `layout_rationale` object in `fill_plan.json` with `layout_pattern`, `why_fit`, and `risk`. This is human-review evidence that selection came from template structure rather than sequential replacement; it is not a mechanical checker gate.

---

## Step 4: Build the Fill Plan

Create a scaffold:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py scaffold "<project_dir>/analysis/<stem>.slide_library.json" -o "<project_dir>/analysis/fill_plan.json" --slides "1,3,4"
```

Then edit `<project_dir>/analysis/fill_plan.json` by hand from the source material. The plan is the single execution contract.

**Pages are reusable**: the output is the ordered `slides` list, not a one-to-one copy of the source deck. A source page is not single-use — list the same `source_slide` as many times as you need, each entry with its own `replacements`, to drive several output slides from one good layout (e.g., reuse a single content layout for five content pages). Likewise you may omit source pages entirely and put the selected ones in any order.

**Scaffold boundary**: `scaffold --slides` is only a convenience starter. If the final plan needs repeated source pages or a story order that differs from the template order, duplicate / reorder entries in `fill_plan.json` manually or generate the plan from `<stem>.slide_library.json`; do not let scaffold output constrain the deck structure.

The plan structure:

```json
{
  "schema": "template_fill_pptx_plan.v1",
  "status": "draft",
  "source_pptx": "projects/source.pptx",
  "accepted_warnings": [
    {
      "plan_slide": 3,
      "slot_id": "s03_sh5",
      "code": "text_capacity",
      "reason": "User accepted dense wording"
    }
  ],
  "slides": [
    {
      "source_slide": 1,
      "purpose": "cover",
      "layout_rationale": {
        "layout_pattern": "hero cover",
        "why_fit": "Large title and subtitle slots fit the opening message without redesign.",
        "risk": "Subtitle must stay short."
      },
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
| `status` | Keep `"draft"` until the user has reviewed the page sequence / reuse / deletion decisions. Set to `"confirmed"` only after approval. |
| `source_slide` | Repeat the same value across multiple entries to reuse one source layout for several output slides; order is free and must follow the target story rather than source deck order |
| `layout_rationale` | Human review aid for page selection. Include `layout_pattern`, `why_fit`, and `risk`; it is not a mechanical checker gate. |
| `accepted_warnings` | Optional audit trail for warnings the user or agent explicitly accepts. `check-plan` warnings remain non-blocking; errors must be fixed. |
| `notes` | Optional spoken speaker notes for the filled slide — see **Speaker notes** below; write prose, not a copy of the on-slide text |
| `transition` | Optional per-slide page transition; overrides the `apply --transition` default. Accepts an effect name (`fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random`), `none` to remove the visual effect, `keep` to preserve the source, or an object such as `{ "effect": "push", "duration": 0.6, "advance_after": 5 }` |
| `replacements` | Target by `slot_id` whenever possible; `shape_id` and `shape_name` are fallback selectors |
| `table_edits` | Optional native table cell edits; target by `table_id` whenever possible and use zero-based `row` / `col` |
| `chart_edits` | Optional native chart data edits; target by `chart_id`, set `categories`, and provide one or more `series` |
| Short text | For labels / chapter names / directory items, fit the slot's visual capacity from geometry and font size; do not rely on old placeholder length alone |
| Body text | May be moderately freer than the original, but keep paragraph count, visual width, and information density near the slot's geometry capacity |
| Empty slots | Use `scaffold --include-empty` only when a real placeholder is empty in the source deck |
| Native tables | Keep the original table row and column count; edit ordinary cells or a merge anchor only. A merge slave is not visible and is rejected by both `check-plan` and `apply`. This route never changes table structure. |
| Native charts | Each series `values` list must match the category count. Single-plot classic charts whose every series uses `c:cat/c:val` are editable; analyzer/checker preflight the structure and the runtime writer revalidates the actual chart XML before mutation. |
| Chart edit boundary | A single classic plot is editable when every series uses `c:cat/c:val`, including stock, 3D, surface, and other classic plot types. Date-axis and multi-level categories are accepted with a warning because replacement categories are flattened to one level. Scatter, bubble, ChartEx/unknown frames, multi-plot/combo charts, missing-series charts, and non-`c:cat/c:val` data models are rejected. Use beautify / main pipeline to redraw unsupported charts, or leave the native chart untouched. |
| Facts | Every substantive claim must come from the user material |

**Fit check before apply**:

- Cover pages: replace title / subtitle / author only.
- Chapter pages: use short section labels.
- Dense content pages: compress material to bullets matching the existing slot capacity.
- Decorative or image-heavy pages: avoid forcing long prose into label-sized slots.
- Repeated source pages: every repeated entry must carry a distinct purpose and replacement set; avoid visual repetition unless the repeated layout expresses the same rhetorical pattern.
- Reordered source pages: verify the new sequence reads as a coherent story; template page numbers, decorative section markers, and notes must be updated to match the output order.

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
python3 skills/ppt-master/scripts/template_fill_pptx.py check-plan "<project_dir>/analysis/<stem>.slide_library.json" "<project_dir>/analysis/fill_plan.json" -o "<project_dir>/analysis/check_report.json"
```

Interpret the report:

| Warning type | Action |
|---|---|
| Short label exceeds visual width | Rewrite shorter or choose a layout with a larger label slot; do not shrink font by default |
| Title too long | Rewrite first; only use font-size changes as a last resort |
| Body much longer than source slot | Compress, split across another selected page, or choose a larger source page |
| SmartArt source content remains unchanged | Pick another source slide unless the original SmartArt wording is intended; otherwise record the accepted warning |
| Missing target | Fix `slot_id` / `shape_id`; do not apply the plan |

`check-plan` emits stable `code` fields in its JSON results so warnings can be tracked without parsing message text. Warnings are advisory and do not fail the command; record any intentionally accepted warning in `accepted_warnings` when it matters for review. Errors are blocking and must be fixed before apply.

**Default fitting policy**: Check fit against visual capacity, not raw character count. CJK characters, Latin letters, numbers, and punctuation occupy different visual widths; old placeholder text is only a weak signal. Use `capacity_visual_width` when present, together with `slots[].geometry` and `slots[].text_metrics.font_size_px`, to decide whether to rewrite, split, or choose a different source layout. Do not use per-item font shrinking as a default strategy because it breaks template consistency.

---

## Step 6: Apply the Plan

⛔ **BLOCKING GATE**: The user has reviewed the planned output order, omitted pages, reused pages, and material-to-layout fit. Set `<project_dir>/analysis/fill_plan.json` top-level `status` to `"confirmed"` only after that review. `apply` rejects an unconfirmed plan by default; `--force` exists only for deliberate recovery/debug use.

Run:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py apply "<project_dir>/sources/<source.pptx>" "<project_dir>/analysis/fill_plan.json" -o "<project_dir>/exports/<output.pptx>"
```

By default `apply` gives every cloned slide a `fade` transition (`0.5s`), preserving the v1 route contract. Override it with `--transition <effect>` (`fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random`) and `--transition-duration <seconds>`; pass `--transition none` for no visual motion, or `--transition keep` to preserve each source slide's existing transition unchanged. A per-slide `transition` field overrides the CLI. `advance_after` keeps click advance enabled and adds timed advance; it also works with `none` (timing-only transition) and `keep` (source effect preserved, Choice/Fallback timing updated together).

`apply` appends a timestamp automatically. For example, `-o "<project_dir>/exports/demo.pptx"` writes `demo_YYYYMMDD_HHMMSS.pptx`. If the filename already ends with `_YYYYMMDD_HHMMSS`, it is left unchanged.

The script:

| Behavior | Result |
|---|---|
| Clones selected source slides | Original slide design, relationships, images, layouts, and animations are preserved where PowerPoint supports them |
| Replaces text nodes | Text frames remain editable in PowerPoint |
| Writes `notes` fields | Speaker notes are embedded as native PowerPoint notes slides |
| Applies `--transition` / per-slide `transition` | Applies the requested visual-transition and slide-advance policy; `keep` may preserve no carrier and `none` may remove it |
| Rebuilds presentation slide list | Output deck contains only the planned slide sequence |
| Adds timestamp to PPTX filename | Matches the main SVG-to-PPTX export convention |
| Drops orphaned source parts | Output carries only the selected pages and the layouts / media / charts they still reference (reachability prune) |

**Animation policy**: Template-fill preserves each cloned slide's existing object animation XML (the SVG pipeline's generated object animation defaults are not applied here). Page transitions are the one motion layer this route writes directly, and `apply` adds a `fade` transition by default; change it with `apply --transition` / a per-slide `transition` field, or opt out with `--transition keep` (preserve source) or `--transition none`. `keep` preserves direct and `mc:AlternateContent` transition effects without converting unknown effects to `fade`; explicit replacement removes the old logical carrier before writing one new carrier. If the user asks to change object-level animation order / timing / effects, treat that as a separate direct-PPTX animation customization task.

---

## Step 7: Validate Output

Run a lightweight readability check:

```bash
python3 skills/ppt-master/scripts/template_fill_pptx.py validate "<project_dir>"
```

The validator finds the latest PPTX in `<project_dir>/exports/`, runs `ppt_to_md.py` into `<project_dir>/validation/readback.md`, and writes `<project_dir>/validation/validate_report.json`. `exports/` must contain only final deliverables.

Verify:

| Check | Expected |
|---|---|
| Output filename | Ends with `_YYYYMMDD_HHMMSS.pptx` |
| Slide count | Matches `len(fill_plan.slides)` |
| Key title text | Appears in the extracted Markdown |
| Native table cells | Updated values appear in the extracted Markdown table |
| Native chart data | Updated labels / values are readable from the extracted Markdown when `ppt_to_md.py` can surface them |
| Multi-line body text | Preserves intended line / paragraph breaks |
| Speaker notes | Read-back note count matches planned `notes` fields |
| Missing target errors | None from `template_fill_pptx.py apply` |

If the extracted text is correct but visual overflow is likely, reduce the text in `fill_plan.json` and re-run Step 4.

```markdown
## ✅ Template Fill Complete

- [x] Standard PPTX intake extracted from the source deck, including `<stem>.slide_library.json`
- [x] `fill_plan.json` selects only pages that fit the target story
- [x] User reviewed the story structure and `fill_plan.json` has `status: "confirmed"`
- [x] `check-plan` run; errors fixed; warnings reviewed / optionally recorded in `accepted_warnings`
- [x] Output PPTX generated through direct OOXML text replacement
- [x] Speaker notes embedded when `notes` fields are present
- [x] `template_fill_pptx.py validate` read-back check passed
```

---

## Current Boundary

| Capability | Status |
|---|---|
| Select / reorder / repeat source slides | Supported |
| Replace text in existing text frames | Supported |
| Edit native PowerPoint table cell text | Supported for ordinary cells and merge anchors; merge slaves fail closed |
| Edit native PowerPoint chart categories / series data | Supported for single-plot classic `c:cat/c:val` charts; runtime XML validation remains authoritative |
| Read SmartArt node text / hierarchy / layout | Supported in intake and planning |
| Preserve existing native SmartArt unchanged | Supported by recursive private-part cloning |
| Preserve original visual design | Supported by cloning slide parts directly |
| Page-to-page transitions | Supported via `apply --transition` or per-slide `transition` |
| Replace images | Not in v1 |
| Object-level entrance animations | Not in v1; preserved from source only, set as a separate task |
| Edit chart formatting / axes / legend layout | Not in v1 |
| Edit or generate native SmartArt | Not supported; regenerated visual routes use ordinary editable shapes |
| Automatic visual overflow detection | Not in v1; use text-capacity judgment from the library slots |
| Material-divergence reshaping (§c content strategy) | Not applicable — this route fills text into existing slots, it does not author an outline from a source, so the Generate PPTX `content_divergence` free-text field has no role here |
