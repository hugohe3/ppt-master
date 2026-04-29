# FAQ

[English](./faq.md) | [中文](./zh/faq.md)

---

## Q: What source formats does PPT Master accept?

Almost anything: **PDF**, **DOCX**, **PPTX**, **EPUB**, **HTML**, **LaTeX**, **RST**, **URLs** (including WeChat articles), **Markdown**, or just plain text pasted into the conversation. The AI agent converts your source material to Markdown automatically before generating slides.

## Q: Can PPT Master produce formats other than PowerPoint?

Yes. Besides the standard **16:9** and **4:3** presentation formats, PPT Master supports social media and marketing formats out of the box:

| Format | Use Case |
|--------|----------|
| Xiaohongshu (RED) 3:4 | Image-text sharing, knowledge posts |
| WeChat Moments / IG 1:1 | Square posters, brand showcases |
| Story / TikTok 9:16 | Vertical stories, short video covers |
| WeChat Article Header | WeChat article cover images |
| A4 Print | Print posters, flyers |

Just specify the format when starting a project (e.g., `--format xhs`). The output is still a `.pptx` file containing native shapes.

## Q: What AI tools work with PPT Master?

PPT Master works with any AI coding agent that can read files and run shell commands — **Claude Code** (CLI / VS Code / JetBrains / Web), **VS Code Copilot**, **Codex**, and others. See the cost comparison below for pricing differences.

## Q: Can I use AI-generated images in my presentation?

Yes. PPT Master includes a built-in image generation script that supports multiple providers (Gemini, OpenAI, FLUX, Qwen, Zhipu, etc.). During the Strategist phase, if you choose "AI generation" for the image approach, the pipeline will automatically generate images based on your content. You can also provide your own images — just place them in the project's `images/` folder.

## Q: Can I edit the generated presentations?

