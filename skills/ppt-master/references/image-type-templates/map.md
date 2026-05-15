# Type: map

A **stylized geographic outline** (country / region / continent / world) with annotated markers — pins, dots, highlighted regions, connection lines. Used for office locations, market presence, regional data distribution, supply-chain routes, expansion roadmaps, go-to-market geographies.

> **What map means inside a PPT block**: a **schematic geographic visualization**, not a photorealistic globe view. Stylized landmasses with simplified outlines, deliberate marker placement, and minimal cartographic detail. Unlike `infographic` (abstract data zones), map has **real geographic shape** anchoring the composition.

---

## 1. Composition skeleton

```
   ┌────────────────────────────────────┐
   │        ▓▓▓▓▓                        │
   │     ▓▓▓     ▓▓▓     ●               │
   │   ▓▓          ▓▓▓                   │
   │   ▓ Stylized    ▓▓     ●            │
   │   ▓▓ landmass    ▓▓                 │
   │    ▓▓▓          ▓▓                  │
   │      ▓▓▓     ●▓▓                    │
   │         ▓▓▓▓▓                       │
   │                                     │
   │   ●  = location markers             │
   └────────────────────────────────────┘
```

| LAYOUT | One or more simplified landmass outlines positioned on the canvas; marker dots/pins placed at meaningful geographic positions; optional thin connector lines between markers |
| ELEMENTS | The landmass (flat fill or stylized outline) + 3-12 markers + optional region highlights (one or two regions with deeper color) + optional connection arcs |
| NEGATIVE SPACE | Ocean / negative space around the landmass — at least 25% of canvas. Markers should not crowd the landmass edges. |
| BALANCE | Geographic accuracy is approximate but recognizable — viewer should identify the region within one glance |

## 2. Text-policy variants

### 3.1 `text_policy: none`

City / country / region names are added later as SVG overlay. The map shows markers only; SVG text labels each marker position.

Sample fragment:

> NO text, letters, numbers, country names, city names, or marker labels in the image. Markers are dots/pins only; SVG text overlay will add all labels externally.

### 3.2 `text_policy: embedded`

Self-contained reference map where place names are typeset into the design. High failure risk — image models often misspell place names or place them at wrong coordinates. Prefer `none` + SVG overlay unless the design language genuinely requires in-image labels (vintage cartography, atlas-style poster).

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate world office map, text_policy: none, 1280×720**

> Clean flat vector illustration of a stylized world map. Simplified continental landmasses (recognizable but not photorealistic) in primary deep navy `#1E3A5F` solid fill, positioned across the canvas with approximate geographic accuracy. Ocean/negative space is secondary light gray `#F8F9FA`. Eight small accent gold `#D4AF37` circular markers placed at meaningful office locations — three in North America, two in Europe, one in East Asia, one in South Asia, one in Australia. Each marker has a thin pulsing-glow effect at 30% opacity (a subtle ring around the dot). Two thin accent gold connection lines (slightly curved, suggesting flight paths) connect three of the markers. Crisp 1.5px outlines on the landmasses. No country borders within continents — landmasses are single-color solid silhouettes. Composed as a 1280×720 full-bleed world map with 12% padding. NO text, country names, or labels anywhere — SVG will overlay all labels. Color values are rendering guidance only.