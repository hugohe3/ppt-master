# 技术路线

[English](../technical-design.md) | [中文](./technical-design.md)

---

## 设计哲学 —— AI 是你的设计师，不是完工师

生成的 PPTX 是一份**设计稿**，而非成品。把它理解成建筑师的效果图：AI 负责视觉设计、排版布局和内容结构，交付给你一个高质量的起点。要想获得真正精良的成品，**需要你自己在 PowerPoint 里做精装修**：换掉形状、细化图表、调整配色、把占位图形替换成原生对象。这个工具的目标是消除 90% 的从零开始的工作量，而不是替代人在最后一公里的判断。不要指望 AI 一遍搞定所有——好的演示文稿从来不是这样做出来的。

**工具的上限是你的上限。** PPT Master 放大的是你已有的能力——你有设计感和内容判断力,它帮你快速落地；你不知道一个好的演示文稿应该长什么样，它也没法替你知道。输出的质量，归根结底是你自身品味与判断力的映射。

---

## 系统架构

```
用户输入 (PDF/DOCX/XLSX/URL/Markdown)
    ↓
[源内容转换] → source_to_md/pdf_to_md.py / doc_to_md.py / excel_to_md.py / ppt_to_md.py / web_to_md.py
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[模板处理（可选）] — 默认跳过，直接自由设计
    用户主动点名模板时：复制模板文件到项目目录
    需要新建全局模板：使用 /create-template 工作流单独完成
    ↓
[Strategist] 策略师 - 八项确认与设计规范 → design_spec.md + spec_lock.md
    ↓
[Image Acquisition] 图片获取（当资源列表中有需要 AI 生成或网络搜索的图片时）
    ↓
[Executor] 执行师
    ├── 视觉构建：连续生成所有 SVG 页面 → svg_output/
    ├── [Quality Check] svg_quality_checker.py（强制通过，0 错误）
    └── 讲稿生成：完整讲稿 → notes/total.md
    ↓
[图表校准（可选）] → verify-charts 工作流（含数据图表的幻灯片在此步骤校准坐标）
    ↓
[后处理] → total_md_split.py（拆分讲稿）→ finalize_svg.py → svg_to_pptx.py
    ↓
输出：
    exports/
    └── presentation_<timestamp>.pptx          ← 原生形状版（DrawingML）— 推荐用于编辑与交付
    backup/<timestamp>/
    ├── presentation_svg.pptx                  ← SVG 快照版 — 像素级视觉参考备份
    └── svg_output/                            ← Executor 原始 SVG 备份（重跑 finalize_svg → svg_to_pptx 即可重建 pptx）
```

---

## 技术流程

**核心流程：AI 生成 SVG → 后处理转换为 DrawingML（PPTX）。**

整个流程分为三个阶段：

**第一阶段：内容理解与设计规划**
源文档（PDF/DOCX/URL/Markdown）经过转换变为结构化文本，由 Strategist 角色完成内容分析、页面规划和设计风格确认，输出完整的设计规格。

**第二阶段：AI 视觉生成**
Executor 角色逐页生成演示文稿的视觉内容，输出为 SVG 文件。这个阶段的产物是**设计稿**，而非成品。

**第三阶段：工程化转换**
后处理脚本将 SVG 转换为 DrawingML，每一个形状都变成真正的 PowerPoint 原生对象——可点击、可编辑、可改色，而不是嵌入的图片。

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

源内容转换对大多数用户不可见，但塑造了下游一切：源文档（PDF / DOCX / EPUB / XLSX / PPTX / 网页）在流水线启动前先被归一化为 Markdown。这份 Markdown 随后成为 Strategist 的阅读材料，是后续所有决策的事实源。

两个贯穿性的设计选择塑造了转换器：

**Native-Python 优先，外部二进制兜底。** `doc_to_md.py` 用 `mammoth` 处理 `.docx`、`markdownify` + `beautifulsoup4` 处理 `.html`、`ebooklib` 处理 `.epub`、`nbconvert` 处理 `.ipynb`——全是纯 Python wheel。Pandoc 仅在长尾格式（`.doc` / `.odt` / `.rtf` / `.tex` / `.rst` / `.org` / `.typ`）时被调用。PDF 主走 `PyMuPDF`（原生文本 PDF），扫描件才推荐 MinerU / OCR 工具。理由：避免每个用户都要安装可能没有权限装的系统级二进制，同时仍覆盖边缘场景。

