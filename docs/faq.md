# FAQ

[English](./faq.md) | [Chinese](./zh/faq.md)

---

## Q: What source formats does PPT Master accept?

Almost anything: **PDF**, **DOCX**, **PPTX**, **EPUB**, **HTML**, **LaTeX**, **RST**, **URLs** (including WeChat articles), **Markdown**, or just plain text pasted into the conversation. The AI agent converts your source material to Markdown automatically before generating slides.

## Q: What happens to images embedded in a DOCX?

DOCX conversion extracts embedded image assets into a companion asset directory and records an image manifest; when the source exposes the information, that record includes displayed dimensions, pixel dimensions, and aspect ratios. Project import makes those companion assets available to the active project. Planning uses source position, surrounding text, captions, alt text, filenames, and geometry to decide whether an extracted asset is used; it does not have to inspect or use every extracted image. A selected image may be shown complete or placed with a focal-safe crop. Extraction and registration do **not** mean that the image is regenerated.

See the [source-conversion output contract](../skills/ppt-master/scripts/docs/conversion.md) for companion assets and the [image-planning contract](../skills/ppt-master/references/strategist-image.md) for selection and geometry evidence.

## Q: Can PPT Master batch-redraw every image in a DOCX to one ratio and style?

No. There is currently no user-facing Generate route that reference-redraws every embedded DOCX image as a batch and automatically replaces the originals. Manifest mode can batch **new** image jobs from prompts, but the built-in CLI's `--reference-image` editing is a narrow single-image path, is not manifest mode, and is available only through supported image backends. The Image to PPTX profile does not fill this gap: it applies when raster inputs represent whole slide pages to reconstruct, not when ordinary photos or illustrations are source assets inside a Word document.

These boundaries are defined by the [image-generation contract](../skills/ppt-master/references/image-generator.md), [Generate Step 5](../skills/ppt-master/workflows/generate-pptx.md), and the [Image to PPTX profile](../skills/ppt-master/workflows/profiles/image-to-pptx.md).

## Q: What is the difference between cropping an image and generating one at a requested aspect ratio?

They change different things. `crop=adaptive` permits but never requires cropping. Executor may use `meet` to show the complete source or a focal-safe `slice` to fill the chosen container; both reuse source pixels. An AI job's `aspect_ratio` requests a newly generated canvas. A reference edit transforms one supplied image through the separate single-image path; it is not a manifest batch operation. See the [image resource-list rules](../skills/ppt-master/references/strategist-image.md), [Executor crop policy](../skills/ppt-master/references/executor-image.md), [SVG image placement contract](../skills/ppt-master/references/svg-image-embedding.md), and [image manifest schema](../skills/ppt-master/references/image-generator.md).

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

When the canvas exactly matches a registered format, pass that key during
initialization (for example, `--format xhs`). For any other canvas, omit
`--format`; Default Generate records the confirmed viewBox in `spec_lock.md`,
and Quick Generate uses the first SVG as the canvas authority. The output is
still a `.pptx` file containing native shapes.

## Q: What AI tools work with PPT Master?

PPT Master works inside any agent-capable AI tool that can read files and run shell commands — **Claude Code** (CLI / VS Code / JetBrains / Web), **VS Code Copilot**, **Codex**, and others. Installation and authentication are handled by the selected host; the [Getting Started guide](./getting-started.md) defines the working-folder model used after installation.

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

For either skill-only path, locate the installed skill directory that contains `SKILL.md` and `requirements.txt`, then run `python3 -m pip install -r "<installed-skill-dir>/requirements.txt"` so the post-processing scripts work.

Neither path carries a `.git` directory, so `git describe` cannot report the version. The installed release is recorded in the `metadata.version` field of the skill's own `SKILL.md` frontmatter.

