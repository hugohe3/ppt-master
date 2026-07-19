> See [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation.

# SVG Effects and Geometry Specification

Conditional reference for advanced paint, effects, transforms, freeform/radial geometry, and constructed visual styles. Load only when the page uses one of these capabilities.

**Cross-reference map**: unqualified §1, §2, and §4 references point to [`shared-standards-core.md`](./shared-standards-core.md); §6 references are local to this file.

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
| Shadow/glow alpha | Opaque `flood-color` + `flood-opacity="0..1"` | Effect alpha; `Native-stable` within §6.4 |
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
PPTX import normalizes compatible gradients and records any property-level
degradation without aborting the deck; `--strict` keeps the closed parser
contract. See
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).
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

Preset patterns are a separate PPT interface in [`native-data-interface.md`](./native-data-interface.md).

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
PPTX import preserves one registered shape/connector shadow or glow and records
unsupported object/run effects as import diagnostics instead of exposing a new
authoring surface. See
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
`data-pptx-carrier`), and the importer metadata
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

Command identity, relative coordinates, shorthand, arc parameters, and original
handles are not retained. Geometry needs non-zero bounds. Use a closed cubic
path for organic silhouettes, polygon/closed path for ribbons/facets, open path
for curved connectors, multi-`M` path for exact linework, and a [`shared-standards-core.md`](./shared-standards-core.md) §1.2 path clip
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
| Halftone | Sparse calculated circles | `Native-stable`; bake dense screens / use suitable [`native-data-interface.md`](./native-data-interface.md) preset |
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
| Exact custom tile | Unannotated `<pattern>` / `patternTransform` | `Bake-required` | Multi-subpath geometry, suitable [`native-data-interface.md`](./native-data-interface.md) preset, or bake |
| Sheared object | Skew/shear matrix | `Bake-required` | Pre-transform geometry path; bake text/image |

**Hard rule — blur semantics**: within §6.4, zero-offset `feGaussianBlur` means
glow; it does not blur the object or backdrop. Use a low-alpha raster for dense
grain and explicit circles/paths only for sparse editable marks.

Unsupported source effects remain visible where possible and retain their
import diagnostics. Resolve those diagnostics before release export; see
[`conversion.md`](../scripts/docs/conversion.md#import-compatibility-and-recovery-boundary).

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
| Data/freeform | Series depth → area first + line above; organic card → closed cubic; shaped image → [`shared-standards-core.md`](./shared-standards-core.md) §1.2 path clip | §6.11 / §6.9 |
| Radial | Donut/gauge → explicit arcs; sunburst → sector per node; position-insensitive ring → shorthand | §6.10; shorthand has 90° preview/native offset |
| Arrow | Manual diagonal arrowhead → calculated triangle; ordinary connector → marker | §6.10 / §1.1 |
| Unsupported | Dense grain, complex composite, or skew → explicit alternative or baked asset | §6.12; foreground text/data stay editable SVG |

---
