# 高级政企演示文稿视觉设计范式

> 这份文档是对 [`executor-base.md`](../../skills/ppt-master/references/executor-base.md) §3 与原版 [`visual-design-paradigm.md`](./visual-design-paradigm.md) 的深度升级，融合了八个维度的工艺研究与三轮专家评审结论。目标：让 Executor 在手写 SVG 时具备「以什么标准判断每个决策对不对」的内化能力。

---

## 0. 设计哲学

**高级感的本质公式**：层次（depth）× 定制度（bespoke）× 克制（restraint）。三者缺一即退化为平庸。

- **层次**：并非指阴影和渐变，而是指信息结构可以被眼睛一层层剥开——眼球触及页面的顺序和设计者的意图完全吻合。
- **定制度**：没有任何一个元素看起来是「从默认样式库拿的」——字间距是算出来的，颜色是调出来的，投影的颜色来自品牌色系。
- **克制**：每一个存在的元素都有不可替代的理由；删掉任何一个元素，层次就会塌陷，而不是「好像少了点装饰」。

**扁平专业 ≠ 平**。政企级扁平包含：品牌色渐变（delta-L ≤ 12%）、navy 色投影（非黑色）、display 字的负间距、精确字号阶梯。拿走任何一条，就只剩「线框图」——那正是 AI 感的根源。

---

## 1. 评价 Rubric（每页可打分，满分 100）

每项满分 10 分，按证据打分（不按印象）。**低于 60 分需重做视觉层**。

| # | 维度 | 0 分（廉价/线框图） | 10 分（高级/定制） |
|---|------|-------------------|------------------|
| 1 | **字号阶梯** | 存在 17、19、24、29px 等非系统值 | 所有尺寸属于同一 Major Third 阶梯（14/18/22/28/36/44px） |
| 2 | **Display 字间距** | 所有标题 `letter-spacing='0'`（Word 默认） | 36px 以上标题 `letter-spacing='-0.72'`；44px → `-1.0` |
| 3 | **CJK 行高** | `dy` ≈ 1.2–1.3× 字号（密不透气） | 正文 `dy = font-size × 1.7`；标题 `dy = font-size × 1.15` |
| 4 | **字重对比** | 标题与正文同为 700 或 400，或差异仅 100 | 同一层级跨越 ≥ 2 档：300/400 正文 vs 700 标题 |
| 5 | **眉标（Eyebrow）** | 无眉标，标题直接开始 | 12px/600wt/letter-spacing +1.4/品牌色，位于标题上方 |
| 6 | **投影品质** | `flood-color='#000000'`（clip-art 感） | `flood-color='#003D66'`，`flood-opacity` ≤ 0.14 |
| 7 | **渐变克制** | 每张卡片、图标、KPI 都有渐变（视觉噪声） | 渐变仅用于结构层（标题栏）或单一 hero 元素，其余全平涂 |
| 8 | **颜色语义** | 绿色既用于装饰边框、又用于正面数据、又用于区域底色 | 每种色只干一件事；绿=正向结果/增长，蓝=结构/权威 |
| 9 | **间距系统** | y 坐标为 147、183、221（任意值） | 所有坐标为 8px 网格倍数（144/184/224） |
| 10 | **克制天花板** | 单页出现 5+ 字号、3+ 字重、4+ 颜色 | 单页 ≤ 3 字号、2 字重、2 文字填充色（眉标可用第三色） |

---

## 2. 排版系统

### 2.1 字号阶梯 — Major Third（×1.25）锚定 18px

18px 为正文基准，向上×1.25（取整）：

| 用途 | 字号 | 字重 | 字间距 | 行高乘数 |
|------|------|------|--------|---------|
| 脚注/注释 | 12px | 400 | +1.5px | ×1.5（dy=18） |
| 眉标/英文大写标签 | 12px | 600 | +1.4px | — |
| 数据标注/图例 | 13–14px | 400 | 0 | ×1.5 |
| 正文 | 18px | 400 | 0 | ×1.7（dy=30） |
| 副标题/小节标题 | 22px | 600 | -0.4px | ×1.3（dy=29） |
| 页标题 | 28px | 700 | -0.5px | ×1.2（dy=34） |
| Slide 主标题 | 36px | 700 | -0.72px | ×1.15（dy=41） |
| 封面/Hero 标题 | 44px | 700 | -1.0px | ×1.1（dy=48） |
| KPI 大数字 | 64–72px | 700 | -1.5px | — |

**绝对禁止**：`font-size='17'`、`'19'`、`'20'`、`'24'`、`'29'`、`'34'`——非系统值破坏隐含的比例关系，使眼睛感知到「随意摆放」。

### 2.2 字重对比 — Skip-a-Weight 法则

同一层级间距至少跨越 2 个字重档位（100 为一档）：

```
300 (Light 支撑说明) → 700 (Bold 标题)   ✅ 跨 4 档
400 (Regular 正文) → 700 (Bold 标题)     ✅ 跨 3 档
400 → 600 (SemiBold)                    ⚠️ 仅可用于眉标 vs. 正文对比
400 → 500 (Medium)                      ❌ 差异过小，CJK 18px 几乎不可见
```

> Microsoft YaHei 在 Windows 只有 Regular（400）和 Bold（700）两个物理字重。`font-weight='300'` 映射到 Regular，**不要在 CJK 中指定 300 期待 Light 效果**——它不会更细。Latin 文字（如 Arial）支持 300。

### 2.3 字间距 — Optical Tracking

| 场景 | SVG 值（绝对 px，非 em） | 计算逻辑 |
|------|------------------------|---------|
| 36px 标题（CJK） | `letter-spacing='-0.72'` | 36 × (−0.02) |
| 44px Hero 标题 | `letter-spacing='-1.0'` | 44 × (−0.023) |
| 28px 副标题 | `letter-spacing='-0.5'` | 28 × (−0.018) |
| 12px 全大写眉标 | `letter-spacing='1.4'` | 12 × 0.12 |
| 18px 正文 | `letter-spacing='0'` | 不触碰 |

### 2.4 CJK 行高 — 1.7× 法则

```xml
<!-- 18px 正文，两行 CJK -->
<text font-size="18" font-family="Microsoft YaHei,sans-serif">
  <tspan x="80" dy="0">第一行正文内容，关于平台核心能力...</tspan>
  <tspan x="80" dy="30">第二行延续，dy=18×1.7≈30</tspan>
</text>

<!-- 36px 双行标题 -->
<text font-size="36" font-weight="700">
  <tspan x="80" dy="0">聚焦三大核心增长引擎</tspan>
  <tspan x="80" dy="41">第二行，dy=36×1.15≈41</tspan>
</text>
```

### 2.5 眉标（Eyebrow / Kicker）— 三级进入层

```xml
<!-- 眉标 → 标题 → 正文 的三层进入序列 -->
<text font-size="12" font-weight="600" letter-spacing="1.4"
      fill="#005792" font-family="Microsoft YaHei,sans-serif"
      x="80" y="108">战略分析 · STRATEGIC ANALYSIS</text>

<text font-size="36" font-weight="700" letter-spacing="-0.72"
      fill="#003D66" font-family="Microsoft YaHei,sans-serif"
      x="80" y="148">聚焦三大核心增长引擎</text>

<text font-size="18" font-weight="400"
      fill="#3A7FAF" font-family="Microsoft YaHei,sans-serif"
      x="80" y="184">正文说明，字间距=0，dy=30 per continuation line</text>
```

