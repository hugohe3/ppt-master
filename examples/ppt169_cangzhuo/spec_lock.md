# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #F5F1E8
- secondary_bg: #EFEAD9
- primary: #1A1A1A
- accent: #A52A2A
- text: #1A1A1A
- text_secondary: #5C5852
- text_tertiary: #8B8680
- border: #C8C0AE
- image_rendering: ink-notes
- image_palette: mono-ink

## typography
- font_family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif
- title_family: KaiTi, Georgia, serif
- body_family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif
- emphasis_family: KaiTi, Georgia, serif
- code_family: Consolas, "Courier New", monospace
- body: 24
- title: 40
- subtitle: 32
- cover_title: 80
- chapter_title: 60
- hero_quote: 48
- annotation: 18
- footer: 14

## icons
- library: tabler-outline
- stroke_width: 1.5
- inventory: quote, eye-off, sword, shield, hourglass, mountain, heart, point

## images
- cover_bg: images/cover_bg.png
- yinzi_bg: images/yinzi_bg.png
- hanxin_bridge: images/hanxin_bridge.png
- qianlong_pool: images/qianlong_pool.png
- zengguofan_lamp: images/zengguofan_lamp.png
- closing_mountain: images/closing_mountain.png

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense
- P04: dense
- P05: breathing
- P06: dense
- P07: dense
- P08: anchor
- P09: dense
- P10: breathing
- P11: dense
- P12: anchor
- P13: dense
- P14: anchor

## page_charts
- P11: pros_cons_chart
- P13: vertical_list

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text — write as raw Unicode; XML reserved chars escaped as `&amp; &lt; &gt; &quot; &apos;`
