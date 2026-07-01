# Technical Design

[English](./technical-design.md) | [中文](./zh/technical-design.md)

---

## Design Philosophy — AI as Your Designer, Not Your Finisher

The generated PPTX is a **design draft**, not a finished product. Think of it like an architect's rendering: the AI handles visual design, layout, and content structure — delivering a high-quality starting point. For truly polished results, **expect to do your own finishing work** in PowerPoint: swapping shapes, refining charts, adjusting colors, replacing placeholder graphics with native objects. The goal is to eliminate 90% of the blank-page work, not to replace human judgment in the final mile. Don't expect one AI pass to do everything — that's not how good presentations are made.

**A tool's ceiling is your ceiling.** PPT Master amplifies the skills you already have — if you have a strong sense of design and content, it helps you execute faster. If you don't know what a great presentation looks like, the tool won't know either. The output quality is ultimately a reflection of your own taste and judgment.

---

## System Architecture

```
User Input (PDF/DOCX/XLSX/PPTX/URL/Markdown/topic text)
    ↓
[Source Content Conversion] → source_to_md/pdf_to_md.py / doc_to_md.py / excel_to_md.py / ppt_to_md.py / web_to_md.py
    ├── Content-type files in sources/ are the content contract
    └── PPTX intake writes analysis/<stem>.identity.json, <stem>.slide_library.json, source_profile.json
    ↓
[Create Project] → project_manager.py init <project_name> --format <format>
    ↓
[Template / Brand / Layout (optional)] — default: skip, proceed with free design
    Trigger only on an explicit template directory path containing design_spec.md kind: brand/layout/deck
    Raw PPTX template requests route to template-fill; reusable SVG templates are created by create-template first
    ↓
[Strategist] - two-tier Eight Confirmations & Design Specifications → design_spec.md + spec_lock.md
    ↓
[Image Acquisition] (when any resource row needs AI generation, web search, or slicing)
    ↓
[Executor]
    ├── Live preview starts and stays available during generation
    ├── Visual construction: generate SVG pages sequentially → svg_output/
    ├── [Quality Check] svg_quality_checker.py (mandatory — must pass with 0 errors)
    └── Notes generation: complete speaker notes → notes/total.md
    ↓
[Chart calibration (optional)] → verify-charts workflow (for decks containing data charts)
    ↓
[Visual self-check (optional, opt-in)] → visual-review workflow (only when the user explicitly requests it)
    ↓
[Post-processing] → total_md_split.py (split notes) → finalize_svg.py → svg_to_pptx.py
    ↓
Output:
    exports/
    ├── presentation_<timestamp>.pptx          ← Native shapes (DrawingML) — canonical output, edit & deliver from here
    └── presentation_<timestamp>_svg.pptx      ← SVG snapshot pptx — pixel-perfect visual reference (opt-in via --svg-snapshot)

    # Always written in default-flow mode (no -o)
    backup/<timestamp>/
    └── svg_output/                            ← Archived Executor SVG source (rerun finalize_svg → svg_to_pptx to rebuild)
```

Direct PPTX workflows intentionally bypass this SVG route:

| Workflow | Input role | Output mechanics | Why it is separate |
|---|---|---|---|
| `template-fill-pptx` | a native PPTX template deck plus new material | clone selected slides and patch text / tables / charts in OOXML | preserves the user's PowerPoint slide shells instead of converting them into SVG |
| `native-enhance-pptx` | a finished PPTX whose layout/content should remain stable | patch notes, narration, timings, and transitions directly in OOXML | appends native enhancements without regenerating design |
| `beautify-pptx` | an existing PPTX whose page count/order/wording must stay 1:1 | extract source facts, regenerate a native deck through the SVG pipeline | changes layout and hierarchy only; it is not direct in-place editing |

---

## Route Decision Quick Reference

Executable route selection is authoritative in [`workflows/routing.md`](../skills/ppt-master/workflows/routing.md); this section is a rationale-oriented quick reference, not a second route matrix to maintain.

Use this table before reasoning about implementation details. Most failed runs start with the wrong route, not the wrong command.

