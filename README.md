# PPT Master — AI generates natively editable PPTX from any document

[![Version](https://img.shields.io/github/v/release/hugohe3/ppt-master?label=version&color=blue)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)
[![AtomGit stars](https://atomgit.com/hugohe3/ppt-master/star/badge.svg)](https://atomgit.com/hugohe3/ppt-master)
[![The Agentic Leaderboard](https://www.theagenticleaderboard.com/badges/ppt-master.svg)](https://www.theagenticleaderboard.com/agent/?q=ppt-master)

<p align="center">
  <a href="https://trendshift.io/repositories/25760?utm_source=repository-badge&amp;utm_medium=badge&amp;utm_campaign=badge-repository-25760" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/repositories/25760" alt="hugohe3%2Fppt-master | Trendshift" width="250" height="55"/></a>
</p>

English | [中文](./README_CN.md)

<details open>
<summary>This project is kept free and open source with the support of <a href="https://www.packyapi.com/register?aff=ppt-master">PackyCode</a>, <a href="https://apikey.fun/register?aff=PPT-MASTER">APIKEY.FUN</a>, <a href="https://runapi.co/register?aff=WMLJ">RunAPI</a>, <a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624">YouYun ZhiSuan</a> and other sponsors.</summary>

<table>
  <tr>
    <td width="180"><a href="https://www.packyapi.com/register?aff=ppt-master"><img src="docs/assets/sponsors/packycode.png" alt="PackyCode" width="150"></a></td>
    <td>Thanks to PackyCode for sponsoring this project! PackyCode is a reliable and efficient API relay service provider, offering relay services for Claude Code, Codex, Gemini, and more. PackyCode provides special discounts for our project users: register using <a href="https://www.packyapi.com/register?aff=ppt-master">this link</a> and enter the promo code <strong>ppt-master</strong> during recharge to get 10% off.</td>
  </tr>
  <tr>
    <td width="180"><a href="https://apikey.fun/register?aff=PPT-MASTER"><img src="docs/assets/sponsors/apikey-fun.png" alt="APIKEY.FUN" width="150"></a></td>
    <td>Thanks to APIKEY.FUN for sponsoring this project! APIKEY.FUN is a professional enterprise-grade AI relay service committed to stable, efficient, and low-cost AI access for businesses and developers. The platform supports mainstream models including Claude, OpenAI, and Gemini, with prices as low as <strong>7% of official rates</strong>. Register through <a href="https://apikey.fun/register?aff=PPT-MASTER">our dedicated link</a> for an exclusive perk: <strong>up to 5% off on top-ups, permanently</strong>.</td>
  </tr>
  <tr>
    <td width="180"><a href="https://runapi.co/register?aff=WMLJ"><img src="docs/assets/sponsors/runapi.png" alt="RunAPI" width="150"></a></td>
    <td>Thanks to RunAPI for sponsoring this project! RunAPI is an efficient and stable API platform — a single API Key gives you access to 150+ leading models, including OpenAI, Claude, Gemini, DeepSeek, and Grok, at prices as low as <strong>10% of official rates</strong>, with exceptional stability and seamless compatibility with tools like Claude Code. RunAPI offers an exclusive perk for PPT Master users: register and contact an administrator via <a href="https://runapi.co/register?aff=WMLJ">our dedicated link</a> to claim <strong>¥7 in free credit</strong>.</td>
  </tr>
  <tr>
    <td width="180"><a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624"><img src="docs/assets/sponsors/youyun.png" alt="YouYun ZhiSuan" width="150"></a></td>
    <td>Thanks to YouYun ZhiSuan for sponsoring this project! YouYun ZhiSuan is UCloud's AI cloud platform, providing one-stop API services for mainstream domestic and international models, all accessible with a single key. The platform features cost-effective CodingPlan packages for domestic models (including GLM5.2, Deepseek-v4, and more), along with official channels for stable access to overseas models, meeting diverse development needs. It's compatible with mainstream AI coding tools like Claude Code and Codex, as well as general API calls. The platform supports enterprise-level high concurrency, 24/7 technical support, and self-service invoicing. Register through <a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624">this link</a> to receive up to <strong>¥10 in free credits</strong>. This project has been built into an Agent — <strong>PPT Master</strong> — ready to use without local deployment.</td>
  </tr>
</table>

</details>

> **AI generates your deck — it doesn't fill in a template.** PPT Master is a workflow that runs inside AI IDEs (Claude Code, Cursor, VS Code + Copilot, etc.): hand the AI your PDF / DOCX / web pages, and it produces a real PowerPoint on your machine — every element editable in PowerPoint, your data stays local, no platform or model lock-in. How it works and where the limits are → [Product Positioning](#product-positioning).

<p align="center">
  <a href="https://hugohe3.github.io/ppt-master/"><strong>Live Demo</strong></a> ·
  <a href="./examples/"><strong>Examples</strong></a> ·
  <a href="./docs/faq.md"><strong>FAQ</strong></a> ·
  <a href="./docs/roadmap.md"><strong>Roadmap</strong></a>
</p>

<h3 align="center">Download the new <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_attention_is_all_you_need/exports/attention_is_all_you_need_narrated.pptx">narrated <em>Attention Is All You Need</em> deck</a> — play it in PowerPoint and every slide reads itself out loud. That's just the tip of what PPT Master can do.</h3>

<table>
  <tr>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_pritzker_2026"><img src="docs/assets/screenshots/preview_pritzker_2026.png" alt="Editorial magazine — Pritzker 2026 architecture review" /></a><br/>
      <sub><b>Editorial Magazine</b> — architecture photography, calm typographic grid<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_pritzker_2026">Flip online</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_pritzker_2026/exports/pritzker_2026.pptx">Download .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_global_ai_capital_2026"><img src="docs/assets/screenshots/preview_global_ai_capital.png" alt="Data journalism — Global AI Capital 2026" /></a><br/>
      <sub><b>Data Journalism</b> — Bloomberg-style dark dashboard, chart-driven<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_global_ai_capital_2026">Flip online</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_global_ai_capital_2026/exports/global_ai_capital_2026.pptx">Download .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_swiss_grid_systems"><img src="docs/assets/screenshots/preview_swiss_grid.png" alt="Swiss typographic grid — Grid Systems primer" /></a><br/>
      <sub><b>Swiss Grid</b> — strict modular grid, restrained type, red-accent<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_swiss_grid_systems">Flip online</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_swiss_grid_systems/exports/swiss_grid_systems.pptx">Download .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_glassmorphism_demo"><img src="docs/assets/screenshots/preview_glassmorphism_demo.png" alt="Glassmorphism SaaS — AI Agent engineering demo" /></a><br/>
      <sub><b>Glassmorphism SaaS</b> — translucent layers, gradient depth, product UI<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_glassmorphism_demo">Flip online</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_glassmorphism_demo/exports/glassmorphism_demo.pptx">Download .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_sugar_rush_memphis"><img src="docs/assets/screenshots/preview_sugar_rush_memphis.png" alt="Memphis pop — Sugar Rush festival" /></a><br/>
      <sub><b>Memphis Pop</b> — bold primaries, geometric patterns, playful energy<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_sugar_rush_memphis">Flip online</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_sugar_rush_memphis/exports/sugar_rush_memphis.pptx">Download .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_indie_bookstore_zine_guide"><img src="docs/assets/screenshots/preview_indie_bookstore_zine.png" alt="Risograph zine — Indie bookstore guide" /></a><br/>
      <sub><b>Risograph Zine</b> — duotone print, hand-made bookstore-culture feel<br/>
      <a href="https://hugohe3.github.io/ppt-master/viewer.html?project=ppt169_indie_bookstore_zine_guide">Flip online</a> · <a href="https://raw.githubusercontent.com/hugohe3/ppt-master/main/examples/ppt169_indie_bookstore_zine_guide/exports/indie_bookstore_zine_guide.pptx">Download .pptx</a></sub>
    </td>
  </tr>
</table>

<p align="center">
  <sub>All examples above were generated in a single pass, with no manual polish (Claude Opus 4.7 + <code>gpt-image-2</code>). Downloading any .pptx and opening it in PowerPoint is the fastest way to see what it can really do.<br/><a href="https://hugohe3.github.io/ppt-master/">Flip through all examples online →</a> · <a href="./examples/"><code>examples/</code> directory</a> · <a href="./docs/why-ppt-master.md">Why PPT Master?</a></sub>
</p>

---

Drop in your source material, and the deck you get back is **more than just editable**: it has native slide transitions and entrance animations, speaker notes that can become audio narration, charts and tables that can ship as real data-backed PowerPoint objects, and it can follow your own PPT template — a complete deck you can present as-is and keep refining. How to use each capability → [Getting Started](./docs/getting-started.md).

## Product Positioning

**If a file can't be opened and edited in PowerPoint, it shouldn't be called a PPT.** AI presentation tools roughly fall into four categories, and PPT Master only does the last one:

| Category | Output | Editable element-by-element in PowerPoint? |
|---|---|:---:|
| Template fill-in | PPTX built from a fixed template | Partially — limited by the template |
| Image-based | One large image per slide, packed into PPTX | ❌ each slide is a picture |
| HTML presentation | Web-based deck | ❌ not a PPTX |
| **Native editable (PPT Master)** | **Real DrawingML shapes, text boxes, charts** | ✅ click any element to edit |

In form, it's not a website or an app but a workflow (a "skill") that runs inside AI IDEs like Claude Code, Cursor, VS Code + Copilot, or Codebuddy: you tell the AI in the IDE's chat — "make a deck from this PDF" — and it follows the workflow to produce a genuinely editable `.pptx` on your machine. No coding on your side; you do exactly three things — install Python, install an AI IDE, drop in your material.

This form buys three promises that other tools struggle to make at the same time:

- **Transparent, predictable cost** — the tool is free and open source; the only cost is your AI model usage. You pay exactly what you consume — no separate PPT subscription added on top
- **Data stays local** — your files shouldn't have to be uploaded to someone else's server just to make a presentation. Apart from AI model communication, the entire pipeline runs on your machine
- **No platform lock-in** — your workflow shouldn't be held hostage by any single company. Works with Claude Code, Cursor, VS Code Copilot, and more; supports Claude, GPT, Gemini, Kimi, and other models

> [!IMPORTANT]
> ### This is a tool, not a wishing well
> `harness + model = agent` — PPT Master only owns the workflow; the model sets the ceiling. Recommended: **Claude with a large context window (~1M tokens) + AI image generation (`gpt-image-2`)**; other models can run the pipeline, with a quality gap.
>
> And don't expect a finished, perfect deck in one shot. The tool's value is taking most of the tedious work off your plate; the polishing that's left is yours — a natively editable deck exists precisely so you can keep working on it, not a flat image you can't touch. The cheaper the model, the more there is to do; if results disappoint, upgrade the model first, then check your usage against [Getting Started](./docs/getting-started.md) and the example projects.

---

## Built by Hugo He

I'm a finance professional (CPA · CPV · Consulting Engineer (Investment)) who regularly reviews and edits presentation decks. I wanted AI-generated slides to remain editable in PowerPoint, not flattened into images — so I built this.

Knowing how to use Python and AI agents will matter more and more, and this project is also meant to show how far you can go with just those two things. There's a learning curve if you're starting cold, but it's the curve worth climbing — making a deck is just the excuse; what I'm really pushing is Python and agents.

---

## Quick Start

### 1. Prerequisites

**All you need to install is [Python](https://www.python.org/downloads/) 3.10+.** Everything else comes with one line — `pip install -r requirements.txt` — after you download the project in Step 3.

<details>
<summary><strong>Windows</strong> — see the dedicated <a href="./docs/windows-installation.md">step-by-step guide</a> ⚠️</summary>

Windows requires a few extra steps (PATH setup, execution policy, etc.). We wrote a **step-by-step guide** specifically for Windows users:

**📖 [Windows Installation Guide](./docs/windows-installation.md)** — from zero to a working presentation in 10 minutes.

Quick version: download Python from [python.org](https://www.python.org/downloads/) → **check "Add to PATH"** during install → done; dependencies are installed in Step 3.
</details>

<details>
<summary><strong>macOS / Linux</strong> — install and go</summary>

```bash
# macOS
brew install python

# Ubuntu / Debian
sudo apt install python3 python3-pip
```
</details>

<details>
<summary><strong>Edge-case fallback</strong> — 99% of users don't need this</summary>

**Pandoc** — only needed for legacy document formats: `.doc`, `.odt`, `.rtf`, `.tex`, `.rst`, `.org`, or `.typ`. `.docx`, `.html`, `.epub`, `.ipynb` are handled natively by Python — no pandoc required.

```bash
# macOS
brew install pandoc

# Ubuntu / Debian
sudo apt install pandoc
```
</details>

### 2. Pick an Agent

PPT Master runs in **any tool with agent capability** — read/write files, execute commands, and sustain multi-turn conversation.

Never used one of these? Don't worry — in this project they play exactly one role: an AI chat window that can read and write files. Pick any tool from the table, install it, and you'll only ever use its chat panel. No coding involved.

> **Author's pick: [Claude Code](https://claude.ai/code)** — the environment this project is developed and tested on most thoroughly, as the CLI or the VS Code / JetBrains extension.

| Type | Examples | Notes |
|---|---|---|
| **IDE-native agent** | • VS Code architecture ([VS Code](https://code.visualstudio.com/) itself, plus forks & derivatives): [Cursor](https://cursor.sh/), Trae, Codebuddy IDE, [Windsurf](https://codeium.com/windsurf), etc.<br>• Other architectures: [Zed](https://zed.dev/), etc. | Editor with a built-in agent |
| **IDE plugin / extension** | [Claude Code](https://claude.ai/code) (VS Code / JetBrains extension), [GitHub Copilot](https://github.com/features/copilot), [Cline](https://cline.bot/), etc. | Installed inside hosts like VS Code or JetBrains |
| **CLI agent** | [Claude Code](https://claude.ai/code) CLI, [Codex CLI](https://github.com/openai/codex), Gemini CLI, etc. | Runs in the terminal; suits scripting, remote, or server use |

> **Model recommendation**: for the best results, use **Claude Opus** with `gpt-image-2`; **Gemini 3.5 Flash** currently offers great overall value for money — notably fast and well worth a try.

**🔑 Want to use Claude / GPT / Gemini but don't have access yet?** Project sponsors **[PackyCode](https://www.packyapi.com/register?aff=ppt-master)**, **[APIKEY.FUN](https://apikey.fun/register?aff=PPT-MASTER)** and **[RunAPI](https://runapi.co/register?aff=WMLJ)** offer pay-as-you-go access to Claude, GPT, Gemini and more — no subscription required, with exclusive discounts for our users (details at the top of this page).

**🔀 Juggling several providers?** Once you hold keys from more than one of them, [cc-switch](https://github.com/farion1231/cc-switch) — a cross-platform desktop app — lets you one-click switch API providers for Claude Code, Codex, Gemini CLI and more, no manual config editing.

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

To update later (Option A / B): `python3 skills/ppt-master/scripts/update_repo.py`

> **Option C — Skill marketplace**: the repo ships `.claude-plugin/marketplace.json`, so it can be installed through the [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) ecosystem:
>
> ```bash
> # Cross-agent CLI (Claude Code, Cursor, Codex, etc.)
> npx skills add hugohe3/ppt-master
>
> # Or inside Claude Code
> /plugin marketplace add hugohe3/ppt-master
> /plugin install ppt-master@ppt-master
> ```
>
> Both install paths above only fetch the skill files (not the full repo); you still need to `pip install -r requirements.txt` from the installed location for the post-processing scripts to run.

### 4. Create

**First, open the project folder in your agent:** the goal is to point the AI at the `ppt-master` directory you unzipped / cloned in the previous step. In an IDE-type tool, use **File → Open Folder** — the AI chat panel is usually in the sidebar; in a CLI agent, `cd ppt-master` first, then launch it. Everything from here on happens in the chat.

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

> **Output:** Native-shapes `.pptx` (directly editable) saved to `exports/<name>_<timestamp>.pptx`. A copy of `svg_output/` is always snapshotted to `backup/<timestamp>/svg_output/` for re-export / archival. Pass `--svg-snapshot` to additionally emit an SVG-image preview pptx alongside the native pptx in `exports/` (see [FAQ](./docs/faq.md)). Requires Office 2016+. By default charts and tables export as SVG-derived shapes (pixel-consistent across PowerPoint / Keynote / WPS); pass `--native-objects` to instead emit them as **real editable PowerPoint chart / table objects backed by data** (rendering may vary across apps), saved as `exports/<name>_<timestamp>_native_charts.pptx`.

> **Already have a `.pptx` you want to reuse?** Hand the AI that deck plus your material and ask it to "fill this deck with the new content" — it fills text, table, and chart data into your existing design and exports only the pages you pick, staying natively editable. See the [FAQ](./docs/faq.md) and [template-fill workflow](./skills/ppt-master/workflows/template-fill-pptx.md).

> **Something went wrong?** If the AI loses context, ask it to read `skills/ppt-master/SKILL.md`; for everything else, check the **[FAQ](./docs/faq.md)** — it covers model selection, layout issues, export problems, and more. Continuously updated from real user reports.

### 5. Image Acquisition (Optional)

Two paths for non-user images, mixable per image in the same deck:

**A) AI generation** — `image_gen.py`. Set `IMAGE_BACKEND` plus the provider's `*_API_KEY` (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.), and the pipeline calls it automatically. Run `python3 skills/ppt-master/scripts/image_gen.py --list-backends` for the full backend list. `gpt-image-2` is currently the best default.

**B) Web image search** — `image_search.py`. **Zero-config works**; configure `PEXELS_API_KEY` / `PIXABAY_API_KEY` (both free) for consistently higher-quality results:

- Without keys, search uses Openverse / Wikimedia Commons only — useful as a fallback, but image quality can be uneven because many results are ordinary user uploads
- With keys, the default provider chain also appends Pexels / Pixabay, which materially improves modern stock photography, people, workplace, lifestyle, and illustration coverage
- Licensing is handled automatically: CC0, Public Domain, Pexels / Pixabay no-attribution licenses, CC BY, and CC BY-SA are all considered together, and Executor adds a small inline credit whenever the selected image requires attribution. Use `--strict-no-attribution` only when a slide cannot tolerate any credit line
- For high-impact covers, product shots, portraits, and branded scenes, prefer this order: user-provided high-resolution assets / AI generation > web search with Pexels / Pixabay keys > zero-config web search

The API keys above all live in `.env`. Clone installs can use `cp .env.example .env`; skill marketplace installs should use a persistent user config:

```bash
mkdir -p ~/.ppt-master
cp /path/to/installed/ppt-master/.env.example ~/.ppt-master/.env
```

PPT Master reads the current process environment first, then the first `.env` found in this order: current working directory, skill directory (e.g. `~/.agents/skills/ppt-master/.env`), clone repo root, `~/.ppt-master/.env`.

> Full reference: [`image-generator.md`](./skills/ppt-master/references/image-generator.md) (AI) · [`image-searcher.md`](./skills/ppt-master/references/image-searcher.md) (web).

---

## Documentation

| | Document | Description |
|---|----------|-------------|
| 📘 | [Getting Started](./docs/getting-started.md) | First deck in 3 steps, plus how to use templates, live preview, animations, narration, voice cloning (**new users start here**) |
| 🆚 | [Why PPT Master](./docs/why-ppt-master.md) | How it compares to Gamma, Copilot, and other AI tools |
| 🪟 | [Windows Installation](./docs/windows-installation.md) | Step-by-step setup guide for Windows users |
| 📖 | [SKILL.md](./skills/ppt-master/SKILL.md) | Core workflow and rules |
| 📐 | [Canvas Formats](./skills/ppt-master/references/canvas-formats.md) | PPT 16:9, Xiaohongshu, WeChat, and 10+ formats |
| 🛠️ | [Scripts & Tools](./skills/ppt-master/scripts/README.md) | All scripts and commands |
| 💼 | [Examples](./examples/README.md) | All example projects |
| 🏗️ | [Technical Design](./docs/technical-design.md) | Architecture, design philosophy, why SVG |
| ❓ | [FAQ](./docs/faq.md) | Model selection, cost, layout troubleshooting, custom templates |

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to get involved.

## License

[MIT](LICENSE)

## Acknowledgments

[SVG Repo](https://www.svgrepo.com/) · [Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core) · [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) (CRAP principles)

## Related Tools

[cc-switch](https://github.com/farion1231/cc-switch) — one-click switching of API providers across Claude Code / Codex / Gemini CLI and more.

## Contact & Collaboration

Looking to collaborate, integrate PPT Master into your workflow, or just have questions?

- 💬 **Questions & sharing** — [GitHub Discussions](https://github.com/hugohe3/ppt-master/discussions)
- 🐛 **Bug reports & feature requests** — [GitHub Issues](https://github.com/hugohe3/ppt-master/issues)

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

<a href="https://www.packyapi.com/register?aff=ppt-master"><img src="docs/assets/sponsors/packycode.png" alt="PackyCode" height="40" /></a>
&nbsp;
<a href="https://apikey.fun/register?aff=PPT-MASTER"><img src="docs/assets/sponsors/apikey-fun.png" alt="APIKEY.FUN" height="40" /></a>
&nbsp;
<a href="https://runapi.co/register?aff=WMLJ"><img src="docs/assets/sponsors/runapi.png" alt="RunAPI" height="40" /></a>
&nbsp;
<a href="https://www.compshare.cn/coding-plan?ytag=GPU_YY-git_pptmaster0624"><img src="docs/assets/sponsors/youyun.png" alt="YouYun ZhiSuan" height="40" /></a>
&nbsp;
<a href="https://m.do.co/c/547f129aabe1"><img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/PoweredByDO/DO_Powered_by_Badge_blue.svg" alt="Powered by DigitalOcean" height="40" /></a>

**Individual support**

If PPT Master has been helpful to you, individual support of any amount helps keep the project moving and free.

<a href="https://paypal.me/hugohe3"><img src="https://img.shields.io/badge/PayPal-Sponsor-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Sponsor via PayPal" /></a>

<img src="docs/assets/alipay-qr.jpg" alt="Alipay QR Code" width="220" />

---

Made with ❤️ by [Hugo He](https://www.hehugo.com/) — if this project helps you, please give it a ⭐ and consider [sponsoring](#sponsors--support).

<sub>Official distribution: <a href="https://github.com/hugohe3/ppt-master">GitHub</a> (primary) · <a href="https://atomgit.com/hugohe3/ppt-master">AtomGit</a> (mirror). Redistributions on other platforms are unofficial. MIT licensed — attribution required.</sub>

[⬆ Back to Top](#ppt-master--ai-generates-natively-editable-pptx-from-any-document)
