# Templates Guide: Use, Derive, and Boundaries

A PPT Master "template" is a **structure + style** preset bundle: a set of page layout SVGs (cover / chapter / TOC / content / ending and their variants), a `design_spec.md` design specification, and matching assets (logos, backgrounds, decorative imagery). It is **not** a PowerPoint Slide Master, and **not** just a color palette — it is a reusable page-skeleton bundle the workflow can invoke directly.

This guide answers three questions:

1. [How do I use an existing template?](#1-use-an-existing-template)
2. [How do I turn someone else's PPT — or my own brand — into a template? (the focus)](#2-derive-a-new-template-the-focus)
3. [What are the limits of templates?](#3-template-boundaries)

---

## 1. Use an existing template

### How to trigger

The workflow **defaults to free design** — it will not ask whether you want a template and will not proactively suggest one. Templates are opt-in by **exact slug** only.

### What is a slug?

A slug is the unique identifier of a template — the directory name under [`templates/layouts/`](../skills/ppt-master/templates/layouts/) and equivalently the top-level key in [`layouts_index.json`](../skills/ppt-master/templates/layouts/layouts_index.json). All three are the same string. Examples:

| Slug | Directory | Index key |
|---|---|---|
| `mckinsey` | `templates/layouts/mckinsey/` | `"mckinsey"` |
| `academic_defense` | `templates/layouts/academic_defense/` | `"academic_defense"` |
| `招商银行` | `templates/layouts/招商银行/` | `"招商银行"` |
| `中国电建_常规` | `templates/layouts/中国电建_常规/` | `"中国电建_常规"` |

Slugs are case-sensitive and must appear **verbatim** in your message to trigger the template flow.

### How to enter the template flow

Type a message that contains an exact slug, anywhere in the sentence:

> "use the **mckinsey** template for this report" ✅
> "用 **academic_defense** 模板做这份汇报" ✅
> "做一份 **招商银行** 风格的产品介绍" ✅

The AI reads [`layouts_index.json`](../skills/ppt-master/templates/layouts/layouts_index.json), copies the template's SVGs, `design_spec.md`, and assets into your project, then proceeds to the Strategist phase. You can also point at the directory (`templates/layouts/mckinsey/`) and the AI will extract the slug from the path.

### What does NOT trigger the template flow

- **Style descriptions** that aren't slugs: "McKinsey style" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → free design. The descriptive words flow into Strategist as a style brief, but no template is copied.
- **Partial / ambiguous matches**: "中国电建" when the library has both `中国电建_常规` and `中国电建_现代` → free design. The AI does not guess; you can clarify which one if you wanted a template.
- **Vague intent**: "想用个模板" / "I want a template" with no slug → free design.

This is intentional — the AI never makes a fuzzy / interpretive judgment about whether your wording maps to a template. If you want a template, name it by its exact slug.

To browse what's available, ask "what templates are available?" — the AI will list slugs from the index. Listing alone does not enter the template flow; you still need to repeat the chosen slug to trigger Step 3.

### Template catalog

Full index in [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md), grouped by Brand / General / Scenario / Government / Special, with primary color and use cases per entry. 21 templates currently shipped, covering McKinsey, Google, Anthropic, China Merchants Bank, PowerChina, CATARC, government blue/red, medical, psychology, pixel-retro and more.

### Free design vs template

Free design is **not** "no style" — the AI designs a fresh visual system **for that specific deck** based on its content. A template **reuses an already-defined structure and style**. Both involve real design work; the difference is whether the style is improvised or preset.

> Rule of thumb: clear content direction + strong brand or scenario constraints (consulting reports, government briefings, defenses) → use a template. Essay-like content where atmosphere matters more (magazine, documentary narrative) → free design usually works better.

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
| **Replication mode** | `standard` (default 5-page roster) / `fidelity` (preserve every distinct layout from a `.pptx` source) — `fidelity` requires a `.pptx` reference |
| **Visual fidelity** | (required when a reference exists) `literal` (reproduce original geometry / decoration / sprite crops as-is) or `adapted` (use reference for tone and structure but allow design evolution). Cover / chapter / ending are usually `literal` |
| **Keywords** | 3–5 tags for index lookup |
| Theme color / design notes / asset list | Optional — can be auto-extracted from the source |

After confirmation the workflow echoes the finalized brief and emits the marker `[TEMPLATE_BRIEF_CONFIRMED]`. Subsequent steps only run after that marker. **This is a hard gate — no brief, no generation.**

> Why so strict? Because a template is a library asset that future projects will reuse. Getting it right once is far cheaper than regenerating after the fact.

### Step 3 — `standard` or `fidelity`?

This is the most easily confused decision when deriving a template.

| | **standard** | **fidelity** |
|---|---|---|
| Output pages | 5 (cover / chapter / TOC / content / ending) | every distinct layout in the source PPTX is preserved |
| Best for | You want "tone + basic skeleton" to generate brand-new decks later | The source PPTX itself is a richly customized layout library and every variant matters |
| Typical use | Building a base brand template | Replicating a 20-variant government briefing layout set |
| Requires PPTX source? | No | **Yes** |
| Decoration complexity | Usually simpler | Must preserve sprite-sheet (cropped image) structure |

**About sprite sheets**: PPTX-exported assets are often a single large image referenced from multiple slides, each cropping a different region via nested `<svg viewBox=...>` wrappers. In `fidelity` mode this nesting must be preserved — you cannot flatten it to a bare `<image>`, or the crop is lost and the page misaligns. The workflow validates this automatically.

### Step 4 — Registration and discovery

After generation, the workflow:

1. Runs [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) (hard gate — no entry without passing)
2. Registers the template ID in [`layouts_index.json`](../skills/ppt-master/templates/layouts/layouts_index.json)
3. Syncs the table in [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md)

Once registered, any future project can invoke it by saying "use the `<your_template_id>` template".

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

Page SVGs use a unified placeholder convention (`{{TITLE}}`, `{{CHAPTER_TITLE}}`, `{{PAGE_TITLE}}`, `{{CONTENT_AREA}}`, ...) that the Strategist phase fills with content.

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

---

## Related docs

- [`workflows/create-template.md`](../skills/ppt-master/workflows/create-template.md) — full workflow spec (AI-facing)
- [`templates/layouts/README.md`](../skills/ppt-master/templates/layouts/README.md) — current template catalog
- [`references/template-designer.md`](../skills/ppt-master/references/template-designer.md) — Template_Designer role definition and SVG technical constraints
- [FAQ: how do I create a custom template?](./faq.md) — short FAQ version