| Request shape | Route | Boundary |
|---|---|---|
| Topic only, no source file or substantive source text | `topic-research` first, then main pipeline | web/source collection is a pre-pipeline step |
| Source files or conversation text, deck structure may be rethought | main SVG pipeline | Strategist may split, merge, drop, reorder, and redesign |
| PPTX as source material, user allows a new story/page structure | `ppt_to_md` + `pptx_intake`, then main SVG pipeline | PPTX identity/geometry are facts and candidates, not replica constraints |
| Raw PPTX template plus new material/topic | `template-fill-pptx` | clone/fill native slides; no SVG generation |
| Existing PPTX, preserve page count/order/wording 1:1, improve layout | `beautify-pptx` | regenerate through SVG; content and pagination are locked |
| Finished PPTX, keep content/layout stable, add notes/audio/timings/transitions | `native-enhance-pptx` | direct OOXML patch; no design regeneration |
| User wants a reusable template package from a PPTX or design reference | `create-template` or `create-brand` | outputs a directory that later triggers Step 3 |
| User supplies an explicit `templates/.../<id>/` directory with `kind: brand/layout/deck` | main SVG pipeline Step 3 | template segment ownership and fusion rules apply |
| User asks to tune object-level animation order/effect/timing | `customize-animations` | optional export policy via `animations.json` |
| User asks to preview, select, annotate, or re-export browser edits | `live-preview` | browser workflow; annotations apply only at defined handoff points |

Ambiguous "optimize this PPT" requests reduce to one discriminator: preserve the original page count/order/wording, or treat the deck as source material and rebuild the story. Preserve means `beautify-pptx`; restructure means the main pipeline.

---

## Technical Pipeline

**The pipeline: AI generates SVG → post-processing converts to DrawingML (PPTX).**

The full flow breaks into three stages:

**Stage 1 — Content Understanding & Design Planning**
Source documents (PDF/DOCX/XLSX/PPTX/URL/Markdown/topic text) are converted into the content and analysis facts the Strategist needs. The Strategist role analyzes the material, reads relevant `analysis/` artifacts, plans the slide structure, and confirms the visual style, producing a complete design specification.

**Stage 2 — AI Visual Generation**
The Executor role generates each slide as an SVG file. The output of this stage is a **design draft**, not a finished product.

**Stage 3 — Engineering Conversion**
Post-processing scripts convert SVG to DrawingML. Every shape becomes a real native PowerPoint object — clickable, editable, recolorable — not an embedded image.

---

## Artifact Flow

Artifact source/derived ownership is authoritative in [`artifact-ownership.md`](../skills/ppt-master/references/artifact-ownership.md); this section visualizes the same dataflow for architecture rationale.

The workflow is easier to maintain if the artifacts are read as a dataflow rather than as folders that happen to exist:

```text
sources/<content files> ────────┐
analysis/source_profile.json ───┼─> Strategist -> design_spec.md + spec_lock.md
analysis/image_analysis.csv ────┘

spec_lock.md + images/ + icons/ + templates/
    └─> Executor -> svg_output/
              ├─> svg_quality_checker.py
              ├─> finalize_svg.py -> svg_final/
              └─> svg_to_pptx.py -> exports/<name>_<ts>.pptx
                                      backup/<ts>/svg_output/

Direct OOXML routes:
analysis/<stem>.slide_library.json + source PPTX + fill_plan.json
    └─> template_fill_pptx.py -> exports/*.pptx
source PPTX project copy + enhancement plan + notes/audio/timing assets
    └─> native_enhance_pptx.py -> exports/*.pptx
```

The critical split is that `svg_output/` is authored state, while `svg_final/`, `exports/`, and `backup/` are derived delivery or archival state. Deleting that distinction makes validation, re-export, and manual repair much harder to reason about.

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

Source documents (PDF / DOCX / EPUB / XLSX / PPTX / web pages) are normalized before Strategist work starts, but there is no single "everything becomes Markdown and nothing else matters" channel anymore. The current design has two fact channels with explicit ownership:

| Channel | Artifact | Owner | Used for |
|---|---|---|---|
| Content contract | `sources/` content-type files (primarily `<stem>.md`) | `source_to_md/*` converters + `import-sources` | text, tables, chart values, citations, and source narrative |
| Structured analysis | `analysis/*.json` / `analysis/*.csv` | intake and analysis tools | PPTX identity, slide geometry, native tables/charts, image dimensions/colors/subjects |

For PPTX sources, `project_manager.py import-sources` runs both `ppt_to_md.py` and `pptx_intake.py`. The Markdown remains the content source for the main generation pipeline. The intake bundle writes `<stem>.identity.json`, `<stem>.slide_library.json`, and merges a compact multi-deck index into `analysis/source_profile.json`. Strategist reads the compact index for source facts and opens raw per-deck artifacts only when a workflow needs them. That distinction matters: the main pipeline may rethink page count and story, while `template-fill` and `beautify` promote parts of the same intake facts into stronger constraints.

Converter-generated image assets are also normalized. Companion `<stem>_files/` directories are imported into the project `images/` pool, `image_manifest.json` is merged by filename, and Markdown asset references are rewritten when imported names change. Office vector images (`.emf` / `.wmf`) are first-class runtime assets: they are not rasterized during intake, `finalize_svg.py` leaves them external for the native path, and `svg_to_pptx.py` embeds them as Office vector media so CJK fonts and vector detail are not lost.