**TLS 指纹模拟应对高安全站点。** `web_to_md.py` 默认用 `curl_cffi` 模拟现代 Chrome 的 TLS 指纹。这一个依赖让同一个脚本能搞定微信公众号（`mp.weixin.qq.com`）和其他屏蔽 Python 默认 `requests` TLS 握手的 CDN。Node.js 兄弟脚本 `web_to_md.cjs` 仅作为 `curl_cffi` 没有预编译 wheel 的环境兜底。

所有转换器产出统一约定：`<input>.md` 加一个同级 `<input>_files/` 目录，里面放抽取出的图片，相对路径引用。这个约定正是项目初始化阶段 `import-sources --move` 的工作前提。

---

## 项目结构与生命周期

PPT Master 项目是一个**形状固定**的目录：

```
projects/<name>_<format>_<timestamp>/
├── sources/              # import-sources 之后的原始输入
├── images/               # AI 生成 + 网络搜到 + 用户提供的图片
├── templates/            # 可选模板 SVG / design_spec_reference
├── design_spec.md        # 人类可读的设计叙述（Strategist 输出）
├── spec_lock.md          # 机器可读的执行契约（Strategist 输出）
├── notes/                # speaker notes，由 total_md_split.py 按页拆分
├── svg_output/           # Executor 手写的 SVG 页面（事实源）
├── svg_final/            # 后处理后的自包含 SVG（IDE 预览用）
├── exports/              # 最终的 native pptx
└── backup/<ts>/          # svg_to_pptx 产生的时间戳快照
```

`project_manager.py init` 创建这个骨架；`import-sources` 是把源文件搬入 `sources/` 的唯一合法路径。两套 import 语义都重要：

- **仓库外**的文件：默认 copy（保留用户原件）；`--move` 强制消费
- **仓库内**的文件：默认 move（避免遗留 stray artifact 被误提交）；`--copy` 强制 copy

这种不对称是有意为之。每种上下文中默认行为正好匹配自然的风险画像——仓库外的文件一般是用户资产，不该动；仓库内的文件一般是中间产物，应该清理掉。

`batch_validate.py` 用于发版前的仓库级健康检查；`error_helper.py` 给常见的项目结构错误提供标准化修复，让 AI 在流水线中途从 broken 状态自恢复。

---

## Canvas 格式系统

PPT Master 不只服务 PPT。同一套 SVG → DrawingML 流水线可以产出方形海报、9:16 故事、A4 印刷品——只需改 `viewBox`。九种 canvas 格式覆盖常见内容用途：

| 格式 | viewBox | 比例 | 用途 |
|---|---|---|---|
| `ppt169` | 1280×720 | 16:9 | 现代演示 |
| `ppt43` | 1024×768 | 4:3 | 传统投影仪 / 学术 |
| `xiaohongshu` | 1242×1660 | 3:4 | 小红书知识帖 |
| `moments` | 1080×1080 | 1:1 | 朋友圈 / IG 方图 |
| `story` | 1080×1920 | 9:16 | 抖音 / Stories |
| `wechat_article` | 900×383 | 2.35:1 | 微信公众号头图 |
| `banner` | 1920×1080 | 16:9 | 网页 / 数字屏 |
| `poster` | 1080×1920 | 9:16 | 手机 / 电梯广告 |
| `a4` | 1240×1754 | 1:√2 | 印刷 |

viewBox 维度是像素值，不是绝对单位（EMU 在 PPTX 导出时计算）。像素 viewBox 让 AI Executor 更容易思考布局（`x="100"` 明确就是左缘 +100px），人类在浏览器里检查也容易。到 PowerPoint EMU 的换算只发生一次——在 `svg_to_pptx` 中，按规范的 EMU/px 比率（914400 EMU/inch ÷ 96 px/inch = 9525 EMU/px）。

各方向的布局原则不同：

- **横版（16:9 / 4:3 / 2.35:1）** —— Z 字形视觉流，多列 / 左右分栏 / 网格布局，40-80px 边距
- **竖版（3:4 / 9:16）** —— 自上而下流动，单列 / 上下分栏 / 卡片堆叠，60-120px 边距
- **方形（1:1）** —— 中心放射，约 800px 核心区域，60-100px 边距

每种格式还有特定的设计约定（PPT 的页码位置、小红书的品牌区、Stories 的安全区）——这些在 `references/canvas-formats.md` 里供 Executor 使用。

---

## 模板系统与可选路径

模板是一条**可选路径**，不是默认。Strategist 阶段的默认流程是**自由设计**——开放画布，AI 完全凭源内容创造视觉系统。只有当用户显式触发时才进入模板路径：点名某个具体模板、点名某种映射到模板的品牌或风格、或问"有哪些模板"。

