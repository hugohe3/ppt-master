---
description: Generate PPTX route authority for source intake, planning, SVG authoring, quality gates, and native PPTX export.
---

# Generate PPTX Route

> Load only after [`routing.md`](./routing.md) selects Generate PPTX. This file owns the route's Step 1–7 sequence, gates, role switching, and mandatory commands.

**Core Pipeline**: `Source Document → Create Project → [Template] → Strategist Structured Plan → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export`

**Generate-specific execution discipline**:

- The current main agent hand-writes every SVG page; never delegate page generation or run a Python, Node, or shell generator over `svg_output/`.
- Generate pages sequentially, one page at a time, in one continuous pass; grouped page batches are forbidden.
- Before each page, re-read `<project_path>/spec_lock.md` and apply the current communication, design, resource, rhythm, chart, and conditional template mappings.
- `preset_shape_svg.py` may provide one stdout fragment only after the main agent chooses its semantic role, frame, and paint; it cannot choose layout or write a page.

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
| Confirm UI details | [`confirm_ui.md`](../scripts/docs/confirm_ui.md) | Owns schema, launcher behavior, port strategy, and chat fallback details |
| Explicit template workspace | [`apply-template-workspace.md`](./stages/apply-template-workspace.md) | Owns Step 3 validation, installation, and fusion; load only when Step 3's explicit-path trigger fires |

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: User has provided source material (PDF / DOCX / EPUB / URL / Markdown file / text description / conversation content — any form is acceptable).

> **No source content?** When the user supplies only a topic name or requirements without any file or substantive description, run the [`topic-research`](stages/topic-research.md) intake stage first, then return here with its products as input.

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

