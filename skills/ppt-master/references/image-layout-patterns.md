# Image and Formula Layout Pattern Catalog

Compact composition vocabulary for prepared images, illustrations, and rendered formula assets. Use the patterns as options, not as a checklist.

---

## 1. Catalog Boundary

| Boundary | Rule |
|---|---|
| Selection | **Reference — not a constraint**: use any pattern, combine compatible ones, or author a clearer free-form composition; no ID, family, or coverage quota applies |
| Canonical IDs | Two-level prompt handles such as `#P1-01` and `#M2-01`; the letters expose composition responsibility, the first digit selects a family, and the final number follows current browse order. No legacy aliases or exporter mapping |
| Composition grammar | Select one or more compatible `P` structures, then add only useful `M`, prepared `A`, or cross-page `C` patterns |
| Effect options | Direction, side, position, proportion, contour, and intensity are options stated after the ID; they do not create another pattern |
| Asset ownership | Consume prepared project-local assets; no acquisition or processing during SVG realization |
| Exact information | Keep exact or editable text, data, labels, and annotations native |

| Group | Responsibility | Families | Entries |
|---|---|---|---:|
| `P` · Primary Structures | Define the page skeleton | `P1` Single Visual · `P2` Image as Canvas · `P3` Multi-Visual | 46 |
| `M` · Modifier Layers | Add crop/reveal, tone/focus, or framing/placement/depth treatment to an existing skeleton | `M1` Reveal/Crop/Registration · `M2` Tone/Focus/Contrast · `M3` Framing/Placement/Depth | 27 |
| `A` · Asset-Dependent Treatments | Require a prepared composite, cutout, or registered derivative | `A1` Composite/Appearance · `A2` Subject Layers · `A3` Registered Derivatives | 10 |
| `C` · Cross-Page Continuity | Sustain a visual relationship across slides | `C1` Persistent State · `C2` Camera Continuity · `C3` Matched Framing | 4 |

| Mechanism, not generic “mask” | Owner |
|---|---|
| Layout geometry | [`image-layout-spec.md`](./image-layout-spec.md) |
| Image-treatment implementation map | [`svg-effects.md`](./svg-effects.md) §6.1 Image-Treatment Implementation Map |
| Crop: policy / legality / wrapper | [`svg-image-embedding.md`](./svg-image-embedding.md) / [`shared-standards-core.md`](./shared-standards-core.md) / [`svg-effects.md`](./svg-effects.md) |
| Scrim / gradient / wash | [`svg-effects.md`](./svg-effects.md) |
| Shadow / glow / overlay-boundary elevation | [`svg-effects.md`](./svg-effects.md) §6.4 |
| Boolean hole / text subtraction | [`native-shape-authoring.md`](./native-shape-authoring.md) |
| Faceted or folded native form | [`native-shape-authoring.md`](./native-shape-authoring.md) §7.1 / [`svg-effects.md`](./svg-effects.md) §6.11 |
| Per-pixel mask / blend | Prepared / baked asset; [`svg-effects.md`](./svg-effects.md) boundary |
| Chart overlay / motion | [`executor-chart.md`](./executor-chart.md) / [`animations.md`](./animations.md) |

---

## 2. Situation Router

| Page need | Pattern options |
|---|---|
| Quiet, direct evidence | `#P1-11` negative space, `#P1-12` framed figure, `#P3-04` small multiples, `#P3-03` comparison |
| One visual should become the page canvas | `#P2-01`–`#P2-10` native overlays |
| One source should span unusual geometry | `#M1-10` one picture, `#M1-11` addressable pictures, `#A3-01` sharp subject over receded copy |
| Several visuals should read as one system | `#P3-05` grid, `#P3-14` mosaic with text cell, `#P3-20` tessellation, `#P3-21` split tiling, `#P3-22` curve array, `#P3-23` depth row |
| A foreground needs an opening or reveal | `#M1-06` true hole, `#M1-07` cut scrim, `#M1-08` background-registered fill, `#M1-05` text subtraction |
| Text needs contrast without discarding the visual | `#M2-01` directional scrim, `#M2-05` spotlight, `#A3-02` prepared frosted panel, `#M2-09` grid scrim |
| A subject should cross or re-layer around native content | `#A2-02` frame breakout or `#A2-03` registered reconstruction group |
| A cover, divider, or promotional page needs image-led structure | `#P1-01`, `#P1-04`, `#P1-13`, or `#P3-15`–`#P3-19` |
| Consecutive pages should share one visual world | `#C1-01` persistent state, `#C2-01` pan, `#C2-02` push/pull, or `#C3-01` matched framing |

