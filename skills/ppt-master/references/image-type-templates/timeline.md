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

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Sub-structure fit |
|---|---|---|---|
| Hero horizontal timeline | 1200×350 | 3.4:1 | Horizontal timeline ✓✓ |
| Wide timeline banner | 1200×500 | 2.4:1 | Horizontal with icons ✓✓ |
| Half-page horizontal (compressed) | 600×400 | 1.5:1 | Horizontal 3-4 stops ✓ |
| Tall vertical timeline | 500×800 | ~0.6 | Vertical timeline ✓✓ |

Inner padding: 12-15% on the axis's "open" sides.

---

## 3. Text-policy variants

### `text_policy: none`

Each milestone has an iconic symbol only. Date labels and milestone descriptions added in SVG overlay.

### `text_policy: embedded`

Each milestone may include a short date (e.g. "2020", "Q1", "v1.0") rendered as part of the artwork. Keep labels minimal — just dates or short anchors, not descriptions.

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, horizontal 5-milestone timeline, text_policy: none, 1200×500**

> Clean flat vector illustration timeline banner. A thin horizontal axis line in primary deep navy `#1E3A5F` runs across the canvas at mid-height. Five circular milestone markers are evenly spaced along the axis — each marker filled with the primary navy and a 2px outline. The third milestone (center) is highlighted with an accent gold `#D4AF37` ring around it (under 5% accent area). Above each marker is a small simple iconic symbol — a seed, a sprout, a plant, a tree, a forest — telling a growth sequence. Below each marker, a thin vertical tick mark drops to the axis. Background is calm secondary light gray `#F8F9FA`. Composed for a 1200×500 hero banner with 12% inner padding above and below the axis. NO text, dates, or labels — SVG labels added externally. Color values are rendering guidance only.

**Snippet B — editorial + editorial-classic, vertical 4-milestone history, text_policy: embedded, 500×800**

> Magazine-style editorial timeline, vertical orientation. A thin vertical axis rule in primary deep navy `#0F2C4C` runs down the canvas, slightly offset to the left of center. Four small circular milestone markers along the axis at equal intervals. Each milestone has a short hand-lettered English year label (e.g. "1980", "2000", "2010", "2020") rendered to the left of the marker in confident editorial type — short numeric labels only, no descriptions. To the right of each marker, one small iconic symbol — a tower, a globe, a phone, a chip — in primary navy with subtle 8% drop shadow. Background is warm secondary cream `#FAF7F2` with subtle paper grain at 8% opacity. Accent burnt orange `#C2410C` appears only on the third milestone's marker as a small emphasis (under 5%). Composed as a 500×800 vertical block with 14% inner padding. English numeric labels only (no Chinese characters). Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Axis line missing or unclear | Axis rule too weak | "Clear continuous axis line connecting all milestones, uniform stroke weight" |
| Milestones unevenly spaced | Spacing rule omitted | "Milestones evenly spaced along the axis" |
| Direction ambiguous | Direction not specified | "Time progresses left-to-right (or top-to-bottom)" |
| Iconic clutter | Icons too detailed | "Each milestone has one simple iconic symbol — recognizable at small size" |
| Date labels garbled in embedded | Long or CJK dates | Use short English numeric labels only ("2020", "Q1") |

---

## 6. When to switch away from timeline

- If progression has process steps with arrows → `flowchart`
- If parallel zones without chronology → `infographic`
- If central concept with related ideas → `framework`
- If atmospheric history scene → `scene`
