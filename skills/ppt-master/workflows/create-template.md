---
description: Generate a new layout or deck template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate one complete layout/deck template workspace under either the **global template library** or `projects/`.

**Default — library scope**: Write `skills/ppt-master/templates/<kind>/<id>/` and register it in the matching discovery index.

**Project scope**: Write the same portable workspace routing at `<project>/` and do not register any global index.

**Hard rule — one workspace routing contract**: Output scope changes only the workspace parent and index registration. Both scopes use required `templates/`, optional `images/` / `icons/`, and optional on-demand `exports/`, with the same relative asset references and validation command. Never add placeholder files only to retain an empty directory. Do not maintain a library-only self-contained-flat package branch or a project-only thin-bundle branch.

> **Boundary against template-fill**: this workflow does not fill content into a PPTX and does not directly output the user's final generated deck. It creates a reusable template contract; an optional PPTX may be generated later for local review. To generate a deck from the workspace, return its root path to the main SKILL.md pipeline. A project-scoped workspace is already installed at that project's Step 3 path and is consumed in place.

> **Companion workflow**: identity-only locking (colors / typography / logo / voice without SVG pages) is handled by [`create-brand.md`](./create-brand.md). Use that when the user wants brand identity but free page layout; use this when fixed page structures are required.

## Kind decision — deck (default) vs layout

This workflow produces one of two kinds of templates depending on whether the source PPT carries a specific brand identity:

| Kind | When | Library-scope output dir | What `design_spec.md` writes |
|---|---|---|---|
| **deck** (default) | Source is a specific organization's branded PPT (e.g. company report, university defense template); the visual identity is part of the replica | `templates/decks/<id>/templates/` | Full segments: identity + structure + middle |
| **layout** | Source is a generic stylistic template (no specific brand); only the structural skeleton should be reusable; color / typography decided per-deck downstream | `templates/layouts/<id>/templates/` | Structure segments only (canvas / page structure / page types / SVG roster); identity segment omitted |

Default to **deck** unless the user explicitly says "structure only" / "layout only" / "no brand identity". When in doubt, lean deck — losing identity later is easy; reconstructing it from a layout-mode strip is not. See [`docs/zh/templates-architecture.md`](../../../docs/zh/templates-architecture.md) for the full kind / schema / fusion model.

## Output scope — library (default) vs project

Output scope is a workflow execution choice, not a new template kind or PPTX structure mode. Surface it in the Step 2 brief; do not invent a CLI flag or persist `output_scope` / `target_project` into portable `design_spec.md` frontmatter.

| Scope | `<template_workspace>` | Template source | Registration |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind_dir>/<template_id>/` | `<template_workspace>/templates/` | Run `register_template.py` against the matching global index |
| `project` | `<target_project>/` | `<template_workspace>/templates/` | Do not update any global index |

Both scopes write this contract:

```text
<template_workspace>/
├── templates/   # design_spec.md, template SVGs, templates/icons/ when used
├── images/      # optional; every bitmap; SVG href is ../images/<name>
├── icons/       # optional; runtime copy of extracted vector assets
└── exports/     # conditional; required package evidence for multi-Master templates
```

The review PPTX is derived evidence, not a source template asset. Create `exports/` only when a review deck is requested or the template declares more than one Master; multi-Master templates require the package-level gate in Step 6. Template application reads `templates/` plus any existing `images/` and `icons/`; it never copies or consumes `exports/`. Library `exports/` directories are Git-ignored.

For `project`, `target_project` is required and must be an existing project initialized by `project_manager.py init`. Before the first final-output write, run one complete preflight. Apply the same collision checks to a library workspace; the only difference is that its root is under the global kind directory:

1. Resolve `<template_workspace>` from the confirmed scope and confirm its required `templates/` destination plus any needed `images/` / `icons/` destinations.
2. Confirm `<template_workspace>/templates/` is empty.
3. Resolve every final bitmap and extracted-icon filename, then confirm none would overwrite an existing file in `images/`, `icons/`, or `templates/icons/`. Check the review-PPTX destination when preview export was requested or a multi-Master template was confirmed.

Any failed check aborts before writing `design_spec.md`, SVGs, images, icons, or the review PPTX. Do not merge into a non-empty template source and do not overwrite a name conflict. Temporary Step 1 analysis workspaces remain allowed because they are not final outputs.

## Process Overview

```
Reference Intake & Analysis -> Basic Norm Extraction -> Fact-Based Brief Proposal -> User Confirmation Gate -> Preflight + Invoke Template_Designer -> Validate Assets -> [Review PPTX: optional for one Master, required for multi-Master] -> [Register Library Index] -> Output
```

The first three steps derive the brief from facts, not guesses. **No final template directory may be created and no template SVG / `design_spec.md` may be written until `[TEMPLATE_BRIEF_CONFIRMED]` is emitted in Step 3.** Reference-analysis intermediates produced by `pptx_template_import.py` (typically under `/tmp/pptx_template_import/`) are explicitly **not** subject to this gate — they are temporary workspaces feeding Step 2.

---

## Step 1: Reference Intake & Analysis

Branch by the type of reference source the user supplied. This step produces analysis artefacts only — it does **not** create the final template directory, write `design_spec.md`, or touch any template index.

### Input source taxonomy

| Type | What the user supplied | Tool / read path | Replication modes available |
|------|-------------------------|------------------|------------------------------|
| **A** `.pptx` reference | A `.pptx` file path | `pptx_template_import.py` → `manifest.json` + `native_structure.json` + `source_template.pptx` + layered/flat SVGs + `assets/` | `standard` / `fidelity` / `mirror` |
| **B** Existing SVG assets | `projects/<x>/svg_output/`, a current template workspace root, a legacy flat template root, or a loose `.svg` folder | Normalize the source directory, create a lightweight projection with `svg_authoring_view.py`, then read projected page SVGs; also read companion `design_spec.md` / `spec_lock.md` when present | `standard` / `fidelity`; `mirror` only when the source already carries a complete explicit Master/Layout/placeholder/native-object contract |
| **C** Image / visual references | Screenshot folder, single image, PDF pages | `ls` + `Read` each file (multimodal visual recognition) | `standard` only |
| **D** No reference source | Verbal description only ("McKinsey style", "tech blue", "dark minimal") | — | `standard` only |

`fidelity` and `mirror` are not available for type C / D — visual references and verbal-only briefs cannot drive page-by-page replication. Type A is the canonical mirror path: `manifest.json`, `native_structure.json`, layered lossless `svg/`, complete-page lossless `svg-flat/`, and inheritance facts are the restoration authority. In `standard` / `fidelity`, those files supply factual canvas/asset/visual references only and do not define output topology.

**Type B source normalization**: when the supplied root contains `templates/design_spec.md`, use `<input>/templates/` as the SVG/spec source and resolve its workspace assets from sibling `<input>/images/` and `<input>/icons/`. Otherwise, use the supplied directory itself as the legacy-flat/loose SVG source. Directory flatness is not a semantic-structure signal.

Type B is supported with caveats:

- **mirror on type B** — require a complete explicit source contract. Preserve page count/order, literal visuals, root Master/Layout identities, slot metadata, supported native-object metadata, and source ownership. Page type for `<NNN>_<page_type>.svg` is read from the source filename when it follows the PPT Master naming convention (`01_cover.svg` → `cover`, `03a_content_two_col.svg` → `content`); fall back to `content` otherwise. A loose visual-only SVG folder has no native structure to restore and cannot use mirror.
- **fidelity on type B** — inspect the complete page roster as visual reference, then design a broader new roster and its own Master/Layout/slot system. Existing keys, families, and repeated source chrome are not output-topology inputs.
- **legacy or unstructured type B** — old `baseline` / `preserve` / `layout_strategy: distill` / `data-pptx-layout-kind` / direct-atomic-placeholder inputs, and SVGs with no root Master identity, first run [`restore-pptx-structure`](./restore-pptx-structure.md). The restored contract is then the Type B input. Do not keep a second compatibility branch inside template creation.
- **selected free-design subset on type B** — restore the named source pages into the current structured contract, then ingest only that explicit subset. Do not scan or copy the whole `svg_output/` directory and silently turn unselected pages into template variants.

**Replication mode boundary**: `standard` and `fidelity` are authored modes: source visuals/assets guide a new SVG roster and a newly designed Master/Layout/slot system, without preserving or distilling source topology. `mirror` is a restoration mode: source page order, visuals, Master/Layout graph, placeholders, ownership, and supported native-object metadata are authoritative. Mirror may mechanically normalize the transport representation for the current compiler, including fixed-layer group expansion, but it never performs semantic synthesis. The modes do not create a downstream generation route, and a completed mirror workspace does not force future decks to preserve the source page count or page order.

### 1A. `.pptx` reference

Run the unified preparation helper:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py "<reference_template.pptx>"
```