Two converter design choices still shape the system:

**Native-Python first, external binaries as fallback.** Common formats are handled by pure-Python wheels; pandoc is only invoked for the long tail of niche formats. Forcing every user to install system binaries they may not have permission for is a usability tax that does not pay off when most inputs are docx / pdf / html / pptx.

**TLS fingerprint impersonation for high-security sites.** Web fetching uses the Python `web_to_md.py` path by default and relies on `curl_cffi` when available for Chrome-like TLS impersonation. WeChat Official Accounts and several CDNs block Python's default handshake outright; keeping this in the Python converter path avoids making a Node fetcher the primary architecture.

---

## Project Structure & Lifecycle

`project_manager.py init` creates a project as a self-contained workspace, not just an output folder:

| Directory | Role |
|---|---|
| `sources/` | archived originals, normalized Markdown, and converter companion files |
| `analysis/` | machine-extracted facts: PPTX intake bundles and regenerated image analysis |
| `images/` | single runtime image pool for user, extracted, formula, web, AI, sliced, EMF/WMF assets |
| `icons/` | project-local icon set copied by `icon_sync.py`, with global library fallback at export |
| `templates/` | copied template specs / SVG references / non-image template assets |
| `svg_output/` | the only hand-authored SVG source directory |
| `svg_final/` | derived, self-contained SVGs for IDE/browser/preview-snapshot workflows |
| `live_preview/` | preview server state, edit history, and annotation logs |
| `notes/` | `total.md` and split per-slide speaker notes |
| `exports/` | timestamped native PPTX deliverables |
| `backup/<timestamp>/` | frozen `svg_output/` snapshots written by default export |

The CLI still supports three source-import modes: `--move`, `--copy`, and an automatic default that moves repo-local files but copies external files. The production workflow in `SKILL.md` deliberately tightens that: agents must call `import-sources ... --move` so every source artifact and generated intermediate enters `sources/` and the working root stays clean. The script-level default exists for ad hoc CLI safety; the workflow-level contract is stricter so AI runs are reproducible and auditable.

---

## Architecture Invariants

Executable artifact ownership invariants are authoritative in [`artifact-ownership.md`](../skills/ppt-master/references/artifact-ownership.md); this section explains why those boundaries matter architecturally.

These invariants are stronger than ordinary implementation preferences. If a change violates one, it is probably changing the architecture rather than refactoring it.

| Invariant | Practical consequence |
|---|---|
| `sources/` content-type files are the main-pipeline content contract | text, tables, and chart values come from content-type files in `sources/` (Markdown is primary, but `.txt` / `.csv` / `.json` / `.yaml` / … count too); known sidecars (`*.conversion_profile.json`, `*_files/image_manifest.json`) are excluded |
| `analysis/` stores machine facts, not design contracts | `source_profile.json` and intake artifacts inform Strategist; they do not lock page count/order except in workflows that say so |
| `design_spec.md` explains the design; `spec_lock.md` executes it | Executor reads locked values from `spec_lock.md`, not from prose memory |
| `spec_lock.md` is re-read before every page | colors, fonts, icons, images, rhythm, layouts, and chart choices stay stable across long decks |
| `svg_output/` is the only hand-authored SVG directory | quality checks, manual edits, re-export, and `update_spec.py` target authored source |
| `svg_final/` is derived | it can be regenerated from `svg_output/` and should not become the native export source of truth |
| Native PPTX export reads `svg_output/` by default | converter preserves icons, `preserveAspectRatio`, rounded rects, and native image crop metadata before finalization rewrites them |
| Direct OOXML routes do not enter the SVG pipeline | preservation workflows patch native PPTX parts directly |
| Image facts come from regenerated metadata | `analysis/image_analysis.csv` is re-derived from the live `images/` folder; agents do not inspect image pixels directly |
| Raw PPTX templates are not Step 3 templates | Step 3 consumes reusable template directories only |

---

## Canvas Format System

PPT Master is not PPT-only — the same SVG → DrawingML pipeline produces square posters, 9:16 stories, A4 prints. Format-specific conventions (ratios, safe zones, brand areas) live in [`references/canvas-formats.md`](../skills/ppt-master/references/canvas-formats.md).

The architectural choice worth flagging: **viewBox is in pixels, not absolute units.** Pixel space makes layout reasoning unambiguous for the AI Executor (`x="100"` is unambiguously left + 100px) and inspectable in any browser. Conversion to PowerPoint's EMU happens once at export — picking pixels means the rest of the pipeline (Strategist, Executor, quality checker, post-processing) never thinks in EMU, which would be hostile both to AI generation and to human debugging.

---

## Template System & Optional Path

