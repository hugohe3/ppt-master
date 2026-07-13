# ppt169_indie_bookstore_zine_guide_20260517 - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | ppt169_indie_bookstore_zine_guide_20260517 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 18 |
| **Design Style** | A) General Versatile + Risograph zine 印刷工艺 / DIY 海报美学 |
| **Target Audience** | 对独立出版 / zine / 艺术书感兴趣的入门读者；可二次用于独立书店推广、设计教学、城市文化分享会 |
| **Use Case** | 线下分享会 / 咖啡馆放映 / 设计学院 onboarding / 文化媒体二创素材 |
| **Created Date** | 2026-05-17 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px / 上下 50px |
| **Content Area** | 1160×620 |

---

## III. Visual Theme

### Theme Style

- **Style**: Risograph zine —— 套色错位 + 半色调网点 + 限定调色 + zine 手作粗粝
- **Theme**: Light theme (暖米色纸底)
- **Tone**: 印刷工艺感、海报感、DIY 张力、复古独立出版气质

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background (paper)** | `#F5EFE0` | 暖米色仿牛皮纸 / 再生纸感页面底色 |
| **Secondary bg** | `#EAE2CC` | 卡片 / 节区微差异底色 |
| **Primary (Riso Federal Blue)** | `#1E4DBC` | 主色块、标题描边、关键图形 |
| **Accent (Riso Fluorescent Pink)** | `#FF5C8A` | 强对比色、套色错位的另一层、装饰 |
| **Secondary accent (Mustard)** | `#E8A02E` | 第三色 <5%，用于焦点强调 |
| **Body text** | `#1A1A1A` | 近黑（贴近 Riso 油墨的不纯黑） |
| **Secondary text** | `#5A5A5A` | 注解、页码、caption |
| **Tertiary text** | `#8C8275` | 极淡背景文字 |
| **Border/divider** | `#1A1A1A` | 主分隔线一律近黑（zine 印刷感） |

> **Riso 美学硬约束**：套色错位 1–3px、半色调网点纹理、相同色块叠加产生第三色错觉。SVG 上以多个偏移色块 + opacity + 网点 `<pattern>` 模拟。

### AI Image Strategy

- **Image Rendering**: `screen-print`
- **Image Palette**: `duotone`

> 用户预先锁定（绕过三候选呈现）。screen-print × duotone 在矩阵中为 ✓✓ 推荐组合。所有 ai 图都使用同一 rendering + palette，HEX 从上表实色值注入（Federal Blue + Fluorescent Pink + 偶用 Mustard）。

### Gradient Scheme

> Risograph zine 一般不用渐变（违反扁平套色逻辑）；只在极少数处用 stop-opacity 模拟纸纹晕染。

```xml
<!-- 纸面半色调晕染（轻微，0.05–0.12 opacity） -->
<radialGradient id="paperHalftone" cx="50%" cy="50%" r="60%">
  <stop offset="0%" stop-color="#F5EFE0" stop-opacity="0"/>
  <stop offset="100%" stop-color="#5A5A5A" stop-opacity="0.08"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Contrast 方案 —— zine punk DIY 张力，标题用 Impact 海报字体，body 用 YaHei，annotation 用等宽 Consolas 制造"打字机/复印机"感

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Impact, "Arial Black"` | `sans-serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `SimHei` | `Impact, "Arial Black"` | `sans-serif` |
| **Code (annotation)** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Impact, "Arial Black", "Microsoft YaHei", sans-serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `Impact, "Arial Black", SimHei, "Microsoft YaHei", sans-serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = **20px**（zine 信息密度适中，介于 dense 18 和 relaxed 24 之间）

| Purpose | Ratio to body | Example @ body=20 | Weight |
| ------- | ------------- | ----------------- | ------ |
| Cover title (Impact 大字) | 4-5x | 80-100px | Heavy |
| Chapter / section opener | 2.5-3x | 50-60px | Bold |
| Page title | 1.6-2x | 32-40px | Bold |
| Hero number / 大字强调 | 2.5-4x | 50-80px | Heavy |
| Subtitle | 1.2-1.4x | 24-28px | SemiBold |
| **Body content** | **1x** | **20px** | Regular |
| Annotation / caption | 0.7-0.85x | 14-17px | Regular |
| Page number / footnote | 0.55-0.65x | 11-13px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 60px 高（页码 + 节标识 + 装饰条）
- **Content area**: 600px 高（主信息区）
- **Footer area**: 40px 高（页码 + footer 装饰条）