This produces, in one workspace:

- `manifest.json` — single source of truth: slide size, theme colors, fonts, per-master theme summaries, asset inventory, placeholder metadata, SVG file paths, per-slide / per-layout / per-master metadata (including source-owned inherited-shape visibility), page-type candidates
- `native_structure.json` — analysis contract: stable master/layout keys, layout picker names, placeholder type/index/geometry, inherited-shape visibility, source hash, and source-graph quality facts
- `source_template.pptx` — byte-preserved analysis copy for visual/package cross-checking; it is not copied into the final template package
- `summary.md` — short human-readable digest derived from manifest.json (for quick scanning only)
- `assets/` — extracted reusable image assets; `manifest.json` owns the asset-name mapping and SVG `href` values reuse that mapping
- `svg/` — **primary view** (layered template view):
  - `svg/master_*.svg` — every slide master in the deck rendered once, including masters that no sample slide currently uses (template packages routinely ship more masters than the visible samples reference)
  - `svg/layout_*.svg` — every slide layout in the deck rendered once (its own contribution; master shapes do **not** repeat here)
  - `svg/slide_NN.svg` — each slide's own shapes and slide-local background; master / layout shapes and backgrounds are **not** inlined here
  - `svg/inheritance.json` — which Layout/Master each Slide consumes plus source-owned `showInheritedShapes` / `showMasterShapes` booleans; Layout shapes follow the Slide's `showInheritedShapes`, while Master shapes require that value and the referenced Layout's `showMasterShapes`; backgrounds remain independent
- `svg-flat/` — **companion view** (one self-contained SVG per slide):
  - `svg-flat/slide_NN.svg` — effective Master/Layout contributions permitted by the source visibility flags plus Slide-local content, painted into one SVG so opening any slide on its own shows the full page like PowerPoint would. Background inheritance remains independent. Use this for previews / screenshot pipelines / "what does the slide actually look like" sanity checks.
- The default `--inheritance-mode both` emits both views. Pass `layered` to skip `svg-flat/`, or `flat` for round-trip use cases (legacy: `svg/` becomes self-contained slides without the master/layout/inheritance files).

Import fidelity rules:

- Placeholder metadata is recorded in `manifest.json`; master / layout SVGs show lightweight dashed guides with labels only in `svg/`, not in `svg-flat/`.
- Charts, SmartArt, diagrams, and OLE objects are typed placeholders in `svg/`. In `svg-flat/`, they use a preview image with a small badge when one exists; otherwise they stay visible as placeholders. Tables are converted to real SVG.
- Missing media and external linked images fail the import. EMF / WMF Office vector media are converted to PNG previews when supported by the local toolchain; otherwise the import fails.

It is a reconstruction aid, not a final direct template conversion.

**Lossless source + lightweight authoring view**:

Keep `<import_workspace>/svg/` and `<import_workspace>/svg-flat/` unchanged as the lossless import evidence. Before the Template_Designer reads any imported page SVG, create non-destructive model-facing projections:

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<import_workspace>/svg" -o "<import_workspace>/authoring-svg"
python3 skills/ppt-master/scripts/svg_authoring_view.py "<import_workspace>/svg-flat" -o "<import_workspace>/authoring-svg-flat"
```

The projection removes opaque text payload, duplicate hidden geometry carriers, and import-only identity attributes while keeping visible shape intent, compact preset/frame metadata, structure markers, logical ids, and valid asset references. It is an inspection surface only. Never export it as a finished template and never overwrite the lossless source.

**Vector illustration readability pass**:

Factor large decorative vector groups out of the lightweight projections so the model-facing SVGs stay readable while export remains native shapes. Never run this in place on the lossless import SVGs:

```bash
# layered view — primary read surface in every mode
python3 skills/ppt-master/scripts/extract_svg_assets.py "<import_workspace>/authoring-svg" --icons-dir "<import_workspace>/icons" --inplace --id-prefix layered --min-decoration-bytes 3000 --clean-stale

# flat view — mirror inspection and optional composition spot checks; the lossless layered/flat sources remain authoritative for mirror
python3 skills/ppt-master/scripts/extract_svg_assets.py "<import_workspace>/authoring-svg-flat" --icons-dir "<import_workspace>/icons" --inplace --id-prefix flat --min-decoration-bytes 3000 --clean-stale
```

The projected SVGs in `<import_workspace>/authoring-svg/` / `<import_workspace>/authoring-svg-flat/` are rewritten in place with compact `<use data-icon="..."/>` placeholders. Extracted assets live directly under `<import_workspace>/icons/`; `icons/` must contain only icon/vector assets, not rewritten page SVGs or inventories. The inventory is written beside the processed projection directory. The existing icon embedding path re-inlines the extracted assets before final export, preserving multi-color artwork and non-square viewBox geometry as native SVG shapes. Text-bearing groups are never extracted; text must stay readable/editable in the working SVG. Extraction triggers on either many drawable elements or a large pure-vector XML block, so long single-path illustrations are factored out too. Pure-vector decoration runs inside text-bearing groups use a lower size threshold, allowing card borders and decorative paths to be extracted without hiding text. Referenced defs (`gradient` / `pattern` / `filter` / `clipPath` / `marker`) are copied into each asset and namespaced so the asset is self-contained after re-inline. If both layered and flat views are processed into the same icon directory, keep distinct `--id-prefix` values to avoid asset ID collisions. `--clean-stale` removes only stale generated assets for the current SVG filenames and prefix; it is safe in this import workspace but should not be used against a shared hand-curated icon directory without a specific prefix.

**Explicit complex-SVG picture normalization (optional; `standard` / `fidelity` only)**:

When one imported native group is deliberately being retained as one complex
SVG picture rather than rebuilt as editable paths, select its exact id in the
lightweight projection and normalize it explicitly:

```bash
python3 skills/ppt-master/scripts/extract_svg_pictures.py \
  "<import_workspace>/authoring-svg/<layered_svg_file>.svg" \
  --select "<group_id>" \
  --resource-root "<import_workspace>" \
  --images-dir "<import_workspace>/picture-assets" \
  --inplace
