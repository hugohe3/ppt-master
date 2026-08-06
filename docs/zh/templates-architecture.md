# 模板架构：Brand / Style / Layout / Deck 四分类

[English](../templates-architecture.md) | [Chinese](./templates-architecture.md)

---

> 本文是**架构对齐文档**，定义“模板”在数据模型层面的四种身份、各自的 `design_spec.md` 字段集、以及多路径合成与冲突解决规则。面向贡献者与 AI 工作流，回答“一个模板目录里应该写什么、不写什么；多个模板同时给时怎么合成”。
>
> 用户视角的用法（怎么触发、怎么选）见 [`templates-guide.md`](./templates-guide.md)；本文不重复。

---

## 一、四分类

| 分类 | 全局库工作区根目录 | 写什么 | 不写什么 | 出处工作流 |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | 仅身份段：color / typography / logo / voice / icon style | 不写 canvas、page structure、SVG roster | `workflows/create-template/create-brand.md` |
| **Style** | `templates/styles/<id>/` | 可移植方向/方法段：沟通方法、页面角色词汇、证据/数据表达、视觉默认值、图片/图标方向、审阅关注点 | 不写身份真值、应用契约、canvas、页面结构或 SVG roster | `workflows/create-template/create-style.md` |
| **Layout** | `templates/layouts/<id>/` | 仅品牌中立的结构段：canvas / page structure / 语义文字角色 / page types / SVG roster | 不写品牌身份，也不拥有可重复沟通场景 | `workflows/create-template/create-layout.md` |
| **Deck** | `templates/decks/<id>/` | 一类可重复演示：描述性应用语境 + 一体化身份与结构 | —— | `workflows/create-template/create-deck.md` |

每张新建的 Layout/Deck SVG 都是完整预览，并在根节点声明 Master/Layout key 与选择器名称；固定 Master/Layout 视觉是直接原子元素；语义槽位是顶层 group。普通槽位必须有正数设计区域 bounds 和恰好一个兼容 carrier；复合 `object` 区域走显式 proxy 绑定，零槽 Layout 也合法。这些专用标记具有最高优先级；最小 `data-pptx-role` 只补充它们无法表达的页面框架行为。Create Template 根据自然语言意图与来源证据在内部推导 `standard` / `fidelity` / `mirror`；Strategist 再根据真实原型与当前内容推导 strict/adaptive 导出行为。这些实现值都不是用户必选项。仅 Brand/Layout/Deck 的旧式平铺目录可在满足当前 kind 合同时继续读取；Style 没有平铺兼容形态。带旧结构语义的包必须替换为新建模板工作区，不能原地升级。

四者是**四种并列的可复用规则包**，不是 PowerPoint 包对象类型。在全局库范围内，物理目录与 frontmatter `kind` 字段双向对齐：

多路径合成后的项目级 `design_spec.md` 沿用能力标签：同时具备身份段和结构段时为 `deck`，只有结构段时为 `layout`，只有身份段时为 `brand`，只有方向/方法段时才为 `style`。Style 与其他 kind 合成时不改变原有能力标签。对于项目内临时组合的 Brand + Layout，`kind: deck` 只表示“已安装两种能力”，不会把组合自动提升为可注册的 Deck，也不会凭空生成应用语境；当前项目的 Stage 1 沟通契约负责提供场景。Strategist 在内部生成模板应用计划，确认页不显示模板模式控件。

```yaml
# templates/brands/anthropic/templates/design_spec.md
---
kind: brand
...
---

# templates/styles/consulting_analytical/templates/design_spec.md
---
kind: style
...
---

# templates/layouts/presentation_core/templates/design_spec.md
---
kind: layout
native_structure_mode: structured
...
---

# templates/decks/中国电信/templates/design_spec.md
---
kind: deck
native_structure_mode: structured
...
---
```

### PowerPoint 原生对象是编译目标

项目模板 kind 与 PresentationML 对象不是一一对应关系：

