# Confirm UI — Strategist and Template Confirmation Page

> The interactive surface for [`generate-pptx`](../../workflows/generate-pptx.md)
> Step 4. Stage 1 shows the template-independent communication recommendation
> and the template/free-design choice on one page and confirms both with one
> submission. That submission writes the Strategist contract to `result.json`
> and the selection sidecar to `template_selection.json`. The agent then installs
> any selected workspace and writes `template_handoff.json`; only afterward does
> final Stage 2 read installed template state and confirm the coordinated deck
> solution plus production mechanics. The chat path mirrors these boundaries
> without fabricating UI receipts.

## Authority and Scope

| Concern | Owner |
|---|---|
| Stage-1 combined confirmation and post-confirmation installation order | [`generate-pptx.md`](../../workflows/generate-pptx.md) |
| Template option/selection schema and page transport | This document |
| Step 4 gate and pipeline order | [`generate-pptx.md`](../../workflows/generate-pptx.md) |
| Confirm UI schema | This document |
| Stage 1 / final Stage 2 field membership | This document |
| Server launch / wait / shutdown behavior | This document |
| Port and lock behavior | This document |
| Chat fallback equivalence | This document |
| Confirmed-value precedence | [`generate-pptx.md`](../../workflows/generate-pptx.md) plus this document's `result.json` contract |

**Hard rule**: Keep detailed Confirm UI behavior here. The Generate route may summarize orchestration, but it should not duplicate the full JSON schema, catalog behavior, or launcher lifecycle.

**Model-facing procedure lives elsewhere**: the surface decision, chat/delegated listing, always-on Stage-1 chat handoff, in-run UI → chat switch, and the authoring shapes of `recommendations.stage1.json`, `recommendations.stage2.json`, and `result.json` are owned by [`confirm-surface.md`](../../references/confirm-surface.md), which the Strategist reads. This document keeps the server lifecycle, the template-selection sidecar, catalogs, the progression guard, and the complete field semantics that the server validates.

## `confirm_ui/server.py`

The following launch and wait commands belong to the **UI branch only**:

```bash
python3 scripts/confirm_ui/server.py <project_path> --daemon         # launch combined Stage 1
python3 scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage1  # communication + template selection
python3 scripts/confirm_ui/server.py <project_path> --complete-template-selection # after Stage-1 free-design closure / template install
python3 scripts/confirm_ui/server.py <project_path> --wait-only       # current final Stage 2
python3 scripts/confirm_ui/server.py <project_path> --daemon --port 5051
python3 scripts/confirm_ui/server.py <project_path> --no-browser
python3 scripts/confirm_ui/server.py <project_path> --timeout 0   # disable idle auto-shutdown
python3 scripts/confirm_ui/server.py <project_path> --reset-template-selection # clear prior template sidecars before a fresh UI run
python3 scripts/confirm_ui/server.py <project_path> --shutdown    # Step 4 cleanup (idempotent)
```

- Without `--port`, binds the first free port from `127.0.0.1:5050`; the launch log prints the actual URL. `--port N` is exact and fails when unavailable. Auto-open is suppressed by `--no-browser`.
- In `--daemon` mode the launcher starts the child with browser opening suppressed, then accepts readiness only when `GET /api/health` identifies this confirm service, project, and child process. It opens the printed `http://127.0.0.1:<port>` URL only after that check.
- Confirm UI and live preview use different defaults (`5050` / `6060`) and separate project-local locks (`.confirm_ui.lock` / `live_preview/lock.json`). Step 4 shuts down the confirm service before ending; concurrent projects may use different ports.
- `--daemon` starts the Flask process in the background and returns after the health check. Every Default UI run launches directly into combined Stage 1 and keeps the same process live through final Stage 2. The wait budget defaults to **590 s** (`--wait-timeout`); on timeout the detached server remains live, and the caller re-checks both Stage-1 receipts before chat fallback.
- `--wait-only` attaches to the page opened by `--daemon` and blocks until the requested receipt. If it is already persisted, the command returns before recovery, so a fast submit between launch, chat handoff, and wait is not lost. Otherwise, if the recorded server died, it restarts on the recorded/default port. Use `stage1` for the combined communication/template submission and the default/final wait for Stage 2.
- `--complete-template-selection` is agent-only. It validates the Stage-1 sidecar and writes the bound `template_handoff.json`; template mode additionally requires at least one project-local `templates/design_spec.<kind>.<id>.md`. Run it after installation/free-design closure and before writing Stage 2. `--reset-template-selection` removes exactly `template_options.json`, `template_selection.json`, and `template_handoff.json`; it does not alter Strategist files, installed template content, or `result.json`. The old `--*-template-phase` names are not aliases.
- `--shutdown` stops a confirm server left running for this project and exits — **idempotent** (a no-op when nothing is running). Tries a graceful `/api/shutdown`, falls back to killing the recorded pid, then clears the lock. Generate Step 4 runs this on every path so the selected port is released before live preview starts.
- Every fresh UI run starts with `--reset-template-selection`, then writes valid `<project_path>/confirm_ui/template_options.json` and a newer `recommendations.stage1.json`; `explicit_workspace_roots` is an empty array when no exact root was supplied. Stage 1 writes the bound selection and communication result together. Stage 2 is exposed only when the matching handoff is newer than that selection and its recommendation is newer than the handoff. `--shutdown` needs neither input.
- Per-project lock at `<project_path>/.confirm_ui.lock` — duplicate launches are refused; stale locks (dead pid) are overwritten.
- Idle auto-shutdown after 900 s by default; `/api/shutdown` exits gracefully and releases the lock.
- Stage-1 `GET /api/recommendations` embeds the server-built candidate catalog
  as top-level `template_options`. Its `/api/confirm` submission validates
  current candidate keys and writes `template_selection.json` beside the pure
  Strategist `result.json`; there is no independent template-options endpoint,
  template-confirm endpoint, or template wait stage. The same APIs later serve
  Stage 2 and strip legacy `template_reuse_scope` / `template_adherence`
  fields. The completed template handoff is authoritative: `free_design`
  strips a stray `template_application`, while `templates` exposes that
  editable natural-language field in Stage 2.

