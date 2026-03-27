# Page Layout Template Library (20 Templates)

Pre-built PPT page layout templates supporting multiple styles and use cases.

- **Full Index**: [README.md](./README.md) (human browsing)
- **JSON Index**: [layouts_index.json](./layouts_index.json) (AI / programmatic lookup — preferred)

> **AI / Programmatic recommendation**: Prefer reading `layouts_index.json`; use this README for human browsing and quick comparison.

---

## Quick Template Index

| Template Name | Category | Use Cases | Primary Color | Design Tone |
|---------------|----------|-----------|---------------|-------------|
| `google_style` | Brand | Annual reports, tech sharing, data presentation | Google Four Colors `#4285F4` `#EA4335` `#FBBC04` `#34A853` | Modern clean, data-driven, ample whitespace |
| `mckinsey` | Brand | Strategic consulting, executive reports, investment analysis | McKinsey Blue `#005587` | Structured thinking, minimalist premium, MECE principle |
| `anthropic` | Brand | AI tech sharing, developer conferences, product launches | Anthropic Orange `#D97757` | Tech-forward, conclusion-first, dark cover |
| `中汽研_常规` | Brand | Product certification, evaluation & testing | Deep Blue `#004098` | [Standard] Professional authority, consulting style |
| `中汽研_商务` | Brand | Business visits, technical exchanges | Blue Gradient `#003366` | [Business] Modern tech, composed and sophisticated |
| `中汽研_现代` | Brand | Strategic launches, future tech | Deep Blue `#001529` | [Future] Future Tech, neon glow |
| `中国电建_常规` | Brand | Power & energy, engineering, state-owned enterprise reports | PowerChina Blue `#00418D` | Craftsmanship, steady and reliable |
| `中国电建_现代` | Brand | International engineering, premium roadshows, tech innovation | Deep Sea Blue `#001F45` | [Modern] Grand narrative, digital tech |
| `招商银行` | Brand | Premium reports, VIP services, annual reports | CMB Red `#C41230` | Minimalist luxury, financial texture, borderless |
| `exhibit` | General | Exhibit-driven strategic reports, executive presentations, board briefings | Gradient top bar + Gold accents | Conclusion-first, data-driven, confidential |
| `academic_defense` | Scenario | Thesis defense, academic reports, grant proposals | Deep Blue + Red accents | Clear hierarchy, academic standards |
| `psychology_attachment` | Scenario | Psychotherapy training, counseling lectures | Blue-green gradient + Colorful semantic colors | Warm professional, therapeutic feel |
| `medical_university` | Scenario | Medical reports, case discussions, research presentations | Medical Blue `#0066B3` | Professional rigorous, life-affirming |
| `government_red` | Government/Enterprise | Government work reports, party-building presentations | Government Red `#8B0000` | Solemn authority, grand and imposing |
| `government_blue` | Government/Enterprise | Smart cities, open governance, digital transformation | Tech Blue `#0050B3` | Modern tech, rigorous and rational |
| `ai_ops` | Government/Enterprise | Telecom AI ops, IT system overview, digital intelligence solutions | Telecom Red `#C00000` + Blue `#2E75B6` | High information density, modular layout, telecom style |
| `pixel_retro` | Special | Git/tech introductions, retro gaming themes | Neon colors `#00FF41` `#FF0080` | Pixel art, cyberpunk |
| `科技蓝商务` | General | Corporate reports, product launches, proposals | Tech Blue `#0078D7` | Tech, business, professional, clean |
| `smart_red` | General | Tech company profiles, education solutions | Smart Red-Orange `#DE3545` | Modern, vibrant, geometric |
| `重庆大学` | Scenario | Academic defense, research presentations | CQU Blue `#006BB7` | Academic solidity, mountain-city character |
---

## Template Categories

### 1. Brand Style Templates

Templates mimicking **specific well-known brands/institutions** with their exclusive design style.
> **Characteristics**: Distinctive brand identity (specific logos, color schemes, VI standards), suitable for internal or external presentations of that organization. Examples: Google, McKinsey, PowerChina.

