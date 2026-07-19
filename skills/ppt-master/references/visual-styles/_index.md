# Visual Styles — Index

A **visual style** is how the deck **looks** — shape language, decoration density, whitespace rhythm, typographic character, texture / elevation. Lock **one per deck**; it anchors the aesthetic of the SVG layout itself (cards, dividers, spacing, corner radius, shadow use).

> **Styles carry NO HEX and lock no palette.** Color truth and role behavior live in `design_spec.colors` / `spec_lock.colors` (confirmation `e`). A visual style only describes how those existing colors are used in SVG composition—never which colors to substitute. Generated images follow the same single source of truth: their rendering comes from [`image-renderings/`](../image-renderings/), while their exact colors inherit the deck roles directly. [`image-palettes/`](../image-palettes/) is legacy compatibility material only.
>
> A visual style is *not* a mode. **Visual style = how it looks; mode = how you argue** (see [`modes/_index.md`](../modes/_index.md)). Locked independently — any style pairs with any mode.

---

## 1. Catalog

Each style has its own file with: shape & decoration, typography character, color-usage discipline (no HEX), texture / elevation, and the paired image-rendering. **Read only the file for the style you lock** — never glob the directory. The catalog mirrors [`image-renderings`](../image-renderings/_index.md): each style's "Paired rendering" names the illustration family that shares its aesthetic.

> The **`visual_style` value is only ever a first-column `id`** (`swiss-minimal`, `editorial`, …). The "Paired rendering" column lists **§h image-rendering** names (`flat`, `minimalist-swiss`, `digital-dashboard`, …) — never lock one of those as the `visual_style`; they belong to confirmation h.
>
> The **`Illus.`** column is each style's spot-illustration propensity — `core` (illustration is intrinsic to the look), `supportive` (use where it lifts, restrained), or `sparse` (the style's lead visual competes; default off). It sets the **default lean** only, for when the user gives no steer: an explicit user request to use / skip illustrations overrides it either way, and `image_usage: none` always writes no illustration rows. Full per-style rule in each file's §6.

### 1.1 Corporate / product

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`swiss-minimal`](./swiss-minimal.md) | Grid-locked, sharp, aggressive whitespace, no decoration | High-end consulting, architecture, type-led | `minimalist-swiss` | sparse |
| [`soft-rounded`](./soft-rounded.md) | Rounded cards, gentle elevation, approachable | Product, SaaS, training, consumer | `flat` | supportive |
| [`glassmorphism`](./glassmorphism.md) | Translucent glass panels, gradient light, floating depth | Modern SaaS, fintech, product launches, AI demos | `glassmorphism` | sparse |
| [`dark-tech`](./dark-tech.md) | Dark canvas, glow accents, geometric precision | Tech, AI, data products, launches | `digital-dashboard` | sparse |
| [`blueprint`](./blueprint.md) | Schematic line work on dark paper, isometric, annotated | Technical briefings, architecture, engineering | `blueprint` | supportive |

### 1.2 Editorial / publication

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`editorial`](./editorial.md) | Magazine hierarchy, rules & columns, serif/sans interplay | Finance, journalism, analysis, explainers | `editorial` | supportive |
| [`photo-editorial`](./photo-editorial.md) | Full-bleed photography dominates, text points & captions | Architecture, design, fashion, culture, photo-led | `corporate-photo` | sparse |
| [`data-journalism`](./data-journalism.md) | Multi-column micro-charts, sidebars, source lines, dense | Finance, market reviews, research, data reports | `editorial` | sparse |
| [`brutalist`](./brutalist.md) | Newsprint density, ruled boxes, raw structure, flat | Annual reviews, research digests, manifestos | `screen-print` / `editorial` | supportive |

