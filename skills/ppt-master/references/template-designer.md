> See shared-standards.md for common technical constraints.

# Template Designer — Template Design Role

## Core Mission

Generate reusable page templates for the **global template library** based on a finalized template brief.

> This is a standalone role: only triggered via the `/create-template` workflow. It is **not** the project-level template selection/customization step in the main PPT generation pipeline.

## Usage

- **Trigger**: `/create-template` workflow
- **Output location**: `templates/layouts/<template_name>/`
- **Input**: finalized template brief (template ID, display name, category, applicable scenarios, tone, theme mode, canvas format, optional reference assets)

When the workflow provides a PPTX reference source, the effective input package comes from the unified `pptx_template_import.py` preparation workspace and becomes:

- finalized template brief
- `manifest.json` — single source of truth (slide size, theme, assets, layouts, masters, slides, page-type candidates)
- `summary.md` — short orientation digest derived from manifest.json
- exported `assets/`
- `svg/master_*.svg` / `svg/layout_*.svg` — every master / layout in the deck rendered once as standalone SVG, including ones no sample slide references (template packages often ship more design surfaces than the embedded samples exercise)
- `svg/slide_NN.svg` — each slide's own shapes only; master / layout decoration is **not** inlined here
- `svg/inheritance.json` — which layout / master each slide consumes
- `svg-flat/slide_NN.svg` — companion view; each slide is self-contained so you can preview or screenshot a single page without losing the surrounding chrome. Use it as a sanity check for "what would PowerPoint actually show", not as an authoring source — the master/layout chrome will be duplicated across every flat slide.
- optional screenshots for visual cross-checking

Input priority for PPTX-backed template creation:

1. `manifest.json` for all factual metadata (theme, assets, unique layout/master structure, slide reuse, page-type guidance)
2. `svg/master_*.svg` + `svg/layout_*.svg` — the **primary source for the deck's shared visual language**: backgrounds, page chrome, decorative bars, recurring brand motifs. These are what the new template's fixed structure should adopt or reinterpret. Read these before any slide SVG.
3. `svg/inheritance.json` for confirming which slide uses which layout / master
4. exported `assets/` for reusable visual resources
5. `svg/slide_NN.svg` — each slide's unique content, useful for judging composition rhythm and content density (not for fixed structure)
6. `summary.md` only as a fast scan; never as the canonical fact source
7. screenshots / original PPTX only for style verification

---

## Page Roster

The output page set is determined by **replication mode**, declared in the Step 1 brief:

| Mode | When to use | Roster |
|------|-------------|--------|
| `standard` (default) | Most templates — clean, reusable, balanced coverage | `01_cover`, `02_chapter`, `03_content`, `04_ending`, optional `02_toc` |
| `fidelity` | User explicitly wants strict replication of a source PPTX | Standard roster + one variant per distinct layout cluster found in `manifest.json` |

### Standard mode

| # | Filename | Purpose | Description |
|---|----------|---------|-------------|
| 01 | `01_cover.svg` | Cover | Fixed structure: title, subtitle, date, organization |
| 02 | `02_chapter.svg` | Chapter page | Fixed structure: chapter number, chapter title |
| 03 | `03_content.svg` | Content page | Flexible structure: only defines header/footer; content area freely laid out by AI |
| 04 | `04_ending.svg` | Ending page | Fixed structure: thank-you message, contact info |
| -- | `02_toc.svg` | Table of contents | Optional: TOC title, chapter list (number + title) |

**Design philosophy**: Templates define visual consistency and structural pages; content pages maintain maximum flexibility.

**Naming note**: TOC page keeps `02_toc.svg` naming for template library compatibility and sort order.

### Fidelity mode

When the brief sets `Replication mode: fidelity`, derive the page roster from `manifest.json` page-type clusters and emit one SVG per distinct visual cluster.

**Variant naming**: append a lowercase letter suffix to the parent type's index, preserving sort order:

