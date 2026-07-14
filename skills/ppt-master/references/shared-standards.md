# Shared Technical Standards

Mandatory reference for every PPT Master route that authors or regenerates slide visuals through SVG: owns shared XML/SVG constraints, editable PPTX mappings, advanced effects, geometry recipes, and PPT-specific interfaces.
Other files link here instead of restating its contracts.

**Document map**:

| Section | Owns | Strength |
|---|---|---|
| §1 Required Foundation, Forbidden Features, and Conditional Interfaces | XML validity, the closed generated-authoring surface, structural blacklist, native line ends, image clipping, static local reuse, and imported/authored native-shape semantics | Required / Forbidden / Conditional |
| §2 Conditional Compatibility Mappings | Direct geometry-length grammar, literal inline geometry, and the approximate group-opacity compatibility boundary | Required / Conditional / Default |
| §3 Canvas Format Quick Reference | Pointer to the complete canvas catalog | Reference |
| §4 Required Page Contract and Conditional Packaging | Complete-page authority, semantic markers, editable text/grouping, and package promotion | Required / Conditional |
| §5 Workflow Authority | Pointer to the serial post-processing/export procedure | Workflow pointer |
| §6 Advanced SVG Effects and Authoring Techniques | Color/alpha, gradients, shadows, glow, overlays, lines, text treatments, transforms, freeform geometry, chart geometry, and constructed visual styles | Contract + optional recipes |
| §7 Conditional PPT Interfaces | Pattern fills, native tables/charts, Master text styles, and Master/Layout/placeholder metadata | Conditional |
| §8 Scope Boundary | Concerns intentionally owned by another reference or workflow | Boundary |

**Advanced capability index**:

| Capability family | Available authoring vocabulary | Detail |
|---|---|---|
| Color and transparency | Default opaque `#RRGGBB` paint plus channel-specific alpha; compatible CSS-color spellings, picture/atomic-element opacity, and approximate group opacity | §2.2, §6.2 |
| Gradients and paint | Linear/radial fills, transparent stops, gradient text, gradient strokes, and preset patterns | §6.3, §7 |
| Depth and light | Soft/colored/directional shadow, glow, layered-geometry fallback, and paper-layer elevation | §6.4 |
| Image treatment | Directional scrim, bottom fade, vignette, spotlight, brand wash, picture fading, and glass-like surfaces | §1.2, §6.5 |
| Lines and connectors | Preset/custom dash, cap/join, gradient flow strokes, markers, and explicit-grid paths | §1.1, §6.6 |
| Text treatments | Mixed runs, tracking, underline, strikethrough, gradient fill, outline, transparency, watermark text, and text glow | §4.2, §6.7 |
| Transforms and composition | Translate, scale, rotate, mirror, supported matrix composition, layering, and static local reuse | §1.3, §6.8 |
| Freeform geometry | Full SVG path vocabulary, curves, organic containers, multi-subpaths, and asymmetric rounded rectangles | §6.9 |
| Imported PowerPoint shapes | Lossless import payload, lightweight inspection projection, and selective restoration of preset/custom geometry, connectors, and unchanged native text bodies | §1.4 |
| Authored PowerPoint preset shapes | Registry-generated visible fragments that export as one native preset shape or connector | §1.5; [`native-shape-authoring.md`](./native-shape-authoring.md) |
| Radial/chart geometry | Pie/donut arcs, dashed-circle ring segments, gauges, progress rings, sunbursts, and diagonal polygon arrowheads | §6.10 |
| Constructed visual styles | Faux glass, hand-drawn marks, ink wash, Riso offset, pixel grid, halftone, isometric facets, paper cut, and line-plus-area data treatment | §6.11 |
| Unsupported-effect fallbacks | Raster baking or explicit-geometry alternatives for blur, inner shadow, soft edge, reflection, turbulence, blend modes, and arbitrary masks | §6.12 |
| Selection quick reference | Grouped scenario routing; fidelity remains in owning subsections | §6.13 |

**Fidelity labels**:

| Label | Meaning |
|---|---|
| `Native-stable` | Generated PPTX uses the corresponding native DrawingML property or object and retains the documented semantics within the technique-specific limits. |
| `Native-normalized` | Export targets an editable DrawingML equivalent, but normalizes the SVG into another structure such as a freeform, run property, or simplified paint/effect. |
| `Approximate` | DrawingML has no exact SVG equivalent; export targets the intended effect through a documented approximation, and material differences require output review. |
| `Bake-required` | The runtime effect is outside the native contract; pre-render it into an image or rebuild it with explicit supported geometry. |

**Reading rules**:

- **Required** / **Forbidden** statements are non-negotiable technical boundaries.
- **Conditional** contracts apply only when the corresponding feature is used.
- **Reference — not a constraint** passages expose capabilities and recipes; they do not require every page or visual style to use them.
- The locked `visual_style` controls whether and how strongly a compatible effect is used. It never expands the technical boundary.

**Hard rule — generated authoring is fail-closed**: `svg_output/` and reusable
template SVGs may use only properties and conditional interfaces explicitly
listed in this file. `svg_quality_checker.py` rejects unknown inline visual
properties and conditional contracts that have no reliable compatibility
mapping; documented fallback forms remain valid and receive warnings.

**Default — recommended authoring and supported input stay separate (may
preserve supported input)**: generated SVG uses one predictable default
spelling, while converter-supported equivalent spellings remain valid input.
The checker may recommend normalization, but such warnings do not require
modification or block export. Only invalid, unsafe, or unreliably convertible
input is an error; do not remove converter support to enforce a narrower
generation preference.

**Hard rule — one-way fidelity vocabulary**: the labels above describe the
`svg_output/` → generated PPTX path. They do not promise reconstruction of the
original SVG syntax, `<defs>` graph, `<use>` structure, path commands, or
`<tspan>` layout after PPTX-to-SVG import, nor pixel identity across PowerPoint,
LibreOffice, Keynote, and WPS.

**Hard rule — capability boundary**: a recipe never expands converter support.
Use only the target elements and syntax documented by each conditional
contract. Unsupported element tags fail preflight; browser-rendered attributes
outside these contracts must not be assumed to have a DrawingML mapping.

---

## 1. Required Foundation, Forbidden Features, and Conditional Interfaces

### 1.0 Text characters: must be well-formed XML

SVG is strict XML. Two rules for all text and attribute values:

| Character category | Required form | Forbidden form |
|---|---|---|
| Typography & symbols (em dash, en dash, ©, ®, →, ·, NBSP, full-width punctuation, emoji…) | **Raw Unicode characters** — write `—` `–` `©` `®` `→` directly | HTML named entities — `&mdash;` `&ndash;` `&copy;` `&reg;` `&rarr;` `&middot;` `&nbsp;` `&hellip;` `&bull;` etc. |
| XML reserved characters (`&`, `<`, `>`, `"`, `'`) | **XML entities only** — `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`) | Bare `&` `<` `>` (e.g. `R&D`, `error < 5%`) |

One offending character invalidates the file and aborts export.

**Structural blacklist** (in addition to the character rules above):

| Banned Feature | Description |
|----------------|-------------|
| `mask` | Masks |
| `<style>` | Embedded stylesheets |
| `class` | CSS selector attributes |
| External CSS | External stylesheet links |
| `<foreignObject>` | Embedded external content |
| `textPath` | Text along a path |
| `@font-face` | Custom font declarations |
| `<animate*>` / `<set>` | SVG animations |
| `<script>` / event attributes | Scripts and interactivity |
| `<iframe>` | Embedded frames |

The blacklist above is exhaustive for globally forbidden structural syntax.
It is not a positive allowlist for every browser-rendered property. Features
that require a restricted form are valid only under the conditional contracts
below; unlisted visual properties are unsupported.

**Hard rule — inline visual-property allowlist**:

| Property family | Allowed inline `style` properties |
|---|---|
| Paint and line | `fill`, `stroke`, `stroke-width`, `stroke-dasharray`, `stroke-linecap`, `stroke-linejoin`, `fill-opacity`, `stroke-opacity`, `vector-effect` |
| Text | `font-family`, `font-size`, `font-weight`, `font-style`, `text-anchor`, `letter-spacing`, `text-decoration` |
| Alpha and definition paint | `opacity`, `stop-color`, `stop-opacity`, `flood-color`, `flood-opacity` |
| Literal geometry | The element-specific properties in §2.1 |
| Preview-only | `shape-rendering`; it does not change native geometry |

**Default — one generated value spelling (may preserve supported input)**: the
table allows inline placement of those property names. New generated paint
prefers the spelling in §6.2 whether it appears as an attribute or inside
`style`. Converter-compatible aliases remain valid input in both locations and
produce recommendation warnings rather than errors.

Conditional properties with a required XML form stay out of inline style:
write `filter="url(#id)"`, `clip-path="url(#id)"`, and
`marker-start` / `marker-end` as direct attributes. `!important`, unknown CSS
properties, blend modes, isolation, and backdrop filters fail quality check.

The table registers property names, not arbitrary CSS values. Text property
values and their element-specific placement are a closed grammar owned by
§6.7; unknown or unmapped declarations on `<text>` / `<tspan>`, and unsupported
inherited text properties, fail both Checker preflight and native export.

> **`marker-start` / `marker-end` is conditional** — see §1.1.
>
> **`clipPath` on `<image>` is conditional** — see §1.2.
>
> **Static same-document `<use>` is conditional** — see §1.3.
>
> **Imported native-shape metadata is conditional** — see §1.4.
>
> **Authored native preset fragments are conditional** — see §1.5.
>
> **Inline CSS geometry, simple gradients, filters, and approximate group
> opacity are conditional** — see §2 and §6.
>
> **PPT preset patterns and native chart/table/template metadata are
> conditional** — see §7.

DrawingML has no arbitrary per-pixel alpha-compositing path. Effects that rely
on one, including text-knockout image fills and arbitrary alpha composites,
must be baked into a raster asset before SVG export.

---

### 1.1 Line-end Markers (Conditional Contract)

`marker-start` and `marker-end` are supported on `<line>` and `<path>` only
when the referenced marker fits this native-arrow contract:

| Concern | Required form |
|---|---|
| Reference | Exact local `url(#id)` to a `<marker>` in `<defs>` |
| Orientation | `orient="auto"` or `orient="auto-start-reverse"`; the latter reverses `marker-start` while behaving like `auto` at `marker-end` |
| Shape | One direct shape representing a DrawingML `triangle`, `stealth`, `arrow`, `diamond`, or `oval` line end: a 3-vertex `<polygon>` / closed path (triangle), a simple concave 4-vertex `<polygon>` / closed path (stealth), an open 3-vertex path (arrow), a simple convex 4-vertex `<polygon>` / closed path (diamond), or one `<circle>` / `<ellipse>` (oval) |
| Path grammar | Use one explicit `M`/`L` command per vertex. Triangle, stealth, and diamond paths end in `Z`; arrow paths remain open after the third vertex. Do not use `H`, `V`, curves, or an implicit multi-point `L` command inside a marker path |
| Color parity | Triangle, stealth, diamond, and oval use a fill matching the parent line stroke. The open arrow uses `fill="none"` and a stroke matching the parent line stroke. DrawingML line ends inherit the line color |

The converter maps these five shapes to their corresponding DrawingML line-end
types. Prefer `<polygon>` for the closed triangle, stealth, and diamond forms;
the open arrow form requires `<path>`. Four-vertex shapes must be simple and
non-degenerate: convex geometry maps to diamond and concave geometry maps to
stealth. Checker and exporter preflight consume this same contract; other
marker shapes have no native mapping and block export instead of being silently
dropped. PPTX import likewise accepts only these five DrawingML line-end types
(plus `none`); an unknown source value stops import instead of being relabeled
as a supported shape. Optional DrawingML `w` and `len` values default to `med`;
explicit values must be `sm`, `med`, or `lg`, and invalid source buckets stop
import instead of being normalized to `med`.

---

### 1.2 Image Clipping (Conditional Contract)

`clip-path` has a native picture-geometry mapping only on SVG-namespace
`<image>` elements (plus the exact imported crop wrapper defined under Images)
and only under this contract:

| Concern | Required form |
|---|---|
| SVG-namespace `<clipPath>` defined inside `<defs>` | Converter looks up one exact local id; missing, duplicate, foreign-namespace, or malformed references fail |
| Contains exactly one direct SVG-namespace supported shape child | Multiple shapes are not composited |
| Shape is one of: `<circle>`, `<ellipse>`, `<rect>` (optional rx/ry), `<path>`, `<polygon>` | These map to DrawingML geometry (preset or custom) |
| No `clip-rule` or `fill-rule`, whether direct or in inline `style` | DrawingML picture geometry has no equivalent winding-rule control |
| Used only on `<image>` or an exact imported crop wrapper | Shapes, groups, text, and generalized nested SVG targets are **forbidden** |

| SVG clip shape | DrawingML output |
|---|---|
| `<circle>` / `<ellipse>` | Full-frame `<a:prstGeom prst="ellipse"/>`; the child must exactly cover the image frame. A `userSpaceOnUse` circle requires a square physical frame; a normalized `objectBoundingBox` circle may fill any frame |
| `<rect>` / `<rect rx="..."/>` | A plain full-frame rect is a compatible no-op; rounded form maps to full-frame `<a:prstGeom prst="roundRect"/>` with one physical radius adjustment. The rect must exactly cover the image frame and cannot express non-uniform physical corner radii |
| `<path>` / `<polygon>` | `<a:custGeom>` with coordinates mapped into the image frame |

`clip-path` on shapes, groups, or text is forbidden; author the target geometry
directly instead. Use a path/polygon clip when the intended contour does not
cover the full picture frame. A contour that depends on even-odd or another
explicit winding rule is outside this mapping and must be rebuilt as one
unambiguous visible contour or pre-rendered.

---

### 1.3 Static Same-Document `<use>` (Conditional Contract)

**Expansion contract**: Static local reuse is compile-time authoring shorthand. `finalize_svg.py` and
native export replace each qualifying instance with cloned primitive content;
PPTX-to-SVG import emits the resulting primitives and does **not** reconstruct
the original `<use>` / `<symbol>` structure.

| Concern | Required form |
|---|---|
| Reference syntax | Author new SVG with the SVG 2 form `href="#id"`. Legacy `xlink:href="#id"` remains read-compatible and Live Preview normalizes it to `href`; if both attributes exist, their values MUST match. |
| Referenced target | One of `<symbol>`, `<g>`, `<use>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<polygon>`, `<polyline>`, `<text>`, or `<image>`. Nested local `<use>` is recursively expanded. |
| Instance position | Generated `<use x>` / `<use y>` use finite unitless values; an explicit `px` suffix is read-compatible. Omitted values default to `0`. |
| Symbol viewport | A referenced `<symbol>` MUST have a finite four-number `viewBox` with positive width/height. Its `<use>` MUST have positive finite unitless `width` and `height`; an explicit `px` suffix is read-compatible. |
| Aspect ratio | Default/aligned `meet` values and plain `preserveAspectRatio="none"` are supported. `slice`, `refX`, and `refY` are forbidden. |
| Viewport boundary | Symbol artwork MUST stay inside its `viewBox`; expansion does not reproduce symbol overflow clipping. |
| Internal references | Author exact `href="#id"` and `url(#id)` fragments. The expander also reads legacy `xlink:href="#id"` and rewrites all instance-local cloned IDs. |
| Structural metadata | Neither the `<use>` instance nor its referenced subtree may carry `data-pptx-layer*`, chart/table replacement metadata (`data-pptx-replace-with`, `data-pptx-replacement-*`, `data-pptx-import-source`, or `data-pptx-fallback-*`), or `data-pptx-placeholder*`. Author those objects directly instead of reusing them. |
| Safety limits | A reachable reference chain may contain at most 64 instances, and one SVG may expand at most 10,000 local `<use>` instances. |

**Forbidden — unsafe local references**:

- External/file/data URLs, missing targets, conflicting `href` / `xlink:href`,
  unsupported target elements, and circular reference chains
- Duplicate IDs on the referenced target, the `<use>` instance, or anywhere in
  the reused subtree
- Quoted/whitespace CSS fragment variants such as `url('#id')`; use exact
  `url(#id)` when an internal paint/filter/clip reference must be rewritten

