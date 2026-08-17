# FAQ

[English](./faq.md) | [Chinese](./zh/faq.md)

---

## Q: What source formats does PPT Master accept?

Almost anything: **PDF**, **DOCX**, **PPTX**, **EPUB**, **HTML**, **LaTeX**, **RST**, **URLs** (including WeChat articles), **Markdown**, or just plain text pasted into the conversation. The AI agent converts your source material to Markdown automatically before generating slides.

## Q: Can I generate a deck with just a topic, no source materials?

Yes. Tell the AI your topic or scenario (e.g. "make a PPT about Hayao Miyazaki", "introduce our new product"). The Generate PPTX route will run its **topic-research stage** to gather the factual baseline and provenance needed for planning. If you provide partial material, the same stage may fill only the factual gaps required by your requested outcome unless you ask for a source-only result. Project import does not bulk-fetch the adopted webpage URLs recorded in provenance. After normal image search fails, one relevant page may be fetched with its companion images for review, and only selected files enter the deck's image pool.

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

PPT Master works inside any agent-capable AI tool that can read files and run shell commands — **Claude Code** (CLI / VS Code / JetBrains / Web), **VS Code Copilot**, **Codex**, and others. See the cost comparison below for pricing differences.

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
- **Manual download**: grab `ppt-master-skill-*.zip` from the [Releases](https://github.com/hugohe3/ppt-master/releases) page — the skill files only (~56 MB), no full-repo clone.

Either way, run `pip install -r requirements.txt` from the installed location so the post-processing scripts work.

Neither path carries a `.git` directory, so `git describe` cannot report the version. The installed release is recorded in the `metadata.version` field of the skill's own `SKILL.md` frontmatter.

## Q: Can I use AI-generated images in my presentation?

Yes. When the agent host exposes a native image tool, PPT Master can use it without a separate provider image-generation API key. It can also use the built-in `image_gen.py` through a configured provider. Choose "AI generation" for the image approach; you can explicitly ask the agent to use its own image tool. You can also place your own images in the project's `images/` folder.

## Q: I don't have an image-generation API key — can I still get images?

Yes. If the agent host exposes native image generation, choose "AI generation" and ask it to use its own image tool; this needs no provider image API key. Otherwise, pick "Web-sourced" in the Strategist's Image Usage step. PPT Master ships a zero-config `image_search.py` that searches openly-licensed images across Openverse and Wikimedia Commons. Zero-config search is a fallback: it works immediately, but quality can be uneven because many results are ordinary user uploads.

For better contemporary stock photography, set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` in `.env` (both are free). The search will include Pexels / Pixabay automatically, which usually improves people, workplace, lifestyle, product, and illustration images. You can mix paths in one deck (e.g. AI for hero illustrations, web for team photos). If a selected image requires attribution, Executor adds a small inline credit on the affected slide.

Be clear on what this buys you: **web search only finds *a* relevant, downloadable, license-clean image — it does not guarantee the image is good or right for that page**, because ranking sees text metadata, not the picture. During generation a multimodal model reads a thumbnail to sanity-check and re-queries a poor fit, but **the most reliable route to high quality is to search yourself**: find a better image anywhere, hand the AI its URL, and it downloads and swaps it in via `image_search.py --from-url <url>` (recorded as a manual source; rights are yours to verify). Replacement can happen any time — mid-generation or from live preview — without stopping the run. In short: treat web search as a placeholder fallback and manual picking as the polish step.

## Q: Can I turn AI-generated slide mockups or screenshots into editable PowerPoint slides?

Yes. Provide one or more images and ask to reconstruct the represented pages as an editable PPTX; PPT Master routes that request to the **Image to PPTX** ([`image-to-pptx`](../skills/ppt-master/workflows/profiles/image-to-pptx.md)) profile. It currently requires Codex. Other agent hosts have not been adapted for this profile, so their behavior is not supported or promised. Image to PPTX always activates Quick; you do not need to ask for Quick separately. It first normalizes every input into one ordered page-frame roster, so slide count follows represented pages rather than file count.

Ordinary visible text is rebuilt as native editable text. Logos, icons, badges, and decorative graphics use the source directly when it is adequate; when it is too low-resolution, Codex may reconstruct them from the reference, but identity, silhouette, proportions, colors, and wordmarks must remain fixed, and a merely similar substitute is forbidden. Charts, tables, and data graphics are never reconstructed generatively: they must be native objects with verifiable values, exact source assets, or marked `manual_required`. Photo and illustration scenes are rebuilt into at least a clean base plus subject or foreground layers. Multiple non-overlapping objects with padded bounding boxes may share one generated plate and then become independent PowerPoint picture objects through grid slicing or SVG bounding-box crops. AI may reconstruct pixels hidden by the separated layers, but it must not redesign the visible composition. A whole-slide screenshot skin with token editable overlays does not count as reconstruction.

## Q: Can I edit the generated presentations?

Yes. The only PPTX converter in the SVG pipeline is PPT Master's own `svg_output/` → DrawingML conversion. It saves a timestamped native PowerPoint deck to `exports/`, with text, graphics, and colors directly editable as PowerPoint objects. With the default output path, both Default Generate and Quick Generate copy the authored `svg_output/` to `backup/<timestamp>/svg_output/`, so the same authored deck can be re-exported without re-running the LLM. For Quick this is package reconstruction, not a recoverable record of the AI's design decisions.

`finalize_svg.py` remains a mandatory Step 7 operation in the default Generate flow even though native PPTX export reads `svg_output/`. It produces self-contained files in `svg_final/` for visual inspection and for manual insertion into another deck as SVG pictures. The explicit quick-generate profile skips this preview artifact, but still retains the normal postflight report and default-path backup after its lockless final quality check. PowerPoint's manual **Convert to Shape** command is not a supported round-trip path; use the generated native PPTX when you need editable shapes.

## Q: How does multiline text export? Can PowerPoint reflow it?

By default, a mergeable multiline block exports as one editable PowerPoint text frame. Authored line breaks are retained and PowerPoint automatic wrapping is disabled, so resizing the frame does not rewrite the authored line layout. An ordinary generated frame uses PowerPoint's native **Resize shape to fit text** behavior: deleting a retained break expands the frame instead of leaving text outside it. Imported exact frames and structured multiline placeholder carriers retain their fixed-size behavior.

To let PowerPoint reflow eligible body text, use `--reflow-text`:

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --reflow-text
```

This restores automatic paragraph reflow and may change the line count. The legacy `--merge-paragraphs` flag is a compatibility alias for `--reflow-text`.

Use `--no-merge` only when every visual line must be an independent PowerPoint text frame:

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --no-merge
```

That mode preserves independent per-line object placement, but a 12-line paragraph becomes 12 textboxes. When chatting with the AI, ask for "automatic text reflow" or "one independent text box per visual line" to select the corresponding export mode.

## Q: Why are font sizes in px, not pt? Do they change on export?

PPT Master works in **unitless px end-to-end** — the confirm page, `spec_lock.md`, and the SVG all carry px; there is no pt layer. The SVG canvas is literally 1280×720 px, so px is the real layout / execution unit, and keeping a single unit avoids the size drift you get when a value is "confirmed as 20pt" but written into the SVG as a different number.

PowerPoint displays pt, so the **export** converts px → pt automatically (`pt = px × 0.75`, kept to one decimal). For example a `24px` body becomes `18pt`, a `42px` title becomes `31.5pt`. So a non-integer like `13.5pt` or `31.5pt` in PowerPoint is **expected and intentional**, not a bug — the size is whatever the px works out to, no longer forced onto whole or half-point values.

The body baseline is a fixed value per **reading mode** (not a range). This controls reading distance and density; it is separate from the open-ended communication intent:

| Reading mode | Body px | ≈ exported pt |
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

And because it runs inside a coding agent, a flat subscription plan lets you make many decks at no extra per-deck cost, while a direct per-token API is simply a different price structure — the choice is yours. Either way, PPT Master adds no cost of its own on top of your AI spend.

## Q: Are the charts in the generated PPTX editable?

By default, charts are rendered as **custom-designed SVG graphics** converted to native PowerPoint shapes — fully editable as shapes (move, recolor, retype, restyle). This is a deliberate default over Excel-driven chart objects: PowerPoint's default charts look generic and dated, and lock decks into rigid templates. SVG charts give you publication-quality visuals you can fine-tune directly in PowerPoint, and they render pixel-consistently across PowerPoint / Keynote / LibreOffice / WPS.

If your workflow specifically requires Excel-driven data editing or PowerPoint's chart/table-specific controls, export with `--native-charts-and-tables`: supported data charts and pure text-grid tables then ship as **PowerPoint-native Chart / Table objects backed by data** (saved as `exports/<name>_<timestamp>_native_charts_tables.pptx`, keeping the deck's own colors instead of PowerPoint's default theme). The default SVG fallback also becomes editable DrawingML shapes, but it has no chart data workbook or table/chart object model. Native objects may look slightly different across PowerPoint / Keynote / LibreOffice / WPS, so the shape-based route remains the visual-stability default.

## Q: Are formulas editable?

Yes, in PowerPoint. PPT Master exports both standalone block equations and
same-paragraph inline formulas as editable OMML, not screenshots or picture
assets. A block uses a formula group; inline math uses a leaf
`<tspan data-pptx-inline-formula="...">preview</tspan>` among ordinary text
runs. Matrices, multiline derivations, and other high-structure expressions
remain blocks. Raw LaTeX does not render in SVG, so each marker carries an
ordinary visible preview that native export replaces without adding an image
fallback.

Forward compilation covers every explicitly named input in Microsoft's
documented Microsoft 365 2606 / Mac 16.110 LaTeX profile and 2605 / 16.109
mhchem profile: symbols, structures, environments, macros, chemistry, local
formula colors, and the documented native normalizations. Unknown and
explicitly unsupported input fails closed instead of appearing as raw LaTeX.
For PPTX import, the same closed OMML validator supports a narrow reverse path:
PPT Master-owned block and inline math becomes canonical formula markers with
visible SVG previews. This recovers normalized semantics, not the author's
original LaTeX spelling and not arbitrary third-party OMML. Unknown OMML is
reported and retained as readable/opaque fallback in tolerant mode.

The generated OMML retains the PowerPoint 2010+ package target, and the
executable source profile is pinned to the Microsoft documentation versions
above. Repository verification covers compiler behavior, OMML structure, and
PPTX packaging rather than complete Microsoft 365 UI rendering/editability
certification. Formula display and editability in Keynote, WPS, LibreOffice,
and other non-PowerPoint clients are not supported; PPT Master does not add an
image fallback for them.

## Q: Can generated slides contain clickable links?

Yes. PPT Master supports PowerPoint-native links on a whole object or an inline
text run. External targets use an absolute URI such as `https:` or `mailto:`;
same-deck jumps use the exact 1-based `#slide-N` form. Both compile from
standard SVG `<a href>` anchors to native click relationships, and supported
PPTX import reconstructs the same SVG form.

This is a hyperlink contract, not a general PowerPoint action API. Mouse-over,
custom-show, navigation-command, program/macro/OLE/file, and arbitrary action
settings are not authored. See the [PowerPoint ↔ SVG Mapping
Guide](./powerpoint-svg-mapping.md#10-powerpoint-playback-and-package-features)
for the carrier and preservation boundaries.

## Q: Can I change page transitions and element animations?

Yes. Page transitions are on by default (`fade` 0.4s); per-element object
animation is **off by default**—a page appears as a whole instead of having
elements auto-cascade in one by one. Both are controlled by `svg_to_pptx.py`
flags: `-t/--transition` for page-level and `-a/--animation` for element-level.
The object registry includes entrance, emphasis, motion-path, and exit effects.
`pptx_to_svg.py` also reconstructs exact current-registry page transitions and
finite exact-duration object-animation rows into `animations.json`;
unsupported source timing remains an explicit diagnostic.

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push       # different transition
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none       # disable transitions
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto       # enable per-element entrance (effect mapped from group id)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation entrance_fade # enable with one canonical effect
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation emphasis_spin # native emphasis
python3 skills/ppt-master/scripts/pptx_animations.py --list             # complete categorized effect list
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click   # presenter-paced reveals
```

`on-click` is for live presentations. Narrated/video export via `--recorded-narration` rejects it because PPT Master writes page timings, not object-level click timings; use `after-previous` or `with-previous` for narrated decks.

For common commands, Start-mode guidance, and object-level customization, see [Animations & Transitions](./animations.md). Exact effect and validation behavior remains in the linked execution reference.

## Q: Which AI model works best?

**Claude** (Opus / Sonnet) is the recommended and most tested model. SVG layout requires precise absolute-coordinate calculations (font size x character count x container width), and Claude handles this significantly better than alternatives.

**GPT series** older versions tended to produce more layout issues — text overflowing containers, misaligned elements, coordinate miscalculations. Newer versions (e.g. GPT-5.5) have improved noticeably and are usable in practice; if issues appear, tell the AI which page to fix.

Other models (Gemini, GLM, MiniMax, etc.) vary in quality. In general, models with stronger frontend/visual capabilities produce better results.

## Q: Someone said PPT Master is "just a toy" — is that fair?

No. PPT Master is a presentation workflow, not a model or a complete agent. It supplies presentation-specific reasoning, contracts, project state, deterministic conversion, and quality gates; the selected model still sets the quality ceiling. Evaluating the workflow with a weak or small-context model is like test-driving a sports car in first gear and concluding it is slow.

**The full-power combination:**

- **Claude with a large context window** (ideally ~1M tokens): a large context window lets the Executor see every previously generated page in the same session, maintaining visual consistency across the entire deck without splitting runs. Smaller windows force split-mode execution, which introduces visible style drift between phases.
- **AI image generation with `gpt-image-2`** (or similar): placeholder-grade stock images are the single biggest reason decks look generic. Replacing them with on-brand AI-generated illustrations changes the perceived quality immediately.

If the results you've seen look mediocre, check your setup before concluding anything about the tool: What model? What context size? Was image generation enabled? PPT Master + Claude Opus at 1M context + `gpt-image-2` images is a genuinely different experience from PPT Master + a small open-source model with no image API configured.

> **No Claude access?** Project sponsor [PackyCode](https://www.packyapi.ai/register?aff=ppt-master) provides pay-as-you-go access to Claude and other models — no subscription, no overseas card required. Use promo code **`ppt-master`** for 10% off.

One last thing: this is a free, solo-maintained open-source project. If it fits your needs, use it — I'm glad it helps; if it doesn't, pick another tool. Sincere feedback and suggestions are always welcome, because that's how the project gets a little better over time.

## Q: Text overflows or elements are misaligned — what can I do?

The cause depends on where the mismatch appears. If the source SVG already overflows or is misaligned, it is usually an authoring/layout problem: the model must calculate coordinates, font metrics, and container sizes correctly. If the SVG preview is correct but the exported PPTX differs, that may be a converter or renderer bug and should be reported with both artifacts.

**Fixes to try**:
1. Compare the page in `svg_output/` with the exported PPTX to isolate authoring from conversion
2. Tell the AI which specific page has the problem and describe the issue — it can regenerate individual pages
3. If the SVG itself is repeatedly wrong, use a stronger model or ask the AI to fix its coordinates directly
4. Remember: the generated PPTX is a **high-quality editable draft**, not a sealed final deliverable — minor finishing adjustments in PowerPoint are expected

## Q: How long does a presentation take to generate?

A typical 10–15 page presentation takes about **10–20 minutes** with a fast model. Generation is **intentionally serial** (one page at a time) to maintain visual consistency across slides — parallel generation was tested and produced inconsistent styles.

If generation feels slow, check your model's token throughput. The bottleneck is usually the model's output speed, not the scripts.

If what you want is less process rather than a different model, explicitly ask
for quick generation: it skips the Strategist analysis and the confirmation
stop, so the planning phase costs nothing, but per-page SVG authoring takes the
same time. See the next question, "I don't want to confirm a design spec first
— can I generate directly?".

## Q: I don't want to confirm a design spec first — can I generate directly?

Yes. Explicitly request **quick generation**, and the Generate route uses the
[`quick-generate` profile](../skills/ppt-master/workflows/profiles/quick-generate.md).

**What it skips is the Strategist analysis, the `design_spec.md` /
`spec_lock.md` artifacts, and the staged confirmation stop: whatever you state
explicitly is followed, and whatever you leave unspecified the current agent
decides directly and continues, without coming back for approval.** State
nothing, and the agent decides everything. It also skips `finalize_svg.py`, so
Quick creates no `svg_final/` preview.

It does not skip preparation or design capability. Source conversion, research
on identified factual gaps, shared aesthetic references, and every resource the
deck needs still run when required: supplied or extracted images,
AI/web/sliced images, project icons, native shapes, charts/tables, and the
required operational manifests or provenance records. Formulas are authored
directly as PowerPoint-native markers in the affected SVG, not prepared as
image assets. If a required asset is not ready, it still stops and asks you for
it instead of substituting unrelated material. After preparation, the current agent
hand-authors `svg_output/` to the shared standards, runs the lockless Quick
final quality checker, fixes every blocking error, and only then exports the
final PPTX.

Ordinary exporter capabilities remain available as needed, including native
chart/table replacement, notes, motion, narration, and diagnostics. Notes,
custom object animation, and narration start off; the agent may enable them when
the request or deck needs them, without opening a confirmation flow. A
default-path export writes the normal postflight report and snapshots
`svg_output/` under `backup/`; an explicit output path keeps the ordinary
no-backup behavior. Page count alone neither activates nor blocks quick
generation.

Because the whole planning phase no longer happens, token usage is materially
lower than the default flow; per-page SVG authoring is the dominant cost of a
run and it does not shrink. Quick keeps the same page-level visual and
resource-authoring capabilities and the shared SVG/resource blocking
standards. It does not run Spec Lock alignment checks; its package keeps
converter-default Theme scaffolding instead of deriving Theme colors, fonts,
and Master title/body size defaults from a lock. It does not promise the same
design decisions or wall-clock time as Default because it has no confirmed
design contract, first-page calibration, or resumable decision history.

## Q: Will long decks blow out the context window in one shot?

Default recommendation: **continuous one-shot generation**. 10–15 page decks fit comfortably in a 200K window, and cross-page visual consistency is best when the Executor can see prior pages in the same session (it actively aligns style, font sizes, and rhythm).

When the current AI editor supports an isolated research worker, `topic-research` keeps raw fetches there and the main chat reads only the saved research supplement and fact-provenance file.

Only when signals are heavy (≥ 18 pages, thick source material, or substantial research material remains in the main chat after a local fallback or unusually large imported supplement) does the AI surface an optional **split mode** hint at the Strategist phase: the planning session (Strategist confirmation stage + image acquisition) ends in the current chat; you open a fresh chat window and type `resume execution projects/<project_name>` to enter the execution session (SVG generation + export). The new session reloads `design_spec` / `spec_lock` / `sources` / `images` from disk and continues from there.

Split mode is a **compromise** — the fresh session pays the fixed cost of reloading the Generate authority and required execution references, but drops the planning-session noise and reuses the freed budget to re-read `sources/` for richer slide content. **Not needed when signals are normal**; the hint won't appear, and you can always ignore it and stay in continuous mode.

## Q: Can I preview or fix individual pages before the full export?

Yes. You can **interrupt the workflow at any time** — after the first few pages are generated, review them and give feedback. The AI can regenerate specific pages based on your comments. You don't need to wait until the end to make corrections.

For post-generation fixes, simply tell the AI: "Page 3 has a layout issue — the title overlaps the chart" and it will fix that specific SVG.

## Q: I have an existing PPT and want to build on it — which route should I use?

Think of "using an existing PPT" as two questions: **keep its content or not**, and **keep its design (layout + visuals) or not**. The four combinations map to three generation paths plus the option to keep the original unchanged:

| Intent | Route | What stays fixed |
|---|---|---|
| Keep content + redo layout | **Generate PPTX + beautify profile** | Page count, page order, per-slide wording, chart/table data |
| Replace content + keep design | **Fill Native PPTX** | Native source slide design; selected pages may be reused/reordered |
| Keep only content, redo design and pagination | **Generate PPTX** | Source facts; story structure and page count may change |
| Keep content + keep design | No generation needed | Use the original file |

Use the **beautify profile** when the source deck's page split is part of the requested output: text stays verbatim, page count and order are preserved 1:1, only layout / hierarchy / whitespace are redone while inheriting the original palette/fonts. Say "make this deck look better" / "re-layout this, keep the wording". See the [beautify profile](../skills/ppt-master/workflows/profiles/beautify-pptx.md).

Use the **main pipeline** when the source PPT is just material: extract it to Markdown with `ppt_to_md`, read PPTX intake facts from `analysis/`, then let Strategist re-architect the outline freely (merge / split / reorder pages). Say "build a better deck from this one's content" or "turn this into a 10-page executive briefing".

The one-line test between beautify and the main pipeline: **is the source's page split information to preserve, or just the previous author's structure to improve?** Preserve → beautify; improve → main pipeline. The concrete discriminator is **page count / order**: if it changes at all — split, merge, drop, reorder, or even keeping every word but splitting one crowded page so it reads better — that is re-pagination, which is the main pipeline. Beautify is strictly 1:1.

If your request is ambiguous, for example "make this PPT more professional" or "optimize this deck", the AI should ask one clarification before routing: **keep the original page count/order and each slide's wording, or treat the PPT as source material and restructure it into a new story?**

There is also one orthogonal route: if you don't want to produce a deck right now but want to **harvest the design into a reusable template** for future use, use **create-template** (see "How do I create a custom template?" below).

---

## Q: I already have a finished `.pptx` — can I reuse its design and just fill in new content?

Yes — this is the **template fill** route, separate from the SVG generation pipeline. Give the AI your existing `.pptx` plus your material (or a topic) and ask it to "fill this deck with the new content" or "fill this back into the template". It treats your deck as a native slide library, lets you pick only the pages that fit the new story (reorder freely, and reuse one page for several output slides), and writes the new text — plus native table cells and chart data — straight into the original OOXML.

The output stays 100% native-editable PowerPoint: the original design, layouts, images, and animations are preserved, and only the selected pages are exported. It deliberately does **not** change layouts, add pages, or swap images — a deck's page structure encodes its logic (lead-then-detail, comparison, progression), so pick pages whose structure already fits your content rather than forcing it in. For a fresh structure or a different page count, use create-template (next question) instead. Full steps: [template-fill workflow](../skills/ppt-master/workflows/template-fill-pptx.md).

---

## Q: Content landed in unexpected places — how do I see what PPT Master detected in my `.pptx`?

Both PPTX-consuming routes write a read-only analysis report before anything is generated. Read that report to see exactly which shapes were recognized.

For **Fill Native PPTX**:

```bash
python3 skills/ppt-master/scripts/pptx_intake.py <deck.pptx> -o <analysis_dir>
```

`<stem>.slide_library.json` lists every fillable slot per slide with geometry, paragraph counts, and text metrics, plus separate `tables` and `charts` sections. A styled plain text box counts as a slot — a shape does not have to be a real placeholder to be filled.

For **Create Template**:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py <deck.pptx> --manifest-only -o <workspace>
```

`manifest.json` reports, per slide, the layout and master paths, placeholders (`type`, `idx`, `semanticRole`, `shapeName`), image assets, text counts, and page type; `native_structure.json` adds the source structure assessment. `--manifest-only` skips SVG export, so it is cheap to run just to look.

Note that Create Template produces a reusable template workspace, not a filled deck: the pages that follow are newly authored by Generate, so the source's body copy and speaker notes are deliberately not carried onto them. If a shape you expected to be usable is missing from these reports, that is the concrete thing to include in an issue.

---

## Q: How do I create a custom template?

Want to turn a PPT you love into a reusable template for PPT Master? Here's how:

**Step 1 — Prepare Reference Material**

The recommended input is the original `.pptx`. PPT Master extracts theme identity, declared Master/Layout topology, placeholder metadata, native-shape evidence, and reusable assets that are actually present and supported. `standard` and `fidelity` use the source as visual reference and author a new SVG roster plus a new Master/Layout/slot system; they neither preserve nor distill source topology. `mirror` instead materializes those validated source facts into a new workspace without semantic synthesis or gap filling. Fixed Master/Layout group wrappers are mechanically expanded into direct atoms because structural layers cannot be `<g>`.

Large imported SVGs may contain native-shape metadata, hidden carriers, and preview fingerprints. That lossless representation stays immutable in the temporary analysis workspace as payload backing. Template creation uses a lightweight editable IR with document-local source refs and a compact path/hash manifest. `standard` / `fidelity` author project-canonical SVG and use compact authored-preset groups only for exact registered preset matches. Mirror materializes final templates from the IR, reuses converter-supported payload only for unchanged Slide-local/slot refs, and keeps an SVG fallback for unsupported or edited objects.

If no source PPTX exists, screenshots of the key page types still work — cover, TOC, chapter, content, and closing — but geometry, fonts, and inheritance must then be inferred visually. This path extracts a reusable template system; when the desired output is one layered editable slide per represented page frame, use Image to PPTX (`image-to-pptx`) instead.

**Step 2 — Let AI Create the Template**

Use an agent-capable AI tool (Claude Code, Codex, etc.) and ask it to use the **PPT Master `/create-template` workflow** to convert your reference material into a template. The more context you give, the better the result — for example:

- Template name and intended use case (e.g., government reports, premium consulting)
- Desired tone and color palette (e.g., "modern and restrained, dark blue primary")
- Category preference (`brand` / `general` / `scenario` / `government` / `special`)
- Canvas format, if not the default 16:9
- Output scope: indexed `library` (default) or one already initialized `project`; both use the same workspace routing and omit empty optional asset directories

You don't need to supply every detail upfront — the AI agent will ask follow-up questions to fill in anything missing (output scope, template ID, theme mode, etc.).

**Step 3 — Wait for the Result**

The AI agent will handle the rest — analyzing your references, writing the kind-specific specification, building structured layout definitions only for Layout/Deck, and validating the workspace. Brand/Style never create a preview PPTX; Layout/Deck generate `exports/<id>_template_preview.pptx` on request and require it for multiple Masters. Both scopes require `templates/`; Brand/Layout/Deck may use package-owned `images/` and `icons/`, while Style contains only `templates/design_spec.md`. Library scope writes `skills/ppt-master/templates/<kind>/<id>/` and registers it; project scope writes `projects/<name>/` and skips registration. Empty optional directories are omitted. Give that workspace root to Step 3; it never copies `exports/`, and library review exports are Git-ignored. A compatible legacy-flat Brand/Layout/Deck workspace remains readable only when it satisfies the current kind contract; Layout/Deck also require current structured SVGs. Style has no legacy-flat form, and semantic-legacy packages must be replaced through `create-template` rather than upgraded in place.

> **Tip**: The more specific you are about the style and use case, the better the generated template will match your expectations.

---

> For more questions, see [SKILL.md](../skills/ppt-master/SKILL.md) and [AGENTS.md](../AGENTS.md)
