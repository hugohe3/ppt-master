<!-- ppt-master-schema: design-spec/v1 -->
# 浸没式光刻缺陷能力建设项目进展 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 浸没式光刻缺陷能力建设项目进展 |
| Canvas Format | PPT 16:9（1280 × 720） |
| Page Count | 8 |
| Primary Language | zh-CN |
| Target Audience | 项目周会的管理层与工程负责人；需同时看完成率、关键路径和五项待决策 |
| Communication Intent | 说明 61.4% 完成、关键路径在 hood 与边缘工程，推动五项决策 |
| Desired Audience Outcome | 与会者承认工艺窗口超前不能掩盖设备/边缘落后，并当场处理冻结阈值与 S02 的 8 小时 PM 窗口 |
| Core Message / Ask / Action | 工艺窗口超前，设备清洁 44%、边缘 39% 落后；D03/D04 在 8/21 前关闭可追回约 6 天 |
| Delivery Context | 12 分钟主讲的项目周会；次要用于会后跟踪里程碑与决策闭环 |
| Artifact Afterlife | 作为当周完成率、工作包状态和五项决策的会后记录 |
| Reading Mode | balanced |
| Content Strategy | 可在不改变演示用虚构数据口径的前提下重组和可视化；机制名称保持文献词汇 |
| Design Style | 深色工程蓝图：技术图纸式网格、单线结构、尺寸标记与少量状态色 |
| Formula Policy | text-only |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — final Stage-2 proactive policy |
| Custom Animations | disabled — final Stage-2 proactive policy |
| Narration Audio | disabled — final Stage-2 proactive policy |
| Created Date | 2026-08-14 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 40 px |
| Content Area | x=40–1240，y=40–680；页标题下方保留统一技术标尺带 |

## III. Visual Theme

### Theme Style

- **Mode**: pyramid
- **Visual style**: blueprint
- **Theme**: 以暗色工程图纸为底，细网格和技术标注组织全篇；完成/可用青绿，风险琥珀，阻塞红。
- **Tone**: 专业、克制、可审计；像缺陷工程图纸而非营销页。

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #071827 | 主画布图纸底 |
| Secondary background | #0D2538 | 分区与标题栏 |
| Primary | #87D9F5 | 结构线与普通信息 |
| Accent | #32E0C4 | 完成、超前、正向 |
| Secondary accent | #FFB454 | 风险、落后、待决策 |
| Body text | #EAF7FF | 主体文本与关键数字 |
| Grid | #16384C | 背景网格 |
| Muted text | #8BA9B8 | 注释与来源 |
| Blocking | #FF6B6B | 明确阻塞与最高风险 |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | clean engineering sans / bold | Microsoft YaHei | Arial | 微软雅黑, sans-serif |
| Body | clean engineering sans / regular | Microsoft YaHei | Arial | 微软雅黑, sans-serif |
| Data | technical monospace | Consolas | Consolas | Microsoft YaHei, monospace |

- **Title stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- **Body stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- **Data stack**: `Consolas, "Microsoft YaHei", "微软雅黑", monospace`
- **Role rationale**: Data is recurring across completion rates, tool codes, PWP and dates.

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 24 |
| Title | 42 |
| Subtitle | 32 |
| Lead | 30 |
| Data | 20 |
| Annotation | 18 |
| Footnote | 16 |

## V. Layout Principles

### Page Structure

- **Header area**: 左上结论式标题；右上项目代号、数据日和页码坐标。
- **Content area**: 闭环架构、完成率条、工具对比或签批板做骨架；文字用引线挂上，不用卡片墙。
- **Footer area**: 含数字页标注“演示用虚构数据｜不代表真实工厂成绩”。

### Spacing Specification

| Element | Current Project |
| --- | --- |
| Safe margin | 40 px |
| Content block gap | 24–32 px |
| Icon-text gap | 12–16 px |

## VI. Icon Usage Specification

- **Primary bundled library**: tabler-outline
- **Stroke Width**: 2

