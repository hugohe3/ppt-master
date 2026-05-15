# Type: hero

Single dominant subject occupying 60-70% of the canvas. The hero image *anchors* a slide — it's what the page is *about* visually. Used for product reveals, concept introductions, chapter title visuals, brand statement pages.

> **What hero means inside a PPT block**: one confident dominant subject with intentional supporting context. Unlike `background` (no subject), hero is **all about the subject**. Unlike `infographic` (multiple labeled zones), hero is **singular focal subject**.

## 1. Composition skeleton

```
   ┌────────────────────────────────────┐
   │                                     │
   │     ┌──────────────┐                │
   │     │              │                │
   │     │   HERO       │                │
   │     │   SUBJECT    │   (60-70%      │
   │     │              │    of canvas)  │
   │     └──────────────┘                │
   │                                     │
   │   small supporting context only     │
   └────────────────────────────────────┘
```

| LAYOUT | One dominant subject occupying 60-70% of the canvas area, positioned with intent (centered, slight left/right offset, or rule-of-thirds) |
| ELEMENTS | The hero subject + minimal supporting context (background environment, small accent elements). Supporting elements <30% of canvas |
| NEGATIVE SPACE | Generous around the subject — at least 15% padding on the subject's "open" side |
| BALANCE | Subject's visual weight clearly dominant; no second-place subject competing |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page hero (image left/right of text) | 600×600 | 1:1 | 15% around subject |
| Full-bleed hero (subject + slide title overlay) | 1280×720 | 16:9 | 20% offset to keep title area clear |
| Hero band | 1200×500 | 2.4:1 | Generous side padding |
| Square hero | 700×700 | 1:1 | 15% |

---

## 3. Text-policy variants

### `text_policy: none` (most common)

The hero subject is the visual; any title or label comes from SVG overlay.

### `text_policy: embedded`

The hero subject itself includes text — product name on packaging, a hand-lettered word as part of the subject, a designed title floating beside the figure. Specify font family in the prompt to echo the deck's body typography. If the headline *is* the entire visual, switch to `typography` type.

---

## 4. Fewshot prompt snippets

**Snippet A — 3d-isometric + tech-neon product reveal, text_policy: none, 600×600**

> 3D isometric illustration in true 30°/30°/30° projection. One dominant product-form subject — a stylized device or sleek tech object — occupies the center of the canvas at roughly 65% of the area. The subject is rendered in primary electric blue `#0EA5E9` on its lit faces, with 15% darker tonal shift on shadowed faces. A subtle 8%-opacity outer glow halo surrounds the subject. Small supporting context: three thin connecting lines in accent vivid cyan `#06B6D4` arcing from the subject toward the canvas edges (suggesting connectivity), and a soft 8% drop shadow grounding the subject. Background is deep secondary navy `#0A0E27` (about 30% of canvas, including shadowed plane). The subject is clearly the singular focal element. Composed as a 600×600 half-page hero block with 15% padding around the subject. NO text, letters, numbers, or labels anywhere. Color values are rendering guidance only.
