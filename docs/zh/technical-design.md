# 技术路线

[English](../technical-design.md) | [中文](./technical-design.md)

---

## 设计哲学 —— AI 是你的设计师，不是完工师

生成的 PPTX 是一份**设计稿**，而非成品。把它理解成建筑师的效果图：AI 负责视觉设计、排版布局和内容结构，交付给你一个高质量的起点。要想获得真正精良的成品，**需要你自己在 PowerPoint 里做精装修**：换掉形状、细化图表、调整配色、把占位图形替换成原生对象。这个工具的目标是消除 90% 的从零开始的工作量，而不是替代人在最后一公里的判断。不要指望 AI 一遍搞定所有——好的演示文稿从来不是这样做出来的。

**工具的上限是你的上限。** PPT Master 放大的是你已有的能力——你有设计感和内容判断力，它帮你快速落地；你不知道一个好的演示文稿应该长什么样，它也没法替你知道。输出的质量，归根结底是你自身品味与判断力的映射。

---

## 系统架构

```
用户输入 (PDF/DOCX/XLSX/PPTX/URL/Markdown/主题文本)
    ↓
[源内容转换] → source_to_md/pdf_to_md.py / doc_to_md.py / excel_to_md.py / ppt_to_md.py / web_to_md.py
    ├── Markdown 是内容契约
    └── PPTX intake 写入 analysis/<stem>.identity.json、<stem>.slide_library.json、source_profile.json
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[模板 / 品牌 / 布局（可选）] — 默认跳过，直接自由设计
    仅在用户提供明确模板目录路径且其中 design_spec.md 声明 kind: brand/layout/deck 时触发
    原生 PPTX 模板请求进入 template-fill；可复用 SVG 模板需先通过 create-template 创建
    ↓
[Strategist] 策略师 - 两层八项确认与设计规范 → design_spec.md + spec_lock.md
    ↓
[Image Acquisition] 图片获取（当资源列表中有需要 AI 生成、网络搜索或切片的图片时）
    ↓
[Executor] 执行师
    ├── 生成开始前启动 live preview，并在生成期间保持可用
    ├── 视觉构建：按页顺序连续生成 SVG 页面 → svg_output/
    ├── [Quality Check] svg_quality_checker.py（强制通过，0 错误）
    └── 讲稿生成：完整讲稿 → notes/total.md
    ↓
[图表校准（可选）] → verify-charts 工作流（含数据图表的幻灯片在此步骤校准坐标）
    ↓
[视觉自检（可选，opt-in）] → visual-review 工作流（仅在用户明确请求时触发）
    ↓
[后处理] → total_md_split.py（拆分讲稿）→ finalize_svg.py → svg_to_pptx.py
    ↓
输出：
    exports/
    ├── presentation_<timestamp>.pptx          ← 原生形状版（DrawingML）— 唯一标准产物，编辑/交付从这里走
    └── presentation_<timestamp>_svg.pptx      ← SVG 快照版 pptx — 像素级视觉参考（加 --svg-snapshot 时生成）

    # 默认流程（未指定 -o）始终写入
    backup/<timestamp>/
    └── svg_output/                            ← Executor 原始 SVG 备份（重跑 finalize_svg → svg_to_pptx 即可重建 pptx）
```

以下直接 PPTX 工作流会有意绕过这条 SVG 路线：

| 工作流 | 输入角色 | 输出机制 | 为什么独立 |
|---|---|---|---|
| `template-fill-pptx` | 原生 PPTX 模板 deck + 新材料 | 克隆选中的幻灯片，并在 OOXML 层改写文本 / 表格 / 图表 | 保留用户的 PowerPoint 原生页面壳，而不是转成 SVG |
| `native-enhance-pptx` | 内容与版式都应保持稳定的已完成 PPTX | 在 OOXML 层直接补讲稿、旁白、计时和转场 | 只追加原生增强，不重新设计 |
| `beautify-pptx` | 页数、页序、每页措辞都必须 1:1 保留的已有 PPTX | 抽取源事实后走 SVG 流水线重新生成 native deck | 只改布局和层级，不做原地编辑 |

---

## 路线判定速查表

先用这张表判定路线，再讨论实现细节。大多数失败执行不是命令错了，而是一开始就走错了路线。

| 请求形态 | 路线 | 边界 |
|---|---|---|
| 只有主题，没有源文件或足够源文本 | 先走 `topic-research`，再进入主流水线 | 网络 / 来源收集是前置步骤 |
| 有源文件或对话文本，deck 结构可以重想 | 主 SVG 流水线 | Strategist 可以拆分、合并、删除、重排和重设计 |
| PPTX 作为源材料，用户允许重构故事和页结构 | `ppt_to_md` + `pptx_intake`，再走主 SVG 流水线 | PPTX 身份和几何是事实与候选，不是复刻约束 |
| 原生 PPTX 模板 + 新材料 / 新主题 | `template-fill-pptx` | 克隆并填充原生页面；不生成 SVG |
| 现有 PPTX，页数 / 页序 / 措辞 1:1 保留，只改善排版 | `beautify-pptx` | 通过 SVG 重新生成；内容和分页锁定 |
| 已完成 PPTX，保持内容 / 布局稳定，只加讲稿、音频、计时、转场 | `native-enhance-pptx` | 直接 OOXML patch；不重新设计 |
| 用户想从 PPTX 或设计参考构建可复用模板包 | `create-template` 或 `create-brand` | 输出后续能触发 Step 3 的目录 |
| 用户提供明确的 `templates/.../<id>/` 目录且声明 `kind: brand/layout/deck` | 主 SVG 流水线 Step 3 | 应用模板片段所有权和融合规则 |
| 用户要求调整对象级动画顺序 / 效果 / 计时 | `customize-animations` | 通过 `animations.json` 控制可选导出策略 |
| 用户要求预览、选择、注解或重导出浏览器编辑 | `live-preview` | 浏览器工作流；注解只在规定交接点应用 |

“优化这份 PPT”这类含糊请求归约为一个判定点：是否保留原始页数、页序和逐页措辞。保留就是 `beautify-pptx`；允许重构就是主流水线。

---

## 技术流程

**核心流程：AI 生成 SVG → 后处理转换为 DrawingML（PPTX）。**