---

## 3. Primary Structures

### 3.1 P1 · Single-Visual Structures

- **#P1-01 · Full-bleed title field** — float a native title over one canvas-filling image; optionally use a poster-scale side or lower-corner stack directly on the image without a title card.
- **#P1-02 · Side image with content field** — place one visual beside native copy; let reading direction choose left/right and hierarchy choose partial- or full-height.
- **#P1-03 · Edge-bleed image** — extend the visual beyond one canvas edge so it enters or exits the page instead of sitting in a box.
- **#P1-04 · Image band or belt** — use a top band with content columns below, a middle band with content above and below, or a lower band beneath the title/content field; native copy may also occupy a verified calm zone while the heading stays outside.
- **#P1-05 · Balanced horizontal split** — give image and content balanced top/bottom fields with a deliberate seam.
- **#P1-06 · Central image in a 3×3 field** — put the visual at the center and use surrounding cells for labels, evidence, or small data.
- **#P1-07 · Centered image with radial callouts** — place one focal visual centrally and route native callouts outward.
- **#P1-08 · Diagonal visual/content transition** — use a diagonal image/content boundary whose contour supports the page's reading direction.
- **#P1-09 · Receded image with oversized type** — push the image into the background and make typography the dominant foreground.
- **#P1-10 · Slim image strip with large type** — place a narrow image strip beside oversized horizontal type.
- **#P1-11 · Negative-space dominant** — keep the visual and copy compact so whitespace carries hierarchy.
- **#P1-12 · Framed figure with caption** — float one image in whitespace with a restrained frame and native caption.
- **#P1-13 · Illustration as layout field** — let a large illustration or cutout set the page rhythm; place copy in its calm regions.

### 3.2 P2 · Image as Canvas with Native Overlay

**Reference — not a constraint**: use `P2` when native annotations, data, or process nodes bind to locations inside the prepared visual; an ordinary side image or inset remains `P1` / `P3`.

- **#P2-01 · Annotated evidence** — place compact annotation cards with routed leaders over the visual.
- **#P2-02 · Hotspots with sidebar legend** — pair numbered points on the visual with a matching native legend.
- **#P2-03 · Detail lens** — outline one sub-region on the existing picture and place a native caption nearby; keep one picture object and do not add a rescaled image inset.
- **#P2-04 · Overview with zoom callout** — keep the full overview visible, add a second independently cropped picture from the exact same source, and link the selected region to that detail with native annotation; preserve source-region correspondence, not page-space registration.
- **#P2-05 · Contextual metrics** — place native KPI tiles in calm regions of the visual.
- **#P2-06 · Process through a scene** — connect numbered flow nodes along meaningful geometry in a real or illustrated scene.
- **#P2-07 · Engineering overlay** — add measurement lines, end ticks, module tags, and exact labels.
- **#P2-08 · Architecture or network overlay** — draw native nodes, connections, icons, and labels over the scene.
- **#P2-09 · Interface overlay** — add translucent UI panels, progress indicators, badges, and native arcs.
- **#P2-10 · Accurate chart over visual context** — draw the chart natively, treat the image as context only, and follow [`executor-chart.md`](./executor-chart.md).

`#P2-03` and `#P2-04` are not interchangeable: the former annotates one picture; the latter exports an overview plus a second same-source picture object with an independent crop.

### 3.3 P3 · Multi-Visual Structures

