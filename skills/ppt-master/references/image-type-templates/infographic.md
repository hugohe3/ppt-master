# Type: infographic

2-5 ordered zones, each with an icon and minimal label/keyword. Used for data summaries, KPI rundowns, step lists, feature highlights, value propositions presented visually. **Used as a local block** — the AI image is a small information panel embedded in a slide.

> **What infographic means inside a PPT block**: the image internally is a 2-5-zone information panel. Unlike `framework` (hub + radiating satellites) or `flowchart` (sequential with arrows), infographic has **parallel zones** without strict ordering or directional flow.

## 1. Composition skeleton

Two sub-structures:

### Sub-structure 1 — Grid (most common for infographic)

```
   ┌──────┬──────┐         ┌──────┬──────┬──────┐
   │      │      │         │      │      │      │
   ├──────┼──────┤   or    └──────┴──────┴──────┘
   │      │      │
   └──────┴──────┘
   2×2 (4 zones)            3×1 (3 zones)
```

### Sub-structure 2 — Radial (4-5 zones around a small center anchor)

```
       ◯
        \
   ◯─── · ───◯
        /
       ◯
```

| LAYOUT | 2-5 equal-weight zones arranged in grid or radial pattern. Each zone is visually distinct (own color/icon) but structurally equal |
| ELEMENTS | One icon per zone + (optional) one short keyword. Connecting lines NOT required (unlike framework/flowchart) |
| NEGATIVE SPACE | Generous between zones (10-15% gutters) and inside each zone (60-70% of zone for content, rest as padding) |
| BALANCE | Zones are visually equal — no zone dominates |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Sub-structure fit |
|---|---|---|---|
| Square half-page (2×2 grid) | 600×600 | 1:1 | Grid 2×2 ✓✓ / Radial 4-zone ✓ |
| Wide banner (3×1 grid) | 1200×400 | 3:1 | Grid 3×1 ✓✓ |
| Square radial | 700×700 | 1:1 | Radial 4-5 zones ✓✓ |
| Portrait list (3-4 zones vertical) | 500×700 | ~0.7 | Grid 1×3 or 1×4 ✓ |

Inner padding: 14-18%.

---

## 3. Text-policy variants

### `text_policy: none`

Each zone contains an icon only. Labels added in SVG overlay around or below the image.

Sample fragment:

> Each zone contains one simple iconic symbol — chart bar, lightbulb, target, etc. No labels, no captions, no text or numbers anywhere in the image. SVG labels will be added externally.

### `text_policy: embedded`

Each zone contains an icon + one short English keyword (≤2 words).

Sample fragment:

> Each zone contains one iconic symbol and one short hand-lettered English keyword (1-2 words, e.g. "Speed", "Reach", "Trust"). Keywords are part of the artwork. No long sentences, no numbers, no Chinese characters.

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, 2×2 grid, text_policy: none, 600×600**

> Clean flat vector illustration infographic. The composition is a 2×2 grid of equal-sized rounded-rectangle zones, separated by clean gutters (about 12% of canvas width). Each zone has a solid fill in a different tint of the deck's palette: upper-left in primary deep navy `#1E3A5F`, upper-right in a slightly lighter navy tint, lower-left in another navy tint, lower-right with accent gold `#D4AF37` as the highlighted zone (about 7% of canvas total accent area). Crisp 2px outlines, single 8% soft drop shadow under each zone. Each zone contains one simple iconic symbol in white fill — chart bar (upper-left), lightbulb (upper-right), target (lower-left), upward arrow (lower-right). Background field secondary light gray `#F8F9FA` showing through the gutters. Composed as a 600×600 half-page block with 14% inner padding around the grid. NO text, letters, numbers, or labels anywhere — SVG labels added externally. Color values are rendering guidance only. Simplified iconic symbols, no realistic faces.

**Snippet B — sketch-notes + macaron, 3-zone vertical list, text_policy: embedded, 500×700**

> Warm hand-drawn sketchnote infographic on warm cream paper background `#F5F0E8`. Three rounded-rectangle zones arranged vertically with hand-drawn black ink wobbly outlines. Each zone has a different soft pastel fill (light blue top, mint middle, peach bottom) with slight hand-painted overshoot beyond outlines. Each zone contains one simple hand-drawn cartoon icon and one short hand-lettered English keyword: top zone with a lightbulb icon and "IDEAS", middle zone with a person icon and "TEAM", bottom zone with an upward arrow and "GROWTH". Hand-drawn wavy connector lines between zones (subtle). Small doodle decorations (a star, a dot) sparingly around the composition. Composed as a 500×700 vertical block with 16% inner padding. Hand-lettered text in English only, no numbers, no Chinese characters. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Zones unequal size | Equality rule omitted | Strengthen "all zones visually equal in size and weight" |
| Zones missing icons | Icon rule too vague | "Each zone contains exactly one iconic symbol" |
| Garbled keywords in embedded | CJK or too long | Switch to English, ≤2 words per zone |
| Connector lines appearing (becomes framework/flowchart) | Composition drift | Reaffirm "zones are parallel and equal — no connector lines, no arrows, no directional flow" |
| Center is overcrowded in radial | Center anchor too large | "Small center anchor only — satellites carry the content" |

---

## 6. When to switch away from infographic

- If structure is **central hub + radiating elements** → `framework`
- If structure is **sequential with arrows** → `flowchart`
- If structure is **two opposing options** → `comparison`
- If structure is **time-ordered** → `timeline`
- If pure ambient backdrop → `background`
