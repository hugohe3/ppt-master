# 高层住宅"主动再生" - Design Spec

> 基于微信公众号文章《香港火灾之后，再也不敢买高层了，"主动再生"能解决高层住宅难题吗？》的演示文稿设计规范。

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 高层住宅"主动再生" — 从悉尼范本到中国困局 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 15 |
| **Design Style** | A) General Versatile + Editorial Magazine（编辑杂志风） |
| **Target Audience** | 城市更新/建筑/地产从业者、政策研究者、关心居住安全的城市居民 |
| **Use Case** | 议题分享 / 行业沙龙 / 内部传阅 |
| **Created Date** | 2026-05-16 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px，上下 50px |
| **Content Area** | 1160×620（安全区） |

---

## III. Visual Theme

### Theme Style

- **Style**: 编辑杂志风（editorial magazine） — 长文摘编 + 案例图片 + 观点提炼
- **Theme**: 浅色主题（米白纸感）
- **Tone**: 沉稳、有思辨张力、可读性强；像《三联生活周刊》《看理想》专题

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F5F2EC` | 米白纸感页面底色 |
| **Secondary bg** | `#EBE6DC` | 卡片/分栏次级底 |
| **Primary** | `#2B3A4A` | 深石板蓝灰 — 标题、正文主色 |
| **Secondary accent** | `#5A6B7A` | 次级文字、分割线 |
| **Accent (warning)** | `#C2410C` | 警示橙红 — 火灾、风险话题 |
| **Accent (regen)** | `#6B7A4F` | 苔绿 — 再生、可持续话题 |
| **Accent (heritage)** | `#8B7355` | 砖褐 — 建筑、历史话题 |
| **Body text** | `#2B3A4A` | 正文 |
| **Secondary text** | `#5A6B7A` | 注释、来源 |
| **Tertiary text** | `#8A8275` | 页码、页脚 |
| **Border/divider** | `#D6CFC0` | 分割线 |

> 60-30-10：米白底 60% / 深蓝灰 30% / 橙红+苔绿+砖褐合计 10%。每页主题色按内容选用（火灾页用橙红、再生页用苔绿、建筑案例页用砖褐）。

---

## IV. Typography System

### Font Plan

