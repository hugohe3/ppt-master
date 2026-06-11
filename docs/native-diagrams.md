# Native Diagrams

A **native diagram** is a pre-designed, fully-editable DrawingML figure that is
*spliced into* a deck at SVG→PPTX conversion time — a first-class peer of
`<use data-icon>` and `<image>`. Unlike a `templates/charts/` SVG (which the
Executor redraws from scratch), a native diagram arrives pixel-faithful and stays
natively editable in PowerPoint, at near-zero authoring cost: the Executor writes a
single placeholder rect, and the converter splices in the named component, scaled
to the rect, recolored to the deck palette, and re-texted to the deck's content.

This page is the contributor-facing overview. The authoring contract the Executor
follows lives in
[`references/native-diagrams.md`](../skills/ppt-master/references/native-diagrams.md).

## How it works

1. **Extract** — [`scripts/extract_diagram.py`](../skills/ppt-master/scripts/extract_diagram.py)
   lifts one slide's shapes into a self-contained component under
   `templates/native_diagrams/<key>/` (`shapes.xml.gz` + `meta.json`). Theme
   colors are flattened to `srgbClr` and theme fonts to concrete typefaces, so the
   figure renders identically in any deck. `meta.json` records every text run as a
   **slot** plus a CJK-aware `slot_spec` (how much text fits, what kind).
2. **Place** — the Executor writes a placeholder rect:
   ```xml
   <rect data-native-diagram="<key>"
         data-recolor="558C5A=<deck primary>,122B87=<deck accent>"
         data-font="<deck font>"
         data-text='{"0":"<title>","1":"<label>", ...}'
         x=".." y=".." width=".." height=".." fill="none"/>
   ```
3. **Resolve** —
   [`svg_to_pptx/native_diagram_resolver.py`](../skills/ppt-master/scripts/svg_to_pptx/native_diagram_resolver.py)
   splices the component into the slide as native shapes, applies the recolor,
   the text fills, and the deck font.

A component carries only **two base hexes** (`558C5A` primary, `122B87` accent);
all gradient/3D depth is expressed as `lumMod`/`lumOff`/`shade` *modifiers* on those
two, so a single `data-recolor` re-derives the whole figure into the deck palette.

## The demo component (CC0)

[`templates/native_diagrams/demo_synthetic_platform/`](../skills/ppt-master/templates/native_diagrams/demo_synthetic_platform/)
is an **original, CC0** 3-layer capability platform (application / capability /
foundation, 5 cards per layer) authored for this repo — no vendor or client asset
— so it is free to ship and reuse. It exercises every part of the pipeline: extract,
splice, recolor, per-slot re-text, and the CJK-aware budget.

### `slot_spec` and the CJK budget

Each slot's `budget` is measured in **visual width**, not character count: a CJK
glyph is ~2 columns wide, a Latin letter / digit 1. A slot designed for `应用层`
(3 glyphs ≈ 6 columns) holds about 6 Latin characters — counting characters would
let a 6-letter English label overflow it. `data-text` replacements should stay
within each slot's `budget`. The map is an object `{"<id>": "<text>"}`; an array
`[{"id": n, "text": "…"}]` is also accepted, and a `data-text` that matches **no**
slots warns on stderr rather than silently keeping the source text.

## One-command reproduction

```bash
py -3.11 skills/ppt-master/scripts/demo_native_diagram.py -o native_diagram_demo_out
```

This writes two slides into a disposable project and runs the real
`finalize_svg` + `svg_to_pptx` pipeline:

- **Slide 1** — the demo component placed via `data-native-diagram`, recolored to a
  sample brand palette (teal / orange) and re-texted onto a *new* scenario. Its SVG
  carries a single placeholder rect; the polished, gradient-shaded, still-editable
  figure is spliced in at conversion time.
- **Slide 2** — the same content drawn by hand as flat SVG rects/text — the
  "without a native diagram" baseline, for an apples-to-apples before/after.

Open `native_diagram_demo_out/exports/*.pptx`: slide 1 should be the recolored,
re-texted platform with gradient depth intact; slide 2 the flat hand-drawn
equivalent. To confirm the splice rather than trust the log, check that slide 1's
XML carries the recolored hexes and your new text, and none of the component's
original base hexes or source labels.

> Requires `py -3.11` (the pipeline uses `str | Path` syntax that fails on 3.9) with
> `python-pptx` + `lxml`. The output directory is disposable — delete it freely.
