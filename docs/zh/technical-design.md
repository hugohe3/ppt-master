# 技术路线

[English](../technical-design.md) | [中文](./technical-design.md)

---

## 设计哲学 —— AI 是你的设计师，不是完工师

生成的 PPTX 是一份**设计稿**，而非成品。把它理解成建筑师的效果图：AI 负责视觉设计、排版布局和内容结构，交付给你一个高质量的起点。要想获得真正精良的成品，**需要你自己在 PowerPoint 里做精装修**：换掉形状、细化图表、调整配色、把占位图形替换成原生对象。这个工具的目标是消除 90% 的从零开始的工作量，而不是替代人在最后一公里的判断。不要指望 AI 一遍搞定所有——好的演示文稿从来不是这样做出来的。

**工具的上限是你的上限。** PPT Master 放大的是你已有的能力——你有设计感和内容判断力，它帮你快速落地；你不知道一个好的演示文稿应该长什么样，它也没法替你知道。输出的质量，归根结底是你自身品味与判断力的映射。

### SVG 是项目的规范中间语言

PPT Master 不以“任意 SVG 都能转成 PPTX”为目标。`svg_output/` 使用的是**项目规范化 SVG 中间语言**：它借用 SVG 的 XML 语法和二维图形模型，但允许的元素、属性、单位、metadata、结构合同与 DrawingML 映射都由项目规范封闭定义。这里的方向是 **SVG 适应 PPT Master，而不是 PPT Master 追随整个 SVG 标准扩张**。

这套中间语言区分三种输入状态：

| 状态 | 定义 | 处理方式 |
|---|---|---|
| 规范创作输入 | 提示词、模板和示例应生成的唯一推荐表达 | 按注册映射校验和编译，不因表达别名产生 warning |
| 兼容输入 | 已明确登记、可确定且安全归一化的历史或人工写法 | Checker 给出非阻塞 warning；转换器确定性归一化后编译，不把别名反向扩散到提示词 |
| 非法或不支持输入 | 缺少映射、存在歧义、破坏结构合同，或可能生成非法 DrawingML / PPTX 的表达 | Checker 或转换器报 error 并停止发布 |

例如，项目字号统一采用 SVG px 语义，规范写法是有限的无单位数值（如 `font-size="24"`）；其他单位只有被兼容合同明确登记且能够确定性换算时才可能作为兼容输入，不能成为生成提示词的新写法。兼容读取是一条受控迁移边界，不是放宽创作语言的理由。

三层职责必须分开，不能用其中一层替代另一层：

| 层级 | 单一职责 | 不承担的职责 |
|---|---|---|
| 提示词、模板与示例 | 精确表达项目规范写法，从源头减少偏差和 warning | 不作为正确性或安全边界 |
| `svg_quality_checker.py` | 在作者状态上执行项目合同；error 阻塞，非阻塞 warning 放行 | 不静默改写页面，也不猜测设计意图 |
| `svg_to_pptx.py` | 对所有调用路径防御校验；归一化已登记兼容形式；阻止已知非法 package 发布 | 不承诺转换任意 SVG，不用默认值掩盖未知或歧义输入 |

---

## 系统架构

```
用户输入 (PDF/DOCX/XLSX/PPTX/URL/Markdown/主题文本)
    ↓
[源内容转换] → source_to_md/pdf_to_md.py / doc_to_md.py / excel_to_md.py / ppt_to_md.py / web_to_md.py
    ├── sources/ 内容型文件是内容契约
    └── PPTX intake 写入 analysis/<stem>.identity.json、<stem>.slide_library.json、source_profile.json
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[模板 / 品牌 / 布局（可选）] — 默认跳过，直接自由设计
    仅在用户提供明确的 Layout/Deck 工作区根目录或直接 Brand/旧包路径时触发
    原生 PPTX 模板请求进入 template-fill；可复用 SVG 模板需先通过 create-template 创建
    ↓
[Strategist] 策略师 - 三阶段策略师确认与设计规范 → design_spec.md + spec_lock.md
    ↓
[Image Acquisition] 图片获取（当资源列表中有需要 AI 生成、网络搜索或切片的图片时）
    ↓
[Executor] 执行师
    ├── 生成开始前启动 live preview，并在生成期间保持可用
    ├── 视觉构建：按页顺序连续生成项目规范化 SVG 页面 → svg_output/
    ├── [Quality Check] svg_quality_checker.py（强制通过，0 错误；warning 非阻塞）
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
    └── *.svg                                           ← 强制生成的自包含视觉预览，可手动作为 SVG 图片插入

    exports/
    ├── presentation_<timestamp>.pptx                ← 原生形状版（DrawingML）— 唯一 PPTX 生成路线的标准文件
    ├── presentation_<timestamp>_native_charts_tables.pptx  ← 同一路线的 PowerPoint 原生 Chart/Table 替换变体（加 --native-charts-and-tables 时生成）
    └── presentation_<timestamp>_narrated.pptx       ← 同一路线的旁白变体（加 --recorded-narration audio 时生成）

    # 默认流程（未指定 -o）始终写入
    backup/<timestamp>/
    └── svg_output/                            ← Executor 原始 SVG 备份（重跑 finalize_svg → svg_to_pptx 即可重建 pptx）
```

### SVG 是受约束的页面设计语言

凡是通过 SVG 创作或重新设计页面的工作流，`svg_output/` 都是完整的页面设计权威，但这里的 SVG 专指通过项目合同校验的项目规范化 SVG，而不是任意浏览器可渲染的 SVG。最终幻灯片中应出现的文字、图片、形状、图示、图表 / 表格 fallback、背景和模板派生布局元素，都必须已经存在于对应页面 SVG 中，或被它明确引用。模板、`design_spec.md` 和 `spec_lock.md` 负责指导 SVG 创作；导出器不能把它们当成第二层画面来源，在导出阶段补入 SVG 缺失的页面内容。

最小语义标记不会削弱这条闭包。自由设计与 brand-only 页面使用 `pptx_structure.mode: flat`：所有已表达对象保持 Slide 本地，不创作任何 Master/Layout 身份、分层或 placeholder metadata。导出器根据当前配色/字体 lock 生成一个属于本项目的干净 Master 和一个 Blank Layout，删除 title/body 等内置内容占位符与未使用的内置 Layout，仅保留标准日期、页脚和页码能力钩子，但不提升任何 Slide 内容。结构化 deck/layout 模板路线上，每张新页面从第一版 SVG 起就声明 Master/Layout 身份。固定 Master/Layout 视觉是根节点直接原子元素；可复用内容槽位是顶层 group，带显式设计区域 bounds 和一个兼容 carrier；复合 `object` 区域走显式 proxy 降级，Layout 也允许零槽。`data-pptx-role` 只补充专用 metadata 尚未表达的少量页面框架、package 或动画行为。结构合同缺失或使用旧形态的 legacy structured/template 项目必须先运行 `restore-pptx-structure`；flat 项目是有意不带 mapping，不算 legacy。导出器不做 Master/Layout 结构或 placeholder 推断。

