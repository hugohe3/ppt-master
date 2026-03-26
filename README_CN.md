# PPT Master — AI 生成原生可编辑 PPTX，支持任意文档输入

[![Version](https://img.shields.io/badge/version-v2.3.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)

[English](./README.md) | 中文

丢进一份 PDF、DOCX、网址或 Markdown，AI 自动生成**原生可编辑的 PowerPoint 演示文稿**——不是图片，每个文本框、图表、图形都是真正的 PowerPoint 对象，点击即可编辑。支持 PPT 16:9、小红书、朋友圈等 10+ 种格式。

> 🔥 **重磅更新：原生可编辑 PPTX** — 生成的演示文稿现在默认包含**真正的 PowerPoint 原生形状**（DrawingML），文字、图表、图形均可在 PowerPoint 中直接编辑，无需任何额外操作。告别"转换为形状"！
>
> 💡 **架构更新**：目前项目使用 Skill-based 架构：
> 1. **大幅减少 Token 消耗与模型依赖**：现在即使不使用 Opus 模型，其他模型也能生成质量尚可的结果。
> 2. **更强的系统扩展性**：整个 `skills` 文件夹按 Agent Skills 标准组织，每个子目录都是一个完全自包含的 Skill。您可以将其直接放入支持该标准的 AI 客户端的 skills 目录中作为本地技能原生调用（例如：Claude Code 的 `.claude/skills/` 或 `~/.claude/skills/`；Antigravity 置于全局 skills 目录后经由 `.agent/workflows/` 引用；GitHub Copilot 的 `.github/skills/` 或 `~/.copilot/skills/`）。
> 3. **稳定版降级选择**：旧版多平台适配架构虽然 Token 消耗较多，但经受了更长时间的检验。如果您在使用当前新版本时遇到不稳定情况，可以随时尝试退回至老架构的最终版本：[v1.3.0](https://github.com/hugohe3/ppt-master/tree/v1.3.0)。

> **在线示例**：[GitHub Pages 在线预览](https://hugohe3.github.io/ppt-master/) — 查看实际生成效果

> 🎨 **设计哲学 —— AI 是你的设计师，不是完工师**
>
> 生成的 PPTX 是一份**设计稿**，而非成品。把它理解成建筑师的效果图：AI 负责视觉设计、排版布局和内容结构，交付给你一个高质量的起点。要想获得真正精良的成品，**需要你自己在 PowerPoint 里做精装修**：换掉形状、细化图表、调整配色、把占位图形替换成原生对象。这个工具的目标是消除 90% 的从零开始的工作量，而不是替代人在最后一公里的判断。不要指望 AI 一遍搞定所有——好的演示文稿从来不是这样做出来的。
>
> **工具的上限是你的上限。** PPT Master 放大的是你已有的能力——你有设计感和内容判断力，它帮你快速落地；你不知道一个好的演示文稿应该长什么样，它也没法替你知道。输出的质量，归根结底是你自身品味与判断力的映射。

---

## 🎴 精选示例

> **示例库**: [`examples/`](./examples/) · **15 个项目** · **229 页**

| 类别            | 项目 | 页数 | 特色 |
| --------------- | ---- | :--: | ---- |
| 🏢 **咨询风格** | [心理治疗中的依恋](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E5%BF%83%E7%90%86%E6%B2%BB%E7%96%97%E4%B8%AD%E7%9A%84%E4%BE%9D%E6%81%8B) |  32  | 顶级咨询风格，最大规模示例 |
|                 | [构建有效AI代理](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E6%9E%84%E5%BB%BA%E6%9C%89%E6%95%88AI%E4%BB%A3%E7%90%86_Anthropic) |  15  | Anthropic 工程博客，AI Agent 架构 |
|                 | [重庆市区域报告](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E9%87%8D%E5%BA%86%E5%B8%82%E5%8C%BA%E5%9F%9F%E6%8A%A5%E5%91%8A_ppt169_20251213) |  20  | 区域财政分析，企业预警通数据 |
|                 | [甘孜州经济财政分析](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E7%94%98%E5%AD%9C%E5%B7%9E%E7%BB%8F%E6%B5%8E%E8%B4%A2%E6%94%BF%E5%88%86%E6%9E%90) |  17  | 政务财政分析，藏区文化元素 |
| 🎨 **通用灵活** | [Debug 六步法](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%80%9A%E7%94%A8%E7%81%B5%E6%B4%BB%2B%E4%BB%A3%E7%A0%81_debug%E5%85%AD%E6%AD%A5%E6%B3%95) |  10  | 深色科技风格 |
|                 | [重庆大学论文格式](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%80%9A%E7%94%A8%E7%81%B5%E6%B4%BB%2B%E5%AD%A6%E6%9C%AF_%E9%87%8D%E5%BA%86%E5%A4%A7%E5%AD%A6%E8%AE%BA%E6%96%87%E6%A0%BC%E5%BC%8F%E6%A0%87%E5%87%86) |  11  | 学术规范指南 |
| ✨ **创意风格** | [地山谦卦深度研究](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E6%98%93%E7%90%86%E9%A3%8E_%E5%9C%B0%E5%B1%B1%E8%B0%A6%E5%8D%A6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6) |  20  | 易经本体美学，阴阳爻变设计 |
|                 | [金刚经第一品研究](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E7%A6%85%E6%84%8F%E9%A3%8E_%E9%87%91%E5%88%9A%E7%BB%8F%E7%AC%AC%E4%B8%80%E5%93%81%E7%A0%94%E7%A9%B6) |  15  | 禅意学术，水墨留白 |
|                 | [Git 入门指南](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E5%83%8F%E7%B4%A0%E9%A3%8E_git_introduction) |  10  | 像素复古游戏风 |

📖 [查看完整示例文档](./examples/README.md)

---

## 🏗️ 系统架构

```
用户输入 (PDF/DOCX/URL/Markdown)
    ↓
[源内容转换] → pdf_to_md.py / doc_to_md.py / web_to_md.py
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[模板选项] A) 使用已有模板 B) 不使用模板
    ↓
[需要新模板？] → 使用 /create-template 工作流单独创建
    ↓
[Strategist] 策略师 - 八项确认与设计规范
    ↓
[Image_Generator] 图片生成师（当选择 AI 生成时）
    ↓
[Executor] 执行师 - 分阶段生成
    ├── 视觉构建阶段：连续生成所有 SVG 页面 → svg_output/
    └── 逻辑构建阶段：生成完整讲稿 → notes/total.md
    ↓
[后处理] → total_md_split.py（拆分讲稿）→ finalize_svg.py → svg_to_pptx.py
    ↓
输出: 自动生成两个文件：
    ├── presentation.pptx        ← 原生形状版（DrawingML）— 推荐用于编辑与交付
    └── presentation_svg.pptx   ← SVG 参考版 — 像素级视觉参考；在 PowerPoint 中选中内容
                                    后使用"转换为形状"可解锁单独元素的编辑
    ↓
[Optimizer_CRAP] 优化师（可选，初版后不满意再用）
    ↓
如有优化：重新运行后处理与导出
```

### 📚 文档导航

| 文档 | 说明 |
|------|------|
| 🧭 [AGENTS.md](./AGENTS.md) | 仓库级入口概览（适用于通用 AI 代理） |
| 📖 [SKILL.md](./skills/ppt-master/SKILL.md) | `ppt-master` 核心流程与规则源 |
| 🎨 [设计指南](./skills/ppt-master/references/design-guidelines.md) | 配色、排版、布局规范详解 |
| 📐 [画布格式](./skills/ppt-master/references/canvas-formats.md) | PPT、小红书、朋友圈等 10+ 种格式 |
| 🖼️ [图片嵌入指南](./skills/ppt-master/references/svg-image-embedding.md) | SVG 图片嵌入最佳实践 |
| 📊 [图表模板库](./skills/ppt-master/templates/charts/) | 13 种标准化图表模板 |
| 🛠️ [工具集](./skills/ppt-master/scripts/README.md) | 所有工具的使用说明 |
| 💼 [示例索引](./examples/README.md) | 15 个项目、229 页 SVG 示例 |

---

## 🚀 快速开始

### 1. 配置环境

#### Python 环境（必需）

本项目需要 **Python 3.8+**，用于运行 PDF 转换、SVG 后处理、PPTX 导出等工具。

| 平台 | 推荐安装方式 |
|------|------------|
| **macOS** | 使用 [Homebrew](https://brew.sh/)：`brew install python` |
| **Windows** | 从 [Python 官网](https://www.python.org/downloads/) 下载安装包 |
| **Linux** | 使用系统包管理器：`sudo apt install python3 python3-pip`（Ubuntu/Debian） |

> 💡 **验证安装**：运行 `python3 --version` 确认版本 ≥ 3.8

#### Node.js 环境（可选）

如需使用 `web_to_md.cjs` 工具（用于微信公众号等高防站点的网页转换），需安装 Node.js。

| 平台 | 推荐安装方式 |
|------|------------|
| **macOS** | 使用 [Homebrew](https://brew.sh/)：`brew install node` |
| **Windows** | 从 [Node.js 官网](https://nodejs.org/) 下载 LTS 版本安装包 |
| **Linux** | 使用 [NodeSource](https://github.com/nodesource/distributions)：`curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |

> 💡 **验证安装**：运行 `node --version` 确认版本 ≥ 18

#### Pandoc（可选）

如需使用 `doc_to_md.py` 工具（用于将 DOCX、EPUB、LaTeX 等文档格式转换为 Markdown），需安装 [Pandoc](https://pandoc.org/)。

| 平台 | 推荐安装方式 |
|------|------------|
| **macOS** | 使用 [Homebrew](https://brew.sh/)：`brew install pandoc` |
| **Windows** | 从 [Pandoc 官网](https://pandoc.org/installing.html) 下载安装包 |
| **Linux** | 使用系统包管理器：`sudo apt install pandoc`（Ubuntu/Debian） |

> 💡 **验证安装**：运行 `pandoc --version` 确认已安装

### 2. 克隆仓库并安装依赖

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

> 如遇权限问题，可使用 `pip install --user -r requirements.txt` 或在虚拟环境中安装。

### 3. 打开 AI 编辑器

推荐使用以下 AI 编辑器：

| 工具                                                | 推荐度 | 说明                                                                          |
| --------------------------------------------------- | :----: | ----------------------------------------------------------------------------- |
| **[Claude Code](https://claude.ai/)**               | ⭐⭐⭐ | **强烈推荐**！Anthropic 官方 CLI，原生 Opus 支持，上下文最充裕                |
| Codebuddy IDE                                       |  ⭐⭐  | 优秀的国产 AI IDE，对 Kimi 2.5、MiniMax 2.7 等国产大模型有较好支持             |
| [Cursor](https://cursor.sh/)                        |  ⭐⭐  | 主流 AI 编辑器，体验好但价格较高                                              |
| [VS Code + Copilot](https://code.visualstudio.com/) |  ⭐⭐  | 微软官方方案，性价比高，但上下文窗口受限（200k，预留 35% 给输出）             |
| [Antigravity](https://antigravity.dev/)             |   ⭐   | 免费但额度极少且不稳定，仅作备选                                              |

### 4. 开始创作

在 AI 编辑器中打开聊天面板，直接描述你想创作的内容：

```
用户：我有一份关于 Q3 季度业绩的报告，需要制作成 PPT

AI：好的，先确认是否使用模板；确认后我会继续八项确认并生成设计规范。
   [模板选项] [建议] B) 不使用模板；如需使用模板，我会先参考 templates/layouts/layouts_index.json 给出推荐
   [Strategist] 1. 画布格式：[建议] PPT 16:9
   [Strategist] 2. 页数范围：[建议] 8-10 页
   ...
```

> 💡 **模型推荐**：Claude Opus 效果最佳，但大部分主流模型（如 Kimi 2.5、MiniMax 2.7 等，可通过 Codebuddy IDE 使用）目前均能生成不错的内容，仅在细节排版效果上可能存在差距。因目前某些 IDE (如 Antigravity) 的 Opus 极不稳定，请优先使用其他稳定的 AI 客户端进行创作。

> 📝 **导出后编辑**：默认导出的 PPTX（`.pptx`）包含**原生 PowerPoint 形状**，文字、图形和颜色可直接编辑，无需额外操作。同时还会生成一份 SVG 参考版（`_svg.pptx`），该版本需在 PowerPoint 中选中内容后右键选择 **"转换为形状"** (Convert to Shape) 方可编辑。需要 **Office 2016** 或更高版本。

> 💡 **AI 迷失上下文？** 可提示 AI 优先阅读 `skills/ppt-master/SKILL.md`；如需一个仓库级入口概览，再参考 `AGENTS.md`

### 5. Gemini 生图配置（可选）

本项目的 `nano_banana_gen.py` 可通过 Gemini API 在 AI 客户端中直接生成高质量配图。使用前需配置环境变量：

```bash
# 必需：Gemini API Key（从 https://aistudio.google.com/apikey 获取）
export GEMINI_API_KEY="your-api-key"

# 可选：自定义 API 端点（用于代理服务）
export GEMINI_BASE_URL="https://your-proxy-url.com/v1beta"
```

> 💡 **持久化**：将上述 `export` 命令添加到 `~/.zshrc`（macOS/Linux zsh）或 `~/.bashrc`（Linux bash）中，重启终端即可永久生效。

> 💡 若使用 Antigravity 代理，调用时需传入模型参数（`-m gemini-3.1-flash-image`）。

> 💡 **AI 生成图片建议**：如需 AI 生成配图，建议在 [Gemini](https://gemini.google.com/) 中生成后选择 **Download full size** 下载，分辨率比 Antigravity 直接生成的更高。Gemini 生成的图片右下角会有星星水印，可使用 [gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover) 或本项目的 `skills/ppt-master/scripts/gemini_watermark_remover.py` 去除。

---

## 📁 项目结构

```text
ppt-master/
├── skills/
│   └── ppt-master/                 # 规范源（完全自包含的单一 Skill 源）
│       ├── SKILL.md                #   主入口：工作流定义与执行边界
│       ├── workflows/              #   工作流引擎脚本与独立任务
│       ├── references/             #   AI 角色定义 + 技术文档规范
│       ├── scripts/                #   工具脚本集成
│       └── templates/              #   模板库（布局 + 图表 + 图标）
├── examples/                       # 示例项目（包含多种生成案例）
├── projects/                       # 用户项目默认工作区
├── AGENTS.md                       # 通用 AI 代理入口概览
└── CLAUDE.md                       # Claude Code CLI 专属入口概览
```

---

## 🛠️ 常用命令

```bash
# 初始化项目
python3 skills/ppt-master/scripts/project_manager.py init <项目名> --format ppt169

# 将源材料归档到项目目录
python3 skills/ppt-master/scripts/project_manager.py import-sources <项目路径> <源文件或URL...>

# PDF 转 Markdown
python3 skills/ppt-master/scripts/pdf_to_md.py <PDF文件>

# DOCX / Office 文档转 Markdown（需要 pandoc）
python3 skills/ppt-master/scripts/doc_to_md.py <DOCX文件>

# 后处理三步（必须按顺序执行）
python3 skills/ppt-master/scripts/total_md_split.py <项目路径>
python3 skills/ppt-master/scripts/finalize_svg.py <项目路径>
python3 skills/ppt-master/scripts/svg_to_pptx.py <项目路径> -s final
# 默认生成两个文件：原生可编辑形状 (.pptx) + SVG 图片参考版 (_svg.pptx)
# 仅生成原生版：--only native    仅生成 SVG 图片版：--only legacy

```

> 📖 完整工具说明请参阅 [脚本使用指南](./skills/ppt-master/scripts/README.md)

---

## ❓ 常见问题

<details>
<summary><b>Q: 生成的 PPT 可以编辑吗？</b></summary>

可以！默认导出的 PPTX（`.pptx`）包含**原生 PowerPoint 形状**，所有文字、图形、颜色均可在 PowerPoint 中直接编辑，无需任何转换操作。同时还会生成一份 SVG 参考版（`_svg.pptx`），该版本需选中内容后右键 **"转换为形状"** (Convert to Shape) 方可编辑。需要 **Office 2016** 或更高版本。

</details>

<details>
<summary><b>Q: 三种执行师有什么区别？</b></summary>

- **Executor_General**: 通用场景，灵活布局
- **Executor_Consultant**: 一般咨询，数据可视化
- **Executor_Consultant_Top**: 顶级咨询（MBB 级），5 大核心技巧

</details>

<details>
<summary><b>Q: 必须使用 Optimizer_CRAP 吗？</b></summary>

不是必须的。仅在需要优化关键页面视觉效果时使用。

</details>

<details>
<summary><b>Q: 生成的图表可以编辑数据吗？</b></summary>

图表以**自定义设计的 SVG 图形**形式渲染，转换为原生 PowerPoint 形状——而不是 Excel 驱动的图表对象。这使得图表外观精良，视觉效果通常优于 PowerPoint 默认图表样式。但图表的底层数据无法通过 PowerPoint 图表编辑器修改。如果你需要可实时更新数据的图表（例如通过编辑表格来刷新数据），需要在导出后自行将其替换为原生 PowerPoint 图表。

</details>

> 📖 更多问题可先查看 [skills/ppt-master/SKILL.md](./skills/ppt-master/SKILL.md) 与 [AGENTS.md](./AGENTS.md)

---

## 🔧 技术路线

**核心流程：AI 生成 SVG → 后处理转换为 DrawingML（PPTX）。**

整个流程分为三个阶段：

**第一阶段：内容理解与设计规划**
源文档（PDF/DOCX/URL/Markdown）经过转换变为结构化文本，由 Strategist 角色完成内容分析、页面规划和设计风格确认，输出完整的设计规格。

**第二阶段：AI 视觉生成**
Executor 角色逐页生成演示文稿的视觉内容，输出为 SVG 文件。这个阶段的产物是**设计稿**，而非成品。

**第三阶段：工程化转换**
后处理脚本将 SVG 转换为 DrawingML，每一个形状都变成真正的 PowerPoint 原生对象——可点击、可编辑、可改色，而不是嵌入的图片。

---

**为什么是 SVG？**

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

## 🤝 贡献指南

欢迎贡献！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

**贡献方向**：🎨 设计模板 · 📊 图表组件 · 📝 文档完善 · 🐛 Bug 报告 · 💡 功能建议

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [SVG Repo](https://www.svgrepo.com/) - 开源图标库
- [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) - CRAP 设计原则
- 麦肯锡、波士顿咨询、贝恩 - 设计灵感来源

## 📮 联系方式

- **Issue**: [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)
- **GitHub**: [@hugohe3](https://github.com/hugohe3)

---

## 🌟 Star History

如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！

<a href="https://star-history.com/#hugohe3/ppt-master&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
 </picture>
</a>

---

## ☕ 赞助

如果这个项目帮你省了时间，欢迎请我喝杯咖啡，支持我继续燃烧 token！

<a href="https://github.com/sponsors/hugohe3">
  <img src="https://img.shields.io/badge/GitHub%20Sponsors-♥-ea4aaa?style=for-the-badge&logo=github-sponsors" alt="GitHub Sponsors" />
</a>

**支付宝**

<img src="docs/assets/alipay-qr.jpg" alt="支付宝收款码" width="250" />

---

Made with ❤️ by Hugo He

[⬆ 回到顶部](#ppt-master--ai-生成原生可编辑-pptx支持任意文档输入)
