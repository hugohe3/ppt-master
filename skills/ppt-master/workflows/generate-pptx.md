---
description: Default Generate PPTX authority for source intake, planning, SVG authoring, quality gates, and native PPTX export.
---

# Generate PPTX Route

> Load only after [`routing.md`](./routing.md) selects Default Generate or its Beautify profile. This file owns that runtime's Step 1–7 sequence, gates, role switching, and mandatory commands; explicit Quick loads [`quick-generate.md`](./profiles/quick-generate.md) instead, and Beautify enters here only when it does not explicitly select Quick.

**Hard rule — runtime paths**: expand every linked or abbreviated package path from the entry-time `SKILL_DIR` anchor inside each tool call; never change CWD or inherit a prior shell working directory.

**Default Core Pipeline**: `Initial Materials → [Fact Research] → Create Project → Template Candidate Preparation → Stage-1 Communication + Template Confirmation → [Template Installation] → Stage-2 Solution → [Image Acquisition] → Executor Live Preview → Quality Check → Post-processing → Export`

**Generate-specific execution discipline**:

- The current main agent hand-writes every SVG page; never delegate page generation or run a generator over `svg_output/`. `preset_shape_svg.py` and `shape_boolean_svg.py` provide only their stdout fragments after the agent chooses role, operands, paint, and z-order.
- SVG cadence: P01 → first-page gate → remaining pages → final gate. No batches, no other mid-run checker calls.
- Gate checklists are internal: on success continue with at most one compact status line; on failure report only the blocking items and required recovery.

**SVG page-design boundary**: `svg_output/` is the complete page-design source — every visible element of the exported slide is in the page SVG or referenced by it; templates, `design_spec.md`, and `spec_lock.md` never supply content at export ([`shared-standards-core.md`](../references/shared-standards-core.md) §4.0). Export compiles only the selected route's explicit structure contract (`flat` Slide-local; `structured` Master/Layout/Slide parts) and never infers structure. `svg_final/` is an optional preview release export never reads. Notes, animations, narration, and Edit Native PPTX stay outside this closure.

## Cross-Cutting Authorities

| Concern | Authority |
|---|---|
| Step 1–7 order, gates, role switching, mandatory commands | This file |
| Fact channels, source/derived artifact boundaries, regeneration | [`artifact-ownership.md`](../references/artifact-ownership.md) |
| Stop/continue policy and resume pointers | [`failure-recovery.md`](./governance/failure-recovery.md) |
| Surface decision, in-run switch, Stage-1/Stage-2/result payload shapes | [`confirm-surface.md`](../references/confirm-surface.md); server lifecycle and template-selection sidecar in [`confirm_ui.md`](../scripts/docs/confirm_ui.md) |
| Validation and installation of confirmed template roots | [`apply-template-workspace.md`](./stages/apply-template-workspace.md); skipped for confirmed free design |

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: the user has provided a topic / desired outcome and any available initial material.

| User provides | Action |
|---|---|
| PDF / DOCX / Office document / XLSX / XLSM / PPTX / EPUB / HTML / LaTeX / RST / web URL | `python3 ${SKILL_DIR}/scripts/source_to_md.py <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]` |
| CSV / TSV | Read directly as a plain-text table source |
| Markdown | Read directly |
| Topic only | Run [`topic-research`](stages/topic-research.md) first and use its research pair as source; Step 2 imports the pair without expanding the facts JSON's URLs |

The dispatcher writes standard Markdown plus a conversion profile beside each source; use `-t <type>` only when detection is ambiguous and `-o` only when a specific output location is required (an output directory for multiple or directory inputs). PPTX sources also receive standard intake in `<project>/analysis/` after Step 2. Backend details: [`conversion.md`](../scripts/docs/conversion.md), whose § Image Orientation Review applies when the user requests correction, converted text asks for rotated viewing, or a downloaded asset is visibly sideways (never launch its legacy HTML tool).

**Sufficiency test**: after reading direct and converted content, run [`topic-research`](stages/topic-research.md) only for gaps where the requested outcome would otherwise require inventing, omitting, or leaving unsupported an externally verifiable claim; a closed corpus stays within the supplied material, and file presence or length is irrelevant. Research records facts and adopted URLs in its pair; Step 2 fetches no adopted page, and Step 5 acquires only Strategist-selected assets after final confirmation.

**EMF/WMF from DOCX/PPTX**: embedded Office vectors land in `images/` with `image_manifest.json` as first-class §VIII assets. Never convert them to PNG — `finalize_svg.py` preserves them as external references and `svg_to_pptx.py` embeds them as native `image/x-emf` / `image/x-wmf` media at full vector fidelity; browser preview shows them blank, which is expected.