**间距规则**：眉标基线 → 标题大写字母顶 = 约 0.8× 标题字号。36px 标题：间距 ≈ 29px → 眉标基线 y=108，标题基线 y=148（预留 40px 含眉标自身高度）。

### 2.6 选择性填色（Chromatic Emphasis）

```xml
<!-- 仅对关键词换色，绝不对整行换色 -->
<text font-size="36" font-weight="700" x="80" y="200">
  <tspan fill="#003D66">推动营收实现</tspan>
  <tspan fill="#2F9A47">突破性</tspan>
  <tspan fill="#003D66">增长</tspan>
</text>
```

规则：每标题行最多一处 tspan 换色；最多 2 个汉字或 1 个英文单词；选色优先品牌绿（动作/成就词），次选品牌蓝（战略/方向词）；不改字号/字重。

### 2.7 KPI 大数字 — Keystone 法则

```xml
<!-- 极端尺寸+字重对比制造视觉锚点 -->
<text font-size="72" font-weight="700" fill="#005792"
      letter-spacing="-1.5" x="200" y="300">47</text>
<text font-size="16" font-weight="400" fill="#555555" x="276" y="286">%</text>
<text font-size="13" font-weight="400" letter-spacing="1.0"
      fill="#5A6B7B" x="200" y="322">市场占有率</text>
```

数字与单位/说明字号比不低于 4:1（72:16）；单位用 400 字重，说明用 300-400 字重；数字字重 700–800。

### 2.8 单页克制天花板 — 3/2/2 法则

在写任何 SVG 之前，先声明本页的字号/字重/颜色配额：

```
本页配额：字号=[36,18,12] | 字重=[700,400] | 文字填充=[#003D66, #005792]
```

随后任何 `<text>`/`<tspan>` 必须使用且仅使用这些值。眉标可引入第三种颜色，但前提是该颜色已出现在页面其他元素上。

### 2.9 CJK 行宽 — 最大 28 字法则

1280px 画布，左边距 80px，行宽上限 ≈ 900px（约 28 个 18px CJK 字符）。标题行：最大 14 字，约 504px，不超过画布 60%。宁可断行，不拉长行宽。

### 2.10 CJK 中嵌 Latin — 大小补偿

在 CJK 标题行内，Latin 字母/数字视觉上比同字号的汉字小约 10–15%：

```xml
<!-- CJK 标题内嵌数字时的视觉等高补偿 -->
<text font-size="36" font-weight="700" fill="#003D66">
  <tspan>战略聚焦</tspan>
  <!-- 嵌入 Latin 时通常不需要额外调整 YaHei 的 Latin 设计；
       若视觉偏小，将嵌入部分 font-size 改为 38–39 -->
  <tspan>2026</tspan>
  <tspan>核心增长</tspan>
</text>
```

---

## 3. 色彩与渐变

### 3.1 品牌色系完整色阶

**深蓝 #005792 的 7 档 Tint/Shade 体系**（从同一色相衍生，禁止混入外来灰色）：

| 变量名 | HEX | 用途 |
|--------|-----|------|
| `blue-tint-1` | `#E8F2F9` | 卡片底色、浅色行背景 |
| `blue-tint-2` | `#C5DCEE` | 分隔线描边（hairline）、表格 zebra |
| `blue-tint-3` | `#7AAFD4` | 图表次级系列、装饰规则线 |
| `blue-mid` | `#3A7FAF` | 元数据/注释文字颜色 |
| `blue-base` | `#005792` | 主色：结构头、主要数据系列 |
| `blue-shade-1` | `#003D66` | 正文文字（非纯黑）、强调背景 |
| `blue-shade-2` | `#00223A` | 投影颜色（flood-color） |

**品牌绿 #2F9A47 的 4 档体系**：

| 变量名 | HEX | 用途 |
|--------|-----|------|
| `green-tint-1` | `#E8F5EC` | 正向状态底色 |
| `green-tint-2` | `#A8D9B4` | 正向数据装饰 |
| `green-base` | `#2F9A47` | 正向/增长/CTA 唯一主体 |
| `green-shade` | `#1E6B30` | 绿色 hover/pressed 状态 |

**扩展色（推导而来，不引入新色系）**：

| 变量名 | HEX | 用途 |
|--------|-----|------|
| `amber-warn` | `#C47A10` | 风险/黄色预警（H=30, S=80%, L=45%） |
| `red-alert` | `#C0392B` | 负向/停止（去饱和暖红，非 #FF0000） |
| `bg-near-white` | `#F7F8FA` | 页面背景（非纯白，高级屏幕感） |

**禁止**：`fill='#CCCCCC'`、`fill='#888888'`、`fill='#F5F5F5'`——这些来自品牌体系外的灰色在视觉上断开色彩逻辑。

### 3.2 区域配比 — 70-20-8-2

| 占比 | 颜色 | 内容 |
|------|------|------|
| 70% | `#F7F8FA` / 白 | 页面底色、大面积留白 |
| 20% | `#005792` 及其 Tint/Shade | 结构条、主要数据系列、标题区 |
| 8% | `#2F9A47` 及其 tint | 每页最多一处正向强调 |
| 2% | 白色高光 / `#F7F8FA` | 深色底上的对比提亮 |

**关键约束**：绿色在单页面积绝不超过蓝色面积；若出现面积相当，将其中一个绿色元素换为 `#7AAFD4`（蓝色 tint）。

### 3.3 渐变构建 — delta-L ≤ 12% 法则

**精确规则**：

| 渐变类型 | 起止色 | delta-L | 角度 | 用途 |
|---------|--------|---------|------|------|
| 结构条微渐变 | `#005792` → `#003D66` | 8% | 水平 x2=1 y2=0 | 卡头栏、章节条 |
| 品牌对角渐变 | `#005792` → `#003D66` | 8% | 35° (x2=0.7 y2=1) | 封面背景 |
| 品牌双色渐变 | 见下方 3 停色定义 | — | 水平 | 封面/章节分隔，全本 ≤ 2 处 |

**品牌双色 3 停色渐变**（防止中间过渡变浑浊）：

```xml
<linearGradient id="brandGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0%"   stop-color="#005792"/>
  <stop offset="40%"  stop-color="#1A6E6E"/>  <!-- 中间色：H=180 teal，L=27% -->
  <stop offset="100%" stop-color="#2F9A47"/>
</linearGradient>
```

中间色 `#1A6E6E` 由两端色相平均（H205+H138=171°，取整 180° 以获得更纯正 teal）计算得出，防止过渡时出现棕灰色泥浆。

**80% 平涂法则**：下列元素**始终使用平涂**，禁止渐变：
- 所有数据表格单元格
- 图标背景圆/方
- 图表柱/线/面
- 小 chip/标签
- 正文文字容器
- 分隔线

