# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFFFFF
- secondary_bg: #F4F7FA
- primary: #1B3A5C
- accent: #E8743B
- secondary_accent: #3E7CB1
- text: #1D2733
- text_secondary: #5B6776
- text_tertiary: #8A94A1
- border: #D8DEE6
- success: #2E7D32
- warning: #C62828
- tint_primary: #EAF0F6
- tint_accent: #FBF0E9
- tint_success: #EAF6EE
- accent_light: #EE9461
- secondary_accent_light: #5C97C7
- cover_dark: #0F2238
- cover_text: #CBD8E6
- cover_text_muted: #9FB2C6
- image_rendering: blueprint
- image_palette: cool-corporate

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 18
- cover_title: 60
- hero_number: 56
- title: 32
- subtitle: 24
- annotation: 14
- chart_annotation: 13
- footnote: 11

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: snowflake, lock, building-bank, server-2, alert-triangle, bulb, layers-subtract, math-function, transform, arrows-split, sitemap, topology-star, share-2, git-branch, bolt, gauge, puzzle, flask, database, chart-bar, circle-check, target

## images
- cover_hero: images/cover_hero.png
- cost_explosion: images/cost_explosion.png
- lowrank_insight: images/lowrank_insight.png
- reparam_diagram: images/reparam_diagram_cropped.png
- attention_apply: images/attention_apply.png
- subspace_heatmap: images/subspace_heatmap.png
- formula_001: images/formula_001.png | no-crop
- formula_002: images/formula_002.png | no-crop
- formula_003: images/formula_003.png | no-crop
- formula_004: images/formula_004.png | no-crop

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: breathing
- P06: breathing
- P07: dense
- P08: dense
- P09: dense
- P10: dense
- P11: dense
- P12: dense
- P13: dense
- P14: dense
- P15: anchor

## page_charts
- P02: agenda_list
- P04: vertical_list
- P09: icon_grid
- P10: grouped_bar_chart
- P11: basic_table
- P12: consulting_table
- P13: kpi_cards
- P14: basic_table
- P15: vertical_list

## forbidden
- Mixing icon libraries
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;` …) — write raw Unicode; escape `& < > " '` as `&amp; &lt; &gt; &quot; &apos;`
