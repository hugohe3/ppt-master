# 模板架构：Brand / Layout / Deck 三分类

> 本文是**架构对齐文档**，定义"模板"在数据模型层面的三种身份、各自的 `design_spec.md` 字段集、以及多路径合成与冲突解决规则。面向贡献者与 AI 工作流，回答"一个模板目录里应该写什么、不写什么；多个模板同时给时怎么合成"。
>
> 用户视角的用法（怎么触发、怎么选）见 [`templates-guide.md`](./templates-guide.md)；本文不重复。

---

## 一、三分类

| 分类 | 物理目录 | 写什么 | 不写什么 | 出处工作流 |
|---|---|---|---|---|
| **Brand** | `templates/brands/<id>/` | 仅身份段：color / typography / logo / voice / icon style | 不写 canvas、page structure、SVG roster | `workflows/create-brand.md` |
| **Layout** | `templates/layouts/<id>/` | 仅结构段：canvas / page structure / page types / SVG roster | 不写品牌身份（无 logo、无品牌色硬约束） | `workflows/create-template.md`（layout 分支）|
| **Deck** | `templates/decks/<id>/` | 全段：身份段 + 结构段 + 中间段（template overview） | —— | `workflows/create-template.md`（deck 分支，默认）|

三者是**三种并列的 reference bundle**，物理目录与 frontmatter `kind` 字段双向对齐：

```yaml
# templates/brands/anthropic/design_spec.md
---
kind: brand
...
---

# templates/layouts/academic_defense/design_spec.md
---
kind: layout
...
---

# templates/decks/招商银行/design_spec.md
---
kind: deck
...
---
```

### 三段的字段切分

为了让多路径合成能干净覆盖，所有字段按段归属，**段级整段替换是默认粒度**：

| 段 | 包含的章节 | 归属（覆盖优先级）|
|---|---|---|
| **身份段** | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand 覆盖 |
| **结构段** | Canvas Specification / Page Structure / Page Types / SVG Roster | layout 覆盖 |
| **中间段** | Template Overview（use cases / design intent / page rhythm 等叙事字段）| deck 独有；brand / layout 不写 |

### 为什么需要 Deck 这一类

Deck 是一份现存 PPT 的"复刻全息"——SVG 几何为该套配色和字体画的，身份与结构在原 PPT 里已经实战搭配。它的价值是「已验证的整体感」，是 layout + brand 自由拼合未必能达到的成品。

但 Deck **不是"不可篡改的复刻"**——它是"作为默认底图的复刻，可被显式 brand / layout 覆盖"。这给了用户最大自由度：默认拿到一份完整方案，需要时显式换身份或换结构。

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

**不允许出现**：品牌 logo、品牌 voice & tone、官方真值色（`provenance: fact`）——这些是 brand 的职责。Layout 自身没有兜底色/字体（这是定义：layout 不写身份段；色彩与字体在 Strategist 八项确认现场决策）。

### Deck schema

**Frontmatter**

```yaml
---
deck_id: <slug>
kind: deck
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
| 只 layout | 复制 layout 全部，身份走自由设计（Strategist 八项确认 e/f/g 决策） |
| 只 deck | 复制 deck 全部 |
| brand + layout | brand 提供身份段 + layout 提供结构段，沿用 SKILL.md 现有 fusion 表 |
| brand + deck | brand 段级覆盖 deck 的身份段，结构段与中间段从 deck 拿 |
| layout + deck | layout 段级覆盖 deck 的结构段，身份段与中间段从 deck 拿 |
| brand + layout + deck | brand 覆盖身份 + layout 覆盖结构 + deck 提供中间段；身份/结构段的 deck 原值整段丢弃 |

### 段级整段替换（默认粒度）

合成默认是**段级整段替换**——例如 deck + brand 时，整个 Color Scheme / Typography / Logo / Voice / Icon Style 五段从 brand 拿，**不做字段级混搭**（即不会发生"primary 从 brand 拿、secondary 从 deck 拿"这类隐式混合）。

字段级微调走 Strategist 八项确认这条已有路径——用户在 chat 里说"用 anthropic brand，但 primary 改成 #FF0000"，由 Strategist 在 e/g 现场调整，不在 Step 3 的 fusion 层加字段级语法。

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

**触发规则不变** —— 仍然是「显式目录路径才触发」（见 [[feedback-template-explicit-path-only]]）。`kind` 字段决定**触发后 AI 怎么处理**：

| 用户路径指向 | Step 3 行为（按 kind 分支）|
|---|---|
| `kind: brand` | 复制 design_spec + logos + asset 子目录到 `<project>/templates/` |
| `kind: layout` | 复制 design_spec + SVG roster + assets 到 `<project>/templates/` |
| `kind: deck` | 复制 design_spec + SVG roster + logos + 全部 assets 到 `<project>/templates/` |
| 多路径 | 按上表合成单份 `design_spec.md` + 各源的 SVG/logo 合并复制 |
| 同类多份 | 按上节"git 冲突解决"问答，得到合成结果 |

### Strategist 八项确认在不同 kind 下的收窄

Deck 路径下用户已经拿到完整方案，八项确认收窄到"目标受众 / 页数 / 大纲 / 调性微调"等 deck 内容相关字段；其他字段直接从锁定值复用。具体收窄规则落在 `references/strategist.md` 与 `spec_lock_reference.md`。

---

## 六、与 workflows 的关系

| 工作流 | 产出 |
|---|---|
| `workflows/create-brand.md` | brand 目录（identity-only），从品牌资产逆向提取 |
| `workflows/create-template.md` | layout 或 deck 目录，内部按 kind 分支：默认走 deck（用户给了一份现存 PPT，提取完整身份 + 结构）；用户明说"只要结构 / 丢掉品牌色"时走 layout |

产出后 frontmatter `kind` 字段决定文件落到 `templates/brands/` / `templates/layouts/` / `templates/decks/`。

---

## 七、不做（与本文 framing 配套的拒绝列表）

- **不在 fusion 层支持字段级覆盖语法** —— 字段级微调走 Strategist 八项确认这条已有路径
- **不为同类三份及以上设计批量冲突解决** —— 用户先在 chat 里收敛到两份
- **不引入双名映射表** —— 模板命名按其品牌/场景母语（中文模板用中文名，英文模板用 snake_case），不强制统一
