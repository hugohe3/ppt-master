# Shared Technical Standards

Mandatory reference for every PPT Master route that authors or regenerates slide visuals through SVG: owns shared XML/SVG constraints, editable PPTX mappings, advanced effects, geometry recipes, and PPT-specific interfaces.
Other files link here instead of restating its contracts.

**Document map**:

| Section | Owns | Strength |
|---|---|---|
| §1 Required Foundation, Forbidden Features, and Conditional Interfaces | XML validity, the exhaustive structural blacklist, native line ends, image clipping, static local reuse, and imported/authored native-shape semantics | Required / Forbidden / Conditional |
| §2 Conditional Compatibility Mappings | Inline geometry and approximate group opacity | Conditional |
| §3 Canvas Format Quick Reference | Pointer to the complete canvas catalog | Reference |
| §4 Required Page Contract and Conditional Packaging | Complete-page authority, semantic markers, editable text/grouping, and package promotion | Required / Conditional |
| §5 Workflow Authority | Pointer to the serial post-processing/export procedure | Workflow pointer |
| §6 Advanced SVG Effects and Authoring Techniques | Color/alpha, gradients, shadows, glow, overlays, lines, text treatments, transforms, freeform geometry, chart geometry, and constructed visual styles | Contract + optional recipes |
| §7 Conditional PPT Interfaces | Pattern fills, native tables/charts, Master text styles, and Master/Layout/placeholder metadata | Conditional |
| §8 Scope Boundary | Concerns intentionally owned by another reference or workflow | Boundary |

**Advanced capability index**:

| Capability family | Available authoring vocabulary | Detail |
|---|---|---|
| Color and transparency | CSS alpha colors; fill, stroke, text, picture, stop, element, and group opacity | §2.2, §6.2 |
| Gradients and paint | Linear/radial fills, transparent stops, gradient text, gradient strokes, and preset patterns | §6.3, §7 |
| Depth and light | Soft/colored/directional shadow, glow, layered-geometry fallback, and paper-layer elevation | §6.4 |
| Image treatment | Directional scrim, bottom fade, vignette, spotlight, brand wash, picture fading, and glass-like surfaces | §1.2, §6.5 |
| Lines and connectors | Preset/custom dash, cap/join, gradient flow strokes, markers, and explicit-grid paths | §1.1, §6.6 |
| Text treatments | Mixed runs, tracking, underline, strikethrough, gradient fill, outline, transparency, watermark text, and text glow | §4.2, §6.7 |
| Transforms and composition | Translate, scale, rotate, mirror, supported matrix composition, layering, and static local reuse | §1.3, §6.8 |
| Freeform geometry | Full SVG path vocabulary, curves, organic containers, multi-subpaths, and asymmetric rounded rectangles | §6.9 |
| Imported PowerPoint shapes | All 187 preset geometries, adjustments, logical frames, custom geometry, connectors, and unchanged native text bodies | §1.4 |
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

The blacklist above is exhaustive for globally forbidden SVG syntax. Features
that require a restricted form are not globally forbidden; they are documented
under the conditional contracts below.

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
> **Inline CSS geometry, group opacity, simple gradients, and filters are
> conditional** — see §2 and §6.
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
| Orientation | `orient="auto"` |
| Shape | A 3-vertex `<polygon>` / closed M/L-only path (triangle), 4-vertex `<polygon>` / closed M/L-only path (diamond), or one `<circle>` / `<ellipse>` (oval) |
| Path grammar | One explicit `M`/`L` command per vertex followed by `Z`; do not use `H`, `V`, curves, or an implicit multi-point `L` command inside a marker path |
| Color parity | Marker fill matches the parent line stroke; DrawingML arrows inherit the line color |

The converter maps the three shapes to DrawingML triangle, diamond, and oval
line ends. Prefer `<polygon>` for triangle/diamond markers because the vertex
count is unambiguous. Other marker shapes do not have a native mapping and are
dropped with a warning.

---

### 1.2 Image Clipping (Conditional Contract)

`clip-path` has a native picture-geometry mapping only on `<image>` elements and
only under this contract:

| Concern | Required form |
|---|---|
| `<clipPath>` element defined inside `<defs>` | Converter looks up clip defs via id index |
| Contains a **single supported** shape child | The converter uses the first supported child; multiple shapes are not composited |
| Shape is one of: `<circle>`, `<ellipse>`, `<rect>` (with rx/ry), `<path>`, `<polygon>` | These map to DrawingML geometry (preset or custom) |
| Used **only on `<image>` elements** | Non-image elements with clip-path are **forbidden** |

| SVG clip shape | DrawingML output |
|---|---|
| `<circle>` / `<ellipse>` | Full-frame `<a:prstGeom prst="ellipse"/>`; child center/radii are not preserved |
| `<rect rx="..."/>` | Full-frame `<a:prstGeom prst="roundRect"/>` with one radius adjustment; child x/y/width/height are not preserved |
| `<path>` / `<polygon>` | `<a:custGeom>` with coordinates mapped into the image frame |

`clip-path` on shapes, groups, or text is forbidden; author the target geometry
directly instead. Use a path/polygon clip when the intended contour does not
cover the full picture frame.

