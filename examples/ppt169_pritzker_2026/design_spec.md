# pritzker_2026_test_20260516 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | pritzker_2026_test_20260516 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 11 |
| **Design Style** | A) General Versatile + 编辑设计 / 杂志感 / 建筑摄影主导 |
| **Target Audience** | 建筑/设计爱好者、设计行业从业者、文化媒体读者 |
| **Use Case** | 行业分享、设计课堂、自媒体长图、读书会演讲 |
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

- **Style**: 编辑杂志感 + 建筑摄影主导
- **Theme**: Light theme
- **Tone**: 克制、克难、克重——大图说话，文字点题；混凝土质感的米白底色 + 墨黑文字 + 暖金强调

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F5F2EC` | 米白宣纸底（主背景） |
| **Secondary bg** | `#EDE8DE` | 卡片/侧栏 |
| **Primary** | `#1C1C1C` | 标题、正文 |
| **Accent** | `#B8935A` | 编号、分隔线、强调 |
| **Body text** | `#1C1C1C` | 正文主色 |
| **Secondary text** | `#5C5852` | 副文、图注 |
| **Tertiary text** | `#8B8680` | 混凝土灰，页脚、辅助 |
| **Border/divider** | `#D4CFC4` | 分隔线 |

---

## IV. Typography System

### Font Plan

**Typography direction**: editorial CJK — 西文衬线 × 中文黑体，杂志专栏感

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei", "PingFang SC"` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `KaiTi` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Georgia, "Microsoft YaHei", "PingFang SC", serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: `KaiTi, Georgia, "Microsoft YaHei", serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body = 22px (中等密度)

| Purpose | Ratio | Project value | Weight |
| ------- | ----- | ------------- | ------ |
| Cover title | 3.3x | 72px | Bold |
| Chapter / section opener | 2.2x | 48px | Bold |
| Page title | 1.6-1.8x | 36-40px | Bold |
| Project number (01-08 大编号) | 4x | 88px | Light Italic (Georgia) |
| Subtitle | 1.3x | 28px | SemiBold |
| **Body** | **1x** | **22px** | Regular |
| Annotation / caption | 0.7x | 15px | Regular |
| Page number / footnote | 0.55x | 12px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 50-100px（编号 + 章节锚标）
- **Content area**: ~520px（图文主体）
- **Footer area**: 30-40px（页码、来源、品牌锚）

### Layout Pattern Library

不预设主导 pattern。每页按内容性格挑节奏（详见 §VIII 表中 `Layout pattern` 列），原则：
1. 相邻两页不重复 pattern
2. 同一 pattern 全 deck 不超过 2 次
3. 图比例驱动方向（横图优先 hero/上下带，方图优先并置，竖图优先左右带）
4. 同主题多图合并到一页（多图组合）而非拆页

### Spacing Specification

**Universal**:

| Element | Range | Project |
| ------- | ----- | ------- |
| Safe margin | 40-60px | 60px |
| Content block gap | 24-40px | 32px |
| Icon-text gap | 8-16px | 12px |

**Non-card containers** (大量 breathing/hero 页):

- 行高 1.5×
- 全幅大图采用 `xMidYMid slice`；hero 文字浮层有 35-55% 半透明黑底 scrim
- 不强求等宽栏；文字宽度按可读性（每行 24-32 汉字）

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `tabler-outline`（描边 1.5px）
- 仅用于章节编号点缀、地理标识、年份徽章；不强加于每页

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 地点定位 | `tabler-outline/map-pin` | P03-P10（每页右上） |
| 时间/年份 | `tabler-outline/calendar` | P02（总览） |
| 建筑师章 | `tabler-outline/blockquote` | P11（结语） |
| 翻页指示 | `tabler-outline/arrow-right` | P02 |

---

## VII. Visualization Reference List

无数据可视化页。本 deck 完全图文叙事驱动，无图表。

---

## VIII. Image Resource List

