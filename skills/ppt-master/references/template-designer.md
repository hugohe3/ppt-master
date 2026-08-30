> See [`shared-standards-core.md`](./shared-standards-core.md) for common technical constraints.

# Template Designer — Template Design Role

## Core Mission

Generate reusable structured page templates inside the workspace selected by Create Template's Create Layout or Create Deck child, and write the Design Spec that captures the source-derived rules making the template reusable — for Deck with descriptive recurring-application context, for Layout brand-neutral and application-neutral. A standalone role triggered only by those two children; Create Brand never invokes it, and this is not the template-selection step of the main pipeline.

## Usage

- **Workspace root**: `library` → `skills/ppt-master/templates/<kind_dir>/<template_name>/`; `project` → the confirmed `<target_project>/`; template source is `<template_workspace>/templates/` in both; the Design Spec is the parent-resolved `<design_spec_path>` (library `templates/design_spec.md`, project `templates/design_spec.<kind>.<id>.md`).
- **Input**: the finalized brief (scope, target project, template ID, display name, kind, structural use cases or Deck application context, tone, theme mode, canvas, optional reference assets, accepted norms) plus, for a PPTX reference, the import workspace described in [`template-tools.md`](../scripts/docs/template-tools.md) — `analysis/manifest.json`, `analysis/native_structure.json`, `sources/source.pptx` (never a template asset), `validation/conversion-report.json`, exported resources, immutable `svg/` layered backing and `svg/inheritance.json`, optional `svg-flat/`, and the editable `authoring-svg/` bundle with model-readable `authoring_summary.json` and tool-only `authoring_manifest.json`.

**Hard rule — scope is execution metadata**: route files by `output_scope` / `target_project` but never write them into frontmatter. Deck/layout output always declares `native_structure_mode: structured`; never invent another structure mode.

**Workspace precondition**: the parent has resolved `<design_spec_path>` and checked all destinations (library `templates/` empty; the authoring root free of a bare spec, selected-kind spec, or roster; collision-free `images/`, `icons/imported/`, `exports/`; an isolated project-shaped root supplied when the other structural kind exists). Never begin final writes before that preflight passes.

**PPTX import interpretation**: placeholder guides in master/layout SVGs are layout signals — use manifest placeholder records for type/index/geometry/base style and copy no dashed boxes unless the design uses them; charts, SmartArt, diagrams, and OLE objects are source intent markers, not reusable decoration; asset filenames follow the manifest map. Use manifest facts for orientation; open screenshots or the PPTX only for visual cross-checking.

| Mode | Authoritative inputs | Model-facing inputs |
|---|---|---|
| `standard` / `fidelity` | The brief for the newly designed output; `analysis/manifest.json` for canvas/theme/resources | `authoring_summary.json`, every layered source Master/Layout as structural and visual evidence, layered Slides, optional flat spot checks, exported resources — never `authoring_manifest.json`. `standard` authors a compact result, `fidelity` broader source-aligned coverage; neither copies source identities merely because they exist |
| `mirror` | Inline native Chart/Table JSON plus `manifest.json`, `native_structure.json`, `svg/inheritance.json`; the publisher validates the tool-only manifest | `authoring_summary.json` plus every reachable layered compact SVG as the editable source; optional `authoring-svg-flat/` for verification; lossless `svg/` only for validation and non-visible payload recovery, never visible-subtree copying |

