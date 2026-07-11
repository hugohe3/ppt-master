> See [`shared-standards.md`](./shared-standards.md) §§1.4–1.5 for the native-shape metadata and validation contracts.

# Native Preset Shape Authoring Reference

Use this reference during Executor SVG construction when one standard
PowerPoint shape can express one complete geometric object. The helper does
not create the preset shape's own `p:txBody`; keep visible text outside the
atomic fragment.

## 1. Selection Gate

Apply this decision order before drawing a stock geometric object.

| Condition | Action |
|---|---|
| Plain rectangle, symmetric rounded rectangle, circle, or ellipse | Write the ordinary SVG primitive; the exporter already emits an editable native shape. |
| One DrawingML preset exactly expresses the intended object | Run `preset_shape_svg.py render`, then insert its complete stdout fragment into the hand-authored page. |
| The visual meaning or contour exceeds one stock shape | Write ordinary `<path>` / `<polygon>` geometry; export keeps it as editable custom geometry. |
| The shape only resembles a preset | Keep ordinary SVG; never infer a preset from contour similarity. |
| Mirror/preserve input already owns native-shape metadata | Keep the existing object and metadata; never reselect its preset. |

**Hard rule**: `preset_shape_svg.py` is the only authoring entry for
`data-pptx-authoring="preset"`. Never add `data-pptx-prst`, frame, adjustment,
carrier, preview, or fingerprint attributes to a hand-written path.

---

## 2. Semantic Preset Candidate Guide

"Automatic" means the Executor independently applies this semantic decision
gate before drawing a new object. It does not scan existing SVG, classify
paths or contours, or upgrade ordinary SVG during export.

| Visual intent | Candidate presets | Boundary |
|---|---|---|
| Literal geometric body | `triangle`, `diamond`, `pentagon`, `hexagon`, `octagon`, `star5` | Use only when the named geometry itself is the intent. |
| Solid block direction | `rightArrow`, `leftArrow`, `upArrow`, `downArrow`, `leftRightArrow`, `upDownArrow`, `chevron` | Thin relationship geometry remains an ordinary SVG `<line>` / `<path>` with no attachment semantics. |
| Standard flowchart node | `flowChartProcess`, `flowChartDecision`, `flowChartInputOutput`, `flowChartTerminator`, `flowChartDocument` | Use only for an actual flowchart; ordinary content cards remain cards. |
| Standard connector route | `straightConnector1`, `bentConnector*`, `curvedConnector*` | The SVG route must match the selected preset; otherwise use a free path. |
| Stock callout | `wedgeRectCallout`, `wedgeRoundRectCallout`, `wedgeEllipseCallout`, `cloudCallout` | Brand-specific or custom-tail callouts remain free SVG. |
| Stock ribbon or scroll | `ribbon*`, `ellipseRibbon*`, `verticalScroll`, `horizontalScroll` | Select only when the stock contour is visually acceptable. |
| Standalone math symbol | `mathPlus`, `mathMinus`, `mathMultiply`, `mathDivide`, `mathEqual`, `mathNotEqual` | Inline formulas and prose symbols remain text/formula assets. |
| Literal Office symbol | `heart`, `sun`, `moon`, `lightningBolt`, `gear6`, `gear9` | Never replace an icon required by `spec_lock.icons`. |

Use registry search for a less common literal shape:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py list --search arrow
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py describe rightArrow
```

**Forbidden — false native semantics**:

- `actionButton*` when navigation or trigger behavior is expected; the helper
  maps its visual preset geometry only and never creates an action or hyperlink;
- `chartX`, `chartStar`, or `chartPlus` as a substitute for native charts;
- logo, icon glyph, illustration, brand contour, or data-chart marks.

---

## 3. Fragment Generation

Run one command for one selected object. Colors must come from the current
page's re-read `spec_lock.md`.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow \
  --frame 160 210 320 112 \
  --fill "#2563EB" \
  --stroke none \
  --adjust "adj1=val 50000"
```

For a native connector:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render bentConnector3 \
  --id p03-flow-connector \
  --object-kind connector \
  --frame 420 180 220 140 \
  --fill none \
  --stroke "#475569" \
  --stroke-width 2
```

Every connector-family preset requires `--object-kind connector`, `--fill none`,
and a visible stroke. It exports as an unconnected `p:cxnSp`; a connector
preset can never be authored as an ordinary `shape`.

**Hard rule — stdout-only exception**: the helper prints one deterministic
`<g>` fragment. Read that output and insert it with the normal page
`apply_patch` edit. Do not redirect it into `svg_output/`, loop over pages,
batch shapes, or let it choose layout. The main Agent still authors every
complete SVG page sequentially.

---

## 4. Atomic Fragment Contract

The helper emits one logical group containing exactly one hidden native carrier
and one complete visible preview.

| Component | Ownership |
|---|---|
| Logical `<g data-pptx-authoring="preset">` | Stable id, object kind, preset, frame, adjustments, and preview fingerprint. |
| `path[data-pptx-part="geometry"]` | Native PowerPoint export authority; hidden from the browser. |
| `g[data-pptx-part="geometry-preview"]` | Browser-visible preset drawing. |
| `path[data-pptx-part="geometry-detail"]` | One visible layer per DrawingML path, including path-level fill/stroke behavior. |

**Hard rule**: treat the returned group as atomic. Put labels, icons, or other
decorations beside it in a parent `<g>`, never inside the preset group.

**Regeneration rule**: rerun the helper when preset, frame, adjustment, fill,
stroke, or stroke width changes. Moving, scaling, rotating, or flipping the
complete logical group is allowed; zero-scale transforms and shear/skew are
forbidden, and the transformed frame must remain inside DrawingML's coordinate
range. Stroke width must remain inside DrawingML's line-width range. To freely
edit the contour, replace the whole fragment with ordinary SVG rather than
modifying a `geometry-detail` path.

---

## 5. Boundaries

| Concern | Behavior |
|---|---|
| Shape text | Keep visible SVG `<text>` outside the atomic fragment. It remains editable but may export as a grouped text box rather than the preset's own `p:txBody`. |
| Connector attachment | Authoring helper v1 creates an unconnected `p:cxnSp` and does not accept endpoint/site metadata. Do not hand-add it. The imported-shape contract may preserve an attachment that already exists in a source PPTX; creating a new attached connector is currently unsupported. |
| Action button behavior | `actionButton*` presets map visual geometry only. No action, navigation target, or hyperlink is created automatically. |
| Gradient/pattern paint | Authoring helper v1 accepts solid HEX paint only. Use ordinary SVG when a complex paint treatment is essential. |
| Multi-path darken/lighten | Browser preview uses the shared normalized paint behavior from the PPTX importer. |
| External edits | Any preview or semantic mismatch fails quality check and export; regenerate the fragment. |

**Validation**: `svg_quality_checker.py` independently rerenders every authored
preset from registry metadata and compares the carrier, visible layers, style,
and fingerprint before export.