> Layout pattern 全部 verbatim from `references/image-layout-patterns.md`。覆盖 Group A / C / D / E 至少 4 组；同组内 id 轮换；相邻页不重复。

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- |
| ando_h_rooftop.png | 685×514 | 1.33 | P01 封面背景（混凝土水景） | Photography | #1 full-bleed background with floating title | user | Existing | 安藤忠雄 H+ 美术馆屋顶水景 |
| ando_h_exterior.png | 1080×810 | 1.33 | P03 安藤代表作主图 | Photography | #41 background image with native callout cards floating over | user | Existing | H+ 美术馆临河外观 |
| ando_h_interior.png | 667×937 | 0.71 | P03 安藤副图（竖图） | Photography | (同上多图组合) | user | Existing | H+ 美术馆室内空间 |
| chipperfield_milan_exterior.png | 1080×810 | 1.33 | P04 奇普菲尔德主图 | Photography | #48 side-by-side comparison (古罗马 vs 当代) | user | Existing | 米兰冰球馆外观 |
| chipperfield_roman_amphitheater.png | 800×533 | 1.50 | P04 古罗马参照 | Photography | (与主图并置) | user | Existing | 古罗马圆形剧场 |
| chipperfield_milan_facade.png | 1024×1365 | 0.75 | P04 立面细节（竖图） | Photography | (副图条带) | user | Existing | 场馆立面金属环带 |
| zaha_tamkang_bridge.png | 960×640 | 1.50 | P05 扎哈大桥主视觉 | Photography | #15 multi-image montage with bold text spanning across | user | Existing | 淡江大桥流线姿态 |
| zaha_tamkang_structure.png | 960×640 | 1.50 | P05 大桥结构 | Photography | (蒙太奇成员) | user | Existing | 大桥单塔斜拉结构 |
| zaha_tamkang_full.png | 831×554 | 1.50 | P05 大桥远景 | Photography | (蒙太奇成员) | user | Existing | 大桥跨江全景 |
| foster_shanghai_exterior.png | 1080×652 | 1.66 | P06 福斯特大图 | Photography | #12 faded image as backdrop with oversized overlay text | user | Existing | 上海嘉艺术外观全景 |
| foster_shanghai_petal.png | 1080×1368 | 0.79 | P06 花瓣细节 | Photography | (浮层旁置小图框) | user | Existing | 花瓣立面细节 |
| oma_new_museum_before.png | 1080×809 | 1.33 | P07 OMA 扩建前后 (前) | Photography | #50 before/after slider-style side-by-side | user | Existing | 纽约新美术馆扩建前 |
| oma_new_museum_after.png | 1080×921 | 1.17 | P07 OMA 扩建前后 (后) | Photography | (#50 配对) | user | Existing | 纽约新美术馆扩建后 |
| oma_new_museum_massing.png | 1080×608 | 1.78 | P07 体块模型条带 | Photography | (#50 下方副条) | user | Existing | OMA 体块模型 |
| oma_new_museum_interior.png | 1080×896 | 1.21 | P07 室内（备用） | Photography | (内嵌副图框) | user | Existing | 美术馆内部 |
| zumthor_lacma_exterior.png | 1080×608 | 1.78 | P08 卒姆托主图 | Photography | #14 horizontal banner strip cutting through mid-section | user | Existing | LACMA 大卫·格芬画廊横幅 |
| zumthor_lacma_underside.png | 1080×720 | 1.50 | P08 底部公共空间 | Photography | (mid-section 横条之下副图) | user | Existing | 悬浮架空底部空间 |
| zumthor_lacma_interior.png | 1080×608 | 1.78 | P08 内部（备用） | Photography | (右上小景) | user | Existing | LACMA 室内 |
| gehry_abu_dhabi_render1.png | 1080×608 | 1.78 | P09 盖里渲染主图 | Photography | #19 image floating in whitespace with thin frame and caption | user | Existing | 阿布扎比古根海姆主渲染 |
| gehry_abu_dhabi_render2.png | 1080×607 | 1.78 | P09 渲染辅图 | Photography | (#19 第二浮层框) | user | Existing | 第二角度渲染 |
| gehry_abu_dhabi_render3.png | 1000×1000 | 1.00 | P09 方图辅 | Photography | (#19 第三浮层) | user | Existing | 鸟瞰渲染 |
| kere_senegal_exterior.png | 818×546 | 1.50 | P10 凯雷主图（土砖外观） | Photography | #38 background image + annotation cards | user | Existing | 塞内加尔歌德学院外观 |
| kere_senegal_courtyard.png | 630×944 | 0.67 | P10 院落（竖图） | Photography | (annotation 中嵌入小图) | user | Existing | 猴面包树核心院落 |
| kere_senegal_interior.png | 980×654 | 1.50 | P10 内部 | Photography | (annotation 中嵌入小图) | user | Existing | 学院内部空间 |

**Layout pattern 覆盖审计**:
- Group A (容器): #1 cover, #12 faded backdrop, #14 mid-section banner, #15 montage with text → 4 patterns
- Group C (overlay): #19 floating frame → 1 pattern
- Group D (image-as-canvas): #38 background + cards, #41 background + callouts → **2 patterns，满足 Group D 覆盖硬约束**
- Group E (multi-image): #48 side-by-side, #50 before/after → 2 patterns
- 共 9 个不同 pattern 跨 4 组，无任何 pattern 使用 >2 次，相邻页无重复

---

## IX. Content Outline

### Part 1: 开篇

#### Slide 01 - 封面

- **Layout**: #1 Full-bleed background + floating title（混凝土水景为视觉锚）
- **Title**: 2026 普利兹克奖大师季
- **Subtitle**: 8 座新作，8 种深耕
- **Info**: 从苏州河畔到沙漠腹地·读懂顶级建筑师的思考与坚守 / 来源：公众号孙琬童 / 2026

#### Slide 02 - 8 位大师总览

- **Layout**: Negative-space-driven + 8 卡（4×2 方阵），每卡只放编号 + 大师名 + 一行项目名 + 地理标识
- **Title**: 八位大师，八种坚守
- **Content**:
  - 01 安藤忠雄 · 苏州 H+ 美术馆 · 中国苏州
  - 02 戴卫·奇普菲尔德 · 米兰圣朱利亚冰球馆 · 意大利米兰
  - 03 扎哈·哈迪德（遗作）· 淡江大桥 · 中国台北
  - 04 诺曼·福斯特 · 上海嘉艺术 · 中国上海
  - 05 OMA + SANAA · 纽约新美术馆扩建 · 美国纽约
  - 06 彼得·卒姆托 · LACMA 大卫·格芬画廊 · 美国洛杉矶
  - 07 弗兰克·盖里（遗作）· 阿布扎比古根海姆博物馆 · 阿联酋阿布扎比
  - 08 迪埃贝多·凯雷 · 塞内加尔歌德学院 · 塞内加尔达喀尔

### Part 2: 8 座新作逐一深耕

#### Slide 03 - 01 安藤忠雄 · 苏州 H+ 美术馆

- **Layout**: #41 image-as-canvas + 浮层 annotation cards（横图为底，左侧浮一张卡片承载文字，竖图作为右上小内嵌图）
- **Title**: 在江南园林里写一首混凝土诗
- **Subtitle**: 安藤忠雄 · 1995 年普利兹克奖 · 2026.1 开馆
- **Content**:
  - 设计理念：立体园林—回游性，从苏州土地记忆中汲取园林精髓
  - 材质语言：清水混凝土肌理，摒弃装饰，几何线条 × 光影留白
  - 空间叙事：屋顶以水为主题，回游中抵达面向天空与水的场所
  - 核心理念："让建筑归于自然，让艺术治愈人心"

#### Slide 04 - 02 戴卫·奇普菲尔德 · 米兰圣朱利亚冰球馆

- **Layout**: #48 side-by-side comparison（左侧主图当代场馆，右侧古罗马剧场参照，下方副图横向立面条带）
- **Title**: 千年罗马竞技场的现代回响
- **Subtitle**: 戴卫·奇普菲尔德 · 2023 年普利兹克奖 · 2026 冬奥会场馆
- **Content**:
  - 容量：16,000 名观众，本届冬奥唯一新建永久场馆
  - 造型源流：呼应米兰古罗马圆形剧场椭圆形态
  - 立面：三道金属环带 + 玻璃腰线 + LED 灯带
  - 设计精神：极致克制与精确，公共建筑服务于人

#### Slide 05 - 03 扎哈·哈迪德（遗作）· 淡江大桥

- **Layout**: #15 multi-image montage + 上方半透明深色横幅承载大标题（三张图横向蒙太奇拼贴）
- **Title**: 跨越江河的流动态势
- **Subtitle**: 扎哈·哈迪德 · 2004 年普利兹克奖 · 2026.5.12 通车
- **Content**:
  - 全长 920 米，全球同类型最长跨度单塔不对称斜拉桥
  - 100% 还原扎哈生前理想化设计
  - 工程力学 × 先锋美学的完美融合
  - "永不设限"——大师已逝，思想延续

#### Slide 06 - 04 诺曼·福斯特 · 上海嘉艺术

- **Layout**: #12 faded image as backdrop + 巨号叠加文字（横图压暗作底纹，巨号"04"和短标题压上，右侧细长竖图作小框）
- **Title**: 苏州河畔绽放的钢铁花瓣
- **Subtitle**: 诺曼·福斯特 · 1999 年普利兹克奖 · 2026.4 开放
- **Content**:
  - 不是白盒子，是城市中缓慢生长的生命体
  - 仿花朵扎根地面、向天空延展的生长轨迹
  - 三重体验：观展、观景、观城
  - 高技派外壳之下，古典人文精神通过现代材料重获新生

#### Slide 07 - 05 OMA + SANAA · 纽约新美术馆扩建

- **Layout**: #50 before/after side-by-side（上方左右并置扩建前/后，下方加体块模型横条）
- **Title**: 双强联动，新旧艺术共生
- **Subtitle**: OMA (库哈斯, 2000) × SANAA (妹岛+西泽, 2010) · 2026.3.21 开放
- **Content**:
  - 投资 8200 万美元，新增 5,574 ㎡
  - OMA 先锋解构 × SANAA 轻盈通透的碰撞
  - 通透立面 + 错落空间 + 开放布局，让城市街景与艺术空间相互渗透
  - "迭代更新、兼容并蓄"——百年美术馆获新活力

#### Slide 08 - 06 彼得·卒姆托 · LACMA 大卫·格芬画廊

- **Layout**: #14 horizontal banner strip 中段贯穿（顶部留标题，中段横幅大图，底部承载叙事文字）
- **Title**: 20 年打磨的诗意艺术方舟
- **Subtitle**: 彼得·卒姆托 · 2009 年普利兹克奖 · 2026.5.4 开放
- **Content**:
  - 耗资 7.24 亿美元，32,293 ㎡，历时 20 年
  - 七座极简混凝土亭子横跨威尔希尔大道之上
  - 摒弃艺术品等级化，古典与当代平等共生
  - "建筑是场所的诗意容器"

#### Slide 09 - 07 弗兰克·盖里（遗作）· 阿布扎比古根海姆博物馆

- **Layout**: #19 image floating in whitespace + 多浮层细框（三张渲染图错落浮于米白底，细框 + 小图注，文字以负空间承载）
- **Title**: 沙漠中的"解构主义绝唱"
- **Subtitle**: 弗兰克·盖里（1929-2025）· 1989 年普利兹克奖 · 2026 开幕
- **Content**:
  - 大师生命尾声 20 年心血，金属外立面随日光变换肌理
  - 不规则曲面 + 灵动褶皱 + 极致冲击的几何
  - 针对沙漠极端气候的先进遮阳与隔热系统
  - "建筑无边界、创意无极限"——解构主义大师的收官终篇

#### Slide 10 - 08 迪埃贝多·凯雷 · 塞内加尔歌德学院

- **Layout**: #38 background image + annotation cards（横图作底，2-3 张半透明信息卡浮上，竖图与内部图嵌入卡内）
- **Title**: 夯土砖"屏风"，扎根乡土的温暖建筑
- **Subtitle**: 迪埃贝多·凯雷 · 2022 年普利兹克奖 · 2026.4 开幕
- **Content**:
  - 核心院落置入猴面包树（生命象征）
  - 本土压制土砖 + 自然通风系统，摆脱空调依赖
  - "顺应自然，而非与之对抗"
  - 全球建筑同质化时代，凯雷再证：顶级建筑扎根土地、温暖人心

### Part 3: 收束

#### Slide 11 - 结语：所有传世，皆源于深耕

- **Layout**: Negative-space-driven 单元素 + 暖金强调引语（无大图，文字为主，留白为主）
- **Title**: 所有传世的经典，皆源于日复一日的坚守
- **Content**:
  - 有人耗时二十年打磨一座场馆 — 卒姆托
  - 有人坚守本土人文，让建筑扎根土地 — 凯雷
  - 有人突破边界、颠覆常规 — 扎哈、盖里
  - 收束语：对空间、自然、人文的极致敬畏与深度思考
- **Footer**: 资料来源：公众号"孙琬童" / 致敬 8 位大师 / 2026

---

## X. Speaker Notes Requirements

- **Filename**: 与 SVG 同名（`01_cover.svg` → `notes/01_cover.md`）
- **Total duration**: 约 12 分钟
- **Notes style**: 文化随笔式，叙述温度优先于技术参数
- **Purpose**: inform + inspire

---

## XI. Technical Constraints Reminder

1. viewBox: `0 0 1280 720`
2. `<rect>` 背景，`<tspan>` 文本换行
3. 透明度默认用 `fill-opacity` / `stroke-opacity`；`rgba()` 保持转换兼容
4. 禁用：`mask`, `<style>`, `class`, `foreignObject`, `textPath`, `<animate*>`, `<script>`
   - `<g opacity>` 可转换但会产生近似保真 warning，默认改用子元素透明度
5. 字符：`—` `·` `→` 等用原生 Unicode，禁用 HTML named entities
6. 全幅图用 `preserveAspectRatio="xMidYMid slice"`；半透明 scrim 用 `<rect fill-opacity>`
