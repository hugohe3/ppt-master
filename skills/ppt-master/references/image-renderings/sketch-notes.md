# Rendering: sketch-notes

Warm cream paper with black hand-drawn lines and soft pastel color blocks. The most "approachable" rendering — used in education, training, onboarding, science communication, knowledge content where warmth and friendliness matter more than corporate precision.

## 1. Style paragraph (paste-ready, 110 words)

> Warm hand-drawn sketchnote style on cream paper background. All lines are drawn with deliberate slight wobble — black ink on cream, never perfectly straight, with the human-hand quality that makes the image feel like a thoughtful teacher's whiteboard. Color blocks are soft pastels — light blue, mint, lavender, peach — filled into rounded shapes that don't quite reach their outlines (a deliberate "hand-painted overshoot" feel). Simple cartoon icons and small doodle decorations (stars, sparkles, dots, underlines) appear sparingly to add warmth. Composition is airy and well-organized, with generous white space between elements. Overall feel is warm, instructional, friendly — the visual language of educational explainer videos and knowledge cards.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Hand-drawn black ink with slight wobble; uniform medium weight |
| Texture | Subtle paper grain at 8-12% opacity over cream background |
| Depth | Flat — sketchnote is intentionally 2D |
| Material | Paper + ink + pastel block (hand-painted overshoot) |
| Mood | Warm, instructional, friendly |

## 3. Using the deck's HEX values

sketch-notes has a strong **built-in palette tendency** toward warm cream + black ink + soft pastels. When the deck's `design_spec.colors` align (warm-earth or macaron palette family), use them directly. When they don't align (cool-corporate primary), sketch-notes may be the wrong rendering — consult the compatibility matrix in `image-palettes/_index.md`.

- Cream paper background: keep close to the rendering's natural `#F5F0E8` even if `design_spec.secondary` differs slightly (the cream **is** part of sketch-notes)
- Black ink lines: keep at `#1A1A1A` or near-black — do not replace with the deck's primary
- Pastel color blocks: the deck's primary / secondary / accent HEX values, **rendered as soft pastel tints** rather than full saturation
- Single emphasis accent: the deck's accent HEX, used in 1-2 strong sparing places (a key arrow, an emphasized doodle)

---

## 4. Fewshot prompt snippets

**Snippet A — half-page educational concept, text_policy: embedded**

> Warm hand-drawn sketchnote on warm cream paper background. Black ink lines with slight wobble define three rounded rectangle info boxes arranged in a soft triangle layout. Each box is filled with a soft pastel block color: top box in light blue (a pastel tint of the deck's primary `#1E3A5F`), bottom-left box in mint, bottom-right box in lavender. Color fills don't completely reach the outlines (slight hand-painted overshoot). Hand-drawn wavy arrows connect the boxes — each arrow with a small inline hand-lettered English keyword like "leads to", "becomes", "supports" (no Chinese characters; ≤2 words per arrow). Each box contains one simple hand-drawn cartoon icon — a lightbulb, a plant, a gear — in black ink. Small doodle decorations (a few stars, dots, sparkles) sparingly around the composition. Composed as a 600×600 half-page block with 14% inner padding. Generous white space. Color values are rendering guidance only — do not display HEX codes or color names as text.