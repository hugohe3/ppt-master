> See [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation.

# SVG Effects and Geometry Specification

Authority for advanced paint, effects, transforms, freeform/radial geometry, and constructed visual styles. Default and Quick Generate load it on the executor-base routing trigger — the first page whose visual job reaches beyond the everyday block — and keep it for the rest of the run; other SVG-authoring routes follow their workflow trigger. It keeps the form the model writes and the design decisions behind each technique; the complete grammar the checker and exporter enforce for §6.2–§6.10 is in [`svg-contract.md`](../scripts/docs/svg-contract.md) Part II under the same section numbers; §6.1 and §6.11–§6.13 are design guidance with no separate contract.

**Cross-reference map**: unqualified §1, §2, and §4 references point to [`shared-standards-core.md`](./shared-standards-core.md); §6 references are local to this file.

## 6. Advanced SVG Effects and Authoring Techniques

**Mandatory**: once triggered, read this file completely before that page's
first SVG line and keep its compatible techniques in active construction vocabulary.
Before finalizing each page, run the §6.1 selection procedure, with the Visual
Job Router as recall for the jobs it diagnoses. Use §6.13 when diagnosed
jobs benefit from one coordinated page recipe.

**Default — situational use (may override when plain construction is stronger)**:
“Advanced” means capability depth, not an effect quota. During page authoring,
recall relevant techniques from content, hierarchy, legibility, semantics,
rhythm, and style; apply those that materially help.

### 6.1 Availability, Precedence, and Fidelity

| Decision layer | Authority |
|---|---|
| Technical validity | Required / Forbidden / Conditional contracts in this file, over the shared core's closed authoring surface, the route's other required construction references, and any triggered module |
| Project values | Default: `<project_path>/spec_lock.md` anchors plus retained Design Spec/page context; Quick: anchors resolved in the current context |
| Aesthetic fit | Locked or Quick-resolved `visual_style` / `visual_style_behavior` |
| Per-page choice | Content purpose, hierarchy, legibility, semantics, and rhythm |

**Reference — job-first effect selection**: establish the editable semantic
skeleton first; the Visual Job Router below lists the visual jobs an effect can
serve.

| Pass | Decision |
|---|---|
| Skeleton / diagnose | Establish native information, relationships, and hierarchy. Image/text integration, plane separation, focus, state/direction, material/style, and the recurring motif are the jobs an effect can serve. |
| Surface / select | Name the target, confirm its owning subsection and fidelity, and let the Router recall candidates. Choose a compatible technique that fully performs the job; prefer simpler/native-stable alternatives only when communication is equal. `Approximate` requires review, not automatic rejection. |
| Integrate / stop | Align paint, contour, light, hierarchy, and z-order; combine only techniques with different jobs. Check legibility, editability, density, fidelity, and style; simplify failures, use legal alternatives, and bake only the smallest pixel-dependent layer. Keep authoritative text/data native. |

**Reference — page-level recipes**: §6.13 carries a back-to-front layer stack for
cover, divider, text-led explanation, process, evidence, comparison, closing, and
cross-page motif pages. Read it with this router rather than after the page is
already composed.

**Default — one dominant composition scaffold (may override when a second
scaffold performs an independent communication job)**: Integrate the page-scale
move and every active Structure / Image / Chart / Table branch into one dominant
system, sharing direction, contour, baseline, and z-order as applicable. Make a
branch-local system visibly subordinate when it cannot share that scaffold;
simplify any competing scaffold without a separate communication job.

#### Visual Job Router

**Reference — not a quota**: recall candidates for a diagnosed problem from
this table. A page may use no listed technique, one technique, or several
techniques with different jobs. The table recalls constructions rather than
bounding them: one it never names is equally valid when it satisfies every
applicable technical contract. Those contracts are the boundary; membership in
this table is not.

| Diagnosed visual problem | Candidate technique | Authority / stop |
|---|---|---|
| Meaningful direction, continuous value, or center focus is missing | Linear/radial gradient or channel alpha | §6.2 / §6.3; otherwise keep solid paint |
| Picture/card/overlay elevation or boundary is unclear | Object or picture/carrier shadow, restrained glow, or hairline | §6.4; one light direction |
| Native copy and image do not integrate | Scrim, fade, wash, vignette, off-center spotlight, or faux glass | §6.5 and the Image-Treatment Implementation Map; verify contrast; no backdrop blur |
| Relationship state, direction, continuity, or boundary is unclear | Draft/optional/future → dash; direction → marker; undirected → solid; continuous flow → gradient stroke; repeated boundary → frame/contour/crop edge; exact grid → multi-subpath | §6.6 / §6.3; every line needs a job |
| Body copy carries a load-bearing figure, contrast, or noun that does not survive a scan | Inline emphasis run — a nested `<tspan>` with its own fill or weight inside the same paragraph | §6.7; the frame stays one editable text object |
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
| `M1 · 01/02/04–08` · crop, opening, subtraction, reveal | Direct clip or materialized Boolean; no `<mask>`; §1.2 / [`native-shape-authoring.md`](./native-shape-authoring.md) §6 |
| Effect-only · faux glass | Visible field + translucent panel + highlight; no blur or frosted-crop substitution; §6.5 |
| `A1 · 02–04; A3 · 02/03` · blur, duotone, blend, frost, desaturation | Prepared local bitmap/composite/derivative; registered frost is a blurred derivative; §6.12 |

**Reference — illustrative colors**: colors below demonstrate syntax only;
generated pages choose paint from the Default locked or Quick-resolved identity
anchors, visual style, content semantics, and current composition. A contextual
tint, gradient stop, shadow/glow paint, or one-off display color need not
already be a persistent identity role; promote it only when it becomes a
recurring named role. Review an `Approximate` result in native PPTX when the
effect carries material meaning.

---

### 6.2 Color, Alpha, and Opacity

Write solid paint as uppercase `#RRGGBB`, `none`, or an exact local `url(#id)`.
Put alpha on the channel that owns it — `fill-opacity`, `stroke-opacity`,
`stop-opacity`, or `flood-opacity` as a unitless `0..1` — and use element
`opacity` only for an `<image>` or one non-group atomic object that fades all
of its channels together. Do not use element `opacity` as an alias for
`rgba()` on a fill-only object, and prefer descendant alpha over group opacity
(§2.2). Alpha multiplies down the tree: color alpha × ancestor group opacity ×
element opacity × channel opacity. Named colors, short/alpha HEX, `rgb()` /
`hsl()`, and percentages remain compatible input that the checker only
recommends normalizing.

---

### 6.3 Gradients and Paint Effects

A gradient is a direct `<linearGradient>` / `<radialGradient>` in `<defs>` with
≥2 explicit-color stops at non-decreasing `0..1` offsets, referenced by exact
`url(#id)`, in `objectBoundingBox` units — no `gradientTransform`,
`spreadMethod`, or CSS gradients. Linear exports as an angle
(`Native-normalized`); radial keeps only its focus point and normalizes the
outer circle to the object (`Approximate`), so place the hotspot with `fx/fy`
inside the object and expect the rim to differ. Text takes gradient fill only;
images take no gradient paint (use §6.5 overlays). A gradient *stroke* needs a
path with both width and height — a perfectly horizontal or vertical gradient
ribbon disappears, so author it as a closed gradient-filled band. Stop colors
are contextual paint: keep them coherent with the deck anchors and page
intent without duplicating a lock row.

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

**Native text picture/texture fill**: when the design calls for a photograph,
material, or texture inside editable glyphs, fill the `<text>` (or a
non-positional `<tspan>`) with a registered single-image `<pattern>` marked
`data-pptx-text-image-fill="stretch"` or `"tile"`. It exports as a PowerPoint
run picture fill (`stretch` `Native-normalized`; `tile` needs visual review),
not as a general SVG pattern; the text stays editable.

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

A filter is native-effect metadata, not a pixel-filter surface: one direct
`<defs><filter>` referenced as a direct `filter="url(#id)"` on a `<rect>`,
`<circle>`, `<image>`, `<path>`, `<text>`, or a helper-authored preset group,
built from `feDropShadow` or the blur + flood + composite + merge graph below
with explicit `stdDeviation`, `dx`/`dy`, and `flood-opacity`. A meaningful
offset becomes one outer shadow; zero offset — even `feDropShadow` with
`dx="0" dy="0"` — becomes one glow. Both are `Approximate`: one filter, one
DrawingML effect. Filters on `<tspan>` or ordinary `<g>` and every other
primitive are forbidden; use an existing accent color for glow, since black
reads as diffuse shadow.

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
paper-layer treatment flips every affected layer together, so one plane keeps
one light direction.

**Reference — not a constraint**: use no more elevation categories than the
hierarchy needs; a page may reuse one category across several related objects,
but two or three shadowed objects usually read cleanest — check that a fourth
earns its weight. Pick one weight tool per container — shadow, border,
gradient fill, or strong tint — never stacked; peer-grid cards, dividers,
body containers, and background panels stay on the floor.
Same-family colored shadow is reserved for a focal accent. On dark backgrounds
a light hairline or restrained glow separates surfaces; glow on body copy
reduces legibility. For older/strict renderers, replace a filter with two or
three offset translucent shapes behind the object: alpha `0.03–0.05`,
increasing offset/radius, and optional same-family tint near `0.04`
(`Native-stable`).

---

### 6.5 Image Treatments, Overlays, and Glass-like Surfaces

| Need | Authoring contract | Fidelity |
|---|---|---|
| Cover/crop | Readable raster dimensions + aligned `slice` | Native `srcRect`; `Native-stable` |
| Contain/fit | Aligned `meet` | Fitted picture frame; `Native-normalized` |
| Stretch | `preserveAspectRatio="none"` | Native stretched frame |
| Uniform fade | `<image opacity="...">` | Native picture alpha |
| Shaped picture | §1.2 image-only `clip-path` | Preset/custom picture geometry |

Every `<image>` has explicit positive `width`/`height`, one decodable
project-local or data-URI `href`, and — when not the default `xMidYMid meet` —
an aligned `preserveAspectRatio` with explicit `meet` or `slice`, or `none`
alone. A clip disables `meet` frame-fit, so match the box to the source ratio
or use `slice`; put a §6.4 filter directly on an unclipped image, and for a
clipped one on an exact outer `<g>` whose sole visual child is that image —
never both on the same `<image>`. A nested `<svg>` is only the exact
single-image crop wrapper the crop parser accepts, not a general viewport.

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

A solid stroke with width and alpha is an editable native line. Dashes map to
the five presets (`4,4` / `6,3` dash, `2,2` sysDot, `8,4` lgDash, `8,4,2,4`
lgDashDot) or to one custom `dash gap` pair; caps are `butt` / `round` /
`square`, joins `miter` / `round` / `bevel`, `vector-effect` `none` or
`non-scaling-stroke`. Markers follow §1.1 (type native, size approximate); a
gradient stroke follows §6.3.

**Default — relationship-fit dash rhythm (may override when style calls for
another rhythm)**: after §6.1 selects dash, preserve direction markers and
branch-owned placeholder patterns.

| Already-dashed/dotted job (illustrative) | Dash |
|---|---|
| Separator/boundary | `4,4` |
| Subtle dotted border/generic non-image placeholder | `2,2` |
| Optional/future timeline/flow connector | `8,4` |
| Technical/dimension line | `8,4,2,4` |

**Default — contour-fit joins (may override when the resolved style calls for
another character)**: smooth polyline/organic form → `round`; technical
diagram → `bevel`; crisp rectangle/arrow → `miter`.

```xml
<rect x="60" y="60" width="400" height="240" rx="12"
  fill="none" stroke="#999999" stroke-width="2" stroke-dasharray="4,4"/>
<line x1="100" y1="420" x2="500" y2="420"
  stroke="#1A73E8" stroke-width="2" stroke-dasharray="8,4"/>
<polyline points="100,200 200,100 300,200" fill="none"
  stroke="#1A73E8" stroke-width="3" stroke-linejoin="round"/>
```

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

Generated text uses only the canonical values: `font-weight` `normal` / `bold`
/ an integer hundred, `font-style` `normal` / `italic`, `text-anchor` on
`<text>` or above, `text-decoration` `underline` / `line-through` / both,
direct `baseline-shift="super|sub"` on `<tspan>`, and unitless-px
`letter-spacing` and `font-size`. Inheritable text declarations belong only on
`<svg>`, `<g>`, `<text>`, or `<tspan>`; `xml:space` (`default` or `preserve`) on
`<text>` / `<tspan>` is the one whitespace control — it inherits through the
text tree and may be reset on a child `<tspan>`, so one frame can mix
collapsed and preserved runs. Every other `font-*` / `text-*`
property has no native mapping and is an error.

| Treatment | SVG surface | Result / boundary |
|---|---|---|
| Underline / strike / both | `text-decoration="underline"`, `line-through`, or both | `Native-stable`; both emits both run properties |
| Mixed runs | Non-positional `<tspan>` | One `Native-normalized` editable frame; §4.2 |
| Superscript / subscript | Direct `baseline-shift="super|sub"` on `<tspan>` | Editable run at PowerPoint's native baseline offset; set `font-size` on the same run when a smaller glyph is intended |
| Tracking | Unitless-px `letter-spacing` | `Native-normalized`; negative tracking must leave every run a positive advance |
| Transparency | `opacity` / `fill-opacity` on text/run | `Native-normalized` run alpha, not isolated compositing |
| Gradient fill | §6.3 gradient on text/run | Editable fill; geometry normalizes |
| Outline | Solid `stroke`, `stroke-width`, `stroke-opacity` | `Native-normalized` editable run outline; re-import does not reconstruct it |
| Shadow/glow | §6.4 filter on `<text>` only | Shape shadow / run glow; `Approximate` |
| Native bullet | Leading `· • ● ▪ ■ ◆ ◇ ◦ ‣` + non-empty content | `·`/`•` → `•`; others unchanged; color/alpha from marker run; font/size follow text |

**Inline emphasis**: bold or accent-colored `<tspan>` runs lift numerical
results, explicit contrasts, or a load-bearing noun inside prose; green/red
conventionally read as polarity.

```xml
<!-- Uniform: the two results disappear into the sentence. -->
<text x="80" y="200" font-size="20" fill="#333333">
  2024年公司营收同比增长35%达到12亿元创历史新高
</text>

<!-- Lifted: data-bearing runs carry the scan. -->
<text x="80" y="200" font-size="20" fill="#333333">
  2024年公司营收同比<tspan fill="#1A73E8" font-weight="bold">增长35%</tspan>达到<tspan fill="#1A73E8" font-weight="bold">12亿元</tspan>创历史新高
</text>
```

**Underline** conventionally marks links, key terms, or local emphasis —
decorate the linked run, not the whole sentence. **Strikethrough** marks
removed/former values; it is ordinary notation, not a style-exclusive effect.

```xml
<text x="100" y="240" font-size="18" fill="#333333">Read <a
  href="https://example.com"><tspan text-decoration="underline">the guide</tspan></a>.</text>
<text x="100" y="200" font-size="20" xml:space="preserve">Current <tspan
  fill="#999999" text-decoration="line-through">old</tspan> value</text>
<text x="100" y="240" font-size="20">CO<tspan
  baseline-shift="sub" font-size="14">2</tspan></text>
```

**Hard rule — generated decorative lettering ownership**: approved AI
decorative lettering is a prepared `<image>` asset under the image contracts,
not an advanced native-text treatment. Keep ordinary editable titles and
subtitles as normal `<text>`; this contract does not add WordArt, text warp, or
text-on-path authoring.

CJK tracking defaults near/below 2% of font size and above 5% triggers review.
Text outline is solid only. `textPath`, masks, blend modes, generated effects,
and text-image knockouts are outside editable text.

---

### 6.8 Transforms, Layering, and Static Reuse

Use only lowercase `translate`, `scale`, `rotate`, and `matrix` with finite
unitless arguments; `rotate` is clockwise and may take a pivot. Geometry,
images, and geometry-only groups accept any of them (`Native-normalized`) as
long as the cumulative matrix stays finite, non-zero, and orthogonal — no
`skewX` / `skewY` or shear, and `matrix` excludes rounded rectangles. Text, and
any group containing text, takes only a translate-only list or one rotate; set
text size/position directly. Native chart/table markers allow translate/scale
only. Mirror around a vertical pivot `cx` with
`translate(cx 0) scale(-1 1) translate(-cx 0)`, and never mirror text, logos,
or directional evidence.

Layer back-to-front: background/image → scrim/shadow → main geometry → labels /
icons → top annotation; source order is PPT z-order. Local `<use>` (§1.3) is
compile-time reuse — finalization and native export expand it into cloned
editable primitives, and PowerPoint retains no symbol/instance graph. Group
opacity remains an approximate compatibility mapping; generated SVG prefers
descendant alpha (§2.2).

---

### 6.9 Freeform Shapes and Curves

Every SVG path command, `<polygon>`, and `<polyline>` is accepted; export
normalizes to absolute `M/L` and cubic Béziers, and arcs become ≤90° cubic
segments (`Approximate`). Write `d` and `points` as finite unitless ordinary
decimals; geometry needs non-zero bounds; do not depend on
`fill-rule="evenodd"` — build explicit visible geometry, bake an essential
knockout, or on a fixed background use a background-colored overlay.

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

Before authoring a freeform, apply [`native-shape-authoring.md`](./native-shape-authoring.md):
prefer editable primitives and exact Office presets, independently composed
when possible; materialize a Boolean only when one contour requires it. Use a
closed cubic path only for an organic silhouette those cannot express,
polygon/closed path for unmatched ribbons/facets, and an open path only for a
required data curve, custom route, or locked or Quick-resolved hand-drawn /
organic style. Straight relationships use `<line>`; exact stock bends/curves
use an authored native Connector preset. Multi-`M` paths remain available for
exact linework, and a §1.2 path clip for unmatched organic pictures. Filled
silhouettes end with `Z`; open paths use `fill="none"`. A rounded `<rect>`
stays a native adjustable `roundRect` only while `rx == ry` and the radius is at
most half the short side; unequal radii become custom geometry without a
handle.

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
Verify all spans plus gaps against the planned sweep. Explicit arc sectors are
editable `Approximate` freeforms.

```xml
<!-- 75% donut: center 400,400; outer 180; inner 100; -90° → 180°. -->
<path d="M400 220 A180 180 0 1 1 220 400
         L300 400 A100 100 0 1 0 400 300 Z" fill="#2563EB"/>
```

**Gauge**: require `max > min`, `p = clamp((value-min)/(max-min),0,1)`, and
`0 < planned clockwise sweep <= 360°`; value sweep is `p × planned sweep`.
`valueEndAngle = startAngle + valueSweep`; large-arc is `1` iff
`abs(valueSweep) > 180°`. Omit the value sector at `p=0`. At `p=1` with
`360°`, split both boundaries into at least two arcs. Track/value share center,
radii, start, and sweep flags.

**Sunburst — `Approximate`**: one explicit annular sector per node; each depth
owns one radius band and child angular intervals partition the parent. Do not
use one `evenodd` compound ring.

A thin circle with a §6.6 preset or two-number dash stays a `Native-normalized`
ellipse line; the shorthand below is for thick ring segments only.

**Thick-circle shorthand — `Approximate`, non-position-sensitive only**: one
`fill="none"` circle per segment with a two-value `dash gap` covering the
circumference and a direct `stroke-dashoffset`; native construction keeps only
the first dash and starts 90° counterclockwise from the SVG preview, so use
explicit arcs whenever start angle, cap, or radial precision matters.

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

---

### 6.13 Page-Level Composition Recipes

**Reference — not a quota**: use the planned page skeleton; when images are
active, select it through
[`image-layout-patterns.md`](./image-layout-patterns.md). Read each recipe
back-to-front and omit every layer without a distinct job.

| Page / deck job | Back-to-front stack | Stop |
|---|---|---|
| Cover | Hero field → optional scrim/wash → purposeful opening/contour → native title, optionally paired with a prepared decorative-lettering image | Stop when copy is safe and title/field read together |
| Divider | Image band or quiet field → restrained wash → recurring geometry → number/title | Reuse deck language |
| Text-led explanation | Quiet field → recurring material/contour → native hierarchy → optional local emphasis | Emphasis sits on the argument's load-bearing runs |
| Process / system | Context field → native relation lines → nodes/labels → optional state/direction focus | Every connector stays semantic |
| Evidence / metric | Context field → local contrast → native leaders/labels/metric → optional focus/elevation | Claims stay native |
| Comparison | Matched planes → optional shared wash/divider → matched labels → one difference marker | Keep crop, elevation, and paint symmetric unless asymmetry is the claim |
| Closing / CTA | Receded field → echoed contour/gradient → native action → optional raised accent | Keep the native action legible |
| Cross-page motif | Reuse contour, gradient direction, line language, texture, or light logic; vary scale, crop, position by page job | Preserve recognition without copying the page or adding novelty effects |

---
