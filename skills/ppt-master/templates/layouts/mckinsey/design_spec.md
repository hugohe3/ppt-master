# McKinsey Style Template - Design Specification

> Suitable for strategic consulting, executive briefings, investment analysis, business proposals, and other high-end business scenarios.

---

## I. Template Overview

| Property       | Description                                                |
| -------------- | ---------------------------------------------------------- |
| **Template Name** | mckinsey (McKinsey Style Template)                      |
| **Use Cases**  | Strategic consulting, executive briefings, investment analysis, business proposals |
| **Design Tone** | Data-driven, structured thinking, professional whitespace, minimalist premium |
| **Theme Mode** | Light theme (white background + McKinsey Blue accent)      |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 60px, Top 60px, Bottom 40px |
| **Safe Area**  | x: 60-1220, y: 60-680         |
| **Grid Baseline** | 40px                       |

---

## III. Color Scheme

### Primary Colors

| Role             | Value       | Notes                            |
| ---------------- | ----------- | -------------------------------- |
| **McKinsey Blue**| `#005587`   | Primary color, title bar, accent elements |
| **Deep Teal**    | `#004D5C`   | Secondary blue, gradient endpoint |
| **Background White** | `#FFFFFF` | Main page background            |
| **Light Gray Background** | `#ECF0F1` | Separators, secondary backgrounds |

### Text Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **Title Dark Gray** | `#2C3E50` | Main titles, card titles |
| **Body Gray**  | `#5D6D7E`   | Body content, descriptive text |
| **Auxiliary Gray** | `#7F8C8D` | Annotations, sources, footer |
| **White Text** | `#FFFFFF`   | Text on blue backgrounds |

### Accent Colors

| Usage            | Value       | Description            |
| ---------------- | ----------- | ---------------------- |
| **Data Highlight** | `#F5A623` | Amber, key data emphasis |
| **Warning/Issue** | `#E74C3C`  | Coral, problem areas, negative indicators |
| **Success/Positive** | `#27AE60` | Green, positive indicators |
| **Info Blue**    | `#0076A8`   | Supplementary info, chart gradients |

---

## IV. Typography System

### Font Stack

**Font Stack**: `Arial, "Helvetica Neue", "Segoe UI", sans-serif`

### Font Size Hierarchy

| Level    | Usage              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | Cover main title   | 52px    | Bold    |
| H2       | Page title         | 36px    | Bold    |
| H3       | Section title      | 22-24px | Bold    |
| H4       | Card title         | 16-18px | Bold    |
| P        | Body content       | 14-16px | Regular |
| Data     | Data highlight     | 44px    | Bold    |
| Sub      | Chart labels/Annotations | 12-14px | Regular |

---

## V. Core Design Principles

### McKinsey Style Characteristics

1. **Data-Driven**: Key data and insights at the core, strengthening argument support
2. **Structured Thinking**: MECE principle, clear logical frameworks
3. **Information Visualization**: Charts, matrices, and funnel models take priority
4. **Professional Whitespace**: Ample breathing room, content coverage < 65%
5. **Grid Alignment**: 40px baseline grid, precise alignment
6. **Minimalist Icons**: Geometric shapes, avoiding ornate decoration
7. **Professional Color Palette**: Avoiding flashy gradients, maintaining restraint

---

## VI. Page Structure

### General Layout

| Area       | Position/Height | Description                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=4px      | McKinsey Blue horizontal bar           |
| **Title Area** | y=40, h=60px | Page title (left-aligned, large bold)  |
| **Content Area** | y=120, h=520px | Main content area                  |
| **Footer** | y=680, h=40px   | Page number (left), data source/confidential label (right) |

### Decorative Design

- **Left Accent Bar**: McKinsey Blue (`#005587`), width 8px (cover page)
- **Top Decoration Line**: McKinsey Blue (`#005587`), height 4px
- **Card Borders**: Light gray (`#ECF0F1`), width 2px
- **Geometric Decoration**: Low-opacity blue geometric patterns (cover page right side)

---

## VII. Page Types

### 1. Cover Page (01_cover.svg)

- White background
- Left-side blue narrow accent bar (8px)
- Top-left short horizontal line decoration
- Main title + subtitle (left-aligned)
- Bottom project code, date
- Right-side low-opacity geometric decoration
- Bottom-right confidential label

### 2. Table of Contents (02_toc.svg)

- White background
- Top blue decoration bar
- Title area "Agenda" / "Contents"
- Chapter list (number + title)
- Clean line separators

### 3. Chapter Page (02_chapter.svg)

- McKinsey Blue full-screen background
- Centered large chapter title
- White text
- Minimalist design

### 4. Content Page (03_content.svg)

- White background
- Top blue decoration bar
- Left-aligned page title
- Flexible content area
- Footer: page number, data source

### 5. Ending Page (04_ending.svg)

- White background
- Centered thank-you message
- Contact information
- Confidential label

---

## VIII. Chart Specifications

### Recommended Chart Dimensions

| Chart Type       | Recommended Size   |
| ---------------- | ------------------ |
| Bar chart        | 500-700 × 400-500px |
| Pie chart        | Diameter 300-400px |
| Data card        | 150 × 120px       |
| Matrix           | 240-280px / cell   |
| Funnel chart     | 500 × 400px       |

### Chart Color Palette

- Primary series: `#005587`, `#0076A8`, `#4A90A4`
- Accent: `#F5A623`
- Warning: `#E74C3C`

---

## IX. Spacing Guidelines

| Element          | Value    |
| ---------------- | -------- |
| Page margins     | 60px     |
| Title area height | 80-100px |
| Chart spacing    | 40-60px  |
| Card padding     | 20-24px  |
| Text line height | 1.6      |
| Grid baseline    | 40px     |

---

## X. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; `rgba()` is prohibited
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed (marker in `<defs>`, `orient="auto"`, shape = triangle/diamond/oval) — see shared-standards.md §1.1
8. Define gradients using `<linearGradient>` within `<defs>`

### PPT Compatibility Rules

- No `<g opacity="...">` (group opacity); set opacity on each child element individually
- Use overlay layers instead of image opacity
- Use inline styles only; external CSS and `@font-face` are prohibited

---

## XI. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{PROJECT_CODE}}` | Project code       |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| Chapter title      |
| `{{PAGE_NUM}}`     | Page number        |
| `{{SOURCE}}`       | Data source        |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title |
| `{{TOC_ITEM_N_DESC}}`  | TOC item description |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Contact information |
| `{{CONFIDENTIAL}}` | Confidential label |

---

## XII. Usage Instructions

1. Copy the template to the project directory
2. Select the appropriate page template based on briefing content requirements
3. Mark content to be replaced using placeholders
4. Prioritize data charts; keep text concise
5. Generate the final SVG through the Executor role