| Icon Path | Suitable Scenarios |
| --- | --- |
| tabler-outline/timeline | 项目进度与里程碑 |
| tabler-outline/tools | 设备清洁与 PM 窗口 |
| tabler-outline/checklist | 决策签批 |
| tabler-outline/alert-triangle | 开放风险 |
| tabler-outline/route | 关键路径 |
| tabler-outline/chart-dots-3 | 完成率与相关性 |
| tabler-outline/zoom-scan | 检测策略 |
| tabler-outline/droplet | 水印 / ADI |
| tabler-outline/target | 资格包与目标 |
| tabler-outline/layers-intersect | 六工作包闭环 |

## VII. Visualization Reference List

| Page | Template | Usage |
| --- | --- | --- |
| P04 | progress_bar_chart | 六工作包完成率对照 |
| P06 | grouped_bar_chart | S01/S02/S03 的 PWP 对比 |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## IX. Content Outline

### Part 1: 本周判断

#### Slide 01 - 封面

- **Audience move**: 从“只知道项目在推进”到“先记住 61.4%，落后 3.8 点，短板在 hood 与边缘”。
- **Layout**: 左侧尺寸线框住 61.4%；右侧落后 3.8 点用琥珀刻度标出，关键路径指向 hood 与边缘，不用卡片墙。
- **Title**: 浸没式光刻缺陷能力建设项目进展
- **Core message**: 总体 61.4%、落后 3.8 点；工艺窗口超前，关键路径在设备清洁与边缘工程。
- **Content**: 副标题“DEF-193I-24｜数据日 2026-08-13｜阶段目标 2026-12-15”；英雄数字 61.4%；落后 3.8 个百分点；状态“D03/D04 8/21 前关闭可追回约 6 天”。
- **Cover impact**: 绑定钩子为“61.4% 看起来过半，真正拖期的是 44% 与 39% 两条路径”。
- **Data class: scenario**: 完成率、落后点和日期均为演示用虚构数据。

#### Slide 02 - 窗口超前，关键路径在 hood 与边缘

- **Audience move**: 形成对进展、能力、风险、决策的一页判断。
- **Layout**: 左主仪表总体完成；右四信号带：进展 / 能力 / 风险 / 决策，超前青绿、落后琥珀。
- **Title**: 窗口超前，关键路径在 hood 与边缘
- **Core message**: 工艺窗口与物料超前；设备清洁 44%、边缘 39% 构成关键路径。
- **Content**: 进展 61.4% / 落后 3.8 点；能力：窗口 88%、物料 81% 超前，检测 58% 偏差；风险：产能挤占 PM 窗口最高；决策：冻结阈值 + S02 的 8 小时 PM。
- **Data class: scenario**: 完成率与落后点为演示用虚构数据。

### Part 2: 结构与短板

#### Slide 03 - 能力由工艺、物料、检测、设备、边缘、HVM 六包闭环

- **Audience move**: 看懂能力不是单点改善，而是六包互相咬合。
- **Layout**: 中央闭环骨架连接六工作包；工艺与物料落在已闭合弧，设备与边缘落在断开弧，HVM 标为未到窗口。
- **Title**: 能力由工艺、物料、检测、设备、边缘、HVM 六包闭环
- **Core message**: 文献中的闭环是工艺窗口、物料规格、检测策略、设备清洁、边缘工程与 HVM 资格。
- **Content**: 六包名称绕环标注；当前缺口指向设备清洁与边缘工程；检测灵敏度未锁非图形–ADI 相关；HVM 22% 尚未进入窗口。
- **Native shape suggestion**: 环形闭环与六段弧，断开处用引线标关键路径。
- **Data class: scenario**: 包状态为演示用虚构设定。
- **Fact IDs**: F050

#### Slide 04 - 落后集中在设备清洁 44% 与边缘工程 39%

- **Audience move**: 把“总体过半”拆到具体落后包。
- **Layout**: 六条水平完成率轨，按完成率降序；44% 与 39% 用琥珀加长标注，22% 用虚线表示未到窗口。
- **Title**: 落后集中在设备清洁 44% 与边缘工程 39%
- **Core message**: 工艺 88%、物料 81% 超前；设备 44%、边缘 39% 落后，检测 58% 偏差。
- **Content**: 工艺窗口与叠层兼容 88% 超前；物料与化学品规格 81% 按期；检测灵敏度与监测策略 58% 偏差；设备清洁与浸没头健康 44% 落后；边缘工程 EBR/WEE 39% 落后；长期稳定性与 HVM 资格 22% 未到窗口。
- **Visualization**: 数据驱动完成率条；参考 P04 `progress_bar_chart`。
- **Native-ready**: no
- **Data class: scenario**: 六包完成率为演示用虚构数据。
- **Fact IDs**: F038, F050

