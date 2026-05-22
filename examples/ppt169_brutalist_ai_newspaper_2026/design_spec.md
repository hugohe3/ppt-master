# ppt169_ai_industry_2026 — Design Spec

> Brutalist editorial newspaper · capability-showcase demo for PPT Master roadmap §P0-2
> Source: `sources/ai_industry_2026.md` (compiled May 2026 from Counterpoint / Stanford HAI / OneTrust / Deluair / IEEE Spectrum)

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | ppt169_ai_industry_2026 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | B) General Consulting + Brutalist editorial newspaper |
| **Target Audience** | AI 行业从业者 / 投资人 / 研究者 / 关心 AI 转折点的科技读者 |
| **Use Case** | 年报式行业回顾 — 论坛 / brown-bag / 投资者季报开场 |
| **Created Date** | 2026-05-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/Right 48px, Top/Bottom 40px (报章式 narrow margins) |
| **Content Area** | 1184×640 |

---

## III. Visual Theme

### Theme Style

- **Style**: Brutalist editorial newspaper — 满版小字 + 不规则栏宽 + 真原生 shape 框线 + halftone 黑白图 + 单点红强调
- **Theme**: Light theme (报章纸白底)
- **Tone**: 严肃、克制、信息密度顶级、reportorial

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | 主背景（纸白） |
| **Secondary bg** | `#F4F1EA` | sidebar / pull-quote / 边栏纸黄 |
| **Primary** | `#111111` | 主形状 / rule line / 主文字 |
| **Accent** | `#C8102E` | 红色强调 — masthead 一条红线、关键数据点、`The Number` 锚点（全文 <5%） |
| **Secondary accent** | `#3A3A3A` | 次文字 / annotation / footer |
| **Body text** | `#111111` | 主文字 |
| **Secondary text** | `#3A3A3A` | 次文字 / caption |
| **Tertiary text** | `#6B6B6B` | footnote / 页码 |
| **Border/divider** | `#000000` | 报章框线、栏分隔、cell border |
| **Success** | `#1A6E3A` | 正向数据点（极少用） |
| **Warning** | `#A02014` | 负向数据点（极少用） |

### AI Image Strategy

- **Image Rendering**: editorial
- **Image Palette**: mono-ink

> 报章纪实风：halftone 颗粒、纸纹质感、clean partition、黑墨平涂、可在墨黑主体之外让单点红 `#C8102E` 出现一次（如红印章 / 红圈标注 / 红 underline）。

---

## IV. Typography System

### Font Plan

**Typography direction**: Brutalist newspaper — display sans 黑体头条 × serif 衬线小字正文 × monospace 数据，三种家族强对比

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title (masthead / 头条)** | `SimHei` | `Impact, "Arial Black"` | `sans-serif` |
| **Subtitle / Section label** | `SimHei` | `"Arial Black"` | `sans-serif` |
| **Body (报章 column)** | `SimSun` | `"Times New Roman"` | `serif` |
| **Emphasis** | `SimSun` | `Georgia` | `serif` |
| **Code / 数据** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Impact, "Arial Black", SimHei, sans-serif`
- Subtitle: `"Arial Black", SimHei, sans-serif`
- Body: `"Times New Roman", SimSun, serif`
- Emphasis: `Georgia, "Times New Roman", SimSun, serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = **14px** (满版小字密度，比常规 dense 18px 更密，是 Brutalist 报章典型阅读节奏)

| Purpose | Ratio to body | Px @ body=14 | Weight |
| ------- | ------------- | ------------ | ------ |
| Cover masthead (THE AI INDUSTRY 2026) | 5-6x | 72-90 | Black |
| Section opener / 头条 | 3-4x | 42-56 | Black |
| Page title | 2-2.5x | 28-36 | Bold |
| Hero number (报章大数字) | 3.5-5x | 50-72 | Black |
| Subtitle / Section label | 1.4-1.6x | 20-22 | SemiBold |
| **Body content** | **1x** | **14** | Regular |
| Annotation / caption | 0.75-0.85x | 11-12 | Regular |
| Page number / footnote / imprint | 0.6-0.75x | 9-10 | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: Masthead/page-header 64px (顶部红线 4px + 报章标题栏 60px)
- **Content area**: 568px (报章主体；多栏不规则栏宽)
- **Footer area**: 28px (imprint / page number / date)

