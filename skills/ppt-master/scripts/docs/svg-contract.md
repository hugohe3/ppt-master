# SVG Compatibility Contract Reference

The complete closed grammar that `svg_quality_checker.py` and the
`svg_to_pptx.py` exporter preflight enforce on generated SVG. The always-read
authoring rules — the canonical form the model writes — live in
[`shared-standards-core.md`](../../references/shared-standards-core.md) and
[`svg-effects.md`](../../references/svg-effects.md); this reference holds the
mapping tables, accepted-but-warned spellings, rejection boundaries, and
import-side behavior that those files no longer repeat. Enforcement is shared:
the checker imports the same validators as the exporter
(`svg_to_pptx/drawingml/utils.py`, `converter.py`, `text_properties.py`), so a
failing check reports the same boundary that export would reject.

Section numbers below mirror the owning section of
`shared-standards-core.md` (`§1.x`, `§2.x`) so cross-references resolve in
either direction.

---

## §1 Inline properties and text grammar

**Registered inline `style` properties** (names only; values follow the
element contract):

| Property family | Allowed inline `style` properties |
|---|---|
| Paint and line | `fill`, `stroke`, `stroke-width`, `stroke-dasharray`, `stroke-linecap`, `stroke-linejoin`, `fill-opacity`, `stroke-opacity`, `vector-effect` |
| Text | `font-family`, `font-size`, `font-weight`, `font-style`, `text-anchor`, `letter-spacing`, `text-decoration` |
| Alpha and definition paint | `opacity`, `stop-color`, `stop-opacity`, `flood-color`, `flood-opacity` |
| Literal geometry | The element-specific properties in §2.1 |
| Preview-only | `shape-rendering`; it does not change native geometry |

Conditional properties with a required XML form stay out of inline style:
`filter="url(#id)"`, `clip-path="url(#id)"`, `marker-start` / `marker-end`,
and `baseline-shift="super|sub"` on `<tspan>` are direct attributes.
`!important`, unknown CSS properties, blend modes, isolation, and backdrop
filters fail quality check.

**Text value grammar**: ordinary generated text uses a non-empty
`font-family`, a finite positive unitless-px `font-size`, `font-weight` of
`normal` / `bold` / an integer hundred from `100` through `900`, `font-style`
of `normal` / `italic`, and `text-anchor` of `start` / `middle` / `end`.
Inheritable text declarations belong only on `<svg>`, `<g>`, `<text>`, or
`<tspan>`; `text-anchor` is invalid on `<tspan>`. Unknown or unmapped
declarations fail checker preflight and native export. Tracking,
underline/strike, text outline/alpha, gradient text, and text filter effects
follow `svg-effects.md` §6.7.

**Compact inherited authoring**: `--canonical-authoring` reports drift from
the compact form (common typography on `<svg>`, shared paint on the nearest
meaningful `<g>`, explicit child overrides) as an advisory warning;
`compact_svg_styles.py --inplace` applies the same normalization on request to
authored project pages, never to structured template rosters.

DrawingML has no arbitrary per-pixel alpha-compositing path. A registered
single-image text picture/texture fill follows `svg-effects.md` §6.3;
arbitrary text-knockout composites, multi-layer image text, and arbitrary
alpha composites remain bake-required before SVG export.

---

## §1.1 Line-end markers

`marker-start` and `marker-end` are supported on `<line>` and `<path>` only
when the referenced marker fits this native-arrow contract:

| Concern | Required form |
|---|---|
| Reference | Exact local `url(#id)` to a `<marker>` in `<defs>` |
| Orientation | `orient="auto"` or `orient="auto-start-reverse"`; the latter reverses `marker-start` while behaving like `auto` at `marker-end` |
| Shape | One direct shape representing a DrawingML `triangle`, `stealth`, `arrow`, `diamond`, or `oval` line end: a 3-vertex `<polygon>` / closed path (triangle), a simple concave 4-vertex `<polygon>` / closed path (stealth), an open 3-vertex path (arrow), a simple convex 4-vertex `<polygon>` / closed path (diamond), or one `<circle>` / `<ellipse>` (oval) |
| Path grammar | One explicit `M`/`L` command per vertex. Triangle, stealth, and diamond paths end in `Z`; arrow paths remain open after the third vertex. No `H`, `V`, curves, or implicit multi-point `L` inside a marker path |
| Color parity | Triangle, stealth, diamond, and oval use a fill matching the parent line stroke. The open arrow uses `fill="none"` and a stroke matching the parent line stroke. DrawingML line ends inherit the line color |

