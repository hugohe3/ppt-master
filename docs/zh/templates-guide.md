# 模板指南：选用、派生与边界

[English](../templates-guide.md) | [Chinese](./templates-guide.md)

---

PPT Master 模板是一种可复用工作区，明确分为四类：**Brand** 只拥有身份系统，**Style** 只拥有可移植沟通方法和视觉默认值，**Layout** 只拥有品牌中立的可复用页面结构，**Deck** 拥有一类可重复演示的描述性应用语境及一体化身份与结构。Layout 与 Deck 工作区包含声明 Master / Layout / slot 合同的完整 SVG 原型；Brand 与 Style 则有意不包含 SVG roster。每个工作区的 `design_spec.md` 声明该 kind 实际提供什么。

本文回答三个问题：

1. [怎么用已有模板？](#一选用已有模板)
2. [怎么把别人的 PPT / 自己的品牌做成模板？（重点）](#二派生新模板重点)
3. [模板的边界是什么？](#三模板的边界)

## 60 秒选对模板路线

先看你手里有什么，以及最终想得到什么：

| 起点与目标 | 路线 | 可直接复制的请求 |
|---|---|---|
| 手里是原始 `.pptx`，想保留现有页面壳并替换内容 | **Edit Native PPTX** | `把 projects/source/content.md 的内容套进 projects/source/template.pptx；保留原设计，只选适合的页面。` |
| 已有可复用 Brand/Style/Layout/Deck 工作区，想生成一份全新 deck | **Generate PPTX → Stage 1 模板选择控件** | `用 sources/report.pdf 做 deck，模板用 skills/ppt-master/templates/layouts/presentation_core/。` |
| 手里是 PPTX、SVG、品牌手册、网站、图片或混合参考，想先建立可复用系统 | **Create Template → Generate PPTX** | `用 /create-template 从 projects/brand/our_deck.pptx 创建一个可复用 Deck 工作区。` |

不要把原始 `.pptx` 当作 Generate PPTX 的模板路径。想沿用它的现有页面就直接回填；想建立可复用系统，就先运行 Create Template。

再按需要复用的内容选择工作区 kind：

| Kind | 复用什么 | 原生 PowerPoint 结果 |
|---|---|---|
| **Brand** | 颜色、字体、Logo、语调、图标风格 | 只提供身份约束。生成页面保持 Slide 本地，文件只有干净的项目 Master 与 Blank Layout 脚手架。 |
| **Style** | 沟通方法、开放页面角色词汇、证据/数据规则、视觉默认值、图片/图标方向及审阅关注点 | 生成 flat Slide-local 页面；这些值只作为最终 Stage 2 起点，不升级为品牌身份或可复用 Layout。 |
| **Layout** | 品牌中立的页面语法、Master/Layout 身份、语义文字角色、槽位与版式 roster | 结构化 deck，包含可复用原生 Master、具名 Layout 与 placeholder；身份、阅读模式字号和沟通应用另行解析。 |
| **Deck** | 一类可重复演示：描述性应用语境、身份、页面结构与真实原型 | AI 根据模板实物与当前内容自动生成页面/原型应用计划。 |

Theme、Slide Master、Slide Layout 与 Placeholder 是 PowerPoint 原生对象，不是新的工作区 kind。Brand 与 Layout 的规则会被编译进这些对象。使用 `layout` 时，语义文字角色来自 Layout，最终字体和字号体系由身份与阅读模式共同解析；使用 `mirror` 时则保留来源的字面格式。最终 Master 可以同时包含结构几何和品牌视觉，但来源合同仍保持分离。

最容易避免误用的两条规则：

1. Default Generate 的 [Step 3](../../skills/ppt-master/workflows/generate-pptx.md#step-3-template-candidate-preparation) 只准备候选；Stage 1 在同一次提交中确认沟通契约与自由设计/使用模板。
2. 普通请求默认自由设计；明确要求使用模板或提供任意精确工作区 root 时默认展开模板模式。只提供一个 root 时会预选，多 root 仍只作为未选候选。非自由设计选择在 Stage 1 后、模板感知的最终 Stage 2 前安装。

---

## 一、选用已有模板

### 选择方式

Default Generate 把模板选择放进 **Stage 1**，与不受模板影响的沟通契约
同屏。页面先提供可切换的「自由设计 / 使用模板」；普通请求默认自由设计并
收起详细选项，明确要求使用模板或提供任意精确 root 时默认展开模板模式。
模板模式展示已注册 Brand/Style/Layout/Deck 与本次提供的 root；只提供一个
root 时会预选，多 root 仍只作为未选候选。系统不会根据主题替用户推断具体模板。

> **快速模式例外：** Quick 不会打开这个页面。请求中的精确 root 会被直接
> 校验并使用，每个 kind 最多一份；Layout 与 Deck 可以共存，结构由 Layout
> 优先提供。多 kind root
> 会原子地贡献其全部 spec。没有精确 root 就直接自由设计，裸模板名仍不会
> 被解析。Quick 是无锁而不是无结构：自由设计和仅 Brand/Style 的输出保持
> flat；一旦由 Layout/Deck 提供结构，创作 SVG 与导出的 PPTX 都保留显式
> Master/Layout/slot 元数据。

### 怎么使用选择器

Stage-1 页面先让用户选择自由设计或使用模板；只有选择使用模板，才展开五个
紧凑下拉框：Brand、Style、Layout、Deck 各一个已注册工作区单选框，再加
一个本次运行指定地址单选框。每个下拉框都有“无”；完整选择可以分别选用
四种 kind，但每个 kind 最多一份。Layout 与 Deck 同时存在时由
Layout 提供结构。指定地址最多选一个，并原子携带
该 root 暴露的全部 kind。已注册列表只来自四类索引，工作流不会扫描模板
目录。需要默认展开模板模式并预选某个 Brand/Style/Layout/Deck 工作区时，
直接在对话里写出精确 root（位置不重要，只要明确即可）：

> "用这个模板做：`skills/ppt-master/templates/layouts/presentation_core/`" ✅
> "用上次那个模板：`projects/last_deck/`" ✅
> "做一份产品介绍，模板用 `/Users/me/Desktop/our_brand_v3/`" ✅

对于当前所有模板类型，显式路径都是**模板工作区根目录**。若精确路径与索引中的注册 root 一致，页面可以把它显示为 `library`；未注册 root 则单独标为 `explicit`，并由服务端解析其中真实的限定名 spec。`explicit` 只是来源，不是第五种类型，也不提高优先级。Stage 1 会原子校验每个已选 root；确认后，每个不同 root 的 spec 和真实包自有 `images/`、`icons/` 只映射一次，并只安装有效结构 roster（有 Layout 时用 Layout，否则用 Deck），始终不复制 `exports/`。Deck/Layout root 会在应用优先级前各自校验 structured SVG 合同；Brand/Style 校验各自无 roster 的 spec。路径可以指向 `skills/ppt-master/templates/<kind>/<id>/` 下的内置库工作区、`projects/<name>/` 下的项目工作区，或其他保持同样路由的工作区。当前对话刚完成 Create Template 时，可把精确的已验证工作区根目录直接交给下一次 Stage-1 选择器。

模板选择与 Stage 1 共用页面和提交动作，但仍作为独立 sidecar 决策保存。
沟通推荐只使用当前请求、源材料事实、对话约束和项目初始化状态；候选元数据、
所选 root、已安装内容及模板画布均不得影响它。合并确认后，非自由设计选择才
运行统一 apply 阶段，把所选工作区分别校验并安装到当前项目的 `templates/`、
`images/`、`icons/`。最终 Stage 2 再把已确认沟通契约与安装状态适配；
`template_application` 只描述**如何使用**，不负责决定**选哪个模板**。

`template_application` 是一段自然语言，不是模式选择器。用户有明确要求时以
用户要求为准；没有时，AI 阅读全部已安装模板 SVG，根据当前内容判断；没有
更强理由时，默认按参照型使用。参照型是在读完整套 SVG 后允许重新设计；增强型
冻结已有非 slot 对象、允许修改 slot，并且只新增；替换型只更换信息载体，
其余内容保持不动。这些只是常见意图表达，不是固定选项。任何只针对某一原型的
规则都必须写出精确 SVG 文件名。Quick
也形成并冻结同样的一段方案，只是保留在当前上下文，不写确认页、Design Spec
或 lock。

> **当前工作区预检：** Step 3 只接受在 `templates/` 下提供 Design Spec 的工作区根目录。根目录平铺、旧的原子 placeholder、未映射 Master/Layout 等语义旧包都会被拒绝。先运行 `create-template` 创建新工作区，再从该工作区生成新的 structured 页面；不会原地升级旧包。

### 什么**不会**自动选中模板

- **在聊天中只写模板名**："presentation_core" / "中国电信模板" 不会被隐式解析，也不会预选工作区。请在页面选择注册项，或在聊天中返回精确路径。
- **风格描述**："麦肯锡风格" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" 仍只是自由设计说明；除非用户选择工作区或提供精确 root，否则不会激活模板。

这是有意的——AI 永远**不做模糊 / 解释性判断**，不会替你把普通文字解析成模板。Default Generate 固定提供 Stage-1 模式切换入口，只有在索引控件中选定的精确 root 才会激活工作区。

想在聊天中查看内置库，问一句“有哪些模板可以用？”即可。聊天列表与 Stage-1 选择器读取同一组四类索引。单纯列出不代表选择；需要返回其中一条精确路径，或在页面完成选择。

### 可直接复制的用法

使用一个工作区：

```text
用 projects/q3-report/sources/report.pdf 做一份 deck。
模板工作区：skills/ppt-master/templates/layouts/presentation_core/
```

组合身份与结构：

```text
用 projects/launch/sources/brief.md 做产品发布 deck。
Brand 工作区：skills/ppt-master/templates/brands/anthropic/
Layout 工作区：skills/ppt-master/templates/layouts/presentation_core/
```

使用之前创建的项目级模板：

```text
用 projects/annual-report/sources/report.md 做一份 deck。
模板工作区：projects/acme_template/
```

在聊天中显式提供 root 时，“模板工作区”这些标签可以不写，但 root 必须精确；页面中的 library 选择已自带精确 root。页面中每个注册 kind 最多选一个、指定地址最多选一个，并拒绝同 kind 重复。Layout 与 Deck 可以同时选择：Layout 拥有结构，Deck 保留其他片段。指定的多 kind root 必须整包选择，其已暴露的 kind 不能再从 library 重复选择。

你不需要选择模板使用模式。Strategist 会读取有效结构 roster（有 Layout 时用 Layout，否则用 Deck）和当前内容，决定选哪些页、哪些重复/跳过/重排，以及是否重组。Brand 只提供身份约束，Style 只提供方向/方法默认值；除非另一个工作区提供结构，否则两者都保持页面自由编排。如果你在意某个边界，直接在同一句请求里用普通语言说明即可，例如“封面和结束页原样保留，中间页由你选择”或“只参考视觉语言”；明确文字优先于 AI 判断。

### 现有模板一览

模板按四种 kind 分目录，并分别由发现索引维护：

- [`brands_index.json`](../../skills/ppt-master/templates/brands/brands_index.json) — 仅身份工作区：color / typography / logo / voice / icon style，不含 SVG 页面 roster
- [`styles_index.json`](../../skills/ppt-master/templates/styles/styles_index.json) — 仅方向/方法工作区：沟通方法、证据/数据表达、视觉默认值与审阅关注点，不含 SVG 页面 roster
- [`layouts_index.json`](../../skills/ppt-master/templates/layouts/layouts_index.json) — 仅结构工作区：canvas / 页面语法 / page types / SVG roster，身份系统下游再选
- [`decks_index.json`](../../skills/ppt-master/templates/decks/decks_index.json) — 可重复演示应用，包含一体化身份、结构与原型事实描述

这四个索引是 Default Stage 1 模板控件与聊天发现共用的完整已注册模板来源；
目录永远不会被扫描。直接问“有哪些模板可以用？”即可得到带精确工作区路径的
可读清单；四类 README 负责定义合同。完整数据模型、安装与片段所有权
规则见 [`templates-architecture.md`](./templates-architecture.md)。

### 自由设计与模板

自由设计不是“没有结构”或“没有风格”——Strategist 仍会为这份 deck 规划叙事、层级与视觉系统，但生成页面使用 `pptx_structure.mode: flat`，所有可见对象都保留在 Slide 本地。仅使用 Brand 或 Style 工作区时同样保持 `flat`：Brand 提供身份约束，Style 提供可复用方法与视觉默认值候选。Layout 与 Deck 工作区提供可复用 Master / Layout / slot 合同；Strategist 会读取真实原型和当前内容，自动判断是复用结构，还是只参考视觉语言。

> 经验：需要锁定身份系统时用 Brand；需要复用方法和视觉方向、但不固定页面时用 Style；需要复用品牌中立结构、但让用途保持开放时用 Layout；需要把品牌化结构或可重复沟通场景作为一份契约复用时用 Deck；希望全部从当前内容出发时走自由设计。

### 风格说明不是 Style 工作区

**风格说明**是解释性语言（“极简风” / “Keynote 风” / “杂志风”），由 Strategist 转化为当前 deck 的具体设计选择。**Style 工作区**则是真实存在的 `kind: style` 模板，预写可复用沟通方法与视觉默认值；只有用户选择注册项、提供精确工作区 root，或接到当前 Create Template 交接后才会消费。

| | Style 工作区 | 风格说明 |
|---|---|---|
| 怎么启用 | 在 Stage 1 选择模板、消息里给出精确目录路径，或当前 Create Template 交接 | 消息里写自由描述；不选择工作区 |
| 提供什么 | 可复用方法、角色/证据纪律和视觉默认值；无身份真值或页面原型 | 由 Strategist 解释为 mode、visual style、色彩、字体、图标与图片方向 |
| 如何确认 | 已存值作为最终 Stage 2 起点；Brand/Deck 身份和用户最终确认仍然权威 | 没有预写数值；Strategist 给出具体候选，由用户确认 |
| 适用场景 | 跨项目复用论证与设计方法，但不锁页面 | 只表达当前项目想要的感觉 |

风格描述和 Style 工作区仍走**两套机制**：“极简风”是解释性语言并留在自由设计，`templates/styles/<id>/` 则是真实注册工作区，必须在页面选择或通过精确路径提供。`kind: style`、最终 Stage 2 `visual_style` 与内部 `template_reuse_scope: style` 是三条不同轴。

### 风格说明如何被解释

Strategist 会把方向拆成两个彼此独立的选择：

- **Mode** 决定 deck 怎么表达：`pyramid`、`narrative`、`instructional`、`showcase`、`briefing`，或经过确认的 `custom`。
- **Visual style** 决定页面怎么呈现：内置方向包括 `swiss-minimal`、`editorial`、`dark-tech`、`data-journalism`、`ink-wash` 等，也支持 `custom`。

任意 mode 都可以搭配任意 visual style。“Keynote 风产品发布”这类描述可能同时影响两条轴，例如形成 `showcase` 叙事与高留白视觉系统，但它永远不是模板查找词。生成前，用户会确认最终组合。规范目录位于 [`references/modes/`](../../skills/ppt-master/references/modes/) 与 [`references/visual-styles/`](../../skills/ppt-master/references/visual-styles/)。

---

## 二、派生新模板（重点）

把一个或多个 PPTX/SVG、图片/PDF、文档/网站、品牌资产或直接文字要求，做成 PPT Master 可调用的模板。参考材料可以混合使用，也可以不提供外部来源，仅根据确认后的简报从零设计。这是本文的核心。

### 入口：`/create-template` 工作流

完整规范见 [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md)。本节是面向用户的简要版本——你只需要在 IDE 对话里说：

```
请用 /create-template 工作流，基于下面的参考材料生成一个新模板。
```

接下来工作流会**强制**先和你确认一份模板简报（不允许跳过）。

入口名称始终保持 **Create Template**。它只分派一个子工作流：仅复用身份走 Create Brand；复用无页面原型的可移植方法/方向走 Create Style；复用品牌中立结构、且沟通应用保持开放时走 Create Layout；复用品牌化结构或可重复演示应用时走 Create Deck。来源是一份完整 PPTX 并不会自动决定 kind，工作流只按真正稳定、值得重复使用的规则分类。子工作流一旦选定，不会在简报里再次选 kind。

### 第一步：准备参考材料包或简报

你可以直接在对话中输入文字或粘贴要求，也可以提供 Markdown/TXT、DOCX/PDF/HTML/URL、网站、图片/截图、logo/icon/字体资产、PPTX/SVG，或这些材料的任意组合。工作流会分析每个适用通道，保留来源，并在强制简报中暴露冲突，而不是静默选择某一个来源。凡是你本人明确写出的值，无论来自对话、粘贴文字还是你编写的简报文件，都属于决策；文件载体本身不会把它变成事实。事实必须来自可独立追溯的外部权威，或可由机器直接观察的源文件/包元数据。视觉估算与模糊文字的解释在确认前都只是建议。

**当现有演示文稿的原生结构很重要时，请直接提供原始 `.pptx` 文件。** 导入器会读取 OOXML，把包内实际存在且受支持的 Master、Layout、placeholder、主题、原生形状与可复用素材事实提取成分层分析参考。你只需用普通语言说明想要的结果，例如“原样保留”“提取成可复用母版和版式”或“保留视觉语言但重做结构”；AI 会据此选择兼容的内部实现。原 PPTX 始终是不可变的分析证据，不进入新模板包。

也可以基于品牌指南从零设计：提供 logo、主色 HEX、字体、调性描述、几张氛围参考图，AI 会现场设计页面骨架。适合品牌方还没有成型 PPT、只有 VI 手册的场景。

> **证据边界：** 图片、截图、文字、文档、网站和零散资产可以驱动重新创作；更广的来源对齐需要 PPTX/SVG 页面证据；字面保留原生结构需要原始 PPTX 或完整的当前结构化 SVG 合同。补充来源可以解释保留意图，但不能补造或改变原生拓扑。

### 第二步：模板简报（强制确认环节）

工作流会在动手前写出一份简洁的自然语言方案，等待你修正或确认；不会要求你选择模板模式、保真枚举或页面/内容政策。

| 字段 | 说明 |
|------|------|
| **输出范围** | `library`（默认）或 `project`；两者使用相同 spec schema，但 library 在单 kind 目录使用裸 spec，project 在共享根使用限定名 spec |
| **目标项目** | 仅 `project` 必填；必须给出已初始化项目的精确路径 |
| **已选子工作流** | Create Brand / Create Style / Create Layout / Create Deck，由入口分派后固定 |
| **模板 ID** | 模板的可移植身份；在 `library` 下同时也是目录名 / 索引键。优先 ASCII slug，如 `acme_consulting`；中文品牌名也行，但要文件系统安全 |
| **显示名称** | 文档中的人类可读名 |
| **kind 专属语境** | Brand：身份适用场景和调性。Style：宽泛 best fit 与发现关键词。Layout：结构可承载场景及 category/keywords。Deck：重复应用场景及 category/keywords。你可直接修改文字 |
| **方法与视觉默认值** | 仅 Create Style：沟通方法、开放页面角色词汇、证据/数据表达、视觉默认值、图片/图标方向和审阅关注点；不写受众/页序/结构契约 |
| **身份** | 仅 Create Brand/Create Deck：色板、字体、Logo、voice 与 icon identity |
| **画布与结构** | 仅 Create Layout/Create Deck：画布、页面语法、Master/Layout/slot 方案、密度行为和来源结构规则 |
| **来源处理** | 每个 child 只说明如何提取自己拥有的片段；仅 Layout/Deck 描述原型覆盖范围、保留/重建策略和原生结构 |
| **来源事实与素材** | Brand/Layout/Deck 列出采用或排除的素材；Layout/Deck 另报告可观察的 Master/Layout 事实和受支持原生能力。Style 只保留文字 provenance |

确认后，工作流会回显一份完整简报并写入标记 `[TEMPLATE_BRIEF_CONFIRMED]`，从这一刻起后续步骤才会启动。**这是一个硬门——简报没确认，不会开始生成**。

无论选择哪种范围，第一次写最终文件前都会做一次完整预检，解析 Design Spec 和全部真实素材目标。Library 范围要求 `templates/` 为空。Project 范围要求目标项目已初始化，并拒绝裸 spec、同 kind spec 或无效限定名集合；不同 kind 可以共存。新增 Deck 而项目已有 Layout 时，不改变 Layout roster；新增 Layout 而项目已有 Deck 时，先隔离校验，再原子替换 Deck 的结构载荷。两种范围都会在写入前拒绝位图、导入向量、审阅导出及其他计划目标冲突。已有空脚手架会原样保留，Create Template 不会只为保留空路径创建可选目录。任一检查失败都会在写入前停止且不覆盖。

> 为什么这么严？无论模板进入全局库，还是只服务当前项目，它都是可复用的 ownership contract。先确认所拥有的片段和目标位置，并且只为 Layout/Deck 确认几何，可避免半成品或资产落错目录。

### 第三步：AI 推导内部实现

Create Style 会直接写入已确认的方向/方法 spec，不进入 SVG 创建模式。对 Create Layout/Create Deck，你不需要选择创建模式；AI 会把已确认的自然语言方案转换成一个内部策略，供确定性工具执行：

- 需要精炼时，创建紧凑的可复用系统；
- 来源本身包含有价值的多种版式时，创建更广的来源对齐原型；
- 明确保留且来源结构完整受支持时，基于解析证据创作紧凑 mirror。

Layout/Deck frontmatter 仍会记录 `replication_mode: standard|fidelity|mirror` 以兼容工具并保留审计信息；它是实现记录，不是用户选项。Style frontmatter 有意不写 replication/native-structure 字段。品牌中立的 Layout 不能同时字面保留品牌/应用事实，AI 会按目标重新创作 Layout，或把这些事实留在 Deck 中。

**关于精灵图**：PPTX 导出的素材常常是**一张大图 + 多页通过 viewBox 裁剪不同区域**。`fidelity` 和 `mirror` 模式下必须保留这层嵌套 `<svg viewBox=...>` 包装，不能扁平化为单张 `<image>`——否则裁剪信息丢失，画面会错位。工作流会自动校验这一点。

**关于 PowerPoint 原生形状**：完整导入 SVG 作为不可变来源/包证据与受支持非可见载荷后备；模板创建使用新生成的紧凑可编辑 `authoring-svg/` 及其 source-ref/hash manifest。Template_Designer 会实际审阅/创作该 SVG，保持结构、语义和相似展示，但不要求代码同构。publisher 只校验、合成并发布当前可见作者树，绝不回填普通 lossless 可见子树。导入/模板拥有的 Chart/Table JSON 始终内嵌且为权威，其 preview 可以近似。

对于 PPTX 来源的 Type A mirror，完成作者审阅后，最终校验/发布统一使用一个确定性命令：

```bash
python3 skills/ppt-master/scripts/mirror_template_materialize.py \
  "<import_workspace>" "<template_workspace>"
```

它会先校验来源 SHA/已知 ref、作者 manifest、可达原生图谱、
可见性/分配事实和导入向量闭包，再原子发布当前按源顺序排列的 SVG roster 及
`icons/imported/`、`images/` 素材。它不要求、也不会把按需生成的
`svg-flat/` 校验视图当成模板来源，并且不会生成 Design Spec；设计角色必须针对物化后的 roster 写入已解析的 spec 路径。

**Mirror 图谱边界**：mirror 为每张来源 Slide 输出一个完整原型，并只保留该 Slide 引用的 Layout 及其父 Master。SVG 会补齐 Master + Layout + Slide 上下文，同时保留显式层归属。未被任何 Slide 引用的来源 Master/Layout 不由 mirror 物化；`standard` / `fidelity` 可读取完整来源清单，并把有用结构重新创作为 Slide 原型。

Design Spec 对每个输出 Slide 原型按正常 roster 说明。若来源还存在未被引用的 Master/Layout，可用一句范围说明指出它们存在、但未由 mirror 物化，不逐个推断用途。

模板使用以 Slide 为主：生成页面 SVG 已经补齐 Master 与 Layout 视觉，正常创作直接选择完整 Slide 原型；工作区不再存放独立 Master/Layout 定义 SVG。

“只生成 Slide”描述的是可编辑 SVG roster。PPTX 来源的 mirror 仍可携带 `source_themes.json`、`native_payloads.json.gz` 等仅供工具使用的结构 sidecar，用于保存可达结构的精确 Theme 及受支持的不透明恢复 payload/属性记录；它们不是页面原型，也不进入 AI 创作上下文。语义 Chart/Table JSON 始终内联在对应 SVG marker 中。

**按 mirror 创建的工作区怎么消费**：从来源到工作区的 `replication_mode: mirror` 是一种能力，不是项目选择。Strategist 会读取真实原型、当前内容和用户明确要求，自动决定选哪些页、哪些重复/跳过/重排，以及采用字面、结构还是仅视觉参考。字面复用时，Executor 复制完整 SVG，只修改允许变更的可见文字，同时保留装饰、精灵图裁剪、几何坐标和规范化结构声明；仍不要求沿用来源页数或页序。

### 第四步：验证、预览导出、注册与发现

模板生成完，两种范围都会先跑 [`svg_quality_checker.py`](../../skills/ppt-master/scripts/svg_quality_checker.py) 作为硬门：Brand 校验 identity-only 规范，Style 校验 method/direction-only 规范，Layout/Deck 校验 SVG roster 和 structured 合同。Brand/Style 不生成预览 PPTX；Layout/Deck 可按需创建 `exports/<id>_template_preview.pptx`，多 Master 时必须创建。创作型模板只在临时预览副本中使用简短占位示例，避免较长的 canonical marker 换行，不会修改源 SVG。唯一按范围分流的动作是全局注册：

| 范围 | 工作区根目录 | 预览 | 发现行为 |
|---|---|---|---|
| `library`（默认） | `skills/ppt-master/templates/<kind>/<id>/` | Create Brand/Create Style：不适用；Create Layout/Create Deck：单 Master 可选、多 Master 必须 | 校验后注册到对应 `brands_index.json`、`styles_index.json`、`layouts_index.json` 或 `decks_index.json` |
| `project` | `projects/<name>/` | 沿用同一套 kind-specific 审阅规则 | 跳过全局索引注册 |

全局注册会让模板出现在 Default Stage-1 模板控件中，也可在聊天中发现，因为两者都读取同一个索引。项目范围或精确交接则提供工作区 root，例如 `用这个模板：projects/<name>/`；这会默认展开模板模式，只提供一个 root 时页面会预选，多 root 保持未选候选，未注册 root 仍标记为 `explicit`。项目 root 可被其他项目直接复用，并原子贡献其中全部限定名 spec。要把其中一项移入单 kind 全局库，则保持 spec 内容不变，把它放到该库工作区的裸 `templates/design_spec.md` 路径后再注册。

选择 Deck/Layout 模板后，Strategist 会自动生成页面/原型应用计划：可以使用全套或子集，重复或重排原型，并按内容需要重组。`strict` / `adaptive` 只作为内部导出值，不再出现在确认选项中。

### 如何确认母版与版式真的生效

使用 Layout 或 Deck 工作区生成后，在 Microsoft PowerPoint 中检查发布文件：

| 检查位置 | 预期结果 |
|---|---|
| **视图 → 幻灯片母版** | 能看到模板声明的 Master 与具名 Layout。 |
| **开始 → 新建幻灯片** | 版式选择器中能在预期 Master 下看到可复用 Layout 名称。 |
| 选中生成页并查看 **版式** | 页面绑定到声明的 Layout，而不是导出器猜出的通用版式。 |
| 点击可复用内容区域 | 模板槽位表现为带声明类型与边界的原生 placeholder。 |
| 从某个已导出 Layout 新建一页 | 不复制成品内容页，也能得到该 Master/Layout 的固定视觉与 placeholder 几何。 |

Brand/Style 的目标不同：两者都让创作内容保持 Slide 本地，因此不应期待除干净包脚手架之外的可复用 Layout roster；Brand 提供身份，Style 提供方法/方向默认值。

`exports/<id>_template_preview.pptx` 是 Create Template 按需或按规则生成的审阅证据，不是模板输入；真正生成时始终传工作区根目录。

Master/Layout 行为以 Microsoft PowerPoint 为验收目标。Keynote、WPS 与 LibreOffice 可以打开 PPTX，但可能归一化模板结构。

### 派生后的模板工作区长什么样

全局库与项目范围使用相同的 spec schema 和素材路由；库工作区用裸 spec，项目共享根则用限定名 spec。把下面的 `<template_workspace>` 替换为 `skills/ppt-master/templates/<kind>/<id>/` 或 `projects/<name>/` 即可：

Brand 与 Style 只写 `templates/design_spec.md`（Brand 可带真实身份资产），
不会生成下面的 SVG 或 `exports/` 行。

```
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_toc.svg              # 可选；不含时为 02_chapter、03_content、04_ending
│   ├── 03_chapter.svg
│   ├── 04_content.svg          # 同类有多个变体时改用 04a/04b 兄弟命名
│   └── 05_ending.svg
├── images/                         # 可选
│   └── *.png / *.jpg           # SVG 统一引用 ../images/<name>
├── icons/                          # 可选
│   └── imported/
│       └── *.svg               # 导入向量素材的唯一规范副本
└── exports/                        # 可选；按需生成审阅文件
    └── <id>_template_preview.pptx
```

`standard` 和 `fidelity` 模式下的页面 SVG 使用统一的占位符约定（`{{TITLE}}`、`{{CHAPTER_TITLE}}`、`{{PAGE_TITLE}}`、`{{CONTENT_AREA}}` 等）。每个原生槽位都是带语义类型与正数 bounds 的顶层 `<g>`，普通槽位恰好包含一个 carrier；固定 Master/Layout 视觉是根级直接原子元素，绝不使用层级 `<g>`。Layout 可以有意保持零槽位。

`mirror` 工作区使用同一棵目录树，只是把按源页排序的 `001_cover.svg`、`002_toc.svg` 等文件放进 `templates/`。它可以保留原示例文字而不写 `{{...}}`，但导入识别出的原生内容槽仍带语义 metadata。

导入向量占位符统一写成 `data-icon="imported/<name>"`。校验、预览导出与最终导出都解析工作区根目录下同一份 `icons/imported/<name>.svg`；不需要、也不允许再创建 `templates/icons/` 副本。

### 全局注册与项目放置

- **全局库范围（`library`，默认）**把工作区写入 `skills/ppt-master/templates/<kind>/<id>/`，并完成全局注册。
- **项目范围（`project`）**把限定名 spec 写入 `projects/<name>/templates/design_spec.<kind>.<id>.md` 并跳过注册，因此同一个项目根可以分多次积累四种 kind 各一份，并把整套 bundle 交给任何指向该 root 的项目。Layout 与 Deck 同时存在时，Layout 拥有有效 roster。

项目范围不是私有或缩减格式。提供精确工作区根目录会把它加入 Step 3
候选输入，并让 Stage 1 默认展开模板模式；只有该 root 是唯一输入时才会预选。
每个不同 root 只迁移一次：携带其暴露的全部限定名 spec 及真实包自有
`images/`、`icons/`，并只安装有效 Layout-or-Deck SVG roster；忽略无关项目脚手架和 `exports/`。
若把其中一项迁入全局库，应将其放入单 kind 库工作区并执行对应注册命令。

---

## 三、模板的边界

避免常见误解：

- **可复用模板是一份显式工作区，不是打包后的源 PPTX。** Brand 与 Style 无 roster；Layout 与 Deck 才增加 structured SVG 合同。创作模式建立这份合同，mirror 则把经过验证的来源归属事实映射进去；导出只编译已声明的结构
- **模板不是一张不可拆分的“风格皮肤”。** Brand、Style、Layout 与 Deck 有意拆开身份、方向/方法、结构和应用，使每个片段都能单独复用；同时安装多个工作区时，各片段按明确的所有权规则生效
- **模板不会替你做内容决策**。策略师仍然会按内容判断每页用哪个版式、要不要扩展为变体，模板提供候选，不预设结果
- **`fidelity` 模式不等于像素级搬运**。即便是 `literal` 保真，AI 仍会把杂质和不必要的重复结构清理掉——载体保留几何，但不照抄冗余
- **`mirror` 的目标是受支持范围内的视觉及每张来源 Slide 的可达拓扑忠实，不是字节级 OOXML**。它继承源 PPT 的导入限制，只允许继承补全、固定结构层 group 展开等机械归一化。不支持的原生对象保留可用 SVG fallback 或明确报告；mirror 不归纳替代 ownership。

---

## 相关文档

- [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md) — 完整工作流规范（面向 AI 执行）
- [`templates/README.md`](../../skills/ppt-master/templates/README.md) — 四类模板及其发现索引
- [`references/template-designer.md`](../../skills/ppt-master/references/template-designer.md) — 模板设计师角色定义和 SVG 技术约束
- [常见问题：如何制作自定义模板](./faq.md#q-如何制作自定义模板) — FAQ 简版
