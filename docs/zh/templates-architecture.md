# 模板架构：Brand / Layout / Deck 三分类

> 本文是**架构对齐文档**，定义"模板"在数据模型层面的三种身份、各自的 `design_spec.md` 字段集、以及多路径合成与冲突解决规则。面向贡献者与 AI 工作流，回答"一个模板目录里应该写什么、不写什么；多个模板同时给时怎么合成"。
>
> 用户视角的用法（怎么触发、怎么选）见 [`templates-guide.md`](./templates-guide.md)；本文不重复。

---

## 一、三分类

| 分类 | 全局库工作区根目录 | 写什么 | 不写什么 | 出处工作流 |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | 仅身份段：color / typography / logo / voice / icon style | 不写 canvas、page structure、SVG roster | `workflows/create-brand.md` |
| **Layout** | `templates/layouts/<id>/` | 仅结构段：canvas / page structure / page types / SVG roster | 不写品牌身份（无 logo、无品牌色硬约束） | `workflows/create-template.md`（layout 分支）|
| **Deck** | `templates/decks/<id>/` | 全段：身份段 + 结构段 + 中间段（template overview） | —— | `workflows/create-template.md`（deck 分支，默认）|

每张新建或已恢复的 Layout/Deck SVG 都是完整预览，并在根节点声明 Master/Layout key 与选择器名称；固定 Master/Layout 视觉是直接原子元素；语义槽位是顶层 group。普通槽位必须有正数设计区域 bounds 和恰好一个兼容 carrier；复合 `object` 区域走显式 proxy 绑定，零槽 Layout 也合法。这些专用标记具有最高优先级；最小 `data-pptx-role` 只补充它们无法表达的页面框架行为。`standard` / `fidelity` 重新创作 SVG 和新的结构，不保留、也不蒸馏来源拓扑。Mirror 按来源恢复 roster、身份、父子关系、placeholder 事实和受支持视觉，不做语义归纳；固定结构层的来源 group 只允许机械展开成直接原子。下游 `strict` 保持所选声明合同，`adaptive` 保持 Master 并可在创作时建立新 Layout 身份；两者都使用 `pptx_structure.mode: structured`。只有使用旧 Master/Layout 语义的包才必须先运行 `restore-pptx-structure`；旧包把 `design_spec.md` 平铺在根目录仍属于受支持的兼容目录形态，目录平铺本身不触发恢复。

三者是**三种并列的 reference bundle**。在全局库范围内，物理目录与 frontmatter `kind` 字段双向对齐：

多路径合成后的项目级 `design_spec.md` 也必须保留准确的 `kind`：同时具备身份段和结构段时为 `deck`，只有结构段时为 `layout`，只有身份段时为 `brand`。Strategist 确认页据此只对真正包含页面结构的 Deck/Layout 显示 `adaptive / strict`。

```yaml
# templates/brands/anthropic/templates/design_spec.md
---
kind: brand
...
---

# templates/layouts/academic_defense/templates/design_spec.md
---
kind: layout
native_structure_mode: structured
...
---

# templates/decks/招商银行/templates/design_spec.md
---
kind: deck
native_structure_mode: structured
...
---
```

### 输出范围与 kind 相互独立

`create-template` 会确认 Layout/Deck 工作区放在哪里。这个执行选择不会增加第四种 kind，也不会增加新的 PPTX 结构模式：

| 范围 | 工作区根目录 | 核心结构 | 发现行为 |
|---|---|---|---|
| `library`（默认） | `skills/ppt-master/templates/<kind>/<id>/` | 必需 `templates/`；可选 `images/`、`icons/` 与按需 `exports/` | 写入对应全局索引 |
| `project` | `projects/<name>/` | 完全相同的路由合同 | 不更新全局索引 |

两种根目录都保持相同的核心形态：

```text
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── *.svg
│   └── icons/                  # 使用时保留 package / 校验副本
├── images/                     # 可选；SVG 统一引用 ../images/<name>
├── icons/                      # 可选；提取向量素材的运行期副本
└── exports/                    # 可选；仅在按需生成审阅文件时创建
    └── <id>_template_preview.pptx
```

空的可选目录直接省略，不添加占位文件。按需生成的预览 PPTX 是派生审阅证据，不是模板源资产。Step 3 读取工作区根目录，只消费 `templates/` 及实际存在的 `images/`、`icons/`，不会复制或使用 `exports/`；全局库下的 `exports/` 统一由 Git 忽略。

原生形状 metadata 采用两级模型。完整导入 SVG 保存 native metadata、隐藏 carrier 和预览证据；轻量 authoring projection 移除大体积载荷与重复 carrier，只供模型检查，永远不是导出源。创作模式使用紧凑 canonical metadata。Mirror 可在未改的 Slide-local/slot 对象上复用转换器已经支持的 metadata；固定结构层保持直接原子，不支持或已修改的对象保留 SVG fallback。导出只编译声明的结构，不推断归属。

