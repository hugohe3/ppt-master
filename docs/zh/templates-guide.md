# 模板指南：选用、派生与边界

[English](../templates-guide.md) | [Chinese](./templates-guide.md)

---

PPT Master 模板是一种可复用工作区，明确分为三类：**Brand** 只拥有身份系统，**Layout** 只拥有可复用页面结构，**Deck** 同时拥有两者及 deck 专属概览信息。Layout 与 Deck 工作区包含声明 Master / Layout / slot 合同的完整 SVG 原型；Brand 工作区则有意不包含 SVG roster。每个工作区的 `design_spec.md` 与配套素材共同声明该 kind 实际提供什么。

本文回答三个问题：

1. [怎么用已有模板？](#一选用已有模板)
2. [怎么把别人的 PPT / 自己的品牌做成模板？（重点）](#二派生新模板重点)
3. [模板的边界是什么？](#三模板的边界)

## 60 秒选对模板路线

先看你手里有什么，以及最终想得到什么：

| 起点与目标 | 路线 | 可直接复制的请求 |
|---|---|---|
| 手里是原始 `.pptx`，想保留现有页面壳并替换内容 | **Fill Native PPTX** | `用 projects/source/template.pptx 套入 projects/source/content.md 的内容。` |
| 已有可复用 Brand/Layout/Deck 工作区，想生成一份全新 deck | **Generate PPTX + 显式工作区路径** | `用 sources/report.pdf 做 deck，模板用 skills/ppt-master/templates/layouts/presentation_core/。` |
| 手里是 PPTX、SVG、品牌手册、网站、图片或混合参考，想先建立可复用系统 | **Create Template → Generate PPTX** | `用 /create-template 从 projects/brand/our_deck.pptx 创建一个可复用 Deck 工作区。` |

不要把原始 `.pptx` 当作 Generate PPTX 的模板路径。想沿用它的现有页面就直接回填；想建立可复用系统，就先运行 Create Template。

再按需要复用的内容选择工作区 kind：

| Kind | 复用什么 | 原生 PowerPoint 结果 |
|---|---|---|
| **Brand** | 颜色、字体、Logo、语调、图标风格 | 只提供身份约束。生成页面保持 Slide 本地，文件只有干净的项目 Master 与 Blank Layout 脚手架。 |
| **Layout** | 页面语法、Master/Layout 身份、槽位与版式 roster | 结构化 deck，包含可复用原生 Master、具名 Layout 与 placeholder；身份系统另行选择。 |
| **Deck** | 品牌身份与页面结构一起复用 | 结构化 deck，同时带完整身份系统和可复用原生 Master、具名 Layout 与 placeholder。 |

最容易避免误用的两条规则：

1. 提供**工作区根目录**，不要只给它的 `templates/` 子目录，也不要只写模板名。
2. 在首次生成请求里写明工作区路径。唯一例外是同一对话刚完成 Create Template，可立即把已验证工作区交给 Generate PPTX。

---

## 一、选用已有模板

### 触发方式

工作流**默认走自由设计**——不会主动问你要不要用模板，也不会基于内容主动推荐模板。模板是 opt-in 的，**只接受显式目录路径**：你在第一条消息里把模板目录的路径写出来。

### 怎么触发模板流程

在对话里写出 Brand/Layout/Deck 工作区根目录（位置不重要，只要明确即可）：

> "用这个模板做：`skills/ppt-master/templates/layouts/presentation_core/`" ✅
> "用上次那个模板：`projects/last_deck/`" ✅
> "做一份产品介绍，模板用 `/Users/me/Desktop/our_brand_v3/`" ✅

对于当前所有模板类型，这里给的都是**模板工作区根目录**。Step 3 会解析其中的 `templates/design_spec.md`，然后把 `templates/` 及实际存在的 `images/`、`icons/` 安装进目标项目；如果工作区本来就是该项目根目录，则原地消费，并且始终不复制 `exports/`。Deck/Layout 还会校验 structured SVG 合同。路径可以指向 `skills/ppt-master/templates/<kind>/<id>/` 下的内置库工作区、`projects/<name>/` 下的项目工作区，或其他保持同样路由的工作区。当前对话刚完成 create-template 时，可把精确的已验证工作区根目录直接交给 Step 3；这是“首条消息显式路径”规则的唯一例外。

> **兼容性预检：** Step 3 也接受 `design_spec.md` 与 SVG 直接位于所给根目录的平铺工作区，但这些 SVG 必须已经满足当前合同。目录平铺本身没有问题；旧的原子 placeholder、未映射 Master/Layout 等语义旧包会被拒绝。先运行 `create-template` 创建新工作区，再从该工作区生成新的 structured 页面；不会原地升级旧包。

### 什么**不会**触发模板流程

- **只写模板名、不给路径**："用 presentation_core 模板" / "做一份中国电信模板的产品介绍" → 走自由设计。AI 不会替你把名字解析成路径。要用模板，请直接给路径。
- **风格描述**："麦肯锡风格" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → 走自由设计。这些描述会顺着对话流到 Strategist 那边作为风格说明使用，但**不会复制任何模板文件**。
- **模糊意图**："想用个模板" / "选一个吧"——没给路径 → 走自由设计。

这是有意的——AI 永远**不做模糊 / 解释性判断**，不替你把名字解析成路径。要用模板，直接给路径。

想知道内置库里有哪些模板，问一句"有哪些模板可以用？"——AI 会从发现索引里列出名字和对应路径。单纯列出并不进入模板流程，需要你**把其中一条路径**再发回来才会触发 Step 3。

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

“模板工作区”这些标签可以不写，但路径本身必须明确。如果给出两个相同 kind 的路径，工作流会进入既有冲突解决门，不会静默替你选一个。

### 现有模板一览

模板按三种 kind 分目录，并分别由发现索引维护：

- [`brands_index.json`](../../skills/ppt-master/templates/brands/brands_index.json) — 仅身份工作区：color / typography / logo / voice / icon style，不含 SVG 页面 roster
- [`layouts_index.json`](../../skills/ppt-master/templates/layouts/layouts_index.json) — 仅结构工作区：canvas / 页面语法 / page types / SVG roster，身份系统下游再选
- [`decks_index.json`](../../skills/ppt-master/templates/decks/decks_index.json) — 完整身份 + 结构工作区，包含 deck 专属概览信息

直接问“有哪些模板可以用？”即可得到带工作区路径的可读清单。索引是当前安装内容的真值，三类 README 负责定义合同。完整数据模型与三类的合成 / 冲突解决规则见 [`templates-architecture.md`](./templates-architecture.md)。

### 自由设计 vs 模板

自由设计不是“没有结构”或“没有风格”——Strategist 仍会为这份 deck 规划叙事、层级与视觉系统，但生成页面使用 `pptx_structure.mode: flat`，所有可见对象都保留在 Slide 本地。仅使用 Brand 工作区时同样保持 `flat`，只是由 Brand 提供身份约束。Layout 与 Deck 工作区使用 `pptx_structure.mode: structured`，因为它们提供显式可复用的 Master / Layout / slot 合同。

> 经验：需要锁定身份系统时用 Brand，需要复用页面结构时用 Layout，两者都要一起复用时用 Deck；希望版式从内容出发重新生长时走自由设计。

### 风格不是模板

**风格说明**是解释性语言（“极简风” / “Keynote 风” / “杂志风”），由 Strategist 转化为具体设计选择。**模板**则是真实存在的 Brand / Layout / Deck 工作区，只有在你给出**显式目录路径**时才会被工作流消费。

| | 模板 | 风格 |
|---|---|---|
| 怎么触发 | 消息里给出明确的目录路径 | 消息里写自由描述 |
| 提供什么 | 由 kind 声明的身份段、结构段或两者 | 由 Strategist 解释为 mode、visual style、色彩、字体、图标与图片方向 |
| 如何确认 | 模板拥有的值构成起始合同；用户最终确认的选择仍然权威 | 没有预写数值；Strategist 给出具体候选，由用户确认 |
| 适用场景 | 复用已有身份系统和 / 或页面系统 | 只表达想要的感觉，不采用已存工作区 |

风格描述和模板名仍走**两套机制**：“极简风”是解释性语言，`presentation_core/` 则是真实模板目录，必须提供显式路径。

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

入口名称始终保持 **Create Template**。它只分派一个子工作流：仅复用身份走 Create Brand，仅复用品牌中立的结构走 Create Layout，身份与结构一起复用走 Create Deck（两者都需要时默认选它）。子工作流一旦选定，不会在简报里再次选 kind。

### 第一步：准备参考材料包或简报

你可以直接在对话中输入文字或粘贴要求，也可以提供 Markdown/TXT、DOCX/PDF/HTML/URL、网站、图片/截图、logo/icon/字体资产、PPTX/SVG，或这些材料的任意组合。工作流会分析每个适用通道，保留来源，并在强制简报中暴露冲突，而不是静默选择某一个来源。凡是你本人明确写出的值，无论来自对话、粘贴文字还是你编写的简报文件，都属于决策；文件载体本身不会把它变成事实。事实必须来自可独立追溯的外部权威，或可由机器直接观察的源文件/包元数据。视觉估算与模糊文字的解释在确认前都只是建议。

**当现有演示文稿的原生结构很重要时，请直接提供原始 `.pptx` 文件。** 导入器会读取 OOXML，把包内实际存在且受支持的 Master、Layout、placeholder、主题、原生形状与可复用素材事实提取成分层分析参考。`standard` / `fidelity` 把它们当视觉参考，创作新的 SVG roster 与 Master/Layout/slot 系统；mirror 则把这些已验证的来源事实物化到新工作区，不补造缺失拓扑或设计意图。原 PPTX 始终是不可变的分析证据，不进入新模板包。

也可以基于品牌指南从零设计：提供 logo、主色 HEX、字体、调性描述、几张氛围参考图，AI 会现场设计页面骨架。适合品牌方还没有成型 PPT、只有 VI 手册的场景。

> **证据边界：** 图片、截图、文字、文档、网站和零散资产都可以独立驱动 `standard`。`fidelity` 需要 PPTX/SVG 页面证据；`mirror` 需要原始 PPTX 或完整的当前结构化 SVG 合同。补充来源可以解释 mirror 证据，但不能补造或改变其原生拓扑。

### 第二步：模板简报（强制确认环节）

工作流不会偷偷推断——它会在动手前向你列出以下条目，等你确认或补全：

| 字段 | 说明 |
|------|------|
| **输出范围** | `library`（默认）或 `project`；两者使用相同的可移植工作区路由，只有 library 会进入全局索引 |
| **目标项目** | 仅 `project` 必填；必须给出已初始化项目的精确路径 |
| **已选子工作流** | Create Brand / Create Layout / Create Deck，由入口分派后固定 |
| **模板 ID** | 模板的可移植身份；在 `library` 下同时也是目录名 / 索引键。优先 ASCII slug，如 `acme_consulting`；中文品牌名也行，但要文件系统安全 |
| **显示名称** | 文档中的人类可读名 |
| **类别** | `brand` / `general` / `scenario` / `government` / `special` 五选一 |
| **适用场景** | 年报 / 咨询 / 答辩 / 政府汇报…… |
| **调性概要** | 一句话，如"现代克制、数据驱动" |
| **主题模式** | 仅 Create Layout/Create Deck：浅色 / 深色 / 渐变…… |
| **画布格式** | 仅 Create Layout/Create Deck；默认 `ppt169`（16:9），其他格式需提前指定 |
| **复刻模式** | 仅 Create Layout/Create Deck：`standard`（默认精简、由确认简报驱动；可包含少量明确要求的差异化变体）/ `fidelity`（根据来源证据覆盖更广的有用语义家族）/ `mirror`（每张源页一个物化原型）。`standard` / `fidelity` 创作新 SVG 语义；mirror 只保留来源包内已经存在且验证通过的事实。 |
| **原生结构事实** | 仅 Create Layout/Create Deck：简报会列出源 Master/Layout 数量、父子关系、placeholder 身份和多母版情况。`standard` / `fidelity` 只把它们当参考；mirror 把受支持事实一对一映射进当前 `structured` 合同。 |
| **保真级别** | 仅 Create Layout/Create Deck；`standard` / `fidelity` 有源时必填，选择 `literal` 或 `adapted`。**`mirror` 模式不询问**——它保留受支持的来源视觉。 |
| **关键词** | 3–5 个标签，用于索引检索 |
| 主题色 / 设计风格 / 素材清单 | 可选，可让 AI 从源里自动提取 |

确认后，工作流会回显一份完整简报并写入标记 `[TEMPLATE_BRIEF_CONFIRMED]`，从这一刻起后续步骤才会启动。**这是一个硬门——简报没确认，不会开始生成**。

无论选择哪种范围，第一次写最终文件前都会做一次完整预检：解析必需的 `templates/` 和实际需要的可选素材目录，要求 `templates/` 为空，并检查 `images/` 与 `icons/imported/` 中计划写入的位图和导入向量文件名没有冲突；只有明确要求审阅 PPTX 时才检查 `exports/`。项目范围还要求目标项目已经初始化。项目初始化时已存在的空脚手架目录可以保留且不会被算作模板产物；Create Template 不会为了保留空路径而新建可选目录。任一检查失败都会在写入前停止，不合并、不覆盖，也不会留下半套输出。

> 为什么这么严？无论模板进入全局库，还是只服务当前项目，它都是结构契约。先确认归属和几何，可避免半成品或资产落错目录。

### 第三步：Create Layout/Create Deck 选择 standard、fidelity 还是 mirror？

这是派生结构型模板里最容易混淆的决策。Create Brand 不执行这一步，因为 identity-only 工作没有 SVG roster 或原生结构。

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| 输出页数 | 通常 4–6 页：封面/章节/结尾、可选目录，以及一个或少量简报明确要求的内容 Layout | 覆盖来源证据中更广的有用语义家族——数量由来源决定 | 每张源页一个物化原型（1:1 页面集合） |
| 抽象程度 | 高 —— 干净可复用骨架 | 中 —— 语义家族重新设计 | 拓扑层面不抽象，只做 structured 合同要求的机械归一化 |
| 作者占位符 | 是（`{{TITLE}}`、`{{CONTENT_AREA}}` 等） | 是 | 可保留原文字，但导入识别出的原生内容槽仍带语义 metadata |
| 适合场景 | 你需要“调性 + 精简骨架”，也可能包含少量简报明确要求的结构，未来用于生成全新 deck | 源 PPTX 本身就是高度定制的版式库，需要更广的来源驱动覆盖 | 别人的精装 deck 直接好用、想把每页都当参考页 |
| 典型例子 | 给品牌做基础模板 | 复刻一套政府汇报的 20 种章节版式 | 把 50 张源构图都保留为视觉忠实的模板原型 |
| 来源要求 | 无 | PPTX 或 SVG 视觉参考 | PPTX，或带完整显式结构合同的 SVG |
| 装饰复杂度 | 通常较简洁 | 需要保留精灵图裁剪等结构 | 保留原几何，并补齐显式层级归属 |

**关于精灵图**：PPTX 导出的素材常常是**一张大图 + 多页通过 viewBox 裁剪不同区域**。`fidelity` 和 `mirror` 模式下必须保留这层嵌套 `<svg viewBox=...>` 包装，不能扁平化为单张 `<image>`——否则裁剪信息丢失，画面会错位。工作流会自动校验这一点。

**关于 PowerPoint 原生形状**：完整导入 SVG 作为原生载荷后备留在临时分析工作区且保持不可变；模板创建使用轻量、可编辑的 `authoring-svg/` IR 及其 source-ref/hash manifest。创作模式使用项目规范化 SVG，只有精确匹配已登记 preset 时才使用 compact authored-preset 组。Mirror 从 IR 物化最终模板 SVG，只为未改且 hash 匹配的 Slide-local/slot ref 重新接入转换器已支持的载荷；固定 Master/Layout 层保持直接原子，不支持或已修改的对象保留当前 SVG fallback，最终模板不包含 IR 专用 ref。

对于 PPTX 来源的 Type A mirror，最终物化统一使用一个确定性命令：

```bash
python3 skills/ppt-master/scripts/mirror_template_materialize.py \
  "<import_workspace>" "<empty_template_workspace>"
```

它会先校验 IR manifest、不可变来源 hash、完整原生图谱、可见性事实和
导入向量闭包，再原子发布按源顺序排列的 SVG roster 及
`icons/imported/`、`images/` 素材。它不要求、也不会把按需生成的
`svg-flat/` 校验视图当成模板来源，并且不会生成 `design_spec.md`；设计角色必须针对物化后的 roster 编写该简报。

**Mirror 图谱边界**：mirror 保留完整且受支持的来源 Master/Layout 图谱。它为每张来源 Slide 输出一个完整原型，并为未被任何来源 Slide 使用的 Layout 额外输出一个定义专用的 `layout_<layout_key>.svg`。后者通过独立 Layout roster 注册进 PowerPoint，不会变成发布页面；其父 Master 也随之保留。预检只在必要来源事实或受支持几何缺失时停止，不会仅因 Layout 未使用而停止。

**按 mirror 创建的工作区怎么消费**：从来源到工作区的 `replication_mode: mirror` 是能力，不是项目选择。开放式沟通契约确认后，Stage 2 只在“重复制作已知固定成果、且新内容适配现有页面角色与文字拓扑”时推荐 `mirror`；结构应延续但内容需要重排时用 `layout`；只需身份语言或论证必须换结构时用 `style`。确认 `mirror` 后，Strategist 为每个项目页选择一张原型，Executor 复制完整 SVG，只修改允许变更的可见文字，同时保留装饰、精灵图裁剪、几何坐标和规范化结构声明；这仍不要求沿用来源页数或页序。Mirror 保留受支持的画面外观，不承诺保留来源 PPTX 的分组编辑层级。

### 第四步：验证、预览导出、注册与发现

模板生成完，两种范围都会先跑 [`svg_quality_checker.py`](../../skills/ppt-master/scripts/svg_quality_checker.py) 作为硬门：Brand 校验 identity-only 规范与素材引用，Layout/Deck 校验 SVG roster 和 structured 合同。如果需要 PowerPoint 审阅文件，再运行可选预览导出；它会按需创建 `exports/<id>_template_preview.pptx`。创作型模板会只在临时预览副本中使用简短占位示例，避免较长的 canonical marker 换行，不会修改源 SVG。唯一按范围分流的动作是全局注册：

| 范围 | 工作区根目录 | 预览 | 发现行为 |
|---|---|---|---|
| `library`（默认） | `skills/ppt-master/templates/<kind>/<id>/` | Create Brand：不适用；Create Layout/Create Deck：单 Master 可选、多 Master 必须 | 校验后注册到对应 `brands_index.json`、`layouts_index.json` 或 `decks_index.json` |
| `project` | `projects/<name>/` | 沿用同一套 kind-specific 审阅规则 | 跳过全局索引注册 |

全局注册让模板**可被发现**——下次有人问“有哪些模板可用？”时，AI 会从索引里把它列出来。两种范围的用法相同：按 SKILL.md Step 3 的规则，在第一条消息里给出工作区根目录，例如 `用这个模板：skills/ppt-master/templates/layouts/<your_template_id>/` 或 `用这个模板：projects/<name>/`。项目工作区也可以迁移或被其他工作区复用，因为核心结构完全一致；只有放进全局库并需要被发现时才执行注册。

选择 Deck/Layout 模板后，Strategist 确认阶段会进一步询问模板的使用方式：

- **适应性使用（adaptive）**——每页都选择一张模板 SVG；没有合适 Layout 时沿用同一 Master 创建新的显式 Layout
- **严格套用（strict）**——每页都选择一张模板 SVG，并保持其 Master/Layout/Placeholder 契约不变

### 如何确认母版与版式真的生效

使用 Layout 或 Deck 工作区生成后，在 Microsoft PowerPoint 中检查发布文件：

| 检查位置 | 预期结果 |
|---|---|
| **视图 → 幻灯片母版** | 能看到模板声明的 Master 与具名 Layout。 |
| **开始 → 新建幻灯片** | 版式选择器中能在预期 Master 下看到可复用 Layout 名称。 |
| 选中生成页并查看 **版式** | 页面绑定到声明的 Layout，而不是导出器猜出的通用版式。 |
| 点击可复用内容区域 | 模板槽位表现为带声明类型与边界的原生 placeholder。 |
| 从某个已导出 Layout 新建一页 | 不复制成品内容页，也能得到该 Master/Layout 的固定视觉与 placeholder 几何。 |

Brand-only 的目标不同：它只施加身份约束，创作内容仍保持 Slide 本地，因此不应期待除干净包脚手架之外的可复用 Layout roster。

`exports/<id>_template_preview.pptx` 是 Create Template 按需或按规则生成的审阅证据，不是模板输入；真正生成时始终传工作区根目录。

Master/Layout 行为以 Microsoft PowerPoint 为验收目标。Keynote、WPS 与 LibreOffice 可以打开 PPTX，但可能归一化模板结构，或在加载包含大量未使用 Layout 的 mirror roster 时明显更慢。

### 派生后的模板工作区长什么样

全局库与项目范围使用相同的核心结构。把下面的 `<template_workspace>` 替换为 `skills/ppt-master/templates/<kind>/<id>/` 或 `projects/<name>/` 即可：

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
- **项目范围（`project`）**把同一份可移植工作区写入 `projects/<name>/`，并跳过注册。

项目范围不是私有或缩减格式。Step 3 可以直接接收任一工作区根目录；`templates/` 及实际存在的 `images/`、`icons/` 可以在两类根目录之间复制或迁移，无需改形。如果迁入全局库，再执行注册，让发现索引反映新位置。

---

## 三、模板的边界

避免常见误解：

- **可复用模板是一份显式工作区，不是打包后的源 PPTX。** Brand 可以只有身份系统；Layout 与 Deck 才增加 structured SVG 合同。创作模式建立这份合同，mirror 则把经过验证的来源归属事实映射进去；导出只编译已声明的结构
- **模板不是一张不可拆分的“风格皮肤”。** Brand、Layout 与 Deck 有意把身份和结构拆开，使每一段都能按明确所有权单独复用或参与合成
- **模板不会替你做内容决策**。策略师仍然会按内容判断每页用哪个版式、要不要扩展为变体，模板提供候选，不预设结果
- **`fidelity` 模式不等于像素级搬运**。即便是 `literal` 保真，AI 仍会把杂质和不必要的重复结构清理掉——载体保留几何，但不照抄冗余
- **`mirror` 的目标是受支持范围内的视觉与来源拓扑忠实，不是字节级 OOXML**。它继承源 PPT 的导入限制，只允许固定结构层 group 展开等机械归一化。不支持的原生对象保留可用 SVG fallback 或明确报告；mirror 不归纳替代 ownership。

---

## 相关文档

- [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md) — 完整工作流规范（面向 AI 执行）
- [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) — 现有模板一览
- [`references/template-designer.md`](../../skills/ppt-master/references/template-designer.md) — 模板设计师角色定义和 SVG 技术约束
- [常见问题：如何制作自定义模板](./faq.md#q-如何制作自定义模板) — FAQ 简版
