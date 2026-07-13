---
deck_id: 中国电信
kind: deck
category: brand
summary: 中国电信政企数字化、转型规划与内部汇报的克制红灰品牌模板。
keywords: [中国电信, 政企, 数字化, 企业汇报]
primary_color: "#C00000"
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

# 中国电信 — Design Specification

## I. Template Overview

- 适用于政企数字化方案、转型规划、内部评审和客户汇报。
- 视觉基调为白底、通信红结构条、银灰内容承载区与少量城市线稿，强调权威、清晰和克制。
- 整套模板使用 China Telecom Brand 与 China Telecom Content 两个 Master，并提供五个可直接从 PowerPoint 布局库调用的 Layout。

## II. Color Scheme

| Role | Color | Application |
| --- | --- | --- |
| Telecom red | #C00000 | 页眉胶囊、编号、分隔线和关键强调 |
| Silver gray | #D9D9D9 | 页眉结构带 |
| Panel gray | #F8FAFC | 内容承载区与品牌卡片 |
| Graphite | #111827 | 标题和关键文字 |
| Muted gray | #6B7280 | 辅助说明与页脚 |
| White | #FFFFFF | Master 背景与反白文字 |

## IV. Signature Design Elements

- 内容页和目录页使用“红色胶囊 + 银灰长带”的页眉结构，右侧保留横向品牌图形。
- 封面、章节页和结束页复用红色口号、城市线稿与底部红色飘带，但控制在独立品牌卡片中。
- China Telecom Brand Master 统一承载白底、顶部红线、底部品牌飘带与英文标识；China Telecom Content Master 统一承载红灰页眉、横向品牌标识和页脚分隔线。
- 内容承载区采用浅灰圆角面板；实际内容由完整 object 占位框承载，不显示提示性虚线。
- 标题与通用内容保持左对齐；只在品牌图形内部使用居中构图。

## V. Page Roster

| File | Master | Layout key | PowerPoint picker name | Visual character | Reusable slots |
| --- | --- | --- | --- | --- | --- |
| (01_cover.svg) | China Telecom Brand | cover | Cover | 左侧标题簇、右侧品牌卡片、底部飘带 | 标题、副标题、单位、日期 |
| (02_toc.svg) | China Telecom Content | agenda | Agenda | 左侧品牌说明卡、右侧四行编号目录 | 页面标题、四个目录项、页码 |
| (02_chapter.svg) | China Telecom Brand | section | Section Header | 左侧章节信息、右侧品牌卡片、底部飘带 | 章节号、章节标题、章节副标题 |
| (03_content.svg) | China Telecom Content | content | Title and Content | 红灰页眉与大面积浅灰开放内容区 | 栏目标、页面标题、内容对象、来源、页码 |
| (04_ending.svg) | China Telecom Brand | closing | Closing | 左侧结束语、右侧品牌卡片、底部飘带 | 结束标题、副标题、联系信息、页码 |

## VI. Assets

| File | Intended usage |
| --- | --- |
| logo.png | 封面、章节页和结束页品牌标识 |
| header_brand.png | 目录页和内容页横向页眉标识 |
| footer_ribbon.png | 封面、章节页和结束页底部品牌飘带 |
| slogan_red.png | 右侧品牌卡片口号 |
| skyline_bg.png | 右侧品牌卡片城市线稿 |
| top_emblem.png | 保留的备用横向品牌资产 |
