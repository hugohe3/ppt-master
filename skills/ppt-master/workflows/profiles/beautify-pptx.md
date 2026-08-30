---
description: Generate profile for 1:1, content-faithful re-layout of an existing deck through Default or explicit Quick execution.
---

# Beautify PPTX (Re-layout) Profile

> Generate profile, not a top-level route. [`edit-native-pptx.md`](../edit-native-pptx.md) keeps a deck's native design and edits selected pages; this profile keeps a deck's content and redoes its layout: text verbatim, source palette/fonts as the preselected recommendation (only explicit user requirements or final confirmation override them), layout, hierarchy, whitespace, and visual treatment rebuilt into a new native deck through the SVG pipeline — not a patch over the original.

**Trigger**: the user supplies a `.pptx` and asks to beautify / re-layout / 重新排版 / 美化 while keeping the content — explicit intent plus a provided file, never inferred.

**Hard rule — select one runtime before continuing**: when the request also meets [`quick-generate.md`](./quick-generate.md)'s explicit trigger, load that runtime and not `generate-pptx.md`; otherwise load [`generate-pptx.md`](../generate-pptx.md) and not Quick. The 1:1 constraints below apply in either runtime.

---

## 1. When to Run

Existing `.pptx` + beautify intent ("把这份 PPT 美化一下" / "make this deck look better"), re-layout intent ("重新排版这份 PPT，内容别动"), or paste-back intent ("重排后我要把元素贴回原来的模板").

**Hard rule — content is frozen**: every source text string is preserved exactly (no add / remove / reword / reorder); freedom lives only in layout, hierarchy, spacing, and rhythm.

