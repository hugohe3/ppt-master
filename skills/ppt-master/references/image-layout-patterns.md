# Image and Formula Layout Pattern Catalog

Compact composition vocabulary for prepared images, illustrations, and rendered formula assets. Use the patterns as options, not as a checklist.

---

## 1. Catalog Boundary

| Boundary | Rule |
|---|---|
| Selection | **Reference — not a constraint**: use any pattern, combine compatible ones, or author a clearer free-form composition; no ID, family, or coverage quota applies |
| Stable IDs | `#1`–`#100` are stable lookup handles, not a workflow |
| Primary vs modifier | One or more compatible Primary Structures + `0..n` Modifier Layers |
| Asset ownership | Consume prepared project-local assets; no acquisition or processing during SVG realization |
| Exact information | Keep exact or editable text, data, labels, and annotations native |

| Mechanism, not generic “mask” | Owner |
|---|---|
| Layout geometry | [`image-layout-spec.md`](./image-layout-spec.md) |
| Crop: policy / legality / wrapper | [`svg-image-embedding.md`](./svg-image-embedding.md) / [`shared-standards-core.md`](./shared-standards-core.md) / [`svg-effects.md`](./svg-effects.md) |
| Scrim / gradient / wash / depth paint | [`svg-effects.md`](./svg-effects.md) |
| Boolean hole / text subtraction | [`native-shape-authoring.md`](./native-shape-authoring.md) |
| Per-pixel mask / blend | Prepared / baked asset; [`svg-effects.md`](./svg-effects.md) boundary |
| Chart overlay / motion | [`executor-chart.md`](./executor-chart.md) / [`animations.md`](./animations.md) |

---

## 2. Situation Router

| Page need | Pattern options |
|---|---|
| Quiet, direct evidence | `#16` negative space, `#19` framed figure, `#47` small multiples, `#48` comparison |
| One visual should become the page canvas | `#38`–`#46` native overlays |
| One source should span unusual geometry | `#82` one picture, `#100` addressable pictures, `#89` sharp subject over receded copy |
| Several visuals should read as one system | `#50` grid, `#77` mosaic with text cell, `#88` tessellation, `#92` split tiling, `#93` curve array, `#94` depth row |
| A foreground needs an opening or reveal | `#83` true hole, `#90` cut scrim, `#95` background-registered fill, `#68` text subtraction |
| Text needs contrast without discarding the visual | `#29` directional scrim, `#33` spotlight, `#97` prepared frosted panel, `#98` grid scrim |
| A cover, divider, or promotional page needs image-led structure | `#73`–`#81` |
| Consecutive pages should share one visual world | `#87` cross-page pan opportunity |

---

## 3. Primary Structures

### 3.1 Single-Image Layouts

1 · 73. **Full-bleed title structures** — **#1** floats a title over one canvas-filling image; **#73** uses a poster-like side or lower-corner title stack without a title card.

2–3. **Side image and text** — **#2** places the visual left and copy right; **#3** mirrors that relationship.

4. **Edge-bleed image** — extend the visual beyond one canvas edge so it enters or exits the page instead of sitting in a box.

5–7. **Horizontal split structures** — **#5** uses an upper image band with content columns below; **#6** places the image band below a title/content field; **#7** gives image and content balanced top/bottom fields with a deliberate seam.

9. **Central image in a 3×3 field** — put the visual at the center and use surrounding cells for labels, evidence, or small data.

10. **Centered image with radial callouts** — place one focal visual centrally and route native callouts outward.

11. **Diagonal visual/content transition** — use a diagonal edge or directional fade whose contour supports the page's reading direction.

12. **Receded image with oversized type** — push the image into the background and make typography the dominant foreground.

13 · 18. **Vertical image columns** — **#13** is a slim strip beside giant horizontal type; **#18** is a full-height sidebar beside a general content field.

14 · 76. **Mid-page image bands** — **#14** runs a banner between content above and below; **#76** places native copy in a calm part of a wider image belt while keeping the heading outside.

16. **Negative-space dominant** — keep the visual and copy compact so whitespace carries hierarchy.

