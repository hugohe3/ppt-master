# Rendering: watercolor

Painterly soft edges, color bleeding, organic flow. The most "artistic" rendering — used for lifestyle, travel, brand story, personal narrative, creative content where mood matters more than data clarity.

## Style paragraph (paste-ready, 100 words)

> Watercolor painting style with soft painterly edges and natural color bleeding. Forms emerge from washes of pigment rather than outlines — sometimes a subject is suggested by where the wash darkens, not by a line. Color pools and bleeds at edges, with characteristic "wet-on-wet" zones where one color transitions into another. Composition feels organic and intentional — not loose like a sketch, but flowing. Negative space is part of the artwork (untouched paper). Optional very subtle pencil lines suggest underlying structure without dominating. Overall feel is calm, contemplative, artistic — well suited to narrative pages and atmosphere-setting content.

## Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Minimal — forms defined by color washes, not outlines |
| Texture | Paper grain at 12-18% visible, characteristic wash bleeding at edges |
| Depth | Achieved through color saturation gradient — saturated foreground, paler background |
| Material | Watercolor + cold-press paper |
| Mood | Calm, contemplative, artistic |

## Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page atmospheric visual | 600×800 | 3:4 | 10% (watercolor often fills the frame) |
| Hero narrative banner | 1200×600 | 2:1 | 10% |
| Square mood piece | 700×700 | 1:1 | 12% |

## Using the deck's HEX values

watercolor uses HEX values as **wash pigments**, not flat fills:

- Primary HEX: dominant wash zone, with natural saturation gradient
- Secondary HEX: background wash or untouched paper field
- Accent HEX: a small concentrated pigment zone where saturation pools

## Fewshot prompt snippets

**Snippet A — half-page narrative scene, text_policy: none**

> Watercolor painting style. A soft mountain landscape suggested by overlapping color washes — distant peaks in pale primary teal `#0F766E` bleeding into the upper third, midground hills in slightly more saturated teal with natural wet-on-wet color pooling, foreground in warm accent terracotta `#C2410C` suggesting a path or warm earth. Untouched paper at the very top creates a calm sky. No outlines defining the forms — they emerge from where the pigment darkens. Subtle paper grain texture at 15% opacity across the painting. Composed as a 600×800 half-page block with 10% inner padding. Atmospheric and contemplative. NO text, no labels anywhere. Color values are rendering guidance only.

**Snippet B — hero brand-story banner, text_policy: none**

> Watercolor painting style hero banner. Soft horizontal composition with pale washes flowing across the canvas. Left third in warm cream `#FEF3C7` (mostly untouched paper), center area in deeper amber `#D97706` with natural color pooling and bleeding edges, right third transitioning into deeper rust `#9A3412` accent. A few suggested forms — perhaps a tree silhouette emerging from the wash, perhaps a soft figure walking — defined entirely by color contrast, no outlines. Subtle pencil under-marks barely visible suggest underlying composition. Paper grain at 15% opacity. Composed for a 1200×600 hero band with 10% inner padding. NO text or labels. Color values are rendering guidance only.

## What to avoid

- Hard outlines (defeats the watercolor identity)
- Saturated solid fills (watercolor is washes)
- Digital-feeling sharp transitions
- Over-detailed subjects (watercolor suggests rather than describes)
- More than 3-4 colors in one painting

## When to switch away

- For golden-hour photographic warmth → `warm-scene`
- For corporate / technical visuals → `vector-illustration`, `flat`, `editorial`
- For storybook character work → `fantasy-animation`
