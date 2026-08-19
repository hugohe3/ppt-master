# Visualization Template Authoring Guide

这是供维护者审阅的中文指南，因此放在两个 Visualization catalog 的共同父目录，
而不是归某一个 family 所有。`templates/charts/` 和 `templates/tables/` 共同组成
page-local Visualization 模板库；模板负责数据编码或单元格关系，不负责最终项目
风格。模板必须保持源码可读、独立可渲染，并允许 Executor 根据项目 Design Spec
与 `spec_lock.md` 重做字体、配色和装饰。

| Family | 定义 | 判定边界 |
|---|---|---|
| `chart` | Value-driven visualization | 数值、类别、时间、权重或持续时间决定 mark 的位置、长度、面积、角度、字号或连接宽度 |
| `table` | Row × column fact grid | 行头与列头共同寻址一个单元格事实；合并、对齐和边界保持该交点关系 |

**Hard rule — Structure is a method, not a catalog**: 定性顺序、层级、角色、
分区和关系由 [`executor-structure.md`](../references/executor-structure.md) 在当前页面
现场构形，不登记固定 `structure/<key>`、SVG roster 或 index。Default 和 Quick 都先
判断页面真实信息模型；需要定性拓扑时都必须采用这套 Structure 方法。删除 catalog
只删除固定示例，不删除 Quick 或 Default 的 Structure 能力。

**Hard rule — Visualization is not Layout**: Chart/Table 模板和运行时 Structure
都不拥有 `data-pptx-master`、`data-pptx-layout`、`data-pptx-layer` 或
`data-pptx-placeholder`。跨页 Master/Layout、page type、slot geometry 和
placeholder 合同仍只属于 [`layouts/`](./layouts/) workspace。

## 0. 上游规范

**Hard rule**: 本指南只定义 Chart/Table 两个 catalog family 的结构与中性预览合同。通用 SVG 语法、效果、原生数据接口和 PowerPoint 结构分别由以下权威文件定义：

| 合同 | 权威文件 |
|---|---|
| 通用 SVG | [`shared-standards.md`](../references/shared-standards.md) |
| 效果与兼容输入 | [`svg-effects.md`](../references/svg-effects.md) |
| Native Chart/Table | [`native-data-interface.md`](../references/native-data-interface.md) |
| 画布格式 | [`canvas-formats.md`](../references/canvas-formats.md) |

**Forbidden — second SVG specification**: 不在本指南复述或放宽上游语法。发生冲突时以上游权威文件为准。

---

## 1. 所有权边界

### 1.1 作者合同与项目消费

以下所有权只约束库内单个模板工件的维护，不把该工件变成项目页面的布局锁：

| 单个 Visualization 模板的作者合同 | 项目页面决策拥有 |
|---|---|
| 该工件的 family 与相应信息模型 | 最终采用的页面级结构、类型与几何 |
| 该工件内的数据映射或单元格关系 | 项目字体、字号、调色板与品牌色 |
| 该工件的示例骨架和阅读顺序 | 实际分组、框架数量、项目数量、组合方式与容量适配 |
| 必要的状态与语义区分 | 页面背景、页头、页脚和品牌 chrome |
| 独立预览所需的中性样式 | 最终强调策略与页面级视觉层级 |

**Hard rule — authoring integrity**: 维护某个库模板时必须保持该模板自身的
family 与信息模型：Chart 的 value mapping、Table 的 row × column fact grid。
若修改结果属于定性关系拓扑，不新增第三类模板，而由 runtime Structure 方法构建；
若仍属于另一 catalog family，应登记到正确 family，不能保留错误标签。最终视觉样式
仍来自使用它的项目，而不是模板的示例审美。

**Hard rule — flexible project reference**: Executor 选中的 `family/key` 仍只是
flexible page-local reference。Default 的 §IX 或 Quick 的页面决策拥有最终结构；
选中引用不会锁死页面的可视化类型、几何、分组数、项目数或组合方式，Executor
可按已确认的页面意图适配、重组或替换。项目若实际采用某一信息模型，必须保持
其真实数据与关系准确；仅有引用本身不构成页面结构权威。

### 1.2 保留判断

对每个视觉元素按顺序判断：

| 判断 | 处理 |
|---|---|
| 删除后会改变数据含义、关系、状态或阅读顺序 | 保留 |
| 删除后会弱化分组、层级、边界或文本容量 | 保留结构表达；只简化不承载信息的样式层 |
| 只让示例显得更精致、立体、品牌化或“高级” | 作为简化候选；通过文本与前后渲染核对后再删除 |
| 只对某个项目风格成立 | 交给 Executor 重建 |

**Default — information first (may override when semantics require it)**: 优先使用清楚的线、面、标签和留白。装饰不能成为理解信息的前提。

### 1.3 保真优先

**Hard rule — fidelity before slimming**: 模板瘦身不得改写或删除原有可见标题、标签、说明、数值、单位、状态、来源、顺序、容量和关系。占位内容保持原文；只有明确重复的信息可以删除，并记录理由。