**Contract example**:

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <defs>
    <symbol id="statusDot" viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet">
      <circle cx="10" cy="10" r="8" fill="#16A34A"/>
    </symbol>
    <g id="legendRow">
      <rect width="120" height="32" rx="8" fill="#F1F5F9"/>
      <text x="42" y="22" font-size="16" fill="#0F172A">Ready</text>
    </g>
  </defs>
  <use href="#statusDot" x="80" y="120" width="32" height="32"/>
  <use href="#legendRow" x="120" y="120"/>
</svg>
```

---

### 1.4 Imported Native PowerPoint Shapes (Conditional Contract)

`pptx_to_svg.py` emits rendering-neutral metadata when a visible SVG object
originates from `p:sp`, `p:cxnSp`, or `p:grpSp`. This contract is for lossless
import SVGs and unchanged imported objects that remain Slide-local or inside a
slot during mirror restoration. Ordinary authored SVG does not need these
attributes, and no separate source-payload opt-in marker exists.

| Metadata | Placement | Required behavior |
|---|---|---|
| `data-pptx-object` | Logical `<g>` and native carrier | `shape`, `connector`, `group`, or `picture`; never infer the object kind from path appearance. |
| `data-pptx-shape-id` + `data-pptx-shape-scope` | Logical `<g>` and carrier | Preserve the source part-scoped identity. Export remaps duplicate Master/Layout/Slide ids into page-unique ids before restoring connector references. |
| `data-pptx-frame="x y width height"` | Logical `<g>` and carrier | Own native `a:xfrm` position and size. Values use sufficient precision for exact EMU recovery; path bounds, stroke, markers, shadows, and text glyph bounds never replace this frame. |
| `data-pptx-prst` | Preset carrier and logical `<g>` | One of the locked 187 DrawingML `ST_ShapeType` values. |
| `data-pptx-av-*` | Preset carrier and logical `<g>` | Preserve the complete validated DrawingML adjustment formula, including non-`val` formulas. |
| `data-pptx-part="geometry"` | One hidden carrier path | The single native export authority for frame, base fill/line/effect, preset/custom geometry, and object identity. |
| `data-pptx-part="geometry-preview"` / `geometry-detail` | Visible preview group/paths | Render the preset's independent path fill/stroke layers. A hash-locked preview group may mirror the carrier's one filter so a multi-path preset renders one aggregate imported effect; these elements are never emitted as duplicate PowerPoint shapes. |
| `data-pptx-preview-sha256` | Logical preset `<g>` and carrier | Detect edits to visible preset paths or paint. A stale preview fails quality check/export instead of silently restoring old native metadata. |
| `data-pptx-geometry-kind="custom"` + `data-pptx-custgeom` | Custom-geometry carrier | Preserve the validated original `a:custGeom` subtree. If the visible path hash is unchanged, export restores formulas, handles, connection sites, text rectangle, and path list exactly; edited paths compile from current SVG geometry. |
| `data-pptx-start/end-shape-id/site` | Connector logical `<g>` and carrier | Restore `a:stCxn` / `a:endCxn` after scoped shape-id allocation. A connector may retain one zero frame axis; it must not be expanded from visible stroke or marker bounds. |
| `data-pptx-shape-style` | Native carrier | Preserve a relationship-free `p:style` independently of text, including shapes with no visible text. |
| `data-pptx-effect-status="unsupported"` + `data-pptx-effect-reason` | Imported `p:sp` / `p:cxnSp` logical object and native carrier; imported `p:pic` carrier and logical object; imported `p:grpSp` logical group; imported table `p:graphicFrame` logical group | Record why an encountered source object or text-run `effectLst` / `effectDag` cannot enter the registered target-specific effect mapping without changing semantics. Checker and export stop with the recorded reason; these attributes are diagnostics, not a preserved effect payload or authoring syntax. |
| `metadata[data-pptx-part="txbody"]` | Logical shape `<g>` | Preserve unchanged `p:txBody`, including an empty text body. Content, whitespace, positioning, visible typography, or incompatible child-topology edits invalidate the payload. A source payload with run-level effects then blocks checker/export instead of losing those effects; an effect-free payload uses the normal SVG text fallback. |

One effect reason remains its existing plain token. If one imported object has
multiple independent unsupported reasons, both marker copies store the same
deduplicated, lexicographically sorted compact JSON string array in
`data-pptx-effect-reason`; adding a later reason must not overwrite an earlier
one. This array is still diagnostic metadata, not an authoring surface.

**Import/authoring representation split**:

| Representation | Contract |
|---|---|
| Lossless import SVG | Keep complete native payload, hidden carriers, and preview evidence in the temporary analysis workspace. This is the round-trip source, not the model-facing authored page. |
| Lightweight authoring projection | Exclude opaque payload and duplicate hidden carriers from model context while retaining visible shape intent and logical ids needed to locate an adopted object in the lossless import. It is not an export source. |
| `standard` / `fidelity` output | Use the compact authored-preset contract (§1.5) for newly authored stock shapes; do not transplant opaque import payload or source topology. |
| `mirror` output | Keep the expanded lossless representation and supported imported metadata only on unchanged Slide-local/slot objects. Expand fixed Master/Layout group wrappers into direct semantic atoms while preserving source ownership, paint order, and visible appearance. |

**Hard rule — structural-layer boundary**: An unchanged imported logical object
may keep currently supported metadata while it remains Slide-local or inside a
slot. An imported logical `<g>` cannot be assigned to Master/Layout because
those layers require direct semantic atoms. Mechanically expand a fixed-layer
source group into direct atoms, rebuilding a preset when supported and
otherwise retaining the visible SVG fallback. A newly authored compact preset
`<g>` from §1.5 is the sole group exception: validation proves that it compiles
to exactly one native shape/connector. Do not use this normalization to change
ownership or appearance.

**Hard rule — selective payload**: Do not copy every imported metadata block into
an authored template. Keep the full lossless import SVG separately as the
audit/fallback source. Mirror may reuse only metadata already supported by the
converter on unchanged Slide-local/slot objects; unsupported or edited objects
use the current SVG fallback. `data-pptx-replace-with` remains reserved for the
optional PowerPoint-native Chart/Table replacement contract.

**Registry and rendering rules**:

- The hash-locked shared registry must equal the independent 187-value shape
  catalog. Missing, duplicate, unknown, or corrupt definitions fail closed.
- Preset preview paths come from the shared DrawingML formula evaluator; do not
  add per-shape Python geometry handlers.
- Preset size is controlled only by `data-pptx-frame` / `a:xfrm`. Adjustment
  formulas control the contour inside that frame and are not rescaled when the
  frame changes.
- A group transform may move, scale, rotate, or flip the complete logical
  shape without invalidating its preview fingerprint. Editing a generated
  `geometry-detail` path directly is unsupported unless the carrier metadata
  and preview fingerprint are regenerated together.
- Unknown or malformed SVG transform operations fail closed. DrawingML cannot
  represent arbitrary shear, so a non-orthogonal transform must stop native
  export instead of being silently approximated as rotation and scale.
- Opaque XML payloads containing any `r:*` relationship attribute are never
  copied into a new slide part. Relationship-bearing text content and
  shape-level `a:blipFill` use the existing rebuilt visual fallback and are
  not covered by atomic `p:sp + p:txBody` restoration.
- Unknown future presets and explicit `unsupported` geometry status never
  downgrade silently to `rect`; native export stops with the recorded reason.

**Fidelity boundary**: native preset/custom geometry, logical frame, scoped
identity, connector topology, and relationship-free unchanged horizontal
text-body semantics on ordinary shape fills are `Native-stable`. The SVG
preview paint for gradient/pattern
`darken`/`lighten` layers is `Native-normalized`; original group child
coordinates, shape-level image-fill reconstruction, and vertical-text
reconstruction are also normalized rather than byte-identical OOXML.

---

### 1.5 Authored Native PowerPoint Presets (Conditional Contract)

New SVG pages and project-owned canonical reusable templates may opt one
complete geometric object into a native DrawingML preset through the
deterministic fragment helper. Selection behavior lives in
[`native-shape-authoring.md`](./native-shape-authoring.md); this section owns
the machine contract. This compact canonical form describes the intended
preset, frame, adjustments, and paint once, keeps only registry-generated
visible SVG paths, and embeds no source OOXML or serialized preview fingerprint.

| Metadata / structure | Required behavior |
|---|---|
| `data-pptx-authoring="preset"` | Appears once on the logical `<g>`; distinguishes strict project authoring from legacy/imported metadata. |
| `data-pptx-object` | `shape` or `connector`; connector-family presets must use `connector`, and `connector` must use a connector-family preset. Authored connectors require `fill="none"` plus a visible stroke and export as unconnected `p:cxnSp`. |
| `data-pptx-prst`, `data-pptx-frame`, `data-pptx-av-*` | Generated together from the locked registry and written once on the logical group. The frame is the helper's exact four-part, space-separated ordinary-decimal spelling and remains authoritative even when visible path bounds differ; commas, scientific notation, leading `+`, and redundant decimal spellings are rejected. |
| Local `fill` / `stroke` plus supported paint attributes | Base paint is written once on the group; a visible stroke also carries an explicit width. Canonical page/template authoring keeps channel paint local. Compatible ancestor paint/opacity may compose under the general SVG rules and receives a recommendation warning. |
| Ordered direct `<path>` children | Browser-visible registry layers only. Each child writes just its required path-level fill/stroke override; labels and decorations stay outside the atomic group. |
| No carrier / wrapper / fingerprint | `data-pptx-part`, hidden geometry carriers, preview wrappers, and `data-pptx-preview-sha256` belong to expanded import/compatibility transport, not canonical project authoring. |

Generate one fragment at a time:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow \
  --frame 160 210 320 112 \
  --fill "#2563EB" \
  --stroke none \
  --adjust "adj1=val 50000"
```

**Hard rule — helper-only metadata**: never add or edit authored preset
metadata or registry paths by hand. The compact helper output is atomic.
Regenerate it when preset, frame, adjustment, fill, stroke, or stroke width
changes. Replace the whole fragment with ordinary SVG when free contour editing
is required.

Template ownership metadata is orthogonal to preset geometry. After inserting
the complete helper output, `create-template` may add only the registered
`data-pptx-layer`, `data-pptx-editable`, `data-pptx-placeholder-carrier`, or
`data-pptx-role` attribute needed by the surrounding structured contract. It
must not change preset/frame/adjustment/paint metadata or any direct path.

**Reusable-template boundary**: a project-owned canonical template may retain
one complete helper-generated atomic fragment when the stock preset is an exact
semantic match and its paint stays inside the authoring boundary below. The
fragment is an executable exemplar and one semantic atom, not a freely editable
template primitive. It may be Slide-local, the one carrier of an `object` slot,
or a direct Master/Layout fixed atom. An adaptation may reuse it unchanged only
when preset, frame, adjustments, and paint are unchanged; otherwise regenerate
the whole fragment with the helper.
Imported, mirror, and third-party templates are never upgraded by contour
inference.

**Hard rule — visible page closure**: the helper prints a complete visible
fragment to stdout; export never invents its preview. The main Agent inserts
that output into the hand-authored page or canonical reusable template. The
helper cannot write a project, select layout, or generate a page.

**Authoring paint boundary**: v1 accepts `none` or six-digit solid HEX fill and
stroke, optional fill/stroke opacity, stroke width, line cap, and line join.
Generated pages take colors from `spec_lock.md`; `create-template` authored
templates take them from the confirmed brief and template `design_spec.md`.
Use ordinary SVG for gradients, patterns, filters, or other treatments outside
this narrow contract. Registry-derived multi-path darken/lighten colors are
authorized derivatives of the locked base paint and do not count as color
drift. Mirror preserves source paint under §1.4 instead.

**Validation**: quality check and export both rerender authored fragments from
`preset + frame + adjustments + group paint` and compare every visible path and
path-level paint override directly. Registry-path edits, geometry metadata that
leaves those paths stale, unknown adjustments, out-of-range frames/transforms,
zero-scale transforms, and shear/skew fail closed. Export expands the validated
compact group only in memory and reuses the lossless native-shape conversion
path. Older authored carrier/preview fragments remain compatible as ordinary
Slide-local input and
receive a non-blocking migration warning; they do not gain the new compact
group's structured-atom exception. `pptx_to_svg` expanded output remains the
lossless round-trip form and is not warned as authored input.

**Fidelity boundary**: an unchanged authored fragment is `Native-stable` as
one `p:sp` or `p:cxnSp`. Text remains outside the atomic fragment and may export
as a grouped editable text box. Authoring v1 creates only unconnected
`p:cxnSp`; it does not accept hand-written endpoint/site metadata. An
`actionButton*` preset maps visual geometry only. Preset appearance never
invents connector attachment, action behavior, navigation targets, or
hyperlinks.

---

## 2. Conditional Compatibility Mappings

### 2.1 Literal Geometry Lengths and Inline Geometry

**Hard rule — direct geometry length grammar**: New generated SVG writes the
following XML geometry values and `stroke-width` as finite unitless ordinary
decimals in the page `viewBox` coordinate space, for example `x="120"` and
`stroke-width="2"`. The explicit `px` suffix is read-compatible and receives a
recommendation warning. No other unit is registered for this surface.

| Element / surface | Direct length attributes |
|---|---|
| `<svg>`, `<rect>`, `<image>`, `<use>` | `x`, `y`, `width`, `height`; `<rect>` also `rx`, `ry` |
| `<circle>` | `cx`, `cy`, `r` |
| `<ellipse>` | `cx`, `cy`, `rx`, `ry` |
| `<line>` | `x1`, `y1`, `x2`, `y2` |
| `<text>` / positional `<tspan>` | `x`, `y`; `<tspan>` also `dx`, `dy` |
| Any supported painted element | `stroke-width` |

`width`, `height`, `r`, `rx`, `ry`, and `stroke-width` must be non-negative;
the stricter positive `<use>` symbol-viewport rule remains in §1.3. `pt`,
`pc` / `pica`, `in`, `cm`, `mm`, `q`, `em`, `rem`, percentages, unknown units,
non-finite values, expressions, scientific notation, leading plus signs, and
trailing decimal points are invalid here even when generic SVG/CSS defines
them. A missing attribute may use its documented SVG/project default; an
explicitly supplied invalid value never falls back to that default.

The following geometry properties may appear in the same element's
`style="..."`. The pipeline materializes them as
XML geometry attributes before SVG post-processing and native PPTX conversion.
An inline geometry declaration overrides an existing same-name XML attribute.

| Element | Recognized properties |
|---|---|
| `<rect>` | `x`, `y`, `width`, `height`, `rx`, `ry` |
| `<circle>` | `cx`, `cy`, `r` |
| `<ellipse>` | `cx`, `cy`, `rx`, `ry` |
| `<image>` | `x`, `y`, `width`, `height` |
| `<svg>` | `x`, `y`, `width`, `height` |
| `<use>` | `x`, `y`, `width`, `height` |

**Hard rule — inline geometry grammar**: every non-zero value is one finite
`px` literal, such as `120px` or `-8.5px`; exact zero may be unitless. `width`,
`height`, `rx`, `ry`, and `r` must be non-negative. Percentages, `auto`,
`calc()`, `var()`, `!important`, `inherit`, and every other unit are forbidden.
Do not put geometry on an unsupported element: line endpoints, text positions,
path data, and polygon/polyline points remain XML attributes.

**Forbidden — CSS geometry cascade**: `<style>`, `class`, selector rules,
external stylesheets, and imported styles remain forbidden. This contract is
only for literal declarations in an element's own `style` attribute; PPT Master
does not compute CSS cascade or custom properties. Root canvas authority remains
the `viewBox`, regardless of root `<svg>` compatibility width/height values.

### 2.2 Group Opacity Compatibility

**Default — descendant alpha (may preserve compatible group opacity)**: New
`svg_output/` and reusable templates put alpha on the affected descendant
paint, text run, picture, or supported effect. DrawingML has no isolated
group-alpha model, so overlapping descendants can look different when one
group value is distributed across them.

The converter nevertheless accepts `<g opacity="...">` and inline group
`opacity` by multiplying group alpha into descendants. That path is
`Approximate`; nested group/child alpha multiplies, and `--native-charts-and-tables`
rejects transparent native table/chart markers. The quality checker reports a
non-blocking fidelity warning so existing or intentionally authored input can
continue without modification.

