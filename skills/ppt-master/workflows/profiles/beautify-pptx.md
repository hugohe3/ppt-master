---
description: Main-generation profile for 1:1, content-faithful re-layout of an existing deck through the standard SVG pipeline.
---

# Beautify PPTX (Re-layout) Profile

> Main-pipeline profile, not a top-level route. [`template-fill-pptx.md`](../template-fill-pptx.md) reuses a deck's design and swaps in new content; this profile keeps a deck's content and redoes its layout.

Re-lays-out an existing `.pptx`: the text is preserved **verbatim**, the source deck's visual identity (palette / fonts) is **inherited as truth**, and only layout, hierarchy, and whitespace are redesigned. Output is a brand-new native deck generated through the standard SVG pipeline — not a patch over the original.

**Trigger**: the user supplies a `.pptx` and asks to beautify / re-layout / 重新排版 / 美化 while keeping the content. Explicit intent + a provided file only; never auto-infer.

---

## 1. When to Run

| Pattern | Example |
|---|---|
| Existing `.pptx` + beautify intent | "把这份 PPT 美化一下" / "make this deck look better" |
| Existing `.pptx` + re-layout intent | "重新排版这份 PPT，内容别动" / "re-layout this, keep the wording" |
| Existing `.pptx` + paste-back intent | "重排后我要把元素贴回原来的模板" |

**Hard rule — content is frozen**: every text string from the source is preserved exactly (no add / remove / reword / reorder). Beautification freedom lives only in layout, hierarchy, spacing, and visual rhythm.

