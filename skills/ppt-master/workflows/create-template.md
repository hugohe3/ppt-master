---
description: Generate a new PPT layout template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate a complete set of reusable PPT layout templates for the **global template library**.

> This workflow is for **library asset creation**, not project-level one-off customization. The output must be reusable by future PPT projects and discoverable from `templates/layouts/layouts_index.json`.

## Process Overview

```
Gather Brief -> Import PPTX References -> Create Directory -> Invoke Template_Designer -> Validate Assets -> Register Index -> Output
```

---

## Step 1: Gather Template Information

Confirm the following with the user:

| Item | Required | Description |
|------|----------|-------------|
| New template ID | Yes | Template directory / index key. Prefer ASCII slug such as `my_company`; if using a Chinese brand name, it must be filesystem-safe and match `layouts_index.json` exactly |
| Template display name | Yes | Human-readable name for documentation |
| Category | Yes | One of `brand` / `general` / `scenario` / `government` / `special` |
| Applicable scenarios | Yes | Typical use cases, such as annual report / defense / government briefing |
| Tone summary | Yes | Short tone description for recommendation, such as `Modern, restrained, data-driven` |
| Theme mode | Yes | Theme description for recommendation, such as `Light theme (white background + blue accent)` |
| Canvas format | Yes | Default `ppt169`; if another format is needed, specify it explicitly before generation |
| Replication mode | Yes | `standard` (default, 5-page roster) or `fidelity` (preserve every distinct layout from a `.pptx` source); `fidelity` requires a `.pptx` reference source |
| Reference source | Optional | Existing project, screenshot folder, or `.pptx` template file path |
| Theme color | Optional | Primary color HEX value (can be auto-extracted from reference) |
| Design style | Optional | Additional style notes, decorative language, brand cues |
| Assets list | Optional | Logos / background textures / reference images to include in the template package |
| Keywords | Yes | 3–5 short tags for `layouts_index.json` lookup (e.g., `McKinsey`, `Consulting`, `Structured`) |

**Required outcome of Step 1**:

- The template is clearly positioned as a **global library template**
- The canvas format is fixed before SVG generation
- The template metadata is complete enough to register into `layouts_index.json`

**If a reference source is provided**, analyze its structure first:

```bash
ls -la "<reference_source_path>"
```

If the reference source is a `.pptx` template file, use the unified preparation helper:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py "<reference_template.pptx>"
```

This helper reads OOXML directly via `pptx_to_svg` and produces, in one workspace:

- `manifest.json` — slide size, theme colors, fonts, asset inventory
- `analysis.md` — page-type guidance summary
- `master_layout_refs.json` / `master_layout_analysis.md` — master/layout structure and inheritance
- `assets/` — extracted reusable image assets
- `svg/` — shape-level SVG per slide (real `<text>`, `<image>`, geometry)

It is a reconstruction aid, not a final direct template conversion.

When the reference source is `.pptx`, use the following internal priority order during template creation:

1. `manifest.json`
2. `master_layout_refs.json`
3. `master_layout_analysis.md`
4. `analysis.md`
5. exported `assets/`
6. cleaned slide SVG references from `svg/`
7. user-provided screenshots or the original PPTX only for visual cross-checking

Interpretation rule:

- `manifest.json` is the source of truth for slide size, theme colors, fonts, background inheritance, and reusable asset inventory
- `master_layout_refs.json` is the source of truth for unique layout/master structure, inherited backgrounds, and slide reuse relationships
- `master_layout_analysis.md` is the compact human-readable summary for quickly understanding reusable master/layout motifs
- `analysis.md` is the compact human-readable summary used to guide page-type selection
- exported `assets/` are the canonical reusable image pool — `<image>` references in `svg/` already point at these files directly
- cleaned `svg/` slides are mandatory reference material for layout rhythm, page composition, and fixed decorative structure; read **every** exported page regardless of slide count
- screenshots remain useful for judging composition and style, but should not override extracted factual metadata unless the import result is clearly incomplete

**Hard gate**:

- Before creating any template file, the agent MUST finish reading every SVG file under `<import_workspace>/svg/`
- The agent MUST explicitly report the read slide indexes before starting template generation

Do **not** treat the imported PPTX or exported slide SVGs as direct final template assets. The goal is to reconstruct a clean, maintainable PPT Master template package, not to perform 1:1 shape translation.

---

## Step 2: Create Template Directory

```bash
mkdir -p "skills/ppt-master/templates/layouts/<template_id>"
```

> **Output location**: Global templates go to `skills/ppt-master/templates/layouts/`; project templates go to `projects/<project>/templates/`
>
> The generated directory name must match the final template ID used in `layouts_index.json`.

---

## Step 3: Invoke Template_Designer Role

**Switch to the Template_Designer role** and generate per role definition. The role input is the finalized template brief from Step 1, not a project design spec.

If the reference source is `.pptx`, pass the following internal package to the role:

- finalized template brief from Step 1
- `manifest.json`
- `master_layout_refs.json`
- `master_layout_analysis.md`
- `analysis.md`
- exported `assets/`
- cleaned slide SVG references from `svg/`
- optional screenshots, if available

The role should use the import output to anchor objective facts such as theme colors, fonts, reusable backgrounds, and common branding assets, then rebuild the final SVG templates in a simplified, maintainable form.

1. **design_spec.md** — Design specification document, with §VI listing the page roster
2. **Page roster** — `standard` mode: `01_cover`, `02_chapter`, `03_content`, `04_ending`; `fidelity` mode: standard set + variant pages (`02a_chapter_*`, `03a_content_*`, ...) and extension pages (`05_section_break`, `06_appendix`, ...) per `manifest.json` clusters
3. **TOC page (optional)** — `02_toc.svg`
4. **Template assets (optional)** — Logos / PNG / JPG / reference SVG needed by the template package

> **Role details**: See [template-designer.md](../references/template-designer.md)

**New-template placeholder contract (mandatory for newly created library templates)**:

- Cover: `{{TITLE}}`, `{{SUBTITLE}}`, `{{DATE}}`, `{{AUTHOR}}`
- Chapter: `{{CHAPTER_NUM}}`, `{{CHAPTER_TITLE}}`
- Content: `{{PAGE_TITLE}}`, `{{CONTENT_AREA}}`, `{{PAGE_NUM}}`
- Ending: `{{THANK_YOU}}`, `{{CONTACT_INFO}}`
- TOC: use indexed placeholders such as `{{TOC_ITEM_1_TITLE}}` and optional `{{TOC_ITEM_1_DESC}}`

**Avoid** introducing one-off placeholder families such as `{{CHAPTER_01_TITLE}}` for new templates. If an extension placeholder is truly required, define it explicitly in `design_spec.md` and keep the naming pattern consistent.

---

## Step 4: Validate Template Assets

```bash
ls -la "skills/ppt-master/templates/layouts/<template_id>"
```

Run SVG validation on the template directory:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "skills/ppt-master/templates/layouts/<template_id>" --format <canvas_format>
```

