# Tech Blue Business (科技蓝商务) - Universal Business Style Design Specification

> Suitable for corporate reports, product launches, proposals, process standards, and other business scenarios. Style: professional, tech-oriented, and clean.

---

## I. Template Overview

| Property         | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| **Template Name**| Tech Blue Business (科技蓝商务 / tech_blue_business)             |
| **Use Cases**    | Corporate reports, product launches, proposals, process standards, training materials |
| **Design Tone**  | Tech, business, professional, clean                              |
| **Theme Mode**   | Mixed theme (dark blue/tech blue cover + light content pages)    |

---

## II. Canvas Specification

| Property           | Value                         |
| ------------------ | ----------------------------- |
| **Format**         | Standard 16:9                 |
| **Dimensions**     | 1280 × 720 px                |
| **viewBox**        | `0 0 1280 720`               |
| **Safe Margins**   | 60px (left/right), 50px (top/bottom) |
| **Content Area**   | x: 60-1220, y: 140-640       |
| **Title Area**     | y: 40-100                    |
| **Grid Baseline**  | 40px                         |

---

## III. Color Scheme

### Primary Colors

| Role               | Value       | Notes                                    |
| ------------------ | ----------- | ---------------------------------------- |
| **Primary Blue**   | `#0078D7`   | Brand identity, title accents, key elements |
| **Dark Blue**      | `#002E5D`   | Dark backgrounds, footer, important nodes |
| **Accent Cyan**    | `#4CA1E7`   | Gradient pairing, secondary accents      |
| **Alert Red**      | `#E60012`   | Key emphasis, warning information        |

### Neutral Colors

| Role               | Value       | Usage                          |
| ------------------ | ----------- | ------------------------------ |
| **Background White**| `#FFFFFF`  | Main page background           |
| **Light Gray BG**  | `#F5F5F7`   | Base color for each page       |
| **Border Gray**    | `#A0C4E3`   | Dashed borders, module dividers |
| **Body Text Black**| `#333333`   | Standard color for titles and body text |
| **Caption Gray**   | `#666666`   | Subtitles, page numbers, annotations |

---

## IV. Typography System

### Font Stack

**Font Stack**: `"Microsoft YaHei", "PingFang SC", sans-serif`

### Font Size Hierarchy

| Level    | Usage              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | Cover main title   | 64px    | Bold    |
| H2       | Page title         | 36-40px | Bold    |
| H3       | Section/card title | 24-28px | Bold    |
| P        | Body content       | 20-24px | Regular |
| Caption  | Supplementary text | 14-16px | Regular |

---

## V. Core Design Principles

### Tech Business Style

1. **Wave Curves**: Multi-layered wave curves at the bottom of cover and transition pages add dynamism and depth.
2. **Dashed Containers**: Content areas use dashed borders (`stroke-dasharray`) to convey a data-driven, rigorous aesthetic.
3. **Blue-White Simplicity**: Generous white space paired with tech blue creates a professional, crisp visual feel.
4. **Hexagonal Patterns**: Cover and chapter pages use hexagonal patterns to evoke a sense of technology and innovation.

### Advanced Styling Features

1. **Gradient Application**: Blue-to-dark-blue linear gradients for backgrounds and important graphics.
2. **Opacity Layering**: Waves use varying opacity levels to create a breathing effect.
3. **Rounded Corners**: Content containers use `rx="10"` rounded corners to soften the tech coldness and add warmth.
4. **Decorative Triangles**: Small triangle prefixes before titles guide the reader's eye.

---

## VI. Page Structure

### General Layout

| Area         | Position/Height | Description                            |
| ------------ | --------------- | -------------------------------------- |
| **Top**      | y=0-120         | Title area, logo, and decorative lines |
| **Content**  | y=140-640       | Main content area (dashed containers)  |
| **Footer**   | y=680-720       | Page number and copyright info         |

### Decorative Design

- **Bottom Waves**: Core visual element of cover and ending pages.
- **Top Accent Bar**: Blue color block as title prefix in the upper-left corner.
- **Dashed Frames**: Standard containers for structured content layout.

---

## VII. Page Types

### 1. Cover Page (01_cover.svg)

- **Layout**: Asymmetric left-right or overlay layout.
- **Background**: Large blue gradient on the left/top; image container on the right.
- **Decoration**: Dual-layer wave curves at the bottom for dynamism.
- **Title**: Left-aligned, large white text with subtitle background accent.
- **Image**: Full-bleed right-side crop showcasing medical/tech scenes.

### 2. Table of Contents (02_toc.svg)

- **Layout**: Left-right split.
- **Left Side**: Dark blue/tech blue sidebar with large "Contents" text.
- **Right Side**: List-style entries with bullet points and line guides.
- **Decoration**: Clean line dividers maintaining visual breathing room.

### 3. Chapter Page (02_chapter.svg)

- **Background**: Full-screen dark blue gradient (`#0078D7` -> `#002E5D`).
- **Center**: Center-aligned large chapter number + bold title.
- **Decoration**: Minimalist geometric rings or line accents focusing on the theme.

### 4. Content Page (03_content.svg)

- **Top**: Minimalist title bar with blue rectangle accent in the upper-left.
- **Background**: Pure white.
- **Content**: Default includes a rounded dashed container (`stroke-dasharray="8,8"`).
- **Footer**: Small gray text for page number and confidentiality label.

### 5. Ending Page (04_ending.svg)

- **Background**: Dark blue gradient echoing the chapter page.
- **Center**: "Thank You" message and Q&A.
- **Decoration**: Bottom wave curves for visual bookending.

---

## VIII. Common Components

### Dashed Content Container

```xml
<!-- Rounded dashed content frame -->
<rect x="60" y="140" width="1160" height="500" fill="none" stroke="#A0C4E3" stroke-width="2" stroke-dasharray="8,8" rx="10" />
```

### Title Prefix Decoration

```xml
<!-- Blue rectangle decoration -->
<rect x="40" y="40" width="10" height="40" fill="#0078D7" />
```

---

## IX. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (**`<foreignObject>` is strictly prohibited**)
4. Use `fill-opacity` / `stroke-opacity` for transparency
5. Prohibited: `clipPath` (avoid unless needed for image cropping), `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`
7. Define gradients in `<defs>`

---

## X. Placeholder Specification

| Placeholder                   | Description                |
| ----------------------------- | -------------------------- |
| `{{TITLE}}`                   | Main title                 |
| `{{SUBTITLE}}`                | Subtitle                   |
| `{{AUTHOR}}`                  | Speaker/Author             |
| `{{DATE}}`                    | Date                       |
| `{{PAGE_TITLE}}`              | Page title                 |
| `{{CONTENT_PLACEHOLDER}}`     | Content area prompt text   |
| `{{SECTION_NUMBER}}`          | Section number (01)        |
| `{{SECTION_TITLE}}`           | Section title              |
| `{{PAGE_NUMBER}}`             | Page number                |
| `{{SECTION_1_TITLE}}`         | TOC item 1                 |

---

## XI. Usage Notes

1. This template is a universal tech blue business style, suitable for various corporate business scenarios.
2. Content pages include dashed frames by default; these can be removed or resized based on content volume.
3. Wave elements and hexagonal patterns are decorative SVG paths; modifications should maintain the original style.
4. The color scheme is primarily blue-based and can be fine-tuned to match corporate brand colors.
