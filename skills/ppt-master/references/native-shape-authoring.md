> See [`shared-standards-core.md`](./shared-standards-core.md) §1.5 for the authored-preset contract and [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.4–§1.5 for the machine metadata.

# Native Shape Authoring Reference

Use during Executor SVG construction or canonical template maintenance whenever a native contour or a supported shape/text operand can express the intended object: choose the contour from the page job, then the simplest exact authoring form; keep atoms independent unless one contour is required; materialize that contour as a PowerPoint-style Boolean result; hand-author freeform last. Neither helper writes a page or a shape's `p:txBody` — visible text stays outside the atomic fragment.

**Contract — the two helpers** (`${SKILL_DIR}` is the retained absolute Skill root; invoke each command once per argument set, read stdout directly, never change CWD, loop, encode the executable or flag list in a scalar shell string, merge stderr, or add a downstream parser when `--compact` exists; `list --search <term>` and `list --grouped --search <term>` are optional spelling/location helpers):

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow --frame 160 210 320 112 \
  --fill "#2563EB" --stroke none --adjust "adj1=val 50000"     # optional --filter-id softShadow (one §6.4 filter id already in <defs>)
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render bentConnector3 \
  --id p03-flow-connector --object-kind connector \
  --frame 420 180 220 140 --fill none --stroke "#475569" --stroke-width 2
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render-batch --input -   # JSON array of the same fields for several already-selected objects
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py describe chevron --compact  # objective identity/adjustment/connector/path facts, only for a serious candidate
python3 ${SKILL_DIR}/scripts/shape_boolean_svg.py render <svg-file> \
  --operation subtract --source body --source cutout --id result
```

- `render` prints one compact atomic `<g data-pptx-authoring="preset">` with preset, frame, adjustments, and base paint written once and registry-generated visible paths as children; **Hard rule — batch after selection**: after selecting two or more objects for one page or template, use `render-batch --input -` so their independent fragments are validated and emitted in one stdout round. `--frame x y w h` is in the coordinate space where the fragment is inserted (group-local inside a `<g transform>`). Insert the fragment unchanged through the normal page edit; never redirect helper output into `svg_output/`.
- Paint accepted: `none` or six-digit solid HEX fill/stroke, optional channel opacity, stroke width, cap, join, and one shape-only filter id. Gradient or pattern paint stays ordinary SVG. Connector-family presets require `--object-kind connector`, `--fill none`, and a visible stroke, and export as unconnected `p:cxnSp`.
- **Hard rule — atomic and helper-owned**: never write `data-pptx-prst`, frame, adjustment, or registry paths by hand, never edit a direct path, and rerun the helper when preset, frame, adjustment, paint, or filter changes. Keep the fragment top-level without `data-pptx-bounds` when standalone (its `data-pptx-frame` owns geometry); put labels or decorations beside it in a separate bounded parent group, never inside. Moving, scaling, rotating, or flipping the whole group is fine; zero-scale and shear are not, the transformed frame stays inside DrawingML's coordinate range, and stroke width stays inside its line-width range. Keep the helper's exact space-separated ordinary-decimal `data-pptx-frame` spelling; compact authoring accepts no alternate numeric spelling. Keep paint and opacity off ancestor groups (the checker warns).
- `shape_boolean_svg.py` consumes closed `path` / `polygon` / `rect` / `circle` / `ellipse`, one unfiltered compact preset, or supported horizontal direct `<text>` with a resolvable OpenType face (`--font-dir` adds roots; text becomes glyph geometry). The first `--source` supplies result paint and explicit paint flags override only their named channels; for `subtract` every later operand is removed from it. Coordinates are baked into root space: insert the stdout paths at the primary operand's z-order with no extra transform. `union` / `combine` / `intersect` / `subtract` emit one `<path>`; `fragment` emits `<id>-1`, `<id>-2`, … in top/left/bottom/right/area order, each a separate shape. Results use nonzero winding and never `fill-rule`, `clip-rule`, `clip-path`, `mask`, or Merge Shapes metadata; operands that depend on even-odd fill, clipping, or masking fail closed. Never use it on mirror/preserve source structure.

**Mandatory — complete vocabulary before contour selection**: [`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md) is read completely before contour work (Generate: with the executor core before the first page; Create Template: as soon as `replication_mode` resolves to `standard` or `fidelity`; never for `mirror`); a filtered lookup cannot replace it. Reread only after context invalidation or a known file change.

## 1. Contour Selection and Materialization Gate

**Hard rule — contour before encoding**: choose the page-fit contour from the intended job and active visual system across the full vocabulary before any syntax. Rectangle, rounded rectangle, circle, and ellipse are not an earlier tier because SVG spells them short; easier syntax never selects a contour.

