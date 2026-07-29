# Image-Text Layout Pattern Library

An optional vocabulary library for ways images can be placed on a slide. Open it when a page would benefit from more composition ideas; ordinary natural-language layout suggestions remain valid without consulting or citing the library. When using it, start at **High-Yield Patterns** below.

Every entry has a name plus a short technical hint. Common techniques get a single line. Less obvious or easily forgotten techniques get a short paragraph — not a full tutorial, but enough that a model unfamiliar with the project can implement it without guessing. This is an inspiration library, not a legality boundary or teaching document; it sets no usage, id, family, or coverage quota.

> **Numbers are stable optional identifiers, not sequence.** The file is split into **Part 1 — Primary Structures** (#1–#19, #38–#56, #73–#81, #88, #92–#94) and **Part 2 — Modifier Layers** (#20–#37, #57–#72, #82–#87, #89–#91, #95–#100). Numbers jump within each Part because Primary structures were grouped first; existing references to `#38`, `#48`, etc. anywhere in the project still resolve correctly. **High-Yield Patterns** is a router over those same numbers; use it when entering by page situation.

---

## Core Principle — Two Layers

Almost every pattern below is an instance of one underlying split:

> **The image carries atmosphere, world-building, emotional weight. Native SVG shapes carry information, data, editable text.**

This is the single most underused move in image-heavy decks. The default reflex is to place image and text in adjacent rectangles. The far more powerful move — especially for content-rich pages — is to let the image **be the canvas** (often full-bleed) and draw native vector elements (annotation cards, flow nodes, KPI tiles, leader lines, network diagrams, dashboards) directly on top.

Anything that must remain editable, numerically or semantically exact, or styled to the deck's exact typography belongs in the SVG layer regardless of what the image looks like underneath. Script alone never decides ownership.

---

## High-Yield Patterns — Optional Starting Points

The patterns below are efficient ways to expand a page beyond familiar splits. Nearly all of them are **one `<image>` plus geometry** — no extra asset, no generation cost, no second render — and they are the SVG equivalents of what PowerPoint users reach for under Merge Shapes.

**Reference — not a constraint**: use this router when it adds a useful composition option. A plain split, equal grid, bare whitespace, or an unlisted free-form construction remains valid when it serves the content.

| Page situation | Reach for | Produces |
|---|---|---|
| One ordinary photo must carry a cover or a chapter divider | `#90` scrim with shapes cut out + `#86` contour echo | Three elements turn a stock image into a designed page; the cut contour is where the page's character comes from |
| The supplied image does not fit the canvas | `#89` same image twice — sharp cutout over a receded copy | Subject at full fidelity in any aspect ratio; no stretching, no letterbox bars, no second asset |
| Several peer images belong to one frame | `#92` split tiling — one parent cut into interlocking cells | Edges interlock exactly; the group still reads as one object |
| One image should span detached containers as one edit object | `#82` one image shattered across separated shapes | Merge-Shapes look; the photo runs continuously behind the gaps |
| Those same-source containers must remain independently editable or animated | `#100` same-source addressable crops | Several native picture objects share one source coordinate system without slice assets |
| A panel needs a real opening onto what is behind it | `#83` panel with a hole punched through it | True subtraction — survives a gradient, a texture, or a second image behind the panel |
| A photo row needs depth without 3D | `#94` embracing arc row, or `#93` containers arrayed along a curve | A perspective wall reproduced in 2D from scale + vertical offset alone |
| A flat scrim reads as a sheet of paint over the photo | `#98` grid scrim with per-cell opacity | The overlay reads as panelled glass or a contact sheet, felt rather than drawn |
| A busy photo has no clear focus | `#99` selective desaturation, or `#96` cutout subject re-laid over its own photo | Focus without cropping; the subject can then overlap a title, a panel, or a grid line |
| Text needs legibility but a solid scrim would kill the photo | `#97` frosted-glass panel | The photo's colour and composition stay visible through the panel |
| An image grid looks like a stock template | `#88` non-rectangular tessellation with 1–3 cells left empty | The empty cells are where the title and body copy live |
| A subject should escape its container | `#85` subject breaking out + `#96` | Depth with no shadow at all |
| One place should be recognized across consecutive pages | `#87` one image panned across pages | The deck reads as one continuous scene; `-t morph` uses heuristic matching, while explicit `morph.pairs` makes the camera pan deterministic |

**Reference — not a constraint**: when citing a modifier-only result, also name the content-appropriate Primary that supplies the page bones. Free-form suggestions may describe the complete relationship without catalog ids.

**Hard rule — registration is what makes this family work**: in `#82`, `#85`, `#87`, `#89`, `#96`, `#97`, and `#100`, the image stays anchored to the *union* of its containers, or the copies share one source coordinate system. A few pixels of drift reads as a printing error. `#84` alone breaks registration on purpose.

**Prepared-asset gate**: select `#96` only when a registered cutout PNG already exists, `#97` only when its blurred crop exists, and `#99` only when its desaturated copy exists. If not, keep the original asset and fall back to a native-shape treatment such as `#30` / `#29`; do not invent an image-processing step during execution.

**Reference — not a constraint**: repeated plain splits may be a reason to consult this library, but are not evidence of failure. Neither §VIII nor the final deck must cite an id or cover a pattern family.

Each entry above is specified in full at its own number below; the table routes, it does not restate.

---

# Part 1 — Primary Structures

Pick one or more of these as the page's bones. Cross-primary combinations are encouraged (see Composition Guidance).

## Container Layouts (where the image sits)

1. **Full-bleed background with floating title** — `<image x=0 y=0 width=1280 height=720 preserveAspectRatio="xMidYMid slice"/>` + scrim `<rect>` for legibility + overlay `<text>`.

2. **Left-third image + right text body** — `<image x=0 y=0 width=~427 height=720>` on the left; text area in the remaining width; optional right-edge gradient fade for smooth transition.

3. **Right-third image + left text body** — mirror of #2.

4. **Right image bleeding off the canvas edge** — `<image>` width extended past viewBox; text on left with a rightward gradient fade so the image emerges from the text area without a visible boundary.

5. **Top-band image + bottom multi-column text** — `<image x=0 y=0 width=1280 height=~340>` at the top + bottom-fade gradient + 2–3 evenly spaced text columns below.

6. **Bottom-band image + top title + middle text** — mirror of #5 with the image at the bottom and a top-fade gradient.

7. **Top-and-bottom symmetric split** — image occupies 50% (top or bottom) with a divider line or thin gradient band separating the halves.

8. **Z-pattern serpentine** — three rows, image on the left in rows 1 and 3, on the right in row 2 (or alternating). Each row roughly 1/3 canvas height; visual flow zigzags down the page.

9. **3×3 grid with central image** — nine cells; center cell holds the image, the other 8 hold text blocks, color swatches, or small data widgets.

93. **Containers arrayed along a curve (fan, arc, ring)** — N image containers distributed along an arc or wave, each rotated to sit square to the curve at its own position. Reads as motion and hierarchy at once, and it is the backbone of fan spreads, ring layouts, dial/roulette pages, and arched photo rows.

    **Geometry** — place container `i` of `n` on a circle of radius `r` about `(cx, cy)`:
    ```
    θᵢ = θ_start + i × (θ_span / (n − 1))
    xᵢ = cx + r·cos(θᵢ)      yᵢ = cy + r·sin(θᵢ)
    rotationᵢ = θᵢ + 90°          (tangent-aligned; drop this for upright containers)
    ```
    Use `transform="rotate(rotationᵢ xᵢ yᵢ)"` on each container group. A `θ_span` of 60–120° reads as a fan; 360° with `θ_start = -90°` gives an evenly spaced ring. For a wave instead of an arc, sample the wave's own path and use its local tangent as the rotation.

    **Two things to get right**: keep radius and angular step *constant* — an eyeballed fan reads as a mistake, not a flourish; and when containers are tangent-aligned, images inside must not inherit the rotation blindly (a sideways face is the failure mode). Counter-rotate the image inside its container, or keep the containers upright and let only their positions follow the curve.

10. **Centered image with radial callouts pointing outward** — image (often circular via `clipPath`) at canvas center; multiple `<line>` leader lines + small `<circle>` endpoints + offset text labels in surrounding space.

11. **Diagonal split with directional gradient (not hard polygon cut)** — full-bleed `<image>` + overlay `<rect fill="url(#grad)">` whose gradient axis runs along the diagonal, plus a `<line>` to make the divider read. Do NOT hard-clip: polygon cuts give stair-stepped edges on text panels.

12. **Faded image as backdrop with oversized overlay text** — `<image>` + heavy semi-transparent `<rect fill="bg-color" fill-opacity="0.5–0.7">` over it + huge `<text>` (80–120px) on top. Image becomes texture; text is the subject.

13. **Narrow vertical image strip + giant horizontal title** — `<image x=0 y=0 width=200–280 height=720>` + thick divider `<rect>` + large `<text>` (60–90px) in the remaining width.

14. **Horizontal banner strip cutting through mid-section** — `<image y=middle width=1280 height=200–280>` with edge fades; text blocks above and below the band.

15. **Multi-image montage with bold text spanning across** — `<image>` tiled with 2–4px gaps + large `<text>` (60–100px) in a `<rect fill-opacity="0.5–0.7">` band spanning the montage, so the text stays legible across every tile beneath it.

16. **Negative-space dominant — small image, mostly whitespace** — image and text together occupy less than 40% of the canvas; rest is empty.

17. **Picture-in-picture inset** — large `<image>` background + small `<image>` overlaid inside it with a `<rect>` frame.

18. **Image as full-height sidebar column** — narrow `<image x=0 y=0 width=~200–280 height=720>`; rest of canvas is content area.

19. **Image floating in whitespace with thin frame and caption** — `<image>` + thin `<rect fill="none" stroke="…">` frame around it + `<text>` caption below.

## Image-as-Canvas + Native Overlay (the most underused family)

This is the family that opens up the largest design space and the one AI is most likely to skip. The shared pattern: image fills the slide (or a large region), native SVG elements are layered on top to carry the actual information. None of the overlay elements need to be generated by the image model — they are vector primitives you draw yourself.

38. **Background image + annotation cards with Shape-first leaders** — full-bleed `<image>` + 2–4 small info cards (`<rect rx>` + icon + title + one-line text) placed in the image's calm regions. Point to each subject with a straight `<line>` by default, or an authored native bent/curved Connector when its stock contour fits. Use a custom Bézier leader only when neither can route around the subject faithfully. Card text and leader lines remain editable; image is the scene.

39. **Background image + flow nodes drawn over the scene** — the image is a real or rendered scene (workshop, control room, landscape). On top, connect numbered `<circle>` stops with straight `<line>` segments or exact native bent/curved Connector contours. Use a custom dashed route only when the workflow must follow meaningful scene geometry those shapes cannot express. Each node = number + icon + label. The flow is fully editable; the image is atmosphere.

40. **Background image + floating KPI metric cards** — full-bleed image (often an operations photo) + dark scrim + multiple `<rect>` cards in negative-space regions. Each card = icon + small label + large metric number. Image gives context; cards give the data.

41. **Background image + measurement lines and module tags (engineering overlay)** — used on technical / blueprint / cross-section images. Draw measurement lines with end-caps (`<line>` + perpendicular ticks) spanning a feature, with a centered label box reading dimensions or part names. Add tagged callouts with `<rect>` + monospace text. Reads as engineering drawing markup.

42. **Background image + glassmorphism UI panels** — image is the visual world; on top, draw UI elements (semi-transparent panels, progress arcs, status badges, indicators). Panels use `fill-opacity="0.6–0.8"` + thin light-color strokes; use exact native `arc` / `blockArc` presets when they fit, and custom `A` geometry only for data-defined arcs they cannot express. Looks like a live dashboard floating above the scene.

43. **Background image + native data chart on top** — AI image generation cannot produce accurate data charts. Solution: use an AI-generated dashboard image as **visual reference only** (clearly labeled as such in a caption), and draw the actual chart with native SVG primitives (`<line>` axes, `<path>` series, `<circle>` data points) directly on or next to it. Required marker if exporting: `<!-- chart-plot-area: x_min,y_min,x_max,y_max -->` inside the chart group.

44. **Background image + native network/architecture diagram** — same logic as #43 but for structural diagrams. Image provides atmosphere or visual anchor; the actual nodes, connections, and labels are SVG circles, lines, icons, and text — all editable.

45. **Background image + numbered hotspots with sidebar legend** — small numbered `<circle>` markers placed on the image at points of interest. A sidebar (left or right) lists "1. … 2. … 3. …" with corresponding descriptions.

46. **Background image + bordered "lens" rectangle highlighting a sub-region** — full-bleed image + a bordered `<rect fill="none" stroke="accent" stroke-width="3"/>` framing a sub-region + caption nearby. Frame draws the eye to one detail without occluding the surrounding context.

## Multi-Image Compositions

94. **Embracing arc row (2D substitute for a 3D perspective wall)** — a row of images or cards where the centre element is largest and each step outward shrinks and drops, so the tops trace an arc and the row appears to curve toward the viewer. This is what PowerPoint decks build with 3D rotation (perspective left / right, X-axis 330° / 30°) for logo walls, certificate rows, and photo shelves — and it is reproducible in 2D, which matters because 3D transforms are outside the SVG contract ([`svg-effects.md`](./svg-effects.md) §6.8).

    **Construction**: for element `k` steps from the centre, apply `scale = 0.88ᵏ` and offset `y` downward so every element's *top* edge lands on one shallow arc; keep the horizontal step constant. Mirror the sequence left and right of the centre. Add a soft ground shadow or a reflection fading downward to seat the row. Bottom-aligning instead of top-arcing gives the flatter "shelf" variant.

    The depth cue is entirely **scale + vertical offset + consistent light**; do not reach for skew or a fake 3D tilt, which fail closed on export. Three to seven elements is the working range — beyond that the outermost ones shrink into illegibility.

47. **Small multiples — 3–6 same-kind images in an evenly spaced row** — identical containers, identical caption blocks (title + one line). Not a generic grid: the identical framing *is* the message, because readers compare across panels only when the structure is constant.

48. **Side-by-side comparison (before/after, A/B, then/now)** — two `<image>` of equal size in 50/50 split with thin divider `<line>` and "before" / "after" labels.

49. **Asymmetric collage** — one large `<image>` + 2–3 smaller `<image>` arranged around it; sizes vary, gaps consistent.

50. **Tiled grid (2×2, 2×3, 3×3) with equal cells** — `cell_size = (canvas - total_gap) / cols`; consistent `gap=2–20px`.

51. **Mosaic** — irregular tile sizes packed together with or without thin gaps; each image clipped to its tile's rect.

92. **Split tiling — one parent shape cut into interlocking cells** — the most-used construction in real image-heavy decks, and the counterpart to #82. Take one parent shape (circle, annulus, rounded rect, trapezoid, wave band), lay cutting lines across it (long bars, evenly distributed or fanned at different angles), and split it into cells. Each cell then holds a *different* image. Because every cell comes from one parent, the edges interlock exactly — no gaps, no overlaps, and the group still reads as one object.

    | Parent + cutters | Result |
    |---|---|
    | Circle + 2 crossed bars | Quadrant wheel |
    | Annulus + radial bars | Ring segments |
    | Wave band + vertical bars | Rhythmic strip |
    | Trapezoid + slanted bars | Perspective row |

    **Authoring**: compute each cell's contour and write it as its own `<path>` clip — the geometry is deterministic, so derive the cells rather than eyeballing them. `shape_boolean_svg.py render <svg-file> --operation fragment --source <id> --source <id> --id <result-id>` returns exactly these interlocking regions as separately addressable paths. Give every cell the same stroke (2px, background color) so the cuts read as designed seams.

    **Choosing between #92 and #82 / #100**: different images per cell (#92)
    are peers. One registered source means one edit object (#82) or independent
    same-source objects (#100).

52–53. **Filmstrip / stack** — a sequence of `<image>` with thin consistent gaps: horizontal, equal height and varying widths (**#52**), or vertical, aligned by width with shared annotations down one side (**#53**).

54. **Overlapping image stack** — `<image>` elements with overlapping `x/y` positions; each subsequent one in front (z-order by document order); often combined with slight rotation for layered photo-print look.

55–56. **Diptych / triptych** — two images abutting 50/50, vertical or horizontal (**#55**), or three side-by-side at equal or 2:1:2 widths (**#56**), with an optional thin divider `<line>`. Distinct from #26, where the panels live inside one image file, and from #48, where the pairing carries a before/after argument.

88. **Non-rectangular tessellation (honeycomb, diamond, chevron array)** — a tiled field of hexagons, diamonds, or slanted parallelograms, each cell holding its own image via `clipPath` (#23) and separated by a consistent 2–3px stroke in the background color, which reads as the grid's mortar. The non-rectangular counterpart to #50 / #51.

    **Geometry**: a flat-top hexagon of width `w` and height `h` is `M x+0.25w,y L x+0.75w,y L x+w,y+0.5h L x+0.75w,y+h L x+0.25w,y+h L x,y+0.5h Z`. Tile it by stepping `0.75w` horizontally and offsetting alternate columns by `0.5h` vertically.

    **Leave cells deliberately empty**: fill 1–3 tiles with a flat or gradient deck color instead of a photo. A fully-populated honeycomb reads as a stock template, and the empty cells are where the title and body copy live. Keep the identical stroke on the empty cells so they read as designed rather than as a missing image.

## Imported Deck Patterns (image-led promotional pages)

These patterns come from polished image-text decks where photos define the slide skeleton instead of sitting inside generic cards. Treat them as layout vocabulary for travel, product, venue, hospitality, real-estate, event, and brochure-style decks.

73. **Full-bleed poster image + side title stack** — title stack on the left or lower-left third, no title card; scrim only where the image is busy.

74. **TOC image-navigation cards** — 3–5 vertical image cards, each with a translucent overlay, chapter number, title, one-line summary. A visual preview of the deck, not a text list.

75. **Asymmetric dual-image chapter banner** — one small + one wide image across the upper half; chapter title below, anchored by an oversized section number.

76. **Mid-page image belt with native text inset** — wide image strip through the middle 45–60%, key text inside its calm region, heading above.

77. **Photo mosaic with a text cell** — irregular grid with one cell reserved for copy. The missing photo is the hierarchy; do not fill every slot just because a grid exists.

78. **Ambient banner + evidence photo + text panel** — atmospheric image above, concrete evidence photo below, copy on a tinted side panel. One image sets mood, the other proves it.

79. **Ribbon-header image cards** — 3 columns, colored ribbon or chevron title above each image, prose below.

80. **Side hero image + staggered evidence cards** — full-height image in a side column; 2–4 smaller cards staggered vertically opposite it rather than gridded.

81. **Illustration-as-layout field** — a large vector or cutout illustration acts as the image region and sets spatial rhythm, with text in its calm areas. For when a photo would be too literal but the page still needs image-scale mass.

---

# Part 2 — Modifier Layers

Stack any of these freely on top of a Primary structure. Multiple Modifiers per page is the expected case, not the exception.

## Non-rectangular Image Shapes

20–23. **Basic shape crops** — `<clipPath>` holding one shape, referenced by `<image clip-path="url(#id)"/>`: `<circle>` (**#20**), `<rect rx ry>` (**#21**, `rx` sets roundness), `<ellipse>` (**#22**), `<polygon points>` (**#23**, keep every vertex inside the image's display rect). #24 supersedes all four whenever the contour is curved or organic.

24. **Custom path crop (blob, leaf, silhouette)** — use `<clipPath><path d="…"/></clipPath>` only when circle, ellipse, rounded-rect, and polygonal crops cannot faithfully express the silhouette. PowerPoint export translates the necessary custom contour to `custGeom` and survives roundtrip.

25. **Layered paper-cut stack** — clip each image layer under the image-only contract in [`shared-standards-core.md`](./shared-standards-core.md) §1.2; draw vector layers directly in their final geometry. A small conditional shadow on each layer can create physical separation.

82. **One image shattered across separated shapes (Merge Shapes look)** — clip
one `<image>` with one `<path>` containing disjoint closed subpaths. Size the
image over their union so the scene remains continuous; export yields one
picture with `custGeom`. Use `shape_boolean_svg.py render` `union` / `combine`
for non-trivial contours and obey
[`shared-standards-core.md`](./shared-standards-core.md) §1.2. Distinct from
#24 (one contour), #47–#56 (different sources), and #100 (several pictures).

100. **Same-source addressable crops** — repeat one exact `href` in independent
nested crop wrappers with different source-unit `viewBox` values. They export
as separate native picture objects for editing and Morph while assembling one
registered scene without slice assets. Follow
[`executor-image.md`](./executor-image.md) §1. Unlike #82 this yields several
pictures; unlike #84 registration remains exact.

    **Registration construction**: choose one visible container union
    `U = (ux, uy, uw, uh)` and one source region
    `S = (sx, sy, sw, sh)`. For a container
    `F = (x, y, w, h)`, derive its source-unit crop as
    `Sx = sx + (x-ux)/uw × sw`, `Sy = sy + (y-uy)/uh × sh`,
    `Sw = w/uw × sw`, and `Sh = h/uh × sh`. Use that result as the nested
    wrapper `viewBox`; do not choose each crop by eye and do not apply
    independent `cover`. This makes irregular heights and gaps behave like
    windows cut from one continuous image while keeping every window a native
    picture object.

83. **Panel with a real hole punched through it (Subtract window)** — a solid or tinted panel with a shape-cut opening that reveals the image below, PowerPoint's Merge Shapes 剪除.

    **Geometry**: one `<path>` containing both contours, running in **opposite directions**. Outer clockwise, inner counter-clockwise — e.g. panel `M 80,80 H 1200 V 640 H 80 Z` followed by hole `M 420,220 V 500 H 760 V 220 H 420 Z` (note the second one descends first, reversing the winding). Under nonzero winding the reversed subpath subtracts, producing a true hole, so the effect never needs `fill-rule` and stays inside the [`shared-standards-core.md`](./shared-standards-core.md) §1.2 boundary. Verified end-to-end: both subpaths survive into a single `<a:path>` in the exported `custGeom`. The `subtract` operation of `shape_boolean_svg.py render` emits this contour directly; follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6.

    **Why not #67**: that pattern fakes the opening by laying a background-colored shape on top. It works only over a flat background and silently breaks the moment the page gains a gradient, a texture, or a second image behind the panel. A real hole also lets the underlying image be moved or swapped without recutting the panel.

84. **Deliberately misregistered fragments (Fragment look)** — the inverse of #82. Cut one image into pieces using several `<image>` elements that share the same source, each with its own clip, then **break the alignment on purpose**: offset a few px, rotate 1–3°, or nudge one piece's scale. The eye still assembles one photo, but the seams now read as intentional — misprint, torn paper, glitch.

    Keep the displacement small and consistent in direction; large or random offsets stop reading as a decision and start reading as a rendering bug. The `fragment` operation of `shape_boolean_svg.py render` returns each atomic region as a separately addressable path when the pieces must be individually positioned; follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6.

85. **Subject breaking out of its container** — the subject sits half inside a card / grid cell / color panel and half outside its boundary. Two `<image>` elements from the same file: one clipped to the container (optionally tinted, #31), one clipped to only the escaping region, positioned so the two halves stay in perfect register. Produces depth with no shadow at all.

    Let the *subject* be what escapes, not a corner of background, and break out only once per page — a page where everything escapes has no frame left to break.

26. **Triptych baked into a single wide image** — one wide `<image width=1160 height=334>` whose internal composition already contains 2–3 scenes. Generate the triptych as one image (not three separate calls) when scene-to-scene consistency matters — the model preserves character identity, lighting continuity, and color grading far more reliably when panels are produced together.

## Overlay, Scrim & Vignette Treatments

**Hard rule — visual masking is not SVG `<mask>`**: Masking in a design brief
names the intended appearance only. Realize it with crop/clip geometry,
scrim/overlay shapes, a real cutout path, or a baked-alpha asset; never emit
`<mask>` or `mask="url(...)"`.

> **Default — focal-safe text contrast (may override when the image and treatment demonstrably remain legible).** `preserveAspectRatio="xMidYMid slice"` center-crops whatever the source aspect ratio does not cover, so estimate the crop before placing text. Keep copy clear of the focal subject and maintain readable contrast across its full area. A gradient transition is valid when those conditions hold; use an opaque plateau or solid panel only when the image and softer treatment cannot guarantee them. When subject position is unresolved, prefer the opaque treatment rather than guessing.

27. **Linear gradient scrim for text legibility** — `<linearGradient>` in `<defs>` (set `x1/y1/x2/y2` for direction) + overlay `<rect fill="url(#grad)">`. Most common is top-to-bottom darkening on full-bleed cover images.

28. **Radial gradient vignette** — `<radialGradient cx cy r>` with dark outer stops; overlay `<rect>`. Focuses attention by darkening the periphery.

29. **Two-stop scrim — opaque on text side, transparent on focal side** — `<linearGradient>` with one stop at `stop-opacity="0.9"` and another at `stop-opacity="0"`. Use when text sits on one side and the image's subject on the other.

30–31. **Flat overlay wash** — one `<rect fill-opacity>` over the image: neutral `#000000` / `#FFFFFF` around 0.4 for uniform darkening or lightening, the simplest scrim there is (**#30**), or a deck color at 0.15–0.25 to pull a foreign-looking photo toward the palette without regenerating it (**#31**).

> **Sample the scrim color from the photo itself.** For any gradient scrim over an image (#27, #29, #31, #32, #90), take the solid end's hex from a dominant color *in that image* rather than defaulting to black or a deck color, and slide the gradient stop until the seam between scrim and photo disappears. A black scrim over a warm photo announces itself as a rectangle; a scrim in the photo's own shadow tone reads as part of the picture. This one substitution is the difference between a page that looks masked and one that looks composed.

98. **Grid scrim with per-cell opacity** — instead of one flat or gradient scrim, cover the image with a grid of adjacent rectangles and give each cell a *slightly different* opacity (say 10–40 %, varied irregularly). The photo shows through unevenly, so the overlay reads as texture — panelled glass, a pixel field, a contact sheet — rather than as a sheet of paint. Text sits on the denser cells.

    Keep the variation small and non-repeating: a regular light/dark alternation reads as a checkerboard, and a wide spread reads as broken rendering. Butt the cells exactly (no gaps, no strokes) so the grid is felt rather than drawn. Distinct from #50 / #88, where every cell holds its own image; here one image lies beneath one grid of glass.

99. **Selective desaturation — colour only where it matters** — the whole image is muted while one subject stays in full colour, which fixes the focus of a busy photo without cropping it. Two registered copies: a desaturated (and usually darkened) version filling the frame, and the colour original clipped to just the subject region, sitting exactly on top.

    **Both copies are baked assets** — there is no runtime colour filter on the native route ([`svg-effects.md`](./svg-effects.md) §6.12), so produce the desaturated file with a one-line Pillow `ImageEnhance.Color(img).enhance(0)` pass rather than reaching for `feColorMatrix`. Clip the colour copy along a real edge in the picture (the subject's own contour, per #96) — a rectangular colour patch over a desaturated field reads as an accident.

32. **Multi-stop scrim with hue shift** — three-or-more-stop `<linearGradient>` where stops are different colors (e.g. dark navy → transparent → warm orange). This re-grades the image's color world without regenerating — particularly useful when an AI image came back with the right composition but wrong color temperature.

90. **Full-canvas scrim with shapes cut out of it (the cover / divider formula)** — the single highest-yield formula in this catalog, and the one real decks reuse most: a full-slide `<path>` whose outer contour is the canvas and whose inner subpath(s) are cut out using the opposite-winding rule from #83, laid over a full-bleed image. The scrim mutes the photo everywhere except through the cuts, so one ordinary image becomes a designed page. Three elements total: image, scrim, title.

    **The cut contour** — any of these, all authored as reversed inner subpaths in the same `<path>`:

    | Contour | Reads as |
    |---|---|
    | Wave, arc, ribbon (one soft curve across the page) | Editorial banner / horizon |
    | Freehand closed curve (irregular, hand-drawn) | Organic torn-paper window |
    | An array of hexagons / trapezoids / circles | Rhythmic screen, a window wall |
    | Oversized numeral or letterform | Chapter marker (see caveat) |

    An array of cuts is just several reversed subpaths in the same `d` — the same construction as #82, except here the image shows *through* the holes rather than being clipped *into* the shapes.

    **Paint the scrim** with either a flat light fill at 0.15–0.25 opacity (white over a photo is the reliable default) or, for a directional reveal, a gradient that varies `stop-opacity` rather than color (`1 → 0.8 → 0`), so the image emerges progressively instead of through one hard boundary. Add a 1–2px stroke in the same light color on the cut edge to keep it crisp.

    **Edge thickness**: to make the cut read as a physical opening, apply `feDropShadow` with `dx="0" dy="0"` and a small `stdDeviation` to the scrim path. Per [`svg-effects.md`](./svg-effects.md) §6.4 a zero-offset shadow is classified and exported as a **glow**, not a shadow — so use an accent or light color; black will read as diffuse haze rather than an edge. Never apply it to the `<image>` itself (#36).

    **Numeral / lettering caveat**: cutting *text* out of the scrim needs the glyph as a `<path>` outline, which is not something to author by hand — least of all for CJK. Set the numeral as ordinary `<text>` over the scrim (nearly as strong, fully editable), or pre-render a knocked-out numeral as an RGBA PNG (#68). Do not approximate glyph outlines.

    **Motion pairing**: the scrim stays fixed while the image beneath drifts slowly (a 4–10s linear path, left, starting with the previous animation) — the cuts then behave like windows onto a moving world. That is an animation-stage decision, not page design; see [`animations.md`](./animations.md). It pairs with this pattern more often than with any other.

97. **Frosted-glass panel over the photo** — a legibility panel that is neither a flat scrim (#30) nor a full blur: a region of the image itself, blurred and lightened, sitting under the text while the rest of the photo stays sharp. It keeps the photo's color and composition visible through the panel, which a solid scrim destroys.

    **Build it from a baked asset** — runtime blur does not survive native export ([#34](#), [`svg-effects.md`](./svg-effects.md) §6.12). Produce a blurred copy of the source (a Pillow `GaussianBlur` at a large radius, plus a brightness lift), then place that copy clipped to the panel contour and registered to the same position as the base image, so the blur lines up exactly with what is behind it. Add a thin light stroke and, if the style wants it, a slight lightening overlay.

    The panel must stay in register with the base photo; a frosted panel showing a *different* part of the scene is the classic tell. Pair with #95 when the panel should also carry a floating edge.

33. **Radial spotlight overlay — clear region surrounded by darkness** — cover the canvas with `<rect>` filled by a `<radialGradient>` whose inner stop is fully transparent and outer stop is opaque dark. Reads as a flashlight beam on the focal area. Use sparingly — it kills everything outside the spotlight.

34. **Gaussian-blur backdrop** — blur the background in the source image, then layer sharp SVG content above it. Native filter export maps the supported blur graph to a glow/shadow effect; it does not preserve a blurred-image backdrop.

35. **Duotone treatment** — two-color mapping of a photograph (e.g. deep navy shadows + warm cream highlights). Bake it into the source image; the native PPT route does not support a runtime duotone filter chain.

36. **Drop shadow under image panel** — `<filter><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.10"/></filter>` applied to the image panel's backing `<rect>`. Standard depth lift; filters do not apply directly to `<image>` under the project contract.

37. **Inner / outer glow on overlay shape** — `<filter><feGaussianBlur stdDeviation="6"/><feMerge/></filter>` on a shape, or simply a slightly larger blurred `<rect>` underneath the target.

## Image as Texture / Atmosphere

57 · 60 · 61. **Image pushed into the background** — the same move at three intensities: a full-bleed texture wash under the page (**#57**, overlay `<rect fill="bg-color" fill-opacity="0.7–0.85"/>`), low-contrast ambient atmosphere that is seen but never read (**#60**), or a watermark sitting behind body copy (**#61**). Suppress it with an overlay `<rect>` or a pre-dimmed asset — never a runtime filter.

58. **Image fragment as decorative corner element** — small `<image>` (often with `clipPath`) placed in one corner; not the focus, just visual seasoning.

59. **Image as horizontal divider band** — narrow `<image height=80–150>` placed between two text sections instead of a `<line>` divider.

## Special Techniques

62. **Same image, two references — full view + zoom-callout** — reference the same image file twice in two `<image>` elements: one shows the full scene at normal size; the second uses `clipPath` (circle or rectangle) plus a larger display size to "zoom into" a sub-region. Connect them with a straight `<line>` or an exact native bent/curved Connector contour; use a custom Bézier only when the leader must avoid meaningful image content. Ring the zoom with a `<circle stroke>` so it reads as a magnifying lens. No special asset needed — the zoom effect comes from same-source-different-display.

63. **Transparent PNG sticker / cutout** — an RGBA PNG placed via plain `<image>`; the transparency lives in the file, so no `clipPath` is needed. Sources: `slice_images.py --alpha` output (see [image-generator.md](./image-generator.md) §4.3), an AI backend with native transparent output, or a user asset.

    Never box a cutout in a rectangle — that throws away the only thing it offers. Combine with #4 (bleed off the edge), #58 (corner fragment), #66 (fade into background), #69 (slight rotation), or #49 (asymmetric collage).

64. **Image with embedded text rendered by the AI** — text becomes part of the artwork: decorative lettering, artistic wordmark, hand-lettered keyword. Prompt with explicit text content — name the exact characters literally. Use for text that is part of the artwork and will not change. Authoritative titles and anything that must stay correct or editable go in the SVG `<text>` layer (#65).

65. **Image with NO text — labels added as native SVG** — generate the image with explicit "no text, no letters, no numbers, no signs" instruction (`text_policy: none`), then place all labels as `<text>` overlays. The right call when labels will be reworded, must stay exact, or carry data that must stay editable — pair with `#64` when stable visual identifiers (axis labels, subplot letters, unit symbols) belong inside the image instead.

66. **Image fading into the solid background** — soften the image's edge into the deck's background color via a `<linearGradient>` overlay whose end-stop matches the background hex exactly. The image's rectangular boundary disappears, producing seamless integration.

67. **Image with knock-out / cut-out shape** — overlay a shape filled with the background color or another image, creating the impression of a hole punched through the underlying image.

68. **Text-as-mask over image** — letterforms revealing image through them. Under the canonical SVG compatibility boundary in [`shared-standards-core.md`](./shared-standards-core.md), realize this pattern as a pre-rendered image rather than a runtime effect. Prompt for "large lettering revealing the underlying scene through letterforms" and treat the result as a fixed artistic choice.

69. **Image rotated at a slight angle for editorial feel** — `transform="rotate(angle cx cy)"` on the `<image>` or its container `<g>`; 2–6 degrees typical. Adds dynamism without breaking layout.

70–71. **Frames** — a single `<rect fill="none" stroke="#color" stroke-width="2–6"/>` at the image edge (**#70**), or several nested outlines at slightly different sizes for a photo-print look (**#71**). When the image was cut to a non-rectangular contour, use #86 instead so the frame follows the cut.

72. **Baked-alpha image-to-image blend** — a genuinely soft blend between two images requires a precomposited bitmap or source images with baked alpha. An ordinary gradient overlay can conceal the join only when both images fade through the same solid bridge color; it is not a per-pixel mask and cannot blend arbitrary imagery.

95. **Shape filled with the page background itself** — the most-used trick in real decks and the one that has no obvious SVG name. A shape is painted not with a color but with *the page's own background, sampled at the shape's own position*, so it becomes invisible against the page while still being a real object that can carry an edge treatment.

    **SVG form**: give the shape the same `<image>` as the page background, positioned in root coordinates exactly as the background is, and clip it to the shape contour (§1.2). Because the fill stays registered to the page rather than to the shape, the object reads as a hole in whatever is above it.

    **Registration boundary**: the sampled shape and page background must remain fixed in the same root coordinates. Moving, resizing, rotating, or morphing the sampled shape moves its pixels with it and exposes the seam; animate independent content above or below the stationary shape instead.

    Three things it buys you, all of which otherwise require a second asset:
    - **A cut that keeps the scene continuous** — the shape "removes" a foreground panel and shows the background through it, with no seam even over a photo or gradient.
    - **A stationary conceal/reveal patch** — it can cover one fixed region while independent content enters or leaves above or below it.
    - **Edge-only forms** — the shape disappears but its stroke, glow, or shadow remains, giving a floating outline that appears cut into the page.

    Distinct from #83 (a panel with a real hole) and #90 (a scrim with cuts): those remove paint, this one *impersonates* the background. Reach for it when the thing above must stay a solid object.

96. **Cutout subject re-laid over its own photo** — the mechanism behind every "subject escapes the frame" page (#85), and worth stating on its own because it is a two-asset technique: keep the original photo as the background layer, and place a background-removed PNG of its subject on top, in perfect register.

    Once the subject exists as a free-floating layer, it can overlap anything drawn between the two copies: a title the subject stands in front of, a color panel it steps out of, a shape frame it breaks through, a grid line it crosses. The base photo can be tinted, desaturated, blurred (baked), or scrimmed as hard as the layout needs, because the sharp subject on top is what the eye reads.

    Register is everything — the cutout must sit exactly where the subject sits in the base image; a few px of drift reads as a printing error. Keep the cutout's own edge clean rather than adding a stroke, unless the design calls for the sticker look of #63.

89. **Same image twice — sharp cutout over a receded full-bleed copy** — the single best answer to "the photo is too narrow / too short for this canvas, and stretching distorts the subject". Reference the same file twice: the bottom copy fills the whole canvas (or panel) and is pushed back; the top copy is clipped to a shape (#82, #24, a slanted band, a folded contour) at native proportions and stays sharp. The subject reads at full fidelity while the background extends the frame to any aspect ratio — no stretching, no letterbox bars, no second asset.

    **Recede the bottom copy with what survives export**: a color-tinted or darkened overlay `<rect>` (#30 / #31) at 0.5–0.8, or a desaturated / lowered-brightness variant of the file. **Blur does not survive** — per #34 the native route does not preserve a blurred-image backdrop, so if the design depends on blur it must be baked into a second image file (a one-line Pillow `GaussianBlur` pass over the original is enough); never rely on a filter at export time. Keep both copies in register — same center, same crop logic — or the trick reads as two unrelated photos.

86. **Contour echo — the clip path reused as a stroke** — after clipping an image (#20–#25, #82, #83), reuse the *same* `d` as a `<path fill="none" stroke="accent"/>`, drawn slightly larger or offset a few px. The outline repeats the cut geometry instead of boxing it in a rectangle, which is what #70 / #71 do. One extra element, no new asset. Offset it in a single consistent direction across the page; an echo on every side reads as a border, not an echo.

91. **Faceted gradients for folded / dimensional form (origami, ribbon, folded band)** — build a folded or faceted object from several adjacent `<path>` facets, then give each facet its own `<linearGradient>` whose direction and lightness differ from its neighbours — one face catching light, the next in shade. The fold is created by the *lightness break between adjacent facets*, not by any shadow effect, so it survives export intact as ordinary shapes.

    Keep every facet on one hue and vary only lightness (a white → light-grey → white ramp across three facets already reads as a crease), remove all strokes so the facets meet seamlessly, and keep the light direction consistent across the whole object. Combine with #82 by using the assembled facet outline as the clip contour, which puts a photo inside the folded form. Do not reach for `<filter>` shadows to fake depth here — [`svg-effects.md`](./svg-effects.md) owns effect limits, and the gradient break is both cheaper and more reliable.

87. **One image panned across consecutive pages** — a single wide image referenced by 2–4 consecutive slides, each showing a different horizontal segment (same `<image>` file and container geometry per page, only `x` shifts). Static on its own, it makes the deck read as one continuous scene; the audience recognizes the place before reading a word.

    **Motion contract**: keep the same image file and compatible direct-root group/container geometry on every participating page. Exporting with `-t morph` alone leaves object matching to PowerPoint's heuristic; stable ids and compatible geometry improve the chance of a camera pan but do not prove it. When the pan must be deterministic, run the custom motion stage and declare the adjacent objects in `animations.json` `morph.pairs` ([`animations.md`](./animations.md) §2.1); the pair may bind different source/destination ids while preserving compatible object kinds. Changing the file or endpoint geometry still changes the visual action and may reduce an unpaired Morph to a cross-fade.

---

## Composition Guidance

A page is built by layering. Pick one or more **Primary Structures** (Part 1) as the page's bones, then add any number of **Modifier Layers** (Part 2) for finish. Both stack — the question on each page is "is the next layer still earning its place", not "have I exceeded a quota".

**Cross-primary combinations are encouraged.** A side-by-side comparison (#48) where each side is annotated with Shape-first leader cards (#38) is one page, not a violation. A 3×3 grid (#9) whose center cell is upgraded to an image-as-canvas with KPI overlay (#40) reads as one composition. The old reflex "one primary per page" tends to under-use the catalog — combine when the page asks for it.

**Reference — motion-aware layer vocabulary, not a constraint**: When focus, comparison, evidence, or reveal order serves the page, the Image-as-Canvas + Native Overlay and Multi-Image Compositions families may expose independently meaningful visible units. `#62` can separate full view from same-source detail; `#63` can isolate a cutout foreground; `#74` / `#77` / `#78` / `#80` can separate image-led navigation or evidence units. These are composition layers, not effect assignments, and no pattern owes animation. `#72` is a static image blend in the fully revealed page, not a PowerPoint page transition.

**Modifier stacking pattern that works in practice** — observed on real content pages combining one Primary with four Modifiers:

- one Primary from Part 1 (e.g. #48 side-by-side comparison)
- `#21` rounded-rectangle clipPath on the image (rx=6 or circle)
- `#27` top-edge linearGradient in the deck's accent color, opacity 0.55 → 0
- `#66` bottom-edge linearGradient fading to background color, opacity 0 → 0.95
- small color-block badge + reversed-out label replacing any opaque color bar that would otherwise sit over the image

Combine freely. The "AI-default" failure mode is the opposite: defaulting to bare #2 / #3 (left/right split) with no Modifier at all.

**Reference — image-led promotional deck moves (not a constraint)**:

| Page intent | Pattern candidates |
|---|---|
| Cover / ending with strong atmosphere | `#73` + `#27` / `#30` only if contrast needs it |
| Visual table of contents | `#74` + `#30` / `#31` |
| Chapter divider | `#75` |
| Venue / destination overview | `#76` or `#78` |
| Many product/place photos | `#77` or `#50` when equality is the message |
| Service / feature comparison | `#79` |
| Benefits with one dominant proof image | `#80` |
| Light promotional page without photos | `#81` |

**Reference — not a constraint**: before adding another photo, consider whether one prepared image plus #82–#100 can express the idea more clearly. Registration and prepared-asset boundaries remain mandatory when the chosen technique depends on them.

**Cross-page through-line (recurring motif).** The patterns above are per-page, but a deck reads as *designed* when one illustration motif family recurs across pages—a cover anchor, section dividers repeating the motif (`#75`), and small `#63` spots threaded through the body. Keep one family (shared rendering / locked deck colors / subject world), vary scale and placement, and never turn recurrence into a quota.

## Hard Constraints

- Page chrome, body copy, captions, and data values that must remain exact or editable stay in SVG. Stable figure-internal identifiers, axis/unit labels, panel markers, or lettering that is deliberately part of the artwork may be image-owned under `text_policy: embedded`, regardless of script or length.
- Project-wide SVG compatibility rules start at [`shared-standards-core.md`](./shared-standards-core.md),
  whose routing table names each conditional owner. This catalog neither
  restates nor relaxes that contract; each pattern records only its
  scenario-specific rendering choice.

---

For sizing math (calculating container dimensions from image aspect ratio when using side-by-side intent), see [`image-layout-spec.md`](image-layout-spec.md). This file is the design vocabulary; that file is the dimension calculator.
