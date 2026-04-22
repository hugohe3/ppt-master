# {project_name} - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

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

> **Per-role families are expected, not optional.** Title / Body / Emphasis / Code may each use a different family — for example, a display serif for titles paired with a geometric sans for body. A deck is not required to stick to one family throughout. See [strategist.md §g — Font Combinations](../references/strategist.md) for common starting directions; you are free to propose a combination not in that list.
>
> **⚠️ PPT-safe stack discipline (HARD rule).** PPTX stores a single `typeface` per text run — no runtime fallback. Every stack below MUST end with a cross-platform pre-installed font (`"Microsoft YaHei", sans-serif` / `SimSun, serif` / `Arial, sans-serif` / `"Times New Roman", serif` / `Consolas, "Courier New", monospace`). Stacks that lead with a non-pre-installed font (Inter / Google Fonts families / brand typefaces) are only allowed when this spec explicitly notes the font-install or font-embedding requirement.

**Typography direction**: [Fill in one phrase, e.g., "modern CJK sans" / "academic serif" / "brand-specific: McKinsey Bower (requires font install)"]

Two views on the same font decisions — fill both, keep them consistent:

- **Role breakdown** (below table) — lists the *pieces* for each role: what CJK font, what Latin font, what CSS generic fallback. This is the human-readable design language.
- **Per-role font stacks** (after the table) — the *ordered* CSS `font-family` strings that actually go into SVG `font-family=""` attributes and into `spec_lock.md`'s `*_family` lines. Order matters because it controls browser character rendering (Latin-led vs. CJK-led) — so this view is the **actual data**, not derivable from the table alone.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | [e.g., `"Microsoft YaHei"`, or `"Microsoft YaHei", "PingFang SC"` for macOS preview nicety] | [e.g., `Georgia`] | [e.g., `serif`] |
| **Body** | [e.g., `"Microsoft YaHei", "PingFang SC"`] | [e.g., `Arial`] | [e.g., `sans-serif`] |
| **Emphasis** | [e.g., `SimSun`, or `—` for Latin-only] | [e.g., `Georgia`] | [e.g., `serif`] |
| **Code** | — | [e.g., `Consolas, "Courier New"`] | [e.g., `monospace`] |

