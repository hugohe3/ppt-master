---
description: Default Generate PPTX authority for source intake, planning, SVG authoring, quality gates, and native PPTX export.
---

# Generate PPTX Route

> Load only after [`routing.md`](./routing.md) selects Default Generate or its
> Beautify profile. This file owns that runtime's Step 1–7 sequence, gates, role
> switching, and mandatory commands. Explicit Quick loads its own profile instead.

**Hard rule — runtime paths**: Resolve every linked or abbreviated package path
below from the entry-time `SKILL_DIR` anchor and expand it inside each tool
call. Never change CWD or inherit a prior shell working directory.

**Default Core Pipeline**: `Initial Materials → [Fact Research] → Create Project → Template Candidate Preparation → Stage-1 Communication + Template Confirmation → [Template Installation] → Stage-2 Solution → [Image Acquisition] → Executor Live Preview → Quality Check → Post-processing → Export`

**Generate-specific execution discipline**:

- The current main agent hand-writes every SVG page; never delegate page generation or run a Python, Node, or shell generator over `svg_output/`.
- Initial SVG cadence: P01 → first-page gate → remaining pages (one page gate per first-exercised `not-exercised` item) → final gate. Batches and other mid-run checker calls are forbidden.
- `preset_shape_svg.py` and `shape_boolean_svg.py` may provide only their documented stdout fragment(s) after the main agent chooses the object's role, operands, paint, and z-order; neither helper chooses layout or writes a page.
- Gate checklists are internal verification, not user-facing output. On success, continue automatically and emit at most one compact status line when useful; on failure, report only the blocking items and required recovery.

**Profile boundary**: Explicit Quick is selected before runtime authority
loading and never enters this file. Beautify enters this file only when its
request does not explicitly select Quick.

### SVG Page-Design Boundary

`svg_output/` is the complete page-design source for every SVG-authoring route: every visible element of the exported slide is present in the page SVG or referenced by it, and templates, `design_spec.md`, and `spec_lock.md` never supply visible content at export ([`shared-standards-core.md`](../references/shared-standards-core.md) §4.0). Export compiles only the selected route's explicit structure contract (`flat` keeps content Slide-local; `structured` places explicitly scoped content in Master/Layout/Slide parts) and never infers structure or invents content. `svg_final/` is an optional derived preview that release export never reads; Quick skips it. Speaker notes, animations, narration, and Edit Native PPTX stay outside this closure.

## Cross-Cutting Authorities

| Concern | Authority | Contract |
|---|---|---|
| Main pipeline sequencing | This file | Owns Step 1–7 order, gates, role switching, and mandatory commands |
| Artifact ownership | [`artifact-ownership.md`](../references/artifact-ownership.md) | Owns fact channels, source/derived artifact boundaries, and regeneration rules |
| Failure recovery | [`failure-recovery.md`](./governance/failure-recovery.md) | Owns stop/continue policy and resume pointers |
| Confirm UI details | [`confirm_ui.md`](../scripts/docs/confirm_ui.md) | Owns the JSON schema, launcher behavior, staged-result contract, port strategy, and chat fallback details |
| Confirmed template application | [`apply-template-workspace.md`](./stages/apply-template-workspace.md) | Owns validation and installation after Stage 1 confirms library or explicit workspace roots; skip for confirmed free design |

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: The user has provided a topic / desired outcome and any available initial material.

> **Topic-only**: run [`topic-research`](stages/topic-research.md) immediately,
> then use its research pair as source content; Step 2 imports that pair without
> expanding the facts JSON's webpage URLs.

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

**Source-image orientation trigger**: Before Step 2, follow
[`conversion.md`](../scripts/docs/conversion.md) § Image Orientation Review when
the user requests correction, converted text asks for rotated viewing, or a
downloaded asset is visibly sideways. Do not launch its legacy HTML tool.

After reading direct and converted content, assess factual sufficiency:

| Material state | Action |
|---|---|
| Requested outcome is supported | Continue Step 2 |
| Required externally verifiable claims remain unsupported | Run [`topic-research`](stages/topic-research.md) for those gaps only |
| Closed corpus / source-only / no external enrichment | Stay within supplied material |

**Sufficiency test**: research only to avoid inventing, omitting, or leaving
unsupported a factual claim the requested outcome requires; file presence or
length is irrelevant. It records the needed facts and adopted webpage URLs in
the research pair. Step 2 fetches no adopted page; Step 5
acquires only Strategist-selected independent AI / web / slice assets after
final confirmation.

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

**✅ Checkpoint — Confirm source content and any factual supplement/provenance pair are ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown file, user-provided text, or requirements described in conversation are all valid).

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name>
```

**Hard rule — truthful canvas token**: append
`--format <registered_format>` only when an explicit user/source fact already
establishes an exact registered canvas before initialization. Otherwise omit
the flag; Stage 1 confirms the canvas and `spec_lock.md` records its viewBox.

Initialization creates `<project_path>/validation/workflow.log`; every later project-scoped Python tool records its command envelope and material outcome lines there automatically. When a helper's arguments and working directory do not identify the project, prefix the same command with `PPT_MASTER_PROJECT_PATH="<project_path>"`. For a material handoff, rework reason, user-approved exception, or manual recovery choice with no owning command output, append one concise note with `python3 ${SKILL_DIR}/scripts/workflow_log.py <project_path> "<detail>"`. The log is cold audit evidence: never read it during normal generation.

Registered formats: [`canvas-formats.md`](../references/canvas-formats.md).

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF/MD/etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...>` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps can reference it directly |

When Topic Research ran, include only its research pair. `project_manager.py`
imports the facts JSON as an ordinary file and never expands its `source_url`
values, so project initialization fetches no adopted page.

For PPTX sources, `import-sources` automatically runs the standard intake enrichment:

```bash
python3 ${SKILL_DIR}/scripts/pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis
```

For each PPTX it writes `<stem>.identity.json` (canvas, theme palette/fonts, observed usage) and `<stem>.slide_library.json` (text slots, geometry, native tables, native chart caches, SmartArt nodes/connections), and merges that deck's Strategist-facing digest into the single multi-deck index `analysis/source_profile.json` (`decks[]`, one self-contained entry per source deck, with prefixed artifact pointers). In the main generation path these are source facts and recommendation candidates, not replica constraints; the beautify profile decides separately which fields become locked constraints.

Multi-deck: several PPTX files may be imported into one main-pipeline project — each gets its own `<stem>.*` artifacts and a deck entry in `source_profile.json`. `source_profile.json` stays the single must-read index (one entry for a one-deck project, several for a combined-source project). Stems must be distinct; re-importing the same stem replaces that deck's entry. The beautify profile remains single-deck (1:1 to one chosen source deck) and reads that deck's `<stem>.*` artifacts.

**Source ownership boundary**: Use the automatic import mode shown above. Only inputs already under the repository's `projects/` tree move into the target project's `sources/`; every other local path is copied and remains untouched, even if `--move` is supplied. Use `--copy` when a projects-local input must also remain in place. If Step 1 wrote Markdown beside the original sources, pass that source path/directory once. If Step 1 used `-o` to write Markdown elsewhere, pass both the original source path(s)/directory and the Markdown output path(s)/directory. Intermediate artifacts (e.g., `_files/`) are handled automatically.