Templates are **opt-in, not default**. The default Strategist flow is free design — AI invents the visual system from the source content alone. The template path activates only on an explicit directory path supplied by the user.

**Why default to free design.** Templates are floors that easily become ceilings: they lock the deck into the template's visual idioms regardless of how the content actually wants to be presented. Free-design layouts derive structure from the source content rather than imposing it from a fixed grammar, so the visual rhythm tracks the content rather than fighting it. Constrained mode is genuinely better in narrow cases (brand-locked decks, strongly-typed scenarios like academic defense or government report), so it stays available — but the AI doesn't proactively reach for it; the user does.

**Mechanical trigger, not semantic matching.** A bare name like `academic_defense`, a brand mention, or a style phrase such as "McKinsey style" does not trigger Step 3 even if a matching library directory exists. Step 3 only consumes a path that resolves to a directory whose `design_spec.md` declares `kind: brand`, `kind: layout`, or `kind: deck`. Discoverability is handled by template indexes and explicit Q&A ("what templates are available?"), not by runtime fuzzy matching.

The three template kinds own different segments of the design contract:

| Kind | Owns | Typical contents | Effect on Strategist |
|---|---|---|---|
| `brand` | identity | colors, typography, logo, voice, icon style | locks identity; structure remains free |
| `layout` | structure | canvas, page structure, page types, SVG roster | locks structure; identity is confirmed in the Eight Confirmations |
| `deck` | identity + structure + template overview | full replica-style package | locks the full template grammar, with only content-specific choices left |

When several paths are supplied, fusion is segment-level, not field-level. A brand overrides the identity segment, a layout overrides the structure segment, and a deck supplies the middle/template-overview segment. Same-kind conflicts are surfaced as conflicts rather than resolved by implicit ordering. This keeps template composition debuggable: a fused spec can say exactly which bundle owns each segment.

**Raw PPTX templates are outside Step 3.** A `.pptx` may be source material, and PPTX intake can extract its identity and geometry. But a raw PPTX template plus a request to generate a new PPTX routes to `template-fill`, because the user's expectation is native slide cloning and text/table/chart replacement. The SVG route can consume only a reusable template package; to use a PPTX's design language in the SVG route, the PPTX must first pass through `create-template`, then the resulting template directory path can be supplied to Step 3.

**Layouts are opt-in; charts and icons are not.** The asymmetry isn't an inconsistency — *layout* is what locks visual idiom (the floor/ceiling problem above), while charts and icons are reusable primitives that don't impose deck-wide style. Same `templates/` directory, different role in the visual contract.

---

## Role System: Specialized Modes in a Single Pipeline

PPT Master uses **role switching within one main agent** rather than parallel sub-agents. Strategist, Image_Generator, Executor, and workflow-specific modes are instruction scopes loaded on demand; they are not independent agents with their own stale copies of the deck state. The choice has three connected reasons:

**Why one agent, not parallel sub-agents.** Page design depends on the full upstream context — Strategist's color choices, the image resources that actually got acquired (vs failed and substituted), prior pages' visual rhythm. Sub-agents would start with a stale partial snapshot of that context and produce visually drifting decks. The same logic forbids batched page generation (e.g., five pages per turn): batching accelerates context compression and the deck's visual consistency degrades faster than the speed gain is worth.

**Why role-specialized references, not one mega prompt.** Strategist runs in "negotiate with user" mode (open-ended, conversational, willing to back up); Executor runs in "produce strict XML" mode (no improvisation, no missing attributes). Mixing both into one prompt forces the model to hold incompatible discipline in the same turn — every prompt-engineering pathology of mode-mixing shows up. Splitting into per-role files lets each role load only what it needs and discard the rest.

**Eight Confirmations as the only blocking gate.** Strategist ends with eight bundled user confirmations (canvas / page count / audience / style / color / icon / typography / image). In the current workflow this is normally delivered through the Confirm UI in two tiers: Tier 1 confirms anchors (canvas, audience, divergence, delivery purpose, mode, visual style); Tier 2 is re-derived from the confirmed anchors and confirms realization choices (page count, palette, typography, icons, formula policy, image usage, AI image path, generation mode, refine-spec). The final `confirm_ui/result.json` is authoritative — if the user changes a field, the generated `design_spec.md` and `spec_lock.md` must use that value, not the AI's original recommendation.

**Image analysis goes through regenerated metadata, not pixels.** When images exist, Strategist and Executor use `analyze_images.py` output (`analysis/image_analysis.csv`) rather than directly opening image files. The CSV is a regenerated view over the live `images/` folder, not a durable cache. Re-running it before image-sensitive decisions is the staleness strategy: user images, extracted images, web images, AI outputs, formulas, and sliced elements all converge into the same measured fact table.

**Per-page spec_lock re-read** is the long-deck anti-drift mechanism — full rationale in § Spec Propagation below.

