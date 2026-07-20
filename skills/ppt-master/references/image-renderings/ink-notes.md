# Rendering: ink-notes

Pure white paper, black ink, sparse semantic color accents — the Mike Rohde sketchnote tradition. Sharper, more professional, more "manifesto" than `sketch-notes`. Used for methodology, Before-After essays, mindset-shift narratives, technical manifestos, professional visual-note style.

## 1. Style paragraph (paste-ready, 105 words)

> Professional hand-drawn visual-note style on a clean paper field. All line work is anchored by the deck's body-text color with slight wobble — confident, intentional, with the human-hand quality of a thoughtful whiteboard session. Hand-lettered titles appear bold and slightly oversized (when text policy allows). Color is intentionally sparse: line work dominates ~85% of the visible content, while one or two semantic accents derive from the deck's accent families and cover less than 10% combined. Backgrounds and shape fills remain mostly empty. Small doodle decorations — stars, dashes, dots — are minimal. Overall feel is professional, considered, manifesto-quality.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Black ink with slight wobble; confident medium weight |
| Texture | Pure white background; no paper grain |
| Depth | Flat |
| Material | Pen-on-paper |
| Mood | Professional, considered, manifesto |

## 3. Using the deck's HEX values

ink-notes has a near-fixed material language: **dark ink + light background + 1-2 semantic accents**. It never overrides `design_spec.colors`; offer it only when the confirmed roles can support that contrast:

- Background: use the deck's `background` / `secondary_bg`
- Lines and text: use the deck's `body_text`
- Semantic accents: derive from the deck's `accent` / `secondary_accent` roles and preserve their established meaning; contextual ink/paper tonal variants are allowed

This makes ink-notes the rendering most likely to fight a deck's identity. Offer it only when the background / text / accent anchors can support the treatment; do not substitute a stock coral / teal / lavender palette merely because the rendering traditionally uses one.

---

## 4. Fewshot prompt snippets

**Snippet A — Before/After methodology (comparison type), text_policy: embedded**

> Professional hand-drawn visual-note style on the deck's locked background color. Composition is a Before/After split — vertical hand-drawn divider down the center. Both sides use the locked body-text color as ink line work with slight wobble. Left side ("Before") shows a simple stick-figure character with a frustrated posture, a speech bubble with hand-lettered "OLD WAY" in English block caps, and a small list of three hand-drawn dashes with brief 1-2 word annotations (e.g. "manual", "slow", "fragile"). Right side ("After") shows a confident stick-figure character with a clean checkmark above, hand-lettered "NEW WAY" in English block caps, and three checkbox-style annotations (e.g. "automated", "fast", "reliable"). A curved hand-drawn "mindset shift" arrow bridges left to right with a small hand-lettered label "the shift". Sparse semantic color: the locked accent marks the left-side pain points and the locked secondary accent marks the right-side positives. Total accent area stays under 10% of canvas. All hand-lettered text is short keywords. Composed as a 1200×500 hero banner with 14% inner padding.