#### Slide 05 - 非图形监控尚未锁住 ADI 水印

- **Audience move**: 看清检测工作包偏差的机制：相关性和 SNV 都未锁。
- **Layout**: 左相关刻度 0.62 对目标 0.80；右 SNV 从 28% 收到 22% 仍高于 15% 内控；底部一条 DSA 草稿未进 SPC 的虚线。
- **Title**: 非图形监控尚未锁住 ADI 水印
- **Core message**: 图形 ADI 捕获率 91% 可用；非图形与 ADI 水印相关仅 0.62，SNV 22% 仍污染复核。
- **Content**: ADI 捕获率样板基线 91%；Surfscan 类监控与 ADI 水印计数相关 0.62，目标 0.80；DSA 当前层/前层规则已草稿、未进 SPC；坐标补偿使 SNV 从 28% 降到 22%，内控 ≤15%。
- **Data class: scenario**: 相关性、SNV 与捕获率为演示用虚构数据。
- **Fact IDs**: F008, F024

#### Slide 06 - S02 PWP 仍是工具健康短板

- **Audience move**: 把设备落后从“浸没整体”收到 S02。
- **Layout**: 三台扫描机分组柱：PWP；S02 柱拉高到 27，S01/S03 贴近目标 12 的参考线。
- **Title**: S02 PWP 仍是工具健康短板
- **Core message**: S01=9、S03=11 在健康带；S02=27，上次台面清洁 2026-08-06，hood 气帘仍未复测。
- **Content**: PWP #/wafer：S01=9，S02=27，S03=11；S02 末镜 haze 相对 S01 高 1.8 倍；M5 in-situ cleaning 周期计划 8/20、预测 8/27，延后 7 天。
- **Visualization**: 数据驱动分组柱；参考 P06 `grouped_bar_chart`。
- **Native-ready**: no
- **Data class: scenario**: 工具 PWP 与日期为演示用虚构数据。
- **Fact IDs**: F023, F038

### Part 3: 风险与决策

#### Slide 07 - 产能挤占 PM 窗口是当前最高风险

- **Audience move**: 按影响排序风险，而不是平铺四条担忧。
- **Layout**: 四条风险轨按严重度从上到下；R01 用阻塞红拉满，R04 管理禁令用红线标出。
- **Title**: 产能挤占 PM 窗口是当前最高风险
- **Core message**: R01 高×高且开放；R04 需管理禁令，避免用 recipe 制造虚假 D0 回收。
- **Content**: R01 产能挤占 S02 hood PM，高/高，开放；R02 非图形–ADI 相关性锁不住，中/高，开放；R03 疏水 topcoat 降水分但抬高 blob，中/中，观察；R04 用 recipe 阈值制造虚假回收，中/高，需禁令。
- **Data class: scenario**: 风险评级为演示用虚构设定。
- **Fact IDs**: F027, F034, F042

#### Slide 08 - 冻结阈值并给出 S02 的 8 小时 PM 窗口

- **Audience move**: 带着五项可签批决策离开。
- **Layout**: 五项决策签批板，编号 D01–D05，横贯全宽；D01/D02 前置，D03–D05 对齐 8/21。
- **Title**: 冻结阈值并给出 S02 的 8 小时 PM 窗口
- **Core message**: 本周先冻 recipe、给 S02 八小时 PM；8/21 前关掉 EBR 试验与 SEM 机时，可追回约 6 天。
- **Content**: D01 冻结 W35 前 recipe 阈值，窗口 8/16；D02 S02 给 8 小时 PM 窗口，8/18；D03 批准 EBR 加宽 0.3 mm 试验，8/21；D04 增补 SEM 复核机时 20%，8/21；D05 若 W35 D0>0.24 则启动 hood 更换评估，8/21。
- **Data class: scenario**: 决策窗口与追回天数为演示用虚构设定。
- **Fact IDs**: F027, F038, F042

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 每页先说结论，再补证据；所有数字口头标明“演示数据”
- **Total duration**: 12 minutes
- **Notes style**: formal
- **Presentation purpose**: report
