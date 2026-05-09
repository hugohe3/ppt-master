# Templates Guide: Use, Derive, and Boundaries

A PPT Master "template" is a **structure + style** preset bundle: a set of page layout SVGs (cover / chapter / TOC / content / ending and their variants), a `design_spec.md` design specification, and matching assets (logos, backgrounds, decorative imagery). It is **not** a PowerPoint Slide Master, and **not** just a color palette — it is a reusable page-skeleton bundle the workflow can invoke directly.

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
> "用这个模板做汇报：`projects/last_deck/template/`" ✅
> "做一份产品介绍，模板用 `/Users/me/Desktop/our_brand_v3/`" ✅

The AI copies that directory's SVGs, `design_spec.md`, and assets into your project, then proceeds to the Strategist phase. The path can point to anywhere — the built-in library under `skills/ppt-master/templates/layouts/`, a previous project's `template/` folder, or any other location on disk.

### What does NOT trigger the template flow

- **A bare template name without a path**: "use the academic_defense template" / "用 招商银行 模板" / "做一份 google_style 模板的答辩" → free design. The AI does not look the name up. You must give a path.
- **Style descriptions**: "McKinsey style" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → free design. The descriptive words flow into Strategist as a style brief, but no template is copied.
- **Vague intent**: "想用个模板" / "I want a template" with no path → free design.

This is intentional — the AI never makes a fuzzy / interpretive judgment about whether your wording maps to a template, and never resolves a name to a path on your behalf. If you want a template, give the path.

To browse what's available in the built-in library, ask "what templates are available?" — the AI lists names and paths from the discovery index. Listing alone does not enter the template flow; you still need to send back a path to trigger Step 3.

### Template catalog

Full index in [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md), grouped by Brand / Scenario / Government / Special, with primary color and use cases per entry. 17 templates currently shipped, covering Google, Anthropic, China Merchants Bank, PowerChina, CATARC, government blue/red, medical, psychology, pixel-retro and more.

### Free design vs template

Free design is **not** "no style" — the AI designs a fresh visual system **for that specific deck** based on its content. A template **reuses an already-defined structure and style**. Both involve real design work; the difference is whether the style is improvised or preset.

> Rule of thumb: clear content direction + strong brand or scenario constraints (consulting reports, government briefings, defenses) → use a template. Essay-like content where atmosphere matters more (magazine, documentary narrative) → free design usually works better.

### Styles are not templates

A **style** is a description ("minimalist" / "Keynote-style" / "magazine 风") — a few words you type in chat. A **template** is a copy-and-paste asset bundle (SVGs + design_spec + assets) the workflow installs into your project when you give it an explicit directory path.

| | Template | Style |
|---|---|---|
| How invoked | Explicit directory path in your message | Free-form description in your message |
| What happens | Files copied into project; layouts inherit from template SVGs | Words flow to Strategist; color / typography / tone proposed in Eight Confirmations |
| Locked values | Yes — values come from the template's `design_spec.md` | No — Strategist invents values that fit the deck |
| Best for | Brand-locked decks; scenarios with strong visual conventions | When you have a feel in mind but no specific brand commitment |

A style mention may resemble a template name (e.g., "Google style" sounds like the `google_style/` template directory), but they go through different machinery — a template requires a real path the AI can copy from, a style mention is interpretive language. Similar words, different paths in the most literal sense.

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

When you describe a style, the AI doesn't pick a template — it interprets the words and lands them in Layer 2 of confirmation `d` (Style Objective) inside Strategist's Eight Confirmations, which then drives e (color), f (icon), g (typography), and h (image). You confirm or refine. If the style you want happens to match one of our built-in templates (e.g., `academic_defense` / `google_style` / `pixel_retro`), you have a choice: send the template's directory path for locked values, or describe the style for AI-interpreted values that adapt to your deck content.

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

**Strongly recommended: hand over the original `.pptx` file.** The current PPTX import pipeline achieves near-high-fidelity reconstruction — the workflow uses [`pptx_template_import.py`](../skills/ppt-master/scripts/pptx_template_import.py) to read OOXML directly, extracting theme colors, fonts, per-master themes, master/layout structure, placeholder metadata, and reusable image assets. It emits a layered `svg/` view as the machine-readable template source plus a self-contained `svg-flat/` view for visual preview, then hands the package to Template_Designer which rebuilds clean, maintainable SVGs. Covers, chapter dividers, and decoration-heavy pages all reproduce reliably. This is by far the most dependable derivation path today.

You can also design from scratch from a brand guideline: provide a logo, primary color HEX, fonts, tone description, and a few mood references — the AI will design the page skeletons on the spot. This suits brands that don't yet have a finished PPT, only a VI manual.

> **Fallback when no source PPTX exists**: a screenshot set (`cover.png` / `chapter.png` / `content.png` / `closing.png`, ...) still works, but fidelity drops noticeably — decoration, fonts, and layout details all rely on the AI's visual inference. Use `.pptx` whenever you can. Screenshots are better used as annotation alongside a PPTX ("this is the look I want") than as the sole reference.

