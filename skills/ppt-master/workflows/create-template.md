---
description: Generate a new layout or deck template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate a complete set of reusable PPT templates for the **global template library**.

> This workflow is for **library asset creation**, not project-level one-off customization. The output must be reusable by future PPT projects and discoverable from the appropriate index file.

> **Boundary against template-fill**: this workflow does not fill content into a PPTX and does not directly output the user's final generated deck. It creates a reusable `templates/<kind>/<id>/` package. To generate a deck from that package, the user must provide the resulting template directory path to the main SKILL.md pipeline.

> **Companion workflow**: identity-only locking (colors / typography / logo / voice without SVG pages) is handled by [`create-brand.md`](./create-brand.md). Use that when the user wants brand identity but free page layout; use this when fixed page structures are required.

## Kind decision — deck (default) vs layout

This workflow produces one of two kinds of templates depending on whether the source PPT carries a specific brand identity:

| Kind | When | Output dir | What `design_spec.md` writes |
|---|---|---|---|
| **deck** (default) | Source is a specific organization's branded PPT (e.g. company report, university defense template); the visual identity is part of the replica | `templates/decks/<id>/` | Full segments: identity + structure + middle |
| **layout** | Source is a generic stylistic template (no specific brand); only the structural skeleton should be reusable; color / typography decided per-deck downstream | `templates/layouts/<id>/` | Structure segments only (canvas / page structure / page types / SVG roster); identity segment omitted |

Default to **deck** unless the user explicitly says "structure only" / "layout only" / "no brand identity". When in doubt, lean deck — losing identity later is easy; reconstructing it from a layout-mode strip is not. See [`docs/zh/templates-architecture.md`](../../../docs/zh/templates-architecture.md) for the full kind / schema / fusion model.

## Process Overview

```
Reference Intake & Analysis -> Basic Norm Extraction -> Fact-Based Brief Proposal -> User Confirmation Gate -> Create Directory + Invoke Template_Designer -> Validate Assets -> Register Index -> Output
```

The first three steps derive the brief from facts, not guesses. **No final template directory may be created and no template SVG / `design_spec.md` may be written until `[TEMPLATE_BRIEF_CONFIRMED]` is emitted in Step 3.** Reference-analysis intermediates produced by `pptx_template_import.py` (typically under `/tmp/pptx_template_import/`) are explicitly **not** subject to this gate — they are temporary workspaces feeding Step 2.

---

## Step 1: Reference Intake & Analysis

Branch by the type of reference source the user supplied. This step produces analysis artefacts only — it does **not** create the final template directory, write `design_spec.md`, or touch any template index.

### Input source taxonomy

| Type | What the user supplied | Tool / read path | Replication modes available |
|------|-------------------------|------------------|------------------------------|
| **A** `.pptx` reference | A `.pptx` file path | `pptx_template_import.py` → `manifest.json` + `native_structure.json` + `source_template.pptx` + layered/flat SVGs + `assets/` | `standard` / `fidelity` / `mirror` |
| **B** Existing SVG assets | `projects/<x>/svg_output/`, `templates/layouts/<existing>`, or a loose `.svg` folder | `ls` + `Read` each `*.svg`; plus `design_spec.md` / `spec_lock.md` if present | `standard` / `fidelity` (AI visual clustering) / `mirror` (direct 1:1 copy) |
| **C** Image / visual references | Screenshot folder, single image, PDF pages | `ls` + `Read` each file (multimodal visual recognition) | `standard` only |
| **D** No reference source | Verbal description only ("McKinsey style", "tech blue", "dark minimal") | — | `standard` only |

`fidelity` and `mirror` are not available for type C / D — visual references and verbal-only briefs cannot drive page-by-page replication. Type A is the canonical path: `manifest.json` page-type candidates and the layered `svg/` workspace anchor cluster detection (fidelity) and verbatim copy (mirror) with factual data. Type B is supported with caveats:

- **mirror on type B** — direct 1:1 copy. B's SVGs are already self-contained (one file per page, equivalent to `svg-flat/slide_*.svg`). Page-type for the `<NNN>_<page_type>.svg` filename is read from the source filename when it follows the PPT Master naming convention (`01_cover.svg` → `cover`, `03a_content_two_col.svg` → `content`); fall back to `content` otherwise. Particularly natural when the source is `templates/layouts/<existing>` and the user wants to fork an existing template.
- **fidelity on type B** — clustering relies on the AI's visual judgement of the SVGs; there is no `manifest.json.pageTypeCandidates` to anchor it. Variant count and grouping are more subjective and may need iteration. If the input is already a PPT Master template (`templates/layouts/<existing>`), parse the existing variant filenames (`03a_content_two_col` etc.) as authoritative cluster hints rather than re-clustering visually.

**Replication mode boundary**: `standard` / `fidelity` / `mirror` are construction choices for this workflow only. They decide how the template package is created from the reference source; they do not create a downstream generation route, and `mirror` must not force future decks to preserve the source page count or page order.

### 1A. `.pptx` reference

