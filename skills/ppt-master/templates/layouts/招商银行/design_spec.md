# China Merchants Bank (招商银行) - Design Specification v2.0

> Suitable for China Merchants Bank and financial institutions' high-end work reports, business showcases, annual reports, VIP client services, and similar scenarios.

---

## I. Template Overview

| Property       | Description                                                |
| -------------- | ---------------------------------------------------------- |
| **Template Name** | 招商银行                                                |
| **Use Cases**  | High-end work reports, business showcases, annual reports, product promotion |
| **Design Tone** | Minimalist luxury, refined, multi-layered, modern finance  |
| **Theme Mode** | Light theme (subtle textured background + CMB red/gold refined accents) |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`               |
| **Safe Margins** | 40px (left/right), 35px (top/bottom) |
| **Safe Area**  | x: 40-1240, y: 70-665        |
| **Grid Base**  | 40px                          |

---

## III. Color Scheme

### Core Colors

| Role             | Color Value | Notes                            |
| ---------------- | ----------- | -------------------------------- |
| **CMB Red**      | `#C41230`   | Brand primary, used for accents, title bars |
| **Auxiliary Gold** | `#C9A962` | Luxury accent for double-line borders, decorations |
| **Dark Red**     | `#9A0E26`   | Deep background color for added depth |
| **Background White** | `#FFFFFF` | Card and highlight area backgrounds |
| **Subtle Texture White** | `#FAFAFA` | Very light background to avoid harsh pure white |
| **Warm Gray Accent** | `#F8F6F3` | Bottom decorative bars, card backgrounds |

### Safe Area Anchor Points (New Minimalist Decoration)

```xml
<!-- Four-corner anchor points (replacing legacy card borders) -->
<path d="M40 140 L50 140 M40 140 L40 150" stroke="#C9A962" stroke-width="1" stroke-opacity="0.5" />
<path d="M1240 140 L1230 140 M1240 140 L1240 150" stroke="#C9A962" stroke-width="1" stroke-opacity="0.5" />
```

---

## IV. Typography System

### Font Stack

**Font Stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`

### Font Size Hierarchy

| Level    | Usage              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | Cover main title   | 52px    | Bold    |
| H2       | Page title         | 24-28px | Bold    |
| H3       | Chapter title      | 52px    | Bold    |
| H4       | Subsection / Card title | 20-22px | Bold |
| P        | Body content       | 16-18px | Regular |
| Caption  | Auxiliary notes    | 12-14px | Regular |
| Number   | Chapter number     | 320px   | Bold (Low Opacity) |

---

## V. Page Structure

### Common Layout

| Area       | Position/Height | Description                            |
| ---------- | --------------- | -------------------------------------- |
| **Header** | y=0-75          | Red background with gold lines, top-left ring decoration |
| **Key Message Bar** | y=95-120 | (Content pages) Minimalist red line guide + text |
| **Content** | y=140-650      | Open layout with no fixed borders      |
| **Footer** | y=665+          | Page number, copyright, institution name |

### Core Decorative Design (Design DNA)

1. **Refined Double Lines**: 1px main line + 3px auxiliary line combination, simulating high-end print craftsmanship.
2. **Multi-Layer Concentric Circles**: Abstract representation of CMB's sunflower logo, adding visual depth.
3. **Micro Dot-Matrix Texture**: Arrays of tiny dots for added visual breathing room.
4. **Diamond Dividers**: Diamond-shaped decorations at title division points for a refined touch.

---

## VI. Page Types

### 1. Cover Page (01_cover.svg)

- **Background**: White main background + bottom warm gray decorative band.
- **Top**: Red horizontal bar + gold double lines.
- **Decoration**: Multi-layer concentric rings at top-left, vertical decorative lines at right edge.
- **Title Area**: Centered layout with rounded border and diamond divider line.

### 2. Table of Contents (02_toc.svg)

- **Header**: Fixed "目录 / CONTENTS" title.
- **List**: Left-right dual-column **checklist layout** (no background cards).
- **Design**: Uses "large red number + title + gold underline" combination for strong adaptability.
- **Decoration**: Left side features vertical lines and decorative "Index" text.

### 3. Chapter Page (02_chapter.svg)

- **Background**: Full-screen dark red background (`#9A0E26`).
- **Visual Center**: Left-side gold vertical bar with title combination.
- **Right Side**: Complex gold horizontal bar staircase effect + diagonal line texture.
- **Background Text**: Giant semi-transparent chapter numbers.

