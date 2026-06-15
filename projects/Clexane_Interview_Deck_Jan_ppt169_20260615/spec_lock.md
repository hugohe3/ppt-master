# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFFFFF
- secondary_bg: #F5F5F5
- primary: #AE232F
- dark_red: #8A1B25
- light_red: #F9E5E7
- text: #1A1A1A
- text_secondary: #555555
- text_tertiary: #888888
- border: #E0E0E0

## typography
- font_family: Arial, sans-serif
- body: 18
- title: 34
- subtitle: 24
- annotation: 14
- cover_title: 72
- footer: 12

## icons
- library: tabler-filled
- inventory: school, briefcase, heart, flask, clipboard-check, shield-check, hospital-circle, user, star, search, message, medical-cross, eye, circle-check, award, book, trophy

## images
- photo_jan.png: images/photo_jan.png | no-crop

## page_rhythm
- P01: anchor
- P02: dense
- P03: dense
- P04: dense
- P05: dense
- P06: breathing

## page_charts
- P01: labeled_card
- P02: vertical_pillars
- P03: basic_table
- P04: chevron_process
- P05: pros_cons_chart

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;`) — write as raw Unicode (—, ©, →, etc.); XML reserved chars & < > " ' must be escaped as `&amp; &lt; &gt; &quot; &apos;`
