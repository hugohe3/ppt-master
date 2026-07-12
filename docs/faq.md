# FAQ

[English](./faq.md) | [Chinese](./zh/faq.md)

---

## Q: What source formats does PPT Master accept?

Almost anything: **PDF**, **DOCX**, **PPTX**, **EPUB**, **HTML**, **LaTeX**, **RST**, **URLs** (including WeChat articles), **Markdown**, or just plain text pasted into the conversation. The AI agent converts your source material to Markdown automatically before generating slides.

## Q: Can I generate a deck with just a topic, no source materials?

Yes. Tell the AI your topic or scenario (e.g. "make a PPT about Hayao Miyazaki", "introduce our new product"). The AI will trigger the **topic-research workflow** — gathering authoritative sources via web search (Wikipedia / official sites / institutional releases), assembling them into a Markdown research document + image folder, then feeding both into the main pipeline.

Quality depends on what's on the open web. If you already have specialized material (papers, internal docs), giving those files to the AI directly produces better results than web research alone.

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

## Q: I downloaded an old version. How do I update to the latest?

It depends on how you installed PPT Master:

| Install method | Update method |
|---|---|
| Git clone | Run `python3 skills/ppt-master/scripts/update_repo.py` inside the `ppt-master` folder |
| Download ZIP | Download the latest ZIP, unzip it into a new folder, copy your old `.env` and `projects/` folder into the new folder, then run `pip install -r requirements.txt` |
| Skill marketplace | Reinstall or update through the matching marketplace / skills tool |

For long-term use, Git clone is recommended. ZIP is fine for a quick trial, but it has no Git history and cannot run `git pull`.

If you are not sure which install method you used, ask the AI to run this from the project folder:

```bash
python3 skills/ppt-master/scripts/update_repo.py
```

If the folder is not a Git clone, the script will tell you how to migrate a ZIP install.

## Q: The repo is over 1 GB and my skills tool fails to download it — can I get just the skill?

Yes. The full repository is large (Git history plus bundled example decks and their assets), and that size is baked into the history — it can't be trimmed without breaking the many existing forks. If you only want the skill and not the full repo, use a lightweight path instead:

