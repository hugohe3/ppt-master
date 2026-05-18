# global_ai_capital_2026 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | global_ai_capital_2026 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 18 |
| **Design Style** | B) General Consulting + Bloomberg/Economist 新闻信息图风 |
| **Target Audience** | 科技/金融行业研究者、AI 从业者、风险投资圈、媒体编辑 |
| **Use Case** | 行业洞察分享 / 投资简报 / 媒体解读专栏 |
| **Created Date** | 2026-05-16 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px / 上下 50px |
| **Content Area** | 1160×620（页眉 80 + 主体 560 + 页脚 30） |

---

## III. Visual Theme

### Theme Style

- **Style**: B) General Consulting + Bloomberg/Economist 新闻信息图风
- **Theme**: Dark theme
- **Tone**: 冷静、克制、出版级、数据导向；不是 keynote 冲击力，而是夜读财经长稿的深思感

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0E1116` | 深石墨黑（不是纯黑） |
| **Secondary bg** | `#1A1F26` | 卡片 / 分区底色 |
| **Primary** | `#E8E6E1` | 报纸暖白 — 主文字、标题 |
| **Accent** | `#E63946` | 财经红 — 风险、警示、关键数字 |
| **Secondary accent** | `#F4A261` | 琥珀金 — 次级强调（中国 / 二线公司） |
| **Body** | `#C9C5BE` | 暖灰白 — 正文 |
| **Secondary text** | `#8A857E` | 注释 / 页脚 |
| **Tertiary text** | `#5C5852` | 极轻信息 / 来源行 |
| **Border** | `#2A2F36` | 极细分割线 |
| **Success** | `#52B788` | 正向趋势（绿涨） |
| **Warning** | `#E63946` | 复用 accent |

### AI Image Strategy

- **Image Rendering**: editorial
- **Image Palette**: dark-cinematic

### Gradient Scheme

```xml
<linearGradient id="scrim_v" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#0E1116" stop-opacity="0.3"/>
  <stop offset="100%" stop-color="#0E1116" stop-opacity="0.92"/>
</linearGradient>

<linearGradient id="accentLine" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#E63946" stop-opacity="1"/>
  <stop offset="100%" stop-color="#E63946" stop-opacity="0"/>
</linearGradient>
```

---

## IV. Typography System

**Typography direction**: 报刊编辑派 — 西文衬线 Cambria 扛标题与大字 hero number，中文走 Microsoft YaHei，正文 Latin 用 Arial 走数字精度

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Cambria` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Cambria, "Microsoft YaHei", serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `Georgia, "Microsoft YaHei", serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = **16px**（chart-heavy 高密度）

| Purpose | Ratio to body | Px @ 16 | Weight |
| ------- | ------------- | ------- | ------ |
| Cover title (hero headline) | 4-5x | 64-80px | Bold |
| Chapter / section opener | 2.5-3x | 40-48px | Bold |
| Page title | 1.5-2x | 24-32px | Bold |
| Hero number (大数字) | 4-6x | 64-96px | Bold（Cambria） |
| Subtitle | 1.2-1.5x | 19-24px | SemiBold |
| **Body content** | **1x** | **16px** | Regular |
| Annotation / caption | 0.7-0.85x | 11-14px | Regular |
| Page number / footnote | 0.6-0.7x | 10-11px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 上 50px — 章节番号 + 章节名（左对齐，11px tertiary） + 极细分割线
- **Content area**: 中 560px — 主可视化 / hero number / chart
- **Footer area**: 下 30px — 页码 + Sources 注脚 + 极细顶部分割线

### Layout Pattern Library

> 本 deck 主导布局：**Asymmetric split（3:7 chart vs 注解）/ Single column centered（封面 / 章节）/ Three-column（KPI cards）/ Top-bottom split（带 hero band 的图表 + 注脚）/ Full-bleed + floating text（3 张氛围图章节页）**。Z-pattern 与 Matrix grid 出现在 quadrant_text_bullets 页。

### Spacing Specification

**Universal**:

| Element | Range | This Deck |
| ------- | ----- | --------- |
| Safe margin | 40-60px | 60px |
| Content block gap | 24-40px | 28px |
| Icon-text gap | 8-16px | 10px |

**Card-based**:

| Element | Range | This Deck |
| ------- | ----- | --------- |
| Card gap | 20-32px | 24px |
| Card padding | 20-32px | 22px |
| Card border radius | 8-16px | 6px（克制，不要圆胖） |