**Hard rule — not a patch, not a fill**: this regenerates a native deck through the selected runtime; it never edits the source in place, is not Edit Native PPTX, and never parses a third-party template for text-only substitution (the rejected #53 direction). It is the inverse of a `replication_mode: mirror` template ([`executor-structured.md`](../../references/executor-structured.md) §1.1), which keeps layout and edits text. When the authoritative input is a raster page roster whose visible layout must be preserved, activate the Quick-only [`image-to-pptx.md`](./image-to-pptx.md) instead; the two fidelity profiles never compose.

**When this profile is wrong**: it preserves page count and order 1:1 — "keep this deck, lay it out better". Merging, splitting, reordering, re-outlining, or re-paginating for fit ("keep every word but split a crowded page") changes the page breakdown: convert with [`ppt_to_md`](../../scripts/source_to_md/ppt_to_md.py) and use ordinary Quick or Default instead. The deciding question: is the source's page split information to preserve, or the previous author's structure to improve?

---

## 2. Inputs

🚧 **GATE**: the source PPTX (required) and an optional beautify scope — density / emphasis preference, never content rewrites or page drops.

---

## 3. Create the Project Workspace

Match the canvas to the source so 1:1 pages and paste-back align: before the project exists, run `beautify_identity.py <source.pptx>` to stdout, read `canvas.aspect`, and pick `ppt169` (≈1.778), `ppt43` (≈1.333), or the exact source `width_px`x`height_px` without `--format`.

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> [--format <format>]                 # Default
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> [--format <format>] --quick-generate # Quick — run exactly one init
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source.pptx>
```

---

## 4. Extract Identity and Data; Assemble Inventory

`import-sources` already wrote the standard PPTX intake bundle under `analysis/` (for an older project, `pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis` once) and ran `ppt_to_md`, so the **frozen content contract** is `sources/<stem>.md` (one source slide per block, in order) and extracted pictures are in `images/` with per-slide binding in `images/image_manifest.json` (`occurrences[].slide_index`); never re-run `ppt_to_md`.

**Visual identity** — read `analysis/<stem>.identity.json`: `theme.palette.background` / `text` / `primary` / `accent1..6` and `theme.fonts.title` / `body` (`latin` / `ea` / `cs`, with `scripts` mapping `Hans` / `Hant` / `Jpan` / `Hang` supplemental faces — use the matching script when `ea` is empty) are what the deck declares; `theme.sizes.title` / `body` (pt) are the master placeholder defaults, `body` being the coarse level-1 value that commonly over-reads, with `theme.sizes.body_levels` as the full ramp for reference; `observed.colors` / `observed.fonts` / `observed.sizes_pt` are frequency-ranked samples of run-level overrides (not a complete style resolution — they miss `schemeClr` and inheritance and count chart/gradient fills); `layout_sizes_pt` is a reference fact only; `canvas.aspect` drove Step 3. A hand-edited deck can diverge from `theme`; Step 5 resolves which to use.

**Hard rule — regenerate visuals, do not carry them over**: charts / tables / images are rebuilt from their data in the effective style, never spliced byte-for-byte; data values are frozen, only rendering is the deck's own; pictures are reused but re-laid-out. A user who wants an original element verbatim copies it across themselves.

**Optional source-SVG visual reference**: when the deck has complex vector decoration or a visual language colors/fonts cannot capture, build a read-only reference package for understanding style, not a carry-over path:

```bash
python3 ${SKILL_DIR}/scripts/pptx_to_svg.py <project_path>/sources/<source.pptx> -o <project_path>/analysis/source_svg_import
python3 ${SKILL_DIR}/scripts/extract_svg_assets.py <project_path>/analysis/source_svg_import/svg-flat --icons-dir <project_path>/analysis/source_svg_import/icons --icon-namespace imported --inplace --id-prefix source_flat --min-decoration-bytes 3000 --clean-stale
```

Use the cleaned `svg-flat/slide_*.svg` pages and `svg-flat_vector_asset_inventory.json` in Step 5; open an individual `icons/imported/*.svg` only when a candidate may be promoted or materially affects the style decision. By default do not copy candidates into `icons/`, list them as output assets, or preserve decorations byte-for-byte. **Optional reuse gate**: a non-text brand/logo/motif/decorative candidate may be promoted to `<project_path>/icons/imported/` and referenced with `<use data-icon="imported/<name>"/>` — Default lists it in Step 5 and waits for confirmation, Quick decides directly and stops only when frozen facts lack a lossless path; never promote text-bearing groups, charts/tables, page layouts, or dense composites.

**Assemble the inventory** — the deterministic per-slide ledger Step 5 resolves and Step 7 verifies against:

```bash
python3 ${SKILL_DIR}/scripts/beautify_inventory.py <project_path>/analysis/<stem>.slide_library.json --images <project_path>/images/image_manifest.json -o <project_path>/analysis/beautify_inventory.json
```

Omit `--images` when no pictures were extracted. It joins `text_blocks`, `tables`, `charts`, `diagrams` (SmartArt nodes + hierarchy + source layout), and `images` (bound through `image_manifest` `occurrences[].slide_index`, with geometry and `usage_count`) per slide with frozen values inlined, and emits empty `ignored` and `needs_confirmation` arrays to fill with judgment: `ignored` — hidden slides/shapes, master-only text, image crop/opacity/rotation/mask; `needs_confirmation` — unreadable SmartArt, combo / dual-axis / waterfall charts, merged-cell or multi-header tables, density outliers (overcrowded or near-empty). SmartArt keeps its wording and relationships and is redrawn as ordinary editable shapes, never regenerated natively.

**Mandatory — bounded inventory reads**: the complete inventory is the validation ledger, not the authoring prompt. Read `beautify_inventory.py <inventory> --summary`, then `--page <N>`, adding `--with-geometry` only for structural ambiguity; never bulk-read either complete file during authoring.

```markdown
## ✅ Extraction Complete
- [x] `sources/<stem>.md` holds every slide's text in order; pictures in `images/` + `image_manifest.json`
- [x] `analysis/<stem>.identity.json`, `<stem>.slide_library.json`, `source_profile.json` present
- [x] `analysis/beautify_inventory.json` ledgers per-slide text / images / data + ignored + needs-confirmation
- [ ] **Next**: Step 5 — resolve Beautify decisions in the selected runtime
```

---

## 5. Beautify Decisions

### Quick branch

Do not run the Default confirmation flow. Apply the same inventory interpretation, identity judgment, and body-size method directly in active context: explicit user requirements are authoritative, otherwise the source identity is the default; resolve `ignored` and `needs_confirmation` without a payload, Design Spec, lock, or substitute plan; if a flagged complex object cannot be regenerated without losing frozen facts, stop as a hard prerequisite instead of simplifying. **Mandatory — close the transient state before §6**: exact source-order roster and one core message per page; identity, palette, fonts, body size, and type-role anchors; per-page density, body frame, primary zone, and composition direction; frozen relationships, reading path, neighbor/section rhythm, and ending; usable local resources and decided notes / motion / audio / image / icon / formula / Chart-Table / verification outcomes. Keep it transient, then continue to §6 Quick.

### Default branch — Recommend & Confirm

⛔ **BLOCKING**: recommend each item from what the deck actually contains, present the plan, and wait for the user to confirm or adjust before writing any spec. The **visual re-confirm** goes through Generate Step 4's selected surface with the full field set seeded from the source — every field pre-filled with the inherited default and left editable (recommend keeping identity, never remove the place to override). The **structural scope** stays in chat:

| Plan item | Recommend from | Default lean |
|---|---|---|
| Identity source | `theme` vs `observed` | Present both as color / typography candidates; theme first when the deck is theme-driven, observed first when slides override heavily; say why |
| Preserve scope | inventory `text_blocks` / `images` / `charts` / `tables` / `diagrams` | All text verbatim; data values and SmartArt relationships frozen; pictures reused |
| Ignored | inventory `ignored` | Name them so the user sees what drops |
| Needs confirmation | inventory `needs_confirmation` | Flag complex charts and overcrowded pages; ask how to handle |
| Verification level | deck size / risk | Recommend the Step 7 per-page checks; user sets strictness |

**Hard rule — content is frozen, not the scope decisions**: text and chart/table/cell values are non-negotiable; which identity to inherit, what to ignore, and how to treat flagged items are recommend-then-confirm, never silently decided. **Name the v1 ceiling honestly**: an overcrowded page improves within the page as-is (no information-overload relief — flag it for manual split); paste-back keeps confirmed palette + font declarations but guarantees neither coordinate alignment nor font availability; combo / dual-axis / waterfall charts and merged-cell tables are best-effort from captured data and flagged.

**Visual re-confirm**: apply Step 4's surface decision; in the UI branch use `confirm_ui/recommendations.stage1.json` / `.stage2.json` at the same two handoffs and the same server, in the chat branch present the same stages without a server or `result.json`. Rows abbreviated; follow the four-locale contract ([`confirm-surface.md`](../../references/confirm-surface.md)) and omit `english` for English sources:

```json
{
  "primary_language": "<source main language>",
  "recommend": {"canvas": "<step3-canvas-id>", "mode": "custom", "visual_style": "custom", "image_strategy": "custom", "icons": "<sensible default icon library>", "image_usage": ["provided"]},
  "page_count": {"value": "<source-slide-count>"},
  "audience": {"value": "<deck's apparent audience, or a concrete provisional one>"},
  "communication_intent": {"value": "<open prose inferred from the deck>"},
  "audience_outcome": {"value": "<know / understand / decide / do>"},
  "core_message": {"value": "<the deck-wide claim already present>"},
  "delivery_context": {"value": "<presenter-led / reader-led / hybrid / recorded; occasion if inferable>"},
  "artifact_afterlife": {"value": "<review / approval / archive / hand-off / reuse / none planned>"},
  "content_divergence": {"value": "keep source wording and page structure verbatim", "locked": true},
  "design_directions": {"selected": 0, "candidates": [
    {"id": "source-replica", "name_en": "Source replica (recommended)", "mode": "custom", "mode_behavior_zh": "briefing 基底；逐页结构、顺序与文字 1:1 逐字不变。", "visual_style": "custom", "visual_style_behavior_zh": "复刻源 PPT 视觉身份与版式。", "icons": "…",
     "color": {"palette": {"background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..."}},
     "typography": {"heading": {"primary": "…"}, "body": {"primary": "…"}, "body_size": "<dominant observed.sizes_pt × 4/3, as px>"},
     "image_strategy": {"rendering": "custom", "behavior_zh": "…"}},
    {"id": "alternative-a", "...": "same shape; body_size = canvas-appropriate baseline"},
    {"id": "alternative-b", "...": "same shape"}
  ]}
}
```

- **Recommend keep, allow override**: pre-fill the communication contract from the source's apparent audience and purpose (composite purposes in prose; examples are hints, never a `primary_job` selector) and canvas / mode / visual style / icons / image strategy with the source-faithful default (mode `briefing`, `image_usage` `provided`). The only true non-choices are frozen text and strict 1:1 page count; `content_divergence` is seeded verbatim with `locked: true` (the UI renders it read-only and restores it on every submit). A request to reshape wording or structure routes to the main pipeline.
- **The pre-selected default is the source replica** (`selected: 0`): the candidate that best replicates the source's `theme` / `observed` style. Author the other candidates with the same content-driven judgment the Strategist uses from scratch (color §e, typography §g) — palette and font pairing chosen for this deck's content, ≥3 meaningful candidates, no manufactured pairings to fill a quota; `primary` follows the source language, `english` only when that language is not English.
- **`body_size` is load-bearing and the replica follows the source's own size**: seed it from the dominant `observed.sizes_pt` value converted to px (`× 4/3` — a 20pt body becomes `26.67`; seeding bare `20` shrinks it ~25%, the pt-as-px trap); the confirm page writes that px to `result.json` and the chat branch retains it, with no second conversion and no `body_size_pt`. The most-frequent-size proxy counts titles, captions, and chart labels too, so cross-check it against the page's actual body blocks and prefer the size body paragraphs visibly render at. Seed chain: `observed` → `theme.sizes.body` (a level-1 default that over-reads; treat as an upper-ish guess) → the consumption-mode baseline (`text` 20 / `balanced` 24 / `presentation` 32 px); `body_levels` and `layout_sizes_pt` are reference context for judging a saner value, never auto-seeds. The canvas hint is a sanity range, not the seed — when the source size lands far outside it, surface that to the user rather than snapping. Alternatives may use the consumption-mode baseline.

Run Step 4's confirmation orchestration unchanged. In the UI branch read `confirm_ui/result.json` exactly once after the final wait and run `--shutdown` before Step 6; in the chat branch retain the visible final summary. Then enter Step 4 as Strategist with the plan pre-resolved under the two invariants — the content-faithful clause ([`strategist.md`](../../references/strategist.md) §d Layer 1) and page count = source slide count — writing the confirmed state completely into `design_spec.md` (mode, canvas, visual style, color + typography incl. `body_size`; skip both recommendation flows). §VII holds only `Page | Family | Template | Usage` rows for selected `chart` / `table` references projected into `spec_lock.md page_visualizations`; qualitative relationships stay in §IX; §VIII holds source pictures for re-layout.

**Hard rule — §IX is verbatim and 1:1**: each source slide becomes exactly one page, in order, its text transcribed word-for-word from `sources/<stem>.md`. Complete and audit `design_spec.md`, then author `spec_lock.md` per `strategist.md` §6 before handing off.

---

## 6. Author + Export

**Quick**: follow [`quick-generate.md`](./quick-generate.md) §3–4 with the inventory as the exact roster and frozen-content contract; keep source order, hand-author every page, run the lockless final checker, export with `--quick-generate`; no Confirm UI, Design Spec, lock, first-page gate, or `finalize_svg.py`. **Long-deck review cadence (may adapt)**: after about five pages or at a section boundary, reread only the inventory summary/current-page views and cross-page anchors — no checker, no gate — and send one `authored/total` status per batch.

**Default**: run [`generate-pptx`](../generate-pptx.md) Steps 6–7. The Executor re-lays-out each page from the lock's semantic anchors plus page/source/template context (page-local colors, gradients, effects, and export-safe faces need no lock rows), regenerates charts/tables as native SVG from the extracted data, and re-lays-out the source pictures. Step 7 owns the serial post-processing commands, gates, and artifacts.

---

## 7. Validate Output

`python3 ${SKILL_DIR}/scripts/source_to_md/ppt_to_md.py <project_path>/exports/<output.pptx>` — every source text string appears unaltered; chart categories / series / table cells match exactly; slide count equals the source; charts/tables are native SVG in the effective palette; text and shapes use the effective colors and fonts; paste-back elements retain palette and font declarations (alignment and font availability not guaranteed).

```markdown
## ✅ Beautify Complete
- [x] Content + data values verbatim (read-back matches the source)
- [x] 1:1 page count preserved
- [x] Effective colors + fonts applied consistently
- [x] Charts / tables regenerated as native SVG
- [x] Native PPTX exported to `exports/`
```

---

## Current Boundary

Supported: re-layout with verbatim text; source palette/fonts as the preselected recommendation with user-approved overrides; strict 1:1 pages; charts/tables regenerated from extracted data; re-laid-out source pictures. Not in v1: re-pagination; batch / multi-deck beautification. Out of scope: carrying charts / tables / images over byte-for-byte (the user copies originals manually); silent visual-style or identity deviation.