```

Repeat `--select` for multiple independent sibling groups. The tool uses an
imported `data-pptx-frame` when present; otherwise it measures the target with
Playwright, or accepts `--bounds ID=x,y,width,height`. It creates a tight,
self-contained SVG under `picture-assets/`, embeds reachable local resources,
and replaces the group at the same z-order with one `<image>`. If the object is
chosen for a final Master or Layout, copy that asset into the project image
pool and author the final fixed atom as a direct `<image>` with
`data-pptx-layer="master|layout"`; export then creates one `p:pic`.
Nested targets are allowed only below metadata-only grouping wrappers. If an
ancestor carries a transform, style, clip, opacity, or other visual attribute,
select that outer group so the effect is not applied twice.

This is a semantic representation decision, not an import heuristic. Never run
it automatically, never select groups by repetition, and never use it to infer
Master/Layout ownership. Do not apply it to placeholders, individual imported
native shapes, native table/chart fallbacks, icon placeholders, or compact
authored presets. `mirror` must keep the source native group/picture identity
and therefore must not use this normalization. The original lossless `svg/`
and `svg-flat/` trees remain unchanged and authoritative.

`extract_svg_assets.py` remains a different operation: it factors vectors out
for model readability and re-inlines them as native shapes before export. It
does not turn those vectors into a picture.

**Read order during analysis**:

| Mode | Required read set |
|---|---|
| `standard` / `fidelity` | `manifest.json`, exported assets, `svg/inheritance.json`, and every cleaned layered projection (`authoring-svg/master_*.svg` / `layout_*.svg` / `slide_NN.svg`). The layered view is the complete read surface: it covers Layouts unused by any sample slide (invisible in `svg-flat/` yet still template vocabulary), and per-page composition follows from `inheritance.json`. Cleaned flat pages are optional composition spot checks, not a required second pass over the same shapes. Source topology remains non-binding; the two modes differ in output design (`fidelity` designs a broader roster covering the useful visual range), not in read coverage. |
| `mirror` | `manifest.json`, `native_structure.json`, `svg/inheritance.json`, every cleaned layered Master/Layout/Slide projection, and every cleaned flat slide projection. Verify the projection against the lossless file inventory; restoration itself reads the matching lossless files by identity rather than placing their opaque payload in model context. |

Use `summary.md` only for orientation. Use screenshots or the original PPTX only for visual cross-checking. Do not bulk-read opaque lossless payload into model context.

Interpretation rule (carries forward into Steps 2 and 4):

- `manifest.json` is the source of truth for facts about the source deck: slide size, theme colors, fonts, background inheritance, reusable asset inventory, declared source layout/master structure, and slide reuse relationships. It dictates mirror restoration facts but not `standard` / `fidelity` output topology.
- `native_structure.json` is the source of truth for source PowerPoint identity: stable layout keys, picker names, parent masters, placeholder types/indices, and the source-package hash. Mirror preserves those facts one-to-one. `standard` / `fidelity` do not mine them into the new structure.
- `summary.md` is a quick scan; never treat it as the canonical fact source — go back to `manifest.json` if anything is unclear
- exported `assets/` are the canonical reusable image pool — `<image>` references in `svg/` already point at these files directly
- exported `icons/*.svg` are the canonical reusable vector illustration pool, but they are **not** part of the default read set. Read the cleaned SVGs and `*_vector_asset_inventory.json` first; open a specific icon SVG only when the cleaned page or inventory shows that the extracted asset is relevant to the current design decision. This is what makes the SVG work surface smaller.
- cleaned layered projections are mirror verification views; they expose source ownership without requiring the model to read opaque payload. Do not use them to promote, demote, merge, or split source structure.
- cleaned complete-page projections are optional composition spot checks for authored modes and verification views for mirror. They are never the lossless restoration source.
- screenshots remain useful for judging composition and style, but should not override extracted factual metadata unless the import result is clearly incomplete

**Mirror complete-graph gate**: compare every `native_structure.json` Layout
and Master with the layered projection inventory before offering `mirror`.
Every source Layout—including one unused by all source slides—must have a
lossless Layout projection from which a reusable definition SVG can be restored.
Every source Master must own at least one retained Layout. Missing projections
or ambiguous parentage are blocking; unused identities themselves are supported
and must not be dropped.

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
| Native PowerPoint structure | `native_structure.json` plus inheritance facts | Mirror restores the source graph one-to-one. Standard/fidelity author an independent output graph and do not distill source common structure. |

Distinguish observed facts from template rules: "`slide_07` uses a left photo crop" is a fact; "content pages may use a left photo rail for location / product / case-study pages" is the reusable rule.

**Read gate**:

- `standard` / `fidelity`: read and report every projected Master, Layout, and Slide plus the inheritance map; flat pages are optional spot checks
- `mirror`: verify and report every projected Master, Layout, and Slide plus the inheritance map, while keeping opaque payload out of model context

Do not treat lightweight projections as final template assets. `standard` / `fidelity` author new SVGs. Mirror restores from the lossless import and uses projections only for inspection.

> **Mirror-mode restoration path** — use lossless layered SVGs, flat SVGs, `native_structure.json`, and `svg/inheritance.json` as authority. The cleaned projections are the literal inspection target, not a replacement data source. Preserve roster, appearance, ownership, placeholders, converter-supported native metadata, and available SVG fallbacks; do not synthesize a different graph.

### 1B. Existing SVG assets

First resolve the Type B source directory using the rule above. Create a non-destructive authoring projection in a throwaway analysis workspace, then run the same vector readability pass only on that projection. Do **not** rewrite the user's original source directory in place.

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<normalized_svg_source>" -o "<svg_analysis_workspace>/authoring-svg"
python3 skills/ppt-master/scripts/extract_svg_assets.py "<svg_analysis_workspace>/authoring-svg" --icons-dir "<svg_analysis_workspace>/icons" --inplace --id-prefix source --min-decoration-bytes 3000 --clean-stale
```

If the source contains one deliberately selected complex subtree that should
remain a single SVG picture, apply the explicit normalization above only to the
analysis projection. Set `--resource-root` to the narrowest workspace directory
that contains both the projection and every local dependency referenced by the
selected group. This does not authorize automatic group selection or mutation
of the user's original SVG directory.

Then `ls` the analysis workspace and `Read` every cleaned `authoring-svg/*.svg` to extract:

- canvas size (`viewBox` on the root `<svg>`)
- recurring colors (`fill` / `stroke` values; identify the dominant 2–4 hex codes as candidate theme colors)
- fonts (`font-family` attributes on `<text>`)
- placeholder usage (existing `{{...}}` strings, if any)
- structural decoration (recurring `<rect>` bars, `<path>` motifs, embedded `<image>` references)

Read the generated `*_vector_asset_inventory.json` before opening individual `<svg_analysis_workspace>/icons/*.svg`; do not bulk-read extracted icons unless a specific asset affects a design decision or is selected for mirror preservation.

If a `design_spec.md` or `spec_lock.md` accompanies the SVGs, read it too. In mirror it is part of the source contract and must agree with the SVG identities; in `standard` / `fidelity` it is visual/contextual reference only. Record the equivalent of a `manifest.json`'s factual fields in analysis notes so Step 2 can label them `[fact]`.

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

**Language adaptation rule**: write the Step 2 brief in the user's language. For technical enum values, show the localized label first and keep the English ID in parentheses only when needed for precision, for example `<localized deck label> (deck)`, `<localized layout label> (layout)`, or `<localized mirror label> (mirror)`. Do not assume users know what each English word means.

**Option visibility rule**: for every field with a finite option set, show both the recommended value and the other valid options. Do not present a single recommended value as if no alternatives exist. If an option is unavailable for the current input type, list it under `Unavailable` with the reason.

| Field | Must show |
|---|---|
| Output scope | Recommended `library` (default) plus `project`; explain that both use the same portable workspace routing and only the parent path / global registration differ |
| Target project | Required only for `project`; show the exact initialized project workspace path, not a project nickname |
| Template kind | Recommended localized label with English ID, plus both options and the rule for choosing |
| Category | Recommended localized category with English ID, plus `brand` / `general` / `scenario` / `government` / `special` with localized explanations |
| Theme mode | Recommended localized mode with English ID, plus available modes such as `light` / `dark` / `mixed` with localized explanations |
| Canvas format | Recommended canvas, plus other supported formats from [`canvas-formats.md`](../references/canvas-formats.md) that fit the source aspect ratio or user intent. Always show the concrete pixel size and `viewBox`; do not treat two same-ratio formats such as `ppt169` (`1280x720`) and `banner` (`1920x1080`) as interchangeable. |
| Replication mode | Recommended localized mode with English ID, plus all modes available for the current input type; state that `standard` / `fidelity` design a new structure while `mirror` restores the source structure; list unavailable modes with reasons |
| Native structure policy | For `standard` / `fidelity`, state that the designer will author a new Master/Layout/slot system without preserving or distilling source topology. Show the planned Master roster; if it contains more than one Master, explain the distinct reusable family owned by each and which Layouts belong to it. Reject one-Master-per-Layout organization and visually/semantically equivalent duplicate Masters. For `mirror`, summarize the exact source Master/Layout/placeholder graph that will be restored one-to-one. |
| Visual fidelity for fixed pages | Recommended localized choice with English ID, plus both `literal` / `adapted` options when applicable |
| Asset bundling | Recommended included assets, plus excluded candidate assets with a one-line reason when reference assets exist |

Items to surface:

| Item | Required | Provenance by input type |
|------|----------|--------------------------|
| Output scope | Yes | `[decision]` — `library` (default, globally reusable and indexed) or `project` (same portable workspace routing under one initialized project) |
| Target project | Yes for `project`; N/A for `library` | `[decision]` — explicit path to the initialized target workspace; validate it during the Step 4 preflight |
| New template ID | Yes | `[decision]` — user chooses ASCII slug; if Chinese brand name, it must be filesystem-safe. In library scope it also becomes the matching index key |
| Template display name | Yes | `[decision]` (often the source deck title — `[suggested]` from `summary.md` for type A) |
| Category | Yes | `[decision]` — one of `brand` / `general` / `scenario` / `government` / `special` |
| Applicable scenarios | Yes | `[suggested]` from analysis; user confirms |
| Tone summary | Yes | `[suggested]` from analysis (e.g. `Modern, restrained, data-driven`) |
| Theme mode | Yes | A: `[fact]` from `manifest.json` background colors. B: `[fact]` from SVG `fill`. C: `[suggested]` from visual estimate. D: `[decision]` |
| Canvas format and dimensions | Yes | A/B: `[fact]` from slide size or SVG `width` / `height` / `viewBox`; show `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, and `source_viewbox`. C: `[suggested]` from image aspect ratio. D: `[decision]`, default `ppt169` (`1280x720`, `0 0 1280 720`) |
| Replication mode | Yes | `[decision]` — `standard` always available; `fidelity` is available for A/B; `mirror` is available for A and for B sources with a complete explicit structure contract. `standard` / `fidelity` author new SVG semantics. Mirror retains one restored prototype per source slide in source order and adds definition-only prototypes for source Layouts unused by those slides. Reject `fidelity` / `mirror` for C/D. |
| Native structure facts | Type A and structured Type B | `[fact]` from `native_structure.json` / source SVG contract: master/layout counts, parentage, page assignments, placeholder identities, and multi-master status. Mirror restores these facts; authored modes do not use them as output topology. |
| Mode-specific ownership | Yes | `standard` / `fidelity`: `[decision]` newly authored Master/Layout ownership, including the reusable-family reason for every additional Master. `mirror`: `[fact]` source ownership restored without synthesis. Every Master must own at least one emitted Layout and every Layout must have at least one emitted prototype; export never infers either contract. |
| Visual fidelity for fixed pages | Yes for `standard` / `fidelity` when reference exists; **N/A for `mirror`** (mirror restores the source visual) | `[decision]` — `literal` (closely reproduce reference geometry / decoration / sprite crops within a newly authored structure) or `adapted` (use reference tone/composition but allow design evolution). Different page types may take different settings. |
| Basic template norms | Yes when reference exists | `[fact]` / `[suggested]` — layout grammar, image system, density rhythm, page roster semantics, and asset policy extracted in Step 1 |
| Reference source | Optional | already known if Step 1 ran |
| Theme color | Optional | A: `[fact]` from theme XML. B: `[fact]` from dominant SVG `fill`. C: `[suggested]` from visual estimate (HEX is approximate). D: `[decision]` |
| Fonts | Optional | A: `[fact]` from `manifest.json`. B: `[fact]` from SVG `font-family`. C / D: not derivable — `[decision]` if user wants a custom stack |
| Design style | Optional | `[suggested]` from analysis |
| Assets list | Optional | A: `[fact]` from `assets/` listing; user picks which to bundle. B / C: `[decision]` per file. D: none |
| Keywords | Yes | `[suggested]` from analysis (3–5 short tags); user confirms |

For type A, also include in this message:

- the exact projected files required by the selected mode and verified during Step 1
- a one-line summary of the source Master/Layout structure
- the source structure facts, including master/layout counts, multi-master status, and reason codes; state whether they will be restored (`mirror`) or ignored as output topology (`standard` / `fidelity`)

The user replies with corrections, additions, or "all good".

> **Persist the portable brief into `design_spec.md`**. When the Template_Designer writes `design_spec.md` in Step 4, declare a YAML frontmatter block at the top with the confirmed portable fields (`template_id`, `category`, `summary`, `keywords`, `primary_color`, `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, `source_viewbox`, `replication_mode`, `native_structure_mode`, etc.). Do not persist the execution-only `output_scope` or `target_project` fields. In library scope, `register_template.py` reads this frontmatter in Step 7 so the brief flows directly into the index without the AI re-deriving it from prose.

---

## Step 3: User Confirmation Gate

**MANDATORY interactive gate — this step BLOCKS Steps 4 onward.**

1. Echo back the finalized brief (post-corrections) in a single message
2. Emit the marker `[TEMPLATE_BRIEF_CONFIRMED]` on its own line

Skipping this gate — including silently inferring values from the reference source, opened IDE file, or prior conversation — is a workflow violation. Even if the user said "use this .pptx as a template" upfront, you MUST still surface Step 2 with provenance labels and obtain explicit confirmation here. The reference source informs the brief; it does not substitute for it.

**Required outcome of Step 3** (all must be true before emitting `[TEMPLATE_BRIEF_CONFIRMED]`):

- [ ] User has been shown every Required item in Step 2 with provenance labels
- [ ] Every finite-option field has shown a recommended value, other available options, and unavailable options with reasons when applicable
- [ ] User-facing labels and option explanations match the user's language; English enum IDs appear only as precision aids
- [ ] User has replied with values or explicit acceptance of suggested defaults
- [ ] Output scope is confirmed; both scopes use the same workspace shape, while `project` includes an explicit initialized target-project path
- [ ] The canvas format is fixed before SVG generation
- [ ] Replication mode is consistent with the input type (`fidelity` allowed for A/B; `mirror` allowed for A and structured B only; both forbidden for C/D)
- [ ] Before offering `mirror`, the source graph and supported geometry are complete; every source Layout absent from the source-slide roster is planned as a definition-only prototype, and any genuinely missing/unsupported facts were reported
- [ ] Basic template norms from prior content have been surfaced and accepted, or explicitly marked N/A when no reference exists
- [ ] Mode-specific ownership policy is explicit: `standard` / `fidelity` author a new structure without source-topology distillation; `mirror` restores source ownership one-to-one
- [ ] For `library`, metadata is complete enough to register into the relevant index; for `project`, the same portable template metadata is complete and no global registration is planned
- [ ] Marker `[TEMPLATE_BRIEF_CONFIRMED]` emitted on its own line after the echoed brief

Step 4 MUST NOT run until `[TEMPLATE_BRIEF_CONFIRMED]` has been emitted in the current conversation.

---

## Step 4: Preflight Output + Invoke Template_Designer

> **Precondition**: `[TEMPLATE_BRIEF_CONFIRMED]` was emitted in Step 3. If not, return to Step 3.

Select the final target from the confirmed output scope:

```bash
# library scope (default)
template_workspace="skills/ppt-master/templates/<kind_dir>/<template_id>"

# project scope
template_workspace="<target_project>"

# identical in both scopes; create optional roots only when writing an asset
mkdir -p "$template_workspace/templates"
```

| Scope | Workspace target | Required action before generation |
|---|---|---|
| `library` | `skills/ppt-master/templates/<kind_dir>/<template_id>/` | Run the common workspace preflight; the directory name matches the final template ID used in the relevant index |
| `project` | `<target_project>/` | Run the same workspace preflight against the initialized project root |

The preflight is atomic at workflow level: discover and settle every output filename first, check all destinations together, then begin generation. Do not partially write a workspace and discover a later collision.

**Switch to the Template_Designer role** and generate per role definition. The role input is the finalized brief from Step 3 plus the analysis bundle from Step 1, including the accepted basic template norms.

If the input source is type A, pass the following internal package to the role:

- finalized brief from Step 3
- `manifest.json`
- `native_structure.json` and `source_template.pptx`
- `summary.md` (orientation only)
- exported `assets/`
- `*_vector_asset_inventory.json`, when the vector readability pass extracted assets; do not bulk-read `icons/*.svg`
- lightweight references from `authoring-svg/` and `authoring-svg-flat/`
- for `mirror` only, matching lossless `svg/`, `svg-flat/`, and `svg/inheritance.json` restoration sources
- optional screenshots, if available

For type B, pass the cleaned SVG file list from the analysis workspace, `*_vector_asset_inventory.json` if extraction ran, any companion `design_spec.md` / `spec_lock.md`, and the analysis notes. Do not bulk-read extracted icons; open individual `icons/*.svg` only when needed.
For type C, pass the image file list and the visual analysis notes.
For type D, pass only the finalized brief.

The role interprets the package according to replication mode:

| Mode | Final SVG authority | Structure behavior |
|---|---|---|
| `standard` / `fidelity` | Newly authored SVGs based on the confirmed brief and visual references | Design an intentional new Master/Layout/slot system. Source topology is neither preserved nor distilled into the output. |
| `mirror` | Lossless imported SVG/native-structure evidence | Restore source pages, Master/Layout identities and parentage, placeholder identity/bounds, ownership, and supported native-object metadata one-to-one. Lightweight projections are inspection views only. |

**Hard rule — mode-specific authorship**: `standard` and `fidelity` author new
project-canonical SVG documents. When one registered PowerPoint preset exactly
expresses one complete object, they use the compact canonical
`<g>` emitted by `preset_shape_svg.py`, following
[`native-shape-authoring.md`](../references/native-shape-authoring.md); its
paint comes from the confirmed brief and template `design_spec.md`. After
inserting the complete helper group, add only the registered structural
attributes required by its Master/Layout or object-slot role; geometry and
paint changes require a new helper render. `mirror` restores the expanded
lossless source contract and may only normalize transport details required by
the current compiler. Mirror never performs commonality
extraction, semantic synthesis, merge/split, promotion/demotion, renaming, or
re-parenting.

**Hard rule — multi-Master package boundary**: More than one Master is valid only when `mirror` restores the source graph or an authored template intentionally defines distinct reusable design families. `standard` / `fidelity` must not create one Master per Layout or duplicate equivalent Masters merely for organization. Every declared Master must own at least one emitted Layout, and every declared Layout must be selected by at least one prototype SVG so the complete graph can be compiled and verified.

| Package concern | Requirement |
|---|---|
| Theme ownership | Every registered Slide Master receives its own Theme part. Two Masters must never resolve to the same `ppt/theme/themeN.xml`. Theme cloning is exporter-owned; do not author or bundle Theme XML in the template workspace. |
| Creation identity | Any generated `p14:creationId` on Slides, Layouts, or Masters is a valid unsigned 32-bit value and unique across those parts. Cloned structural parts always receive fresh values. |
| Numeric registration | Master and Layout registration IDs are valid and unique in their owning lists; Layout numeric IDs are unique across the complete package, including across different Masters. |
| Relationship graph | The presentation registers the exact Master and Slide rosters; each Master registers exactly its owned Layouts; each Layout targets exactly one declared Master; each Slide targets exactly its declared Layout. |

SVG authors own the semantic roster, parentage, picker names, direct atoms, and slots. The exporter owns OOXML part cloning, Theme isolation, relationship registration, and package identity. Do not encode package repair workarounds in individual template SVGs.

Do not package `native_structure.json` or `source_template.pptx` as template inputs. In `standard` / `fidelity`, author Master/Layout direct semantic atoms and bounded slot groups deliberately from the intended reusable behavior. A validated compact canonical authored-preset `<g>` compiles to one native shape and therefore counts as one semantic atom; it may own a Master/Layout fixed layer or serve as the one direct carrier of an `object` slot. Ordinary groups are not structural atoms or single-object carriers. In `mirror`, use the lossless layered and flat SVGs plus inheritance/native facts to preserve source ownership. Recursively expand fixed Master/Layout group wrappers only because the structured contract requires semantic atoms; preserve transforms, styles, paint order, and appearance, and never flatten or regroup by semantic judgment.

`design_spec.md §V` records the newly authored roster for `standard` / `fidelity`. For `mirror`, add the `Source Restoration Map` required by [template-designer.md](../references/template-designer.md), with one row per source slide and its preserved Master/Layout assignment. Do not add a synthesis-decision table.

**Native-shape metadata boundary**: The lightweight authoring projection
removes opaque payload only from model context; it never becomes the
restoration source. `standard` / `fidelity` use helper-generated compact
canonical preset groups and project SVG/assets rather than copied source
payload. `mirror` preserves the expanded lossless representation and reuses
only native metadata already supported by the converter on unchanged
Slide-local/slot objects. Fixed layers are normalized to semantic atoms;
unsupported or edited objects keep the current SVG fallback and are reported
rather than silently replaced by stale metadata. Do not reproduce the preset
syntax here; its single authority is
[`shared-standards.md`](../references/shared-standards.md), with selection and
usage guidance in the native-shape reference.

Downstream, both template-adherence choices use `pptx_structure.mode: structured`. `page_layouts` selects one complete authoring prototype per page, `pptx_masters` / `pptx_layouts` declare unique reusable definitions, and `page_pptx_layouts` assigns generated pages. Strict preserves the selected prototype contract. Adaptive keeps its Master and may explicitly create and assign a new Layout key/name while authoring the page that needs it. A retained Layout may remain unassigned while still registering through its definition SVG. A mirror-created package does not force a future generated deck to keep the source page count or order.

**Apply the visual-fidelity decision from Step 3 to authored modes**: in `standard` / `fidelity`, pages marked `literal` reproduce the selected reference geometry and decoration while still using a newly designed structure; pages marked `adapted` may evolve the composition. Mirror restores every supported source visual and does not use this authored-page distinction.

**Sprite-sheet preservation (do NOT simplify away)**: PPTX-exported assets are often sprite sheets — a single tall/large image referenced from multiple slides, each cropping a different region via nested `<svg ... viewBox="...">` wrappers around `<image width="1" height="1">`. This nesting is **load-bearing geometry**, not redundant structure. When rebuilding, preserve the exact `viewBox` crop and the outer `<svg>` placement for every image; do not flatten to a single `<image>` with direct `x/y/width/height`. Verify by sampling: if any asset's pixel dimensions don't match the on-page display aspect, it is a sprite and the wrapper must stay.

**Mirror-mode restoration contract** (type A or B): when `Replication mode: mirror`, the Template_Designer role:

1. **Restores one output SVG per source page** in `<template_workspace>/templates/`. Use lightweight projections for inspection, but materialize from the matching lossless source and native structure facts. Preserve source Master/Layout keys and picker names, Layout parentage, slide assignment, placeholder type/index/bounds, ownership, paint order, and supported native metadata. Mechanical namespace, root-declaration, asset-path, and fixed-layer group normalization is allowed only when source ownership and appearance remain unchanged.
   - Type A restoration source: `<import_workspace>/svg/`, `<import_workspace>/svg-flat/`, `svg/inheritance.json`, and `native_structure.json`
   - Type B restoration source: the complete explicit source SVG contract; `authoring-svg/` remains inspection-only
   - For every source Layout unused by all source slides, additionally restore one definition-only SVG named `layout_<layout_key>.svg` from its lossless Master/Layout projections. It carries the exact root identity, fixed atoms, and placeholder contract but is not a generated page assignment. Use source placeholder prompts/carriers; do not invent business content. This definition SVG lets downstream export register the Layout and any otherwise-unused parent Master without retaining an internal carrier slide.
2. **Renames each file** using the source-order-first convention `<NNN>_<page_type>.svg`, where `<NNN>` is the source-order index zero-padded to 3 digits and `<page_type>` is typically `cover` / `toc` / `chapter` / `content` / `ending` (fall back to `content` when the type cannot be confidently classified). Examples: `001_cover.svg`, `002_toc.svg`, `003_content.svg`, ..., `050_ending.svg`.
   - Type A: derive `<page_type>` from `manifest.json.pageTypeCandidates`
   - Type B: derive `<page_type>` from the source filename when it follows the PPT Master convention (`01_cover.svg` → `cover`, `03a_content_two_col.svg` → `content`); otherwise infer from page content or fall back to `content`
3. **Routes bundled assets through the common workspace contract** and rewrites every `<image href="...">` consistently. Keep stable source asset identity in mirror; do not rename, merge, or replace assets by semantic judgment.
   - Type A: assets come from `<import_workspace>/assets/`
   - Type B: resolve relative paths in source `<image href="...">` against the source SVG location and copy each unique asset; if the source already follows PPT Master conventions (assets co-located with SVGs in the same directory), copy the whole asset set and then rewrite paths
   - Both scopes: write bitmaps to `<template_workspace>/images/`, point SVG references at `../images/<name>`, and keep non-bitmap template-source assets under `<template_workspace>/templates/`.
4. **Copies `icons/` when present** and preserves every adopted `<use data-icon="..."/>` reference. Both scopes write the package/validation copy to `<template_workspace>/templates/icons/` and an identical runtime copy to `<template_workspace>/icons/`. Do not inline these assets manually in the template working SVGs; the shared icon embedding path owns re-inlining before export.
5. Writes `design_spec.md` per [template-designer.md](../references/template-designer.md) §1. The §V Page Roster remains the content-fit index; explicit SVG metadata is the native Master/Layout contract. Mirror is only the template-creation replication mode; downstream generation still treats the finished package as a selectable / reusable roster, not as a forced 1:1 slide sequence.

Mirror mode does not simplify the visual target or synthesize layer ownership. The sprite-sheet preservation rule applies because crop wrappers carry visible geometry; preserve those wrappers and their source scope faithfully.

**Expected outputs from this step** (full spec → [template-designer.md](../references/template-designer.md)):

1. `design_spec.md` — **personality only**. Required sections: Template Overview, Color Scheme, Signature Design Elements, Page Roster (matching the actual SVG files on disk). Skip Typography / Assets / Placeholder Overrides when they would just restate defaults. Declare portable brief frontmatter; `register_template.py` consumes it only in library scope. **Do not** restate generic SVG constraints, layout pattern libraries, font-size ratio bands, the canonical placeholder table, or content methodology — those are sourced from `shared-standards.md` / `design_spec_reference.md` / `strategist.md` and are already in the downstream reader's context. Full scope rule and skeleton: [template-designer.md §1](../references/template-designer.md#1-must-generate-design_specmd).
2. Page roster — see [Page Roster](../references/template-designer.md#page-roster) for `standard` / `fidelity` / `mirror` mode rosters, variant naming, and TOC handling
3. Placeholder vocabulary — pages should adopt the conventional names (`{{TITLE}}`, `{{CONTENT_AREA}}`, ...) when they fit. Full reference: [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). When a template style legitimately needs different vocabulary (consulting → `{{KEY_MESSAGE}}`, branded cover → `{{BRAND_LOGO}}`), declare a `placeholders:` block in `design_spec.md` frontmatter so the registrar and quality checker treat it as the template's authoritative contract. **Avoid** one-off indexed families such as `{{CHAPTER_01_TITLE}}` — use the indexed TOC pattern instead.
   - `{{...}}` placeholders are the authoring vocabulary used to generate final slide content. Each emitted SVG also carries the native reconstruction contract: root Master/Layout key/name, direct atomic Master/Layout elements, and direct slot `<g>` elements with explicit design-zone bounds plus exactly one compatible carrier. A validated compact canonical authored-preset `<g>` counts as one semantic atom or one `object` carrier; ordinary groups do not. Composite regions use only the explicit `object` + `proxy` downgrade. Minimal structural `data-pptx-role` hints are added only when specialized metadata cannot express required behavior. Both strict and adaptive downstream set `mode: structured` and require complete `page_layouts`, `page_pptx_layouts`, `pptx_masters`, and `pptx_layouts` from planning onward.
4. Template assets (optional) — both scopes apply the same `templates/` / `images/` / dual-icon routing defined above

**Hard rule — placeholder examples are executable defaults**: In authored
`standard` / `fidelity` templates, a carrier is not a floating review label. It
becomes the prototype Slide placeholder, while
`data-pptx-placeholder-bounds` becomes the reusable Layout frame.

| Concern | Requirement |
|---|---|
| Full editable frame | `data-pptx-placeholder-bounds` describes the complete intended text, picture, chart, table, or object box. Never derive it from the sample text's glyph bounds or leave it as a one-line tight box. |
| Generic text entry | General `body` and text-carried `object` slots begin at the upper-left, use left paragraph alignment, and wrap inside the full frame. Title/subtitle alignment follows the authored composition. |
| Centered exceptions | Center alignment is reserved for semantically short focal content such as KPI values, short process nodes, hero statements, and compact takeaways. Record a template-wide exception in `design_spec.md §IV` when it is part of the layout grammar. |
| Review Slide binding | `template_preview_pptx.py` sizes each authored Slide carrier to the same complete frame as its registered Layout placeholder. A review deck whose Slide carrier is only the prompt text's tight box fails Step 6. |
| Mirror boundary | `mirror` preserves source Slide carrier geometry exactly; do not normalize it to the Layout frame when the source intentionally overrides that frame. |

---

## Step 5: Validate Template Assets

Set `<template_source>` to `<template_workspace>/templates/` in both scopes.

```bash
ls -la "<template_workspace>/templates"
ls -la "<template_workspace>/images" "<template_workspace>/icons"
```

Run SVG validation on the template directory:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_workspace>/templates" --template-mode --format <canvas_format>
```

`--template-mode` makes the checker:

- glob `*.svg` in the template directory directly (templates do not live under `svg_output/`)
- skip `spec_lock.md` drift checks (templates do not ship a spec_lock)
- enforce roster ↔ `design_spec.md` consistency as **errors** (orphan files / missing files break the template contract and, in library scope, the target kind's index)
- emit advisory **warnings** when a page lacks a conventional placeholder — these are hints, not failures. Declare a `placeholders:` block in `design_spec.md` frontmatter to silence them when your template intentionally uses a different vocabulary
- require every SVG root to declare one output Master and Layout; zero-slot Layouts are valid
- reject ordinary Master/Layout `<g>` elements, nested structure markers, missing slot bounds, and carrier-bound slots without exactly one compatible carrier; a validated compact canonical authored-preset `<g>` is the sole fixed-layer group exception and may be one `object` carrier
- validate cross-page Master equality plus same-key Layout atom/slot equality
- warn when distinct Layout keys have identical static framing/slot contracts. Resolve this for `standard` / `fidelity`; mirror may retain the distinct source identities and records that fact in its Source Restoration Map

This checker validates the authoring contract, not the compiled OOXML package. Theme ownership, package IDs, and registered part relationships are verified by `template_preview_pptx.py` in Step 6.

**Checklist**:

- [ ] `design_spec.md` follows the personality-only skeleton (Overview / Color / Signature / Page Roster); generic constraints (SVG rules, pattern libraries, ratio bands, canonical placeholder table) are NOT restated. The source-derived basic norms are present as template-specific layout / image / density / asset rules, not generic advice. §V Page Roster lists every emitted page
- [ ] Every page declared in `design_spec.md §V Page Roster` exists as an SVG file in the template directory (and vice versa — no orphan files)
- [ ] Variant filenames follow the letter-suffix convention (e.g. `03a_content_two_col.svg`); variants typically reuse the parent type's placeholder set unless the spec frontmatter declares otherwise
- [ ] If TOC exists, placeholder pattern uses the canonical indexed form
- [ ] `design_spec.md` frontmatter declares `canvas_format`, `canvas_width`, `canvas_height`, and `canvas_viewbox`; PPTX/SVG-backed templates also declare `source_canvas_width`, `source_canvas_height`, and `source_viewbox`
- [ ] SVG `viewBox` matches the declared canvas dimensions, not just the aspect ratio (for `ppt169`: `0 0 1280 720`; for `banner`: `0 0 1920 1080`); `width` / `height`, if written, equal it
- [ ] Placeholder names follow the canonical convention where applicable; templates with intentionally different vocabularies (e.g. `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`) should declare a `placeholders:` frontmatter block to silence advisory warnings
- [ ] Asset files referenced by SVGs exist at their resolved paths. In both scopes, bitmap references resolve through `../images/`; no bitmap remains accidentally stranded in `templates/`
- [ ] `design_spec.md` frontmatter declares `native_structure_mode: structured`; no `native_structure.json` or `source_template.pptx` is packaged
- [ ] Every SVG root declares Master/Layout key and picker names; Master/Layout visuals are direct semantic atoms and obey the explicit paint-order contract. Ordinary `<g>` elements remain forbidden there; a validated helper-generated compact canonical preset `<g>` is the sole group exception because it compiles to one native shape. Structural `data-pptx-role` is used only when specialized metadata cannot express required package/page-number/animation behavior
- [ ] Every slot is a direct `<g id>` with explicit design-zone bounds and exactly one compatible direct carrier, or an explicit composite `object` proxy. A validated compact canonical preset `<g>` may be the one carrier of an `object` slot; an ordinary multi-object group may not. Zero-slot Layouts remain valid
- [ ] For `standard` / `fidelity`, every placeholder bound is the complete editable box rather than the current marker text's tight bounds; general body/object carriers begin at the upper-left and only intentional short focal roles remain centered
- [ ] `standard` / `fidelity` output SVGs and their Master/Layout/slot contracts were newly authored without preserving or distilling source topology
- [ ] Every additional authored Master represents a distinct reusable design family, not one Layout or an equivalent duplicate; every declared Master owns at least one emitted Layout and every declared Layout has at least one emitted prototype
- [ ] Mirror output preserves source slide order, Master/Layout identity and parentage, placeholder facts, and ownership; fixed-layer group expansion is mechanical and pixel-equivalent, and the Source Restoration Map lists every source slide
- [ ] Mirror preflight covered the complete source graph; each unused Layout has one `layout_<layout_key>.svg` definition prototype and each otherwise-unused Master is retained through at least one such Layout
- [ ] For `standard` / `fidelity`, no duplicate-Layout-contract warning remains; mirror may keep equivalent source Layout identities when the restoration map explains them
- [ ] Lightweight projections were used only for inspection. Mirror materialized from lossless sources, reused only converter-supported metadata on unchanged Slide-local/slot objects, and kept fixed Master/Layout visuals as direct atoms
- [ ] If any SVG references an extracted vector `data-icon`, the corresponding SVG asset exists under `<template_workspace>/templates/icons/` and the identical runtime copy exists under `<template_workspace>/icons/`; do not add a separate illustration embedding script
- [ ] For `fidelity` mode: every sprite-sheet asset retains its nested `<svg viewBox=...>` crop wrapper; no image whose file aspect differs from its on-page aspect was flattened to a bare `<image>`
- [ ] For `mirror` mode: source-page SVG count equals source page count, while additional files are exactly the required `layout_<layout_key>.svg` definitions for unused source Layouts; source-page filenames follow the `<NNN>_<page_type>.svg` convention; **no new `{{...}}` authoring placeholders were inserted into restored source-page SVGs**; §V Page Roster lists every emitted file and marks definition-only prototypes explicitly

This step is a **hard gate**. Do not generate a review PPTX, register, or hand the workspace to the main pipeline until validation passes. A one-Master template may skip Step 6 when no review was requested; a multi-Master template must continue to Step 6 and may not register or complete before that package gate passes.

---

## Step 6: Template Review PPTX and Multi-Master Package Gate

**Trigger**: Run when the user requests a PowerPoint review file **or** when the validated SVG roster declares more than one unique Master key. A multi-Master template requires this step even when no review artifact was requested. A one-Master template may skip directly to Step 7 when the user did not request a review file.

Export the complete SVG roster, one prototype per slide, from the workspace root:

```bash
python3 skills/ppt-master/scripts/template_preview_pptx.py "<template_workspace>"
```

The default output is `<template_workspace>/exports/<template_id>_template_preview.pptx`; the command creates `exports/` on demand. The script consumes `templates/*.svg` directly, compiles the declared structured Master/Layout contract, and reopens the result. It does not require a project `spec_lock.md`, does not create an intermediate project, and does not infer or distill structure.

The first export refuses an existing output. After intentionally fixing the template and replacing its prior review deck, rerun with `--force`; never rely on a silent overwrite:

```bash
python3 skills/ppt-master/scripts/template_preview_pptx.py "<template_workspace>" --force
```

**Validation**:

- [ ] Review PPTX exists under `<template_workspace>/exports/`
- [ ] PPTX slide count equals the template SVG roster count
- [ ] Package read-back reports the expected Master and Layout counts
- [ ] The presentation registers the exact Master and Slide rosters; every Master registers exactly its owned Layouts; every Layout and Slide relationship resolves to its declared parent
- [ ] Every registered Master targets a distinct Theme part; shared Theme ownership across structured Masters is a hard failure
- [ ] Generated `p14:creationId` values are valid and unique across Slides, Layouts, and Masters; Master/Layout numeric registration IDs are valid and unique in their required scopes
- [ ] For `standard` / `fidelity`, every carrier-bound placeholder on each review Slide has exactly the same type, effective index, and full frame as its registered Layout placeholder; `template_preview_pptx.py` verifies this automatically
- [ ] For `mirror`, source Slide-local placeholder geometry remains unchanged even when it differs from the Layout default frame
- [ ] The user can open one file and review every template page in deterministic filename order
- [ ] When Microsoft PowerPoint is available for acceptance testing, the file opens without a repair prompt and every emitted Layout appears under its intended Master. When PowerPoint is unavailable, report package read-back as the verified evidence and do not claim a PowerPoint-open result

`template_preview_pptx.py` automatically enforces the deterministic package checks above during read-back. Every applicable validation item is a hard gate for the review artifact. Fix the owning SVG/spec/asset or exporter defect before reporting the preview as verified. For a multi-Master template, any Step 6 failure blocks registration and completion; for a one-Master template, failure of an unrequested preview does not block a workspace that already passed Step 5.

---

## Step 7: Register Template in Library Index (Library Scope Only)

Branch on the confirmed output scope:

| Scope | Action |
|---|---|
| `library` | Run the registrar below after Step 5 passes and Step 6 also passes whenever it was requested or required by a multi-Master roster |
| `project` | Skip the registrar entirely. Do not edit `decks_index.json`, `layouts_index.json`, or any library README; continue to Step 8 with index status `Not registered (project workspace)` |

Run the unified registrar with the kind flag; it derives the corresponding index entry from `templates/design_spec.md` (frontmatter when present, prose fallback otherwise) plus the actual `templates/*.svg` file list. The registrar retains read compatibility with old flat library packages; new creation never writes that shape:

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

The completion card's file roster is collected by globbing `templates/*.svg` in the workspace. Legacy flat packages still use their root `*.svg` roster.

The index file is a **discovery index** — it lets the AI answer "what templates are available?" by listing names and workspace-root paths. It is **not** consulted to trigger Step 3 (SKILL.md). Step 3 triggers on an explicit workspace-root path supplied by the user, regardless of whether that path is registered. An unregistered workspace still works when the user gives its path; it just will not appear in discovery listings.

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
> # All current deck/layout templates rebuild the current structured SVG contract.
> # Downstream strict/adaptive use is confirmed by Strategist and is not stored here.
> native_structure_mode: structured
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

## Step 8: Output Confirmation

Produce one scope-aware, evidence-driven completion card for either location:

```markdown
## Template Creation Complete

**Template Name**: <template_id> (<display_name>)
**Kind**: deck | layout
**Output Scope**: library | project
**Workspace Path**: `<template_workspace>/`
**Template Source**: `<template_workspace>/templates/`
**Bitmap Path**: `<template_workspace>/images/`  ← omit when absent
**Runtime Icon Path**: `<template_workspace>/icons/`  ← omit when absent
**Review PPTX**: `<template_workspace>/exports/<template_id>_template_preview.pptx`  ← omit only when a one-Master template was not requested for review
**Primary Color**: <hex>  ← deck only; omit for layout
**Index Registration**: Done | Not registered (project workspace)

### Files Included

| File | Status |
|------|--------|
| `templates/01_cover.svg` | Done |
| `templates/02_toc.svg` | Done |
| `templates/03_chapter.svg` | Done |
| `templates/04_content.svg` | Done |
| `templates/05_ending.svg` | Done |
| `exports/<template_id>_template_preview.pptx` | Verified, when requested or required for multi-Master |
```

The next main-pipeline Step 3 input is the exact `<template_workspace>/` root in either scope. Step 3 resolves its `templates/design_spec.md`, ignores `exports/`, and copies or consumes `templates/` plus any existing `images/` and `icons/` as one unit. A legacy flat package root remains readable, but directory flatness alone is not a legacy Master/Layout condition and does not trigger `restore-pptx-structure`.

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
4. **Discovery requirement**: A library template is discoverable only after `register_template.py` has been run against it (Step 7). A project-scoped workspace intentionally stays out of global discovery and is consumed by its explicit workspace-root path.
5. **Review output**: Generate `exports/<template_id>_template_preview.pptx` on request and always for a multi-Master template. It is derived local evidence, never a source input during template application, and library exports stay Git-ignored.

> **Full role specification**: [template-designer.md](../references/template-designer.md)