Direct supported bitmap inputs follow both boundaries: the original is archived under `sources/`, and a collision-safe basename is copied into `images/` for analysis and §VIII planning. SVG/EMF/WMF remain source assets unless they arrive through a converter companion manifest that supplies their display metadata. This does not classify an asset's role; Strategist still decides whether it is used.

**✅ Checkpoint — Confirm project structure created successfully, `sources/` contains all source files, converted materials are ready. Proceed to Step 3.** `import-sources` exits 0 when any input converts; read the printed `skipped` reasons and treat those inputs as absent sources.

---

### Step 3: Template Candidate Preparation

**Scope**: Every Default Generate run. This is internal preparation only: do not
open a page, ask a question, wait for a receipt, select a workspace, read a
template spec/prototype, or install anything. Quick resolves exact supplied
roots or free design inside its profile and skips this Step.

Prepare the candidate boundary that Stage 1 will confirm. Registered candidates
come from exactly these discovery sources:

- `templates/brands/brands_index.json`
- `templates/styles/styles_index.json`
- `templates/layouts/layouts_index.json`
- `templates/decks/decks_index.json`

Derive each library root as `templates/<kind_dir>/<id>/` from its index entry.
Never scan kind directories, infer unregistered entries, or resolve a bare name,
brand mention, or style phrase to a path. Preserve every exact root supplied for
this run. A registered-root equality match remains `library`; every other exact
root remains `explicit`. Candidate provenance never changes later validation,
installation, or precedence.

Resolve the confirmation surface under
[`confirm_ui.md`](../scripts/docs/confirm_ui.md). In the UI branch, run
`--reset-template-selection`, then write
`<project_path>/confirm_ui/template_options.json` with schema version `1`,
`phase: "template"`, the UI language, and all supplied exact roots as absolute
`explicit_workspace_roots`; use an empty array when none were supplied. Also
write required `default_mode`: `templates` when the user explicitly asks to use
or browse templates or supplies any exact root, otherwise `free_design`. The
server reads the four indexes itself. Do not launch it yet. In chat/delegated
confirmation, retain the same candidate boundary in context and create no UI
artifact.

Stage 1 initializes from `default_mode`, but the user can switch modes. Template
mode alone expands the candidates and must eventually select at least one
workspace. Exactly one supplied root may be preselected as an editable default;
multiple supplied roots remain unselected candidates. `free_design` selects none.

**Raw PPTX boundary**: A raw PPTX remains valid source material, but it is not a
template workspace candidate. Raw PPTX plus new content uses
[`edit-native-pptx`](./edit-native-pptx.md). To create a reusable workspace,
run [`create-template`](./create-template.md), then return with the generated
root. Never add Master/Layout/placeholder structure directly to an existing
PPTX or SVG project.

**✅ Checkpoint**: Candidate input is ready for the combined Stage-1
confirmation. No template has been selected, read, validated, or
installed. Proceed to Step 4 without a user-visible stop.

---

### Step 4: Strategist Phase (MANDATORY in the default pipeline)

🚧 **GATE**: Source preparation and Step-3 candidate preparation are
complete. No template content has entered planning context and no template has
been installed. Stage 1 has not started before this point.

**Hard rule — Stage 1 is template-independent**: Author every Stage-1
communication recommendation from the user's current request, source facts,
conversation constraints, and project-initialization state only. Candidate
paths, index summaries, template specs/prototypes/assets, and template canvas
are not recommendation evidence. Author the communication proposal before any
chat-branch catalog listing. The project initialization canvas remains the
Stage-1 starting value unless the current user/source context changes it.
Template inspection and current-project fit begin only after Stage 1 confirms
both the communication contract and template/free-design choice and any selected
workspace has been installed.

At Step-4 entry, load the always-required planning context directly in one
batch: the role core, every canonical content-type source file defined below,
and the compact structured analysis facts already present. Do not load any
mode, visual-style, or image-rendering detail file before Stage 1. For a multi-deck
`source_profile.json`, read its compact `decks[]` digests in that batch and open
a deck's larger identity/slide-library files only when the specific need below
arises.

```
Read ${SKILL_DIR}/references/strategist.md
Read ${SKILL_DIR}/references/canvas-formats.md
```

Then load only the extra role modules triggered by the current plan:

| Deterministic trigger | Additional Strategist reference |
|---|---|
| Stage 1 is confirmed and its template choice installed a selected Brand/Style/Layout/Deck workspace into this project | `references/strategist-template.md` before Stage 2 |
| The confirmed Stage-1 `delivery_context` identifies recorded/self-running/video delivery, or input is an explicit final/literal narration script | `references/video-design.md` before the three Stage-2 whole solutions and page roster |

After Stage 1 and template handoff, load the fixed planning-capability block
below in one batch before authoring any Stage-2 whole-solution intent, image
source recommendation, or page roster:

```
Read ${SKILL_DIR}/references/strategist-image.md
Read ${SKILL_DIR}/references/image-layout-spec.md
Read ${SKILL_DIR}/references/image-layout-patterns.md
Read ${SKILL_DIR}/references/modes/_index.md
Read ${SKILL_DIR}/references/visual-styles/_index.md
Read ${SKILL_DIR}/references/image-renderings/_index.md
Read ${SKILL_DIR}/templates/icons/README.md
Read ${SKILL_DIR}/templates/charts/chart-vocabulary.md
Read ${SKILL_DIR}/templates/tables/table-vocabulary.md
```

This is a capability map; retain the Strategist/Executor ownership boundary. Author the three whole solution
intents before mapping any component basis. Freeze every referenced
mode/style/rendering id from the indexes, then read once only the deduplicated
union of those exact detail files and finish the three custom behaviors. A novel
custom reads no detail file. Confirmed non-`none` uses the already-loaded image
layout references and continues into resource planning; confirmed `none` writes
no image rows while retaining recommendation-only rendering candidates. Only an installed
project-local template state loads the template module, and only after Stage 1
is confirmed; a bare template/style name does not.

> ⚠️ **Mandatory artifact gates**: after final confirmation, author `design_spec.md` at the confirmed `design_spec_depth` from `${SKILL_DIR}/templates/design_spec_reference.md`. After Gate 1 and any refinement approval, author `spec_lock.md` from `${SKILL_DIR}/templates/spec_lock_reference.md` plus approved Design Spec/context. Author each new artifact once without placeholders or `scaffold-*` (manual-only). Schema validity does not prove semantic fidelity.

**Artifact ownership**: fact-channel and source/derived artifact boundaries are defined in [`references/artifact-ownership.md`](../references/artifact-ownership.md). This Step uses those ownership rules; it does not redefine them.

**Fact channels** (owned by [`artifact-ownership.md`](../references/artifact-ownership.md) §1–2): before Stage 1, read the compact machine facts already in `<project_path>/analysis/` — `source_profile.json`'s `decks[]` digests (canvas, chart/table/SmartArt structure per source deck), opening a deck's `<stem>.identity.json` / `<stem>.slide_library.json` only when its raw facts are needed. Content — text, tables, chart values, SmartArt wording — comes from the content-type files in `sources/` (`<stem>.md` and any archived `.txt` / `.csv` / `.json` / `.yaml`), never from the structural digest; `*.conversion_profile.json` and `*_files/image_manifest.json` are sidecars, not content. A source deck's palette, typography, and visual identity are reference, not constraint: inherit where they fit the content and confirmed style, design fresh where they do not. `analysis/image_analysis.csv` arrives at the image step below and is a regenerated view of `images/`, not a durable store.

