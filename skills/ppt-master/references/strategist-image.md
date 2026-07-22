> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Image Planning

Conditional extension for formula assets, proposed / confirmed image elaboration, AI rendering selection, and `design_spec.md §VIII` resource planning.

**Trigger**: Core first derives proposed `recommend.image_usage`. Load this module before Stage-2 direction construction when that proposal contains any non-`none` source, when the user supplied an explicit non-`none` image constraint, or when formula handling is triggered. After confirmation, the confirmed sources bound production: confirmed `none` with no formula trigger stops before resource authoring. On a formula-only path, read §3 and the formula-row rules in §4; skip non-formula planning. [`strategist.md`](./strategist.md) owns source recommendation; this module owns image-dependent candidates, production detail, and §VIII rows.

---

## 1. Proposed and Confirmed Image Plan

Before Stage 2, use proposed sources only for candidate construction. After confirmation, discard candidate-only sources, map the confirmed set through [`strategist.md`](./strategist.md) §h, and honor explicit `image_notes` roles; this module never adds a source. The confirmed non-`none` set is an allowed acquisition boundary, not coverage: use a suitable subset and leave irrelevant sources unused. Explicit must-use sources, assets, or page roles remain required. Asset inventory and judgment determine unconfirmed count, subject, placement, and composition without substituting an unconfirmed source.

For illustration, apply this precedence: confirmed `none` → explicit user intent → the locked visual style's `Illus.` propensity (`core` / `supportive` / `sparse`) → none. Propensity controls the lean, not the source or a page quota. When illustration is active, prefer one coherent motif family across hero/section anchors and local spots, but only when the confirmed assets can form that family.

**Context-first understanding for provided assets**: Do not visually scan `images/`. First infer identity, role, and crop / focus needs from source position and surrounding prose, captions / alt / titles, filename, user notes / confirmed `image_notes`, existing resource records, and CSV geometry. Inspect only one specific image when a remaining ambiguity would change selection, factual identity, page role, crop safety, or focal placement. Never inspect for inspiration, bulk-open the folder, or infer external facts / provenance from pixels. Record the result in §VIII. Leave an optional unresolved asset unused; route an unresolved must-use asset through failure recovery.

For ≥3 AI-generated same-family spots, plan one unplaced `ai` Illustration Sheet row plus one placed `slice` row per used element; only slice rows enter `spec_lock.md images`. State the intended placement shape family in the sheet reference and use separate sheets for incompatible shapes. [`image-generator.md`](./image-generator.md) §4.3 owns grid, ratio, slicing, and execution details. Stage 3 chooses the AI execution path under `image-generator.md` §7; do not pre-empt or re-pick it here.

## 2. AI Image Strategy — propose before Stage 2; lock only for confirmed `ai`

When proposed sources include `ai`, read [`image-renderings/_index.md`](./image-renderings/_index.md) before constructing Stage 2. Unless the user or active template already names a rendering, place at least three credible, distinct preset renderings across the coordinated safe/shifted/bold directions; a genuine compatibility shortfall may return fewer with a reason. Each preset `image_strategy` carries localized `rendering`, `visual`, and `mood` only. Mood includes a recognizable real-world analogy. Image colors always inherit that direction's deck HEX roles; never add an image palette or alter deck colors to rescue a rendering.

Also write one `custom_candidates.image_strategy` under the Confirm UI contract: localized `name` / `visual` / `mood`, `rendering: custom`, and non-empty localized `behavior` satisfying the catalog grammar. If it combines or borrows existing renderings, name every exact id in the visible proposal and read every corresponding `image-renderings/<id>.md` before writing the synthesis. If it is genuinely novel, read no preset file and name no catalog basis. Keep it unselected unless the user supplied it (`recommend.image_strategy: custom`); under a template it obeys inherited identity and application. Only a selected custom locks its edited behavior as `image_rendering_behavior`; when catalog material is actually used, also project the exact ids as `image_rendering_references`, otherwise omit that field. Discard an unselected candidate downstream. Ignore legacy `image_palette`.

For specialized or regulated paper-figure subjects, preserve the prompt depth required by [`image-generator.md`](./image-generator.md) §4.2 rather than shortening to a generic brief. Scan the outline for genuine image-led pages, list the proposed hero pages in Stage-2 `image_notes` so the user can retain, edit, or remove them in the same confirmation, then mark only the confirmed pages' AI rows `page_role: hero_page`; local is the default. `text_policy: embedded` is reserved for lettering that must be fused into the artwork; ordinary titles, data, labels, and prose remain editable SVG. Resolve confirmed provided assets through the context-first boundary above before writing §VIII.

## 3. Formula Asset Policy