Dependency:

```bash
pip install flask
```

## Stage-1 template-selection sidecar contract

Template selection shares the Stage-1 page and submit action but remains a
separate artifact from the Strategist contract. Its files live under
`<project_path>/confirm_ui/`; selection keys never enter `result.json`.

### Input — `template_options.json` (created before launch)

```json
{
  "schema_version": 1,
  "phase": "template",
  "lang": "zh",
  "default_mode": "free_design",
  "explicit_workspace_roots": [
    "/absolute/path/to/a/project-or-template-workspace"
  ]
}
```

- `schema_version` is exactly `1`; `phase` is exactly `template`.
- `lang` is optional, but when present it is a non-empty UI-language string.
- `default_mode` is required and is exactly `free_design` or `templates`.
  Ordinary requests use `free_design`; explicit template intent or any supplied
  exact root uses `templates`. It initializes the UI but never locks the user.
- `explicit_workspace_roots` is required even when empty. Every item is a
  unique absolute path resolving to an existing directory with a library
  `templates/design_spec.md`, one or more project-qualified
  `templates/design_spec.<kind>.<id>.md`, or compatible legacy
  `design_spec.md`.
- The array supplies candidates for the one specified-root dropdown; it does
  not authorize selecting several explicit roots in one confirmation.
- Do not write library entries into this file. The server reads only
  `templates/brands/brands_index.json`,
  `templates/styles/styles_index.json`,
  `templates/layouts/layouts_index.json`, and
  `templates/decks/decks_index.json`, derives each direct-child workspace root,
  and validates that it exists with `templates/design_spec.md`. It never scans
  kind directories.

Stage-1 `GET /api/recommendations` embeds this browser catalog as top-level
`template_options`:

```json
{
  "schema_version": 1,
  "phase": "template",
  "lang": "zh",
  "default_mode": "free_design",
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
explicit. Candidate keys are server-owned. The Stage-1 submit payload carries
the current `{ "mode": "free_design"|"templates", "selection_keys": [...] }`
beside the Strategist fields; the server validates that selection and writes it
to the sidecar rather than copying keys into `result.json`.

When the input supplies exactly one root, `preselected_keys` contains its
resolved candidate key as a convenience default, including when exact equality
reclassifies it as library. When several roots are supplied, all remain
candidates but none is preselected; one specified-root dropdown cannot encode
an instruction to use all of them.

**Page selection model**: Stage 1 first asks the user to choose `Free design` or
`Use templates`, initialized from `default_mode` but always switchable. Exactly
one supplied root may initialize its candidate as an editable convenience
default; multiple roots remain unselected. Only `Use templates` expands the
candidate controls: Brand, Style, Layout, and Deck each have one registered
single-select dropdown, and Specified has one explicit-root single-select
dropdown. Every dropdown includes `None`; template mode cannot submit until at
least one is non-empty. Free design clears all dropdowns. Registered kinds may
be combined, and the complete selection contains at most one contribution per
kind. Layout and Deck may coexist; Layout takes structural precedence. The specified channel contributes at
most one root, selected atomically with every kind it exposes; it can coexist
only with registered roots of non-overlapping kinds. Source provenance never
grants priority.

### Output — `template_selection.json` (written with Stage 1)

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
There is at most one explicit workspace **root** overall. The unit of choice is
the root, not the kind: the browser's specified-path control lists roots, and
selecting one emits a selection for every kind that root exposes. Across those
emitted selections and all library choices, each kind appears at most once.
Layout and Deck may coexist; downstream installation gives Layout structural
precedence. The browser cannot submit arbitrary paths
because the server resolves posted keys against the catalog it just built.
`options_sha256` binds the receipt to the current input, four index files, and
resolved candidates. `selection_sha256` binds the mode and canonical sorted
selections to that option hash. Every receipt read rebuilds the catalog and
rejects option/index drift or an incomplete explicit-root bundle.

The Stage-1 submission writes this receipt and the Stage-1 `result.json`
together. Generate reads both exactly once after `--wait-only --wait-stage
stage1` returns. Free design skips installation. Template mode runs
`apply-template-workspace` against all selected roots and waits for complete
project-local installation. Only then does the agent complete the
handoff below. Installation validates and maps each distinct root once while
preserving its separate specs; Stage 2 resolves segment ownership and
current-project fit from the installed set. Strategist never reads the source
roots.

### Agent handoff — `template_handoff.json`

After free design closes or template installation succeeds, run:

```bash
python3 scripts/confirm_ui/server.py <project_path> --complete-template-selection
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
at least one `<project_path>/templates/design_spec.<kind>.<id>.md`; free design
requires no installed spec. Write `recommendations.stage2.json` only after this
command succeeds, so its file time is newer than the handoff.