渐变**仅用于**：(a) 封面整页背景，(b) 主要章节条/标题栏，(c) 每页一个 hero KPI 数字（可选，全本仅 1 次）。

### 3.4 渐变文字 — 精确使用条件

```xml
<!-- 仅在满足全部条件时使用：字号≥32px，单页唯一，1–4字/单词 -->
<defs>
  <linearGradient id="textGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"  stop-color="#005792"/>
    <stop offset="100%" stop-color="#2F9A47"/>
  </linearGradient>
</defs>
<text font-size="72" font-weight="700" fill="url(#textGrad)"
      letter-spacing="-1.5">47%</text>
```

条件：(1) 字号 ≥ 32px；(2) 每页唯一使用；(3) 内容为 1–4 字或单数字；(4) 全本最多用于封面和一个中段 hero 页，**不是**每页标题。

### 3.5 投影 — 纵深等级系统

```xml
<defs>
  <!-- alt1: 卡片轻微浮起 -->
  <filter id="alt1" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="4"
                  flood-color="#003D66" flood-opacity="0.10"/>
  </filter>

  <!-- alt2: 重要标注框 -->
  <filter id="alt2" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="4" stdDeviation="8"
                  flood-color="#003D66" flood-opacity="0.14"/>
  </filter>

  <!-- alt3: Hero 封面/模态框 -->
  <filter id="alt3" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="6" stdDeviation="14"
                  flood-color="#003D66" flood-opacity="0.18"/>
  </filter>
</defs>
```

投影规则：
- `flood-color` **永远是** `#003D66` 或 `#00223A`（品牌 shade），**绝不用** `#000000`——黑色投影是 clip-art 信号
- `dx=0`：光源正上方，扁平专业风格
- `stdDeviation = dy × 2`（2倍关系）
- 每页使用 alt1 的元素 ≤ 3 个；同一页不混用多个 alt 等级（一页用一个等级）

### 3.6 颜色语义单职责

| 颜色 | 唯一职责 | 绝不用于 |
|------|---------|---------|
| `#005792` | 结构/权威（头条、导航条、主数据系列） | 正向增长提示 |
| `#2F9A47` | 正向结果/增长/CTA | 装饰性边框、背景底色 |
| `#7AAFD4` | 次要数据/支撑说明 | 主要强调 |
| `#C0392B` | 负向/警告（专用于痛点/负指标） | 品牌装饰 |
| `#C47A10` | 风险/待关注 | 品牌色代替 |

### 3.7 fill-opacity 的安全用法

```xml
<!-- ✅ 安全：白色叠加在深色背景上制造磨砂面板 -->
<rect fill="white" fill-opacity="0.10" rx="4" .../>

<!-- ✅ 安全：使用预混实色代替半透明品牌色叠加白底 -->
<!-- 15% #005792 叠白底 = RGB(216,232,242) = #D8E8F2 -->
<rect fill="#D8E8F2" rx="4" .../>

<!-- ❌ 危险：品牌色半透明叠加非白背景，输出颜色不可预测 -->
<rect fill="#005792" fill-opacity="0.15" .../>  <!-- 底色决定结果 -->
```

---

## 4. 网格与构图

### 4.1 8px 原子网格

1280×720 画布坐标系规则：

| 参数 | 值 |
|------|---|
| 安全区外边距 | 左=右=64px，上=48px，下=56px |
| 内容活跃区 | x: 64–1216，y: 98–664 |
| 列宽（12 列） | 74px（列） + 24px（沟槽）= 98px/单元 |
| 6 列模式单列宽 | 172px |
| 基线网格步长 | 24px（18px × 1.33） |
| 最小可接受间距 | 16px（内容区块间） |
| 子元素内边距 | 4px（微调） |

**所有** `x`/`y`/`width`/`height`/`rx` 值必须是 8 的倍数（或 4 的倍数作为微调）。禁止 `y='147'`，改为 `y='144'`。

### 4.2 光学中心（非几何中心）

720px 高度的光学中心 ≈ y=330（46%，非 50%=360）。Hero 内容顶边 = `(720 - H) × 0.46`：

```
一个 120px 高的数字块：顶边 y = (720-120) × 0.46 = 276px（非 300px）
单行 Hero 文字基线：y=300（非 y=360）
```

### 4.3 不对称分割 — 38/62 与 33/67

```xml
<!-- 38/62 黄金比例分割（1152px 活跃区） -->
<!-- 左窄列：437px 放序号/品牌/callout -->
<rect x="64"  y="98" width="437" height="566" fill="#E8F2F9" rx="0"/>
<!-- 右宽列：691px 放主要内容/图表/正文 -->
<rect x="525" y="98" width="691" height="566" fill="none"/>

<!-- 33/67 三分法分割 -->
<!-- 左：374px；右：754px -->
```

**主要信息永远在宽列**；窄列用于：序号标签、品牌色竖条、单个 callout 数字、辅助插图。

### 4.4 左脊锚点 — 全本视觉连贯

```xml
<!-- Option A：4px 左侧品牌脊线（每页一致，零空间成本） -->
<rect x="56" y="48" width="4" height="616" fill="#005792"/>

<!-- Option B：顶部标题栏（标题内嵌白字） -->
<rect x="0" y="0" width="1280" height="48" fill="#005792"/>
<text x="64" y="34" font-size="20" font-weight="700"
      fill="white" font-family="Microsoft YaHei,sans-serif">示例 · 平台名称</text>
```

不要在同一页同时使用 A 和绿色竖条——两个竖条方案互斥。

### 4.5 Z 形扫描布局（数据页标准）

1280×720 数据图表页的 4 个区域对应读者眼球 Z 轨迹：

| 区域 | 坐标 | 内容 | 字号 |
|------|------|------|------|
| 左上（进入） | x=64 y=48 w=620 h=40 | 行动标题（断言式） | 28px/700 |
| 右上（上下文） | x=720 y=48 w=496 h=40 | 数据来源/时间范围 | 12px/400，右对齐 |
| 中央（主视） | x=64 y=108 w=760 h=490 | 图表/信息图 | — |
| 左下（结论） | x=64 y=618 w=640 h=34 | 关键洞察（4px×16px 绿色前缀矩形） | 16px/400 |
| 右下（导航） | x=960 y=618 w=256 h=34 | 页码+文件名 | 12px/400，右对齐 |

### 4.6 圆角纪律

| 元素类型 | `rx` 值 |
|---------|--------|
| 大面积背景面板 | 0（绝对平，政企感） |
| KPI 卡片/高亮框 | 3 |
| 图标背景方块 | 4 |
| Pill 标签/状态 badge | 10（真正 pill 形：= 元素高度/2） |
| 注释 tooltip 框 | 2 |
| 进度条 | 2 |

**绝不使用** `rx=8`、`rx=12`、`rx=16`——这些值读来像 SaaS 产品 UI。

### 4.7 线条字重体系 — 5 档笔触

