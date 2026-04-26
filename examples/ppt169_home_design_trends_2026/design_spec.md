# 2026家居趋势 - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 2026家居趋势：回归"人的尺度" |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 12 |
| **Design Style** | General Versatile (A) |
| **Target Audience** | 室内设计师、家居爱好者、装修计划者 |
| **Use Case** | 家居设计趋势分享/培训演示 |
| **Created Date** | 2026-04-22 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160×620 |

---

## III. Visual Theme

### Theme Style

- **Style**: General Versatile — 杂志质感的图文混排风格
- **Theme**: Dark theme（深色暖调底色）
- **Tone**: 高端、温暖、自然、人文、杂志感

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#1A1714` | 深棕暖黑底色 |
| **Secondary bg** | `#2A2520` | 卡片/区域背景 |
| **Primary** | `#C4A882` | 标题装饰、金色暖调 |
| **Accent** | `#D4956A` | 数据高亮、关键信息 |
| **Secondary accent** | `#8B7355` | 渐变过渡、次要装饰 |
| **Body text** | `#E8E0D4` | 主体文字（浅暖白） |
| **Secondary text** | `#B0A08E` | 注释说明 |
| **Tertiary text** | `#7A6E60` | 补充信息、页脚 |
| **Border/divider** | `#3D362E` | 卡片边框、分隔线 |
| **Success** | `#7BA37B` | 可持续/正向指标 |
| **Warning** | `#C06048` | 强调/警示 |

### Gradient Scheme

```xml
<!-- Title gradient -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#C4A882"/>
  <stop offset="100%" stop-color="#D4956A"/>
</linearGradient>

<!-- Background decorative gradient -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#C4A882" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#C4A882" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Editorial Display（杂志展示风）— 标题使用衬线字体传递高级感，正文使用无衬线保证阅读性。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `SimSun` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei"`, `"PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `SimSun` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Georgia, SimSun, serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `Georgia, SimSun, serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 22px（内容密度适中，每页 3-5 要点为主）

| Purpose | Ratio to body | Size | Weight |
| ------- | ------------- | ---- | ------ |
| Cover title | 3.6x | 80px | Bold |
| Chapter opener | 2.2x | 48px | Bold |
| Page title | 1.5x | 32px | Bold |
| Subtitle | 1.3x | 28px | SemiBold |
| **Body content** | **1x** | **22px** | Regular |
| Annotation / caption | 0.73x | 16px | Regular |
| Page number / footnote | 0.55x | 12px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 50-80px, 含页面标题及装饰元素
- **Content area**: 560-620px, 主要图文内容区域
- **Footer area**: 30-40px, 页码及来源信息

### Layout Pattern Library

本项目以图文并茂为核心，主要使用以下布局模式：

| Pattern | Used In |
| ------- | ------- |
| **Full-bleed + floating text** | P01 封面、P10 可持续奢华 |
| **Asymmetric split (4:6 / 3:7)** | P03 色彩、P05 材质、P06 纹理、P08 奶油风 |
| **Symmetric split (5:5)** | P04 色彩实践、P09 波西米亚&复古 |
| **Center-radiating** | P07 CMT体系 |
| **Single column centered** | P02 引言 |
| **Three-column cards** | P11 书籍推荐 |
| **Negative-space-driven** | P12 结语 |

### Spacing Specification

**Universal**:

| Element | Current Project |
| ------- | --------------- |
| Safe margin from canvas edge | 60px |
| Content block gap | 30px |
| Icon-text gap | 10px |

**Card-based layouts** (P07, P11):