## Field shapes

The following fields belong to the Strategist stages, not to the
template-selection receipt.

- **Enumerable + custom** — canvas / base icons retain blank manual inputs. The base icon field stays single-select: one generic SVG style, Emoji, custom, or none. `simple-icons` is not listed; Strategist prepares actual brand marks from content as needed. Mode and visual style first show three project-specific `custom` values projected from the complete directions, then the full fixed base catalog as conservative single-select alternatives. Selecting a projected card expands its behavior editor in place; edits change only the current value, while the adjusted active whole-direction card exposes an explicit restore action for the authored text.
- **Visual examples for hard-to-name choices** — the full-screen confirmation page loads real SVG page samples from `static/style_previews/` for fixed `visual_style` catalog choices, and renders real sample SVGs from `templates/icons` for the base `icons` field. Project-specific `custom` direction cards show their authored summary instead of requesting a nonexistent preset asset. These thumbnails and summaries make style and icon-library choices visually comparable before the user locks them. Preview copy is fixed role text (big title / section title / body / points), not project content from recommendation files, so users compare visual treatment rather than copywriting. These previews are a confirmation aid only: they do not add fields to recommendation stage files or `result.json`, and they do not replace the later Step 6 live preview.
- **Image usage multi-select** — image sources are selected as one or more catalog ids: `ai` = AI-generated, `web` = Web-sourced, `provided` = User-provided, `placeholder` = Placeholder, `none` = No images. `none` is exclusive. A confirmed non-`none` set is the allowed acquisition-source boundary, not a requirement to use every selected source; only explicit `image_notes` wording can require a source, asset, or page role. Recommendation and result values may be a legacy single string, but new files should use an array. When several sources are recommended, write the source ids to `recommend.image_usage` and write the actual usage strategy to `image_notes`, not a custom prose value.
- **Closed enumerable** — PPT reading mode (`delivery_purpose` compatibility key), generation mode / refine spec, plus AI source only when image usage includes `ai`. These have no Custom box; out-of-catalog values snap back to the recommended option.
- **Proactive execution booleans** — Final Stage 2 carries top-level `proactive_speaker_notes`, `proactive_custom_animations`, and `proactive_narration_audio` values. Defaults are `true`, `false`, and `false`, respectively. They control what the Agent does proactively only when the user has not explicitly instructed otherwise; the latest explicit user instruction always wins. These three values are raw confirmation evidence: the UI and server neither couple nor rewrite them, and every boolean combination is valid. When narration audio is enabled, Strategist later resolves the effective Speaker Notes outcome to enabled and records `Narration Audio dependency` as its Design Spec provenance. Disabling proactive custom animation does not suppress the Strategist's advisory motion recommendations.
- **Open prose** — `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife`, `content_divergence`, and `page_count`. `communication_intent` may carry several purposes plus priority / sequence; common paths appear only as help text. `delivery_context` states one primary presenter-led / reader-led / hybrid / recorded-self-running context plus optional secondary use; a hybrid recommendation names which context leads. `content_divergence` is the source-treatment axis. `page_count` may be a range here; Strategist resolves the exact §IX roster, leaving Executor no pagination latitude.
- **Coordinated generative directions** — `design_directions` carries exactly three complete candidates authored top-down from the project contract. Each has a unique stable id and bundles `custom` mode, `custom` visual style, color, typography, icon id, and `custom` generated-image rendering regardless of recommended image source. Its localized note is a compact, user-facing style summary. It may reuse localized display labels from `catalogs.visual_styles` when they describe the result concisely, but those labels are optional vocabulary rather than a selection constraint or required mapping. Otherwise it uses concise natural language and never forces the nearest label. The summary stays within one or two short sentences and does not expose catalog ids or reference mechanics. Each candidate is one complete design authored top-down within the confirmed contract, never assembled bottom-up from catalog picks; three exist so a single recommendation cannot lock the user in, while the fixed catalogs stay the manual lower layer. Its custom projections are unrestricted by catalog relationship and may carry one preset unchanged. The candidates are plainly different whole-deck designs; any component may carry the difference or coincide. Names, notes, or reference counts alone do not distinguish them, and identical projections are valid only when authoritative truth leaves nothing open, stated in the note instead of inventing variation. Do not force safe / shifted / bold archetypes. After completing all three bundles, Strategist writes the strongest overall fit's zero-based index to `selected` when no template is installed. With installed template state, every candidate obeys the same resolved context; `selected` identifies the viable candidate that most fully expresses it, while the other two vary only open dimensions—never by weakening template use or splitting segments across cards. Array position does not determine preference. That bundle becomes the initial default and applies its three custom projections coherently. The page can still render legacy top-level `color`, `typography`, and `image_strategy` candidates, but new staged recommendations use the coordinated bundle.