**Checklist**:

- [ ] `design_spec.md` contains complete design specification, with §VI listing every emitted page
- [ ] Every page declared in `design_spec.md §VI` exists as an SVG file in the template directory (and vice versa — no orphan files)
- [ ] Variant filenames follow the letter-suffix convention (e.g. `03a_content_two_col.svg`); variants reuse the parent type's placeholder set
- [ ] If TOC exists, placeholder pattern uses the canonical indexed form
- [ ] SVG viewBox matches the chosen canvas format (for `ppt169`: `0 0 1280 720`)
- [ ] Placeholder names are consistent with the new-template contract and `design_spec.md`
- [ ] Asset files referenced by SVGs actually exist in the template package

This step is a **hard gate**. Do not register the template into the library index until validation passes.

---

## Step 5: Register Template in Library Index

Add a top-level entry to `skills/ppt-master/templates/layouts/layouts_index.json`. The file is a flat map of `template_id → { label, summary, keywords, pages }`:

```json
"<template_id>": {
  "label": "<Human-readable Name>",
  "summary": "<One-sentence description of what this template is for>",
  "keywords": ["<Tag1>", "<Tag2>", "<Tag3>"],
  "pages": ["01_cover", "02_chapter", "02_toc", "03_content", "04_ending"]
}
```

`pages` lists every layout SVG (without the `.svg` suffix) the template ships, so downstream consumers can see the full roster — especially for `fidelity`-mode templates that include variant pages such as `03a_content_two_col`.

`layouts_index.json` is the lightweight lookup used when a user explicitly opts into the template flow. The main workflow defaults to free design and does not read this file unless a template trigger fires (see `SKILL.md` Step 3). A template directory that is not registered here will not be discoverable by that flow.

Also sync the summary table in `templates/layouts/README.md` (the human-facing index with categories, primary colors, and detailed tone).

---

## Step 6: Output Confirmation

```markdown
## Template Creation Complete

**Template Name**: <template_id> (<display_name>)
**Template Path**: `skills/ppt-master/templates/layouts/<template_id>/`
**Category**: <category>
**Canvas Format**: <canvas_format>
**Index Registration**: Done

### Files Included

| File | Status |
|------|--------|
| `design_spec.md` | Done |
| `01_cover.svg` | Done |
| `02_chapter.svg` | Done |
| `03_content.svg` | Done |
| `04_ending.svg` | Done |
| `02_toc.svg` | Optional |
```

---

## Color Scheme Quick Reference

| Style | Primary Color | Use Cases |
|-------|---------------|-----------|
| Tech Blue | `#004098` | Certification, evaluation |
| McKinsey | `#005587` | Strategic consulting |
| Government Blue | `#003366` | Government projects |
| Business Gray | `#2C3E50` | General business |

---

## Notes

1. **SVG technical constraints**: See the technical constraints section in [template-designer.md](../references/template-designer.md)
2. **Color consistency**: All SVG files must use the same color scheme
3. **Placeholder convention**: Use `{{}}` format and the canonical new-template placeholder contract above
4. **Discovery requirement**: New templates must be added to `layouts_index.json`, otherwise they will not be discoverable when a user opts into the template flow

> **Detailed specification**: See [template-designer.md](../references/template-designer.md)
