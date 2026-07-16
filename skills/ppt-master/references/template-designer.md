> See shared-standards.md for common technical constraints.

# Template Designer — Template Design Role

## Core Mission

Generate reusable structured page templates inside the workspace selected by Create Template's Create Layout or Create Deck child workflow, and write a concise `design_spec.md` that captures the source-derived basic norms that make the template reusable.

> This is a standalone role: only triggered by the Create Layout or Create Deck child workflow under `/create-template`. Create Brand never invokes it. Library and project outputs use one workspace shape; this is not the template selection step in the main PPT generation pipeline.

## Usage

- **Trigger**: `/create-template` → Create Layout or Create Deck child workflow
- **Workspace root**: `library` (default) → `skills/ppt-master/templates/<kind_dir>/<template_name>/`; `project` → the confirmed `<target_project>/`
- **Template source**: `<template_workspace>/templates/` in both scopes
- **Input**: finalized template brief (output scope, target project when project-scoped, template ID, display name, kind, applicable scenarios, tone, theme mode, canvas format, optional reference assets, accepted basic template norms)

**Hard rule — scope is execution metadata**: Use `output_scope` and `target_project` to route files, but do not write either field into portable `design_spec.md` frontmatter. Do not create a new PPTX structure mode; deck/layout output declares `native_structure_mode: structured`.

**Workspace precondition**: The workflow has already resolved the selected root, confirmed an empty `<template_workspace>/templates/`, and checked collision-free destination filenames in `images/` and `icons/imported/`. Check `exports/` when review was requested or the confirmed roster contains multiple Masters. Optional directories may be absent until their first real file is written. Project scope additionally requires an initialized target project. Do not begin final writes before that all-at-once preflight passes.

When the workflow provides a PPTX reference source, the effective input package comes from the unified `pptx_template_import.py` preparation workspace and becomes:

- finalized template brief
- `manifest.json` — single source of truth for source-deck facts (slide size, theme, per-master themes, assets, asset map, placeholders, layouts, masters, slides, SVG file paths, page-type candidates)
- `native_structure.json` — stable source master/layout keys, picker names, parent-master relationships, placeholder type/index/geometry, source hash, and source-graph quality facts
- `source_template.pptx` — byte-preserved analysis copy for visual/package cross-checking; never a final template asset
- `conversion-report.json` — source-recovery and fidelity diagnostics, when present
- exported `assets/`
- `svg/master_*.svg` / `svg/layout_*.svg` — immutable layered native-payload backing; every master / layout in the deck rendered once, including ones no sample slide references
- `svg/slide_NN.svg` — immutable slide-local native-payload backing; do not bulk-read because opaque native payload is retained
- `svg/inheritance.json` — which layout / master each slide consumes
- optional `svg-flat/slide_NN.svg` — immutable complete-page verification backing generated only when explicitly requested; do not use it as the editable source
- `authoring-svg/` and optional `authoring-svg-flat/` — lightweight non-destructive IR bundles created by `svg_authoring_view.py`; each contains editable SVGs, model-readable `authoring_summary.json`, and tool-only `authoring_manifest.json`
- optional screenshots for visual cross-checking

PPTX import interpretation:

- Placeholder guides in master / layout SVGs are layout signals. Use `manifest.json` placeholder records for type / index / geometry / base style; do not copy dashed guide boxes into final templates unless the visual design truly uses dashed boxes.
- Charts, SmartArt, diagrams, and OLE objects may appear as typed placeholders in layered SVGs. In flat SVGs they may show preview images. Treat them as source intent markers, not reusable decorative assets.
- The asset filenames referenced by SVGs are governed by the manifest asset map. Prefer those references over inventing duplicate asset names.

Input priority for PPTX-backed template creation depends on replication mode:

| Mode | Authoritative inputs | Model-facing inputs |
|---|---|---|
| `standard` / `fidelity` | Finalized brief for the newly designed output; `manifest.json` for factual canvas/theme/assets | `authoring-svg/authoring_summary.json`, layered authoring SVGs, optional flat spot checks, and exported assets as visual references. Do not read `authoring_manifest.json`. Source Master/Layout topology is informational only and is not mined into output structure. |
| `mirror` | `manifest.json`, `native_structure.json`, and `svg/inheritance.json`; the compiler validates the tool-only authoring manifest | `authoring-svg/authoring_summary.json` plus layered authoring SVGs as the editable preservation IR; optional `authoring-svg-flat/` for complete-page verification; matching lossless `svg/` and optional `svg-flat/` only as immutable backing. |