| Template | Description |
|----------|-------------|
| `google_style` | Google Material Design style, four-color brand identity |
| `mckinsey` | McKinsey consulting style, data-driven and structured |
| `anthropic` | Anthropic AI style, dark tech-forward aesthetic |
| `中汽研_常规` | CATARC standard style (v1), suitable for certification and evaluation |
| `中汽研_商务` | CATARC business style (v2), modern tech business, composed and sophisticated |
| `中汽研_现代` | CATARC modern style (v3 Future), Future Tech style, deep blue + neon cyan |
| `中国电建_常规` | PowerChina standard style (v1), suitable for power, energy, and engineering SOEs |
| `中国电建_现代` | PowerChina modern style (v2), emphasis on grand narrative and digital tech |
| `招商银行` | China Merchants Bank v2.0, minimalist luxury, borderless open layout |

### 2. General Style Templates

Universal business styles not tied to any specific brand, broadly applicable.

| Template | Description |
|----------|-------------|
| `exhibit` | Exhibit-driven style, conclusion-first layout with Exhibit takeaway bar, gradient top bar, grid decoration |
| `科技蓝商务` | Tech business style, rigorous and professional, hexagonal texture |
| `smart_red` | Smart red-orange business style, modern and vibrant, geometric cutaway design |

### 3. Scenario-Specific Templates

Designed for **specific use cases**, with content structures tailored to scenario requirements.

| Template | Description |
|----------|-------------|
| `academic_defense` | Academic defense, clear research content hierarchy |
| `psychology_attachment` | Psychotherapy theme, warm and professional color palette |
| `medical_university` | Hospital / medical university template, suitable for medical reports |
| `重庆大学` | Chongqing University template, blending mountain-city layered imagery with modern academic style |

### 4. Government & Enterprise Templates

Industry-standard designs for **government agencies and general state-owned enterprises**.
> **Distinction**: Unlike brand styles, these are not targeted at specific organizations but provide templates matching the common aesthetic preferences of government/SOE contexts (e.g., official document red, smart governance blue).

| Template | Description |
|----------|-------------|
| `government_red` | Red government style, suitable for government work reports, party-building events |
| `government_blue` | Blue government style, suitable for smart cities, digital governance reports |
| `ai_ops` | Enterprise digital intelligence style, telecom AI ops architecture, high-density reports (includes `reference_style.svg` style reference) |

### 5. Special Style Templates

Unconventional visual styles for specific creative scenarios.

| Template | Description |
|----------|-------------|
| `pixel_retro` | Pixel retro style, cyberpunk / gaming themes |

> **Design philosophy**: Style and scenario are **orthogonal** concepts. Scenario templates define content structure; style templates define visual presentation. In theory, scenario templates can be combined with different styles.

---

## Template File Structure

Each template should contain the following standard files (TOC page is optional):

| Filename | Required | Purpose | Description |
|----------|----------|---------|-------------|
| `design_spec.md` | Yes | Design specification | Complete color, typography, and layout specs |
| `01_cover.svg` | Yes | Cover page | Title, subtitle, date, organization |
| `02_toc.svg` | Optional | Table of contents | Chapter list, navigation |
| `02_chapter.svg` | Yes | Chapter page | Chapter number, chapter title |
| `03_content.svg` | Yes | Content page | Fixed header/footer, flexible content area |
| `04_ending.svg` | Yes | Ending page | Thank-you message, contact info |

> **Design philosophy**: Templates define visual consistency and structural pages; content pages maintain maximum flexibility, letting AI determine layout based on actual content.

---

## design_spec.md Standard Structure

All template design specification documents should follow this chapter structure:

```markdown
# [Template Name] - Design Specification

> One-line description of applicable scenarios

## I. Template Overview
## II. Canvas Specification
## III. Color Scheme
## IV. Typography System
## V. Page Structure
## VI. Page Types
## VII. Layout Modes (Recommended)
## VIII. Spacing Specification
## IX. SVG Technical Constraints
## X. Placeholder Specification
## XI. Usage Guide (Recommended)
```

---

## Placeholder Specification

Templates use `{{PLACEHOLDER}}` format to mark replaceable content:

> For **newly created library templates**, use the canonical placeholder contract below. Some existing templates still contain legacy placeholder variants; those should be treated as historical exceptions rather than the standard for new assets.