---

## 3. Canvas Format Quick Reference

> See [`canvas-formats.md`](canvas-formats.md) for the full format table (presentations / social / marketing) and the format-selection decision tree.

---

## 4. Required Page Contract and Conditional Packaging

### 4.0 Complete Page-Design Contract

| Concern | Requirement |
|---|---|
| Visible slide result | The completed `svg_output/<slide>.svg` MUST contain every visible text, image, shape, diagram, chart/table fallback, background, and template-derived layout element intended for that slide. External visual assets are valid when the SVG references them explicitly. |
| Template/control inputs | Templates, `design_spec.md`, and `spec_lock.md` guide authoring. Do not depend on them to add visible elements after the page SVG is complete. |
| PPTX translation | The exporter may map represented SVG content to DrawingML/native objects and deduplicate represented elements into Master/Layout/Slide parts. It MUST NOT invent visible slide content absent from the SVG. |
| Excluded package behavior | Speaker notes, animations, transitions, narration audio, PPTX relationships, and direct native-PPTX workflows remain separately owned. They are not part of the SVG page-design contract. |

**Hard rule — page-design closure**: A final page SVG is the sole visual/design authority for that page on every SVG-authoring route. SVG is not the authority for the entire PPTX package.

### 4.1 Semantic SVG Marker Contract

Semantic markers are minimal compiler hints orthogonal to native SVG semantics. Free-design and brand-only pages use flat export, declare one canonical root `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`), and omit Master/Layout/layer/placeholder markers. On deck/layout template routes, root Master/Layout identity, atomic layer elements, grouped slots, and native-object metadata are authoritative and read first; each page carries its final structured contract from the start of SVG authoring and omits `data-pptx-page-role`. Add `data-pptx-role` only when no specialized marker expresses the required page-frame behavior; the element also uses a stable unique `id`. Do not classify ordinary page content or move visible facts out of SVG attributes/text into metadata. See [`semantic-svg.md`](semantic-svg.md) for the canonical vocabulary and examples.

- **Canvas authority**: New authoring writes the root canvas exactly as
  `viewBox="0 0 W H"`, using single spaces and positive ordinary-decimal integer
  pixels from the selected project/template lock. Numerically identical SVG
  spellings (integral decimals, exponent or leading-plus notation, and comma
  separators) are compatible input and receive a normalization warning.
  Positive fractional dimensions are also read-compatible for custom slide
  sizes reconstructed from PPTX; export quantizes them once at
  `1 SVG px = 9,525 EMU`. Missing/malformed/non-finite values, a non-zero
  origin, non-positive dimensions, or dimensions outside PowerPoint's supported
  slide-size range are errors. Every public page and internal Layout prototype
  in one build MUST use the same numeric canvas and match `spec_lock.md`
  `canvas.viewBox`; standalone templates match `design_spec.md`
  `canvas_viewbox`. Root `width` and `height` are optional and do not override
  the `viewBox`. Root `<svg>` `transform` is forbidden; apply transforms to
  child elements or groups. This root-page rule does not replace the separate
  nested-crop and `<symbol viewBox>` contracts.
- **Font portability**: font families used by the deck must resolve to installed
  export faces. `@font-face` remains forbidden; the typography contract lives in
  [`strategist.md §g`](strategist.md).
- **Icon placeholders**: `<use data-icon="library/name">` is a pipeline-specific
  form, distinct from local SVG reuse. Follow the contract in
  [`../templates/icons/README.md`](../templates/icons/README.md).
- **Local reuse**: ordinary same-document `<use>` follows §1.3.

### 4.2 Conditional Editability and Package Promotion

These forms are needed only when the stated PPT behavior matters:

| Desired behavior | Required form |
|---|---|
| One editable PPT text frame with mixed inline formatting | Put the logical line in one `<text>` with non-positional `<tspan>` children. A `<tspan>` with `x`/`y`/`dy` starts a new positioned line. Evenly `dy`-stacked lines that repeat the parent `<text>`'s `x` stay in one frame: equal effective `font-size` may flow in the current paragraph, while a font-size change, list marker, or accepted larger gap starts a new paragraph. An unmergeable gap or mismatched `x` flattens to separate frames. Separate `<text>` elements stay valid when separate frames are intended. |
| Stable object grouping or object-level animation anchor | Wrap the intended object in `<g id="...">`. Content grouping is **mandatory** per §4.3 — a top-level `<g id>` is also the animation anchor; it is not an optional convenience. |
| Native PowerPoint background promotion | Outside structured mode, the first eligible visual layer may be a direct full-canvas `<rect>` or one inside a simple single-child group. Its fill must have a registered native mapping (solid, linear/radial gradient, or preset pattern), and it must have no transform, filter, clip, rounding, or visible stroke. Export writes the fill as Slide `p:bg`; image elements remain pictures. Structured routes use the narrower explicit solid-background ownership contract in §7. |
| Free-design / brand-only PowerPoint structure | Use `pptx_structure.mode: flat`. Keep every represented object Slide-local; export materializes one clean project-owned Master plus one Blank Layout from the current lock, removes stock content placeholders/Layout inventory, and retains only the standard date/footer/slide-number capability hooks. Do not author Master/Layout identities, layers, or placeholder slots. |
| Reusable template-based PowerPoint Layout | Select one complete authoring SVG per page in `page_layouts`, declare each unique Master/Layout definition once, and assign pages through `page_pptx_layouts`. Strict preserves the prototype contract; adaptive retains its Master and may define and assign a new explicit Layout key during page authoring. Non-mirror skin follows `spec_lock`. |

**Hard rule — supported shape conversion**: Every PPT editability claim in this specification refers to the project converter reading `svg_output/` and emitting native DrawingML. `svg_final/` is a self-contained visual preview that may be inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is unsupported; do not narrow the authoring contract to its undocumented SVG subset.

### 4.3 Element Grouping (Mandatory)

Wrap logically related Slide-local elements in top-level `<g id="...">` groups. This is **required on every generated page**, not an optional convenience: it produces real PowerPoint groups in the exported PPTX and gives each content unit a stable animation anchor. Plain `<g>` is the grouping primitive; keep alpha on individual descendants per §2.2. Flat free-design/brand-only pages use only ordinary semantic groups. On structured template pages, direct atomic Master/Layout elements are the required exception and a top-level slot `<g>` is already a semantic group. Nested implementation groups inside one named content unit may remain anonymous unless another specialized contract requires an id; they are not independent animation targets.

**Semantic-group rule**: direct Slide content uses semantic groups. Aim for **3–8 ordinary top-level content `<g id>` groups per slide**; on structured template pages, slot groups and atomic Master/Layout objects are excluded. Each ordinary group becomes one entrance step under the chosen animation trigger. Leaving Slide-local titles, body lines, list items, cards, or decorative clusters as ungrouped top-level atoms is an authoring-contract violation reported as an aggregate Checker warning.

**Structural atoms and slots are excluded automatically.** `data-pptx-layer` and `data-pptx-placeholder` semantics are read first; otherwise explicit `data-pptx-role` values (`background`, `decoration`, `header`, `footer`, `chrome`, `watermark`, `page-number`, `logo`) mark Slide-local static framing (§4.1, [`semantic-svg.md`](semantic-svg.md)). A normal slot group has exactly one direct compatible carrier; several drawing atoms require the explicit composite `object` proxy fallback. Native chart/table carrier groups retain their specialized §7 contract.

**What to group** (one `<g id>` per unit):

| Grouping unit | Contains |
|---|---|
| Card / panel | Background rect + optional shadow (only if it floats over a photo/colored panel, §6.4) + icon + title + body text |
| Process step | Number/marker + icon + label + description |
| List item | Bullet / number + icon + title + description |
| Icon-text combo | Icon element + adjacent label |
| Page header | Title + subtitle + accent decoration |
| Page footer | Page number + branding |
| Decorative cluster | Related decorative shapes (rings, dots, orbs) |

An authored native preset fragment (§1.5) is already an atomic `<g id>` and
counts as one content group. Keep it top-level when it stands alone. When it
needs a label or decoration, place the preset and those siblings inside a
separate parent content group; never put them inside the preset group itself.

**Forbidden**:

- One giant `<g>` around the whole slide (collapses to a single animation step).
- Many ungrouped Slide-local `<rect>` / `<text>` / `<path>` atoms — they have no stable sidecar target and selection/editing degrades. Primitive fallback applies only when the root contains no top-level `<g>` at all; it is capped at 8 visible primitives.
- One group per icon / text line / mark (too many steps).
- Anonymous top-level groups — every top-level semantic group needs a descriptive `id`.

**Naming — required.** A descriptive, page-unique `id` on every top-level content `<g>` (`card-1`, `step-discover`, `header`, `footer`) is mandatory; it is the stable SVG-side animation and trace anchor. An anonymous top-level group still converts, but `animations.json` cannot reference it; an anonymous one-child implementation wrapper may also flatten. Primitive fallback is unrelated and applies only to roots with no top-level groups.

```xml
<g id="card-benefits-1">
  <!-- Shadow only if the card floats over a colored panel; on flat white, omit it. -->
  <rect x="60" y="115" width="565" height="260" rx="20" fill="#FFFFFF" filter="url(#shadow)"/>
  <use data-icon="chunk-filled/bolt" x="108" y="163" width="44" height="44" fill="#0071E3"/>
  <text x="105" y="270" font-size="56" font-weight="bold" fill="#0071E3">10×</text>
  <text x="250" y="270" font-size="30" font-weight="bold" fill="#1D1D1F">Faster</text>
  <text x="105" y="310" font-size="18" fill="#6E6E73">Reduce production time from days to hours.</text>
</g>
```

---

## 5. Workflow Authority

The serial post-processing and export workflow belongs to
[`SKILL.md` Step 7](../SKILL.md). This file defines SVG authoring boundaries
and intentionally does not mirror commands, flags, or output behavior.

---

## 6. Advanced SVG Effects and Authoring Techniques

**Reference — not a constraint**: “Advanced” means capability depth, not rarity.
Use any compatible technique when it serves the locked visual style and content.

### 6.1 Availability, Precedence, and Fidelity

| Decision layer | Authority |
|---|---|
| Technical validity | Required / Forbidden / Conditional contracts in this file |
| Project values | `<project_path>/spec_lock.md` colors, fonts, icons, and images |
| Aesthetic fit | Locked `visual_style` / `visual_style_behavior` |
| Per-page choice | Content purpose, hierarchy, legibility, semantics, and rhythm |

**Hard rule — illustrative colors**: colors below demonstrate syntax only;
generated pages use matching `spec_lock.md` roles. Fidelity labels are defined
at the front of this document. Review an `Approximate` result in native PPTX
when the effect carries material meaning.

---

### 6.2 Color, Alpha, and Opacity

Compatible paint grammar includes recognized named colors, `rgb()` / `rgba()`,
`hsl()` / `hsla()`, and `#RGB` / `#RGBA` / `#RRGGBB` / `#RRGGBBAA`. The
converter also tolerates legacy bare 3/4/6/8-digit hexadecimal tokens.

**Default — canonical generated paint tokens (may preserve compatible
alternatives)**: New `svg_output/` and reusable template SVGs write solid paint
as uppercase six-digit `#RRGGBB`. `fill` / `stroke` may instead use lowercase
`none` or the exact local reference form `url(#id)`. Named colors, lowercase or
short/alpha HEX, functional colors, and bare legacy HEX remain supported input.
The quality checker prints an optional canonical rewrite as a recommendation
warning; it does not require modification or block export.
Explicit empty, malformed, or unrecognized paint values are errors in both
Checker and exporter preflight; neither converts unknown intent into
`noFill` or default black. Omitted properties still follow their own element
contract, such as SVG's default fill or §6.3's required gradient-stop color.

| Intent | Canonical authoring | Native result / fidelity |
|---|---|---|
| Solid fill or text paint | `fill="#RRGGBB"` | Solid DrawingML paint; `Native-stable` |
| Fill/text alpha | Opaque `fill` + `fill-opacity="0..1"` | Fill/run alpha; `Native-stable` |
| Stroke alpha | Opaque `stroke` + `stroke-opacity="0..1"` | Line/outline alpha; `Native-stable` |
| Gradient-stop alpha | Opaque `stop-color` + `stop-opacity="0..1"` | Per-stop alpha; `Native-stable` |
| Shadow/glow alpha | Opaque `flood-color` + `flood-opacity="0..1"` | Effect alpha; `Native-stable` within §6.4 |
| Picture fade | `<image opacity="0..1">` | Picture `<a:alphaModFix>`; `Native-stable` |
| One atomic whole-object fade | Non-group element `opacity="0..1"` | Alpha compiled into its supported paint/effect channels; `Native-normalized` |
| Pattern alpha | Opaque pattern child paint + child fill/stroke opacity | Conditional; §7 |
| CSS color alpha | Alpha-bearing named/functional/HEX paint | `Native-normalized`; recommendation warning only |
| Group fade | `<g opacity>` compatibility | `Approximate`; fidelity warning; §2.2 |

```text
effective fill alpha
= color alpha × ancestor group opacity × element opacity × fill-opacity
```

**Default — opaque color authority (may preserve compatible alpha colors)**:
New generated SVG puts alpha on the semantic channel that owns it. Existing or
intentional alpha-bearing color tokens remain convertible; they normalize into
the matching DrawingML color/alpha channels.

**Default — channel-specific alpha (may override for one atomic whole-object
fade)**: use `fill-opacity`, `stroke-opacity`, `stop-opacity`, or
`flood-opacity` when only that channel fades. Use element `opacity` only when
an image or one non-group atomic object intentionally fades all of its
supported paint/effect channels together. Do not use element `opacity` as an
alias for `rgba()` on a fill-only object.

**Default — alpha grammar (may preserve compatible alternatives)**: write
`opacity`, `fill-opacity`, `stroke-opacity`, `stop-opacity`, and
`flood-opacity` as finite unitless numbers from `0` to `1`. The converter also
accepts finite numeric values that SVG/CSS clamps into that interval;
`stop-opacity` and `flood-opacity` additionally accept finite percentages. The
checker reports those supported non-default spellings as recommendation warnings.
Malformed or non-finite values are errors in both Checker and exporter
preflight; neither substitutes an opaque default for unknown intent.
`fill="transparent"` / `stroke="transparent"` become no fill/line; use a color
plus alpha when a painted transparent layer must remain represented. Prefer
descendant alpha over group opacity when isolated compositing matters (§2.2).

---

### 6.3 Gradients and Paint Effects

| Concern | Contract |
|---|---|
| Definition | Direct `<linearGradient>` / `<radialGradient>` child of `<defs>` with unique `id` |
| Reference | Exact local `url(#id)` |
| Stops | Direct `<stop>` children; explicit color; finite offset `0..1` or `0%..100%`; optional stop alpha |
| Coordinates | Normalized values / percentages; do not depend on `gradientUnits` user-space geometry |
| Forbidden | External/quoted refs, `href` inheritance, `gradientTransform`, `spreadMethod`, CSS gradients |

| Target | Contract and fidelity |
|---|---|
| `<rect>`, `<circle>`, `<ellipse>`, `<path>`, `<polygon>` fill/stroke | Linear `Native-normalized`; radial `Approximate` |
| `<line>` / `<polyline>` | Gradient stroke only; linear `Native-normalized`, radial `Approximate` |
| `<text>` / non-positional `<tspan>` | Gradient fill only; no gradient text outline |
| `<image>` | No gradient paint; use §6.5 overlays |

Linear export preserves stops/alpha/direction but reduces coordinates to an
angle. Radial export becomes a centered circular gradient and does not preserve
`cx/cy/r/fx/fy`. Gradient strokes remain editable, but PPTX-to-SVG re-import may
retain only the first stop. Stop alpha and element opacity multiply.
The quality checker and exporter preflight both validate definition location,
references, gradient structure, and paint context from the same closed contract.

**Hard rule — non-degenerate gradient geometry**: an `objectBoundingBox`
gradient stroke requires non-zero intrinsic width and height. SVG stroke width
does not expand that object bounding box, so a perfectly horizontal or vertical
gradient ribbon disappears even when its stroke is thick. Author such a ribbon
as a closed shape with gradient `fill`, or use a path whose intrinsic geometry
has both dimensions. Checker and exporter reject the degenerate stroke form.