| 粗细 | 用途 | 颜色 |
|------|------|------|
| 0.5px | 表格行分隔（`stroke-dasharray="4 4"` 可选）、网格背景线 | `#C5DCEE` |
| 1px | 图表坐标轴 tick、次要数据标签边框 | `#005792` 或 `#7AAFD4` |
| 1.5px | 折线图主数据线、坐标轴 | `#005792` |
| 2px | 内容区块分隔规则线、页脚分隔线 | `#005792` |
| 3px | 章节标题下划线、两列分隔线 | `#005792` |
| 4px | 左侧品牌脊线 | `#005792` |

**禁止** 2.5px、3.5px 等非 0.5 倍数值——产生渲染锯齿。

---

## 5. 纵深与材质

### 5.1 纵深层次模型（4 层）

| 层 | 亮度范围（L值） | 元素 | SVG 填色 |
|----|--------------|------|---------|
| L1 结构层 | 10–30% | 标题栏、导航条、主数据系列 | `#005792`, `#003D66` |
| L2 容器层 | 85–95% | 卡片底色、浅色面板 | `#E8F2F9`, `#F7F8FA` |
| L3 正文层 | 15–22% | 主要文字 | `#003D66` |
| L4 元数据层 | 45–60% | 注释、轴标签、脚注 | `#3A7FAF`, `#5A6B7B` |

L3 用 `#003D66`（非纯黑）：纯黑 `#000000` 读起来像打印稿，深海军蓝更贴合屏幕呈现。

对比度验证：L3 `#003D66` 在 L2 `#E8F2F9` 上 ≈ 9.4:1（远超 WCAG AA 4.5:1）。

### 5.2 背景质感（非纯白）

```xml
<!-- 极淡纹理层（放在所有内容下方） -->
<rect width="1280" height="720" fill="#F7F8FA"/>
<!-- 斜向色带（opacity 极低，制造质感不喧哗） -->
<line x1="-100" y1="220" x2="1380" y2="-120"
      stroke="#005792" stroke-opacity="0.04" stroke-width="40"/>
<line x1="-100" y1="520" x2="1380" y2="180"
      stroke="#2F9A47" stroke-opacity="0.03" stroke-width="60"/>
<!-- 可选：底部城市/机架天际线 -->
<g fill="#005792" fill-opacity="0.05">
  <rect x="60"  y="664" width="26" height="56"/>
  <rect x="92"  y="648" width="20" height="72"/>
  <rect x="118" y="676" width="30" height="44"/>
</g>
```

### 5.3 卡片材质标准模板

```xml
<defs>
  <filter id="alt1" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="4"
                  flood-color="#003D66" flood-opacity="0.10"/>
  </filter>
  <linearGradient id="gradHeader" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#005792"/>
    <stop offset="100%" stop-color="#003D66"/>
  </linearGradient>
</defs>

<!-- 高级卡片（渐变头栏 + navy 投影 + 无描边） -->
<g>
  <!-- 卡体：无 stroke，只有投影 -->
  <rect x="56" y="150" width="360" height="240"
        rx="3" fill="white" stroke="none" filter="url(#alt1)"/>
  <!-- 标题栏（delta-L=8%，在12%规则内） -->
  <rect x="56" y="150" width="360" height="40"
        rx="3" fill="url(#gradHeader)"/>
  <text x="76" y="176" font-size="16" font-weight="700"
        fill="white" font-family="Microsoft YaHei,sans-serif">卡片标题</text>
  <!-- 角标（序号/单位） -->
  <text x="400" y="172" text-anchor="end" font-size="13"
        fill="white" fill-opacity="0.80">¥/卡</text>
  <!-- 正文区 -->
  <text x="76" y="212" font-size="14" font-weight="400"
        fill="#003D66" font-family="Microsoft YaHei,sans-serif">主说明文字</text>
  <text x="76" y="236" font-size="13" font-weight="400"
        fill="#5A6B7B" font-family="Microsoft YaHei,sans-serif">辅助说明（灰）</text>
</g>
```

---

## 6. 数据可视化 — 去默认化

### 6.1 信息图优先原则

**决策树**：
1. 这组数据能否用**尺寸/面积/位置**直接表达？→ 做信息图（圆环/蜂巢/流带）
2. 需要展示趋势/时序？→ 平滑贝塞尔折线图（去默认坐标）
3. 需要对比类别？→ 去图例化柱图（值直标）
4. 只剩下精确数值表格？→ 设计稿级表格（zebra + hairline + 语义色 chip）

**永远不要**直接使用图表库默认样式输出。

### 6.2 图表去默认化检查列表

| 默认特征 | 高级替换 |
|---------|---------|
| 标准网格线（灰色虚线） | 仅保留 y 轴 0 基线（`stroke="#C5DCEE" stroke-width="0.5"`），其余删除 |
| 独立图例框 | 数据标签直接标注在系列末端/内部 |
| 默认柱图颜色（蓝/橙/绿/红） | 品牌色阶：主系列 `#005792`，次要 `#7AAFD4`，正向标注 `#2F9A47` |
| 平涂面积图 | 面积用渐变（top `#005792` → bottom `#E8F2F9`，`fill-opacity` 渐变） |
| 折线使用折角 | 平滑贝塞尔 `<path d="M... C... S...">` |
| 轴标签用默认 12px 黑字 | `font-size="12" fill="#5A6B7B"` L4 颜色 |
| 基准线无标注 | 基准线 + 右侧小标签 chip：`<rect rx="2" fill="#C47A10"/>` |
| 数据点用默认圆点 | 关键数据点用 `r=5` 品牌色实心圆 + 白色 `r=2` 中心 |
| 标注压在数据图形上（曲线/柱/面） | 标注移到清晰留白区、留间距，绝不遮挡数据；区段标签顶部对齐成行；去重冗余词 |

### 6.3 KPI 值标注（Value-In-Shape）

```xml
<!-- 值标注直接嵌入柱形或气泡内 -->
<rect x="200" y="200" width="80" height="200" fill="#005792" rx="2"/>
<text x="240" y="310" text-anchor="middle"
      font-size="14" font-weight="700" fill="white">47%</text>
```

### 6.4 语义色状态点

```xml
<!-- 状态指示器（绿=正常/红=告警/橙=风险） -->
<circle r="5" fill="#2F9A47"/>   <!-- on-track -->
<circle r="5" fill="#C47A10"/>   <!-- at-risk -->
<circle r="5" fill="#C0392B"/>   <!-- off-track -->
<!-- 绝不使用 fill="green" / fill="red"——浏览器默认色与品牌无关 -->
```

### 6.5 表格设计稿化

```xml
<!-- 表头 -->
<rect x="64" y="140" width="1152" height="40" fill="#005792"/>
<text ... fill="white" font-weight="700">列标题</text>

<!-- 奇数行 zebra -->
<rect x="64" y="180" width="1152" height="36" fill="#F7F8FA"/>
<rect x="64" y="252" width="1152" height="36" fill="#F7F8FA"/>

<!-- 行分隔（hairline，非 #CCCCCC） -->
<line x1="64" y1="216" x2="1216" y2="216"
      stroke="#C5DCEE" stroke-width="0.5"/>

<!-- 状态 chip（替代纯文字"低/中/高"） -->
<rect x="900" y="188" width="56" height="20" rx="10" fill="#E8F5EC"/>
<text x="928" y="202" text-anchor="middle"
      font-size="12" font-weight="600" fill="#2F9A47">正常</text>
```