| 项目合同 | 原生投影 |
|---|---|
| **Brand** | Theme 的颜色、字体与效果，以及 Logo 等固定身份资产规则 |
| **Style** | 不提供可复用包结构；已确认的方法和视觉默认值指导 flat Slide-local 创作 |
| **Layout** | Master/Layout/Placeholder 拓扑、可复用几何、语义文字角色与槽位空间行为 |
| **Deck** | Brand 与 Layout 的投影，再加描述性重复应用语境和真实原型 |

一个 Slide Master 可以同时包含结构几何和品牌视觉。来源规则仍分开归属：Layout 决定拓扑、位置、语义文字角色与空间行为，Brand 决定身份值与资产。下游选择 `layout` 时，导出结合已确认的阅读模式和字号体系解析最终 placeholder 格式；选择 `mirror` 时则保留来源的字面格式与文字拓扑。最后再把适用规则编译进同一套 Master/Layout 图谱。因此 Theme 是已解析身份的实现投影——身份可以来自 Brand、Deck 或当前项目——而不是另一种模板 kind；Style 的色彩/字体 fallback 也不是 Theme 身份真值。

### 输出范围与 kind 相互独立

`create-template` 会确认工作区放在哪里。这个执行选择不会增加另一种 kind，也不会增加新的 PPTX 结构模式：

| 范围 | 工作区根目录 | 核心结构 | 发现行为 |
|---|---|---|---|
| `library`（默认） | `skills/ppt-master/templates/<kind>/<id>/` | 必需 `templates/`；可选 `images/`、`icons/` 与按需 `exports/` | 写入对应全局索引 |
| `project` | `projects/<name>/` | 完全相同的路由合同 | 不更新全局索引 |

两种根目录都保持相同的核心形态：

```text
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   └── *.svg
├── images/                     # 可选；SVG 统一引用 ../images/<name>
├── icons/
│   └── imported/               # 可选；导入向量素材的唯一规范副本
└── exports/                    # 可选；用户要求审阅或多 Master 包需要证据时创建
    └── <id>_template_preview.pptx
```

空的可选目录直接省略，不添加占位文件。预览 PPTX 是派生审阅证据，不是模板源资产；单 Master 按需生成，多 Master 必须通过该 package gate。Step 3 读取工作区根目录，只消费 `templates/` 及实际存在的 `images/`、`icons/`，不会复制或使用 `exports/`；全局库下的 `exports/` 统一由 Git 忽略。

导入向量统一使用 `data-icon="imported/<name>"`，唯一规范文件位于 `icons/imported/<name>.svg`。具备工作区感知的校验与导出会直接解析这个根目录路径；`templates/icons/` 不属于模板包结构。

原生形状 metadata 采用两级模型。完整导入 SVG 保存 native metadata、隐藏 carrier 和预览证据，并作为不可变原生载荷后备；`svg_authoring_view.py` 生成可编辑 authoring IR，其中轻量 SVG 使用文档内 source ref 标识对象，manifest 只保存路径和初始 hash。创作模式使用项目规范化 SVG，只有精确匹配已登记 preset 时才使用 compact authored-preset 组。Mirror 从 IR 物化模板，仅为未改且 hash 匹配的 Slide-local/slot ref 重新接入转换器已支持的载荷；固定结构层保持直接原子，不支持或已修改的对象保留 SVG fallback，最终模板不包含 IR 专用 ref。导出只编译声明的结构，不推断归属。

两种范围都在可移植 frontmatter 中保留所选 `kind`。`output_scope` 与 `target_project` 只属于工作流简报，不写入 `design_spec.md`。

任何范围第一次写最终文件前，都必须解析工作区根目录、确认 `templates/` 为空，并检查全部计划写入的图片与图标文件名无冲突；用户要求预览或已确认 roster 含多个 Master 时检查预览 PPTX 目标。项目范围还必须确认目标项目已初始化。任一失败都在写入前停止，不合并、不覆盖。

### 四段的字段切分

为了让多路径合成能干净覆盖，所有字段按段归属，**段级整段替换是默认粒度**：

