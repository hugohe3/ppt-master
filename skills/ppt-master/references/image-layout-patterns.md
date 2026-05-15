# Image-Text Layout Patterns

A vocabulary registry of ways images can be placed on a slide. The point of this file is to **expand the mental list of options** so that when you reach for an image layout, you do not default to the same three patterns (left/right, top/bottom, full-bleed cover).

Every entry has a name plus a short technical hint. Common techniques get a single line. Less obvious or easily forgotten techniques get a short paragraph — not a full tutorial, but enough that a model unfamiliar with the project can implement it without guessing. This is a registry, not a teaching document; no use-case prescriptions, no decision tables.

---

## Core Principle — Two Layers

Almost every pattern below is an instance of one underlying split:

> **The image carries atmosphere, world-building, emotional weight. Native SVG shapes carry information, data, editable text.**

This is the single most underused move in image-heavy decks. The default reflex is to place image and text in adjacent rectangles. The far more powerful move — especially for content-rich pages — is to let the image **be the canvas** (often full-bleed) and draw native vector elements (annotation cards, flow nodes, KPI tiles, leader lines, network diagrams, dashboards) directly on top.

Anything that must be editable, numerically accurate, contain Chinese, or be styled to the deck's exact palette belongs in the SVG layer regardless of what the image looks like underneath.

---

## A. Container Layouts (where the image sits)

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

11. **Diagonal split with directional gradient (not hard polygon cut)** — full-bleed `<image>` (do NOT hard-clip) + overlay `<rect fill="url(#grad)">` whose `<linearGradient>` axis runs along the desired diagonal + a `<line>` on the diagonal to make the divider visible. The gradient does the "splitting" softly; hard polygon clipping produces ugly stair-step edges on text panels.

12. **Faded image as backdrop with oversized overlay text** — `<image>` + heavy semi-transparent `<rect fill="bg-color" fill-opacity="0.5–0.7">` over it + huge `<text>` (80–120px) on top. Image becomes texture; text is the subject.

13. **Narrow vertical image strip + giant horizontal title** — `<image x=0 y=0 width=200–280 height=720>` + thick divider `<rect>` + large `<text>` (60–90px) in the remaining width.

14. **Horizontal banner strip cutting through mid-section** — `<image y=middle width=1280 height=200–280>` with edge fades; text blocks above and below the band.

15. **Multi-image montage with bold text spanning across** — multiple `<image>` tiled with 2–4px gaps + large `<text>` (60–100px) in a darkened band spanning the full montage. The band uses `<rect fill-opacity="0.5–0.7">` to keep text legible across all underlying images.

16. **Negative-space dominant — small image, mostly whitespace** — image and text together occupy less than 40% of the canvas; rest is empty.

17. **Picture-in-picture inset** — large `<image>` background + small `<image>` overlaid inside it with a `<rect>` frame.

18. **Image as full-height sidebar column** — narrow `<image x=0 y=0 width=~200–280 height=720>`; rest of canvas is content area.

19. **Image floating in whitespace with thin frame and caption** — `<image>` + thin `<rect fill="none" stroke="…">` frame around it + `<text>` caption below.

## B. Non-rectangular Image Shapes

20. **Circular crop** — `<clipPath><circle cx cy r/></clipPath>` referenced by `<image clip-path="url(#id)"/>`.

21. **Rounded rectangle crop** — `<clipPath><rect rx ry/></clipPath>`; the `rx` value controls roundness.

22. **Ellipse / oval crop** — `<clipPath><ellipse cx cy rx ry/></clipPath>`.

23. **Hexagonal / polygonal crop** — `<clipPath><polygon points="x1,y1 x2,y2 …"/></clipPath>`; remember to keep all vertices inside the image's display rectangle.

24. **Custom path crop (blob, arrow, leaf, silhouette)** — `<clipPath><path d="…"/></clipPath>`; allows any curved or organic shape. PowerPoint export translates this to `custGeom` and survives roundtrip.

25. **Layered paper-cut stack** — multiple image or shape layers each with `clipPath` + a small `<feDropShadow>` offset to fake physical layering depth. Each layer casts a shadow onto the next, producing real-looking craft depth.

26. **Triptych baked into a single wide image** — one wide `<image width=1160 height=334>` whose internal composition already contains 2–3 scenes. Generate the triptych as one image (not three separate calls) when scene-to-scene consistency matters — the model preserves character identity, lighting continuity, and color grading far more reliably when panels are produced together.

## C. Overlay & Masking Treatments