---

## 7. 图形语言与装饰

### 7.1 图标规范

```xml
<!-- 图标置于品牌色填充圆内，绝不裸放 -->
<circle cx="120" cy="120" r="22" fill="#E8F2F9"/>
<path d="..." fill="#005792"/>  <!-- icon path，尺寸约 20px -->
```

- 图标圆半径：22px（对应 44px 直径，Altitude-1 卡片内）
- 背景：`#E8F2F9`（蓝 tint-1），图标色 `#005792`
- 图标**不使用渐变**（80% 平涂法则）

### 7.2 连接 motif（关系表达）

```xml
<!-- 贝塞尔曲线连接（精致，替代直线折线） -->
<path d="M 200 300 C 350 300, 350 450, 500 450"
      fill="none" stroke="#005792" stroke-width="1.5"/>

<!-- 品牌色虚线（表示「将要发生」或「弱关系」） -->
<path d="M 200 300 L 500 300"
      fill="none" stroke="#7AAFD4" stroke-width="1"
      stroke-dasharray="6 3"/>
```

### 7.3 Chevron 流程（替代「框+→」）

参见 `templates/charts/chevron_process.svg`。核心思路：用闭合多边形 `<polygon>` 表达箭羽，而非 `<rect>` + `marker`。

### 7.4 标题签名条（全本统一）

```xml
<!-- 每页标题下方的渐变短条 — 全本视觉锚点 -->
<text x="64" y="62" font-size="30" font-weight="800"
      fill="url(#gradBrand)" font-family="Microsoft YaHei,sans-serif">
  页面标题（断言式）
</text>
<rect x="64" y="74" width="76" height="6" rx="3" fill="url(#gradBrand)"/>
<line x1="140" y1="77" x2="1216" y2="77"
      stroke="#C5DCEE" stroke-width="0.5"/>
```

---

## 8. 顶级范式拆解

### 8.1 封面页（两分法）

```xml
<!-- 左侧白色半透明文字区 + 右侧深蓝斜切背景 -->
<defs>
  <linearGradient id="coverBg" x1="0" y1="0" x2="0.7" y2="1">
    <stop offset="0%"  stop-color="#005792"/>
    <stop offset="100%" stop-color="#003D66"/>
  </linearGradient>
</defs>
<!-- 全页深蓝背景 -->
<rect width="1280" height="720" fill="url(#coverBg)"/>
<!-- 左侧白色半透明叠加（制造文字区） -->
<rect x="0" y="0" width="700" height="720" fill="white" fill-opacity="0.92"/>
<!-- 眉标 -->
<text x="80" y="260" font-size="12" font-weight="600" letter-spacing="1.4"
      fill="#005792">产品系列 · PRODUCT CATEGORY</text>
<!-- 主标题 -->
<text x="80" y="320" font-size="48" font-weight="700" letter-spacing="-1.0"
      fill="#003D66" font-family="Microsoft YaHei,sans-serif">主标题 · 产品名称</text>
<!-- 品牌签名条 -->
<rect x="80" y="334" width="88" height="6" rx="3" fill="url(#gradBrand)"/>
<!-- 副标题（正文调，fill=#3A7FAF L4） -->
<text x="80" y="372" font-size="18" font-weight="400"
      fill="#3A7FAF" font-family="Microsoft YaHei,sans-serif">
  <tspan x="80" dy="0">一句话价值主张，</tspan>
  <tspan fill="#2F9A47" font-weight="700">三个核心收益</tspan>
  <tspan fill="#3A7FAF">写在这里</tspan>
</text>
```

### 8.2 四卡片价值页（Keystone KPI）

```xml
<!-- 每张卡内：图标平涂圆 + KPI 超大字 + Light 说明 -->
<circle cx="card_cx" cy="card_cy" r="22" fill="#E8F2F9"/>
<!-- 图标路径 fill="#005792" -->

<text x="card_x+20" y="card_kpi_y"
      font-size="64" font-weight="700" letter-spacing="-1.5"
      fill="#005792" font-family="Microsoft YaHei,sans-serif">70%+</text>

<text x="card_x+20" y="card_kpi_y+20"
      font-size="14" font-weight="400"
      fill="#5A6B7B" font-family="Microsoft YaHei,sans-serif">GPU 利用率（行业均值 &lt;30%）</text>
```

### 8.3 矩阵/3×3 表格页（语义 chip + 眉标列头）

```xml
<!-- 列头：眉标风格 -->
<text font-size="12" font-weight="600" letter-spacing="1.4"
      fill="#005792" text-anchor="middle">业务模式</text>
<!-- 列头下 hairline -->
<line stroke="#C5DCEE" stroke-width="0.5" x1="..." x2="..." y1="..." y2="..."/>

<!-- 客户类型 chip：统一蓝 tint 底 + 蓝字 -->
<rect rx="10" fill="#E8F2F9"/>
<text fill="#005792" font-size="12" font-weight="600">政府</text>

<!-- 价值结果 chip：统一蓝 tint 底 + 绿字（语义色来自文字，非背景） -->
<rect rx="10" fill="#E8F2F9"/>
<text fill="#2F9A47" font-size="12" font-weight="600">↑利用率</text>
```

### 8.4 时间轴 Gantt 页（dashed alert 框规范）

```xml
<!-- 告警区域框：无填充，品牌红 dashed 描边，非 emoji -->
<rect rx="4" fill="#FFF5F5" stroke="#C0392B"
      stroke-width="1.5" stroke-dasharray="6 3"
      x="..." y="..." width="..." height="..."/>
<!-- 闪电图标（SVG path，非 emoji） -->
<path d="M8,2 L3,10 H7 L4,18 L13,7 H9 Z" fill="#E85A2A"
      transform="translate(labelX, labelY)"/>
<!-- 说明文字 -->
<text font-size="12" font-weight="700" fill="#C0392B"
      letter-spacing="0.5">错配=买长用短</text>
```

---

## 9. 廉价信号清单（反模式）

逐条对照，命中即触发重做：

