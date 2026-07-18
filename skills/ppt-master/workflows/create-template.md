---
description: Create Template entry workflow and shared contract for the Create Brand, Create Layout, and Create Deck sub-workflows.
---

# Create Template Workflow

> **Fixed entry name**: user-facing template creation always enters **Create Template**. This workflow selects exactly one child workflow — [`create-brand.md`](./create-template/create-brand.md), [`create-layout.md`](./create-template/create-layout.md), or [`create-deck.md`](./create-template/create-deck.md) — and owns their shared execution contract.
>
> **Role invoked for Create Layout/Create Deck**: [Template_Designer](../references/template-designer.md)

Create one reusable template workspace under either the **global template library** or `projects/` from one or more reference channels or a direct user brief, then dispatch to exactly one child workflow.

**Default — library scope**: Write `skills/ppt-master/templates/<kind_dir>/<template_id>/` and register it in the matching discovery index.

**Project scope**: Write the same portable workspace routing at `<project>/` and do not register any global index.

**Hard rule — one workspace routing contract**: Output scope changes only the workspace parent and index registration. Both scopes use required `templates/`, optional `images/` / `icons/`, and optional on-demand `exports/`, with the same relative asset references and validation command. Create Template must not create an optional directory or placeholder file solely to retain an empty path. An initialized project may already contain empty `images/`, `icons/`, or `exports/` scaffolding; leave it untouched, do not count it as template output, and omit the path from completion unless this workflow wrote or adopted a real file there. Do not maintain a library-only self-contained-flat package branch or a project-only thin-bundle branch.

> **Boundary against template-fill and in-place structure edits**: Create Template does not fill content into a PPTX, add Master/Layout structure to an existing PPTX/SVG, or directly output the user's final generated deck. It authors a separate reusable workspace; an optional PPTX is review evidence only. To generate a deck, return the workspace root to [`generate-pptx`](./generate-pptx.md) Step 3 and author new SVG pages from it. A project-scoped workspace is already installed at that project's Step 3 path and is consumed in place.

## Child Workflow Dispatch

Create Template is the fixed user-facing entry and common contract. It selects one child workflow, then that child owns the kind-specific lifecycle. Do not execute two children for one workspace or blend their schemas.

| Child workflow | Select when | Library-scope output | Exclusive responsibility |
|---|---|---|---|
| [`Create Brand`](./create-template/create-brand.md) | Reuse identity only: colors, typography, logo, voice, and icon style | `templates/brands/<brand_id>/` | Identity analysis and identity-only `design_spec.md`; no SVG roster |
| [`Create Layout`](./create-template/create-layout.md) | Reuse a brand-neutral structural skeleton without a recurring communication application | `templates/layouts/<layout_id>/` | Canvas, page grammar, semantic text roles, Master/Layout/slot contract, and SVG roster; no brand identity or application contract |
| [`Create Deck`](./create-template/create-deck.md) | Reuse a branded structural system or a recurring presentation application | `templates/decks/<deck_id>/` | Application contract, integrated identity/structure, content reuse policy, and SVG roster |

Select Create Brand only for identity-only intent. Select Create Layout only when identity remains downstream-selectable and the reusable artifact does not prescribe communication objectives, audience outcomes, a required narrative sequence, or scenario-specific starting content. Select Create Deck when structure carries brand identity or reusable application semantics. A complete source PPTX alone does not determine the kind: classify only the stable rules worth reusing. Ask one discriminator question only when the user's requested reusable artifact is genuinely ambiguous; once selected, enter that child workflow and do not repeat route selection inside its confirmation gate.

See [`templates/README.md`](../templates/README.md) for the shared kind and
workspace model. Downstream template application and fusion remain owned by
[`generate-pptx.md`](./generate-pptx.md) Step 3.

## Output scope — library (default) vs project

Output scope is a shared Create Template execution choice, not a new template kind or PPTX structure mode. Surface it in the Step 2 brief; do not invent a CLI flag or persist `output_scope` / `target_project` into portable `design_spec.md` frontmatter.

| Scope | `<template_workspace>` | Template source | Registration |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind_dir>/<template_id>/` | `<template_workspace>/templates/` | Run `register_template.py` against the matching global index |
| `project` | `<target_project>/` | `<template_workspace>/templates/` | Do not update any global index |

Both scopes write this contract:

```text
<template_workspace>/
├── templates/   # design_spec.md; Create Layout/Create Deck also write SVGs
├── images/      # optional; every bitmap; SVG href is ../images/<name>
├── icons/
│   └── imported/ # optional; one canonical copy of imported vector assets
└── exports/     # conditional; required package evidence for multi-Master templates
```

The review PPTX is derived evidence, not a source template asset. Create `exports/` only when a review deck is requested or the template declares more than one Master; multi-Master templates require the package-level gate in Step 6. Template application reads `templates/` plus any existing `images/` and `icons/`; it never copies or consumes `exports/`. Library `exports/` directories are Git-ignored.

For `project`, `target_project` is required and must be an existing project initialized by `project_manager.py init`. Before the first final-output write, run one complete preflight. Apply the same collision checks to a library workspace; the only difference is that its root is under the global kind directory:

1. Resolve `<template_workspace>` from the confirmed scope and confirm its required `templates/` destination plus any needed `images/` / `icons/` destinations.
2. Confirm `<template_workspace>/templates/` is empty.
3. Resolve every final bitmap and extracted-vector filename, then confirm none would overwrite an existing file in `images/` or `icons/imported/`. Check the review-PPTX destination when preview export was requested or a multi-Master template was confirmed.

Any failed check aborts before writing `design_spec.md`, SVGs, images, icons, or the review PPTX. Do not merge into a non-empty template source and do not overwrite a name conflict. Temporary Step 1 analysis workspaces remain allowed because they are not final outputs.

## Process Overview

```
Reference Bundle Intake & Analysis -> Fact-Based Brief Proposal -> User Confirmation Gate -> Preflight + Invoke Selected Child -> Validate Child Output -> [Structured Review PPTX: optional for one Master, required for multi-Master] -> [Register Library Index] -> Output
```

The first three steps derive the brief from facts, not guesses. **No final template directory may be created and no template SVG / `design_spec.md` may be written until `[TEMPLATE_BRIEF_CONFIRMED]` is emitted in Step 3.** Reference-analysis intermediates produced by `pptx_template_import.py` (typically under `/tmp/pptx_template_import/`) are explicitly **not** subject to this gate — they are temporary workspaces feeding Step 2.

After dispatch, the selected child workflow executes these shared steps with its kind fixed. Child-owned fields and validation rules come from that workflow; Create Template supplies the common mechanics and never reopens the child selection.

---

## Step 1: Reference Bundle Intake & Analysis

Run every applicable input branch for the reference bundle the user supplied. A bundle may contain one source, several files of one type, multiple source types, direct text in the conversation, or no external file. This step produces analysis artefacts only — it does **not** create the final template directory, write `design_spec.md`, or touch any template index. When Create Brand was selected, follow that child workflow's analysis rules and do not run page-topology analysis merely because the reference is a PPTX/PDF.

### Input source taxonomy

The rows are evidence channels, not mutually exclusive routes. Run every matching row and retain source-level provenance. The replication-mode column applies to Create Layout/Create Deck. Create Brand uses the same reference formats for identity evidence but has no replication mode, SVG roster, or native-structure path.

| Type | What the user supplied | Tool / read path | Replication modes available |
|------|-------------------------|------------------|------------------------------|
| **A** `.pptx` reference | A `.pptx` file path | `pptx_template_import.py` → `manifest.json` + `native_structure.json` + `source_template.pptx` + layered SVGs + `assets/`; flat verification SVGs are opt-in | `standard` / `fidelity` / `mirror` |
| **B** Existing SVG assets | `projects/<x>/svg_output/`, a current template workspace root, a legacy flat template root, or a loose `.svg` folder | Normalize the source directory, create an editable authoring IR bundle with `svg_authoring_view.py`, then use its page SVGs; also read companion `design_spec.md` / `spec_lock.md` when present | `standard` / `fidelity`; `mirror` only when the source already carries a complete explicit Master/Layout/placeholder/native-object contract |
| **C** Image / visual references | PNG/JPG/WebP images, screenshots, moodboards, PDF page visuals, or a visual-reference folder | `ls` + `Read` each supplied visual or PDF (multimodal recognition) | `standard` only by itself |
| **D** Text / document / website / asset references | Direct conversation text, pasted requirements, Markdown/TXT, DOCX/PDF/HTML/URL, brand/design manuals, or supplied logo/icon/font assets | Use direct text as-is; read plain text/Markdown; convert supported documents/URLs with `source_to_md.py` into a temporary analysis workspace; inventory explicit assets | `standard` only by itself |
| **E** No reference material | A template request with no external source and no substantive brief yet | Skip analysis; collect every required value in Steps 2–3 | `standard` only |

| Bundle rule | Behavior |
|---|---|
| Combine channels | `standard` may use every confirmed visual, textual, documentary, web, and asset source together. Do not force the user to choose one source type. |
| Determine mode eligibility | `fidelity` requires Type A or B page evidence. `mirror` requires Type A or a complete current Type B structure contract. Type C/D/E evidence may supplement an eligible bundle but never creates native topology. |
| Preserve provenance | Keep facts, explicit user decisions, and AI suggestions distinct. Surface contradictions in Step 2 instead of resolving them silently. |
| Protect mirror | Supplemental text, images, websites, or assets may explain the source but cannot alter a confirmed `mirror` graph or visuals. Use `standard` / `fidelity` when the user wants those inputs to change the resulting system. |

Type A is the canonical mirror path: `manifest.json`, `native_structure.json`, layered lossless `svg/`, and inheritance facts describe the native structure that still exists in the PPTX package. Optional `svg-flat/` files are complete-page verification views, never structure authority. In `standard` / `fidelity`, imported facts and visuals do not define output topology.

**Type B source normalization**: when the supplied root contains `templates/design_spec.md`, use `<input>/templates/` as the SVG/spec source and resolve its workspace assets from sibling `<input>/images/` and `<input>/icons/`. Otherwise, use the supplied directory itself as the legacy-flat/loose SVG source. Directory flatness is not a semantic-structure signal.

Type B is supported with caveats:

- **mirror on type B** — require a complete current explicit source contract. Preserve page count/order, literal visuals, root Master/Layout identities, slot metadata, supported native-object metadata, and source ownership in the **new** workspace. Page type for `<NNN>_<page_type>.svg` is read from the source filename when it follows the PPT Master naming convention (`01_cover.svg` → `cover`, `03a_content_two_col.svg` → `content`); fall back to `content` otherwise. A loose visual-only SVG folder has no native structure to preserve and cannot use mirror.
- **fidelity on type B** — inspect the complete page roster as visual reference, then design a broader new roster and its own Master/Layout/slot system. Existing keys, families, and repeated source chrome are not output-topology inputs.
- **legacy or unstructured type B** — old `baseline` / `preserve` / `layout_strategy: distill` / `data-pptx-layout-kind` / direct-atomic-placeholder inputs, and SVGs with no root Master identity, are visual/contextual reference for `standard` / `fidelity` only. Author a new current contract in the output workspace. Use the original PPTX Type A path when existing native Master/Layout facts must be mirrored; do not mutate the SVG source or claim topology recovery from incomplete metadata.
- **selected free-design subset on type B** — ingest only the explicitly named pages as visual reference, then author a new current structured contract in the output workspace. Do not scan or copy the whole `svg_output/` directory or silently turn unselected pages into template variants.

**Replication mode boundary**: `standard` and `fidelity` are authored modes: source visuals/assets guide a new SVG roster and a newly designed Master/Layout/slot system, without preserving or distilling source topology. `mirror` is a native-preservation mode: only Master/Layout/placeholder/ownership facts that exist in a PPTX package or complete current Type B contract are authoritative. Mirror may mechanically normalize transport representation for the current compiler, including fixed-layer group expansion, but it never infers missing historical intent or modifies the input. Because mirror preserves supported visual and application facts, Create Layout may use it only when the source contract already satisfies the Layout boundary: brand-neutral and application-neutral. A source outside that boundary must use `standard` or `fidelity` to author a new Layout, or retain those facts through Create Deck. The modes create a template workspace, not a downstream generated deck; future decks are authored anew and do not inherit the source page count/order requirement.

### 1A. `.pptx` reference

Run the unified preparation helper:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py "<reference_template.pptx>"
```

