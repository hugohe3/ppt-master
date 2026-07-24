---
description: Generate PPTX route authority for source intake, planning, SVG authoring, quality gates, and native PPTX export.
---

# Generate PPTX Route

> Load only after [`routing.md`](./routing.md) selects Generate PPTX. This file owns the route's Step 1–7 sequence, gates, role switching, and mandatory commands.

**Core Pipeline**: `Initial Materials → [Fact Research] → Create Project → [Template] → Strategist Structured Plan → [Image Acquisition] → Executor Live Preview → Quality Check → Post-processing → Export`

**Generate-specific execution discipline**:

- The current main agent hand-writes every SVG page; never delegate page generation or run a Python, Node, or shell generator over `svg_output/`.
- Initial SVG cadence: P01 → first-page gate → uninterrupted remaining pages → final gate. Grouped batches and mid-run checker calls are forbidden.
- `preset_shape_svg.py` may provide one stdout fragment only after the main agent chooses its semantic role, frame, and paint; it cannot choose layout or write a page.
- Gate checklists are internal verification, not user-facing output. On success, continue automatically and emit at most one compact status line when useful; on failure, report only the blocking items and required recovery.

### SVG Page-Design Boundary

| Scope | Contract |
|---|---|
| Any route that authors or regenerates slide visuals through SVG | `svg_output/` is the complete page-design source: every visible text, image, shape, chart/table fallback, and layout element that should appear on the exported slide is present in that page SVG or referenced by it. |
| Templates, `design_spec.md`, and `spec_lock.md` | Authoring/control inputs. They guide SVG creation but MUST NOT supply visible slide content that is absent from the completed SVG during export. |
| Semantic SVG markers | Minimal rendering-neutral compiler hints used only after existing Layout/Layer/Placeholder/Native metadata has been considered. They never replace native SVG geometry, text, styles, grouping, or asset references. |
| `svg_final/` | Mandatory derived, self-contained SVG visual preview. It may be opened directly or inserted into PowerPoint as an SVG picture, but it is not a supported PPTX source and carries no manual Convert-to-Shape compatibility contract. |
| SVG-to-PPTX export | The only supported generated-PPTX route reads `svg_output/` and maps its content through the project converter to DrawingML/native objects. It compiles only the selected route's explicit structure contract: `flat` keeps represented content Slide-local, while `structured` may place explicitly scoped content in Master/Layout/Slide parts. It MUST NOT infer structure, upgrade `flat`, or invent new visible page content. |
| Native PPTX routes and presentation-behavior stages | Remain outside SVG page-design closure. `template-fill-pptx`, `native-enhance-pptx`, animations, transitions, speaker notes, narration, and package relationships are not required to round-trip through SVG. |

**MUST — page-design closure**: For an SVG-authoring route, inspect the final page SVG to determine what the exported slide looks like. Do not reinterpret “SVG is the page-design language” as “SVG is the complete PPTX package description language.”

## Cross-Cutting Authorities

| Concern | Authority | Contract |
|---|---|---|
| Main pipeline sequencing | This file | Owns Step 1–7 order, gates, role switching, and mandatory commands |
| Artifact ownership | [`artifact-ownership.md`](../references/artifact-ownership.md) | Owns fact channels, source/derived artifact boundaries, and regeneration rules |
| Failure recovery | [`failure-recovery.md`](./governance/failure-recovery.md) | Owns stop/continue policy and resume pointers |
| Confirm UI details | [`confirm_ui.md`](../scripts/docs/confirm_ui.md) | Owns the JSON schema, launcher behavior, staged-result contract, port strategy, and chat fallback details |
| Explicit template workspace | [`apply-template-workspace.md`](./stages/apply-template-workspace.md) | Owns Step 3 validation, installation, and fusion; load only when Step 3's explicit-path trigger fires |

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: The user has provided a topic / desired outcome and any available initial material.

> **Topic-only**: run [`topic-research`](stages/topic-research.md) immediately, then use its factual supplement as source content.

When the user provides non-Markdown content, convert immediately through the
unified dispatcher. It preserves the backend converters' existing behavior,
routes by source type, and writes the standard Markdown plus conversion profile.

| User Provides | Action |
|---------------|--------|
| PDF / DOCX / Office document / XLSX / XLSM / PPTX / EPUB / HTML / LaTeX / RST / web URL | `python3 ${SKILL_DIR}/scripts/source_to_md.py <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]` |
| CSV / TSV | Read directly as plain-text table source |
| Markdown | Read directly |

For PPTX sources, Step 1 converts the deck to Markdown content; after Step 2
`import-sources`, standard PPTX intake is also written to `<project>/analysis/`.
Use `source_to_md.py -t <type>` only when extension detection is ambiguous.
Default local conversion writes Markdown/profile outputs beside each source file.
Use `-o` only when a specific output file/directory is required; with multiple
inputs or directory inputs, `-o` is an output directory. Backend converter details are documented in
[`scripts/docs/conversion.md`](../scripts/docs/conversion.md).

After reading direct and converted content, assess factual sufficiency:

| Material state | Action |
|---|---|
| Requested outcome is supported | Continue Step 2 |
| Required externally verifiable claims remain unsupported | Run [`topic-research`](stages/topic-research.md) for those gaps only |
| Closed corpus / source-only / no external enrichment | Stay within supplied material |

**Sufficiency test**: research only to avoid inventing, omitting, or leaving unsupported a factual claim the requested outcome requires; file presence or length is irrelevant. It gathers facts only. Step 5 acquires Strategist-selected images after final confirmation.