| 领域 | 权威来源 |
|---|---|
| SVG 创作路线中的可见页面内容与布局 | `svg_output/` 中的最终页面 SVG |
| 项目规范化 SVG 的语法、兼容形式与映射边界 | [`references/shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) |
| Master/Layout/Slide 打包与原生对象映射 | SVG 到 PPTX 的翻译；可以重组 SVG 已表达的内容，但不能创造新的可见内容 |
| 动画、转场、讲稿和旁白 | 各自的 sidecar / 资源与 PPTX package 后处理 |
| 直接原生 PPTX 编辑 | 所选原生工作流自己的 PPTX / OOXML 契约 |

这是一条“页面设计闭包”规则，不代表 SVG 要描述完整 PPTX package。相关验收是：完成的页面 SVG 能重建对应幻灯片的可见设计；不要求仅凭 SVG 重建讲稿、音频、计时、relationships 或直接原生编辑结果。

`svg_final/` 不改变这条边界。Step 7 必须从 `svg_output/` 派生这组自包含视觉预览，供 IDE、浏览器查看，也可由用户手动作为 SVG 图片插入 PowerPoint；它不是第二条 PPTX 导出路线，也不承担 PowerPoint 手工“转换为形状”的兼容性。需要可编辑形状时，唯一受支持的路径是项目转换器把 `svg_output/` 翻译为原生 DrawingML PPTX。

以下直接 PPTX 工作流会有意绕过 SVG 创作路线，并继续保持独立：

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
| 只有主题，没有源文件或足够源文本 | 先走 `topic-research`，再进入主流水线 | 网络 / 来源收集是前置步骤 |
| 有源文件或对话文本，deck 结构可以重想 | 主 SVG 流水线 | Strategist 可以拆分、合并、删除、重排和重设计 |
| PPTX 作为源材料，用户允许重构故事和页结构 | `ppt_to_md` + `pptx_intake`，再走主 SVG 流水线 | PPTX 身份和几何是事实与候选，不是复刻约束 |
| 原生 PPTX 模板 + 新材料 / 新主题 | `template-fill-pptx` | 克隆并填充原生页面；不生成 SVG |
| 现有 PPTX，页数 / 页序 / 措辞 1:1 保留，只改善排版 | `beautify-pptx` | 通过 SVG 重新生成；内容和分页锁定 |
| 已完成 PPTX，保持内容 / 布局稳定，只加讲稿、音频、计时、转场 | `native-enhance-pptx` | 直接 OOXML patch；不重新设计 |
| 用户想从 PPTX 或设计参考构建可复用模板工作区 | `create-template` 或 `create-brand` | 输出后续能触发 Step 3 的工作区根目录；create-template 可按需导出审阅 PPTX |
| 用户提供明确模板路径 | 主 SVG 流水线 Step 3 | 当前 Brand/Layout/Deck 工作区均解析 `templates/design_spec.md`；兼容的旧式平铺包解析根目录 `design_spec.md`；只有旧 SVG 语义才恢复结构 |
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
后处理脚本将受支持的 SVG 向量元素转换为 DrawingML。文本和向量形状会保持为 PowerPoint 原生对象——可点击、可编辑、可改样式；位图资源则复制为 PPT picture media，而不是把整页压平成一张图片。

---

## 产物流

Artifact 的来源 / 派生所有权以 [`artifact-ownership.md`](../../skills/ppt-master/references/artifact-ownership.md) 为准；本节只把同一数据流可视化成架构说明。

维护这套系统时，把文件夹理解成数据流会比“这些目录刚好存在”更清楚：

```text
sources/<content files> ────────┐
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

这张表只展示概念对应关系，不是对整个 SVG 标准的承诺，也不承诺所有映射语义无损。每项受支持能力都必须在 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 中拥有明确的映射记录，说明项目规范写法、允许的兼容输入、目标 DrawingML 表达、保真度和拒绝条件；涉及 PPTX 回导的能力还要说明来源 PPTX / OOXML 语义。映射状态可以是精确、确定性归一化、显式 fallback、sidecar 或 unsupported；讲稿、动画、relationships 等 package 语义不必强行塞进 SVG，但必须明确由哪条路线承载。

如需从 PowerPoint 功能出发逐项查看这些关系，请参阅 [PowerPoint 功能 ↔ 项目 SVG 映射指南](./powerpoint-svg-mapping.md)。该文档负责公开能力与 PPTX 导入恢复映射；`shared-standards.md` 继续负责生成 SVG 创作合同。

主生成路线采用**规范窄写入、受控兼容读取**。新生成的 `svg_output/` 与可复用模板只使用项目规范写法，例如不透明的六位大写 `#RRGGBB`，透明度放在对应的 `fill-opacity`、`stroke-opacity`、`stop-opacity`、`flood-opacity` 或原子元素 `opacity` 中。历史或人工输入只有在兼容合同明确登记、转换结果唯一且输出合法时才可继续导出；Checker 对这类写法给出非阻塞 warning，转换器在编译边界统一归一化。任何需要猜测、没有映射或可能产生损坏 PPTX 的表达都必须报 error。

因此，转换不是在任意 SVG 和 DrawingML 之间做格式猜测，而是在项目规范化 SVG 与 DrawingML 之间执行有注册表、有保真度说明、可测试的编译。

SVG 也是唯一同时满足流程中所有角色需要的格式：**AI 能可靠地生成它，人能在任意浏览器里直接预览和调试，脚本能按明确的兼容合同转换它**——在生成任何 DrawingML 之前，设计稿就已经完全透明可见。

---

## 源内容转换

源文档（PDF / DOCX / EPUB / XLSX / PPTX / 网页）会在 Strategist 开始前完成归一化，但当前架构已经不是“全部转成 Markdown 后其他信息都不重要”的单通道模型。现在有两条事实通道，各自拥有明确职责：

| 通道 | 产物 | 所有者 | 用途 |
|---|---|---|---|
| 内容契约 | `sources/` 内容型文件（以 `<stem>.md` 为主） | `source_to_md/*` 转换器 + `import-sources` | 文本、表格、图表数值、SmartArt 节点文字、引用和源材料叙事 |
| 结构化分析 | `analysis/*.json` / `analysis/*.csv` | intake 与分析工具 | PPTX 身份信息、页面几何、原生表格/图表、SmartArt 关系、图片尺寸/色彩/主体 |

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
| `svg_final/` | 强制派生的自包含视觉预览 SVG，服务 IDE / 浏览器，也可手动作为 SVG 图片插入 PowerPoint；不保证“转换为形状” |
| `live_preview/` | 预览服务状态、直接编辑历史和注解日志 |
| `notes/` | `total.md` 与拆分后的逐页讲稿 |
| `exports/` | 带时间戳的 native PPTX 交付物 |
| `backup/<timestamp>/` | 默认导出时写入的冻结 `svg_output/` 快照 |

CLI 仍支持三种导入模式：`--move`、`--copy`，以及“仓库内文件 move、仓库外文件 copy”的自动默认。`SKILL.md` 中的生产工作流会刻意收紧这一点：agent 必须调用 `import-sources ... --move`，让所有源文件和中间产物进入 `sources/`，保持工作根目录干净。脚本级默认服务临时 CLI 使用的安全性；工作流级契约更严格，是为了让 AI 执行具备可复现和可审计性。

---

## 架构不变量

可执行的 artifact ownership 不变量以 [`artifact-ownership.md`](../../skills/ppt-master/references/artifact-ownership.md) 为准；本节解释这些边界为什么在架构上重要。

这些不变量强于普通实现偏好。如果某个改动破坏了其中一条，它很可能是在改变架构，而不是做重构。

| 不变量 | 实际后果 |
|---|---|
| `sources/` 内容型文件是主流水线内容契约 | 主 SVG 路线中的文本、表格和图表数值来自 `sources/` 内容型文件（Markdown 为主，`.txt` / `.csv` / `.json` / `.yaml` 等同样计入）；已知 sidecar（`*.conversion_profile.json`、`*_files/image_manifest.json`）排除在外 |
| `analysis/` 存机器事实，不存设计契约 | `source_profile.json` 和 intake artifact 辅助 Strategist；除非工作流明确规定，否则不锁定页数 / 页序 |
| `design_spec.md` 解释设计；`spec_lock.md` 执行设计 | Executor 从 `spec_lock.md` 取锁定值，而不是从叙述记忆里取 |
| 每页生成前重读 `spec_lock.md` | 长 deck 中的颜色、字体、图标、图片、节奏、布局和图表选择保持稳定 |
| `svg_output/` 是唯一手写 SVG 目录 | 质量检查、手工编辑、重导出和 `update_spec.py` 都面向作者源 |
| `svg_final/` 是派生产物 | 它必须能从 `svg_output/` 重建，只负责自包含视觉预览，不应成为 native 导出的事实源 |
| native PPTX 标准导出读取 `svg_output/` | 唯一受支持的可编辑形状路线由项目转换器执行；它要在 finalize 重写前保留图标、`preserveAspectRatio`、圆角矩形和原生图片裁剪语义 |
| PowerPoint 手工“转换为形状”不属于兼容性契约 | `svg_final/` 可以作为 SVG 图片插入，但转换后的结构与视觉结果不做保证，也不反向约束 SVG 允许能力 |
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

**机械触发，不做语义匹配。** 像 `presentation_core` 这样的裸名字、品牌提及，或“麦肯锡风格”这类风格短语，即使库里存在相似目录，也不会触发 Step 3。Step 3 只消费显式路径。当前 Brand/Layout/Deck 工作区均解析 `templates/design_spec.md`；兼容的旧式平铺包从根目录读取 `design_spec.md`。目录平铺本身不是恢复理由；只有旧 Master/Layout/placeholder 语义才触发 `restore-pptx-structure`。发现性交给模板索引和显式问答（“有哪些模板可以用？”），不交给运行时 fuzzy matching。

当前 Brand/Layout/Deck 都采用同一工作区路由合同；Brand 不含 SVG roster，空的可选目录直接省略：

```text
<template_workspace>/
├── templates/   # design_spec.md、SVG 原型，以及使用时的 templates/icons/
├── images/      # 可选；位图素材，SVG 统一引用 ../images/<name>
├── icons/       # 可选；提取向量素材的运行期副本
└── exports/     # 可选、按需生成的审阅文件；全局库下由 Git 忽略
```

`<template_workspace>` 可以是 `skills/ppt-master/templates/<kind>/<id>/`，也可以是 `projects/<name>/`。Step 3 接收这个根目录。工作区可在两个位置之间迁移而不改形；唯一的范围差异是全局索引注册。空的可选目录不创建，`exports/` 也不会复制进新项目。

`standard` 与 `fidelity` 会重新创作 SVG 和新的 Master/Layout/slot 系统；来源拓扑只作为视觉证据，不保留、也不蒸馏。`mirror` 按来源页序恢复 Master/Layout 身份与父子关系、placeholder 事实和受支持视觉，不做语义归纳。由于结构层不能是 `<g>`，固定结构层的来源 group wrapper 只允许机械展开成直接原子，同时保持归属、paint order 和视觉一致。

三类模板拥有不同的设计契约片段：

| Kind | 拥有的片段 | 典型内容 | 对 Strategist 的影响 |
|---|---|---|---|
| `brand` | 身份片段 | 配色、字体、logo、语气、图标风格 | 锁定身份；结构保持自由 |
| `layout` | 结构片段 | 画布、页面结构、页面类型、SVG roster | 锁定结构；身份仍在策略师确认阶段里确定 |
| `deck` | 身份 + 结构 + 模板总览 | 完整身份 + 结构包 | 锁定完整模板语法，只剩内容相关选择 |

当用户提供多个路径时，融合是**片段级**而不是字段级：brand 覆盖身份片段，layout 覆盖结构片段，deck 提供中间的 template overview 片段。同类冲突会被显式列为冲突，而不是按输入顺序默默决定。这样融合后的 spec 能明确说明每个片段来自哪里，便于审计和复现。

**原生 PPTX 模板不属于 Step 3。** `.pptx` 可以作为源材料进入流水线，PPTX intake 也能抽取其身份和几何信息。但“给一个原生 PPTX 模板并生成新 PPTX”的请求会进入 `template-fill`，因为用户期望的是克隆 PowerPoint 页面壳并替换文本 / 表格 / 图表。SVG 路线只能消费可复用模板工作区；如果要把某个 PPTX 的设计语言用于 SVG 路线，必须先通过 `create-template` 生成工作区，再把工作区根目录路径提供给 Step 3。

**布局是 opt-in，图表和图标不是。** 这种不对称不是矛盾——*布局*正是锁定视觉惯用语的那一层（地板/天花板问题），而图表和图标是不会施加 deck 级风格约束的复用原语。同一个 `templates/` 目录，但在视觉契约里扮演的角色不同。

---

## 角色系统：单一流水线中的专业模式

PPT Master 用的是**单主代理内的角色切换**，不是并行子代理。Strategist、Image_Generator、Executor 以及各独立工作流模式，本质上都是按需加载的指令作用域；它们不是带着各自过期 deck 状态的独立 agent。这个选择有三条互相支撑的理由：

**为什么是单代理而非并行子代理。** 页面设计依赖完整的上游上下文——Strategist 的色彩选择、图片资源是否成功获取（还是失败被替代）、之前几页的视觉节奏。子代理拿到的只能是这个上下文的过期局部快照，产出的 deck 视觉会逐页漂。同一逻辑也禁止分批生成（比如一次 5 页）：分批加速上下文压缩，deck 的视觉一致性下降速度比节省的速度更快——不划算。

**为什么是角色专属 reference 而不是一个超大 prompt。** Strategist 跑的是「跟用户协商」模式（开放式、对话式、可以回退），Executor 跑的是「产出严格 XML」模式（不准即兴、不准漏属性）。把两者塞进同一个 prompt，强迫模型在同一个 turn 里持守相互矛盾的纪律——所有混合模式的 prompt 工程病灶都会出现。按角色拆开，每个角色只加载它需要的、扔掉其他。

**策略师确认阶段是唯一的阻塞 gate。** Strategist 阶段以一个三阶段确认 gate 作为核心阻塞决策点：第一阶段确认方向锚点（画布、受众、改写幅度、交付目的、mode、visual style，以及只在 Step 3 加载 Deck/Layout 模板时出现的模板遵循方式）；第二阶段基于已确认锚点重新推导并确认设计系统（页数、调色板、字体、图标、公式策略）；第三阶段基于已确认设计系统重新推导并确认图片与执行方式（图片来源、生成图风格、AI 图片路径、生成模式、refine-spec）。模板遵循默认推荐 `adaptive`：每页仍引用模板架构，但无匹配构图时可在同一 Master 下创建新 Layout；`strict` 则保持所选 Layout 契约不变。最终的 `confirm_ui/result.json` 是权威输入。

**图片分析走重算元数据，不读像素。** 当项目里存在图片时，Strategist 和 Executor 使用 `analyze_images.py` 的输出（`analysis/image_analysis.csv`），而不是直接打开图片文件。这个 CSV 是基于当前 `images/` 目录重算出来的视图，不是持久缓存。每次做图片敏感决策前重跑分析，就是它的防陈旧策略：用户图、抽取图、网络图、AI 图、公式图和切片图最终都会汇入同一张可度量事实表。

**逐页 spec_lock 重读** 是长 deck 的抗漂移机制——完整理由见下面的 § 设计规范的传播。

---

## 执行纪律

流水线由 [`SKILL.md` § 全局执行纪律](../../skills/ppt-master/SKILL.md) 中的 10 条规则强制——那份文件是权威，规则住在那里。它们看起来很官僚，但存在的理由是：LLM 默认行为是“让我在这一 turn 里把整个问题搞定”，而这恰好是串行流水线最不该有的形状——串行流水线要求每一步的输出都是有界、过 checkpoint、被下一步消费的。这套规则共同关闭了实际反复出现的失败模式：乱序执行、AI 代为做用户设计决策、跨阶段打包、前置条件未满足、投机预先准备、子代理上下文丢失、分批漂移、长 deck 色彩字体漂移、脚本批量生成 SVG 漂移，以及路由歧义。

常见失败的停 / 继续规则以 [`failure-recovery.md`](../../skills/ppt-master/workflows/failure-recovery.md) 为准；本节不复制恢复矩阵。

其中两条新边界尤其关键。第一，Executor 页面 SVG 必须由当前主代理逐页手写；禁止写 Python / Node / shell 生成器批量吐 SVG，因为这种输出会丢失跨页判断和视觉连续性。第二，路由是确定性的：原生 PPTX 模板、beautify、native enhancement、自定义动画、live preview 等触发条件已经在仓库里定义清楚时，不再额外抛给用户一个开放式路线选择题。

角色切换协议（切换模式前必须 `read_file references/<role>.md`）有两个互相支撑的作用：把新鲜的角色指令载入上下文，覆盖前一模式的漂移；对话 transcript 中的可见标记构成审计轨迹，让用户能看到 agent 何时切换了模式——回看一个具体决策为什么这样做时，这条线索很关键。

---

## 设计规范的传播：spec_lock.md 作为执行契约

Strategist 阶段产出两份看起来冗余但服务不同对象的产物：

- `design_spec.md` —— 人类可读叙述；设计的「为什么」（目标受众、风格目标、配色理由、页面大纲）
- `spec_lock.md` —— 机器可读执行契约；Executor 必须**字面照搬**的「是什么」（HEX 颜色、确切的 font family 字符串、图标库选择、带状态的图片资源列表）

为什么两份都要？没有 `spec_lock.md` 的话，Executor 在长 deck 里会逐页重读 `design_spec.md`，LLM 上下文压缩漂移会逐渐扭曲色值和字体。`spec_lock.md` 是**抗漂移机制**——SKILL.md 强制要求生成每一页前 `read_file <project>/spec_lock.md`，让数值在 20+ 页里保持字面一致。

这份 lock 同时也是逐页路由表。除了全局配色和字体，它还承载 `page_rhythm`（`anchor` / `dense` / `breathing`）、`page_charts`（某页应适配哪个图表模板）、带放置/裁剪契约的图片行，以及决定加载哪些执行规则文件的 `mode` / `visual_style`。结构化 deck/layout 模板项目额外承载 `page_layouts`（每页继承哪个输入模板 SVG）、唯一的 `pptx_masters` / `pptx_layouts` 定义，以及 `page_pptx_layouts` 页面分配；flat 自由设计 / brand-only 项目只保留 `pptx_structure.mode: flat`，那些段整段省略，而不是写成空值。其余字段的空值本身仍是信号：没有图表、没有图片，很多时候是设计选择，而不是漏填。

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

**开发期外部引用，下游分叉成预览与原生导出两套嵌入策略。** 在 `svg_output/` 里编辑时，图片是外部文件引用——快速迭代、单点替换。随后分成两种表达：`svg_final/` 走 Base64 内联，产出一组不依赖外部位图文件的自包含 SVG，供 IDE、浏览器和手工插入为 SVG 图片；native PPTX 则把位图复制进 PPTX 的 media 文件夹，用 `<a:srcRect>` 表达裁剪。分叉的理由是职责不同：前者服务视觉预览，后者服务项目转换器生成的可编辑 DrawingML。`svg_final/` 不作为 PowerPoint 手工“转换为形状”的兼容源。

**AI 图片三维系统：Strategist 阶段就锁定。** 当 deck 包含 AI 生成图片时，Strategist 在前置阶段一次性确定三个正交维度——`rendering`（视觉风格家族：vector-illustration / editorial / 3d-isometric / sketch-notes / ……）、`palette`（deck 的 HEX 在图里**怎么用**：比例 + 角色 + 气质）、`type`（每张图的内部构图：background / hero / framework / comparison / ……）。前两个是 deck 级、写进 `spec_lock.md`；Image_Generator 此后每张图的 prompt 都从同一份锁定的 rendering + palette 加上该图的 type 组装出来，而不是逐图重决风格。没有这层锁定，每张图都会自己风格漂移，整套 deck 读起来就是一摞互不相关的插画。这是 `spec_lock` 字体/色彩抗漂移机制在像素上游的对偶——同一思路，往前推一层。Strategist 在策略师确认阶段会向用户呈现 **≥3 个 `rendering × palette` 候选**，绝不静默地自动锁定单一组合，因为这是一个会牵动全 deck 视觉的选择，唯一权威只有用户的品味。

---

## 图文版式：Primary 主结构 + Modifier 修饰层

「图片**怎么放上幻灯片**」的词表（完整词汇在 [`references/image-layout-patterns.md`](../../skills/ppt-master/references/image-layout-patterns.md)）把 72 条编号技法拆成两层、自由组合：

- **Primary 主结构**（容器布局 / 图作画布 + 原生覆盖 / 多图组合）—— 页面的骨架。一页可一个也可多个；跨 Primary 的组合，如「侧边对比 + 图作画布的注解卡」，是合规的。
- **Modifier 修饰层**（非矩形裁剪 / 遮罩与叠加 / 纹理 / 特殊技法）—— 装饰层。一页可叠任意多个，附着在 Primary 之上。

**为什么显式鼓励复合，而不是「一页一个 primary」。** 这份词表对抗的 AI 失败模式不是「叠太多」，而是「用得太少」——把每页图片默认堆成裸的 `#2 左三分` 或 `#48 侧边对比`，Modifier 层完全不动，产出视觉扁平的「AI 默认感」版式。早先的规则「一页一个 primary，modifier 可叠」听起来有原则，实际上加剧了 Modifier 层的弃用——AI 把它读作「可以不叠」的许可。现在的措辞反过来：组合是常态，单 Primary + 无 Modifier 才需要解释。

**为什么物理拆分两层，而不是只打标签。** 词表被重排成「Primary 全部在前，Modifier 全部在后」——Strategist 或 Executor 读一次目录，就能从结构上内化「两层」心智模型。编号是稳定 id（`#38` 永远是「图作画布 + 注解卡」，不论它在文件里的物理位置），所以 `spec_lock.md`、`design_spec.md §VIII`、历史 executor 输出、过往示例里所有 `#<id>` 引用照样解析。

**为什么组合走 Strategist 资源列表，不只交给 Executor 临场发挥。** `§VIII 图片资源列表` 的 `Layout pattern` 列接受 `#<id> + #<id> ...` 表达式——Primary id 加可选 Modifier id——所以组合在 SVG 生成**之前**就被声明、被 `svg_quality_checker` 审计、并能在 session 重入后存活。把组合责任只压在 Executor 身上，长 deck 上下文压缩时就会丢；把它编码进 spec_lock 旁的资源列表，组合就成为设计契约的一部分。

**为什么真正的硬约束留在上游。** 跨切的 SVG 创作与 PPTX 兼容性例外独家住在 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md)。版式词表只指向这份合同，不再复述——这样规则变化时只有一个文件要改，词表里也不会留下一份过期副本继续暗中强制旧规则。

