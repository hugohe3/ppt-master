# Type: pyramid

A **tiered triangular stack** — bottom-wide, top-narrow — where each layer carries its own label/color/concept. The structural backbone for Maslow's hierarchy, food pyramids, capability stacks, value hierarchies, software-architecture layer diagrams.

> **What pyramid means inside a PPT block**: a **converging-upward** layered structure embodying "foundation supports value" — wide stable base, narrow apex of meaning. Unlike `funnel` (narrows downward, about filtering), pyramid narrows upward, about **stacking value or hierarchy**. Unlike `framework` (centered hub), pyramid is **strictly vertical layered**.

---

## 1. Composition skeleton

```
              ┌──────┐                ← Apex (smallest)
              │ T 5  │
            ┌─┴──────┴─┐
            │   T 4    │
          ┌─┴──────────┴─┐
          │     T 3      │
        ┌─┴──────────────┴─┐
        │       T 2        │
      ┌─┴──────────────────┴─┐
      │         T 1          │       ← Foundation (widest)
      └──────────────────────┘
```

| LAYOUT | 3-6 horizontal layers stacked vertically; each layer narrower than the one below it. May be a true triangular outline (sloping sides) OR stepped (right-angled tiers). |
| ELEMENTS | One simple iconic symbol per tier + the tier itself as the dominant color block. Tier colors usually progress from a darker/heavier color at the base to a brighter/lighter color at the apex (or vice versa, depending on the metaphor) |
| NEGATIVE SPACE | Side margins grow as tiers narrow — outer field on either side of upper tiers |
| BALANCE | Vertical center axis is the pyramid's spine — all tiers center-align |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed pyramid page | 1280×720 | 16:9 | 12% sides, 10% top/bottom |
| Portrait pyramid block | 600×800 | 3:4 | 12% |
| Half-page pyramid | 600×700 | ~0.85 | 12% |
| Square reference pyramid | 700×700 | 1:1 | 12% |

---

## 3. Text-policy variants

### 3.1 `text_policy: none` (default)

Tier labels are added later as SVG overlay. Each tier shows an icon only; the SVG places tier names beside or inside.

Sample fragment:

> NO text, letters, numbers, or tier labels in the image. Each tier contains only one simple iconic symbol; SVG text overlay will add tier names externally.

### 3.2 `text_policy: embedded` (when tier names are part of the design)

Self-contained pyramid with tier names typeset into the artwork. Keep tier names to single English words in a font family echoing the deck's body typography. High failure risk on 5+ tier pyramids — stay at 3-4 tiers when going embedded.

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate Maslow pyramid, text_policy: none, 600×800**

> Clean flat vector illustration of a hierarchy pyramid. Five horizontal stepped tiers stacked vertically, each tier centered on the canvas vertical axis and ~18% narrower than the tier below. From bottom to top: tier 1 (foundation, widest) in deeper primary `#1E3A5F`; tier 2 in primary `#3B5478`; tier 3 in lighter primary `#5A7099`; tier 4 in secondary blue tint `#A8BDDD`; tier 5 (apex, narrowest) in accent gold `#D4AF37`. Each tier has one simple white iconic symbol centered — a brick (physiological), a shield (safety), a heart (belonging), a trophy (esteem), a star (self-actualization). Thin secondary cream `#F8F9FA` dividers separate the tiers. Background secondary cream. Composed as a 600×800 portrait pyramid block with 12% padding. NO text or labels — SVG will overlay tier names. Color values are rendering guidance only.

**Snippet B — 3d-isometric + tech-neon capability stack, text_policy: none, 700×700**

> 3D isometric illustration of a software capability stack — four stepped layers stacked vertically in true 30°/30°/30° projection, each layer narrower than the one below, slightly offset to suggest depth. Bottom layer (widest, foundation) in deep primary navy `#0A0E27`; layer 2 in primary electric blue `#0EA5E9`; layer 3 in accent vivid cyan `#06B6D4`; top layer (narrowest, apex) in bright accent white-cyan `#A5F3FC` with subtle outer glow. Each layer's top face carries one simple iconic symbol in white — a server, a database icon, an API connector, a sparkle. Soft 8% drop shadow under the stack. Background secondary deep navy. Composed as a 700×700 reference pyramid block with 12% padding. NO text in the image. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Tiers same width (looks like a stack of bars) | Narrowing rule omitted | "Each tier is 15-20% narrower than the tier below — the pyramid must visibly narrow upward" |
| Pyramid inverted (narrowing downward) | Direction reversed | "Pyramid narrows UPWARD — widest tier at the bottom (foundation), narrowest at the top (apex)" |
| Tiers off-center | Center-axis rule omitted | "All tiers center-align on the canvas vertical axis — the pyramid is symmetrical left-right" |
| Confused with funnel | Metaphor wrong | "Pyramid narrows UPWARD for hierarchy/value stacking, not downward for conversion filtering" |
| Wrong number of tiers | Count drifted | Explicitly state "exactly N tiers" |

---

## 6. When to switch away from pyramid

- If structure is **narrowing downward (conversion)** → `funnel`
- If structure is **central hub + radial** → `framework`
- If structure is **2×2 quadrant grid** → `matrix`
- If chronological progression → `timeline`
- If closed loop → `cycle`
- If linear sequential → `flowchart`
