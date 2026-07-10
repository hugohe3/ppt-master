---
layout_id: government_red
kind: layout
native_structure_mode: template
summary: Government briefings, policy interpretation, work summaries, project introductions, investment promotion.
canvas_format: ppt169
page_count: 5
page_types: [cover, toc, chapter, content, ending]
---

# Government Red Style Template - Design Specification

> Suitable for government agency briefings, policy presentations, work summaries, project introductions, and similar scenarios across all levels of government.

---

## I. Template Overview

| Property       | Description                                                  |
| -------------- | ------------------------------------------------------------ |
| **Template Name** | government_red (Government Red Template)                  |
| **Use Cases**  | Government briefings, policy interpretation, work summaries, project introductions, investment promotion |
| **Design Tone** | Authoritative, dignified, professional, modern government style |
| **Theme Mode** | Light theme (white background + government red/blue accents) |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 60px, Top 80px, Bottom 40px |
| **Safe Area**  | x: 60-1220, y: 80-680         |

---

## III. Page Structure

### General Layout

| Area       | Position/Height | Description                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=6px      | Dual-color gradient bar (red + blue), full width |
| **Title Bar** | y=30, h=50px | Section number block + title text + top-right logo |
| **Content Area** | y=100, h=560px | Main content area                 |
| **Footer** | y=680, h=40px   | Page number, organization name, bottom decoration line |

### Navigation Bar Design

- **Top Decoration Line**: Dual-color gradient (`#8B0000` → `#003366`), height 6px, full width
- **Bottom Decoration Line**: Government red (`#8B0000`), height 4px, y=716
- **Title Bar** (y=30):
  - Section number block: Government red square (50×50px), white number centered
  - Title text: 20px from number block, 28px font size, `#1A1A1A`
  - Top-right logo: Fixed at x=1107, dimensions 113×50px

---

## IV. Page Types

### 1. Cover Page (01_cover.svg)

- Dark gradient background (primarily government blue)
- Top gold decoration line
- Main title + subtitle (centered, white)
- Organization name
- Bottom date area

### 2. Table of Contents (02_toc.svg)

- White background + left-side red vertical bar decoration
- Supports up to 5 chapters
- Numbering uses red square blocks + white numbers
- Optional data display area on the right

### 3. Chapter Page (02_chapter.svg)

- Deep blue gradient background
- Large chapter number (semi-transparent decoration)
- Chapter title + English subtitle
- Geometric decorative elements

### 4. Content Page (03_content.svg)

- White background
- Standard navigation bar (red number block)
- Flexible content area
- Supports multiple layout modes

### 5. Ending Page (04_ending.svg)

- Deep blue background
- Centered thank-you message
- Full organization name
- Contact/Address information

---

## V. SVG Page Roster

| File | Role | Description |
|------|------|-------------|
| `01_cover.svg` | cover | Title slide; project name, presenter, date |
| `02_chapter.svg` | chapter | Chapter divider page (large number + chapter title) |
| `02_toc.svg` | toc | Table of contents listing major sections |
| `03_content.svg` | content | Main content page; body of the deck |
| `04_ending.svg` | ending | Closing/thank-you page |

## VI. Layout Modes

| Mode               | Use Cases                      |
| ------------------ | ------------------------------ |
| **Single Column Centered** | Cover, closing, key points |
| **Two Columns (5:5)** | Comparative display         |
| **Two Columns (4:6)** | Image-text mixed layout     |
| **Top-Bottom Split** | Process descriptions, policy lists |
| **Three-Column Cards** | Project lists, data display |
| **Matrix Grid**    | Category display               |
| **Table**          | Data comparison, specification lists |

---

## VII. Spacing Guidelines

| Element          | Value  |
| ---------------- | ------ |
| Card spacing     | 24px   |
| Content block spacing | 32px |
| Card padding     | 24px   |
| Card border radius | 8px  |
| Icon-to-text gap | 12px   |

---

## VIII. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; `rgba()` is prohibited
5. Prohibited: `mask`, `<style>`, `class`, `foreignObject`. `clipPath` is allowed only on `<image>` under `shared-standards.md` §1.2
6. Prohibited: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed (marker in `<defs>`, `orient="auto"`, shape = triangle/diamond/oval) — see shared-standards.md §1.1

### PPT Compatibility Rules

- `<g opacity="0..1">` is allowed as per-descendant alpha; overlapping children may composite differently
- `<image opacity="0..1">` maps to native picture transparency; use overlays only for color washes
- Use inline styles only; external CSS and `@font-face` are prohibited

---

## IX. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{AUTHOR}}`       | Organization name (Chinese) |
| `{{AUTHOR_EN}}`    | Organization name (English) |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{PAGE_NUM}}`     | Page number        |
| `{{DATE}}`         | Date               |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title |
| `{{TOC_ITEM_N_DESC}}`  | TOC item description |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Contact information |
| `{{LOGO_HEADER}}`  | Header logo filename |
| `{{COVER_BG_IMAGE}}`| Cover background image filename |

---

## X. Usage Instructions

1. Copy the template to the project directory
2. Replace logo files in the images directory (if applicable)
3. Select the appropriate page template based on content requirements
4. Mark content to be replaced using placeholders
5. Generate the final SVG through the Executor role

---

## XI. Design Highlights

- **Dual-Color Gradient Top Decoration**: Red-blue gradient reflects a government style
- **Gold Accent Elements**: Adds a sense of dignity
- **Geometric Decorative Patterns**: Modern government aesthetic
- **Clear Visual Hierarchy**: Ensures efficient information delivery
