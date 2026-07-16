# Templates Guide: Use, Derive, and Boundaries

A PPT Master "template" is a **structure + style** preset bundle: complete standalone SVG pages whose metadata explicitly identifies one Master and Layout, atomic fixed-layer objects, and grouped content slots, plus `design_spec.md` and matching assets. Export deterministically compiles that declared contract into native PowerPoint structure.

This guide answers three questions:

1. [How do I use an existing template?](#1-use-an-existing-template)
2. [How do I turn someone else's PPT — or my own brand — into a template? (the focus)](#2-derive-a-new-template-the-focus)
3. [What are the limits of templates?](#3-template-boundaries)

---

## 1. Use an existing template

### How to trigger

The workflow **defaults to free design** — it will not ask whether you want a template and will not proactively suggest one. Templates are opt-in by **explicit directory path** only: name the path in your initial message.

### How to enter the template flow

Send the Brand/Layout/Deck workspace root in your initial message. Anywhere in the sentence is fine; the path just has to be unambiguous:

> "use this template: `skills/ppt-master/templates/layouts/presentation_core/`" ✅
> "use last deck's template: `projects/last_deck/`" ✅
> "make a product introduction with `/Users/me/Desktop/our_brand_v3/`" ✅

For every current template kind, the path is the **template workspace root**. Step 3 resolves `templates/design_spec.md`, then installs `templates/` plus any existing `images/` and `icons/` into the target project or consumes them in place when the workspace is already that project. It never copies `exports/`. Deck/Layout workspaces additionally validate the structured SVG contract. The path may point to a built-in library workspace under `skills/ppt-master/templates/<kind>/<id>/`, a project workspace under `projects/<name>/`, or another workspace with the same routing. A create-template run may hand its exact validated workspace root directly to Step 3 in the same conversation; this is the only exception to the initial-message rule.

> **Compatibility preflight:** Step 3 also accepts a flat-directory workspace with `design_spec.md` and SVGs directly at the supplied root, but only when those SVGs already satisfy the current contract. Flat placement by itself is harmless. Former atomic-placeholder, unmapped Master/Layout, and other semantic-legacy packages are rejected; run `create-template` to create a new workspace, then generate new structured pages from that workspace. Nothing upgrades the old package in place.

### What does NOT trigger the template flow

- **A bare template name without a path**: "use the presentation_core template" / "use the China Telecom template" → free design. The AI does not look the name up. You must give a path.
- **Style descriptions**: "McKinsey style" / "Google style" / "minimalist" / "Keynote style" → free design. The descriptive words flow into Strategist as a style brief, but no template is copied.
- **Vague intent**: "I want a template" with no path → free design.

This is intentional — the AI never makes a fuzzy / interpretive judgment about whether your wording maps to a template, and never resolves a name to a path on your behalf. If you want a template, give the path.

To browse what's available in the built-in library, ask "what templates are available?" — the AI lists names and paths from the discovery index. Listing alone does not enter the template flow; you still need to send back a path to trigger Step 3.

### Template catalog

Templates are organized into three kinds, each in its own directory:

- [`templates/brands/README.md`](../skills/ppt-master/templates/brands/README.md) — identity-only presets (color / typography / logo / voice / icon style), no SVG pages; Anthropic, Google
- [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md) — structure-only patterns (canvas / page structure / page types / SVG roster), no identity; presentation_core
- [`templates/decks/README.md`](../skills/ppt-master/templates/decks/README.md) — full identity + structure references (including the middle segment); CATARC and China Telecom

Full data model + fusion / conflict-resolution rules: [`docs/zh/templates-architecture.md`](./zh/templates-architecture.md) (Chinese only for now).

### Free design vs template

Free design is **not** "no structure" or "no style" — the AI plans a fresh Master/Layout system and visual language **for that specific deck** before drawing the SVG pages. A template reuses an already-defined structure and style. Both use the same structured output contract; the difference is where the structure originates.

> Rule of thumb: clear content direction + strong brand or scenario constraints (consulting reports, government briefings, defenses) → use a template. Essay-like content where atmosphere matters more (magazine, documentary narrative) → free design usually works better.

### Styles are not templates

A **style** is a description ("minimalist" / "Keynote-style" / "editorial") — a few words you type in chat. A **template** is a copy-and-paste asset bundle (SVGs + design_spec + assets) the workflow installs into your project when you give it an explicit directory path.

| | Template | Style |
|---|---|---|
| How invoked | Explicit directory path in your message | Free-form description in your message |
| What happens | Files copied into project; layouts inherit from template SVGs | Words flow to Strategist; color / typography / tone proposed in Strategist confirmation stage |
| Locked values | Yes — values come from the template's `design_spec.md` | No — Strategist invents values that fit the deck |
| Best for | Brand-locked decks; scenarios with strong visual conventions | When you have a feel in mind but no specific brand commitment |

A style description and a template name still go through different machinery: "minimalist" is interpretive language, while `presentation_core/` is a real template directory that requires an explicit path.

### Common styles you can describe

Three axes, freely combinable ("dark tech + minimalist" or "magazine + neo-Chinese"):

**Aesthetic direction**

| Style | One-line characterization |
|---|---|
| **Minimalist** | High whitespace, 2-3 colors, single focal point per page |
| **Information-dense** | McKinsey-style structured tables, high density, conclusion-first |
| **Keynote-style** | Single-page hero text, premium whitespace, Apple-feel |
| **Editorial** | Large hero images, asymmetric layouts, strong typography contrast |
| **Editorial illustration** | Warm tones, hand-drawn feel, zine-like |

**Scenario / Industry**

| Style | One-line characterization |
|---|---|
| **Business consulting** | Data-driven, restrained, blue / grey palette |
| **Academic defense** | Strict hierarchy, citation-heavy, clean |
| **Government briefing** | Red / blue, formal, symmetric |
| **Product launch** | Visually bold, marketing-driven, single hero per page |
| **Education / training** | Clear hierarchy, friendly tone, bright palette |
| **Pitch deck / BP** | Narrative-driven, conclusion-bold |

**Visual character / atmosphere**

| Style | One-line characterization |
|---|---|
| **Dark tech** | Dark backgrounds, neon accents, futuristic |
| **Pixel retro** | 8-bit, scanlines, gaming aesthetic |
| **Neo-Chinese** | Restrained traditional motifs, ink / vermilion |
| **Scandinavian** | Light, natural, restrained |
| **Memphis / pop** | High-saturation blocks, geometric, 80s |
| **Cyberpunk / vaporwave** | Neon purple-pink, grids, dreamlike |

When you describe a style, the AI doesn't pick a template — it interprets the words and lands them in Layer 2 of confirmation `d` (Style Objective) inside Strategist's confirmation stage, which then drives e (color), f (icon), g (typography), and h (image). You confirm or refine. To use the built-in `presentation_core` structure, send its workspace path; to keep structure free, describe only the style and let the AI adapt it to the deck content.

---

## 2. Derive a new template (the focus)

Turn one or more PPTX/SVG files, images/PDFs, documents/websites, brand assets, or direct written requirements into a PPT Master template. References may be combined, and a template may also be designed from a confirmed brief with no external source. This is the core of this guide.

### Entry point: the `/create-template` workflow

Full spec in [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md). This section is the user-facing short version — in your IDE, just say:

```
Please use the /create-template workflow to generate a new template based on the reference materials below.
```

The workflow will then **mandatorily** confirm a template brief with you before doing anything (this gate cannot be skipped).

The entry name always remains **Create Template**. It dispatches exactly one child workflow: Create Brand for identity only, Create Layout for brand-neutral structure only, or Create Deck for identity and structure together (the default when both are needed). The selected child is not reconsidered inside the brief.

### Step 1 — Prepare a reference bundle or brief

You may provide direct conversation text, pasted requirements, Markdown/TXT, DOCX/PDF/HTML/URL, websites, images/screenshots, logo/icon/font assets, PPTX/SVG files, or any useful combination. The workflow analyzes every applicable channel, keeps source provenance, and surfaces conflicts in the mandatory brief instead of silently choosing one source. Exact values stated by you are decisions; traceable statements from identified manuals or official sites are facts; visual estimates and vague-text interpretations remain suggestions until confirmed.

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
| **Replication mode** | Create Layout/Create Deck only: `standard` (default compact roster) / `fidelity` (one variant per reusable semantic family) / `mirror` (one materialized prototype per source slide). `standard` / `fidelity` author new SVG semantics; mirror preserves only validated facts already present in the source package. |
| **Native structure facts** | Create Layout/Create Deck only: the brief reports source Master/Layout counts, parent relationships, placeholder identities, and multi-master status. `standard` / `fidelity` treat them as reference only; mirror maps the supported facts one-to-one into the current `structured` contract. |
| **Visual fidelity** | Create Layout/Create Deck only; required for `standard` / `fidelity` when a reference exists. Choose `literal` or `adapted`. **Not asked for `mirror`** — mirror preserves the supported source visual. |
| **Keywords** | 3–5 tags for index lookup |
| Theme color / design notes / asset list | Optional — can be auto-extracted from the source |

After confirmation the workflow echoes the finalized brief and emits the marker `[TEMPLATE_BRIEF_CONFIRMED]`. Subsequent steps only run after that marker. **This is a hard gate — no brief, no generation.**

Before either scope writes final files, one hard preflight resolves the required `templates/` destination and any optional asset destinations, requires an empty `templates/` root, and rejects bitmap or imported-vector filename collisions in `images/` and `icons/imported/`. It checks `exports/` only when a review PPTX was requested. Project scope additionally requires an initialized target project. A failed check stops before partial output; the workflow does not merge or overwrite.

> Why so strict? A template is a structural contract, whether it is reused globally or only inside the current project. Confirming ownership and geometry first avoids partial or misplaced output.

### Step 3 — Create Layout/Create Deck: `standard`, `fidelity`, or `mirror`?

This is the most easily confused decision when deriving a structured template. Create Brand skips it because identity-only work has no SVG roster or native structure.

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| Output pages | 4–5 (cover / chapter / content / ending, with optional TOC) | one variant per reusable semantic family — count driven by the source | one materialized prototype per source slide (1:1 roster) |
| Abstraction | High — clean, reusable skeleton | Medium — semantic source families redesigned with cleanup | None at the topology level; only mechanical structured-contract normalization |
| Authoring placeholders | Yes (`{{TITLE}}`, `{{CONTENT_AREA}}`, …) | Yes | Literal text may remain, but imported native content slots still carry semantic metadata |
| Best for | You want "tone + basic skeleton" to generate brand-new decks later | The source PPTX itself is a customized layout library and every variant matters | Someone else's polished deck is great as-is, you want every page available as a reference |
| Typical use | Building a base brand template | Replicating a 20-variant government briefing layout set | Keeping all 50 source compositions available as faithful prototypes |
| Source requirement | None | PPTX or SVG visual reference | PPTX, or SVGs with a complete explicit structure contract |
| Decoration complexity | Usually simpler | Must preserve sprite-sheet crop structure | Preserves literal geometry while adding explicit layer ownership |

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

**How mirror is consumed**: the Strategist picks one mirror page per project page, and the Executor copies that complete SVG and edits visible text in place while preserving decoration, sprite crops, geometry, and the normalized structured declarations. Mirror preserves supported appearance, not the source PPTX group-editing hierarchy.

### Step 4 — Validation, review export, registration, and discovery

After generation, both scopes run [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) as a hard gate. If you want a PowerPoint review file, run the optional preview export; it creates `exports/<id>_template_preview.pptx` on demand. The only scope-specific action is library registration:

| Scope | Workspace root | Preview | Discovery behavior |
|---|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind>/<id>/` | Create Brand: N/A; Create Layout/Create Deck: optional for one Master, mandatory for multiple Masters | Register in the matching `brands_index.json`, `layouts_index.json`, or `decks_index.json` after validation |
| `project` | `projects/<name>/` | Same kind-specific review behavior | Skip global index registration |

Library registration makes the template **discoverable** — when someone asks "what templates are available?", the AI lists it from the index. To use either scope, follow the SKILL.md Step 3 rule: name the workspace root in your first message, for example `use this template: skills/ppt-master/templates/layouts/<your_template_id>/` or `use this template: projects/<name>/`. A project workspace can also be migrated or reused elsewhere because its core shape is identical; register it only if it is placed in the library and should appear in discovery.

When a deck/layout template is selected, the Strategist confirmation stage asks how it should be used:

- **adaptive** — choose one template SVG per page; keep its Master and assign a new explicit Layout key during authoring when fixed Layout atoms or slot topology/bounds must change
- **strict** — choose one template SVG per page and keep its Master/Layout/slot contract unchanged

### What a derived template workspace looks like

Library and project scopes use the same core structure; substitute either `skills/ppt-master/templates/<kind>/<id>/` or `projects/<name>/` for `<template_workspace>`:

```
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_toc.svg              # optional; without it: 02_chapter, 03_content, 04_ending
│   ├── 03_chapter.svg
│   ├── 04_content.svg
│   ├── 04a_content_two_col.svg # fidelity variant
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

- **A reusable template is an explicit SVG contract, not a packaged source PPTX.** Authored modes create that contract; mirror maps validated source ownership facts into it. Every page previews independently, and export compiles only declared Master/Layout/Slide structure
- **A template is not a "style skin".** It bundles structure (which blocks per page, how information is hierarchized) with style (colors, fonts, decoration). Trying to swap "skin" without structure tends to put the information architecture and the visuals at odds
- **A template does not make content decisions for you.** The Strategist still decides per-page which layout to use and whether to extend a variant. Templates offer candidates, not predetermined results
- **`fidelity` mode is not pixel-perfect copying.** Even with `literal` fidelity, the AI still strips noise and unnecessary repetition — geometry stays, redundancy goes
- **`mirror` targets literal supported appearance and source topology, not byte-identical OOXML.** It inherits source import limitations and permits only mechanical normalization such as fixed-layer group expansion. Unsupported native objects keep their available SVG fallback or are reported; mirror never synthesizes replacement ownership.

---

## Related docs

- [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md) — full workflow spec (AI-facing)
- [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md) — current template catalog
- [`references/template-designer.md`](../skills/ppt-master/references/template-designer.md) — Template_Designer role definition and SVG technical constraints
- [FAQ: how do I create a custom template?](./faq.md) — short FAQ version
