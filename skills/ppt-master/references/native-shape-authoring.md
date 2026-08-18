> See [`shared-standards-core.md`](./shared-standards-core.md) §§1.4–1.5 for the native-shape metadata and validation contracts.

# Native Shape Authoring Reference

Use this reference during Executor SVG construction or project-owned canonical
template maintenance when native contours or supported shape/text operands can
express the intended object. Choose each contour from its page job before
deciding how to encode it, then use the simplest exact authoring form. Keep
faithful atoms independent unless one contour is required; materialize that
contour with a PowerPoint-style Boolean result, and use hand-authored freeform
only when those constructions fail. Neither helper writes a page. The preset
helper does not create the shape's own `p:txBody`; keep visible text outside the
atomic fragment.

**Mandatory — complete registry discovery at authoring entry**: before the
first newly authored page or template contour in each valid context, run the
following command unfiltered and retain its complete output (currently 187
names). This is authoring-time capability discovery, never a Strategist task or
Design Spec field. Rerun only after context invalidation or a registry change.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py list
```

Choose from that full inventory by page job. Use `list --search` only to narrow
the already-read inventory and `describe <name>` only after identifying a
candidate; neither replaces the complete initial read. Discovery is prerequisite;
each page consumes it through §§1–2.1 without a quota.

## 1. Contour Selection and Materialization Gate

**Hard rule — contour before encoding**: choose the page-fit contour from the
intended job and active visual system across the full native vocabulary before
considering authoring syntax. Rectangle, rounded-rectangle, circle, and ellipse
contours are not an earlier visual tier merely because SVG has short primitive
syntax for them. Easier syntax is never the reason to select a contour.

**Default — semantic native geometry before neutral fallback (may override when
neutrality itself serves the page)**: Use a relationship-bearing preset or
compound construction for direction, sequence, membership, hierarchy,
convergence, reveal, or contrast. Select a neutral contour, grid, or equal-column
system only when neutrality or equivalence positively serves the page; retain
that fit in active context. Quick speed, restrained style, readability, equal
importance, precedent, and shorter syntax are not such a fit.

**Hard rule — style does not narrow capability**: the active visual system may
weight contour fit and control paint, stroke, texture, density, and recurrence.
It never removes primitives, Office presets, independent composition, Boolean,
or necessary freeform from consideration. Style-specific syntax guidance
applies only to the named style-defining mark, not every functional page
contour.

After contour selection, use the simplest exact materialization below. Do not
hand-author a freeform merely because an SVG path is convenient.

| Selected result | Authoring form |
|---|---|
| Mirror/preserve input already owns native-shape metadata | Keep the existing object and metadata; never reselect its preset. |
| One exact non-Connector stock contour | Use an ordinary SVG primitive only when the exporter maps it to that same contour; otherwise run `preset_shape_svg.py render` and insert its complete stdout fragment. |
| A stock `bentConnector*` / `curvedConnector*` contour exactly expresses a bent or curved relationship and endpoint attachment is not required | Run `preset_shape_svg.py render --object-kind connector`; the result is an unconnected native Connector shape. |
| A straight relationship, divider, or leader | Write `<line>`; use a registered marker only when direction is meaningful. |
| A selected text/content boundary needs no filled surface | Use its exact authoring form with `fill="none"` and a visible stroke; keep its content as independent siblings. |
| Two or more selected native contours form the page construction but do not need one contour | Keep them as independently editable siblings in one ordinary semantic group; use §2.1 to compose the page-level geometry system. |
| Two or more supported closed-shape / resolvable-text operands require Union, Combine, Fragment, Intersect, or Subtract | Run `shape_boolean_svg.py render`, then replace the operands with every stdout path; the result remains ordinary editable custom geometry. |
| Exact native contours, their independent composition, and Boolean materialization cannot faithfully express the visual meaning or contour | Write ordinary `<path>` / `<polygon>` geometry; export keeps it as editable custom geometry. |
| The shape only resembles a preset | Never infer a preset; continue to the Boolean gate, then use freeform only if no faithful construction exists. |

**Hard rule**: `preset_shape_svg.py` is the only authoring entry for
`data-pptx-authoring="preset"`. Never add `data-pptx-prst`, frame, adjustment,
or registry path data by hand. Insert the helper's complete compact `<g>` and
rerun the helper whenever its geometry, paint, or filter reference changes.

---

## 2. Semantic Preset Candidate Guide

Use the table below as semantic navigation, not a shortlist: match the page's
visual intent against the complete inventory already loaded above before
settling on a neutral rectangle / ellipse or a freeform path. Do not let the
examples, selected style, or authoring convenience hide a more specific
registered contour. A style's composition examples are generative vocabulary,
not the set of permitted page moves.

"Automatic" means the Executor independently applies this semantic decision
gate before drawing a new object. It does not scan existing SVG, classify
paths or contours, or upgrade ordinary SVG during export.

| Visual intent | Candidate presets | Boundary |
|---|---|---|
| Literal geometric body | `triangle`, `diamond`, `pentagon`, `hexagon`, `octagon`, `star5` | Use only when the named geometry itself is the intent. |
| Solid block direction | `rightArrow`, `leftArrow`, `upArrow`, `downArrow`, `leftRightArrow`, `upDownArrow`, `chevron` | Use `<line>` for a thin straight relationship; do not fake a solid directional object with a stroked path. |
| Standard flowchart node | `flowChartProcess`, `flowChartDecision`, `flowChartInputOutput`, `flowChartTerminator`, `flowChartDocument` | Use only for an actual flowchart; ordinary content cards remain cards. |
| Stock bent / curved relationship contour | `bentConnector*`, `curvedConnector*` | Prefer when the contour fits and endpoint attachment is not required. The authored object is an unconnected native Connector, so moving nodes does not reroute it. |
| Stock callout | `wedgeRectCallout`, `wedgeRoundRectCallout`, `wedgeEllipseCallout`, `cloudCallout` | For a brand-specific or custom tail, continue through the Boolean gate; use freeform only if the result still cannot be expressed faithfully. |
| Stock ribbon or scroll | `ribbon*`, `ellipseRibbon*`, `verticalScroll`, `horizontalScroll` | Select only when the stock contour is visually acceptable. |
| Standalone math symbol | `mathPlus`, `mathMinus`, `mathMultiply`, `mathDivide`, `mathEqual`, `mathNotEqual` | Use only when the symbol itself is a diagram shape; simple notation remains text, while non-trivial inline or block mathematics follows [`native-formula.md`](./native-formula.md). |
| Literal Office symbol | `heart`, `sun`, `moon`, `lightningBolt`, `gear6`, `gear9` | Never replace an icon required by `spec_lock.icons`. |

Narrow and inspect candidates from the already-loaded inventory:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py list --search arrow
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py describe rightArrow
```

