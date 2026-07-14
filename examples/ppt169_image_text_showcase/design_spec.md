# Image-Text Showcase — Design Spec

> Human-readable design narrative. Machine-readable contract: `spec_lock.md`. On divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Image-Text Showcase |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 20 |
| **Design Style** | A) General Versatile + editorial-showcase |
| **Target Audience** | 设计师、PPT制作者、AI工具用户 |
| **Use Case** | 图文结合能力展示 / 视觉样例集 |
| **Created Date** | 2026-05-15 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160×620 (x=60, y=50) |

---

## III. Visual Theme

### Theme Style

- **Style**: A) General Versatile + editorial-showcase
- **Theme**: 每页独立主题（dark/light 随各页 rendering 而异）
- **Tone**: 多元视觉语言并置；每页是一个独立的视觉风格样本

### Color Scheme

> 每页颜色服从该页 rendering × palette 组合，以下为 SVG 结构色（非图像色）

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0F1117` | 默认深底（各页可覆盖） |
| **Secondary bg** | `#1A1D2E` | 卡片/区块底色 |
| **Primary** | `#7C6FF7` | 主调紫蓝 |
| **Accent** | `#F5A623` | 金橙强调 |
| **Secondary accent** | `#4ECDC4` | 青绿对比 |
| **Body text** | `#E8E8F0` | 正文浅灰白 |
| **Secondary text** | `#9090A0` | 说明文字 |
| **Tertiary text** | `#5A5A72` | 页码/补充 |
| **Border/divider** | `#2A2D3E` | 边框分割线 |
| **Success** | `#4CAF50` | 正向指标 |
| **Warning** | `#EF5350` | 警示标记 |

### AI Image Strategy

每页图像独立指定 rendering × palette（见 §VIII 及 §IX），非统一锁定。

---

## IV. Typography System

**Typography direction**: contrast — serif title × sans body

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:
- Title: `Georgia, "Microsoft YaHei", serif`
- Body: `Arial, "Microsoft YaHei", "PingFang SC", sans-serif`
- Emphasis: `Georgia, "Microsoft YaHei", serif`
- Code: `Consolas, "Courier New", monospace`

**Baseline**: Body = 20px

| Purpose | Ratio | @ 20px |
| ------- | ----- | ------ |
| Cover title | 3-5x | 60-100px |
| Chapter opener | 2-2.5x | 40-50px |
| Page title | 1.5-2x | 30-40px |
| Subtitle | 1.2-1.5x | 24-30px |
| **Body** | **1x** | **20px** |
| Annotation | 0.7-0.85x | 14-17px |
| Page number | 0.5-0.65x | 10-13px |

---

## V. Layout Principles

### Page Structure

- **Header area**: y=0~80px，页面标题或留白
- **Content area**: y=80~670px，主内容区
- **Footer area**: y=670~720px，页码/标注

### Layout Pattern Library

本项目每页使用不同布局，详见 §IX Content Outline。

### Spacing Specification

| Element | Value |
| ------- | ----- |
| Safe margin | 60px (left/right), 50px (top/bottom) |
| Content block gap | 32px |
| Card gap | 24px |
| Card padding | 28px |
| Card border radius | 12px |

---

## VI. Icon Usage Specification

**Library**: `tabler-outline`, stroke-width `2`

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 图文结合 | `tabler-outline/layout-collage` | P02 目录 |
| 全出血布局 | `tabler-outline/frame` | P02 目录 |
| 左右分栏 | `tabler-outline/layout-columns` | P02 目录 |
| 图文叠压 | `tabler-outline/layers-intersect` | P02 目录 |
| 卡片网格 | `tabler-outline/layout-grid` | P02 目录 |
| 图片 | `tabler-outline/photo` | P02 目录 |
| 调色板 | `tabler-outline/palette` | P02 目录 |
| 画板 | `tabler-outline/artboard` | P02 目录 |

---

## VII. Visualization Reference List

Catalog read: 71 templates

本项目以图文布局展示为主，无数据图表页，不使用 charts 模板库。

No-template-match: all pages use custom layouts designed to demonstrate image-text composition patterns.

---

## VIII. Image Resource List

每页一张AI图，rendering × palette 各页独立。