This produces, in one workspace:

- `manifest.json` — single source of truth: slide size, theme colors, fonts, per-master theme summaries, asset inventory, placeholder metadata, SVG file paths, per-slide / per-layout / per-master metadata (including source-owned inherited-shape visibility), page-type candidates
- `native_structure.json` — analysis contract: stable master/layout keys, layout picker names, placeholder type/index/geometry, inherited-shape visibility, source hash, and source-graph quality facts
- `source_template.pptx` — byte-preserved analysis copy for visual/package cross-checking; it is not copied into the final template package
- `assets/` — extracted reusable image assets; `manifest.json` owns the asset-name mapping and SVG `href` values reuse that mapping
- `conversion-report.json` — source-recovery and fidelity diagnostics; retain it for audit because these warnings are not duplicated in the structural manifests
- `svg/` — **primary view** (layered template view):
  - `svg/master_*.svg` — every slide master in the deck rendered once, including masters that no sample slide currently uses (template packages routinely ship more masters than the visible samples reference)
  - `svg/layout_*.svg` — every slide layout in the deck rendered once (its own contribution; master shapes do **not** repeat here)
  - `svg/slide_NN.svg` — each slide's own shapes and slide-local background; master / layout shapes and backgrounds are **not** inlined here
  - `svg/inheritance.json` — which Layout/Master each Slide consumes plus source-owned `showInheritedShapes` / `showMasterShapes` booleans; Layout shapes follow the Slide's `showInheritedShapes`, while Master shapes require that value and the referenced Layout's `showMasterShapes`; backgrounds remain independent
- `svg-flat/` — **optional verification view** (only with `--inheritance-mode both`; one self-contained SVG per slide):
  - `svg-flat/slide_NN.svg` — effective Master/Layout contributions permitted by the source visibility flags plus Slide-local content, painted into one SVG so opening any slide on its own shows the full page like PowerPoint would. Background inheritance remains independent. Use this for previews / screenshot pipelines / "what does the slide actually look like" sanity checks.
- The default `--inheritance-mode layered` emits only the canonical layered view. Pass `both` when a separate complete-page verification tree is worth the storage cost, or `flat` for round-trip use cases (legacy: `svg/` becomes self-contained slides without the master/layout/inheritance files).
- The importer does not generate a duplicate narrative summary or persistent SVG-size CSV. Read compact facts from `manifest.json`; run ad hoc size measurements outside the canonical workspace when needed.

Import fidelity rules:

- Placeholder metadata is recorded in `manifest.json`; master / layout SVGs show lightweight dashed guides with labels only in `svg/`, not in `svg-flat/`.
- Charts, SmartArt, diagrams, and OLE objects are typed placeholders in `svg/`. In `svg-flat/`, they use a preview image with a small badge when one exists; otherwise they stay visible as placeholders. Tables are converted to real SVG.
- Missing media and external linked images fail the import. EMF / WMF Office vector media are converted to PNG previews when supported by the local toolchain; otherwise the import fails.

It is an analysis aid, not a final direct template conversion.

**Lossless payload backing + editable authoring IR**:

Keep `<import_workspace>/svg/` unchanged as lossless native-payload backing. If the optional `<import_workspace>/svg-flat/` verification tree was requested, keep it unchanged too. Before the Template_Designer reads or edits any imported page SVG, create the canonical non-destructive authoring IR bundle:

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<import_workspace>/svg" -o "<import_workspace>/authoring-svg" --projection-kind layered
```

Only when the import explicitly used `--inheritance-mode both`, create the optional complete-page verification IR:

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<import_workspace>/svg-flat" -o "<import_workspace>/authoring-svg-flat" --projection-kind flat
```

Each bundle contains editable SVGs, a model-readable `authoring_summary.json`, and a tool-only `authoring_manifest.json`. The projection removes opaque text payload, duplicate hidden geometry carriers, and import-only identity attributes while keeping visible shape intent, compact preset/frame metadata, structure markers, logical ids, valid asset references, and a reserved `data-pptx-source-ref` on each imported logical object. Model-facing `data-pptx-frame` values and safe transform page coordinates use at most two decimals; normalized crop ratios, path geometry, transform linear coefficients, and the immutable lossless source retain their required precision. The summary lists the current SVG roster plus per-file canvas, size, text, image, vector, placeholder, and source-ref counts. The machine manifest records relative source files, document hashes, source paths, and initial authoring-subtree hashes; it does not duplicate opaque payload and MUST NOT enter model context. Source refs are unique within one document and are interpreted by tools together with that document's manifest record.

