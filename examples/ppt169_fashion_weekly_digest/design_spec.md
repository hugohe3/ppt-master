# 美学周鉴 · 解锁潮流序章 - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 美学周鉴 · 解锁潮流序章 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 16 |
| **Design Style** | General Versatile — Magazine Editorial |
| **Target Audience** | 时尚行业从业者、奢侈品爱好者、品牌营销人员 |
| **Use Case** | 时尚资讯分享、品牌动态播报、社交传播 |
| **Created Date** | 2026-04-26 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 50px, 上下 40px |
| **Content Area** | 1180×640 |

---

## III. Visual Theme

### Theme Style

- **Style**: Magazine Editorial — 高端时尚杂志编辑风格
- **Theme**: Dark theme — 深色背景突出品牌视觉
- **Tone**: 奢华、精致、现代、杂志感

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0A0A0A` | 深黑底色，奢侈品杂志调性 |
| **Secondary bg** | `#1A1A1A` | 卡片/区块底色 |
| **Primary** | `#C9A96E` | 金色，奢侈品标志色，标题装饰、图标 |
| **Accent** | `#E8D5B5` | 浅金/米白，副标题、关键信息高亮 |
| **Secondary accent** | `#8B7355` | 暗金/古铜，渐变过渡、辅助装饰 |
| **Body text** | `#F5F0EB` | 暖白色正文 |
| **Secondary text** | `#9E9690` | 灰棕色注释文字 |
| **Border/divider** | `#2A2520` | 深棕色边框、分割线 |

### Gradient Scheme

```xml
<!-- Title accent gradient -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#C9A96E"/>
  <stop offset="100%" stop-color="#E8D5B5"/>
</linearGradient>

<!-- Decorative radial glow -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#C9A96E" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#C9A96E" stop-opacity="0"/>
</radialGradient>

<!-- Image overlay gradient (bottom fade) -->
<linearGradient id="imageOverlay" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#0A0A0A" stop-opacity="0"/>
  <stop offset="60%" stop-color="#0A0A0A" stop-opacity="0.3"/>
  <stop offset="100%" stop-color="#0A0A0A" stop-opacity="0.85"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Editorial display — 标题衬线体营造杂志质感，正文无衬线体保证可读性

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `SimSun` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `SimSun` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks** (CSS `font-family` strings):

- Title: `Georgia, SimSun, serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `Georgia, SimSun, serif`
- Code: `Consolas, "Courier New", monospace`

> **Stack ordering rationale**: Title stack is Latin-led (`Georgia` first) because brand names dominate headline text — Georgia's elegant serifs display English brand names beautifully, while CJK characters fall through to SimSun. Body stack is CJK-led because the main content is in Chinese.

### Font Size Hierarchy

**Baseline**: Body font size = 18px (dense — accommodating 16 brand stories across 16 pages)

| Purpose | Ratio to body | Size | Weight |
| ------- | ------------- | ---- | ------ |
| Cover title | 3.3x | 60px | Bold |
| Brand name heading | 2x | 36px | Bold |
| Page title | 1.7x | 30px | Bold |
| Subtitle | 1.3x | 24px | SemiBold |
| **Body content** | **1x** | **18px** | Regular |
| Brand tag / label | 0.8x | 14px | SemiBold |
| Annotation / caption | 0.7x | 13px | Regular |
| Page number / footnote | 0.6x | 11px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 40px — 品牌名/栏目标识区，金色细线分割
- **Content area**: 640px — 主内容区，根据品牌数量灵活分配
- **Footer area**: 40px — 页码、来源标注

### Layout Pattern Library

本项目以杂志编辑风格为核心，采用多样化布局避免 AI 生成感：

| Pattern | Usage |
| ------- | ----- |
| **Full-bleed + floating text** | 封面页，品牌图片铺满画布，标题浮于图上 |
| **Asymmetric split (3:7 / 4:6)** | 单品牌专题页，图片占主导，文字简洁 |
| **Figure-text overlap** | 品牌标题叠于图片边缘，杂志排版感 |
| **Two-column magazine** | 双品牌合并页，左右各一品牌 |
| **Negative-space-driven** | 呼吸页，留白突出单一品牌视觉 |
| **Top-bottom split** | 宽幅品牌图 + 下方文案 |

### Spacing Specification

**Universal**:

| Element | Value |
| ------- | ----- |
| Safe margin | 50px |
| Content block gap | 30px |
| Icon-text gap | 10px |

