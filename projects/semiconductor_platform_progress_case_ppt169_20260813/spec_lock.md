<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 公司管理层，以及研发、工程、采购、EHS负责人
- objective: 说明平台建设阶段、能力形成和关键阻塞，使管理层能够确认未来90天行动及五项资源决策
- core_message: 项目总体完成68.6%，按节点关闭关键阻塞并及时决策，可追回7–10天并维持2026年12月15日阶段验收目标
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
- inventory: tabler-outline/building-factory-2, tabler-outline/circuit-resistor, tabler-outline/timeline, tabler-outline/tools, tabler-outline/shield-check, tabler-outline/alert-triangle, tabler-outline/route, tabler-outline/database, tabler-outline/chart-dots-3, tabler-outline/checklist

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: dense
- P06: anchor
- P07: dense
- P08: dense
- P09: dense
- P10: dense
- P11: breathing

## page_charts
- P04: progress_bar_chart
- P06: funnel_chart
- P07: heatmap_chart
- P10: roadmap_vertical

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
