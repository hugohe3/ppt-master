# AI Smart-Glasses Launch — Design Spec

> Fictional demo product (**VEO One**). Original placeholder content for a light
> keynote product-launch style. See `templates/design_spec_reference.md` for the
> full §I–XI structure.

## III. Visual Theme
- **Style**: bright / airy "Apple-keynote" product launch — white studio, product hero
  on a pedestal, big type, generous whitespace, single calm accent. NOT dark, NOT neon.
- **Color Scheme**: ink `#0C1B33` · ink-2 `#13315C` · body `#4A5568` · accent `#2E6BE6`
  (tech blue) · accent-deep `#1B47B0` · accent-tint `#E8F0FE` · page `#F6F9FD` / `#FFFFFF`
  · hairline `#E2E8F0` / `#EDF2F8` · muted `#9AA8BD`
- **Icons**: `phosphor-duotone`, accent-blue.

## IV. Typography
- font_family: "Microsoft YaHei", Arial, sans-serif (display numerals: Arial)
- Display 74–92 (cover) · H1 40–46 · H2 22–28 · body 15–18 · eyebrow 12/600/+1.6 · caption 13

## V. Layout system
- Margin 80px; signature bar = 96×6 `gradAccent` under each section title.
- Two page modes: **image-as-canvas** (full-bleed hero + leftScrim + SVG text) and
  **light vector** (white/`#F6F9FD`, soft `cardFloat` cards, duotone icons).

## IX. Content Outline (per-page Treatment)
- 01 Cover · `image:hero_cover.png (hero_page)` + SVG title
- 02 Vision · `image:hero_wearing.png (hero_page)` + SVG statement
- 03 Design · `image:hero_design.png (hero_page)` + SVG spec cards
- 04 Capability overview · free-svg (3 pillars: 看见 / 听懂 / 提示)
- 05 Capture · free-svg (before/after)
- 06 Assistant · free-svg (chat mock)
- 07 Translate · free-svg (bidirectional flow)
- 08 AR info · `image:hero_ar.png (hero_page)` + SVG
- 09 Audio · free-svg (3 cards)
- 10 Hardware · free-svg (6-cell spec grid)
- 11 Capability model · `native:solid3d_bluegreen_012` + SVG title
- 12 Scenarios · free-svg (4 cards)
- 13 Ecosystem · free-svg (radial)
- 14 Battery · `image:hero_case.png (hero_page)` + SVG stats
- 15 Why now · free-svg (3 reasons)
- 16 Pricing · free-svg (2 editions)
- 17 Closing · `image:hero_lifestyle.png (hero_page)` + SVG

## VII. Visualization Reference List
| Page | Template | Path |
|------|----------|------|
| P11 | solid3d_bluegreen_012 | `templates/native_diagrams/solid3d_bluegreen_012` |

## VIII. Image Resource List
| Filename | Purpose | Acquire Via | page_role |
|----------|---------|-------------|-----------|
| hero_cover.png | Cover hero (glasses on pedestal) | ai (Codex) | hero_page |
| hero_wearing.png | Vision page | ai (Codex) | hero_page |
| hero_design.png | Design page | ai (Codex) | hero_page |
| hero_ar.png | AR info (POV) | ai (Codex) | hero_page |
| hero_case.png | Battery / case | ai (Codex) | hero_page |
| hero_lifestyle.png | Closing | ai (Codex) | hero_page |
