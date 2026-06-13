# Visual Styles — Index

A **visual style** is how the deck **looks** — shape language, decoration density, whitespace rhythm, typographic character, texture / elevation. Lock **one per deck**; it anchors the aesthetic of the SVG layout itself (cards, dividers, spacing, corner radius, shadow use).

> **Styles carry NO HEX and lock no palette.** Color truth lives in `design_spec.colors` / `spec_lock.colors` (confirmation `e`); color *behavior* lives in [`image-palettes/`](../image-palettes/). A visual style only describes how the deck's existing colors are *used* — never which colors. (Same discipline as [`image-renderings/`](../image-renderings/) for AI images.)
>
> A visual style is *not* a mode. **Visual style = how it looks; mode = how you argue** (see [`modes/_index.md`](../modes/_index.md)). Locked independently — any style pairs with any mode.

---

## 1. Catalog

Each style has its own file with: shape & decoration, typography character, color-usage discipline (no HEX), texture / elevation, and the paired image-rendering. **Read only the file for the style you lock** — never glob the directory.

| Visual style | Character | Best for | Paired rendering |
|---|---|---|---|
| [`swiss-minimal`](./swiss-minimal.md) | Grid-locked, sharp, aggressive whitespace, no decoration | High-end consulting, architecture, type-led | `minimalist-swiss` |
| [`editorial`](./editorial.md) | Magazine hierarchy, rules & columns, serif/sans interplay | Finance, journalism, analysis, explainers | `editorial` |
| [`soft-rounded`](./soft-rounded.md) | Rounded cards, gentle elevation, approachable | Product, SaaS, training, consumer | `flat` / `glassmorphism` |
| [`dark-tech`](./dark-tech.md) | Dark canvas, glow accents, geometric precision | Tech, AI, data products, launches | `digital-dashboard` / `blueprint` |

---

## 2. Auto-selection — content vibe / industry → style

| Signal | Recommended style | Alternates |
|---|---|---|
| High-end consulting / architecture / luxury / minimal | `swiss-minimal` | `editorial` |
| Finance / journalism / research / long-form analysis | `editorial` | `swiss-minimal` |
| Product / SaaS / training / consumer / friendly | `soft-rounded` | `editorial` |
| Tech / AI / dev tools / data / futuristic | `dark-tech` | `soft-rounded` |

> When the deck has AI images, align style with rendering: a `swiss-minimal` layout reads best with a `minimalist-swiss` rendering, so page and illustrations share one aesthetic. The "Paired rendering" column is the default pairing; override when content demands.

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
