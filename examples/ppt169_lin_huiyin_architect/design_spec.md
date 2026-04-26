# 林徽因：被文学光环遮蔽的建筑巨匠 - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 林徽因：被文学光环遮蔽的建筑巨匠 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | General Versatile (A) |
| **Target Audience** | 文化爱好者、建筑学关注者、历史人文读者 |
| **Use Case** | 知识分享、纪念专题、文化传播 |
| **Created Date** | 2026-04-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px，上下 50px |
| **Content Area** | 1160×620 (60,50 → 1220,670) |

---

## III. Visual Theme

### Theme Style

- **Style**: General Versatile — 图文并茂、视觉叙事
- **Theme**: Dark theme（深色主题）
- **Tone**: 中式古典建筑美学 × 人文纪念感。以深藏青为底、古铜金为魂，营造庄重典雅、跨越时空的历史感

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#1A1A2E` | 深藏青页面背景，沉稳厚重 |
| **Secondary bg** | `#16213E` | 卡片底色、分区背景 |
| **Primary** | `#C9A96E` | 古铜金，标题装饰、关键区块、图标 |
| **Accent** | `#E8D5B7` | 暖象牙，高光数据、重点信息 |
| **Secondary accent** | `#8B6F47` | 深棕色，辅助强调、渐变过渡 |
| **Body text** | `#E8E8E8` | 浅灰白正文文字 |
| **Secondary text** | `#A0A0B0` | 灰色注释说明 |
| **Tertiary text** | `#6B6B80` | 页码、辅助信息 |
| **Border/divider** | `#2A2A4A` | 卡片边框、分隔线 |
| **Success** | `#4CAF50` | 正向指标（绿色系） |
| **Warning** | `#E57373` | 问题标记（红色系） |

### Gradient Scheme

```xml
<!-- 标题渐变（金色系） -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#C9A96E"/>
  <stop offset="100%" stop-color="#E8D5B7"/>
</linearGradient>

<!-- 背景装饰光晕 -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#C9A96E" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#C9A96E" stop-opacity="0"/>
</radialGradient>

<!-- 卡片渐变底色 -->
<linearGradient id="cardGradient" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#16213E"/>
  <stop offset="100%" stop-color="#1A1A2E"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Recommended preset**: P3 — Culture/Arts/Humanities

| Role | Chinese | English | Fallback |
| ---- | ------- | ------- | -------- |
| **Title** | KaiTi | Georgia | serif |
| **Body** | Microsoft YaHei | Arial | sans-serif |
| **Code** | - | Consolas | Monaco |
| **Emphasis** | SimHei | Arial | sans-serif |

**Font stack**: `"KaiTi", Georgia, serif` (标题) / `"Microsoft YaHei", Arial, sans-serif` (正文)

### Font Size Hierarchy

**Baseline**: Body font size = 22px (内容密度适中)

| Purpose | Ratio | Size | Weight |
| ------- | ----- | ---- | ------ |
| Cover title | 2.5x | 54px | Bold |
| Chapter title | 2x | 44px | Bold |
| Content title | 1.5x | 32px | Bold |
| Subtitle | 1.3x | 28px | SemiBold |
| **Body content** | **1x** | **22px** | Regular |
| Annotation | 0.73x | 16px | Regular |
| Page number/date | 0.55x | 12px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 高 80px — 页面标题 + 金色装饰线
- **Content area**: 高 540px — 主要内容区域
- **Footer area**: 高 40px — 页码 + 来源信息

### Common Layout Modes

| Mode | Suitable Scenarios |
| ---- | ----------------- |
| **Single column centered** | 封面、结尾、关键引言 |
| **Left-right split (4:6)** | 图文混排（图片+文字说明） |
| **Left-right split (5:5)** | 双概念对比 |
| **Three-column cards** | 并列要点、作品展示 |
| **Top-bottom split** | 超宽图片 + 文字 |
| **Timeline** | 人生轨迹、编年概述 |

### Spacing Specification

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Content block gap | 32px |
| Card padding | 24px |
| Card border radius | 12px |
| Icon-text gap | 12px |
| Single-row card height | 540px |
| Double-row card height | 260px each |
| Three-column card width | 360px each |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/chunk/` (直线几何风格，适配典雅庄重调性)
- **Library**: `chunk`
- **Usage method**: Placeholder format `{{icon:chunk/icon-name}}`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 建筑/设计 | `{{icon:chunk/building}}` | Slide 03, 04 |
| 古堡/历史建筑 | `{{icon:chunk/castle}}` | Slide 03 |
| 博物馆/文化 | `{{icon:chunk/museum}}` | Slide 04 |
| 地图/考察 | `{{icon:chunk/map}}` | Slide 05 |
| 圆规/制图 | `{{icon:chunk/compass-drafting}}` | Slide 06 |
| 书籍/学术 | `{{icon:chunk/book-open}}` | Slide 07 |
| 钢笔/写作 | `{{icon:chunk/pen-nib}}` | Slide 08 |
| 皇冠/巨匠 | `{{icon:chunk/crown}}` | Slide 01, 10 |
| 星星/成就 | `{{icon:chunk/star}}` | Slide 09 |
| 旗帜/先驱 | `{{icon:chunk/flag}}` | Slide 09 |
| 心/情怀 | `{{icon:chunk/heart}}` | Slide 10 |
| 眼睛/重识 | `{{icon:chunk/eye}}` | Slide 02 |
| 时钟/时光 | `{{icon:chunk/clock}}` | Slide 02 |
| 全球/影响力 | `{{icon:chunk/globe}}` | Slide 07 |