> **Office vector assets (EMF/WMF) from DOCX/PPTX sources**:
> Source conversion extracts embedded Office vector images (.emf/.wmf)
> alongside bitmap images when the source format exposes them. After `import-sources`, these land in `images/`
> together with `image_manifest.json` and are first-class assets in §VIII Image Resource List.
>
> **Do NOT convert EMF/WMF to PNG.** The PPT Master pipeline preserves them as external
> references (`finalize_svg.py` skips them) and `svg_to_pptx.py` embeds them as
> PPTX-native media via `image/x-emf` / `image/x-wmf` MIME — PowerPoint renders them at full vector fidelity.
> Converting via LibreOffice/Inkscape introduces CJK font substitution drift and
> rasterization loss; the original EMF/WMF is always higher fidelity than the converted PNG.
>
> Browser-based live preview cannot render EMF (will show blank) — this is expected;
> the PPTX output is the source of truth.

**✅ Checkpoint — Confirm source content and any factual supplement are ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown file, user-provided text, or requirements described in conversation are all valid).

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

Format options must be named with concrete dimensions. Default: `ppt169` = `1280x720`, `viewBox="0 0 1280 720"`. Other examples: `ppt43` = `1024x768`, `story` = `1080x1920`, `banner` = `1920x1080`. For the full format list, see `references/canvas-formats.md`.

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF/MD/etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...>` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps can reference it directly |

For PPTX sources, `import-sources` automatically runs the standard intake enrichment:

```bash
python3 ${SKILL_DIR}/scripts/pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis
```

For each PPTX it writes `<stem>.identity.json` (canvas, theme palette/fonts, observed usage) and `<stem>.slide_library.json` (text slots, geometry, native tables, native chart caches, SmartArt nodes/connections), and merges that deck's Strategist-facing digest into the single multi-deck index `analysis/source_profile.json` (`decks[]`, one self-contained entry per source deck, with prefixed artifact pointers). In the main generation path these are source facts and recommendation candidates, not replica constraints; the beautify profile and Fill Native PPTX route decide separately which fields become locked constraints.

Multi-deck: several PPTX files may be imported into one main-pipeline project — each gets its own `<stem>.*` artifacts and a deck entry in `source_profile.json`. `source_profile.json` stays the single must-read index (one entry for a one-deck project, several for a combined-source project). Stems must be distinct; re-importing the same stem replaces that deck's entry. The beautify profile and Fill Native PPTX route remain single-deck (1:1 to one chosen source deck) and read that deck's `<stem>.*` artifacts.

**Source ownership boundary**: Use the automatic import mode shown above. Only inputs already under the repository's `projects/` tree move into the target project's `sources/`; every other local path is copied and remains untouched, even if `--move` is supplied. Use `--copy` when a projects-local input must also remain in place. If Step 1 wrote Markdown beside the original sources, pass that source path/directory once. If Step 1 used `-o` to write Markdown elsewhere, pass both the original source path(s)/directory and the Markdown output path(s)/directory. Intermediate artifacts (e.g., `_files/`) are handled automatically.

**✅ Checkpoint — Confirm project structure created successfully, `sources/` contains all source files, converted materials are ready. Proceed to Step 3.**

---

### Step 3: Template Option

🚧 **GATE**: Step 2 complete; project directory structure is ready.

**Default — free design**: Proceed directly to Step 4. Do not query any `*_index.json`, ask about templates, suggest a local template, or fuzzy-match a name from content, brand mentions, or style language.

**Explicit-path trigger only**: Load and run [`apply-template-workspace.md`](./stages/apply-template-workspace.md) only when either condition is true:

- The user supplied one or more explicit workspace-root paths.
- Create Template completed in the current conversation and handed off its exact validated workspace root.

Bare names, style descriptions, brand mentions, vague template intent, and silence do not trigger the runbook. There is no slug lookup or fuzzy path resolution.

**Raw PPTX boundary**: A raw PPTX remains valid source material, but it is not a Step 3 workspace. Raw PPTX plus new content uses [`template-fill-pptx`](./template-fill-pptx.md). To create a reusable workspace, run [`create-template`](./create-template.md), then return with the generated root. Never add Master/Layout/placeholder structure directly to an existing PPTX or SVG project.

> “What templates exist?” is out-of-band Q&A. List indexed workspace paths, then stop; listing does not trigger Step 3. The user must send an explicit path.

**✅ Checkpoint**: Free design selected without loading template details, or the conditional template runbook completed and `<project_path>/templates/` plus any portable assets are ready.

---

### Step 4: Strategist Phase (MANDATORY — cannot be skipped)

🚧 **GATE**: Step 3 complete; default free-design path taken, or (if triggered) template files copied or confirmed in place in the project.

First, read the role core, then only the modules triggered by the current plan:
```
Read references/strategist.md
```

| Deterministic trigger | Additional Strategist reference |
|---|---|
| Step 3 installed an explicit Brand/Layout/Deck workspace | `references/strategist-template.md` |
| The core's proposed Stage 2 `image_usage` contains a source other than `none`, the user supplied an explicit non-`none` image constraint, or formula-worthy content activates formula planning | `references/strategist-image.md` before authoring image renderings, production detail, formula resources, or §VIII |

The core first chooses the proposed Stage 2 source ids. Load the image module before writing Stage 2 whenever that proposal is non-`none`; after confirmation, keep it active only for confirmed non-`none` sources or an active formula plan. A confirmed `none` path with no formula work writes no image rows. Bare template names and style language do not load the template module.

> ⚠️ **Mandatory artifact gates**: after final confirmation, read `templates/design_spec_reference.md` and author the complete `design_spec.md` from scratch; after Gate 1, read `templates/spec_lock_reference.md` and author the complete `spec_lock.md` from the Design Spec plus current context. For a new project, create each finished artifact once—do not materialize a placeholder scaffold and fill it piecemeal. The references own authoring structure, the schemas own machine validation, and semantic projection fidelity remains mandatory. `scaffold-spec` / `scaffold-lock` are optional manual conveniences, not normal Generate steps.

**Artifact ownership**: fact-channel and source/derived artifact boundaries are defined in [`references/artifact-ownership.md`](../references/artifact-ownership.md). This Step uses those ownership rules; it does not redefine them.

**`<project_path>/analysis/` is the project's intermediate-analysis folder: the canonical home for machine-extracted source/asset facts — the PPTX intake bundle (`source_profile.json` index + per-deck `<stem>.identity.json` / `<stem>.slide_library.json`) and `image_analysis.csv`. It holds facts, not design contracts — `design_spec.md` / `spec_lock.md` stay at the project root.** The MUST-read contract covers only the **compact structured data files (`.json` / `.csv`)**; other artifacts that may live under `analysis/` (e.g. a beautify `source_svg_import/` vector reference package) are NOT bulk-read — they are read selectively only when a specific workflow step calls for them. Before the Strategist confirmation stage, Strategist MUST read the auto-extracted fact files already in `analysis/` — currently `source_profile.json` (PPTX intake), when present. This file is the multi-deck index: read it once for the `decks[]` digests (canvas / chart / table / SmartArt entries per source deck), then open a specific deck's `<stem>.identity.json` / `<stem>.slide_library.json` only if you need its full raw facts. Use these entries as **factual source context** (format default + content facts); when several decks are present, synthesize across all of them. The source's **palette / typography / visual identity are a reference, not a constraint**: the main pipeline may inherit them where they fit the content and the confirmed style, or design fresh where they don't — the Strategist's judgment, never an obligation to either keep or discard. (Template-fill preserves the native source design by editing cloned slides directly; beautify defaults to the source identity but still follows the confirmed values; the main pipeline treats source identity as reference only and defaults to fresh design.) (`image_analysis.csv` lands later, at the image-analysis step below, and is the authoritative regenerated image-fact view there — re-derived from the live `images/` folder, not a durable store.)

**Channel ownership — read each fact once from its owning channel.** In the main pipeline the **content contract is the content-type files in `sources/`** — primarily `<stem>.md`, but also any user-supplied content the import archived there: `.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml` (a `metrics.json` or `data.csv` may carry core content — judge by what the file holds). Text, tables, chart data values, and SmartArt node wording come from these (`ppt_to_md` transcribes native charts as Markdown tables and SmartArt nodes as hierarchical bullets). **Do NOT read pipeline sidecars in `sources/` as content**: `*.conversion_profile.json` (conversion audit) and `*_files/image_manifest.json` (asset index) are process metadata — open them only to audit a conversion or resolve assets, never as slide content. Converted-source originals archived in `sources/` (`.pdf` / `.pptx` / `.docx` / `.xlsx` / `.html` / `.epub` / `.tex` / `.rst` / `.ipynb` / `.typ`, etc.) are read via their converted `<stem>.md`, not scanned directly in the main pipeline. The `analysis/` chart / table / diagram entries are a **structural digest** for outline decisions (which slides carried charts, tables, or SmartArt; chart types / series names; SmartArt layout and hierarchy) — not a second copy of the content values; do NOT also pull chart values or SmartArt wording from `<stem>.slide_library.json` in the main pipeline. The `<stem>.slide_library.json` full structured data is owned by the direct-PPTX workflows: template-fill uses it as the native fill contract while preserving SmartArt unchanged; beautify uses it for native chart / table data and SmartArt relationships while keeping all wording from the Markdown.

**Confirmation orchestration**: field meaning and recommendation logic belong to the active Strategist modules; [`confirm_ui.md`](../scripts/docs/confirm_ui.md) owns the JSON schema, server lifecycle, staged-result contract, port behavior, and equivalent chat fallback.

⛔ **BLOCKING**: Unless explicitly delegated, final confirmation is the single user gate. Keep Stage 1/2 handoffs in one turn; after each wait, author the next stage without chat. Author each stage once; submitted values—including blanks or unusual overrides—are authoritative.

**Confirmation ownership and surface**: Only the user confirms. Default Stage 1 is `--daemon --wait`; use chat only by explicit chat-only/delegation or after launch failure/timeout plus a `result.json` re-check. Chat tools do not replace launch. The agent may write recommendations, operate the server, and read state, but MUST NOT call `/api/confirm`, automate submission, synthesize a payload, or write/replace `result.json`. Delegation applies only to this run: show the complete three-stage summary and never fabricate UI results. Silence confirms nothing.

| Stage file (the active unconfirmed stage may be overwritten) | Strategist writes | Completion evidence |
|---|---|---|
| `confirm_ui/recommendations.stage1.json` | Communication contract, `content_divergence`, and canvas only | `status: stage1-confirmed` |
| `confirm_ui/recommendations.stage2.json` | Complete deck solution from the confirmed contract; never skip for a template | `status: stage2-confirmed` |
| `confirm_ui/recommendations.stage3.json` | Production mechanics only: conditional AI path, formula policy, generation mode, refine-spec | `stage: final`, `status: confirmed` |

If the user rejects the current recommendation before confirming it, regenerate by overwriting that same stage file and have the page refresh; do not create revision-suffixed files. This never authorizes one stage file to carry another stage's payload.

1. Create `confirm_ui/recommendations.stage1.json` per the Confirm UI contract, then launch and wait:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon --wait
   ```

