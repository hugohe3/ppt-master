# Native Diagram Library

Reusable, **natively editable** DrawingML diagrams that are spliced into a deck at
SVG→PPTX conversion time. A native diagram keeps the source figure pixel-identical
*and* keeps it a set of native PowerPoint shapes you can click, recolor, and
restyle — the opposite of re-rendering it through SVG.

## Why this is not the SVG path

The SVG import path (`pptx_to_svg.py` → `svg_to_pptx.py`) re-renders a diagram as
SVG and back. That works for clean structural diagrams but **degrades elaborate
flourishes** — bezier flow arrows, halftone patterns, multi-stop gradient 3D
shading can simplify or drop when they round-trip through a different format.

A *native diagram* skips SVG entirely. The original `<p:sp>` / `<p:grpSp>` XML is
kept byte-for-byte; the only transform is **theme flattening** (`schemeClr` →
`srgbClr`, theme fonts → typefaces) so it survives moving to a deck with a
different theme.

## Layout

```
<key>/
    shapes.xml.gz   flattened top-level shapes wrapped in <a:diagram> (gzip; ~18x)
    meta.json       provenance + canvas + text_slots + slot_spec + structure
    media/          only when the diagram references bitmaps (gitignored by default)
```

[`diagrams_index.json`](./diagrams_index.json) is `{ meta, diagrams }` — the
single-pass selection schema (scenario × type/use × slots × holds × density …).
See [`references/native-diagrams.md`](../../references/native-diagrams.md) for the
selection and placement contract, and [`docs/native-diagrams.md`](../../../../docs/native-diagrams.md)
for the end-to-end overview + one-command demo.

## License

Components shipped here are **original CC0 assets** authored for this repo — free
to ship and reuse. `demo_synthetic_platform` is the reference component: a 3-layer
capability platform built from plain DrawingML (no vendor or client source).

## Build your own

Lift one slide of any `.pptx` into a component:

```bash
python3 scripts/extract_diagram.py <source.pptx> <slide_num> \
    -o templates/native_diagrams/<key> --key <key> \
    --summary "..." --structure "..."
```

`extract` records every text run as a slot and writes a CJK-aware `slot_spec`
(budgets in visual width, where a CJK glyph counts as 2 columns).