Use the compact facts in `manifest.json` for orientation. Open screenshots or the original PPTX only for visual cross-checking.

**Native structure output**: Always set `native_structure_mode: structured`.

| Mode | Output structure contract |
|---|---|
| `standard` / `fidelity` | Author project-canonical SVG prototypes and an intentional new Master/Layout/slot system. Source visual language and assets may guide the design, but source ownership, keys, picker names, parent relationships, placeholders, and repeated Slide-local elements do not define or seed the output topology. Use the compact authored-preset group only for exact registered preset matches. |
| `mirror` | Materialize a new workspace from the validated source graph one-to-one: keep the Master/Layout identities and parentage, slide assignments, placeholder type/index/bounds, and supported visual/native-object facts that are actually present. Edit the authoring IR; materialization may rehydrate converter-supported native payload only for unchanged source refs. Mechanical normalization maps fixed-layer source groups into the direct atoms required by the current explicit SVG contract while preserving ownership, paint order, and appearance; it must not invent missing facts or semantically redesign the graph. |

Every page remains a complete standalone SVG preview.

**Authored preset rule**: In `standard` / `fidelity`, when one registered
PowerPoint preset exactly expresses one complete object, use
`preset_shape_svg.py` as defined by
[`native-shape-authoring.md`](./native-shape-authoring.md). Its compact
canonical `<g>` is one semantic atom after validation: it may remain
Slide-local, serve as the one direct carrier of an `object` slot, or carry
Master/Layout fixed-layer ownership. This is the only `<g>` exception to the
fixed-layer atomicity rule; ordinary groups remain forbidden there. Preset
paint comes from the confirmed brief and this template's `design_spec.md`
color scheme. Do not copy an expanded import carrier/preview/fingerprint
bundle into an authored template. `mirror` instead preserves the supported
expanded lossless source representation. The exact syntax and validation
contract remain owned by
[`shared-standards.md`](./shared-standards.md) and the native-shape reference.

**Hard rule — complete mirror graph**: Preserve every supported source Layout represented by the validated import,
including Layouts unused by source Slides. Emit one complete source-page
prototype per source Slide and one definition-only
`layout_<layout_key>.svg` prototype for each otherwise unrepresented Layout.
The definition prototype carries the exact parent Master identity, Layout
identity, fixed atoms, and placeholder contract but is not a generated page.
This also retains a source Master that is reachable only through unused Layouts.
Never silently drop or merge an identity, and never invent a carrier page.

**Hard rule — no duplicate authored Layout contracts**: In `standard` / `fidelity`, distinct output Layout keys must differ in fixed Layout atoms or slot topology/type/index/bounds/binding. Topic, sample wording, or Slide-local content alone never justifies another authored key. Mirror keeps source Layout identities even when two source contracts are visibly equivalent.

**Downstream boundary**: The Strategist confirmation stage selects `strict` or `adaptive` when a project consumes this package. Both export through `pptx_structure.mode: structured`. Strict keeps the referenced Layout contract; adaptive may create a new Layout identity while retaining the template Master. Template_Designer does not preselect that project-level choice.

For `mirror`, `design_spec.md §V` must be followed by a `Source Preservation Map` that records each source slide's Master/Layout assignment and output file. The map is evidence of one-to-one preservation, not a design-decision log. `standard` and `fidelity` record only their newly authored output roster and structure; do not add a source-topology disposition table.

---

## Page Roster

The output page set is determined by **replication mode**, declared in the finalized template brief:

| Mode | When to use | Roster |
|------|-------------|--------|
| `standard` (default) | Most templates — clean, reusable, compact coverage driven by the confirmed brief | Cover, chapter, ending, optional TOC, and one or a small explicitly required set of distinct content Layouts; typically 4–6 prototypes |
| `fidelity` | User wants a broader, source-aligned but newly designed template | Canonical roles plus intentionally designed variants that cover the useful source composition range |
| `mirror` | User wants a new template workspace that preserves validated native source facts | One SVG prototype materialized from the authoring IR per source slide, named `<NNN>_<page_type>.svg` by source order |

