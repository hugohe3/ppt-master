# Native Diagram Demo (数字化能力成熟度)

A minimal 2-page deck demonstrating the **native-diagram** capability end-to-end:
the per-page **vehicle decision**, a **native diagram** spliced in and **recolored**
to the deck palette with its text replaced by the deck's own content, an
**AI-generated cover image**, all exported to a natively-editable `.pptx`.

## What each page shows

| Page | Treatment (vehicle stack) | Demonstrates |
|------|---------------------------|--------------|
| **01 Cover** | `image:cover_bg.png (hero_page)` + SVG title overlay | an AI image as the page backdrop with SVG text on top |
| **02 Maturity model** | `native:solid3d_bluegreen_012` (a 3-tier pyramid) | a native diagram placed via `data-native-diagram`, **recolored** green/blue → navy/gold via `data-recolor`, and **filled with this deck's content** via `data-text` (text slots) — not the source pack's labels |

## How it was built (end-to-end, Claude + Codex)

- **Claude** authored the SVG pages and made the per-page vehicle decision
  (cover = image; maturity page = native diagram).
- **Codex** generated `images/cover_bg.png` (a navy/gold tech backdrop).
- The maturity page's `svg_output/02_maturity.svg` reserves the figure with:
  ```xml
  <rect data-native-diagram="solid3d_bluegreen_012"
        data-recolor="558C5A=1E3A5F,122B87=D4AF37"
        data-text='{"0":"数字化能力","1":"成熟度模型","13":"L1 基础数字化", ...}'
        x="120" y="125" width="1040" height="575" fill="none"/>
  ```
  At export, the converter splices the component's native DrawingML in (scaled to
  the rect), recolors it, and replaces the text runs — see
  [`references/native-diagrams.md`](../../skills/ppt-master/references/native-diagrams.md).

## Rebuild

```bash
# requires Python 3.10+ with python-pptx / lxml / pillow
python3 skills/ppt-master/scripts/svg_to_pptx.py examples/ppt169_native_diagram_demo --no-compat
```

> Note on the slot fill: text slots are indexed in **document order, not visual
> reading order**, so map content by each slot's original text (see
> `meta.text_slots`) and verify the render. (Here the three tiers first came out
> L1 / L3 / L2 top-to-bottom; swapping two slot ids fixed it to L3 / L2 / L1.)