**Explicit migration exception**: 经明确批准的 family/key 合并、重组或退役可以用
中性占位内容重建 canonical SVG，或移除不再存活的工件；这不是普通模板瘦身。
迁移必须在 §8 记录 catalog 边界和仍可读取的 legacy 语义。未列入批准迁移的模板
仍受上一条逐字保真约束。

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

## 5. SVG 分组与边界

### 5.1 语义分组

**Hard rule**: 使用描述性顶层 `<g id>` 表达页面级逻辑单元，例如 Header、Chart、Legend、Card Grid 或 Process。不要为每条文字、图标或数据点建立一个直属根组。

| 顶层组 | 典型内容 |
|---|---|
| `header` | 标题与副标题 |
| `chart-area` / replacement carrier | Chart 的轴、数据系列、标签、必要 metadata |
| `legend` | 系列或状态说明 |
| `table-area` / replacement carrier | Table 的行、列、单元格和必要 metadata |
| `table-notes` | 来源、口径或脚注 |

**Forbidden — workspace metadata**: 两个 catalog family 都不得写入
Master/Layout/placeholder 所有权标记。运行时 Structure 即使占满整个
`1280×720` 画布也仍是 Slide-local 构形，不会因此成为 Layout workspace。

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
| 直线关系/分隔/引线 | `<line>` |
| 预设可精确表达的弯折/曲线关系 | 完整 compact authored `bentConnector*` / `curvedConnector*` `<g>`；端点不附着 |
| 单一预设不能表达、但封闭形状可组合的对象 | 优先用 `shape_boolean_svg.py` 物化 Merge Shapes 结果 |
| 图元、预设、Boolean 都不能表达的数据/语义/锁定风格几何 | `<path>`、`<polygon>`、`<polyline>` |
| 数据图表 | 默认 Shape fallback；符合条件时附带 native replacement marker |

**Forbidden — inferred native semantics**: 概念图、流程图和框架图不添加 `data-pptx-replace-with="chart"`；普通关系线不添加 Connector attachment metadata。

---

## 6. Chart 与 Native Data 合同

### 6.1 绘图区标记

**Hard rule**: calculator-supported 数据图表在 `<g id="chartArea">` 内、轴之后、首个数据元素之前保留精确机器注释：

```xml
<!-- chart-plot-area: 140,150,1160,550 -->
```

Pie、Donut、Radar 使用对应中心和半径格式。该注释是工具输入，不得作为“清理注释”删除。

Catalog 模板本身只有一个主 Chart，可保留上述 unscoped marker 与
`id="chartArea"`。Executor 在项目页面组合多个已验证 Chart 对象时，改用
[`executor-chart.md`](../references/executor-chart.md) 定义的 semantic object key
和 scoped marker；不能在同一 SVG 中复制多个 `chartArea` id。

### 6.2 Native Chart/Table

**Hard rule**: 只有 [`native-data-interface.md`](../references/native-data-interface.md) 支持的真实 Chart 或纯文本 Table 使用 replacement marker。JSON metadata 与可见 fallback 必须表达同一份数据。运行时构建的 Structure 永远不使用 Chart/Table replacement marker。

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

### 7.2 分类索引与规划投影

新增模板只登记到其 owning family index：

| 分类 | 目录 | 机器索引 | 规划词汇表 |
|---|---|---|---|
| `chart` | `charts/` | `charts_index.json` → `charts` | `chart-vocabulary.md` |
| `table` | `tables/` | `tables_index.json` → `tables` | 同一份紧凑注册表 |

每个 `<key>.summary` 使用相同的选择句合同：

```json
"line_chart": {
  "summary": "Pick for 1-3 time-series on a continuous axis showing direction. Skip if cumulative volume matters (use area_chart)."
}
```

`summary` 保留 `Pick for ... Skip if ...` 句式，供可选的机器召回诊断使用；
规划主路径不读取这些记录。Chart 的 `chart-vocabulary.md` 必须完整列出同一组
canonical `chart/<key>`，只说明信息关系，不写 SVG 实现、布局参数或选择结论。

**Hard rule**: `key` 与同 family 文件名一致，`meta.total` 与该 family catalog
数量一致；Chart vocabulary 与 index 的成员集合必须精确一致。除此以外不要建立
跨 family 的第二份成员清单。

---

## 8. 迁移边界

本指南是新建和修改 Chart/Table 模板的目标合同。当前两个 catalog family 共
39 个 SVG：Chart 33 个、Table 6 个。各 live index 是成员清单的唯一权威；
Structure 不再有固定 SVG roster、index 或 canonical key。

**Hard rule — topology is generated, not recalled**: 从来源 deck 吸收的是 Shape
grammar 和构形思维，而不是页面示例清单。先还原顺序、层级、分组、分区、连接、
交叠等真实关系，再由 `executor-structure.md` 使用区域、节点、主轴、连接、标签与
装饰等角色现场组合。Default 在 §IX 描述该关系，Quick 在当前上下文作同一判断；
两条路径都不依赖 `structure/<key>` 或固定 SVG，不能因 Quick 跳过 §VII/lock 就跳过
Structure 载体判断。