### 1.3 Expressive / print

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`memphis`](./memphis.md) | Clashing color blocks, geometric confetti, bold outlines | Festivals, consumer, youth, launch hype | `flat` | core |
| [`zine`](./zine.md) | Riso misregistration, halftone, limited palette, print grit | Culture, design talks, indie brands | `screen-print` | core |
| [`vintage-poster`](./vintage-poster.md) | Mid-century flat blocks, halftone, retro-geometric warmth | Heritage, hospitality, cultural, anniversaries | `vintage-poster` | core |
| [`paper-cut`](./paper-cut.md) | Layered cut-paper sheets, soft inter-layer shadow, tactile | Cultural / folk, children, festival, sustainability | `paper-cut` | core |

### 1.4 Hand-drawn / brush

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`sketch-notes`](./sketch-notes.md) | Warm paper, doodle line work, soft pastel blocks | Education, training, onboarding, knowledge | `sketch-notes` | core |
| [`ink-notes`](./ink-notes.md) | Pale field, black hand-ink, sparse semantic accent | Methodology, before/after, manifestos | `ink-notes` | supportive |
| [`chalkboard`](./chalkboard.md) | Dark slate, chalk strokes, powdery pastel accents | Teaching, tutorials, classroom, academic | `chalkboard` | core |
| [`ink-wash`](./ink-wash.md) | Rice-paper whitespace, brush marks, seal accent, still | Cultural, philosophy, heritage, 新中式 | `ink-notes` / `watercolor` | supportive |

### 1.5 Specialty

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`pixel-art`](./pixel-art.md) | Strict pixel grid, blocky forms, limited palette, flat | Gaming, retro-tech, nostalgic, game-flavored | `pixel-art` | core |

---

## 2. Auto-selection — content vibe / industry → style

| Signal | Recommended style | Alternates |
|---|---|---|
| High-end consulting / architecture / luxury / minimal | `swiss-minimal` | `editorial` |
| Finance / journalism / research / long-form analysis | `editorial` | `data-journalism` |
| Photography-led / architecture / design / fashion / 大图 | `photo-editorial` | `editorial` |
| Data report / market review / 财经 / Bloomberg / Economist | `data-journalism` | `editorial` |
| Product / SaaS / training / consumer / friendly | `soft-rounded` | `editorial` |
| Modern SaaS / fintech / health-tech / premium app | `glassmorphism` | `dark-tech` |
| Tech / AI / dev tools / data / futuristic | `dark-tech` | `glassmorphism` |
| Cultural / philosophy / heritage / 新中式 / 东方 | `ink-wash` | `editorial` |
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
> Not every image-rendering becomes its own visual style. A rendering earns a layout twin only when it defines a whole-page layout language (shape, whitespace, composition, texture) — not merely how an inserted image looks. Purely atmospheric renderings (`nature`, `warm-scene`, `fantasy-animation`) stay imagery-only: they pair with whichever layout style fits rather than being one. (Note the distinction `photo-editorial` draws: photography as a *rendering* is image-look, but photo-*led composition* is a real layout language — so the style exists, paired with `corporate-photo`.)

---

## 3. Escape hatch — `custom`

Stage 2 always authors one visible, non-empty AI custom proposal beside the preset spectrum. Its paragraph names shape language, composition geometry (page-scale moves), decoration density, whitespace, typographic character, and texture — **no HEX, no color names as values**. The proposal is initially unselected and remains recommendation-only unless the user chooses it; a template-backed proposal must stay inside the inherited identity and confirmed application plan. When selected, record the edited aesthetic in the Design Spec first, then project `- visual_style: custom` plus `- visual_style_behavior:` to `spec_lock.md`. The candidate is mandatory; selecting `custom` remains a tail-case, not the default.

---

## 4. How to use

1. Strategist reads this index at confirmation `d. Layer 2`.
2. Preselect one style from the auto-selection table + the deck's vibe; separately author the visible AI custom proposal from §3.
3. Record the confirmed style and rationale in `design_spec.md`, then project `- visual_style: <name>` into `spec_lock.md`.
4. Executor reads **only** `visual-styles/<locked-style>.md` at generation entry — never globs this directory.

**Lock scope**: deck-wide (one style per deck). It anchors taste as a **reference**, not a whitelist — pages may deviate with reason.
