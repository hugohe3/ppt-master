---
layout_id: government_blue
kind: layout
native_structure_mode: template
summary: Key project briefings, Five-Year Plan presentations, work summaries, investment promotion, policy interpretation.
canvas_format: ppt169
page_count: 5
page_types: [cover, toc, chapter, content, ending]
---

# Government Blue Style Template - Design Specification

> Suitable for government agency briefings, key project presentations, planning proposals, investment promotion, and similar scenarios across all levels of government.

---

## I. Template Overview

| Property       | Description                                                  |
| -------------- | ------------------------------------------------------------ |
| **Template Name** | government_blue (Government Blue Template)                |
| **Use Cases**  | Key project briefings, Five-Year Plan presentations, work summaries, investment promotion, policy interpretation |
| **Design Tone** | Grand, tech-forward, modern, professional government style  |
| **Theme Mode** | Light theme (white background + blue gradient accents)       |

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
| **Top**    | y=0, h=6px      | Blue gradient bar (bright blue → deep blue), full width |
| **Title Bar** | y=30, h=50px | Section number block + title text + top-right logo |
| **Content Area** | y=100, h=560px | Main content area                 |
| **Footer** | y=680, h=40px   | Page number, organization name, bottom decoration line |

### Navigation Bar Design

- **Top Decoration Line**: Blue gradient (`#00B4D8` → `#0050B3`), height 6px, full width
- **Bottom Decoration Line**: Deep blue (`#0050B3`), height 4px, y=716
- **Title Bar** (y=30):
  - Section number block: Deep blue square (50×50px), white number centered
  - Title text: 20px from number block, 28px font size, `#1A1A1A`
  - Top-right logo: Fixed at x=1107, dimensions 113×50px

---

## IV. Page Types

### 1. Cover Page (01_cover.svg)

- Deep blue gradient background + tech grid texture
- Left-side bright blue accent bar
- Main title + subtitle (white)
- Presenter/Organization info
- Bottom date area
- Geometric decorative circles

### 2. Table of Contents (02_toc.svg)

- Light blue gradient background
- Left-side decorative trapezoid + gradient vertical bar
- Supports up to 5 chapters
- Circular numbering + connector line design
- Floating card effect (simulated with solid colors)

### 3. Chapter Page (02_chapter.svg)

- Deep blue gradient background
- Radial glow decoration
- Large chapter number (semi-transparent + stroke effect)
- Chapter title + English subtitle
- Bright blue accent bar

### 4. Content Page (03_content.svg)

- Light gradient background
- Gradient number block
- Dashed divider lines
- Flexible content area
- Supports multiple layout modes

### 5. Ending Page (04_ending.svg)

- Deep blue gradient background
- Wave curve decoration
- Centered thank-you message (Chinese and English)
- Bright blue divider line
- Contact information

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

## VIII. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{AUTHOR}}`       | Organization name (Chinese) |
| `{{AUTHOR_EN}}`    | Organization name (English) |
| `{{PRESENTER}}`    | Presenter          |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{PAGE_NUM}}`     | Page number        |
| `{{DATE}}`         | Date               |
| `{{ORGANIZATION}}` | Full organization name |
| `{{ORG_SHORT}}`    | Abbreviated organization name |
| `{{CONTACT_INFO}}` | Contact information |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title |
| `{{TOC_ITEM_N_DESC}}`  | TOC item description |
| `{{LOGO_HEADER}}`  | Header logo filename |

---

## IX. Usage Instructions

1. Copy the template to the project directory
2. Replace logo files in the images directory (if applicable)
3. Select the appropriate page template based on content requirements
4. Mark content to be replaced using placeholders
5. Generate the final SVG through the Executor role

---

## X. Design Highlights

- **Tech Gradient**: Bright-to-deep blue gradient reflects a modern tech aesthetic
- **Geometric Decorative Elements**: Circles and grids add a tech atmosphere
- **Wave Curves**: Dynamic decoration on the ending page
- **Floating Card Effect**: Modern design for the table of contents page
- **Clear Visual Hierarchy**: Ensures efficient information delivery