**Confirmation orchestration**: field meaning and recommendation logic belong to the active Strategist modules; [`confirm_ui.md`](../scripts/docs/confirm_ui.md) owns the JSON schema, server lifecycle, staged-result contract, port behavior, and equivalent chat fallback.

⛔ **BLOCKING**: The two-stage Strategist confirmation is the always-on user
gate unless explicitly delegated. Stage 1 confirms the communication contract
and, on the same screen or in the same chat turn, exactly one template mode:
`free_design` or `templates`. Only `templates` expands the four registered-kind
selectors plus supplied exact-root candidates, and it requires at least one
selection. Final Stage 2 confirms the complete deck solution plus production
mechanics only after the Stage-1 choice is installed or its free-design handoff
is complete. An enabled `refine_spec` adds the one conditional chat gate after
Design Spec Gate 1. Author each stage once; submitted values—including blanks or
unusual overrides—are authoritative.

**Confirmation ownership and surface**: Only the user confirms. Before any
confirmation server command, apply
`confirm_ui.md`'s surface
decision to this run's most recent explicit surface instruction and retain that
branch as the owner specifies. A natural-language request or agreement to
personally confirm in chat, or to avoid the page, selects the chat branch without
a magic keyword; skip UI launch/wait commands and UI-authored result state.
Explicit delegation is a separate higher-priority branch. With no surface
instruction, use the default UI branch. A chat-question tool alone does not
replace that default. The agent may author recommendations, operate the
server, read state, and apply a selected template, but MUST NOT confirm on the
user's behalf, automate submission, synthesize a payload, or write/replace user
result state. Delegation applies only to this run: make the Stage-1 communication
and template decision, install any selection, then derive and show the complete
Stage-2 summary without fabricating UI results. Silence confirms nothing.

**UI branch files**: `confirm_ui/template_options.json` (Step 3), `recommendations.stage1.json`, `template_handoff.json` (written only by `--complete-template-selection`), and `recommendations.stage2.json` are the agent-authored inputs; `template_selection.json` and `result.json` are user-owned receipts. Only the active unconfirmed stage file may be overwritten — regenerate a rejected recommendation in place, never as a revision-suffixed file, and never let one stage file carry another stage's payload. Schemas and completion evidence: [`confirm_ui.md`](../scripts/docs/confirm_ui.md).

**UI branch only** — Step 3 wrote `template_options.json` but did not launch or
wait. Create `confirm_ui/recommendations.stage1.json` without reading template
candidate content, then launch the combined Stage-1 page and post
`confirm_ui.md`'s required communication + template-choice summary/fallback:

```bash
python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon
python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage1
```

**Hard rule — Stage 1 is intermediate**: exit `0` from this first wait is an
instruction to continue, not a route-completion condition. Do not send a final
chat reply, go idle, or yield the task here. In the same active run, read the two
Stage-1 receipts, complete the template/free-design handoff, author fresh Stage
2, and invoke the final wait below. Only `stage: final` + `status: confirmed`
may close this confirmation flow.

The single Stage-1 submission writes both `result.json` and
`template_selection.json`; neither replaces the other. Read each exactly once.
Require a confirmed communication result and either `free_design` with no roots
or `templates` with at least one server-resolved root.

1. For `templates`, load and run
   [`apply-template-workspace.md`](./stages/apply-template-workspace.md) against
   every confirmed exact root. It validates them and installs each as its own
   `templates/design_spec.<kind>.<id>.md` plus any real `images/` and `icons/`.
   For `free_design`, skip installation. Then bind the completed state:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --complete-template-selection
   ```

   This agent-only command writes `template_handoff.json`; do not hand-author
   it. The server requires this handoff before Stage 2.

2. Only now inspect installed template state and apply
   `strategist-template.md` when active. Load the fixed Stage-2 planning-capability
   block above, author three whole solution intents, freeze their exact component
   references from its indexes, then read only the referenced detail files and
   complete the custom projections. Derive the
   remaining production defaults and create
   `confirm_ui/recommendations.stage2.json` without changing Stage 1; declare
   `stage: "stage2"`, then wait for the final confirmation:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only
   ```

3. After the final wait returns, read the complete `result.json` exactly once
   and retain that object through Design Spec authoring and its fidelity audit.
   Proceed only when it carries `stage: final` and `status: confirmed`. Do not
   reopen the file during normal lock authoring or downstream execution. On a
   non-zero wait, this same single read determines whether the persisted result
   succeeded before using the documented chat fallback. A stage-skip result
   returns to the missing stage; it is not a browser failure.