The converter maps these five shapes to their corresponding DrawingML line-end
types. Prefer `<polygon>` for the closed triangle, stealth, and diamond forms;
the open arrow form requires `<path>`. Four-vertex shapes must be simple and
non-degenerate: convex geometry maps to diamond and concave geometry maps to
stealth. Other marker shapes have no native mapping and block export instead
of being silently dropped. Marker type is `Native-normalized`; size is
`Approximate` (`sm` / `med` / `lg`).

PPTX import compatibility, tolerant recovery, strict-mode rejection, and
diagnostic behavior are indexed in
[`conversion.md`](conversion.md#import-compatibility-and-recovery-boundary).

---

## §1.2 Image clipping

`clip-path` maps natively only on SVG `<image>` (including an exact crop
wrapper's inner image). Legacy imported crops may retain an outer-wrapper clip
as compatible input.

| Concern | Required form |
|---|---|
| SVG-namespace `<clipPath>` defined inside `<defs>` | Converter looks up one exact local id; missing, duplicate, foreign-namespace, or malformed references fail |
| Contains exactly one direct SVG-namespace supported shape child | Multiple shapes are not composited |
| Shape is one of: `<circle>`, `<ellipse>`, `<rect>` (optional rx/ry), `<path>`, `<polygon>` | These map to DrawingML geometry (preset or custom) |
| No `clip-rule` or `fill-rule`, whether direct or in inline `style` | DrawingML picture geometry has no equivalent winding-rule control |
| Used only on `<image>` or a compatible legacy imported crop wrapper | Shapes, groups, text, and generalized nested SVG targets are forbidden |

| SVG clip shape | DrawingML output |
|---|---|
| `<circle>` / `<ellipse>` | Full-frame `<a:prstGeom prst="ellipse"/>`; the child must exactly cover the image frame. A `userSpaceOnUse` circle requires a square physical frame; a normalized `objectBoundingBox` circle may fill any frame |
| `<rect>` / `<rect rx="..."/>` | A plain full-frame rect is a compatible no-op; rounded form maps to full-frame `<a:prstGeom prst="roundRect"/>` with one physical radius adjustment. The rect must exactly cover the image frame and cannot express non-uniform physical corner radii |
| `<path>` / `<polygon>` | `<a:custGeom>` with coordinates mapped into the image frame |

A contour that depends on even-odd or another explicit winding rule is outside
this mapping and must be rebuilt as one unambiguous visible contour or
pre-rendered.

---

## §1.3 Static same-document `<use>`

Static local reuse is compile-time authoring shorthand. `finalize_svg.py` and
native export replace each qualifying instance with cloned primitive content;
PPTX-to-SVG import emits the resulting primitives and does **not** reconstruct
the original `<use>` / `<symbol>` structure.

| Concern | Required form |
|---|---|
| Reference syntax | SVG 2 form `href="#id"`. Legacy `xlink:href="#id"` remains read-compatible and Live Preview normalizes it to `href`; if both attributes exist, their values MUST match |
| Referenced target | One of `<symbol>`, `<g>`, `<use>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<polygon>`, `<polyline>`, `<text>`, or `<image>`. Nested local `<use>` is recursively expanded |
| Instance position | Generated `<use x>` / `<use y>` use finite unitless values; an explicit `px` suffix is read-compatible. Omitted values default to `0` |
| Symbol viewport | A referenced `<symbol>` MUST have a finite four-number `viewBox` with positive width/height. Its `<use>` MUST have positive finite unitless `width` and `height`; an explicit `px` suffix is read-compatible |
| Aspect ratio | Default/aligned `meet` values and plain `preserveAspectRatio="none"` are supported. `slice`, `refX`, and `refY` are forbidden |
| Viewport boundary | Symbol artwork MUST stay inside its `viewBox`; expansion does not reproduce symbol overflow clipping |
| Internal references | Author exact `href="#id"` and `url(#id)` fragments. The expander also reads legacy `xlink:href="#id"` and rewrites all instance-local cloned IDs |
| Structural metadata | Neither the `<use>` instance nor its referenced subtree may carry `data-pptx-layer*`, chart/table replacement metadata (`data-pptx-replace-with`, `data-pptx-replacement-*`, `data-pptx-import-source`, or `data-pptx-fallback-*`), or `data-pptx-placeholder*`. Author those objects directly instead |
| Safety limits | A reachable reference chain may contain at most 64 instances, and one SVG may expand at most 10,000 local `<use>` instances |

**Forbidden — unsafe local references**: external/file/data URLs, missing
targets, conflicting `href` / `xlink:href`, unsupported target elements,
circular reference chains; duplicate IDs on the referenced target, the `<use>`
instance, or anywhere in the reused subtree; quoted/whitespace CSS fragment
variants such as `url('#id')`.

---

## §1.4 Imported native PowerPoint shapes

`pptx_to_svg.py` emits rendering-neutral metadata when a visible SVG object
originates from `p:sp`, `p:cxnSp`, or `p:grpSp`. This contract is for lossless
import SVGs and unchanged imported objects that remain Slide-local or inside a
slot during mirror materialization. Ordinary authored SVG does not need these
attributes, and no separate source-payload opt-in marker exists.

| Metadata | Placement | Required behavior |
|---|---|---|
| `data-pptx-object` | Logical `<g>` and native carrier | `shape`, `connector`, `group`, or `picture`; never infer the object kind from path appearance. |
| `data-pptx-shape-id` + `data-pptx-shape-scope` | Logical `<g>` and carrier | Preserve the source part-scoped identity. Export remaps duplicate Master/Layout/Slide ids into page-unique ids before rebinding connector references. |
| `data-pptx-frame="x y width height"` | Logical `<g>` and carrier | Own native `a:xfrm` position and size. Lossless import SVGs and tool-side native records use sufficient precision for exact EMU recovery; the model-facing authoring IR may use the compact page-coordinate spelling defined below. Path bounds, stroke, markers, shadows, and text glyph bounds never replace this frame. |
| `data-pptx-prst` | Preset carrier and logical `<g>` | One of the locked 187 DrawingML `ST_ShapeType` values. |
| `data-pptx-av-*` | Preset carrier and logical `<g>` | Preserve the complete validated DrawingML adjustment formula, including non-`val` formulas. |
| `data-pptx-part="geometry"` | One hidden carrier path | The single native export authority for frame, base fill/line/effect, preset/custom geometry, and object identity. |
| `data-pptx-part="geometry-preview"` / `geometry-detail` | Visible preview group/paths | Render the preset's independent path fill/stroke layers. A hash-locked preview group may mirror the carrier's one filter so a multi-path preset renders one aggregate imported effect; these elements are never emitted as duplicate PowerPoint shapes. |
| `data-pptx-preview-sha256` | Logical preset `<g>` and carrier | Detect edits to visible preset paths or paint. A stale preview fails quality check/export instead of silently reusing old native metadata. |
| `data-pptx-geometry-kind="custom"` + `data-pptx-custgeom` or `data-pptx-custgeom-ref` | Custom-geometry carrier | Preserve the validated original `a:custGeom` subtree. If the visible path hash is unchanged, export writes formulas, handles, connection sites, text rectangle, and path list exactly; edited paths compile from current SVG geometry. |
| `data-pptx-start/end-shape-id/site` | Connector logical `<g>` and carrier | Restore `a:stCxn` / `a:endCxn` after scoped shape-id allocation. A connector may retain one zero frame axis; it must not be expanded from visible stroke or marker bounds. |
| `data-pptx-shape-style` or `data-pptx-shape-style-ref` | Native carrier | Preserve a relationship-free `p:style` independently of text, including shapes with no visible text. |
| `data-pptx-effect-status="unsupported"` + `data-pptx-effect-reason` | Imported `p:sp` / `p:cxnSp` logical object and native carrier; imported `p:pic` carrier and logical object; imported `p:grpSp` logical group; imported table `p:graphicFrame` logical group | Record why an encountered source object or text-run `effectLst` / `effectDag` cannot enter the registered target-specific effect mapping without changing semantics. Checker and export stop with the recorded reason; these attributes are diagnostics, not a preserved effect payload or authoring syntax. |
| `metadata[data-pptx-part="txbody"]` with inline Base64 or `data-pptx-ref` | Logical shape `<g>` | Preserve unchanged `p:txBody`, including an empty text body. Content, whitespace, positioning, visible typography, or incompatible child-topology edits invalidate the payload. A source payload with run-level effects then blocks checker/export instead of losing those effects; an effect-free payload uses the normal SVG text fallback. |

**Compact native metadata transport**: Type A mirror materialization moves
`p:txBody`, relationship-free `p:style`, and `a:custGeom` payloads into the
content-addressed `templates/native_payloads.json.gz` store. It also
deduplicates repeated native restoration fields — object identity, frame,
preset/custom-geometry guards, preview/text hashes, connector endpoints,
payload references, and adjustment formulas — into short
`data-pptx-native-ref` records in the same store. Checker, template-structure
validation, and export validate and hydrate both layers in memory. Keep
Master/Layout, placeholder, layer, editable-object, diagnostic, and editable
chart/table metadata inline; authoritative Chart/Table JSON stays inside its
SVG marker, never in the payload store. Legacy inline Base64 and v1
payload-only stores remain readable.

One effect reason remains its existing plain token. If one imported object has
multiple independent unsupported reasons, both marker copies store the same
deduplicated, lexicographically sorted compact JSON string array in
`data-pptx-effect-reason`; adding a later reason must not overwrite an earlier
one. This array is diagnostic metadata, not an authoring surface.

**Import/authoring representation split**:

| Representation | Contract |
|---|---|
| Lossless import SVG | Immutable native payload and preview evidence in the temporary analysis workspace; never editable template source. |
| Authoring IR bundle | Editable SVG plus model-readable `authoring_summary.json` and tool-only `authoring_manifest.json`. Keep visible intent and document-local `data-pptx-source-ref`, but omit opaque/duplicate carriers. Before hashing, compact safe imported frame/transform coordinates to two decimals. Summary indexes current files; manifest owns source paths/hashes and stays outside model context. |
| `standard` / `fidelity` output | Use §1.5 compact presets; never transplant opaque payload or source topology. |
| `mirror` output | Template_Designer reviews/authors the compact parsed IR; materialization validates refs/graph and publishes that tree without restoring visible lossless subtrees. Recover only supported non-visible semantics; expand fixed Master/Layout wrappers without changing ownership or intended presentation. |

**Model-facing page-coordinate precision** (the canonical checker reports
over-precision as an advisory warning):

| Surface | Precision contract |
|---|---|
| Imported `data-pptx-frame` in authoring IR | At most two decimals; the compact frame owns visible geometry. |
| `data-pptx-bounds` in generated and final template SVG | At most two decimals. |
| `translate(...)`, `rotate(... cx cy)`, and `matrix(... e f)` | Translation/center values use at most two decimals; keep angle and matrix `a b c d` unchanged. |
| Protected values | Never compact path/points geometry, crop/nested-`viewBox` ratios, gradient offsets, opacity, scale, canonical preset frames, or lossless/tool-side frames. |

**Authoring source refs**: `data-pptx-source-ref` is create-template IR-only
and unique per document. Tools resolve it through that document's
`authoring_manifest.json`; models never read the manifest. Extract/re-inline
preserves the ref and vector inventory mapping. Final templates and
`svg_output/` contain no source refs.

**Decoration extraction**: move text-free imported vectors to
`icons/imported/` and leave an inventoried `<use data-icon="imported/...">`.
The editor expands it; unchanged assets restore source objects and edited ones
become page-local vector units.

**Imported source proxy fallback**: only unsupported, text-free, schema-free,
unmarked ornament may use an atomic
`<image data-pptx-source-proxy="native-restore">` preview under
`images/source-object-previews/`. Meaning-bearing content stays readable inline
or reports a conversion gap. Unchanged proxies restore; removing a Slide-local
proxy deletes it, while inherited proxies remain. Proxy edits fail export.
Extraction/proxies are import-time only, never free-authored `svg_output/`.

**Structural-layer boundary**: An unchanged imported logical object may keep
currently supported metadata while it remains Slide-local or inside a slot. An
imported logical `<g>` cannot be assigned to Master/Layout because those layers
require direct semantic atoms. Mechanically expand a fixed-layer source group
into direct atoms, rebuilding a preset when supported and otherwise retaining
the visible SVG fallback. A newly authored compact preset `<g>` from §1.5 is
the sole group exception: validation proves that it compiles to exactly one
native shape/connector. Do not use this normalization to change ownership or
appearance.

**Selective payload**: Keep the lossless import SVG as immutable evidence; do
not copy every metadata block into a template. Mirror publishes the compact
authored subtree and recovers only converter-supported non-visible metadata,
never ordinary visible source XML. Unsupported/edited objects use the SVG
fallback. `data-pptx-replace-with` remains reserved for optional native
Chart/Table replacement.

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
  not covered by atomic `p:sp + p:txBody` rehydration.
- Unknown future presets and explicit `unsupported` geometry status never
  downgrade silently to `rect`; native export stops with the recorded reason.

**Fidelity boundary**: native preset/custom geometry, logical frame, scoped
identity, connector topology, and relationship-free unchanged horizontal
text-body semantics on ordinary shape fills are `Native-stable`. The SVG
preview paint for gradient/pattern `darken`/`lighten` layers is
`Native-normalized`; original group child coordinates, shape-level image-fill
reconstruction, and vertical-text reconstruction are also normalized rather
than byte-identical OOXML.

---

## §1.5 Authored native PowerPoint presets — machine contract

Selection behavior lives in
[`native-shape-authoring.md`](../../references/native-shape-authoring.md);
this section owns the machine contract of the compact canonical fragment that
`preset_shape_svg.py` prints.

| Metadata / structure | Required behavior |
|---|---|
| `data-pptx-authoring="preset"` | Appears once on the logical `<g>`; distinguishes strict project authoring from legacy/imported metadata. |
| `data-pptx-object` | `shape` or `connector`; connector-family presets must use `connector`, and `connector` must use a connector-family preset. Authored connectors require `fill="none"` plus a visible stroke and export as unconnected `p:cxnSp`. |
| `data-pptx-prst`, `data-pptx-frame`, `data-pptx-av-*` | Generated together from the locked registry and written once on the logical group. The frame is the helper's exact four-part, space-separated ordinary-decimal spelling and remains authoritative even when visible path bounds differ; commas, scientific notation, leading `+`, and redundant decimal spellings are rejected. |
| Local `fill` / `stroke` plus supported paint attributes | Base paint is written once on the group; a visible stroke also carries an explicit width. Canonical page/template authoring keeps channel paint local. Compatible ancestor paint/opacity may compose under the general SVG rules and receives a recommendation warning. |
| Optional direct `filter="url(#id)"` | Shape presets only: the helper writes one exact local reference to a direct `svg-effects.md` §6.4 filter definition. It compiles once on the complete native shape; connector presets, inline style, ordinary group filters, and child-path filters remain unsupported. |
| Ordered direct `<path>` children | Browser-visible registry layers only. Each child writes just its required path-level fill/stroke override; labels and decorations stay outside the atomic group. |
| No carrier / wrapper / fingerprint | `data-pptx-part`, hidden geometry carriers, preview wrappers, and `data-pptx-preview-sha256` belong to expanded import/compatibility transport, not canonical project authoring. |

Template ownership metadata is orthogonal to preset geometry. After inserting
the complete helper output, `create-template` may add only the registered
`data-pptx-layer`, `data-pptx-editable`, `data-pptx-carrier`, or
`data-pptx-role` attribute needed by the surrounding structured contract. It
must not change preset/frame/adjustment/paint metadata, the filter reference,
or any direct path.

**Reusable-template boundary**: a project-owned canonical template may retain
one complete helper-generated atomic fragment when the stock preset is an exact
semantic match and both its paint and optional effect stay inside the authoring
boundary. The fragment is an executable exemplar and one semantic atom, not a
freely editable template primitive. It may be Slide-local, the one carrier of
an `object` slot, or a direct Master/Layout fixed atom. An adaptation may reuse
it unchanged only when preset, frame, adjustments, paint, and the optional
filter reference are unchanged; otherwise regenerate the whole fragment with
the helper. Imported, mirror, and third-party templates are never upgraded by
contour inference.

**Authoring paint/effect boundary**: v1 accepts `none` or six-digit solid HEX
fill and stroke, optional fill/stroke opacity, stroke width, line cap, line
join, and one shape-only local filter id under `svg-effects.md` §6.4. Use
ordinary SVG for gradients, patterns, or other treatments outside this narrow
contract. Registry-derived multi-path darken/lighten colors and other
contextual derivatives need no separate lock row unless they become a
recurring named role. Mirror preserves source paint under §1.4 instead.

**Validation**: quality check and export both rerender authored fragments from
`preset + frame + adjustments + group paint` and compare every visible path and
path-level paint override directly. They separately validate the optional
effect reference through `svg-effects.md` §6.4. Registry-path edits, geometry
metadata that leaves those paths stale, unknown adjustments, invalid or
unresolved filter references, out-of-range frames/transforms, zero-scale
transforms, and shear/skew fail closed. Export expands the validated compact
group only in memory and reuses the lossless native-shape conversion path.
Older authored carrier/preview fragments remain compatible as ordinary
Slide-local input and receive a non-blocking migration warning; they do not
gain the new compact group's structured-atom exception. `pptx_to_svg` expanded
output remains the lossless round-trip form and is not warned as authored
input.

**Fidelity boundary**: an unchanged authored fragment is `Native-stable` as
one `p:sp` or `p:cxnSp`. Text remains outside the atomic fragment and may
export as a grouped editable text box. Authoring v1 creates only unconnected
`p:cxnSp`; it does not accept hand-written endpoint/site metadata. An
`actionButton*` preset maps visual geometry only. Preset appearance never
invents connector attachment, action behavior, navigation targets, or
hyperlinks; link behavior is authored under
[`native-hyperlinks.md`](../../references/native-hyperlinks.md).

---

## §2.1 Literal geometry lengths and inline geometry

**Direct geometry length grammar**: generated SVG writes the following XML
geometry values and `stroke-width` as finite unitless ordinary decimals in the
page `viewBox` coordinate space. The explicit `px` suffix is read-compatible
and receives a recommendation warning. No other unit is registered for this
surface.

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

**Inline geometry in `style`**: the following properties may appear in the
same element's `style="..."`. The pipeline materializes them as XML geometry
attributes before SVG post-processing and native PPTX conversion; an inline
declaration overrides an existing same-name XML attribute.

| Element | Recognized properties |
|---|---|
| `<rect>` | `x`, `y`, `width`, `height`, `rx`, `ry` |
| `<circle>` | `cx`, `cy`, `r` |
| `<ellipse>` | `cx`, `cy`, `rx`, `ry` |
| `<image>` | `x`, `y`, `width`, `height` |
| `<svg>` | `x`, `y`, `width`, `height` |
| `<use>` | `x`, `y`, `width`, `height` |

Every non-zero inline geometry value is one finite `px` literal, such as
`120px` or `-8.5px`; exact zero may be unitless. `width`, `height`, `rx`,
`ry`, and `r` must be non-negative. Percentages, `auto`, `calc()`, `var()`,
`!important`, `inherit`, and every other unit are forbidden. Line endpoints,
text positions, path data, and polygon/polyline points remain XML attributes.

`<style>`, `class`, selector rules, external stylesheets, and imported styles
remain forbidden. This contract is only for literal declarations in an
element's own `style` attribute; PPT Master does not compute CSS cascade or
custom properties. Root canvas authority remains the `viewBox`, regardless of
root `<svg>` compatibility width/height values. The shared coordinate and
geometry implementation is
[`utils.py`](../svg_to_pptx/drawingml/utils.py).

---

## §2.2 Group opacity

DrawingML has no isolated group-alpha model. The converter accepts
`<g opacity="...">` and inline group `opacity` by multiplying group alpha into
descendants. That path is `Approximate`; nested group/child alpha multiplies,
and `--native-charts-and-tables` rejects transparent native table/chart
markers. The quality checker reports a non-blocking fidelity warning so
existing or intentionally authored input can continue without modification.
New `svg_output/` puts alpha on the affected descendant paint, text run,
picture, or supported effect instead.

---

## §4 Canvas and packaging boundaries

**Canvas authority**: `viewBox="0 0 W H"` with positive integer pixels.
Numerically equivalent spellings and positive fractional imported dimensions
remain compatible; export quantizes once at `1 SVG px = 9,525 EMU`.
Invalid/non-finite values, non-zero origin, non-positive size, or unsupported
PowerPoint dimensions are errors. Optional root `width`/`height` do not
override `viewBox`. Root `<svg>` transform is forbidden; nested crop and
`<symbol viewBox>` keep their own contracts.

**Native PowerPoint background promotion**: outside structured mode, the first
eligible visual layer may be a direct full-canvas `<rect>` or one inside a
simple single-child group. Its fill must have a registered native mapping
(solid, linear/radial gradient, or preset pattern), and it must have no
transform, filter, clip, rounding, or visible stroke. Export writes the fill as
Slide `p:bg`; image elements remain pictures. Structured routes use the
narrower explicit solid-background ownership contract in
[`pptx-structure-interface.md`](../../references/pptx-structure-interface.md).

**Flat packaging**: `pptx_structure.mode: flat` keeps represented objects
Slide-local; export emits one clean Master plus Blank Layout, removes stock
content placeholders/Layout inventory, and retains the standard
date/footer/slide-number hooks. Without a Layout/Deck owner, Quick uses the
same ownership with converter-default theme scaffolding. Reusable Layouts are
mapped through `page_layouts` / `page_pptx_layouts` in Default and inferred
from the complete structured SVG roster in Quick; ownership is never inferred
from repeated Slide-local geometry.

**Root-group bounds checks**: every visible direct root `<g>` except a compact
helper-authored preset atom declares root-coordinate
`data-pptx-bounds="x y width height"`. The checker fails ordinary root-group
overlap exceeding `1px` on both axes (structured slots, structural-role groups,
and off-canvas Morph staging groups are exempt; structured Slide-local groups
are not). It compares each subcanvas with the root `viewBox`, and estimable
descendant text — including both multiline `<tspan>` forms — with the
subcanvas using the shared per-run width estimate, inline-formula height
envelope, and DrawingML wrapping headroom; it separately compares estimable
visible text with the root `viewBox` before that headroom. Per side, overflow
through `1px` is ignored; module-boundary overflow warns through `5%` and
fails above `5%`, while any larger root-`viewBox` text overflow fails. Bounds
do not clip or reflow; unestimable visible text receives an advisory warning.
Only a wholly off-canvas direct-root Morph endpoint may set
`data-pptx-morph-staging="true"`; its own module bounds still apply, retained
Morph uses an explicit pair, and the marker never excuses partial page
overflow. Primitive fallback (a root with no top-level `<g>` at all) is capped
at 8 visible primitives.
