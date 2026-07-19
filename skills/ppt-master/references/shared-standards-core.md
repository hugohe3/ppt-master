# Shared SVG Core Standards

Mandatory reference for every route that authors or regenerates slide visuals through SVG. It owns XML validity, the closed generated-authoring surface, basic converter compatibility, page closure, semantic grouping, and shared fidelity vocabulary.

**Conditional module routing**:

| Trigger | Load |
|---|---|
| Noncanonical/alpha paint, advanced line or text treatment, gradient/filter/effect, transform, freeform/radial geometry, or constructed style | [`svg-effects.md`](./svg-effects.md) |
| A page will use a preset pattern fill or evaluate native chart/table replacement | [`native-data-interface.md`](./native-data-interface.md) before deciding eligibility or emitting metadata |
| `pptx_structure.mode: structured` | [`pptx-structure-interface.md`](./pptx-structure-interface.md) |

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
listed in this file or a triggered module in the routing table above. `svg_quality_checker.py` rejects unknown inline visual
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

**Default — ordinary generated paint**: the table allows inline placement of
those property names. New solid paint uses uppercase six-digit `#RRGGBB`;
`fill` / `stroke` may instead use lowercase `none` or an exact local
`url(#id)`. Load [`svg-effects.md`](./svg-effects.md) before authoring any
alternative compatible color spelling, alpha/opacity channel, dash/cap/join,
gradient, filter, or constructed paint/effect. Existing compatible alternatives
remain valid input and receive recommendation warnings rather than errors.

Conditional properties with a required XML form stay out of inline style:
write `filter="url(#id)"`, `clip-path="url(#id)"`, and
`marker-start` / `marker-end` as direct attributes. `!important`, unknown CSS
properties, blend modes, isolation, and backdrop filters fail quality check.

The table registers property names, not arbitrary CSS values. Ordinary generated
text uses a non-empty `font-family`, a finite positive unitless-px `font-size`,
`font-weight` of `normal` / `bold` / an integer hundred from `100` through
`900`, `font-style` of `normal` / `italic`, and `text-anchor` of `start` /
`middle` / `end`. Inheritable text declarations belong only on `<svg>`, `<g>`,
`<text>`, or `<tspan>`; `text-anchor` is invalid on `<tspan>`. Load
[`svg-effects.md`](./svg-effects.md) §6.7 before authoring tracking,
underline/strike, text outline/alpha, gradient text, or text filter effects.
Unknown or unmapped declarations fail Checker preflight and native export.

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
> opacity are conditional** — see §2 and [`svg-effects.md`](./svg-effects.md).
>
> **PPT preset patterns and native chart/table/template metadata are
> conditional** — see [`native-data-interface.md`](./native-data-interface.md) and [`pptx-structure-interface.md`](./pptx-structure-interface.md).

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
dropped.

PPTX import compatibility, tolerant recovery, strict-mode rejection, and
diagnostic behavior are indexed in
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).

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

**Hard rule — compact native metadata transport**: Type A mirror
materialization moves `p:txBody`, relationship-free `p:style`, and
`a:custGeom` payloads into the content-addressed
`templates/native_payloads.json.gz` store. It also deduplicates repeated native
restoration fields—object identity, frame, preset/custom-geometry guards,
preview/text hashes, connector endpoints, payload references, and adjustment
formulas—into short `data-pptx-native-ref` records in the same store. Checker,
template-structure validation, and export validate and hydrate both layers in
memory. Keep Master/Layout, placeholder, layer, editable-object, diagnostic,
and editable chart/table metadata inline. Legacy inline Base64 and v1
payload-only stores remain readable.

One effect reason remains its existing plain token. If one imported object has
multiple independent unsupported reasons, both marker copies store the same
deduplicated, lexicographically sorted compact JSON string array in
`data-pptx-effect-reason`; adding a later reason must not overwrite an earlier
one. This array is still diagnostic metadata, not an authoring surface.

**Import/authoring representation split**:

| Representation | Contract |
|---|---|
| Lossless import SVG | Keep complete native payload, hidden carriers, and preview evidence in the temporary analysis workspace. It is immutable native-payload backing, not the editable template source. |
| Authoring IR bundle | Keep editable SVGs plus model-readable `authoring_summary.json` and tool-only `authoring_manifest.json`. Exclude opaque payload and duplicate hidden carriers from model context while retaining visible shape intent and a stable document-local `data-pptx-source-ref` on each imported logical object. Compact model-facing imported frames and safe transform page coordinates to at most two decimals before hashing the IR. The summary owns the compact current-file index; the manifest owns source paths and initial hashes and never enters model context. |
| `standard` / `fidelity` output | Use the compact authored-preset contract (§1.5) for newly authored stock shapes; do not transplant opaque import payload or source topology. |
| `mirror` output | Materialize from the edited authoring IR. Rehydrate supported imported metadata only when a Slide-local/slot object's source ref and initial authoring hash still match; otherwise keep the current SVG fallback. Expand fixed Master/Layout group wrappers into direct semantic atoms while preserving source ownership, paint order, and visible appearance. |

**Hard rule — model-facing page-coordinate precision**:

| Surface | Precision contract |
|---|---|
| Imported `data-pptx-frame` in authoring IR | At most two decimals. An unchanged mirror source ref recovers the exact lossless frame before tool-side native-record externalization. |
| `data-pptx-bounds` in generated and final template SVG | At most two decimals. |
| `translate(...)`, `rotate(... cx cy)`, and `matrix(... e f)` | Translation values and rotation centers use at most two decimals. Keep the rotation angle and matrix `a b c d` coefficients unchanged. |
| Protected values | Do not apply this compaction to path/points geometry, normalized crop or nested `viewBox` ratios, gradient offsets, opacity, scale arguments, canonical authored-preset frames, or lossless/tool-side native frames. |

**Hard rule — authoring source refs**: `data-pptx-source-ref` is reserved for
the create-template authoring IR. Its value is unique within one authoring SVG,
not across the workspace, and must be resolved through that document's
`authoring_manifest.json` record by the owning tool. Models MUST NOT read that
machine manifest. Moving a referenced subtree into
`icons/imported/` for readability must preserve the attribute and record it in
the vector inventory; re-inlining re-establishes the same mapping. Final materialized
template SVGs and normal project `svg_output/` must not contain this attribute.

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
an authored template. Keep the full lossless import SVG separately as immutable
audit/fallback backing. Mirror may reuse only metadata already supported by the
converter on source-ref/hash-matching Slide-local/slot objects; unsupported or
edited objects use the current SVG fallback. `data-pptx-replace-with` remains reserved for the
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
  not covered by atomic `p:sp + p:txBody` rehydration.
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
`data-pptx-layer`, `data-pptx-editable`, `data-pptx-carrier`, or
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

Use the already locked canvas id and exact viewBox. [`canvas-formats.md`](canvas-formats.md) owns format selection; this core owns only SVG conformance on that canvas.

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

Semantic markers are minimal compiler hints. Flat pages declare one root `data-pptx-page-role` and omit Master/Layout/layer/placeholder markers. Structured pages carry their final root identity, layer atoms, slots, and native-object metadata from authoring start and omit `data-pptx-page-role`. Use `data-pptx-role` with a stable `id` only when no specialized marker expresses page-frame behavior. Keep ordinary visible content in SVG attributes/text; [`semantic-svg.md`](semantic-svg.md) owns the vocabulary.