4. After final confirmation or chat fallback, always release the server:

   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --shutdown
   ```

If the user selects chat any time after the UI server launches, immediately
apply `confirm_ui.md`'s in-run switch procedure. Continue the unresolved current
stage and all remaining stages in chat; do not enter UI interruption recovery
or relaunch the server.

**Chat branch** — present the template mode and Stage-1 communication contract
together and wait for one explicit response. Show registered candidates only
when the user chooses `templates`; supplied exact roots remain available in that
expanded choice. Initialize free design for an ordinary request and template
mode for explicit template intent or any exact root; with exactly one root it
may also be the preselected candidate, while multiple roots remain unselected.
Do not create UI receipts
or call `--complete-template-selection`. After confirmation, install/fuse any
selected roots (or close free design) and retain that completed state in context
as the Stage-2 gate. Then run final Stage 2 in chat and retain one visible
cumulative summary as the equivalent final state. Under explicit delegation,
make the same Stage-1 decision, install it, derive Stage 2, and present one
complete AI-authored summary.

⛔ **GATE — final state → Design Spec → conditional review → lock.** Consume every present final value once into the complete, audited `design_spec.md` under [`strategist.md`](../references/strategist.md) §6.2. Preserve each owning semantic type and all production, typography, image-source, and `image_notes` obligations; acceptance never turns a Reference/Permission into a Literal. Do not reopen `result.json`.

With `refine_spec: true`, run [`refine-spec`](stages/refine-spec.md) after Gate 1: review that same file in chat, accept arbitrary revisions, touch no lock, and stop until explicit approval. Revisions supersede only affected decisions. Otherwise skip the stop.

After the review closes, author `spec_lock.md` from the approved Design Spec and context. Preserve identity/refinements, every recurring typography role, reusable routing anchors, and each placed image's source/layout suggestion/crop policy; omit page-local garnish and never write a separate image palette. Apply `strategist-template.md` §3 when active. Unhonorable requirements follow [`failure-recovery.md`](governance/failure-recovery.md).

**Conditional — split-mode note** (not a separate confirmation): after listing the Strategist confirmation stage details, append one short line (rendered in the user's language, prefixed with 💡) only when the confirmed mode is `split` or upstream-load signals make a fresh execution context materially useful. Judge those signals from recommended page count, source-material bulk, and research material actually retained in this chat. Raw fetches performed by a successful isolated `topic-research` worker do not count; substantial local-fallback fetches or unusually large imported research artifacts do.

| Signal read | Line content |
|---|---|
| Heavy (long page count / bulky sources / heavy retained research context) | State the applicable heavy signals; recommend switching to [split mode](stages/resume-execute.md) after Step 5 — stop this chat, open a fresh window and input `继续生成 projects/<project_name>` to enter the execution session (SVG generation + export); no response or "continue" = default continuous mode. |
| Explicit `split` selection | Confirm that planning will stop after Step 5 and give the `继续生成 projects/<project_name>` handoff command. |

For the normal/default `continuous` path, print no split-mode reminder and proceed automatically. Confirm UI still exposes the generation-mode toggle and records it in `result.json`; a chat fallback captures the same choice in its confirmation summary without adding a separate reminder.

**Mandatory — spec-refinement note** (not another Confirm UI stage): after confirmation details and any split-mode line, append one localized 💡 line offering review of the complete Design Spec before the lock; any part may be revised in chat until explicit approval. Default OFF; only explicit chat opt-in or `refine_spec: true` runs [`refine-spec`](stages/refine-spec.md) after Gate 1. Confirm UI records the toggle; chat fallback prints the same line.

**Native formula content**: Formula handling is not a confirmation field or an
image-acquisition path. Strategist records exact mathematical content as a
delimiter-free LaTeX expression body in the applicable §IX page block without
classifying its implementation. Executor independently chooses ordinary text,
same-paragraph native inline math, or a standalone native block under
[`native-formula.md`](../references/native-formula.md); matrices, multiline
derivations, and other high-structure expressions remain blocks.
No formula manifest, §VIII resource row, or `spec_lock.md images` entry is
created.

**Native hyperlink content**: Hyperlinks are not a confirmation field or a
resource-acquisition path. Strategist records the linked text/object intent and
exact absolute URI or 1-based same-deck slide target in the applicable §IX page
block. Executor chooses an inline or whole-object carrier and authors the
canonical SVG `<a href>` under
[`native-hyperlinks.md`](../references/native-hyperlinks.md). Unknown targets
return upstream; no hyperlink manifest or `spec_lock.md` entry is created.

**Proactive production decisions**: Final Stage 2 records
`proactive_speaker_notes`, `proactive_custom_animations`, and
`proactive_narration_audio`. They control only what the agent initiates when the
user has not already given an explicit instruction. Resolve each effective
outcome as latest explicit user instruction → final Stage-2 value → workflow
default `true` / `false` / `false`. Final Stage-2 Narration Audio enabled raises a
non-explicitly-disabled Speaker Notes outcome to enabled and names that
dependency in its provenance without rewriting the raw proactive preference.
Persist the resolved effective outcomes plus provenance as the `Speaker Notes`,
`Custom Animations`, and `Narration Audio` rows in `design_spec.md §I`; keep the
raw proactive fields only as confirmation evidence and do not project either
form into `spec_lock.md`.

**Post-confirmation override**: A later explicit request updates only affected
§I outcomes/provenance and resumes their owning step; do not reopen Confirm UI.
If it disables Speaker Notes while Narration Audio remains enabled, write
neither row and ask one question: disable audio too, or retain its required
notes. Wait, then update both. Before `generate-audio`, create and split notes
when complete per-slide files are absent.

If the user provided images, run analysis **before outputting the design spec**. It writes `analysis/image_analysis.csv` — the authoritative regenerated image-fact view in the `analysis/` folder, which MUST be read before authoring §VIII:
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> 🔁 **Image facts are regenerated on change, never maintained as a second store.** `images/` is the live working folder and single source of truth; `analysis/image_analysis.csv` is its regenerated view. Run `analyze_images.py` before the first inventory read, then reuse that CSV while `images/` is unchanged. Re-run after import/acquisition or any user addition, removal, or replacement; an empty folder produces a fresh header-only CSV rather than leaving stale facts.

> ⚠️ **Image understanding**: Do not bulk-open images. Strategist starts from context, filenames, records, and `image_analysis.csv`; inspect only a specifically ambiguous asset under [`strategist-image.md`](../references/strategist-image.md), then record the result in §VIII. Under [`executor-image.md`](../references/executor-image.md), Executor may inspect one selected `Existing` / `Sourced` asset only to resolve crop, focal placement, or text contrast—never to reselect, replace, or infer provenance.

**Output**:
- `<project_path>/design_spec.md` — complete human-readable design narrative and durable confirmed production state
- `<project_path>/spec_lock.md` — machine-readable stable execution anchors/routing, authored after conditional review approval
- `<project_path>/notes/total.md` — only when the prepared final narration branch is active; frozen verbatim production input

For a new project, use the reference-first whole-document sequence:

1. Read `${SKILL_DIR}/templates/design_spec_reference.md`; create complete I–X `<project_path>/design_spec.md` once from retained confirmation, analysis, and context, without placeholders/examples.
2. Audit it field by field against retained confirmation; Gate 1 must pass.
3. If enabled, run [`refine-spec`](stages/refine-spec.md) on that file until explicit approval; touch no lock.
4. Read `${SKILL_DIR}/templates/spec_lock_reference.md`; create or resynchronize the lock once from approved Design Spec and context. Never reopen `result.json` or make a new design choice.
5. Compare lock anchors/routing to the Design Spec; run `python3 ${SKILL_DIR}/scripts/project_manager.py validate <project_path>`.

Final state → initial Design Spec mismatch, approved Design Spec/context → lock mismatch, or an unapplied revision blocks despite schema validity. `validate` does not prove fidelity. Repair from retained confirmation before refinement; during it, preserve unaffected values and apply explicit revisions. After approval, derive the lock from that Design Spec/context. Resume/refine edits existing files, never scaffolds. Fresh recovery alone may reread persisted final evidence once.

**Prepared final narration branch**: follow `video-design.md` §1 and §3 when an
explicit final/literal script will become notes or generated audio. Segment it
by semantic scene during Stage 2; §IX gives each segment a supporting visible
state and §X records its source/verbatim policy. After Gate 2, before Step 5 or
split handoff, write the exact segments once to `notes/total.md`; split them only
in Step 7.1. This is frozen production input, not a third planning artifact.

**✅ Internal checkpoint — Phase deliverables complete**: facts read; confirmation consumed once; final Stage-2 production fields resolved (generation mode, refine-spec, proactive choices, and conditional AI path); mathematical content recorded where applicable; every §IX page resolved its one-pass carrier mix and §VIII contains only assigned external image-resource jobs; Design Spec passed Gate 1; enabled refinement approved; lock derived from it; split handling resolved; communication and every §IX `Audience move` validated. Do not print this checklist; auto-proceed.

---

### Step 5: Image Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; `<project_path>/design_spec.md` and `<project_path>/spec_lock.md` both exist. If either required artifact is missing, stop before any acquisition or generation and follow [`failure-recovery.md`](governance/failure-recovery.md) §3.

> **Trigger**: §VIII is Step 4's committed external image-resource result, not a candidate inventory. At least one row has `Acquire Via: ai`, `web`, and/or `slice`, or one row is a pending prepared derivative declared by `Reference: Derived from <canonical bare filename>; treatment=...`. A prepared-user-only plan skips this step only when it has no derivative to materialize; `placeholder` rows alone do not trigger it. A permitted but unused image source creates no row and does not trigger acquisition. If §VIII omits a source, asset, or page role that `image_notes` explicitly requires, the Design Spec is incomplete; return to Step 4 Gate 1, repair it from the retained final state, and re-author the affected lock anchors from context. Do not reopen `result.json` during this check.

**Failure recovery**: stop/continue behavior for AI/web/slice/image-readiness failures is defined in [`workflows/governance/failure-recovery.md`](governance/failure-recovery.md). This Step keeps the acquisition procedure.

**Always load the common framework**:

```
Read ${SKILL_DIR}/references/image-base.md
```

Then **lazy-load the path-specific reference** for each row that actually needs it:

| Row kind / Acquire Via | Load reference (only if any such row exists) | Run |
|---|---|---|
| Prepared derivative | `references/image-base.md`; add `references/image-generator.md` §4.4 only for registered layers | after its named canonical source reaches a usable terminal state, run `python3 ${SKILL_DIR}/scripts/image_treat.py ...` for the declared per-pixel treatment or the existing §4.4 preparation path |
| `ai` | `references/image-generator.md` | write `<project_path>/images/image_prompts.json`, then follow `image-generator.md §7 Path Selection` (`image_gen.py --manifest` is **Path A only**) |
| `web` | `references/image-searcher.md` | `python3 ${SKILL_DIR}/scripts/image_search.py ...` (≥2 web rows → `--batch images/image_queries.json`) |
| `slice` | `references/image-generator.md` §4.3 | derived — **after** the parent `ai` sheet row is `Generated`, run `python3 ${SKILL_DIR}/scripts/slice_images.py <project_path>/images/<sheet>.png --grid RxC --names ... --trim --alpha --bg KEY_HEX_FROM_PROMPT --strict-alpha` (see workflow step 2.5) |
| `user` / `placeholder` | (skip) | (skip) |

A deck with only `ai` rows never loads `image-searcher.md`; a deck with only `web` rows never loads `image-generator.md`. A mixed deck loads both, processes each row through its own path, and writes both `image_prompts.json` and `image_sources.json`.

> ⚠️ **In-pipeline `ai` rows use the manifest contract** even for one row: write `images/image_prompts.json`, render `image_prompts.md` with `--render-md`, then follow the confirmed path from [`image-generator.md`](../references/image-generator.md) §7 — `image_gen.py --manifest` is Path A only, `host-native` is Path B and skips `--manifest`, `manual` writes prompts and stops. The recorded `design_spec.md §I` path wins over `IMAGE_BACKEND`; never reopen `result.json` here. The positional `image_gen.py "prompt"` form is for out-of-pipeline fixups and the §4.4 registered reconstruction derivation only.

> ⚠️ **`web` rows**: with ≥2 rows write `images/image_queries.json` and run `image_search.py --batch` once. When any vision-capable context exists, add `--save-candidates` with explicit `query_variants` and run [`web-image-review`](stages/web-image-review.md) on the saved sheets; only a stage-selected candidate is promoted (`--promote`), the row advances to `next_candidate_page` before the query changes, and only an exhausted pool returns the row to `Pending` with new variants. Without vision, omit `--save-candidates`: best-only mode may download a strict metadata-verified candidate (`selection_method: metadata-ranked`) or stops at `Needs-Manual`. Only after normal search is exhausted may a vision-capable owner fetch one [`topic-research`](stages/topic-research.md) `source_url` as a reviewed source package. Keep §VIII `Reference` as the locked intent and author a separate short provider query.

> 🚧 **Default exhausted-automation GATE**: `auto` tries Path A then Path B but never silently enters Offline Manual. When both are unavailable/exhausted — or a confirmed `api` / `host-native` path stays unavailable after its retry — ask whether to repair and retry the same path, generate the listed files manually, or cancel the affected AI images and repair the plan. Only confirmed `manual` creates `Needs-Manual` rows. Quick applies its own non-interactive no-AI replan instead.

Workflow:

1. Extract all resource rows from the design spec. First separate rows whose `Reference` starts `Derived from <canonical bare filename>; treatment=` so they cannot re-enter ordinary ai/web/slice acquisition; reject source/output equality, a derivative parent, chains, cycles, or self-reference; then group canonical rows by `Acquire Via`. Every Pending/Failed canonical acquisition row and Pending derivative must reach a terminal state before Executor starts.
2. Generate prompts (ai rows) and/or run search (web rows) per [image-base.md](../references/image-base.md) §3 dispatch table
2.5. **Slice any illustration, illustrated-icon, or lettering sheets (only if `slice` rows exist).** For each generated `ai` **sheet** row, run `slice_images.py` with the matching grid/`--names`, `--trim --alpha`, the exact key HEX named in its prompt as `--bg`, and `--strict-alpha`. Mark each `slice` row `Generated` only after exit 0; a strict keying failure writes no replacement outputs and returns the affected sheet to image preparation. A sheet still in `Needs-Manual` cannot be sliced — leave its `slice` rows `Needs-Manual` and surface them at the Step 7 readiness gate. Contract: [image-generator.md](../references/image-generator.md) §4.3.
2.6. **Materialize planned prepared derivatives.** After each named canonical source reaches a usable terminal state, preserve it and write the separately named derivative only from its declared treatment. Use `image_treat.py` for per-pixel blur, desaturation/grayscale, duotone, brightness, or contrast; that row inherits the canonical `Acquire Via` and terminal class. Use `image-generator.md` §4.4 only for registered clean-base/layer work; a supplied final asset is `user / Existing`, while generated/reconstructed output remains `ai / Generated`. A standalone cutout must be prepared RGBA, a flat-key slice, or supplied by the active host; otherwise follow its owning source's terminal rule, including the Default AI recovery decision before `Needs-Manual`. Do not present `image_treat.py` as photo background removal. Do not bake crop/clip, rotation/mirror, opacity, frame, shadow, scrim/wash, vignette, or overlap into a bitmap. Any derivative of a web source copies that source's license/attribution record to the new filename. A parent without a usable status leaves the child in the same unresolved or manual state.
3. Verify every processed acquisition/derivative row reaches its source-class terminal status under [`svg-image-embedding.md`](../references/svg-image-embedding.md); no `Pending`, `Failed`, or web `Needs-Selection` remains. On `auto`, follow the owning automated fallback chain. For confirmed `api` or `host-native`, retry only that path. Any unresolved Default AI row stops at the recovery decision above; do not mark it `Needs-Manual` or switch provider before the user's choice.
4. Re-derive image facts after canonical acquisition, slicing, and prepared derivatives are final — `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` — so `analysis/image_analysis.csv` reflects every image the Executor may place. Image facts are regenerated on use, never a stale store (see Step 4's image-facts note).

**✅ Internal checkpoint — acquisition complete**: verify conditional AI/web sidecars, all required slice outputs, terminal status for every resource row, and a refreshed `image_analysis.csv`. Do not print this checklist. On success, auto-proceed under the compact status rule above.

**Default — auto-proceed to Step 6.** Only when `design_spec.md §I` records `generation_mode: split`, output the planning-session handoff below and stop this conversation:

  ```markdown
  ## ✅ Planning Session Complete
  - [x] Spec: `design_spec.md`, `spec_lock.md`
  - [x] Resources: `sources/`, `images/`, `templates/`
  - [ ] **Next**: open a fresh chat window and input `继续生成 projects/<project_name>` to enter the execution session via the [`resume-execute`](stages/resume-execute.md) stage.
  ```

> On web acquisition failure, follow [image-base.md](../references/image-base.md) §6 without halting. Continue through materially different query/provider/license/URL strategies; after exhaustion, mark `Needs-Manual`, report, and continue. AI rows use the separate Default recovery gate above.

---

### Step 6: Executor Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete; all prerequisite deliverables are ready.

Read the Executor role core before applying its context policy:

```
Read ${SKILL_DIR}/references/executor-base.md     # REQUIRED: flat/shared execution core
```

**Planning context**: follow [`executor-base.md`](../references/executor-base.md) §2.1. Reuse the complete Design Spec and lock in an unchanged, uncompacted context. Fresh/resumed/restarted, compacted/summary-only, or externally/unknown changed execution reads both once and reloads triggered inputs. For a local question, consult the retained lock first, then only the owning Design Spec fragment; do not poll files merely to prove validity.

**Scheduled lock re-read (Default Generate only)**: when another page follows, re-read `spec_lock.md` once after P05/P10/P15/… per [`executor-base.md`](../references/executor-base.md) §2.1.

**Exact page roster**: render `design_spec.md §IX` one-for-one, in order. Any add/drop/merge/split/reorder requires Spec repair first; a continuous run may repair within the confirmed range per [`executor-base.md`](../references/executor-base.md) §2.1.

**Page content**: §IX is preferred wording and semantic authority. Use it when it works; adapt it when presentation benefits while preserving intent, facts, and explicit literal requirements. Read sources only to verify requested evidence; return incomplete blocks to Step 4 instead of enriching them during execution.

**Prepared final narration**: when §X records a literal script, read the frozen
`notes/total.md` once before P01 and design each visible state/semantic group
around its exact segment; never edit or pad it.

**Artifact ownership**: `svg_output/` is the author source, `svg_final/` is derived, and image facts come from the regenerated `analysis/image_analysis.csv`; see [`references/artifact-ownership.md`](../references/artifact-ownership.md).

Read the construction references and the exact detail files named by this deck's retained `spec_lock.md` as one batch; do not reopen the planning indexes:

```
Read ${SKILL_DIR}/references/shared-standards-core.md      # REQUIRED: SVG contract + shared aesthetic/leading baseline
Read ${SKILL_DIR}/references/svg-effects.md                # REQUIRED: effects/construction vocabulary
Read ${SKILL_DIR}/references/native-shape-authoring.md     # REQUIRED: native-shape selection and Boolean construction
Read ${SKILL_DIR}/references/preset-shape-vocabulary.md    # REQUIRED: complete 187-name authoring vocabulary
Read ${SKILL_DIR}/references/executor-structure.md         # REQUIRED: qualitative relationship and topology grammar
Read ${SKILL_DIR}/references/topology-assembly.md          # REQUIRED: topology assembly material
Read ${SKILL_DIR}/references/semantic-svg.md               # REQUIRED: semantic metadata boundary
Read ${SKILL_DIR}/references/modes/<resolved-id>.md        # one preset id, or each `mode_references` id
Read ${SKILL_DIR}/references/visual-styles/<resolved-id>.md # one preset id, or each `visual_style_references` id
```

A preset reads its one locked file; a `custom` reads only the exact bases named by `mode_references` / `visual_style_references` and otherwise follows the behavior directly — never infer adjacent bases, glob a catalog, or blend unselected identities. Conditional modules (structured templates, Chart/Table branches, native data, formula, hyperlink, image, web-image, video-design, notes) load on the triggers in [`executor-base.md`](../references/executor-base.md)'s routing table; `video-design.md` is read before the first SVG when §I records recorded/self-running/video delivery or §X a literal script. No branch loads by analogy. The per-page Structure decision and the page carrier-mix decision follow `executor-base.md` §2.1 and §3.

**Design Parameter Confirmation (Mandatory)**: before the first SVG, output key design parameters from the spec (canvas dimensions, color scheme, font plan, body font size). See executor-base.md §2.

**Live Preview Auto-Startup (Mandatory)**: before the first SVG, automatically start the browser editor in live mode and keep it running continuously through Executor + Step 7 export:
```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live --daemon
```
- Start when Executor begins; `svg_output/` may be empty. Default: first free port from `6060`; `--port N`: strict bind. Read the actual URL from output or `<project_path>/live_preview/lock.json`.
- Before the first SVG, report that URL or the launch failure; never claim an unavailable preview.
- Run it as a long-running side process/session; do not wait for it to exit before generating SVG pages. Do not wait for user confirmation after startup.
- **Service must keep running** until one of: (a) the user clicks **Exit preview** in the browser, or (b) the user explicitly asks in chat to stop it. Generation continues even if the user closes the editor.
- **Do NOT read or apply submitted annotations during generation.** Users may annotate at any time, but Executor proceeds without touching them. The window to apply annotations opens only after Step 7 completes — see [`workflows/stages/live-preview.md`](stages/live-preview.md).
- The editor also supports **staged direct edits** (text content + SVG element attributes previewed immediately, then written to `svg_output/` only when the user clicks **Apply changes**; `Ctrl+Z` / Undo drops staged edits) alongside annotation; re-export stays chat-driven. Full scope and editor details: see [`workflows/stages/live-preview.md`](stages/live-preview.md) Notes.

**Conditional reference reads**: `executor-structured.md` owns template specs
and prototypes. `executor-visualization.md` resolves a selected canonical or
legacy value; read only its returned SVG plus applicable family branches. Read
each full reference once per valid context and reread only after change/context
invalidation. Flat routes skip template reads; never substitute summaries,
sidecars, or guessed family paths.

> Image facts: trust the latest `analysis/image_analysis.csv` from the Step 4 inventory read or the Step 5 post-acquisition refresh. If `images/` changed since, re-run `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` before layout; if the folder is empty, use no image inventory and ignore a stale CSV.

**Page-context**: use the read-only projector only for the diagnostic/telemetry triggers in Executor §2.1, never as a routine pre-page load.

> ⚠️ **Main-agent only**: SVG generation MUST stay in the current main agent — page design depends on full upstream context. Do NOT delegate to sub-agents.
> ⚠️ **Generation rhythm**: P01 → first-page gate → remaining pages (one page gate per first-exercised `not-exercised` item) → final gate. After context invalidation, reload under §2.1 before continuing.

**Visual Construction Phase**: generate SVG pages sequentially, one at a time, in one continuous pass → `<project_path>/svg_output/`

Each completed SVG carries the slide's complete visible design (a JSON-first Chart/Table is the sole object-local exception: its inline JSON is authoritative and the visible subtree an approximate preview). Native shapes are Executor-local capabilities under [`native-shape-authoring.md`](../references/native-shape-authoring.md): read the full preset vocabulary before page one, prefer independent native atoms, use Merge Shapes only when contour semantics require it, and use freeform last.

**Motion-ready image composition**: only when an explicit user motion instruction, an enabled effective Custom Animations outcome in `design_spec.md §I`, or an existing `animations.json` activates custom motion, evaluate §IX `Motion suggestion` rows and author any distinct in-slide image states or cross-slide continuity now under [`executor-image.md`](../references/executor-image.md), giving each independently revealable or continuing Slide-local unit a descriptive direct-root `<g id>`. Effects, pairing, order, and timing stay in the conditional custom stage after the final gate; a Motion suggestion alone activates nothing, and deterministic Morph still needs the continuing object as a direct-root group on both pages.

`template_reuse_scope: mirror|layout` pages start from the complete `page_layouts` SVG and preserve inherited visuals, root Master/Layout identity, atoms, and slots (strict keeps the contract; `layout` may reflow carrier text within unchanged slot bounds; adaptive uses a Strategist-declared Layout); a required fixed-atom or slot change returns upstream for plan/lock repair, and Executor never edits `spec_lock.md`. `style`, Style-only, free-design, and brand-only pages use `pptx_structure.mode: flat` per [`executor-base.md`](../references/executor-base.md) and [`semantic-svg.md`](../references/semantic-svg.md).

**First-page gate (Mandatory)** — after the **first** SVG page, before drawing page 2:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --canonical-authoring --stage first-page --json
```
Run the command unfiltered (no `tail`/`head`/`grep`). Review the complete P01 issue set from that one run before editing. Select any advisory warnings worth addressing, fix all blocking errors and selected warnings in one consolidated edit pass, then perform one verification rerun. If verification still fails, treat its complete output as the next batch and repeat the same review → consolidated edit → single verification cycle; never check between individual fixes. If the terminal output itself is truncated, read only the relevant issue arrays from `validation/svg_quality_first_page_report.json`; do not launch another checker run for discovery.