整个流程分为三个阶段：

**第一阶段：内容理解与设计规划**
源文档（PDF/DOCX/XLSX/PPTX/URL/Markdown/主题文本）会被转换成 Strategist 所需的内容事实与分析事实。Strategist 角色分析材料、读取相关 `analysis/` artifact、规划页面结构，并确认视觉风格，最终输出完整设计规格。

**第二阶段：AI 视觉生成**
Executor 角色逐页生成演示文稿的视觉内容，输出为 SVG 文件。这个阶段的产物是**设计稿**，而非成品。

**第三阶段：工程化转换**
后处理脚本将 SVG 转换为 DrawingML，每一个形状都变成真正的 PowerPoint 原生对象——可点击、可编辑、可改色，而不是嵌入的图片。

---

## 产物流

维护这套系统时，把文件夹理解成数据流会比“这些目录刚好存在”更清楚：

```text
sources/<stem>.md ──────────────┐
analysis/source_profile.json ───┼─> Strategist -> design_spec.md + spec_lock.md
analysis/image_analysis.csv ────┘

spec_lock.md + images/ + icons/ + templates/
    └─> Executor -> svg_output/
              ├─> svg_quality_checker.py
              ├─> finalize_svg.py -> svg_final/
              └─> svg_to_pptx.py -> exports/<name>_<ts>.pptx
                                      backup/<ts>/svg_output/

直接 OOXML 路由：
analysis/<stem>.slide_library.json + 源 PPTX + fill_plan.json
    └─> template_fill_pptx.py -> exports/*.pptx
源 PPTX 项目归档副本 + 增强计划 + 讲稿/音频/计时资产
    └─> native_enhance_pptx.py -> exports/*.pptx
```

关键切分是：`svg_output/` 是作者状态，`svg_final/`、`exports/` 和 `backup/` 是派生的交付或归档状态。模糊这条线，会让校验、重导出和人工修复都更难推理。

---

## 为什么是 SVG？

SVG 是这套流程的核心枢纽。这个选择是通过逐一排除其他方案得出的。

**直接生成 DrawingML** 看起来最直接——跳过中间格式，AI 直接输出 PowerPoint 的底层 XML。但 DrawingML 极其繁琐，一个简单的圆角矩形就需要数十行嵌套 XML，AI 的训练数据中远少于 SVG，生成质量不稳定，调试几乎无法肉眼完成。

**HTML/CSS** 是 AI 最熟悉的格式之一，但 HTML 和 PowerPoint 有根本不同的世界观。HTML 描述的是**文档**——标题、段落、列表，元素的位置由内容流动决定。PowerPoint 描述的是**画布**——每个元素都是独立的、绝对定位的对象，没有流，没有上下文关系。这不只是排版计算的问题，而是两种完全不同的内容组织方式之间的鸿沟。就算解决了浏览器排版引擎的问题（Chromium 用数百万行代码做这件事），HTML 里的一个 `<table>` 也没法自然地变成 PPT 里的几个独立形状。

**WMF/EMF**（Windows 图元文件）是微软自家的原生矢量图形格式，与 DrawingML 有直接的血缘关系——理论上转换损耗最小。但 AI 对它几乎没有训练数据，这条路死在起点。值得注意的是：连微软自家的格式在这里都输给了 SVG。

**SVG 作为嵌入图片** 是最简单的路线——把整张幻灯片渲染成图片塞进 PPT。但这样完全丧失可编辑性，形状变成像素，文字无法选中，颜色无法修改，和截图没有本质区别。

SVG 胜出，因为它与 DrawingML 拥有相同的世界观：两者都是绝对坐标的二维矢量图形格式，共享同一套概念体系：

| SVG | DrawingML |
|---|---|
| `<path d="...">` | `<a:custGeom>` |
| `<rect rx="...">` | `<a:prstGeom prst="roundRect">` |
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse">` |
| `transform="translate/scale/rotate"` | `<a:xfrm>` |
| `linearGradient` / `radialGradient` | `<a:gradFill>` |
| `fill-opacity` / `stroke-opacity` | `<a:alpha>` |

转换不是格式错配，而是两种方言之间的精确翻译。

SVG 也是唯一同时满足流程中所有角色需要的格式：**AI 能可靠地生成它，人能在任意浏览器里直接预览和调试，脚本能精确地转换它**——在生成任何 DrawingML 之前，设计稿就已经完全透明可见。

---

## 源内容转换

源文档（PDF / DOCX / EPUB / XLSX / PPTX / 网页）会在 Strategist 开始前完成归一化，但当前架构已经不是“全部转成 Markdown 后其他信息都不重要”的单通道模型。现在有两条事实通道，各自拥有明确职责：

| 通道 | 产物 | 所有者 | 用途 |
|---|---|---|---|
| 内容契约 | `sources/<stem>.md` | `source_to_md/*` 转换器 | 文本、表格、图表数值、引用和源材料叙事 |
| 结构化分析 | `analysis/*.json` / `analysis/*.csv` | intake 与分析工具 | PPTX 身份信息、页面几何、原生表格/图表、图片尺寸/色彩/主体 |

对 PPTX 源文件，`project_manager.py import-sources` 会同时运行 `ppt_to_md.py` 和 `pptx_intake.py`。Markdown 仍然是主生成流水线的内容源；intake bundle 会写出 `<stem>.identity.json`、`<stem>.slide_library.json`，并把紧凑的多 deck 索引合并到 `analysis/source_profile.json`。Strategist 默认读取这个紧凑索引来获取源事实；只有特定工作流需要原始细节时，才打开单个 deck 的原始 artifact。这个边界很重要：主流水线可以重构页数和叙事，而 `template-fill` 与 `beautify` 会把同一批 intake 事实中的一部分提升为更强约束。

转换器生成的图片资产也会被归一化。伴随的 `<stem>_files/` 目录会导入项目级 `images/` 池，`image_manifest.json` 按文件名合并；当导入后目录名发生变化时，Markdown 中的资源引用会被重写。Office 矢量图（`.emf` / `.wmf`）是一等运行时资产：intake 阶段不栅格化它们，`finalize_svg.py` 为 native 路径保留外部引用，`svg_to_pptx.py` 以 Office 矢量媒体嵌入，避免 CJK 字体替换和矢量细节损失。

