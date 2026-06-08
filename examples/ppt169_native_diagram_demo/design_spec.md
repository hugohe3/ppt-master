# Native Diagram Demo - Design Spec

> A deliberately small spec focused on showing the **per-page Vehicle Decision**
> (the `Treatment` field) and the native-diagram path. See
> `templates/design_spec_reference.md` for the full §I–XI structure.

## III. Visual Theme
- **Style**: modern, dimensional (welcomes 3D figures → native diagrams are in play)
- **Color Scheme**: primary `#1E3A5F` (navy) · accent `#D4AF37` (gold) · bg `#FFFFFF` · text `#1A1A1A`

## IV. Typography
- font_family: "Microsoft YaHei", Arial, sans-serif

## IX. Content Outline (per-page Treatment = the vehicle decision)

### Slide 01 — Cover
- **Core message**: the deck's subject and the 3-level arc.
- **Treatment**: `image:cover_bg.png (hero_page)` + SVG overlay (title / subtitle).
  - The image is the page's body; SVG carries the editable title.

### Slide 02 — Capability maturity model
- **Core message**: digital capability matures across three levels (foundation → platform → intelligence).
- **Treatment**: `native:solid3d_bluegreen_012` (a 3-tier pyramid) + SVG overlay (page title).
  - Primary body is a **native diagram**, recolored to the deck palette
    (`data-recolor="558C5A=1E3A5F,122B87=D4AF37"`) and filled with this deck's
    content via text slots (`data-text`). No hand-drawn figure, no chart template.

## VII. Visualization Reference List (derived from §IX Treatment)
| Page | Template | Path | Summary-quote (from `diagrams_index.json`) |
|------|----------|------|--------------------------------------------|
| P02 | solid3d_bluegreen_012 | `templates/native_diagrams/solid3d_bluegreen_012` | "Pick for a 3-level hierarchy / precedence / maturity. Skip if >4 levels or nested layers (013)." |

## VIII. Image Resource List (derived from §IX Treatment)
| Filename | Purpose | Acquire Via | page_role |
|----------|---------|-------------|-----------|
| cover_bg.png | Cover backdrop (navy/gold tech, calm center for title) | ai (Codex) | hero_page |
