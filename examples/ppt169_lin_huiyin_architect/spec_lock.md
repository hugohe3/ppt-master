# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values NOT listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.
>
> After SVG generation begins, this file is the canonical source for color / font / icon / image values. Modifications should go through `scripts/update_spec.py` so both this file and the generated SVGs stay in sync.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #1A1A2E
- bg_secondary: #16213E
- primary: #C9A96E
- accent: #E8D5B7
- secondary_accent: #8B6F47
- text: #E8E8E8
- text_secondary: #A0A0B0
- text_tertiary: #6B6B80
- border: #2A2A4A

## typography
- font_title: "KaiTi", Georgia, serif
- font_body: "Microsoft YaHei", Arial, sans-serif
- font_emphasis: "SimHei", Arial, sans-serif
- cover_title: 54
- chapter_title: 44
- title: 32
- subtitle: 28
- body: 22
- annotation: 16
- page_number: 12

## icons
- library: chunk
- inventory: building, castle, museum, map, compass-drafting, book-open, pen-nib, crown, star, flag, heart, eye, clock, globe

## images
- cover_bg: images/cover_bg.png
- lin_portrait: images/lin_portrait.png
- jihai_station_old: images/jihai_station_old.png
- jihai_station_new: images/jihai_station_new.png
- pku_geology: images/pku_geology.png
- yingqiu_院: images/yingqiu_院.png
- kunming_site: images/kunming_site.png
- babaoshan: images/babaoshan.png
- lin_tomb: images/lin_tomb.png
- monument: images/monument.png
- liang_lin_together: images/liang_lin_together.png
- first_paper: images/first_paper.png
- lin_survey: images/lin_survey.png
- lin_later: images/lin_later.png

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
