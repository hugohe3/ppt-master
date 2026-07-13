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

在对话里写出 Brand/Layout/Deck 工作区根目录（位置不重要，只要明确即可）：

> "用这个模板做：`skills/ppt-master/templates/layouts/presentation_core/`" ✅
> "用上次那个模板：`projects/last_deck/`" ✅
> "做一份产品介绍，模板用 `/Users/me/Desktop/our_brand_v3/`" ✅

对于当前所有模板类型，这里给的都是**模板工作区根目录**。Step 3 会解析其中的 `templates/design_spec.md`，然后把 `templates/` 及实际存在的 `images/`、`icons/` 安装进目标项目；如果工作区本来就是该项目根目录，则原地消费，并且始终不复制 `exports/`。Deck/Layout 还会校验 structured SVG 合同。路径可以指向 `skills/ppt-master/templates/<kind>/<id>/` 下的内置库工作区、`projects/<name>/` 下的项目工作区，或其他保持同样路由的工作区。当前对话刚完成 create-template 时，可把精确的已验证工作区根目录直接交给 Step 3；这是“首条消息显式路径”规则的唯一例外。

> **兼容性预检：** Step 3 也接受旧式平铺包，即 `design_spec.md` 与 SVG 直接位于所给根目录。目录平铺本身不需要恢复；只有 SVG 仍使用旧的原子 placeholder / 未映射 Master/Layout 语义时，才先运行 [`restore-pptx-structure`](../../skills/ppt-master/workflows/restore-pptx-structure.md)。Step 3 不会先复制语义旧包、再延后恢复。

### 什么**不会**触发模板流程

- **只写模板名、不给路径**："用 presentation_core 模板" / "做一份中国电信模板的产品介绍" → 走自由设计。AI 不会替你把名字解析成路径。要用模板，请直接给路径。
- **风格描述**："麦肯锡风格" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → 走自由设计。这些描述会顺着对话流到 Strategist 那边作为风格说明使用，但**不会复制任何模板文件**。
- **模糊意图**："想用个模板" / "选一个吧"——没给路径 → 走自由设计。

这是有意的——AI 永远**不做模糊 / 解释性判断**，不替你把名字解析成路径。要用模板，直接给路径。

想知道内置库里有哪些模板，问一句"有哪些模板可以用？"——AI 会从发现索引里列出名字和对应路径。单纯列出并不进入模板流程，需要你**把其中一条路径**再发回来才会触发 Step 3。

### 现有模板一览

模板按三种身份分目录：

- [`templates/brands/README.md`](../../skills/ppt-master/templates/brands/README.md) — 仅身份预设（color / typography / logo / voice / icon style），无 SVG 页面；Anthropic、Google
- [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) — 仅结构样板（canvas / page structure / page types / SVG roster），无身份；presentation_core
- [`templates/decks/README.md`](../../skills/ppt-master/templates/decks/README.md) — 完整 PPT 复刻（身份 + 结构 + 中间段）；中汽研、中国电信

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

风格描述和模板名仍走**两套机制**：“极简风”是解释性语言，`presentation_core/` 则是真实模板目录，必须提供显式路径。

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

你描述风格时，AI **不会基于这些词去挑模板**——它把这些词解释为对应的色彩 / 字体 / 版式建议，放到 策略师确认阶段里 `d` 项的第二层（视觉风格），然后驱动 e/f/g/h（色彩 / 图标 / 字体 / 图片）。你可以确认或调整。要使用内置 `presentation_core` 结构，就发送其工作区路径；要保持结构自由，则只描述风格，让 AI 现场适配内容。

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

**强烈推荐：直接给原始 `.pptx` 文件。** 导入器会读取 OOXML，提取全部 Master、Layout、placeholder、主题、原生形状事实与可复用素材，并生成分层分析参考。`standard` / `fidelity` 把它们当视觉参考，创作新的 SVG roster 与 Master/Layout/slot 系统；mirror 则一对一恢复来源身份、父子关系、placeholder 事实和受支持视觉。原 PPTX 只作分析证据，不进入新模板包。

