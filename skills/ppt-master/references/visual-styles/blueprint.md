# Visual style: blueprint

Engineering schematic — thin line work on dark blueprint paper, isometric projection, technical-annotation language. Speaks like a drawing hung on a wall, not a marketing slide. For architecture walkthroughs, technical briefings, engineering whitepapers, systems explainers.

---

## 1. Shape & decoration

- Shape language: thin single-weight line frames (no heavy fills); components drawn as outlined geometry; optional isometric / 3D-axonometric projection for structures. Slight or zero corner rounding.
- Decoration: the engineering-drawing vocabulary — dimension lines, leader arrows, component codes, coordinate labels, a faint gridline backdrop under everything. Annotation *is* the decoration.
- Whitespace: the grid breathes through; let line work float on the dark field with measured spacing.

## 2. Typography character

- Clean sans for labels and body; monospace for every component name / code / coordinate — mirroring how real technical docs read.
- Small, precise annotation type; wide tracking on coordinate / dimension labels. Restraint over emphasis.

> Families are chosen at confirmation `g`; this style asks for a clean sans + monospace pairing.

## 3. Using the deck's colors

- Dark paper field; a single line-color carries all the schematic line work (frames, connectors, edges); one spot accent marks the current state / key path / callout — the classic engineering-drawing convention of one highlight color.
- Everything else stays low-key line work. The accent appears at few points, high contrast.

> HEX values come from confirmation `e`; this style only governs the line-vs-accent discipline — it names no colors.

## 4. Texture / elevation

- Flat line work, not material elevation. Depth reads from isometric projection and layered line weights, not shadows. Optional subtle corner vignette / accent glow on the dark paper — keep it faint. (Dark-field legibility: [`shared-standards.md §6`](../shared-standards.md).)

## 5. Paired image-rendering

`blueprint` — lock it so AI imagery shares the schematic line-drawing aesthetic.

## 6. Illustration propensity

**supportive** — but note the natural illustration here is hand-drawn **SVG schematic line-work / annotated marks**, not raster spot sheets; reach for line diagrams over decorative cutouts. If raster spots are used at all, keep them schematic, sparse, and secondary to the SVG line work. With no user steer this is the default lean; an explicit user request wins either way, and `image_usage: none` writes no illustration rows.
