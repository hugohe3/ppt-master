# 裁云织月 草木成诗 — Design Spec

> 本文档为人类可读的设计叙事 — 包含设计动机、受众、风格、色彩选择与内容大纲。由下游角色（Executor）一次性读取以获得语境。
>
> 机器可读执行契约存放在 `spec_lock.md`（色彩 / 字体 / 图标 / 图片决策的简化短表）。Executor 在生成每一页 SVG 之前会重新读取 `spec_lock.md` 以抵抗长文档语境漂移。两份文件须保持同步，若出现冲突以 `spec_lock.md` 为准。

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | liziqi-plant-dye-colors |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 12 |
| **Design Style** | A) General Versatile — 东方文化叙事风 |
| **Target Audience** | 文化爱好者、设计师、传统美学学习者、博物馆/教育工作者 |
| **Use Case** | 文化分享会 / 设计师讲座 / 博物馆讲解 / 美学课程 |
| **Created Date** | 2026-04-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 60px，上下 50px |
| **Content Area** | 1160×620 |

---

## III. Visual Theme

### Theme Style

- **Style**: 东方植物染美学 · 文化叙事
- **Theme**: 浅色（宣纸米白底）
- **Tone**: 典雅 · 含蓄 · 诗意 · 温润 · 手作温度

### Color Scheme（取自文章中真实存在的传统色谱）

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background (宣纸白)** | `#F7F2E8` | 页面主背景，仿宣纸质感 |
| **Secondary bg (月白)** | `#EDE5D3` | 卡片/章节底/次级区域 |
| **Primary (雨过天青)** | `#6B9AAE` | 主视觉、章节主色、装饰线 |
| **Accent (黄栌黄)** | `#C99E62` | 副标题、强调色、副主视觉 |
| **Secondary accent (马兰青)** | `#6F8F75` | 渐变过渡、次要强调 |
| **Accent 2 (酡红)** | `#B04A5C` | 关键字、重点高亮（克制使用） |
| **Body text (茶墨)** | `#3A3530` | 正文主色 |
| **Secondary text (暮云灰)** | `#7A7068` | 注释、副文、引文 |
| **Tertiary text (淡墨)** | `#9B948B` | 页脚、元信息 |
| **Border/divider (淡米灰)** | `#D7CEB9` | 分隔线、描边、卡片边 |

### Gradient Scheme（使用 SVG 语法，无 rgba）

```xml
<!-- 战袍吊染渐变：黄栌 → 马兰青 -->
<linearGradient id="diaoyanGradient" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#C99E62"/>
  <stop offset="100%" stop-color="#6F8F75"/>
</linearGradient>

<!-- 章节扉页雨过天青渐变 -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#6B9AAE"/>
  <stop offset="100%" stop-color="#6F8F75"/>
</linearGradient>

<!-- 背景装饰（雨过天青晕染） -->
<radialGradient id="bgDecor" cx="85%" cy="15%" r="55%">
  <stop offset="0%" stop-color="#6B9AAE" stop-opacity="0.10"/>
  <stop offset="100%" stop-color="#6B9AAE" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Recommended preset**: P3（文化/艺术）

| Role | Chinese | English | Fallback |
| ---- | ------- | ------- | -------- |
| **Title** | KaiTi / STKaiti | Georgia | serif |
| **Body** | Microsoft YaHei / PingFang SC | Arial | sans-serif |
| **Code** | - | Consolas | Monaco |
| **Emphasis (引文/色名)** | KaiTi | Georgia | serif |

**Font stack**: `"KaiTi", "STKaiti", "Microsoft YaHei", "PingFang SC", Georgia, serif`

### Font Size Hierarchy

**Baseline**: Body font size = **22px**（中等密度，利于阅读古典长句）

| Purpose | Ratio | Size | Weight |
| ------- | ----- | ---- | ------ |
| Cover title | 3x | 66px | Bold |
| Chapter title | 2.3x | 50px | Bold |
| Content title | 1.6x | 36px | Bold |
| Subtitle | 1.2x | 26px | SemiBold |
| **Body content** | **1x** | **22px** | Regular |
| Annotation | 0.8x | 18px | Regular |
| Page number/date | 0.6x | 13px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 高 72px（页码 + 章节线 + 小装饰印章）
- **Content area**: 高 580px（主视觉区）
- **Footer area**: 高 40px（页脚 / 项目名 / 分隔线）

### Common Layout Modes

| Mode | 使用页 |
| ---- | ------ |
| **Single column centered** | 封面、引子、结语 |
| **Left-right split (5:5)** | 两色并列对照页 |
| **Left-right split (4:6)** | 图文混排（图左文右） |
| **Top-bottom split** | 历史时间线、流程页 |
| **Four column cards** | 染料植物分类 |

### Spacing Specification

| Element | Value |
| ------- | ----- |
| Card gap | 28px |
| Content block gap | 36px |
| Card padding | 26px |
| Card border radius | 12px |
| Icon-text gap | 12px |
| Single-row card height | 540px |
| Double-row card height | 275px each |

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-filled`（贝塞尔曲线圆润风格，契合植物/自然/东方美学）
- **Usage method**: `{{icon:tabler-filled/<name>}}`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 植物/叶 | `{{icon:tabler-filled/leaf}}` | 03, 09, 10 |
| 花朵 | `{{icon:tabler-filled/flower}}` | 09, 11 |
| 水滴/染料 | `{{icon:tabler-filled/droplet}}` | 03, 10 |
| 调色板 | `{{icon:tabler-filled/palette}}` | 05, 06, 07, 08 |
| 书籍 | `{{icon:tabler-filled/book}}` | 04, 12 |
| 历史 | `{{icon:tabler-filled/history}}` | 04 |
| 心/疗愈 | `{{icon:tabler-filled/heart}}` | 10 |
| 星光 | `{{icon:tabler-filled/sparkles}}` | 02, 12 |
| 画笔 | `{{icon:tabler-filled/brush}}` | 03, 11 |
| 月 | `{{icon:tabler-filled/moon}}` | 06, 08 |