2. Read the Stage 1 result. Derive proposed image sources in core and load `strategist-image.md` before constructing Stage 2 when its trigger fires; apply `strategist-template.md` when active. Create `confirm_ui/recommendations.stage2.json` without changing Stage 1, then wait:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage2
   ```

3. Read the Stage 2 result, create `confirm_ui/recommendations.stage3.json` without changing either earlier stage, then perform the final blocking wait:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only
   ```

4. After the final wait returns, read the complete `result.json` exactly once and retain that object through Design Spec authoring and its fidelity audit. Proceed only when it carries `stage: final` and `status: confirmed`. Do not reopen the file during normal lock authoring or downstream execution. On a non-zero wait, this same single read determines whether the persisted result succeeded before using the documented chat fallback. A stage-skip result returns to the missing stage; it is not a browser failure.

5. After final confirmation or chat fallback, always release the server:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --shutdown
   ```

If the user opted out of the page but did not delegate confirmation, skip launch and run the same three stages in chat with explicit user responses. If the user explicitly delegated confirmation, consolidate the same three stages into one AI-authored summary and proceed without `result.json`. Otherwise report the launch URL and keep the staged chat summaries available as fallback.

⛔ **GATE — consume the final state once into the Design Spec, then author the lock from context.** Treat every explicitly present final value as user-owned input and consume it at the semantic type defined by [`strategist.md`](../references/strategist.md) §1 and its field owner. Do not omit or substitute a value, and do not silently strengthen or weaken its type; accepting a recommendation does not turn a Reference or Permission into a Literal requirement. First author and audit the complete `design_spec.md` through [`strategist.md`](../references/strategist.md) §6.2 from the retained final object, including production mechanics, the complete recurring typography-role system, the confirmed image-source boundary, and explicit `image_notes` obligations. Do not reopen `result.json` afterward. Only after that audit passes, author `spec_lock.md` from the completed Design Spec and current project/page/template context: preserve confirmed identity, project every declared recurring typography family and size-anchor role without collapsing it into one default stack, choose reusable execution anchors and routing values, project each placed image's source/pattern/crop policy without reselection, and do not enumerate page-local paint or font-family garnish. Apply `strategist-template.md` §3 for an active template, and never write a separate image palette. If a confirmed requirement cannot be honored, follow [`failure-recovery.md`](governance/failure-recovery.md) instead of silently changing it.

**Conditional — split-mode note** (not a separate confirmation): after listing the Strategist confirmation stage details, append one short line (rendered in the user's language, prefixed with 💡) only when the confirmed mode is `split` or upstream-load signals make a fresh execution context materially useful. Judge those signals from recommended page count, source-material bulk, and substantial `topic-research` web-fetch accumulation:

| Signal read | Line content |
|---|---|
| Heavy (long page count / bulky sources / heavy web-fetch accumulation) | State estimated page count and large source size; recommend switching to [split mode](stages/resume-execute.md) after Step 5 — stop this chat, open a fresh window and input `继续生成 projects/<project_name>` to enter the execution session (SVG generation + export); no response or "continue" = default continuous mode. |
| Explicit `split` selection | Confirm that planning will stop after Step 5 and give the `继续生成 projects/<project_name>` handoff command. |

For the normal/default `continuous` path, print no split-mode reminder and proceed automatically. Confirm UI still exposes the generation-mode toggle and records it in `result.json`; a chat fallback captures the same choice in its confirmation summary without adding a separate reminder.

**Mandatory — spec-refinement note** (not a separate confirmation): after the confirmation details and any conditional split-mode line, you MUST append one short opt-in line (rendered in the user's language, prefixed with 💡) telling the user they may **refine the spec first** — Strategist will produce the full design spec, then stop for review/revision of any part of it before any generation, via the [refine-spec](stages/refine-spec.md) stage. Default is OFF: no request → the spec is written in one go and the pipeline auto-proceeds as usual. Only when the user explicitly asks in chat (e.g. "refine the spec first") or confirms `refine_spec: true` through Confirm UI does the [refine-spec](stages/refine-spec.md) stage take over after the Strategist confirmation stage. This opt-in line remains required output every run; whether to act on it is the user's call. When the Confirm UI is used, this choice also appears as the in-page refine-spec toggle and is captured in `result.json` (`refine_spec`); the chat-summary fallback still prints this line.

**Formula policy**: Stage 3 confirms `mixed`, `render-all`, or `text-only`. When the confirmed policy requires rendering formula-worthy content, load [`strategist-image.md`](../references/strategist-image.md) even if `image_usage` is `none`, and follow its formula-resource contract before filling the planning artifacts. `text-only` creates no formula image rows.

If the user provided images or formula PNGs were rendered, run analysis **before outputting the design spec**. It writes `analysis/image_analysis.csv` — the authoritative regenerated image-fact view in the `analysis/` folder, which MUST be read before authoring §VIII:
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> 🔁 **Image facts are regenerated on change, never maintained as a second store.** `images/` is the live working folder and single source of truth; `analysis/image_analysis.csv` is its regenerated view. Run `analyze_images.py` before the first inventory read, then reuse that CSV while `images/` is unchanged. Re-run after import/acquisition or any user addition, removal, or replacement; if the folder becomes empty, treat the inventory as empty and ignore a stale CSV.

> ⚠️ **Image understanding**: Do not bulk-open images. Strategist uses source context, captions / alt / titles, filenames, user notes, existing resource records, and `image_analysis.csv` first; only a specifically ambiguous asset may be inspected under [`strategist-image.md`](../references/strategist-image.md). Record the result in §VIII. Executor never reopens source images for semantic discovery or reselection.

**Output**:
- `<project_path>/design_spec.md` — complete human-readable design narrative and durable confirmed production state
- `<project_path>/spec_lock.md` — machine-readable communication + stable execution anchors/routing contract; Executor retains it in the active execution context and may inspect an on-demand current-page projection for diagnostics

For a new project, use the reference-first whole-document sequence:

1. Read `templates/design_spec_reference.md`. Compose the complete I–X document in active context from the retained final confirmation, source analysis, and project context; then create `<project_path>/design_spec.md` once with no `[fill]` placeholders or example rows. This is the only normal consumption of the final result.
2. Audit the finished Design Spec field by field against that retained confirmation. Gate 1 must pass before lock authoring.
3. Read `templates/spec_lock_reference.md`. Compose the complete execution projection from the audited Design Spec plus current page/resource/template context; then create `<project_path>/spec_lock.md` once. Do not reopen `result.json` or make an independent design choice.
4. Compare the lock's identity anchors and routing values against the completed Design Spec, then run `python3 ${SKILL_DIR}/scripts/project_manager.py validate <project_path>`.

A retained final state → Design Spec mismatch or Design Spec/context → lock mismatch is blocking even when the standalone Markdown schemas pass. `validate` reads the planning artifacts only; it does not reopen `confirm_ui/result.json` or prove semantic fidelity. Repair the Design Spec from the retained final state; only a fresh recovery turn with no retained state reads persisted final evidence once. Then re-author the affected lock rows from the corrected Design Spec and current context. A resume or refine path edits existing completed files in the same order; it does not replace them with scaffolds.

**✅ Internal checkpoint — Phase deliverables complete**: verify that analysis facts were read before confirmation; final confirmation was consumed once; applicable split/refinement handling is resolved; the complete Design Spec passed Gate 1; the lock was authored from it; and communication plus every §IX `Audience move` were validated. Do not print this checklist. On success, auto-proceed to Image_Generator / Executor under the compact status rule above.

---

### Step 5: Image Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; `<project_path>/design_spec.md` and `<project_path>/spec_lock.md` both exist. If either required artifact is missing, stop before any acquisition or generation and follow [`failure-recovery.md`](governance/failure-recovery.md) §3. Formula rows already have `Acquire Via: formula` and status `Rendered` or `Needs-Manual`.

> **Trigger**: At least one row in the resource list has `Acquire Via: ai`, `web`, and/or `slice`. A prepared-user-only plan contains `user / Existing` rows and skips this entire step; `formula` and `placeholder` rows also do not trigger acquisition. A permitted but unused image source creates no row and does not trigger acquisition. If §VIII omits a source, asset, or page role that `image_notes` explicitly requires, the Design Spec is incomplete; return to Step 4 Gate 1, repair it from the retained final state, and re-author the affected lock anchors from context. Do not reopen `result.json` during this check.

**Failure recovery**: stop/continue behavior for AI/web/slice/image-readiness failures is defined in [`workflows/governance/failure-recovery.md`](governance/failure-recovery.md). This Step keeps the acquisition procedure.

**Always load the common framework**:

```
Read references/image-base.md
```

Then **lazy-load the path-specific reference** for each row that actually needs it:

| Acquire Via | Load reference (only if any such row exists) | Run |
|---|---|---|
| `ai` | `references/image-generator.md` | write `<project_path>/images/image_prompts.json`, then follow `image-generator.md §7 Path Selection` (`image_gen.py --manifest` is **Path A only**) |
| `web` | `references/image-searcher.md` | `python3 ${SKILL_DIR}/scripts/image_search.py ...` (≥2 web rows → `--batch images/image_queries.json`) |
| `slice` | `references/image-generator.md` §4.3 | derived — **after** the parent `ai` sheet row is `Generated`, run `python3 ${SKILL_DIR}/scripts/slice_images.py <project_path>/images/<sheet>.png --grid RxC --names ... --trim --alpha` (see workflow step 2.5) |
| `user` / `formula` / `placeholder` | (skip) | (skip) |

A deck with only `ai` rows never loads `image-searcher.md`; a deck with only `web` rows never loads `image-generator.md`. A mixed deck loads both, processes each row through its own path, and writes both `image_prompts.json` and `image_sources.json`.

> ⚠️ **In-pipeline ai rows MUST use the manifest contract** — even when only 1 ai row exists. Always write `images/image_prompts.json` first and render `image_prompts.md` with `image_gen.py --render-md`. Then execute the confirmed path from `image-generator.md §7`: `image_gen.py --manifest` is **Path A only**; `host-native` is **Path B** and MUST skip `--manifest`; `manual` writes the prompts and stops for external generation. The positional form (`image_gen.py "prompt" ...`) is reserved for **out-of-pipeline one-off testing / single-image fixups** — it skips manifest + sidecar, leaving no audit trail.

> ⚠️ **web path — batch multiple rows**: when ≥2 rows are `Acquire Via: web`, write all queries into `images/image_queries.json` and run `image_search.py --batch` once (concurrent acquisition, status written back), instead of one CLI call per row. A single web row may use the positional single-query form. See [image-searcher.md](../references/image-searcher.md) §5.

> 💡 **ai path — spot illustrations as one sheet**: when the §VIII image resource plan needs ≥3 same-family spot illustrations as decorative accessories, generate **one grid sheet** (a single `ai` sheet row) instead of one row per element, then slice it (workflow step 2.5 below). Choose sheet geometry from intended placement: `1xN` / `Nx1` are useful for extreme portrait / landscape cells, and a designed `MxN` grid is valid when its cell ratio fits the planned elements. The sheet row is generated but not placed; each cut **element row** (`Acquire Via: slice`) is placed and must appear in `spec_lock.md images`. One generation = one coherent style across all pieces. Resource contract + the geometry rules: [image-generator.md](../references/image-generator.md) §4.3.

> ⚠️ **Honor the Design Spec's confirmed image source before running any generation command**: the `ai` generation path (Path A = `image_gen.py` API / Path B = host-native tool / Offline Manual) is **not** auto-only — the production value recorded in `design_spec.md §I` wins. `host-native` forces Path B even when `IMAGE_BACKEND` is configured; `api` forces Path A; `manual` forces offline. Never reopen `result.json` here, and never run `image_gen.py --manifest` when the recorded value is `host-native` or `manual`. Full selection rule: [image-generator.md](../references/image-generator.md) §7 Path Selection.

Workflow:

1. Extract all resource rows from the design spec and group them by `Acquire Via`; rows with `Status: Pending` or `Status: Failed` and `Acquire Via ∈ {ai, web, slice}` must all reach a terminal state before Executor starts
2. Generate prompts (ai rows) and/or run search (web rows) per [image-base.md](../references/image-base.md) §3 dispatch table
2.5. **Slice any spot-illustration sheets (only if `slice` rows exist).** For each generated `ai` **sheet** row, run `slice_images.py` (grid + the element `--names` matching the `slice` rows, `--trim --alpha`) so every element file lands in `images/`; mark each `slice` row `Generated`. A sheet still in `Needs-Manual` cannot be sliced — leave its `slice` rows `Needs-Manual` and surface them at the Step 7 readiness gate. Contract: [image-generator.md](../references/image-generator.md) §4.3.
3. Verify every row reaches a terminal status: `Generated` (ai success / sliced element), `Sourced` (web success), or `Needs-Manual`. `Failed` is not a terminal status: it means the current run did not generate that item, but the item remains retryable. On `auto`, follow the owning fallback chain. On an explicitly confirmed `api` or `host-native` path, retry only that path; if it still fails, mark the row `Needs-Manual` without switching to another automated provider.
4. Re-derive image facts now that web / AI / sliced files are in the folder — `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` — so `analysis/image_analysis.csv` reflects every acquired image **including the sliced elements** (real measured sizes) before the Executor lays them out. Image facts are regenerated on use, never a stale store (see Step 4's image-facts note).

**✅ Internal checkpoint — acquisition complete**: verify conditional AI/web sidecars, all required slice outputs, terminal status for every resource row, and a refreshed `image_analysis.csv`. Do not print this checklist. On success, auto-proceed under the compact status rule above.

**Default — auto-proceed to Step 6.** Only when `design_spec.md §I` records `generation_mode: split`, output the planning-session handoff below and stop this conversation:

  ```markdown
  ## ✅ Planning Session Complete
  - [x] Spec: `design_spec.md`, `spec_lock.md`
  - [x] Resources: `sources/`, `images/`, `templates/`
  - [ ] **Next**: open a fresh chat window and input `继续生成 projects/<project_name>` to enter the execution session via the [`resume-execute`](stages/resume-execute.md) stage.
  ```

> On acquisition failure, do NOT halt — follow the Failure Handling rule in [image-base.md](../references/image-base.md) §5: retry once, then mark the row `Needs-Manual`, report to user, and continue to the checkpoint above.

---

### Step 6: Executor Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete; all prerequisite deliverables are ready.

**Exact page roster**: render `design_spec.md §IX` one-for-one, in order. Any add/drop/merge/split/reorder requires Spec repair/refinement first.

**Page content**: §IX is preferred wording and semantic authority. Use it when it works; adapt it when presentation benefits while preserving intent, facts, and explicit literal requirements. Read sources only to verify requested evidence; return incomplete blocks to Step 4 instead of enriching them during execution.

**Planning context**: follow [`executor-base.md`](../references/executor-base.md) §2.1. Reuse the complete Design Spec and lock in an unchanged, uncompacted context. Fresh/resumed/restarted, compacted/summary-only, or externally/unknown changed execution reads both once and reloads triggered inputs. For a local question, consult the retained lock first, then only the owning Design Spec fragment; do not poll files merely to prove validity.

**Artifact ownership**: `svg_output/` is the author source, `svg_final/` is derived, and image facts come from the regenerated `analysis/image_analysis.csv`; see [`references/artifact-ownership.md`](../references/artifact-ownership.md).

Read the execution references for this deck's locked `mode` + `visual_style` (from `spec_lock.md`):
```
Read references/executor-base.md                  # REQUIRED: flat/shared execution core
Read references/shared-standards-core.md          # REQUIRED: SVG compatibility core
Read references/semantic-svg.md                   # REQUIRED: semantic metadata boundary
Read references/modes/<resolved-id>.md            # one preset id, or each `mode_references` id
Read references/visual-styles/<resolved-id>.md    # one preset id, or each `visual_style_references` id
```

> Read only the five always-on references above plus the conditionally triggered modules below. A preset reads its one locked file. For `mode: custom` or `visual_style: custom`, read every exact file named by the optional `mode_references` / `visual_style_references`, then synthesize those sources under the corresponding behavior. If the reference field is absent, the direction is genuinely novel: read no preset file and follow the behavior directly. Never infer adjacent references or glob `modes/` / `visual-styles/`.

| Deterministic trigger | Additional references |
|---|---|
| `pptx_structure.mode: structured` | `executor-structured.md` + `pptx-structure-interface.md` |
| Any data chart/table, including mini or inset charts and sparklines | `executor-chart.md` |
| Preset pattern or supported native chart/table | `native-data-interface.md` before drawing |
| `spec_lock.md images` or §VIII contains at least one image/formula row, or an active template carries bundled images | `executor-image.md` + `image-layout-patterns.md` + `image-layout-spec.md` + `svg-image-embedding.md` |
| At least one placed image has `Status: Sourced` | `executor-web-image.md` after the image branch |
| The locked style/current page calls for noncanonical or alpha paint, dash/cap/join, tracking/decoration/outline, gradient/filter/glow/shadow, path/transform/clipping, or another constructed effect | `svg-effects.md` before authoring that value or effect |
| A page calls for a literal PowerPoint stock shape | `native-shape-authoring.md` before selecting or emitting that shape |
| All SVG pages and SVG quality gates are complete | `executor-notes.md` before generating speaker notes |

No branch is loaded by analogy. Evaluate these triggers from `spec_lock.md`, §VII/§VIII, the selected style, and the current page plan.

**Design Parameter Confirmation (Mandatory)**: before the first SVG, output key design parameters from the spec (canvas dimensions, color scheme, font plan, body font size). See executor-base.md §2.

**Live Preview Auto-Startup (Mandatory)**: before the first SVG, automatically start the browser editor in live mode and keep it running continuously through Executor + Step 7 export:
```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live --daemon
```
- Start it immediately when Executor begins; `svg_output/` may be empty. Editor opens at the launch-log URL such as `http://127.0.0.1:5050`; if another project already holds it, the launcher **auto-advances to the next free port** — read the actual URL from the launch log and report that.
- Treat the launch URL as a checkpoint value: before writing the first SVG, either report the actual URL from the launcher or state the launch failure explicitly. Do not silently continue while claiming preview is available.
- Run it as a long-running side process/session; do not wait for it to exit before generating SVG pages. Do not wait for user confirmation after startup.
- **Service must keep running** until one of: (a) the user clicks **Exit preview** in the browser, or (b) the user explicitly asks in chat to stop it. Generation continues even if the user closes the editor.
- **Do NOT read or apply submitted annotations during generation.** Users may annotate at any time, but Executor proceeds without touching them. The window to apply annotations opens only after Step 7 completes — see [`workflows/stages/live-preview.md`](stages/live-preview.md).
- The editor also supports **staged direct edits** (text content + SVG element attributes previewed immediately, then written to `svg_output/` only when the user clicks **Apply changes**; `Ctrl+Z` / Undo drops staged edits) alongside annotation; re-export stays chat-driven. Full scope and editor details: see [`workflows/stages/live-preview.md`](stages/live-preview.md) Notes.