**Mandatory — authored construction bundle**: as soon as `replication_mode` resolves to `standard` or `fidelity`, and before selecting any contour, read [`native-shape-authoring.md`](./native-shape-authoring.md) and [`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md) completely; never load them for `mirror`.

**Hard rule — native objects are compiled output**: Theme, Master, Layout, and Placeholder are PowerPoint implementation objects, not template kinds. Layout owns topology, placement, semantic text roles, and spatial text behavior; Deck identity owns paint, typeface identity, and fixed identity assets, with application context describing the recurring family. Downstream `layout` scope resolves placeholder formatting from the Layout roles plus confirmed identity, reading mode, and type scale; `mirror` scope preserves source structure and comparable presentation in compact SVG. Compile the rules into one native graph without merging ownership.

| Mode | Output structure contract |
|---|---|
| `standard` / `fidelity` | Review the complete source Master/Layout inventory, then author complete Slide SVG prototypes and an intentional new Master/Layout/slot system; every retained Layout has at least one prototype; `standard` stays compact, `fidelity` retains broader useful families; source identities never define output topology. Choose page-fit contours from the full native vocabulary before their authoring forms: exact native atoms independent, a Boolean result only where one contour requires it, freeform last |
| `mirror` | Review and author one complete compact SVG per validated source Slide with only its referenced Layout and parent Master, keeping reachable identities, parentage, assignment, placeholder facts, inline JSON authority, and meaning; presentation recognizably similar, nodes and code not isomorphic; publication completes inherited context and maps fixed-layer groups into direct atoms without inventing facts |

Every output is a complete standalone Slide preview resolving Master + Layout + Slide context with explicit layer markers; standalone Master/Layout definition SVGs are not template artifacts.

**Authored preset rule**: in `standard` / `fidelity`, when one registered preset exactly expresses one complete object, use `preset_shape_svg.py` per [`native-shape-authoring.md`](./native-shape-authoring.md); its compact canonical `<g>` is one semantic atom after validation — Slide-local, the one carrier of an `object` slot, or a Master/Layout fixed layer — and the only `<g>` exception to fixed-layer atomicity. Paint comes from the brief and spec color scheme. Never copy an expanded import carrier/preview/fingerprint bundle into an authored template; `mirror` authors from the compact parsed SVG and never transplants the lossless subtree. When one preset is insufficient, apply the same reference's compound-page gate. Syntax and validation are owned by `shared-standards-core.md` and the native-shape reference.

**Hard rule — reachable mirror graph**: exactly one prototype per source Slide, preserving only the transitive `Slide → Layout → Master` chain; identities outside that closure produce no SVG (re-author useful ones through `standard` / `fidelity`).

**Hard rule — no duplicate authored Layout contracts**: distinct authored keys differ in fixed atoms or slot topology/type/index/bounds/binding; topic, sample wording, or Slide-local content never justifies another key. Mirror keeps distinct reachable source identities even when visibly equivalent.

**Downstream boundary**: Stage 1 independently confirms the communication contract; Strategist inspects the installed prototypes, Deck context, and content, authors one application plan, and records `mirror` / `layout` / `style` and `strict` / `adaptive` only as internal exporter values. Template_Designer never preselects that plan. For `mirror`, `§V` is followed by a `Source Preservation Map` (each Slide's retained Master/Layout assignment and output file, one optional sentence for unmaterialized identities); authored modes record only their new roster.

---

## Page Roster

| Mode | When | Roster |
|------|------|--------|
| `standard` (default) | A clean, reusable, compact system | Cover, chapter, ending, optional TOC, and one or a small required set of distinct content Layouts; typically 4–6 prototypes |
| `fidelity` | Broader, source-aligned but newly designed coverage | Canonical roles plus intentionally designed variants covering the useful source composition range |
| `mirror` | Preserving validated native source facts and a similar presentation | One compact prototype per source slide, `<NNN>_<page_type>.svg` in source order |

**Hard rule — mode controls authorship**: `standard` / `fidelity` inspect the complete source but create new SVGs and their own Master/Layout system; `mirror` authors compact new SVG from parsed evidence while retaining the validated closure rather than distilling, supplementing, or redesigning it.

### Standard mode

`01_cover.svg` (title, subtitle, date, organization), `02_chapter.svg` (chapter number and title), `03_content.svg` (header/footer only; content area free), `04_ending.svg` (thank-you, contact), optional `02_toc.svg` (TOC title, chapter list) which shifts later types by one (`01_cover`, `02_toc`, `03_chapter`, `04_content`, `05_ending`). **Default — compact authored roster (may override when the confirmed Deck application requires distinct roles)**: keep Layout content pages structurally flexible; for Deck add only the prototypes its confirmed roles need, never variants from hypothetical uses. `standard` may hold several Layouts for one canonical role when the brief requires genuinely different structures (two-column evidence vs three-card KPI), suffixing every sibling (`03a_content_two_col.svg`, `03b_content_three_card.svg`) rather than leaving one unsuffixed; this does not require `fidelity`. The numeric prefix is the template's own order with a contiguous base sequence; tooling reads the page type from the token after the underscore.

### Fidelity mode

Design a broader roster close to the source's visual language with an independently authored Master/Layout system. Variants append a lowercase letter to the parent index (`02a_chapter_full.svg`, `02b_chapter_minimal.svg`, `03a_content_two_col.svg`, `03b_content_data_card.svg`, `03c_content_quote.svg`, `04a_ending_thanks.svg`); extension types (transition / appendix / disclaimer / divider) take the next free index (`05_section_break.svg`, `06_appendix.svg`). Choose variants from useful composition types (two-column, hero image, icon grid, data card, quote); keep only genuinely useful authored compositions — source Layout keys and repeated chrome are not clustering inputs; design each variant's contract from its reusable behavior; record every page in `§V` (library registration derives the index entry from `templates/*.svg`). Variants reuse the parent placeholder set (§4).

### Mirror mode

Author a new compact workspace from validated parsed evidence rather than a different system. Create Layout mirror is legal only when the source contract is already brand-neutral and application-neutral; otherwise return to dispatch (author a Layout through `standard` / `fidelity`, or retain a Deck) — removing, repainting, retyping, or discarding rules is never mirror. Model-facing source: `authoring_summary.json`, every reachable layered `authoring-svg/*.svg`, `svg/inheritance.json`, `native_structure.json`; inspect and where needed redraw these before publication; never read `authoring_manifest.json`; lossless `svg/` is immutable evidence. Precondition: the evidence identifies every source Slide with its Layout/Master, picker names, placeholder contract, and fixed layers — stop when reachable facts or supported geometry are missing. Output `<template_workspace>/templates/<NNN>_<page_type>.svg` per source Slide (type from `pageTypeCandidates`, fallback `content`), no standalone Master/Layout SVG, each resolving full context with explicit layer markers. Preserve within the closure: keys and picker names, parentage, assignments, placeholder type/index/bounds, example meaning, sprite-sheet crop behavior, supported native facts; imported Chart/Table JSON is authoritative with an approximate preview. Allowed: redrawing geometry, paint spelling, grouping, root declarations, asset paths, and fixed-layer wrappers while presentation and ownership stay intact. Forbidden: commonality extraction, synthesis, promotion/demotion, renaming, re-parenting, placeholder invention, JSON changes without intent, visible redesign. Mirror describes source-to-workspace fidelity and only makes literal reuse possible; Strategist independently decides selection, repetition, order, and reorganization. Mirror is not a recovery mode: charts, SmartArt, OLE, and EMF/WMF that fail to enter the parsed evidence stay gaps — report them before authoring.

---

## Template Design Specifications

### 1. Must Generate design_spec.md

**Scope rule — package-specific rules only.** A Deck spec describes its recurring application plus integrated identity and structure; a Layout spec only brand-neutral reusable structure with supported content shapes. Neither restates generic constraints already in every downstream reader's context — SVG rules and module routing (`shared-standards-core.md`), the layout-structure vocabulary (`executor-base.md`), spacing bands and font-size ratio bands (`strategist.md`), the canonical placeholder table (§4), content methodology (`strategist.md`), usage-instruction boilerplate, created-date / page-count rows. If a rule is generic, omit it; if the template breaks a generic rule, write only the deviation. When rewriting an existing template, delete such sections rather than leaving pointers.

Frontmatter is portable across scopes: never `output_scope`, `target_project`, or a generic `template_id`; use `deck_id` / `layout_id`.

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
source_canvas_width: 1280        # required when a PPTX/SVG source canvas is known
source_canvas_height: 720
source_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
# placeholders:                  # optional vocabulary override; [] asserts an intentional zero-marker page
#   01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LOGO}}"]
---

# [Template Name] — Design Specification

## I. Template Overview
| Application context | Definition |
|---|---|
| Recurring presentation family | <repeatable situations> |
| Intended audiences and outcomes | <who and what it enables> |
| Delivery and reading assumptions | <presented / close-read / handoff / mixed> |
| Representative narrative/page roles | <descriptive, not mandatory> |
- Design tone, theme mode, and the visual identity visible at a glance

## II. Color Scheme
- HEX values with role labels; brand-specific application rules when present

## III. Typography (omit without template-owned typeface identity)
- Per-role stacks; a non-preinstalled face leads only after user-confirmed installation, no auto-embedding; otherwise a safe face, with proprietary faces as references (CSS tails aid preview only); body baseline px (informational — `spec_lock.md` owns project values)

## IV. Signature Design Elements
- Motifs that ARE this template; source-derived grammar — grid/column rhythm, chrome, image zones, crop/clip, scrim/overlay or baked alpha, density rhythm; optional XML for a unique reusable component

## V. Page Roster
One row per Slide SVG: background, decorative anchors, rhythm, image behavior, density, role, reusable slots, capacity; the authored Layout key and picker name (mirror: the preserved keys). No required/optional/repeatable status or fixed/replaceable/example-only policy. Entries match every SVG on disk. Mirror adds `### Source Preservation Map` (`Source slide | Source Master | Source Layout | Output SVG | Preservation status`) plus one optional sentence for unmaterialized identities.

## VI. Assets (omit when none)
## VII. Placeholder Overrides (omit when none)
```

**Layout**: `layout_id`, `kind: layout`, `category: general | scenario | government | special`, `summary`, `keywords`, the canvas and source-canvas fields, `replication_mode`, `native_structure_mode: structured`, `page_count`, `page_types: [cover, toc, chapter, content, ending]`, optional `placeholders:`; body sections **IV** (structure-specific grid, zones, chrome, image behavior, density, semantic text roles, alignment/wrapping/capacity, slot conventions; neutral preview paint is not identity), **V** (one row per SVG with Layout key, picker name, content shape, slot behavior; mirror map as above), and **VII** when overrides exist. Omit Template Overview, Color Scheme, Typography, Logo, Voice & Tone, and Icon Style; a scenario category records geometric fit only; never prescribe objectives, outcomes, narrative order, boilerplate, or example retention — the frontmatter `summary` carries selection context.

### 2. Inherit Design Specification

Templates strictly follow the brief and `<design_spec_path>`: root `viewBox` equals `canvas_viewbox` (`width` / `height` optional and non-authoritative); with a PPTX/SVG reference record `source_canvas_*` and `source_viewbox`, and normalize all geometry, typography, strokes, and crops explicitly when the output canvas differs; colors, fonts, margins, image system, and Deck application follow the spec. With import output, prefer imported theme values over guesses, reuse exported `images/` directly, and treat `pageTypeCandidates` as hints. Preconditions: `standard` inspects the complete lightweight Master/Layout inventory plus enough page IR to understand direction and assets; `fidelity` inspects every Master/Layout and page; `mirror` verifies every Slide and chain against the summary, `native_structure.json`, and `inheritance.json`, reports retained/omitted identities before authoring, then publishes only that graph.

#### 2.1 PPTX Import Mode Rule

`standard` reviews complete evidence, then authors a compact canonical roster and structure; `fidelity` authors a broader source-aligned roster matching the visual language without one-to-one identity retention; `mirror` preserves validated Slides, inheritance, placeholders, native facts, meaning, and presentation while authoring a compact workspace — visible SVG may be redrawn, retained structure cannot be renamed, gaps cannot be invented. **Hard rule — mirror publication is mechanical, visual authoring is not**: the materializer validates identity/SHA, refs, graph, assignments, and closure, composes inherited context, strips IR-only refs, and publishes the current tree; it never replaces an unchanged visible subtree with lossless XML.

#### 2.2 Native Shape Payload and Authoring IR

| Representation | Purpose | Payload rule |
|---|---|---|
| Lossless import SVG | Immutable evidence | Retains complete metadata, native boundaries, hidden carriers, scope identity for validation and non-visible recovery; its visible subtree is never copied into templates |
| Authoring IR bundle | Editable source | Compact SVG from parsed evidence without opaque payload or duplicate carriers; retains visible intent and document-local source refs; models read the summary, tools the manifest |
| `standard` / `fidelity` output | Newly authored contract | Editable primitives, compact canonical preset groups for exact matches, `shape_boolean_svg.py` only where one compound contour must become an object, necessary freeform last; paint from the brief/spec; exported assets reused, never opaque payload or source topology |
| `mirror` output | Compact preservation contract | Publishes the reviewed tree, preserves validated structure/native facts, recovers only supported non-visible semantics, normalizes fixed layers into semantic atoms, strips IR-only refs |

Materialization validates document hashes, refs, and closure and classifies subtree hashes — a changed subtree is a legitimate edit, never permission to copy the old tree back; an object that cannot use supported non-visible metadata keeps its SVG fallback and is reported. `data-pptx-replace-with` stays reserved for Chart/Table replacement markers.

| Authored/preserved fact | Template SVG declaration |
|---|---|
| Master/Layout identity | Root `data-pptx-master` / `-master-name` / `data-pptx-layout` / `-layout-name`; authored keys for `standard` / `fidelity`, source keys for `mirror` |
| Authored Master/Layout visual | Direct atomic child with `data-pptx-layer="master|layout"` and `data-pptx-editable="false"`; ordinary `<g>` forbidden, one validated compact preset `<g>` the sole exception |
| Preserved source visual | Direct atoms with the same ownership and comparable paint order; grouping and spelling may differ, regrouping and ownership changes may not |
| Content slot | Direct `<g id>` with `data-pptx-placeholder` and explicit `data-pptx-bounds`; authored modes author the slot, mirror preserves source type/index/bounds and carrier identity |
| Page-only background | Direct full-canvas solid rect with `data-pptx-layer="slide"` |
| Structural hint | Optional `data-pptx-role` only when layer/placeholder metadata cannot express background/decoration/header/footer/logo/watermark/chrome/page-number behavior; stable unique `id` |

Repeat inherited visuals in every standalone SVG so preview stays complete; export validates their equality and infers no ownership. **Forbidden — legacy contract**: never carry `data-pptx-layout-kind`, `distilled`, `utility`, unmapped `baseline`, `preserve`, or direct atomic placeholders into a package; such Type B input is visual reference only, and native topology requires the Type A path. **Composite slot boundary**: a normal slot has exactly one compatible carrier (a validated preset `<g>` counts for `object`; an ordinary group does not); only a genuinely composite region uses `data-pptx-placeholder="object"` + `data-pptx-binding="proxy"`, never as the default form. Mirror preserves imported types, indices, bounds, and carriers exactly (never replacing `subTitle`, `obj`, `media`, or `dt` with generic body); authored modes assign `title`, `subtitle`, `body`, `picture`, `chart`, `table`, `object`, `media`, `date`, `footer`, `slide-number` deliberately, with indices only to disambiguate repeated roles. **Hard rule — explicit design-zone bounds**: every slot carries `data-pptx-bounds="x y width height"` (≤ two decimals) from the source Layout frame (mirror) or the intended safe area, column, panel inset, or media frame (authored) — never from character count, glyph width, wrapping, or the sample-content box; zero-slot Layouts are valid.

### 3. Placeholder Markers

Mirror retains literal source text and placeholder metadata and inserts no `{{...}}`. Authored modes mark replaceable content:

```xml
<g id="title-slot" data-pptx-placeholder="title" data-pptx-bounds="80 280 1120 96">
  <text id="title-carrier" data-pptx-carrier="true" x="80" y="320" fill="#FFFFFF" font-size="48" font-weight="bold">{{TITLE}}</text>
</g>
<rect x="40" y="90" width="1200" height="550" fill="#FFFFFF" rx="8"/>
<g id="body-slot" data-pptx-placeholder="body" data-pptx-bounds="40 90 1200 550">
  <text id="body-carrier" data-pptx-carrier="true" x="640" y="365" text-anchor="middle" fill="#CBD5E1" font-size="16">{{CONTENT_AREA}}</text>
</g>
```

### 4. Placeholder Reference (canonical convention, overridable per template)

Default vocabulary; new templates SHOULD prefer it and MAY substitute or extend when a style genuinely needs different names (`{{KEY_MESSAGE}}`, `{{BRAND_LOGO}}`). `svg_quality_checker.py --template-mode` warns when a page lacks its conventional placeholder; a `placeholders:` frontmatter map (`03a_content_dual_col: []` asserts none) silences it and documents the contract.

| Placeholder | Purpose | Page | Role |
|------------|---------|------|------|
| `{{TITLE}}`, `{{SUBTITLE}}`, `{{DATE}}`, `{{AUTHOR}}` | Title, subtitle, date, author/organization | Cover | Default |
| `{{CHAPTER_NUM}}`, `{{CHAPTER_TITLE}}` / `{{CHAPTER_DESC}}` | Chapter number, title / description | Chapter | Default / Optional |
| `{{PAGE_TITLE}}`, `{{CONTENT_AREA}}`, `{{PAGE_NUM}}` | Page title, content area, page number | Content (page number also ending) | Default |
| `{{KEY_MESSAGE}}` | Key takeaway | Content (consulting) | Style-specific |
| `{{SECTION_NAME}}`, `{{SOURCE}}` | Section name, data source | Content footer | Optional |
| `{{THANK_YOU}}`, `{{CONTACT_INFO}}` / `{{ENDING_SUBTITLE}}`, `{{COPYRIGHT}}` / `{{CLOSING_MESSAGE}}` | Ending content | Ending | Default / Optional / Style-specific |

TOC pages use indexed `{{TOC_ITEM_N_TITLE}}` / `{{TOC_ITEM_N_DESC}}`, never new families such as `{{CHAPTER_01_TITLE}}`. Variants reuse the parent set unless the frontmatter overrides that stem. In authored modes canonical insertion takes priority over visual mimicry; mirror preserves source placeholders and text.

---

## Output Requirements

Both scopes share one workspace shape; only the root differs:

```
<template_workspace>/
├── templates/   design_spec.md (project: design_spec.<kind>.<id>.md) + 01_cover.svg, [02_toc.svg,] 02|03_chapter.svg, 03|04_content.svg, 04|05_ending.svg
│                fidelity adds lettered variants and extension pages; mirror emits 001_cover.svg … 050_ending.svg
├── images/      optional; SVG href ../images/<name>
├── icons/imported/   optional canonical imported vectors
└── exports/     <deck_id|layout_id>_template_preview.pptx when requested or multi-Master
```

**Hard rule — common routing**: spec, SVGs, and non-bitmap template-source assets in `templates/`; every bitmap in `images/`; each imported vector once in `icons/imported/` referenced as `data-icon="imported/<name>"`; never `templates/icons/`; a review deck in `exports/` on request and always for multi-Master; no optional directory created merely to exist; no asset placement branching by scope.

**Template Preview**: on request or for multiple Masters, run `template_preview_pptx.py <template_workspace>` after validation ([`template-tools.md`](../scripts/docs/template-tools.md#template_preview_pptxpy)); include the path in the completion summary and omit `exports/` only for an unrequested one-Master package. For import-based templates, note which extracted assets were reused, which references influenced the authored roster, what mirror could not preserve, and any page-type mapping that needed judgment.

**Using an existing library workspace** (downstream reuse, not this role's authoring): copy or stage `templates/` plus `images/` / `icons/` (never `exports/`), adjust colors to the project spec, then customize; query the matching kind index (`brands_index.json`, `styles_index.json`, `layouts_index.json`, `decks_index.json`).

---

## Phase Completion Checkpoint

```markdown
## Template_Designer Phase Complete
- [x] Scope confirmed (`library` | `project`); preflight passed before final writes
- [x] Strategy derived from natural-language intent: `standard` | `fidelity` | `mirror`; Layout mirror source is brand/application-neutral
- [x] Every §V page saved to `<template_workspace>/templates/` with the naming convention applied
- [x] Templates follow the spec (colors, fonts, layout); Deck Overview and Roster describe without mandatory policy; Layout carries no application or identity contract
- [x] Authored modes inspected complete source evidence and represented each retained Layout through a new prototype; mirror preserved only Slides and their reachable structure
- [x] Placeholder markers clear and standardized for authored modes; mirror preserved literal text and source placeholder facts
- [x] Every SVG is a complete preview with explicit root identity and `native_structure_mode: structured`; authored Layout keys non-duplicative
- [x] Creation used the authoring IR; lossless imports stayed immutable; authored modes used helper-generated preset groups and spec paint
- [x] Bitmaps in `images/`, one canonical copy of each imported vector in `icons/imported/`
- [ ] **Next**: validate assets, export review evidence when requested or required, register library scope only
```