**Shape-first diagram rule**: use `<line>` for straight thin relationships;
use an exact connector-family preset for a stock bent or curved contour; use a
block-arrow / chevron preset for a solid direction. Resort to an open freeform
path only when those native constructions cannot faithfully express the
relationship, data geometry, or locked hand-drawn / organic style. Newly
authored connector-family presets remain unconnected and do not gain attachment
semantics. Existing Connector topology imported from a source PPTX remains
owned by the preserve/mirror round-trip contract.

**Forbidden — false native semantics**:

- `actionButton*` when navigation or trigger behavior is expected; the helper
  maps its visual preset geometry only and never creates an action or hyperlink;
- `chartX`, `chartStar`, or `chartPlus` as a substitute for native charts;
- logo, icon glyph, illustration, brand contour, or data-chart marks.

### 2.1 Compound page geometry

**Trigger**: after the page or prototype's communication / slot job, composition
anchors, and any applicable topology under
[`executor-structure.md`](./executor-structure.md) are resolved, but before
writing coordinates, resolve the page-scale geometry move that best carries its
background field, content zoning, focal hierarchy, or reading path. Apply §1's
semantic-before-neutral default and compare the useful lenses below. Before
falling back to stacked rectangles / rounded cards or uniform equal columns,
use a relationship-bearing construction to stage the primary zone. Readability
of the first workable arrangement does not close this gate.
This applies whether the per-page Structure result is `no` or `yes`; it never
creates a decoration requirement.

