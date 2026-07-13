# sugar_rush_memphis - Design Spec

> Human-readable design narrative. Machine-readable execution contract: `spec_lock.md`. Executor re-reads `spec_lock.md` before every SVG page. On divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | sugar_rush_memphis |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 14 |
| **Design Style** | A) General Versatile + Memphis / Pop |
| **Target Audience** | 音乐节观众（18-35）+ 品牌赞助方 + 媒体 |
| **Use Case** | 虚构音乐节年度手册（翻阅 + 媒体投放） |
| **Created Date** | 2026-05-17 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px / 上下 50px |
| **Content Area** | 1160×620（安全区） |

---

## III. Visual Theme

### Theme Style

- **Style**: A) General Versatile + Memphis / Pop
- **Theme**: Light theme（奶油底）
- **Tone**: 张扬、糖果感、80s 回潮、撞色狂欢

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFF8EE` | 奶油白页面底（55%） |
| **Secondary bg** | `#FFE9C7` | 浅奶油卡片底（特定卡片） |
| **Primary** | `#FF3DA5` | 泡泡糖粉 — 标题 / 重音色块 |
| **Accent** | `#00B8D9` | 电光蓝 — 次级强调 / 链接 |
| **Secondary accent** | `#FFD93D` | 鲜黄 — 高亮 / 数字 |
| **Tertiary accent** | `#00C896` | 薄荷绿 — 章节分色 |
| **Quaternary accent** | `#FF6B4A` | 珊瑚红 — 装饰碎片 |
| **Body text** | `#1A1A2E` | 墨黑 — 正文 |
| **Secondary text** | `#5C5C7A` | 灰紫 — 注释 |
| **Border/divider** | `#1A1A2E` | 墨黑粗描边（2-4px） |
| **Success** | `#00C896` | 复用薄荷绿 |
| **Warning** | `#FF6B4A` | 复用珊瑚红 |

> 撞色合计占比 ≤ 40%；每页正面只用 2-3 个撞色，不全堆。文字对比度 #1A1A2E on #FFF8EE = 15.5:1（远超 4.5:1）。

### AI Image Strategy

- **Image Rendering**: `flat`
- **Image Palette**: `vivid-launch`

> 锁全 deck — 每张 AI 图共享 flat 渲染 + vivid-launch 配色行为。Image_Generator 自动注入。

### Gradient Scheme