- **Marketplace CLI**: `npx skills add hugohe3/ppt-master` or Claude Code's `/plugin install` fetch the skill files only (see the Set Up section of the README).
- **Manual download**: grab `ppt-master-skill-*.zip` from the [Releases](https://github.com/hugohe3/ppt-master/releases) page — the skill files only (~50 MB), no full-repo clone.

Either way, run `pip install -r requirements.txt` from the installed location so the post-processing scripts work.

## Q: Can I use AI-generated images in my presentation?

Yes. PPT Master includes a built-in image generation script that supports multiple providers (Gemini, OpenAI, FLUX, Qwen, Zhipu, etc.). During the Strategist phase, if you choose "AI generation" for the image approach, the pipeline will automatically generate images based on your content. You can also provide your own images — just place them in the project's `images/` folder.

## Q: I don't have an image-generation API key — can I still get images?

Yes — pick "Web-sourced" in the Strategist's Image Usage step. PPT Master ships a zero-config `image_search.py` that searches openly-licensed images across Openverse and Wikimedia Commons (no API key needed). Zero-config search is a fallback: it works immediately, but quality can be uneven because many results are ordinary user uploads.

For better contemporary stock photography, set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` in `.env` (both are free). The search will include Pexels / Pixabay automatically, which usually improves people, workplace, lifestyle, product, and illustration images. You can mix paths in one deck (e.g. AI for hero illustrations, web for team photos). If a selected image requires attribution, Executor adds a small inline credit on the affected slide.

Be clear on what this buys you: **web search only finds *a* relevant, downloadable, license-clean image — it does not guarantee the image is good or right for that page**, because ranking sees text metadata, not the picture. During generation a multimodal model reads a thumbnail to sanity-check and re-queries a poor fit, but **the most reliable route to high quality is to search yourself**: find a better image anywhere, hand the AI its URL, and it downloads and swaps it in via `image_search.py --from-url <url>` (recorded as a manual source; rights are yours to verify). Replacement can happen any time — mid-generation or from live preview — without stopping the run. In short: treat web search as a placeholder fallback and manual picking as the polish step.

## Q: Can I edit the generated presentations?

Yes. The only PPTX export route in the SVG pipeline is PPT Master's own `svg_output/` → DrawingML conversion. It saves a timestamped native PowerPoint deck to `exports/`, with text, graphics, and colors directly editable as PowerPoint objects. A copy of `svg_output/` (the Executor's raw SVG source) is always written to `backup/<timestamp>/svg_output/` so you can rebuild via `finalize_svg → svg_to_pptx` without re-running the LLM.

`finalize_svg.py` remains a mandatory Step 7 operation even though native PPTX export reads `svg_output/`. It produces self-contained files in `svg_final/` for visual inspection and for manual insertion into another deck as SVG pictures. PowerPoint's manual **Convert to Shape** command is not a supported round-trip path; use the generated native PPTX when you need editable shapes.

## Q: Why is one paragraph split into multiple text boxes? Can I get one text box per paragraph instead?

By default, mergeable body text exports as one editable PowerPoint text frame. Authored SVG visual lines remain hard line breaks inside that frame; larger gaps and list items remain separate paragraphs. Only text explicitly marked with `data-pptx-break="soft"` joins authored rows during export — the Executor declares that marker on flowing body prose at draw time, so ordinary paragraphs edit as one reflowing paragraph while deliberately designed line breaks (titles, verse, aligned labels) stay hard breaks. The frame still uses normal PowerPoint wrapping, so deleting a hard break or editing the text reflows it within the frame.

If you need strict line-layout fidelity, re-export with `--no-merge`:

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --no-merge
```

With `--no-merge`, every visual line becomes its own PowerPoint text frame. This preserves the SVG's exact line layout pixel-for-pixel, which matters for covers, charts, tables, and any page with tight typographic alignment.

**Trade-off**: default merging keeps one editable frame and preserves authored line boundaries. Use `--no-merge` only when every visual line must also remain an independently movable text box. The detection is conservative — mixed-layout `<text>` falls through to the per-line path automatically.

When you're chatting with the AI, you can also just ask for strict line fidelity on layout-sensitive pages — the AI will add `--no-merge` when re-exporting.

## Q: Why are font sizes in px, not pt? Do they change on export?

PPT Master works in **unitless px end-to-end** — the confirm page, `spec_lock.md`, and the SVG all carry px; there is no pt layer. The SVG canvas is literally 1280×720 px, so px is the real layout / execution unit, and keeping a single unit avoids the size drift you get when a value is "confirmed as 20pt" but written into the SVG as a different number.

PowerPoint displays pt, so the **export** converts px → pt automatically (`pt = px × 0.75`, kept to one decimal). For example a `24px` body becomes `18pt`, a `42px` title becomes `31.5pt`. So a non-integer like `13.5pt` or `31.5pt` in PowerPoint is **expected and intentional**, not a bug — the size is whatever the px works out to, no longer forced onto whole or half-point values.

The body baseline is a fixed value per **delivery purpose** (not a range):

| Delivery purpose | Body px | ≈ exported pt |
|---|---|---|
| `text` (read-close: report / leave-behind) | 20px | 15pt |
| `balanced` (default: roadshow / review) | 24px | 18pt |
| `presentation` (projected / launch) | 32px | 24pt |

Title, subtitle, footnote and the other roles derive from the body by ratio and snap to clean even px. You can override any role's px value on the confirm page.

## Q: How does PPT Master decide a deck's style?

Two independent choices, locked at confirmation `d`:

- **Mode** (how the deck argues): `pyramid` / `narrative` / `instructional` / `showcase` / `briefing` — see `references/modes/`
- **Visual style** (how it looks): `swiss-minimal` / `editorial` / `soft-rounded` / `dark-tech` … + `custom` — see `references/visual-styles/`

Any mode pairs with any visual style.

## Q: Is PPT Master expensive to use?

PPT Master itself is free and open source. The only cost is your own AI model usage.

AI tools across the industry are shifting to usage-based billing — you pay for what you actually consume. PPT Master works with this model naturally: there's no separate PPT subscription, no proprietary credits, no per-seat fee for a presentation platform on top of what you're already paying for AI.

For comparison, Gamma subscriptions run $8–20/month, Beautiful.ai $12–45/month — regardless of how much you actually use them. PPT Master adds zero cost on top of your existing AI spend.

## Q: Are the charts in the generated PPTX editable?

By default, charts are rendered as **custom-designed SVG graphics** converted to native PowerPoint shapes — fully editable as shapes (move, recolor, retype, restyle). This is a deliberate default over Excel-driven chart objects: PowerPoint's default charts look generic and dated, and lock decks into rigid templates. SVG charts give you publication-quality visuals you can fine-tune directly in PowerPoint, and they render pixel-consistently across PowerPoint / Keynote / LibreOffice / WPS.

If your workflow specifically requires Excel-driven data editing, export with `--native-objects`: supported data charts and pure text-grid tables then ship as **real editable PowerPoint chart / table objects backed by data** (saved as `exports/<name>_<timestamp>_native_charts.pptx`, keeping the deck's own colors instead of PowerPoint's default theme). The trade-off is cross-app rendering — native objects may look slightly different across PowerPoint / Keynote / LibreOffice / WPS, which is why SVG shapes stay the default.

## Q: Can I change page transitions and element animations?

Yes. Page transitions are on by default (`fade` 0.4s); per-element entrance animation is **off by default** — a page appears as a whole instead of having elements auto-cascade in one by one (that unsolicited cascade is the strongest "AI deck" tell). Both are controlled by `svg_to_pptx.py` flags — `-t/--transition` for page-level and `-a/--animation` for element-level. Turn element animation on explicitly when you want it:

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push       # different transition
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none       # disable transitions
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto       # enable per-element entrance (effect mapped from group id)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade        # enable with a single effect
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click   # presenter-paced reveals
```

`on-click` is for live presentations. Narrated/video export via `--recorded-narration` rejects it because PPT Master writes page timings, not object-level click timings; use `after-previous` or `with-previous` for narrated decks.

Full effect list, anchor logic (top-level `<g id="...">`), fallback behavior, and limitations: see [Animations & Transitions](../skills/ppt-master/references/animations.md).

## Q: Which AI model works best?

**Claude** (Opus / Sonnet) is the recommended and most tested model. SVG layout requires precise absolute-coordinate calculations (font size x character count x container width), and Claude handles this significantly better than alternatives.

**GPT series** older versions tended to produce more layout issues — text overflowing containers, misaligned elements, coordinate miscalculations. Newer versions (e.g. GPT-5.5) have improved noticeably and are usable in practice; if issues appear, tell the AI which page to fix.

Other models (Gemini, GLM, MiniMax, etc.) vary in quality. In general, models with stronger frontend/visual capabilities produce better results.

## Q: Someone said PPT Master is "just a toy" — is that fair?

No. PPT Master is a **harness**, not a complete agent — `harness + model = agent`, and the output ceiling is set entirely by the model, not the harness. Evaluating PPT Master with a weak or small-context model is like test-driving a sports car in first gear and concluding it's slow.

**The full-power combination:**

- **Claude with a large context window** (ideally ~1M tokens): a large context window lets the Executor see every previously generated page in the same session, maintaining visual consistency across the entire deck without splitting runs. Smaller windows force split-mode execution, which introduces visible style drift between phases.
- **AI image generation with `gpt-image-2`** (or similar): placeholder-grade stock images are the single biggest reason decks look generic. Replacing them with on-brand AI-generated illustrations changes the perceived quality immediately.

If the results you've seen look mediocre, check your setup before concluding anything about the tool: What model? What context size? Was image generation enabled? PPT Master + Claude Opus at 1M context + `gpt-image-2` images is a genuinely different experience from PPT Master + a small open-source model with no image API configured.

> **No Claude access?** Project sponsor [PackyCode](https://www.packyapi.com/register?aff=ppt-master) provides pay-as-you-go access to Claude and other models — no subscription, no overseas card required. Use promo code **`ppt-master`** for 10% off.

One last thing: this is a free, solo-maintained open-source project. If it fits your needs, use it — I'm glad it helps; if it doesn't, pick another tool. Sincere feedback and suggestions are always welcome, because that's how the project gets a little better over time.

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

## Q: Will long decks blow out the context window in one shot?

Default recommendation: **continuous one-shot generation**. 10–15 page decks fit comfortably in a 200K window, and cross-page visual consistency is best when the Executor can see prior pages in the same session (it actively aligns style, font sizes, and rhythm).

Only when signals are heavy (≥ 18 pages, thick source material, or `topic-research` ran with substantial web-fetch accumulation) does the AI surface an optional **split mode** hint at the Strategist phase: the planning session (Strategist confirmation stage + image acquisition) ends in the current chat; you open a fresh chat window and type `resume execution projects/<project_name>` to enter the execution session (SVG generation + export). The new session reloads `design_spec` / `spec_lock` / `sources` / `images` from disk and continues from there.

Split mode is a **compromise** — it pays ~6K tokens (re-reading SKILL.md) to drop 60–200K of planning-session noise, then reuses the freed budget in the execution session to re-read `sources/` for richer slide content. **Not needed when signals are normal**; the hint won't appear, and you can always ignore it and stay in continuous mode.

## Q: Can I preview or fix individual pages before the full export?

Yes. You can **interrupt the workflow at any time** — after the first few pages are generated, review them and give feedback. The AI can regenerate specific pages based on your comments. You don't need to wait until the end to make corrections.

For post-generation fixes, simply tell the AI: "Page 3 has a layout issue — the title overlaps the chart" and it will fix that specific SVG.

## Q: I have an existing PPT and want to build on it — which route should I use?

Think of "using an existing PPT" as two questions: **keep its content or not**, and **keep its design (layout + visuals) or not**. The four combinations map to four routes:

| Intent | Route | What stays fixed |
|---|---|---|
| Keep content + redo layout | **beautify (re-layout)** | Page count, page order, per-slide wording, chart/table data |
| Replace content + keep design | **template-fill** | Native source slide design; selected pages may be reused/reordered |
| Keep only content, redo design and pagination | **main pipeline** | Source facts; story structure and page count may change |
| Keep content + keep design | No generation needed | Use the original file |

Use **beautify** when the source deck's page split is part of the requested output: text stays verbatim, page count and order are preserved 1:1, only layout / hierarchy / whitespace are redone while inheriting the original palette/fonts. Say "make this deck look better" / "re-layout this, keep the wording". See the [beautify workflow](../skills/ppt-master/workflows/beautify-pptx.md).

Use the **main pipeline** when the source PPT is just material: extract it to Markdown with `ppt_to_md`, read PPTX intake facts from `analysis/`, then let Strategist re-architect the outline freely (merge / split / reorder pages). Say "build a better deck from this one's content" or "turn this into a 10-page executive briefing".

The one-line test between beautify and the main pipeline: **is the source's page split information to preserve, or just the previous author's structure to improve?** Preserve → beautify; improve → main pipeline. The concrete discriminator is **page count / order**: if it changes at all — split, merge, drop, reorder, or even keeping every word but splitting one crowded page so it reads better — that is re-pagination, which is the main pipeline. Beautify is strictly 1:1.

If your request is ambiguous, for example "make this PPT more professional" or "optimize this deck", the AI should ask one clarification before routing: **keep the original page count/order and each slide's wording, or treat the PPT as source material and restructure it into a new story?**

There is also one orthogonal route: if you don't want to produce a deck right now but want to **harvest the design into a reusable template** for future use, use **create-template** (see "How do I create a custom template?" below).

---

## Q: I already have a finished `.pptx` — can I reuse its design and just fill in new content?

Yes — this is the **template fill** route, separate from the SVG generation pipeline. Give the AI your existing `.pptx` plus your material (or a topic) and ask it to "fill this deck with the new content" or "fill this back into the template". It treats your deck as a native slide library, lets you pick only the pages that fit the new story (reorder freely, and reuse one page for several output slides), and writes the new text — plus native table cells and chart data — straight into the original OOXML.

The output stays 100% native-editable PowerPoint: the original design, layouts, images, and animations are preserved, and only the selected pages are exported. It deliberately does **not** change layouts, add pages, or swap images — a deck's page structure encodes its logic (lead-then-detail, comparison, progression), so pick pages whose structure already fits your content rather than forcing it in. For a fresh structure or a different page count, use create-template (next question) instead. Full steps: [template-fill workflow](../skills/ppt-master/workflows/template-fill-pptx.md).

---

## Q: How do I create a custom template?

Want to turn a PPT you love into a reusable template for PPT Master? Here's how:

**Step 1 — Prepare Reference Material**

The recommended input is the original `.pptx`. PPT Master extracts theme identity, the complete Master/Layout topology, placeholder metadata, and reusable assets, then reconstructs every source Master and Layout as complete structured SVG pages. Source Master/Layout groups are flattened object by object into direct atomic layer elements; supported appearance, parent relationships, picker names, placeholder type/index/bounds, and stacking order are retained, but the source group-editing hierarchy is not. When that template is used, `adaptive` may create a new explicit Layout under the retained Master; `strict` preserves the selected Master/Layout/slot contract.

If no source PPTX exists, screenshots of the key page types still work — cover, TOC, chapter, content, and closing — but geometry, fonts, and inheritance must then be inferred visually.

**Step 2 — Let AI Create the Template**

Use an AI coding agent (Claude Code, Codex, etc.) and ask it to use the **PPT Master `/create-template` workflow** to convert your reference material into a template. The more context you give, the better the result — for example:

- Template name and intended use case (e.g., government reports, premium consulting)
- Desired tone and color palette (e.g., "modern and restrained, dark blue primary")
- Category preference (`brand` / `general` / `scenario` / `government` / `special`)
- Canvas format, if not the default 16:9
- Output scope: indexed `library` (default) or one already initialized `project`; both use the same complete workspace shape

You don't need to supply every detail upfront — the AI agent will ask follow-up questions to fill in anything missing (output scope, template ID, theme mode, etc.).

**Step 3 — Wait for the Result**

The AI agent will handle the rest — analyzing your screenshots, building the layout definitions, validating the template, and exporting `exports/<id>_template_preview.pptx` for visual review in PowerPoint. Both scopes contain the same `templates/`, `images/`, `icons/`, and `exports/` core: library scope writes `skills/ppt-master/templates/<kind>/<id>/` and registers it; project scope writes `projects/<name>/` and skips registration. Give that workspace root to Step 3. Older flat packages with `design_spec.md` at the root remain compatible, and flat placement alone is not a reason to run structure restoration. Because the new workspace shapes match, a complete result can be migrated or reused between the two locations without restructuring it.

> **Tip**: The more specific you are about the style and use case, the better the generated template will match your expectations.

---

> For more questions, see [SKILL.md](../skills/ppt-master/SKILL.md) and [AGENTS.md](../AGENTS.md)