### Layout Pattern Library

> **原则 —— 比例服从信息权重，不拘泥固定网格。** zine 美学鼓励打破均匀网格、有意"乱排"、保留留白与高密度的对位。

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | 封面 / 封底 / 大字 outro |
| **Asymmetric split (3:7 / 2:8)** | 章节图 + 大字标题 / 单 hero + 边栏 |
| **Top-bottom split** | banner 图 + 多列内容 |
| **Three/four column cards** | 四浪潮 / 城市并列 / 工具列举 |
| **Full-bleed + floating text** | hero_page 封面 / Jimbocho / 柏林 |
| **Figure-text overlap** | 大字与图边缘交叠（zine 经典手法） |
| **Negative-space-driven** | breathing 页 —— 单元素 + 大量留白 |
| **Z-pattern waterfall** | 步骤型页（八页折叠 / Risograph 流程） |

### Spacing Specification

**Universal**:

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 40-60px | **60px 左右 / 50px 上下** |
| Content block gap | 24-40px | **32px** |
| Icon-text gap | 8-16px | **12px** |

**Card-based layouts** (used on P12 表 / P08 内容类型 grid / P10 三城并列 / P13 双书展卡 / P14-P15 vertical_list):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Card gap | 20-32px | **24px** |
| Card padding | 20-32px | **24px** |
| Card border radius | 8-16px | **0px**（Risograph 美学 = 硬边、无圆角）|
| Three-column card width | 360-380px each | **360px** |

**Non-card containers** (breathing 页 / hero pages):

- Line-height: 1.5x body (= 30px @ body 20)
- Full-bleed text placement: 大字标题与图边缘交叠为常见手法
- 信息按权重排版，不回算"列宽"

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/chunk-filled/` (粗实心几何，与 Riso 色块面感最协调)
- **Library lock**: **chunk-filled**（全 deck 单一库；混用 forbidden）
- **Usage method**: SVG placeholder `<use data-icon="chunk-filled/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| zine / 杂志 / 书 | `chunk-filled/book` | P03, P14 |
| 翻开的书 | `chunk-filled/book-open` | P02 (TOC) |
| 多本书 / 书架 | `chunk-filled/books` | P09, P10, P11 |
| 报刊 | `chunk-filled/newspaper` | P04 |
| 便签 / 短文 | `chunk-filled/sticky-note` | P08 |
| 打印机 | `chunk-filled/printer` | P05, P06 |
| 复制 / 复印 | `chunk-filled/copy` | P06 |
| 油墨 / 笔刷 | `chunk-filled/brush` | P05 |
| 剪刀（折 zine 工具） | `chunk-filled/scissors` | P07 |
| 铅笔 / 内容创作 | `chunk-filled/pencil` | P08 |
| 钢笔 / 写作 | `chunk-filled/pen-nib` | P08 |
| 工具箱 | `chunk-filled/toolbox` | P07 |
| 地图 | `chunk-filled/map` | P12 |
| 地图针 / 定位 | `chunk-filled/map-pin` | P09, P10, P11, P12 |
| 地球 / 全球 | `chunk-filled/globe` | P09 |
| 日历 / 书展 | `chunk-filled/calendar` | P13 |
| 时钟 | `chunk-filled/clock` | P13 |
| 心 / 收藏 | `chunk-filled/heart` | P15 |
| 星 / 推荐 | `chunk-filled/star` | P12 |
| 旗帜 / 行动 | `chunk-filled/flag` | P16 |
| 箭头 right | `chunk-filled/arrow-right` | 多处 |
| 圆形箭头 | `chunk-filled/circle-arrow-right` | P02, P16 |
| 建筑 / 书店 | `chunk-filled/building` | P12 |
| 购物袋 / 买买 | `chunk-filled/shopping-bag` | P14 |
| 文件夹 / 收藏 | `chunk-filled/folders` | P15 |
| 网格 / 库 | `chunk-filled/grid` | P02 |
| 手 / 自制 | `chunk-filled/hand` | P07, P16 |
| 用户 / 社群 | `chunk-filled/users` | P04 (Riot grrrl) |

