# Visual style: brutalist

Brutalist editorial newspaper. Wall-to-wall small type, irregular column widths, heavy rule lines, raw structure on show. Reportorial and information-dense — for annual reviews, research digests, manifestos, editorial decks that flaunt density.

---

## 1. Shape & decoration

- Shape language: hard rectangles and ruled boxes; thick black borders / cell frames; visible column dividers. Corner radius `rx="0"` — never rounded.
- Decoration: the grid itself is the decoration — masthead bars, rule lines, boxed pull-quotes, halftone fills. No gradients, no soft cards, no shadows.
- Whitespace: tight and deliberate — narrow margins, dense columns, a newspaper's packed rhythm. Density is the point; one or two breathing zones per page keep it readable, not airy.
- Irregular multi-column layout (mixed column widths) over a uniform grid; asymmetry is intentional.

## 2. Typography character

- Three-family hard contrast: a heavy display sans for headlines (poster-black weight), a serif for column body, monospace for figures / data — the collision is the look.
- Small body size, high density; strong size jump between masthead headline and body. Flush-left columns, tight leading.

> Families are chosen at confirmation `g`; this style asks for a display-black × serif-body × monospace-data *character*.

## 3. Using the deck's colors

- Near-monochrome: ink-dark structure and type on a paper-light field; a single spot accent appears rarely (a masthead rule, one key figure, a stamp) — a few percent of canvas at most.
- Color as punctuation, not fill. No color blocking, no gradients — the accent earns attention by scarcity.

> HEX values come from confirmation `e`; this style only governs how sparingly the accent is used — it names no colors.

## 4. Texture / elevation

- Strictly flat — no drop shadows, no elevation. Depth comes from rule weight and halftone texture, not material. Optional paper-grain / halftone `<pattern>` for a printed feel.

## 5. Paired image-rendering

`screen-print` or `editorial` — halftone monochrome imagery that sits inside the newsprint aesthetic.

## 6. Illustration propensity

**supportive** — raw halftone cuts fit the newsprint density, but structure leads; use them sparingly, only where a page needs a visual jolt. With no user steer this is the default lean; an explicit user request wins either way, and `image_usage: none` writes no illustration rows.
