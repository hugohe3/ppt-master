> See [`shared-standards-core.md`](./shared-standards-core.md) §§1.4–1.5 for the native-shape metadata and validation contracts.

# Native Preset Shape Authoring Reference

Use this reference during Executor SVG construction or project-owned canonical
template maintenance when one standard PowerPoint shape can express one
complete geometric object. The helper does not create the preset shape's own
`p:txBody`; keep visible text outside the atomic fragment.

## 1. Selection Gate

Apply this decision order before drawing a stock geometric object.

> This gate is for picking the **right** native shape, not for avoiding presets.
> When a page needs an arrow, chevron, callout, banner, flowchart node, or a
> literal Office symbol, authoring it as a preset is the **default** — the
> ordinary-SVG rows below are deliberate exceptions, not the norm.

| Condition | Action |
|---|---|
| Plain rectangle, symmetric rounded rectangle, circle, or ellipse | Write the ordinary SVG primitive; the exporter already emits an editable native shape. |
| One DrawingML preset exactly expresses the intended object | Run `preset_shape_svg.py render`, then insert its complete stdout fragment into the hand-authored page or canonical template. |
| The visual meaning or contour exceeds one stock shape | Write ordinary `<path>` / `<polygon>` geometry; export keeps it as editable custom geometry. |
| The shape only resembles a preset | Keep ordinary SVG; never infer a preset from contour similarity. |
| Mirror/preserve input already owns native-shape metadata | Keep the existing object and metadata; never reselect its preset. |

**Hard rule**: `preset_shape_svg.py` is the only authoring entry for
`data-pptx-authoring="preset"`. Never add `data-pptx-prst`, frame, adjustment,
or registry path data by hand. Insert the helper's complete compact `<g>` and
rerun the helper whenever its geometry or paint changes.

---

## 2. Semantic Preset Candidate Guide

Use the table below as the **go-to menu**: match the page's visual intent to a
candidate preset *before* defaulting to a plain rect or path. Reaching here
first is exactly how presets get used instead of forgotten.

"Automatic" means the Executor independently applies this semantic decision
gate before drawing a new object. It does not scan existing SVG, classify
paths or contours, or upgrade ordinary SVG during export.

| Visual intent | Candidate presets | Boundary |
|---|---|---|
| Literal geometric body | `triangle`, `diamond`, `pentagon`, `hexagon`, `octagon`, `star5` | Use only when the named geometry itself is the intent. |
| Solid block direction | `rightArrow`, `leftArrow`, `upArrow`, `downArrow`, `leftRightArrow`, `upDownArrow`, `chevron` | Thin relationship geometry remains an ordinary SVG `<line>` / `<path>` with no attachment semantics. |
| Standard flowchart node | `flowChartProcess`, `flowChartDecision`, `flowChartInputOutput`, `flowChartTerminator`, `flowChartDocument` | Use only for an actual flowchart; ordinary content cards remain cards. |
| Explicit standalone connector | `straightConnector1`, `bentConnector*`, `curvedConnector*` | Use only when the user explicitly requests a PowerPoint Connector object. Diagram relationships otherwise stay ordinary SVG line/path shapes with no attachment semantics. |
| Stock callout | `wedgeRectCallout`, `wedgeRoundRectCallout`, `wedgeEllipseCallout`, `cloudCallout` | Brand-specific or custom-tail callouts remain free SVG. |
| Stock ribbon or scroll | `ribbon*`, `ellipseRibbon*`, `verticalScroll`, `horizontalScroll` | Select only when the stock contour is visually acceptable. |
| Standalone math symbol | `mathPlus`, `mathMinus`, `mathMultiply`, `mathDivide`, `mathEqual`, `mathNotEqual` | Inline formulas and prose symbols remain text/formula assets. |
| Literal Office symbol | `heart`, `sun`, `moon`, `lightningBolt`, `gear6`, `gear9` | Never replace an icon required by `spec_lock.icons`. |

Use registry search for a less common literal shape:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py list --search arrow
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py describe rightArrow
```

**Shape-first diagram rule**: chart-template adaptations use ordinary line/path
shapes for thin relationships and ordinary `shape` presets for solid block
directions. Connector-family presets are reserved for an explicit request for
a standalone PowerPoint Connector; they are not the default for architecture,
process, hierarchy, or framework diagrams and do not gain attachment semantics.
Existing Connector topology imported from a source PPTX remains owned by the
preserve/mirror round-trip contract.

**Forbidden — false native semantics**:

- `actionButton*` when navigation or trigger behavior is expected; the helper
  maps its visual preset geometry only and never creates an action or hyperlink;
- `chartX`, `chartStar`, or `chartPlus` as a substitute for native charts;
- logo, icon glyph, illustration, brand contour, or data-chart marks.

---

## 3. Fragment Generation

Run one command for one selected object. Generated project pages take colors
from the current page's re-read `spec_lock.md`; `create-template` takes colors
from the confirmed brief and template `design_spec.md`. Mirror/preserve input
keeps the source object's paint instead of regenerating this authored form.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow \
  --frame 160 210 320 112 \
  --fill "#2563EB" \
  --stroke none \
  --adjust "adj1=val 50000"
```