---

### 1.3 Static Same-Document `<use>` (Conditional Contract)

**Expansion contract**: Static local reuse is compile-time authoring shorthand. `finalize_svg.py` and
native export replace each qualifying instance with cloned primitive content;
PPTX-to-SVG import emits the resulting primitives and does **not** reconstruct
the original `<use>` / `<symbol>` structure.

| Concern | Required form |
|---|---|
| Reference syntax | Exact same-document fragment: `href="#id"` or `xlink:href="#id"`. If both attributes exist, their values MUST match. |
| Referenced target | One of `<symbol>`, `<g>`, `<use>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<polygon>`, `<polyline>`, `<text>`, or `<image>`. Nested local `<use>` is recursively expanded. |
| Instance position | `<use x>` / `<use y>` are finite unitless or `px` values; omitted values default to `0`. |
| Symbol viewport | A referenced `<symbol>` MUST have a finite four-number `viewBox` with positive width/height. Its `<use>` MUST have positive finite unitless or `px` `width` and `height`. |
| Aspect ratio | Default/aligned `meet` values and plain `preserveAspectRatio="none"` are supported. `slice`, `refX`, and `refY` are forbidden. |
| Viewport boundary | Symbol artwork MUST stay inside its `viewBox`; expansion does not reproduce symbol overflow clipping. |
| Internal references | Reusable subtrees use exact fragment forms: `href="#id"`, `xlink:href="#id"`, and `url(#id)`. The expander rewrites these references together with instance-local cloned IDs. |
| Structural metadata | Neither the `<use>` instance nor its referenced subtree may carry `data-pptx-layer*`, `data-pptx-native*`, or `data-pptx-placeholder*`. Author those objects directly instead of reusing them. |
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
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
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
  <use xlink:href="#legendRow" x="120" y="120"/>
