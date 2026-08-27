> See [`shared-standards-core.md`](./shared-standards-core.md) for common technical constraints.

# Template Designer — Template Design Role

## Core Mission

Generate reusable structured page templates inside the workspace selected by Create Template's Create Layout or Create Deck child workflow, and write the resolved Design Spec that captures the source-derived rules that make the template reusable. For Deck, include descriptive recurring-application context; for Layout, keep structure brand-neutral and application-neutral.

> This is a standalone role: only triggered by the Create Layout or Create Deck child workflow under `/create-template`. Create Brand never invokes it. Library and project outputs share one spec schema and asset routing with scope-resolved spec filenames; this is not the template selection step in the main PPT generation pipeline.

## Usage

- **Trigger**: `/create-template` → Create Layout or Create Deck child workflow
- **Workspace root**: `library` (default) → `skills/ppt-master/templates/<kind_dir>/<template_name>/`; `project` → the confirmed `<target_project>/`
- **Template source**: `<template_workspace>/templates/` in both scopes
- **Design Spec**: use the parent-resolved `<design_spec_path>` — library `templates/design_spec.md`; project `templates/design_spec.<kind>.<id>.md`
- **Input**: finalized template brief (output scope, target project when project-scoped, template ID, display name, kind, structural use cases or Deck application context, tone, theme mode, canvas format, optional reference assets, accepted basic template norms)

**Hard rule — scope is execution metadata**: Use `output_scope` and `target_project` to route files, but do not write either field into `<design_spec_path>` frontmatter. Do not create a new PPTX structure mode; deck/layout output declares `native_structure_mode: structured`.

**Workspace precondition**: The workflow has already resolved `<design_spec_path>` and checked all destinations. Library `templates/` is empty. The active authoring root contains no bare spec, selected-kind spec, or SVG roster; unique qualified roster-free siblings may remain untouched. When the target project already has the other structural kind, the parent workflow supplies an isolated project-shaped authoring root and owns the later Layout-over-Deck atomic install. Check collision-free destinations in `images/`, `icons/imported/`, and `exports/` when applicable. Optional directories may be absent until their first real file is written. Project scope additionally requires an initialized target project. Do not begin final writes before that all-at-once preflight passes.

When the workflow provides a PPTX reference source, the effective input package comes from the unified `pptx_template_import.py` preparation workspace and becomes:

- finalized template brief
- `analysis/manifest.json` — source-deck facts (slide size, theme, per-master themes, resources, image map, placeholders, layouts, masters, slides, SVG file paths, page-type candidates)
- `analysis/native_structure.json` — stable source master/layout keys, picker names, parent-master relationships, placeholder type/index/geometry, source hash, and source-graph quality facts
- `sources/source.pptx` — byte-preserved backing package for visual/package cross-checking; never a final template asset
- `validation/conversion-report.json` — source-recovery and fidelity diagnostics, when present
- exported `images/` plus other populated semantic resource directories
- `svg/master_*.svg` / `svg/layout_*.svg` — immutable layered native-payload backing; every master / layout in the deck rendered once, including ones no sample slide references
- `svg/slide_NN.svg` — immutable slide-local native-payload backing; do not bulk-read because opaque native payload is retained
- `svg/inheritance.json` — which layout / master each slide consumes
- optional `svg-flat/slide_NN.svg` — immutable complete-page verification backing generated only when explicitly requested; do not use it as the editable source
- `authoring-svg/` and optional `authoring-svg-flat/` — new compact SVG bundles generated from parsed PPTX evidence by `pptx_template_import.py` for Type A input or by the standalone `svg_authoring_view.py` migration path; the layered bundle is Template_Designer's editable authoring surface and also contains model-readable `authoring_summary.json` plus tool-only `authoring_manifest.json`
- optional screenshots for visual cross-checking

PPTX import interpretation:

- Placeholder guides in master / layout SVGs are layout signals. Use `analysis/manifest.json` placeholder records for type / index / geometry / base style; do not copy dashed guide boxes into final templates unless the visual design truly uses dashed boxes.
- Charts, SmartArt, diagrams, and OLE objects may appear as typed placeholders in layered SVGs. In flat SVGs they may show preview images. Treat them as source intent markers, not reusable decorative assets.
- The asset filenames referenced by SVGs are governed by the manifest asset map. Prefer those references over inventing duplicate asset names.

Input priority for PPTX-backed template creation depends on the AI-derived internal strategy recorded as `replication_mode`:

| Mode | Authoritative inputs | Model-facing inputs |
|---|---|---|
| `standard` / `fidelity` | Finalized brief for the newly designed output; `analysis/manifest.json` for factual canvas/theme/resources | `authoring-svg/authoring_summary.json`, every layered source Master/Layout as structural and visual evidence, layered source Slides, optional flat spot checks, and exported resources. Do not read `authoring_manifest.json`. `standard` authors a compact result; `fidelity` authors broader useful source-aligned coverage. Neither copies source identities merely because they exist. |
| `mirror` | Inline native Chart/Table JSON plus `analysis/manifest.json`, `analysis/native_structure.json`, and `svg/inheritance.json`; the publisher validates the tool-only authoring manifest | `authoring-svg/authoring_summary.json` plus every reachable layered compact SVG as the editable authoring source; optional `authoring-svg-flat/` for complete-page verification; matching lossless `svg/` only for source/package validation and supported non-visible payload recovery, never visible-subtree copying. |

