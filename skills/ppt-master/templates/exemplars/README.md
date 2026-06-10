# Exemplars — 最佳示例库（gold pages）

> 用户**明确认可**的页面 SVG 集合，作为后续 deck 的视觉起点。这是 [`docs/zh/visual-design-paradigm.md`](../../../../docs/zh/visual-design-paradigm.md) §13 反馈进化机制 的产物之一。

## 用法

Executor 起一份新 deck 前，先按页面类型在这里找同类示例（封面 / KPI 卡页 / 数据图页 / 案例页 / 章节页），**复制其结构与组件做法作为起点**，再换内容与品牌色——而不是从零摸索。

## 维护

- 每当用户明确认可某页，复制其 `svg_output/<page>.svg` 进来，文件名带类型前缀（如 `cover_*`、`kpi-cards_*`、`chart_*`），并在下表加一行「为什么它高级」。
- 被更好示例取代的，文件名后缀 `.deprecated.svg` 或在表中标注。

## 索引

| 文件 | 类型 | 来源 | 为什么它高级（认可点）|
|------|------|------|---------------------|
| `cover_image-canvas-keynote.svg` | 封面 | 临港算力对外介绍 | 满版 hero 大图 + 大字渐变标题 + 眉标 chip + 底部磨砂特征胶囊；keynote 发布会感，文字仍为可编辑 SVG 叠层 |

> 注：示例中的品牌色 / 文案是来源项目的；复用时按目标 deck 的 `spec_lock` 替换，保留结构 / 组件 / 排版工艺。
