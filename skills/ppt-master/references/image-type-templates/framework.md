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

## 2. Text-policy variants

### `text_policy: none`

The image shows the geometric structure with iconic symbols only; labels are handled in SVG.

Sample fragment to add to the prompt:

> Pure geometric structure — no labels, no captions, no text, no letters or numbers anywhere in the image. Each satellite/cell/layer contains a simple iconic symbol only (gear, arrow, chart, etc.).

### `text_policy: embedded`

A short keyword (1-2 English words) appears inside or beside each satellite / cell / layer.

Sample fragment:

> Each satellite includes a single short hand-lettered keyword in English (≤2 words) — e.g. "data", "process", "growth". Keywords are part of the artwork, not labels. No long sentences, no numbers, no Chinese characters (most models render CJK characters incorrectly).

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, hub-and-spokes, `text_policy: none`, 700×700 half-page**

> Clean flat vector illustration with bold geometric shapes and confident solid fills. Crisp 2px outlines, no gradients, single 8% soft drop shadow under elevated elements. The composition is a hub-and-spokes framework: one central rounded-square node in primary deep navy `#1E3A5F` sits at the exact center; four satellite circles in the same navy are evenly distributed around it (top, right, bottom, left), connected to the center by thin straight lines in a darker neutral. Each satellite contains one simple iconic symbol in white fill — a gear, a chart bar, an upward arrow, a chat bubble — chosen for clear recognition at small sizes. Background is calm secondary light gray `#F8F9FA` carrying 65% of the canvas area. Accent gold `#D4AF37` appears only as one thin emphasis ring around the central node — under 5% of canvas area. Composed as a 700×700 half-page block with 16% inner padding on all sides — satellites breathe well within the canvas, no element touches the edge. No text, letters, numbers, or labels anywhere in the image — SVG labels will be added externally. Color values are rendering guidance only — do not display HEX codes or color names as text. Simplified iconic symbols only, no realistic faces.