两种范围都在可移植 frontmatter 中保留 `kind: layout` 或 `kind: deck`。`output_scope` 与 `target_project` 只属于工作流简报，不写入 `design_spec.md`。

任何范围第一次写最终文件前，都必须解析工作区根目录、确认 `templates/` 为空，并检查全部计划写入的图片与图标文件名无冲突；只有明确要求预览导出时才检查预览 PPTX 目标。项目范围还必须确认目标项目已初始化。任一失败都在写入前停止，不合并、不覆盖。

### 三段的字段切分

为了让多路径合成能干净覆盖，所有字段按段归属，**段级整段替换是默认粒度**：

| 段 | 包含的章节 | 归属（覆盖优先级）|
|---|---|---|
| **身份段** | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand 覆盖 |
| **结构段** | Canvas Specification / Page Structure / Page Types / SVG Roster | layout 覆盖 |
| **中间段** | Template Overview（use cases / design intent / page rhythm 等叙事字段）| deck 独有；brand / layout 不写 |

### 为什么需要 Deck 这一类

Deck 是从一份现存 PPT 或明确设计方向形成的完整身份与结构参考——配色、字体、视觉节奏与页面类型共同组成一个整体。它的价值是「已验证的整体感」，是 layout + brand 自由拼合未必能达到的成品。

它的构建方式由 replication mode 决定：`standard` / `fidelity` 根据视觉参考创作新系统；mirror 一对一恢复来源身份与父子关系。打包完成后，两者都作为可被显式 brand / layout 覆盖的完整参考方案使用。

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

### Layout schema

**Frontmatter**

```yaml
---
layout_id: <slug>
kind: layout
native_structure_mode: structured
summary: <一句话描述用途>
canvas_format: <ppt169 | ppt43 | a4 | ...>
page_count: <N>
page_types: [<cover, toc, chapter, content, ending, ...>]
---
```

**正文章节**（结构段全集 + Template Overview）

| 节 | 标题 | 必写字段 |
|---|---|---|
| I | Template Overview | Use Cases / Design Intent / Page Rhythm 建议 |
| II | Canvas Specification | Format / Dimensions / viewBox / Margins / Content Area |
| III | Page Structure | General Layout Grid / Decorative DNA / Navigation 规则 |
| IV | Page Types | 每种页面的角色（cover / toc / chapter / content / ending …）与变体说明 |
| V | SVG Page Roster | 文件清单 + 用途，每个文件对应 III/IV 哪一类 |

**不允许出现**：品牌 logo、品牌 voice & tone、官方真值色（`provenance: fact`）——这些是 brand 的职责。Layout 自身没有兜底色/字体（这是定义：layout 不写身份段；色彩与字体在 策略师确认阶段现场决策）。

### Deck schema

**Frontmatter**

```yaml
---
deck_id: <slug>
kind: deck
native_structure_mode: structured
summary: <一句话描述用途>
canvas_format: <ppt169 | ...>
page_count: <N>
primary_color: "<HEX>"
---
```

**正文章节**（身份段全部 + 结构段全部 + 中间段）

| 节 | 标题 | 归属段 |
|---|---|---|
| I | Template Overview | 中间段 |
| II | Canvas Specification | 结构段 |
| III | Color Scheme（含 provenance）| 身份段 |
| IV | Typography | 身份段 |
| V | Logo | 身份段 |
| VI | Voice & Tone | 身份段 |
| VII | Icon Style | 身份段 |
| VIII | Page Structure | 结构段 |
| IX | Page Types | 结构段 |
| X | SVG Page Roster | 结构段 |

> Deck 是身份段 + 结构段全字段的并集，无可选段。这样合成时段级替换粒度统一。

---

## 三、三套 index 文件

每个 index 跟物理目录一一对应，字段按需精简（参照 [[project-charts-index-full-read-intentional]] 的"meta + summary"模式，但保留对 Strategist 选型有用的结构化元数据）。

