# Confirm UI — Template Selection and Strategist Confirmation Page

> The interactive surface for [`generate-pptx`](../../workflows/generate-pptx.md)
> Conditional Step 3 template selection and Step 4 Strategist confirmation.
> Step 3 exists only for explicit template discovery/selection, an exact
> workspace root, or a current Create Template handoff; selected workspaces are
> applied before Stage 1. Ordinary free design starts at Stage 1. Stage 1
> confirms the open communication brief, and final Stage 2 confirms the
> coordinated deck solution plus production mechanics—including editable prose
> for **how** to apply an installed template. When triggered, template selection
> persists separately in `template_selection.json`; Strategist values accumulate
> into `result.json`. The chat path mirrors the same active phase boundaries.

## Authority and Scope

| Concern | Owner |
|---|---|
| Step 3 template-selection gate and installation order | [`generate-pptx.md`](../../workflows/generate-pptx.md) |
| Template option/selection schema and page transport | This document |
| Step 4 gate and pipeline order | [`generate-pptx.md`](../../workflows/generate-pptx.md) |
| Confirm UI schema | This document |
| Stage 1 / final Stage 2 field membership | This document |
| Server launch / wait / shutdown behavior | This document |
| Port and lock behavior | This document |
| Chat fallback equivalence | This document |
| Confirmed-value precedence | [`generate-pptx.md`](../../workflows/generate-pptx.md) plus this document's `result.json` contract |

**Hard rule**: Keep detailed Confirm UI behavior here. The Generate route may summarize orchestration, but it should not duplicate the full JSON schema, catalog behavior, or launcher lifecycle.

**Mandatory surface decision — before a triggered Step 3 or any UI command**: Resolve the most recent
explicit confirmation-surface instruction for this run before running
`--daemon` or `--wait-only`. Unrelated later messages do not reset the selected
branch. A new explicit selection may change it before launch; once confirmation
starts in chat or UI switches to chat, keep chat for the rest of this run.

| Most recent explicit surface instruction | Branch |
|---|---|
| The user explicitly delegates confirmation | Present one complete two-stage summary plus the template choice when Step 3 is triggered. Do not launch the page or fabricate UI receipts. |
| Otherwise, the user asks for or agrees to personally confirm in chat, or declines the confirmation page | Use chat for both Strategist stages and any triggered Step-3 selection. Do not launch the page, run `--wait-only`, or require UI-authored receipts. |
| No explicit confirmation-surface instruction exists for this run | Use the page as the default. |

Interpret the instruction semantically: “confirm here”, “use the chat window”, or
“do not open the confirmation page” are sufficient; no literal `chat-only`
keyword is required. Invoking a chat-question tool by itself does not select the
chat branch—the user's instruction does. Both branches preserve the same
two-stage Strategist confirmation and, when triggered, the independent template
choice that precedes it.

**Fallback rule**: When no surface was selected before launch, the page is the
default. Use chat when the user answers either always-on handoff in chat, or
after launch failure/timeout and one re-check of the receipt for the active
phase (`template_selection.json` for a triggered Step 3, `result.json`
otherwise). A
chat-question tool alone is not a launch failure. Preserve template selection
as an independent choice and keep Stage-1 prompts open-ended.

**In-run UI → chat switch — any phase or stage**: If the user explicitly selects chat
after the UI server has launched—while `--wait-only` is active, before that wait
starts, or after it times out while the server remains live:

1. If a wait is active, interrupt it and confirm that its process has exited.
   Only the return code from this deliberate wait interruption is expected to
   be non-zero.
2. Run `server.py <project_path> --shutdown` and require that cleanup to
   succeed. The browser tab may remain open, but its stopped server makes it
   inactive.
3. Re-check the active receipt once: `template_selection.json` during Step 3,
   otherwise `result.json`. Retain only values persisted before shutdown; an
   unsubmitted browser draft is not confirmed.
4. Continue the unresolved current phase/stage and everything remaining in chat. Do
   not call `--wait-only` again, recover the server, or relaunch the page during
   this run.

**Triggered Step-3 chat handoff**: After writing `template_options.json`, launch
the healthy daemon without `--wait`. Immediately post its actual URL plus a
compact localized summary: free design is available; the page has one
single-select dropdown for each registered kind plus one for supplied exact
roots; registered options come only from the four kind indexes; and every
supplied exact root is shown as a library or explicit candidate according to
exact canonical-root equality. End
with a localized line saying the user may select on the page or reply in chat
with free design / exact roots if the page did not open. Only then run
`--wait-only --wait-stage template`. Silence confirms nothing.

**Always-on Stage-1 chat handoff**: After a triggered Step 3 closes and any
template is installed—or immediately for ordinary free design—write
`recommendations.stage1.json`. Reuse the live Step-3 page when present;
otherwise launch the page directly. Immediately post the actual URL plus one
compact, localized summary of the current Stage-1 recommendations: audience, communication intent,
audience outcome, core message, delivery context, artifact afterlife,
`content_divergence`, and canvas. Show a blank as “not specified” without
changing its value. End with an explicit localized line saying that, if the
page did not open or cannot be reached, the user may reply “continue with these
recommendations” or revise the same items directly in chat; the same two-stage
flow will continue. Only then run `--wait-only --wait-stage stage1`. A chat
reply to that handoff applies the in-run switch above without waiting for
timeout. The handoff is context, not confirmation, and silence confirms
nothing. After launch failure/timeout and the required result re-check, present
the same items as open Stage-1 chat questions and wait for an explicit response.

## `confirm_ui/server.py`