**Mandatory — read P01 as a method sample, then emit the classification before editing**: the gate validates how the remaining pages will be authored, not only this page.

| Signal | Reading |
|---|---|
| Two or more issues share a category and direction | Method-level bias — resolve it to the authoritative rule before P02; a correction fitted to the observed offset only patches this sample. For text extents that rule is the shared estimator, exposed as `python3 ${SKILL_DIR}/scripts/text_measure.py measure|wrap|box` — calibrate each role once; measure only lines near a limit (`--stdin` batches) |
| One isolated issue tied to this page's structure | Page-local — fix and continue |
| A recurring element appears for the first time (page furniture, caption format, section numbering, accent discipline) | It will be copied to every later page — confirm its semantics now |

Emit one line before the consolidated edit:

```
gate-signal: method=<rule resolved, or none> | page-local=<count> | not-exercised=<list>
```

`not-exercised` names what P01 could not test — a cover typically omits multi-line text, columns, charts, image captions, and data objects. Carry every resolved rule forward as arithmetic.

**Mandatory — first-exercise gate**: the first page exercising a listed item runs `python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --canonical-authoring --stage page --page <svg>` once (items first exercised together share it), fixes blocking items, then continues. Every other page runs without checker calls.

**Quality Check Gate (Mandatory)** — only after every planned SVG exists, BEFORE annotation handling and speaker notes:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --canonical-authoring --stage final --json
```
- **MUST**: Before this gate, every §IX `Native-ready` entry `<object-key>=yes` already has one matching draw-time marker group and JSON metadata child; `=no` and incidental microvisuals remain ordinary SVG. A legacy bare `yes|no` is readable only when that page has exactly one eligible object; it never derives from §VII.
- **Authority gate**: JSON-first Chart/Table validates inline schema/bounds; its preview has no freshness authority. SVG-first native-ready markers require a current `data-pptx-fallback-sha256`, stamped after SVG/JSON synchronization. Missing/stale baselines block canonical/native export, not fallback export.
- Run the command unfiltered (no `tail`/`head`/`grep`). One invocation already scans every page and reports the complete issue set.
- On failure, review all `blocking` errors and all advisory warnings from that run before editing. Choose which warnings merit work, fix every blocking error and the selected warnings in one consolidated edit pass, then perform one verification rerun. If it still fails, its complete output begins the next batch cycle; never run the checker between individual fixes or use repeated invocations to discover one next issue at a time. If terminal output is truncated, extract only `categories.blocking.issues` and, when needed, `categories.introduced.issues` from the report written by that same run.
- Every `warning` is advisory and non-blocking: do not return the page for mandatory modification, do not auto-normalize user-authored compatible syntax, and do not require an acknowledgement/disposition line. Recommendation warnings identify the generated-SVG default; fidelity/quality warnings may be reported when material, but the existing input may ship unchanged. If a condition must be corrected before release, the checker must classify it as an `error`, not a `warning`.
- The same rule applies to structured-template warnings (empty/framing-only Layout, bare Master, duplicate layout keys): they may guide an optional template cleanup, but warnings alone never fail the quality gate. Flat `style`, free-design, and brand-only routes still rely on their existing hard errors for invalid structure metadata or incomplete required locks.
- Run against `svg_output/` (not after `finalize_svg.py` — finalize rewrites SVG and masks violations).
- The JSON report is written to `validation/svg_quality_report.json`. `inherited` prototype diagnostics and `source-import` compatibility losses are informational provenance; only changed/new warnings remain `introduced`, and all release-blocking failures remain `blocking`.
- **Hard rule — token-safe report handling**: On a successful checker run, use the exit status and terminal summary as gate evidence. Do not open, `cat`, or otherwise load the complete JSON report into model context. Read it only for failure investigation, an explicit audit request, or a field absent from stdout; extract only the required field(s).

**Mandatory — final carrier-receipt review**: the final checker prints one
factual `[CARRIERS]` summary and stores per-page detail under
`files[].info.carrier_receipt`. Compare the summary with the retained page jobs,
chosen resource roles, and running geometry signatures before export. Counts
and diversity never create a quota or prove quality; zero preset use alone
neither proves fit nor establishes a defect. When the facts contradict an
active decision — an adopted preset absent from output, a primary image reduced
to a minor frame, unrelated jobs collapsing to one neutral construction — read
only the affected receipt rows, repair those pages in one consolidated pass,
and rerun the final checker.

**Logic Construction Phase (conditional)**: after the SVG quality gate passes,
when the effective Speaker Notes outcome in `design_spec.md §I` is enabled, load
[`executor-notes.md`](../references/executor-notes.md). When the prepared final
narration branch already created `notes/total.md`, validate its exact segments
against every information-bearing final SVG group and repair the visual page or
upstream plan on mismatch; never rewrite the script. Otherwise ground each
page's narration in its final SVG and generate complete speaker notes →
`<project_path>/notes/total.md`. When the outcome is `disabled`, do not load the
notes branch and do not require or create `notes/total.md`.

**✅ Internal checkpoint — execution complete**: verify live preview timing,
the P01 method gate, uninterrupted remaining-page generation, consolidated
repair of any complete failure set, exact §IX roster coverage, one-frame prose
wrapping, a final checker result of 0 errors, and `notes/total.md` only when
speaker notes are enabled. Do not print this checklist. Run the applicable
conditional gates below, then proceed to Step 7 under the compact status rule
above.

> **Chart pages?** If this deck contains data charts, run the [`verify-charts`](stages/verify-charts.md) quality-gate stage before Step 7 to calibrate coordinates. Skip if no chart pages.

> **Visual self-check (opt-in)?** If the user explicitly asked for a per-page visual re-pass on the SVGs ("跑一下视觉自检 / 视觉回看", "visual review", "check pages visually", etc.), run the [`visual-review`](stages/visual-review.md) quality-gate stage before Step 7. Do NOT run it by default and do NOT recommend it based on inferred model capability or deck size — trigger is user request only.

> **Motion execution (conditional)?** Visible-layer preparation belongs to the
> main SVG pass above. An existing `<project_path>/animations.json` always runs
> [`customize-animations`](stages/customize-animations.md) to validate and
> resolve preserve/adjust/replace/suppress intent before export. Without a sidecar, run
> the custom stage only for an explicit per-slide/per-object motion request or
> when the effective Custom Animations outcome in `design_spec.md §I` is
> enabled; §IX `Motion suggestion` rows inform that active pass but never
> trigger it alone. A deck-wide request loads
> [`animations.md`](../references/animations.md) and resolves Step 7.3 flags
> without activating the custom stage. Otherwise keep the exporter defaults
> (`fade` page transition, per-element animation `none`) and load no motion
> reference. Strategist owns the communication purpose; Executor owns exact
> native effects, options, order, timing, and whether a non-literal suggestion
> should simplify to `none`. Never add motion for coverage or variation.
> Sound is not a Strategist resource: do not select or sync it during Steps
> 3–6 and never write a sound id/path into `design_spec.md` or `spec_lock.md`.
> Any optional cue is selected only after the visual motion solution is final,
> under [`animations.md`](../references/animations.md) §2.2.

---

### Step 7: Post-processing & Export

🚧 **GATE**: Step 6 is complete; `svg_output/` contains every final page, all
required conditional quality gates passed, and the final SVG quality report has
0 errors. When the effective Speaker Notes outcome in `design_spec.md §I` is
enabled,
`notes/total.md` also exists and covers every page; when it is disabled, notes
artifacts are not gate requirements.

🚧 **Image readiness GATE**: When any required resource row is `Needs-Manual`, every expected file and derived slice output MUST exist under `<project_path>/images/` before the first active Step 7 sub-step. If any file is absent, pause and list the exact filenames; do not run `finalize_svg.py`, `svg_to_pptx.py`, or any other export path, and never ship the dashed placeholder. After the files arrive, rerun `analyze_images.py`, replace each dashed placeholder in `svg_output/`, reconcile every `no-crop` container to the measured native ratio, then rerun the final SVG quality check so the gate covers the changed sources.

After the separate readiness gate above has supplied every required manual file, the final SVG quality check closes each usable terminal §VIII row through `spec_lock.md images`, the exact locked file, and a real `<image href>`; it rejects unplanned/wrong-path references and also validates Sourced provenance/license records, image-specific visible credits, and effective per-placement pixel scale under `meet` / `slice` / `none`.

**Failure recovery**: On a command failure, repair the owning source artifact and resume from that failed sub-step per [`failure-recovery.md`](./governance/failure-recovery.md). Do not restart planning unless its owning source changed.

**Hard rule — strict serial commands**: Run the following commands one at a time. Do not combine them in one code block or shell invocation. Enter the next sub-step only after the current command exits successfully and its success criterion is true.

#### Step 7.1 — Split Speaker Notes

Run this sub-step only when the effective Speaker Notes outcome in
`design_spec.md §I` is enabled:

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Success criterion**: When enabled, per-slide Markdown files exist under
`<project_path>/notes/` and cover every published slide. When disabled, skip the
command and proceed directly to Step 7.2.

#### Step 7.2 — Build the Self-Contained SVG Preview

```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Success criterion**: `<project_path>/svg_final/` contains one self-contained preview SVG for every published slide. This optional derived preview does not replace `svg_output/` as the native-export source, and its absence never blocks Step 7.3.

