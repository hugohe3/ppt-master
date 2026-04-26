# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values NOT listed here must NOT appear in SVGs.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #F7F2E8
- bg_secondary: #EDE5D3
- primary: #6B9AAE
- accent: #C99E62
- secondary_accent: #6F8F75
- accent_2: #B04A5C
- text: #3A3530
- text_secondary: #7A7068
- text_tertiary: #9B948B
- border: #D7CEB9

## typography
- font_family: "KaiTi", "STKaiti", "Microsoft YaHei", "PingFang SC", Georgia, serif
- cover_title: 66
- chapter_title: 50
- content_title: 36
- subtitle: 26
- body: 22
- annotation: 18
- page_number: 13

## icons
- library: tabler-filled
- inventory: leaf, flower, droplet, palette, book, heart, sparkles, moon, paint, quote

## images
- chunwan_stage: images/640.png
- zhanpao_portrait: images/640_4.png
- diaoyan_collab: images/640.jpg
- daolian_scroll: images/640_1.png
- ruyao_bowl: images/640_5.png
- yuguo_tianqing_silk: images/640_1.jpg
- cang_huang: images/640_6.png
- mu_yun_hui: images/640_7.png
- tian_shui_bi: images/640_8.png
- yin_hong_silk: images/640_10.png
- ba_wang_bie_ji: images/640_11.png
- dai_qing: images/640_12.png
- xiang_si_hui: images/640_13.png
- ranliao_zhiwu: images/640_14.png
- ranse_process: images/640_15.png
- meng_hua_lu: images/640_17.png
- xuetao_paper: images/640_18.png

## color_tokens
- 雨过天青: #7AA4B6
- 苍黄: #B29A55
- 暮云灰: #7D6E74
- 天水碧: #8FB09A
- 银红: #E49AA5
- 酡色: #C86868
- 黛青: #3D4A5A
- 相思灰: #A69E98

## forbidden
- Mixing icon libraries (locked to tabler-filled)
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
