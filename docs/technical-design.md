# Technical Design

[English](./technical-design.md) | [中文](./zh/technical-design.md)

---

## Design Philosophy — AI as Your Designer, Not Your Finisher

The generated PPTX is a **design draft**, not a finished product. Think of it like an architect's rendering: the AI handles visual design, layout, and content structure — delivering a high-quality starting point. For truly polished results, **expect to do your own finishing work** in PowerPoint: swapping shapes, refining charts, adjusting colors, replacing placeholder graphics with native objects. The goal is to eliminate 90% of the blank-page work, not to replace human judgment in the final mile. Don't expect one AI pass to do everything — that's not how good presentations are made.

**A tool's ceiling is your ceiling.** PPT Master amplifies the skills you already have — if you have a strong sense of design and content, it helps you execute faster. If you don't know what a great presentation looks like, the tool won't know either. The output quality is ultimately a reflection of your own taste and judgment.

---

## System Architecture

```
User Input (PDF/DOCX/URL/Markdown)
    ↓
[Source Content Conversion] → source_to_md/pdf_to_md.py / doc_to_md.py / web_to_md.py
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
Output: Two files are generated automatically:
    ├── presentation.pptx        ← Native shapes (DrawingML) — recommended for editing & delivery
    └── presentation_svg.pptx   ← SVG reference version — pixel-perfect visual reference; use
                                    "Convert to Shape" in PowerPoint to unlock individual elements
```

---

## Technical Pipeline

**The pipeline: AI generates SVG → post-processing converts to DrawingML (PPTX).**

The full flow breaks into three stages:

**Stage 1 — Content Understanding & Design Planning**
Source documents (PDF/DOCX/URL/Markdown) are converted to structured text. The Strategist role analyzes the content, plans the slide structure, and confirms the visual style, producing a complete design specification.

**Stage 2 — AI Visual Generation**
The Executor role generates each slide as an SVG file. The output of this stage is a **design draft**, not a finished product.

**Stage 3 — Engineering Conversion**
Post-processing scripts convert SVG to DrawingML. Every shape becomes a real native PowerPoint object — clickable, editable, recolorable — not an embedded image.

---

## Why SVG?

SVG sits at the center of this pipeline. The choice was made by elimination.

**Direct DrawingML generation** seems most direct — skip the intermediate format, have AI output PowerPoint's underlying XML. But DrawingML is extremely verbose; a simple rounded rectangle requires dozens of lines of nested XML. AI has far less training data for it than SVG, output is unreliable, and debugging is nearly impossible by eye.

**HTML/CSS** is one of the formats AI knows best. But HTML and PowerPoint have fundamentally different world views. HTML describes a *document* — headings, paragraphs, lists — where element positions are determined by content flow. PowerPoint describes a *canvas* — every element is an independent, absolutely positioned object with no flow and no context. This isn't just a layout calculation problem; it's a structural mismatch. Even if you solved the browser layout engine problem (what Chromium does in millions of lines of code), an HTML `<table>` still has no natural mapping to a set of independent shapes on a slide.

**WMF/EMF** (Windows Metafile) is Microsoft's own native vector graphics format and shares direct ancestry with DrawingML — the conversion loss would be minimal. But AI has essentially no training data for it, so this path is dead on arrival. Notably, even Microsoft's own format loses to SVG here.

**SVG as embedded images** is the simplest path — render each slide as an image and embed it. But this destroys editability entirely: shapes become pixels, text cannot be selected, colors cannot be changed. No different from a screenshot.

SVG wins because it shares the same world view as DrawingML: both are absolute-coordinate 2D vector graphics formats built around the same concepts:

| SVG | DrawingML |
|---|---|
| `<path d="...">` | `<a:custGeom>` |
| `<rect rx="...">` | `<a:prstGeom prst="roundRect">` |
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse">` |
| `transform="translate/scale/rotate"` | `<a:xfrm>` |
| `linearGradient` / `radialGradient` | `<a:gradFill>` |
| `fill-opacity` / `stroke-opacity` | `<a:alpha>` |

The conversion is a translation between two dialects of the same idea — not a format mismatch.

SVG is also the only format that simultaneously satisfies every role in the pipeline: **AI can reliably generate it, humans can preview and debug it in any browser, and scripts can precisely convert it** — all before a single line of DrawingML is written.