**Hard rule — not a patch, not a fill**: this regenerates a native deck through Strategist → Executor → export ([`generate-pptx`](../generate-pptx.md) Steps 4–7). It does **not** edit the source file in place, and it is **not** [`template-fill-pptx`](../template-fill-pptx.md) (which clones source slides and replaces text). It also does not parse an arbitrary third-party template for text-only substitution (the rejected #53 direction) — it builds every page from scratch.

**Distinct from mirror templates**: `replication_mode: mirror` ([`executor-structured.md`](../../references/executor-structured.md) §1.1) keeps layout + visuals verbatim and edits text. Beautify is the inverse — content verbatim, layout redone, identity inherited.

**When this profile is wrong — re-architecture belongs to the default main pipeline**: this profile preserves the source's page count and page order 1:1. It is for "keep this deck, just lay it out better". When the user instead wants the original page breakdown reconsidered — merge / split / reorder pages, re-outline the structure, build a *better deck* from the same content rather than a prettier version of the same pages — do not activate this profile. This includes re-pagination for fit: "keep every word but split a crowded page so it reads better" changes page count. Convert the deck with [`ppt_to_md`](../../scripts/source_to_md/ppt_to_md.py) and run the default main pipeline, where the Strategist re-architects the outline freely from the extracted content. The deciding question: is the source's page split information to preserve, or just the previous author's structure to improve? Preserve → activate this profile; improve → default main pipeline.

---

## 2. Inputs

🚧 **GATE**: the user has provided:

| Input | Required | Notes |
|---|---:|---|
| Source PPTX | Yes | The deck to re-lay-out |
| Beautify scope | Optional | Density / emphasis preference — never content rewrites, and never page drops (v1 is strict 1:1) |

---

## 3. Create the Project Workspace

Match the canvas to the source so 1:1 pages and paste-back align. Determine the source aspect first — before the project exists, run `beautify_identity.py <source.pptx>` to **stdout** and read `canvas.aspect` (the formal standard intake bundle is written in Step 4, after `init`) — then `init` with the matching format:

| Source aspect | Format |
|---|---|
| ≈1.778 (16:9) | `ppt169` |
| ≈1.333 (4:3) | `ppt43` |
| other | nearest format in [`canvas-formats.md`](../../references/canvas-formats.md); record the source pixel size in the spec |

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source.pptx>
```

---

## 4. Extract Identity and Data; Assemble Inventory

Use the standard PPTX intake bundle from Step 3. `project_manager.py import-sources` already writes it under `analysis/` for PPTX-family inputs. If the bundle is missing because the project predates this workflow, generate it once:

```bash
python3 ${SKILL_DIR}/scripts/pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis
```

**Content + images — already produced by Step 3.** `import-sources` ran `ppt_to_md` on the deck, so the **frozen content contract** is `sources/<stem>.md` (one source slide per block, in order). If the source deck contains pictures, they are already propagated to `images/` with per-slide binding in `images/image_manifest.json` (`occurrences[].slide_index`). Do **not** re-run `ppt_to_md` — it would duplicate the conversion and write images to `analysis/<stem>_files/` instead of `images/`.

**Visual identity (theme + observed sample + canvas)**: read `<project_path>/analysis/<stem>.identity.json` (intake prefixes per-deck artifacts by source-file stem).

| Field | Use |
|---|---|
| `theme.palette.background` / `text` / `primary` / `accent1..6` | the deck's *declared* colors |
| `theme.fonts.title` / `body` (`ea` = CJK, `latin`) | the deck's *declared* fonts |
| `theme.sizes.title` / `body` (pt) | the deck's *declared* placeholder sizes (master `txStyles`) — the size a run inherits when it sets no explicit `sz`; `body` is the **level-1** default (coarsest, commonly over-reads) |
| `theme.sizes.body_levels` (pt list) | the full master `bodyStyle` ramp (lvl1..lvl9, e.g. `[32, 28, 24, 20, …]`) — **reference context** so you can read a deeper level than the over-reading level-1, not an auto-seed |
| `observed.colors` / `observed.fonts` (`latin` / `ea`, frequency-ranked) | a usage **sample / frequency hint** — run-level fonts + explicit `srgbClr` fills across slides |
| `observed.sizes_pt` (pt, frequency-ranked) | a usage **sample** of run-level explicit point sizes — the **size the deck actually renders at** when it overrides the placeholder default; the source for the Step 5 `body_size` recommendation |
| `layout_sizes_pt` (pt, frequency-ranked) | **reference fact only**, NOT an auto-seed — the level-1 sizes that the in-use slide layouts' body placeholders declare. Usually empty (decks rely on runs / master) and ambiguous when present; use it as a hint when judging the body size, never as the authoritative seed |
| `canvas.aspect` | drives the Step 3 format choice |

> Note: `theme` is what the deck declares; `observed` is a frequency sample of run-level overrides (not a complete style resolution — it misses `schemeClr` and master/layout inheritance, and counts chart/gradient fills). A hand-edited deck can diverge from `theme` — Step 5 recommends which to inherit and the user confirms.

**Chart + table data (for regeneration)**: read `<project_path>/analysis/<stem>.slide_library.json`. It contains the source chart and table *data* so they can be redrawn natively in the inherited style:

| `<stem>.slide_library.json` field | Use |
|---|---|
| `slides[].charts[]` (`chart_type` / `categories` / `series[].values`) | regenerate as a native SVG chart; use the §VII catalog key only when recall selects a real reference, otherwise plan the custom chart in §IX |
| `slides[].tables[]` (`row_count` / `column_count` / cell text) | regenerate as a native SVG table |

**Hard rule — regenerate visuals, do not carry them over**: charts / tables / images are rebuilt from their data in the inherited style, never spliced in byte-for-byte. This keeps the deck style-consistent and natively editable. **Data values are frozen** (categories / series / cell text / numbers unchanged); only their rendering is the deck's own. Pictures (`ppt_to_md`-extracted files) are reused but re-laid-out — position / crop / size follow the new layout, not the source slot. A user who wants an original element verbatim copies it across themselves.

**Optional source-SVG visual reference**: when the source deck has complex vector decoration, distinctive page chrome, or a visual language that cannot be captured by `<stem>.identity.json` colors/fonts alone, create a read-only SVG reference package under `analysis/`. This is for understanding style only; it is not a carry-over asset path.

```bash
python3 ${SKILL_DIR}/scripts/pptx_to_svg.py <project_path>/sources/<source.pptx> -o <project_path>/analysis/source_svg_import
python3 ${SKILL_DIR}/scripts/extract_svg_assets.py <project_path>/analysis/source_svg_import/svg-flat \
    --icons-dir <project_path>/analysis/source_svg_import/icons \
    --icon-namespace imported \
    --inplace --id-prefix source_flat --min-decoration-bytes 3000 --clean-stale
```

Use the cleaned `analysis/source_svg_import/svg-flat/slide_*.svg` files plus `analysis/source_svg_import/svg-flat_vector_asset_inventory.json` in Step 5/Strategist. Extraction is required for inspection when complex vectors exist: it creates a candidate pool the AI can index, compare, and judge for possible reuse without reading every heavy vector body. Read an individual `analysis/source_svg_import/icons/imported/*.svg` only when the cleaned page and inventory indicate that candidate may be promoted or materially affects the style decision. These candidates are analysis artifacts first, not automatic output assets.

Default: do **not** copy these candidates into the project `icons/`, do **not** list them as reusable output assets, and do **not** preserve original vector decorations byte-for-byte in the beautified deck. The Executor still regenerates fresh native shapes from the confirmed plan.

Optional reuse gate: if a candidate is a non-text brand/logo/motif/decorative asset that should survive the beautification, list it in the Step 5 plan with source slide, candidate filename, intended reuse, and dependency notes from the inventory. Wait for user confirmation. Only confirmed candidates may be promoted into `<project_path>/icons/imported/` and referenced from generated SVGs with `<use data-icon="imported/<name>"/>`; `finalize_svg.py` then re-inlines them as native shapes. Never promote text-bearing groups, charts/tables, source page layouts, or dense slide composites as reusable assets.

**Assemble the inventory** — the deterministic join into one per-slide ledger, `analysis/beautify_inventory.json`, the contract Step 5 confirms and Step 7 verifies against:

```bash
python3 ${SKILL_DIR}/scripts/beautify_inventory.py <project_path>/analysis/<stem>.slide_library.json \
    --images <project_path>/images/image_manifest.json -o <project_path>/analysis/beautify_inventory.json
```

If `images/image_manifest.json` does not exist because the source deck has no extracted pictures, omit `--images`. The script joins per slide: `text_blocks` (slot text + geometry), `tables` (cell grid), `charts` (categories + series values), `diagrams` (SmartArt nodes + hierarchy/connections + source layout), and `images` (bound via `image_manifest` `occurrences[].slide_index`, with geometry / `usage_count`). The **frozen source values are inlined**, so the inventory is a self-contained contract, not a pointer back to `slide_library.json`. It emits `ignored` and `needs_confirmation` as **empty arrays** — fill them with judgment before Step 5:

| Field | Fill with |
|---|---|
| `ignored` | hidden slides / shapes, master-only text, image crop / opacity / rotation / mask (not captured upstream) |
| `needs_confirmation` | unreadable SmartArt data; combo / dual-axis / waterfall charts; merged-cell or multi-header tables; density-outlier pages — **either** overcrowded **or** near-empty / title-only |

**SmartArt output boundary**: Preserve its extracted wording and semantic relationships, then redraw it through SVG as ordinary editable PowerPoint shapes. Do not attempt to regenerate a native SmartArt object or reuse persisted-drawing text as a second content source.

```markdown
## ✅ Extraction Complete

- [x] `sources/<stem>.md` (from Step 3) holds every source slide's text, in order; extracted pictures, if any, are in `images/` + `images/image_manifest.json`
- [x] `analysis/<stem>.identity.json` has theme + observed identity + canvas aspect
- [x] `analysis/<stem>.slide_library.json` holds chart + table data and SmartArt semantic structure for regeneration
- [x] `analysis/source_profile.json` (multi-deck index) summarizes the source facts in its `decks[]` entry
- [x] `analysis/beautify_inventory.json` ledgers per-slide text / images / data + ignored + needs-confirmation
- [ ] **Next**: Step 5 — Beautify Plan (recommend & confirm)
```

---

## 5. Beautify Plan — Recommend & Confirm

⛔ **BLOCKING**: the scope is not hard-coded — same spirit as the Strategist confirmation stage. Recommend each item below from what the deck actually contains (the Step 4 inventory), present the plan, and **wait for the user to confirm or adjust** before writing any spec. Chat is the canonical channel; the confirm UI below is the visual convenience surface over it for the palette + typography review (its result is honored identically to a chat reply).

This step has two halves:
- **Visual re-confirm via the confirm UI** — the **full** Step 4 confirm page (below), seeded from the source so every targeted-confirmation field (canvas, mode, visual style, palette, icons, typography incl. body baseline, image strategy, generation mode) is **pre-filled with the inherited / source-derived default and left editable**. Beautify *recommends* keeping the source's identity, but never removes the user's place to override any field — you may choose not to change a value, but you must not deny the place to change it. This is also where the deck's text size is confirmed: `<stem>.identity.json` now carries size hints — `observed.sizes_pt` (the point sizes the deck actually renders at) and `theme.sizes` (the declared placeholder defaults) — so the `body_size` recommendation **follows the source's own font size** rather than a blind canvas default; the user still confirms or overrides it here.
- **Structural scope** — the inventory-driven list decisions below (ignored, reuse, needs-confirmation, verification level) stay in **chat**; they have no confirm-UI widget.

| Plan item | Recommend from | Default lean |
|---|---|---|
| Identity source | `<stem>.identity.json` `theme` vs `observed` | present **both as color / typography candidates in the confirm UI** so the user picks the one that looks right (theme first when the deck is theme-driven; observed first when slides override heavily) — recommend a default ordering and say why |
| Preserve scope | inventory `text_blocks` / `images` / `charts` / `tables` / `diagrams` | all text verbatim; data values and SmartArt relationships frozen; pictures reused |
| Ignored | inventory `ignored` | name them so the user sees what drops (hidden / master-only text / image crop / rotation) |
| Needs confirmation | inventory `needs_confirmation` | flag complex charts + overcrowded pages explicitly; ask how to handle |
| Verification level | deck size / risk | recommend the Step 7 per-page checks; user sets strictness |

**Hard rule — content is frozen, not the scope decisions**: text strings and chart/table/table-cell data values are non-negotiable (verbatim). *Which* identity to inherit, what to ignore, and how to treat flagged items are recommend-then-confirm, never silently decided.

**Recommend honestly — name the v1 ceiling**:

| Item | What v1 delivers |
|---|---|
| Overcrowded source page | layout / hierarchy / whitespace improve **within the page as-is** — v1 does **not** relieve information overload (that needs re-pagination / rewrite, deferred). Flag such pages; the user may accept or note them for manual split |
| Paste-back into the original | regenerated elements share the inherited palette + fonts, so they **blend visually** when pasted. v1 does **not** guarantee a seamless coordinate-level drop-in (slide coordinates, master placeholders, font availability are the original deck's, not ours) |
| Complex charts / merged-cell tables | best-effort from the captured data; combo / dual-axis / waterfall lose the un-captured plots — flagged for the user |

**Visual re-confirm — full confirm UI seeded from the source**:

Write `<project_path>/confirm_ui/recommendations.json` and launch the same confirm server [`generate-pptx`](../generate-pptx.md) Step 4 uses. Do **not** hide fields: seed **every** targeted-confirmation field with the inherited / source-derived default so the user sees the recommendation and keeps the place to change it. Schema → [`scripts/docs/confirm_ui.md`](../../scripts/docs/confirm_ui.md).

```json
{
  "recommend": {
    "canvas": "<step3-canvas-id>",
    "mode": "briefing",
    "visual_style": "<closest visual-style id to the source look>",
    "icons": "<sensible default icon library>",
    "image_usage": ["provided"]
  },
  "page_count": { "value": "<source-slide-count>" },
  "audience": { "value": "<carry over from the deck's apparent audience, or state a concrete provisional audience>" },
  "communication_intent": { "value": "<open prose inferred from the deck; preserve multiple purposes and their relationship>" },
  "audience_outcome": { "value": "<what the audience should know, understand, decide, or do>" },
  "core_message": { "value": "<the deck-wide claim / ask / action already present in the source>" },
  "delivery_context": { "value": "<presenter-led / reader-led / hybrid / recorded, plus occasion if inferable>" },
  "artifact_afterlife": { "value": "<review / approval / archive / hand-off / reuse / none planned>" },
  "content_divergence": { "value": "keep source wording and page structure verbatim", "locked": true },
  "color": { "selected": 0, "candidates": [
    { "name_zh": "复刻源 PPT（推荐）", "name_en": "Source replica (recommended)", "name_ja": "元PPTを再現（推奨）", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
    { "name_zh": "实际用色（observed）", "name_en": "Observed palette", "name_ja": "実際の使用色（observed）", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
    { "name_zh": "备选配色 A", "name_en": "Alternative palette A", "name_ja": "代替配色A", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } }
  ] },
  "typography": { "selected": 0, "candidates": [
    { "name_zh": "复刻源 PPT（推荐）", "name_en": "Source replica (recommended)", "name_ja": "元PPTを再現（推奨）", "heading": { "cjk": "...", "latin": "...", "css": "<PPT-safe stack>" }, "body": { "cjk": "...", "latin": "...", "css": "<PPT-safe stack>" }, "body_size": <dominant observed.sizes_pt × 4/3, as px> },
    { "name_zh": "实际字体（observed）", "name_en": "Observed fonts", "name_ja": "実際のフォント（observed）", "heading": { "cjk": "...", "latin": "...", "css": "<PPT-safe stack>" }, "body": { "cjk": "...", "latin": "...", "css": "<PPT-safe stack>" }, "body_size": <dominant observed.sizes_pt × 4/3, as px> },
    { "name_zh": "备选字体 A", "name_en": "Alternative pairing A", "name_ja": "代替ペアリングA", "heading": { "cjk": "...", "latin": "...", "css": "<PPT-safe stack>" }, "body": { "cjk": "...", "latin": "...", "css": "<PPT-safe stack>" }, "body_size": <canvas-appropriate baseline> }
  ] }
}
```

- **Recommend keep, allow override**: pre-fill the open communication contract from the source's apparent audience and purpose, preserving composite purposes in prose; also pre-fill canvas / mode / visual style / icons / image strategy with the source-faithful default (canvas = Step 3 format, mode = `briefing`, image_usage = `provided`). The purpose examples are hints, never a `primary_job` selector. Beautify's only true non-choices are frozen text and strict 1:1 page count (changing either means routing to the main pipeline). Seed `content_divergence` to verbatim preservation with `locked: true`; the Confirm UI renders it read-only and the server restores the locked value on every staged submit. A request to reshape wording or page structure routes to the main pipeline instead of weakening this profile.
- **Our recommendation is the pre-selected default = the source replica**: for color and typography, author **several candidates** like the from-scratch flow. The pre-selected default (`selected: 0`, the first card) is what beautify recommends — the candidate that **best replicates the source deck's style** (the truest reading of `theme` / `observed`). Replicate-by-default.
- **Judge the other alternatives exactly as the from-scratch flow does — fonts as much as colors**: don't invent a beautify-specific rule. Author each non-replica candidate with the **same content-driven judgment the Strategist uses when generating from scratch** (color §e, typography §g), applied to the material this project provides — the source document's content and subject, the company's own theme colors, and any brand signal. Pick the palette **and** the font pairing by what fits *this* deck's content; fonts are chosen by content fit, not just defaulted to a safe face. Reach **≥3 candidates total** (PPT-safe stacks; the same creative-choice rule used elsewhere) so a user who departs from the replica still lands on a considered, content-fitting direction — depart-by-choice.
- **`body_size` is the load-bearing field, and the replica follows the source's own size**: seed the replica candidate's `body_size` from the source's actual body size — take the dominant `observed.sizes_pt` value (the most frequent run-level size, the **body proxy**) and **convert it to px (`× 4/3`)** before seeding, since the system is px-only and the source measures in pt: a source 20pt body becomes `26.67`px, so the replica renders at the source's true size (seeding the bare `20` as px would shrink it ~25% — the pt-as-px trap). Whichever source value you land on below (observed mode, or `theme.sizes.body`) gets the same `× 4/3` conversion. The confirm page (and chat fallback) then writes that px to `result.json` (`body_size`) **directly — no further conversion, no `body_size_pt` provenance** (pt never enters the contract). The "most frequent = body" read is a proxy, not a guarantee — `observed.sizes_pt` counts every explicit run size (titles, captions, footnotes, chart/label text included, no placeholder-type resolution), so a deck dense with small labels can let a caption size outrank true body; cross-check the proxy against the page's actual body blocks and the sanity range below before trusting it, and prefer the size the body paragraphs visibly render at over the raw mode when the two disagree. Fall back to `theme.sizes.body` (the declared placeholder size) when `observed.sizes_pt` is empty, and to a PPT consumption-mode baseline (`text` 20 / `balanced` 24 / `presentation` 32 px — one fixed value per mode) only when neither is present. Note `theme.sizes.body` is the master `bodyStyle` **level-1 declared default** — a coarse value that commonly **over-reads** the real body density (decks often render body at a deeper outline level or override it smaller), so when you land on this fallback treat it as an upper-ish guess and run it through the sanity check below, never as a precise body size. `theme.sizes.body_levels` and `layout_sizes_pt` are **reference context, not extra fallback tiers**: consult them to judge a saner body value when the deck is theme-driven (`observed` empty) — e.g. a deeper `body_levels` entry or a `layout_sizes_pt` hint may read truer than level-1 — but do not auto-seed from them; the seed chain stays `observed → theme.sizes.body → consumption-mode baseline`, and a theme-driven deck whose body size genuinely can't be pinned cleanly is exactly the case the sanity check is for. The canvas hint stays a **sanity range**, not the seed: if the source's own size lands far outside it (a dense source doc reads tiny on a projection canvas), surface that to the user rather than silently snapping — the replica recommendation is the source's size, the user confirms or overrides. Non-replica alternatives may use the consumption-mode baseline. This is what prevents the deck from exporting at an unintentionally small size while still honoring the source.

```bash
python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon --wait
```

After the final wait returns, read `<project_path>/confirm_ui/result.json` exactly once and retain the complete confirmed object through Design Spec authoring. Chat is the canonical fallback when the page cannot open (remote / headless) — present the same fields in chat and retain the reply identically. Always run `--shutdown` on exit (page-confirm or chat-fallback) so port 5050 is free for Step 6 live preview.

On confirmation, enter [`generate-pptx`](../generate-pptx.md) Step 4 as Strategist with the plan pre-resolved. The two beautify invariants always hold: the content-faithful clause ([`strategist.md`](../../references/strategist.md) §d Layer 1) and page count = source slide count (strict 1:1). Write the retained confirmed object completely into `design_spec.md` — `mode` (recommended `briefing`), canvas, `visual_style`, color (e) + typography (g) incl. `body_size` (the reviewed values; skip both recommendation flows) — honoring whatever the user kept or overrode. Do not reopen `result.json` afterward. §VII contains only `Page | Template | Usage` rows for selected catalog references; unmatched chart/table plans stay in their §IX page blocks. §VIII contains source pictures for re-layout.

**Hard rule — §IX is verbatim and 1:1**: each source slide becomes exactly one page, in source order, its text transcribed word-for-word from `sources/<stem>.md`. Do not merge, split, drop, or rewrite. Complete and audit `design_spec.md` first, then author `spec_lock.md` from that Design Spec plus the source/page/template context per `strategist.md` §6 before handing off to the Executor.

---

## 6. Executor + Export

Run the standard pipeline ([`generate-pptx`](../generate-pptx.md) Steps 6–7). The Executor re-lays-out each page — hierarchy, spacing, alignment, page rhythm — using the semantic anchors in `spec_lock.md` plus current page/source/template context; valid page-local colors, gradients, effects, and export-safe display faces need not be added to the lock. It regenerates charts / tables as native SVG from the extracted data and re-lays-out the source pictures.

Follow [`generate-pptx`](../generate-pptx.md) Step 7 for the canonical serial
post-processing commands, gates, success criteria, and export artifacts.

---

## 7. Validate Output

```bash
python3 ${SKILL_DIR}/scripts/source_to_md/ppt_to_md.py <project_path>/exports/<output.pptx>
```

| Check | Expected |
|---|---|
| Text fidelity | every source text string appears in the output, unaltered |
| Data fidelity | chart categories / series / table cells match the source exactly |
| Page count | output slide count equals the source slide count |
| Regenerated visuals | charts / tables are native SVG re-themed to the inherited palette |
| Identity | generated text / shapes use only `<stem>.identity.json` colors + fonts |
| Paste-back | copying a beautified element into the original deck looks native |

```markdown
## ✅ Beautify Complete

- [x] Content + data values verbatim (read-back Markdown matches the source)
- [x] 1:1 page count preserved
- [x] Source colors + fonts inherited as locked truth
- [x] Charts / tables regenerated as native SVG in the inherited style
- [x] Native PPTX exported to `exports/`
```

---

## Current Boundary

| Capability | Status |
|---|---|
| Re-layout with verbatim text | Supported |
| Inherit source palette / fonts as truth | Supported |
| Strict 1:1 page mapping | Supported |
| Regenerate charts / tables as native SVG from extracted data | Supported |
| Re-lay-out source pictures | Supported |
| Re-pagination (split dense / merge sparse) | Not in v1 |
| Carry source charts / tables / images over byte-for-byte | Out of scope — user copies originals manually if wanted |
| Free visual-style application / cleanup deviating from source identity | Not in v1 |
| Batch / multi-deck beautification | Not in v1 |
