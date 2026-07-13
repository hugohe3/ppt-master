---
layout_id: presentation_core
kind: layout
category: general
summary: A structure-first presentation layout system combining familiar PowerPoint defaults with advanced editorial, image, and data compositions.
keywords: [general, powerpoint, business, editorial, image, data-story]
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
source_canvas_width: 1280
source_canvas_height: 720
source_viewbox: "0 0 1280 720"
replication_mode: fidelity
native_structure_mode: structured
page_count: 18
page_types:
  - title_slide
  - title_content
  - section_header
  - two_content
  - comparison
  - title_only
  - blank
  - content_caption
  - picture_caption
  - hero_statement
  - editorial_split
  - three_card
  - kpi_dashboard
  - process_timeline
  - data_story
  - title_picture
  - two_picture_caption
  - screenshot_focus
placeholders:
  01_title_slide: ["{{TITLE}}", "{{SUBTITLE}}"]
  02_title_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}"]
  03_section_header: ["{{CHAPTER_TITLE}}", "{{CHAPTER_DESC}}"]
  04_two_content: ["{{PAGE_TITLE}}", "{{LEFT_CONTENT}}", "{{RIGHT_CONTENT}}"]
  05_comparison: ["{{PAGE_TITLE}}", "{{LEFT_TITLE}}", "{{LEFT_CONTENT}}", "{{RIGHT_TITLE}}", "{{RIGHT_CONTENT}}"]
  06_title_only: ["{{PAGE_TITLE}}"]
  07_blank: []
  08_content_caption: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{CAPTION}}"]
  09_picture_caption: ["{{PAGE_TITLE}}", "{{CAPTION}}"]
  10_hero_statement: ["{{KEY_MESSAGE}}", "{{SUBTITLE}}"]
  11_editorial_split: ["{{PAGE_TITLE}}", "{{BODY_TEXT}}"]
  12_three_card: ["{{PAGE_TITLE}}", "{{CARD_1}}", "{{CARD_2}}", "{{CARD_3}}"]
  13_kpi_dashboard: ["{{PAGE_TITLE}}", "{{KPI_1}}", "{{KPI_2}}", "{{KPI_3}}", "{{KPI_4}}", "{{CONTENT_AREA}}"]
  14_process_timeline: ["{{PAGE_TITLE}}", "{{STEP_1}}", "{{STEP_2}}", "{{STEP_3}}", "{{STEP_4}}", "{{KEY_MESSAGE}}"]
  15_data_story: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{KEY_MESSAGE}}", "{{SOURCE}}"]
  16_title_picture: ["{{PAGE_TITLE}}"]
  17_two_picture_caption: ["{{PAGE_TITLE}}", "{{LEFT_CAPTION}}", "{{RIGHT_CAPTION}}"]
  18_screenshot_focus: ["{{PAGE_TITLE}}", "{{ANNOTATION}}", "{{SOURCE}}"]
---

# Presentation Core — Design Specification

## I. Template Overview

Presentation Core is a structure-only library for general business, teaching,
project, and reporting decks. Its regular set mirrors the familiar PowerPoint
layout vocabulary; its advanced set adds asymmetric, editorial, image-led,
process, and data-story compositions without introducing industry-specific
content.

The light neutral preview treatment exists only to expose hierarchy and slot
geometry. Color, typography, logo, voice, and icon treatment remain downstream
identity decisions and are not owned by this layout.

## IV. Signature Design Elements

| Element | Template-specific behavior |
|---|---|
| Shared frame | One restrained Master background and a 64 px horizontal safe frame keep the roster visually coherent without imposing brand chrome. |
| Regular vocabulary | Nine familiar PowerPoint layouts preserve the expected title, content, comparison, caption, picture, and blank starting points. |
| Editorial rhythm | Hero, split, card, process, and data layouts alternate breathing and dense structures instead of repeating one card grid. |
| Image system | Picture layouts use explicit native picture regions for one-image, paired-image, captioned-image, and screenshot scenarios. |
| Text entry | General body and object slots begin at the upper-left; centered alignment is reserved for KPI values, short process nodes, and focused statements. |
| Neutral framing | Pale panels and hairlines reveal intended zones in the prototype; downstream deck or brand skin controls final paint. |

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|
| `01_title_slide.svg` | `title_slide` | Title Slide | Centered title and subtitle cover |
| `02_title_content.svg` | `title_content` | Title and Content | Page title over one flexible content region |
| `03_section_header.svg` | `section_header` | Section Header | Large section title with supporting description |
| `04_two_content.svg` | `two_content` | Two Content | Equal left and right content regions |
| `05_comparison.svg` | `comparison` | Comparison | Paired headings and paired comparison bodies |
| `06_title_only.svg` | `title_only` | Title Only | Title slot with an otherwise open canvas |
| `07_blank.svg` | `blank` | Blank | Zero-slot composition surface |
| `08_content_caption.svg` | `content_caption` | Content with Caption | Main content with a dedicated caption rail |
| `09_picture_caption.svg` | `picture_caption` | Picture with Caption | Native picture region with a caption column |
| `10_hero_statement.svg` | `hero_statement` | Hero Statement | One dominant claim with a short qualifier |
| `11_editorial_split.svg` | `editorial_split` | Editorial Split | Asymmetric body and picture composition |
| `12_three_card.svg` | `three_card` | Three-Card Synthesis | Three parallel synthesis regions |
| `13_kpi_dashboard.svg` | `kpi_dashboard` | KPI Dashboard | Four compact KPI slots over one evidence region |
| `14_process_timeline.svg` | `process_timeline` | Process Timeline | Four ordered steps plus a takeaway rail |
| `15_data_story.svg` | `data_story` | Data Story | Evidence canvas, interpretation rail, and source line |
| `16_title_picture.svg` | `title_picture` | Title and Picture | Page title over one large native picture region |
| `17_two_picture_caption.svg` | `two_picture_caption` | Two Pictures with Captions | Two equal native pictures with independent captions |
| `18_screenshot_focus.svg` | `screenshot_focus` | Screenshot Focus | Screenshot frame with annotation and source rail |
