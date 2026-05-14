# Rendering: digital-dashboard

Polished UI / data-visualization aesthetic. The image looks like a screenshot of a product or analytics dashboard — clean cards, soft shadows, restrained type, chart-like visual elements. Used in SaaS demos, data product showcases, B2B analytics decks.

## Style paragraph (paste-ready, 105 words)

> Polished digital UI / dashboard aesthetic. Clean card-based layout with rounded corners (8-12px radius), uniform soft shadows (8% opacity, slight Y-offset), and crisp pixel-aligned edges. Surfaces are flat with restrained color — primarily one neutral background, several brand-color cards or chart elements, and a single accent for the focal data point. Chart-like visual elements (bar graphs, line graphs, sparklines, donut segments, KPI tiles) appear stylized — recognizable as charts but without specific data values. Typography would be small, neutral, almost-text-as-texture if any appeared, but defaults to no-text. Overall feel is product-screenshot — modern, restrained, data-fluent.

## Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | No outlines on cards; chart elements use thin uniform strokes (1-1.5px feel) |
| Texture | None — clean digital surfaces |
| Depth | Uniform 8% soft drop shadows under cards; no inset/raised effects |
| Material | Flat with deliberate elevation hierarchy via shadows |
| Mood | Polished, restrained, product-fluent |

## Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page product demo | 600×500 | ~1.2 | 10% (dashboards lean toward edge-aligned cards) |
| Hero product showcase | 1200×600 | 2:1 | 10% |
| Spot dashboard tile | 400×300 | 4:3 | 8% |
| Full-bleed product hero | 1280×720 | 16:9 | 10% |

## Using the deck's HEX values

- Primary HEX: dominant chart element / featured card header
- Secondary HEX: background canvas (usually pale or near-white)
- Accent HEX: the single highlighted data point or focal metric
- Optional 4th: a muted neutral for secondary chart elements (gray bars, faded sparklines)

## Fewshot prompt snippets

**Snippet A — half-page product demo, text_policy: none**

> Polished digital dashboard UI aesthetic. Three rounded-corner cards arranged in a clean grid on a soft secondary background `#F8FAFC`. The largest card (top, occupying 60% of the area) shows a stylized line chart trending upward in primary blue `#0EA5E9` — three line segments, smooth curve, anchor dots at peaks. Two smaller cards below show: (left) a stylized donut chart with the primary color filling about 70% of the ring, (right) a simple KPI tile with a large iconic upward arrow in accent green `#10B981`. All cards have 8-12px rounded corners and uniform 8% soft drop shadows. Pixel-aligned edges. Composed as a 600×500 half-page block with 10% inner padding. NO text, no numbers, no chart labels, no axes — pure visual chart elements only. Color values are rendering guidance only.

**Snippet B — hero product showcase, text_policy: none**

> Polished SaaS dashboard hero image. A large central rectangular card occupies 75% of the canvas with 12px rounded corners and a soft 8% drop shadow, sitting on a clean secondary background `#F1F5F9`. The card surface shows a stylized analytics screen — a tall vertical bar chart on the left using primary navy `#1E3A8A` with one accent orange `#F97316` bar highlighted, a line chart on the right with two intersecting trend lines, and three small KPI tiles across the top. All chart elements are stylized — recognizable as charts but without specific values, axes, or labels. Background field is calm and uncluttered. Composed for a 1200×600 hero band with 10% inner padding. NO text, no numbers, no axis labels, no captions anywhere. Color values are rendering guidance only.

## What to avoid

- Real numbers, real labels (model often invents misleading values)
- Photorealistic device frames (laptop bezel, phone shell) unless explicitly intended
- Overly busy charts — keep to 3-5 chart elements maximum
- Skeuomorphic depth (glass, metal, gloss) — keep it flat-modern

## When to switch away

- For non-product visuals → `vector-illustration` or `flat`
- For technical architecture with 3D forms → `3d-isometric`
- For schematic technical drawings → `blueprint`
