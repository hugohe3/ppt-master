<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 光刻、缺陷、良率和设备工程师，以及当值经理
- objective: 说明本周 D0 上升是 S02 水印而非漏检，并推动冻结 recipe、关闭残液路径
- core_message: W33 L28 D0 升至 0.42/cm²，捕获率稳定，4 个 killer lot 全部来自 S02，先做浸没头/台面与后淋洗
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
- inventory: tabler-outline/droplet, tabler-outline/zoom-scan, tabler-outline/chart-column, tabler-outline/chart-funnel, tabler-outline/alert-triangle, tabler-outline/checklist, tabler-outline/chart-dots-3, tabler-outline/layers-intersect, tabler-outline/wave-sine, tabler-outline/circle-dot

## page_rhythm
- P01: anchor
- P02: anchor
- P03: dense
- P04: dense
- P05: anchor
- P06: dense
- P07: dense
- P08: breathing

## page_charts
- P04: pareto_chart
- P05: funnel_chart
- P06: grouped_bar_chart

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
