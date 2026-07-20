# 路线图

[English](../roadmap.md) | [Chinese](./roadmap.md)

---

> PPT Master 是一个由个人维护的开源项目，按**优先级而非固定时间表**推进。这份路线图用来对齐预期：项目往哪个方向走、当下在做什么、哪些事等真实需求出现再做、哪些明确不做。优先级会随用户反馈和真实使用信号调整——不承诺交付时间窗口。

---

## 方向

项目的主轴是**原生深度**：逐版本创作或保留更多 PowerPoint 自身的对象模型、行为与可复用结构——持续向 PowerPoint 本身靠拢。完整论述见[项目定位章程](./project-positioning.md)；[PowerPoint ↔ SVG 映射指南](./powerpoint-svg-mapping.md)逐特性诚实记录当前边界。

这条主轴今天体现为四条显式产物路线：**Generate PPTX** 通过受约束的 SVG → DrawingML 创作全新设计的页面；**Create Template** 产出可复用的 Brand / Layout / Deck 模板工作区；**Fill Native PPTX** 与 **Enhance Native PPTX** 通过限定范围的 OOXML 操作保留既有文件包。

---

## 进行中 / 下一步

明确在做或下一步要做，不承诺时间窗口。

- **在真实 deck 上校准新落地的体系** — 多 deck 合并 intake、材料发散度、插画体系、结构化模板创作均已上线；它们现在需要的是真实使用信号，而不是更多机制。不预先加机械阈值或配额。
- **Prompt 精简** — 在不降质量的前提下压缩各角色 prompt 的 token 占用、提升缓存命中率，带来间接的成本 / 速度改善。与「纯速度优化」的边界见下方「明确不做」。

---

## 未来方向（信号驱动）

已评估为「真实需求出现时值得做」的候选项，列出来是为了公开意图，均不构成承诺。

- **持续收窄[映射指南](./powerpoint-svg-mapping.md)记录的原生覆盖缺口** — 逐版本把更多「仅 SVG」的格子推向 PowerPoint 原生结构与行为。
- **创作型预设形状的效果支持**（如原生阴影）— 等形成精确的 preset-effect 契约并补齐 checker 覆盖再做；在此之前，需要阴影的库存形状保守留普通 SVG。
- **生成侧超链接创作** — 源 deck 里已有的超链接如今能在转换中保留；让 Strategist 主动创作新链接，等需求出现再做。
- **图片页面背景提升为原生背景填充** — 纯色 / 渐变页面背景已导出为 PowerPoint 原生底色；图片背景按需求驱动。

---

## 已交付里程碑