三套索引只覆盖全局库范围。项目根工作区有意不进入任何索引，仍可通过显式 `projects/<name>/` 路径使用。因为两种范围采用相同工作区形态，完整核心工作区可在两者之间移动或复制，不需要重写素材路径；只有全局库注册不同。

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
    "summary": "China Merchants Bank transaction banking deck",
    "canvas_format": "ppt169",
    "page_count": 5,
    "primary_color": "#XXXXXX"
  }
}
```

- 含 `primary_color`（deck 自带身份）+ 结构元数据
- 不展开 `page_types` —— deck 的页面类型与 layout 的相同集合，不冗余记录

---

## 四、多路径合成与冲突解决

### 合成优先级（隐式触发）

用户在第一条消息里给出一组路径，Step 3 按以下表合成 `<project>/templates/design_spec.md`：

| 用户路径 | 合成行为 |
|---|---|
| 无 | 跳过 Step 3，走自由设计 |
| 只 brand | 复制 brand 全部，结构走自由设计 |
| 只 layout | 复制 layout 全部，身份走自由设计（策略师确认阶段 e/f/g 决策） |
| 只 deck | 复制 deck 全部 |
| brand + layout | brand 提供身份段 + layout 提供结构段，沿用 SKILL.md 现有 fusion 表 |
| brand + deck | brand 段级覆盖 deck 的身份段，结构段与中间段从 deck 拿 |
| layout + deck | layout 段级覆盖 deck 的结构段，身份段与中间段从 deck 拿 |
| brand + layout + deck | brand 覆盖身份 + layout 覆盖结构 + deck 提供中间段；身份/结构段的 deck 原值整段丢弃 |

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
- `layout × 2`、`deck × 2`、`brand × 2` 同处理
- 三类各最多两份（再多让用户先在 chat 里收敛）

### Provenance 记录

合成后的 `<project>/templates/design_spec.md` 顶部必须加：

```markdown
> **Fused from:**
> - deck: `templates/decks/招商银行/` （base）
> - brand: `templates/brands/anthropic/` （identity 段覆盖）
> - layout: `templates/layouts/academic_defense/` （structure 段覆盖）
> - conflicts resolved: Color Scheme from anthropic（用户选 a）
```

让 AI 和人类都能回溯每段来自哪。

---

## 五、与 SKILL.md Step 3 的关系

**触发规则仍以路径为准**——仍需显式工作区根目录路径（见 [[feedback-template-explicit-path-only]]），裸名称绝不触发。Step 3 先解析 `<workspace>/templates/design_spec.md`；为兼容旧包，也接受根目录直接包含 `<workspace>/design_spec.md` 的平铺形态。平铺只是目录兼容，不会触发 `restore-pptx-structure`；只有 SVG 合同仍使用 `native_structure_mode: template`、缺 Master 身份、原子 placeholder 或蒸馏时代标记时才需要恢复。唯一的窄例外是当前对话刚完成 `create-template`：验证通过后可把精确的工作区根目录直接交给 Step 3。`kind` 字段决定**触发后 AI 怎么处理**：

| 用户路径指向 | Step 3 行为（按 kind 分支）|
|---|---|
| `kind: brand` | 把工作区 `templates/` 及实际存在的 `images/`、`icons/` 映射到项目同名目录；忽略 `exports/` |
| `kind: layout` | 把工作区 `templates/` 及实际存在的 `images/`、`icons/` 映射到项目同名目录；忽略 `exports/` |
| `kind: deck` | 把工作区 `templates/` 及实际存在的 `images/`、`icons/` 映射到项目同名目录；忽略 `exports/` |
| 多路径 | 按上表合成单份 `design_spec.md`，解决冲突后再合并实际存在的可移植目录 |
| 同类多份 | 按上节"git 冲突解决"问答，得到合成结果 |

位图统一进入工作区 `images/`，模板 SVG 通过 `../images/` 引用。如果显式输入根目录本来就是目标项目根目录，Step 3 原地消费：不得复制到自身，也不得再次移动素材。除此之外，完整核心工作区是可移植的：可以从项目根复制到全局库根、从全局库复制到项目，或从另一个工作区直接复用，而不改变内部结构。注册是唯一与范围相关的步骤。

### 策略师确认阶段在不同 kind 下的收窄

Deck 路径下用户已经拿到完整方案，策略师确认阶段收窄到"目标受众 / 页数 / 大纲 / 调性微调"等 deck 内容相关字段；其他字段直接从锁定值复用。具体收窄规则落在 `references/strategist.md` 与 `spec_lock_reference.md`。

---

## 六、与 workflows 的关系

| 工作流 | 产出 |
|---|---|
| `workflows/create-brand.md` | 使用统一路由的 identity-only brand 工作区；空的可选目录省略 |
| `workflows/create-template.md` | 完整 layout 或 deck 工作区。`standard` / `fidelity` 创作新语义 SVG，mirror 恢复来源合同。输出范围默认 `library`（`templates/<kind>/<id>/` + 注册），确认 `project` 时写 `projects/<name>/`（不注册）。两者使用相同的可选目录路由，预览 PPTX 按需生成；内部 kind 分支仍默认 deck，用户明说"只要结构 / 丢掉品牌色"时走 layout |

在全局库范围，frontmatter `kind` 字段决定工作区父目录位于 `templates/brands/` / `templates/layouts/` / `templates/decks/`。项目范围在项目工作区根目录保留同一 kind 语义。完整工作区可在两种范围之间迁移而不改形，只需增加或移除全局索引注册。

---

## 七、不做（与本文 framing 配套的拒绝列表）

- **不在 fusion 层支持字段级覆盖语法** —— 字段级微调走 策略师确认阶段这条已有路径
- **不为同类三份及以上设计批量冲突解决** —— 用户先在 chat 里收敛到两份
- **不引入双名映射表** —— 模板命名按其品牌/场景母语（中文模板用中文名，英文模板用 snake_case），不强制统一
- **不为输出范围新增结构分支或 CLI flag** —— 输出范围是 `create-template` 简报里的执行选择；两种范围的 Layout/Deck 都声明 `native_structure_mode: structured`