**Mandatory — authored construction bundle**: As soon as `replication_mode`
resolves to `standard` or `fidelity`, and before selecting any page or template
contour, read [`native-shape-authoring.md`](./native-shape-authoring.md) and
[`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md) completely and
retain both for the active authoring context. Do not load this bundle for
`mirror`; it preserves source-owned geometry and never selects or authors
replacement contours.

Use the compact facts in `analysis/manifest.json` for orientation. Open screenshots or the original PPTX only for visual cross-checking.

**Native structure output**: Always set `native_structure_mode: structured`.

**Hard rule — native objects are compiled output**: Treat Theme, Master,
Layout, and Placeholder as PowerPoint implementation objects, not template
kinds. Layout owns topology, placement, semantic text roles, and spatial text
behavior. Deck identity owns paint, typeface identity, and fixed identity
assets; its application context describes the recurring presentation family. Under
downstream `layout` scope, resolve final placeholder formatting from the Layout
roles plus the confirmed identity, reading mode, and type scale; downstream
`mirror` scope preserves source structure and comparable presentation while
allowing compact SVG spelling. Compile
the applicable rules into the same native graph without merging their source
ownership.

| Mode | Output structure contract |
|---|---|
| `standard` / `fidelity` | Review the complete source Master/Layout inventory, then author complete project-canonical Slide SVG prototypes and an intentional new Master/Layout/slot system. Every retained Layout has at least one Slide prototype. `standard` stays compact; `fidelity` retains broader useful source-aligned families. Source identities do not define the output topology. Choose page-fit contours from the full native vocabulary before their authoring forms; keep exact native atoms independent, materialize a Boolean result only where one contour requires it, and use freeform last. |
| `mirror` | Review and author one complete compact SVG per validated source Slide, retaining only its referenced Layout and parent Master. Keep reachable identities, parentage, assignment, placeholder facts, inline JSON native authority, and source meaning. Presentation should remain recognizably similar, but SVG nodes and code need not be isomorphic. Publication completes inherited context and maps fixed-layer groups into direct atoms without inventing facts or semantically redesigning the reachable graph. |

Every output is a complete standalone Slide SVG preview that resolves Master +
Layout + Slide context. Explicit layer markers retain ownership; standalone
Master/Layout definition SVGs are not template artifacts.

**Authored preset rule**: In `standard` / `fidelity`, when one registered
PowerPoint preset exactly expresses one complete object, use
`preset_shape_svg.py` as defined by
[`native-shape-authoring.md`](./native-shape-authoring.md). Its compact
canonical `<g>` is one semantic atom after validation: it may remain
Slide-local, serve as the one direct carrier of an `object` slot, or carry
Master/Layout fixed-layer ownership. This is the only `<g>` exception to the
fixed-layer atomicity rule; ordinary groups remain forbidden there. Preset
paint comes from the confirmed brief and `<design_spec_path>`
color scheme. Do not copy an expanded import carrier/preview/fingerprint
bundle into an authored template. `mirror` instead uses the new compact parsed
SVG as its visible authoring source and never transplants the expanded lossless
visible subtree. The exact syntax and validation
contract remain owned by
[`shared-standards-core.md`](./shared-standards-core.md) and the native-shape reference.
When one preset is insufficient, apply the same reference's compound-page gate:
keep faithful atoms independent unless one contour requires Boolean
materialization, then use freeform only if neither construction succeeds.

**Hard rule — reachable mirror graph**: Emit exactly one complete source-page
prototype per source Slide and preserve only the transitive chain `Slide →
Layout → Master`. Source Master/Layout identities outside that closure remain
analysis evidence and produce no SVG. Use `standard` / `fidelity` when useful
unreferenced source structures must be re-authored as complete Slide prototypes.

**Hard rule — no duplicate authored Layout contracts**: In `standard` / `fidelity`, distinct output Layout keys must differ in fixed Layout atoms or slot topology/type/index/bounds/binding. Topic, sample wording, or Slide-local content alone never justifies another authored key. Mirror keeps distinct reachable source Layout identities even when two source contracts are visibly equivalent.

**Downstream boundary**: Stage 1 independently confirms the current communication contract. Strategist then inspects the installed prototypes, the Deck's descriptive application context, and the current content to author one application plan. It records `mirror`, `layout`, or `style` and, where applicable, `strict` or `adaptive` only as internal exporter values. Explicit user language overrides AI judgment, but the confirmation UI never asks the user to choose these implementation labels. Template_Designer does not preselect that project-level plan.

For `mirror`, `<design_spec_path> §V` must be followed by a `Source Preservation Map` that records each source Slide's retained Master/Layout assignment and output file. When source identities fall outside the reachable closure, one sentence may note that they exist but were not materialized; no per-identity analysis is required. The map is execution evidence, not a design-decision log. `standard` and `fidelity` record only their newly authored output roster and structure.

---

## Page Roster

The output page set is determined by the confirmed natural-language creation intent. Template_Designer derives one internal `replication_mode` so the deterministic authoring tools can execute:

| Mode | When to use | Roster |
|------|-------------|--------|
| `standard` (default internal strategy) | The requested result is a clean, reusable, compact system | Cover, chapter, ending, optional TOC, and one or a small explicitly required set of distinct content Layouts; typically 4–6 prototypes |
| `fidelity` | The natural-language intent calls for broader, source-aligned but newly designed coverage | Canonical roles plus intentionally designed variants that cover the useful source composition range |
| `mirror` | The natural-language intent calls for preserving validated native source facts and a similar presentation | One compact SVG prototype reviewed/authored from parsed evidence per source slide, named `<NNN>_<page_type>.svg` by source order |

**Hard rule — mode controls authorship**: `standard` and `fidelity` inspect the complete source structure but create new SVG documents and their own Master/Layout system. `mirror` also authors compact new SVG from parsed evidence, but it must retain the validated reachable identities, assignments, slots, meaning, and similar presentation rather than distilling, supplementing, or redesigning that closure. Code and node identity are not preservation requirements.

### Standard mode

| # | Filename | Purpose | Description |
|---|----------|---------|-------------|
| 01 | `01_cover.svg` | Cover | Fixed structure: title, subtitle, date, organization |
| 02 | `02_chapter.svg` | Chapter page | Fixed structure: chapter number, chapter title |
| 03 | `03_content.svg` | Content page | Flexible structure: only defines header/footer; content area freely laid out by AI |
| 04 | `04_ending.svg` | Ending page | Fixed structure: thank-you message, contact info |
| -- | `02_toc.svg` | Table of contents | Optional: TOC title, chapter list (number + title) |

**Default — compact authored roster (may override when the confirmed Deck application requires distinct roles)**: Keep Layout content pages structurally flexible. For Deck, add only the distinct prototypes needed to express its confirmed recurring narrative/content roles; do not manufacture variants from hypothetical future uses.

**Intent-derived compact variants**: `standard` may include more than one Layout for the same canonical role when the brief requires genuinely different reusable structures, such as two-column evidence and three-card KPI content. Keep the roster compact and brief-driven rather than mining the source page set. When siblings exist, suffix every sibling (`03a_content_two_col.svg`, `03b_content_three_card.svg`) instead of treating one arbitrary variant as the unsuffixed default. This does not require `fidelity`; derive `fidelity` when the broader roster is driven by complete PPTX/SVG page evidence.

**Naming note**: The numeric prefix is the template's own presentation order. Its base sequence stays contiguous; sibling variants share their parent's number only through unique lowercase suffixes such as `03a` / `03b`. When the optional TOC page is included it takes `02_toc.svg` and the later types shift by one: `01_cover`, `02_toc`, `03_chapter`, `04_content`, `05_ending`. Numbers carry no meaning across templates — tooling derives the page type from the token after the underscore, so both spellings of each type are equivalent.

### Fidelity mode

When the derived implementation writes `replication_mode: fidelity`, design a broader reusable roster that stays close to the source's visual language and useful composition examples. The output Master/Layout system is authored independently from source topology.

**Variant naming**: append a lowercase letter suffix to the parent type's index, preserving sort order:

| Parent type | Example variants |
|-------------|------------------|
| Chapter | `02a_chapter_full.svg`, `02b_chapter_minimal.svg` |
| Content | `03a_content_two_col.svg`, `03b_content_data_card.svg`, `03c_content_quote.svg` |
| Ending | `04a_ending_thanks.svg`, `04b_ending_contact.svg` |

Extension page types beyond the canonical four (transition / appendix / disclaimer / divider) take the next free index after the roster: `05_section_break.svg`, `06_appendix.svg`, `07_disclaimer.svg` in a four-page roster (one higher when `02_toc` is present).

**Roster decision**:

- Choose variants from useful visual composition types such as two-column content, hero image, icon grid, data card, and quote
- Keep only variants that add a genuinely useful authored composition; source Layout keys and repeated source chrome are not clustering inputs
- Design each variant's Master/Layout/slot contract directly from its intended reusable behavior
- Record every emitted page in `<design_spec_path> §V Page Roster`; in library scope, `register_template.py` generates the corresponding index entry from `<template_workspace>/templates/*.svg`. Project scope skips registration

> Variants reuse the parent type's placeholder set — see §4 (Placeholder Reference) below.

### Mirror mode

When the derived implementation writes `replication_mode: mirror`, author a new compact template workspace from validated parsed evidence rather than designing a different system:

- Kind eligibility: Create Layout mirror is legal only when the validated source contract is already brand-neutral and application-neutral. If supported source facts retain organization-specific identity or reusable application policy, stop and return to Create Template dispatch: use `standard` / `fidelity` to author a new Layout, or Create Deck to retain those facts. Removing, repainting, retyping, or discarding application rules is never mirror.
- Model-facing authoring source: `authoring-svg/authoring_summary.json`, every reachable layered `authoring-svg/*.svg`, `svg/inheritance.json`, and `analysis/native_structure.json`. Template_Designer must actually inspect and, where needed, redraw/normalize these new compact SVGs before publication. Do not read `authoring-svg/authoring_manifest.json`; the publisher validates it internally. When present, use `authoring-svg-flat/` only for full-page verification. Matching lossless `svg/` files are immutable source/package evidence and non-visible payload backing, never visible authoring input.
- Precondition: the import evidence identifies every source Slide and its referenced Layout/Master, picker names, placeholder contract, and fixed visual layers. Stop when required reachable facts or supported mirrored geometry are missing; unused source identities are out of scope.
- Output: `<template_workspace>/templates/<NNN>_<page_type>.svg` for every source Slide and no standalone Master/Layout SVG. `<NNN>` is the zero-padded source slide index (3 digits) and `<page_type>` comes from `analysis/manifest.json` `pageTypeCandidates` — `cover` / `toc` / `chapter` / `content` / `ending`, falling back to `content`. Preserve source Slide order.
- Context completion: each source-page SVG resolves Master + Layout + Slide context while retaining explicit layer markers, so completion does not flatten ownership.
- Required preservation: within the reachable closure, preserve source Master/Layout keys and picker names, Layout-to-Master parentage, slide assignments, placeholder type/index/bounds, original example meaning, sprite-sheet crop behavior, and supported native facts. Imported/template-owned Chart/Table inline JSON is authoritative; its compact SVG preview may be approximate.
- Allowed authoring: redraw or normalize visible SVG geometry, paint spelling, grouping, root declarations, asset paths, and fixed-layer wrappers when the resulting presentation remains similar and ownership/paint intent stays intact. Complete inherited context and emit direct structural atoms; code, node count, and exact path identity need not match the import.
- Forbidden: commonality extraction, semantic synthesis, promotion/demotion, renaming, re-parenting, placeholder invention, changes to authoritative Chart/Table JSON without matching intent, or any visible redesign that changes the source communication result.
- `<design_spec_path>` §V gives each emitted source-Slide prototype a roster row. If relevant, one sentence notes source Master/Layout identities outside the mirror closure; `Source Preservation Map` records each retained source-Slide assignment.

**Mirror consumption boundary**: `replication_mode: mirror` describes source-to-workspace fidelity and only makes literal downstream reuse technically possible. Strategist independently derives the application plan from the current communication contract, content, actual prototype roster, and any explicit natural-language instruction. It may select, repeat, skip, reorder, or reorganize prototypes; no internal scope forces source page count, source order, or one output slide per source slide.

**What mirror is not**: a redesign, topology-cleanup, or recovery mode. It is a new compact SVG authoring pass over parsed evidence, followed by deterministic validation/publication; neither byte identity nor SVG-code identity is promised. Charts, SmartArt, OLE objects, and EMF / WMF media that fail to enter the parsed evidence cannot be recovered by mirror. If the import workspace has missing media or unsupported objects, mirror inherits those gaps — report them before authoring begins.

---

## Template Design Specifications

### 1. Must Generate design_spec.md

**Scope rule — package-specific rules only.** A Deck `design_spec.md` describes its recurring application plus integrated identity and structure. A Layout spec describes only brand-neutral reusable structure and may state supported content shapes/delivery settings without owning a communication objective or narrative. Neither restates generic constraints — those live in the canonical references and are already loaded by every downstream role:

- Always-on SVG rules and conditional-module routing → [`shared-standards-core.md`](./shared-standards-core.md)
- Generic layout pattern library, spacing bands, font-size ratio bands → [`strategist.md`](strategist.md) (used when authoring the **project** design spec)
- Canonical placeholder vocabulary → §4 below
- Content methodology (pyramid / SCQA / MECE) → [`strategist.md`](strategist.md)

Re-declaring any of these in a template `design_spec.md` is noise — Strategist already has them in context, and duplication forces every relaxation to sweep N templates instead of one source. **If a rule is generic, omit it. If this template breaks a generic rule, write only the deviation.**

**Required skeleton by kind:**

The frontmatter is portable across library and project scope. Do not add
`output_scope` or `target_project`; those belong only to the workflow execution
brief. Use `deck_id` or `layout_id`; do not invent a generic `template_id`
field that the registrar cannot bind to its library kind.

**Deck**:

```markdown
---
deck_id: <id>
kind: deck
category: brand | general | scenario | government | special
summary: <one-line recurring presentation family and intended outcome>
keywords: [tag1, tag2, tag3]
primary_color: "#......"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
# Required when a PPTX/SVG source canvas is known; keep equal to canvas_* unless explicitly normalized.
source_canvas_width: 1280
source_canvas_height: 720
source_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
# Required for every deck/layout template. Source packages remain analysis-only.
native_structure_mode: structured
page_count: <N>
# Optional — only when this template overrides canonical placeholder vocabulary.
# Omit the map when canonical vocabulary is sufficient; use [] for an intentional zero-marker page.
# placeholders:
#   01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LOGO}}"]
#   03_content: ["{{KEY_MESSAGE}}", "{{CONTENT_AREA}}"]
---

# [Template Name] — Design Specification

## I. Template Overview
| Application context | Definition |
|---|---|
| Recurring presentation family | <repeatable situations this Deck serves> |
| Intended audiences and outcomes | <who it serves and what the presentation should enable> |
| Delivery and reading assumptions | <presented / close-read / handoff / mixed> |
| Representative narrative/page roles | <roles commonly present in this presentation family; descriptive, not mandatory> |

- Design tone, theme mode (light / dark / mixed), and the visual identity visible at a glance

## II. Color Scheme
- HEX values with role labels (primary / accent / background / text / etc.)
- Brand-specific application rules when present (e.g. "KPI cards rotate blue→green→red→yellow")

## III. Typography (omit without template-owned typeface identity)
- Per-role stacks for identity (display serif, brand face, etc.)
- A non-preinstalled face may lead only after user-confirmed target installation/approved install; no auto-embedding
- Otherwise export a safe face; unavailable proprietary faces stay references. CSS tails aid preview, not deterministic PowerPoint fallback
- Body baseline px (informational; `spec_lock.md` owns the actual values per project)

## IV. Signature Design Elements
- Decorative motifs that ARE this template — top bar, gradient underline, logo treatment, brand emblem placement
- Source-derived layout grammar — grid / column rhythm, page chrome, image zones, crop/clip behavior, scrim/overlay or baked-alpha treatment, and density rhythm that make the template recognizable
- Optional XML snippet for any reusable component unique to this template

## V. Page Roster
One row per complete Slide SVG describing what this template's version of cover / chapter / content / ending looks like: background treatment, decorative anchors, layout rhythm, image behavior, content density, intended role, reusable slots, and structural capacity. Do not add required/optional/repeatable status or fixed/replaceable/example-only content policy. For `standard` / `fidelity`, record the newly authored Layout key and PowerPoint picker name. For `mirror`, record the preserved reachable Master/Layout keys and picker names without redesigning them. Roster entries must match every SVG on disk.

For `mirror`, add `### Source Preservation Map` immediately after the roster with columns `Source slide`, `Source Master`, `Source Layout`, `Output SVG`, and `Preservation status`. When relevant, add one sentence that unreferenced source identities were not materialized by mirror; do not add individual disposition rows or synthesis rationale. Do not add source-structure disposition rows to `standard` / `fidelity` templates.

## VI. Assets (omit when none)
Logos, cover backgrounds, brand textures bundled with the template package — file name, dimensions, intended usage.

## VII. Placeholder Overrides (omit when none)
Reference the `placeholders:` frontmatter declaration and explain the rationale (e.g. "consulting decks lead with `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`").
```

**Layout**:

```markdown
---
layout_id: <id>
kind: layout
category: general | scenario | government | special
summary: <one-line structural use case>
keywords: [tag1, tag2, tag3]
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
# Required when a PPTX/SVG source canvas is known.
source_canvas_width: 1280
source_canvas_height: 720
source_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
page_types: [cover, toc, chapter, content, ending]
# Optional vocabulary override.
# placeholders:
#   01_cover: ["{{TITLE}}", "{{SUBTITLE}}"]
---

# [Layout Name] — Design Specification

## IV. Signature Design Elements
- Structure-specific grid, zones, page chrome, image behavior, density rhythm, semantic text roles, alignment/wrapping/capacity behavior, and slot conventions
- Neutral preview paint/font/size may expose hierarchy, but it is not a color, typeface, or final type-scale identity

## V. Page Roster
One row per emitted SVG with Layout key, picker name, supported content shape, and slot behavior. Roster entries must match the actual files on disk.

For `mirror`, append the same `### Source Preservation Map` required above.

## VII. Placeholder Overrides (omit when none)
Reference the `placeholders:` frontmatter declaration and explain the structural vocabulary deviation.
```

**Layout boundary**: Omit Template Overview, Color Scheme, Typography, Logo,
Voice & Tone, and Icon Style. A scenario category records geometric fit only.
Structural text roles, alignment, wrapping, and capacity remain valid Layout
rules; final font families, weights, colors, and absolute sizes do not.
Do not prescribe communication objectives, audience outcomes, required
narrative order, fixed boilerplate, or example-content retention. The
frontmatter `summary` carries concise structural selection context; the
deck-only Template Overview remains the application segment read during
template application.

Sections to **omit** from template `design_spec.md` (sourced elsewhere — listing them here is noise):

| Don't write | Source |
|---|---|
| Always-on SVG rules and conditional-module routing | `shared-standards-core.md` |
| Generic layout pattern library (centered card / three-column / timeline / …) | `strategist.md` §4 |
| Generic font-size hierarchy (cover 2.5-5x body, page title 1.5-2x, …) | `strategist.md` §g |
| Canonical placeholder table (`{{TITLE}}`, `{{PAGE_NUM}}`, …) | §4 below |
| Content methodology (pyramid / SCQA / MECE) | `strategist.md` |
| "Usage Instructions" boilerplate (copy template / select page / …) | `create-template.md` |
| Created Date / Page Count rows | not a library-level field |

When rewriting an existing template that contains an omitted generic section,
delete it rather than leaving a pointer. Keep a template-specific boundary only
inside the package-owned section it qualifies (asset system, motif, image
treatment, or page roster); do not preserve a generic technical-rules heading.

### 2. Inherit Design Specification

Templates must strictly follow the finalized template brief and the generated `<design_spec_path>`:
- **Canvas dimensions**: `canvas_format` is not enough; root SVG `viewBox` matches `canvas_viewbox` in the design spec. Root `width` / `height` are optional compatibility attributes and are not PPT Master canvas authority.
- **Source canvas**: when a PPTX/SVG reference is used, record `source_canvas_width`, `source_canvas_height`, and `source_viewbox`. If the output canvas differs from the source, normalize all geometry, typography, line heights, strokes, and image crop coordinates explicitly instead of relying on the shared aspect ratio.
- **Color scheme**: Uses primary, secondary, and accent colors from the spec
- **Font plan**: Uses the per-role font families declared in the spec
- **Layout principles**: Margins and spacing conform to the spec
- **Image system**: Image placement, crop/clip behavior, full-bleed zones, and scrim/overlay or baked-alpha treatment follow the source-derived norms in the spec
- **Deck application**: Template Overview describes the recurring situations, audiences/outcomes, and representative roles; Page Roster factually describes the actual prototypes and reusable slots without prescribing future use

If PPTX import output exists:
- Prefer imported theme colors and fonts over visually guessed values
- Reuse exported `images/` directly — raster images and SVG/EMF/WMF image media use the same canonical pool, and `<image>` references in `svg/` already point at it
- Treat page-type candidates from `analysis/manifest.json.pageTypeCandidates` as hints, not guarantees

**Precondition**:

- For `standard`, inspect the complete lightweight source Master/Layout inventory plus enough complete-page IR documents to understand the requested visual direction, structural vocabulary, and reusable assets. Author a compact new structure; source identities are evidence, not output requirements.
- For `fidelity`, inspect every lightweight source Master/Layout and complete-page IR document so the newly designed roster covers the useful source structure and composition range. Author broader source-aligned families without automatically copying every source identity.
- For `mirror`, verify every source Slide and its referenced Layout/Master against `authoring_summary.json`, `analysis/native_structure.json`, and `svg/inheritance.json`; then review/author every reachable compact SVG and publish only that graph. Lossless backing may validate provenance and recover supported non-visible payload, but never replaces the visible authored tree. Before authoring begins, report source Slide indexes plus retained and omitted Master/Layout identities.

### 2.1 PPTX Import Mode Rule

The imported PPTX has a different authority level in each replication mode.

| Mode | Required behavior |
|---|---|
| `standard` | Review the complete source Master/Layout and visual evidence, then author a compact project-canonical roster and its Master/Layout/slot structure from the confirmed brief. Do not preserve source identities merely because they exist. |
| `fidelity` | Review the complete source Master/Layout and visual roster, then author a broader canonical roster and its own useful source-aligned Master/Layout/slot families. Match the source visual language closely without implying one-to-one identity retention. |
| `mirror` | Preserve validated source Slides and their reachable inheritance, placeholders, native facts, meaning, and similar presentation while authoring a compact new workspace. Complete each standalone SVG's inherited context; visible SVG may be redrawn/normalized without code isomorphism, but retained structure cannot be renamed and semantic gaps cannot be invented. |

**Hard rule — mirror publication is mechanical, visual authoring is not**:
Template_Designer owns the compact visible SVG created from parsed evidence.
The materializer validates source identity/SHA, refs, graph, assignments, and
closure; composes inherited context; strips IR-only refs; and publishes that
current tree. It must never replace an unchanged visible subtree with lossless
source XML. Redrawing for compactness is allowed only while structure, meaning,
ownership, and a similar presentation remain intact.

### 2.2 Native Shape Payload and Authoring IR

| Representation | Purpose | Payload rule |
|---|---|---|
| Lossless import SVG | Immutable source/package evidence | Retain complete imported metadata, native object boundaries, hidden carriers, and source-scope identity for validation and supported non-visible payload recovery. Never copy its ordinary visible subtree into final templates. |
| Authoring IR bundle | Editable template-creation source | New compact SVG generated from parsed PPTX evidence. Omit opaque native payload and duplicate hidden carriers from model context; retain visible shape intent and stable document-local source refs. Models read `authoring_summary.json`; tools read `authoring_manifest.json` for source paths and initial hashes. |
| `standard` / `fidelity` output | Newly authored contract | Use editable basic primitives directly and `preset_shape_svg.py` compact canonical `<g>` output for exact preset matches. Keep faithful atoms independently composed when one contour is unnecessary; use `shape_boolean_svg.py` only where one compound closed contour must become an object, then allow a necessary freeform only if neither construction is faithful. Paint comes from the confirmed brief / `<design_spec_path>`. Reuse exported image/vector assets, not opaque source shape payload or source topology. |
| `mirror` output | Authored compact preservation contract | Publish the reviewed current authoring SVG, preserve validated structure/native facts, recover only supported non-visible semantics, and normalize fixed structural layers into semantic atoms. Strip IR-only source refs; never rehydrate ordinary visible source subtrees. |

**Validation**: Mirror does not silently use stale metadata. Materialization
validates source-document hashes, known refs, graph/assignment closure, and
classifies authoring subtree hashes; a changed subtree is a legitimate authored
edit, not permission to copy the old visible tree back. If an imported object
cannot use the converter's supported non-visible metadata after normalization,
keep its current SVG fallback and report the
limitation. For exact registered preset matches, `standard` / `fidelity`
regenerate the compact helper group instead of transplanting opaque source
payload; otherwise they keep faithful atoms independently composed unless one
contour requires the Boolean gate, with necessary freeform last.
`data-pptx-replace-with` remains reserved for optional PowerPoint-native
Chart/Table replacement markers.

**Explicit template SVG contract**:

| Authored/preserved fact | Template SVG declaration |
|---|---|
| Master/Layout identity | Root `data-pptx-master` / `data-pptx-master-name` plus `data-pptx-layout` / `data-pptx-layout-name`; authored keys for `standard` / `fidelity`, source keys for `mirror` |
| Authored Master/Layout visual | In `standard` / `fidelity`, use a direct atomic child with `data-pptx-layer="master|layout"` and `data-pptx-editable="false"`. An ordinary `<g>` is forbidden; one validated compact canonical authored-preset `<g>` is a semantic atom and is the sole group exception. |
| Preserved source Master/Layout visual | In `mirror`, author direct atoms with the same Master/Layout ownership and comparable paint order/presentation. Compact grouping, geometry, and style spelling may differ; semantic regrouping or ownership changes are forbidden. |
| Content slot | Direct `<g id>` with `data-pptx-placeholder` and explicit `data-pptx-bounds`; `standard` / `fidelity` author the slot, while `mirror` preserves source type/index/bounds and carrier identity |
| Page-only background | Direct full-canvas solid rect with `data-pptx-layer="slide"` |
| Structural page-frame hint | Optional `data-pptx-role` only when background/decoration/header/footer/logo/watermark/chrome/page-number behavior is not already expressed by layer/placeholder metadata; stable unique `id` required |

Repeat inherited visuals in every standalone SVG so browser preview remains complete. Template export validates their equality and materializes the declared Master/Layout parts. It does not infer ownership.

**Forbidden — legacy structure contract**: Do not carry `data-pptx-layout-kind`, `distilled`, `utility`, unmapped `baseline`, `preserve`, or direct atomic placeholders into a reusable template package. In `standard` / `fidelity`, treat such Type B inputs only as visual reference and author a complete current contract in a new workspace. Require the original PPTX Type A path when mirror must preserve existing native topology; see [`create-template`](../workflows/create-template.md).

**Composite slot boundary**: A normal slot group has exactly one compatible
direct carrier. A validated compact canonical authored-preset `<g>` counts as
one carrier for an `object` slot because it compiles to one native shape; an
ordinary multi-object `<g>` does not. Only a genuinely composite region may
declare `data-pptx-placeholder="object"` with
`data-pptx-binding="proxy"`; the visible group stays Slide-local
and export creates a hidden transparent binding proxy. Do not use proxy binding
as the default template slot form.

In `mirror`, preserve imported placeholder types, indices, bounds, and carrier
identity exactly when the importer supports them. Do not replace source
`subTitle`, `obj`, `media`, or `dt` roles with generic body content. In
`standard` / `fidelity`, assign the canonical authored types deliberately:
`title`, `subtitle`, `body`, `picture`, `chart`, `table`, `object`, `media`,
`date`, `footer`, and `slide-number`. An authored title normally has no index;
assign stable indices only when repeated roles need disambiguation inside the
new Layout.

**Hard rule — explicit design-zone bounds**: Every slot carries `data-pptx-bounds="x y width height"` with at most two decimals per value. Mirror uses the source Layout placeholder frame. `standard` / `fidelity` author bounds from the intended safe area, column, panel inset, or media frame. Do not use character count, glyph width, current wrapping, or the tight sample-content box. An authored Layout may intentionally have zero slots.

### 3. Placeholder Markers

> Mirror retains literal source example text and source placeholder metadata. It does not insert `{{...}}` markers. The rest of this section defines the preferred authoring vocabulary for standard and fidelity modes.

Use clear placeholder markers for replaceable content:

```xml
<!-- Text slot -->
<g id="title-slot" data-pptx-placeholder="title"
   data-pptx-bounds="80 280 1120 96">
  <text id="title-carrier" data-pptx-carrier="true"
        x="80" y="320" fill="#FFFFFF" font-size="48" font-weight="bold">
    {{TITLE}}
  </text>
</g>

<!-- Content area placeholder (content page only) -->
<rect x="40" y="90" width="1200" height="550" fill="#FFFFFF" rx="8"/>
<g id="body-slot" data-pptx-placeholder="body"
   data-pptx-bounds="40 90 1200 550">
  <text id="body-carrier" data-pptx-carrier="true"
        x="640" y="365" text-anchor="middle" fill="#CBD5E1" font-size="16">
    {{CONTENT_AREA}}
  </text>
</g>
```

### 4. Placeholder Reference (canonical convention, overridable per template)

This is the **default vocabulary** used across template packages. Newly created templates SHOULD prefer these names so downstream projects find familiar slots; designers MAY substitute or extend them when a style genuinely needs different vocabulary (e.g. consulting decks lead with `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`; a brand cover may need `{{BRAND_LOGO}}`).

`svg_quality_checker.py --template-mode --canonical-authoring` emits **advisory warnings** when a page lacks the conventional placeholder for its type. To silence those warnings — and document the template's actual contract — declare a `placeholders:` map in `<design_spec_path>` frontmatter:

```yaml
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LOGO}}"]
  03_content: ["{{KEY_MESSAGE}}", "{{CONTENT_AREA}}"]
  03a_content_dual_col: []   # explicitly assert "no required placeholders"
```

| Placeholder | Purpose | Applicable page | Convention role |
|------------|---------|-------------------|--------|
| `{{TITLE}}` | Main title | Cover | Default |
| `{{SUBTITLE}}` | Subtitle | Cover | Default |
| `{{DATE}}` | Date | Cover | Default |
| `{{AUTHOR}}` | Author / Organization | Cover | Default |
| `{{CHAPTER_NUM}}` | Chapter number | Chapter page | Default |
| `{{CHAPTER_TITLE}}` | Chapter title | Chapter page | Default |
| `{{CHAPTER_DESC}}` | Chapter description | Chapter page | Optional |
| `{{PAGE_TITLE}}` | Page title | Content page | Default |
| `{{CONTENT_AREA}}` | Content area | Content page | Default |
| `{{PAGE_NUM}}` | Page number | Content page, ending page | Default |
| `{{KEY_MESSAGE}}` | Key takeaway | Content page (consulting style) | Style-specific |
| `{{SECTION_NAME}}` | Section name | Content page footer | Optional |
| `{{SOURCE}}` | Data source | Content page footer | Optional |
| `{{THANK_YOU}}` | Thank-you message | Ending page | Default |
| `{{CONTACT_INFO}}` | Contact info | Ending page | Default |
| `{{ENDING_SUBTITLE}}` | Ending subtitle | Ending page | Optional |
| `{{CLOSING_MESSAGE}}` | Closing message | Ending page | Style-specific |
| `{{COPYRIGHT}}` | Copyright | Ending page | Optional |

For TOC pages in **newly created templates**, use indexed placeholders:

- `{{TOC_ITEM_1_TITLE}}`, `{{TOC_ITEM_1_DESC}}`
- `{{TOC_ITEM_2_TITLE}}`, `{{TOC_ITEM_2_DESC}}`
- ...

Do **not** create new TOC placeholder families such as `{{CHAPTER_01_TITLE}}` for new templates. Existing templates may contain legacy placeholder variants, but new output should converge on the indexed TOC contract.

Variants reuse their parent type's placeholder set by default: every `03*_content*.svg` shares the content placeholder list above, unless the spec frontmatter declares an override for that specific stem.

For `standard` / `fidelity`, canonical placeholder insertion takes priority over visual mimicry; adjust the newly designed layout or declare an intentional vocabulary override. Mirror preserves the source placeholders and literal text instead of inserting canonical authoring markers.

---

## Output Requirements

### File Save Location

Both scopes use one complete workspace shape. Only the workspace root differs:

| Scope | `<template_workspace>` |
|---|---|
| `library` | `skills/ppt-master/templates/<kind_dir>/<template_name>/` |
| `project` | `<target_project>/` |

Standard mode (default):

```
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   │   # project scope uses design_spec.<kind>.<id>.md instead
│   ├── 01_cover.svg
│   ├── 02_toc.svg              # Optional; without it: 02_chapter, 03_content, 04_ending
│   ├── 03_chapter.svg
│   ├── 04_content.svg
│   └── 05_ending.svg
├── images/                         # Optional; omit when unused
│   └── *.png / *.jpg           # SVG href is ../images/<name>
├── icons/                          # Optional; omit when unused
│   └── imported/
│       └── *.svg               # Canonical imported vectors, when used
└── exports/                        # Optional; requested review or required multi-Master evidence
    └── <deck_id|layout_id>_template_preview.pptx
```

Fidelity mode changes only the roster under `templates/`, e.g.:

```
<template_workspace>/templates/
├── design_spec.md              # project scope: design_spec.<kind>.<id>.md
├── 01_cover.svg
├── 02_toc.svg
├── 03a_chapter_full.svg
├── 03b_chapter_minimal.svg
├── 04a_content_two_col.svg
├── 04b_content_data_card.svg
├── 04c_content_quote.svg
├── 05_ending.svg
└── 06_section_break.svg
```

Mirror mode emits one SVG per source slide, named by source order:

```
<template_workspace>/templates/
├── design_spec.md              # project scope: design_spec.<kind>.<id>.md
├── 001_cover.svg
├── 002_toc.svg
├── 003_content.svg
├── 004_content.svg
├── 005_chapter.svg
├── 006_content.svg
├── ...
├── 049_content.svg
└── 050_ending.svg
```

Filenames preserve the source slide order via the 3-digit prefix; `<page_type>` is derived from `analysis/manifest.json` `pageTypeCandidates`. Source meaning and validated native structure facts are preserved while Template_Designer authors the compact new SVG; code/node identity is not required, and IR-only refs plus its manifest are not copied into template output.

**Hard rule — common routing**: Keep `<design_spec_path>`, template SVGs, and non-bitmap template-source assets in `templates/`; place every bitmap in `images/`; place each imported vector exactly once in `icons/imported/` and reference it as `data-icon="imported/<name>"`. Never create `templates/icons/`. Write a review deck to `exports/` when explicitly requested and always for a multi-Master package gate. Create Template must not create optional directories or placeholder files solely to retain empty paths. An initialized project may already contain empty scaffolding; leave it untouched and omit it from completion unless real template files were written or adopted there. Do not branch asset placement by output scope.

### Template Preview

When the user requests a PowerPoint review file or the validated roster declares multiple Masters, run `template_preview_pptx.py <template_workspace>` after SVG validation. The default review keeps visible SVG Chart/Table fallbacks. To verify JSON-first native capability, write a separately named review with `--native-charts-and-tables -o <distinct_path>`; marker presence alone never activates replacement. The command creates `exports/` on demand and verifies one slide per SVG prototype plus the expected Master/Layout counts. In authored modes, it shortens canonical marker text only in ephemeral review copies so prompts remain readable without changing the source SVG, carrier typography, or placeholder frames. The first export refuses a collision; an intentional post-fix replacement uses `--force`. The review PPTX is derived evidence and never a template-application input.

When a review deck was generated, include its path in the completion summary. Omit `exports/` only for an unrequested one-Master package.

If the template is based on PPTX import output, briefly note:
- which extracted assets were reused directly
- for `standard` / `fidelity`, which visual references influenced the newly authored roster
- for `mirror`, whether any source feature could not be preserved and the exact affected source object/page
- whether any page-type filename mapping required judgment beyond the import heuristic

---

## Using Pre-built Template Library (Optional)

If suitable template resources already exist, use them directly instead of generating new ones:

1. **Copy template workspace**: copy or stage `templates/` plus any existing `images/` and `icons/`; exclude `exports/` from template application.
2. **Adjust colors**: Modify colors per the project design spec
3. **Customize**: Make project-specific adjustments

This section describes downstream reuse of an existing workspace. Library and project scopes carry the same portable template contract.

**Example library structure** (query the appropriate kind's index — `templates/brands/brands_index.json` for identity, `templates/styles/styles_index.json` for roster-free direction/method, `templates/layouts/layouts_index.json` for brand-neutral structure, and `templates/decks/decks_index.json` for recurring applications with integrated identity/structure):

```
templates/
├── brands/
│   ├── anthropic/         # Anthropic brand identity (logo + colors + typography)
│   └── google/            # Google brand identity
├── styles/
│   └── <style_id>/         # Communication method and design direction; no SVG roster
├── layouts/
│   └── presentation_core/ # General structure system (no identity)
└── decks/
    ├── <bank_deck>/        # Example banking deck
    └── <engineering_deck>/ # Example engineering deck
```

---

## Phase Completion Checkpoint

```markdown
## Template_Designer Phase Complete

- [x] Read `references/template-designer.md`
- [x] Output scope confirmed: `library` | `project`; the common workspace preflight passed before final writes
- [x] Internal creation strategy derived from the confirmed natural-language intent: `standard` | `fidelity` | `mirror`; Layout mirror source is already brand-neutral and application-neutral
- [x] Every page listed in `<design_spec_path>` §V Page Roster saved to `<template_workspace>/templates/`
- [x] Naming convention applied (standard / fidelity: letter-suffix variants; mirror: `<NNN>_<page_type>.svg`)
- [x] Templates follow design spec (colors, fonts, layout)
- [x] Deck Template Overview and factual Page Roster describe the recurring application and actual prototypes without mandatory use policy; Layout output contains no application or identity contract
- [x] `standard` / `fidelity` inspected complete source Master/Layout evidence and represented each retained Layout through a newly authored Slide prototype; `mirror` SVGs preserve only source Slides and their reachable structure without semantic redesign
- [x] Placeholder markers are clear and standardized for `standard` / `fidelity`; preview-only sample text remains readable without changing source markers, while mirror preserves literal source text plus source placeholder type/index/bounds
- [x] Every SVG is a complete preview with explicit root Master/Layout identity and `native_structure_mode: structured`; authored modes use canonical fixed layers/slots, while mirror preserves source ownership and mechanically expands fixed-layer groups into direct atoms
- [x] Authored `standard` / `fidelity` Layout keys are non-duplicative; mirror keeps distinct reachable source Layout identities even when their current visible contracts are equivalent
- [x] Template creation used the authoring IR; lossless expanded imports remained immutable payload backing for mirror materialization, while `standard` / `fidelity` used helper-generated compact canonical preset groups and `<design_spec_path>` paint
- [x] Both scopes route bitmaps to `images/` and keep one canonical copy of every imported vector under `icons/imported/`
- [ ] **Next step**: Validate assets, export review evidence when requested or required for multiple Masters, then register only library scope
```
