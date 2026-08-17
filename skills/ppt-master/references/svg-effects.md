> See [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation.

# SVG Effects and Geometry Specification

Authority for advanced paint, effects, transforms, freeform/radial geometry, and constructed visual styles. Default and Quick Generate load it before SVG authoring; other SVG-authoring routes follow their workflow trigger.

**Cross-reference map**: unqualified §1, §2, and §4 references point to [`shared-standards-core.md`](./shared-standards-core.md); §6 references are local to this file.

## 6. Advanced SVG Effects and Authoring Techniques

**Mandatory**: Default and Quick Generate read this file completely before SVG
authoring and keep its compatible techniques in active construction vocabulary.
Before finalizing each page, run the §6.1 selection procedure and Visual Job
Router. Use §6.13 when diagnosed jobs benefit from one coordinated page recipe.

**Default — situational use (may override when plain construction is stronger)**:
“Advanced” means capability depth, not an effect quota. During page authoring,
recall relevant techniques from content, hierarchy, legibility, semantics,
rhythm, and style; apply those that materially help.

### 6.1 Availability, Precedence, and Fidelity

| Decision layer | Authority |
|---|---|
| Technical validity | Required / Forbidden / Conditional contracts in this file |
| Project values | Default: `<project_path>/spec_lock.md` anchors plus retained Design Spec/page context; Quick: anchors resolved in the current context |
| Aesthetic fit | Locked or Quick-resolved `visual_style` / `visual_style_behavior` |
| Per-page choice | Content purpose, hierarchy, legibility, semantics, and rhythm |

**Mandatory — job-first effect selection**: establish the editable semantic
skeleton first, then diagnose effect jobs before treating the page as complete.
Plain construction remains valid only when that diagnostic finds no unresolved
visual job.

| Pass | Decision |
|---|---|
| Skeleton / diagnose | Establish native information, relationships, and hierarchy. Before completion, check image/text integration, plane separation, focus, state/direction, material/style, and the recurring motif; keep plain construction when none needs treatment. |
| Surface / select | Name the target, confirm its owning subsection and fidelity, then use the Router. Choose a compatible technique that fully performs the job; prefer simpler/native-stable alternatives only when communication is equal. `Approximate` requires review, not automatic rejection. |
| Integrate / stop | Align paint, contour, light, hierarchy, and z-order; combine only techniques with different jobs. Check legibility, editability, density, fidelity, and style; simplify failures, use legal alternatives, and bake only the smallest pixel-dependent layer. Keep authoritative text/data native. |

**Default — one dominant composition scaffold (may override when a second
scaffold performs an independent communication job)**: Integrate the page-scale
move and every active Structure / Image / Chart / Table branch into one dominant
system, sharing direction, contour, baseline, and z-order as applicable. Make a
branch-local system visibly subordinate when it cannot share that scaffold;
simplify any competing scaffold without a separate communication job.

#### Visual Job Router

**Reference — not a quota**: route diagnosed problems through this table. A
page may use no listed technique, one technique, or several techniques with
different jobs.

| Diagnosed visual problem | Candidate technique | Authority / stop |
|---|---|---|
| Meaningful direction, continuous value, or center focus is missing | Linear/radial gradient or channel alpha | §6.2 / §6.3; otherwise keep solid paint |
| Picture/card/overlay elevation or boundary is unclear | Object or picture/carrier shadow, restrained glow, or hairline | §6.4; equal peers stay flat; one light direction |
| Native copy and image do not integrate | Scrim, fade, wash, vignette, off-center spotlight, or faux glass | §6.5 and the Image-Treatment Implementation Map; verify contrast; no backdrop blur |
| Relationship state, direction, continuity, or boundary is unclear | Draft/optional/future → dash; direction → marker; undirected → solid; continuous flow → gradient stroke; repeated boundary → frame/contour/crop edge; exact grid → multi-subpath | §6.6 / §6.3; every line needs a job |
| Short display text needs notation, silhouette, or material/image emphasis | Removed/former → strike; eyebrow distinction → tracking; display silhouette → outline/gradient; justified material/image emphasis → native picture/texture fill; luminous metric → glow; semantic list → native bullet | §6.7 / §6.3 / §6.4; no decorative body-copy treatment |
| Tilt, repetition, or reversible asset direction helps composition | Rotate, translate/mirror, or local `<use>` | §6.8; never mirror text, logos, or directional evidence |
| Resolved style needs hand, print, pixel, facets, layers, ribbon, or line-plus-area | Matching constructed recipe | §6.11; no generic decorative freeform |
| Meaning needs an unmatched silhouette, radial hierarchy, gauge, or custom route | Freeform, explicit arc/sector, or calculated arrowhead | §6.9 / §6.10; prefer an equal stock shape/marker |
| Look depends on dense texture, source blur, per-pixel composite, reflection, or skew | Native-safe alternative or prepared/baked asset | §6.12; text/data stay editable |

#### Image-Treatment Implementation Map

**Reference — not a constraint**: when image composition names one of these
modifier or prepared-asset treatments, resolve its implementation here.
`Effect-only` keeps a visible capability here without restoring a layout ID.

| Image handles / treatment | Construction / boundary |
|---|---|
| `M2 · 01/03/04/08/09` · scrim, wash, fade, grid | Explicit solid/linear/radial layers over one picture; §6.2 / §6.3 / §6.5 |
| `M2 · 06/07` · atmospheric wash, watermark/receded field | Reduced picture alpha + optional wash; subordinate to native content; §6.2 / §6.5 |
| `M2 · 02/05` · vignette or spotlight | Radial layer with movable `fx/fy` or `cx/cy`; outer geometry `Approximate`; §6.3 / §6.5 |
| `M3 · 04` · lifted picture panel / visible overlay edge | Picture/carrier shadow, glow, or hairline; shadow one support shape for a framed/captioned panel; §6.4 |
| `M3 · 01/02/05` · frame, print frame, contour/cut edge | Registered native stroke/path; §6.6 |
| `M3 · 03; M1 · 09` · rotation, misregistration, Riso offset | Transform + explicit duplicate layers; §6.8 / §6.11 |
| `M1 · 03` + effect-only forms · paper cut, facets/folds, ribbon, staging | Ordered paths/facets + consistent paint/light; §6.11 / [`native-shape-authoring.md`](./native-shape-authoring.md) §7 |
| `M1 · 01/02/04–08` · crop, opening, subtraction, reveal | Direct clip or materialized Boolean; no `<mask>`; [`shared-standards-core.md`](./shared-standards-core.md) §1.2 / [`native-shape-authoring.md`](./native-shape-authoring.md) §6 |
| Effect-only · faux glass | Visible field + translucent panel + highlight; no blur or frosted-crop substitution; §6.5 |
| `A1 · 02–04; A3 · 02/03` · blur, duotone, blend, frost, desaturation | Prepared local bitmap/composite/derivative; registered frost is a blurred derivative; §6.12 |

**Reference — illustrative colors**: colors below demonstrate syntax only;
generated pages choose paint from the Default locked or Quick-resolved identity
anchors, visual style, content semantics, and current composition. A contextual
tint, gradient stop, shadow/glow paint, or one-off display color need not
already be a persistent identity role;
promote it only when it becomes a recurring named role. Fidelity labels are defined
in [`shared-standards-core.md`](./shared-standards-core.md). Review an `Approximate` result in native PPTX
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
| Shadow/glow alpha | Opaque `flood-color` + `flood-opacity="0..1"` | Glow is `Native-stable`; outer shadow is visually calibrated `Approximate` within §6.4 |
| Picture fade | `<image opacity="0..1">` | Picture `<a:alphaModFix>`; `Native-stable` |
| One atomic whole-object fade | Non-group element `opacity="0..1"` | Alpha compiled into its supported paint/effect channels; `Native-normalized` |
| Pattern alpha | Opaque pattern child paint + child fill/stroke opacity | Conditional; [`native-data-interface.md`](./native-data-interface.md) |
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

PPTX import is a user-input boundary, not generated authoring. Tolerant mode
retains recognized color semantics, omits only unsupported paint properties,
and records the decision in `conversion-report.json`; `--strict` keeps the
closed parser checks. See
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).
---

