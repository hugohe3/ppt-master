---
layout_id: moments_square
kind: layout
category: scenario
summary: A structure-only 1:1 system with 8 authored PowerPoint Layouts that use both horizontal and vertical division on a square canvas.
keywords: [moments, square, social, 1-1, center-radiating]
canvas_format: moments
canvas_width: 1080
canvas_height: 1080
canvas_viewbox: "0 0 1080 1080"
replication_mode: standard
native_structure_mode: structured
page_count: 8
page_types:
  - cover
  - statement
  - title_content
  - two_column
  - three_row
  - image_center
  - image_full
  - ending
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LINE}}"]
  02_statement: ["{{KEY_MESSAGE}}", "{{SUPPORT_TEXT}}"]
  03_title_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}"]
  04_two_column: ["{{PAGE_TITLE}}", "{{LEFT_CONTENT}}", "{{RIGHT_CONTENT}}", "{{FOOTER_NOTE}}"]
  05_three_row: ["{{PAGE_TITLE}}", "{{ITEM_1}}", "{{ITEM_2}}", "{{ITEM_3}}", "{{FOOTER_NOTE}}"]
  06_image_center: ["{{PAGE_TITLE}}", "{{CAPTION}}"]
  07_image_full: ["{{PAGE_TITLE}}", "{{CAPTION}}"]
  08_ending: ["{{CLOSING_MESSAGE}}", "{{CTA_TEXT}}", "{{BRAND_LINE}}"]
---

# Moments Square — Design Specification

## IV. Signature Design Elements

Moments Square provides a structural vocabulary for 1:1 canvases used as
standalone square posters and feed cards. The neutral prototype paint exists
only to expose hierarchy and slot geometry; it is not an identity segment, and
no platform palette, mark, or typeface is claimed. Color, typography, logo,
voice, and icon treatment remain downstream decisions.

| Element | Template-specific behavior |
|---|---|
| Both axes are available | A square field is the only canvas in this family where horizontal and vertical division are equally sound. `two_column` splits the 880 px content field into two 420 px columns, which still carries 28 px body copy at a workable line length, while `three_row` divides the same field into three 148 px bands. Neither is a fallback for the other; keep both when adapting this system. |
| Center-radiating governs focal pages only | `cover`, `statement`, `image_center`, and `ending` center one dominant block on the canvas axis, and the closing brand line stays centered with them. `title_content`, `two_column`, and `three_row` keep a left axis at x 100 because centering running body copy destroys its readability. Do not extend the radiating treatment to those pages. |
| Band structure | Titled pages use a title band at `100 110 880 210`, a content field from y 380 to y 880, and a `100 940 880 56` footer note. `cover` and `ending` replace the footer with a full-bleed band from y 900 to y 1080, sized for a closing identity or code area. |
| Fixed list markers | `three_row` owns its 1–3 markers as Layout atoms: the circle and its digit are static structure, so only the item copy stays Slide-local. |
| Image system | `image_center` holds a 500×500 typed `picture` slot on both canvas axes with the title above and caption below — the square-native composition. `image_full` instead runs the picture edge to edge down to y 820 with a caption band beneath, for pages where the image is the whole message. |
| Type scale | Prototype sizes step from cover title 68 through focal 60, page title 60, body 30, and note 24. They are provisional preview values, not a locked project type scale. |

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|
| `01_cover.svg` | `cover` | Cover | Centered title and subtitle over a full-bleed brand band |
| `02_statement.svg` | `statement` | Statement | Centered dominant claim with a short supporting line |
| `03_title_content.svg` | `title_content` | Title and Content | Left-axis page title over one content field |
| `04_two_column.svg` | `two_column` | Two Column | Two equal 420 px columns |
| `05_three_row.svg` | `three_row` | Three Row | Three stacked bands with fixed Layout-owned numeric markers |
| `06_image_center.svg` | `image_center` | Centered Image | Square picture slot centered on both axes, title above and caption below |
| `07_image_full.svg` | `image_full` | Full-Bleed Image | Edge-to-edge picture slot over a caption band |
| `08_ending.svg` | `ending` | Ending | Centered closing message and action line over a full-bleed brand band |
