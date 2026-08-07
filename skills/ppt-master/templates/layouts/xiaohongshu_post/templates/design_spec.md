---
layout_id: xiaohongshu_post
kind: layout
category: scenario
summary: A structure-only 3:4 vertical system with 10 authored PowerPoint Layouts for single-column image-text posts on tall social canvases.
keywords: [xiaohongshu, vertical, social, portrait, knowledge-post]
canvas_format: xiaohongshu
canvas_width: 1242
canvas_height: 1660
canvas_viewbox: "0 0 1242 1660"
replication_mode: standard
native_structure_mode: structured
page_count: 10
page_types:
  - cover
  - statement
  - title_content
  - numbered_list
  - two_card_stack
  - image_top_text
  - image_full_caption
  - quote
  - step_flow
  - ending
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LINE}}"]
  02_statement: ["{{KEY_MESSAGE}}", "{{SUPPORT_TEXT}}"]
  03_title_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}"]
  04_numbered_list: ["{{PAGE_TITLE}}", "{{ITEM_1}}", "{{ITEM_2}}", "{{ITEM_3}}", "{{FOOTER_NOTE}}"]
  05_two_card_stack: ["{{PAGE_TITLE}}", "{{CARD_1}}", "{{CARD_2}}", "{{FOOTER_NOTE}}"]
  06_image_top_text: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}"]
  07_image_full_caption: ["{{PAGE_TITLE}}", "{{CAPTION}}"]
  08_quote: ["{{QUOTE_TEXT}}", "{{ATTRIBUTION}}", "{{FOOTER_NOTE}}"]
  09_step_flow: ["{{PAGE_TITLE}}", "{{STEP_1}}", "{{STEP_2}}", "{{STEP_3}}", "{{FOOTER_NOTE}}"]
  10_ending: ["{{CLOSING_MESSAGE}}", "{{CTA_TEXT}}", "{{BRAND_LINE}}"]
---

# Xiaohongshu Post — Design Specification

## IV. Signature Design Elements

Xiaohongshu Post provides a structural vocabulary for tall 3:4 canvases read on
a phone in a single top-to-bottom pass. The neutral prototype paint exists only
to expose hierarchy and slot geometry; it is not an identity segment, and no
platform palette, mark, or typeface is claimed. Color, typography, logo, voice,
and icon treatment remain downstream decisions.

| Element | Template-specific behavior |
|---|---|
| Vertical bands | The page divides into a title band (`80 112 1082 200`), a content field from y 376 to y 1440, and a closing band. Interior pages use a `80 1500 1082 60` footer note; `cover`, `image_full_caption`, and `ending` replace it with a full-bleed band so the last screen-height carries its own weight. |
| Single-column rule | The 1082 px content field is never split into side-by-side columns. Two 521 px halves would leave 34 px body copy with too few characters per line, so every multi-part page stacks instead: rows in `numbered_list`, cards in `two_card_stack`, bands in `image_top_text`. |
| Card and row rhythm | Stacked cards are 504 px tall with a 56 px gap; list rows are 320 px with a 52 px gap. Both keep each unit tall enough to hold a heading plus supporting lines at this reading distance. |
| Fixed list markers | `numbered_list` owns its 1–3 markers as Layout atoms: the circle and its digit are static structure, so only the item copy stays Slide-local. |
| Vertical flow | `step_flow` runs its axis and nodes down the left gutter at x 176 rather than across the page. Progression on this canvas reads downward, matching the scroll direction. |
| Image system | Images carry rather than decorate. `image_top_text` gives a typed `picture` slot the upper 620 px above a text band; `image_full_caption` runs the picture full-bleed to y 1400 with a caption band beneath it, so the crop is never letterboxed by page margins. |
| Focal pages | `statement`, `quote`, and `ending` center a single dominant text block with generous empty field above and below. Centered alignment is confined to these focal roles plus the closing brand line; all list, card, step, and body slots begin at the upper-left. |
| Type scale | Prototype sizes step from cover title 86 through page title 64, focal statement 72/68, body 34, and note 26. They are provisional preview values sized for this canvas, not a locked project type scale. |

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|
| `01_cover.svg` | `cover` | Cover | Accent-anchored title and subtitle over a full-bleed brand band |
| `02_statement.svg` | `statement` | Statement | Centered dominant claim with a short supporting line |
| `03_title_content.svg` | `title_content` | Title and Content | Page title over one single-column content field |
| `04_numbered_list.svg` | `numbered_list` | Numbered List | Three stacked rows with fixed Layout-owned numeric markers |
| `05_two_card_stack.svg` | `two_card_stack` | Two-Card Stack | Two stacked cards of equal height |
| `06_image_top_text.svg` | `image_top_text` | Image over Text | Typed picture slot above a text band |
| `07_image_full_caption.svg` | `image_full_caption` | Full-Bleed Image with Caption | Edge-to-edge picture slot over a caption band |
| `08_quote.svg` | `quote` | Quote | Quotation-marked excerpt with a rule and attribution, no page title |
| `09_step_flow.svg` | `step_flow` | Vertical Step Flow | Three ordered steps on a vertical gutter axis |
| `10_ending.svg` | `ending` | Ending | Centered closing message and action line over a full-bleed brand band |
