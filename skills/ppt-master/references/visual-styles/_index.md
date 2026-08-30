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
> The **`Illus.`** column describes illustration's role only after the resource-need review selects illustration — `core` (illustration may lead the look), `supportive` (illustration may share the composition), or `sparse` (illustration stays selective so the style's lead visual remains clear). It tunes selected illustration's centrality and recurrence; it never recommends adding illustration, selects an AI source or image row, or narrows eligible page types, element scale, or carrier combinations. An explicit user request to use / skip illustrations overrides it either way, and `image_usage: none` always writes no illustration rows. Full per-style rule in each file's §6.
>
> **Typography character applies to editable native text.** Decorative
> lettering is a separate carrier decision; a selected style informs its
> treatment, never its eligibility.

### 1.1 Corporate / product

| Visual style | Character | Paired rendering | Illus. |
|---|---|---|---|
| [`swiss-minimal`](./swiss-minimal.md) | Grid-locked, sharp, aggressive whitespace, near-zero ornament | `minimalist-swiss` | sparse |
| [`soft-rounded`](./soft-rounded.md) | Rounded cards, gentle elevation, approachable | `flat` | supportive |
| [`glassmorphism`](./glassmorphism.md) | Translucent glass panels, gradient light, floating depth | `glassmorphism` | sparse |
| [`dark-tech`](./dark-tech.md) | Dark canvas, glow accents, geometric precision | `digital-dashboard` | sparse |
| [`blueprint`](./blueprint.md) | Schematic line work on dark paper, isometric, annotated | `blueprint` | supportive |

### 1.2 Editorial / publication

| Visual style | Character | Paired rendering | Illus. |
|---|---|---|---|
| [`editorial`](./editorial.md) | Magazine hierarchy, rules & columns, serif/sans interplay | `editorial` | supportive |
| [`photo-editorial`](./photo-editorial.md) | Full-bleed photography dominates, text points & captions | `corporate-photo` | sparse |
| [`data-journalism`](./data-journalism.md) | Multi-column micro-charts, sidebars, source lines, dense | `editorial` | sparse |
| [`brutalist`](./brutalist.md) | Newsprint density, ruled boxes, raw structure, flat | `screen-print` / `editorial` | supportive |

### 1.3 Expressive / print

| Visual style | Character | Paired rendering | Illus. |
|---|---|---|---|
| [`memphis`](./memphis.md) | Clashing color blocks, geometric confetti, bold outlines | `flat` | core |
| [`zine`](./zine.md) | Riso misregistration, halftone, limited palette, print grit | `screen-print` | core |
| [`vintage-poster`](./vintage-poster.md) | Mid-century flat blocks, halftone, retro-geometric warmth | `vintage-poster` | core |
| [`paper-cut`](./paper-cut.md) | Layered cut-paper sheets, soft inter-layer shadow, tactile | `paper-cut` | core |

### 1.4 Hand-drawn / brush

| Visual style | Character | Paired rendering | Illus. |
|---|---|---|---|
| [`sketch-notes`](./sketch-notes.md) | Warm paper, doodle line work, soft pastel blocks | `sketch-notes` | core |
| [`ink-notes`](./ink-notes.md) | Pale field, black hand-ink, sparse semantic accent | `ink-notes` | supportive |
| [`chalkboard`](./chalkboard.md) | Dark slate, chalk strokes, powdery pastel accents | `chalkboard` | core |
| [`ink-wash`](./ink-wash.md) | Rice-paper whitespace, brush marks, seal accent, still | `ink-notes` / `watercolor` | supportive |

### 1.5 Specialty

| Visual style | Character | Paired rendering | Illus. |
|---|---|---|---|
| [`pixel-art`](./pixel-art.md) | Strict pixel grid, blocky forms, limited palette, flat | `pixel-art` | core |

---

## 2. Selection Boundary

**Reference — not a constraint**: Resolve the audience task, outcome, delivery
context, required carriers, and artifact afterlife before choosing. Compare the
complete catalog's character, composition language, density, typography, and
texture with the project as a whole. A topic, industry, or style keyword never
selects a row; the same subject may support different visual systems when its
communication job changes.

| Decision dimension | Evidence to compare |
|---|---|
| Shape and space | Contour language, grid behavior, whitespace, and boundary strength |
| Information texture | Sparse presence, editorial hierarchy, dense evidence, or hand-made expression |
| Carrier integration | How the system accommodates the page's actual photos, illustrations, charts, tables, and native geometry |
| Typography character | The role editable type plays inside the composition, independent of exact font choice |
| Delivery and afterlife | Viewing distance, projection/print behavior, reuse, and expected editing |

**Default — derive shape language from project fit (may override when a generic
primitive system is itself the clearest identity or communication choice)**:
Before settling on lines, rectangles, circles, or ellipses as the deck's main
shape language, test whether the source material, identity, or communication
job offers a more specific edge, corner, opening, angle, contour, or layering
logic. Retain a primitive-led result when it deliberately fits; do not select
an exact authoring preset here.

> When the deck has AI images, the "Paired rendering" column exposes an
> aesthetically related option. It does not select the rendering or create an
> AI image job; compare it with the actual image roles before using it.
>
> Not every image-rendering becomes its own visual style. A rendering earns a layout twin only when it defines a whole-page layout language (shape, whitespace, composition, texture) — not merely how an inserted image looks. Purely atmospheric renderings (`nature`, `warm-scene`, `fantasy-animation`) stay imagery-only: they pair with whichever layout style fits rather than being one. (Note the distinction `photo-editorial` draws: photography as a *rendering* is image-look, but photo-*led composition* is a real layout language — so the style exists, paired with `corporate-photo`.)

---

## 3. Editable `custom` projection

Each Default Stage-2 direction authors one visible, non-empty `custom` aesthetic under [`strategist.md`](../strategist.md) §d — its executable shape language, composition geometry, decoration density, whitespace, typography character, and texture — naming only the catalog bases it actually uses; freeze those ids from this index, then read only their files before writing the behavior. Quick resolves one preset or custom behavior the same way and persists nothing.

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
