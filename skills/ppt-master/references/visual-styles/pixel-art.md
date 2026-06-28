# Visual style: pixel-art

8-bit retro game — strict pixel grid, chunky blocky forms, a limited palette, no anti-aliasing. Playful and nostalgic. For gaming decks, retro-tech decks, nostalgic or game-flavored education / entertainment.

---

## 1. Shape & decoration

- Shape language: everything aligns to a visible pixel grid — blocky shapes, stepped edges, sharp transitions, no smooth curves; optional 1-pixel darker outlines for definition.
- Decoration: classic game framing — HUD bars, tile floors, sprite icons, chunky pixel borders. References NES / SNES / arcade composition.
- Whitespace: grid-disciplined; let blocks sit on clean tiled ground rather than crowd.

## 2. Typography character

- Pixel / bitmap display character for headlines; keep body in a clean legible face — full-pixel body type strains at reading length.

> Families are chosen at confirmation `g`; this style asks for a pixel / bitmap display *character* for titles, legible body alongside.

## 3. Using the deck's colors

- Colors used as palette slots: primary the dominant object, secondary the terrain / background, accent the highlights and markers; a darker shade of the primary serves as outline pixels.
- Flat blocks only — shading comes from palette layering (lighter top, darker bottom), never gradients.

> HEX values come from confirmation `e`; this style only governs the palette-slot, flat-pixel discipline — it names no colors.

## 4. Texture / elevation

- No texture beyond the pixel grid itself; strictly flat blocks. Depth reads from lighter-top / darker-bottom pixel shading, not drop shadows.

## 5. Paired image-rendering

`pixel-art` — 8-bit imagery on the same grid, sharing the retro-game aesthetic.

## 6. Illustration propensity

**core** — pixel sprites and blocky icons *are* the style; with no user steer, default to recommending a coherent spot-illustration family. Default *lean* only — heaviness and placement stay Strategist judgment, an explicit user request wins either way, and `image_usage: none` writes no illustration rows.
