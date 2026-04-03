# FAQ

[English](./faq.md) | [中文](./zh/faq.md)

---

## Q: Can I edit the generated presentations?

Yes! The default export (`.pptx`) produces **native PowerPoint shapes** — all text, graphics, and colors are directly editable in PowerPoint without any conversion. An SVG reference version (`_svg.pptx`) is also generated; for that file, select the content and use **"Convert to Shape"** to unlock editing. Requires **Office 2016** or later.

## Q: What's the difference between the three Executors?

- **Executor_General**: General scenarios, flexible layout
- **Executor_Consultant**: General consulting, data visualization
- **Executor_Consultant_Top**: Top consulting (MBB level), 5 core techniques

## Q: Isn't using Claude too expensive?

It depends on how you use it. If you're using a direct API or subscription quota, a single presentation may cost around **$5** — but compared to spending 1–2 days building a presentation manually, this is a reasonable trade-off.

There are much cheaper options. **VS Code Copilot** at $10/month gives you 300 standard requests, which converts to roughly **100 premium (Opus-level) requests**. By default PPT Master has 2 confirmation rounds (template selection + eight confirmations), but if you specify "no template" upfront, it reduces to just **1 confirmation round — only 2 messages** (AI asks, you confirm). That means each presentation costs about **6 Opus requests** or **2 Sonnet requests**. At the $0.04 USD/request overage rate:

| Model | Requests per PPT | Overage Cost |
|-------|:-----------------:|:------------:|
| Opus | ~6 | ~$0.24 USD |
| Sonnet | ~2 | ~$0.08 USD |

For a complete presentation, **$0.08–$0.24 USD** is not expensive at all.

## Q: Are the charts in the generated PPTX editable?

Charts are rendered as **custom-designed SVG graphics** converted to native PowerPoint shapes — not Excel-driven chart objects. This gives them a polished, high-fidelity appearance that often looks better than default PowerPoint charts. However, the underlying data is not editable via PowerPoint's chart editor. If you need a live, data-driven chart (e.g., one you can update by editing a spreadsheet), you will need to manually replace it with a native PowerPoint chart after export.

## Q: How do I create a custom template?

Want to turn a PPT you love into a reusable template for PPT Master? Here's how:

**Step 1 — Prepare Reference Material**

The simplest path is still to prepare screenshots of the key page types from your reference PPT — cover page, table of contents, chapter divider, content page, and closing page. Save them as images in a single folder with clear, descriptive filenames (e.g., `cover.png`, `toc.png`, `chapter.png`, `content.png`, `closing.png`).

If you already have the original `.pptx` template file, you can also provide it as a reference source. PPT Master can extract reusable background images, logos, theme colors, and font metadata from the PPTX first, then use those assets during template reconstruction.

**Step 2 — Let AI Create the Template**

Use an AI coding agent (Claude Code, Codex, etc.) and ask it to use the **PPT Master `/create-template` workflow** to convert your reference material into a template. In your prompt, provide:

- The template's English name and Chinese name
- The intended use case (e.g., government reports, premium consulting, product launches)
- The desired visual effects and color palette to apply when this template is used
- Whether to enable AI image generation

**Step 3 — Wait for the Result**

The AI agent will handle the rest — analyzing your screenshots, building the layout definitions, and registering the template so it appears as a selectable option in the PPT Master workflow.

> **Tip**: The more specific you are about the style and use case, the better the generated template will match your expectations.

---

> For more questions, see [SKILL.md](../skills/ppt-master/SKILL.md) and [AGENTS.md](../AGENTS.md)