**Default — exact page-fit geometry before generic neutrality (may override when neutrality itself communicates the page)**: resolve relationship fit when the content carries direction, sequence, membership, hierarchy, convergence, reveal, or contrast; independently resolve page-field / carrier fit from ownership, focal hierarchy, boundary strength, and the deck's edge / opening language (`Structure=no` removes only relationship topology). Choose a plain primitive, uniform grid, or no drawn carrier only when that lack of inflection gives the reader a concrete benefit or avoids a false inference — and before it wins, name the strongest fitting native or compound alternative and why its inflection would add nothing, mislead, weaken hierarchy, or conflict with the job. Quick speed, restrained style, readability, equal importance, precedent, and shorter syntax alone never qualify.

**Hard rule — style does not narrow capability**: the visual system weights contour fit and controls paint, stroke, texture, density, and recurrence; it never removes primitives, presets, composition, Boolean, or necessary freeform from consideration. Style-specific syntax guidance applies only to the named style-defining mark.

| Selected result | Authoring form |
|---|---|
| Mirror/preserve input already owns native-shape metadata | Keep the object and metadata; never reselect its preset |
| One exact non-Connector stock contour | Ordinary SVG primitive only when the exporter maps it to that same contour; otherwise `render` and insert the fragment |
| A stock `bentConnector*` / `curvedConnector*` contour expresses a bend or curve with no endpoint attachment | `render --object-kind connector`; an unconnected native Connector |
| A straight relationship, divider, or leader | `<line>`, with a §1.1 marker only when direction is meaningful |
| A boundary that needs no filled surface | The exact form with `fill="none"` and a visible stroke; content stays an independent sibling |
| Two or more native contours form the construction without needing one contour | Independent siblings in one semantic group, composed under §2.1 |
| Operands require Union, Combine, Fragment, Intersect, or Subtract | `shape_boolean_svg.py`; replace the operands with its paths (editable custom geometry) |
| Nothing above expresses the meaning or contour faithfully | Ordinary `<path>` / `<polygon>` (editable custom geometry) |
| The shape only resembles a preset | Never infer a preset; continue to the Boolean gate, then freeform only if no faithful construction exists |

---

## 2. Vocabulary-Guided Preset Selection