The following launch and wait commands belong to the **UI branch only**:

```bash
python3 scripts/confirm_ui/server.py <project_path> --daemon         # launch triggered Step 3, or launch ordinary free-design Stage 1
python3 scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage template # Step 3 selection
python3 scripts/confirm_ui/server.py <project_path> --complete-template-phase # after free-design closure / template install
python3 scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage1  # Stage 1
python3 scripts/confirm_ui/server.py <project_path> --wait-only       # current final Stage 2
python3 scripts/confirm_ui/server.py <project_path> --daemon --port 5051
python3 scripts/confirm_ui/server.py <project_path> --no-browser
python3 scripts/confirm_ui/server.py <project_path> --timeout 0   # disable idle auto-shutdown
python3 scripts/confirm_ui/server.py <project_path> --reset-template-phase # clear prior Step-3 artifacts before a fresh UI run
python3 scripts/confirm_ui/server.py <project_path> --shutdown    # Step 4 cleanup (idempotent)
```

- Without `--port`, binds the first free port from `127.0.0.1:5050`; the launch log prints the actual URL. `--port N` is exact and fails when unavailable. Auto-open is suppressed by `--no-browser`.
- In `--daemon` mode the launcher starts the child with browser opening suppressed, then accepts readiness only when `GET /api/health` identifies this confirm service, project, and child process. It opens the printed `http://127.0.0.1:<port>` URL only after that check.
- Confirm UI and live preview prefer the same memorable base port but keep separate processes and project-local locks (`.confirm_ui.lock` vs `live_preview/lock.json`). Normal Step 4 cleanup releases the confirm port before Step 6; concurrent projects may use different ports.
- `--daemon` starts the Flask process in the background and returns after the health check. A triggered template run first uses it for the Step-3 handoff and keeps the same process live; ordinary free design launches it only after Stage-1 recommendations exist. The current Strategist flow then spans Stage 1 and final Stage 2. `--daemon --wait --wait-stage template` remains a combined form for the triggered phase. The wait budget defaults to **590 s** (`--wait-timeout`); on timeout the detached server remains live, and the caller re-checks the active receipt once before chat fallback.
- `--wait-only` attaches to the page opened by `--daemon` and blocks until the requested receipt. If it is already persisted, the command returns before recovery, so a fast submit between launch, chat handoff, and wait is not lost. Otherwise, if the recorded server died, it restarts on the recorded/default port. Use `template` only for triggered Step 3, `stage1` for the communication contract, and the default/final wait for final Stage 2. Strategist resume derives its target from persisted `result.json`; template resume derives it from `template_selection.json`.
- `--complete-template-phase` is agent-only. It validates the current selection and writes the bound `template_handoff.json`; template mode additionally requires project-local `templates/design_spec.md`. Run it before writing Stage 1. `--reset-template-phase` removes exactly `template_options.json`, `template_selection.json`, and `template_handoff.json`; it does not alter Strategist files, installed template content, or `result.json`.
- `--shutdown` stops a confirm server left running for this project and exits — **idempotent** (a no-op when nothing is running). Tries a graceful `/api/shutdown`, falls back to killing the recorded pid, then clears the lock. Generate Step 4 runs this on every path so the selected port is released before live preview starts.
- Every fresh UI run starts with `--reset-template-phase`. A triggered Step-3 run then writes valid `<project_path>/confirm_ui/template_options.json`; ordinary free design leaves all three template-phase artifacts absent and launches from the current Stage-1 recommendation. After template selection, the same service exposes Stage 1 only when the selection is newer than those options, the matching handoff is newer than that selection, and the Stage-1 recommendation is newer than the handoff. `--shutdown` needs neither input.
- Per-project lock at `<project_path>/.confirm_ui.lock` — duplicate launches are refused; stale locks (dead pid) are overwritten.
- Idle auto-shutdown after 900 s by default; `/api/shutdown` exits gracefully and releases the lock.
- `/api/template-options` serves the server-built Step-3 catalog and `/api/template-confirm` accepts only current candidate keys, then writes the trusted receipt. `/api/recommendations` and `/api/confirm` own only the later Strategist stages and strip legacy `template_reuse_scope` / `template_adherence` fields. The completed template handoff is authoritative: `free_design` also strips a stray `template_application`, while `templates` exposes that editable natural-language field in Stage 2.

Dependency:

```bash
pip install flask
```

## Conditional Step-3 template-selection contract

When triggered, template selection is a separate pre-Strategist phase. Its files live under
`<project_path>/confirm_ui/` but never enter `result.json`.

### Input — `template_options.json` (created before launch)

```json
{
  "schema_version": 1,
  "phase": "template",
  "lang": "zh",
  "explicit_workspace_roots": [
    "/absolute/path/to/a/project-or-template-workspace"
  ]
}
```

- `schema_version` is exactly `1`; `phase` is exactly `template`.
- `lang` is optional, but when present it is a non-empty UI-language string.
- `explicit_workspace_roots` is required even when empty. Every item is a
  unique absolute path resolving to an existing directory with
  `templates/design_spec.md` or compatible legacy `design_spec.md`.
- The array supplies candidates for the one specified-root dropdown; it does
  not authorize selecting several explicit roots in one confirmation.
- Do not write library entries into this file. The server reads only
  `templates/brands/brands_index.json`,
  `templates/styles/styles_index.json`,
  `templates/layouts/layouts_index.json`, and
  `templates/decks/decks_index.json`, derives each direct-child workspace root,
  and validates that it exists with `templates/design_spec.md`. It never scans
  kind directories.

