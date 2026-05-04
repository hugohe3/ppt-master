# 技术路线

[English](../technical-design.md) | [中文](./technical-design.md)

---

## 设计哲学 —— AI 是你的设计师，不是完工师

生成的 PPTX 是一份**设计稿**，而非成品。把它理解成建筑师的效果图：AI 负责视觉设计、排版布局和内容结构，交付给你一个高质量的起点。要想获得真正精良的成品，**需要你自己在 PowerPoint 里做精装修**：换掉形状、细化图表、调整配色、把占位图形替换成原生对象。这个工具的目标是消除 90% 的从零开始的工作量，而不是替代人在最后一公里的判断。不要指望 AI 一遍搞定所有——好的演示文稿从来不是这样做出来的。

**工具的上限是你的上限。** PPT Master 放大的是你已有的能力——你有设计感和内容判断力，它帮你快速落地；你不知道一个好的演示文稿应该长什么样，它也没法替你知道。输出的质量，归根结底是你自身品味与判断力的映射。

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

源文档（PDF / DOCX / EPUB / XLSX / PPTX / 网页）在流水线启动前先被归一化为 Markdown——这是 Strategist 阅读的事实源。两个设计选择塑造了转换器：

**Native-Python 优先，外部二进制兜底。** 常见格式由纯 Python wheel 处理，pandoc 仅在长尾的小众格式时才被调用。让每个用户都去装一份可能没有权限装的系统级二进制是一种可用性税，而 95% 的输入是 docx / pdf / html，付这种税不划算。

**TLS 指纹模拟应对高安全站点。** 网页抓取默认模拟 Chrome TLS 指纹。微信公众号和不少 CDN 直接屏蔽 Python 默认 `requests` 握手；用一个依赖把这事一并解决，比维持一份 Node.js 抓取器作为主路径更划算。

---

## 项目结构与生命周期

项目布局里非显然的一点是 `import-sources` 的**非对称默认**：仓库**外**的文件默认 *copy*（保留用户原件），仓库**内**的文件默认 *move*（避免中间产物被误提交）。这种不对称恰好对应自然的风险画像——仓库外的文件一般是用户资产、不该动；仓库内的文件一般是临时产物、应该清理。一个统一默认无论选 copy 还是 move，每次都会在另一种场景出错。

---

## Canvas 格式系统

PPT Master 不只服务 PPT——同一套 SVG → DrawingML 流水线还能产出方形海报、9:16 故事、A4 印刷品。各格式特定的约定（比例、安全区、品牌区等）住在 [`references/canvas-formats.md`](../../skills/ppt-master/references/canvas-formats.md)。

值得标注的架构选择：**viewBox 是像素，不是绝对单位。** 像素空间让 AI Executor 思考布局没有歧义（`x="100"` 就是左缘 +100px），人类在浏览器里检查也直接。到 EMU 的换算只在导出时发生一次——选像素意味着流水线的其余环节（Strategist、Executor、质量检查、后处理）永远不需要在 EMU 思维下工作，那对 AI 生成和人类调试都是敌对的。

---

## 模板系统与可选路径

模板是**可选项，不是默认**。Strategist 默认走自由设计——AI 完全凭源内容创造视觉系统。模板路径只在用户显式触发时启用。

**为什么默认自由设计。** 模板是地板，但很容易变成天花板：它会把整个 deck 锁进模板自有的视觉惯用语，无视内容本身想要怎样被呈现。自由设计的布局从源内容的结构推导而来，而不是从一套固定语法套上去——视觉节奏跟着内容走，而不是跟内容打架。约束模式在窄场景里确实更好（品牌锁定的 deck、强类型场景如学术答辩或政府报告），所以它一直在；但 AI 不主动去抓，是用户去抓。

**软提示，不是软追问。** 当内容明显匹配某个模板而用户又没触发时，Strategist 发一句非阻塞的提示就继续按自由设计走。这里之所以是提示而不是问题：每次"也许你想用模板"都打断流，会侵蚀默认节奏；而用户随时可以中途打断，没有信息损失。

**布局是 opt-in，图表和图标不是。** 这种不对称不是矛盾——*布局*正是锁定视觉惯用语的那一层（地板/天花板问题），而图表和图标是不会施加 deck 级风格约束的复用原语。同一个 `templates/` 目录，但在视觉契约里扮演的角色不同。

