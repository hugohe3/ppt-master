# Exhibit Style Template - Design Specification

> Conclusion-first layout with Exhibit takeaway bars, ideal for data-driven strategic reports and executive presentations.

---

## I. Template Overview

| Property       | Description                                            |
| -------------- | ------------------------------------------------------ |
| **Template Name** | exhibit (Exhibit Style Template)                    |
| **Use Cases**  | Strategic planning, executive reports, investment analysis, board presentations |
| **Design Tone** | Premium, refined, authoritative, data-driven, conclusion-first |
| **Theme Mode** | Dark theme (dark background + gradient accents + gold highlights) |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 40px, Top 20px, Bottom 40px |
| **Safe Area**  | x: 40-1240, y: 40-680        |

---

## III. Color Scheme

### Primary Colors

| Role           | Value       | Notes                            |
| -------------- | ----------- | -------------------------------- |
| **Primary Dark** | `#0D1117` | Cover, chapter, ending page backgrounds |
| **Content White** | `#FFFFFF` | Content page main background     |
| **Gradient Start Blue** | `#1E40AF` | Top gradient bar start point |
| **Gradient End Purple** | `#7C3AED` | Top gradient bar end point   |
| **Gold Accent** | `#D4AF37`  | Dividers, highlight decorations  |
| **Purple-Blue Accent** | `#6366F1` | Chapter numbers, secondary accents |

### Text Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **White Text** | `#FFFFFF`   | Primary text on dark backgrounds |
| **Light Gray Text** | `#9CA3AF` | Descriptions, subtitles |
| **Tertiary Text** | `#6B7280` | Footer, timestamps     |
| **Body Black** | `#111827`   | Body text on light backgrounds |

### Neutral Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **Card Background** | `#1F2937` | Dark card background |
| **Divider**    | `#E5E7EB`   | Dividers on light backgrounds |
| **Border Gray** | `#374151`  | Borders on dark backgrounds |

---

## IV. Typography System

### Font Stack

**Font Stack**: `Arial, "Helvetica Neue", sans-serif`

### Font Size Hierarchy

| Level | Usage            | Size | Weight  | Letter Spacing |
| ----- | ---------------- | ---- | ------- | -------------- |
| H1    | Cover main title | 56px | Bold    | 2px            |
| H2    | Page main title  | 28px | Bold    | 1px            |
| H3    | Section title    | 48px | Bold    | 2px            |
| H4    | Card title       | 18px | Bold    | 1px            |
| P     | Body content     | 14px | Regular | -              |
| High  | Highlighted data | 40px | Bold    | -              |
| Sub   | Auxiliary text   | 12px | Regular | -              |

---

## V. Page Structure

### General Layout

| Area           | Position/Height | Description                            |
| -------------- | --------------- | -------------------------------------- |
| **Top**        | y=0, h=6px      | Gradient decorative bar (blue-purple gradient) |
| **Header**     | y=20, h=60px    | Key message / page title               |
| **Content Area** | y=100, h=520px | Main content area                    |
| **Footer**     | y=660, h=60px   | Data source, confidential label, page number |

### Decorative Elements

- **Top Gradient Bar**: Blue-purple gradient (`#1E40AF` → `#7C3AED`), height 4-6px
- **Left Gold Line**: Gold (`#D4AF37`), width 4px, used for chapter page decoration
- **Grid Decoration**: Low-opacity line grid for a data/precision feel

---

## VI. Page Types

### 1. Cover Page (01_cover.svg)

- Dark background (`#0D1117`)
- Top gradient decorative bar
- Left gold vertical line decoration
- Main title + subtitle + project ID
- Right-side grid decoration
- Bottom date, confidential label, author info

### 2. Table of Contents Page (02_toc.svg)

- Dark background
- Top gradient bar
- Double vertical line separator `||` design (gold)
- Chapter numbers in purple-blue
- Right-side grid decoration
- Confidential label

### 3. Chapter Page (02_chapter.svg)

- Dark background
- Top gradient bar
- Left gold vertical line
- Large semi-transparent background number
- Chapter title + description
- Right-side grid decoration

### 4. Content Page (03_content.svg)

- White background
- Top gradient thin bar
- Dark key message bar (gold left decoration)
- Flexible content area
- Footer: data source, confidential label, page number

### 5. Ending Page (04_ending.svg)

- Dark background
- Top gradient bar
- Grid decoration background
- Centered thank-you message
- Gold divider
- Contact info card
- Confidential label + copyright

---

## VII. Layout Patterns

| Pattern            | Use Cases                      |
| ------------------ | ------------------------------ |
| **Single Column Centered** | Cover, ending            |
| **Left-Right Split (5:5)** | Data comparison         |
| **Left-Right Split (3:7)** | Chart + text            |
| **Matrix Grid**    | Multi-dimensional analysis     |
| **Waterfall Chart** | Financial analysis            |
| **Table**          | Data summary                   |

---

## VIII. Spacing Guidelines

| Element            | Value  |
| ------------------ | ------ |
| Card gap           | 20px   |
| Content block gap  | 24px   |
| Card padding       | 24px   |
| Card border radius | 8px    |
| Icon-to-text gap   | 10px   |

---

## IX. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; no `rgba()`
5. Prohibited: `mask`, `<style>`, `class`, `foreignObject`. `clipPath` is allowed only on `<image>` under `shared-standards.md` §1.2
6. Prohibited: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed (marker in `<defs>`, `orient="auto"`, shape = triangle/diamond/oval) — see shared-standards.md §1.1
8. Define gradients using `<defs>` with `<linearGradient>`

### PPT Compatibility Rules

- No `<g opacity="...">` (group opacity); set opacity on each child element individually
- Use overlay layers for image transparency
- Inline styles only; no external CSS or `@font-face`

---

## X. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{PROJECT_ID}}`   | Project ID         |
| `{{AUTHOR}}`       | Author             |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{KEY_MESSAGE}}`  | Key message (Exhibit) |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| Chapter title      |
| `{{PAGE_NUM}}`     | Page number        |
| `{{SOURCE}}`       | Data source        |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title |
| `{{TOC_ITEM_N_DESC}}`  | TOC item description |
| `{{CONTACT_NAME}}` | Contact person name |
| `{{CONTACT_INFO}}` | Contact information |
| `{{COPYRIGHT}}`    | Copyright info     |
| `{{LOGO}}`         | Logo text          |

---

## XI. Signature Design Elements

### Confidential Label

All pages display a centered `CONFIDENTIAL` label at the bottom in gold text.

### Exhibit Title Bar

Content pages feature a dark background + gold left decoration key message bar at the top, similar to the "Exhibit" style used by consulting firms.

### Grid Background

Chapter and ending pages use low-opacity grid line decoration to create a professional data analysis atmosphere.

---

## XII. Usage Instructions

1. Copy the template to the project directory
2. Select the appropriate page template based on content needs
3. Use placeholders to mark content that needs replacement
4. Ensure the confidential label displays correctly
5. Generate the final SVG through the Executor role