| Pass | Action | Result |
|---|---|---|
| Page job | Name the page-scale geometry move, then the geometric jobs already implied by the resolved page: surface, boundary, direction, reveal, focal mark, shared region, or counterweight. | One composition direction and a small set of functional zones; no shape names yet. |
| Decompose | Separate visible content from geometric atoms. Identify which atoms need independent movement, paint, or reuse and which contour must become one object. | Editable siblings plus any explicit Boolean operand set. |
| Select | Choose each atom's contour from its job and the full native vocabulary, then apply §1's simplest exact materialization; retain the positive page-job fit when the final result is neutral. | Page-fit native atoms without syntax bias. |
| Compose | Establish page frame, scale, z-order, and negative space with independent atoms. Keep text, images, icons, data marks, and non-merged accents outside Boolean operands. | One page-level geometry system, not a collection of unrelated decorations. |
| Materialize | Run the preset helper for each adopted preset. Run the Boolean helper only for contours that require Merge Shapes semantics, then replace those operands with its stdout paths. | Valid authoring SVG ready for native export. |

**Composition lenses — not a checklist**:

| Lens | Use when it strengthens the resolved page |
|---|---|
| Page field | Let one large surface, outline, aperture, or off-canvas contour organize major zones instead of wrapping every content unit in a card. |
| Outline carrier | Use `fill="none"` plus a coherent stroke on a frame, arc, bracket, band, or other faithful contour when bare text needs ownership without a heavy filled card. |
| Nested fields | Visually nest an inset contour, secondary surface, badge, port, or focal shape inside / across a larger field to create hierarchy; keep them as siblings unless one contour must merge. |
| Continuity | Align or overlap independent shapes across zones so geometry reinforces the intended reading path. |
| Depth and contrast | Combine filled, outlined, offset, and negative-space atoms; use Boolean only when the contour itself must change. |
| Deck language | Reuse a corner, arc, slant, notch, or layering logic with page-fit variation rather than cloning one composition. |

**Default — running deck topology check (may override for literal pages or
isolated template prototypes)**: After each generated page, retain
`relationship → topology → contour vocabulary` and compare it before the next.
Repeat only for the same semantic relationship or deliberate continuity;
section, equal weight/density, style, and precedent are insufficient. Create no
artifact or second pass.

**Boolean decision gate**:

| Required result | Construction |
|---|---|
| Stock contour already expresses the job | Keep that exact contour and materialize it through §1; do not rebuild it from other shapes or Boolean operands. |
| Shapes overlap or layer but must remain independently editable | Keep separate primitives / presets in one ordinary semantic group; do not merge them. |
| One continuous outer silhouette | `union`; use `combine` only for intentional symmetric negative regions. |
| A true hole, edge cut, or reveal | `subtract`, with the visible body first and cutout operands after it. |
| Only the common covered region should remain | `intersect`. |
| Exclusive and shared regions need separate styling or motion | `fragment`, retaining every required result path as an independent shape. |

**Authoring-to-export map**:

| SVG authoring form | Native PPTX result |
|---|---|
| Ordinary `<rect>`, rounded `<rect>`, `<circle>`, `<ellipse>`, or `<line>` | Matching editable preset geometry / line shape. |
| Complete `preset_shape_svg.py` fragment | One exact `a:prstGeom` shape, or `p:cxnSp` for an authored connector preset. |
| `shape_boolean_svg.py` result path | Editable `a:custGeom`; the final contour is retained, not replayable Merge Shapes history. |
| Parent semantic group containing independent atoms and content | A grouped page construction whose child shapes remain separately editable. |

**Reference — not a constraint**: derive the operand count, preset choices,
geometry, paint, rotation, and grouping from the current page. A strong compound
construction may use only independent presets, only one Boolean result, or a mix;
there is no Boolean quota and no catalog of allowed combinations.