#### Step 7.3 — Export the Native PPTX

Choose exactly one notes mode:

| Effective decision | Command |
|---|---|
| Speaker Notes `enabled` | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>` |
| Speaker Notes `disabled` | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --no-notes` |

Append `--native-charts-and-tables` only for an explicit editable PowerPoint
Chart/Table delivery decision. Templates, markers, semantic tables, and imported
charts never activate it. Without the flag, Chart/Table uses its SVG fallback;
formula native behavior remains intrinsic.

For deck-wide motion settings, append the resolved flags from
[`animations.md`](../references/animations.md). When the conditional custom
stage preserves or produces `<project_path>/animations.json`, keep the base command above:
the exporter reads the sidecar automatically. Explicit motion flags override
the corresponding sidecar default/slide fields, while group overrides remain
unless `-a none` hard-disables object motion. Exception: explicit Custom
Animations disable keeps the sidecar and appends `-a none`; final Stage-2 `false`
does neither. Only explicit all-motion disable uses `--no-animations`.
Otherwise do not mix deck-wide flags with a sidecar. With no motion input or
sidecar, preserve `fade` / `none`.

After the motion solution is final, run the optional sound pass in [`animations.md`](../references/animations.md) §2.2: no selected cue creates no `sounds/`; a selected cue is synced with `sound_sync.py` for its namespaced id(s), referenced from the validated sidecar, and never read from `templates/sounds/` directly. For a narrated MP4 with sound cues, [`generate-audio`](stages/generate-audio.md) owns the delivery choice (default `--conversion-trace` narrated export plus native raw video and verified mix, or an explicit real-time slideshow capture); do not enable conversion trace on every base export for a possible later branch.

