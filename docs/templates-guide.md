# Templates Guide: Use, Derive, and Boundaries

A PPT Master "template" is a **structure + style** preset bundle: complete standalone SVG pages whose metadata explicitly identifies Master, Layout, Slide, and placeholders, plus `design_spec.md` and matching assets. Export deterministically reconstructs native PowerPoint structure from those SVGs.

This guide answers three questions:

1. [How do I use an existing template?](#1-use-an-existing-template)
2. [How do I turn someone else's PPT — or my own brand — into a template? (the focus)](#2-derive-a-new-template-the-focus)
3. [What are the limits of templates?](#3-template-boundaries)

---

## 1. Use an existing template

### How to trigger

The workflow **defaults to free design** — it will not ask whether you want a template and will not proactively suggest one. Templates are opt-in by **explicit directory path** only: name the path in your initial message.

### How to enter the template flow

Send a path to a template directory in your initial message. Anywhere in the sentence is fine; the path just has to be unambiguous:

> "use this template: `skills/ppt-master/templates/layouts/academic_defense/`" ✅
> "用这个模板做汇报：`projects/last_deck/templates/`" ✅
> "做一份产品介绍，模板用 `/Users/me/Desktop/our_brand_v3/`" ✅

The AI installs that directory's SVGs, `design_spec.md`, and assets into your project, then proceeds to the Strategist phase. The path may point to the built-in library under `skills/ppt-master/templates/layouts/` or another self-contained template directory. When the path already is the current project's own `<project>/templates/` root, the workflow consumes it in place instead of copying it onto itself. A project-scoped create-template run may hand this exact validated path directly to Step 3 in the same conversation; this is the only exception to the initial-message rule. Do not use a different project's `templates/` root as an external package: its `../images/` and runtime icon references are owner-local. Promote that design through library scope first.

### What does NOT trigger the template flow

- **A bare template name without a path**: "use the academic_defense template" / "用 招商银行 模板" / "做一份 pixel_retro 模板的答辩" → free design. The AI does not look the name up. You must give a path.
- **Style descriptions**: "McKinsey style" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → free design. The descriptive words flow into Strategist as a style brief, but no template is copied.
- **Vague intent**: "想用个模板" / "I want a template" with no path → free design.

This is intentional — the AI never makes a fuzzy / interpretive judgment about whether your wording maps to a template, and never resolves a name to a path on your behalf. If you want a template, give the path.

To browse what's available in the built-in library, ask "what templates are available?" — the AI lists names and paths from the discovery index. Listing alone does not enter the template flow; you still need to send back a path to trigger Step 3.

### Template catalog

Templates are organized into three kinds, each in its own directory:

- [`templates/brands/README.md`](../skills/ppt-master/templates/brands/README.md) — identity-only presets (color / typography / logo / voice / icon style), no SVG pages; Anthropic, Google
- [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md) — structure-only patterns (canvas / page structure / page types / SVG roster), no identity; academic_defense, government_blue/red, ai_ops, medical_university, pixel_retro, psychology_attachment
- [`templates/decks/README.md`](../skills/ppt-master/templates/decks/README.md) — full-PPT replicas (identity + structure + middle segments); 招商银行, 中国电建_*, 中汽研_*, 重庆大学, 中国电信

Full data model + fusion / conflict-resolution rules: [`docs/zh/templates-architecture.md`](./zh/templates-architecture.md) (Chinese only for now).

### Free design vs template

Free design is **not** "no style" — the AI designs a fresh visual system **for that specific deck** based on its content. A template **reuses an already-defined structure and style**. Both involve real design work; the difference is whether the style is improvised or preset.

> Rule of thumb: clear content direction + strong brand or scenario constraints (consulting reports, government briefings, defenses) → use a template. Essay-like content where atmosphere matters more (magazine, documentary narrative) → free design usually works better.

### Styles are not templates

A **style** is a description ("minimalist" / "Keynote-style" / "magazine 风") — a few words you type in chat. A **template** is a copy-and-paste asset bundle (SVGs + design_spec + assets) the workflow installs into your project when you give it an explicit directory path.

| | Template | Style |
|---|---|---|
| How invoked | Explicit directory path in your message | Free-form description in your message |
| What happens | Files copied into project; layouts inherit from template SVGs | Words flow to Strategist; color / typography / tone proposed in Strategist confirmation stage |
| Locked values | Yes — values come from the template's `design_spec.md` | No — Strategist invents values that fit the deck |
| Best for | Brand-locked decks; scenarios with strong visual conventions | When you have a feel in mind but no specific brand commitment |

A style mention may resemble a template name (e.g., "academic style" sounds like the `academic_defense/` template directory), but they go through different machinery — a template requires a real path the AI can copy from, a style mention is interpretive language. Similar words, different paths in the most literal sense.

### Common styles you can describe

Three axes, freely combinable ("dark tech + minimalist" or "magazine + neo-Chinese"):

**Aesthetic direction**

| Style | One-line characterization |
|---|---|
| **Minimalist / 极简风** | High whitespace, 2-3 colors, single focal point per page |
| **Information-dense / 信息密集** | McKinsey-style structured tables, high density, conclusion-first |
| **Keynote-style** | Single-page hero text, premium whitespace, Apple-feel |
| **Editorial / 杂志风** | Large hero images, asymmetric layouts, strong typography contrast |
| **Editorial illustration / 文艺手绘** | Warm tones, hand-drawn feel, zine-like |

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
| **Dark tech / 暗色科技** | Dark backgrounds, neon accents, futuristic |
| **Pixel retro** | 8-bit, scanlines, gaming aesthetic |
| **Neo-Chinese / 新中式** | Restrained traditional motifs, ink / vermilion |
| **Scandinavian / 北欧极简** | Light, natural, restrained |
| **Memphis / pop** | High-saturation blocks, geometric, 80s |
| **Cyberpunk / vaporwave** | Neon purple-pink, grids, dreamlike |

When you describe a style, the AI doesn't pick a template — it interprets the words and lands them in Layer 2 of confirmation `d` (Style Objective) inside Strategist's confirmation stage, which then drives e (color), f (icon), g (typography), and h (image). You confirm or refine. If the style you want happens to match one of our built-in templates (e.g., `academic_defense` / `pixel_retro` / `psychology_attachment`), you have a choice: send the template's directory path for locked values, or describe the style for AI-interpreted values that adapt to your deck content.

---

## 2. Derive a new template (the focus)

Turn a PPT you like, a brand guideline, or an existing PPTX file into a PPT Master template. This is the core of this guide.

### Entry point: the `/create-template` workflow

Full spec in [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md). This section is the user-facing short version — in your IDE, just say:

```
Please use the /create-template workflow to generate a new template based on the reference materials below.
```

The workflow will then **mandatorily** confirm a template brief with you before doing anything (this gate cannot be skipped).

### Step 1 — Prepare reference material

**Strongly recommended: hand over the original `.pptx` file.** The importer reads OOXML directly and extracts every Master, Layout, placeholder, theme, and reusable asset into layered analysis references. Template_Designer uses those facts to rebuild one clean Master plus semantic Layouts as complete, explicitly annotated SVG pages. The original PPTX remains analysis input and is not packaged into the new template.

You can also design from scratch from a brand guideline: provide a logo, primary color HEX, fonts, tone description, and a few mood references — the AI will design the page skeletons on the spot. This suits brands that don't yet have a finished PPT, only a VI manual.

> **Fallback when no source PPTX exists**: a screenshot set (`cover.png` / `chapter.png` / `content.png` / `closing.png`, ...) still works, but fidelity drops noticeably — decoration, fonts, and layout details all rely on the AI's visual inference. Use `.pptx` whenever you can. Screenshots are better used as annotation alongside a PPTX ("this is the look I want") than as the sole reference.

### Step 2 — The template brief (mandatory confirmation)

The workflow does not silently infer values — before generation it lists these items and waits for your reply:

| Field | Notes |
|-------|-------|
| **Output scope** | `library` (default; reusable by every project and registered globally) or `project` (thin bundle written directly into one initialized project's template root) |
| **Target project** | Required only for `project`; give the exact initialized project path |
| **Template ID** | Portable template identity; in library scope it is also the directory / index key. Prefer ASCII slug like `acme_consulting`; non-ASCII names work but must be filesystem-safe |
| **Display name** | Human-readable name for documentation |
| **Category** | One of `brand` / `general` / `scenario` / `government` / `special` |
| **Use cases** | Annual report / consulting / defense / government briefing / ... |
| **Tone summary** | One line, e.g. "modern, restrained, data-driven" |
| **Theme mode** | Light / dark / gradient / ... |
| **Canvas format** | Default `ppt169` (16:9); specify other formats up front |
| **Replication mode** | `standard` (default 5-page roster) / `fidelity` (one variant per visually distinct cluster) / `mirror` (literal visual copy of every source slide plus explicit layer ownership) |
| **Native structure facts** | The brief reports source Master/Layout counts, placeholder identities, and multi-master status. Output is always rebuilt explicit SVG structure (`template`). |
| **Visual fidelity** | (required for `standard` / `fidelity` when a reference exists) `literal` (reproduce original geometry / decoration / sprite crops as-is) or `adapted` (use reference for tone and structure but allow design evolution). Cover / chapter / ending are usually `literal`. **Not asked for `mirror`** — mirror is implicitly literal |
| **Keywords** | 3–5 tags for index lookup |
| Theme color / design notes / asset list | Optional — can be auto-extracted from the source |

After confirmation the workflow echoes the finalized brief and emits the marker `[TEMPLATE_BRIEF_CONFIRMED]`. Subsequent steps only run after that marker. **This is a hard gate — no brief, no generation.**

For project scope, one more hard preflight runs before any final file is written: the target must already be initialized, its `templates/` root must be empty, and the planned bitmap/icon filenames must not collide with anything already in `images/` or `icons/`. A failed check stops before partial output; the workflow does not merge or overwrite.

> Why so strict? A template is a structural contract, whether it is reused globally or only inside the current project. Confirming ownership and geometry first avoids partial or misplaced output.

### Step 3 — `standard`, `fidelity`, or `mirror`?

This is the most easily confused decision when deriving a template.

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| Output pages | 5 (cover / chapter / TOC / content / ending) | one variant per visually distinct cluster — count driven by the source | one page per source slide (1:1) |
| Abstraction | High — clean, reusable skeleton | Medium — clusters preserved with cleanup | **Zero** — verbatim copy |
| Authoring placeholders | Yes (`{{TITLE}}`, `{{CONTENT_AREA}}`, …) | Yes | Literal text may remain, but imported native content slots still carry semantic metadata |
| Best for | You want "tone + basic skeleton" to generate brand-new decks later | The source PPTX itself is a customized layout library and every variant matters | Someone else's polished deck is great as-is, you want every page available as a reference |
| Typical use | Building a base brand template | Replicating a 20-variant government briefing layout set | Reusing a 50-page McKinsey-style deck verbatim |
| Requires PPTX source? | No | **Yes** | **Yes** |
| Decoration complexity | Usually simpler | Must preserve sprite-sheet crop structure | Preserves literal geometry while adding explicit layer ownership |

**About sprite sheets**: PPTX-exported assets are often a single large image referenced from multiple slides, each cropping a different region via nested `<svg viewBox=...>` wrappers. In `fidelity` and `mirror` modes this nesting must be preserved — you cannot flatten it to a bare `<image>`, or the crop is lost and the page misaligns. The workflow validates this automatically.

**How mirror is consumed**: the Strategist picks one mirror page per project page, and the Executor copies that complete SVG and edits visible text in place while preserving decoration, sprite crops, geometry, and every `data-pptx-*` structure declaration.

### Step 4 — Validation, registration, and discovery

After generation, both scopes run [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) as a hard gate. What happens next depends on the confirmed output scope:

| Scope | Output | Discovery behavior |
|---|---|---|
| `library` (default) | `skills/ppt-master/templates/<kind>/<id>/` | Register in the matching `layouts_index.json` or `decks_index.json` after validation |
| `project` | Direct `<project>/templates/` bundle; bitmaps in `<project>/images/`; extracted icons in both `<project>/templates/icons/` and `<project>/icons/` | Skip every global index and library README update |

Library registration makes the template **discoverable** — when someone asks "what templates are available?", the AI lists it from the index. To use it in a new project, follow the SKILL.md Step 3 rule: name its directory path in your first message, e.g. `use this template: skills/ppt-master/templates/layouts/<your_template_id>/`. A project-scoped template is intentionally private to that project and is consumed in place through the explicit `<project>/templates/` path.

When a deck/layout template is selected, the Strategist confirmation stage asks how it should be used:

- **adaptive** — choose one template SVG per page; when no Layout fits, keep the same Master and create a new explicit Layout
- **strict** — choose one template SVG per page and keep its Master/Layout/Placeholder contract unchanged

### What a derived template looks like

Library scope (the default) remains a self-contained package:

```
skills/ppt-master/templates/layouts/<your_template_id>/
├── design_spec.md          # design spec; §VI lists every page
├── 01_cover.svg
├── 02_chapter.svg
├── 02_toc.svg              # optional
├── 03_content.svg
├── 03a_content_two_col.svg # variant in fidelity mode
├── 04_ending.svg
├── logo.png                # brand asset
└── bg_pattern.jpg
```

`standard` and `fidelity` SVGs use a unified placeholder convention (`{{TITLE}}`, `{{CHAPTER_TITLE}}`, `{{PAGE_TITLE}}`, `{{CONTENT_AREA}}`, ...) that the Strategist phase fills with content.

A `mirror` template emits one SVG per source slide, named by source order. It may keep literal example text instead of `{{...}}` markers, but imported native slots still carry semantic metadata:

```
skills/ppt-master/templates/layouts/<your_template_id>/
├── design_spec.md          # frontmatter sets replication_mode: mirror; §V Page Roster describes every page in detail
├── 001_cover.svg
├── 002_toc.svg
├── 003_content.svg
├── 004_content.svg
├── ...
├── 049_content.svg
├── 050_ending.svg
└── *.png / *.jpg
```

Project scope writes a thin bundle directly into the initialized project's existing roots. It does not create `<project>/templates/<template_id>/`:

```
projects/<project>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_chapter.svg
│   ├── 03_content.svg
│   ├── 04_ending.svg
│   └── icons/             # package/validation copy
├── images/
│   └── *.png / *.jpg      # SVG references use ../images/<name>
└── icons/
    └── *.svg              # runtime copy of extracted icons
```

### Project-level customization vs global template

Choose the output scope according to ownership:

- **Library scope (`library`, default)** = enter `skills/ppt-master/templates/<kind>/<id>/`, register globally, and make the package available to future projects
- **Project scope (`project`)** = create the same validated template contract directly under `projects/<project>/templates/`, keep its runtime images/icons beside that project, and skip global registration

`/create-template` supports both. Project scope is the safe route when the template exists only to drive the current deck; it still gets the normal brief, explicit Master/Layout metadata, and template validation without polluting the global library. Choose library scope when another project must consume the result.

---

## 3. Template boundaries

Common misconceptions to avoid:

- **A reusable template is a complete SVG reconstruction contract, not a preserved source package.** Every page previews independently, while explicit metadata lets export restore Master/Layout/Slide structure
- **A template is not a "style skin".** It bundles structure (which blocks per page, how information is hierarchized) with style (colors, fonts, decoration). Trying to swap "skin" without structure tends to put the information architecture and the visuals at odds
- **A template does not make content decisions for you.** The Strategist still decides per-page which layout to use and whether to extend a variant. Templates offer candidates, not predetermined results
- **`fidelity` mode is not pixel-perfect copying.** Even with `literal` fidelity, the AI still strips noise and unnecessary repetition — geometry stays, redundancy goes
- **`mirror` mode IS pixel-perfect copying — but it inherits the source's import limitations.** Charts, SmartArt, OLE objects, and EMF / WMF media that don't round-trip through `pptx_template_import.py` will fail the same way in mirror. The flat SVG is the source of truth; if it looks broken in `<workspace>/svg-flat/`, the mirror template will too

---

## Related docs

- [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md) — full workflow spec (AI-facing)
- [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md) — current template catalog
- [`references/template-designer.md`](../skills/ppt-master/references/template-designer.md) — Template_Designer role definition and SVG technical constraints
- [FAQ: how do I create a custom template?](./faq.md) — short FAQ version