**Hard rule — merge only geometry that must become one contour**: never merge
text, images, icons, or otherwise independent accents merely to simplify the
SVG tree. Boolean materialization discards editable operand history; preserve
siblings whenever one-object contour semantics are unnecessary.

---

## 3. Fragment Generation

One helper invocation owns one selected object; multiple chosen objects may
render in one tool round as separate outputs.
Generated project pages choose each object's solid paint from the current page
context, using `spec_lock.md` roles as reusable anchors rather than an exhaustive
palette; `create-template` takes colors from the confirmed brief and template
`design_spec.md`. Mirror/preserve input keeps the source object's paint instead
of regenerating this authored form.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow \
  --frame 160 210 320 112 \
  --fill "#2563EB" \
  --stroke none \
  --adjust "adj1=val 50000"
```

When one native effect is justified, append `--filter-id softShadow`.
`softShadow` must already be one direct page-level `<defs><filter>` id under
[`svg-effects.md`](./svg-effects.md) §6.4. Omit the option otherwise.

For a stock bent / curved contour that does not require endpoint attachment:

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
`apply_patch` edit. Do not redirect it into `svg_output/`, drive it from a batch
manifest, loop over pages/templates, or let it choose layout. The main Agent
still authors each complete SVG page and reusable template explicitly.

---

## 4. Atomic Fragment Contract

The helper emits one compact logical group. Metadata and base paint are written
once on the group; its direct children are the visible paths regenerated from
the locked preset registry.

| Component | Ownership |
|---|---|
| Logical `<g data-pptx-authoring="preset">` | Stable id, object kind, preset, frame, adjustments, explicit local base paint, and an optional helper-authored shape filter reference. |
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
helper group; it still must not alter preset metadata, paint, the filter
reference, or direct paths.

**Frame coordinate space**: `--frame x y w h` is expressed in the coordinate
space where you insert the fragment. At the page root that is page coordinates;
inside a `<g transform="translate(…)">` use **group-local** coordinates — the
ancestor transform stacks on top, so page-absolute values would double-offset
the shape off-canvas. Keep the helper's exact space-separated ordinary-decimal
`data-pptx-frame` spelling; compact authoring does not accept alternate numeric
spellings.

**Regeneration rule**: rerun the helper when preset, frame, adjustment, fill,
stroke, stroke width, or the filter id changes. Moving, scaling, rotating, or
flipping the complete logical group is allowed; zero-scale transforms and
shear/skew are forbidden, and the transformed frame must remain inside
DrawingML's coordinate range. Stroke width must remain inside DrawingML's
line-width range. To freely edit the contour, replace the whole fragment with
ordinary SVG rather than modifying a generated direct path.

For a canonical reusable template, the complete helper fragment may remain as
an executable exemplar. A final-page adaptation may copy it unchanged only
when all registry metadata, frame, adjustments, paint, and the optional filter
reference remain unchanged; otherwise regenerate the complete compact group.

---

## 5. Boundaries

| Concern | Behavior |
|---|---|
| Shape text | Keep visible SVG `<text>` outside the atomic fragment. It remains editable but may export as a grouped text box rather than the preset's own `p:txBody`. |
| Connector attachment | Authoring helper v1 creates an unconnected `p:cxnSp` and does not accept endpoint/site metadata. Do not hand-add it. The imported-shape contract may preserve an attachment that already exists in a source PPTX; creating a new attached connector is currently unsupported. |
| Action button behavior | `actionButton*` presets map visual geometry only. No action, navigation target, or hyperlink is created automatically. |
| Gradient/pattern paint | Authoring helper v1 accepts solid HEX paint only. Use ordinary SVG when a complex paint treatment is essential. |
| Shadow/glow | Shape presets may reference one existing [`svg-effects.md`](./svg-effects.md) §6.4 filter through `--filter-id`; it applies once to the complete native shape. Connector presets, multiple effects, child-path filters, and other effect graphs remain unsupported. |
| Multi-path darken/lighten | Direct visible layers use the shared normalized paint behavior from the PPTX importer. Their registry-derived HEX values are authorized derivatives of the selected base color and need no separate lock row. |
| Expanded compatibility | Existing helper-authored carrier/preview fragments remain readable as ordinary Slide-local input and receive a non-blocking migration warning; they do not become structured fixed atoms or object-slot carriers. Imported expanded fragments remain the lossless mirror/preserve form. |
| External edits | Any registry-path, style, or semantic mismatch fails quality check and export; regenerate the fragment. |

**Validation**: `svg_quality_checker.py` independently rerenders every compact
authored preset from registry metadata and compares its direct visible paths
and paint. It also validates the optional shape filter through the shared
[`svg-effects.md`](./svg-effects.md) §6.4 contract. The exporter performs the
same validation, then expands the compact group only in memory to reuse the
lossless native-shape conversion path.
Compatible expanded authored input remains under its separate carrier/preview
freshness contract.

---

## 6. Shape Boolean Materialization

**Trigger**: Current page construction has two or more supported shape/text operands
whose faithful result calls for PowerPoint-style Union, Combine, Fragment,
Intersect, or Subtract. Executor decides this directly from the actual content,
complete native inventory, and explicit user/template constraints; no upstream
suggestion or planning field is required.

```bash
python3 ${SKILL_DIR}/scripts/shape_boolean_svg.py render <svg-file> \
  --operation subtract \
  --source body \
  --source cutout \
  --id result
