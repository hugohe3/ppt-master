# Visual Styles — Index

A **visual style** is how the deck **looks** — shape language, decoration density, whitespace rhythm, typographic character, texture / elevation. Resolve **one per deck**; Default locks it, while Quick keeps it only in active context. It anchors the aesthetic of the SVG layout itself (cards, dividers, spacing, corner radius, shadow use).

**Hard rule — capability boundary**: A style governs treatment, visual weight,
density, recurrence, and coherence. It never decides carrier eligibility or
image source, and never narrows the complete primitive, Office-preset,
independent-composition, Boolean, or necessary-freeform authoring vocabulary.
Page purpose selects the carriers and construction; the style makes the chosen
forms belong to one visual system.

> **Styles carry NO fixed HEX and define no palette.** Default core color identity and recurring role behavior live in `design_spec.colors` / `spec_lock.colors` (confirmation `e`); Quick resolves equivalent palette anchors in active context. A visual style describes how those anchors behave in SVG composition and may call for contextual tints, gradients, effects, or material transitions; it does not substitute an unrelated palette. Generated images follow the same anchor model through [`image-renderings/`](../image-renderings/). [`image-palettes/`](../image-palettes/) is legacy compatibility material only.
>
> A visual style is *not* a mode. **Visual style = how it looks; mode = how you argue** (see [`modes/_index.md`](../modes/_index.md)). Resolve them independently — any style pairs with any mode.

---

## 1. Catalog

Each style keeps its own authoritative file with: shape & decoration, typography character, color-usage discipline (no HEX), texture / elevation, and the paired image-rendering. Read this index alone while choosing a direction. Only after a preset or custom bases are fixed may the active role read the selected sibling files: one file for a preset, every exact `visual_style_references` file for a catalog-based custom, and none for a novel custom. Never glob the directory or read an unselected sibling. The catalog mirrors [`image-renderings`](../image-renderings/_index.md): each style's "Paired rendering" names the illustration family that shares its aesthetic.

> The **`visual_style` value is only ever a first-column `id`** (`swiss-minimal`, `editorial`, …). The "Paired rendering" column lists **image-rendering** names (`flat`, `minimalist-swiss`, `digital-dashboard`, …) — never treat one of those as the `visual_style`. Default records rendering under confirmation h; Quick keeps the selected rendering only in active context and any required image manifest.
>
> The **`Illus.`** column describes illustration's role only after page-carrier selection activates it — `core` (illustration may lead the look), `supportive` (illustration may share the composition), or `sparse` (illustration stays selective so the style's lead visual remains clear). It tunes selected illustration's centrality and recurrence; it never recommends adding illustration, selects an AI source or image row, or narrows eligible page types, element scale, or carrier combinations. An explicit user request to use / skip illustrations overrides it either way, and `image_usage: none` always writes no illustration rows. Full per-style rule in each file's §6.
>
> **Typography character applies to editable native text.** Decorative
> lettering is a separate carrier decision; a selected style informs its
> treatment, never its eligibility.

### 1.1 Corporate / product

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`swiss-minimal`](./swiss-minimal.md) | Grid-locked, sharp, aggressive whitespace, near-zero ornament | High-end consulting, architecture, type-led | `minimalist-swiss` | sparse |
| [`soft-rounded`](./soft-rounded.md) | Rounded cards, gentle elevation, approachable | Product, SaaS, training, consumer | `flat` | supportive |
| [`glassmorphism`](./glassmorphism.md) | Translucent glass panels, gradient light, floating depth | Modern SaaS, fintech, product launches, AI demos | `glassmorphism` | sparse |
| [`dark-tech`](./dark-tech.md) | Dark canvas, glow accents, geometric precision | Tech, AI, data products, launches | `digital-dashboard` | sparse |
| [`blueprint`](./blueprint.md) | Schematic line work on dark paper, isometric, annotated | Technical briefings, architecture, engineering | `blueprint` | supportive |

### 1.2 Editorial / publication

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`editorial`](./editorial.md) | Magazine hierarchy, rules & columns, serif/sans interplay | Finance, journalism, analysis, explainers | `editorial` | supportive |
| [`photo-editorial`](./photo-editorial.md) | Full-bleed photography dominates, text points & captions | Architecture, design, fashion, culture, travel / destination, photo-led | `corporate-photo` | sparse |
| [`data-journalism`](./data-journalism.md) | Multi-column micro-charts, sidebars, source lines, dense | Finance, market reviews, research, data reports | `editorial` | sparse |
| [`brutalist`](./brutalist.md) | Newsprint density, ruled boxes, raw structure, flat | Annual reviews, research digests, manifestos | `screen-print` / `editorial` | supportive |

