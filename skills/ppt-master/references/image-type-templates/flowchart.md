# Type: flowchart

Sequential blocks connected by arrows, showing process / workflow / pipeline. Used for "how-it-works" visuals, onboarding steps, pipeline diagrams, sequential methodologies.

> **What flowchart means inside a PPT block**: the image internally shows 3-6 stages in a clear directional sequence. Unlike `infographic` (parallel zones), flowchart has **direction**. Unlike `framework` (hub + satellites), flowchart has **sequence**.

## Composition skeleton

Three sub-structures:

### Sub-structure 1 — Horizontal flow (most common)

```
   ┌───┐ → ┌───┐ → ┌───┐ → ┌───┐
   │ 1 │   │ 2 │   │ 3 │   │ 4 │
   └───┘   └───┘   └───┘   └───┘
```

### Sub-structure 2 — Vertical flow

```
   ┌───┐
   │ 1 │
   └─┬─┘
     ↓
   ┌───┐
   │ 2 │
   └─┬─┘
     ↓
   ┌───┐
   │ 3 │
   └───┘
```

### Sub-structure 3 — Looping / cyclical

```
   ┌───┐ → ┌───┐
   │ 1 │   │ 2 │
   └───┘   └─┬─┘
     ↑       ↓
   ┌───┐ ← ┌───┐
   │ 4 │   │ 3 │
   └───┘   └───┘
```

| LAYOUT | 3-6 stage blocks with explicit connectors (arrows or lines with arrowheads) showing direction |
| ELEMENTS | Stages visually consistent (same shape, similar size); connectors uniform stroke weight; arrowheads consistent style |
| NEGATIVE SPACE | Generous around the flow — stages don't touch edges, connectors don't crowd |
| DIRECTIONAL CLARITY | The flow direction is unambiguous |

## Container sizing for local PPT inserts

| Use | Canvas | Aspect | Sub-structure fit |
|---|---|---|---|
| Horizontal banner (3-5 stage flow) | 1200×400 | 3:1 | Horizontal flow ✓✓ |
| Half-page vertical (3-4 stages) | 500×700 | ~0.7 | Vertical flow ✓✓ |
| Square cyclical | 700×700 | 1:1 | Looping ✓✓ |
| Half-page horizontal (3 stages) | 600×400 | 1.5:1 | Horizontal compressed ✓ |

Inner padding: 14-16%.

## Text-policy variants

### `text_policy: none`

Each stage contains an iconic symbol only. Stage labels added in SVG overlay below or above the image.

### `text_policy: embedded`

Each stage may contain a short English keyword (≤2 words) inside or beside it.

## Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate, horizontal 4-stage flow, text_policy: none, 1200×400**

> Clean flat vector illustration flowchart banner. Four rounded-rectangle stages arranged horizontally across the canvas, separated by uniform gaps. Each stage is filled with primary deep navy `#1E3A5F`, with crisp 2px outlines and 8% soft drop shadow. Between each pair of stages, a thin uniform horizontal arrow with a clean triangular arrowhead in secondary `#F8F9FA` or near-black. The third stage (highlighted as the focal stage) has a thin accent gold `#D4AF37` ring around it — under 5% accent area. Each stage contains one simple iconic symbol in white — an input arrow, a gear, a magnifier, an output arrow respectively. Background field is secondary light gray `#F8F9FA`. Composed for a 1200×400 hero band with 14% inner padding. NO text, letters, numbers, or labels — SVG labels added externally. Color values are rendering guidance only.

**Snippet B — blueprint + tech-neon, vertical 4-stage pipeline, text_policy: none, 500×700**

> Technical blueprint pipeline schematic, vertical orientation. Four rounded rectangle stages stacked vertically on a near-white background `#FAFAFA` with subtle grid pattern at 6% opacity in primary deep blue. Each stage uses 1.5px primary deep blue `#1E40AF` stroke; the second stage from top has its stroke replaced with accent vivid cyan `#06B6D4` as the focal stage. Between each pair of stages, a clean downward-pointing arrow with precise arrowhead in blueprint blue. Small anchor dots at line junctions. Each stage contains one iconic symbol in monoline schematic style — input symbol, transform symbol, validate symbol, output symbol. Composed as a 500×700 vertical pipeline with 14% inner padding. NO text or labels anywhere. Color values are rendering guidance only.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Arrows missing or unclear direction | Arrow rule too weak | Reaffirm "clear directional arrows between every consecutive stage, uniform arrowhead style" |
| Stages unequal size | Equality rule omitted | "All stages visually equal — same shape, similar size, same color treatment" |
| Stages too dense | Padding omitted | "Generous gaps between stages — stages don't crowd each other" |
| Flow direction ambiguous | Composition error | Explicit "flow reads left-to-right (or top-to-bottom)" |
| Cyclical not closing | Looping rule omitted (for cyclical only) | "Cyclical flow closes back to stage 1 via a return arrow" |

## When to switch away from flowchart

- If parallel zones without sequence → `infographic`
- If central hub with satellites → `framework`
- If two opposing options → `comparison`
- If time-ordered milestones → `timeline`