Run the unified preparation helper:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py "<reference_template.pptx>"
```

This produces, in one workspace:

- `manifest.json` — single source of truth: slide size, theme colors, fonts, per-master theme summaries, asset inventory, placeholder metadata, SVG file paths, per-slide / per-layout / per-master metadata, page-type candidates
- `native_structure.json` — portable machine contract: stable master/layout keys, source package parts, layout picker names, placeholder type/index/geometry, source hash, and a preserve-vs-rebuild recommendation
- `source_template.pptx` — byte-preserved source package paired with `native_structure.json`; required for downstream `pptx_structure.mode: preserve`
- `summary.md` — short human-readable digest derived from manifest.json (for quick scanning only)
- `assets/` — extracted reusable image assets; `manifest.json` owns the asset-name mapping and SVG `href` values reuse that mapping
- `svg/` — **primary view** (layered template view):
  - `svg/master_*.svg` — every slide master in the deck rendered once, including masters that no sample slide currently uses (template packages routinely ship more masters than the visible samples reference)
  - `svg/layout_*.svg` — every slide layout in the deck rendered once (its own contribution; master shapes do **not** repeat here)
  - `svg/slide_NN.svg` — each slide's own shapes and slide-local background; master / layout shapes and backgrounds are **not** inlined here
  - `svg/inheritance.json` — which layout & master each slide consumes
- `svg-flat/` — **companion view** (one self-contained SVG per slide):
  - `svg-flat/slide_NN.svg` — master + layout + slide painted into a single SVG so opening any slide on its own shows the full page like PowerPoint would. Use this for previews / screenshot pipelines / "what does the slide actually look like" sanity checks.
- The default `--inheritance-mode both` emits both views. Pass `layered` to skip `svg-flat/`, or `flat` for round-trip use cases (legacy: `svg/` becomes self-contained slides without the master/layout/inheritance files).

Import fidelity rules:

- Placeholder metadata is recorded in `manifest.json`; master / layout SVGs show lightweight dashed guides with labels only in `svg/`, not in `svg-flat/`.
- Charts, SmartArt, diagrams, and OLE objects are typed placeholders in `svg/`. In `svg-flat/`, they use a preview image with a small badge when one exists; otherwise they stay visible as placeholders. Tables are converted to real SVG.
- Missing media and external linked images fail the import. EMF / WMF Office vector media are converted to PNG previews when supported by the local toolchain; otherwise the import fails.

It is a reconstruction aid, not a final direct template conversion.

**Vector illustration readability pass**:

Before the Template_Designer reads imported SVGs, factor large decorative vector groups into project icon assets so the working SVGs stay readable while export remains native shapes. Run this on the SVG view that will feed the selected replication path:

```bash
# standard / fidelity analysis path
python3 skills/ppt-master/scripts/extract_svg_assets.py "<import_workspace>/svg" --icons-dir "<import_workspace>/icons" --inplace --id-prefix layered --min-decoration-bytes 3000 --clean-stale