| Filename | Dimensions | Ratio | Purpose | Type | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | ---------- | ----- | ------- | ---- | ----------- | ------ | --------- | ----------- | --------- |
| p01_cover.png | 1280×720 | 1.78 | 封面全出血背景 | Background | ai | Pending | Futuristic frosted glass panels layered over deep space; calm center reserved for title overlay; subtle light refractions at edges | none | hero_page |
| p03_left_img.png | 427×620 | 0.69 | 左1/3竖版图 | Photography | ai | Pending | Professional editorial portrait: diverse creative team collaborating, modern studio, natural sidelighting, shallow depth of field | none | local |
| p04_right_img.png | 800×720 | 1.11 | 右侧出血大图 | Illustration | ai | Pending | Bold flat vector composition: abstract geometric cityscape with sharp color blocks; right edge bleeds off canvas | none | local |
| p05_top_img.png | 1280×320 | 4.0 | 顶部全幅横图 | Background | ai | Pending | Soft watercolor wash: mountain lake at dawn, wide panoramic, muted pastel reflections, top-heavy composition leaving bottom clear | none | local |
| p06_bottom_img.png | 1280×360 | 3.56 | 底部全幅图 | Illustration | ai | Pending | Hand-drawn sketch: cozy reading corner, warm pencil lines, pastel color fills, bottom-weighted scene with open sky at top | none | local |
| p07_z_img1.png | 560×200 | 2.8 | Z型第一段图 | Illustration | ai | Pending | Isometric 3D tech object: server rack or CPU chip, clean shadows, top-left anchor composition | none | local |
| p07_z_img2.png | 560×200 | 2.8 | Z型第三段图 | Illustration | ai | Pending | Isometric 3D network diagram: connected nodes and cables, same isometric angle as img1 | none | local |
| p08_grid_center.png | 400×400 | 1.0 | 九宫格中心图 | Illustration | ai | Pending | Blueprint-style technical schematic: circuit board with grid lines, monospace annotations, monochrome blue-on-dark | none | local |
| p09_circle_img.png | 400×400 | 1.0 | 圆形中心图 | Illustration | ai | Pending | Digital dashboard interface fragment: glowing circular gauge, data rings, dark background, high-tech UI aesthetic | none | local |
| p10_bg_texture.png | 1280×720 | 1.78 | 全幅底纹背景 | Background | ai | Pending | Pixel art cityscape at night: 8-bit buildings and neon signs tiled across the full canvas, vibrant saturated colors | none | hero_page |
| p11_papercut.png | 1280×720 | 1.78 | 剪纸分层背景 | Illustration | ai | Pending | Layered paper-cut landscape: 4 depth layers of mountains and trees, each layer a different green-earth tone, soft cast shadows | none | hero_page |
| p12_poster_img.png | 256×720 | 0.36 | 竖版杂志窄图 | Illustration | ai | Pending | Mid-century vintage poster fragment: bold geometric shapes, halftone texture, limited 3-color palette, vertical composition | none | local |
| p13_diagonal_img.png | 700×420 | 1.67 | 对角线上半图 | Illustration | ai | Pending | Fantasy animation style: dreamy forest scene with soft glowing particles, warm amber light filtering through canopy, Ghibli-inspired atmosphere | none | local |
| p14_fade_bg.png | 1280×720 | 1.78 | 褪色底图 | Background | ai | Pending | Ink wash painting: abstract brushstrokes suggesting mountains and mist, desaturated earthy tones, large central negative space | none | hero_page |
| p15_bottom_img.png | 1280×360 | 3.56 | 下半幅图 | Illustration | ai | Pending | Flat design scene: modern office workspace seen from above, geometric furniture shapes, jewel-tone color palette, clean isometric-free flat view | none | local |
| p16_center_img.png | 480×480 | 1.0 | 中心圆形图 | Illustration | ai | Pending | Minimalist swiss-style graphic: single bold geometric form (circle or square) centered on white field, aggressive negative space, Helvetica-era precision | none | local |
| p17_strip_img.png | 1280×240 | 5.33 | 横贯中部窄条图 | Illustration | ai | Pending | Screen-print style banner: bold halftone pattern, limited 2-color duotone treatment, horizontal rhythm of repeated graphic motifs | none | local |
| p18_polygon_img.png | 600×500 | 1.2 | 不规则多边形图 | Illustration | ai | Pending | Organic nature illustration: lush tropical leaves and botanical elements arranged in a loose hexagonal cluster, earthy warm greens | none | local |
| p19_collage1.png | 380×320 | 1.19 | 蒙太奇图1 | Photography | ai | Pending | Editorial magazine photo: urban architecture detail, dramatic shadow play, high contrast, cropped unconventionally | none | local |
| p19_collage2.png | 380×320 | 1.19 | 蒙太奇图2 | Photography | ai | Pending | Editorial magazine photo: close-up texture surface — fabric or concrete, abstract pattern, monochromatic | none | local |
| p19_collage3.png | 460×320 | 1.44 | 蒙太奇图3（宽） | Photography | ai | Pending | Editorial magazine photo: motion blur street scene, long exposure light trails, cool blue atmosphere | none | local |
| p20_closing.png | 1280×720 | 1.78 | 结尾背景 | Background | ai | Pending | Chalk drawing on blackboard: simple constellation of dots and hand-drawn lines forming a subtle geometric pattern, warm white chalk marks on dark green surface | none | hero_page |