**为什么默认自由设计。** 模板是地板，但很容易变成天花板——它会把整个 deck 锁进模板自有的视觉惯用语。AI 擅长生成与内容节奏匹配的原创布局；把它约束在模板里，常常比让它自由设计更不贴合。所以 AI 从不主动推荐模板——用户必须自己提出。

**软提示机制。** 当源内容明显强匹配某个现有模板（学术答辩、政府报告、麦肯锡风 deck），且用户没有触发模板路径，Strategist 会发一句**非阻塞**提示：*「库里有个模板 `<name>` 跟这个场景非常贴合。需要的话说一声；否则我继续按自由设计走。」* 这是提示，不是问题——不等待，继续生成。弱匹配或模糊匹配时跳过。

**三个模板库。** `templates/` 目录托管三个角色不同的库：

| 库 | 路径 | 提供什么 | 何时使用 |
|---|---|---|---|
| 布局 | `templates/layouts/<name>/` | 整 deck 模板：SVG 页面 + `design_spec_reference.md` + 资产 | Opt-in，仅在用户触发时 |
| 图表 | `templates/charts/<name>.svg` | 可复用可视化 SVG（图表、信息图、流程图、框架图） | 每个 Executor 都引用，含图表的页面 |
| 图标 | `templates/icons/<library>/` | 三个图标库（`chunk-filled` / `tabler-filled` / `tabler-outline`）——根据内容调性每个 deck 选一个 | 每个 deck 必选其一；不能混用 |

图表库和图标库是每个 Executor 都会引用的，跟是否选了布局模板无关；布局模板才是 opt-in 的那部分。

**新建模板。** `create-template` standalone workflow 接受一份参考 PPTX，外部化它的资产，推断主题色和排版，输出 SVG 幻灯片 + manifest 到 `<pptx_stem>_template_import/`。这是一次性 ingestion 流程，不在 deck 生成流水线里。从 PPTX 原生导出 SVG 是 Windows-only（用安装的 PowerPoint COM）；macOS 走 Keynote → PDF → SVG 兜底。

---

## 角色系统：单一流水线中的三个专业代理

PPT Master 用的是**单主代理内的角色切换**，而不是并行子代理。三个角色，一份连续上下文，串行执行：

```
Strategist  →  Image Acquisition（条件触发）  →  Executor
   ↓                  ↓                                ↓
design_spec.md   images/*.png                      svg_output/*.svg
spec_lock.md     image_prompts.md                  notes/total.md
                 image_sources.json
```

Image Acquisition 阶段按每行的 `Acquire Via` 派发到两个**独立的子角色**：`ai` 行走 `image-generator`（AI 生成），`web` 行走 `image-searcher`（网络搜索）。两者按需懒加载——纯 `ai` 行的 deck 永远不会读 `image-searcher.md`。详见下面的「图片获取与嵌入」一节。

**为什么是单代理而非并行子代理？** 页面设计依赖完整的上游上下文——Strategist 的色彩选择、是否成功获取了图片资源、之前几页的视觉节奏。SKILL.md 明确禁止把页面 SVG 生成委托给子代理（全局执行纪律第 6 条）。串行逐页生成在一份连续 pass 里完成是被强制的（第 7 条）——分组（如每 5 页一批）是禁止的，因为它会加速上下文压缩并破坏视觉一致性。

**为什么用角色专属 reference 而不是一个超大 prompt？** 每个角色有自己的 `references/<role>.md`，指令聚焦。把它们全混在一个 prompt 里，会强迫模型在同一个 turn 里同时切换 Strategist 的「跟用户协商」模式和 Executor 的「产出严格 XML」模式——这两个模式想要的温度、格式纪律、容错度都不同。

**Eight Confirmations（八项确认）。** Strategist 阶段以八项打包确认（画布 / 页数 / 受众 / 风格 / 配色 / 图标 / 排版 / 图像）作为终点，作为**单一阻塞决策点**呈现给用户。确认后所有后续阶段自动运行，不再有用户卡点。这是 deck 生成流程中**唯一**的阻塞 checkpoint——其他都是程序性的。

**用户已有图片的分析（条件触发，在八项确认之前）。** 当用户随源文档一并提供了图片时，Strategist **必须**先跑 `analyze_images.py <project>/images`，再起草 `design_spec.md`。脚本提取每张图的尺寸、EXIF 方向、主色调和主体元信息，输出一份文本化摘要。Strategist 在这份摘要上做推理——SKILL.md 的图像处理规则禁止直接打开图片字节，因为 LLM 做布局决策不需要像素，需要的是能塞进一页的元数据（用宽高比定位置、用色调判定调色板兼容性、用主体决定哪页放）。输出喂入 `design_spec.md` 里的图片资源列表，让八项确认建立在真实资产上，而不是仅靠文件名猜。

