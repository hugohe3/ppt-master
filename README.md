# PPT Master — AI generates natively editable PPTX from any document

[![Version](https://img.shields.io/badge/version-v2.3.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)
[![AtomGit stars](https://atomgit.com/hugohe3/ppt-master/star/badge.svg)](https://atomgit.com/hugohe3/ppt-master)

English | [中文](./README_CN.md)

<p align="center">
  <a href="https://hugohe3.github.io/ppt-master/"><strong>Live Demo</strong></a> ·
  <a href="https://www.hehugo.com/"><strong>About Hugo He</strong></a> ·
  <a href="./examples/"><strong>Examples</strong></a> ·
  <a href="./docs/faq.md"><strong>FAQ</strong></a> ·
  <a href="mailto:heyug3@gmail.com"><strong>Contact</strong></a>
</p>

---

Drop in a PDF, DOCX, URL, or Markdown — get back a **natively editable PowerPoint** with real shapes, real text boxes, and real charts. Not images. Click anything and edit it.

**What makes it different:**

- Every element is a real PowerPoint object (DrawingML) — no "Convert to Shape" needed
- Works with Claude Code, Cursor, VS Code Copilot, and other AI editors
- 10+ output formats: PPT 16:9, social media cards, marketing posters, and more
- Low cost — as little as **$0.08 per presentation** with VS Code Copilot; even non-Opus models produce decent results

**[See live examples →](https://hugohe3.github.io/ppt-master/)** · [`examples/`](./examples/) — 15 projects, 229 pages

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

I'm a finance professional (CPA · CPV · Consulting Engineer) who got tired of spending hours on presentations that could be automated. So I built this.

PPT Master started from a simple frustration: existing AI slide tools export images, not editable shapes. As someone who reviews and edits hundreds of slides in investment and consulting work, that was unacceptable. I wanted real DrawingML — click on any element and change it, just like you built it by hand.

This project is my attempt to bridge the gap between **domain expertise** and **product engineering** — turning a complex professional pain point into an open-source tool that anyone can use.

🌐 [Personal website](https://www.hehugo.com/) · 📧 [heyug3@gmail.com](mailto:heyug3@gmail.com) · 🐙 [@hugohe3](https://github.com/hugohe3)

---

## Quick Start

### 1. Install

**Required:** [Python](https://www.python.org/downloads/) 3.10+ · **Optional:** [Node.js](https://nodejs.org/) 18+ (for WeChat page conversion) · [Pandoc](https://pandoc.org/) (for DOCX/EPUB conversion)

```bash
# macOS
brew install python
brew install node                # optional — for WeChat page conversion
brew install pandoc              # optional — for DOCX/EPUB conversion

# Ubuntu/Debian
sudo apt install python3 python3-pip
sudo apt install nodejs npm      # optional
sudo apt install pandoc          # optional

# Windows — download from python.org, nodejs.org, pandoc.org
```

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

To update later: `python3 skills/ppt-master/scripts/update_repo.py`

### 2. Pick an AI Editor

| Tool | Rating | Notes |
|------|:------:|-------|
| **[Claude Code](https://claude.ai/)** | ⭐⭐⭐ | Best results — native Opus, largest context |
| [Cursor](https://cursor.sh/) / [VS Code + Copilot](https://code.visualstudio.com/) | ⭐⭐ | Good alternatives |
| Codebuddy IDE | ⭐⭐ | Best for Chinese models (Kimi 2.5, MiniMax 2.7) |

### 3. Create

Open the AI chat panel and describe what you want:

```
You: I have a Q3 quarterly report that needs to be made into a PPT

AI:  Sure. Let's confirm the design spec:
     [Template] B) No template
     [Format]   PPT 16:9
     [Pages]    8-10 pages
     ...
```

The AI handles everything — content analysis, visual design, SVG generation, and PPTX export.

> **Output:** Two timestamped files are saved to `exports/` — a native-shapes `.pptx` (directly editable) and an `_svg.pptx` snapshot for visual reference. Requires Office 2016+.

> **AI lost context?** Ask it to read `skills/ppt-master/SKILL.md`.

### 4. AI Image Generation (Optional)

```bash
cp .env.example .env    # then edit with your API key
```

```env
IMAGE_BACKEND=gemini                        # required — must be set explicitly
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

Supported backends: `gemini` · `openai` · `qwen` · `zhipu` · `volcengine` · `stability` · `bfl` · `ideogram` · `siliconflow` · `fal` · `replicate`

Run `python3 skills/ppt-master/scripts/image_gen.py --list-backends` to see tiers. Environment variables override `.env`. Use provider-specific keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, etc.) — global `IMAGE_API_KEY` is not supported.

> **Tip:** For best quality, generate images in [Gemini](https://gemini.google.com/) and select **Download full size**. Remove the watermark with `scripts/gemini_watermark_remover.py`.

---

## Documentation

| | Document | Description |
|---|----------|-------------|
| 📖 | [SKILL.md](./skills/ppt-master/SKILL.md) | Core workflow and rules |
| 📐 | [Canvas Formats](./skills/ppt-master/references/canvas-formats.md) | PPT 16:9, Xiaohongshu, WeChat, and 10+ formats |
| 🛠️ | [Scripts & Tools](./skills/ppt-master/scripts/README.md) | All scripts and commands |
| 💼 | [Examples](./examples/README.md) | 15 projects, 229 pages |
| 🏗️ | [Technical Design](./docs/technical-design.md) | Architecture, design philosophy, why SVG |
| ❓ | [FAQ](./docs/faq.md) | Cost, editing, custom templates |

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to get involved.

## License

[MIT](LICENSE)

## Acknowledgments

[SVG Repo](https://www.svgrepo.com/) · [Tabler Icons](https://github.com/tabler/tabler-icons) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) (CRAP principles) · McKinsey, BCG, Bain

## Contact & Collaboration

Looking to collaborate, integrate PPT Master into your workflow, or just have questions?

- 💬 **Open-source discussions** — [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)
- 📧 **Business & consulting inquiries** — [heyug3@gmail.com](mailto:heyug3@gmail.com)
- 🌐 **Learn more about the author** — [www.hehugo.com](https://www.hehugo.com/)

---

## Star History

If this project helps you, please give it a ⭐!

<a href="https://star-history.com/#hugohe3/ppt-master&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
 </picture>
</a>

---

## Supported by DigitalOcean

<p>This project is supported by:</p>
<p>
  <a href="https://m.do.co/c/547f129aabe1">
    <img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" alt="Powered by DigitalOcean" width="201" />
  </a>
</p>

---

## Sponsor

If this project saves you time, consider buying me a coffee!

**Alipay / 支付宝**

<img src="docs/assets/alipay-qr.jpg" alt="Alipay QR Code" width="250" />

---

Made with ❤️ by [Hugo He](https://www.hehugo.com/)

[⬆ Back to Top](#ppt-master--ai-generates-natively-editable-pptx-from-any-document)