### 1.3 Expressive / print

| Visual style | Character | Best for | Paired rendering | Illus. |
|---|---|---|---|---|
| [`memphis`](./memphis.md) | Clashing color blocks, geometric confetti, bold outlines | Festivals, consumer, youth, launch hype | `flat` | core |
| [`zine`](./zine.md) | Riso misregistration, halftone, limited palette, print grit | Culture, design talks, indie brands | `screen-print` | core |
| [`vintage-poster`](./vintage-poster.md) | Mid-century flat blocks, halftone, retro-geometric warmth | Heritage brands, historic hospitality identities, cultural retrospectives, anniversaries | `vintage-poster` | core |
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

## 2. Selection recall — communication task + content signal → style

**Reference — not a constraint**: Resolve the audience task, outcome, delivery context, required carriers, and artifact afterlife before using this table. A topic or industry word alone never selects a style. Reject a candidate that weakens the audience's practical task or cannot integrate required real-world imagery. A travel itinerary or destination decision aid is not retro merely because its subject is cultural or hospitality-related; choose retro only when nostalgia / heritage storytelling or an explicit user direction makes it part of the communication job.

| Signal | Recommended style | Alternates |
|---|---|---|
| High-end consulting / architecture / luxury / minimal | `swiss-minimal` | `editorial` |
| Finance / journalism / research / long-form analysis | `editorial` | `data-journalism` |
| Photography-led / architecture / design / fashion / 大图 | `photo-editorial` | `editorial` |
| Itinerary / destination guide / trip planning / 旅游计划 / 行程 | `photo-editorial` | `editorial`, `soft-rounded` |
| Data report / market review / 财经 / Bloomberg / Economist | `data-journalism` | `editorial` |
| Product / SaaS / training / consumer / friendly | `soft-rounded` | `editorial` |
| Modern SaaS / fintech / health-tech / premium app | `glassmorphism` | `dark-tech` |
| Tech / AI / dev tools / data / futuristic | `dark-tech` | `glassmorphism` |
| Cultural / philosophy / heritage / 新中式 / 东方 | `ink-wash` | `editorial` |
| Engineering / systems / architecture walkthrough | `blueprint` | `dark-tech` |
| Annual review / manifesto / max-density editorial | `brutalist` | `editorial` |
| Festival / consumer brand / youth / loud launch | `memphis` | `soft-rounded` |
| Indie publishing / design / culture / printed feel | `zine` | `editorial` |
| Heritage brand / historic hospitality identity / retro brand / 老字号 / 周年 | `vintage-poster` | `zine` |
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

Each coordinated Default Stage-2 direction authors one visible, non-empty `custom` aesthetic whose paragraph names project-specific shape language, composition geometry, decoration density, whitespace, typographic character, and texture — **no HEX, no color names as values**. Use this index to freeze any catalog bases before reading their detail files. A template-backed synthesis stays inside the inherited identity and confirmed application plan. Record the confirmed current aesthetic in the Design Spec first, then project `- visual_style: custom` plus `- visual_style_behavior:`. The 18 fixed styles remain lower-level single-select alternatives; do not create a fourth AI-custom proposal.

Quick does not display a candidate spectrum. It reads this index, resolves one preset or custom behavior, then reads only the selected detail files and persists nothing.

**Mandatory — select before detail reading**: Freeze every catalog source actually used from this index, then read only those exact files before writing the behavior. A custom may use zero, one, or many sources: keep one when it owns the whole specialized aesthetic, or include every style that contributes a distinct executable job across shape language, composition, decoration, whitespace, typography, or texture. Reference count has no fixed cap; count is an outcome, not a target. A coherent three-basis direction may assign `swiss-minimal` to grid and whitespace, `soft-rounded` to selective surface contours and elevation, and `editorial` to evidence hierarchy and rules. Default persists every actual id as `visual_style_references`; Quick retains them only in active context. Omit every source whose contribution cannot be stated, never add a second merely to imply synthesis, and do not open candidates for comparison after this gate. A genuinely new aesthetic names and reads no catalog source.

---

## 4. How to use

| Active profile | Use |
|---|---|
| Default Generate | Strategist reads only this index while mapping three whole solution intents, freezes each custom direction's exact bases, then reads only their deduplicated detail files. Executor reads the confirmed preset file or exact custom references. |
| Quick Generate | The current main agent reads only this index while deciding, then reads the resolved preset or exact custom bases and retains that one direction without Design Spec/lock. |

**Resolution scope**: deck-wide (one style per deck). It anchors taste as a
**reference**, not a whitelist. Each §1 `Composition geometry` list is
generative vocabulary, not a finite layout menu; pages may synthesize or
deviate when their communication job calls for it.