Direction-local custom projections apply to mode, visual style, and generated-image rendering; all three are editable after selection and a selected custom value cannot be blank. The original recommendation remains immutable so the active whole-direction card can explicitly restore every edited component without making an ordinary card click destructive. Legacy standalone `custom_candidates` remain readable but are optional and are not authored in new files. Color / typography keep their existing manual Custom cards. Image usage uses source ids plus `image_notes`; closed sets have no Custom path.

**Stage-2 catalog read gate.** Before choosing component bases, Strategist reads only `modes/_index.md`, `visual-styles/_index.md`, and `image-renderings/_index.md`. It authors the three whole solution intents first, freezes every basis id from those indexes, and only then reads the deduplicated selected detail files before completing the custom behaviors. `custom` has no required catalog relationship: one exact preset may supply an entire editable projection unchanged, several may contribute distinct jobs, or no preset may be used. These are examples, not a closed classification. The behavior remains non-empty; omit every source whose contribution it cannot state and never add a decorative second basis. Unselected sibling files never enter context.

**Stage-1 current-value contract.** Each editable prose box starts with the Strategist's recommendation, if one exists. The user may retain, revise, or clear it; no Stage-1 prose field has a non-empty validation gate. On confirmation, the browser submits the current strings and the server preserves them through every later stage and the final `result.json`, including `""`. Blank means no explicit user constraint and may cause downstream default judgment, but it never causes the initial recommendation to be restored. A profile-declared `locked: true` field is read-only and remains the sole exception.

`image_ai_path` is conditional: the page shows it and writes it to `result.json` only when `image_usage` includes `ai`. Web-sourced / User-provided / Placeholder / No images paths do not carry an AI backend choice.

## Catalogs — `static/catalogs.json` (the finite option universe)

The front-end loads `/api/catalogs` (served by the confirm server) and falls back to the static `/static/catalogs.json` if that route is unavailable. `/api/catalogs` returns the static file **with the `canvas` list synced live from `config.py CANVAS_FORMATS`** — the set of formats and their `dim` come from config (single source of truth, zero drift), while four-language labels / use text stay in catalogs.json (a plain fallback label is synthesized for any new id config adds). Keys: `canvas`, `modes`, `visual_styles` (grouped), `icons`, `image_usage`, `image_ai_path`, `generation_mode`, `design_spec_depth`, `delivery_purpose`. `simple-icons` is content-driven and has no option. Each catalog entry is `{ "id", "label", "label_zh", "label_zh_tw", "label_en", "label_ja", ... }`; descriptions use `desc_zh` / `desc_zh_tw` / `desc_en` / `desc_ja`, and `visual_styles` groups use `group_zh` / `group_zh_tw` / `group_en` / `group_ja`. The front-end falls back to legacy `label` / `desc` / `group`, so old catalogs still load, but new user-facing catalog text must cover all four languages (zh / zh-TW / en / ja). English labels should mirror canonical reference names (`pyramid`, `swiss-minimal`, `Path A`, `continuous`, etc.); Simplified Chinese, Traditional Chinese, and Japanese labels should be translated for users. Descriptions render inline after the option title, not as a separate selected-option line. `visual_styles` is `[{ "group", "group_zh", "group_zh_tw", "group_en", "group_ja", "items": [...] }]`. For `canvas` you only need to maintain the four-language labels in catalogs.json; the format set and dimensions are authoritative in `config.py CANVAS_FORMATS`.

## Round-trip data contract

In the UI branch, round-trip and session files live under
`<project_path>/confirm_ui/`. `template_options.json` is prepared beside the
Stage-1 recommendation. The Stage-1 submit writes `result.json` and
`template_selection.json` together; after installation/free-design closure,
`template_handoff.json` unlocks Stage 2. The chat/delegated branch preserves the
same logical order without fabricating these UI receipts.

### Current two-stage flow

The page runs a **two-stage Strategist wizard in one browser session**. Stage 1
contains the communication contract and template/free-design controls. Each stage
has its own Strategist-authored file and top-level `"stage"` selector. The active,
unconfirmed stage may be overwritten any number of times when the user asks for
a better recommendation; refresh the page to load the replacement. Once the
user confirms it, normal progression writes the next stage file rather than
repurposing the previous one. The server derives the active Strategist filename
from `result.json`; the bound template handoff is the prerequisite for Stage 2.

Confirm UI is a one-run surface, not a migration layer. It accepts only the
current Stage-1/Stage-2 files. If a project starts UI confirmation again, run
`--reset-template-selection`, write fresh `template_options.json`, then author a
fresh `recommendations.stage1.json`. Those two inputs start the new UI
lifecycle; neither a standalone newer Stage-1 file nor a standalone option file
does so.
The completed result cannot be reopened or overwritten, and a standalone newer
Stage-1 file cannot start its replacement. After Stage 1 writes both receipts,
the agent completes a newer bound handoff; `recommendations.stage2.json` must be
newer than that handoff and the Stage-1 result. A Stage-2 file left by an earlier
run remains inactive. An existing `result.json` outside the current `stage1` /
`final` contract also fails closed unless fresh paired inputs start a new run.