---

## IX. Content Outline

### Part 1: 封面与导航

#### Slide 01 — 封面

- **Layout**: 全出血背景图 + 居中悬浮标题块
- **Rendering × Palette**: `glassmorphism` × `dark-cinematic`
- **Image**: p01_cover.png (hero_page，全出血)
- **Title**: 图文结合
- **Subtitle**: 20种视觉语言的并置实验
- **Info**: PPT Master · 2026

#### Slide 02 — 目录

- **Layout**: 左侧深色色块 + 右侧编号列表（无图）
- **Rendering × Palette**: 无图，使用项目主配色
- **Content**: 列出20页风格速览，每条一行

### Part 2: 图文组合样本

#### Slide 03 — 左1/3竖图 + 右文字主体

- **Layout**: 左侧竖版图 width=427px，右侧文字区 width=733px
- **Rendering × Palette**: `corporate-photo` × `cool-corporate`
- **Image**: p03_left_img.png
- **Title**: 编辑摄影 × 专业蓝
- **Content**: 竖版人物图左置，文字在右大面积展开；图文比例约3:7，适合以文字为主的叙述型页面

#### Slide 04 — 右图左文，图出血至右边缘

- **Layout**: 左侧文字区 width=440px，右侧图出血至边缘 width=840px
- **Rendering × Palette**: `vector-illustration` × `frost-ice`
- **Image**: p04_right_img.png
- **Title**: 矢量插画 × 冰霜白
- **Content**: 扁平矢量图占据右侧并出血，文字在左浮动；大图小字制造张力

#### Slide 05 — 顶部全幅图 + 底部三栏文字

- **Layout**: 上半 height=360px 全幅图，下半 height=310px 三栏等宽文字
- **Rendering × Palette**: `watercolor` × `warm-earth`
- **Image**: p05_top_img.png
- **Title**: 水彩渲染 × 暖土色
- **Content**: 宽幅水彩图压顶，下方三栏简短文字如图注般排列

#### Slide 06 — 底部全幅图 + 顶部标题 + 中段文字

- **Layout**: 顶部 height=120px 标题区，中段 height=200px 文字，底部 height=360px 全幅图
- **Rendering × Palette**: `sketch-notes` × `macaron`
- **Image**: p06_bottom_img.png
- **Title**: 手绘速写 × 马卡龙
- **Content**: 图在底部如舞台布景，文字浮于上方；温暖手绘感

#### Slide 07 — Z型图文交替三段蛇形

- **Layout**: 三行交替：图左文右 → 文左图右 → 图左文右，每段 height≈190px
- **Rendering × Palette**: `3d-isometric` × `tech-neon`
- **Image**: p07_z_img1.png, p07_z_img2.png
- **Title**: 等距3D × 霓虹科技
- **Content**: Z型视线引导；两张等距3D图与三段文字交织排列

#### Slide 08 — 九宫格图文混排网格

- **Layout**: 3×3 grid，中心格放图，其余8格放文字/色块
- **Rendering × Palette**: `blueprint` × `editorial-classic`
- **Image**: p08_grid_center.png
- **Title**: 蓝图技术 × 编辑经典
- **Content**: 电路板图居中，周围8格填充标题、说明、标注等文字元素

#### Slide 09 — 圆形图像居中 + 四角文字放射

- **Layout**: 圆形裁切图居中 diameter=380px，四个角落各一文字块
- **Rendering × Palette**: `digital-dashboard` × `mono-ink`
- **Image**: p09_circle_img.png (clipPath圆形裁切)
- **Title**: 数字仪表 × 墨黑单色
- **Content**: 高科技仪表盘图像圆形展示，四角文字如标注向外发散

#### Slide 10 — 图作全幅底纹 + 文字信息密铺

- **Layout**: 图全幅平铺为背景，深色遮罩overlay，文字分四区域密铺
- **Rendering × Palette**: `pixel-art` × `vivid-launch`
- **Image**: p10_bg_texture.png (hero_page)
- **Title**: 像素复古 × 活力发射
- **Content**: 8-bit像素背景上铺设四块信息卡片，霓虹文字与像素感呼应

#### Slide 11 — 剪纸分层叠叠 + 文字嵌入各层

- **Layout**: 图全出血为剪纸背景，文字块嵌入各剪纸层之间
- **Rendering × Palette**: `paper-cut` × `nature-organic`
- **Image**: p11_papercut.png (hero_page)
- **Title**: 剪纸艺术 × 自然有机
- **Content**: 多层剪纸山景，文字分布于不同景深层，模拟纸层嵌字

#### Slide 12 — 竖版杂志：窄图占左20% + 大标题横排

