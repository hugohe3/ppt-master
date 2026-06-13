# Visual Styles — Index

A **visual style** is how the deck **looks** — shape language, decoration density, whitespace rhythm, typographic character, texture / elevation. Lock **one per deck**; it anchors the aesthetic of the SVG layout itself (cards, dividers, spacing, corner radius, shadow use).

> **Styles carry NO HEX and lock no palette.** Color truth lives in `design_spec.colors` / `spec_lock.colors` (confirmation `e`); color *behavior* lives in [`image-palettes/`](../image-palettes/). A visual style only describes how the deck's existing colors are *used* — never which colors. (Same discipline as [`image-renderings/`](../image-renderings/) for AI images.)
>
> A visual style is *not* a mode. **Visual style = how it looks; mode = how you argue** (see [`modes/_index.md`](../modes/_index.md)). Locked independently — any style pairs with any mode.

---

## 1. Catalog

Each style has its own file with: shape & decoration, typography character, color-usage discipline (no HEX), texture / elevation, and the paired image-rendering. **Read only the file for the style you lock** — never glob the directory. The catalog mirrors [`image-renderings`](../image-renderings/_index.md): each style's "Paired rendering" names the illustration family that shares its aesthetic.

### 1.1 Structured / graphic

| Visual style | Character | Best for | Paired rendering |
|---|---|---|---|
| [`swiss-minimal`](./swiss-minimal.md) | Grid-locked, sharp, aggressive whitespace, no decoration | High-end consulting, architecture, type-led | `minimalist-swiss` |
| [`editorial`](./editorial.md) | Magazine hierarchy, rules & columns, serif/sans interplay | Finance, journalism, analysis, explainers | `editorial` |
| [`soft-rounded`](./soft-rounded.md) | Rounded cards, gentle elevation, approachable | Product, SaaS, training, consumer | `flat` / `glassmorphism` |
| [`dark-tech`](./dark-tech.md) | Dark canvas, glow accents, geometric precision | Tech, AI, data products, launches | `digital-dashboard` |
| [`blueprint`](./blueprint.md) | Schematic line work on dark paper, isometric, annotated | Technical briefings, architecture, engineering | `blueprint` |
| [`brutalist`](./brutalist.md) | Newsprint density, ruled boxes, raw structure, flat | Annual reviews, research digests, manifestos | `screen-print` / `editorial` |

### 1.2 Expressive / print

| Visual style | Character | Best for | Paired rendering |
|---|---|---|---|
| [`memphis`](./memphis.md) | Clashing color blocks, geometric confetti, bold outlines | Festivals, consumer, youth, launch hype | `flat` |
| [`zine`](./zine.md) | Riso misregistration, halftone, limited palette, print grit | Culture, design talks, indie brands | `screen-print` |
| [`vintage-poster`](./vintage-poster.md) | Mid-century flat blocks, halftone, retro-geometric warmth | Heritage, hospitality, cultural, anniversaries | `vintage-poster` |
| [`paper-cut`](./paper-cut.md) | Layered cut-paper sheets, soft inter-layer shadow, tactile | Cultural / folk, children, festival, sustainability | `paper-cut` |

### 1.3 Hand-drawn / educational

| Visual style | Character | Best for | Paired rendering |
|---|---|---|---|
| [`sketch-notes`](./sketch-notes.md) | Warm paper, doodle line work, soft pastel blocks | Education, training, onboarding, knowledge | `sketch-notes` |
| [`ink-notes`](./ink-notes.md) | Pale field, black hand-ink, sparse semantic accent | Methodology, before/after, manifestos | `ink-notes` |
| [`chalkboard`](./chalkboard.md) | Dark slate, chalk strokes, powdery pastel accents | Teaching, tutorials, classroom, academic | `chalkboard` |

### 1.4 Specialty

| Visual style | Character | Best for | Paired rendering |
|---|---|---|---|
| [`pixel-art`](./pixel-art.md) | Strict pixel grid, blocky forms, limited palette, flat | Gaming, retro-tech, nostalgic, game-flavored | `pixel-art` |

---

## 2. Auto-selection — content vibe / industry → style

| Signal | Recommended style | Alternates |
|---|---|---|
| High-end consulting / architecture / luxury / minimal | `swiss-minimal` | `editorial` |
| Finance / journalism / research / long-form analysis | `editorial` | `swiss-minimal` |
| Product / SaaS / training / consumer / friendly | `soft-rounded` | `editorial` |
| Tech / AI / dev tools / data / futuristic | `dark-tech` | `soft-rounded` |
| Engineering / systems / architecture walkthrough | `blueprint` | `dark-tech` |
| Annual review / manifesto / max-density editorial | `brutalist` | `editorial` |
| Festival / consumer brand / youth / loud launch | `memphis` | `soft-rounded` |
| Indie publishing / design / culture / printed feel | `zine` | `editorial` |
| Heritage / hospitality / retro brand / 老字号 / 周年 | `vintage-poster` | `zine` |
| Cultural / folk / festival / children / sustainability | `paper-cut` | `sketch-notes` |
| Education / training / onboarding / 教学 | `sketch-notes` | `paper-cut` |
| Methodology / before-after / manifesto / 方法论 | `ink-notes` | `editorial` |
| Classroom / tutorial / academic / 课堂 | `chalkboard` | `sketch-notes` |
| Gaming / retro / 8-bit / 复古游戏 | `pixel-art` | `vintage-poster` |

> When the deck has AI images, align style with rendering: a `swiss-minimal` layout reads best with a `minimalist-swiss` rendering, so page and illustrations share one aesthetic. The "Paired rendering" column is the default pairing; override when content demands.
>
> Not every image-rendering has a layout twin: photographic / painterly renderings (`corporate-photo`, `nature`, `warm-scene`, `fantasy-animation`, `watercolor`) describe how an *image* looks, not how a deck is laid out — they pair with one of the layout styles above rather than being one.

---

## 3. Escape hatch — `custom`

When no preset captures the intended aesthetic, set `- visual_style: custom` in `spec_lock.md` and add a `- visual_style_behavior:` line: one paragraph naming shape language, decoration density, whitespace, typographic character, and texture — **no HEX, no color names as values**. `custom` is a tail-case, not a default; reach for a preset first.

---

## 4. How to use

1. Strategist reads this index at confirmation `d. Layer 2`.
2. Pick one style from the auto-selection table + the deck's vibe.
3. Lock it: write `- visual_style: <name>` into `spec_lock.md`, record rationale in `design_spec.md`.
4. Executor reads **only** `visual-styles/<locked-style>.md` at generation entry — never globs this directory.

**Lock scope**: deck-wide (one style per deck). It anchors taste as a **reference**, not a whitelist — pages may deviate with reason.
