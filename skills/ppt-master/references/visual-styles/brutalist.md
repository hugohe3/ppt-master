# Visual style: brutalist

Brutalist editorial newspaper. Wall-to-wall small type, irregular column widths, heavy rule lines, raw structure on show. Reportorial and information-dense — for annual reviews, research digests, manifestos, editorial decks that flaunt density.

---

## 1. Shape & decoration

- Shape language: favor hard-edged native contours, ruled boxes, thick black borders / cell frames, visible column dividers, brackets, block arrows, and raw stamps. Exact native shapes remain eligible when their semantic job fits; treat them with the same sharp print discipline. Corner radius `rx="0"` — never rounded.
- Composition geometry: a masthead numeral or headline set so large it crosses column rules; one grid cell inverted to solid ink (light type on dark) as the focal cell; full-bleed rule bars slicing sections; a single rotated stamp-box breaking the grid at one deliberate point.
- Decoration: the grid itself is the decoration — masthead bars, rule lines, boxed pull-quotes, halftone fills. No gradients, no soft cards, no shadows.
- Whitespace: tight and deliberate — narrow margins, dense columns, a newspaper's packed rhythm. Density is the point; retain enough breathing room for hierarchy and readability without imposing a per-page count.
- Irregular multi-column layout (mixed column widths) over a uniform grid; asymmetry is intentional.

## 2. Typography character

- Strong role contrast: a heavy display sans for headlines (poster-black weight), a serif character for column body, and monospace for figures / data can create the collision this style needs without imposing a family count.
- Small body size, high density; strong size jump between masthead headline and body. Flush-left columns, tight leading.

> Families are chosen at confirmation `g`; this style asks for a display-black × serif-body × monospace-data *character*. This governs editable native text; decorative-lettering eligibility remains a separate carrier decision.

## 3. Using the deck's colors

- Near-monochrome: ink-dark structure and type on a paper-light field; use a localized spot accent as punctuation, such as a masthead rule, key figure, or stamp.
- Color as punctuation, not fill. No color blocking, no gradients — the accent earns attention by scarcity.

> HEX values come from confirmation `e`; this style only governs how sparingly the accent is used — it names no colors.

## 4. Texture / elevation

- Strictly flat — no drop shadows, no elevation. Depth comes from rule weight and halftone texture, not material. Optional paper-grain / halftone `<pattern>` for a printed feel.

## 5. Paired image-rendering

`screen-print` or `editorial` — halftone monochrome imagery that sits inside the newsprint aesthetic.

## 6. Illustration propensity

**supportive** — when illustration is selected, raw halftone cuts and illustration elements can anchor or disrupt the newsprint composition while structure remains legible. Role, scale, reuse, and placement stay Strategist judgment; an explicit user request wins either way, and `image_usage: none` writes no illustration rows.
