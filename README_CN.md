# PPT Master — AI 生成原生可编辑 PPTX，支持任意文档输入

[![Version](https://img.shields.io/github/v/release/hugohe3/ppt-master?label=version&color=blue)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)
[![AtomGit stars](https://atomgit.com/hugohe3/ppt-master/star/badge.svg)](https://atomgit.com/hugohe3/ppt-master)
[![The Agentic Leaderboard](https://www.theagenticleaderboard.com/badges/ppt-master.svg)](https://www.theagenticleaderboard.com/agent/?q=ppt-master)

<p align="center">
  <a href="https://trendshift.io/repositories/25760?utm_source=repository-badge&amp;utm_medium=badge&amp;utm_campaign=badge-repository-25760" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/repositories/25760" alt="hugohe3%2Fppt-master | Trendshift" width="250" height="55"/></a>
</p>

[English](./README.md) | 中文

<details open>
<summary>本项目由 <a href="https://www.packyapi.com/register?aff=ppt-master">PackyCode</a>、<a href="https://apikey.fun/register?aff=PPT-MASTER">APIKEY.FUN</a>、<a href="https://runapi.co/register?aff=WMLJ">RunAPI</a>、<a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624">优云智算</a> 等赞助方支持，得以持续免费开源。</summary>

<table>
  <tr>
    <td width="180"><a href="https://www.packyapi.com/register?aff=ppt-master"><img src="docs/assets/sponsors/packycode.png" alt="PackyCode" width="150"></a></td>
    <td>感谢 PackyCode 赞助了本项目！PackyCode 是一家稳定、高效的 API 中转服务商，提供 Claude Code、Codex、Gemini 等多种中转服务。PackyCode 为本项目的用户提供了特别优惠，使用<a href="https://www.packyapi.com/register?aff=ppt-master">此链接</a>注册并在充值时填写"ppt-master"优惠码，可以享受 9 折优惠。</td>
  </tr>
  <tr>
    <td width="180"><a href="https://apikey.fun/register?aff=PPT-MASTER"><img src="docs/assets/sponsors/apikey-fun.png" alt="APIKEY.FUN" width="150"></a></td>
    <td>感谢 APIKEY.FUN 赞助了本项目！APIKEY.FUN 是一家专业的企业级 AI 中转站，致力于为企业和开发者提供稳定、高效、低成本的 AI 中转服务。平台支持 Claude、OpenAI、Gemini 等主流热门模型，价格低至官方原价的 <strong>7%</strong>。通过<a href="https://apikey.fun/register?aff=PPT-MASTER">本项目专属链接</a>注册，还可享受最高 <strong>永久充值 95 折</strong> 专属优惠。</td>
  </tr>
  <tr>
    <td width="180"><a href="https://runapi.co/register?aff=WMLJ"><img src="docs/assets/sponsors/runapi.png" alt="RunAPI" width="150"></a></td>
    <td>感谢 RunAPI 赞助了本项目！RunAPI 是一个高效稳定的 API 平台，一个 API Key 即可访问 OpenAI、Claude、Gemini、DeepSeek、Grok 等 150+ 主流模型，价格低至官方原价的 <strong>1 折</strong>，极其稳定，可无缝兼容 Claude Code 等工具。RunAPI 为 PPT Master 用户提供专属福利：通过<a href="https://runapi.co/register?aff=WMLJ">本项目专属链接</a>注册并联系管理员，即可领取 <strong>￥7 的免费额度</strong>。</td>
  </tr>
  <tr>
    <td width="180"><a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624"><img src="docs/assets/sponsors/youyun.png" alt="优云智算" width="150"></a></td>
    <td>感谢优云智算赞助了本项目！优云智算是 UCloud 旗下 AI 云平台，一站式提供国内外主流模型的 API 服务，一个 Key 即可调用所有模型。主打高性价比国产模型 CodingPlan 套餐（GLM5.2、Deepseek-v4 等），同时提供官方转发的稳定海外模型通道，满足多场景开发需求。已兼容 Claude Code、Codex 等主流 AI 编程工具及通用 API 调用，支持企业级高并发、7×24 技术支持和自助开票。通过<a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624">此链接</a>注册，最高可获得 <strong>¥10 免费体验金</strong>。该项目已制作成 Agent【PPT 制作大师】，无需本地部署即可使用。</td>
  </tr>
</table>

</details>

> **AI 生成 PPT，不是 AI 套模板。** PPT Master 是一套在 AI IDE（Claude Code / Cursor / VS Code + Copilot 等）里运行的工作流：把 PDF / DOCX / 网页等材料交给 AI，它在你本机生成一份真正的 PowerPoint——每个元素都能在 PowerPoint 里点开修改，数据不出本地，不锁定任何平台和模型。工作原理与能力边界 → [产品定位](#产品定位)。

<p align="center">
  <a href="https://hugohe3.github.io/ppt-master/"><strong>在线预览</strong></a> ·
  <a href="./examples/"><strong>示例下载</strong></a> ·
  <a href="./docs/zh/faq.md"><strong>常见问题</strong></a> ·
  <a href="./docs/zh/roadmap.md"><strong>路线图</strong></a>
</p>

<h3 align="center">下载这份<a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_attention_is_all_you_need/exports/attention_is_all_you_need_narrated.pptx">带音频旁白的 <em>Attention Is All You Need</em> 论文精读 deck</a>，在 PowerPoint 里直接放映，每一页都会自己"读"给你听 —— 这只是 PPT Master 能力的冰山一角。</h3>

<table>
  <tr>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_pritzker_2026"><img src="docs/assets/screenshots/preview_pritzker_2026.png" alt="杂志风 — 普利兹克奖 2026" /></a><br/>
      <sub><b>杂志风</b> — 建筑摄影 + 排版网格，冷静克制的编辑感<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_pritzker_2026">在线翻页</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_pritzker_2026/exports/pritzker_2026.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_global_ai_capital_2026"><img src="docs/assets/screenshots/preview_global_ai_capital.png" alt="新闻风 — 2026 全球 AI 资本格局" /></a><br/>
      <sub><b>新闻 / 财经数据风</b> — 深色仪表盘，图表驱动，彭博风<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_global_ai_capital_2026">在线翻页</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_global_ai_capital_2026/exports/global_ai_capital_2026.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_swiss_grid_systems"><img src="docs/assets/screenshots/preview_swiss_grid.png" alt="瑞士风 — 网格系统入门" /></a><br/>
      <sub><b>瑞士风</b> — 严格栅格，克制字体，红色点缀<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_swiss_grid_systems">在线翻页</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_swiss_grid_systems/exports/swiss_grid_systems.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_glassmorphism_demo"><img src="docs/assets/screenshots/preview_glassmorphism_demo.png" alt="毛玻璃风 — AI Agent 工程化 Demo" /></a><br/>
      <sub><b>毛玻璃 SaaS</b> — 半透明叠层，渐变景深，产品 UI 感<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_glassmorphism_demo">在线翻页</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_glassmorphism_demo/exports/glassmorphism_demo.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_sugar_rush_memphis"><img src="docs/assets/screenshots/preview_sugar_rush_memphis.png" alt="孟菲斯风 — Sugar Rush 音乐节" /></a><br/>
      <sub><b>孟菲斯波普</b> — 高饱和原色，几何图形，俏皮活力<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_sugar_rush_memphis">在线翻页</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_sugar_rush_memphis/exports/sugar_rush_memphis.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_indie_bookstore_zine_guide"><img src="docs/assets/screenshots/preview_indie_bookstore_zine.png" alt="Zine 风 — 独立书店指南" /></a><br/>
      <sub><b>Risograph Zine</b> — 双色印刷质感，手作书店文化<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_indie_bookstore_zine_guide">在线翻页</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_indie_bookstore_zine_guide/exports/indie_bookstore_zine_guide.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
</table>

<p align="center">
  <sub>以上示例均为一次性生成、未经精修（生成模型：Claude Opus 4.7 + <code>gpt-image-2</code>）。下载任意一份 .pptx 在 PowerPoint 里打开，是感受真实产出水平最快的方式。<br/><a href="https://hugohe3.github.io/ppt-master/">在线翻看全部示例 →</a> · <a href="./examples/"><code>examples/</code> 目录</a> · <a href="./docs/zh/why-ppt-master.md">为什么选 PPT Master？</a></sub>
</p>

<p align="center">
  更多端到端实例：<a href="https://space.bilibili.com/111258938/lists/8144072"><strong>合集·PPT-Master 能力展示</strong></a>（B 站）
</p>

---

丢进原材料，拿回的这份 PPT **不只是能改**：它有 PPT 原生的转场与入场动画，演讲者备注能直接合成音频旁白，图表和表格还能以带数据的 PowerPoint 原生对象形式导出，也能参考你自己的 PPT 模板来设计——一份能直接拿去讲、回头还能改的成品。每项能力怎么用 → [快速入门](./docs/zh/getting-started.md)。

## 产品定位

**一个文件如果在 PowerPoint 里打不开、改不动，就不该被叫做 PPT。** 市面上的 AI PPT 工具大致分四类，PPT Master 只做最后一类：

| 类型 | 产物形态 | 能在 PowerPoint 里逐元素改吗 |
|---|---|:---:|
| 模板填空 | 套模板的 PPTX | 部分可以，受模板限制 |
| 图片式 | 一页一张大图拼成 PPTX | ❌ 整页是图片 |
| HTML 演示 | 网页演示 | ❌ 不是 PPTX |
| **原生可编辑（PPT Master）** | **真 DrawingML 形状、文本框、图表** | ✅ 每个元素都能点开改 |

形态上，它不是网站也不是 App，而是一套在 AI IDE（Claude Code / Cursor / VS Code + Copilot / Codebuddy 等）里运行的工作流（一个 "skill"）：你在 IDE 的对话框里说"用这份 PDF 做一份 PPT"，AI 按这套工作流在你本机生成真正可编辑的 `.pptx`。你不写任何代码，要做的只有三件事——装 Python、装一个 AI IDE、把资料放进来。

这个形态换来三个别的工具很难同时给出的承诺：

- **成本透明可控** — 工具免费开源，唯一成本是你自己的 AI 模型用量，你用多少付多少，不在此之外增加任何订阅费用
- **数据不出本地** — 你的文件不应该为了做一份 PPT 就被上传到别人的服务器。除与 AI 模型的对话外，全流程在你的电脑上完成
- **不锁定平台** — 你的工作流不应该被任何一家公司绑架。Claude Code、Cursor、VS Code Copilot 等均可驱动；Claude、GPT、Gemini、Kimi 等模型均可使用

> [!IMPORTANT]
> ### 这是一个工具，不是一个许愿池
> `harness + model = agent`——PPT Master 只负责工作流，产出上限由模型决定。推荐 **Claude 大上下文窗口（~100 万 token）+ AI 生图（`gpt-image-2`）**；其他模型能跑通流程，但有质量差距。
>
> 也别指望一把就拿到完美成品。它的价值是帮你把大部分枯燥的活儿干掉，剩下的打磨交给你——做原生可编辑的 PPT，本就是为了让你接着改，而不是甩给你一张改不动的图。模型越便宜，要补的人工就越多；效果不理想，先升级模型，再对照[快速入门](./docs/zh/getting-started.md)和示例工程检查用法。

---

## 关于作者

我是何雨果（Hugo He），投融资领域从业者（注册会计师 · 资产评估师 · 咨询工程师（投资）），工作中经常审阅和修改 PPT。我希望 AI 生成的幻灯片仍然能在 PowerPoint 里继续编辑，而不是被压成一张张图片——所以做了这个。

未来，使用 Python 和 AI agent 的能力会越来越重要，这个项目也想展示：仅凭这两样，你能走多远。零基础上手有一段学习曲线，但走完这段，你就接上了未来——做 PPT 只是个借口，我真正想推广的是 Python 和 agent。

---

## 你可能也感兴趣

### <a href="https://github.com/microsoft/ResearchStudio">ResearchStudio-<img src="https://raw.githubusercontent.com/ai-nuts/Storage/main/ResearchStudio/ResearchStudio-Reel/docs/figures/reel-wordmark.png" alt="Reel" height="16"></a>

> 微软开源项目，我最近也参与其中——从**论文**到**演讲视频**、**海报**与**博客**，自动化科研传播的**最后一公里**。
>
> 📦 **仓库：**[microsoft/ResearchStudio](https://github.com/microsoft/ResearchStudio) · 📄 **论文：**[arXiv:2607.04438](https://arxiv.org/abs/2607.04438)

<table align="center">
<tr>
<td align="center" valign="middle" width="53%">
  <a href="https://aka.ms/ResearchStudio">
    <img src="https://raw.githubusercontent.com/ai-nuts/Storage/main/ResearchStudio/ResearchStudio-Reel/docs/figures/reel_demo.gif" width="100%"
    alt="ResearchStudio-Reel 演示" />
  </a>
</td>
<td align="center" valign="middle" width="47%">
  <a href="https://aka.ms/ResearchStudio">
    <img src="https://raw.githubusercontent.com/ai-nuts/Storage/main/ResearchStudio/ResearchStudio-Reel/docs/examples/latent_diffusion_landscape/poster.png" width="100%" alt="ResearchStudio-Reel 生成的海报" />
  </a>
</td>
</tr>
</table>

<details>
<summary><strong>BibTeX</strong> —— 如果你在研究中使用了 ResearchStudio-Reel</summary>

```bibtex
@article{xiao2026researchstudioreel,
  title   = {ResearchStudio-Reel: Automate the Last Mile of Research from Paper to Poster, Video, and Blog},
  author  = {Lingao Xiao and Yalun Dai and Yangyu Huang and Qihao Zhao and Wenshan Wu and Hugo He and Ruishuo Chen and Jin Jiang and Qianli Ma and Jiahuan Zhang and Xin Zhang and Ying Xin and Yang Ou and Yan Xia and Scarlett Li and Longbo Huang and Zhipeng Zhang and Yang He and Yap Kim Hui and Yan Lu},
  journal = {arXiv preprint arXiv:2607.04438},
  year    = {2026},
  url     = {https://arxiv.org/abs/2607.04438}
}
```

</details>

---

## 快速开始

### 1. 前置条件

**只需安装 [Python](https://www.python.org/downloads/) 3.10+。** 其余依赖在第 3 步下载好项目后，用一行 `pip install -r requirements.txt` 装齐。

<details>
<summary><strong>Windows</strong> — 请看专门的<a href="./docs/zh/windows-installation.md">手把手安装指南</a> ⚠️</summary>

Windows 需要一些额外步骤（PATH 设置、执行策略等）。我们为 Windows 用户写了一份**手把手安装指南**：

**📖 [Windows 安装指南](./docs/zh/windows-installation.md)** — 从零到跑通第一份 PPT，10 分钟搞定。

简要流程：从 [python.org](https://www.python.org/downloads/) 下载 Python → **安装时勾选 "Add to PATH"** → 完成，依赖安装见第 3 步。
</details>

<details>
<summary><strong>macOS / Linux</strong> — 安装即用</summary>

```bash
# macOS
brew install python

# Ubuntu / Debian
sudo apt install python3 python3-pip
```
</details>

<details>
<summary><strong>边缘场景备用方案</strong> — 99% 的用户用不到</summary>

**Pandoc** — 只在需要转小众格式时才装：`.doc`、`.odt`、`.rtf`、`.tex`、`.rst`、`.org`、`.typ`。`.docx`、`.html`、`.epub`、`.ipynb` 已由 Python 原生处理，不需要 pandoc。

```bash
# macOS
brew install pandoc

# Ubuntu / Debian
sudo apt install pandoc
```
</details>

### 2. 选择一个 Agent

PPT Master 在**任何具备 agent 能力**（可读写文件、执行命令、持续多轮对话）的工具里都能跑。

没用过这类工具也不用担心：它们在本项目里只扮演一个角色——一个能读写文件的 AI 聊天窗口。从下表任选一款装好即可，全程只用它的聊天面板，不需要写任何代码。

> **作者最推荐：[Claude Code](https://claude.ai/code)** ——本项目开发与测试最充分的环境，CLI 与 VS Code / JetBrains 扩展均可。

| 类型 | 代表工具 | 说明 |
|---|---|---|
| **IDE 内置 agent** | • VS Code 架构（含 [VS Code](https://code.visualstudio.com/) 本体及分支与衍生）：[Cursor](https://cursor.sh/)、Trae、Codebuddy IDE、[Windsurf](https://codeium.com/windsurf) 等<br>• 其他架构：[Zed](https://zed.dev/) 等 | 编辑器原生集成 agent |
| **IDE 插件 / 扩展** | [Claude Code](https://claude.ai/code)（VS Code / JetBrains 扩展）、[GitHub Copilot](https://github.com/features/copilot)、[Cline](https://cline.bot/)、通义灵码 等 | 装在 VS Code / JetBrains 等宿主里使用 |
| **CLI agent** | [Claude Code](https://claude.ai/code) CLI、[Codex CLI](https://github.com/openai/codex)、Gemini CLI 等 | 终端里运行，适合脚本化 / 远程 / 服务器场景 |

> **模型推荐**：追求最佳效果选 **Claude Opus**，搭配 `gpt-image-2` 生图；**Gemini 3.5 Flash** 目前综合性价比很高，尤其速度很快，值得一试。

**🔑 想用 Claude / GPT / Gemini 但还没有渠道？** 本项目赞助商 **[PackyCode](https://www.packyapi.com/register?aff=ppt-master)**、**[APIKEY.FUN](https://apikey.fun/register?aff=PPT-MASTER)** 与 **[RunAPI](https://runapi.co/register?aff=WMLJ)** 均支持按量调用 Claude、GPT、Gemini 等主流模型，无需订阅、支持国内支付，并为本项目用户提供专属优惠（详情见页首）。

**🔀 手上有多个渠道？** 拿到多家的 API Key 后，[cc-switch](https://github.com/farion1231/cc-switch)（跨平台桌面应用）可以一键切换 Claude Code、Codex、Gemini CLI 等工具的 API 供应商，免去手动改配置。

### 3. 配置项目

**方式 A — 下载 ZIP**（无需安装 Git，适合快速体验）：
[GitHub](https://github.com/hugohe3/ppt-master) → **Code → Download ZIP** · [AtomGit](https://atomgit.com/hugohe3/ppt-master) → **克隆/下载 → 下载ZIP**（国内网速更快）

如果你打算长期使用并持续更新，推荐使用下面的 Git clone 方式。

**方式 B — Git clone**（推荐；需先安装 [Git](https://git-scm.com/downloads)）：

```bash
# GitHub
git clone https://github.com/hugohe3/ppt-master.git
# AtomGit（国内网速更快）
git clone https://atomgit.com/hugohe3/ppt-master.git
cd ppt-master
```

然后安装依赖：

```bash
pip install -r requirements.txt
```

#### 日常更新

**Git clone 安装：**

```bash
python3 skills/ppt-master/scripts/update_repo.py
```

脚本会拉取最新版；如果 `requirements.txt` 有变化，会自动同步 Python 依赖。

**下载 ZIP 安装：**

ZIP 目录没有 Git 历史，不能自动 `git pull`。更新时请重新下载最新版 ZIP，解压到新目录，然后把旧目录里的 `.env` 和 `projects/` 复制过去，再执行：

```bash
pip install -r requirements.txt
```

> **方式 C — Skill marketplace**：仓库已添加 `.claude-plugin/marketplace.json` 元数据，可通过 [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) 生态一行安装：
>
> ```bash
> # 跨 agent CLI（Claude Code、Cursor、Codex 等）
> npx skills add hugohe3/ppt-master
>
> # 或在 Claude Code 内
> /plugin marketplace add hugohe3/ppt-master
> /plugin install ppt-master@ppt-master
> ```
>
> 上述两种安装方式都只会拉取 skill 文件本身（不含完整仓库），后处理脚本仍需在安装目录跑 `pip install -r requirements.txt`。

### 4. 开始创作

**先在 Agent 里打开项目文件夹：** 目标是让 AI 工作在上一步解压 / 克隆出来的 `ppt-master` 目录里——IDE 类工具通过菜单 **文件 → 打开文件夹**（File → Open Folder）打开它，AI 聊天面板通常在侧边栏；CLI 类工具先 `cd ppt-master` 再启动。之后的一切都在聊天里完成。

**提供原始材料（推荐）：** 将 PDF、DOCX、图片等文件放入 `projects/` 目录下，在 AI 聊天面板中告诉它使用哪些文件。获取路径的最快方式：在文件管理器或 IDE 侧边栏中右键文件 → **复制路径**（Copy Path / Copy Relative Path），直接粘贴进聊天框。

```
你：请用 projects/q3-report/sources/report.pdf 这份文件生成一份 PPT
```

**直接输入内容：** 也可以把文字内容直接粘贴进聊天窗口，AI 会根据这些内容生成 PPT。

```
你：请根据以下内容制作成 PPT：[粘贴你的文字内容...]
```

两种方式下 AI 都会先确认设计规范：

```
AI：好的，先确认设计规范：
   [模板] B) 自由设计
   [格式] PPT 16:9
   [页数] 8-10 页
   ...
```

AI 全程处理——内容分析、视觉设计、SVG 生成、PPTX 导出。

> **输出说明：** 原生形状版 `.pptx`（可直接编辑）保存至 `exports/<name>_<timestamp>.pptx`；`svg_output/` 始终镜像到 `backup/<timestamp>/svg_output/`，便于归档或后续重跑。加 `--svg-snapshot` 时，额外在 `exports/` 内并排生成 SVG 快照版 pptx（详见[常见问题](./docs/zh/faq.md)）。需要 Office 2016+。图表和表格默认导出为 SVG 派生的形状（在 PowerPoint / Keynote / WPS 间像素一致）；加 `--native-objects` 则改为导出**带数据、可直接编辑的 PowerPoint 原生图表 / 表格对象**（跨软件渲染可能略有差异），保存为 `exports/<name>_<timestamp>_native_charts.pptx`。

> **已有一份想复用的 `.pptx`？** 把那份 deck 连同素材给 AI，说「套模板」即可——它会把新内容（文字、表格、图表数据）填进你现有的设计，只导出你挑选的页面，且保持原生可编辑。详见 [常见问题](./docs/zh/faq.md) 与 [套模板工作流](./skills/ppt-master/workflows/template-fill-pptx.md)。

> **遇到问题？** AI 迷失上下文时，让它先读 `skills/ppt-master/SKILL.md`；其他问题查看 **[常见问题](./docs/zh/faq.md)** — 涵盖模型选择、排版问题、导出异常等，基于真实用户反馈持续更新。

### 5. 图片获取（可选）

非用户自带图片有两条路径，可在同一份 deck 里按图混用：

**A) AI 生图** — `image_gen.py`。设置 `IMAGE_BACKEND` 和对应 `*_API_KEY`（`OPENAI_API_KEY`、`GEMINI_API_KEY` 等），流程会自动调用。`python3 skills/ppt-master/scripts/image_gen.py --list-backends` 查看完整后端清单。`gpt-image-2` 目前综合质量最佳。

**B) 网络图片搜索** — `image_search.py`。**零配置**可用；建议配置 `PEXELS_API_KEY` / `PIXABAY_API_KEY`（都免费申请）以获得稳定的高质量结果：

- 不配置时只使用 Openverse / Wikimedia Commons，适合作为兜底，但容易出现构图随意、清晰度不稳定的图片
- 配置后默认搜索链会追加 Pexels / Pixabay，现代商业摄影、人物、办公、生活方式和插画类图片质量明显更稳定
- 许可自动处理：默认把 CC0、公有领域、Pexels / Pixabay 免署名许可、CC BY、CC BY-SA 一起纳入候选；选中需署名的图片时，Executor 会在该幻灯片自动添加小字署名。只有明确不能出现署名时，才使用 `--strict-no-attribution` 限制为免署名图片
- 对视觉要求高的封面、产品图、人物图和品牌场景，优先级建议：用户自带高清素材 / AI 生图 > 配置 Pexels / Pixabay 的网络搜索 > 零配置网络搜索

上面提到的 API Key 统一通过 `.env` 配置。clone 安装可以用 `cp .env.example .env`；skill marketplace 安装建议使用持久的用户级配置：

```bash
mkdir -p ~/.ppt-master
cp /path/to/installed/ppt-master/.env.example ~/.ppt-master/.env
```

PPT Master 会优先读取当前进程环境变量，然后按顺序读取第一个存在的 `.env`：当前工作目录、skill 安装目录（如 `~/.agents/skills/ppt-master/.env`）、clone 仓库根目录、`~/.ppt-master/.env`。

> 完整说明：[`image-generator.md`](./skills/ppt-master/references/image-generator.md)（AI）·[`image-searcher.md`](./skills/ppt-master/references/image-searcher.md)（网络）。

---

## 文档导航

| | 文档 | 说明 |
|---|------|------|
| 📘 | [快速入门](./docs/zh/getting-started.md) | 三步做出第一份 deck，外加模板、实时预览、动画、旁白、声音复刻的用法（**新用户从这里开始**） |
| 🆚 | [为什么选 PPT Master](./docs/zh/why-ppt-master.md) | 与 Gamma、Copilot 等工具的对比 |
| 🪟 | [Windows 安装指南](./docs/zh/windows-installation.md) | Windows 用户手把手安装教程 |
| 📖 | [SKILL.md](./skills/ppt-master/SKILL.md) | 核心流程与规则 |
| 📐 | [画布格式](./skills/ppt-master/references/canvas-formats.md) | PPT 16:9、小红书、朋友圈等 10+ 种格式 |
| 🛠️ | [脚本与工具](./skills/ppt-master/scripts/README.md) | 所有脚本和命令 |
| 💼 | [示例](./examples/README.md) | 所有示例项目 |
| 🏗️ | [技术路线](./docs/zh/technical-design.md) | 架构、设计哲学、为什么选 SVG |
| ❓ | [常见问题](./docs/zh/faq.md) | 模型选择、费用、排版问题排查、自定义模板 |

---

## 贡献

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 开源协议

[MIT](LICENSE)

## 致谢

[SVG Repo](https://www.svgrepo.com/) · [Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author))（CRAP 设计原则）

## 相关工具

[cc-switch](https://github.com/farion1231/cc-switch) —— 一键切换 Claude Code / Codex / Gemini CLI 等工具的 API 供应商。

## 联系与合作

欢迎合作交流、将 PPT Master 集成到你的工作流，或者单纯提问：

- 💬 **提问与分享** — [GitHub Discussions](https://github.com/hugohe3/ppt-master/discussions)
- 🐛 **Bug 反馈与功能建议** — [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)

---

## Star History

<a href="https://star-history.com/#hugohe3/ppt-master&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
 </picture>
</a>

---

## 赞助与支持

PPT Master 目前主要由我开发维护。每个新模板、Bug 修复、文档更新都需要持续的资源投入，目前由以下赞助方和个人支持者共同分担。

**企业赞助方**

<a href="https://www.packyapi.com/register?aff=ppt-master"><img src="docs/assets/sponsors/packycode.png" alt="PackyCode" height="40" /></a>
&nbsp;
<a href="https://apikey.fun/register?aff=PPT-MASTER"><img src="docs/assets/sponsors/apikey-fun.png" alt="APIKEY.FUN" height="40" /></a>
&nbsp;
<a href="https://runapi.co/register?aff=WMLJ"><img src="docs/assets/sponsors/runapi.png" alt="RunAPI" height="40" /></a>
&nbsp;
<a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624"><img src="docs/assets/sponsors/youyun.png" alt="优云智算" height="40" /></a>
&nbsp;
<a href="https://m.do.co/c/547f129aabe1"><img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" alt="Powered by DigitalOcean" height="40" /></a>

**个人赞助**

如果 PPT Master 帮到了你，任何金额的个人赞助都能帮助项目持续更新、保持免费开源。

<a href="https://paypal.me/hugohe3"><img src="https://img.shields.io/badge/PayPal-赞助-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="通过 PayPal 赞助" /></a>

<img src="docs/assets/alipay-qr.jpg" alt="支付宝收款码" width="220" />

---

Made with ❤️ by [何雨果 Hugo He](https://www.hehugo.com/) — 如果这个项目对你有帮助，请给一个 ⭐，也欢迎[赞助支持](#赞助与支持)。

<sub>官方发布渠道：<a href="https://github.com/hugohe3/ppt-master">GitHub</a>（主仓库）· <a href="https://atomgit.com/hugohe3/ppt-master">AtomGit</a>（镜像）。其他平台转发版本均为非官方版本。MIT 协议，使用需保留署名。</sub>

[⬆ 回到顶部](#ppt-master--ai-生成原生可编辑-pptx支持任意文档输入)
