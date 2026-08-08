---
layout_id: presentation_core_43
kind: layout
category: general
summary: A structure-only 4:3 system with 16 authored PowerPoint Layouts for projector, classroom, academic, and meeting-room presentations.
keywords: [general, powerpoint, 4-3, projector, academic]
canvas_format: ppt43
canvas_width: 1024
canvas_height: 768
canvas_viewbox: "0 0 1024 768"
replication_mode: standard
native_structure_mode: structured
page_count: 16
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
  - three_card
  - kpi_grid
  - process_timeline
  - stacked_split
  - chart_insight
  - table_summary
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
  11_three_card: ["{{PAGE_TITLE}}", "{{CARD_1}}", "{{CARD_2}}", "{{CARD_3}}"]
  12_kpi_grid: ["{{PAGE_TITLE}}", "{{KPI_1}}", "{{KPI_2}}", "{{KPI_3}}", "{{KPI_4}}", "{{CONTENT_AREA}}"]
  13_process_timeline: ["{{PAGE_TITLE}}", "{{STEP_1}}", "{{STEP_2}}", "{{STEP_3}}", "{{STEP_4}}", "{{KEY_MESSAGE}}"]
  14_stacked_split: ["{{PAGE_TITLE}}", "{{TOP_CONTENT}}", "{{BOTTOM_CONTENT}}"]
  15_chart_insight: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{SOURCE}}"]
  16_table_summary: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{SOURCE}}"]
---

# Presentation Core 4:3 — Design Specification

## IV. Signature Design Elements

Presentation Core 4:3 provides a structural vocabulary for rooms and devices
that still project in 4:3: classrooms, lecture halls, academic sessions, and
meeting rooms with fixed legacy displays. The neutral prototype paint exists
only to expose hierarchy and slot geometry; it is not an identity segment.
Color, typography, logo, voice, and icon treatment remain downstream decisions.

| Element | Template-specific behavior |
|---|---|
| Shared frame | One restrained Master background and a 56 px horizontal safe frame keep the roster coherent. The title band occupies `56 36 912 64` on every titled page, and the content field runs from y 136 to y 712. |
| Narrower column budget | The 912 px content width gives each half-page column 440 px and each third 288 px. Body copy in split layouts steps down one size relative to single-column pages so line length stays readable instead of forcing hyphenation. |
| Vertical preference | The taller field makes stacking a first-class option rather than a fallback. `stacked_split` divides the page into two full-width bands; use it where a wide canvas would reach for a left/right split. |
| Square-leaning metric grid | `kpi_grid` places four metrics in a 2×2 block over one evidence panel instead of a single four-across row, which would compress each metric below a readable width on this canvas. |
| Image system | `picture_caption` uses a typed `picture` slot occupying the full left field with an independent caption rail, matching the near-square crop that 4:3 rooms display well. |
| Data system | `chart_insight` and `table_summary` declare typed `chart` / `table` slots. Their authored groups remain complete SVG fallbacks; optional replacement metadata can materialize PowerPoint-native data objects only when that export path is requested. |
| Text entry | General body and object slots begin at the upper-left. Centered alignment is reserved for KPI values, short process nodes, the timeline takeaway, and focused statements. |
| Neutral framing | Pale panels and hairlines reveal intended zones in the prototype; downstream deck or brand skin controls final paint. |

## V. Page Roster

| SVG | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|
| `01_title_slide.svg` | `title_slide` | Title Slide | Accent-anchored title and subtitle cover |
| `02_title_content.svg` | `title_content` | Title and Content | Page title over one full-width content region |
| `03_section_header.svg` | `section_header` | Section Header | Large section title with supporting description |
| `04_two_content.svg` | `two_content` | Two Content | Equal left and right content regions |
| `05_comparison.svg` | `comparison` | Comparison | Paired headings over paired comparison bodies |
| `06_title_only.svg` | `title_only` | Title Only | Title slot with an otherwise open canvas |
| `07_blank.svg` | `blank` | Blank | Zero-slot composition surface |
| `08_content_caption.svg` | `content_caption` | Content with Caption | Main content with a dedicated caption rail |
| `09_picture_caption.svg` | `picture_caption` | Picture with Caption | Full-height picture slot with a caption column |
| `10_hero_statement.svg` | `hero_statement` | Hero Statement | One dominant claim with a short qualifier |
| `11_three_card.svg` | `three_card` | Three-Card Synthesis | Three parallel synthesis regions |
| `12_kpi_grid.svg` | `kpi_grid` | KPI Grid | Four metrics in a 2×2 block over one evidence region |
| `13_process_timeline.svg` | `process_timeline` | Process Timeline | Four ordered steps on a shared axis plus a takeaway rail |
| `14_stacked_split.svg` | `stacked_split` | Stacked Split | Two full-width horizontal bands |
| `15_chart_insight.svg` | `chart_insight` | Chart and Insight | Chart slot with SVG fallback, interpretation, and source rails |
| `16_table_summary.svg` | `table_summary` | Table and Summary | Table slot with SVG fallback, summary, and source rails |