### Layout Pattern Library

Brutalist 报章主要用：
- **Asymmetric multi-column** (2/3/4 栏不等宽) — 不规则栏宽是核心特征
- **Top-band + multi-column** — 大图压顶 + 下方多栏
- **Sidebar column** (image 或 pull-quote) — 整页右侧或左侧固定边栏
- **Hero number + body** — 单个巨型数字 + 解释栏
- **Rule-line grid** — 用粗细 rule line 分割，不用 box card
- **Center-radiating** — 用于 P06 KPI overlay

### Spacing Specification

**Universal**:

| Element | Range | Current |
| ------- | ----- | ------- |
| Safe margin from canvas edge | 40-60px | **48px L/R, 40px T/B** |
| Content block gap | 16-24px | **20px** |
| Column gap (rule line gutter) | 14-20px | **16px** |

**Non-card containers** (Brutalist 报章基本不用 card，全靠 rule line 分割):

- Line-height: 1.35-1.45× body font size (报章紧凑节奏)
- Body column width: 220-340px (3-4 栏典型)
- Rule line stroke: 0.5px hairline / 1px standard / 2-3px section divider / 4px masthead red bar

---

## VI. Icon Usage Specification

**不使用 icon library**。Brutalist 报章靠 typography + rule line + halftone 图说话，icon 反而稀释力度。

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P02 | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, dashboard headline," | 头版 4 个核心 KPI： $2.02T 支出 / 3.8B 用户 / $20.7B Q1 收入 / 1000+ 政策 |
| P03 | horizontal_bar_chart | `templates/charts/horizontal_bar_chart.svg` | "Pick for ranking 5-12 items, especially with long labels. Skip if <=8 short-label items (use bar_chart)." | LLM 收入份额 Q1 2026 ranking — Anthropic / OpenAI / Google / MSFT / Tencent / Baidu / Alibaba / Meta / Grok / Perplexity |
| P04 | dumbbell_chart | `templates/charts/dumbbell_chart.svg` | "Pick for before-vs-after or two-state difference across 5-10 items. Skip for single snapshot (use bar_chart) or 3+ states" | ARPU 差距对比：5 大 lab 的 MAU vs 月 ARPU 两态 |
| P05 | line_chart | `templates/charts/line_chart.svg` | "Pick for 1-3 time-series on a continuous axis showing direction. Skip if cumulative volume matters (use area_chart) or d" | 训练成本时间轨迹 GPT-4 → Llama 3.1 → Gemini Ultra → 2026 frontier → 2027 projected |
| P06 | bar_chart | `templates/charts/bar_chart.svg` | "Pick for single-series category value comparison, 3-8 categories. Skip for >12 long-label items (use horizontal_bar_char" | 推理功率对比 W/query：Claude 4 Opus / GPT-4 / Gemini 2.5 / DeepSeek V3 / Llama 3.1 |
| P07 | dumbbell_chart | `templates/charts/dumbbell_chart.svg` | "Pick for before-vs-after or two-state difference across 5-10 items. Skip for single snapshot (use bar_chart) or 3+ states" | Benchmark 饱和：SWE-bench / HLE / PhD-QA / Math 多项 2024 → 2025 跳变 |
| P08 | comparison_table | `templates/charts/comparison_table.svg` | "Pick for 2-4 plans/products compared across many feature rows (dense matrix). Skip for pricing-tier marketing layout (us" | 三套监管对照：EU / US / China 在生效日期 / 罚则 / 范围 / 重点上的差异 |
| P09 | timeline | `templates/charts/timeline.svg` | "Pick for 3-8 milestone events on a horizontal time axis (no duration). Skip for tasks with start/end ranges (use gantt_c" | 2025-01 → 2026-04 6 个里程碑事件 |

**Runners-up considered**:

- `grouped_bar_chart` | rejected for P04: 双态 MAU/ARPU 两端差异巨大（4 数量级），dumbbell 拉开尺度更易读，grouped bar 在差距悬殊时会失衡。
- `vertical_pillars` | rejected for P08: 监管对照是「多行多列」结构化对比，pillars 更适合 1×N 并列单元；comparison_table 更精准匹配「many feature rows」的密度。
- `process_flow` | rejected for P09: 2025-2026 事件是离散里程碑非线性流程，timeline 直接匹配「milestone events on a horizontal time axis」。
- `bullet_chart` | rejected for P02: bullet 需要 target + actual 双值，本页 4 个 KPI 是 standalone 数字无目标值。
- `area_chart` | rejected for P05: 训练成本不是 cumulative volume 而是 model-by-model trajectory，line_chart 更准。

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| p01_cover_hero.png | 1280×720 | 1.78 | 封面 hero 主图 | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | An abstract editorial newspaper photograph: vast information surge depicted as parallel cascading data ribbons descending from the upper darkness into bright reflective floor; silhouette of a lone figure standing at the foot looking up; high-contrast halftone, paper grain, slight motion blur on the ribbons; calm right-side area reserved for masthead title overlay | none | hero_page |
| p03_revenue_leader.png | 480×720 | 0.67 | 收入排行配图 — 侧边图 | #18 image as full-height sidebar column + #70 thin colored matte frame | ai | Pending | A vertical editorial photograph: an empty stage podium with the front sign blank and a smaller secondary podium behind partially in shadow; bright ceiling spotlight only on the front podium; halftone grain; suggests a changing of the guard, no people | none | local |
| p05_training_cost.png | 1280×320 | 4.00 | 训练成本横幅 — 中段横向 banner | #14 horizontal banner strip cutting through mid-section + #70 thin colored matte frame | ai | Pending | An editorial wide photograph of a vast GPU server hall stretching to vanishing point; long aisle between two walls of black server racks with small status lights; cold overhead lighting; halftone, paper grain; reads as scale and power infrastructure | none | local |
| p06_inference_thermal.png | 1280×720 | 1.78 | 推理功率 hero — 浮动 KPI 卡背景 | #40 background image + floating KPI metric cards + #30 flat semi-transparent rectangle overlay | ai | Pending | An editorial photograph: extreme close-up of a single matte-black processor die with intricate etched circuitry visible; ambient heat shimmer above the die surface; one tiny bright red anomaly point at the corner; halftone grain; calm uniform areas reserved for KPI card overlays | none | local |
| p08_regulation_table.png | 1280×280 | 4.57 | 监管对照配图 — 顶部 banner | #5 top-band image + bottom multi-column text + #70 thin colored matte frame | ai | Pending | An editorial wide photograph: three closed leather-bound official folders side by side on a wooden table under raking light, each folder slightly different in age and patina; a single bold rubber stamp impression visible on the center folder; halftone, paper grain; suggests three regulatory traditions | none | local |

---

## IX. Content Outline

### Part 1: Masthead

#### Slide 01 - Cover (Masthead)

- **Layout**: Full-bleed hero image + 顶部 4px 红线 + 大字 masthead overlay 在右下calm region
- **Title**: `THE AI INDUSTRY 2026`
- **Subtitle**: `Annual Report — Volume 1, Edition 1`
- **Info**: `Compiled May 2026 · Sources: Stanford HAI · Counterpoint · OneTrust · Deluair · IEEE Spectrum`
- **Tagline (red accent)**: `THE YEAR THE LEAGUE TABLE CHANGED.`

### Part 2: Front Page

#### Slide 02 - Issue at a Glance

- **Layout**: Top page-header 红线 + 大字 masthead 复用 + 4 个 KPI 卡（1×4 横排） + 下方三栏短文「Three Observations」
- **Title**: `ISSUE AT A GLANCE`
- **Visualization**: kpi_cards (see VII)
- **KPIs**:
  - `$2.02T` — Worldwide AI spending 2026E (+36% YoY) · Gartner
  - `3.8B` — Monthly LLM users worldwide · Counterpoint
  - `$20.7B` — Quarterly LLM revenue Q1 2026 · Counterpoint
  - `1,000+` — Active national AI policy initiatives across 72 countries · OneTrust
