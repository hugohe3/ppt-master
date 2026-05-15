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
