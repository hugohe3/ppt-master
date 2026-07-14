# 藏拙 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | cangzhuo (《男人最顶级的城府：藏拙》) |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 14 |
| **Design Style** | A) 通用大众 + 新中式水墨留白 |
| **Target Audience** | 30+ 男性职场人 / 自我修养读者 / 公众号转发场景 |
| **Use Case** | 朋友圈传播、读书分享、个人成长课件 |
| **Created Date** | 2026-05-16 |

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

- **Style**: 新中式 / 水墨留白 / 文人气质
- **Theme**: Light theme（宣纸底）
- **Tone**: 静、克制、文气、东方哲思

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F5F1E8` | 宣纸米白，全页底色 |
| **Secondary bg** | `#EFEAD9` | 副底色 / 卡片背景（比主底色略深） |
| **Primary** | `#1A1A1A` | 墨黑，标题、主体文字、深色块 |
| **Accent** | `#A52A2A` | 朱砂，重点字、印章、关键论点强调 |
| **Body text** | `#1A1A1A` | 正文 |
| **Secondary text** | `#5C5852` | 副文、引文出处 |
| **Tertiary text** | `#8B8680` | 远山灰，辅助元素、页码、注释 |
| **Border/divider** | `#C8C0AE` | 分割线、印章描边 |

### AI Image Strategy

- **Image Rendering**: `ink-notes`
- **Image Palette**: `mono-ink`

---

## IV. Typography System

### Font Plan

**Typography direction**: 楷书标题 + 现代黑体正文（Kai × Hei 对比轴）

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `KaiTi` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `KaiTi` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `KaiTi, Georgia, serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `KaiTi, Georgia, serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body = 24px（轻松节奏，传播阅读优先）

| Purpose | Ratio | Size |
| ------- | ----- | ---- |
| Cover title | 3.3x | 80px |
| Chapter / section opener | 2.5x | 60px |
| Page title | 1.5–1.8x | 36–44px |
| Hero number / 引文大字 | 2x | 48px |
| Subtitle | 1.3x | 32px |
| **Body** | **1x** | **24px** |
| Annotation / caption | 0.75x | 18px |
| Page number / footer | 0.6x | 14px |

---

## V. Layout Principles

### Page Structure

- **Header area**: 60–80px（页眉印章或章节号，可省略）
- **Content area**: 500–560px（主内容）
- **Footer area**: 40px（页码 / 落款）

### Layout Pattern Library (combine or break as content demands)

| Pattern | Use in this deck |
| ------- | ----------------- |
| Single column centered | 封面 / 引子 / 结语 |
| Symmetric split (5:5) | 藏拙 vs 消极避世 对照 |
| Asymmetric split (3:7 / 2:8) | 引言 + 释义 |
| Three/four column cards | 顶级城府的三件事 |
| Full-bleed + floating text | breathing 页（封面、引子、章节转场） |
| Negative-space-driven | 单独印证页（潜龙勿用 / 木秀于林） |
| Figure-text overlap | 韩信典故页 |

### Spacing Specification

**Universal**:

| Element | Value |
| ------- | ----- |
| Safe margin | 左右 60px / 上下 50px |
| Content block gap | 32px |
| Icon-text gap | 12px |

**Card-based**:

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Card padding | 28px |
| Card border radius | 8px |
| Three-column card width | 360px |
| Four-column card width | 268px |