| Parent type | Example variants |
|-------------|------------------|
| Chapter | `02a_chapter_full.svg`, `02b_chapter_minimal.svg` |
| Content | `03a_content_two_col.svg`, `03b_content_data_card.svg`, `03c_content_quote.svg` |
| Ending | `04a_ending_thanks.svg`, `04b_ending_contact.svg` |

Extension page types beyond the canonical four (transition / appendix / disclaimer / divider) take the next free index: `05_section_break.svg`, `06_appendix.svg`, `07_disclaimer.svg`.

**Roster decision**:

- Cluster slides from `manifest.json` by `pageType` + visual structure (column count, hero-image vs. icon-grid vs. quote, etc.)
- One SVG per cluster — do **not** emit a variant for a cluster represented by a single source slide unless that slide is structurally distinct from existing variants
- Cap at 8 content variants per template; collapse near-duplicates into the closest existing variant
- Record every emitted page in `design_spec.md §VI` and in the `pages` field of the `layouts_index.json` entry (auto-collected by `register_template.py`)

> Variants reuse the parent type's placeholder set — see §4 (Placeholder Reference) below.

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
## VI. Page Roster (one row per emitted SVG, with replication mode and cluster source)
## VII. Layout Modes (recommended)
## VIII. Spacing Specification
## IX. SVG Technical Constraints
## X. Placeholder Specification
```

### 2. Inherit Design Specification

Templates must strictly follow the finalized template brief and the generated `design_spec.md`:
- **Canvas dimensions**: viewBox matches the design spec
- **Color scheme**: Uses primary, secondary, and accent colors from the spec
- **Font plan**: Uses the per-role font families declared in the spec
- **Layout principles**: Margins and spacing conform to the spec

If PPTX import output exists:
- Prefer imported theme colors and fonts over visually guessed values
- Reuse exported `assets/` images directly — `<image>` references in `svg/` already point at canonical files
- Treat page-type candidates from `manifest.pageTypeCandidates` as hints, not guarantees

**Precondition**:

- When PPTX import output is provided, do not generate any template SVG or `design_spec.md` until every file under `<import_workspace>/svg/` has been read — including `master_*.svg`, `layout_*.svg`, and every `slide_*.svg`
- Before template generation begins, explicitly report the read slide indexes

### 2.1 PPTX Import Simplification Rule

The imported PPTX is a **reference source**, not a direct conversion target.

Do:
- preserve brand assets, recurring backgrounds, and stable structural motifs
- rebuild the layout into a clean SVG structure aligned with PPT Master constraints
- simplify repeated decorative fragments into a smaller number of maintainable SVG elements
- use a background image asset when the original decorative layer is too complex to recreate cleanly
- use cleaned slide SVG references to inspect composition, spacing, text hierarchy, and fixed decorative structure only after factual metadata has been anchored
- read every reference SVG under `svg/` — `master_*.svg`, `layout_*.svg`, and every `slide_*.svg` regardless of slide count. Master / layout files describe the deck's shared visual language (read first); slide files describe per-page content (read after). Partial coverage drops template fidelity.
- rename adopted assets to semantic names (`cover_bg.png`, `brand_emblem.png`) rather than carrying raw `image3.png` into the final template

Do not:
- attempt 1:1 translation of every PowerPoint shape, group, shadow, or decorative fragment
- mirror PPT-specific complexity when it makes the resulting SVG brittle or hard to edit
- introduce dense low-value vector detail that does not materially improve template reuse

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

### 4. Placeholder Reference (canonical convention, overridable per template)

This is the **default vocabulary** used across the library. Newly created templates SHOULD prefer these names so projects that consume the library find familiar slots; designers MAY substitute or extend them when a style genuinely needs different vocabulary (e.g. consulting decks lead with `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`; a brand cover may need `{{BRAND_LOGO}}`).

`svg_quality_checker.py --template-mode` emits **advisory warnings** when a page lacks the conventional placeholder for its type. To silence those warnings — and document the template's actual contract — declare a `placeholders:` map in `design_spec.md` frontmatter:

```yaml
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LOGO}}"]
  03_content: ["{{KEY_MESSAGE}}", "{{CONTENT_AREA}}"]
  03a_content_dual_col: []   # explicitly assert "no required placeholders"