19. **Framed image with caption** — float one image in whitespace with a restrained frame and native caption.

81. **Illustration-as-layout field** — let a large illustration or cutout set the page rhythm; place copy in its calm regions.

### 3.2 Image-as-Canvas Layouts with Native Overlay

Use the prepared visual as the spatial field while native SVG carries the information layer.

38. **Annotated evidence** — place compact annotation cards with routed leaders over the visual.

39. **Process through a scene** — connect numbered flow nodes along meaningful geometry in a real or illustrated scene.

40. **Contextual metrics** — place native KPI tiles in calm regions of the visual.

41. **Engineering overlay** — add measurement lines, end ticks, module tags, and exact labels.

42. **Interface overlay** — add translucent UI panels, progress indicators, badges, and native arcs.

43. **Accurate chart over visual context** — draw the chart natively, treat the image as context only, and follow [`executor-chart.md`](./executor-chart.md).

44. **Architecture or network overlay** — draw native nodes, connections, icons, and labels over the scene.

45. **Hotspots with sidebar legend** — pair numbered points on the visual with a matching native legend.

46. **Detail lens** — border one sub-region and place a native caption nearby.

### 3.3 Multi-Image Layouts

8. **Z-pattern serpentine** — alternate image and text positions down successive bands to create a zigzag reading path.

15. **Montage with spanning type** — tile several visuals and run one legible title treatment across the assembled field.

17. **Picture-in-picture inset** — overlay one framed inset image over a larger image; the sources may differ. Use `#62` when an overview and detail must share one source.

47. **Small multiples** — arrange same-kind images in one evenly spaced row with identical containers and caption structures so peers can be compared.

48. **Before/after or A/B comparison** — place two equally sized image containers side by side and label both states explicitly.

49. **Asymmetric collage** — balance one dominant visual with smaller supporting visuals using consistent gaps.

50. **Equal-cell tiled grid** — use equal containers when equality and scanability are the message.

51. **Irregular mosaic** — pack different-sized tiles into one coherent field.

52–53. **Filmstrip and stack** — **#52** aligns a horizontal sequence by height while allowing content-driven widths; **#53** aligns a vertical sequence by width with annotations on a shared side.

54. **Overlapping image stack** — use z-order and restrained offsets to create a layered print or archive feel.

55–56. **Diptych and triptych** — **#55** pairs adjacent images; **#56** aligns three distinct sources, unlike baked **#26**.

74. **Image-navigation table of contents** — turn sections into visual navigation cards with native numbering and summaries.

75. **Asymmetric dual-image chapter banner** — pair a compact image with a wider image and anchor them with a native section marker.

77. **Photo mosaic with a text cell** — reserve one mosaic cell for copy so absence of a photo creates hierarchy.

78. **Ambient image, evidence image, and text panel** — let one visual establish mood and another provide concrete proof.

79. **Ribbon-header image cards** — give peer image columns distinct native ribbon or chevron headings.

80. **Side hero with staggered evidence cards** — pair a full-height hero field with supporting cards that step through the opposite side.

88. **Non-rectangular tessellation** — tile clipped geometric cells and reserve selected cells for native copy or color.

92. **Split tiling** — fragment one parent contour into interlocking cells, each holding a different image as an independent object.

93. **Containers arrayed along a curve** — distribute containers consistently along an arc, wave, or ring; keep image orientation intentional.

94. **Embracing arc row** — create depth with a center-weighted scale and vertical-offset rhythm while keeping the objects two-dimensional.

---

## 4. Modifier Layers

### 4.1 Reveal, Crop, and Registration

20–23. **Basic crops** — **#20** is a circle, **#21** a rounded rectangle, **#22** an ellipse, and **#23** a bounded polygon.

24. **Custom-path crop** — use one authored organic or silhouette contour when basic crops cannot express it.

25. **Layered paper-cut stack** — clip image layers independently and draw vector layers in their final geometry.

62. **Full view plus zoom callout** — reuse one source for an overview and a differently cropped detail linked by native annotation.