---

## 角色系统：单一流水线中的三个专业代理

PPT Master 用的是**单主代理内的角色切换**，不是并行子代理。这个选择有三条互相支撑的理由：

**为什么是单代理而非并行子代理。** 页面设计依赖完整的上游上下文——Strategist 的色彩选择、图片资源是否成功获取（还是失败被替代）、之前几页的视觉节奏。子代理拿到的只能是这个上下文的过期局部快照，产出的 deck 视觉会逐页漂。同一逻辑也禁止分批生成（比如一次 5 页）：分批加速上下文压缩，deck 的视觉一致性下降速度比节省的速度更快——不划算。

**为什么是角色专属 reference 而不是一个超大 prompt。** Strategist 跑的是「跟用户协商」模式（开放式、对话式、可以回退），Executor 跑的是「产出严格 XML」模式（不准即兴、不准漏属性）。把两者塞进同一个 prompt，强迫模型在同一个 turn 里持守相互矛盾的纪律——所有混合模式的 prompt 工程病灶都会出现。按角色拆开，每个角色只加载它需要的、扔掉其他。

**Eight Confirmations 是唯一的阻塞 gate。** Strategist 阶段以八项打包确认（画布 / 页数 / 受众 / 风格 / 配色 / 图标 / 排版 / 图像）作为单一阻塞决策点呈现给用户。确认后，流水线一路跑到结束，不再有用户中断点。打包且单一的理由：设计选项之间是相关的（配色影响图标库、影响排版），一起决能产出一致的决策；分散到各阶段确认会引入互相矛盾的用户输入，最后被迫回退重做。

**用户已有图片走元数据，不读像素。** 用户自带图片时，Strategist 跑的是一个抽取器，把尺寸、EXIF 方向、主色调、主体内容总结成文本，然后基于这份文本推理。直接读图片字节是被禁的，因为 LLM 做布局决策不需要像素，需要的是能塞进一页的事实（用宽高比定位置、用色调判定调色板兼容、用主体决定哪页放）。读像素只会消耗上下文而不带来决策质量收益。

**逐页 spec_lock 重读** 是长 deck 的抗漂移机制——完整理由见下面的 § 设计规范的传播。

---

## 执行纪律

流水线由 [`SKILL.md` § 全局执行纪律](../../skills/ppt-master/SKILL.md) 中的 8 条规则强制——那份文件是权威，规则住在那里。它们看起来很官僚，但存在的理由是：LLM 默认行为是「让我在这一 turn 里把整个问题搞定」，而这恰好是串行流水线最不该有的形状——串行流水线要求每一步的输出都是有界、过 checkpoint、被下一步消费的。这套规则共同关闭了实际反复出现的失败模式：乱序执行、AI 代为做用户设计决策、跨阶段打包、前置条件未满足、投机预先准备、子代理上下文丢失、分批漂移、长 deck 色彩字体漂移。

角色切换协议（切换模式前必须 `read_file references/<role>.md`）有两个互相支撑的作用：把新鲜的角色指令载入上下文，覆盖前一模式的漂移；对话 transcript 中的可见标记构成审计轨迹，让用户能看到 agent 何时切换了模式——回看一个具体决策为什么这样做时，这条线索很关键。

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

这一阶段有三个架构层面的决策：

**provider 专属 config key，不用通用 `IMAGE_API_KEY`。** 每个 backend 用自己的 `OPENAI_API_KEY` / `MINIMAX_API_KEY` 等等，当前 backend 由显式的 `IMAGE_BACKEND=<name>` 选定。统一的 `IMAGE_API_KEY` 字段第一眼看着干净，但当用户同时配了多个 provider 又不确定哪个在生效时会造成静默混乱——这种 fault 通常只表现为「图像生成结果怪怪的」，找不到清晰失败点。强制 per-provider key 让「我现在用的是哪个 backend」从推理变成可读配置。