[`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md) follows the Office gallery taxonomy (Lines, Rectangles, Basic Shapes, Block Arrows, Equation Shapes, Flowchart, Stars and Banners, Callouts, Action Buttons); its families and objective identities expose what exists without deciding page use.

| Pass | Action | Result |
|---|---|---|
| Job | State what the object must do for the reader before naming a shape | Page role plus any real relationship, direction, aspect, text load, or literal scope |
| Browse | Compare that job against the complete vocabulary: category → family → exact name | A small candidate set chosen by meaning |
| Inspect | `describe --compact` only when exact facts could change the decision | Objective geometry evidence |
| Select | The contour whose inference and character fit the page | One contour; no syntax yet |
| Encode | §1's materialization gate | Primitive, helper preset, Boolean result, or necessary freeform |

**Hard rule — semantic fit, not name association**: a preset name, topic word, or metaphor is not evidence of use; respect `literal_only` and `scope`. A scroll is not a generic playbook carrier, a lightning bolt is not price tension, `chartX` / `chartStar` / `chartPlus` are partition symbols not charts, a flowchart symbol belongs only in an actual flowchart, an `actionButton*` creates no action or link, and logos, icon glyphs, illustrations, brand contours, and data marks are never presets. The vocabulary exposes contours; Executor chooses them; §1 chooses syntax. Export never scans or upgrades existing geometry.

**Shape-first diagram rule**: `<line>` for a straight thin relationship; an exact connector preset for a stock bend or curve; a block-arrow or chevron preset for a solid direction; an open freeform only when none of those expresses the relationship, data geometry, or a locked hand-drawn / organic style. Imported Connector topology stays under the preserve/mirror contract.

### 2.1 Topology assembly and compound page geometry

**Trigger**: after the page's communication / slot job, composition anchors, and any [`executor-structure.md`](./executor-structure.md) topology are resolved, before writing coordinates — at every active granularity. For `Structure=yes`, assemble the resolved topology without changing it, with [`topology-assembly.md`](./topology-assembly.md) as material; for every page, resolve the page-scale geometry move carrying its background field, content zoning, focal hierarchy, or reading path. Before repeating stacked cards or uniform equal columns, compare a page-field, outline, nesting, or continuity construction and the relevant family's exact members; the first workable arrangement's readability does not close this gate, and the gate creates no decoration requirement.

| Pass | Action | Result |
|---|---|---|
| Topology / page job | Retain the resolved topology and its relationship duties; name the page-scale move and its jobs — surface, boundary, focal mark, shared region, counterweight, or a source-backed direction / reveal | Duties plus one composition direction and a few functional zones; no shape names |
| Decompose | Split components needing independent editing, movement, paint, animation, or reuse; separately identify contour / region semantics that need one object or retained Boolean paths | Editable siblings plus any explicit Boolean operand set |
| Select | For each component choose the family, then the exact member from job, full vocabulary, and edge / corner / opening behavior; retain the reader effect when the result is generic or undrawn | Page-fit atoms without syntax bias |
| Compose | Assemble the topology from its atoms; set page frame, scale, z-order, and negative space; keep text, images, icons, data marks, and non-merged accents outside Boolean operands | One relationship-faithful geometry system |
| Materialize | Preset helper per adopted preset; Boolean helper only for contours needing Merge Shapes semantics | Valid authoring SVG |

**Composition lenses — not a checklist**:

| Lens | Use when it strengthens the page |
|---|---|
| Page field | One large surface, outline, aperture, or off-canvas contour organizes major zones instead of a card per unit |
| Outline carrier | `fill="none"` plus a coherent stroke on a frame, arc, bracket, or band gives bare text ownership without a heavy card |
| Nested fields | An inset contour, secondary surface, badge, port, or focal shape inside / across a larger field creates hierarchy; siblings unless one contour must merge |
| Continuity | Independent shapes aligned or overlapped across zones reinforce the reading path |
| Depth and contrast | Filled, outlined, offset, and negative-space atoms combine; Boolean only when the contour itself must change |
| Deck language | A corner, arc, slant, notch, or layering logic recurs with page-fit variation rather than a cloned composition |

At topology scale, independent pieces, one body with dividers, overlapping siblings, fitted joints, intentional gaps, and retained `fragment` regions are common strategies, not a set; never map a topology name to a shape list or infer equal size or spacing.

**Default — running deck geometry check (may override for literal pages or isolated prototypes)**: after each page retain `page job → composition move → contour / edge language` (plus `relationship → topology` for `Structure=yes`) and compare before the next; repeat only for the same job / relationship or deliberate continuity — section, equal weight, style, and precedent are insufficient. No artifact, no second pass.

**Boolean decision gate**:

| Required result | Construction |
|---|---|
| A stock contour already expresses the job | Keep it and materialize through §1; never rebuild it from operands |
| Shapes overlap but must stay independently editable | Separate primitives / presets in one semantic group |
| One continuous outer silhouette | `union` (`combine` only for intentional symmetric negative regions) |
| A true hole, edge cut, or reveal | `subtract`, visible body first |
| Only the common region should remain | `intersect` |
| Exclusive and shared regions need separate styling or motion | `fragment`, each required region retained as its own shape |

**Hard rule — merge only geometry that must become one contour**: never merge text, images, icons, or independent accents to simplify the tree; Boolean discards editable operand history.

| SVG authoring form | Native PPTX result |
|---|---|
| Ordinary `<rect>`, rounded `<rect>`, `<circle>`, `<ellipse>`, `<line>` | Matching editable preset geometry / line |
| Complete `preset_shape_svg.py` fragment | One exact `a:prstGeom` shape, or `p:cxnSp` for a connector preset |
| `shape_boolean_svg.py` result path | Editable `a:custGeom`; the contour, not replayable Merge Shapes history |
| Semantic group of independent atoms and content | A grouped construction whose children stay separately editable |

Operand count, preset choice, geometry, paint, rotation, and grouping come from the page; there is no Boolean quota and no catalog of allowed combinations.

---

## 3. Fragment Generation

`render` emits one object; `render-batch --input -` emits several already-selected objects for one page or template construction from a JSON array with the `render` fields (required `preset`, `id`, `frame` `[x, y, w, h]`; optional `object_kind`, `name`, `fill`, `fill_opacity`, `stroke`, `stroke_width`, `stroke_opacity`, `stroke_linecap`, `stroke_linejoin`, `filter_id`, `adjustments` such as `{"adj": "val 42000"}`). Paint comes from the page context with `spec_lock.md` roles as anchors (create-template: from the confirmed brief and template Design Spec); mirror/preserve input keeps source paint. The batch is transient input, never a project resource or multi-page plan, and never chooses layout.

---

## 4. Atomic Fragment Contract

The logical `<g data-pptx-authoring="preset">` owns id, object kind, preset, frame, adjustments, base paint, and the optional filter reference; its direct `<path>` children are ordered registry layers with only the per-path override a preset requires. No hidden carrier, preview wrapper, `data-pptx-part`, or fingerprint belongs in project-authored SVG. On a structured template the validated group is one semantic atom — Slide-local, the single carrier of an `object` slot, or a direct Master/Layout fixed atom — and the template workflow may add only registered ownership attributes. A canonical template may keep the fragment as an executable exemplar; a page adaptation copies it unchanged only when every field matches, otherwise regenerates it. Full machine contract and validation: [`svg-contract.md`](../scripts/docs/svg-contract.md) §1.5.

---

## 5. Boundaries

| Concern | Behavior |
|---|---|
| Shape text | Stays outside the fragment; editable, but may export as a grouped text box rather than the preset's own `p:txBody` |
| Connector attachment | v1 authors unconnected `p:cxnSp` and accepts no endpoint/site metadata; imported attachments survive only under preserve/mirror |
| Action buttons | Geometry only; no action, navigation, or hyperlink |
| Gradient/pattern paint | Ordinary SVG |
| Shadow/glow | One existing §6.4 filter via `--filter-id`, shape presets only, applied once to the whole shape |
| Multi-path darken/lighten | Registry-derived derivatives of the base color; no lock row |
| Expanded legacy fragments | Readable as Slide-local input with a migration warning; never structured atoms or slot carriers |
| External edits | Any registry-path, style, or semantic mismatch fails quality check and export; regenerate |

---

## 6. Shape Boolean Materialization

**Trigger**: the current construction has two or more supported operands whose faithful result calls for Union, Combine, Fragment, Intersect, or Subtract — decided by Executor from the content and inventory, with no upstream field. Operation semantics match PowerPoint's Merge Shapes: `union` keeps every covered region, `combine` the symmetric difference, `intersect` the common coverage, `subtract` removes later sources from the primary, `fragment` returns each atomic region; the PPTX stores the resulting freeform, not history. Ordinary Slide-local results belong in the applicable untransformed direct-root semantic `<g>` with its normal `id` / `data-pptx-bounds`; Master/Layout results stay direct-root atoms that redeclare `data-pptx-layer`; one non-fragment result may be the `data-pptx-carrier="true"` child of an `object` slot; fragment paths may share a group but never collectively claim one carrier or atom, and helper output inherits no structural role from its operands. In one page edit, remove every operand and insert every returned path at the primary operand's z-order.

---

## 7. Shape-Only Modelling Techniques

Plain geometry plus gradient paint, so all of it survives native export; reachable from any shape-built page, with or without images.

### 7.1 Alternating light/dark gradient = dimensional form

The highest-yield shape technique: a cylinder, metallic band, dimensional numeral, or curved panel comes from one gradient whose stops alternate light · dark · light (three stops) or light · dark · light · dark · light (five). The alternation reads as a curved surface catching light twice; a two-stop ramp always reads flat. Keep every stop on one hue and vary only lightness, hold one light direction per page, and remove strokes so facets meet cleanly. A cylinder takes the ramp across its body and a shallower ramp on its cap ellipse; the same light logic runs across the facets of any folded form.

### 7.2 Reflection without a reflection effect

Native reflection is `Bake-required` (§6.12), so build it: duplicate and flip with `transform="translate(0, 2·y_bottom) scale(1, -1)"`, keep only the top 10–25 % of the copy, lay over it a rectangle whose gradient runs from fully transparent at the object's base to the page background at the cut, and drop the whole reflection to 60–70 % opacity. Seats certificate rows, product shots, logo tiles, and cylinders; no blur.

### 7.3 Fragment as a modelling tool

`fragment` builds registered layered diagrams from one silhouette: a triangle crossed by topology-derived bars gives pyramid tiers, a circle crossed by two bars a quadrant wheel, an annulus sliced radially ring segments — every piece inherits the parent contour, so the assembly stays registered. Derive cutter count, position, and piece size from the resolved topology; use a constant step and one §7.1 gradient family only when equal weight and one-solid reading are semantic.

### 7.4 Soft edges without the soft-edge effect

Feathered edges are `Bake-required`, but their four jobs are gradients:

| Intent | Build instead |
|---|---|
| Contact shadow under an object | Ellipse with a `radialGradient` from dark-transparent at the centre to transparent at the rim |
| Spotlight / stage pool | Cone or ellipse fading to transparent at its far end, low opacity over the scene |
| Object dissolving into the page | A rectangle whose gradient runs from transparent to the exact page background hex |
| Hiding an object while keeping it live | Full transparency, or a background-registered fill ([`image-layout-patterns.md`](./image-layout-patterns.md) `#M1-08`) |

A radial or linear alpha ramp reads as a feathered edge at slide scale and exports intact; never approximate a soft edge with stacked stroked outlines.

### 7.5 Ground plane and staging

An object floating in empty canvas looks pasted on. Give it a wide shallow ellipse or trapezoid beneath, filled with a gradient fading to the background at its edges, optionally with a soft dark ellipse directly under it as contact shadow; a trapezoid narrowing away reads as a receding floor, a cylinder or slab as a pedestal. Keep the plane low-contrast — staging, not content. Two shapes make certificate rows, product heroes, and award pages look composed.