</svg>
```

---

### 1.4 Imported Native PowerPoint Shapes (Conditional Contract)

`pptx_to_svg.py` emits rendering-neutral metadata when a visible SVG object
originates from `p:sp`, `p:cxnSp`, or `p:grpSp`. This contract is for imported
round-trip SVG; ordinary authored SVG does not need these attributes.

| Metadata | Placement | Required behavior |
|---|---|---|
| `data-pptx-object` | Logical `<g>` and native carrier | `shape`, `connector`, `group`, or `picture`; never infer the object kind from path appearance. |
| `data-pptx-shape-id` + `data-pptx-shape-scope` | Logical `<g>` and carrier | Preserve the source part-scoped identity. Export remaps duplicate Master/Layout/Slide ids into page-unique ids before restoring connector references. |
| `data-pptx-frame="x y width height"` | Logical `<g>` and carrier | Own native `a:xfrm` position and size. Values use sufficient precision for exact EMU recovery; path bounds, stroke, markers, shadows, and text glyph bounds never replace this frame. |
| `data-pptx-prst` | Preset carrier and logical `<g>` | One of the locked 187 DrawingML `ST_ShapeType` values. |
| `data-pptx-av-*` | Preset carrier and logical `<g>` | Preserve the complete validated DrawingML adjustment formula, including non-`val` formulas. |
| `data-pptx-part="geometry"` | One hidden carrier path | The single native export authority for frame, base fill/line/effect, preset/custom geometry, and object identity. |
| `data-pptx-part="geometry-preview"` / `geometry-detail` | Visible preview group/paths | Render the preset's independent path fill/stroke layers. These elements are never emitted as duplicate PowerPoint shapes. |
| `data-pptx-preview-sha256` | Logical preset `<g>` and carrier | Detect edits to visible preset paths or paint. A stale preview fails quality check/export instead of silently restoring old native metadata. |
| `data-pptx-geometry-kind="custom"` + `data-pptx-custgeom` | Custom-geometry carrier | Preserve the validated original `a:custGeom` subtree. If the visible path hash is unchanged, export restores formulas, handles, connection sites, text rectangle, and path list exactly; edited paths compile from current SVG geometry. |
| `data-pptx-start/end-shape-id/site` | Connector logical `<g>` and carrier | Restore `a:stCxn` / `a:endCxn` after scoped shape-id allocation. A connector may retain one zero frame axis; it must not be expanded from visible stroke or marker bounds. |
| `data-pptx-shape-style` | Native carrier | Preserve a relationship-free `p:style` independently of text, including shapes with no visible text. |
| `metadata[data-pptx-part="txbody"]` | Logical shape `<g>` | Preserve unchanged `p:txBody`, including an empty text body. Content, whitespace, positioning, or visible typography edits invalidate the payload and use the normal SVG text fallback. |

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

New SVG pages may opt one complete geometric object into a native DrawingML
preset through the deterministic fragment helper. Selection behavior lives in
[`native-shape-authoring.md`](./native-shape-authoring.md); this section owns
the machine contract.

| Metadata / structure | Required behavior |
|---|---|
| `data-pptx-authoring="preset"` | Appears on the logical group and hidden carrier; distinguishes the strict new authoring contract from legacy/imported metadata. |
| `data-pptx-object` | `shape` or `connector`; connector-family presets must use `connector`, and `connector` must use a connector-family preset. Authored connectors require `fill="none"` plus a visible stroke and export as unconnected `p:cxnSp`. |
| `data-pptx-prst`, `data-pptx-frame`, `data-pptx-av-*` | Generated together from the locked registry; group and carrier values must be identical. |
| One direct `path[data-pptx-part="geometry"]` | Hidden native export authority; carries the same semantics and solid paint used for regeneration. |
| One direct `g[data-pptx-part="geometry-preview"]` | Complete browser-visible preview with one ordered detail path per registry path. |
| `data-pptx-preview-sha256` | Identical on group/carrier and equal to an independent registry rerender of metadata, paint, and preview. |

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
metadata on a hand-written leaf. The helper output is atomic. Regenerate it
when preset, frame, adjustment, fill, stroke, or stroke width changes. Replace
the whole fragment with ordinary SVG when free contour editing is required.

**Hard rule — visible page closure**: the helper prints a complete visible
fragment to stdout; export never invents its preview. The main Agent inserts
that output into the hand-authored page. The helper cannot write a project,
select layout, or generate a page.

**Authoring paint boundary**: v1 accepts `none` or six-digit solid HEX fill and
stroke, optional fill/stroke opacity, stroke width, line cap, and line join.
Colors come from `spec_lock.md`. Use ordinary SVG for gradients, patterns,
filters, or other treatments outside this narrow contract.

**Validation**: quality check and export both rerender authored fragments from
`preset + frame + adjustments + carrier paint`. They require one carrier, one
preview, equal group/carrier semantics, exact ordered registry paths, and a
matching fingerprint. Preview edits, metadata-only edits, unknown adjustments,
out-of-range frames/transforms, zero-scale transforms, and shear/skew fail
closed.

**Fidelity boundary**: an unchanged authored fragment is `Native-stable` as
one `p:sp` or `p:cxnSp`. Text remains outside the atomic fragment and may export
as a grouped editable text box. Authoring v1 creates only unconnected
`p:cxnSp`; it does not accept hand-written endpoint/site metadata. An
`actionButton*` preset maps visual geometry only. Preset appearance never
invents connector attachment, action behavior, navigation targets, or
hyperlinks.

---

## 2. Conditional Compatibility Mappings

### 2.1 Literal Inline Geometry

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

### 2.2 Group Opacity Is Approximate

`<g opacity="0.3">...</g>` maps the group alpha onto each descendant shape,
text run, picture, and supported
shadow/glow effect. Nested group and child opacity values multiply. Overlapping
children may differ from SVG isolated-group compositing because DrawingML has no
equivalent group-alpha model. With `--native-objects`, transparent native
table/chart markers are rejected; omit that flag to export their SVG fallback.

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

Semantic markers are minimal compiler hints orthogonal to native SVG semantics.
Existing `data-pptx-layout` / layer / placeholder / native-object metadata is
authoritative and read first. A `baseline` / free-design root declares
`data-pptx-page-role`; template/preserve roots already declare their Layout.
Add `data-pptx-role` only when no specialized marker expresses the required
page-frame behavior; the element also uses a stable unique `id`. Do not classify
ordinary page content or move visible facts out of SVG attributes/text into
metadata. See
[`semantic-svg.md`](semantic-svg.md) for the canonical vocabulary and examples.

- **Canvas authority**: `viewBox` MUST match the selected canvas dimensions.
  Root `width` and `height` are optional and do not override it. Root `<svg>`
  `transform` is forbidden; apply transforms to child elements or groups.
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
| One editable PPT text frame with mixed inline formatting | Put the logical line in one `<text>` with non-positional `<tspan>` children. A `<tspan>` with `x`/`y`/`dy` starts a new positioned line; evenly `dy`-stacked lines that repeat the parent `<text>`'s `x` **merge into one frame as multiple paragraphs** (the default paragraph-merge), while an irregular gap or a mismatched `x` flattens to separate frames. Separate `<text>` elements stay valid when separate frames are intended. |
| Stable object grouping or object-level animation anchor | Wrap the intended object in `<g id="...">`. Content grouping is **mandatory** per §4.3 — a top-level `<g id>` is also the animation anchor; it is not an optional convenience. |
| Native PowerPoint background promotion | Use a direct, full-canvas, solid `<rect>` without transform, filter, clip, rounding, or visible stroke. Other SVG backgrounds remain ordinary slide shapes. Template routes add the ownership metadata in §7. |
| Free-design page family/chrome extraction | Use the semantic markers in §4.1. Marker-free pages retain conservative filename/id fallbacks, but no visual content is inferred. |

**Hard rule — supported shape conversion**: Every PPT editability claim in this specification refers to the project converter reading `svg_output/` and emitting native DrawingML. `svg_final/` is a self-contained visual preview that may be inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is unsupported; do not narrow the authoring contract to its undocumented SVG subset.

### 4.3 Element Grouping (Mandatory)

Wrap logically related elements in top-level `<g id="...">` groups. This is **required on every generated page**, not an optional convenience: it produces real PowerPoint groups in the exported PPTX (easier to select / move / edit) and gives each content unit a stable anchor for optional per-element entrance animation. Plain `<g>` is the normal grouping primitive; `<g opacity="0..1">` additionally maps to the per-descendant alpha approximation in §2.2.

**Semantic-group rule**: direct children of `<svg>` are semantic content groups, **not** raw drawing atoms. Aim for **3–8 top-level content `<g id>` groups per slide** (the budget excludes page chrome — see below); each content group becomes one entrance step under the chosen animation trigger (one click in `on-click`, one cascade slot in `after-previous`, parallel in `with-previous`). Leaving titles, body lines, list items, cards, or decorative clusters as ungrouped top-level `<text>` / `<rect>` / `<path>` is a contract violation, not a style choice.

**Chrome is excluded automatically.** Existing `data-pptx-layer` and `data-pptx-placeholder="slide-number"` semantics are read first; otherwise explicit `data-pptx-role` values (`background`, `decoration`, `header`, `footer`, `chrome`, `watermark`, `page-number`, `logo`) mark static framing (§4.1, [`semantic-svg.md`](semantic-svg.md)). Marker-free legacy SVGs keep id-token fallbacks. Keep the `<g>` wrapper on chrome for editing/grouping even though it does not count against the 3–8 content budget.

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

An authored native preset fragment (§1.5) is already an atomic `<g id>` and counts as one content group; keep its labels / decorations in a sibling parent `<g>`, never inside the preset group.

**Forbidden**:

- One giant `<g>` around the whole slide (collapses to a single animation step).
- Many ungrouped top-level `<rect>` / `<text>` / `<path>` — fallback animation caps at 8 primitives, dense pages may skip animation, and selection/editing degrades.
- One group per icon / text line / mark (too many steps).
- Anonymous top-level groups — every top-level semantic group needs a descriptive `id`.

**Naming — required.** A descriptive `id` on every top-level content `<g>` (`card-1`, `step-discover`, `header`, `footer`) is mandatory; it is the animation anchor and the group identity in PPTX. Without it, the exporter falls back to at most 8 top-level primitives or skips animation on dense pages.

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

Supported paint grammar: recognized named colors, `rgb()` / `rgba()`, `hsl()` /
`hsla()`, and `#RGB` / `#RGBA` / `#RRGGBB` / `#RRGGBBAA`. Bare hexadecimal
without `#` is invalid.