`GET /api/template-options` returns the browser catalog:

```json
{
  "schema_version": 1,
  "phase": "template",
  "lang": "zh",
  "library": {
    "brand": [],
    "style": [],
    "layout": [],
    "deck": []
  },
  "explicit": [],
  "preselected_keys": [],
  "options_sha256": "<64 lowercase hex characters>"
}
```

A library candidate has `key`, `source: "library"`, `kind`, `id`, `label`,
`summary`, and canonical absolute `workspace_root`. An unregistered explicit
candidate has `key`, `source: "explicit"`, parsed `kind`, `label`, and
canonical absolute `workspace_root`. If a supplied root exactly equals a registered canonical
root, the server reuses the library candidate/key instead of duplicating it as
explicit. Candidate keys are server-owned; the page posts only
`{ "mode": "free_design"|"templates", "selection_keys": [...] }` to
`POST /api/template-confirm`.

When the input supplies exactly one root, `preselected_keys` contains its
resolved candidate key as a convenience default, including when exact equality
reclassifies it as library. When several roots are supplied, all remain
candidates but none is preselected; one specified-root dropdown cannot encode
an instruction to use all of them.

**Page selection model**: The first control is exclusive free design. Below it,
Brand, Style, Layout, and Deck each have one registered single-select dropdown,
and Specified has one explicit-root single-select dropdown. Every dropdown
starts with `None`. Selecting any template exits free design; selecting free
design clears all dropdowns. The registered kinds may be combined, but each
contributes at most one root and the specified channel contributes at most one.
The server enforces the same limits. Because an explicit candidate carries its
parsed kind, it may coexist with one registered root of that kind and enter the
two-workspace same-kind conflict gate. Source provenance never grants priority.

### Output — `template_selection.json` (written on confirmation)

```json
{
  "schema_version": 1,
  "phase": "template",
  "status": "confirmed",
  "mode": "templates",
  "selections": [
    {
      "source": "library",
      "kind": "style",
      "id": "example_style",
      "workspace_root": "/canonical/library/root/example_style"
    },
    {
      "source": "explicit",
      "kind": "deck",
      "workspace_root": "/canonical/unregistered/workspace/root"
    }
  ],
  "options_sha256": "<64 lowercase hex characters>",
  "selection_sha256": "<64 lowercase hex characters>",
  "confirmed_at": "2026-08-04T12:00:00"
}
```

`mode: "free_design"` requires `selections: []`; `mode: "templates"` requires
at least one selection. Roots are unique canonical absolute paths. A library
selection contains exactly `source`, `kind`, `id`, and `workspace_root`; an
explicit selection contains exactly `source`, `kind`, and `workspace_root`.
There is at most one library selection per kind and at most one explicit
selection overall; cross-kind composition remains valid, and one explicit plus
one library selection may share a kind. The browser
cannot submit arbitrary paths because the server resolves posted keys against
the catalog it just built. `options_sha256` binds the receipt to the current
input, four index files, and resolved candidates. `selection_sha256` binds the
mode and canonical sorted selections to that option hash. Every receipt read
rebuilds the catalog and rejects option/index drift.

After `--wait-only --wait-stage template` returns, Generate reads this receipt
once. Free design skips installation but still completes the agent handoff
below before Stage 1. Template mode runs `apply-template-workspace` against all
selected roots, waits for complete project-local installation/fusion, and only
then completes that handoff. Step 3 resolves only template-to-template segment
ownership and installation; it does not evaluate current-project fit.
Strategist never reads the source roots.

### Agent handoff — `template_handoff.json`

After free design closes or template installation succeeds, run:

```bash
python3 scripts/confirm_ui/server.py <project_path> --complete-template-phase
```

The command writes, and agents must not hand-author:

```json
{
  "schema_version": 1,
  "phase": "template",
  "status": "ready",
  "mode": "templates",
  "selection_sha256": "<64 lowercase hex characters>",
  "completed_at": "2026-08-04T12:01:00"
}
```

The handoff must match the current valid selection. Template mode also requires
`<project_path>/templates/design_spec.md`; free design requires no installed
spec. Write `recommendations.stage1.json` only after this command succeeds, so
its file time is no earlier than the handoff.

## Field shapes

The following fields belong to the Strategist stages, not to any triggered
template-selection receipt.