| # | 反模式 | 诊断信号 |
|---|-------|---------|
| 1 | **标题默认 letter-spacing=0** | ≥28px 的标题没有负间距，看起来「Word 导出感」 |
| 2 | **黑色投影** | `flood-color="#000000"` 出现 → clip-art 信号 |
| 3 | **非系统字号** | 17/19/20/24/29px 出现 → 断裂比例关系 |
| 4 | **CJK 行高 1.2–1.3×** | `dy` ≈ 1.2 × 字号 → 汉字行笔画粘连 |
| 5 | **无眉标的标题页** | 标题直接开始，无 12px 眉标前导 → 缺少进入层 |
| 6 | **全渐变（每个图标都有渐变）** | 3+ 渐变面/元素并存 → 视觉噪音，渐变失去语义 |
| 7 | **外来灰色** | `fill="#CCCCCC"`, `#F5F5F5"`, `#888888"` → 断开色彩逻辑 |
| 8 | **绿色滥用** | 绿色出现在边框+底色+数据+图标（4处）→ 失去强调语义 |
| 9 | **品牌双色无中间停色** | `#005792`→`#2F9A47` 两停 → 中间出现浑浊棕灰 |
| 10 | **渐变文字在每页标题** | `fill="url(#grad)"` 出现在每页 30px 标题 → 2007 年风格 |
| 11 | **不对称列中主信息在窄列** | 主标题/主图在窄侧，辅助内容在宽侧 → 读者进入顺序错误 |
| 12 | **`fill="red"` / `fill="green"`** | 浏览器命名色与品牌色无关 |
| 13 | **所有文字同色同重（400/#333333）** | 无字重跨越，层次靠字号单独承载 |
| 14 | **分隔线 `stroke="#CCCCCC"`** | 外来灰，不属于品牌色阶 → 用 `#C5DCEE` |
| 15 | **`fill-opacity` 叠在非白底** | 输出颜色取决于底层 → PPTX 导出颜色不可控 |
| 16 | **emoji 图标** | `⚡` `🔥` `✓` 直接写入文字 → 字体渲染不稳定，非 SVG 元素 |
| 17 | **直线折线连接关系** | 用 `<line>` 表达关系 → 用贝塞尔 `<path C...>` 替代 |
| 18 | **5+ 字号/3+ 字重/4+ 颜色 per 页** | 超出 3/2/2 天花板 → 每个选择失去信号意义 |

---

## 10. Premium 落地规格（可复制 SVG defs 与模式）

### 10.1 完整共享 defs（每页 `<defs>` 内必须包含）

```xml
<defs>
  <!-- ── 品牌渐变 ── -->
  <!-- 品牌双色（3停色，防浑浊中间） -->
  <linearGradient id="gradBrand" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#005792"/>
    <stop offset="40%"  stop-color="#1A6E6E"/>
    <stop offset="100%" stop-color="#2F9A47"/>
  </linearGradient>

  <!-- 卡片标题栏（delta-L=8%，在12%规则内） -->
  <linearGradient id="gradHeader" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#005792"/>
    <stop offset="100%" stop-color="#003D66"/>
  </linearGradient>

  <!-- 封面背景（35°对角，delta-L=8%） -->
  <linearGradient id="gradCover" x1="0" y1="0" x2="0.7" y2="1">
    <stop offset="0%"   stop-color="#005792"/>
    <stop offset="100%" stop-color="#003D66"/>
  </linearGradient>

  <!-- 强调 chip（亮色） -->
  <linearGradient id="gradChip" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#1E6FA8"/>
    <stop offset="100%" stop-color="#2F9A47"/>
  </linearGradient>

  <!-- 渐变文字（仅 hero 数字专用，全本 ≤1处） -->
  <linearGradient id="gradText" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#005792"/>
    <stop offset="100%" stop-color="#2F9A47"/>
  </linearGradient>

  <!-- ── 投影等级 ── -->
  <!-- alt1: 卡片轻浮 -->
  <filter id="alt1" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="4"
                  flood-color="#003D66" flood-opacity="0.10"/>
  </filter>

  <!-- alt2: 重要标注框 -->
  <filter id="alt2" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="4" stdDeviation="8"
                  flood-color="#003D66" flood-opacity="0.14"/>
  </filter>

  <!-- alt3: 封面 Hero 面板 -->
  <filter id="alt3" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="6" stdDeviation="14"
                  flood-color="#003D66" flood-opacity="0.18"/>
  </filter>
</defs>
```

### 10.2 调色板快查

```
主结构：#005792   正文：#003D66   元数据：#3A7FAF / #5A6B7B
正向强调：#2F9A47  浅卡底：#E8F2F9  发灰线：#C5DCEE
页面背景：#F7F8FA  风险：#C47A10   负向：#C0392B
深背景：#00223A（仅投影 flood-color 使用）
```

### 10.3 标题区标准模板

```xml
<g id="page-header">
  <!-- 眉标 -->
  <text x="64" y="56" font-family="Microsoft YaHei,sans-serif"
        font-size="12" font-weight="600" letter-spacing="1.4"
        fill="#005792">页面类别 · PAGE CATEGORY</text>
  <!-- 主标题（36px/700/-0.72） -->
  <text x="64" y="96" font-family="Microsoft YaHei,sans-serif"
        font-size="36" font-weight="700" letter-spacing="-0.72"
        fill="#003D66">断言式页面标题</text>
  <!-- 签名条 -->
  <rect x="64" y="108" width="80" height="5" rx="2" fill="url(#gradBrand)"/>
  <!-- 贯通浅线 -->
  <line x1="152" y1="111" x2="1216" y2="111"
        stroke="#C5DCEE" stroke-width="0.5"/>
</g>
```

### 10.4 字号/字重/颜色参数速查

```
body-size=18    body-weight=400  body-color=#003D66   body-dy=30
title-size=36   title-weight=700 title-color=#003D66  title-ls=-0.72
eyebrow-size=12 eyebrow-weight=600 eyebrow-color=#005792  eyebrow-ls=+1.4
caption-size=13 caption-weight=400 caption-color=#5A6B7B
kpi-size=64-72  kpi-weight=700  kpi-color=#005792   kpi-ls=-1.5
kpi-label-size=14 kpi-label-weight=400 kpi-label-color=#5A6B7B
```

---

## 11. 组件级规范（逐组件 anatomy + do/don't）

> 这一节把「页面级范式」下沉到「组件级」——每个组件的精确结构与禁忌。Executor 写每个卡片/表格/chip 时按此对照。

### 11.1 卡片 — 视觉权重单一法则（最常违反）

**一个容器只能用一种"抬升"手段**：阴影 **或** 描边 **或** 渐变底 **或** 重色底——**四选一，绝不叠加**。叠加（阴影+描边）= 立刻的"模板感/廉价感"。

| 卡片场景 | 用哪一种 | 禁止 |
|---|---|---|
| 浮在图片/浅底上的卡 | 仅 **navy 柔投影**（`#003D66`，无 stroke） | 投影 + 描边同时 |
| 纯白底上的平级网格卡 | 仅 **0.5px hairline 描边**（`#C5DCEE`，无投影） | 描边 + 投影同时 |
| 需要强调的单卡 | 仅 **渐变标题栏** 或 **重色底**（其余卡保持平） | 每张卡都渐变 |

```xml
<!-- ✅ 浮动卡：只有阴影，无描边 -->
<rect x="64" y="200" width="268" height="372" rx="4" fill="#FFFFFF" fill-opacity="0.94" filter="url(#cardFloat)"/>
<!-- ❌ 阴影 + 描边叠加（删掉 stroke） -->
<rect ... fill="#FFFFFF" stroke="#C5DCEE" filter="url(#cardFloat)"/>
```

### 11.2 卡片内部 — 减元素法则

1. **删装饰序号**：4 张并列卡不证自明，右上角 `01/02/03` 是不承重的装饰噪声 → **删**。仅当序号承载真实顺序语义（步骤/排名）时保留。
2. **删元标签**：`实证支撑` / `说明` / `详情` 这类**无信息量的标题词**会凭空多出一档字号、让卡片"字看起来很多" → **删**，让正文直接说话（必要时用一条 0.5px hairline 分隔即可）。
3. **每卡字号 ≤ 3 种**：典型 = 卡标题(16) + KPI 大数字(40–56) + 说明/实证(14)。每多一档字号都要"挣到"理由。
4. **图标-文字光学对齐**：图标圆**圆心** 与 标题文字**视觉中线** 必须共一条水平线。