For an explicitly requested standalone native connector only:

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
`<g>` fragment. Read that output and insert it with the normal page/template
`apply_patch` edit. Do not redirect it into `svg_output/`, loop over pages or
templates, batch shapes, or let it choose layout. The main Agent still authors
every complete SVG page sequentially and maintains each reusable template
explicitly.

---

## 4. Atomic Fragment Contract

The helper emits one compact logical group. Metadata and base paint are written
once on the group; its direct children are the visible paths regenerated from
the locked preset registry.

| Component | Ownership |
|---|---|
| Logical `<g data-pptx-authoring="preset">` | Stable id, object kind, preset, frame, adjustments, and explicit local base paint. |
| Direct `<path>` children | Ordered browser-visible registry layers. A child writes only a path-specific fill/stroke override when the preset requires one. |
| Deliberately absent transport fields | No hidden carrier, preview wrapper, `data-pptx-part`, or stored fingerprint belongs in project-authored SVG. Those fields remain part of expanded PPTX import/round-trip transport. |

**Hard rule**: treat the returned group as atomic. Keep it as the content group
when it stands alone. When it needs labels, icons, or other decorations, put
the preset and those siblings in a separate parent content group; never put
them inside the preset group itself. Do not edit the direct paths; they are
validation evidence generated from the registry, not a freehand contour
surface.

Canonical page/template authoring also keeps paint and opacity off ancestor
groups that contain the preset. Compatible ancestor paint still exports under
the general SVG composition rules, but the checker warns because the atom is no
longer paint-self-contained; rerun the helper with channel alpha instead.

On a structured template, a validated authored-preset group is one semantic
atom. It may be Slide-local, the single carrier of an `object` slot, or a direct
Master/Layout fixed atom. This narrow exception does not permit ordinary nested
`<g>` structures in Master/Layout layers or placeholder carriers. The template
workflow may add the registered structural ownership attributes to the complete
helper group; it still must not alter preset metadata, paint, or direct paths.

**Frame coordinate space**: `--frame x y w h` is expressed in the coordinate
space where you insert the fragment. At the page root that is page coordinates;
inside a `<g transform="translate(…)">` use **group-local** coordinates — the
ancestor transform stacks on top, so page-absolute values would double-offset
the shape off-canvas. Keep the helper's exact space-separated ordinary-decimal
`data-pptx-frame` spelling; compact authoring does not accept alternate numeric
spellings.

**Regeneration rule**: rerun the helper when preset, frame, adjustment, fill,
stroke, or stroke width changes. Moving, scaling, rotating, or flipping the
complete logical group is allowed; zero-scale transforms and shear/skew are
forbidden, and the transformed frame must remain inside DrawingML's coordinate
range. Stroke width must remain inside DrawingML's line-width range. To freely
edit the contour, replace the whole fragment with ordinary SVG rather than
modifying a generated direct path.

For a canonical reusable template, the complete helper fragment may remain as
an executable exemplar. A final-page adaptation may copy it unchanged only
when all registry metadata, frame, adjustments, and paint remain unchanged;
otherwise regenerate the complete compact group.

---

## 5. Boundaries

| Concern | Behavior |
|---|---|
| Shape text | Keep visible SVG `<text>` outside the atomic fragment. It remains editable but may export as a grouped text box rather than the preset's own `p:txBody`. |
| Connector attachment | Authoring helper v1 creates an unconnected `p:cxnSp` and does not accept endpoint/site metadata. Do not hand-add it. The imported-shape contract may preserve an attachment that already exists in a source PPTX; creating a new attached connector is currently unsupported. |
| Action button behavior | `actionButton*` presets map visual geometry only. No action, navigation target, or hyperlink is created automatically. |
| Gradient/pattern paint | Authoring helper v1 accepts solid HEX paint only. Use ordinary SVG when a complex paint treatment is essential. |
| Multi-path darken/lighten | Direct visible layers use the shared normalized paint behavior from the PPTX importer. Their registry-derived HEX values are authorized derivatives of the locked base color, not spec-lock drift. |
| Expanded compatibility | Existing helper-authored carrier/preview fragments remain readable as ordinary Slide-local input and receive a non-blocking migration warning; they do not become structured fixed atoms or object-slot carriers. Imported expanded fragments remain the lossless mirror/preserve form. |
| External edits | Any registry-path, style, or semantic mismatch fails quality check and export; regenerate the fragment. |

**Validation**: `svg_quality_checker.py` independently rerenders every compact
authored preset from registry metadata and compares its direct visible paths
and paint. The exporter performs the same validation, then expands the compact
group only in memory to reuse the lossless native-shape conversion path.
Compatible expanded authored input remains under its separate carrier/preview
freshness contract.