| 段 | 包含的章节 | 归属（覆盖优先级）|
|---|---|---|
| **身份段** | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand 覆盖 |
| **方向/方法段** | Communication Method / Page Role Vocabulary / Evidence & Data Expression / Visual System Defaults / Image & Icon Direction / Review Focus | style；默认值低于用户确认及身份/结构所有者 |
| **结构段** | 可移植 canvas/page-type 元数据、结构归属的 Signature 规则、SVG Page Roster，以及 SVG Master/Layout/slot 合同 | layout 覆盖 |
| **应用段** | Template Overview：重复场景、受众与结果、交付假设及代表性叙事/页面角色 | deck 独有；brand / layout 不写 |

### 为什么需要 Deck 这一类

Deck 编码的是**一类可重复演示**，而不只是预先组合好的 Brand 和 Layout。它描述模板服务哪些沟通场景、支持哪些受众结果，以及常见的叙事或页面角色。身份与结构围绕这份语境形成一个整体；具体选哪些原型、如何处理内容，由当前 Strategist 决定。

`standard` / `fidelity` 根据已确认的证据创作新完整系统；mirror 把已验证的来源身份与父子关系一对一映射进新工作区。Mirror 能保留来源事实，但不能单独证明来源就是可复用 Deck：创建时仍要识别稳定的应用规则。只得到身份时创建 Brand；方法与视觉方向需要脱离原型复用时创建 Style；得到品牌中立的可复用结构时创建 Layout；结构带品牌身份，或者包含场景叙事与内容语法时创建 Deck。

这也约束创建模式：只有来源合同本身已经品牌中立且应用中立时，Layout mirror 才成立。删除品牌色、字体、Logo、固定身份对象或可复用应用规则都属于重新创作；越过这条边界的来源要么使用 `standard` / `fidelity` 创作新的 Layout，要么保留这些事实并创建 Deck mirror。

---

## 二、各分类的 `design_spec.md` Schema

字段集只规定**必须写**的部分。「非必要不表明」——当前 schema 没列出的字段，不写。

### Brand schema

**Frontmatter**

```yaml
---
brand_id: <slug>
kind: brand
summary: <一句话描述用途，含主色>
primary_color: "<HEX>"
---
```

**正文章节**（身份段全集）

| 节 | 标题 | 必写字段 |
|---|---|---|
| I | Brand Overview | Brand Name / Use Cases / Tone |
| II | Color Scheme | role / HEX / provenance（`fact` 官方真值 \| `approx` 推导）/ notes |
| III | Typography | role / family / weight |
| IV | Logo | file / form / usage + clearspace 与组合规则 |
| V | Voice & Tone | formality / person / emoji / abbreviation 策略 |
| VI | Icon Style | preference（stroke / filled / duotone …）+ 推荐字库 |

**不允许出现**：canvas viewBox、page types、SVG roster——这些是 layout 的职责。

### Style schema

**Frontmatter**

```yaml
---
style_id: <slug>
kind: style
summary: <一句话描述可移植方法与视觉方向>
keywords: [tag1, tag2, tag3]
---
```

**正文章节**（方向/方法段）

| 节 | 标题 | 必写内容 |
|---|---|---|
| I | Style Overview | 名称、宽泛适用语境、复用意图与来源；不绑定受众/结果 |
| II | Communication Method | mode 候选、论证流、页面信息纪律与证据纪律 |
| III | Page Role Vocabulary | 开放角色及其沟通任务、证据义务和构图倾向；不规定顺序/页数 |
| IV | Evidence & Data Expression | 主张/证据、事实/假设/含义/建议区分，以及图表/表格/来源规则 |
| V | Visual System Defaults | visual-style 候选、构图、密度、装饰、节奏及可选色彩/字体 fallback |
| VI | Image & Icon Direction | 渲染、使用与处理方向；不写 inventory 或逐页映射 |
| VII | Review Focus | 仅在用户另行开启 visual review 后追加的检查点 |

