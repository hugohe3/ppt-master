---
layout_id: medical_university
kind: layout
native_structure_mode: template
summary: Medical academic reports, case discussions, research presentations, hospital work reports, medical education and training.
canvas_format: ppt169
page_count: 5
page_types: [cover, toc, chapter, content, ending]
---

# Hospital / Medical University Template (Medical University Style) - Design Specification

> Suitable for hospitals, medical universities, affiliated hospitals, and medical research institutions for academic reports, case presentations, research results, and related scenarios.

---

## I. Template Overview

| Property         | Description                                                          |
| ---------------- | -------------------------------------------------------------------- |
| **Template Name**| medical_university (Hospital / Medical University Template)          |
| **Use Cases**    | Medical academic reports, case discussions, research presentations, hospital work reports, medical education and training |
| **Design Tone**  | Professional, rigorous, life-affirming, tech-forward, trustworthy   |
| **Theme Mode**   | Light theme (white background + medical blue title bar + life green accents) |
| **Target Institutions** | All types of medical institutions (hospitals, medical universities, affiliated hospitals, medical research institutes) |

---

## II. Canvas Specification

| Property           | Value                        |
| ------------------ | ---------------------------- |
| **Format**         | Standard 16:9                |
| **Dimensions**     | 1280 × 720 px               |
| **viewBox**        | `0 0 1280 720`              |
| **Page Margins**   | Left/right 40px, top 0px, bottom 35px |
| **Content Safe Area** | x: 40-1240, y: 70-665    |

---

## III. Page Structure

### General Layout

| Area              | Position/Height  | Description                                  |
| ----------------- | ---------------- | -------------------------------------------- |
| **Header**        | y=0, h=70px      | Medical blue background + orange left vertical bar + page title |
| **Key Message Bar** | y=70, h=50px   | Core message/summary area (light blue background) |
| **Content Area**  | y=135, h=515px   | Main content area                            |
| **Footer**        | y=665, h=55px    | Data source, institution name, page number   |

### Decorative Design

- **Left Orange Vertical Bar**: Emphasis orange (`#FF6B35`), width 6px, used for header and card decoration
- **Medical Blue Border**: Primary blue (`#0066B3`), used for card borders
- **Green Accents**: Accent green (`#00A86B`), used for health/life-related elements
- **Cross/ECG Decorations**: Medical-themed geometric decorative elements

---

## IV. Page Types

### 1. Cover Page (01_cover.svg)

- White background
- Medical blue top horizontal bar + orange left vertical bar decoration
- Upper-right logo/emblem placeholder area
- Centered main title + subtitle
- Decorative divider line (blue + green dots)
- Presenter information area (name, department/advisor, institution)
- Bottom gray info area (date)

### 2. Table of Contents (02_toc.svg)

- White background
- Standard header (medical blue + orange vertical bar)
- Card-style TOC layout (2 columns)
- Light blue/light green background cards + left colored vertical bar
- Optional items use dashed borders

### 3. Chapter Page (02_chapter.svg)

- Deep medical blue full-screen background (`#004080`)
- Right-side geometric decorations (medical theme)
- Left orange vertical bar decoration
- Large semi-transparent background chapter number
- Prominent white chapter title
- Light blue chapter description

### 4. Content Page (03_content.svg)

- White background
- Standard header (medical blue + orange vertical bar)
- Key message bar (light blue background + blue left vertical bar)
- Flexible content area
- Footer: data source, institution name, page number

### 5. Ending Page (04_ending.svg)

- White background
- Medical blue top horizontal bar
- Centered thank-you message
- Department/contact information
- Institution logo area

---

## V. SVG Page Roster

| File | Role | Description |
|------|------|-------------|
| `01_cover.svg` | cover | Title slide; project name, presenter, date |
| `02_chapter.svg` | chapter | Chapter divider page (large number + chapter title) |
| `02_toc.svg` | toc | Table of contents listing major sections |
| `03_content.svg` | content | Main content page; body of the deck |
| `04_ending.svg` | ending | Closing/thank-you page |

## VI. Layout Patterns (Recommended)

### Common Layouts for Medical Reports

| Layout Name           | Applicable Scenarios             | Features                       |
| --------------------- | -------------------------------- | ------------------------------ |
| **Single Column Center** | Case overview, main conclusions | Highlights key points, clear hierarchy |
| **Dual Column Comparison** | Before/after treatment, plan comparison | Symmetrical, easy to compare |
| **Image-Text Mixed**  | Imaging materials, pathology images | Images with text descriptions |
| **Data Cards**        | Lab results, vital signs         | Multiple metrics side by side  |
| **Timeline**          | Disease progression, treatment course | Clear chronological order    |
| **Flowchart**         | Clinical pathways, procedure standards | Clear steps, logical flow   |

