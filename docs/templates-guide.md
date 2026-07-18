# Templates Guide: Use, Derive, and Boundaries

[English](./templates-guide.md) | [Chinese](./zh/templates-guide.md)

---

A PPT Master template is a reusable workspace with one of three explicit kinds: **Brand** owns identity, **Layout** owns brand-neutral reusable page structure, and **Deck** owns a recurring presentation application together with integrated identity and structure. Layout and Deck workspaces include complete SVG prototypes with declared Master / Layout / slot contracts; Brand workspaces intentionally have no SVG roster. Each workspace's `design_spec.md` and matching assets declare exactly what that kind contributes.

This guide answers three questions:

1. [How do I use an existing template?](#1-use-an-existing-template)
2. [How do I turn someone else's PPT — or my own brand — into a template? (the focus)](#2-derive-a-new-template-the-focus)
3. [What are the limits of templates?](#3-template-boundaries)

## 60-second template path

Choose the route by the artifact you already have and the result you want:

| Starting point and goal | Route | Copy-ready request |
|---|---|---|
| A raw `.pptx`; keep its existing slide shells and replace content | **Fill Native PPTX** | `Fill projects/source/template.pptx with projects/source/content.md.` |
| A reusable Brand/Layout/Deck workspace; generate a fresh deck | **Generate PPTX with an explicit workspace path** | `Make a deck from sources/report.pdf with template skills/ppt-master/templates/layouts/presentation_core/.` |
| A PPTX, SVG set, brand guide, website, images, or mixed references; first build a reusable system | **Create Template → Generate PPTX** | `Use /create-template to create a reusable Deck workspace from projects/brand/our_deck.pptx.` |

Do not pass a raw `.pptx` as a Generate PPTX template path. Fill it directly when you want its existing pages, or run Create Template first when you want a reusable system.

Choose the workspace kind by what must be reused:

| Kind | Reuses | Native PowerPoint result |
|---|---|---|
| **Brand** | Color, typography, logo, voice, icon style | Identity constraints only. Generated pages remain Slide-local under one clean project Master and Blank Layout. |
| **Layout** | Brand-neutral page grammar, Master/Layout identities, semantic text roles, slots, and layout roster | A structured deck with reusable native Masters, named Layouts, and placeholders; identity, reading-mode typography, and communication application are resolved separately. |
| **Deck** | A recurring presentation family: application rules, identity, page structure, and starting-content policy | A structured deck with the template's integrated identity, reusable native structure, and scenario-aware starting rules. |

Theme, Slide Master, Slide Layout, and Placeholder are native PowerPoint
objects, not additional workspace kinds. Brand and Layout rules are compiled
into those objects. Under `layout` reuse, semantic text roles come from Layout
while final font and type scale are resolved from identity and reading mode;
`mirror` instead keeps literal source formatting. A final Master may contain
both structural geometry and brand visuals even though their source contracts
stay separate.

The two rules that prevent most mistakes:

1. Supply the **workspace root**, not its `templates/` subdirectory and not a bare template name.
2. Provide the explicit workspace path before [Generate PPTX Step 3](../skills/ppt-master/workflows/generate-pptx.md#step-3-template-option). A Create Template run may instead hand its validated workspace directly to Generate PPTX in the same conversation.

---

## 1. Use an existing template

### How to trigger

The workflow **defaults to free design** — it will not ask whether you want a template and will not proactively suggest one. Templates are opt-in by **explicit directory path** only: provide the path before Generate PPTX reaches Step 3.

### How to enter the template flow

Send the Brand/Layout/Deck workspace root in chat before Generate PPTX reaches Step 3. Anywhere in the sentence is fine; the path just has to be unambiguous:

> "use this template: `skills/ppt-master/templates/layouts/presentation_core/`" ✅
> "use last deck's template: `projects/last_deck/`" ✅
> "make a product introduction with `/Users/me/Desktop/our_brand_v3/`" ✅

For every current template kind, the path is the **template workspace root**. Step 3 resolves `templates/design_spec.md`, then installs `templates/` plus any existing `images/` and `icons/` into the target project or consumes them in place when the workspace is already that project. It never copies `exports/`. Deck/Layout workspaces additionally validate the structured SVG contract. The path may point to a built-in library workspace under `skills/ppt-master/templates/<kind>/<id>/`, a project workspace under `projects/<name>/`, or another workspace with the same routing. A create-template run may hand its exact validated workspace root directly to Step 3 in the same conversation; user-supplied paths and current-conversation Create Template handoffs are the two valid triggers.

> **Compatibility preflight:** Step 3 also accepts a flat-directory workspace with `design_spec.md` and SVGs directly at the supplied root, but only when those SVGs already satisfy the current contract. Flat placement by itself is harmless. Former atomic-placeholder, unmapped Master/Layout, and other semantic-legacy packages are rejected; run `create-template` to create a new workspace, then generate new structured pages from that workspace. Nothing upgrades the old package in place.

### What does NOT trigger the template flow

- **A bare template name without a path**: "use the presentation_core template" / "use the China Telecom template" → free design. The AI does not look the name up. You must give a path.
- **Style descriptions**: "McKinsey style" / "Google style" / "minimalist" / "Keynote style" → free design. The descriptive words flow into Strategist as a style brief, but no template is copied.
- **Vague intent**: "I want a template" with no path → free design.

This is intentional — the AI never makes a fuzzy / interpretive judgment about whether your wording maps to a template, and never resolves a name to a path on your behalf. If you want a template, give the path.

To browse what's available in the built-in library, ask "what templates are available?" — the AI lists names and paths from the discovery index. Listing alone does not enter the template flow; you still need to send back a path to trigger Step 3.

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

The path labels are optional; the paths themselves are mandatory. If two paths have the same kind, the workflow stops at the existing conflict-resolution gate instead of choosing one silently.

### Template catalog

Templates are organized into three kinds, each with a discovery index:

- [`brands_index.json`](../skills/ppt-master/templates/brands/brands_index.json) — identity-only workspaces: color / typography / logo / voice / icon style, with no SVG page roster
- [`layouts_index.json`](../skills/ppt-master/templates/layouts/layouts_index.json) — structure-only workspaces: canvas / page grammar / page types / SVG roster, with identity selected downstream
- [`decks_index.json`](../skills/ppt-master/templates/decks/decks_index.json) — recurring presentation applications with integrated identity, structure, and content-reuse rules

Ask "what templates are available?" for a readable list with workspace paths. The indexes are the current source of truth; the kind-specific READMEs define their contracts. Full data model + fusion / conflict-resolution rules: [`templates-architecture.md`](./templates-architecture.md).

### Free design vs template

Free design is **not** "no structure" or "no style" — the Strategist still plans the narrative, hierarchy, and visual system for that specific deck. Its generated pages use `pptx_structure.mode: flat`, so every visible object remains Slide-local. A Brand-only workspace also stays `flat` while supplying identity constraints. Layout and Deck workspaces expose a reusable Master / Layout / slot contract: confirmed `mirror` or `layout` use it through `pptx_structure.mode: structured`, while confirmed `style` intentionally discards native structure and generates `flat`.

> Rule of thumb: use a Brand workspace when identity must be fixed; use a Layout workspace when brand-neutral structure should be reused while purpose remains open; use a Deck when a branded structural system or recurring communication application should travel as one contract. Use free design when composition should grow from the current content.

### Styles are not templates

A **style brief** is interpretive language ("minimalist" / "Keynote-style" / "editorial") that the Strategist turns into concrete design choices. A **template** is a real Brand / Layout / Deck workspace that the workflow consumes only when you provide its explicit directory path.

| | Template | Style |
|---|---|---|
| How invoked | Explicit directory path in your message | Free-form description in your message |
| What it supplies | The segments declared by its kind: identity, structure, or both | Intent that the Strategist interprets into mode, visual style, color, typography, icons, and imagery |
| Confirmation | Template-owned values become the starting contract; user-confirmed choices remain authoritative | No pre-authored values; the Strategist proposes concrete candidates and the user confirms them |
| Best for | Reusing an existing identity and/or page system | Expressing a desired feel without adopting a stored workspace |

A style description and a template name still go through different machinery: "minimalist" is interpretive language, while `presentation_core/` is a real template directory that requires an explicit path.

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

The entry name always remains **Create Template**. It dispatches exactly one child workflow: Create Brand for identity only, Create Layout for brand-neutral structure whose communication application remains open, or Create Deck for a branded structural system or recurring presentation application. A complete source PPTX alone does not determine the kind; the workflow classifies the stable rules worth reusing. The selected child is not reconsidered inside the brief.

### Step 1 — Prepare a reference bundle or brief

You may provide direct conversation text, pasted requirements, Markdown/TXT, DOCX/PDF/HTML/URL, websites, images/screenshots, logo/icon/font assets, PPTX/SVG files, or any useful combination. The workflow analyzes every applicable channel, keeps source provenance, and surfaces conflicts in the mandatory brief instead of silently choosing one source. Exact values authored by you are decisions whether they arrive in chat, pasted text, or your own brief file; a file carrier does not turn them into facts. Facts require independently traceable external authority or machine-observable source metadata. Visual estimates and vague-text interpretations remain suggestions until confirmed.

**When an existing deck's native structure matters, hand over the original `.pptx` file.** The importer reads OOXML directly and extracts the Master, Layout, placeholder, theme, native-shape, and reusable-asset facts that are actually present and supported into layered analysis references. In `standard` / `fidelity`, Template_Designer uses them as visual reference and authors a new SVG roster plus a new Master/Layout/slot system. In mirror, it materializes those validated source facts into a new workspace without inventing missing topology or design intent. The original PPTX remains immutable analysis evidence and is not packaged into the new template.

You can also design from scratch from a brand guideline: provide a logo, primary color HEX, fonts, tone description, and a few mood references — the AI will design the page skeletons on the spot. This suits brands that don't yet have a finished PPT, only a VI manual.

> **Evidence boundary:** images, screenshots, text, documents, websites, and loose assets can independently drive `standard`. `fidelity` requires PPTX/SVG page evidence, while `mirror` requires an original PPTX or a complete current structured-SVG contract. Supplemental sources may clarify mirror evidence but cannot invent or change its native topology.

### Step 2 — The template brief (mandatory confirmation)

The workflow does not silently infer values — before generation it lists these items and waits for your reply:

| Field | Notes |
|-------|-------|
| **Output scope** | `library` (default) or `project`; both use the same portable workspace routing, while only library scope registers it globally |
| **Target project** | Required only for `project`; give the exact initialized project path |
| **Selected child workflow** | Create Brand / Create Layout / Create Deck, fixed by the entry dispatch |
| **Template ID** | Portable template identity; in library scope it is also the directory / index key. Prefer ASCII slug like `acme_consulting`; non-ASCII names work but must be filesystem-safe |
| **Display name** | Human-readable name for documentation |
| **Category** | One of `brand` / `general` / `scenario` / `government` / `special` |
| **Use cases** | Annual report / consulting / defense / government briefing / ... |
| **Tone summary** | One line, e.g. "modern, restrained, data-driven" |
| **Theme mode** | Create Layout/Create Deck only: light / dark / gradient / ... |
| **Canvas format** | Create Layout/Create Deck only; default `ppt169` (16:9), with other formats specified up front |
| **Replication mode** | Create Layout/Create Deck only: `standard` (default compact, brief-driven roster; may include a small number of explicitly required distinct variants) / `fidelity` (broader source-aligned coverage of useful semantic families) / `mirror` (one materialized prototype per source slide). `standard` / `fidelity` author new SVG semantics; mirror preserves only validated facts already present in the source package. Layout mirror is available only when that source contract is already brand-neutral and application-neutral. |
| **Native structure facts** | Create Layout/Create Deck only: the brief reports source Master/Layout counts, parent relationships, placeholder identities, and multi-master status. `standard` / `fidelity` treat them as reference only; mirror maps the supported facts one-to-one into the current `structured` contract. |
| **Visual fidelity** | Create Layout/Create Deck only; required for `standard` / `fidelity` when a reference exists. Choose `literal` or `adapted`. **Not asked for `mirror`** — mirror preserves the supported source visual. |
| **Keywords** | 3–5 tags for index lookup |
| Theme color / design notes / asset list | Optional — can be auto-extracted from the source |

After confirmation the workflow echoes the finalized brief and emits the marker `[TEMPLATE_BRIEF_CONFIRMED]`. Subsequent steps only run after that marker. **This is a hard gate — no brief, no generation.**

Before either scope writes final files, one hard preflight resolves the required `templates/` destination and any optional asset destinations, requires an empty `templates/` root, and rejects bitmap or imported-vector filename collisions in `images/` and `icons/imported/`. It checks `exports/` only when a review PPTX was requested. Project scope additionally requires an initialized target project. Existing empty scaffolding created by project initialization is allowed and left untouched; Create Template does not create optional directories merely to keep empty paths. A failed check stops before partial output; the workflow does not merge or overwrite.

> Why so strict? A template is a structural contract, whether it is reused globally or only inside the current project. Confirming ownership and geometry first avoids partial or misplaced output.

### Step 3 — Create Layout/Create Deck: `standard`, `fidelity`, or `mirror`?

This is the most easily confused decision when deriving a structured template. Create Brand skips it because identity-only work has no SVG roster or native structure.

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| Output pages | Usually 4–6: cover / chapter / ending, optional TOC, and one or a small explicitly required set of content Layouts | broader useful semantic-family coverage — count driven by the source evidence | one materialized prototype per source slide (1:1 roster) |
| Abstraction | High — clean, reusable skeleton | Medium — semantic source families redesigned with cleanup | None at the topology level; only mechanical structured-contract normalization |
| Authoring placeholders | Yes (`{{TITLE}}`, `{{CONTENT_AREA}}`, …) | Yes | Literal text may remain, but imported native content slots still carry semantic metadata |
| Best for | You want "tone + compact skeleton", including a few brief-required structures, to generate brand-new decks later | The source PPTX itself is a customized layout library and broader source-driven coverage matters | Someone else's polished deck is great as-is, you want every page available as a reference |
| Typical use | Building a base brand template | Replicating a 20-variant government briefing layout set | Keeping all 50 source compositions available as faithful prototypes |
| Source requirement | None | PPTX or SVG visual reference | PPTX, or SVGs with a complete explicit structure contract |
| Decoration complexity | Usually simpler | Must preserve sprite-sheet crop structure | Preserves literal geometry while adding explicit layer ownership |

`mirror` cannot preserve identity/application rules while also producing a
brand-neutral, application-neutral Layout. Choose `standard` / `fidelity` when
those rules should be removed and a new Layout authored; choose Create Deck
mirror when they should remain literal.

**About sprite sheets**: PPTX-exported assets are often a single large image referenced from multiple slides, each cropping a different region via nested `<svg viewBox=...>` wrappers. In `fidelity` and `mirror` modes this nesting must be preserved — you cannot flatten it to a bare `<image>`, or the crop is lost and the page misaligns. The workflow validates this automatically.

**About native PowerPoint shapes**: the lossless import SVG stays immutable in the temporary analysis workspace as native-payload backing. Template creation uses the lightweight editable `authoring-svg/` IR and its source-ref/hash manifest. Authored modes use project-canonical SVG and compact authored-preset groups only for exact registered preset matches. Mirror materializes final template SVGs from the IR, reusing converter-supported payload only for unchanged Slide-local/slot refs; fixed Master/Layout layers remain direct atoms, unsupported or edited objects keep the current SVG fallback, and final templates contain no IR-only refs.

For a PPTX-backed Type A mirror, that final step is one deterministic command:

```bash
python3 skills/ppt-master/scripts/mirror_template_materialize.py \
  "<import_workspace>" "<empty_template_workspace>"
```

It validates the IR manifest, immutable source hashes, complete native graph,
visibility facts, and imported-vector closure before atomically publishing the
source-ordered SVG roster and its `icons/imported/` / `images/` assets. It never
requires or uses the opt-in `svg-flat/` verification tree as the template source
and never generates `design_spec.md`;
the designer writes that brief against the published roster.

**Mirror graph boundary**: mirror preserves the complete supported source Master/Layout graph. It emits one complete prototype per source slide and one definition-only `layout_<layout_key>.svg` prototype for every source Layout unused by those slides. The latter registers in PowerPoint through the independent Layout roster without becoming a published page; its parent Master is retained with it. Preflight stops only when required source facts or supported geometry are missing, never merely because a Layout is unused.

**How a mirror-authored workspace is consumed**: source-to-workspace `replication_mode: mirror` is a capability, not the project choice. After the open communication contract is confirmed, Stage 2 first compares a Deck's stored application contract with the current audience, outcome, and content roles. It recommends `mirror` only for a recurring artifact whose new content fits the existing page roles and text topology; use `layout` when compatible structure should continue but content needs reflow, and `style` when only identity should carry over or the argument needs a different structure. If `mirror` is confirmed, the Strategist picks one prototype per project page and the Executor copies that complete SVG and edits only allowed visible text values while preserving decoration, sprite crops, geometry, and normalized structured declarations. This still does not require the source page count or order. Mirror preserves supported appearance, not the source PPTX group-editing hierarchy.

### Step 4 — Validation, review export, registration, and discovery

After generation, both scopes run [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) as a hard gate: Brand validates its identity-only spec and asset references, while Layout/Deck validate the SVG roster and structured contract. If you want a PowerPoint review file, run the optional preview export; it creates `exports/<id>_template_preview.pptx` on demand. Authored templates use concise preview-only placeholder samples so long canonical markers stay readable without changing the source SVGs. The only scope-specific action is library registration:

| Scope | Workspace root | Preview | Discovery behavior |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind>/<id>/` | Create Brand: N/A; Create Layout/Create Deck: optional for one Master, mandatory for multiple Masters | Register in the matching `brands_index.json`, `layouts_index.json`, or `decks_index.json` after validation |
| `project` | `projects/<name>/` | Same kind-specific review behavior | Skip global index registration |

Library registration makes the template **discoverable** — when someone asks "what templates are available?", the AI lists it from the index. To use either scope, follow [Generate PPTX Step 3](../skills/ppt-master/workflows/generate-pptx.md#step-3-template-option): provide the workspace root before Step 3 runs, for example `use this template: skills/ppt-master/templates/layouts/<your_template_id>/` or `use this template: projects/<name>/`. A project workspace can also be migrated or reused elsewhere because its core shape is identical; register it only if it is placed in the library and should appear in discovery.

When a deck/layout template is selected, the Strategist confirmation stage asks how it should be used:

- **adaptive** — choose one template SVG per page; keep its Master and assign a new explicit Layout key during authoring when fixed Layout atoms or slot topology/bounds must change
- **strict** — choose one template SVG per page and keep its Master/Layout/slot contract unchanged

### Verify that Master and Layout were really applied

For a generated deck that used a Layout or Deck workspace, verify the release artifact in Microsoft PowerPoint:

| Check | Expected result |
|---|---|
| **View → Slide Master** | The declared Master(s) and named Layouts are present. |
| **Home → New Slide** | The reusable Layout names appear in the layout picker under the intended Master. |
| Select a generated slide and inspect **Layout** | The slide is bound to its declared Layout, not a generic inferred layout. |
| Click a reusable content region | Template slots behave as native placeholders with the declared type and frame. |
| Add a new slide from one of the emitted Layouts | Master/Layout visuals and placeholder geometry appear without copying a finished content slide. |

Brand-only use is intentionally different: it applies identity while keeping authored content Slide-local, so do not expect a reusable template Layout roster beyond the clean package scaffold.

`exports/<id>_template_preview.pptx` is review evidence created by Create Template when requested or required. It is not the template input; generation always consumes the workspace root.

Microsoft PowerPoint is the acceptance target for Master/Layout behavior. Keynote, WPS, and LibreOffice can open PPTX files but may normalize template structure or load a large mirror roster of unused Layouts more slowly.

### What a derived template workspace looks like

Library and project scopes use the same core structure; substitute either `skills/ppt-master/templates/<kind>/<id>/` or `projects/<name>/` for `<template_workspace>`:

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
- **Project scope (`project`)** writes the same portable workspace at `projects/<name>/` and skips registration.

The result is not a private or reduced project-only format. You can point Step 3 at either workspace root, copy `templates/` plus any existing `images/` and `icons/` between roots, or migrate a project result into the library without restructuring it. If it moves into the library, run registration so discovery reflects its new location.

---

## 3. Template boundaries

Common misconceptions to avoid:

- **A reusable template is an explicit workspace, not a packaged source PPTX.** Brand workspaces may contain identity only; Layout and Deck workspaces add the structured SVG contract. Authored modes create that contract, while mirror maps validated source ownership facts into it. Export compiles only declared structure
- **A template is not one undifferentiated "style skin".** Brand, Layout, and Deck deliberately separate identity from structure so each segment can be reused or fused under an explicit ownership rule
- **A template does not make content decisions for you.** The Strategist still decides per-page which layout to use and whether to extend a variant. Templates offer candidates, not predetermined results
- **`fidelity` mode is not pixel-perfect copying.** Even with `literal` fidelity, the AI still strips noise and unnecessary repetition — geometry stays, redundancy goes
- **`mirror` targets literal supported appearance and source topology, not byte-identical OOXML.** It inherits source import limitations and permits only mechanical normalization such as fixed-layer group expansion. Unsupported native objects keep their available SVG fallback or are reported; mirror never synthesizes replacement ownership.

---

## Related docs

- [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md) — full workflow spec (AI-facing)
- [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md) — current template catalog
- [`references/template-designer.md`](../skills/ppt-master/references/template-designer.md) — Template_Designer role definition and SVG technical constraints
- [FAQ: how do I create a custom template?](./faq.md) — short FAQ version