### 6.3 Gradients and Paint Effects

| Concern | Contract |
|---|---|
| Definition | Direct `<linearGradient>` / `<radialGradient>` child of `<defs>` with unique `id` |
| Reference | Exact local `url(#id)` |
| Stops | ≥2 direct `<stop>` children; explicit color; finite non-decreasing offset in `0..1` or `0%..100%` (ties form hard edges); optional alpha |
| Coordinates | `objectBoundingBox` only. Generated values: `0..1`; omitted linear axis = `(0,0) → (1,0)`. Only import-normalized linear projections may reach `-0.105..1.105`; radial values stay in `0..1`, and their effective focus must lie inside the circle centered at `(0.5,0.5)` with radius `0.5` |
| Forbidden | External/quoted refs, `href` inheritance, `gradientTransform`, `spreadMethod`, CSS gradients |

| Target | Contract and fidelity |
|---|---|
| `<rect>`, `<circle>`, `<ellipse>`, `<path>`, `<polygon>` fill/stroke | Linear `Native-normalized`; radial `Approximate` |
| `<line>` / `<polyline>` | Gradient stroke only; linear `Native-normalized`, radial `Approximate` |
| `<text>` / non-positional `<tspan>` | Gradient fill only; no gradient text outline |
| `<image>` | No gradient paint; use §6.5 overlays |