**Success criterion**: The command exits successfully and produces:

- `exports/<project_name>_<timestamp>.pptx`
- `validation/<project_name>_<timestamp>.report.json` with `passed` or `passed-with-warnings` package/resource postflight status
- `validation/<project_name>_<timestamp>.trace.json` when bare `--conversion-trace` is enabled; an explicit `--conversion-trace <path>` uses that destination instead

Before creating the PPTX, the exporter independently requires the current matching `final` quality report; a missing, unreadable, unsupported, non-final, blocking, stale, or unverifiable report exits nonzero. The compact `[POSTFLIGHT]` receipt prints `status`, `quality_gate`, Slide count, warning-category counts, and PPTX/report paths. Disclose material warnings. Do not open or `cat` the complete report on routine success; use targeted field extraction only for failure investigation, an explicit audit request, or information absent from the receipt. A failed report or missing PPTX is not success. Retain its report path for later Generate narration (`deck_motion` handoff). This postflight proves the PPTX package, including native sound relationships; it is not acceptance evidence for a later MP4 audio track. `generate-audio` owns that triggered delivery check.

## ✅ Generate PPTX Complete

- [x] Image readiness gate passed
- [x] The final carrier receipt was compared with the retained page decisions, and any factual contradiction was repaired without treating counts as quotas
- [x] Notes split completed when enabled; disabled exports used `--no-notes`
- [x] `svg_final/` preview completed
- [x] Native PPTX published and postflight report written
- [ ] **Next**: Report the exported PPTX path; when the effective Narration Audio outcome in `design_spec.md §I` is enabled, run [`generate-audio`](stages/generate-audio.md), otherwise run a supporting post-export stage only when its explicit trigger is present