> 最终可用名单由 Executor 以 `ls templates/icons/tabler-filled/ | grep <keyword>` 确认后锁定。

---

## VII. Visualization Reference List

| Visualization Type | Reference Template | Used In |
| ------------------ | ------------------ | ------- |
| `timeline` | `templates/charts/timeline.svg` | Slide 04（植物染历史脉络） |
| `numbered_steps` | `templates/charts/numbered_steps.svg` | Slide 10（植物染工艺步骤） |
| `icon_grid` | `templates/charts/icon_grid.svg` | Slide 09（染料植物分类） |

---

## VIII. Image Resource List

> 图片源自公众号原文，直接使用于演示（文化分享场景）。所有图片已存放于 `images/`。

| Filename | Dimensions | Ratio | Purpose | Type | Status |
| -------- | --------- | ----- | ------- | ---- | ------ |
| `640.png` | 1080×605 | 1.79 | 春晚开场视觉秀截图（李子柒） | Photography | Existing |
| `640_4.png` | 800×1291 | 0.62 | 李子柒战袍全身特写 | Photography | Existing |
| `640.jpg` | 900×1200 | 0.75 | 李子柒与黄荣华协作吊染 | Photography | Existing |
| `640_1.png` | 1080×279 | 3.87 | 唐·张萱《捣练图》局部 | Illustration | Existing |
| `640_5.png` | 1024×802 | 1.28 | 宋·汝窑天青釉圆洗 | Photography | Existing |
| `640_1.jpg` | 943×602 | 1.57 | 黄荣华染制雨过天青丝巾 | Photography | Existing |
| `640_6.png` | 1080×720 | 1.50 | 苍黄色意境图 | Photography | Existing |
| `640_7.png` | 1080×720 | 1.50 | 暮云灰意境图 | Photography | Existing |
| `640_8.png` | 400×265 | 1.51 | 天水碧色卡 | Photography | Existing |
| `640_10.png` | 800×600 | 1.33 | 黄荣华染制银红色丝巾 | Photography | Existing |
| `640_11.png` | 1080×684 | 1.58 | 《霸王别姬》酡色剧照 | Photography | Existing |
| `640_12.png` | 403×228 | 1.77 | 黛青色卡 | Photography | Existing |
| `640_13.png` | 1080×721 | 1.50 | 相思灰意境图 | Photography | Existing |
| `640_14.png` | 1080×699 | 1.55 | 染料植物（茜草/红花等） | Photography | Existing |
| `640_15.png` | 640×640 | 1.00 | 植物染操作过程 | Photography | Existing |
| `640_17.png` | 1080×1072 | 1.01 | 《梦华录》薛涛笺意象 | Photography | Existing |
| `640_18.png` | 974×731 | 1.33 | 薛涛笺染色成品 | Photography | Existing |