Style 不写 SVG，也不拥有 Brand 官方身份、Deck 应用契约、canvas、页数/
顺序、Master/Layout/placeholder 结构或逐页资源。其色彩与字体只是可覆盖
fallback：用户最终确认及 Brand/Deck 身份优先。Review Focus 不能启动
visual review。`kind: style` 表示可复用包类型，区别于 Stage 2 的
`visual_style` 选择和内部 flat 导出值 `template_reuse_scope: style`。

### Layout schema

**Frontmatter**

```yaml
---
layout_id: <slug>
kind: layout
category: general | scenario | government | special
native_structure_mode: structured
summary: <一句话描述用途>
keywords: [tag1, tag2, tag3]
canvas_format: <ppt169 | ppt43 | a4 | ...>
canvas_width: <像素>
canvas_height: <像素>
canvas_viewbox: "0 0 <width> <height>"
source_canvas_width: <像素>       # 已知 PPTX/SVG 来源画布时填写
source_canvas_height: <像素>
source_viewbox: "0 0 <width> <height>"
replication_mode: standard | fidelity | mirror
page_count: <N>
page_types: [<cover, toc, chapter, content, ending, ...>]
---
```

**正文章节**（该包特有的结构段）

| 节 | 标题 | 必写字段 |
|---|---|---|
| IV | Signature Design Elements | 该 Layout 特有的网格、区域、图片行为、密度节奏、中性框架、语义文字角色、对齐/换行/容量行为和 slot 约定 |
| V | Page Roster | 每个 SVG 文件、Layout key、picker name、适用内容与 slot 行为 |

只有 Layout 改写规范占位词汇时才增加 `Placeholder Overrides`。frontmatter
`summary` 承担简短的选型语境；Layout 不写 deck 独有的 Template Overview。

`category: scenario` 只表示发现时的适配标签。Layout 可以针对某种内容形态或交付环境优化几何，但不能规定沟通目的、受众结果、必需叙事顺序、固定措辞或示例内容；如果这些规则也要重复使用，应创建 Deck。

**不允许出现**：Color Scheme、品牌字体家族/字重身份、最终字号体系、品牌 logo、品牌 voice & tone、Icon Style 或官方真值色（`provenance: fact`）。Layout 可以保留语义文字角色、对齐、换行与容量规则，因为它们属于结构；SVG 中性 paint、字体和字号只用于审阅。最终色彩与字体由策略师确认阶段或其他模板 kind 解析。

### Deck schema

**Frontmatter**

```yaml
---
deck_id: <slug>
kind: deck
category: brand | general | scenario | government | special
native_structure_mode: structured
summary: <一句话描述可重复演示类型与预期结果>
keywords: [tag1, tag2, tag3]
canvas_format: <ppt169 | ...>
canvas_width: <像素>
canvas_height: <像素>
canvas_viewbox: "0 0 <width> <height>"
source_canvas_width: <像素>       # 已知 PPTX/SVG 来源画布时填写
source_canvas_height: <像素>
source_viewbox: "0 0 <width> <height>"
replication_mode: standard | fidelity | mirror
page_count: <N>
primary_color: "<HEX>"
---
```

**正文章节**（应用契约 + 一体化身份/结构）

| 节 | 标题 | 归属段 |
|---|---|---|
| I | Template Overview | 应用段 |
| II | Color Scheme | 身份段 |
| III | Typography | 身份段；只有使用共享默认字体栈时才省略 |
| IV | Signature Design Elements | 模板特有的身份图形与可复用结构语法 |
| V | Page Roster | 结构段 |
| VI | Assets | 身份/支撑资产；无资产时省略 |
| VII | Placeholder Overrides | 结构词汇；无覆盖时省略 |

Template Overview 写明可重复演示类型、目标受众与结果、交付/阅读假设及代表性叙事或页面角色。Page Roster 只需如实描述每个原型的 Master/Layout/slot 合同、视觉特征、用途和容量，不得添加必需/可选/可重复或固定/可替换/仅示例政策；当前 Strategist 会按实际内容推导这些决定。

可移植 canvas 字段、`page_count` 和显式 SVG roster 承载其余结构合同。通用间距、字号比例、SVG 和 placeholder 规则保持集中管理，不复制进每个 deck spec。省略条件章节只表示“采用共享默认值或没有资产”，不表示该段改由其他 kind 所有。

