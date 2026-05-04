# Technical Design

[English](./technical-design.md) | [中文](./zh/technical-design.md)

---

## Design Philosophy — AI as Your Designer, Not Your Finisher

The generated PPTX is a **design draft**, not a finished product. Think of it like an architect's rendering: the AI handles visual design, layout, and content structure — delivering a high-quality starting point. For truly polished results, **expect to do your own finishing work** in PowerPoint: swapping shapes, refining charts, adjusting colors, replacing placeholder graphics with native objects. The goal is to eliminate 90% of the blank-page work, not to replace human judgment in the final mile. Don't expect one AI pass to do everything — that's not how good presentations are made.

**A tool's ceiling is your ceiling.** PPT Master amplifies the skills you already have — if you have a strong sense of design and content, it helps you execute faster. If you don't know what a great presentation looks like, the tool won't know either. The output quality is ultimately a reflection of your own taste and judgment.

---

## System Architecture

```
User Input (PDF/DOCX/XLSX/URL/Markdown)
    ↓
[Source Content Conversion] → source_to_md/pdf_to_md.py / doc_to_md.py / excel_to_md.py / ppt_to_md.py / web_to_md.py
    ↓
[Create Project] → project_manager.py init <project_name> --format <format>
    ↓
[Template (optional)] — default: skip, proceed with free design
    User names a template: copy template files into the project
    Need a new global template: use /create-template workflow separately
    ↓
[Strategist] - Eight Confirmations & Design Specifications → design_spec.md + spec_lock.md
    ↓
[Image Acquisition] (when any row in the resource list needs AI generation or web search)
    ↓
[Executor]
    ├── Visual construction: generate all SVG pages → svg_output/
    ├── [Quality Check] svg_quality_checker.py (mandatory — must pass with 0 errors)
    └── Notes generation: complete speaker notes → notes/total.md
    ↓
[Chart calibration (optional)] → verify-charts workflow (for decks containing data charts)
    ↓
[Post-processing] → total_md_split.py (split notes) → finalize_svg.py → svg_to_pptx.py
    ↓
Output:
    exports/
    └── presentation_<timestamp>.pptx          ← Native shapes (DrawingML) — recommended for editing & delivery
    backup/<timestamp>/
    ├── presentation_svg.pptx                  ← SVG snapshot — pixel-perfect visual reference backup
    └── svg_output/                            ← Archived Executor SVG source (rerun finalize_svg → svg_to_pptx to rebuild)
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

---

## Source Content Conversion

Source documents (PDF / DOCX / EPUB / XLSX / PPTX / web pages) are normalized into Markdown before the pipeline starts — this is the source of truth Strategist reads from. Two design choices shape the converters:

**Native-Python first, external binaries as fallback.** Common formats are handled by pure-Python wheels; pandoc is only invoked for the long tail of niche formats. Forcing every user to install system binaries they may not have permission for is a usability tax that doesn't pay off when 95% of inputs are docx / pdf / html.

**TLS fingerprint impersonation for high-security sites.** Web fetching impersonates a Chrome TLS fingerprint by default. WeChat Official Accounts and several CDNs block Python's default `requests` handshake outright, and a single dependency that handles them is preferable to maintaining a parallel Node.js fetcher as the primary path.

---

## Project Structure & Lifecycle

The non-obvious bit of the project layout is `import-sources`'s **asymmetric default**: files outside the repo are *copied* in (preserving the user's original), files inside the repo are *moved* in (so intermediate artifacts don't get committed by accident). The asymmetry tracks the natural risk profile — outside-repo files are typically user assets we shouldn't disturb, inside-repo files are typically transient artifacts that should be cleaned up. A single uniform default would get one or the other case wrong every time.

---

## Canvas Format System

PPT Master is not PPT-only — the same SVG → DrawingML pipeline produces square posters, 9:16 stories, A4 prints. Format-specific conventions (ratios, safe zones, brand areas) live in [`references/canvas-formats.md`](../skills/ppt-master/references/canvas-formats.md).

The architectural choice worth flagging: **viewBox is in pixels, not absolute units.** Pixel space makes layout reasoning unambiguous for the AI Executor (`x="100"` is unambiguously left + 100px) and inspectable in any browser. Conversion to PowerPoint's EMU happens once at export — picking pixels means the rest of the pipeline (Strategist, Executor, quality checker, post-processing) never thinks in EMU, which would be hostile both to AI generation and to human debugging.

---

## Template System & Optional Path

Templates are **opt-in, not default**. The default Strategist flow is free design — AI invents the visual system from the source content alone. The template path activates only on explicit user trigger.

**Why default to free design.** Templates are floors that easily become ceilings: they lock the deck into the template's visual idioms regardless of how the content actually wants to be presented. Free-design layouts derive structure from the source content rather than imposing it from a fixed grammar, so the visual rhythm tracks the content rather than fighting it. Constrained mode is genuinely better in narrow cases (brand-locked decks, strongly-typed scenarios like academic defense or government report), so it stays available — but the AI doesn't proactively reach for it; the user does.

**Soft-hint, not soft-prompt.** When the content is an obvious match for an existing template AND no trigger fired, Strategist emits a single non-blocking notice and continues with free design. The reason it's a hint rather than a question: blocking on every "you might want a template" prompt would erode the default pace of the flow, and the user can interrupt mid-stream anyway.

**Layouts are opt-in; charts and icons are not.** The asymmetry isn't an inconsistency — *layout* is what locks visual idiom (the floor/ceiling problem above), while charts and icons are reusable primitives that don't impose deck-wide style. Same `templates/` directory, different role in the visual contract.

---

## Role System: Three Specialized Agents in a Single Pipeline

PPT Master uses **role switching within one main agent** rather than parallel sub-agents. The choice has three connected reasons:

**Why one agent, not parallel sub-agents.** Page design depends on the full upstream context — Strategist's color choices, the image resources that actually got acquired (vs failed and substituted), prior pages' visual rhythm. Sub-agents would start with a stale partial snapshot of that context and produce visually drifting decks. The same logic forbids batched page generation (e.g., five pages per turn): batching accelerates context compression and the deck's visual consistency degrades faster than the speed gain is worth.

**Why role-specialized references, not one mega prompt.** Strategist runs in "negotiate with user" mode (open-ended, conversational, willing to back up); Executor runs in "produce strict XML" mode (no improvisation, no missing attributes). Mixing both into one prompt forces the model to hold incompatible discipline in the same turn — every prompt-engineering pathology of mode-mixing shows up. Splitting into per-role files lets each role load only what it needs and discard the rest.

**Eight Confirmations as the only blocking gate.** Strategist ends with eight bundled user confirmations (canvas / page count / audience / style / color / icon / typography / image) presented as one blocking decision point. After confirmation, the pipeline runs to completion without further interrupts. The reason it's bundled and singular: design choices are correlated (color affects icon library affects typography), so resolving them together produces coherent decisions, while spreading confirmations across phases would invite contradictory user inputs and force backtracking.

**User-provided image analysis goes through metadata, not pixels.** When the user supplies images, Strategist runs an extractor that summarizes dimensions, EXIF orientation, dominant color, and subject — and reasons over that text. Opening image bytes directly is forbidden because the LLM doesn't need pixels to make layout decisions; it needs facts that fit on a page (aspect ratio for placement, color tone for palette compatibility, subject for slide assignment). Pixel reading would burn context for no decision-quality gain.

**Per-page spec_lock re-read** is the long-deck anti-drift mechanism — full rationale in § Spec Propagation below.

---

## Execution Discipline

The pipeline is enforced by an 8-rule set in [`SKILL.md` § Global Execution Discipline](../skills/ppt-master/SKILL.md) — that file is authoritative; the rules live there. They look bureaucratic but exist because LLMs default to "let me solve the whole problem in this turn", which is exactly the wrong shape for a serial pipeline where each step's output is bounded, checkpointed, and consumed by the next. The rules collectively close failure modes that surfaced repeatedly in practice: out-of-order execution, AI proxying user design decisions, cross-phase bundling, missing prerequisites, speculative pre-work, sub-agent context loss, page-batching drift, and long-deck color/font drift.

The Role Switching Protocol (mandated read of `references/<role>.md` before mode change) serves two reinforcing purposes: forcing fresh role instructions into context overrides drift from the previous mode, and the visible marker in the conversation transcript creates an audit trail so the user can see when the agent moved between modes — critical when reviewing why a particular decision was made.

---

## Spec Propagation: spec_lock.md as Execution Contract

The Strategist phase produces two artifacts that look redundant but serve different masters:

- `design_spec.md` — human-readable narrative; the "why" of the design (target audience, style objective, color rationale, page outline)
- `spec_lock.md` — machine-readable execution contract; the "what" Executor must literally use (HEX colors, exact font family string, icon library choice, image resource list with status)

Why both? Without `spec_lock.md`, the Executor would re-read `design_spec.md` per page during long decks and the LLM's context-compression drift would gradually mutate colors and fonts mid-deck. `spec_lock.md` is the **anti-drift mechanism** — the SKILL.md mandates `read_file <project>/spec_lock.md` before every page, so values stay verbatim across 20+ slides.

`update_spec.py` propagates a post-generation change in two coordinated steps: write the new value to `spec_lock.md`, then literal-replace it across every `svg_output/*.svg`. The tool's scope is deliberately narrow — only `colors.*` (HEX values, case-insensitive replacement) and `typography.font_family` (attribute-scoped). Other fields (font sizes, icons, images, canvas) are intentionally **not supported** because their replacements would need attribute-scoped or semantic awareness whose risk/benefit doesn't justify bulk propagation. For those, edit `spec_lock.md` and re-author the affected pages.

The tool refuses to back up: it relies on git for revert. Adding a backup mechanism would just duplicate git's job and create stale snapshots.

---

## Image Acquisition & Embedding

Two architectural decisions shape this phase:

**Provider-specific config keys, not a generic `IMAGE_API_KEY`.** Every backend takes its own `OPENAI_API_KEY` / `MINIMAX_API_KEY` / etc. and the active one is selected by an explicit `IMAGE_BACKEND=<name>`. A unified `IMAGE_API_KEY` field looks tidier on first glance but causes silent confusion when a user has multiple providers configured at once and isn't sure which one is active — the kind of fault that surfaces only as "image generation gives weird results" with no clear failure point. Forcing per-provider keys makes "which backend am I using" a config-readable fact, not an inference.

**Permissive-by-default license filter, with strict mode for credit-incompatible layouts.** Web image search defaults to allowing CC BY / CC BY-SA images with inline attribution — most slides have visual room for a credit element. `--strict-no-attribution` is the escape hatch for full-bleed hero images and tight composition where there's no place to put a credit without breaking the design. Non-commercial (CC BY-NC*) and no-derivatives (CC BY-ND*) licenses are auto-rejected because the typical PPT Master output is shared in commercial or modified contexts; a permissive default with that floor is the failure mode users actually want.

**External refs during development, two divergent embedding strategies for delivery.** While editing in `svg_output/`, images are external file references — fast iteration, single-source-of-truth replacement. The two delivery artifacts then diverge: `svg_final/` Base64-inlines (a folder of self-contained SVGs that IDE preview, browser, and the preview pptx can all open without missing the bitmap dependencies); native pptx instead copies bitmaps into the PPTX media folder and uses `<a:srcRect>` to express the cropping. The split exists because Base64 inside DrawingML works but bloats file size 3-4×, while file-referenced bitmaps are PowerPoint's native idiom for which `<a:srcRect>` is the canonical crop expression — wrong tool in either direction would cost editability or file size.

---

## SVG Constraints: Banned Features and Conditional Allowances

PowerPoint's DrawingML is a strict subset of what SVG can express. The Executor operates inside an empirically-grown blacklist (mask, style/class, `@font-face`, foreignObject, symbol+use, textPath, animate*, script/iframe …) plus narrow conditional allowances for `marker-start`/`marker-end` and image-only `clip-path`. The authoritative list and exact per-feature constraints — including the substitute-effect routing table for `<mask>` (gradient overlays, clipPath, filter shadow, source-image bake-in) — live in [`references/shared-standards.md`](../skills/ppt-master/references/shared-standards.md).

The architectural reasons worth knowing here:

- **Why a blacklist, not a whitelist.** SVG is a wide spec; enumerating allowed features would force constant maintenance as the Executor finds new useful constructs. The blacklist captures the narrow set whose semantics have no DrawingML representation, leaving everything else implicitly available.
- **Why empirical, not derived from spec.** The list grew from real PPT export failures, not from reading the OOXML spec. Several features (e.g., `<mask>`) are theoretically expressible in DrawingML but practically unreliable across PowerPoint versions; the blacklist reflects the actually-shippable subset.
- **XML well-formedness traps.** Two cross-cutting gotchas independent of DrawingML: typography must use raw Unicode (`—`, `→`, `©`, NBSP) since HTML named entities (`&mdash;`) are XML-illegal in SVG, and reserved XML chars (`& < >`) must be entity-escaped or `R&D` will abort the export. These bite often enough to flag at the architecture level.
- **The blacklist runs before post-processing.** `svg_quality_checker.py` enforces it on `svg_output/`; post-processing rewrites SVG and would mask source-level violations. Fixes are always re-authoring in the Executor — there is intentionally no auto-fix mode (see Quality Gate).

---

## Quality Gate

**Why a checker exists at all.** SVG generated by an LLM is not deterministic — banned features creep in over long decks and only surface when `svg_to_pptx` aborts mid-conversion or PowerPoint silently drops elements. The checker turns "PowerPoint export failed at page 14" into "the Executor used `<style>` on page 14, regenerate it" — an order-of-magnitude faster diagnosis loop, which is what makes long decks economically feasible to iterate on.

**Why placed before post-processing, not after.** Post-processing rewrites SVG (icon embedding, image inlining), which would mask source-level violations. Reading `svg_output/` directly catches the Executor's actual output, before any cleanup that might paper over a bug.

**Severity model: errors block, warnings don't, and there is intentionally no auto-fix.** Errors require the Executor to re-author the offending page in context — a banned `<style>` element isn't a mechanical patch, because the Executor used it for a reason and the substitute (e.g., inline attributes) needs the same design intent re-applied. Auto-fix would silently lose that intent and ship a worse-looking page.

**Why chart coordinate verification hangs off the same gate.** Chart pages have geometric correctness requirements (bar heights / pie sweep angles / axis tick positions) that aren't structural and aren't caught by SVG validity rules. The natural place to catch them is the same gate where the AI is asked to revisit its output — bundling the cognitive context "look at what you generated and fix it" into one phase, rather than splitting structural and geometric review into separate review rounds.

---

## Post-Processing Pipeline

> Why each artifact and module exists in the engineering conversion stage, and which workflows would break if you delete it. Read this before considering any simplification of `svg_final/` / `finalize_svg.py` / `svg_to_pptx.py`.

### Four artifacts, four workflows

The post-processing stage produces four artifacts. Each one serves a workflow that nothing else in the pipeline can replace.

| Artifact | Workflow it serves | Why nothing else replaces it |
| --- | --- | --- |
| `svg_output/` | source of truth, manual editing, `update_spec.py`, `svg_quality_checker.py` | only directory whose contents are authored, not derived |
| `svg_final/` | IDE inline preview (VSCode/Cursor open `.svg` directly), browser open of a single page | `.pptx` is not openable in IDEs; `svg_output/` won't render fully because of external icon / image refs |
| `exports/<name>_<ts>.pptx` (native) | primary deliverable — editable in PowerPoint with DrawingML shapes | only artifact whose shapes the user can resize / recolor / restyle natively in PowerPoint |
| `backup/<ts>/<name>_svg.pptx` (preview) | cross-platform single-file distribution, multi-page browse, email attachment | self-contained, multi-page, opens in PowerPoint / Keynote / WPS / LibreOffice; an `svg_final/` folder is harder to distribute |

### The `svg_finalize/` package has TWO consumers

This is the key insight that's easy to miss when reading the code. The same modules under `skills/ppt-master/scripts/svg_finalize/` are used in two places, for two different products.

**Disk consumer** — `finalize_svg.py` writes `svg_output/` → `svg_final/` once per run. `svg_final/` then feeds IDE preview and the preview pptx.

**Memory consumer** — native pptx generation reads `svg_output/` directly (no disk hop), but DrawingML can't handle two SVG features inline, so the converter calls `svg_finalize` modules **in memory**:

| In-memory call site | Module reused | Why native pptx needs it |
| --- | --- | --- |
| `svg_to_pptx/use_expander.py` | `svg_finalize.embed_icons` | DrawingML doesn't recognize `<use data-icon="...">`; without expansion every icon silently drops |
| `svg_to_pptx/tspan_flattener.py` | `svg_finalize.flatten_tspan` | DrawingML text runs cannot reposition mid-paragraph; a dy-stacked block of `<tspan>`s would otherwise collapse onto one baseline, and an x-anchored tspan would render in the wrong column |

### Per-module consumer table

| Module | Disk consumer | Memory consumer | Delete impact |
| --- | --- | --- | --- |
| `embed_icons.py` | `finalize_svg` `embed-icons` step | `svg_to_pptx/use_expander.py` | native pptx loses all icons + `svg_final/` not self-contained |
| `flatten_tspan.py` | `finalize_svg` `flatten-text` step | `svg_to_pptx/tspan_flattener.py` | **native pptx multi-line `dy`-stacked text collapses to one line** |
| `align_embed_images.py` | `finalize_svg` `align-images` step | — | `svg_final/` loses image embedding → IDE preview / preview pptx have no images |
| `crop_images.py` / `embed_images.py` / `fix_image_aspect.py` | imported by `align_embed_images.py` | — | `align_embed_images` `ImportError`, full chain broken |
| `svg_rect_to_path.py` | `finalize_svg` `fix-rounded` step | — | only PowerPoint's manual "Convert to Shape" loses rounded corners; browsers / IDE / PowerPoint's own SVG renderer all OK without it |

---

## Native PPTX Conversion Internals

**Why per-element dispatch, not whole-file translation.** SVG's hierarchical model maps cleanly onto DrawingML's group / shape / picture types — there's no need for a holistic optimizer that re-plans the slide. Each shape kind gets its own narrow translator, which keeps each translator simple enough to debug and unit-test in isolation. The output quality of a slide is the sum of independent local conversions; that property is fragile under whole-file translation but robust under element dispatch.

**Why Office compatibility mode is on by default.** PowerPoint versions before 2019 can't render SVG natively. The converter generates a per-slide PNG fallback and embeds it alongside the native shapes — newer Office still shows editable shapes, older Office falls back to the PNG. The default-on choice trades a moderate file-size cost for not silently shipping unopenable decks to users on legacy installs; the escape hatch exists for users who know they're on a modern stack and want the smaller file.

---

## Animation & Transition Model

The interesting design choice is the animation **anchor**, not the effect list.

**Why anchor entrance animations on top-level `<g>` groups.** PowerPoint's animation timeline is shape-keyed — each animated object needs a stable shape ID. Animating individual primitives would produce 30+ separately-flying-in atoms per slide (a kinetic mess), while animating only the slide as a whole loses visual storytelling. Top-level groups are the natural granularity: Executor is required to use `<g id="...">` to mark logical content blocks anyway (so 3-8 groups per slide), and these blocks are exactly the units a viewer reads as "one thing arriving" — animation matches the existing logical structure rather than imposing a new one.

**Why page chrome is auto-skipped.** Groups named `background` / `header` / `footer` / `decoration` / `watermark` / `page_number` represent the static slide frame, not content; flying them in would feel jarring (the page itself materializing every transition) and is virtually never what the user wants. Filtering by id-token is brittle in principle but reliable in practice because the token vocabulary is small and the Executor controls naming.

**Why recorded narration drives auto-advance from clip duration.** When narration is embedded, the deck targets video export — and a video has no presenter to click. Setting per-slide auto-advance timings to the audio clip's actual duration produces a deck PowerPoint exports cleanly to MP4 without manual timing work. Picking any other duration source (estimated reading speed, fixed per-slide) breaks the audio-visual sync.

---

## Standalone Workflows

Four capabilities (`create-template`, `verify-charts`, `visual-edit`, `generate-audio`) live as standalone workflows rather than pipeline steps. Each is sparsely triggered — per-template, per-chart-deck, per-complaint, per-video-export — not per-deck. Folding any into the default pipeline would either run unnecessary steps for the majority of users (added latency and failure surface) or force a one-size-fits-all narrowing of the main flow. Keeping them opt-in lets the deck-generation pipeline stay tight and predictable while making the capability available when its trigger condition fires; each `workflows/<name>.md` is self-contained and loaded on demand, so paying the prompt-context cost is also opt-in.