```xml
<defs>
  <linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#2563EB"/>
    <stop offset="100%" stop-color="#10B981" stop-opacity="0.7"/>
  </linearGradient>
</defs>
<path d="M100 200 C260 80 420 320 620 180" fill="none"
      stroke="url(#flow)" stroke-width="12"/>
```

Preset patterns are a separate PPT interface in §7.

---

### 6.4 Shadows, Glow, and Elevation

Filters are native-effect metadata, not a general pixel-filter surface.

| Concern | Contract |
|---|---|
| Definition/reference | Direct `<defs><filter id="...">` child with unique id; direct `filter="url(#id)"` attribute, never inline style |
| Public targets | `<rect>`, `<circle>`, `<path>`, `<text>` |
| Required primitive | `feDropShadow` or `feGaussianBlur` |
| Required parameters | Explicit `stdDeviation` on either effect primitive; explicit `dx`, `dy`, and `flood-opacity` on `feDropShadow`; explicit `flood-opacity` on `feFlood`; explicit `slope` on linear `feFuncA` |
| Accepted helpers | `feOffset`, `feFlood`, `feComposite`, `feMerge`, `feMergeNode`, `feComponentTransfer`, linear `feFuncA` |
| Alpha transfer | Linear `feFuncA` maps multiplicative `slope` only; `intercept` is unsupported |
| Blur sampling | `feGaussianBlur edgeMode` is unsupported; native effects do not expose the SVG edge-sampling modes |
| Primitive coordinates | Omit `primitiveUnits` or use `userSpaceOnUse`; `objectBoundingBox` coordinates are unsupported |
| Numeric values | Finite unitless values; non-negative `stdDeviation`; finite `dx` / `dy`; `feFuncA slope` within `0..1`; mapped glow `rad = stdDeviation × 9525`, shadow `blurRad = stdDeviation × 2 × 9525`, and shadow `dist = hypot(dx,dy) × 9525` must round into DrawingML `0..27273042316900` |
| Classification | Meaningful non-zero offset → one outer shadow; zero/no offset → one glow |
| Fidelity | `Approximate`; one filter becomes one DrawingML effect |

Flood opacity, linear `feFuncA slope`, and element opacity multiply. The
converter-only historical path may also multiply flood-color alpha and
ancestor group opacity.
Native export does not preserve filter-region, `in/in2/result`, merge order, or
composite topology. Other primitives, multiple independent effects, filters on
`<image>` / `<tspan>` / `<g>` / unsupported targets are forbidden; apply the
effect to supported objects or use explicit layers.
The sole `<g filter>` exception is the hash-locked
`data-pptx-part="geometry-preview"` transport in §1.4: it must be a direct child
of an imported preset object and reference the same filter as that object's one
hidden geometry carrier. The preview is render-only and never becomes a second
PowerPoint object; this exception does not authorize filters on ordinary groups.
PPTX shape/connector import emits a public filter only for exactly one source
`outerShdw` with a meaningful non-zero offset, or exactly one source `glow`.
Glow import uses the registered Gaussian/flood/composite graph and preserves
its radius conversion. Zero-offset outer shadow, duplicate or foreign-namespace
effect containers, multiple effects, `effectDag`, unknown effects, and invalid
numeric or color data receive the blocking §1.4 effect-status metadata instead
of being reclassified or silently omitted.
Each supported source effect must contain exactly one resolvable DrawingML
color choice. Malformed choices and valid color semantics outside the
registered color/modifier subset also receive effect-status metadata; the
importer never substitutes black or drops an unhandled modifier.
DrawingML color alpha transforms are evaluated in document order. Each
`alpha`, `alphaMod`, or `alphaOff` result saturates into `0..100%` before the
next transform, and the importer writes that effective value to the SVG
`flood-opacity` channel.
Picture and group targets do not expose the public filter mapping: any source
effect DAG or non-empty effect list on `p:pic/p:spPr` or `p:grpSp/p:grpSpPr`
keeps the base object but receives effect-status metadata instead of attaching
an invalid filter to `<image>` or ordinary `<g>`.
Imported metadata-backed logical shapes preserve slide-local run-level effects
only inside an unchanged `metadata[data-pptx-part="txbody"]` payload. If
visible text, typography, or child topology invalidates that payload, checker
and exporter stop when the source `rPr` / `defRPr` / `endParaRPr` contains a
non-empty `effectLst` or `effectDag`; effect-free edited text keeps the normal
fallback.
Effects found in the inherited Layout/Master list-style chain are outside that
slide-local payload. Horizontal import keeps the visible fallback and payload
but stamps the logical shape and native carrier with
`unsupported-run-effect-route:inherited-text-style`.
The separate vertical-text output cannot carry that payload. When its source
text body or inherited list-style chain contains the same non-empty run-effect
containers, import keeps the normalized geometry and visible vertical text but
stamps the logical shape and native carrier with the blocking §1.4 effect
status; effect-free and empty effect containers keep the existing normalized
fallback.
Relationship-bearing text bodies also cannot carry the opaque payload across
parts. When such a body or its inherited list-style chain contains a non-empty
run effect, import keeps its rebuilt visible text but stamps the same two
blocking object markers; relationship-bearing text without a run effect keeps
the existing visual fallback.
Table-cell text bodies use neither the opaque payload nor the public filter
mapping. A non-empty run effect disables the native Table replacement payload,
keeps the visible table fallback, and stamps its imported `p:graphicFrame`
logical group with the blocking effect status. The existing replacement status
still records any independent table fallback reason; empty effect containers
and effect-free cells remain eligible for the closed native Table schema.
If a shape has both an unsupported shape-level effect and one of these run-level
fallback reasons, the canonical compound marker records both reasons.
This conditional guard is not a public run-effect authoring surface.
The quality checker and exporter preflight enforce the same definition,
reference, primitive, target, and numeric-value contract. Missing required
geometry and malformed values are never replaced by effect defaults during
native export.

```xml
<defs>
  <filter id="softShadow" x="-15%" y="-20%" width="130%" height="150%">
    <feDropShadow dx="0" dy="6" stdDeviation="8"
                  flood-color="#000000" flood-opacity="0.10"/>
  </filter>
  <filter id="expandedShadow" x="-15%" y="-20%" width="130%" height="150%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="8" result="b"/>
    <feOffset in="b" dx="0" dy="6" result="o"/>
    <feFlood flood-color="#000000" flood-opacity="0.10" result="c"/>
    <feComposite in="c" in2="o" operator="in" result="s"/>
    <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="titleGlow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="b"/>
    <feFlood flood-color="#38BDF8" flood-opacity="0.45" result="c"/>
    <feComposite in="c" in2="b" operator="in" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
```

Even `feDropShadow` with `dx="0" dy="0"` becomes glow. Use an existing accent
color for glow; black reads as diffuse shadow.

| Elevation | Use | `dy` | `stdDeviation` | Alpha |
|---|---|---:|---:|---:|
| Floor | Backgrounds, dividers, equal peers, body containers, decorative lines/icons, single-layer pages | — | — | — |
| Resting | Card over photo/panel, secondary callout | 2–4 | 4–8 | 0.06–0.10 |
| Raised | Primary CTA, focused card, overlay | 6–10 | 10–16 | 0.12–0.20 |
| Glow | Short display text, metric, focus accent | 0 offset | 4–8 | 0.35–0.55 |

**Strong default — single light source per page**: every `feOffset` shadow on
one slide shares the same `dx`/`dy` direction (default `dx="0"`, `dy="4"`–`dy="8"`,
light from upper front). Contradictory shadow directions read as multiple light
sources — a clear low-quality tell. The one sanctioned exception is a deliberate
upward paper-layer light, where every affected layer flips direction together;
never mix directions on the same plane. This is a strong default, not a
checker-enforced hard rule.

**Reference — not a constraint**: keep at most two
non-floor tiers; two or three shadowed objects usually suffice. Do not lift
every peer card or stack strong shadow, border, gradient, and tint on one
container. Same-family colored shadow is reserved for a focal accent. On dark
backgrounds, prefer a light hairline or restrained glow; never glow body copy.
Negative `dy` is valid for an intentional upward paper-layer light source when
every affected layer uses the same direction. For older/strict renderers,
replace a filter with two or three offset translucent shapes behind the object:
alpha `0.03–0.05`, increasing offset/radius, and optional same-family tint near
`0.04` (`Native-stable`).

---

### 6.5 Image Treatments, Overlays, and Glass-like Surfaces

| Need | Authoring contract | Fidelity |
|---|---|---|
| Cover/crop | Readable raster dimensions + aligned `slice` | Native `srcRect`; `Native-stable`; otherwise native crop cannot be guaranteed |
| Contain/fit | Aligned `meet` | Fitted picture frame; `Native-normalized` |
| Stretch | `preserveAspectRatio="none"` | Native stretched frame |
| Uniform fade | `<image opacity="...">` | Native picture alpha |
| Shaped picture | §1.2 image-only `clip-path` | Preset/custom picture geometry |

**Hard rule — closed image aspect-ratio grammar**: on `<image>`, omit
`preserveAspectRatio` for the default `xMidYMid meet`, use `none` alone for
stretch, or use one of the nine case-sensitive alignments (`xMinYMin`,
`xMidYMin`, `xMaxYMin`, `xMinYMid`, `xMidYMid`, `xMaxYMid`, `xMinYMax`,
`xMidYMax`, `xMaxYMax`) followed by explicit `meet` or `slice`. Generated SVG
always includes the mode on an aligned value. An alignment without a mode and
values needing whitespace normalization are compatible input and receive a
Checker recommendation. Empty values, `defer`, unknown/wrong-case alignments or
modes, `none` with a mode, and extra tokens are errors; the converter never
guesses a fallback.

**Hard rule — fit/clip interaction**: a non-trivial clip disables `meet`
frame-fit. Match the image box to the source ratio or use `slice`. Do not apply
filters directly to `<image>`.

**Hard rule — picture frames and sources are explicit and decodable**: every
SVG `<image>` has explicit positive `width`/`height` and exactly one non-empty
`href` or compatible `xlink:href`. A data URI must use a supported `image/*`
MIME type, valid strict base64 when marked
`base64`, a non-empty payload, and bytes that decode as the declared format.
An external asset must resolve, use a supported extension, be non-empty, and
decode as that extension. The registered formats are PNG, JPEG, GIF, WebP,
BMP, TIFF, SVG, EMF, and WMF. Explicit template substitution tokens may remain
unresolved only during template checking; export requires the resolved image.
Missing, ambiguous, corrupt, mislabeled, or unsupported sources are errors and
must never be dropped or packaged as invalid zero-byte media.

**Hard rule — nested SVG is an imported crop transport, not a general
viewport**: every non-root `<svg>` must be the exact picture-crop wrapper emitted
by `pptx_to_svg`. The outer element has explicit registered project-geometry
`x`, `y`, positive `width`/`height`, a unit-coordinate `viewBox` made of four
ordinary decimal values, and
`preserveAspectRatio="none"`; it contains exactly one direct, empty `<image>`
with exactly one non-empty `href` or `xlink:href`, `x="0"`, `y="0"`, `width="1"`,
`height="1"`, and `preserveAspectRatio="none"`. Its ancestor chain contains
only the root SVG and ordinary visual `<g>` wrappers; definitions, text,
render-only geometry details, and other non-visual containers cannot own this
transport. The outer wrapper may additionally carry `id`, a supported
`transform`, registered structure metadata (`data-pptx-layer` or
`data-pptx-placeholder-carrier`), and the importer metadata
`data-pptx-frame`, `data-pptx-object`, `data-pptx-shape-id`,
`data-pptx-shape-name`, and `data-pptx-shape-scope`. A shape clip is present
only when exact `data-pptx-crop="1"` and a registered image-only `clip-path`
occur together and the local clip definition resolves. The inner image may
add only registered `opacity`. The `viewBox` must quantize without clamping to
a DrawingML `srcRect` with a positive visible region: each signed crop value
must fit the OOXML percentage integer range `-2147483648..2147483647`, while
`l + r < 100000` and
`t + b < 100000` preserve a positive visible region. Negative crop values and
crop windows extending outside the source unit rectangle are retained exactly,
not clamped. `0 0 1 1` is redundant and must be written as a plain `<image>`.
Extra visual children, indirect images, character data, unknown attributes,
malformed or unrepresentable crop coordinates, and generalized nested
viewports are errors. Checker and the converter share this parser so a nested
subtree cannot pass validation and then silently disappear during export.

| Overlay | Construction | Typical stops / alpha |
|---|---|---|
| Directional scrim | Linear rect, darkest beside text | `0%: 0.88; 55%: 0.30; 100%: 0` |
| Bottom title fade | Vertical rect over lower image | black `0 → 0.72` |
| Vignette/spotlight | Centered radial rect (`cx=50%`, `cy=50%`, `r=70%`); native center only | black `0 → 0.58` |
| Brand wash | Directional existing brand-color gradient | `0.80 → 0.10` |
| Faux glass | Visible fields + diagonal linear panel (`0,0 → 1,1`) + highlight stroke; optional §6.4 elevation | white `0.38 → 0.12`; stroke about `0.55` |

Layer in document order: image → scrim/wash → text. True source/backdrop blur is
`Bake-required`; faux glass is explicit layering, not blur. Validate contrast
against the actual image. All overlay gradients follow §6.3 linear/radial
fidelity.

---

### 6.6 Lines, Connectors, Borders, and Markers

| Surface | Contract / native result |
|---|---|
| Solid stroke/width/alpha | `Native-stable` editable line |
| `4,4`; `6,3`; `2,2`; `8,4`; `8,4,2,4` (comma or space separators) | `dash`; `dash`; `sysDot`; `lgDash`; `lgDashDot` (`Native-normalized`) |
| Canonical custom dash | Exactly two positive finite unitless ordinary decimals (`dash gap`); export scales/quantizes against stroke width; `Native-normalized` |
| Compatible custom dash | Three or more positive finite unitless values are accepted but reduce to the first pair with a Checker recommendation; compatible numeric spellings also warn |
| `stroke-linecap` | `butt`, `round`, `square`; `Native-stable` |
| `stroke-linejoin` | `miter`, `round`, `bevel`; `Native-stable` |
| `vector-effect` | Exactly `none` or `non-scaling-stroke`; export resolves the choice into native line width (`Native-normalized`) |
| `stroke-dashoffset` | No general line mapping; allowed only as a direct finite unitless ordinary-decimal attribute on a §6.10 thick-circle shorthand (`px` suffix is compatible input and warns) |
| Gradient stroke | §6.3; re-import may flatten to first stop |
| `marker-start` / `marker-end` | §1.1 native line end; type `Native-normalized`, size `Approximate` (`sm/med/lg`) |

The dash grammar is closed: exact lowercase `none`, or at least two finite
unitless numbers separated by whitespace or one comma. Generated SVG uses
ordinary decimal spellings. A leading plus sign, exponent, trailing decimal
point, surrounding whitespace, or longer custom list is compatible input and
produces a non-blocking normalization recommendation. Unknown units, one-value
arrays, empty or repeated comma fields, non-finite values, and negative or zero
entries are errors. The only zero exception is a gap declared directly on the
§6.10 thick-circle element.

Generated cap, join, and `vector-effect` values use the exact lowercase tokens
in the table. Surrounding whitespace is compatible input and produces a
recommendation; every other token is an error.

Match marker fill to the parent stroke. Use markers for connectors and §6.10
calculated geometry for a manual diagonal arrowhead. When exact grid spacing
matters, use one multi-subpath path rather than a fixed-density preset pattern:

```xml
<path d="M40 0V120 M80 0V120 M0 40H120 M0 80H120"
      fill="none" stroke="#2E6EA8" stroke-width="0.8"/>
```

---

### 6.7 Advanced Text Treatments

**Hard rule — closed text property grammar**: generated text uses only the
values in the `Canonical authoring` column. Registered compatible input remains
convertible and receives a non-blocking normalization recommendation. Every
other value is invalid; the converter must not replace it with a default.