```xml
<!-- 图标圆心 cy=250 ＝ 标题视觉中线；title baseline=center+6 -->
<circle cx="106" cy="250" r="22" fill="#E8F2F9"/>
<use data-icon="tabler-outline/gauge" x="94" y="238" width="24" height="24" fill="#005792"/>
<text x="140" y="256" font-size="16" font-weight="700" fill="#005792">利用率优</text>
```

### 11.3 KPI 卡 — Keystone + 留白

- 大数字 40–72px/700，说明 14px/400，比 ≥ 3:1；数字色用结构蓝 `#005792`，仅小号实证里的"正向 delta"（`+40%`/`-50%`）用品牌绿。
- 卡内容**整体偏上**，底部留 80–120px 呼吸空白（keynote 感），不要塞满。

### 11.4 chip / 标签

- **平涂** `#E8F2F9` 底 + `#005792` 字；真 pill 形 `rx = 高度/2`（h24 → rx12）。
- **语义靠文字色，不靠底色**：价值/正向 chip 仍 `#E8F2F9` 底，把文字改 `#2F9A47`；不要做成绿底。
- chip 不加投影、不加渐变（80% 平涂法则）。

### 11.5 表格

- 表头 `#005792` 深底白字；**只画横向 hairline**（`#C5DCEE` 0.5px），不画竖向满格线；奇数行 `#F7F8FA` zebra。
- 定性状态用 **chip**（`正常`/`风险`）替代纯文字；数字右对齐、文字左对齐。
- 禁外来灰 `#CCC/#888/#F5F5F5`，一律用品牌色阶。

### 11.6 重点结论 — 必须落进容器（Takeaway 锚）

孤立漂浮在页面底部的一行结论 = "不合群/没落地"。**重点结论必须有填充背景锚住它**：

```xml
<!-- navy 填充 takeaway 条（pill 或 rx4），白字，关键词浅色高亮 -->
<rect x="360" y="618" width="560" height="44" rx="22" fill="#003D66" filter="url(#cardFloat)"/>
<text x="640" y="646" text-anchor="middle" font-size="16" fill="#FFFFFF">
  P11 的<tspan fill="#F2B8B0" font-weight="700">三低</tspan>，到此翻成<tspan fill="#A8E6B8" font-weight="700">三优</tspan></text>
```

> navy 底上的红/绿要用**浅色变体**（`#F2B8B0` / `#A8E6B8`）才有对比；深色语义色在深底上会糊。

### 11.7 image-canvas 页（keynote 大图页）

- **hero 大图铺底/占一侧** + **浮动磨砂卡**（白 0.92–0.94 + navy 阴影、**不描边**）+ 大字 + 巨留白。
- **文字永远是 SVG 叠层，绝不烤进图**——拿 keynote 的脸、保政企的可编辑准确。
- 标题区需要在图上读清时，叠一层 `#F7F8FA` 0.4–0.6 的局部 scrim，而非全图压暗。
- **每页构图不同**：满版 hero / 左右编辑 / 居中产品 / 第一视角，避免同骨架复读。

### 11.8 标题区（全本统一）

`eyebrow(12/600/+1.4/#005792) → 主标题(36/700/-0.72/#003D66) → 签名渐变条(80×5) → 副标题(16/400/#5A6B7B)`，断言式标题优先于描述式。

---

### 11.9 元素一致性与跨页呼应

同一 deck 内**重复出现的同类元素必须同款**，形成系统感：
- **统一圆角**：卡片 / 容器 / 强调条用同一 `rx` 档；不要上面小圆角矩形、下面大圆角胶囊混用。
- **统一收边方式**：标题栏 / 强调条的渐变收尾一致（如同款「左右淡出」），不要一处实心、一处淡出。
- **统一边距与对齐**：同层元素的左右边界、间距对齐到同一网格。
- **跨页呼应**：标题区 / 价值条 / 章节元素等跨页同类元素，全 deck 用同一套样式与位置——读者翻页时感到「同一系统」，而非每页另起炉灶。

> 自检：相邻几页并排，重复元素是否「一眼同款」？某元素的圆角 / 渐变 / 收边是否与它呼应的元素一致？

---

### 11.10 图标质量标准

- **必有容器**：图标不裸放——置于 tint 圆 / 渐变栏 / chip 内；裸的细描边线图标在大屏上显单薄、廉价。
- **足够分量**：主视觉图标用 filled / duotone，或描边图标但放进实色 / tint 容器；深色栏上用白色图标。
- **全 deck 单一风格库**：一套 deck 只用一个图标库（粗细、转角、留白一致）；品牌 logo 例外。
- **光学对齐与配额**：图标圆心与相邻文字视觉中线共线；图标尺寸成体系（如容器直径同档），不逐页随意。

### 11.11 配图与高质量图标准

- **三类用途，按需选**：① **hero 大图**（封面 / 章节 / 轻页：图即主体，大字浮于其上）② **氛围底图**（内容页极淡铺底，文字在上可读）③ **局部配图**（一块区域的场景 / 实物，矢量画不出的才用图）。
- **AI 图全 deck 同调**：同一 deck 的 AI 图统一 rendering（质感）+ palette（主题色），像一个人拍的一套；高分辨率（≥ 画布 2×）。
- **文字永不烤进图**：所有标题 / 数据 / 标签为 SVG 叠层，图只承载氛围 / 场景；图上压字时加局部 scrim 保可读。
- **image-as-canvas 优先**：内容页若用图，让图作画布、原生元素（卡 / 节点 / 标注）叠其上，而非图文各占一半的呆板分栏。
- **忌**：clip-art、廉价 stock、光污染（霓虹 / 满屏发光）、与主题无关的装饰图。

---

## 12. 制作流程 & 导出前视觉 QA 清单

### 12.1 制作流程（每页动笔前）

1. **声明配额**：字号 ≤3 / 字重 ≤2 / 文字色 ≤2（眉标可第三色）。写在心里，超了就返工。
2. **铺 8px 网格**：所有 `x/y/w/h/rx` 取 8（或微调 4）的倍数；安全边距 64/48/56。
3. **定 hero 与构图**：这页主角是什么（大图 / 大数字 / 信息图 / 表）？构图选哪种（满版 / 左右 / 居中 / Z）？避免与相邻页同骨架。
4. **填载体**：手画 SVG / 图表（去默认化）/ 原生图示 / 配图，按需。
5. **叠 SVG 文字层**：眉标→标题→正文→takeaway，关键词选择性换色。

### 12.2 导出前视觉 QA 清单（逐条勾，命中即改后再导出）