Linear export preserves stops/alpha and reduces direction to an angle;
coincident endpoints are invalid. Radial export preserves the effective focus
(`fx/fy`, otherwise `cx/cy`) as a point-focused circle; its outer center and
radius normalize to `0.5`, so distinct outer `cx/cy` and `r` are dropped. A
focus outside that canonical circle is invalid because SVG renderers clamp it
to the circumference while DrawingML retains the rectangle coordinates;
reverse import centers such a source focus and records a diagnostic.
Gradient strokes stay editable;
reverse import may keep the first stop only. Stop alpha multiplies element opacity.
PPTX import normalizes gradients and reports degradation;
`--strict` keeps the closed parser contract. See
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).
Checker/exporter preflight share this validation.
Gradient-stop colors are contextual paint values. Keep them coherent with the
deck anchors and page intent; they are not required to duplicate existing
Default `spec_lock.colors` literals or Quick-resolved anchors.

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

**Native text picture/texture fill**:

| Concern | Contract |
|---|---|
| Target | Direct `fill="url(#id)"` on `<text>` or a non-positional `<tspan>`; the text remains editable |
| Definition | Direct `<pattern>` child of `<defs>` with unique `id` and exact `data-pptx-text-image-fill="stretch"` or `"tile"` |
| Image | Exactly one direct SVG-namespace `<image>` child; project-local or data-URI source; explicit positive `width` / `height` |
| Native result | `stretch` → run-level `a:blipFill/a:stretch`; `tile` → run-level `a:blipFill/a:tile` |
| Alpha | Text `fill-opacity` multiplies the native picture-fill alpha |
| Forbidden | Preset-pattern attributes; `patternTransform`; additional pattern children; image style/alpha/clip/filter/mask/transform; use outside text; unannotated custom image patterns; multi-image/layer knockout composites |

Use this registered pattern when the design calls for a photograph, material,
or texture inside editable glyphs. The pattern is an authoring carrier for a
PowerPoint run picture fill, not a general SVG pattern promise. PowerPoint owns
the final run bounding box: `stretch` is `Native-normalized`, while `tile` may
normalize tile scale or phase and needs visual review. Forward SVG→PPTX export
is native; PPTX→SVG does not reconstruct run-level picture fills yet.

```xml
<defs>
  <pattern id="titleTexture" data-pptx-text-image-fill="stretch"
           patternUnits="objectBoundingBox"
           patternContentUnits="objectBoundingBox" width="1" height="1">
    <image href="../images/cloud-texture.png"
           x="0" y="0" width="1" height="1"
           preserveAspectRatio="none"/>
  </pattern>
</defs>
<text x="96" y="220" fill="url(#titleTexture)" fill-opacity="0.85"
      font-family="Microsoft YaHei" font-size="72" font-weight="700">
  国风之美
</text>
```

Preset patterns are a separate PPT interface in [`native-data-interface.md`](./native-data-interface.md).

---

### 6.4 Shadows, Glow, and Elevation