| Property | Canonical authoring | Compatible input | DrawingML mapping / rejection boundary |
|---|---|---|---|
| `font-weight` | `normal`, `bold`, or an exact integer hundred from `100` through `900` | `medium` → `500`; `semibold` → `600` | `normal` and `100..500` map to regular; `bold` and `600..900` map to `b="1"`; therefore numeric weights are `Native-normalized` |
| `font-style` | `normal` or `italic` | None | `italic` maps to `i="1"`; oblique, angle, relative, and CSS-wide values are invalid |
| `text-anchor` | `start`, `middle`, or `end` on `<svg>`, `<g>`, or `<text>` | None | Maps to left/center/right paragraph alignment plus normalized frame position; it is invalid on `<tspan>` because run-level anchoring has no mapping |
| `text-decoration` | `none`, `underline`, `line-through`, or `underline line-through` | `line-through underline` → canonical order | Maps to the single underline and strike run properties; unknown, repeated, or substring-like tokens are invalid |
| `letter-spacing` | Finite unitless ordinary decimal SVG px | The same ordinary decimal with `px`, `pt`, or `em`; normalize to unitless px | Maps to `a:rPr@spc`; the final value must fit DrawingML `-400000..400000`, and negative tracking must leave every generated DrawingML run with a positive estimated advance and its text frame with a positive extent; keywords, percentages, exponents, leading plus signs, trailing decimal points, non-finite values, and other units are invalid |

The registered text properties follow SVG inheritance, including declarations
on the root `<svg>`: inline `style` overrides the same element's direct
attribute, which overrides its ancestor. Relative font sizes and `em` tracking
resolve against the same effective inherited size in Checker and converter.
Every declaration is validated even when a later declaration overrides it, so
hidden garbage cannot bypass preflight.

The DrawingML character-spacing range is necessary but not sufficient for
negative tracking. After run assembly, each output run must retain a positive
estimated advance using the quantized `sz` and `spc` values that will actually
be written; a wider sibling run or paragraph line cannot hide a run whose
aggregate advance would reverse or collapse, which can reorder or drop
characters across PowerPoint-compatible renderers. The generated text frame
must also retain a positive horizontal and vertical extent. Checker rejects
directly measurable single-line violations, and the converter revalidates
every generated run and text frame before writing OOXML. It must not clamp,
take the absolute value of, or otherwise hide a non-positive advance or extent.
Adjacent authored runs with identical final DrawingML run properties form one
output run before sizing and validation; splitting text across equivalent
`<tspan>` nodes is not a tracking escape hatch. Tracking and width estimates
count the registered project text clusters rather than raw Unicode code points:
combining marks, variation selectors, emoji modifiers and ZWJ sequences,
paired regional indicators, and same-script virama conjuncts do not receive
internal spacing.
An unchanged imported native text body reuses the geometry carrier's positive
shape frame and attaches the preserved `txBody` payload instead of regenerating
runs or a text frame from the SVG estimate.

**Hard rule — element-specific text surface**:

- Inheritable text declarations belong only on `<svg>`, `<g>`, `<text>`, or
  `<tspan>`; placing them on geometry, image, definition, or reuse elements is
  an error rather than ignored decoration.
- `<text>` accepts `x`, `y`, registered paint/alpha/run properties, the text
  properties above, `font-family`, `font-size`, direct `filter`, direct
  `transform`, `xml:space`, `id`, and project `data-*` metadata.
- `<tspan>` accepts `x`, `y`, `dx`, `dy`, registered paint/alpha/run
  properties, `font-family`, `font-size`, `font-weight`, `font-style`,
  `letter-spacing`, `text-decoration`, `xml:space`, `id`, and project `data-*`
  metadata. It does not accept `text-anchor`, `filter`, or `transform`.
- `word-spacing`, `dominant-baseline`, `alignment-baseline`, `baseline-shift`,
  font shorthand/variant/stretch/feature/variation/synthesis controls,
  `font-kerning`/`kerning`, `font-size-adjust`, `line-height`, text alignment,
  indent/shadow/rendering controls, white-space/word-break/hyphenation
  controls, `writing-mode`, `vertical-align`, `direction`, `unicode-bidi`, and
  `text-transform` have no registered native mapping and are errors as direct
  attributes or inline style.
- Any other unregistered `font-*` or `text-*` property is also an error; the
  closed grammar must not grow through an ignored CSS spelling.

**Hard rule — project text whitespace**:

- `xml:space` is the project's closed authoring control for significant text
  whitespace. It is valid only as an exact direct attribute on `<text>` or
  `<tspan>`, accepts only the case-sensitive values `default` and `preserve`,
  inherits through the text tree, and may be reset on a child `<tspan>`.
- The project maps this control to the visible Chromium/SVG2 behavior used by
  Live Preview; it does not claim the legacy SVG 1.1 newline-deletion model.
  XML line endings and tabs become U+0020 SPACE. In `default` mode, contiguous
  U+0020 characters collapse across inline run boundaries and leading or
  trailing default-mode spaces in the resulting text chunk are removed. In
  `preserve` mode, every resulting U+0020 character remains significant.
- Only XML whitespace is normalized. NBSP, ideographic space, and other
  Unicode spacing characters remain literal text and must not be rewritten by
  a generic Unicode-whitespace regular expression.
- Source line breaks do not create PowerPoint paragraphs. Use the registered
  positioned-`tspan`/paragraph structure for visual lines, and preserve DOM
  text/tail order plus original style inheritance when normalizing that
  structure.

These allowlists are additive to the global structural blacklist and the
paint, font-size, opacity, filter, and transform value contracts owned by their
respective sections; they do not weaken those contracts.

| Treatment | SVG surface | Result / boundary |
|---|---|---|
| Underline / strike / both | `text-decoration="underline"`, `line-through`, or both | `Native-stable`; both emits both run properties |
| Mixed runs | Non-positional `<tspan>` | One `Native-normalized` editable frame; §4.2 |
| Font size | Generated default is a finite unitless SVG px value; compatible `px`, `pt`, `pc`/`pica`, `in`, `cm`, `mm`, `q`, `em`, and `rem` values receive a recommendation warning only | Converted to SVG px, then editable DrawingML point size; unsupported units/percentages error |
| Tracking | §6.7 closed `letter-spacing` grammar | `Native-normalized`; compatible units normalize to SVG px before DrawingML conversion |
| Transparency | `opacity` / `fill-opacity` on text/run | `Native-normalized` run alpha, not isolated compositing |
| Gradient fill | §6.3 gradient on text/run | Editable fill; geometry normalizes |
| Outline | Solid `stroke`, `stroke-width`, `stroke-opacity` | `Native-normalized` editable run outline; re-import does not reconstruct it |
| Shadow/glow | §6.4 filter on `<text>` only | Shape shadow / run glow; `Approximate` |
| Native bullet | Leading `· • ● ▪ ■ ◆ ◇ ◦ ‣` + non-empty content | `·`/`•` → `•`; others unchanged; color/alpha from marker run; font/size follow text |

```xml
<text x="100" y="200" font-size="20" xml:space="preserve">Current <tspan
  fill="#999999" text-decoration="line-through">old</tspan> value</text>
```

Use strikethrough for removed/former values; it is ordinary notation, not a
style-exclusive effect. Imported double underline/strike normalizes to single.
Bullet detection allows optional leading whitespace, requires non-empty content,
and leaves non-leading decorative glyphs as ordinary text.
Keep body tracking normal; CJK tracking defaults near/below 2% of font size and
above 5% triggers review. Text outline is solid only. `textPath`, masks, blend
modes, generated effects, and text-image knockouts are outside editable text.

---

### 6.8 Transforms, Layering, and Static Reuse

| Surface | Contract / fidelity |
|---|---|
| `rotate(angle[, cx, cy])` | Geometry/image/text/ordinary group; `Native-normalized` |
| `translate(x y)` | Geometry/image/group; pure translation also safe on text; `Native-normalized` |
| Positive scale / negative mirror | Geometry/image or a group/use whose expanded visual subtree is geometry/image only; explicit pivot; `Native-normalized` |
| `matrix(a b c d e f)` | Geometry/image or the same geometry/image-only group/use; transformed axes finite, non-zero, orthogonal; excludes rounded rectangles and subtrees containing them; `Native-normalized` |
| Source order | Back-to-front PPT z-order; `Native-stable` |
| `<g opacity>` | Compatible approximate mapping; generated SVG prefers descendant alpha, §2.2 |
| Local `<use>` | §1.3 compile-time reuse; `Native-normalized` |

**Hard rule — closed transform grammar**: Use only lowercase `translate`,
`scale`, `rotate`, and `matrix` with exact finite unitless argument counts:
`translate` 1/2, `scale` 1/2, `rotate` 1/3, and `matrix` 6. Separate arguments
and operations with whitespace or one comma. Leading/trailing/repeated commas,
adjacent operations without a separator, units, unknown functions, and
incomplete input fail quality check and export. Generated numeric tokens use
ordinary decimals; a supported leading `+`, exponent, or trailing decimal point
remains compatible input and receives a non-blocking normalization warning.

Set text size/position directly. A text transform is either a translate-only
list or one rotate operation; do not scale, matrix-transform, or mix operations
on text. A group containing text follows the same translate-only/single-rotate
limit. `skewX`, `skewY`, zero/non-orthogonal axes, and shear matrices are
forbidden. Native chart/table markers allow translate/scale only. The §6.10
thick-circle shortcut does not inherit general transform support. Positive
rotation is clockwise and pivoted rotation normalizes the native frame. Every
cumulative matrix, including transforms split across ancestors, must remain
finite, non-zero, and orthogonal; importer/live-editor matrices do not expand
the hand-authored contract.
Mirror around vertical pivot `cx` with
`translate(cx 0) scale(-1 1) translate(-cx 0)`; use the analogous Y sequence
for a horizontal pivot.

Layer back-to-front: background/image → scrim/shadow → main geometry → labels /
icons → top annotation. Finalization and native export independently expand
`<use>` into cloned editable primitives; PowerPoint does not retain a symbol /
instance graph.

---

### 6.9 Freeform Shapes and Curves

| Input | Native normalization | Fidelity |
|---|---|---|
| `M/L/H/V`, absolute or relative | Absolute `M/L` | `Native-normalized` |
| `C` | Cubic Bézier | `Native-normalized` |
| `S/Q/T` | Explicit cubic controls | `Native-normalized` |
| `A` | Cubic segments of at most 90° | `Approximate` |
| `Z`; polygon/polyline | Closed/open freeform | `Native-normalized` |

**Hard rule — complete freeform grammar**: Generated `path@d` and
`polygon` / `polyline@points` use finite unitless ordinary decimals and only
the commands registered above. Native export consumes the complete attribute;
it never extracts recognizable fragments while ignoring other characters.
Finite scientific notation, a leading plus sign, and a trailing decimal point
remain read-compatible and receive recommendation warnings; generated SVG does
not write them. Unknown commands or characters, misplaced/repeated commas,
non-finite numbers, missing attributes, incomplete command groups, and odd
point counts are invalid. A path starts with `M` / `m`; `A` radii are
non-negative and both arc flags are exactly `0` or `1`. Each registered path
command accepts its uppercase absolute and lowercase relative form. Legal
separator-free arc flag sequences remain valid and are parsed as individual
flag tokens. A polygon has at least three coordinate pairs and a polyline at
least two.

**Validation**: Checker and native export consume the same parser in
[`paths.py`](../scripts/svg_to_pptx/drawingml/paths.py); native-object fallback
bounds reuse its normalized commands rather than a second path grammar.

Command identity, relative coordinates, shorthand, arc parameters, and original
handles are not retained. Geometry needs non-zero bounds. Use a closed cubic
path for organic silhouettes, polygon/closed path for ribbons/facets, open path
for curved connectors, multi-`M` path for exact linework, and a §1.2 path clip
for organic pictures. Filled silhouettes end with `Z`; open paths use
`fill="none"`. Do not depend on `fill-rule="evenodd"`; build explicit visible
geometry or bake an essential knockout.
For a fixed background, a background-colored overlay is also valid.

| Rounded rect input | Result |
|---|---|
| One positive radius, or `0 < rx == ry <= min(width,height)/2` | `Native-stable` adjustable `roundRect` without distorting transforms; the same short-side limit applies to one-radius input |
| `0 < abs(rx-ry) < 0.5px` after scaling | One normalized native radius; `Approximate` |
| `abs(rx-ry) >= 0.5px`, either positive | Cubic custom geometry; no radius handle; `Approximate` |
| Equal radius above half the short side | Native short-side clamp may differ from SVG; `Approximate` |

---

### 6.10 Radial Geometry, Donuts, Gauges, Sunbursts, and Diagonal Arrowheads

For center `(cx,cy)`, radius `r`, and degrees `θ`:

```text
x = cx + r × cos(θ × π / 180)
y = cy + r × sin(θ × π / 180)
```

For clockwise pie/donut sectors, default to `-90°` only when the chart starts at
12 o'clock. A full-circle percentage sector spans `percentage × 360°`;
large-arc is `1` above `180°`; outer sweep is `1`, inner return is `0`. Split
both outer and inner boundaries of a full ring into at least two arcs each.
Calculated endpoints survive subject to EMU rounding; `A` curves remain cubic
approximations. Verify all spans plus gaps against the planned sweep.
Explicit arc sectors are editable `Approximate` freeforms. Thin circles using a
§6.6 preset/two-number dash stay `Native-normalized` ellipse lines.

```xml
<!-- 75% donut: center 400,400; outer 180; inner 100; -90° → 180°. -->
<path d="M400 220 A180 180 0 1 1 220 400
         L300 400 A100 100 0 1 0 400 300 Z" fill="#2563EB"/>
```

**Gauge**: require `max > min`, `p = clamp((value-min)/(max-min),0,1)`, and
`0 < planned clockwise sweep <= 360°`; value sweep is `p × planned sweep`.
`valueEndAngle = startAngle + valueSweep`; large-arc is `1` iff
`abs(valueSweep) > 180°`.
Omit the value sector at `p=0`. At `p=1` with `360°`, split both boundaries into
at least two arcs. Track/value share center, radii, start, and sweep flags.

**Sunburst — `Approximate`**: one explicit annular sector per node; each depth owns one radius
band and child angular intervals partition the parent. Do not use one `evenodd`
compound ring.

**Thick-circle shorthand — `Approximate`, non-position-sensitive only**:

- One circle per segment; `fill="none"`; the circle may use one `rotate` for its
  start angle, and ancestor transforms must be translate-only.
- Exactly two non-preset finite unitless ordinary-decimal values (`dash gap`);
  `stroke-dashoffset` is a direct finite unitless ordinary-decimal attribute.
- `0 < stroke-width < 2r`, `stroke-width/r >= 0.15`,
  `0 < dash < 2πr`, `gap >= 0`, and `dash + gap >= 2πr - 1` SVG unit. The
  one-unit tolerance exists only for integer-rounded circumference values.
- Native construction uses only the first dash and re-imports as a freeform.
  Its native start is 90° counterclockwise from the SVG preview; use explicit
  arcs whenever start angle, cap, or radial precision matters.

```xml
<circle cx="400" cy="400" r="140" fill="none" stroke="#2563EB"
        stroke-width="48" stroke-dasharray="615.75 263.90" stroke-dashoffset="0"/>
```

**Diagonal polygon arrowhead**: for a non-zero line, calculate rather than use a
fixed triangle:

```text
dx=x2-x1; dy=y2-y1; len=√(dx²+dy²); ux=dx/len; uy=dy/len
px=-uy; py=ux
tip=(x2,y2)
back1=(x2-ux×12+px×5, y2-uy×12+py×5)
back2=(x2-ux×12-px×5, y2-uy×12-py×5)
```

Use §1.1 markers for ordinary connectors; the polygon is for a manually drawn
filled `Native-normalized` arrowhead. Example:
`<polygon points="370,430 365.6,417.8 358.2,424.6"/>`.

---

### 6.11 Constructed Visual Styles

**Hard rule — explicit construction**: these are supported-layer recipes, not
browser-filter permissions.

**Reference — not a constraint**: use them only when they match the locked style.