27. **Linear gradient mask for text legibility** — `<linearGradient>` in `<defs>` (set `x1/y1/x2/y2` for direction) + overlay `<rect fill="url(#grad)">`. Most common is top-to-bottom darkening on full-bleed cover images.

28. **Radial gradient vignette** — `<radialGradient cx cy r>` with dark outer stops; overlay `<rect>`. Focuses attention by darkening the periphery.

29. **Two-stop scrim — opaque on text side, transparent on focal side** — `<linearGradient>` with one stop at `stop-opacity="0.9"` and another at `stop-opacity="0"`. Use when text sits on one side and the image's subject on the other.

30. **Flat semi-transparent rectangle overlay** — `<rect fill="#000" fill-opacity="0.4"/>` over the image. Uniform darkening/lightening; simplest scrim.

31. **Color-tinted overlay** — `<rect fill="#brandColor" fill-opacity="0.15–0.25"/>`. Pushes a foreign-looking image toward the deck's palette without regenerating it.

32. **Multi-stop scrim with hue shift** — three-or-more-stop `<linearGradient>` where stops are different colors (e.g. dark navy → transparent → warm orange). This re-grades the image's color world without regenerating — particularly useful when an AI image came back with the right composition but wrong color temperature.

33. **Spotlight mask — clear region surrounded by darkness** — cover the canvas with `<rect>` filled by a `<radialGradient>` whose inner stop is fully transparent and outer stop is opaque dark. Reads as a flashlight beam on the focal area. Use sparingly — it kills everything outside the spotlight.

34. **Gaussian-blur backdrop** — `<filter><feGaussianBlur stdDeviation="8–15"/></filter>` applied to the background image, with sharp content layered on top unblurred. Reads as depth-of-field. Be aware that filters have inconsistent PPT export support — if fidelity matters, bake the blur into the source image instead.

35. **Duotone treatment** — two-color mapping of a photograph (e.g. deep navy shadows + warm cream highlights). Most reliable when baked into the source image at generation time. Runtime SVG duotone via `<feColorMatrix>` + `<feComponentTransfer>` is possible but the filter chain is fragile through PPT export — only attempt if you control the renderer.

36. **Drop shadow under image panel** — `<filter><feDropShadow dx dy stdDeviation flood-color flood-opacity/></filter>` applied to the image's container `<rect>` (or to the `<image>` itself). Standard depth lift.

37. **Inner / outer glow on overlay shape** — `<filter><feGaussianBlur/><feMerge/></filter>` on a shape, or simply a slightly larger blurred `<rect>` underneath the target.

## D. Image-as-Canvas + Native Overlay (the most underused family)

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

## E. Multi-Image Compositions

47. **Small multiples — 3–6 same-kind images in an evenly spaced row** — each in identical container, each with identical caption block underneath (title + one-line description). This is **not** a generic grid: the identical framing is itself the message — readers compare across panels because the structure is the same. Useful for style comparisons, time-series snapshots, product variations.

48. **Side-by-side comparison (before/after, A/B, then/now)** — two `<image>` of equal size in 50/50 split with thin divider `<line>` and "before" / "after" labels.

49. **Asymmetric collage** — one large `<image>` + 2–3 smaller `<image>` arranged around it; sizes vary, gaps consistent.

50. **Tiled grid (2×2, 2×3, 3×3) with equal cells** — `cell_size = (canvas - total_gap) / cols`; consistent `gap=2–20px`.

51. **Mosaic** — irregular tile sizes packed together with or without thin gaps; each image clipped to its tile's rect.

52. **Image strip / filmstrip** — horizontal sequence of `<image>` elements with thin gaps; same height, varying widths allowed.

53. **Vertical image stack** — column of `<image>` aligned by width, shared annotations on one side.

54. **Overlapping image stack** — `<image>` elements with overlapping `x/y` positions; each subsequent one in front (z-order by document order); often combined with slight rotation for layered photo-print look.

55. **Diptych split — two images abutting at 50/50** — vertical or horizontal split with optional thin divider `<line>`.