---

## VII. Spacing Specification

| Spacing Type       | Value | Usage                            |
| ------------------ | ----- | -------------------------------- |
| **Page Margins**   | 40px  | Distance from content to page edge |
| **Card Spacing**   | 24px  | Spacing between cards            |
| **Element Spacing** | 16px | Spacing between elements within cards |
| **Line Height**    | 1.5   | Body text line height multiplier |
| **Paragraph Spacing** | 20px | Spacing between paragraphs     |

---

## VIII. SVG Technical Constraints

### Mandatory Rules

- viewBox fixed at `0 0 1280 720`
- Use `<rect>` elements for backgrounds
- Use `<tspan>` for text wrapping
- All colors in HEX format (no rgba)
- Use `fill-opacity` / `stroke-opacity` for transparency

### Prohibited Elements (PPT Incompatible)

| Prohibited Item      | Alternative                    |
| -------------------- | ------------------------------ |
| `clipPath` | Allowed only on `<image>` under `shared-standards.md` §1.2 |
| `mask` | Do not use masking |
| `<style>`            | Use inline styles              |
| `class`              | Use inline attributes (`id` inside `<defs>` is allowed) |
| `foreignObject`      | Use `<tspan>` for wrapping     |
| `textPath`           | Use standard `<text>`          |
| `animate*` / `set`   | Do not use animations          |
| `<g opacity>`        | Set opacity on each element individually |

> `marker-start` / `marker-end` are conditionally allowed — see `shared-standards.md` §1.1 (marker must be in `<defs>`, `orient="auto"`, shape = triangle / diamond / oval). The converter maps them to native DrawingML arrow heads.

---

## IX. Placeholder Specification

| Placeholder         | Usage                        |
| ------------------- | ---------------------------- |
| `{{LOGO}}`          | Emblem/institution logo      |
| `{{TITLE}}`         | Main title                   |
| `{{SUBTITLE}}`      | Subtitle                     |
| `{{AUTHOR}}`        | Presenter name               |
| `{{DEPARTMENT}}`    | Department/school            |
| `{{ADVISOR}}`       | Thesis advisor               |
| `{{INSTITUTION}}`   | Institution name             |
| `{{DATE}}`          | Date                         |
| `{{CHAPTER_NUM}}`   | Chapter number               |
| `{{CHAPTER_TITLE}}` | Chapter title                |
| `{{CHAPTER_DESC}}`  | Chapter description          |
| `{{PAGE_TITLE}}`    | Page title                   |
| `{{KEY_MESSAGE}}`   | Key message                  |
| `{{CONTENT_AREA}}`  | Content area                 |
| `{{SOURCE}}`        | Data source                  |
| `{{PAGE_NUM}}`      | Page number                  |
| `{{SECTION_NAME}}`  | Section name (footer)        |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title (N=1..n)   |
| `{{TOC_ITEM_N_DESC}}`  | TOC item description (N=1..n) |
| `{{THANK_YOU}}`     | Thank-you message            |
| `{{ENDING_SUBTITLE}}` | Ending subtitle/tagline    |

---

## X. Usage Notes

### 1. Copy Template to Project

```bash
cp templates/layouts/medical_university/* projects/<project>/templates/
```

### 2. Logo Placement Guidelines

- Cover page: Upper-right corner, approx. 160×50px
- Content page: Upper-right within header, approx. 120×35px
- Ending page: Can be enlarged, centered or paired with contact info

---

## XI. Medical Content-Specific Components

### Data Card (Vital Signs)

```xml
<rect x="x" y="y" width="180" height="100" fill="#E8F5EE" rx="8"/>
<text x="x+90" y="y+35" text-anchor="middle" fill="#333333" font-size="14">Temperature</text>
<text x="x+90" y="y+70" text-anchor="middle" fill="#00A86B" font-size="28" font-weight="bold">36.5°C</text>
```

### Warning Label

```xml
<rect x="x" y="y" width="80" height="28" fill="#FFC107" rx="4"/>
<text x="x+40" y="y+19" text-anchor="middle" fill="#333333" font-size="14">Caution</text>
```

### Critical Value Label

```xml
<rect x="x" y="y" width="80" height="28" fill="#DC3545" rx="4"/>
<text x="x+40" y="y+19" text-anchor="middle" fill="#FFFFFF" font-size="14">Critical</text>
```