| Intent | Construction | Boundary / fidelity |
|---|---|---|
| Faux glass | §6.5 translucent panel + highlight stroke + visible fields | No backdrop blur; `Native-normalized` |
| Hand-drawn mark | Rotated translucent bar + irregular `Q/C` paths + round caps | No roughness filter; `Native-normalized` |
| Ink wash | Few same-family translucent closed curves/strokes | No feather/wet edge; `Native-normalized` |
| Riso offset | Duplicate text/shape with small offset, second ink, lower alpha | No blend mode; `Native-normalized` |
| Pixel grid | Integer-aligned rects on one cell grid | `shape-rendering` preview-only; `Native-stable` |
| Halftone | Sparse calculated circles | `Native-stable`; bake dense screens / use suitable §7 preset |
| Isometric facets | Shared-vertex top/front/side polygons, one light direction | 2D only; `Native-normalized` |
| Paper cut | Ordered organic paths + consistent §6.4 shadow per layer | Filter each layer, not group; `Approximate` |
| Gradient ribbon | Non-degenerate cubic path + §6.3 gradient stroke; closed gradient-filled shape for horizontal/vertical ribbons | `Native-normalized`; no mesh gradient; re-import may flatten color |
| Line-plus-area data | Low-alpha closed area first, crisp line above | Keep area subordinate; `Native-normalized` |

**Minimal construction anchors**:

```xml
<!-- Hand-drawn + ink. -->
<rect x="80" y="80" width="240" height="28" fill="#FDE68A"
      opacity="0.72" transform="rotate(-1,200,94)"/>
<path d="M90 150 Q210 142 330 151" fill="none" stroke="#1F2937"
      stroke-width="3" stroke-linecap="round"/>
<path d="M80 220 C160 160 250 180 330 230 Z" fill="#1F2937" opacity="0.16"/>
<path d="M90 240 C180 210 250 260 340 220" fill="none" stroke="#1F2937"
      stroke-width="10" stroke-linecap="round" opacity="0.70"/>

<!-- Riso, pixel cells, sparse dots. -->
<text x="86" y="320" font-family="Arial, sans-serif" font-size="64"
      fill="#EC4899" opacity="0.85">PRINT</text>
<text x="92" y="326" font-family="Arial, sans-serif" font-size="64"
      fill="#2563EB">PRINT</text>
<g id="pixel-cells" shape-rendering="crispEdges" fill="#2563EB">
  <rect x="400" y="80" width="16" height="16"/><rect x="416" y="80" width="16" height="16"/>
</g>
<g id="sparse-dots" fill="#EC4899"><circle cx="410" cy="140" r="3"/><circle cx="426" cy="140" r="6"/></g>

<!-- Isometric facets + line-over-area. -->
<g id="isometric-facets" transform="translate(520 160)">
  <polygon points="0,0 80,-24 160,0 80,24" fill="#60A5FA"/>
  <polygon points="0,0 0,48 80,72 80,24" fill="#3B82F6"/>
  <polygon points="80,24 80,72 160,48 160,0" fill="#2563EB"/>
</g>
<path d="M760 260 L860 220 L960 250 L960 340 L760 340 Z" fill="#2563EB" opacity="0.10"/>
<path d="M760 260 L860 220 L960 250" fill="none" stroke="#2563EB" stroke-width="4"/>
```

**Default — integer pixel grid (may override for deliberate irregular
treatment)**: avoid soft scaling; use explicit dots only for sparse editable
halftone and route dense full-slide texture to §6.12.

---

### 6.12 Unsupported Effects and Native-Safe Alternatives

| Unsupported intent | Do not author | Fidelity | Alternative |
|---|---|---|---|
| Source/backdrop blur; procedural texture | Plain blur, `feTurbulence`, `feDisplacementMap`, `feColorMatrix`, arbitrary filter graph | `Bake-required` | §6.4 effect, explicit geometry, translucent layers, or baked texture |
| Inner shadow, soft edge, reflection | Non-outer-shadow/glow graph | `Bake-required` | Explicit inset/highlight/shadow layers or image |
| Per-pixel compositing | Mask, blend mode, knockout, arbitrary alpha composite | `Bake-required` | Direct geometry; §1.2 image clip; otherwise bake |
| Exact custom tile | Unannotated `<pattern>` / `patternTransform` | `Bake-required` | Multi-subpath geometry, suitable §7 preset, or bake |
| Sheared object | Skew/shear matrix | `Bake-required` | Pre-transform geometry path; bake text/image |

**Hard rule — blur semantics**: within §6.4, zero-offset `feGaussianBlur` means
glow; it does not blur the object or backdrop. Use a low-alpha raster for dense
grain and explicit circles/paths only for sparse editable marks.

**Hard rule — unsupported imported object effects remain explicit**:
`pptx_to_svg.py` keeps the underlying object but stamps blocking effect-status
metadata for unsupported shape/connector effects and for every picture/group
effect DAG or non-empty effect list.
Before release export, rasterize the affected object from the source PPTX or
rebuild its effect with supported explicit geometry; baking the effect-less
analysis SVG alone cannot recover the source appearance. This diagnostic path
covers `p:sp`, `p:cxnSp`, `p:pic`, and `p:grpSp` source effects. Text-run source
effects follow the route-specific §6.4 contract: unchanged metadata-backed
horizontal text preserves slide-local effects in its native `txBody`, while a
lossy edit blocks from that payload and inherited list-style effects receive a
separate blocking marker; vertical and relationship-bearing shape-text routes
keep their visible fallback and stamp the logical shape plus carrier with
effect-status; table-cell text keeps the visible table fallback, disables
native Table replacement, and stamps the imported `p:graphicFrame` group.
Handled object or text-run effects must never become a different effect or
disappear without a diagnostic.

---

### 6.13 Scenario Quick Reference

**Reference — not a constraint**: fidelity remains authoritative in the owning
subsection; this table only routes scenarios.

| Decision family | Scenario routing | Authority / boundary |
|---|---|---|
| Elevation | Floating card → resting shadow; one CTA → colored shadow; equal peers/background → flat; maximum predictability → layered shapes; title/metric → glow | §6.4; never body-copy glow |
| Image/material | Text over image → directional scrim; bottom title → bottom fade; centered hero → vignette; brand wash → brand overlay; glass card → faux glass | §6.5; no backdrop blur |
| Lines | Draft/optional → dash; process direction → marker; flow/series → gradient stroke; exact grid → multi-subpath path | §6.6 / §6.3 |
| Text | Removed/former value → line-through; eyebrow → tracking; watermark/outline heading → text outline; list → native bullet | §6.7 |
| Composition | Move/rotate/mirror → §6.8 transform; repeated static mark → local `<use>` | §6.8; preserve z-order |
| Hand/print | Annotation → highlighter/curve; ink wash → layered alpha paths; Riso → offset duplicate | §6.11; no turbulence, true bleed, or blend mode |
| Pixel/halftone | Pixel accent → integer rect grid; sparse screen → circles | §6.11; dense screen → §6.12 |
| Faceted/layered | Pseudo-3D → 2D facets; paper cut → direct shadow per layer | §6.11; no 3D transform/group composite shadow |
| Data/freeform | Series depth → area first + line above; organic card → closed cubic; shaped image → §1.2 path clip | §6.11 / §6.9 |
| Radial | Donut/gauge → explicit arcs; sunburst → sector per node; position-insensitive ring → shorthand | §6.10; shorthand has 90° preview/native offset |
| Arrow | Manual diagonal arrowhead → calculated triangle; ordinary connector → marker | §6.10 / §1.1 |
| Unsupported | Dense grain, complex composite, or skew → explicit alternative or baked asset | §6.12; foreground text/data stay editable SVG |

---
## 7. Conditional PPT Interfaces

The interfaces below exist only for PPT behavior that ordinary SVG semantics
cannot express. Use them only when the corresponding native capability is
required.

### Pattern Fill — `<pattern>` with PPTX preset annotation

`<pattern>` requests one fixed DrawingML preset; the converter does not render
the tile's arbitrary geometry. Use this interface only when that preset mapping
is intended.

`data-pptx-pattern="<preset>"` is the generated default for selecting the
intended preset from the enum below. The converter retains an `ltUpDiag`
fallback when the annotation is absent; the checker reports that fallback as a
non-blocking fidelity warning. Invalid explicit preset names remain errors
because they violate the closed OOXML enum.

Pattern colors may come from importer metadata (`data-pptx-fg` /
`data-pptx-bg`) or from the pattern's child paint. Without metadata, the first
child `<rect>` fill becomes the background and the first stroke (or other fill)
becomes the foreground. A missing background defaults to white; a missing
foreground means no native pattern fill can be emitted. The child geometry
itself is never used as a repeatable tile.

**Valid `data-pptx-pattern` values** (OOXML `ST_PresetPatternVal` — closed enum, anything outside makes PowerPoint open with "needs to be repaired"):

| Category | Values |
|---|---|
| Grids | `smGrid` · `lgGrid` · `dotGrid` *(no `ltGrid` — common typo)* |
| Diagonal lines | `ltUpDiag` · `ltDnDiag` · `dkUpDiag` · `dkDnDiag` · `wdUpDiag` · `wdDnDiag` · `dashUpDiag` · `dashDnDiag` · `diagCross` |
| Horizontal / vertical lines | `horz` · `vert` · `ltHorz` · `ltVert` · `dkHorz` · `dkVert` · `narHorz` · `narVert` · `dashHorz` · `dashVert` · `cross` |
| Percent fills | `pct5` · `pct10` · `pct20` · `pct25` · `pct30` · `pct40` · `pct50` · `pct60` · `pct70` · `pct75` · `pct80` · `pct90` |
| Checks & confetti | `smCheck` · `lgCheck` · `smConfetti` · `lgConfetti` |
| Decorative | `horzBrick` · `diagBrick` · `weave` · `plaid` · `trellis` · `zigZag` · `wave` · `sphere` · `divot` · `shingle` · `solidDmnd` · `openDmnd` · `dotDmnd` |

`svg_quality_checker.py` warns when a referenced pattern lacks the annotation;
it errors when the pattern uses `patternTransform` or names a preset outside
this enum.

### PowerPoint-Native Chart / Table Replacement Markers (Opt-in)

Native PowerPoint tables and Excel-backed charts activate at export time only. The default chart/table route remains hand-authored SVG geometry so the deck stays pixel-stable across PowerPoint / Keynote / LibreOffice / WPS.

**Authoring — markers are standard on supported data charts and text-grid tables**: Executor writes the marker at draw time on every data chart whose type falls in the supported set and on every pure text-grid data table ([executor-base.md §3.2](executor-base.md)), so any deck can later form native objects without regeneration. Canonical rectangular merged text cells may use the narrow `row_span` / `col_span` contract below; graphical cells stay unmarked on the SVG fallback route. The marker group supplies both: visible SVG fallback children for browser/live-preview rendering, and JSON metadata for `svg_to_pptx` native export.

**Hard rule — activation is the opt-in, dormant unless exported with `--native-charts-and-tables`**: A marker only declares that a group is eligible for PowerPoint-native Chart/Table replacement. Normal `svg_to_pptx.py` runs keep the fallback SVG children and convert them into independently editable DrawingML shapes. Pass `--native-charts-and-tables` only when the data source and chart/table-specific object model matter more than cross-renderer layout fidelity: it emits the PowerPoint Chart/Table object and skips the fallback children to avoid duplicates. Native styling preserves the core palette, text, axis, grid, and background colors where possible, but it is still a PowerPoint Chart/Table object rather than a pixel-identical SVG drawing.

The native route is deliberately data-object-first and may be lossy: marker-local labels, callouts, KPIs, guide lines, custom split/bin semantics, or styling that is absent from the payload may disappear or normalize. Export warns about this route-level risk and any narrower issue it can detect. Loss of visual parity is not grounds to remove an active marker that the emitter can otherwise convert; use the default SVG-fallback export when exact authored artwork matters more than a native data source and object-specific controls.

| Replacement marker | Native output | Required metadata |
|---|---|---|
| `<g data-pptx-replace-with="table">` | `<p:graphicFrame>` with `<a:tbl>` | bounds + `columns` or `rows` |
| `<g data-pptx-replace-with="chart">` | `<p:graphicFrame>` with `c:chart` / `cx:chart` + chart part + embedded workbook | bounds + `type`, plus chart data |

**Metadata placement**: Put JSON in one child
`<metadata type="application/json">`. The parent group's
`data-pptx-replace-with` value selects the table or chart schema, so the
metadata child does not repeat an object-kind attribute. Attribute JSON
(`data-pptx-json="..."`) remains read-compatible but is harder to XML-escape
correctly and is not canonical authoring.

**Bounds**: Provide `x`, `y`, `width`, and `height` in metadata, or as
`data-pptx-x` / `data-pptx-y` / `data-pptx-width` / `data-pptx-height` on the
marker group. If any bound is omitted, the exporter infers the object frame
from the visible fallback geometry; this keeps SVG fallback and native object
placement aligned. Complete explicit bounds are absolute slide coordinates;
marker/ancestor `translate` and `scale` transforms apply only when at least one
bound is inferred. `x`, `y`, `width`, and `height` must be finite and resolve
inside PowerPoint's 32-bit DrawingML coordinate range; `width` and `height`
must resolve to at least one EMU. Native table frames must additionally resolve
to at least one EMU per resolved row and column.

**Validation**: `svg_quality_checker.py` validates replacement marker kind, JSON
metadata, bounds/fallback availability, table rows/columns, supported chart
type, chart data shape, and any imported fallback baseline before export.

**Hard rule — imported fallback freshness**: active table/chart markers emitted
by `pptx_to_svg.py` carry `data-pptx-fallback-sha256`, a canonical hash of the
marker fallback plus reachable document-level SVG fragment definitions. Editing
geometry/text/paint, switching a local `url(#...)` or `href="#..."` target,
changing a reachable definition, or changing the marker transform makes the
replacement metadata stale. The mandatory quality checker warns and the default route
keeps the edited SVG; `--native-charts-and-tables` hard-fails before replacement so it
cannot discard that edit. Metadata/title/description nodes, `data-pptx-*`
runtime attributes, marker-local stable ID renames, and marker-local
`display:none` subtrees are excluded. `visibility:hidden` content,
marker-local unused definitions, and explicitly referenced document-level
target roots (even when hidden) remain conservatively hashed. External
image/font file bytes are not read.
Generated authoring and reusable templates omit import provenance and do not
preseed a static fallback baseline; that hashless authored state is normal and
does not warn. A hashless legacy imported marker that still carries PPTX import
provenance remains native-compatible and warns in the checker/native route that
stale detection is unavailable. An explicitly sealed authored marker that does
carry a baseline is validated by the same integrity rule; only a missing
authored baseline is silent. A stale hash is an integrity mismatch, not a
visual-parity gate on an unchanged active marker.

**Hard rule — imported fallback kind**: A PPTX chart with a complete baked
preview may carry `data-pptx-fallback-kind="source-preview"`. Supported parsed
classic families without a preview use a deterministic readable fallback
marked `data-pptx-fallback-kind="normalized"`; it is explicitly not
source-exact. When no current renderer exists, the importer emits its typed
reconstruction aid with `data-pptx-fallback-kind="placeholder"`. That value
alone records the diagnostic reconstruction-only fallback: quality checking
and export warn, default export keeps the placeholder, and
`--native-charts-and-tables` may reconstruct a PowerPoint-native chart when the same
group has a valid active `data-pptx-replace-with="chart"` payload. The allowed
values remain closed; unknown, whitespace-padded, or contradictory values fail.
`data-pptx-replacement-status` records the closed reason code when imported
content has a complete visual fallback but cannot make an active replacement
claim. It and `data-pptx-replace-with` are mutually exclusive on the same
visible group.

**Imported replacement provenance**: A table/chart group created by
`pptx_to_svg.py` under this contract—whether it has an active replacement claim
or a fallback-only status—carries `data-pptx-import-source="pptx"`. This records
provenance for the imported-style normalization path; it does not identify the
replacement kind, and generated authoring omits it.

**Legacy read compatibility**: The converter and checker continue to read
`data-pptx-native`, `data-pptx-native-status`, `data-pptx-native-source`, and
`data-pptx-visual-status`. The legacy pair
`data-pptx-visual-status="placeholder"` plus
`data-pptx-route-status="reconstruction-only"` maps to canonical
`data-pptx-fallback-kind="placeholder"`; canonical authoring has no route-status
attribute. `--native-objects` remains a compatibility alias for
`--native-charts-and-tables`. New generated SVG and documented commands MUST
use the canonical spellings. If a legacy and canonical attribute are both
present, they must resolve to the same value; a conflict fails validation.

