# Type: typography

A large headline, number, or single word as the primary visual. The text itself is the image. Used for big-stat pages ("$2.3M"), slogan pages ("MOVE FAST"), chapter openers, hero quotes, signature numbers in consulting decks.

> **What typography means inside a PPT block**: the image's primary content is a piece of text rendered as art. Unlike all other types where text is forbidden or minimal, typography **requires** text — and that text is the visual anchor.

## Composition skeleton

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

## Critical: text accuracy

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

## Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed big-stat page | 1280×720 | 16:9 | 20% padding around text |
| Half-page stat block | 600×600 | 1:1 | 20% |
| Hero slogan banner | 1200×500 | 2.4:1 | 18% |
| Square emphasis | 700×700 | 1:1 | 20% |

## Text-policy variants

### `text_policy: embedded` (required)

typography type is the **one type where embedded text is the entire point**. Always use `text_policy: embedded`.

Sample fragment:

> The image's central content is the hand-lettered (or appropriately styled) word "GROWTH" — rendered as a large confident headline occupying about 50% of the canvas height. Text is in English only (most models render CJK characters poorly). No other text or labels in the image — just the single headline word.

### `text_policy: none` (essentially never)

If text_policy is none, this isn't typography — switch to `background` or `hero`.

## Fewshot prompt snippets

**Snippet A — ink-notes + mono-ink big-number stat, text_policy: embedded, 800×500**

> Professional hand-drawn visual-note style on pure white background. The image's central content is the hand-lettered number "100x" — rendered in bold confident ink strokes occupying about 50% of the canvas height, centered with deliberate slight wobble characteristic of hand-lettering. Text is in English/Latin characters only. Beneath the number, a thin hand-drawn underline in ink. To the side of the number, one small hand-drawn doodle decoration — a star or upward arrow — adds visual rhythm. Accent coral `#E8655A` (from the deck's accent) appears only as a tiny emphasis dot above the number's exclamation, totaling under 4% of canvas. Background is pure white `#FFFFFF`. Composed as an 800×500 typography block with 20% padding around the number. No other text or labels in the image — just the "100x" headline and the small doodle.

**Snippet B — vector-illustration + cool-corporate slogan banner, text_policy: embedded, 1200×500**

> Clean flat vector illustration banner. The image's central content is the bold word "SCALE" — rendered as a large geometric block-letter headline in primary deep navy `#1E3A5F`, occupying about 45% of the canvas height, centered. Letters have crisp vector edges (sans-serif geometric character). Beneath the word, a thin accent gold `#D4AF37` horizontal rule (about 60% of word width). Background is calm secondary light gray `#F8F9FA`. No supporting visuals beyond the rule. Composed as a 1200×500 hero typography banner with 18% padding. Text is English only (5 characters). Color values are rendering guidance — do not paint HEX codes or color names as additional text.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Typo / garbled letters | Word too long, or model unreliable | Shorten to 1-2 short words; verify after generation |
| Multiple text elements | "Just one headline" not specified | Reaffirm "only the single headline word — no additional text, no labels, no captions" |
| Chinese characters garbled | CJK requested | Switch to English keyword or use `background` + SVG text overlay |
| Text too small | Size rule omitted | Restate "headline text occupies 40-60% of canvas height" |
| Decorative elements distract | Supporting visuals too prominent | Reaffirm "supporting visuals minimal, under 25% of canvas weight" |

## When to switch away from typography

- If text is long / CJK → use `background` type + SVG text overlay
- If image is a dominant subject (not text) → `hero`
- If pure atmosphere → `background`
- If multiple labeled zones → `infographic`
