# 模板指南：选用、派生与边界

PPT Master 的"模板"是一份**结构 + 风格**的预设包：包含若干页面布局 SVG（封面/章节/目录/内容/结尾及其变体）、`design_spec.md` 设计规范，以及配套素材（logo、背景、装饰图）。它不是 PPTX 母版，也不是单纯的配色方案——而是一组可被工作流直接复用的页面骨架。

本文回答三个问题：

1. [怎么用已有模板？](#一选用已有模板)
2. [怎么把别人的 PPT / 自己的品牌做成模板？（重点）](#二派生新模板重点)
3. [模板的边界是什么？](#三模板的边界)

---

## 一、选用已有模板

### 触发方式

工作流**默认走自由设计**——不会主动问你要不要用模板，也不会基于内容主动推荐模板。模板是 opt-in 的，**只接受精确 slug**。

### 什么是 slug？

slug 是模板的唯一标识——[`templates/layouts/`](../../skills/ppt-master/templates/layouts/) 下的目录名，同时也是 [`layouts_index.json`](../../skills/ppt-master/templates/layouts/layouts_index.json) 里的顶层 key，三者完全一致。例如：

| slug | 目录 | 索引 key |
|---|---|---|
| `mckinsey` | `templates/layouts/mckinsey/` | `"mckinsey"` |
| `academic_defense` | `templates/layouts/academic_defense/` | `"academic_defense"` |
| `招商银行` | `templates/layouts/招商银行/` | `"招商银行"` |
| `中国电建_常规` | `templates/layouts/中国电建_常规/` | `"中国电建_常规"` |

slug 区分大小写，必须**一字不差**地出现在你的输入里才会触发模板流程。

### 怎么触发模板流程

在对话里把 slug 写进去（位置不重要，只要出现即可）：

> "用 **mckinsey** 模板做这份报告" ✅
> "做一份 **academic_defense** 模板的答辩 PPT" ✅
> "做一份 **招商银行** 风格的产品介绍" ✅

AI 会读取 [`layouts_index.json`](../../skills/ppt-master/templates/layouts/layouts_index.json)，把对应模板的 SVG、`design_spec.md` 和素材复制到项目目录，然后进入 Strategist 阶段。你也可以直接给出目录路径（`templates/layouts/mckinsey/`），AI 从路径里抽 slug。

### 什么**不会**触发模板流程

- **不是 slug 的风格描述**："麦肯锡风格" / "Google style" / "麦肯锡那种" / "极简风" / "Keynote 风" → 走自由设计。这些描述会顺着对话流到 Strategist 那边作为风格说明使用，但**不会复制任何模板文件**。
- **不完整 / 有歧义的匹配**："中国电建"——库里有 `中国电建_常规` 和 `中国电建_现代` 两个，没有唯一对应 → 走自由设计。AI 不替你猜（你可以再说一次精确的那个 slug 重新触发）。
- **模糊意图**："想用个模板" / "选一个吧"——没出现具体 slug → 走自由设计。

这是有意的——AI 永远**不做模糊 / 解释性判断**，不替你决定模糊的描述对应哪个模板。要用模板，请用精确 slug 点名。

想知道库里有哪些模板，问一句"有哪些模板可以用？"——AI 会从索引里列出 slug 清单。单纯列出并不进入模板流程，需要你再用其中一个 slug 重新说一次才会触发 Step 3。

### 现有模板一览

完整索引见 [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md)，按"品牌 / 通用 / 场景 / 政企 / 特殊"分类，每条都标注了主色和适用场景。当前共 21 套，覆盖麦肯锡、Google、Anthropic、招商银行、中国电建、中汽研、政府蓝/红、医学院、心理学、像素复古等。

### 自由设计 vs 模板

自由设计不是"没有风格"，而是 AI 根据你的内容**为这一份 deck 现场设计**视觉系统；模板则是**沿用一套已经定型的结构和风格**。两条路都不会少做"设计"，区别只在于风格是即兴还是预设。

> 经验：内容方向明确、品牌或场景有强约束（咨询报告、政府汇报、答辩）→ 用模板。内容偏散文式、视觉氛围更重要（杂志风、纪录式叙事）→ 自由设计往往效果更好。

### 风格不是模板

**风格**是一种描述（"极简风" / "Keynote 风" / "杂志风"）——你在对话里打几个字。**模板**是一份要复制粘贴的资产包（SVG + design_spec + 素材），只在你精确点出 slug 时由工作流安装到项目里。

| | 模板 | 风格 |
|---|---|---|
| 怎么触发 | 消息里出现精确 slug | 消息里写自由描述 |
| 发生什么 | 文件复制到项目；layouts 继承自模板 SVG | 描述流到 Strategist；色彩 / 字体 / 调性在八项确认里推荐 |
| 数值锁定 | 是 — 来源于模板的 `design_spec.md` | 否 — Strategist 现场推适合 deck 的具体值 |
| 适用场景 | 品牌锁定的 deck；强视觉约定的场景 | 心里有感觉但没有具体品牌承诺 |

风格描述可能看起来像模板名（比如 "麦肯锡风格" 看上去像 `mckinsey` slug），但走的是**两套机制**——slug 匹配是字面字符串检查，风格描述是解释性语言。同样的字，路径不同。

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

你描述风格时，AI **不会基于这些词去挑模板**——它把这些词解释为对应的色彩 / 字体 / 版式建议，放到 Strategist 八项确认里 `d` 项的第二层（视觉风格），然后驱动 e/f/g/h（色彩 / 图标 / 字体 / 图片）。你可以确认或调整。如果你想要的风格刚好对上库里某个模板（如 `academic_defense` / `mckinsey` / `pixel_retro`），有两条路可选：用 slug 触发模板得到锁定值，或描述风格让 AI 现场推适配你内容的值。

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

**强烈推荐：直接给原始 `.pptx` 文件。** 当前的 PPTX 导入管线已经做到接近高保真还原——工作流会用 [`pptx_template_import.py`](../../skills/ppt-master/scripts/pptx_template_import.py) 直接读取 OOXML，提取主题色、字体、每个 master 的主题摘要、母版/版式结构、placeholder 元数据和可复用图片资源。它会输出作为机器事实源的 layered `svg/`，以及用于视觉预览的自包含 `svg-flat/`，再交给 Template_Designer 重建出干净可维护的 SVG。封面、章节、装饰繁复的页面都能稳定还原，这是目前最靠谱的派生路径。

也可以基于品牌指南从零设计：提供 logo、主色 HEX、字体、调性描述、几张氛围参考图，AI 会现场设计页面骨架。适合品牌方还没有成型 PPT、只有 VI 手册的场景。

> **没有源 PPTX 时的兜底**：截图集（`cover.png` / `chapter.png` / `content.png` / `closing.png` 等）也能跑，但保真度会明显下降——装饰、字体、版式细节都靠 AI 视觉推断。能拿到 `.pptx` 就尽量用 `.pptx`。截图更适合作为标注辅助（"这页是我想要的样子"）混进 PPTX 一起给。

### 第二步：模板简报（强制确认环节）

工作流不会偷偷推断——它会在动手前向你列出以下条目，等你确认或补全：

| 字段 | 说明 |
|------|------|
| **模板 ID** | 目录名 / 索引键。优先 ASCII slug，如 `acme_consulting`；中文品牌名也行，但要文件系统安全 |
| **显示名称** | 文档中的人类可读名 |
| **类别** | `brand` / `general` / `scenario` / `government` / `special` 五选一 |
| **适用场景** | 年报 / 咨询 / 答辩 / 政府汇报…… |
| **调性概要** | 一句话，如"现代克制、数据驱动" |
| **主题模式** | 浅色 / 深色 / 渐变…… |
| **画布格式** | 默认 `ppt169`（16:9），其他格式需提前指定 |
| **复刻模式** | `standard`（默认 5 页基本套）/ `fidelity`（保留 PPTX 源里所有不同版式）—— `fidelity` 必须有 `.pptx` 源 |
| **保真级别** | （有源时必填）`literal`（按原样复刻几何/装饰/精灵图裁剪）/ `adapted`（借结构和调性、允许设计演化）。封面 / 章节 / 结尾通常用 `literal` |
| **关键词** | 3–5 个标签，用于索引检索 |
| 主题色 / 设计风格 / 素材清单 | 可选，可让 AI 从源里自动提取 |

确认后，工作流会回显一份完整简报并写入标记 `[TEMPLATE_BRIEF_CONFIRMED]`，从这一刻起后续步骤才会启动。**这是一个硬门——简报没确认，不会开始生成**。

> 为什么这么严？因为模板是入库资产，未来会被复用。一次说清楚，比生成完再返工便宜得多。

### 第三步：选 standard 还是 fidelity？

这是派生模板里最容易混淆的决策。

| | **standard** | **fidelity** |
|---|---|---|
| 输出页数 | 5 页（封面/章节/目录/内容/结尾） | 源 PPTX 里所有不同版式都保留 |
| 适合场景 | 你只需要"调性 + 基本骨架"，未来用模板生成全新 deck | 源 PPTX 本身就是高度定制的版式库，每种版式都有用 |
| 典型例子 | 给品牌做基础模板 | 复刻一套政府汇报模板的 20 种章节版式 |
| 必须有 PPTX 源吗 | 否 | **是** |
| 装饰复杂度 | 通常较简洁 | 需要保留精灵图（sprite sheet）裁剪等结构 |

**关于精灵图**：PPTX 导出的素材常常是**一张大图 + 多页通过 viewBox 裁剪不同区域**。`fidelity` 模式下必须保留这层嵌套 `<svg viewBox=...>` 包装，不能扁平化为单张 `<image>`——否则裁剪信息丢失，画面会错位。工作流会自动校验这一点。

### 第四步：注册与发现

模板生成完，工作流会：

1. 跑 [`svg_quality_checker.py`](../../skills/ppt-master/scripts/svg_quality_checker.py) 验证（硬门，不通过不入库）
2. 把模板 ID 注册到 [`layouts_index.json`](../../skills/ppt-master/templates/layouts/layouts_index.json)
3. 同步 [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) 表格

注册完毕，下次任何项目里你说"用 `<你的模板 ID>` 模板"，工作流就能找到它。

### 派生后的目录长什么样

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

页面 SVG 里使用统一的占位符约定（`{{TITLE}}`、`{{CHAPTER_TITLE}}`、`{{PAGE_TITLE}}`、`{{CONTENT_AREA}}` 等），策略师阶段会按内容填充。

### 项目级一次性定制 vs 全局模板

二者别搞混：

- **派生新模板** = 入全局库，在 `skills/ppt-master/templates/layouts/` 下，未来所有项目都能调用
- **项目级定制** = 只在 `projects/<project>/templates/` 里改这一份 deck 的页面，不入库、不影响其他项目

`/create-template` 工作流只做前者。后者直接在项目目录里改 SVG 即可，不需要走这个流程。

---

## 三、模板的边界

避免常见误解：

- **模板 ≠ 母版（Slide Master）**。PPT Master 的输出是原生 DrawingML 形状，不依赖 PowerPoint 母版机制。模板是 SVG 骨架，最终在导出阶段被翻译为 PPTX 形状
- **模板不是"风格皮肤"**。它包含结构（页面有几块、信息层级如何分布）+ 风格（配色、字体、装饰），两者不可分割。试图只换"皮肤"不换结构，往往会让信息架构和视觉打架
- **模板不会替你做内容决策**。策略师仍然会按内容判断每页用哪个版式、要不要扩展为变体，模板提供候选，不预设结果
- **`fidelity` 模式不等于像素级搬运**。即便是 `literal` 保真，AI 仍会把杂质和不必要的重复结构清理掉——载体保留几何，但不照抄冗余

---

## 相关文档

- [`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md) — 完整工作流规范（面向 AI 执行）
- [`templates/layouts/README.md`](../../skills/ppt-master/templates/layouts/README.md) — 现有模板一览
- [`references/template-designer.md`](../../skills/ppt-master/references/template-designer.md) — 模板设计师角色定义和 SVG 技术约束
- [常见问题：如何制作自定义模板](./faq.md#q-如何制作自定义模板) — FAQ 简版