- **Enumerable + custom** — canvas / icons retain blank manual inputs; mode / visual_style instead show a mandatory AI-authored proposal in full, initially unselected and editable after selection. Selected mode / style writes literal `custom` plus its behavior sibling.
- **Visual examples for hard-to-name choices** — the full-screen confirmation page loads real SVG page samples from `static/style_previews/` for `visual_style`, and renders real sample SVGs from `templates/icons` for `icons`. These thumbnails make style and icon-library choices visually comparable before the user locks them. Preview copy is fixed role text (big title / section title / body / points), not project content from recommendation files, so users compare visual treatment rather than copywriting. These previews are a confirmation aid only: they do not add fields to recommendation stage files or `result.json`, and they do not replace the later Step 6 live preview.
- **Image usage multi-select** — image sources are selected as one or more catalog ids: `ai` = AI-generated, `web` = Web-sourced, `provided` = User-provided, `placeholder` = Placeholder, `none` = No images. `none` is exclusive. A confirmed non-`none` set is the allowed acquisition-source boundary, not a requirement to use every selected source; only explicit `image_notes` wording can require a source, asset, or page role. Recommendation and result values may be a legacy single string, but new files should use an array. When several sources are recommended, write the source ids to `recommend.image_usage` and write the actual usage strategy to `image_notes`, not a custom prose value.
- **Closed enumerable** — PPT reading mode (`delivery_purpose` compatibility key), formula policy / generation mode / refine spec, plus AI source only when image usage includes `ai`. These have no Custom box; out-of-catalog values snap back to the recommended option.
- **Proactive execution booleans** — Final Stage 2 carries top-level `proactive_speaker_notes`, `proactive_custom_animations`, and `proactive_narration_audio` values. Defaults are `true`, `false`, and `false`, respectively. They control what the Agent does proactively only when the user has not explicitly instructed otherwise; the latest explicit user instruction always wins. These three values are raw confirmation evidence: the UI and server neither couple nor rewrite them, and every boolean combination is valid. When narration audio is enabled, Strategist later resolves the effective Speaker Notes outcome to enabled and records `Narration Audio dependency` as its Design Spec provenance. Disabling proactive custom animation does not suppress the Strategist's advisory motion recommendations.
- **Open prose** — `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife`, `content_divergence`, and `page_count`. `communication_intent` may carry several purposes plus priority / sequence; common paths appear only as help text. `delivery_context` states one primary presenter-led / reader-led / hybrid / recorded-self-running context plus optional secondary use; a hybrid recommendation names which context leads. `content_divergence` is the source-treatment axis. `page_count` may be a range here; Strategist resolves the exact §IX roster, leaving Executor no pagination latitude.
- **Coordinated generative directions** — `design_directions` carries ≥3 safe / shifted / bold candidates. Each candidate bundles visual style, color, typography, icon id, and conditional generated-image rendering. The page can still render legacy top-level `color`, `typography`, and `image_strategy` candidates, but new staged recommendations use the coordinated bundle.

AI-authored custom proposals apply only to mode, visual style, and conditional AI-image rendering; a selected proposal cannot be blank. Color / typography keep their existing manual Custom cards. Image usage uses source ids plus `image_notes`; closed sets have no Custom path.

**Stage-1 current-value contract.** Each editable prose box starts with the Strategist's recommendation, if one exists. The user may retain, revise, or clear it; no Stage-1 prose field has a non-empty validation gate. On confirmation, the browser submits the current strings and the server preserves them through every later stage and the final `result.json`, including `""`. Blank means no explicit user constraint and may cause downstream default judgment, but it never causes the initial recommendation to be restored. A profile-declared `locked: true` field is read-only and remains the sole exception.

`image_ai_path` is conditional: the page shows it and writes it to `result.json` only when `image_usage` includes `ai`. Web-sourced / User-provided / Placeholder / No images paths do not carry an AI backend choice.

## Catalogs — `static/catalogs.json` (the finite option universe)

The front-end loads `/api/catalogs` (served by the confirm server) and falls back to the static `/static/catalogs.json` if that route is unavailable. `/api/catalogs` returns the static file **with the `canvas` list synced live from `config.py CANVAS_FORMATS`** — the set of formats and their `dim` come from config (single source of truth, zero drift), while trilingual labels / use text stay in catalogs.json (a plain fallback label is synthesized for any new id config adds). Keys: `canvas`, `modes`, `visual_styles` (grouped), `icons`, `image_usage`, `image_ai_path`, `formula_policy`, `generation_mode`, `delivery_purpose`. Each entry is `{ "id", "label", "label_zh", "label_en", "label_ja", ... }`; descriptions use `desc_zh` / `desc_en` / `desc_ja`, and `visual_styles` groups use `group_zh` / `group_en` / `group_ja`. The front-end falls back to legacy `label` / `desc` / `group`, so old catalogs still load, but new user-facing catalog text must cover all three languages (zh / en / ja). English labels should mirror canonical reference names (`pyramid`, `swiss-minimal`, `Path A`, `mixed`, etc.); Chinese and Japanese labels should be translated for users. Descriptions render inline after the option title, not as a separate selected-option line. `visual_styles` is `[{ "group", "group_zh", "group_en", "group_ja", "items": [...] }]`. For `canvas` you only need to maintain the trilingual labels in catalogs.json; the format set and dimensions are authoritative in `config.py CANVAS_FORMATS`.

## Round-trip data contract

Round-trip and session files live under `<project_path>/confirm_ui/`. When Step
3 is triggered, its files (`template_options.json` / `template_selection.json`
/ `template_handoff.json`) close before the Strategist pair
(`recommendations.stageN.json` / `result.json`) begins. Ordinary free design
creates none of those template files.

### Current two-stage flow

The page runs a **two-stage Strategist wizard in one browser session**, directly
for ordinary free design or after triggered template installation. Each stage
has its own Strategist-authored file and top-level `"stage"` selector. The active,
unconfirmed stage may be overwritten any number of times when the user asks for
a better recommendation; refresh the page to load the replacement. Once the
user confirms it, normal progression writes the next stage file rather than
repurposing the previous one. The server derives the active Strategist filename
from `result.json`; `template_selection.json` is a separate prerequisite only
when template options exist.

Confirm UI is a one-run surface, not a migration layer. It accepts only the
current Stage-1/Stage-2 files. If a project starts confirmation again, author a
fresh `recommendations.stage1.json`; when it is newer than the prior
`result.json`, the server treats it as the start of the new two-stage session.
The completed result cannot be reopened or overwritten: launching without that
fresh Stage-1 file fails instead of exposing old choices. After Stage 1 is
confirmed, `recommendations.stage2.json` must likewise be newer than that
Stage-1 receipt; a Stage-2 file left by an earlier run remains inactive. An
existing `result.json` outside the current `stage1` / `final` contract also
fails closed unless fresh template options or a newer Stage-1 file starts the
replacement run.