**Hard rule — mode controls authorship**: `standard` and `fidelity` create new SVG documents and their own Master/Layout system. `mirror` maps the validated imported source contract into a new workspace and must not reauthor, distill, reinterpret, or supplement its structure.

### Standard mode

| # | Filename | Purpose | Description |
|---|----------|---------|-------------|
| 01 | `01_cover.svg` | Cover | Fixed structure: title, subtitle, date, organization |
| 02 | `02_chapter.svg` | Chapter page | Fixed structure: chapter number, chapter title |
| 03 | `03_content.svg` | Content page | Flexible structure: only defines header/footer; content area freely laid out by AI |
| 04 | `04_ending.svg` | Ending page | Fixed structure: thank-you message, contact info |
| -- | `02_toc.svg` | Table of contents | Optional: TOC title, chapter list (number + title) |

**Design philosophy**: Templates define visual consistency and structural pages; content pages maintain maximum flexibility.

**Confirmed compact variants**: `standard` may include more than one Layout for the same canonical role when the user brief explicitly requires genuinely different reusable structures, such as two-column evidence and three-card KPI content. Keep the roster compact and brief-driven rather than mining the source page set. When siblings exist, suffix every sibling (`03a_content_two_col.svg`, `03b_content_three_card.svg`) instead of treating one arbitrary variant as the unsuffixed default. This does not require `fidelity`; use `fidelity` when the broader roster is derived from complete PPTX/SVG page evidence.

**Naming note**: The numeric prefix is the template's own presentation order. Its base sequence stays contiguous; sibling variants share their parent's number only through unique lowercase suffixes such as `03a` / `03b`. When the optional TOC page is included it takes `02_toc.svg` and the later types shift by one: `01_cover`, `02_toc`, `03_chapter`, `04_content`, `05_ending`. Numbers carry no meaning across templates — tooling derives the page type from the token after the underscore, so both spellings of each type are equivalent.

### Fidelity mode

When the brief sets `Replication mode: fidelity`, design a broader reusable roster that stays close to the source's visual language and useful composition examples. The output Master/Layout system is authored independently from source topology.

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
- Record every emitted page in `design_spec.md §V Page Roster`; in library scope, `register_template.py` generates the corresponding index entry from `<template_workspace>/templates/*.svg`. Project scope skips registration

> Variants reuse the parent type's placeholder set — see §4 (Placeholder Reference) below.

### Mirror mode

When the brief sets `Replication mode: mirror`, materialize a new template workspace from validated imported facts rather than designing a new system:

- Model-facing authoring source: `authoring-svg/authoring_summary.json`, layered `authoring-svg/*.svg`, `svg/inheritance.json`, and `native_structure.json`. Do not read `authoring-svg/authoring_manifest.json`; materialization validates it internally. When present, use `authoring-svg-flat/` only for full-page verification. Matching lossless `svg/` and optional `svg-flat/` files are immutable backing; materialization resolves only the layered backing.
- Precondition: the import evidence identifies every source Master/Layout, parent relationship, picker name, placeholder contract, and fixed visual layer. Stop only when required facts or supported geometry are missing; unused identities are not a stop condition.
- Output: `<template_workspace>/templates/<NNN>_<page_type>.svg` for every source slide, plus `layout_<layout_key>.svg` for every source Layout unused by all source slides. `<NNN>` is the zero-padded source slide index (3 digits) and `<page_type>` is derived from `manifest.json` `pageTypeCandidates` — `cover` / `toc` / `chapter` / `content` / `ending`. When the page-type heuristic is ambiguous, fall back to `content`. Preserve source slide order via the numeric prefix; definition-only files are not generated pages.
- Required preservation: preserve source Master/Layout keys and picker names, Layout-to-Master parentage, slide assignments, placeholder type/index/bounds, supported native-object metadata, geometry, decoration, sprite-sheet wrappers, original example text, chart previews, fonts, effects, and paint order whenever the importer represents them.
- Allowed normalization: add or normalize explicit root declarations and asset paths, and recursively expand fixed Master/Layout group wrappers into direct atoms. The mapping must remain one-to-one at the ownership level and must not change paint order or appearance.
- Forbidden: commonality extraction, semantic synthesis, merging, splitting, promotion, demotion, renaming, re-parenting, decorative simplification, placeholder invention, or replacement of supported source-native metadata / SVG fallback with a model-authored approximation.
- `design_spec.md` §V Page Roster lists every emitted file and marks definition-only prototypes explicitly. `Source Preservation Map` records each source-slide assignment plus every unused Layout definition and its parent Master.

