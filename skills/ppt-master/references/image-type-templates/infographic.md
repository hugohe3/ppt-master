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

## 2. Text-policy variants

### `text_policy: none`

Each zone contains an icon only. Labels added in SVG overlay around or below the image.

Sample fragment:

> Each zone contains one simple iconic symbol — chart bar, lightbulb, target, etc. No labels, no captions, no text or numbers anywhere in the image. SVG labels will be added externally.

### `text_policy: embedded`

Each zone contains an icon + one short English keyword (≤2 words).

Sample fragment:

> Each zone contains one iconic symbol and one short hand-lettered English keyword (1-2 words, e.g. "Speed", "Reach", "Trust"). Keywords are part of the artwork. No long sentences, no numbers, no Chinese characters.

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, 2×2 grid, text_policy: none, 600×600**

> Clean flat vector illustration infographic. The composition is a 2×2 grid of equal-sized rounded-rectangle zones, separated by clean gutters (about 12% of canvas width). Each zone has a solid fill in a different tint of the deck's palette: upper-left in primary deep navy `#1E3A5F`, upper-right in a slightly lighter navy tint, lower-left in another navy tint, lower-right with accent gold `#D4AF37` as the highlighted zone (about 7% of canvas total accent area). Crisp 2px outlines, single 8% soft drop shadow under each zone. Each zone contains one simple iconic symbol in white fill — chart bar (upper-left), lightbulb (upper-right), target (lower-left), upward arrow (lower-right). Background field secondary light gray `#F8F9FA` showing through the gutters. Composed as a 600×600 half-page block with 14% inner padding around the grid. NO text, letters, numbers, or labels anywhere — SVG labels added externally. Color values are rendering guidance only. Simplified iconic symbols, no realistic faces.