Filters are native-effect metadata, not a general pixel-filter surface.

| Concern | Contract |
|---|---|
| Definition/reference | Direct `<defs><filter id="...">` child with unique id; direct `filter="url(#id)"` attribute, never inline style |
| Public targets | `<rect>`, `<circle>`, `<image>`, `<path>`, `<text>`; one validated compact authored shape-preset `<g>` from [`native-shape-authoring.md`](./native-shape-authoring.md) §4; an exact outer `<g filter>` whose sole visual child is one clipped `<image>` |
| Required primitive | `feDropShadow` or `feGaussianBlur` |
| Generated glow form | Zero-offset `feDropShadow` with flood paint, or the complete blur + flood + composite + merge graph below; never bare blur |
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
`<tspan>` / ordinary `<g>` / unsupported targets are forbidden; apply the
effect to supported objects or use explicit layers.
Special `<g filter>` targets are limited to the helper-authored compact shape
preset above, the exact single clipped-image form in §6.5, the hash-locked
`data-pptx-part="geometry-preview"` transport in §1.4—a direct child of an
imported preset object referencing the hidden geometry carrier's filter—and the
exact imported picture-crop carrier in §6.5, which keeps the effect outside its
viewport. The compact preset applies its filter once to the logical shape; its
direct registry paths remain unfiltered. None of these cases authorizes ordinary
group filters or creates a second PowerPoint object.
PPTX import maps one classifiable shape/connector/picture outer shadow or glow
to this contract. Unsupported effects and outer-shadow variants whose scale,
skew, alignment, or rotation semantics cannot be retained become import
diagnostics instead of a silently simplified authoring surface. See
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary)
for tolerant, strict, and release-handling behavior.
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
color; black reads as diffuse shadow. Bare `feGaussianBlur` remains compatible
input but is never generated: preview blurs the object while export emits glow.

| Elevation | Use | `dy` | `stdDeviation` | Alpha |
|---|---|---:|---:|---:|
| Floor | Backgrounds, dividers, equal peers, body containers, decorative lines/icons, single-layer pages | — | — | — |
| Resting | Card over photo/panel, secondary callout | 2–4 | 4–8 | 0.06–0.10 |
| Raised | Primary CTA, focused card, overlay | 6–10 | 10–16 | 0.12–0.20 |
| Glow | Short display text, metric, focus accent | 0 offset | 4–8 | 0.35–0.55 |

**Default — one light source per page (may override when every affected layer
uses one deliberate alternative direction)**: every `feOffset` shadow on one
slide shares the same `dx`/`dy` direction (default `dx="0"`,
`dy="4"`–`dy="8"`, light from upper front). Contradictory shadow directions
make one plane read as several incompatible surfaces. A deliberate upward
paper-layer treatment flips every affected layer together; never mix
directions on the same plane.

**Reference — not a constraint**: use no more elevation categories than the
hierarchy needs; a page may reuse one category across several related objects.
Do not lift every peer card or stack strong shadow, border, gradient, and tint
on one container. Same-family colored shadow is reserved for a focal accent.
On dark backgrounds, prefer a light hairline or restrained glow; never glow body copy.
For older/strict renderers, replace a filter with two or three offset
translucent shapes behind the object:
alpha `0.03–0.05`, increasing offset/radius, and optional same-family tint near
`0.04` (`Native-stable`).

---

### 6.5 Image Treatments, Overlays, and Glass-like Surfaces

#### Image Carrier and Crop Contracts

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
frame-fit. Match the image box to the source ratio or use `slice`. Put one §6.4
filter directly on an unclipped `<image>`. For a clipped picture, keep
`clip-path` on the `<image>` and put the filter on an exact outer `<g>` whose
sole visual child is that image. Never combine `filter` and `clip-path` on the
same `<image>`: SVG would clip the preview effect while PowerPoint would not.
The carrier may keep object-local id, role, transform, and
`data-pptx-carrier`. It may own `data-pptx-layer="master|layout"` only when
the carrier itself is the direct fixed atom. It must not own
`data-pptx-placeholder`, `data-pptx-binding`, or chart/table replacement
metadata; keep slot ownership on the outer placeholder boundary.

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

