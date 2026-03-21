# PPT Master — AI generates editable, beautifully designed presentations from any document

[![Version](https://img.shields.io/badge/version-v2.0.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)

English | [中文](./README.md)

Drop in a PDF, URL, or Markdown file — AI generates **beautifully designed presentations that you can edit directly in PowerPoint**. Supports PPT 16:9, social media cards, marketing posters, and 10+ other formats.

> 💡 **Major Update**: The project architecture has undergone a massive upgrade (Skill-based architecture):
> 1. **Lower Token Consumption & Model Dependency**: Significantly reduced token consumption. Now, even non-Opus models can generate decent results.
> 2. **High Extensibility**: The `skills` folder is organized according to the Agent Skills standard, with each subdirectory being a fully self-contained Skill. It can be natively invoked by dropping it into the skills directory of compatible AI clients (e.g., `.claude/skills/` or `~/.claude/skills/` for Claude Code; global skills directory referenced via `.agent/workflows/` for Antigravity; `.github/skills/` or `~/.copilot/skills/` for GitHub Copilot).
> 3. **Stable Fallback**：Although the previous multi-platform architecture consumes more tokens, it has been more extensively tested. If you experience instability with the current version, you can always fall back to the last release of the old architecture: [v1.3.0](https://github.com/hugohe3/ppt-master/tree/v1.3.0).

> **Online Examples**: [GitHub Pages Preview](https://hugohe3.github.io/ppt-master/) — See actual generated results

> **Video Demo**: [YouTube](https://www.youtube.com/watch?v=jM2fHmvMwx0) | [Bilibili](https://www.bilibili.com/video/BV1ZZAFzWEPJ/)

---

## 🎴 Featured Examples

> **Example Library**: [`examples/`](./examples/) · **15 projects** · **229 pages**

| Category | Project | Pages | Features |
| -------- | ------- | :---: | -------- |
| 🏢 **Consulting Style** | [Attachment in Psychotherapy](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E5%BF%83%E7%90%86%E6%B2%BB%E7%96%97%E4%B8%AD%E7%9A%84%E4%BE%9D%E6%81%8B) |  32   | Top consulting style, largest scale example |
|                         | [Building Effective AI Agents](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E6%9E%84%E5%BB%BA%E6%9C%89%E6%95%88AI%E4%BB%A3%E7%90%86_Anthropic) |  15   | Anthropic engineering blog, AI Agent architecture |
|                         | [Chongqing Regional Report](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E9%87%8D%E5%BA%86%E5%B8%82%E5%8C%BA%E5%9F%9F%E6%8A%A5%E5%91%8A_ppt169_20251213) |  20   | Regional fiscal analysis |
|                         | [Ganzi Prefecture Economic Analysis](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%A1%B6%E7%BA%A7%E5%92%A8%E8%AF%A2%E9%A3%8E_%E7%94%98%E5%AD%9C%E5%B7%9E%E7%BB%8F%E6%B5%8E%E8%B4%A2%E6%94%BF%E5%88%86%E6%9E%90) |  17   | Government fiscal analysis, Tibetan cultural elements |
| 🎨 **General Flexible** | [Debug Six-Step Method](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%80%9A%E7%94%A8%E7%81%B5%E6%B4%BB%2B%E4%BB%A3%E7%A0%81_debug%E5%85%AD%E6%AD%A5%E6%B3%95) |  10   | Dark tech style |
|                         | [Chongqing University Thesis Format](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E9%80%9A%E7%94%A8%E7%81%B5%E6%B4%BB%2B%E5%AD%A6%E6%9C%AF_%E9%87%8D%E5%BA%86%E5%A4%A7%E5%AD%A6%E8%AE%BA%E6%96%87%E6%A0%BC%E5%BC%8F%E6%A0%87%E5%87%86) |  11   | Academic standards guide |
| ✨ **Creative Style**   | [I Ching Qian Hexagram Study](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E6%98%93%E7%90%86%E9%A3%8E_%E5%9C%B0%E5%B1%B1%E8%B0%A6%E5%8D%A6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6) |  20   | I Ching aesthetics, Yin-Yang design |
|                         | [Diamond Sutra Chapter 1 Study](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E7%A6%85%E6%84%8F%E9%A3%8E_%E9%87%91%E5%88%9A%E7%BB%8F%E7%AC%AC%E4%B8%80%E5%93%81%E7%A0%94%E7%A9%B6) |  15   | Zen academic, ink wash whitespace |
|                         | [Git Introduction Guide](https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_%E5%83%8F%E7%B4%A0%E9%A3%8E_git_introduction) |  10   | Pixel retro game style |

📖 [View Complete Examples Documentation](./examples/README.md)

---

## 🚀 Quick Start

### 1. Configure Environment

#### Python Environment (Required)

This project requires **Python 3.8+** for running PDF conversion, SVG post-processing, PPTX export, and other tools.

| Platform | Recommended Installation |
|----------|-------------------------|
| **macOS** | Use [Homebrew](https://brew.sh/): `brew install python` |
| **Windows** | Download installer from [Python Official Website](https://www.python.org/downloads/) |
| **Linux** | Use package manager: `sudo apt install python3 python3-pip` (Ubuntu/Debian) |

> 💡 **Verify Installation**: Run `python3 --version` to confirm version ≥ 3.8

#### Node.js Environment (Optional)

If you need to use the `web_to_md.cjs` tool (for converting web pages from WeChat and other high-security sites), install Node.js.

| Platform | Recommended Installation |
|----------|-------------------------|
| **macOS** | Use [Homebrew](https://brew.sh/): `brew install node` |
| **Windows** | Download LTS version from [Node.js Official Website](https://nodejs.org/) |
| **Linux** | Use [NodeSource](https://github.com/nodesource/distributions): `curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |

> 💡 **Verify Installation**: Run `node --version` to confirm version ≥ 18

### 2. Clone Repository and Install Dependencies

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

> If you encounter permission issues, use `pip install --user -r requirements.txt` or install in a virtual environment.

### 3. Open AI Editor

Recommended AI editors:

| Tool                                                | Rating | Description                                                                   |
| --------------------------------------------------- | :----: | ----------------------------------------------------------------------------- |
| **[Claude Code](https://claude.ai/)**               | ⭐⭐⭐ | **Highly Recommended**! Anthropic official CLI, native Opus support, largest context window |
| Codebuddy IDE                                       |  ⭐⭐  | Great Chinese AI IDE, good support for local models like Kimi 2.5 and MiniMax 2.7 |
| [Cursor](https://cursor.sh/)                        |  ⭐⭐  | Mainstream AI editor, great experience but relatively expensive                |
| [VS Code + Copilot](https://code.visualstudio.com/) |  ⭐⭐  | Microsoft official solution, cost-effective, but limited context window (200k, 35% reserved for output) |
| [Antigravity](https://antigravity.dev/)             |   ⭐   | Free but very limited quota and unstable. Alternative only.                    |

### 4. Start Creating

Open the AI chat panel in your editor and describe what content you want to create:

```
User: I have a Q3 quarterly report that needs to be made into a PPT

AI: Sure. First we'll confirm whether to use a template; after that Strategist will
   continue with the eight confirmations and generate the design spec.
   [Template Option] [Recommended] B) No template
   [Strategist] 1. Canvas format: [Recommended] PPT 16:9
   [Strategist] 2. Page count: [Recommended] 8-10 pages
   ...
```

> 💡 **Model Recommendation**: Claude Opus works best, but most mainstream models today (like Kimi 2.5 and MiniMax 2.7, tested via Codebuddy IDE) can also generate decent results with only minor gaps in layout details. Due to the instability of Opus on some IDEs (like Antigravity), trying other stable AI clients is recommended.

#### Gemini Image Generation API (Optional)

The `nano_banana_gen.py` tool can generate high-quality images via the Gemini API directly within AI clients. Configure the following environment variables before use:

```bash
# Required: Gemini API Key (obtain from https://aistudio.google.com/apikey)
export GEMINI_API_KEY="your-api-key"

# Optional: Custom API endpoint (for proxy services)
export GEMINI_BASE_URL="https://your-proxy-url.com/v1beta"
```

> 💡 **Persist settings**: Add the `export` commands above to `~/.zshrc` (macOS/Linux zsh) or `~/.bashrc` (Linux bash), then restart your terminal.

> 💡 If using the Antigravity proxy, pass the model parameter (`-m gemini-3.1-flash-image`).

> 💡 **AI Lost Context?** Ask the AI to read `skills/ppt-master/SKILL.md` first; use `AGENTS.md` as the repository-level entry overview.

> 💡 **AI Image Generation Tip**: For AI-generated images, we recommend generating them in [Gemini](https://gemini.google.com/) and selecting **Download full size** for higher resolution. Gemini images have a star watermark in the bottom right corner, which can be removed using [gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover) or this project's `skills/ppt-master/scripts/gemini_watermark_remover.py`.

---

## 🏗️ System Architecture

```
User Input (PDF/URL/Markdown)
    ↓
[Source Content Conversion] → pdf_to_md.py / web_to_md.py
    ↓
[Create Project] → project_manager.py init <project_name> --format <format>
    ↓
[Template Option] A) Use existing template B) No template
    ↓
[Need New Template?] → Use /create-template workflow separately
    ↓
[Strategist] - Eight Confirmations & Design Specifications
    ↓
[Image_Generator] (When AI generation is selected)
    ↓
[Executor] - Two-Phase Generation
    ├── Visual Construction Phase: Generate all SVG pages → svg_output/
    └── Logic Construction Phase: Generate complete speaker notes → notes/total.md
    ↓
[Post-processing] → total_md_split.py (split notes) → finalize_svg.py → svg_to_pptx.py
    ↓
Output: Editable PPTX (auto-embeds speaker notes)
    ↓
[Optimizer_CRAP] (Optional, only if the first draft is unsatisfactory)
    ↓
If optimized: re-run post-processing and export
```

> 📖 For the full workflow, start with [SKILL.md](./skills/ppt-master/SKILL.md). For a repository-level overview, see [AGENTS.md](./AGENTS.md).

> 💡 **PPT Editing Tip**: Each page in the exported PPTX is in SVG format. Select the page content in PowerPoint, right-click and choose **"Convert to Shape"** to freely edit all elements. Requires **Office 2016** or later.

---

## 📚 Documentation Navigation

| Document | Description |
|----------|-------------|
| 🧭 [AGENTS.md](./AGENTS.md) | Repository-level entry overview for general AI agents |
| 📖 [SKILL.md](./skills/ppt-master/SKILL.md) | Canonical `ppt-master` workflow and rules |
| 🎨 [Design Guidelines](./skills/ppt-master/references/design-guidelines.md) | Colors, typography, and layout specifications |
| 📐 [Canvas Formats](./skills/ppt-master/references/canvas-formats.md) | PPT, Xiaohongshu (RED), WeChat Moments, and 10+ formats |
| 🖼️ [Image Embedding Guide](./skills/ppt-master/references/svg-image-embedding.md) | SVG image embedding best practices |
| 📊 [Chart Template Library](./skills/ppt-master/templates/charts/) | Standardized chart templates |
| 🔧 [Role Definitions](./skills/ppt-master/references/) | Role definitions and technical references |
| 🛠️ [Toolset](./skills/ppt-master/scripts/README.md) | Usage instructions for all tools |
| 💼 [Examples Index](./examples/README.md) | 15 projects, 229 SVG pages of examples |

---

## 🛠️ Common Commands

```bash
# Initialize project
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169

# Archive source materials into the project folder
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_file_or_url...>

# Note: files outside the workspace are copied by default; files already in the workspace are moved into sources/

# PDF to Markdown
python3 skills/ppt-master/scripts/pdf_to_md.py <PDF_file>

# Post-processing (run in order)
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> -s final
```

> 📖 For complete tool documentation, see [Tools Usage Guide](./skills/ppt-master/scripts/README.md)

---

## 📁 Project Structure

```text
ppt-master/
├── skills/
│   └── ppt-master/                 # Main skill source
│       ├── SKILL.md                #   Main entry: workflow definition
│       ├── workflows/              #   Workflow entry files
│       ├── references/             #   Role definitions and specs
│       ├── scripts/                #   Tool scripts
│       └── templates/              #   Layouts, charts, icons
├── examples/                       # Example projects
├── projects/                       # User project workspace
├── AGENTS.md                       # General AI agent entry
└── CLAUDE.md                       # Dedicated Claude Code CLI entry
```

---

## ❓ FAQ

<details>
<summary><b>Q: Can I edit the generated presentations?</b></summary>

Yes! Each page in the exported PPTX is in SVG format. In PowerPoint, select the content, right-click and choose **"Convert to Shape"** — then all text, shapes, and colors become fully editable. Requires **Office 2016** or later.

</details>

<details>
<summary><b>Q: What's the difference between the three Executors?</b></summary>

- **Executor_General**: General scenarios, flexible layout
- **Executor_Consultant**: General consulting, data visualization
- **Executor_Consultant_Top**: Top consulting (MBB level), 5 core techniques

</details>

<details>
<summary><b>Q: Is Optimizer_CRAP required?</b></summary>

No. Only use it when you need to optimize the visual effects of key pages.

</details>

> 📖 For more questions, see [SKILL.md](./skills/ppt-master/SKILL.md) and [AGENTS.md](./AGENTS.md)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository
2. Create your branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Contribution Areas**: 🎨 Design templates · 📊 Chart components · 📝 Documentation · 🐛 Bug reports · 💡 Feature suggestions

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [SVG Repo](https://www.svgrepo.com/) - Open source icon library
- [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) - CRAP design principles
- McKinsey, Boston Consulting, Bain - Design inspiration

## 📮 Contact

- **Issue**: [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)
- **GitHub**: [@hugohe3](https://github.com/hugohe3)

---

## 🌟 Star History

If this project helps you, please give it a ⭐ Star!

<a href="https://star-history.com/#hugohe3/ppt-master&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=hugohe3/ppt-master&type=Date" />
 </picture>
</a>

---

Made with ❤️ by Hugo He

[⬆ Back to Top](#ppt-master--ai-generates-editable-beautifully-designed-presentations-from-any-document)
