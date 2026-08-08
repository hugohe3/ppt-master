---
layout_id: report_core
kind: layout
category: general
summary: A structure-only 16:9 system with 13 authored PowerPoint Layouts across two Masters, carrying persistent page chrome and page-number placeholders.
keywords: [report, business, dense, chrome, multi-master]
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard
native_structure_mode: structured
page_count: 13
page_types:
  - cover
  - section_divider
  - agenda
  - title_content
  - two_content
  - three_block
  - kpi_row
  - chart_insight
  - table_summary
  - process_timeline
  - matrix_2x2
  - appendix
  - closing
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{DATE}}"]
  02_section_divider: ["{{CHAPTER_NUM}}", "{{CHAPTER_TITLE}}", "{{CHAPTER_DESC}}"]
  03_agenda: ["{{PAGE_TITLE}}", "{{ITEM_1}}", "{{ITEM_2}}", "{{ITEM_3}}", "{{ITEM_4}}", "{{ITEM_5}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  04_title_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  05_two_content: ["{{PAGE_TITLE}}", "{{LEFT_CONTENT}}", "{{RIGHT_CONTENT}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  06_three_block: ["{{PAGE_TITLE}}", "{{BLOCK_1}}", "{{BLOCK_2}}", "{{BLOCK_3}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  07_kpi_row: ["{{PAGE_TITLE}}", "{{KPI_1}}", "{{KPI_2}}", "{{KPI_3}}", "{{KPI_4}}", "{{CONTENT_AREA}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  08_chart_insight: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{SOURCE}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  09_table_summary: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{SOURCE}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  10_process_timeline: ["{{PAGE_TITLE}}", "{{STEP_1}}", "{{STEP_2}}", "{{STEP_3}}", "{{STEP_4}}", "{{KEY_MESSAGE}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  11_matrix_2x2: ["{{PAGE_TITLE}}", "{{Y_AXIS}}", "{{X_AXIS}}", "{{QUADRANT_1}}", "{{QUADRANT_2}}", "{{QUADRANT_3}}", "{{QUADRANT_4}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  12_appendix: ["{{PAGE_TITLE}}", "{{LEFT_CONTENT}}", "{{RIGHT_CONTENT}}", "{{FOOTER_NOTE}}", "{{PAGE_NUM}}"]
  13_closing: ["{{CLOSING_MESSAGE}}", "{{CONTACT_LINE}}"]
---

# Report Core — Design Specification

## IV. Signature Design Elements

Report Core provides a structural vocabulary for paginated 16:9 material that is
read as much as it is presented: reviews, analyses, and evidence-carrying
decks whose pages need to be citable and navigable. The neutral prototype paint
exists only to expose hierarchy and slot geometry; it is not an identity
segment. Color, typography, logo, voice, and icon treatment remain downstream
decisions.

| Element | Template-specific behavior |
|---|---|
| Two Masters, two background planes | `report_core_content_master` carries the light reading plane plus persistent chrome; `report_core_divider_master` carries an inverted plane with no chrome, used by `cover`, `section_divider`, and `closing`. The reusable structural fact is that the roster owns two independent background planes and two Theme parts — not the specific prototype hex values, which remain replaceable preview paint. |
| Persistent page chrome | The content Master owns a header hairline at y 64 and a footer hairline at y 664 as static atoms repeated on every content page. Divider pages carry neither, so a section break reads as a genuine interruption rather than a restyled content page. |
| Page numbering is structural | Every content Layout declares a `slide-number` slot at `1112 676 120 32` and a `footer` slot at `48 676 900 32`; `cover` declares a `date` slot. These enable the matching Layout header/footer flags so the compiled package carries real numbering capability instead of drawn text. |
| Tightened frame | Margins are 48 px and the title band is `48 88 1184 56` at 28 px, against a 64 px margin and 36 px title on a breathing general system. The content field runs y 176 to y 640 on every content page. |
| Rules before containers | Grouping is carried by hairlines wherever it can be: `agenda` separates its five rows with rules and Layout-owned `01`–`05` indices, and `appendix` uses a single column rule with no panel at all. Filled panels appear only where a region genuinely needs a distinct material plane. |
| Density ladder | Body text steps from 20 px on single-region pages, to 19 px in split panels, to 18 px in step and evidence regions, down to 15 px in `appendix`. Chrome text sits at 12 px. The ladder is what lets one system carry both a synthesis page and a reference page without changing frame. |
| Analytical page types | `kpi_row` places four metrics across the full 1184 px field, which this canvas width supports without compressing them. `matrix_2x2` adds four quadrant slots plus two axis-label slots for positioning arguments. `chart_insight` and `table_summary` declare typed `chart` / `table` slots whose authored groups remain complete SVG fallbacks; optional replacement metadata can materialize PowerPoint-native data objects only when that export path is requested. |
| Text entry | General body and object slots begin at the upper-left. Centered alignment is reserved for KPI values, short process nodes, and the timeline takeaway. |

## V. Page Roster

| SVG | Master | Layout key | PowerPoint picker name | Purpose |
|---|---|---|---|---|
| `01_cover.svg` | Divider | `cover` | Cover | Title and subtitle on the inverted plane with a date slot |
| `02_section_divider.svg` | Divider | `section_divider` | Section Divider | Chapter number, title, and description above a rule |
| `03_agenda.svg` | Content | `agenda` | Agenda | Five rule-separated rows with Layout-owned ordinal indices |
| `04_title_content.svg` | Content | `title_content` | Title and Content | Page title over one full-width content region |
| `05_two_content.svg` | Content | `two_content` | Two Content | Equal left and right content panels |
| `06_three_block.svg` | Content | `three_block` | Three Block | Three parallel content panels |
| `07_kpi_row.svg` | Content | `kpi_row` | KPI Row | Four metrics across the full field over one evidence region |
| `08_chart_insight.svg` | Content | `chart_insight` | Chart and Insight | Chart slot with SVG fallback, interpretation, and source rails |
| `09_table_summary.svg` | Content | `table_summary` | Table and Summary | Table slot with SVG fallback, summary, and source rails |
| `10_process_timeline.svg` | Content | `process_timeline` | Process Timeline | Four ordered steps on a shared axis plus a takeaway rail |
| `11_matrix_2x2.svg` | Content | `matrix_2x2` | Two-by-Two Matrix | Four quadrant slots with two axis-label slots |
| `12_appendix.svg` | Content | `appendix` | Appendix | Dense two-column reference page with no container |
| `13_closing.svg` | Divider | `closing` | Closing | Closing message and contact line on the inverted plane |