**Non-card** (breathing 页 / 氛围底图):
- Line-height: 1.5× body
- Full-bleed text 用 `scrim_v` 渐变扛 legibility
- 不强行列宽对齐，按报刊导语自由 inset

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-outline`（stroke 1.5）
- **Brand-logo library**: `simple-icons`（用于 OpenAI / Anthropic / xAI / Nvidia / Google / Microsoft / Amazon / Meta / Oracle / SoftBank 等 logo 标识）
- **Usage**: `<use data-icon="library/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Trending up（资本流入） | `tabler-outline/trending-up` | P04, P05, P11 |
| Currency dollar（估值） | `tabler-outline/currency-dollar` | P04, P06, P09 |
| Building（公司） | `tabler-outline/building` | P06, P09 |
| Chart bar（数据） | `tabler-outline/chart-bar` | P05, P15 |
| Server（基建） | `tabler-outline/server` | P14, P15 |
| Bolt（电力） | `tabler-outline/bolt` | P05, P14 |
| Alert triangle（风险） | `tabler-outline/alert-triangle` | P15, P16, P17 |
| Globe（全球） | `tabler-outline/globe` | P04, P09 |
| Cpu（芯片） | `tabler-outline/cpu` | P12, P13 |
| Trending down（衰减） | `tabler-outline/trending-down` | P15, P16 |
| Arrow right（流向） | `tabler-outline/arrow-right` | P12, P14 |
| Bookmark（章节标志） | `tabler-outline/bookmark` | 章节页 |
| OpenAI 品牌 | `simple-icons/openai` | P06, P08, P14 |
| Anthropic | `simple-icons/anthropic` | P06 |
| Nvidia | `simple-icons/nvidia` | P12, P13 |
| Google | `simple-icons/google` | P05, P06 |
| Microsoft | `simple-icons/microsoft` | P05 |
| Amazon | `simple-icons/amazon` | P05 |
| Meta | `simple-icons/meta` | P05 |
| Oracle | `simple-icons/oracle` | P14 |
| SoftBank | `simple-icons/softbank` | P14 |

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P04 | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, " | Q1 风投总盘子四大 KPI（VC 总额 / AI 占比 / 三笔大单 / 集中度） |
| P05 | bar_chart | `templates/charts/bar_chart.svg` | "Pick for single-series category value comparison, 3-8 categories. Skip for >12 long-label items (use" | Amazon / Microsoft / Google / Meta 四家 capex 对比 |
| P07 | dumbbell_chart | `templates/charts/dumbbell_chart.svg` | "Pick for before-vs-after or two-state difference across 5-10 items. Skip for single snapshot (use ba" | OpenAI/Anthropic/xAI 估值前后对比（年初 vs Q2） |
| P08 | bubble_chart | `templates/charts/bubble_chart.svg` | "Pick for 3-axis data (x position, y position, size). Skip for plain x-y correlation (use scatter_cha" | 三巨头 估值 × ARR × 投资人数 散点 |
| P09 | donut_chart | `templates/charts/donut_chart.svg` | "Pick for 3-6 part proportions where a center KPI/total deserves emphasis. Skip if no center value to" | OpenAI $122B 投资人构成（Amazon/Nvidia/SoftBank/MSFT/其他） |
| P10 | horizontal_bar_chart | `templates/charts/horizontal_bar_chart.svg` | "Pick for ranking 5-12 items, especially with long labels. Skip if <=8 short-label items (use bar_cha" | 中国阵营 5 家估值排名（DeepSeek/Zhipu/MiniMax/Moonshot/StepFun） |
| P11 | comparison_table | `templates/charts/comparison_table.svg` | "Pick for 2-4 plans/products compared across many feature rows (dense matrix). Skip for pricing-tier " | 中美 AI 资本路径双轨对比（私募规模/IPO/政府/估值峰值/退出方式） |
| P12 | sankey_chart | `templates/charts/sankey_chart.svg` | "Pick for 3-stage flow with magnitude (sources -> nodes -> sinks). Skip for simple linear conversion " | Nvidia 闭环：股权投资 → AI 公司 → 芯片采购回流 |
| P13 | pareto_chart | `templates/charts/pareto_chart.svg` | "Pick for 80/20 contribution: descending bars + cumulative line. Skip if cumulative line is not t" | Nvidia 客户集中度 85% 来自 6 家 |
| P14 | hub_spoke | `templates/charts/hub_spoke.svg` | "Pick for 1 core capability + 4-8 surrounding capabilities (platform/ecosystem); each spoke = title o" | Stargate 项目 hub + 7 个数据中心站点 |
| P16 | dual_axis_line_chart | `templates/charts/dual_axis_line_chart.svg` | "Pick when 2 metrics with different units/scales must be compared over time. Skip if both metrics sha" | 2020-2026 Capex（左轴 $B）vs Enterprise AI Revenue（右轴 $B）剪刀差 |
| P17 | quadrant_text_bullets | `templates/charts/quadrant_text_bullets.svg` | "Pick for any 2×2 framework where each quadrant holds a titled bullet list — SWOT (Strengths/Weakness" | 四大风险象限：资本鸿沟 / 企业 ROI / 客户集中 / 融资结构 |

