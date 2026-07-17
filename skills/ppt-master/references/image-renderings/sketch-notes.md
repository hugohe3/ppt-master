# Rendering: sketch-notes

Warm cream paper with black hand-drawn lines and soft pastel color blocks. The most "approachable" rendering — used in education, training, onboarding, science communication, knowledge content where warmth and friendliness matter more than corporate precision.

## 1. Style paragraph (paste-ready, 110 words)

> Warm hand-drawn sketchnote style on the deck's light background role. All lines use the locked body-text color with deliberate slight wobble, never perfectly straight, giving the human-hand quality of a thoughtful teacher's whiteboard. Soft color blocks derive only from the locked primary, secondary-accent, and accent roles and fill rounded shapes without quite reaching their outlines (a deliberate "hand-painted overshoot" feel). Simple cartoon icons and small doodle decorations (stars, sparkles, dots, underlines) appear sparingly to add warmth. Composition is airy and well organized, with generous whitespace. Overall feel is instructional, friendly, and approachable.

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

sketch-notes has a strong built-in tendency toward warm paper, dark ink, and soft color blocks. Offer it only when the locked deck roles can carry that tendency; otherwise choose another rendering in Stage 2. Once confirmed, use only the locked deck colors.

- Paper background: use the deck's `background` or `secondary_bg`; do not introduce a natural cream outside the lock
- Ink lines: use the deck's `body_text` role
- Color blocks: use the deck's primary / secondary-accent / accent roles with restrained coverage; do not invent pastel HEX
- Single emphasis accent: the deck's accent HEX, used in 1-2 strong sparing places (a key arrow, an emphasized doodle)

---

## 4. Fewshot prompt snippets

**Snippet A — half-page educational concept, text_policy: embedded**

> Warm hand-drawn sketchnote on the deck's locked background color. Lines use the locked body-text color with slight wobble and define three rounded rectangle info boxes arranged in a soft triangle. The top box uses the locked primary, the bottom-left uses the locked secondary accent, and the bottom-right uses the locked accent, each with restrained coverage and no invented tint. Color fills do not completely reach their outlines (slight hand-painted overshoot). Hand-drawn wavy arrows connect the boxes, each with a brief inline keyword such as "leads to", "becomes", or "supports" (≤2 words). Each box contains one simple hand-drawn cartoon icon — a lightbulb, a plant, a gear. Small doodle decorations appear sparingly. Composed as a 600×600 half-page block with 14% inner padding and generous whitespace.