也可以基于品牌指南从零设计：提供 logo、主色 HEX、字体、调性描述、几张氛围参考图，AI 会现场设计页面骨架。适合品牌方还没有成型 PPT、只有 VI 手册的场景。

> **没有源 PPTX 时的兜底**：截图集（`cover.png` / `chapter.png` / `content.png` / `closing.png` 等）也能跑，但保真度会明显下降——装饰、字体、版式细节都靠 AI 视觉推断。能拿到 `.pptx` 就尽量用 `.pptx`。截图更适合作为标注辅助（"这页是我想要的样子"）混进 PPTX 一起给。

### 第二步：模板简报（强制确认环节）

工作流不会偷偷推断——它会在动手前向你列出以下条目，等你确认或补全：

| 字段 | 说明 |
|------|------|
| **输出范围** | `library`（默认）或 `project`；两者使用相同的可移植工作区路由，只有 library 会进入全局索引 |
| **目标项目** | 仅 `project` 必填；必须给出已初始化项目的精确路径 |
| **模板 ID** | 模板的可移植身份；在 `library` 下同时也是目录名 / 索引键。优先 ASCII slug，如 `acme_consulting`；中文品牌名也行，但要文件系统安全 |
| **显示名称** | 文档中的人类可读名 |
| **类别** | `brand` / `general` / `scenario` / `government` / `special` 五选一 |
| **适用场景** | 年报 / 咨询 / 答辩 / 政府汇报…… |
| **调性概要** | 一句话，如"现代克制、数据驱动" |
| **主题模式** | 浅色 / 深色 / 渐变…… |
| **画布格式** | 默认 `ppt169`（16:9），其他格式需提前指定 |
| **复刻模式** | `standard`（默认精简基本套）/ `fidelity`（每个可复用语义家族一个变体）/ `mirror`（每张源页一个恢复原型）。`standard` / `fidelity` 创作新 SVG 语义；mirror 恢复来源结构，不做归纳。 |
| **原生结构事实** | 简报会列出源 Master/Layout 数量、父子关系、placeholder 身份和多母版情况。`standard` / `fidelity` 只把它们当参考；mirror 通过当前 `structured` 合同一对一恢复。 |
| **保真级别** | （`standard` / `fidelity` 有源时必填）`literal`（在新创作结构内尽量复现原几何、装饰和精灵图裁剪）/ `adapted`（借调性与构图、允许设计演化）。封面 / 章节 / 结尾通常用 `literal`。**`mirror` 模式不询问**——它恢复来源视觉。 |
| **关键词** | 3–5 个标签，用于索引检索 |
| 主题色 / 设计风格 / 素材清单 | 可选，可让 AI 从源里自动提取 |

确认后，工作流会回显一份完整简报并写入标记 `[TEMPLATE_BRIEF_CONFIRMED]`，从这一刻起后续步骤才会启动。**这是一个硬门——简报没确认，不会开始生成**。

无论选择哪种范围，第一次写最终文件前都会做一次完整预检：解析必需的 `templates/` 和实际需要的可选素材目录，要求 `templates/` 为空，并检查 `images/`、`icons/` 与 `templates/icons/` 中计划写入的位图和图标文件名没有冲突；只有明确要求审阅 PPTX 时才检查 `exports/`。项目范围还要求目标项目已经初始化。任一检查失败都会在写入前停止，不合并、不覆盖，也不会留下半套输出。

> 为什么这么严？无论模板进入全局库，还是只服务当前项目，它都是结构契约。先确认归属和几何，可避免半成品或资产落错目录。

### 第三步：选 standard、fidelity 还是 mirror？

这是派生模板里最容易混淆的决策。