```xml
<g id="p03-revenue-chart" data-pptx-replace-with="chart">
  <metadata type="application/json">
    {
      "x": 120, "y": 150, "width": 520, "height": 320,
      "type": "column",
      "title": "Revenue by Segment",
      "categories": ["Q1", "Q2", "Q3"],
      "series": [
        {"name": "Cloud", "values": [12, 15, 19]},
        {"name": "Services", "values": [8, 9, 11]}
      ]
    }
  </metadata>
  <!-- Visible SVG fallback for live preview / non-native export goes here. -->
</g>
```

**Table schema**: Native tables are rectangular DrawingML grids. Use `columns`
for the optional header row and `rows` for body rows; shorter rows are padded
with blank cells unless `strict_grid: true` is set. Tables may contain at most
1000 resolved rows and 1000 resolved columns. Use `column_widths` and
`row_heights` as relative weights. Weight lists must match the resolved grid,
contain finite non-negative numbers, and include at least one positive value.
If present, `header_rows` must be an integer from `0` through the resolved row
count. Write `strict_grid`, `style.band_row`, and cell `bold` as JSON booleans.
Cell objects accept `text`, `fill`, `color`,
`align`, `valign`, `bold`, `font_size`, `padding`, `border_color`, and
`border_width`, plus optional `lang`; the same `padding`, `border_color`,
`border_width`, and `lang` keys may also live under `style` as table defaults.
For multi-paragraph text, replace cell `text` with a non-empty `paragraphs`
list. Each entry is either a string or an object containing optional
`align: "l|ctr|r"` and exactly one of `text` or non-empty `runs`; empty
paragraph strings are preserved, and cell `text` / `paragraphs` are mutually
exclusive. Each run is an object with required string `text` and optional JSON
boolean `bold`, `italic`, `underline`, and `strike`, plus optional `color`,
`font_size`, one-typeface `font_family`, `lang`, and `alt_lang`. Unknown fields,
wrong types, empty run lists, multi-typeface `font_family`, and unsupported
colors fail fast. PPTX import requires exact physical row/grid topology and
normalizes source presentation-only run XML outside this closed schema only
when it contains no non-empty `rPr` / `defRPr` / `endParaRPr` `effectLst` or
`effectDag`. A table-cell run effect follows the blocking effect contract above
instead of entering either the native payload or an effect-free fallback.
Relationship-bearing text, extensions, structural line breaks, fields, tabs,
bullets, malformed run topology, and unsupported text-body structure remain
fallback-only.
Per-side cell borders use `borders.left|right|top|bottom`, where each value is
either `{ "style": "none" }` or
`{ "style": "solid", "color": "#RRGGBB", "width": <positive-px> }`.
Per-side borders are cell-only; legacy uniform `border_color` / `border_width`
remain supported as defaults that an individual side may override.
When `lang` is absent, export derives `zh-CN` for CJK text and `en-US`
otherwise. `style.band_row: false` disables both `<a:tblPr bandRow>` and
materialized alternating row fills. Native table typography mirrors the
visible SVG fallback: put `style.font_family` and `style.font_size` on the
marker from the table text already drawn, then use `style.header_font_size` or
per-cell `font_size` only when the fallback visibly differs. If the fallback
has no explicit table font, use the deck body family and locked body size from
`spec_lock.md`.

**Hard rule — table metadata is the native source of truth**: Every row,
summary line, value, and cell-level style that must survive
`--native-charts-and-tables` must be present in `columns` / `rows`. SVG fallback text is
discarded during native export. `svg_quality_checker.py` warns when visible
fallback `<text>` inside a native table marker does not appear in metadata.
For numeric or currency columns, use cell objects with `align: "r"`; SVG
`text-anchor="end"` does not carry into the native table.

**Merged table cells — canonical rectangular contract only**: Put positive JSON
integer `row_span` / `col_span` values on the merge anchor and keep every
covered grid cell blank. Spans must stay within the resolved rectangular grid
and may not overlap. The exporter emits the canonical DrawingML topology
(`rowSpan` on the top edge, `gridSpan` on the left edge, `hMerge` / `vMerge` on
covered cells). CamelCase aliases, raw OOXML merge fields, top-level merge lists,
nonblank covered cells, invalid spans, and overlaps fail fast. The PPTX importer
activates native reconstruction only for that same explicit rectangular topology
with empty merge-slave text bodies; other merge encodings remain fallback-only
with `unsupported-merge-topology`.

**Category chart schema**: `column`, `bar`, `line`, `area`, `pie`,
`doughnut`, `pieOfPie`, `barOfPie`, and `radar` use `categories` plus
`series[].values`. Pie-family charts (`pie`, `doughnut`, `pieOfPie`, and
`barOfPie`) must have exactly one series; the exporter assigns per-category
slice colors so single-series charts do not collapse into one solid color.
Column and bar charts may set per-point colors with `series[].point_colors`
or `series[].pointColors`; the list must match `series[].values` length.
Classic category charts may set native PowerPoint data labels with
`data_labels`. Use `data_labels: true` for default value labels, or an object
with `show_value`, `position`, `number_format`, `font_size`, `font_family`,
`bold`, `color`, and optional per-point `colors`. Supported label positions
depend on chart type: clustered column/bar labels may use `outside_end`,
`inside_end`, `inside_base`, or `center`; stacked / percent-stacked column/bar
labels may use `inside_end`, `inside_base`, or `center`; line labels may use
`above`, `center`, or `best_fit`; area labels do not emit a native label
position. To label only selected data points, use `data_labels.points` with
zero-based `idx` plus optional per-point `position`, `number_format`,
`font_size`, `font_family`, `bold`, and `color`.

**Combo chart schema**: `combo` uses shared `categories` plus either `plots[]`
or typed `series[]`. Each plot supports `type: "column" | "line" | "area"`,
its own `series`, and optional `axis: "secondary"` for a right-side value axis.
When primary and secondary plots genuinely use different category caches,
`plots[]` may also carry its own `categories` and `category_numeric`; the
workbook writer allocates independent category/value ranges. Typed `series[]`
continues to require the shared top-level categories.
Imported `plots[]` may carry `series_indices` so the verified source identity
where each `c:idx` equals its `c:order` survives when physical plot order differs
from legend order. If one plot supplies it, every plot must supply a same-length
list of unique non-negative JSON integers, and the combined values must form one
contiguous `0..N-1` range. Sources whose `idx` and `order` differ stay
fallback-only; typed `series[]` does not accept this plot-scoped field.
Typed `series[]` accepts the same `type` and `axis` fields per series, and
adjacent compatible series are grouped into the same PowerPoint plot. Area
series may set `fill_opacity` / `fillOpacity` as a `0..1` SVG opacity value
when the SVG fallback uses a transparent area fill under an opaque line. A line plot with `area_fill: true`
is exported as a PowerPoint area chart under the hood; `fill_opacity` only sets
the fill style and does not trigger conversion by itself. Combo export layers
area plots below columns and lines while preserving the original series indices.
Line and area series may set `line_width` / `lineWidth` in SVG px units to
match fallback `stroke-width`.

**Narrow classic-axis schema**: `axes` is a closed object with the roles
`category`, `value`, `secondary_category`, and `secondary_value`. Each role may
set only `kind` (`text`, `date`, or `value`, as appropriate), `position`,
`visible`, `label_position` (`next_to`, `none`, `low`, or `high`),
`number_format`, `minimum`, `maximum`, `major_unit`, `reverse`, and
`major_gridlines`. `major_unit` applies to value axes only. PPTX date-axis
**import** is deliberately narrow: numeric Excel date serials are accepted for
area charts and OHLC stock charts; arbitrary date-axis source families are not.
This contract is not a full `AxisSpec`: logarithmic scales, minor units/gridlines,
crossing values, display units, tick skipping, and other unlisted OOXML semantics
remain unsupported and fail closed on import.

**Narrow XY-axis schema**: `scatter` and `bubble` may use a closed `axes` object
with only `x` and `y` roles. Both roles have `kind: "value"`; `x.position`
is `bottom` or `top`, while `y.position` is `left` or `right`. Each accepts the
same closed fields above, and `major_unit` is valid on both value axes. PPTX
import requires the plot to reference exactly two mutually cross-linked
`c:valAx` nodes and separately enforces the closed field/topology gates. The
native writer emits and the importer reads back every field in this closed
contract. Scatter import derives the effective `scatter_style` from a uniform
per-series line/marker/smooth state; unsupported or nonuniform states remain
fallback-only. The normalized SVG fallback newly consumes only
`axes.x.major_gridlines` and `axes.y.major_gridlines`; the other fields do not
imply full visual-axis parity.

**XY chart schema**: `scatter` and `bubble` use `series[].x` + `series[].y`;
`bubble` also requires one `series[].size` / `series[].sizes` value per point.
`series[].points` is also accepted as `[x, y]` / `[x, y, size]` tuples or
`{x, y, size}` objects.

**Chart typography**: Metadata sizes use the same px-style unit as SVG text
(`1px = 0.75pt`). `style.font_family` and the role-specific
`title_font_size`, `subtitle_font_size`, `axis_font_size`,
`axis_title_font_size`, `legend_font_size`, and `note_font_size` fields are
required only when the native object must preserve typography that cannot be
inferred unambiguously from the visible fallback.

**Chart chrome metadata**: Text that is visually part of the chart must be in
metadata, not only in SVG fallback children; metadata MUST still match visible
fallback chrome. `title` becomes the native chart title on classic charts; it
is not an object name, so use `name` for semantic object naming. `subtitle`
becomes the second rich-text line of that classic chart title. `title`,
`subtitle`, and axis-title values may be strings or objects with `text`,
`font_size`, `font_family`, and `color` when the fallback uses local role
typography. `svg_quality_checker.py` rejects `title`, `subtitle`, or axis-title
metadata whose text is not visible inside the replacement marker's fallback. Direct
`--native-charts-and-tables` export keeps the chart native but omits that inconsistent
chrome with a warning. chartEx keeps PowerPoint's empty `<cx:title>` and emits
the title / subtitle as companion editable text boxes until chartEx rich titles
are validated. Axis
titles are optional and explicit: use `axis_titles` with
`category`, `value`, `x`, `y`, or `secondary_value` keys, or the root aliases
`category_axis_title`, `value_axis_title`, `x_axis_title`, `y_axis_title`, and
`secondary_value_axis_title`; do not add semantic axis titles that are not
visible in the fallback. Set `show_value_axis_labels: false` when the fallback
keeps category labels but omits numeric value-axis tick labels, such as a radar
chart without radial coordinates. Native legends are metadata-controlled: use
`show_legend: true` and `legend_position` only when the fallback's legend is
meant to be replaced by PowerPoint's native legend.
Companion text such as `caption`, `source`, `note`, `notes`, `footnote`, and
`footnotes` is exported as editable PPT text boxes next to the native chart. A
companion entry may be a string or an object with `text`, `x`, `y`, `width`,
`height`, `font_size`, `color`, `align`, and `bold`; explicit bounds are
recommended so the native export matches the SVG fallback placement. Explicit
companion bounds are slide coordinates, not local coordinates inside a
transformed marker group. Use companion text for chart captions, source notes,
center labels, and freeform annotations; use `data_labels` for values that
belong to chart points.

**Chart color styling**: For classic native charts, `style.colors` sets series
colors. The exporter also writes explicit chart-area fill, plot-area fill,
axis line, gridline, and label text colors so PowerPoint does not substitute a
white/default-theme chart. If omitted, the exporter infers these colors from
the visible SVG fallback: the largest panel-like `<rect>` becomes the chart
background, fallback text supplies label color, and fallback strokes supply
axis/grid colors. Override any of them explicitly under `style` with
`chart_area_fill`, `plot_area_fill`, `text_color`, `axis_color`, and
`grid_color`; use `"none"` for transparent chart or plot area fill. Generated
payloads default to uppercase `#RRGGBB`. The exporter retains compatibility for
`#RGB`, `rgb(...)` / `rgba(...)`, and common CSS names, normalizing them to
6-digit OOXML RGB. Bar and column series also disable PowerPoint's negative-value
inversion so negative bars keep the same series fill instead of turning into
white/theme fill.

For ChartEx native charts, valid payload `style.colors` (or root `colors`)
populate the ChartEx color-style part instead of being replaced by a fixed
accent1–accent6 list. Other ChartEx style semantics remain normalized.

**PowerPoint chartEx schema**: `treemap`, `sunburst`, `histogram`, `pareto`,
`boxWhisker`, `waterfall`, and `funnel` use Office 2016+ chartEx parts. Use
these input shapes:

| Type | Required data |
|---|---|
| `treemap`, `sunburst` | `values` plus either `levels` (`levels[level][point]`) or path-style `categories` (`[["Region", "Group", "Leaf"], ...]`) |
| `treemap` display note | Top-level group labels default to `overlapping`; override with `parent_label_layout: "banner" \| "overlapping" \| "none"`. PowerPoint labels only the top level and leaves — intermediate levels group tiles spatially without labels (sunburst shows every ring). |
| `histogram` | `values` |
| `pareto`, `waterfall`, `funnel` | `categories` + `values`; `waterfall` also accepts `subtotals` / `subtotal_indices` point indexes |
| `boxWhisker` | `series[].values`; optional `series[].categories` per value |

> Note: chartEx files are valid PPTX and editable in PowerPoint; non-Microsoft
> renderers can display a limited subset.

**Stock chart schema**: `stock` uses numeric Excel date serials in
`categories` or `dates`, plus exactly four series in open / high / low / close
order. Use either `series` with four entries, or top-level `open`, `high`,
`low`, and `close` arrays. PPTX import currently recognizes only canonical OHLC
stock charts with shared numeric date caches, `hiLowLines`, and `upDownBars`.
Safe stock series style may pass the structural gate, but stock series,
`hiLowLines`, and up-down bar local styling can still normalize under the
data-object-first contract. HLC, volume, noncanonical structure, and style XML
outside the safe parsing boundary stay fallback-only.

**PPTX chart-import boundary**: The importer recognizes conservative classic
single-plot charts plus the verified scatter/bubble XY-axis, column/line/area
combo, area date-axis, canonical OHLC stock, radar, safe `of_pie` `serLines`,
axis/title/legend normalization, and bar/column gap/overlap subsets. Imported
`gapWidth` must be one canonical integer in `0..500`; imported `overlap` must be
one canonical integer in `-100..100`. Both values intentionally normalize to
the native writer contract rather than claiming exact source-style retention.
Malformed, duplicate, or out-of-range values fail closed.

ChartEx import is closed to seven validated data models: `treemap`, `sunburst`,
`histogram`, `pareto`, `box_whisker`, `waterfall`, and `funnel`. The importer
retains their supported hierarchy/category/value/series/subtotal topology for
native read-back. Numeric cache values must be non-empty and finite, and cache
counts/indexes must be canonical non-negative decimal integers with exact,
contiguous topology; malformed, non-numeric, `NaN`, infinite, sparse, duplicate,
or mismatched caches fail closed. ChartEx style, axis, label, and binning details
outside the payload normalize. Full `AxisSpec`, arbitrary ChartEx families or
presentation fidelity, arbitrary stock variants, and axis/combo/date-axis
semantics outside the closed fields above remain fallback-only. The C4/C5
import work does not expand the normalized SVG renderer and does not reduce
existing SVG-marker-to-native writer support.

**Deferred chart types**: Exploded pie / doughnut variants, `map`, `heatmap`,
`bullet`, and `gantt` are intentionally outside the current native-object
support boundary. The exporter fails fast for these types until each mapping is
implemented and validated one by one.

**Supported chart types**:

- `column`, `bar`: `clustered`, `stacked`, or `percentStacked` (`grouping`)
- `line`: `standard`, `stacked`, or `percentStacked` (`grouping`); `line` or `lineMarker` (`line_style`, default `line` / no markers)
- `area`: `standard`, `stacked`, or `percentStacked` (`grouping`)
- `pie`: exactly one series, per-slice colors
- `doughnut`: exactly one series, per-slice colors
- `pieOfPie`, `barOfPie`: exactly one series, per-slice colors
- `radar`, `radarMarkers`, `radarFilled`
- `scatter`: `marker` (default), `lineMarker`, `line`, `smoothMarker`, or `smooth` (`scatter_style`)
- `bubble`: x/y/size series
- `combo`: `column`, `line`, and `area` plots, optional secondary value axis
- `treemap`, `sunburst`: hierarchical chartEx charts
- `histogram`, `pareto`
- `boxWhisker`
- `waterfall`, `funnel`
- `stock`: open / high / low / close series

