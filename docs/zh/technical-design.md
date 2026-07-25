# 技术路线

[English](../technical-design.md) | [中文](./technical-design.md)

---

## 设计哲学 —— AI 驱动工作流，人掌握最终判断

PPT Master 交付的是一份**高质量、可继续编辑的 PowerPoint 草稿**，而不是封闭的最终成品。工作流先推理信息与论证，再设计页面，并按照明确的路线合同创作或保留 PowerPoint 原生对象。用户负责确认方向，并在 PowerPoint 中掌握最后一公里的判断。后续工作应当是对真实 deck 的精修，而不是从整页图片或浅层可编辑外壳重新搭建。

工作流提供演示文稿专用的推理、状态、合同与质量门；确定性工具负责转换、校验、打包和可重复文件操作。**最终质量上限仍由所选模型决定**，用户的审美与判断则负责评审和收尾。

### SVG 是项目的规范中间语言

PPT Master 不以“任意 SVG 都能转成 PPTX”为目标。`svg_output/` 使用的是**项目规范化 SVG 中间语言**：它借用 SVG 的 XML 语法和二维图形模型，但允许的元素、属性、单位、metadata、结构合同与 DrawingML 映射都由项目规范封闭定义。这里的方向是 **SVG 适应 PPT Master，而不是 PPT Master 追随整个 SVG 标准扩张**。

这套中间语言区分三种输入状态：

| 状态 | 定义 | 处理方式 |
|---|---|---|
| 规范创作输入 | 提示词、模板和示例应生成的唯一推荐表达 | 按注册映射校验和编译，不因表达别名产生 warning |
| 兼容输入 | 已明确登记、可确定且安全归一化的历史或人工写法 | Checker 给出非阻塞 warning；转换器确定性归一化后编译，不把别名反向扩散到提示词 |
| 非法或不支持输入 | 缺少映射、存在歧义、破坏结构合同，或可能生成非法 DrawingML / PPTX 的表达 | Checker 报 error 并阻断标准流程；转换器在自身预检或 package 校验命中同一非法条件时失败 |

例如，项目字号统一采用 SVG px 语义，规范写法是有限的无单位数值（如 `font-size="24"`）；其他单位只有在转换器已有确定性换算、Checker 也按兼容输入放行时才可保留，不能成为生成提示词的新写法。兼容读取是一条受控迁移边界，不是放宽创作语言的理由。

三层职责必须分开，不能用其中一层替代另一层：

| 层级 | 单一职责 | 不承担的职责 |
|---|---|---|
| 提示词、模板与示例 | 精确表达项目规范写法，从源头减少偏差和 warning | 不作为正确性或安全边界 |
| `svg_quality_checker.py` | 在作者状态上执行项目合同；error 阻塞，非阻塞 warning 放行 | 不静默改写页面，也不猜测设计意图 |
| `svg_to_pptx.py` | 对编译映射与 package 执行防御校验；归一化已支持的兼容形式；把前置 SVG 质量报告关联进 postflight | 不重跑完整 `svg_quality_checker.py`，也不以“文件已生成”替代前置质量门 |

---

## Generate PPTX 路线架构

下图描述 Generate PPTX 路线，也包含其 `beautify-pptx` profile。Create Template 有独立的工作区生命周期；Fill Native PPTX 与 Enhance Native PPTX 直接操作 OOXML。本文后续路线表会覆盖全部四条顶层路线。

```
用户输入 (PDF/DOCX/XLSX/PPTX/URL/Markdown/主题文本)
    ↓
[源内容处理与事实充分性检查] → source_to_md.py 按类型分派转换器；topic-only 或关键事实缺口进入 topic-research
    └── 原始或转换后内容就绪；研究分支形成补充 Markdown 与 facts provenance，随后作为来源导入项目
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[归档来源与项目级分析（有来源文件时；纯对话文本跳过）] → project_manager.py import-sources <项目路径> <来源...>
    ├── 先按所有权边界把传入文件 move/copy 到 sources/
    ├── 再对已归档 PPTX 执行 intake，写入 analysis/<stem>.identity.json、<stem>.slide_library.json、source_profile.json
    ├── 若缺少同 stem 的规范 Markdown，再对该归档 PPTX 运行 ppt_to_md.py
    └── sources/ 内容型文件成为内容契约
    ↓
[模板 / 品牌 / 布局（可选）] — 默认跳过，直接自由设计
    仅在用户明确提供符合当前合同的 Brand/Layout/Deck 工作区根路径时触发：可以是全局模板库条目根，也可以是项目工作区根
    原生 PPTX 模板请求进入 template-fill；可复用 SVG 模板需先通过 create-template 创建
    ↓
[Strategist] 策略师 - 三阶段策略师确认与设计规范 → design_spec.md + spec_lock.md
    ↓
[Image Acquisition] 图片获取（当资源列表中有需要 AI 生成、网络搜索或切片的图片时）
    ↓
[Executor] 执行师
    ├── 生成开始前启动 live preview，并在生成期间保持可用
    ├── 先生成 P01 → svg_quality_checker.py --stage first-page --json
    ├── 把 P01 作为方法样本分类完整 issue set；消除全部 blocking error，并处理选定的 advisory warning
    ├── P02 至末页连续生成项目规范化 SVG 页面 → svg_output/（中途不再运行 checker）
    ├── [Quality Check] svg_quality_checker.py --stage final --json（强制通过，0 错误；warning 非阻塞）
    └── 讲稿生成：完整讲稿 → notes/total.md
    ↓
[图表校准（条件触发）] → verify-charts 工作流（含数据图表的 deck 必须在此步骤校准坐标）
    ↓
[视觉自检（可选，opt-in）] → visual-review 工作流（仅在用户明确请求时触发）
    ↓
[后处理] → total_md_split.py（拆分讲稿）→ finalize_svg.py → svg_to_pptx.py（防御校验后编译）
    ↓
输出：
    svg_final/
    └── *.svg                                           ← 强制派生的视觉预览；尝试内联受支持图片，EMF/WMF 保留外链例外

    exports/
    ├── <project_name>_<timestamp>.pptx                       ← 默认原生形状版（DrawingML）
    ├── <project_name>_<timestamp>_native_charts_tables.pptx  ← 显式 --native-charts-and-tables 变体
    └── <project_name>_<timestamp>_narrated.pptx              ← --recorded-narration 或 --narration-audio-dir 变体

    validation/
    ├── svg_quality_report.json                      ← blocking / introduced / inherited / source-import 分类结果
    └── <output_stem>.report.json                    ← 关联最终 SVG 质量报告的 package / 资源审计

    # 默认流程（未指定 -o）先创建备份目录，再 best-effort 复制作者源
    backup/<timestamp>/
    └── svg_output/                            ← 成功复制时可由冻结作者源重建 pptx
```

未显式指定 `-o` 时，native 与 narration 标记可以组合成 `<project_name>_<timestamp>_native_charts_tables_narrated.pptx`；显式 `-o` 则保留调用者给定的文件名。

### SVG 是受约束的页面设计语言

凡是通过 SVG 创作或重新设计页面的工作流，`svg_output/` 都是完整的页面设计权威，但这里的 SVG 专指通过项目合同校验的项目规范化 SVG，而不是任意浏览器可渲染的 SVG。最终幻灯片中应出现的文字、图片、形状、图示、图表 / 表格 fallback、背景和模板派生布局元素，都必须已经存在于对应页面 SVG 中，或被它明确引用。模板、`design_spec.md` 和 `spec_lock.md` 负责指导 SVG 创作；导出器不能把它们当成第二层画面来源，在导出阶段补入 SVG 缺失的页面内容。

最小语义标记不会削弱这条闭包。自由设计、brand-only 和 `template_reuse_scope: style` 页面使用 `pptx_structure.mode: flat`：所有已表达对象保持 Slide 本地，不创作任何 Master/Layout 身份、分层或 placeholder metadata。导出器根据当前配色/字体 lock 生成一个属于本项目的干净 Master 和一个 Blank Layout，删除 title/body 等内置内容占位符与未使用的内置 Layout，仅保留标准日期、页脚和页码能力钩子，但不提升任何 Slide 内容。只有 `template_reuse_scope: mirror|layout` 使用 structured 路线，每张新页面从第一版 SVG 起就声明 Master/Layout 身份。固定 Master/Layout 视觉是根节点直接原子元素；可复用内容槽位是顶层 group，带显式设计区域 bounds 和一个兼容 carrier；复合 `object` 区域走显式 proxy 降级，Layout 也允许零槽。`data-pptx-role` 只补充专用 metadata 尚未表达的少量页面框架、package 或动画行为。带旧结构语义的模板包不能原地升级，也不能作为 Step 3 的 structured 输入：先通过 `create-template` 创建新工作区；原生 PPTX 只提供包内仍然存在的事实，旧 SVG 只作为视觉参考；随后由 Generate PPTX 路线按照 AI 推导的应用计划创作新页面。flat 项目是有意不带 mapping，不算 legacy。导出器不推断、修补或迁移 Master/Layout 结构与 placeholder。