**Mirror consumption boundary**: `mirror` applies only while creating the template package from the source deck. Once created, the package is consumed as an ordinary deck / layout template roster: downstream generation may select, repeat, skip, reorder, or adapt pages according to the new content. The `replication_mode: mirror` field must not force the generated deck to preserve the source page count, source order, or one-output-slide-per-template-slide mapping.

**What mirror is not**: a redesign, topology-cleanup, or recovery mode. It may mechanically transcode the imported representation into the current explicit SVG/package contract, so byte identity is not promised. Charts, SmartArt, OLE objects, and EMF / WMF media that fail to round-trip in `pptx_template_import.py` will fail the same way in mirror. If the import workspace has missing media or unsupported objects, mirror inherits those gaps — report them before materialization begins.

---

## Template Design Specifications

### 1. Must Generate design_spec.md

**Scope rule — personality only.** A deck `design_spec.md` describes the identity and structure that make the complete template recognizable. A layout spec describes only its distinctive reusable structure. Neither restates generic constraints — those live in the canonical references and are already loaded by every downstream role:

- General SVG required / forbidden / conditional interfaces → [`shared-standards.md`](shared-standards.md)
- Generic layout pattern library, spacing bands, font-size ratio bands → [`templates/design_spec_reference.md`](../templates/design_spec_reference.md) (read by Strategist when authoring the **project** design_spec)
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
summary: <one-line tone & use case>
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
- Use cases, design tone, theme mode (light / dark / mixed)
- One paragraph: what visually identifies this template at a glance

## II. Color Scheme
- HEX values with role labels (primary / accent / background / text / etc.)
- Brand-specific application rules when present (e.g. "KPI cards rotate blue→green→red→yellow")

## III. Typography (omit when using the default `Arial, "Microsoft YaHei", sans-serif` stack)
- Per-role font stacks ONLY when the template intentionally diverges (display serif title, brand typeface, etc.)
- Font-install or embedding requirement when a non-preinstalled font leads any stack
- Body baseline px (informational; `spec_lock.md` owns the actual values per project)

## IV. Signature Design Elements
- Decorative motifs that ARE this template — top bar, gradient underline, logo treatment, brand emblem placement
- Source-derived layout grammar — grid / column rhythm, page chrome, image zones, mask / crop behavior, overlay treatment, and density rhythm that make the template recognizable
- Optional XML snippet for any reusable component unique to this template

## V. Page Roster
One row per emitted SVG describing what this template's version of cover / chapter / content / ending looks like (background treatment, decorative anchors, layout rhythm, image behavior, content density, intended content slot). For `standard` / `fidelity`, record the newly authored Layout key and PowerPoint picker name. For `mirror`, record the preserved source Master/Layout keys and picker names without redesigning them. Roster entries must match the actual SVG files on disk.

For `mirror`, add `### Source Preservation Map` immediately after the roster with columns `Source slide`, `Source Master`, `Source Layout`, `Output SVG`, and `Preservation status`. This is a one-to-one mapping record. Do not add synthesis rationale or source-structure disposition rows to `standard` / `fidelity` templates.

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
- Structure-specific grid, zones, page chrome, image behavior, density rhythm, and slot conventions
- Neutral preview paint may expose hierarchy, but it is not a color or typography identity

## V. Page Roster
One row per emitted SVG with Layout key, picker name, intended content, and slot behavior. Roster entries must match the actual files on disk.

For `mirror`, append the same `### Source Preservation Map` required above.