两个转换器设计选择仍然成立：

**Native-Python 优先，外部二进制兜底。** 常见格式由纯 Python wheel 处理，pandoc 仅在长尾小众格式时才被调用。让每个用户都去装一份可能没有权限装的系统级二进制是一种可用性税，而大多数输入是 docx / pdf / html / pptx，这种税不值得。

**TLS 指纹模拟应对高安全站点。** 网页抓取默认走 Python 版 `web_to_md.py`，并在可用时依赖 `curl_cffi` 做类 Chrome TLS 指纹模拟。微信公众号和不少 CDN 会直接屏蔽 Python 默认握手；把这件事留在 Python 转换路径里，避免让 Node 抓取器成为主架构。

---

## 项目结构与生命周期

`project_manager.py init` 创建的是一个自包含工作区，而不只是输出目录：

| 目录 | 职责 |
|---|---|
| `sources/` | 原件归档、归一化 Markdown、转换器伴随文件 |
| `analysis/` | 机器抽取事实：PPTX intake bundle 与按需重算的图片分析 |
| `images/` | 单一运行时图片池：用户图、抽取图、公式图、网络图、AI 图、切片图、EMF/WMF |
| `icons/` | 由 `icon_sync.py` 复制的项目级图标集；导出时可回退到全局库 |
| `templates/` | 复制进项目的模板 spec / SVG reference / 非图片模板资产 |
| `svg_output/` | 唯一手写 SVG 源目录 |
| `svg_final/` | 派生出的自包含 SVG，服务 IDE / 浏览器 / 预览快照 |
| `live_preview/` | 预览服务状态、直接编辑历史和注解日志 |
| `notes/` | `total.md` 与拆分后的逐页讲稿 |
| `exports/` | 带时间戳的 native PPTX 交付物 |
| `backup/<timestamp>/` | 默认导出时写入的冻结 `svg_output/` 快照 |

CLI 仍支持三种导入模式：`--move`、`--copy`，以及“仓库内文件 move、仓库外文件 copy”的自动默认。`SKILL.md` 中的生产工作流会刻意收紧这一点：agent 必须调用 `import-sources ... --move`，让所有源文件和中间产物进入 `sources/`，保持工作根目录干净。脚本级默认服务临时 CLI 使用的安全性；工作流级契约更严格，是为了让 AI 执行具备可复现和可审计性。

---

## 架构不变量

这些不变量强于普通实现偏好。如果某个改动破坏了其中一条，它很可能是在改变架构，而不是做重构。

| 不变量 | 实际后果 |
|---|---|
| `sources/<stem>.md` 是主流水线内容契约 | 主 SVG 路线中的文本、表格和图表数值来自 Markdown |
| `analysis/` 存机器事实，不存设计契约 | `source_profile.json` 和 intake artifact 辅助 Strategist；除非工作流明确规定，否则不锁定页数 / 页序 |
| `design_spec.md` 解释设计；`spec_lock.md` 执行设计 | Executor 从 `spec_lock.md` 取锁定值，而不是从叙述记忆里取 |
| 每页生成前重读 `spec_lock.md` | 长 deck 中的颜色、字体、图标、图片、节奏、布局和图表选择保持稳定 |
| `svg_output/` 是唯一手写 SVG 目录 | 质量检查、手工编辑、重导出和 `update_spec.py` 都面向作者源 |
| `svg_final/` 是派生产物 | 它可以从 `svg_output/` 重建，不应成为 native 导出的事实源 |
| native PPTX 默认读取 `svg_output/` | 转换器要在 finalize 重写前保留图标、`preserveAspectRatio`、圆角矩形和原生图片裁剪语义 |
| 直接 OOXML 路由不进入 SVG 流水线 | 保留型工作流直接 patch 原生 PPTX parts |
| 图片事实来自重算元数据 | `analysis/image_analysis.csv` 从实时 `images/` 目录重算；agent 不直接看图片像素 |
| 原生 PPTX 模板不是 Step 3 模板 | Step 3 只消费可复用模板目录 |

---

## Canvas 格式系统

PPT Master 不只服务 PPT——同一套 SVG → DrawingML 流水线还能产出方形海报、9:16 故事、A4 印刷品。各格式特定的约定（比例、安全区、品牌区等）住在 [`references/canvas-formats.md`](../../skills/ppt-master/references/canvas-formats.md)。

值得标注的架构选择：**viewBox 是像素，不是绝对单位。** 像素空间让 AI Executor 思考布局没有歧义（`x="100"` 就是左缘 +100px），人类在浏览器里检查也直接。到 EMU 的换算只在导出时发生一次——选像素意味着流水线的其余环节（Strategist、Executor、质量检查、后处理）永远不需要在 EMU 思维下工作，那对 AI 生成和人类调试都是敌对的。

---

## 模板系统与可选路径

模板是**可选项，不是默认**。Strategist 默认走自由设计——AI 完全凭源内容创造视觉系统。模板路径只在用户明确提供目录路径时启用。

**为什么默认自由设计。** 模板是地板，但很容易变成天花板：它会把整个 deck 锁进模板自有的视觉惯用语，无视内容本身想要怎样被呈现。自由设计的布局从源内容的结构推导而来，而不是从一套固定语法套上去——视觉节奏跟着内容走，而不是跟内容打架。约束模式在窄场景里确实更好（品牌锁定的 deck、强类型场景如学术答辩或政府报告），所以它一直在；但 AI 不主动去抓，是用户去抓。

**机械触发，不做语义匹配。** 像 `academic_defense` 这样的裸名字、品牌提及，或“麦肯锡风格”这类风格短语，即使库里存在相似目录，也不会触发 Step 3。Step 3 只消费一个能解析为目录的路径，并且该目录的 `design_spec.md` 必须声明 `kind: brand`、`kind: layout` 或 `kind: deck`。发现性交给模板索引和显式问答（“有哪些模板可以用？”），不交给运行时 fuzzy matching。

三类模板拥有不同的设计契约片段：

