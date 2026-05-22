# Roadmap

[English](../roadmap.md) | [中文](./roadmap.md)

---

> PPT Master 是单人维护的开源项目，按**优先级**而非时间表推进。这份 roadmap 用来统一对外预期：正在做什么、想做什么、暂时不打算做什么。优先级会随用户反馈和实际使用信号调整，不承诺时间窗口。
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
- **Template 架构三分类收口**（[`docs/zh/templates-architecture.md`](./templates-architecture.md)） — brand / layout / deck 三独立目录 + 每类独立 schema + 段级合成 + git-style 冲突解决；SKILL.md Step 3 按 kind 分支处理，触发规则仍是「显式路径才触发」
- **Pattern 填充 PPTX 安全网** — `svg_quality_checker.py` 现在对未标 `data-pptx-pattern` 的 `<pattern>` 元素发 warning（会静默回退 `ltUpDiag` 斜纹）、对超出 OOXML `ST_PresetPatternVal` 枚举的值发 error（schema 校验失败 PPT 无法打开）；`shared-standards.md §7` 落地了完整 preset 清单和 `<rect fill="<bg>"/>` 子元素约定

---

## P1 — 想做但未排期

### 1. AI 图 Mood 独立维度

当前 palette 文件里同时承担「色相」「饱和度」「对比度」三类属性，文件偏长。计划抽出独立 Mood 维度（subtle / balanced / bold），palette 文件瘦身。

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