For users in mainland China who cannot reach GitHub reliably, the complete repository is also mirrored on [AtomGit](https://atomgit.com/hugohe3/ppt-master); clone it or download its ZIP there.

## Q: I installed from a skill marketplace. What prerequisites and working directory do I need?

All installation paths require Python 3.10+ and an installed, authenticated agent host that can read and write files and run shell commands. The `npx skills add hugohe3/ppt-master` path additionally requires a working `npx` command, normally supplied with Node.js/npm; the repository does not declare a Node/npm minimum version. A host's own `/plugin install` command does not use that `npx` path.

The installed skill directory and your working folder are different roles. Install Python dependencies from the directory that contains the installed skill's `SKILL.md` and `requirements.txt`, but start the agent in a separate persistent, writable working folder of your choice. The agent creates that folder's `projects/` directory as needed; you do not need to run it from the host-managed skill cache. See [Getting Started: Set up the installation and working folders](./getting-started.md#set-up-the-installation-and-working-folders) and the skill's [execution entry point](../skills/ppt-master/SKILL.md).

## Q: How can I run the same minimal installation check on macOS or Linux?

After installing the Python dependencies, run the same core import check used by the Windows guide:

```bash
python3 -c "import pptx; import fitz; print('All core dependencies OK')"
```

Then ask the agent for a three-slide "Hello World" deck in Quick mode, with no source file. The import command checks the core Python packages; the Quick run checks project initialization, SVG authoring, validation, and export together. Success means a PPTX appears in the active project's `exports/` directory and the file opens in a presentation application. See the [Windows installation smoke test](./windows-installation.md) and the [Quick profile](../skills/ppt-master/workflows/profiles/quick-generate.md).

## Q: Do I need to create `projects/<name>` manually, and which `exports/` contains my deck?

No. In an agent-driven run, Default Generate Step 2 or Quick initialization creates the active project, normally under `<working-folder>/projects/<generated-project-name>/`, and reports its exact path. With the default exporter path, the deck belongs to that project:

```text
<active-project>/exports/<project-name>_<timestamp>.pptx
```

That is not an unqualified `exports/` at the repository root. An explicitly supplied output path is the exception. See [Generate project initialization and export](../skills/ppt-master/workflows/generate-pptx.md), the [Quick profile](../skills/ppt-master/workflows/profiles/quick-generate.md), and the [working-folder explanation](./getting-started.md#set-up-the-installation-and-working-folders).

## Q: Can I use AI-generated images in my presentation?

Yes. When the agent host exposes a native image tool, PPT Master can use it without a separate provider image-generation API key. It can also use the built-in `image_gen.py` through a configured provider. Choose "AI generation" for the image approach; you can explicitly ask the agent to use its own image tool. You can also place your own images in the project's `images/` folder.

## Q: Why are there no icons? Are icons supposed to appear on every slide?

No per-slide icon coverage is required. In Default, `No base icons` is a valid confirmed choice alongside emoji, bundled SVG icons, and custom project icons. Default's `icons.inventory` indexes its curated prepared pool without assigning icons to pages. Both profiles may use project-local prepared icons; Quick creates neither a general resource roster nor an icon-to-page assignment. The author uses an icon only when it serves that page's communication task, so a deck or page may use none. AI-generated illustrated-icon slices are image assets under a separate path and are also optional.

See the [Strategist icon choice](../skills/ppt-master/references/strategist.md), [Executor icon usage](../skills/ppt-master/references/executor-base.md), and [Quick resource preparation](../skills/ppt-master/workflows/profiles/quick-generate.md).

## Q: I don't have an image-generation API key — can I still get images?

Yes. If the agent host exposes native image generation, choose "AI generation" and ask it to use its own image tool; this needs no provider image API key. Otherwise, pick "Web-sourced" in the Strategist's Image Usage step. PPT Master ships a zero-config `image_search.py` that searches openly-licensed images across Openverse and Wikimedia Commons. Zero-config search is a fallback: it works immediately, but quality can be uneven because many results are ordinary user uploads.

For better contemporary stock photography, set `PEXELS_API_KEY` and/or `PIXABAY_API_KEY` in `.env` (both are free). The search will include Pexels / Pixabay automatically, which usually improves people, workplace, lifestyle, product, and illustration images. You can mix paths in one deck (e.g. AI for hero illustrations, web for team photos). If a selected image requires attribution, Executor adds a small inline credit on the affected slide.

Be clear on what this buys you: **web search only finds *a* relevant, downloadable, license-clean image — it does not guarantee the image is good or right for that page**, because ranking sees text metadata, not the picture. During generation a multimodal model reads a thumbnail to sanity-check and re-queries a poor fit, but **the most reliable route to high quality is to search yourself**: find a better image anywhere, hand the AI its URL, and it downloads and swaps it in via `image_search.py --from-url <url>` (recorded as a manual source; rights are yours to verify). Replacement can happen any time — mid-generation or from live preview — without stopping the run. In short: treat web search as a placeholder fallback and manual picking as the polish step.

## Q: Can I turn AI-generated slide mockups or screenshots into editable PowerPoint slides?

Yes. Provide one or more images and ask to reconstruct the represented pages as an editable PPTX; PPT Master routes that request to the **Image to PPTX** ([`image-to-pptx`](../skills/ppt-master/workflows/profiles/image-to-pptx.md)) profile. It currently requires Codex. Other agent hosts have not been adapted for this profile, so their behavior is not supported or promised. Image to PPTX always activates Quick; you do not need to ask for Quick separately. It first normalizes every input into one ordered page-frame roster, so slide count follows represented pages rather than file count.

Ordinary visible text is rebuilt as native editable text. Logos, icons, badges, and decorative graphics use the source directly when it is adequate; when it is too low-resolution, Codex may reconstruct them from the reference, but identity, silhouette, proportions, colors, and wordmarks must remain fixed, and a merely similar substitute is forbidden. Charts, tables, and data graphics are never reconstructed generatively: they must be native objects with verifiable values, exact source assets, or marked `manual_required`. Photo and illustration scenes are rebuilt into at least a clean base plus subject or foreground layers. Multiple non-overlapping objects with padded bounding boxes may share one generated plate and then become independent PowerPoint picture objects through grid slicing or SVG bounding-box crops. AI may reconstruct pixels hidden by the separated layers, but it must not redesign the visible composition. A whole-slide screenshot skin with token editable overlays does not count as reconstruction.

## Q: Can I edit the generated presentations?

Yes. The only PPTX converter in the SVG pipeline is PPT Master's own `svg_output/` → DrawingML conversion. It saves a timestamped native PowerPoint deck to the active project's `exports/`, with text, graphics, and colors directly editable as PowerPoint objects. With the default output path, both Default Generate and Quick Generate copy the authored `svg_output/` to `backup/<timestamp>/svg_output/`, so the same authored deck can be re-exported without re-running the LLM. For Quick this is package reconstruction, not a recoverable record of the AI's design decisions.

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

## Q: The result looks like only boxes and lines. What run facts should I check first?

PPT Master has no documented `wireframe` runtime mode and no documented visual-equivalence guarantee between releases, so appearance alone does not identify a version regression. First record whether the run used Default or Quick, plus the actual mode, visual style, image-usage choice, base-icon choice, Custom Animations setting, and prepared-resource state. Quick keeps these decisions in the active agent context rather than writing `design_spec.md` or `spec_lock.md`.

Next compare the same page in the active project's `svg_output/` with the exported PPTX. If the SVG is already sparse, inspect the planning, resource, and SVG-authoring layers. If the SVG contains the intended objects but the PPTX loses or changes them, inspect the conversion or rendering layer. This boundary follows [Materials → Plan → Realization](./technical-design.md), the [Default Generate workflow](../skills/ppt-master/workflows/generate-pptx.md), and the [Quick profile](../skills/ppt-master/workflows/profiles/quick-generate.md).

## Q: How is PPT Master priced, and does template reuse reduce token usage?

You pay according to your AI usage; PPT Master adds no subscription fee.

The repository documents template reuse as reuse of identity, method, structure, or a recurring application contract. It contains no measured or guaranteed relationship between template reuse and token usage. See the [product positioning](../README.md#product-positioning) and [template boundaries](./templates-guide.md).

## Q: Are the charts in the generated PPTX editable?

By default, charts are rendered as **custom-designed SVG graphics** converted to native PowerPoint shapes — fully editable as shapes (move, recolor, retype, restyle). This is a deliberate default over Excel-driven chart objects: PowerPoint's default charts look generic and dated, and lock decks into rigid templates. SVG charts give you publication-quality visuals you can fine-tune directly in PowerPoint, and they render pixel-consistently across PowerPoint / Keynote / LibreOffice / WPS.

If your workflow specifically requires Excel-driven data editing or PowerPoint's chart/table-specific controls, export with `--native-charts-and-tables`: supported data charts and pure text-grid tables then ship as **PowerPoint-native Chart / Table objects backed by data** (saved as `<active-project>/exports/<name>_<timestamp>_native_charts_tables.pptx`, keeping the deck's own colors instead of PowerPoint's default theme). The default SVG fallback also becomes editable DrawingML shapes, but it has no chart data workbook or table/chart object model. Native objects may look slightly different across PowerPoint / Keynote / LibreOffice / WPS, so the shape-based route remains the visual-stability default.

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

## Q: Why are there no element animations? Were animations removed?

Animations were not removed. Page transitions are on by default (`fade` 0.4s); per-element object
animation is **off by default**—a page appears as a whole instead of having
elements auto-cascade in one by one. Both are controlled by `svg_to_pptx.py`
flags: `-t/--transition` for page-level and `-a/--animation` for element-level.
The object registry includes entrance, emphasis, motion-path, and exit effects.
`pptx_to_svg.py` also reconstructs exact current-registry page transitions and
finite exact-duration object-animation rows into `animations.json`;
unsupported source timing remains an explicit diagnostic.

Use `-a auto` for deck-wide automatic entrances, a canonical effect for one deck-wide effect, or a project-level `animations.json` for explicit page/object timing. Default runs the custom stage for an existing sidecar, an explicit per-slide/per-object request, or an enabled effective Custom Animations outcome. Quick runs it when a sidecar or its active-context motion decision requires object-level work; recorded, self-running, or video-directed Quick delivery requires that stage unless the user explicitly requests static or page-transition-only playback. A deck-wide-only request can remain exporter flags. If none of these triggers applies, the `fade`/`none` defaults remain. The [Generate workflow](../skills/ppt-master/workflows/generate-pptx.md) and [Quick profile](../skills/ppt-master/workflows/profiles/quick-generate.md) define those triggers.

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
for quick generation: it omits the Strategist analysis and the confirmation
stop, while per-page SVG authoring remains. The repository does not promise a
fixed time reduction for Quick. See the next question, "I don't want to confirm
a design spec first — can I generate directly?".

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
image assets. An explicitly selected manual path or another irreplaceable file
dependency still blocks until you provide the required file. If automated AI
generation or its required slicing is exhausted, Quick instead removes the
failed jobs and stale manifest entries, replans their communication role with
native editable text/SVG or already-prepared non-AI assets, continues the same
run, and discloses the replacement in the final handoff. It never fills the gap
with unrelated material. After preparation, the current agent hand-authors
`svg_output/` to the shared standards, runs the lockless Quick final quality
checker, fixes every blocking error, and only then exports the final PPTX.

Ordinary exporter capabilities remain available as needed, including native
chart/table replacement, notes, motion, narration, and diagnostics. Notes,
custom object animation, and narration start off; the agent may enable them when
the request or deck needs them, without opening a confirmation flow. A
default-path export writes the normal postflight report and snapshots
`svg_output/` under `backup/`; an explicit output path keeps the ordinary
no-backup behavior. Page count alone neither activates nor blocks quick
generation.

Quick omits the separate planning phase, but the repository does not document
a measured or guaranteed token reduction; per-page SVG authoring remains.
Quick keeps the same page-level visual and
resource-authoring capabilities and the shared SVG/resource blocking
standards. It does not run Spec Lock alignment checks or derive a
current-project Theme from a lock. Flat Quick keeps converter-default Theme
scaffolding; structured Quick retains installed per-Master source Themes when
available and infers Master title/body size defaults from semantic slot
carriers. It does not promise the same
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

Think of "using an existing PPT" as two questions: **keep its content or not**, and **keep its design (layout + visuals) or not**. The four combinations map to three processing paths plus the option to keep the original unchanged:

| Intent | Route | What stays fixed |
|---|---|---|
| Keep content + redo layout | **Generate PPTX + beautify profile** | Page count, page order, per-slide wording, chart/table data |
| Replace content + keep design | **Edit Native PPTX** | Native source design; unchanged pages stay byte-for-byte, while selected pages may be edited, reordered, repeated, or omitted |
| Keep only content, redo design and pagination | **Generate PPTX** | Source facts; story structure and page count may change |
| Keep content + keep design | No generation needed | Use the original file |

Use the **beautify profile** when the source deck's page split is part of the requested output: text stays verbatim, page count and order are preserved 1:1, and layout / hierarchy / whitespace are redone. The source palette and fonts are the recommended, preselected defaults; an explicit request or final confirmation can override visual fields, but Beautify never departs from the source identity silently. Say "make this deck look better" / "re-layout this, keep the wording". See the [beautify profile](../skills/ppt-master/workflows/profiles/beautify-pptx.md).

Use the **main pipeline** when the source PPT is just material: extract it to Markdown with `ppt_to_md`, read PPTX intake facts from `analysis/`, then let Strategist re-architect the outline freely (merge / split / reorder pages). Say "build a better deck from this one's content" or "turn this into a 10-page executive briefing".

The one-line test between beautify and ordinary Generate applies when the visible design will be regenerated: **is the source's page split information to preserve, or just the previous author's structure to improve?** Preserve → beautify; improve → ordinary Generate. Beautify is strictly 1:1. If the native design must survive instead, use Edit Native PPTX; its `page_plan.json` may select, reorder, repeat, or omit existing pages without redesigning them.

If your request is ambiguous, for example "make this PPT more professional" or "optimize this deck", the AI should ask one clarification before routing: **keep the original page count/order and each slide's wording, or treat the PPT as source material and restructure it into a new story?**

There is also one orthogonal route: if you don't want to produce a deck right now but want to **harvest the design into a reusable template** for future use, use **create-template** (see "How do I create a custom template?" below).

---

## Q: I already have a finished `.pptx` — can I reuse its design and just fill in new content?

Yes — this is the **Edit Native PPTX** route, separate from Generate. Give the AI your existing `.pptx` plus your material (or a topic) and ask it to "fill this deck with the new content" or "fill this back into the template". It imports the deck into a source-preserving round-trip workspace under `projects/`, treats the source pages as a native slide library, and lets you choose, reorder, repeat, or omit pages before editing selected content.

Unchanged output pages are referenced and restored byte-for-byte. On an edited page, unchanged objects restore in their native form and only changed objects are rebuilt. The ordered `pages` roster in `page_plan.json` uses `source_slide` plus an optional copied `svg` filename to select, reorder, repeat, or omit source pages. Notes, narration, timings, and transitions are overlays on the preserved slide. A deck's page structure encodes its logic (lead-then-detail, comparison, progression), so pick pages whose structure already fits your content rather than forcing it in. When the source library lacks a required new structure, use ordinary Generate, or run Create Template first and then Generate from the resulting workspace. Full steps: [Edit Native PPTX workflow](../skills/ppt-master/workflows/edit-native-pptx.md).

---

## Q: Content landed in unexpected places — how do I see what PPT Master detected in my `.pptx`?

Edit Native PPTX and Create Template each write a readable inventory before authoring begins. Read it to see which pages and objects were recognized.

For **Edit Native PPTX**:

```bash
python3 skills/ppt-master/scripts/pptx_to_svg.py <deck.pptx> \
  -o projects/<slug> --inheritance-mode both --roundtrip
```

`authoring-svg-flat/authoring_summary.json` lists the source page roster and per-page text, image, vector, placeholder, and source-reference counts. Open only the selected compact SVG pages you need to inspect or edit.

For **Create Template**:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py <deck.pptx> --manifest-only -o <workspace>
```

`manifest.json` reports, per slide, the layout and master paths, placeholders (`type`, `idx`, `semanticRole`, `shapeName`), image assets, text counts, and page type; `native_structure.json` adds the source structure assessment. `--manifest-only` skips SVG export, so it is cheap to run just to look.

Note that Create Template produces a reusable template workspace, not a filled deck: the pages that follow are newly authored by Generate, so the source's body copy and speaker notes are deliberately not carried onto them. If a shape you expected to be usable is missing from these reports, that is the concrete thing to include in an issue.

---

## Q: Can I turn a company `.pptx` into a reusable workspace? Which kind should I choose?

Yes, through an explicit `/create-template` request. A complete source deck does not by itself imply `Deck`; choose the kind by what must remain reusable:

| Kind | Reusable contract |
|---|---|
| **Brand** | Identity only: colors, type, logo, voice, and icon language; no page roster |
| **Style** | Communication method and visual defaults without identity truth, page prototypes, or native structure |
| **Layout** | Brand-neutral and application-neutral Master/Layout/slot structure |
| **Deck** | A recurring application or branded structure that integrates identity, structure, and an SVG roster |

Create Template confirms the brief before writing either an indexed `library` workspace or a non-registered initialized `project` workspace. For later Generate runs, pass the resulting workspace root—not the source `.pptx` or its inner `templates/` directory. See the [Create Template route](../skills/ppt-master/workflows/create-template.md) and [Templates Guide](./templates-guide.md).

---

## Q: Does registering a template make every future deck use it automatically?

No. Registration makes a workspace discoverable; it does not select it. In Default Generate, the template must still be confirmed in Stage 1. Supplying exactly one workspace root can preselect it there, but does not bypass confirmation; supplying several roots leaves them as unselected candidates. Quick has no template selector, so an exact root is validated and used directly, while no exact root means free design. A raw `.pptx`, an inner `templates/` directory, a bare template name, or a style phrase is not a workspace selection. See [How template selection works](./templates-guide.md) and the [Quick template boundary](../skills/ppt-master/workflows/profiles/quick-generate.md).

---

## Q: How do I create a custom template?

Want to turn a PPT you love into a reusable template for PPT Master? Here's how:

**Step 1 — Prepare Reference Material**

The recommended input is the original `.pptx`. PPT Master extracts theme identity, declared Master/Layout topology, placeholder metadata, native-shape evidence, and reusable assets that are actually present and supported. `standard` and `fidelity` inspect the complete source inventory as evidence and author a new SVG roster plus a new Master/Layout/slot system; they neither preserve nor distill source topology. `mirror` instead materializes one prototype per source Slide together with only that Slide roster's reachable Layout/Master facts, without semantic synthesis or gap filling. Unreferenced source Layouts/Masters remain analysis evidence rather than mirror output. Fixed Master/Layout group wrappers are mechanically expanded into direct atoms because structural layers cannot be `<g>`.

Large imported SVGs may contain native-shape metadata, hidden carriers, and preview fingerprints. That lossless representation stays immutable as source/package evidence. Template creation uses a lightweight editable IR with document-local source refs and a compact path/hash manifest. `standard` / `fidelity` author project-canonical SVG and use compact authored-preset groups only for exact registered preset matches. Mirror publishes the reviewed current IR as the visible tree; it uses source refs only to validate identity and recover supported non-visible semantics, never to restore ordinary visible lossless subtrees. Unsupported or edited objects keep an SVG fallback.

If no source PPTX exists, screenshots of the key page types still work — cover, TOC, chapter, content, and closing — but geometry, fonts, and inheritance must then be inferred visually. This path extracts a reusable template system; when the desired output is one layered editable slide per represented page frame, use Image to PPTX (`image-to-pptx`) instead.

**Step 2 — Let AI Create the Template**

Use an agent-capable AI tool (Claude Code, Codex, etc.) and ask it to use the **PPT Master `/create-template` workflow** to convert your reference material into a template. The more context you give, the better the result — for example:

- Template name and intended use case (e.g., government reports, premium consulting)
- Desired tone and color palette (e.g., "modern and restrained, dark blue primary")
- Category preference (`brand` / `general` / `scenario` / `government` / `special`)
- Canvas format, if not the default 16:9
- Output scope: indexed `library` (default) or one already initialized `project`; both share one spec schema and asset routing, while library uses a bare spec and project uses qualified specs

You don't need to supply every detail upfront — the AI agent will ask follow-up questions to fill in anything missing (output scope, template ID, theme mode, etc.).

**Step 3 — Wait for the Result**

The AI agent will handle the rest — analyzing your references, writing the kind-specific specification, building structured layout definitions only for Layout/Deck, and validating the workspace. Brand/Style never create a preview PPTX; Layout/Deck generate `exports/<id>_template_preview.pptx` on request and require it for multiple Masters. Both scopes require `templates/`; Brand/Layout/Deck may use package-owned `images/` and `icons/`, while Style contributes only its Design Spec. Library scope writes a bare `templates/design_spec.md` under `skills/ppt-master/templates/<kind>/<id>/` and registers it; project scope writes `templates/design_spec.<kind>.<id>.md` under `projects/<name>/` and skips registration, allowing one contribution of every kind to coexist. Layout owns the active SVG roster when Layout and Deck are both present. Empty optional directories are omitted. Give that workspace root to Step 3; a project root contributes all of its specs atomically, and installation never copies `exports/`. Older flat or semantic-legacy packages are reference inputs only and must be rebuilt through `create-template` before Generate can select them.

> **Tip**: The more specific you are about the style and use case, the better the generated template will match your expectations.

---

> For more questions, see [SKILL.md](../skills/ppt-master/SKILL.md) and [AGENTS.md](../AGENTS.md)