**Hard rule — nested SVG is picture-crop transport, not a general viewport**:
every non-root `<svg>` is the exact wrapper accepted by the shared crop parser:

| Part | Required form |
|---|---|
| Outer | Registered `x`, `y`, positive `width`/`height`; four ordinary-decimal unit coordinates in `viewBox`; `preserveAspectRatio="none"`; `overflow="hidden"` |
| Child | Exactly one direct empty `<image>` with one non-empty `href`/`xlink:href`, `x="0" y="0" width="1" height="1" preserveAspectRatio="none"` |
| Context | Only root SVG / ordinary visual `<g>` ancestors; outer may add `id`, supported `transform`, registered layer/carrier metadata, and `data-pptx-frame`, `data-pptx-object`, `data-pptx-shape-id`, `data-pptx-shape-name`, `data-pptx-shape-scope`; an exact imported picture carrier may hold its one §6.4 filter outside this viewport |
| Shape crop | Exact outer `data-pptx-crop="1"`; authored wrappers put the registered, locally resolving image-only clip on the inner image, using `userSpaceOnUse` geometry matching the visible `viewBox`; legacy imported outer clips remain compatible |

The inner image may add only registered `opacity` and that clip. Quantize the
`viewBox` without clamping: every signed crop fits
`-2147483648..2147483647`, with `l + r < 100000` and `t + b < 100000`.
Retain negative/outside-source crops exactly; write redundant `0 0 1 1` as a
plain `<image>`. Extra, indirect, or character content; unknown attributes;
malformed or unrepresentable crops; and general nested viewports fail. Checker
and converter share this parser.

#### Image Overlay and Material Techniques

| Overlay | Construction | Typical stops / alpha |
|---|---|---|
| Directional scrim | Linear rect, darkest beside text | `0%: 0.88; 55%: 0.30; 100%: 0` |
| Bottom title fade | Vertical rect over lower image | black `0 → 0.72` |
| Vignette/spotlight | Radial rect; place the hotspot with `fx/fy` or `cx/cy` inside the canonical focus circle; outer center/radius remain approximate | black `0 → 0.58` |
| Brand wash | Directional existing brand-color gradient | `0.80 → 0.10` |
| Grid scrim | Seamless no-stroke rect cells over one image; vary neighboring alpha narrowly and irregularly | Keep the field subordinate; a regular alternation reads as a checkerboard |
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

PPTX import treats unsupported line properties as source diagnostics: tolerant
mode retains the object and omits only the unsupported outline; `--strict`
retains the closed rejection behavior. See
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).

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

Match marker paint to the parent stroke using the shape-specific channel from
§1.1: fill for closed/oval line ends and stroke for the open arrow. Use markers
for connectors and §6.10 calculated geometry for a manual diagonal arrowhead.
When exact grid spacing matters, use one multi-subpath path rather than a
fixed-density preset pattern:

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
| `baseline-shift` | Exact direct `super` or `sub` on `<tspan>` | None | Maps to editable ordinary-text `a:rPr@baseline` at `30000` or `-25000`; it does not resize the run, is invalid as inline style or on any other element, and cannot combine with an inline formula marker |
| `letter-spacing` | Finite unitless ordinary decimal SVG px | The same ordinary decimal with `px`, `pt`, or `em`; normalize to unitless px | Maps to `a:rPr@spc`; the final value must fit DrawingML `-400000..400000`, and negative tracking must leave every generated DrawingML run with a positive estimated advance and its text frame with a positive extent; keywords, percentages, exponents, leading plus signs, trailing decimal points, non-finite values, and other units are invalid |

The registered inheritable text properties follow SVG inheritance, including
declarations on the root `<svg>`: inline `style` overrides the same element's
direct attribute, which overrides its ancestor. `baseline-shift` is the narrow
exception: declare it directly on the owning `<tspan>`; nested inline content
inherits that run shift, while surrounding text keeps its own baseline.
Relative font sizes and `em` tracking resolve against the same effective
inherited size in Checker and converter. Every declaration is validated even
when a later declaration overrides it, so hidden garbage cannot bypass
preflight.

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
  `letter-spacing`, `text-decoration`, direct `baseline-shift`, `xml:space`,
  `id`, and project `data-*` metadata. It does not accept `text-anchor`,
  `filter`, or `transform`.