**默认宽松 license 过滤，配以严格模式应对没法放致谢的版面。** 网络图片搜索默认允许 CC BY / CC BY-SA 加内联致谢——大部分幻灯片都有视觉空间放一个致谢元素。`--strict-no-attribution` 是给全屏 hero image 和紧凑构图的逃生口，那些场景没法放致谢又不打破设计。NC（CC BY-NC*）和 ND（CC BY-ND*）自动拒绝，因为 PPT Master 的典型产物会用于商用或修改场景；宽松默认 + 这个底线正好对应用户实际想要的 fail-mode。

**开发期外部引用，交付期分叉成两套嵌入策略。** 在 `svg_output/` 里编辑时，图片是外部文件引用——快速迭代、单点替换。两份交付产物随后分叉：`svg_final/` 走 Base64 内联（产出一组自包含 SVG，IDE 预览、浏览器、preview pptx 都能开而不丢位图依赖）；native pptx 反过来把位图复制进 PPTX 的 media 文件夹，用 `<a:srcRect>` 表达裁剪。分叉的理由：在 DrawingML 里塞 Base64 能跑但文件膨胀 3-4 倍；文件引用的位图是 PowerPoint 原生表达方式，配 `<a:srcRect>` 的裁剪也是 DrawingML 的规范写法——任一方向用错工具都要付出可编辑性或文件大小的代价。

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

---

## Native PPTX 转换器内部

**为什么是逐元素派发而不是整体翻译。** SVG 的层级模型干净地映射到 DrawingML 的 group / shape / picture 类型——不需要一个全局优化器去重新规划幻灯片。每种形状都有自己窄的翻译器，简单到能单独调试和单元测试。一张幻灯片的最终质量等于这些独立局部转换之和；这个性质在整体翻译下脆弱，在元素派发下稳健。

**为什么 Office 兼容模式默认开启。** 2019 之前的 PowerPoint 不能原生渲染 SVG。转换器为每页生成 PNG 兜底，与原生形状并存——新版 Office 仍显示可编辑形状，旧版回退到 PNG。默认开启的取舍是：用适度的文件大小代价换取「不会静默地把打不开的 deck 交给跑老版本的用户」；逃生口给那些明确知道自己在新栈上、想要更小文件的用户。

---

## 动画与转场模型

值得讲的设计选择是动画**锚点**，不是效果列表。

**为什么把入场动画锚在顶层 `<g>` group。** PowerPoint 的动画时序基于形状 ID——每个被动画的对象需要稳定的 shape ID。给单个原语做动画会产出每页 30+ 个分别飞入的原子（动感泛滥），只给整页做动画又损失视觉叙事。顶层 group 是自然粒度：Executor 本来就被强制要求用 `<g id="...">` 标记逻辑内容块（每页 3-8 个 group），而这些块正是观众读作「一个东西到达」的单位——动画对齐了已有的逻辑结构，而不是另立门户。

**为什么页面装饰自动跳过。** 名为 `background` / `header` / `footer` / `decoration` / `watermark` / `page_number` 的 group 代表静态页面框架，不是内容；让它们飞入会让人出戏（页面本身在每次切换时具象化），几乎不会是用户想要的。按 id token 过滤原则上脆弱，实际上可靠——因为 token 词表很小，命名权又掌握在 Executor 手里。

**为什么录制旁白让自动推进时长跟着片段时长走。** 嵌入旁白意味着 deck 目标是视频导出——视频里没有演讲者去点击。把每页自动推进时长设为该页音频片段的实际时长，PowerPoint 能干净地导出为 MP4，无需人工配时。任何其他时长来源（估算朗读速度、固定每页时长）都会破坏音画同步。

---

## Standalone Workflows（独立工作流）

四个能力（`create-template`、`verify-charts`、`visual-edit`、`generate-audio`）作为独立工作流存在，而不是流水线步骤。每个都是稀疏触发的——按模板、按含图表的 deck、按一次具体抱怨、按一次视频导出，而不是按每个 deck。把任何一个塞进默认流水线，要么对大多数用户运行无意义的步骤（增加延迟和失败面），要么强制一刀切收窄主流程。保持 opt-in 让 deck 生成主流水线保持紧凑、可预期，同时在触发条件命中时仍提供这些能力；每个 `workflows/<name>.md` 是自包含的、按需加载——所以 prompt context 的开销也是 opt-in。