---

## Execution Discipline

The pipeline is enforced by a 10-rule set in [`SKILL.md` § Global Execution Discipline](../skills/ppt-master/SKILL.md) — that file is authoritative; the rules live there. They look bureaucratic but exist because LLMs default to "let me solve the whole problem in this turn", which is exactly the wrong shape for a serial pipeline where each step's output is bounded, checkpointed, and consumed by the next. The rules collectively close failure modes that surfaced repeatedly in practice: out-of-order execution, AI proxying user design decisions, cross-phase bundling, missing prerequisites, speculative pre-work, sub-agent context loss, page-batching drift, long-deck color/font drift, batch/script-generated SVG drift, and routing ambiguity.

Common stop/continue recovery behavior is authoritative in [`failure-recovery.md`](../skills/ppt-master/workflows/failure-recovery.md); this section does not duplicate that matrix.

Two newer rules are especially important to the architecture. First, Executor page SVGs must be hand-authored by the current main agent, one page at a time; writing a Python/Node/shell generator to emit pages is prohibited because the resulting deck loses cross-page judgment and visual continuity. Second, routing is deterministic: raw PPTX template requests, beautify requests, native enhancement, custom animation, live preview, and other workflow triggers are not turned into open-ended user route questions when the repository already defines the boundary.

The Role Switching Protocol (mandated read of `references/<role>.md` before mode change) serves two reinforcing purposes: forcing fresh role instructions into context overrides drift from the previous mode, and the visible marker in the conversation transcript creates an audit trail so the user can see when the agent moved between modes — critical when reviewing why a particular decision was made.

---

## Spec Propagation: spec_lock.md as Execution Contract

The Strategist phase produces two artifacts that look redundant but serve different masters:

- `design_spec.md` — human-readable narrative; the "why" of the design (target audience, style objective, color rationale, page outline)
- `spec_lock.md` — machine-readable execution contract; the "what" Executor must literally use (HEX colors, exact font family string, icon library choice, image resource list with status)

Why both? Without `spec_lock.md`, the Executor would re-read `design_spec.md` per page during long decks and the LLM's context-compression drift would gradually mutate colors and fonts mid-deck. `spec_lock.md` is the **anti-drift mechanism** — the SKILL.md mandates `read_file <project>/spec_lock.md` before every page, so values stay verbatim across 20+ slides.

The lock is also the per-page routing table. Beyond global colors and typography, it carries `page_rhythm` (`anchor` / `dense` / `breathing`), `page_layouts` (which layout template SVG, if any, a page should inherit), `page_charts` (which chart template should be adapted), image rows with placement/cropping contracts, and the locked `mode` / `visual_style` references that decide which execution rule files are loaded. Empty entries are meaningful signals: no template, no chart, or no image is often a design decision rather than missing data.

`update_spec.py` propagates a post-generation change in two coordinated steps: write the new value to `spec_lock.md`, then literal-replace it across every `svg_output/*.svg`. The tool's scope is deliberately narrow — only `colors.*` (HEX values, case-insensitive replacement) and `typography.font_family` (attribute-scoped). Other fields (font sizes, icons, images, canvas) are intentionally **not supported** because their replacements would need attribute-scoped or semantic awareness whose risk/benefit doesn't justify bulk propagation. For those, edit `spec_lock.md` and re-author the affected pages.

The tool refuses to back up: it relies on git for revert. Adding a backup mechanism would just duplicate git's job and create stale snapshots.

---

## Image Acquisition & Embedding

Several architectural decisions shape this phase:

**Provider-specific config keys, not a generic `IMAGE_API_KEY`.** Every backend takes its own `OPENAI_API_KEY` / `MINIMAX_API_KEY` / etc. and the active one is selected by an explicit `IMAGE_BACKEND=<name>`. A unified `IMAGE_API_KEY` field looks tidier on first glance but causes silent confusion when a user has multiple providers configured at once and isn't sure which one is active — the kind of fault that surfaces only as "image generation gives weird results" with no clear failure point. Forcing per-provider keys makes "which backend am I using" a config-readable fact, not an inference.

**Permissive-by-default license filter, with strict mode for credit-incompatible layouts.** Web image search defaults to allowing CC BY / CC BY-SA images with inline attribution — most slides have visual room for a credit element. `--strict-no-attribution` is the escape hatch for full-bleed hero images and tight composition where there's no place to put a credit without breaking the design. Non-commercial (CC BY-NC*) and no-derivatives (CC BY-ND*) licenses are auto-rejected because the typical PPT Master output is shared in commercial or modified contexts; a permissive default with that floor is the failure mode users actually want.

