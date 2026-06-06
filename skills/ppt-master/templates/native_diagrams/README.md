# Native Diagram Library

Reusable, **natively editable** DrawingML diagrams lifted verbatim from existing
`.pptx` decks. This library is the answer to "I have a beautiful diagram in a
PowerPoint file — keep it pixel-identical AND keep it editable in new decks."

## Why this is not the SVG path

The SVG import path (`pptx_to_svg.py` → `svg_to_pptx.py`) re-renders a diagram as
SVG and back. That works for clean structural diagrams but **degrades elaborate
flourishes** — bezier flow arrows, halftone dot patterns, multi-stop gradient 3D
shading can simplify or drop, because they round-trip through a different format.

A *native diagram* skips SVG entirely. The original `<p:sp>` / `<p:grpSp>` XML is
kept byte-for-byte, so it renders **exactly** like the source and stays a set of
native PowerPoint shapes you can click, recolor, and restyle. The only transform
is **theme flattening** (see below) so it survives moving to a deck with a
different theme.

## Source of truth

[`diagrams_index.json`](./diagrams_index.json) lists every component with a
one-line selection `summary` (format: `"Pick for X. Skip if Y."`). Roles and
humans scan it top-to-bottom; there is no category sub-index.

## Component format

Each component is a directory `native_diagrams/<key>/`:

| File | Purpose |
|------|---------|
| `shapes.xml` | flattened top-level shapes wrapped in `<a:diagram>` — theme-independent, editable |
| `media/` | bitmaps the diagram references (only when present) |
| `meta.json` | provenance, canvas size, media rId map, flatten counts, summary |

**Theme flattening** resolves every `<a:schemeClr>` → `<a:srgbClr>` (through the
source master's `clrMap` + theme color scheme) and every `+mj-ea` / `+mn-lt` font
token → its concrete typeface. Gradient/3D modifier children (`lumMod` / `shade`
/ `tint` / …) are preserved, so the look is identical with zero theme dependency.

## Building the library

```bash
# 1) Extract a valuable diagram from a source deck (1-based slide number)
python3 scripts/extract_diagram.py <source.pptx> <slide_num> \
    -o templates/native_diagrams/<key> --key <key> \
    --summary "Pick for X. Skip if Y (use other_key)."

# 2) Register it (hand-edit diagrams_index.json — add a "<key>": { "summary": ... } entry)
```

## Using a diagram in a new deck

```bash
# Drop onto a new blank slide in a fresh deck
python3 scripts/inject_diagram.py templates/native_diagrams/<key> -o out.pptx

# Append onto an existing deck (new blank slide)
python3 scripts/inject_diagram.py templates/native_diagrams/<key> -o out.pptx --target deck.pptx

# Place into an existing slide, reframed into a rectangle (EMU; 914400 = 1 inch)
python3 scripts/inject_diagram.py templates/native_diagrams/<key> -o out.pptx \
    --target deck.pptx --slide 2 --into-existing --pos 914400,914400,10363200,5029200
```

## Using a diagram inside a generated deck (SVG placeholder)

Native diagrams are a first-class peer of `<use data-icon>` and `<image>` in the
SVG → DrawingML pipeline. The Executor draws a placeholder in the page SVG and
`svg_to_pptx` splices the named component in at conversion time — scaled to the
placeholder rect and optionally recolored to the deck palette:

```xml
<!-- the component is scaled into x/y/width/height; resolved to native shapes -->
<rect data-native-diagram="combo_product_system"
      data-recolor="558C5A=1E3A5F,122B87=D4AF37"
      x="140" y="120" width="1000" height="480" fill="none"/>
```

- `data-native-diagram` — the library `<key>`.
- `data-recolor` (optional) — `OLD=NEW,…` base-hex map (see "color" below); maps
  the diagram's accents onto the deck's `spec_lock` palette, 3D shading re-derived.
- The rect itself never renders — it is replaced by the spliced DrawingML. Give it
  `fill="none"` (optionally a dashed stroke) so the SVG preview shows the reserved
  region; the real diagram only materializes in the PPTX.

> Resolved by `svg_to_pptx/native_diagram_resolver.py`; string-spliced so the
> component's namespaces (`a`/`p`/`r`/`a14`/`a16`) stay byte-exact.

## Limits (v1)

- **Charts** (`graphicFrame` → chart part) are recorded in `meta['charts_unsupported']`
  and NOT lifted — chart parts carry their own data/embedding sub-parts. Use the
  SVG chart templates (`templates/charts/`) for data charts instead.
- A native diagram is a **frozen component**: place / recolor / relabel it, but the
  LLM does not redraw it. Decks needing free-form generated layouts use the SVG
  pipeline; this library is for reusing exact pre-designed diagrams.
- SVG-blip images (`<asvg:svgBlip>`) are uncommon in diagram packs; PNG/JPEG media
  are fully supported.