**逐页 spec_lock 重读。** 生成每一页 SVG 之前，Executor 必须重读 `spec_lock.md`。这是显式的抗漂移机制，让系统能在 LLM 上下文窗口有损的情况下产出 20 页 deck 仍保持一致的色彩 / 字体 / 图标纪律。

三种 Executor 风格分散在不同的 reference 文件里——`executor-general.md` / `executor-consultant.md` / `executor-consultant-top.md`——按用户选定的风格加载。每次只加载相关风格文件加上共享的 `executor-base.md` 和 `shared-standards.md`，让上下文负载最小。

---

## 执行纪律

流水线由 SKILL.md 的全局执行纪律 8 条规则强制执行。它们看起来很官僚，但每一条都关闭了一个实际观察到的失败模式。

| # | 规则 | 禁止什么 | 为什么 |
|---|---|---|---|
| 1 | **串行执行** | 跳步或乱序 | 每一步的输出是下一步的输入；乱序会静默使用过期或缺失的输入 |
| 2 | **BLOCKING = 硬停** | 在 `⛔ BLOCKING` checkpoint（八项确认）越权决策 | 用户必须拥有设计决策权；AI 代为做主会让 deck 偏离用户意图 |
| 3 | **无跨阶段打包** | 把多个阶段合进一个 turn | 想一次性做完 Strategist + Executor 的 LLM 会在正确性或风格上漂移 |
| 4 | **进入前过门** | 在前置条件未满足时启动一步 | 每步都列出 🚧 GATE 前置条件；检查它们能阻止级联错误 |
| 5 | **无投机执行** | 提前准备后续步骤的内容（比如在 Strategist 阶段写 SVG） | 前一阶段的输出可能让那些预先准备作废；浪费上下文还制造不一致 |
| 6 | **不允许子代理生成 SVG** | 把页面 SVG 生成委托给子代理 | 页面设计需要完整的上游上下文（色彩选择、之前的视觉节奏、可用图片）；子代理开始时只有过期的部分上下文 |
| 7 | **仅串行逐页生成** | 分批生成（比如 5 页一组） | 分批会加速上下文压缩，并破坏 deck 的视觉一致性 |
| 8 | **逐页 spec_lock 重读** | 生成一页 SVG 而不重读 `spec_lock.md` | 抵抗长 deck 中的上下文压缩漂移——第 18 页的颜色必须跟第 1 页一致 |

**角色切换协议。** 当 agent 切换角色（Strategist → Executor 等）时，必须先 `read_file references/<role>.md` 并输出 markdown 标记：

