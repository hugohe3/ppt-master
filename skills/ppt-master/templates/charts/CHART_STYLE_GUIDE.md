# Chart Template Authoring Guide

`templates/charts/` 的模板负责可视化结构、数据编码和信息关系，不负责最终项目风格。模板必须保持源码可读、独立可渲染，并允许 Executor 根据项目 Design Spec 与 `spec_lock.md` 重做字体、配色和装饰。

## 0. 上游规范

**Hard rule**: 本指南只定义 Chart 模板库的结构与中性预览合同。通用 SVG 语法、效果、原生数据接口和 PowerPoint 结构分别由以下权威文件定义：

| 合同 | 权威文件 |
|---|---|
| 通用 SVG | [`shared-standards.md`](../../references/shared-standards.md) |
| 效果与兼容输入 | [`svg-effects.md`](../../references/svg-effects.md) |
| Native Chart/Table | [`native-data-interface.md`](../../references/native-data-interface.md) |
| 画布格式 | [`canvas-formats.md`](../../references/canvas-formats.md) |

**Forbidden — second SVG specification**: 不在本指南复述或放宽上游语法。发生冲突时以上游权威文件为准。

---

## 1. 所有权边界

### 1.1 模板与项目

| Chart 模板拥有 | 项目拥有 |
|---|---|
| 可视化类型与数据到图形的映射 | 项目字体与字号体系 |
| 节点、连接、轴、系列和标签关系 | 项目调色板与品牌色 |
| 可视化类型、构图骨架和阅读顺序 | 实际分组、框架数量、项目数量与容量适配 |
| 必要的状态与语义区分 | 页面背景、页头、页脚和品牌 chrome |
| 独立预览所需的中性样式 | 最终强调策略与页面级视觉层级 |

**Hard rule**: Executor 适配模板时保留可视化类型、信息关系和数据准确性；最终视觉必须来自当前项目，而不是继承模板的示例审美。

**Reference — not a constraint**: 模板的分组、框架数、项目数和示例容量用于展示结构，不是项目上限。Executor 可按实际内容调整，但不能改变已选可视化类型、关系或数据语义。

### 1.2 保留判断

对每个视觉元素按顺序判断：

| 判断 | 处理 |
|---|---|
| 删除后会改变数据含义、关系、状态或阅读顺序 | 保留 |
| 删除后会弱化分组、层级、边界或文本容量 | 保留结构表达；只简化不承载信息的样式层 |
| 只让示例显得更精致、立体、品牌化或“高级” | 作为简化候选；通过文本与前后渲染核对后再删除 |
| 只对某个项目风格成立 | 交给 Executor 重建 |

**Default — structure first (may override when semantics require it)**: 优先使用清楚的线、面、标签和留白。装饰不能成为理解结构的前提。

### 1.3 保真优先

**Hard rule — fidelity before slimming**: 模板瘦身不得改写或删除原有可见标题、标签、说明、数值、单位、状态、来源、顺序、容量和关系。占位内容保持原文；只有明确重复的信息可以删除，并记录理由。

**Hard rule — structural frames survive**: 框线、底色、分隔、标签页或面板只要表达真实的信息单元、父子层级、阶段范围、绘图区或输出区，就属于结构。可以减少叠加效果，但不得为了 token 数字把有效层级压平。

**Forbidden — compression by rewriting**: 不用缩写、概括、换词或删句降低 token。体积优化来自属性继承、重复样式合并和非语义效果简化，不来自内容编辑。

---

## 2. 中性预览

### 2.1 独立可渲染

**Hard rule**: 每个模板保持完整 `<svg>`、`viewBox="0 0 1280 720"` 和一个直接的白色全画布背景，使文件无需外部样式即可打开审阅。

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720"
     font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif">
    <rect width="1280" height="720" fill="#FFFFFF"/>
    <!-- semantic content -->
</svg>
```

白色背景是预览基线，不是项目背景指令。Executor 必须按当前页面风格处理最终背景。

### 2.2 中性参考色

以下色值只保证模板独立展示时清晰。它们不是最终项目调色板：

| 角色 | 中性参考值 | 使用边界 |
|---|---|---|
| 主文本 | `#0F172A` | 标题、关键值 |
| 正文 | `#475569` | 描述、图例 |
| 次文本 | `#64748B` | 轴标签、辅助说明 |
| 弱线 | `#CBD5E1` / `#E2E8F0` | 网格、边界、分隔 |
| 参考强调 | `#2563EB` | 第一系列、当前状态或结构焦点 |
| 正向语义 | `#059669` | 仅表示上升、完成、达标 |
| 负向语义 | `#E11D48` | 仅表示下降、异常、未达标 |
| 警示语义 | `#D97706` | 仅表示风险或待处理 |