**Conditional reference reads**: Follow `executor-structured.md` for template Design Spec/prototypes and `executor-chart.md` for chart SVGs. Read each selected full reference once per valid context; reread only after a known change or context invalidation. Flat routes skip template reads. Summaries and sidecars never replace full SVGs.

> Image facts: trust the latest `analysis/image_analysis.csv` from the Step 4 inventory read or the Step 5 post-acquisition refresh. If `images/` changed since, re-run `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` before layout; if the folder is empty, use no image inventory and ignore a stale CSV.

**Page-context**: use the read-only projector only for the diagnostic/telemetry triggers in Executor §2.1, never as a routine pre-page load.

> ⚠️ **Main-agent only**: SVG generation MUST stay in the current main agent — page design depends on full upstream context. Do NOT delegate to sub-agents.
> ⚠️ **Generation rhythm**: P01 → first-page gate → uninterrupted remaining pages → final gate. After context invalidation, reload under §2.1 before continuing; do not insert batches or mid-run checker calls.

**Visual Construction Phase**: generate SVG pages sequentially, one at a time, in one continuous pass → `<project_path>/svg_output/`

Each completed SVG MUST be a standalone, complete representation of that slide's visible design. Template SVGs and locked planning artifacts may guide construction, but export must not reach back to them to add visible objects omitted from `svg_output/`. Speaker notes, animation, narration, transitions, and direct native-PPTX workflows remain separately owned artifacts/capabilities. When a page actually needs a literal stock shape, load and apply [`native-shape-authoring.md`](../references/native-shape-authoring.md) before drawing it. Diagram relationships remain Shape-first; do not infer a preset from contour similarity.

