# Type: funnel

A **top-wide, bottom-narrow stack** of horizontal bands representing successive conversion stages. Each band is narrower than the one above it, suggesting attrition/filtering as the process progresses. The standard structural backbone for marketing funnels, sales pipelines, hiring funnels, customer-journey conversion.

> **What funnel means inside a PPT block**: a **converging-downward** stack — visual weight shrinks as you descend, embodying "many enter the top, few reach the bottom". Unlike `pyramid` (which can be either direction but typically narrows-upward for hierarchy/value), funnel is **always wide-to-narrow downward** and is about **filtering**, not hierarchy.

---

## 1. Composition skeleton

```
   ┌──────────────────────────────────┐ ← Band 1 (widest)
   │             Awareness            │
   ├────────────────────────────────  ┤
    ┌────────────────────────────┐    ← Band 2 (narrower)
    │           Interest         │
    ├──────────────────────────  ┤
      ┌──────────────────────┐         ← Band 3
      │      Consideration   │
      ├────────────────────  ┤
        ┌──────────────┐               ← Band 4
        │   Conversion │
        └──────────────┘
```

| LAYOUT | 3-6 horizontal bands stacked vertically; each band's width decreases by ~15-25% from the band above |
| ELEMENTS | One simple iconic symbol per band (left side) + the band itself as the dominant color block. Optional thin divider lines between bands |
| NEGATIVE SPACE | Side margins grow as bands narrow — outer field on either side of the lower bands provides breathing room |
| BALANCE | Vertical center axis is the funnel's spine — all bands center-align to this axis |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed funnel page | 1280×720 | 16:9 | 12% sides, 10% top/bottom |
| Portrait funnel block | 600×800 | 3:4 | 12% (portrait reads funnels naturally) |
| Half-page funnel | 600×700 | ~0.85 | 12% |
| Square reference funnel | 700×700 | 1:1 | 12% |

---

## 3. Text-policy variants

### 3.1 `text_policy: none`

Each band shows an icon only; stage labels are handled in SVG.

Sample fragment:

> NO text, letters, numbers, or stage labels in the image. Each band contains only one simple iconic symbol; SVG text overlay will add stage names externally.

### 3.2 `text_policy: embedded`

Self-contained funnel diagram where band names are typeset into the artwork. Keep band names to single English words ("AWARE", "LIKE", "BUY", "REFER") in a font family echoing the deck's body typography. High failure risk on 5+ band funnels — stay at 3-4 bands when going embedded.

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate marketing funnel, text_policy: none, 600×800**

> Clean flat vector illustration of a marketing conversion funnel. Four horizontal bands stacked vertically, each band centered on the vertical axis and each ~20% narrower than the one above. Band 1 (top, widest): primary deep navy `#1E3A5F` solid fill, with a simple white megaphone icon centered on the left. Band 2: secondary lighter navy tint, with a heart icon. Band 3: accent gold `#D4AF37`, with a shopping-cart icon. Band 4 (bottom, narrowest): deeper accent gold, with a star icon. Each band has crisp straight edges and 8% drop shadow beneath. Thin secondary cream `#F8F9FA` dividers separate the bands. Background is calm secondary cream. Composed as a 600×800 portrait funnel block with 12% padding. NO text, letters, numbers, or stage labels anywhere — SVG will overlay all band names. Color values are rendering guidance only.

**Snippet B — flat + vivid-launch sales pipeline, text_policy: none, 600×700**

> Flat geometric sales pipeline funnel. Five horizontal bands stacked vertically with a smooth gradient of narrowing widths (each band ~18% narrower than the one above). Bands cycle through the deck's three colors as flat solid fills: band 1 in primary vivid coral `#F97316`, band 2 in secondary cream `#FEF3C7`, band 3 in primary coral, band 4 in accent deep purple `#7C3AED`, band 5 (narrowest) in deeper purple. Each band has one simple white iconic symbol centered on its left third — a magnet, an eye, a hand, a handshake, a trophy. Crisp solid edges, no gradients, no shadows beyond a single 8% drop. The funnel's narrowing creates symmetric breathing room on left and right. Composed as a 600×700 half-page funnel block with 12% padding. NO text or labels in the image. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Bands not narrowing (looks like stacked bars) | Width gradient omitted | "Each successive band is 15-25% narrower than the band above it — the funnel must visibly converge" |
| Bands off-center | Center-axis rule omitted | "All bands center-align on the canvas vertical axis — the funnel is symmetrical left-right" |
| Pyramid shape (narrowing upward) | Direction reversed | "Funnel narrows DOWNWARD — widest band at the top, narrowest at the bottom" |
| Wrong number of bands | Count drifted | Explicitly state "exactly N bands" |
| Bands visually equivalent in importance | Color cycling weak | "Color progression supports the conversion narrative — typically primary at top fades through palette to accent at bottom (or vice versa)" |

---

## 6. When to switch away from funnel

- If structure is **value/hierarchy stack (narrowing upward)** → `pyramid`
- If structure is **linear sequential with no narrowing** → `flowchart` or `timeline`
- If closed loop with feedback → `cycle`
- If two-way comparison → `comparison`
- If central hub + radial → `framework`
