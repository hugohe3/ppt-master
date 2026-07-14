# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFF8EE
- bg_secondary: #FFE9C7
- primary: #FF3DA5
- accent: #00B8D9
- secondary_accent: #FFD93D
- tertiary_accent: #00C896
- quaternary_accent: #FF6B4A
- text: #1A1A2E
- text_secondary: #5C5C7A
- border: #1A1A2E
- success: #00C896
- warning: #FF6B4A
- image_rendering: flat
- image_palette: vivid-launch

## typography
- font_family: Arial, "Microsoft YaHei", "PingFang SC", sans-serif
- title_family: Impact, "Arial Black", "Microsoft YaHei", sans-serif
- body_family: Arial, "Microsoft YaHei", "PingFang SC", sans-serif
- emphasis_family: Impact, "Microsoft YaHei", sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 20
- title: 40
- subtitle: 30
- annotation: 15
- cover_title: 96
- chapter_hero: 200
- chapter_title: 64
- hero_number: 140

## icons
- library: chunk-filled
- inventory: calendar, music, microphone, users, clock, bolt, heart, star, map-pin, sun, sparkles, headphones, shopping-bag, game-controller, ticket, gift, arrow-right

## images
- cover_bg: images/cover_bg.png
- ch1_what: images/ch1_what.png
- ch2_who: images/ch2_who.png
- headliners: images/headliners.png
- ch3_where: images/ch3_where.png
- ch4_vibes: images/ch4_vibes.png
- market: images/market.png
- installation: images/installation.png
- closing: images/closing.png

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense
- P04: dense
- P05: breathing
- P06: dense
- P07: dense
- P08: breathing
- P09: dense
- P10: dense
- P11: breathing
- P12: dense
- P13: dense
- P14: anchor

## page_charts
- P03: kpi_cards
- P04: vertical_pillars
- P06: icon_grid
- P07: quadrant_text_bullets
- P09: hub_spoke
- P10: timeline
- P12: comparison_columns
- P13: comparison_columns

## forbidden
- Mixing icon libraries
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`. See shared-standards.md §1.0
