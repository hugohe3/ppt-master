---
deck_id: 中国电信
kind: deck
category: brand
summary: 中国电信政企数字化方案、转型规划与内部评审，用于说明方案并对齐决策和下一步；采用克制的红灰品牌视觉。
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

| Application contract | Definition |
| --- | --- |
| Recurring presentation family | 政企数字化方案、转型规划、内部评审和客户汇报 |
| Intended audiences and outcomes | 面向政企客户决策者、项目干系人与内部评审者；帮助受众理解背景与方案、形成判断，并明确下一步 |
| Delivery and reading assumptions | 以会议讲解为主，同时需要会后流转和复核；页面应保留关键结论与必要证据，不依赖口头说明才能辨认主题 |
| Stable narrative/page roles | 必需封面；可选目录与章节页；正文页可重复；需要正式收束时使用结束页。具体论证顺序由当前项目的沟通契约决定 |
| Content reuse boundary | Logo、品牌口号与固定品牌图形可保留；项目标题、目录、章节名、正文、数据、来源和联系信息必须替换；原型中的示例文字不得进入成品 |

- 视觉基调为白底、通信红结构条、银灰内容承载区与少量城市线稿，强调权威、清晰和克制。
- 结构上分为两个可复用 Master 家族：China Telecom Brand 服务封面、章节与收尾，China Telecom Content 服务目录与正文；它们按视觉体系分工，不是按单个 Layout 拆分出的重复 Master。

## II. Color Scheme

| Role | Color | Application |
| --- | --- | --- |
| Telecom red | #C00000 | 页眉胶囊、编号、分隔线和关键强调 |
| Silver gray | #D9D9D9 | 页眉结构带 |
| Panel gray | #F8FAFC | 内容承载区与品牌卡片 |
| Graphite | #111827 | 标题和关键文字 |
| Muted gray | #6B7280 | 辅助说明与页脚 |
| White | #FFFFFF | Master 背景与反白文字 |

## III. Typography

| Role | Font stack | Application |
| --- | --- | --- |
| Chinese title and body | `"Microsoft YaHei", "PingFang SC", Arial, sans-serif` | 标题、正文、目录项与中文品牌说明 |
| Latin label and folio | `Arial, "Microsoft YaHei", sans-serif` | 英文标识、日期与页码 |

字体栈仅使用常见系统字体；Windows 优先微软雅黑，macOS 可回退苹方，不依赖额外字体安装。

## IV. Signature Design Elements

- 内容页和目录页使用“红色胶囊 + 银灰长带”的页眉结构，右侧保留横向品牌图形。
- 封面、章节页和结束页复用红色口号、城市线稿与底部红色飘带，但控制在独立品牌卡片中。
- China Telecom Brand Master 统一承载白底、顶部红线、底部品牌飘带与英文标识；China Telecom Content Master 统一承载红灰页眉、横向品牌标识和页脚分隔线。
- 内容承载区采用浅灰圆角面板；实际内容由边界完整的 `object` slot（PowerPoint 内容占位区域）承载，不显示提示性虚线。
- 标题与通用内容保持左对齐；只在品牌图形内部使用居中构图。

## V. Page Roster

| File | Master | Layout key | PowerPoint picker name | Visual character | Reusable slots | Content policy |
| --- | --- | --- | --- | --- | --- | --- |
| `01_cover.svg` | China Telecom Brand | cover | Cover | 左侧标题簇、右侧品牌卡片、底部飘带 | 标题、副标题、单位、日期 | 必需起始页；品牌图形固定，演示标题信息全部替换 |
| `02_toc.svg` | China Telecom Content | agenda | Agenda | 左侧品牌说明卡、右侧四行编号目录 | 页面标题、四个目录项、页码 | 可选；目录项按当前叙事生成，不保留原型示例 |
| `03_chapter.svg` | China Telecom Brand | section | Section Header | 左侧章节信息、右侧品牌卡片、底部飘带 | 章节号、章节标题、章节副标题 | 可选且可重复；章节信息全部替换，品牌图形固定 |
| `04_content.svg` | China Telecom Content | content | Title and Content | 红灰页眉与大面积浅灰开放内容区 | 栏目标、页面标题、内容对象、来源、页码 | 可重复；承载当前项目事实、论证、数据或行动，所有内容均替换 |
| `05_ending.svg` | China Telecom Brand | closing | Closing | 左侧结束语、右侧品牌卡片、底部飘带 | 结束标题、副标题、联系信息、页码 | 可选收束页；品牌图形固定，结束语与联系信息按项目替换 |

## VI. Assets

| File | Intended usage |
| --- | --- |
| logo.png | 封面、章节页和结束页品牌标识 |
| header_brand.png | 目录页和内容页横向页眉标识 |
| footer_ribbon.png | 封面、章节页和结束页底部品牌飘带 |
| slogan_red.png | 右侧品牌卡片口号 |
| skyline_bg.png | 右侧品牌卡片城市线稿 |
| top_emblem.png | 保留的备用横向品牌资产 |
