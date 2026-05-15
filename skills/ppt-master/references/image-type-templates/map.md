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

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed map page | 1280×720 | 16:9 | 12% all sides (world map fits 16:9 well) |
| Half-page country map | 600×600 | 1:1 | 12% |
| Wide regional map | 1200×500 | 2.4:1 | 12% |
| Square continent map | 700×700 | 1:1 | 12% |

---

## 3. Text-policy variants

### 3.1 `text_policy: none` (default)

City / country / region names are added later as SVG overlay. The map shows markers only; SVG text labels each marker position.

Sample fragment:

> NO text, letters, numbers, country names, city names, or marker labels in the image. Markers are dots/pins only; SVG text overlay will add all labels externally.

### 3.2 `text_policy: embedded` (when place names belong in the artwork)

Self-contained reference map where place names are typeset into the design. High failure risk — image models often misspell place names or place them at wrong coordinates. Prefer `none` + SVG overlay unless the design language genuinely requires in-image labels (vintage cartography, atlas-style poster).

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate world office map, text_policy: none, 1280×720**

> Clean flat vector illustration of a stylized world map. Simplified continental landmasses (recognizable but not photorealistic) in primary deep navy `#1E3A5F` solid fill, positioned across the canvas with approximate geographic accuracy. Ocean/negative space is secondary light gray `#F8F9FA`. Eight small accent gold `#D4AF37` circular markers placed at meaningful office locations — three in North America, two in Europe, one in East Asia, one in South Asia, one in Australia. Each marker has a thin pulsing-glow effect at 30% opacity (a subtle ring around the dot). Two thin accent gold connection lines (slightly curved, suggesting flight paths) connect three of the markers. Crisp 1.5px outlines on the landmasses. No country borders within continents — landmasses are single-color solid silhouettes. Composed as a 1280×720 full-bleed world map with 12% padding. NO text, country names, or labels anywhere — SVG will overlay all labels. Color values are rendering guidance only.

**Snippet B — flat + tech-neon Asia-Pacific market map, text_policy: none, 1200×500**

> Modern flat geometric stylized map of the Asia-Pacific region. Recognizable simplified outlines of China, Japan, Korea, Southeast Asian countries, and Australia in primary electric blue `#0EA5E9` solid fill. Ocean is secondary deep navy `#0A0E27`. Six accent vivid cyan `#06B6D4` circular markers placed at major commercial cities. Two markers (the highest-value ones) carry a subtle outer glow halo at 25% opacity. Curved thin accent cyan arcs (3-4 of them) suggest trade routes between markers. No country borders, no political subdivisions — landmasses are single-color silhouettes. Composed as a 1200×500 wide regional map block with 12% padding. NO text, country names, or labels in the image. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Landmasses unrecognizable | Stylization went too far | "Landmasses simplified but recognizable — viewer must identify the region at a glance" |
| Photorealistic globe / satellite imagery | Wrong cartographic register | Reaffirm "stylized flat vector silhouette, NOT photorealistic globe view" |
| Country borders cluttering | Sub-region detail crept in | "Landmasses are single-color silhouettes — NO country borders within continents, no political subdivisions" |
| Markers off-coast / on ocean | Geographic placement loose | "Markers placed on land at approximately accurate geographic positions" |
| Misspelled place names | Text policy violated | Set `text_policy: none` and add labels in SVG |
| Map fills entire canvas (no breathing) | Negative space rule omitted | "Ocean / negative space surrounds the landmass on all sides — at least 25% of canvas is open ocean" |

---

## 6. When to switch away from map

- If geographic shape is irrelevant (just abstract data zones) → `infographic`
- If data is sequential / chronological → `timeline`
- If structure is hierarchical → `pyramid` or `framework`
- If comparing two regions explicitly → `comparison` (each side a map)
- If atmospheric environment / scene → `scene`