## VII. Placeholder Overrides (omit when none)
Reference the `placeholders:` frontmatter declaration and explain the structural vocabulary deviation.
```

**Layout boundary**: Omit Template Overview, Color Scheme, Typography, Logo,
Voice & Tone, and Icon Style. The frontmatter `summary` carries concise
selection context; the deck-only Template Overview remains the middle segment
used during fusion.

Sections to **omit** from template `design_spec.md` (sourced elsewhere — listing them here is noise):

| Don't write | Source |
|---|---|
| General SVG technical / compatibility rules | `shared-standards.md` |
| Generic layout pattern library (centered card / three-column / timeline / …) | `design_spec_reference.md` §V |
| Generic spacing bands (margin 40-60px, card gap 20-32px, etc.) | `design_spec_reference.md` §V |
| Generic font-size hierarchy (cover 2.5-5x body, page title 1.5-2x, …) | `design_spec_reference.md` §IV |
| Canonical placeholder table (`{{TITLE}}`, `{{PAGE_NUM}}`, …) | §4 below |
| Content methodology (pyramid / SCQA / MECE) | `strategist.md` |
| "Usage Instructions" boilerplate (copy template / select page / …) | `create-template.md` |
| Created Date / Page Count rows | not a library-level field |

When rewriting an existing template that contains an omitted generic section,
delete it rather than leaving a pointer. Keep a template-specific boundary only
inside the personality section it qualifies (asset system, motif, image
treatment, or page roster); do not preserve a generic technical-rules heading.

### 2. Inherit Design Specification

Templates must strictly follow the finalized template brief and the generated `design_spec.md`:
- **Canvas dimensions**: `canvas_format` is not enough; root SVG `viewBox` matches `canvas_viewbox` in the design spec. Root `width` / `height` are optional compatibility attributes and are not PPT Master canvas authority.
- **Source canvas**: when a PPTX/SVG reference is used, record `source_canvas_width`, `source_canvas_height`, and `source_viewbox`. If the output canvas differs from the source, normalize all geometry, typography, line heights, strokes, and image crop coordinates explicitly instead of relying on the shared aspect ratio.
- **Color scheme**: Uses primary, secondary, and accent colors from the spec
- **Font plan**: Uses the per-role font families declared in the spec
- **Layout principles**: Margins and spacing conform to the spec
- **Image system**: Image placement, crop / mask behavior, full-bleed zones, and overlay rules follow the source-derived norms in the spec

If PPTX import output exists:
- Prefer imported theme colors and fonts over visually guessed values
- Reuse exported `assets/` images directly — `<image>` references in `svg/` already point at canonical files
- Treat page-type candidates from `manifest.pageTypeCandidates` as hints, not guarantees

**Precondition**:

- For `standard`, inspect enough lightweight complete-page IR documents to understand the requested visual direction and reusable assets; do not analyze source topology.
- For `fidelity`, inspect every lightweight complete-page IR document so the newly designed roster covers the useful source composition range; do not derive output ownership from source Master/Layout recurrence.
- For `mirror`, verify every authoring Master, Layout, and Slide listed by `authoring_summary.json` against `native_structure.json` and `svg/inheritance.json`, then materialize from the IR with matching lossless payload backing. The compiler validates each machine-manifest record. Before materialization begins, report the verified source slide indexes.

### 2.1 PPTX Import Mode Rule

The imported PPTX has a different authority level in each replication mode.

| Mode | Required behavior |
|---|---|
| `standard` | Use source visuals/assets as references, then author the project-canonical roster and its Master/Layout/slot structure from the confirmed brief. Do not preserve or distill source topology. |
| `fidelity` | Use the complete visual roster as design reference, then author a broader canonical roster and its own Master/Layout/slot structure. Match the source visual language closely, but do not cluster, merge, or split source Layouts into output families. |
| `mirror` | Preserve validated source pages, inheritance, placeholders, native objects, and visuals from the lossless import while creating a new workspace. Do not simplify, redesign, rename structure, infer new common structure, or fill gaps. |

**Hard rule — mirror materialization is mechanical**: Mirror may normalize namespaces,
portable asset paths, explicit root declarations, and fixed-layer group wrappers
required by the current compiler. Expanding a source Master/Layout group must
produce direct atoms with the same ownership, transforms, paint order, and
appearance. A maintainability preference is not authority to alter the source
template.

### 2.2 Native Shape Payload and Authoring IR

| Representation | Purpose | Payload rule |
|---|---|---|
| Lossless import SVG | Native-payload backing | Retain complete imported metadata, native object boundaries, hidden carriers, and source-scope identity. Keep it immutable and resolve it only through validated source refs. |
| Authoring IR bundle | Editable template-creation source | Omit opaque native payload and duplicate hidden carriers from model context; retain visible shape intent and stable document-local source refs. Models read `authoring_summary.json`; tools read `authoring_manifest.json` for source paths and initial hashes. |
| `standard` / `fidelity` output | Newly authored contract | Use `preset_shape_svg.py` compact canonical `<g>` output for exact preset matches, with paint from the confirmed brief / `design_spec.md`; use ordinary project SVG for other geometry. Reuse exported image/vector assets, not opaque source shape payload or source topology. |
| `mirror` output | Materialized preserved contract | Preserve currently supported imported metadata on unchanged Slide-local/slot refs, use the edited SVG fallback otherwise, and normalize fixed structural layers into semantic atoms. Strip IR-only source refs from final templates. |

**Validation**: Mirror does not silently use stale metadata. Materialization
validates source-document hashes and each referenced object's initial authoring
hash before reusing native payload. If an imported object cannot use the
converter's supported native metadata after normalization, keep its current SVG fallback and report the
limitation. For exact registered preset matches, `standard` / `fidelity`
regenerate the compact helper group instead of transplanting opaque source
payload; other geometry stays ordinary project SVG. `data-pptx-replace-with` remains
reserved for optional PowerPoint-native Chart/Table replacement markers.

**Explicit template SVG contract**:

| Authored/preserved fact | Template SVG declaration |
|---|---|
| Master/Layout identity | Root `data-pptx-master` / `data-pptx-master-name` plus `data-pptx-layout` / `data-pptx-layout-name`; authored keys for `standard` / `fidelity`, source keys for `mirror` |
| Authored Master/Layout visual | In `standard` / `fidelity`, use a direct atomic child with `data-pptx-layer="master|layout"` and `data-pptx-editable="false"`. An ordinary `<g>` is forbidden; one validated compact canonical authored-preset `<g>` is a semantic atom and is the sole group exception. |
| Preserved source Master/Layout visual | In `mirror`, recursively expand each fixed-layer source group into direct atoms with the same Master/Layout ownership, transforms, styles, paint order, and appearance; semantic regrouping is forbidden |
| Content slot | Direct `<g id>` with `data-pptx-placeholder` and explicit `data-pptx-placeholder-bounds`; `standard` / `fidelity` author the slot, while `mirror` preserves source type/index/bounds and carrier identity |
| Page-only background | Direct full-canvas solid rect with `data-pptx-layer="slide"` |
| Structural page-frame hint | Optional `data-pptx-role` only when background/decoration/header/footer/logo/watermark/chrome/page-number behavior is not already expressed by layer/placeholder metadata; stable unique `id` required |

Repeat inherited visuals in every standalone SVG so browser preview remains complete. Template export validates their equality and materializes the declared Master/Layout parts. It does not infer ownership.

**Forbidden — legacy structure contract**: Do not carry `data-pptx-layout-kind`, `distilled`, `utility`, unmapped `baseline`, `preserve`, or direct atomic placeholders into a reusable template package. In `standard` / `fidelity`, treat such Type B inputs only as visual reference and author a complete current contract in a new workspace. Require the original PPTX Type A path when mirror must preserve existing native topology; see [`create-template`](../workflows/create-template.md).

**Composite slot boundary**: A normal slot group has exactly one compatible
direct carrier. A validated compact canonical authored-preset `<g>` counts as
one carrier for an `object` slot because it compiles to one native shape; an
ordinary multi-object `<g>` does not. Only a genuinely composite region may
declare `data-pptx-placeholder="object"` with
`data-pptx-placeholder-binding="proxy"`; the visible group stays Slide-local
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

**Hard rule — explicit design-zone bounds**: Every slot carries `data-pptx-placeholder-bounds="x y width height"`. Mirror uses the source Layout placeholder frame. `standard` / `fidelity` author bounds from the intended safe area, column, panel inset, or media frame. Do not use character count, glyph width, current wrapping, or the tight sample-content box. An authored Layout may intentionally have zero slots.

### 3. Placeholder Markers

> Mirror retains literal source example text and source placeholder metadata. It does not insert `{{...}}` markers. The rest of this section defines the preferred authoring vocabulary for standard and fidelity modes.

Use clear placeholder markers for replaceable content:

```xml
<!-- Text slot -->
<g id="title-slot" data-pptx-placeholder="title"
   data-pptx-placeholder-bounds="80 280 1120 96">
  <text id="title-carrier" data-pptx-placeholder-carrier="true"
        x="80" y="320" fill="#FFFFFF" font-size="48" font-weight="bold">
    {{TITLE}}
  </text>
