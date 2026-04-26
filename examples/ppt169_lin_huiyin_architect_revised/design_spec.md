# 林徽因：重识建筑师，而非传说 - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 林徽因：重识建筑师，而非传说 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 9 |
| **Design Style** | General Versatile (A) |
| **Target Audience** | 建筑与人文兴趣受众、文化传播从业者、讲座观众 |
| **Use Case** | 纪念专题短讲、展陈式内容演示、公众号内容延展分享 |
| **Created Date** | 2026-04-22 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 64px，上下 48px |
| **Content Area** | 1152×624 (64,48 → 1216,672) |

---

## III. Visual Theme

### Theme Style

- **Style**: General Versatile — 博物馆展陈感、建筑图志感、编辑化版式
- **Theme**: Light theme（浅底展签式视觉）
- **Tone**: 克制、考据、现代，避免“厚重纪念片”套路，强调“重新认识”与“建筑专业身份”

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F6F1E8` | 主背景，纸张感米白 |
| **Secondary bg** | `#EFE7DA` | 分区底色、卡片浅底 |
| **Primary** | `#A44A3F` | 建筑砖红，主标题、关键引导线 |
| **Accent** | `#6E7C80` | 青灰，用于结构线与辅助标签 |
| **Secondary accent** | `#B6915E` | 金棕，用于强调与页码装饰 |
| **Body text** | `#1F1B16` | 主正文深墨黑 |
| **Secondary text** | `#6A6258` | 图注、说明、注解 |
| **Tertiary text** | `#978C7E` | 页脚、辅助信息 |
| **Border/divider** | `#D8CBB8` | 细分隔线、轮廓线 |
| **Success** | `#4F7A59` | 正向标记 |
| **Warning** | `#B45B4C` | 风险、争议、历史张力标记 |

### Gradient Scheme (if needed, using SVG syntax)

```xml
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#A44A3F"/>
  <stop offset="100%" stop-color="#B6915E"/>
</linearGradient>

<linearGradient id="paperFade" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#F6F1E8"/>
  <stop offset="100%" stop-color="#EFE7DA"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: editorial display + modern CJK sans

| Role | Chinese | English | Fallback |
| ---- | ------- | ------- | -------- |
| **Title** | Songti SC | Georgia | SimSun |
| **Body** | PingFang SC | Arial | Microsoft YaHei |
| **Emphasis** | SimHei | Arial | Microsoft YaHei |
| **Code** | - | Consolas | Courier New |

**Per-role font stacks**:
- Title: `Georgia, "Times New Roman", "Songti SC", SimSun, serif`
- Body: `"PingFang SC", "Microsoft YaHei", Arial, sans-serif`
- Emphasis: `"Microsoft YaHei", Arial, sans-serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 20px

| Purpose | Ratio to body | 24px baseline (relaxed) | 18px baseline (dense) | Weight |
| ------- | ------------- | ---------------------- | -------------------- | ------ |
| Cover title (hero headline) | 2.5-5x | 60-120px | 45-90px | Bold / Heavy |
| Chapter / section opener | 2-2.5x | 48-60px | 36-45px | Bold |
| Page title | 1.5-2x | 36-48px | 27-36px | Bold |
| Hero number (consulting KPIs) | 1.5-2x | 36-48px | 27-36px | Bold |
| Subtitle | 1.2-1.5x | 29-36px | 22-27px | SemiBold |
| **Body content** | **1x** | **24px** | **18px** | Regular |
| Annotation / caption | 0.7-0.85x | 17-20px | 13-15px | Regular |
| Page number / footnote | 0.5-0.65x | 12-16px | 9-12px | Regular |

**Current project anchors**:
- Cover title: 64px
- Page title: 34px
- Subtitle: 24px
- Body: 20px
- Annotation: 14px
- Page number: 11px

---

## V. Layout Principles

### Page Structure

- **Header area**: 88px，高标题区，含页码与章节标识
- **Content area**: 560px，主内容区
- **Footer area**: 24px，来源/页码/说明信息

### Layout Pattern Library (combine or break as content demands)

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | 封面、结尾、核心判断 |
| **Asymmetric split (4:6 / 5:5)** | 图文叙事、作品说明 |
| **Three-column cards** | 作品拼图、贡献拆解 |
| **Matrix grid (2×2)** | 多图现场对照 |
| **Z-pattern / waterfall** | 生平与方法论展开 |
| **Figure-text overlap** | 封面、人物页、纪念碑页 |
| **Negative-space-driven** | “重新认识”式强调页 |

### Spacing Specification

