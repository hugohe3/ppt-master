# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values NOT listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.
>
> After SVG generation begins, this file is the canonical source for color / font / icon / image values. Modifications should go through `scripts/update_spec.py` so both this file and the generated SVGs stay in sync.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

> Strategist: fill the viewBox and format for the chosen canvas. Common values: `0 0 1280 720` (PPT 16:9), `0 0 1024 768` (PPT 4:3), `0 0 1242 1660` (Xiaohongshu), `0 0 1080 1080` (WeChat Moments), `0 0 1080 1920` (Story).

## colors
- bg: #FFFFFF
- primary: #......
- accent: #......
- secondary_accent: #......
- text: #......
- text_secondary: #......
- border: #......

> Strategist: fill only the colors actually used in this deck. Extra rows may be added; unused rows should be deleted rather than left as `#......`.

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- title: 32
- subtitle: 24
- body: 22
- annotation: 14

> Sizes are in px, matching SVG native units. `font_family` is a CSS font-stack string.

## icons
- library: chunk
- inventory: target, bolt, shield, users, chart-bar, lightbulb

> `library` MUST be one of `chunk` / `tabler-filled` / `tabler-outline` (exactly one — mixing is forbidden). `inventory` lists the approved icon names (without library prefix); Executor may only use icons from this list.

## images
- cover_bg: images/cover_bg.jpg

> One entry per image file actually used. Remove the section entirely if the deck uses no images.

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