---

## VII. Visualization Reference List

> Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P02 | agenda_list | `templates/charts/agenda_list.svg` | "Pick for table of contents, meeting agendas, or presentation roadmap — numbered items + brief description + duration / owner per row. Skip for substantive content lists (use vertical_list) or single-page section dividers (use a cover layout)." | 18 页 deck 的目录（5 节 + 简述 + 页码区间） |
| P04 | timeline | `templates/charts/timeline.svg` | "Pick for 3-8 milestone events on a horizontal time axis (no duration). Skip for tasks with start/end ranges (use gantt_chart) or vertical layout (use roadmap_vertical)." | zine 简史四浪潮（业余出版 1920s / 科幻 1930s / 朋克 1976 / Riot grrrl 1991 / 当代 2010s）= 5 milestones |
| P05 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | Risograph 4 大视觉特征：限定调色板 / 套色错位 / 网点纹理 / 油墨气味 |
| P06 | numbered_steps | `templates/charts/numbered_steps.svg` | "Pick for 3-6 horizontal sequential steps with numeric emphasis — how-it-works section, getting-started guide, methodology overview, implementation phases. Skip if steps need connector arrows (use process_flow) or named output artifacts (use pipeline_with_stages)." | Risograph 工作流 5 步：数字图像 → 烧蚀母版 → 包裹墨筒 → 滚压油墨 → 多次过纸 |
| P07 | numbered_steps | `templates/charts/numbered_steps.svg` | "Pick for 3-6 horizontal sequential steps with numeric emphasis — how-it-works section, getting-started guide, methodology overview, implementation phases. Skip if steps need connector arrows (use process_flow) or named output artifacts (use pipeline_with_stages)." | 八页折叠法 4 步：折叠 → 关键剪口 → 组装 → 填内容 |
| P08 | icon_grid | `templates/charts/icon_grid.svg` | "Pick for 4-9 parallel features/capabilities/services as icon cards — feature grid, service lineup, benefits matrix, brand values, product highlights. Skip for sequential ordering (use numbered_steps) or hierarchical layers (use pyramid_chart)." | zine 6 大内容类型：草图 / 诗 + 宣言 / 食谱插图 / 私人写作 / 拼贴 / 漫画 |
| P10 | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST (Political/Economic/Social/Technological), four-pillar strategy overview, side-by-side independent categories. Skip for 2×2 quadrant (use quadrant_text_bullets), pricing tiers (use comparison_columns), or 2×2 parallel aspects (use labeled_card)." | 三城三店并列：Shakespeare and Company（巴黎）/ Daunt + Word on the Water（伦敦）/ Strand + Yu and Me（纽约） |
| P12 | basic_table | `templates/charts/basic_table.svg` | "Pick for plain tabular text/number grid, 3-8 columns. Skip if cells need visual bars (use consulting_table) or qualitative scores (use harvey_balls_table)." | 中国大陆 15 家 zine 倾向独立书店地图（书店 / 城市 / 特色 / zine 倾向 4 列） |
| P13 | labeled_card | `templates/charts/labeled_card.svg` | "Pick for 3-4 parallel aspects of one subject with per-aspect titles + short body (self-introduction, four-pillar overview, capability quadrant). Skip for plain feature lists (use icon_grid), sequential steps (use numbered_steps), or strategic quadrants (use quadrant_text_bullets / matrix_2x2)." | 双书展并列卡：abC（2015 创办，京沪双城）+ UNFOLD（高摊位费，大客流） |
| P14 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | 怎么逛独立书店 4 条要点：看选品 / 留 1 小时 / 带现金 / 拍照先问 |
| P15 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | 怎么收藏 zine 4 条：从兴趣切入 / 塑封保护 / 跟踪作者 IG / 参加 zine fair |
| P16 | numbered_steps | `templates/charts/numbered_steps.svg` | "Pick for 3-6 horizontal sequential steps with numeric emphasis — how-it-works section, getting-started guide, methodology overview, implementation phases. Skip if steps need connector arrows (use process_flow) or named output artifacts (use pipeline_with_stages)." | 第一本 zine 行动清单 4 步：选主题 / 折一张 A4 / 填 8 页 / 印 10 份送出去 |

**Runners-up considered**:

- `roadmap_vertical` | rejected for P04: timeline 数据是横向年代轴的"事件 milestone"（无 duration），roadmap_vertical 适用"项目里程碑+状态"，本页是文化史轴更贴 timeline
- `agenda_list` | rejected for P02 备选 `vertical_list`: agenda_list 含 duration/owner 列匹配"目录+页码区间"语义；vertical_list 是"原则/要点"型清单，语义不符
- `process_flow` | rejected for P06: process_flow 有连接箭头适合审批流；Riso 工作流是"工艺步骤"无分叉无审批语义，numbered_steps 更轻
- `icon_grid` | rejected for P08 内容类型本身就是 icon_grid（用作正选）；rejected for P14/P15 因 P14/P15 是"原则要点"非"能力/特性"
- `consulting_table` | rejected for P12: 表格是纯文本+定性标签（★），无 micro bar 数据可视；basic_table 正解

---

## VIII. Image Resource List

> Layout pattern 列内的 `#<id>` 全部 verbatim 引用 `references/image-layout-patterns.md`（Part 1 Primary + Part 2 Modifiers）。Image-as-canvas coverage（#38–#46）由 P07 + P09 承担。

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_hero.png | 1280×720 | 1.78 | P01 封面 hero | Background | `#1 Full-bleed background with floating title + #27 Linear gradient mask for text legibility + #29 Two-stop scrim — opaque on text side, transparent on focal side` | ai | Pending | "A risograph print studio scene: a hand-pulled silkscreen 'pull' of a two-color zine sheet rising from a paper stack; ink rollers and color drums visible in the lower edge; left side reserved as calm flat color block for large title overlay; bold silhouette composition" | none | hero_page |
| zine_history_collage.png | 760×420 | 1.81 | P03 装饰图：zine 是什么 | Illustration | `#13 Narrow vertical image strip + giant horizontal title + #21 Rounded rectangle crop` | ai | Pending | "Collage silhouette of stacked zines across eras: a sci-fi pulp magazine corner, a punk fanzine front, a riot grrrl xeroxed page, a modern art-book spine — overlapping at slight angles like a desk pile; the stack is the only motif, off-white paper background visible behind" | none | local |
| risograph_machine.png | 720×900 | 0.80 | P05 Risograph 工艺侧栏 | Illustration | `#18 Image as full-height sidebar column + #21 Rounded rectangle crop` | ai | Pending | "Front-three-quarter view of a vintage Risograph duplicator (Riso EZ200 era), boxy industrial silhouette, two color drums visible through a side panel slot, paper tray protruding from front; clean stencil-cut machine outline, no operator, isolated against off-white paper field" | none | local |
| risograph_process_banner.png | 1280×280 | 4.57 | P06 工艺横幅 | Diagram | `#14 Horizontal banner strip cutting through mid-section + #29 Two-stop scrim` | ai | Pending | "Horizontal silkscreen frieze depicting Risograph workflow: from left to right — a digital file glyph, a stencil master sheet, a wrapped color drum, an inked roller pressing paper, a paper output stack; five stages connected by subtle ink-trail lines; bold stencil silhouettes, no text labels on the image" | none | local |
| zine_folding_hands.png | 1080×720 | 1.50 | P07 八页折叠示意 hero | Illustration | `#38 Background image + annotation cards with bezier leader lines + #21 Rounded rectangle crop` | ai | Pending | "Overhead view of two hands folding a single A4 sheet into an 8-page zine; the sheet partially folded mid-crease, scissors and pencil nearby; composition leaves four open negative-space pockets in corners for native SVG annotation cards to overlay; soft top-down vantage" | none | local |
| jimbocho_hero.png | 1280×720 | 1.78 | P09 神保町 hero | Background | `#1 Full-bleed background with floating title + #29 Two-stop scrim + #27 Linear gradient mask for text legibility` | ai | Pending | "Tokyo Jimbocho bookstore street at evening: rows of paper-lantern shop signs glowing, stacked secondhand books spilling onto sidewalk shelves, narrow alley vanishing into perspective; bold silhouette of pedestrian browsing in foreground; cinematic poster framing" | none | hero_page |
| three_cities_triptych.png | 1160×400 | 2.90 | P10 三城三店三联 | Illustration | `#56 Image triptych + #21 Rounded rectangle crop + #70 Image with thin colored matte frame` | ai | Pending | "Three-panel triptych baked in one image, panels equal width separated by 4px gutters. Left panel: Paris's Shakespeare and Company exterior — narrow green-fronted shop with cobbled foreground. Middle panel: London Word-on-the-Water bookbarge on canal at dusk. Right panel: New York Strand Bookstore corner with the red awning visible. All three panels in matching screen-print silhouette style, unified color treatment for visual continuity" | none | local |
| berlin_bucherbogen.png | 1280×720 | 1.78 | P11 柏林 hero | Background | `#1 Full-bleed background with floating title + #12 Faded image as backdrop with oversized overlay text` | ai | Pending | "Berlin Bücherbogen under S-Bahn arches: arched brick vault interior, light spilling from book-lined walls under the curved ceiling, a single train rumble silhouette implied above; central calm zone reserved for huge overlay title; atmospheric depth via halftone gradation" | none | hero_page |
| zine_fair_scene.png | 720×720 | 1.00 | P13 书展现场氛围 | Illustration | `#2 Left-third image + right text body + #21 Rounded rectangle crop + #70 Image with thin colored matte frame` | ai | Pending | "Art-book-fair booth aisle scene: rows of low tables stacked with zines and small-press books, a few visitor silhouettes browsing, hand-lettered booth signs visible but unreadable, ceiling string-lights overhead; bold flat composition, no readable text in scene" | none | local |
| zine_action_outro.png | 1280×720 | 1.78 | P18 封底 outro hero | Background | `#1 Full-bleed background with floating title + #12 Faded image as backdrop with oversized overlay text + #29 Two-stop scrim` | ai | Pending | "Single open hand from above holding up a small folded zine toward the viewer; the zine cover slightly halftoned; rest of canvas is open paper field; composition designed to host enormous closing-line typography overlay in upper region" | none | hero_page |