**✅ Checkpoint — Confirm source content is ready, proceed to Step 2.**

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
| Has source files (PDF/MD/etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...> --move` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps can reference it directly |

For PPTX sources, `import-sources` automatically runs the standard intake enrichment:

```bash
python3 ${SKILL_DIR}/scripts/pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis
```

For each PPTX it writes `<stem>.identity.json` (canvas, theme palette/fonts, observed usage) and `<stem>.slide_library.json` (text slots, geometry, native tables, native chart caches, SmartArt nodes/connections), and merges that deck's Strategist-facing digest into the single multi-deck index `analysis/source_profile.json` (`decks[]`, one self-contained entry per source deck, with prefixed artifact pointers). In the main generation path these are source facts and recommendation candidates, not replica constraints; the beautify profile and Fill Native PPTX route decide separately which fields become locked constraints.

Multi-deck: several PPTX files may be imported into one main-pipeline project — each gets its own `<stem>.*` artifacts and a deck entry in `source_profile.json`. `source_profile.json` stays the single must-read index (one entry for a one-deck project, several for a combined-source project). Stems must be distinct; re-importing the same stem replaces that deck's entry. The beautify profile and Fill Native PPTX route remain single-deck (1:1 to one chosen source deck) and read that deck's `<stem>.*` artifacts.

> ⚠️ **MUST use `--move`** (not copy): all source files — Step 1's generated Markdown, original PDFs / MDs / images — go into `sources/` via `import-sources --move`. If Step 1 wrote Markdown beside the original sources, pass that source path/directory once. If Step 1 used `-o` to write Markdown elsewhere, pass both the original source path(s)/directory and the Markdown output path(s)/directory. After execution they no longer exist at the original location. Intermediate artifacts (e.g., `_files/`) are handled automatically.

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

First, read the role definition:
```
Read references/strategist.md
```

> ⚠️ **Mandatory gate**: before writing `design_spec.md`, Strategist MUST `read_file templates/design_spec_reference.md` and follow its full I–X section structure. See `strategist.md` Section 1.

**Artifact ownership**: fact-channel and source/derived artifact boundaries are defined in [`references/artifact-ownership.md`](../references/artifact-ownership.md). This Step uses those ownership rules; it does not redefine them.

**`<project_path>/analysis/` is the project's intermediate-analysis folder: the canonical home for machine-extracted source/asset facts — the PPTX intake bundle (`source_profile.json` index + per-deck `<stem>.identity.json` / `<stem>.slide_library.json`) and `image_analysis.csv`. It holds facts, not design contracts — `design_spec.md` / `spec_lock.md` stay at the project root.** The MUST-read contract covers only the **compact structured data files (`.json` / `.csv`)**; other artifacts that may live under `analysis/` (e.g. a beautify `source_svg_import/` vector reference package) are NOT bulk-read — they are read selectively only when a specific workflow step calls for them. Before the Strategist confirmation stage, Strategist MUST read the auto-extracted fact files already in `analysis/` — currently `source_profile.json` (PPTX intake), when present. This file is the multi-deck index: read it once for the `decks[]` digests (canvas / chart / table / SmartArt entries per source deck), then open a specific deck's `<stem>.identity.json` / `<stem>.slide_library.json` only if you need its full raw facts. Use these entries as **factual source context** (format default + content facts); when several decks are present, synthesize across all of them. The source's **palette / typography / visual identity are a reference, not a constraint**: the main pipeline may inherit them where they fit the content and the confirmed style, or design fresh where they don't — the Strategist's judgment, never an obligation to either keep or discard. (Template-fill preserves the native source design by editing cloned slides directly; beautify defaults to the source identity but still follows the confirmed values; the main pipeline treats source identity as reference only and defaults to fresh design.) (`image_analysis.csv` lands later, at the image-analysis step below, and is the authoritative regenerated image-fact view there — re-derived from the live `images/` folder, not a durable store.)

**Channel ownership — read each fact once from its owning channel.** In the main pipeline the **content contract is the content-type files in `sources/`** — primarily `<stem>.md`, but also any user-supplied content the import archived there: `.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml` (a `metrics.json` or `data.csv` may carry core content — judge by what the file holds). Text, tables, chart data values, and SmartArt node wording come from these (`ppt_to_md` transcribes native charts as Markdown tables and SmartArt nodes as hierarchical bullets). **Do NOT read pipeline sidecars in `sources/` as content**: `*.conversion_profile.json` (conversion audit) and `*_files/image_manifest.json` (asset index) are process metadata — open them only to audit a conversion or resolve assets, never as slide content. Converted-source originals archived in `sources/` (`.pdf` / `.pptx` / `.docx` / `.xlsx` / `.html` / `.epub` / `.tex` / `.rst` / `.ipynb` / `.typ`, etc.) are read via their converted `<stem>.md`, not scanned directly in the main pipeline. The `analysis/` chart / table / diagram entries are a **structural digest** for outline decisions (which slides carried charts, tables, or SmartArt; chart types / series names; SmartArt layout and hierarchy) — not a second copy of the content values; do NOT also pull chart values or SmartArt wording from `<stem>.slide_library.json` in the main pipeline. The `<stem>.slide_library.json` full structured data is owned by the direct-PPTX workflows: template-fill uses it as the native fill contract while preserving SmartArt unchanged; beautify uses it for native chart / table data and SmartArt relationships while keeping all wording from the Markdown.

**Strategist confirmation stage** (full template: `templates/design_spec_reference.md`):

⛔ **BLOCKING**: present the Strategist confirmation stage and **wait for explicit user confirmation or modification** before outputting Design Specification & Content Outline. This is the single core confirmation gate — once the final confirmation lands, all subsequent steps proceed automatically. The default Confirm UI delivers the gate in **three stages** (communication contract → complete deck solution → resources / production; see below); the chat fallback mirrors the same staged order.

1. Communication contract — target audience; open-ended `communication_intent` (one or several purposes, with priority / sequence when useful); desired `audience_outcome`; `core_message` / decision ask / action; delivery context; artifact afterlife
2. Source-treatment intent — open-ended `content_divergence`; facts remain sourced at every level
3. Canvas format
4. Complete deck solution — reading mode (JSON compatibility key `delivery_purpose`); narrative mode; page count; visual / template direction; color; icons; typography; image sources and generated-image rendering
5. Production plan — conditional AI-image acquisition path; formula rendering policy; execution mode; optional spec-refinement toggle

**Confirm UI Auto-Launch (Mandatory — default visual confirmation surface)**: by default the Strategist confirmation stage is presented through an interactive local page in **three stages within one browser session**. Stage 1 confirms the scene and communication contract before asking the user to select tools. The AI then authors Stage 2's **complete deck solution once** from the user's actual contract: argument structure, reading density, template use, visual system, and image direction are judged together. After Stage 2 is confirmed, Stage 3 is authored once and asks only how to produce the already-decided solution. A change inside the current page never asks the AI or server to regenerate that stage. Color swatches, live font previews, icon samples, rendering references, and coordinated direction candidates appear where they help judgment; the chat path is the always-valid fallback. [`scripts/docs/confirm_ui.md`](../scripts/docs/confirm_ui.md) owns the schema, server lifecycle, port strategy, and fallback details; this section keeps the orchestration contract. The split:

| Stage | Confirms | Driven by |
|---|---|---|
| **1 — communication contract** | audience · open-ended `communication_intent` (may combine several purposes) · `audience_outcome` · `core_message` / delivery context / artifact afterlife · `content_divergence` (all prose fields may be blank) · canvas | the source + user intent |
| **2 — complete deck solution** (derived once from Stage 1) | reading mode (`delivery_purpose`, PPT only) · narrative `mode` · page count · `visual_style` · conditional template reuse / adherence · color · typography · icons · image usage · generated-image rendering | the confirmed communication contract |
| **3 — resources / production** (derived once from Stage 1 + Stage 2) | conditional AI-image acquisition path · formula policy · generation mode · refine-spec toggle | the confirmed solution |

> **Why three stages.** A presentation may serve several purposes at once (for example, report progress, expose risk, and request a decision), so Stage 1 uses open prose rather than a purpose enum. Every editable Stage-1 prose field is non-blocking: the user may retain, revise, or clear the recommendation, and confirmation makes the field's current value authoritative, including an empty string. Blank means no explicit user constraint; derive downstream defaults from the source and request without writing the old recommendation back into `result.json`. Stage 2 chooses tools only after that contract is known and keeps mutually dependent choices together: `mode` is the argument strategy, template reuse is the inheritance strategy, and reading mode decides how meaning is divided among the page, visuals, and presenter. It therefore drives content grammar, page granularity, density / rhythm, speaker-note burden, and the body baseline; the visual / image fields form the remaining deck system. `delivery_purpose` remains the compatibility key for **reading mode**, not communication purpose. Page count is derived from content volume × audience outcome × reading mode. Generated images inherit the chosen deck color roles directly; the user confirms rendering, not a second image palette. Stage 3 therefore contains production mechanics only, never another aesthetic decision. Each stage is authored once; documented deterministic UI dependencies may update visible values locally, but there is no same-stage AI recomputation.

Steps:

> ⛔ **Steps 2 → 3 → 4 are ONE uninterrupted run — do NOT yield to the user mid-flow.** When an intermediate `--wait` returns, the AI **immediately and autonomously** derives and writes the next stage once in the **same turn**: do **not** summarize, ask a question, report progress, or end the turn in between. The browser is sitting on a "deriving…" spinner polling for the next stage you must write — stopping here strands the page and the user must prod you in chat to finish (a bug, not the intended flow). **Stage-1 and Stage-2 confirmations are intermediate machine handoffs, not stopping points.** The single ⛔ BLOCKING wait is the **final** confirmation at the end of step 4. (Chat-fallback path — only when the page never opened — is the exception: there you do present each stage in chat and wait for a reply.)

1. **Write Stage 1** to `<project_path>/confirm_ui/recommendations.json` with `"stage": "stage1"` and only the communication-contract fields. New recommendations MUST use the canonical `stage` selector. Put only the recommended `canvas` id in `recommend`. Write `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife`, and `content_divergence` as `{ "value": "<free text>" }`. Seed concrete editable recommendations where the source and request support them; all seven prose values may be blank and none blocks confirmation. The submitted current value is the sole truth: preserve a user-cleared field as `""` through every later stage and the final `result.json`; never restore the earlier recommendation. `communication_intent` is deliberately open prose: it may combine several purposes and state their priority or sequence; the nine common paths are prompt examples only and MUST NOT become a checkbox / enum. `content_divergence` asks how closely to follow the source vs how freely to reshape it (blank = balanced; facts stay sourced at every level); it is consumed while authoring `§IX`, recorded in `design_spec.md §I`, and is not written to `spec_lock.md`. A profile may make this field read-only with `{ "value": "...", "locked": true }`; Beautify uses that contract and is the only exception to user editing. Do **not** include reading mode, `mode`, `visual_style`, page count, template, color, typography, icon, or image fields in Stage 1. Set `lang` to the page language (`zh` / `en` / `ja`); visible text matches `lang`, or provide multilingual name / note variants as documented by the Confirm UI.
2. **Launch + wait for Stage 1.** Background launch; the parent returns when the page writes the stage-1 `result.json`. **Long tool timeout — 600000 ms** (the `--wait` ≈590 s budget):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon --wait
   ```
   Page opens at the launch-log URL such as `http://127.0.0.1:5050` — the **same port as the Step 6 live preview** (they never run at once: this page shuts down at the end of Step 4). If 5050 is held, the launcher **auto-advances** (5051, …) — read the actual URL from the launch log and report it. The page does **not** close after Stage 1: it shows a "deriving…" state and polls for Stage 2. **Launch or wait failure is non-fatal**: if it fails or times out (flask missing, port blocked, no GUI / remote / web host), do **NOT** troubleshoot — **on any non-zero exit, re-check `result.json` once** for a fresh `status: stage1-confirmed` before dropping to the chat fallback. **On success (exit 0 with a stage-1 result), do not pause or report — go straight to step 3 in the same turn.**
3. **Derive Stage 2 once from the confirmed communication contract, write it, then wait for the solution handoff — immediately, same turn (the page is polling for it).** Read the stage-1 `result.json` (`status: stage1-confirmed`). Using the user's **actual** contract (not your originals), **overwrite** `recommendations.json` with `"stage": "stage2"` and author the complete deck solution:
   - Recommend PPT-only reading mode through the compatibility key `recommend.delivery_purpose` (`text` / `balanced` / `presentation`) from the confirmed audience, delivery context, and artifact afterlife. `text` makes the page self-contained with complete prose and detail; `balanced` shares meaning between page and presenter; `presentation` uses one idea, concise claims, and visual evidence per page while speech / notes carry explanation. Then recommend one narrative `mode` and page count from source volume × desired audience outcome × reading mode. Reading mode governs content grammar and page granularity as well as the body baseline; it is not a font-size preset. The page applies `reading mode → body baseline → unpinned role sizes` as a deterministic browser-only dependency. This never calls the backend, and a manually edited size is pinned against later reading-mode changes.
   - When Step 3 loaded a deck/layout template, recommend `template_reuse_scope` now: `mirror`, `layout`, or `style`; `mirror` is legal only for `replication_mode: mirror`. Include `template_adherence: strict|adaptive` only for `mirror|layout`; `style` hides it and later writes `pptx_structure.mode: flat`. For a Deck, first compare its application contract—situations, audiences/outcomes, required narrative/page roles, and content policy—with the confirmed Stage-1 contract; do not treat the stored application as truth when the current request differs. Select from scenario fit: literal recurring artifact → consider `mirror`; compatible reusable structure with new content → `layout`; identity only or a contract that needs a different structure → `style`. Omit both fields for free design and brand-only templates.
   - Author `design_directions` with ≥3 coordinated candidates (safe / shifted / bold; honest-shortfall exception unchanged). Each candidate carries one compatible `visual_style`, color object, typography object, icon id, and—when `image_usage` includes `ai`—one generated-image **rendering** object. The page applies a candidate as one coherent starting point and then exposes the component fields for deliberate override. Do not generate Cartesian combinations or random mix-and-match defaults.
   - Color candidates carry background / secondary_bg / primary / accent / secondary_accent / body_text. Typography splits CJK + Latin for heading/body, includes topic-matched sample text, and uses one fixed body baseline per reading mode (`text` 20 / `balanced` 24 / `presentation` 32 on PPT). Font and direction cards change font character while preserving the current reading-mode sizing state. Recommend one or more `image_usage` source ids (`["ai"]`, `["ai","provided"]`, `["web","placeholder"]`, or `["none"]`; `none` is exclusive) and keep mixed-source / page-role guidance in `image_notes`. When AI is included, each direction's `image_strategy` contains rendering / visual / mood only; **never offer or submit a separate image palette**. Image HEX and role behavior come directly from that direction's deck color object. Spot-illustration lean remains rationale, not a field.

   **Stage 2 is never skipped** — an installed template is an input to the decision, not a substitute for deciding how it serves the contract. Never jump `recommendations.json` from `stage1` to `stage3`: the server refuses to render a skipped stage. The still-open page polls, renders Stage 2, and preserves Stage 1. Then attach to the already-running page; if Windows cleaned up the server, `--wait-only` auto-recovers it on the recorded/default port so the browser reconnects:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage2
   ```
   This returns when the page writes the stage-2 `result.json` (`status: stage2-confirmed`). On a non-zero exit, re-check `result.json` once before falling back to chat — except a `stage skip detected` error, which is not a page failure: you wrote a stage out of order; rewrite `recommendations.json` with the stage the error names and re-attach.
4. **Derive Stage 3 once from the confirmed solution, then wait for the final confirmation.** Read the stage-2 `result.json`. **Do not reopen aesthetic choices.** Overwrite `recommendations.json` with `"stage": "stage3"` and recommend only production mechanics: enumerable `formula_policy`; conditional `image_ai_path` when confirmed `image_usage` includes `ai`; `generation_mode`; and `refine_spec`. The page shows the confirmed image-source summary as read-only context. Then attach to the already-running page; `--wait-only` auto-recovers a dead server as above (same 600000 ms budget):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only
   ```
   This is the ⛔ BLOCKING completion: returns when the page writes the final `result.json` (`status: confirmed`, `stage: final`, carrying Stage 1 + Stage 2 + Stage 3 fields). On a non-zero exit, re-check `result.json` once (a `stage skip detected` error means Stage 2 was never confirmed — go back to step 3, not the chat fallback). Confirmed sizes are **already px** (the system is px-only — no pt anywhere, no conversion): write `result.json` `typography.body_size` / `sizes` into `design_spec.md` / `spec_lock.md` / SVG verbatim. `generation_mode: "split"` / `refine_spec: true` are explicit user choices.
5. **Close the confirm page (Mandatory cleanup — every path).** Shut the server down before leaving Step 4 so it cannot keep holding port 5050 (which Step 6 live preview reuses):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --shutdown
   ```
   **Idempotent and required regardless of whether Confirm was clicked**: clicking the final Confirm already shuts the page down (then a no-op); the chat-fallback path leaves it running. Run it after reading the confirmation, before Step 5.

**Always also print each stage's recommendations + URL in chat** as the always-valid fallback. **The chat fallback is staged too**: if the page never opens or a wait times out with no fresh result, present Stage 1 as open communication questions (the common purposes are examples, never a numbered pick-list) → get confirmation → derive and present Stage 2 → get confirmation → derive and present Stage 3 → get confirmation → take those values. Either path converges.

**Honoring the confirmation (result.json is authoritative — Mandatory)**: the confirmed values **override your own recommendations** when you write `design_spec.md` / `spec_lock.md`. A user who changed any field changed it on purpose. In particular, map `image_usage` to §VIII `Acquire Via` (its value names differ from §h options — translate). `image_usage` may be either a legacy single string or a Confirm UI multi-select array; for arrays, apply every selected source. `image_notes`, when present, is a user-authored image intent note that Strategist must honor while assigning per-page §VIII rows:

For a confirmed template route, map `template_reuse_scope` mechanically: `style` → `pptx_structure.mode: flat` and omit `template_adherence`, `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, and `page_layouts`; `layout` / `mirror` → `mode: structured`, retain the confirmed `template_adherence`, and write the complete mappings. Never infer mirror behavior from the template workspace's `replication_mode` alone—the confirmed reuse scope is the downstream execution authority.

| `result.json.image_usage` | §VIII `Acquire Via` | h.5 + Step 5 generation |
|---|---|---|
| `ai` | `ai` rows | Run h.5 (lock rendering; inherit deck colors); Step 5 generates |
| `web` | `web` rows | None |
| `provided` | **`user`** rows | None — never generate |
| `placeholder` | `placeholder` rows | None |
| `none` | no image rows (§h option A) | None |
| Legacy custom prose | Infer the intended rows from the prose | Run h.5 only if the prose includes AI |

When the confirmed `image_usage` does not include `ai` (and no legacy custom prose includes AI), do **NOT** run h.5, do **NOT** write `ai` rows, and do **NOT** generate images in Step 5 — regardless of what you recommended. `none` is exclusive: if confirmed, write no §VIII image rows. The same "confirmed value wins" rule applies to every field (color → §III, typography → §IV, etc.).

**Small spot illustrations are a Strategist judgment, not a confirmation field.** The user chooses image *source* through `image_usage`; whether the deck leans into decorative illustrations is anchored by the locked `visual_style`'s **illustration propensity** (`core` / `supportive` / `sparse`), expressed only in the `image_notes` rationale — never a new confirmation control. An explicit user request to use or skip illustrations overrides that default either way; `image_usage: none` still wins (write no illustration rows); and source still comes from `image_usage` — a `core` style does not silently generate AI spots when the user did not pick AI. They are ordinary §VIII image rows (`Type: Illustration` / `Illustration Sheet`) using normal `Acquire Via` values. If the plan needs ≥3 same-family AI spot illustrations, use the `ai` Illustration Sheet + `slice` workflow by default; do not generate one AI image per spot. Full rule + precedence: [`references/strategist.md`](../references/strategist.md) §h. Use them on suitable pages and omit them where they would weaken clarity.

**One authored recommendation per stage; final visible state wins (Mandatory).** Author each stage exactly once. A user edit inside Stage 2 MUST NOT trigger AI / backend re-recommendation, and confirmation MUST NOT be followed by a hidden repair pass that changes any displayed field. The page may apply only documented deterministic local dependencies: reading mode sets the default body baseline, body sets unpinned role sizes, and manual size edits pin those values. Font / direction changes preserve the current sizing state. No other advanced override silently rewrites a sibling choice.

Writing `design_spec.md` / `spec_lock.md` and later pages is **consumption of the confirmed state**, not another confirmation-stage calculation. Preserve every confirmed field verbatim and use it as an execution constraint:

| Confirmed anchor | Consume it in |
|---|---|
| `communication_intent` / `audience_outcome` / `core_message` | outline obligations, argument emphasis, and audience moves |
| `delivery_context` / `artifact_afterlife` | page-vs-presenter information load, standalone completeness, notes / citation depth, and hand-off structure |
| `visual_style` (§d Layer 2) | layout treatment, shape language, and visual rhythm while preserving the separately confirmed color / icon / typography values |
| `mode` (§d Layer 1) | outline structure and register (§IX) |
| `delivery_purpose` compatibility key (reading mode, §g) | content grammar, page granularity, notes burden, and per-page density / rhythm (§6.1); use the already-confirmed body / role sizes verbatim |
| `audience` (§c) | tone, evidence depth, and outline emphasis (§IX) |
| `color` HEX (§e) | exact deck roles and AI prompt color-role instructions; never invent or restore an image-palette choice |

If a deliberately mixed set of advanced overrides is unusual, honor it rather than silently “fixing” it. Canvas remains the explicit exception only in the sense that changing canvas does not rescale font sizes (see strategist §g); it still does not trigger a second stage calculation.

**Opt-out**: if the user has said they don't want the page (e.g. "不要网页" / "just confirm in chat" / "纯聊天确认"), skip the launch entirely (step 2) and present the Strategist confirmation stage in chat as before — steps 1, 3, 4 still apply (recommendations summary in chat; wait; take chat values).

The page is a **confirmation surface only** — Strategist still authors every recommendation; the page never generates content.

**Mandatory — split-mode note** (not a separate confirmation): after listing the Strategist confirmation stage details, you MUST append exactly one short line (rendered in the user's language, prefixed with 💡) about generation mode. Pick the variant by qualitative read of upstream-load signals — recommended page count, source-material bulk, whether `topic-research` ran with substantial web-fetch accumulation:

| Signal read | Line content |
|---|---|
| Heavy (long page count / bulky sources / heavy web-fetch accumulation) | State estimated page count and large source size; recommend switching to [split mode](stages/resume-execute.md) after Step 5 — stop this chat, open a fresh window and input `继续生成 projects/<project_name>` to enter the execution session (SVG generation + export); no response or "continue" = default continuous mode. |
| Normal (default) | State scale is moderate, default continuous mode generates in one go; if mid-way window switch is desired, input `继续生成 projects/<project_name>` after Step 5 to switch to [split mode](stages/resume-execute.md). |

This line is required output every run — the user must always see the mode choice exists. Whether to act on it is the user's call. When the Confirm UI is used, this choice also appears as the in-page generation-mode toggle and is captured in `result.json` (`generation_mode`); the chat-summary fallback still prints this line.

**Mandatory — spec-refinement note** (not a separate confirmation): after the split-mode line, you MUST append one short opt-in line (rendered in the user's language, prefixed with 💡) telling the user they may **refine the spec first** — Strategist will produce the full design spec, then stop for review/revision of any part of it before any generation, via the [refine-spec](stages/refine-spec.md) stage. Default is OFF: no request → the spec is written in one go and the pipeline auto-proceeds as usual. Only when the user explicitly asks in chat (e.g. "refine the spec first") or confirms `refine_spec: true` through Confirm UI does the [refine-spec](stages/refine-spec.md) stage take over after the Strategist confirmation stage. This line, like the split-mode line, is required output every run — the user must see the choice exists; whether to act on it is theirs. When the Confirm UI is used, this choice also appears as the in-page refine-spec toggle and is captured in `result.json` (`refine_spec`); the chat-summary fallback still prints this line.

**Formula rendering policy lives inside item 7 (Typography plan)**:

| Policy | Behavior |
|---|---|
| `mixed` (default) | Strategist renders complex formula-worthy expressions as PNG assets; simple inline expressions remain editable text / Unicode |
| `render-all` | Strategist renders every formula-worthy expression as PNG assets |
| `text-only` | No formula rendering; formulas remain editable text / Unicode |

After the Strategist confirmation stage is approved and **before outputting `design_spec.md` / `spec_lock.md`**, if the confirmed formula policy is `mixed` or `render-all` and the content contains formula-worthy expressions, Strategist MUST:

1. Identify explicit LaTeX and any source expressions that should be faithfully structured as formulas.
2. Write `<project_path>/images/formula_manifest.json` with only the formulas selected for rendering.
3. Run:
   ```bash
   python3 ${SKILL_DIR}/scripts/latex_render.py <project_path>
   ```
4. Include each formula as an `Acquire Via: formula`, `Type: Latex Formula` row in `design_spec.md §VIII Image Resource List`: use `Status: Rendered` when the PNG exists, or `Status: Needs-Manual` after provider exhaustion. List every formula in `spec_lock.md images` with `| no-crop`.

The formula renderer uses a provider fallback chain by default: `codecogs,quicklatex,mathpad,wikimedia`. The first three are color-aware; Wikimedia is an availability fallback. If every provider fails for a selected formula, report its manifest item, LaTeX source, target filename, and provider errors; mark only that row `Needs-Manual` and continue without claiming `Rendered`. The user may supply the exact target PNG before the Step 7 image-readiness gate or change the formula policy. Formula PNGs are transparent by default: manifest `background` is the temporary render matte and transparency-removal reference, not a retained final background unless `transparent: false` is set for that item. Do not scan `spec_lock.md` for `$...$` or `$$...$$`. Dollar-delimited math in source material is only a signal for Strategist; the renderer consumes the explicit manifest.

If the user provided images or formula PNGs were rendered, run analysis **before outputting the design spec**. It writes `analysis/image_analysis.csv` — the authoritative regenerated image-fact view in the `analysis/` folder, which MUST be read before authoring §VIII:
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> 🔁 **Image facts are regenerated on demand, never a durable store.** `images/` is a live working folder — pictures are extracted from the source at import, the user may drop or replace files at any time, and Step 5 writes web/AI images into it. The single source of truth is therefore the **current contents of `images/`**, and `analysis/image_analysis.csv` is a *regenerated view* of it, not a fact to keep in sync. Re-run `analyze_images.py <project_path>/images` immediately **before any step that reads image facts** so the view reflects the live folder: before the §h image-usage recommendation (see [strategist.md](../references/strategist.md) §h), here before authoring §VIII, after Step 5 acquisition (so web/AI files join the view), and again any time the user says they added or replaced images. This is the staleness strategy — re-derive on use, no cache to invalidate.

> ⚠️ **Image handling**: NEVER directly read / open / view image files (`.jpg`, `.png`, etc.). All image info comes from `analyze_images.py` output (`analysis/image_analysis.csv`) or the Design Spec's Image Resource List.

**Output**:
- `<project_path>/design_spec.md` — human-readable design narrative
- `<project_path>/spec_lock.md` — machine-readable communication + execution contract (skeleton: `templates/spec_lock_reference.md`); Executor re-reads before every page

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:
```markdown
## ✅ Strategist Phase Complete
- [x] Read the auto-extracted facts already in `analysis/` (e.g. `source_profile.json`) before the Strategist confirmation stage
- [x] Strategist confirmation stage completed (user confirmed via Confirm UI `result.json` or chat fallback)
- [x] Split-mode note appended below the confirmation fields (heavy or normal variant)
- [x] Spec-refinement opt-in line appended (default OFF; only the user's explicit request enters the refine-spec stage)
- [x] Design Specification & Content Outline generated
- [x] Execution lock (spec_lock.md) generated
- [x] Communication trace validated: `spec_lock.md ## communication` contains all six contract key lines (optional values may be blank), and every `design_spec.md §IX` Slide block has an `Audience move`
- [ ] **Next**: Auto-proceed to [Image_Generator / Executor] phase
```

---

### Step 5: Image Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; `<project_path>/design_spec.md` and `<project_path>/spec_lock.md` both exist. If either required artifact is missing, stop before any acquisition or generation and follow [`failure-recovery.md`](governance/failure-recovery.md) §3. Formula rows already have `Acquire Via: formula` and status `Rendered` or `Needs-Manual`.

> **Trigger**: At least one row in the resource list has `Acquire Via: ai`, `web`, and/or `slice`. If every row is `user`, `formula`, or `placeholder`, skip to Step 6.

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

> ⚠️ **Honor the confirmed image source before running any generation command**: the `ai` generation path (Path A = `image_gen.py` API / Path B = host-native tool / Offline Manual) is **not** auto-only — a confirmed choice other than `auto` wins, whether it came from chat (canonical) or, when the page was used, `result.json.image_ai_path`. `host-native` forces Path B even when `IMAGE_BACKEND` is configured; `api` forces Path A; `manual` forces offline. Never run `image_gen.py --manifest` when the confirmed value is `host-native` or `manual`. Full selection rule: [image-generator.md](../references/image-generator.md) §7 Path Selection.

Workflow:

1. Extract all resource rows from the design spec and group them by `Acquire Via`; rows with `Status: Pending` or `Status: Failed` and `Acquire Via ∈ {ai, web, slice}` must all reach a terminal state before Executor starts
2. Generate prompts (ai rows) and/or run search (web rows) per [image-base.md](../references/image-base.md) §3 dispatch table
2.5. **Slice any spot-illustration sheets (only if `slice` rows exist).** For each generated `ai` **sheet** row, run `slice_images.py` (grid + the element `--names` matching the `slice` rows, `--trim --alpha`) so every element file lands in `images/`; mark each `slice` row `Generated`. A sheet still in `Needs-Manual` cannot be sliced — leave its `slice` rows `Needs-Manual` and surface them at the Step 7 readiness gate. Contract: [image-generator.md](../references/image-generator.md) §4.3.
3. Verify every row reaches a terminal status: `Generated` (ai success / sliced element), `Sourced` (web success), or `Needs-Manual`. `Failed` is not a terminal status: it means the current run did not generate that item, but the item remains retryable. On `auto`, follow the owning fallback chain. On an explicitly confirmed `api` or `host-native` path, retry only that path; if it still fails, mark the row `Needs-Manual` without switching to another automated provider.
4. Re-derive image facts now that web / AI / sliced files are in the folder — `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` — so `analysis/image_analysis.csv` reflects every acquired image **including the sliced elements** (real measured sizes) before the Executor lays them out. Image facts are regenerated on use, never a stale store (see Step 4's image-facts note).

**✅ Checkpoint — Confirm acquisition attempted for every row**:
```markdown
## ✅ Image Acquisition Phase Complete
- [x] image_prompts.json created (when any ai rows processed)
- [x] image_prompts.md sidecar rendered (when any ai rows processed)
- [x] image_sources.json created (when any web rows processed)
- [x] Spot-illustration sheets sliced (when any `slice` rows exist); every element file present in `images/` and listed in `spec_lock.md images`
- [x] Each row: status is `Generated` / `Sourced` / `Needs-Manual` (no `Pending` or `Failed` remaining)
- [x] analyze_images.py re-run so image_analysis.csv covers the acquired web / AI / sliced images
```

**Default — auto-proceed to Step 6.** Only when the user's Step 4 response explicitly opted into split mode (in chat or via Confirm UI `result.json` with `generation_mode: "split"`), output the planning-session handoff below and stop this conversation:

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

**Artifact ownership**: `svg_output/` is the author source, `svg_final/` is derived, and image facts come from the regenerated `analysis/image_analysis.csv`; see [`references/artifact-ownership.md`](../references/artifact-ownership.md).

Read the execution references for this deck's locked `mode` + `visual_style` (from `spec_lock.md`):
```
Read references/executor-base.md                  # REQUIRED: common guidelines
Read references/shared-standards.md               # REQUIRED: SVG/PPT technical constraints
Read references/native-shape-authoring.md         # REQUIRED: stock-shape selection and fragment helper contract
Read references/modes/<locked-mode>.md            # narrative skeleton (spec_lock.md `mode`)
Read references/visual-styles/<locked-style>.md   # aesthetic (spec_lock.md `visual_style`)
```

> Read executor-base + shared-standards + native-shape-authoring + the one locked mode file + the one locked visual-style file. For `mode: custom` or `visual_style: custom`, skip that preset file and follow `mode_behavior` / `visual_style_behavior` from `spec_lock.md` instead. Never glob `modes/` or `visual-styles/`.

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

**Pre-generation Template Read (Mandatory)**: first read `templates/template_execution_manifest.json` when present. It is the compact prototype roster and points each prototype to one `text_slots_path`. Use the roster to select prototypes; before each mirror page, read that prototype's text-slot sidecar and complete `templates/<basename>.svg`. Layout reuse reads the selected complete SVG but does not apply mirror-only text topology restrictions. When the manifest or selected sidecar is unavailable, batch-read every distinct layout SVG referenced in `spec_lock.page_layouts` once before the first page and apply the full-SVG mirror/layout rules. In all cases, batch-read every distinct chart SVG referenced in `spec_lock.page_charts` (plus any §VII backup charts) once up front. Do not substitute a manifest or sidecar for the selected full prototype. See executor-base.md §1.0.

> Image facts: trust the `analysis/image_analysis.csv` regenerated at the end of Step 5. If `images/` changed since (the user swapped or added files), re-run `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` before laying images out — facts are re-derived on use, never a stale store (Step 4 image-facts note).

**Per-page spec_lock re-read (Mandatory)**: before **each** SVG page, `read_file <project_path>/spec_lock.md`; check the global `communication` contract, including `consumption_mode`, against the current §IX `Core message` + `Audience move`, and use only the lock's colors / fonts / icons / images, plus `pptx_structure.mode`, `template_reuse_scope`, and the per-page `page_rhythm` / `page_charts` lookups. Read `page_layouts` / `page_pptx_layouts` / `pptx_masters` / `pptx_layouts` only on a structured `template_reuse_scope: mirror|layout` route; they are absent in flat `style`, free-design, and brand-only projects. Resists purpose and design drift on long decks. See executor-base.md §2.1.

> ⚠️ **Main-agent only**: SVG generation MUST stay in the current main agent — page design depends on full upstream context. Do NOT delegate to sub-agents.
> ⚠️ **Generation rhythm**: generate pages sequentially, one at a time, in the same continuous context. Do NOT batch (e.g., 5 per group).

**Visual Construction Phase**: generate SVG pages sequentially, one at a time, in one continuous pass → `<project_path>/svg_output/`

Each completed SVG MUST be a standalone, complete representation of that slide's visible design. Template SVGs and locked planning artifacts may guide construction, but export must not reach back to them to add visible objects omitted from `svg_output/`. Speaker notes, animation, narration, transitions, and direct native-PPTX workflows remain separately owned artifacts/capabilities. Before drawing a literal stock shape, apply [`native-shape-authoring.md`](../references/native-shape-authoring.md): use the stdout-only helper when one PowerPoint preset exactly matches, keep basic SVG primitives for rect/round-rect/ellipse, and keep free SVG for custom semantics. Diagram relationships are Shape-first: use ordinary line/path shapes with registered arrow markers for thin edges and ordinary shape presets for solid block arrows; do not default to connector-family presets or author attachment metadata. Never infer a preset from contour similarity.

`template_reuse_scope: mirror|layout` pages MUST start from the complete `page_layouts` SVG, keep all inherited visible objects in `svg_output/`, and preserve the locked root Master/Layout identity plus stable atomic Master/Layout and slot ids. Strict keeps the prototype structure unchanged. Adaptive keeps its Master contract and, when Layout atoms or slot topology/bounds genuinely evolve, assigns a new key/name and updates `spec_lock.md` immediately. `layout` pages may reflow and re-skin to the project lock; `mirror` pages preserve literal visuals and may change only visible `<text>` / `<tspan>` values while keeping text/tspan count, order, nesting, and every attribute unchanged. `template_reuse_scope: style` follows the flat free-design paragraph below and does not inherit template structure metadata.

`template_reuse_scope: style`, free-design, and brand-only pages use `pptx_structure.mode: flat`. Draw the complete page directly: keep backgrounds, repeated chrome, headings, text, images, and decoration as ordinary Slide-local SVG content. Do not plan `pptx_masters` / `pptx_layouts` / `page_pptx_layouts`, do not add root Master/Layout identity, and do not add `data-pptx-layer` or `data-pptx-placeholder` metadata. Group logical content normally with top-level `<g id>` elements. Export materializes one clean project-owned Master plus one Blank Layout, applies the locked theme colors/fonts/title-body defaults, removes stock content placeholders and unused built-in Layouts, and retains only the standard date/footer/slide-number capability hooks. It does not promote or deduplicate page content.

Do not duplicate specialized identity with `data-pptx-role`. Add it only to structural page-frame objects whose package, page-number, or animation behavior is not already expressed by `data-pptx-layer`, `data-pptx-placeholder`, or `data-pptx-replace-with`; such an element needs a stable unique `id`. Do not add generic content roles to ordinary titles, body text, cards, KPIs, diagrams, charts, icons, or images. Full contract: [`references/semantic-svg.md`](../references/semantic-svg.md).

**First-page gate (Mandatory)** — after the **first** SVG page, before drawing page 2:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage first-page
```
Fix every `error` on page 1 first — structural violations are systematic, and a first-page error repeated deck-wide costs a whole-deck rewrite.

**Quality Check Gate (Mandatory)** — after all SVGs, BEFORE annotation handling and speaker notes:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage final --json
```
- Any `error` (banned/unsupported SVG features, invalid values, unresolved references, viewBox mismatch, etc.) MUST be fixed before proceeding — return to Visual Construction, regenerate that page, re-run check.
- Every `warning` is advisory and non-blocking: do not return the page for mandatory modification, do not auto-normalize user-authored compatible syntax, and do not require an acknowledgement/disposition line. Recommendation warnings identify the generated-SVG default; fidelity/quality warnings may be reported when material, but the existing input may ship unchanged. If a condition must be corrected before release, the checker must classify it as an `error`, not a `warning`.
- The same rule applies to structured-template warnings (empty/framing-only Layout, bare Master, duplicate layout keys): they may guide an optional template cleanup, but warnings alone never fail the quality gate. Flat `style`, free-design, and brand-only routes still rely on their existing hard errors for invalid structure metadata or incomplete required locks.
- Run against `svg_output/` (not after `finalize_svg.py` — finalize rewrites SVG and masks violations).
- The JSON report is written to `exports/svg_quality_report.json`. `inherited` prototype diagnostics and `source-import` compatibility losses are informational provenance; only changed/new warnings remain `introduced`, and all release-blocking failures remain `blocking`.

**Logic Construction Phase**: generate speaker notes → `<project_path>/notes/total.md`

**✅ Checkpoint — Confirm all SVGs and notes are fully generated and quality-checked. Run the applicable conditional gates below, then proceed to Step 7**:
```markdown
## ✅ Executor Phase Complete
- [x] Live preview started before the first SVG and kept available at the reported URL
- [x] First-page gate run after page 1 (errors fixed before page 2)
- [x] All SVGs generated to svg_output/
- [x] svg_quality_checker.py passed (0 errors)
- [x] Speaker notes generated at notes/total.md
```

> **Chart pages?** If this deck contains data charts (bar / line / pie / radar / etc.), run the [`verify-charts`](stages/verify-charts.md) quality-gate stage before Step 7 to calibrate coordinates. AI models routinely introduce 10–50 px errors when mapping data to pixel positions; verify-charts eliminates that class of error. Skip if no chart pages.

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

**Success criterion**: The command exits successfully and publishes:

- `exports/<project_name>_<timestamp>.pptx`
- `exports/<project_name>_<timestamp>.report.json` with `passed` or `passed-with-warnings` package/resource postflight status

Disclose material postflight warnings to the user. A failed report or missing PPTX is not success.

## ✅ Generate PPTX Complete

- [x] Image readiness gate passed
- [x] Notes split completed
- [x] `svg_final/` preview completed
- [x] Native PPTX and postflight report published
- [ ] **Next**: Report the exported PPTX path; run a supporting post-export stage only when its explicit trigger is present