| 领域 | 权威来源 |
|---|---|
| SVG 创作路线中的可见页面内容与布局 | `svg_output/` 中的最终页面 SVG |
| 项目规范化 SVG 的语法、兼容形式与映射边界 | 由 [`references/shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 选择的拆分权威集 |
| Master/Layout/Slide 打包与原生对象映射 | SVG 到 PPTX 的翻译；可以重组 SVG 已表达的内容，但不能创造新的可见内容 |
| 动画、转场、讲稿和旁白 | 各自的 sidecar / 资源与 PPTX package 后处理 |
| 直接原生 PPTX 编辑 | 所选原生工作流自己的 PPTX / OOXML 契约 |

这是一条“页面设计闭包”规则，不代表 SVG 要描述完整 PPTX package。相关验收是：完成的页面 SVG 能重建对应幻灯片的可见设计；不要求仅凭 SVG 重建讲稿、音频、计时、relationships 或直接原生编辑结果。

`svg_final/` 不改变这条边界。Step 7 必须从 `svg_output/` 派生视觉预览：受支持的位图 / SVG 资源会内联，EMF/WMF 为 native passthrough 保留外部引用；无法解析的普通图片会保留原引用，当前 finalizer 只统计这类处理错误，并不据此让整次处理失败。这组文件供 IDE、浏览器查看，也可由用户手动作为 SVG 图片插入 PowerPoint；它不是第二条 PPTX 导出路线，也不承担 PowerPoint 手工“转换为形状”的兼容性。需要可编辑形状时，唯一受支持的路径是项目转换器把 `svg_output/` 翻译为原生 DrawingML PPTX。

已有 PPTX 请求按修改模型分流：两条原生工作流绕过 SVG，`beautify-pptx` 则仍是 Generate PPTX 内部通过 SVG 重做可见设计的 profile：

| 工作流 | 输入角色 | 输出机制 | 为什么独立 |
|---|---|---|---|
| `template-fill-pptx` | 原生 PPTX 模板 deck + 新材料 | 克隆选中的幻灯片，并在 OOXML 层改写文本 / 表格 / 图表 | 保留用户的 PowerPoint 原生页面壳，而不是转成 SVG |
| `native-enhance-pptx` | 内容与版式都应保持稳定的已完成 PPTX | 在 OOXML 层直接补讲稿、旁白、计时和转场 | 只追加原生增强，不重新设计 |
| `beautify-pptx` | 页数、页序、每页措辞都必须 1:1 保留的已有 PPTX | 抽取源事实后走 SVG 流水线重新生成 native deck | 只改布局和层级，不做原地编辑 |

---

## 路线判定速查表

可执行路线判定以 [`workflows/routing.md`](../../skills/ppt-master/workflows/routing.md) 为准；本节只是面向技术设计的速查和解释，不是第二份路线矩阵。

先用这张表判定路线，再讨论实现细节。大多数失败执行不是命令错了，而是一开始就走错了路线。

| 请求形态 | 路线 | 边界 |
|---|---|---|
| 只有主题，或现有材料缺少实现用户目标所需的事实 | Generate PPTX Step 1 内运行 `topic-research` | 只有主题时立即研究；有材料时先转换 / 阅读，只补已识别的事实缺口 |
| 有源文件或对话文本，deck 结构可以重想 | Generate PPTX | Strategist 可以拆分、合并、删除、重排和重设计 |
| PPTX 作为源材料，用户允许重构故事和页结构 | Generate PPTX，经 `ppt_to_md` + `pptx_intake` | PPTX 身份和几何是事实与候选，不是复刻约束 |
| 原生 PPTX 模板 + 新材料 / 新主题 | Fill Native PPTX（`template-fill-pptx`） | 克隆并填充原生页面；不生成 SVG |
| 现有 PPTX，页数 / 页序 / 措辞 1:1 保留，只改善排版 | Generate PPTX + `beautify-pptx` profile | 通过 SVG 重新生成；内容和分页锁定 |
| 已完成 PPTX，保持内容 / 布局稳定，只加讲稿、音频、计时、转场 | Enhance Native PPTX（`native-enhance-pptx`） | 直接 OOXML patch；不重新设计 |
| 用户想从一个或多个 PPTX/SVG、图片/PDF、文档/网站、品牌资产、直接文字或混合参考材料包构建可复用模板工作区 | Create Template（`create-template`） | 固定入口读取每个适用证据通道，只分派一个 Create Brand、Create Layout 或 Create Deck 子工作流，再返回供 Generate Step 3 使用的工作区根目录；结构型子工作流可导出审阅 PPTX |
| 用户提供符合当前合同的明确模板路径 | Generate PPTX Step 3 | Brand/Layout/Deck 工作区解析 `templates/design_spec.md`；平铺根目录可解析直接 `design_spec.md`；语义旧包会被拒绝，并通过 Create Template 替换 |
| 用户要求调整对象级动画顺序 / 效果 / 计时 | Generate PPTX + `customize-animations` 阶段 | 通过 `animations.json` 控制可选导出策略 |
| 用户要求预览、选择、注解或重导出浏览器编辑 | Generate PPTX + `live-preview` 阶段 | 注解只在规定交接点应用 |

“优化这份 PPT”这类含糊请求归约为一个判定点：是否保留原始页数、页序和逐页措辞。两者都属于 Generate PPTX；保留时选择 `beautify-pptx` profile，允许重构时使用普通 profile。

---

## 技术流程

**核心流程：AI 生成 SVG → 后处理转换为 DrawingML（PPTX）。**

整个流程分为三个阶段：

**第一阶段：内容理解与设计规划**
源文档（PDF/DOCX/XLSX/PPTX/URL/Markdown/主题文本）会被转换成 Strategist 所需的内容事实与分析事实。Strategist 先确认开放式沟通契约，再由此推导完整 PPT 方案、解决生产机制，最终输出完整设计规格。

**第二阶段：AI 视觉生成**
Executor 角色逐页生成演示文稿的视觉内容，输出为 SVG 文件。这个阶段的产物是**设计稿**，而非成品。

**第三阶段：工程化转换**
后处理脚本将受支持的 SVG 向量元素转换为 DrawingML。文本和向量形状会保持为 PowerPoint 原生对象——可点击、可编辑、可改样式；位图资源则复制为 PPT picture media，而不是把整页压平成一张图片。

---

## 产物流

Artifact 的来源 / 派生所有权以 [`artifact-ownership.md`](../../skills/ppt-master/references/artifact-ownership.md) 为准；本节只把同一数据流可视化成架构说明。

维护这套系统时，把文件夹理解成数据流会比“这些目录刚好存在”更清楚：

```text
sources/<content files> ────────┐
sources/*.facts.json ───────────┤
analysis/source_profile.json ───┼─> Strategist -> design_spec.md + spec_lock.md
analysis/image_analysis.csv ────┘

design_spec.md + spec_lock.md + images/ + icons/ + templates/
    └─> Executor -> svg_output/
          ├─> 规划产物与引用保留在有效的当前上下文中
          ├─> project_manager.py page-context <project> P<NN> [按需]
          │     └─> --record-usage -> analysis/page-context/P<NN>.usage.json
          ├─> svg_quality_checker.py -> validation/svg_quality_report.json
          ├─> finalize_svg.py -> svg_final/
          └─> svg_to_pptx.py -> exports/<name>_<ts>.pptx + validation/<output_stem>.report.json
                                       backup/<ts>/svg_output/ [默认输出路径；目录创建后复制为 best-effort]

直接 OOXML 路由：
analysis/<stem>.slide_library.json + 源 PPTX + fill_plan.json
    └─> template_fill_pptx.py -> exports/*.pptx
源 PPTX 项目归档副本 + 增强计划 + 讲稿/音频/计时资产
    └─> native_enhance_pptx.py -> exports/*.pptx
```

关键切分是：`svg_output/` 是作者状态，`svg_final/` 是派生视觉预览，`exports/` 和 `backup/` 是派生的交付或归档状态。模糊这条线，会让校验、重导出和人工修复都更难推理。

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

这张表只展示概念对应关系，不是对整个 SVG 标准的承诺，也不承诺所有映射语义无损。每项受支持能力都必须在 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 路由到的适用模块中拥有明确映射，说明项目规范写法、允许的兼容输入、目标 DrawingML 表达、保真度和拒绝条件；涉及 PPTX 回导的能力还要说明来源 PPTX / OOXML 语义。映射状态可以是精确、确定性归一化、显式 fallback、sidecar 或 unsupported；讲稿、动画、relationships 等 package 语义不必强行塞进 SVG，但必须明确由哪条路线承载。

如需从 PowerPoint 功能出发逐项查看这些关系，请参阅 [PowerPoint 功能 ↔ 项目 SVG 映射指南](./powerpoint-svg-mapping.md)。该文档负责公开能力与 PPTX 导入语义映射；由 `shared-standards.md` 路由的权威集负责生成 SVG 创作。

主生成路线采用**规范窄写入、受控兼容读取**。新生成的 `svg_output/` 与可复用模板只使用项目规范写法，例如不透明的六位大写 `#RRGGBB`，透明度放在对应的 `fill-opacity`、`stroke-opacity`、`stop-opacity`、`flood-opacity` 或原子元素 `opacity` 中。历史或人工输入只有在兼容合同明确登记、转换结果唯一且输出合法时才可继续导出；Checker 对这类写法给出非阻塞 warning，转换器在编译边界统一归一化。任何需要猜测、没有映射或可能产生损坏 PPTX 的表达都必须报 error。

因此，转换不是在任意 SVG 和 DrawingML 之间做格式猜测，而是在项目规范化 SVG 与 DrawingML 之间执行有注册表、有保真度说明、可测试的编译。

SVG 也是唯一同时满足流程中所有角色需要的格式：**AI 能可靠地生成它，人能在任意浏览器里直接预览和调试，脚本能按明确的兼容合同转换它**——在生成任何 DrawingML 之前，设计稿就已经完全透明可见。

---

## 源内容转换

源文档（PDF / DOCX / EPUB / XLSX / PPTX / 网页）会在 Strategist 开始前完成归一化，但当前架构已经不是“全部转成 Markdown 后其他信息都不重要”的单通道模型。现在有两条事实通道，各自拥有明确职责：

| 通道 | 产物 | 所有者 | 用途 |
|---|---|---|---|
| 内容契约 | `sources/` 内容型文件（以 `<stem>.md` 为主） | `source_to_md/*` 转换器 + `import-sources` | 文本、表格、图表数值、SmartArt 节点文字、引用和源材料叙事 |
| 结构化分析 | `analysis/*.json` / `analysis/*.csv` | intake 与分析工具 | PPTX 身份信息、页面几何、原生表格/图表、SmartArt 关系，以及图片尺寸、比例、引用次数、媒体类型与渲染能力等可测量事实 |

对 PPTX 源文件，`project_manager.py import-sources` 先按所有权边界把原件 move/copy 到项目 `sources/`，再以归档后的路径运行 `pptx_intake.py`；只有没有同 stem 的显式或既有规范 Markdown 时，才在最后调用 `ppt_to_md.py`。因此正常首次导入会得到两条事实通道，但去重路径可跳过重复 Markdown 转换，intake 失败也会记录为导入 note，而不是伪造分析产物。Markdown 仍然是主生成流水线的内容源；成功的 intake bundle 会写出 `<stem>.identity.json`、`<stem>.slide_library.json`，并把紧凑的多 deck 索引合并到 `analysis/source_profile.json`。Strategist 默认读取这个紧凑索引来获取源事实；只有特定工作流需要原始细节时，才打开单个 deck 的原始 artifact。这个边界很重要：主流水线可以重构页数和叙事，而 `template-fill` 与 `beautify` 会把同一批 intake 事实中的一部分提升为更强约束。

转换器生成的图片资产也会被归一化。伴随的 `<stem>_files/` 目录会导入项目级 `images/` 池，`image_manifest.json` 按文件名合并；当导入后目录名发生变化时，Markdown 中的资源引用会被重写。Office 矢量图（`.emf` / `.wmf`）是一等运行时资产：intake 阶段不栅格化它们，`finalize_svg.py` 为 native 路径保留外部引用，`svg_to_pptx.py` 以 Office 矢量媒体嵌入，避免 CJK 字体替换和矢量细节损失。

两个转换器设计选择仍然成立：

**Native-Python 优先，外部二进制兜底。** 常见格式由纯 Python wheel 处理，pandoc 仅在长尾小众格式时才被调用。让每个用户都去装一份可能没有权限装的系统级二进制是一种可用性税，而大多数输入是 docx / pdf / html / pptx，这种税不值得。

**TLS 指纹模拟应对高安全站点。** 网页抓取默认走 Python 版 `web_to_md.py`，并在可用时依赖 `curl_cffi` 做类 Chrome TLS 指纹模拟。微信公众号和不少 CDN 会直接屏蔽 Python 默认握手；把这件事留在 Python 转换路径里，避免让 Node 抓取器成为主架构。

---

## 项目结构与生命周期

`project_manager.py init` 创建固定的项目工作目录；默认导出随后创建带时间戳的备份目录，再尝试复制 `backup/` 快照。完整生命周期结构如下：

| 目录 | 职责 |
|---|---|
| `sources/` | 原件归档、归一化 Markdown、转换器伴随文件 |
| `analysis/` | 机器抽取事实：PPTX intake bundle 与按需重算的图片分析 |
| `images/` | 单一运行时图片池：用户图、抽取图、公式图、网络图、AI 图、切片图、EMF/WMF |
| `icons/` | 由 `icon_sync.py` 复制的项目级图标集；导出时的全局库回退仅用于 legacy compatibility |
| `templates/` | 复制进项目的模板 spec / SVG reference / 非图片模板资产 |
| `svg_output/` | 唯一手写 SVG 源目录 |
| `svg_final/` | 强制派生的视觉预览 SVG；尝试内联受支持位图 / SVG，保留 EMF/WMF 外链例外；服务 IDE / 浏览器，也可手动作为 SVG 图片插入 PowerPoint |
| `live_preview/` | 预览服务状态、直接编辑历史和注解日志 |
| `notes/` | `total.md` 与拆分后的逐页讲稿 |
| `validation/` | SVG 质量报告与 PPTX postflight 审计报告 |
| `exports/` | 带时间戳的 native PPTX 交付物 |
| `backup/<timestamp>/` | 默认导出先创建时间戳目录，再尝试复制冻结的 `svg_output/`；复制失败不令导出失败，但目录创建失败当前不会降级处理 |

CLI 支持 `--move`、`--copy` 和自动默认，但共享同一条固定的所有权边界：只有仓库 `projects/` 目录下的源文件可以 move 到目标项目的 `sources/`；其他本地路径一律 copy 并保留原文件，即使显式传入 `--move` 也不例外。`--copy` 用于要求保留的 projects-local 输入。Generate PPTX 使用自动模式，因此仓库正式文档和外部用户文件不会在导入时被移除。

---

## 架构不变量

可执行的 artifact ownership 不变量以 [`artifact-ownership.md`](../../skills/ppt-master/references/artifact-ownership.md) 为准；本节解释这些边界为什么在架构上重要。

这些不变量强于普通实现偏好。如果某个改动破坏了其中一条，它很可能是在改变架构，而不是做重构。

| 不变量 | 实际后果 |
|---|---|
| `sources/` 内容型文件是主流水线内容契约 | 主 SVG 路线中的文本、表格和图表数值来自 `sources/` 内容型文件（Markdown 为主，`.txt` / `.csv` / `.json` / `.yaml` 等同样计入）；已知 sidecar（`*.conversion_profile.json`、`*_files/image_manifest.json`）排除在外 |
| `analysis/` 存机器事实，不存设计契约 | `source_profile.json` 和 intake artifact 辅助 Strategist；除非工作流明确规定，否则不锁定页数 / 页序 |
| `design_spec.md` 解释设计；`spec_lock.md` 执行设计 | 两者始终是权威产物；按需投影不会取代它们 |
| 规划上下文有效时持续复用 | 连续执行直接使用完整 Design Spec、lock 与已触发引用；fresh/resumed/restarted 或压缩后才重新读取一次 |
| `page-context` 按需调用 | 只读投影器用于诊断、确定性路由检查和可选的用量统计，不是逐页门禁 |
| `svg_output/` 是唯一手写 SVG 目录 | 质量检查、手工编辑、重导出和 `update_spec.py` 都面向作者源 |
| `svg_final/` 是派生产物 | 它必须能从 `svg_output/` 重建，只负责视觉预览；受支持资源尽量内联，EMF/WMF 保留外链例外，不应成为 native 导出的事实源 |
| native PPTX 标准导出读取 `svg_output/` | 唯一受支持的可编辑形状路线由项目转换器执行；它要在 finalize 重写前保留图标、`preserveAspectRatio`、圆角矩形和原生图片裁剪语义 |
| PowerPoint 手工“转换为形状”不属于兼容性契约 | `svg_final/` 可以作为 SVG 图片插入，但转换后的结构与视觉结果不做保证，也不反向约束 SVG 允许能力 |
| 直接 OOXML 路由不进入 SVG 流水线 | 保留型工作流直接 patch 原生 PPTX parts |
| 图片事实来自重算元数据 | `analysis/image_analysis.csv` 从实时 `images/` 目录重算；Strategist 先用源文上下文，只在图片语义或安全放置仍无法确定时查看那一张具体图片；Executor 不重新读取源图像素 |
| 原生 PPTX 模板不是 Step 3 模板 | Step 3 只消费可复用模板目录 |

---

## Canvas 格式系统

PPT Master 不只服务 PPT——同一套 SVG → DrawingML 流水线还能产出方形海报、9:16 故事、A4 印刷品。各格式特定的约定（比例、安全区、品牌区等）住在 [`references/canvas-formats.md`](../../skills/ppt-master/references/canvas-formats.md)。

值得标注的架构选择：**viewBox 是像素，不是绝对单位。** 像素空间让 AI Executor 思考布局没有歧义（`x="100"` 就是左缘 +100px），人类在浏览器里检查也直接。到 EMU 的换算只在导出时发生一次——选像素意味着流水线的其余环节（Strategist、Executor、质量检查、后处理）永远不需要在 EMU 思维下工作，那对 AI 生成和人类调试都是敌对的。

---

## 模板系统与可选路径

模板是**可选项，不是默认**。Strategist 默认走自由设计——AI 完全凭源内容创造视觉系统。模板路径只在用户明确提供目录路径时启用。

**为什么默认自由设计。** 模板是地板，但很容易变成天花板：它会把整个 deck 锁进模板自有的视觉惯用语，无视内容本身想要怎样被呈现。自由设计的布局从源内容的结构推导而来，而不是从一套固定语法套上去——视觉节奏跟着内容走，而不是跟内容打架。约束模式在窄场景里确实更好（品牌锁定的 deck、强类型场景如学术答辩或政府报告），所以它一直在；但 AI 不主动去抓，是用户去抓。

**机械触发，不做语义匹配。** 像 `presentation_core` 这样的裸名字、品牌提及，或“麦肯锡风格”这类风格短语，即使库里存在相似目录，也不会触发 Step 3。Step 3 只消费显式路径。当前 Brand/Layout/Deck 工作区均解析 `templates/design_spec.md`；平铺目录只有在 SVG 已满足当前合同时，才兼容从根目录读取 `design_spec.md`。目录形态从不授权结构迁移；带旧 Master/Layout/placeholder 语义的包必须先替换为新建的模板工作区，才能进入 Step 3。发现性交给模板索引和显式问答（“有哪些模板可以用？”），不交给运行时 fuzzy matching。

当前 Brand/Layout/Deck 都采用同一工作区路由合同；Brand 不含 SVG roster，空的可选目录直接省略：

```text
<template_workspace>/
├── templates/   # design_spec.md；Create Layout / Create Deck 另含 SVG 原型
├── images/      # 可选；位图素材，SVG 统一引用 ../images/<name>
├── icons/
│   └── imported/ # 可选；导入向量素材的唯一规范副本
└── exports/     # 可选、按需生成的审阅文件；全局库下由 Git 忽略
```

`<template_workspace>` 可以是 `skills/ppt-master/templates/<kind>/<id>/`，也可以是 `projects/<name>/`。Step 3 接收这个根目录。工作区可在两个位置之间迁移而不改形；唯一的范围差异是全局索引注册。空的可选目录不创建，`exports/` 也不会复制进新项目。

对 Create Layout / Create Deck，`standard` 与 `fidelity` 会重新创作 SVG 和新的 Master/Layout/slot 系统；来源拓扑只作为视觉证据，不保留、也不蒸馏。`mirror` 把来源包内实际存在且已验证的页序、Master/Layout 身份与父子关系、placeholder 事实和受支持视觉物化到新工作区，不做语义归纳或缺口补造。只有被保留的来源本身已经品牌中立且应用中立时，Layout mirror 才合法；否则应重新创作 Layout，或把这些事实保留为 Deck。由于结构层不能是 `<g>`，固定结构层的来源 group wrapper 只允许机械展开成直接原子，同时保持归属、paint order 和视觉一致。Create Brand 只分析并物化身份片段，不进入这些结构复制策略，也不生成 SVG roster。

三类模板拥有不同的设计契约片段：

| Kind | 拥有的片段 | 典型内容 | 对 Strategist 的影响 |
|---|---|---|---|
| `brand` | 身份片段 | 配色、字体、logo、语气、图标风格 | 锁定身份；结构保持自由 |
| `layout` | 品牌中立的结构片段 | 画布、页面结构、语义文字角色/空间行为、页面类型、SVG roster | 提供结构能力；身份与沟通应用仍由下游决定 |
| `deck` | 应用段 + 一体化身份/结构 | 重复场景、受众与结果、代表性页面角色、身份和真实 SVG roster | 提供描述性语境和原型；Strategist 将其与独立确认的 Stage-1 契约及当前内容对照，再推导应用计划 |

Theme、Slide Master、Slide Layout 与 Placeholder 是编译生成的 PowerPoint 原生对象，不是新的模板 kind。Layout 决定拓扑、位置、语义文字角色与空间行为，Brand 决定身份值与资产。`template_reuse_scope: layout` 会结合已确认的阅读模式和字号体系解析最终 placeholder 格式；`mirror` 则保留来源的字面格式与文字拓扑。两类规则都可编译进同一套原生 Master/Layout 图谱。

当用户提供多个路径时，融合是**片段级**而不是字段级：brand 覆盖身份片段，layout 覆盖结构片段，deck 提供应用段。只有 Layout 的页面角色和槽位能够表达 Deck 的必需叙事/内容角色时，才能覆盖 Deck 结构，否则必须显式提出合成冲突。项目内 Brand + Layout 组合的应用语境来自 Stage 1，不会自动升级成可注册的 Deck。同类冲突也会显式列出，而不是按输入顺序默默决定。这样融合后的 spec 能明确说明每个片段来自哪里，便于审计和复现。

**原生 PPTX 不能直接作为 Step 3 工作区。** 普通 Generate 可以把 PPTX 作为源材料使用，`beautify-pptx` 也可以在页数、页序和逐页措辞 1:1 的边界下重新设计；这两种情况都不会把原始 PPTX 当作 Step 3 模板。把原生 PPTX 作为模板或页面壳、再用新材料填充时，默认进入 Fill Native PPTX；若请求允许拆分、合并、删页、重排或叙事重构，则仍属于 Generate。只有当目标是创建可复用模板工作区、并在 SVG 路线的 Step 3 中重复使用其设计系统时，才先运行 Create Template，再传入生成的工作区根目录。

**布局是 opt-in，图表和图标不是。** 这种不对称不是矛盾——*布局*正是锁定视觉惯用语的那一层（地板/天花板问题），而图表和图标是不会施加 deck 级风格约束的复用原语。同一个 `templates/` 目录，但在视觉契约里扮演的角色不同。

---

## 角色系统：单一流水线中的专业模式

PPT Master 用的是**单主代理内的角色切换**，不是并行子代理。Strategist、Image_Generator、Executor，以及各路线中的 child workflow / profile / stage，本质上都是按需加载的指令作用域；它们不是带着各自过期 deck 状态的独立 agent。这个选择有三条互相支撑的理由：

**为什么是单代理而非并行子代理。** 页面设计依赖完整的上游上下文——Strategist 的色彩选择、图片资源是否成功获取（还是失败被替代）、之前几页的视觉节奏。子代理拿到的只能是这个上下文的过期局部快照，产出的 deck 视觉会逐页漂。同一逻辑也禁止分批生成（比如一次 5 页）：分批加速上下文压缩，deck 的视觉一致性下降速度比节省的速度更快——不划算。

**为什么是角色专属 reference 而不是一个超大 prompt。** Strategist 跑的是「跟用户协商」模式（开放式、对话式、可以回退），Executor 跑的是「产出严格 XML」模式：不得重选上游方案或漏掉必需属性，但在 Design Spec 留出的范围内仍拥有几何、构图、层级和视觉处理的实现权。把两者塞进同一个 prompt，强迫模型在同一个 turn 里持守相互矛盾的纪律——所有混合模式的 prompt 工程病灶都会出现。按角色拆开，每个角色只加载它需要的、扔掉其他。

**策略师确认阶段是默认连续路线中的主要用户设计决策 gate。** Strategist 阶段以一个按依赖排序的三阶段 gate 作为核心决策点。第一阶段确认开放式沟通契约与画布。其中的文本框承载可编辑推荐，但没有任何一项要求非空：确认时按当前文本原样保存，清空后的值保持为空，不会回退到推荐内容。第二阶段只从该契约计算一次并确认完整 PPT 方案：阅读模式、叙事 mode、页数、成套视觉系统、图片来源和生成图渲染。存在模板时，Strategist 还会根据真实工作区和当前内容推导页面/原型应用计划，并以可编辑的自然语言文本展示；只有内部复用/遵循模式保持隐藏。阅读模式决定信息由页面、视觉、讲者和备注如何共同承担，其选项卡不展示 px 数值。浏览器可以在本地执行确定性的「阅读模式 → 正文基准 → 未锁定角色字号」联动；手动编辑字号即锁定可见值，不会重新计算第二阶段。第三阶段也只计算一次，并且只处理生产机制：条件式 AI 图片获取路径、公式策略、生成模式与规范精修。JSON 为兼容保留 `delivery_purpose` 键，但用户侧统一称为阅读模式。生成图直接继承已选 PPT 色彩锚点，不再单设图片调色选择。最终状态有两个等价载体：默认 UI 路径在最终等待返回后只读取一次 `confirm_ui/result.json`；显式 chat-only 或委托路径保留等价的最终确认摘要，并可不产生 `result.json`。两条路径都先把全部最终值（含生产机制）固化到 `design_spec.md` 并完成 fidelity audit，再据此编写 `spec_lock.md`；正常的 lock 编写与下游执行不再回读确认通道。显式 `refine-spec` 和必需人工素材未就绪仍会引入各自的条件式阻塞点，因此这里不是对所有 runtime gate 的排他声明。项目校验要求 `spec_lock.md ## communication` 下存在紧凑的 `audience` / `objective` / `core_message` 锚点，并要求 §IX 每个 Slide block 都有 `Audience move`。

**图片分析以重算元数据为先，Strategist 只保留小范围视觉兜底。** 当项目里存在图片时，`analyze_images.py` 把可度量事实重算到 `analysis/image_analysis.csv`；该 CSV 是实时 `images/` 目录的派生视图，不是持久缓存。Strategist 先根据图片在源文中的位置与前后文、图注 / alt / 标题、文件名、用户说明、已有资源记录和这些元数据判断。只有当某一张具体图片在选用、事实身份、页面角色、裁剪安全或焦点放置上仍有实质歧义时，才可单独查看它，绝不得扫描整个图片目录。结论写入 Design Spec §VIII 后，Executor 只消费该计划与几何数据，不会重新打开源图进行语义探索。用户图、抽取图、网络图、AI 图、公式图和切片图仍统一汇入同一张可度量事实表。

**保留的规划上下文**负责跨页连续性；按需逐页投影只承担下文所述的诊断用途。

---

## 执行纪律

Generate 执行以 [`workflows/generate-pptx.md`](../../skills/ppt-master/workflows/generate-pptx.md) 为权威，该文档拥有 Step 1–7 与 Generate 专属规则；[`SKILL.md`](../../skills/ppt-master/SKILL.md) 只拥有全局执行纪律，以及交接到 `routing.md` 的强制入口。这些规则整体看起来很官僚，但存在的理由是：LLM 默认行为是“让我在这一 turn 里把整个问题搞定”，而这恰好是串行流水线最不该有的形状——串行流水线要求每一步的输出都是有界、过 checkpoint、被下一步消费的。它们共同关闭了实际反复出现的失败模式：乱序执行、AI 代为做用户设计决策、跨阶段打包、前置条件未满足、投机预先准备、子代理上下文丢失、分批漂移、长 deck 色彩字体漂移、脚本批量生成 SVG 漂移，以及路由歧义。

全路由通用的停止 / 继续规则以 [`failure-recovery.md`](../../skills/ppt-master/workflows/governance/failure-recovery.md) 为准；其中具体故障矩阵与续跑入口目前覆盖 Generate PPTX。本节不复制这些规则。

其中三条边界尤其关键。第一，Executor 页面 SVG 必须由当前主代理逐页手写；禁止写 Python / Node / shell 生成器批量吐 SVG，因为这种输出会丢失跨页判断和视觉连续性。第二，生成节奏固定为 `P01 → first-page gate → 不间断生成其余页面 → final gate`。P01 不只是单页样张：执行者必须先输出 `gate-signal`，区分 method-level、page-local 与未覆盖的能力，再把已解决的方法规则带入后续页面；P02 到末页之间不分批，也不插入 checker 调用。第三，路由是确定性的：原生 PPTX 模板、beautify、native enhancement、自定义动画、live preview 等触发条件已经在仓库里定义清楚时，不再额外抛给用户一个开放式路线选择题。

角色切换协议（切换模式前必须 `read_file references/<role>.md`）有两个互相支撑的作用：把新鲜的角色指令载入上下文，覆盖前一模式的漂移；对话 transcript 中的可见标记构成审计轨迹，让用户能看到 agent 何时切换了模式——回看一个具体决策为什么这样做时，这条线索很关键。

---

## 设计规范的传播：spec_lock.md 作为上下文执行契约

Strategist 阶段产出两份看起来冗余但服务不同对象的产物：

- `design_spec.md` —— 人类可读叙述；deck 的「为什么」（沟通意图、受众变化、叙事 / 模板 / 视觉理由、页面大纲）
- `spec_lock.md` —— 机器可读执行契约；包含紧凑的 `audience` / `objective` / `core_message` 沟通锚点，以及跨页稳定的身份/复用角色和路由值（核心 HEX/字体角色、图标库、图片资源与结构映射）

为什么两份都要？`design_spec.md` 保存完整的确认方案与理由；`spec_lock.md` 只命名必须跨页稳定或参与路由的子集。它根据 Design Spec 与页面/资源/模板上下文编写，不再逐字段复制 UI JSON 或聊天摘要等确认通道原始载荷。[Generate PPTX Step 6](../../skills/ppt-master/workflows/generate-pptx.md#step-6-executor-phase) 在有效执行上下文中只保留并复用这两份产物。fresh/resumed/restarted、上下文压缩或只剩摘要时重新完整读取一次；未变化的连续上下文不重复读取。局部色阶、渐变/效果色与零星的非结构性展示字体属于页面判断；一旦重复出现或形成稳定语义，就必须先提升为上游 lock 角色。

该视图省略 Executor core 已经恒定加载的通用 SVG/图标禁令，只保留项目专属 forbidden 行。图片从当前页 brief、图片资源表中的显式页分配和 mirror 原型引用中选择；已分配给其他页面的图片会被排除，仍无法归属的 legacy 图片保留在兼容子集中，只有所有锁定图片都能确定归属到其他页面时才记录 `confirmed-none`。

这份 lock 同时也是逐页路由表。除了全局配色和字体，它还承载 `page_rhythm`（`anchor` / `dense` / `breathing`）、`page_charts`（某页选中的图表目录参考；它只触发读取对应 SVG 与 §VII Usage，不锁定最终图表类型或几何）、带放置/裁剪契约的图片行，以及决定加载哪些执行规则文件的 `mode` / `visual_style`。选定 custom 方向时，lock 还承载已消解的 `mode_behavior` / `visual_style_behavior`；当它确实综合或借鉴已有目录项时，再用可选的 `mode_references` / `visual_style_references` / `image_rendering_references` 记录全部精确 id，执行阶段会先读取每个对应文件再综合。真正全新的 custom 不写参考字段。`template_reuse_scope: mirror|layout` 项目的 lock 还承载 `page_layouts`（每页继承哪个输入模板 SVG）、唯一的 `pptx_masters` / `pptx_layouts` 定义，以及 `page_pptx_layouts` 页面分配；`template_reuse_scope: style`、自由设计和 brand-only 项目使用 `pptx_structure.mode: flat`，那些段整段省略，而不是写成空值。其余字段的空值本身仍是信号：没有图表、没有图片，很多时候是设计选择，而不是漏填。

`page-context v2` 保留为按需投影器。每次调用都会输出绑定 `lock_source.sha256` 的紧凑全局锚点、当前 §IX/资源/路由 delta，以及大型引用的带 scope 路径/SHA 指纹；该投影既不是颜色/字体白名单，也不是替代权威。只有明确的诊断/统计需求，或页面/模板/图表的路径-SHA 问题仍未解决时才调用。有效且未压缩的上下文中做有界精确回修，可以只回读修改片段并校验；fresh、已压缩、外部、来源不明、结构性或投影不符的修改必须完整读取 Design Spec 与 lock。flat 页面没有原型引用；structured 页面使用权威完整 SVG。manifest 与 text-slot sidecar 只保留为派生工具诊断，不注入页面创作上下文。

`--record-usage` 在 `analysis/page-context/` 下为实际调用的页面写入派生快照，记录输入 hash 和紧凑 stdout 的实测大小。token 计数按需加载 `o200k_base`；没有安装 `tiktoken` 时写入 `tokens: null`，但不阻塞执行。`page-context-report` 排除过期快照，汇总已有快照并列出唯一引用指纹；统计可以只覆盖部分页面。一次加载的大型引用 payload 与其他会话上下文有意不纳入统计。

`update_spec.py` 用两个协调步骤传播一次有意的 deck 级锚点修改：把新值写入 `spec_lock.md`，然后字面替换到每一份 `svg_output/*.svg`。工具的范围**故意收得很窄**——只支持 `colors.*`（HEX 值，大小写不敏感替换）和 `typography.font_family`（属性级）。其他字段（字号、图标、图片、画布）**有意不支持**——它们的替换需要属性级或语义级理解，风险/收益不值得做批量传播。当重复出现的上下文值被明确提升为具名语义角色时，反向回写 lock 同样合理；但不能只为了清空 checker 的信息提示而扩充 lock。其他字段应修改其权威产物并重做受影响页面。

工具拒绝做备份：依赖 git 回滚。加备份机制只是重复 git 的工作，还会留下过时快照。

---

## 材料 → 规划 → 实现：餐厅合同

“做饭”不是临时解释，而是生成流程的正式所有权模型：

| 餐厅角色 | PPT Master 对应项 | 决策权 |
|---|---|---|
| 顾客与初始食材 | 用户确认与用户提供的原材料/素材 | 决定事实、意图、排除项、材料补充许可，以及要求具体到什么程度 |
| 菜单策划与备料负责人 | Strategist、`design_spec.md`、`spec_lock.md` 及其负责的材料获取阶段 | 判断材料是否充分；补齐获准补充的事实；选定内容、资源、页面清单、图表参考 key / 版式 key、字体、色板锚点、图标和裁剪边界；在执行前备齐项目级材料清单 |
| 厨师 | Executor | 只使用项目中已备好的材料，以几何、构图、层级、间距和视觉处理实现方案；不得改变所选“菜品”，也不得自行找料、换料 |

**备料有两个时点。** Topic Research 在最终确认前补充规划所需的事实：只有主题时立即运行；已有材料时先转换 / 阅读，仅在仍有关键事实缺口时补齐，而且不获取任何图片。AI / web / slice 图片只能在最终确认以及完整的 `design_spec.md §VIII` / `spec_lock.md` 之后获取，并在 Executor 开始前进入终态。Strategist 还会在编写最终方案时解析、同步并验证图标 inventory。Image_Generator、Image_Searcher 与图标同步工具只是 Strategist 负责的备料机制，不是独立决策者。

**项目中已备好的材料就是边界。** 图片和其他声明型资源，仍须由 Strategist 选定、写入规划产物，并保证项目路径可解析或明确标为 `Needs-Manual`。图标 SVG 只要已位于 `<project>/icons/` 就属于已备材料；`spec_lock.icons.inventory` 记录 Strategist 计划选用的内置图标，但不是穷尽式执行白名单。其他目录中的文件不构成使用许可。缺料必须返回上游；Executor 不得搜索、生成、下载、同步或替换资源。

**具体程度决定自由度。** “做麻婆豆腐”锁定成品身份：火候、口感和摆盘可以发挥，但不能换成番茄炒蛋或豆腐汤。“做一道豆腐菜”则保留了品类内选择空间。Strategist 可以把这个开放要求收敛成具体方案；如果 Design Spec 有意保留某个维度的开放性，Executor 可以在该范围内实现。一旦 Design Spec 已经选定具体结果，执行阶段不得重新打开选择。

**点缀只能保持局部。** 零星的页面级字体或颜色可以用于增加层级、区分和氛围，但不能发展成第二套视觉系统。结构性或重复出现的字体、色板角色、资源与 pattern 仍属于 Strategist 决策；复用前必须先更新 Design Spec/lock。

**提示词重构不变量。** 压缩提示词时，必须继续区分初始材料、用户确认、Strategist 负责的备料、策略规划和执行自由。把材料获取下放给 Executor、把许可变成配额、把灵活实现变成重新选型，或把精确计划降级成近似目标，均属于语义回归。运行时权威位于 [`strategist.md`](../../skills/ppt-master/references/strategist.md) 与 [`executor-base.md`](../../skills/ppt-master/references/executor-base.md)，提示词编写规则位于 [`prompt-style.md`](../rules/prompt-style.md)。

---

## 图片获取与嵌入

这一阶段有多项架构层面的决策：

**provider 专属 config key，不用通用 `IMAGE_API_KEY`。** 每个 backend 用自己的 `OPENAI_API_KEY` / `MINIMAX_API_KEY` 等等，当前 backend 由显式的 `IMAGE_BACKEND=<name>` 选定。统一的 `IMAGE_API_KEY` 字段第一眼看着干净，但当用户同时配了多个 provider 又不确定哪个在生效时会造成静默混乱——这种 fault 通常只表现为「图像生成结果怪怪的」，找不到清晰失败点。强制 per-provider key 让「我现在用的是哪个 backend」从推理变成可读配置。

**默认宽松 license 过滤，配以严格模式应对没法放致谢的版面。** 网络图片搜索默认允许 CC BY / CC BY-SA 加内联致谢——大部分幻灯片都有视觉空间放一个致谢元素。`--strict-no-attribution` 是给全屏 hero image 和紧凑构图的逃生口，那些场景没法放致谢又不打破设计。NC（CC BY-NC*）和 ND（CC BY-ND*）自动拒绝，因为 PPT Master 的典型产物会用于商用或修改场景；宽松默认 + 这个底线正好对应用户实际想要的 fail-mode。

**Manifest-first 获取。** 流水线内的 AI 图片生成永远先写 `images/image_prompts.json`，并渲染旁路 `image_prompts.md`，哪怕只有一张图。`image_gen.py "prompt"` 这种位置参数形式只保留给一次性调试，因为它没有 manifest / sidecar 审计轨迹。网络图片获取也类似：多行 web 资源写入 `images/image_queries.json` 批量执行，并用 `image_sources.json` 追踪来源和致谢信息。

**图片执行路径以 Design Spec 为权威。** UI 或聊天中的最终确认都先固化为 `design_spec.md §I` 的 `AI Image Acquisition Path`；Image_Generator 根据该值选择 API、host-native 或 manual，不能在执行阶段重新决定。`image_gen.py --manifest` 只属于 API Path A。当前 CLI 仍保留一个读取 UI `result.json` 的防误调用 guard，用于在该文件明确记录 `host-native` / `manual` 时阻止误跑 Path A；它不是权威来源，不覆盖 chat-only，也不能替代 Design Spec 的路线判断。这是当前代码与上游权威链尚未闭合的实现差异，不能当作正常消费路径。

**相关小插画用一张统一 sheet。** 当 deck 需要三个或更多同风格小插画时，资源计划使用一个 AI illustration sheet 行，再用若干 `slice` 行派生元素，而不是分别生成多张小图。`slice_images.py` 把 sheet 切成具名透明元素，这些派生文件进入 `images/`，随后重跑 `analyze_images.py`，让 Executor 看到真实尺寸。这既是成本规则，也是风格一致性规则：一张 sheet 会强迫这些小元素来自同一种视觉手法。

**Executor 前必须进入终态。** 需要获取的资源行必须落到 `Generated`、`Sourced` 或 `Needs-Manual`；`Pending` 和 `Failed` 不能漏进 Executor。`Needs-Manual` 可以作为已知占位 / 依赖继续进入 SVG 生成，但 Step 7 会在最终导出前重新检查必需文件是否已经存在。

**开发期外部引用，下游分叉成预览与原生导出两套嵌入策略。** 在 `svg_output/` 里编辑时，图片是外部文件引用——快速迭代、单点替换。随后分成两种表达：`svg_final/` 对普通位图和受支持的 SVG 资源执行 Base64 内联，EMF/WMF 则保留外部引用供 native PPTX passthrough；个别资源内联失败会计入处理错误，但不会回写作者源或让 finalizer 整体失败。native PPTX 则把位图或 Office vector 复制进 PPTX 的 media 文件夹，用 `<a:srcRect>` 表达受支持的位图裁剪。分叉的理由是职责不同：前者服务视觉预览，后者服务项目转换器生成的可编辑 DrawingML。`svg_final/` 不是无条件脱离项目资产即可搬运的交换格式，也不作为 PowerPoint 手工“转换为形状”的兼容源。

**一份渲染锁、继承 PPT 色彩锚点、逐图确定构图。** 当 deck 包含 AI 生成图片时，Stage 2 会在每套成套设计方向中确认 deck 级 `rendering`。图片颜色不再形成第二次用户决策：Image_Generator 从 `spec_lock.md colors` 的核心 HEX 角色出发，再结合完整 Design Spec 与每项资源按用途推导的 `type` 或 hero-page 构图。渲染可以在不改变核心角色语义的前提下，按上下文派生色阶、材质色、明暗过渡与氛围色；不得用一套无关的图片专属调色替换 deck 身份。重复使用的派生色可以提升为具名 lock 角色。

---

## 图文版式：Primary 主结构 + Modifier 修饰层

「图片**怎么放上幻灯片**」的词表（完整词汇在 [`references/image-layout-patterns.md`](../../skills/ppt-master/references/image-layout-patterns.md)）把 81 条稳定编号技法拆成两层、自由组合：

- **Primary 主结构**（容器布局 / 图作画布 + 原生覆盖 / 多图组合）—— 页面的骨架。一页可一个也可多个；跨 Primary 的组合，如「侧边对比 + 图作画布的注解卡」，是合规的。
- **Modifier 修饰层**（非矩形裁剪 / 遮罩与叠加 / 纹理 / 特殊技法）—— 装饰层。一页可叠任意多个，附着在 Primary 之上。

**为什么显式允许复合，而不设「一页一个 Primary」配额。** 这份词表用于扩展构图选择，不是层数指标。一页可以由一个或多个 Primary 构成，并按需要叠加任意数量的 Modifier；每一层都必须对当前叙事或视觉层级有贡献。需要警惕的是整套 deck 反复退化为裸的 `#2` / `#3` / `#5` / `#6` 且完全不使用 Modifier，而不是要求每一页都必须复合。

**为什么物理拆分两层，而不是只打标签。** 词表被重排成「Primary 全部在前，Modifier 全部在后」——Strategist 或 Executor 读一次目录，就能从结构上内化「两层」心智模型。编号是稳定 id（`#38` 永远是「图作画布 + 注解卡」，不论它在文件里的物理位置），所以 `spec_lock.md`、`design_spec.md §VIII`、历史 executor 输出、过往示例里所有 `#<id>` 引用照样解析。

**为什么组合走 Strategist 资源列表，不只交给 Executor 临场发挥。** `§VIII 图片资源列表` 的 `Layout pattern` 列接受 `#<id> + #<id> ...` 表达式——Primary id 加可选 Modifier id；`Crop Policy` 则记录 `adaptive` 或 `no-crop`。Strategist 会在 SVG 生成前同时选定语义构图和信息完整性边界，并通过 lock 投影让两者在 session 重入后继续存在。Executor 负责实现方式，而不是重新选型：它可以根据真实图片比例和内容层级调整所选 pattern 的尺寸、位置、流向与权重；`adaptive` 行既可完整显示，也可安全裁剪。若要更换 pattern 或改变裁剪策略，必须先更新 Design Spec。

**为什么真正的硬约束留在上游。** 跨切的 SVG 创作与 PPTX 兼容性例外属于 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 路由的权威集。版式词表只指向该路由，不再复述合同；每条规则仍只有一个所属模块，词表里也不会留下过期副本。

---

## 项目规范化 SVG 与兼容性边界

SVG 与 DrawingML 的表达模型并不等价，因此主编译路径不把“浏览器可以渲染”视为“项目可以导出”。只有在 [`references/shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 路由到的适用模块中登记了项目规范表达或显式兼容形式，并且拥有确定 DrawingML 映射的词汇，才属于可接受输入。该拆分权威集负责语法、结构、单位、metadata、兼容别名、保真度和拒绝条件；本架构文档只定义分层原则，不复制具体规则。

**为什么本地复用是编译期复用，不是 PowerPoint 保留对象。** 接受的创作形式由权威合同定义、共享校验器执行。校验通过后，流水线会递归实体化引用子树并重写克隆局部 ID 后再导出；PPTX 回导因此只返回展开后的原语，不重建创作期复用图。

值得在架构层标记的理由：

- **为什么需要封闭映射，而不是默认接受普通 SVG。** 项目规范化 SVG 是编译器中间语言，不是浏览器兼容层。新增元素、属性或取值必须同时补齐导入语义、导出映射、校验规则和回归验证；未登记能力默认不进入主编译路径。
- **为什么兼容输入不等于创作许可。** 已登记的历史别名可以由转换器确定性归一化，并由 Checker 给出非阻塞 warning；提示词、模板和示例仍只生成项目规范写法。兼容面只能服务迁移和人工输入，不能反向扩大生成语法。
- **为什么 warning 可以放过。** warning 只表示合法输出前提下的推荐写法、确定性归一化、已知保真度下降或视觉质量风险。它不改变页面语义，不要求 Executor 回改，也不阻断发布；如果某项必须修正才能交付，它就应被定义为 error。
- **为什么是经验性，不是从规范推导。** 兼容性边界从真实的 PPT 导出失败长出来，不是读 OOXML 规范推导出来的。有些理论上能表达的效果跨 PowerPoint 版本仍不可靠，因此合同反映的是实际能交付的子集。
- **XML 良构性仍是前置条件。** SVG 一旦不是合法 XML，尚未进入 DrawingML 兼容性阶段就会失败。接受的创作形式集中在权威合同中，避免架构与提示文档分别维护后发生漂移。
- **兼容性校验在后处理之前执行。** `svg_quality_checker.py` 在 `svg_output/` 上执行；后处理会重写 SVG，可能掩盖源级别违规。阻断性 error 由 Executor 重新写，warning 不触发回改。Generate 路线只允许在 final Checker 达到 0 error 后进入导出；转换器不重跑完整 Checker，而是独立校验编译映射、ZIP、页数和 package 结构，并把前置质量报告的阶段、阻塞计数与 SVG 源指纹写入 postflight。

---

## 质量门

**为什么需要这道检查器。** LLM 生成的 SVG 不是确定性的——兼容性违规会在长 deck 中悄悄混入，只在 `svg_to_pptx` 中途崩或 PowerPoint 静默丢元素时才暴露。检查器把「PowerPoint 在第 14 页导出失败」转化为「第 14 页违反 SVG 兼容性合同」，诊断速度提升一个数量级——这正是让长 deck 在经济上可迭代的关键。

**为什么放在后处理之前，而不是之后。** 后处理会重写 SVG（图标嵌入、图片内联），会掩盖源级别违规。直接读 `svg_output/` 抓的是 Executor 的实际输出，先于任何可能掩盖 bug 的清理动作。

**为什么有 first-page 与 final 两道检查。** P01 gate 把第一张页面当作方法样本：先区分 method-level、page-local 与未覆盖能力，完整审阅该轮 issue set，再在合并修复循环中消除全部 blocking error，并处理选定的 advisory warning。通过后，P02 到末页连续生成且不插入 checker；final gate 才对完整作者源做发布前检查。前者校准方法，后者验证全集，不能互相替代。

**严重性模型：error 阻塞、warning 不阻塞，且有意没有 auto-fix。** 严重性不按“是否符合推荐写法”划分，而按“能否确定、合法地映射”划分：

| 严重性 | 判定条件 | 流水线行为 |
|---|---|---|
| `error` | 结构合同被破坏；输入无映射或有歧义；必要 metadata 缺失；数值非法；转换后可能违反 DrawingML / PPTX 约束；或可能导致 PowerPoint 修复文件 | Executor 必须重写并重新校验；Generate 路线不得在 final 报告仍有阻塞错误时进入导出。若导出器读到带阻塞错误的 final 报告，postflight 标记 `quality_gate=failed`，该产物不得被声明为成功交付 |
| `warning` | 已有唯一、安全、合法的转换结果，但输入不是项目规范写法，或存在已知的确定性归一化、保真度下降、视觉质量风险 | 记录诊断后允许发布；不要求逐条确认或强制回改 |

质量门沿用设计哲学中定义的三层职责。这里有意不提供 auto-fix：机械修补可能静默覆盖有效的设计意图，也可能交付一个更差的页面。

**当前实现边界。** `svg_to_pptx.py` 会先生成 PPTX，再写 postflight；`quality_gate=failed` 会得到失败报告，但这一状态目前不会单独让 CLI 返回非零，也不会删除已经生成的文件。缺失、非 final、过期或无法验证的质量报告会以对应 `quality_gate` 出现在回执中，并使报告进入 `passed-with-warnings`；当前 Step 7 允许这类产物在读取回执并披露实质 warning 后完成。因而 PPTX 文件存在或命令退出 `0` 都不等于成功：`failed` 报告绝不能交付，`passed-with-warnings` 则必须结合具体 `quality_gate` 和 warning 判断、披露。导出器尚未把 `quality_gate=failed` 独立收口为非零退出或回滚，这是当前防御缺口，而不是放宽 error 语义。

如果同一种 warning 持续出现在新生成页面中，应优先修正提示词、模板示例或规范说明，使默认输出回到项目规范写法；这属于生成质量问题，不需要把本来安全的兼容输入升级成阻塞错误。反过来，如果实践证明某个 warning 可能产生非法文件或不确定语义，就必须把合同和 Checker 同步升级为 error。

**为什么图表坐标验证挂在同一道 gate。** 图表页面有几何正确性需求（柱高、饼图扇角、坐标轴刻度位置），这些不是结构问题，SVG 合法性规则也抓不到。最自然的捕捉位置就是已经要求 AI 回看自己输出的那道 gate——把「看一眼你刚生成的东西然后修」的认知上下文打包到一个阶段，比把结构和几何审查分到两轮 review 更高效。

---

## 后处理流水线

> 工程化转换阶段中每一份产物和每一个模块为何存在，删除它会破坏哪些工作流。在考虑简化 `svg_final/` / `finalize_svg.py` / `svg_to_pptx.py` 之前，先读这一节。

### 后处理产物与工作流

后处理与导出阶段严格区分创作源、校验、预览、交付与归档产物。每一份都服务于一种流水线中无法替代的工作流。

| 产物 | 服务的工作流 | 为何无可替代 |
| --- | --- | --- |
| `svg_output/` | 唯一源、手工编辑入口、`update_spec.py`、`svg_quality_checker.py` | 流水线中唯一**手写**而非派生的目录 |
| `svg_final/` | IDE 内即时预览（VSCode/Cursor 直接打开 `.svg`）、浏览器单页预览、手动作为 SVG 图片插入 | `.pptx` 在 IDE 里打不开；`svg_output/` 因图标 / 图片是外部引用，IDE 中渲染不完整。普通资源尽量内联，EMF/WMF 保留外链；PowerPoint 手工“转换为形状”不在支持范围 |
| `exports/<name>_<ts>.pptx`（native） | 默认主交付物——PowerPoint 中以 DrawingML 形状形态可编辑 | 默认 DrawingML 对象模型；原生 Chart/Table 与旁白变体同样可编辑，但拥有不同的对象或播放行为 |
| `validation/svg_quality_report.json` | 机器可读的最终 SVG 门禁 | 把阻断错误、新增提示、原型继承项和来源导入损失分开，并为受检 SVG 字节生成指纹 |
| `validation/<output_stem>.report.json` | 已发布 PPTX 的 postflight 与资源审计 | 记录实际 ZIP/package part 数量；重新检查 ZIP 与正式页数；把内部关系、结构化包、转场和动画如实标为构建期强制校验；只有 SHA-256 指纹与导出输入一致时才接受质量报告关联，同时暴露未解析变量、外部图片和纯通用字体栈 |
| `exports/<name>_<ts>_native_charts_tables.pptx`（需 `--native-charts-and-tables` 显式开启） | 让带 `data-pptx-replace-with` 标记的 SVG 派生形状图表/表格替换为 PowerPoint 原生 Chart/Table 对象 | 带数据源和图表/表格专属控制的对象；默认 DrawingML shape 本身仍可独立编辑 |
| `exports/<name>_<ts>_narrated.pptx`（经 `--recorded-narration` 或 `--narration-audio-dir` 生成） | 嵌入匹配到的旁白音频；完整录制模式可直接服务自动放映与 PowerPoint 视频导出 | `--recorded-narration` 要求每页匹配音频，并写入“时长 + padding”的自动推进；低层 `--narration-audio-dir` 允许部分或零覆盖，只有另加 `--use-narration-timings` 才写自动推进 |
| `exports/<narrated_stem>.mp4`（可选，经 `powerpoint_video.py`） | Windows PowerPoint 2016+ 下保留动画与旁白的视频交付物 | 委托 PowerPoint 原生编码器并等待完成；它是 PPTX 后处理集成，不是第二套 deck 渲染器 |
| `backup/<ts>/svg_output/`（仅默认输出路径；目录创建后复制为 best-effort） | 在不重跑 LLM 的前提下从冻结 SVG 源重建 pptx | 转换成功后先创建备份目录再尝试复制；显式 `-o` 不创建，复制失败不阻断导出，非 quiet 模式打印 warning，postflight 的 `backup_path` 为空，但目录创建失败仍会中断 |

校验 JSON 是冷审计产物，不是常规模型输入。导出器在程序内部读取 SVG 质量报告，并在默认非 quiet 流程打印紧凑的 `[POSTFLIGHT]` 回执，包含状态、质量门结果、Slide 数量、warning 类别计数和产物路径。成功流程只消费该回执，不加载两份完整 JSON；只有失败排查或用户明确要求审计时才定向提取报告字段。

### SVG 预处理器有**两种使用形态**

这是读代码时容易忽略的关键事实。共享清理模块、本地引用展开器和 inline geometry materializer 一方面写盘生成 `svg_final/`，另一方面在 native 转换中以内存形式复用。Checker、编辑器和结构解析器也共享部分几何解释，但不属于本节的产物消费者。

**写盘消费者** —— `finalize_svg.py` 每次运行都把 `svg_output/` → `svg_final/` 写到磁盘一次，同时展开项目图标占位符和合规的本地 `<use>` 引用。`svg_final/` 随后供 IDE / 浏览器视觉预览及手工 SVG 图片插入使用。

**内存消费者** —— native pptx 直接读 `svg_output/`（不经磁盘中转），依次物化作者 SVG 的 inline geometry、展开项目图标占位符、再次物化图标注入的 geometry、展开合规的本地 `<use>`，最后处理定位文本 run：

| 内存调用点 | 预处理器 | native pptx 为何需要 |
| --- | --- | --- |
| `svg_to_pptx/drawingml/converter.py` | `svg_to_pptx.geometry_properties` | inline style 中的几何声明要先物化为 XML 属性；图标展开后需再执行一次 |
| `svg_to_pptx/use_expander.py` | `svg_finalize.embed_icons` | DrawingML 不识别 `<use data-icon="...">`；不展开图标会静默丢失 |
| `svg_to_pptx/use_expander.py` | 静态本地引用展开 | DrawingML 不保留 SVG `<use>` 实例图；合规子树必须实体化并获得实例级独立 ID |
| `svg_to_pptx/tspan_flattener.py` | `svg_finalize.flatten_tspan` | DrawingML 文本块无法在段落中跳位置；`dy` 堆叠的多行 `<tspan>` 会塌成一行，`x` 锚定的 tspan 会跑到错误的列 |

### 各模块消费者一览

| 模块 | 写盘消费者 | 内存消费者 | 删除影响 |
| --- | --- | --- | --- |
| `geometry_properties.py` | `finalize_svg.py` 在复制后及图标展开后调用 | `drawingml/converter.py`；Checker、编辑器与 template structure parser 共享同一解释 | inline style 几何属性无法稳定转为 XML geometry，预览、校验和 native 转换可能产生不同结果 |
| `embed_icons.py` | `finalize_svg` 的 `embed-icons` 步骤（随后展开本地 use） | `svg_to_pptx/use_expander.py` | native pptx 丢失全部图标，`svg_final/` 也失去受支持图标的视觉闭包 |
| `svg_to_pptx/use_expander.py`（本地引用） | `finalize_svg` 的 `embed-icons` 步骤 | native 转换器预检 | finalize/native 导出失去实体化合规本地复用的能力 |
| `flatten_tspan.py` | `finalize_svg` 的 `flatten-text` 步骤 | `svg_to_pptx/tspan_flattener.py` | **native pptx 中 `dy` 堆叠的多行文本塌成一行** |
| `align_embed_images.py` | `finalize_svg` 的 `align-images` 步骤 | — | `svg_final/` 失去图片嵌入 → IDE / 浏览器预览和手工插入的 SVG 图片缺图 |
| `crop_images.py` / `embed_images.py` / `fix_image_aspect.py` | 被 `align_embed_images.py` import | — | `align_embed_images` `ImportError`，整条链路 broken |
| `svg_rect_to_path.py` | — | — | 仅保留为历史诊断工具，不属于 `finalize_svg` 或受支持导出流程；不得据此承诺 PowerPoint 手工“转换为形状”兼容性 |

---

## 直接 OOXML 路由

不是所有 PPTX 相关请求都应该重新生成页面。PPT Master 现在为“原生 deck 本身就是编辑对象”的场景提供直接 OOXML 路由。

`template_fill_pptx.py` 是 `scripts/template_fill_pptx/` 包的薄 CLI 入口。analyzer 抽取带文本槽位、表格、图表和几何信息的 slide library；fill plan 选择源页面并确认替换内容；applier 克隆幻灯片并直接 patch XML parts。这条路线故意绕开 SVG：用户提供 PowerPoint 模板时，通常期望原生母版、占位符、表格和图表继续保持 PowerPoint-native。

`native_enhance_pptx.py` 是已完成 deck 原生增强的稳定入口。它委托 `native_enhance_pptx_core.py`，在项目归档副本上直接 patch PPTX package：讲稿、页面转场、录制旁白媒体、页面计时和相关元数据。旧名称 `native_narration_pptx.py` 仅保留为精简的 CLI 兼容包装器。它的契约是保留：已有内容、布局和格式不重新生成。

这些直接路线会和主流水线共享部分分析原语，但复用深度不同：Template Fill 消费标准 PPTX intake 的 slide library；Native Enhance 只用 `ppt_to_md.py` 理解内容，并从归档 package 生成自己的轻量 `slide_index.json`。两者都不共享 SVG 作者阶段和后处理阶段。这个分离是有意的：SVG 生成是设计合成路径；直接 OOXML 编辑是保留路径。

---

## Native PPTX 转换器内部

`svg_to_pptx.py` 执行设计哲学中定义的最终防线；本节只解释这条受约束编译路线的内部结构。

**为什么是逐元素派发而不是整体翻译。** SVG 的层级模型干净地映射到 DrawingML 的 group / shape / picture 类型——不需要一个全局优化器去重新规划幻灯片。每种形状都有自己窄的翻译器，简单到能单独调试和单元测试。一张幻灯片的最终质量等于这些独立局部转换之和；这个性质在整体翻译下脆弱，在元素派发下稳健。

**为什么导入型与生成型 metadata 分层。** 导入 PPTX 时，完整 SVG 可以携带高级形状所需的 metadata、隐藏 carrier 和预览指纹，因此作为原生载荷后备留在临时分析工作区且保持不可变。`svg_authoring_view.py` 生成模板创建所用的可编辑 IR：轻量 SVG 通过文档内 source ref 标识对象，`authoring_manifest.json` 只记录路径与初始 hash，不重复保存原始载荷。`standard` / `fidelity` 创作项目规范化 SVG，只有精确匹配已登记 preset 时才使用 compact authored-preset 组。Mirror 从 IR 物化通过校验的模板，只为未改且 hash 匹配的 Slide-local/slot ref 重新接入转换器已支持的 metadata；固定结构层保持直接原子，不支持或已修改的对象保留当前 SVG fallback，IR 专用 ref 不进入最终模板 SVG。

**为什么只有一条 PPTX 编译路线。** Native 导出把作者 SVG 中受支持的元素逐个翻译成 DrawingML 形状。常规 deck 路线读取 `svg_output/`；用户需要时，create-template 对通过校验的模板原型调用同一 structured 编译器，生成 `exports/<id>_template_preview.pptx` 作为审阅证据。项目不会把整页 SVG 媒体或另一套位图渲染打包成第二类 PPTX。`svg_final/` 仍由常规 deck 的强制后处理生成，但只承担派生视觉预览和 SVG 图片插入，不为 PowerPoint 手工“转换为形状”提供兼容兜底。

**为什么结构化复用路线必须在视觉生成前确定结构。** Master 和 Layout 不是后处理阶段才发现的结果。使用 `template_reuse_scope: mirror|layout` 时，Strategist 在 SVG 生成前写出唯一 Master/Layout 定义和完整页面分配；Executor 在构图时同步写入这些身份、固定原子元素和槽位，导出器只编译声明。`template_reuse_scope: style`、自由设计与 brand-only deck 做的是相反的取舍：保持 `mode: flat`，所有对象留在 Slide 本地，不写任何结构 metadata，导出时只获得一个属于本项目的干净 Master/Blank-Layout 壳。旧输入可以为新的 `create-template` 工作区提供参考，但不存在原地升级结构的路线；两种生成模式都不会触发启发式 Master/Layout 提升或 placeholder 推断。

**为什么 Master/Layout 视觉必须原子化。** 一个 Master 或固定 Layout 对象必须是根节点的直接子元素。导入 PPTX 时，group 的 transform、opacity、style 和 z-order 会下推到各个原子对象。这个选择有意放弃来源 group 的整体编辑层级，换取简单、可比较、可确定重建的结构归属，避免嵌套结构歧义。

**为什么 Layout 槽位使用 group。** 一个可复用槽位是顶层 `<g>`，携带语义类型和设计区域 bounds。普通槽位恰好包含一个兼容 carrier；导出时 carrier 被解包并绑定成真实 Slide placeholder。无法由单一 placeholder 表示的复合 `object` 区域走显式 proxy 降级：可见 group 保持普通 Slide 对象，隐藏透明 placeholder 负责 PowerPoint 绑定。Layout 也可以零槽，因此纯视觉页面无需制造假全页槽位。

**为什么可复用 bounds 是设计区域，不是量出来的文本框。** bounds 来自安全区、分栏、面板内框或图片框，而不是字形宽度、行数或当前内容紧包围盒。当前 Slide 保留自己的 carrier 几何，因此只要语义构图相同，4:6、3:7、5:5 的实例都可复用同一 Layout。文本长度不会意外拆分或改变可复用合同。

**为什么内部应用计划保留两个字段。** Strategist 推导 `template_reuse_scope`，记录字面镜像复用、结构化版式复用或 flat 风格参考；structured 计划再推导 `template_adherence: strict|adaptive`。`page_layouts` 记录完整创作原型，`pptx_masters` / `pptx_layouts` 记录唯一可复用定义，`page_pptx_layouts` 记录页面分配。strict 保持声明的原型合同；adaptive 保持原型 Master，只有固定 Layout 原子或槽位 topology/bounds 改变时，Strategist 才可声明新 Layout。若制作过程暴露出这一需求，执行必须退回上游，待 Strategist 更新、回读并校验定义与分配后才能继续；导出器不会事后推断。这些是导出器内部值，不是用户确认选项。模板定义即使暂时没有页面使用，也能注册进最终文件。layout 的皮肤由项目控制；mirror 还要保持字面视觉与文字节点拓扑。`style` 不带 adherence 或结构 mapping。

**为什么显式版式把文字默认值分在 Master 与 Layout 两层。** Flat 与 structured 导出都会把锁定的 title 字号和确定性的九级 body 层级写入 Master 文本默认值，同时保留原有缩进与项目符号设置；在 structured 路线上，每个 Layout 文字槽位还会把 carrier 首个 run 的字号写入一级默认值，同时保留提示文字的直接字号。这样，插入或重置 placeholder 时仍能继承 Layout 特定尺度，而生成 Slide 上的直接 run 不变。

**为什么 structured 输出要在发布前回读。** 元数据预检不能证明 package 序列化保留了所有 relationship 与注册信息。导出器会重新打开临时 PPTX，把已发布 Slide 与完整 Master/Layout roster 分开校验，包括没有任何 Slide 使用的定义；同时核对 Presentation → Master → Layout → Slide 注册链、物理 part/content-type roster、选择器身份、固定对象顺序、placeholder 类型/有效索引/bounds、carrier 绑定、隐藏 proxy 与零槽 Layout，只有通过后才发布。

**为什么 Create Layout / Create Deck 分为创作模式和保留模式。** `pptx_template_import.py` 输出分层 Master/Layout/Slide 参考和 native 结构事实。`standard` / `fidelity` 把这些素材和视觉当参考，再按照确认后的可复用行为创作新拓扑。Mirror 则把已验证的来源 roster 与拓扑一对一物化到新工作区，只允许显式 structured 合同要求的机械归一化，不补造缺失事实。原始 PPTX 保持为不可变分析证据，不成为最终模板依赖。Create Brand 没有结构复制策略。

**为什么 create-template 在两种范围都使用同一工作区路由。** `create-template` 仍以写入索引的 `library` 为默认，也可写入已初始化项目。两种根目录都要求 `templates/`；`images/`、`icons/` 和按需生成的 `exports/` 只有存在真实内容时才出现，已有 SVG 素材的引用规则也一致。因此工作区可直接迁移和复用，不需要全局库专用 package 分支或缩减的项目分支。唯一范围差异是全局索引注册；两种范围共享同一可迁移工作区合同，但只有 Layout / Deck 拥有 structured SVG 合同，Brand 仍是 identity-only。

**为什么模板 SVG 保持完整却仍能编译成原生结构。** 模板 SVG 会重复携带继承的 Master/Layout 视觉和示例 Slide 内容，因此可独立打开。生成时由 `page_layouts` 选择该原型，输出 SVG 仍保持视觉闭包。导出器移除重复继承原子、生成真实 Master/Layout part，并把槽位 carrier 与 Slide-local 内容留在 Slide。

**为什么 PowerPoint 原生 Chart/Table 重建使用显式替换 marker，而不是自动替换对象。** 独立的 `pptx_to_svg.py` 导入器只为已验证的表格 / 图表子集输出可见 SVG fallback、`data-pptx-replace-with` 与 `<metadata type="application/json">`。生成型 deck 只在 Strategist 将 §IX 页面块标为 `Native-ready: yes` 时准备这组内容；§VII 只保存正向 catalog reference，catalog marker 只是能力示例，不替项目做决策。父组 marker 决定 payload schema；普通 shape 与 connector 不使用该合同。表格导入覆盖精确的物理行列 topology、slave 为空的规范矩形 merge、安全的 solid/no-fill 逐边 border、纯文本多段落，以及封闭的 run 级富文本段落。富文本段落包含非空 `runs`；每个 run 必须有 `text`，并且只能使用 `bold`、`italic`、`underline`、`strike`、`color`、`font_size`、单一 `font_family`、`lang` 和 `alt_lang`。不含非空 `effectLst` / `effectDag` 的来源展示型 run XML 会归一化到该 schema；表格单元格 run 效果则会禁用原生替换，并添加阻塞效果诊断。带 relationship 的文本、扩展节点、换行、字段、tab、项目符号、破损文本 topology、非规范 merge、不安全 border 与非纯色填充仍保持 fallback-only。表格样式 `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}` 的规范化 fallback 会解析 `wholeTbl`、`firstRow`、横向带状行、主题颜色 / 字体和直接格式覆盖；这不代表完整 built-in/custom style registry。

受支持的柱 / 条 / 折线 / 面积、饼 / 圆环、散点 / 气泡图在没有 baked preview 时会生成确定性、可读的 SVG fallback，并标记 `data-pptx-fallback-kind="normalized"`。导入器还覆盖已验证的柱 / 折线 / 面积组合图、规范四系列 OHLC stock、数值日期轴面积图、采用封闭 `axes.x` / `axes.y` 合同的散点 / 气泡图、radar、安全的 `of_pie` `serLines`、坐标轴 / 标题 / 图例归一化，以及有界的柱 / 条图 gap/overlap 场景。`gapWidth` 只接受 `0..500` 内的单个整数，`overlap` 只接受 `-100..100` 内的单个整数；这两个表现字段在 native 输出中有意归一化，非法、重复或越界输入 fail closed。组合图可保留主 / 次 plot 各自的 category cache 与 workbook range。XY 导入根据各系列一致的有效 line/marker/smooth 状态推导 `scatter_style`。封闭的 category/value 与 XY 轴合同为 native read-back 保留 kind、position、visibility、label position、number format、min/max/major unit、reverse 和 major gridlines；规范化 XY fallback 只消费两个 `major_gridlines` 开关。

ChartEx 导入被有意限制为 7 个已验证数据模型：`treemap`、`sunburst`、`histogram`、`pareto`、`box_whisker`、`waterfall` 与 `funnel`。其受支持的层级 / 分类 / 数值 / 系列 / 小计数据 topology 可经 native 输出再导入回读。数值 cache 必须非空且有限，count/index 必须是规范非负整数，并满足精确连续的 point topology。来源 ChartEx 的样式、坐标轴、标签与 binning 可能归一化；这不代表任意 ChartEx 导入或表现层保真。C4/C5 不扩展 normalized renderer，因此 renderer 外的有效 active 类型在没有源 preview 时仍使用 `data-pptx-fallback-kind="placeholder"`。完整 `AxisSpec`、任意 ChartEx 家族、任意富文本 OOXML、旋转 / 翻转 / 3D 图表、未验证的 combo/stock/date-axis 变体及其他未建模语义仍不在 active 导入子集内。native replacement 仍可能归一化 payload 外的表现细节，并保留数据模型优先 warning。默认导出把 fallback 子元素作为可编辑 DrawingML shape；只有 `--native-charts-and-tables` 才启用带数据源和对象专属编辑模型的 PowerPoint 原生 Chart/Table。每个 active 导入 marker 都带有 `data-pptx-import-source="pptx"` 与 `data-pptx-fallback-sha256`：可见 fallback、可达 SVG definition/reference 或 marker transform 变更后，native replacement 会 fail，而不是丢弃 SVG 编辑；仍保留导入来源标记但没有 hash 的旧导入 marker 兼容并给出 warning。生成型创作会同时省略导入来源和静态 baseline，且不产生 warning。该 importer/exporter 组合只用于重建，不替代 `template-fill-pptx` 或 `native-enhance-pptx` 的保留型路线。

---

## 动画与转场模型

值得讲的设计选择是动画**锚点**，不是效果列表。

**为什么把入场动画锚在顶层 `<g>` group。** PowerPoint 的动画时序基于形状 ID——每个被动画的对象需要稳定的 shape ID。给单个原语做动画会产出每页 30+ 个分别飞入的原子（动感泛滥），只给整页做动画又损失视觉叙事。顶层 group 是自然粒度：Executor 本来就被强制要求用 `<g id="...">` 标记逻辑内容块，而这些块正是观众读作「一个东西到达」的单位——动画对齐了已有的逻辑结构，而不是另立门户。

**为什么页面结构自动跳过。** 顶层 group 只要带有 `data-pptx-layer`，就被视为不可动画的结构层；当前实现也把任何显式 `data-pptx-placeholder` 视为静态页框，`background` / `header` / `footer` / `decoration` / `watermark` / `page-number` 等 role 再补齐其余页面 chrome。ID token 回退不是按整份 SVG 启停，而是仅对同时缺少 layer、role 和 placeholder 的单个顶层 group 生效，因此新旧标记混合的 SVG 仍可能只在未标记 group 上使用 legacy ID 判断。另有一个有界的原语兼容回退：只有整页没有顶层 group、尚未找到任何动画目标且根原语候选为 1–8 个时，才把这些根原语作为锚点。这是当前扫描器的真实作用域；动画 reference 中“仅 marker-free legacy SVG”这一整页口径仍需另行与实现对齐。

**为什么对象级动画用 sidecar，而不是 SVG 属性。** SVG 继续作为静态视觉源。自定义 PPTX 动画属于导出策略，所以对象级覆盖放在可选的 `animations.json`，按 slide stem 和顶层 group id 关联。这样不会把 PowerPoint 专用元数据塞进 SVG，同时仍能在默认全局动画不够用时调整顺序、效果、延迟和时长。

**为什么录制旁白让自动推进时长跟着片段时长走。** 录制旁白模式面向视频导出，视频里没有演讲者去点击。该模式会逐页探测音频实际时长，并把自动推进设置为“音频时长 + `--narration-padding`”；padding 默认是 0.5 秒，用于避免音频尾部被切断。它不使用估算朗读速度或固定每页时长。

**为什么录制旁白拒绝 on-click 对象动画。** PowerPoint 可以在真实排练时记录点击计时，但 PPT Master 不合成对象级点击事件。录制旁白路径只写页面级音频和页面自动推进计时，所以单击触发的对象入场会让导出依赖额外的 PowerPoint 人工排练。使用 `--recorded-narration` 导出的 deck 必须采用无点击入场（`after-previous` 或 `with-previous`）。

**为什么原生视频导出保持独立命令。** 音频合成和 PPTX 打包属于跨平台项目操作；PowerPoint 视频编码则是 Windows 桌面集成。`powerpoint_video.py` 接收最终带旁白 PPTX，调用 `CreateVideo` 并轮询 `CreateVideoStatus`，对调用方呈现同步结果，同时避免把 Office 自动化耦合进 TTS backend。

---

## 维护边界：不要合并什么

下面这些“简化”都有明确代价。除非要有意识地重新设计周边架构，否则应把它们视作反向契约。

| 不要合并或新增 | 原因 |
|---|---|
| 不要把模板名或风格短语模糊匹配到库路径 | Step 3 必须确定性触发；选错模板比自由设计更难恢复 |
| 不要把原生 PPTX 模板当作 Step 3 模板 | 作为模板 / 页面壳时应走原生克隆与填充；作为来源、1:1 beautify 或可重构材料时分别走对应 Generate 边界，而不是把 PPTX 直接交给 Step 3 |
| 不要把 `template-fill-pptx`、`beautify-pptx`、`native-enhance-pptx` 合成一个“PPTX 优化”路线 | 三者的保留契约不同：原生填充、1:1 重排、直接增强是三种操作 |
| 不要用脚本批量生成 Executor SVG 页面 | 跨页设计判断依赖主代理逐页连续创作 |
| 不要把 `image_analysis.csv` 当持久缓存 | `images/` 是实时工作目录；事实必须按需重算 |
| 不要让 `svg_final/` 成为 native PPTX 默认输入 | `svg_final/` 为视觉预览而重写资源，native 转换需要 `svg_output/` 的高保真语义 |
| 不要把 `svg_final/` 当作可还原形状或无外部依赖的交换格式 | 它服务视觉预览和 SVG 图片插入，但 EMF/WMF 保留外链例外；PowerPoint 手工“转换为形状”不在支持范围 |
| 不要默认开启对象级入场动画 | 页面转场是默认；对象 build 是显式导出策略 |
| 不要把 visual review、旁白、图表校准或动画定制默认塞进每次运行 | 这些工作流触发范围窄，且有额外依赖 |
| 不要用文件复制替代 `finalize_svg.py` | finalize 会嵌入图标 / 图片、展开特殊文本并准备预览产物 |
| 不要在主流水线里把 `analysis/<stem>.slide_library.json` 当作第二份图表数值来源 | Markdown 拥有内容数值；除非直接 PPTX 工作流接管，否则 intake 图表 / 表格条目只是结构摘要 |

---

## 顶层路线与支撑文档

[`workflows/index.md`](../../skills/ppt-master/workflows/index.md) 是仅供维护者使用的目录，不进入任务加载链。运行时路线选择以 [`workflows/routing.md`](../../skills/ppt-master/workflows/routing.md) 为权威。PPT Master 只有四条顶层产物路线：Generate PPTX、Create Template、Fill Native PPTX、Enhance Native PPTX。用户请求只能进入其中一条；任何支撑文档都不与它们竞争。

支撑文件保持拆分，只是为了收紧路线合同，并在需要时加载可选上下文：

| 分类 | 文档 | 归属路线 |
|---|---|---|
| 生成 profile | `beautify-pptx` | Generate PPTX；逐字措辞、页数与页序 1:1 冻结 |
| 模板子工作流 | `create-brand`、`create-layout`、`create-deck` | Create Template 在“仅身份 / 品牌中立且应用中立的结构 / 应用契约与身份结构一体化”中只分派一个 |
| 模板输入阶段 | `apply-template-workspace` | Generate PPTX Step 3；只在显式工作区根目录触发时加载 |
| 生成阶段 | `topic-research`、`resume-execute`、`refine-spec`、`verify-charts`、`visual-review`、`live-preview`、`customize-animations` | Generate PPTX 中各自定义的 intake、planning、editing、quality 或 post-processing 节点 |
| 共享阶段 | `generate-audio` | Generate PPTX 后处理，或 Enhance Native PPTX 的旁白集成 |
| 治理文档 | `failure-recovery` | 四条顶层路线的全局停止 / 继续规则；Generate PPTX 的具体故障矩阵与续跑入口 |

这种分类是职责边界，不是文件命名偏好。只有出现不同的产物生命周期和修改模型时，才新增顶层路线；Create Template 内按模板类型区分的执行归入子工作流，路线内的可选行为归入 profile 或 stage，跨路线政策归入 governance。
