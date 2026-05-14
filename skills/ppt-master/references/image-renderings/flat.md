# Rendering: flat

Modern flat design with bolder geometric blocks than `vector-illustration`. More design-forward, slightly more decorative confidence. Used when a deck wants to feel "brand-aware" rather than purely utilitarian.

## Style paragraph (paste-ready, 90 words)

> Modern flat design illustration with bold geometric blocks and confident color zones. Forms are simplified to essential silhouettes — circles, rectangles, triangles, rounded squares. No outlines, or very thin uniform outlines as a deliberate accent. Color is applied as flat solid fills with deliberate juxtaposition (one block of saturated color against a large field of neutral). Subtle layered overlap creates flat depth without shadows. Composition has clear visual hierarchy — one dominant block, one secondary, one accent. Overall feel is contemporary, brand-aware, designed with intention — common in product launch and marketing decks.

## Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Often no outlines; when used, thin uniform stroke as accent only |
| Texture | None — flat color blocks |
| Depth | Through layered overlap and color contrast, not shadow |
| Material | Flat — color is brand identity, not material |
| Mood | Designed, intentional, slightly more expressive than vector-illustration |

## Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed background | 1280×720 | 16:9 | 12-15% |
| Half-page block | 600×500 | ~1.2 | 12% |
| Hero band | 1200×400 | 3:1 | 12% |
| Spot accent | 320×320 | 1:1 | 10% |

## Using the deck's HEX values

- Primary HEX: largest filled block, the dominant brand voice
- Secondary HEX: secondary block or large negative space
- Accent HEX: a single saturated callout block or geometric anchor
- Optional 4th neutral: dark text/anchor color (near-black or deck's text color)

## Fewshot prompt snippets

**Snippet A — half-page product visual, text_policy: none**

> Modern flat design illustration. One large rounded rectangle in primary deep teal `#0F766E` occupying the lower-left two-thirds of the canvas, slightly overlapped by a smaller circle in accent coral `#F97316` positioned upper-right. The remaining area is calm secondary cream `#FAFAF9`. No outlines, no shadows. A simple iconic symbol — a stylized package, rendered as a flat silhouette — sits within the teal block, white on teal. Composed as a 600×500 half-page block with 12% inner padding. NO text, letters, numbers, or labels anywhere. Color values are rendering guidance only — do not display HEX codes or color names as text.

**Snippet B — hero banner, text_policy: none**

> Modern flat design illustration banner. Three confident geometric blocks arranged across a wide canvas — a tall navy `#1E3A8A` rectangle on the left occupying the lower 70%, a circular orange `#F97316` accent center-right at mid-height, and a softer beige `#FEF3C7` rectangle filling the right third. Blocks subtly overlap, creating flat layered depth without shadows. The composition reads left-to-right with the orange circle as the focal anchor. Background is a single off-white `#FAFAFA`. Composed for a 1200×400 hero band with 12% inner padding. NO text, no labels. Color values are rendering guidance only.

## What to avoid

- Gradients within blocks (use `tech-neon` or `dark-cinematic` if a gradient is needed)
- Heavy outlines (switch to `vector-illustration`)
- Drop shadows simulating realism (flat is intentionally non-physical)
- More than 4 colors in one image

## When to switch away

- For 15+ page corporate decks needing utility over design flair → `vector-illustration`
- For tech architecture with depth → `3d-isometric`
- For educational warmth → `sketch-notes`