`template_reuse_scope: mirror|layout` pages MUST start from the complete `page_layouts` SVG, keep inherited visible objects, and preserve root Master/Layout identity plus stable atoms/slots. Strict preserves that reusable contract; under `layout`, the once-loaded Design Spec's `Template Application` may still authorize carrier text/tspan reflow inside unchanged slot bounds. Adaptive uses the current or new Layout key/name already declared by Strategist. If construction proves that fixed atoms or slot topology/bounds must change, stop and return upstream for Strategist to repair the owning plan and lock, validate and read back the affected fragments, then resume; Executor never mutates `spec_lock.md`. `mirror` changes only visible text values while preserving text/tspan topology and attributes. `style` follows the flat paragraph below without structure metadata.

`template_reuse_scope: style`, free-design, and brand-only pages use `pptx_structure.mode: flat`. Draw the complete page directly: keep backgrounds, repeated chrome, headings, text, images, and decoration as ordinary Slide-local SVG content. Do not plan `pptx_masters` / `pptx_layouts` / `page_pptx_layouts`, do not add root Master/Layout identity, and do not add `data-pptx-layer` or `data-pptx-placeholder` metadata. Group logical content normally with top-level `<g id>` elements. Export materializes one clean project-owned Master plus one Blank Layout, applies the locked theme colors/fonts/title-body defaults, removes stock content placeholders and unused built-in Layouts, and retains only the standard date/footer/slide-number capability hooks. It does not promote or deduplicate page content.

