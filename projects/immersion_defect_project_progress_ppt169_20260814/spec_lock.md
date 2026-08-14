<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 项目周会管理层与工程负责人
- objective: 说明 61.4% 完成且关键路径在 hood 与边缘工程，并推动冻结阈值与 S02 的 8 小时 PM 窗口
- core_message: 工艺窗口超前，设备清洁 44%、边缘 39% 落后；D03/D04 在 8/21 前关闭可追回约 6 天
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
- inventory: tabler-outline/timeline, tabler-outline/tools, tabler-outline/checklist, tabler-outline/alert-triangle, tabler-outline/route, tabler-outline/chart-dots-3, tabler-outline/zoom-scan, tabler-outline/droplet, tabler-outline/target, tabler-outline/layers-intersect

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: breathing

## page_charts
- P04: progress_bar_chart
- P06: grouped_bar_chart

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
