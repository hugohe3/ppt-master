> See [`strategist.md`](./strategist.md) for the core role and load trigger.

# Strategist Image Planning

Conditional extension for formula assets, proposed / confirmed image elaboration, AI rendering selection, and `design_spec.md §VIII` resource planning.

**Trigger**: Load before Stage-2 directions for a proposed non-`none` source, an explicit non-`none` constraint, or formulas. If confirmed `none` becomes non-`none`, load after Stage 2 without backfilling candidates. Confirmed `none` without formulas stops before resources. A formula-only path reads §3 and §4 formula rows only. [`strategist.md`](./strategist.md) owns source recommendation; this module owns image-dependent candidates, production detail, and §VIII rows.

---

## 1. Proposed and Confirmed Image Plan

Before Stage 2, use proposed sources only for candidate construction. After confirmation, discard candidate-only sources, map the confirmed set through [`strategist.md`](./strategist.md) §h, and honor explicit `image_notes` roles; this module never adds a source. The confirmed non-`none` set is an allowed acquisition boundary, not coverage: use a suitable subset and leave irrelevant sources unused. Explicit must-use sources, assets, or page roles remain required. Asset inventory and judgment determine unconfirmed count, subject, placement, and composition without substituting an unconfirmed source.

For illustration, apply this precedence: confirmed `none` → explicit user intent → the locked visual style's `Illus.` propensity (`core` / `supportive` / `sparse`) → none. Propensity controls the lean, not the source or a page quota. When illustration is active, prefer one coherent motif family across hero/section anchors and local spots, but only when the confirmed assets can form that family.

**Context-first understanding for provided assets**: Do not visually scan `images/`. First infer identity, role, and crop / focus needs from source position and surrounding prose, captions / alt / titles, filename, user notes / confirmed `image_notes`, existing resource records, and CSV geometry. Inspect only one specific image when a remaining ambiguity would change selection, factual identity, page role, crop safety, or focal placement. Never inspect for inspiration, bulk-open the folder, or infer external facts / provenance from pixels. Record the result in §VIII. Leave an optional unresolved asset unused; route an unresolved must-use asset through failure recovery.

**Default — one coherent sheet for compatible same-family spots (may override when aspect, detail, quality, or semantic needs differ)**: prefer one Illustration Sheet when several AI-generated spots can share a useful cell shape and production treatment; generate them independently when forcing one sheet would weaken a planned element. When a sheet is chosen, plan one unplaced `ai` Illustration Sheet row plus one placed `slice` row per used element; only slice rows enter `spec_lock.md images`. State the intended placement shape family in the sheet reference and use separate sheets for incompatible shapes. [`image-generator.md`](./image-generator.md) §4.3 owns grid, ratio, slicing, and execution details. Final Stage 2 chooses the AI execution path under `image-generator.md` §7; do not pre-empt or re-pick it here.

## 2. AI Image Strategy — propose only for recommended `ai`; lock any confirmed `ai`

When proposed sources include `ai`, read [`image-renderings/_index.md`](./image-renderings/_index.md) before constructing Stage 2. Unless the user or active template already names a rendering, place at least three credible, distinct preset renderings across the coordinated safe/shifted/bold directions; a genuine compatibility shortfall may return fewer with a reason. Each preset `image_strategy` carries localized `rendering`, `visual`, and `mood` only. Mood includes a recognizable real-world analogy. Image colors always inherit that direction's deck HEX roles; never add an image palette or alter deck colors to rescue a rendering.

Also write one `custom_candidates.image_strategy` under the Confirm UI contract: localized `name` / `visual` / `mood`, `rendering: custom`, and non-empty localized `behavior` satisfying the catalog grammar. If it combines or borrows existing renderings, name every exact id in the visible proposal and read every corresponding `image-renderings/<id>.md` before writing the synthesis. If it is genuinely novel, read no preset file and name no catalog basis. Keep it unselected unless the user supplied it (`recommend.image_strategy: custom`); under a template it obeys inherited identity and application. Only a selected custom locks its edited behavior as `image_rendering_behavior`; when catalog material is actually used, also project the exact ids as `image_rendering_references`, otherwise omit that field. Discard an unselected candidate downstream. Ignore legacy `image_palette`.

Post-confirmation AI activation creates no candidates: read the selected preset, or consume custom behavior/references.