### Step 2 — The template brief (mandatory confirmation)

The workflow does not silently infer values — before generation it lists these items and waits for your reply:

| Field | Notes |
|-------|-------|
| **Template ID** | Directory / index key. Prefer ASCII slug like `acme_consulting`; non-ASCII names work but must be filesystem-safe |
| **Display name** | Human-readable name for documentation |
| **Category** | One of `brand` / `general` / `scenario` / `government` / `special` |
| **Use cases** | Annual report / consulting / defense / government briefing / ... |
| **Tone summary** | One line, e.g. "modern, restrained, data-driven" |
| **Theme mode** | Light / dark / gradient / ... |
| **Canvas format** | Default `ppt169` (16:9); specify other formats up front |
| **Replication mode** | `standard` (default 5-page roster) / `fidelity` (one variant per visually distinct cluster from a `.pptx` source — count is driven by the source) / `mirror` (1:1 verbatim copy of every source slide, no abstraction, no placeholders) — `fidelity` and `mirror` both require a `.pptx` reference |
| **Visual fidelity** | (required for `standard` / `fidelity` when a reference exists) `literal` (reproduce original geometry / decoration / sprite crops as-is) or `adapted` (use reference for tone and structure but allow design evolution). Cover / chapter / ending are usually `literal`. **Not asked for `mirror`** — mirror is implicitly literal |
| **Keywords** | 3–5 tags for index lookup |
| Theme color / design notes / asset list | Optional — can be auto-extracted from the source |

After confirmation the workflow echoes the finalized brief and emits the marker `[TEMPLATE_BRIEF_CONFIRMED]`. Subsequent steps only run after that marker. **This is a hard gate — no brief, no generation.**

> Why so strict? Because a template is a library asset that future projects will reuse. Getting it right once is far cheaper than regenerating after the fact.

### Step 3 — `standard`, `fidelity`, or `mirror`?

This is the most easily confused decision when deriving a template.

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| Output pages | 5 (cover / chapter / TOC / content / ending) | one variant per visually distinct cluster — count driven by the source | one page per source slide (1:1) |
| Abstraction | High — clean, reusable skeleton | Medium — clusters preserved with cleanup | **Zero** — verbatim copy |
| Placeholders inserted? | Yes (`{{TITLE}}`, `{{CONTENT_AREA}}`, …) | Yes | **No** — Executor edits text in place against the project content |
| Best for | You want "tone + basic skeleton" to generate brand-new decks later | The source PPTX itself is a customized layout library and every variant matters | Someone else's polished deck is great as-is, you want every page available as a reference |
| Typical use | Building a base brand template | Replicating a 20-variant government briefing layout set | Reusing a 50-page McKinsey-style deck verbatim |
| Requires PPTX source? | No | **Yes** | **Yes** |
| Decoration complexity | Usually simpler | Must preserve sprite-sheet (cropped image) structure | Inherits whatever the source had, byte-for-byte |

**About sprite sheets**: PPTX-exported assets are often a single large image referenced from multiple slides, each cropping a different region via nested `<svg viewBox=...>` wrappers. In `fidelity` and `mirror` modes this nesting must be preserved — you cannot flatten it to a bare `<image>`, or the crop is lost and the page misaligns. The workflow validates this automatically.

**How mirror is consumed**: a mirror template carries no `{{}}` placeholders, so the Strategist picks one mirror page per project page (using `design_spec.md §V Page Roster` descriptions to match content), and the Executor copies that mirror SVG and edits the text in place against the project content — preserving all decoration, sprite crops, and geometry. The library asset stays 100% verbatim; per-project edits live in `projects/<project>/svg_output/`.

### Step 4 — Registration and discovery

After generation, the workflow:

1. Runs [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) (hard gate — no entry without passing)
2. Registers the template ID in [`layouts_index.json`](../skills/ppt-master/templates/layouts/layouts_index.json)
3. Syncs the table in [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md)

Registration makes the template **discoverable** — when someone asks "what templates are available?", the AI lists it from the index. To use it in a new project, follow the SKILL.md Step 3 rule: name its directory path in your first message, e.g. `use this template: skills/ppt-master/templates/layouts/<your_template_id>/`.

### What a derived template looks like

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

A `mirror` template emits one SVG per source slide, named by source order, with **no** placeholders inside:

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

### Project-level customization vs global template

Don't confuse the two:

- **Derive a new template** = enter the global library at `skills/ppt-master/templates/layouts/`, available to all future projects
- **Project-level customization** = edit only the SVGs under `projects/<project>/templates/` for this one deck; not registered, no impact elsewhere

`/create-template` is for the former. For the latter, just edit the SVGs in the project directory directly — no workflow needed.

---

## 3. Template boundaries

Common misconceptions to avoid:

- **A template is not a PowerPoint Slide Master.** PPT Master outputs native DrawingML shapes and does not depend on the PowerPoint master mechanism. The template is an SVG skeleton, translated to PPTX shapes at export time
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