### General Placeholders

| Placeholder | Purpose | Applicable Pages |
|-------------|---------|-----------------|
| `{{TITLE}}` | Main title | Cover |
| `{{SUBTITLE}}` | Subtitle | Cover |
| `{{DATE}}` | Date | Cover, Ending |
| `{{AUTHOR}}` | Author / Organization (Chinese) | Cover |
| `{{AUTHOR_EN}}` | Author / Organization (English) | Cover |

### Chapter-Related

| Placeholder | Purpose | Applicable Pages |
|-------------|---------|-----------------|
| `{{CHAPTER_NUM}}` | Chapter number | Chapter, Content |
| `{{CHAPTER_TITLE}}` | Chapter title | Chapter |
| `{{CHAPTER_TITLE_EN}}` | Chapter English subtitle | Chapter |

### Content Page

| Placeholder | Purpose | Applicable Pages |
|-------------|---------|-----------------|
| `{{PAGE_TITLE}}` | Page title | Content |
| `{{CONTENT_AREA}}` | Content area placeholder | Content |
| `{{PAGE_NUM}}` | Page number | Content, Ending |
| `{{SOURCE}}` | Data source | Content footer |

### Table of Contents

| Placeholder | Purpose |
|-------------|---------|
| `{{TOC_ITEM_1_TITLE}}` ~ `{{TOC_ITEM_N_TITLE}}` | TOC item titles |
| `{{TOC_ITEM_1_DESC}}` ~ `{{TOC_ITEM_N_DESC}}` | Optional TOC item descriptions |
| `{{TOC_ITEM_1}}` ~ `{{TOC_ITEM_N}}` | Legacy simple TOC items; do not use for new templates unless no description field is needed |

### Ending Page

| Placeholder | Purpose |
|-------------|---------|
| `{{THANK_YOU}}` | Thank-you message |
| `{{ENDING_SUBTITLE}}` | Ending page subtitle |
| `{{CLOSING_MESSAGE}}` | Closing message |
| `{{CONTACT_INFO}}` | Contact information |

---

## Usage

### Copy from Template Library to Project

```bash
# Copy exhibit style template to project
cp templates/layouts/exhibit/* projects/<project>/templates/

# Copy Google style template to project
cp templates/layouts/google_style/* projects/<project>/templates/

# Copy government style template to project (e.g., government red)
cp templates/layouts/government_red/* projects/<project>/templates/
```

### After Copying

1. Read `design_spec.md` to understand the design specification
2. Adjust colors based on project requirements (if needed)
3. Place logo files in the `images/` directory
4. Use the Executor role to generate SVG pages based on templates

---

## Template Development Guide

### Creating New Templates

1. Create a new directory under `templates/layouts/`
2. Create required files following the existing template structure
3. Ensure `design_spec.md` follows the standard chapter structure
4. All SVGs use `viewBox="0 0 1280 720"`
5. Follow SVG technical constraints (see below)
6. Validate the template directory with `python3 scripts/svg_quality_checker.py templates/layouts/<template_name> --format ppt169`
7. Register the new template in `templates/layouts/layouts_index.json`

`layouts_index.json` is the primary machine-readable source for template discovery. A template folder without an index entry is considered incomplete.

### SVG Technical Constraints (All Templates Must Comply)

#### Required

- viewBox: `0 0 1280 720`
- Backgrounds use `<rect>` elements
- Text wrapping uses `<tspan>`
- Transparency uses `fill-opacity` / `stroke-opacity`
- Gradients use `<defs>` with `<linearGradient>`

#### Forbidden (PPT Incompatible)

| Banned Element | Alternative |
|----------------|-------------|
| `<foreignObject>` | Use `<text>` + `<tspan>` |
| `clipPath` | Redesign layout |
| `mask` | Use `fill-opacity` |
| `<style>` / `class` | Use inline styles |
| `textPath` | Use plain `<text>` |
| `animate*` | Static design |
| `script` | No interactivity supported |
| `marker` / `marker-end` | Use `<polygon>` triangles |
| `rgba()` | Use HEX + `fill-opacity` |
| `<g opacity="...">` | Set opacity on each child element individually |

---
