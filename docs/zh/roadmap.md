# Roadmap

[English](../roadmap.md) | [中文](./roadmap.md)

---

> PPT Master 是单人维护的开源项目，按**优先级**而非时间表推进。这份 roadmap 用来统一对外预期：已经做了什么、在持续维护演进什么、暂时不打算做什么。优先级会随用户反馈和实际使用信号调整，不承诺时间窗口。
>
> 项目当前定位：**AI 从零生成 SVG → DrawingML 原生可编辑 PPTX**。这条路线的核心是「跨四渲染器的位置保真 + 真原生形状」，所有方向都围绕这条主轴展开。

---

## 近期能力演进

近两个月的能力面扩张。只列结构性的，单 flag / 增量优化看 commit log。

### 2026-03（真原生 PPTX 路线成型）

- **直接导出原生可编辑 PPTX** — `svg_to_pptx` 补齐 glow / rotate / text-decoration / stroke-linejoin，整条 SVG → DrawingML 链路开始可用
- 图表 / 布局模板 JSON 索引上线，AI 选型路径打通

### 2026-04（管线规模化）

- **无源生成**：`topic-research` 工作流支持「只给主题、不给源文件」
- **PPTX 导出质变**：SVG clipPath → DrawingML picture geometry、marker → 原生箭头、输出归集到 `exports/`
- **图表库 70 个 + 图标三库**（simple-icons / phosphor-duotone / brand-logo）
- **`spec_lock.md` 机器可读契约**：Strategist 锁定后 Executor 每页强制重读，跨页一致性有了保证
- **元素级动画默认开启** + 旁白音频 / 视频导出([`workflows/generate-audio.md`](../../skills/ppt-master/workflows/generate-audio.md))

### 2026-05（视觉编辑 + AI 图系统化）

