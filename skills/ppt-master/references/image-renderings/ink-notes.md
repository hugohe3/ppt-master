# Rendering: ink-notes

Pure white paper, black ink, sparse semantic color accents — the Mike Rohde sketchnote tradition. Sharper, more professional, more "manifesto" than `sketch-notes`. Used for methodology, Before-After essays, mindset-shift narratives, technical manifestos, professional visual-note style.

## 1. Style paragraph (paste-ready, 105 words)

> Professional hand-drawn visual-note style on pure white paper. All line work is black ink with slight wobble — confident, intentional, with the human-hand quality of a thoughtful whiteboard session. Hand-lettered titles appear bold and slightly oversized (when text policy allows). Color is intentionally sparse — black ink dominates ~85% of the visible content, with one or two semantic accent colors (coral red for risk/emphasis, muted teal for positive/solution, dusty lavender for neutral categories) covering less than 10% of canvas combined. Backgrounds and shape fills are mostly empty white. Small doodle decorations — stars, dashes, dots — are minimal. Overall feel is professional, considered, manifesto-quality.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Black ink with slight wobble; confident medium weight |
| Texture | Pure white background; no paper grain |
| Depth | Flat |
| Material | Pen-on-paper |
| Mood | Professional, considered, manifesto |

---

## 3. Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page methodology block | 600×600 | 1:1 | 14% |
| Hero manifesto banner | 1200×500 | 2.4:1 | 14% |
| Before/After comparison | 1200×500 | 2.4:1 | 14% |
| Spot diagram | 500×500 | 1:1 | 12% |

---

## 4. Using the deck's HEX values

ink-notes has a near-fixed visual language: **black ink + white background + 1-2 semantic accents**. This palette tendency may override `design_spec.colors`:

- Background: pure white `#FFFFFF` (do not replace with the deck's secondary unless it's already near-white)
- Lines and text: near-black `#1A1A1A` (do not replace with the deck's primary)
- Semantic accents: ink-notes traditionally uses coral red, muted teal, dusty lavender. The deck's `accent` HEX can serve as the emphasis color, but consider whether it carries the right semantic weight (red=risk, teal=positive, gold=highlight)

This makes ink-notes **the rendering most likely to deviate from the deck's HEX**. Reaffirm in the prompt that the ink-notes natural palette is intentional and the deck's primary HEX is reserved for the accent role.

---

## 5. Fewshot prompt snippets

**Snippet A — Before/After methodology (comparison type), text_policy: embedded**

> Professional hand-drawn visual-note style on pure white background. Composition is a Before/After split — vertical hand-drawn divider down the center. Both sides use black ink line work with slight wobble. Left side ("Before") shows a simple stick-figure character with a frustrated posture, a speech bubble with hand-lettered "OLD WAY" in English block caps, and a small list of three hand-drawn dashes with brief 1-2 word annotations (e.g. "manual", "slow", "fragile"). Right side ("After") shows a confident stick-figure character with a clean checkmark above, hand-lettered "NEW WAY" in English block caps, and three checkbox-style annotations (e.g. "automated", "fast", "reliable"). A curved hand-drawn "mindset shift" arrow bridges left to right with a small hand-lettered label "the shift". Sparse semantic color: coral red `#E8655A` (the deck's accent) appears only on the left side's pain points; muted teal `#5FA8A8` appears only on the right side's positives. Total color accent area under 10% of canvas. NO Chinese characters — all hand-lettered text is short English keywords. Composed as a 1200×500 hero banner with 14% inner padding.