| Recommendation file | Declared stage | Page renders | Button | On submit |
|---|---|---|---|---|
| `recommendations.stage1.json` | `"stage1"` | communication contract — content language; audience; open `communication_intent`; audience outcome; core message / primary delivery context + optional secondary use / artifact afterlife / `content_divergence` (all prose fields may be blank); canvas | **Confirm contract & continue** | writes `result.json` `{ stage: "stage1", status: "stage1-confirmed", <communication contract> }`; the page stays open and polls |
| `recommendations.stage2.json` | `"stage2"` | complete deck solution and production — conditional natural-language template application, reading mode, mode, page count, visual direction, color, icons, typography, image usage/rendering, conditional AI acquisition path, formula policy, proactive notes/custom-animation/narration-audio toggles, generation mode, and Design Spec review toggle | **Confirm final plan** | writes `result.json` `{ stage: "final", status: "confirmed", <all fields> }`, then shuts the page down |

The AI launches a template phase only when triggered, applies its confirmed
receipt, and only then authors Stage 1; ordinary free design authors Stage 1
directly. Stage-1 recommendations use only the current user request,
source facts, conversation constraints, and project initialization; the
selection, installed template content/assets, and template canvas are excluded.
After Stage 1 is confirmed, the AI inspects the installed project-local state
when present and authors the complete final Stage-2 solution plus production
mechanics once from the user's actual communication contract. An edit inside
the current stage never requests another recommendation. The page preserves
earlier answers across transitions. When template options exist,
`GET /api/session` reports `phase: "template"` until selection closes, its bound
handoff is ready, and a fresh Stage-1 file exists; otherwise it reports
`phase: "strategist"` directly. `GET /api/recommendations`
is `no-store`, and the server folds confirmed earlier-stage choices back into
the final Stage-2 payload so an in-run refresh preserves the confirmed Stage-1
communication contract. Unsubmitted Stage-2 edits are browser-local and a
completed final result is never reopened.

**Progression guard.** Stage 1 must not be exposed while
`template_options.json` exists without a valid confirmed
`template_selection.json`. After confirmation the session requires a valid
`template_handoff.json` bound to that selection and a Stage-1 recommendation
newer than the handoff. Each template selection must be newer than its current
options, and each handoff newer than that selection, so receipts from an earlier
one-run UI cannot satisfy a new template phase. Strategist then confirms Stage 1
→ final Stage 2.
`/api/confirm` accepts only the submit stage matching the
active filename and its required predecessor; the declared `stage` must also
match the filename. A confirmed templates-mode workspace does not exempt final
Stage 2: its recommendations must include `template_application.value`.

### Input — `recommendations.stage1.json` (created directly or after a triggered Step-3 handoff)

When Step 3 ran, installation is only the ordering prerequisite. Do not read template selection,
specs, prototypes, assets, fused segment owners, or template canvas when
authoring this file.

```json
{
  "stage": "stage1",
  "lang": "zh",
  "primary_language": "zh-CN",
  "recommend": {
    "canvas": "ppt169"
  },
  "audience": { "value": "公司管理层，包括财务与产品负责人" },
  "communication_intent": {
    "value": "先汇报进展并暴露交付风险，再推动管理层决定下一阶段投入"
  },
  "audience_outcome": {
    "value": "管理层能比较三个选项、接受风险判断，并选定一条获得预算的路径"
  },
  "core_message": {
    "value": "现在为方案 B 增加投入，能以可接受的成本守住发布时间"
  },
  "delivery_context": {
    "value": "主要为有主讲的 20 分钟管理层现场评审；次要为会后独立阅读的审批材料"
  },
  "artifact_afterlife": {
    "value": "作为审批记录、项目交接依据和季度审计材料"
  },
  "content_divergence": { "value": "" }
}
```

All seven Stage-1 prose values may be blank. `primary_language` is required canonical BCP-47. The server normalizes legacy English / Chinese / Japanese / Korean aliases, rejects `und` and Chinese without script/region, and carries it forward; `lang` is UI-only. Prose submits verbatim, including `""`. A profile's `{ "locked": true }` value is read-only, persisted, and stripped of that marker in final `result.json`.

The common paths — inform / explain / persuade / decide / align / teach / report and account / mobilize / record and hand off — appear only as help text for `communication_intent`. They are not catalog ids and must not be emitted as a `primary_job` field.

After Stage 1 is confirmed, create `recommendations.stage2.json` with the complete solution; leave Stage 1 unchanged (the server folds confirmed communication fields back in when serving the page):

**Stage-2 production contract**: the server rejects the recommendation file
unless `recommend.formula_policy`, `recommend.generation_mode`, and boolean
`refine_spec.value` are present; `recommend.image_ai_path` is additionally
required when `image_usage` includes `ai`. Final submission must retain the
corresponding direct values (`formula_policy`, `generation_mode`, boolean
`refine_spec`, and conditional `image_ai_path`) or confirmation is rejected.