---

## 三、四套 index 文件

每个 index 跟物理目录一一对应，字段按需精简，沿用 [`charts_index.json`](../../skills/ppt-master/templates/charts/charts_index.json) 的紧凑“meta + summary”模式，同时保留对 Strategist 选型有用的结构化元数据。

四套索引只覆盖全局库范围。项目根工作区有意不进入任何索引，仍可通过显式 `projects/<name>/` 路径使用。因为两种范围采用相同工作区形态，完整核心工作区可在两者之间移动或复制，不需要重写素材路径；只有全局库注册不同。

### `templates/brands/brands_index.json`

```json
{
  "<brand_id>": {
    "summary": "Anthropic brand identity — AI/LLM tech talks, developer conferences",
    "primary_color": "#D97757"
  }
}
```

- 保留 `primary_color` —— Strategist 选 brand 时第一眼就要知道主色
- 去掉 keywords —— summary 自带英文等价词，AI 用自然语言匹配（沿用 charts 经验）

### `templates/styles/styles_index.json`

```json
{
  "<style_id>": {
    "summary": "Answer-first、证据驱动的决策文档默认值，不含页面原型或品牌身份",
    "keywords": ["consulting", "decision-support", "evidence"]
  }
}
```

- 保留 `keywords`：方法/方向没有结构 roster，发现主要依赖语义
- 不写 canvas、page count 或 primary color；Style 不拥有结构或身份真值

### `templates/layouts/layouts_index.json`

```json
{
  "<layout_id>": {
    "summary": "Standard academic defense layout — cover/toc/chapter/content/ending",
    "canvas_format": "ppt169",
    "page_count": 5,
    "page_types": ["cover", "toc", "chapter", "content", "ending"]
  }
}
```

- 加 `canvas_format` / `page_count` / `page_types` —— Strategist 选 layout 时要快速判断"页面骨架能不能装下我的 deck"
- 无 `primary_color` —— layout 无身份

### `templates/decks/decks_index.json`

```json
{
  "<deck_id>": {
    "summary": "中国电信政企方案说明与下一步对齐汇报",
    "canvas_format": "ppt169",
    "page_count": 5,
    "primary_color": "#XXXXXX"
  }
}
```

- 含 `primary_color`（deck 自带身份）+ 结构元数据
- `summary` 优先描述可重复演示类型与预期结果，而不只是视觉气质
- 详细应用契约留在 Template Overview；紧凑索引不重复整份契约

---

## 四、多路径合成与冲突解决

### 片段所有权（隐式触发）

用户确认已注册和/或指定工作区根目录后，Step 3 会解析每个 root 的真实
`kind`，再分片段写入一份 `<project>/templates/design_spec.md`。
`library` / `explicit` 只记录发现来源，不改变所有权：

| 片段 | 起始所有者 |
|---|---|
| 身份 | Brand，其次 Deck，否则留到 Stage 2；Style 只提供 fallback 候选 |
| 方向/方法 | Style，否则留到 Stage 2；Deck 的真实原型与 Signature 事实只提供兼容性依据 |
| 结构 | 兼容 Layout，其次 Deck，否则留到 Stage 2 / 自由设计 |
| 可复用应用语境 | 仅 Deck；保留供 Stage 2 对照，绝不充当当前项目的应用契约 |

用户当前明确指令和最终确认高于所有起始所有者。Brand 身份高于 Style
的色彩/字体 fallback。Style-only 或 Style + Brand 使用 flat 创作；Style
与 Layout/Deck 合成时沿用所选结构源。Style 自身不升级或降级结构。

Layout 覆盖 Deck 前，必须把 Deck 的可复用应用角色与 Layout 的页面角色、
槽位类型和容量对照；Style 与 Layout/Deck 合成前，也要确认其沟通方法和
构图预期能够被该可复用语境与结构兑现。不兼容时显式报告模板片段冲突，
不能静默混合字段或保留一份当前结构无法兑现的承诺。当前项目的适配只在
Stage 1 确认后的 Stage 2 开始。