**Per-role font stacks** (CSS `font-family` strings, one per role — arrange the table's pieces in the order your design intends):

- Title: `[Fill in stack, e.g. Georgia, "Microsoft YaHei", serif for Latin-led; or "Microsoft YaHei", "PingFang SC", Georgia, serif for CJK-led]`
- Body: `[Fill in stack — may be same as Title]`
- Emphasis: `[Fill in stack, or write "same as Body" to omit the override]`
- Code: `[Fill in monospace stack, e.g. Consolas, "Courier New", monospace]`

> **Stack ordering — why it matters**: CSS `font-family` falls back font-by-font (not char-by-char with all fonts parallel) — the browser uses the **first installed** font in the stack for everything it can render, and only skips to the next font when that font lacks a glyph for a specific character. So:
> - `Georgia, "Microsoft YaHei", serif` → Latin characters render in Georgia (elegant serif), CJK characters fall through to Microsoft YaHei. **Use this when Latin typography is the primary design statement** (academic / editorial / Latin-heavy covers).
> - `"Microsoft YaHei", Georgia, serif` → Everything renders in Microsoft YaHei (including Latin, using YaHei's Latin glyphs — a different design tone). **Use this when the deck is CJK-primary and Latin characters are incidental**.
>
> The converter (`drawingml_utils.py parse_font_family`) maps these to PPTX `<a:latin>` / `<a:ea>` typefaces regardless of order — but the browser preview and the SVG's native rendering reflect stack order, so pick the order that matches your design intent.

> **Why two views**: the role breakdown is compact and shows font role assignment at a glance; the stacks carry the ordering information the breakdown can't encode. Keep the fonts consistent between the two — the table's cells should be exactly the fonts that appear in the stacks (in any order).

### Font Size Hierarchy

> **Ramp discipline, not a fixed menu.** The `body` baseline is the single anchor; every other size is a ratio of it. The table below is a **ramp** — each row gives the allowed ratio band for that role, and Executor may pick any px value inside the band during generation (e.g., 40px hero number, 13px chart annotation, 72px cover headline) without having to pre-declare every intermediate value in `spec_lock.md`.
> **Unit convention**: Use px uniformly (SVG native unit) to avoid pt/px conversion errors.
> **Baseline selection**: Drive by **content density**, not design style.

**Baseline**: Body font size = [fill in]px (choose 18-24px based on content density)

| Purpose | Ratio to body | 24px baseline (relaxed) | 18px baseline (dense) | Weight |
| ------- | ------------- | ---------------------- | -------------------- | ------ |
| Cover title (hero headline) | 2.5-5x | 60-120px | 45-90px | Bold / Heavy |
| Chapter / section opener | 2-2.5x | 48-60px | 36-45px | Bold |
| Page title | 1.5-2x | 36-48px | 27-36px | Bold |
| Hero number (consulting KPIs) | 1.5-2x | 36-48px | 27-36px | Bold |
| Subtitle | 1.2-1.5x | 29-36px | 22-27px | SemiBold |
| **Body content** | **1x** | **24px** | **18px** | Regular |
| Annotation / caption | 0.7-0.85x | 17-20px | 13-15px | Regular |
| Page number / footnote | 0.5-0.65x | 12-16px | 9-12px | Regular |

> Sizes outside **every** band remain forbidden — surface the need and extend `spec_lock.md typography` (e.g., add `cover_title: 96`) rather than invent a one-off value.

> **Tip**: Dense content (6+ points per page) use 18px; relaxed content (3-5 points per page) use 24px

---

## V. Layout Principles

### Page Structure

- **Header area**: [Height and content description]
- **Content area**: [Height and content description]
- **Footer area**: [Height and content description]

### Layout Pattern Library (combine or break as content demands)

> **Principle — proportion follows information weight, not preset ratios.** The table below is a **pattern library**, not a menu. Executor may combine two patterns on one page, break the grid entirely for a `breathing` page, or propose a pattern not listed here when the content calls for it. Defaulting every page to a symmetric grid is what produces the "AI-generated" look — vary intentionally.

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | Covers, conclusions, key points |
| **Symmetric split (5:5)** | Comparisons where two sides carry equal weight |
| **Asymmetric split (3:7 / 2:8)** | One side dominates — data chart vs. brief takeaway, image vs. caption |
| **Top-bottom split** | Processes, timelines, ultra-wide image + text |
| **Three/four column cards** | Feature lists, parallel points, team intros |
| **Matrix grid (2×2)** | Two-axis classifications, strategic quadrants |
| **Z-pattern / waterfall** | Storytelling, case studies — content blocks alternate left/right guiding the eye |
| **Center-radiating** | Core concept + surrounding nodes, ecosystem / stakeholder maps |
| **Full-bleed + floating text** | `breathing` / feature pages — image fills canvas, text floats with opacity overlay |
| **Figure-text overlap** | Hero moments — headline / big number sits over or against an image edge instead of beside it |
| **Negative-space-driven** | A single element in 40-60% whitespace — lets one idea land with weight |

### Spacing Specification

> Spacing defaults depend on **container type**. Cards are one option, not the universal default. The tables below split by container type; a page may use only one set (e.g., a `breathing` page with no cards only consults the universal and non-card entries).

**Universal** (any container type):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 40-60px | [fill in] |
| Content block gap | 24-40px | [fill in] |
| Icon-text gap | 8-16px | [fill in] |

**Card-based layouts** (consult only when the page uses cards — typically `dense` pages with parallel containers):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Card gap | 20-32px | [fill in] |
| Card padding | 20-32px | [fill in] |
| Card border radius | 8-16px | [fill in] |
| Single-row card height | 530-600px | [fill in] |
| Double-row card height | 265-295px each | [fill in] |
| Three-column card width | 360-380px each | [fill in] |

**Non-card containers** (naked text blocks / full-bleed imagery / divider-separated content — typical for `breathing` pages or minimalist designs):

- Block-to-block vertical rhythm is carried by **whitespace**, not gutters — block gaps tend to run wider than card gaps since there is no container edge to help separate content.
- **Line-height (leading)**: 1.4-1.6× body font size — standard typographic convention.
- **Full-bleed text placement**: inset text away from the image's visual focal points; legibility over photographic backgrounds typically requires a gradient or opacity overlay layer.
- **Content width** is driven by reading comfort and image composition, not by a card grid slot — avoid back-computing "column width" when there is no column.

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

- **Layout**: [Choose a pattern from §V, combine two, or break the grid as the content demands]
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
