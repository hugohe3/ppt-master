# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #0E2A47
- bg_secondary: #1A3A5C
- primary: #5BA3E0
- accent: #FFB627
- secondary_accent: #3E7AB8
- text: #F0F4F8
- text_secondary: #A0B8D0
- text_tertiary: #6B85A3
- border: #2D4A6B
- success: #7FD99F
- warning: #FF6B6B

## typography
- font_family: Arial, "Microsoft YaHei", sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 18
- cover_title: 64
- chapter: 45
- title: 30
- hero_number: 36
- subtitle: 24
- annotation: 13
- footer_label: 11

## icons
- library: tabler-outline
- stroke_width: 1.5
- inventory: network, server, database, settings, refresh, cloud, cube, box, route, heartbeat, plug, device-floppy, stack, shield-check, arrow-right

## page_rhythm
- P01: anchor
- P02: dense
- P03: dense
- P04: dense
- P05: anchor
- P06: dense
- P07: dense
- P08: anchor
- P09: anchor
- P10: breathing

## page_charts
- P03: hub_spoke
- P05: process_flow
- P06: vertical_pillars
- P09: client_server_flow

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;` …); raw Unicode only; XML reserved chars escaped as `&amp; &lt; &gt; &quot; &apos;`