- **Layout**: 左侧竖条图 width=256px，右侧大标题 + 正文占余下1024px
- **Rendering × Palette**: `vintage-poster` × `duotone`
- **Image**: p12_poster_img.png
- **Title**: 复古海报 × 双色调
- **Content**: 窄竖图如书脊般立于左缘，右侧大号字排版如杂志封面

#### Slide 13 — 对角线分割：左上图，右下文

- **Layout**: 对角线切割，左上三角区域放图，右下三角区域放文字
- **Rendering × Palette**: `fantasy-animation` × `sunset-gradient`
- **Image**: p13_diagonal_img.png
- **Title**: 奇幻动画 × 落日渐变
- **Content**: 吉卜力风森林图占左上，文字在右下三角内排列；对角张力

#### Slide 14 — 图片褪色为底色 + 大字叠压

- **Layout**: 图全出血低饱和度处理，大字（font-size≈80px）直接叠压其上
- **Rendering × Palette**: `ink-notes` × `earthy-dusty`
- **Image**: p14_fade_bg.png (hero_page，低饱和底图)
- **Title**: 水墨笔记 × 尘土大地
- **Content**: 水墨山水褪为底色，单行超大字叠压；图为纹理，字为主角

#### Slide 15 — 上下各半：上段文字，下段图

- **Layout**: 上半 height=340px 文字区，下半 height=340px 全幅图（有细分割线）
- **Rendering × Palette**: `flat` × `jewel-tone`
- **Image**: p15_bottom_img.png
- **Title**: 扁平设计 × 宝石色调
- **Content**: 上方大标题+正文，下方扁平俯视图；图文各占半幅，对等对话

#### Slide 16 — 中心大图 + 环绕一圈文字标注

- **Layout**: 正方形图居中 size=480×480，周围六个方向标注文字带指示线
- **Rendering × Palette**: `minimalist-swiss` × `editorial-classic`
- **Image**: p16_center_img.png
- **Title**: 极简瑞士 × 编辑经典
- **Content**: 包豪斯感极简图形居中，六条标注线向外辐射，文字像产品图解

#### Slide 17 — 窄条图片横贯中部 + 上下各一段文字

- **Layout**: 顶部文字区 height=200px，中部图条 height=240px，底部文字区 height=240px
- **Rendering × Palette**: `screen-print` × `vivid-launch`
- **Image**: p17_strip_img.png
- **Title**: 网版印刷 × 活力发射
- **Content**: 丝网印刷风横条图贯穿页面中腰，上下文字各成一节，图将文切开

#### Slide 18 — 不规则多边形图像 + 文字填缝

- **Layout**: 六边形裁切图 (clipPath polygon) 居左偏，文字块填入右侧和角落空隙
- **Rendering × Palette**: `nature` × `sunset-gradient`
- **Image**: p18_polygon_img.png (clipPath六边形裁切)
- **Title**: 自然插画 × 落日渐变
- **Content**: 热带植物图以六边形呈现，文字在图形外围和角落自由填充

#### Slide 19 — 多图拼贴蒙太奇 + 大字压跨多图

- **Layout**: 三张图拼接平铺全幅，大号文字（font-size≈72px）横跨多图之上
- **Rendering × Palette**: `editorial` × `dark-cinematic`
- **Image**: p19_collage1.png, p19_collage2.png, p19_collage3.png
- **Title**: 杂志编辑 × 暗黑影院
- **Content**: 三张编辑摄影拼贴铺满页面，超大标题字横压其上；蒙太奇叙事

#### Slide 20 — 结尾：暗底反白 + 单句居中收场

- **Layout**: 图全出血黑板背景，单行文字绝对居中，页面留白≥60%
- **Rendering × Palette**: `chalkboard` × `mono-ink`
- **Image**: p20_closing.png (hero_page)
- **Title**: 黑板粉笔 × 墨黑单色
- **Content**: 黑板星座底图，正中一句话收尾；负空间即内容

---

## X. Speaker Notes Requirements

- 文件命名与SVG对应：`01_cover.md` ↔ `01_cover.svg`
- 演讲时长：约15分钟
- 备注风格：简洁说明，指出每页图文结合要点
- 演示目的：展示（showcase）

---

## XI. Technical Constraints Reminder

1. viewBox: `0 0 1280 720`
2. 背景用 `<rect>`
3. 文字换行用 `<tspan>`，禁止 `<foreignObject>`
4. 透明度默认用 `fill-opacity` / `stop-opacity`；`rgba()` 保持转换兼容
5. 禁止：`mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. 文字符号写原始 Unicode，禁止 HTML 实体（&nbsp; &mdash; 等）
7. `clipPath` 仅用于 `<image>` 裁切（P09圆形、P18六边形）
8. 图标使用 `<use data-icon="tabler-outline/xxx"/>` 占位符
