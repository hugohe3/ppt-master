---
layout_id: story_vertical
kind: layout
category: scenario
summary: A structure-only 9:16 system with 9 authored PowerPoint Layouts whose text geometry respects the top and bottom story safe zones.
keywords: [story, vertical, social, 9-16, safe-zone]
canvas_format: story
canvas_width: 1080
canvas_height: 1920
canvas_viewbox: "0 0 1080 1920"
replication_mode: standard
native_structure_mode: structured
page_count: 9
page_types:
  - cover
  - statement
  - title_content
  - numbered_list
  - image_full
  - image_top_text
  - two_block
  - step_flow
  - ending
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LINE}}"]
  02_statement: ["{{KEY_MESSAGE}}", "{{SUPPORT_TEXT}}"]
  03_title_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}"]
  04_numbered_list: ["{{PAGE_TITLE}}", "{{ITEM_1}}", "{{ITEM_2}}", "{{ITEM_3}}", "{{FOOTER_NOTE}}"]
  05_image_full: ["{{PAGE_TITLE}}", "{{CAPTION}}"]
  06_image_top_text: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}"]
  07_two_block: ["{{PAGE_TITLE}}", "{{BLOCK_1}}", "{{BLOCK_2}}", "{{FOOTER_NOTE}}"]
  08_step_flow: ["{{PAGE_TITLE}}", "{{STEP_1}}", "{{STEP_2}}", "{{STEP_3}}", "{{FOOTER_NOTE}}"]
  09_ending: ["{{CLOSING_MESSAGE}}", "{{CTA_TEXT}}", "{{BRAND_LINE}}"]
---

# Story Vertical — Design Specification

## IV. Signature Design Elements

Story Vertical provides a structural vocabulary for 9:16 canvases viewed
full-screen on a phone, where surrounding interface chrome overlays the top and
bottom of the frame. The neutral prototype paint exists only to expose hierarchy
and slot geometry; it is not an identity segment, and no platform palette, mark,
or typeface is claimed. Color, typography, logo, voice, and icon treatment
remain downstream decisions.

| Element | Template-specific behavior |
|---|---|
| Safe zones govern text, not pictures | Every text slot stays inside y 120–1740. Picture geometry deliberately does not: `image_full` runs its typed `picture` slot from `0 0` to y 1440 so a full-bleed image sits under the interface chrome rather than being inset into a visible letterbox. This asymmetry is the defining rule of the canvas and must survive any reskin. |
| Band structure | Titled pages use a title band at `80 200 920 180`, a content field from y 440 to y 1620, and a `80 1660 920 56` footer note. `cover` and `ending` replace the footer with a full-bleed band from y 1560 to y 1740, which ends exactly where the bottom safe zone begins. |
| Narrow single column | The content field is 920 px wide — 15% narrower than a 3:4 canvas of the same family — so no page splits it into columns and body copy runs at 32 px. Multi-part pages stack: rows in `numbered_list`, blocks in `two_block`. |
| Row and block rhythm | List rows are 360 px with a 50 px gap; blocks are 560 px with a 60 px gap. Both sit at the upper end of the portrait card range because a 9:16 field has vertical room to spend and few units per page. |
| Fixed list markers | `numbered_list` owns its 1–3 markers as Layout atoms: the circle and its digit are static structure, so only the item copy stays Slide-local. |
| Vertical flow | `step_flow` runs its axis and nodes down the left gutter at x 168. Progression reads downward, matching how the canvas is consumed. |
| Focal pages | `statement` and `ending` center one dominant text block with a wide empty field above and below. Centered alignment is confined to those focal roles plus the closing brand line; list, block, step, and body slots begin at the upper-left. |
| Type scale | Prototype sizes step from cover title 76 through focal 64, page title 56, body 32, and note 24 — one step below the same roles on a 3:4 canvas because the column is narrower. They are provisional preview values, not a locked project type scale. |

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|
| `01_cover.svg` | `cover` | Cover | Accent-anchored title and subtitle over a full-bleed brand band |
| `02_statement.svg` | `statement` | Statement | Centered dominant claim with a short supporting line |
| `03_title_content.svg` | `title_content` | Title and Content | Page title over one single-column content field |
| `04_numbered_list.svg` | `numbered_list` | Numbered List | Three stacked rows with fixed Layout-owned numeric markers |
| `05_image_full.svg` | `image_full` | Full-Bleed Image | Edge-to-edge picture slot crossing the top safe zone, over a caption band |
| `06_image_top_text.svg` | `image_top_text` | Image over Text | Typed picture slot above a text band |
| `07_two_block.svg` | `two_block` | Two Block | Two stacked blocks of equal height |
| `08_step_flow.svg` | `step_flow` | Vertical Step Flow | Three ordered steps on a vertical gutter axis |
| `09_ending.svg` | `ending` | Ending | Centered closing message and action line over a full-bleed brand band |
