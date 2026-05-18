# glassmorphism_demo - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md`. Executor re-reads `spec_lock.md` before every SVG page.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | glassmorphism_demo |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 12 |
| **Design Style** | B) General Consulting + Glassmorphism SaaS |
| **Target Audience** | AI 产品经理 / 工程负责人 / 技术决策者 |
| **Use Case** | 技术分享 / 内部培训 / 产品发布 |
| **Created Date** | 2026-05-17 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 60px 左右 / 50px 上下 |
| **Content Area** | 1160×620（除去 margin） |

---

## III. Visual Theme

### Theme Style

- **Style**: B) General Consulting + Glassmorphism SaaS
- **Theme**: Dark theme（深色玻璃 + 流光霓虹）
- **Tone**: 未来感、科技、轻盈悬浮、专业

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0A0E27` | 深空蓝主底 |
| **Secondary bg** | `#1A2150` | Glass 面板透明叠层基底（实际 fill-opacity 0.4-0.6） |
| **Primary** | `#5B8DEF` | 流光蓝 — 标题装饰 / 主图标 / 主图表 |
| **Accent** | `#A26BFA` | 流光紫 — 关键数据 / 渐变端点 |
| **Secondary accent** | `#3DDDFC` | 霓虹青 — 高亮、连接线发光 |
| **Body text** | `#E8ECFF` | 淡蓝白主文 |
| **Secondary text** | `#A8B0D0` | 柔灰蓝注释 |
| **Tertiary text** | `#6B7299` | 页脚、辅助 |
| **Border/divider** | `#2E3672` | 玻璃描边（实际 stroke-opacity 0.4-0.6） |
| **Success** | `#4ADE80` | 薄荷绿 |
| **Warning** | `#FB7185` | 霓虹粉红 |

> 60-30-10：深空底 60% / glass + 文字 30% / 霓虹 accent 10%。

### AI Image Strategy

- **Image Rendering**: glassmorphism
- **Image Palette**: tech-neon

### Gradient Scheme

```xml
<!-- 主标题渐变（蓝→紫→青） -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#5B8DEF"/>
  <stop offset="50%" stop-color="#A26BFA"/>
  <stop offset="100%" stop-color="#3DDDFC"/>
</linearGradient>

<!-- 玻璃面板渐变 -->
<linearGradient id="glassPanel" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#5B8DEF" stop-opacity="0.18"/>
  <stop offset="100%" stop-color="#A26BFA" stop-opacity="0.08"/>
</linearGradient>

<!-- 背景流光 radial -->
<radialGradient id="bgGlow" cx="80%" cy="20%" r="60%">
  <stop offset="0%" stop-color="#5B8DEF" stop-opacity="0.25"/>
  <stop offset="100%" stop-color="#5B8DEF" stop-opacity="0"/>
</radialGradient>

<radialGradient id="bgGlow2" cx="20%" cy="80%" r="55%">
  <stop offset="0%" stop-color="#A26BFA" stop-opacity="0.2"/>
  <stop offset="100%" stop-color="#A26BFA" stop-opacity="0"/>
</radialGradient>

<!-- 玻璃面板高光线 -->
<linearGradient id="glassEdge" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.35"/>
  <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
```

---

## IV. Typography System