```json
{
  "stage": "stage2",
  "lang": "zh",
  "recommend": {
    "delivery_purpose": "balanced",
    "mode": "pyramid",
    "visual_style": "swiss-minimal",
    "image_usage": ["ai", "provided"],
    "image_ai_path": "auto",
    "formula_policy": "mixed",
    "generation_mode": "continuous"
  },
  "page_count": { "value": "12-15" },
  "image_notes": { "value": "封面和章节页用 AI 主视觉；产品页优先用户素材。" },
  "proactive_speaker_notes": { "value": true },
  "proactive_custom_animations": { "value": false },
  "proactive_narration_audio": { "value": false },
  "refine_spec": { "value": false },
  "custom_candidates": {
    "mode": {
      "name_zh": "冲突到决策",
      "behavior_zh": "先建立业务冲突，再用结论先行结构推动决策。"
    },
    "visual_style": {
      "name_zh": "编辑批注风",
      "behavior_zh": "严格栅格配合边注和证据强调。"
    },
    "image_strategy": {
      "name_zh": "证据拼贴",
      "rendering": "custom",
      "visual_zh": "纸面证据拼贴",
      "mood_zh": "审慎可信",
      "behavior_zh": "裁切纸面配少量批注，保持平面深度并继承演示色板。"
    }
  },
  "design_directions": {
    "selected": 0,
    "candidates": [
      {
        "name_zh": "稳妥专业",
        "note_zh": "像成熟咨询简报",
        "visual_style": "swiss-minimal",
        "icons": "tabler-outline",
        "color": { "name_zh": "冷静专业", "palette": {
          "background": "#FFFFFF", "secondary_bg": "#F4F6F8",
          "primary": "#1A3A6B", "accent": "#E8A317",
          "secondary_accent": "#4A7BB5", "body_text": "#1D2430"
        } },
        "typography": {
          "name_zh": "微软雅黑 + Arial",
          "heading": { "primary": "Microsoft YaHei", "english": "Arial", "css": "sans-serif" },
          "body": { "primary": "Microsoft YaHei", "english": "Arial", "css": "sans-serif" },
          "body_size": 24
        },
        "image_strategy": {
          "name_zh": "克制矢量",
          "rendering": "vector-illustration",
          "visual_zh": "扁平矢量、实色块、少阴影",
          "mood_zh": "稳定、可信、克制"
        }
      }
    ]
  }
}
```

The example abbreviates the required ≥3 directions. Custom mode/style candidates remain mandatory; only a recommendation containing AI requires the custom image candidate. Final Stage 2 rejects fewer than three bundles, incomplete six-role palettes, or incomplete heading/body stacks. Legacy grids remain readable only with three complete palettes and complete typography.

- `recommend.*` names each recommended id. New mode / style values use a catalog id or literal `custom`; arbitrary prose values are legacy-only. Use `recommend.image_strategy: "custom"` only when an explicit user-supplied image direction should start selected. Missing recommendations fall back to the normal preset. Legacy aliases remain accepted; new files write canonical ids.
- The three proactive-execution fields are top-level boolean `{ "value": ... }` objects, not catalog ids. Omitted fields use `true / false / false` for notes / custom animation / narration audio. These are absence-of-instruction defaults, not permission to override the user's latest explicit request. Preserve all three raw values independently through `result.json`; do not couple or rewrite them. Strategist derives effective Speaker Notes as enabled when audio is `true` and records `Narration Audio dependency` as provenance in the Design Spec. `proactive_custom_animations: false` leaves Strategist animation suggestions unchanged; it only prevents unrequested custom-animation execution.
- `custom_candidates` is recommendation-only. Mode / style carry localized `name` + `behavior`; conditional image strategy also carries `rendering: "custom"`, `visual`, and `mood`. When a proposal combines or borrows existing catalog entries, the visible behavior names every exact id and Strategist reads every corresponding file before authoring it; a genuinely novel proposal names none. The server rejects missing required candidates; the UI shows full copy, edits it only after selection, rejects a selected blank, and omits unselected candidates from `result.json`. Template-backed proposals obey inherited identity, prototype capacity, and `template_application`.
- Seed `audience`, `communication_intent`, `audience_outcome`, and `delivery_context` when evidence supports them; users need not supply them, and every Stage-1 prose field may end blank. The contract and `primary_language` stay in `result.json` and `design_spec.md`; `spec_lock.md communication` receives `primary_language`, compact `audience` / `objective` / `core_message`, and reading mode. `communication_intent` may preserve multiple purposes and priority/sequence; never add a `primary_job` enum.
- Do not write `recommend.template_reuse_scope` or `recommend.template_adherence`. Strategist records those internal exporter values later in `spec_lock.md` after inspecting the actual template and current content.
- For a confirmed templates-mode handoff, write one editable prose field as top-level `template_application.value`. It summarizes **how to use** the already selected project-local template: actual page/prototype use and preservation/reorganization decisions. It never chooses, changes, or reinstalls a workspace. Omit it for free design. The UI returns the current string through final Stage 2; Strategist then persists the final effective plan as `- **Template Application**: ...` in `design_spec.md §I`, which Executor reads from the retained Design Spec. Never replace it with internal reuse/adherence ids or a fixed option menu.

Template-mode-only Stage-2 fragment:

```json
{
  "template_application": {
    "value": "选用封面、章节页和数据页原型；跳过示例内容页。品牌标识和页脚保留，正文可按当前材料重组。"
  }
}
```

