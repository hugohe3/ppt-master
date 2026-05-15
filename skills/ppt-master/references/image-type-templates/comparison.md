# Type: comparison

Split composition showing two opposing sides — left vs right, before vs after, A vs B, traditional vs new. Used for pros/cons pages, mindset-shift narratives, option evaluations, transformation stories.

> **What comparison means inside a PPT block**: the image internally has **two symmetric or near-symmetric halves** with clear divider. Each half represents one option/state. Unlike all other types, comparison's signature is the **explicit duality**.

## 1. Composition skeleton

Two sub-structures:

### Sub-structure 1 — Horizontal split (most common)

```
   ┌────────────┬────────────┐
   │            │            │
   │   LEFT     │   RIGHT    │
   │   (before, │   (after,  │
   │   option A)│   option B)│
   │            │            │
   └────────────┴────────────┘
```

### Sub-structure 2 — Vertical split

```
   ┌──────────────┐
   │    TOP       │
   │  (before)    │
   ├──────────────┤
   │   BOTTOM     │
   │  (after)     │
   └──────────────┘
```

| LAYOUT | Two near-equal halves with a clear divider (vertical or horizontal). Each half contains its own content |
| ELEMENTS | Each side has its own anchor element (a figure, an icon cluster, a chart, a stylized scene). Visual treatment is symmetric in structure, distinct in content |
| NEGATIVE SPACE | 12-15% padding on the outer edges; the divider may be a thin line, geometric shape, or simply negative space |
| DIVIDER | Clean — a hand-drawn line, a vertical rule, a geometric shape, or just empty space. Should feel intentional |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Sub-structure fit |
|---|---|---|---|
| Hero before/after banner | 1200×500 | 2.4:1 | Horizontal split ✓✓ |
| Square comparison | 700×700 | 1:1 | Horizontal ✓ or vertical ✓ |
| Half-page comparison | 600×500 | ~1.2 | Horizontal split (compressed) ✓ |
| Tall comparison (vertical split) | 500×700 | ~0.7 | Vertical split ✓✓ |

Inner padding: 12-15% per side.

---

## 3. Text-policy variants

### `text_policy: none`

Each side contains a visual anchor (figure, icon, scene) but no text labels. SVG labels added externally to indicate "Before / After" or "A / B".

### `text_policy: embedded`

Each side may contain short hand-lettered labels: "BEFORE" / "AFTER" at the top, plus 2-3 short English bullet words inside (e.g. "slow / manual / fragile" vs "fast / automated / reliable").

> ink-notes + comparison + embedded is a classic combination — the "manifesto Before/After" page.

---

## 4. Fewshot prompt snippets

**Snippet A — ink-notes + mono-ink, Before/After horizontal split, text_policy: embedded, 1200×500**

> Professional hand-drawn visual-note style on pure white background `#FFFFFF`. The composition is a Before/After horizontal split with a clean vertical hand-drawn divider down the center. Both sides use confident black ink line work with slight wobble. Left side ("Before"): a simplified stick-figure character with frustrated posture, a speech bubble in hand-lettered English caps reading "OLD WAY", and three small hand-drawn dashes with brief 1-word annotations ("manual", "slow", "fragile"). Right side ("After"): a confident stick-figure character with a checkmark above, hand-lettered "NEW WAY" caps label, and three checkbox-style annotations ("automated", "fast", "reliable"). A curved "shift" arrow bridges left to right at mid-height. Sparse semantic accent: coral red `#E8655A` only on left-side pain markers (about 4% area); muted teal `#5FA8A8` only on right-side positive markers (about 3% area). Total color accent under 8%. Composed as a 1200×500 hero banner with 14% inner padding. English-only hand-lettered text. NO Chinese characters. Color values are rendering guidance only.