| Authoring surface | Native result | Fidelity |
|---|---|---|
| `fill-opacity`; `stroke-opacity` | Fill, text, line, or outline alpha | `Native-stable` |
| CSS color alpha | Alpha-bearing named/functional/HEX paint | `Native-normalized` |
| Element `opacity` | Alpha compiled into supported paint/effect channels | `Native-normalized` |
| `<image opacity>` | Picture `<a:alphaModFix>` | `Native-stable` |
| `<stop stop-opacity>` | Per-stop gradient alpha | `Native-stable` |
| `<g opacity>` | Alpha multiplied into each supported descendant shape, text run, picture, and effect | `Approximate` |
| Pattern child/color alpha | Preset-pattern foreground/background alpha | Conditional; §7 |

```text
effective fill alpha
= color alpha × element opacity × fill-opacity × ancestor group opacity
```

**Hard rule — alpha grammar**: write `opacity`, `fill-opacity`,
`stroke-opacity`, and `stop-opacity` as finite numbers from `0` to `1`.
`fill="transparent"` / `stroke="transparent"` become no fill/line; use a color
plus alpha when a painted transparent layer must remain represented. Group
alpha is not isolated compositing, so overlapping descendants may differ from
the browser. Transparent groups around `data-pptx-native` chart/table markers
cannot be promoted under `--native-objects`; export the SVG fallback or remove
the group opacity.

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
The quality checker validates definition location, references, and paint context.

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
| Accepted helpers | `feOffset`, `feFlood`, `feComposite`, `feMerge`, `feMergeNode`, `feComponentTransfer`, linear `feFuncA` |
| Classification | Meaningful non-zero offset → one outer shadow; zero/no offset → one glow |
| Fidelity | `Approximate`; one filter becomes one DrawingML effect |

Flood/color alpha, linear `feFuncA slope`, element opacity, and ancestor opacity
multiply. Native export does not preserve filter-region, `in/in2/result`, merge
order, or composite topology. Other primitives, multiple independent effects,
filters on `<image>` / `<tspan>` / unsupported targets are forbidden. Do not
put a filter on a multi-element `<g>`; apply it to supported objects or use
explicit layers.

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

**Hard rule — fit/clip interaction**: a non-trivial clip disables `meet`
frame-fit. Match the image box to the source ratio or use `slice`. Do not apply
filters directly to `<image>`.

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
| `4,4`; `2,2`; `8,4`; `8,4,2,4` | `dash`; `sysDot`; `lgDash`; `lgDashDot` (`Native-normalized`) |
| Other custom dash | Exactly two positive finite unitless numbers (`dash gap`); export scales/quantizes against stroke width; longer arrays reduce to the first pair; `Native-normalized` |
| `stroke-linecap` | `butt`, `round`, `square`; `Native-stable` |
| `stroke-linejoin` | `miter`, `round`, `bevel`; `Native-stable` |
| Gradient stroke | §6.3; re-import may flatten to first stop |
| `marker-start` / `marker-end` | §1.1 native line end; type `Native-normalized`, size `Approximate` (`sm/med/lg`) |