**Manifest-first acquisition.** In-pipeline AI generation always writes `images/image_prompts.json` and renders the sidecar `image_prompts.md`, even for one image. The positional `image_gen.py "prompt"` form is intentionally limited to one-off debugging because it leaves no manifest/sidecar audit trail. Web acquisition mirrors this with `images/image_queries.json` for multi-row batches and `image_sources.json` for attribution/source tracking.

**One coherent sheet for related spot illustrations.** When a deck needs three or more same-family small illustrations, the plan uses one AI illustration sheet row plus `slice` rows rather than separate generations. `slice_images.py` cuts the sheet into named transparent elements, those derived files join `images/`, and `analyze_images.py` is rerun so Executor sees their real dimensions. This is a style-cohesion rule as much as a cost rule: one sheet forces the small elements to share a visual hand.

**Terminal status before Executor.** Rows that require acquisition must end in `Generated`, `Sourced`, or `Needs-Manual`; `Pending` and `Failed` are not allowed to leak into Executor. A `Needs-Manual` row can continue through SVG generation only as a known placeholder/dependency, and Step 7 re-checks required files before final export.

**External refs during development, two divergent embedding strategies for delivery.** While editing in `svg_output/`, images are external file references — fast iteration, single-source-of-truth replacement. The two delivery artifacts then diverge: `svg_final/` Base64-inlines (a folder of self-contained SVGs that IDE preview, browser, and the preview pptx can all open without missing the bitmap dependencies); native pptx instead copies bitmaps into the PPTX media folder and uses `<a:srcRect>` to express the cropping. The split exists because Base64 inside DrawingML works but bloats file size 3-4×, while file-referenced bitmaps are PowerPoint's native idiom for which `<a:srcRect>` is the canonical crop expression — wrong tool in either direction would cost editability or file size.