- **Live Preview 进入主流程**（[`workflows/live-preview.md`](../../skills/ppt-master/workflows/live-preview.md)） — 浏览器实时预览 + 点选元素写要求 + 「apply my annotations」让 AI 重做该区域（基于 [@WodenJay](https://github.com/WodenJay) [PR #85](https://github.com/hugohe3/ppt-master/pull/85)）
- **任意 PPTX 复刻为模板**（[`workflows/create-template.md`](../../skills/ppt-master/workflows/create-template.md)） — PPTX → SVG 逆向 + OOXML 主题 / 母版 / 版式 / 资源提取
- **AI 图三维系统** rendering × palette × type + Strategist h.5 锁定，下游消费固定契约
- **AI 图 `hero_page` 双档** — 局部插图 + 整页主角图共存
- **品牌身份预设子系统**（[`workflows/create-brand.md`](../../skills/ppt-master/workflows/create-brand.md)） — 提取并复用品牌色板 / 字体 / Logo / 语调
- **视觉自检工作流**（[`workflows/visual-review.md`](../../skills/ppt-master/workflows/visual-review.md)） — 按 rubric 逐页自查 AI 生成的 SVG
- **AI 图 Type 概念边界澄清** — Type 收窄回「local 信息图的内部几何骨架」(11 个真骨架);原 4 个伪 type (hero/background/portrait/typography) 折回 `page_role: hero_page` + 4 条构图通则(single-subject / portrait / typographic / atmospheric);hero_page 文字分层规则(关键视觉词 embedded、可改文字走 SVG)
- **Brutalist AI 报章示例 deck 交付**（[`examples/ppt169_brutalist_ai_newspaper_2026/`](../../examples/ppt169_brutalist_ai_newspaper_2026/)） — P0 三档第一档落地：满版小字 + 不规则栏宽 + halftone 黑白图 + 单点红 + 真原生 shape，10 页编辑部年报实压「文字位置精度 + 跨页一致性」
- **Kubernetes Blueprint 示例 deck 交付**（[`examples/ppt169_kubernetes_blueprint_2026/`](../../examples/ppt169_kubernetes_blueprint_2026/)） — P0 三档第二档落地：等距工程图美学 + 蓝图青/琥珀色板 + 全手写 SVG 几何（无 raster 图）+ 自定义"逐笔绘制"动画，10 页 Kubernetes 架构走读实压「几何形状泛化 + chart 结构扩展性」
- **AI 图 `custom` 兜底出口** — `rendering` / `palette` / hero 构图三处允许声明 `custom` + 一段 `*_behavior` prose，替换原"找不到匹配就硬塞 vector-illustration / cool-corporate"的假兜底；端到端契约：[`image-renderings/_index.md`](../../skills/ppt-master/references/image-renderings/_index.md) §1.5 + [`image-palettes/_index.md`](../../skills/ppt-master/references/image-palettes/_index.md) §2 + Strategist h.5 hard-rule（每维 ≤1 custom，单候选可双 custom）+ spec_lock 字段 + Image_Generator Step 2 消费分支
- **Template 架构三分类收口**（[`docs/zh/templates-architecture.md`](./templates-architecture.md)） — brand / layout / deck 三独立目录 + 每类独立 schema + 段级合成 + git-style 冲突解决；SKILL.md Step 3 按 kind 分支处理，触发规则仍是「显式路径才触发」
- **Pattern 填充 PPTX 安全网** — `svg_quality_checker.py` 现在对未标 `data-pptx-pattern` 的 `<pattern>` 元素发 warning（会静默回退 `ltUpDiag` 斜纹）、对超出 OOXML `ST_PresetPatternVal` 枚举的值发 error（schema 校验失败 PPT 无法打开）；`shared-standards.md §7` 落地了完整 preset 清单和 `<rect fill="<bg>"/>` 子元素约定
- **LaTeX 数学公式渲染上线**（[`scripts/latex_render.py`](../../skills/ppt-master/scripts/latex_render.py)） — Strategist 在 Typography 确认中锁定 `mixed` / `render-all` / `text-only` 三档策略，显式写 `images/formula_manifest.json`；脚本走 codecogs → quicklatex → mathpad → wikimedia 四源 fallback chain，输出透明 PNG 进 §VIII 表的 `Acquire Via: formula` / `Status: Rendered` 行；公式密集型 deck（学术 / 工程 / 教学）首次拥有原生渲染路径，规则面禁止扫源文件 `$...$` 自动渲染（公式选取是 Strategist 决策）
- **实时预览直接编辑 — L1 / L2 / L3**（[`workflows/live-preview.md`](../../skills/ppt-master/workflows/live-preview.md)） — 浏览器编辑器新增无需 AI 往返的确定性就地编辑：文字内容（L1）、fill / stroke / font-size 等样式属性（L2）、以及画布上的几何操作（L3）——在选中元素上拖拽即移动、方向键微调（`Shift` = 10px）、多选、加右键重叠选择器选取堆叠元素。编辑支持 `Ctrl+Z` 撤销 + 合并，点 **Apply changes** 写回 `svg_output/`；移动经 finalize / 导出保位（移动的 text、提升的多行 tspan、重定位的 icon 都在 PPTX 中如实再现）。重新导出仍由对话触发；画布上的缩放手柄尚未实现（缩放走几何输入框）

### 2026-06（讲解 mode 与视觉风格双 catalog 化）

- **三个 executor 退役 → mode + visual-style 双 catalog**（[`references/modes/`](../../skills/ppt-master/references/modes/) + [`references/visual-styles/`](../../skills/ppt-master/references/visual-styles/)） — 原三个 `executor-*.md`（general / consultant / consultant-top）把「领域 · 受众 · 说服 · 叙事」捆在一条线；拆成两个正交 catalog（照 `image-renderings` 范式：扁平目录 + `_index` + 按需读 + Strategist 锁一个）。**mode** = 讲解骨架（`pyramid` / `narrative` / `instructional` / `showcase`，consultant + top 因叙事内核相同合并为 pyramid）；**visual-style** = SVG 排版美学（`swiss-minimal` / `editorial` / `soft-rounded` / `dark-tech`，各 paired 一个 image-rendering，**零 HEX**——颜色真值守在 confirmation e + image-palettes）。Strategist `§d` 双层独立锁定 `mode` + `visual_style` 进 `spec_lock`，Executor 加载两个 locked 文件；任意 mode × 任意 style 自由组合，渲染坐标仍留 `templates/charts/`
- **提示词约束强度三档解耦**（[`docs/rules/prompt-style.md`](../rules/prompt-style.md) §4） — 规则（`Hard rule` / `Forbidden`）/ 默认（`Default — … may override`）/ 参考（`Reference — not a constraint`）三档显式化 + 「客观失败 vs 品味」判据 + checker 边界，让模型对「该守 vs 可破」一目了然；visual-style catalog 全程用 Reference 强度
- **visual-style catalog 扩充至 18 个，与 image-renderings 对齐 + 示例库回收** — 先从[示例库](../../examples/)提炼 4 个（`brutalist` / `blueprint` / `memphis` / `zine`），再补齐 [`image-renderings`](../../skills/ppt-master/references/image-renderings/) 里有排版对应物的手绘 / 纹理风格 6 个（`sketch-notes` / `ink-notes` / `chalkboard` / `paper-cut` / `vintage-poster` / `pixel-art`），再回收示例库里仍未覆盖的独立气质：`ink-wash`（新中式水墨留白，源 藏拙 / 李子柒）· `glassmorphism`（深底磨砂玻璃 + 流光，源 glassmorphism_demo，从 soft-rounded 独立）· `photo-editorial`（满版摄影主导、文字点题，源 Pritzker / fashion_weekly）· `data-journalism`（Bloomberg/Economist 新闻信息图，多栏微图表 + 数据侧栏，源 global_ai_capital）。catalog 重组为 5 组（企业产品 / 编辑出版 / 表现印刷 / 手绘笔触 / 特殊）。**关键判据**：一个 rendering 升 visual-style 的前提是它定义「整页版面语言」而非「插入图的样子」——故 corporate-photo「摄影主导版面」该建（photo-editorial），而 nature / warm-scene / fantasy-animation 等纯氛围 rendering 仍只配对、不单建。全程零 HEX、Reference 强度
- **mode catalog 扩档至 5 个：加 `briefing`** — 补上「中性信息平铺」这一格：无论点 / 无故事 / 不教学 / 不冲击，topic 标题、等权铺事实、完整可扫读，服务周报 / 参考册 / 目录 / 会议材料 / FAQ 这类「只告知不论证」的 deck。五个 mode 自此更接近 MECE 地切分**表达意图**：说服（pyramid）· 讲故事（narrative）· 教会（instructional）· 震住（showcase）· 只告知（briefing）。`_index` 加了 `briefing` vs `pyramid` 的灰区判据（「要不要造个 thesis 才塞得进 pyramid → 那就是 briefing」）。五个预设之外加一个 `custom` 兜底，承接预设盖不住的 bespoke 方向（特殊节奏 / 多 mode 融合 / 特定姿态）——用户点名**或策略师推荐**皆可，与所有锁一样由用户确认；一份 deck 永远只锁一个值，融合=一个 custom 描述多幕。唯一要避免的是「预设明明贴合却图省事甩 custom」。这与「用户自带大纲 / 方向覆盖 mode」是同一条真值优先原则

---

## 进行中 / 下一步

明确在做或下一步要做的方向，不承诺时间窗口。

- **mode catalog 边界打磨** — 5 个讲解骨架（pyramid / narrative / instructional / showcase / briefing）已覆盖主要表达意图；后续主要是边界灰区的持续打磨，暂无新增计划

---

## 持续维护方向

不承诺时间窗口的长期改进项。只列真方向，具体修复 / 单 flag 看 commit log。

- **Prompt 精简** — 在不降质量的前提下压缩各角色 prompt 的 token 占用、提升缓存命中率，带来间接的成本 / 速度改善。与下面「纯速度优化」一节互补：做间接优化，不做牺牲质量的提速。

---

## 明确不做（Non-goals）

下面这些方向被多次提过，已经评估并决定**不做**。列出来不是否定需求价值，而是说明它们与本项目主路线不匹配；如果你刚好需要这些能力，建议看其他工具或 fork 本项目走自己的路。

### 读取任意 PPTX 模板 → 仅填充文字

**对应 Issue**：[#53](https://github.com/hugohe3/ppt-master/issues/53)、[#118](https://github.com/hugohe3/ppt-master/issues/118)

PPT Master 主路线是「AI 从零生成 SVG → DrawingML」，整条管线围绕完全可控的形状/文字/版式构建。「解析既有 PPTX 占位符 + 仅回填文字」是另一种产品形态，需要处理任意来源的母版 / 主题 / 占位符体系，与现有架构发力点正交。

**基础诉求其实很简单**：如果只是「固定位置替换 Excel 数据到 PPT 模板」，直接让 AI 写一段 `python-pptx` 脚本即可，几行代码搞定，不需要本项目这套管线。

### 改用原生 PowerPoint 图表（Excel-native chart）

**对应 Issue**：[#99](https://github.com/hugohe3/ppt-master/issues/99)、[#100](https://github.com/hugohe3/ppt-master/issues/100) 类

跨四渲染器（PowerPoint / Keynote / LibreOffice / WPS）的位置保真是项目主轴。改用 PowerPoint 原生图表会让「像素级一致性」破功——同一个 PPTX 在不同渲染器里图表会显示不同布局。图表用 SVG 是 **by design**，不是能力缺失。

如果需要数据驱动的原生 Excel 图表，建议另选工具或在导出后用 PowerPoint 手动替换；本项目不会内置这条路径。

### uv 作为默认 / 必需依赖

**对应 Issue**：[#111](https://github.com/hugohe3/ppt-master/issues/111)

`pip + requirements.txt` 是唯一官方安装路径，因为它在所有 Python 环境下都可用、不需要额外学习成本。uv 是好工具，但「让 uv 成为默认」会抬高新用户的入门门槛。如果你个人偏好 uv，完全可以在 fork 里用，不影响主线。

### 纯速度优化

**对应 Issue**：[#97](https://github.com/hugohe3/ppt-master/issues/97)

成本 / 速度 / 质量三角下，本项目选择**质量优先**。20 分钟生成一个高质量 PPTX 是当前的合理点。

会做：通过 prompt 精简 / 缓存命中率提升带来的间接改善；
不会做：以牺牲质量为代价的「随便几页应付交差」式提速。

如果对速度敏感且能接受质量下降，Gamma / 美图 AI 等竞品更合适。

### CLI / SaaS / 桌面 App 形态

产品形态明确为 **chat-driven AI IDE skill**（Claude Code / Cursor / VS Code + Copilot / Codebuddy）。

不会做：独立 CLI（`ppm` 之类）、SaaS Web 服务、Electron 桌面壳。所有「让它脱离 chat 独立运行」的提案都会被拒。chat 是交互核心，不是包装层。

---

## 反馈渠道

- **Issues**：[github.com/hugohe3/ppt-master/issues](https://github.com/hugohe3/ppt-master/issues) — 报告 Bug / 提建议
- **Discussions**：[github.com/hugohe3/ppt-master/discussions](https://github.com/hugohe3/ppt-master/discussions) — 用法讨论 / 经验分享
- **邮箱**：heyug3@gmail.com

提需求前先扫一眼上面的 **Non-goals**；如果你的需求落在那一节，多半不会被采纳，但欢迎讨论是否还有别的路径解决你的真实问题。