### 段级整段替换（默认粒度）

合成默认是**段级整段替换**——例如 deck + brand 时，整个 Color Scheme / Typography / Logo / Voice / Icon Style 五段从 brand 拿，**不做字段级混搭**（即不会发生"primary 从 brand 拿、secondary 从 deck 拿"这类隐式混合）。

字段级微调走 策略师确认阶段这条已有路径——用户在 chat 里说"用 anthropic brand，但 primary 改成 #FF0000"，由 Strategist 在 e/g 现场调整，不在 Step 3 的 fusion 层加字段级语法。

### 同类多份 = git 冲突解决

用户给 `brands/anthropic` + `brands/google`（同类多份的任意排列组合）：

```
AI: 你给了两个 brand，检测到段级冲突：
    - Color Scheme（Anthropic 橙红 vs Google 多色）
    - Typography（Styrene/AnthropicSans vs GoogleSans/Roboto）
    - Logo（Anthropic 标 vs Google 标）
    - Voice & Tone（restrained vs friendly）
    - Icon Style（stroke vs filled）

    要 (a) 全部按 Anthropic / (b) 全部按 Google / (c) 逐段挑？
```

- 默认无隐式顺序，所有冲突都问
- 仅在用户选 (c) 才进入逐段问答；不做字段级冲突解决
- `style × 2`、`layout × 2`、`deck × 2`、`brand × 2` 同处理
- 每类最多两份（再多让用户先在 chat 里收敛）

默认页面已经把组合空间收窄：Brand/Style/Layout/Deck 各有一个已注册模板
单选下拉框，另有一个指定地址下拉框；指定地址按解析出的 kind，最多给该类
增加第二份。服务端强制同一限制；聊天组合仍保留每类最多两份的通用边界。

### Provenance 记录

合成后的 `<project>/templates/design_spec.md` 顶部必须加：

```markdown
> **Fused from:**
> - deck: `templates/decks/中国电信/` （base）
> - brand: `templates/brands/anthropic/` （identity 段覆盖）
> - style: `templates/styles/consulting_analytical/` （方向/方法）
> - layout: `templates/layouts/presentation_core/` （structure 段覆盖）
> - conflicts resolved: Color Scheme from anthropic（用户选 a）
```

让 AI 和人类都能回溯每段来自哪。

---

## 五、与 Generate PPTX Step 3 的关系

