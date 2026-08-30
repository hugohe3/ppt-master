---
description: Create Template entry workflow and shared contract for the Create Brand, Create Style, Create Layout, and Create Deck sub-workflows.
---

# Create Template Workflow

> **Fixed entry name**: template creation always enters **Create Template**, which selects exactly one child — [`create-brand.md`](./create-template/create-brand.md), [`create-style.md`](./create-template/create-style.md), [`create-layout.md`](./create-template/create-layout.md), or [`create-deck.md`](./create-template/create-deck.md) — and owns their shared execution contract. Create Layout/Create Deck invoke the [Template_Designer](../references/template-designer.md) role. Tool behavior (import workspace, template-mode checker, review deck, registrar) is documented in [`template-tools.md`](../scripts/docs/template-tools.md).

Create one reusable template workspace under the global library (default) or `projects/` from one or more reference channels or a direct brief, then dispatch to one child.

| Scope | `<template_workspace>` | `<design_spec_path>` | Registration |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind_dir>/<template_id>/` | `templates/design_spec.md` | `register_template.py` against the kind index |
| `project` | `<target_project>/` (initialized by `project_manager.py init`) | `templates/design_spec.<kind>.<id>.md` (kind/id equal frontmatter `kind` / `<kind>_id`) | None; the root stays an ordinary explicit workspace whose `templates/` may accumulate one Brand, Style, Layout, and Deck over separate runs — Layout owns the active roster when both coexist, Deck keeps identity and application context |

**Hard rule — one workspace routing contract**: scope changes the parent path, spec filename, and registration — never the spec schema or asset routes. Both scopes use required `templates/`, optional `images/` (every bitmap; SVG href `../images/<name>`) and `icons/imported/` (one canonical copy of each imported decoration vector), and conditional `exports/` (review evidence, required for multi-Master templates, Git-ignored in the library, never consumed by application). Never create an optional directory or placeholder solely to keep an empty path; leave pre-existing empty project scaffolding untouched and omit it from completion. Create Style contributes only its spec. Do not maintain a library-only flat package or project-only thin-bundle branch.

**Boundaries**: Create Template never fills content into a PPTX, adds Master/Layout structure to an existing PPTX/SVG, or outputs the user's final deck — it authors a separate workspace whose root returns to [`generate-pptx`](./generate-pptx.md) Step 3 as an exact candidate (a project-scoped workspace selected for its own project is consumed in place). Page images that should become final editable slides use [`image-to-pptx.md`](./profiles/image-to-pptx.md), not a template.

## Child Workflow Dispatch

| Child | Select when | Library output | Exclusive responsibility |
|---|---|---|---|
| Create Brand | Reuse identity only: colors, typography, logo, voice, icon style | `templates/brands/<brand_id>/` | Identity-only spec; no SVG roster |
| Create Style | Reuse a communication method and visual direction without identity truth or prototypes | `templates/styles/<style_id>/` | Method, page-role vocabulary, evidence expression, visual defaults, image/icon direction, advisory review focus; no roster |
| Create Layout | Reuse a brand-neutral structural skeleton without a recurring application | `templates/layouts/<layout_id>/` | Canvas, page grammar, semantic text roles, Master/Layout/slot contract, SVG roster; no identity or application contract |
| Create Deck | Reuse a branded structural system or a recurring application | `templates/decks/<deck_id>/` | Descriptive application context, integrated identity/structure, SVG roster |

A complete source PPTX does not determine the kind — classify only the stable rules worth reusing. Ask one discriminator only when the requested artifact is genuinely ambiguous; once selected, never reopen kind selection inside the child's gate, execute two children for one workspace, or blend schemas. Shared kind and workspace model: [`templates/README.md`](../templates/README.md); application: [`apply-template-workspace`](./stages/apply-template-workspace.md).

## Process Overview

```
Reference Bundle Intake & Analysis → Fact-Based Brief Proposal → User Confirmation Gate → Preflight + Invoke Selected Child → Validate Child Output → [Review PPTX: optional for one Master, required for multi-Master] → [Register Library Index] → Output
```

**No final template directory, template SVG, or Design Spec may be written until `[TEMPLATE_BRIEF_CONFIRMED]` is emitted in Step 3.** Reference-analysis intermediates (import workspaces under `/tmp/`) are not subject to this gate.

---

## Step 1: Reference Bundle Intake & Analysis

Run every applicable branch for the bundle (one source, several files, mixed types, direct text, or nothing); produce analysis only. Create Brand/Create Style follow their child analysis rules and never run page-topology analysis merely because the reference is a PPTX/PDF.

| Type | Supplied | Tool / read path | Strategies the evidence supports |
|---|---|---|---|
| **A** `.pptx` | A `.pptx` path | `pptx_template_import.py` → import workspace ([`template-tools.md`](../scripts/docs/template-tools.md)) | `standard` / `fidelity` / `mirror` |
| **B** SVG assets | `projects/<x>/svg_output/`, a current workspace root, or a loose `.svg` folder | Normalize the source, create an authoring IR bundle with `svg_authoring_view.py`, run the readability pass on that IR only; read companion `design_spec.md` / `spec_lock.md` | `standard` / `fidelity`; `mirror` only with a complete explicit Master/Layout/placeholder/native-object contract |
| **C** Images / visuals | PNG/JPG/WebP, screenshots, moodboards, PDF pages | `ls` + `Read` each visual (multimodal) | `standard` only by itself |
| **D** Text / document / website / assets | Direct text, Markdown/TXT, DOCX/PDF/HTML/URL, brand manuals, logo/icon/font assets | Direct text as-is; convert documents/URLs with `source_to_md.py` into a temporary analysis workspace; inventory explicit assets | `standard` only by itself |
| **E** Nothing | A request with no source and no substantive brief | Skip analysis; collect every Required value in Steps 2–3 | `standard` only |

**Bundle rules**: `standard` may combine every confirmed channel — never force one source type. The AI derives the internal strategy from natural-language intent plus evidence (`fidelity` needs A/B page evidence; `mirror` needs A or a complete current B contract; C/D/E supplement but never create native topology) and never asks the user to choose these labels. Keep facts, explicit user decisions, and AI suggestions distinct; surface contradictions in Step 2. Supplemental inputs may explain a confirmed `mirror` source but cannot alter its graph or visuals.

**Internal strategies**: `standard` / `fidelity` review all source structure, then author a compact or broader source-aligned roster with one Slide prototype per retained Layout; `mirror` authors compact parsed SVG for every source Slide, preserving the reachable graph, meaning, ownership, and similar presentation — not code identity. Create Layout mirror requires a brand/application-neutral contract. Future decks need not keep source page count/order.

### 1A. `.pptx` reference

Run `pptx_template_import.py "<reference.pptx>"`. Type A is the canonical mirror path: analysis manifests and inheritance own surviving native structure; `authoring-svg/` is the compact editable projection Template_Designer inspects and may redraw while preserving meaning, structure, and similar presentation; lossless `svg/` is immutable validation and non-visible-payload backing, never visible authoring; optional `svg-flat/` verifies full pages. In `standard` / `fidelity`, imported facts do not define output topology. Never copy lossless or flat pages into `templates/`; for Type A `mirror`, `mirror_template_materialize.py` validates and publishes after review, fidelity edits, and the readability pass, and authored modes never use it.

**Explicit complex-SVG picture normalization** (`standard` / `fidelity` only): when one imported native group is deliberately retained as one complex SVG picture rather than rebuilt as editable paths, select its exact id in the layered IR with `extract_svg_pictures.py ... --select "<group_id>" --resource-root "<import_workspace>" --images-dir "<import_workspace>/picture-assets" --inplace` (repeat `--select` for independent siblings; select the outer group when an ancestor carries a transform, style, clip, or opacity). If chosen for a Master or Layout, copy the asset into the image pool and author the fixed atom as a direct `<image data-pptx-layer="master|layout">`. This is a semantic decision, never automatic, never by repetition, never a way to infer ownership; not for placeholders, individual native shapes, table/chart fallbacks, icon placeholders, authored presets, or `mirror`.

**Read order**: `standard` / `fidelity` read `analysis/manifest.json`, exported resources, `svg/inheritance.json`, `authoring_summary.json`, and every cleaned layered IR document (Masters, Layouts, Slides — the complete read surface, including Layouts unused by any sample slide); flat pages are optional spot checks; never `authoring_manifest.json`. `mirror` reads both manifests, inheritance, the summary, every source Slide SVG, and only reachable Master/Layout SVGs. Use manifest facts for orientation and screenshots or the original PPTX only for visual cross-checking; never bulk-read opaque payload.

**Mirror reachable-graph gate**: before offering `mirror`, compare every source Slide and referenced Layout/Master with the authoring summary; missing reachable evidence or ambiguous parentage blocks; omit unused identities. The publisher verifies source SHA, refs, graph/assignment closure, and subtree hashes; an authored change never triggers visible XML restoration.

### Basic norm extraction (mandatory when reference content exists)

Extract the source's observable operating rules — not generic design advice — so they flow into `design_spec.md`. Create Brand extracts only the identity subset; Create Style extracts argument flow, message/evidence discipline, open page-role vocabulary, data-expression rules, composition/density rhythm, visual defaults, and image/icon direction while discarding source-specific audience, objective, page order/count, mappings, canvas, and structure. Create Layout/Create Deck extract:

| Norm area | Extract from | Record as |
|---|---|---|
| Canvas / page geometry | Manifest slide size, SVG `viewBox` | `[fact]` canvas format, pixel dimensions, source `viewBox`, aspect ratio |
| Identity system | Theme colors, font usage, logo assets, recurring backgrounds | `[fact]` when imported; `[suggested]` for visual estimates |
| Layout grammar | Masters/layouts, repeated chrome, margins, columns, card grids, dividers | Template-specific rules, not generic spacing |
| Image system | Crops/clips, scrims, baked alpha, full-bleed zones, hero placement, mosaics, captions | Template-specific placement rules with source examples |
| Density rhythm | Title scale, block count, whitespace, dense vs breathing pages | Page-type guidance |
| Page roster semantics | Cover / TOC / chapter / content / ending variants and slots | `design_spec.md §V` rows |
| Asset policy | Template-owned vs sample-only images/icons/textures | `§VI` or omit sample-only assets |
| Native structure | `native_structure.json` plus inheritance | Mirror maps each source Slide's reachable chain one-to-one; authored modes review the inventory and author a new graph through Slide prototypes |

"`slide_07` uses a left photo crop" is a fact; "content pages may use a left photo rail for case-study pages" is the reusable rule.

### 1B. Existing SVG assets

Resolve the Type B source: a root exposing any `templates/` Design Spec uses `<input>/templates/` plus sibling `images/` / `icons/`; otherwise the directory is loose evidence (flatness is not a structure signal). Build the throwaway IR bundle per [`template-tools.md`](../scripts/docs/template-tools.md), then read `authoring_summary.json`, `ls` the workspace, and every cleaned `authoring-svg/*.svg` for canvas, recurring colors (dominant 2–4 hex as candidate theme colors), fonts, existing `{{...}}` placeholders, and structural decoration; open imported vectors only when a specific asset affects a decision. A companion `design_spec.md` / `spec_lock.md` is part of the mirror source contract and must agree with the SVG identities; in authored modes it is context only. Caveats: `mirror` requires a complete current explicit contract and preserves page count/order, presentation, each Slide's Layout/Master chain, slot metadata, native-object metadata, and ownership in the new workspace (page type from a PPT Master-convention filename, else `content`; a loose visual-only folder cannot mirror); `fidelity` designs a broader new roster and structure after inspecting the complete roster; legacy or unstructured B (`baseline` / `preserve` / `layout_strategy: distill` / `data-pptx-layout-kind` / direct atomic placeholders / no root identity) is visual reference for authored modes only — use the original PPTX to mirror native facts; a selected free-design subset ingests only the named pages and never scans the whole `svg_output/`.

### 1C. Image / visual references

`Read` each image/PDF page: rough theme hues (never exact HEX as fact), approximate page count, typography style (sans / serif / display, never a font name), motifs and rhythm. Every derived value is `[suggested]`.

### 1D. Text, document, website, and asset references

Direct chat text is valid input. Read Markdown/TXT directly; convert documents/URLs with `source_to_md.py "<file_or_URL_or_dir>" -o "<text_analysis_workspace>"`; inventory supplied logo/icon/font assets (raster assets also enter the Type C pass; page/template SVGs may enter Type B); never infer licensing, official status, or native structure from filenames. Extract only what the source states: identity rules; Style method (argument flow, evidence discipline, page-role vocabulary, hierarchy, rhythm, visual defaults, image/icon direction, review focus — never the source's audience, objective, sequence, or page count); structure rules; Deck application (recurring situations, audiences/outcomes, delivery assumptions, representative roles, examples, negative requirements — never converted into mandatory future-use policy). A user-authored value is `[decision]` in any carrier; `[fact]` only when independently traceable to an external authority or machine-observable metadata; vague prose stays `[suggested]`. Text and assets never supply Master/Layout topology.

### 1E. No reference material

Skip analysis; Step 2 lists every Required item as `[decision]`. Create Brand may emit an empty skeleton only under its explicit child rule; the other children still require the gate.

---

## Step 2: Fact-Based Brief Proposal

Compose one concise natural-language proposal, in the user's language, describing the intended result with every material value labelled: `[fact]` (external authority or machine-observable metadata — a user-written brief file is not a fact), `[suggested]` (AI-inferred), `[decision]` (explicit user-authored, in chat, pasted text, or a brief file), `[derived]` (internal execution value recorded for provenance, never a user choice). Present one recommended creation plan — never a menu of modes, fidelity levels, or checklists; translate "原样还原" / "提取成可复用母版和版式" / "保留风格但重新设计" directly into the plan; ask a follow-up only when a missing decision would materially change the artifact. Technical IDs appear only in a compact audit note.

| Field | Must show |
|---|---|
| Output scope | Recommended `library` plus `project`; same schema and asset routing, different parent path, spec filename, and registration |
| Target project | `project` only: the exact initialized workspace path |
| Selected child | Echo the dispatched child; never reopen kind selection |
| Method and direction | Style only: portable method, evidence discipline, page-role vocabulary, information design, visual defaults, image/icon direction, review focus — no current audience/outcome, page order/count, canvas, or prototype plan |
| Category | Layout/Deck: one discovery category (Deck `brand` / `general` / `scenario` / `government` / `special`; Layout without `brand`); a Layout scenario category records geometric fit only |
| Application context | Deck only: recurring family, likely audiences/outcomes, delivery assumptions, representative roles — descriptive, not future-use policy |
| Theme direction | Layout/Deck: light/dark/mixed in plain language (Brand records identity colors instead) |
| Canvas | Layout/Deck: the recommended canvas with exact pixels and `viewBox`; no same-ratio alternatives unless asked or genuinely ambiguous |
| Creation plan | Layout/Deck: what is preserved, what is rebuilt, how broad the roster is, how native structure is handled; `replication_mode` is derived from this prose after confirmation |
| Native structure plan | Layout/Deck: compact `standard`, broader `fidelity`, or source-reachable `mirror`; every authored Layout needs a Slide prototype; reject duplicate Masters |
| Asset bundling | Brand/Layout/Deck: included assets plus excluded candidates with a one-line reason; Style records textual provenance only |

Items to surface: output scope and target project (`[decision]`); template ID (`[decision]` or a filesystem-safe ASCII slug `[suggested]`, the library index key) and display name (`[decision]` when supplied, otherwise `[suggested]`, for Type A often from `analysis/manifest.json.source.name`); category; applicable scenarios (Brand identity use cases; Style broad best-fit context without binding audience/outcome; Layout supported content shapes and delivery settings without communication ownership; Deck recurring situations); Deck application context and representative roles; identity/method/structural summary; Style communication method, visual-system defaults (overrideable seeds, never identity truth or Stage-2 locks), and review focus (applies only if the user enables visual review); theme mode and canvas (A/B `[fact]`, C `[suggested]`, D `[fact]` / `[decision]` / `[suggested]`, E `[decision]` with default `ppt169` `1280x720`); internal creation strategy (`[derived]`); native structure facts for A/structured B (`[fact]`: master/layout counts, parentage, assignments, placeholder identities, multi-master status); structure ownership plan and per-page reference treatment (`[derived]`); basic norms; reference source; theme color and fonts (Brand/Deck only; C fonts are never derivable); design style (required for Style as an overrideable seed); assets list (never for Style); keywords (3–5 tags; not for Brand). For Type A Layout/Deck, also name the authoring documents the derived strategy requires, a one-line source Master/Layout summary, and whether source structure facts will be preserved or used only as evidence.

**Persist the portable brief into `<design_spec_path>`** in Step 4 as YAML frontmatter with the child ID key (`brand_id` / `style_id` / `layout_id` / `deck_id`) and only child-owned fields: Brand its identity schema; Style only `style_id`, `kind`, `summary`, `keywords`; Layout/Deck the confirmed portable fields (`kind`, `category`, `summary`, `keywords`, `primary_color` for deck, `page_types` for layout, `canvas_format`, `canvas_width`, `canvas_height`, `canvas_viewbox`, `source_viewbox`, `replication_mode`, `native_structure_mode`, …). Never persist a generic `template_id`, `output_scope`, or `target_project`. In library scope `register_template.py` reads this frontmatter in Step 7.

---

## Step 3: User Confirmation Gate

**MANDATORY interactive gate — blocks Steps 4 onward.** Echo the finalized brief in one message, then emit `[TEMPLATE_BRIEF_CONFIRMED]` on its own line. Silently inferring values from files, direct text, an opened IDE file, or prior conversation is a route violation: even a complete PPTX, website, or written brief only informs the brief.

Before emitting the marker, all must hold: every Required item shown with provenance; one natural-language plan, no mode menu; internal IDs absent or confined to an audit note; the user replied with corrections or acceptance; scope confirmed (project with an explicit initialized path); for Layout/Deck the canvas is fixed and the derived strategy matches the evidence (`fidelity` needs A/B, `mirror` needs A or structured B, C/D/E permit only `standard`; Layout mirror evidence is brand/application-neutral); every channel analyzed or explicitly excluded with conflicts surfaced; for mirror, every source Slide and reachable chain valid and context-complete with omitted identities and missing facts reported; child-specific norms surfaced or marked N/A; for Style, method, vocabulary, evidence rules, defaults, direction, and review focus confirmed with project-specific context and identity/structure N/A; for Layout/Deck, structure ownership explicit; for Deck, application context understood without turning it into policy, and for Layout no application or identity leaked; for Brand, all identity fields confirmed with canvas/replication/structure N/A; library metadata complete enough to register, or project scope with no registration planned.

---

## Step 4: Preflight Output + Invoke the Selected Child

> Precondition: `[TEMPLATE_BRIEF_CONFIRMED]` emitted in Step 3.

Resolve `<template_workspace>` from scope (`skills/ppt-master/templates/<kind_dir>/<template_id>` or `<target_project>`), `mkdir -p "$template_workspace/templates"`, and create optional roots only when writing a real asset. Normally `<authoring_workspace>` equals `<template_workspace>`; when the project already has the other structural kind, author in an isolated project-shaped root through validation and preview, then install its spec at `<installed_design_spec_path>` and assets atomically (Layout replaces the Deck roster; Deck beside Layout installs no structural payload), deleting staging only after the final root passes.

**Preflight (atomic, parent-level, before any final write)**: resolve `<design_spec_path>` and every destination; for `library` confirm `templates/` is empty; for `project` reject a bare `design_spec.md`, an existing spec of the selected kind, or an invalid qualified-name set (distinct kinds coexist; Layout owns structure when present; adding Layout beside Deck replaces the Deck structural payload only after isolated validation); resolve every bitmap and vector filename and confirm nothing overwrites an existing file in `images/` or `icons/imported/`; check the review-PPTX destination when requested or multi-Master. Any failure aborts before writing anything; never overwrite an unrelated name conflict.

**Create Brand / Create Style branch**: continue in the child's §3 with the confirmed brief and resolved paths, then return to that child's branch in Step 5 — no Template_Designer, no SVG, no structure.

**Create Layout / Create Deck branch**: switch to Template_Designer with `<template_workspace>` bound to `<authoring_workspace>`, `<design_spec_path>`, the Step 3 brief, and the Step 1 analysis bundle. **Mandatory — authored construction bundle**: as soon as the strategy resolves to `standard` or `fidelity`, and before selecting any contour, read [`native-shape-authoring.md`](../references/native-shape-authoring.md) and [`preset-shape-vocabulary.md`](../references/preset-shape-vocabulary.md) completely; never load them for `mirror`. Pass the applicable package: Type A — the brief, `analysis/manifest.json`, `native_structure.json` and `sources/source.pptx`, `validation/conversion-report.json` when present, exported resources, `*_vector_asset_inventory.json` as an exact-id query surface, `authoring_summary.json` plus the layered IR (manifest bundled for the compiler, never loaded), and for `mirror` the immutable `svg/` plus `inheritance.json`; Type B — the summary, cleaned SVG list, inventory query surface, companion specs, notes; Type C — image list and notes; Type D — direct text, converted outputs, source list, asset inventory, notes; Type E — the brief only; mixed — the union with provenance and conflicts explicit.

| Mode | Final SVG authority | Structure behavior |
|---|---|---|
| `standard` / `fidelity` | Newly authored SVGs from the brief and complete source evidence | Author a compact or broader useful Master/Layout/slot system; never retain identities merely because they exist. Use the compact canonical `<g>` from `preset_shape_svg.py` when one registered preset expresses one object (paint from the brief and spec; add only the registered structural attributes after insertion; geometry or paint changes require a new render); Template_Designer decides any `shape_boolean_svg.py` use under [`native-shape-authoring.md`](../references/native-shape-authoring.md) §6 |
| `mirror` | Reviewed compact authoring SVG plus inline native JSON and structure facts | Publish source Slides and their reachable chains from the current authored tree; complete inherited context without changing ownership; similar presentation required, code isomorphism not. Redraw/normalize visible SVG, equivalent inheritance, safe metadata, and transport without changing meaning; never synthesize, promote/demote, rename, or re-parent |

For Type A `mirror`, publish with `mirror_template_materialize.py "<import_workspace>" "<authoring_workspace>"` into a workspace with no existing roster; it validates and publishes but never authors visible design, writes the sidecars listed in [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md#mirror_template_materializepy), and does not create the Design Spec — Template_Designer writes it from the brief and the materialized roster before Step 5.

**Hard rule — multi-Master package boundary**: more than one Master is valid only when `mirror` preserves a source graph or an authored template intentionally defines distinct reusable design families — never one Master per Layout or equivalent duplicates. Every Master owns at least one emitted Layout and every Layout is selected by at least one prototype. SVG authors own the semantic roster, parentage, picker names, atoms, and slots; the exporter owns OOXML cloning, Theme isolation (one Theme part per Master — two Masters never resolve to the same `ppt/theme/themeN.xml`), `p14:creationId` uniqueness, numeric registration, and relationship registration — never encode package repair in SVGs. Do not package `native_structure.json` or `source.pptx` as template inputs.

**Sprite-sheet preservation**: PPTX-exported assets are often sprite sheets cropped through nested `<svg viewBox>` wrappers around `<image width="1" height="1">`; that nesting is load-bearing geometry — preserve the exact `viewBox` crop and outer placement, never flatten to one `<image>` with direct geometry. If an asset's pixel aspect differs from its on-page aspect, it is a sprite.

**Mirror authoring/publication** (A or B): author and publish one SVG per source Slide in `<authoring_workspace>/templates/` — inspect every matching `authoring-svg/` document, redraw where useful, refresh the summary, then run the materializer (never hand-copy the lossless tree or rebuild the graph); preserve reachable keys, picker names, parentage, assignment, placeholder type/index/bounds, inherited-shape visibility, ownership, and native facts; unused identities produce no file. Name files `<NNN>_<page_type>.svg` (3-digit source order; type from `pageTypeCandidates` for A, from a convention filename or content for B, else `content`). Route assets through the common contract — Type A media from `<import_workspace>/images/`, Type B relative hrefs resolved and copied once — into `images/` with `../images/<name>` references and semantic directories for audio/video/payloads, keeping stable source asset identity; copy decoration vectors once to `icons/imported/` as `<use data-icon="imported/<name>" data-pptx-asset-role="decoration"/>` (never `templates/icons/`, never inlined by hand). Write `<design_spec_path>` per template-designer §1; `replication_mode: mirror` records creation, never a 1:1 downstream sequence.

**Expected outputs**: `<design_spec_path>` with package-specific rules only (deck: descriptive Overview, Color Scheme, Signature Elements, factual Page Roster, conditional Typography / Assets / Overrides; layout: structure-owned Signature Elements and Page Roster only) and no restated generic constraints; the roster per template-designer; conventional `{{...}}` placeholder vocabulary with a `placeholders:` frontmatter override when a style legitimately differs (indexed TOC pattern, never one-off families); each SVG carrying the native contract — root identity, direct atomic fixed layers, direct slot `<g>` with design-zone bounds and exactly one compatible carrier (a validated compact preset `<g>` counts as one atom or one `object` carrier; composite regions use only the `object` + `proxy` downgrade; `data-pptx-role` only when specialized metadata cannot express behavior); optional assets under the common routing.

**Hard rule — placeholder examples are executable defaults**: in authored templates a carrier is the prototype Slide placeholder and `data-pptx-bounds` the reusable Layout frame — the complete intended box, never the sample text's glyph bounds; general `body` and text-carried `object` slots begin upper-left, left-aligned, wrapping inside the frame, while center alignment is reserved for short focal content (record a template-wide exception in `§IV`); `template_preview_pptx.py` sizes each review carrier to the same frame and substitutes concise sample text only in ephemeral copies; `mirror` keeps source Slide carrier geometry in the tool-side native record and `data-pptx-bounds` as the Layout default without normalizing one to the other.

---

## Step 5: Validate Template Assets

**Create Brand / Create Style**: run the child's §4 checklist and `svg_quality_checker.py "<template_workspace>/templates" --template-mode --canonical-authoring` in both scopes (it detects the kind and validates the roster-free contract); in `library` add `register_template.py <id> --kind brand|style --dry-run`. Then skip the rest of this step and Step 6. Style Review Focus is advisory only and never activates visual review.

**Create Layout / Create Deck**: `<template_source>` is the active authoring root's `templates/`. `ls` it and the `images/` / `icons/` roots, then run read-only validation (Template_Designer writes canonical compact SVG directly; mirror normalizes in memory; authored-preset and native record frames stay unchanged):

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_source>" --template-mode --canonical-authoring --format <canvas_format>
```

Checker behavior in template mode: [`template-tools.md`](../scripts/docs/template-tools.md#svg_quality_checkerpy---template-mode). It validates the authoring contract; Theme ownership, package IDs, and registrations are verified by Step 6.

**Checklist**: the spec follows the kind skeleton with template-specific norms and no generic restatement; every SVG is a complete prototype with a §V row (mirror adds one scope sentence for omitted identities); variant filenames use letter suffixes and reuse the parent placeholder set unless overridden; TOC uses the indexed form; frontmatter declares the canvas fields (and `source_*` for PPTX/SVG-backed templates) and `native_structure_mode: structured`; `viewBox` equals the declared canvas; model-facing bounds and page coordinates use at most two decimals while crop/path/transform/preset/native frames keep required precision; placeholder names follow the convention or a declared override; every referenced asset exists via `../images/` with no bitmap stranded in `templates/`; no `native_structure.json` or `source.pptx` packaged; every root declares Master/Layout keys and names with direct atomic fixed visuals in paint order; every slot is a direct `<g id>` with design-zone bounds and one compatible carrier or an explicit `object` proxy; authored bounds are complete editable boxes with upper-left body entry; review prompts stay readable without changing source markers; authored output was newly authored without distilling source topology; every extra Master is a distinct family with owned Layouts and prototypes; mirror preserves order, identity, parentage, placeholder facts, ownership, meaning, and presentation with a complete Source Preservation Map, canonical lowercase visibility attributes, complete reachable-chain preflight, and the execution manifest plus text-slot sidecars; no duplicate-Layout warning remains for authored modes; edits used the compact authoring SVG and mirror published through the materializer without lossless rehydration; extracted vectors use the `imported/<name>` decoration reference with no `templates/icons/`; fidelity keeps every sprite crop wrapper; mirror SVG count equals source Slide count with `<NNN>_<page_type>.svg` names, no standalone Master/Layout SVG, and no new `{{...}}` markers.

This step is a **hard gate**: no review PPTX, registration, staged install, or handoff until it passes. After a staged project install, rerun the checker on the final `<target_project>/templates/`. A one-Master template may skip Step 6 when no review was requested; a multi-Master template must pass Step 6 before registration or completion.

---

## Step 6: Template Review PPTX and Multi-Master Package Gate

**Trigger — Layout/Deck only**: a requested PowerPoint review file, or a validated roster declaring more than one unique Master key (required even without a request). Brand and Style always skip it.

```bash
python3 skills/ppt-master/scripts/template_preview_pptx.py "<authoring_workspace>"            # exports/<template_id>_template_preview.pptx
python3 skills/ppt-master/scripts/template_preview_pptx.py "<authoring_workspace>" --native-charts-and-tables -o "<authoring_workspace>/exports/<template_id>_template_preview_native.pptx"   # optional JSON-first check
python3 skills/ppt-master/scripts/template_preview_pptx.py "<authoring_workspace>" --force    # intentional replacement after a fix
```

Copy a requested/required review artifact into the target project's `exports/` during a staged install. **Validation**: the PPTX exists (and was copied after a staged transition); slide count equals the roster; read-back reports the expected Master/Layout counts and exact registrations; every Master targets a distinct Theme part; `p14:creationId` and registration IDs are valid and unique; for authored modes every carrier-bound placeholder matches its Layout placeholder's type, index, and frame (verified automatically); for mirror, source Slide-local geometry is unchanged; the user can review every page in filename order; when PowerPoint is available it opens without repair with every Layout under its Master — otherwise report package read-back as the evidence and claim no PowerPoint-open result. Every item is a hard gate for the artifact; a multi-Master failure blocks registration and completion, while an unrequested one-Master preview failure does not block a workspace that passed Step 5.

---

## Step 7: Register Template in Library Index (Library Scope Only)

`library`: after Step 5 (and Step 6 when requested or required), run `python3 skills/ppt-master/scripts/register_template.py <template_id> --kind brand|style|deck|layout`; it derives the entry from the spec frontmatter (preferred) or prose plus the actual `templates/*.svg` roster and updates that kind's `*_index.json` — the complete discovery source for Default Stage-1 controls and chat listing (neither scans directories). `project`: skip the registrar, edit no index or README, and report `Not registered (project workspace)`. An exact unregistered root supplied by the user or handed off by this route appears as an `explicit` candidate preselected only when it is the sole root; a root matching a registered canonical root may display as `library`; bare names are never resolved. Frontmatter examples per kind live in the child workflows; `--rebuild-all` rebuilds a kind's index after editing many specs.

---

## Step 8: Output Confirmation

```markdown
## Template Creation Complete

**Template Name**: <template_id> (<display_name>)
**Kind**: brand | style | layout | deck
**Output Scope**: library | project
**Workspace Path**: `<template_workspace>/`
**Template Source**: `<template_workspace>/templates/`
**Design Spec**: `<installed_design_spec_path>`
**Bitmap Path**: `<template_workspace>/images/`  ← omit when nothing was written or adopted
**Imported Vector Path**: `<template_workspace>/icons/imported/`  ← omit when nothing was written or adopted
**Review PPTX**: `<template_workspace>/exports/<template_id>_template_preview.pptx`  ← Layout/Deck only; omit when an optional one-Master review was not requested
**Primary Color**: <hex>  ← Brand/Deck only
**Index Registration**: Done | Not registered (project workspace)

### Files Included
| File | Status |
|------|--------|
| `templates/01_cover.svg` … | Done |
| `exports/<template_id>_template_preview.pptx` | Verified, when requested or required |
```

Brand lists the spec plus real identity assets; Style lists only its spec; both state `SVG roster: N/A` and `Native structure: N/A`, and Style adds `Visual review trigger: N/A (advisory focus only)`. The exact `<template_workspace>/` root is the current-conversation handoff to Generate Step 3: it appears as the specified candidate, defaults Stage 1 to template mode, and is preselected only when it is the sole root; after Stage 1 confirms it, application resolves its spec(s), ignores `exports/`, and authors new `svg_output/` pages — neither the reference nor the prototypes are upgraded in place, and any older flat or legacy package is evidence only.

---

## Notes

1. Layout/Deck load [`shared-standards-core.md`](../references/shared-standards-core.md) and [`pptx-structure-interface.md`](../references/pptx-structure-interface.md), plus [`svg-effects.md`](../references/svg-effects.md) only when the design uses those effects; Brand and Style author no SVG and load none. Never restate these contracts in a template spec.
2. Deck SVGs use the spec's §II Color Scheme; Layout owns no identity colors; Style owns only overrideable defaults.
3. Theme/Master/Layout/Placeholder are compiled PowerPoint objects, not template kinds: Layout owns topology and placement, Brand identity values and assets, Style portable direction, Deck descriptive application context.
4. Placeholders use `{{}}` with the canonical names in [template-designer.md §4](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template), overridden per template through `placeholders:` frontmatter.
5. A library template is discoverable only after Step 7; a project workspace stays out of the catalog and is consumed as an exact `explicit` root. Stage 1 confirms communication plus free design/template use together; only a non-free confirmed selection installs a workspace before Stage 2.
6. The review PPTX is derived local evidence, generated on request and always for multi-Master; Brand and Style never generate it.