- `recommend.image_usage` should be an array of source ids when more than one source applies, e.g. `["ai", "provided"]`. A single string is still accepted for backward compatibility. Do not write bare `"custom"` and do not encode a mixed-source plan as prose here; write the prose to top-level `image_notes.value`.
- `image_notes` is the initial strategy note shown under the image source chips. Use it for page-role guidance and constraints: which source applies where, what to avoid, which user assets are authoritative, how realistic / abstract the imagery should be, and what can remain as placeholders. It is intent guidance, not a separate finite option.
- Final Stage 2 shows and submits `recommend.image_ai_path` as one of `auto` / `api` / `host-native` / `manual` only while its current `image_usage` includes `ai`; changing sources refreshes that production control on the same page.
- **Color candidates carry the user-facing core `palette`**: `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, and `body_text`. The page renders every role as a labelled swatch with its HEX value visible, and offers per-role override inputs for precise single-role edits, plus a **Custom color card with a free-text box** — the user can describe the palette in words or paste HEX values instead of filling each role; this writes `color: { "name": "custom", "custom": "<text>" }` to `result.json` for the AI to interpret. Legacy `text` is accepted as an alias for `body_text`, but new files should write `body_text`. Strategist derives secondary text, borders, state colors, and visual-style neutral tiers while writing `design_spec.md`, then projects the machine values to `spec_lock.md`; those are not user-facing confirmation choices.
- **Candidate display text may be multilingual**: color / typography candidates can provide `name_zh` / `name_en` / `name_ja` and `note_zh` / `note_en` / `note_ja`; the page falls back to legacy `name` / `note`. Labels resolve in the page language first, then fall back across the others (a `ja` page: ja → en → zh; zh/en pages keep their zh↔en fallback and try `_ja` last), so when `lang` is `ja` always include the `_ja` variants — otherwise the candidate labels render in English.
- **Typography candidates** use concrete heading/body `primary`; non-English decks also use `english`, while English-primary decks omit it. `cjk` / `latin` remain legacy aliases. Localized `name` labels the pair and `css` only previews. Bundles differ overall; font pairs may repeat without blocking. Fixed pairs require `fixed: true`. Catalog `fonts` supplies language-filtered dropdowns plus Other without limiting recommendations; edits mark Custom and refresh the preview. Include topic samples. PPT baselines are `text` 20 · `balanced` 24 · `presentation` 32 px; cards preserve sizes and submit px.
- **Per-role size override** (parallel to color's per-role HEX override): besides `body_size`, the page exposes editable inputs for `title` / `subtitle` / `annotation`. The browser applies one documented deterministic dependency chain: `reading mode → body baseline → unpinned role sizes` (role ramp: `body ×` the §g ratios). Changing reading mode updates the body and all unpinned roles locally; changing body updates unpinned roles locally. Editing body or a role pins that value, so later reading-mode changes do not overwrite it. Font / direction-card selection preserves all current sizes. This is a browser-only state update: it performs no fetch, asks the backend to author no new recommendations, and a re-render preserves exactly what the user sees. Each role input is labelled as px and shows an approximate pt equivalent (`1px = 0.75pt`) for orientation. The final values are written to `result.json` as `typography.sizes: { "title", "subtitle", "annotation" }` in **px** — every canvas, no pt and no `sizes_pt` provenance. These confirmed values are Strategist input anchors: the completed page plan may add recurring roles, and downstream execution owns bounded per-occurrence treatment. Candidate `sizes` remain accepted for compatibility, but the fresh Stage-2 baseline is normalized through the same local ramp before first render.
- **`delivery_purpose` compatibility key / Reading mode** (enumerable, PPT only) decides where meaning is carried, not merely how large type is: `text` makes pages self-contained with complete sentences, short prose, captions, tables, and necessary detail; `balanced` shares explanation between page and presenter; `presentation` uses one idea, concise claims, and visual evidence while speech / notes carry the detail. It therefore governs page grammar, granularity, density / rhythm, and note burden. Reading-mode cards intentionally show **no px value**; the typography section owns the separately visible body / role sizes and applies any local default. It is surfaced in Stage 2 beside the visual system, separate from communication intent. `recommend.delivery_purpose` pre-selects one; `result.json` retains the key, while `spec_lock.md` uses canonical `consumption_mode`. Non-PPT canvases omit it.
- **Combined style preview** — a compact live "overall impression" strip sits just above the color section and is **sticky**: it pins under the topbar so it stays visible while the user scrolls through the color / icon / typography sections, keeping the picking controls and their combined effect on screen together. It applies the currently selected color palette **and** typography (heading sample in `primary` over `background`, body sample in `body_text`, an `accent` bar, a `secondary_bg` chip) and repaints on every color / HEX-override / font / `body_size` change. It does not replace the per-candidate swatches or font samples (those stay for picking); it is deliberately an abstract style chip, **not** a slide-layout preview — page layout preview remains the live-preview server's job (Step 6). No schema field; it derives entirely from the existing color + typography selections.
- **Generated-image direction** appears only for `image_usage: ai`. One preset dropdown contains project recommendations when present plus the 20 system styles; Custom remains a separate card and is blank when AI was added manually. A preset submits its id; Custom submits `rendering: "custom"` + non-empty `behavior`; closing AI omits `image_strategy`. Catalog-based custom behavior names exact ids for optional `image_rendering_references`; a novel behavior has none. The left preview follows selection. No image palette is written; deck colors remain authoritative, and legacy `image_strategy.palette` is ignored.
- **`design_directions`** is the canonical Stage-2 spectrum: ≥3 meaningfully different safe / shifted / bold bundles with localized copy, style, icons, conditional image strategy, complete language-aware typography, and HEX `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, `body_text`. Selection applies the bundle; component controls override it. `result.json` stores components, not a direction id.
- `recommend.generation_mode` and `refine_spec` mirror [`generate-pptx`](../../workflows/generate-pptx.md) Step 4. `split` / `true` are explicit opt-ins. Refinement adds no UI stage: after Gate 1 it stops before the lock for unrestricted chat revision until approval.
- `content_divergence` is a **free-text** Stage-1 source-treatment field. Blank means a balanced default; facts stay sourced at every level. Strategist consumes it while authoring §IX and records it in `design_spec.md §I`; it is not written to `spec_lock.md`. Beautify sends `{ "value": "keep source wording and page structure verbatim", "locked": true }`, so the UI displays it read-only and the server restores it on every staged submit. Template-fill does not use this confirmation flow and does not surface it.
- `lang` is the soft UI-language default (`zh` / `en` / `ja`); the persisted user choice wins. It never sets `primary_language`.