---

## 项目规范化 SVG 与兼容性边界

PowerPoint 的 DrawingML 是 SVG 表达力的严格子集，因此主编译路径不把“浏览器可以渲染”视为“项目可以导出”。只有在 [`references/shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 中登记了项目规范表达或显式兼容形式，并且拥有确定 DrawingML 映射的词汇，才属于可接受输入。该文件是语法、结构、单位、metadata、兼容别名、保真度和拒绝条件的唯一权威；本架构文档只定义分层原则，不复制具体规则。

**为什么本地复用是编译期复用，不是 PowerPoint 保留对象。** 接受的创作形式由权威合同定义、共享校验器执行。校验通过后，流水线会递归实体化引用子树并重写克隆局部 ID 后再导出；PPTX 回导因此只返回展开后的原语，不重建创作期复用图。

值得在架构层标记的理由：

- **为什么需要封闭映射，而不是默认接受普通 SVG。** 项目规范化 SVG 是编译器中间语言，不是浏览器兼容层。新增元素、属性或取值必须同时补齐导入语义、导出映射、校验规则和回归验证；未登记能力默认不进入主编译路径。
- **为什么兼容输入不等于创作许可。** 已登记的历史别名可以由转换器确定性归一化，并由 Checker 给出非阻塞 warning；提示词、模板和示例仍只生成项目规范写法。兼容面只能服务迁移和人工输入，不能反向扩大生成语法。
- **为什么 warning 可以放过。** warning 只表示合法输出前提下的推荐写法、确定性归一化、已知保真度下降或视觉质量风险。它不改变页面语义，不要求 Executor 回改，也不阻断发布；如果某项必须修正才能交付，它就应被定义为 error。
- **为什么是经验性，不是从规范推导。** 兼容性边界从真实的 PPT 导出失败长出来，不是读 OOXML 规范推导出来的。有些理论上能表达的效果跨 PowerPoint 版本仍不可靠，因此合同反映的是实际能交付的子集。
- **XML 良构性仍是前置条件。** SVG 一旦不是合法 XML，尚未进入 DrawingML 兼容性阶段就会失败。接受的创作形式集中在权威合同中，避免架构与提示文档分别维护后发生漂移。
- **兼容性校验在后处理之前执行。** `svg_quality_checker.py` 在 `svg_output/` 上执行；后处理会重写 SVG，可能掩盖源级别违规。阻断性 error 由 Executor 重新写，warning 不触发回改；转换器按设计哲学中定义的职责再次校验关键发布条件。

---

## 质量门

**为什么需要这道检查器。** LLM 生成的 SVG 不是确定性的——兼容性违规会在长 deck 中悄悄混入，只在 `svg_to_pptx` 中途崩或 PowerPoint 静默丢元素时才暴露。检查器把「PowerPoint 在第 14 页导出失败」转化为「第 14 页违反 SVG 兼容性合同」，诊断速度提升一个数量级——这正是让长 deck 在经济上可迭代的关键。

**为什么放在后处理之前，而不是之后。** 后处理会重写 SVG（图标嵌入、图片内联），会掩盖源级别违规。直接读 `svg_output/` 抓的是 Executor 的实际输出，先于任何可能掩盖 bug 的清理动作。

**严重性模型：error 阻塞、warning 不阻塞，且有意没有 auto-fix。** 严重性不按“是否符合推荐写法”划分，而按“能否确定、合法地映射”划分：

| 严重性 | 判定条件 | 流水线行为 |
|---|---|---|
| `error` | 结构合同被破坏；输入无映射或有歧义；必要 metadata 缺失；数值非法；转换后可能违反 DrawingML / PPTX 约束；或可能导致 PowerPoint 修复文件 | Executor 必须重写并重新校验；转换器也必须拒绝发布 |
| `warning` | 已有唯一、安全、合法的转换结果，但输入不是项目规范写法，或存在已知的确定性归一化、保真度下降、视觉质量风险 | 记录诊断后允许发布；不要求逐条确认或强制回改 |

质量门沿用设计哲学中定义的三层职责。这里有意不提供 auto-fix：机械修补可能静默覆盖有效的设计意图，也可能交付一个更差的页面。

如果同一种 warning 持续出现在新生成页面中，应优先修正提示词、模板示例或规范说明，使默认输出回到项目规范写法；这属于生成质量问题，不需要把本来安全的兼容输入升级成阻塞错误。反过来，如果实践证明某个 warning 可能产生非法文件或不确定语义，就必须把合同和 Checker 同步升级为 error。

**为什么图表坐标验证挂在同一道 gate。** 图表页面有几何正确性需求（柱高、饼图扇角、坐标轴刻度位置），这些不是结构问题，SVG 合法性规则也抓不到。最自然的捕捉位置就是已经要求 AI 回看自己输出的那道 gate——把「看一眼你刚生成的东西然后修」的认知上下文打包到一个阶段，比把结构和几何审查分到两轮 review 更高效。

---

## 后处理流水线

> 工程化转换阶段中每一份产物和每一个模块为何存在，删除它会破坏哪些工作流。在考虑简化 `svg_final/` / `finalize_svg.py` / `svg_to_pptx.py` 之前，先读这一节。

### 交付产物与工作流

后处理与导出阶段涉及几类职责不同的产物。每一份都服务于一种流水线中无法替代的工作流。

| 产物 | 服务的工作流 | 为何无可替代 |
| --- | --- | --- |
| `svg_output/` | 唯一源、手工编辑入口、`update_spec.py`、`svg_quality_checker.py` | 流水线中唯一**手写**而非派生的目录 |
| `svg_final/` | IDE 内即时预览（VSCode/Cursor 直接打开 `.svg`）、浏览器单页预览、手动作为 SVG 图片插入 | `.pptx` 在 IDE 里打不开；`svg_output/` 因图标 / 图片是外部引用，IDE 中渲染不完整。PowerPoint 手工“转换为形状”不在支持范围 |
| `exports/<name>_<ts>.pptx`（native） | 主交付物——PowerPoint 中以 DrawingML 形状形态可编辑 | 唯一一份用户可在 PowerPoint 中原生改尺寸 / 改色 / 改样式的产物 |
| `exports/<name>_<ts>_native_charts_tables.pptx`（需 `--native-charts-and-tables` 显式开启） | 让带 `data-pptx-replace-with` 标记的 SVG 派生形状图表/表格替换为 PowerPoint 原生 Chart/Table 对象 | 带数据源和图表/表格专属控制的对象；默认 DrawingML shape 本身仍可独立编辑 |
| `exports/<name>_<ts>_narrated.pptx`（经 `--recorded-narration audio` 生成） | 自动放映与 PowerPoint 视频导出用的旁白版 deck | 逐页嵌入音频并写入自动推进时间;命名与无声导出区分开 |
| `backup/<ts>/svg_output/`（默认流程下始终生成） | 不重跑 LLM 的前提下从冻结 SVG 源重建 pptx、长期存档 | 项目下游被改动后，Executor 原始 SVG 唯一的留存副本 |

### SVG 预处理器有**两种**消费者

这是读代码时容易忽略的关键事实。`skills/ppt-master/scripts/svg_finalize/` 下的清理模块和本地引用展开器，会在两个地方被使用，服务两份不同的产物。

**写盘消费者** —— `finalize_svg.py` 每次运行都把 `svg_output/` → `svg_final/` 写到磁盘一次，同时展开项目图标占位符和合规的本地 `<use>` 引用。`svg_final/` 随后供 IDE / 浏览器视觉预览及手工 SVG 图片插入使用。

**内存消费者** —— native pptx 直接读 `svg_output/`（不经磁盘中转），但 DrawingML 无法内联处理项目图标占位符、保留的 SVG 引用实例和定位文本 run，所以转换器在内存中应用对应预处理器：

| 内存调用点 | 预处理器 | native pptx 为何需要 |
| --- | --- | --- |
| `svg_to_pptx/use_expander.py` | `svg_finalize.embed_icons` | DrawingML 不识别 `<use data-icon="...">`；不展开图标会静默丢失 |
| `svg_to_pptx/use_expander.py` | 静态本地引用展开 | DrawingML 不保留 SVG `<use>` 实例图；合规子树必须实体化并获得实例级独立 ID |
| `svg_to_pptx/tspan_flattener.py` | `svg_finalize.flatten_tspan` | DrawingML 文本块无法在段落中跳位置；`dy` 堆叠的多行 `<tspan>` 会塌成一行，`x` 锚定的 tspan 会跑到错误的列 |

### 各模块消费者一览

| 模块 | 写盘消费者 | 内存消费者 | 删除影响 |
| --- | --- | --- | --- |
| `embed_icons.py` | `finalize_svg` 的 `embed-icons` 步骤（随后展开本地 use） | `svg_to_pptx/use_expander.py` | native pptx 丢失全部图标 + `svg_final/` 不再自包含 |
| `svg_to_pptx/use_expander.py`（本地引用） | `finalize_svg` 的 `embed-icons` 步骤 | native 转换器预检 | finalize/native 导出失去实体化合规本地复用的能力 |
| `flatten_tspan.py` | `finalize_svg` 的 `flatten-text` 步骤 | `svg_to_pptx/tspan_flattener.py` | **native pptx 中 `dy` 堆叠的多行文本塌成一行** |
| `align_embed_images.py` | `finalize_svg` 的 `align-images` 步骤 | — | `svg_final/` 失去图片嵌入 → IDE / 浏览器预览和手工插入的 SVG 图片缺图 |
| `crop_images.py` / `embed_images.py` / `fix_image_aspect.py` | 被 `align_embed_images.py` import | — | `align_embed_images` `ImportError`，整条链路 broken |
| `svg_rect_to_path.py` | — | — | 仅保留为历史诊断工具，不属于 `finalize_svg` 或受支持导出流程；不得据此承诺 PowerPoint 手工“转换为形状”兼容性 |

---

## 直接 OOXML 路由

不是所有 PPTX 相关请求都应该重新生成页面。PPT Master 现在为“原生 deck 本身就是编辑对象”的场景提供直接 OOXML 路由。

`template_fill_pptx.py` 是 `scripts/template_fill_pptx/` 包的薄 CLI 入口。analyzer 抽取带文本槽位、表格、图表和几何信息的 slide library；fill plan 选择源页面并确认替换内容；applier 克隆幻灯片并直接 patch XML parts。这条路线故意绕开 SVG：用户提供 PowerPoint 模板时，通常期望原生母版、占位符、表格和图表继续保持 PowerPoint-native。

`native_enhance_pptx.py` 是已完成 deck 原生增强的稳定入口。它委托 native narration / timing 实现，在项目归档副本上直接 patch PPTX package：讲稿、页面转场、录制旁白媒体、页面计时和相关元数据。它的契约是保留：已有内容、布局和格式不重新生成。

这些直接路线会和主流水线共享部分分析原语，尤其是 PPTX intake，但不共享 SVG 作者阶段和后处理阶段。这个分离是有意的：SVG 生成是设计合成路径；直接 OOXML 编辑是保留路径。

---

## Native PPTX 转换器内部

`svg_to_pptx.py` 执行设计哲学中定义的最终防线；本节只解释这条受约束编译路线的内部结构。

**为什么是逐元素派发而不是整体翻译。** SVG 的层级模型干净地映射到 DrawingML 的 group / shape / picture 类型——不需要一个全局优化器去重新规划幻灯片。每种形状都有自己窄的翻译器，简单到能单独调试和单元测试。一张幻灯片的最终质量等于这些独立局部转换之和；这个性质在整体翻译下脆弱，在元素派发下稳健。

**为什么导入型与生成型 metadata 分层。** 导入 PPTX 时，完整 SVG 可以携带高级形状所需的 metadata、隐藏 carrier 和预览指纹，但这类载荷不适合直接进入模型上下文。authoring projection 会非破坏性地移除大体积载荷，只保留可见几何和紧凑意图，而且永远不是导出源。`standard` / `fidelity` 创作项目规范化 SVG，只有精确匹配已登记 preset 时才使用 compact authored-preset 组。Mirror 从无损来源物化，可在未改的 Slide-local/slot 对象上复用转换器已经支持的 metadata；固定结构层保持直接原子，不支持或已修改的对象保留当前 SVG fallback。

**为什么只有一条 PPTX 编译路线。** Native 导出把作者 SVG 中受支持的元素逐个翻译成 DrawingML 形状。常规 deck 路线读取 `svg_output/`；用户需要时，create-template 对通过校验的模板原型调用同一 structured 编译器，生成 `exports/<id>_template_preview.pptx` 作为审阅证据。项目不会把整页 SVG 媒体或另一套位图渲染打包成第二类 PPTX。`svg_final/` 仍由常规 deck 的强制后处理生成，但只承担自包含视觉预览和 SVG 图片插入，不为 PowerPoint 手工“转换为形状”提供兼容兜底。

**为什么模板路线的结构必须在视觉生成前确定。** Master 和 Layout 不是后处理阶段才发现的结果。在结构化 deck/layout 模板路线上，Strategist 在 SVG 生成前写出唯一 Master/Layout 定义和完整页面分配；Executor 在构图时同步写入这些身份、固定原子元素和槽位，导出器只编译声明。自由设计与 brand-only deck 做的是相反的取舍：保持 `mode: flat`，所有对象留在 Slide 本地，不写任何结构 metadata，导出时只获得一个属于本项目的干净 Master/Blank-Layout 壳——可复用结构是模板路线的交付物，不是自由设计的创作税。legacy structured/template 项目进入 `restore-pptx-structure`；两条路线都不会触发启发式 Master/Layout 提升或 placeholder 推断。

**为什么 Master/Layout 视觉必须原子化。** 一个 Master 或固定 Layout 对象必须是根节点的直接子元素。导入 PPTX 时，group 的 transform、opacity、style 和 z-order 会下推到各个原子对象。这个选择有意放弃来源 group 的整体编辑层级，换取简单、可比较、可确定重建的结构归属，避免嵌套结构歧义。

**为什么 Layout 槽位使用 group。** 一个可复用槽位是顶层 `<g>`，携带语义类型和设计区域 bounds。普通槽位恰好包含一个兼容 carrier；导出时 carrier 被解包并绑定成真实 Slide placeholder。无法由单一 placeholder 表示的复合 `object` 区域走显式 proxy 降级：可见 group 保持普通 Slide 对象，隐藏透明 placeholder 负责 PowerPoint 绑定。Layout 也可以零槽，因此纯视觉页面无需制造假全页槽位。

**为什么可复用 bounds 是设计区域，不是量出来的文本框。** bounds 来自安全区、分栏、面板内框或图片框，而不是字形宽度、行数或当前内容紧包围盒。当前 Slide 保留自己的 carrier 几何，因此只要语义构图相同，4:6、3:7、5:5 的实例都可复用同一 Layout。文本长度不会意外拆分或改变可复用合同。

**为什么 strict 与 adaptive 模板共享一条 structured 路线。** `page_layouts` 记录完整创作原型，`pptx_masters` / `pptx_layouts` 记录唯一可复用定义，`page_pptx_layouts` 记录页面分配。strict 保持声明的原型合同；adaptive 保持原型 Master，只有固定 Layout 原子或槽位 topology/bounds 改变时才定义新 Layout，并在页面创作时立即更新分配，而不是事后推断。模板定义即使暂时没有页面使用，也能注册进最终文件。非 mirror 的皮肤由项目控制；mirror 保持已恢复的输出视觉身份。

**为什么显式版式把文字默认值分在 Master 与 Layout 两层。** Flat 与 structured 导出都会把锁定的 title 字号和确定性的九级 body 层级写入 Master 文本默认值，同时保留原有缩进与项目符号设置；在 structured 路线上，每个 Layout 文字槽位还会把 carrier 首个 run 的字号写入一级默认值，同时保留提示文字的直接字号。这样，插入或重置 placeholder 时仍能继承 Layout 特定尺度，而生成 Slide 上的直接 run 不变。

**为什么 structured 输出要在发布前回读。** 元数据预检不能证明 package 序列化保留了所有 relationship 与注册信息。导出器会重新打开临时 PPTX，把已发布 Slide 与完整 Master/Layout roster 分开校验，包括没有任何 Slide 使用的定义；同时核对 Presentation → Master → Layout → Slide 注册链、物理 part/content-type roster、选择器身份、固定对象顺序、placeholder 类型/有效索引/bounds、carrier 绑定、隐藏 proxy 与零槽 Layout，只有通过后才发布。

**为什么模板创建分为创作模式和恢复模式。** `pptx_template_import.py` 输出分层 Master/Layout/Slide 参考和 native 结构事实。`standard` / `fidelity` 把这些素材和视觉当参考，再按照确认后的可复用行为创作新拓扑。Mirror 则一对一恢复来源 roster 与拓扑，只允许显式 structured 合同要求的机械归一化。原始 PPTX 保留为分析证据，不成为最终模板依赖。

**为什么 create-template 在两种范围都使用同一工作区路由。** `create-template` 仍以写入索引的 `library` 为默认，也可写入已初始化项目。两种根目录都要求 `templates/`；`images/`、`icons/` 和按需生成的 `exports/` 只有存在真实内容时才出现，SVG 素材引用完全一致。因此工作区可直接迁移和复用，不需要全局库专用 package 分支或缩减的项目分支。唯一范围差异是全局索引注册，两种范围都使用同一 `structured` 合同。

**为什么模板 SVG 保持完整却仍能编译成原生结构。** 模板 SVG 会重复携带继承的 Master/Layout 视觉和示例 Slide 内容，因此可独立打开。生成时由 `page_layouts` 选择该原型，输出 SVG 仍保持视觉闭包。导出器移除重复继承原子、生成真实 Master/Layout part，并把槽位 carrier 与 Slide-local 内容留在 Slide。

**为什么 PowerPoint 原生 Chart/Table 重建使用显式替换 marker，而不是自动替换对象。** 独立的 `pptx_to_svg.py` 导入器只为已验证的表格 / 图表子集输出可见 SVG fallback、`data-pptx-replace-with` 与 `<metadata type="application/json">`。父组 marker 决定 payload schema；普通 shape 与 connector 不使用该合同。表格导入覆盖精确的物理行列 topology、slave 为空的规范矩形 merge、安全的 solid/no-fill 逐边 border、纯文本多段落，以及封闭的 run 级富文本段落。富文本段落包含非空 `runs`；每个 run 必须有 `text`，并且只能使用 `bold`、`italic`、`underline`、`strike`、`color`、`font_size`、单一 `font_family`、`lang` 和 `alt_lang`。不含非空 `effectLst` / `effectDag` 的来源展示型 run XML 会归一化到该 schema；表格单元格 run 效果则会禁用原生替换，并添加阻塞效果诊断。带 relationship 的文本、扩展节点、换行、字段、tab、项目符号、破损文本 topology、非规范 merge、不安全 border 与非纯色填充仍保持 fallback-only。表格样式 `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}` 的规范化 fallback 会解析 `wholeTbl`、`firstRow`、横向带状行、主题颜色 / 字体和直接格式覆盖；这不代表完整 built-in/custom style registry。

受支持的柱 / 条 / 折线 / 面积、饼 / 圆环、散点 / 气泡图在没有 baked preview 时会生成确定性、可读的 SVG fallback，并标记 `data-pptx-fallback-kind="normalized"`。导入器还覆盖已验证的柱 / 折线 / 面积组合图、规范四系列 OHLC stock、数值日期轴面积图、采用封闭 `axes.x` / `axes.y` 合同的散点 / 气泡图、radar、安全的 `of_pie` `serLines`、坐标轴 / 标题 / 图例归一化，以及有界的柱 / 条图 gap/overlap 场景。`gapWidth` 只接受 `0..500` 内的单个整数，`overlap` 只接受 `-100..100` 内的单个整数；这两个表现字段在 native 输出中有意归一化，非法、重复或越界输入 fail closed。组合图可保留主 / 次 plot 各自的 category cache 与 workbook range。XY 导入根据各系列一致的有效 line/marker/smooth 状态推导 `scatter_style`。封闭的 category/value 与 XY 轴合同为 native read-back 保留 kind、position、visibility、label position、number format、min/max/major unit、reverse 和 major gridlines；规范化 XY fallback 只消费两个 `major_gridlines` 开关。

ChartEx 导入被有意限制为 7 个已验证数据模型：`treemap`、`sunburst`、`histogram`、`pareto`、`box_whisker`、`waterfall` 与 `funnel`。其受支持的层级 / 分类 / 数值 / 系列 / 小计数据 topology 可经 native 输出再导入回读。数值 cache 必须非空且有限，count/index 必须是规范非负整数，并满足精确连续的 point topology。来源 ChartEx 的样式、坐标轴、标签与 binning 可能归一化；这不代表任意 ChartEx 导入或表现层保真。C4/C5 不扩展 normalized renderer，因此 renderer 外的有效 active 类型在没有源 preview 时仍使用 `data-pptx-fallback-kind="placeholder"`。完整 `AxisSpec`、任意 ChartEx 家族、任意富文本 OOXML、旋转 / 翻转 / 3D 图表、未验证的 combo/stock/date-axis 变体及其他未建模语义仍不在 active 导入子集内。native replacement 仍可能归一化 payload 外的表现细节，并保留数据模型优先 warning。默认导出把 fallback 子元素作为可编辑 DrawingML shape；只有 `--native-charts-and-tables` 才启用带数据源和对象专属编辑模型的 PowerPoint 原生 Chart/Table。每个 active 导入 marker 都带有 `data-pptx-import-source="pptx"` 与 `data-pptx-fallback-sha256`：可见 fallback、可达 SVG definition/reference 或 marker transform 变更后，native replacement 会 fail，而不是丢弃 SVG 编辑；仍保留导入来源标记但没有 hash 的旧导入 marker 兼容并给出 warning。生成型创作会同时省略导入来源和静态 baseline，且不产生 warning。该 importer/exporter 组合只用于重建，不替代 `template-fill-pptx` 或 `native-enhance-pptx` 的保留型路线。

---

## 动画与转场模型

值得讲的设计选择是动画**锚点**，不是效果列表。

**为什么把入场动画锚在顶层 `<g>` group。** PowerPoint 的动画时序基于形状 ID——每个被动画的对象需要稳定的 shape ID。给单个原语做动画会产出每页 30+ 个分别飞入的原子（动感泛滥），只给整页做动画又损失视觉叙事。顶层 group 是自然粒度：Executor 本来就被强制要求用 `<g id="...">` 标记逻辑内容块，而这些块正是观众读作「一个东西到达」的单位——动画对齐了已有的逻辑结构，而不是另立门户。

**为什么页面装饰自动跳过。** 现有 Layer 与 slide-number Placeholder 语义首先识别静态结构；最小 `background` / `header` / `footer` / `decoration` / `watermark` / `page-number` role 只补其余缺口。让页面框架飞入会让人出戏（页面本身在每次切换时具象化），几乎不会是用户想要的。只有所有显式标记都缺失的旧 SVG 才回退到精确 id token。

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
| 不要把 `svg_final/` 当作可还原形状的交换格式 | 它只保证自包含视觉预览和 SVG 图片插入；PowerPoint 手工“转换为形状”不在支持范围 |
| 不要默认开启对象级入场动画 | 页面转场是默认；对象 build 是显式导出策略 |
| 不要把 visual review、旁白、图表校准或动画定制默认塞进每次运行 | 这些工作流触发范围窄，且有额外依赖 |
| 不要用文件复制替代 `finalize_svg.py` | finalize 会嵌入图标 / 图片、展开特殊文本并准备预览产物 |
| 不要在主流水线里把 `analysis/<stem>.slide_library.json` 当作第二份图表数值来源 | Markdown 拥有内容数值；除非直接 PPTX 工作流接管，否则 intake 图表 / 表格条目只是结构摘要 |

---

## Standalone Workflows（独立工作流）

独立工作流注册表以 [`workflows/index.md`](../../skills/ppt-master/workflows/index.md) 为准；本节解释为什么这些能力保持独立。

独立工作流是路线定义，不是可有可无的装饰。只有当某个能力与主流水线契约不同，或触发频率太低、不值得默认加载时，才会独立成 `workflows/<name>.md`。

| 工作流 | 触发条件 | 契约 |
|---|---|---|
| `topic-research` | 用户只有主题、没有源材料 | 在 Step 1 前收集网络材料 |
| `template-fill-pptx` | 原生 PPTX 模板 + 新材料 / 新主题 | 直接克隆并填充原生页面；不进入 SVG 流水线 |
| `beautify-pptx` | 现有 PPTX，页数/页序/措辞必须 1:1 保留，只改善排版 | 锁定源身份与内容后，通过 SVG 流水线重新生成 |
| `create-template` | 构建可复用 layout/deck 模板工作区 | 输出可移植工作区根目录；可按需生成 `exports/<id>_template_preview.pptx`；只有全局库范围执行注册 |
| `create-brand` | 提取或定义可复用品牌身份 | 输出 `templates/brands/<id>/` |
| `resume-execute` | 规划会话后新开聊天，用户要求继续某项目 | 不重跑 Strategist，直接进入执行会话 |
| `refine-spec` | 用户明确要求生成前先审阅 / 修改 spec | 写出完整 spec/lock 后停下，用户修改后再恢复 |
| `verify-charts` | 生成 deck 含数据图表 | 导出前校准图表几何 |
| `customize-animations` | 用户要求调对象级动画顺序 / 效果 / 计时 | 创建 / 校验 `animations.json` 并控制再导出策略 |
| `live-preview` | 用户要求预览、点击选择、应用注解或重导出浏览器编辑 | 启动 / 重入浏览器预览，并只在规定时机应用提交内容 |
| `visual-review` | 用户明确要求逐页视觉自检 | 在 Executor 与后处理之间做 rubric pass |
| `generate-audio` | 用户要求旁白 / 视频导出 | 生成旁白音频并走录制计时导出路径 |
| `native-enhance-pptx` | 已完成 PPTX 要保留内容/布局，同时追加原生增强 | 直接 OOXML patch 路线 |

保持这些文件独立，是依赖控制决策。主路径只加载当前需要的角色和 reference；旁白 backend、动画 sidecar、图表校准 rubric、模板导入契约等，只有触发命中时才进入上下文。这样默认 deck 生成路径保持紧凑，同时让低频能力也有确定实现，而不是临场发挥。