**Hard rule**: 多系列数据必须可区分；正负、完成/计划等语义状态必须可辨认。颜色承担这些信息时保留，颜色只承担装饰时移除。

**Forbidden — fixed catalog palette**: 不要求每个卡片、步骤或能力点使用不同 Tailwind hue。项目配色不从模板示例反向推导。

### 2.3 页面 chrome

| 元素 | 模板行为 |
|---|---|
| 标题/副标题 | 可用简短占位文本展示层级和可用空间；不附带装饰条、徽章或品牌图形 |
| 数据来源 | 仅当该可视化结构需要来源/脚注槽时保留；不是每个模板的固定页脚 |
| 页码、Logo、部门名 | 省略 |
| 进度徽章、状态胶囊 | 只有状态本身属于信息时保留，移除纯装饰外壳 |

---

## 3. 装饰与效果

### 3.1 减少冗余效果

**Default — one clear treatment (may override when structure requires depth)**: 中性模板避免阴影、发光、纹理、渐变和多层框同时叠加；保留能帮助读者识别真实边界、重叠或空间关系的最少效果。

| 效果 | 默认 | 允许条件 |
|---|---|---|
| 阴影/filter | 有描边或底色已能分组时省略 | 重叠、浮层或空间深度本身属于结构 |
| 渐变 | 只承担审美时可换成实色 | 连续色阶、流量、深度面或方向确实承载编码 |
| 透明光晕 | 省略 | 透明度本身编码范围或不确定性 |
| 圆角卡片 | 保留真实信息单元的一层边界 | 圆角值与最终外观由项目适配 |
| 图标底板 | 非默认 | 需要明确图标槽位或状态边界 |

**Hard rule**: Heatmap 色阶、Sankey 流量宽度、系列区分、Isometric 面向关系和真实模块边界属于信息编码或结构。普通卡片阴影、气泡高光、无含义色带和不承担顺序的大号淡色编号通常不属于；删除前仍需确认没有弱化层级。

### 3.2 容器克制

**Hard rule**: 每个真实信息单元保留至少一种清楚的边界表达：留白、分隔线、描边或底色。通常只需一种；父级区域与子级内容确实表达两个层级时可以保留两层。不要同时叠加无语义的描边、阴影、渐变和多层圆角框。

**Reference — not a constraint**: 项目最终可能采用强装饰风格。那是 Executor 根据 Design Spec 重建的项目决策，不是共享模板的默认形态。

---

## 4. 源码可读性与体积

### 4.1 语义压缩

**Hard rule**: 缩小模板时保留正常换行、缩进、语义 `id` 和必要分区注释。压缩目标是减少重复信息，不是把 XML 变成一行。

| 做法 | 要求 |
|---|---|
| 字体继承 | 公共 `font-family` 放在根 `<svg>` 或清楚的父 `<g>` |
| 属性继承 | 同组重复的 `fill`、`stroke`、字号或锚点可提升到父组 |
| 注释 | 保留结构、语义和机器标记；删除色名、营销解释和重复说明 |
| 文本 | 普通单行直接写在 `<text>`；只有多 run/多行需要 `<tspan>` |
| 坐标 | 页面坐标使用必要精度；按上游合同运行 `compact_svg_coordinates.py` |
| ID | 使用 `chart-area`、`series-1`、`card-1` 等结构名称，避免示例业务名 |

### 4.2 禁止的压缩

**Forbidden — opaque source**:

- 单行 minify、随机缩写 ID 或删除结构注释。
- 为省字符把核心构图拆成难以追踪的深层 `<symbol>/<use>` 图。
- 把模板必要信息藏进外部 CSS、脚本或未登记依赖。
- 用 Base64、压缩字符串或生成器说明替代可读的可视几何。

静态同文档 `<use>` 只在重复原语保持清晰、且满足上游条件合同时使用；它不是默认瘦身手段。

### 4.3 文本可读性

| 角色 | 中性范围 |
|---|---|
| 页面标题 | `30–36`，`700–800` |
| 区域标题 | `18–24`，`600–700` |
| 正文/标签 | `13–16` |
| Caption/轴刻度 | `12–14` |