Match marker fill to the parent stroke. Use markers for connectors and §6.10
calculated geometry for a manual diagonal arrowhead. When exact grid spacing
matters, use one multi-subpath path rather than a fixed-density preset pattern:

```xml
<path d="M40 0V120 M80 0V120 M0 40H120 M0 80H120"
      fill="none" stroke="#2E6EA8" stroke-width="0.8"/>
```

---

### 6.7 Advanced Text Treatments

| Treatment | SVG surface | Result / boundary |
|---|---|---|
| Underline / strike / both | `text-decoration="underline"`, `line-through`, or both | `Native-stable`; both emits both run properties |
| Mixed runs | Non-positional `<tspan>` | One `Native-normalized` editable frame; §4.2 |
| Tracking | Numeric `letter-spacing` | `Native-normalized`; unitless/`px` = SVG px, `pt` converts to px, `em` resolves against run size |
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
| Positive scale / negative mirror | Geometry/image only; explicit pivot; `Native-normalized` |
| `matrix(a b c d e f)` | Geometry/image only; transformed axes finite, non-zero, orthogonal; excludes rounded rects; `Native-normalized` |
| Source order | Back-to-front PPT z-order; `Native-stable` |
| `<g opacity>` | Descendant alpha; `Approximate`, §2.2 |
| Local `<use>` | §1.3 compile-time reuse; `Native-normalized` |

Set text size/position directly; do not scale or general-matrix text. `skewX`,
`skewY`, zero/non-orthogonal axes, and shear matrices are forbidden. Native
chart/table markers allow translate/scale only. The §6.10 thick-circle shortcut
does not inherit general transform support. Positive rotation is clockwise and
pivoted rotation normalizes the native frame. A legal transform sequence can
still produce non-orthogonal axes; importer/live-editor matrices do not expand
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

- One circle per segment; `fill="none"`; no element transform or ancestor full-matrix.
- Exactly two non-preset finite unitless values (`dash gap`); finite unitless `stroke-dashoffset`.
- `0 < stroke-width < 2r`, `stroke-width/r >= 0.15`,
  `0 < dash < 2πr`, `gap >= 0`, and `dash + gap >= 2πr`.
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
| Gradient ribbon | Thick cubic path + §6.3 gradient stroke | `Native-normalized`; no mesh gradient; re-import may flatten color |
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

`data-pptx-pattern="<preset>"` is required to select the intended preset from
the enum below; without it, export falls back to `ltUpDiag`.

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

`svg_quality_checker.py` warns when the annotation is missing and errors when
the preset is outside this enum.

### Native PPTX Table / Chart Markers (Opt-in)

Native PowerPoint tables and Excel-backed charts activate at export time only. The default chart/table route remains hand-authored SVG geometry so the deck stays pixel-stable across PowerPoint / Keynote / LibreOffice / WPS.

**Authoring — markers are standard on supported data charts and text-grid tables**: Executor writes the marker at draw time on every data chart whose type falls in the supported set and on every pure text-grid data table ([executor-base.md §3.2](executor-base.md)), so any deck can later form native objects without regeneration. Canonical rectangular merged text cells may use the narrow `row_span` / `col_span` contract below; graphical cells stay unmarked on the SVG fallback route. The marker group supplies both: visible SVG fallback children for browser/live-preview rendering, and JSON metadata for `svg_to_pptx` native export.

**Hard rule — activation is the opt-in, dormant unless exported with `--native-objects`**: A marker only declares that a group is eligible for native export. Normal `svg_to_pptx.py` runs keep the fallback SVG children. Pass `--native-objects` only when editability in PowerPoint matters more than cross-renderer layout fidelity: it emits the PowerPoint object and skips the fallback children to avoid duplicates. Native styling preserves the core palette, text, axis, grid, and background colors where possible, but it is still a PowerPoint chart/table object rather than a pixel-identical SVG drawing.

The native route is deliberately editable-first and may be lossy: marker-local labels, callouts, KPIs, guide lines, custom split/bin semantics, or styling that is absent from the payload may disappear or normalize. Export warns about this route-level risk and any narrower issue it can detect. Loss of visual parity is not grounds to remove an active marker that the emitter can otherwise convert; use the default SVG-fallback export when exact authored artwork matters more than editability.

| Marker | Native output | Required metadata |
|---|---|---|
| `<g data-pptx-native="table">` | `<p:graphicFrame>` with `<a:tbl>` | bounds + `columns` or `rows` |
| `<g data-pptx-native="chart">` | `<p:graphicFrame>` with `c:chart` / `cx:chart` + chart part + embedded workbook | bounds + `type`, plus chart data |

**Metadata placement**: Put JSON in a child `<metadata data-pptx-native="...">`. Attribute JSON (`data-pptx-json="..."`) is supported but harder to XML-escape correctly.

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

**Validation**: `svg_quality_checker.py` validates native marker kind, JSON
metadata, bounds/fallback availability, table rows/columns, supported chart
type, chart data shape, and any imported fallback baseline before export.