In-place vector and picture normalization refreshes the summary automatically.
After any other direct IR edit, refresh it before the next analysis pass:

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<import_workspace>/authoring-svg" --refresh-summary
```

`authoring-svg/` is the canonical editable IR for template creation. The lossless trees are read only by materialization when an unchanged referenced object needs supported native payload or fallback evidence. Do not edit or copy the lossless SVGs directly. The IR is not a finished template directory and must be materialized into validated `<template_workspace>/templates/*.svg` before preview or export.

For a Type A `mirror`, final materialization is owned by
`mirror_template_materialize.py`; never assemble the structured output by
copying lossless SVGs or `svg-flat/` pages into `templates/`. The command runs
only after the confirmed IR edits and vector-readability pass described below.
`standard` / `fidelity` remain newly authored Template_Designer output and do
not use this compiler.

**Vector illustration readability pass**:

Factor large decorative vector groups out of the lightweight IR documents so the model-facing SVGs stay readable while export remains native shapes. Never run this in place on the lossless import SVGs:

```bash
# layered view — primary read surface and canonical extracted-vector inventory
python3 skills/ppt-master/scripts/extract_svg_assets.py "<import_workspace>/authoring-svg" --icons-dir "<import_workspace>/icons" --icon-namespace imported --inplace --id-prefix layered --min-decoration-bytes 3000 --clean-stale

# optional flat verification view — run only when authoring-svg-flat/ exists;
# reuse matching layered assets so only genuinely flat-only vectors create files
python3 skills/ppt-master/scripts/extract_svg_assets.py "<import_workspace>/authoring-svg-flat" --icons-dir "<import_workspace>/icons" --icon-namespace imported --reuse-inventory "<import_workspace>/authoring-svg_vector_asset_inventory.json" --inplace --id-prefix flat --min-decoration-bytes 3000 --clean-stale
```

The authoring SVGs in `<import_workspace>/authoring-svg/` and, when requested, `<import_workspace>/authoring-svg-flat/` are rewritten in place with compact `<use data-icon="imported/..."/>` placeholders. Each in-place extraction refreshes that bundle's `authoring_summary.json` automatically. Extracted assets have one canonical copy under `<import_workspace>/icons/imported/`; never duplicate them under `templates/icons/`. The root `icons/` directory remains a namespace container and must not contain rewritten page SVGs or inventories. The inventory is written beside the processed IR directory and records every preserved `data-pptx-source-ref`; re-inlining an asset therefore re-establishes the referenced object mapping before materialization. The existing icon embedding path re-inlines the extracted assets before final export, preserving multi-color artwork and non-square viewBox geometry as native SVG shapes. Text-bearing groups are never extracted; text must stay readable/editable in the working SVG. Extraction triggers on either many drawable elements or a large pure-vector XML block, so long single-path illustrations are factored out too. Pure-vector decoration runs inside text-bearing groups use a lower size threshold, allowing card borders and decorative paths to be extracted without hiding text. Referenced defs (`gradient` / `pattern` / `filter` / `clipPath` / `marker`) are copied into each asset and namespaced so the asset is self-contained after re-inline. If both layered and flat views are processed into the same icon namespace, keep distinct `--id-prefix` values to avoid asset ID collisions. `--clean-stale` removes only stale generated assets for the current SVG filenames and prefix inside the selected namespace; it is safe in this import workspace but should not be used against a shared hand-curated icon directory without a specific prefix.

The layered pass owns the canonical extracted-vector pool. Each new asset records a source fingerprint before generated ID namespacing. The flat pass MUST consume the layered inventory through `--reuse-inventory`: an exact fingerprint match writes only a `<use>` reference to the existing layered asset, while an unmatched flat-only subtree may create one new asset under the `flat` prefix. Do not independently extract the two views into parallel asset sets. With `--clean-stale`, a rerun also removes obsolete generated `flat_*` duplicates while retaining every reused layered reference.

**Explicit complex-SVG picture normalization (optional; `standard` / `fidelity` only)**:

When one imported native group is deliberately being retained as one complex
SVG picture rather than rebuilt as editable paths, select its exact id in the
layered authoring IR and normalize it explicitly:

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
tree remains unchanged and authoritative. Any optional `svg-flat/` tree remains
unchanged but is verification-only.

`extract_svg_assets.py` remains a different operation: it factors vectors out
for model readability and re-inlines them as native shapes before export. It
does not turn those vectors into a picture.

**Read order during analysis**:

| Mode | Required read set |
|---|---|
| `standard` / `fidelity` | `manifest.json`, exported assets, `svg/inheritance.json`, `authoring-svg/authoring_summary.json`, and every cleaned layered IR document (`authoring-svg/master_*.svg` / `layout_*.svg` / `slide_NN.svg`). Do not read `authoring_manifest.json`; it is compiler-only. The layered IR is the complete read surface: it covers Layouts unused by any sample slide (invisible in `svg-flat/` yet still template vocabulary), and per-page composition follows from `inheritance.json`. Cleaned flat pages are optional composition spot checks, not a required second pass over the same shapes. Source topology remains non-binding; the two modes differ in output design (`fidelity` designs a broader roster covering the useful visual range), not in read coverage. |
| `mirror` | `manifest.json`, `native_structure.json`, `svg/inheritance.json`, `authoring-svg/authoring_summary.json`, and every cleaned layered Master/Layout/Slide IR document. Do not read `authoring_manifest.json`; `mirror_template_materialize.py` loads and validates it internally. The layered `authoring-svg/` tree is the sole editable and materialization input. Cleaned `authoring-svg-flat/` slides are optional visual composition checks only; never edit or feed them into template materialization. Materialization may resolve unchanged refs against the matching lossless backing without placing opaque payload in model context. |

Use the compact facts in `manifest.json` for orientation. Use screenshots or the original PPTX only for visual cross-checking. Do not bulk-read opaque lossless payload into model context.

Interpretation rule (carries forward into Steps 2 and 4):

- `manifest.json` is the source of truth for facts about the source deck: slide size, theme colors, fonts, background inheritance, reusable asset inventory, declared source layout/master structure, and slide reuse relationships. It dictates which source facts mirror may preserve during materialization, but not `standard` / `fidelity` output topology.
- `authoring_summary.json` is the model-facing index for the current authoring SVG roster and readability statistics. Regenerate it after direct IR edits before analysis.
- `authoring_manifest.json` is machine-only provenance. Do not open or quote it in model context; the mirror compiler validates it internally against the edited IR and immutable backing.
- `native_structure.json` is the source of truth for source PowerPoint identity: stable layout keys, picker names, parent masters, placeholder types/indices, and the source-package hash. Mirror preserves those facts one-to-one. `standard` / `fidelity` do not mine them into the new structure.
- `manifest.json`, `native_structure.json`, and `svg/inheritance.json` intentionally overlap only at contract boundaries so materialization can cross-check source identity, graph ownership, and visibility; do not collapse them into a cache or substitute one for another
- exported `assets/` are the canonical reusable image pool — `<image>` references in `svg/` already point at these files directly
- exported `icons/imported/*.svg` files are the canonical reusable vector illustration pool, but they are **not** part of the default read set. Use `authoring_summary.json` `icon_refs` and the cleaned SVGs first. Query `*_vector_asset_inventory.json` by an exact asset id only when source-ref or fingerprint detail is required; do not load the complete inventory into model context. Open a specific imported SVG only when that asset affects the current design decision.
- cleaned layered authoring SVGs are the mirror editing and verification surface; they expose source ownership without requiring the model to read opaque payload. Do not use them to promote, demote, merge, or split source structure.
- cleaned complete-page IR documents are optional composition spot checks for authored modes and verification views for mirror. They never replace the layered editable IR or immutable payload backing.
- screenshots remain useful for judging composition and style, but should not override extracted factual metadata unless the import result is clearly incomplete

**Mirror complete-graph gate**: compare every `native_structure.json` Layout
and Master with the layered `authoring_summary.json` roster before offering `mirror`.
Every source Layout—including one unused by all source slides—must have a
layered IR document and matching payload backing from which a reusable
definition SVG can be materialized. Every source Master must own at least one retained Layout. Missing IR documents
or ambiguous parentage are blocking; unused identities themselves are supported
and must not be dropped. The compiler performs the exact source-ref and hash
checks from `authoring_manifest.json`.

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
| Native PowerPoint structure | `native_structure.json` plus inheritance facts | Mirror maps the validated source graph one-to-one into a new workspace. Standard/fidelity author an independent output graph and do not distill source common structure. |

Distinguish observed facts from template rules: "`slide_07` uses a left photo crop" is a fact; "content pages may use a left photo rail for location / product / case-study pages" is the reusable rule.

**Read gate**:

- `standard` / `fidelity`: read `authoring_summary.json`, every layered IR Master, Layout, and Slide, and the inheritance map; flat pages are optional spot checks
- `mirror`: read `authoring_summary.json`, verify and report every layered IR Master, Layout, and Slide plus the inheritance map, and leave `authoring_manifest.json` to the compiler

Do not treat authoring IR documents as final template assets. `standard` / `fidelity` author new SVGs from the confirmed brief and IR references. Mirror edits the IR and materializes it with lossless native-payload backing.

> **Mirror-mode materialization path** — use `native_structure.json` and `svg/inheritance.json` as model-readable structural authority. The cleaned layered IR is the editable source, `authoring_summary.json` is its model-facing index, and lossless layered SVGs are immutable payload backing; optional flat SVGs are verification-only. `mirror_template_materialize.py` consumes the machine manifest internally. Preserve only the roster, appearance, ownership, placeholders, converter-supported native metadata, and available SVG fallbacks that are actually present and validated; do not synthesize missing facts or a different graph.

### 1B. Existing SVG assets

First resolve the Type B source directory using the rule above. Create a non-destructive authoring IR bundle in a throwaway analysis workspace, then run the same vector readability pass only on that IR. Do **not** rewrite the user's original source directory in place.

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<normalized_svg_source>" -o "<svg_analysis_workspace>/authoring-svg" --projection-kind generic
python3 skills/ppt-master/scripts/extract_svg_assets.py "<svg_analysis_workspace>/authoring-svg" --icons-dir "<svg_analysis_workspace>/icons" --icon-namespace imported --inplace --id-prefix source --min-decoration-bytes 3000 --clean-stale
```

If the source contains one deliberately selected complex subtree that should
remain a single SVG picture, apply the explicit normalization above only to the
analysis IR. Set `--resource-root` to the narrowest workspace directory
that contains both the IR and every local dependency referenced by the
selected group. This does not authorize automatic group selection or mutation
of the user's original SVG directory.

Then read `authoring-svg/authoring_summary.json`, `ls` the analysis workspace,
and read every cleaned `authoring-svg/*.svg` to extract:

- canvas size (`viewBox` on the root `<svg>`)
- recurring colors (`fill` / `stroke` values; identify the dominant 2–4 hex codes as candidate theme colors)
- fonts (`font-family` attributes on `<text>`)
- placeholder usage (existing `{{...}}` strings, if any)
- structural decoration (recurring `<rect>` bars, `<path>` motifs, embedded `<image>` references)

Use `authoring_summary.json` `icon_refs` before opening individual
`<svg_analysis_workspace>/icons/imported/*.svg`. Query the generated
`*_vector_asset_inventory.json` by exact asset id only when provenance,
source-ref, or fingerprint detail is required. Do not bulk-read the inventory
or extracted vectors unless a specific asset affects a design decision or is
selected for mirror preservation.

If a `design_spec.md` or `spec_lock.md` accompanies the SVGs, read it too. In mirror it is part of the source contract and must agree with the SVG identities; in `standard` / `fidelity` it is visual/contextual reference only. Record the equivalent of a `manifest.json`'s factual fields in analysis notes so Step 2 can label them `[fact]`.

### 1C. Image / visual references

`ls` the folder (or single file) and `Read` each image / PDF page. Extract what's visible:

- rough theme colors (eyeball the dominant 2–4 hues; do NOT report exact HEX as fact)
- page count (count the supplied images as an approximate slide count)
- dominant typography style (sans / serif / display) — never report a font name
- decorative motifs and composition rhythm

Be explicit in Step 2 that exact HEX values, font names, and placeholder structure are **estimates from visual inspection** (`[suggested]`), never `[fact]`.

### 1D. Text, document, website, and asset references

Direct text in the conversation is already a valid input; do not require the user to save it as a file. Read Markdown/TXT directly. Convert supported document or website inputs into a temporary analysis workspace so the reference file or final template workspace is not modified:

```bash
python3 skills/ppt-master/scripts/source_to_md.py "<file_or_URL_or_dir>" -o "<text_analysis_workspace>"
```

Inventory explicitly supplied logo, icon, font, and other brand/design assets. Raster assets also enter the Type C visual pass; readable SVG assets may additionally enter Type B when they are page/template SVGs. Do not infer asset licensing, official status, or native PowerPoint structure from filenames alone.

Extract only what the source actually states:

- Identity rules: colors, typography, logo usage, voice, icon style, and explicit exclusions.
- Structure rules: canvas, page types, grids, zones, placeholders, density, image behavior, and requested variants.
- Deck application: recurring situations, intended audiences/outcomes, delivery or reading assumptions, stable narrative/page roles, content reuse boundaries, examples, and negative requirements.

Treat an explicit value authored by the user as `[decision]` regardless of carrier: direct chat, pasted text, or a user-written Markdown/TXT/DOCX/PDF brief all retain user authorship. Merely arriving in a file does not make a statement a fact. Treat a statement as `[fact]` only when it is independently traceable to an identified external authority such as an official manual/site, or when it is machine-observable file/package metadata such as dimensions, hashes, or existing PPTX structure. Any interpretation of vague prose remains `[suggested]` and must pass the Step 3 confirmation gate. Text and asset evidence never supplies Master/Layout topology by itself.

### 1E. No reference material

Skip the analysis. Step 2 will list every Required item as `[decision]`; nothing is fact-derivable from a non-existent source. Create Brand may emit an incomplete empty skeleton only under its explicit child-workflow rule; Create Layout/Create Deck still require the shared confirmation gate before authoring a `standard` workspace.

---

## Step 2: Fact-Based Brief Proposal

Compose a single message that surfaces every Required brief item to the user, **labelling each value's provenance**:

- **`[fact]`** — independently traceable external authority or machine-observable source metadata (e.g. theme color from `manifest.json`, image dimensions, or an identified official manual); a user-authored brief file is not a fact merely because it is a file
- **`[suggested]`** — AI-inferred from analysis or context (e.g. tone summary, applicable scenarios; visually estimated values from type C)
- **`[decision]`** — an explicit user-authored instruction or choice, including exact values supplied in conversation, pasted text, or a user-written brief file (e.g. `template_id`, replication mode, category, palette, or layout rule)

**Language adaptation rule**: write the Step 2 brief in the user's language. For technical enum values, show the localized label first and keep the English ID in parentheses only when needed for precision, for example `<localized deck label> (deck)`, `<localized layout label> (layout)`, or `<localized mirror label> (mirror)`. Do not assume users know what each English word means.

**Option visibility rule**: for every field with a finite option set, show both the recommended value and the other valid options. Do not present a single recommended value as if no alternatives exist. If an option is unavailable for the current bundle evidence, list it under `Unavailable` with the reason.

| Field | Must show |
|---|---|
| Output scope | Recommended `library` (default) plus `project`; explain that both use the same portable workspace routing and only the parent path / global registration differ |
| Target project | Required only for `project`; show the exact initialized project workspace path, not a project nickname |
| Selected child workflow | Echo the already-dispatched Create Brand, Create Layout, or Create Deck workflow; do not reopen kind selection inside the brief |
| Category | Create Layout/Create Deck only. Show the recommended localized value and alternatives; `brand` is valid for Create Deck but not Create Layout. For Layout, a scenario category records geometric fit only and never grants application ownership. |
| Application contract | Create Deck only. Show the recurring presentation family, intended audiences/outcomes, delivery/reading assumptions, stable narrative/page roles, and content reuse boundary. Values unsupported by evidence remain `[suggested]` until confirmed. |
| Theme mode | Create Layout/Create Deck only; recommended localized mode with English ID, plus available modes such as `light` / `dark` / `mixed`. Create Brand records identity colors instead and does not own a page theme mode. |
| Canvas format | Create Layout/Create Deck only; recommended canvas plus other supported formats from [`canvas-formats.md`](../references/canvas-formats.md) that fit the source aspect ratio or user intent. Always show the concrete pixel size and `viewBox`; do not treat two same-ratio formats such as `ppt169` (`1280x720`) and `banner` (`1920x1080`) as interchangeable. |
| Replication mode | Create Layout/Create Deck only; recommended localized mode with English ID, plus all modes available for the current input type. State that `standard` / `fidelity` design a new structure while `mirror` materializes validated source-package facts into a new workspace; list unavailable modes with reasons. For Create Layout, mark `mirror` unavailable when the source retains brand identity or reusable application rules. Create Brand has no replication mode. |
| Native structure policy | Create Layout/Create Deck only. For `standard` / `fidelity`, state that the designer will author a new Master/Layout/slot system without preserving or distilling source topology. Show the planned Master roster; if it contains more than one Master, explain the distinct reusable family owned by each and which Layouts belong to it. Reject one-Master-per-Layout organization and visually/semantically equivalent duplicate Masters. For `mirror`, summarize the exact source Master/Layout/placeholder facts that are present, supported, and will be mapped one-to-one into the new workspace. |
| Visual fidelity for fixed pages | Create Layout/Create Deck only; recommended localized choice with English ID, plus both `literal` / `adapted` options when applicable |
| Asset bundling | Recommended included assets, plus excluded candidate assets with a one-line reason when reference assets exist |

Items to surface:

| Item | Required | Provenance by evidence channel |
|------|----------|--------------------------|
| Output scope | Yes | `[decision]` — `library` (default, globally reusable and indexed) or `project` (same portable workspace routing under one initialized project) |
| Target project | Yes for `project`; N/A for `library` | `[decision]` — explicit path to the initialized target workspace; validate it during the Step 4 preflight |
| New template ID | Yes | `[decision]` — user chooses a filesystem-safe ASCII slug. In library scope it also becomes the matching index key |
| Template display name | Yes | `[decision]` (often the source deck title — `[suggested]` from `manifest.json.source.name` for type A) |
| Category | Create Layout/Create Deck only | `[decision]` — Create Deck: `brand` / `general` / `scenario` / `government` / `special`; Create Layout: `general` / `scenario` / `government` / `special` |
| Applicable scenarios | Yes | Create Brand: identity use cases. Create Layout: content shapes and delivery settings its geometry can support, without communication or narrative ownership. Create Deck: recurring presentation situations inside the application contract. `[suggested]` from analysis unless explicitly authored or externally sourced; user confirms. |
| Audience outcomes and stable narrative/page roles | Create Deck only | `[decision]` when supplied explicitly; otherwise `[suggested]` from recurring source patterns. Separate stable reusable rules from one-off source content. |
| Content reuse boundary | Create Deck only | `[decision]` or `[suggested]` classification of fixed, replaceable, optional, and example-only starting content; never infer that visible source text is reusable merely because it appears in a PPTX. |
| Identity tone or structural summary | Yes | Create Brand/Create Deck: identity tone. Create Layout: structural use case and density/rhythm summary only. |
| Theme mode | Create Layout/Create Deck only | A: `[fact]` from `manifest.json` background colors. B: `[fact]` from SVG `fill`. C: `[suggested]` from visual estimate. D: `[fact]` from an independently identified external authority, `[decision]` from user-authored text in any carrier, otherwise `[suggested]`. E: `[decision]`. |
| Canvas format and dimensions | Create Layout/Create Deck only | A/B: `[fact]` from slide size or SVG `width` / `height` / `viewBox`; show `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, and `source_viewbox`. C: `[suggested]` from image aspect ratio. D: `[fact]` from an independently identified external authority or `[decision]` from user-authored text in any carrier when specified. E: `[decision]`, default `ppt169` (`1280x720`, `0 0 1280 720`). |
| Replication mode | Create Layout/Create Deck only | `[decision]` — `standard` is always available and authors a compact roster from the confirmed brief; it may include a small number of explicitly required distinct variants without becoming source-driven. `fidelity` requires A/B page evidence and expands coverage from the useful source composition range; `mirror` requires A or B with a complete explicit structure contract. Create Layout mirror additionally requires the source contract itself to be brand-neutral and application-neutral; stripping identity or application rules is authorship, not mirror. C/D/E channels may supplement an eligible mixed bundle but do not establish mode eligibility. `standard` / `fidelity` author new SVG semantics. Mirror retains one materialized prototype per source slide in source order and adds definition-only prototypes for source Layouts unused by those slides. |
| Native structure facts | Create Layout/Create Deck with Type A or structured Type B | `[fact]` from `native_structure.json` / source SVG contract: master/layout counts, parentage, page assignments, placeholder identities, and multi-master status. Mirror preserves these validated facts in the new workspace; authored modes do not use them as output topology. |
| Mode-specific ownership | Create Layout/Create Deck only | `standard` / `fidelity`: `[decision]` newly authored Master/Layout ownership, including the reusable-family reason for every additional Master. `mirror`: `[fact]` source ownership mapped without synthesis. Every Master must own at least one emitted Layout and every Layout must have at least one emitted prototype; export never infers either contract. |
| Visual fidelity for fixed pages | Create Layout/Create Deck `standard` / `fidelity` when reference exists; **N/A for `mirror` and Create Brand** | `[decision]` — `literal` (closely reproduce reference geometry / decoration / sprite crops within a newly authored structure) or `adapted` (use reference tone/composition but allow design evolution). Different page types may take different settings. |
| Basic template norms | Yes when reference exists | Create Brand uses the identity fields and provenance rules from its child workflow. Create Layout/Create Deck use `[fact]` / `[suggested]` layout grammar, image system, density rhythm, page roster semantics, and asset policy from Step 1. |
| Reference source | Optional | already known if Step 1 ran |
| Theme color | Create Brand/Create Deck only | A: `[fact]` from theme XML. B: `[fact]` from dominant SVG `fill`. C: `[suggested]` from visual estimate (HEX is approximate). D: `[fact]` from an independently identified external authority, `[decision]` from user-authored text in any carrier, otherwise `[suggested]`. E: `[decision]`. Create Layout may use neutral preview paint but stores no identity color. |
| Fonts | Create Brand/Create Deck only | A: `[fact]` from `manifest.json`. B: `[fact]` from SVG `font-family`. C: font family is not derivable — use `[decision]` if the user supplies one. D: `[fact]` from an independently identified external authority or `[decision]` from user-authored text in any carrier. E: `[decision]` when a custom stack is wanted. Create Layout stores no typeface identity or final type scale; its structural text roles, alignment, wrapping, and capacity remain part of page grammar. |
| Design style | Optional | `[suggested]` from analysis |
| Assets list | Optional | A: `[fact]` from `assets/` listing; user picks which to bundle. B/C/D: retain each file's source and let the user confirm adoption. E: none. |
| Keywords | Yes | `[suggested]` from analysis (3–5 short tags); user confirms |

When the bundle includes Type A for Create Layout/Create Deck, also include in this message:

- the exact authoring-manifest documents required by the selected mode and verified during Step 1
- a one-line summary of the source Master/Layout structure
- the source structure facts, including master/layout counts, multi-master status, and reason codes; state whether they will be preserved in a new workspace (`mirror`) or ignored as output topology (`standard` / `fidelity`)

The user replies with corrections, additions, or "all good".

> **Persist the portable brief into `design_spec.md`**. In Step 4, declare a YAML frontmatter block with the child-specific ID key (`brand_id`, `deck_id`, or `layout_id`) and only fields owned by that child. Create Brand follows its identity schema. Create Layout/Create Deck persist the confirmed portable fields (`kind`, `category`, `summary`, `keywords`, `primary_color` for deck, `page_types` for layout, `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, `source_viewbox`, `replication_mode`, `native_structure_mode`, etc.). A Deck writes its confirmed application contract in Template Overview and content policies in Page Roster rather than duplicating that prose into frontmatter. Do not persist a generic `template_id` field: it is the parent workflow's cross-kind name, not a registrar schema key. Do not persist the execution-only `output_scope` or `target_project` fields. In library scope, `register_template.py` reads this frontmatter in Step 7 so the brief flows directly into the index without the AI re-deriving it from prose.

---

## Step 3: User Confirmation Gate

**MANDATORY interactive gate — this step BLOCKS Steps 4 onward.**

1. Echo back the finalized brief (post-corrections) in a single message
2. Emit the marker `[TEMPLATE_BRIEF_CONFIRMED]` on its own line

Skipping this gate — including silently inferring values from reference files, direct text, an opened IDE file, or prior conversation — is a route violation. Even if the user already supplied a PPTX, image, website, document, asset bundle, or complete written brief, you MUST still surface Step 2 with provenance labels and obtain explicit confirmation here. The reference bundle informs the brief; it does not substitute for it.

**Required outcome of Step 3** (all must be true before emitting `[TEMPLATE_BRIEF_CONFIRMED]`):

- [ ] User has been shown every Required item in Step 2 with provenance labels
- [ ] Every finite-option field has shown a recommended value, other available options, and unavailable options with reasons when applicable
- [ ] User-facing labels and option explanations match the user's language; English enum IDs appear only as precision aids
- [ ] User has replied with values or explicit acceptance of suggested defaults
- [ ] Output scope is confirmed; both scopes use the same workspace shape, while `project` includes an explicit initialized target-project path
- [ ] For Create Layout/Create Deck, the canvas format is fixed before SVG generation
- [ ] For Create Layout/Create Deck, replication mode is consistent with the bundle evidence (`fidelity` requires A/B page evidence; `mirror` requires A or structured B; C/D/E channels alone permit only `standard`); Create Layout mirror evidence is already brand-neutral and application-neutral
- [ ] Every supplied visual, textual, documentary, web, and asset channel has been analyzed or explicitly excluded; mixed-input conflicts are surfaced rather than silently resolved
- [ ] For Create Layout/Create Deck mirror, the source graph and supported geometry are complete; every source Layout absent from the source-slide roster is planned as a definition-only prototype, and any genuinely missing/unsupported facts were reported; Create Layout mirror contains no retained brand identity or reusable application policy
- [ ] Child-specific norms from prior content have been surfaced and accepted, or explicitly marked N/A when no reference exists: identity/provenance for Create Brand; layout/image/density/asset behavior for Create Layout/Create Deck
- [ ] For Create Layout/Create Deck, mode-specific ownership is explicit: `standard` / `fidelity` author a new structure without source-topology distillation; `mirror` maps validated source ownership one-to-one into a new workspace
- [ ] For Create Deck, the recurring presentation family, intended audiences/outcomes, stable narrative/page roles, and content reuse boundary are confirmed; for Create Layout, no application contract or brand identity has leaked into the structure brief
- [ ] For Create Brand, all required identity fields from its child workflow are confirmed and canvas/replication/native-structure fields remain N/A
- [ ] For `library`, metadata is complete enough to register into the relevant index; for `project`, the same portable template metadata is complete and no global registration is planned
- [ ] Marker `[TEMPLATE_BRIEF_CONFIRMED]` emitted on its own line after the echoed brief

Step 4 MUST NOT run until `[TEMPLATE_BRIEF_CONFIRMED]` has been emitted in the current conversation.

---

## Step 4: Preflight Output + Invoke the Selected Child

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

The preflight is atomic at the Create Template parent level: discover and settle every output filename first, check all destinations together, then begin generation. Do not partially write a workspace and discover a later collision.

**Create Brand branch**: continue in [`create-brand.md`](./create-template/create-brand.md) §3 with the confirmed identity brief and resolved `<template_workspace>`. Then return to the Create Brand branch in Step 5. Do not invoke Template_Designer, create SVGs, or apply the Create Layout/Create Deck-only material below.

**Create Layout/Create Deck branch**: continue in the selected child workflow, switch to the Template_Designer role, and generate per role definition. The role input is the finalized brief from Step 3 plus the analysis bundle from Step 1, including the accepted basic template norms.

When the bundle includes Type A, pass the following internal package to the role:

- finalized brief from Step 3
- `manifest.json`
- `native_structure.json` and `source_template.pptx`
- `conversion-report.json` when source-recovery diagnostics exist
- exported `assets/`
- `*_vector_asset_inventory.json`, when the vector readability pass extracted assets, as an exact-id query surface only; do not load it or `icons/imported/*.svg` wholesale
- `authoring-svg/authoring_summary.json` and editable layered IR documents; keep `authoring_manifest.json` bundled for compiler use but do not load it into the role context; optional `authoring-svg-flat/` is a visual cross-check only and never a template materialization input
- for `mirror` only, matching immutable `svg/` payload backing plus `svg/inheritance.json`; immutable `svg-flat/` remains an optional visual cross-check
- optional screenshots, if available

When the bundle includes Type B, pass `authoring_summary.json`, the cleaned SVG file list from the analysis workspace, `*_vector_asset_inventory.json` as an exact-id query surface if extraction ran, any companion `design_spec.md` / `spec_lock.md`, and the analysis notes. Do not bulk-read the inventory or extracted vectors; open individual `icons/imported/*.svg` files only when needed.
When the bundle includes Type C, pass the image file list and the visual analysis notes.
When the bundle includes Type D, pass the direct text, converted document/website outputs, traceable source list, explicit asset inventory, and analysis notes.
For Type E, pass only the finalized brief.
For a mixed reference bundle, pass the union of the applicable packages while keeping each fact's source and every unresolved conflict explicit.

The role interprets the package according to replication mode:

| Mode | Final SVG authority | Structure behavior |
|---|---|---|
| `standard` / `fidelity` | Newly authored SVGs based on the confirmed brief and visual references | Design an intentional new Master/Layout/slot system. Source topology is neither preserved nor distilled into the output. |
| `mirror` | Editable `authoring-svg/` IR plus native-structure facts and lossless payload backing | Materialize source pages, Master/Layout identities and parentage, placeholder identity/bounds, ownership, and supported native-object metadata one-to-one in the new workspace. Materialization resolves unchanged source refs; it does not copy the lossless tree as the editable source. |

For Type A `mirror`, materialize the reviewed layered IR into an empty template
workspace with the deterministic compiler:

```bash
python3 skills/ppt-master/scripts/mirror_template_materialize.py \
  "<import_workspace>" "<template_workspace>"
```

The destination `templates/` directory must be absent or empty. Before
publication, the command verifies the layered manifest and source-ref closure,
lossless SVG and source-PPTX hashes, complete native/inheritance graph, and
extracted-vector inventory. It then stages and publishes the entire roster in
one operation. It emits source-ordered page SVGs, unused-Layout definition
SVGs, `icons/imported/`, referenced `images/` / `templates/assets/`, and one
deduplicated `templates/native_payloads.json.gz` store when supported native
payload or repeated restoration metadata exists. It also writes
`templates/template_execution_manifest.json`, a compact model-readable prototype
roster and grouped source-import warning summary. Each prototype points to one
`templates/template_execution/*.text-slots.json` sidecar containing its exact
mirror text selectors, segments, attributes, topology hashes, bounds, and font
stacks. Template SVGs and imported
vectors keep content-hash payload references plus short
`data-pptx-native-ref` attribute-record ids. Structural Master/Layout,
placeholder, layer, and editable-object fields remain inline. The command does
not create `design_spec.md`. Template_Designer writes that file from the
confirmed brief and the materialized roster before Step 5. A rerun targets a
new empty workspace rather than overwriting a partially reviewed template.

**Hard rule — mode-specific authorship**: `standard` and `fidelity` author new
project-canonical SVG documents. When one registered PowerPoint preset exactly
expresses one complete object, they use the compact canonical
`<g>` emitted by `preset_shape_svg.py`, following
[`native-shape-authoring.md`](../references/native-shape-authoring.md); its
paint comes from the confirmed brief and template `design_spec.md`. After
inserting the complete helper group, add only the registered structural
attributes required by its Master/Layout or object-slot role; geometry and
paint changes require a new helper render. `mirror` preserves the expanded
lossless source contract in a new workspace and may only normalize transport details required by
the current compiler. Mirror never performs commonality
extraction, semantic synthesis, merge/split, promotion/demotion, renaming, or
re-parenting.

**Hard rule — multi-Master package boundary**: More than one Master is valid only when `mirror` preserves an existing source graph in the new workspace or an authored template intentionally defines distinct reusable design families. `standard` / `fidelity` must not create one Master per Layout or duplicate equivalent Masters merely for organization. Every declared Master must own at least one emitted Layout, and every declared Layout must be selected by at least one prototype SVG so the complete graph can be compiled and verified.

| Package concern | Requirement |
|---|---|
| Theme ownership | Every registered Slide Master receives its own Theme part. Two Masters must never resolve to the same `ppt/theme/themeN.xml`. Theme cloning is exporter-owned; do not author or bundle Theme XML in the template workspace. |
| Creation identity | Any generated `p14:creationId` on Slides, Layouts, or Masters is a valid unsigned 32-bit value and unique across those parts. Cloned structural parts always receive fresh values. |
| Numeric registration | Master and Layout registration IDs are valid and unique in their owning lists; Layout numeric IDs are unique across the complete package, including across different Masters. |
| Relationship graph | The presentation registers the exact Master and Slide rosters; each Master registers exactly its owned Layouts; each Layout targets exactly one declared Master; each Slide targets exactly its declared Layout. |

SVG authors own the semantic roster, parentage, picker names, direct atoms, and slots. The exporter owns OOXML part cloning, Theme isolation, relationship registration, and package identity. Do not encode package repair workarounds in individual template SVGs.

Do not package `native_structure.json` or `source_template.pptx` as template inputs. In `standard` / `fidelity`, author Master/Layout direct semantic atoms and bounded slot groups deliberately from the intended reusable behavior. A validated compact canonical authored-preset `<g>` compiles to one native shape and therefore counts as one semantic atom; it may own a Master/Layout fixed layer or serve as the one direct carrier of an `object` slot. Ordinary groups are not structural atoms or single-object carriers. In `mirror`, edit the layered authoring IR and use inheritance/native facts to preserve source ownership; the lossless trees remain payload backing. Recursively expand fixed Master/Layout group wrappers only because the structured contract requires semantic atoms; preserve transforms, styles, paint order, and appearance, and never flatten or regroup by semantic judgment.

`design_spec.md §V` records the newly authored roster for `standard` / `fidelity`. For `mirror`, add the `Source Preservation Map` required by [template-designer.md](../references/template-designer.md), with one row per source slide and its preserved Master/Layout assignment. Do not add a synthesis-decision table.

**Native-shape metadata boundary**: The authoring IR removes opaque payload
from model context while retaining stable source refs. `standard` / `fidelity`
use helper-generated compact canonical preset groups and project SVG/assets
rather than copied source payload. `mirror` materialization rehydrates only
native metadata already supported by the converter when a referenced
Slide-local/slot object's initial authoring hash still matches. Fixed layers are normalized to semantic atoms;
unsupported or edited objects keep the current SVG fallback and are reported
rather than silently replaced by stale metadata. Do not reproduce the preset
syntax here; its single authority is
[`shared-standards-core.md`](../references/shared-standards-core.md), with selection and
usage guidance in the native-shape reference.

Downstream, a mirror-created workspace supports three separately confirmed reuse scopes. `mirror` and `layout` use `pptx_structure.mode: structured`; `page_layouts` selects one complete authoring prototype per page, `pptx_masters` / `pptx_layouts` declare unique reusable definitions, and `page_pptx_layouts` assigns generated pages. Strict preserves the selected prototype contract. Adaptive keeps its Master and may explicitly create and assign a new Layout key/name while authoring the page that needs it. `mirror` additionally preserves literal visuals/text topology; `layout` allows project-controlled reflow/re-skinning. `style` uses `mode: flat` and takes only the workspace's design language. A retained Layout may remain unassigned while still registering through its definition SVG. No scope forces a future generated deck to keep the source page count or order.

**Apply the visual-fidelity decision from Step 3 to authored modes**: in `standard` / `fidelity`, pages marked `literal` reproduce the selected reference geometry and decoration while still using a newly designed structure; pages marked `adapted` may evolve the composition. Mirror preserves every supported source visual represented by the validated IR and does not use this authored-page distinction.

**Sprite-sheet preservation (do NOT simplify away)**: PPTX-exported assets are often sprite sheets — a single tall/large image referenced from multiple slides, each cropping a different region via nested `<svg ... viewBox="...">` wrappers around `<image width="1" height="1">`. This nesting is **load-bearing geometry**, not redundant structure. When rebuilding, preserve the exact `viewBox` crop and the outer `<svg>` placement for every image; do not flatten to a single `<image>` with direct `x/y/width/height`. Verify by sampling: if any asset's pixel dimensions don't match the on-page display aspect, it is a sprite and the wrapper must stay.

**Mirror-mode materialization contract** (type A or B): when `Replication mode: mirror`, the Template_Designer role:

1. **Materializes one output SVG per source page** in `<template_workspace>/templates/`. Edit and normalize the matching `authoring-svg/` IR document, then run `mirror_template_materialize.py`; the compiler consumes the tool-only authoring manifest together with native structure facts and immutable payload backing. Do not hand-copy or independently rebuild its graph. Preserve the source Master/Layout keys and picker names, Layout parentage, slide assignment, placeholder type/index/bounds, inherited-shape visibility, ownership, paint order, and supported native metadata that are present and validated. Mechanical namespace, root-declaration, asset-path, and fixed-layer group normalization is allowed only when source ownership and appearance remain unchanged.
   - Type A model-facing source: `<import_workspace>/authoring-svg/authoring_summary.json` plus the editable SVGs; `<import_workspace>/svg/`, `svg/inheritance.json`, and `native_structure.json` provide payload and structural backing. The compiler alone reads `<import_workspace>/authoring-svg/authoring_manifest.json`. Optional `<import_workspace>/svg-flat/` is verification-only.
   - Type B model-facing source: `<svg_analysis_workspace>/authoring-svg/authoring_summary.json` plus its editable SVGs; the complete explicit source SVG contract is immutable backing
   - For every source Layout unused by all source slides, additionally materialize one definition-only SVG named `layout_<layout_key>.svg` from its layered authoring IR document and payload backing. It carries the exact root identity, fixed atoms, and placeholder contract but is not a generated page assignment. Use source placeholder prompts/carriers; do not invent business content. This definition SVG lets downstream export register the Layout and any otherwise-unused parent Master without retaining an internal carrier slide.
2. **Renames each file** using the source-order-first convention `<NNN>_<page_type>.svg`, where `<NNN>` is the source-order index zero-padded to 3 digits and `<page_type>` is typically `cover` / `toc` / `chapter` / `content` / `ending` (fall back to `content` when the type cannot be confidently classified). Examples: `001_cover.svg`, `002_toc.svg`, `003_content.svg`, ..., `050_ending.svg`.
   - Type A: derive `<page_type>` from `manifest.json.pageTypeCandidates`
   - Type B: derive `<page_type>` from the source filename when it follows the PPT Master convention (`01_cover.svg` → `cover`, `03a_content_two_col.svg` → `content`); otherwise infer from page content or fall back to `content`
3. **Routes bundled assets through the common workspace contract** and rewrites every `<image href="...">` consistently. Keep stable source asset identity in mirror; do not rename, merge, or replace assets by semantic judgment.
   - Type A: assets come from `<import_workspace>/assets/`
   - Type B: resolve relative paths in source `<image href="...">` against the source SVG location and copy each unique asset; if the source already follows PPT Master conventions (assets co-located with SVGs in the same directory), copy the whole asset set and then rewrite paths
   - Both scopes: write bitmaps to `<template_workspace>/images/`, point SVG references at `../images/<name>`, and keep non-bitmap template-source assets under `<template_workspace>/templates/`.
4. **Copies imported vector assets once** to `<template_workspace>/icons/imported/` and rewrites their placeholders to `<use data-icon="imported/<name>"/>`. Never place a second copy under `templates/icons/`. Other explicitly adopted icon-library references keep their existing library namespace. Do not inline these assets manually in the template working SVGs; template validation, preview, and final export all resolve icons from the workspace-root `icons/` directory.
5. Writes `design_spec.md` per [template-designer.md](../references/template-designer.md) §1. The §V Page Roster remains the content-fit index; explicit SVG metadata is the native Master/Layout contract. `replication_mode: mirror` governs template creation and merely enables the separately confirmed downstream `template_reuse_scope: mirror`; it never forces a 1:1 slide sequence.

Mirror mode does not simplify the visual target or synthesize layer ownership. The sprite-sheet preservation rule applies because crop wrappers carry visible geometry; preserve those wrappers and their source scope faithfully.

**Expected outputs from this step** (full spec → [template-designer.md](../references/template-designer.md)):

1. `design_spec.md` — **package-specific rules only**. A deck writes an application-bearing Template Overview, Color Scheme, Signature Design Elements, and Page Roster with content policies; Typography / Assets / Placeholder Overrides are conditional. A layout writes only structure-owned Signature Design Elements and Page Roster; its frontmatter `summary` carries concise selection context, and it omits the deck-only Template Overview plus every identity section. The Page Roster must match the actual SVG files on disk. Declare portable brief frontmatter; `register_template.py` consumes it only in library scope. **Do not** restate generic SVG constraints, layout pattern libraries, font-size ratio bands, the canonical placeholder table, or content methodology — those are sourced from `shared-standards-core.md` / `pptx-structure-interface.md` / `strategist.md` and are already in the downstream reader's context. Full scope rule and skeleton: [template-designer.md §1](../references/template-designer.md#1-must-generate-design_specmd).
2. Page roster — see [Page Roster](../references/template-designer.md#page-roster) for `standard` / `fidelity` / `mirror` mode rosters, variant naming, and TOC handling
3. Placeholder vocabulary — pages should adopt the conventional names (`{{TITLE}}`, `{{CONTENT_AREA}}`, ...) when they fit. Full reference: [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). When a template style legitimately needs different vocabulary (consulting → `{{KEY_MESSAGE}}`, branded cover → `{{BRAND_LOGO}}`), declare a `placeholders:` block in `design_spec.md` frontmatter so the registrar and quality checker treat it as the template's authoritative contract. **Avoid** one-off indexed families such as `{{CHAPTER_01_TITLE}}` — use the indexed TOC pattern instead.
   - `{{...}}` placeholders are the authoring vocabulary used to generate final slide content. Each emitted SVG also carries the native structure contract: root Master/Layout key/name, direct atomic Master/Layout elements, and direct slot `<g>` elements with explicit design-zone bounds plus exactly one compatible carrier. A validated compact canonical authored-preset `<g>` counts as one semantic atom or one `object` carrier; ordinary groups do not. Composite regions use only the explicit `object` + `proxy` downgrade. Minimal structural `data-pptx-role` hints are added only when specialized metadata cannot express required behavior. Both strict and adaptive downstream set `mode: structured` and require complete `page_layouts`, `page_pptx_layouts`, `pptx_masters`, and `pptx_layouts` from planning onward.
4. Template assets (optional) — both scopes apply the same `templates/` / `images/` / root `icons/imported/` routing defined above

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
| Review prompt legibility | For `standard` / `fidelity`, the preview exporter substitutes concise sample text only in ephemeral review SVGs so long canonical markers such as `{{CHAPTER_NUM}}` or `{{PAGE_NUM}}` do not wrap. The source SVG markers, carrier font sizes, slot metadata, and Layout frames remain unchanged. |
| Mirror boundary | `mirror` preserves source Slide carrier geometry exactly in the tool-side native record referenced by its text carrier and keeps `data-pptx-placeholder-bounds` as the reusable Layout default. Do not normalize one to the other when the source intentionally overrides that frame. |

---

## Step 5: Validate Template Assets

**Create Brand branch**: run the child workflow's §4 checklist and the shared project-safe validator below in both scopes. It detects `kind: brand`, validates the identity-only frontmatter/sections/colors/provenance/asset references, and does not require an SVG roster or touch a global index. Any failure blocks completion.

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_workspace>/templates" --template-mode
```

In `library` scope, additionally run the registrar dry-run so `brand_id` is checked against the library directory/index key:

```bash
python3 skills/ppt-master/scripts/register_template.py <brand_id> --kind brand --dry-run
```

After Create Brand validation passes, skip the Create Layout/Create Deck-only remainder of this step and all of Step 6; continue at Step 7.

**Create Layout/Create Deck branch**: set `<template_source>` to `<template_workspace>/templates/` in both scopes.

```bash
ls -la "<template_workspace>/templates"
ls -la "<template_workspace>/images" "<template_workspace>/icons"
```

Compact safe page-space metadata and transform coordinates, then run SVG
validation on the template directory. Keep canonical authored-preset and native
record frames unchanged:

```bash
python3 skills/ppt-master/scripts/compact_svg_coordinates.py "<template_workspace>/templates" --inplace --keep-native-frames
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
- warn when distinct Layout keys have identical static framing/slot contracts. Resolve this for `standard` / `fidelity`; mirror may retain the distinct source identities and records that fact in its Source Preservation Map

This checker validates the authoring contract, not the compiled OOXML package. Theme ownership, package IDs, and registered part relationships are verified by `template_preview_pptx.py` in Step 6.

**Checklist**:

- [ ] `design_spec.md` follows the kind-specific package skeleton: deck = application-bearing Overview / Color / Signature / Page Roster plus conditional sections; layout = structure-owned Signature / Page Roster with no Overview, application contract, or identity sections. Generic constraints (SVG rules, pattern libraries, ratio bands, canonical placeholder table) are NOT restated. The source-derived basic norms are present as template-specific layout / image / density / asset rules, not generic advice. Deck Overview identifies recurring situations, audiences/outcomes, delivery assumptions, stable narrative/page roles, and content reuse boundaries; §V Page Roster lists every emitted page and, for Deck, each prototype's content policy
- [ ] Every page declared in `design_spec.md §V Page Roster` exists as an SVG file in the template directory (and vice versa — no orphan files)
- [ ] Variant filenames follow the letter-suffix convention (e.g. `03a_content_two_col.svg`); variants typically reuse the parent type's placeholder set unless the spec frontmatter declares otherwise
- [ ] If TOC exists, placeholder pattern uses the canonical indexed form
- [ ] `design_spec.md` frontmatter declares `canvas_format`, `canvas_width`, `canvas_height`, and `canvas_viewbox`; PPTX/SVG-backed templates also declare `source_canvas_width`, `source_canvas_height`, and `source_viewbox`
- [ ] SVG `viewBox` matches the declared canvas dimensions, not just the aspect ratio (for `ppt169`: `0 0 1280 720`; for `banner`: `0 0 1920 1080`); `width` / `height`, if written, equal it
- [ ] Model-facing placeholder bounds and transform page coordinates use at most two decimals; normalized crop/viewBox ratios, path geometry, transform scale/rotation coefficients, authored-preset frames, and tool-side native frames retain their required precision
- [ ] Placeholder names follow the canonical convention where applicable; templates with intentionally different vocabularies (e.g. `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`) should declare a `placeholders:` frontmatter block to silence advisory warnings
- [ ] Asset files referenced by SVGs exist at their resolved paths. In both scopes, bitmap references resolve through `../images/`; no bitmap remains accidentally stranded in `templates/`
- [ ] `design_spec.md` frontmatter declares `native_structure_mode: structured`; no `native_structure.json` or `source_template.pptx` is packaged
- [ ] Every SVG root declares Master/Layout key and picker names; Master/Layout visuals are direct semantic atoms and obey the explicit paint-order contract. Ordinary `<g>` elements remain forbidden there; a validated helper-generated compact canonical preset `<g>` is the sole group exception because it compiles to one native shape. Structural `data-pptx-role` is used only when specialized metadata cannot express required package/page-number/animation behavior
- [ ] Every slot is a direct `<g id>` with explicit design-zone bounds and exactly one compatible direct carrier, or an explicit composite `object` proxy. A validated compact canonical preset `<g>` may be the one carrier of an `object` slot; an ordinary multi-object group may not. Zero-slot Layouts remain valid
- [ ] For `standard` / `fidelity`, every placeholder bound is the complete editable box rather than the current marker text's tight bounds; general body/object carriers begin at the upper-left and only intentional short focal roles remain centered
- [ ] In review output, authored placeholder prompts remain readable; `template_preview_pptx.py` uses preview-only sample text and leaves every canonical source marker and carrier style unchanged
- [ ] `standard` / `fidelity` output SVGs and their Master/Layout/slot contracts were newly authored without preserving or distilling source topology
- [ ] Every additional authored Master represents a distinct reusable design family, not one Layout or an equivalent duplicate; every declared Master owns at least one emitted Layout and every declared Layout has at least one emitted prototype
- [ ] Mirror output preserves source slide order, Master/Layout identity and parentage, placeholder facts, and ownership; fixed-layer group expansion is mechanical and pixel-equivalent, and the Source Preservation Map lists every source slide
- [ ] Mirror materialization wrote the compact `templates/template_execution_manifest.json`; each prototype is listed once and links one `template_execution/*.text-slots.json` sidecar, every sidecar slot records selector/current segments/tspan attributes/topology hash/bounds/font stack, and source-import diagnostics are summarized separately from downstream generation issues
- [ ] Mirror roots preserve source inherited-shape visibility with canonical lowercase `data-pptx-show-master-shapes` and `data-pptx-show-inherited-shapes`; same-key Layouts agree on the former, while each Slide retains its own latter value
- [ ] Mirror preflight covered the complete source graph; each unused Layout has one `layout_<layout_key>.svg` definition prototype and each otherwise-unused Master is retained through at least one such Layout
- [ ] For `standard` / `fidelity`, no duplicate-Layout-contract warning remains; mirror may keep equivalent source Layout identities when the preservation map explains them
- [ ] All template-creation edits used the authoring IR; Type A mirror used `mirror_template_materialize.py`, validated its manifest/hash/graph/source-ref closure before atomic publication, reused only converter-supported payload for hash-matching Slide-local/slot refs, deduplicated supported opaque payload and repeated native restoration attributes into `templates/native_payloads.json.gz`, stripped IR-only source-ref metadata, and kept fixed Master/Layout visuals as direct atoms
- [ ] If any SVG references an extracted vector, it uses `data-icon="imported/<name>"` and the sole SVG asset exists at `<template_workspace>/icons/imported/<name>.svg`; `templates/icons/` does not exist and no separate illustration embedding script was added
- [ ] For `fidelity` mode: every sprite-sheet asset retains its nested `<svg viewBox=...>` crop wrapper; no image whose file aspect differs from its on-page aspect was flattened to a bare `<image>`
- [ ] For `mirror` mode: source-page SVG count equals source page count, while additional files are exactly the required `layout_<layout_key>.svg` definitions for unused source Layouts; source-page filenames follow the `<NNN>_<page_type>.svg` convention; **no new `{{...}}` authoring placeholders were inserted into materialized source-page SVGs**; §V Page Roster lists every emitted file and marks definition-only prototypes explicitly

This step is a **hard gate**. Do not generate a review PPTX, register, or hand the workspace to the main pipeline until validation passes. A one-Master template may skip Step 6 when no review was requested; a multi-Master template must continue to Step 6 and may not register or complete before that package gate passes.

---

## Step 6: Template Review PPTX and Multi-Master Package Gate

**Trigger — Create Layout/Create Deck only**: Run when the user requests a PowerPoint review file **or** when the validated SVG roster declares more than one unique Master key. A multi-Master template requires this step even when no review artifact was requested. A one-Master template may skip directly to Step 7 when the user did not request a review file. Create Brand always skips this step because it owns no SVG roster or native structure.

Export the complete SVG roster, one prototype per slide, from the workspace root:

```bash
python3 skills/ppt-master/scripts/template_preview_pptx.py "<template_workspace>"
```

The default output is `<template_workspace>/exports/<template_id>_template_preview.pptx`; the command creates `exports/` on demand. The script consumes `templates/*.svg` directly, compiles the declared structured Master/Layout contract, and reopens the result. For `standard` / `fidelity`, it uses ephemeral SVG copies with concise preview-only placeholder samples so long `{{...}}` markers stay readable; canonical source SVGs and placeholder semantics are not modified. It does not require a project `spec_lock.md`, does not create a persistent intermediate project, and does not infer or distill structure.

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
# For brand
python3 skills/ppt-master/scripts/register_template.py <template_id> --kind brand

# For deck
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

The index file is a **discovery index** — it lets the AI answer "what templates are available?" by listing names and workspace-root paths. It is **not** consulted to trigger [`generate-pptx`](./generate-pptx.md) Step 3. Step 3 triggers on an explicit workspace-root path supplied by the user, regardless of whether that path is registered. An unregistered workspace still works when the user gives its path; it just will not appear in discovery listings.

> **Recommended for new templates**: declare a YAML frontmatter block at the top of `design_spec.md`. The registrar prefers it over prose extraction:
>
> ```yaml
> # deck example
> ---
> deck_id: my_deck
> kind: deck
> category: brand
> summary: ...
> keywords: [brand, reporting, structured]
> canvas_format: ppt169
> canvas_width: 1280
> canvas_height: 720
> canvas_viewbox: "0 0 1280 720"
> source_canvas_width: 1280
> source_canvas_height: 720
> source_viewbox: "0 0 1280 720"
> replication_mode: standard
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
> category: general
> summary: ...
> keywords: [general, layout, structured]
> canvas_format: ppt169
> canvas_width: 1280
> canvas_height: 720
> canvas_viewbox: "0 0 1280 720"
> source_canvas_width: 1280
> source_canvas_height: 720
> source_viewbox: "0 0 1280 720"
> replication_mode: standard
> native_structure_mode: structured
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
**Kind**: brand | layout | deck
**Output Scope**: library | project
**Workspace Path**: `<template_workspace>/`
**Template Source**: `<template_workspace>/templates/`
**Bitmap Path**: `<template_workspace>/images/`  ← omit when no bitmap was written or adopted
**Imported Vector Path**: `<template_workspace>/icons/imported/`  ← omit when no imported vector was written or adopted
**Review PPTX**: `<template_workspace>/exports/<template_id>_template_preview.pptx`  ← Create Layout/Create Deck only; omit for Create Brand and when an optional one-Master review was not requested
**Primary Color**: <hex>  ← Create Brand/Create Deck only; omit for Create Layout
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

For Create Brand, replace the SVG/review rows with `templates/design_spec.md` plus only the real `images/*` / `icons/*` assets. Its completion card must explicitly state `SVG roster: N/A` and `Native structure: N/A`.

The next Generate PPTX Step 3 input is the exact `<template_workspace>/` root in either scope. Step 3 resolves its `templates/design_spec.md`, ignores `exports/`, and copies or consumes `templates/` plus any existing `images/` and `icons/` as one unit. It then authors new `svg_output/` pages under the template contract and exports a new PPTX. Neither the reference PPTX/SVG nor the template prototypes are upgraded in place. A legacy-flat package root remains readable only when its semantic SVG contract is current; otherwise create a new workspace through this route.

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

1. **SVG technical constraints**: Create Layout/Create Deck load [shared-standards-core.md](../references/shared-standards-core.md) plus [pptx-structure-interface.md](../references/pptx-structure-interface.md), and load [svg-effects.md](../references/svg-effects.md) only when the authored design uses those effects. Create Brand authors no SVG and loads none of these SVG modules. Do not restate the contracts in the template's `design_spec.md`.
2. **Color consistency**: Create Deck SVG files must use the same color scheme as `design_spec.md §II Color Scheme`; Create Layout owns no identity colors, and Create Brand owns no SVG files
3. **Native-object mapping**: Treat Theme/Master/Layout/Placeholder as compiled PowerPoint objects, not template kinds. Layout owns topology and placement, Brand owns identity values/assets, and Deck adds the reusable application contract.
4. **Placeholder convention**: `{{}}` format only; default names listed in [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). Override per template via `placeholders:` frontmatter when needed.
5. **Discovery requirement**: A library template is discoverable only after `register_template.py` has been run against it (Step 7). A project-scoped workspace intentionally stays out of global discovery and is consumed by its explicit workspace-root path.
6. **Review output**: Generate `exports/<template_id>_template_preview.pptx` on request and always for a multi-Master template. It is derived local evidence, never a source input during template application, and library exports stay Git-ignored.

> **Full role specification**: [template-designer.md](../references/template-designer.md)