**Non-card**: 行距 1.6×；breathing 页正文宽度 720–900px 居中，依信息体量自由收放。

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `tabler-outline`（stroke_width = 1.5，线性轻盈，与水墨留白调性契合）
- **Usage method**: SVG 占位符 `<use data-icon="tabler-outline/<name>" stroke-width="1.5"/>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 章节符号 / 引文 | `tabler-outline/quote` | P02, P05, P10 |
| 不亮牌 / 隐藏 | `tabler-outline/eye-off` | P04, P07 |
| 锋芒 / 武器 | `tabler-outline/sword` | P06, P09 |
| 盾 / 防御 | `tabler-outline/shield` | P09 |
| 时间 / 等待 | `tabler-outline/hourglass` | P10, P12 |
| 山 / 沉稳 | `tabler-outline/mountain` | P12 |
| 心 / 情绪 | `tabler-outline/heart` | P13 |
| 圆点 / 列表 | `tabler-outline/point-filled` | 通用 |

---

## VII. Visualization Reference List

> 本篇为人文哲思散文，数据可视化页很少。仅 2 页采用 charts 模板作为结构骨架；其余页面均为自由排版。

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P11 | pros_cons_chart | `templates/charts/pros_cons_chart.svg` | "Pick for bilateral pros/cons list, 2-5 items per side. Skip for full feature comparison (use comparison_table) or numeric A/B mirror data (u…)" | 藏拙 vs 消极避世 四维对照 |
| P13 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendation…" | 藏住四件事 → 养出四种力（核心输出页） |

**Runners-up considered** (fewer than 3 viz pages, runners-up listed per page):

- `comparison_table` | rejected for P11: 仅四个维度、两栏对比，pros_cons 视觉更利落；comparison_table 适合多列多行密集矩阵
- `principles_grid` (不在库内) → `vertical_pillars` | rejected for P13: 四组"藏 → 养"是同质化条目，vertical_list 的"序号 + 标题 + 说明"格式更贴合
- `numbered_steps` | rejected for P13: 该页是平行四条原则，不是顺序步骤；步骤化会误导读者以为有先后

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_bg.png | 1280×720 | 1.78 | 封面背景：水墨远山留白 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | Distant misty mountain range in ink wash style, vast empty paper sky on top three-fifths reserved for vertical title, sparse brushstrokes, a single tiny boatman silhouette on a lake at lower right; deep silence and restraint | none | hero_page |
| yinzi_bg.png | 1280×720 | 1.78 | 引子背景：藏锋 atmosphere | Background | #12 faded image as backdrop with oversized overlay text + #30 flat semi-transparent rectangle overlay | ai | Pending | Half-sheathed brushstroke or ink-trail receding into white paper, calm left two-thirds reserved for floating quote text, single faint seal mark at lower right corner; suggests withdrawn force without revealing it | none | hero_page |
| hanxin_bridge.png | 1280×720 | 1.78 | 韩信胯下之辱场景 | Illustration | #4 right image bleeding off the canvas edge + #29 two-stop scrim | ai | Pending | Lone scholar-warrior figure standing quietly under a stone bridge in ancient market street, ink-wash brushwork, no facial detail, body language steady not humbled, crowd as faint ink dots in background; restraint as strength | none | local |
| qianlong_pool.png | 1280×720 | 1.78 | 潜龙勿用 atmosphere | Background | #1 full-bleed background with floating title + #28 radial gradient vignette | ai | Pending | Deep still pool surrounded by craggy ink-wash cliffs, suggestion of a coiled dragon shape barely visible beneath the water surface as faint darker ink swirls, mist rising; latent power waiting for time | none | hero_page |
| zengguofan_lamp.png | 1280×720 | 1.78 | 曾国藩 笨功夫 atmosphere | Illustration | #2 left-third image + right text body + #21 rounded rectangle crop | ai | Pending | Single oil lamp on a wooden desk with stacked ancient books and an open ink-stone, no human figure, view through a paper window showing pre-dawn darkness; persistence in solitude | none | local |
| closing_mountain.png | 1280×720 | 1.78 | 结语：山外有山 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | Layered ink-wash mountain ridges receding into distance, foreground sharp dark mountain, middle and far ridges progressively lighter into mist, vast empty sky reserved for closing quote; depth and patience | none | hero_page |

> **Image-as-canvas (#38–#46) coverage note**: 本篇为文学哲思散文，无 KPI / 流程节点 / 仪表盘 / 网络架构图等需"在图上叠加结构化信息层"的页面；所有 image-bearing 页面均为氛围烘托型（hero / atmosphere），原生 SVG 文字层独立承担信息，无需 #38–46 family。这是该 deck 内容性质决定的合理偏移。

---

## IX. Content Outline

### Part 1: 开篇

#### Slide 01 — Cover

- **Layout**: Full-bleed background image + 居中竖排标题 + 副标题 + 落款（page_rhythm: anchor）
- **Title**: 男人最顶级的城府：藏拙
- **Subtitle**: 沉得住，藏得住，等得起
- **Info**: 谋事论 · 论尽成事逻辑

#### Slide 02 — 引子

- **Layout**: Full-bleed faded backdrop + 中央大字引言（page_rhythm: breathing）
- **Title**: （无标题，引文即主体）
- **Content**: "男人太早亮牌，就是给别人递刀。"

### Part 2: 看见问题

#### Slide 03 — 烧烤摊故事

- **Layout**: 左右对照（5:5 split）+ 底部一行总结（page_rhythm: dense）
- **Title**: 烧烤摊上的两种人
- **Content**:
  - 左：刚升职的人——开口讲资源、人脉、项目；旁人嘴上恭维、眼里盘算
  - 右：另一个男人——话不多，只问关键问题，散场时把每人底牌看了七八分
  - 底部："世上的局，很多不是输在没本事，而是输在太早让别人知道你有什么本事"

#### Slide 04 — 什么是藏拙

- **Layout**: 三列卡片（page_rhythm: dense）
- **Title**: 藏拙 ≠ 装傻 ≠ 认怂
- **Content**: 三个核心动作
  - 把锋芒收起来
  - 把欲望压下去
  - 把自己从别人的视线中心挪开

#### Slide 05 — 木秀于林

- **Layout**: Full-bleed + 居中大字引文（page_rhythm: breathing）
- **Title**: （引文页，无小标题）
- **Content**: "木秀于林，风必摧之"——《增广贤文》
- 解读：实力没强到能自保时，锋芒就是风险

### Part 3: 常见错误

#### Slide 06 — 年轻人最容易犯的错

- **Layout**: 2x2 grid 卡片 + 底部一句话（page_rhythm: dense）
- **Title**: 把"被看见"误以为"被尊重"
- **Content**:
  - 刚有点成绩，就想让所有人知道
  - 刚有点资源，就忍不住展示
  - 刚看透一点人性，就急着戳破
  - 底部：明处的人没有遮挡，所有试探、嫉妒、借力、拆台，都会先冲他来

#### Slide 07 — 会藏拙的人怎么做

- **Layout**: 三列对照 + 底部引言（page_rhythm: dense）
- **Title**: 不在小场面里浪费锋芒
- **Content**:
  - 饭局上 — 不抢话
  - 会议里 — 不乱表态
  - 人群中 — 不急着显摆关系
  - 底部："沉默不是空白，是在收集信息；退让不是无能，是不把弹药浪费在无价值的目标上"

### Part 4: 历史佐证

#### Slide 08 — 韩信胯下之辱

- **Layout**: 右侧出血图 + 左侧文字（page_rhythm: anchor）
- **Title**: 韩信胯下之辱
- **Content**:
  - 不是为了歌颂屈辱
  - 而是他没有把人生押在一场街头冲突里
  - 小局赢了，可能只是出口气；大局赢了，才有翻身的资格

#### Slide 09 — 藏拙的高明

- **Layout**: 四行表格（page_rhythm: dense）
- **Title**: 把"拙"变成盾
- **Content**: 表现 × 旁人反应 四行对照
  - 太聪明 → 防他
  - 太强势 → 躲他
  - 太急切 → 资源方压价
  - 太想赢 → 对手拖他入局
  - 底部：适当慢一点、钝一点、淡一点，反而能减少无谓的消耗

#### Slide 10 — 潜龙勿用

- **Layout**: Full-bleed + 居中引文（page_rhythm: breathing）
- **Title**: （引文页）
- **Content**: "潜龙勿用"——《易经》
- 解读：龙在深渊时，不是没有力量，而是时机未到

### Part 5: 辨明区分

#### Slide 11 — 藏拙 ≠ 消极避世

- **Layout**: pros_cons_chart 双列对照（page_rhythm: dense）
- **Title**: 藏拙 ≠ 消极避世
- **Visualization**: pros_cons_chart
- **Content**: 四维对照
  - 动机：消极=怕输 vs 藏拙=为赢
  - 状态：消极=越躲越废 vs 藏拙=越藏越厚
  - 沉默：消极=借口 vs 藏拙=蓄力
  - 内心：消极=委屈 vs 藏拙=布局

#### Slide 12 — 曾国藩典范

- **Layout**: 左图 + 右文字（page_rhythm: anchor）
- **Title**: 曾国藩：笨功夫、慢功夫、深功夫
- **Content**:
  - 早年并不以聪明见长，甚至常被认为迟钝
  - 靠的是：笨功夫 / 慢功夫 / 深功夫
  - 不争一时快，不贪一寸巧
  - 拙到深处，是定力；定力够了，局势才会慢慢站到他这边

### Part 6: 核心输出

#### Slide 13 — 藏住四件事 养出四种力

- **Layout**: vertical_list 四条编号原则（page_rhythm: dense）
- **Title**: 藏住四件事，养出四种力
- **Visualization**: vertical_list
- **Content**:
  - 01 藏住情绪 → 不被几句话激怒
  - 02 藏住野心 → 不被人提前设防
  - 03 藏住实力 → 不被人过早消耗
  - 04 藏住判断 → 不在局势未明时被迫站队

#### Slide 14 — 结语

- **Layout**: Full-bleed 远山 + 中央三行短语 + 落款（page_rhythm: anchor）
- **Title**: 顶级城府 = 压表现欲 × 稳胜负心 × 延迟满足
- **Content**:
  - 沉得住，才不怕暂时被低估
  - 藏得住，才不怕一时没掌声
  - 等得起，才有资格在该出手的时刻，让结果替自己说话

---

## X. Speaker Notes Requirements

- 文件命名：`notes/01_cover.md` … `notes/14_closing.md`
- 风格：conversational（散文气，避免商务术语）
- 目的：inspire（传播 / 共鸣 / 触发反思）
- 单页时长：约 30–45 秒口述

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. 背景用 `<rect>` 元素铺底色
3. 文本换行用 `<tspan>`（禁止 `<foreignObject>`）
4. 透明度默认用 `fill-opacity` / `stroke-opacity`；`rgba()` 保持转换兼容
5. 禁止：`mask` / `<style>` / `class` / `foreignObject` / `textPath` / `animate*` / `script`
6. 文本中的字符直接写 Unicode（— · → " " ©），禁止 HTML 实体（`&nbsp;` `&mdash;` 等）；XML 保留字按需转义（`&amp;` `&lt;`）

### PPT Compatibility Rules:

- opacity 默认写在子元素上；`<g opacity="...">` 可转换但会产生近似保真 warning
- 图片半透明用覆盖矩形（`<rect fill="bg-color" opacity="0.x"/>`）
- 仅允许行内样式；禁止外部 CSS 和 `@font-face`