**Hard rule — imported fallback freshness**: active table/chart markers emitted
by `pptx_to_svg.py` carry `data-pptx-fallback-sha256`, a canonical hash of the
marker fallback plus reachable document-level SVG fragment definitions. Editing
geometry/text/paint, switching a local `url(#...)` or `href="#..."` target,
changing a reachable definition, or changing the marker transform makes the
native metadata stale. The mandatory quality checker warns and the default route
keeps the edited SVG; `--native-objects` hard-fails before replacement so it
cannot discard that edit. Metadata/title/description nodes, `data-pptx-*`
runtime attributes, marker-local stable ID renames, and marker-local
`display:none` subtrees are excluded. `visibility:hidden` content,
marker-local unused definitions, and explicitly referenced document-level
target roots (even when hidden) remain conservatively hashed. External
image/font file bytes are not read.
Hashless legacy markers remain native-compatible and warn in the checker/native
route that stale detection is unavailable. A stale hash is an integrity mismatch,
not a visual-parity gate on an unchanged active marker.

**Hard rule — imported visual/route status**: A PPTX chart with a complete baked preview
may carry `data-pptx-visual-status="source-preview"`. Supported parsed classic
families without a preview use a deterministic readable fallback marked
`data-pptx-visual-status="normalized"`; it is explicitly not source-exact.
When no current renderer exists, the importer emits its typed reconstruction aid with both
`data-pptx-visual-status="placeholder"` and
`data-pptx-route-status="reconstruction-only"`. The valid pair is diagnostic:
quality checking and export warn, default export keeps the placeholder, and
`--native-objects` may reconstruct an editable chart when the same group has a
valid active `data-pptx-native="chart"` payload. The allowed values and pair
remain closed; unknown, whitespace-padded, or contradictory values fail.
`data-pptx-native` and `data-pptx-native-status` are mutually exclusive on the
same visible group.

```xml
<g id="p03-revenue-chart" data-pptx-native="chart">
  <metadata data-pptx-native="chart">
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
For plain multi-paragraph text, replace `text` with a non-empty `paragraphs`
list. Each entry is either a string or `{ "text": "...", "align": "l|ctr|r" }`;
empty paragraph strings are preserved, and `text` / `paragraphs` are mutually
exclusive. This is paragraph-level plain text, not run-level rich text.
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
`--native-objects` must be present in `columns` / `rows`. SVG fallback text is
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
metadata whose text is not visible inside the native marker's fallback. Direct
`--native-objects` export keeps the chart native but omits that inconsistent
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
`grid_color`; use `"none"` for transparent chart or plot area fill. Color
values may be `#RRGGBB`, `#RGB`, `rgb(...)` / `rgba(...)`, or common CSS names
such as `white`, `black`, and `gray`; the exporter normalizes them to 6-digit
OOXML RGB. Bar and column series also disable PowerPoint's negative-value
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
editable-first contract. HLC, volume, noncanonical structure, and style XML
outside the safe parsing boundary stay fallback-only.

**PPTX chart-import boundary**: The importer recognizes conservative classic
single-plot charts plus the verified scatter/bubble XY-axis, column/line/area
combo, area date-axis, and canonical OHLC stock subsets above. ChartEx output
can be authored from marker metadata, but ChartEx **import** is still
unsupported. Full `AxisSpec`, radar import, arbitrary stock variants, and axis,
combo, or date-axis semantics outside the closed fields above remain
fallback-only; this does not reduce the existing SVG-marker-to-native writer
support.

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

**Forbidden — native marker transforms**: Do not rotate, skew, or matrix-transform native table/chart marker groups. Translate / scale is accepted; complex transforms fail export because PowerPoint native table/chart frames do not preserve arbitrary SVG transforms.

### Baseline Layout Family Extraction

Native `baseline` export assigns layout families after every SVG page has been
converted. This package-only pass does not change SVG authoring or live preview.

| Root `data-pptx-page-role` | Output layout |
|---|---|
| `cover` | `Cover` |
| `toc` | `Agenda` |
| `section` | `Section` |
| `ending` | `Closing` |
| `content` | `Content` |

Marker-free legacy SVGs retain conservative filename-token fallback: explicit
cover / agenda / section / closing tokens select those families, and every
other page becomes `Content`. When a valid root marker exists, it is
authoritative even if the filename suggests another family.

Keep an existing `Cover` assignment when the Master chrome safety pass already
used it to hide promoted Master shapes from a minority page.

**Hard rule — no visual inference**: Keep every actual title, body, picture,
chart, table, and page-specific shape on the Slide. Baseline layouts do not
infer placeholders or promote visually similar content.

**Background rule**: Move a Slide `p:bg` to its family Layout only when every
slide in that family carries exactly the same explicit background. Otherwise,
keep each background on its Slide. Preserve whether each family shows or hides
the parent Master shape tree.

**Layout chrome rule**: After family assignment, move only the identical
leading prefix of explicitly marked chrome (`logo`, `footer`, `header`,
`watermark`, `chrome`) carried by every family member. Legacy id tokens are
consulted only when `data-pptx-role` is absent. Generated OOXML and
image relationships must match exactly, no animation may target the shapes,
and moving them behind Slide content must preserve z-order. Keep page numbers
and every non-identical object Slide-local.