- **#P3-01 · Diptych** — pair two adjacent images around one shared visual argument.
- **#P3-02 · Triptych** — align three distinct sources, unlike a baked multi-scene asset.
- **#P3-03 · Before/after or A/B comparison** — place two equally sized image containers side by side and label both states explicitly.
- **#P3-04 · Small multiples** — arrange same-kind images in identical containers and caption structures so peers can be compared.
- **#P3-05 · Equal-cell tiled grid** — use equal containers when equality and scanability are the message.
- **#P3-06 · Linear image sequence** — align a horizontal sequence by height with content-driven widths, or a vertical sequence by width with annotations and captions on one shared side.
- **#P3-07 · Z-pattern serpentine** — alternate image and text positions down successive bands to create a zigzag reading path.
- **#P3-08 · Ascending or descending picture process** — step image containers progressively upward or downward and use native numbering or connectors to preserve sequence.
- **#P3-09 · Picture-in-picture inset** — overlay one framed image over a larger source; use `#P2-04` when the inset magnifies a selected region from that exact source.
- **#P3-10 · Overlapping image stack** — use z-order and restrained offsets to create a layered print or archive feel.
- **#P3-11 · Asymmetric collage** — balance one dominant visual with smaller supporting visuals using consistent gaps.
- **#P3-12 · Irregular mosaic** — pack different-sized tiles into one coherent field.
- **#P3-13 · Montage with spanning type** — tile several visuals and run one legible native title treatment across the assembled field.
- **#P3-14 · Photo mosaic with a text cell** — reserve one mosaic cell for copy so absence of a photo creates hierarchy.
- **#P3-15 · Image-navigation table of contents** — turn sections into visual navigation cards with native numbering and summaries.
- **#P3-16 · Asymmetric dual-image chapter banner** — pair a compact image with a wider image and anchor them with a native section marker.
- **#P3-17 · Ambient image, evidence image, and text panel** — let one visual establish mood and another provide concrete proof.
- **#P3-18 · Ribbon-header image cards** — give peer image columns distinct native ribbon or chevron headings.
- **#P3-19 · Side hero with staggered evidence cards** — pair a full-height hero field with supporting cards that step through the opposite side.
- **#P3-20 · Non-rectangular tessellation** — tile clipped geometric cells and reserve selected cells for native copy or color.
- **#P3-21 · Split tiling** — fragment one parent contour into interlocking cells, each holding a different image as an independent object.
- **#P3-22 · Containers arrayed along a curve** — distribute containers consistently along an arc, wave, or ring; keep image orientation intentional.
- **#P3-23 · Embracing arc row** — create depth with a center-weighted scale and vertical-offset rhythm while keeping the objects two-dimensional.

---

## 4. Modifier Layers

### 4.1 M1 · Reveal, Crop, and Registration

- **#M1-01 · Geometric crop** — clip the visual to a circle, ellipse, rounded rectangle, or bounded polygon; the contour is an effect option.
- **#M1-02 · Custom-path crop** — use one authored organic or silhouette contour when a basic geometric crop cannot express it.
- **#M1-03 · Layered paper-cut stack** — clip image layers independently and draw vector layers in their final geometry.
- **#M1-04 · Faux painted knock-out** — cover part of an image with the matching background or another prepared visual only when the surrounding field makes the imitation credible.
- **#M1-05 · Text-as-subtraction** — reveal an image or field through glyph-shaped holes; materialize supported text Boolean geometry through [`native-shape-authoring.md`](./native-shape-authoring.md).
- **#M1-06 · Panel with a true hole** — subtract an opening from a foreground panel so changing content behind it remains valid; follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6.
- **#M1-07 · Scrim with true cutouts** — subtract image-reveal openings from a full-canvas scrim; lettering and complex cuts follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6.
- **#M1-08 · Background-registered shape fill** — fill a stationary shape with the page background sampled in root coordinates so it impersonates a hole while remaining an object.
- **#M1-09 · Deliberately misregistered fragments** — separate same-source fragments and break their alignment intentionally for torn, misprint, or glitch language.
- **#M1-10 · One image across detached shapes** — export one native picture with disjoint clip subpaths so one continuous scene spans every shape.
- **#M1-11 · Same-source addressable crops** — export several independent native pictures that share an exact source coordinate system; follow [`executor-image.md`](./executor-image.md) §1.

The following three patterns are topologically different and are not interchangeable:

| ID | Sources | Exported picture topology | Visual relationship |
|---|---|---|---|
| One-picture compound crop (`#M1-10`) | One source | One native picture with disjoint clip subpaths | One continuous scene spans detached shapes; fragments are not independent picture objects |
| Addressable same-source crops (`#M1-11`) | One exact source reference | Several independently addressable native pictures | Crops share one source coordinate system and remain in exact registration; follow [`executor-image.md`](./executor-image.md) §1 |
| Different-source split tiling (`#P3-21`) | Different sources | Several independent picture objects in interlocking cells | The parent contour unifies peers; scene continuity across cells is not implied |

