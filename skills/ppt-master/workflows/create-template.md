---
description: Generate a new PPT layout template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate a complete set of reusable PPT layout templates for the **global template library**.

> This workflow is for **library asset creation**, not project-level one-off customization. The output must be reusable by future PPT projects and discoverable from `templates/layouts/layouts_index.json`.

## Process Overview

```
Gather Brief -> Create Directory -> Invoke Template_Designer -> Validate Assets -> Register Index -> Output
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
| Reference source | Optional | Existing project or template path |
| Theme color | Optional | Primary color HEX value (can be auto-extracted from reference) |
| Design style | Optional | Additional style notes, decorative language, brand cues |
| Assets list | Optional | Logos / background textures / reference images to include in the template package |
| Quick lookup tags | Optional | Tags used in `layouts_index.json > quickLookup`, such as `technology`, `finance`, `academic` |

**Required outcome of Step 1**:

- The template is clearly positioned as a **global library template**
- The canvas format is fixed before SVG generation
- The template metadata is complete enough to register into `layouts_index.json`

**If a reference source is provided**, analyze its structure first:

```bash
ls -la "<reference_source_path>"
```

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

## Step 4: Validate Template Assets

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

## Step 5: Register Template in Library Index

Update `skills/ppt-master/templates/layouts/layouts_index.json`:

- `meta.total`
- `meta.updated`
- the correct `categories.<category>.layouts` entry
- the appropriate `quickLookup` entries
- the new `layouts.<template_id>` metadata block

`layouts_index.json` is the **source of truth** for template discovery in the main PPT generation workflow. A template directory that is not registered here is considered incomplete.

If the human-facing `templates/layouts/README.md` summary table is maintained manually, sync it after updating the JSON index. The JSON index takes priority.

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
4. **Discovery requirement**: New templates must be added to `layouts_index.json`, otherwise the main workflow cannot recommend them

> **Detailed specification**: See [template-designer.md](../references/template-designer.md)