### Explicit PPTX Master / Layout / Placeholder Metadata (Template Export)

**Trigger**: Deck/layout template routes set `spec_lock.md`
`pptx_structure.mode` to `template`; direct diagnostics may pass
`--pptx-structure template`. Both strict and adaptive template adherence use
this mode. Without either trigger, metadata stays visually dormant.

**Project lock**: In the standard project pipeline, template mode requires one
`pptx_layouts` row per page using
`P<NN>: <layout_key> | <PowerPoint layout name>`. The SVG root values MUST
match that row. Strict uses the selected template key/name. Adaptive may create
a new key/name while repeating the same Master contract. Reuse one layout key
only when pages share the same static Layout layer and placeholder contract;
different content is not a reason to create a new layout. Direct diagnostic
exports may select the mode with the CLI flag instead of a locked
`pptx_structure.mode` row, but still require `spec_lock.md` typography
`title` / `body` rows.

**Master text-style contract**: Template mode requires numeric `title` and
`body` rows under `spec_lock.md` `typography`. Export maps the locked `title`
size to every `a:defRPr` in Master `p:titleStyle`, and maps the locked `body`
size to every level in both `p:bodyStyle` and `p:otherStyle`.

| Master style | Locked source | XML field changed |
|---|---|---|
| `p:titleStyle` | `typography.title` | Every `a:defRPr@sz` |
| `p:bodyStyle` | `typography.body` | Every `a:defRPr@sz` |
| `p:otherStyle` | `typography.body` | Every `a:defRPr@sz` |

**Hard rule — narrow scope**: This Master update changes only Master
`p:txStyles//a:defRPr@sz`. It does not rewrite direct run sizes on generated
slides, so the initial slide rendering remains controlled by the authored SVG.
Missing `title` or `body` rows fail template export. `baseline`, `preserve`,
and `flat` modes do not apply this Master text-style update.

**Layout level-one text-default contract**: For every text-bearing placeholder
whose first prototype run has a direct `a:rPr@sz`, template export copies that
size to the generated Layout prompt run and
`p:txBody/a:lstStyle/a:lvl1pPr/a:defRPr@sz`. It does not rewrite Slide direct
runs or Layout levels 2–9. This preserves the layout-specific size when
level-one placeholder text is inserted or reset; placeholders without a direct
prototype size remain unchanged.

| Metadata | Placement | Behavior |
|---|---|---|
| `data-pptx-layout="content"` | root `<svg>` | Binds the slide to one generated reusable layout key |
| `data-pptx-layout-name="Title and Content"` | root `<svg>` | Sets the PowerPoint layout-picker name; defaults from the layout key |
| `data-pptx-layer="master"` | direct visual child | Moves one repeated static object/background into the slide master |
| `data-pptx-layer="layout"` | direct visual child | Moves one repeated static object/background into the selected layout |
| `data-pptx-layer="slide"` | direct full-canvas solid `<rect>` only | Writes a one-page override as Slide `p:bg` |
| `data-pptx-placeholder="..."` | direct visual child | Keeps actual content on the slide and maps it to a generated layout placeholder |
| `data-pptx-placeholder-bounds="x y width height"` | placeholder element | Overrides the reusable placeholder frame in SVG user units |
| `data-pptx-placeholder-idx="1"` | placeholder element | Retains an imported source layout placeholder index; optional for reconstructed layouts |
| `data-pptx-editable="false"` | master/layout element or slide background | Declares intentional editing outside ordinary slide content |

**Hard rule — explicit only**: Template export never promotes visually similar
content by inference. Every SVG requires a root `data-pptx-layout`; every
master/layout/placeholder element requires a unique `id` and must be a direct
child of the root SVG.

**Layer order**: Author the SVG in PowerPoint paint order: Master background,
Layout background, optional Slide background, Master shapes, Layout shapes,
then slide-local content/placeholders. Backgrounds are a special inheritance
plane beneath every shape; this order keeps standalone SVG preview and
PowerPoint rendering aligned. The exporter rejects interleaved layers.

**Solid background ownership**: A direct full-canvas solid `<rect>` becomes a
real `p:bg`, not a selectable shape. Mark it `data-pptx-layer="master"` for the
deck-wide default, `data-pptx-layer="layout"` for a page-type override, or
`data-pptx-layer="slide"` for a one-slide override. An unmarked direct
full-canvas solid rect in the background plane is also treated as Slide scope. A
Layout background overrides the Master background; a Slide background
overrides both. Use the Master for a globally stable color and the Layout for
cover/section/content variants under the same design language. Gradients,
images, textures, transformed rects, and visible-stroke rects are not promoted
by this solid-background rule.

| Placeholder value | SVG element | PowerPoint placeholder |
|---|---|---|
| `title`, `subtitle`, `body` | direct `<text>` | `title`, `subTitle`, `body` |
| `date`, `footer`, `slide-number` | direct `<text>` | `dt`, `ftr`, `sldNum` |
| `picture` | direct `<image>` or imported crop `<svg>` | `pic` |
| `chart`, `table` | direct matching `data-pptx-native` marker group | `chart`, `tbl` |
| `object` | one direct text, image, or basic SVG shape | `obj` |
| `media` | direct `<image>` or imported crop `<svg>` | `media` |