56. **Image triptych** — three independent `<image>` side-by-side, equal widths or 2:1:2 etc. (distinct from #26 baked-in triptych, where the three scenes are inside one image file).

## F. Image as Texture / Atmosphere

57. **Full-bleed image with extreme low opacity as texture wash** — full-bleed `<image>` + overlay `<rect fill="bg-color" fill-opacity="0.7–0.85"/>` so the image only barely shows through.

58. **Image fragment as decorative corner element** — small `<image>` (often with `clipPath`) placed in one corner; not the focus, just visual seasoning.

59. **Image as horizontal divider band** — narrow `<image height=80–150>` placed between two text sections instead of a `<line>` divider.

60. **Image as ambient noise** — visible but low contrast; mood-setting only, not informational.

61. **Image as watermark behind body content** — large `<image>` at very low opacity behind body text. Use either a pre-baked low-alpha image or a high-opacity overlay `<rect>` to suppress visibility.

## G. Special Techniques

62. **Same image, two references — full view + zoom-callout** — reference the same image file twice in two `<image>` elements: one shows the full scene at normal size; the second uses `clipPath` (circle or rectangle) plus a larger display size to "zoom into" a sub-region. Connect them with a bezier `<path>` ending in `marker-end`; ring the zoom with a `<circle stroke>` so it reads as a magnifying lens. No special asset needed — the zoom effect comes from same-source-different-display.

63. **Transparent PNG sticker / cutout** — an RGBA PNG (with alpha channel) placed via standard `<image>` — no `clipPath` required, the transparency lives in the file itself. Useful for subjects that should not appear inside a rectangular frame (people cutouts, product shots, decorative motifs floating over backgrounds). Producing transparent PNGs is **not** a standard ppt-master pipeline step — three paths: (a) AI backend that supports transparent output natively, (b) generate a chroma-key (solid green background) image then strip the green with a separate tool, (c) user-supplied transparent asset. SVG-side usage is trivial; asset preparation is the work.

64. **Image with embedded text rendered by the AI** — text becomes part of the artwork: decorative lettering, designed title, hand-lettered keyword. Prompt with explicit text content. Reliable only for **short English**. Chinese characters, long phrases, and digits regularly come back malformed and cannot be edited. Anything that must be correct or editable goes in the SVG `<text>` layer.

65. **Image with NO text — labels added as native SVG** — generate the image with explicit "no text, no letters, no numbers, no signs" instruction (`text_policy: none`), then place all labels as `<text>` overlays. Default safe path for any deck with Chinese, data, or editable copy.

66. **Image fading into the solid background** — soften the image's edge into the deck's background color via a `<linearGradient>` overlay whose end-stop matches the background hex exactly. The image's rectangular boundary disappears, producing seamless integration.

67. **Image with knock-out / cut-out shape** — overlay a shape filled with the background color or another image, creating the impression of a hole punched through the underlying image.

68. **Text-as-mask over image** — letterforms revealing image through them. SVG-level `<mask>` is forbidden in this project (PPT export breaks). The only reliable way: bake this effect into the image at generation time by prompting for "large lettering revealing the underlying scene through letterforms." Treat as a pre-rendered artistic choice, not a runtime effect.

69. **Image rotated at a slight angle for editorial feel** — `transform="rotate(angle cx cy)"` on the `<image>` or its container `<g>`; 2–6 degrees typical. Adds dynamism without breaking layout.

70. **Image with thin colored matte frame** — `<rect fill="none" stroke="#color" stroke-width="2–6"/>` over or around the image edge. Single rule, single color.

71. **Image with multiple stacked frames for "photo print" aesthetic** — nested `<rect>` outlines or `<rect>` containers of slightly different sizes giving a "framed photograph" look.

72. **Image-to-image transition / merge** — two `<image>` elements with overlapping regions, one or both with gradient masks (from group C) creating a soft blend between them.

## H. Decision Guidance

When picking from this catalog, the question is rarely "which one is best" — it is "what is the image actually doing on this page." If the image *is* the message, use a full-bleed pattern from group A. If the image is supporting context, use a side or strip pattern. If the page needs editable information *on top of* an image, group D is almost always the right answer — it is also the family AI most often forgets exists. Groups B, C, F, G are modifiers — apply them on top of a primary layout choice. Do not stack multiple primary layouts on one page.

## I. Hard Constraints

- Long body copy, data points, numeric labels, and Chinese text always go in the SVG layer — never baked into the image.
- `<clipPath>` is only allowed on `<image>` elements, never on shapes, groups, or text.
- Transparency uses `fill-opacity` / `stop-opacity` — never `rgba()`.
- No `<mask>` (use gradient overlays instead). No `<feComposite>` for alpha compositing. `<feDropShadow>` and `<feGaussianBlur>` are acceptable but their PPT export is inconsistent — bake into the source image when fidelity is critical.
- One primary layout per page. Overlay treatments compose; layouts do not.

---

For sizing math (calculating container dimensions from image aspect ratio when using side-by-side intent), see [`image-layout-spec.md`](image-layout-spec.md). This file is the design vocabulary; that file is the dimension calculator.
