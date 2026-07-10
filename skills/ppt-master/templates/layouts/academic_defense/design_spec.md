---
layout_id: academic_defense
kind: layout
native_structure_mode: template
summary: Thesis defense, academic presentations, research progress reports, grant applications.
canvas_format: ppt169
page_count: 5
page_types: [cover, toc, chapter, content, ending]
---

# Academic Defense Template - Design Specification

> Suitable for academic thesis defense, research presentations, graduation project showcases, and similar scenarios.

---

## I. Template Overview

| Property       | Description                                            |
| -------------- | ------------------------------------------------------ |
| **Template Name** | academic_defense                                    |
| **Use Cases**  | Thesis defense, academic presentations, research progress reports, grant applications |
| **Design Tone** | Professional, rigorous, research-oriented, clear hierarchy |
| **Theme Mode** | Light theme (white background + dark blue title bar)   |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 40px, Top 0px, Bottom 35px |
| **Safe Area**  | x: 40-1240, y: 70-665        |

---

## III. Page Structure

### General Layout

| Area           | Position/Height | Description                            |
| -------------- | --------------- | -------------------------------------- |
| **Header**     | y=0, h=70px     | Dark blue background + red left bar + page title |
| **Key Message Bar** | y=70, h=50px | Core message/summary area (light blue-gray background) |
| **Content Area** | y=135, h=515px | Main content area                    |
| **Footer**     | y=665, h=55px   | Data source, section name, page number |

### Decorative Elements

- **Left Red Bar**: Red (`#CC0000`), width 6px, used for header and card decoration
- **Blue Border**: Accent blue (`#0066CC`), used for card borders
- **Decorative Divider**: Blue (`#0066CC`), paired with decorative dots

---

## IV. Page Types

### 1. Cover Page (01_cover.svg)

- White background
- Dark blue top bar + red left vertical bar decoration
- Top-right Logo placeholder area
- Centered main title + subtitle
- Decorative divider line (blue + dots)
- Presenter info area (name, advisor, institution)
- Bottom gray info area (date)

### 2. Table of Contents Page (02_toc.svg)

- White background
- Standard header (dark blue + red vertical bar)
- Card-style TOC item layout (2 columns)
- Light blue-gray background cards + left colored vertical bar
- Optional items use dashed borders

### 3. Chapter Page (02_chapter.svg)

- Dark blue full-screen background (`#003366`)
- Right-side geometric decorations
- Left red vertical bar decoration
- Large semi-transparent background number
- Prominent white chapter title
- Light blue-gray chapter description
- Red decorative horizontal line

### 4. Content Page (03_content.svg)

- White background
- Standard header (dark blue + red vertical bar)
- Key message bar (light blue-gray background + blue left vertical bar)
- Flexible content area
- Footer: data source, section name, page number

### 5. Ending Page (04_ending.svg)

- White background
- Dark blue top bar
- Centered thank-you message
- Tagline
- Decorative divider line
- Contact info card (gray background)
- Bottom gray area (copyright, page number)

---

## V. SVG Page Roster

| File | Role | Description |
|------|------|-------------|
| `01_cover.svg` | cover | Title slide; project name, presenter, date |
| `02_chapter.svg` | chapter | Chapter divider page (large number + chapter title) |
| `02_toc.svg` | toc | Table of contents listing major sections |
| `03_content.svg` | content | Main content page; body of the deck |
| `04_ending.svg` | ending | Closing/thank-you page |

## VI. Layout Patterns

| Pattern            | Use Cases                      |
| ------------------ | ------------------------------ |
| **Single Column Centered** | Cover, ending, key points |
| **Two-Column Cards** | Table of contents            |
| **Left-Right Split (5:5)** | Comparison display      |
| **Left-Right Split (4:6)** | Image-text mixed layout |
| **Card Grid**      | Research content list           |
| **Timeline**       | Research progress               |
| **Table**          | Data comparison, experiment results |

---

## VII. Spacing Guidelines

| Element            | Value  |
| ------------------ | ------ |
| Card gap           | 20px   |
| Content block gap  | 24px   |
| Card padding       | 20px   |
| Card border radius | 8px    |
| Icon-to-text gap   | 12px   |

---

## VIII. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; no `rgba()`
5. Prohibited: `mask`, `<style>`, `class`, `foreignObject`. `clipPath` is allowed only on `<image>` under `shared-standards.md` §1.2
6. Prohibited: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed (marker in `<defs>`, `orient="auto"`, shape = triangle/diamond/oval) — see shared-standards.md §1.1

### PPT Compatibility Rules

- `<g opacity="0..1">` is allowed as per-descendant alpha; overlapping children may composite differently
- `<image opacity="0..1">` maps to native picture transparency; use overlays only for color washes
- Inline styles only; no external CSS or `@font-face`

---

## IX. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Thesis/project main title |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{AUTHOR}}`       | Presenter name     |
| `{{ADVISOR}}`      | Advisor            |
| `{{INSTITUTION}}`  | University/institution |
| `{{DATE}}`         | Defense date       |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{SECTION_NUM}}`  | Section number     |
| `{{CHAPTER_NUM}}`  | Chapter number (large) |
| `{{CHAPTER_TITLE}}`| Chapter title      |
| `{{CHAPTER_DESC}}` | Chapter description |
| `{{KEY_MESSAGE}}`  | Key message        |
| `{{PAGE_NUM}}`     | Page number        |
| `{{SOURCE}}`       | Data source        |
| `{{SECTION_NAME}}` | Section name (footer) |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title (N=1..n) |
| `{{TOC_ITEM_N_DESC}}` | TOC item description (N=1..n) |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{ENDING_SUBTITLE}}` | Ending subtitle/tagline |
| `{{CONTACT_INFO}}` | Contact information |
| `{{EMAIL}}`        | Email address      |
| `{{COPYRIGHT}}`    | Copyright info     |
| `{{LOGO}}`         | Logo text          |

---

## X. Component Specifications

### 1. Tag

```xml
<!-- Blue background white text tag -->
<rect x="40" y="150" width="80" height="28" fill="#0066CC" rx="4"/>
<text x="80" y="170" text-anchor="middle" fill="#FFFFFF" font-size="14" font-weight="bold">内容详解</text>

<!-- Red background white text tag (emphasis) -->
<rect x="40" y="150" width="80" height="28" fill="#CC0000" rx="4"/>
<text x="80" y="170" text-anchor="middle" fill="#FFFFFF" font-size="14" font-weight="bold">核心目标</text>
```

### 2. Flow Arrow

```xml
<!-- Horizontal flow arrow -->
<line x1="200" y1="300" x2="350" y2="300" stroke="#0066CC" stroke-width="2"/>
<polygon points="350,295 360,300 350,305" fill="#0066CC"/>
```

### 3. Data Highlight Box

```xml
<!-- Key data block -->
<rect x="40" y="400" width="200" height="80" fill="#FFFFFF" stroke="#CC0000" stroke-width="2" rx="8"/>
<text x="140" y="445" text-anchor="middle" fill="#CC0000" font-size="24" font-weight="bold">30%</text>
<text x="140" y="470" text-anchor="middle" fill="#666666" font-size="12">关键指标</text>
```

---

## XI. Usage Instructions

1. Copy the template to the project directory
2. Select the appropriate page template based on defense content needs
3. Use placeholders to mark content that needs replacement
4. Ensure presenter info and advisor info are complete
5. Generate the final SVG through the Executor role