### 4.2 M2 · Tone, Focus, and Contrast

- **#M2-01 · Directional gradient scrim** — add directional contrast while retaining image detail; when copy overlays the image, protect its side and keep the focal side clear. Direction, protected side, opacity curve, and stops are options.
- **#M2-02 · Radial vignette** — darken the periphery to emphasize the central field.
- **#M2-03 · Flat wash** — uniformly darken, lighten, or palette-tint an image to integrate it with the page.
- **#M2-04 · Multi-hue gradient scrim** — shift color temperature or bridge image regions with a multi-stop field.
- **#M2-05 · Radial spotlight** — keep a selected region clear while surrounding content recedes.
- **#M2-06 · Texture or atmospheric wash** — turn an image into a low-contrast supporting texture or atmosphere field rather than presenting it as primary evidence.
- **#M2-07 · Watermark image field** — place a strongly receded image behind body copy.
- **#M2-08 · Fade into a solid background** — match the fade endpoint to the page background so the image edge disappears.
- **#M2-09 · Grid scrim with varied opacity** — modulate one underlying image through a seamless grid of translucent cells.

### 4.3 M3 · Framing, Placement, and Depth Accents

- **#M3-01 · Restrained image frame** — trace the image with one restrained outline.
- **#M3-02 · Repeated photo-print frames** — repeat nearby outlines for a layered photo-print treatment.
- **#M3-03 · Editorial rotation** — rotate an image or its container slightly when the style benefits from an informal print gesture.
- **#M3-04 · Lifted image panel** — separate a standalone image panel from the background with one restrained depth cue; [`svg-effects.md`](./svg-effects.md) owns the legal effect.
- **#M3-05 · Contour echo** — reuse a non-rectangular clip contour as an offset stroke instead of boxing it in a rectangle.
- **#M3-06 · Decorative corner fragment** — use a cropped image fragment as a secondary corner accent.
- **#M3-07 · Image divider band** — replace a line between content regions with a narrow visual strip.

---

## 5. Asset-Dependent Treatments

**Prepared-asset gate**: every treatment below consumes its named project-local asset; it does not authorize creation during SVG realization. Embedded lettering belongs to the artwork only when deliberately fixed; authoritative or editable labels remain native SVG. If a required asset is absent, return to the active workflow's preparation owner or choose a native treatment.

### 5.1 A1 · Prepared Composites and Appearance

- **#A1-01 · Baked multi-scene composite** — use one prepared source containing coordinated internal scenes; distinct from a `P3` structure built from separate images.
- **#A1-02 · Prepared blurred backdrop** — use a prepared blurred asset; runtime image blur is not the backdrop mechanism.
- **#A1-03 · Prepared duotone photograph** — use a prepared two-color image treatment.
- **#A1-04 · Prepared soft image-to-image blend** — use a precomposited or baked-alpha asset when arbitrary images must blend per pixel.

### 5.2 A2 · Subject and Cutout Layers

- **#A2-01 · Transparent sticker or cutout** — use a prepared RGBA asset and preserve its open silhouette.
- **#A2-02 · Subject breaking out of a container** — register a prepared foreground subject across its frame boundary.
- **#A2-03 · Registered reconstruction group** — align a clean base with one or more prepared transparent midground/subject/foreground layers in one coordinate system. Draw each member at its required z-order. Give every full-canvas member the same `x`, `y`, `width`, `height`, and aspect mapping; never trim or independently crop it. Several padded-bbox-disjoint objects may share one prepared plate while remaining separate nested-SVG picture crops.

### 5.3 A3 · Registered Derivatives

- **#A3-01 · Sharp subject over receded full-frame derivative** — register a sharp focal crop or prepared cutout subject over a blurred, tinted, or desaturated full-frame derivative; never cover it with an opaque full-frame copy.
- **#A3-02 · Registered frosted-glass panel** — place a prepared registered blurred crop beneath the native text panel.
- **#A3-03 · Selective desaturation** — register a prepared color subject layer over a desaturated base.

---

## 6. Cross-Page Continuity

### 6.1 C1 · Persistent Visual State

- **#C1-01 · Persistent visual with progressive overlays** — keep one source, crop, and placement stable while native annotations or claims change, replace, or accumulate across consecutive pages.

### 6.2 C2 · Camera Continuity

