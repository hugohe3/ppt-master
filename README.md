# PPT Master — AI generates natively editable PPTX from any document

[![Version](https://img.shields.io/badge/version-v2.3.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)
[![AtomGit stars](https://atomgit.com/hugohe3/ppt-master/star/badge.svg)](https://atomgit.com/hugohe3/ppt-master)

English | [中文](./README_CN.md)

<p align="center">
  <sub>This project is kept free and open source with the support of <a href="https://www.packyapi.com/register?aff=ppt-master">PackyCode</a> and other sponsors.</sub>
</p>

<table>
  <tr>
    <td width="180"><a href="https://www.packyapi.com/register?aff=ppt-master"><img src="docs/assets/sponsors/packycode.png" alt="PackyCode" width="150"></a></td>
    <td>Thanks to PackyCode for sponsoring this project! PackyCode is a reliable and efficient API relay service provider, offering relay services for Claude Code, Codex, Gemini, and more. PackyCode provides special discounts for our project users: register using <a href="https://www.packyapi.com/register?aff=ppt-master">this link</a> and enter the promo code <strong>ppt-master</strong> during recharge to get 10% off.</td>
  </tr>
</table>

<p align="center">
  <a href="https://hugohe3.github.io/ppt-master/"><strong>Live Demo</strong></a> ·
  <a href="https://www.hehugo.com/"><strong>About Hugo He</strong></a> ·
  <a href="./examples/"><strong>Examples</strong></a> ·
  <a href="./docs/faq.md"><strong>FAQ</strong></a> ·
  <a href="mailto:heyug3@gmail.com"><strong>Contact</strong></a>
</p>

<p align="center">
  <img src="docs/assets/hero-liziqi-colors.gif" alt="Demo: generating a 12-page PPT from a WeChat article with Claude Opus 4.7" width="860" />
</p>

<p align="center">
  <sub>↑ A <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_liziqi_plant_dye_colors">12-page natively editable deck</a>, generated end-to-end from <a href="https://mp.weixin.qq.com/s/6ZmBl0uE3sOtD8TJcHfNAw">a single WeChat article URL</a> using Claude Opus 4.7. No manual design. No image export. Every shape, text box, and chart is clickable and editable in PowerPoint.</sub>
</p>

---

Drop in a PDF, DOCX, URL, or Markdown — get back a **natively editable PowerPoint** with real shapes, real text boxes, and real charts. Not images. Click anything and edit it.

> **How it works** — PPT Master is a workflow (a "skill") that works inside AI IDEs like Claude Code, Cursor, VS Code + Copilot, or Codebuddy. You chat with the AI — "make a deck from this PDF" — and it follows the workflow to produce a real editable `.pptx` on your computer. No coding on your side; the IDE is just where the conversation happens.
>
> **What you'll do**: install Python, install an AI IDE, drop in your material.

PPT Master is different:

- **Real PowerPoint** — if a file can't be opened and edited in PowerPoint, it shouldn't be called a PPT. Every element PPT Master outputs is directly clickable and editable
- **Transparent, predictable cost** — the tool is free and open source; the only cost is your AI model usage. As AI tools move to usage-based billing, you pay exactly what you consume — no separate PPT subscription added on top
- **Data stays local** — your files shouldn't have to be uploaded to someone else's server just to make a presentation. Apart from AI model communication, the entire pipeline runs on your machine
- **No platform lock-in** — your workflow shouldn't be held hostage by any single company. Works with Claude Code, Cursor, VS Code Copilot, and more; supports Claude, GPT, Gemini, Kimi, and other models

AI presentation tools roughly fall into four categories. PPT Master only does the last one:

| Category | Output | Editable element-by-element in PowerPoint? |
|---|---|:---:|
| Template fill-in | PPTX built from a fixed template | Partially — limited by the template |
| Image-based | One large image per slide, packed into PPTX | ❌ each slide is a picture |
| HTML presentation | Web-based deck | ❌ not a PPTX |
| **Native editable (PPT Master)** | **Real DrawingML shapes, text boxes, charts** | ✅ click any element to edit |

**[See live examples →](https://hugohe3.github.io/ppt-master/)** · [`examples/`](./examples/) — 22 projects, 309 pages · **[Why PPT Master?](./docs/why-ppt-master.md)**

## Gallery

<table>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_magazine_garden.png" alt="Magazine style — Garden building guide" /><br/><sub><b>Magazine</b> — warm earthy tones, photo-rich layout</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_academic_medical.png" alt="Academic style — Medical image segmentation research" /><br/><sub><b>Academic</b> — structured research format, data-driven</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_dark_art_mv.png" alt="Dark art style — Music video analysis" /><br/><sub><b>Dark Art</b> — cinematic dark background, gallery aesthetic</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_nature_wildlife.png" alt="Nature style — Wildlife wetland documentary" /><br/><sub><b>Nature Documentary</b> — immersive photography, minimal UI</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/screenshots/preview_tech_claude_plans.png" alt="Tech style — Claude AI subscription plans" /><br/><sub><b>Tech / SaaS</b> — clean white cards, pricing table layout</sub></td>
    <td align="center"><img src="docs/assets/screenshots/preview_launch_xiaomi.png" alt="Product launch style — Xiaomi spring release" /><br/><sub><b>Product Launch</b> — high contrast, bold specs highlight</sub></td>
  </tr>
</table>

---

## Built by Hugo He

I'm a finance professional (CPA · CPV · Consulting Engineer (Investment)) who reviews and edits hundreds of slides every week. I got tired of AI tools that output images instead of editable shapes — so I built this.

🌐 [Personal website](https://www.hehugo.com/) · 📧 [heyug3@gmail.com](mailto:heyug3@gmail.com) · 🐙 [@hugohe3](https://github.com/hugohe3)

---

## Quick Start

### 1. Prerequisites

**You only need Python.** Everything else is installed via `pip install -r requirements.txt`.

| Dependency | Required? | What it does |
|------------|:---------:|--------------|
| [Python](https://www.python.org/downloads/) 3.10+ | ✅ **Yes** | Core runtime — the only thing you actually need to install |

> **TL;DR** — Install Python, run `pip install -r requirements.txt`, and you're ready to generate presentations.

<details open>
<summary><strong>Windows</strong> — see the dedicated step-by-step guide ⚠️</summary>

Windows requires a few extra steps (PATH setup, execution policy, etc.). We wrote a **step-by-step guide** specifically for Windows users:

**📖 [Windows Installation Guide](./docs/windows-installation.md)** — from zero to a working presentation in 10 minutes.

Quick version: download Python from [python.org](https://www.python.org/downloads/) → **check "Add to PATH"** during install → `pip install -r requirements.txt` → done.
</details>

<details>
<summary><strong>macOS / Linux</strong> — install and go</summary>

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
<summary><strong>Edge-case fallbacks</strong> — 99% of users don't need these</summary>

Two external tools exist as fallbacks for edge cases. **Most users will never need them** — install only if you hit one of the specific scenarios below.

| Fallback | Install only if… |
|----------|-----------------|
| [Node.js](https://nodejs.org/) 18+ | You need to import WeChat Official Account articles **and** `curl_cffi` (part of `requirements.txt`) has no prebuilt wheel for your Python + OS + CPU combination. In normal setups `web_to_md.py` handles WeChat directly through `curl_cffi`. |
| [Pandoc](https://pandoc.org/) | You need to convert legacy formats: `.doc`, `.odt`, `.rtf`, `.tex`, `.rst`, `.org`, or `.typ`. `.docx`, `.html`, `.epub`, `.ipynb` are handled natively by Python — no pandoc required. |

```bash
# macOS (only if the above conditions apply)
brew install node
brew install pandoc

# Ubuntu / Debian
sudo apt install nodejs npm
sudo apt install pandoc
```
</details>

### 2. Pick an Agent

PPT Master runs in **any tool with agent capability** — read/write files, execute commands, and sustain multi-turn conversation.

| Type | Examples | Notes |
|---|---|---|
| **IDE-native agent** | • VS Code architecture ([VS Code](https://code.visualstudio.com/) itself, plus forks & derivatives): [Cursor](https://cursor.sh/), Trae, Codebuddy IDE, [Windsurf](https://codeium.com/windsurf), Void, etc.<br>• Other architectures: [Zed](https://zed.dev/), etc. | Editor with a built-in agent |
| **IDE plugin / extension** | [GitHub Copilot](https://github.com/features/copilot), [Claude Code](https://claude.ai/code) (VS Code / JetBrains extension), [Cline](https://cline.bot/), [Continue](https://continue.dev/), Roo Code, etc. | Installed inside hosts like VS Code or JetBrains |
| **CLI agent** | [Claude Code](https://claude.ai/code) CLI, [Codex CLI](https://github.com/openai/codex), [Aider](https://aider.chat/), Gemini CLI, etc. | Runs in the terminal; suits scripting, remote, or server use |

> **Model recommendation**: [Claude](https://claude.ai/) Opus / Sonnet works best and is most tested. Other mainstream models (GPT, Gemini, Kimi, MiniMax, etc.) also work, but SVG absolute-coordinate layout precision varies.

**🔑 Want to use Claude / GPT / Gemini but don't have access yet?** Project sponsor **[PackyCode](https://www.packyapi.com/register?aff=ppt-master)** can help — whether you lack an API key, can't connect directly, have no way to subscribe, or just don't want to pay a full monthly fee for occasional use, PackyCode lets you call Claude, GPT, Gemini and more on a pay-as-you-go basis, no subscription required. Enter promo code **`ppt-master`** when topping up for 10% off.

### 3. Set Up

**Option A — Download ZIP** (no Git required): click **Code → Download ZIP** on the [GitHub page](https://github.com/hugohe3/ppt-master), then unzip.

**Option B — Git clone** (requires [Git](https://git-scm.com/downloads) installed):

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

To update later (Option B only): `python3 skills/ppt-master/scripts/update_repo.py`

### 4. Create

**Provide source materials (recommended):** Place your PDF, DOCX, images, or other files in the `projects/` directory, then tell the AI chat panel which files to use. The quickest way to get the path: right-click the file in your file manager or IDE sidebar → **Copy Path** (or **Copy Relative Path**) and paste it directly into the chat.

```
You: Please create a PPT from projects/q3-report/sources/report.pdf
```

**Paste content directly:** You can also paste text content straight into the chat window and the AI will generate a PPT from it.

```
You: Please turn the following into a PPT: [paste your content here...]
```

Either way, the AI will first confirm the design spec:

```
AI:  Sure. Let's confirm the design spec:
     [Template] B) Free design
     [Format]   PPT 16:9
     [Pages]    8-10 pages
     ...
```

The AI handles everything — content analysis, visual design, SVG generation, and PPTX export.

> **Output:** Two timestamped files are saved to `exports/` — a native-shapes `.pptx` (directly editable) and an `_svg.pptx` snapshot for visual reference. Requires Office 2016+.

> **AI lost context?** Ask it to read `skills/ppt-master/SKILL.md`.

> **Something went wrong?** Check the **[FAQ](./docs/faq.md)** — it covers model selection, layout issues, export problems, and more. Continuously updated from real user reports.

### 5. AI Image Generation (Optional)

```bash
cp .env.example .env    # then edit with your API key
```

```env
IMAGE_BACKEND=gemini                        # required — must be set explicitly
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

Multiple backends are supported across Core / Extended / Experimental tiers. Run `python3 skills/ppt-master/scripts/image_gen.py --list-backends` to see the full list. Environment variables override `.env`. Use provider-specific keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, etc.) — global `IMAGE_API_KEY` is not supported.

> **Tip:** For best quality, generate images in [Gemini](https://gemini.google.com/) and select **Download full size**. Remove the watermark with `scripts/gemini_watermark_remover.py`.

---

## Documentation

| | Document | Description |
|---|----------|-------------|
| 🆚 | [Why PPT Master](./docs/why-ppt-master.md) | How it compares to Gamma, Copilot, and other AI tools |
| 🪟 | [Windows Installation](./docs/windows-installation.md) | Step-by-step setup guide for Windows users |
| 📖 | [SKILL.md](./skills/ppt-master/SKILL.md) | Core workflow and rules |
| 🎨 | [Create a Custom Template](./skills/ppt-master/workflows/create-template.md) | Standalone workflow for building your own brand or industry template |
| 📐 | [Canvas Formats](./skills/ppt-master/references/canvas-formats.md) | PPT 16:9, Xiaohongshu, WeChat, and 10+ formats |
| 🛠️ | [Scripts & Tools](./skills/ppt-master/scripts/README.md) | All scripts and commands |
| 💼 | [Examples](./examples/README.md) | 22 projects, 309 pages |
| 🏗️ | [Technical Design](./docs/technical-design.md) | Architecture, design philosophy, why SVG |
| ❓ | [FAQ](./docs/faq.md) | Model selection, cost, layout troubleshooting, custom templates |

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to get involved.

## License

[MIT](LICENSE)

## Acknowledgments

[SVG Repo](https://www.svgrepo.com/) · [Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) (CRAP principles)

## Contact & Collaboration

Looking to collaborate, integrate PPT Master into your workflow, or just have questions?

- 💬 **Questions & sharing** — [GitHub Discussions](https://github.com/hugohe3/ppt-master/discussions)
- 🐛 **Bug reports & feature requests** — [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)
- 🌐 **Learn more about the author** — [www.hehugo.com](https://www.hehugo.com/)

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

## Sponsors & Support

PPT Master is currently built and maintained primarily by me. Every new template, bug fix, and documentation update takes ongoing resources — currently shared by the sponsors and individual supporters below.

**Corporate sponsors**

<a href="https://www.packyapi.com/register?aff=ppt-master"><img src="https://img.shields.io/badge/PackyCode-AI_API_Relay-4A90E2?style=for-the-badge" alt="PackyCode" /></a>
&nbsp;
<a href="https://m.do.co/c/547f129aabe1"><img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" alt="Powered by DigitalOcean" height="28" /></a>

**Individual support**

If PPT Master has been helpful to you, individual support of any amount helps keep the project moving and free.

<a href="https://paypal.me/hugohe3"><img src="https://img.shields.io/badge/PayPal-Sponsor-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Sponsor via PayPal" /></a>

<img src="docs/assets/alipay-qr.jpg" alt="Alipay QR Code" width="220" />

---

Made with ❤️ by [Hugo He](https://www.hehugo.com/) — if this project helps you, please give it a ⭐ and consider [sponsoring](#sponsors--support).

<sub>Official distribution: <a href="https://github.com/hugohe3/ppt-master">GitHub</a> (primary) · <a href="https://atomgit.com/hugohe3/ppt-master">AtomGit</a> (mirror). Redistributions on other platforms are unofficial. MIT licensed — attribution required.</sub>

[⬆ Back to Top](#ppt-master--ai-generates-natively-editable-pptx-from-any-document)
