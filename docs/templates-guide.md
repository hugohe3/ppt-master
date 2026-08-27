# Templates Guide: Use, Derive, and Boundaries

[English](./templates-guide.md) | [Chinese](./zh/templates-guide.md)

---

A PPT Master template is a reusable workspace with one of four explicit kinds: **Brand** owns identity, **Style** owns portable communication method and visual defaults, **Layout** owns brand-neutral reusable page structure, and **Deck** owns a recurring presentation application together with integrated identity and structure. Layout and Deck workspaces include complete SVG prototypes with declared Master / Layout / slot contracts; Brand and Style intentionally have no SVG roster. Each workspace's `design_spec.md` declares exactly what that kind contributes.

This guide answers three questions:

1. [How do I use an existing template?](#1-use-an-existing-template)
2. [How do I turn someone else's PPT — or my own brand — into a template? (the focus)](#2-derive-a-new-template-the-focus)
3. [What are the limits of templates?](#3-template-boundaries)

## 60-second template path

Choose the route by the artifact you already have and the result you want:

| Starting point and goal | Route | Copy-ready request |
|---|---|---|
| A raw `.pptx`; keep its existing slide shells and replace content | **Edit Native PPTX** | `Fill projects/source/template.pptx with projects/source/content.md; keep its design and use only the pages that fit.` |
| A reusable Brand/Style/Layout/Deck workspace; generate a fresh deck | **Generate PPTX → Stage-1 template controls** | `Make a deck from sources/report.pdf with template skills/ppt-master/templates/layouts/presentation_core/.` |
| A PPTX, SVG set, brand guide, website, images, or mixed references; first build a reusable system | **Create Template → Generate PPTX** | `Use /create-template to create a reusable Deck workspace from projects/brand/our_deck.pptx.` |

Do not pass a raw `.pptx` as a Generate PPTX template path. Fill it directly when you want its existing pages, or run Create Template first when you want a reusable system.

Choose the workspace kind by what must be reused:

| Kind | Reuses | Native PowerPoint result |
|---|---|---|
| **Brand** | Color, typography, logo, voice, icon style | Identity constraints only. Generated pages remain Slide-local under one clean project Master and Blank Layout. |
| **Style** | Communication method, open page-role vocabulary, evidence/data rules, visual defaults, image/icon direction, and advisory review focus | Flat Slide-local pages. Style values seed final Stage 2 but do not become brand identity or reusable Layouts. |
| **Layout** | Brand-neutral page grammar, Master/Layout identities, semantic text roles, slots, and layout roster | A structured deck with reusable native Masters, named Layouts, and placeholders; identity, reading-mode typography, and communication application are resolved separately. |
| **Deck** | A recurring presentation family: descriptive application context, identity, page structure, and actual prototypes | A deck whose page/prototype application plan is derived by AI from the template and current content. |

Theme, Slide Master, Slide Layout, and Placeholder are native PowerPoint
objects, not additional workspace kinds. Brand and Layout rules are compiled
into those objects. Under `layout` reuse, semantic text roles come from Layout
while final font and type scale are resolved from identity and reading mode;
`mirror` instead keeps literal source formatting. A final Master may contain
both structural geometry and brand visuals even though their source contracts
stay separate.

The two rules that prevent most mistakes:

1. Default Generate [Step 3](../skills/ppt-master/workflows/generate-pptx.md#step-3-template-candidate-preparation) only prepares candidates. Stage 1 confirms the communication contract and free-design/template choice together.
2. Ordinary requests start in free design. Explicit template intent or any exact workspace root opens template mode; exactly one supplied root is preselected, while multiple roots remain unselected candidates. A non-free selection is installed after Stage 1 and before template-aware final Stage 2.

---

## 1. Use an existing template

### How selection works

Default Generate places template selection inside **Stage 1**, beside the
template-independent communication contract. The page first shows switchable
Free design / Use templates choices. Ordinary requests initialize Free design
and keep the detailed selectors collapsed. Explicit template intent or any
exact workspace root initializes Use templates and expands the registered
Brand/Style/Layout/Deck plus supplied-root candidates. Exactly one supplied root
is preselected; multiple roots remain unselected candidates. The system does
not infer a specific template from the topic.

> **Quick Generate exception:** Quick never opens that page. Exact roots in the
> request are validated and used directly, with at most one contribution per
> kind. Layout and Deck may coexist, with Layout taking structural precedence;
> a multi-kind root contributes all of its specs.
> No exact root means free design. Bare names still do not resolve. Quick is
> lockless, not structureless: free design and Brand/Style-only output stays
> flat, while an installed Layout/Deck structure owner remains explicit
> Master/Layout/slot metadata in the authored SVGs and exported PPTX.

### How to use the selector

On the Stage-1 page, choose Free design or Use templates. Only Use templates
reveals five compact dropdowns: one each for registered Brand, Style, Layout,
and Deck workspaces, plus one for exact roots supplied for this run. Each is
single-select and includes `None`; the complete selection may combine all four
distinct kinds but contains at most one of each kind. Layout supplies structure
when present; otherwise Deck does. The
specified-root channel contributes at most one workspace, atomically with every
kind it exposes. The lists
come only from the four kind indexes; the workflow never scans the template
directories. Send an exact Brand/Style/Layout/Deck workspace root in chat when
you want template mode opened and that sole path preselected. Anywhere in the
sentence is fine; the path just has to be unambiguous:

> "use this template: `skills/ppt-master/templates/layouts/presentation_core/`" ✅
> "use last deck's template: `projects/last_deck/`" ✅
> "make a product introduction with `/Users/me/Desktop/our_brand_v3/`" ✅

For every current template kind, an explicit path is the **template workspace root**. An exact root matching a registered index entry may be displayed as `library`; an unregistered root remains separately labelled `explicit`. The server parses the latter's actual qualified specs; `explicit` is provenance, not a fifth kind or a priority tier. Stage 1 validates each selected root atomically. After confirmation, installation maps every selected spec and asset root exactly once, installs only the effective structural roster (Layout when present, otherwise Deck), and never copies `exports/`. Deck/Layout roots additionally validate their structured SVG contracts before precedence is applied; Brand/Style validate their roster-free specs. The path may point to a built-in library workspace under `skills/ppt-master/templates/<kind>/<id>/`, a project workspace under `projects/<name>/`, or another workspace with the same routing. A Create Template run may hand its exact validated workspace root directly to the next Stage-1 selector in the same conversation.

Template selection shares the Stage-1 screen and submit action but remains a
separate sidecar decision. The communication recommendation is authored only
from the current request, source facts, conversation constraints, and project
initialization; candidate metadata, selected roots, installed content, and
template canvas cannot influence it. After the combined confirmation, a
non-free choice runs the common apply stage and installs the selected
workspaces into the project's `templates/`, `images/`, and `icons/`. Final
Stage 2 then compares the confirmed communication contract with that installed
state; `template_application` describes **how** to use it and never chooses
**which** template to use.

`template_application` is one natural-language paragraph, not a mode selector.
Explicit user instructions win; otherwise the AI reads every installed template
SVG, decides from the current content, and defaults to reference-led use when no
stronger fit exists. Reference-led use may redesign after studying the full
roster; augment-only preserves existing non-slot objects, permits slot edits,
and only adds; replacement-only changes information carriers while preserving
the rest. These are examples, not fixed options. Any prototype-specific exception
names the exact SVG basename. Quick makes and freezes the same paragraph only in
its active context instead of writing confirmation/spec artifacts.

> **Current-workspace preflight:** Step 3 accepts only a workspace root exposing its Design Spec under `templates/`. Flat-root, former atomic-placeholder, unmapped Master/Layout, and other semantic-legacy packages are rejected; run `create-template` to create a new workspace, then generate new structured pages from that workspace. Nothing upgrades the old package in place.

### What does NOT select a template automatically

- **A bare template name in chat**: "presentation_core" / "China Telecom template" does not resolve implicitly or preselect a workspace. Choose the registered entry on the page or return its exact path in chat.
- **Style descriptions**: "McKinsey style" / "Google style" / "minimalist" / "Keynote style" remain design briefs. They never activate a workspace unless the user selects one or supplies its exact root.

This is intentional: the AI never makes a fuzzy or interpretive judgment about whether wording maps to a template. The Stage-1 mode switch is always available in Default Generate, while only an exact root selected from the indexed controls activates a workspace.

To browse in chat, ask "what templates are available?" The chat listing and Stage-1 selector use the same four indexes. Listing alone does not select anything; return one of those exact paths or make the choice on the page.

### Copy-ready examples

Use one workspace:

```text
Make a deck from projects/q3-report/sources/report.pdf.
Template workspace: skills/ppt-master/templates/layouts/presentation_core/
```

Combine identity and structure:

```text
Make a product-launch deck from projects/launch/sources/brief.md.
Brand workspace: skills/ppt-master/templates/brands/anthropic/
Layout workspace: skills/ppt-master/templates/layouts/presentation_core/
```

Use a project-scoped template created earlier:

```text
Make a deck from projects/annual-report/sources/report.md.
Template workspace: projects/acme_template/
```

For chat-based explicit root selection, path labels are optional but exact roots are mandatory. The page's library selection already carries exact roots. The page allows one registered selection per kind and one specified root, and rejects only duplicate kinds. Layout and Deck may be selected together; Layout then owns structure while Deck retains its other segments. A specified multi-kind root is all-or-nothing; its exposed kinds cannot be selected again from the library.

You do not need to choose a template-use mode. Strategist reads the effective structural roster—Layout when present, otherwise Deck—and current content, then decides which pages to select, repeat, skip, reorder, or reorganize. Brand instead supplies identity constraints, while Style supplies direction/method defaults; both leave pages freely composed unless another workspace supplies structure. If you care about a specific boundary, state it in ordinary language in the same request—for example, “keep the cover and closing page exactly, choose suitable middle pages yourself” or “use only the visual language”. That explicit sentence wins over AI judgment.

### Template catalog

Templates are organized into four kinds, each with a discovery index:

- [`brands_index.json`](../skills/ppt-master/templates/brands/brands_index.json) — identity-only workspaces: color / typography / logo / voice / icon style, with no SVG page roster
- [`styles_index.json`](../skills/ppt-master/templates/styles/styles_index.json) — direction/method workspaces: communication method, evidence/data expression, visual defaults, and advisory review focus, with no SVG page roster
- [`layouts_index.json`](../skills/ppt-master/templates/layouts/layouts_index.json) — structure-only workspaces: canvas / page grammar / page types / SVG roster, with identity selected downstream
- [`decks_index.json`](../skills/ppt-master/templates/decks/decks_index.json) — recurring presentation applications with integrated identity, structure, and factual prototype descriptions

These four indexes are the complete registered-library source for the Default
Stage-1 template controls and chat discovery; directories are never scanned.
Ask "what templates are available?" for a readable list with exact workspace
paths. The kind-specific READMEs define their contracts. Full data model +
installation / segment-ownership rules: [`templates-architecture.md`](./templates-architecture.md).

### Free design vs template

Free design is **not** "no structure" or "no style" — the Strategist still plans the narrative, hierarchy, and visual system for that specific deck. Its generated pages use `pptx_structure.mode: flat`, so every visible object remains Slide-local. Brand-only and Style-only workspaces also stay `flat`; Brand supplies identity constraints, while Style supplies reusable method and visual-default seeds. Layout and Deck workspaces expose a reusable Master / Layout / slot contract. Strategist inspects the real prototypes and current content, then automatically decides whether to use that structure or only its visual language.

> Rule of thumb: use a Brand workspace when identity must be fixed; use a Style workspace when a repeatable method and visual direction should travel without page prototypes; use a Layout workspace when brand-neutral structure should be reused while purpose remains open; use a Deck when a branded structural system or recurring communication application should travel as one contract. Use free design when composition should grow only from the current content.

### A style brief is not a Style workspace

A **style brief** is interpretive language ("minimalist" / "Keynote-style" / "editorial") that the Strategist turns into concrete design choices for one deck. A **Style workspace** is a real `kind: style` template with pre-authored communication method and visual defaults, consumed only after the user chooses its registered entry, supplies its exact workspace root, or receives it through the current Create Template handoff.

| | Style workspace | Style brief |
|---|---|---|
| How invoked | Stage-1 template selection, exact directory path, or current Create Template handoff | Free-form description in your message; does not select a workspace |
| What it supplies | Reusable method, role/evidence discipline, and visual defaults; no identity truth or page prototypes | Intent that the Strategist interprets into mode, visual style, color, typography, icons, and imagery |
| Confirmation | Stored values seed final Stage 2; Brand/Deck identity and user-confirmed choices remain authoritative | No pre-authored values; the Strategist proposes concrete candidates and the user confirms them |
| Best for | Repeating a design/argument approach across projects without freezing pages | Expressing a desired feel for the current project only |

A style description and a Style workspace still go through different machinery: "minimalist" is interpretive language and stays in free design, while `templates/styles/<id>/` is a real registered workspace selected on the page or through an exact path. `kind: style`, final Stage-2 `visual_style`, and internal `template_reuse_scope: style` are separate axes.

### How style briefs are interpreted

The Strategist separates two independent choices:

- **Mode** controls how the deck communicates: `pyramid`, `narrative`, `instructional`, `showcase`, `briefing`, or a confirmed `custom` direction.
- **Visual style** controls how the pages look: built-ins such as `swiss-minimal`, `editorial`, `dark-tech`, `data-journalism`, `ink-wash`, and others, plus `custom`.

Any mode can pair with any visual style. Terms such as "Keynote-style product launch" may influence both axes — for example, a `showcase` narrative with a restrained high-whitespace visual system — but they are never a template lookup token. The user confirms the resulting choices before generation. The canonical catalogs live under [`references/modes/`](../skills/ppt-master/references/modes/) and [`references/visual-styles/`](../skills/ppt-master/references/visual-styles/).

---

## 2. Derive a new template (the focus)

Turn one or more PPTX/SVG files, images/PDFs, documents/websites, brand assets, or direct written requirements into a PPT Master template. References may be combined, and a template may also be designed from a confirmed brief with no external source. This is the core of this guide.

### Entry point: the `/create-template` workflow

Full spec in [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md). This section is the user-facing short version — in your IDE, just say:

```
Please use the /create-template workflow to generate a new template based on the reference materials below.
```

The workflow will then **mandatorily** confirm a template brief with you before doing anything (this gate cannot be skipped).

The entry name always remains **Create Template**. It dispatches exactly one child workflow: Create Brand for identity only, Create Style for portable method/direction without prototypes, Create Layout for brand-neutral structure whose communication application remains open, or Create Deck for a branded structural system or recurring presentation application. A complete source PPTX alone does not determine the kind; the workflow classifies the stable rules worth reusing. The selected child is not reconsidered inside the brief.

### Step 1 — Prepare a reference bundle or brief

You may provide direct conversation text, pasted requirements, Markdown/TXT, DOCX/PDF/HTML/URL, websites, images/screenshots, logo/icon/font assets, PPTX/SVG files, or any useful combination. The workflow analyzes every applicable channel, keeps source provenance, and surfaces conflicts in the mandatory brief instead of silently choosing one source. Exact values authored by you are decisions whether they arrive in chat, pasted text, or your own brief file; a file carrier does not turn them into facts. Facts require independently traceable external authority or machine-observable source metadata. Visual estimates and vague-text interpretations remain suggestions until confirmed.

**When an existing deck's native structure matters, hand over the original `.pptx` file.** The importer reads OOXML directly and extracts the Master, Layout, placeholder, theme, native-shape, and reusable-asset facts that are actually present and supported into layered analysis references. Tell the AI in ordinary language what result you want—for example, “preserve it as-is”, “extract a reusable Master/Layout system”, or “keep the visual language but redesign the structure”. It then chooses the compatible internal implementation. The original PPTX remains immutable analysis evidence and is not packaged into the new template.

You can also design from scratch from a brand guideline: provide a logo, primary color HEX, fonts, tone description, and a few mood references — the AI will design the page skeletons on the spot. This suits brands that don't yet have a finished PPT, only a VI manual.

> **Evidence boundary:** images, screenshots, text, documents, websites, and loose assets can drive a newly authored template. Broad source-aligned coverage requires PPTX/SVG page evidence; literal native preservation requires an original PPTX or a complete current structured-SVG contract. Supplemental sources may clarify preservation intent but cannot invent or change native topology.

### Step 2 — The template brief (mandatory confirmation)

Before generation, the workflow writes one concise natural-language proposal and waits for corrections or acceptance. It does **not** ask you to choose template modes, fidelity enums, or page/content policies.

| Field | Notes |
|-------|-------|
| **Output scope** | `library` (default) or `project`; both use the same spec schema, while the library uses a bare spec in a single-kind directory and a project uses a qualified spec in its shared root |
| **Target project** | Required only for `project`; give the exact initialized project path |
| **Selected child workflow** | Create Brand / Create Style / Create Layout / Create Deck, fixed by the entry dispatch |
| **Template ID** | Portable template identity; in library scope it is also the directory / index key. Prefer ASCII slug like `acme_consulting`; non-ASCII names work but must be filesystem-safe |
| **Display name** | Human-readable name for documentation |
| **Kind-specific context** | Brand: identity use cases and tone. Style: broad best fit plus discovery keywords. Layout: structure-compatible situations plus category/keywords. Deck: recurring application plus category/keywords. You may correct the prose directly |
| **Method and visual defaults** | Create Style only: communication method, open page-role vocabulary, evidence/data expression, visual defaults, image/icon direction, and advisory review focus; no audience/page/structure contract |
| **Identity** | Create Brand/Create Deck only: palette, typography, logo, voice, and icon identity |
| **Canvas and structure** | Create Layout/Create Deck only: canvas, page grammar, Master/Layout/slot plan, density behavior, and source-derived structural rules |
| **Source treatment** | Every child states what it extracts inside its owned segment. Only Layout/Deck describe prototype breadth, preservation/rebuild strategy, and native structure |
| **Source facts and assets** | Brand/Layout/Deck list adopted or excluded assets; Layout/Deck also report observable Master/Layout facts and supported native features. Style retains textual provenance only |

After confirmation the workflow echoes the finalized brief and emits the marker `[TEMPLATE_BRIEF_CONFIRMED]`. Subsequent steps only run after that marker. **This is a hard gate — no brief, no generation.**

Before either scope writes final files, one hard preflight resolves the Design Spec and all real asset destinations. Library scope requires an empty `templates/` root. Project scope requires an initialized project and rejects a bare spec, an existing spec of the new kind, or invalid qualified naming; distinct kinds may coexist. Adding Deck beside Layout preserves the Layout roster, while adding Layout beside Deck uses isolated validation and an atomic structural replacement. Both scopes reject bitmap, imported-vector, review-export, and unrelated destination collisions before writing. Existing empty project scaffolding is left untouched, and optional directories are not created merely to retain empty paths. A failed check stops before partial output; the workflow does not overwrite.

> Why so strict? A template is a reusable ownership contract, whether it is global or project-scoped. Confirming the owned segment and destination first—and geometry only for Layout/Deck—avoids partial or misplaced output.

### Step 3 — The AI derives the implementation

Create Style writes its confirmed direction/method spec directly and does not
enter an SVG creation mode. For Create Layout/Create Deck, you do not select a
creation mode. The AI translates the confirmed prose into one internal
strategy so deterministic tools can run:

- a compact reusable system when the request calls for distillation;
- broader source-aligned coverage when the source itself contains useful variants;
- compact mirror authoring when the request calls for preservation and the source has a complete supported structure contract.

Layout/Deck frontmatter still records `replication_mode: standard|fidelity|mirror` for tool compatibility and audit. It is an implementation record, not a user-facing choice. Style frontmatter intentionally has no replication/native-structure fields. A brand-neutral Layout cannot literally preserve brand/application facts; the AI either re-authors it as a Layout or keeps those facts in a Deck according to the requested result.

**About sprite sheets**: PPTX-exported assets are often a single large image referenced from multiple slides, each cropping a different region via nested `<svg viewBox=...>` wrappers. In `fidelity` and `mirror` modes this nesting must be preserved — you cannot flatten it to a bare `<image>`, or the crop is lost and the page misaligns. The workflow validates this automatically.

**About native PowerPoint shapes**: the lossless import SVG stays immutable as source/package evidence and supported non-visible payload backing. Template creation uses the new compact editable `authoring-svg/` tree and its source-ref/hash manifest. Template_Designer reviews/authors that tree for mirror, preserving structure, meaning, and similar presentation without requiring identical SVG code. The publisher validates/composes the current visible tree and never restores ordinary lossless subtrees; final templates contain no IR-only refs. Imported/template-owned Chart/Table JSON remains inline and authoritative, while its compact preview may be approximate.

For a PPTX-backed Type A mirror, final validation/publication uses one deterministic command after the authoring review:

```bash
python3 skills/ppt-master/scripts/mirror_template_materialize.py \
  "<import_workspace>" "<template_workspace>"
```

It validates source SHA/known refs, the authoring manifest, reachable native
graph, visibility/assignment facts, and imported-vector closure before atomically publishing the
current source-ordered SVG roster and assets. It never
requires or uses the opt-in `svg-flat/` verification tree as the template source
and never generates a Design Spec; the designer writes the resolved spec
against the published roster.

**Mirror graph boundary**: mirror emits one complete prototype per source Slide and preserves only each Slide's referenced Layout and parent Master. The SVG resolves Master + Layout + Slide context while keeping layer ownership explicit. Source Master/Layout identities unused by every Slide are not materialized by mirror; `standard` / `fidelity` may use the complete source inventory to author useful new Slide prototypes.

The Design Spec gives every emitted Slide prototype its normal roster row. When the source contains unreferenced Master/Layout identities, one scope sentence may note that they exist but were not materialized by mirror; it does not invent per-identity usage analysis.

Template use is Slide-first: each generated-page SVG already resolves its Master and Layout visuals, so normal authoring selects that complete Slide prototype. The workspace contains no standalone Master/Layout definition SVGs.

“Slide-only” describes the editable SVG roster. A PPTX-backed mirror may also carry tool-only structural sidecars such as `source_themes.json` and `native_payloads.json.gz`; they preserve exact reachable Theme plus supported opaque restoration payloads/attribute records and are not page prototypes or AI authoring inputs. Semantic Chart/Table JSON always stays inline in its SVG marker.

**How a mirror-authored workspace is consumed**: source-to-workspace `replication_mode: mirror` is a capability, not a project choice. Strategist inspects the actual prototypes, current content, and any explicit instruction, then decides which pages to select, repeat, skip, or reorder and whether literal, structural, or visual-only reuse is appropriate. Literal reuse copies a complete prototype and edits only allowed visible text values while preserving decoration, sprite crops, geometry, and normalized structured declarations. This never requires the source page count or order.

### Step 4 — Validation, review export, registration, and discovery

After generation, both scopes run [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) as a hard gate: Brand validates its identity-only spec, Style validates its method/direction-only spec, and Layout/Deck validate the SVG roster and structured contract. Brand/Style never create a preview PPTX. Layout/Deck may create `exports/<id>_template_preview.pptx` on request, and must do so for multiple Masters. Authored templates use concise preview-only placeholder samples so long canonical markers stay readable without changing the source SVGs. The only scope-specific action is library registration:

| Scope | Workspace root | Preview | Discovery behavior |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind>/<id>/` | Create Brand/Create Style: N/A; Create Layout/Create Deck: optional for one Master, mandatory for multiple Masters | Register in the matching `brands_index.json`, `styles_index.json`, `layouts_index.json`, or `decks_index.json` after validation |
| `project` | `projects/<name>/` | Same kind-specific review behavior | Skip global index registration |

Library registration makes the template **selectable** in the Default Stage-1 template controls and discoverable in chat because both read the same index. For project scope or an exact handoff, supply the workspace root, for example `use this template: projects/<name>/`; this initializes template mode, exactly one supplied root is preselected, multiple supplied roots remain unselected candidates, and an unregistered root remains labelled `explicit`. A project root remains directly reusable by another project and contributes every qualified spec it exposes. Moving one contribution into the single-kind library requires placing its unchanged spec body at that library workspace's bare `templates/design_spec.md` path and registering it.

When a Deck/Layout template is selected, Strategist automatically authors the page/prototype plan. It may use the whole roster or a subset, repeat or reorder prototypes, and reorganize content where needed. `strict` / `adaptive` remain internal exporter values and do not appear as confirmation options.

### Verify that Master and Layout were really applied

For a generated deck that used a Layout or Deck workspace, verify the release artifact in Microsoft PowerPoint:

| Check | Expected result |
|---|---|
| **View → Slide Master** | The declared Master(s) and named Layouts are present. |
| **Home → New Slide** | The reusable Layout names appear in the layout picker under the intended Master. |
| Select a generated slide and inspect **Layout** | The slide is bound to its declared Layout, not a generic inferred layout. |
| Click a reusable content region | Template slots behave as native placeholders with the declared type and frame. |
| Add a new slide from one of the emitted Layouts | Master/Layout visuals and placeholder geometry appear without copying a finished content slide. |

Brand/Style use is intentionally different: both keep authored content Slide-local, so do not expect a reusable template Layout roster beyond the clean package scaffold. Brand supplies identity; Style supplies method/direction defaults.

`exports/<id>_template_preview.pptx` is review evidence created by Create Template when requested or required. It is not the template input; generation always consumes the workspace root.

Microsoft PowerPoint is the acceptance target for Master/Layout behavior. Keynote, WPS, and LibreOffice can open PPTX files but may normalize template structure.

### What a derived template workspace looks like

Library and project scopes use the same spec schema and asset routing; a library workspace uses a bare spec while a shared project root uses qualified specs. Substitute either `skills/ppt-master/templates/<kind>/<id>/` or `projects/<name>/` for `<template_workspace>`:

Brand and Style stop at `templates/design_spec.md` (plus real Brand assets when
present); they do not create the SVG or `exports/` rows shown above.

```
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_toc.svg              # optional; without it: 02_chapter, 03_content, 04_ending
│   ├── 03_chapter.svg
│   ├── 04_content.svg          # use 04a/04b siblings when multiple variants exist
│   └── 05_ending.svg
├── images/                         # optional
│   └── *.png / *.jpg           # SVG references use ../images/<name>
├── icons/                          # optional
│   └── imported/
│       └── *.svg               # one canonical copy of imported vectors
└── exports/                        # optional; on-demand review output
    └── <id>_template_preview.pptx
```

`standard` and `fidelity` SVGs use a unified authoring-placeholder vocabulary (`{{TITLE}}`, `{{CHAPTER_TITLE}}`, `{{PAGE_TITLE}}`, `{{CONTENT_AREA}}`, ...). Each native slot is a top-level `<g>` with semantic type and positive bounds; a normal slot contains exactly one carrier. Fixed Master/Layout visuals are direct root atoms and never layer `<g>` elements. A Layout may intentionally expose zero slots.

A `mirror` workspace uses the same tree but places its source-ordered `001_cover.svg`, `002_toc.svg`, … files under `templates/`. It may keep literal example text instead of `{{...}}` markers, while imported native slots still carry semantic metadata.

Imported vector placeholders use `data-icon="imported/<name>"`. Validation,
preview export, and final export all resolve the same workspace-root asset at
`icons/imported/<name>.svg`; a second `templates/icons/` copy is neither needed
nor allowed.

### Library registration vs project placement

- **Library scope (`library`, default)** writes the workspace under `skills/ppt-master/templates/<kind>/<id>/` and registers it globally.
- **Project scope (`project`)** writes a qualified spec at `projects/<name>/templates/design_spec.<kind>.<id>.md` and skips registration, so one project root can accumulate one contribution of every kind over separate runs and hand the complete bundle to any project that points at that root. Layout owns the active roster when Layout and Deck coexist.

The result is not a private or reduced project-only format. Supplying an exact
workspace root adds it to the Step-3 candidate input, defaults Stage 1 to
template mode, and preselects that root only when it is the sole supplied root.
Each distinct root migrates once with every qualified spec it exposes and any
real package-owned `images/` and `icons/`; only the effective Layout-or-Deck SVG
roster is installed;
unrelated project scaffolding and `exports/` are ignored. If one contribution
moves into the library, place it in a single-kind library workspace and run its
kind-specific registration so discovery reflects the new location.

---

## 3. Template boundaries

Common misconceptions to avoid:

- **A reusable template is an explicit workspace, not a packaged source PPTX.** Brand and Style workspaces are roster-free; Layout and Deck workspaces add the structured SVG contract. Authored modes create that contract, while mirror maps validated source ownership facts into it. Export compiles only declared structure
- **A template is not one undifferentiated "style skin".** Brand, Style, Layout, and Deck deliberately separate identity, direction/method, structure, and application so each segment can be reused or combined under an explicit ownership rule
- **A template does not make content decisions for you.** The Strategist still decides per-page which layout to use and whether to extend a variant. Templates offer candidates, not predetermined results
- **`fidelity` mode is not pixel-perfect copying.** Even with `literal` fidelity, the AI still strips noise and unnecessary repetition — geometry stays, redundancy goes
- **`mirror` targets literal supported appearance and each source Slide's reachable topology, not byte-identical OOXML.** It inherits source import limitations and permits only mechanical normalization such as inheritance completion and fixed-layer group expansion. Unsupported native objects keep their available SVG fallback or are reported; mirror never synthesizes replacement ownership.

---

## Related docs

- [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md) — full workflow spec (AI-facing)
- [`templates/README.md`](../skills/ppt-master/templates/README.md) — four template kinds and their discovery indexes
- [`references/template-designer.md`](../skills/ppt-master/references/template-designer.md) — Template_Designer role definition and SVG technical constraints
- [FAQ: how do I create a custom template?](./faq.md) — short FAQ version
