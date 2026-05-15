# Rendering: minimalist-swiss

Swiss-grid / Bauhaus-adjacent visual discipline. Grid-locked geometry, generous negative space, sans-serif typographic character, no decoration. The most restrained rendering — used for high-end consulting, architecture, design firms, luxury brands, type foundries.

---

## 1. Style paragraph (paste-ready, 100 words)

> Strict Swiss-grid minimalism. Composition is built on a visible or implied modular grid — every element snaps to grid lines, deliberate column-and-row alignment carries the whole page. Forms are reduced to essential geometric primitives — clean rectangles, perfect circles, single-weight lines. Typographic character is sans-serif, often Helvetica-adjacent, set with rigorous spacing. Color is applied sparingly — usually one primary block, large fields of white or near-white, single accent. No gradients, no shadows, no texture, no decoration. Negative space carries as much weight as filled areas. Overall feel is rigorous, considered, almost academic — the aesthetic of Müller-Brockmann posters and Vignelli design systems.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Single uniform stroke weight; mathematically straight or perfectly circular |
| Texture | None — flat fills only |
| Depth | None — strictly 2D; no shadows, no perspective |
| Material | None — color is conceptual zone |
| Mood | Rigorous, considered, austere, academic |

---

## 3. Container sizing for local PPT inserts

| Embedded position | Recommended canvas | Aspect | Inner padding |
|---|---|---|---|
| Full-bleed grid page | 1280×720 | 16:9 | 18-20% all sides (Swiss design needs aggressive whitespace) |
| Half-page composition | 600×600 | 1:1 | 18% |
| Hero band | 1200×400 | 3:1 | 20% sides |
| Spot composition | 400×400 | 1:1 | 15% |

---

## 4. Using the deck's HEX values

minimalist-swiss treats colors as **conceptual zones**, not decoration. Apply HEX exactly — one color dominates a deliberate grid cell, secondary fills the field, accent appears at one rule-of-thirds intersection only.

- Primary HEX: one large grid block (typically a square or rectangle covering 20-30% of canvas)
- Secondary HEX: the field (most of the canvas — usually near-white)
- Accent HEX: a single thin line or a single small dot — never more than 2-3% of canvas
- Outlines: rarely used; when needed, the deck's primary in 1px

---

## 5. Fewshot prompt snippets

**Snippet A — half-page composition, text_policy: none**

> Strict Swiss-grid minimalist composition. The canvas is built on an invisible 6-column grid. One large primary deep navy `#1E3A5F` square occupies the lower-left grid cells (about 25% of canvas area), positioned with rigorous alignment to the grid. The rest of the canvas is secondary near-white `#F8F9FA` — calm, vast, deliberate negative space. One thin horizontal accent gold `#D4AF37` line sits at the upper rule-of-thirds, spanning four grid columns (about 2% of canvas area). No other elements. No gradients, no shadows, no texture, no decoration. Composed as a 600×600 half-page block with 18% inner padding. Color values are rendering guidance only — do not display HEX codes or color names as text in the image. NO text of any kind anywhere in the image.

**Snippet B — hero band, text_policy: none**

> Swiss-grid minimalist hero band. Composition divided on a strict modular grid into rectangular zones. Left third: solid primary deep teal `#0F766E` rectangle. Center third: secondary near-white `#F8F9FA` calm field. Right third: secondary near-white `#F8F9FA` field with one small accent burnt-orange `#C2410C` circle positioned at the grid's rule-of-thirds intersection (about 2% of canvas). All edges are mathematically straight, all alignment is grid-precise. No decoration, no gradients, no shadows. Composed as a 1200×400 hero band with 20% side padding. NO text or labels. Color values are rendering guidance only.

---

## 6. Forbidden

- Decorative elements, illustrative iconography, ornamental flourishes (defeats Swiss discipline)
- Gradients, shadows, glows, textures (minimalist-swiss is strictly flat)
- Multiple accents in the same composition (one accent only)
- Off-grid placement, free-form positioning (every element snaps to grid)
- More than 3 colors total

---

## 7. When to switch away

- For warmer / softer aesthetic → `flat` or `editorial`
- For tech depth → `3d-isometric` or `blueprint`
- For data products → `digital-dashboard`
- For human warmth → `corporate-photo` or `warm-scene`