For specialized or regulated paper-figure subjects, preserve the prompt depth required by [`image-generator.md`](./image-generator.md) §4.2 rather than shortening to a generic brief. Scan the outline for genuine image-led pages, list the proposed hero pages in Stage-2 `image_notes` so the user can retain, edit, or remove them in the same confirmation, then mark only the confirmed pages' AI rows `page_role: hero_page`; local is the default. `text_policy: embedded` is reserved for stable figure-internal identifiers or lettering deliberately fused into the artwork; page titles, editable data values/labels, and prose remain SVG. Resolve confirmed provided assets through the context-first boundary above before writing §VIII.

## 3. Formula Asset Policy

Formula rendering is a conditional choice surfaced in final Stage 2 production confirmation. Recommend one policy and let the user confirm or override it:

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

Add §VIII rows for the image resources actually planned from the confirmed source boundary and for every selected formula; a formula-only plan contains only formula rows. A permitted but unused source needs no row. Author each row's filename, dimensions/ratio, preferred layout suggestion, crop policy, purpose/type, acquisition, status, reference, and conditional AI fields as part of the complete Design Spec. `Acquire Via` is `ai`, `web`, `user`, `formula`, `placeholder`, or `slice`; status follows [`svg-image-embedding.md`](./svg-image-embedding.md). When a planned or explicitly required asset is not yet available, retain its row as `Pending` or `Needs-Manual`; never remove the row or change `Acquire Via` to make the Design Spec look complete. After §VIII passes final confirmation, project every placed row into `spec_lock.md images` as `<path> | source=<Acquire Via> | pattern=<Layout pattern> | crop=<adaptive|no-crop>` and omit unplaced Illustration Sheets. `source` and `crop` preserve the exact confirmed §VIII text; `pattern` preserves the non-empty free-form suggestion, including any optional hierarchical catalog ids, while remaining preferred expression rather than locked geometry.

References describe visual intent: AI uses subject + intent + composition without repeating rendering or HEX; web records exact subject, view/mood, focal/quiet region, and crop safety with positive quality cues; Image_Searcher later derives a separate short, specific provider query without rewriting this locked intent, while complete entity names or necessary disambiguation may use more words; formula preserves source LaTeX and placement intent. Any subject direction, focal placement, quiet region, or overlay-safety requirement that must affect acquisition/generation belongs in `Reference` or the matching §IX block, not only in `Layout pattern`.

**Prepared-user fast path**: For initial imported or user-supplied assets confirmed as `provided`, copy the exact `Filename` basename and derive `Dimensions` / `Ratio` from that row's EXIF-corrected `Width` / `Height` / native `AspectRatio` in the latest `analysis/image_analysis.csv`; `SourceDisplayRatio` is source-context metadata, not the bitmap crop ratio. Drop source-side directories, set `Acquire Via: user` and `Status: Existing`, and decide the remaining §VIII fields normally. Existing §VIII / lock / provenance-manifest records override this inference. Assets declared as `ai`, `web`, `slice`, `formula`, or manual fulfillment retain that provenance and advance through their own status lifecycle after entering `images/`; location never reclassifies them as `user / Existing`.

**Mandatory**: each placed row, including formulas, gets one executable `Layout pattern`. It is preferred expression, not locked geometry; optional hierarchical ids from the already-read [`image-layout-patterns.md`](./image-layout-patterns.md) must be exact. They are prompt lookup handles for Executor, not exporter effect codes. Executor may adapt the suggestion while preserving resource identity/source, must-use status, crop/content, and explicit user/template constraints; layout-only changes need no upstream rewrite.

**Default — action-bearing image plan (may override when restraint better serves the page)**: For a `hero_page` or other image-led row, name an image/content or image/shape action—not position, size, crop, or legibility scrim alone. Plain split and full bleed remain valid when clearest.

Choose narrative intent before dimensions, then apply the already-read [`image-layout-spec.md`](./image-layout-spec.md) to the actual page region. Techniques needing a cutout, blurred crop, or desaturated copy require that prepared asset. Write `Crop Policy: no-crop` whenever cropping could remove required pixels, labels, evidence, identity, or edge content; screenshots, charts, certificates/contracts, dense diagrams, logos, product markings, and formulas are common triggers rather than an exhaustive list. Otherwise write `Crop Policy: adaptive`: Executor may use complete display or a focal-safe crop, and the value never commands cropping. Formula rows use `Type: Latex Formula`, `Acquire Via: formula`, `Crop Policy: no-crop`, and `Rendered` or `Needs-Manual`.

Judge `text_policy` per AI row using [`image-generator.md`](./image-generator.md) §5.3; paper figures, academic schematics, panel comparisons, and data-axis graphics are positive triggers for reconsidering an all-`none` plan. Step 5 dispatches pending `ai` / `slice` rows to Image_Generator and pending `web` rows to Image_Searcher; formula rows bypass both.
