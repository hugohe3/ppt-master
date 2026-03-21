---
description: Generate a new PPT layout template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate a complete set of PPT layout templates for the **global template library**.

## Process Overview

```
Gather Info -> Create Directory -> Invoke Template_Designer -> Validate Completeness
```

---

## Step 1: Gather Template Information

Confirm the following with the user:

| Item | Required | Description |
|------|----------|-------------|
| New template name | Yes | English identifier, e.g., `my_company` |
| Template display name | Yes | Human-readable name for documentation |
| Reference source | Optional | Existing project or template path |
| Theme color | Optional | Primary color HEX value (can be auto-extracted from reference) |
| Design style | Optional | Brief description of use cases and design tone |

**If a reference source is provided**, analyze its structure first:

```bash
ls -la "<reference_source_path>"
```

---

## Step 2: Create Template Directory

```bash
mkdir -p "skills/ppt-master/templates/layouts/<new_template_name>"
```

> **Output location**: Global templates go to `skills/ppt-master/templates/layouts/`; project templates go to `projects/<project>/templates/`

---

## Step 3: Invoke Template_Designer Role

**Switch to the Template_Designer role** and generate per role definition:

1. **design_spec.md** — Design specification document
2. **4 core templates** — Cover, chapter, content, ending pages
3. **TOC page (optional)** — `02_toc.svg`

> **Role details**: See [template-designer.md](../references/template-designer.md)

---

## Step 4: Validate Template Completeness

```bash
ls -la "skills/ppt-master/templates/layouts/<new_template_name>"
```

**Checklist**:

- [ ] `design_spec.md` contains complete design specification
- [ ] All 4 core templates present
- [ ] SVG viewBox correct (`0 0 1280 720`)
- [ ] Placeholder format consistent (`{{PLACEHOLDER}}`)

---

## Step 5: Output Confirmation

```markdown
## Template Creation Complete

**Template Name**: <new_template_name> (<display_name>)
**Template Path**: `skills/ppt-master/templates/layouts/<new_template_name>/`

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
3. **Placeholder convention**: Use `{{}}` format

> **Detailed specification**: See [template-designer.md](../references/template-designer.md)