| | **standard** | **fidelity** | **mirror** |
|---|---|---|---|
| 输出页数 | 4–5 页（封面/章节/内容/结尾，可选目录） | 每个可复用语义家族一个变体——数量由源决定 | 每张源页一个恢复原型（1:1 页面集合） |
| 抽象程度 | 高 —— 干净可复用骨架 | 中 —— 语义家族重新设计 | 拓扑层面不抽象，只做 structured 合同要求的机械归一化 |
| 作者占位符 | 是（`{{TITLE}}`、`{{CONTENT_AREA}}` 等） | 是 | 可保留原文字，但导入识别出的原生内容槽仍带语义 metadata |
| 适合场景 | 你只需要"调性 + 基本骨架"，未来用模板生成全新 deck | 源 PPTX 本身就是高度定制的版式库 | 别人的精装 deck 直接好用、想把每页都当参考页 |
| 典型例子 | 给品牌做基础模板 | 复刻一套政府汇报的 20 种章节版式 | 把 50 张源构图都保留为视觉忠实的模板原型 |
| 来源要求 | 无 | PPTX 或 SVG 视觉参考 | PPTX，或带完整显式结构合同的 SVG |
| 装饰复杂度 | 通常较简洁 | 需要保留精灵图裁剪等结构 | 保留原几何，并补齐显式层级归属 |

**关于精灵图**：PPTX 导出的素材常常是**一张大图 + 多页通过 viewBox 裁剪不同区域**。`fidelity` 和 `mirror` 模式下必须保留这层嵌套 `<svg viewBox=...>` 包装，不能扁平化为单张 `<image>`——否则裁剪信息丢失，画面会错位。工作流会自动校验这一点。

**关于 PowerPoint 原生形状**：完整导入 SVG 保留在临时分析工作区，模型读取的是移除 opaque payload 和重复 carrier 的轻量 projection；projection 永远不是导出源。创作模式使用紧凑 canonical metadata。Mirror 可在未改的 Slide-local/slot 对象上复用转换器已支持的 metadata；固定 Master/Layout 层保持直接原子，不支持或已修改的对象保留当前 SVG fallback。

**Mirror 图谱边界**：mirror 保留完整且受支持的来源 Master/Layout 图谱。它为每张来源 Slide 输出一个完整原型，并为未被任何来源 Slide 使用的 Layout 额外输出一个定义专用的 `layout_<layout_key>.svg`。后者通过独立 Layout roster 注册进 PowerPoint，不会变成发布页面；其父 Master 也随之保留。预检只在必要来源事实或受支持几何缺失时停止，不会仅因 Layout 未使用而停止。

**`mirror` 模板怎么消费**：Strategist 为每个项目页选择一张 mirror 参考，Executor 复制完整 SVG 并原位修改可见文字，同时保留装饰、精灵图裁剪、几何坐标和全部 `data-pptx-*` 结构声明。

### 第四步：验证、预览导出、注册与发现

模板生成完，两种范围都会先跑 [`svg_quality_checker.py`](../../skills/ppt-master/scripts/svg_quality_checker.py) 作为硬门。如果需要 PowerPoint 审阅文件，再运行可选预览导出；它会按需创建 `exports/<id>_template_preview.pptx`。唯一按范围分流的动作是全局注册：

| 范围 | 工作区根目录 | 预览 | 发现行为 |
|---|---|---|---|
| `library`（默认） | `skills/ppt-master/templates/<kind>/<id>/` | 可选 `exports/<id>_template_preview.pptx` | 校验后注册到对应 `layouts_index.json` 或 `decks_index.json` |
| `project` | `projects/<name>/` | 可选 `exports/<id>_template_preview.pptx` | 跳过全局索引注册 |

全局注册让模板**可被发现**——下次有人问“有哪些模板可用？”时，AI 会从索引里把它列出来。两种范围的用法相同：按 SKILL.md Step 3 的规则，在第一条消息里给出工作区根目录，例如 `用这个模板：skills/ppt-master/templates/layouts/<your_template_id>/` 或 `用这个模板：projects/<name>/`。项目工作区也可以迁移或被其他工作区复用，因为核心结构完全一致；只有放进全局库并需要被发现时才执行注册。

