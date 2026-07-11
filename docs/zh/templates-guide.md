# 模板指南：选用、派生与边界

PPT Master 的“模板”是一份**结构 + 风格**的预设包：每张 SVG 都能独立完整预览，并用 metadata 显式标出 Master、Layout、Slide 与 placeholder；同时包含 `design_spec.md` 和配套素材。导出器据此确定性还原 PowerPoint 原生结构。

本文回答三个问题：

1. [怎么用已有模板？](#一选用已有模板)
2. [怎么把别人的 PPT / 自己的品牌做成模板？（重点）](#二派生新模板重点)
3. [模板的边界是什么？](#三模板的边界)

---

## 一、选用已有模板

### 触发方式

工作流**默认走自由设计**——不会主动问你要不要用模板，也不会基于内容主动推荐模板。模板是 opt-in 的，**只接受显式目录路径**：你在第一条消息里把模板目录的路径写出来。

### 怎么触发模板流程

在对话里把模板目录的路径写进去（位置不重要，只要明确即可）：

> "用这个模板做：`skills/ppt-master/templates/layouts/academic_defense/`" ✅
> "用上次那个模板：`projects/last_deck/templates/`" ✅
> "做一份产品介绍，模板用 `/Users/me/Desktop/our_brand_v3/`" ✅

AI 会把这个目录里的 SVG、`design_spec.md` 和素材安装到项目目录，然后进入 Strategist 阶段。路径可以指向内置库 `skills/ppt-master/templates/layouts/` 下的 package，或其他自包含模板目录。如果该路径本来就是当前项目自己的 `<project>/templates/` 根目录，流程会原地消费，不会再复制到自身。项目范围 create-template 可在同一对话里把这个已验证的精确路径直接交给 Step 3；这是“首条消息显式路径”规则的唯一例外。不要把另一个项目的 `templates/` 根目录当外部 package 使用：其中 `../images/` 与运行期图标引用只归属原项目；应先通过 library 范围提升为自包含 package。

### 什么**不会**触发模板流程

- **只写模板名、不给路径**："用 academic_defense 模板" / "做一份 招商银行 模板的产品介绍" → 走自由设计。AI 不会替你把名字解析成路径。要用模板，请直接给路径。
- **风格描述**："麦肯锡风格" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → 走自由设计。这些描述会顺着对话流到 Strategist 那边作为风格说明使用，但**不会复制任何模板文件**。
- **模糊意图**："想用个模板" / "选一个吧"——没给路径 → 走自由设计。

这是有意的——AI 永远**不做模糊 / 解释性判断**，不替你把名字解析成路径。要用模板，直接给路径。

想知道内置库里有哪些模板，问一句"有哪些模板可以用？"——AI 会从发现索引里列出名字和对应路径。单纯列出并不进入模板流程，需要你**把其中一条路径**再发回来才会触发 Step 3。

### 现有模板一览

模板按三种身份分目录：

- [`templates/brands/README.md`](../../skills/ppt-master/templates/brands/README.md) — 仅身份预设（color / typography / logo / voice / icon style），无 SVG 页面；Anthropic、Google
- [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) — 仅结构样板（canvas / page structure / page types / SVG roster），无身份；academic_defense、government_blue/red、ai_ops、medical_university、pixel_retro、psychology_attachment
- [`templates/decks/README.md`](../../skills/ppt-master/templates/decks/README.md) — 完整 PPT 复刻（身份 + 结构 + 中间段）；招商银行、中国电建_*、中汽研_*、重庆大学、中国电信

完整数据模型与三类的合成 / 冲突解决规则见 [`templates-architecture.md`](./templates-architecture.md)。

### 自由设计 vs 模板

自由设计不是"没有风格"，而是 AI 根据你的内容**为这一份 deck 现场设计**视觉系统；模板则是**沿用一套已经定型的结构和风格**。两条路都不会少做"设计"，区别只在于风格是即兴还是预设。

> 经验：内容方向明确、品牌或场景有强约束（咨询报告、政府汇报、答辩）→ 用模板。内容偏散文式、视觉氛围更重要（杂志风、纪录式叙事）→ 自由设计往往效果更好。

### 风格不是模板

**风格**是一种描述（"极简风" / "Keynote 风" / "杂志风"）——你在对话里打几个字。**模板**是一份要复制粘贴的资产包（SVG + design_spec + 素材），只在你给出**显式目录路径**时由工作流安装到项目里。

| | 模板 | 风格 |
|---|---|---|
| 怎么触发 | 消息里给出明确的目录路径 | 消息里写自由描述 |
| 发生什么 | 文件复制到项目；layouts 继承自模板 SVG | 描述流到 Strategist；色彩 / 字体 / 调性在策略师确认阶段里推荐 |
| 数值锁定 | 是 — 来源于模板的 `design_spec.md` | 否 — Strategist 现场推适合 deck 的具体值 |
| 适用场景 | 品牌锁定的 deck；强视觉约定的场景 | 心里有感觉但没有具体品牌承诺 |

风格描述可能看起来像模板名（比如 "学术风" 听上去像 `academic_defense/` 模板目录），但走的是**两套机制**——模板需要你给一个真实可复制的路径，风格描述是解释性语言。字面接近，落地完全是两条路。

### 常见风格描述

三条轴自由组合（"暗色科技 + 极简" 或 "杂志风 + 新中式" 都行）：

**美学路线**

| 风格 | 一句话特征 |
|---|---|
| **极简风 / Minimalist** | 高留白、2-3 色、单焦点、几乎零装饰 |
| **信息密集 / Information-dense** | 麦肯锡派结构化表格、密度高、conclusion-first |
| **Keynote 风** | 单页 Hero 文字、premium 留白、Apple 感 |
| **杂志风 / Editorial** | 大图当主体、不对称版式、字体反差强 |
| **文艺手绘** | 暖色、手绘质感、像 zine |

**行业 / 场景**

| 风格 | 一句话特征 |
|---|---|
| **商务咨询风** | 数据驱动、专业克制、蓝/灰主调 |
| **学术答辩风** | 严谨层级、citation-heavy、清晰朴素 |
| **政府汇报风** | 红/蓝、庄重对称、标题加粗 |
| **产品发布风** | 视觉冲击、营销大胆、Hero 单图 |
| **教学课件风** | 清晰层级、友好亲和、配色明亮 |
| **路演/BP 风** | 叙事驱动、金句配图、conclusion-bold |

**视觉调性**

| 风格 | 一句话特征 |
|---|---|
| **暗色科技风** | 深蓝/黑底、霓虹强调、未来感 |
| **像素复古** | 8-bit、扫描线、游戏机美学 |
| **新中式** | 留白、传统纹样克制使用、墨色/朱砂 |
| **北欧极简** | 浅色、原木自然、字号克制 |
| **孟菲斯/波普风** | 高饱和大色块、几何图形、80 年代 |
| **赛博朋克/蒸汽波** | 霓虹紫粉、网格、迷幻 |

你描述风格时，AI **不会基于这些词去挑模板**——它把这些词解释为对应的色彩 / 字体 / 版式建议，放到 策略师确认阶段里 `d` 项的第二层（视觉风格），然后驱动 e/f/g/h（色彩 / 图标 / 字体 / 图片）。你可以确认或调整。如果你想要的风格刚好对上库里某个模板（如 `academic_defense` / `pixel_retro` / `psychology_attachment`），有两条路可选：把模板的目录路径发出来锁定值，或描述风格让 AI 现场推适配你内容的值。

---

## 二、派生新模板（重点）

把你自己喜欢的 PPT、品牌指南、或一份现成的 PPTX，做成 PPT Master 可调用的模板。这是本文的核心。

### 入口：`/create-template` 工作流

完整规范见 [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md)。本节是面向用户的简要版本——你只需要在 IDE 对话里说：

```
请用 /create-template 工作流，基于下面的参考材料生成一个新模板。
```

接下来工作流会**强制**先和你确认一份模板简报（不允许跳过）。

### 第一步：准备参考材料

**强烈推荐：直接给原始 `.pptx` 文件。** 导入器会读取 OOXML，提取全部 Master、Layout、placeholder、主题与可复用素材，并生成分层分析参考。Template_Designer 据此重建一个干净 Master 与语义 Layout，输出完整且显式分层的 SVG；原 PPTX 只作分析输入，不进入新模板包。

也可以基于品牌指南从零设计：提供 logo、主色 HEX、字体、调性描述、几张氛围参考图，AI 会现场设计页面骨架。适合品牌方还没有成型 PPT、只有 VI 手册的场景。

> **没有源 PPTX 时的兜底**：截图集（`cover.png` / `chapter.png` / `content.png` / `closing.png` 等）也能跑，但保真度会明显下降——装饰、字体、版式细节都靠 AI 视觉推断。能拿到 `.pptx` 就尽量用 `.pptx`。截图更适合作为标注辅助（"这页是我想要的样子"）混进 PPTX 一起给。

### 第二步：模板简报（强制确认环节）

工作流不会偷偷推断——它会在动手前向你列出以下条目，等你确认或补全：

| 字段 | 说明 |
|------|------|
| **输出范围** | `library`（默认；所有项目可复用并进入全局索引）或 `project`（直接写入一个已初始化项目的模板根目录） |
| **目标项目** | 仅 `project` 必填；必须给出已初始化项目的精确路径 |
| **模板 ID** | 模板的可移植身份；在 `library` 下同时也是目录名 / 索引键。优先 ASCII slug，如 `acme_consulting`；中文品牌名也行，但要文件系统安全 |
| **显示名称** | 文档中的人类可读名 |
| **类别** | `brand` / `general` / `scenario` / `government` / `special` 五选一 |
| **适用场景** | 年报 / 咨询 / 答辩 / 政府汇报…… |
| **调性概要** | 一句话，如"现代克制、数据驱动" |
| **主题模式** | 浅色 / 深色 / 渐变…… |
| **画布格式** | 默认 `ppt169`（16:9），其他格式需提前指定 |
| **复刻模式** | `standard`（默认 5 页基本套）/ `fidelity`（按视觉版式簇生成变体）/ `mirror`（逐页保持原视觉，同时补齐显式层级归属） |
| **原生结构事实** | 简报会列出源 Master/Layout 数量、placeholder 身份和多母版情况；最终一律重建显式 SVG 结构（`template`）。 |
| **保真级别** | （`standard` / `fidelity` 有源时必填）`literal`（按原样复刻几何/装饰/精灵图裁剪）/ `adapted`（借结构和调性、允许设计演化）。封面 / 章节 / 结尾通常用 `literal`。**`mirror` 模式不询问**——隐含 literal |
| **关键词** | 3–5 个标签，用于索引检索 |
| 主题色 / 设计风格 / 素材清单 | 可选，可让 AI 从源里自动提取 |

确认后，工作流会回显一份完整简报并写入标记 `[TEMPLATE_BRIEF_CONFIRMED]`，从这一刻起后续步骤才会启动。**这是一个硬门——简报没确认，不会开始生成**。

如果选择 `project`，第一次写最终文件前还会做一次完整预检：目标必须已初始化、`templates/` 根目录必须为空、计划写入的位图与图标文件名不得和现有 `images/` / `icons/` 冲突。任一检查失败都会在写入前停止，不合并、不覆盖，也不会留下半套输出。

> 为什么这么严？无论模板进入全局库，还是只服务当前项目，它都是结构契约。先确认归属和几何，可避免半成品或资产落错目录。

### 第三步：选 standard、fidelity 还是 mirror？

这是派生模板里最容易混淆的决策。

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| 输出页数 | 5 页（封面/章节/目录/内容/结尾） | 视觉上真正不同的版式簇各一个变体——数量由源决定 | 每张源页 1:1 一页 |
| 抽象程度 | 高 —— 干净可复用骨架 | 中 —— 聚类后清理 | **零** —— 原样复制 |
| 作者占位符 | 是（`{{TITLE}}`、`{{CONTENT_AREA}}` 等） | 是 | 可保留原文字，但导入识别出的原生内容槽仍带语义 metadata |
| 适合场景 | 你只需要"调性 + 基本骨架"，未来用模板生成全新 deck | 源 PPTX 本身就是高度定制的版式库 | 别人的精装 deck 直接好用、想把每页都当参考页 |
| 典型例子 | 给品牌做基础模板 | 复刻一套政府汇报的 20 种章节版式 | 把一份 50 页的麦肯锡风格 deck 整套用作模板 |
| 必须有 PPTX 源吗 | 否 | **是** | **是** |
| 装饰复杂度 | 通常较简洁 | 需要保留精灵图裁剪等结构 | 保留原几何，并补齐显式层级归属 |

**关于精灵图**：PPTX 导出的素材常常是**一张大图 + 多页通过 viewBox 裁剪不同区域**。`fidelity` 和 `mirror` 模式下必须保留这层嵌套 `<svg viewBox=...>` 包装，不能扁平化为单张 `<image>`——否则裁剪信息丢失，画面会错位。工作流会自动校验这一点。

**`mirror` 模板怎么消费**：Strategist 为每个项目页选择一张 mirror 参考，Executor 复制完整 SVG 并原位修改可见文字，同时保留装饰、精灵图裁剪、几何坐标和全部 `data-pptx-*` 结构声明。

### 第四步：验证、注册与发现

模板生成完，两种范围都会先跑 [`svg_quality_checker.py`](../../skills/ppt-master/scripts/svg_quality_checker.py) 作为硬门。之后按确认的输出范围分流：

| 范围 | 产物 | 发现行为 |
|---|---|---|
| `library`（默认） | `skills/ppt-master/templates/<kind>/<id>/` | 验证通过后注册到对应 `layouts_index.json` 或 `decks_index.json` |
| `project` | 直接写 `<project>/templates/`；位图在 `<project>/images/`；提取图标同时保留在 `<project>/templates/icons/` 与 `<project>/icons/` | 跳过全部全局索引和库 README 更新 |

全局注册让模板**可被发现**——下次有人问"有哪些模板可用？"时，AI 会从索引里把它列出来。要在新项目里用它，仍然按 SKILL.md Step 3 的规则：在第一条消息里把目录路径写出来，例如 `用这个模板：skills/ppt-master/templates/layouts/<your_template_id>/`。项目范围模板有意保持项目私有，直接通过显式 `<project>/templates/` 路径原地消费。

选择 Deck/Layout 模板后，Strategist 确认阶段会进一步询问模板的使用方式：

- **适应性使用（adaptive）**——每页都选择一张模板 SVG；没有合适 Layout 时沿用同一 Master 创建新的显式 Layout
- **严格套用（strict）**——每页都选择一张模板 SVG，并保持其 Master/Layout/Placeholder 契约不变

### 派生后的目录长什么样

全局库范围（默认）保持原有的自包含 package：

```
skills/ppt-master/templates/layouts/<your_template_id>/
├── design_spec.md          # 设计规范，§VI 列出全部页面
├── 01_cover.svg
├── 02_chapter.svg
├── 02_toc.svg              # 可选
├── 03_content.svg
├── 03a_content_two_col.svg # fidelity 模式下的变体
├── 04_ending.svg
├── logo.png                # 品牌素材
└── bg_pattern.jpg
```

`standard` 和 `fidelity` 模式下的页面 SVG 里使用统一的占位符约定（`{{TITLE}}`、`{{CHAPTER_TITLE}}`、`{{PAGE_TITLE}}`、`{{CONTENT_AREA}}` 等），策略师阶段会按内容填充。

`mirror` 模板按源页序号每页一张 SVG。它可以保留原示例文字而不写 `{{...}}`，但导入识别出的原生内容槽仍带语义 metadata：

```
skills/ppt-master/templates/layouts/<your_template_id>/
├── design_spec.md          # frontmatter 设 replication_mode: mirror；§V Page Roster 逐页描述
├── 001_cover.svg
├── 002_toc.svg
├── 003_content.svg
├── 004_content.svg
├── ...
├── 049_content.svg
├── 050_ending.svg
└── *.png / *.jpg
```

项目范围会把薄模板直接写入已初始化项目的现有根目录，不会创建 `<project>/templates/<template_id>/`：

```
projects/<project>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_chapter.svg
│   ├── 03_content.svg
│   ├── 04_ending.svg
│   └── icons/             # package / 验证副本
├── images/
│   └── *.png / *.jpg      # SVG 统一引用 ../images/<name>
└── icons/
    └── *.svg              # 提取图标的运行期副本
```

### 项目级一次性定制 vs 全局模板

按资产归属选择输出范围：

- **全局库范围（`library`，默认）** = 进入 `skills/ppt-master/templates/<kind>/<id>/`，写入全局索引，供未来项目复用
- **项目范围（`project`）** = 把同一份经过验证的模板契约直接写进 `projects/<project>/templates/`，运行期图片/图标留在该项目内，不做全局注册

`/create-template` 两种范围都支持。模板只服务当前 deck 时用 `project`：仍然经过完整简报、显式 Master/Layout metadata 与模板校验，但不会污染全局库。另一个项目也要使用时，应选择 `library`。

---

## 三、模板的边界

避免常见误解：

- **可复用模板是一份完整 SVG 重建契约，不是源 PPTX package**。每页可独立预览，显式 metadata 负责在导出时还原 Master/Layout/Slide
- **模板不是"风格皮肤"**。它包含结构（页面有几块、信息层级如何分布）+ 风格（配色、字体、装饰），两者不可分割。试图只换"皮肤"不换结构，往往会让信息架构和视觉打架
- **模板不会替你做内容决策**。策略师仍然会按内容判断每页用哪个版式、要不要扩展为变体，模板提供候选，不预设结果
- **`fidelity` 模式不等于像素级搬运**。即便是 `literal` 保真，AI 仍会把杂质和不必要的重复结构清理掉——载体保留几何，但不照抄冗余
- **`mirror` 模式确实是像素级搬运——但它继承源 PPT 的导入限制**。图表、SmartArt、OLE 对象、EMF / WMF 媒体如果在 `pptx_template_import.py` 里 round-trip 失败，mirror 也会同样失败。flat SVG 是事实源——`<workspace>/svg-flat/` 里看着断了，mirror 模板也会断

---

## 相关文档

- [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md) — 完整工作流规范（面向 AI 执行）
- [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) — 现有模板一览
- [`references/template-designer.md`](../../skills/ppt-master/references/template-designer.md) — 模板设计师角色定义和 SVG 技术约束
- [常见问题：如何制作自定义模板](./faq.md#q-如何制作自定义模板) — FAQ 简版