| Kind | 拥有的片段 | 典型内容 | 对 Strategist 的影响 |
|---|---|---|---|
| `brand` | 身份片段 | 配色、字体、logo、语气、图标风格 | 锁定身份；结构保持自由 |
| `layout` | 结构片段 | 画布、页面结构、页面类型、SVG roster | 锁定结构；身份仍在八项确认里确定 |
| `deck` | 身份 + 结构 + 模板总览 | 完整复刻型包 | 锁定完整模板语法，只剩内容相关选择 |

当用户提供多个路径时，融合是**片段级**而不是字段级：brand 覆盖身份片段，layout 覆盖结构片段，deck 提供中间的 template overview 片段。同类冲突会被显式列为冲突，而不是按输入顺序默默决定。这样融合后的 spec 能明确说明每个片段来自哪里，便于审计和复现。

**原生 PPTX 模板不属于 Step 3。** `.pptx` 可以作为源材料进入流水线，PPTX intake 也能抽取其身份和几何信息。但“给一个原生 PPTX 模板并生成新 PPTX”的请求会进入 `template-fill`，因为用户期望的是克隆 PowerPoint 页面壳并替换文本 / 表格 / 图表。SVG 路线只能消费可复用模板包；如果要把某个 PPTX 的设计语言用于 SVG 路线，必须先通过 `create-template` 生成模板目录，再把该目录路径提供给 Step 3。

**布局是 opt-in，图表和图标不是。** 这种不对称不是矛盾——*布局*正是锁定视觉惯用语的那一层（地板/天花板问题），而图表和图标是不会施加 deck 级风格约束的复用原语。同一个 `templates/` 目录，但在视觉契约里扮演的角色不同。

---

## 角色系统：单一流水线中的专业模式

PPT Master 用的是**单主代理内的角色切换**，不是并行子代理。Strategist、Image_Generator、Executor 以及各独立工作流模式，本质上都是按需加载的指令作用域；它们不是带着各自过期 deck 状态的独立 agent。这个选择有三条互相支撑的理由：

**为什么是单代理而非并行子代理。** 页面设计依赖完整的上游上下文——Strategist 的色彩选择、图片资源是否成功获取（还是失败被替代）、之前几页的视觉节奏。子代理拿到的只能是这个上下文的过期局部快照，产出的 deck 视觉会逐页漂。同一逻辑也禁止分批生成（比如一次 5 页）：分批加速上下文压缩，deck 的视觉一致性下降速度比节省的速度更快——不划算。

**为什么是角色专属 reference 而不是一个超大 prompt。** Strategist 跑的是「跟用户协商」模式（开放式、对话式、可以回退），Executor 跑的是「产出严格 XML」模式（不准即兴、不准漏属性）。把两者塞进同一个 prompt，强迫模型在同一个 turn 里持守相互矛盾的纪律——所有混合模式的 prompt 工程病灶都会出现。按角色拆开，每个角色只加载它需要的、扔掉其他。

**Eight Confirmations 是唯一的阻塞 gate。** Strategist 阶段以八项打包确认（画布 / 页数 / 受众 / 风格 / 配色 / 图标 / 排版 / 图像）作为核心阻塞决策点。当前流程默认通过 Confirm UI 分两层呈现：Tier 1 确认锚点（画布、受众、改写幅度、交付目的、mode、visual style）；Tier 2 基于用户已确认的锚点重新推导，再确认实现层选择（页数、调色板、字体、图标、公式策略、图片来源、AI 图片路径、生成模式、refine-spec）。最终的 `confirm_ui/result.json` 是权威输入——用户改过的字段必须进入 `design_spec.md` 和 `spec_lock.md`，不能回退到 AI 的原始推荐。

**图片分析走重算元数据，不读像素。** 当项目里存在图片时，Strategist 和 Executor 使用 `analyze_images.py` 的输出（`analysis/image_analysis.csv`），而不是直接打开图片文件。这个 CSV 是基于当前 `images/` 目录重算出来的视图，不是持久缓存。每次做图片敏感决策前重跑分析，就是它的防陈旧策略：用户图、抽取图、网络图、AI 图、公式图和切片图最终都会汇入同一张可度量事实表。

**逐页 spec_lock 重读** 是长 deck 的抗漂移机制——完整理由见下面的 § 设计规范的传播。

---

## 执行纪律

流水线由 [`SKILL.md` § 全局执行纪律](../../skills/ppt-master/SKILL.md) 中的 10 条规则强制——那份文件是权威，规则住在那里。它们看起来很官僚，但存在的理由是：LLM 默认行为是“让我在这一 turn 里把整个问题搞定”，而这恰好是串行流水线最不该有的形状——串行流水线要求每一步的输出都是有界、过 checkpoint、被下一步消费的。这套规则共同关闭了实际反复出现的失败模式：乱序执行、AI 代为做用户设计决策、跨阶段打包、前置条件未满足、投机预先准备、子代理上下文丢失、分批漂移、长 deck 色彩字体漂移、脚本批量生成 SVG 漂移，以及路由歧义。

其中两条新边界尤其关键。第一，Executor 页面 SVG 必须由当前主代理逐页手写；禁止写 Python / Node / shell 生成器批量吐 SVG，因为这种输出会丢失跨页判断和视觉连续性。第二，路由是确定性的：原生 PPTX 模板、beautify、native enhancement、自定义动画、live preview 等触发条件已经在仓库里定义清楚时，不再额外抛给用户一个开放式路线选择题。

角色切换协议（切换模式前必须 `read_file references/<role>.md`）有两个互相支撑的作用：把新鲜的角色指令载入上下文，覆盖前一模式的漂移；对话 transcript 中的可见标记构成审计轨迹，让用户能看到 agent 何时切换了模式——回看一个具体决策为什么这样做时，这条线索很关键。

---

## 设计规范的传播：spec_lock.md 作为执行契约

Strategist 阶段产出两份看起来冗余但服务不同对象的产物：

- `design_spec.md` —— 人类可读叙述；设计的「为什么」（目标受众、风格目标、配色理由、页面大纲）
- `spec_lock.md` —— 机器可读执行契约；Executor 必须**字面照搬**的「是什么」（HEX 颜色、确切的 font family 字符串、图标库选择、带状态的图片资源列表）