`title` is normally type-matched without an index in reconstructed layouts; if
an imported source title explicitly has one, preserve that exact index. Every
indexed placeholder on one layout uses a unique OOXML UInt32 index. Template
export writes the semantic type on both the Layout and Slide placeholder
(except `obj`, whose OOXML default is already
`obj`) so PowerPoint and `python-pptx` retain the same identity. Date, footer,
and slide-number placeholders enable their matching Layout `p:hf` flags; a
date placeholder also gets a `datetimeFigureOut` field in the reusable Layout
definition. The current Slide keeps its authored date content.

Because an omitted `p:ph@idx` has the effective value `0`, an omitted-index
title reserves `0`; no other placeholder on that Layout may use the same
effective index.

**Placeholder prototype**: The first slide using a layout key supplies that
layout's placeholder formatting. `data-pptx-placeholder-bounds` supplies the
reusable frame; when omitted, the exporter uses the prototype object's native
DrawingML bounds. Repeat the same placeholder ids/types on every slide using
that layout. Actual slide content and local geometry may differ.

**Final-package read-back gate**: After writing the temporary template-mode
PPTX and before publishing it, export reopens the package and verifies that
each Slide targets exactly one Layout, one layout key always resolves to the
same part, different keys do not collapse onto one part, and every Layout is
registered through its Master and the Presentation. It also verifies the
Layout picker name/content type, placeholder type and effective index,
matching `p:hf` flags, prototype-derived or explicitly overridden frame,
direct prompt size, and level-one default size. Later slides may keep different
slide-local geometry; only the reusable Layout frame is checked against the
explicit/prototype contract. Any mismatch fails export without replacing the
requested output.
This gate applies only to `template`; `baseline`, `preserve`, and `flat` retain
their existing behavior.

**Static structure consistency**: Repeat the same master element ids on every
slide and the same layout element ids on every slide sharing a layout. Their
generated OOXML must be identical within the affected master/layout group.
Static structure may carry shapes, text, or images; non-image/external
relationships are rejected. A full-canvas first rect/group may be marked as a
master or layout background.

**Native object placeholders**: `chart` / `table` placeholders require
`--native-objects`; fallback groups contain several shapes and cannot map to one
PowerPoint placeholder. `object` is the generic PowerPoint content slot and
must still resolve to one top-level DrawingML object. `media` currently binds
an authored image/crop to a native `media` placeholder; it does not synthesize
video or audio media from a decorative SVG group.

### Legacy Preserved Source Master / Layout Contract

**Trigger**: An existing project already ships `native_structure.json` and `source_template.pptx`, has strict template adherence, and sets `pptx_structure.mode: preserve`. Current `create-template` output does not emit this pair; retain this contract only for backward compatibility.

| Artifact | Authority |
|---|---|
| `source_template.pptx` | Original master/layout/theme/package parts |
| `native_structure.json` | Stable layout keys, picker names, parent masters, placeholder types/indices, source SHA-256 |
| `pptx_layouts` | Per-generated-page source layout selection |
| SVG metadata | Standalone preview layers and slide-content placeholder binding |

**Hard rule — source package wins**: Mark source master/layout visuals as direct `data-pptx-layer="master|layout"` preview children. Preserve export removes those generated copies and renders the original source parts. Unmarked content stays slide-local.

**Placeholder identity**: Keep actual content on the slide. Copy the source placeholder index into `data-pptx-placeholder-idx` when present; the exporter restores the source placeholder type/idx pair. Imported `subTitle`, `obj`, `media`, and `dt` placeholders retain distinct `subtitle`, `object`, `media`, and `date` semantic roles instead of collapsing into body/other. Multiple placeholders with the same semantic role require explicit indices.

**Multi-master boundary**: Preserve every source master already present in the package. Do not synthesize a new master merely for cover/section differences; rebuilt templates continue to prefer one master plus semantic layouts.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1280 720"
     data-pptx-layout="content"
     data-pptx-layout-name="Title and Content">
  <rect id="master-bg" data-pptx-layer="master"
        data-pptx-editable="false"
        width="1280" height="720" fill="#F8FAFC"/>
  <rect id="content-bg" data-pptx-layer="layout"
        data-pptx-editable="false"
        width="1280" height="720" fill="#FFFFFF"/>
  <g id="content-rule" data-pptx-layer="layout"
     data-pptx-editable="false">
    <line x1="48" y1="96" x2="1232" y2="96"
          stroke="#CBD5E1" stroke-width="2"/>
  </g>
  <text id="page-title" data-pptx-placeholder="title"
        data-pptx-placeholder-bounds="80 112 1120 72"
        x="80" y="158" font-size="40">Actual page title</text>
  <image id="hero-image" data-pptx-placeholder="picture"
         data-pptx-placeholder-bounds="680 210 480 320"
         x="680" y="210" width="480" height="320"
         href="../images/hero.png"/>
</svg>
```

---

## 8. Scope Boundary

Project structure, commands, quality-gate order, and export products are owned
by [`SKILL.md`](../SKILL.md). They are intentionally outside this SVG
authoring policy.