---

## IX. Content Outline

### Part 1：启幕 — 春晚惊艳

#### Slide 01 - Cover（封面）

- **Layout**: 单列居中 + 左侧竖排印章式标题 + 右侧配图
- **Title**: 裁云织月 · 草木成诗
- **Subtitle**: 揭秘李子柒春晚战袍背后，植物染成的 300 种中国传统色
- **Image**: `640.png`（春晚截图）右侧图 · 左侧竖排主标
- **Footer**: 源自 · 凤凰空间 | 2026.04

#### Slide 02 - 引子

- **Layout**: 左右分栏（图左文右，图 0.62 竖图放左侧居中）
- **Title**: 最动人的色彩
- **Image**: `640_4.png`（战袍特写，portrait 0.62）
- **Content**:
  - 核心观点："最动人的色彩不在潘通色卡里，而早已藏在山河草木之间"
  - 2025 春晚《迎福》视觉秀
  - 13 项非遗技艺集于一身
  - 黄青渐变 · 化身蝴蝶仙子

---

### Part 2：战袍解密

#### Slide 03 - 战袍解密：五方正色 × 手工吊染

- **Layout**: 上下分栏 · 上方两色色块并列 + 下方吊染工艺示意
- **Title**: 战袍解密 · 五方正色 × 手工吊染
- **Image**: `640.jpg`（李子柒与黄荣华协作吊染）右侧小图
- **Content**:
  - **黄色**：取材湖北神农架黄栌 → 代表**土地**
  - **青色**：取材江南初春马兰草 → 代表**春天**
  - **寓意**：中华土地 · 生生不息
  - **吊染工艺**：布料吊起 → 浸入染料 → 每 30 秒上拉 1 厘米 → 水墨晕染般渐变

#### Slide 04 - 植物染：千年染技的时间长河

- **Layout**: 上下分栏（顶部《捣练图》装饰条 + 下方 timeline）
- **Title**: 染色之术 · 远始轩辕之世
- **Visualization**: `timeline`
- **Image**: `640_1.png`（《捣练图》超宽图 3.87 作顶部装饰条）
- **Content**（5 个时间节点）：
  - **轩辕之世**：黄帝制玄冠黄裳，以草木之汁染成文彩
  - **西周**：设专职"染人"
  - **秦朝**：设"染色司"
  - **唐宋**：设"染院"
  - **明清**：设"蓝靛所"；《齐民要术》《天工开物》记载技艺

---

### Part 3：草木之色 — 染出自然万物

#### Slide 05 - 草木之色（上）：雨过天青 × 苍黄

- **Layout**: 左右分栏（5:5），两色并列
- **Title**: 草木之色（上）· 染出自然万物
- **Image**: `640_5.png`（汝窑圆洗）左 + `640_6.png`（苍黄）右
- **Content**:
  - **雨过天青 `#7AA4B6`** | 宋徽宗"雨过天青云破处，这般颜色做将来" | 土靛 95% + 黄芩 5% 套染
  - **苍黄 `#B29A55`** | 报春鸟 · 麛鹿之色 | 大黄+苏木，蓝矾媒染

#### Slide 06 - 草木之色（下）：暮云灰 × 天水碧

- **Layout**: 左右分栏（5:5），两色并列
- **Title**: 草木之色（下）· 日暮云彩与露染青碧
- **Image**: `640_7.png`（暮云灰）左 + `640_8.png`（天水碧）右
- **Content**:
  - **暮云灰 `#7D6E74`** | 柳永"千里烟波暮霭沉沉"，李清照"落日熔金，暮云合璧" | 苏木为染料，蓝矾+皂矾媒染
  - **天水碧 `#8FB09A`** | 南唐李煜妃 · 丝帛露宿染成 | 蓝靛染月白，极少黄色套染

---

### Part 4：诗意之色 — 还原文学意境

#### Slide 07 - 诗意之色（上）：银红 × 酡色

- **Layout**: 左右分栏（5:5），两色并列
- **Title**: 诗意之色（上）· 朝霞初染与饮酒颜酡
- **Image**: `640_10.png`（银红丝巾）左 + `640_11.png`（霸王别姬）右
- **Content**:
  - **银红 `#E49AA5`** | 浅绯色 · 朝霞初染 · 黛玉窗前霞影纱 | 红花+苏木+朱砂，明矾媒染
  - **酡色 `#C86868`** | "美人欲醉朱颜酡" · 贵妃醉酒 | 红蓝/苏木/茜草，明矾媒染