为什么两份都要？没有 `spec_lock.md` 的话，Executor 在长 deck 里会逐页重读 `design_spec.md`，LLM 上下文压缩漂移会逐渐扭曲色值和字体。`spec_lock.md` 是**抗漂移机制**——SKILL.md 强制要求生成每一页前 `read_file <project>/spec_lock.md`，让数值在 20+ 页里保持字面一致。

这份 lock 同时也是逐页路由表。除了全局配色和字体，它还承载 `page_rhythm`（`anchor` / `dense` / `breathing`）、`page_layouts`（某页是否继承某个 layout 模板 SVG）、`page_charts`（某页应适配哪个图表模板）、带放置/裁剪契约的图片行，以及决定加载哪些执行规则文件的 `mode` / `visual_style`。空值本身也是信号：没有模板、没有图表、没有图片，很多时候是设计选择，而不是漏填。

`update_spec.py` 把生成后的修改用两个协调步骤传播：把新值写入 `spec_lock.md`，然后字面替换到每一份 `svg_output/*.svg`。工具的范围**故意收得很窄**——只支持 `colors.*`（HEX 值，大小写不敏感替换）和 `typography.font_family`（属性级）。其他字段（字号、图标、图片、画布）**有意不支持**——它们的替换需要属性级或语义级理解，风险/收益不值得做批量传播。这些情况手动改 `spec_lock.md` 然后重做受影响的页面。

工具拒绝做备份：依赖 git 回滚。加备份机制只是重复 git 的工作，还会留下过时快照。

---

## 图片获取与嵌入

这一阶段有多项架构层面的决策：

**provider 专属 config key，不用通用 `IMAGE_API_KEY`。** 每个 backend 用自己的 `OPENAI_API_KEY` / `MINIMAX_API_KEY` 等等，当前 backend 由显式的 `IMAGE_BACKEND=<name>` 选定。统一的 `IMAGE_API_KEY` 字段第一眼看着干净，但当用户同时配了多个 provider 又不确定哪个在生效时会造成静默混乱——这种 fault 通常只表现为「图像生成结果怪怪的」，找不到清晰失败点。强制 per-provider key 让「我现在用的是哪个 backend」从推理变成可读配置。

**默认宽松 license 过滤，配以严格模式应对没法放致谢的版面。** 网络图片搜索默认允许 CC BY / CC BY-SA 加内联致谢——大部分幻灯片都有视觉空间放一个致谢元素。`--strict-no-attribution` 是给全屏 hero image 和紧凑构图的逃生口，那些场景没法放致谢又不打破设计。NC（CC BY-NC*）和 ND（CC BY-ND*）自动拒绝，因为 PPT Master 的典型产物会用于商用或修改场景；宽松默认 + 这个底线正好对应用户实际想要的 fail-mode。

**Manifest-first 获取。** 流水线内的 AI 图片生成永远先写 `images/image_prompts.json`，并渲染旁路 `image_prompts.md`，哪怕只有一张图。`image_gen.py "prompt"` 这种位置参数形式只保留给一次性调试，因为它没有 manifest / sidecar 审计轨迹。网络图片获取也类似：多行 web 资源写入 `images/image_queries.json` 批量执行，并用 `image_sources.json` 追踪来源和致谢信息。

**相关小插画用一张统一 sheet。** 当 deck 需要三个或更多同风格小插画时，资源计划使用一个 AI illustration sheet 行，再用若干 `slice` 行派生元素，而不是分别生成多张小图。`slice_images.py` 把 sheet 切成具名透明元素，这些派生文件进入 `images/`，随后重跑 `analyze_images.py`，让 Executor 看到真实尺寸。这既是成本规则，也是风格一致性规则：一张 sheet 会强迫这些小元素来自同一种视觉手法。

**Executor 前必须进入终态。** 需要获取的资源行必须落到 `Generated`、`Sourced` 或 `Needs-Manual`；`Pending` 和 `Failed` 不能漏进 Executor。`Needs-Manual` 可以作为已知占位 / 依赖继续进入 SVG 生成，但 Step 7 会在最终导出前重新检查必需文件是否已经存在。

**开发期外部引用，交付期分叉成两套嵌入策略。** 在 `svg_output/` 里编辑时，图片是外部文件引用——快速迭代、单点替换。两份交付产物随后分叉：`svg_final/` 走 Base64 内联（产出一组自包含 SVG，IDE 预览、浏览器、preview pptx 都能开而不丢位图依赖）；native pptx 反过来把位图复制进 PPTX 的 media 文件夹，用 `<a:srcRect>` 表达裁剪。分叉的理由：在 DrawingML 里塞 Base64 能跑但文件膨胀 3-4 倍；文件引用的位图是 PowerPoint 原生表达方式，配 `<a:srcRect>` 的裁剪也是 DrawingML 的规范写法——任一方向用错工具都要付出可编辑性或文件大小的代价。

**AI 图片三维系统：Strategist 阶段就锁定。** 当 deck 包含 AI 生成图片时，Strategist 在前置阶段一次性确定三个正交维度——`rendering`（视觉风格家族：vector-illustration / editorial / 3d-isometric / sketch-notes / ……）、`palette`（deck 的 HEX 在图里**怎么用**：比例 + 角色 + 气质）、`type`（每张图的内部构图：background / hero / framework / comparison / ……）。前两个是 deck 级、写进 `spec_lock.md`；Image_Generator 此后每张图的 prompt 都从同一份锁定的 rendering + palette 加上该图的 type 组装出来，而不是逐图重决风格。没有这层锁定，每张图都会自己风格漂移，整套 deck 读起来就是一摞互不相关的插画。这是 `spec_lock` 字体/色彩抗漂移机制在像素上游的对偶——同一思路，往前推一层。Strategist 在八项确认阶段会向用户呈现 **≥3 个 `rendering × palette` 候选**，绝不静默地自动锁定单一组合，因为这是一个会牵动全 deck 视觉的选择，唯一权威只有用户的品味。

---

## 图文版式：Primary 主结构 + Modifier 修饰层

「图片**怎么放上幻灯片**」的词表（完整词汇在 [`references/image-layout-patterns.md`](../../skills/ppt-master/references/image-layout-patterns.md)）把 72 条编号技法拆成两层、自由组合：