# mirror creation path
python3 skills/ppt-master/scripts/extract_svg_assets.py "<import_workspace>/svg-flat" --icons-dir "<import_workspace>/icons" --inplace --id-prefix flat --min-decoration-bytes 3000 --clean-stale
```

The source SVGs in `<import_workspace>/svg/` / `<import_workspace>/svg-flat/` are rewritten in place with compact `<use data-icon="..."/>` placeholders. Extracted assets live directly under `<import_workspace>/icons/`; `icons/` must contain only icon/vector assets, not rewritten page SVGs or inventories. The inventory is written beside the processed SVG directory (for example `<import_workspace>/svg_vector_asset_inventory.json`). The existing icon embedding path re-inlines the extracted assets before final export, preserving multi-color artwork and non-square viewBox geometry as native SVG shapes. Text-bearing groups are never extracted; text must stay readable/editable in the working SVG. Extraction triggers on either many drawable elements or a large pure-vector XML block, so long single-path illustrations are factored out too. Pure-vector decoration runs inside text-bearing groups use a lower size threshold, allowing card borders and decorative paths to be extracted without hiding text. Referenced defs (`gradient` / `pattern` / `filter` / `clipPath` / `marker`) are copied into each asset and namespaced so the asset is self-contained after re-inline. If both layered and flat views are processed into the same icon directory, keep distinct `--id-prefix` values to avoid asset ID collisions. `--clean-stale` removes only stale generated assets for the current SVG filenames and prefix; it is safe in this import workspace but should not be used against a shared hand-curated icon directory without a specific prefix.

**Read order during analysis** (read everything below before composing Step 2):

1. `manifest.json` (factual metadata: slide size, theme, assets, layouts, masters, slide page-types)
2. `native_structure.json` (stable native keys, source layout names/placeholders, relationship completeness, recommended structure strategy)
3. cleaned `svg/master_*.svg` and `svg/layout_*.svg` — read these **before** any slide SVG; they show the deck's shared visual language (background, headers, footers, decorative bars). This is what the new template's fixed structure should adapt from.
4. `svg/inheritance.json` — confirms which slide uses which layout/master
5. exported `assets/`
6. cleaned slide SVG references from `svg/` — content unique to each slide; consult after the master/layout language is understood
7. `summary.md` only as a quick orientation aid
8. user-provided screenshots or the original PPTX only for visual cross-checking

Interpretation rule (carries forward into Steps 2 and 4):

- `manifest.json` is the source of truth for slide size, theme colors, fonts, background inheritance, reusable asset inventory, unique layout/master structure, and slide reuse relationships
- `native_structure.json` is the source of truth for native PowerPoint identity: stable layout keys, picker names, parent masters, placeholder types/indices, and the source-package hash
- `summary.md` is a quick scan; never treat it as the canonical fact source — go back to `manifest.json` if anything is unclear
- exported `assets/` are the canonical reusable image pool — `<image>` references in `svg/` already point at these files directly
- exported `icons/*.svg` are the canonical reusable vector illustration pool, but they are **not** part of the default read set. Read the cleaned SVGs and `*_vector_asset_inventory.json` first; open a specific icon SVG only when the cleaned page or inventory shows that the extracted asset is relevant to the current design decision. This is what makes the SVG work surface smaller.
- cleaned `svg/master_*.svg` / `svg/layout_*.svg` are the **primary source for fixed structural design** — recurring backgrounds, page chrome, decorative motifs that the template should preserve. The new template's `01_cover` / `02_chapter` / `03_content` / `04_ending` typically inherit elements from these layers.
- cleaned `svg/slide_NN.svg` shows page-specific content — useful for judging composition rhythm and content density, not for fixed structure. Read every slide regardless of count.
- cleaned `svg-flat/slide_NN.svg` is for human preview and screenshot comparison; do not treat duplicated master/layout chrome inside flat slides as separate reusable template structure.
- screenshots remain useful for judging composition and style, but should not override extracted factual metadata unless the import result is clearly incomplete

### Basic norm extraction (mandatory when reference content exists)

Before composing Step 2, extract the template's reusable norms from the previous content. These norms are not generic design advice; they are the source deck's observable operating rules, and they must flow into `design_spec.md`.

| Norm area | Extract from | Record as |
|---|---|---|
| Canvas / page geometry | `manifest.json` slide size, SVG `width` / `height` / `viewBox` | `[fact]` canvas format, pixel dimensions, source `viewBox`, and aspect ratio |
| Identity system | theme colors, font usage, logo / emblem assets, recurring backgrounds | `[fact]` when imported; `[suggested]` only for visual estimates |
| Layout grammar | masters / layouts, repeated chrome, margins, columns, card grids, section dividers | Template-specific rules, not generic spacing boilerplate |
| Image system | image crops, masks, full-bleed zones, hero-image placement, mosaic rules, caption / overlay treatment | Template-specific image-placement rules with source examples |
| Density rhythm | title scale, content block count, whitespace balance, dense vs. breathing pages | Page-type guidance for Strategist / Executor |
| Page roster semantics | cover / TOC / chapter / content / ending variants and their intended content slots | `design_spec.md §V Page Roster` rows |
| Asset policy | source images / icons / textures that are part of the template vs. sample-only content | `design_spec.md §VI Assets` or omit sample-only assets |
| Native PowerPoint structure | `native_structure.json` strategy, masters/layouts, picker names, placeholder type/index, source slide mapping | Preserve contract when reusable; otherwise rebuild one master plus semantic layouts |

Distinguish observed facts from template rules: "`slide_07` uses a left photo crop" is a fact; "content pages may use a left photo rail for location / product / case-study pages" is the reusable rule.

**Hard read gate** (`standard` / `fidelity` modes — `mirror` differs, see below):

- The agent MUST finish reading every cleaned `master_*.svg`, `layout_*.svg`, and `slide_*.svg` file from the layered `svg/` view before moving on to Step 2
- The agent MUST list the read master / layout / slide filenames inside the Step 2 brief proposal as proof of the gate

Do **not** treat the imported PPTX or exported slide SVGs as direct final template assets — Step 4 reconstructs them as a clean, maintainable PPT Master template package, not a 1:1 shape translation.

> **Mirror-mode fast path** — when the user has indicated mirror replication (verbatim copy of every source slide):
> - Run the vector illustration readability pass on `svg-flat/`, then read **only** the cleaned flat `slide_*.svg` files (the self-contained, what-PowerPoint-shows view) and `manifest.json` (for theme colors, fonts, asset inventory).
> - Skip `svg/master_*.svg` / `svg/layout_*.svg` / `svg/inheritance.json` — chrome / content separation is irrelevant in mirror mode (no placeholder insertion happens).
> - Mirror is explicitly a visual-verbatim copy flow: every slide becomes a template page as-is, except that large vector illustrations may be factored into `icons/` placeholders for maintainability. The "reconstruct, don't translate" rule applies to `standard` / `fidelity` only.

### 1B. Existing SVG assets

If the source SVG directory contains complex vector blobs, first copy the SVG files into a throwaway analysis workspace and run the same readability pass there. Do **not** rewrite the user's original source directory in place.

```bash
python3 skills/ppt-master/scripts/extract_svg_assets.py "<svg_analysis_workspace>/svg" --icons-dir "<svg_analysis_workspace>/icons" --inplace --id-prefix source --min-decoration-bytes 3000 --clean-stale
```

Then `ls` the analysis workspace and `Read` every cleaned `*.svg` to extract:

- canvas size (`viewBox` on the root `<svg>`)
- recurring colors (`fill` / `stroke` values; identify the dominant 2–4 hex codes as candidate theme colors)
- fonts (`font-family` attributes on `<text>`)
- placeholder usage (existing `{{...}}` strings, if any)
- structural decoration (recurring `<rect>` bars, `<path>` motifs, embedded `<image>` references)

Read the generated `*_vector_asset_inventory.json` before opening individual `<svg_analysis_workspace>/icons/*.svg`; do not bulk-read extracted icons unless a specific asset affects a design decision or is selected for mirror preservation.

If a `design_spec.md` or `spec_lock.md` accompanies the SVGs, `Read` it too — it is a higher-confidence source than re-deriving from the SVG alone. Record the equivalent of a `manifest.json`'s factual fields in your own analysis notes (no actual file written) so Step 2 can label them `[fact]`.

### 1C. Image / visual references

`ls` the folder (or single file) and `Read` each image / PDF page. Extract what's visible:

- rough theme colors (eyeball the dominant 2–4 hues; do NOT report exact HEX as fact)
- page count (count the supplied images as an approximate slide count)
- dominant typography style (sans / serif / display) — never report a font name
- decorative motifs and composition rhythm

Be explicit in Step 2 that exact HEX values, font names, and placeholder structure are **estimates from visual inspection** (`[suggested]`), never `[fact]`.

### 1D. No reference source

Skip the analysis. Step 2 will list every Required item as `[decision]`; nothing is fact-derivable from a non-existent source.

---

## Step 2: Fact-Based Brief Proposal

Compose a single message that surfaces every Required brief item to the user, **labelling each value's provenance**:

- **`[fact]`** — extracted from Step 1 analysis (e.g. theme color from `manifest.json`)
- **`[suggested]`** — AI-inferred from analysis or context (e.g. tone summary, applicable scenarios; visually estimated values from type C)
- **`[decision]`** — pure user choice, no analysis substitute (e.g. `template_id`, `replication mode`, `category`)

**Language adaptation rule**: write the Step 2 brief in the user's language. For technical enum values, show the localized label first and keep the English ID in parentheses only when needed for precision, e.g. `完整套版（deck）`, `结构版式（layout）`, `逐页采样（mirror）`. Do not assume users know what each English word means.

**Option visibility rule**: for every field with a finite option set, show both the recommended value and the other valid options. Do not present a single recommended value as if no alternatives exist. If an option is unavailable for the current input type, list it under `Unavailable` with the reason.

| Field | Must show |
|---|---|
| Template kind | Recommended localized label with English ID, plus both options and the rule for choosing |
| Category | Recommended localized category with English ID, plus `brand` / `general` / `scenario` / `government` / `special` with localized explanations |
| Theme mode | Recommended localized mode with English ID, plus available modes such as `light` / `dark` / `mixed` with localized explanations |
| Canvas format | Recommended canvas, plus other supported formats from [`canvas-formats.md`](../references/canvas-formats.md) that fit the source aspect ratio or user intent. Always show the concrete pixel size and `viewBox`; do not treat two same-ratio formats such as `ppt169` (`1280x720`) and `banner` (`1920x1080`) as interchangeable. |
| Replication mode | Recommended localized mode with English ID, plus all modes available for the current input type; list forbidden modes for type C / D as unavailable with localized reasons |
| Native structure strategy | For type A, show the `native_structure.json` recommendation and both choices: preserve source package (`preserve`) or rebuild explicit layouts (`template`). `mirror` cannot use preserve because its flat SVGs do not identify inherited layers. |
| Visual fidelity for fixed pages | Recommended localized choice with English ID, plus both `literal` / `adapted` options when applicable |
| Asset bundling | Recommended included assets, plus excluded candidate assets with a one-line reason when reference assets exist |

Items to surface:

| Item | Required | Provenance by input type |
|------|----------|--------------------------|
| New template ID | Yes | `[decision]` — user chooses ASCII slug; if Chinese brand name, must be filesystem-safe and match the target kind's index exactly |
| Template display name | Yes | `[decision]` (often the source deck title — `[suggested]` from `summary.md` for type A) |
| Category | Yes | `[decision]` — one of `brand` / `general` / `scenario` / `government` / `special` |
| Applicable scenarios | Yes | `[suggested]` from analysis; user confirms |
| Tone summary | Yes | `[suggested]` from analysis (e.g. `Modern, restrained, data-driven`) |
| Theme mode | Yes | A: `[fact]` from `manifest.json` background colors. B: `[fact]` from SVG `fill`. C: `[suggested]` from visual estimate. D: `[decision]` |
| Canvas format and dimensions | Yes | A/B: `[fact]` from slide size or SVG `width` / `height` / `viewBox`; show `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, and `source_viewbox`. C: `[suggested]` from image aspect ratio. D: `[decision]`, default `ppt169` (`1280x720`, `0 0 1280 720`) |
| Replication mode | Yes | `[decision]` — `standard` always available; `fidelity` and `mirror` available for type A (canonical, manifest-anchored) and type B (AI visual clustering / direct 1:1 copy — see Step 1 caveats); reject `fidelity` / `mirror` upfront for type C / D |
| Native structure strategy | Type A only | `[fact]` recommendation from `native_structure.json.strategy`; preserve (`preserve`) when the source graph is complete/reusable, rebuild (`template`) when minimal/incomplete. Force rebuild for `mirror`. |
| Visual fidelity for fixed pages | Yes for `standard` / `fidelity` when reference exists; **N/A for `mirror`** (mirror is implicitly literal) | `[decision]` — `literal` (preserve original geometry / decoration / sprite crops as-is; for cover / chapter / ending especially) or `adapted` (use the reference for tone/structure but allow design evolution). Different page types may take different settings |
| Basic template norms | Yes when reference exists | `[fact]` / `[suggested]` — layout grammar, image system, density rhythm, page roster semantics, and asset policy extracted in Step 1 |
| Reference source | Optional | already known if Step 1 ran |
| Theme color | Optional | A: `[fact]` from theme XML. B: `[fact]` from dominant SVG `fill`. C: `[suggested]` from visual estimate (HEX is approximate). D: `[decision]` |
| Fonts | Optional | A: `[fact]` from `manifest.json`. B: `[fact]` from SVG `font-family`. C / D: not derivable — `[decision]` if user wants a custom stack |
| Design style | Optional | `[suggested]` from analysis |
| Assets list | Optional | A: `[fact]` from `assets/` listing; user picks which to bundle. B / C: `[decision]` per file. D: none |
| Keywords | Yes | `[suggested]` from analysis (3–5 short tags); user confirms |

For type A, also include in this message:

- the exact cleaned `master_*.svg`, `layout_*.svg`, `slide_*.svg` filenames you read from the layered `svg/` view (proof of the hard read gate)
- a one-line summary of the master / layout structure you extracted
- the native structure recommendation, including master/layout counts, multi-master status, and reason codes

The user replies with corrections, additions, or "all good".

> **Persist the brief into `design_spec.md`**. When the Template_Designer writes `design_spec.md` in Step 4, declare a YAML frontmatter block at the top with the confirmed brief (`template_id`, `category`, `summary`, `keywords`, `primary_color`, `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, `source_viewbox`, `replication_mode`, `native_structure_mode`, etc.). `register_template.py` reads this in Step 6, so the brief flows directly into the index without the AI re-deriving it from prose. See Step 6 for the recommended frontmatter shape.

---

## Step 3: User Confirmation Gate

**MANDATORY interactive gate — this step BLOCKS Steps 4 onward.**

1. Echo back the finalized brief (post-corrections) in a single message
2. Emit the marker `[TEMPLATE_BRIEF_CONFIRMED]` on its own line

Skipping this gate — including silently inferring values from the reference source, opened IDE file, or prior conversation — is a workflow violation. Even if the user said "用这个 .pptx 做模板" upfront, you MUST still surface Step 2 with provenance labels and obtain explicit confirmation here. The reference source informs the brief; it does not substitute for it.

**Required outcome of Step 3** (all must be true before emitting `[TEMPLATE_BRIEF_CONFIRMED]`):

- [ ] User has been shown every Required item in Step 2 with provenance labels
- [ ] Every finite-option field has shown a recommended value, other available options, and unavailable options with reasons when applicable
- [ ] User-facing labels and option explanations match the user's language; English enum IDs appear only as precision aids
- [ ] User has replied with values or explicit acceptance of suggested defaults
- [ ] The template is clearly positioned as a **global library template**
- [ ] The canvas format is fixed before SVG generation
- [ ] Replication mode is consistent with the input type (`fidelity` / `mirror` allowed for A and B with B's caveats noted; forbidden for C / D)
- [ ] Basic template norms from prior content have been surfaced and accepted, or explicitly marked N/A when no reference exists
- [ ] Metadata is complete enough to register into the relevant index
- [ ] Marker `[TEMPLATE_BRIEF_CONFIRMED]` emitted on its own line after the echoed brief

Step 4 MUST NOT run until `[TEMPLATE_BRIEF_CONFIRMED]` has been emitted in the current conversation.

---

## Step 4: Create Template Directory + Invoke Template_Designer

> **Precondition**: `[TEMPLATE_BRIEF_CONFIRMED]` was emitted in Step 3. If not, return to Step 3.

Create the final template directory:

```bash
mkdir -p "skills/ppt-master/templates/<kind_dir>/<template_id>"
```

> **Output location**: Templates go to `skills/ppt-master/templates/<kind>/<template_id>/`. The generated directory name must match the final template ID used in the relevant index.

**Switch to the Template_Designer role** and generate per role definition. The role input is the finalized brief from Step 3 plus the analysis bundle from Step 1, including the accepted basic template norms.

If the input source is type A, pass the following internal package to the role:

- finalized brief from Step 3
- `manifest.json`
- `native_structure.json` and `source_template.pptx`
- `summary.md` (orientation only)
- exported `assets/`
- `*_vector_asset_inventory.json`, when the vector readability pass extracted assets; do not bulk-read `icons/*.svg`
- cleaned SVG references from `svg/`
- optional screenshots, if available

For type B, pass the cleaned SVG file list from the analysis workspace, `*_vector_asset_inventory.json` if extraction ran, any companion `design_spec.md` / `spec_lock.md`, and the analysis notes. Do not bulk-read extracted icons; open individual `icons/*.svg` only when needed.
For type C, pass the image file list and the visual analysis notes.
For type D, pass only the finalized brief.

The role uses the analysis bundle to anchor objective facts such as theme colors, fonts, reusable backgrounds, common branding assets, layout grammar, image-placement rules, density rhythm, and page-slot semantics, then rebuilds the final SVG templates in a simplified, maintainable form.

**Native structure strategy**: When the confirmed strategy is `preserve`, copy `native_structure.json` and `source_template.pptx` unchanged into the final template directory. Author every template SVG with the source layout key/name on the root, source master/layout visuals as preview layers, and slide content as source-compatible placeholder markers. When the strategy is `template`, do not copy the native pair; reconstruct one master plus semantic layouts through the explicit metadata contract. Mirror mode always takes this rebuild/baseline path because flat slides do not retain layer ownership.

**Apply the visual-fidelity decision from Step 3**: pages marked `literal` (typically cover / chapter / ending) must reproduce the reference's geometry, decoration, and sprite-sheet crops as-is — "simplified, maintainable form" applies only to genuinely redundant structure, not to load-bearing layout. Pages marked `adapted` may use the reference for tone and structural rhythm but evolve the design.

**Sprite-sheet preservation (do NOT simplify away)**: PPTX-exported assets are often sprite sheets — a single tall/large image referenced from multiple slides, each cropping a different region via nested `<svg ... viewBox="...">` wrappers around `<image width="1" height="1">`. This nesting is **load-bearing geometry**, not redundant structure. When rebuilding, preserve the exact `viewBox` crop and the outer `<svg>` placement for every image; do not flatten to a single `<image>` with direct `x/y/width/height`. Verify by sampling: if any asset's pixel dimensions don't match the on-page display aspect, it is a sprite and the wrapper must stay.

**Mirror-mode override** (type A or B): when `Replication mode: mirror`, this step is a **verbatim copy** rather than a reconstruction. The Template_Designer role:

1. **Copies the cleaned source pages** into the template directory **without reconstruction** — no content placeholder insertion, no decorative simplification, no chrome/content reorganization. The SVG that ships in the template is the cleaned source page, modulo filename changes, asset path rewrites, and the vector illustration placeholders created by the readability pass.
   - Type A: source is the cleaned flat `<import_workspace>/svg-flat/slide_NN.svg`
   - Type B: source is each cleaned `*.svg` in the analysis workspace when extraction ran; otherwise each `*.svg` in the input directory (already self-contained)
2. **Renames each file** using the source-order-first convention `<NNN>_<page_type>.svg`, where `<NNN>` is the source-order index zero-padded to 3 digits and `<page_type>` is typically `cover` / `toc` / `chapter` / `content` / `ending` (fall back to `content` when the type cannot be confidently classified). Examples: `001_cover.svg`, `002_toc.svg`, `003_content.svg`, ..., `050_ending.svg`.
   - Type A: derive `<page_type>` from `manifest.json.pageTypeCandidates`
   - Type B: derive `<page_type>` from the source filename when it follows the PPT Master convention (`01_cover.svg` → `cover`, `03a_content_two_col.svg` → `content`); otherwise infer from page content or fall back to `content`
3. **Copies bundled assets** into the template directory and rewrites the `<image href="...">` paths inside each copied SVG to point at the local copies. Asset filenames may be renamed to semantic names (`brand_emblem.png` instead of `image3.png`) when it improves readability — but the rewrite must be consistent across every page.
   - Type A: assets come from `<import_workspace>/assets/`
   - Type B: resolve relative paths in source `<image href="...">` against the source SVG location and copy each unique asset; if the source already follows PPT Master conventions (assets co-located with SVGs in the same directory), copy the whole asset set and then rewrite paths
4. **Copies `icons/` when present** and preserves every extracted `<use data-icon="..."/>` reference. Do not inline these assets manually in the template working SVGs; the shared icon embedding path owns re-inlining before export.
5. Writes `design_spec.md` per [template-designer.md](../references/template-designer.md) §1 — the **§V Page Roster description per page is the load-bearing artifact** because mirror has no placeholders to advertise the per-page contract. Mirror is only the template-creation replication mode; downstream generation still treats the finished template package as a selectable / reusable roster, not as a forced 1:1 slide sequence.

Mirror mode does **not** invoke the "reconstruct into clean SVG" pathway. The sprite-sheet preservation rule still applies (because the flat SVGs already contain the original sprite wrappers — do not flatten them when copying). Vector illustration placeholders are the only allowed maintainability rewrite.

**Expected outputs from this step** (full spec → [template-designer.md](../references/template-designer.md)):

1. `design_spec.md` — **personality only**. Required sections: Template Overview, Color Scheme, Signature Design Elements, Page Roster (matching the actual SVG files on disk). Skip Typography / Assets / Placeholder Overrides when they would just restate defaults. Declare brief frontmatter for `register_template.py`. **Do not** restate generic SVG constraints, layout pattern libraries, font-size ratio bands, the canonical placeholder table, or content methodology — those are sourced from `shared-standards.md` / `design_spec_reference.md` / `strategist.md` and are already in the downstream reader's context. Full scope rule and skeleton: [template-designer.md §1](../references/template-designer.md#1-must-generate-design_specmd).
2. Page roster — see [Page Roster](../references/template-designer.md#page-roster) for `standard` / `fidelity` / `mirror` mode rosters, variant naming, and TOC handling
3. Placeholder vocabulary — pages should adopt the conventional names (`{{TITLE}}`, `{{CONTENT_AREA}}`, ...) when they fit. Full reference: [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). When a template style legitimately needs different vocabulary (consulting → `{{KEY_MESSAGE}}`, branded cover → `{{BRAND_LOGO}}`), declare a `placeholders:` block in `design_spec.md` frontmatter so the registrar and quality checker treat it as the template's authoritative contract. **Avoid** one-off indexed families such as `{{CHAPTER_01_TITLE}}` — use the indexed TOC pattern instead.
   - `{{...}}` placeholders are the authoring contract used to generate final slide content; they are not PowerPoint `p:ph` objects. For reconstructed layouts, use `pptx_structure.mode: template`. For a template package carrying `native_structure.json` + `source_template.pptx`, use `mode: preserve`. Both modes require `pptx_layouts` and explicit root/layer/placeholder metadata; preserve-mode placeholders retain the source `data-pptx-placeholder-idx`.
4. Template assets (optional) — Logos / PNG / JPG / reference SVG bundled with the template package

---

## Step 5: Validate Template Assets

```bash
# Replace <kind_dir> with "decks" or "layouts" depending on the kind decided above
ls -la "skills/ppt-master/templates/<kind_dir>/<template_id>"
```

Run SVG validation on the template directory:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "skills/ppt-master/templates/<kind_dir>/<template_id>" --template-mode --format <canvas_format>
```

`--template-mode` makes the checker:

- glob `*.svg` in the template directory directly (templates do not live under `svg_output/`)
- skip `spec_lock.md` drift checks (templates do not ship a spec_lock)
- enforce roster ↔ `design_spec.md` consistency as **errors** (orphan files / missing files break the target kind's index)
- emit advisory **warnings** when a page lacks a conventional placeholder — these are hints, not failures. Declare a `placeholders:` block in `design_spec.md` frontmatter to silence them when your template intentionally uses a different vocabulary
- validate `native_structure.json` and `source_template.pptx` as an inseparable pair, including source hash, package layout parts, SVG layout keys/names, and placeholder compatibility

**Checklist**:

- [ ] `design_spec.md` follows the personality-only skeleton (Overview / Color / Signature / Page Roster); generic constraints (SVG rules, pattern libraries, ratio bands, canonical placeholder table) are NOT restated. The source-derived basic norms are present as template-specific layout / image / density / asset rules, not generic advice. §V Page Roster lists every emitted page
- [ ] Every page declared in `design_spec.md §V Page Roster` exists as an SVG file in the template directory (and vice versa — no orphan files)
- [ ] Variant filenames follow the letter-suffix convention (e.g. `03a_content_two_col.svg`); variants typically reuse the parent type's placeholder set unless the spec frontmatter declares otherwise
- [ ] If TOC exists, placeholder pattern uses the canonical indexed form
- [ ] `design_spec.md` frontmatter declares `canvas_format`, `canvas_width`, `canvas_height`, and `canvas_viewbox`; PPTX/SVG-backed templates also declare `source_canvas_width`, `source_canvas_height`, and `source_viewbox`
- [ ] SVG `viewBox` matches the declared canvas dimensions, not just the aspect ratio (for `ppt169`: `0 0 1280 720`; for `banner`: `0 0 1920 1080`); `width` / `height`, if written, equal it
- [ ] Placeholder names follow the canonical convention where applicable; templates with intentionally different vocabularies (e.g. `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`) should declare a `placeholders:` frontmatter block to silence advisory warnings
- [ ] Asset files referenced by SVGs actually exist in the template package
- [ ] When native strategy is `preserve`, both `native_structure.json` and `source_template.pptx` exist; every SVG root references a contract layout key/name and every placeholder uses a compatible source type/index
- [ ] If any SVG references an extracted vector `data-icon`, the corresponding SVG asset exists directly under the package's `icons/` directory; do not add a separate illustration embedding script
- [ ] For `fidelity` mode: every sprite-sheet asset retains its nested `<svg viewBox=...>` crop wrapper; no image whose file aspect differs from its on-page aspect was flattened to a bare `<image>`
- [ ] For `mirror` mode: file count equals source page count (type A: `ls templates/<kind_dir>/<id>/*_*.svg | wc -l` matches the cleaned flat `<import_workspace>/svg-flat/slide_*.svg | wc -l`; type B: matches the source SVG count); filenames follow the `<NNN>_<page_type>.svg` convention; **no `{{...}}` placeholder strings appear in any copied SVG** (`grep -l "{{" templates/<kind_dir>/<id>/*.svg` should return nothing — if the type B source itself contains placeholders, the user should be in `standard` mode, not `mirror`); §V Page Roster in `design_spec.md` lists every emitted file with a one-line description of what the page contains and what content slot it suits

This step is a **hard gate**. Do not register a template into the library index until validation passes.

---

## Step 6: Register Template in Library Index

Run the unified registrar with the kind flag; it derives the corresponding index entry from `design_spec.md` (frontmatter when present, prose fallback otherwise) plus the actual SVG file list:

```bash
# For deck (default)
python3 skills/ppt-master/scripts/register_template.py <template_id> --kind deck

# For layout
python3 skills/ppt-master/scripts/register_template.py <template_id> --kind layout
```

Outputs by kind (the JSON index is the single source of truth — READMEs describe the kind in prose but do not enumerate templates):

| `--kind` | Index updated |
|---|---|
| `deck` | `templates/decks/decks_index.json` |
| `layout` | `templates/layouts/layouts_index.json` |
| `brand` | `templates/brands/brands_index.json` |

The completion card's file roster is collected by globbing `*.svg` in the template directory.

The index file is a **discovery index** — it lets the AI answer "what templates are available?" by listing names and paths. It is **not** consulted to trigger Step 3 (SKILL.md). Step 3 triggers on an explicit directory path supplied by the user, regardless of whether that path is registered. A template directory that has not been run through `register_template.py` still works fine when the user gives its path; it just won't appear in discovery listings.

> **Recommended for new templates**: declare a YAML frontmatter block at the top of `design_spec.md`. The registrar prefers it over prose extraction:
>
> ```yaml
> # deck example
> ---
> deck_id: my_deck
> kind: deck
> summary: ...
> canvas_format: ppt169
> canvas_width: 1280
> canvas_height: 720
> canvas_viewbox: "0 0 1280 720"
> source_canvas_width: 1280
> source_canvas_height: 720
> source_viewbox: "0 0 1280 720"
> # Type-A preserve strategy only; omit all three rows for rebuilt templates.
> native_structure_mode: preserve
> native_structure: native_structure.json
> source_template: source_template.pptx
> page_count: 5
> primary_color: "#005587"
> ---
>
> # layout example
> ---
> layout_id: my_layout
> kind: layout
> summary: ...
> canvas_format: ppt169
> canvas_width: 1280
> canvas_height: 720
> canvas_viewbox: "0 0 1280 720"
> source_canvas_width: 1280
> source_canvas_height: 720
> source_viewbox: "0 0 1280 720"
> page_count: 5
> page_types: [cover, toc, chapter, content, ending]
> ---
> ```

> To rebuild every entry at once (e.g. after editing many specs), run:
>
> ```bash
> python3 skills/ppt-master/scripts/register_template.py --kind deck --rebuild-all
> python3 skills/ppt-master/scripts/register_template.py --kind layout --rebuild-all
> ```

README files describe each kind in prose only — they do not list templates. Discovery happens against the JSON index file; the registrar does not touch READMEs.

---

## Step 7: Output Confirmation

`register_template.py` already printed a "Template Creation Complete" card during Step 6 — copy it verbatim into the conversation. The card includes the template name, path, category, primary color, index status, and the full SVG file roster (auto-collected from disk, so `fidelity`-mode variant pages and TOC pages are listed correctly without manual editing).

For a standard-mode template the card looks like:

```markdown
## Template Creation Complete

**Template Name**: <template_id> (<display_name>)
**Kind**: deck | layout
**Template Path**: `templates/<kind_dir>/<template_id>/`
**Primary Color**: <hex>  ← deck only; omit for layout
**Index Registration**: Done

### Files Included

| File | Status |
|------|--------|
| `01_cover.svg` | Done |
| `02_chapter.svg` | Done |
| `02_toc.svg` | Done |
| `03_content.svg` | Done |
| `04_ending.svg` | Done |
```

---

## Color Scheme Quick Reference

| Style | Primary Color | Use Cases |
|-------|---------------|-----------|
| Tech Blue | `#004098` | Certification, evaluation |
| McKinsey | `#005587` | Strategic consulting |
| Government Blue | `#003366` | Government projects |
| Business Gray | `#2C3E50` | General business |

---

## Notes

1. **SVG technical constraints**: See [shared-standards.md](../references/shared-standards.md) — do not restate them in the template's `design_spec.md`
2. **Color consistency**: All SVG files must use the same color scheme as `design_spec.md §II Color Scheme`
3. **Placeholder convention**: `{{}}` format only; default names listed in [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). Override per template via `placeholders:` frontmatter when needed.
4. **Discovery requirement**: A template directory is only discoverable after `register_template.py` has been run against it (Step 6)

> **Full role specification**: [template-designer.md](../references/template-designer.md)
