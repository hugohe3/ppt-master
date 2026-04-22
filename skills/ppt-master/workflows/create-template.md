---
description: Generate a new PPT layout template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate a complete set of reusable PPT layout templates for the **global template library**.

> This workflow is for **library asset creation**, not project-level one-off customization. The output must be reusable by future PPT projects and discoverable from `templates/layouts/layouts_index.json`.

## Process Overview

```
Gather Brief -> Import PPTX References -> Normalize Assets -> Create Directory -> Invoke Template_Designer -> Validate Assets -> Register Index -> Output
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

This helper performs the full PPTX reference preparation in one workspace:

- extracts reusable assets and style metadata
- generates `manifest.json`
- generates `analysis.md`
- generates `master_layout_refs.json`
- generates `master_layout_analysis.md`
- exports each slide to `svg/`
- externalizes large inline bitmap payloads into `assets/`
- generates `reference_svg_selection.json`

It is still a reconstruction aid, not a final direct template conversion.

Use the generated `manifest.json`, `analysis.md`, `master_layout_refs.json`, `master_layout_analysis.md`, exported `assets/`, and `svg/` slide references as internal reference material for template reconstruction.

Then perform an **AI-only asset normalization step** before template generation:

- compare exported original assets such as `image1.png` with `inline_*` assets used by the cleaned slide SVGs
- if an `inline_*` visible image corresponds to an original exported asset, treat the **original asset** as the canonical source
- if an `inline_*` asset has no matching original exported asset, keep it as a derived candidate asset
- if an `inline_*` asset is only used as a mask / alpha helper / auxiliary layer, do **not** promote it to the final template asset set by default
- write the normalization result to `<import_workspace>/normalized_assets.json`

Recommended fields in `normalized_assets.json`:

- canonical asset path
- matched `inline_*` references
- role guess such as `cover_background`, `content_background`, `brand_overlay`, `mask_only`
- whether the asset should enter the final template package

When the reference source is `.pptx`, use the following internal priority order during template creation:

1. `manifest.json`
2. `master_layout_refs.json`
3. `master_layout_analysis.md`
4. `analysis.md`
5. `normalized_assets.json`
6. exported `assets/`
7. cleaned slide SVG references from `svg/`
8. user-provided screenshots or the original PPTX only for visual cross-checking

Interpretation rule:

- `manifest.json` is the source of truth for slide size, theme colors, fonts, background inheritance, and reusable asset inventory
- `master_layout_refs.json` is the source of truth for unique layout/master structure, inherited backgrounds, and slide reuse relationships
- `master_layout_analysis.md` is the compact human-readable summary for quickly understanding reusable master/layout motifs
- `analysis.md` is the compact human-readable summary used to guide page-type selection
- `normalized_assets.json` is the source of truth for which imported assets are canonical and which `inline_*` assets are only derived helpers
- exported `assets/` remain the raw import pool and should not be consumed blindly once normalization exists
- cleaned `svg/` slides are mandatory reference material for layout rhythm, page composition, and fixed decorative structure
- if the remaining cleaned SVG reference pages are `<= 10`, read all of them; if they are `> 10`, read only `10` representative pages
- screenshots remain useful for judging composition and style, but should not override extracted factual metadata unless the import result is clearly incomplete

**Hard gate**:

- Before creating any template file, the agent MUST finish reading all SVG files listed in `reference_svg_selection.json`
- The agent MUST explicitly report the read slide indexes before starting template generation

Do **not** treat the imported PPTX or exported slide SVGs as direct final template assets. The goal is to reconstruct a clean, maintainable PPT Master template package, not to perform 1:1 shape translation.

---

## Step 2: Normalize Imported Assets

When the reference source is `.pptx`, create the normalization artifact before generating the template.

**Required outcome of Step 2**:

- original exported assets and `inline_*` assets have been compared
- canonical assets prefer original exported files when a reliable match exists
- mask-only / helper-only `inline_*` assets are excluded from the final template asset shortlist by default
- `normalized_assets.json` is available for downstream template generation

If no `.pptx` source is involved, this step can be skipped.

---

## Step 3: Create Template Directory

```bash
mkdir -p "skills/ppt-master/templates/layouts/<template_id>"
```

> **Output location**: Global templates go to `skills/ppt-master/templates/layouts/`; project templates go to `projects/<project>/templates/`
>
> The generated directory name must match the final template ID used in `layouts_index.json`.

---

## Step 4: Invoke Template_Designer Role

**Switch to the Template_Designer role** and generate per role definition. The role input is the finalized template brief from Step 1, not a project design spec.

If the reference source is `.pptx`, pass the following internal package to the role:

- finalized template brief from Step 1
- `manifest.json`
- `master_layout_refs.json`
- `master_layout_analysis.md`
- `analysis.md`
- `normalized_assets.json`
- exported `assets/`
- cleaned slide SVG references from `svg/`
- `reference_svg_selection.json`
- optional screenshots, if available

The role should use the import output to anchor objective facts such as theme colors, fonts, reusable backgrounds, and common branding assets, then rebuild the final SVG templates in a simplified, maintainable form.

1. **design_spec.md** — Design specification document
2. **4 core templates** — Cover, chapter, content, ending pages
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

## Step 5: Validate Template Assets

```bash
ls -la "skills/ppt-master/templates/layouts/<template_id>"
```

Run SVG validation on the template directory:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "skills/ppt-master/templates/layouts/<template_id>" --format <canvas_format>
```

**Checklist**:

- [ ] `design_spec.md` contains complete design specification
- [ ] All 4 core templates present
- [ ] If TOC exists, placeholder pattern uses the canonical indexed form
- [ ] SVG viewBox matches the chosen canvas format (for `ppt169`: `0 0 1280 720`)
- [ ] Placeholder names are consistent with the new-template contract and `design_spec.md`
- [ ] Asset files referenced by SVGs actually exist in the template package

This step is a **hard gate**. Do not register the template into the library index until validation passes.

---

## Step 6: Register Template in Library Index

Add a top-level entry to `skills/ppt-master/templates/layouts/layouts_index.json`. The file is a flat map of `template_id → { label, summary, keywords }`:

```json
"<template_id>": {
  "label": "<Human-readable Name>",
  "summary": "<One-sentence description of what this template is for>",
  "keywords": ["<Tag1>", "<Tag2>", "<Tag3>"]
}
```

`layouts_index.json` is the lightweight lookup used when a user explicitly opts into the template flow. The main workflow defaults to free design and does not read this file unless a template trigger fires (see `SKILL.md` Step 3). A template directory that is not registered here will not be discoverable by that flow.

Also sync the summary table in `templates/layouts/README.md` (the human-facing index with categories, primary colors, and detailed tone).

---

## Step 7: Output Confirmation

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
