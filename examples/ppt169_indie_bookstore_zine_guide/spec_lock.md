# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #F5EFE0
- secondary_bg: #EAE2CC
- primary: #1E4DBC
- accent: #FF5C8A
- secondary_accent: #E8A02E
- text: #1A1A1A
- text_secondary: #5A5A5A
- text_tertiary: #8C8275
- border: #1A1A1A
- image_rendering: screen-print
- image_palette: duotone

## typography
- font_family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif
- title_family: Impact, 'Arial Black', 'Microsoft YaHei', sans-serif
- body_family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif
- emphasis_family: Impact, 'Arial Black', SimHei, 'Microsoft YaHei', sans-serif
- code_family: Consolas, 'Courier New', monospace
- body: 20
- title: 36
- subtitle: 26
- annotation: 15
- cover_title: 88
- hero_number: 64
- chapter_opener: 56

## icons
- library: chunk-filled
- inventory: book, book-open, books, newspaper, sticky-note, printer, copy, brush, scissors, pencil, pen-nib, toolbox, map, map-pin, globe, calendar, clock, heart, star, flag, arrow-right, circle-arrow-right, building, home, shopping-bag, folders, grid, hand, users

## images
- cover_hero: images/cover_hero.png
- zine_history_collage: images/zine_history_collage.png
- risograph_machine: images/risograph_machine.png
- risograph_process_banner: images/risograph_process_banner.png
- zine_folding_hands: images/zine_folding_hands.png
- jimbocho_hero: images/jimbocho_hero.png
- three_cities_triptych: images/three_cities_triptych.png
- berlin_bucherbogen: images/berlin_bucherbogen.png
- zine_fair_scene: images/zine_fair_scene.png
- zine_action_outro: images/zine_action_outro.png

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: breathing
- P10: dense
- P11: breathing
- P12: dense
- P13: dense
- P14: dense
- P15: dense
- P16: breathing
- P17: anchor
- P18: anchor

## page_charts
- P02: agenda_list
- P04: timeline
- P05: vertical_list
- P06: numbered_steps
- P07: numbered_steps
- P08: icon_grid
- P10: vertical_pillars
- P12: basic_table
- P13: labeled_card
- P14: vertical_list
- P15: vertical_list
- P16: numbered_steps

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`
- Card border-radius > 0 (Risograph 美学 = 硬边、无圆角)