- `word-spacing`, `dominant-baseline`, `alignment-baseline`,
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
| Superscript / subscript | Direct `baseline-shift="super|sub"` on `<tspan>` | Editable ordinary-text run at PowerPoint's native baseline offset; set `font-size` on the same run when a smaller glyph is intended |
| Font size | Generated default is a finite unitless SVG px value; compatible `px`, `pt`, `pc`/`pica`, `in`, `cm`, `mm`, `q`, `em`, and `rem` values receive a recommendation warning only | Converted to SVG px, then editable DrawingML point size; unsupported units/percentages error |
| Tracking | §6.7 closed `letter-spacing` grammar | `Native-normalized`; compatible units normalize to SVG px before DrawingML conversion |
| Transparency | `opacity` / `fill-opacity` on text/run | `Native-normalized` run alpha, not isolated compositing |
| Gradient fill | §6.3 gradient on text/run | Editable fill; geometry normalizes |
| Outline | Solid `stroke`, `stroke-width`, `stroke-opacity` | `Native-normalized` editable run outline; re-import does not reconstruct it |
| Shadow/glow | §6.4 filter on `<text>` only | Shape shadow / run glow; `Approximate` |
| Native bullet | Leading `· • ● ▪ ■ ◆ ◇ ◦ ‣` + non-empty content | `·`/`•` → `•`; others unchanged; color/alpha from marker run; font/size follow text |

**Hard rule — generated decorative lettering ownership**: Approved AI
decorative lettering is a prepared `<image>` asset under the image contracts,
not an advanced native-text treatment. Keep ordinary editable titles and
subtitles as normal `<text>`; this contract does not add WordArt, text warp, or
text-on-path authoring.

```xml
<text x="100" y="200" font-size="20" xml:space="preserve">Current <tspan
  fill="#999999" text-decoration="line-through">old</tspan> value</text>
<text x="100" y="240" font-size="20">CO<tspan
  baseline-shift="sub" font-size="14">2</tspan></text>
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
Model-facing translation values, rotation centers, and matrix `e/f` use at
most two decimals under §1.4; angles, scale arguments, and matrix `a/b/c/d`
retain the precision required by the transform.

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
for a horizontal pivot. During mirror materialization, imported PowerPoint
groups with an axis flip keep their geometry reflection, while each descendant
SVG text node receives the matching counter-reflection so browser previews keep
glyphs upright. The tool-side native record retains the source group flip.

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

**Reference — not a constraint**: use the fewest curve segments and control
points that preserve the intended silhouette. Set endpoints and tangent
directions first; use `S` after `C` or `T` after `Q` when reflected controls
preserve deliberate tangent continuity.

```xml
<path d="M80 300 C180 180 300 180 400 300 S620 420 720 300"
      fill="none" stroke="#2563EB" stroke-width="4" stroke-linecap="round"/>
<path d="M80 520 Q240 400 400 520 T720 520"
      fill="none" stroke="#0F766E" stroke-width="4" stroke-linecap="round"/>
