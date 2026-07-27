# Image-Text Layout Patterns

A vocabulary registry of ways images can be placed on a slide. The point of this file is to **expand the mental list of options** so that when you reach for an image layout, you do not default to the same three patterns (left/right, top/bottom, full-bleed cover).

Every entry has a name plus a short technical hint. Common techniques get a single line. Less obvious or easily forgotten techniques get a short paragraph — not a full tutorial, but enough that a model unfamiliar with the project can implement it without guessing. This is a registry, not a teaching document; no use-case prescriptions, no decision tables.

> **Numbers are stable identifiers, not sequence.** The file is split into **Part 1 — Primary Structures** (#1–#19, #38–#56, #73–#81, #88) and **Part 2 — Modifier Layers** (#20–#37, #57–#72, #82–#87, #89–#91). Numbers jump within each Part because Primary structures were grouped first; existing references to `#38`, `#48`, etc. anywhere in the project still resolve correctly.

---

## Core Principle — Two Layers

Almost every pattern below is an instance of one underlying split:

> **The image carries atmosphere, world-building, emotional weight. Native SVG shapes carry information, data, editable text.**

This is the single most underused move in image-heavy decks. The default reflex is to place image and text in adjacent rectangles. The far more powerful move — especially for content-rich pages — is to let the image **be the canvas** (often full-bleed) and draw native vector elements (annotation cards, flow nodes, KPI tiles, leader lines, network diagrams, dashboards) directly on top.

Anything that must be editable, numerically accurate, contain Chinese, or be styled to the deck's exact palette belongs in the SVG layer regardless of what the image looks like underneath.

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

38. **Background image + annotation cards with bezier leader lines** — full-bleed `<image>` + 2–4 small info cards (`<rect rx>` + icon + title + one-line text) placed in the image's calm regions. From each card, draw a bezier `<path>` ending in a `marker-end` arrow that points to the specific object in the image being annotated. Card text and leader lines are editable; image is the scene.

39. **Background image + flow nodes drawn over the scene** — the image is a real or rendered scene (workshop, control room, landscape). On top, draw a dashed `<path>` route that traces a workflow through the scene, with numbered `<circle>` nodes at each stop. Each node = number + icon + label. The flow is fully editable; the image is atmosphere.

40. **Background image + floating KPI metric cards** — full-bleed image (often an operations photo) + dark scrim + multiple `<rect>` cards in negative-space regions. Each card = icon + small label + large metric number. Image gives context; cards give the data.

41. **Background image + measurement lines and module tags (engineering overlay)** — used on technical / blueprint / cross-section images. Draw measurement lines with end-caps (`<line>` + perpendicular ticks) spanning a feature, with a centered label box reading dimensions or part names. Add tagged callouts with `<rect>` + monospace text. Reads as engineering drawing markup.

42. **Background image + glassmorphism UI panels** — image is the visual world; on top, draw UI elements (semi-transparent panels, progress arcs, status badges, indicators). Panels use `fill-opacity="0.6–0.8"` + thin light-color strokes; arcs via `<path d="…A…">`. Looks like a live dashboard floating above the scene.

43. **Background image + native data chart on top** — AI image generation cannot produce accurate data charts. Solution: use an AI-generated dashboard image as **visual reference only** (clearly labeled as such in a caption), and draw the actual chart with native SVG primitives (`<line>` axes, `<path>` series, `<circle>` data points) directly on or next to it. Required marker if exporting: `<!-- chart-plot-area: x_min,y_min,x_max,y_max -->` inside the chart group.

44. **Background image + native network/architecture diagram** — same logic as #43 but for structural diagrams. Image provides atmosphere or visual anchor; the actual nodes, connections, and labels are SVG circles, lines, icons, and text — all editable.

45. **Background image + numbered hotspots with sidebar legend** — small numbered `<circle>` markers placed on the image at points of interest. A sidebar (left or right) lists "1. … 2. … 3. …" with corresponding descriptions.

46. **Background image + bordered "lens" rectangle highlighting a sub-region** — full-bleed image + a bordered `<rect fill="none" stroke="accent" stroke-width="3"/>` framing a sub-region + caption nearby. Frame draws the eye to one detail without occluding the surrounding context.

## Multi-Image Compositions

47. **Small multiples — 3–6 same-kind images in an evenly spaced row** — identical containers, identical caption blocks (title + one line). Not a generic grid: the identical framing *is* the message, because readers compare across panels only when the structure is constant.

48. **Side-by-side comparison (before/after, A/B, then/now)** — two `<image>` of equal size in 50/50 split with thin divider `<line>` and "before" / "after" labels.

49. **Asymmetric collage** — one large `<image>` + 2–3 smaller `<image>` arranged around it; sizes vary, gaps consistent.

50. **Tiled grid (2×2, 2×3, 3×3) with equal cells** — `cell_size = (canvas - total_gap) / cols`; consistent `gap=2–20px`.

51. **Mosaic** — irregular tile sizes packed together with or without thin gaps; each image clipped to its tile's rect.

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

24. **Custom path crop (blob, arrow, leaf, silhouette)** — `<clipPath><path d="…"/></clipPath>`; allows any curved or organic shape. PowerPoint export translates this to `custGeom` and survives roundtrip.

25. **Layered paper-cut stack** — clip each image layer under the image-only contract in [`shared-standards-core.md`](./shared-standards-core.md) §1.2; draw vector layers directly in their final geometry. A small conditional shadow on each layer can create physical separation.

82. **One image shattered across separated shapes (Merge Shapes look)** — a *single* `<image>` clipped by **one `<path>` whose `d` contains several disjoint subpaths** (`M … Z M … Z`), so one photo appears inside several detached containers — staggered rounded slices, a gapped 2×2 grid, a rotated cross. This is the SVG equivalent of PowerPoint's Merge Shapes 结合 → 相交, and export maps it to one picture with `custGeom`.

    **Geometry**: write each container as its own subpath in one `d`. A rounded rect is `M x+r,y H x+w-r A r,r 0 0 1 x+w,y+r V y+h-r A r,r 0 0 1 x+w-r,y+h H x+r A r,r 0 0 1 x,y+h-r V y+r A r,r 0 0 1 x+r,y Z`; repeat per container, all in the same `<path>`. Keep the subpaths disjoint so no winding rule is ever needed.

    **The one thing that makes or breaks it — registration**: place the `<image>` over the *union bounding box* of every subpath (not one image per shape), sized with `preserveAspectRatio="xMidYMid slice"`. The photo then runs continuously *behind* the containers and the gaps read as cuts through one scene. Give each container a different image and it instantly collapses into an ordinary tile grid (#50 / #51) — the continuity is the entire design, not the shapes.

    Distinct from #24 (one connected contour) and #47–#56 (every cell its own image). For non-trivial contours take the `d` from `shape_boolean_svg.py union` / `combine` (see [`native-shape-authoring.md`](./native-shape-authoring.md)) instead of deriving it by hand. Clip-shape constraints — one direct shape child, no `fill-rule` / `clip-rule`, `<image>` targets only — are owned by [`shared-standards-core.md`](./shared-standards-core.md) §1.2.

83. **Panel with a real hole punched through it (Subtract window)** — a solid or tinted panel with a shape-cut opening that reveals the image below, PowerPoint's Merge Shapes 剪除.

    **Geometry**: one `<path>` containing both contours, running in **opposite directions**. Outer clockwise, inner counter-clockwise — e.g. panel `M 80,80 H 1200 V 640 H 80 Z` followed by hole `M 420,220 V 500 H 760 V 220 H 420 Z` (note the second one descends first, reversing the winding). Under nonzero winding the reversed subpath subtracts, producing a true hole, so the effect never needs `fill-rule` and stays inside the [`shared-standards-core.md`](./shared-standards-core.md) §1.2 boundary. Verified end-to-end: both subpaths survive into a single `<a:path>` in the exported `custGeom`. `shape_boolean_svg.py subtract` emits this contour directly.

    **Why not #67**: that pattern fakes the opening by laying a background-colored shape on top. It works only over a flat background and silently breaks the moment the page gains a gradient, a texture, or a second image behind the panel. A real hole also lets the underlying image be moved or swapped without recutting the panel.

84. **Deliberately misregistered fragments (Fragment look)** — the inverse of #82. Cut one image into pieces using several `<image>` elements that share the same source, each with its own clip, then **break the alignment on purpose**: offset a few px, rotate 1–3°, or nudge one piece's scale. The eye still assembles one photo, but the seams now read as intentional — misprint, torn paper, glitch.

    Keep the displacement small and consistent in direction; large or random offsets stop reading as a decision and start reading as a rendering bug. `shape_boolean_svg.py fragment` returns each atomic region as a separately addressable path when the pieces must be individually positioned.

85. **Subject breaking out of its container** — the subject sits half inside a card / grid cell / color panel and half outside its boundary. Two `<image>` elements from the same file: one clipped to the container (optionally tinted, #31), one clipped to only the escaping region, positioned so the two halves stay in perfect register. Produces depth with no shadow at all.

    Let the *subject* be what escapes, not a corner of background, and break out only once per page — a page where everything escapes has no frame left to break.

26. **Triptych baked into a single wide image** — one wide `<image width=1160 height=334>` whose internal composition already contains 2–3 scenes. Generate the triptych as one image (not three separate calls) when scene-to-scene consistency matters — the model preserves character identity, lighting continuity, and color grading far more reliably when panels are produced together.

## Overlay & Masking Treatments

> **Crop displacement (HARD rule for text over images).** `preserveAspectRatio="xMidYMid slice"` center-crops whatever the source aspect ratio does not cover — when source and display aspects differ, the subject can land under the text column even if the prompt asked for it on the "focal side". Before layering text on a slice-cropped image: estimate the crop from the aspect-ratio difference, and keep the **entire text column on the scrim's opaque plateau** — text must never start inside a gradient's transition zone. When the subject position is unverified, fall back to an opaque treatment (`#30` at high opacity, or a solid panel) instead of a two-stop scrim (`#29`).

27. **Linear gradient mask for text legibility** — `<linearGradient>` in `<defs>` (set `x1/y1/x2/y2` for direction) + overlay `<rect fill="url(#grad)">`. Most common is top-to-bottom darkening on full-bleed cover images.

28. **Radial gradient vignette** — `<radialGradient cx cy r>` with dark outer stops; overlay `<rect>`. Focuses attention by darkening the periphery.

29. **Two-stop scrim — opaque on text side, transparent on focal side** — `<linearGradient>` with one stop at `stop-opacity="0.9"` and another at `stop-opacity="0"`. Use when text sits on one side and the image's subject on the other.

30–31. **Flat overlay wash** — one `<rect fill-opacity>` over the image: neutral `#000` / `#fff` around 0.4 for uniform darkening or lightening, the simplest scrim there is (**#30**), or a deck color at 0.15–0.25 to pull a foreign-looking photo toward the palette without regenerating it (**#31**).

32. **Multi-stop scrim with hue shift** — three-or-more-stop `<linearGradient>` where stops are different colors (e.g. dark navy → transparent → warm orange). This re-grades the image's color world without regenerating — particularly useful when an AI image came back with the right composition but wrong color temperature.

90. **Full-canvas scrim with a shape cut out of it (chapter-page formula)** — a full-slide `<path>` whose outer contour is the canvas and whose inner subpath is a wave, arc, ribbon, or oversized numeral, cut using the opposite-winding rule from #83. Fill the scrim with a gradient whose stops vary `stop-opacity` (e.g. `1 → 0.8 → 0`) rather than color, so the underlying image emerges progressively across the page instead of showing through one hard hole. Add a 1–2px light stroke on the cut edge to keep the boundary crisp. This is the most reliable chapter/divider formula in the catalog: one image, one scrim, one numeral.

    **Numeral / lettering caveat**: cutting *text* out of the scrim requires the glyph as a `<path>` outline, which is not something to author by hand — least of all for CJK. For a chapter number, either set the numeral as ordinary `<text>` on top of the scrim (nearly as strong, fully editable), or pre-render the knocked-out numeral as an RGBA PNG (#68). Do not attempt to approximate glyph outlines.

33. **Spotlight mask — clear region surrounded by darkness** — cover the canvas with `<rect>` filled by a `<radialGradient>` whose inner stop is fully transparent and outer stop is opaque dark. Reads as a flashlight beam on the focal area. Use sparingly — it kills everything outside the spotlight.

34. **Gaussian-blur backdrop** — blur the background in the source image, then layer sharp SVG content above it. Native filter export maps the supported blur graph to a glow/shadow effect; it does not preserve a blurred-image backdrop.

35. **Duotone treatment** — two-color mapping of a photograph (e.g. deep navy shadows + warm cream highlights). Bake it into the source image; the native PPT route does not support a runtime duotone filter chain.

36. **Drop shadow under image panel** — `<filter><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.10"/></filter>` applied to the image panel's backing `<rect>`. Standard depth lift; filters do not apply directly to `<image>` under the project contract.

37. **Inner / outer glow on overlay shape** — `<filter><feGaussianBlur stdDeviation="6"/><feMerge/></filter>` on a shape, or simply a slightly larger blurred `<rect>` underneath the target.

## Image as Texture / Atmosphere

57 · 60 · 61. **Image pushed into the background** — the same move at three intensities: a full-bleed texture wash under the page (**#57**, overlay `<rect fill="bg-color" fill-opacity="0.7–0.85"/>`), low-contrast ambient atmosphere that is seen but never read (**#60**), or a watermark sitting behind body copy (**#61**). Suppress it with an overlay `<rect>` or a pre-dimmed asset — never a runtime filter.

58. **Image fragment as decorative corner element** — small `<image>` (often with `clipPath`) placed in one corner; not the focus, just visual seasoning.

59. **Image as horizontal divider band** — narrow `<image height=80–150>` placed between two text sections instead of a `<line>` divider.

## Special Techniques

62. **Same image, two references — full view + zoom-callout** — reference the same image file twice in two `<image>` elements: one shows the full scene at normal size; the second uses `clipPath` (circle or rectangle) plus a larger display size to "zoom into" a sub-region. Connect them with a bezier `<path>` ending in `marker-end`; ring the zoom with a `<circle stroke>` so it reads as a magnifying lens. No special asset needed — the zoom effect comes from same-source-different-display.

63. **Transparent PNG sticker / cutout** — an RGBA PNG placed via plain `<image>`; the transparency lives in the file, so no `clipPath` is needed. Sources: `slice_images.py --alpha` output (see [image-generator.md](./image-generator.md) §4.3), an AI backend with native transparent output, or a user asset.

    Never box a cutout in a rectangle — that throws away the only thing it offers. Combine with #4 (bleed off the edge), #58 (corner fragment), #66 (fade into background), #69 (slight rotation), or #49 (asymmetric collage).

64. **Image with embedded text rendered by the AI** — text becomes part of the artwork: decorative lettering, designed title, hand-lettered keyword. Prompt with explicit text content — name the exact characters literally. Use for text that is part of the artwork and will not change. Anything that must be correct or editable goes in the SVG `<text>` layer (#65).

65. **Image with NO text — labels added as native SVG** — generate the image with explicit "no text, no letters, no numbers, no signs" instruction (`text_policy: none`), then place all labels as `<text>` overlays. The right call when labels will be reworded, must stay exact, or carry data that must stay editable — pair with `#64` when stable visual identifiers (axis labels, subplot letters, unit symbols) belong inside the image instead.

66. **Image fading into the solid background** — soften the image's edge into the deck's background color via a `<linearGradient>` overlay whose end-stop matches the background hex exactly. The image's rectangular boundary disappears, producing seamless integration.

67. **Image with knock-out / cut-out shape** — overlay a shape filled with the background color or another image, creating the impression of a hole punched through the underlying image.

68. **Text-as-mask over image** — letterforms revealing image through them. Under the canonical SVG compatibility boundary in [`shared-standards-core.md`](./shared-standards-core.md), realize this pattern as a pre-rendered image rather than a runtime effect. Prompt for "large lettering revealing the underlying scene through letterforms" and treat the result as a fixed artistic choice.

69. **Image rotated at a slight angle for editorial feel** — `transform="rotate(angle cx cy)"` on the `<image>` or its container `<g>`; 2–6 degrees typical. Adds dynamism without breaking layout.

70–71. **Frames** — a single `<rect fill="none" stroke="#color" stroke-width="2–6"/>` at the image edge (**#70**), or several nested outlines at slightly different sizes for a photo-print look (**#71**). When the image was cut to a non-rectangular contour, use #86 instead so the frame follows the cut.

72. **Image-to-image transition / merge** — two `<image>` elements with overlapping regions, one or both with gradient masks (from group C) creating a soft blend between them.

89. **Same image twice — sharp cutout over a receded full-bleed copy** — the single best answer to "the photo is too narrow / too short for this canvas, and stretching distorts the subject". Reference the same file twice: the bottom copy fills the whole canvas (or panel) and is pushed back; the top copy is clipped to a shape (#82, #24, a slanted band, a folded contour) at native proportions and stays sharp. The subject reads at full fidelity while the background extends the frame to any aspect ratio — no stretching, no letterbox bars, no second asset.

    **Recede the bottom copy with what survives export**: a color-tinted or darkened overlay `<rect>` (#30 / #31) at 0.5–0.8, or a desaturated / lowered-brightness variant of the file. **Blur does not survive** — per #34 the native route does not preserve a blurred-image backdrop, so if the design depends on blur it must be baked into a second image file (a one-line Pillow `GaussianBlur` pass over the original is enough); never rely on a filter at export time. Keep both copies in register — same center, same crop logic — or the trick reads as two unrelated photos.

86. **Contour echo — the clip path reused as a stroke** — after clipping an image (#20–#25, #82, #83), reuse the *same* `d` as a `<path fill="none" stroke="accent"/>`, drawn slightly larger or offset a few px. The outline repeats the cut geometry instead of boxing it in a rectangle, which is what #70 / #71 do. One extra element, no new asset. Offset it in a single consistent direction across the page; an echo on every side reads as a border, not an echo.

91. **Faceted gradients for folded / dimensional form (origami, ribbon, folded band)** — build a folded or faceted object from several adjacent `<path>` facets, then give each facet its own `<linearGradient>` whose direction and lightness differ from its neighbours — one face catching light, the next in shade. The fold is created by the *lightness break between adjacent facets*, not by any shadow effect, so it survives export intact as ordinary shapes.

    Keep every facet on one hue and vary only lightness (a white → light-grey → white ramp across three facets already reads as a crease), remove all strokes so the facets meet seamlessly, and keep the light direction consistent across the whole object. Combine with #82 by using the assembled facet outline as the clip contour, which puts a photo inside the folded form. Do not reach for `<filter>` shadows to fake depth here — [`svg-effects.md`](./svg-effects.md) owns effect limits, and the gradient break is both cheaper and more reliable.

87. **One image panned across consecutive pages** — a single wide image referenced by 2–4 consecutive slides, each showing a different horizontal segment (same `<image>` file and container geometry per page, only `x` shifts). Static on its own, it makes the deck read as one continuous scene; the audience recognizes the place before reading a word.

    **To make it actually move, the pages must be morph-compatible**: keep the same image file, the same container size, and the same group `id` on every participating page, then export with `-t morph` ([`animations.md`](./animations.md)). Morph then treats it as one object and slides it — the flip becomes a camera pan. Change the filename or the container dimensions between pages and morph stops matching the object, silently degrading to a cross-fade with none of the effect. Nothing else in the deck needs to know about this; it is a page-authoring decision plus one export flag.

---

## Composition Guidance

A page is built by layering. Pick one or more **Primary Structures** (Part 1) as the page's bones, then add any number of **Modifier Layers** (Part 2) for finish. Both stack — the question on each page is "is the next layer still earning its place", not "have I exceeded a quota".

**Cross-primary combinations are encouraged.** A side-by-side comparison (#48) where each side is annotated with bezier-leader cards (#38) is one page, not a violation. A 3×3 grid (#9) whose center cell is upgraded to an image-as-canvas with KPI overlay (#40) reads as one composition. The old reflex "one primary per page" tends to under-use the catalog — combine when the page asks for it.

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

**The boolean-geometry family (#82–#91)** is where a deck stops looking like slides and starts looking designed. Nearly all of them are one `<image>` plus geometry — no extra assets, no generation cost — and they are the SVG equivalents of what PowerPoint users reach for under Merge Shapes. Their shared discipline is registration: the image stays anchored to the *union* of the containers so the scene reads as continuous (#82, #85, #87, #89), and the one pattern that deliberately breaks registration (#84) only works because the others establish the expectation. Reach here before adding another photo to the page.

**When the supplied image does not fit the canvas**, the answer is #89, not stretching and not letterboxing: the same file placed twice, receded behind and sharp in front. This is the single most common image problem in real decks and it has a purely geometric solution.

**Skip-detection signal** — if every page's `Layout pattern` column resolves to bare #2 / #3 / #5 / #6 with no Modifier ids, the catalog was not consulted. Re-read and reconsider.

**Cross-page through-line (recurring motif).** The patterns above are per-page, but a deck reads as *designed* when one illustration motif family recurs across pages—a cover anchor, section dividers repeating the motif (`#75`), and small `#63` spots threaded through the body. Keep one family (shared rendering / locked deck colors / subject world), vary scale and placement, and never turn recurrence into a quota.

## Hard Constraints

- Long body copy, data points, numeric labels, and Chinese text always go in the SVG layer — never baked into the image.
- Project-wide SVG compatibility rules start at [`shared-standards-core.md`](./shared-standards-core.md),
  whose routing table names each conditional owner. This catalog neither
  restates nor relaxes that contract; each pattern records only its
  scenario-specific rendering choice.

---

For sizing math (calculating container dimensions from image aspect ratio when using side-by-side intent), see [`image-layout-spec.md`](image-layout-spec.md). This file is the design vocabulary; that file is the dimension calculator.
