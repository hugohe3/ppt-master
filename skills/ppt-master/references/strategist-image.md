> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Image Planning

Conditional extension for formula assets, proposed / confirmed image elaboration, AI rendering selection, and `design_spec.md §VIII` resource planning.

**Trigger**: Core first derives proposed `recommend.image_usage`. Load this module before Stage-2 direction construction when that proposal contains any non-`none` source, when the user supplied an explicit non-`none` image constraint, or when formula handling is triggered. After confirmation, the confirmed sources bound production: confirmed `none` with no formula trigger stops before resource authoring. On a formula-only path, read §3 and the formula-row rules in §4; skip non-formula planning. [`strategist.md`](./strategist.md) owns source recommendation; this module owns image-dependent candidates, production detail, and §VIII rows.

---

## 1. Proposed and Confirmed Image Plan

Before Stage 2, use proposed sources only for candidate construction. After confirmation, discard candidate-only sources, map the confirmed set through [`strategist.md`](./strategist.md) §h, and honor every explicit role or page instruction in `image_notes`; this module never adds a source. The confirmed set is a production requirement, not a fresh candidate list: represent every confirmed non-`none` source at least once. Asset inventory and later aesthetic judgment may shape the unconfirmed count, subject, placement, and composition, but must not delete, substitute, or demote a confirmed source.

For illustration, apply this precedence: confirmed `none` → explicit user intent → the locked visual style's `Illus.` propensity (`core` / `supportive` / `sparse`) → none. Propensity controls the lean, not the source or a page quota. When illustration is active, prefer one coherent motif family across hero/section anchors and local spots, but only when the confirmed assets can form that family.

For ≥3 AI-generated same-family spots, plan one unplaced `ai` Illustration Sheet row plus one placed `slice` row per used element; only slice rows enter `spec_lock.md images`. State the intended placement shape family in the sheet reference and use separate sheets for incompatible shapes. [`image-generator.md`](./image-generator.md) §4.3 owns grid, ratio, slicing, and execution details. Stage 3 chooses the AI execution path under `image-generator.md` §7; do not pre-empt or re-pick it here.

## 2. AI Image Strategy — propose before Stage 2; lock only for confirmed `ai`

When proposed sources include `ai`, read [`image-renderings/_index.md`](./image-renderings/_index.md) before constructing Stage 2. Unless the user or active template already names a rendering, place at least three credible, distinct preset renderings across the coordinated safe/shifted/bold directions; a genuine compatibility shortfall may return fewer with a reason. Each preset `image_strategy` carries localized `rendering`, `visual`, and `mood` only. Mood includes a recognizable real-world analogy. Image colors always inherit that direction's deck HEX roles; never add an image palette or alter deck colors to rescue a rendering.

Also write one `custom_candidates.image_strategy` under the Confirm UI contract: localized `name` / `visual` / `mood`, `rendering: custom`, and non-empty localized `behavior` satisfying the catalog grammar. If it combines or borrows existing renderings, name every exact id in the visible proposal and read every corresponding `image-renderings/<id>.md` before writing the synthesis. If it is genuinely novel, read no preset file and name no catalog basis. Keep it unselected unless the user supplied it (`recommend.image_strategy: custom`); under a template it obeys inherited identity and application. Only a selected custom locks its edited behavior as `image_rendering_behavior`; when catalog material is actually used, also project the exact ids as `image_rendering_references`, otherwise omit that field. Discard an unselected candidate downstream. Ignore legacy `image_palette`.

For specialized or regulated paper-figure subjects, preserve the prompt depth required by [`image-generator.md`](./image-generator.md) §4.2 rather than shortening to a generic brief. Scan the outline for genuine image-led pages, list the proposed hero pages in Stage-2 `image_notes` so the user can retain, edit, or remove them in the same confirmation, then mark only the confirmed pages' AI rows `page_role: hero_page`; local is the default. `text_policy: embedded` is reserved for lettering that must be fused into the artwork; ordinary titles, data, labels, and prose remain editable SVG. Analyze confirmed provided assets before writing §VIII.

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

Add §VIII for every confirmed non-`none` source and selected formula; a formula-only plan contains only formula rows. Fill the scaffold's filename, dimensions/ratio, layout suggestion/pattern, purpose/type, acquisition, status, reference, and conditional AI fields. `Acquire Via` is `ai`, `web`, `user`, `formula`, `placeholder`, or `slice`; status follows [`svg-image-embedding.md`](./svg-image-embedding.md). When an asset is not yet available, retain its confirmed-source row as `Pending` or `Needs-Manual`; never remove the row or change `Acquire Via` to make the Design Spec look complete. Only after §VIII passes the final-confirmation fidelity gate, project the same planned filenames and acquisition sources into `spec_lock.md images`; do not redesign the image plan while writing the lock. References describe visual intent: AI uses subject + intent + composition without repeating rendering or HEX; web uses a concrete subject plus a few positive quality descriptors; formula preserves the source LaTeX and placement intent.

🚧 **GATE — non-formula rows**: read every entry in [`image-layout-patterns.md`](./image-layout-patterns.md). Copy one primary `#<id> <name>` plus any modifier names verbatim into each row; no empty, paraphrased, or invented ids. For decks with at least four image-bearing pages, use an Image-as-Canvas + Native Overlay pattern at least once unless every image is purely a cover, divider, or atmospheric backdrop; record the legitimate exception below the table. Reconsider a plan that collapses every row to the same left/right or top/bottom split.

Choose narrative intent before dimensions: hero/full-bleed, atmosphere/background, side-by-side, or accent/inline. Only side-by-side containers follow native ratio; portrait and multi-image calculations belong to [`image-layout-spec.md`](./image-layout-spec.md). Most assets are croppable. Add `no-crop` in `spec_lock.md images` only for screenshots, charts, certificates/contracts, dense diagrams, and every formula; formula rows use `Type: Latex Formula`, `Acquire Via: formula`, and `Rendered` or `Needs-Manual`.

Judge `text_policy` per AI row using [`image-generator.md`](./image-generator.md) §5.3; paper figures, academic schematics, panel comparisons, and data-axis graphics are positive triggers for reconsidering an all-`none` plan. Step 5 dispatches pending `ai` / `slice` rows to Image_Generator and pending `web` rows to Image_Searcher; formula rows bypass both.
