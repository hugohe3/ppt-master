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

## 2. Text-policy variants

### 3.1 `text_policy: none`

Tier labels are added later as SVG overlay. Each tier shows an icon only; the SVG places tier names beside or inside.

Sample fragment:

> NO text, letters, numbers, or tier labels in the image. Each tier contains only one simple iconic symbol; SVG text overlay will add tier names externally.

### 3.2 `text_policy: embedded`

Self-contained pyramid with tier names typeset into the artwork. Keep tier names to single English words in a font family echoing the deck's body typography. High failure risk on 5+ tier pyramids — stay at 3-4 tiers when going embedded.

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate Maslow pyramid, text_policy: none, 600×800**

> Clean flat vector illustration of a hierarchy pyramid. Five horizontal stepped tiers stacked vertically, each tier centered on the canvas vertical axis and ~18% narrower than the tier below. From bottom to top: tier 1 (foundation, widest) in deeper primary `#1E3A5F`; tier 2 in primary `#3B5478`; tier 3 in lighter primary `#5A7099`; tier 4 in secondary blue tint `#A8BDDD`; tier 5 (apex, narrowest) in accent gold `#D4AF37`. Each tier has one simple white iconic symbol centered — a brick (physiological), a shield (safety), a heart (belonging), a trophy (esteem), a star (self-actualization). Thin secondary cream `#F8F9FA` dividers separate the tiers. Background secondary cream. Composed as a 600×800 portrait pyramid block with 12% padding. NO text or labels — SVG will overlay tier names. Color values are rendering guidance only.