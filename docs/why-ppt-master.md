# Why PPT Master

[English](./why-ppt-master.md) | [中文](./zh/why-ppt-master.md)

---

There are dozens of AI presentation tools. This page explains what PPT Master does differently — and where it's not the right choice.

I'm [Hugo He](https://www.hehugo.com/), an investment & finance professional who builds presentations every day. PPT Master is an open-source tool I've spent extensive time refining — because I'm its most demanding user.

## 1. Real PowerPoint Output — Not Images, Not Web Screenshots

**This is the core differentiator.**

Most AI presentation tools take one of three approaches, each with a hard limitation:

- **Embed images** → Many tools render each slide as a flat image inside the PPTX. It looks polished, but text can't be selected, colors can't be changed, and scaling loses quality — it's a screenshot, not a presentation.
- **HTML/CSS rendering** → Gamma, Tome, and similar tools look great in the browser, but HTML describes document flow while PowerPoint is a canvas. Exporting to PPTX inevitably breaks layouts and flattens elements.
- **python-pptx / direct generation** → ChatGPT and similar tools build PPTX programmatically. Elements are editable, but AI lacks the training data to produce complex designs — the result is basic text boxes and bullet lists.

PPT Master takes a fourth path — **AI generates SVG, then scripts convert SVG to DrawingML**. This works because SVG and DrawingML are fundamentally the same kind of thing — both are absolute-coordinate 2D vector formats where rectangles, paths, gradients, and shadows map one-to-one. The conversion is a dialect translation, not a format mismatch.

In the exported PPTX, every shape, text box, gradient, and shadow is a native PowerPoint object. Click anything, edit it — just like you built it by hand.

> See [Technical Design](./technical-design.md) for the full rationale.

---

## 2. Predictable Cost — No Subscription Required

PPT Master itself is free and open source. No subscriptions, no credits to purchase. The only cost comes from your own AI editor — and it's remarkably low:

| Model | Requests per PPT | Cost |
|---|:---:|:---:|
| Sonnet | ~2 | ~$0.08 |
| Opus | ~6 | ~$0.24 |

With VS Code Copilot ($10/month), producing dozens of presentations per month costs just a few dollars total. No credit limits, no seat fees, no getting locked out when "this month's quota" runs out.

For comparison, Gamma subscriptions run $8–20/month, Beautiful.ai $12–45/month, and MS Copilot around $30/month — regardless of how much you actually use.

---

## 3. Data Privacy — 100% Local

Your files never leave your machine. Source documents are converted locally, SVGs are generated locally, PPTX is exported locally. The only external communication is between you and your AI editor — no different from how you normally use it.

No third-party server stores your source documents or output. This matters for finance, government, and any organization with data residency requirements.

---

## 4. Fully Open — No Lock-in on Editors or Models

Your workflow shouldn't be held hostage by any single company. Today you depend on their platform; tomorrow they raise prices, change the rules, or shut down — and everything you've built on top of it is gone. That's not what open source should look like.

PPT Master is a framework, not a plugin for a specific IDE. **On editors:** Claude Code, VS Code Copilot, Cursor, Codebuddy IDE, and whatever comes next — they all work. **On models:** Claude produces the best results, but GPT, Gemini, Kimi, MiniMax, and others can all drive PPT Master — the difference is in layout precision, and as models improve, these gaps will narrow.

The choice is yours. PPT Master doesn't make that decision for you.

---

## Features

### Consulting-Grade Design System

Three built-in styles: General (training, tech talks), Consultant (business reports, data visualization), and Consultant Top (MBB level — investment memos, strategic plans, government briefings).

The [examples/](../examples/) directory contains 15 projects and 229 pages spanning government fiscal analysis, AI architecture design, Zen philosophy, pixel-art gaming, and more.

### Full Source-Document Input

Feed it almost anything: PDF, DOCX, PPTX, EPUB, HTML, LaTeX, RST, web URLs, WeChat articles, Markdown, or plain text. Most SaaS tools only accept prompts or limited file uploads.

### Multi-Format Output

Output is not limited to standard 16:9 and 4:3 slide ratios. Xiaohongshu 3:4, WeChat/Instagram 1:1, vertical Story 9:16, A4 print — same pipeline, just specify the format.

---

## Where PPT Master Is Not the Right Choice

Being honest about limitations:

| Limitation | Detail |
|---|---|
| **Setup required** | Install Python, clone repo, configure AI editor. Not a "open browser and go" experience. |
| **Slower generation** | 10–20 min for a 10-page deck (serial page-by-page for cross-slide consistency). SaaS tools take seconds. |
| **No collaboration** | Local files, no real-time co-editing, no share links. |
| **No visual UI** | All interaction through AI chat — no drag-and-drop canvas. |
| **Charts aren't data-bound** | Charts are visual shapes, not Excel-linked objects. Great-looking but not dynamically updatable. |

**If you want zero-setup, instant slides in a browser** — Gamma and Canva are excellent choices.

**If you want native editability, predictable cost, local data, and no lock-in** — that's what PPT Master is built for.
