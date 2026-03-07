# SVG 图表模板库（33 种）

本目录提供 **33 种标准化 SVG 图表模板**，可直接作为 PPT Master 的图表选型参考。

- **完整索引**：[README.md](./README.md)（人工浏览）
- **JSON 索引**：[charts_index.json](./charts_index.json)（AI / 程序优先读取）

生成图表页面前，建议先阅读对应模板文件了解其结构和布局。

## 快速选择

> 🤖 **AI / 程序选型建议**：优先读取 `charts_index.json`；人工浏览和快速比对时使用本 README。

| 我想展示... | 推荐模板 | 文件名 |
|------------|---------|--------|
| 关键数字指标 | KPI 卡片 | `kpi_cards.svg` |
| 类别数值对比 | 柱状图 | `bar_chart.svg` |
| 长标签排名 | 水平条形图 | `horizontal_bar_chart.svg` |
| 多系列对比 | 分组柱状图 | `grouped_bar_chart.svg` |
| 时间趋势 | 折线图 | `line_chart.svg` |
| 累积趋势 | 面积图 | `area_chart.svg` |
| 占比构成 | 饼图 / 环形图 | `pie_chart.svg` / `donut_chart.svg` |
| 目标完成度 | 进度条 / 仪表盘 | `progress_bar_chart.svg` / `gauge_chart.svg` |
| 转化漏斗 | 漏斗图 | `funnel_chart.svg` |
| 项目排期 | 甘特图 | `gantt_chart.svg` |
| 里程碑事件 | 时间轴 | `timeline.svg` |
| 多维评估 | 雷达图 | `radar_chart.svg` |
| 左右双向对比 | 蝴蝶图 | `butterfly_chart.svg` |
| 增减分解 | 瀑布图 | `waterfall_chart.svg` |
| 流量/资金流向 | 桑基图 | `sankey_chart.svg` |
| 战略分析 | SWOT / 波特五力 | `swot_analysis.svg` / `porter_five_forces.svg` |
| 四象限分析 | 矩阵图 | `matrix_2x2.svg` |

## 完整图表索引

### 对比类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `bar_chart.svg` | 垂直柱状对比（3-8 柱） | 销售额对比、区域排名 |
| `horizontal_bar_chart.svg` | 水平条形排名（5-12 条） | 品牌排行、满意度评分 |
| `grouped_bar_chart.svg` | 多系列分组对比 | 季度产品线对比、同比环比 |
| `stacked_bar_chart.svg` | 堆叠构成对比 | 收入构成、市场份额变化 |
| `butterfly_chart.svg` | 左右双向对比 | 人口金字塔、AB 测试、收支对比 |
| `bullet_chart.svg` | 目标 vs 实际 | KPI 达成、绩效评估 |
| `dumbbell_chart.svg` | 多维度得分对比 | 竞品评估、综合指数 |
| `waterfall_chart.svg` | 增减变化分解 | 利润分解、预算变化 |

### 趋势类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `line_chart.svg` | 折线趋势（支持多条） | 时间序列、增长趋势 |
| `area_chart.svg` | 面积累积趋势 | 流量趋势、用户增长 |
| `stacked_area_chart.svg` | 多系列堆叠趋势 | 营收来源、流量来源变化 |
| `dual_axis_line_chart.svg` | 双 Y 轴不同量纲对比 | 销量与利润率、流量与转化率 |

### 占比类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `pie_chart.svg` | 基础占比（3-6 块） | 市场份额、预算分配 |
| `donut_chart.svg` | 环形占比（带中心数据） | 结构占比、类别构成 |
| `treemap_chart.svg` | 层级面积占比 | 预算分配、市场份额构成 |

### 指标类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `kpi_cards.svg` | 关键指标卡片（2×2 / 1×4） | 财务总览、数据看板 |
| `gauge_chart.svg` | 仪表盘达成度 | KPI 完成率、性能监控 |
| `progress_bar_chart.svg` | 多项进度条对比 | OKR 进度、项目完成度 |

### 分析类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `radar_chart.svg` | 多维度评估（4-8 维） | 能力评估、竞品对比 |
| `scatter_chart.svg` | 相关性 / 分布 | 投入产出、价格需求 |
| `funnel_chart.svg` | 转化漏斗（3-5 阶段） | 销售漏斗、用户转化 |
| `matrix_2x2.svg` | 四象限分析 | 波士顿矩阵、优先级分析 |
| `bubble_chart.svg` | 三维气泡（X/Y/大小） | 市场规模 vs 增长率 vs 份额 |
| `heatmap_chart.svg` | 矩阵热力图 | 用户活跃时段、相关性矩阵 |
| `pareto_chart.svg` | 80/20 帕累托分析 | 质量归因、销售贡献 |
| `box_plot_chart.svg` | 箱线图分布统计 | 薪资分布、质量控制 |

### 项目管理 / 关系类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `gantt_chart.svg` | 甘特图排期（6-12 任务） | 项目管理、产品路线图 |
| `timeline.svg` | 时间轴事件（3-8 节点） | 里程碑、历史演进 |
| `process_flow.svg` | 流程图步骤 | 业务流程、操作指南 |
| `org_chart.svg` | 组织结构（2-4 层） | 公司架构、汇报关系 |
| `sankey_chart.svg` | 数据流向（三层级） | 预算流向、用户转化路径 |

### 战略框架类

| 文件名 | 用途 | 适用场景 |
|--------|------|---------|
| `swot_analysis.svg` | SWOT 四象限分析 | 战略规划、竞品分析 |
| `porter_five_forces.svg` | 波特五力模型 | 行业分析、市场进入评估 |
