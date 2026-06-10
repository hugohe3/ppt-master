# Native Diagram Demo - Design Spec

> A deliberately small spec focused on showing the **per-page Vehicle Decision**
> (the `Treatment` field) and the native-diagram path. See
> `templates/design_spec_reference.md` for the full §I–XI structure.

## III. Visual Theme
- **Style**: modern, dimensional (welcomes 3D figures → native diagrams are in play)
- **Color Scheme**: primary `#1B1F3B` (deep indigo) · accent `#18C8D6` (cyan) · bg `#FFFFFF` · text `#1A1A1A`

## IV. Typography
- font_family: "Microsoft YaHei", Arial, sans-serif

## IX. Content Outline (per-page Treatment = the vehicle decision)

### Slide 01 — Cover
- **Core message**: an AI smart-glasses product, framed by its 看见 / 听懂 / 执行 arc.
- **Treatment**: `image:cover_bg.png (hero_page)` + SVG overlay (title / subtitle).
  - The image is the page's body; SVG carries the editable title.

### Slide 02 — Capability tier model
- **Core message**: the glasses' capability builds across three tiers (perception hardware → real-time interaction → intelligent ecosystem).
- **Treatment**: `native:solid3d_bluegreen_012` (a 3-tier pyramid) + SVG overlay (page title).
  - Primary body is a **native diagram**, recolored to the deck palette
    (`data-recolor="558C5A=18C8D6,122B87=1B1F3B"`) and filled with this deck's
    content via text slots (`data-text`). No hand-drawn figure, no chart template.

## VII. Visualization Reference List (derived from §IX Treatment)
| Page | Template | Path | Summary-quote (from `diagrams_index.json`) |
|------|----------|------|--------------------------------------------|
| P02 | solid3d_bluegreen_012 | `templates/native_diagrams/solid3d_bluegreen_012` | "Pick for a 3-level hierarchy / precedence / maturity. Skip if >4 levels or nested layers (013)." |

## VIII. Image Resource List (derived from §IX Treatment)
| Filename | Purpose | Acquire Via | page_role |
|----------|---------|-------------|-----------|
| cover_bg.png | Cover backdrop (AI glasses, dark indigo/cyan, calm left for title) | ai (Codex) | hero_page |