**Three-dimensional AI image lock at Strategist time.** When the deck includes AI-generated images, Strategist decides three orthogonal dimensions up front — `rendering` (visual style family: vector-illustration / editorial / 3d-isometric / sketch-notes / …), `palette` (how the deck's HEX values are *used*: proportion + role + temperament), `type` (per-image internal composition: background / hero / framework / comparison / …). The first two are deck-wide and written into `spec_lock.md`; Image_Generator then assembles every per-image prompt from the single locked rendering + palette plus a per-image type, instead of re-deciding style per image. Without this, every image gets its own style drift and the deck reads as a stack of unrelated illustrations. This is the visual-cohesion dual of `spec_lock`'s typography/color anti-drift mechanism, just one level upstream of pixels. Strategist surfaces ≥3 candidate `rendering × palette` combinations to the user during the Eight Confirmations — never auto-locking a single combination silently, because the choice has far-reaching deck-wide consequences and the user's taste is the only oracle for it.

---

## Image-Text Layout: Primary Structures + Modifier Layers

The catalog of *how an image is placed on a slide* (full vocabulary in [`references/image-layout-patterns.md`](../skills/ppt-master/references/image-layout-patterns.md)) splits 72 numbered techniques into two layers that compose freely:

- **Primary Structures** (container layouts / image-as-canvas + native overlay / multi-image compositions) — the page's bones. One or more per page; cross-Primary combinations like *side-by-side comparison + image-as-canvas annotation* are legitimate.
- **Modifier Layers** (non-rectangular clips / overlays & masks / texture / special techniques) — finish. Any number per page, stacked on top of the Primary.

**Why explicit composition, not "one primary per page".** The AI failure mode this catalog fights isn't *over-combining*, it's *under-using*: defaulting every image page to bare `#2 left-third` or `#48 side-by-side` with no Modifier on top, producing visually flat, "AI-default" layouts. The earlier rule "one primary layout per page; modifiers compose" sounded principled but reinforced the under-use — the AI read it as permission to skip the Modifier layer entirely. The current framing flips the encouragement: combining is normal, single-Primary-no-Modifier is the case that needs justification.

**Why the layers are physically separated, not just tagged.** Patterns are reorganized so all Primary structures appear first, then all Modifiers — a Strategist or Executor reading the file once internalizes the two-layer mental model from the table of contents alone. Numbers are stable identifiers (`#38` is still image-as-canvas + annotation cards regardless of where it sits in the file), so existing references across `spec_lock.md`, `design_spec.md §VIII`, executor logs, and historical examples all keep resolving.

**Why composition flows through Strategist's resource list, not just Executor's improvisation.** The `Layout pattern` column in `§VIII Image Resource List` accepts a `#<id> + #<id> ...` expression — Primary id plus optional Modifier ids — so the composition is declared *before* SVG generation, audited by `svg_quality_checker`, and survives session re-entry. Pushing composition onto Executor alone would lose it on context compression in long decks; encoding it in the spec_lock-adjacent resource list makes it a piece of the design contract.

**Why true hard constraints stay upstream.** Cross-cutting technical constraints (`<clipPath>` only on `<image>`, `fill-opacity` instead of `rgba()`, no `<mask>`, alpha-effect routing) live exclusively in [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md). The layout patterns file points at them with one-line references rather than restating — so when a constraint relaxes (e.g., a new DrawingML feature becomes reliable), only one file changes, and a stale duplicate in patterns can't silently keep enforcing the old rule.

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

### Five artifacts, five workflows

The post-processing stage works with five artifacts. Each one serves a workflow that nothing else in the pipeline can replace.

| Artifact | Workflow it serves | Why nothing else replaces it |
| --- | --- | --- |
| `svg_output/` | source of truth, manual editing, `update_spec.py`, `svg_quality_checker.py` | only directory whose contents are authored, not derived |
| `svg_final/` | IDE inline preview (VSCode/Cursor open `.svg` directly), browser open of a single page | `.pptx` is not openable in IDEs; `svg_output/` won't render fully because of external icon / image refs |
| `exports/<name>_<ts>.pptx` (native) | primary deliverable — editable in PowerPoint with DrawingML shapes | only artifact whose shapes the user can resize / recolor / restyle natively in PowerPoint |
| `exports/<name>_<ts>_svg.pptx` (preview, opt-in via `--svg-snapshot`) | cross-platform single-file distribution, multi-page browse, email attachment | self-contained, multi-page, opens in PowerPoint / Keynote / WPS / LibreOffice; an `svg_final/` folder is harder to distribute. Off by default — live preview already provides the SVG visual reference for dev/diagnostic work |
| `backup/<ts>/svg_output/` (always written in default-flow mode) | re-export from frozen SVG sources without re-running the LLM, archival | the only persisted copy of the Executor's raw SVG source after the project has been edited downstream |

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

## Direct OOXML Routes

Not every PPTX-related request should regenerate slides. PPT Master now has direct OOXML routes for cases where the native deck itself is the object being edited.

`template_fill_pptx.py` is a thin CLI wrapper over `scripts/template_fill_pptx/`. Its analyzer extracts a slide library with text slots, tables, charts, and geometry; the fill plan selects source slides, confirms replacements, then the applier clones slides and patches XML parts directly. This route deliberately avoids SVG: a user who supplies a PowerPoint template usually wants those native slide masters, placeholders, tables, and charts to remain PowerPoint-native.

`native_enhance_pptx.py` is the stable entry point for finished-deck enhancement. It delegates to the native narration/timing implementation and patches the PPTX package in place from a project copy: notes, page transitions, recorded narration media, slide timings, and related metadata. The contract is preservation: existing content, layout, and formatting are not regenerated.

These direct routes share some analysis primitives with the main pipeline, especially PPTX intake, but they do not share the SVG authoring or post-processing stages. That separation is intentional: SVG generation is a design synthesis path; direct OOXML editing is a preservation path.

---

## Native PPTX Conversion Internals

**Why per-element dispatch, not whole-file translation.** SVG's hierarchical model maps cleanly onto DrawingML's group / shape / picture types — there's no need for a holistic optimizer that re-plans the slide. Each shape kind gets its own narrow translator, which keeps each translator simple enough to debug and unit-test in isolation. The output quality of a slide is the sum of independent local conversions; that property is fragile under whole-file translation but robust under element dispatch.

**Why Office compatibility mode is on by default.** PowerPoint versions before 2019 can't render SVG natively. The converter generates a per-slide PNG fallback and embeds it alongside the native shapes — newer Office still shows editable shapes, older Office falls back to the PNG. The default-on choice trades a moderate file-size cost for not silently shipping unopenable decks to users on legacy installs; the escape hatch exists for users who know they're on a modern stack and want the smaller file.

---

## Animation & Transition Model

The interesting design choice is the animation **anchor**, not the effect list.

**Why anchor entrance animations on top-level `<g>` groups.** PowerPoint's animation timeline is shape-keyed — each animated object needs a stable shape ID. Animating individual primitives would produce 30+ separately-flying-in atoms per slide (a kinetic mess), while animating only the slide as a whole loses visual storytelling. Top-level groups are the natural granularity: Executor is required to use `<g id="...">` to mark logical content blocks, and these blocks are exactly the units a viewer reads as "one thing arriving" — animation matches the existing logical structure rather than imposing a new one.

**Why page chrome is auto-skipped.** Groups named `background` / `header` / `footer` / `decoration` / `watermark` / `page_number` represent the static slide frame, not content; flying them in would feel jarring (the page itself materializing every transition) and is virtually never what the user wants. Filtering by id-token is brittle in principle but reliable in practice because the token vocabulary is small and the Executor controls naming.

**Why object-level animation uses a sidecar, not SVG attributes.** SVG remains the static visual source of truth. Custom PPTX animation is export policy, so per-object overrides live in optional `animations.json` keyed by slide stem and top-level group id. This avoids polluting SVG with PowerPoint-specific metadata while still letting users tune order, effect, delay, and duration when the default global animation is not enough.

**Why recorded narration drives auto-advance from clip duration.** When narration is embedded, the deck targets video export — and a video has no presenter to click. Setting per-slide auto-advance timings to the audio clip's actual duration produces a deck PowerPoint exports cleanly to MP4 without manual timing work. Picking any other duration source (estimated reading speed, fixed per-slide) breaks the audio-visual sync.

**Why recorded narration rejects on-click object animation.** PowerPoint can record click timings during a real rehearsal, but PPT Master does not synthesize object-level click events. The recorded narration path writes page-level audio and slide auto-advance timings only, so click-driven object reveals would leave the export dependent on extra manual PowerPoint rehearsal. For narrated decks, object entrances must be click-free (`after-previous` or `with-previous`).

---

## Maintenance Boundaries: What Not To Collapse

The tempting simplifications below have explicit costs. Treat them as negative contracts unless the surrounding architecture is deliberately redesigned.

| Do not collapse or add | Why |
|---|---|
| Do not fuzzy-match template names or style phrases to library paths | Step 3 must be deterministic; wrong template selection is harder to recover from than free design |
| Do not treat a raw PPTX template as a Step 3 template | raw PPTX template requests expect native slide cloning/filling, not SVG synthesis |
| Do not merge `template-fill-pptx`, `beautify-pptx`, and `native-enhance-pptx` into one "PPTX optimization" route | their preservation contracts differ: native fill, 1:1 redesign, and direct enhancement are separate operations |
| Do not script-generate batches of Executor SVG pages | cross-page design judgment depends on sequential main-agent authoring |
| Do not make `image_analysis.csv` a durable cache | `images/` is a live folder; facts must be regenerated on use |
| Do not make `svg_final/` the default native PPTX input | `svg_final/` is rewritten for self-contained preview, while native conversion needs high-fidelity `svg_output/` semantics |
| Do not auto-enable object-level entrance animations | page transitions are default; object builds are an explicit export policy |
| Do not default visual review, narration, chart verification, or animation customization into every run | these workflows have narrow triggers and extra dependencies |
| Do not replace `finalize_svg.py` with a file copy | finalization embeds icons/images, flattens special text, and prepares preview artifacts |
| Do not use `analysis/<stem>.slide_library.json` as a second source of chart values in the main pipeline | Markdown owns content values; intake chart/table entries are structural digests unless a direct-PPTX workflow owns them |

---

## Standalone Workflows

The standalone workflow registry is authoritative in [`workflows/index.md`](../skills/ppt-master/workflows/index.md); this section explains why these capabilities stay separate.

Standalone workflows are route definitions, not optional decorations. They exist when a capability has a different contract from the main pipeline or is too sparse to justify loading by default.

| Workflow | Trigger | Contract |
|---|---|---|
| `topic-research` | user provides only a topic and no source material | gather web materials before Step 1 |
| `template-fill-pptx` | raw PPTX template + new material/topic | direct native slide clone/fill; no SVG pipeline |
| `beautify-pptx` | existing PPTX, preserve page count/order/wording 1:1, improve layout | regenerate through SVG pipeline with source identity/content locked |
| `create-template` | build a reusable layout/deck template package | output a directory Step 3 can consume later |
| `create-brand` | extract or define a reusable brand identity | output `templates/brands/<id>/` |
| `resume-execute` | fresh chat after Phase A; user says to continue a project | enter Phase B without rerunning Strategist |
| `refine-spec` | user explicitly wants to review/refine the spec before generation | stop after full spec/lock for revision, then resume |
| `verify-charts` | generated deck contains data charts | calibrate chart geometry before export |
| `customize-animations` | user asks for object-level animation order/effect/timing | create/validate `animations.json` and re-export policy |
| `live-preview` | user asks to preview, click/select, apply annotations, or re-export browser edits | start/re-enter browser preview and apply submitted edits only at the defined point |
| `visual-review` | user explicitly requests per-page visual self-check | rubric pass between Executor and post-processing |
| `generate-audio` | user asks for narration/video export | produce narration audio and recorded timing export path |
| `native-enhance-pptx` | finished PPTX should keep existing content/layout while adding native enhancements | direct OOXML patch route |

Keeping these files separate is a dependency-control decision. The main path loads only the roles and references it actually needs; a narration backend, animation sidecar, chart calibration rubric, or template-import contract is pulled into context only when the trigger fires. That keeps the default deck-generation path tight while making the rarer capabilities deterministic rather than improvised.