Yes. The main `.pptx` (native PowerPoint shapes — all text, graphics, and colors directly editable without any conversion) is saved to `exports/` with a timestamp. The SVG snapshot `_svg.pptx` plus a copy of `svg_output/` (the Executor's raw SVG source) are archived to `backup/<timestamp>/`, so you can revisit the visual reference or rebuild the pptx via `finalize_svg → svg_to_pptx` without re-running the LLM. `backup/<timestamp>/` directories can be deleted manually when no longer needed. Requires **Office 2016** or later.

## Q: What's the difference between the three Executors?

- **Executor_General**: General scenarios, flexible layout
- **Executor_Consultant**: General consulting, data visualization
- **Executor_Consultant_Top**: Top consulting (MBB level), 5 core techniques

## Q: Is PPT Master expensive to use?

PPT Master itself is free and open source. The only cost is your own AI model usage.

AI tools across the industry are shifting to usage-based billing — you pay for what you actually consume. PPT Master works with this model naturally: there's no separate PPT subscription, no proprietary credits, no per-seat fee for a presentation platform on top of what you're already paying for AI.

For comparison, Gamma subscriptions run $8–20/month, Beautiful.ai $12–45/month — regardless of how much you actually use them. PPT Master adds zero cost on top of your existing AI spend.

## Q: Are the charts in the generated PPTX editable?

Charts are rendered as **custom-designed SVG graphics** converted to native PowerPoint shapes — fully editable as shapes (move, recolor, retype, restyle). This is a deliberate choice over Excel-driven chart objects: PowerPoint's default charts look generic and dated, and lock decks into rigid templates. SVG charts give you publication-quality visuals you can fine-tune directly in PowerPoint.

If your workflow specifically requires Excel-driven data editing, manually create a similar chart yourself in PowerPoint after export.

## Q: Can I change page transitions and element animations?

Yes. The exported PPTX supports both **page transitions** and **per-element entrance animations**, controlled via `svg_to_pptx.py` CLI flags.

**Page transitions** (on by default, 0.4s `fade`)

```bash
# Pick a different effect: fade / push / wipe / split / strips / cover / random
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push --transition-duration 0.6

# Disable transitions
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none

# Auto-advance every 5 seconds
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5
```

**Per-element animations** (off by default — existing users see no behavior change)

Enter a slide → click once → semantic groups cascade in by z-order. To enable:

```bash
# Cascade every element with fade (recommended starting point)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade

# Auto-vary effects within a slide (title fades, content rotates fly/zoom/wipe...)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed

# Slower pace: 0.5s per element, 0.2s gap between elements
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade \
        --animation-duration 0.5 --animation-stagger 0.2
```

12 single effects: `appear / fade / fly / zoom / wipe / split / blinds / dissolve / peek / wheel / box / circle`, plus `mixed` and `random` auto-vary modes.

**Anchor logic**: animations are anchored on top-level SVG `<g id="...">` groups (e.g. `<g id="cover-title">`, `<g id="card-1">`) — this is the cleanest cascade granularity. Slides whose root is flat `<rect>` / `<text>` / `<path>` (no top-level `<g>` wrappers) **fall back automatically**: if there are ≤20 top-level visible elements, each becomes one animation anchor; beyond 20 (typical of dense consulting pages / charts), animation is skipped on that slide — cascading dozens of atoms in series would just be noise. So Executors are recommended to wrap logical sections in `<g id>` regardless of animation, since it also improves PowerPoint's group-select / group-move ergonomics.

**Note**: per-element animations only apply in native shapes mode (the default); `--only legacy` produces one image per slide and has no element anchors to animate.

## Q: Which AI model works best?

**Claude** (Opus / Sonnet) is the recommended and most tested model. SVG layout requires precise absolute-coordinate calculations (font size x character count x container width), and Claude handles this significantly better than alternatives.

**GPT series** older versions tended to produce more layout issues — text overflowing containers, misaligned elements, coordinate miscalculations. Newer versions (e.g. GPT-5.5) have improved noticeably and are usable in practice; if issues appear, tell the AI which page to fix.

Other models (Gemini, GLM, MiniMax, etc.) vary in quality. In general, models with stronger frontend/visual capabilities produce better results.

## Q: Text overflows or elements are misaligned — what can I do?

This is almost always a model capability issue, not a bug in PPT Master. SVG layout is essentially manual absolute positioning — the model must calculate coordinates, font metrics, and container sizes correctly.

**Fixes to try**:
1. Switch to **Claude** (Opus or Sonnet) if you're using another model
2. Tell the AI which specific page has the problem and describe the issue — it can regenerate individual pages
3. Open the SVG source file directly and ask the AI to fix coordinates
4. Remember: the generated PPTX is a **high-quality starting point**, not a final deliverable — minor adjustments in PowerPoint are expected

## Q: How long does a presentation take to generate?

A typical 10–15 page presentation takes about **10–20 minutes** with a fast model. Generation is **intentionally serial** (one page at a time) to maintain visual consistency across slides — parallel generation was tested and produced inconsistent styles.

If generation feels slow, check your model's token throughput. The bottleneck is usually the model's output speed, not the scripts.

## Q: Can I preview or fix individual pages before the full export?

Yes. You can **interrupt the workflow at any time** — after the first few pages are generated, review them and give feedback. The AI can regenerate specific pages based on your comments. You don't need to wait until the end to make corrections.

For post-generation fixes, simply tell the AI: "Page 3 has a layout issue — the title overlaps the chart" and it will fix that specific SVG.

## Q: How do I create a custom template?

Want to turn a PPT you love into a reusable template for PPT Master? Here's how:

**Step 1 — Prepare Reference Material**

The simplest path is still to prepare screenshots of the key page types from your reference PPT — cover page, table of contents, chapter divider, content page, and closing page. Save them as images in a single folder with clear, descriptive filenames (e.g., `cover.png`, `toc.png`, `chapter.png`, `content.png`, `closing.png`).

If you already have the original `.pptx` template file, you can also provide it as a reference source. PPT Master can extract reusable background images, logos, theme colors, and font metadata from the PPTX first, then use those assets during template reconstruction.

**Step 2 — Let AI Create the Template**

Use an AI coding agent (Claude Code, Codex, etc.) and ask it to use the **PPT Master `/create-template` workflow** to convert your reference material into a template. The more context you give, the better the result — for example:

- Template name and intended use case (e.g., government reports, premium consulting)
- Desired tone and color palette (e.g., "modern and restrained, dark blue primary")
- Category preference (`brand` / `general` / `scenario` / `government` / `special`)
- Canvas format, if not the default 16:9

You don't need to supply every detail upfront — the AI agent will ask follow-up questions to fill in anything missing (template ID, theme mode, etc.).

**Step 3 — Wait for the Result**

The AI agent will handle the rest — analyzing your screenshots, building the layout definitions, and registering the template so it appears as a selectable option in the PPT Master workflow.

> **Tip**: The more specific you are about the style and use case, the better the generated template will match your expectations.

---

> For more questions, see [SKILL.md](../skills/ppt-master/SKILL.md) and [AGENTS.md](../AGENTS.md)