3D chart aliases (`3DColumn`, `3DBar`, `3DLine`, `3DArea`, `3DPie`, cone,
cylinder, pyramid variants, and `surface`) are unsupported.

Native legends are opt-in through `show_legend: true`; `legend_position`
defaults to `bottom` and accepts `top`, `left`, or `right`.

**Forbidden — replacement marker transforms**: Do not rotate, skew, or matrix-transform table/chart replacement groups. Translate / scale is accepted; complex transforms fail export because PowerPoint-native table/chart frames do not preserve arbitrary SVG transforms.

### PPTX Structure Routing

Every new SVG project declares one deterministic route. Free-design and brand-only projects use `pptx_structure.mode: flat`, omit `pptx_masters` / `pptx_layouts` / `page_pptx_layouts` / `page_layouts`, and author no Master/Layout/layer/placeholder metadata. Export keeps all represented content Slide-local while materializing one clean project-owned Master plus one Blank Layout from the current color/typography lock; stock content placeholders and unused built-in Layouts are removed, while the standard date/footer/slide-number capability hooks remain. Deck/layout template projects use `mode: structured`; `standard` / `fidelity` templates use their authored contract, while mirror templates use restored source identities and parentage.

**Hard rule — no structure inference**: Flat export performs no promotion or deduplication; every object stays Slide-local. Structured template export compiles only declared root identities, atomic fixed layers, and slot groups—it does not assign Layout families, cluster pages, infer placeholders, or repair missing metadata. Legacy structured/template projects must run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) first.

**Layout reuse**: Reuse one Layout key only when its ordered fixed Layout atoms and slot ids/types/effective indices/default bounds/binding modes are identical. Different wording, data, imagery, crop, or Slide-local carrier geometry does not create a new Layout. A genuinely different reusable contract gets a new key even when both pages are semantically `content`.

**Zero-slot Layout**: A named Layout may contain no slots and no fixed Layout atoms. This is valid for a cover, poster, full-visual page, or other fixed composition. Do not manufacture an empty `utility` kind or full-page fake `object` slot.

**Adaptive change**: Template `strict` preserves the selected prototype contract. `adaptive` retains the prototype Master and may create a new Layout identity only when fixed Layout atoms or slot topology/bounds change. Update the page mapping immediately while authoring the first such page; never mutate a reused key silently.

### Explicit PPTX Master / Layout / Placeholder Metadata

**Trigger**: This explicit metadata interface applies only to deck/layout template projects and structure-restoration workflows. `spec_lock.md` declares `pptx_structure.mode: structured`, complete unique `pptx_masters` / `pptx_layouts` rosters, one `page_pptx_layouts` assignment per generated page, and `page_layouts` as authoring-prototype provenance. Flat free-design/brand-only SVGs use none of these metadata fields.

**Project lock**: A Master row is `<master_key>: <PowerPoint picker name>`. A unique Layout row is `<layout_key>: <master_key> | <PowerPoint picker name> | <prototype source>`, where the source is a generated `P<NN>` or installed `template:<basename>`. A page assignment is `P<NN>: <layout_key>` under `page_pptx_layouts`. The SVG root values MUST match the assigned definition. A Layout key belongs to exactly one Master and must be globally unique. Reuse one key only when prototypes share identical ordered Layout atoms and slot ids/types/effective indices/default bounds/binding modes. An unused Layout uses a template SVG source and remains registered without a published carrier slide. Every structured route requires numeric `spec_lock.md` typography `title` / `body` rows.

**Template behavior**: Strict preserves the selected prototype's declared Master/Layout/slot contract. Adaptive retains its Master and may allocate a new Layout key/name only when fixed Layout atoms or slot topology/bounds change; update the lock during authoring. Mirror-created prototypes preserve restored source identity, literal paint, typography, effects, atomic geometry, and referenced assets. `standard` / `fidelity` never make source topology authoritative; mirror does not synthesize a replacement topology.

**Imported inherited-shape visibility**: PPTX import reads
`p:sld@showMasterSp` and `p:sldLayout@showMasterSp` as XML Schema booleans;
an absent value, `1`, or `true` enables the relevant inherited shapes, while
`0` or `false` disables them. A disabled Slide value suppresses both Layout
and Master drawable shapes on that page. A disabled Layout value suppresses
only its parent Master's drawable shapes; the Layout's own shapes remain.
Neither flag changes background inheritance, Slide-local objects,
placeholder geometry/style inheritance, or the Master/Layout relationship
graph. Flat SVG import bakes the effective visibility. Layered import keeps
every standalone part SVG and records the source-owned booleans as
`slides[].showInheritedShapes` and `layouts[].showMasterShapes` in
`inheritance.json`, `manifest.json`, and `native_structure.json`. This is an
import/analysis fact; it does not introduce a generated-authoring SVG marker.

**Master text-style contract**: Flat and structured export map the
locked `title` size to every `a:defRPr` in Master `p:titleStyle`. Level 1 in
both `p:bodyStyle` and `p:otherStyle` uses the locked `body` size; levels 2–9
use a deterministic descending hierarchy from `15/16` through `8/16` of that
size, rounded to 0.5 pt and floored at the smaller of 8 pt or the body size.
Existing per-level indentation and bullet properties remain unchanged.

| Master style | Locked source | XML field changed |
|---|---|---|
| `p:titleStyle` | `typography.title` | Every `a:defRPr@sz` |
| `p:bodyStyle` | `typography.body` | Level 1 plus derived level 2–9 `a:defRPr@sz` |
| `p:otherStyle` | `typography.body` | Level 1 plus derived level 2–9 `a:defRPr@sz` |

**Hard rule — narrow scope**: This Master update changes only Master
`p:txStyles//a:defRPr@sz`; it preserves level indentation, bullet, margin, and
paragraph settings. It does not rewrite direct run sizes on generated slides,
so the initial slide rendering remains controlled by the authored SVG. Missing
`title` or `body` rows fail flat or structured export.

**Layout level-one text-default contract**: For every text-bearing placeholder
whose first prototype run has a direct `a:rPr@sz`, explicit Layout export copies that
size to the generated Layout prompt run and
`p:txBody/a:lstStyle/a:lvl1pPr/a:defRPr@sz`. It does not rewrite Slide direct
runs or Layout levels 2–9. This preserves the layout-specific size when
level-one placeholder text is inserted or reset; placeholders without a direct
prototype size remain unchanged.

| Metadata | Placement | Behavior |
|---|---|---|
| `data-pptx-master="master-default"` | root `<svg>` | Binds the slide to one generated Slide Master key |
| `data-pptx-master-name="Default Master"` | root `<svg>` | Sets the Master picker/display name |
| `data-pptx-layout="content"` | root `<svg>` | Binds the slide to one generated reusable layout key |
| `data-pptx-layout-name="Title and Content"` | root `<svg>` | Sets the PowerPoint layout-picker name; defaults from the layout key |
| `data-pptx-layer="master"` | direct semantic atom | Moves one repeated static object/background into the named Slide Master; ordinary `<g>` is forbidden, while one validated compact authored-preset `<g>` (§1.5) is an atomic exception |
| `data-pptx-layer="layout"` | direct semantic atom | Moves one repeated static object/background into the selected Layout; ordinary `<g>` is forbidden, while one validated compact authored-preset `<g>` (§1.5) is an atomic exception |
| `data-pptx-layer="slide"` | direct full-canvas solid `<rect>` only | Writes a one-page override as Slide `p:bg` |
| `data-pptx-placeholder="..."` | direct slot `<g id>` | Declares a reusable Layout slot whose visible content remains Slide-local |
| `data-pptx-placeholder-bounds="x y width height"` | slot `<g>` | Supplies the positive reusable design-zone frame in SVG user units |
| `data-pptx-placeholder-idx="1"` | slot `<g>` | Retains an imported source Layout placeholder index; optional for reconstructed layouts |
| `data-pptx-placeholder-carrier="true"` | one compatible direct child of a normal slot | Binds that visible child as the real Slide placeholder carrier |
| `data-pptx-placeholder-binding="proxy"` | composite `object` slot `<g>` only | Keeps the visible group ordinary and creates one hidden transparent binding proxy |
| `data-pptx-editable="false"` | master/layout element or slide background | Declares intentional editing outside ordinary slide content |

**Hard rule — explicit only**: On a structured deck/layout template route, every SVG requires the four root Master/Layout identity attributes. Every Master/Layout atom and slot requires a unique stable `id` and is a direct root child. Layouts with zero slots are valid. `data-pptx-layout-kind`, `distilled`, and `utility` are legacy metadata and fail the structured contract. Flat free-design/brand-only pages omit the entire interface.

**Layer order**: Author the SVG in PowerPoint paint order: Master background,
Layout background, optional Slide background, remaining Master atoms, remaining Layout atoms,
then slot groups and Slide-local content groups. Backgrounds are a special inheritance
plane beneath every shape; this order keeps standalone SVG preview and
PowerPoint rendering aligned. The exporter rejects interleaved layers.

**Solid background ownership**: Structured export deliberately narrows scoped
background ownership to a direct full-canvas solid `<rect>` and disables the
generic conversion-level promotion described in §4.2. Mark the solid rect
`data-pptx-layer="master"` for the deck-wide default,
`data-pptx-layer="layout"` for a page-type override, or
`data-pptx-layer="slide"` for a one-slide override. An unmarked direct
full-canvas solid rect in the background plane is also treated as Slide scope.
A Layout background overrides the Master background; a Slide background
overrides both. Use the Master for a globally stable color and the Layout for
cover/section/content variants under the same design language. Gradient and
preset-pattern rects remain ordinary shapes on declared Master/Layout layers
or as Slide-local content; images remain pictures. Textures, transformed rects,
and visible-stroke rects also remain ordinary objects.

| Placeholder value | Direct carrier inside slot `<g>` | PowerPoint placeholder |
|---|---|---|
| `title`, `subtitle`, `body` | one `<text data-pptx-placeholder-carrier="true">` | `title`, `subTitle`, `body` |
| `date`, `footer`, `slide-number` | one `<text data-pptx-placeholder-carrier="true">` | `dt`, `ftr`, `sldNum` |
| `picture` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `pic` |
| `chart`, `table` | one matching `data-pptx-replace-with` marker group, marked as carrier | `chart`, `tbl` |
| `object` | one text, image, basic SVG shape, or validated compact authored-preset `<g>` marked as carrier; alternatively the slot group declares `binding="proxy"` | `obj` |
| `media` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `media` |

**Text slot carrier**: A multiline text placeholder must remain one
native text frame. Use the default paragraph merge; `--no-merge` cannot supply
several line shapes as one
PowerPoint placeholder prototype/binding. Leave strict-line text Slide-local
when separate frames are the required result.

**Blank text carrier**: Leave a marked text carrier empty or whitespace-only
when the placeholder must remain visually blank. Export materializes one
invisible U+200B run so the carrier still becomes a native PowerPoint text
shape. Do not insert a dummy dash, shrink text below the DrawingML 1pt minimum,
or hide a visible glyph with opacity/background paint; those workarounds either
leak content or produce a PPTX that PowerPoint repairs.

`title` is normally type-matched without an index in reconstructed layouts; if
an imported source title explicitly has one, preserve that exact index. Every
indexed placeholder on one layout uses a unique OOXML UInt32 index. Structured export writes the semantic type on both the Layout and Slide carrier (except `obj`, whose OOXML default is already `obj`) so PowerPoint and `python-pptx` retain the same identity. A composite object slot instead keeps its visible group ordinary and uses a hidden transparent proxy.
Date, footer, and slide-number placeholders enable their matching Layout `p:hf`
flags; a date placeholder also gets a `datetimeFigureOut` field in the reusable
Layout definition. The current Slide keeps its authored date content.

Because an omitted `p:ph@idx` has the effective value `0`, an omitted-index
title reserves `0`; no other placeholder on that Layout may use the same
effective index.

**Slot prototype**: The prototype source declared by the unique Layout definition supplies that Layout's placeholder formatting. `data-pptx-placeholder-bounds` supplies the reusable default frame and is mandatory on every slot. Derive it from
the intended design zone, column, panel inset, safe area, or picture frame —
never from text length, glyph width, line count, or a tight content bounding
box. Repeat the same slot ids/types/effective indices/default bounds/binding modes on every slide using that Layout. The Layout owns the reusable `p:ph`; normal visible carriers keep a matching Slide binding so approved rendering stays identical. A composite `object` proxy adds one hidden transparent binding shape to suppress empty inherited placeholder paint. Bounds define the Layout default only; actual Slide content and local carrier geometry may differ.

**Final-package read-back gate**: After writing a temporary structured PPTX and before publishing it, export reopens the package and
verifies that each published Slide targets exactly one Layout, one Layout key always resolves to the
same part, different keys do not collapse onto one part, and every declared Layout—including one unused by all published Slides—is
registered through its Master and the Presentation. Physical Slide/Layout/
Master part rosters, their content-type overrides, and their Presentation/
Master registrations must be exact. It also verifies the Layout picker name,
Master picker identity, placeholder type and effective index, matching `p:hf` flags, explicit design-zone frame, direct prompt size, and level-one default size.
Every owned `p:bg` is checked as an exact zero-or-one payload against the pre-
promotion result; this includes preserving the base Master background when no
authored Master background replaces it. During the same export, every finished
Slide, Layout, and Master must reproduce its exact top-level shape-name roster
and order after packaging. The gate verifies that each carrier-bound slot owns the expected Slide binding, each composite visible carrier remains ordinary, and every composite binding proxy is hidden. A zero-slot Layout must read back with no placeholder. Later slides may keep different Slide-local geometry; only the reusable
Layout frame is checked against the explicit/prototype contract. Any mismatch
fails export without replacing the requested output.

**Static structure consistency**: Repeat the same master element ids on every
slide and the same layout element ids on every slide sharing a layout. Their
generated OOXML must be identical within the affected master/layout group.
Static structure may carry shapes, text, or images; non-image/external
relationships are rejected. Every static object is atomic. An ordinary
`<g data-pptx-layer="master|layout">` is forbidden; the validated compact
authored-preset group from §1.5 is the sole group exception because it compiles
to one native object. A full-canvas first rect may be marked as a Master or
Layout background.

**Native object slot carriers**: `chart` / `table` slots require
`--native-charts-and-tables`; fallback groups contain several shapes and cannot map to one
PowerPoint placeholder. `object` is the generic PowerPoint content slot and
uses either one carrier object—including one validated compact authored-preset
group—or the explicit composite proxy downgrade. `media` currently binds
an authored image/crop to a native `media` placeholder; it does not synthesize
video or audio media from a decorative SVG group.

### Legacy Structure Migration Boundary

Existing structured/template projects or packages that carry `native_structure.json` / `source_template.pptx`, `pptx_structure.mode: baseline|template|preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled` / `utility`, direct atomic placeholders, or an incomplete root Master identity must run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) before generation or export. A project explicitly declaring `pptx_structure.mode: flat` is the current free-design/brand-only route and does not require restoration merely because it has no Master/Layout metadata.

When original PPTX/native facts exist, migration preserves the complete source Master roster, Layout parent relationships and picker names, placeholder type/index/bounds, and visible supported geometry while normalizing the package into the explicit contract. Source Master/Layout groups are recursively flattened into atomic SVG elements. Create one reusable prototype SVG for every retained Layout, including Layouts unused by source slides; downstream `pptx_layouts` definitions can register those prototypes without manufacturing generated pages. A subsequent `create-template` run treats the result according to its selected mode: `standard` / `fidelity` author a new topology, while mirror keeps the restored source topology. When no native facts exist, the main Agent explicitly derives a structured contract from the complete SVG pages; the exporter never performs that derivation.

---

## 8. Scope Boundary

Project structure, commands, quality-gate order, and export products are owned
by [`SKILL.md`](../SKILL.md). They are intentionally outside this SVG
authoring policy.