#### Slide 08 - 诗意之色（下）：黛青 × 相思灰

- **Layout**: 左右分栏（5:5），两色并列
- **Title**: 诗意之色（下）· 画眉深青与相思成灰
- **Image**: `640_12.png`（黛青）左 + `640_13.png`（相思灰）右
- **Content**:
  - **黛青 `#3D4A5A`** | 画眉之色 · 王实甫《西厢记》"眉黛青颦" | 蓝草提取青黛
  - **相思灰 `#A69E98`** | 李商隐"春心莫共花争发，一寸相思一寸灰" | 茶叶+石榴皮，皂矾媒染

---

### Part 5：草木疗愈 — 亲手染色

#### Slide 09 - 染料植物：四色取自草木

- **Layout**: 四列卡片（icon_grid）
- **Title**: 染料植物 · 四色皆取自草木
- **Visualization**: `icon_grid`
- **Image**: `640_14.png`（染料植物）作页眉装饰
- **Content**（4 色卡）：
  - **红**：茜草根 / 苏木茎 / 红花花瓣
  - **黄**：槐花花蕾 / 栀子果实 / 姜黄根茎
  - **蓝**：蓝草 / 鼠李叶茎
  - **黑**：胡桃果壳 / 板栗果壳

#### Slide 10 - 亲手植物染 · 自我疗愈的过程

- **Layout**: 左图右流程（4:6）
- **Title**: 亲手植物染 · 自我疗愈的过程
- **Visualization**: `numbered_steps`
- **Image**: `640_15.png`（染色过程）左
- **Content**（5 步）：
  1. **烧水** — 清水入锅煮沸
  2. **投料** — 植物染料浸入
  3. **熬制** — 1-2 小时滤出染液
  4. **浸染** — 布料入染液
  5. **定色** — 阳光晒暖固定色彩
  - 结语："紧张焦虑的情绪渐渐消失不见"

---

### Part 6：文脉与传承

#### Slide 11 - 薛涛笺 · 风雅可复刻

- **Layout**: 图左文右（4:6）
- **Title**: 薛涛笺 · 千年风雅可复刻
- **Image**: `640_17.png`（梦华录）左，`640_18.png` 作副图
- **Content**:
  - 唐代才女**薛涛**用**浣花溪水 + 木芙蓉皮 + 芙蓉花**捣汁
  - 染成**"芙蓉红"**信笺
  - 今日复刻：**苏木 + 明矾**效果最佳
  - "这是一扇通往东方美学的窗"

#### Slide 12 - 结语：色彩，文化记忆的承载者

- **Layout**: 单列居中 + 印章式收尾
- **Title**: 色彩不止于视觉 · 更是文化记忆的承载者
- **Content**:
  - 从天地造化的草木之色
  - 到流转千年的绢帛华章
  - **中国传统色彩** = 视觉体验 × 文化记忆
  - 参考：《国色 300 色》(黄荣华 著 · 江苏人民出版社)
- **Footer**: 完

---

## X. Speaker Notes Requirements

- **Total duration**: 约 12-15 分钟
- **Notes style**: 讲解式 · 典雅书面语 · 适量诗词引用
- **Purpose**: 分享（inspire + instruct）
- **File naming**: `notes/<slide_name>.md`（与 SVG 同名）
- **Content per slide**: 3-5 句关键讲稿 + 过渡衔接 + 节奏提示

---

## XI. Technical Constraints Reminder

### SVG 生成必须遵守：

1. viewBox: `0 0 1280 720`
2. 背景用 `<rect>`
3. 文本换行使用 `<tspan>`（`<foreignObject>` 禁用）
4. 透明度使用 `fill-opacity` / `stroke-opacity`；禁止 `rgba()`
5. 禁用：`clipPath`（image 除外）、`mask`、`<style>`、`class`、`foreignObject`
6. 禁用：`textPath`、`<animate*>`、`<script>`、`<symbol>+<use>`
7. `marker-start` / `marker-end` 条件允许（定义在 `<defs>`，箭头为三角形/菱形/圆）

### PPT 兼容规则：

- 禁止 `<g opacity="...">`（分组不透明度）；分别在子元素上设置
- 图片透明度使用遮罩矩形覆盖
- 仅内联样式；禁止外部 CSS 和 `@font-face`
- 图标一律使用 `tabler-filled/` 前缀（本项目锁定单一图标库）