- **Three observations (3 栏 short body)**:
  1. Revenue concentration is breaking from user-count rankings.
  2. Frontier training costs cleared the $200M floor and are heading to $1–3B by late 2027.
  3. Inference cost is falling ~10× per year for the same capability.

### Part 3: Lead Story

#### Slide 03 - Story I: Revenue League Q1 2026

- **Layout**: 左 1/3 侧边 sidebar 图片（podium） + 右 2/3 上 horizontal_bar_chart + 下 pull-quote 红字小评论
- **Title**: `STORY I — REVENUE LEAGUE TABLE`
- **Subtitle**: `Anthropic 31.4 %  vs  OpenAI 29.0 %`
- **Visualization**: horizontal_bar_chart (see VII)
- **Data points**:
  - Anthropic 31.4%, OpenAI 29.0%, Google 12.1%, Microsoft 7.2%, Tencent 4.8%, Baidu 3.6%, Alibaba 2.9%, Meta 1.4%, Grok 1.4%, Perplexity 1.0%, DeepSeek 0.2%, Zhipu 0.1%
- **Pull-quote (red)**: `"FIRST NON-OPENAI LAB IN #1 SINCE THE MODERN LLM ERA BEGAN."`
- **Source line**: `Counterpoint Research · Global LLM Adoption and Revenue Snapshot, Q1 2026`

### Part 4: Sidebar Data

#### Slide 04 - The ARPU Divide

- **Layout**: 全幅 dumbbell_chart 占上 2/3，下方 4-栏 short caption；no image
- **Title**: `THE ARPU DIVIDE — SCALE ≠ MONETISATION`
- **Visualization**: dumbbell_chart (see VII)
- **Data points (MAU left dot · ARPU right dot)**:
  - Meta: ~1,000M MAU · $0.10
  - OpenAI: 900M · $2.20
  - Google: — · $1.10
  - Anthropic: 134M · $16.20
  - Microsoft: — · $5.00
- **Caption body**: Anthropic's per-user revenue is 7.4× OpenAI's, 14.7× Google's, 162× Meta's. Enterprise-API and coding workloads compound faster than consumer free-tier scale.

#### Slide 05 - Frontier Training Cost

- **Layout**: 中段 1280×320 wide banner photo（GPU 走廊） + 上 page title + 下 line_chart + 右侧 annotation 栏
- **Title**: `FRONTIER TRAINING COST — PAST THE HALF-BILLION LINE`
- **Visualization**: line_chart (see VII)
- **Data points**: GPT-4 $78M → Llama 3.1 $170M → Gemini Ultra $191M → 2026 frontier $200-500M → late-2027 projected $1-3B
- **Annotation**: `1e26 – 1e27 FLOPs` (2026 frontier compute range). Power and grid interconnect, not chip supply, are the binding constraint for the late-2027 cohort.

### Part 5: Inside Pages

#### Slide 06 - Inference — Watts per Query

- **Layout**: full-bleed processor die image as canvas + 4 个 floating KPI 卡 + 半透明 overlay 保证可读
- **Title**: `INFERENCE — A 4.6× SPREAD INSIDE THE FRONTIER CLASS`
- **Visualization**: bar_chart (see VII)
- **KPI cards (floating)**:
  - `5 W` Claude 4 Opus per medium prompt
  - `23 W` DeepSeek V3 per medium prompt
  - `10×` Carbon emissions spread (most-vs-least efficient)
  - `~10×/yr` Inference cost decline at constant capability
- **Source**: Stanford HAI AI Index 2026

#### Slide 07 - Capability — Benchmarks Saturated

- **Layout**: 全幅 dumbbell_chart 2024→2025 跳变 + 下方 short body；no image
- **Title**: `CAPABILITY — BENCHMARKS SATURATED FASTER THAN BUILT`
- **Visualization**: dumbbell_chart (see VII)
- **Data points (2024 → 2025)**:
  - SWE-bench Verified (coding): ~60% → ~100% of human baseline
  - Humanity's Last Exam: baseline → +30 pp
  - PhD-level science QA: below baseline → meet/exceed
  - Multimodal reasoning: below baseline → meet/exceed
  - Competition mathematics: below baseline → meet baseline