**✅ Checkpoint** — source content and any research pair are ready; proceed to Step 2.

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown, direct text, or requirements described in conversation).

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name>
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...>   # skip when content is only in conversation
```

**Hard rule — truthful canvas token**: append `--format <registered_format>` only when an explicit user/source fact already establishes an exact registered canvas ([`canvas-formats.md`](../references/canvas-formats.md)); otherwise Stage 1 confirms the canvas, starting from the project-initialization canvas unless the user/source context changes it, and `spec_lock.md` records its viewBox.

Initialization creates `<project_path>/validation/workflow.log`; later project-scoped Python tools record their command envelopes there automatically (prefix `PPT_MASTER_PROJECT_PATH="<project_path>"` when a helper's arguments do not identify the project; append one concise note with `python3 ${SKILL_DIR}/scripts/workflow_log.py <project_path> "<detail>"` only for a material handoff, rework reason, approved exception, or manual recovery with no owning command output). The log is cold audit evidence, never read during generation.

**Import rules**: pass the source path once when Step 1 wrote Markdown beside it, both locations when `-o` wrote it elsewhere, and only the research pair when Topic Research ran (its facts JSON is imported as a file; no URL is fetched). Inputs already under `projects/` move; every other path is copied and left untouched even with `--move` (`--copy` keeps a projects-local input in place). Direct bitmap inputs are archived under `sources/` and copied collision-safely into `images/`; SVG/EMF/WMF stay source assets unless a converter manifest supplies display metadata. For each PPTX, `import-sources` runs `pptx_intake.py <source.pptx> -o <project_path>/analysis` and writes `analysis/<stem>.identity.json`, `<stem>.slide_library.json`, and the multi-deck index `analysis/source_profile.json` (one `decks[]` entry per distinct stem; re-importing a stem replaces its entry) — source facts and recommendation candidates, not replica constraints; Beautify stays single-deck.

**✅ Checkpoint** — project created, `sources/` complete, converted materials ready. `import-sources` exits 0 when any input converts: read the printed `skipped` reasons and treat those inputs as absent. Proceed to Step 3.

---

### Step 3: Template Candidate Preparation

Internal preparation for every Default run — no page, question, receipt, selection, template read, or installation. Quick skips this Step.

Registered candidates come only from `templates/{brands,styles,layouts,decks}/*_index.json`, each root derived as `templates/<kind_dir>/<id>/`; never scan kind directories or resolve a bare name, brand mention, or style phrase to a path. Preserve every exact root supplied for this run (a registered-root match stays `library`; any other root is `explicit`; provenance never changes precedence). Raw PPTX is source material, not a candidate — raw PPTX plus new content is [`edit-native-pptx`](./edit-native-pptx.md), and a reusable workspace comes from [`create-template`](./create-template.md).

Resolve the surface under [`confirm-surface.md`](../references/confirm-surface.md). UI branch: run `--reset-template-selection`, then write `<project_path>/confirm_ui/template_options.json` with `schema_version: 1`, `phase: "template"`, the UI `lang`, all supplied roots as absolute `explicit_workspace_roots` (empty array when none), and `default_mode` — `templates` for explicit template intent or any supplied root, otherwise `free_design`. Do not launch yet; the server reads the indexes itself. Chat/delegated branch: retain the same candidate boundary in context and create no UI artifact. Stage 1 initializes from `default_mode` but the user may switch; template mode requires at least one selection; exactly one supplied root may be preselected, several remain unselected.

**✅ Checkpoint** — candidates ready; nothing selected, read, validated, or installed. Proceed to Step 4 without a user-visible stop.

---

### Step 4: Strategist Phase (MANDATORY in the default pipeline)

🚧 **GATE**: Steps 1–3 complete; no template content in planning context; Stage 1 not started.

**Hard rule — Stage 1 is template-independent**: author every Stage-1 recommendation from the user's request, source facts, conversation constraints, and project-initialization state only; candidate paths, index summaries, template specs/prototypes/assets, and template canvas are not evidence. Template inspection begins only after Stage 1 confirms both the communication contract and the template/free-design choice and any selection is installed.

Load the planning core in one batch, plus the structured facts already in `<project_path>/analysis/`:

```
Read ${SKILL_DIR}/references/strategist.md
Read ${SKILL_DIR}/references/canvas-formats.md
```

| Trigger | Additional Strategist reference |
|---|---|
| Stage 1 confirmed and a Brand/Style/Layout/Deck workspace installed | `references/strategist-template.md` before Stage 2 |
| Confirmed `delivery_context` is recorded/self-running/video, or input is a final/literal narration script | `references/video-design.md` before the three Stage-2 solutions and page roster |

After Stage 1 and the template handoff, load the fixed planning-capability block in one batch before authoring any Stage-2 solution, image recommendation, or roster:

```
Read ${SKILL_DIR}/references/strategist-image.md
Read ${SKILL_DIR}/references/modes/_index.md
Read ${SKILL_DIR}/references/visual-styles/_index.md
Read ${SKILL_DIR}/references/image-renderings/_index.md
Read ${SKILL_DIR}/templates/icons/README.md
Read ${SKILL_DIR}/templates/charts/chart-vocabulary.md
Read ${SKILL_DIR}/templates/tables/table-vocabulary.md
```

This is a capability map, not a usage checklist. Author the three whole-solution intents first, freeze every mode/style/rendering id from the indexes, then read once only the deduplicated union of those detail files; a novel custom reads none. Confirmed non-`none` image sources continue into resource planning under `strategist-image.md` (the image-layout files are Executor's); confirmed `none` writes no image rows but keeps the rendering candidates.

**Fact channels** ([`artifact-ownership.md`](../references/artifact-ownership.md) §1–2): before Stage 1 read `analysis/source_profile.json`'s `decks[]` digests, opening a deck's identity/slide-library files only when raw facts are needed. Content — text, tables, chart values, SmartArt wording — comes from the content-type files in `sources/` (`<stem>.md` and archived `.txt` / `.csv` / `.json` / `.yaml`), never from the digest; `*.conversion_profile.json` and `*_files/image_manifest.json` are sidecars. A source deck's identity is reference, not constraint. If the user provided images, run `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` before the Design Spec and read `analysis/image_analysis.csv` before §VIII; the CSV is a regenerated view of `images/` — rerun after any change, never treat it as a store. Never bulk-open images: Strategist inspects one specifically ambiguous asset under [`strategist-image.md`](../references/strategist-image.md) and records the result in §VIII; Executor inspects one `Existing` / `Sourced` asset only for crop, focal placement, or text contrast.

⛔ **BLOCKING — two-stage confirmation**: the always-on user gate unless explicitly delegated. Stage 1 confirms the communication contract and exactly one template mode (`free_design` or `templates`, the latter expanding the four registered-kind selectors plus supplied roots and requiring at least one selection). Final Stage 2 confirms the complete deck solution plus production mechanics only after the Stage-1 choice is installed or free design is closed; `refine_spec: true` adds one chat gate after Design Spec Gate 1. Author each stage once; submitted values — including blanks and unusual overrides — are authoritative. Only the user confirms: the agent authors recommendations, operates the server, reads state, and applies a template, but never confirms on the user's behalf, automates submission, synthesizes a payload, or writes user result state; silence confirms nothing. Under explicit delegation the agent makes the Stage-1 decision, installs it, derives Stage 2, and presents one complete summary without fabricating UI receipts.

**UI branch** — `template_options.json` (Step 3), `recommendations.stage1.json`, `template_handoff.json` (written only by `--complete-template-selection`), and `recommendations.stage2.json` are agent inputs; `template_selection.json` and `result.json` are user receipts. Only the active unconfirmed stage file may be overwritten, in place, never with a revision suffix or another stage's payload. Author Stage 1 without reading candidates, launch, post the [`confirm-surface.md`](../references/confirm-surface.md) handoff summary, then wait:

```bash
python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon
python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage1
```

**Hard rule — Stage 1 is intermediate**: exit `0` here means continue, not finish — no final reply, no idling. Read `result.json` and `template_selection.json` exactly once (a confirmed contract plus either `free_design` with no roots or `templates` with ≥1 server-resolved root), then in the same run:

1. For `templates`, run [`apply-template-workspace.md`](./stages/apply-template-workspace.md) against every confirmed root (each installs as `templates/design_spec.<kind>.<id>.md` plus real `images/` and `icons/`); for `free_design` skip it. Then bind the state — agent-only, never hand-authored:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --complete-template-selection
   ```
2. Only now inspect installed template state (apply `strategist-template.md` when active), load the planning-capability block, author the three solutions, freeze and read their exact bases, derive the production defaults, and create `recommendations.stage2.json` (`stage: "stage2"`) without changing Stage 1. Wait:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only
   ```
3. Read the complete `result.json` exactly once and retain it through Design Spec authoring; proceed only on `stage: final` + `status: confirmed`. On a non-zero wait this single read decides whether the persisted result succeeded before the chat fallback; a stage-skip result returns to the missing stage.
4. Always release the server:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --shutdown
   ```

If the user selects chat after launch, apply `confirm-surface.md`'s in-run switch and finish every remaining stage in chat without relaunching.

**Chat branch** — present the template mode and Stage-1 contract together and wait for one explicit response (registered candidates shown only when the user chooses `templates`; free design for an ordinary request, template mode for explicit intent or any supplied root, one root preselectable). Create no UI receipts and do not call `--complete-template-selection`. After confirmation, install or fuse selected roots (or close free design), retain that state as the Stage-2 gate, run final Stage 2 in chat, and keep one visible cumulative summary as the final state.

⛔ **GATE — final state → Design Spec → conditional review → lock**: consume every present final value once into the complete, audited `design_spec.md` under [`strategist.md`](../references/strategist.md) §6.2, preserving each field's semantic type (acceptance never turns a Reference or Permission into a Literal) and every production, typography, image-source, and `image_notes` obligation; never reopen `result.json`.

1. Read `${SKILL_DIR}/templates/design_spec_reference.md`; create the complete I–X `design_spec.md` once at the confirmed `design_spec_depth`, without placeholders or `scaffold-*`.
2. Audit it field by field against the retained confirmation — Gate 1.
3. With `refine_spec: true`, run [`refine-spec`](stages/refine-spec.md): review that file in chat, accept arbitrary revisions, touch no lock, stop until explicit approval. Otherwise skip.
4. Read `${SKILL_DIR}/templates/spec_lock_reference.md`; author `spec_lock.md` once from the approved Design Spec and context — identity and refinements, every recurring typography role, routing anchors, each placed image's source/layout suggestion/crop policy; no page-local garnish, no image palette; `strategist-template.md` §3 when active.
5. Compare lock anchors to the Design Spec and run `python3 ${SKILL_DIR}/scripts/project_manager.py validate <project_path>`. Schema validity never proves fidelity: a final-state → Design Spec mismatch, an approved Design Spec → lock mismatch, or an unapplied revision blocks. Repair from the retained confirmation (or the approved revision); resume and refine edit existing files, never scaffolds; only fresh recovery may reread persisted final evidence once. Unhonorable requirements follow [`failure-recovery.md`](governance/failure-recovery.md).

**Confirmation notes**, appended after the stage details in the user's language, each one 💡 line: the split-mode note only when the confirmed mode is `split` or the run is heavy (long page count, bulky sources, substantial research retained in this chat — an isolated `topic-research` worker's fetches do not count) — recommend or confirm stopping after Step 5 and entering the execution session with `继续生成 projects/<project_name>` ([`resume-execute`](stages/resume-execute.md)); no response or "continue" means `continuous`, and the default path prints no reminder. The spec-refinement note always: offer review of the complete Design Spec before the lock (default OFF; only explicit opt-in or `refine_spec: true` runs `refine-spec`).

**Production fields**: resolve Speaker Notes, Custom Animations, and Narration Audio as latest explicit user instruction → final Stage-2 proactive value → default `true` / `false` / `false`; enabled Narration Audio raises a non-explicitly-disabled Speaker Notes outcome and names that dependency. Persist the effective outcomes with provenance as the three rows in `design_spec.md §I`, keep the raw proactive fields as evidence only, and project neither into `spec_lock.md`. A later explicit request updates only its §I outcome and resumes the owning step without reopening Confirm UI; disabling notes while audio stays enabled asks one question (disable audio too, or keep its required notes) before writing either row. Formulas and hyperlinks are §IX content, not confirmation fields or resources: Strategist records the delimiter-free LaTeX body or the exact URI / 1-based slide target, and Executor chooses the realization (text, inline, or block math; inline or whole-object link carrier) under [`native-formula.md`](../references/native-formula.md) / [`native-hyperlinks.md`](../references/native-hyperlinks.md); no manifest or lock entry exists for either.

**Prepared final narration**: when an explicit final/literal script will become notes or audio, follow `video-design.md` §1 and §3 — segment it by scene in Stage 2, give each segment a supporting visible state in §IX, record source and verbatim policy in §X, and after Gate 2 (before Step 5 or the split handoff) write the exact segments once to `notes/total.md`, split only in Step 7.1.

**Output**: `design_spec.md`, `spec_lock.md`, and `notes/total.md` only on the narration branch.

**✅ Internal checkpoint** — facts read; confirmation consumed once; production fields, mathematics, per-page `Relationships`, and §VIII resource jobs resolved; Gate 1 passed; refinement approved when enabled; lock derived; split handling resolved; every §IX `Audience move` present. Do not print; auto-proceed.

---

### Step 5: Image Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; `design_spec.md` and `spec_lock.md` exist (otherwise stop under [`failure-recovery.md`](governance/failure-recovery.md) §3).

**Trigger**: §VIII has at least one `Acquire Via: ai`, `web`, or `slice` row, or a pending derivative declared by `Reference: Derived from <canonical bare filename>; treatment=...`. Prepared-user-only plans and `placeholder` rows do not trigger it; a permitted but unused source creates no row. If §VIII omits a source, asset, or page role that `image_notes` explicitly requires, return to Step 4 Gate 1 and repair from the retained final state.

```
Read ${SKILL_DIR}/references/image-base.md          # always
```

| Row | Additional reference | Run |
|---|---|---|
| Prepared derivative | `image-generator.md` §4.4 only for registered layers | after its canonical source is terminal: `python3 ${SKILL_DIR}/scripts/image_treat.py ...` for blur, desaturation/grayscale, duotone, brightness, or contrast, or the §4.4 preparation path |
| `ai` | `image-generator.md` | write `images/image_prompts.json`, render `image_prompts.md` with `image_gen.py --render-md`, then follow §7 Path Selection — `image_gen.py --manifest` is Path A only, `host-native` is Path B and skips `--manifest`, `manual` writes prompts and stops; the recorded `design_spec.md §I` path wins over `IMAGE_BACKEND` |
| `web` | `image-searcher.md` | `python3 ${SKILL_DIR}/scripts/image_search.py ...`; with ≥2 rows write `images/image_queries.json` and run `--batch` once |
| `slice` | `image-generator.md` §4.3 | after the parent sheet is `Generated`: `python3 ${SKILL_DIR}/scripts/slice_images.py <project_path>/images/<sheet>.png --grid RxC --names ... --trim --alpha --bg KEY_HEX_FROM_PROMPT --strict-alpha` |
| `user` / `placeholder` | — | skip |

Load only the references the rows need; a mixed deck writes both `image_prompts.json` and `image_sources.json`. The positional `image_gen.py "prompt"` form is for out-of-pipeline fixups and the §4.4 reconstruction derivation only.

**Web selection**: when any vision-capable context exists, add `--save-candidates` with explicit `query_variants` and run [`web-image-review`](stages/web-image-review.md); only a stage-selected candidate is promoted with `--promote`, a row advances to `next_candidate_page` before its query changes, and only an exhausted pool returns it to `Pending` with new variants. Without vision, omit `--save-candidates`: best-only mode downloads a strict metadata-verified candidate (`selection_method: metadata-ranked`) or stops at `Needs-Manual`. Only after normal search is exhausted may a vision-capable owner fetch one [`topic-research`](stages/topic-research.md) `source_url` as a reviewed source package. §VIII `Reference` stays the locked intent; the provider query is authored separately.

🚧 **Exhausted-automation GATE**: `auto` tries Path A then Path B and never silently enters Offline Manual. When both are exhausted, or a confirmed `api` / `host-native` path stays unavailable after retry, ask whether to repair and retry the same path, generate the listed files manually, or cancel the affected AI images and repair the plan; only confirmed `manual` creates `Needs-Manual` rows. Web failures follow [`image-base.md`](../references/image-base.md) §3 without halting: try materially different query/provider/license strategies, then mark `Needs-Manual`, report, and continue.

**Workflow**:

1. Extract §VIII rows; separate derivative rows first (reject source/output equality, a derivative parent, chains, cycles, self-reference), then group canonical rows by `Acquire Via`. Every Pending/Failed row reaches a terminal state before Executor starts.
2. Generate prompts and/or run search per [`image-base.md`](../references/image-base.md) §1.
3. Slice each generated sheet with its grid, `--names`, and the exact key HEX from its prompt; a `slice` row is `Generated` only after exit 0, a strict keying failure writes no replacement outputs and returns the sheet to preparation, and a `Needs-Manual` sheet leaves its slices `Needs-Manual` for the Step 7 gate.
4. Materialize derivatives from their terminal source under the declared treatment only (`image_treat.py` for per-pixel treatments; §4.4 for registered clean-base/layer work — supplied assets are `user / Existing`, generated ones `ai / Generated`). A standalone cutout is prepared RGBA, a flat-key slice, or host-supplied. Never bake crop/clip, rotation/mirror, opacity, frame, shadow, scrim/wash, vignette, or overlap into a bitmap, never present `image_treat.py` as background removal, and copy a web source's license record to its derivative.
5. Verify every row's terminal status under [`svg-image-embedding.md`](../references/svg-image-embedding.md) — no `Pending`, `Failed`, or `Needs-Selection`; `auto` follows its fallback chain, confirmed `api` / `host-native` retries only that path, and an unresolved Default AI row waits at the gate above.
6. `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` so the CSV reflects every placeable image.

**✅ Internal checkpoint** — sidecars, slice outputs, terminal statuses, refreshed CSV. Do not print. Auto-proceed to Step 6; only `generation_mode: split` prints the handoff and stops this conversation:

```markdown
## ✅ Planning Session Complete
- [x] Spec: `design_spec.md`, `spec_lock.md`
- [x] Resources: `sources/`, `images/`, `templates/`
- [ ] **Next**: open a fresh chat window and input `继续生成 projects/<project_name>` to enter the execution session via the [`resume-execute`](stages/resume-execute.md) stage.
```

---

### Step 6: Executor Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete.

```
Read ${SKILL_DIR}/references/executor-base.md              # REQUIRED core: execution rules, device menu, everyday effects, module triggers
Read ${SKILL_DIR}/references/shared-standards-core.md      # REQUIRED core: SVG contract + shared aesthetic/leading baseline
Read ${SKILL_DIR}/references/semantic-svg.md               # REQUIRED core: semantic metadata boundary
Read ${SKILL_DIR}/references/preset-shape-vocabulary.md    # REQUIRED core: complete 187-name preset vocabulary
Read ${SKILL_DIR}/references/modes/<resolved-id>.md        # one preset id, or each `mode_references` id
Read ${SKILL_DIR}/references/visual-styles/<resolved-id>.md # one preset id, or each `visual_style_references` id
# Triggered modules — evaluate every trigger over the §IX roster before P01 and read the triggered ones now, in this batch;
# a page reaching a capability the sweep did not foresee reads its module then (executor-base routing table):
#   executor-structure.md + topology-assembly.md      first `Structure = yes` page
#   native-shape-authoring.md                         first contour beyond rect / roundRect / circle / ellipse / line, or a Boolean / freeform
#   svg-effects.md                                    first visual job beyond the everyday block
```

Read the core as one batch with the exact detail files named by the retained `spec_lock.md`, then every module the roster sweep triggers, in the same batch (each page's module line records what it uses; a capability the sweep did not foresee loads at that page); never reopen the planning indexes, infer adjacent bases, glob a catalog, or blend unselected identities (an unreferenced custom follows its behavior alone). Conditional modules load on [`executor-base.md`](../references/executor-base.md)'s routing table, never by analogy; `video-design.md` is read before the first SVG when §I records recorded/self-running/video delivery or §X a literal script. `executor-structured.md` owns template specs and prototypes; `executor-visualization.md` resolves a selected reference to one SVG plus its family branch. Read each reference once per valid context.

**Context validity**: reuse the retained Design Spec and lock for every page while the context is unchanged and uncompacted; do not reread or poll them. A fresh, resumed, restarted, compacted, or externally changed context rereads `design_spec.md`, then `spec_lock.md`, once, plus triggered references and the latest completed SVG when mid-deck ([`failure-recovery.md`](governance/failure-recovery.md)); on local uncertainty consult the retained lock, then only the owning Design Spec fragment — sources supply facts only, and the Design Spec wins a conflict. A bounded same-context repair that preserves roster/order/identity/communication needs only the affected fragment readback plus `project_manager.py validate`. **Five-page lock re-read**: after P05, P10, P15, … when another page follows, read `spec_lock.md` in full once before the next page — a pure re-anchor of palette, typography, icon style, and `page_rhythm` under long context, with no checker run, no output, no pause, and no repair loop; an external change found here follows the recovery branch. **Hard rule — exact page roster**: `design_spec.md §IX` is the ordered queue — one final slide per entry, same id and order; never add, drop, merge, split, or reorder while drawing. A continuous run may first repair the affected §IX blocks and `page_rhythm` rows and rerun `validate` while the count stays inside the Stage-1 confirmed range; leaving that range reconfirms Stage 1. §IX is preferred wording and semantic authority, adapted only under `executor-base.md` §2.1's content-vs-expression contract, with sources read only for verification. **Missing `spec_lock.md` or `design_spec.md`** → stop and report the missing gate artifact; recover through [`failure-recovery.md`](governance/failure-recovery.md) §3; a missing field in an existing lock → its §2. When §X records a literal script, read the frozen `notes/total.md` once before P01 and design each visible state around its segment. Trust the latest `analysis/image_analysis.csv` (rerun `analyze_images.py` if `images/` changed; an empty folder means no inventory). `page-context` is a diagnostic only ([`artifact-ownership.md`](../references/artifact-ownership.md) §1).

**Design Parameter Confirmation (Mandatory)**: before the first SVG, output one confirmation listing the compact communication objective, canvas dimensions, body font size, color scheme (primary/secondary/accent HEX), font plan, the per-role calibration table from `python3 ${SKILL_DIR}/scripts/text_measure.py calibrate <project_path> --outline` (every lock role: family, size, CJK and Latin ≈ chars per 100 px, and the longest planned §IX line per role in px — the checker's own estimator with wrapping headroom, written to `validation/text_calibration.json`), and the live-preview URL from the launcher below. If the preview failed to launch, say so here rather than proceeding silently.

**Live Preview Auto-Startup (Mandatory)**: before the first SVG, start the editor and keep it running through Step 7:

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live --daemon
```

Default first free port from `6060` (`--port N` binds strictly); read the URL from output or `<project_path>/live_preview/lock.json` and report it — or the launch failure — before the first SVG. It is a side process: never wait for it or for user confirmation, and keep it running until the user clicks **Exit preview** or asks in chat. Do not read or apply submitted annotations during generation; that window opens after Step 7 ([`live-preview.md`](stages/live-preview.md), which also describes staged direct edits).

> ⚠️ **Main-agent only**: SVG generation stays in the current main agent — page design depends on full upstream context. Cadence: P01 → first-page gate → remaining pages → final gate, in one context, no batches or other mid-run checker calls; reload under Context validity above after context invalidation.

**Visual Construction Phase**: generate pages sequentially into `<project_path>/svg_output/`. Each SVG carries the slide's complete visible design (a JSON-first Chart/Table is the sole exception: inline JSON authoritative, visible subtree an approximate preview). Native shapes follow [`native-shape-authoring.md`](../references/native-shape-authoring.md), loaded at the first contour beyond basic primitives while the preset vocabulary is read before page one: independent atoms first, Merge Shapes only when contour semantics require it, freeform last. `mirror|layout` pages start from the complete `page_layouts` SVG and preserve inherited visuals, root identity, atoms, and slots (strict keeps the contract; `layout` may reflow carrier text inside unchanged slot bounds; adaptive uses a Strategist-declared Layout; a required atom or slot change returns upstream, and Executor never edits `spec_lock.md`); `style`, free-design, and brand-only pages are flat per `executor-base.md` and [`semantic-svg.md`](../references/semantic-svg.md).

**Motion-ready image composition**: only when an explicit user motion instruction, an enabled Custom Animations outcome in §I, or an existing `animations.json` activates custom motion, evaluate §IX `Motion suggestion` rows and author any in-slide image states or cross-slide continuity now under [`executor-image.md`](../references/executor-image.md), each revealable or continuing Slide-local unit in a descriptive direct-root `<g id>`. Effects, pairing, order, and timing stay in the custom stage after the final gate; a suggestion alone activates nothing; deterministic Morph needs the continuing object as a direct-root group on both pages.

**First-page gate (Mandatory)** — after the first SVG, before page 2:

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --canonical-authoring --stage first-page --json
```

Run unfiltered, review the complete P01 issue set, fix every blocking error plus selected warnings in one consolidated pass, verify once; a still-failing verification is the next batch. If terminal output is truncated, read only the issue arrays from `validation/svg_quality_first_page_report.json`. The gate validates the method, not just the page — emit one line before editing:

```
gate-signal: method=<rule resolved, or none> | page-local=<count> | not-exercised=<list>
```

| Signal | Reading |
|---|---|
| Two or more issues share a category and direction | Method-level bias — resolve to the authoritative rule before P02 (for text extents: correct the per-role calibration table — rerun `python3 ${SKILL_DIR}/scripts/text_measure.py calibrate <project_path> --outline` or add the missing `--role` — then every later page estimates by that arithmetic and measures nothing); a correction fitted to the observed offset patches only this sample |
| One isolated issue tied to this page's structure | Page-local — fix and continue |
| A recurring element appears for the first time (furniture, caption format, section numbering, accent discipline) | It will be copied to every later page — confirm its semantics now |

`not-exercised` names what P01 could not test (a cover typically omits multi-line text, columns, charts, captions, data objects); carry each resolved rule forward as arithmetic. Every later page runs without checker calls; a listed item first exercised later is held to the carried-forward rule and caught by the final gate.

**Quality Check Gate (Mandatory)** — only after every planned SVG exists, before annotations and speaker notes:

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --canonical-authoring --stage final --json
```

- Before the gate, every §IX `Native-ready` `<object-key>=yes` has its draw-time marker group and JSON child; `=no` and incidental microvisuals stay ordinary SVG (a legacy bare `yes|no` is readable only when the page has exactly one eligible object). JSON-first Chart/Table validates inline schema/bounds; SVG-first markers need a current `data-pptx-fallback-sha256`, stamped after synchronization — missing or stale baselines block canonical/native export, not fallback export.
- Run unfiltered against `svg_output/` (never after `finalize_svg.py`, which masks violations); one run reports every page. On failure review all `blocking` errors and advisory warnings, fix every error plus the selected warnings in one consolidated pass, verify once; never check between individual fixes. If output is truncated, extract only `categories.blocking.issues` (and `categories.introduced.issues` when needed) from that run's `validation/svg_quality_report.json`, where `inherited` and `source-import` are provenance and `introduced` holds changed/new warnings.
- Every `warning` is advisory — no mandatory modification, no auto-normalizing user syntax, no disposition line; structured-template warnings (empty/framing-only Layout, bare Master, duplicate layout keys) guide optional cleanup only. A condition that must be corrected before release is an `error`.
- **Hard rule — token-safe report handling**: on success use the exit status and terminal summary; never `cat` the complete JSON into context. Read it only for failure investigation, an explicit audit, or a field absent from stdout.

**Mandatory — final carrier-receipt review**: compare the checker's `[CARRIERS]` summary (detail under `files[].info.carrier_receipt`) with the retained page jobs, resource roles, and running geometry signatures. Counts and diversity are not quotas; when the facts contradict an active decision — an adopted preset absent, a directional / step / flowchart relationship drawn as a hand path or polygon where `executor-base.md` §3.0 names a preset, a primary image reduced to a minor frame, unrelated jobs collapsing to one neutral construction — read only the affected rows, repair those pages in one pass, and rerun the final checker. **Absence needs a reason**: when the receipt shows a deck-wide zero — `Presets: (none)`, or `inline emphasis 0`, `gradients 0`, or `filters 0` on the `Effects:` line — or fewer pages carrying a preset or connector than pages whose §IX `Relationships` line names `order` / `link` / `parent` / `membership`, answer one line per absent family or per such page: what carries that job instead, and why it serves the reader better — for presets, one line per job the family serves, not for arrows alone: direction and sequence (arrows, chevrons, flow nodes), grouping and ownership (brackets, braces, frames, plaques), emphasis and annotation (callouts, badges, banners, stars). The style, speed, restraint, "text was enough", or "it is editable anyway" are not answers; a family or page without one is repaired where the page job calls for it, then the checker reruns. Choosing not to use a device is valid — only an unstated reason is not.

**Logic Construction Phase (conditional)**: when the effective Speaker Notes outcome in §I is enabled, load [`executor-notes.md`](../references/executor-notes.md): validate a frozen `notes/total.md` against every information-bearing final SVG group (repair the page or the plan, never the script), or otherwise ground each page's narration in its final SVG and write `notes/total.md`. When disabled, load nothing and create no notes.

**✅ Internal checkpoint** — preview launched in time, P01 method gate, uninterrupted remaining pages, consolidated repair, exact §IX coverage, one-frame prose, final checker 0 errors, `notes/total.md` only when enabled. Do not print. Then run the applicable conditional gates and proceed to Step 7.

> **Chart pages?** Run [`verify-charts`](stages/verify-charts.md) before Step 7 to calibrate coordinates; skip without chart pages.
>
> **Visual self-check (opt-in)?** Run [`visual-review`](stages/visual-review.md) before Step 7 only when the user explicitly asked for a per-page visual re-pass ("跑一下视觉自检 / 视觉回看", "visual review", "check pages visually"); never by default, on inferred model capability, or on deck size.
>
> **Motion execution (conditional)?** An existing `animations.json` always runs [`customize-animations`](stages/customize-animations.md) before export. Without a sidecar, run it only for an explicit per-slide/per-object request or an enabled Custom Animations outcome in §I (§IX suggestions inform it, never trigger it); a deck-wide request loads [`animations.md`](../references/animations.md) and resolves Step 7.3 flags instead; otherwise keep `fade` / `none` and load nothing. Executor owns effects, options, order, timing, and simplification to `none`; never add motion for coverage. Sound is never a Strategist resource: no id or path in `design_spec.md` / `spec_lock.md`, and any cue is selected only after the motion solution is final under `animations.md` §2.2.

---

### Step 7: Post-processing & Export

🚧 **GATE**: Step 6 complete — every final page in `svg_output/`, all conditional gates passed, final report 0 errors, and `notes/total.md` covering every page when Speaker Notes is enabled.

🚧 **Image readiness GATE**: when any required row is `Needs-Manual`, every expected file and slice output must exist under `images/` before the first Step 7 command. If any is absent, pause and list the exact filenames; never run `finalize_svg.py` or `svg_to_pptx.py`, never ship the dashed placeholder. When the files arrive, rerun `analyze_images.py`, replace each placeholder, reconcile every `no-crop` container to the measured native ratio, and rerun the final checker (which then closes each terminal §VIII row through `spec_lock.md images`, the exact file, and a real `<image href>`, and validates Sourced provenance, visible credits, and per-placement pixel scale under `meet` / `slice` / `none`).

**Hard rule — strict serial commands**: one command at a time, each in its own invocation; enter the next sub-step only after the current one exits successfully and its success criterion holds. On failure, repair the owning source artifact and resume from the failed sub-step ([`failure-recovery.md`](./governance/failure-recovery.md)); never restart planning unless its source changed.

#### Step 7.1 — Split Speaker Notes (only when enabled)

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Success criterion**: per-slide Markdown files under `notes/` cover every published slide. When disabled, skip to 7.2.

#### Step 7.2 — Build the Self-Contained SVG Preview

```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Success criterion**: `svg_final/` holds one self-contained preview per slide. Its absence never blocks 7.3.

#### Step 7.3 — Export the Native PPTX

| Effective decision | Command |
|---|---|
| Speaker Notes `enabled` | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>` |
| Speaker Notes `disabled` | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --no-notes` |

Append `--native-charts-and-tables` only for an explicit editable Chart/Table delivery decision (markers, templates, semantic tables, and imported charts never activate it; formulas are always native). Motion: with a preserved or produced `animations.json`, keep the base command — the exporter reads the sidecar; append the resolved [`animations.md`](../references/animations.md) flags for a deck-wide setting — explicit flags override the corresponding sidecar default/slide fields while group overrides remain; an explicit Custom Animations disable keeps the sidecar and appends `-a none`, an explicit all-motion disable uses `--no-animations`, and final Stage-2 `false` does neither. Sound: after the motion solution is final, run the optional pass in `animations.md` §2.2 — no cue creates no `sounds/`; a selected cue is synced with `sound_sync.py` (never read from `templates/sounds/` directly) and referenced from the validated sidecar. For a narrated MP4, [`generate-audio`](stages/generate-audio.md) owns the delivery choice; do not add `--conversion-trace` to every base export; an explicit `--conversion-trace <path>` writes to that destination instead of the default.

**Success criterion**: the command exits 0 and produces `exports/<project_name>_<timestamp>.pptx`, `validation/<project_name>_<timestamp>.report.json` with `passed` or `passed-with-warnings`, and `validation/<project_name>_<timestamp>.trace.json` when `--conversion-trace` was enabled. The exporter itself requires the current matching `final` quality report and exits nonzero on a missing, unreadable, unsupported, non-final, blocking, stale, or unverifiable one. Read the compact `[POSTFLIGHT]` receipt (`status`, `quality_gate`, slide count, warning counts, paths), disclose material warnings, and never `cat` the full report on success. Retain the report path for a later `deck_motion` handoff; postflight proves the package, not a later MP4 audio track.

## ✅ Generate PPTX Complete

- [x] Image readiness gate passed
- [x] Carrier receipt compared with the retained page decisions; contradictions repaired without treating counts as quotas
- [x] Notes split when enabled; disabled exports used `--no-notes`
- [x] `svg_final/` preview built
- [x] Native PPTX published and postflight report written
- [ ] **Next**: report the exported PPTX path; when the effective Narration Audio outcome in `design_spec.md §I` is enabled, run [`generate-audio`](stages/generate-audio.md); otherwise run a supporting post-export stage only on its explicit trigger