Do not duplicate specialized identity with `data-pptx-role`. Add it only to structural page-frame objects whose package, page-number, or animation behavior is not already expressed by `data-pptx-layer`, `data-pptx-placeholder`, or `data-pptx-replace-with`; such an element needs a stable unique `id`. Do not add generic content roles to ordinary titles, body text, cards, KPIs, diagrams, charts, icons, or images. Full contract: [`references/semantic-svg.md`](../references/semantic-svg.md).

**First-page gate (Mandatory)** — after the **first** SVG page, before drawing page 2:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage first-page --json
```
Run the command unfiltered—do not pipe it through `tail`, `head`, `grep`, or another output truncator. Review the complete P01 issue set from that one run before editing. Select any advisory warnings worth addressing, fix all blocking errors and selected warnings in one consolidated edit pass, then perform one verification rerun. Do not rerun merely to reveal the next issue. If verification still fails, treat its complete output as the next batch and repeat the same review → consolidated edit → single verification cycle; never check between individual fixes. If the terminal output itself is truncated, read only the relevant issue arrays from `validation/svg_quality_first_page_report.json`; do not launch another checker run for discovery. After the gate passes, draw P02 through the final page without checker calls.

**Mandatory — read P01 as a method sample, then emit the classification before editing**: the gate validates how the remaining pages will be authored, not only this page.

| Signal | Reading |
|---|---|
| Two or more issues share a category and direction | Method-level bias — resolve it to the authoritative rule before P02; a correction fitted to the observed offset only patches this sample. For text extents that rule is `svg_to_pptx.drawingml.elements.estimate_single_line_text_frame_width(runs)`, with `skills/ppt-master/scripts` on `sys.path` and every run key present — `text`, `font_size`, `font_family`, `font_weight`, `letter_spacing` — since omissions under-measure |
| One isolated issue tied to this page's structure | Page-local — fix and continue |
| A recurring element appears for the first time (page furniture, caption format, section numbering, accent discipline) | It will be copied to every later page — confirm its semantics now |

Emit one line before the consolidated edit:

```
gate-signal: method=<rule resolved, or none> | page-local=<count> | not-exercised=<list>
```

`not-exercised` names what P01 could not test — a cover typically omits multi-line text, columns, charts, image captions, and data objects. Carry every resolved rule forward as arithmetic; P02 through the final page run without further tool calls.

**Quality Check Gate (Mandatory)** — only after every planned SVG exists, BEFORE annotation handling and speaker notes:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage final --json
```
- **MUST**: Before this gate, every chart/table whose Design Spec §IX page block says `Native-ready: yes` already has its own draw-time marker plus JSON metadata. Rows marked `no` and incidental microvisuals remain ordinary SVG. For legacy specs only, a matching §VII value may supply the decision when §IX has no field.
- Run the command unfiltered—do not pipe it through `tail`, `head`, `grep`, or another output truncator. One invocation already scans every page and reports the complete issue set.
- On failure, review all `blocking` errors and all advisory warnings from that run before editing. Choose which warnings merit work, fix every blocking error and the selected warnings in one consolidated edit pass, then perform one verification rerun. If it still fails, its complete output begins the next batch cycle; never run the checker between individual fixes or use repeated invocations to discover one next issue at a time. If terminal output is truncated, extract only `categories.blocking.issues` and, when needed, `categories.introduced.issues` from the report written by that same run.
- Every `warning` is advisory and non-blocking: do not return the page for mandatory modification, do not auto-normalize user-authored compatible syntax, and do not require an acknowledgement/disposition line. Recommendation warnings identify the generated-SVG default; fidelity/quality warnings may be reported when material, but the existing input may ship unchanged. If a condition must be corrected before release, the checker must classify it as an `error`, not a `warning`.
- The same rule applies to structured-template warnings (empty/framing-only Layout, bare Master, duplicate layout keys): they may guide an optional template cleanup, but warnings alone never fail the quality gate. Flat `style`, free-design, and brand-only routes still rely on their existing hard errors for invalid structure metadata or incomplete required locks.
- Run against `svg_output/` (not after `finalize_svg.py` — finalize rewrites SVG and masks violations).
- The JSON report is written to `validation/svg_quality_report.json`. `inherited` prototype diagnostics and `source-import` compatibility losses are informational provenance; only changed/new warnings remain `introduced`, and all release-blocking failures remain `blocking`.
- **Hard rule — token-safe report handling**: On a successful checker run, use the exit status and terminal summary as gate evidence. Do not open, `cat`, or otherwise load the complete JSON report into model context. Read it only for failure investigation, an explicit audit request, or a field absent from stdout; extract only the required field(s).