Formula rendering is a conditional choice surfaced in Stage 3 production confirmation. Recommend one policy and let the user confirm or override it:

| Policy | Behavior | Use |
|---|---|---|
| `mixed` (default) | Render complex expressions to PNG; keep simple inline math as editable text / Unicode | Most academic, engineering, educational, and technical decks |
| `render-all` | Render every formula-worthy expression to PNG | Formula-heavy teaching / research decks where consistency matters more than editability |
| `text-only` | Keep expressions as editable text / Unicode | Business decks, light technical briefs, or an explicit editability preference |

`$...$` / `$$...$$` in source material are input signals only. Never scan output files for dollar-delimited formulas. Fractions, radicals, integrals, sums, limits, matrices, multiline derivations, and complex super/subscripts are formula-worthy; short variables, simple assignments, percentages, and expressions such as `O(n log n)` normally remain text. Never invent an equation for decoration.

For `mixed` or `render-all`, write selected source expressions to `<project_path>/images/formula_manifest.json` before writing the final spec, then run:

```bash
python3 skills/ppt-master/scripts/latex_render.py <project_path>
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
```

Follow `latex_render.py --help` for the manifest fields. The renderer writes dimensions, ratio, file, provider, and status back into it. Formula PNGs default to transparent; use an opaque final background only when the asset requires it.

## 4. Image Resource List

Add §VIII rows for the image resources actually planned from the confirmed source boundary and for every selected formula; a formula-only plan contains only formula rows. A permitted but unused source needs no row. Author each row's filename, dimensions/ratio, layout pattern, crop policy, purpose/type, acquisition, status, reference, and conditional AI fields as part of the complete Design Spec. `Acquire Via` is `ai`, `web`, `user`, `formula`, `placeholder`, or `slice`; status follows [`svg-image-embedding.md`](./svg-image-embedding.md). When a planned or explicitly required asset is not yet available, retain its row as `Pending` or `Needs-Manual`; never remove the row or change `Acquire Via` to make the Design Spec look complete. After §VIII passes final confirmation, project every placed row into `spec_lock.md images` as `<path> | source=<Acquire Via> | pattern=<Layout pattern> | crop=<adaptive|no-crop>` and omit unplaced Illustration Sheets. References describe visual intent: AI uses subject + intent + composition without repeating rendering or HEX; web uses a concrete subject plus a few positive quality descriptors; formula preserves the source LaTeX and placement intent.

**Prepared-user fast path**: For initial imported or user-supplied assets confirmed as `provided`, copy the exact `Filename` basename and derive `Dimensions` / `Ratio` from that row's `Width` / `Height` / `AspectRatio` in the latest `analysis/image_analysis.csv`; drop source-side directories, set `Acquire Via: user` and `Status: Existing`, and decide the remaining §VIII fields normally. Existing §VIII / lock / provenance-manifest records override this inference. Assets declared as `ai`, `web`, `slice`, `formula`, or manual fulfillment retain that provenance and advance through their own status lifecycle after entering `images/`; location never reclassifies them as `user / Existing`.

🚧 **GATE — non-formula rows**: read every entry in [`image-layout-patterns.md`](./image-layout-patterns.md). Copy one primary `#<id> <name>` plus any modifier names verbatim into each row; no empty, paraphrased, or invented ids. Strategist owns that pattern selection; Executor adapts its geometry while retaining the selected primary/modifier semantics, resource role, and explicit constraints. Audit the completed column against page intent: repeated left/right or top/bottom structures are valid when the narrative calls for them, but catalog families and modifiers must remain available without a usage quota.

Choose narrative intent before dimensions: hero/full-bleed, atmosphere/background, side-by-side, or accent/inline. Portrait and multi-image calculations belong to [`image-layout-spec.md`](./image-layout-spec.md). Write `Crop Policy: no-crop` whenever cropping could remove required pixels, labels, evidence, identity, or edge content; screenshots, charts, certificates/contracts, dense diagrams, logos, product markings, and formulas are common triggers rather than an exhaustive list. Otherwise write `Crop Policy: adaptive`: Executor may use complete display or a focal-safe crop, and the value never commands cropping. Formula rows use `Type: Latex Formula`, `Acquire Via: formula`, `Crop Policy: no-crop`, and `Rendered` or `Needs-Manual`.

Judge `text_policy` per AI row using [`image-generator.md`](./image-generator.md) §5.3; paper figures, academic schematics, panel comparisons, and data-axis graphics are positive triggers for reconsidering an all-`none` plan. Step 5 dispatches pending `ai` / `slice` rows to Image_Generator and pending `web` rows to Image_Searcher; formula rows bypass both.
