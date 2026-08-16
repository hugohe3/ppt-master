# Visual style: glassmorphism

Frosted-glass SaaS — translucent layered panels, flowing gradient light, floating depth on a dark field. Future-tech, weightless, premium. For modern SaaS, fintech, health-tech, product launches, AI demos.

---

## 1. Shape & decoration

- Shape language: visibly rounded translucent glass panels (low fill-opacity over the dark field) with bright hairline edges; layered, floating cards that imply blur and frost.
- Composition geometry: one hero glass panel set off-axis over a radial bloom; overlapping translucent discs building the focal cluster; a large glass ring encircling the key metric; panels stepped in depth to imply sequence; a diagonal light beam crossing the dark field.
- Decoration: soft radial light blooms in the background; thin luminous edge highlights along panels; restrained — the glass material is the decoration, not added ornament. Realize the radial bloom / glow halo as a `<circle>` / `<ellipse>` with a `<radialGradient>` fill, never a `rect rx=w/2` standing in for it.
- Whitespace: dark negative space reads as depth; let panels float on it with room to breathe.

## 2. Typography character

- Clean modern sans; regular with selective bold; airy. Exact Light/Black requires a user-confirmed installed face. Headlines can carry a luminous gradient on the dark field.

> Families are chosen at confirmation `g`; this style asks for a clean, modern, airy sans *character*.

## 3. Using the deck's colors

- Dark field; the deck's colors read as luminous gradients flowing across panels and titles, low-opacity glass tints, and a subordinate neon accent. Color behaves like light through glass, not flat fill.
- Depth and hierarchy come from how brightly the glass glows, not from heavy saturation.

> HEX values come from confirmation `e`; this style only governs the translucent-glass, luminous-gradient discipline — it names no colors.

## 4. Texture / elevation

- Depth via translucency, layering, bright edge highlights, and soft background glow — not hard drop shadows. Smooth multi-stop gradients are intrinsic here (the one style where generous gradient use is on-brand); keep them luminous, not muddy.

## 5. Paired image-rendering

`glassmorphism` — frosted translucent panels / soft-gradient imagery matching the glass surfaces.

## 6. Illustration propensity

**sparse** — translucent panels, gradient light, and floating depth lead. Use illustration selectively within, behind, beside, or across the glass layers when it improves composition without obscuring their hierarchy. An explicit user request wins either way, and `image_usage: none` writes no illustration rows.
