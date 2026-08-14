<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 良率与工艺专项决策会
- objective: 说明 D0 从 0.51 收到 0.29、剩余 0.09 挂在后淋洗与 hood，并推动按 D0、PWP、捕获率签批 W35 释放
- core_message: 真实工艺/设备回收约 0.16；W32 recipe 回退使表观 D0 回升；剩余靠 hood 气帘与 EBR，禁止把 recipe 收热算作回收
- consumption_mode: balanced

## mode
- mode: pyramid

## visual_style
- visual_style: blueprint

## colors
- background: #071827
- secondary_bg: #0D2538
- primary: #87D9F5
- accent: #32E0C4
- secondary_accent: #FFB454
- body_text: #EAF7FF
- grid: #16384C
- muted_text: #8BA9B8
- blocking: #FF6B6B

## typography
- font_family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif
- title_family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif
- body_family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif
- data_family: Consolas, "Microsoft YaHei", "微软雅黑", monospace
- body: 24
- title: 42
- subtitle: 32
- lead: 30
- data: 20
- annotation: 18
- footnote: 16

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: tabler-outline/target, tabler-outline/adjustments, tabler-outline/droplet, tabler-outline/chart-column, tabler-outline/activity, tabler-outline/filter, tabler-outline/checklist, tabler-outline/alert-triangle, tabler-outline/timeline, tabler-outline/chart-dots-3

## page_rhythm
- P01: anchor
- P02: anchor
- P03: dense
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: breathing

## page_charts
- P03: waterfall_chart
- P06: line_chart

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