**Logic Construction Phase**: after the SVG quality gate passes, load [`executor-notes.md`](../references/executor-notes.md), ground each page's narration in all information-bearing content in its final SVG, and generate speaker notes → `<project_path>/notes/total.md`

**✅ Internal checkpoint — execution complete**: verify live preview timing, the P01 method gate, uninterrupted remaining-page generation, consolidated repair of any complete failure set, exact §IX roster coverage, one-frame prose wrapping, a final checker result of 0 errors, and `notes/total.md`. Do not print this checklist. Run the applicable conditional gates below, then proceed to Step 7 under the compact status rule above.

> **Chart pages?** If this deck contains data charts, run the [`verify-charts`](stages/verify-charts.md) quality-gate stage before Step 7 to calibrate coordinates. Skip if no chart pages.

> **Visual self-check (opt-in)?** If the user explicitly asked for a per-page visual re-pass on the SVGs ("跑一下视觉自检 / 视觉回看", "visual review", "check pages visually", etc.), run the [`visual-review`](stages/visual-review.md) quality-gate stage before Step 7. Do NOT run it by default and do NOT recommend it based on inferred model capability or deck size — trigger is user request only.

---

### Step 7: Post-processing & Export

🚧 **GATE**: Step 6 is complete; `svg_output/` contains every final page, `notes/total.md` exists, all required conditional quality gates passed, and the final SVG quality report has 0 errors.