**Hard rule**: 所有文本 `font-size >= 12`，使用有限无单位数值。需要成为一个 PowerPoint 文本框的多格式逻辑行使用一个 `<text>` 加非定位 `<tspan>`；独立文本框使用独立 `<text>`。

---

## 5. 结构与边界

### 5.1 语义分组

**Hard rule**: 使用描述性顶层 `<g id>` 表达页面级逻辑单元，例如 Header、Chart、Legend、Card Grid 或 Process。不要为每条文字、图标或数据点建立一个直属根组。

| 顶层组 | 典型内容 |
|---|---|
| `header` | 标题与副标题 |
| `chart-area` / replacement carrier | 轴、数据系列、标签、必要 metadata |
| `legend` | 系列或状态说明 |
| `card-1` / `feature-card-1` | 一个完整信息单元 |
| `timeline-track` | 时间轴与阶段标签 |
| `milestone-cards` | 同一结构的一组里程碑卡片 |

### 5.2 `data-pptx-bounds`

**Hard rule**: 每个可见直属根 `<g>` 都声明正数、根坐标系的 `data-pptx-bounds="x y width height"`。即使该组已有 native chart/table frame，也保留 bounds。

```xml
<g id="header" data-pptx-bounds="60 40 1160 72">
    <text x="60" y="74" font-size="32">Title</text>
</g>

<g id="card-1" data-pptx-bounds="60 150 560 250">
    <!-- complete card -->
</g>
```

| 边界要求 | 行为 |
|---|---|
| 坐标系 | 使用根 `viewBox` 坐标，不使用局部 transform 后坐标 |
| 范围 | 覆盖该逻辑单元允许使用的布局子画布，不从示例文字紧包围盒推断 |
| 精度 | 最多两位小数 |
| 嵌套组 | 不写；Checker 忽略嵌套 bounds |
| 背景/defs | 直接背景 primitive 与非可见定义不需要 bounds |

**Forbidden — bounds noise**: 不给每个嵌套 `<g>`、图标、数据点或实现碎片添加 bounds。

### 5.3 Shape-first

| 对象 | 模板表达 |
|---|---|
| 基础节点/容器 | `<rect>`、`<circle>`、`<ellipse>` |
| 细关系线 | `<line>` 或少量开放 `<path>` |
| 标准块箭头/流程节点 | 仅在 preset 精确匹配时使用完整 compact authored-preset `<g>` |
| 自定义数据几何 | `<path>`、`<polygon>`、`<polyline>` |
| 数据图表 | 默认 Shape fallback；符合条件时附带 native replacement marker |

**Forbidden — inferred native semantics**: 概念图、流程图和框架图不添加 `data-pptx-replace-with="chart"`；普通关系线不添加 Connector attachment metadata。

---

## 6. 数据图表合同

### 6.1 绘图区标记

**Hard rule**: calculator-supported 数据图表在 `<g id="chartArea">` 内、轴之后、首个数据元素之前保留精确机器注释：

```xml
<!-- chart-plot-area: 140,150,1160,550 -->
```

Pie、Donut、Radar 使用对应中心和半径格式。该注释是工具输入，不得作为“清理注释”删除。

### 6.2 Native Chart/Table

**Hard rule**: 只有 [`native-data-interface.md`](../../references/native-data-interface.md) 支持的真实数据图表或纯文本表格使用 replacement marker。JSON metadata 与可见 fallback 必须表达同一份数据。

```xml
<g id="line-chart"
   data-pptx-bounds="100 140 1080 460"
   data-pptx-replace-with="chart">
    <metadata type="application/json">...</metadata>
    <g id="chartArea">...</g>
</g>
```

**Hard rule**: 项目颜色适配时同步修改可见系列颜色和 metadata `style.colors`。默认 Shape 输出与显式 native 输出都必须可验证。

### 6.3 数据装饰边界

| 元素 | 分类 |
|---|---|
| 轴、刻度、网格、图例 | 结构 |
| 系列颜色、正负语义色 | 数据编码 |
| 数据点节点 | `lineMarker` 等类型需要时保留 |
| Area fill | 面积/累计量是信息时保留；普通 line chart 仅在确认填充不承担范围、基线或强调含义后简化 |
| 柱体渐变、节点高光、卡片阴影 | 只承担审美时可简化；若用于区分重叠、层级或状态则保留结构作用 |
| 来源与注释 | 内容需要时保留，不作为全库固定 chrome |

---

## 7. 占位内容与注册