**Typography direction**: Cool serif（学术编辑） + 中文楷体引言

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `KaiTi` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `KaiTi` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Georgia, KaiTi, serif`（拉丁先行，杂志感）
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `KaiTi, Georgia, serif`（楷体引言/案例名）
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body = 20px（中等密度，适合科普长文）

| Purpose | Ratio | Px | Weight |
| ------- | ----- | -- | ------ |
| Cover title | 3-4x | 60-80 | Bold |
| Chapter opener | 2.2-2.5x | 44-50 | Bold |
| Page title | 1.6-1.8x | 32-36 | Bold |
| Subtitle | 1.2-1.4x | 24-28 | SemiBold |
| **Body** | **1x** | **20** | Regular |
| Annotation | 0.7-0.8x | 14-16 | Regular |
| Page number | 0.6x | 12 | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 80px — 章节编号（罗马数字）+ 页码 + 细分割线
- **Content area**: 540px — 自由排布，多种 image-layout-pattern 混用
- **Footer area**: 40px — 页脚来源/页码

### Layout Pattern Library

按内容选用：单栏居中（封面/结语）、不对称分栏（案例对照）、全屏图+浮字（章节扉页/hero 页）、图文叠压、并置对照（改造前后）、多图拼贴（全球案例巡览）、负空间驱动（金句页）。

### Spacing Specification

**Universal**:
- Safe margin: 60px 左右 / 50px 上下
- Content block gap: 28-36px
- Icon-text gap: 12px

**Non-card containers**（编辑杂志风以分割线和留白为主，少量卡片）:
- Line-height: 1.5× body
- Full-bleed text: 文字浮于图上时加 0.4-0.6 不透明遮罩

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-outline`（线条 stroke=2，编辑风格首选）
- **Usage**: SVG 占位 `<use data-icon="tabler-outline/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 火灾/警示 | `tabler-outline/flame` | P03 |
| 时间/楼龄 | `tabler-outline/clock` | P03 |
| 建筑/塔楼 | `tabler-outline/building-skyscraper` | P04, P12 |
| 维修/工具 | `tabler-outline/tool` | P04 |
| 再生/循环 | `tabler-outline/refresh` | P06, P07 |
| 树叶/可持续 | `tabler-outline/leaf` | P07 |
| 拆除/爆破 | `tabler-outline/bomb` | P05 |
| 地图/位置 | `tabler-outline/map-pin` | P09, P10, P11 |
| 资金/钱袋 | `tabler-outline/coin` | P12 |
| 用户/居民 | `tabler-outline/users` | P13 |
| 检查/体检 | `tabler-outline/clipboard-check` | P13 |
| 引用/金句 | `tabler-outline/quote` | P14 |

> Executor 生成时如发现额外图标需求，在 `tabler-outline/` 目录内 `ls | grep` 查找最近邻；不混库。

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P02 | agenda_list | `templates/charts/agenda_list.svg` | "Pick for table of contents, meeting agendas, or presentation roadmap — numbered items + brief description + duration / owner per row." | 全篇议程导览（4 部分） |
| P13 | numbered_steps | `templates/charts/numbered_steps.svg` | "Pick for 3-6 horizontal sequential steps with numeric emphasis — how-it-works section, getting-started guide, methodology overview, implementation phases." | "先体检、后更新"治理流程 4 步 |

**Runners-up considered**:

- `vertical_list` | rejected for P02：议程页通常需要章节编号 + 简述列项，agenda_list 更专门，vertical_list 过于通用
- `process_flow` | rejected for P13：内容是治理理念的并列阶段而非箭头连接的工作流，numbered_steps 更贴合
- `pros_cons_chart` | rejected for P12：高层住宅改造困局是单边复杂论述，不是清晰的利弊对照，故走自由设计

> 其它页面以叙述 + 图片为主，走自由设计（编辑杂志拼贴/分栏/hero），不强行套图表模板。

---

## VIII. Image Resource List

> 用户提供 25 张原文配图，全部已就位 `images/`。布局采用多样化 image-layout-pattern，不全用左右/上下分栏。

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- |
| 640.png | 606x991 | 0.61 | 香港高层夜景（封面背景） | Background | #1 full-bleed background with floating title | user | Existing | 城市夜景，灯火密集的超高层建筑 |
| 640_1.png | 1080x917 | 1.18 | 电影《焚城》剧照 | Photography | #38 background image + annotation cards | user | Existing | 高层火灾电影场景，警示氛围 |
| 640_2.png | 1080x648 | 1.67 | 普鲁特·艾格住宅区 | Photography | #48 side-by-side comparison（与 640_3 并置） | user | Existing | 美国失败住宅区原貌 |
| 640_3.png | 660x521 | 1.27 | 普鲁特·艾格被爆破 | Photography | #48 side-by-side comparison（与 640_2 并置） | user | Existing | 1972 年爆破拆除瞬间 |
| 640_4.png | 801x1200 | 0.67 | 改造前 AMP 中心 | Photography | #44 before-after split-screen（与 640_5 并置） | user | Existing | 老旧办公塔楼原貌 |
| 640_5.png | 1080x2172 | 0.50 | 改造后 Quay Quarter Tower | Photography | #44 before-after split-screen（与 640_4 并置） | user | Existing | 全新摩天楼正面竖幅 |
| 640_6.png | 750x1000 | 0.75 | Quay Quarter Tower 细节 1 | Photography | #2 left-third image / right-side text | user | Existing | 弧形顶部呼应港湾 |
| 640_7.png | 1080x440 | 2.45 | Quay Quarter Tower 细节 2 | Photography | #5 top-bottom band（超宽） | user | Existing | 摩天楼远景超宽幅 |
| 640_8.png | 1080x1166 | 0.93 | Quay Quarter Tower 细节 3 | Photography | #41 image-as-canvas + KPI overlay | user | Existing | 建筑近景，叠加环保数据 |
| 640_9.png | 640x345 | 1.86 | 改造前深圳妇儿大厦 | Photography | #44 before-after split-screen（与 640_10 并置） | user | Existing | 老旧大厦原貌 |
| 640_10.png | 1080x1620 | 0.67 | 改造后深圳妇儿大厦 | Photography | #44 before-after split-screen（与 640_9 并置） | user | Existing | 彩色网格立面新貌 |
| 640_11.png | 600x781 | 0.77 | 改造前华东电力大楼 | Photography | #44 before-after split-screen（与 640_12 并置） | user | Existing | 1988 年原貌 |
| 640_12.png | 1080x720 | 1.50 | 改造后艾迪逊酒店 | Photography | #44 before-after split-screen（与 640_11 并置） | user | Existing | 节能改造后立面 |
| 640_13.png | 1080x718 | 1.50 | 纽约 One Wall Street 改造后 | Photography | #2 left-third image / right-side text | user | Existing | 装饰艺术风格摩天楼 |
| 640_14.png | 1080x608 | 1.78 | One Wall Street 公寓内景 | Photography | #20 polaroid stack | user | Existing | 室内空间细节 |
| 640_15.png | 469x581 | 0.81 | 城市建筑氛围 | Atmosphere | #6 atmospheric backdrop with overlay | user | Existing | 玻璃幕墙仰视 |
| 640_16.png | 1080x1439 | 0.75 | 北京"办公环橙"项目 | Photography | #3 right-third image / left-side text | user | Existing | 高层住宅改办公楼案例 |
| 640_17.png | 640x400 | 1.60 | MUJI 改造老旧公寓 | Photography | #20 polaroid stack（与 640_16 拼贴） | user | Existing | 日式翻新房间 |
| 640_18.png | 1080x1440 | 0.75 | 高层住宅外景氛围 | Atmosphere | #6 atmospheric backdrop with overlay | user | Existing | 高层楼群仰视 |
| 640_19.png | 1080x810 | 1.33 | 改造前浙工新村 | Photography | #44 before-after split-screen（与 640_20 并置） | user | Existing | 80 年代老旧小区 |
| 640_20.png | 1080x619 | 1.74 | 浙工新村建成效果图 | Photography | #44 before-after split-screen（与 640_19 并置） | user | Existing | 原拆原建效果图 |
| 640_21.png | 870x580 | 1.50 | 居民议事氛围 | Atmosphere | #38 background image + annotation cards | user | Existing | 社区共建共治氛围 |
| 640_22.png | 1074x806 | 1.33 | 城市更新/体检氛围 | Photography | #2 left-third image / right-side text | user | Existing | 城市俯瞰，体检意象 |
| 640_23.png | 1080x723 | 1.49 | 城市天际线（结语） | Background | #1 full-bleed background with floating title | user | Existing | 结语 hero 大图 |
| 640_24.png | 640x640 | 1.00 | 圆形建筑装饰元素 | Decorative | #21 circular crop accent | user | Existing | 装饰圆图，章节扉页 accent |

> Layout 多样性自检：含 #1（hero）、#2/#3（不对称分栏）、#5（超宽 band）、#6（氛围背景）、#20（polaroid 拼贴）、#21（圆裁饰角）、#38（背景+卡）、#41（image-as-canvas + 叠数据）、#44（before-after 对照）、#48（并置对比）共 10 种 pattern；Group D 覆盖：P08（#41 image-as-canvas + KPI 叠层）。

---

## IX. Content Outline

### Part 1: 引子 — 从一场火灾说起

#### Slide 01 - Cover

- **Layout**: 全屏 hero 背景 + 浮字标题（Pattern #1）
- **Title**: 主动再生
- **Subtitle**: 香港火灾之后，老旧高层何去何从
- **Info**: 基于公众号《孙琬童》原文 · 2026.05
- **Image**: 640.png（高层夜景）

#### Slide 02 - Agenda

- **Layout**: 单列议程（agenda_list）
- **Title**: 本次议程
- **Visualization**: agenda_list（4 项）
- **Content**:
  - I. 警钟：高层老龄化与消防困局
  - II. 范本：悉尼摩天楼的"再生革命"
  - III. 巡览：全球功能再造案例
  - IV. 困局：中国老旧高层住宅的硬骨头

### Part 2: 警钟 — 高层老龄化与消防困局

#### Slide 03 - 香港火灾敲响警钟

- **Layout**: 背景图 + 注释卡（Pattern #38）
- **Title**: 一场火灾，暴露的不只是消防隐患
- **Content**:
  - 2025.11.26 香港大埔宏福苑：7 栋 30 层以上、近百米高、楼龄 42 年
  - 2025 年前 8 个月全国高层建筑火灾 **3.6 万起**，超 2023 全年总量
  - 地面消防救援高度通常 50–80 米；超过 100 米主要靠建筑自救
- **Image**: 640_1.png（《焚城》剧照背景）

#### Slide 04 - 高层正在老去

- **Layout**: 不对称分栏 #2（左图右文）
- **Title**: 当年的繁荣象征，正在变成沉重的维修负担
- **Content**:
  - 建成 10 余年后，结构、消防、电梯、外墙等风险密集显现
  - 维护成本随楼龄陡增；愿意住高层的人正在变少
  - "高层住宅是未来的贫民窟" — 西方已有先例
- **Image**: 640_18.png（高层楼群仰视）

#### Slide 05 - 前车之鉴：普鲁特·艾格

- **Layout**: 并置对照（Pattern #48）
- **Title**: 老旧高层只有"被爆破"一条路吗？
- **Content**:
  - 美国普鲁特·艾格：33 栋高层，公共空间长期失养 → 1972 年全部爆破
  - 富裕居民迁出 → 中低收入聚居 → 设施破败 → 高犯罪率 → 拆除
- **Images**: 640_2.png（原貌） + 640_3.png（爆破瞬间）

### Part 3: 范本 — 悉尼摩天楼的"再生革命"

#### Slide 06 - 章节扉页 II

- **Layout**: 全屏背景 + 浮字 + 圆形装饰（Pattern #1 + #21）
- **Title**: II
- **Subtitle**: 悉尼范本 — 一座摩天楼的"再生"革命
- **Image**: 640_24.png（圆形装饰）

#### Slide 07 - Quay Quarter Tower：从拆到改

- **Layout**: Before-after 对照（Pattern #44）
- **Title**: 世界上第一座"全面升级改造"的摩天大楼
- **Content**:
  - 原 AMP 中心：1976 年，206 米，49 层
  - 设计：3XN — "最大化保留、高质量升级"
  - 保留 65% 主体结构 + 95% 核心筒，转型多功能综合体
- **Images**: 640_4.png（改造前） + 640_5.png（改造后）

#### Slide 08 - 环保数据：再生的真正分量

- **Layout**: Image-as-canvas + KPI 叠层（Pattern #41）
- **Title**: 入围"为地球奋斗奖"决赛的关键
- **Visualization**: 三个大数字（hero number）叠在建筑图上
- **Content**:
  - **−80%** 建筑垃圾（结构复用）
  - **−40%** 碳排放（相比推倒重建）
  - **−30%** 能源消耗（智能通风+光伏幕墙+雨水回收）
- **Image**: 640_8.png（建筑近景作底）

### Part 4: 巡览 — 全球功能再造案例

#### Slide 09 - 深圳妇儿大厦（MVRDV）

- **Layout**: Before-after 对照（Pattern #44）
- **Title**: 给老建筑穿一件"彩色网格外衣"
- **Content**:
  - 1994 年建成，MVRDV 主导改造
  - 彩色网格立面增 1 米进深 → 遮阳 + 自然通风
  - 引入酒店、儿童探索馆、图画书博物馆等多种业态
- **Images**: 640_9.png（改造前） + 640_10.png（改造后）

#### Slide 10 - 上海艾迪逊酒店（华东电力大楼）

- **Layout**: Before-after 对照（Pattern #44）
- **Title**: 全国首家城市更新领域**碳中和酒店**
- **Content**:
  - 原 1988 年华东电力大楼，126 米，南京东路第一栋高层
  - 2018 改扩建为艾迪逊酒店；2023 完成节能改造
  - 高性能外窗 + 空气源热泵 + 节能电梯 + 节水器具
- **Images**: 640_11.png（改造前） + 640_12.png（改造后）

#### Slide 11 - 纽约 One Wall Street：办公变住宅

- **Layout**: 不对称分栏 #2（左图右文） + polaroid 拼贴 #20
- **Title**: 1931 年的装饰艺术摩天楼，变成 566 套公寓
- **Content**:
  - 50 层办公塔 → 单间到四居室全户型公寓
  - 办公/商业改住宅是全球趋势：结构强度高、灵活性大
- **Images**: 640_13.png（外景） + 640_14.png（公寓内景 polaroid）

### Part 5: 困局 — 中国老旧高层住宅的硬骨头

#### Slide 12 - 章节扉页 IV

- **Layout**: 氛围背景 + 浮字（Pattern #6）
- **Title**: IV
- **Subtitle**: 高层住宅老了、坏了，该怎么办？
- **Image**: 640_15.png（玻璃幕墙仰视）

#### Slide 13 - 试点案例：北京"办公环橙" + 浙工新村

- **Layout**: 双列拼贴（#3 右图左文 + #44 对照）
- **Title**: 已有的尝试：从功能再造到原拆原建
- **Content**:
  - **办公环橙**（北京天通苑）：高层住宅 → 办公楼，缓解"职住分离"
  - **浙工新村**（杭州）：首个原拆原建老旧小区
    - 拆 13 幢，新建 7 幢 11 层；总投资 5.3 亿，居民自筹 4.7 亿
    - 每户出资 10–100 万元
- **Images**: 640_16.png（办公环橙） + 640_19.png + 640_20.png（浙工新村对照）

#### Slide 14 - 真正的难题：让每家掏钱

- **Layout**: 负空间驱动 — 大字金句 + 注释（Pattern #11）
- **Title**: "原拆原建"在高层项目中，注定极其复杂
- **Content**:
  - **金句**："高层住宅区户数更多，全体业主达成共识的难度大。"
  - 资金从哪来、由谁出 → 仍在探索
  - 出路可能在"共建共治共享"治理模式 — 设立"养老金"、引入"居委会"自管
- **Image**: 640_21.png（社区议事氛围背景）

#### Slide 15 - 结语：先体检、后更新

- **Layout**: 全屏 hero + numbered_steps 4 步
- **Title**: 从追求高度，到沉淀厚度
- **Visualization**: numbered_steps（4 步）
- **Content**:
  - **1. 体检** — 截至 2025.11，全国 297 个地级市 + 150+ 县级市启动城市体检
  - **2. 设计** — 专业机构提供安全可靠方案
  - **3. 协调** — 政府平台 + 社区基层组织
  - **4. 再生** — 多方合力，老旧超高层焕发新机
- **Image**: 640_23.png（城市天际线 hero 背景）

---

## X. Speaker Notes Requirements

- 每页 100–180 字，对应 SVG 同名（`01_cover.md` ↔ `01_cover.svg`）
- 风格：解说式，杂志主持口吻；不堆砌数据，提炼观点
- `notes/total.md` 主文档使用 `#` 章节标题；分页文件不使用 `#`

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. 背景使用 `<rect>` 元素
3. 文字换行使用 `<tspan>`（`<foreignObject>` 禁用）
4. 透明度默认使用 `fill-opacity` / `stroke-opacity`；`rgba()` 保持转换兼容
5. 禁用：`mask`、`<style>`、`class`、`foreignObject`、`textPath`、`animate*`、`script`
6. 字符使用原生 Unicode（— – © ® → NBSP），HTML 命名实体禁用；`&` `<` `>` `"` `'` 必须转义
7. `clipPath` 仅允许用于 `<image>` 元素

### PPT Compatibility Rules:

- opacity 默认设到每个子元素；`<g opacity="...">` 可转换但会产生近似保真 warning
- 图片透明用叠加 `<rect>` 蒙版
- 仅内联样式；外部 CSS 与 `@font-face` 禁用