**Runners-up considered**:

- `donut_chart` | rejected for P04: KPI cards 更适合 4 个独立指标并列展示，donut 强调比例切分而非单独读取
- `stacked_bar_chart` | rejected for P05: 单一指标（capex 金额）对比，无内部分组结构
- `grouped_bar_chart` | rejected for P07: dumbbell 更适合"两状态差值"叙事，grouped bar 适合 YoY 多类别
- `treemap_chart` | rejected for P09: OpenAI 投资人只有 5-6 个独立份额，donut 中心可显总额 $122B，treemap 强调层级
- `radar_chart` | rejected for P10: 5 家公司单一指标（估值）排名，radar 适合多维能力
- `hub_inward_arrows` | rejected for P12: sankey 才能表达"金额流量"，hub_inward 只有方向无量值
- `bar_chart` | rejected for P13: pareto 同时显示个体贡献 + 累积占比，bar 只有前者
- `process_flow` | rejected for P14: hub_spoke 表达"一个中枢 + 多个外围站点"的 Stargate 拓扑，process_flow 暗示线性

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_atmosphere.png | 1280×720 | 1.78 | 封面氛围底图 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | Abstract nighttime aerial of a vast data-center campus, faint server-rack lights forming a constellation pattern; quiet wide-angle composition with reserved dark sky for title overlay; sense of capital flowing through silent infrastructure | none | hero_page |
| nvidia_circular.png | 1280×720 | 1.78 | Part V Nvidia 闭环章节锚点 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | Abstract macro shot of a circular wafer-like geometry with subtle red glow at the rim suggesting circulation; central dark void reserved for chapter title; metallic finish but no recognizable logos | none | hero_page |
| bubble_tension.png | 1280×720 | 1.78 | Part VI 泡沫论章节锚点 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | Abstract atmospheric image of a single iridescent soap-bubble suspended in deep dark space, surface tension catching a faint warning-red highlight; quiet composition with negative space; sense of fragile inflation | none | hero_page |

---

## IX. Content Outline

### Part 0: 开场（封面 + 导语 + 目录）

#### Slide 01 - 封面

- **Layout**: Full-bleed 氛围底图 + 底部 scrim + 左下大字标题
- **Title**: 2026 全球 AI 资本格局
- **Subtitle**: Capital, Compute, and the Closed Loop
- **Info**: 2026 年 5 月 · 行业洞察 · 数据截至 2026-05-15

#### Slide 02 - 编辑导语

- **Layout**: 单栏居中 + 大引号 + 三行核心叙述
- **Title**: 编辑导语 | Editor's Note
- **Content**:
  - 单季 2970 亿美元 VC，AI 拿走 81%
  - 四笔交易 1880 亿美元，65% 流向四家公司
  - 资本与商业 ROI 的鸿沟，已超 2001 电信泡沫期

#### Slide 03 - 目录

- **Layout**: 左侧六部分罗马字 + 右侧每部分页码与一句话标题
- **Title**: 目录 | Contents
- **Content**:
  - I. 全景 — P04-P05
  - II. 三巨头 — P06-P09
  - III. 中国阵营 — P10-P11
  - IV. 二线梯队 — P12
  - V. 基建与闭环 — P13-P15
  - VI. 泡沫与判断 — P16-P18

### Part I: 全景

#### Slide 04 - Q1 风投全景

- **Layout**: 四象限 KPI cards + 顶部小字章节标记
- **Title**: 2026 Q1 全球风投：$297B 创纪录，AI 拿走 81%
- **Visualization**: kpi_cards
- **Content**:
  - $297B — 单季 VC 总额（Crunchbase）
  - 81% — AI 占比（约 $242B）
  - $188B — Top 4 笔大单合计（OpenAI + Anthropic + xAI + Waymo）
  - 65% — 集中度（前 4 单占全季 VC）

#### Slide 05 - Hyperscaler Capex

