# {project_name} - Design Spec

> This document is the unified handoff artifact for design definition and execution constraints. It combines visual specifications, content outline, speaker-notes requirements, and implementation boundaries needed by downstream roles.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | {project_name} |
| **Canvas Format** | {canvas_info['name']} ({canvas_info['dimensions']}) |
| **Page Count** | [Filled by Strategist] |
| **Design Style** | {design_style} |
| **Target Audience** | [Filled by Strategist] |
| **Use Case** | [Filled by Strategist] |
| **Created Date** | {date_str} |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | {canvas_info['name']} |
| **Dimensions** | {canvas_info['dimensions']} |
| **viewBox** | `{canvas_info['viewbox']}` |
| **Margins** | [Recommended by Strategist, e.g., left/right 60px, top/bottom 50px] |
| **Content Area** | [Calculated from canvas] |

---

## III. Visual Theme

### Theme Style

- **Style**: {design_style}
- **Theme**: [Light theme / Dark theme]
- **Tone**: [Filled by Strategist, e.g., tech, professional, modern, innovative]

### Color Scheme

> Strategist should determine specific color values based on project content, industry, and brand colors

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#......` | Page background (light theme typically white; dark theme dark gray/navy) |
| **Secondary bg** | `#......` | Card background, section background |
| **Primary** | `#......` | Title decorations, key sections, icons |
| **Accent** | `#......` | Data highlights, key information, links |
| **Secondary accent** | `#......` | Secondary emphasis, gradient transitions |
| **Body text** | `#......` | Main body text (dark theme uses light text) |
| **Secondary text** | `#......` | Captions, annotations |
| **Tertiary text** | `#......` | Supplementary info, footers |
| **Border/divider** | `#......` | Card borders, divider lines |
| **Success** | `#......` | Positive indicators (green family) |
| **Warning** | `#......` | Issue markers (red family) |

> **Reference**: Industry colors in `references/strategist.md` or `scripts/config.py` under `INDUSTRY_COLORS`

### Gradient Scheme (if needed, using SVG syntax)

```xml
<!-- Title gradient -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#[primary]"/>
  <stop offset="100%" stop-color="#[secondary accent]"/>
</linearGradient>

<!-- Background decorative gradient (note: rgba forbidden, use stop-opacity) -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#[primary]" stop-opacity="0.15"/>
  <stop offset="100%" stop-color="#[primary]" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

> Strategist should select a font preset based on content characteristics, or customize the font combination
> Preset descriptions: P1=Modern business/tech | P2=Government docs | P3=Culture/arts | P4=Traditional/conservative | P5=English-primary

**Recommended preset**: [Fill in preset code]

| Role | Chinese | English | Fallback |
| ---- | ------- | ------- | -------- |
| **Title** | [font name] | [font name] | [font name] |
| **Body** | [font name] | [font name] | [font name] |
| **Code** | - | Consolas | Monaco |
| **Emphasis** | [font name] | [font name] | [font name] |

**Font stack**: `[Fill in CSS font-family string]`

### Font Size Hierarchy

> **Design principle**: Use body font size as baseline (1x), derive other levels proportionally
> **Unit convention**: Use px uniformly (SVG native unit) to avoid pt/px conversion errors
> **Selection principle**: Font size is based on **content density**, not design style

**Baseline**: Body font size = [fill in]px (choose 18-24px based on content density)

| Purpose | Ratio | 24px baseline (relaxed) | 18px baseline (dense) | Weight |
| ------- | ----- | ---------------------- | -------------------- | ------ |
| Cover title | 2.5-3x | 60-72px | 45-54px | Bold |
| Chapter title | 2-2.5x | 48-60px | 36-45px | Bold |
| Content title | 1.5-2x | 36-48px | 27-36px | Bold |
| Subtitle | 1.2-1.5x | 29-36px | 22-27px | SemiBold |
| **Body content** | **1x** | **24px** | **18px** | Regular |
| Annotation | 0.75-0.85x | 18-20px | 14-15px | Regular |
| Page number/date | 0.55-0.65x | 13-16px | 10-12px | Regular |

> **Tip**: Dense content (6+ points per page) use 18px; relaxed content (3-5 points per page) use 24px

---

## V. Layout Principles

### Page Structure

- **Header area**: [Height and content description]
- **Content area**: [Height and content description]
- **Footer area**: [Height and content description]

### Common Layout Modes

| Mode | Suitable Scenarios |
| ---- | ----------------- |
| **Single column centered** | Covers, conclusions, key points |
| **Left-right split (5:5)** | Comparisons, dual concepts |
| **Left-right split (4:6)** | Image-text mix |
| **Top-bottom split** | Processes, timelines |
| **Three/four column cards** | Feature lists, team introductions |
| **Matrix grid** | Comparative analysis, classifications |

### Spacing Specification

> Strategist may adjust based on project needs

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Card gap | 20-32px | [fill in] |
| Content block gap | 24-40px | [fill in] |
| Card padding | 20-32px | [fill in] |
| Card border radius | 8-16px | [fill in] |
| Icon-text gap | 8-16px | [fill in] |
| Single-row card height | 530-600px | [fill in] |
| Double-row card height | 265-295px each | [fill in] |
| Three-column card width | 360-380px each | [fill in] |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/` (6700+ icons across three libraries)
- **Usage method**: Placeholder format `{{icon:category/icon-name}}`

