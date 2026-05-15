# Type: framework

A central concept surrounded by related sub-concepts, or a multi-component system shown as a relational structure. Used when the image's job is to make a methodology, model, or architecture **legible at a glance**.

> **What framework means inside a PPT block**: the image *itself* is a small relational diagram — central hub + radiating satellites, or a labeled matrix, or a layered stack. The PPT page's slide layout (where this image sits, what text accompanies it) is a separate decision. This file only governs what's *inside* the image rectangle.

## 1. Composition skeleton

Three valid sub-structures. Pick one per image; do not mix.

### Sub-structure 1 — Hub & spokes (most common)

```
        ◯
         \
   ◯ ─── ◆ ─── ◯
         /
        ◯
```

| LAYOUT | One central element (geometric anchor: circle, rounded square, diamond, hexagon) with 3-6 satellites positioned around it |
| ELEMENTS | Satellite nodes are visually consistent — same shape family, same size, same color treatment. Connecting lines are thin, clean, all the same weight |
| NEGATIVE SPACE | Generous radial breathing room — satellites should not feel cramped against the center or the canvas edge |
| BALANCE | Symmetric (satellites evenly distributed) OR deliberate asymmetric weighting (one satellite emphasized) — never accidental imbalance |

### Sub-structure 2 — Matrix (2×2 or 3×3)

```
   ┌──────┬──────┐
   │      │      │
   ├──────┼──────┤
   │      │      │
   └──────┴──────┘
```

| LAYOUT | Equal-sized cells in a grid; each cell carries one concept |
| ELEMENTS | One icon or symbolic shape per cell; cells are visually equal (no cell dominates unless that's the point — e.g. SWOT, BCG matrices) |
| NEGATIVE SPACE | Generous cell padding — internal content occupies the inner 70% of each cell |

### Sub-structure 3 — Layered stack

```
   ╔══════════════╗
   ║   layer 3    ║
   ╠══════════════╣
   ║   layer 2    ║
   ╠══════════════╣
   ║   layer 1    ║
   ╚══════════════╝
```

| LAYOUT | 3-5 horizontal bands stacked vertically; visual weight increases or decreases monotonically |
| ELEMENTS | Each layer has a consistent visual treatment; one icon or shape per layer |
| NEGATIVE SPACE | Equal-height bands with consistent gap between them; top and bottom padding to canvas edge |

---

## 2. Container sizing for local PPT inserts

| Embedded position | Canvas | Aspect | Sub-structure fit |
|---|---|---|---|
| Square half-page (most common) | 700×700 | 1:1 | Hub & spokes ✓✓ / Matrix ✓✓ |
| Portrait half-page | 600×800 | 3:4 | Layered stack ✓✓ |
| Landscape banner | 1200×500 | 2.4:1 | Hub & spokes (flattened) ✓ / Matrix (1×N) ✓ |
| Full-bleed (page_role: full_page only) | 1280×720 | 16:9 | All three work — but require explicit user request |

Inner padding: 15-18% on all sides. Framework imagery suffers most when satellites/cells push against the canvas edge.

---

## 3. Text-policy variants

### `text_policy: none` (default — recommended for most decks)

The image shows **only the geometric structure**. Labels for each satellite / cell / layer are added in SVG overlay around the image.

This is the recommended path because:
- SVG labels are editable, translatable, accurate
- The model can fail on text rendering; geometry it can do
- The page looks more polished with crisp vector text overlaying the AI art

Sample fragment to add to the prompt:

> Pure geometric structure — no labels, no captions, no text, no letters or numbers anywhere in the image. Each satellite/cell/layer contains a simple iconic symbol only (gear, arrow, chart, etc.). SVG text overlay will be added externally.

### `text_policy: embedded` (rare — for sketch-notes / ink-notes hand-lettered decks)

A short keyword (1-2 English words) appears inside or beside each satellite / cell / layer.

Sample fragment:

> Each satellite includes a single short hand-lettered keyword in English (≤2 words) — e.g. "data", "process", "growth". Keywords are part of the artwork, not labels. No long sentences, no numbers, no Chinese characters (most models render CJK characters incorrectly).

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, hub-and-spokes, `text_policy: none`, 700×700 half-page**

> Clean flat vector illustration with bold geometric shapes and confident solid fills. Crisp 2px outlines, no gradients, single 8% soft drop shadow under elevated elements. The composition is a hub-and-spokes framework: one central rounded-square node in primary deep navy `#1E3A5F` sits at the exact center; four satellite circles in the same navy are evenly distributed around it (top, right, bottom, left), connected to the center by thin straight lines in a darker neutral. Each satellite contains one simple iconic symbol in white fill — a gear, a chart bar, an upward arrow, a chat bubble — chosen for clear recognition at small sizes. Background is calm secondary light gray `#F8F9FA` carrying 65% of the canvas area. Accent gold `#D4AF37` appears only as one thin emphasis ring around the central node — under 5% of canvas area. Composed as a 700×700 half-page block with 16% inner padding on all sides — satellites breathe well within the canvas, no element touches the edge. No text, letters, numbers, or labels anywhere in the image — SVG labels will be added externally. Color values are rendering guidance only — do not display HEX codes or color names as text. Simplified iconic symbols only, no realistic faces.

**Snippet B — sketch-notes + macaron, matrix (2×2), `text_policy: embedded`, 700×700**

> Warm cream paper background `#F5F0E8` with subtle paper texture. Black hand-drawn lines with slight wobble, à la sketch-notes / hand-lettered educational style. Composition is a 2×2 matrix — four rounded rectangles arranged in a grid, each cell filled with a different pastel block color (light blue, mint, lavender, peach). Each cell contains one simple hand-drawn cartoon icon (a lightbulb, a chart, a person, a target) and one short hand-lettered English keyword (e.g. "ideas", "data", "team", "goal") — 1-2 words per cell maximum. Cells are separated by hand-drawn dividers with slight wobble. Generous white space around the matrix — internal cell content occupies the inner 70% of each cell. Color values are rendering guidance only — do not display HEX codes or color names as text. Hand-lettered keywords only in English; no long sentences, no numbers, no Chinese characters. Composed as a 700×700 half-page block with 18% inner padding on all sides.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Satellites uneven, asymmetric in unintended way | "Evenly distributed" omitted | Add explicit "evenly distributed around the center, equal spacing between satellites" |
| Center node lost among satellites | Center is same size/weight as satellites | Specify "center is visually dominant — larger and more saturated than satellites" |
| Lines connecting nodes look messy | Stroke weight not specified | Add "all connecting lines are thin, uniform stroke weight, perfectly straight" |
| Labels appearing despite `text_policy: none` | Prompt allowed iconic symbols loosely | Add "no labels, no captions, no text, no letters, no numbers — pure geometric structure only" |
| Garbled CJK characters in `embedded` | Chinese keywords requested | Switch keywords to English or accept manual regen |
| Image too dense, no room for SVG overlay | Padding rule omitted | Restate "15-18% inner padding on all sides, central content occupies inner 70%" |

---

## 6. When to switch away from framework

- If the structure is **sequential / stepwise**, use `flowchart`
- If the structure is **two competing options**, use `comparison`
- If the structure is **chronological**, use `timeline`
- If the structure is **dominant single subject with smaller elements**, use `hero`
- If the structure is **pure backdrop with no internal structure**, use `background`