</g>

<!-- Content area placeholder (content page only) -->
<rect x="40" y="90" width="1200" height="550" fill="#FFFFFF" rx="8"/>
<g id="body-slot" data-pptx-placeholder="body"
   data-pptx-placeholder-bounds="40 90 1200 550">
  <text id="body-carrier" data-pptx-placeholder-carrier="true"
        x="640" y="365" text-anchor="middle" fill="#CBD5E1" font-size="16">
    {{CONTENT_AREA}}
  </text>
</g>
```

### 4. Placeholder Reference (canonical convention, overridable per template)

This is the **default vocabulary** used across template packages. Newly created templates SHOULD prefer these names so downstream projects find familiar slots; designers MAY substitute or extend them when a style genuinely needs different vocabulary (e.g. consulting decks lead with `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`; a brand cover may need `{{BRAND_LOGO}}`).

`svg_quality_checker.py --template-mode` emits **advisory warnings** when a page lacks the conventional placeholder for its type. To silence those warnings — and document the template's actual contract — declare a `placeholders:` map in `design_spec.md` frontmatter:

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
├── design_spec.md
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
├── design_spec.md
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

Filenames preserve the source slide order via the 3-digit prefix; `<page_type>` is derived from `manifest.json` `pageTypeCandidates`. Literal source text and validated native structure facts are preserved when the authoring IR is materialized into the new workspace; IR-only refs and its manifest are not copied into the template output.

**Hard rule — common routing**: Keep `design_spec.md`, template SVGs, and non-bitmap template-source assets in `templates/`; place every bitmap in `images/`; place each imported vector exactly once in `icons/imported/` and reference it as `data-icon="imported/<name>"`. Never create `templates/icons/`. Write a review deck to `exports/` when explicitly requested and always for a multi-Master package gate. Create Template must not create optional directories or placeholder files solely to retain empty paths. An initialized project may already contain empty scaffolding; leave it untouched and omit it from completion unless real template files were written or adopted there. Do not branch asset placement by output scope.

### Template Preview

When the user requests a PowerPoint review file or the validated roster declares multiple Masters, run `template_preview_pptx.py <template_workspace>` after SVG validation. The command creates `exports/` on demand and verifies one slide per SVG prototype plus the expected Master/Layout counts. In authored modes, it shortens canonical marker text only in ephemeral review copies so prompts remain readable without changing the source SVG, carrier typography, or placeholder frames. The first export refuses a collision; an intentional post-fix replacement uses `--force`. The review PPTX is derived evidence and never a template-application input.

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

**Example library structure** (query the appropriate kind's index — `templates/layouts/layouts_index.json` for structure-only templates, `templates/decks/decks_index.json` for complete identity + structure templates, `templates/brands/brands_index.json` for identity-only presets):

```
templates/
├── brands/
│   ├── anthropic/         # Anthropic brand identity (logo + colors + typography)
│   └── google/            # Google brand identity
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
- [x] Replication mode confirmed: `standard` | `fidelity` | `mirror`
- [x] Every page listed in `design_spec.md §V Page Roster` saved to `<template_workspace>/templates/`
- [x] Naming convention applied (standard / fidelity: letter-suffix variants; mirror: `<NNN>_<page_type>.svg`)
- [x] Templates follow design spec (colors, fonts, layout)
- [x] `standard` / `fidelity` SVGs and Master/Layout contracts were newly authored; `mirror` SVGs were materialized from the authoring IR while preserving the source graph without semantic redesign
- [x] Placeholder markers are clear and standardized for `standard` / `fidelity`; preview-only sample text remains readable without changing source markers, while mirror preserves literal source text plus source placeholder type/index/bounds
- [x] Every SVG is a complete preview with explicit root Master/Layout identity and `native_structure_mode: structured`; authored modes use canonical fixed layers/slots, while mirror preserves source ownership and mechanically expands fixed-layer groups into direct atoms
- [x] Authored `standard` / `fidelity` Layout keys are non-duplicative; mirror keeps distinct source Layout identities even when their current visible contracts are equivalent
- [x] Template creation used the authoring IR; lossless expanded imports remained immutable payload backing for mirror materialization, while `standard` / `fidelity` used helper-generated compact canonical preset groups and `design_spec.md` paint
- [x] Both scopes route bitmaps to `images/` and keep one canonical copy of every imported vector under `icons/imported/`
- [ ] **Next step**: Validate assets, export review evidence when requested or required for multiple Masters, then register only library scope
```