### 7.1 占位内容

**Hard rule**: 模板占位文本使用英文，展示真实文本容量和数据格式，但不承载具体项目事实。

| 应展示 | 示例 |
|---|---|
| 标题长度 | `Revenue Trend`、`Implementation Plan` |
| 数据格式 | `$245.5M`、`98.5%`、`2026 Q1` |
| 正常换行 | 2–3 行短描述 |
| 结构容量 | 真实建议数量范围内的 series/items/nodes |

**Forbidden — placeholder storytelling**: 不写长篇营销文案、部门归属、真实品牌或无法复用的项目背景。

### 7.2 `charts_index.json`

新增模板必须登记 `<key>.summary`：

```json
"line_chart": {
  "summary": "Pick for 1-3 time-series on a continuous axis showing direction. Skip if cumulative volume matters (use area_chart)."
}
```

**Hard rule**: `summary` 是选型句，使用 `Pick for ... Skip if ...`，不是视觉描述；`key` 与文件名一致，`meta.total` 与 catalog 数量一致。

---

## 8. 迁移边界

本指南是新建和修改模板的目标合同。当前目录中的 76 个 SVG 均已纳入该合同；后续不得以历史文件为由恢复无语义装饰，也不得把中性化误解为删除结构边界。

**Current reference set**:

| 模板 | 覆盖结构 |
|---|---|
| `timeline.svg` | 时间、状态和里程碑卡片 |
| `kpi_cards.svg` | KPI 值、单位与趋势 |
| `labeled_card.svg` | 2×2 标签卡片结构 |
| `icon_grid.svg` | 2×3 图标槽与能力卡片 |
| `line_chart.svg` | 双系列折线与 native chart metadata |
| `pipeline_with_stages.svg` | 分阶段管线、贯通流程和输出链 |
| `layered_architecture.svg` | 分层架构、能力输出和底座 |
| `stacked_area_chart.svg` | 累计面积、图例和统计卡片 |
| `heatmap_chart.svg` | 时间×日期矩阵、连续色阶和统计侧栏 |
| `bubble_chart.svg` | 三变量气泡、象限、系列清单和尺寸图例 |
| `quadrant_text_bullets.svg` | 二轴四象限、分区说明和行动标签 |
| `financial_statement_table.svg` | 财务层级、数值列和强调合计行 |
| `box_plot_chart.svg` | 五数分布、异常值、图例和统计摘要 |
| `dual_axis_line_chart.svg` | 双轴序列、阶段带和数据标注 |
| `stacked_bar_chart.svg` | 堆叠分类、总量标签和洞察侧栏 |
| `segmented_wheel.svg` | 中心主题、等权扇区和配对说明卡 |
| `sankey_chart.svg` | 零损耗流向、节点层级和流量编码 |
| `roadmap_vertical.svg` | 纵向里程碑、状态轨道和目标侧栏 |
| `snake_flow.svg` | 多行蛇形长流程、顺序节点和配对里程碑卡 |
| `concentric_circles.svg` | 同心优先级、资源占比和分层说明卡 |
| `scatter_chart.svg` | 双系列散点、回归趋势、置信区间和统计洞察 |
| `area_chart.svg` | 双系列累计面积、月度趋势和摘要指标 |
| `chevron_process.svg` | 连续阶段箭头、周期带和阶段交付物 |
| `radar_chart.svg` | 多维能力对比、系列面积和基准数据表 |
| `module_composition.svg` | 父模块边界、三级处理链和端到端数据流 |
| `fishbone_diagram.svg` | 核心问题、六类原因分支和具体成因标签 |
| `numbered_steps.svg` | 编号步骤、连接顺序、任务卡和阶段时长 |
| `pareto_chart.svg` | 80/20 分界、降序柱体、累计曲线和行动洞察 |
| `top_down_tree.svg` | 父子层级、汇报连线和末级节点摘要 |
| `butterfly_chart.svg` | 共用中轴、双侧镜像系列和对称刻度 |
| `chevron_chain_with_tail.svg` | 连续箭头阶段、支撑标签和结果汇总尾块 |
| `gauge_chart.svg` | 单项指标、目标区间、当前值和状态说明 |
| `gantt_chart.svg` | 任务行、时间跨度、依赖关系和当前时间标记 |
| `waterfall_chart.svg` | 起始值、增减贡献、连接基线和最终合计 |
| `hub_inward_arrows.svg` | 外围输入、向心关系和中心结论 |
| `treemap_chart.svg` | 层级面积编码、分类色块、标签和解释注记 |
| `hub_spoke.svg` | 中心枢纽、径向连接、能力节点和参考环 |
| `matrix_2x2.svg` | 双轴象限、点位分布、象限标签和优先级说明 |
| `process_flow.svg` | 顺序节点、连接关系、阶段时长和状态图例 |
| `donut_chart.svg` | 环形占比、中心总值、系列图例和摘要指标 |
| `grouped_bar_chart.svg` | 多系列并列柱、共用分类轴和系列图例 |
| `pyramid_isometric.svg` | 分层金字塔、等距深度面和层级说明 |
| `progress_bar_chart.svg` | 多项进度、目标标记、当前值和状态分组 |
| `basic_table.svg` | 表头、数据行、对齐列和状态单元格 |
| `mind_map.svg` | 中心主题、放射分支、二级节点和分支骨架 |
| `comparison_columns.svg` | 并列方案列、价格层级、功能清单和推荐状态 |
| `bullet_chart.svg` | 定性区间、实际值、目标线和多指标对照 |
| `comparison_table.svg` | 多方案表头、横向属性行和结果强调 |
| `client_server_flow.svg` | 客户端与服务端分区、请求响应和交互方向 |
| `dumbbell_chart.svg` | 双状态端点、变化连线、差值和项目排序 |
| `pyramid_chart.svg` | 递进层级、分层容量和层级说明 |
| `vertical_pillars.svg` | 并列支柱、分类标题、要点列表和底部结论 |
| `journey_map.svg` | 阶段轨道、用户行动、情绪曲线和痛点卡片 |
| `consulting_table.svg` | 分层行列、指标数值、数据条和重点结论 |
| `pros_cons_chart.svg` | 正反双栏、判断轴、论据列表和建议结论 |
| `project_schedule_table.svg` | 任务表格、负责人、状态和横向排期 |
| `horizontal_bar_chart.svg` | 长标签排名、横向数值条和洞察侧栏 |
| `funnel_chart.svg` | 递减阶段、转化率、流失关系和摘要指标 |
| `isometric_stairs.svg` | 递进台阶、阶段标签、空间顺序和接地基线 |
| `pie_chart.svg` | 单层占比、扇区标签、图例和总量摘要 |
| `circular_stages.svg` | 环形阶段、循环方向、阶段说明和中心主题 |
| `team_roster.svg` | 成员卡片、头像槽、姓名职务和简介容量 |
| `harvey_balls_table.svg` | 评价行列、分级圆点、评分图例和汇总状态 |
| `column_chart.svg` | 单系列分类柱、数值标签、坐标轴和基准线 |
| `arc_anchored_list.svg` | 弧线主轴、锚点节点、顺序条目和配对说明 |
| `vertical_list.svg` | 纵向轨道、顺序节点、内容卡片和阶段状态 |
| `sunburst_chart.svg` | 多层环形层级、父子占比、叶子图例和解释面板 |
| `agenda_list.svg` | 编号议程、条目说明、时长信息和纵向导轨 |
| `stock_chart.svg` | OHLC 蜡烛、日期轴、价格区间和指标摘要 |
| `feature_matrix_table.svg` | 功能行、产品列、二元状态和方案对照 |
| `histogram_chart.svg` | 连续分箱、频数柱、统计标记和分布解释 |
| `venn_diagram.svg` | 集合边界、交集区域、关系标签和结论说明 |
| `quadrant_bubble_scatter.svg` | 双轴象限、气泡位置、尺寸编码和项目标签 |
| `bar_of_pie_chart.svg` | 主饼占比、长尾聚合、堆叠条明细和连接关系 |
| `pie_of_pie_chart.svg` | 主饼占比、长尾聚合、次级饼明细和连接关系 |
| `word_cloud.svg` | 词项权重、字号编码、主题分布和关键词层级 |

**Hard rule**: 修改任一模板时先冻结可见文本、数据和结构层级，再简化确认无语义的效果、补齐直属根 bounds，并完成文本差异、独立渲染与双路线验证。未经明确说明的文本删除、改写或结构边界丢失都会阻断变更。不要仅为追求 catalog 一次性整齐而批量重写。

---

## 9. 检查清单

### 9.1 结构与可读性