> **User-provided photos** (in `sources/`, available as visual references for Image_Generator prompts — not embedded directly): `riso_ez200_printer.jpg`, `risograph_two_color_print.jpg`, `shakespeare_and_company_paris.jpg`, `jimbocho_yaguchi_koga.jpg`, `jimbocho_used_books.jpg`, `sanseido_bookstore.jpg`. Strategist 不将其作为 §VIII 资源行（避免与 ai 行 hero 冲突）；Image_Generator 在 prompt 撰写时可参照其构图与氛围。

---

## IX. Content Outline

### Part 1: 开篇

#### Slide 01 - Cover 封面

- **Layout**: Full-bleed hero image + floating Impact 大字标题（zine 海报感）
- **Title**: 「Zine 文化指南 / INDIE BOOKSTORE × ZINE」
- **Subtitle**: 一份从一张纸到一家书店的独立出版地图
- **Info**: PPT Master Risograph 风格演示 · 2026

#### Slide 02 - 目录

- **Layout**: agenda_list（5 节 + 简述 + 页码区间）
- **Title**: 目录 / TABLE OF CONTENTS
- **Visualization**: agenda_list
- **Content**:
  - 01 zine 是什么 + 简史四浪潮（P03–P04）
  - 02 Risograph：zine 工艺的灵魂载体（P05–P06）
  - 03 怎么自己做一本 zine（P07–P08）
  - 04 全球 + 中国独立书店地图（P09–P13）
  - 05 怎么逛 / 怎么收藏 / 行动清单（P14–P18）

### Part 2: zine 是什么

#### Slide 03 - zine 是什么

- **Layout**: 大字定义 + 左侧 narrow vertical image strip + 三条特征列举
- **Title**: ZINE = MAGAZINE − 商业逻辑
- **Content**:
  - 自制、非商业、印量极小（多在 1000 份以内，常少于 100）
  - 装订简单 / 内容混合 / 完全作者主权
  - 与 magazine / book 的边界：印量 + 商业意图 + 编辑流程

#### Slide 04 - zine 简史四浪潮

- **Layout**: timeline 横向年代轴
- **Title**: 一百年里 zine 的四次浪潮
- **Visualization**: timeline
- **Content**:
  - 1920s 业余出版 + 哈莱姆 *Fire!!*
  - 1930s 科幻同人志 *The Comet* / "fanzine" 一词 1940 由 Russ Chauvenet 创
  - 1976 朋克 *Sniffin' Glue* 复印机普及
  - 1991 Riot Grrrl *Bikini Kill* + Riot Grrrl Press
  - 2010s 当代复兴 + zine fair 爆发