**Universal**:

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 40-60px | 48-64px |
| Content block gap | 24-40px | 28px |
| Icon-text gap | 8-16px | 10px |

**Card-based layouts**:

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Card gap | 20-32px | 24px |
| Card padding | 20-32px | 22px |
| Card border radius | 8-16px | 14px |
| Single-row card height | 530-600px | 540px |
| Double-row card height | 265-295px each | 268px |
| Three-column card width | 360-380px each | 356px |

**Non-card containers**:

- 用留白和细分隔线，而非大量深色大卡片
- 图注与正文分层明确，图像边缘允许与文本轻微叠压形成编辑感
- breathing 页避免多卡片并列

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/tabler-outline/`
- **Library**: `tabler-outline`
- **Usage method**: Placeholder format `{{icon:tabler-outline/icon-name}}`

### Recommended Icon List (fill as needed)

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 建筑身份 | `{{icon:tabler-outline/building}}` | Slide 01, 03 |
| 纪念性建筑 | `{{icon:tabler-outline/building-monument}}` | Slide 05, 09 |
| 校园与教育 | `{{icon:tabler-outline/school}}` | Slide 04, 07 |
| 交通建筑 | `{{icon:tabler-outline/train}}` | Slide 03 |
| 测绘与勘察 | `{{icon:tabler-outline/compass}}` | Slide 07, 08 |
| 论文与著述 | `{{icon:tabler-outline/article}}` | Slide 06 |
| 学术出版 | `{{icon:tabler-outline/book-2}}` | Slide 07 |
| 重识/观看 | `{{icon:tabler-outline/eye}}` | Slide 02 |
| 历史节点 | `{{icon:tabler-outline/timeline}}` | Slide 03 |
| 先驱/方向 | `{{icon:tabler-outline/flag}}` | Slide 07 |
| 人文温度 | `{{icon:tabler-outline/heart}}` | Slide 08, 09 |
| 世界眼光 | `{{icon:tabler-outline/globe}}` | Slide 06 |

---

## VII. Visualization Reference List (if needed)

| Visualization Type | Reference Template | Used In |
| ------------------ | ------------------ | ------- |
| timeline | `templates/charts/timeline.svg` | Slide 03 |
| icon_grid | `templates/charts/icon_grid.svg` | Slide 07 |
| vertical_list | `templates/charts/vertical_list.svg` | Slide 06 |

---

## VIII. Image Resource List (if needed)

| Filename | Dimensions | Ratio | Purpose | Type | Status | Generation Description |
| -------- | --------- | ----- | ------- | ---- | ------ | --------------------- |
| lin_portrait.png | 640x703 | 0.91 | 封面人物主视觉 | Photography | Existing | - |
| jihai_station_old.png | 670x346 | 1.94 | 吉海铁路总站历史照片 | Photography | Existing | - |
| jihai_station_new.png | 1080x608 | 1.78 | 吉海铁路总站修复后照片 | Photography | Existing | - |
| pku_geology.png | 745x414 | 1.80 | 北大地质馆旧址 | Photography | Existing | - |
| yingqiu_yuan.png | 792x606 | 1.31 | 映秋院历史照片 | Photography | Existing | - |
| kunming_site.png | 1080x783 | 1.38 | 昆明自宅相关照片 | Photography | Existing | - |
| babaoshan.png | 1080x712 | 1.52 | 八宝山革命公墓 | Photography | Existing | - |
| monument.png | 960x1280 | 0.75 | 人民英雄纪念碑 | Photography | Existing | - |
| lin_tomb.png | 1080x796 | 1.36 | 林徽因墓碑 | Photography | Existing | - |
| first_paper.png | 1080x810 | 1.33 | 首篇建筑论文图像 | Photography | Existing | - |
| liang_lin_together.png | 1000x710 | 1.41 | 梁思成与林徽因合影 | Photography | Existing | - |
| lin_survey.png | 1080x1145 | 0.94 | 实地考察古建筑照片 | Photography | Existing | - |
| lin_later.png | 640x640 | 1.00 | 晚年肖像 | Photography | Existing | - |

---

## IX. Content Outline

### Part 1: 重新认识她

#### Slide 01 - 封面

- **Layout**: 左侧大标题 + 右侧竖向人物照片 + 下方展签式副标题
- **Title**: 林徽因
- **Subtitle**: 重识建筑师，而非传说
- **Content**:
  - 小标题：逝世 70 周年
  - 辅助说明：从作品、理论与行动三个维度，重看她在中国建筑史中的位置
- **Image**: lin_portrait.png

#### Slide 02 - 为什么今天要重识林徽因

- **Layout**: breathing 页，中央判断句 + 三个并列观察维度
- **Title**: 被看见的，常常不是她最重要的部分
- **Content**:
  - 她长期被“才女”“爱情故事”“文学光环”覆盖
  - 但真正支撑其历史地位的是建筑实践、理论建构与学科奠基
  - 这份重新认识，不是纠偏趣闻，而是重写知识坐标

### Part 2: 她作为建筑师

#### Slide 03 - 建筑实践并不缺席

- **Layout**: 上方横向时间轴 + 下方三段作品节点
- **Title**: 从墓碑到车站，她的建筑实践有清晰轨迹
- **Visualization**: timeline
- **Content**:
  - 1929 梁启超墓碑：学成归国后的起点
  - 1929 石头楼与吉海铁路总站：现代性与民族象征并置
  - 1932—1940 北大、映秋院、西南联大、昆明自宅：在战乱中坚持建筑理想

#### Slide 04 - 作品现场：建筑不是抽象名词

- **Layout**: 2×2 图像矩阵 + 右侧注释栏
- **Title**: 四个现场，四种建筑回应
- **Content**:
  - 吉海铁路总站：地标性公共建筑的象征表达
  - 北大地质馆：现代主义转向
  - 映秋院：地方材料与民居经验
  - 昆明自宅：战时条件下的自我建造
- **Image**: jihai_station_new.png, pku_geology.png, yingqiu_yuan.png, kunming_site.png

#### Slide 05 - 国家尺度上的建筑参与

- **Layout**: 左图右文，纪念碑大图做视觉锚点
- **Title**: 她的建筑工作，最终进入国家记忆
- **Content**:
  - 八宝山革命公墓：主体格局设计
  - 人民英雄纪念碑：提出扩大碑座与双层台阶的关键修改
  - 纹样与尺度处理体现其对中国传统建筑语汇的理解
  - 她最终也安葬在自己参与设计的空间中
- **Image**: monument.png, babaoshan.png

### Part 3: 她作为理论奠基者

#### Slide 06 - 她不是“辅助者”，而是理论提出者

- **Layout**: 左侧论文图像 + 右侧纵向要点
- **Title**: 1932 年，她已在定义“中国建筑”
- **Visualization**: vertical_list
- **Content**:
  - 《论中国建筑之几个特征》是中国专业学者首次系统论述中国建筑
  - 她反驳了西方知识框架中的误读
  - 她提出了中国木构架体系的关键特征
  - 她为之后的中国建筑史叙述打下理论骨架
- **Image**: first_paper.png

#### Slide 07 - 学科、方法与远见

- **Layout**: 三列方法卡片 + 下方补充带
- **Title**: 她真正留下的，是一套方法
- **Visualization**: icon_grid
- **Content**:
  - 研究方法：测绘、考察、史料与类型分析并重
  - 学科建设：参与东北大学、清华大学建筑系建设
  - 理论前瞻：民居保护、现代住宅、普通人居住问题
  - 关键词：建筑意、营造则例、住宅概论、民间建筑保护
- **Image**: liang_lin_together.png

### Part 4: 她作为行动者

#### Slide 08 - 她如何穿过战火与病痛

- **Layout**: 左文右图，非卡片式长段落 + 引语强调
- **Title**: 她不是“被陪伴的人”，她本身就是行动者
- **Content**:
  - 实地考察古建筑，翻山涉水并非旁观
  - 战乱流亡与长期病痛，没有中止她的研究和写作
  - “我还有好多事要做呢”呈现的是职业使命感，而非姿态
  - 她把个人生命压进了中国建筑学的奠基时刻
- **Image**: lin_survey.png, lin_later.png

#### Slide 09 - 结尾

- **Layout**: 单图纪念式收束 + 中央引文
- **Title**: 墓碑上的七个字，已经足够准确
- **Subtitle**: 建筑师林徽因墓
- **Content**:
  - 重新认识她，不是从传奇回到八卦，而是从八卦回到专业
  - 她是中国第一代建筑学人中的关键建构者
  - 她留下的，不只是作品，更是中国如何理解自身建筑的一套语言
- **Image**: lin_tomb.png

---

## X. Speaker Notes Requirements

- **File naming**: Match SVG names (e.g., `01_封面.svg` → `notes/01_封面.md`)
- **Total duration**: ~12 minutes
- **Notes style**: 讲解型 + 展签式叙述，克制、准确、少煽情
- **Presentation purpose**: 纠偏认知 + 建立专业印象
- **Content includes**: 每页讲解要点、页间过渡、必要的史实强调

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Built-in icons use one library only: `tabler-outline`

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