- [ ] SVG 独立可渲染，`viewBox` 为 `0 0 1280 720`。
- [ ] 源码有正常缩进、语义 ID 和必要结构注释。
- [ ] 原有可见文本、数值、单位、来源、状态和关系保持不变；删除项只有审核过的重复信息。
- [ ] 真实信息单元、父子层级、阶段范围和输出区仍有清楚边界。
- [ ] 每个可见直属根 `<g>` 有准确的 `data-pptx-bounds`；嵌套组不滥加 bounds。
- [ ] 模板只保留结构、数据编码和必要中性预览。
- [ ] 字体在根或清楚父组继承，文本字号不小于 12。

### 9.2 风格归属

- [ ] 无固定项目调色板、品牌字体或品牌 chrome。
- [ ] 纯装饰效果已减少，但没有以“去装饰”为由删除结构框线或压平层级。
- [ ] 颜色差异确实表达 series、state、positive/negative 等语义。
- [ ] 标题、副标题和来源只用于展示必要结构或容量。

### 9.3 数据与 PowerPoint

- [ ] 数据图表保留准确 `chart-plot-area` 标记。
- [ ] Eligible Chart/Table 的 metadata 与可见 fallback 数据一致。
- [ ] 默认 Shape-first 导出通过。
- [ ] 存在 replacement marker 时，显式 native Chart/Table 导出通过。
- [ ] `svg_quality_checker.py` 无 error；warning 已人工判断。

### 9.4 Catalog

- [ ] 新模板已登记 `charts_index.json`。
- [ ] 修改 key/summary 后通过 `chart_recall.py validate` 和 recall 烟测。
- [ ] 前后可见文本差异已审阅，非重复内容没有意外丢失或改写。
- [ ] 前后渲染对比确认结构仍可读。
- [ ] 记录 bytes/tokens 变化，但不以牺牲源码可读性换取数字。

---

## 10. 验证命令

```bash
# 单文件 SVG 合同
python3 skills/ppt-master/scripts/svg_quality_checker.py \
  skills/ppt-master/templates/charts/<key>.svg

# Catalog key
python3 skills/ppt-master/scripts/chart_recall.py validate <key>

# 可安全压缩的页面坐标（默认 dry-run）
python3 skills/ppt-master/scripts/compact_svg_coordinates.py \
  skills/ppt-master/templates/charts/<key>.svg
```

**Validation**: 修改后至少完成 XML 解析、独立 SVG 渲染、Checker、默认 Shape-first 导出，以及 marker 模板的 native Chart/Table 导出。

---

## 11. 结构图式兼容索引

本节保留旧引用锚点，但所有图式都受 §1 所有权边界约束。

### 11.1 Attached Section Tab

**Reference — not a constraint**: 半圆标签只在“标签从属于当前信息块”是结构信息时使用。颜色、圆角和高度由项目适配；它不是卡片的默认装饰。

**Forbidden — cover hack**: 不用“全圆角矩形 + 同色覆盖矩形”拼接单侧圆角；需要时直接使用一个可编辑 path。

### 11.2 Nested Card Border

**Default — single boundary (may override when hierarchy requires two levels)**: 中性模板优先一层描边或留白。浅色外框 + 内层白卡属于旧视觉配方，不再作为共享模板默认；只有外层与内层表达两个真实层级时才保留。

### 11.3 Card Grid

卡片网格表达并列关系和容量，不决定最终卡片风格：

| 结构 | 典型容量 | 参考画布分配 |
|---|---|---|
| 2×2 | 4 个平行方面/KPI | `560×255`，横向间距约 40 |
| 2×3 | 6 个能力/服务 | `370×260`，横向间距约 25 |
| 1×3 | 3 个平行支柱 | 每列约 `400×540` |
| 1×4 | 4 个紧凑指标 | 每列约 `280×250` |

**Hard rule**: `page_rhythm: breathing` 不因 catalog 示例自动变成卡片网格；最终结构仍服从页面内容和项目节奏。

### 11.5 Diagonal Relationship Arrow

**Hard rule**: 倾斜虚线箭头只表达跨象限迁移、影响或建议方向，并配一条简短关系标签。颜色与标签外观由项目决定。

### 11.6 Ground Anchor

**Default — omit (may override when depth is semantic)**: 接地椭圆是深度装饰，不属于中性模板默认。只有物体与地面/层级的空间关系本身有意义时保留；不得为了“漂浮感”普遍添加。

### 11.7 Bidirectional Interaction Arrows

**Hard rule**: 双向关系使用两条方向明确的线，每条线都有动作标签。请求/响应的颜色只需可区分，最终映射由项目调色板决定。