**Typography direction**: modern CJK sans, same family weight contrast (heavy title / regular body)

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei", "PingFang SC"` | — | `sans-serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei", "PingFang SC"` | — | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Microsoft YaHei", "PingFang SC", sans-serif`（font-weight: 900）
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`（font-weight: 400）
- Emphasis: same as Body（font-weight: 600）
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = **20px**（中等密度 SaaS deck）

| Purpose | Ratio to body | Example @ body=20 | Weight |
| ------- | ------------- | ------------------ | ------ |
| Cover title (hero headline) | 2.5-5x | 60-100px | 900 |
| Chapter / section opener | 2-2.5x | 40-50px | 900 |
| Page title | 1.5-2x | 30-40px | 900 |
| Hero number (KPI) | 1.5-2x | 30-40px | 900 |
| Subtitle | 1.2-1.5x | 24-30px | 600 |
| **Body content** | **1x** | **20px** | 400 |
| Annotation / caption | 0.7-0.85x | 14-17px | 400 |
| Page number / footnote | 0.5-0.65x | 10-13px | 400 |

---

## V. Layout Principles

### Page Structure

- **Header area**: 60px top margin + page title 50px = 顶部 ~110px
- **Content area**: 中部 ~500px（含玻璃面板 / chart / 图）
- **Footer area**: 40px 底（页码 + 项目标识）

### Layout Pattern Library

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | 封面、收尾 (P01/P12) |
| **Symmetric split (5:5)** | 模式对比 (P05) |
| **Three/four column cards** | 三难现状 / KPI 仪表板 (P03/P08) |
| **Matrix grid (2×2)** | 失败模式 (P10) |
| **Top-bottom split** | Hero 转场 (P02) |
| **Center-radiating** | 上下文工程 hub_spoke (P07) |
| **Layered horizontal** | Agent 架构 layered (P04) |
| **Z-pattern / waterfall** | 工具编排 numbered_steps (P06) |
| **Negative-space-driven** | breathing 页（P02/P12） |
| **Image-as-canvas + native overlay** | 所有有 AI 图的页（P01/P02/P04/P06/P07/P08/P10/P12） |

### Spacing Specification

**Universal**：

| Element | Value |
| ------- | ----- |
| Safe margin from canvas edge | 50-60px |
| Content block gap | 28px |
| Icon-text gap | 12px |

**Card-based (glass panels)**：

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Card padding | 24-28px |
| Card border radius | 16px |
| Card stroke | `#FFFFFF` stroke-width 1, stroke-opacity 0.18 |
| Card fill | `url(#glassPanel)` or `#1A2150` with fill-opacity 0.5 |

**Non-card / breathing**：

- Line-height 1.5x body
- Full-bleed text inset 80px+；with #29 two-stop scrim 保证 legibility

---

## VI. Icon Usage Specification

### Source

