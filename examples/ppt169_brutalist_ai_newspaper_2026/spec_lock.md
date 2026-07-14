# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFFFFF
- bg_paper: #F4F1EA
- primary: #111111
- accent: #C8102E
- secondary_accent: #3A3A3A
- text: #111111
- text_secondary: #3A3A3A
- text_tertiary: #6B6B6B
- border: #000000
- success: #1A6E3A
- warning: #A02014
- image_rendering: editorial
- image_palette: mono-ink

## typography
- font_family: "Times New Roman", SimSun, serif
- title_family: Impact, "Arial Black", SimHei, sans-serif
- subtitle_family: "Arial Black", SimHei, sans-serif
- body_family: "Times New Roman", SimSun, serif
- emphasis_family: Georgia, "Times New Roman", SimSun, serif
- code_family: Consolas, "Courier New", monospace
- body: 14
- title: 32
- subtitle: 20
- cover_title: 84
- section_opener: 48
- hero_number: 64
- annotation: 11
- footnote: 9

## images
- p01_cover_hero: images/p01_cover_hero.png
- p03_revenue_leader: images/p03_revenue_leader.png
- p05_training_cost: images/p05_training_cost.png
- p06_inference_thermal: images/p06_inference_thermal.png
- p08_regulation_table: images/p08_regulation_table.png

## page_rhythm
- P01: anchor
- P02: dense
- P03: dense
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: dense
- P10: breathing

## page_charts
- P02: kpi_cards
- P03: horizontal_bar_chart
- P04: dumbbell_chart
- P05: line_chart
- P06: bar_chart
- P07: dumbbell_chart
- P08: comparison_table
- P09: timeline

## forbidden
- Mixing icon libraries
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`