- **Primary 主结构**（容器布局 / 图作画布 + 原生覆盖 / 多图组合）—— 页面的骨架。一页可一个也可多个；跨 Primary 的组合，如「侧边对比 + 图作画布的注解卡」，是合规的。
- **Modifier 修饰层**（非矩形裁剪 / 遮罩与叠加 / 纹理 / 特殊技法）—— 装饰层。一页可叠任意多个，附着在 Primary 之上。

**为什么显式鼓励复合，而不是「一页一个 primary」。** 这份词表对抗的 AI 失败模式不是「叠太多」，而是「用得太少」——把每页图片默认堆成裸的 `#2 左三分` 或 `#48 侧边对比`，Modifier 层完全不动，产出视觉扁平的「AI 默认感」版式。早先的规则「一页一个 primary，modifier 可叠」听起来有原则，实际上加剧了 Modifier 层的弃用——AI 把它读作「可以不叠」的许可。现在的措辞反过来：组合是常态，单 Primary + 无 Modifier 才需要解释。

**为什么物理拆分两层，而不是只打标签。** 词表被重排成「Primary 全部在前，Modifier 全部在后」——Strategist 或 Executor 读一次目录，就能从结构上内化「两层」心智模型。编号是稳定 id（`#38` 永远是「图作画布 + 注解卡」，不论它在文件里的物理位置），所以 `spec_lock.md`、`design_spec.md §VIII`、历史 executor 输出、过往示例里所有 `#<id>` 引用照样解析。

**为什么组合走 Strategist 资源列表，不只交给 Executor 临场发挥。** `§VIII 图片资源列表` 的 `Layout pattern` 列接受 `#<id> + #<id> ...` 表达式——Primary id 加可选 Modifier id——所以组合在 SVG 生成**之前**就被声明、被 `svg_quality_checker` 审计、并能在 session 重入后存活。把组合责任只压在 Executor 身上，长 deck 上下文压缩时就会丢；把它编码进 spec_lock 旁的资源列表，组合就成为设计契约的一部分。

**为什么真正的硬约束留在上游。** 跨切的技术硬约束（`<clipPath>` 只能用在 `<image>` 上、用 `fill-opacity` 而非 `rgba()`、禁 `<mask>`、alpha 效果的路由表）独家住在 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md)。版式词表只用一行指针指向它们，不复述——这样某条约束放开时（比如某个 DrawingML 特性变得可靠），只有一个文件要改，词表里也不会留下一份过期副本继续暗中强制旧规则。

---

## SVG 约束：禁用特性与条件允许

PowerPoint 的 DrawingML 是 SVG 表达力的严格子集。Executor 在一份经验生长起来的黑名单（mask、style/class、`@font-face`、foreignObject、symbol+use、textPath、animate*、script/iframe ……）里运行，外加对 `marker-start`/`marker-end` 和仅 `<image>` 上的 `clip-path` 的窄条件允许。权威清单和每条特性的具体约束——包括 `<mask>` 的替代效果路由表（渐变叠加、clipPath、filter shadow、源图烘焙）——住在 [`references/shared-standards.md`](../../skills/ppt-master/references/shared-standards.md)。

值得在架构层标记的理由：

- **为什么是黑名单，不是白名单。** SVG 是个宽规范；穷举允许特性会随着 Executor 不断发现新的有用构造而要持续维护。黑名单只圈住语义上没有 DrawingML 表达的窄集合，其余隐式可用。
- **为什么是经验性，不是从规范推导。** 这份清单从真实的 PPT 导出失败长出来，不是读 OOXML 规范读出来的。有几个特性（如 `<mask>`）理论上能在 DrawingML 表达，但跨 PowerPoint 版本不可靠；黑名单反映的是实际能交付的子集。
- **XML 良构性陷阱。** 两个独立于 DrawingML 的跨切陷阱：排版字符必须用裸 Unicode（`—`、`→`、`©`、NBSP），HTML 命名实体（`&mdash;`）在 SVG 里是非法 XML；XML 保留字符（`& < >`）必须实体转义，否则 `R&D` 直接终止导出。这两个坑出现频率高到值得在架构层 flag 一下。
- **黑名单在后处理之前执行。** `svg_quality_checker.py` 在 `svg_output/` 上执行；后处理会重写 SVG，会掩盖源级别违规。修复永远是 Executor 重新写——有意没有 auto-fix 模式（见 § 质量门）。

---

## 质量门

**为什么需要这道检查器。** LLM 生成的 SVG 不是确定性的——禁用特性会在长 deck 中悄悄混入，只在 `svg_to_pptx` 中途崩或 PowerPoint 静默丢元素时才暴露。检查器把「PowerPoint 在第 14 页导出失败」转化为「Executor 在第 14 页用了 `<style>`，重新生成它」，诊断速度提升一个数量级——这正是让长 deck 在经济上可迭代的关键。

**为什么放在后处理之前，而不是之后。** 后处理会重写 SVG（图标嵌入、图片内联），会掩盖源级别违规。直接读 `svg_output/` 抓的是 Executor 的实际输出，先于任何可能掩盖 bug 的清理动作。

**严重性模型：error 阻塞、warning 不阻塞，且有意没有 auto-fix。** error 要求 Executor 在上下文里重新写出错的页面——一个被禁的 `<style>` 元素不是机械 patch，因为 Executor 用它是有原因的，替代方案（比如改成内联属性）需要带着同样的设计意图重新落地。Auto-fix 会静默丢失这份意图，交付一个更难看的页面。

**为什么图表坐标验证挂在同一道 gate。** 图表页面有几何正确性需求（柱高、饼图扇角、坐标轴刻度位置），这些不是结构问题，SVG 合法性规则也抓不到。最自然的捕捉位置就是已经要求 AI 回看自己输出的那道 gate——把「看一眼你刚生成的东西然后修」的认知上下文打包到一个阶段，比把结构和几何审查分到两轮 review 更高效。

---

## 后处理流水线

> 工程化转换阶段中每一份产物和每一个模块为何存在，删除它会破坏哪些工作流。在考虑简化 `svg_final/` / `finalize_svg.py` / `svg_to_pptx.py` 之前，先读这一节。

