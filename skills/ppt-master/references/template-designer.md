> See shared-standards.md for common technical constraints.

# Template Designer — Template Design Role

## Core Mission

Generate reusable page templates for the **global template library** based on a finalized template brief.

> This is a standalone role: only triggered via the `/create-template` workflow. It is **not** the project-level template selection/customization step in the main PPT generation pipeline.

## Usage

- **Trigger**: `/create-template` workflow
- **Output location**: `templates/layouts/<template_name>/`
- **Input**: finalized template brief (template ID, display name, category, applicable scenarios, tone, theme mode, canvas format, optional reference assets)

---

## Core Template Inventory

| # | Filename | Purpose | Description |
|---|----------|---------|-------------|
| 01 | `01_cover.svg` | Cover | Fixed structure: title, subtitle, date, organization |
| 02 | `02_chapter.svg` | Chapter page | Fixed structure: chapter number, chapter title |
| 03 | `03_content.svg` | Content page | Flexible structure: only defines header/footer; content area freely laid out by AI |
| 04 | `04_ending.svg` | Ending page | Fixed structure: thank-you message, contact info |
| -- | `02_toc.svg` | Table of contents | Optional: TOC title, chapter list (number + title) |

**Design philosophy**: Templates define visual consistency and structural pages; content pages maintain maximum flexibility.

**Naming note**: TOC page keeps `02_toc.svg` naming for template library compatibility and sort order.

### Optional Extension Pages (As Needed)

- Transition / sub-section page (e.g., `05_section_break.svg`)
- Appendix page (e.g., `06_appendix.svg`)
- Disclaimer / confidentiality page (e.g., `07_disclaimer.svg`)

---

## Template Design Specifications

### 1. Must Generate design_spec.md

When creating a global template, a `design_spec.md` must be generated, containing:

```markdown
# [Template Name] - Design Specification

## I. Template Overview (name, use cases, design tone)
## II. Canvas Specification (16:9, 1280x720, viewBox)
## III. Color Scheme (primary, secondary, accent HEX values)
## IV. Typography System (font stack, font size hierarchy)
## V. Page Structure (common layout, decorative design)
## VI. Page Types (4 core page types)
## VII. Layout Modes (recommended)
## VIII. Spacing Specification
## IX. SVG Technical Constraints
## X. Placeholder Specification
```

### 2. Inherit Design Specification

Templates must strictly follow the finalized template brief and the generated `design_spec.md`:
- **Canvas dimensions**: viewBox matches the design spec
- **Color scheme**: Uses primary, secondary, and accent colors from the spec
- **Font plan**: Uses font presets from the spec
- **Layout principles**: Margins and spacing conform to the spec

### 3. Placeholder Markers

Use clear placeholder markers for replaceable content:

```xml
<!-- Text placeholder -->
<text x="80" y="320" fill="#FFFFFF" font-size="48" font-weight="bold">
  {{TITLE}}
</text>

<!-- Content area placeholder (content page only) -->
<rect x="40" y="90" width="1200" height="550" fill="#FFFFFF" rx="8"/>
<text x="640" y="365" text-anchor="middle" fill="#CBD5E1" font-size="16">
  {{CONTENT_AREA}}
</text>
```

### 4. Placeholder Reference

| Placeholder | Purpose | Applicable Template |
|------------|---------|-------------------|
| `{{TITLE}}` | Main title | Cover |
| `{{SUBTITLE}}` | Subtitle | Cover |
| `{{DATE}}` | Date | Cover |
| `{{AUTHOR}}` | Author / Organization | Cover |
| `{{CHAPTER_NUM}}` | Chapter number | Chapter page |
| `{{CHAPTER_TITLE}}` | Chapter title | Chapter page |
| `{{CHAPTER_DESC}}` | Chapter description | Chapter page |
| `{{PAGE_TITLE}}` | Page title | Content page |
| `{{KEY_MESSAGE}}` | Key takeaway | Content page (consulting style) |
| `{{CONTENT_AREA}}` | Content area | Content page |
| `{{SECTION_NAME}}` | Section name | Content page footer |
| `{{SOURCE}}` | Data source | Content page footer |
| `{{PAGE_NUM}}` | Page number | Content page, ending page |
| `{{THANK_YOU}}` | Thank-you message | Ending page |
| `{{ENDING_SUBTITLE}}` | Ending subtitle | Ending page |
| `{{CLOSING_MESSAGE}}` | Closing message | Ending page |
| `{{CONTACT_INFO}}` | Contact info | Ending page |
| `{{COPYRIGHT}}` | Copyright | Ending page |

For TOC pages in **newly created library templates**, use indexed placeholders:

- `{{TOC_ITEM_1_TITLE}}`, `{{TOC_ITEM_1_DESC}}`
- `{{TOC_ITEM_2_TITLE}}`, `{{TOC_ITEM_2_DESC}}`
- ...

Do **not** create new TOC placeholder families such as `{{CHAPTER_01_TITLE}}` for new templates. Existing templates may contain legacy placeholder variants, but new library assets should converge on the indexed TOC contract.

---

## Output Requirements

### File Save Location

```
templates/layouts/<template_name>/
├── design_spec.md     # Design specification (required)
├── 01_cover.svg
├── 02_chapter.svg
├── 02_toc.svg          # Optional
├── 03_content.svg
├── 04_ending.svg
└── *.png / *.jpg       # Image assets (if any)
```

### Template Preview

After each template is generated, provide a brief summary table listing each template's status.

---

## Using Pre-built Template Library (Optional)

If suitable template resources already exist, use them directly instead of generating new ones:

1. **Copy template**: Copy template files to the project's `templates/` directory
2. **Adjust colors**: Modify colors per the project design spec
3. **Customize**: Make project-specific adjustments

This section describes downstream reuse. The `Template_Designer` role itself is responsible for creating or normalizing the reusable library asset first.

**Example library structure** (query `templates/layouts/layouts_index.json`):

```
templates/layouts/
├── exhibit/           # Exhibit style (conclusion-first, data-driven)
├── 科技蓝商务/         # Tech blue business style
└── smart_red/         # Smart red-orange style
```

---

## Phase Completion Checkpoint

```markdown
## Template_Designer Phase Complete

- [x] Read `references/template-designer.md`
- [x] Generated 4 core page templates
- [ ] TOC page template (optional)
- [ ] Optional extension pages (if needed)
- [x] All templates saved to `templates/layouts/<template_name>/`
- [x] Templates follow design spec (colors, fonts, layout)
- [x] Placeholder markers are clear and standardized
- [ ] **Next step**: Validate assets and register the template in `layouts_index.json`
```