**触发规则仍以精确选择为准**——使用 Step 3 已注册模板下拉选项或显式工作区根目录路径（见 [Generate PPTX Step 3](../../skills/ppt-master/workflows/generate-pptx.md#step-3-template-option)）；裸名称绝不触发。Step 3 先解析 `<workspace>/templates/design_spec.md`；为兼容目录形态，也接受根目录直接包含 `<workspace>/design_spec.md`、且满足当前 kind 合同的旧式平铺 Brand/Layout/Deck 工作区。Layout/Deck 还必须带有当前 structured SVG；Style 没有平铺形态。若包仍使用 `native_structure_mode: template`、缺 Master 身份、原子 placeholder 或蒸馏时代标记等旧语义，Step 3 必须拒绝；先由 `create-template` 产出新工作区，再继续生成。唯一的窄例外是当前对话刚完成 `create-template`：验证通过后可把精确的工作区根目录直接交给 Step 3。`kind` 字段决定**触发后 AI 怎么处理**：

| 用户路径指向 | Step 3 行为（按 kind 分支）|
|---|---|
| `kind: brand` | 把工作区 `templates/` 及实际存在的 `images/`、`icons/` 映射到项目同名目录；忽略 `exports/` |
| `kind: style` | 安装仅含 spec 的方向/方法工作区；要求无 SVG roster，并保持生成页面为 flat |
| `kind: layout` | 把工作区 `templates/` 及实际存在的 `images/`、`icons/` 映射到项目同名目录；忽略 `exports/` |
| `kind: deck` | 把工作区 `templates/` 及实际存在的 `images/`、`icons/` 映射到项目同名目录；忽略 `exports/` |
| 多路径 | 按上表合成单份 `design_spec.md`，解决冲突后再合并实际存在的可移植目录 |
| 同类多份 | 按上节"git 冲突解决"问答，得到合成结果 |

位图统一进入工作区 `images/`，模板 SVG 通过 `../images/` 引用。如果显式输入根目录本来就是目标项目根目录，Step 3 原地消费：不得复制到自身，也不得再次移动素材。除此之外，完整核心工作区是可移植的：可以从项目根复制到全局库根、从全局库复制到项目，或从另一个工作区直接复用，而不改变内部结构。注册是唯一与范围相关的步骤。

### 策略师确认阶段在不同 kind 下的行为

安装模板不会让沟通问题消失。Stage 1 始终独立确认同一份开放式沟通契约，只使用当前请求、源材料事实、对话约束和项目初始化状态，连模板画布也不能参与。Stage 1 完成后，Stage 2 才读取已安装状态。Brand 提供身份约束、结构仍然自由；Style 提供方法和视觉默认值候选并保持 flat；Layout 提供结构能力；Deck 提供描述性的可复用应用语境供对照，但不充当当前项目契约。Style-only 时 Strategist 不读取原型，固定写入 `template_reuse_scope: style` 与 flat 结构；Layout/Deck 才读取真实原型和当前内容，生成页面/原型计划，并把 `mirror`、`layout` 或 `style` 记录为内部导出值。按 mirror 创建的工作区因此只提供原样复用能力，不会强制使用；Confirm UI 不显示模板模式字段。规划语义由 `references/strategist.md` 与 `references/strategist-template.md` 负责，机器结构由 `templates/schemas/spec_lock.schema.json` 负责。

---

## 六、与路线和子工作流的关系

| 路线或子工作流 | 产出 |
|---|---|
| `workflows/create-template.md` | 固定 Create Template 入口，以及范围、确认、预检、结构创作、注册、完成和交接的共享合同；只分派一个子工作流 |
| `workflows/create-template/create-brand.md` | 仅身份的 Brand 工作区；无 SVG roster，空的可选目录省略 |
| `workflows/create-template/create-style.md` | 仅方向/方法的 Style 工作区；无 SVG roster、身份真值、应用契约、原生结构或预览 PPTX |
| `workflows/create-template/create-layout.md` | 品牌中立、带结构化 SVG roster 的 Layout 工作区 |
| `workflows/create-template/create-deck.md` | 应用契约与身份/结构一体化、带结构化 SVG roster 的 Deck 工作区；可复用成果带品牌身份或场景语义时选择，不能只因来源是一份完整 PPTX 就默认选择 |

在全局库范围，frontmatter `kind` 字段决定工作区父目录位于 `templates/brands/` / `templates/styles/` / `templates/layouts/` / `templates/decks/`。项目范围在项目工作区根目录保留同一 kind 语义。完整工作区可在两种范围之间移动而不改形，只需增加或移除全局索引注册。

---

## 七、不做（与本文 framing 配套的拒绝列表）

- **不在 fusion 层支持字段级覆盖语法** —— 字段级微调走 策略师确认阶段这条已有路径
- **不为同类三份及以上设计批量冲突解决** —— 用户先在 chat 里收敛到两份
- **不引入双名映射表** —— 模板命名按其品牌/场景母语（中文模板用中文名，英文模板用 snake_case），不强制统一
- **不为输出范围新增结构分支或 CLI flag** —— 输出范围是 `create-template` 简报里的执行选择；两种范围的 Layout/Deck 都声明 `native_structure_mode: structured`，Brand/Style 均无 roster
- **不增加 Theme kind** —— Theme 投影 Brand、Deck 或当前项目解析后的身份；Style fallback 不是身份真值
- **不让 Style 自动触发 visual review** —— Review Focus 只补充已启用的审阅阶段
- **不把 Brand + Layout 自动提升成可注册的 Deck** —— 项目内组合可以按同时具备身份/结构能力来路由，但可复用 Deck 仍必须包含应用契约