```
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

这有两个作用：强制把新鲜的角色指令载入上下文（覆盖任何前一个角色模式的漂移），并在对话 transcript 中创建审计轨迹，让用户能看到 agent 何时切换了模式。

这套纪律刻意做得很显式，因为 LLM 默认行为是「让我在这一 turn 里把整个问题搞定」——而这恰好是串行流水线最不该有的形状，串行流水线要求每一步都依赖前一步**有界且过 checkpoint** 的输出。

---

## 设计规范的传播：spec_lock.md 作为执行契约

Strategist 阶段产出两份看起来冗余但服务不同对象的产物：

- `design_spec.md` —— 人类可读叙述；设计的「为什么」（目标受众、风格目标、配色理由、页面大纲）
- `spec_lock.md` —— 机器可读执行契约；Executor 必须**字面照搬**的「是什么」（HEX 颜色、确切的 font family 字符串、图标库选择、带状态的图片资源列表）

为什么两份都要？没有 `spec_lock.md` 的话，Executor 在长 deck 里会逐页重读 `design_spec.md`，LLM 上下文压缩漂移会逐渐扭曲色值和字体。`spec_lock.md` 是**抗漂移机制**——SKILL.md 强制要求生成每一页前 `read_file <project>/spec_lock.md`，让数值在 20+ 页里保持字面一致。

`update_spec.py` 把生成后的修改用两个协调步骤传播：把新值写入 `spec_lock.md`，然后字面替换到每一份 `svg_output/*.svg`。工具的范围**故意收得很窄**——只支持 `colors.*`（HEX 值，大小写不敏感替换）和 `typography.font_family`（属性级）。其他字段（字号、图标、图片、画布）**有意不支持**——它们的替换需要属性级或语义级理解，风险/收益不值得做批量传播。这些情况手动改 `spec_lock.md` 然后重做受影响的页面。

工具拒绝做备份：依赖 git 回滚。加备份机制只是重复 git 的工作，还会留下过时快照。

---

## 图片获取与嵌入

图片获取阶段是条件触发的。设计 spec 产出一份资源列表，每行图片有 `Acquire Via` 字段：`ai`（AI 生成）/ `web`（网络搜索）/ `user`（已提供）/ `placeholder`（推迟）。只有 `ai` 或 `web` 行触发这一阶段；纯 `user` 的 deck 跳过。这一阶段按每行的 `Acquire Via` 分裂为**两个独立的子角色**——`ai` 行走 `image-generator`，`web` 行走 `image-searcher`。混合 deck 同时加载两份 reference 文件，每行各走自己的路；纯 `ai` 或纯 `web` 的 deck 只加载相应的角色。

**多 backend 图像生成**（`ai` 路径）。`image_gen.py` 是 backend 注册表上的一层薄派发器。Backend 分级：

- **Core** —— 生产可用（OpenAI gpt-image / Google Imagen / MiniMax / Qwen / Volcengine / Zhipu / Gemini）
- **Extended** —— 用户按需选择的特殊模型
- **Experimental** —— API 不稳定，仅 opt-in

配置只用 **provider-specific key**（`OPENAI_API_KEY` / `MINIMAX_API_KEY` / `GEMINI_API_KEY` / ...）。`IMAGE_API_KEY` / `IMAGE_MODEL` / `IMAGE_BASE_URL` 这种 generic 字段被故意拒绝——它们在 `.env` 里配多个 provider 时会造成静默混乱。当前 backend 必须通过 `IMAGE_BACKEND=<name>` 显式选定。

**带 license 纪律的网络图片搜索**（`web` 路径）。`image_search.py` 是姊妹工具，资源列表里 `Acquire Via: web` 时使用。默认链：免配置 provider（Openverse、Wikimedia）→ 配置了 key 的 provider（Pexels、Pixabay）。License 过滤默认宽松（CC0 / PDM / Pexels / Pixabay / CC BY / CC BY-SA）——选定图片是 `attribution-required` 时 Executor 会加内联致谢。`--strict-no-attribution` 限制为零致谢的 license，用于全屏 hero image（视觉上没有放致谢的位置）。自动拒绝：任何 NC（非商用 CC BY-NC*）或 ND（禁止演绎 CC BY-ND*）。来源记录在 `image_sources.json`（provider / license / author / source URL / dimensions / attribution_text），按 filename 幂等。

**嵌入策略。** 开发期间，图片在 `svg_output/` 中保持**外部引用**——快速迭代、易于替换。`finalize_svg.py` 的 `align-images` 步骤把它们 Base64 内联到 `svg_final/`，因为 IDE / 浏览器 / preview pptx 都需要自包含文件。Native pptx 转换器**不**做 Base64 内联——它把位图文件复制到 PPTX 的 media 文件夹，并通过 `<a:srcRect>` 在 DrawingML 中表达 SVG 的 `preserveAspectRatio="... slice"` 裁剪。两条路径——外部引用便于调试，嵌入 payload 适合交付——共存是设计如此。

---

## SVG 约束：禁用特性与条件允许

PowerPoint 的 DrawingML 是 SVG 表达能力的严格子集。Executor 在一个**禁用特性黑名单**里运行，这份黑名单是从 PPT 导出失败的经验积累中归纳出来的：

**硬禁用（否则导出会坏）：**
- `<mask>` —— DrawingML 没有像素级 alpha
- `<style>` / `class` —— DrawingML 没有 CSS 选择器模型
- 外部 CSS / `@font-face` —— 字体必须系统可安装，不能用文件加载
- `<foreignObject>` —— SVG 内嵌 HTML 没有 DrawingML 映射
- `<symbol>` + `<use>` 的通用复用 —— DrawingML 没有 symbol 模型（图标 `<use data-icon>` 是项目内部约定，会在转换前展开，不算 symbol）
- `textPath` —— 文字沿任意路径没有 DrawingML 原语
- `<animate*>` / `<set>` —— SVG 动画；PowerPoint 动画是单独的时序模型，写在 slide XML
- `<script>` / 事件属性 / `<iframe>` —— 交互性是另一层

**XML 良构性：**
- 所有文本和属性值的排版字符（`—` / `→` / `©` / NBSP）必须用**裸 Unicode**——HTML 命名实体（`&mdash;` / `&rarr;`）在 SVG 里是非法 XML
- XML 保留字符（`& < > " '`）必须用 XML 实体（`&amp;` 等）——裸 `R&D` 直接终止导出

**条件允许（精确约束集见 `references/shared-standards.md`）：**
- `<line>` / `<path>` 上的 `marker-start` / `marker-end` —— 仅当 marker 形状能干净映射到 DrawingML 三种箭头原语之一（triangle / diamond / oval），且 marker 填色与 line stroke 颜色匹配
- `<image>` 上的 `clip-path` —— 仅当 clip 形状是单一 circle / ellipse / rect / path / polygon 时允许，映射到 DrawingML picture 几何。非 image 元素上的 clip 是禁用的（一个 rect 被 clip 成 circle 不如直接是个 circle）

**效果路由。** 因为 `<mask>` 被禁，常见视觉效果走不同的路：

| 效果 | 替代方案 |
|---|---|
| 图片渐变叠加（vignette / fade / 着色） | 堆叠 `<rect>` + `<linearGradient>` / `<radialGradient>` |
| 非矩形图片裁剪 | `clipPath` 作用于 `<image>` |
| 内发光 / 软边 | `<filter>` + `<feGaussianBlur>` |
| 投影 | filter shadow 或分层 rect |
| 像素级 alpha（文字镂空填充、任意 alpha 合成） | **PPT 没有路径**——在 Image Acquisition 阶段烘焙到源图 |

`svg_quality_checker.py` 在后处理之前强制执行这份黑名单——任何禁用特性都是阻塞错误，必须由 Executor 重新生成相关页面来修复。

---

## 质量门

`svg_quality_checker.py` 在 Executor 完成所有页面之后、任何后处理之前运行。位置是有意安排的：后处理会重写 SVG（图标嵌入、图片内联），会掩盖源级别的违规。检查器只读 `svg_output/`。

**它检查什么：**

- **`viewBox`** —— 存在且匹配项目的 canvas 格式。不匹配会让脚本默认的「画布是规范像素空间」假设静默失效。
- **禁用特性** —— SVG 黑名单的每一条（mask / style / class / foreignObject / symbol+use / textPath / @font-face / animate* / script / iframe）。任何命中都是阻塞错误。
- **width/height 一致性** —— `<svg>` 根属性匹配 viewBox 维度。
- **换行结构** —— 多行 `<text>` 用定位的 `<tspan>`（带 x + dy），而不是 `\n` 字符或兄弟 text 漂移。
- **spec_lock 漂移** —— SVG 中的颜色 / 字体 / 图标 / 图片必须来自 `spec_lock.md`。off-spec 值是 warning（有时合理）或 error（暗示 Executor 跑偏了）。
- **低分辨率图片 / 非 PPT 安全字体尾部** —— soft warning；能直接修就修，否则确认后放行。

**严重性模型：** error 阻塞流水线（重新生成出错的页面）；warning 提示但不阻塞。**有意没有 auto-fix 模式**——修复一个禁用特性需要 Executor 在上下文里重新写页面，不是机械的 patch。

**为什么需要这层。** LLM 生成的 SVG 不是确定性的。没有检查器的话，禁用特性会在长 deck 中悄悄混入，只在 `svg_to_pptx` 中途崩或 PowerPoint 静默丢元素时才暴露。检查器把「PowerPoint 导出在第 14 页崩溃」转化为「Executor 在第 14 页用了 `<style>`，重新生成它」——诊断速度提升一个数量级。

质量检查器也是**图表坐标验证**（`verify-charts` workflow）的天然插入点。图表页面有几何正确性需求（柱状图高度 / 饼图扇形角 / 坐标轴刻度位置），这些不是结构问题，SVG 合法性规则也抓不到。`svg_position_calculator.py` 从数据计算期望坐标，workflow 让 AI 对比并修复不一致，再继续后处理。

---

## 后处理流水线

> 工程化转换阶段中每一份产物和每一个模块为何存在，删除它会破坏哪些工作流。在考虑简化 `svg_final/` / `finalize_svg.py` / `svg_to_pptx.py` 之前，先读这一节。

### 四份产物，四种工作流

后处理阶段产生四份产物。每一份都服务于一种流水线中无法替代的工作流。

| 产物 | 服务的工作流 | 为何无可替代 |
| --- | --- | --- |
| `svg_output/` | 唯一源、手工编辑入口、`update_spec.py`、`svg_quality_checker.py` | 流水线中唯一**手写**而非派生的目录 |
| `svg_final/` | IDE 内即时预览（VSCode/Cursor 直接打开 `.svg`）、浏览器单页预览 | `.pptx` 在 IDE 里打不开；`svg_output/` 因图标 / 图片是外部引用，IDE 中渲染不完整 |
| `exports/<name>_<ts>.pptx`（native） | 主交付物——PowerPoint 中以 DrawingML 形状形态可编辑 | 唯一一份用户可在 PowerPoint 中原生改尺寸 / 改色 / 改样式的产物 |
| `backup/<ts>/<name>_svg.pptx`（preview） | 跨平台单文件分发、整体多页浏览、邮件附件 | 自包含、多页、PowerPoint / Keynote / WPS / LibreOffice 都能直接打开；`svg_final/` 是文件夹，分发不便 |

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

### FAQ ——「这个能删吗？」

| 问题 | 简答 | 原因 |
| --- | --- | --- |
| 能删 legacy / preview pptx 吗？ | **不能** | 跨平台单文件分发、多页整体浏览备份——这两种工作流，`svg_final/`（文件夹）和 native pptx 都满足不了 |
| 能删 `svg_final/` 吗？ | **不能** | IDE 内即时预览—— `.pptx` 在 VSCode / Cursor 里打不开；`svg_output/` 因外部引用在 IDE 中渲染不完整 |
| 能删 `finalize_svg.py` 吗？ | **不能** | `svg_final/` 没有其他生成入口；子模块仍被 native 转换器在内存中复用 |
| 能删 `svg_finalize/{flatten_tspan, embed_icons}` 吗？ | **不能——native pptx 会坏** | 见「两种消费者」一节 |
| 能删 `svg_finalize/{crop, embed, fix_image_aspect}_images.py` 吗？ | **不能** | `align_embed_images.py` import 它们 |
| 能删 `svg_rect_to_path.py` 吗？ | **可以考虑** | 仅为 PowerPoint 手动「Convert to Shape」圆角兜底而保留；价值边缘；目前留着是为了避免少数手动场景下静默回归 |

### 编辑规则

- 只编辑 `svg_output/` —— `svg_final/` 每次运行 `finalize_svg.py` 都会重新生成
- 编辑完 `svg_output/` 后，重跑 `finalize_svg.py` 让 IDE 预览的 `svg_final/` 同步刷新
- `update_spec.py` 只动 `svg_output/` —— spec 改完后重跑 `finalize_svg.py`，让 `svg_final/` 反映变更

---

## Native PPTX 转换器内部

`svg_to_pptx/` 把 SVG 翻译成 DrawingML，逐元素地。映射表很大——用户面向版本看 `references/shared-standards.md`——但架构是这样的：

```
svg_output/*.svg
    ↓
[parse 成 ElementTree]
    ↓
[内存中预处理]
   ├─ use_expander       ← svg_finalize.embed_icons
   └─ tspan_flattener    ← svg_finalize.flatten_tspan
    ↓
[逐元素派发]  drawingml_converter.convert_element(child, ctx)
    ├─ rect / circle / ellipse / line  → prstGeom（preset 形状）
    ├─ rect with rx==ry                → prstGeom roundRect（带 adj 值）
    ├─ rect with rx!=ry                → custGeom（每 90° 弧用 Bézier）
    ├─ path                            → custGeom（path 命令 → moveTo/lnTo/cubicBezTo/arcTo）
    ├─ polygon / polyline              → custGeom
    ├─ text                            → txBody，run 级格式化
    ├─ image                           → blipFill picture，slice 裁剪用 srcRect
    └─ g                               → grpSp（group），嵌套 xfrm
    ↓
pptx_builder 拼装幻灯片 → exports/<name>_<ts>.pptx
```

**为什么是逐元素派发而不是整体翻译？** SVG 的层级模型干净地映射到 DrawingML 的 group / shape / picture 类型。元素级派发让每种形状都有自己窄的翻译器（`drawingml_elements.py` 约 1500 行聚焦的转换器），可单独调试和测试。没有全局的 SVG-to-PPTX 优化器——每个形状独立转换，最终 PPT 文件的质量是这些局部转换的总和。

**两个内存中的预处理步骤。** Native pptx 直接读 `svg_output/`（不经 `svg_final/` 中转），但 DrawingML 不能内联处理两种 SVG 特性：

- `<use data-icon="...">` 占位符——DrawingML 不识别 `<use>`，所以 `use_expander.py` 调用 `svg_finalize.embed_icons` 在内存中把它们展开为原始 path 后再派发
- 定位的 `<tspan>`（带 x / y / 非零 dy）——DrawingML 文本块无法在段落中跳位置；`tspan_flattener.py` 调用 `svg_finalize.flatten_tspan` 把每个定位 tspan 提升为独立的 `<text>` 元素

这就是上面「后处理流水线」一节描述的「内存消费者」关系。

**Office 兼容模式（默认开启）。** 2019 之前的 PowerPoint 不能原生渲染 SVG。转换器为每页生成一份 PNG 兜底（通过 svglib + reportlab）并嵌入为 fallback，与原生形状并存。新版 Office 仍然显示可编辑形状；旧版显示 PNG。`--no-compat` 关闭这层兜底。

---

## 动画与转场模型

PPT Master 映射两层运动：

**页面转场**（`-t` 标志）—— 应用在幻灯片之间。可用效果：`fade`（默认）/ `push` / `wipe` / `split` / `strips` / `cover` / `random`。在 slide XML 中实现为 `<p:transition>` 元素。`none` 关闭。

**逐元素入场动画**（`-a` 标志）—— 应用在顶层 `<g id="...">` group 上，按 z 序。默认 `mixed` 在精选的可见效果池中确定性循环（每页第一个 group 总是 `fade`，然后跨 deck 多样化）以提供视觉变化而无需逐页配置。其他选择：单一具名效果、`random`、或 `none`。

为什么锚点在顶层 `<g>` group？PowerPoint 的动画时序基于形状 ID——每个被动画的对象需要稳定的 shape ID。顶层 group 是自然的粒度（一个逻辑内容块对应一个 group），而且 Executor 本来就被强制要求用 `<g id="...">` 分组（用户记忆规则）。每页 3-8 个内容 group 比较合理；没有顶层 group 的页面 fallback 到顶层可见原语，上限 8 个。

**页面装饰自动跳过。** 动画跳过 `id` 匹配 `background` / `header` / `footer` / `decoration` / `watermark` / `page_number` 等 token 的 group——这些是静态画面元素，不应该飞入。

**起始模式**（`--animation-trigger`）镜像 PowerPoint 动画窗格的 Start 下拉菜单：

- `after-previous`（默认）—— 进入幻灯片时级联，间隔由 `--animation-stagger` 控制（默认 0.5 秒）。无需点击。
- `with-previous` —— 所有 group 在进入幻灯片时一起开始
- `on-click` —— 每个 group 一次点击，演讲者节奏控制

**录制旁白。** 视频导出的可选层。`notes_to_audio.py` 从 `notes/*.md` 生成逐页音频（默认 edge-tts；云 TTS provider 如 ElevenLabs / MiniMax / Qwen / CosyVoice 可选）。`svg_to_pptx --recorded-narration audio` 逐页嵌入音频，并按每个片段时长设置自动推进时序，产出可被 PowerPoint 用「使用录制的时序和旁白」选项导出为视频的 deck。

完整的动画效果列表、锚点逻辑、装饰跳过 token 在 `references/animations.md`。

---

## Standalone Workflows（独立工作流）

仓库随附四个**不在主 deck 生成流水线里**的工作流。每个都是 opt-in 的，由特定的用户需求或内容形态触发，独立于 Strategist → Executor 主流程运行。

| 工作流 | 路径 | 何时使用 |
|---|---|---|
| `create-template` | `workflows/create-template.md` | 一次性 ingestion：把参考 PPTX 转成 `templates/layouts/` 下的可复用模板 |
| `verify-charts` | `workflows/verify-charts.md` | **仅当** deck 含数据图表（柱 / 折 / 饼 / 雷达）时，在 Executor 与后处理之间插入。校准 AI 在数据→像素映射上常见的 10–50px 偏差 |
| `visual-edit` | `workflows/visual-edit.md` | 导出后迭代。当用户模糊指出"哪里看着不对"时，工作流打开浏览器可视化编辑器做精细编辑。如果用户描述足够具体可以直接修改，则跳过 |
| `generate-audio` | `workflows/generate-audio.md` | 视频导出用的录制旁白。选 TTS 后端（默认 edge-tts；云端 ElevenLabs / MiniMax / Qwen / CosyVoice 可选），从 `notes/*.md` 生成逐页音频；可选地用 `--recorded-narration audio` 重新导出 PPTX，让 PowerPoint 视频导出用录制好的时序 |

**为什么这些是 workflow 而不是流水线步骤。** 每一个解决的都是范围明确、不适用于大多数 deck 的问题：

- `create-template` 是每个模板一次性的设置活动，不是每个 deck 都要做
- `verify-charts` 只对含数据可视化的 deck 才有意义
- `visual-edit` 是被动响应（针对具体投诉），不是主动行为
- `generate-audio` 是下游附加（视频导出），不是 deck 构造的一部分

把任何一个塞进默认流水线，要么对大多数用户运行无意义的步骤（增加延迟和失败面），要么强制一刀切收窄。保持 opt-in 让主流水线保持紧凑，同时在用户需要时仍提供这些能力。每个 workflow 有自己自包含的 `workflows/<name>.md`，agent 按需加载——没有 agent 必须提前查的全局注册表。