- **Editorial line**: `THE BENCH-DESIGN COMMUNITY IS NOW PERMANENTLY BEHIND THE MODEL-RELEASE CYCLE.`

### Part 6: Regulation

#### Slide 08 - Three Rulebooks, One Race

- **Layout**: 顶部 1280×280 banner photo (三本文件夹) + 下方 comparison_table 3 列 × N 行
- **Title**: `THREE RULEBOOKS, ONE RACE`
- **Visualization**: comparison_table (see VII)
- **Columns**: EU · United States · China
- **Rows**:
  - Posture — Class-of-model regulation · Sector + state regulation · Output-tagging regulation
  - Core instrument — AI Act · EO 14179 + state laws · Gen-AI Services Mgmt Measures
  - Full force — August 2025 · No federal statute · Watermark rules effective 2025-09-01
  - Max penalty — €35M or 7 % turnover · Varies by state · Administrative + license revocation
  - Frontier focus — General-purpose AI w/ systemic risk · Innovation-first reframing · Domestic data + party-aligned standards
- **Closing line**: `Convergence on principle, divergence on implementation.`

### Part 7: Timeline

#### Slide 09 - 2025-2026 Timeline

- **Layout**: 全幅 horizontal timeline + 上 page title + 下 6 个 milestone 注释栏
- **Title**: `2025 – 2026 — SIX MILESTONES`
- **Visualization**: timeline (see VII)
- **Milestones**:
  - 2025-01 · US EO 14179 signed — Federal posture reversed
  - 2025-08 · EU AI Act takes full effect — First binding horizontal AI statute on a major economy
  - 2025-09 · China synthetic-content rules effective — First state-mandated watermark regime at frontier scale
  - 2025-Q4 · DeepSeek-R1 released — Open-weights reasoning at frontier-adjacent capability
  - 2026-Q1 · Anthropic overtakes OpenAI on LLM revenue — First non-OpenAI lab in #1
  - 2026-04 · Stanford HAI AI Index 2026 published — First year SWE-bench Verified saturated

### Part 8: Closing

#### Slide 10 - What Changed, What Didn't

- **Layout**: 二栏纯文字 (breathing) — 左栏「CHANGED」红字 section header + 4 行；右栏「DID NOT CHANGE」黑字 section header + 4 行；底部 imprint footer
- **Title**: `WHAT CHANGED · WHAT DIDN'T`
- **Visualization**: none
- **Changed (left column, red header)**:
  - Revenue leader no longer the user-count leader.
  - Frontier training cost crossed the half-billion line per run.
  - Inference power-per-query became a 4.6× discriminator inside the frontier class.
  - Benchmark half-life dropped from years to months.
- **Did not change (right column, black header)**:
  - Frontier cohort still ~5 labs. No Tier-1 added or removed since 2024.
  - China frontier labs still have $0 of EU-market revenue.
  - Open-weights distribution still does not translate to direct revenue capture.
  - Power and grid interconnect remain the single hardest input to source.
- **Imprint footer**: `THE AI INDUSTRY 2026 · Annual Report · Volume 1, Edition 1 · Compiled May 2026 · PPT Master ☐ AI Newspaper Demo`

---

## X. Speaker Notes Requirements

- **File naming**: match SVG names (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Total presentation duration**: ~12-15 minutes
- **Notes style**: formal, reportorial — match Brutalist newspaper tone
- **Purpose**: inform (年报式 industry briefing)

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` (`#FFFFFF` 纸白)
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. Text chars: raw Unicode for typographic marks (em dash `—`, en dash `–`, `→`, NBSP, `©`); HTML named entities FORBIDDEN
7. `marker-start` / `marker-end` conditionally allowed (triangle / diamond / circle in `<defs>` with `orient="auto"`)
8. `clipPath` only on `<image>` (used here on hero / sidebar / banner photos)

### PPT Compatibility Rules

- `<g opacity="...">` FORBIDDEN — set opacity per child
- Image transparency via overlay `<rect fill="bg" opacity="0.x"/>`
- Inline styles only; external CSS / `@font-face` FORBIDDEN
- Stick to PPT-safe fonts in `typography` stacks; converter writes first Latin + first CJK only