### Output — `result.json` (written on submit, read by the AI)

```json
{
  "primary_language": "zh-CN",
  "canvas": "ppt169",
  "page_count": "12-15",
  "audience": "...",
  "communication_intent": "Report progress and expose risk first; then obtain an investment decision",
  "audience_outcome": "The committee compares the options and chooses one funded path",
  "core_message": "Fund option B now to protect the launch date at acceptable incremental cost",
  "delivery_context": "Primary: presenter-led 20-minute leadership review; secondary: reader-led approval copy shared afterward",
  "artifact_afterlife": "Approval record, hand-off reference, and audit trail",
  "content_divergence": "freely restructure and expand within the source",
  "mode": "pyramid",
  "visual_style": "swiss-minimal",
  "color": { "name": "...", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
  "icons": "tabler-outline",
  "typography": { "name": "...", "heading": { "primary": "...", "english": "...", "css": "..." }, "body": { "primary": "...", "english": "...", "css": "..." }, "body_size": 24, "body_size_unit": "px", "sizes": { "title": 42, "subtitle": 32, "annotation": 18 } },
  "delivery_purpose": "balanced",
  "formula_policy": "mixed",
  "image_usage": ["ai", "provided"],
  "image_notes": "封面和章节页用 AI 主视觉；产品页优先用户素材，缺口页可用占位符。",
  "image_ai_path": "auto",
  "image_strategy": { "name": "方案 A", "rendering": "vector-illustration", "visual": "...", "mood": "..." },
  "proactive_speaker_notes": true,
  "proactive_custom_animations": false,
  "proactive_narration_audio": false,
  "generation_mode": "continuous",
  "refine_spec": false,
  "stage": "final",
  "status": "confirmed",
  "confirmed_at": "2026-06-15T11:44:44"
}
```

The shape above is final for Strategist confirmation. It intentionally contains
no template-selection field: `template_selection.json`, its agent handoff, and
the installed project-local state own that earlier decision. The proactive-execution values
are independent flat booleans in `result.json`; old recommendations and results
that omit them resolve to `true / false / false`. They remain raw evidence even
when `proactive_speaker_notes` is `false` and `proactive_narration_audio` is
`true`; Strategist owns the effective dependency resolution described above.
Selected custom values use `mode: custom` + `mode_behavior`, `visual_style:
custom` + `visual_style_behavior`, or `image_strategy.rendering: custom` +
`behavior`. During Design Spec and lock authoring, Strategist projects optional
`mode_references`, `visual_style_references`, or
`image_rendering_references` only when that confirmed behavior actually uses
named catalog sources; genuinely novel custom behavior has no reference list.
The Stage-1 intermediate write retains the communication contract for Stage 2.

**Final-result consumption contract.** A final result is the user-confirmed input contract for the Strategist's Design Spec, not another recommendation input. After the final wait, Generate Step 4 reads the complete final object exactly once and retains it while Strategist writes and audits `design_spec.md` against every explicitly present field. Normal lock authoring and downstream execution do not reopen `result.json`; the completed Design Spec is the durable authority. Only after that audit passes does Strategist author `spec_lock.md` from the Design Spec plus current execution context, selecting stable anchors and routing rather than copying every field or enumerating every legal color/font. Every value must be consumed at the semantic type owned by [`strategist.md`](../../references/strategist.md) §1 and its field owner: do not omit or substitute it, and do not silently strengthen or weaken its type. If a confirmed requirement cannot be honored, the owning workflow reports or pauses under failure recovery; it never deletes the requirement to keep the pipeline moving.

- Bespoke mode / style prose lives only in the required behavior sibling; image custom prose lives in `image_strategy.behavior`. Canvas / icons retain free-text edge cases, color / typography retain `name: "custom"`, and image usage remains a source-id array plus `image_notes`.
- `image_ai_path` and `image_strategy` appear only with `image_usage: ai` and remain confirmed downstream. The page is default; explicit/failure chat fallback keeps identical fields. `image_ai_path` selects the Step 5 path, and [`strategist-image.md`](../../references/strategist-image.md) §2 retains the selected rendering or custom behavior as the deck-level image identity anchor; individual prompts still adapt subject, composition, and atmosphere within it.
- Triggered Step-3 **Confirm template & continue** writes `template_selection.json` and keeps the page open while the agent applies the choice. The agent then runs `--complete-template-phase` and writes fresh Stage 1; ordinary free design writes Stage 1 and launches directly. Stage-1 **Confirm contract & continue** keeps polling for the newly authored Stage 2. Stage-2 **Confirm final plan** saves the final `result.json` and shuts the server down (auto-close). The AI reads each receipt at its owning boundary; chat fallback mirrors the same choices. Either way, Step 4 ends with `--shutdown` so a never-confirmed page cannot retain its selected port ahead of Step 6 live preview.

## Scope

- Confirmation surface only — Strategist authors every recommendation; the page never generates deck content.
- No SVG / layout preview here — that is the live preview server's job (`workflows/stages/live-preview.md`, Step 6).
