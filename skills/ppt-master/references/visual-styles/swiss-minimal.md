# Visual style: swiss-minimal

Strict Swiss-grid discipline. Modular grid, sharp geometry, aggressive whitespace, near-zero decoration. The most restrained style — for high-end consulting, architecture, design firms, type-led decks.

---

## 1. Shape & decoration

- Shape language: sharp rectangles, true circles, single-weight rules. Corner radius `rx="0"` by default; if rounding at all, ≤4.
- Decoration: none. No gradient fills, no decorative blocks, no badges — structure carries the page.
- Whitespace: vast and deliberate; negative space carries as much weight as content. Wide margins, generous gutters.
- Layout snaps to a visible or implied modular grid; rigorous column / row alignment.

## 2. Typography character

- Sans-serif, single family; weight contrast (e.g. 900 / 300) over family contrast. Tight, rigorous spacing.
- Strong size hierarchy — large headlines, small precise body. Left-aligned, flush.

> Family is chosen at confirmation `g` by subject fit — this style asks for a grotesque / neo-grotesque *character*, not a specific font.

## 3. Using the deck's colors

- One color dominates a deliberate grid zone; the field stays near-white; the accent appears at a single point — never more than a few percent of canvas.
- Color as conceptual zone, not decoration. No gradients.

> HEX values come from confirmation `e`; this style only governs how sparingly they are applied — it names no colors.

## 4. Texture / elevation

- Strictly flat. No shadows, no depth, no material — 2D conceptual planes only.

## 5. Paired image-rendering

`minimalist-swiss` — lock it for AI images so illustrations share the grid-austere aesthetic.

## 6. Illustration propensity

**sparse** — the whitespace and grid *are* the design; decorative spots compete with that restraint, so with no user steer, default to none. If the user explicitly asks, use them — but stay austere: very few, very light, never crowding the negative space. `image_usage: none` writes no illustration rows.
