# SVG 图标库

本目录提供 **640+ 个高质量 SVG 图标**，可直接嵌入到 PPT Master 生成的 SVG 文件中。图标来源于 [SVG Repo](https://www.svgrepo.com/)，采用统一的填充风格（Solid），viewBox 为 `0 0 16 16`。

---

## 📋 目录

- [使用方式](#使用方式)
- [图标分类索引](#图标分类索引)
- [自定义指南](#自定义指南)
- [设计规范](#设计规范)

---

## 使用方式

### 方法一：在 AI 对话中引用（推荐）

直接告诉 AI 使用图标库中的图标：

```
请在第3页使用 templates/icons/ 中的图标：
- 标题左侧使用 rocket.svg 图标
- 第一个卡片使用 chart-bar.svg
- 第二个卡片使用 users.svg
- 成功状态使用 circle-checkmark.svg
```

### 方法二：复制粘贴嵌入

1. 打开图标文件（如 `rocket.svg`）
2. 复制 `<path>` 元素内容
3. 用 `<g>` 包裹并添加 `transform` 调整位置和大小：

```xml
<!-- 在目标 SVG 中嵌入图标 -->
<g transform="translate(100, 200) scale(3)">
  <!-- 从 rocket.svg 复制的 path 内容 -->
  <path fill-rule="evenodd" clip-rule="evenodd" 
        d="M10 16L12 14V10L13.6569 8.34314..." 
        fill="#0076A8"/>
</g>
```

### transform 参数说明

| 参数 | 作用 | 示例 |
|------|------|------|
| `translate(x, y)` | 移动位置 | `translate(100, 200)` 移到 (100, 200) |
| `scale(n)` | 缩放大小 | `scale(3)` 放大到 48px（基础 16px × 3） |
| `rotate(deg)` | 旋转角度 | `rotate(45)` 顺时针旋转 45 度 |

**组合使用**：`transform="translate(100, 200) scale(2)"`

### 修改颜色

图标默认使用 `fill="#000000"`（黑色），可直接替换为任意颜色：

```xml
<!-- 修改为主题蓝色 -->
<path fill="#0076A8" d="..." />

<!-- 或在 <g> 上统一设置 -->
<g transform="..." fill="#2196F3">
  <path d="..." />
</g>
```

---

## 图标分类索引

### 📍 导航与箭头 (50+)

**基础箭头**
`arrow-up` `arrow-down` `arrow-left` `arrow-right` `arrow-up-left` `arrow-up-right` `arrow-down-left` `arrow-down-right`

**带线箭头**
`arrow-up-from-line` `arrow-up-to-line` `arrow-down-from-line` `arrow-down-to-line` `arrow-left-from-line` `arrow-left-to-line` `arrow-right-from-line` `arrow-right-to-line`

**转向箭头**
`arrow-turn-down-left` `arrow-turn-down-right` `arrow-turn-up-left` `arrow-turn-up-right` `arrow-u-down-left` `arrow-u-up-right`

**趋势箭头**
`arrow-trend-up` `arrow-trend-down` `arrow-up-wide-short` `arrow-down-wide-short`

**双向箭头**
`arrows-left-right` `arrows-up-down` `arrow-left-arrow-right` `arrow-up-arrow-down`

**旋转箭头**
`arrow-rotate-left` `arrow-rotate-right` `arrows-rotate-clockwise` `arrows-rotate-counter-clockwise` `arrows-repeat`

**角度符号**
`angle-up` `angle-down` `angle-left` `angle-right` `angles-up` `angles-down` `angles-left` `angles-right` `caret-up` `caret-down` `caret-left` `caret-right`

**圆形箭头**
`circle-arrow-up` `circle-arrow-down` `circle-arrow-left` `circle-arrow-right`

---

### 👤 用户与人物 (10+)

`user` `users` `person` `person-walking` `person-wave` `circle-user` `square-user` `group` `address-card` `head-side`

---

### 📊 数据与图表 (15+)

`chart-bar` `chart-line` `chart-pie` `arrow-trend-up` `arrow-trend-down` `gauge-high` `gauge-medium` `gauge-low` `table` `database` `server` `funnel` `filter` `sort` `sliders`

---

### 📁 文件与文件夹 (15+)

`file` `file-plus` `files` `folder` `folder-open` `folders` `floppy-disk` `archive-box` `clipboard` `copy` `image` `images` `newspaper` `receipt` `sticky-note`

---

### ✅ 状态与反馈 (20+)

**成功/确认**
`checkmark` `circle-checkmark` `square-checkmark` `badge-check` `shield-check` `thumbs-up`

**错误/取消**
`x` `x-1` `circle-x` `square-x` `ban` `thumbs-down`

**警告/提示**
`circle-exclamation` `triangle-exclamation` `diamond-exclamation` `octagon-exclamation` `circle-info` `circle-question`

**加减操作**
`plus` `minus` `circle-plus` `circle-minus` `square-plus` `square-minus`

---

### 🔧 工具与操作 (25+)

**编辑工具**
`pencil` `pencil-square` `pen-nib` `brush` `paint-bucket` `paint-roller` `eyedropper` `palette` `crop` `scissors` `ruler`

**系统操作**
`cog` `sliders` `wrench` `hammer` `screwdriver` `toolbox`

**视图操作**
`magnifying-glass` `zoom-in` `zoom-out` `eye` `eye-slash` `maximize` `minimize`

**删除操作**
`trash` `delete`

---

### 💻 设备与技术 (30+)

**计算设备**
`desktop` `laptop` `mobile` `tablet` `smartwatch` `tv` `tv-retro`

**输入设备**
`keyboard` `mouse` `joystick` `game-controller` `d-pad`

**存储与连接**
`database` `server` `microchip` `plug` `outlet` `usb`

**网络**
`wifi` `wifi-low` `wifi-medium` `wifi-slash` `signal` `signal-fair` `signal-good` `signal-weak` `signal-slash` `bluetooth` `globe` `rss`

**电池**
`battery-full` `battery-half` `battery-empty` `battery-charge` `battery-slash`

---

### 📱 通讯与社交 (15+)

`phone` `phone-slash` `envelope` `mailbox` `paper-plane` `comment` `comment-dots` `comments` `comments-slash` `bell` `bell-slash` `at` `hashtag` `share-nodes`

---

### 🏢 商业与金融 (20+)

**货币**
`dollar` `euro` `british-pound` `yen` `coin` `money` `wallet` `credit-card`

**购物**
`shopping-cart` `shopping-bag` `shopping-basket` `shop` `receipt` `tag` `ticket`

**建筑**
`building` `city` `factory` `hospital` `museum` `castle` `home` `home-1`

---

### 🚗 交通与出行 (15+)

`car` `bus` `train` `plane` `ship` `truck` `bicycle` `scooter` `rocket` `route` `map` `map-pin` `location-arrow` `location-target` `signpost` `traffic-light` `traffic-cone`

---

### 🎨 媒体与娱乐 (30+)

**播放控制**
`play` `pause` `stop` `play-pause` `fast-forward` `rewind` `skip-forward` `skip-backward` `shuffle` `arrows-repeat`

**音频**
`volume-high` `volume-low` `volume-none` `volume-x` `volume-slash` `microphone` `microphone-slash` `headphones` `music` `waveform`

**视频与相机**
`video` `video-camera` `video-camera-slash` `camera` `camera-slash` `film` `compact-disc`

**游戏**
`game-controller` `joystick` `dice` `die-1` `die-2` `die-3` `die-4` `die-5` `die-6` `playing-card` `meeple`

---

### ⚽ 运动与健身 (15+)

`soccer` `basketball` `baseball` `football` `tennis-ball` `hockey` `curling-stone` `trophy` `target` `target-arrow` `bow-and-arrow`

---

### 🍔 食物与饮品 (15+)

`burger` `pizza` `cake` `cake-slice` `cupcake` `ice-cream` `citrus-slice` `bowl` `utensils` `mug` `cocktail` `wine-glass` `soda` `bottle`

---

### 🌤️ 天气与自然 (20+)

**天气**
`sun` `sun-cloud` `sun-fog` `moon` `moon-cloud` `moon-fog` `cloud` `cloud-fog` `cloud-rain` `cloud-snow` `cloud-lightning` `rainbow` `rainbow-cloud` `snow` `wind` `droplet` `umbrella`

**自然**
`tree` `tree-evergreen` `leaf` `seedling` `flower` `mountains` `water` `fire`

---

### ✨ 形状与装饰 (25+)

**基础形状**
`circle` `square` `triangle` `hexagon` `octagon` `diamond-shape` `star` `star-half` `heart` `heart-half` `heart-broken`

**特殊形状**
`sparkles` `bolt` `crown` `gem` `crystal-ball` `wand-with-sparkles`

**扑克符号**
`spade` `club` `diamond`

---

### 🔒 安全与权限 (10+)

`lock-closed` `lock-open` `key` `key-skeleton` `keyhole` `shield` `shield-check` `shield-half` `eye` `eye-slash` `face-id`

---

### 📝 文本与编辑 (20+)

**格式**
`bold` `italic` `underline` `strikethrough` `text` `font-case`

**对齐**
`align-left` `align-right` `align-text-center` `align-text-justify` `align-text-left` `align-text-right` `indent` `outdent`

**引用与列表**
`quote-left` `quote-right` `block-quote` `list` `list-ordered`

**代码**
`code` `code-block` `terminal`

---

### 🧭 布局与对齐 (15+)

`align-top` `align-bottom` `align-left` `align-right` `align-center-horizontal` `align-center-vertical` `distribute-horizontal` `distribute-vertical` `grid` `grid-masonry` `columns` `rows` `layers` `frame` `component`

---

### 🔢 数字与字母 (46)

**字母 A-Z**
`a` `b` `c` `d` `e` `f` `g` `h` `i` `j` `k` `l` `m` `n` `o` `p` `q` `r` `s` `t` `u` `v` `w` `x-1` `y` `z`

**数字 0-9**
`number-0` `number-1` `number-2` `number-3` `number-4` `number-5` `number-6` `number-7` `number-8` `number-9`

**带圆圈数字**
`circle-number-0` `circle-number-1` `circle-number-2` `circle-number-3` `circle-number-4` `circle-number-5` `circle-number-6` `circle-number-7` `circle-number-8` `circle-number-9`

---

### ♈ 星座 (12)

`aries` `taurus` `gemini` `cancer` `leo` `virgo` `libra` `scorpio` `sagittarius` `capricorn` `aquarius` `pisces`

---

### ♟️ 国际象棋 (6)

`king` `queen` `rook` `bishop` `knight` `pawn`

---

### 😀 表情 (10)

`face-smile` `face-laugh` `face-meh` `face-sad` `face-cry` `face-angry` `face-open-mouth` `face-no-mouth` `face-melt`

---

### 🐾 动物 (10+)

`dog` `cat` `fish` `bee` `butterfly` `paw` `bone`

---

### 🎲 其他常用 (30+)

**时间**
`clock` `stopwatch` `alarm-clock` `hourglass-empty` `hourglass-half-top` `hourglass-half-bottom` `calendar` `watch`

**开关**
`power` `toggle-circle-left` `toggle-circle-right`

**书籍**
`book` `book-open` `books` `bookmark` `bookmark-plus`

**礼物与庆祝**
`gift` `cake` `trophy` `crown` `sparkles`

**工作**
`suitcase` `briefcase` `mortarboard`

**其他**
`lightbulb` `flag` `anchor` `compass` `life-ring` `rocket` `robot` `ghost` `skull` `alien` `ufo`

---

## 自定义指南

### 调整大小

图标基础尺寸为 **16×16**（viewBox: `0 0 16 16`），通过 `scale()` 调整：

| 目标尺寸 | scale 值 | 使用场景 |
|----------|----------|----------|
| 16px | 1 | 小图标（默认） |
| 24px | 1.5 | 常规图标 |
| 32px | 2 | 中等图标 |
| 48px | 3 | 大图标、章节标识 |
| 64px | 4 | 特大图标、封面 |

### 修改颜色

图标使用 `fill="#000000"`，可直接替换：

```xml
<!-- 主题蓝 -->
<path fill="#0076A8" d="..." />

<!-- 成功绿 -->
<path fill="#4CAF50" d="..." />

<!-- 警告橙 -->
<path fill="#FF9800" d="..." />

<!-- 错误红 -->
<path fill="#F44336" d="..." />
```

### 添加描边效果

如需线条风格，可添加 stroke 并移除 fill：

```xml
<g transform="..." stroke="#0076A8" stroke-width="1" fill="none">
  <path d="..." />
</g>
```

---

## 设计规范

### 图标参数

| 参数 | 值 |
|------|-----|
| viewBox | `0 0 16 16` |
| 基础尺寸 | 16 × 16 px |
| 风格 | 填充（Solid） |
| 来源 | SVG Repo |

### 颜色建议

| 场景 | 推荐颜色 |
|------|----------|
| 主要功能 | 主色调（如 #0076A8） |
| 次要功能 | 灰色 #757575 |
| 成功状态 | 绿色 #4CAF50 |
| 警告状态 | 橙色 #FF9800 |
| 错误状态 | 红色 #F44336 |
| 信息状态 | 蓝色 #2196F3 |

### 使用原则

✅ **推荐做法**：
- 同一页面/项目使用统一风格图标
- 图标大小与文字层级匹配
- 颜色与整体配色方案协调
- 图标与文字保持适当间距

❌ **避免做法**：
- 混用不同风格的图标
- 图标过大或过小
- 颜色与背景对比度不足
- 图标堆砌过多

---

## 图标来源

所有图标来自 [SVG Repo](https://www.svgrepo.com/)，遵循 CC0 或 MIT 许可证，可免费商用。

如需更多图标，可从以下来源获取：

| 图标库 | 网址 | 特点 |
|--------|------|------|
| SVG Repo | https://www.svgrepo.com/ | 本库来源，50万+免费图标 |
| Lucide | https://lucide.dev/ | 简洁线条风格 |
| Heroicons | https://heroicons.com/ | Tailwind 风格 |
| Tabler | https://tabler-icons.io/ | 丰富全面 |

---

**图标数量**：640+  
**最后更新**：2025-12-06