67. **Painted knock-out** — cover part of an image with the matching background or another prepared visual; use this imitation only when the surrounding field makes it credible.

68. **Text-as-subtraction** — reveal an image or field through glyph-shaped holes; materialize supported text Boolean geometry through [`native-shape-authoring.md`](./native-shape-authoring.md).

83. **Panel with a true hole** — subtract an opening from a foreground panel so changing content behind it remains valid; follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6.

84. **Deliberately misregistered fragments** — separate same-source fragments and break their alignment intentionally for torn, misprint, or glitch language.

85. **Subject breaking out of a container** — layer a registered foreground subject across its frame boundary; use an already prepared cutout when the composition requires one.

90. **Scrim with true cutouts** — subtract image-reveal openings from a full-canvas scrim; lettering and complex cuts follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6.

95. **Background-registered shape fill** — fill a stationary shape with the page background sampled in root coordinates so it impersonates a hole while remaining an object.

82. **One image across detached shapes** — export one native picture with disjoint clip subpaths so one continuous scene spans every shape.

100. **Same-source addressable crops** — export several independent native pictures that share an exact source coordinate system; follow [`executor-image.md`](./executor-image.md) §1.

The following three patterns are topologically different and are not interchangeable:

| ID | Sources | Exported picture topology | Visual relationship |
|---|---|---|---|
| One-picture compound crop (`#82`) | One source | One native picture with disjoint clip subpaths | One continuous scene spans detached shapes; fragments are not independent picture objects |
| Addressable same-source crops (`#100`) | One exact source reference | Several independently addressable native pictures | Crops share one source coordinate system and remain in exact registration; follow [`executor-image.md`](./executor-image.md) §1 |
| Different-source split tiling (`#92`) | Different sources | Several independent picture objects in interlocking cells | The parent contour unifies peers; scene continuity across cells is not implied |

### 4.2 Tone and Contrast

27. **Linear-gradient scrim** — add directional contrast while retaining image detail.

28. **Radial vignette** — darken the periphery to emphasize the central field.

29. **Opaque-to-transparent directional scrim** — protect copy on one side while keeping the focal side clear.

30–31. **Flat washes** — **#30** uniformly darkens or lightens with a neutral wash; **#31** uses a palette color to integrate a foreign-looking image.

32. **Multi-hue gradient scrim** — shift color temperature or bridge image regions with a multi-stop field.

33. **Radial spotlight** — keep a selected region clear while surrounding content recedes.

57 · 60 · 61. **Receded image fields** — **#57** is a texture wash, **#60** ambient atmosphere, and **#61** a watermark behind body copy.

66. **Fade into a solid background** — match the fade endpoint to the page background so the image edge disappears.

98. **Grid scrim with varied cell opacity** — modulate one underlying image through a seamless grid of translucent cells.

### 4.3 Placement, Framing, and Depth

58. **Decorative corner fragment** — use a cropped image fragment as a secondary corner accent.

59. **Image divider band** — replace a line between content regions with a narrow visual strip.

36. **Shadow under an image panel** — apply one §6.4 filter directly to a standalone unclipped `<image>`; for a clipped picture, keep `clip-path` on the image and put the filter on its exact single-image outer carrier. When the lifted object includes a frame or caption, shadow that supporting shape instead.

37. **Glow on an overlay shape** — emphasize an overlay boundary within the supported effect contract.

69. **Editorial rotation** — rotate an image or its container slightly when the style benefits from an informal print gesture.

70–71. **Frames** — **#70** traces the image with one restrained outline; **#71** repeats nearby outlines for a layered photo-print treatment.

86. **Contour echo** — reuse a non-rectangular clip contour as an offset stroke instead of boxing it in a rectangle.

91. **Faceted gradient form** — build a folded or ribbon-like object from adjacent facets with consistent light logic.

### 4.4 Prepared-Asset Treatments

**Prepared-asset gate**: every treatment below consumes its named project-local asset; it does not authorize creation during SVG realization. In particular, `#96`, `#97`, and `#99` require their derivative pairs in advance. If a required asset is absent, return to the active workflow's preparation owner or choose a native treatment.

