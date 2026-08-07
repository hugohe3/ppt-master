---
layout_id: editorial_bleed
kind: layout
category: general
summary: A structure-only 16:9 system with 10 authored PowerPoint Layouts whose images bleed to the canvas edge and whose text sits on the image behind a scrim.
keywords: [editorial, full-bleed, image, scrim, dark]
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard
native_structure_mode: structured
page_count: 10
page_types:
  - hero_full
  - hero_side_scrim
  - split_bleed
  - split_bleed_reverse
  - chapter_full
  - quote_over_image
  - triptych
  - image_grid_four
  - full_statement
  - closing_full
placeholders:
  01_hero_full: ["{{TITLE}}", "{{SUBTITLE}}"]
  02_hero_side_scrim: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}"]
  03_split_bleed: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}"]
  04_split_bleed_reverse: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}"]
  05_chapter_full: ["{{CHAPTER_NUM}}", "{{CHAPTER_TITLE}}", "{{CHAPTER_DESC}}"]
  06_quote_over_image: ["{{QUOTE_TEXT}}", "{{ATTRIBUTION}}"]
  07_triptych: ["{{PAGE_TITLE}}", "{{CAPTION_1}}", "{{CAPTION_2}}", "{{CAPTION_3}}"]
  08_image_grid_four: ["{{CAPTION_1}}", "{{CAPTION_2}}", "{{CAPTION_3}}", "{{CAPTION_4}}"]
  09_full_statement: ["{{KEY_MESSAGE}}", "{{SUPPORT_TEXT}}"]
  10_closing_full: ["{{CLOSING_MESSAGE}}", "{{CONTACT_LINE}}"]
---

# Editorial Bleed — Design Specification

## IV. Signature Design Elements

Editorial Bleed provides a structural vocabulary for 16:9 material where imagery
carries the argument and text is set on the image rather than beside it. The
neutral prototype paint exists only to expose hierarchy and slot geometry; it is
not an identity segment. Color, typography, logo, voice, and icon treatment
remain downstream decisions.

| Element | Template-specific behavior |
|---|---|
| No safe frame for pictures | Every `picture` slot reaches at least one canvas edge: full canvas on `hero_full`, `hero_side_scrim`, `chapter_full`, `quote_over_image`, and `closing_full`; an exact half on the two `split_bleed` variants; equal vertical bands on `triptych`; four `640×360` quadrants on `image_grid_four`. Text keeps an 80 px margin, pictures keep none. Insetting a picture inside a margin turns this system into an ordinary content layout. |
| Scrims are Slide-local, by PowerPoint's rule | PowerPoint paints Layout shapes beneath Slide content, and the picture is Slide content, so an overlay cannot be a Layout atom. Every scrim is therefore a Slide-local `data-pptx-role="decoration"` rect placed after its picture slot in document order. It travels as a prototype pattern, not as Layout-inherited chrome, and a page authored from this system must carry its own scrim. |
| Four overlay techniques | `hero_full` and `closing_full` use a bottom vertical fade (black `0 → 0.78 / 0.82`). `hero_side_scrim` uses a horizontal directional scrim (`0.88 → 0.30 → 0`) so the picture stays readable on the open side. `chapter_full` uses a full-canvas graded wash (`0.44 → 0.68`) that darkens toward its text. `quote_over_image` uses a raised-floor radial vignette (`0.42 → 0.72`) so a centered quote holds contrast while the frame edges fall away. |
| Overlays are gradients, never solid rects | A full-canvas solid `<rect>` is reserved for background ownership in a structured package and is compiled into the background plane, which sits below every picture. Every overlay here therefore carries a gradient paint even where the intent reads as a flat wash. Replacing one with a solid fill plus `fill-opacity` inverts its stacking and fails template validation. |
| Dark base plane | The single Master carries a dark background. The reusable structural fact is that the base plane is dark because text sits on imagery and reverses out of it; the prototype hex is replaceable preview paint, not an identity value. It is visible only where no picture covers it: the text half of the split pages, and all of `full_statement`. |
| A page without a picture | `full_statement` carries no picture slot. A system built entirely on imagery needs one page that stops, or every page competes for the same attention. |
| Captions instead of titles | `image_grid_four` declares no title slot, and `triptych` puts its title inside a top fade rather than above the images, because there is no margin band to hold one. Captions carry the reading order on those pages. |
| Text entry | Body and caption slots begin at the upper-left. Centered alignment is reserved for the quote page, whose composition is symmetric by intent. |

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|
| `01_hero_full.svg` | `hero_full` | Hero Full | Full-canvas picture under a bottom fade with title and subtitle |
| `02_hero_side_scrim.svg` | `hero_side_scrim` | Hero with Side Scrim | Full-canvas picture with a directional scrim over a left text column |
| `03_split_bleed.svg` | `split_bleed` | Split Bleed | Left half-canvas picture beside a right text column |
| `04_split_bleed_reverse.svg` | `split_bleed_reverse` | Split Bleed Reverse | Right half-canvas picture beside a left text column |
| `05_chapter_full.svg` | `chapter_full` | Chapter Full | Full-canvas picture under a flat wash with chapter number, title, and description |
| `06_quote_over_image.svg` | `quote_over_image` | Quote over Image | Full-canvas picture under a wash and vignette with a centered quote |
| `07_triptych.svg` | `triptych` | Triptych | Three full-height picture bands with top and bottom fades and three captions |
| `08_image_grid_four.svg` | `image_grid_four` | Four-Image Grid | Four edge-to-edge picture quadrants with per-cell fades and captions |
| `09_full_statement.svg` | `full_statement` | Full Statement | Picture-free dark canvas with one dominant statement |
| `10_closing_full.svg` | `closing_full` | Closing Full | Full-canvas picture under a bottom fade with closing message and contact line |