- **#C2-01 · Cross-page image pan** — show different regions of one wide image across consecutive pages so the audience recognizes one continuous place.
- **#C2-02 · Cross-page push-in or pull-out** — reuse one source while the crop or scale moves from overview to detail, or detail to overview, across consecutive pages.

If motion is enabled, [`animations.md`](./animations.md) owns its implementation; these patterns only define the static framing relationship.

### 6.3 C3 · Matched Framing

- **#C3-01 · Matched framing across sources** — keep the subject anchor, visual scale, horizon, or dominant contour aligned while consecutive pages replace one source with another.

---

## 7. Composition Playbook

**Reference — not a constraint**: build from the page's communication job, not catalog coverage. Choose the smallest combination that resolves the page and any intentional cross-page relationship.

### 7.1 Combination Procedure

| Pass | Decision |
|---|---|
| Skeleton | Select the `P` relationship: one visual field, comparison, sequence, evidence view, or multi-image system. Compatible Primaries may share one page |
| Job | Name the concrete integration need or stylistic role: contrast, aspect fit, focus, reveal/opening, peer cohesion, exact native information, or a recurring depth/print gesture |
| Apply | Add the smallest `M` that serves each chosen job; add no technique without a job |
| Prepared asset | Use `A` only when the named project-local composite, cutout, or derivative already exists |
| Continuity | Add `C` only when adjacent pages deliberately share a persistent state, camera relationship, or matched framing |
| Integrate | Reuse contours, baselines, gap rhythm, palette, and required registration so the layers read as one composition |
| Stop | Omit or simplify the next layer when it repeats a job, competes with the message, requires an unavailable asset, or weakens legibility/editability |

### 7.2 High-Yield Combinations

| Page job | Composition candidates |
|---|---|
| Atmospheric cover or divider | `#P1-01` + `#M2-01`; use `#M1-07` + optional `#M3-05` when an opening should supply the page character |
| One source does not fit the canvas | `#A3-01` + `#M1-02` or `#M1-10`, with every copy kept in exact registration |
| Comparison with evidence on both sides | `#P3-03` + `#P2-01`; keep labels, leaders, and exact claims native |
| Scene-backed evidence or metrics | `#P2-01` / `#P2-05` + `#M2-01` or `#M2-03`; let the image carry context and native SVG carry information |
| One selected region needs explanation | Use `#P2-03` for an outline and caption on one picture; use `#P2-04` when a second same-source picture must magnify the region |
| Several sources should read as one object | `#P3-21` + restrained `#M3-01`, or `#P3-20` + a native text/color cell |
| One continuous scene should span detached shapes | `#M1-10` + optional `#M3-05`; keep one-picture topology |
| Same-source windows must remain independent | `#M1-11`; add `#C2-01` or `#C2-02` only when consecutive pages use the relationship |
| A prepared subject should re-layer over its source | `#A2-03`; keep the base and cutout registered, and insert a native middle layer only when it has a distinct job |
| A busy visual needs one focal region | `#M2-05`, or prepared `#A3-01` / `#A3-03` when a native contrast treatment is insufficient |
| A visual argument should build across pages | `#C1-01` + `#P2-01` or `#P2-05`; keep the underlying source and frame stable |
| Formula or technical figure needs explanation | `#P1-12` + `#P2-07` / `#P2-03`; use `#P2-04` only when a second cropped detail is useful, and keep explanatory labels native |

**Registration boundary**: registration-dependent effects succeed only when their declared coordinate relationship remains exact. Preserve registration for `#M1-10`, `#A2-02`, `#A3-01`, `#M1-08`, `#A2-03`, `#A3-02`, `#A3-03`, and `#M1-11`; `#M1-09` is the intentional exception.

**Source-correspondence boundary**: `#P2-04` reuses one exact source but intentionally changes the detail crop, scale, and placement; preserve the selected-region correspondence instead of forcing page-space registration.

**Formula placement**: treat a rendered formula as a prepared visual asset. Use whitespace patterns such as `#P1-11` or `#P1-12` for isolated derivations, `#P1-07`, `#P2-07`, `#P2-03`, or `#P2-04` for annotated formulas, and `#P3-04` or `#P3-03` for comparisons; keep editable explanatory text native.

All compatibility details remain owned by [`shared-standards-core.md`](./shared-standards-core.md) and its routed references.