### Part 3: Risograph

#### Slide 05 - Risograph 起源 + 视觉特征

- **Layout**: 左侧 full-height 机器侧栏图 + 右侧 vertical_list 4 视觉特征
- **Title**: Risograph：zine 工艺的灵魂载体
- **Visualization**: vertical_list
- **Content**:
  - 起源：Riso Kagaku 1946 / Risograph 007 1986
  - 视觉特征 1：限定调色板（一墨筒一色）
  - 视觉特征 2：套色错位 1–3px（misregistration）
  - 视觉特征 3：半色调网点 + 油墨气味
  - 视觉特征 4：色块叠加产生第三色

#### Slide 06 - Risograph 工作流程

- **Layout**: 中段横幅图（工艺示意）+ 下方 numbered_steps 5 步
- **Title**: 工艺：5 步从数字图像到印张
- **Visualization**: numbered_steps
- **Content**:
  - ① 接收数字图像
  - ② 烧蚀像素化母版
  - ③ 母版包裹彩色墨筒
  - ④ 墨筒滚压油墨到纸
  - ⑤ 多次过纸完成多色

### Part 4: 怎么自己做一本 zine

#### Slide 07 - 八页折叠法

- **Layout**: 中央 hero 图（折叠的手）+ 四角 annotation cards（image-as-canvas + bezier 引线 #38）
- **Title**: 一张纸 → 一本 zine
- **Visualization**: numbered_steps（叠加在 image-as-canvas 上）
- **Content**:
  - ① 折叠：长边对折 → 短边对折 → 中线对折，得 8 矩形
  - ② 关键剪口：从对折边沿剪到中心点
  - ③ 组装：双手两端往中心推
  - ④ 填内容：没有规则

#### Slide 08 - 内容类型

- **Layout**: icon_grid 2×3 或 3×2
- **Title**: 你能填的东西
- **Visualization**: icon_grid
- **Content**:
  - 草图 / 涂鸦 / 迷你漫画（pencil）
  - 诗 / 宣言 / 短文（pen-nib）
  - 带插图的食谱（sticky-note）
  - 家庭照片 + 私人写作（book）
  - 拼贴 + 混合媒材（scissors）
  - 实验性视觉（brush）

### Part 5: 全球独立书店

#### Slide 09 - 东京 Jimbōchō 神保町

- **Layout**: Full-bleed hero + 大字 + 左下三条事实条
- **Title**: 神保町 / JIMBŌCHŌ
- **Content**:
  - 全球最大旧书街之一：130–180 家书店
  - 1875 Takayama Honten / 1902 Kitazawa English Books / 2015 Morioka Shoten（一周一本）
  - 2025 Time Out "全球最酷街区"

#### Slide 10 - 巴黎 / 伦敦 / 纽约

- **Layout**: vertical_pillars 1×3
- **Title**: 三座城市，三种姿态
- **Visualization**: vertical_pillars
- **Content**:
  - **巴黎 Shakespeare and Company**：1951 George Whitman 现址；曾接纳数千 tumbleweeds 写作者
  - **伦敦 Daunt + Word on the Water**：Daunt 按国家分类；Word on the Water 1920s 荷兰运河船
  - **纽约 Strand + Yu and Me**：1927 Strand 18 英里书架；2021 Yu and Me 华埠亚裔女性书店

#### Slide 11 - 柏林 Bücherbogen

- **Layout**: Full-bleed hero + 大字 + 浮动定义文字
- **Title**: BÜCHERBOGEN
- **Content**:
  - 位于 S-Bahn 高架桥下，砖砌拱顶
  - 专攻艺术、设计、摄影、电影、建筑

#### Slide 12 - 中国大陆书店地图

- **Layout**: basic_table（4 列 × 15 行）
- **Title**: 中国独立书店地图（zine 倾向）
- **Visualization**: basic_table
- **Content**: 15 家书店表 —— 书店 / 城市 / 特色 / zine 倾向（★/★★/★★★）

#### Slide 13 - 中国艺术书展