**排版**
- [ ] 所有字号属系统阶梯（12/14/18/22/28/36/44/52–72），无 17/19/20/24/29/30/34
- [ ] ≥28px 标题已加负字间距（36→-0.72，44→-1.0，56→-1.2）
- [ ] 多行 CJK 正文 dy = 字号×1.7（18→30）
- [ ] 每页眉标三级进入（eyebrow→title→body）齐全
- [ ] 单页字号 ≤3 / 字重 ≤2 / 文字色 ≤2

**组件**
- [ ] 卡片**视觉权重单一**：阴影/描边/渐变/重底只用其一，无叠加
- [ ] 无装饰性序号、无"实证支撑/说明"类元标签
- [ ] 图标圆心与标题视觉中线对齐
- [ ] chip 平涂、真 pill（rx=h/2）、语义靠文字色
- [ ] 表格只横向 hairline、无外来灰、状态用 chip
- [ ] 重点结论已进填充容器（无孤立漂浮文字）

**色彩 / 纵深**
- [ ] 投影 `flood-color=#003D66`（非黑）、opacity ≤0.14、`dx=0`
- [ ] 渐变只在结构层（卡头/封面/价值条/1 个 hero）；图标/数据/chip 全平涂
- [ ] 颜色单职责：蓝=结构、绿=正向结果(≤蓝面积)、红=痛点专用；无 `fill="red/green"`、无 `#CCC/#888/#F5F5F5`
- [ ] 品牌双色渐变为 3 停色（中停 `#1A6E6E`）

**载体 / 图**
- [ ] 数据图已去默认化（去满格网格/独立图例/折角，值直标、平滑贝塞尔、hairline 轴）
- [ ] image-canvas 页文字为 SVG 叠层（未烤进图），构图与相邻页不同
- [ ] 无 emoji（用 SVG path）、关系用贝塞尔曲线非直折线

**技术安全（导出不崩）**
- [ ] 无 `mask`/`foreignObject`/`<g opacity>`/`rgba()`/HTML 实体；XML 保留字已转义
- [ ] `svg_quality_checker.py` 0 error

> 这份清单是 [executor-base.md](../../skills/ppt-master/references/executor-base.md) Quality Check Gate 的**视觉前置**：先过 §12 视觉自检，再跑 `svg_quality_checker.py` 技术自检。

---

## 13. 反馈进化机制（让规范越用越高级）

> 目标：把真实项目里的视觉反馈，沉淀成**通用的设计 / 排版 / 布局 / 美化经验**，让后续每份 deck 站在前人肩上。**沉淀对象是 brand- 与 content-agnostic 的原则**，不是某一份 deck 的具体色值 / 元素 / 文案。

### 13.1 沉淀原则（怎么记，比记什么更重要）

1. **只记通用经验**：记可迁移到任意主题、任意行业的设计原则；**不记具体色值（HEX）、具体元素 id、具体文案、页码、deck 名**——这些一旦进通用规范，换场景复用即被污染。
2. **具体归项目层**：某 deck 的调色板、可复用元素定义、认可的成品页 → 落在该项目的 `spec_lock.md` 与 §13.3 exemplars，**不进本通用文档**。（本文档中带具体 HEX 的 §3.1 / §10 仅为「示例实例化」，原则部分应保持 brand-agnostic。）
3. **落前先论证**：每条经验入库前，先做必要的调研 / 比对（与设计常识、参考标杆、现有规则对照），确认其**普适性与正确性**，再下笔。
4. **有机融合，不堆叠**：新经验优先**融进相应正文章节**（§1–§12）——精炼、去重、与既有规则合并或细化；§13.2 只留一行**抽象变更摘要 + 指向章节**，不复制细节。
5. **冲突取新**：与旧规则冲突时以新反馈为准，标注覆盖了哪条，并同步改正文（单一事实源）。
6. **触发**：用户说「记下来 / 形成规范」或每次收尾默认执行一次（可 `/ppt-feedback`）。

### 13.2 变更摘要（抽象原则 · 倒序；细节见所指章节）

- **标注不压数据**：图表 / 曲线 / 柱 / 面的标签文字绝不叠在它标注的数据图形上；放在清晰留白区并留间距，区段标签（如昼/夜）顶部对齐成行、靠近但不遮挡；去重冗余词。→ §6.2
- **配图与图标纳入高级标准**：图标须有容器与足够分量（避免裸细线）、全 deck 单一风格；配图分 hero / 氛围 / 局部三类，AI 图全 deck 同一 rendering+palette、高清、不烤文字、优先 image-as-canvas 叠层。→ §11.10 / §11.11
- **元素一致性与跨页呼应**：同款元素全 deck 统一（圆角 / 渐变收边 / 边距），并跨页呼应同类元素形成系统感；避免同页上下或跨页同类元素风格不一。→ §11.9
- **配色纪律收紧**：单页 ≤3 色（不含黑白）；只用主题色及其 tint / 透明度变体；**禁止为对比临时造新色相**；深底上的强调用主题色的更亮 tint，而非外来色相；色系在「定主题」阶段一次锁定、逐页只取用。→ §3.2 / §3.6 / §1 #8
- **素材「元素级」借鉴优先**：从优质素材抽取可复用元素（标题栏 / 标签 / 序号 / 图形）嫁接到合适版式；**整套照搬只用于内容形态高度吻合的页**，否则显「硬」。→ §11.7
- **卡片要有「分量」**：用结构性元素（如实色→淡出的渐变标题栏）建立层次，避免细描边线图标置于浅色圆的单薄感；图标宜用实色置于深色栏或 filled / duotone。→ §11.1 / §11.2
- **装饰按「是否承重」取舍**：承载信息或秩序的元素（大号序号、机制标签）保留；纯装饰（小角标序号、空元标签如「说明 / 实证」）删除。→ §11.2
- **容器视觉权重单一**：阴影 / 描边 / 渐变 / 重底，四选一，不叠加。→ §11.1
- **重点结论必须入容器**：关键结论落进填充容器（takeaway），不留孤立漂浮文字。→ §11.6
- **宏观先于微观**：高级感主要来自版式 / 图形概念 / 构图多样（image-led、强 hero、留白）；微观工艺（字距 / 行高 / 投影）是地基。→ §0 / §11.7
- **参数随标杆校准**：当客户认可的标杆风格与既有硬值（如圆角）冲突时，以标杆更新参数带，不锁死单一值。→ §4.6

### 13.3 最佳示例库（exemplars/）

- 位置：[`skills/ppt-master/templates/exemplars/`](../../skills/ppt-master/templates/exemplars/)，存放用户**明确认可**的页面 SVG + 一句「为什么它高级」。
- 用法：Executor 起一份新 deck 前，先翻 exemplars/ 找同类页（封面 / KPI 卡页 / 数据图页 / 案例页）作视觉起点，而非从零。
- 维护：每次有新认可页就 append；过时/被更好示例取代的标注 `deprecated`。

---

> 权威技术约束仍以 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) §1–§7 为准；本文件负责把「什么算高级、每个决策的判断依据、每个组件怎么做、导出前查什么、以及如何持续进化」讲清楚。**Executor 手写每页 SVG 前按 §1 Rubric + §11 组件规范自检、翻 §13.3 exemplars 找起点，导出前按 §12 清单逐条过；交付后按 §13.1 把新反馈进化进 §13.2。**