- **Layout**: Bar chart 左 7 右 3 + 右侧三条关键注解
- **Title**: 四家 Hyperscaler 2026 年 Capex：$725B，同比 +77%
- **Visualization**: bar_chart
- **Content**:
  - Amazon $200B / Microsoft $190B / Alphabet $190B / Meta $145B+
  - 60%+ 流向电力 / 冷却 / 土建，非芯片
  - 资源约束已从"算力"转向"电力"

### Part II: 三巨头

#### Slide 06 - 估值前后对比

- **Layout**: Dumbbell chart + 顶部章节标记
- **Title**: 三巨头 2026 估值跃迁：从年初到 Q2 的双倍线
- **Visualization**: dumbbell_chart
- **Content**:
  - OpenAI: $300B → $852B（Mar 2026）
  - Anthropic: $61.5B → $380B（Series G）→ $900B（在谈）
  - xAI: $50B → $230B（Jan 2026）→ $1.25T 合并 SpaceX

#### Slide 07 - 估值 × 收入 × 投资人

- **Layout**: Bubble chart 全屏 + 角落数据来源
- **Title**: 估值兑现度：收入越高，估值越实
- **Visualization**: bubble_chart
- **Content**:
  - X 轴：ARR（$B），Y 轴：估值（$B），气泡大小：投资人数量
  - OpenAI: ARR $24B / Val $852B / 7 大投资人
  - Anthropic: ARR $30B+ / Val $380B（在谈 $900B）/ 5 大投资人
  - xAI: ARR $5B（est）/ Val $230B / 8+ 投资人

#### Slide 08 - OpenAI 投资人结构

- **Layout**: Donut chart 居左 + 右侧投资人列表
- **Title**: OpenAI $122B 这笔钱从哪来
- **Visualization**: donut_chart
- **Content**:
  - Amazon $50B（41%）
  - Nvidia $30B（25%）
  - SoftBank $30B（25%）
  - Microsoft + 其他 $12B（10%）
  - 中心：$122B / $852B 估值

#### Slide 09 - 三巨头综合对比

- **Layout**: 三列对照 + 顶部小标 + 底部一行总结
- **Title**: OpenAI vs Anthropic vs xAI：三种成长曲线
- **Content**:
  - OpenAI：消费驱动 + 强 IPO 预期
  - Anthropic：企业驱动 + 估值反超 OpenAI（$900B vs $852B）
  - xAI：合并叙事 + SpaceX 协同

### Part III: 中国阵营

#### Slide 10 - 中国五雄

- **Layout**: Horizontal bar chart + 顶部一行总结
- **Title**: 中国 AI 五雄：DeepSeek 领跑，估值阶梯分明
- **Visualization**: horizontal_bar_chart
- **Content**:
  - DeepSeek $50B（国家大基金领投）
  - Zhipu AI（港股市值）$56B
  - MiniMax（港股市值）$37B
  - Moonshot (Kimi) $20B
  - StepFun ~$8B

#### Slide 11 - 中美双轨

- **Layout**: Comparison table（5 行 × 2 列）+ 顶部小标
- **Title**: 中美 AI 资本：两条路径，两种节奏
- **Visualization**: comparison_table
- **Content**:
  - 私募规模：美国 $30-122B 单轮 vs 中国 $2-4B 单轮
  - IPO 节奏：美国推迟 vs 中国 Q1 已落港
  - 政府角色：美国市场驱动 vs 中国大基金领投
  - 估值峰值：美 $852B vs 中 $56B（市值）
  - 退出方式：私募延后 IPO vs 二级市场优先

### Part IV: 二线梯队

#### Slide 12 - 二线 $10-50B 阵营

- **Layout**: 四列卡片（每列：公司 logo + 估值 hero number + 一行特点）+ 顶部小标
- **Title**: 二线梯队：$10-50B 的精英层
- **Content**:
  - SSI $32B（Sutskever，6 倍跳涨）
  - Perplexity $21B（月活 4500 万）
  - Mistral $13.7B（巴黎数据中心 13800 GPU）
  - Cohere + Aleph Alpha 合并 $20B（跨大西洋主权 AI）

### Part V: 基建与闭环

#### Slide 13 - Nvidia 闭环（章节锚点页）

- **Layout**: Full-bleed 氛围底图（nvidia_circular.png）+ 大字章节标 + 底部 scrim + 三句导语
- **Title**: V. 闭环
- **Subtitle**: 当芯片商同时是大股东
- **Content**:
  - Nvidia 2026 至今股权投资 $40B+
  - OpenAI $30B + xAI + Anthropic + Mistral 全到位
  - 收入 85% 来自 6 个客户