---

## VII. Visualization Reference List

| Visualization Type | Reference Template | Used In | Purpose |
| ------------------ | ------------------ | ------- | ------- |
| timeline | `templates/charts/timeline.svg` | Slide 02 | 林徽因人生关键节点时间轴 |
| icon_grid | `templates/charts/icon_grid.svg` | Slide 03 | 建筑作品一览（多项目卡片） |
| vertical_list | `templates/charts/vertical_list.svg` | Slide 07 | 学术贡献要点列表 |

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Status | Generation Description |
| -------- | --------- | ----- | ------- | ---- | ------ | --------------------- |
| cover_bg.png | 1280x720 | 1.78 | 封面背景 | Background | Pending generation | Chinese traditional architectural elements (curved tile rooflines, wooden brackets/dougong) silhouetted against a deep navy-to-midnight blue gradient sky (#1A1A2E to #16213E), golden light (#C9A96E) glowing along the roofline edges, subtle mist/cloud in lower third, clean center area reserved for title text overlay, cinematic atmospheric style |
| lin_portrait.png | 640x703 | 0.91 | 封面人物肖像 | Photography | Existing | - |
| jihai_station_old.png | 670x346 | 1.94 | 吉海铁路总站历史照片 | Photography | Existing | - |
| jihai_station_new.png | 1080x608 | 1.78 | 修复后的吉海铁路总站 | Photography | Existing | - |
| pku_geology.png | 745x414 | 1.80 | 北大地质馆旧址 | Photography | Existing | - |
| yingqiu_院.png | 792x606 | 1.31 | 映秋院历史照片 | Photography | Existing | - |
| kunming_site.png | 1080x783 | 1.38 | 昆明建筑工地 | Photography | Existing | - |
| babaoshan.png | 1080x712 | 1.52 | 八宝山革命公墓 | Photography | Existing | - |
| lin_tomb.png | 1080x796 | 1.36 | 林徽因墓碑 | Photography | Existing | - |
| monument.png | 960x1280 | 0.75 | 人民英雄纪念碑 | Photography | Existing | - |
| liang_lin_together.png | 1000x710 | 1.41 | 梁思成与林徽因合影 | Photography | Existing | - |
| first_paper.png | 1080x810 | 1.33 | 首篇建筑论文 | Photography | Existing | - |
| lin_survey.png | 1056x1080 | 0.98 | 林徽因考察古建筑 | Photography | Existing | - |
| lin_later.png | 857x804 | 1.07 | 林徽因晚年照片 | Photography | Existing | - |

---

## IX. Content Outline

### Part 1: 开篇

#### Slide 01 - 封面

- **Layout**: 全屏背景图 + 居中竖排标题 + 人物剪影
- **Title**: 林徽因：被文学光环遮蔽的建筑巨匠
- **Subtitle**: 逝世70周年 · 重识中国建筑史上的女性力量
- **Info**: 凤凰空间 · 2025
- **Image**: cover_bg.png (全屏底), lin_portrait.png (右侧)

#### Slide 02 - 人生轨迹概览

- **Layout**: 横向时间轴
- **Title**: 建筑巨匠的一生
- **Visualization**: timeline
- **Content**:
  - 1904 出生于杭州
  - 1924 赴美留学宾夕法尼亚大学
  - 1928 与梁思成结婚，归国
  - 1930 加入中国营造学社
  - 1932 发表首篇建筑论文
  - 1937-1946 战时流亡，坚持研究
  - 1949 参与国徽设计
  - 1952 参与人民英雄纪念碑设计
  - 1955 逝世，墓碑刻"建筑师林徽因墓"

### Part 2: 建筑师林徽因

#### Slide 03 - 为数不多的建筑作品（上）

- **Layout**: 三列卡片布局
- **Title**: 归国初期的建筑实践
- **Visualization**: icon_grid
- **Content**:
  - 1929 梁启超墓碑设计 — 学成归来第一件作品
  - 1929 吉林大学石头楼 — 参与"梁陈童蔡营造事务所"设计
  - 1929 吉海铁路总站 — 林徽因设计总体风貌，哥特式雄狮造型

#### Slide 04 - 为数不多的建筑作品（下）

- **Layout**: 左右分栏（4:6），左图右文
- **Title**: 战火中的建筑理想
- **Content**:
  - 1932 北大地质馆与女生宿舍 — 中国最早引入西方现代主义建筑
  - 1938 云南大学映秋院 — 融合云南民间建筑元素
  - 1938 西南联大校舍 — "一生中最痛苦、最委屈的设计"
  - 1940 昆明自宅 — 两位建筑师一生唯一为自己设计的房子
- **Image**: kunming_site.png

#### Slide 05 - 丰碑之作

- **Layout**: 左右分栏（5:5），左文右图
- **Title**: 国之重器上的建筑印记
- **Content**:
  - 1950 八宝山革命公墓 — 主体建筑格局设计
  - 1952 人民英雄纪念碑 — 提出创造性修改方案
  - 亲自设计碑座全套饰纹与花环浮雕
  - 以唐代风格为蓝本，展现中国传统建筑美学
  - 墓碑上只有七个字：建筑师林徽因墓
- **Image**: monument.png

### Part 3: 被低估的学术先驱

#### Slide 06 - 中国建筑理论的奠基者

- **Layout**: 左右分栏（4:6），左图右文
- **Title**: 首篇建筑论文：技惊四座
- **Content**:
  - 1932《论中国建筑之几个特征》— 首次由中国专业学者发表的建筑理论文章
  - 首次在理论上定义了中国建筑木框架结构体系的基本特征
  - 反驳西方学者对中国建筑的误读
  - 描绘出关于中国建筑史的完整概念框架
- **Image**: first_paper.png

#### Slide 07 - 独创概念与超前思想

- **Layout**: 纵向要点列表
- **Title**: 学术贡献一览
- **Visualization**: vertical_list
- **Content**:
  - "建筑意"概念 — 原创性的中国建筑美学理念，建筑是技术、美、历史与人情的凝聚
  - 《清式营造则例》绪论 — 归纳中国建筑理论框架
  - 民居研究先驱 — 在中国建筑界率先提出保护民间建筑
  - 《现代住宅设计的参考》 — 远见性地提出战后为普通人设计建筑
  - 首开"住宅概论"课 — 1949年清华大学首次系统教授现代住宅设计理论

### Part 4: 强者与精神

#### Slide 08 - 远比传闻更震撼的一生

- **Layout**: 左右分栏（5:5），左文右图
- **Title**: 穿越战火的建筑斗士
- **Content**:
  - 荒郊野谷考察古建筑，风餐露宿不退缩
  - "只要梁先生敢爬敢上的，林先生就敢上"
  - 战乱流亡中肺炎发作，此后再未恢复健康
  - 带病坚持在偏远小镇一笔一笔书写中国建筑史
  - "什么美人不美人，我还有好多事要做呢！"
- **Image**: lin_survey.png

#### Slide 09 - 她想要终生奋斗的事业

- **Layout**: 引言卡片 + 成就总结
- **Title**: 当之无愧的建筑师
- **Content**:
  - 引言："我自己也到了相当年纪，也没有什么成就…我禁不住伤心起来" — 28岁写给胡适的信
  - 与梁思成共同创办东北大学、清华大学建筑系
  - 深入荒凉之地一寸寸测量古建筑
  - 在国徽和纪念碑上倾注最后心血
  - 她是学科的奠基者，更是思想上的先行者

#### Slide 10 - 结尾

- **Layout**: 单列居中，引言式
- **Title**: 建筑师林徽因墓
- **Subtitle**: 她用一生证明，她是当之无愧的建筑师
- **Content**:
  - 中央金色竖线装饰
  - 墓碑铭文引用
  - 致敬语
  - 来源信息

---

## X. Speaker Notes Requirements

- **File naming**: Match SVG names (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Total duration**: ~15 minutes
- **Notes style**: 叙述型（Narrative），兼具历史厚重感与人文温度
- **Presentation purpose**: Inspire + Inform（致敬与知识传递）
- **Content includes**: 每页演讲要点、补充历史细节、过渡衔接语

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
