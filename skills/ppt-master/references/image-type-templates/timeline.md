# Type: timeline

Linear progression along a time axis — milestones, evolution, roadmap, history. Used for company history pages, product evolution, project roadmaps, era-by-era narratives.

> **What timeline means inside a PPT block**: the image internally has a clear **axis (horizontal or vertical)** with 3-6 milestone markers along it. Unlike `flowchart` (process with arrows), timeline is **about time positions**. Unlike `framework` (relational), timeline is **sequential and chronological**.

## 1. Composition skeleton

Two sub-structures:

### Sub-structure 1 — Horizontal timeline (most common)

```
   ──●─────●─────●─────●─────●──
     |     |     |     |     |
   2020  2021  2022  2023  2024
   icon  icon  icon  icon  icon
```

### Sub-structure 2 — Vertical timeline

```
   ●─── milestone 1
   │
   ●─── milestone 2
   │
   ●─── milestone 3
   │
   ●─── milestone 4
```

| LAYOUT | A clear axis (line) with 3-6 milestone markers (dots, small shapes) positioned along it. Each milestone has its associated visual element (icon, illustration) near it |
| ELEMENTS | Axis line is thin and uniform; milestone markers are visually consistent; iconic elements at each milestone are simple and parallel in style |
| NEGATIVE SPACE | Generous space above/below (or left/right) the axis to give milestones breathing room |
| TIME DIRECTION | Direction is unambiguous (left-to-right = earlier-to-later) |

## 2. Text-policy variants

### `text_policy: none`

Each milestone has an iconic symbol only. Date labels and milestone descriptions added in SVG overlay.

### `text_policy: embedded`

Each milestone may include a short date (e.g. "2020", "Q1", "v1.0") rendered as part of the artwork. Keep labels minimal — just dates or short anchors, not descriptions.

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, horizontal 5-milestone timeline, text_policy: none, 1200×500**

> Clean flat vector illustration timeline banner. A thin horizontal axis line in primary deep navy `#1E3A5F` runs across the canvas at mid-height. Five circular milestone markers are evenly spaced along the axis — each marker filled with the primary navy and a 2px outline. The third milestone (center) is highlighted with an accent gold `#D4AF37` ring around it (under 5% accent area). Above each marker is a small simple iconic symbol — a seed, a sprout, a plant, a tree, a forest — telling a growth sequence. Below each marker, a thin vertical tick mark drops to the axis. Background is calm secondary light gray `#F8F9FA`. Composed for a 1200×500 hero banner with 12% inner padding above and below the axis. NO text, dates, or labels — SVG labels added externally. Color values are rendering guidance only.