#### Slide 14 - Nvidia 资本流图

- **Layout**: Sankey chart 全幅 + 顶部章节标 + 底部 source
- **Title**: 钱怎么转：Nvidia 的圆形投资
- **Visualization**: sankey_chart
- **Content**:
  - 左侧：Nvidia $40B 投资
  - 中间：OpenAI / xAI / Anthropic / Mistral / CoreWeave
  - 右侧：Nvidia 芯片销售回流（数百亿美元算力承诺）

#### Slide 15 - Nvidia 客户集中度

- **Layout**: Pareto chart + 右下风险注解
- **Title**: 单点风险：Nvidia 收入 85% 来自 6 个客户
- **Visualization**: pareto_chart
- **Content**:
  - 前 4 名客户占近 60%（MSFT / Meta / Google / Amazon）
  - 6 名累积 85%
  - 任一家砍 capex 都会级联打击全链

#### Slide 16 - Stargate

- **Layout**: Hub-spoke chart（中心 Stargate logo + 7 个站点辐射）+ 顶部章节标
- **Title**: Stargate：$500B / 10GW / 7 个站点
- **Visualization**: hub_spoke
- **Content**:
  - 中心：Stargate（OpenAI + Oracle + SoftBank）
  - 7 辐射：Abilene TX（运行）/ Shackelford TX / Doña Ana NM / Midwest / Lordstown OH / Milam TX / Saline MI
  - 已规划近 7GW，未来 3 年投入 $400B

### Part VI: 泡沫与判断

#### Slide 17 - 泡沫论章节锚点

- **Layout**: Full-bleed 氛围底图（bubble_tension.png）+ 章节大字 + 底部 scrim + 三行核心论点
- **Title**: VI. 泡沫
- **Subtitle**: 资本主义 vs 商业现实的剪刀差
- **Content**:
  - Capex 增速比 AI 收入快 46 个百分点
  - 2001 电信泡沫期差距为 32%
  - **当前差距已超 2001 电信泡沫**

#### Slide 18 - Capex vs Revenue 剪刀差

- **Layout**: Dual-axis line chart + 顶部章节标 + 底部 source
- **Title**: 资本与营收的鸿沟：$400B 投入 vs $100B 营收
- **Visualization**: dual_axis_line_chart
- **Content**:
  - 左轴：Hyperscaler Capex（$B）2020-2026
  - 右轴：Enterprise AI Revenue（$B）2020-2026
  - 阴影：两线之间的 ROI Gap

#### Slide 19 - 四大风险

- **Layout**: 2×2 quadrant + 每象限标题 + 2-3 行 bullet
- **Title**: 四大风险，互相放大
- **Visualization**: quadrant_text_bullets
- **Content**:
  - 左上 Capex/Revenue 鸿沟：差距已超 2001 电信泡沫
  - 右上 企业 ROI：MIT 95% 试点未产生商业价值
  - 左下 客户集中：Nvidia 85% 来自 6 家
  - 右下 融资结构：经营现金流 → 举债融资

#### Slide 20 - 六大判断与结语

- **Layout**: 单栏 6 行编号列表 + 底部 Sources 致谢
- **Title**: 六大判断 | Closing
- **Content**:
  - ① 资本集中度是 2026 主旋律
  - ② 算力是真硬通货
  - ③ 电力 > 芯片
  - ④ 中美双轨结构
  - ⑤ 真实 ROI 滞后但巨头未止血
  - ⑥ Anthropic 估值反超 OpenAI

> 注：实际页数 = 20（封面 1 + 导语 1 + 目录 1 + 内容 16 + 结语 1）。Strategist 在八项确认中报告 18 页，含编辑导语后微调至 20 页以保持单页一论点的密度。

---

## X. Speaker Notes Requirements

- 文件命名：与 SVG 同名（`01_cover.svg` → `notes/01_cover.md`）
- 单页 100-150 字，编辑导语派口吻，不是销售也不是教学
- 全 deck 总时长目标：15-20 分钟

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background 用 `<rect>`
3. Text wrap 用 `<tspan>`
4. 透明度用 `fill-opacity` / `stroke-opacity`
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`, `<symbol>`+`<use>` 自定义, `<g opacity>`, rgba()
6. HTML named entities 禁用，写 raw Unicode
7. `marker-start` / `marker-end` 仅 `<marker>` in `<defs>` 且 orient="auto"
8. `clipPath` 仅作用于 `<image>`，且 single shape child

### PPT Compatibility:

- Inline styles only
- 每个元素单独设 opacity
- 字体栈每条以预装字体收尾
