# Type: typography

A large headline, number, or single word as the primary visual. The text itself is the image. Used for big-stat pages ("$2.3M"), slogan pages ("MOVE FAST"), chapter openers, hero quotes, signature numbers in consulting decks.

> **What typography means inside a PPT block**: the image's primary content is a piece of text rendered as art. Unlike all other types where text is forbidden or minimal, typography **requires** text — and that text is the visual anchor.

## 1. Composition skeleton

```
   ┌────────────────────────────────────┐
   │                                     │
   │          ┌─────────────┐            │
   │          │             │            │
   │          │    $2.3M    │  ← The     │
   │          │             │    text    │
   │          └─────────────┘    IS the  │
   │                              image  │
   │     small supporting visual         │
   │                                     │
   └────────────────────────────────────┘
```

| LAYOUT | Large text element occupying 40-60% of canvas height, centered or rule-of-thirds positioned |
| ELEMENTS | The text + minimal supporting visual context (small icon, geometric anchor, accent line). Supporting elements <25% of weight |
| NEGATIVE SPACE | Generous around the text — at least 20% padding |
| TEXT CHARACTER | Rendered with intention — confident weight, deliberate spacing, may have texture/style matching deck rendering |

---

## 2. Critical: text accuracy

Image models have **variable accuracy on text rendering**:

- **English short text (1-5 characters / one short word)**: most modern models render correctly most of the time
- **English longer text (sentences)**: high failure rate (typos, glyph errors)
- **Numbers / symbols**: variable, often fail at typography scale
- **Chinese / Japanese / Korean characters**: most models fail consistently

**For typography type, prefer**:
- A short English word (1-2 words max)
- A simple number ("100", "5x", "$50M") — verify after generation
- A simple symbol or letter ("∞", "?", "A")

**Avoid for typography type**:
- Long quotes / sentences (use SVG text instead)
- Chinese/CJK characters (model failure expected)
- Complex symbols or composite text

When the desired headline is long or CJK: switch to `background` type and overlay the headline as SVG text.

## 3. Text-policy variants

### `text_policy: embedded`

typography type is built around in-image text — the headline word, number, or quote is the visual. `text_policy: embedded` is the natural choice.

Sample fragment:

> The image's central content is the hand-lettered (or appropriately styled) word "GROWTH" — rendered as a large confident headline occupying about 50% of the canvas height, in {font family echoing deck's body typography}. Text is in English only (most models render CJK characters poorly). No other text or labels in the image — just the single headline word.

**Font family in prompt**: name the family so the lettering coheres with the deck's SVG typography. Read `spec_lock.md deck_typography` if present; otherwise infer from rendering (vector-illustration / flat → clean sans-serif; editorial → serif; sketch-notes / ink-notes → hand-written; 3d-isometric / digital-dashboard → geometric display).

### `text_policy: none`

If the page wants no text inside the image, the type is probably `background` or `hero`, not `typography`.

---

## 4. Fewshot prompt snippets

**Snippet A — ink-notes + mono-ink big-number stat, text_policy: embedded, 800×500**

> Professional hand-drawn visual-note style on pure white background. The image's central content is the hand-lettered number "100x" — rendered in bold confident ink strokes occupying about 50% of the canvas height, centered with deliberate slight wobble characteristic of hand-lettering. Text is in English/Latin characters only. Beneath the number, a thin hand-drawn underline in ink. To the side of the number, one small hand-drawn doodle decoration — a star or upward arrow — adds visual rhythm. Accent coral `#E8655A` (from the deck's accent) appears only as a tiny emphasis dot above the number's exclamation, totaling under 4% of canvas. Background is pure white `#FFFFFF`. Composed as an 800×500 typography block with 20% padding around the number. No other text or labels in the image — just the "100x" headline and the small doodle.