- **Library**: `phosphor-duotone`（双层 backplate 与 glassmorphism 分层语言共振）
- **Usage**: `<use data-icon="phosphor-duotone/<name>" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 性能/延迟痛点 | `phosphor-duotone/gauge` | P03, P08 |
| 成本痛点 | `phosphor-duotone/coin` | P03, P08, P10 |
| 质量/错误痛点 | `phosphor-duotone/bug` | P03, P10 |
| 感知层 | `phosphor-duotone/eye` | P04 |
| 推理层 | `phosphor-duotone/brain` | P04 |
| 行动层 | `phosphor-duotone/lightning` | P04 |
| 记忆层 | `phosphor-duotone/database` | P04, P07 |
| Workflow 模式 | `phosphor-duotone/flow-arrow` | P05 |
| Agent 模式 | `phosphor-duotone/robot` | P05 |
| Multi-Agent 模式 | `phosphor-duotone/users-three` | P05 |
| 解析任务 | `phosphor-duotone/magnifying-glass` | P06, P07 |
| 选择工具 | `phosphor-duotone/target` | P06 |
| 调用 | `phosphor-duotone/plug` | P06 |
| 验证 | `phosphor-duotone/check-circle` | P06, P08 |
| 重试/循环 | `phosphor-duotone/arrows-clockwise` | P06, P10 |
| 汇总 | `phosphor-duotone/stack` | P06 |
| 上下文核心 | `phosphor-duotone/cube` | P07 |
| 重排/筛选 | `phosphor-duotone/funnel` | P07 |
| 截断/平衡 | `phosphor-duotone/scales` | P07 |
| 工具说明 | `phosphor-duotone/gear` | P07 |
| 系统提示 | `phosphor-duotone/code-block` | P07 |
| 可靠性 | `phosphor-duotone/shield-check` | P08 |
| 幻觉 | `phosphor-duotone/sparkle` | P10 |
| 原型阶段 | `phosphor-duotone/crosshair` | P11 |
| 工程化阶段 | `phosphor-duotone/gear-six` | P11 |
| 规模化阶段 | `phosphor-duotone/chart-line-up` | P11 |
| 生产阶段 | `phosphor-duotone/rocket` | P11, P12 |
| 合作号召 | `phosphor-duotone/handshake` | P12 |

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P03 | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST (Political/Economic/Social/Technological), four-pillar strategy overview, side-by-side independent categories. Skip for 2×2 quadrant (use quadrant_text_bullets), pricing tiers (use comparison_columns), or 2×2 parallel aspects (use labeled_card)." | 三大痛点并列展示 |
| P04 | layered_architecture | `templates/charts/layered_architecture.svg` | "Pick for 3-4 horizontal architecture layers (presentation/service/data), 2-4 module cards per layer, each card = title + 1-line description (description required, even if source brief). Skip if no per-module descriptions (use icon_grid) or no horizontal layering (use module_composition)." | Agent 四层架构 (Perception/Reasoning/Action/Memory) |
| P05 | comparison_columns | `templates/charts/comparison_columns.svg` | "Pick for 2-4 pricing/service tier cards in side-by-side columns (marketing layout). Skip for dense feature comparison (use comparison_table)." | Workflow vs Agent vs Multi-Agent 三模式对比 |
| P06 | numbered_steps | `templates/charts/numbered_steps.svg` | "Pick for 3-6 horizontal sequential steps with numeric emphasis — how-it-works section, getting-started guide, methodology overview, implementation phases. Skip if steps need connector arrows (use process_flow) or named output artifacts (use pipeline_with_stages)." | 工具编排六步法 |
| P07 | hub_spoke | `templates/charts/hub_spoke.svg` | "Pick for 1 core capability + 4-8 surrounding capabilities (platform/ecosystem); each spoke = title or title + 1-2 line description. Skip if center is a system containing parts with their own descriptions (use module_composition), or surroundings exert inward pressure on the center (use hub_inward_arrows)." | 上下文工程 — 1 核心 + 6 能力 |
| P08 | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, dashboard headline, quarterly recap, results-at-a-glance. Skip if metrics have target baselines (use bullet_chart) or single hero number (use gauge_chart)." | 4 张 KPI 卡 (Accuracy/Latency/Cost/Reliability) |
| P09 | line_chart | `templates/charts/line_chart.svg` | "Pick for 1-3 time-series on a continuous axis showing direction. Skip if cumulative volume matters (use area_chart) or different units (use dual_axis_line_chart)." | 上线后 12 周准确率 + 成本双线趋势 |
| P10 | quadrant_text_bullets | `templates/charts/quadrant_text_bullets.svg` | "Pick for any 2×2 framework where each quadrant holds a titled bullet list — SWOT (Strengths/Weaknesses/Opportunities/Threats, internal-external × helpful-harmful), Ansoff (Existing/New Markets × Existing/New Products), or any named two-axis matrix with text content. Skip for items plotted as points (use matrix_2x2) or bubble-sized portfolios (use quadrant_bubble_scatter)." | 失败模式四象限 (工具错误/死循环/幻觉/成本失控) |
| P11 | roadmap_vertical | `templates/charts/roadmap_vertical.svg` | "Pick for 4-8 milestones on a vertical timeline with status indicators. Skip for horizontal time emphasis (use timeline) or tasks with durations (use gantt_chart)." | 四阶段落地路线图 |

**Runners-up considered** (3 entries minimum):

- `pyramid_chart` | rejected for P04: Agent 架构需要横向多层 × 每层多模块卡片，pyramid 是纵向单元素分层，无法承载每层 2-3 模块的描述结构
- `icon_grid` | rejected for P03: 三大痛点每个需要 title + 2-3 行 bullet 描述，icon_grid 只配 title + 短副标，深度不够
- `mind_map` | rejected for P07: 上下文工程是聚焦的 1 核心 + 6 能力固定结构，hub_spoke 比 mind_map 更对称稳重（mind_map 偏脑暴 / 不对称扇形）

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| 01_cover_aurora.png | 1280×720 | 1.78 | 封面流光主背景 | Background | #1 full-bleed background with floating title + #29 two-stop scrim + #28 radial gradient vignette | ai | Pending | Deep space backdrop, drifting frosted glass shards in soft orbit, neon blue-purple-cyan light beams streaming horizontally, calm center band reserved for title overlay, no figures or text | none | hero_page |
| 02_hero_transition.png | 1280×720 | 1.78 | "Demo → Production" 转场氛围 | Background | #12 faded image as backdrop with oversized overlay text + #28 radial vignette + #30 flat semi-transparent overlay | ai | Pending | Wide cinematic horizon: a glowing data city rising from violet mist, distant translucent towers and floating glass platforms, sense of crossing from small workshop to large infrastructure, low-contrast central area for hero title | none | hero_page |
| 04_agent_topology.png | 1280×720 | 1.78 | Agent 拓扑神经脉络背景 | Background | #44 background image + native network/architecture diagram + #28 radial vignette + #30 flat overlay | ai | Pending | Abstract agent topology background: glowing neural mesh with constellation nodes connected by thin luminous filaments, soft depth-of-field, frosted glass tiles floating quietly, dark deep-space field with low-contrast working zone, no labels or text | none | local |
| 06_pipeline_flow.png | 1280×720 | 1.78 | 工具调用流光管线 | Background | #39 background image + flow nodes drawn over the scene + #30 flat overlay + #21 rounded rectangle crop | ai | Pending | Translucent data pipelines flowing horizontally behind frosted glass, glowing liquid light traveling through tubes, scattered floating cubes catching reflections, low-detail center band, dark cosmic backdrop | none | local |
| 07_context_sphere.png | 1280×720 | 1.78 | 上下文知识球 / RAG 隐喻 | Background | #42 background image + glassmorphism UI panels + #28 radial vignette + #30 overlay | ai | Pending | Large luminous sphere of light filaments suspended in deep space, fine threads of information radiating outward, smaller glass shards in orbit, slight chromatic aberration, calm dark surrounding for overlay panels | none | local |
| 08_dashboard_bokeh.png | 1280×720 | 1.78 | 仪表盘失焦光斑 | Background | #40 background image + floating KPI metric cards + #34 gaussian blur backdrop baked-in + #30 overlay | ai | Pending | Out-of-focus dashboard scene: rows of soft neon bokeh circles in blue, purple, cyan against deep-space dark, hint of translucent interface panels in the distance, no readable text or numbers | none | local |
| 10_failure_glow.png | 1280×720 | 1.78 | 失败模式警示氛围 | Background | #12 faded image as backdrop with oversized overlay text + #31 color-tinted overlay + #28 radial vignette | ai | Pending | Dark moody field washed with neon pink and violet, fractured glass shards scattered with subtle distortion, faint warning halos, deep-space backdrop, calm working zone in the center | none | local |
| 12_cta_horizon.png | 1280×720 | 1.78 | CTA 收尾远景地平线 | Background | #1 full-bleed background with floating title + #66 image fading into solid background + #29 two-stop scrim | ai | Pending | Distant glowing horizon at dawn of the data era, floating glass platforms drifting toward the light, soft particulate atmosphere, deep navy field grading into warm blue-purple toward horizon, no figures or text | none | hero_page |

---

## IX. Content Outline

### Part 1: 开场

#### Slide 01 - Cover

- **Layout**: Full-bleed AI 背景 + 中央浮玻璃标题面板（Single column centered + #1 + #29）
- **Title**: AI Agent 工程化与落地
- **Subtitle**: 从 Demo 到生产，需要的不只是大模型
- **Info**: 2026 · 技术分享系列

#### Slide 02 - Hero / Section opener "从 Demo 到生产"

- **Layout**: Full-bleed AI 背景 + 大字浮文（breathing — #1 + #12 + #28）
- **Title**: 90% 的 Agent 项目，止步于 Demo
- **Body**: 真正进入生产需要跨越四道工程化门槛 ——
- **Sub-text**: 架构 · 上下文 · 评估 · 可观测
- **Visualization**: 无（breathing 页，纯文字 + AI 氛围背景）

### Part 2: 现状与基础

#### Slide 03 - 三大痛点：为什么 Agent 上不了生产

- **Layout**: 1×3 vertical_pillars（V. 三列）
- **Title**: 三道阻碍 Agent 落地的现实门槛
- **Visualization**: vertical_pillars
- **Content**:
  - 性能不稳定（gauge）：多步推理累积误差，P95 延迟不可控
  - 成本不可预测（coin）：单次任务 token 漂移 5-50 倍
  - 质量难闭环（bug）：失败原因模糊，回归测试缺失

#### Slide 04 - Agent 架构基础：四层模型

- **Layout**: layered_architecture（4 横层）+ #44 AI 背景叠加
- **Title**: Agent 的四层骨架
- **Visualization**: layered_architecture
- **Content**:
  - **Perception 感知** (eye) — 输入解析 / 多模态 / 上下文窗口管理
  - **Reasoning 推理** (brain) — Plan / ReAct / Tree-of-Thought / Reflection
  - **Action 行动** (lightning) — 工具调用 / 函数执行 / API 编排
  - **Memory 记忆** (database) — 短期上下文 / 长期向量库 / 任务级缓存

#### Slide 05 - 三种工作模式对比

- **Layout**: Symmetric 3-column (comparison_columns)
- **Title**: Workflow / Agent / Multi-Agent — 选哪种？
- **Visualization**: comparison_columns
- **Content**:
  - **Workflow** (flow-arrow): 路径固定 / 可预测 / 易调试 / 适用确定性任务
  - **Agent** (robot): 路径动态 / LLM 决策 / 工具调用 / 适用半结构化探索
  - **Multi-Agent** (users-three): 多角色协作 / 任务分发 / 上下文共享 / 适用复杂长程任务

### Part 3: 工程化四大能力

#### Slide 06 - 工具调用与编排：六步法

- **Layout**: numbered_steps（横向 6 步） + #39 AI 管线背景
- **Title**: 让工具调用从"能跑"到"稳跑"
- **Visualization**: numbered_steps
- **Content**:
  - 01 解析任务 (magnifying-glass) — 拆解用户意图
  - 02 选择工具 (target) — schema 匹配 + 描述检索
  - 03 调用执行 (plug) — 参数填充 + 超时控制
  - 04 验证返回 (check-circle) — JSON schema / 业务规则
  - 05 重试回退 (arrows-clockwise) — 指数退避 / 降级路径
  - 06 结果汇总 (stack) — 多轮聚合 → 最终回答

#### Slide 07 - 上下文工程：1 核 + 6 能力

- **Layout**: hub_spoke（中心 + 6 外围） + #42 AI 球体背景
- **Title**: 上下文，才是 Agent 真正的"权重"
- **Visualization**: hub_spoke
- **Content**:
  - **核心** (cube): Context Engineering
  - **检索** (magnifying-glass): RAG / 向量召回 / BM25 混排
  - **重排** (funnel): Reranker / Top-K 筛选
  - **截断** (scales): Token 预算分配 / 关键信息优先
  - **记忆** (database): 长短期记忆 / 会话状态
  - **工具说明** (gear): Tool schema / 示例描述
  - **系统提示** (code-block): Persona / 输出格式 / 安全规则

#### Slide 08 - KPI 仪表板：盯住四个数

- **Layout**: kpi_cards 2×2 + #40 AI bokeh 背景
- **Title**: 上生产前，先把四张表盘装上
- **Visualization**: kpi_cards
- **Content**:
  - **任务成功率** (check-circle): 92.4% ↑ 3.2pp / 周
  - **P95 延迟** (gauge): 4.8s ↓ 18% / 周
  - **单次成本** (coin): ¥0.42 ↓ 22% / 周
  - **可靠性** (shield-check): 99.7% SLO / 30 天

#### Slide 09 - 指标趋势：上线后 12 周

- **Layout**: 全宽 line_chart（双线 — 准确率 + 成本）
- **Title**: 持续优化的真实曲线：准确率 ↑ 成本 ↓
- **Visualization**: line_chart
- **Content**:
  - Series A: 任务成功率（左轴 %，从 71% → 92.4%）
  - Series B: 单次平均成本（右轴 ¥，从 1.20 → 0.42）
  - 12 周时间轴 W1-W12，关键节点：W4 引入 reranker / W8 引入 fallback / W11 引入缓存

#### Slide 10 - 失败模式四象限

- **Layout**: quadrant_text_bullets 2×2 + #12 AI failure 背景
- **Title**: 这四类失败，你最先会遇到哪个
- **Visualization**: quadrant_text_bullets
- **Content**:
  - **工具错误** (bug): schema 不匹配 / 参数幻觉 / 超时无回退
  - **死循环** (arrows-clockwise): 反思链路无终止 / Plan 反复修改
  - **幻觉** (sparkle): 编造工具 / 编造结果 / 假装成功
  - **成本失控** (coin): Token 漂移 / 重复检索 / 链路过长

### Part 4: 落地与收尾

#### Slide 11 - 落地路线图：四阶段

- **Layout**: roadmap_vertical（4 milestone 纵向）
- **Title**: 从原型到生产 — 12 周分四阶段走
- **Visualization**: roadmap_vertical
- **Content**:
  - **W1-W3 原型** (crosshair): 单一任务跑通 + 工具 schema 初稿
  - **W4-W7 工程化** (gear-six): 评估集 + 自动测试 + 回退机制
  - **W8-W10 规模化** (chart-line-up): 缓存 + 限流 + 多租户隔离
  - **W11-W12 生产** (rocket): 灰度上线 + SLO 监控 + 持续优化

#### Slide 12 - CTA / Closing

- **Layout**: breathing — Full-bleed AI 远景 + 中央 CTA 玻璃面板（#1 + #66 + #29）
- **Title**: 下一个 Agent，从工程化开始
- **Body**: 不是"加个 LLM"，是把 LLM 真正装进系统
- **CTA**: 立刻开始你的 Agent 工程化（rocket / handshake）

---

## X. Speaker Notes Requirements

One file per page, saved to `notes/`:

- **Filename**: match SVG name (e.g., `01_cover.md`)
- **Total duration**: 12-15 分钟
- **Style**: conversational + 技术分享
- **Purpose**: inform + persuade（说服决策者把 Agent 工程化提上日程）

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>`（`<foreignObject>` FORBIDDEN）
4. Transparency uses `fill-opacity` / `stroke-opacity`；`rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. Text characters: raw Unicode (`—`, `→`, `©`, NBSP)；HTML named entities FORBIDDEN；XML reserved chars escape as `&amp; &lt; &gt; &quot; &apos;`
7. `clipPath` 仅可用在 `<image>` 上（rounded crop 等）
8. `<g opacity>` FORBIDDEN — 每个 child 单独设 opacity

### Glassmorphism 实现专项

- 玻璃面板：`<rect fill="url(#glassPanel)" stroke="#FFFFFF" stroke-opacity="0.18" stroke-width="1" rx="16"/>`
- 玻璃描边高光线：`<rect ... fill="url(#glassEdge)" height="1"/>` 放在面板顶边
- 不允许使用 `<feGaussianBlur>` 做毛玻璃模糊效果（PPT 导出不稳定）——氛围由 AI 图承担
- 流光霓虹效果通过半透明叠层 `<rect fill="primary" fill-opacity="0.15-0.25"/>` 模拟
- 阴影若需，使用 `<feDropShadow>` 仅在装饰元素，不在主结构

### PPT Compatibility Rules

- `<g opacity="...">` FORBIDDEN
- 图像透明用 overlay mask layer
- Inline styles only；no external CSS / `@font-face`
