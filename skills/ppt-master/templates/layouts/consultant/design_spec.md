# Consultant Style Template - Design Specification

> Suitable for business consulting, strategic analysis, project reports, corporate training, and similar scenarios.

---

## I. Template Overview

| Property       | Description                                            |
| -------------- | ------------------------------------------------------ |
| **Template Name** | consultant (Consultant Style Template)              |
| **Use Cases**  | Business consulting, strategic analysis, project reports, corporate training |
| **Design Tone** | Professional, minimalist, business-oriented, modern  |
| **Theme Mode** | Dark theme (dark blue background + blue accent + gold accents) |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 60px, Top 40px, Bottom 40px |
| **Safe Area**  | x: 60-1220, y: 80-660        |

---

## III. Color Scheme

### Primary Colors

| Role           | Value       | Notes                            |
| -------------- | ----------- | -------------------------------- |
| **Primary Dark Blue** | `#0A1628` | Cover, chapter, ending page backgrounds |
| **Content White** | `#FFFFFF` | Content page main background     |
| **Accent Blue** | `#0066CC`  | Decorative bars, buttons, title emphasis |
| **Gold Accent** | `#D4AF37`  | Dividers, highlight decorations  |
| **Auxiliary Gray** | `#F1F5F9` | Card backgrounds, key message area |

### Text Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **White Text** | `#FFFFFF`   | Primary text on dark backgrounds |
| **Primary Text** | `#0A1628` | Body text on light backgrounds |
| **Secondary Text** | `#94A3B8` | Subtitles, descriptions |
| **Tertiary Text** | `#64748B` | Footer, timestamps, sources |

### Functional Colors

| Usage      | Value       | Description    |
| ---------- | ----------- | -------------- |
| **Success** | `#22C55E`  | Positive indicators |
| **Warning** | `#EF4444`  | Risk alerts    |
| **Info**   | `#3B82F6`   | General info   |

---

## IV. Typography System

### Font Stack

**Font Stack**: `Arial, "Helvetica Neue", sans-serif`

### Font Size Hierarchy

| Level | Usage            | Size | Weight  |
| ----- | ---------------- | ---- | ------- |
| H1    | Cover main title | 52px | Bold    |
| H2    | Page main title  | 28px | Bold    |
| H3    | Section title    | 42px | Bold    |
| H4    | Card title       | 20px | Bold    |
| P     | Body content     | 16px | Regular |
| High  | Highlighted data | 36px | Bold    |
| Sub   | Auxiliary text   | 14px | Regular |

---

## V. Page Structure

### General Layout

| Area           | Position/Height | Description                            |
| -------------- | --------------- | -------------------------------------- |
| **Left Side**  | x=0, w=8px      | Blue decorative vertical bar           |
| **Header**     | y=0, h=60px     | Page title, Logo                       |
| **Content Area** | y=80, h=540px | Main content area                      |
| **Footer**     | y=660, h=60px   | Data source, page number               |

### Decorative Elements

- **Left Decorative Bar**: Blue (`#0066CC`), width 8px, spanning the full page
- **Gold Divider**: Gold (`#D4AF37`), width 2-3px, used for title decoration
- **Geometric Decoration**: Transparent-bordered rectangles for a modern feel

---

## VI. Page Types

### 1. Cover Page (01_cover.svg)

- Dark background (`#0A1628`)
- Left blue decorative bar
- Gold decorative lines
- Main title + subtitle
- Right-side geometric decoration
- Bottom date, author info

### 2. Table of Contents Page (02_toc.svg)

- Dark background
- Double vertical line separator `||` design
- Supports up to 5 chapters
- Left decorative vertical line
- Right-side geometric decoration

### 3. Chapter Page (02_chapter.svg)

- Dark background
- Blue chapter number block
- Chapter title + gold divider
- Right-side geometric decoration

### 4. Content Page (03_content.svg)

- White background
- Dark header bar
- Key message area (gray background + gold left decoration)
- Flexible content area
- Footer with data source and page number

### 5. Ending Page (04_ending.svg)

- Dark background
- Centered thank-you message
- Gold divider
- Contact information
- Confidential label

---

## VII. Layout Patterns

| Pattern            | Use Cases                      |
| ------------------ | ------------------------------ |
| **Single Column Centered** | Cover, ending, key points |
| **Left-Right Split (5:5)** | Comparison display      |
| **Left-Right Split (4:6)** | Image-text mixed layout |
| **Top-Bottom Split** | Process descriptions          |
| **Three-Column Cards** | Project lists                |
| **Table**          | Data comparison                |

---

## VIII. Spacing Guidelines

| Element            | Value  |
| ------------------ | ------ |
| Card gap           | 24px   |
| Content block gap  | 32px   |
| Card padding       | 20px   |
| Card border radius | 4px    |
| Icon-to-text gap   | 12px   |

---

## IX. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; no `rgba()`
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles for arrows instead of `<marker>`

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
| `{{AUTHOR}}`       | Author             |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| Chapter title      |
| `{{KEY_MESSAGE}}`  | Key message        |
| `{{PAGE_NUM}}`     | Page number        |
| `{{SOURCE}}`       | Data source        |
| `{{CONFIDENTIAL}}` | Confidential label |
| `{{LOGO}}`         | Logo text          |

---

## XI. Usage Instructions

1. Copy the template to the project directory
2. Select the appropriate page template based on content needs
3. Use placeholders to mark content that needs replacement
4. Generate the final SVG through the Executor role