### Recommended Icon List (fill as needed)

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| [example] | `{{icon:interface/check-circle}}` | Slide XX |

---

## VII. Visualization Reference List (if needed)

> When the presentation includes data visualization or infographic-style structured information design, Strategist selects visualization types from `templates/charts/charts_index.json` and lists them here for the Executor to reference. The path remains under `templates/charts/` for backward compatibility.

| Visualization Type | Reference Template | Used In |
| ------------------ | ------------------ | ------- |
| [e.g. grouped_bar_chart] | `templates/charts/grouped_bar_chart.svg` | Slide 05 |

---

## VIII. Image Resource List (if needed)

| Filename | Dimensions | Ratio | Purpose | Type | Status | Generation Description |
| -------- | --------- | ----- | ------- | ---- | ------ | --------------------- |
| cover_bg.png | {canvas_info['dimensions']} | [ratio] | Cover background | [Background/Photography/Illustration/Diagram/Decorative] | [Pending/Existing/Placeholder] | [AI generation prompt] |

**Status descriptions**:

- **Pending** - Needs AI generation, provide detailed description
- **Existing** - User already has image, place in `images/`
- **Placeholder** - Not yet processed, use dashed border placeholder in SVG

**Type descriptions** (used by Image_Generator for prompt strategy selection):

- **Background** - Full-page background for covers/chapters, reserve text area
- **Photography** - Real scenes, people, products, architecture
- **Illustration** - Flat design, vector style, cartoon, concept diagrams
- **Diagram** - Flowcharts, architecture diagrams, concept maps
- **Decorative** - Partial decorations, textures, borders, dividers

---

## IX. Content Outline

### Part 1: [Chapter Name]

#### Slide 01 - Cover

- **Layout**: Full-screen background image + centered title
- **Title**: [Main title]
- **Subtitle**: [Subtitle]
- **Info**: [Author / Date / Organization]

#### Slide 02 - [Page Name]

- **Layout**: [Choose layout mode]
- **Title**: [Page title]
- **Visualization**: [visualization_type] (see VII. Visualization Reference List)
- **Content**:
  - [Point 1]
  - [Point 2]
  - [Point 3]

> **Visualization field**: Only add when the page includes data visualization or structured infographic elements. Visualization type must be listed in section VII.

---

[Strategist continues adding more pages based on source document content and page count planning...]

---

## X. Speaker Notes Requirements

Generate corresponding speaker note files for each page, saved to the `notes/` directory:

- **File naming**: Match SVG names, e.g., `01_cover.md`
- **Content includes**: Script key points, timing cues, transition phrases

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `{canvas_info['viewbox']}`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle (see shared-standards.md §1.1)

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