**已批准的图表容量迁移**：

| Canonical key | 已批准边界 | 兼容处理 |
|---|---|---|
| `gauge_chart` | 2026-08-10：中性预览从三个并列 Gauge 重组为一个有界域、明确目标或阈值的 KPI；多个同级 KPI 改用 `bullet_chart` 或 `progress_bar_chart` | canonical key 保持不变；旧三指标示例不再作为可读取容量合同，无需 alias |

**Canonical Table set**:

| Canonical key | 核心信息关系 |
|---|---|
| `record_table` | 每行一条记录、每列一个稳定字段 |
| `metric_table` | 实体与 KPI 的交点承载度量、变化、状态或 cell 内微图形 |
| `comparison_matrix` | 行维度与列方案的交点承载文本、精确值或异构事实 |
| `feature_matrix` | 能力与方案的交点承载支持、不支持、部分支持或例外状态 |
| `rating_matrix` | 评价维度与方案的交点使用同一套序数等级 |
| `hierarchical_table` | 分组或缩进行、明细与小计/总计形成层级网格 |

**Hard rule — semantic family before physical object**: PowerPoint 中的物理
Table 对象不自动属于 `table` family。只有行头与列头的交点可寻址为一个事实时才是
Table；日期或持续时间决定 `x`/`width` 的排期是 `chart/gantt_chart`；阶段与泳道只
表达定性活动位置时由 runtime Structure 构建。

**Canonical catalog aliases**:

| Canonical reference | Legacy bare keys |
|---|---|
| `table/record_table` | `basic_table` |
| `table/metric_table` | `consulting_table` |
| `table/comparison_matrix` | `comparison_table` |
| `table/feature_matrix` | `feature_matrix_table` |
| `table/rating_matrix` | `harvey_balls_table` |
| `table/hierarchical_table` | `financial_statement_table` |
| `chart/gantt_chart` | `project_schedule_table` |

新文档、§VII 和 `page_visualizations` 只写 canonical `chart|table/<key>`。表中 Alias
只服务旧 `page_charts` 读取，不是新模板命名候选；旧的 family-qualified key 不获得
兼容特权。此前 36 个 canonical Structure bare key 只在旧 `page_charts` 读取时保留为
`legacy-structure-intent`：它没有 canonical SVG、path 或 reference，不参与 recall，
也不能写入新 §VII/lock。消费方把该意图投影为定性关系提示，再交给 runtime Structure
构形；不得把它伪装成仍存活的模板。

**Hard rule**: 修改一个仍属 canonical 的模板时先冻结可见文本、数据和结构层级，
再简化确认无语义的效果、补齐直属根 bounds，并完成文本差异、独立渲染与双路线
验证。经本节明确登记的 catalog 合并/重组/退役不要求保留旧示例文案；除此之外，未经
说明的文本删除、改写或结构边界丢失都会阻断变更。

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

### 9.3 Family 与 PowerPoint

- [ ] Family 判定正确：Chart 为 value-driven、Table 为 row × column fact grid；定性拓扑退出 catalog 并由 runtime Structure 构建。
- [ ] Chart/Table 模板不含 Master/Layout/layer/placeholder ownership metadata。
- [ ] Calculator-supported Chart 保留准确 `chart-plot-area` 标记。
- [ ] Eligible Chart/Table 的 metadata 与可见 fallback 数据一致。
- [ ] 默认 Shape-first 导出通过。
- [ ] 存在 replacement marker 时，显式 native Chart/Table 导出通过。
- [ ] `svg_quality_checker.py` 无 error；warning 已人工判断。

### 9.4 Catalog

- [ ] 新模板只登记到 owning family index，index object、`meta.total` 与 SVG roster 一致。
- [ ] 修改 key/summary 后通过 `visualization_recall.py validate` 和 recall 烟测。
- [ ] 前后可见文本差异已审阅，非重复内容没有意外丢失或改写。
- [ ] 前后渲染对比确认结构仍可读。
- [ ] 记录 bytes/tokens 变化，但不以牺牲源码可读性换取数字。

---

## 10. 验证命令

```bash
# 单文件 SVG 合同
python3 skills/ppt-master/scripts/svg_quality_checker.py \
  skills/ppt-master/templates/<family-directory>/<key>.svg

# Canonical family/key
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  <family>/<key>

# 可安全压缩的页面坐标（默认 dry-run）
python3 skills/ppt-master/scripts/compact_svg_coordinates.py \
  skills/ppt-master/templates/<family-directory>/<key>.svg
```

**Validation**: 修改后至少完成 XML 解析、独立 SVG 渲染、Checker、默认 Shape-first 导出，以及 marker 模板的 native Chart/Table 导出。