| Element | Current Project |
| ------- | --------------- |
| Card gap | 24px |
| Card padding | 24px |
| Card border radius | 12px |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/tabler-filled/` — 圆润贝塞尔曲线，契合家居/生活方式温暖调性
- **Usage method**: Placeholder format `{{icon:tabler-filled/icon-name}}`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 色彩主题 | `{{icon:tabler-filled/palette}}` | P03, P04 |
| 材质主题 | `{{icon:tabler-filled/diamond}}` | P05 |
| 纹理主题 | `{{icon:tabler-filled/paint}}` | P06 |
| 家居 | `{{icon:tabler-filled/home}}` | P01, P02 |
| 太阳/光线 | `{{icon:tabler-filled/sun}}` | P05 |
| 树叶/自然 | `{{icon:tabler-filled/leaf}}` | P10 |
| 星星/亮点 | `{{icon:tabler-filled/sparkles}}` | P07 |
| 心/情感 | `{{icon:tabler-filled/heart}}` | P12 |
| 书籍 | `{{icon:tabler-filled/book}}` | P11 |
| 眼睛/视觉 | `{{icon:tabler-filled/eye}}` | P06 |
| 调整 | `{{icon:tabler-filled/adjustments}}` | P07 |
| 星标 | `{{icon:tabler-filled/star}}` | P08 |

---

## VII. Visualization Reference List

| Visualization Type | Reference Template | Used In |
| ------------------ | ------------------ | ------- |
| concentric_circles | `templates/charts/concentric_circles.svg` | P07 (CMT三层体系) |

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Intent | Type | Status |
| -------- | ---------- | ----- | ------- | ------ | ---- | ------ |
| intro_living.png | 1080x608 | 1.78 | P01 封面全屏背景 | Hero | Photography | Existing |
| space_overview.png | 800x540 | 1.48 | P02 引言配图 | Side-by-side | Photography | Existing |
| color_wheel.png | 559x823 | 0.68 | P03 色彩理论配图 | Side-by-side | Diagram | Existing |
| brown_cozy.png | 658x496 | 1.33 | P03 棕色舒适空间 | Accent | Photography | Existing |
| light_tone_room.png | 749x749 | 1.00 | P04 浅色调空间 | Side-by-side | Photography | Existing |
| saturated_room.png | 853x671 | 1.27 | P04 高饱和度空间 | Side-by-side | Photography | Existing |
| material_detail.png | 749x708 | 1.06 | P05 材质细节 | Side-by-side | Photography | Existing |
| light_material.png | 800x1000 | 0.80 | P05 光与材质 | Accent | Photography | Existing |
| texture_tactile.png | 615x398 | 1.55 | P06 触觉纹理 | Side-by-side | Photography | Existing |
| texture_visual.png | 519x569 | 0.91 | P06 视觉纹理 | Side-by-side | Photography | Existing |
| cmt_overview.png | 990x744 | 1.33 | P07 CMT体系总览 | Side-by-side | Photography | Existing |
| cmt_neutral_mix.png | 1023x636 | 1.61 | P07 中性色搭配 | Accent | Photography | Existing |
| dark_tone_luxury.png | 614x423 | 1.45 | P07 深色调奢华 | Accent | Photography | Existing |
| cream_style.png | 681x499 | 1.36 | P08 奶油风空间 | Side-by-side | Photography | Existing |
| bohemian_style.png | 615x924 | 0.67 | P09 波西米亚风 | Side-by-side | Photography | Existing |
| retro_style.png | 1080x608 | 1.78 | P09 怀旧复古风 | Side-by-side | Photography | Existing |
| sustainable_luxury.png | 417x500 | 0.83 | P10 可持续奢华 | Side-by-side | Photography | Existing |
| book_cover1.png | 1080x732 | 1.48 | P11 书籍封面 | Side-by-side | Photography | Existing |
| book_cover2.png | 1080x735 | 1.47 | P11 书籍封面背面 | Accent | Photography | Existing |
| book_inside1.png | 1080x741 | 1.46 | P11 书籍内页展示 | Accent | Photography | Existing |
| book_inside2.png | 1080x738 | 1.46 | P11 书籍内页展示 | Accent | Photography | Existing |
| book_display1.png | 1080x727 | 1.49 | P12 书籍展示 | Side-by-side | Photography | Existing |
| book_display2.png | 1080x743 | 1.45 | P12 书籍展示 | Accent | Photography | Existing |

---

## IX. Content Outline

### Part 1: 开篇

#### Slide 01 - 封面

- **Layout**: Full-bleed + floating text
- **Title**: 2026家居趋势
- **Subtitle**: 回归"人的尺度"，让色彩、材质与纹理塑造"空间的高级感"
- **Info**: 基于《空间的高级感》· 2026
- **Images**: `intro_living.png`（hero全屏，暗色渐变叠加层保证文字可读）

#### Slide 02 - 从"网红风"到"人的尺度"

- **Layout**: Single column centered + side-by-side image
- **Title**: 从"网红风"到"人的尺度"
- **Images**: `space_overview.png`
- **Content**:
  - 过去几年家居"网红风"迅速更迭
  - 2026年转向：从视觉符号堆砌回归人本关怀
  - 高级感 = 色彩 + 材质 + 纹理的精妙搭配
  - 有颜值，更有温度与情感

### Part 2: 三大底层元素

#### Slide 03 - 色彩：空间的情绪魔法师

- **Layout**: Asymmetric split (4:6) — 左图右文
- **Title**: 色彩：空间的"情绪魔法师"
- **Images**: `color_wheel.png`（左侧主图），`brown_cozy.png`（右下小图点缀）
- **Content**:
  - 色彩是空间的第一印象
  - 能改变视觉尺度、营造氛围
  - 暖色调 → 温柔包裹感；冷色调 → 开阔冷静
  - 不同色彩传递不同信号与心理反应

#### Slide 04 - 色彩实践：冷暖色调的空间效果

- **Layout**: Symmetric split (5:5) — 左右对比
- **Title**: 冷暖色调的空间效果对比
- **Images**: `light_tone_room.png`（左，浅色调），`saturated_room.png`（右，高饱和度）
- **Content**:
  - 左：浅色调 → 增大光线反射 → 空间显得宽敞
  - 右：高饱和度 → 房间紧凑小巧
  - 灰绿 → 平静专注；咖色 → 阳光包裹；跳色 → 个性活力

#### Slide 05 - 材质：触手可及的空间语言

- **Layout**: Asymmetric split (3:7) — 右侧大图
- **Title**: 材质：触手可及的空间语言
- **Images**: `material_detail.png`（主图），`light_material.png`（次图/accent）
- **Content**:
  - 材料是色彩搭配的物理基础
  - 原木地板 → 质朴温暖；手工编织 → 慵懒松弛
  - 光本身也是一种材质
  - 巧妙照明 + 色彩光影 → 不依赖昂贵材料也能实现高级感

#### Slide 06 - 纹理：赋予空间灵魂的细节

- **Layout**: Asymmetric split (5:5) — 左右并列
- **Title**: 纹理：赋予空间灵魂的细节
- **Images**: `texture_tactile.png`（左，触觉），`texture_visual.png`（右，视觉）
- **Content**:
  - 纹理 = 空间的"指纹"，独一无二的辨识度
  - 触觉纹理：羊毛地毯 → 柔软温暖；粗陶花瓶 → 凹凸肌理
  - 视觉纹理：壁纸图案 → 眼睛"感受"肌理

### Part 3: CMT 体系

#### Slide 07 - CMT 体系：色彩·材质·纹理的交响

- **Layout**: Center-radiating + accent images
- **Title**: CMT 体系：编织全方位感官体验
- **Visualization**: concentric_circles (CMT三层)
- **Images**: `cmt_overview.png`（主视觉），`cmt_neutral_mix.png`（中性色案例），`dark_tone_luxury.png`（深色调案例）
- **Content**:
  - CMT = Colour + Material + Texture
  - 物理层：光滑/粗糙、透明/不透明、高光/亚光
  - 心理层：手工/工业、简朴/奢华、安慰/刺激
  - 不是简单叠加，是系统性编织 — 如交响乐团的指挥

### Part 4: 2026 流行风格

#### Slide 08 - 奶油风进化论

- **Layout**: Asymmetric split (4:6) — 左文右图
- **Title**: 奶油风 2.0：从公式化到细腻表达
- **Images**: `cream_style.png`
- **Content**:
  - 奶油风正经历深刻"进化"
  - 不再只是"米白墙面+原木家具"的公式
  - 颜色基底：奶油色、燕麦色、米白色
  - 材质点睛：羊毛、亚麻、天然结疤原木、手工陶瓷
  - 真正的治愈空间 = 可触摸 + 可感知

#### Slide 09 - 波西米亚 & 怀旧复古

- **Layout**: Symmetric split (5:5) — 左右双风格
- **Title**: 自由灵魂与时间记忆
- **Images**: `bohemian_style.png`（左，波西米亚），`retro_style.png`（右，怀旧复古）
- **Content**:
  - 波西米亚：大胆色彩 + 自由织物 + 手工挂毯 → "有层次的不羁感"
  - 怀旧复古：风化木材 + 熟铁 + 柳编 → 带有使用痕迹的"时间感"
  - 共同特点：对真实与情感的渴望

#### Slide 10 - 可持续奢华

- **Layout**: Full-bleed + floating text（breathing页）
- **Title**: 可持续奢华：负责任的审美
- **Images**: `sustainable_luxury.png`
- **Content**:
  - 2026 奢华不再是昂贵材料的堆砌
  - 环保饰面、自然光照、再生木材、软木、黄麻纤维
  - 从"炫耀性消费"转向"负责任的审美"
  - 与世界和谐共存的生活哲学

### Part 5: 结语

#### Slide 11 - 一本书解锁空间高级感

- **Layout**: Three-column cards（书籍展示）
- **Title**: 《空间的高级感》— 可拆解、可复制、可验证的美学体系
- **Images**: `book_cover1.png`, `book_cover2.png`, `book_inside1.png`, `book_inside2.png`
- **Content**:
  - 作者：宋文雯（清华大学色彩研究所常务副所长）
  - 创新引入 CMF → CMT 体系
  - 色彩篇 + 材料篇 + 纹理篇 + 综合篇
  - 适合：设计师专业提升 / 装修业主自学

#### Slide 12 - 结语

- **Layout**: Negative-space-driven + accent image
- **Title**: 让家回归"人的尺度"
- **Images**: `book_display1.png`, `book_display2.png`
- **Content**:
  - 高级感的本质：色彩、材质、纹理的精妙共鸣
  - 有颜值，更有温度与情感
  - 参考来源：《空间的高级感——设计师的色彩、材质、纹理搭配指南》

---

## X. Speaker Notes Requirements

Generate corresponding speaker note files for each page, saved to the `notes/` directory:

- **File naming**: Match SVG names, e.g., `01_cover.md`
- **Content includes**: Script key points, timing cues, transition phrases
- **Style**: 自然对话式（conversational），适合设计趋势分享场景
- **Duration**: 约 15-20 分钟总时长
- **Purpose**: Inform + Inspire

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set opacity on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