- **Canvas authority**: New authoring writes `viewBox="0 0 W H"` with positive
  integer pixels from the lock. Numerically equivalent spellings and positive
  fractional imported dimensions remain compatible; export quantizes once at
  `1 SVG px = 9,525 EMU`. Invalid/non-finite values, non-zero origin,
  non-positive size, or unsupported PowerPoint dimensions are errors. All pages
  and Layout prototypes in one build share the numeric canvas and match
  `spec_lock.md canvas.viewBox`; standalone templates match `design_spec.md
  canvas_viewbox`. Optional root `width`/`height` do not override `viewBox`.
  Root `<svg>` transform is forbidden; nested crop and `<symbol viewBox>` keep
  their own contracts.
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
| Native PowerPoint background promotion | Outside structured mode, the first eligible visual layer may be a direct full-canvas `<rect>` or one inside a simple single-child group. Its fill must have a registered native mapping (solid, linear/radial gradient, or preset pattern), and it must have no transform, filter, clip, rounding, or visible stroke. Export writes the fill as Slide `p:bg`; image elements remain pictures. Structured routes use the narrower explicit solid-background ownership contract in [`pptx-structure-interface.md`](./pptx-structure-interface.md). |
| Free-design / brand-only PowerPoint structure | Use `pptx_structure.mode: flat`. Keep every represented object Slide-local; export materializes one clean project-owned Master plus one Blank Layout from the current lock, removes stock content placeholders/Layout inventory, and retains only the standard date/footer/slide-number capability hooks. Do not author Master/Layout identities, layers, or placeholder slots. |
| Reusable template-based PowerPoint Layout | Select one complete authoring SVG per page in `page_layouts`, declare each unique Master/Layout definition once, and assign pages through `page_pptx_layouts`. Strict preserves the prototype contract; adaptive retains its Master and may define and assign a new explicit Layout key during page authoring. Non-mirror skin follows `spec_lock`. |

**Hard rule — supported shape conversion**: Every PPT editability claim in this specification refers to the project converter reading `svg_output/` and emitting native DrawingML. `svg_final/` is a self-contained visual preview that may be inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is unsupported; do not narrow the authoring contract to its undocumented SVG subset.

### 4.3 Element Grouping (Mandatory)

**Hard rule — root groups protect body-text layout**: Every visible direct root `<g>` declares positive root-coordinate `data-pptx-bounds="x y width height"`. Keep it when frame/native coordinates size one PowerPoint object; placeholder bounds also supply the slot frame. Checker validates this subcanvas against the root `viewBox`, then recursively validates only estimable `<text>` descendants against it. Nested groups and all shapes, images, paths, `<use>` instances, effects, and object frames are not content-boundary inputs. Per side, Checker ignores text/bounds overflow through `1px`, warns through `5%` of the containing boundary dimension, and fails above `5%`. Bounds do not clip or reflow.

Wrap each logical Slide-local body unit in a descriptive top-level `<g id>`; aim for **3–8 ordinary groups**, each becoming one animation step. Nested implementation groups may remain anonymous and need no bounds; any nested bounds are ignored. Flat pages use ordinary groups; structured slots already qualify, while titles, direct atomic Master/Layout elements, and canvas-level decoration may remain root primitives.

**Structural atoms and slots are excluded automatically.** `data-pptx-layer` and `data-pptx-placeholder` semantics are read first; otherwise explicit `data-pptx-role` values (`background`, `decoration`, `header`, `footer`, `chrome`, `watermark`, `page-number`, `logo`) mark Slide-local static framing (§4.1, [`semantic-svg.md`](semantic-svg.md)). A normal slot group has exactly one direct compatible carrier; several drawing atoms require the explicit composite `object` proxy fallback. Native chart/table carrier groups retain their specialized [`native-data-interface.md`](./native-data-interface.md) contract.

**What to group** (one `<g id>` per unit):

| Grouping unit | Contains |
|---|---|
| Card / panel | Background rect + optional shadow (only if it floats over a photo/colored panel, [`svg-effects.md`](./svg-effects.md) §6.4) + icon + title + body text |
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
<g id="card-benefits-1" data-pptx-bounds="60 115 565 260">
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
[`generate-pptx.md`](../workflows/generate-pptx.md) Step 7. This file defines SVG authoring boundaries
and intentionally does not mirror commands, flags, or output behavior.

---


## 8. Scope Boundary

Generate project structure, commands, quality-gate order, and export products
are owned by [`generate-pptx.md`](../workflows/generate-pptx.md). They are
intentionally outside this SVG authoring policy.