```xml
<!-- 章节扉页 scrim 渐变 -->
<linearGradient id="heroScrim" x1="0%" y1="100%" x2="0%" y2="0%">
  <stop offset="0%" stop-color="#1A1A2E" stop-opacity="0.55"/>
  <stop offset="60%" stop-color="#1A1A2E" stop-opacity="0"/>
</linearGradient>

<!-- 收尾页融入背景 -->
<linearGradient id="fadeToBg" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#FFF8EE" stop-opacity="0"/>
  <stop offset="100%" stop-color="#FFF8EE" stop-opacity="0.95"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Display × Neutral 强对比 — 标题用 Impact 制造海报张力，正文用 Arial / 微软雅黑保证可读。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Impact, "Arial Black"` | `sans-serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Impact` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Impact, "Arial Black", "Microsoft YaHei", sans-serif`
- Body: `Arial, "Microsoft YaHei", "PingFang SC", sans-serif`
- Emphasis: `Impact, "Microsoft YaHei", sans-serif`
- Code: `Consolas, "Courier New", monospace`

> Title/Emphasis Latin-led（Impact 优先）→ 英文承担海报张力；CJK 回落到 Microsoft YaHei。Body 改为 Arial-led 以保证 Latin 字符现代感，正文中文仍走 YaHei。

### Font Size Hierarchy

**Baseline**: Body font size = **20px**（中等密度，海报感）

| Purpose | Ratio to body | Px | Weight |
| ------- | ------------- | ---- | ------ |
| Cover hero headline | 4-5x | 80-100px | Black |
| Chapter opener | 2.8-3.6x | 56-72px | Black |
| Page title | 1.8-2.2x | 36-44px | Black |
| Hero number | 4-6x | 80-120px | Black |
| Subtitle | 1.4-1.6x | 28-32px | Bold |
| **Body content** | **1x** | **20px** | Regular |
| Annotation / caption | 0.7-0.85x | 14-17px | Regular |
| Page number / footnote | 0.55-0.65x | 11-13px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 顶部 50-80px — 章节标识 / 页码 / 装饰碎片
- **Content area**: 中部 540-600px — 主要内容
- **Footer area**: 底部 30-50px — 页脚 / Logo / 页码

### Layout Pattern Library

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | 封面、章节扉页、收尾 |
| **Asymmetric split (3:7 / 2:8)** | 内容主页（左标题 + 右图卡） |
| **Top-bottom split** | 票务页（上对比 + 下赞助） |
| **Three/four column cards** | KPI / 风格阵营 / 票档 |
| **Matrix grid (2×2)** | 风格阵营四分类 |
| **Center-radiating** | 5 舞台 hub_spoke |
| **Full-bleed + floating text** | 6 个章节扉页与封面 |
| **Figure-text overlap** | 头牌艺人页（粗描边块叠在人像上） |
| **Z-pattern / waterfall** | 时间轴日程（蛇形） |

### Memphis 装饰碎片（每页可叠加 1-3 个）

- 圆点阵 (3-5 个 #FF3DA5 圆点排成不规则排列)
- 波浪线 (3-5 个起伏的 #00B8D9 波浪)
- Z 字闪电 (#FFD93D / #FF6B4A 几何 Z 字)
- 三角块 (45° 旋转的实心三角)
- 棋盘条纹 (黑白小方块组成的边角条带)
- 粗黑描边 (2-4px 墨黑边框，所有块都加)

### Spacing Specification

**Universal**:

| Element | Range | Project Value |
| ------- | ----- | ------------- |
| Safe margin from canvas edge | 40-60px | 60px |
| Content block gap | 24-40px | 32px |
| Icon-text gap | 8-16px | 12px |

**Card-based**:

| Element | Range | Project Value |
| ------- | ----- | ------------- |
| Card gap | 20-32px | 24px |
| Card padding | 20-32px | 24px |
| Card border radius | 8-16px | 12px |
| Card border (Memphis 必备) | 2-4px | 3px solid #1A1A2E |

**Non-card / breathing pages**:

- Line-height: 1.4-1.5× body font size
- Full-bleed text placement: 留焦点区域，文字侧加 scrim

---

## VI. Icon Usage Specification

### Source

- **Library**: `chunk-filled`（粗实、几何、与孟菲斯硬边性格契合）
- **Usage**: SVG `<use data-icon="chunk-filled/<name>" .../>` 占位符

### Recommended Icon List

| Purpose | Icon | Page |
| ------- | ---- | ---- |
| 天数 | `chunk-filled/calendar` | P03 |
| 舞台 / 音乐 | `chunk-filled/music` | P03, P09 |
| 艺人 | `chunk-filled/microphone` | P03, P05 |
| 观众 | `chunk-filled/users` | P03 |
| 时间 | `chunk-filled/clock` | P10 |
| 闪电 / 能量 | `chunk-filled/bolt` | P04, P07 |
| 心 / 爱 | `chunk-filled/heart` | P04, P14 |
| 星 / 头牌 | `chunk-filled/star` | P06 |
| 场地 / 定位 | `chunk-filled/map-pin` | P09 |
| 太阳 / 夏日 | `chunk-filled/sun` | P02, P14 |
| 闪烁装饰 | `chunk-filled/sparkles` | 全 deck 装饰 |
| 耳机 / 电子 | `chunk-filled/headphones` | P07 |
| 周边市集 | `chunk-filled/shopping-bag` | P12 |
| 游戏 / 互动 | `chunk-filled/game-controller` | P12 |
| 票务 | `chunk-filled/ticket` | P13 |
| 赞助 / 礼物 | `chunk-filled/gift` | P13 |
| 流程箭头 | `chunk-filled/arrow-right` | P10 |

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P03 | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, dashboard headline, quarterly recap, res..." | 4 个核心数字：7天 / 5舞台 / 80组艺人 / 50000观众 |
| P04 | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST (Political/Economic..." | 三大理念：FREE / FUN / FOREVER YOUNG |
| P06 | icon_grid | `templates/charts/icon_grid.svg` | "Pick for 4-9 parallel features/capabilities/services as icon cards — feature grid, service lineup, benefits matrix, brand values, product hi..." | 4 组头牌艺人卡片 |
| P07 | quadrant_text_bullets | `templates/charts/quadrant_text_bullets.svg` | "Pick for any 2×2 framework where each quadrant holds a titled bullet list — SWOT (Strengths/Weaknesses/Opportunities/Threats, internal-exter..." | 4 风格阵营：摇滚 / 电子 / 民谣 / 嘻哈 |
| P09 | hub_spoke | `templates/charts/hub_spoke.svg` | "Pick for 1 core capability + 4-8 surrounding capabilities (platform/ecosystem); each spoke = title or title + 1-2 line description. Skip if..." | 中央主舞台 + 4 个分舞台辐射 |
| P10 | timeline | `templates/charts/timeline.svg` | "Pick for 3-8 milestone events on a horizontal time axis (no duration). Skip for tasks with start/end ranges (use gantt_chart) or vertical la..." | 7 天音乐节日程 |
| P12 | comparison_columns | `templates/charts/comparison_columns.svg` | "Pick for 2-4 pricing/service tier cards in side-by-side columns (marketing layout). Skip for dense feature comparison (use comparison_table)..." | 周边市集 vs 互动装置（两栏对照） |
| P13 | comparison_columns | `templates/charts/comparison_columns.svg` | "Pick for 2-4 pricing/service tier cards in side-by-side columns (marketing layout). Skip for dense feature comparison (use comparison_table)..." | 票务 EARLY / REGULAR / VIP 三档 |

**Runners-up considered**:

- `team_roster` | rejected for P06: 项目用插画化头像而非真人员工照，且需要嵌入"专辑代表作"等非身份字段；icon_grid 更自由
- `numbered_steps` | rejected for P10: 7 天日程是固定日期里程碑而非"如何做"步骤，timeline 才匹配时间轴语义
- `comparison_table` | rejected for P13: 票档只有 4-5 行属性，列式营销卡片更孟菲斯波普；表格密度过高反而压住视觉

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_bg.png | 1280×720 | 1.78 | P01 封面主视觉 | Illustration | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 夏日狂欢主视觉：糖果色霓虹灯牌「SUGAR RUSH」横向居中悬浮于热带丛林夜空，左下角圆点群+右上角波浪闪电装饰碎片，左侧留出大面积冷色暗区供副标题叠加，鸟瞰人群剪影沿底部成弧线 | embedded | hero_page |
| ch1_what.png | 1280×720 | 1.78 | P02 章节1 WHAT 扉页 | Illustration | #12 faded image as backdrop with oversized overlay text + #27 linear gradient mask | ai | Pending | 夏日沙滩派对俯视全景：撞色伞群+人群涂鸦风轮廓，画面中央保留 50% 留白让标题压上去，右下角棋盘条纹边角装饰 | none | hero_page |
| ch2_who.png | 1280×720 | 1.78 | P05 章节2 WHO 扉页 | Illustration | #1 full-bleed background with floating title + #38 background image + annotation cards with bezier leader lines | ai | Pending | 五位风格化音乐人剪影并排站在霓虹聚光灯下的舞台，手持麦克风/吉他/合成器，背景为粉/蓝/黄撞色光柱，画面留有空气感不拥挤 | none | hero_page |
| headliners.png | 1200×500 | 2.40 | P06 头牌艺人四联画 | Illustration | #26 triptych baked into a single wide image + #21 rounded rectangle crop | ai | Pending | 四联横幅插画：4 位风格化虚构音乐人正面半身像并排，左到右为电吉他女主唱（粉发）/ 电子合成器男 DJ（金色墨镜）/ 民谣女吉他手（薄荷绿衬衫）/ 嘻哈男 rapper（鲜黄连帽衫），每位人物背后是与其音乐风格匹配的撞色块背景，统一粗黑描边 | none | local |
| ch3_where.png | 1280×720 | 1.78 | P08 章节3 WHERE & WHEN 扉页 | Illustration | #41 background image + measurement lines and module tags (engineering overlay) + #29 two-stop scrim | ai | Pending | 鸟瞰视角的虚构音乐节场地全景：椰林环抱、中央大舞台与四个卫星舞台呈放射状分布、彩色帐篷与霓虹路灯点缀、人流以柔和粉色矢量化暗示，画面留出顶部三分之一空区供标题 | none | hero_page |
| ch4_vibes.png | 1280×720 | 1.78 | P11 章节4 VIBES 扉页 | Illustration | #1 full-bleed background with floating title + #28 radial gradient vignette | ai | Pending | 夜场氛围全景：荧光手环与彩色烟雾在人群上方腾起，远处舞台 LED 屏幕显示巨型抽象波浪图案，前景设置一个跳跃中的人物剪影做视觉焦点，左上保留暗区供标题 | none | hero_page |
| market.png | 600×400 | 1.50 | P12 周边市集场景 | Illustration | #19 image floating in whitespace with thin frame and caption + #21 rounded rectangle crop | ai | Pending | 户外周边市集摊位：撞色雨篷下陈列着印有 SUGAR RUSH 字样的 T 恤、帆布袋、贴纸、霓虹光剑，摊主向顾客递商品的瞬间，画面充满波普海报感 | none | local |
| installation.png | 600×400 | 1.50 | P12 互动装置场景 | Illustration | #19 image floating in whitespace with thin frame and caption + #21 rounded rectangle crop | ai | Pending | 沉浸式互动艺术装置：巨型充气几何雕塑（粉色圆球+蓝色三角+黄色波浪）矗立在草坪，两三个观众在装置间穿梭、自拍、跃起，蓝天白云作背景 | none | local |
| closing.png | 1280×720 | 1.78 | P14 收尾页 | Illustration | #1 full-bleed background with floating title + #66 image fading into the solid background | ai | Pending | 夕阳下空荡的舞台后景：散落的彩色纸屑、被风扬起的气球、远处地平线的紫粉色霞光，画面底部 1/3 用渐变融入奶油色背景，整体悠长怀念感 | none | hero_page |

> 9 张 AI 图全 deck 共享 `flat × vivid-launch`（h.5 锁定）。其中 6 张 hero_page（P01/P02/P05/P08/P11/P14）+ 3 张 local（P06 / P12 ×2）。#38 image-as-canvas + native overlay 覆盖在 P05；#41 用于 P08，满足"≥4 image-bearing pages 至少 1 个 #38–#46"的硬性要求。

---

## IX. Content Outline

### Part 1: WHAT — 是什么

#### Slide 01 - Cover

- **Layout**: Full-bleed + floating title（hero_page）
- **Title**: `SUGAR RUSH`
- **Subtitle**: 2026 夏日音乐节 · 年度手册
- **Info**: 7.18 – 7.24 · 椰岛大草原 · 让甜炸的夏天到来

#### Slide 02 - Chapter 1: WHAT IS SUGAR RUSH

- **Layout**: 章节扉页 — Faded image backdrop + 巨字标题
- **Title**: `WHAT.`
- **Subtitle**: 当全世界都在变热，我们决定，让它变甜。

#### Slide 03 - 关键数字

- **Layout**: Four-column cards（2×2 or 1×4）
- **Title**: BY THE NUMBERS
- **Visualization**: kpi_cards
- **Content**:
  - `7` DAYS · 7 天连续狂欢（icon: calendar）
  - `5` STAGES · 5 个主题舞台（icon: music）
  - `80` ARTISTS · 80 组艺人阵容（icon: microphone）
  - `50K` FANS · 50000 名观众预期（icon: users）

#### Slide 04 - 三大理念

- **Layout**: Three-column vertical pillars
- **Title**: WHAT WE STAND FOR
- **Visualization**: vertical_pillars
- **Content**:
  - **FREE**（icon: bolt）— 不设鄙视链，所有风格都是好风格
  - **FUN**（icon: sparkles）— 玩到极致，留下最甜回忆
  - **FOREVER YOUNG**（icon: heart）— 18 岁还是 80 岁，舞池里没有年纪

### Part 2: WHO — 谁来玩

#### Slide 05 - Chapter 2: WHO

- **Layout**: Full-bleed + 标题压音乐人剪影 + annotation cards
- **Title**: `WHO.`
- **Subtitle**: 80 组艺人，5 个风格阵营，1 张你忘不掉的脸。

#### Slide 06 - 头牌艺人

- **Layout**: 2×2 grid，4 张头像 + 名字 + 风格 + 代表作
- **Title**: THE HEADLINERS
- **Visualization**: icon_grid（每格 = 头像 + 文字）
- **Content**:
  - **CHERRY BOMB**（粉发女主唱 · 摇滚 · 代表作 "Pink Static"）
  - **NEON CLOUD**（金色墨镜 DJ · 电子 · 代表作 "3AM Mirror"）
  - **MINT FOLK**（薄荷绿衬衫 · 民谣 · 代表作 "Slow Lemon"）
  - **YELLOW HUSTLE**（鲜黄连帽 · 嘻哈 · 代表作 "Sugar High"）

#### Slide 07 - 四大风格阵营

- **Layout**: 2×2 quadrant matrix
- **Title**: FOUR FLAVORS, ONE FESTIVAL
- **Visualization**: quadrant_text_bullets
- **Content**:
  - 摇滚（icon: bolt）— 噪音、燃、释放 · 25 组艺人
  - 电子（icon: headphones）— 律动、深夜、迷幻 · 30 组艺人
  - 民谣（icon: heart）— 故事、慢、温度 · 15 组艺人
  - 嘻哈（icon: music）— 街头、节拍、态度 · 10 组艺人

### Part 3: WHERE & WHEN — 何时何地

#### Slide 08 - Chapter 3: WHERE & WHEN

- **Layout**: Full-bleed 鸟瞰图 + 模块标签 + scrim
- **Title**: `WHERE.`
- **Subtitle**: 椰岛大草原 · 一座为夏天造的城市。

#### Slide 09 - 5 个主题舞台

- **Layout**: Hub-spoke center-radiating
- **Title**: 5 STAGES, ONE WORLD
- **Visualization**: hub_spoke
- **Content**:
  - **中央 · SUGAR DOME**（主舞台，最大容量 30000）
  - **粉 · CHERRY STAGE**（摇滚，5000）
  - **蓝 · NEON GRID**（电子，5000）
  - **绿 · MINT GROVE**（民谣，3000）
  - **黄 · YELLOW BLOCK**（嘻哈，7000）

#### Slide 10 - 7 天日程

- **Layout**: Horizontal timeline
- **Title**: SEVEN DAYS OF SUGAR
- **Visualization**: timeline
- **Content**:
  - Day 1 (7.18) · OPENING · 开幕之夜
  - Day 2 (7.19) · ROCK DAY
  - Day 3 (7.20) · ELECTRO NIGHT
  - Day 4 (7.21) · FOLK AFTERNOON
  - Day 5 (7.22) · HIPHOP MIDNIGHT
  - Day 6 (7.23) · CROSSOVER · 跨界之夜
  - Day 7 (7.24) · CLOSING · 闭幕大狂欢

### Part 4: VIBES — 玩什么

#### Slide 11 - Chapter 4: VIBES

- **Layout**: Full-bleed + radial vignette
- **Title**: `VIBES.`
- **Subtitle**: 音乐之外，还有十种甜的方式。

#### Slide 12 - 周边市集 + 互动装置

- **Layout**: Two-column comparison
- **Title**: BEYOND THE MUSIC
- **Visualization**: comparison_columns（左：MARKET / 右：ART INSTALL）
- **Content**:
  - **左 · MARKET**（icon: shopping-bag）— 50+ 摊位、限定周边、手作市集、本地小吃
  - **右 · ART INSTALL**（icon: game-controller）— 10 件巨型装置、AR 互动、彩绘工坊、夜光涂鸦墙

#### Slide 13 - 票务 + 赞助

- **Layout**: Top three-column tickets + bottom sponsor strip
- **Title**: GET YOUR TICKET
- **Visualization**: comparison_columns
- **Content**:
  - **EARLY BIRD** · ¥499（限 5000 张 · 已售罄字样）
  - **REGULAR** · ¥799（含 1 杯指定饮品）
  - **VIP 7-DAY PASS** · ¥1999（含全程通票 + VIP 专区 + 会面机会）
  - 底部 sponsor 行：5-7 个虚构赞助 logo（占位文字 + icon 装饰）

#### Slide 14 - Closing

- **Layout**: Full-bleed + fade to background
- **Title**: `SEE YOU IN SUMMER.`
- **Subtitle**: SUGAR RUSH 2026 · 7.18 – 7.24
- **Info**: Get tickets at sugarrush.fest

---

## X. Speaker Notes Requirements

- **Total duration**: ~15 分钟（演示性朗读 · 1 分钟/页）
- **Notes style**: 对话式 + 略带营销感 — 像一个 host 在介绍音乐节
- **Presentation purpose**: 激发兴趣 + 传达品牌调性 + 引导购票
- **File naming**: 对齐 SVG `01_cover.svg → notes/01_cover.md`

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements（#FFF8EE 奶油底）
3. Text wrapping uses `<tspan>`（`<foreignObject>` FORBIDDEN）
4. Transparency defaults to `fill-opacity` / `stroke-opacity`; `rgba()` remains converter-compatible
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. 文字字符直接写 Unicode（`—` `→` `·` 等），HTML 命名实体 FORBIDDEN；`&` 在文字里必须 `&amp;`
7. `clipPath` 只用于 `<image>`（圆 / 圆角矩形 / 多边形），不用于 shape / group / text
8. Memphis 粗描边：所有几何块加 `stroke="#1A1A2E" stroke-width="2-4"`

### PPT Compatibility Rules:

- Prefer opacity on each child; `<g opacity="...">` remains converter-compatible with an approximate-fidelity warning
- Image 透明走 overlay 蒙层
- 仅 inline 样式；`@font-face` FORBIDDEN
- Memphis 装饰碎片用基础 SVG 图元（circle / rect / path / polygon），不用 `<pattern>`+`<use>`
