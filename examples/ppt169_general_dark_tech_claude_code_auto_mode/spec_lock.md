# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values NOT listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #0D1117
- bg_secondary: #161B22
- card_bg: #1C2333
- primary: #D4A574
- accent: #60A5FA
- secondary_accent: #34D399
- text: #E6EDF3
- text_secondary: #8B949E
- text_tertiary: #6E7681
- border: #30363D
- success: #34D399
- warning: #F97316

## typography
- font_family: "Arial", "Calibri", "Helvetica", sans-serif
- cover_title: 54
- title: 40
- content_title: 30
- subtitle: 24
- body: 18
- annotation: 14
- page_number: 11

## icons
- library: chunk
- inventory: shield-check, terminal, eye, filter, bug, lock-closed, layers, chart-bar, circle-checkmark, robot, bolt, target, key, arrow-trend-up, code, eye-slash, server, gauge-high

## images
- fig1_permissions: images/image.png
- fig2_architecture: images/image_1.png
- fig3_classifier: images/image_2.png
- fig4_pipeline: images/image_3.png

## page_rhythm
- P01: anchor
- P02: breathing
- P03: breathing
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: dense
- P10: anchor

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
