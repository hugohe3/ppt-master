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

Source content conversion is invisible to most users but shapes everything downstream: source documents (PDF / DOCX / EPUB / XLSX / PPTX / web pages) are normalized into Markdown before the pipeline starts. The Markdown becomes Strategist's reading material and the source of truth for every subsequent decision.

Two cross-cutting design choices shape the converters:

**Native-Python first, external binaries as fallback.** `doc_to_md.py` uses `mammoth` for `.docx`, `markdownify` + `beautifulsoup4` for `.html`, `ebooklib` for `.epub`, `nbconvert` for `.ipynb` — all pure Python wheels. Pandoc is only invoked for the long tail (`.doc` / `.odt` / `.rtf` / `.tex` / `.rst` / `.org` / `.typ`). PDF goes through `PyMuPDF` for native-text PDFs, with MinerU / OCR tools recommended only when the PDF is scanned. Rationale: avoid making every user install a system-level binary they may not have permissions for, while still covering edge cases.

**TLS fingerprint impersonation for high-security sites.** `web_to_md.py` uses `curl_cffi` to impersonate a modern Chrome TLS fingerprint by default. This single dependency lets the same script handle WeChat Official Accounts (`mp.weixin.qq.com`) and other CDNs that block Python's default `requests` TLS handshake. The Node.js sibling `web_to_md.cjs` is retained only as a backup for environments where `curl_cffi` has no prebuilt wheel.

All converters produce the same output convention: `<input>.md` plus a sibling `<input>_files/` directory with extracted images at relative paths. This convention is what `import-sources --move` keys off of during project initialization.

---

## Project Structure & Lifecycle

A PPT Master project is a directory with a fixed shape:

```
projects/<name>_<format>_<timestamp>/
├── sources/              # raw inputs after import-sources
├── images/               # AI-generated + searched + user-supplied images
├── templates/            # optional template SVGs / design_spec_reference
├── design_spec.md        # human-readable design narrative (Strategist output)
├── spec_lock.md          # machine-readable execution contract (Strategist output)
├── notes/                # speaker notes, split per slide by total_md_split.py
├── svg_output/           # Executor's authored SVG pages (source of truth)
├── svg_final/            # post-processed self-contained SVGs (IDE preview)
├── exports/              # final native pptx
└── backup/<ts>/          # timestamped snapshots from svg_to_pptx
```

`project_manager.py init` creates this skeleton; `import-sources` is the only sanctioned way to bring source files into `sources/`. Two import semantics matter:

- Files **outside** the repo: copied by default (preserve user's original); `--move` to consume them
- Files **inside** the repo: moved by default (avoid leaving stray artifacts that get accidentally committed); `--copy` to override

This asymmetry is deliberate. The default behavior matches the natural risk profile in each context — outside-repo files are typically user assets we shouldn't disturb; inside-repo files are typically intermediate artifacts that should be cleaned up.

`batch_validate.py` exists for repository-wide health checks before release, and `error_helper.py` provides standardized fixes for the common project-structure errors so the AI can self-recover from broken state mid-pipeline.

---

## Canvas Format System

PPT Master is not PPT-only. The same SVG → DrawingML pipeline can produce square posters, 9:16 stories, or A4 prints — only the `viewBox` changes. Nine canvas formats cover the common content purposes:

| Format | viewBox | Ratio | Purpose |
|---|---|---|---|
| `ppt169` | 1280×720 | 16:9 | Modern presentations |
| `ppt43` | 1024×768 | 4:3 | Traditional projectors / academic |
| `xiaohongshu` | 1242×1660 | 3:4 | RED knowledge posts |
| `moments` | 1080×1080 | 1:1 | WeChat / IG square |
| `story` | 1080×1920 | 9:16 | TikTok / Stories |
| `wechat_article` | 900×383 | 2.35:1 | WeChat article header |
| `banner` | 1920×1080 | 16:9 | Web / digital screens |
| `poster` | 1080×1920 | 9:16 | Phone / elevator ads |
| `a4` | 1240×1754 | 1:√2 | Print |

The viewBox dimensions are pixel values, not absolute units (EMU is computed at PPTX export time). Pixel viewBox makes it easier for the AI Executor to reason about layout (`x="100"` is unambiguously left edge + 100px), and easier for human inspection in any browser. The conversion to PowerPoint's EMU happens once, during `svg_to_pptx`, via the canonical EMU/px ratio (914400 EMU per inch ÷ 96 px per inch = 9525 EMU/px).

Layout principles diverge per orientation:

- **Landscape (16:9 / 4:3 / 2.35:1)** — Z-pattern visual flow, multi-column / left-right split / grid layouts, 40-80px margins
- **Portrait (3:4 / 9:16)** — top-to-bottom flow, single-column / top-bottom split / card stack, 60-120px margins
- **Square (1:1)** — center-radiating, ~800px core area, 60-100px margins

Each format also has format-specific design conventions (page number position for PPT; brand area for RED; safe zones for Stories) — these live in `references/canvas-formats.md` for the Executor.

---

## Template System & Optional Path

Templates are an opt-in path, not a default. The default Strategist flow is **free design** — open canvas, AI invents the visual system from the source content alone. The template path is entered only when an explicit user trigger fires: naming a specific template, naming a brand or style that maps to one, or asking what templates exist.

**Why default to free design.** Templates are floors that easily become ceilings — they lock the deck into the template's visual idioms. AI is good at generating original layouts that match content rhythm; constraining it to a template often produces a worse fit than letting it design fresh. So the AI never proactively offers a template — the user must reach for it.

**Soft-hint mechanism.** When the source content is an obvious strong match for an existing template (academic defense, government report, McKinsey-style deck) AND no user trigger fired, Strategist emits a one-sentence non-blocking notice: *"the library has a template `<name>` that matches this scenario closely. Say the word if you want to use it; otherwise I'll continue with free design."* This is a hint, not a question — generation continues without waiting. Skipped on weak or ambiguous matches.

**Three template libraries.** The `templates/` directory hosts three libraries with different roles:

| Library | Path | What it provides | When used |
|---|---|---|---|
| Layouts | `templates/layouts/<name>/` | Whole-deck templates: SVG pages + `design_spec_reference.md` + assets | Opt-in only, on user trigger |
| Charts | `templates/charts/<name>.svg` | Reusable visualization SVGs (charts, infographics, diagrams, frameworks) | Every Executor references these for chart pages |
| Icons | `templates/icons/<library>/` | Three icon libraries (`chunk-filled` / `tabler-filled` / `tabler-outline`) — pick one library per deck based on content tone | Every deck uses one library; never mixed |

Charts and icons are referenced by every Executor regardless of layout choice; layout templates are the opt-in piece.

**Creating new templates.** The `create-template` standalone workflow takes a reference PPTX, externalizes its assets, infers theme colors and typography, and produces SVG slides + manifest in `<pptx_stem>_template_import/`. This is a one-shot ingestion, not part of the deck-generation pipeline. Native SVG export from PPTX is Windows-only (uses installed PowerPoint COM); macOS falls back to Keynote → PDF → SVG.

---

## Role System: Three Specialized Agents in a Single Pipeline

PPT Master uses **role switching within one main agent** rather than parallel sub-agents. Three roles, one continuous context, sequential execution:

```
Strategist  →  Image Acquisition (conditional)  →  Executor
   ↓                  ↓                                ↓
design_spec.md   images/*.png                      svg_output/*.svg
spec_lock.md     image_prompts.md                  notes/total.md
                 image_sources.json
```

The Image Acquisition phase dispatches each row to one of two independent sub-roles based on its `Acquire Via`: `image-generator` for `ai` rows (AI generation), `image-searcher` for `web` rows (web search). They are loaded lazily — a deck with only `ai` rows never reads `image-searcher.md`. See "Image Acquisition & Embedding" below.

**Why one agent, not parallel sub-agents?** Page design depends on the full upstream context — Strategist's color choices, the image resources that did or did not get acquired, prior pages' visual rhythm. SKILL.md explicitly forbids delegating page SVG generation to sub-agents (rule 6 of the Global Execution Discipline). Sequential page-by-page generation in one continuous pass is mandated (rule 7) — batched generation (e.g., 5 pages at a time) is forbidden because it accelerates context compression and breaks visual consistency.

**Why role-specialized references rather than one mega prompt?** Each role has its own `references/<role>.md` with focused instructions. Mixing them all in one prompt would force the model to juggle Strategist's "negotiate with user" mode with Executor's "produce strict XML" mode in the same turn — they want different temperature, different formatting discipline, different failure tolerance.

**Eight Confirmations.** The Strategist phase ends with eight bundled confirmations (canvas / page count / audience / style / color / icon / typography / image) that are presented to the user as a **single blocking decision point**. After confirmation, all subsequent phases run automatically without further user gates. This is the only blocking checkpoint in the deck-generation flow — every other gate is procedural.

**User-provided image analysis (conditional, runs before the Eight Confirmations).** When the user supplies images alongside source documents, Strategist MUST run `analyze_images.py <project>/images` before drafting `design_spec.md`. The script extracts each image's dimensions, EXIF orientation, dominant color, and subject metadata into a textual summary. Strategist reasons over that summary — opening image bytes directly is forbidden by SKILL.md's image-handling rule, because the LLM doesn't need pixels to make layout decisions, it needs metadata that fits on a page (aspect ratio for placement, color tone for palette compatibility, subject for slide assignment). The output feeds into the image resource list inside `design_spec.md`, grounding the Eight Confirmations in actual provided assets rather than filenames.

**Per-page spec_lock re-read.** Before generating each SVG page, Executor must re-read `spec_lock.md`. This is the explicit anti-drift mechanism that lets the system produce 20-page decks with consistent color/font/icon discipline despite the LLM's context window being lossy.

Three Executor styles ship as separate references — `executor-general.md`, `executor-consultant.md`, `executor-consultant-top.md` — selected by the user's chosen style. Each loads only the relevant style file plus the shared `executor-base.md` and `shared-standards.md`, keeping the context payload minimal.

---

## Execution Discipline

The pipeline is enforced by an 8-rule set in SKILL.md's Global Execution Discipline. They look bureaucratic but each one closes a specific failure mode observed in practice.

| # | Rule | What it forbids | Why |
|---|---|---|---|
| 1 | **Serial execution** | Skipping or reordering steps | Each step's output is the next step's input; out-of-order execution silently uses stale or absent inputs |
| 2 | **BLOCKING = hard stop** | Auto-deciding past a `⛔ BLOCKING` checkpoint (Eight Confirmations) | The user must own design choices; AI proxying the decision creates decks that don't match user intent |
| 3 | **No cross-phase bundling** | Combining multiple phases into one turn | LLMs that try to do Strategist + Executor in one shot drift on either correctness or style |
| 4 | **Gate before entry** | Starting a step before its prerequisites are met | Each step lists 🚧 GATE prerequisites; checking them prevents cascading errors |
| 5 | **No speculative execution** | Pre-preparing later step's content (e.g., writing SVG during Strategist phase) | The earlier phase's outputs may invalidate that pre-work; doing it wastes context and creates inconsistency |
| 6 | **No sub-agent SVG generation** | Delegating page SVG generation to sub-agents | Page design needs full upstream context (color choices, prior visual rhythm, available images); sub-agents start with stale partial context |
| 7 | **Sequential page generation only** | Batching pages (e.g., 5 at a time) | Batching accelerates context compression and breaks visual consistency across the deck |
| 8 | **Per-page spec_lock re-read** | Generating an SVG without re-reading `spec_lock.md` | Resists context-compression drift on long decks — page 18's color must match page 1's |

**Role Switching Protocol.** When the agent switches roles (Strategist → Executor, etc.), it MUST first `read_file references/<role>.md` and output a markdown marker:

```
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

This serves two purposes: forces fresh role instructions into context (overriding any drift from the previous role's mode), and creates an audit trail in the conversation transcript so the user can see when the agent moved between modes.

The discipline is intentionally explicit because LLMs default to "let me solve the whole problem in this turn" — which is the wrong shape for a serial pipeline where each step depends on bounded, checkpointed outputs from the previous one.

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

Image Acquisition is conditional. The design spec produces a resource list where each image row has an `Acquire Via` field: `ai` (AI generation), `web` (web search), `user` (already provided), or `placeholder` (defer). Only rows marked `ai` or `web` trigger this phase; pure-`user` decks skip it. The phase splits into two independent sub-roles dispatched per row: `image-generator` for `ai` rows, `image-searcher` for `web` rows. A mixed deck loads both reference files and runs each row through its own path; `ai`-only or `web`-only decks load only the relevant role.

**Multi-backend image generation** (the `ai` path). `image_gen.py` is a thin dispatcher over a backend registry. Backends are tiered:

- **Core** — production-ready (OpenAI gpt-image, Google Imagen, MiniMax, Qwen, Volcengine, Zhipu, Gemini)
- **Extended** — specialized models opt-in by the user
- **Experimental** — API-unstable, opt-in only

Configuration uses **provider-specific keys only** (`OPENAI_API_KEY`, `MINIMAX_API_KEY`, `GEMINI_API_KEY`, ...). Generic fields like `IMAGE_API_KEY` / `IMAGE_MODEL` / `IMAGE_BASE_URL` are intentionally rejected — they cause silent confusion when multiple providers are configured in one `.env`. The active backend must be selected explicitly via `IMAGE_BACKEND=<name>`.

**Web image search with license discipline** (the `web` path). `image_search.py` is the sister tool, used when the resource list says `Acquire Via: web`. Default chain: zero-config providers (Openverse, Wikimedia) → keyed providers (Pexels, Pixabay) when their key is set. License filter defaults to permissive (CC0, PDM, Pexels, Pixabay, CC BY, CC BY-SA) — Executor adds inline credit when the chosen image is `attribution-required`. `--strict-no-attribution` restricts to zero-attribution licenses, used for full-bleed hero images that have no visual room for a credit element. Auto-rejected: any non-commercial (CC BY-NC*) or no-derivatives (CC BY-ND*) license. Provenance is tracked in `image_sources.json` (provider / license / author / source URL / dimensions / attribution_text), idempotent on filename.

**Embedding strategy.** During development, images stay as **external references** in `svg_output/` — fast iteration, easy replacement. `finalize_svg.py align-images` step Base64-inlines them when producing `svg_final/`, because IDE / browser / preview pptx all need self-contained files. The native pptx converter does **not** Base64-inline — it copies bitmap files into the PPTX media folder and uses `<a:srcRect>` to express SVG's `preserveAspectRatio="... slice"` cropping inside DrawingML. Two paths because external references are debuggable while embedded payloads are deliverable; they coexist by design.

---

## SVG Constraints: Banned Features and Conditional Allowances

PowerPoint's DrawingML is a strict subset of what SVG can express. The Executor operates inside a **banned-features blacklist** designed empirically from PPT export failures:

**Hard-banned (export breaks otherwise):**
- `<mask>` — DrawingML has no per-pixel alpha
- `<style>` / `class` — DrawingML has no CSS selector model
- External CSS / `@font-face` — fonts must be system-installable, not file-loaded
- `<foreignObject>` — embedded HTML inside SVG has no DrawingML mapping
- `<symbol>` + `<use>` for general reuse — DrawingML has no symbol model (icon `<use data-icon>` is project-internal and gets expanded pre-conversion, not the same thing)
- `textPath` — text along arbitrary path has no DrawingML primitive
- `<animate*>` / `<set>` — SVG animation; PowerPoint animation is a separate timing model expressed in slide XML
- `<script>` / event attributes / `<iframe>` — interactivity is a different layer

**XML well-formedness:**
- All text and attribute values must use **raw Unicode** for typography (`—`, `→`, `©`, NBSP) — HTML named entities (`&mdash;`, `&rarr;`) are XML-illegal in SVG
- Reserved XML chars (`& < > " '`) must use XML entities (`&amp;` etc.) — bare `R&D` aborts export

**Conditional allowances (with exact constraint sets in `references/shared-standards.md`):**
- `marker-start` / `marker-end` on `<line>` / `<path>` — allowed only when the marker shape maps cleanly to DrawingML's three arrow-head primitives (triangle / diamond / oval), with marker fill matching line stroke
- `clip-path` on `<image>` only — allowed when the clip shape is a single circle / ellipse / rect / path / polygon, mapping to DrawingML picture geometry. Clip on non-image elements is forbidden (a rect clipped to a circle should just be a circle)

**Effect routing.** Because `<mask>` is banned, common visual effects route differently:

| Effect | Substitute |
|---|---|
| Image gradient overlay (vignette/fade/tint) | Stacked `<rect>` with `<linearGradient>` / `<radialGradient>` |
| Non-rectangular image crop | `clipPath` on `<image>` |
| Inner glow / soft edge | `<filter>` with `<feGaussianBlur>` |
| Drop shadow | Filter shadow or layered rect |
| Pixel-level alpha (text-knockout fills, arbitrary alpha composites) | **No PPT path** — bake into source image at Image Acquisition stage |

`svg_quality_checker.py` enforces this blacklist before post-processing — any banned feature is a blocking error, fixed by regenerating the offending page in the Executor.

---

## Quality Gate

`svg_quality_checker.py` runs after Executor finishes all pages and before any post-processing. The placement is deliberate: post-processing rewrites SVG (icon embedding, image inlining) and would mask source-level violations. The checker reads `svg_output/` only.

**What it checks:**

- **`viewBox`** — present and matching the project's canvas format. Mismatch silently breaks layout when scripts assume canonical pixel space.
- **Banned features** — every entry in the SVG blacklist (mask, style, class, foreignObject, symbol+use, textPath, @font-face, animate*, script, iframe). Any hit is a blocking error.
- **width/height consistency** — `<svg>` root attributes match `viewBox` dimensions.
- **Line-break structure** — multi-line `<text>` uses positional `<tspan>` with `x` + `dy`, not `\n` characters or sibling text drift.
- **spec_lock drift** — colors / fonts / icons / images in the SVG must come from `spec_lock.md`. Off-spec values are warnings (sometimes legitimate) or errors (when they suggest the Executor went off-script).
- **Low-resolution image / non-PPT-safe font tail** — soft warnings; fixed when straightforward, otherwise acknowledged and released.

**Severity model:** errors block the pipeline (regenerate the offending page); warnings inform but don't block. There is intentionally no "auto-fix" mode — fixing a banned feature requires the Executor to re-author the page in context, not a mechanical patch.

**Why this exists at all.** SVG generated by an LLM is not deterministic. Without a checker, banned features creep in over long decks and only surface when `svg_to_pptx` aborts mid-conversion or PowerPoint silently drops elements. The checker turns "PowerPoint export failed at page 14" into "the Executor used `<style>` on page 14, regenerate it" — an order of magnitude faster to diagnose.

The quality checker is also the natural insertion point for **chart coordinate verification** (`verify-charts` workflow). Chart pages have geometric correctness requirements (bar heights / pie sweep angles / axis tick positions) that aren't structural and aren't caught by SVG validity rules. `svg_position_calculator.py` calculates expected coordinates from the data, and the workflow asks the AI to compare and fix mismatches before continuing to post-processing.

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

### FAQ — "Can I delete this?"

| Question | Short answer | Why |
| --- | --- | --- |
| Drop the legacy / preview pptx? | **No** | Cross-platform single-file distribution and multi-page browse-of-backup are workflows neither `svg_final/` (a folder) nor native pptx satisfy |
| Drop `svg_final/`? | **No** | IDE inline preview — `.pptx` is not openable in VSCode / Cursor; `svg_output/` won't render in IDE because of external icon / image refs |
| Drop `finalize_svg.py`? | **No** | `svg_final/` has no other entry point; sub-modules are still memory-reused by native conversion |
| Drop `svg_finalize/{flatten_tspan, embed_icons}`? | **No** — native pptx breaks | See "two consumers" above |
| Drop `svg_finalize/{crop, embed, fix_image_aspect}_images.py`? | **No** | `align_embed_images.py` imports them |
| Drop `svg_rect_to_path.py`? | **Maybe** | Only kept for PowerPoint's manual "Convert to Shape" rounded-corner fallback. Marginal; currently kept to avoid silent regressions on uncommon manual workflows |

### Editing rules

- Edit only `svg_output/` — `svg_final/` is regenerated by `finalize_svg.py` on every run
- After editing `svg_output/`, re-run `finalize_svg.py` to refresh `svg_final/` for IDE preview
- `update_spec.py` only touches `svg_output/` — re-run `finalize_svg.py` after spec changes so `svg_final/` reflects them too

---

## Native PPTX Conversion Internals

`svg_to_pptx/` translates SVG into DrawingML element by element. The mapping table is extensive — see `references/shared-standards.md` for the user-facing version — but the architecture is:

```
svg_output/*.svg
    ↓
[parse to ElementTree]
    ↓
[in-memory pre-process]
   ├─ use_expander       ← svg_finalize.embed_icons
   └─ tspan_flattener    ← svg_finalize.flatten_tspan
    ↓
[per-element dispatch]  drawingml_converter.convert_element(child, ctx)
    ├─ rect / circle / ellipse / line  → prstGeom (preset shapes)
    ├─ rect with rx==ry                → prstGeom roundRect (with adj value)
    ├─ rect with rx!=ry                → custGeom (Bézier per 90° arc)
    ├─ path                            → custGeom (path commands → moveTo/lnTo/cubicBezTo/arcTo)
    ├─ polygon / polyline              → custGeom
    ├─ text                            → txBody with run-level formatting
    ├─ image                           → blipFill picture, with srcRect for slice cropping
    └─ g                               → grpSp (group) with nested xfrm
    ↓
pptx_builder assembles slides → exports/<name>_<ts>.pptx
```

**Why per-element dispatch and not whole-file translation?** SVG's hierarchical model maps cleanly to DrawingML's group / shape / picture types. An element-level dispatcher means each shape kind has its own narrow translator (`drawingml_elements.py` is ~1500 lines of focused converters), debuggable and testable in isolation. There is no global SVG-to-PPTX optimizer — every shape converts independently, and the final PowerPoint file's quality is the sum of those local conversions.

**Two pre-processing steps in memory.** Native pptx reads `svg_output/` directly (no `svg_final/` hop), but DrawingML can't handle two SVG features inline:

- `<use data-icon="...">` placeholders — DrawingML doesn't know `<use>`, so `use_expander.py` calls `svg_finalize.embed_icons` to expand them into raw paths in memory before dispatch
- positional `<tspan>` (with x/y/non-zero dy) — DrawingML text runs cannot reposition mid-paragraph; `tspan_flattener.py` calls `svg_finalize.flatten_tspan` to promote each positional tspan to an independent `<text>` element

This is the "memory consumer" relationship described in the Post-Processing Pipeline section above.

**Office compatibility mode (default on).** PowerPoint versions before 2019 can't render SVG natively. The converter generates a PNG fallback for each slide (via svglib + reportlab) and embeds it as a fallback alongside the native shapes. Newer Office still shows editable shapes; older Office shows the PNG. `--no-compat` disables this fallback.

---

## Animation & Transition Model

PPT Master maps two layers of motion:

**Page transitions** (`-t` flag) — applied between slides. Available effects: `fade` (default), `push`, `wipe`, `split`, `strips`, `cover`, `random`. Implemented as `<p:transition>` elements in slide XML. `none` disables.

**Per-element entrance animations** (`-a` flag) — applied to top-level `<g id="...">` groups in z-order. Default `mixed` cycles through a curated visible-effect pool deterministically (first group always `fade`, then varied across the deck) to give visual variety without per-page configuration. Other choices: a single named effect, `random`, or `none`.

Why anchor on top-level `<g>` groups? PowerPoint's animation timeline is shape-keyed — each animated object needs a stable shape ID. Top-level groups are the natural granularity (one logical content block per group), and Executor is required to use `<g id="...">` grouping anyway (memory rule). Aim for 3-8 content groups per slide; pages with no top-level groups fall back to top-level visible primitives, capped at 8.

**Page chrome is auto-skipped.** Animation skips groups whose `id` matches `background` / `header` / `footer` / `decoration` / `watermark` / `page_number` tokens — these are static frame elements that shouldn't fly in.

**Start mode** (`--animation-trigger`) mirrors PowerPoint's animation-pane Start dropdown:

- `after-previous` (default) — cascade on slide entry, gap controlled by `--animation-stagger` (default 0.5s). Click-free.
- `with-previous` — all groups start together on slide entry
- `on-click` — one click per group, presenter-paced

**Recorded narration.** Optional layer for video export. `notes_to_audio.py` generates per-slide audio (edge-tts default; cloud TTS providers like ElevenLabs / MiniMax / Qwen / CosyVoice opt-in) from `notes/*.md`. `svg_to_pptx --recorded-narration audio` embeds the audio per slide and sets auto-advance timings from each clip's duration, producing a deck PowerPoint can export to video using "use recorded timings and narrations".

The full animation effect list, anchor logic, and chrome-skip tokens live in `references/animations.md`.

---

## Standalone Workflows

The repository ships four workflows that are **not part of the main deck-generation pipeline**. Each is opt-in, triggered by a specific user need or content shape, and runs independently from the Strategist → Executor flow.

| Workflow | Path | When to use |
|---|---|---|
| `create-template` | `workflows/create-template.md` | One-shot ingestion: turn a reference PPTX into a reusable template under `templates/layouts/` |
| `verify-charts` | `workflows/verify-charts.md` | Insert between Executor and post-processing **only if** the deck contains data charts (bar / line / pie / radar). Calibrates chart coordinate math that AI routinely gets off by 10–50 px |
| `visual-edit` | `workflows/visual-edit.md` | Post-export iteration. When the user vaguely points at "something looks off" on a generated slide, the workflow opens a browser-based visual editor for fine-grained edits. Skipped when the user describes the change with enough specificity to apply directly |
| `generate-audio` | `workflows/generate-audio.md` | Recorded narration for video export. Picks a TTS backend (edge-tts default; cloud providers like ElevenLabs / MiniMax / Qwen / CosyVoice opt-in), generates per-slide audio from `notes/*.md`, optionally re-exports the PPTX with `--recorded-narration audio` so PowerPoint's video export uses the recorded timings |

**Why these are workflows and not pipeline steps.** Each one solves a sharply scoped problem that doesn't apply to most decks:

- `create-template` is a one-time setup activity per template, not per deck
- `verify-charts` only matters for decks with data visualizations
- `visual-edit` is reactive (responding to a specific complaint), not proactive
- `generate-audio` is a downstream addition (video export), not deck construction

Folding any of them into the default pipeline would either run unnecessary steps for most users (adding latency and failure surface) or force a one-size-fits-all narrowing. Keeping them opt-in lets the main pipeline stay tight while still offering the capability when the user needs it. Each workflow has its own self-contained `workflows/<name>.md` that the agent loads on demand — there is no global registry the agent must consult ahead of time.