| Recommendation file | Declared stage | Page renders | Button | On submit |
|---|---|---|---|---|
| `recommendations.stage1.json` + `template_options.json` | `"stage1"` | communication contract — content language; audience; open `communication_intent`; audience outcome; core message / primary delivery context + optional secondary use / artifact afterlife / `content_divergence` (all prose fields may be blank); canvas; free-design/template mode and conditional candidate selectors | **Confirm contract & template choice** | writes Stage-1 `result.json` plus `template_selection.json` in one submission; the page stays open and polls while the agent installs/completes the handoff |
| `recommendations.stage2.json` | `"stage2"` | complete deck solution and production — conditional natural-language template application, reading mode, mode, page count, visual direction, color, icons, typography, image usage/rendering, conditional AI acquisition path, proactive notes/custom-animation/narration-audio toggles, generation mode, Design Spec review toggle, and Design Spec depth | **Confirm final plan** | writes `result.json` `{ stage: "final", status: "confirmed", <all fields> }`, then shuts the page down |

In the UI branch, the AI authors Stage 1 without reading template candidates,
then launches the combined page. In chat/delegated confirmation it authors the
same communication recommendation before listing template candidates. After
the one Stage-1 confirmation, the AI installs any selection, completes the
handoff/equivalent state, then inspects only the project-local template and
authors the complete final Stage-2 solution plus production mechanics once from
the user's actual communication contract. An edit inside
the current stage never requests another recommendation. The page preserves
earlier answers across transitions. `GET /api/session` reports `phase:
"strategist"` with current Stage 1 from launch; after Stage-1 submission it
reports `waiting_agent` until the bound handoff and fresh Stage-2 file exist.
`GET /api/recommendations`
is `no-store`, and the server folds confirmed earlier-stage choices back into
the final Stage-2 payload so an in-run refresh preserves the confirmed Stage-1
communication contract. Unsubmitted Stage-2 edits are browser-local and a
completed final result is never reopened.

**Progression guard.** Stage 1 requires current `template_options.json` and a
fresh `recommendations.stage1.json`; it does not require a prior selection or
handoff. Its one submit must persist a valid Stage-1 result and selection bound
to those options. Stage 2 requires a newer `template_handoff.json` bound to that
selection and a fresh Stage-2 recommendation. This ordering prevents receipts
from an earlier one-run UI from satisfying a new run. Strategist confirms Stage
1 → installation/free-design handoff → final Stage 2.
`/api/confirm` accepts only the submit stage matching the
active filename and its required predecessor; the declared `stage` must also
match the filename. A confirmed templates-mode workspace does not exempt final
Stage 2: its recommendations must include `template_application.value`.

### Input — `recommendations.stage1.json` (created beside template options)

Author this file before reading candidate index summaries in chat and without
reading any template spec, prototype, asset, segment owner, or template
canvas. `template_options.json` supplies display state only and never changes
the communication recommendation.

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
unless `recommend.generation_mode`, boolean `refine_spec.value`, and
`design_spec_depth.value` as `brief` or `complete` are present;
`recommend.image_ai_path` is additionally required when `image_usage` includes
`ai`. Final submission must retain the corresponding direct values
(`generation_mode`, boolean `refine_spec`, `design_spec_depth`, and conditional
`image_ai_path`) or confirmation is rejected. `design_spec_depth: brief` is
rejected when `generation_mode` is `split` or `refine_spec` is `true`; those
conditions require `complete`. A legacy `result.json` without the field is read
as `complete`, while a Stage-2 recommendation without it is invalid. Formula
realization is Executor-owned and is not a Stage-2 choice. Legacy
recommendation/result objects may contain
`formula_policy`; the server tolerates the extra field but does not render or
persist it in a new receipt.

```json
{
  "stage": "stage2",
  "lang": "zh",
  "recommend": {
    "delivery_purpose": "balanced",
    "mode": "custom",
    "visual_style": "custom",
    "image_strategy": "custom",
    "image_usage": ["ai", "provided"],
    "image_ai_path": "auto",
    "generation_mode": "continuous"
  },
  "page_count": { "value": "12-15" },
  "image_notes": { "value": "封面和章节页用 AI 主视觉；产品页优先用户素材。" },
  "proactive_speaker_notes": { "value": true },
  "proactive_custom_animations": { "value": false },
  "proactive_narration_audio": { "value": false },
  "refine_spec": { "value": false },
  "design_spec_depth": { "value": "brief" },
  "design_directions": {
    "selected": 1,
    "candidates": [
      {
        "id": "executive-clarity",
        "name_zh": "稳妥专业",
        "note_zh": "以瑞士极简为主，融合柔和圆角与编辑出版风格。",
        "mode": "custom",
        "mode_behavior_zh": "以 pyramid 作为唯一目录基底，为当前风险决策材料定制两次结论闸门；标题保持判断句，每章先给判断，再用证据展开并以可执行结论收束。",
        "visual_style": "custom",
        "visual_style_behavior_zh": "由 swiss-minimal 负责精确栅格和大留白，soft-rounded 负责少量关键容器的轮廓与轻微抬升，editorial 负责细规则、边注与证据层级；标题锐利，正文中性，装饰只标记推理关系。",
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
          "name_zh": "编辑式证据图",
          "rendering": "custom",
          "visual_zh": "简化矢量主体配合编辑式注释与局部材质对比",
          "mood_zh": "审慎、可信，像调查报道中的证据插图",
          "behavior_zh": "由 vector-illustration 负责清晰轮廓，minimalist-swiss 负责留白构图，screen-print 负责克制的半调纹理，warm-scene 负责暖光与可信氛围；四者服从同一平面主体和当前演示文稿颜色角色，避免写实景深与装饰性渐变。"
        }
      }
    ]
  }
}
```