🚧 **Image readiness GATE**: When any required resource row is `Needs-Manual`, every expected file and derived slice output MUST exist under `<project_path>/images/` before Step 7.1. If any file is absent, pause and list the exact filenames. After the files arrive, rerun `analyze_images.py`, replace each dashed placeholder in `svg_output/`, reconcile every `no-crop` container to the measured native ratio, then rerun the final SVG quality check so the gate covers the changed sources.

**Failure recovery**: On a command failure, repair the owning source artifact and resume from that failed sub-step per [`failure-recovery.md`](./governance/failure-recovery.md). Do not restart planning unless its owning source changed.

**Hard rule — strict serial commands**: Run the following commands one at a time. Do not combine them in one code block or shell invocation. Enter the next sub-step only after the current command exits successfully and its success criterion is true.

#### Step 7.1 — Split Speaker Notes

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Success criterion**: Per-slide Markdown files exist under `<project_path>/notes/` and cover every published slide.

#### Step 7.2 — Build the Self-Contained SVG Preview

```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Success criterion**: `<project_path>/svg_final/` contains one self-contained preview SVG for every published slide. This mandatory derived preview does not replace `svg_output/` as the native-export source.

#### Step 7.3 — Export the Native PPTX

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>
```

**Success criterion**: The command exits successfully and produces:

- `exports/<project_name>_<timestamp>.pptx`
- `validation/<project_name>_<timestamp>.report.json` with `passed` or `passed-with-warnings` package/resource postflight status
- `validation/<project_name>_<timestamp>.trace.json` when bare `--conversion-trace` is enabled; an explicit `--conversion-trace <path>` uses that destination instead

The command prints a compact `[POSTFLIGHT]` receipt containing `status`, `quality_gate`, Slide count, warning-category counts, and the PPTX/report paths. Use that receipt as completion evidence and disclose its material warnings to the user. Do not open or `cat` the complete report on routine success; use targeted field extraction only for failure investigation, an explicit audit request, or information absent from the receipt. A failed report or missing PPTX is not success.

## ✅ Generate PPTX Complete

- [x] Image readiness gate passed
- [x] Notes split completed
- [x] `svg_final/` preview completed
- [x] Native PPTX published and postflight report written
- [ ] **Next**: Report the exported PPTX path; run a supporting post-export stage only when its explicit trigger is present