```

| Concern | Contract |
|---|---|
| Sources | Closed `path`, `polygon`, `rect`, `circle`, `ellipse`, one validated unfiltered compact authored shape preset, or supported horizontal implicit-LTR direct `<text>` with a resolvable exact OpenType weight/style (`--font-dir` adds search roots). Text becomes glyph geometry and is no longer editable text. A filtered preset is not a Boolean operand; materialize the geometry without the effect, then reapply one supported filter to the result. Open geometry, groups, nested text, images, definitions, and nested SVG viewports fail closed. |
| Primary shape | The first `--source` supplies result paint. For `subtract`, all later operands are removed from that primary geometry. Explicit paint flags override only their named channels. |
| Coordinates | Ancestor and local transforms are baked into SVG-root coordinate space. Place stdout in the primary operand's z-order with no additional transform; never reinsert it under an original transformed ancestor. Root-coordinate space does not require each result path to be a direct `<svg>` child. |
| Placement | Ordinary Slide-local results belong in the applicable untransformed direct-root semantic `<g>` with its normal `id` / `data-pptx-bounds`. Master/Layout results remain direct-root path atoms and redeclare `data-pptx-layer`. One non-fragment result may be the direct `data-pptx-carrier="true"` child of an `object` slot. |
| Fragment roles | Fragment paths may share one ordinary Slide-local semantic group, but remain separate shapes and cannot collectively claim one carrier or one Master/Layout atom. Helper output inherits no structural role metadata from its operands; redeclare only the final layer/carrier/role contract. |
| Result | `union`, `combine`, `intersect`, and `subtract` emit one ordinary `<path>`. `fragment` emits stable sibling paths named `<id>-1`, `<id>-2`, ... in top/left/bottom/right/area order. |
| Winding | Results use explicit nonzero contour direction and never emit `fill-rule`, `clip-rule`, `clip-path`, `mask`, or Merge Shapes metadata. Operands that depend on even-odd fill, clipping, or masking fail closed. |
| Preservation | This helper authors new geometry only. Never use it to merge or split mirror/preserve source structure. |

Operation semantics match PowerPoint's visible Merge Shapes result: `union`
keeps every covered region, `combine` keeps the symmetric difference,
`intersect` keeps only common coverage, `subtract` removes every later source
from the primary, and `fragment` returns each atomic filled region. The PPTX
stores the materialized freeform geometry, not replayable operation history.

**Hard rule — stdout-only replacement**: The helper never writes the source
page. In one normal `apply_patch` edit, remove every selected operand and insert
every returned path in root coordinate space at the primary operand's z-order,
using the placement contract above. Fragment paths remain separate shapes; an
ordinary semantic group does not turn them into one structural atom.

---

## 7. Shape-Only Modelling Techniques

Applies to any page built from shapes, **with or without images** — a text-only,
data-only, or icon-only deck reaches these the same way. Each technique below is
plain geometry plus gradient paint, so all of it survives native export.

### 7.1 Alternating light/dark gradient = dimensional form

The single highest-yield shape technique. A cylinder, metallic band, dimensional
numeral, or curved panel is produced by one gradient whose stops **alternate
light and dark** across the shape — light · dark · light for a three-stop ramp,
or light · dark · light · dark · light for a five-stop one. The alternation
imitates a curved surface catching light twice; a plain two-stop ramp always
reads flat no matter how strong the contrast.

Keep every stop on one hue and vary only lightness, hold one light direction for
the whole page, and remove strokes so adjacent facets meet cleanly. For a
cylinder, apply the alternating ramp across the body and cap it with an ellipse
carrying its own shallower ramp. The same light logic applies across separate
facets of any folded form.

### 7.2 Reflection without a reflection effect

Native reflection is `Bake-required` ([`svg-effects.md`](./svg-effects.md) §6.12),
so build it from geometry instead:

1. Duplicate the object and flip it with `transform="translate(0, 2·y_bottom) scale(1, -1)"`.
2. Keep only the top **10–25 %** of the flipped copy — that is all a reflection
   ever shows.
3. Lay a rectangle over it filled with a gradient running from fully transparent
   at the object's base to the page background color at the cut line, so the
   copy dissolves into the page.
4. Drop the whole reflection to roughly **60–70 %** opacity.

Seat rows of certificates, product shots, logo tiles, and cylinders this way. Do
not add a blur — it will not survive export, and a short gradient fade already
reads correctly at slide scale.

### 7.3 Fragment as a modelling tool, not just a boolean

`fragment` (§6) is the fastest way to build layered diagrams from one silhouette:
lay evenly distributed bars across a triangle and fragment it into pyramid tiers;
cross a circle with two bars for a quadrant wheel; slice an annulus radially for
ring segments. Every piece inherits the parent contour, so the assembly stays
perfectly registered — impossible to achieve by drawing the tiers separately.

Distribute the cutting bars with a constant step before fragmenting; uneven tiers
read as a mistake rather than a hierarchy. Paint the resulting pieces with one
gradient family per §7.1 so the stack reads as a single solid.

### 7.4 Soft edges without the soft-edge effect

Feathered edges are `Bake-required` ([`svg-effects.md`](./svg-effects.md) §6.12),
but the four jobs they normally do are all reachable with gradients:

| Intent | Build instead |
|---|---|
| Contact shadow under an object | Ellipse filled with a `radialGradient` from dark-transparent at the centre to fully transparent at the rim |
| Spotlight / stage pool | Cone or ellipse filled with a gradient fading to transparent at its far end, at low opacity over the scene |
| Object dissolving into the page | Overlay a rectangle whose gradient runs from transparent to the exact page background hex |
| Hiding an object while keeping it live | Full transparency, or a background-registered fill ([`image-layout-patterns.md`](./image-layout-patterns.md) `#M1-08`) |

A radial or linear alpha ramp reads the same as a feathered edge at slide scale
and, unlike a filter, exports intact. Never approximate a soft edge with a stack
of stroked outlines — the banding is visible on projection.

### 7.5 Ground plane and staging

An object floating in empty canvas looks pasted on. Give it a surface: a wide
shallow ellipse or trapezoid beneath it, filled with a gradient that fades to the
background at its edges, optionally with a soft dark ellipse directly under the
object as contact shadow. A trapezoid narrowing away from the viewer reads as a
receding floor; a cylinder or slab reads as a pedestal.

Keep the plane low-contrast — it is staging, not content. This is what makes
certificate rows, product hero shots, and trophy/award pages look composed
rather than floating, and it costs two shapes.
