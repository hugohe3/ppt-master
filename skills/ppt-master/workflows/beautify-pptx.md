---
description: Content-faithful PPT beautification — re-layout an existing deck while preserving its text verbatim and inheriting its visual identity, so regenerated elements share the original's palette/fonts and blend with it when pasted back.
---

# Beautify PPTX (Re-layout) Workflow

> Mirror of [`template-fill-pptx.md`](./template-fill-pptx.md): template-fill reuses a deck's design and swaps in new content; beautify keeps a deck's content and redoes its layout.

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

**Hard rule — not a patch, not a fill**: this regenerates a native deck through Strategist → Executor → export (SKILL.md Steps 4–7). It does **not** edit the source file in place, and it is **not** [`template-fill-pptx`](./template-fill-pptx.md) (which clones source slides and replaces text). It also does not parse an arbitrary third-party template for text-only substitution (the rejected #53 direction) — it builds every page from scratch.

**Distinct from mirror templates**: `replication_mode: mirror` (executor §1.1) keeps layout + visuals verbatim and edits text. Beautify is the inverse — content verbatim, layout redone, identity inherited.

---

## 2. Inputs

🚧 **GATE**: the user has provided:

| Input | Required | Notes |
|---|---:|---|
| Source PPTX | Yes | The deck to re-lay-out |
| Beautify scope | Optional | Density / emphasis preference — never content rewrites, and never page drops (v1 is strict 1:1) |

---

## 3. Create the Project Workspace

Match the canvas to the source so 1:1 pages and paste-back align. Determine the source aspect first — before the project exists, run `beautify_identity.py <source.pptx>` to **stdout** and read `canvas.aspect` (the formal `analysis/identity.json` is written in Step 4, after `init`) — then `init` with the matching format:

| Source aspect | Format |
|---|---|
| ≈1.778 (16:9) | `ppt169` |
| ≈1.333 (4:3) | `ppt43` |
| other | nearest format in [`canvas-formats.md`](../references/canvas-formats.md); record the source pixel size in the spec |

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source.pptx> --move
```

---

## 4. Extract Identity and Data; Assemble Inventory

Two reads off the source PPTX (text + images already exist from Step 3). Neither rewrites the deck.

**Content + images — already produced by Step 3.** `import-sources` ran `ppt_to_md` on the deck, so the **frozen content contract** is `sources/<stem>.md` (one source slide per block, in order). If the source deck contains pictures, they are already propagated to `images/` with per-slide binding in `images/image_manifest.json` (`occurrences[].slide_index`). Do **not** re-run `ppt_to_md` — it would duplicate the conversion and write images to `analysis/<stem>_files/` instead of `images/`.

**Visual identity (theme + observed sample + canvas)**:

```bash
python3 ${SKILL_DIR}/scripts/beautify_identity.py <project_path>/sources/<source.pptx> -o <project_path>/analysis/identity.json
```

| Field | Use |
|---|---|
| `theme.palette.background` / `text` / `primary` / `accent1..6` | the deck's *declared* colors |
| `theme.fonts.title` / `body` (`ea` = CJK, `latin`) | the deck's *declared* fonts |
| `observed.colors` / `observed.fonts` (`latin` / `ea`, frequency-ranked) | a usage **sample / frequency hint** — run-level fonts + explicit `srgbClr` fills across slides |
| `canvas.aspect` | drives the Step 3 format choice |

> Note: `theme` is what the deck declares; `observed` is a frequency sample of run-level overrides (not a complete style resolution — it misses `schemeClr` and master/layout inheritance, and counts chart/gradient fills). A hand-edited deck can diverge from `theme` — Step 5 recommends which to inherit and the user confirms.

**Chart + table data (for regeneration)**: read the source's chart and table *data* so they can be redrawn natively in the inherited style:

```bash
python3 ${SKILL_DIR}/scripts/template_fill_pptx.py analyze <project_path>/sources/<source.pptx> -o <project_path>/analysis/slide_library.json
```

| `slide_library.json` field | Use |
|---|---|
| `slides[].charts[]` (`chart_type` / `categories` / `series[].values`) | regenerate as a native SVG chart via the `§VII` `templates/charts/` path |
| `slides[].tables[]` (`row_count` / `column_count` / cell text) | regenerate as a native SVG table |

**Hard rule — regenerate visuals, do not carry them over**: charts / tables / images are rebuilt from their data in the inherited style, never spliced in byte-for-byte. This keeps the deck style-consistent and natively editable. **Data values are frozen** (categories / series / cell text / numbers unchanged); only their rendering is the deck's own. Pictures (`ppt_to_md`-extracted files) are reused but re-laid-out — position / crop / size follow the new layout, not the source slot. A user who wants an original element verbatim copies it across themselves.

**Assemble the inventory** — the deterministic join into one per-slide ledger, `analysis/beautify_inventory.json`, the contract Step 5 confirms and Step 7 verifies against:

```bash
python3 ${SKILL_DIR}/scripts/beautify_inventory.py <project_path>/analysis/slide_library.json \
    --images <project_path>/images/image_manifest.json -o <project_path>/analysis/beautify_inventory.json
```

If `images/image_manifest.json` does not exist because the source deck has no extracted pictures, omit `--images`. The script joins per slide: `text_blocks` (slot text + geometry), `tables` (cell grid) / `charts` (categories + series values) — the **frozen data values inlined**, so the inventory is a self-contained contract, not a pointer back to `slide_library.json` — and `images` (bound via `image_manifest` `occurrences[].slide_index`, with geometry / `usage_count`). It emits `ignored` and `needs_confirmation` as **empty arrays** — fill them with judgment before Step 5:

| Field | Fill with |
|---|---|
| `ignored` | hidden slides / shapes, master-only text, image crop / opacity / rotation / mask (not captured upstream) |
| `needs_confirmation` | combo / dual-axis / waterfall charts (only the first plot type is captured), merged-cell or multi-header tables, overcrowded pages |

```markdown
## ✅ Extraction Complete

- [x] `sources/<stem>.md` (from Step 3) holds every source slide's text, in order; extracted pictures, if any, are in `images/` + `images/image_manifest.json`
- [x] `analysis/identity.json` has theme + observed identity + canvas aspect
- [x] `analysis/slide_library.json` holds chart + table data for regeneration
- [x] `analysis/beautify_inventory.json` ledgers per-slide text / images / data + ignored + needs-confirmation
- [ ] **Next**: Step 5 — Beautify Plan (recommend & confirm)
```

---

## 5. Beautify Plan — Recommend & Confirm

⛔ **BLOCKING**: the scope is not hard-coded — same spirit as the Eight Confirmations. Recommend each item below from what the deck actually contains (the Step 4 inventory), present the plan, and **wait for the user to confirm or adjust** before writing any spec. Chat is the canonical channel.

| Plan item | Recommend from | Default lean |
|---|---|---|
| Identity source | `identity.json` `theme` vs `observed` | theme when the deck is theme-driven; `observed` (or a merge) when slides override heavily (`observed` colors / fonts dominate). State which and why |
| Preserve scope | inventory `text_blocks` / `images` / `charts` / `tables` | all text verbatim; data values frozen; pictures reused |
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

On confirmation, enter SKILL.md Step 4 as Strategist with the plan pre-resolved: lock `mode: briefing` + the content-faithful clause ([`strategist.md`](../references/strategist.md) §d Layer 1), canvas = Step 3 format, page count = source slide count (strict 1:1), color (e) + typography (g) = the confirmed identity (skip both recommendation flows), §VII = chart/table data → `templates/charts/`, §VIII = source pictures for re-layout.

**Hard rule — §IX is verbatim and 1:1**: each source slide becomes exactly one page, in source order, its text transcribed word-for-word from `sources/<stem>.md`. Do not merge, split, drop, or rewrite. Write `design_spec.md` + `spec_lock.md` per `strategist.md` §6, then hand off to the Executor.

---

## 6. Executor + Export

Run the standard pipeline (SKILL.md Steps 6–7). The Executor re-lays-out each page — hierarchy, spacing, alignment, page rhythm — using **only** the inherited palette + fonts from `spec_lock.md`, regenerates charts / tables as native SVG from the extracted data, and re-lays-out the source pictures.

```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>
```

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
| Identity | generated text / shapes use only `identity.json` colors + fonts |
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
