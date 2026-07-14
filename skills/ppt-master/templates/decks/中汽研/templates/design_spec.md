---
deck_id: 中汽研
kind: deck
category: brand
summary: 中汽研认证展示、技术交流与业务来访场景的深蓝专业模板。
keywords: [中汽研, 认证, 评测, 技术交流]
primary_color: "#004098"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
source_canvas_width: 1280
source_canvas_height: 720
source_viewbox: "0 0 1280 720"
replication_mode: fidelity
native_structure_mode: structured
page_count: 5
---

# 中汽研 — Design Specification

## I. Template Overview

- 适用于产品认证展示、评测汇报、技术推广和业务来访。
- 视觉以中汽研深蓝、白底内容页、方形章节编号和简洁网格为识别核心，强调专业、可信和工程秩序。
- 整套模板使用 CATARC Dark 与 CATARC Light 两个 Master，并提供五个可直接从 PowerPoint 布局库调用的 Layout。

## II. Color Scheme

| Role | Color | Application |
| --- | --- | --- |
| CATARC blue | #004098 | 深色页面背景、章节编号块、结构线 |
| Deep blue | #003B82 | 封面背景 |
| Panel gray | #F8FAFC | 内容承载区 |
| Border gray | #E0E0E0 | 分隔线和面板边界 |
| Primary text | #333333 | 内容页标题和正文 |
| White | #FFFFFF | 深色页面文字与 Master 背景 |

## IV. Signature Design Elements

- 白底内容页使用“蓝色方形章节号 + 左对齐标题 + 右上角 Logo”的稳定页眉。
- 封面、章节页和结束页保留深蓝底、低透明度圆形与细网格，但删除无内容价值的复杂渐变和动态图片依赖。
- CATARC Dark Master 统一承载深蓝背景和上下结构线；章节页与结束页各自保留原稿中的圆形几何，封面不继承圆形。CATARC Light Master 统一承载白底、章节号方块、页眉 Logo、分隔线和底部蓝线。
- 目录页延续数字与双竖线的行式导航，并保留右侧独立数据对象区。
- 通用内容对象从框体左上角开始；封面、章节页、结束页以及小型章节号属于短焦点内容，允许在完整占位框中居中。

## V. Page Roster

| File | Master | Layout key | PowerPoint picker name | Visual character | Reusable slots |
| --- | --- | --- | --- | --- | --- |
| (01_cover.svg) | CATARC Dark | cover | Cover | 深蓝背景、居中大型 Logo 与标题簇 | 标题、副标题、单位、英文单位 |
| (02_toc.svg) | CATARC Light | agenda | Agenda | 数字双竖线目录、右侧数据面板 | 页面标题、五个目录项、数据对象、页码 |
| (03_chapter.svg) | CATARC Dark | section | Section Header | 深蓝章节页、居中章节号和标题 | 章节号、章节标题、章节副标题 |
| (04_content.svg) | CATARC Light | content | Title and Content | 方形章节号页眉与开放内容面板 | 章节号、页面标题、内容对象、页码 |
| (05_ending.svg) | CATARC Dark | closing | Closing | 深蓝网格背景、居中 Logo 与结束语 | 结束标题、英文副标题、联系信息、页脚 |

## VI. Assets

| File | Intended usage |
| --- | --- |
| 大型 logo.png | 封面和结束页主标识 |
| 右上角 logo.png | 目录页和内容页页眉标识 |