### 4. Content Page (03_content.svg)

- **Layout**: **Fully open layout**, removing center borders to maximize content display area.
- **Key Message**: Top area presented with minimalist left-side red line + text, reducing visual distraction.
- **Boundary**: Only very faint "safe area anchor points" retained at four corners.
- **Footer**: Contains data source, page number, and chapter name.

### 5. Ending Page (04_ending.svg)

- **Echo**: Layout closely mirrors the cover page, creating a cohesive bookend.
- **Contact Info**: Wide contact information card at the bottom.
- **Decoration**: Symmetrical multi-layer gold concentric rings on left and right.

---

## VII. Layout Patterns (Recommended)

### 1. Key Message Layout
- Use the top gray message bar to present a one-sentence key conclusion.
- Pair with a single large chart or emphasized text below.

### 2. Card Grid
- Place 2x2 or 3x2 data cards within the white content area.
- Recommended card backgrounds: `#FDF2F4` (light red) or `#F8F6F3` (warm gray).

### 3. Split Column Comparison
- Left side presents current state / problems; right side presents solutions / results.
- Gold arrows can serve as logical connectors in the middle.

---

## VIII. Spacing Guidelines

| Property       | Value | Description              |
| -------------- | ----- | ------------------------ |
| **Base Unit**  | 4px   | All spacing should be multiples of 4px |
| **Module Gap** | 40px  | Standard gap between major modules |
| **Card Gap**   | 24px  | Gap between cards        |
| **Inner Padding** | 20px | Padding inside cards    |
| **Line Height** | 1.5  | Standard body line height |

---

## IX. SVG Technical Constraints

### Mandatory Rules

1. viewBox fixed at `0 0 1280 720`
2. Background must include a full-screen `<rect>`
3. Text wrapping via `<tspan>`
4. Opacity must use `fill-opacity` / `stroke-opacity`
5. Arrows must use `<polygon>`, no `marker`

### Forbidden Elements (Blacklist)

- `clipPath`, `mask` (clipping/masking)
- `<style>`, `class` (stylesheets; `id` within `<defs>` is allowed)
- `foreignObject` (foreign objects)
- `textPath` (text on path)
- `animate`, `animateTransform`, `set` (animations)

- `rgba()` color format (must use hex + opacity)
- `<g opacity="...">` (group opacity — set individually on each element)

---

## X. Placeholder Specification

| Placeholder           | Description        |
| --------------------- | ------------------ |
| `{{TITLE}}`           | Main title         |
| `{{SUBTITLE}}`        | Subtitle           |
| `{{AUTHOR}}`          | Presenter name     |
| `{{DATE}}`            | Date               |
| `{{CHAPTER_NUM}}`     | Chapter number     |
| `{{CHAPTER_TITLE}}`   | Chapter title      |
| `{{CHAPTER_DESC}}`    | Chapter description |
| `{{PAGE_TITLE}}`      | Page title         |
| `{{KEY_MESSAGE}}`     | Key message        |
| `{{CONTENT_AREA}}`    | Content area identifier |
| `{{TOC_ITEM_N_TITLE}}`| TOC item title (N=1..n) |
| `{{TOC_ITEM_N_DESC}}` | TOC item description (N=1..n) |
| `{{THANK_YOU}}`       | Closing message    |
| `{{ENDING_SUBTITLE}}` | Ending subtitle    |
| `{{CONTACT_INFO}}`    | Contact information |

---

## XI. Usage Notes

1. **Logo Adaptation**: Recommend using white inverted Logo.
2. **Font Installation**: Recommend installing "Microsoft YaHei" or an equivalent sans-serif font.
3. **Extended Colors**: If additional colors are needed, maintain the red-gold ratio unchanged.