26. **Baked triptych** — use one prepared wide source containing coordinated internal scenes; distinct from separate-image **#56**.

34. **Blurred-image backdrop** — use a prepared blurred asset; runtime image blur is not the backdrop mechanism.

35. **Duotone photograph** — use a prepared two-color image treatment.

63. **Transparent sticker or cutout** — use a prepared RGBA asset and preserve its open silhouette.

64. **Artwork with embedded lettering** — use only for deliberate, fixed lettering that belongs to the artwork.

65. **Text-free artwork with native labels** — keep authoritative or editable labels outside the asset as native SVG.

72. **Soft image-to-image blend** — use a precomposited or baked-alpha asset when arbitrary images must blend per pixel.

89. **Sharp subject over a receded full-frame copy** — register two references to the same source; any blurred or desaturated derivative must already be prepared.

96. **Cutout subject re-laid over its source photo** — use a base photo plus its prepared transparent subject cutout, aligned in one coordinate system.

97. **Frosted-glass image panel** — use a base photo plus its prepared registered blurred crop beneath the text panel.

99. **Selective desaturation** — use a prepared desaturated base plus a registered color subject layer.

### 4.5 Cross-Page Continuity

87. **Cross-page image pan opportunity** — show different regions of one wide image across consecutive pages so the audience recognizes one continuous place. Keep the source and framing relationship coherent; if motion is enabled, [`animations.md`](./animations.md) owns its implementation.

---

## 5. Composition Playbook

**Reference — not a constraint**: build from the page's communication job, not catalog coverage. Choose one or more compatible Primary Structures, then add only Modifier Layers or native overlays that solve an observed page problem.

### 5.1 Combination Procedure

| Pass | Decision |
|---|---|
| Skeleton | Select the Primary relationship: one visual field, comparison, sequence, evidence view, or multi-image system. Compatible Primaries may share one page. |
| Diagnose | Name the concrete integration problem: weak text contrast, aspect mismatch, unclear focus, missing reveal/opening, unrelated peers, or exact information needing a native layer. |
| Repair | Add the smallest legal Modifier or native overlay that solves each chosen problem; add no technique without a job. |
| Integrate | Reuse contours, baselines, gap rhythm, palette, and required registration so the layers read as one composition. |
| Stop | Omit or simplify the next layer when it repeats a job, competes with the message, requires an unavailable asset, or weakens legibility/editability. |

### 5.2 High-Yield Combinations

| Page job | Composition candidates |
|---|---|
| Atmospheric cover or divider | `#1` / `#73` + `#29`; use `#90` + optional `#86` when an opening should supply the page character |
| One source does not fit the canvas | `#89` + `#24` or `#82`, with every copy kept in exact registration |
| Comparison with evidence on both sides | `#48` + `#38`; keep labels, leaders, and exact claims native |
| Scene-backed evidence or metrics | `#38` / `#40` + `#29` or `#30`; let the image carry context and native SVG carry information |
| Several sources should read as one object | `#92` + restrained `#70`, or `#88` + a native text/color cell |
| One continuous scene should span detached shapes | `#82` + optional `#86`; keep one-picture topology |
| Same-source windows must remain independent | `#100`; add `#87` only when consecutive pages benefit from continuity or motion |
| A busy visual needs one focal region | `#33`, or prepared-pair `#96` / `#99` when native contrast treatment is insufficient |
| Formula or technical figure needs explanation | `#19` + `#41` / `#46`; keep explanatory labels native |

**Registration boundary**: registration-dependent effects succeed only when their declared coordinate relationship remains exact. Preserve registration for `#62`, `#82`, `#85`, `#89`, `#95`, `#96`, `#97`, `#99`, and `#100`; `#84` is the intentional exception.

**Formula placement**: treat a rendered formula as a prepared visual asset. Use whitespace patterns such as `#16` or `#19` for isolated derivations, `#10`, `#41`, or `#46` for annotated formulas, and `#47` or `#48` for comparisons; keep editable explanatory text native.

All compatibility details remain owned by [`shared-standards-core.md`](./shared-standards-core.md) and its routed references.