```

| Placeholder | Purpose | Applicable page | Convention role |
|------------|---------|-------------------|--------|
| `{{TITLE}}` | Main title | Cover | Default |
| `{{SUBTITLE}}` | Subtitle | Cover | Default |
| `{{DATE}}` | Date | Cover | Default |
| `{{AUTHOR}}` | Author / Organization | Cover | Default |
| `{{CHAPTER_NUM}}` | Chapter number | Chapter page | Default |
| `{{CHAPTER_TITLE}}` | Chapter title | Chapter page | Default |
| `{{CHAPTER_DESC}}` | Chapter description | Chapter page | Optional |
| `{{PAGE_TITLE}}` | Page title | Content page | Default |
| `{{CONTENT_AREA}}` | Content area | Content page | Default |
| `{{PAGE_NUM}}` | Page number | Content page, ending page | Default |
| `{{KEY_MESSAGE}}` | Key takeaway | Content page (consulting style) | Style-specific |
| `{{SECTION_NAME}}` | Section name | Content page footer | Optional |
| `{{SOURCE}}` | Data source | Content page footer | Optional |
| `{{THANK_YOU}}` | Thank-you message | Ending page | Default |
| `{{CONTACT_INFO}}` | Contact info | Ending page | Default |
| `{{ENDING_SUBTITLE}}` | Ending subtitle | Ending page | Optional |
| `{{CLOSING_MESSAGE}}` | Closing message | Ending page | Style-specific |
| `{{COPYRIGHT}}` | Copyright | Ending page | Optional |

For TOC pages in **newly created library templates**, use indexed placeholders:

- `{{TOC_ITEM_1_TITLE}}`, `{{TOC_ITEM_1_DESC}}`
- `{{TOC_ITEM_2_TITLE}}`, `{{TOC_ITEM_2_DESC}}`
- ...

Do **not** create new TOC placeholder families such as `{{CHAPTER_01_TITLE}}` for new templates. Existing templates may contain legacy placeholder variants, but new library assets should converge on the indexed TOC contract.

Variants reuse their parent type's placeholder set by default: every `03*_content*.svg` shares the content placeholder list above, unless the spec frontmatter declares an override for that specific stem.

When rebuilding from imported PPTX references, placeholder insertion takes priority over visual mimicry. If the original layout leaves insufficient room for canonical placeholders, adjust the layout instead of inventing one-off placeholder families — or, if the deviation is intentional and meaningful, declare it in frontmatter.

---

## Output Requirements

### File Save Location

Standard mode (default):

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

Fidelity mode adds variants and extension pages, e.g.:

```
templates/layouts/<template_name>/
├── design_spec.md
├── 01_cover.svg
├── 02a_chapter_full.svg
├── 02b_chapter_minimal.svg
├── 02_toc.svg
├── 03a_content_two_col.svg
├── 03b_content_data_card.svg
├── 03c_content_quote.svg
├── 04_ending.svg
├── 05_section_break.svg
└── *.png / *.jpg
```

### Template Preview

After each template is generated, provide a brief summary table listing each template's status.

If the template is based on PPTX import output, briefly note:
- which extracted assets were reused directly
- which complex original decorations were intentionally simplified
- whether any page-type mapping required judgment beyond the import heuristic

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
- [x] Replication mode confirmed: `standard` | `fidelity`
- [x] Every page listed in `design_spec.md §VI` saved to `templates/layouts/<template_name>/`
- [x] Variant naming follows the letter-suffix convention; variants reuse parent placeholder contract
- [x] Templates follow design spec (colors, fonts, layout)
- [x] Placeholder markers are clear and standardized
- [ ] **Next step**: Validate assets and register the template in `layouts_index.json` (include `pages` field)
```