**Card-based layouts** (where applicable):

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Card padding | 24px |
| Card border radius | 12px |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `phosphor-duotone` — 双色调风格，层次丰富，时尚现代
- **Brand icons**: `simple-icons` — 品牌 logo 标识（如需展示品牌标志）
- **Usage method**: SVG placeholder `<use data-icon="library/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 时尚/潮流 | `phosphor-duotone/dress` | 封面、多页 |
| 高级珠宝 | `phosphor-duotone/diamond` | P07 |
| 腕表 | `phosphor-duotone/watch` | P04 |
| 家居/设计 | `phosphor-duotone/house` | P02, P05 |
| 展览/艺术 | `phosphor-duotone/palette` | P06, P08 |
| 香氛/美妆 | `phosphor-duotone/flower` | P11 |
| 手袋/配饰 | `phosphor-duotone/handbag` | P10 |
| 活动/明星 | `phosphor-duotone/star` | P12 |
| 联名/合作 | `phosphor-duotone/handshake` | P13 |
| 剪刀/裁缝 | `phosphor-duotone/scissors` | P09 |
| 商店/零售 | `phosphor-duotone/storefront` | P07 |
| 相机/摄影 | `phosphor-duotone/camera` | P08 |
| 皇冠/奢华 | `phosphor-duotone/crown` | 封面 |
| 闪耀/亮点 | `phosphor-duotone/sparkle` | 多页 |
| 标签/品牌 | `phosphor-duotone/tag` | 多页 |
| 全球/国际 | `phosphor-duotone/globe` | P07 |

---

## VII. Visualization Reference List

```
Catalog read: 40+ templates / 8 categories
Runners-up considered: fewer than 3 viz pages — this is a magazine-style news digest, not a data-driven deck
```

本项目为时尚资讯汇编，内容以品牌叙事和图片展示为主，不包含数据可视化需求。所有页面采用图文编辑排版，无需引用图表模板。

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Intent | Purpose | Type | Status |
| -------- | ---------- | ----- | ------ | ------- | ---- | ------ |
| cover_hermes.jpg | 1080x997 | 1.08 | Hero / full-bleed | 封面主视觉 | Photography | Existing |
| hermes_home.jpg | 1080x772 | 1.40 | Side-by-side | Hermès 家居世界 | Photography | Existing |
| chanel_coco.jpg | 1080x608 | 1.78 | Hero / full-bleed | CHANEL COCO BEACH | Photography | Existing |
| dior_fashion.jpg | 1080x1080 | 1.00 | Side-by-side | Dior 时装 | Photography | Existing |
| dior_watch1.jpg | 1080x1080 | 1.00 | Side-by-side | Dior Chiffre Rouge 腕表 | Photography | Existing |
| lv_objets.jpg | 1080x608 | 1.78 | Hero / full-bleed | LV Objets Nomades | Photography | Existing |
| gucci_memoria1.jpg | 1080x810 | 1.33 | Side-by-side | Gucci Memoria 展览 | Photography | Existing |
| gucci_memoria2.jpg | 1080x810 | 1.33 | Accent | Gucci 展览补充 | Photography | Existing |
| vhernier_jewelry.jpg | 1080x720 | 1.50 | Side-by-side | Vhernier 珠宝 | Photography | Existing |
| celine_summer.jpg | 1080x1350 | 0.80 | Side-by-side | CELINE 夏季 | Photography | Existing |
| bv_arts.jpg | 1080x1350 | 0.80 | Side-by-side | BV 艺术摄影 | Photography | Existing |
| mcqueen_exhibition.jpg | 1080x721 | 1.50 | Side-by-side | McQueen 表象之下 | Photography | Existing |
| maxmara_show.jpg | 1080x634 | 1.70 | Hero / full-bleed | Max Mara 首秀 | Photography | Existing |
| chloe_tomato.jpg | 1080x1440 | 0.75 | Side-by-side | Chloé Tomato 座椅 | Photography | Existing |
| tadfab_bag.jpg | 1080x1440 | 0.75 | Side-by-side | TAD FAB 包袋 | Photography | Existing |
| apedemod_fold.jpg | 1080x1619 | 0.67 | Side-by-side | Apede Mod 折纸 | Photography | Existing |
| boss_fragrance.jpg | 1080x1440 | 0.75 | Side-by-side | BOSS 香氛 | Photography | Existing |
| fresh_event.jpg | 1080x721 | 1.50 | Side-by-side | fresh 发布会 | Photography | Existing |
| jorya_popup.jpg | 1080x810 | 1.33 | Side-by-side | JORYA 快闪 | Photography | Existing |
| arket_gohar.jpg | 1080x720 | 1.50 | Side-by-side | ARKET 联名 | Photography | Existing |
| stevemadden_lexie.jpg | 1080x721 | 1.50 | Side-by-side | Steve Madden 代言人 | Photography | Existing |
| crocs_molly.jpg | 1080x608 | 1.78 | Side-by-side | Crocs × MOLLY | Photography | Existing |

---

## IX. Content Outline

### Part 1: 开篇

#### Slide 01 — 封面

- **Layout**: Full-bleed + floating text — cover_hermes.jpg 铺满画布，标题浮于暗色渐变层上
- **Title**: NEWS Café | 美学周鉴
- **Subtitle**: 解锁潮流序章
- **Info**: 本周时尚热点 · 2026年4月

### Part 2: 顶级奢侈品牌

#### Slide 02 — Hermès 家居世界

- **Layout**: Asymmetric split (4:6) — 左侧文字，右侧 hermes_home.jpg
- **Title**: Hermès 家居世界
- **Content**:
  - 米兰设计周全新家居系列发布
  - 三十根矩形立柱构筑沉浸式布景
  - 金属锻打、皮革镶嵌、织物雕琢，材质对话与物件叙事
  - 延续匠心工艺与隽永美学

#### Slide 03 — CHANEL COCO BEACH

- **Layout**: Hero / full-bleed — chanel_coco.jpg 作为背景，文字浮于底部渐变层
- **Title**: CHANEL COCO BEACH 2026
- **Content**:
  - 上海市中心限时精品店启幕
  - 面朝花园的度假别墅概念
  - 田园风光与黑色沙滩灵感
  - Matthieu Blazy 创作的首个 COCO BEACH 系列

#### Slide 04 — Dior：时装与时计

- **Layout**: Two-column — 左 dior_fashion.jpg，右 dior_watch1.jpg + 文案
- **Title**: Dior 双面魅力
- **Content**:
  - 左栏：Sabrina Carpenter 身着 Jonathan Anderson 设计礼服亮相 Coachella
  - 右栏：Chiffre Rouge 腕表系列焕新，三款限量臻品
  - 红色秒针致敬迪奥心中的生命之色
  - 迪奥先生钟爱数字"8"化作护身符

#### Slide 05 — Louis Vuitton Objets Nomades

- **Layout**: Hero / full-bleed — lv_objets.jpg 背景 + 浮动文字块
- **Title**: Louis Vuitton Objets Nomades
- **Content**:
  - 米兰设计周全新旅行家居系列
  - 致敬 Art Deco 与 Pierre Legrain 大师
  - 坎帕纳工作室、Raw Edges、Franck Genser 当代设计师新作
  - Collar 休闲椅、Aqua 餐桌等新品

#### Slide 06 — Gucci Memoria

- **Layout**: Asymmetric split (3:7) — 右 gucci_memoria1.jpg 主导 + 左文案，gucci_memoria2.jpg 作小图点缀
- **Title**: Gucci Memoria
- **Content**:
  - 米兰圣辛普利齐亚诺回廊沉浸式展览
  - Demna 策划，追溯品牌 105 年历程
  - 十二幅挂毯凝练品牌关键发展节点
  - Flora 花卉主题花园装置及专享预售

### Part 3: 高级珠宝与时装

#### Slide 07 — Vhernier × CELINE

- **Layout**: Two-column magazine — 左 Vhernier (vhernier_jewelry.jpg)，右 CELINE (celine_summer.jpg)
- **Title**: 珠宝新境 · 法式灵韵
- **Content**:
  - 左栏：Vhernier 正式进驻中国内地，北京上海双店开幕，米兰纯粹设计
  - 右栏：Été CELINE 广告大片，海滨假日灵感，法式海岸随性魅力

#### Slide 08 — BV × McQueen：艺术的两种表达

- **Layout**: Two-column magazine — 左 BV (bv_arts.jpg)，右 McQueen (mcqueen_exhibition.jpg)
- **Title**: 艺术的两种表达
- **Content**:
  - 左栏：BV "for the Arts" 摄影集，Peter Fraser 镜头下的威尼斯，编织美学
  - 右栏：McQueen "表象之下" 上海沉浸式展览，Manta 手袋复刻 2010 经典

### Part 4: 设计与生活方式

#### Slide 09 — Max Mara × Chloé

- **Layout**: Two-column — 左 Max Mara (maxmara_show.jpg)，右 Chloé (chloe_tomato.jpg)
- **Title**: 传承新章
- **Content**:
  - 左栏：Max Mara 2027 早春系列上海首秀，"THE MAX!" 75 周年档案展
  - 右栏：Chloé × Poltronova Tomato 座椅限量复刻，1970 年意大利激进设计运动标志

#### Slide 10 — TAD FAB × Apede Mod

- **Layout**: Two-column — 左 TAD FAB (tadfab_bag.jpg)，右 Apede Mod (apedemod_fold.jpg)
- **Title**: 结构重塑
- **Content**:
  - 左栏：TAD FAB 全新系列，拉链设计语言，环绕拉链 Hobo 包，松弛精致格调
  - 右栏：Apede Mod 十周年 PF 2026 折纸系列，折叠结构设计进阶

### Part 5: 美妆与香氛

#### Slide 11 — BOSS × fresh

- **Layout**: Two-column — 左 BOSS (boss_fragrance.jpg)，右 fresh (fresh_event.jpg)
- **Title**: 感官新篇
- **Content**:
  - 左栏：BOSS 王者之心香氛，清新木质皮革调，双极香型，王天辰等出席
  - 右栏：fresh 馥蕾诗「酵」你去野新品，CORTIS 全员代言，茶饮文化灵感

### Part 6: 联名与跨界

#### Slide 12 — JORYA × ARKET

- **Layout**: Two-column — 左 JORYA (jorya_popup.jpg)，右 ARKET (arket_gohar.jpg)
- **Title**: 跨界新风
- **Content**:
  - 左栏：JORYA × YVMIN「公主日记」成都快闪，赵露思亮相，千金轻纱叠穿概念
  - 右栏：ARKET × Laila Gohar 米兰装置，十八世纪旋转木马改造，27 款联名单品

#### Slide 13 — Steve Madden × Crocs

- **Layout**: Two-column — 左 Steve Madden (stevemadden_lexie.jpg)，右 Crocs (crocs_molly.jpg)
- **Title**: 潮流共振
- **Content**:
  - 左栏：刘柏辛成为 Steve Madden 中国区代言人，「不赶潮流，踩点登场」
  - 右栏：Crocs × 泡泡玛特 MOLLY 20 周年联名，三款洞洞鞋，易梦玲助阵

### Part 7: 收尾

#### Slide 14 — 本周亮点回顾

- **Layout**: Matrix grid — 6 个品牌亮点卡片，每卡一行品牌名 + 一行关键词
- **Title**: 本周亮点一览
- **Content**:
  - Hermès 家居世界 | CHANEL COCO BEACH | Dior 双面魅力
  - LV Objets Nomades | Gucci Memoria | McQueen 表象之下
  - 六个精选亮点品牌的微型视觉回顾

#### Slide 15 — 品牌全景

- **Layout**: Three-row layout — 按品类分行展示所有品牌名
- **Title**: 本期品牌全景
- **Content**:
  - 顶奢：Hermès · CHANEL · Dior · Louis Vuitton · Gucci
  - 轻奢/设计师：Vhernier · CELINE · BV · McQueen · Max Mara · Chloé
  - 潮流/生活方式：TAD FAB · Apede Mod · BOSS · fresh · JORYA · ARKET · Steve Madden · Crocs

#### Slide 16 — 结尾

- **Layout**: Negative-space-driven — 极简结尾，品牌/栏目标识居中
- **Title**: NEWS Café
- **Subtitle**: 下期见 See You Next Week
- **Info**: 美学周鉴，解锁潮流序章

---

## X. Speaker Notes Requirements

- **File naming**: Match SVG names (e.g., `01_cover.md`)
- **Total duration**: 15-20 minutes（每页约 1 分钟）
- **Notes style**: Conversational — 资讯播报式，轻松专业
- **Presentation purpose**: Inform — 传递本周时尚行业资讯

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography & symbols as raw Unicode; HTML named entities FORBIDDEN. XML reserved chars use `&amp;` `&lt;` `&gt;` `&quot;` `&apos;`
8. `clipPath` conditionally allowed only on `<image>` elements
9. `<g opacity>` FORBIDDEN — set opacity on each child individually
10. Dark theme: all text must use light colors (contrast ratio >= 4.5:1 against #0A0A0A)
