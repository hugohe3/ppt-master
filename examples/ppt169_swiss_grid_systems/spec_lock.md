# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFFFFF
- secondary_bg: #F4F4F4
- primary: #1A1A1A
- accent: #D9251D
- secondary_accent: #1A4FA0
- text: #1A1A1A
- text_secondary: #666666
- text_tertiary: #999999
- border: #E8E8E8
- image_rendering: minimalist-swiss
- image_palette: mono-ink

## typography
- font_family: Arial, "Microsoft YaHei", sans-serif
- title_family: "Arial Black", "Microsoft YaHei", sans-serif
- body_family: Arial, "Microsoft YaHei", sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 18
- title: 32
- subtitle: 22
- annotation: 13
- cover_title: 84
- hero_number: 36
- display_xl: 92
- specimen: 240

## icons
- library: tabler-outline
- stroke_width: 1.5
- brand_library: simple-icons
- inventory: blockquote, grid-3x3

## images
- cover_bg: images/cover_bg.png
- negative_space: images/negative_space.png
- closing_grid: images/closing_grid.png

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: anchor
- P10: breathing
- P11: dense
- P12: dense
- P13: dense
- P14: breathing

## page_charts
- P03: timeline
- P04: vertical_list
- P05: team_roster
- P06: timeline
- P07: comparison_columns
- P08: quadrant_text_bullets
- P11: icon_grid
- P12: numbered_steps
- P13: icon_grid

## forbidden
- Mixing icon libraries
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- HTML named entities in text — write as raw Unicode; XML reserved chars must be escaped as `&amp; &lt; &gt; &quot; &apos;`
- Rounded corners (rx > 0) — except inside `simple-icons` brand glyphs
- Linear/radial gradients — pure flat color only
- Drop shadows / filter effects
