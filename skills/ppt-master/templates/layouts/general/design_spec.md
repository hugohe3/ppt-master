# General Style Template - Design Specification

> Suitable for various general presentation scenarios, including work reports, project introductions, product showcases, and more.

---

## I. Template Overview

| Property       | Description                                            |
| -------------- | ------------------------------------------------------ |
| **Template Name** | general (General Template)                          |
| **Use Cases**  | Work reports, project introductions, product showcases, training presentations |
| **Design Tone** | Modern, fresh, professional, versatile               |
| **Theme Mode** | Mixed theme (dark cover/chapter pages + light content pages) |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 40px, Top 10px, Bottom 60px |
| **Safe Area**  | x: 40-1240, y: 90-660        |

---

## III. Color Scheme

### Primary Colors

| Role           | Value       | Notes                            |
| -------------- | ----------- | -------------------------------- |
| **Primary Dark Blue** | `#1E3A5F` | Cover, chapter page backgrounds, titles |
| **Dark Blue Deep** | `#0F1C2E` | Gradient end point             |
| **Content Background** | `#F8FAFC` | Content page main background |
| **Card White** | `#FFFFFF`   | Card background                  |
| **Purple Accent** | `#6366F1` | Chapter numbers, decorative circles, emphasis elements |
| **Cyan Accent** | `#22D3EE`  | Secondary decorative circles     |

### Text Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **White Text** | `#FFFFFF`   | Primary text on dark backgrounds |
| **Primary Text** | `#333333` | Body text in cards     |
| **Title Dark Blue** | `#1E3A5F` | Titles on light backgrounds |
| **Secondary Text** | `#94A3B8` | Subtitles, descriptions |
| **Tertiary Text** | `#64748B` | Footer, section labels |

### Neutral Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **Border Gray** | `#E2E8F0`  | Dividers, card borders |
| **Light Gray Background** | `#CBD5E1` | Placeholder text |

---

## IV. Typography System

### Font Stack

**Font Stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`

### Font Size Hierarchy

| Level | Usage            | Size | Weight  |
| ----- | ---------------- | ---- | ------- |
| H1    | Cover main title | 48px | Bold    |
| H2    | Page title       | 24px | Bold    |
| H3    | Section title    | 48px | Bold    |
| H4    | Card title       | 20px | Bold    |
| P     | Body content     | 16px | Regular |
| High  | Highlighted data | 36px | Bold    |
| Sub   | Auxiliary text   | 14px | Regular |
| XS    | Page number, copyright | 12px | Regular |

---

## V. Page Structure

### General Layout

| Area           | Position/Height | Description                            |
| -------------- | --------------- | -------------------------------------- |
| **Header**     | y=0, h=70px     | White background + bottom divider + page title |
| **Content Area** | y=90, h=550px | Main content area (white cards)        |
| **Footer**     | y=660, h=60px   | White background + top divider + section label + page number |

### Decorative Elements

- **Decorative Circles**: Low-opacity gradient circles in purple and cyan
- **Left Indicator Bar**: Dark blue (`#1E3A5F`), width 4-6px
- **Divider Lines**: Light gray (`#E2E8F0`), width 1px

---

## VI. Page Types

### 1. Cover Page (01_cover.svg)

- Dark gradient background (`#1E3A5F` → `#0F1C2E`)
- Top-right decorative circles (purple, cyan, low opacity)
- Left decorative white line
- Main title + subtitle
- Bottom semi-transparent info area (date, author)

### 2. Table of Contents Page (02_toc.svg)

- Light background
- White header + dark blue title
- Card-style TOC item layout
- Double vertical line separator `||` design
- Different colored left bars to distinguish sections
- Decorative circle accents

### 3. Chapter Page (02_chapter.svg)

- Dark solid background (`#1E3A5F`)
- Decorative circles (purple, cyan, low opacity)
- Large semi-transparent background number
- Centered chapter title
- Divider line + chapter description

### 4. Content Page (03_content.svg)

- Light gray background (`#F8FAFC`)
- White header + bottom divider
- White content cards (border radius 8px)
- White footer + top divider
- Left dark blue vertical bar section indicator

### 5. Ending Page (04_ending.svg)

- Dark gradient background
- Decorative circles
- Centered thank-you message
- Divider line + tagline
- Contact information
- Bottom copyright

---

## VII. Layout Patterns

| Pattern            | Use Cases                      |
| ------------------ | ------------------------------ |
| **Single Column Centered** | Cover, ending            |
| **Two-Column Cards** | Table of contents             |
| **Left-Right Split (5:5)** | Comparison display      |
| **Left-Right Split (4:6)** | Image-text mixed layout |
| **Grid Cards**     | Project lists                  |
| **Table**          | Data summary                   |

---

## VIII. Spacing Guidelines

| Element            | Value  |
| ------------------ | ------ |
| Card gap           | 20px   |
| Content block gap  | 24px   |
| Card padding       | 20px   |
| Card border radius | 8px    |
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
| `{{AUTHOR}}`       | Author             |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| Chapter title      |
| `{{CHAPTER_DESC}}` | Chapter description |
| `{{SECTION_NAME}}` | Section name (footer) |
| `{{PAGE_NUM}}`     | Page number        |
| `{{CONTACT_INFO}}` | Contact information |
| `{{COPYRIGHT}}`    | Copyright info     |
| `{{LOGO}}`         | Logo text          |

---

## XI. Usage Instructions

1. Copy the template to the project directory
2. Select the appropriate page template based on content needs
3. Use placeholders to mark content that needs replacement
4. Generate the final SVG through the Executor role
