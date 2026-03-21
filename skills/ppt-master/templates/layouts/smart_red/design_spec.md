# smart_red - Smart Red-Orange Business Style Design Specification

> Suitable for tech company introductions, education industry solutions, smart campus proposals, and similar scenarios. Modern and energetic style.

---

## I. Template Overview

| Property       | Description                                                |
| -------------- | ---------------------------------------------------------- |
| **Template Name** | smart_red (Smart Red-Orange Business Style)              |
| **Use Cases**  | Company introductions, product launches, solution presentations, education industry courseware |
| **Design Tone** | Modern, energetic, professional, geometric                |
| **Theme Mode** | Hybrid theme (dark/colorful cover + light content pages)   |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Safe Margins** | 60px (left/right), 50px (top/bottom) |
| **Content Area** | x: 60-1220, y: 100-670      |
| **Title Area** | y: 50-100                     |
| **Grid Baseline** | 40px                       |

---

## III. Color Scheme

### Primary Colors

| Role             | Value       | Notes                            |
| ---------------- | ----------- | -------------------------------- |
| **Primary Red**  | `#DE3545`   | Brand identity, title decoration, geometric cutouts |
| **Auxiliary Orange** | `#F0964D` | Geometric accents, gradient pairing |
| **Dark Background** | `#333333` | Cover background, geometric cutouts, dark footer |

### Neutral Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **Light Gray Background** | `#F5F5F7` | Page background  |
| **Border Gray** | `#E0E0E0`  | Section dividers, card borders |
| **Body Black** | `#333333`   | Standard color for titles and body text |
| **Description Gray** | `#666666` | Subtitles, annotation text |
| **Pure White** | `#FFFFFF`   | Card background        |

---

## IV. Typography System

### Font Stack

**Font Stack**: `Arial, "Helvetica Neue", "Microsoft YaHei", sans-serif`

### Font Size Hierarchy

| Level    | Usage              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | Cover main title   | 60-80px | Bold    |
| H2       | Page title         | 32-40px | Bold    |
| H3       | Subsection/Card title | 24-28px | Bold |
| P        | Body content       | 18-20px | Regular |
| Caption  | Supplementary text | 14-16px | Regular |

---

## V. Core Design Principles

### Geometric Business Style

1. **Geometric Cutouts**: Cover, table of contents, and transition pages use large triangular cutout designs.
2. **Red-Black Contrast**: Red primary color paired with dark gray blocks creates a professional and impactful visual.
3. **Card-Based Layout**: Content pages use white cards to hold content, with light gray backgrounds for added depth.
4. **Whitespace**: Maintain adequate whitespace to avoid information overload.

### Advanced Refinement Features (v2.0)

1. **Multi-Layer Geometric Overlay**: Main triangles paired with semi-transparent smaller triangles for visual depth.
2. **Shadow Effects**: Text shadows, card shadows, and circle shadows for a 3D feel.
3. **Dual-Line Decoration**: Decorative lines use dual-line styles (thick + thin) for enhanced design appeal.
4. **Subtle Glow**: Ultra-faint color glow behind content areas for a premium feel.
5. **Texture Accents**: Panels with very faint diagonal line textures for added tactile quality.
6. **Circle Shadows**: Table of contents numbering circles with shadows to suggest interactivity.

---

## VI. Page Structure

### General Layout

| Area       | Position/Height | Description                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0-80          | Navigation bar / Title area            |
| **Content Area** | y=100-660 | Main content area (cards/diagrams)     |
| **Footer** | y=680           | Page number and copyright information  |

### Decorative Design

- **Triangular Cutouts**: Core visual element of cover and back pages.
- **Sidebar**: Left-side red polygonal panel unique to the table of contents page.
- **Top Decoration Bar**: Red cutout decoration at the top of content pages.

---

## VII. Page Types

### 1. Cover Page (01_cover.svg)

- **Background**: Light gray background `#F5F5F7`
- **Top-Left**: Red large triangular cutout (0,0 -> 350,0 -> 0,350)
- **Bottom-Left**: Dark gray triangular cutout (0,720 -> 300,720 -> 0,420)
- **Bottom-Right**: Red large triangular cutout (1280,720 -> 1280,320 -> 880,720)
- **Title Area**: Main title `{{TITLE}}` and subtitle `{{SUBTITLE}}` displayed center-right
- **Info Area**: Presenter `{{AUTHOR}}` and date `{{DATE}}` displayed at bottom

### 2. Table of Contents (02_toc.svg)

- **Background**: Light gray background `#F5F5F7`
- **Left Side**: Full-height red polygonal panel + large "Contents" text
- **Right Side**: Content list area
- **TOC Items**: Vertically arranged with circular number indices (01, 02...)

### 3. Chapter Page (02_chapter.svg)

- **Decoration**: Red triangles echoing the cover (top-left / bottom-right)
- **Center**: Large chapter number `{{CHAPTER_NUM}}` + chapter title `{{CHAPTER_TITLE}}`
- **Style**: Clean and impactful, vivid colors

### 4. Content Page (03_content.svg)

- **Top**: White navigation bar + top-right red cutout decoration + title dual-triangle decoration
- **Background**: Light gray background `#F5F5F7`
- **Title**: Page title `{{PAGE_TITLE}}` displayed left-aligned
- **Content**: `{{CONTENT_AREA}}` uses white card style (rounded corners + border)
- **Footer**: Includes copyright information and page number

### 5. Ending Page (04_ending.svg)

- **Layout**: Triangular layout fully echoing the cover (top-left red, bottom-left gray, bottom-right red)
- **Center**: Thank-you message displayed
- **Bottom**: Whitespace reserved for contact information

---

## VIII. Common Components

### Card Style

```xml
<!-- White content card -->
<rect x="60" y="110" width="1160" height="540" rx="4" ry="4" fill="#FFFFFF" stroke="#E0E0E0" stroke-width="1" />
```

### TOC Circular Numbering

```xml
<circle cx="40" cy="40" r="30" fill="#FFFFFF" stroke="#DE3545" stroke-width="2" />
<text x="40" y="50" text-anchor="middle" font-family="Arial" font-size="28" font-weight="bold" fill="#DE3545">01</text>
```

---

## IX. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (**strictly no** `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`
7. Define gradients using `<defs>`

---

## X. Placeholder Specification

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{AUTHOR}}`       | Presenter/Author   |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{CONTENT_AREA}}` | Content area identifier |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| Chapter title      |
| `{{PAGE_NUM}}`     | Page number        |
| `{{TOC_ITEM_1}}`   | TOC item 1         |
| `{{CLOSING_MESSAGE}}`| Closing message  |

---

## XI. Usage Instructions

1. Copy this directory to the project directory.
2. Select the appropriate page template based on content requirements.
3. Modify the text content in the SVG files or replace images.
4. Use the `ppt-master` tool to generate the PPTX file.