```

Command identity, relative coordinates, shorthand, arc parameters, and original
handles are not retained. Geometry needs non-zero bounds. Before authoring a
freeform, apply [`native-shape-authoring.md`](./native-shape-authoring.md):
prefer editable primitives and exact Office presets, independently composed
when possible; materialize a Boolean only when one contour requires it. Use a
closed cubic path only for an organic silhouette those
cannot express, polygon/closed path for unmatched ribbons/facets, and an open
path only for a required data curve, custom route, or locked or Quick-resolved
hand-drawn / organic style. Straight relationships use `<line>`; exact stock bends/curves
use an authored native Connector preset. Multi-`M` paths remain available for
exact linework, and a [`shared-standards-core.md`](./shared-standards-core.md)
§1.2 path clip for unmatched organic pictures. Filled silhouettes end with
`Z`; open paths use `fill="none"`. Do not depend on
`fill-rule="evenodd"`; build explicit visible geometry or bake an essential
knockout.
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

### 6.11 Constructed Technique Recipes

**Hard rule — explicit construction**: these are supported-layer recipes, not
browser-filter permissions.

**Reference — not a constraint**: use them only when they match the locked or
Quick-resolved style. Their curve recipes are explicit exceptions to the
Shape-first default above; they do not authorize decorative freeforms in
another style.

| Family | Technique | Use when | Construction / boundary |
|---|---|---|---|
| Material / depth | Faux glass | Visible field must remain present behind a panel | §6.5 translucent panel + highlight; no backdrop blur; `Native-normalized` |
| Material / depth | Paper cut | Ordered layers/openings carry the material language | Organic paths + one §6.4 shadow per layer, never the group; `Approximate` |
| Hand / print | Hand-drawn mark | Annotation, underline, or highlighter gesture | Rotated translucent bar + restrained `Q/C` paths + round caps; no roughness filter; `Native-normalized` |
| Hand / print | Ink wash | Brush mass or atmosphere | Same-family translucent curves/strokes; no feather/wet edge; `Native-normalized` |
| Hand / print | Riso offset | Deliberate print misregistration | Offset duplicate, second ink, lower alpha; no blend mode; `Native-normalized` |
| Hand / print | Pixel grid | Sparse hard-cell digital accent | Integer-aligned rect grid; `shape-rendering` preview-only; `Native-stable` |
| Hand / print | Halftone | Sparse screen modulation | Calculated circles; `Native-stable`; bake dense screens or use [`native-data-interface.md`](./native-data-interface.md) |
| Form / geometry | Faceted or folded form | Isometric object, folded ribbon, dimensional numeral/band | Shared vertices, one light direction, same-hue alternating paint per [`native-shape-authoring.md`](./native-shape-authoring.md) §7.1; no 3D; `Native-normalized` |
| Form / geometry | Gradient ribbon | Continuous directional energy, not faceted depth | Cubic gradient stroke or closed gradient-filled band; no mesh gradient; `Native-normalized`, re-import may flatten color |
| Data expression | Line plus area | Magnitude context beneath an exact reading edge | Subordinate low-alpha area first, crisp line above; `Native-normalized` |

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
| Exact custom tile | Unannotated `<pattern>` / `patternTransform` | `Bake-required` | Multi-subpath geometry, suitable [`native-data-interface.md`](./native-data-interface.md) preset, or bake |
| Sheared object | Skew/shear matrix | `Bake-required` | Pre-transform geometry path; bake text/image |

**Hard rule — blur semantics**: within §6.4, zero-offset `feGaussianBlur` means
glow; it does not blur the object or backdrop. Use a low-alpha raster for dense
grain and explicit circles/paths only for sparse editable marks.

Unsupported source effects remain visible where possible and retain their
import diagnostics. Resolve those diagnostics before release export; see
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).

---

### 6.13 Page-Level Composition Recipes

**Reference — not a quota**: use the planned page skeleton; when images are
active, select it through
[`image-layout-patterns.md`](./image-layout-patterns.md). Read each recipe
back-to-front and omit every layer without a distinct job.

| Page / deck job | Back-to-front stack | Stop |
|---|---|---|
| Cover | Hero field → optional scrim/wash → purposeful opening/contour → native title, optionally paired with a prepared decorative-lettering image | Stop when copy is safe and title/field read together |
| Divider | Image band or quiet field → restrained wash → recurring geometry → number/title | Reuse deck language; add no effect family |
| Text-led explanation | Quiet field → recurring material/contour → native hierarchy → optional local emphasis | Emphasis clarifies the argument, never decorates body copy |
| Process / system | Context field → native relation lines → nodes/labels → optional state/direction focus | Every connector stays semantic; atmosphere must not obscure flow |
| Evidence / metric | Context field → local contrast → native leaders/labels/metric → optional focus/elevation | Claims stay native; atmosphere must not weaken evidence |
| Comparison | Matched planes → optional shared wash/divider → matched labels → one difference marker | Keep crop, elevation, and paint symmetric unless asymmetry is the claim |
| Closing / CTA | Receded field → echoed contour/gradient → native action → optional raised accent | Add no effect family or competing image |
| Cross-page motif | Reuse contour, gradient direction, line language, texture, or light logic; vary scale, crop, or position by page job | Preserve recognition without copying the page or adding novelty effects |

---