- **Layout**: labeled_card 双卡并列（abC + UNFOLD）
- **Title**: 中国艺术书展双子星
- **Visualization**: labeled_card
- **Content**:
  - **abC Art Book Fair**：2015 创办，京沪双城，第 6 届上海 145 中国 + 41 国际 + 10,000 参观
  - **UNFOLD Shanghai Art Book Fair**：abC 后一周举办，更高摊位费 + 更大客流

### Part 6: 怎么逛 / 怎么收藏 / 行动

#### Slide 14 - 怎么逛独立书店

- **Layout**: vertical_list 4 条
- **Title**: 进店前的 4 条
- **Visualization**: vertical_list
- **Content**:
  - ① 看选品 = 看店主 —— 独立书店本质是"精神书架"
  - ② 留至少 1 小时 —— 浏览本身就是产品
  - ③ 带现金 —— 一些小店不接受电子支付
  - ④ 拍照前先问 —— 多数独立书店对拍照敏感

#### Slide 15 - 怎么收藏 zine

- **Layout**: vertical_list 4 条
- **Title**: 收藏 zine 的 4 条
- **Visualization**: vertical_list
- **Content**:
  - ① 从一本起步 —— 找你最关心的主题
  - ② 用塑料封套保护 —— 二次印刷罕见
  - ③ 跟踪作者 / 出版方 Instagram
  - ④ 参加 abC / UNFOLD —— 新刊首发就是现场

#### Slide 16 - 行动清单：你的第一本 zine

- **Layout**: numbered_steps 4 步
- **Title**: 你的第一本 zine：4 步起手
- **Visualization**: numbered_steps
- **Content**:
  - ① 选一个真心关心的主题（不必宏大）
  - ② 折一张 A4 —— 用本 deck P07 的方法
  - ③ 填 8 页 —— 手写 / 拼贴 / 复印的旧照片
  - ④ 印 10 份 —— 5 份送朋友，5 份寄给独立书店

#### Slide 17 - Sources & 致谢

- **Layout**: 双列 sources 罗列 + 致谢小字
- **Title**: Sources / References
- **Content**: 来源链接清单（Wikipedia / My Modern Met / AFAR / The Creative Independent / 数英 / Sixth Tone 等）

#### Slide 18 - 封底 outro

- **Layout**: Full-bleed hero（手举 zine）+ 大字 outro
- **Title**: 「印一份。送一份。换一份。」
- **Subtitle**: A zine is the world's smallest publishing house. It can also be yours.

---

## X. Speaker Notes Requirements

- **Filename**: 与 SVG 名一一对应（`01_cover.svg` → `notes/01_cover.md`）
- **Style**: conversational（适合咖啡馆 / 分享会场景，不走正式）
- **Total duration**: ~12-15 分钟（每页 40-50 秒）
- **Purpose**: inspire（让人想做一本 zine 而不只是知道 zine）

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements with `#F5EFE0` paper color
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency defaults to `fill-opacity` / `stroke-opacity`; `rgba()` remains converter-compatible
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. Text characters: raw Unicode (`—`, `→`, `©`, NBSP); HTML named entities (`&nbsp;`, `&mdash;`) FORBIDDEN. XML reserved chars escape as `&amp; &lt; &gt; &quot; &apos;`
7. **Risograph 美学专项**：
   - 套色错位用偏移色块叠加模拟（如同一形状的 Federal Blue 与 Fluorescent Pink 副本 offset 1-3px）
   - 半色调网点用 `<pattern>` + 小 circles 模拟（dot density 控制）
   - 卡片无圆角（border-radius: 0）—— 与 Riso 印刷工艺一致
8. `clipPath` 仅允许应用于 `<image>` 元素；卡片 / 块面用原生 `<rect>` 描述
9. Icon 严格只用 `chunk-filled/` 库列表中的 27 个；缺失图标在库内找最近替代，禁止混库

### PPT Compatibility Rules

- 默认逐子元素设置 opacity；`<g opacity="...">` 可转换但会产生近似保真 warning
- Image transparency 用覆盖层 (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only；external CSS 与 `@font-face` FORBIDDEN
- Impact 字体是 PPT 内置 display 字体，可安全使用；Microsoft YaHei / Consolas 同样 Windows 预装

---

## ✅ Design spec complete.

Next step:
- Images include AI generation → Invoke Image_Generator
