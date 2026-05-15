# Rendering: vintage-poster

Mid-century modern (1950s–1970s) poster aesthetic. Limited color palette, halftone or paper texture, retro geometric character, hand-drawn warmth without looseness. Used for cultural decks, brand storytelling, hospitality, retro tech narratives, anniversaries, heritage brands.

---

## 1. Style paragraph (paste-ready, 105 words)

> Mid-century modern poster aesthetic — the design language of 1950s–1970s travel posters, jazz album covers, and Saul Bass title cards. Composition uses bold geometric shapes with rounded organic edges, often slightly off-axis for retro tension. Color is applied in limited flat blocks (typically 3-5 colors total) with subtle halftone or screen-print texture over the fills. Lines are thick but hand-aware — not perfectly mechanical, with slight character. Imagery is stylized and reduced — a stylized sun, an angular mountain, an iconic silhouette — never photorealistic. Paper grain at ~10% opacity overlays the composition for tactile age. Overall feel is warm, confident, nostalgic without being kitsch — the aesthetic of Knoll, Olivetti, Pan Am.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Confident thick lines with slight hand-aware character; rounded corners |
| Texture | Halftone dot pattern OR subtle paper grain at 10-15% opacity over fills |
| Depth | Flat — depth implied via overlapping shapes, never via shadow |
| Material | Printed-paper aesthetic — slight ink misregistration adds authenticity |
| Mood | Warm, confident, nostalgic, optimistic-retro |

---

## 3. Container sizing for local PPT inserts

| Embedded position | Recommended canvas | Aspect | Inner padding |
|---|---|---|---|
| Full-bleed poster page | 1280×720 | 16:9 | 12% all sides |
| Half-page poster block | 600×800 | 3:4 | 12% |
| Hero band | 1200×500 | 2.4:1 | 12% |
| Square album-cover style | 700×700 | 1:1 | 12% |

---

## 4. Using the deck's HEX values

vintage-poster works best when the deck's HEX values lean **earthy or saturated-warm**. Cool-corporate primaries can work but lose some retro character.

- Primary HEX: dominant shape fills (large geometric blocks)
- Secondary HEX: paper-field background (often warm cream rather than pure white)
- Accent HEX: small accent shapes or the halftone overlay tint
- Add 1-2 additional muted retro neutrals (warm cream, faded ivory) if the deck only specifies a primary triplet

---

## 5. Fewshot prompt snippets

**Snippet A — travel-poster hero, text_policy: none**

> Mid-century modern travel-poster composition. A stylized angular mountain silhouette in primary deep teal `#0F766E` rises across the lower 60% of the canvas, slightly off-axis for retro tension. Above it, a perfect-circle sun in accent burnt-orange `#C2410C` sits at the upper-right rule-of-thirds. Background is warm cream `#FEF3C7` (the deck's secondary, slightly toned toward paper). Subtle halftone dot pattern at 12% opacity overlays the mountain and sun. Thin slightly-misregistered ink offset along the mountain edge adds screen-print authenticity. Paper grain at 10% opacity over the whole composition. No additional elements. Composed as a 1200×500 hero poster band with 12% padding. NO text, letters, or numbers in the image. Color values are rendering guidance only.

**Snippet B — album-cover style spot, text_policy: none**

> Mid-century modern album-cover composition. A stylized abstract figure formed from interlocking geometric shapes — a half-circle, a triangle, a thick curved line — arranged in deliberate retro asymmetry. Primary mustard `#D4A017` and secondary deep maroon `#7C2D12` carry the figure. A small accent cream `#FEF3C7` shape acts as the visual rest. Background is muted warm gray with subtle paper grain at 12% opacity. Halftone overlay at 10% opacity over the figure. Slight ink misregistration along edges suggests screen-print. Composed as a 700×700 square poster spot with 12% padding. NO text in the image. Color values are rendering guidance only.

---

## 6. Forbidden

- Photorealistic imagery (defeats poster stylization)
- Modern thin-line vector look (this is hand-aware retro)
- More than 5 colors total
- Gradients (vintage-poster uses flat color + halftone, never smooth gradient)
- Clean digital edges without any misregistration or paper texture

---

## 7. When to switch away

- For pure poster without retro reference → `screen-print`
- For corporate restraint → `vector-illustration` or `flat`
- For story / narrative atmosphere → `warm-scene` or `watercolor`
- For magazine editorial → `editorial`