选择 Deck/Layout 模板后，Strategist 确认阶段会进一步询问模板的使用方式：

- **适应性使用（adaptive）**——每页都选择一张模板 SVG；没有合适 Layout 时沿用同一 Master 创建新的显式 Layout
- **严格套用（strict）**——每页都选择一张模板 SVG，并保持其 Master/Layout/Placeholder 契约不变

### 派生后的模板工作区长什么样

全局库与项目范围使用相同的核心结构。把下面的 `<template_workspace>` 替换为 `skills/ppt-master/templates/<kind>/<id>/` 或 `projects/<name>/` 即可：

```
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_chapter.svg
│   ├── 02_toc.svg              # 可选
│   ├── 03_content.svg
│   ├── 03a_content_two_col.svg # fidelity 变体
│   ├── 04_ending.svg
│   └── icons/                  # 使用时的 package / 校验副本
├── images/                         # 可选
│   └── *.png / *.jpg           # SVG 统一引用 ../images/<name>
├── icons/                          # 可选
│   └── *.svg                   # 提取向量素材的运行期副本
└── exports/                        # 可选；按需生成审阅文件
    └── <id>_template_preview.pptx
```

`standard` 和 `fidelity` 模式下的页面 SVG 使用统一的占位符约定（`{{TITLE}}`、`{{CHAPTER_TITLE}}`、`{{PAGE_TITLE}}`、`{{CONTENT_AREA}}` 等）。每个原生槽位都是带语义类型与正数 bounds 的顶层 `<g>`，普通槽位恰好包含一个 carrier；固定 Master/Layout 视觉是根级直接原子元素，绝不使用层级 `<g>`。Layout 可以有意保持零槽位。

`mirror` 工作区使用同一棵目录树，只是把按源页排序的 `001_cover.svg`、`002_toc.svg` 等文件放进 `templates/`。它可以保留原示例文字而不写 `{{...}}`，但导入识别出的原生内容槽仍带语义 metadata。

### 全局注册与项目放置

- **全局库范围（`library`，默认）**把工作区写入 `skills/ppt-master/templates/<kind>/<id>/`，并完成全局注册。
- **项目范围（`project`）**把同一份可移植工作区写入 `projects/<name>/`，并跳过注册。

项目范围不是私有或缩减格式。Step 3 可以直接接收任一工作区根目录；`templates/` 及实际存在的 `images/`、`icons/` 可以在两类根目录之间复制或迁移，无需改形。如果迁入全局库，再执行注册，让发现索引反映新位置。

---

## 三、模板的边界

避免常见误解：

- **可复用模板是一份显式 SVG 契约，不是打包后的源 PPTX**。创作模式新建该合同，mirror 通过该合同恢复来源归属；每页都能独立预览，导出只编译已声明的 Master/Layout/Slide 结构
- **模板不是"风格皮肤"**。它包含结构（页面有几块、信息层级如何分布）+ 风格（配色、字体、装饰），两者不可分割。试图只换"皮肤"不换结构，往往会让信息架构和视觉打架
- **模板不会替你做内容决策**。策略师仍然会按内容判断每页用哪个版式、要不要扩展为变体，模板提供候选，不预设结果
- **`fidelity` 模式不等于像素级搬运**。即便是 `literal` 保真，AI 仍会把杂质和不必要的重复结构清理掉——载体保留几何，但不照抄冗余
- **`mirror` 的目标是受支持范围内的视觉与来源拓扑忠实，不是字节级 OOXML**。它继承源 PPT 的导入限制，只允许固定结构层 group 展开等机械归一化。不支持的原生对象保留可用 SVG fallback 或明确报告；mirror 不归纳替代 ownership。

---

## 相关文档

- [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md) — 完整工作流规范（面向 AI 执行）
- [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) — 现有模板一览
- [`references/template-designer.md`](../../skills/ppt-master/references/template-designer.md) — 模板设计师角色定义和 SVG 技术约束
- [常见问题：如何制作自定义模板](./faq.md#q-如何制作自定义模板) — FAQ 简版