### 五份产物，五种工作流

后处理阶段涉及五份产物。每一份都服务于一种流水线中无法替代的工作流。

| 产物 | 服务的工作流 | 为何无可替代 |
| --- | --- | --- |
| `svg_output/` | 唯一源、手工编辑入口、`update_spec.py`、`svg_quality_checker.py` | 流水线中唯一**手写**而非派生的目录 |
| `svg_final/` | IDE 内即时预览（VSCode/Cursor 直接打开 `.svg`）、浏览器单页预览 | `.pptx` 在 IDE 里打不开；`svg_output/` 因图标 / 图片是外部引用，IDE 中渲染不完整 |
| `exports/<name>_<ts>.pptx`（native） | 主交付物——PowerPoint 中以 DrawingML 形状形态可编辑 | 唯一一份用户可在 PowerPoint 中原生改尺寸 / 改色 / 改样式的产物 |
| `exports/<name>_<ts>_svg.pptx`（preview，需 `--svg-snapshot` 显式开启） | 跨平台单文件分发、整体多页浏览、邮件附件 | 自包含、多页、PowerPoint / Keynote / WPS / LibreOffice 都能直接打开；`svg_final/` 是文件夹，分发不便。默认关闭——live preview 已经覆盖 dev / 诊断场景的 SVG 视觉参考需求 |
| `backup/<ts>/svg_output/`（默认流程下始终生成） | 不重跑 LLM 的前提下从冻结 SVG 源重建 pptx、长期存档 | 项目下游被改动后，Executor 原始 SVG 唯一的留存副本 |

### `svg_finalize/` 包有**两种**消费者

这是读代码时容易忽略的关键事实。同一组 `skills/ppt-master/scripts/svg_finalize/` 下的模块，在两个地方被使用，服务两份不同的产物。

**写盘消费者** —— `finalize_svg.py` 每次运行都把 `svg_output/` → `svg_final/` 写到磁盘一次。`svg_final/` 随后供 IDE 预览和 preview pptx 使用。

**内存消费者** —— native pptx 直接读 `svg_output/`（不经磁盘中转），但 DrawingML 无法内联处理两种 SVG 特性，所以转换器在内存中调用 `svg_finalize` 模块：

| 内存调用点 | 复用的模块 | native pptx 为何需要 |
| --- | --- | --- |
| `svg_to_pptx/use_expander.py` | `svg_finalize.embed_icons` | DrawingML 不识别 `<use data-icon="...">`；不展开图标会静默丢失 |
| `svg_to_pptx/tspan_flattener.py` | `svg_finalize.flatten_tspan` | DrawingML 文本块无法在段落中跳位置；`dy` 堆叠的多行 `<tspan>` 会塌成一行，`x` 锚定的 tspan 会跑到错误的列 |

### 各模块消费者一览

| 模块 | 写盘消费者 | 内存消费者 | 删除影响 |
| --- | --- | --- | --- |
| `embed_icons.py` | `finalize_svg` 的 `embed-icons` 步骤 | `svg_to_pptx/use_expander.py` | native pptx 丢失全部图标 + `svg_final/` 不再自包含 |
| `flatten_tspan.py` | `finalize_svg` 的 `flatten-text` 步骤 | `svg_to_pptx/tspan_flattener.py` | **native pptx 中 `dy` 堆叠的多行文本塌成一行** |
| `align_embed_images.py` | `finalize_svg` 的 `align-images` 步骤 | — | `svg_final/` 失去图片嵌入 → IDE 预览 / preview pptx 都没图 |
| `crop_images.py` / `embed_images.py` / `fix_image_aspect.py` | 被 `align_embed_images.py` import | — | `align_embed_images` `ImportError`，整条链路 broken |
| `svg_rect_to_path.py` | `finalize_svg` 的 `fix-rounded` 步骤 | — | 只影响 PowerPoint 内手动「Convert to Shape」时圆角丢失；浏览器 / IDE / PowerPoint 自带的 SVG 渲染器都正常 |

---

## 直接 OOXML 路由

不是所有 PPTX 相关请求都应该重新生成页面。PPT Master 现在为“原生 deck 本身就是编辑对象”的场景提供直接 OOXML 路由。

`template_fill_pptx.py` 是 `scripts/template_fill_pptx/` 包的薄 CLI 入口。analyzer 抽取带文本槽位、表格、图表和几何信息的 slide library；fill plan 选择源页面并确认替换内容；applier 克隆幻灯片并直接 patch XML parts。这条路线故意绕开 SVG：用户提供 PowerPoint 模板时，通常期望原生母版、占位符、表格和图表继续保持 PowerPoint-native。

`native_enhance_pptx.py` 是已完成 deck 原生增强的稳定入口。它委托 native narration / timing 实现，在项目归档副本上直接 patch PPTX package：讲稿、页面转场、录制旁白媒体、页面计时和相关元数据。它的契约是保留：已有内容、布局和格式不重新生成。

这些直接路线会和主流水线共享部分分析原语，尤其是 PPTX intake，但不共享 SVG 作者阶段和后处理阶段。这个分离是有意的：SVG 生成是设计合成路径；直接 OOXML 编辑是保留路径。

---

## Native PPTX 转换器内部

**为什么是逐元素派发而不是整体翻译。** SVG 的层级模型干净地映射到 DrawingML 的 group / shape / picture 类型——不需要一个全局优化器去重新规划幻灯片。每种形状都有自己窄的翻译器，简单到能单独调试和单元测试。一张幻灯片的最终质量等于这些独立局部转换之和；这个性质在整体翻译下脆弱，在元素派发下稳健。

**为什么 Office 兼容模式默认开启。** 2019 之前的 PowerPoint 不能原生渲染 SVG。转换器为每页生成 PNG 兜底，与原生形状并存——新版 Office 仍显示可编辑形状，旧版回退到 PNG。默认开启的取舍是：用适度的文件大小代价换取「不会静默地把打不开的 deck 交给跑老版本的用户」；逃生口给那些明确知道自己在新栈上、想要更小文件的用户。

---

## 动画与转场模型

值得讲的设计选择是动画**锚点**，不是效果列表。

