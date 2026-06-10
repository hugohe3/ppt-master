# AI Smart-Glasses Launch (VEO One)

A 17-page, light **product-launch keynote** deck — bright/airy "Apple-keynote" aesthetic
(white studio, product hero on a pedestal, big type, generous whitespace, a single
calm tech-blue accent). It demonstrates an end-to-end deck built with **Claude + Codex**:
hand-authored editable-SVG pages, AI-generated product photography as page heroes, and
a **native diagram** spliced in on the capability page — all exported to a
natively-editable `.pptx`.

> **VEO One is a fictional demo product.** All product names, specs, prices and copy are
> original placeholder content authored for this style/layout example — it is not a real
> product and does not replicate any third-party deck.

## What it shows

| # | Page | Treatment | Demonstrates |
|---|------|-----------|--------------|
| 01 | Cover | `image:hero_cover.png` + SVG overlay | image-as-canvas hero with editable title |
| 02 | Vision | `image:hero_wearing.png` + SVG | keynote statement page |
| 03 | Design | `image:hero_design.png` + SVG | hero + floating spec cards |
| 04 | Capability | free-SVG | 3-pillar light vector layout (duotone icons) |
| 05 | Capture | free-SVG | before/after contrast |
| 06 | Assistant | free-SVG | chat-mock conversation |
| 07 | Translate | free-SVG | bidirectional flow diagram |
| 08 | AR info | `image:hero_ar.png` + SVG | text over a busy photo (bottom scrim) |
| 09 | Audio | free-SVG | feature cards + waveform motif |
| 10 | Hardware | free-SVG | 6-cell spec grid |
| 11 | Capability model | `native:solid3d_bluegreen_012` | a **native diagram**, recolored to the deck's blue and filled with this deck's tier content via `data-recolor` / `data-text` |
| 12 | Scenarios | free-SVG | 4 scenario cards |
| 13 | Ecosystem | free-SVG | center-node radial |
| 14 | Battery | `image:hero_case.png` + SVG | hero + stat callouts |
| 15 | Why now | free-SVG | 3 reasons + takeaway bar |
| 16 | Pricing | free-SVG | two pricing editions |
| 17 | Closing | `image:hero_lifestyle.png` + SVG | bookend cover |

## How it was built

- **Claude** authored all 17 SVG pages, made the per-page vehicle decision (hero image vs.
  light vector vs. native diagram), and chose the palette / type system.
- **Codex** generated the six product images in `images/` with its built-in image tool
  (bright keynote product photography of the fictional glasses; no text/logos baked in).
- Page 11 reserves the figure with `data-native-diagram="solid3d_bluegreen_012"` +
  `data-recolor` + `data-text`; at export the converter splices the component's native
  DrawingML in, recolors it to the deck's blue, and replaces the text runs.

## Rebuild

```bash
# requires Python 3.10+ with python-pptx / lxml / pillow
python3 skills/ppt-master/scripts/svg_to_pptx.py examples/ppt169_ai_glasses_launch --no-compat
```

Output: `exports/ppt169_ai_glasses_launch.pptx` (17 natively-editable slides).