一个月一行，细节见 [Release 发布说明](https://github.com/hugohe3/ppt-master/releases)与 commit log。

| 时间 | 主题 |
|---|---|
| 2026-03 | **原生 PPTX 路线成形** — SVG → DrawingML 链路可用；图表 / 版式模板索引上线 |
| 2026-04 | **管线规模化** — 仅凭主题生成、70 个图表模板 + 三套图标库、`spec_lock` 跨页一致性契约、逐元素动画与旁白 / 视频导出 |
| 2026-05 | **可视化编辑 + AI 图片体系化** — Live Preview 确定性原位编辑（基于 [@WodenJay](https://github.com/WodenJay) 的 [PR #85](https://github.com/hugohe3/ppt-master/pull/85)）、从 PPTX 创建模板工作区、rendering × palette × type 图片体系、LaTeX 公式渲染 |
| 2026-06 | **mode 与 visual-style 双 catalog + intake 扩展** — 5 种叙事 mode × 18 种视觉风格（+ `custom`）、内容忠实的美化 profile、多 deck 合并 intake、插画切片管线、网络图片质量闸门、源转换保真提升（图注识别基于 [@suay1113](https://github.com/suay1113) 的 [PR #191](https://github.com/hugohe3/ppt-master/pull/191)，超链接保留提炼自 [@ZhaoZuohong](https://github.com/ZhaoZuohong) 的 [PR #155](https://github.com/hugohe3/ppt-master/pull/155)） |
| 2026-07 | **定位章程 + 原生母版 / 版式 + token 效率**（[v4.0.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)）— 三段式分步确认 UI、真 `p:sldMaster` / `p:sldLayout` 导出、`--native-charts-and-tables` opt-in、动效导出加固、图表模板库压缩 |

---

## 明确不做（Non-goals）

下面这些方向被多次提过，已经评估并决定**不做**。列出来不是否定需求价值，而是说明它们与本项目产品方向不匹配；如果你刚好需要这些能力，建议看其他工具或 fork 本项目走自己的路。

### 对任意 PPTX placeholder 系统做无契约盲填

**对应 Issue**：[#53](https://github.com/hugohe3/ppt-master/issues/53)、[#118](https://github.com/hugohe3/ppt-master/issues/118)

Generate PPTX 路线围绕完全可控的新形状、文字与版式创作。结构完整的 PPTX 可以通过两种显式方式为经过确认的可复用模板包提供依据：`standard` / `fidelity` 以视觉证据为参考，创作新的 SVG 与 Master/Layout 系统；`mirror` 把来源包内实际存在的全部受支持事实物化到新工作区，包括未使用的 Layout 定义。两者都不修改来源 PPTX，也不补造缺失的设计意图。但「打开任意 PPTX 后不经规范化就盲填所有占位框」仍是另一种产品形态。

**基础诉求其实很简单**：如果只是「固定位置替换 Excel 数据到 PPT 模板」，直接让 AI 写一段 `python-pptx` 脚本即可，几行代码搞定，不需要本项目这套管线。

> **已支持边界**：Fill Native PPTX（`template-fill-pptx`）直接回填选中的源页面；Create Template（`create-template`）根据自然语言请求和来源证据，在内部推导重新创作或 mirror 物化实现；Strategist 再根据真实模板和当前内容推导 strict/adaptive 导出行为。仍不做未经审查、没有契约的任意第三方 placeholder 全自动替换。

### 把原生 PowerPoint 图表设为默认路线

**对应 Issue**：[#99](https://github.com/hugohe3/ppt-master/issues/99)、[#100](https://github.com/hugohe3/ppt-master/issues/100) 类

跨四渲染器（PowerPoint / Keynote / LibreOffice / WPS）的位置保真是项目主轴。把默认路线改成 PowerPoint 原生图表会让「像素级一致性」破功——同一个 PPTX 在不同渲染器里图表会显示不同布局。图表默认用 SVG 是 **by design**，不是能力缺失。

窄例外是 `data-pptx-replace-with` marker：受支持的数据图表与纯文本网格表格在生成时携带 PowerPoint 原生 Chart/Table 替换 payload，导出加 `--native-charts-and-tables` 才激活——供主动用跨渲染器保真换取带数据源对象及图表/表格专属编辑模型的用户使用；激活后的对象会保留 deck 的 chart-area / plot / 轴线 / 网格线 / 标签颜色与原生表格格式，不再塌回 PowerPoint 默认主题（见 [v4.0.0 发布说明](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)）。默认导出路径与可编辑的 SVG 派生形状系统不变。

### uv 作为默认 / 必需依赖

**对应 Issue**：[#111](https://github.com/hugohe3/ppt-master/issues/111)

`pip + requirements.txt` 是唯一官方安装路径，因为它在所有 Python 环境下都可用、不需要额外学习成本。uv 是好工具，但「让 uv 成为默认」会抬高新用户的入门门槛。如果你个人偏好 uv，完全可以在 fork 里用，不影响主线。

### 纯速度优化

**对应 Issue**：[#97](https://github.com/hugohe3/ppt-master/issues/97)

成本 / 速度 / 质量三角下，本项目选择**质量优先**。20 分钟生成一个高质量 PPTX 是当前的合理点。

会做：通过 prompt 精简 / 缓存命中率提升带来的间接改善；
不会做：以牺牲质量为代价的「随便几页应付交差」式提速。

如果对速度敏感且能接受质量下降，零配置的浏览器 SaaS 工具更合适。

### 独立 CLI / 托管 SaaS / 桌面 App 形态

产品形态明确为**运行在支持 Agent 的 AI 工具中的对话式工作流 / skill**（Claude Code、Codex、Cursor、VS Code agents 等）。

不会做：独立 CLI（`ppm` 之类）、SaaS Web 服务、Electron 桌面壳。所有「让它脱离 chat 独立运行」的提案都会被拒。chat 是交互核心，不是包装层。

---

## 反馈渠道

- **Issues**：[github.com/hugohe3/ppt-master/issues](https://github.com/hugohe3/ppt-master/issues) — 报告 Bug / 提建议
- **Discussions**：[github.com/hugohe3/ppt-master/discussions](https://github.com/hugohe3/ppt-master/discussions) — 用法讨论 / 经验分享
- **邮箱**：heyug3@gmail.com

提需求前先扫一眼上面的 **Non-goals**；如果你的需求落在那一节，多半不会被采纳，但欢迎讨论是否还有别的路径解决你的真实问题。
