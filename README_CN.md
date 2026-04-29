# PPT Master — AI 生成原生可编辑 PPTX，支持任意文档输入

[![Version](https://img.shields.io/badge/version-v2.3.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)
[![AtomGit stars](https://atomgit.com/hugohe3/ppt-master/star/badge.svg)](https://atomgit.com/hugohe3/ppt-master)

[English](./README.md) | 中文

<p align="center">
  <sub>本项目由 <a href="https://www.packyapi.com/register?aff=ppt-master">PackyCode</a> 等赞助方支持，得以持续免费开源。</sub>
</p>

<table>
  <tr>
    <td width="180"><a href="https://www.packyapi.com/register?aff=ppt-master"><img src="docs/assets/sponsors/packycode.png" alt="PackyCode" width="150"></a></td>
    <td>感谢 PackyCode 赞助了本项目！PackyCode 是一家稳定、高效的 API 中转服务商，提供 Claude Code、Codex、Gemini 等多种中转服务。PackyCode 为本项目的用户提供了特别优惠，使用<a href="https://www.packyapi.com/register?aff=ppt-master">此链接</a>注册并在充值时填写"ppt-master"优惠码，可以享受 9 折优惠。</td>
  </tr>
</table>

<p align="center">
  <a href="https://hugohe3.github.io/ppt-master/"><strong>在线预览</strong></a> ·
  <a href="https://www.hehugo.com/"><strong>关于何雨果</strong></a> ·
  <a href="./examples/"><strong>示例下载</strong></a> ·
  <a href="./docs/zh/faq.md"><strong>常见问题</strong></a> ·
  <a href="mailto:heyug3@gmail.com"><strong>联系我</strong></a>
</p>

<p align="center">
  <img src="docs/assets/hero-liziqi-colors.gif" alt="演示：用 Claude Opus 4.7 从一篇微信文章生成 12 页 PPT" width="860" />
</p>

<p align="center">
  <sub>↑ <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_liziqi_plant_dye_colors">一份 12 页的原生可编辑 PPT</a>，端到端由 <a href="https://mp.weixin.qq.com/s/6ZmBl0uE3sOtD8TJcHfNAw">一个微信公众号链接</a> 通过 Claude Opus 4.7 生成。无需人工设计，不走图片导出——每一个形状、文本框、图表都可以在 PowerPoint 里直接点击编辑。</sub>
</p>

---

丢进一份 PDF、DOCX、网址或 Markdown，拿回一份**原生可编辑的 PowerPoint**——真正的形状、真正的文本框、真正的图表，不是图片。点击任何元素即可编辑。

> **动画** —— 导出的 deck 支持**页间转场**和**页内元素入场动画**，输出为真正的 OOXML 动画（不是嵌入视频），在 PowerPoint 和 Keynote 中按点击逐次播放，无需额外工具。详见 [转场与动画使用指南 →](./docs/zh/animations.md)。

> **运作方式** —— PPT Master 是一套在 AI IDE（Claude Code / Cursor / VS Code + Copilot / Codebuddy 等）里运行的工作流（一个 "skill"）。你在 IDE 的对话框里跟 AI 说"用这份 PDF 做一份 PPT"，AI 按这套工作流在你本机生成一个真正可编辑的 `.pptx`。你不写任何代码——IDE 只是你和 AI 对话的地方。
>
> **你要做的**：装 Python、装一个 AI IDE、把资料放进来。

PPT Master 不一样：

- **真正的 PPT** — 如果一个文件在 PowerPoint 里打不开、不能编辑，它就不应该被叫做 PPT。PPT Master 输出的每个元素都能直接点击修改
- **成本透明可控** — 工具免费开源，唯一成本是你自己的 AI 模型用量。当前主流 AI 工具都已转向按量计费，你用多少付多少——PPT Master 不在此之外增加任何额外订阅费用
- **数据不出本地** — 你的文件不应该为了做一份 PPT 就被上传到别人的服务器。除与 AI 模型的对话外，全流程在你的电脑上完成
- **不锁定平台** — 你的工作流不应该被任何一家公司绑架。Claude Code、Cursor、VS Code Copilot 等均可驱动；Claude、GPT、Gemini、Kimi 等模型均可使用

市面上的 AI PPT 工具大致分四类，PPT Master 只做最后一类：

| 类型 | 产物形态 | 能在 PowerPoint 里逐元素改吗 |
|---|---|:---:|
| 模板填空 | 套模板的 PPTX | 部分可以，受模板限制 |
| 图片式 | 一页一张大图拼成 PPTX | ❌ 整页是图片 |
| HTML 演示 | 网页演示 | ❌ 不是 PPTX |
| **原生可编辑（PPT Master）** | **真 DrawingML 形状、文本框、图表** | ✅ 每个元素都能点开改 |

**[在线预览 →](https://hugohe3.github.io/ppt-master/)** · [`examples/`](./examples/) — 22 个项目，309 页 · **[为什么选 PPT Master？](./docs/zh/why-ppt-master.md)**

## 效果展示

<table>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_magazine_garden.png" alt="杂志风 — 打造小院指南" /><br/><sub><b>杂志风</b> — 暖色调，大图排版，生活方式感</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_academic_medical.png" alt="学术风 — 医学图像分割研究" /><br/><sub><b>学术风</b> — 严谨结构，数据图表，论文答辩场景</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_dark_art_mv.png" alt="暗色艺术风 — MV 深度解析" /><br/><sub><b>暗色艺术风</b> — 电影感深色背景，美术馆陈列感</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_nature_wildlife.png" alt="自然风 — 湿地野生动物纪录" /><br/><sub><b>自然纪录风</b> — 沉浸式摄影，简洁信息层级</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_tech_claude_plans.png" alt="科技风 — Claude AI 订阅方案" /><br/><sub><b>科技 / SaaS 风</b> — 白底卡片，定价表格，产品说明书</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_launch_xiaomi.png" alt="发布会风 — 小米春季新品" /><br/><sub><b>发布会风</b> — 高对比度，参数突出，苹果/小米发布会感</sub></td>
  </tr>
</table>

---

## 关于作者

我是何雨果（Hugo He），投融资领域从业者（注册会计师 · 资产评估师 · 咨询工程师（投资）），每周要审阅和修改大量 PPT。受够了 AI 工具只能导图片不能编辑——所以做了这个。

🌐 [个人网站](https://www.hehugo.com/) · 📧 [heyug3@gmail.com](mailto:heyug3@gmail.com) · 🐙 [@hugohe3](https://github.com/hugohe3)

---

## 快速开始

### 1. 前置条件

**只需装 Python 即可。** 其余依赖通过 `pip install -r requirements.txt` 一次装齐。

| 依赖 | 是否必须 | 用途 |
|------|:--------:|------|
| [Python](https://www.python.org/downloads/) 3.10+ | ✅ **必需** | 核心运行时——唯一真正需要安装的东西 |

> **一句话总结** — 装好 Python，跑一行 `pip install -r requirements.txt`，就可以开始生成 PPT 了。

<details open>
<summary><strong>Windows</strong> — 请看专门的手把手安装指南 ⚠️</summary>

Windows 需要一些额外步骤（PATH 设置、执行策略等）。我们为 Windows 用户写了一份**手把手安装指南**：

**📖 [Windows 安装指南](./docs/zh/windows-installation.md)** — 从零到跑通第一份 PPT，10 分钟搞定。

简要流程：从 [python.org](https://www.python.org/downloads/) 下载 Python → **安装时勾选 "Add to PATH"** → `pip install -r requirements.txt` → 完成。
</details>

<details>
<summary><strong>macOS / Linux</strong> — 安装即用</summary>

```bash
# macOS
brew install python
pip install -r requirements.txt

# Ubuntu / Debian
sudo apt install python3 python3-pip
pip install -r requirements.txt
```
</details>

<details>
<summary><strong>边缘场景备用方案</strong> — 99% 的用户用不到</summary>

下面两个外部程序只作为极端场景的兜底。**绝大多数用户根本不需要装**，只有遇到以下具体场景才装：

| 备用方案 | 只在以下情况才装 |
|---------|-----------------|
| [Node.js](https://nodejs.org/) 18+ | 你需要抓取微信公众号文章，**且**你的 Python + 系统 + CPU 组合下 `curl_cffi`（`requirements.txt` 里已默认安装）没有预编译 wheel。正常安装下 `web_to_md.py` 已能通过 `curl_cffi` 直接抓微信。 |
| [Pandoc](https://pandoc.org/) | 你需要转 `.doc`、`.odt`、`.rtf`、`.tex`、`.rst`、`.org`、`.typ` 这些小众格式。`.docx`、`.html`、`.epub`、`.ipynb` 已由 Python 原生处理，不需要 pandoc。 |

```bash
# macOS（仅在上述条件成立时才装）
brew install node
brew install pandoc

# Ubuntu / Debian
sudo apt install nodejs npm
sudo apt install pandoc
```
</details>

### 2. 选择一个 Agent

PPT Master 在**任何具备 agent 能力**（可读写文件、执行命令、持续多轮对话）的工具里都能跑。

| 类型 | 代表工具 | 说明 |
|---|---|---|
| **IDE 内置 agent** | • VS Code 架构（含 [VS Code](https://code.visualstudio.com/) 本体及分支与衍生）：[Cursor](https://cursor.sh/)、Trae、Codebuddy IDE、[Windsurf](https://codeium.com/windsurf)、Void 等<br>• 其他架构：[Zed](https://zed.dev/) 等 | 编辑器原生集成 agent |
| **IDE 插件 / 扩展** | [GitHub Copilot](https://github.com/features/copilot)、[Claude Code](https://claude.ai/code)（VS Code / JetBrains 扩展）、[Cline](https://cline.bot/)、[Continue](https://continue.dev/)、Roo Code、通义灵码、CodeGeeX 等 | 装在 VS Code / JetBrains 等宿主里使用 |
| **CLI agent** | [Claude Code](https://claude.ai/code) CLI、[Codex CLI](https://github.com/openai/codex)、[Aider](https://aider.chat/)、Gemini CLI 等 | 终端里运行，适合脚本化 / 远程 / 服务器场景 |

> **模型推荐**：[Claude](https://claude.ai/) Opus / Sonnet 效果最好且测试最充分。其他主流模型（GPT、Gemini、Kimi、MiniMax 等）也能驱动，但 SVG 绝对坐标布局精度会有差异。
>
**🔑 想用 Claude / GPT / Gemini 但还没有渠道？** 本项目赞助商 **[PackyCode](https://www.packyapi.com/register?aff=ppt-master)** 可以解决大多数卡点——没有 API Key、无法直连、没有境外信用卡无法订阅、或者只是不想为偶尔使用付整月费，PackyCode 都能让你按量调用 Claude、GPT、Gemini 等主流模型，支持国内支付，开箱即用。充值时填写优惠码 **`ppt-master`** 享 9 折。

### 3. 配置项目

**方式 A — 下载 ZIP**（无需安装 Git）：
[GitHub](https://github.com/hugohe3/ppt-master) → **Code → Download ZIP** · [AtomGit](https://atomgit.com/hugohe3/ppt-master) → **克隆/下载 → 下载ZIP**（国内网速更快）

**方式 B — Git clone**（需先安装 [Git](https://git-scm.com/downloads)）：

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

日常更新（仅方式 B）：`python3 skills/ppt-master/scripts/update_repo.py`

### 4. 开始创作

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

> **输出说明：** 原生形状版主 `.pptx`（可直接编辑）保存至 `exports/<name>_<timestamp>.pptx`；SVG 快照版 `_svg.pptx` 与 `svg_output/` 副本归档至 `backup/<timestamp>/`，便于回溯视觉参考或免去 LLM 重跑直接重建 pptx。需要 Office 2016+。

> **AI 迷失上下文？** 让它先读 `skills/ppt-master/SKILL.md`。

> **遇到问题？** 查看 **[常见问题](./docs/zh/faq.md)** — 涵盖模型选择、排版问题、导出异常等，基于真实用户反馈持续更新。

### 5. AI 生图配置（可选）

```bash
cp .env.example .env    # 然后填入你的 API Key
```

```env
IMAGE_BACKEND=openai                        # 必填——必须显式指定
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-image-2
```

支持多家后端，按 Core / Extended / Experimental 分级。运行 `python3 skills/ppt-master/scripts/image_gen.py --list-backends` 查看完整清单。环境变量优先于 `.env`。使用各家独立的 Key（`OPENAI_API_KEY`、`GEMINI_API_KEY` 等）——不支持全局 `IMAGE_API_KEY`。

> **建议：** `gpt-image-2` 目前综合质量最佳。Gemini 同样支持——下载 full size 后可用 `scripts/gemini_watermark_remover.py` 去水印。

---

## 文档导航

| | 文档 | 说明 |
|---|------|------|
| 🆚 | [为什么选 PPT Master](./docs/zh/why-ppt-master.md) | 与 Gamma、Copilot 等工具的对比 |
| 🪟 | [Windows 安装指南](./docs/zh/windows-installation.md) | Windows 用户手把手安装教程 |
| 📖 | [SKILL.md](./skills/ppt-master/SKILL.md) | 核心流程与规则 |
| 🎨 | [创建自定义模板](./skills/ppt-master/workflows/create-template.md) | 独立工作流，构建你自己的品牌或行业模板 |
| 📐 | [画布格式](./skills/ppt-master/references/canvas-formats.md) | PPT 16:9、小红书、朋友圈等 10+ 种格式 |
| 🎬 | [转场与动画](./docs/zh/animations.md) | 页间转场和页内元素入场动画 |
| 🛠️ | [脚本与工具](./skills/ppt-master/scripts/README.md) | 所有脚本和命令 |
| 💼 | [示例](./examples/README.md) | 22 个项目，309 页 |
| 🏗️ | [技术路线](./docs/zh/technical-design.md) | 架构、设计哲学、为什么选 SVG |
| ❓ | [常见问题](./docs/zh/faq.md) | 模型选择、费用、排版问题排查、自定义模板 |

---

## 贡献

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 开源协议

[MIT](LICENSE)

## 致谢

[SVG Repo](https://www.svgrepo.com/) · [Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author))（CRAP 设计原则）

## 联系与合作

欢迎合作交流、将 PPT Master 集成到你的工作流，或者单纯提问：

- 💬 **提问与分享** — [GitHub Discussions](https://github.com/hugohe3/ppt-master/discussions)
- 🐛 **Bug 反馈与功能建议** — [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)
- 🌐 **了解更多** — [www.hehugo.com](https://www.hehugo.com/)

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
<a href="https://m.do.co/c/547f129aabe1"><img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" alt="Powered by DigitalOcean" height="40" /></a>

**个人赞助**

如果 PPT Master 帮到了你，任何金额的个人赞助都能帮助项目持续更新、保持免费开源。

<a href="https://paypal.me/hugohe3"><img src="https://img.shields.io/badge/PayPal-赞助-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="通过 PayPal 赞助" /></a>

<img src="docs/assets/alipay-qr.jpg" alt="支付宝收款码" width="220" />

---

Made with ❤️ by [何雨果 Hugo He](https://www.hehugo.com/) — 如果这个项目对你有帮助，请给一个 ⭐，也欢迎[赞助支持](#赞助与支持)。

<sub>官方发布渠道：<a href="https://github.com/hugohe3/ppt-master">GitHub</a>（主仓库）· <a href="https://atomgit.com/hugohe3/ppt-master">AtomGit</a>（镜像）。其他平台转发版本均为非官方版本。MIT 协议，使用需保留署名。</sub>

[⬆ 回到顶部](#ppt-master--ai-生成原生可编辑-pptx支持任意文档输入)
