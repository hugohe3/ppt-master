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
| 构图骨架、阅读顺序和容量边界 | 圆角、阴影、渐变、纹理和装饰语言 |
| 必要的状态与语义区分 | 页面背景、页头、页脚和品牌 chrome |
| 独立预览所需的中性样式 | 最终强调策略与页面级视觉层级 |

**Hard rule**: Executor 适配模板时保留可视化类型、信息关系和数据准确性；最终视觉必须来自当前项目，而不是继承模板的示例审美。

### 1.2 保留判断

对每个视觉元素按顺序判断：

| 判断 | 处理 |
|---|---|
| 删除后会改变数据含义、关系、状态或阅读顺序 | 保留 |
| 删除后会使独立 SVG 无法辨认结构或文本容量 | 使用最小中性表达 |
| 只让示例显得更精致、立体、品牌化或“高级” | 删除 |
| 只对某个项目风格成立 | 交给 Executor 重建 |

**Default — structure first (may override when semantics require it)**: 优先使用清楚的线、面、标签和留白。装饰不能成为理解结构的前提。

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

### 3.1 默认省略

**Default — no decorative effects (may override when data encoding requires it)**: 中性模板不使用阴影、发光、纹理、玻璃面板、装饰渐变或漂浮效果。

| 效果 | 默认 | 允许条件 |
|---|---|---|
| 阴影/filter | 省略 | 无；项目执行阶段按视觉风格决定 |
| 渐变 | 省略 | 连续色阶、流量、深度面等确实承载数据或空间编码 |
| 透明光晕 | 省略 | 透明度本身编码范围或不确定性 |
| 圆角卡片 | 非默认 | 边界确实表达一个信息单元 |
| 图标底板 | 非默认 | 需要明确图标槽位或状态边界 |

**Hard rule**: Heatmap 色阶、Sankey 流量宽度、系列区分和 Isometric 面向关系属于信息编码；普通卡片阴影、气泡高光、装饰性色带和大号淡色序号不属于。

### 3.2 容器克制

**Hard rule**: 一个信息单元最多使用一种主要边界表达：留白、分隔线、描边或底色。不要同时叠加描边、阴影、渐变和多层圆角框。

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
| Area fill | 只有面积/累计量是信息时保留；普通 line chart 删除 |
| 柱体渐变、节点高光、卡片阴影 | 装饰，默认删除 |
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

本指南是新建和修改模板的目标合同。尚未迁移的存量文件可继续存在，但不得作为新增装饰规则的依据。

**Current reference set**:

| 模板 | 覆盖结构 |
|---|---|
| `timeline.svg` | 时间、状态和里程碑卡片 |
| `kpi_cards.svg` | KPI 值、单位与趋势 |
| `labeled_card.svg` | 2×2 标签卡片结构 |
| `icon_grid.svg` | 2×3 图标槽与能力卡片 |
| `line_chart.svg` | 双系列折线与 native chart metadata |

**Hard rule**: 修改其他模板时按本指南删除无语义装饰、补齐直属根 bounds，并完成独立渲染与双路线验证。不要仅为追求 catalog 一次性整齐而进行未经视觉审阅的批量重写。

---

## 9. 检查清单

### 9.1 结构与可读性

- [ ] SVG 独立可渲染，`viewBox` 为 `0 0 1280 720`。
- [ ] 源码有正常缩进、语义 ID 和必要结构注释。
- [ ] 每个可见直属根 `<g>` 有准确的 `data-pptx-bounds`；嵌套组不滥加 bounds。
- [ ] 模板只保留结构、数据编码和必要中性预览。
- [ ] 字体在根或清楚父组继承，文本字号不小于 12。

### 9.2 风格归属

- [ ] 无固定项目调色板、品牌字体或品牌 chrome。
- [ ] 无纯装饰阴影、发光、纹理、渐变或大号淡色编号。
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
