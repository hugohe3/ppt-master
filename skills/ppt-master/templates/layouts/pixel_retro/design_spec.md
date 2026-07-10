---
layout_id: pixel_retro
kind: layout
native_structure_mode: template
summary: Tech talks, programming tutorials, game introductions, geek-style showcases.
canvas_format: ppt169
page_count: 5
page_types: [cover, toc, chapter, content, ending]
---

# Pixel Retro Style Template - Design Specification

> Suitable for tech talks, programming tutorials, game-related presentations, geek-style content showcases, and similar scenarios.

---

## I. Template Overview

| Property       | Description                                                |
| -------------- | ---------------------------------------------------------- |
| **Template Name** | pixel_retro (Pixel Retro Template)                      |
| **Use Cases**  | Tech talks, programming tutorials, game introductions, geek-style showcases |
| **Design Tone** | Retro gaming, neon cyberpunk, geek tech, 8-bit style      |
| **Theme Mode** | Dark theme (deep space black background + neon accents)    |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 60px, Top 50px, Bottom 40px |
| **Safe Area**  | x: 60-1220, y: 50-680         |

---

## III. Page Structure

### General Layout

| Area       | Position/Height | Description                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=4-6px    | Neon green decoration line (dual-line effect) |
| **Title Area** | y=50, h=70px | Page title + English subtitle         |
| **Content Area** | y=130, h=510px | Main content area                  |
| **Footer** | y=680, h=40px   | Page number, decoration line, progress indicator |

### Decorative Elements

- **Top Decoration Line**: Neon green dual lines (main line 4px + auxiliary line 2px)
- **Bottom Decoration Line**: Neon green dual lines (auxiliary line 4px + main line 4px)
- **Pixel Blocks**: Corner decorations with decreasing opacity (100% → 60% → 30%)
- **Scanline Grid**: Optional low-opacity background grid lines

---

## IV. Page Types

### 1. Cover Page (01_cover.svg)

- Deep space black background
- Top/bottom neon decoration lines
- Pixel-style console graphic (optional)
- Main title (neon green glow effect)
- Subtitle (moonlight white)
- Function button group (horizontal layout)
- Bottom prompt text (e.g., "PRESS START")

### 2. Table of Contents (02_toc.svg)

- Deep space black background
- Standard top decoration
- Chapter list (with importance labels)
  - Red: Essential / Must-learn
  - Yellow: Recommended
  - Green: Optional
- Pixel-style list design

### 3. Chapter Page (02_chapter.svg)

- Deep space black background
- Full-screen neon effect
- Large chapter number (glow effect)
- Chapter title + English subtitle
- Pixel-style decorative frame

### 4. Content Page (03_content.svg)

- Deep space black background
- Standard top decoration
- Page title (neon green + glow)
- English subtitle (mist gray)
- **Fully open content area** (y=140 to y=670, width 1160px)
- Bottom page number

> **Design Principle**: The content page template only provides the page frame (title area + footer). The content area is freely designed by the Executor based on actual content. Available layouts include but are not limited to: cards, progress bars, tables, timelines, comparison charts, etc.

### 5. Ending Page (04_ending.svg)

- Deep space black background
- Neon glow main title
- Summary card group
- "GAME SAVED" visual effect
- Progress button group

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
| **Two Columns (5:5)** | Comparative display (e.g., Git vs GitHub) |
| **Dual-Column Cards** | Feature lists, trait comparisons |
| **Three-Column Cards** | Key takeaways, project lists |
| **Progress Bar Display** | Data statistics, usage rates |
| **Timeline**       | History, processes, workflows  |

---

## VII. Spacing Guidelines

| Element          | Value  |
| ---------------- | ------ |
| Card spacing     | 20-30px |
| Content block spacing | 30px |
| Card padding     | 20-24px |
| Card border radius | 0px (blocky feel) or 4px |
| Border width     | 2-3px  |
| Icon-to-text gap | 12px   |

---

## VIII. Visual Effects

### Pixel Style Characteristics

- Blocky icons and decorations
- Use block characters such as: full block, dark shade, light shade, upper half, lower half, small black/white squares for decoration
- Progress bars filled with blocks
- Borders use double lines or dotted patterns
- Card corners with pixel decoration blocks

### Neon Glow Effect

Apply glow filters to key text/elements:

```xml
<defs>
  <filter id="glowGreen" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3-4" result="blur" />
    <feMerge>
      <feMergeNode in="blur" />
      <feMergeNode in="SourceGraphic" />
    </feMerge>
  </filter>
</defs>

<!-- Usage -->
<text filter="url(#glowGreen)" fill="#39FF14">Glowing Text</text>
```

> **Note**: `filter` effects are typically ignored in PPT, but render well in SVG-compatible viewers.

### Emoji Usage

- 🎮 Game/Save
- 💾 Save
- 🔀 Branch/Merge
- 📁 Folder
- 📝 Document
- 🚀 Release
- ⏪ Revert
- 👾 Developer
- 🌐 Network/Cloud
- ✅ Confirm/Success
- 🎯 Target/Key Point
- 🤔 Question/Thinking

---

## IX. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. CSS alpha colors and explicit `fill-opacity` / `stroke-opacity` are both supported; values multiply
5. Prohibited: `mask`, `<style>`, `class`, `foreignObject`. `clipPath` is allowed only on `<image>` under `shared-standards.md` §1.2
6. Prohibited: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed (marker in `<defs>`, `orient="auto"`, shape = triangle/diamond/oval) — see shared-standards.md §1.1

### PPT Compatibility Rules

- `<g opacity="0..1">` is allowed as per-descendant alpha; overlapping children may composite differently
- `<image opacity="0..1">` maps to native picture transparency; use overlays only for color washes
- Use inline styles only; external CSS and `@font-face` are prohibited
- `filter` effects serve as enhancements (allowed) and do not affect baseline display

---

## X. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{AUTHOR}}`       | Author/Organization |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{PAGE_TITLE_EN}}`| Page title (English) |
| `{{CONTENT_AREA}}` | Flexible content area |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{PAGE_NUM}}`     | Page number        |
| `{{TOTAL_PAGES}}`  | Total page count   |
| `{{VERSION}}`      | Version number     |
| `{{TOC_ITEM_N_TITLE}}` | TOC item title |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Primary contact info |

---

## XI. Usage Instructions

1. Copy the template to the project `templates/` directory
2. Select the appropriate page template based on content requirements
3. Mark content to be replaced using placeholders
4. Generate the final SVG through the Executor role
5. Define glow effects using `filter` (within `<defs>`)
6. Maintain consistency of the neon color scheme

---

## XII. Color Quick Reference

```
Background Layer:
  Main background    #0D1117  Deep Space Black
  Card background    #161B22  Starry Night Blue
  Borders            #30363D  Dark Border

Accent Colors (use in order):
  Primary accent     #39FF14  Neon Green
  Secondary accent   #FF2E97  Cyber Pink
  Tertiary accent    #00D4FF  Electric Blue
  Quaternary accent  #FFD700  Gold Yellow

Text:
  Primary text       #E6EDF3  Moonlight White
  Secondary text     #8B949E  Mist Gray
  Emphasis text      #FFFFFF  Pure White
```