**为什么把入场动画锚在顶层 `<g>` group。** PowerPoint 的动画时序基于形状 ID——每个被动画的对象需要稳定的 shape ID。给单个原语做动画会产出每页 30+ 个分别飞入的原子（动感泛滥），只给整页做动画又损失视觉叙事。顶层 group 是自然粒度：Executor 本来就被强制要求用 `<g id="...">` 标记逻辑内容块，而这些块正是观众读作「一个东西到达」的单位——动画对齐了已有的逻辑结构，而不是另立门户。

**为什么页面装饰自动跳过。** 名为 `background` / `header` / `footer` / `decoration` / `watermark` / `page_number` 的 group 代表静态页面框架，不是内容；让它们飞入会让人出戏（页面本身在每次切换时具象化），几乎不会是用户想要的。按 id token 过滤原则上脆弱，实际上可靠——因为 token 词表很小，命名权又掌握在 Executor 手里。

**为什么对象级动画用 sidecar，而不是 SVG 属性。** SVG 继续作为静态视觉源。自定义 PPTX 动画属于导出策略，所以对象级覆盖放在可选的 `animations.json`，按 slide stem 和顶层 group id 关联。这样不会把 PowerPoint 专用元数据塞进 SVG，同时仍能在默认全局动画不够用时调整顺序、效果、延迟和时长。

**为什么录制旁白让自动推进时长跟着片段时长走。** 嵌入旁白意味着 deck 目标是视频导出——视频里没有演讲者去点击。把每页自动推进时长设为该页音频片段的实际时长，PowerPoint 能干净地导出为 MP4，无需人工配时。任何其他时长来源（估算朗读速度、固定每页时长）都会破坏音画同步。

**为什么录制旁白拒绝 on-click 对象动画。** PowerPoint 可以在真实排练时记录点击计时，但 PPT Master 不合成对象级点击事件。录制旁白路径只写页面级音频和页面自动推进计时，所以单击触发的对象入场会让导出依赖额外的 PowerPoint 人工排练。带旁白的 deck 必须使用无点击入场（`after-previous` 或 `with-previous`）。

---

## 维护边界：不要合并什么

下面这些“简化”都有明确代价。除非要有意识地重新设计周边架构，否则应把它们视作反向契约。

| 不要合并或新增 | 原因 |
|---|---|
| 不要把模板名或风格短语模糊匹配到库路径 | Step 3 必须确定性触发；选错模板比自由设计更难恢复 |
| 不要把原生 PPTX 模板当作 Step 3 模板 | 原生 PPTX 模板请求期待的是克隆 / 填充原生页面，不是 SVG 合成 |
| 不要把 `template-fill-pptx`、`beautify-pptx`、`native-enhance-pptx` 合成一个“PPTX 优化”路线 | 三者的保留契约不同：原生填充、1:1 重排、直接增强是三种操作 |
| 不要用脚本批量生成 Executor SVG 页面 | 跨页设计判断依赖主代理逐页连续创作 |
| 不要把 `image_analysis.csv` 当持久缓存 | `images/` 是实时工作目录；事实必须按需重算 |
| 不要让 `svg_final/` 成为 native PPTX 默认输入 | `svg_final/` 为自包含预览而重写，native 转换需要 `svg_output/` 的高保真语义 |
| 不要默认开启对象级入场动画 | 页面转场是默认；对象 build 是显式导出策略 |
| 不要把 visual review、旁白、图表校准或动画定制默认塞进每次运行 | 这些工作流触发范围窄，且有额外依赖 |
| 不要用文件复制替代 `finalize_svg.py` | finalize 会嵌入图标 / 图片、展开特殊文本并准备预览产物 |
| 不要在主流水线里把 `analysis/<stem>.slide_library.json` 当作第二份图表数值来源 | Markdown 拥有内容数值；除非直接 PPTX 工作流接管，否则 intake 图表 / 表格条目只是结构摘要 |

---

## Standalone Workflows（独立工作流）

独立工作流是路线定义，不是可有可无的装饰。只有当某个能力与主流水线契约不同，或触发频率太低、不值得默认加载时，才会独立成 `workflows/<name>.md`。

| 工作流 | 触发条件 | 契约 |
|---|---|---|
| `topic-research` | 用户只有主题、没有源材料 | 在 Step 1 前收集网络材料 |
| `template-fill-pptx` | 原生 PPTX 模板 + 新材料 / 新主题 | 直接克隆并填充原生页面；不进入 SVG 流水线 |
| `beautify-pptx` | 现有 PPTX，页数/页序/措辞必须 1:1 保留，只改善排版 | 锁定源身份与内容后，通过 SVG 流水线重新生成 |
| `create-template` | 构建可复用 layout/deck 模板包 | 输出后续 Step 3 可消费的目录 |
| `create-brand` | 提取或定义可复用品牌身份 | 输出 `templates/brands/<id>/` |
| `resume-execute` | Phase A 后新开聊天，用户要求继续某项目 | 不重跑 Strategist，直接进入 Phase B |
| `refine-spec` | 用户明确要求生成前先审阅 / 修改 spec | 写出完整 spec/lock 后停下，用户修改后再恢复 |
| `verify-charts` | 生成 deck 含数据图表 | 导出前校准图表几何 |
| `customize-animations` | 用户要求调对象级动画顺序 / 效果 / 计时 | 创建 / 校验 `animations.json` 并控制再导出策略 |
| `live-preview` | 用户要求预览、点击选择、应用注解或重导出浏览器编辑 | 启动 / 重入浏览器预览，并只在规定时机应用提交内容 |
| `visual-review` | 用户明确要求逐页视觉自检 | 在 Executor 与后处理之间做 rubric pass |
| `generate-audio` | 用户要求旁白 / 视频导出 | 生成旁白音频并走录制计时导出路径 |
| `native-enhance-pptx` | 已完成 PPTX 要保留内容/布局，同时追加原生增强 | 直接 OOXML patch 路线 |

保持这些文件独立，是依赖控制决策。主路径只加载当前需要的角色和 reference；旁白 backend、动画 sidecar、图表校准 rubric、模板导入契约等，只有触发命中时才进入上下文。这样默认 deck 生成路径保持紧凑，同时让低频能力也有确定实现，而不是临场发挥。