The example shows one candidate's complete shape; the actual array repeats that shape for exactly three candidates. Every candidate requires a unique stable `id`, literal `custom` mode/style/rendering with localized behavior, an icon value, complete six-role palette, complete heading/body stack, and complete image strategy even when `recommend.image_usage` excludes AI. The server rejects any fixed mode/style/rendering inside a new direction and any explicit `design_directions.selected` outside integer `0` through `2`; omission remains readable as a legacy index-`0` fallback. Legacy grids remain readable only with three complete palettes and complete typography.

- `design_directions.selected` owns the initial complete bundle and MUST be the actual zero-based index (`0`, `1`, or `2`) that Strategist chooses only after all three bundles are complete. The chosen card is marked Recommended and initially applies its matching mode, visual-style, and generated-image custom candidates together; array order carries no recommendation meaning. New direction mode/style/rendering values are always literal `custom`; prose stays in the required behavior sibling. `recommend.*` remains a compatibility hint and may mirror `custom`, but it never replaces the selected direction. Legacy aliases remain accepted; new files write canonical ids.
- The three proactive-execution fields are top-level boolean `{ "value": ... }` objects, not catalog ids. Omitted fields use `true / false / false` for notes / custom animation / narration audio. These are absence-of-instruction defaults, not permission to override the user's latest explicit request. Preserve all three raw values independently through `result.json`; do not couple or rewrite them. Strategist derives effective Speaker Notes as enabled when audio is `true` and records `Narration Audio dependency` as provenance in the Design Spec. `proactive_custom_animations: false` leaves Strategist animation suggestions unchanged; it only prevents unrequested custom-animation execution.
- `custom_candidates` is an optional legacy recommendation-only shape. New files place all three project-specific variants inside `design_directions`; each remains separately selectable and becomes editable in place. A custom behavior may use zero, one, or many exact catalog bases. Reference count has no fixed cap: every named id must contribute a distinct executable job, the behavior omits any id whose contribution it cannot state, and one basis never requires a decorative second. The UI rejects a selected blank and submits only the edited current value. Template-backed variants obey inherited identity, prototype capacity, and `template_application`.
- Seed `audience`, `communication_intent`, `audience_outcome`, and `delivery_context` when evidence supports them; users need not supply them, and every Stage-1 prose field may end blank. The contract and `primary_language` stay in `result.json` and `design_spec.md`; `spec_lock.md communication` receives `primary_language`, compact `audience` / `objective` / `core_message`, and reading mode. `communication_intent` may preserve multiple purposes and priority/sequence; never add a `primary_job` enum.
- Do not write `recommend.template_reuse_scope` or `recommend.template_adherence`. Strategist records those internal exporter values later in `spec_lock.md` after inspecting the actual template and current content.
- For a confirmed templates-mode handoff, write one editable prose paragraph as top-level `template_application.value`. It summarizes **how to use** the already selected project-local template after every installed template SVG has been inspected: actual prototype use and preservation/reorganization decisions, with the exact SVG basename for every prototype-specific rule. Explicit user instructions win; otherwise Strategist decides from the content and workspace, falling back to reference-led use when no stronger fit exists. Reference, augment-only, and replacement-only are useful interpretations, never submitted enum values or a fixed option menu. The field never chooses, changes, or reinstalls a workspace. Omit it for free design. The UI returns the current string through final Stage 2; Strategist then persists the final effective plan as `- **Template Application**: ...` in `design_spec.md §I`, which Executor reads from the retained Design Spec. Never replace it with internal reuse/adherence ids.

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
- **Candidate display text is written once, in the confirmed UI language**: use the plain keys (`name`, `note`, `mode_behavior`, `visual_style_behavior`, `visual`, `mood`, `behavior`). The server accepts the plain key or any one of the `_zh` / `_zh_tw` / `_en` / `_ja` suffixed variants, and the page falls back across them, so authoring the same text in several languages only adds output.
- **Typography candidates** use concrete heading/body `primary`; non-English decks also use `english`, while English-primary decks omit it. `cjk` / `latin` remain legacy aliases. Localized `name` labels the pair and `css` only previews. Bundles differ overall; font pairs may repeat without blocking. Fixed pairs require `fixed: true`. Catalog `fonts` supplies language-filtered dropdowns plus Other without limiting recommendations; edits mark Custom and refresh the preview. Include topic samples. [`canvas-formats.md`](../../references/canvas-formats.md) § "Typography Scale Start" is the single owner of initial body anchors and sanity bands; the browser mirrors that rule, and submitted values remain px.
- **Per-role size override** (parallel to color's per-role HEX override): besides `body_size`, the page exposes editable inputs for `title` / `subtitle` / `annotation`. The browser applies one documented deterministic dependency chain: PPT uses `reading mode → body baseline`, non-PPT uses `canvas → body baseline`, then every canvas uses `body baseline → unpinned role sizes` (role ramp: `body ×` the §g ratios). Changing reading mode updates a PPT body and all unpinned roles locally; changing body updates unpinned roles locally. Editing body or a role pins that value, so later reading-mode changes do not overwrite it. A font-only selection preserves current sizes; applying a different complete direction, or using the active card's explicit restore action, restores that direction's typography baseline and derived unpinned sizes. This is a browser-only state update: it performs no fetch and asks the backend to author no new recommendations. Each role input is labelled as px and shows an approximate pt equivalent (`1px = 0.75pt`) for orientation. The final values are written to `result.json` as `typography.sizes: { "title", "subtitle", "annotation" }` in **px** — every canvas, no pt and no `sizes_pt` provenance. These confirmed values are Strategist input anchors: the completed page plan may add recurring roles, and downstream execution owns bounded per-occurrence treatment. Candidate `sizes` remain accepted for compatibility; fresh Stage 2 preserves a candidate `body_size` as its baseline and derives only missing or unpinned role sizes from the same local ramp before first render.
- **`delivery_purpose` compatibility key / Reading mode** (enumerable, PPT only) decides where meaning is carried, not merely how large type is: `text` makes pages self-contained with complete sentences, short prose, captions, tables, and necessary detail; `balanced` shares explanation between page and presenter; `presentation` uses one idea, concise claims, and visual evidence while speech / notes carry the detail. It therefore governs page grammar, granularity, density / rhythm, and note burden. Reading-mode cards intentionally show **no px value**; the typography section owns the separately visible body / role sizes and applies any local default. It is surfaced in Stage 2 beside the visual system, separate from communication intent. `recommend.delivery_purpose` pre-selects one; `result.json` retains the key, while `spec_lock.md` uses canonical `consumption_mode`. Non-PPT canvases omit it.
- **Combined style preview** — a compact live "overall impression" strip sits just above the color section and is **sticky**: it pins under the topbar so it stays visible while the user scrolls through the color / icon / typography sections, keeping the picking controls and their combined effect on screen together. It applies the currently selected color palette **and** typography (heading sample in `primary` over `background`, body sample in `body_text`, an `accent` bar, a `secondary_bg` chip) and repaints on every color / HEX-override / font / `body_size` change. It does not replace the per-candidate swatches or font samples (those stay for picking); it is deliberately an abstract style chip, **not** a slide-layout preview — page layout preview remains the live-preview server's job (Step 6). No schema field; it derives entirely from the existing color + typography selections.
- **Generated-image direction** appears only for current `image_usage: ai`, but all three custom project candidates already exist in `design_directions` before that toggle. Turning AI on reveals those candidates immediately without a backend rerun, followed by the 20 fixed system styles. Selecting a project candidate expands its behavior editor in that card; a fixed preset submits its id, while a project candidate submits `rendering: "custom"` + edited non-empty `behavior`. Turning AI off omits `image_strategy` from the final result without deleting the authored recommendation candidates. Catalog-based custom behavior names exact ids for optional `image_rendering_references`; a novel behavior has none. The left preview follows selection. No image palette is written; deck colors remain authoritative, and legacy `image_strategy.palette` is ignored. Illustrated icons and decorative lettering are downstream AI carrier decisions; neither adds a Confirm UI field or `result.json` key.
- **`design_directions`** is the canonical Stage-2 starting set: exactly three top-down, project-fit bundles with stable ids, localized copy, custom mode/style/rendering, icons, complete language-aware typography, and HEX `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, `body_text`. The `selected` card carries the persistent Recommended marker and is applied first. A custom direction card uses its localized style-summary note—or the required behavior fallback—instead of requesting a preset-style preview. Newly authored notes may borrow localized catalog display labels where useful or use concise natural language freely; they never force an approximate label or expose internal catalog ids. Clicking an inactive card applies every field it owns; projected custom fields can then be edited in place and all lower controls may diverge. The active card shows an adjusted state and exposes an explicit restore action for its immutable authored bundle. `result.json` stores the edited current components, never a direction id.
- `recommend.generation_mode`, `refine_spec`, and `design_spec_depth` are Stage-2 production fields. `design_spec_depth.value` is exactly `brief` or `complete`: `brief` records each page as a short block list without full page copy, while `complete` records full page briefs. `split` generation or enabled refinement locks the field to `complete` in the UI, and the server rejects a recommendation or final `brief` value under either condition.
- `content_divergence` is a **free-text** Stage-1 source-treatment field. Blank means a balanced default; facts stay sourced at every level. Strategist consumes it while authoring §IX and records it in `design_spec.md §I`; it is not written to `spec_lock.md`. Beautify sends `{ "value": "keep source wording and page structure verbatim", "locked": true }`, so the UI displays it read-only and the server restores it on every staged submit. Edit Native PPTX uses its source-backed round-trip plan instead of this confirmation flow and does not surface the field.
- `lang` is the soft UI-language default (`zh` / `zh-TW` / `en` / `ja`); the persisted user choice wins. It never sets `primary_language`.

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
  "mode": "custom",
  "mode_behavior": "...",
  "visual_style": "custom",
  "visual_style_behavior": "...",
  "color": { "name": "...", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
  "icons": "tabler-outline",
  "typography": { "name": "...", "heading": { "primary": "...", "english": "...", "css": "..." }, "body": { "primary": "...", "english": "...", "css": "..." }, "body_size": 24, "body_size_unit": "px", "sizes": { "title": 42, "subtitle": 32, "annotation": 18 } },
  "delivery_purpose": "balanced",
  "image_usage": ["ai", "provided"],
  "image_notes": "封面和章节页用 AI 主视觉；产品页优先用户素材，缺口页可用占位符。",
  "image_ai_path": "auto",
  "image_strategy": { "name": "方案 A", "rendering": "custom", "visual": "...", "mood": "...", "behavior": "..." },
  "proactive_speaker_notes": true,
  "proactive_custom_animations": false,
  "proactive_narration_audio": false,
  "generation_mode": "continuous",
  "refine_spec": false,
  "design_spec_depth": "brief",
  "stage": "final",
  "status": "confirmed",
  "confirmed_at": "2026-06-15T11:44:44"
}
```

The shape above is final for Strategist confirmation. It intentionally contains
no template-selection field: `template_selection.json`, its agent handoff, and
the installed project-local state own the parallel Stage-1 decision. The proactive-execution values
are independent flat booleans in `result.json`; old recommendations and results
that omit them resolve to `true / false / false`. They remain raw evidence even
when `proactive_speaker_notes` is `false` and `proactive_narration_audio` is
`true`; Strategist owns the effective dependency resolution described above.
Selected custom values use `mode: custom` + `mode_behavior`, `visual_style:
custom` + `visual_style_behavior`, or `image_strategy.rendering: custom` +
`behavior`. During Design Spec and lock authoring, Strategist projects optional
`mode_references`, `visual_style_references`, or
`image_rendering_references` only when that confirmed behavior actually uses
named catalog sources. These lists have no fixed item limit. One item may carry
the complete preset behavior unchanged; with several, each owns a distinct
executable contribution. Genuinely novel custom behavior has no reference list.
The Stage-1 intermediate write retains the communication contract for Stage 2.
Legacy final results without `design_spec_depth` resolve to `complete` when read
by the server.

**Final-result consumption contract.** A final result is the user-confirmed input contract for the Strategist's Design Spec, not another recommendation input. After the final wait, Generate Step 4 reads the complete final object exactly once and retains it while Strategist writes and audits `design_spec.md` against every explicitly present field. Normal lock authoring and downstream execution do not reopen `result.json`; the completed Design Spec is the durable authority. Only after that audit passes does Strategist author `spec_lock.md` from the Design Spec plus current execution context, selecting stable anchors and routing rather than copying every field or enumerating every legal color/font. Every value must be consumed at the semantic type owned by [`strategist.md`](../../references/strategist.md) §1 and its field owner: do not omit or substitute it, and do not silently strengthen or weaken its type. If a confirmed requirement cannot be honored, the owning workflow reports or pauses under failure recovery; it never deletes the requirement to keep the pipeline moving.

- Bespoke mode / style prose lives only in the required behavior sibling; image custom prose lives in `image_strategy.behavior`. Canvas / icons retain free-text edge cases, color / typography retain `name: "custom"`, and image usage remains a source-id array plus `image_notes`.
- `image_ai_path` and `image_strategy` appear only with `image_usage: ai` and remain confirmed downstream. The page is default; explicit/failure chat fallback keeps identical fields. `image_ai_path` selects the Step 5 path, and [`strategist-image.md`](../../references/strategist-image.md) §2 retains the selected rendering or custom behavior as the deck-level image identity anchor; individual prompts still adapt subject, composition, and atmosphere within it.
- Stage-1 **Confirm contract & template choice** writes the Stage-1 `result.json` and `template_selection.json` together, then keeps the page open while the agent installs the selection. A successful Stage-1 wait is explicitly intermediate and cannot end the task. In the same active run, the agent runs `--complete-template-selection`, writes fresh Stage 2 only after that handoff, and enters the final wait while the page keeps polling. Stage-2 **Confirm final plan** saves the final `result.json` and shuts the server down (auto-close). The AI reads each receipt at its owning boundary; chat fallback mirrors the same decisions without UI artifacts. Either way, Step 4 ends with `--shutdown` so a never-confirmed page does not outlive Step 4.

## Scope

- Confirmation surface only — Strategist authors every recommendation; the page never generates deck content.
- No SVG / layout preview here — that is the live preview server's job (`workflows/stages/live-preview.md`, Step 6).
